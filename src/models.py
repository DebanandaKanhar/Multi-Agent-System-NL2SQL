from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import pandas as pd


@dataclass
class QueryIntent:
    raw_question: str
    metric: str
    dimensions: list[str]
    filters: dict[str, Any]
    chart_hint: str
    time_granularity: str | None = None
    confidence: float = 0.0
    interpretation_notes: list[str] = field(default_factory=list)


@dataclass
class DataSourceRequest:
    source: str
    table: str
    required_columns: list[str]


@dataclass
class QueryPlan:
    requests: list[DataSourceRequest] = field(default_factory=list)
    joins: list[dict[str, str]] = field(default_factory=list)
    aggregations: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ValidationReport:
    is_valid: bool
    messages: list[str]


@dataclass
class AgentResult:
    intent: QueryIntent
    plan: QueryPlan
    answer_text: str
    result_df: pd.DataFrame
    validation: ValidationReport
    query_logs: list[str] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
