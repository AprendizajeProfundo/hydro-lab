"""S2.5: reproducible, paired-policy scientific acceptance benchmarks.

Policy API receives observations only. Environment diagnostics are consumed only
by the evaluator after each action, never passed into policy functions.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable
import json
from pathlib import Path
import numpy as np
from .environment import HydroLabEnv
from .observations import OBSERVATION_NAMES

Policy = Callable[[np.ndarray], np.ndarray]


def constant_policy(observation: np.ndarray) -> np.ndarray:
    """u=(.8,.8,.8); ignores its observation by design."""
    return np.zeros(3, dtype=np.float32)


def demand_feedback_policy(observation: np.ndarray) -> np.ndarray:
    """A simple, non-optimized, observation-only demand feedback baseline.

    Uses measured demand (index 2) and measured tank volumes (indices 0,1).
    It does not access latent health, future demand, or evaluation info.
    """
    o = np.asarray(observation, dtype=float)
    demand = float(o[2]); source = float(o[0]); receiver = float(o[1])
    correction = np.clip((demand - .11) * 4.0 + (700. - receiver) / 3000.
                         - (500. - source) / 4000., -.15, .15)
    u = float(np.clip(.8 + correction, .65, .95))
    return np.full(3, (u - .8) / .2, dtype=np.float32)

def health_aware_policy(observation: np.ndarray) -> np.ndarray:
    """Observation-only risk-sensitive controller (experimental heuristic).

    Start from demand feedback and redistribute commanded speed toward pumps
    with larger estimated health. Uses observed health indices 12:15 only;
    never accesses true health or uncertainty hidden from the observation.
    Centering the correction keeps the mean requested speed unchanged before
    clipping. This is not an optimal controller or a proven safety guarantee.
    """
    o = np.asarray(observation, dtype=float)
    if o.shape != (15,) or not np.isfinite(o).all():
        raise ValueError('Expected 15 finite observed features')
    baseline = demand_feedback_policy(o).astype(float)
    health = np.clip(o[12:15], .65, 1.)
    correction = 0.65 * (health - health.mean())
    return np.clip(baseline + correction, -1., 1.).astype(np.float32)

def health_robust_policy(observation: np.ndarray) -> np.ndarray:
    """S2.10 conservative teaching controller; observation-only.

    Shrinks health-based redistribution and bounds its amplitude. This limits
    sensitivity to noisy inspections but cannot guarantee superior reward.
    """
    o = np.asarray(observation, dtype=float)
    if o.shape != (15,) or not np.isfinite(o).all():
        raise ValueError('Expected 15 finite observed features')
    base = demand_feedback_policy(o).astype(float)
    health = np.clip(o[12:15], .65, 1.)
    correction = np.clip(.20 * (health - health.mean()), -.035, .035)
    return np.clip(base + correction, -1., 1.).astype(np.float32)

POLICIES: dict[str, Policy] = {
    'constant': constant_policy,
    'demand_feedback': demand_feedback_policy,
    'health_aware': health_aware_policy,
    'health_robust': health_robust_policy,
}

@dataclass(frozen=True)
class EpisodeMetrics:
    seed: int
    policy: str
    steps: int
    reward: float
    energy_kwh: float
    energy_cost_um: float
    deficit_cost_um: float
    maneuver_cost_um: float
    terminal_cost_um: float
    served_m3: float
    unserved_m3: float
    interventions: int
    safe_shutdowns: int
    max_mass_error_m3: float
    terminated: bool
    truncated: bool
    termination_reason: str | None


def run_episode(seed: int, policy_name: str = 'constant', *, max_steps: int = 96,
                policy: Policy | None = None) -> EpisodeMetrics:
    if policy is None:
        if policy_name not in POLICIES:
            raise ValueError(f'Unknown policy: {policy_name}')
        policy = POLICIES[policy_name]
    env = HydroLabEnv(max_steps=max_steps)
    obs, _ = env.reset(seed=int(seed))
    totals = {key: 0. for key in ('energy_um','deficit_um','maneuver_um','terminal_um')}
    energy = served = unserved = reward_sum = max_mass_error = 0.
    interventions = shutdowns = 0
    terminated = truncated = False
    info = {}
    steps = 0
    try:
        for steps in range(1, max_steps + 1):
            # Only the observable vector is passed to the policy.
            action = np.asarray(policy(obs.copy()), dtype=np.float32)
            obs, reward, terminated, truncated, info = env.step(action)
            reward_sum += float(reward)
            for k in totals:
                totals[k] += float(info['costs'][k])
            energy += float(info.get('energy_kwh', 0.))
            served += float(info.get('served_m3', 0.))
            unserved += float(info.get('unserved_m3', 0.))
            max_mass_error = max(max_mass_error, abs(float(info.get('mass_error_m3', 0.))))
            interventions += info.get('intervention_reason') is not None
            shutdowns += info.get('intervention_reason') == 'SAFE_SHUTDOWN'
            if terminated or truncated:
                break
    finally:
        env.close()
    return EpisodeMetrics(
        seed=int(seed),policy=policy_name,steps=steps,reward=reward_sum,
        energy_kwh=energy,energy_cost_um=totals['energy_um'],
        deficit_cost_um=totals['deficit_um'],maneuver_cost_um=totals['maneuver_um'],
        terminal_cost_um=totals['terminal_um'],served_m3=served,unserved_m3=unserved,
        interventions=int(interventions),safe_shutdowns=int(shutdowns),
        max_mass_error_m3=max_mass_error,terminated=bool(terminated),
        truncated=bool(truncated),termination_reason=info.get('termination_reason'))


def paired_benchmark(seeds: tuple[int,...], policies: tuple[str,...] = ('constant','demand_feedback')) -> dict:
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError('seeds must be nonempty and unique')
    if len(policies) < 2 or len(set(policies)) != len(policies):
        raise ValueError('at least two unique policies are required')
    results = [run_episode(seed, policy) for seed in seeds for policy in policies]
    summary = {}
    for name in policies:
        rows = [r for r in results if r.policy == name]
        summary[name] = {
            'n': len(rows),
            'mean_reward': float(np.mean([r.reward for r in rows])),
            'mean_energy_kwh': float(np.mean([r.energy_kwh for r in rows])),
            'mean_unserved_m3': float(np.mean([r.unserved_m3 for r in rows])),
            'mean_interventions': float(np.mean([r.interventions for r in rows])),
            'terminal_rate': float(np.mean([r.terminated for r in rows])),
        }
    a,b = policies[:2]
    by_key = {(r.seed,r.policy): r for r in results}
    differences = np.array([by_key[s,b].reward - by_key[s,a].reward for s in seeds],dtype=float)
    comparison = {
        'contrast': f'{b} minus {a}',
        'paired_mean_reward_difference': float(np.mean(differences)),
        'paired_sd_reward_difference': float(np.std(differences,ddof=1)) if len(seeds)>1 else None,
        'n_pairs': len(seeds),
    }
    return {'schema':'hydro-lab-s2.5-v1','seeds':list(seeds),'policies':list(policies),
            'observation_names':list(OBSERVATION_NAMES),
            'summary':summary,'comparison':comparison,
            'episodes':[asdict(r) for r in results]}


def save_report(report: dict, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite report: {path}')
    path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    return path
