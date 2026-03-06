from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pandas as pd

from src.data.gateway import HybridDataGateway
from src.models import QueryIntent, QueryPlan


class QueryExecutionAgent:
    def __init__(self, gateway: HybridDataGateway):
        self.gateway = gateway

    def execute(self, intent: QueryIntent, plan: QueryPlan) -> tuple[pd.DataFrame, list[str]]:
        table_map: dict[str, pd.DataFrame] = {}
        query_logs: list[str] = []
        for req in plan.requests:
            query_logs.append(
                f"FETCH source={req.source} table={req.table} columns={req.required_columns} limit={self.gateway.max_rows}"
            )
            df = self.gateway.fetch(req.source, req.table)
            if not df.empty:
                keep_cols = [c for c in req.required_columns if c in df.columns]
                table_map[req.table] = df[keep_cols].copy()
                query_logs.append(f"FETCH_RESULT table={req.table} rows={len(table_map[req.table])}")
            else:
                query_logs.append(f"FETCH_RESULT table={req.table} rows=0")

        if intent.metric in {"total_sales", "order_count"}:
            base = table_map.get("orders", pd.DataFrame())
            date_col = "order_date"
        else:
            base = table_map.get("support_tickets", pd.DataFrame())
            date_col = "created_at"

        if base.empty:
            query_logs.append("EXECUTION_RESULT rows=0 (no base dataset)")
            return pd.DataFrame(), query_logs

        if "customers" in table_map:
            base = base.merge(table_map["customers"], on="customer_id", how="left")
            query_logs.append("JOIN orders_or_tickets WITH customers ON customer_id")

        base = self._apply_filters(base, intent.filters, date_col)
        query_logs.append(f"FILTERS_APPLIED {intent.filters if intent.filters else '{}'}")

        if date_col in base.columns:
            base[date_col] = pd.to_datetime(base[date_col], errors="coerce")

        if intent.time_granularity and date_col in base.columns:
            freq = {"day": "D", "week": "W", "month": "M"}[intent.time_granularity]
            base["time_bucket"] = base[date_col].dt.to_period(freq).astype(str)

        group_by = [d for d in intent.dimensions if d in base.columns]
        if "time_bucket" in base.columns:
            group_by = group_by + ["time_bucket"]

        if intent.metric == "total_sales":
            out = self._aggregate(base, group_by, "amount", "sum", "total_sales")
            query_logs.append(f"AGG metric=total_sales group_by={group_by} rows={len(out)}")
            return out, query_logs
        if intent.metric == "order_count":
            out = self._aggregate(base, group_by, "order_id", "count", "order_count")
            query_logs.append(f"AGG metric=order_count group_by={group_by} rows={len(out)}")
            return out, query_logs
        if intent.metric == "ticket_count":
            out = self._aggregate(base, group_by, "ticket_id", "count", "ticket_count")
            query_logs.append(f"AGG metric=ticket_count group_by={group_by} rows={len(out)}")
            return out, query_logs
        if intent.metric == "avg_resolution_time":
            out = self._aggregate(
                base, group_by, "resolution_time_hours", "mean", "avg_resolution_time"
            )
            query_logs.append(f"AGG metric=avg_resolution_time group_by={group_by} rows={len(out)}")
            return out, query_logs

        out = base.head(200)
        query_logs.append(f"EXECUTION_RESULT fallback_rows={len(out)}")
        return out, query_logs

    @staticmethod
    def _aggregate(
        df: pd.DataFrame, group_by: list[str], metric_col: str, op: str, output_col: str
    ) -> pd.DataFrame:
        if metric_col not in df.columns:
            return pd.DataFrame()
        if not group_by:
            value = getattr(df[metric_col], op)()
            return pd.DataFrame([{output_col: float(value)}])
        agg_df = (
            df.groupby(group_by, dropna=False)[metric_col]
            .agg(op)
            .reset_index()
            .rename(columns={metric_col: output_col})
        )
        return agg_df.sort_values(by=output_col, ascending=False)

    @staticmethod
    def _apply_filters(df: pd.DataFrame, filters: dict[str, str], date_col: str) -> pd.DataFrame:
        out = df.copy()
        if "status" in filters and "status" in out.columns:
            out = out[out["status"].astype(str).str.lower() == filters["status"].lower()]
        if "priority" in filters and "priority" in out.columns:
            out = out[out["priority"].astype(str).str.lower() == filters["priority"].lower()]
        if "last_n_days" in filters and date_col in out.columns:
            out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
            now_utc = datetime.now(tz=timezone.utc).replace(tzinfo=None)
            cutoff = now_utc - timedelta(days=int(filters["last_n_days"]))
            out = out[out[date_col] >= cutoff]
        return out
