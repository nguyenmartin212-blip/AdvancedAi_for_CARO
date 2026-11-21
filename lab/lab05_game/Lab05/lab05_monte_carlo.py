"""Pure Monte Carlo Search và UCT chỉ phân nhánh ở nút gốc."""

from functools import lru_cache
from math import log, sqrt
import random

from tictactoe import actions, check_board, other, result


@lru_cache(maxsize=None)
def _outcome(board):
    return check_board(board)


def _continue_playout(child, next_player, root_player, rng):
    board = child.copy()
    empty = [index for index, mark in enumerate(board) if mark == " "]
    while True:
        outcome = _outcome(tuple(board))
        if outcome != "n":
            return 0 if outcome == "d" else 1 if outcome == root_player else -1
        action = empty.pop(rng.randrange(len(empty)))
        board[action] = next_player
        next_player = other(next_player)


def playout(state, action, player="x", *, rng=random):
    """Chơi ngẫu nhiên đến hết ván sau khi thử một hành động ở gốc."""
    if _outcome(tuple(state)) != "n":
        raise ValueError("Bàn cờ đã kết thúc.")
    child = result(state, player, action)
    return _continue_playout(child, other(player), player, rng)


def playouts(board, action, player="x", N=100, *, rng=random):
    """Lấy N mẫu độc lập theo cùng chính sách mô phỏng."""
    if _outcome(tuple(board)) != "n":
        raise ValueError("Bàn cờ đã kết thúc.")
    if N < 1:
        raise ValueError("N phải dương.")
    child = result(board, player, action)
    return [_continue_playout(child, other(player), player, rng) for _ in range(N)]


def _root_actions(board, budget):
    legal = actions(board)
    if _outcome(tuple(board)) != "n":
        raise ValueError("Bàn cờ đã kết thúc.")
    if budget < len(legal):
        raise ValueError("Cần ít nhất một playout cho mỗi nước đi.")
    return legal


def pmcs(board, N=100, player="x", *, rng=random, return_stats=False):
    """Chia đều N playout; chọn trung bình utility lớn nhất."""
    legal = _root_actions(board, N)
    per_move, remainder = divmod(N, len(legal))
    extra = set(rng.sample(legal, remainder))
    stats = {}
    for action in legal:
        samples = playouts(board, action, player, per_move + (action in extra), rng=rng)
        stats[action] = {"visits": len(samples), "mean": sum(samples) / len(samples)}
    move = max(legal, key=lambda action: stats[action]["mean"])
    return (move, stats) if return_stats else move


def UCT_depth1(board, N=100, player="x", *, rng=random, return_stats=False):
    """Dùng UCB1 để cấp playout cho các nước đi gốc; chọn theo số lượt thăm."""
    legal = _root_actions(board, N)
    next_player = other(player)
    children = [result(board, player, action) for action in legal]
    visits = [0] * len(legal)
    totals = [0] * len(legal)
    for trial in range(N):
        if trial < len(legal):
            index = trial
        else:
            exploration = 2 * log(trial)
            index = max(
                range(len(legal)),
                key=lambda i: totals[i] / visits[i] + sqrt(exploration / visits[i]),
            )
        totals[index] += _continue_playout(children[index], next_player, player, rng)
        visits[index] += 1

    move = legal[visits.index(max(visits))]
    if not return_stats:
        return move
    stats = {
        action: {"visits": count, "mean": total / count}
        for action, count, total in zip(legal, visits, totals)
    }
    return move, stats


def pmcs10_player(board, player="x"):
    return pmcs(board, 10, player)


def pmcs100_player(board, player="x"):
    return pmcs(board, 100, player)


def pmcs1000_player(board, player="x"):
    return pmcs(board, 1000, player)


def ucb1_10_player(board, player="x"):
    return UCT_depth1(board, 10, player)


def ucb1_100_player(board, player="x"):
    return UCT_depth1(board, 100, player)
