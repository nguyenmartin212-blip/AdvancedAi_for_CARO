"""Xuất bảng Ablation 2 từ log thô để dùng lại trong notebook/báo cáo."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from arena.round_robin import summarize

COLUMNS = [
    "simulations", "c", "opponent", "games", "wins", "draws", "losses",
    "score", "ci_low", "ci_high", "mean_ms", "p95_ms", "rollouts_per_move",
]


def export_summary(log_path: Path, output_path: Path) -> list[dict]:
    events = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not events or events[-1].get("event") != "finished":
        raise ValueError("Lượt chạy chưa hoàn tất, chưa thể xuất kết quả thí nghiệm")
    cases = [event for event in events if event.get("event") == "summary"]
    if len(cases) != events[-1]["configurations"]:
        raise ValueError("Số cấu hình không khớp bản ghi kết thúc")
    rows = []
    total_games = 0
    seen = set()
    for case in cases:
        raw_run = case["raw_run"]
        if Path(raw_run).name != raw_run or "/" in raw_run or "\\" in raw_run:
            raise ValueError("Tên file log thô không hợp lệ")
        if raw_run in seen:
            raise ValueError("Log thô bị lặp")
        seen.add(raw_run)
        records = [
            json.loads(line)
            for line in (log_path.parent / f"{raw_run}.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if not records or len(records) != case["games"]:
            raise ValueError(f"Số ván trong log thô không khớp bảng tổng hợp: {raw_run}")
        if any(record["run"] != raw_run or
               {record["agent_x"], record["agent_o"]} != {"mcts", case["opponent"]}
               for record in records):
            raise ValueError(f"Cặp đấu trong log thô không khớp bảng tổng hợp: {raw_run}")
        stats = summarize(records)["mcts"]
        if any(stats[key] != case[key] for key in ("wins", "draws", "losses")):
            raise ValueError(f"Kết quả trong log thô không khớp bảng tổng hợp: {raw_run}")
        total_games += len(records)
        rows.append({
            "simulations": case["simulations"], "c": case["c"], "opponent": case["opponent"],
            **{key: stats[key] for key in ("games", "wins", "draws", "losses", "score", "ci_low", "ci_high")},
            "mean_ms": stats["time_per_move"] * 1000,
            "p95_ms": stats["p95_time"] * 1000,
            "rollouts_per_move": stats["work_per_move"],
        })
    if total_games != events[-1]["total_games"]:
        raise ValueError("Tổng số ván không khớp bản ghi kết thúc")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Kiểm tra log thô và xuất CSV cho Ablation 2.")
    parser.add_argument("log", type=Path, help="file JSONL tổng hợp của run đã hoàn tất")
    parser.add_argument("--output", type=Path, help="đường dẫn CSV (mặc định cùng tên log)")
    args = parser.parse_args(argv)
    try:
        rows = export_summary(args.log, args.output or args.log.with_suffix(".csv"))
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    print(f"Đã đối chiếu log thô và xuất {len(rows)} dòng kết quả.")


if __name__ == "__main__":
    main()
