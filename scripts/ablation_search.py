"""Ablation 1: Alpha-Beta pruning (on/off), move ordering (on/off), and depth (2 vs 3).

    python -X utf8 -m scripts.ablation_search
"""
from __future__ import annotations

import argparse
import random
import time

from agents.alphabeta import AlphaBetaAgent
from agents.heuristic import HeuristicAgent
from arena.play import play_game
from game.engine import Gomoku
from utils.logger import JsonlLogger


def _sample_midgame_positions(count: int = 20, plies: int = 6, seed: int = 0) -> list[Gomoku]:
    rng = random.Random(seed)
    positions: list[Gomoku] = []
    while len(positions) < count:
        g = Gomoku(9, 5)
        for _ in range(plies):
            cands = g.candidate_moves(2) if g.history else [40]
            g.step(rng.choice(cands))
            if g.done:
                break
        if not g.done:
            positions.append(g)
    return positions


def run_ablation(num_positions: int = 20, games_per_pair: int = 40, seed: int = 0) -> None:
    positions = _sample_midgame_positions(num_positions, plies=6, seed=seed)
    configs = [
        ("minimax_d3_no_prune", {"depth": 3, "candidate_limit": 10, "use_pruning": False, "use_ordering": False}),
        ("alphabeta_d3_no_order", {"depth": 3, "candidate_limit": 10, "use_pruning": True, "use_ordering": False}),
        ("alphabeta_d3_full", {"depth": 3, "candidate_limit": 12, "use_pruning": True, "use_ordering": True}),
        ("alphabeta_d2_full", {"depth": 2, "candidate_limit": 12, "use_pruning": True, "use_ordering": True}),
    ]

    print("=== Phần 1: So sánh số nút duyệt & thời gian trên", len(positions), "thế cờ trung cuộc ===")
    print(f"{'Cấu hình':<24} {'Nodes TB':>12} {'Thời gian TB (ms)':>20} {'Giảm nút so với tắt tỉa':>25}")
    print("-" * 84)

    baseline_nodes = None
    unpruned_moves: list[int] = []
    pruned_no_order_moves: list[int] = []

    with JsonlLogger("ablation_search") as logger:
        for label, params in configs:
            nodes_list: list[int] = []
            times_ms: list[float] = []
            chosen_moves: list[int] = []
            for idx, pos in enumerate(positions):
                bot = AlphaBetaAgent(seed=seed + idx, **params)
                t0 = time.perf_counter()
                act = bot.select_action(pos)
                dt_ms = (time.perf_counter() - t0) * 1000.0
                nodes_list.append(bot.last_nodes)
                times_ms.append(dt_ms)
                chosen_moves.append(act)

            if label == "minimax_d3_no_prune":
                baseline_nodes = sum(nodes_list) / len(nodes_list)
                unpruned_moves = chosen_moves
            elif label == "alphabeta_d3_no_order":
                pruned_no_order_moves = chosen_moves

            mean_nodes = sum(nodes_list) / len(nodes_list)
            mean_ms = sum(times_ms) / len(times_ms)
            reduction = (1.0 - mean_nodes / baseline_nodes) * 100.0 if baseline_nodes else 0.0
            print(f"{label:<24} {mean_nodes:>12.1f} {mean_ms:>20.3f} {reduction:>24.1f}%")
            logger.log(
                run="ablation_search",
                phase="node_benchmark",
                config=label,
                positions=len(positions),
                mean_nodes=round(mean_nodes, 2),
                mean_ms=round(mean_ms, 3),
                node_reduction_pct=round(reduction, 2),
                seed=seed,
            )

        exact_matches = sum(a == b for a, b in zip(unpruned_moves, pruned_no_order_moves))
        print(
            f"\nKiểm chứng bảo toàn quyết định (cùng thứ tự duyệt, bật vs. tắt cắt tỉa): "
            f"{exact_matches}/{len(positions)} thế cờ trùng khít nước đi."
        )

        print(f"\n=== Phần 2: Đối kháng trực tiếp ({games_per_pair} ván/cặp, đổi bên đối xứng) ===")
        matchups = [
            ("alphabeta_d3_full", lambda s: AlphaBetaAgent(depth=3, seed=s),
             "alphabeta_d2_full", lambda s: AlphaBetaAgent(depth=2, seed=s)),
            ("alphabeta_d3_full", lambda s: AlphaBetaAgent(depth=3, use_ordering=True, seed=s),
             "alphabeta_d3_no_order", lambda s: AlphaBetaAgent(depth=3, use_ordering=False, seed=s)),
            ("alphabeta_d2_full", lambda s: AlphaBetaAgent(depth=2, seed=s),
             "heuristic", lambda s: HeuristicAgent(seed=s)),
        ]
        print(f"{'Cặp đấu (A vs B)':<44} {'A thắng':>8} {'Hòa':>6} {'B thắng':>8} {'Score A':>9}")
        print("-" * 79)
        rounds = games_per_pair // 2
        for name_a, make_a, name_b, make_b in matchups:
            w_a = w_b = draws = 0
            for r in range(rounds):
                s = seed + r
                w1, _ = play_game(make_a(s), make_b(s + 1000), opening_moves=2, seed=s)
                if w1 == 1:
                    w_a += 1
                elif w1 == -1:
                    w_b += 1
                else:
                    draws += 1

                w2, _ = play_game(make_b(s + 1000), make_a(s), opening_moves=2, seed=s)
                if w2 == -1:
                    w_a += 1
                elif w2 == 1:
                    w_b += 1
                else:
                    draws += 1

            total = w_a + w_b + draws
            score_a = (w_a + 0.5 * draws) / total
            pair_label = f"{name_a} vs {name_b}"
            print(f"{pair_label:<44} {w_a:>8} {draws:>6} {w_b:>8} {score_a:>9.3f}")
            logger.log(
                run="ablation_search",
                phase="head_to_head",
                agent_a=name_a,
                agent_b=name_b,
                games=total,
                wins_a=w_a,
                draws=draws,
                wins_b=w_b,
                score_a=round(score_a, 4),
                seed=seed,
            )


def main() -> None:
    ap = argparse.ArgumentParser(description="Chạy Ablation 1 cho Minimax / Alpha-Beta.")
    ap.add_argument("--positions", type=int, default=20)
    ap.add_argument("-n", "--games-per-pair", type=int, default=40)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    run_ablation(args.positions, args.games_per_pair, args.seed)


if __name__ == "__main__":
    main()
