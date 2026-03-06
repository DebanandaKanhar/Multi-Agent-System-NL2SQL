from __future__ import annotations

import pandas as pd
import plotly.express as px

from src.models import QueryIntent


class VisualizationAgent:
    def build(self, intent: QueryIntent, df: pd.DataFrame):
        dashboard = self.build_dashboard(intent, df)
        if not dashboard:
            return None
        if "Primary" in dashboard:
            return dashboard["Primary"]
        return next(iter(dashboard.values()))

    def build_dashboard(self, intent: QueryIntent, df: pd.DataFrame) -> dict[str, object]:
        if df.empty:
            return {}

        numeric_cols = list(df.select_dtypes(include=["number"]).columns)
        categorical_cols = [c for c in df.columns if c not in numeric_cols]
        metric_col = next(
            (c for c in ["total_sales", "order_count", "ticket_count", "avg_resolution_time"] if c in df.columns),
            numeric_cols[0] if numeric_cols else None,
        )
        if metric_col is None:
            return {}

        charts: dict[str, object] = {}

        if intent.chart_hint == "line":
            x_col = "time_bucket" if "time_bucket" in df.columns else (categorical_cols[0] if categorical_cols else None)
            if x_col is None:
                return {}
            charts["Primary"] = px.line(df.sort_values(x_col), x=x_col, y=metric_col, markers=True, title="Trend")
        elif intent.chart_hint == "pie":
            names_col = categorical_cols[0] if categorical_cols else None
            if names_col is not None:
                charts["Primary"] = px.pie(df, names=names_col, values=metric_col, title="Share")
        elif intent.chart_hint == "histogram":
            charts["Primary"] = px.histogram(df, x=metric_col, nbins=20, title="Distribution")
        else:
            x_col = categorical_cols[0] if categorical_cols else (df.columns[0] if len(df.columns) > 1 else None)
            if x_col and x_col != metric_col:
                charts["Primary"] = px.bar(df, x=x_col, y=metric_col, title="Comparison")
            else:
                charts["Primary"] = px.bar(df.reset_index(), x="index", y=metric_col, title="Metric")

        if len(categorical_cols) > 0 and metric_col in df.columns:
            top_dim = categorical_cols[0]
            if top_dim != "time_bucket":
                top_df = df.sort_values(metric_col, ascending=False).head(10)
                charts["Top 10"] = px.bar(
                    top_df,
                    x=top_dim,
                    y=metric_col,
                    title=f"Top 10 by {top_dim}",
                )

        if "time_bucket" in df.columns and metric_col in df.columns:
            trend_df = df.groupby("time_bucket", dropna=False)[metric_col].sum().reset_index()
            charts["Time Trend"] = px.line(
                trend_df.sort_values("time_bucket"),
                x="time_bucket",
                y=metric_col,
                markers=True,
                title="Time Trend",
            )

        if metric_col in numeric_cols:
            charts["Distribution"] = px.histogram(df, x=metric_col, nbins=25, title="Metric Distribution")

        return charts
