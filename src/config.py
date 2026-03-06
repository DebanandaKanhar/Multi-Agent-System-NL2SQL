from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalized_provider(raw: str | None) -> str:
    provider = (raw or "openai").strip().lower()
    if provider not in {"openai", "groq", "ollama"}:
        return "openai"
    return provider


def _default_llm_api_url(provider: str) -> str:
    if provider == "groq":
        return "https://api.groq.com/openai/v1/chat/completions"
    if provider == "ollama":
        return "http://localhost:11434/api/chat"
    return "https://api.openai.com/v1/chat/completions"


def _default_llm_model(provider: str) -> str:
    if provider == "groq":
        return "llama-3.1-8b-instant"
    if provider == "ollama":
        return "llama3.1:8b"
    return "gpt-4o-mini"


@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str


@dataclass(frozen=True)
class CassandraConfig:
    hosts: list[str]
    port: int
    keyspace: str
    username: str
    password: str


@dataclass(frozen=True)
class MongoConfig:
    uri: str
    database: str


@dataclass(frozen=True)
class LLMConfig:
    enabled: bool
    provider: str
    api_url: str
    api_key: str
    model: str
    timeout_seconds: int


@dataclass(frozen=True)
class Settings:
    use_mock_data: bool
    max_rows_per_table_scan: int
    postgres: PostgresConfig
    cassandra: CassandraConfig
    mongo: MongoConfig
    llm: LLMConfig


def load_settings() -> Settings:
    llm_provider = _normalized_provider(os.getenv("LLM_PROVIDER", "openai"))
    llm_api_url = os.getenv("LLM_API_URL", "").strip() or _default_llm_api_url(llm_provider)
    llm_model = os.getenv("LLM_MODEL", "").strip() or _default_llm_model(llm_provider)

    return Settings(
        use_mock_data=_as_bool(os.getenv("USE_MOCK_DATA"), default=True),
        max_rows_per_table_scan=int(os.getenv("MAX_ROWS_PER_TABLE_SCAN", "10000")),
        postgres=PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            dbname=os.getenv("POSTGRES_DB", "analytics"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        ),
        cassandra=CassandraConfig(
            hosts=os.getenv("CASSANDRA_HOSTS", "localhost").split(","),
            port=int(os.getenv("CASSANDRA_PORT", "9042")),
            keyspace=os.getenv("CASSANDRA_KEYSPACE", "analytics"),
            username=os.getenv("CASSANDRA_USERNAME", "cassandra"),
            password=os.getenv("CASSANDRA_PASSWORD", "cassandra"),
        ),
        mongo=MongoConfig(
            uri=os.getenv("MONGO_URI", "mongodb://localhost:27017"),
            database=os.getenv("MONGO_DB", "analytics"),
        ),
        llm=LLMConfig(
            enabled=_as_bool(os.getenv("ENABLE_LLM_PARSER"), default=False),
            provider=llm_provider,
            api_url=llm_api_url,
            api_key=os.getenv("LLM_API_KEY", ""),
            model=llm_model,
            timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "20")),
        ),
    )
