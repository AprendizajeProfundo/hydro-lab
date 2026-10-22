"""Steady-state G2.4 hydraulics. Inventory feasibility belongs to S2.3."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite, pi
from typing import Any
import numpy as np
from numpy.typing import NDArray
from scipy.optimize import least_squares, brentq
from .parameters import NetworkParameters
from .topology import edge_flows, incidence_matrix

class HydraulicStatus(str, Enum):
    FEASIBLE = 'FEASIBLE'
    INFEASIBLE_PHYSICAL = 'INFEASIBLE_PHYSICAL'
    NUMERICAL_FAILURE = 'NUMERICAL_FAILURE'

@dataclass(frozen=True)
class HydraulicResult:
    status: HydraulicStatus
    q_edges: NDArray[np.float64] | None
    heads: NDArray[np.float64] | None
    pressures: NDArray[np.float64] | None
    powers: NDArray[np.float64] | None
    residual_max: float | None
    constraint_violations: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)

def _fail(status: HydraulicStatus, reason: str, **details: Any) -> HydraulicResult:
    return HydraulicResult(status, None, None, None, None, None, (reason,), details)

def _pump_head(q: float, u: float, h: float, a: float, b: float) -> float:
    return h * max(0.0, a*u*u - b*q*q)

def _efficiency(q: float, u: float, h: float, qref: float) -> float:
    return float(np.clip(0.78 - 0.08*(u-0.82)**2 - 0.04*(q/qref-1)**2 - 0.08*(1-h), 0.55, 0.82))

def solve_hydraulics(V0: float, V4: float, viscosity: float,
                     health: tuple[float, float, float],
                     availability: tuple[bool, bool, bool],
                     u: tuple[float, float, float], *,
                     params: NetworkParameters | None = None,
                     residual_tolerance_m: float = 1e-6) -> HydraulicResult:
    """Return a physical solution, or explicit failure without fabricated flows.

    Closed branches have undetermined intermediate-node head/pressure (NaN).
    Infeasible numerical roots return no q_edges. Pressure/velocity violations
    retain the candidate state for diagnosis, but status is never FEASIBLE.
    """
    p = params or NetworkParameters()
    try:
        h, speeds, avail = tuple(map(float, health)), tuple(map(float, u)), tuple(availability)
        if len(h) != 3 or len(speeds) != 3 or len(avail) != 3:
            raise ValueError('three pumps required')
        if not all(isinstance(x, (bool, np.bool_)) for x in avail):
            raise ValueError('availability must be boolean')
        if not all(isfinite(float(x)) for x in (V0,V4,viscosity,*h,*speeds,residual_tolerance_m)):
            raise ValueError('nonfinite input')
        if not p.origin.min_volume_m3 <= V0 <= p.origin.max_volume_m3:
            raise ValueError('V0 outside limits')
        if not p.receiver.min_volume_m3 <= V4 <= p.receiver.max_volume_m3:
            raise ValueError('V4 outside limits')
        if viscosity <= 0 or residual_tolerance_m <= 0:
            raise ValueError('invalid viscosity or tolerance')
        if any(not 0.65 <= x <= 1 for x in h):
            raise ValueError('health outside limits')
        for enabled, speed in zip(avail, speeds):
            if enabled and not 0.60 <= speed <= 1.0:
                raise ValueError('active pump speed outside limits')
            if not enabled and speed != 0:
                raise ValueError('closed pump speed must be zero')
    except (TypeError, ValueError, OverflowError) as exc:
        return _fail(HydraulicStatus.INFEASIBLE_PHYSICAL, 'INVALID_INPUT', error=str(exc))
    if not avail[0]:
        return _fail(HydraulicStatus.INFEASIBLE_PHYSICAL, 'P0_UNAVAILABLE_SAFE_STOP', safe_stop=True, zero_transport=True)
    north_on, south_on = avail[1], avail[2]
    if not north_on and not south_on:
        return _fail(HydraulicStatus.INFEASIBLE_PHYSICAL, 'ALL_BRANCHES_CLOSED_SAFE_STOP', safe_stop=True, zero_transport=True)
    H0, H4 = p.origin.head_m(V0), p.receiver.head_m(V4)
    delta = H4-H0
    R = np.asarray(p.resistances_s2_m5) * (viscosity/p.reference_viscosity_pa_s)**p.resistance_viscosity_exponent
    def hp(i: int, q: float) -> float:
        pump = p.pumps[i]
        return _pump_head(q, speeds[i], h[i], pump.a_m, pump.b_s2_m5)
    def residuals(n: float, s: float) -> tuple[float,float]:
        Q = n+s
        common = hp(0,Q)-R[0]*Q*Q-delta
        return (common+hp(1,n)-(R[1]+R[2])*n*n,
                common+hp(2,s)-(R[3]+R[4])*s*s)
    qmax = 0.15
    if north_on and south_on:
        candidates = []
        for start in ((.05,.05),(.01,.12),(.12,.01),(0.,0.),(.15,.15)):
            try:
                sol = least_squares(lambda x: residuals(x[0],x[1]), start,
                                    bounds=(0.,qmax), max_nfev=1000,
                                    ftol=1e-13, xtol=1e-13, gtol=1e-13)
                if np.all(np.isfinite(sol.x)) and np.all(np.isfinite(sol.fun)):
                    candidates.append((float(np.max(np.abs(sol.fun))), sol.x))
            except (ValueError, FloatingPointError):
                pass
        if not candidates:
            return _fail(HydraulicStatus.NUMERICAL_FAILURE, 'NO_FINITE_CANDIDATE')
        residual, best = min(candidates, key=lambda x:x[0])
        n,s = map(float,best)
    else:
        idx = 0 if north_on else 1
        def f(q: float) -> float:
            r = residuals(q,0.) if north_on else residuals(0.,q)
            return r[idx]
        lo,hi = f(0.),f(qmax)
        if abs(lo) <= residual_tolerance_m:
            q = 0.
        elif lo*hi > 0:
            return _fail(HydraulicStatus.INFEASIBLE_PHYSICAL,'NO_ROOT_OPEN_BRANCH',
                         residual_at_zero_m=lo,residual_at_upper_m=hi)
        else:
            try:
                q = float(brentq(f,0.,qmax,xtol=1e-14))
            except (ValueError,RuntimeError) as exc:
                return _fail(HydraulicStatus.NUMERICAL_FAILURE,'ONE_BRANCH_SOLVER_FAILURE',error=str(exc))
        n,s = (q,0.) if north_on else (0.,q)
        residual = abs(f(q))
    if residual > residual_tolerance_m:
        return _fail(HydraulicStatus.INFEASIBLE_PHYSICAL,'NO_ROOT_WITHIN_TOLERANCE',
                     best_residual_m=residual,candidate_branch_flows_m3_s=(n,s))
    Q = n+s
    flows = edge_flows(n,s)
    H1 = H0+hp(0,Q)-R[0]*Q**2
    H2 = H1+hp(1,n)-R[1]*n*n if north_on else float('nan')
    H3 = H1+hp(2,s)-R[3]*s*s if south_on else float('nan')
    heads = np.array([H0,H1,H2,H3,H4])
    pressures = np.array([0.,p.density_kg_m3*p.gravity_m_s2*(H1-p.internal_elevations_m[0]),
                          p.density_kg_m3*p.gravity_m_s2*(H2-p.internal_elevations_m[1]) if north_on else np.nan,
                          p.density_kg_m3*p.gravity_m_s2*(H3-p.internal_elevations_m[2]) if south_on else np.nan,0.])
    powers = np.array([p.density_kg_m3*p.gravity_m_s2*q*hp(i,q)/_efficiency(q,speeds[i],h[i],p.pumps[i].reference_flow_m3_s)
                       if avail[i] else 0. for i,q in enumerate((Q,n,s))])
    velocities = flows/(pi*(p.diameter_m/2)**2)
    mass_error = float(np.max(np.abs(incidence_matrix()@flows-np.array([-Q,0.,0.,0.,Q]))))
    reconstructed = {}
    if north_on: reconstructed['north'] = H2-R[2]*n*n
    if south_on: reconstructed['south'] = H3-R[4]*s*s
    head_error = max(abs(x-H4) for x in reconstructed.values())
    violations = []
    if mass_error > 1e-9: violations.append('MASS_BALANCE')
    if head_error > residual_tolerance_m: violations.append('HEAD_RECONSTRUCTION')
    if np.any(velocities > p.max_velocity_m_s+1e-10): violations.append('VELOCITY_LIMIT')
    for i in (1,2,3):
        if (i==2 and not north_on) or (i==3 and not south_on): continue
        if not 0 <= pressures[i] <= p.max_internal_pressure_pa:
            violations.append(f'PRESSURE_NODE_{i}')
    if np.any(~np.isfinite(flows)) or np.any(~np.isfinite(powers)) or np.any(powers < 0):
        violations.append('INVALID_FLOW_OR_POWER')
    return HydraulicResult(HydraulicStatus.INFEASIBLE_PHYSICAL if violations else HydraulicStatus.FEASIBLE,
                           flows,heads,pressures,powers,residual,tuple(violations),{
                           'delta_head_m':delta,'branch_flows_m3_s':(n,s),'total_flow_m3_s':Q,
                           'edge_velocity_m_s':velocities.tolist(),
                           'mass_residual_m3_s':mass_error,
                           'head_reconstruction_error_m':head_error,
                           'head_reconstructions_m':reconstructed,
                           'inventory_feasibility_checked':False,
                           'closed_branch_head_is_nan':True})
