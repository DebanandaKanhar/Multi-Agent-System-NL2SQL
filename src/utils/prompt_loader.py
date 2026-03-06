from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_intent_prompt_bundle() -> dict[str, Any]:
    prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "intent_parser.yaml"
    with prompt_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
