"""S2.4 Gymnasium POMDP environment using the S2.3 physics and safety semantics."""
from __future__ import annotations
from itertools import product
from typing import Any
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .parameters import NetworkParameters
from .scenarios import Scenario, generate_scenario, tariff
from .dynamics import _try_step
from .observations import HealthBelief, OBSERVATION_NAMES, observe

class HydroLabEnv(gym.Env):
    """Continuous normalized speed controls. One step = 900 s; max 96 steps.

    No access to scenario or true health is exposed through observation.
    The `info['evaluation_truth']` diagnostic is intended ONLY for offline
    evaluation and must not be passed to the deployed policy.
    """
    metadata = {'render_modes': []}

    def __init__(self, *, params: NetworkParameters | None = None, max_steps: int = 96):
        super().__init__()
        if not 1 <= max_steps <= 96:
            raise ValueError('max_steps must be in [1,96]')
        self.params = params or NetworkParameters()
        self.max_steps = max_steps
        self.action_space = spaces.Box(-1.,1.,shape=(3,),dtype=np.float32)
        lo = np.array([200.,200.,0.,0.,0.,0.,0.,0.,0.,0.,0.,0.,.65,.65,.65],dtype=np.float32)
        hi = np.array([1500.,1500.,.17,.30,.30,600000.,600000.,600000.,1.,1.,1.,1.,1.,1.,1.],dtype=np.float32)
        self.observation_space = spaces.Box(lo,hi,dtype=np.float32)
        self._grid = tuple(product((.65,.80,.95),repeat=3)) + ((.72,.72,.72),(.92,.90,.90),(1.,1.,1.))
        self._initialized = False

    def _observation(self):
        return observe(volume0=self.v0,volume4=self.v4,demand=self.scenario.demand[self.t],
                       price=tariff(self.t),previous_flow=self.previous_flow,
                       previous_pressures=self.previous_pressures,previous_action=self.previous_action,
                       t=self.t,belief=self.belief,rng=self.sensor_rng)

    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        options = options or {}
        if 'scenario_id' in options and 'scenario' not in options:
            raise ValueError('scenario_id requires a registered scenario; pass options={"scenario": Scenario}')
        scenario = options.get('scenario')
        if scenario is not None and not isinstance(scenario,Scenario):
            raise TypeError('options["scenario"] must be Scenario')
        if scenario is None:
            if seed is None:
                seed = int(self.np_random.integers(0,2**32-1))
            scenario = generate_scenario(int(seed),steps=self.max_steps)
        if len(scenario.demand)<self.max_steps:
            raise ValueError('Scenario shorter than episode')
        self.scenario = scenario
        self.sensor_rng = np.random.default_rng(np.random.SeedSequence(scenario.seed).spawn(5)[4])
        self.v0 = self.params.origin.initial_volume_m3
        self.v4 = self.params.receiver.initial_volume_m3
        self.health = tuple(scenario.initial_health)
        self.availability = (True,True,True)
        self.previous_action = (.8,.8,.8)
        self.previous_flow = 0.
        self.previous_pressures = (0.,0.,0.)
        self.belief = HealthBelief.initial()
        self.t=0
        self._initialized=True
        obs=self._observation()
        self.last_obs=obs.copy()
        return obs, {'scenario_seed':scenario.seed,'observation_names':OBSERVATION_NAMES}

    def step(self, action):
        if not self._initialized or self.t>=self.max_steps:
            raise RuntimeError('Call reset() before step() or after episode ends')
        raw=np.asarray(action,dtype=np.float64)
        if raw.shape!=(3,) or not np.all(np.isfinite(raw)) or np.any(raw < -1.) or np.any(raw > 1.):
            raise ValueError('action must be finite Box(3) in [-1,1]')
        requested=tuple(float(x) for x in (.8+.2*raw))
        s=self.scenario;t=self.t;p=self.params
        density_p=__import__('dataclasses').replace(p,density_kg_m3=s.density)
        demand=s.demand[t];mu=s.viscosity[t];price=tariff(t)
        def try_action(a):
            return _try_step(self.v0,self.v4,mu,self.health,self.availability,a,
                             p.supply_nominal_m3_s,demand,density_p)
        executed=tuple(x if on else 0. for x,on in zip(requested,self.availability))
        candidate=try_action(executed)
        intervention=None
        if candidate is None:
            for speed in sorted(self._grid,key=lambda x:(sum((a-b)**2 for a,b in zip(x,requested)),x)):
                masked=tuple(x if on else 0. for x,on in zip(speed,self.availability))
                candidate=try_action(masked)
                if candidate is not None:
                    executed=masked;intervention='SAFETY_GRID';break
        hydraulic=None
        if candidate is None:
            from .inventory import transition
            try:
                inv=transition(self.v0,self.v4,0.,p.supply_nominal_m3_s,demand,dt=p.time_step_s,
                               lower=p.origin.min_volume_m3,upper=p.origin.max_volume_m3)
                executed=(0.,0.,0.);intervention='SAFE_SHUTDOWN'
            except ValueError:
                # No transition is fabricated: terminal cost and original state.
                self.t+=1
                info={'scenario_seed':s.seed,'action_requested':requested,'action_executed':(0.,0.,0.),
                      'intervention_reason':'TERMINAL_NO_SAFE_ACTION',
                      'intervention_distance':float(np.linalg.norm(np.array(requested))),
                      'termination_reason':'NO_SAFE_ACTION_OR_STOP',
                      'costs':{'energy_um':0.,'deficit_um':0.,'maneuver_um':0.,'terminal_um':200.},
                      'evaluation_truth':{'health':self.health,'availability':self.availability,
                                          'volumes_m3':(self.v0,self.v4)}}
                # terminal observation repeats last observable state, not a new physical sample
                self._initialized=False
                return self.last_obs.copy(),-200.,True,False,info
        else:
            hydraulic,inv=candidate
        Q=float(hydraulic.q_edges[0]) if hydraulic is not None else 0.
        flows=(Q,float(hydraulic.q_edges[1]),float(hydraulic.q_edges[3])) if hydraulic is not None else (0.,0.,0.)
        energy=float(np.sum(hydraulic.powers))*p.time_step_s/3.6e6 if hydraulic is not None else 0.
        costs={'energy_um':price*energy,'deficit_um':4.*inv.unserved_m3,
               'maneuver_um':.5*sum(abs(a-b) for a,b in zip(executed,self.previous_action)),
               'terminal_um':0.}
        next_h=[];next_avail=[]
        for k,(old,q,on) in enumerate(zip(self.health,flows,self.availability)):
            wear=2e-5*(q/p.pumps[k].reference_flow_m3_s)**2*(executed[k]/.8)**2 if on and executed[k]>0 else 0.
            nh=float(np.clip(old-wear+s.health_noise[t][k],.65,1.))
            failure_prob=min(.002,.00005+.001*(1.-nh))
            next_h.append(nh)
            next_avail.append(bool(on and s.failure_uniform[t][k]>=failure_prob))
        self.v0,self.v4=inv.V0_next,inv.V4_next
        self.health=tuple(next_h);self.availability=tuple(next_avail)
        self.previous_action=executed;self.previous_flow=Q
        self.previous_pressures=(tuple(float(hydraulic.pressures[i]) for i in (1,2,3))
                                 if hydraulic is not None else (0.,0.,0.))
        self.belief.predict()
        self.t+=1
        truncated=self.t>=self.max_steps
        info={'scenario_seed':s.seed,'action_requested':requested,'action_executed':executed,
              'intervention_reason':intervention,
              'intervention_distance':float(np.linalg.norm(np.subtract(executed,requested))),
              'termination_reason':None,'costs':costs,
              'energy_kwh':energy,'served_m3':inv.served_m3_s*p.time_step_s,
              'unserved_m3':inv.unserved_m3,'mass_error_m3':inv.mass_error_m3,
              'hydraulic_status':hydraulic.status.value if hydraulic is not None else 'SAFE_SHUTDOWN',
              'evaluation_truth':{'health':self.health,'availability':self.availability,
                                  'volumes_m3':(self.v0,self.v4)}}
        reward=-sum(costs.values())
        if truncated:
            # Gymnasium requires a terminal observation; last available demand
            # is used for display only, never advanced beyond scenario horizon.
            self.t=self.max_steps-1
            obs=self._observation()
            self.t=self.max_steps
            self._initialized=False
        else:
            obs=self._observation()
        self.last_obs=obs.copy()
        return obs,float(reward),False,truncated,info
