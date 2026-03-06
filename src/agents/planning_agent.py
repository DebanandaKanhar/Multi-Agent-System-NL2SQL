from __future__ import annotations

from src.models import QueryIntent, QueryPlan, DataSourceRequest


class QueryPlanningAgent:
    def plan(self, intent: QueryIntent, requests: list[DataSourceRequest]) -> QueryPlan:
        plan = QueryPlan(requests=requests)

        sources = {r.source: r.table for r in requests}

        if "postgresql" in sources and "cassandra" in sources:
            plan.joins.append(
                {
                    "left_table": "orders",
                    "right_table": "customers",
                    "left_on": "customer_id",
                    "right_on": "customer_id",
                }
            )
        if "postgresql" in sources and "mongodb" in sources:
            plan.joins.append(
                {
                    "left_table": "support_tickets",
                    "right_table": "customers",
                    "left_on": "customer_id",
                    "right_on": "customer_id",
                }
            )

        plan.aggregations.append(
            {
                "metric": intent.metric,
                "dimensions": intent.dimensions,
                "time_granularity": intent.time_granularity,
            }
        )
        return plan
