from __future__ import annotations

import numpy as np
import pandas as pd


def build_mock_data(seed: int = 42) -> dict[tuple[str, str], pd.DataFrame]:
    rng = np.random.default_rng(seed)
    customer_count = 120

    customer_ids = np.arange(1, customer_count + 1)
    regions = rng.choice(["North", "South", "East", "West"], size=customer_count)
    segments = rng.choice(["Enterprise", "SMB", "Consumer"], size=customer_count)
    signup_dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        rng.integers(0, 365, size=customer_count), unit="D"
    )

    customers = pd.DataFrame(
        {
            "customer_id": customer_ids,
            "name": [f"Customer {i}" for i in customer_ids],
            "region": regions,
            "segment": segments,
            "signup_date": signup_dates,
        }
    )

    order_count = 1500
    order_customer_ids = rng.choice(customer_ids, size=order_count)
    categories = rng.choice(["Hardware", "Software", "Services"], size=order_count)
    status = rng.choice(["completed", "pending", "cancelled"], p=[0.76, 0.18, 0.06], size=order_count)
    amount = rng.normal(loc=350, scale=180, size=order_count).clip(min=20).round(2)
    order_dates = pd.to_datetime("2025-01-01") + pd.to_timedelta(
        rng.integers(0, 365, size=order_count), unit="D"
    )
    orders = pd.DataFrame(
        {
            "order_id": np.arange(1, order_count + 1),
            "customer_id": order_customer_ids,
            "order_date": order_dates,
            "amount": amount,
            "product_category": categories,
            "status": status,
        }
    )

    ticket_count = 900
    ticket_customer_ids = rng.choice(customer_ids, size=ticket_count)
    issue_type = rng.choice(
        ["Login", "Billing", "Feature Request", "Bug", "Performance"], size=ticket_count
    )
    priority = rng.choice(["Low", "Medium", "High"], p=[0.45, 0.40, 0.15], size=ticket_count)
    resolution_hours = rng.gamma(shape=2.2, scale=8.0, size=ticket_count).round(2)
    created_at = pd.to_datetime("2025-01-01") + pd.to_timedelta(
        rng.integers(0, 365, size=ticket_count), unit="D"
    )
    tickets = pd.DataFrame(
        {
            "ticket_id": np.arange(1, ticket_count + 1),
            "customer_id": ticket_customer_ids,
            "created_at": created_at,
            "issue_type": issue_type,
            "priority": priority,
            "resolution_time_hours": resolution_hours,
        }
    )

    return {
        ("postgresql", "customers"): customers,
        ("cassandra", "orders"): orders,
        ("mongodb", "support_tickets"): tickets,
    }
