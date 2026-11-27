from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("torch")

from agents.cnn import DEFAULT_CHECKPOINT
from agents.mcts_cnn import MCTSCNNAgent
from agents.registry import accepts_param, make_agent
from arena.play import play_game
from game.engine import Gomoku


def _pos(*coords: tuple[int, int]) -> Gomoku:
    g = Gomoku(9, 5)
    for r, c in coords:
        g.step(r * 9 + c)
    return g


@pytest.mark.parametrize(
    "kwargs",
    [
        {"simulations": 0},
        {"simulations": True},
        {"c_puct": -0.1},
        {"time_limit": 0.0},
        {"time_limit": -1.0},
        {"max_children": 0},
    ],
)
def test_invalid_hyperparameters_raise_value_error(kwargs):
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    with pytest.raises(ValueError):
        MCTSCNNAgent(**kwargs)


def test_preserves_input_deterministic_and_supports_time_limit():
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    assert accepts_param("mcts_cnn", "time_limit")

    game = _pos((4, 4), (3, 4), (4, 5), (3, 5), (5, 3), (3, 3))
    before = game.clone()
    a1 = make_agent("mcts_cnn", simulations=12, seed=7)
    a2 = make_agent("mcts_cnn", simulations=12, seed=7)
    act1 = a1.select_action(game)
    act2 = a2.select_action(game)

    assert game.is_legal(act1)
    assert act1 == act2
    assert a1.last_simulations == 12
    assert np.array_equal(game.board, before.board)
    assert game.history == before.history

    timed = make_agent("mcts_cnn", time_limit=0.02, seed=0)
    act_t = timed.select_action(game)
    assert game.is_legal(act_t)
    assert timed.last_simulations >= 2


def test_wins_immediately_blocks_four_and_builds_open_four():
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    bot = make_agent("mcts_cnn", simulations=24, seed=0)

    win_pos = _pos((2, 0), (3, 0), (2, 1), (3, 1), (2, 2), (3, 2), (2, 3), (6, 6))
    assert bot.select_action(win_pos) == 2 * 9 + 4
    assert bot.last_simulations == 0

    block_pos = _pos((2, 0), (4, 4), (2, 1), (4, 5), (2, 2), (5, 4), (2, 3))
    assert bot.select_action(block_pos) == 2 * 9 + 4
    assert bot.last_simulations == 0

    # X holds an open three at (4,3),(4,4),(4,5) with (4,1),(4,2) and (4,6),(4,7) empty;
    # playing (4,2) or (4,6) creates an unstoppable open four.
    fork_pos = _pos((4, 3), (1, 1), (4, 4), (1, 2), (4, 5), (7, 7))
    chosen = bot.select_action(fork_pos)
    assert chosen in (4 * 9 + 2, 4 * 9 + 6)

    done_game = _pos((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4))
    with pytest.raises(ValueError):
        bot.select_action(done_game)
    with pytest.raises(ValueError):
        bot.select_action(Gomoku(size=5, k=4))


def test_mcts_cnn_beats_random_with_swapped_sides():
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    wins = 0
    for seed in range(4):
        for side in (1, -1):
            puct = make_agent("mcts_cnn", simulations=16, seed=seed)
            rnd = make_agent("random", seed=seed + 100)
            x, o = (puct, rnd) if side == 1 else (rnd, puct)
            winner, _ = play_game(x, o, opening_moves=2, seed=seed)
            wins += winner == side
    assert wins == 8
