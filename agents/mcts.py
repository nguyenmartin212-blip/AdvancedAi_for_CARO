"""UCT search with seeded random rollouts and root win/block checks.

Each node stores total outcome from its *player to move*'s perspective.
Selection therefore negates the child's mean; backup flips sign at every ply.
Trees are rebuilt on each call, and all simulated moves use clones.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

from agents.base import Agent
from agents.registry import register
from game.engine import Gomoku


@dataclass
class _Node:
    player: int
    untried: list[int]
    action: int | None = None
    children: list[_Node] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0

    def select(self, c: float) -> _Node:
        return max(self.children, key=lambda child: (
            -child.value / child.visits
            + c * math.sqrt(math.log(self.visits) / child.visits)
        ))


def _backup(path: list[_Node], outcome: float) -> None:
    """Outcome is from the last node's player-to-move perspective."""
    for node in reversed(path):
        node.visits += 1
        node.value += outcome
        outcome = -outcome


def _winning_action(game: Gomoku, player: int, actions: list[int]) -> int | None:
    probe = game.clone()
    probe.player = player
    for action in actions:
        _, reward, _ = probe.step(action)
        probe.undo()
        if reward:
            return action
    return None


class MCTSAgent(Agent):
    name = "mcts"

    def __init__(self, simulations: int = 100, c: float = 1.4,
                 seed: int | None = None):
        if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations < 1:
            raise ValueError("simulations must be a positive integer")
        if not math.isfinite(c) or c < 0:
            raise ValueError("c must be finite and non-negative")
        self.simulations = simulations
        self.c = c
        self.rng = random.Random(seed)

    def select_action(self, game: Gomoku) -> int:
        actions = game.legal_actions()
        if not actions:
            raise ValueError("No legal actions in a finished game")
        for player in (game.player, -game.player):
            action = _winning_action(game, player, actions)
            if action is not None:
                return action

        root = _Node(game.player, list(actions))
        for _ in range(self.simulations):
            state = game.clone()
            node = root
            path = [node]
            # Selection: expanded nodes choose the opponent's worst outcome.
            while not state.done and not node.untried:
                node = node.select(self.c)
                state.step(node.action)
                path.append(node)
            # Expansion: random order prevents a fixed low-index bias.
            if not state.done and node.untried:
                index = self.rng.randrange(len(node.untried))
                action = node.untried.pop(index)
                state.step(action)
                child = _Node(state.player, state.legal_actions(), action)
                node.children.append(child)
                node = child
                path.append(node)
            # Rollout: shuffle once, then play until a win or draw.
            rollout = state.legal_actions()
            self.rng.shuffle(rollout)
            while not state.done:
                state.step(rollout.pop())
            _backup(path, state.result(node.player))

        # Robust child: visits first, then root-perspective average reward.
        best = max(root.children, key=lambda child: (
            child.visits, -child.value / child.visits
        ))
        return best.action


@register("mcts")
def _make(simulations: int = 100, c: float = 1.4,
          seed: int | None = None) -> MCTSAgent:
    return MCTSAgent(simulations=simulations, c=c, seed=seed)
