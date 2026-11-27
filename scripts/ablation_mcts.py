"""Ablation 2: độ nhạy MCTS theo số mô phỏng và hệ số khám phá UCT.

Mỗi cấu hình dùng cùng seed khai cuộc, đổi bên X/O và tác tử mới cho từng ván.
Log thô dùng đúng định dạng Arena; bản tổng hợp có cấu hình và thông tin môi trường.
"""
from __future__ import annotations

import argparse
from itertools import product
import math
from pathlib import Path
import platform
import sys

import numpy as np

from arena.round_robin import run_round_robin
from utils.logger import JsonlLogger


def run_ablation(
    simulations: list[int] | None = None,
    exploration: list[float] | None = None,
    opponents: list[str] | None = None,
    games_per_pair: int = 40,
    seed: int = 0,
    run_name: str = "ablation_mcts",
    log_dir: Path | str = "logs",
) -> list[dict]:
    simulations = [100, 400, 1000, 2000] if simulations is None else simulations
    exploration = [0.7, 1.4, 2.0] if exploration is None else exploration
    opponents = ["random", "heuristic"] if opponents is None else opponents
    if not simulations or any(isinstance(n, bool) or not isinstance(n, int) or n < 1 for n in simulations):
        raise ValueError("simulations phải gồm các số nguyên dương")
    if not exploration or any(isinstance(c, bool) or not math.isfinite(c) or c < 0 for c in exploration):
        raise ValueError("exploration phải gồm các số hữu hạn, không âm")
    if not opponents or any(name not in {"random", "heuristic", "alphabeta"} for name in opponents):
        raise ValueError("opponents chỉ nhận random, heuristic hoặc alphabeta")
    if isinstance(games_per_pair, bool) or not isinstance(games_per_pair, int) or games_per_pair < 2 or games_per_pair % 2:
        raise ValueError("games_per_pair phải là số nguyên chẵn từ 2 trở lên")
    if not run_name or Path(run_name).name != run_name or "/" in run_name or "\\" in run_name:
        raise ValueError("run_name phải là tên file, không chứa đường dẫn")
    if len(set(simulations)) != len(simulations) or len(set(exploration)) != len(exploration) or len(set(opponents)) != len(opponents):
        raise ValueError("Không được lặp cấu hình")

    cases = [
        (n, c, opponent, f"{run_name}_s{n}_c{c:g}_vs_{opponent}")
        for n, c, opponent in product(simulations, exploration, opponents)
    ]
    directory = Path(log_dir)
    # JsonlLogger ghi nối tiếp nên cần từ chối run đã có để tránh gộp nhầm thí nghiệm.
    for name in [run_name, *(case[3] for case in cases)]:
        if (directory / f"{name}.jsonl").exists():
            raise FileExistsError(f"Log đã tồn tại: {directory / (name + '.jsonl')}")

    summaries: list[dict] = []
    with JsonlLogger(run_name, directory) as logger:
        logger.log(
            run=run_name, event="metadata", seed=seed, games_per_pair=games_per_pair,
            simulations=simulations, exploration=exploration, opponents=opponents,
            opening_moves=2, budget_mode="compute", python=sys.version.split()[0],
            numpy=np.__version__, platform=platform.platform(), processor=platform.processor(),
            timer="perf_counter", time_unit="seconds",
        )
        for index, (n, c, opponent, raw_run) in enumerate(cases, 1):
            records, stats = run_round_robin(
                ["mcts", opponent], games_per_pair=games_per_pair, opening_moves=2,
                seed=seed, budget_mode="compute",
                agent_overrides={"mcts": {"simulations": n, "c": c}},
                run_name=raw_run, log_dir=directory,
            )
            result = {
                "run": run_name, "event": "summary", "raw_run": raw_run,
                "agent": "mcts", "opponent": opponent, "simulations": n, "c": c,
                "seed": seed, "opening_moves": 2, "budget_mode": "compute",
                **stats["mcts"],
            }
            logger.log(**result)
            summaries.append(result)
            print(
                f"[{index}/{len(cases)}] mô phỏng={n:4d}, c={c:g}, gặp {opponent}: "
                f"{result['wins']}-{result['draws']}-{result['losses']} "
                f"| điểm={result['score']:.3f} "
                f"| TB={result['time_per_move'] * 1000:.2f} ms "
                f"| P95={result['p95_time'] * 1000:.2f} ms",
                flush=True,
            )
        logger.log(run=run_name, event="finished", configurations=len(cases),
                   total_games=sum(row["games"] for row in summaries))
    return summaries


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Ablation 2: ngân sách mô phỏng và hằng số UCT của MCTS.")
    parser.add_argument("--simulations", type=int, nargs="+", default=[100, 400, 1000, 2000])
    parser.add_argument("--c", type=float, nargs="+", default=[0.7, 1.4, 2.0])
    parser.add_argument("--opponents", nargs="+", choices=["random", "heuristic", "alphabeta"],
                        default=["random", "heuristic"])
    parser.add_argument("-n", "--games-per-pair", type=int, default=40,
                        help="số ván/cấu hình/đối thủ, chẵn >= 2")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--run", default="ablation_mcts")
    parser.add_argument("--log-dir", type=Path, default=Path("logs"))
    args = parser.parse_args(argv)
    try:
        run_ablation(args.simulations, args.c, args.opponents, args.games_per_pair,
                     args.seed, args.run, args.log_dir)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
