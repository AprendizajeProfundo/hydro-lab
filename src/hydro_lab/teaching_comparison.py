"""S2.10 concise paired teaching comparison, not statistical certification."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np
from .control_center import EpisodeSession
from .scientific_validation import scenario_for, REGIMES

ARMS = (('health_aware','off'), ('health_aware','uncertainty'),
        ('health_robust','off'), ('health_robust','value'))


def run_teaching_comparison(seeds=range(10), regimes=REGIMES, steps=96):
    seeds=tuple(int(x) for x in seeds)
    regimes=tuple(regimes)
    if not seeds or len(set(seeds))!=len(seeds) or any(s<0 for s in seeds):
        raise ValueError('Distinct nonnegative seeds required')
    if not 1<=steps<=96 or not regimes or any(r not in REGIMES for r in regimes):
        raise ValueError('Invalid regimes or steps')
    rows=[]
    for regime in regimes:
        for seed in seeds:
            scenario=scenario_for(seed,regime,steps)
            for controller, robot in ARMS:
                session=EpisodeSession(seed=seed,policy_name=controller,robot_policy=robot,
                                       max_steps=steps,scenario=scenario)
                try:
                    session.advance(steps)
                    r=session.report()
                    rows.append(dict(regime=regime,seed=seed,controller=controller,
                        robot=robot,reward_um=r['reward_total'],robot_cost_um=session.robot.cost_um,
                        hydraulic_reward_um=r['reward_total']+session.robot.cost_um,
                        energy_kwh=r['total_energy_kwh'],unserved_m3=r['total_unserved_m3'],
                        inspections=session.robot.inspections,moves=session.robot.moves,
                        interventions=r['interventions'],steps=r['steps']))
                finally:
                    session.close()
    groups={}
    for regime in regimes:
        groups[regime]={}
        for ctrl,robot in ARMS:
            subset=[x for x in rows if x['regime']==regime and x['controller']==ctrl and x['robot']==robot]
            groups[regime][ctrl+'/'+robot]={key:round(float(np.mean([x[key] for x in subset])),4)
                for key in ('reward_um','robot_cost_um','hydraulic_reward_um','energy_kwh','unserved_m3','inspections','moves')}
        by={(x['seed'],x['controller'],x['robot']):x for x in rows if x['regime']==regime}
        groups[regime]['paired_robust_value_minus_robust_off']={
            'mean_um':round(float(np.mean([by[s,'health_robust','value']['reward_um']-
                                            by[s,'health_robust','off']['reward_um'] for s in seeds])),4),
            'differences_um':[round(float(by[s,'health_robust','value']['reward_um']-
                                           by[s,'health_robust','off']['reward_um']),4) for s in seeds]}
    return {'schema':'hydro-lab-s2.10-teaching-v1','seeds':list(seeds),
            'regimes':list(regimes),'steps':steps,'summary':groups,'episodes':rows,
            'caveat':'Synthetic teaching heuristic; not an optimal VOI algorithm or safety guarantee.'}


def save_teaching_comparison(report, directory):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=False)
    (directory/'comparison_s210.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    with (directory/'episodes_s210.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(report['episodes'][0]))
        writer.writeheader();writer.writerows(report['episodes'])
    lines=['# S2.10 — Comparación didáctica','',
           'Resultados sintéticos; las políticas no garantizan mejora.','',
           '| Régimen | Controlador/robot | Recompensa UM | Costo robot UM | Inspecciones | Demanda no atendida m³ |',
           '|---|---|---:|---:|---:|---:|']
    for regime, groups in report['summary'].items():
        for key, vals in groups.items():
            if key.startswith('paired_'):continue
            lines.append(f"| {regime} | {key} | {vals['reward_um']:.2f} | {vals['robot_cost_um']:.2f} | {vals['inspections']:.2f} | {vals['unserved_m3']:.2f} |")
    lines+=['','Las diferencias pareadas por semilla se encuentran en comparison_s210.json.',
            'No interpretar diferencias observadas como una demostración de superioridad.']
    (directory/'summary_s210.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return directory
