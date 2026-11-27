"""Zero-dependency web server & JSON API for 9x9 Gomoku (Human-vs-AI & AI-vs-AI).

Local 1-click / CLI:
    python -X utf8 -m ui.web_app

Cloud deploy (Render / Railway / etc., no Docker needed):
    python -X utf8 -m ui.web_app --host 0.0.0.0 --no-browser
"""
from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import re
import threading
import time
from urllib.parse import parse_qs, urlparse
import webbrowser

from agents.registry import available, make_agent
from arena.round_robin import head_to_head, run_round_robin, side_advantage, summarize
from game.engine import DIRECTIONS, Gomoku
from utils.config import load_config
from utils.logger import LOG_DIR, JsonlLogger

_HTML_PATH = Path(__file__).resolve().parent / "web_index.html"
_RUN_NAME_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,63}$")


def _safe_run_name(name: str) -> str:
    if not isinstance(name, str) or not _RUN_NAME_RE.fullmatch(name):
        raise ValueError("Tên file log chỉ được chứa chữ cái, chữ số, dấu chấm, gạch dưới hoặc gạch ngang; không được bắt đầu bằng dấu chấm.")
    return name


def _winning_cells(game: Gomoku) -> list[list[int]]:
    """Return coordinates [[r, c], ...] of the winning >=k line if game has a winner."""
    if not game.winner or not game.history:
        return []
    r0, c0 = divmod(game.history[-1], game.size)
    p = int(game.board[r0, c0])
    for dr, dc in DIRECTIONS:
        cells = [[r0, c0]]
        for sign in (-1, 1):
            r, c = r0 + sign * dr, c0 + sign * dc
            while 0 <= r < game.size and 0 <= c < game.size and game.board[r, c] == p:
                if sign < 0:
                    cells.insert(0, [r, c])
                else:
                    cells.append([r, c])
                r += sign * dr
                c += sign * dc
        if len(cells) >= game.k:
            return cells
    return []


def inspect_agents(cfg: dict) -> tuple[list[str], dict[str, str]]:
    """Return (usable_agent_names, unavailable_reasons) without crashing on optional deps."""
    usable: list[str] = []
    skipped: dict[str, str] = {}
    cfg_agents = cfg.get("agents", {})
    ordered = [a for a in cfg_agents if a in available()] + [
        a for a in available() if a not in cfg_agents
    ]
    for name in ordered:
        try:
            make_agent(name, seed=0, **dict(cfg_agents.get(name, {})))
            usable.append(name)
        except Exception as exc:  # pragma: no cover - optional torch/checkpoint missing
            skipped[name] = str(exc)
    return usable, skipped


def apply_step(payload: dict, cfg: dict) -> dict:
    """Stateless turn handler: validate history, then apply opening, human action, or AI move."""
    size, k = int(cfg["game"]["size"]), int(cfg["game"]["k"])
    moves = payload.get("moves", [])
    if not isinstance(moves, list) or len(moves) > size * size:
        raise ValueError("Danh sách nước đi (moves) không hợp lệ.")

    game = Gomoku(size=size, k=k)
    for m in moves:
        if isinstance(m, bool) or not isinstance(m, int) or not game.is_legal(m):
            raise ValueError(f"Lịch sử ván cờ chứa nước không hợp lệ: {m}")
        game.step(m)

    action = payload.get("action")
    agent_name = payload.get("agent")
    opening_moves = int(payload.get("opening_moves", 0) or 0)
    seed_raw = payload.get("seed", 0)
    seed = 0 if seed_raw is None else int(seed_raw)
    elapsed_ms = 0.0
    work = 0.0
    actor = "none"

    if opening_moves > 0 and not game.history:
        if opening_moves > 6:
            raise ValueError("opening_moves phải nằm trong đoạn [0, 6].")
        rng = random.Random(seed)
        for _ in range(opening_moves):
            cands = game.candidate_moves(2) if game.history else game.legal_actions()
            game.step(rng.choice(cands))
            if game.done:
                break
        actor = "opening"
    elif action is not None:
        if isinstance(action, bool) or not isinstance(action, int) or not game.is_legal(action):
            raise ValueError(f"Nước đi không hợp lệ hoặc ô đã có quân: {action}")
        game.step(action)
        actor = "human"
    elif agent_name is not None:
        if game.done:
            raise ValueError("Ván cờ đã kết thúc.")
        if not isinstance(agent_name, str) or agent_name not in available():
            raise ValueError(f"Agent không tồn tại: {agent_name}")
        params = dict(cfg.get("agents", {}).get(agent_name, {}))
        bot = make_agent(agent_name, seed=seed + len(game.history), **params)
        t0 = time.perf_counter()
        chosen = bot.select_action(game)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if not game.is_legal(chosen):
            raise RuntimeError(f"Agent '{agent_name}' trả nước bất hợp lệ: {chosen}")
        game.step(chosen)
        raw_work = getattr(bot, "last_nodes", None)
        if raw_work is None:
            raw_work = getattr(bot, "last_simulations", None)
        if raw_work is None:
            raw_work = getattr(bot, "simulations", 0)
        work = float(raw_work or 0)
        actor = agent_name

    return {
        "size": size,
        "k": k,
        "moves": game.history,
        "board": game.board.tolist(),
        "player": int(game.player),
        "winner": int(game.winner),
        "done": bool(game.done),
        "last_action": game.history[-1] if game.history else None,
        "winning_cells": _winning_cells(game),
        "actor": actor,
        "elapsed_ms": round(elapsed_ms, 2),
        "work": round(work, 1),
    }


def _read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_log_report(log_dir: Path, run_name: str | None = None) -> dict:
    """Summarize JSONL match logs from `log_dir` and return recent playable history."""
    log_dir.mkdir(parents=True, exist_ok=True)
    if run_name:
        _safe_run_name(run_name)
    # Chỉ đưa log ván cờ vào lịch sử, bỏ qua metadata và bảng tổng hợp thí nghiệm.
    games_by_run = {}
    for path in log_dir.glob("*.jsonl"):
        records = [row for row in _read_jsonl(path)
                   if isinstance(row, dict) and {"agent_x", "agent_o", "winner", "moves"} <= row.keys()]
        if records:
            games_by_run[path.stem] = records
    runs = sorted(games_by_run)
    default_run = (
        "web_matches" if "web_matches" in runs
        else ("rr_compute_100" if "rr_compute_100" in runs else (runs[0] if runs else ""))
    )
    selected = run_name if (run_name in runs) else default_run
    records = games_by_run.get(selected, [])
    summary = summarize(records) if records else {}
    agents = list(summary.keys())
    lengths = [len(r.get("moves", [])) for r in records if isinstance(r.get("moves"), list)]
    recent = [
        {
            "index": idx + 1,
            "ts": r.get("ts", ""),
            "agent_x": r.get("agent_x", "?"),
            "agent_o": r.get("agent_o", "?"),
            "winner": int(r.get("winner", 0)),
            "moves": r.get("moves", []),
            "seed": int(r.get("seed", 0)),
            "move_log": r.get("move_log", []),
        }
        for idx, r in enumerate(records)
    ][-50:][::-1]
    return {
        "runs": runs,
        "selected": selected,
        "log_file": f"logs/{selected}.jsonl" if selected else "",
        "total_games": len(records),
        "avg_moves": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
        "min_moves": min(lengths) if lengths else 0,
        "max_moves": max(lengths) if lengths else 0,
        "summary": summary,
        "head_to_head": head_to_head(records, agents) if len(agents) >= 2 else {},
        "side_advantage": side_advantage(records),
        "recent_games": recent,
    }


def run_batch_series(payload: dict, log_dir: Path) -> dict:
    """Run an N-game swapped-side series between selected agents and append to web_matches.jsonl."""
    agents_list = payload.get("agents")
    if not isinstance(agents_list, list) or len(agents_list) < 2:
        raise ValueError("Cần chọn ít nhất 2 agent khác nhau để chạy thống kê đối đầu.")
    dedup_agents = list(dict.fromkeys(str(a) for a in agents_list))
    if len(dedup_agents) < 2:
        raise ValueError("Hai agent đối đầu phải khác tên nhau để thống kê bảng vòng tròn.")
    run_name = _safe_run_name(str(payload.get("run", "web_matches") or "web_matches"))
    records, _ = run_round_robin(
        dedup_agents,
        games_per_pair=int(payload.get("games_per_pair", 10)),
        opening_moves=int(payload.get("opening_moves", 2)),
        seed=int(payload.get("seed", 0)),
        budget_mode="compute",
        run_name=run_name,
        log_dir=log_dir,
    )
    report = build_log_report(log_dir, run_name)
    report["batch_games_added"] = len(records)
    return report


def _log_interactive_game(payload: dict, log_dir: Path) -> dict:
    tx = [round(float(t), 6) for t in payload.get("times_x", []) if isinstance(t, (int, float))]
    to = [round(float(t), 6) for t in payload.get("times_o", []) if isinstance(t, (int, float))]
    both = tx + to
    raw_mlog = payload.get("move_log", [])
    with JsonlLogger("web_matches", log_dir) as logger:
        logger.log(
            run="web_matches",
            mode=str(payload.get("mode", "interactive")),
            agent_x=str(payload.get("agent_x", "human")),
            agent_o=str(payload.get("agent_o", "human")),
            winner=int(payload.get("winner", 0)),
            moves=[int(m) for m in payload.get("moves", [])],
            seed=int(payload.get("seed", 0)),
            budget_mode="interactive",
            time_per_move=sum(both) / len(both) if both else 0.0,
            times_x=tx,
            times_o=to,
            work_x=round(float(payload.get("work_x", 0.0)), 2),
            work_o=round(float(payload.get("work_o", 0.0)), 2),
            move_log=raw_mlog if isinstance(raw_mlog, list) else [],
        )
    return {"ok": True}


def make_handler(cfg: dict | None = None, log_dir: Path | str | None = None):
    loaded_cfg = cfg if cfg is not None else load_config()
    target_log_dir = Path(log_dir) if log_dir is not None else LOG_DIR
    html_bytes = _HTML_PATH.read_bytes()

    class CaroHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            return

        def _send_bytes(self, status: int, content_type: str, raw: bytes, extra_headers: dict[str, str] | None = None) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            for k, v in (extra_headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(raw)

        def _send_json(self, status: int, data: dict) -> None:
            self._send_bytes(status, "application/json; charset=utf-8", json.dumps(data, ensure_ascii=False).encode("utf-8"))

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            if path in ("/", "/index.html"):
                self._send_bytes(HTTPStatus.OK, "text/html; charset=utf-8", html_bytes)
                return
            if path in ("/api/info", "/healthz"):
                usable, skipped = inspect_agents(loaded_cfg)
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "status": "ok",
                        "size": loaded_cfg["game"]["size"],
                        "k": loaded_cfg["game"]["k"],
                        "agents": usable,
                        "unavailable": skipped,
                    },
                )
                return
            if path == "/api/logs":
                run_param = parse_qs(parsed.query).get("run", [None])[0]
                try:
                    self._send_json(HTTPStatus.OK, build_log_report(target_log_dir, run_param))
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            if path == "/api/download_log":
                run_param = parse_qs(parsed.query).get("run", ["web_matches"])[0]
                try:
                    safe_run = _safe_run_name(run_param)
                except ValueError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                file_path = target_log_dir / f"{safe_run}.jsonl"
                if not file_path.is_file():
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": f"Chưa có file log {safe_run}.jsonl"})
                    return
                self._send_bytes(
                    HTTPStatus.OK,
                    "application/x-ndjson; charset=utf-8",
                    file_path.read_bytes(),
                    {"Content-Disposition": f'attachment; filename="{safe_run}.jsonl"'},
                )
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

        def do_POST(self) -> None:
            path = self.path.split("?", 1)[0]
            routes = {
                "/api/step": lambda p: apply_step(p, loaded_cfg),
                "/api/series": lambda p: run_batch_series(p, target_log_dir),
                "/api/log_game": lambda p: _log_interactive_game(p, target_log_dir),
            }
            handler_fn = routes.get(path)
            if handler_fn is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 65_536:
                    self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Payload quá lớn"})
                    return
                payload = json.loads((self.rfile.read(length) if length > 0 else b"{}").decode("utf-8"))
                if not isinstance(payload, dict):
                    raise ValueError("JSON body phải là một object.")
                self._send_json(HTTPStatus.OK, handler_fn(payload))
            except (ValueError, json.JSONDecodeError) as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
            except Exception as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    return CaroHandler


def create_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    cfg: dict | None = None,
    log_dir: Path | str | None = None,
) -> ThreadingHTTPServer:
    """Bind ThreadingHTTPServer; fall back to an ephemeral free port if requested local port is busy."""
    handler = make_handler(cfg, log_dir=log_dir)
    try:
        return ThreadingHTTPServer((host, port), handler)
    except OSError:
        if port != 0 and host in ("127.0.0.1", "localhost"):
            return ThreadingHTTPServer((host, 0), handler)
        raise


def main(argv: list[str] | None = None) -> None:
    default_port = int(os.environ.get("PORT", "8000"))
    ap = argparse.ArgumentParser(description="Chạy giao diện Web Caro 9x9 (Người đấu AI & AI đấu AI).")
    ap.add_argument("--host", default="127.0.0.1", help="địa chỉ lắng nghe (mặc định: 127.0.0.1; cloud: 0.0.0.0)")
    ap.add_argument("--port", type=int, default=default_port, help="cổng HTTP (mặc định: $PORT hoặc 8000)")
    ap.add_argument("--no-browser", action="store_true", help="không tự động mở trình duyệt")
    args = ap.parse_args(argv)

    server = create_server(args.host, args.port)
    bound_host, bound_port = server.server_address[:2]
    browse_host = "127.0.0.1" if bound_host in ("0.0.0.0", "::") else bound_host
    url = f"http://{browse_host}:{bound_port}"

    print(f"Caro 9x9 Web AI đang chạy tại: {url}")
    print("Nhấn Ctrl+C để dừng máy chủ.")
    if not args.no_browser and args.host in ("127.0.0.1", "localhost"):
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng máy chủ Web Caro.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
