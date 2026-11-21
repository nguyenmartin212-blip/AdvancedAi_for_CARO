"""Minimax and Alpha-Beta search for the lab's Tic-Tac-Toe model."""

from math import inf

from tictactoe import actions, other, result, utility


MOVE_ORDER = (4, 0, 2, 6, 8, 1, 3, 5, 7)
LINES = (
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
)


def ordered_actions(board):
    """Visit the center, corners, and sides in that order."""
    return [move for move in MOVE_ORDER if board[move] == ' ']


def _open_two_score(state, player):
    opponent = other(player)
    difference = 0
    for line in LINES:
        marks = tuple(state[index] for index in line)
        if ' ' in marks:
            difference += (marks.count(player) == 2) - (marks.count(opponent) == 2)
    return max(-0.8, min(0.8, 0.4 * difference))


def eval_fun(state, player='x'):
    """Return (value, terminal), from the specified player's perspective."""
    value = utility(state, player)
    if value is not None:
        return value, True
    return _open_two_score(state, player), False


def _search(board, player, *, prune, cutoff=None, ordered=False):
    nodes = 0
    moves_for = ordered_actions if ordered else actions
    opponent = other(player)

    def visit(state, turn, alpha, beta, depth):
        nonlocal nodes
        nodes += 1
        value = utility(state, player)
        if value is not None:
            return value, None
        if depth == cutoff:
            return _open_two_score(state, player), None

        maximizing = turn == player
        next_turn = opponent if maximizing else player
        best_value = -inf if maximizing else inf
        best_move = None
        for move in moves_for(state):
            child = result(state, turn, move)
            child_value, _ = visit(child, next_turn, alpha, beta, depth + 1)
            if maximizing:
                if child_value > best_value:
                    best_value, best_move = child_value, move
                if prune:
                    alpha = max(alpha, best_value)
            else:
                if child_value < best_value:
                    best_value, best_move = child_value, move
                if prune:
                    beta = min(beta, best_value)
            if prune and alpha >= beta:
                break
        return best_value, best_move

    value, move = visit(board, player, -inf, inf, 0)
    return {"move": move, "value": value, "nodes": nodes}


def minimax_search(board, player='x'):
    """Search to terminal states and count every visited tree node."""
    return _search(board, player, prune=False)


def alpha_beta_search(board, player='x', *, ordered=False, cutoff=None):
    """Search with pruning and an optional cutoff measured in plies."""
    if cutoff is not None and (not isinstance(cutoff, int) or cutoff < 1):
        raise ValueError("cutoff must be a positive integer or None")
    return _search(board, player, prune=True, cutoff=cutoff, ordered=ordered)


def alpha_beta_player(board, player='x'):
    return alpha_beta_search(board, player, ordered=True)["move"]


def heuristic2_player(board, player='x'):
    return alpha_beta_search(board, player, ordered=True, cutoff=2)["move"]


def heuristic4_player(board, player='x'):
    return alpha_beta_search(board, player, ordered=True, cutoff=4)["move"]
