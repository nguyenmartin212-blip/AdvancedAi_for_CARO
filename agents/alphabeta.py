"""Depth-limited Minimax (Negamax) with optional alpha-beta pruning and move ordering."""
from __future__ import annotations

import math
import random

from agents.base import Agent
from agents.heuristic import evaluate, winning_action
from agents.registry import register
from game.engine import Gomoku


class AlphaBetaAgent(Agent):
    name = "alphabeta"

    def __init__(
        self,
        depth: int = 3,
        seed: int | None = None,
        candidate_limit: int = 12,
        use_pruning: bool = True,
        use_ordering: bool = True,
    ):
        if depth < 1:
            raise ValueError("depth must be at least 1")
        if candidate_limit < 1:
            raise ValueError("candidate_limit must be at least 1")
        self.depth = depth
        self.candidate_limit = candidate_limit
        self.use_pruning = bool(use_pruning)
        self.use_ordering = bool(use_ordering)
        self.rng = random.Random(seed)
        self.last_nodes: int = 0
        self._nodes: int = 0

    def select_action(self, game: Gomoku) -> int:
        if game.is_terminal():
            raise ValueError("No legal actions in a finished game")

        self._nodes = 0
        probe = game.clone()
        actions = self._ordered_actions(probe, shuffle=True)
        best_action = actions[0]
        best_score = -math.inf
        alpha = -math.inf
        for action in actions:
            probe.step(action)
            child_beta = -alpha if self.use_pruning else math.inf
            score = -self._search(probe, self.depth - 1, -math.inf, child_beta)
            probe.undo()
            if score > best_score:
                best_score = score
                best_action = action
                alpha = max(alpha, best_score)
        self.last_nodes = self._nodes
        return best_action

    def _search(self, game: Gomoku, depth: int, alpha: float, beta: float) -> float:
        """Negamax form of Minimax. Scores belong to the side to move."""
        self._nodes += 1
        if game.is_terminal():
            # Remaining depth rewards faster wins and slower losses.
            return evaluate(game, game.player) * (depth + 1)
        if depth == 0:
            return evaluate(game, game.player)

        best = -math.inf
        for action in self._ordered_actions(game):
            game.step(action)
            if self.use_pruning:
                score = -self._search(game, depth - 1, -beta, -alpha)
            else:
                score = -self._search(game, depth - 1, -math.inf, math.inf)
            game.undo()
            best = max(best, score)
            if self.use_pruning:
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
        return best

    def _ordered_actions(self, game: Gomoku, *, shuffle: bool = False) -> list[int]:
        actions = game.candidate_moves(radius=min(2, game.size - 1))
        if len(actions) == 1:
            return actions
        if not self.use_ordering:
            if shuffle:
                self.rng.shuffle(actions)
            return actions[:self.candidate_limit]

        player = game.player
        win = winning_action(game, player, actions)
        if win is not None:
            return [win]
        block = winning_action(game, -player, actions)
        if block is not None:
            # An immediate threat forces this reply. With multiple threats
            # and no winning move of our own, blocking one still loses.
            return [block]

        if shuffle:
            self.rng.shuffle(actions)
        scores = {}
        for action in actions:
            game.step(action)
            scores[action] = evaluate(game, player)
            game.undo()
        actions.sort(key=scores.__getitem__, reverse=True)
        return actions[:self.candidate_limit]


@register("alphabeta")
def _make(
    depth: int = 3,
    seed: int | None = None,
    candidate_limit: int = 12,
    use_pruning: bool = True,
    use_ordering: bool = True,
) -> AlphaBetaAgent:
    return AlphaBetaAgent(
        depth=depth,
        seed=seed,
        candidate_limit=candidate_limit,
        use_pruning=use_pruning,
        use_ordering=use_ordering,
    )
