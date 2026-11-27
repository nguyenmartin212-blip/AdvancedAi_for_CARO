import numpy as np
import pytest

from agents.mcts import MCTSAgent, _Node, _backup
from agents.registry import make_agent
from arena.play import play_game
from game.engine import Gomoku


def position(*moves: tuple[int, int]) -> Gomoku:
    game = Gomoku()
    for row, col in moves:
        game.step(row * game.size + col)
    return game


def test_wins_before_blocking():
    game = position((4, 0), (1, 0), (4, 1), (1, 1), (4, 2), (1, 2), (4, 3), (1, 3))
    assert make_agent("mcts", seed=0, simulations=50).select_action(game) == 40


def test_blocks_only_winning_move_at_edge():
    game = position((4, 4), (0, 0), (5, 4), (0, 1), (4, 5), (0, 2), (5, 5), (0, 3))
    assert make_agent("mcts", seed=0, simulations=50).select_action(game) == 4


def test_second_player_fills_gap_to_win_diagonally():
    game = position((0, 0), (1, 7), (0, 2), (2, 6), (0, 4), (4, 4), (8, 0), (5, 3), (8, 2))
    assert game.player == -1
    assert make_agent("mcts", seed=0).select_action(game) == 32


@pytest.mark.parametrize("simulations", [1, 50, 100])
def test_seeded_search_is_legal_and_preserves_input(simulations):
    game = position((4, 4), (3, 4), (4, 5))
    before = game.clone()
    agent = make_agent("mcts", seed=7, simulations=simulations)
    action = agent.select_action(game)
    assert game.is_legal(action)
    assert action == make_agent("mcts", seed=7, simulations=simulations).select_action(game)
    assert np.array_equal(game.board, before.board)
    assert game.history == before.history
    assert (game.player, game.done, game.winner) == (before.player, before.done, before.winner)


def test_backup_and_selection_use_alternating_perspectives():
    root, child, leaf = (_Node(player, []) for player in (1, -1, 1))
    _backup([root, child, leaf], 1)
    assert [node.value for node in (root, child, leaf)] == [1, -1, 1]
    assert [node.visits for node in (root, child, leaf)] == [1, 1, 1]
    opponent_win = _Node(-1, [], visits=1, value=1)
    root.children = [opponent_win, child]
    root.visits = 2
    assert root.select(c=0) is child
    # Đến lượt đối thủ, họ cũng chọn kết quả có lợi nhất cho mình.
    child.children = [leaf, _Node(1, [], visits=1, value=-1)]
    child.visits = 2
    assert child.select(c=0) is child.children[1]
    _backup([root, child, leaf], 0)
    assert leaf.visits == 2 and leaf.value == 1


def test_uct_explores_less_visited_children():
    root = _Node(1, [], visits=11)
    root.children = [_Node(-1, [], visits=10), _Node(-1, [], visits=1)]
    assert root.select(c=1.4) is root.children[1]


def test_search_handles_last_move_draw_and_finished_game():
    game = Gomoku(size=3, k=3)
    for action in [4, 0, 2, 6, 3, 5, 1, 7]:
        game.step(action)
    agent = MCTSAgent(seed=0, simulations=50)
    assert agent.select_action(game) == 8
    game.step(8)
    assert game.done and game.winner == 0
    with pytest.raises(ValueError, match="đã kết thúc"):
        agent.select_action(game)


@pytest.mark.parametrize("params", [
    {"simulations": 0}, {"simulations": -1}, {"simulations": 1.5},
    {"simulations": True}, {"c": -1}, {"c": float("nan")}, {"c": float("inf")},
])
def test_rejects_invalid_budget(params):
    with pytest.raises(ValueError):
        MCTSAgent(**params)


def test_beats_random_with_paired_openings():
    wins = 0
    for seed in range(3):
        for side in (1, -1):
            mcts = make_agent("mcts", seed=seed, simulations=50)
            baseline = make_agent("random", seed=seed)
            x, o = (mcts, baseline) if side == 1 else (baseline, mcts)
            winner, _ = play_game(x, o, opening_moves=2, seed=seed)
            wins += winner == side
    assert wins > 3
