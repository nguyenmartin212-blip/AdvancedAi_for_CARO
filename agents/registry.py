"""Agent registry: map a name to a factory so arena/UI/CLI can build agents from config.

Each team member registers their agent here:

    @register("alphabeta")
    def _make(depth=3, seed=None, **kw): return AlphaBetaAgent(depth=depth, seed=seed)

Factories are imported lazily so a missing optional dependency (torch, pygame)
does not break the other agents.
"""
from __future__ import annotations

from typing import Callable

from agents.base import Agent, RandomAgent

_REGISTRY: dict[str, Callable[..., Agent]] = {}


def register(name: str):
    def deco(factory: Callable[..., Agent]):
        if name in _REGISTRY:
            raise ValueError(f"Agent '{name}' already registered")
        _REGISTRY[name] = factory
        return factory
    return deco


def make_agent(name: str, **params) -> Agent:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown agent '{name}'. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[name](**params)


def available() -> list[str]:
    return sorted(_REGISTRY)


@register("random")
def _random(seed: int | None = None, **_) -> Agent:
    return RandomAgent(seed)
