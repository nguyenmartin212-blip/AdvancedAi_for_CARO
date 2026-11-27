from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest

from scripts.web_app import create_server


@pytest.fixture()
def web_url(tmp_path):
    server = create_server("127.0.0.1", 0, log_dir=tmp_path)
    host, port = server.server_address[:2]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as resp:
        assert resp.status == 200
        return json.loads(resp.read().decode("utf-8"))


def _post_step(base_url: str, payload: dict) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"{base_url}/api/step",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read().decode("utf-8"))


def test_index_and_info_endpoints(web_url):
    with urllib.request.urlopen(f"{web_url}/", timeout=5) as resp:
        html = resp.read().decode("utf-8")
        assert resp.status == 200
        assert "Người đấu AI" in html and "AI đấu AI" in html
        assert "--x-red" in html and "--o-black" in html and 'id="grid"' in html

    info = _get_json(f"{web_url}/api/info")
    assert info["size"] == 9 and info["k"] == 5
    for bot in ("random", "heuristic", "alphabeta", "mcts"):
        assert bot in info["agents"]


def test_human_move_validation_and_ai_reply(web_url):
    code, step1 = _post_step(web_url, {"moves": [], "action": 40})
    assert code == 200
    assert step1["moves"] == [40]
    assert step1["player"] == -1
    assert not step1["done"]

    # Reject occupied cell and out-of-bounds action at trust boundary
    bad_occ, _ = _post_step(web_url, {"moves": [40], "action": 40})
    bad_oob, _ = _post_step(web_url, {"moves": [40], "action": 99})
    bad_bot, _ = _post_step(web_url, {"moves": [40], "agent": "unknown_bot"})
    assert bad_occ == 400 and bad_oob == 400 and bad_bot == 400

    code_ai, step2 = _post_step(web_url, {"moves": step1["moves"], "agent": "heuristic", "seed": 0})
    assert code_ai == 200
    assert len(step2["moves"]) == 2
    assert step2["actor"] == "heuristic"


def test_ai_vs_ai_full_game_reaches_terminal_with_winning_line(web_url):
    moves: list[int] = []
    state = None
    for turn in range(81):
        bot = "heuristic" if turn % 2 == 0 else "random"
        code, state = _post_step(web_url, {"moves": moves, "agent": bot, "seed": 3})
        assert code == 200
        moves = state["moves"]
        if state["done"]:
            break

    assert state is not None and state["done"]
    if state["winner"] != 0:
        assert len(state["winning_cells"]) >= 5


def test_random_opening_moves_diversify_matches_across_seeds(web_url):
    c1, s1 = _post_step(web_url, {"moves": [], "opening_moves": 2, "seed": 1})
    c2, s2 = _post_step(web_url, {"moves": [], "opening_moves": 2, "seed": 2})
    assert c1 == 200 and c2 == 200
    assert len(s1["moves"]) == 2 and len(s2["moves"]) == 2
    assert s1["moves"] != s2["moves"]


def test_series_runner_and_logs_stats_endpoints(web_url):
    req = urllib.request.Request(
        f"{web_url}/api/series",
        data=json.dumps({"agents": ["heuristic", "random"], "games_per_pair": 4, "seed": 0}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        assert resp.status == 200
        report = json.loads(resp.read().decode("utf-8"))

    assert report["total_games"] == 4
    assert "heuristic" in report["summary"] and "random" in report["summary"]
    assert report["summary"]["heuristic"]["games"] == 4
    assert "web_matches" in report["runs"]

    fetched = _get_json(f"{web_url}/api/logs?run=web_matches")
    assert fetched["total_games"] == 4
    assert fetched["avg_moves"] >= 5.0
    assert len(fetched["recent_games"]) == 4


def test_log_game_move_history_and_safe_download(web_url):
    sample = {
        "mode": "human",
        "agent_x": "human",
        "agent_o": "heuristic",
        "winner": 1,
        "moves": [40, 31, 41, 32, 42, 33, 43, 34, 44],
        "seed": 7,
        "times_x": [],
        "times_o": [0.001, 0.001, 0.001, 0.001],
        "move_log": [{"step": 1, "side": "X", "actor": "bạn", "r": 4, "c": 4, "action": 40, "ms": 0, "work": 0}],
    }
    req = urllib.request.Request(
        f"{web_url}/api/log_game",
        data=json.dumps(sample).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200

    report = _get_json(f"{web_url}/api/logs?run=web_matches")
    assert report["recent_games"][0]["seed"] == 7
    assert report["recent_games"][0]["move_log"][0]["action"] == 40

    with urllib.request.urlopen(f"{web_url}/api/download_log?run=web_matches", timeout=5) as dl:
        assert dl.status == 200
        line = json.loads(dl.read().decode("utf-8").splitlines()[-1])
        assert line["moves"] == sample["moves"]

    with pytest.raises(urllib.error.HTTPError) as bad_dl:
        urllib.request.urlopen(f"{web_url}/api/download_log?run=../secret", timeout=5)
    assert bad_dl.value.code == 400
