from __future__ import annotations

from pathlib import Path
import yaml


def load_catalog() -> dict:
    catalog_path = Path(__file__).resolve().parent.parent / "schema" / "catalog.yaml"
    with catalog_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
