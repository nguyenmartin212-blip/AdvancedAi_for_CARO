import numpy as np
import pytest

from game.engine import Gomoku
from agents.base import RandomAgent
from arena.play import play_game


def play(g, moves):
    for m in moves:
        g.step(m)


def rc(g, r, c):
    return r * g.size + c


def alternate(g, line_cells, other_cells):
    """X plays line_cells, O plays other_cells in turn; returns after X's last move."""
    for i, cell in enumerate(line_cells):
        g.step(cell)
        if i < len(other_cells) and not g.done:
            g.step(other_cells[i])


def test_horizontal_win():
    g = Gomoku()
    alternate(g, [rc(g, 4, c) for c in range(5)], [rc(g, 0, c) for c in range(4)])
    assert g.done and g.winner == 1 and g.result(1) == 1 and g.result(-1) == -1


def test_vertical_win_second_player():
    g = Gomoku()
    g.step(rc(g, 8, 8))
    for i in range(5):
        g.step(rc(g, i, 0))               # O
        if i < 4:
            g.step(rc(g, 8, i))           # X (avoid making 5 itself)
    assert g.done and g.winner == -1


def test_diagonal_and_antidiagonal():
    g = Gomoku()
    alternate(g, [rc(g, i, i) for i in range(5)], [rc(g, 0, 8 - i) for i in range(4)])
    assert g.winner == 1
    g = Gomoku()
    alternate(g, [rc(g, i, 8 - i) for i in range(5)], [rc(g, 8, i) for i in range(4)])
    assert g.winner == 1


def test_four_is_not_win_and_overline_wins():
    g = Gomoku()
    alternate(g, [rc(g, 4, c) for c in (0, 1, 2, 3)], [rc(g, 0, c) for c in range(4)])
    assert not g.done
    # fill gap to make 6 in a row: 0,1,2,3,_,5,6 then play 4 -> 7 in a row (freestyle win)
    g = Gomoku()
    alternate(g, [rc(g, 4, c) for c in (0, 1, 2, 3, 5, 6, 4)], [rc(g, 0, c) for c in (0, 2, 4, 6, 8, 1)][:5] + [rc(g, 8, 0)])
    assert g.done and g.winner == 1


def test_draw_3x3():
    g = Gomoku(size=3, k=3)
    play(g, [4, 0, 2, 6, 3, 5, 1, 7, 8])
    assert g.done and g.winner == 0 and g.result(1) == 0


def test_illegal_moves_raise():
    g = Gomoku()
    g.step(0)
    for bad in (0, -1, 81, 100):
        with pytest.raises(ValueError):
            g.step(bad)
    g2 = Gomoku()
    alternate(g2, [rc(g2, 4, c) for c in range(5)], [rc(g2, 0, c) for c in range(4)])
    with pytest.raises(ValueError):
        g2.step(rc(g2, 8, 8))            # game over
    assert g2.legal_actions() == []


def test_undo_restores_state():
    g = Gomoku()
    alternate(g, [rc(g, 4, c) for c in range(5)], [rc(g, 0, c) for c in range(4)])
    assert g.done
    g.undo()
    assert not g.done and g.winner == 0 and g.player == 1
    assert g.board[4, 4] == 0 and len(g.history) == 8


def test_clone_independent():
    g = Gomoku()
    g.step(40)
    h = g.clone()
    h.step(41)
    assert g.board[4, 5] == 0 and len(g.history) == 1 and h.player == 1


def test_candidate_moves():
    g = Gomoku()
    assert g.candidate_moves() == [40]
    g.step(40)
    cm = set(g.candidate_moves(2))
    assert 40 not in cm and len(cm) == 24
    assert all(g.is_legal(m) for m in cm)


def test_encode_is_player_independent():
    g = Gomoku()
    g.step(0)            # X at (0,0); O to move
    e = g.encode()
    assert e[1, 0, 0] == 1 and e[0].sum() == 0 and e[2, 0, 0] == 1


def test_random_games_always_terminate_and_are_legal():
    for s in range(30):
        w, hist = play_game(RandomAgent(s), RandomAgent(s + 100), seed=s)
        assert w in (-1, 0, 1) and len(set(hist)) == len(hist)
