"""S2.8 paired experiments: identical seeds, policy/robot factorial design.

Robot costs are subtracted from reward by EpisodeSession.step. Policies see
only noisy observations. The experiment does not claim common-random-number
coupling after divergent trajectories; it uses matched initial seeds.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np
from .control_center import EpisodeSession
from .termination_diagnostics import summarize_terminations

@dataclass(frozen=True)
class ActiveResult:
    seed: int
    policy: str
    robot_policy: str
    steps: int
    net_reward_um: float
    robot_cost_um: float
    energy_kwh: float
    unserved_m3: float
    interventions: int
    inspections: int
    terminated: bool
    termination_reason: str | None = None


def run_active_episode(seed: int, *, policy: str='health_aware', robot_policy: str='uncertainty', max_steps: int=96) -> ActiveResult:
    session = EpisodeSession(seed=seed, policy_name=policy, robot_policy=robot_policy, max_steps=max_steps)
    try:
        session.advance(max_steps)
        report = session.report()
        return ActiveResult(seed, policy, robot_policy, len(session.records),
            report['reward_total'], session.robot.cost_um,
            report['total_energy_kwh'], report['total_unserved_m3'],
            report['interventions'], session.robot.inspections, session.terminated,
            (report.get('termination_reason') or next(
                (rec.get('termination_reason') for rec in reversed(session.records)
                 if rec.get('terminated') and rec.get('termination_reason')), None)))
    finally:
        session.close()


def active_paired_benchmark(seeds: tuple[int,...], *, max_steps: int=96) -> dict:
    """Four arms isolate policy effect, robot effect and interaction.

    Arms: feedback/off, aware/off, feedback/uncertainty, aware/uncertainty.
    The primary contrast isolates inspection value for the aware controller.
    """
    if not seeds or len(set(seeds)) != len(seeds) or any(int(s)<0 for s in seeds):
        raise ValueError('Provide distinct nonnegative seeds')
    arms = [('demand_feedback','off'), ('health_aware','off'),
            ('demand_feedback','uncertainty'), ('health_aware','uncertainty')]
    rows = [run_active_episode(int(seed),policy=p,robot_policy=r,max_steps=max_steps)
            for seed in seeds for p,r in arms]
    by = {(v.seed,v.policy,v.robot_policy):v for v in rows}
    differences = np.array([by[s,'health_aware','uncertainty'].net_reward_um -
                            by[s,'health_aware','off'].net_reward_um for s in seeds])
    summary = {}
    for p,r in arms:
        subset=[v for v in rows if (v.policy,v.robot_policy)==(p,r)]
        summary[f'{p}/{r}']={k:float(np.mean([getattr(v,k) for v in subset]))
            for k in ('net_reward_um','robot_cost_um','energy_kwh','unserved_m3','interventions','inspections','terminated','steps')}
        summary[f'{p}/{r}']['termination_diagnostics'] = summarize_terminations([asdict(v) for v in subset])
    return {'schema':'hydro-lab-s2.8-paired-v1','seeds':list(seeds),'max_steps':max_steps,
        'summary':summary,'primary_contrast':'health_aware/uncertainty minus health_aware/off',
        'paired_net_reward_differences_um':differences.tolist(),
        'paired_mean_net_reward_difference_um':float(differences.mean()),
        'paired_sd_um':float(differences.std(ddof=1)) if len(seeds)>1 else None,
        'episodes':[asdict(v) for v in rows]}
