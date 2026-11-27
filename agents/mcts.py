"""Tìm kiếm UCT với mô phỏng ngẫu nhiên có seed và kiểm tra thắng/chặn ở gốc.

Mỗi nút lưu tổng kết quả từ góc nhìn bên sắp đi tại nút đó.
Khi chọn con, đổi dấu giá trị trung bình của con; khi cập nhật ngược, đổi dấu qua mỗi lượt.
Cây được tạo lại sau mỗi lần gọi; mọi nước mô phỏng đều dùng bản sao.
Khi đặt time_limit, bot áp dụng cả giới hạn số mô phỏng và giới hạn thời gian mềm.
Kiểm tra chiến thuật ở gốc và mô phỏng đã bắt đầu có thể làm vượt thời gian yêu cầu.
last_simulations đếm số mô phỏng đã hoàn tất; nước chiến thuật có giá trị 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
import time

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
    """Kết quả được tính từ góc nhìn bên sắp đi tại nút cuối."""
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
                 seed: int | None = None, time_limit: float | None = None):
        if isinstance(simulations, bool) or not isinstance(simulations, int) or simulations < 1:
            raise ValueError("simulations phải là số nguyên dương")
        if not math.isfinite(c) or c < 0:
            raise ValueError("c phải hữu hạn và không âm")
        if time_limit is not None and (isinstance(time_limit, bool)
                                       or not math.isfinite(time_limit) or time_limit <= 0):
            raise ValueError("time_limit phải là số hữu hạn lớn hơn 0")
        self.time_limit = time_limit
        self.last_simulations = 0
        self.simulations = simulations
        self.c = c
        self.rng = random.Random(seed)

    def select_action(self, game: Gomoku) -> int:
        self.last_simulations = 0
        deadline = None if self.time_limit is None else time.perf_counter() + self.time_limit
        actions = game.legal_actions()
        if not actions:
            raise ValueError("Ván cờ đã kết thúc, không còn nước đi hợp lệ")
        for player in (game.player, -game.player):
            action = _winning_action(game, player, actions)
            if action is not None:
                return action

        root = _Node(game.player, list(actions))
        for _ in range(self.simulations):
            # Hoàn tất mô phỏng đã bắt đầu; kiểm tra thời hạn giữa hai lần mô phỏng.
            if deadline is not None and time.perf_counter() >= deadline:
                break
            state = game.clone()
            node = root
            path = [node]
            # Chọn nút: nút đã mở rộng ưu tiên kết quả bất lợi cho đối thủ.
            while not state.done and not node.untried:
                node = node.select(self.c)
                state.step(node.action)
                path.append(node)
            # Mở rộng: chọn thứ tự ngẫu nhiên để tránh thiên về ô có chỉ số nhỏ.
            if not state.done and node.untried:
                index = self.rng.randrange(len(node.untried))
                action = node.untried.pop(index)
                state.step(action)
                child = _Node(state.player, state.legal_actions(), action)
                node.children.append(child)
                node = child
                path.append(node)
            # Mô phỏng: xáo trộn một lần rồi chơi đến khi thắng hoặc hòa.
            rollout = state.legal_actions()
            self.rng.shuffle(rollout)
            while not state.done:
                state.step(rollout.pop())
            _backup(path, state.result(node.player))

            self.last_simulations += 1

        # Kiểm tra ở gốc có thể dùng hết ngân sách nhỏ trước khi kịp mô phỏng.
        if not root.children:
            return self.rng.choice(actions)

        # Ưu tiên con có nhiều lượt thăm nhất, rồi so điểm trung bình từ góc nhìn gốc.
        best = max(root.children, key=lambda child: (
            child.visits, -child.value / child.visits
        ))
        return best.action


@register("mcts")
def _make(simulations: int = 100, c: float = 1.4,
          seed: int | None = None, time_limit: float | None = None) -> MCTSAgent:
    return MCTSAgent(simulations=simulations, c=c, seed=seed, time_limit=time_limit)
