"""JSONL logger shared by arena, training and ablations.

One JSON object per line -> easy to load with pandas.read_json(path, lines=True).
Every record gets a UTC timestamp. Files go to logs/<run_name>.jsonl.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


class JsonlLogger:
    def __init__(self, run_name: str, log_dir: Path | str | None = None):
        d = Path(log_dir) if log_dir else LOG_DIR
        d.mkdir(parents=True, exist_ok=True)
        self.path = d / f"{run_name}.jsonl"
        self._f = open(self.path, "a", encoding="utf-8")

    def log(self, **record) -> None:
        record.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        self._f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._f.flush()

    def close(self) -> None:
        self._f.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
