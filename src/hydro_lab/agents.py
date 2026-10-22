"""S2.11 agent interface and safe inference-only episode evaluation.

No policy is allowed to receive the environment's privileged evaluation_truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable
import numpy as np

from .environment import HydroLabEnv


@runtime_checkable
class Agent(Protocol):
    """Policy contract: choose an action from an observable state only."""

    def act(self, observation: np.ndarray, *, deterministic: bool = True) -> np.ndarray:
        ...


@dataclass(frozen=True)
class ConstantAgent:
    """Deterministic benchmark; normalized actions correspond to pump speeds."""

    action: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def act(self, observation: np.ndarray, *, deterministic: bool = True) -> np.ndarray:
        return np.asarray(self.action, dtype=np.float32).copy()


@dataclass
class EpisodeResult:
    seed: int
    return_um: float = 0.0
    steps: int = 0
    terminated: bool = False
    truncated: bool = False
    costs_um: dict[str, float] = field(default_factory=lambda: {
        'energy_um': 0.0, 'deficit_um': 0.0, 'maneuver_um': 0.0, 'terminal_um': 0.0
    })
    energy_kwh: float = 0.0
    served_m3: float = 0.0
    unserved_m3: float = 0.0
    interventions: int = 0
    intervention_distance_total: float = 0.0
    traces: list[dict] = field(default_factory=list)


def evaluate_episode(agent: Agent, *, seed: int, max_steps: int = 96,
                     env: HydroLabEnv | None = None) -> EpisodeResult:
    """Evaluate without training, recording requested vs executed actions.

    A fresh environment is used by default. Do not reuse training seeds for final tests.
    """
    environment = env if env is not None else HydroLabEnv(max_steps=max_steps)
    obs, _ = environment.reset(seed=seed)
    result = EpisodeResult(seed=seed)
    while True:
        # Copy prevents an agent from modifying the environment's observation.
        action = np.asarray(agent.act(obs.copy(), deterministic=True), dtype=np.float32)
        if action.shape != (3,) or not np.all(np.isfinite(action)) or np.any(np.abs(action) > 1):
            raise ValueError('Agent action must be finite, shape (3,), within [-1,1]')
        obs, reward, terminated, truncated, info = environment.step(action)
        result.steps += 1
        result.return_um += float(reward)
        result.terminated = bool(terminated)
        result.truncated = bool(truncated)
        for key in result.costs_um:
            result.costs_um[key] += float(info['costs'].get(key, 0.0))
        result.energy_kwh += float(info.get('energy_kwh', 0.0))
        result.served_m3 += float(info.get('served_m3', 0.0))
        result.unserved_m3 += float(info.get('unserved_m3', 0.0))
        if info.get('intervention_reason') is not None:
            result.interventions += 1
        result.intervention_distance_total += float(info.get('intervention_distance', 0.0))
        # Deliberately whitelist fields: never persist evaluation_truth in policy traces.
        result.traces.append({
            'step': result.steps, 'reward_um': float(reward),
            'requested': tuple(info['action_requested']),
            'executed': tuple(info['action_executed']),
            'intervention_reason': info.get('intervention_reason'),
            'costs_um': dict(info['costs']),
        })
        if terminated or truncated:
            return result
