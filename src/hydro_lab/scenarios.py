"""Independent seeded substreams and immutable exogenous episode realizations."""
from dataclasses import dataclass
from math import pi
import numpy as np

@dataclass(frozen=True)
class Scenario:
    seed: int
    density: float
    mean_demand: float
    amplitude: float
    phase: float
    initial_health: tuple[float,float,float]
    demand: tuple[float,...]
    viscosity: tuple[float,...]
    health_noise: tuple[tuple[float,float,float],...]
    failure_uniform: tuple[tuple[float,float,float],...]
    viscosity_clips: int

def tariff(step: int) -> float:
    if not 0 <= step < 96: raise ValueError('step must be 0..95')
    return 0.12 if step < 24 else 0.18 if step < 64 else 0.30 if step < 84 else 0.15

def generate_scenario(seed: int, *, steps: int=96, nominal: bool=False) -> Scenario:
    if steps < 1: raise ValueError('steps must be positive')
    streams=np.random.SeedSequence(seed).spawn(4)
    rng_s,rng_d,rng_h,rng_f=(np.random.default_rng(s) for s in streams)
    density=850. if nominal else float(rng_s.uniform(830.,870.))
    mean=.11 if nominal else float(rng_s.uniform(.09,.13))
    amplitude=.15 if nominal else float(rng_s.uniform(.05,.20))
    phase=0. if nominal else float(rng_s.uniform(0.,2*pi))
    health=(.95,.95,.95) if nominal else tuple(float(x) for x in rng_s.uniform(.9,1.,3))
    zeta=float(rng_d.normal(0.,.006/np.sqrt(1-.75**2)))
    demands=[]
    for t in range(steps):
        demands.append(float(np.clip(mean*(1+amplitude*np.sin(2*pi*t/96+phase))+zeta,0.,.17)))
        zeta=.75*zeta+.006*float(rng_d.normal())
    logmu=np.log(.020)
    viscosity=[]; clips=0
    for t in range(steps):
        mu=float(np.exp(logmu)); clipped=float(np.clip(mu,.008,.080))
        clips+=int(clipped!=mu);viscosity.append(clipped)
        logmu=np.log(.020)+.97*(logmu-np.log(.020))+.015*float(rng_s.normal())
    noise=tuple(tuple(float(x) for x in row) for row in rng_h.normal(0.,2e-5,(steps,3)))
    failures=tuple(tuple(float(x) for x in row) for row in rng_f.uniform(size=(steps,3)))
    return Scenario(seed,density,mean,amplitude,phase,health,tuple(demands),tuple(viscosity),noise,failures,clips)
