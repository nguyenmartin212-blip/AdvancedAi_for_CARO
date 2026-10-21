"""Play one game between two agents. Returns (winner, moves)."""
from __future__ import annotations

import random

from game.engine import Gomoku


def play_game(agent_x, agent_o, size=9, k=5, opening_moves=0, seed=None):
    """agent_x moves first. Optional random opening (same stones can be replayed
    with swapped sides by passing the same seed). Returns (winner in {1,-1,0}, history)."""
    g = Gomoku(size, k)
    rng = random.Random(seed)
    for _ in range(opening_moves):
        g.step(rng.choice(g.candidate_moves(2) if g.history else g.legal_actions()))
        if g.done:
            return g.winner, list(g.history)
    agents = {1: agent_x, -1: agent_o}
    while not g.done:
        g.step(agents[g.player].select_action(g))
    return g.winner, list(g.history)
