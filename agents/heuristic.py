"""Rule-based Gomoku agent and position evaluation for search."""
from __future__ import annotations

from functools import lru_cache
import random

import numpy as np

from agents.base import Agent
from agents.registry import register
from game.engine import DIRECTIONS, Gomoku


@lru_cache(maxsize=32)
def _line_windows(size: int, length: int) -> np.ndarray:
    """Return flat board indices for each in-bounds winning segment."""
    windows = []
    for dr, dc in DIRECTIONS:
        for row in range(size):
            for col in range(size):
                end_row = row + (length - 1) * dr
                end_col = col + (length - 1) * dc
                if 0 <= end_row < size and 0 <= end_col < size:
                    windows.append([
                        (row + offset * dr) * size + col + offset * dc
                        for offset in range(length)
                    ])
    return np.asarray(windows, dtype=np.intp).reshape(-1, length)


def evaluate(game: Gomoku, player: int) -> float:
    """Score the board from player's perspective without modifying it.

    Count segments that can still become a win. A run open at both ends
    contributes through more segments than a run blocked at one end.
    """
    indices = _line_windows(game.size, game.k)
    if game.is_terminal():
        win_score = 4.0 ** game.k * max(1, len(indices))
        return game.result(player) * win_score

    windows = game.board.ravel()[indices]
    own_counts = np.count_nonzero(windows == player, axis=1)
    opponent_counts = np.count_nonzero(windows == -player, axis=1)
    weights = 4.0 ** np.arange(game.k + 1)
    weights[0] = 0
    own_score = weights[own_counts[opponent_counts == 0]].sum()
    opponent_score = weights[opponent_counts[own_counts == 0]].sum()
    return float(own_score - opponent_score)


def _winning_action(game: Gomoku, player: int, actions: list[int]) -> int | None:
    probe = game.clone()
    probe.player = player
    for action in actions:
        _, reward, _ = probe.step(action)
        if reward:
            return action
        probe.undo()
    return None


class HeuristicAgent(Agent):
    name = "heuristic"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def select_action(self, game: Gomoku) -> int:
        if game.is_terminal():
            raise ValueError("No legal actions in a finished game")

        actions = game.candidate_moves(radius=min(2, game.size - 1))
        if len(actions) == 1:
            return actions[0]

        player = game.player
        for side in (player, -player):
            tactical_action = _winning_action(game, side, actions)
            if tactical_action is not None:
                return tactical_action

        probe = game.clone()
        scores = []
        for action in actions:
            probe.step(action)
            scores.append(evaluate(probe, player))
            probe.undo()

        best_score = max(scores)
        best_actions = [
            action for action, score in zip(actions, scores) if score == best_score
        ]
        return self.rng.choice(best_actions)


@register("heuristic")
def _make(seed: int | None = None) -> HeuristicAgent:
    return HeuristicAgent(seed=seed)
