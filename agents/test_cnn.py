from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from agents.cnn import CNNAgent, DEFAULT_CHECKPOINT
from agents.registry import make_agent
from arena.play import play_game
from game.engine import Gomoku
from train.train_cnn import generate_expert_games, split_and_deduplicate


def _pos(*coords: tuple[int, int]) -> Gomoku:
    g = Gomoku(9, 5)
    for r, c in coords:
        g.step(r * 9 + c)
    return g


def test_missing_checkpoint_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        CNNAgent(checkpoint=tmp_path / "missing.pt")


def test_game_level_split_has_zero_cross_split_leakage():
    games = generate_expert_games(num_games=12, expert_depth=1, seed=0)
    splits, meta = split_and_deduplicate(games, seed=0)
    assert meta["train_games"] + meta["val_games"] + meta["test_games"] == 12
    assert meta["train_samples_augmented"] == 8 * (
        meta["unique_positions"] - meta["val_samples"] - meta["test_samples"]
    )


def test_predict_masks_illegal_moves_and_preserves_input():
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    game = _pos((4, 4), (3, 4), (4, 5), (3, 5))
    before = game.clone()
    agent = make_agent("cnn", seed=3)
    probs, val = agent.predict(game)

    assert probs.shape == (81,)
    assert np.isclose(probs.sum(), 1.0, atol=1e-5)
    for occupied in (4 * 9 + 4, 3 * 9 + 4, 4 * 9 + 5, 3 * 9 + 5):
        assert probs[occupied] == 0.0
    assert -1.0 <= val <= 1.0

    act = agent.select_action(game)
    assert game.is_legal(act)
    assert act == make_agent("cnn", seed=3).select_action(game)
    assert np.array_equal(game.board, before.board)
    assert game.history == before.history


def test_rejects_finished_game_and_wrong_board_size():
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    agent = make_agent("cnn", seed=0)
    done_game = _pos((0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4))
    assert done_game.is_terminal()
    with pytest.raises(ValueError):
        agent.select_action(done_game)
    with pytest.raises(ValueError):
        agent.select_action(Gomoku(size=5, k=4))


def test_trained_cnn_beats_random_with_swapped_sides():
    if not DEFAULT_CHECKPOINT.is_file():
        pytest.skip("CNN checkpoint not trained yet")
    wins = 0
    for seed in range(6):
        for side in (1, -1):
            cnn = make_agent("cnn", seed=seed)
            rnd = make_agent("random", seed=seed + 100)
            x, o = (cnn, rnd) if side == 1 else (rnd, cnn)
            winner, _ = play_game(x, o, opening_moves=2, seed=seed)
            wins += winner == side
    assert wins >= 9
