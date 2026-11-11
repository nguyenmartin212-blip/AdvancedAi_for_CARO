import numpy as np

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
    assert make_agent("heuristic", seed=0).select_action(Gomoku()) == 40


def test_wins_before_blocking():
    game = position((4, 0), (1, 0), (4, 1), (1, 1), (4, 2), (1, 2), (4, 3), (1, 3))
    assert make_agent("heuristic", seed=0).select_action(game) == 4 * 9 + 4


def test_blocks_only_winning_move_at_edge():
    game = position((4, 4), (0, 0), (5, 4), (0, 1), (4, 5), (0, 2), (5, 5), (0, 3))
    assert make_agent("heuristic", seed=0).select_action(game) == 4


def test_second_player_fills_gap_to_win_diagonally():
    game = position((0, 0), (1, 7), (0, 2), (2, 6), (0, 4), (4, 4), (8, 0), (5, 3), (8, 2))
    assert game.player == -1
    assert make_agent("heuristic", seed=0).select_action(game) == 3 * 9 + 5


def test_seeded_selection_is_legal_and_preserves_input():
    game = position((4, 4), (3, 4), (4, 5))
    before = game.clone()
    action = make_agent("heuristic", seed=7).select_action(game)
    assert game.is_legal(action)
    assert action == make_agent("heuristic", seed=7).select_action(game)
    assert np.array_equal(game.board, before.board)
    assert game.history == before.history
    assert (game.player, game.done, game.winner) == (before.player, before.done, before.winner)


def test_evaluation_favors_open_runs_and_respects_perspective():
    open_run = position((4, 2), (0, 0), (4, 3), (0, 2), (4, 4), (0, 4), (4, 5))
    edge_run = position((4, 0), (0, 0), (4, 1), (0, 2), (4, 2), (0, 4), (4, 3))
    open_score = evaluate(open_run, 1)
    assert open_score > evaluate(edge_run, 1)
    assert open_score == -evaluate(open_run, -1)


def test_beats_random_with_paired_openings():
    wins = 0
    for seed in range(6):
        for side in (1, -1):
            heuristic = make_agent("heuristic", seed=seed)
            baseline = make_agent("random", seed=seed)
            x, o = (heuristic, baseline) if side == 1 else (baseline, heuristic)
            winner, _ = play_game(x, o, opening_moves=2, seed=seed)
            wins += winner == side
    assert wins > 6
