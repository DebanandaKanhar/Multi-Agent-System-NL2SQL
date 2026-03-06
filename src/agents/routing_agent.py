from __future__ import annotations

from src.models import DataSourceRequest, QueryIntent


class SchemaRoutingAgent:
    """Routes user intent to the minimum required tables across databases."""

    def route(self, intent: QueryIntent) -> list[DataSourceRequest]:
        requests = []

        if intent.metric in {"total_sales", "order_count"}:
            requests.append(
                DataSourceRequest(
                    source="cassandra",
                    table="orders",
                    required_columns=[
                        "order_id",
                        "customer_id",
                        "order_date",
                        "amount",
                        "product_category",
                        "status",
                    ],
                )
            )

        if intent.metric in {"ticket_count", "avg_resolution_time"}:
            requests.append(
                DataSourceRequest(
                    source="mongodb",
                    table="support_tickets",
                    required_columns=[
                        "ticket_id",
                        "customer_id",
                        "created_at",
                        "issue_type",
                        "priority",
                        "resolution_time_hours",
                    ],
                )
            )

        requires_customer_enrichment = (
            len(set(intent.dimensions).intersection({"region", "segment"})) > 0
            or "customer" in intent.raw_question.lower()
        )

        if requires_customer_enrichment:
            requests.append(
                DataSourceRequest(
                    source="postgresql",
                    table="customers",
                    required_columns=["customer_id", "name", "region", "segment", "signup_date"],
                )
            )

        if not requests:
            requests.append(
                DataSourceRequest(
                    source="cassandra",
                    table="orders",
                    required_columns=["order_id", "customer_id", "order_date", "amount"],
                )
            )

        return requests
