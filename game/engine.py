"""Gomoku engine (freestyle: >= k in a row wins, no forbidden moves).

Conventions
-----------
- board[r, c] in {0, 1, -1}; 1 = first player (black), -1 = second player (white).
- action = r * size + c  (int in [0, size*size)).
- result(player) is from the given player's point of view: +1 win, -1 loss, 0 draw/ongoing.
"""
from __future__ import annotations

import numpy as np

DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


class Gomoku:
    def __init__(self, size: int = 9, k: int = 5):
        self.size = size
        self.k = k
        self.reset()

    # ------------------------------------------------------------------ core
    def reset(self) -> np.ndarray:
        self.board = np.zeros((self.size, self.size), dtype=np.int8)
        self.player = 1          # player to move
        self.winner = 0          # 1, -1 or 0
        self.done = False
        self.history: list[int] = []
        return self.board

    def legal_actions(self) -> list[int]:
        if self.done:
            return []
        rs, cs = np.nonzero(self.board == 0)
        return (rs * self.size + cs).tolist()

    def is_legal(self, action: int) -> bool:
        if self.done or not (0 <= action < self.size * self.size):
            return False
        return self.board[divmod(action, self.size)] == 0

    def step(self, action: int):
        """Play `action` for the current player.

        Returns (board, reward, done) where reward is from the view of the player
        who just moved (+1 if that move won, else 0). Illegal moves raise ValueError.
        """
        if not self.is_legal(action):
            raise ValueError(f"Illegal action {action}")
        r, c = divmod(action, self.size)
        self.board[r, c] = self.player
        self.history.append(action)
        reward = 0
        if self._wins_at(r, c):
            self.winner = self.player
            self.done = True
            reward = 1
        elif len(self.history) == self.size * self.size:
            self.done = True   # draw
        self.player = -self.player
        return self.board, reward, self.done

    def undo(self) -> None:
        if not self.history:
            raise ValueError("Nothing to undo")
        action = self.history.pop()
        r, c = divmod(action, self.size)
        self.board[r, c] = 0
        self.player = -self.player
        self.winner = 0
        self.done = False

    def is_terminal(self) -> bool:
        return self.done

    def result(self, player: int | None = None) -> int:
        """Outcome from `player`'s view (default: player to move). 0 if draw or ongoing."""
        if player is None:
            player = self.player
        return int(self.winner * player)

    def clone(self) -> "Gomoku":
        g = Gomoku.__new__(Gomoku)
        g.size, g.k = self.size, self.k
        g.board = self.board.copy()
        g.player, g.winner, g.done = self.player, self.winner, self.done
        g.history = list(self.history)
        return g

    # ------------------------------------------------------------- win check
    def _count(self, r: int, c: int, dr: int, dc: int, p: int) -> int:
        n = 0
        r, c = r + dr, c + dc
        while 0 <= r < self.size and 0 <= c < self.size and self.board[r, c] == p:
            n += 1
            r, c = r + dr, c + dc
        return n

    def _wins_at(self, r: int, c: int) -> bool:
        """Incremental check: only look at 4 lines through the last move."""
        p = self.board[r, c]
        for dr, dc in DIRECTIONS:
            if 1 + self._count(r, c, dr, dc, p) + self._count(r, c, -dr, -dc, p) >= self.k:
                return True
        return False

    # ------------------------------------------------------- helpers for AI
    def candidate_moves(self, radius: int = 2) -> list[int]:
        """Empty cells within `radius` of any stone (centre if board empty)."""
        if self.done:
            return []
        if not self.history:
            return [(self.size // 2) * self.size + self.size // 2]
        occ = self.board != 0
        mask = np.zeros_like(occ)
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                src = occ[max(0, -dr):self.size - max(0, dr), max(0, -dc):self.size - max(0, dc)]
                mask[max(0, dr):self.size - max(0, -dr), max(0, dc):self.size - max(0, -dc)] |= src
        rs, cs = np.nonzero(mask & (self.board == 0))
        return (rs * self.size + cs).tolist()

    def encode(self) -> np.ndarray:
        """Player-independent planes, shape (3, size, size), float32.

        plane 0: stones of the player to move, plane 1: opponent stones,
        plane 2: last move (one-hot). Same net can serve both sides.
        """
        planes = np.zeros((3, self.size, self.size), dtype=np.float32)
        planes[0] = self.board == self.player
        planes[1] = self.board == -self.player
        if self.history:
            planes[2][divmod(self.history[-1], self.size)] = 1.0
        return planes

    # --------------------------------------------------------------- display
    def render(self) -> str:
        sym = {0: ".", 1: "X", -1: "O"}
        head = "   " + " ".join(f"{c:2d}" for c in range(self.size))
        rows = [f"{r:2d} " + " ".join(f" {sym[int(v)]}" for v in self.board[r]) for r in range(self.size)]
        return "\n".join([head] + rows)

    def __repr__(self) -> str:
        return self.render()
