import csv
import json

import pytest

from scripts.ablation_mcts import run_ablation
from scripts.summarize_mcts import export_summary


def test_csv_is_derived_from_raw_games_and_rejects_corrupted_outcomes(tmp_path):
    run_ablation(simulations=[2], exploration=[1.4], opponents=["random"],
                 games_per_pair=2, run_name="small", log_dir=tmp_path)
    log = tmp_path / "small.jsonl"
    output = tmp_path / "small.csv"
    rows = export_summary(log, output)
    assert len(rows) == 1 and rows[0]["games"] == 2
    assert rows[0]["wins"] + rows[0]["draws"] + rows[0]["losses"] == 2
    with output.open(encoding="utf-8", newline="") as stream:
        assert next(csv.DictReader(stream))["simulations"] == "2"
    raw_path = tmp_path / "small_s2_c1.4_vs_random.jsonl"
    records = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines()]
    record = records[0]
    record["winner"] = -record["winner"] if record["winner"] else 1
    raw_path.write_text("\n".join(json.dumps(row) for row in records), encoding="utf-8")
    with pytest.raises(ValueError, match="Kết quả"):
        export_summary(log, output)


def test_rejects_unfinished_run_before_creating_csv(tmp_path):
    log = tmp_path / "unfinished.jsonl"
    log.write_text('{"event": "metadata"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="chưa hoàn tất"):
        export_summary(log, tmp_path / "unfinished.csv")
    assert not (tmp_path / "unfinished.csv").exists()
