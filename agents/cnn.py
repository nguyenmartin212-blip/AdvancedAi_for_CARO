"""Level-5 Supervised Policy-Value CNN agent for 9x9 Gomoku.

PyTorch is imported lazily so environments with only numpy/pytest can still
import `agents` and run Levels 1-4 without error.
"""
from __future__ import annotations

from pathlib import Path
import random

import numpy as np

from agents.base import Agent
from agents.registry import register
from game.engine import Gomoku

BOARD_SIZE = 9
DEFAULT_CHECKPOINT = Path(__file__).resolve().parent.parent / "checkpoints" / "cnn_9x9.pt"


def _require_torch():
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
    except ImportError as exc:
        raise ImportError(
            "PyTorch is required for CNNAgent. Install with: pip install torch"
        ) from exc
    return torch, nn, F


def build_policy_value_net(channels: int = 48):
    """Compact residual policy-value CNN over `Gomoku.encode()` shape (3, 9, 9)."""
    torch, nn, F = _require_torch()

    class _ResBlock(nn.Module):
        def __init__(self, ch: int):
            super().__init__()
            self.conv1 = nn.Conv2d(ch, ch, kernel_size=3, padding=1, bias=False)
            self.bn1 = nn.BatchNorm2d(ch)
            self.conv2 = nn.Conv2d(ch, ch, kernel_size=3, padding=1, bias=False)
            self.bn2 = nn.BatchNorm2d(ch)

        def forward(self, x):
            out = F.relu(self.bn1(self.conv1(x)))
            out = self.bn2(self.conv2(out))
            return F.relu(x + out)

    class PolicyValueNet(nn.Module):
        def __init__(self, ch: int = channels):
            super().__init__()
            cells = BOARD_SIZE * BOARD_SIZE
            self.stem = nn.Sequential(
                nn.Conv2d(3, ch, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(ch),
                nn.ReLU(),
            )
            self.trunk = nn.Sequential(_ResBlock(ch), _ResBlock(ch))
            self.policy_head = nn.Sequential(
                nn.Conv2d(ch, 2, kernel_size=1, bias=False),
                nn.BatchNorm2d(2),
                nn.ReLU(),
                nn.Flatten(),
                nn.Linear(2 * cells, cells),
            )
            self.value_head = nn.Sequential(
                nn.Conv2d(ch, 1, kernel_size=1, bias=False),
                nn.BatchNorm2d(1),
                nn.ReLU(),
                nn.Flatten(),
                nn.Linear(cells, 48),
                nn.ReLU(),
                nn.Linear(48, 1),
                nn.Tanh(),
            )

        def forward(self, x):
            feat = self.trunk(self.stem(x))
            return self.policy_head(feat), self.value_head(feat).squeeze(-1)

    return PolicyValueNet(channels)


class CNNAgent(Agent):
    name = "cnn"

    def __init__(
        self,
        checkpoint: str | Path | None = None,
        temperature: float = 0.0,
        seed: int | None = None,
        device: str = "cpu",
    ):
        if temperature < 0:
            raise ValueError("temperature must be non-negative")
        torch, _, _ = _require_torch()
        ckpt_path = Path(checkpoint) if checkpoint is not None else DEFAULT_CHECKPOINT
        if not ckpt_path.is_file():
            raise FileNotFoundError(
                f"Trained CNN checkpoint not found at '{ckpt_path}'. "
                "Run `python -m train.train_cnn` first."
            )
        self.checkpoint_path = ckpt_path
        self.temperature = float(temperature)
        self.rng = random.Random(seed)
        self.device = torch.device(device)

        payload = torch.load(ckpt_path, map_location=self.device, weights_only=True)
        channels = int(payload.get("channels", 48))
        self.model = build_policy_value_net(channels=channels).to(self.device)
        self.model.load_state_dict(payload["model_state"])
        self.model.eval()

    def predict(self, game: Gomoku) -> tuple[np.ndarray, float]:
        """Return (masked_action_probs[81], state_value in [-1, 1]) for current player."""
        if game.size != BOARD_SIZE:
            raise ValueError(f"CNNAgent requires a {BOARD_SIZE}x{BOARD_SIZE} board")
        legal = game.legal_actions()
        if not legal:
            raise ValueError("No legal actions in a finished game")

        torch, _, _ = _require_torch()
        planes = torch.from_numpy(game.encode()).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits, value = self.model(planes)
        raw_logits = logits[0].cpu().numpy().astype(np.float64)

        masked = np.full_like(raw_logits, -np.inf)
        masked[legal] = raw_logits[legal]
        shifted = masked - np.max(masked[legal])
        probs = np.zeros_like(raw_logits, dtype=np.float64)
        exp_legal = np.exp(shifted[legal])
        probs[legal] = exp_legal / exp_legal.sum()
        return probs.astype(np.float32), float(value.item())

    def select_action(self, game: Gomoku) -> int:
        probs, _ = self.predict(game)
        legal = game.legal_actions()
        if len(legal) == 1:
            return legal[0]

        if self.temperature == 0.0:
            best_prob = float(probs[legal].max())
            ties = [a for a in legal if abs(float(probs[a]) - best_prob) <= 1e-7]
            return self.rng.choice(ties)

        weights = [float(probs[a]) ** (1.0 / self.temperature) for a in legal]
        return self.rng.choices(legal, weights=weights, k=1)[0]


@register("cnn")
def _make(
    checkpoint: str | Path | None = None,
    temperature: float = 0.0,
    seed: int | None = None,
    device: str = "cpu",
) -> CNNAgent:
    return CNNAgent(
        checkpoint=checkpoint,
        temperature=temperature,
        seed=seed,
        device=device,
    )
