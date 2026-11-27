"""Round-robin tournament runner and statistical evaluation for Gomoku agents.

    python -m arena.round_robin --seed 0
    python -m arena.round_robin -n 100 --budget-mode compute --seed 0 --run rr_compute_100
    python -m arena.round_robin -n 100 --budget-mode time --seconds-per-move 0.05 --seed 0 --run rr_time_100
"""
from __future__ import annotations

import argparse
from itertools import combinations
import math
from pathlib import Path
import time

import numpy as np

from agents.base import Agent
from agents.registry import accepts_param, available, make_agent
from arena.play import play_game
from game.engine import Gomoku
from utils.config import load_config
from utils.logger import JsonlLogger


def wilson_ci(score: float, n: int, z: float = 1.959964) -> tuple[float, float]:
    """95% Wilson score interval for normalized score in [0, 1] over n games."""
    if n <= 0:
        return 0.0, 0.0
    p = min(1.0, max(0.0, float(score)))
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = (p + z2 / (2.0 * n)) / denom
    half = (z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _p95(values: list[float]) -> float:
    return float(np.percentile(values, 95)) if values else 0.0


class _TimedAgent(Agent):
    """Wraps an Agent to record wall-clock seconds and search work per move."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.name = getattr(agent, "name", "agent")
        self.times: list[float] = []
        self.works: list[float] = []

    def select_action(self, game: Gomoku) -> int:
        start = time.perf_counter()
        action = self.agent.select_action(game)
        self.times.append(time.perf_counter() - start)
        work = getattr(self.agent, "last_nodes", None)
        if work is None:
            work = getattr(self.agent, "last_simulations", None)
        if work is None:
            # shortcut: static MCTS simulation budget until agents expose per-move counters
            work = getattr(self.agent, "simulations", None)
        if work is not None:
            self.works.append(float(work))
        return action


def _probe_board(size: int, k: int) -> Gomoku:
    g = Gomoku(size, k)
    mid = size // 2
    for dr, dc in ((0, 0), (-1, 0), (0, 1), (-1, -1), (0, -1), (1, 0)):
        r, c = mid + dr, mid + dc
        if 0 <= r < size and 0 <= c < size and not g.done:
            g.step(r * size + c)
    return g


def _apply_time_budget(
    params_by_agent: dict[str, dict],
    seconds_per_move: float,
    size: int,
    k: int,
    overridden: set[str],
) -> None:
    """Pass native time_limit if supported; else calibrate depth/simulations once."""
    probe = _probe_board(size, k)
    for name, params in params_by_agent.items():
        if accepts_param(name, "time_limit"):
            params["time_limit"] = seconds_per_move
            continue
        # shortcut: probe-calibrated depth/sims until agents accept time_limit natively
        if name == "mcts" and "mcts.simulations" not in overridden:
            probe_sims = 25
            agent = make_agent("mcts", seed=0, **{**params, "simulations": probe_sims})
            t0 = time.perf_counter()
            agent.select_action(probe)
            dt = max(time.perf_counter() - t0, 1e-6)
            params["simulations"] = max(1, int(seconds_per_move * probe_sims / dt))
        elif name == "alphabeta" and "alphabeta.depth" not in overridden:
            chosen = 1
            for d in (1, 2, 3, 4):
                agent = make_agent("alphabeta", seed=0, **{**params, "depth": d})
                t0 = time.perf_counter()
                agent.select_action(probe)
                if time.perf_counter() - t0 <= seconds_per_move:
                    chosen = d
                else:
                    break
            params["depth"] = chosen


def _collect_agent_names(records: list[dict], agent_names: list[str] | None) -> list[str]:
    if agent_names is not None:
        return list(agent_names)
    seen: list[str] = []
    for rec in records:
        for key in ("agent_x", "agent_o"):
            name = rec[key]
            if name not in seen:
                seen.append(name)
    return seen


def summarize(
    records: list[dict],
    agent_names: list[str] | None = None,
    agent_times: dict[str, list[float]] | None = None,
) -> dict[str, dict[str, int | float]]:
    """Aggregate W/D/L, score, Wilson 95% CI, mean/p95 move time and search work."""
    names = _collect_agent_names(records, agent_names)
    stats: dict[str, dict[str, int | float]] = {
        name: {
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "games": 0,
            "score": 0.0,
            "ci_low": 0.0,
            "ci_high": 0.0,
            "time_per_move": 0.0,
            "p95_time": 0.0,
            "work_per_move": 0.0,
        }
        for name in names
    }
    log_times: dict[str, list[float]] = {name: [] for name in names}
    work_totals: dict[str, float] = {name: 0.0 for name in names}
    work_moves: dict[str, int] = {name: 0 for name in names}

    for rec in records:
        ax, ao, winner = rec["agent_x"], rec["agent_o"], rec["winner"]
        for side, name, win_val, t_key, w_key in (
            (1, ax, 1, "times_x", "work_x"),
            (-1, ao, -1, "times_o", "work_o"),
        ):
            if name not in stats:
                continue
            stats[name]["games"] += 1
            if winner == win_val:
                stats[name]["wins"] += 1
            elif winner == -win_val:
                stats[name]["losses"] += 1
            else:
                stats[name]["draws"] += 1

            side_times = rec.get(t_key)
            if isinstance(side_times, list):
                log_times[name].extend(float(t) for t in side_times)
                n_moves = len(side_times)
            else:
                log_times[name].append(float(rec.get("time_per_move", 0.0)))
                n_moves = 1

            w_val = float(rec.get(w_key, 0.0) or 0.0)
            if w_key in rec and w_val >= 0.0 and n_moves > 0:
                work_totals[name] += w_val * n_moves
                work_moves[name] += n_moves

    for name in names:
        g = int(stats[name]["games"])
        score = (int(stats[name]["wins"]) + 0.5 * int(stats[name]["draws"])) / g if g else 0.0
        lo, hi = wilson_ci(score, g)
        times = agent_times.get(name, []) if agent_times is not None else log_times[name]
        stats[name]["score"] = score
        stats[name]["ci_low"] = lo
        stats[name]["ci_high"] = hi
        stats[name]["time_per_move"] = sum(times) / len(times) if times else 0.0
        stats[name]["p95_time"] = _p95(times)
        stats[name]["work_per_move"] = (
            work_totals[name] / work_moves[name] if work_moves[name] else 0.0
        )

    return stats


def head_to_head(
    records: list[dict],
    agent_names: list[str] | None = None,
) -> dict[str, dict[str, dict[str, int | float]]]:
    """Pairwise W/D/L, score and 95% Wilson CI matrix from row agent's perspective."""
    names = _collect_agent_names(records, agent_names)
    matrix: dict[str, dict[str, dict[str, int | float]]] = {
        a: {
            b: {"wins": 0, "draws": 0, "losses": 0, "games": 0, "score": 0.0, "ci_low": 0.0, "ci_high": 0.0}
            for b in names
            if b != a
        }
        for a in names
    }
    for rec in records:
        ax, ao, w = rec["agent_x"], rec["agent_o"], rec["winner"]
        if ax in matrix and ao in matrix[ax]:
            cell_x = matrix[ax][ao]
            cell_o = matrix[ao][ax]
            cell_x["games"] += 1
            cell_o["games"] += 1
            if w == 1:
                cell_x["wins"] += 1
                cell_o["losses"] += 1
            elif w == -1:
                cell_x["losses"] += 1
                cell_o["wins"] += 1
            else:
                cell_x["draws"] += 1
                cell_o["draws"] += 1

    for a in names:
        for b, cell in matrix[a].items():
            g = int(cell["games"])
            score = (int(cell["wins"]) + 0.5 * int(cell["draws"])) / g if g else 0.0
            lo, hi = wilson_ci(score, g)
            cell["score"] = score
            cell["ci_low"] = lo
            cell["ci_high"] = hi
    return matrix


def side_advantage(records: list[dict]) -> dict[str, int | float]:
    """First-player (X) vs second-player (O) outcome counts and rates."""
    n = len(records)
    x_wins = sum(1 for r in records if r["winner"] == 1)
    o_wins = sum(1 for r in records if r["winner"] == -1)
    draws = n - x_wins - o_wins
    return {
        "games": n,
        "x_wins": x_wins,
        "o_wins": o_wins,
        "draws": draws,
        "x_win_rate": x_wins / n if n else 0.0,
        "o_win_rate": o_wins / n if n else 0.0,
        "draw_rate": draws / n if n else 0.0,
    }


def format_summary(summary: dict[str, dict[str, int | float]]) -> str:
    """Format per-agent W/D/L, score, 95% CI, mean/p95 move time and search work."""
    header = (
        f"{'Agent':<12} {'Thắng':>6} {'Hòa':>6} {'Thua':>6} {'Điểm':>7} "
        f"{'CI 95%':>15} {'Thời gian/nước (s)':>20} {'P95 (s)':>10} {'Nodes/Sims':>11}"
    )
    sep = "-" * len(header)
    rows = [header, sep]
    for name, s in summary.items():
        wins, draws, losses = int(s.get("wins", 0)), int(s.get("draws", 0)), int(s.get("losses", 0))
        games = int(s.get("games", wins + draws + losses))
        score = float(s["score"]) if "score" in s else ((wins + 0.5 * draws) / games if games else 0.0)
        if "ci_low" in s and "ci_high" in s:
            lo, hi = float(s["ci_low"]), float(s["ci_high"])
        else:
            lo, hi = wilson_ci(score, games)
        ci_str = f"[{lo:.2f}, {hi:.2f}]"
        tpm = float(s.get("time_per_move", 0.0))
        p95 = float(s.get("p95_time", tpm))
        work = float(s.get("work_per_move", 0.0))
        rows.append(
            f"{name:<12} {wins:>6} {draws:>6} {losses:>6} {score:>7.3f} "
            f"{ci_str:>15} {tpm:>20.6f} {p95:>10.6f} {work:>11.1f}"
        )
    return "\n".join(rows)


def format_matrix(
    matrix: dict[str, dict[str, dict[str, int | float]]],
    agent_names: list[str] | None = None,
) -> str:
    """Format pairwise score (W-D-L) matrix."""
    names = list(agent_names) if agent_names is not None else list(matrix.keys())
    col_w = 18
    header = f"{'A \\ B':<12}" + "".join(f"{b:>{col_w}}" for b in names)
    rows = [header, "-" * len(header)]
    for a in names:
        cells = []
        for b in names:
            if a == b:
                cells.append(f"{'---':>{col_w}}")
            else:
                c = matrix[a][b]
                txt = f"{c['score']:.2f} ({c['wins']}-{c['draws']}-{c['losses']})"
                cells.append(f"{txt:>{col_w}}")
        rows.append(f"{a:<12}" + "".join(cells))
    return "\n".join(rows)


def run_round_robin(
    agent_names: list[str] | None = None,
    *,
    games_per_pair: int = 2,
    opening_moves: int | None = None,
    seed: int = 0,
    budget_mode: str = "compute",
    seconds_per_move: float | None = None,
    agent_overrides: dict[str, dict] | None = None,
    run_name: str = "round_robin",
    log_dir: Path | str | None = None,
    config_path: Path | str | None = None,
) -> tuple[list[dict], dict[str, dict[str, int | float]]]:
    """Run a round-robin tournament, write JSONL logs, and return (records, summary)."""
    if isinstance(games_per_pair, bool) or not isinstance(games_per_pair, int) or games_per_pair < 2 or games_per_pair % 2 != 0:
        raise ValueError("games_per_pair must be a positive even integer (>= 2)")
    if budget_mode not in ("compute", "time"):
        raise ValueError("budget_mode must be 'compute' or 'time'")

    cfg = load_config(config_path)
    size, k = cfg["game"]["size"], cfg["game"]["k"]
    arena_cfg = cfg.get("arena", {})
    if opening_moves is None:
        opening_moves = int(arena_cfg.get("random_opening_moves", 2))
    if opening_moves < 0:
        raise ValueError("opening_moves must be non-negative")

    reg = available()
    if agent_names is None:
        cfg_agents = [a for a in cfg.get("agents", {}) if a in reg]
        agent_names = cfg_agents if len(cfg_agents) >= 2 else reg
    if len(agent_names) < 2:
        raise ValueError("Need at least two agents for a round-robin tournament")
    for name in agent_names:
        if name not in reg:
            raise KeyError(f"Unknown agent '{name}'. Available: {reg}")

    params_by_agent: dict[str, dict] = {
        name: dict(cfg.get("agents", {}).get(name, {})) for name in agent_names
    }
    mode_cfg = arena_cfg.get("budget_modes", {}).get(budget_mode, {})
    if budget_mode == "compute":
        if "alphabeta_depth" in mode_cfg and "alphabeta" in params_by_agent:
            params_by_agent["alphabeta"]["depth"] = mode_cfg["alphabeta_depth"]
        if "mcts_simulations" in mode_cfg and "mcts" in params_by_agent:
            params_by_agent["mcts"]["simulations"] = mode_cfg["mcts_simulations"]

    overridden: set[str] = set()
    if agent_overrides:
        for name, overrides in agent_overrides.items():
            if not overrides:
                continue
            for param_key in overrides:
                overridden.add(f"{name}.{param_key}")
            if name in params_by_agent:
                params_by_agent[name].update(overrides)
            else:
                merged = dict(cfg.get("agents", {}).get(name, {}), **overrides)
                make_agent(name, seed=seed, **merged)

    move_budget_s: float | None = None
    if budget_mode == "time":
        move_budget_s = float(
            seconds_per_move if seconds_per_move is not None else mode_cfg.get("seconds_per_move", 1.0)
        )
        if not math.isfinite(move_budget_s) or move_budget_s <= 0:
            raise ValueError("seconds_per_move must be a positive finite number")
        _apply_time_budget(params_by_agent, move_budget_s, size, k, overridden)
    elif seconds_per_move is not None:
        if not math.isfinite(seconds_per_move) or seconds_per_move <= 0:
            raise ValueError("seconds_per_move must be a positive finite number")

    records: list[dict] = []
    agent_times: dict[str, list[float]] = {name: [] for name in agent_names}
    rounds_per_pair = games_per_pair // 2

    with JsonlLogger(run_name, log_dir) as logger:
        for pair_idx, (agent_a, agent_b) in enumerate(combinations(agent_names, 2)):
            for round_idx in range(rounds_per_pair):
                opening_seed = seed + pair_idx * rounds_per_pair + round_idx
                for name_x, name_o in ((agent_a, agent_b), (agent_b, agent_a)):
                    ax = make_agent(name_x, seed=opening_seed, **params_by_agent[name_x])
                    ao = make_agent(name_o, seed=opening_seed + 1000, **params_by_agent[name_o])
                    timed_x = _TimedAgent(ax)
                    timed_o = _TimedAgent(ao)
                    winner, moves = play_game(
                        timed_x,
                        timed_o,
                        size=size,
                        k=k,
                        opening_moves=opening_moves,
                        seed=opening_seed,
                    )
                    agent_times[name_x].extend(timed_x.times)
                    agent_times[name_o].extend(timed_o.times)
                    game_times = timed_x.times + timed_o.times
                    time_per_move = sum(game_times) / len(game_times) if game_times else 0.0
                    record = {
                        "run": run_name,
                        "agent_x": name_x,
                        "agent_o": name_o,
                        "winner": int(winner),
                        "moves": moves,
                        "seed": int(opening_seed),
                        "budget_mode": budget_mode,
                        "time_per_move": float(time_per_move),
                        "times_x": [round(t, 6) for t in timed_x.times],
                        "times_o": [round(t, 6) for t in timed_o.times],
                        "work_x": round(sum(timed_x.works) / len(timed_x.works), 2) if timed_x.works else 0.0,
                        "work_o": round(sum(timed_o.works) / len(timed_o.works), 2) if timed_o.works else 0.0,
                    }
                    if move_budget_s is not None:
                        record["seconds_per_move"] = move_budget_s
                    logger.log(**record)
                    records.append(record)

    summary = summarize(records, agent_names=agent_names, agent_times=agent_times)
    return records, summary


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chạy giải đấu vòng tròn (round-robin) giữa các agent.")
    parser.add_argument(
        "--agents",
        nargs="+",
        choices=available(),
        help="danh sách agent tham gia (mặc định: tất cả agent trong cấu hình)",
    )
    parser.add_argument(
        "-n",
        "--games-per-pair",
        type=int,
        default=2,
        help="số ván mỗi cặp, phải là số chẵn >= 2 (mặc định: 2; cuối kỳ: 100 hoặc 200)",
    )
    parser.add_argument(
        "--opening-moves",
        type=int,
        help="số nước khai cuộc ngẫu nhiên (mặc định theo config)",
    )
    parser.add_argument("--seed", type=int, default=0, help="seed gốc (mặc định: 0)")
    parser.add_argument(
        "--budget-mode",
        choices=("compute", "time"),
        default="compute",
        help="chế độ ngân sách: compute (mặc định) hoặc time (cùng giây/nước)",
    )
    parser.add_argument(
        "--seconds-per-move",
        type=float,
        help="ngân sách giây/nước khi chạy --budget-mode time (mặc định theo config)",
    )
    parser.add_argument("--depth", type=int, help="ghi đè độ sâu tìm kiếm cho alphabeta")
    parser.add_argument("--simulations", type=int, help="ghi đè số mô phỏng cho mcts")
    parser.add_argument("--c", type=float, help="ghi đè hệ số khám phá UCT cho mcts")
    parser.add_argument("--matrix", action="store_true", help="in thêm ma trận đối đầu và thống kê đi trước X/O")
    parser.add_argument("--run", default="round_robin", help="tên run lưu log JSONL (mặc định: round_robin)")
    parser.add_argument("--log-dir", type=Path, help="thư mục lưu file log JSONL")
    parser.add_argument("--config", type=Path, help="đường dẫn file cấu hình JSON")
    args = parser.parse_args(argv)

    overrides: dict[str, dict] = {"alphabeta": {}, "mcts": {}}
    if args.depth is not None:
        overrides["alphabeta"]["depth"] = args.depth
    if args.simulations is not None:
        overrides["mcts"]["simulations"] = args.simulations
    if args.c is not None:
        overrides["mcts"]["c"] = args.c

    try:
        records, summary = run_round_robin(
            args.agents,
            games_per_pair=args.games_per_pair,
            opening_moves=args.opening_moves,
            seed=args.seed,
            budget_mode=args.budget_mode,
            seconds_per_move=args.seconds_per_move,
            agent_overrides=overrides,
            run_name=args.run,
            log_dir=args.log_dir,
            config_path=args.config,
        )
    except ValueError as error:
        parser.error(str(error))

    print(format_summary(summary))
    if args.matrix:
        print("\nMa trận đối đầu (score | W-D-L):")
        print(format_matrix(head_to_head(records, list(summary.keys()))))
        adv = side_advantage(records)
        print(
            f"\nLợi thế lượt đi ({adv['games']} ván): "
            f"X thắng {adv['x_wins']} ({adv['x_win_rate']:.1%}), "
            f"O thắng {adv['o_wins']} ({adv['o_win_rate']:.1%}), "
            f"Hòa {adv['draws']} ({adv['draw_rate']:.1%})"
        )


if __name__ == "__main__":
    main()
