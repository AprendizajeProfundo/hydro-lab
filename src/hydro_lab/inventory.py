"""Conservative G2.4 inventory transition; no post-hoc clipping."""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class InventoryResult:
    V0_next: float
    V4_next: float
    served_m3_s: float
    unserved_m3: float
    mass_error_m3: float

def transition(V0: float, V4: float, Q: float, supply: float, demand: float,
               *, dt: float = 900., lower: float = 200., upper: float = 1500.) -> InventoryResult:
    vals=(V0,V4,Q,supply,demand,dt,lower,upper)
    if not all(isfinite(v) for v in vals) or dt <= 0 or lower >= upper or any(x < 0 for x in (Q,supply,demand)):
        raise ValueError('Invalid inventory inputs')
    if not lower-1e-9 <= V0 <= upper+1e-9 or not lower-1e-9 <= V4 <= upper+1e-9:
        raise ValueError('Initial inventory out of bounds')
    served=min(demand,max(0.,(V4+dt*Q-lower)/dt))
    next0=V0+dt*(supply-Q)
    next4=V4+dt*(Q-served)
    if not lower-1e-9 <= next0 <= upper+1e-9 or not lower-1e-9 <= next4 <= upper+1e-9:
        raise ValueError('INVENTORY_INFEASIBLE')
    err=(next0+next4)-(V0+V4)-dt*(supply-served)
    return InventoryResult(next0,next4,served,dt*(demand-served),err)
