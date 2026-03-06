from __future__ import annotations

from datetime import datetime, timedelta

import psycopg
from psycopg import sql
from cassandra.cluster import Cluster
from pymongo import MongoClient

from src.config import load_settings


def ensure_postgres_database() -> None:
    settings = load_settings()
    with psycopg.connect(
        host=settings.postgres.host,
        port=settings.postgres.port,
        dbname="postgres",
        user=settings.postgres.user,
        password=settings.postgres.password,
        autocommit=True,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (settings.postgres.dbname,))
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(
                    sql.SQL("CREATE DATABASE {}").format(sql.Identifier(settings.postgres.dbname))
                )


def setup_postgres() -> None:
    settings = load_settings()
    ensure_postgres_database()
    with psycopg.connect(
        host=settings.postgres.host,
        port=settings.postgres.port,
        dbname=settings.postgres.dbname,
        user=settings.postgres.user,
        password=settings.postgres.password,
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    region TEXT NOT NULL,
                    signup_date DATE NOT NULL,
                    segment TEXT NOT NULL
                );
                """
            )
            cur.execute("TRUNCATE TABLE customers;")
            cur.executemany(
                """
                INSERT INTO customers (customer_id, name, region, signup_date, segment)
                VALUES (%s, %s, %s, %s, %s);
                """,
                [
                    (1, "Acme Corp", "North", "2024-01-12", "Enterprise"),
                    (2, "Zen Retail", "West", "2024-02-03", "SMB"),
                    (3, "Nova Foods", "South", "2024-03-21", "Consumer"),
                    (4, "CloudWave", "East", "2024-05-01", "Enterprise"),
                    (5, "Pixel Mart", "North", "2024-06-18", "SMB"),
                    (6, "Blue Orchard", "West", "2024-08-09", "Consumer"),
                    (7, "Terra Labs", "South", "2024-09-14", "Enterprise"),
                    (8, "Aero Point", "East", "2024-11-02", "SMB"),
                ],
            )
        conn.commit()


def setup_cassandra() -> None:
    settings = load_settings()
    cluster = Cluster(contact_points=settings.cassandra.hosts, port=settings.cassandra.port)
    session = cluster.connect()

    session.execute(
        f"""
        CREATE KEYSPACE IF NOT EXISTS {settings.cassandra.keyspace}
        WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}};
        """
    )
    session.set_keyspace(settings.cassandra.keyspace)
    session.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INT PRIMARY KEY,
            customer_id INT,
            order_date TIMESTAMP,
            amount DOUBLE,
            product_category TEXT,
            status TEXT
        );
        """
    )
    session.execute("TRUNCATE orders;")

    base_date = datetime(2025, 1, 1)
    rows = [
        (1, 1, base_date + timedelta(days=5), 480.0, "Hardware", "completed"),
        (2, 2, base_date + timedelta(days=10), 120.0, "Software", "completed"),
        (3, 3, base_date + timedelta(days=15), 210.0, "Services", "pending"),
        (4, 4, base_date + timedelta(days=20), 890.0, "Hardware", "completed"),
        (5, 5, base_date + timedelta(days=25), 320.0, "Software", "cancelled"),
        (6, 6, base_date + timedelta(days=32), 410.0, "Services", "completed"),
        (7, 7, base_date + timedelta(days=40), 760.0, "Hardware", "completed"),
        (8, 8, base_date + timedelta(days=45), 230.0, "Software", "pending"),
        (9, 1, base_date + timedelta(days=52), 550.0, "Services", "completed"),
        (10, 2, base_date + timedelta(days=60), 199.0, "Hardware", "completed"),
        (11, 3, base_date + timedelta(days=70), 275.0, "Software", "completed"),
        (12, 4, base_date + timedelta(days=80), 990.0, "Services", "completed"),
    ]
    insert_cql = """
        INSERT INTO orders (order_id, customer_id, order_date, amount, product_category, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    for row in rows:
        session.execute(insert_cql, row)

    cluster.shutdown()


def setup_mongo() -> None:
    settings = load_settings()
    client = MongoClient(settings.mongo.uri)
    db = client[settings.mongo.database]
    collection = db["support_tickets"]
    collection.delete_many({})

    base_date = datetime(2025, 1, 1)
    docs = [
        {
            "ticket_id": 1001,
            "customer_id": 1,
            "created_at": base_date + timedelta(days=2),
            "issue_type": "Billing",
            "priority": "High",
            "resolution_time_hours": 12.5,
        },
        {
            "ticket_id": 1002,
            "customer_id": 2,
            "created_at": base_date + timedelta(days=6),
            "issue_type": "Login",
            "priority": "Medium",
            "resolution_time_hours": 4.0,
        },
        {
            "ticket_id": 1003,
            "customer_id": 3,
            "created_at": base_date + timedelta(days=10),
            "issue_type": "Bug",
            "priority": "High",
            "resolution_time_hours": 18.75,
        },
        {
            "ticket_id": 1004,
            "customer_id": 4,
            "created_at": base_date + timedelta(days=15),
            "issue_type": "Performance",
            "priority": "Low",
            "resolution_time_hours": 30.2,
        },
        {
            "ticket_id": 1005,
            "customer_id": 5,
            "created_at": base_date + timedelta(days=20),
            "issue_type": "Feature Request",
            "priority": "Medium",
            "resolution_time_hours": 9.3,
        },
        {
            "ticket_id": 1006,
            "customer_id": 6,
            "created_at": base_date + timedelta(days=25),
            "issue_type": "Billing",
            "priority": "High",
            "resolution_time_hours": 16.4,
        },
        {
            "ticket_id": 1007,
            "customer_id": 7,
            "created_at": base_date + timedelta(days=31),
            "issue_type": "Bug",
            "priority": "Medium",
            "resolution_time_hours": 7.6,
        },
        {
            "ticket_id": 1008,
            "customer_id": 8,
            "created_at": base_date + timedelta(days=36),
            "issue_type": "Login",
            "priority": "Low",
            "resolution_time_hours": 2.8,
        },
    ]
    collection.insert_many(docs)
    client.close()


def main() -> None:
    setup_postgres()
    setup_cassandra()
    setup_mongo()
    print("Sample databases and tables are created with seed data.")


if __name__ == "__main__":
    main()
