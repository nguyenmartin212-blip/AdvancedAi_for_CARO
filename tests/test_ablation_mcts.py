import json

import pytest

from scripts.ablation_mcts import main, run_ablation


def test_small_grid_logs_real_games_and_replays_seeded_outcomes(tmp_path):
    arguments = dict(simulations=[2, 3], exploration=[0.7, 1.4], opponents=["random"],
                     games_per_pair=2, seed=7, log_dir=tmp_path)
    first = run_ablation(**arguments, run_name="grid")
    second = run_ablation(**arguments, run_name="repeat")
    assert len(first) == 4
    for a, b in zip(first, second):
        for key in ("wins", "draws", "losses", "score"):
            assert a[key] == b[key]
        raw = [json.loads(line) for line in (tmp_path / (a["raw_run"] + ".jsonl")).read_text(encoding="utf-8").splitlines()]
        assert len(raw) == a["games"] == 2
        assert (raw[0]["agent_x"], raw[1]["agent_o"]) == ("mcts", "mcts")
        assert raw[0]["seed"] == raw[1]["seed"] == 7
        assert raw[0]["moves"][:2] == raw[1]["moves"][:2]
        assert sum(row["winner"] == (1 if row["agent_x"] == "mcts" else -1) for row in raw) == a["wins"]
        assert 0 <= a["work_per_move"] <= a["simulations"]
        assert 0 <= a["ci_low"] <= a["score"] <= a["ci_high"] <= 1
    metadata = [json.loads(line) for line in (tmp_path / "grid.jsonl").read_text(encoding="utf-8").splitlines()]
    assert metadata[0]["event"] == "metadata"
    assert metadata[-1]["total_games"] == 8
    before = (tmp_path / "grid.jsonl").read_bytes()
    with pytest.raises(FileExistsError):
        run_ablation(**arguments, run_name="grid")
    assert (tmp_path / "grid.jsonl").read_bytes() == before


@pytest.mark.parametrize("kwargs", [
    {"games_per_pair": 1}, {"games_per_pair": True},
    {"simulations": []}, {"simulations": [0]}, {"simulations": [True]},
    {"exploration": []}, {"exploration": [float("nan")]},
    {"opponents": []}, {"opponents": ["mcts"]},
    {"simulations": [100, 100]}, {"exploration": [0.7, 0.7]},
    {"run_name": "../outside"},
])
def test_rejects_invalid_design_before_writing_logs(tmp_path, kwargs):
    with pytest.raises(ValueError):
        run_ablation(log_dir=tmp_path, **kwargs)
    assert not list(tmp_path.iterdir())


def test_cli_reports_invalid_design(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["-n", "3", "--log-dir", str(tmp_path)])
    assert error.value.code == 2
