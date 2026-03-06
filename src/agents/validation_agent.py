from __future__ import annotations

import pandas as pd
from src.models import QueryIntent, ValidationReport


class ValidationAgent:
    def validate(self, intent: QueryIntent, df: pd.DataFrame) -> ValidationReport:
        messages: list[str] = []

        if df.empty:
            return ValidationReport(
                is_valid=False,
                messages=["No rows returned. Try removing strict filters or checking table mappings."],
            )

        metric_col_map = {
            "total_sales": "total_sales",
            "order_count": "order_count",
            "ticket_count": "ticket_count",
            "avg_resolution_time": "avg_resolution_time",
        }
        metric_col = metric_col_map.get(intent.metric)

        if metric_col and metric_col in df.columns and df[metric_col].isna().all():
            messages.append("Metric column has only null values.")

        if df.duplicated().sum() > 0:
            messages.append("Duplicate rows detected in final result.")

        is_valid = len(messages) == 0
        if is_valid:
            messages.append("Validation passed: result shape and metric values look consistent.")

        return ValidationReport(is_valid=is_valid, messages=messages)
