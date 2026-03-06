from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import pandas as pd

from src.config import Settings
from src.utils.mock_data import build_mock_data


class DataAdapter(Protocol):
    def fetch_table(self, table: str, limit: int) -> pd.DataFrame:
        ...


@dataclass
class MockAdapter:
    source: str
    mock_data: dict[tuple[str, str], pd.DataFrame]

    def fetch_table(self, table: str, limit: int) -> pd.DataFrame:
        df = self.mock_data.get((self.source, table))
        if df is None:
            return pd.DataFrame()
        return df.head(limit).copy()


class PostgresAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch_table(self, table: str, limit: int) -> pd.DataFrame:
        import psycopg

        query = f"SELECT * FROM {table} LIMIT %s"
        with psycopg.connect(
            host=self.settings.postgres.host,
            port=self.settings.postgres.port,
            dbname=self.settings.postgres.dbname,
            user=self.settings.postgres.user,
            password=self.settings.postgres.password,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit,))
                rows = cur.fetchall()
                columns = [desc.name for desc in cur.description]
        return pd.DataFrame(rows, columns=columns)


class CassandraAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch_table(self, table: str, limit: int) -> pd.DataFrame:
        from cassandra.auth import PlainTextAuthProvider
        from cassandra.cluster import Cluster

        auth_provider = PlainTextAuthProvider(
            username=self.settings.cassandra.username,
            password=self.settings.cassandra.password,
        )
        cluster = Cluster(
            contact_points=self.settings.cassandra.hosts,
            port=self.settings.cassandra.port,
            auth_provider=auth_provider,
        )
        session = cluster.connect(self.settings.cassandra.keyspace)
        rows = session.execute(f"SELECT * FROM {table} LIMIT {int(limit)}")
        records = [dict(row._asdict()) for row in rows]
        cluster.shutdown()
        return pd.DataFrame(records)


class MongoAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch_table(self, table: str, limit: int) -> pd.DataFrame:
        from pymongo import MongoClient

        client = MongoClient(self.settings.mongo.uri)
        db = client[self.settings.mongo.database]
        docs = list(db[table].find({}, {"_id": 0}).limit(limit))
        client.close()
        return pd.DataFrame(docs)


def build_adapters(settings: Settings) -> dict[str, DataAdapter]:
    if settings.use_mock_data:
        mock = build_mock_data()
        return {
            "postgresql": MockAdapter("postgresql", mock),
            "cassandra": MockAdapter("cassandra", mock),
            "mongodb": MockAdapter("mongodb", mock),
        }

    return {
        "postgresql": PostgresAdapter(settings),
        "cassandra": CassandraAdapter(settings),
        "mongodb": MongoAdapter(settings),
    }
