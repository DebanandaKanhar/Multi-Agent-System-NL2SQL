from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

from src.config import Settings
from src.models import QueryIntent
from src.utils.prompt_loader import load_intent_prompt_bundle


class QueryUnderstandingAgent:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings
        self.last_llm_error: str | None = None
        self.prompt_bundle = load_intent_prompt_bundle()

    def analyze(self, question: str) -> QueryIntent:
        if self.settings and self.settings.llm.enabled:
            llm_intent = self._analyze_with_llm(question)
            if llm_intent is not None:
                return llm_intent
            deterministic = self._analyze_deterministic(question)
            if self.last_llm_error:
                deterministic.interpretation_notes.append(
                    f"LLM parser fallback used ({self.last_llm_error})."
                )
            return deterministic

        return self._analyze_deterministic(question)

    def _analyze_deterministic(self, question: str) -> QueryIntent:
        q = question.lower()
        notes: list[str] = []
        confidence = 0.25

        metric = "total_sales"
        if "ticket" in q and ("avg" in q or "average" in q):
            metric = "avg_resolution_time"
            notes.append("Detected support-ticket average resolution intent.")
            confidence += 0.30
        elif "ticket" in q and ("count" in q or "number" in q):
            metric = "ticket_count"
            notes.append("Detected support-ticket count intent.")
            confidence += 0.30
        elif "order" in q and ("count" in q or "number" in q):
            metric = "order_count"
            notes.append("Detected order count intent.")
            confidence += 0.30
        elif "sales" in q or "revenue" in q or "amount" in q:
            metric = "total_sales"
            notes.append("Detected sales/revenue intent.")
            confidence += 0.30
        else:
            notes.append("No explicit metric keyword found, using default metric.")

        dimensions: list[str] = []
        for dim in ["region", "segment", "product_category", "status", "issue_type", "priority"]:
            if dim.replace("_", " ") in q or dim in q:
                dimensions.append(dim)
        if dimensions:
            notes.append(f"Dimensions inferred: {dimensions}.")
            confidence += min(0.20, len(dimensions) * 0.07)

        chart_hint = "bar"
        if "trend" in q or "over time" in q or "monthly" in q:
            chart_hint = "line"
            notes.append("Chart hint set to line (trend/time-series cues).")
        elif "distribution" in q:
            chart_hint = "histogram"
            notes.append("Chart hint set to histogram (distribution cue).")
        elif "share" in q or "proportion" in q or "pie" in q:
            chart_hint = "pie"
            notes.append("Chart hint set to pie (share cue).")

        filters: dict[str, str] = {}
        if "completed" in q:
            filters["status"] = "completed"
            confidence += 0.07
        if "high priority" in q:
            filters["priority"] = "High"
            confidence += 0.07

        last_n_days_match = re.search(r"last\s+(\d+)\s+days", q)
        if last_n_days_match:
            filters["last_n_days"] = last_n_days_match.group(1)
            notes.append(f"Time filter detected: last {filters['last_n_days']} days.")
            confidence += 0.08

        time_granularity = None
        if "monthly" in q:
            time_granularity = "month"
            confidence += 0.08
        elif "weekly" in q:
            time_granularity = "week"
            confidence += 0.08
        elif "daily" in q:
            time_granularity = "day"
            confidence += 0.08

        confidence = min(0.99, round(confidence, 2))

        return QueryIntent(
            raw_question=question,
            metric=metric,
            dimensions=dimensions,
            filters=filters,
            chart_hint=chart_hint,
            time_granularity=time_granularity,
            confidence=confidence,
            interpretation_notes=notes,
        )

    def _analyze_with_llm(self, question: str) -> QueryIntent | None:
        if not self.settings:
            self.last_llm_error = "missing settings"
            return None
        provider = self.settings.llm.provider

        if provider in {"openai", "groq"} and not self.settings.llm.api_key:
            self.last_llm_error = f"{provider} API key is not configured"
            return None

        messages = self._build_prompt_messages(question)

        try:
            raw = self._request_llm(messages)
            content = self._extract_content(raw)
            if content is None:
                self.last_llm_error = "empty LLM content"
                return None
            parsed = self._parse_llm_content(content)
            if parsed is None:
                self.last_llm_error = "LLM did not return valid JSON"
                return None
            validated = self._validate_llm_payload(parsed, question)
            validated.interpretation_notes.append(f"LLM provider used: {provider}.")
            self.last_llm_error = None
            return validated
        except (URLError, HTTPError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as exc:
            self.last_llm_error = str(exc)[:140]
            return None

    def _request_llm(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        if not self.settings:
            raise ValueError("Missing settings")

        provider = self.settings.llm.provider
        if provider in {"openai", "groq"}:
            body = {
                "model": self.settings.llm.model,
                "messages": messages,
                "temperature": 0.0,
            }
            headers = {"Content-Type": "application/json"}
            if self.settings.llm.api_key:
                headers["Authorization"] = f"Bearer {self.settings.llm.api_key}"
        elif provider == "ollama":
            body = {
                "model": self.settings.llm.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0},
            }
            headers = {"Content-Type": "application/json"}
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

        req = Request(
            self.settings.llm.api_url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(req, timeout=self.settings.llm.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _build_prompt_messages(self, question: str) -> list[dict[str, str]]:
        system_prompt = str(
            self.prompt_bundle.get("system_prompt", "You are a strict intent parser. Output JSON only.")
        )
        examples = self.prompt_bundle.get("few_shot_examples", [])
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if isinstance(examples, list):
            for example in examples[:8]:
                user_q = example.get("user")
                assistant_json = example.get("assistant_json")
                if not user_q or not isinstance(assistant_json, dict):
                    continue
                messages.append({"role": "user", "content": str(user_q)})
                messages.append(
                    {
                        "role": "assistant",
                        "content": json.dumps(assistant_json, ensure_ascii=True),
                    }
                )

        messages.append({"role": "user", "content": question})
        return messages

    def _extract_content(self, raw: dict[str, Any]) -> str | None:
        if not self.settings:
            return None
        provider = self.settings.llm.provider

        if provider in {"openai", "groq"}:
            return raw.get("choices", [{}])[0].get("message", {}).get("content")
        if provider == "ollama":
            return raw.get("message", {}).get("content")
        return None

    @staticmethod
    def _parse_llm_content(content: str) -> dict[str, Any] | None:
        text = content.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            value = json.loads(text)
            if isinstance(value, dict):
                return value
            return None
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _validate_llm_payload(payload: dict[str, Any], question: str) -> QueryIntent:
        allowed_metrics = {"total_sales", "order_count", "ticket_count", "avg_resolution_time"}
        allowed_dims = {"region", "segment", "product_category", "status", "issue_type", "priority"}
        allowed_charts = {"line", "bar", "pie", "histogram"}
        allowed_granularity = {"day", "week", "month"}

        metric = payload.get("metric", "total_sales")
        if metric not in allowed_metrics:
            metric = "total_sales"

        dimensions = payload.get("dimensions", [])
        if not isinstance(dimensions, list):
            dimensions = []
        dimensions = [d for d in dimensions if d in allowed_dims]

        filters = payload.get("filters", {})
        if not isinstance(filters, dict):
            filters = {}
        clean_filters: dict[str, Any] = {}
        for key in ["status", "priority", "last_n_days"]:
            if key in filters:
                clean_filters[key] = filters[key]

        chart_hint = payload.get("chart_hint", "bar")
        if chart_hint not in allowed_charts:
            chart_hint = "bar"

        time_granularity = payload.get("time_granularity")
        if time_granularity not in allowed_granularity:
            time_granularity = None

        confidence = payload.get("confidence", 0.65)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.65
        confidence = min(0.99, max(0.0, confidence))

        notes = payload.get("interpretation_notes", [])
        if not isinstance(notes, list):
            notes = []
        notes = [str(n) for n in notes][:8]
        notes.append("Parsed with LLM intent parser.")

        return QueryIntent(
            raw_question=question,
            metric=metric,
            dimensions=dimensions,
            filters=clean_filters,
            chart_hint=chart_hint,
            time_granularity=time_granularity,
            confidence=round(confidence, 2),
            interpretation_notes=notes,
        )
