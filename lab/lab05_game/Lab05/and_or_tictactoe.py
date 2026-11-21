"""Conditional plans for Tic-Tac-Toe with a nondeterministic opponent."""

from functools import cache

from tictactoe import actions, other, random_player, result, utility


def results(state, action, player="x"):
    """Return every outcome of the agent's move and the opponent's response."""
    after_action = result(list(state), player, action)
    if utility(after_action, player) is not None:
        return (tuple(after_action),)
    return tuple(
        tuple(result(after_action, other(player), reply))
        for reply in actions(after_action)
    )


def and_or_search(state, player="x", draw_is_win=True):
    """Find a plan that guarantees a win or, optionally, a draw."""
    return or_search(tuple(state), player, draw_is_win)


@cache
def or_search(state, player, draw_is_win):
    """Choose the first action that succeeds against every possible reply."""
    score = utility(state, player)
    if score == 1:
        return "win"
    if score == 0 and draw_is_win:
        return "draw"
    if score is not None:
        return None

    for action in actions(state):
        branches = and_search(results(state, action, player), player, draw_is_win)
        if branches is not None:
            return action, branches
    return None


def and_search(states, player, draw_is_win):
    """Collect one subplan per outcome, failing if any outcome fails."""
    branches = []
    for state in states:
        plan = or_search(state, player, draw_is_win)
        if plan is None:
            return None
        branches.append((state, plan))
    return tuple(branches)


def and_or_player(board, player="x"):
    """Pick the first move of a non-losing plan, or a random move if none exists."""
    plan = and_or_search(board, player)
    return random_player(board, player) if plan is None else plan[0]
