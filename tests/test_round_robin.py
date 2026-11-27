from __future__ import annotations

import json
import math
import pytest

import agents.registry as registry_mod
from agents.registry import available, make_agent
from arena import round_robin
from arena.play import play_game
from arena.round_robin import (
    format_matrix,
    format_summary,
    head_to_head,
    main,
    run_round_robin,
    side_advantage,
    summarize,
    wilson_ci,
)

REQUIRED_FIELDS = {
    "run",
    "agent_x",
    "agent_o",
    "winner",
    "moves",
    "seed",
    "budget_mode",
    "time_per_move",
    "ts",
}


def test_four_agents_six_pairs_twelve_games_and_log_match(tmp_path):
    bots = ["random", "heuristic", "alphabeta", "mcts"]
    assert set(bots).issubset(set(available()))

    records, summary = run_round_robin(
        bots,
        games_per_pair=2,
        opening_moves=2,
        seed=0,
        budget_mode="compute",
        agent_overrides={"alphabeta": {"depth": 1}, "mcts": {"simulations": 10}},
        run_name="test_rr",
        log_dir=tmp_path,
    )

    log_path = tmp_path / "test_rr.jsonl"
    assert log_path.exists()
    logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 12
    assert len(logged) == 12

    for rec in logged:
        assert REQUIRED_FIELDS.issubset(rec.keys())
        assert rec["run"] == "test_rr"
        assert rec["winner"] in (-1, 0, 1)
        assert isinstance(rec["moves"], list) and len(rec["moves"]) >= 5
        assert isinstance(rec["time_per_move"], float) and rec["time_per_move"] >= 0.0

    # Check 6 pairs, each with 2 swapped-side games sharing the same opening seed & opening moves.
    seen_pairs = set()
    for i in range(0, 12, 2):
        g1, g2 = logged[i], logged[i + 1]
        assert g1["agent_x"] == g2["agent_o"]
        assert g1["agent_o"] == g2["agent_x"]
        assert g1["seed"] == g2["seed"]
        assert g1["moves"][:2] == g2["moves"][:2]
        seen_pairs.add(tuple(sorted((g1["agent_x"], g1["agent_o"]))))
    assert len(seen_pairs) == 6

    # Check W/D/L totals match the JSONL log records exactly.
    from_log = summarize(logged, agent_names=bots)
    total_wins = 0
    total_losses = 0
    total_draws = 0
    for bot in bots:
        assert summary[bot]["wins"] == from_log[bot]["wins"]
        assert summary[bot]["draws"] == from_log[bot]["draws"]
        assert summary[bot]["losses"] == from_log[bot]["losses"]
        assert summary[bot]["wins"] + summary[bot]["draws"] + summary[bot]["losses"] == 6
        total_wins += int(summary[bot]["wins"])
        total_losses += int(summary[bot]["losses"])
        total_draws += int(summary[bot]["draws"])

    assert total_wins == total_losses
    assert total_wins + total_draws // 2 == 12


def test_fresh_agents_created_per_game_and_play_game_reused(monkeypatch, tmp_path):
    created_ids: list[int] = []
    play_calls: list[tuple[str, str, int]] = []
    real_make_agent = round_robin.make_agent
    real_play_game = round_robin.play_game

    def spy_make_agent(name: str, **params):
        agent = real_make_agent(name, **params)
        created_ids.append(id(agent))
        return agent

    def spy_play_game(agent_x, agent_o, size=9, k=5, opening_moves=0, seed=None):
        play_calls.append((agent_x.name, agent_o.name, seed))
        return real_play_game(agent_x, agent_o, size=size, k=k, opening_moves=opening_moves, seed=seed)

    monkeypatch.setattr(round_robin, "make_agent", spy_make_agent)
    monkeypatch.setattr(round_robin, "play_game", spy_play_game)

    records, _ = run_round_robin(
        ["random", "heuristic"],
        games_per_pair=2,
        opening_moves=2,
        seed=5,
        run_name="spy_rr",
        log_dir=tmp_path,
    )
    assert len(records) == 2
    assert len(play_calls) == 2
    assert play_calls[0] == ("random", "heuristic", 5)
    assert play_calls[1] == ("heuristic", "random", 5)
    assert len(created_ids) == 4
    assert len(set(created_ids)) == 4


def test_quick_match_play_game_compatibility():
    a = make_agent("random", seed=1)
    b = make_agent("random", seed=2)
    winner, history = play_game(a, b, size=9, k=5, opening_moves=2, seed=42)
    assert winner in (-1, 0, 1)
    assert isinstance(history, list) and len(history) >= 5
    assert {"alphabeta", "heuristic", "mcts", "random"}.issubset(registry_mod.available())


def test_cli_smoke_test_and_summary_output(tmp_path, capsys):
    main([
        "--agents", "random", "heuristic", "alphabeta", "mcts",
        "-n", "2",
        "--seed", "0",
        "--depth", "1",
        "--simulations", "5",
        "--run", "cli_smoke",
        "--log-dir", str(tmp_path),
    ])
    out = capsys.readouterr().out
    assert "Thắng" in out and "Hòa" in out and "Thua" in out and "Thời gian/nước" in out
    for bot in ("random", "heuristic", "alphabeta", "mcts"):
        assert bot in out
    lines = (tmp_path / "cli_smoke.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12


@pytest.mark.parametrize("bad_args", [
    ["-n", "1"],
    ["-n", "3"],
    ["-n", "0"],
    ["--opening-moves", "-1"],
    ["--depth", "0"],
    ["--simulations", "0"],
])
def test_cli_rejects_invalid_arguments(tmp_path, bad_args):
    with pytest.raises(SystemExit) as exc:
        main(["--agents", "random", "heuristic", "--log-dir", str(tmp_path), *bad_args])
    assert exc.value.code == 2


def test_format_summary_contains_all_columns():
    summary = {
        "random": {"wins": 1, "draws": 0, "losses": 1, "games": 2, "time_per_move": 0.001234},
    }
    table = format_summary(summary)
    assert "random" in table
    assert "0.001234" in table


def test_multiple_runs_append_to_log(tmp_path):
    run_round_robin(["random", "heuristic"], games_per_pair=2, run_name="multi", log_dir=tmp_path)
    run_round_robin(["random", "heuristic"], games_per_pair=2, seed=10, run_name="multi", log_dir=tmp_path)
    lines = (tmp_path / "multi.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 4


def test_metrics_wilson_p95_head_to_head_and_log_roundtrip(tmp_path):
    records, summary = run_round_robin(
        ["random", "heuristic", "mcts"],
        games_per_pair=4,
        seed=2,
        budget_mode="compute",
        agent_overrides={"mcts": {"simulations": 8}},
        run_name="metrics_rr",
        log_dir=tmp_path,
    )
    logged = [json.loads(line) for line in (tmp_path / "metrics_rr.jsonl").read_text(encoding="utf-8").splitlines()]
    from_log = summarize(logged, agent_names=["random", "heuristic", "mcts"])

    for bot in ("random", "heuristic", "mcts"):
        s = summary[bot]
        assert 0.0 <= s["ci_low"] <= s["score"] <= s["ci_high"] <= 1.0
        assert s["p95_time"] >= s["time_per_move"] >= 0.0 or math.isclose(s["p95_time"], s["time_per_move"])
        assert math.isclose(s["score"], from_log[bot]["score"])
        assert math.isclose(s["time_per_move"], from_log[bot]["time_per_move"], abs_tol=1e-5)
        assert math.isclose(s["p95_time"], from_log[bot]["p95_time"], abs_tol=1e-5)
    assert 0.0 < summary["mcts"]["work_per_move"] <= 8.0
    assert summary["mcts"]["work_per_move"] == pytest.approx(from_log["mcts"]["work_per_move"])

    h2h = head_to_head(logged, ["random", "heuristic", "mcts"])
    assert h2h["heuristic"]["random"]["games"] == 4
    assert math.isclose(h2h["heuristic"]["random"]["score"] + h2h["random"]["heuristic"]["score"], 1.0)
    assert "heuristic" in format_matrix(h2h)
    adv = side_advantage(logged)
    assert adv["games"] == 12
    assert adv["x_wins"] + adv["o_wins"] + adv["draws"] == 12
    lo, hi = wilson_ci(1.0, 100)
    assert 0.95 < lo < 1.0 and hi == pytest.approx(1.0)


def test_time_budget_mode_and_invalid_seconds(tmp_path, capsys):
    main([
        "--agents", "random", "alphabeta", "mcts",
        "-n", "2",
        "--budget-mode", "time",
        "--seconds-per-move", "0.02",
        "--matrix",
        "--run", "time_rr",
        "--log-dir", str(tmp_path),
    ])
    out = capsys.readouterr().out
    assert "Ma trận đối đầu" in out and "Lợi thế lượt đi" in out
    rec = json.loads((tmp_path / "time_rr.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert rec["budget_mode"] == "time"
    assert rec["seconds_per_move"] == pytest.approx(0.02)

    with pytest.raises(SystemExit) as exc:
        main(["--agents", "random", "heuristic", "--budget-mode", "time", "--seconds-per-move", "0", "--log-dir", str(tmp_path)])
    assert exc.value.code == 2



def test_native_mcts_time_budget_skips_probe_calibration(monkeypatch):
    params = {"mcts": {"simulations": 123, "c": 0.7}}
    def unexpected_factory(*args, **kwargs):
        raise AssertionError("MCTS đã hỗ trợ thời hạn trực tiếp, không cần hiệu chuẩn số mô phỏng")
    monkeypatch.setattr(round_robin, "make_agent", unexpected_factory)
    round_robin._apply_time_budget(params, 0.03, 9, 5, set())
    assert params["mcts"] == {"simulations": 123, "c": 0.7, "time_limit": 0.03}


def test_work_average_includes_games_with_zero_rollouts():
    records = [
        {"agent_x": "mcts", "agent_o": "random", "winner": 1,
         "times_x": [0.01, 0.01], "times_o": [0.0], "work_x": 8.0},
        {"agent_x": "mcts", "agent_o": "random", "winner": 1,
         "times_x": [0.001, 0.001], "times_o": [0.0], "work_x": 0.0},
    ]
    assert summarize(records)["mcts"]["work_per_move"] == pytest.approx(4.0)
