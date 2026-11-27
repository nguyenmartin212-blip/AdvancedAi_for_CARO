"""Generate expert Gomoku games across full-board openings and train Level-5 CNN.

    python -X utf8 -m train.train_cnn --games 600 --epochs 18 --seed 42
"""
from __future__ import annotations

import argparse
from pathlib import Path
import platform
import random
import time

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

from agents.alphabeta import AlphaBetaAgent
from agents.base import RandomAgent
from agents.cnn import BOARD_SIZE, DEFAULT_CHECKPOINT, build_policy_value_net
from agents.heuristic import HeuristicAgent, winning_action
from game.engine import Gomoku
from utils.logger import JsonlLogger
from utils.seed import set_seed


def _transform_sample(
    planes: np.ndarray,
    action: int,
    rot_k: int,
    flip: bool,
) -> tuple[np.ndarray, int]:
    """Apply one of the 8 D4 board symmetries to (3, 9, 9) planes and flat action."""
    p = np.rot90(planes, k=rot_k, axes=(1, 2))
    r, c = divmod(action, BOARD_SIZE)
    for _ in range(rot_k % 4):
        r, c = BOARD_SIZE - 1 - c, r
    if flip:
        p = p[:, :, ::-1]
        c = BOARD_SIZE - 1 - c
    return np.ascontiguousarray(p, dtype=np.float32), r * BOARD_SIZE + c


def _mask_occupied_logits(logits: torch.Tensor, planes: torch.Tensor) -> torch.Tensor:
    """Mask already-occupied cells so training loss matches CNNAgent.predict()."""
    occupied = (planes[:, 0] + planes[:, 1]).flatten(1) > 0.5
    return logits.masked_fill(occupied, -1e9)


def generate_expert_games(
    num_games: int = 600,
    expert_depth: int = 2,
    seed: int = 42,
) -> list[list[tuple[bytes, int, np.ndarray, int, float, float]]]:
    """Simulate complete games and label each state with Alpha-Beta policy + game outcome.

    Matches `arena/play.py` full-board first-stone openings (`legal_actions()`) so edge
    and corner fights are covered, and upweights must-win / must-block tactical states.
    """
    rng = random.Random(seed)
    games_data: list[list[tuple[bytes, int, np.ndarray, int, float, float]]] = []

    for g_idx in range(num_games):
        game = Gomoku(BOARD_SIZE, 5)
        opening_plies = rng.choice((0, 1, 2, 2, 2, 2, 3, 4))
        for ply_i in range(opening_plies):
            cands = ([40] if g_idx % 5 == 0 else game.legal_actions()) if ply_i == 0 else game.candidate_moves(2)
            game.step(rng.choice(cands))
            if game.done:
                break

        expert = AlphaBetaAgent(depth=expert_depth, candidate_limit=10, seed=seed + g_idx)
        mode = g_idx % 20
        if mode < 7:
            opp = AlphaBetaAgent(depth=expert_depth, candidate_limit=10, seed=seed + 10_000 + g_idx)
            expert_side = 0
        elif mode < 16:
            opp = HeuristicAgent(seed=seed + 20_000 + g_idx)
            expert_side = 1 if (g_idx % 2 == 0) else -1
        else:
            opp = RandomAgent(seed=seed + 30_000 + g_idx)
            expert_side = 1 if (g_idx % 2 == 0) else -1

        trajectory: list[tuple[bytes, int, np.ndarray, int, float]] = []
        while not game.done:
            state_key = game.board.tobytes()
            player = game.player
            planes = game.encode()
            cands = game.candidate_moves(2)

            # Reuse immediate win/block check to avoid redundant tree search on forced plies.
            forced = winning_action(game, player, cands)
            if forced is None:
                forced = winning_action(game, -player, cands)
            if forced is not None:
                label_action = forced
                weight = 3.5
            else:
                label_action = expert.select_action(game)
                weight = 1.0

            trajectory.append((state_key, player, planes, label_action, weight))
            chosen = label_action if (expert_side == 0 or player == expert_side) else opp.select_action(game)
            game.step(chosen)

        winner = game.winner
        games_data.append([
            (key, player, planes, action, float(winner * player), weight)
            for key, player, planes, action, weight in trajectory
        ])

    return games_data


def split_and_deduplicate(
    games_data: list[list[tuple]],
    seed: int = 42,
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
) -> tuple[dict[str, tuple[np.ndarray, ...]], dict[str, int]]:
    """Split strictly at the game level first, then deduplicate board states across splits."""
    rng = random.Random(seed)
    indices = list(range(len(games_data)))
    rng.shuffle(indices)

    n = len(indices)
    n_train = max(1, int(n * ratios[0]))
    n_val = max(1, int(n * ratios[1]))
    split_ids = {
        "train": indices[:n_train],
        "val": indices[n_train:n_train + n_val],
        "test": indices[n_train + n_val:],
    }

    seen_states: set[tuple[bytes, int]] = set()
    raw_positions = 0
    dedup_removed = 0
    splits: dict[str, tuple[np.ndarray, ...]] = {}

    for split_name in ("train", "val", "test"):
        xs, ys_policy, ys_value, ys_weight = [], [], [], []
        for g_id in split_ids[split_name]:
            for key, player, planes, action, z, w in games_data[g_id]:
                raw_positions += 1
                sig = (key, player)
                if sig in seen_states:
                    dedup_removed += 1
                    continue
                seen_states.add(sig)
                if split_name == "train":
                    for rot_k in range(4):
                        for flip in (False, True):
                            aug_p, aug_a = _transform_sample(planes, action, rot_k, flip)
                            xs.append(aug_p)
                            ys_policy.append(aug_a)
                            ys_value.append(z)
                            ys_weight.append(w)
                else:
                    xs.append(planes)
                    ys_policy.append(action)
                    ys_value.append(z)

        base = (
            np.asarray(xs, dtype=np.float32),
            np.asarray(ys_policy, dtype=np.int64),
            np.asarray(ys_value, dtype=np.float32),
        )
        splits[split_name] = (*base, np.asarray(ys_weight, dtype=np.float32)) if split_name == "train" else base

    meta = {
        "total_games": n,
        "train_games": len(split_ids["train"]),
        "val_games": len(split_ids["val"]),
        "test_games": len(split_ids["test"]),
        "raw_positions": raw_positions,
        "unique_positions": raw_positions - dedup_removed,
        "dedup_removed": dedup_removed,
        "train_samples_augmented": int(len(splits["train"][0])),
        "val_samples": int(len(splits["val"][0])),
        "test_samples": int(len(splits["test"][0])),
    }
    return splits, meta


def _evaluate_split(
    model: nn.Module,
    arrays: tuple[np.ndarray, ...],
    device: torch.device,
) -> dict[str, float]:
    model.eval()
    x, y_p, y_v = arrays[:3]
    if len(x) == 0:
        return {"loss": 0.0, "top1_acc": 0.0, "top3_acc": 0.0, "value_mse": 0.0}
    tx = torch.from_numpy(x).to(device)
    tp = torch.from_numpy(y_p).to(device)
    tv = torch.from_numpy(y_v).to(device)
    with torch.no_grad():
        raw_logits, pred_v = model(tx)
        logits = _mask_occupied_logits(raw_logits, tx)
        p_loss = F.cross_entropy(logits, tp)
        v_loss = F.mse_loss(pred_v, tv)
        top1 = (logits.argmax(dim=-1) == tp).float().mean().item()
        top3_idx = logits.topk(k=min(3, logits.shape[-1]), dim=-1).indices
        top3 = (top3_idx == tp.unsqueeze(-1)).any(dim=-1).float().mean().item()
    return {
        "loss": float((p_loss + 0.5 * v_loss).item()),
        "top1_acc": float(top1),
        "top3_acc": float(top3),
        "value_mse": float(v_loss.item()),
    }


def train_cnn(
    *,
    num_games: int = 600,
    expert_depth: int = 2,
    channels: int = 48,
    epochs: int = 18,
    batch_size: int = 256,
    lr: float = 3e-3,
    seed: int = 42,
    checkpoint_path: Path | str = DEFAULT_CHECKPOINT,
) -> dict:
    set_seed(seed)
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    hw_desc = torch.cuda.get_device_name(0) if device.type == "cuda" else f"CPU ({platform.processor() or platform.machine()})"

    t_gen = time.perf_counter()
    games_data = generate_expert_games(num_games=num_games, expert_depth=expert_depth, seed=seed)
    splits, meta = split_and_deduplicate(games_data, seed=seed)
    gen_seconds = time.perf_counter() - t_gen

    train_ds = TensorDataset(
        torch.from_numpy(splits["train"][0]),
        torch.from_numpy(splits["train"][1]),
        torch.from_numpy(splits["train"][2]),
        torch.from_numpy(splits["train"][3]),
    )
    gen_rng = torch.Generator().manual_seed(seed)
    loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, generator=gen_rng)

    model = build_policy_value_net(channels=channels).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=3e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=max(1, epochs), eta_min=1e-4)

    ckpt_path = Path(checkpoint_path)
    ckpt_path.parent.mkdir(parents=True, exist_ok=True)
    best_val_loss = float("inf")
    best_state = None
    best_epoch = 0

    t_train = time.perf_counter()
    with JsonlLogger("train_cnn") as logger:
        logger.log(
            run="train_cnn",
            event="dataset_ready",
            seed=seed,
            expert_depth=expert_depth,
            channels=channels,
            hardware=hw_desc,
            gen_seconds=round(gen_seconds, 2),
            **meta,
        )
        print(f"Thiết bị: {hw_desc} | Sinh dữ liệu: {gen_seconds:.1f}s | {meta}", flush=True)

        for epoch in range(1, epochs + 1):
            model.train()
            ep_loss = 0.0
            ep_correct = 0
            ep_count = 0
            for bx, bp, bv, bw in loader:
                bx, bp, bv, bw = bx.to(device), bp.to(device), bv.to(device), bw.to(device)
                optimizer.zero_grad()
                raw_logits, pred_v = model(bx)
                logits = _mask_occupied_logits(raw_logits, bx)
                p_loss = (F.cross_entropy(logits, bp, reduction="none") * bw).sum() / bw.sum()
                loss = p_loss + 0.5 * F.mse_loss(pred_v, bv)
                loss.backward()
                optimizer.step()

                ep_loss += float(loss.item()) * len(bx)
                ep_correct += int((logits.argmax(dim=-1) == bp).sum().item())
                ep_count += len(bx)
            scheduler.step()

            train_loss = ep_loss / max(1, ep_count)
            train_acc = ep_correct / max(1, ep_count)
            val_metrics = _evaluate_split(model, splits["val"], device)

            if val_metrics["loss"] < best_val_loss:
                best_val_loss = val_metrics["loss"]
                best_epoch = epoch
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

            logger.log(
                run="train_cnn",
                event="epoch",
                epoch=epoch,
                train_loss=round(train_loss, 4),
                train_acc=round(train_acc, 4),
                val_loss=round(val_metrics["loss"], 4),
                val_top1_acc=round(val_metrics["top1_acc"], 4),
                val_top3_acc=round(val_metrics["top3_acc"], 4),
                val_value_mse=round(val_metrics["value_mse"], 4),
            )
            if epoch in (1, 5, 10, 15, epochs):
                print(
                    f"Epoch {epoch:02d}/{epochs} | train_loss={train_loss:.4f} acc={train_acc:.3f} "
                    f"| val_loss={val_metrics['loss']:.4f} top1={val_metrics['top1_acc']:.3f} top3={val_metrics['top3_acc']:.3f}",
                    flush=True,
                )

        train_seconds = time.perf_counter() - t_train
        assert best_state is not None
        model.load_state_dict(best_state)
        test_metrics = _evaluate_split(model, splits["test"], device)

        summary = {
            "seed": seed,
            "channels": channels,
            "epochs": epochs,
            "best_epoch": best_epoch,
            "hardware": hw_desc,
            "gen_seconds": round(gen_seconds, 2),
            "train_seconds": round(train_seconds, 2),
            "dataset": meta,
            "test_metrics": {k: round(v, 4) for k, v in test_metrics.items()},
        }
        torch.save(
            {
                "model_state": best_state,
                "channels": channels,
                "seed": seed,
                "summary": summary,
            },
            ckpt_path,
        )
        logger.log(run="train_cnn", event="finished", checkpoint=str(ckpt_path), **summary)
        print(
            f"Đã lưu checkpoint tốt nhất (epoch {best_epoch}) tại {ckpt_path} "
            f"| train_time={train_seconds:.1f}s | test={summary['test_metrics']}",
            flush=True,
        )
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description="Sinh dữ liệu chuyên gia và huấn luyện CNN Level 5 cho Caro 9x9.")
    ap.add_argument("--games", type=int, default=600, help="số ván chuyên gia tự sinh (mặc định: 600)")
    ap.add_argument("--expert-depth", type=int, default=2, help="độ sâu Alpha-Beta sinh nhãn (mặc định: 2)")
    ap.add_argument("--channels", type=int, default=48, help="số kênh thân mạng CNN (mặc định: 48)")
    ap.add_argument("--epochs", type=int, default=18, help="số epoch huấn luyện (mặc định: 18)")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=3e-3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=DEFAULT_CHECKPOINT)
    args = ap.parse_args()

    train_cnn(
        num_games=args.games,
        expert_depth=args.expert_depth,
        channels=args.channels,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=args.seed,
        checkpoint_path=args.out,
    )


if __name__ == "__main__":
    main()
