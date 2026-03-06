from __future__ import annotations

import pandas as pd
from src.models import QueryIntent, ValidationReport


class AnswerSynthesisAgent:
    def compose(self, intent: QueryIntent, df: pd.DataFrame, validation: ValidationReport) -> str:
        if df.empty:
            return "I could not find matching data for this question."

        metric_col = next(
            (
                c
                for c in ["total_sales", "order_count", "ticket_count", "avg_resolution_time"]
                if c in df.columns
            ),
            None,
        )
        if metric_col is None:
            return "I prepared a result table, but could not infer the main metric."

        total = df[metric_col].sum() if metric_col != "avg_resolution_time" else df[metric_col].mean()
        preview = df.head(3).to_dict(orient="records")

        return (
            f"Question understood as `{intent.metric}` with dimensions {intent.dimensions or ['none']}. "
            f"Computed `{metric_col}` value: {round(float(total), 2)}. "
            f"Top rows preview: {preview}. "
            f"Validation status: {'passed' if validation.is_valid else 'failed'}. "
            f"Intent confidence: {intent.confidence:.2f}."
        )
