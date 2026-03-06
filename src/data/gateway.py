from __future__ import annotations

import pandas as pd

from src.config import Settings
from src.data.adapters import build_adapters


class HybridDataGateway:
    def __init__(self, settings: Settings):
        self.adapters = build_adapters(settings)
        self.max_rows = settings.max_rows_per_table_scan

    def fetch(self, source: str, table: str) -> pd.DataFrame:
        adapter = self.adapters[source]
        return adapter.fetch_table(table, self.max_rows)
