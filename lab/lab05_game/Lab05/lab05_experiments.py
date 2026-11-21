"""Trạng thái kiểm thử, giá trị đối chiếu và giao thức đo cho Lab 05."""

from functools import lru_cache
from time import perf_counter

import numpy as np

from tictactoe import actions, other, play, random_player, result, utility

LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def make_board(x=(), o=()):
    board = [" "] * 9
    for index in x:
        board[index] = "x"
    for index in o:
        board[index] = "o"
    return board


CASES = [
    ("X thắng ngay", make_board(x=(0, 4), o=(1, 3)), "x"),
    ("X phải chặn", make_board(x=(0, 2), o=(1, 4)), "x"),
    ("X bất lợi (giả định)", make_board(x=(2,), o=(0, 8)), "x"),
    ("Bàn trống", make_board(), "x"),
    ("X thua cưỡng bức", make_board(x=(3, 5, 6), o=(0, 1, 4)), "x"),
]


@lru_cache(maxsize=None)
def game_value(board, player):
    """Minimax chính xác theo góc nhìn của bên sắp đi, dùng để đối chiếu."""
    end_value = utility(board, player)
    if end_value is not None:
        return end_value
    values = []
    for action in actions(board):
        child = list(board)
        child[action] = player
        values.append(-game_value(tuple(child), other(player)))
    return max(values)


def move_values(board, player):
    return {
        action: -game_value(tuple(result(board, player, action)), other(player))
        for action in actions(board)
    }


def benchmark(agent, games_per_role=100):
    """Đo lượt tác tử trước Random, số ván bằng nhau ở hai vai."""
    by_role = {}
    total_time = total_moves = 0
    random_state = np.random.get_state()
    try:
        for player in ("x", "o"):
            results = {"x": 0, "o": 0, "d": 0}
            elapsed = moves = 0

            def timed_agent(board, turn):
                nonlocal elapsed, moves
                start = perf_counter()
                action = agent(board, turn)
                elapsed += perf_counter() - start
                moves += 1
                return action

            for game in range(games_per_role):
                np.random.seed(51000 + game + (10000 if player == "o" else 0))
                x, o = (timed_agent, random_player) if player == "x" else (random_player, timed_agent)
                outcome = play(x, o, N=1)
                for key, count in outcome.items():
                    results[key] += count

            by_role[player] = {
                "wins": results[player], "draws": results["d"], "losses": results[other(player)],
                "games": games_per_role, "ms_per_move": elapsed * 1000 / moves,
            }
            total_time += elapsed
            total_moves += moves
    finally:
        np.random.set_state(random_state)

    combined = {
        key: sum(role[key] for role in by_role.values())
        for key in ("wins", "draws", "losses", "games")
    }
    return dict(combined, ms_per_move=total_time * 1000 / total_moves, by_role=by_role)


def print_benchmark(label, stats):
    print(label)
    for player, role in stats["by_role"].items():
        print(f"  Vai {player.upper()}: {role['wins']} thắng, {role['draws']} hòa, "
              f"{role['losses']} thua / {role['games']} ván; {role['ms_per_move']:.4f} ms/nước")
    print(f"  Tổng: {stats['wins']} thắng, {stats['draws']} hòa, "
          f"{stats['losses']} thua / {stats['games']} ván; {stats['ms_per_move']:.4f} ms/nước")
