"""Load JSON config (default: configs/default.json)."""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "configs" / "default.json"


def load_config(path: Path | str | None = None) -> dict:
    with open(path or DEFAULT, encoding="utf-8") as f:
        return json.load(f)
