"""Round-robin tournament runner for registered Gomoku agents.

    python -m arena.round_robin
    python -m arena.round_robin --simulations 50 --depth 2 --seed 0
"""
from __future__ import annotations

import argparse
from itertools import combinations
from pathlib import Path
import time

from agents.base import Agent
from agents.registry import available, make_agent
from arena.play import play_game
from game.engine import Gomoku
from utils.config import load_config
from utils.logger import JsonlLogger


class _TimedAgent(Agent):
    """Wraps an Agent to record wall-clock seconds spent in select_action()."""

    def __init__(self, agent: Agent):
        self.agent = agent
        self.name = getattr(agent, "name", "agent")
        self.times: list[float] = []

    def select_action(self, game: Gomoku) -> int:
        start = time.perf_counter()
        action = self.agent.select_action(game)
        self.times.append(time.perf_counter() - start)
        return action


def summarize(
    records: list[dict],
    agent_names: list[str] | None = None,
    agent_times: dict[str, list[float]] | None = None,
) -> dict[str, dict[str, int | float]]:
    """Aggregate wins, draws, losses and average move time per agent."""
    if agent_names is None:
        seen: list[str] = []
        for rec in records:
            for key in ("agent_x", "agent_o"):
                name = rec[key]
                if name not in seen:
                    seen.append(name)
        agent_names = seen

    stats: dict[str, dict[str, int | float]] = {
        name: {"wins": 0, "draws": 0, "losses": 0, "games": 0, "time_per_move": 0.0}
        for name in agent_names
    }
    fallback_times: dict[str, list[float]] = {name: [] for name in agent_names}

    for rec in records:
        ax, ao, winner = rec["agent_x"], rec["agent_o"], rec["winner"]
        if ax in stats:
            stats[ax]["games"] += 1
            fallback_times[ax].append(float(rec.get("time_per_move", 0.0)))
            if winner == 1:
                stats[ax]["wins"] += 1
            elif winner == -1:
                stats[ax]["losses"] += 1
            else:
                stats[ax]["draws"] += 1
        if ao in stats:
            stats[ao]["games"] += 1
            fallback_times[ao].append(float(rec.get("time_per_move", 0.0)))
            if winner == -1:
                stats[ao]["wins"] += 1
            elif winner == 1:
                stats[ao]["losses"] += 1
            else:
                stats[ao]["draws"] += 1

    for name in agent_names:
        times = agent_times.get(name, []) if agent_times is not None else fallback_times[name]
        stats[name]["time_per_move"] = sum(times) / len(times) if times else 0.0

    return stats


def format_summary(summary: dict[str, dict[str, int | float]]) -> str:
    """Format the per-agent W/D/L and average move time table."""
    header = f"{'Agent':<12} {'Thắng':>6} {'Hòa':>6} {'Thua':>6} {'Thời gian/nước (s)':>20}"
    sep = "-" * len(header)
    rows = [header, sep]
    for name, s in summary.items():
        rows.append(
            f"{name:<12} {int(s['wins']):>6} {int(s['draws']):>6} "
            f"{int(s['losses']):>6} {float(s['time_per_move']):>20.6f}"
        )
    return "\n".join(rows)


def run_round_robin(
    agent_names: list[str] | None = None,
    *,
    games_per_pair: int = 2,
    opening_moves: int | None = None,
    seed: int = 0,
    budget_mode: str = "compute",
    agent_overrides: dict[str, dict] | None = None,
    run_name: str = "round_robin",
    log_dir: Path | str | None = None,
    config_path: Path | str | None = None,
) -> tuple[list[dict], dict[str, dict[str, int | float]]]:
    """Run a round-robin tournament, write JSONL logs, and return (records, summary)."""
    if isinstance(games_per_pair, bool) or not isinstance(games_per_pair, int) or games_per_pair < 2 or games_per_pair % 2 != 0:
        raise ValueError("games_per_pair must be a positive even integer (>= 2)")

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
    if "alphabeta_depth" in mode_cfg and "alphabeta" in params_by_agent:
        params_by_agent["alphabeta"]["depth"] = mode_cfg["alphabeta_depth"]
    if "mcts_simulations" in mode_cfg and "mcts" in params_by_agent:
        params_by_agent["mcts"]["simulations"] = mode_cfg["mcts_simulations"]

    if agent_overrides:
        for name, overrides in agent_overrides.items():
            if not overrides:
                continue
            if name in params_by_agent:
                params_by_agent[name].update(overrides)
            else:
                merged = dict(cfg.get("agents", {}).get(name, {}), **overrides)
                make_agent(name, seed=seed, **merged)

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
                    }
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
        help="số ván mỗi cặp, phải là số chẵn >= 2 (mặc định: 2)",
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
        help="chế độ ngân sách ghi log (mặc định: compute)",
    )
    parser.add_argument("--depth", type=int, help="ghi đè độ sâu tìm kiếm cho alphabeta")
    parser.add_argument("--simulations", type=int, help="ghi đè số mô phỏng cho mcts")
    parser.add_argument("--c", type=float, help="ghi đè hệ số khám phá UCT cho mcts")
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
        _, summary = run_round_robin(
            args.agents,
            games_per_pair=args.games_per_pair,
            opening_moves=args.opening_moves,
            seed=args.seed,
            budget_mode=args.budget_mode,
            agent_overrides=overrides,
            run_name=args.run,
            log_dir=args.log_dir,
            config_path=args.config,
        )
    except ValueError as error:
        parser.error(str(error))

    print(format_summary(summary))


if __name__ == "__main__":
    main()
