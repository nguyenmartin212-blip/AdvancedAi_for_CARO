"""Common agent interface + Level-1 Random baseline."""
from __future__ import annotations

import random


class Agent:
    name = "agent"

    def select_action(self, game) -> int:
        """Return a legal action for game.player. Must NOT mutate `game`."""
        raise NotImplementedError

    def reset(self) -> None:  # optional hook between games
        pass


class RandomAgent(Agent):
    name = "random"

    def __init__(self, seed: int | None = None):
        self.rng = random.Random(seed)

    def select_action(self, game) -> int:
        return self.rng.choice(game.legal_actions())
