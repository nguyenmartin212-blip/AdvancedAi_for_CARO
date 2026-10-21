"""Quick sanity match between two registered agents.

    python -m scripts.quick_match random random -n 20
"""
from __future__ import annotations

import argparse

from agents.registry import available, make_agent
from arena.play import play_game
from utils.config import load_config


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a", help=f"agent for X, one of {available()}")
    ap.add_argument("b", help="agent for O")
    ap.add_argument("-n", type=int, default=20, help="number of games (sides alternate)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    cfg = load_config()
    size, k = cfg["game"]["size"], cfg["game"]["k"]
    pa = cfg["agents"].get(args.a, {})
    pb = cfg["agents"].get(args.b, {})
    wins = {"a": 0, "b": 0, "draw": 0}
    for i in range(args.n):
        a = make_agent(args.a, seed=args.seed + i, **pa)
        b = make_agent(args.b, seed=args.seed + 1000 + i, **pb)
        if i % 2 == 0:
            w, _ = play_game(a, b, size, k, opening_moves=2, seed=args.seed + i)
            wins["a" if w == 1 else "b" if w == -1 else "draw"] += 1
        else:
            w, _ = play_game(b, a, size, k, opening_moves=2, seed=args.seed + i)
            wins["b" if w == 1 else "a" if w == -1 else "draw"] += 1
    print(f"{args.a} vs {args.b}: {wins} over {args.n} games")


if __name__ == "__main__":
    main()
