"""Kiểm thử ngân sách thời gian bằng đồng hồ giả, tránh phụ thuộc tốc độ máy."""
import numpy as np
import pytest

from agents.mcts import MCTSAgent
from agents.registry import accepts_param, make_agent
from game.engine import Gomoku


def position(*moves: tuple[int, int]) -> Gomoku:
    game = Gomoku()
    for row, col in moves:
        game.step(row * game.size + col)
    return game


@pytest.mark.parametrize("limit", [0, -0.1, float("nan"), float("inf"), True])
def test_rejects_invalid_time_limit(limit):
    with pytest.raises(ValueError, match="time_limit"):
        MCTSAgent(time_limit=limit)


def test_stops_at_deadline_and_counts_completed_rollouts(monkeypatch):
    ticks = iter([10.0, 10.0, 10.01, 10.05])
    monkeypatch.setattr("agents.mcts.time.perf_counter", lambda: next(ticks))
    game = position((4, 4), (3, 4), (4, 5))
    before = game.clone()
    bot = make_agent("mcts", simulations=100, seed=2, time_limit=0.05)
    assert game.is_legal(bot.select_action(game))
    assert bot.last_simulations == 2
    assert np.array_equal(game.board, before.board)
    assert game.history == before.history
    assert (game.player, game.done, game.winner) == (before.player, before.done, before.winner)
    assert accepts_param("mcts", "time_limit")


def test_tiny_budget_returns_legal_fallback_without_rollout(monkeypatch):
    ticks = iter([0.0, 1.0])
    monkeypatch.setattr("agents.mcts.time.perf_counter", lambda: next(ticks))
    bot = MCTSAgent(simulations=10, time_limit=0.001, seed=0)
    game = Gomoku()
    assert game.is_legal(bot.select_action(game))
    assert bot.last_simulations == 0


def test_simulation_cap_still_applies_with_time_limit(monkeypatch):
    monkeypatch.setattr("agents.mcts.time.perf_counter", lambda: 0.0)
    bot = MCTSAgent(simulations=3, time_limit=1.0, seed=0)
    bot.select_action(Gomoku())
    assert bot.last_simulations == 3


def test_fixed_budget_does_not_read_clock_and_resets_counter(monkeypatch):
    def unexpected_clock():
        raise AssertionError("Tìm kiếm theo số mô phỏng cố định không được phụ thuộc đồng hồ")
    monkeypatch.setattr("agents.mcts.time.perf_counter", unexpected_clock)
    bot = MCTSAgent(simulations=3, seed=0)
    bot.select_action(Gomoku())
    assert bot.last_simulations == 3
    bot.select_action(Gomoku())
    assert bot.last_simulations == 3


def test_tactical_move_resets_previous_work_even_with_tiny_budget():
    bot = MCTSAgent(simulations=3, seed=0)
    bot.select_action(Gomoku())
    bot.time_limit = 1e-9
    win = position((4, 0), (1, 0), (4, 1), (1, 1), (4, 2), (1, 2), (4, 3), (1, 3))
    assert bot.select_action(win) == 40
    assert bot.last_simulations == 0
    block = position((4, 4), (0, 0), (5, 4), (0, 1), (4, 5), (0, 2), (5, 5), (0, 3))
    assert bot.select_action(block) == 4
    assert bot.last_simulations == 0
