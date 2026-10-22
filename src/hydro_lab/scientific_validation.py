"""S2.9: predeclared, reproducible tests of active-observation value.

All comparisons use matching exogenous scenario realizations. Differences
in hydraulic trajectories remain causal consequences of different policies.
Stress is a documented hypothetical stress test, not a field calibration.
"""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import csv
import json
import math
import numpy as np
from .scenarios import generate_scenario
from .control_center import EpisodeSession

ARMS = (('demand_feedback','off'), ('health_aware','off'),
        ('demand_feedback','uncertainty'), ('health_aware','uncertainty'))
REGIMES = ('baseline','degraded','accelerated_wear')


def scenario_for(seed: int, regime: str, steps: int = 96):
    """Exogenous scenarios; no access to controller or outcome when generated.

    degraded: initial health (.75,.90,.90).
    accelerated_wear: same initial health and deterministic negative
    per-step shocks of -.001 on pump P0 (beyond original stochastic noise).
    Both are synthetic stress assumptions, NOT empirically calibrated wear.
    """
    if regime not in REGIMES:
        raise ValueError(f'Unknown regime {regime}')
    s = generate_scenario(seed, steps=steps)
    if regime == 'baseline':
        return s
    s = replace(s, initial_health=(.75,.90,.90))
    if regime == 'accelerated_wear':
        noise = tuple((row[0]-.001,row[1],row[2]) for row in s.health_noise)
        s = replace(s,health_noise=noise)
    return s


def _run(seed, regime, policy, robot_policy, steps):
    scenario = scenario_for(seed, regime, steps)
    session = EpisodeSession(seed=seed, policy_name=policy, robot_policy=robot_policy,
                             max_steps=steps, scenario=scenario)
    try:
        session.advance(steps)
        records = session.records
        total = session.report()
        robot_cost = float(session.robot.cost_um)
        # Explicit accounting: net reward already includes robot costs.
        hydraulic_reward = float(total['reward_total']) + robot_cost
        return dict(seed=seed, regime=regime, policy=policy, robot_policy=robot_policy,
            steps=len(records), net_reward_um=float(total['reward_total']),
            hydraulic_reward_um=hydraulic_reward, robot_cost_um=robot_cost,
            energy_kwh=float(total['total_energy_kwh']),
            unserved_m3=float(total['total_unserved_m3']),
            interventions=int(total['interventions']),
            inspections=int(session.robot.inspections), moves=int(session.robot.moves),
            terminated=bool(session.terminated),
            max_mass_error_m3=max((abs(r['mass_error_m3']) for r in records),default=0.),
            # Requested hydraulic actions differ from the no-robot arm only
            # if the controller actually uses observations in a consequential way.
            requested_actions=[r['action_requested'] for r in records])
    finally:
        session.close()


def _stats(values):
    x=np.asarray(values,dtype=float)
    n=len(x)
    mean=float(np.mean(x))
    sd=float(np.std(x,ddof=1)) if n>1 else None
    # Approximate descriptive normal interval, not a definitive claim of significance.
    ci= [mean-1.96*sd/math.sqrt(n),mean+1.96*sd/math.sqrt(n)] if n>1 else None
    return dict(n=n,mean=mean,sd=sd,approx_95pct_ci=ci,
                min=float(np.min(x)),max=float(np.max(x)),values=x.tolist())


def run_validation(seeds, regimes=REGIMES, steps=96):
    seeds=tuple(int(s) for s in seeds)
    regimes=tuple(regimes)
    if not seeds or len(set(seeds))!=len(seeds) or any(s<0 for s in seeds):
        raise ValueError('seeds must be distinct nonnegative integers')
    if not 1<=steps<=96 or not regimes or len(set(regimes))!=len(regimes) or any(r not in REGIMES for r in regimes):
        raise ValueError('invalid regimes or steps')
    rows=[_run(seed,regime,p,r,steps) for regime in regimes for seed in seeds for p,r in ARMS]
    lookup={(x['regime'],x['seed'],x['policy'],x['robot_policy']):x for x in rows}
    summary={}
    for regime in regimes:
        effects={}
        for policy in ('demand_feedback','health_aware'):
            paired=[(lookup[regime,seed,policy,'uncertainty'],lookup[regime,seed,policy,'off']) for seed in seeds]
            effects[policy]={
                'net_reward_difference_um':_stats([a['net_reward_um']-b['net_reward_um'] for a,b in paired]),
                'hydraulic_reward_difference_um':_stats([a['hydraulic_reward_um']-b['hydraulic_reward_um'] for a,b in paired]),
                'robot_cost_um':_stats([a['robot_cost_um'] for a,b in paired]),
                'energy_difference_kwh':_stats([a['energy_kwh']-b['energy_kwh'] for a,b in paired]),
                'unserved_difference_m3':_stats([a['unserved_m3']-b['unserved_m3'] for a,b in paired]),
                'requested_action_different_steps':_stats([sum(not np.allclose(u,v,rtol=0,atol=1e-7) for u,v in zip(a['requested_actions'],b['requested_actions'])) for a,b in paired]),
                'different_episode_lengths':sum(a['steps']!=b['steps'] for a,b in paired),
            }
        # Difference in differences isolates incremental response of health-aware
        # controller to inspection relative to demand feedback.
        effects['difference_in_differences_net_um']=_stats([
            (lookup[regime,s,'health_aware','uncertainty']['net_reward_um']-lookup[regime,s,'health_aware','off']['net_reward_um'])-
            (lookup[regime,s,'demand_feedback','uncertainty']['net_reward_um']-lookup[regime,s,'demand_feedback','off']['net_reward_um'])
            for s in seeds])
        summary[regime]=effects
    public_rows=[{k:v for k,v in x.items() if k!='requested_actions'} for x in rows]
    return dict(schema='hydro-lab-s2.9-scientific-validation-v1',seeds=list(seeds),
        steps=steps,regimes=list(regimes),arms=[list(a) for a in ARMS],
        assumptions={'degraded_initial_health':[.75,.90,.90],
                     'accelerated_wear_extra_health_shock_per_step':[-.001,0,0],
                     'stress_scenarios_are_synthetic_not_calibrated':True,
                     'paired_same_seed_and_exogenous_scenario':True,
                     'interval':'normal-approximation descriptive 95%, not multiple-comparison adjusted'},
        summary=summary,episodes=public_rows)


def save_validation(report, directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    json_path=directory/'scientific_validation_s29.json'
    csv_path=directory/'scientific_validation_s29.csv'
    md_path=directory/'scientific_validation_s29.md'
    # No silent overwrite of prior experimental results.
    for p in (json_path,csv_path,md_path):
        if p.exists():raise FileExistsError(f'Already exists: {p}')
    json_path.write_text(json.dumps(report,indent=2,allow_nan=False,ensure_ascii=False)+'\n',encoding='utf8')
    with csv_path.open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=list(report['episodes'][0]))
        writer.writeheader();writer.writerows(report['episodes'])
    lines=['# S2.9 — Scientific validation of active observation','',
        f"Seeds: {report['seeds']}; horizon: {report['steps']} steps.",'',
        'Net difference = with robot minus without robot. Positive favors robot.','',
        '| Regime | Controller | Net difference (UM) | Hydraulic benefit (UM) | Robot cost (UM) | Action changes (steps) |',
        '|---|---|---:|---:|---:|---:|']
    for regime, group in report['summary'].items():
        for policy in ('demand_feedback','health_aware'):
            v=group[policy]
            lines.append(f"| {regime} | {policy} | {v['net_reward_difference_um']['mean']:.4f} | {v['hydraulic_reward_difference_um']['mean']:.4f} | {v['robot_cost_um']['mean']:.4f} | {v['requested_action_different_steps']['mean']:.2f} |")
    lines += ['', '## Interpretation',
        'The paired net difference is a descriptive estimate for the predeclared seeds, not proof of general superiority.',
        'Hydraulic benefit excludes robot costs; net difference includes them.',
        'The stress scenarios are hypothetical, not empirical calibration. Differences in actions show use of information, not necessarily its value.',
        'Normal-approximation confidence intervals are descriptive and may be unreliable for rare failures or small samples.',
        'A single day and synthetic health sensor cannot establish field safety or reliability.','']
    md_path.write_text('\n'.join(lines),encoding='utf8')
    return json_path,csv_path,md_path
