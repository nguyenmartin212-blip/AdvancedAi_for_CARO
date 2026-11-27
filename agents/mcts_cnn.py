"""Level-7 AlphaGo/AlphaZero-inspired PUCT agent combining MCTS with Policy-Value CNN.

Uses `CNNAgent` (`checkpoints/cnn_9x9.pt`) in two ways:
- Policy head `P(s, a)` guides PUCT selection over local candidate moves.
- Value head `V(s)` in [-1, 1] replaces noisy uniform random rollouts at leaves,
  paired with exact 1-ply win and unstoppable open-four detection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from pathlib import Path
import random
import time

from agents.base import Agent
from agents.cnn import BOARD_SIZE, CNNAgent
from agents.registry import register
from game.engine import Gomoku


@dataclass
class _PUCTNode:
    player: int
    action: int | None = None
    prior: float = 1.0
    children: list[_PUCTNode] = field(default_factory=list)
    visits: int = 0
    value_sum: float = 0.0
    expanded: bool = False
    terminal_value: float | None = None

    def select(self, c_puct: float) -> _PUCTNode:
        sqrt_n = math.sqrt(max(1, self.visits))
        return max(
            self.children,
            key=lambda ch: (
                (-ch.value_sum / ch.visits if ch.visits else 0.0)
                + c_puct * ch.prior * sqrt_n / (1 + ch.visits)
            ),
        )


def _backup(path: list[_PUCTNode], leaf_value: float) -> None:
    """Propagate `leaf_value` (from `path[-1].player`'s view), flipping sign per ply."""
    val = leaf_value
    for node in reversed(path):
        node.visits += 1
        node.value_sum += val
        val = -val


def _winning_moves(game: Gomoku, player: int, actions: list[int]) -> list[int]:
    """Return all actions in `actions` that win immediately for `player`."""
    probe = game.clone()
    probe.player = player
    wins: list[int] = []
    for act in actions:
        _, reward, _ = probe.step(act)
        if reward:
            wins.append(act)
        probe.undo()
    return wins


class MCTSCNNAgent(Agent):
    name = "mcts_cnn"

    def __init__(
        self,
        simulations: int = 56,
        c_puct: float = 1.5,
        time_limit: float | None = None,
        max_children: int = 12,
        checkpoint: str | Path | None = None,
        seed: int | None = None,
        device: str = "cpu",
    ):
        if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations < 1:
            raise ValueError("simulations must be a positive integer")
        if not math.isfinite(c_puct) or c_puct < 0:
            raise ValueError("c_puct must be finite and non-negative")
        if time_limit is not None and (
            isinstance(time_limit, bool) or not math.isfinite(time_limit) or time_limit <= 0
        ):
            raise ValueError("time_limit must be a positive finite number or None")
        if isinstance(max_children, bool) or not isinstance(max_children, int) or max_children < 1:
            raise ValueError("max_children must be a positive integer")

        self.net = CNNAgent(checkpoint=checkpoint, temperature=0.0, seed=seed, device=device)
        self.simulations = simulations
        self.c_puct = float(c_puct)
        self.time_limit = float(time_limit) if time_limit is not None else None
        self.max_children = max_children
        self.rng = random.Random(seed)
        self.last_simulations = 0

    def _expand(self, node: _PUCTNode, state: Gomoku, *, is_root: bool = False) -> float:
        node.expanded = True
        if state.done:
            node.terminal_value = float(state.result(state.player))
            return node.terminal_value

        cands = state.candidate_moves(2)
        if not is_root:
            own_wins = _winning_moves(state, state.player, cands)
            if own_wins:
                node.terminal_value = 1.0
                return 1.0
            opp_wins = _winning_moves(state, -state.player, cands)
            if len(opp_wins) >= 2:
                node.terminal_value = -1.0
                return -1.0
            if len(opp_wins) == 1:
                _, val = self.net.predict(state)
                node.children = [_PUCTNode(-state.player, opp_wins[0], 1.0)]
                return val

        probs, val = self.net.predict(state)
        ordered = sorted(cands, key=lambda a: float(probs[a]), reverse=True)[: self.max_children]
        p_sum = sum(float(probs[a]) for a in ordered)
        priors = (
            [float(probs[a]) / p_sum for a in ordered]
            if p_sum > 0.0
            else [1.0 / len(ordered)] * len(ordered)
        )
        node.children = [_PUCTNode(-state.player, a, p) for a, p in zip(ordered, priors)]
        return val

    def select_action(self, game: Gomoku) -> int:
        if game.size != BOARD_SIZE:
            raise ValueError(f"MCTSCNNAgent requires a {BOARD_SIZE}x{BOARD_SIZE} board")
        if game.is_terminal():
            raise ValueError("No legal actions in a finished game")

        cands = game.candidate_moves(2)
        if len(cands) == 1:
            self.last_simulations = 0
            return cands[0]

        for side in (game.player, -game.player):
            wins = _winning_moves(game, side, cands)
            if wins:
                self.last_simulations = 0
                return wins[0]

        deadline = (time.perf_counter() + self.time_limit) if self.time_limit is not None else None
        root = _PUCTNode(player=game.player)
        _backup([root], self._expand(root, game, is_root=True))
        sims = 1

        while True:
            if deadline is not None:
                if sims > 1 and (time.perf_counter() >= deadline or sims >= 5000):
                    break
            elif sims >= self.simulations:
                break

            state = game.clone()
            node = root
            path = [root]
            while node.expanded and node.children:
                node = node.select(self.c_puct)
                state.step(node.action)
                path.append(node)

            leaf_val = node.terminal_value if node.expanded else self._expand(node, state)
            _backup(path, leaf_val)
            sims += 1

        self.last_simulations = sims
        best_key = max(
            (ch.visits, round(-ch.value_sum / ch.visits, 6) if ch.visits else -1.0)
            for ch in root.children
        )
        ties = [
            ch.action
            for ch in root.children
            if (ch.visits, round(-ch.value_sum / ch.visits, 6) if ch.visits else -1.0) == best_key
        ]
        return self.rng.choice(ties)


@register("mcts_cnn")
def _make(
    simulations: int = 56,
    c_puct: float = 1.5,
    time_limit: float | None = None,
    max_children: int = 12,
    checkpoint: str | Path | None = None,
    seed: int | None = None,
    device: str = "cpu",
) -> MCTSCNNAgent:
    return MCTSCNNAgent(
        simulations=simulations,
        c_puct=c_puct,
        time_limit=time_limit,
        max_children=max_children,
        checkpoint=checkpoint,
        seed=seed,
        device=device,
    )
