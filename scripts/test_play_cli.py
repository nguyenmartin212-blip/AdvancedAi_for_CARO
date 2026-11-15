import pytest

from agents.base import Agent
from agents.registry import make_agent
from game.engine import Gomoku
from scripts.play_cli import main, play


class ScriptedAgent(Agent):
    name = "scripted"

    def __init__(self, actions):
        self.actions = iter(actions)

    def select_action(self, game):
        return next(self.actions)


def enter(monkeypatch, moves):
    entries = iter(moves)
    monkeypatch.setattr("builtins.input", lambda _: next(entries))


def test_full_human_win_with_invalid_input(monkeypatch, capsys):
    enter(monkeypatch, ["abc", "1", "0 1 2", "-1 0", "0 9", "0 0",
                        "0 0", "0 1", "0 2", "0 3", "0 4"])
    game = Gomoku()
    assert play(game, ScriptedAgent([9, 10, 11, 12])) == 1
    assert game.history == [0, 9, 1, 10, 2, 11, 3, 12, 4]
    output = capsys.readouterr().out
    assert "hai số nguyên" in output
    assert "từ 0 đến 8" in output
    assert "đã có quân" in output
    assert "Bạn thắng (X)" in output
    assert output.count(game.render().splitlines()[0]) == 10


def test_ai_first_and_ai_win(monkeypatch, capsys):
    enter(monkeypatch, ["1 0", "1 1", "1 2", "1 3"])
    game = Gomoku()
    assert play(game, ScriptedAgent([0, 1, 2, 3, 4]), human_player=-1) == 1
    assert game.history[0] == 0 and game.done
    assert "AI thắng (X)" in capsys.readouterr().out


def test_full_draw(monkeypatch, capsys):
    enter(monkeypatch, ["1 1", "0 2", "1 0", "0 1", "2 2"])
    game = Gomoku(size=3, k=3)
    assert play(game, ScriptedAgent([0, 6, 5, 7])) == 0
    assert game.done and len(game.history) == 9
    assert "Hòa" in capsys.readouterr().out


@pytest.mark.parametrize("reason", [EOFError, KeyboardInterrupt])
def test_input_interrupt_exits_cleanly(monkeypatch, capsys, reason):
    def interrupt(_):
        raise reason
    monkeypatch.setattr("builtins.input", interrupt)
    game = Gomoku()
    play(game, make_agent("random"))
    assert not game.history
    assert "Đã dừng" in capsys.readouterr().out


def test_cli_builds_seeded_mcts_with_budget(monkeypatch, capsys):
    enter(monkeypatch, ["q"])
    main(["mcts", "--side", "o", "--seed", "7", "--simulations", "2", "--c", "0"])
    output = capsys.readouterr().out
    assert "Bạn cầm quân O" in output and "AI (mcts)" in output
    assert "Đã dừng" in output


@pytest.mark.parametrize("args", [
    ["unknown"], ["mcts", "--simulations", "0"], ["mcts", "--c", "nan"],
    ["random", "--simulations", "50"],
])
def test_cli_rejects_invalid_arguments(args):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == 2
