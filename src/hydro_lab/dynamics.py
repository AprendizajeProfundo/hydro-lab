"""S2.3 physical episode runner: deterministic safety filter and separated costs."""
from dataclasses import dataclass, asdict
from itertools import product
from math import isfinite
import json
from pathlib import Path
from typing import Any
import numpy as np
from .parameters import NetworkParameters
from .hydraulics import solve_hydraulics, HydraulicStatus, HydraulicResult
from .inventory import transition, InventoryResult
from .scenarios import Scenario, generate_scenario, tariff

@dataclass(frozen=True)
class StepRecord:
    t: int
    demand_m3_s: float
    supply_m3_s: float
    viscosity_pa_s: float
    tariff_um_kwh: float
    volume0_m3: float
    volume4_m3: float
    volume0_next_m3: float
    volume4_next_m3: float
    flow_m3_s: float
    served_m3_s: float
    unserved_m3: float
    energy_kwh: float
    energy_cost_um: float
    deficit_cost_um: float
    maneuver_cost_um: float
    terminal_cost_um: float
    total_cost_um: float
    action_requested: tuple[float,float,float]
    action_executed: tuple[float,float,float]
    intervention_reason: str | None
    intervention_distance: float
    health: tuple[float,float,float]
    health_next: tuple[float,float,float]
    availability: tuple[bool,bool,bool]
    availability_next: tuple[bool,bool,bool]
    hydraulic_status: str
    hydraulic_residual_m: float | None
    mass_error_m3: float
    termination_reason: str | None

@dataclass(frozen=True)
class EpisodeResult:
    seed: int
    records: tuple[StepRecord,...]
    terminated: bool
    reason: str | None
    final_volumes: tuple[float,float]
    final_health: tuple[float,float,float]
    final_availability: tuple[bool,bool,bool]

    def summary(self) -> dict[str,Any]:
        r=self.records
        return {'seed':self.seed,'steps':len(r),'terminated':self.terminated,
                'reason':self.reason,'total_cost_um':sum(x.total_cost_um for x in r),
                'energy_kwh':sum(x.energy_kwh for x in r),
                'energy_cost_um':sum(x.energy_cost_um for x in r),
                'unserved_m3':sum(x.unserved_m3 for x in r),
                'served_m3':sum(x.served_m3_s*900 for x in r),
                'interventions':sum(x.intervention_reason is not None for x in r),
                'final_volumes_m3':self.final_volumes,
                'max_abs_mass_error_m3':max((abs(x.mass_error_m3) for x in r),default=0.)}

    def save_json(self,path: str | Path) -> None:
        target=Path(path)
        if target.exists(): raise FileExistsError('Results are immutable: choose a new filename')
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps({'summary':self.summary(),'records':[asdict(x) for x in self.records]},indent=2,allow_nan=False),encoding='utf8')

def _try_step(v0:float,v4:float,mu:float,h:tuple[float,float,float],
              avail:tuple[bool,bool,bool],speed:tuple[float,float,float],
              supply:float,demand:float,params:NetworkParameters):
    effective=tuple(s if on else 0. for s,on in zip(speed,avail))
    hydraulic=solve_hydraulics(v0,v4,mu,h,avail,effective,params=params)
    if hydraulic.status!=HydraulicStatus.FEASIBLE: return None
    try:
        inv=transition(v0,v4,float(hydraulic.q_edges[0]),supply,demand,dt=params.time_step_s,
                       lower=params.origin.min_volume_m3,upper=params.origin.max_volume_m3)
    except ValueError: return None
    return hydraulic,inv

def _rule(v4:float,demand:float,price:float,prev:tuple[float,float,float])->tuple[float,float,float]:
    if v4<400 or demand>.13: return (.92,.90,.90)
    if v4>800 or price>=.30: return (.72,.72,.72)
    return (.8,.8,.8)

def run_episode(seed:int=20261018,*,scenario:Scenario|None=None,
                controller=None, steps:int=96,
                params:NetworkParameters|None=None)->EpisodeResult:
    """No RL/Gymnasium here. Safety action grid is fixed lexicographically.

    A safe stop is Q=0 only when inventory balances remain feasible.
    An impossible step terminates with 200 UM and no fabricated flow.
    """
    p=params or NetworkParameters()
    s=scenario if scenario is not None else generate_scenario(seed,steps=steps)
    if steps>len(s.demand): raise ValueError('scenario shorter than requested horizon')
    p=__import__('dataclasses').replace(p,density_kg_m3=s.density)
    v0,v4=p.origin.initial_volume_m3,p.receiver.initial_volume_m3
    h=tuple(s.initial_health);avail=(True,True,True)
    previous=(.8,.8,.8); records=[]; reason=None
    # Frozen deterministic safety grid: full cartesian set and baseline presets.
    grid=tuple(product((.65,.80,.95),repeat=3)) + ((.72,.72,.72),(.92,.90,.90),(1.,1.,1.))
    for t in range(steps):
        d=s.demand[t]; mu=s.viscosity[t]; supply=p.supply_nominal_m3_s; price=tariff(t)
        requested=tuple(controller(t,v0,v4,d,price,previous) if controller else _rule(v4,d,price,previous))
        if len(requested)!=3 or any(not isfinite(float(x)) or not .60<=float(x)<=1. for x in requested):
            raise ValueError('Controller must return three speeds in [0.60,1.00]')
        requested=tuple(map(float,requested))
        effective=tuple(x if available else 0. for x,available in zip(requested,avail))
        candidate=_try_step(v0,v4,mu,h,avail,effective,supply,d,p)
        executed=effective;intervention=None
        if candidate is None:
            # Search all predeclared grid actions by Euclidean distance, then lexicographic tie-break.
            # Availability masks are imposed before evaluating each candidate.
            choices=sorted(grid,key=lambda x:(sum((a-b)**2 for a,b in zip(x,requested)),x))
            for action in choices:
                masked=tuple(x if on else 0. for x,on in zip(action,avail))
                candidate=_try_step(v0,v4,mu,h,avail,masked,supply,d,p)
                if candidate is not None:
                    executed=masked; intervention='SAFETY_GRID';break
        if candidate is None:
            # Hydraulic shutdown is a separate operating mode, not a fake hydraulic root.
            try:
                inv=transition(v0,v4,0.,supply,d,dt=p.time_step_s,
                               lower=p.origin.min_volume_m3,upper=p.origin.max_volume_m3)
            except ValueError:
                inv=None
            if inv is None:
                reason='NO_SAFE_ACTION_OR_STOP'
                # No state transition is claimed; explicit terminal record with 200 UM.
                records.append(StepRecord(t,d,supply,mu,price,v0,v4,v0,v4,0.,0.,0.,0.,0.,0.,0.,200.,200.,requested,
                                          (0.,0.,0.),'TERMINAL_NO_SAFE_ACTION',float(np.linalg.norm(requested)),
                                          h,h,avail,avail,'INFEASIBLE_PHYSICAL',None,0.,reason))
                break
            executed=(0.,0.,0.); intervention='SAFE_SHUTDOWN';hydraulic=None
        else:
            hydraulic,inv=candidate
        Q=float(hydraulic.q_edges[0]) if hydraulic is not None else 0.
        flows=(Q,float(hydraulic.q_edges[1]),float(hydraulic.q_edges[3])) if hydraulic is not None else (0.,0.,0.)
        energy=float(np.sum(hydraulic.powers))*p.time_step_s/3.6e6 if hydraulic is not None else 0.
        energy_cost=price*energy
        deficit_cost=4.*inv.unserved_m3
        maneuver_cost=.5*sum(abs(a-b) for a,b in zip(executed,previous))
        next_h=[];next_avail=[]
        for k,(old,q,on) in enumerate(zip(h,flows,avail)):
            wear=2e-5*(q/p.pumps[k].reference_flow_m3_s)**2*(executed[k]/.8)**2 if on and executed[k]>0 else 0.
            nh=float(np.clip(old-wear+s.health_noise[t][k],.65,1.))
            failure_prob=min(.002,.00005+.001*(1.-nh))
            next_h.append(nh)
            next_avail.append(bool(on and s.failure_uniform[t][k]>=failure_prob))
        new_h=tuple(next_h);new_avail=tuple(next_avail)
        records.append(StepRecord(t,d,supply,mu,price,v0,v4,inv.V0_next,inv.V4_next,Q,inv.served_m3_s,
                                  inv.unserved_m3,energy,energy_cost,deficit_cost,maneuver_cost,0.,
                                  energy_cost+deficit_cost+maneuver_cost,requested,executed,intervention,
                                  float(np.linalg.norm(np.subtract(executed,requested))),h,new_h,avail,new_avail,
                                  hydraulic.status.value if hydraulic is not None else 'SAFE_SHUTDOWN',
                                  hydraulic.residual_max if hydraulic is not None else None,inv.mass_error_m3,None))
        v0,v4=inv.V0_next,inv.V4_next;h=new_h;avail=new_avail;previous=executed
    return EpisodeResult(s.seed,tuple(records),reason is not None,reason,(v0,v4),h,avail)
