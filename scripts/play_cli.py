"""Play against a registered agent: python -m scripts.play_cli mcts --seed 0."""
from __future__ import annotations

import argparse

from agents.base import Agent
from agents.registry import available, make_agent
from game.engine import Gomoku
from utils.config import load_config


def play(game: Gomoku, agent: Agent, human_player: int = 1) -> int:
    """Run a terminal game; EOF or Ctrl+C exits cleanly without more moves."""
    print(game.render())
    try:
        while not game.done:
            if game.player == human_player:
                raw = input(f"Nhập nước đi (hàng cột, 0-{game.size - 1}; q để thoát): ").strip()
                if raw.lower() in {"q", "quit", "exit"}:
                    print("Đã dừng ván cờ.")
                    return 0
                try:
                    row, col = map(int, raw.split())
                except ValueError:
                    print("Nhập hai số nguyên cách nhau bằng dấu cách.")
                    continue
                if not (0 <= row < game.size and 0 <= col < game.size):
                    print(f"Tọa độ phải từ 0 đến {game.size - 1}.")
                    continue
                action = row * game.size + col
                if not game.is_legal(action):
                    print("Ô này đã có quân. Hãy nhập lại.")
                    continue
            else:
                action = agent.select_action(game)
                row, col = divmod(action, game.size)
                print(f"AI ({agent.name}) đánh {row} {col}.")
            game.step(action)
            print(game.render())
    except (EOFError, KeyboardInterrupt):
        print("\nĐã dừng ván cờ.")
        return 0

    if game.winner:
        symbol = "X" if game.winner == 1 else "O"
        who = "Bạn thắng" if game.winner == human_player else "AI thắng"
        print(f"{who} ({symbol}).")
    else:
        print("Hòa.")
    return game.winner


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Chơi Gomoku qua terminal với bot trong registry.",
                                     add_help=False)
    parser._positionals.title = "Tham số vị trí"
    parser._optionals.title = "Tùy chọn"
    parser.add_argument("-h", "--help", action="help", help="hiện hướng dẫn và thoát")
    parser.add_argument("bot", choices=available(), nargs="?", default="random", help="tên bot (mặc định: random)")
    parser.add_argument("--side", choices=("x", "o"), default="x", help="quân của người chơi (mặc định: x)")
    parser.add_argument("--seed", type=int, default=0, help="seed ngẫu nhiên (mặc định: 0)")
    parser.add_argument("--simulations", type=int, help="số mô phỏng MCTS cho mỗi nước")
    parser.add_argument("--c", type=float, help="hệ số khám phá UCT của MCTS")
    args = parser.parse_args(argv)
    if args.bot != "mcts" and (args.simulations is not None or args.c is not None):
        parser.error("--simulations và --c chỉ dùng với bot mcts")
    cfg = load_config()
    params = dict(cfg["agents"].get(args.bot, {}))
    for key in ("simulations", "c"):
        value = getattr(args, key)
        if value is not None:
            params[key] = value
    try:
        agent = make_agent(args.bot, seed=args.seed, **params)
    except ValueError as error:
        parser.error(str(error))
    game = Gomoku(**cfg["game"])
    print(f"Bạn cầm quân {args.side.upper()}; AI là {args.bot}.")
    play(game, agent, human_player=1 if args.side == "x" else -1)


if __name__ == "__main__":
    main()
