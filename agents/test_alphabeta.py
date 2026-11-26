import numpy as np
import pytest

from agents.heuristic import evaluate
from agents.registry import make_agent
from arena.play import play_game
from game.engine import Gomoku


def position(*moves: tuple[int, int]) -> Gomoku:
    game = Gomoku()
    for row, col in moves:
        game.step(row * game.size + col)
    return game


def test_opening_uses_center():
    assert make_agent("alphabeta", depth=2).select_action(Gomoku()) == 40


def test_wins_before_blocking():
    game = position((4, 0), (1, 0), (4, 1), (1, 1), (4, 2), (1, 2), (4, 3), (1, 3))
    assert make_agent("alphabeta", depth=1, candidate_limit=1).select_action(game) == 40


def test_blocks_even_with_one_candidate_at_depth_one():
    game = position((4, 4), (0, 0), (5, 4), (0, 1), (4, 5), (0, 2), (5, 5), (0, 3))
    assert make_agent("alphabeta", depth=1, candidate_limit=1).select_action(game) == 4


def test_depth_three_finds_forced_win_for_o():
    game = position((0, 0), (4, 3), (0, 2), (4, 4), (2, 0), (4, 5), (2, 2))
    agent = make_agent("alphabeta", depth=3, seed=2)
    action = agent.select_action(game)
    assert action in {4 * 9 + 2, 4 * 9 + 6}

    game.step(action)
    for reply in game.legal_actions():
        variation = game.clone()
        variation.step(reply)
        variation.step(agent.select_action(variation))
        assert variation.winner == -1


def test_seeded_selection_is_legal_and_preserves_input():
    game = position((4, 4), (3, 4), (4, 5))
    before = game.clone()
    action = make_agent("alphabeta", depth=2, seed=7).select_action(game)
    assert game.is_legal(action)
    assert action == make_agent("alphabeta", depth=2, seed=7).select_action(game)
    assert np.array_equal(game.board, before.board)
    assert game.history == before.history
    assert (game.player, game.done, game.winner) == (before.player, before.done, before.winner)


@pytest.mark.parametrize("params", [{"depth": 0}, {"candidate_limit": 0}])
def test_invalid_search_budget(params):
    with pytest.raises(ValueError):
        make_agent("alphabeta", **params)


def test_beats_random_with_paired_openings():
    wins = 0
    for seed in range(4):
        for side in (1, -1):
            search = make_agent("alphabeta", depth=2, seed=seed)
            baseline = make_agent("random", seed=seed)
            x, o = (search, baseline) if side == 1 else (baseline, search)
            winner, _ = play_game(x, o, opening_moves=2, seed=seed)
            wins += winner == side
    assert wins > 4


def test_matches_exhaustive_minimax_on_small_board():
    game = Gomoku(size=3, k=3)
    for action in (4, 0, 1, 7):
        game.step(action)

    def minimax(board, player, depth):
        if board.is_terminal():
            return evaluate(board, player) * (depth + 1)
        if depth == 0:
            return evaluate(board, player)
        best = -float("inf")
        for action in board.legal_actions():
            board.step(action)
            best = max(best, -minimax(board, -player, depth - 1))
            board.undo()
        return best

    scores = {}
    for action in game.legal_actions():
        game.step(action)
        scores[action] = -minimax(game, game.player, 4)
        game.undo()
    chosen = make_agent("alphabeta", depth=5, seed=1).select_action(game)
    assert scores[chosen] == max(scores.values())


def test_pruning_reduces_nodes_and_preserves_move_on_unshuffled_tree():
    game = position((4, 4), (3, 4), (4, 3), (3, 3), (5, 3), (4, 5))
    pruned = make_agent("alphabeta", depth=3, candidate_limit=10, use_pruning=True, use_ordering=False, seed=0)
    unpruned = make_agent("alphabeta", depth=3, candidate_limit=10, use_pruning=False, use_ordering=False, seed=0)
    act_pruned = pruned.select_action(game)
    act_unpruned = unpruned.select_action(game)
    assert act_pruned == act_unpruned
    assert 0 < pruned.last_nodes < unpruned.last_nodes


def test_ordering_further_reduces_nodes():
    game = position((4, 4), (3, 4), (4, 3), (3, 3), (5, 3), (4, 5))
    ordered = make_agent("alphabeta", depth=3, candidate_limit=10, use_pruning=True, use_ordering=True, seed=0)
    unordered = make_agent("alphabeta", depth=3, candidate_limit=10, use_pruning=True, use_ordering=False, seed=0)
    assert game.is_legal(ordered.select_action(game))
    unordered.select_action(game)
    assert 0 < ordered.last_nodes < unordered.last_nodes
