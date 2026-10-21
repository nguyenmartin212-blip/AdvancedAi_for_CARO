import json

from agents.registry import available, make_agent
from game.engine import Gomoku
from utils.config import load_config
from utils.logger import JsonlLogger


def test_registry_random():
    assert "random" in available()
    a = make_agent("random", seed=1)
    g = Gomoku()
    assert a.select_action(g) in g.legal_actions()


def test_logger_roundtrip(tmp_path):
    with JsonlLogger("t", tmp_path) as lg:
        lg.log(a=1, b="x")
    rec = json.loads((tmp_path / "t.jsonl").read_text().splitlines()[0])
    assert rec["a"] == 1 and "ts" in rec


def test_config():
    cfg = load_config()
    assert cfg["game"] == {"size": 9, "k": 5}
