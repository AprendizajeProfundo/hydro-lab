"""S2.2 acceptance checks T02 T03 T04 T08 T09 T17 (partial)."""
from dataclasses import replace
from math import sqrt
import numpy as np
import pytest
from hydro_lab.hydraulics import solve_hydraulics, HydraulicStatus
from hydro_lab.parameters import NetworkParameters
from hydro_lab.topology import incidence_matrix

NOMINAL = dict(V0=750.,V4=500.,viscosity=.020,health=(1.,1.,1.),
               availability=(True,True,True),u=(.8,.8,.8))

def test_nominal_analytic_solution_and_conservation():
    r = solve_hydraulics(**NOMINAL)
    assert r.status == HydraulicStatus.FEASIBLE, (r.constraint_violations,r.diagnostics)
    assert r.residual_max <= 1e-6
    n,s = r.diagnostics['branch_flows_m3_s']
    assert n/s == pytest.approx(sqrt(2700/2100),rel=1e-9)
    assert 26.24-1150*(n+s)**2-2100*n*n == pytest.approx(5.,abs=1e-6)
    assert 26.24-1150*(n+s)**2-2700*s*s == pytest.approx(5.,abs=1e-6)
    np.testing.assert_allclose(incidence_matrix()@r.q_edges,[-(n+s),0,0,0,n+s],atol=1e-9)
    assert r.diagnostics['head_reconstruction_error_m'] <= 1e-6
    assert np.all(r.powers>=0)
    assert np.all(np.isfinite(r.heads))
    assert np.all(np.isfinite(r.pressures))
    assert max(r.diagnostics['edge_velocity_m_s']) <= 3.

def test_north_closed_one_dimensional():
    args = {**NOMINAL,'availability':(True,False,True),'u':(.8,0.,.8)}
    r = solve_hydraulics(**args)
    assert r.status == HydraulicStatus.FEASIBLE, (r.constraint_violations,r.diagnostics)
    assert r.q_edges[1] == r.q_edges[2] == 0.
    assert r.q_edges[3] == pytest.approx(r.q_edges[4])
    assert np.isnan(r.heads[2]) and np.isnan(r.pressures[2])
    assert r.diagnostics['head_reconstruction_error_m'] <= 1e-6
    assert r.powers[1] == 0.

def test_south_closed_one_dimensional():
    args = {**NOMINAL,'availability':(True,True,False),'u':(.8,.8,0.)}
    r = solve_hydraulics(**args)
    assert r.status == HydraulicStatus.FEASIBLE, (r.constraint_violations,r.diagnostics)
    assert r.q_edges[3] == r.q_edges[4] == 0.
    assert np.isnan(r.heads[3]) and np.isnan(r.pressures[3])
    assert r.powers[2] == 0.

def test_p0_failure_safe_stop_no_fabricated_flow():
    r = solve_hydraulics(**{**NOMINAL,'availability':(False,True,True),'u':(0.,.8,.8)})
    assert r.status == HydraulicStatus.INFEASIBLE_PHYSICAL
    assert 'P0_UNAVAILABLE_SAFE_STOP' in r.constraint_violations
    assert r.q_edges is None
    assert r.diagnostics['safe_stop']

def test_both_branches_closed_safe_stop():
    r = solve_hydraulics(**{**NOMINAL,'availability':(True,False,False),'u':(.8,0.,0.)})
    assert r.status == HydraulicStatus.INFEASIBLE_PHYSICAL
    assert r.q_edges is None

def test_insufficient_head_not_accepted():
    p = replace(NetworkParameters(), receiver=replace(NetworkParameters().receiver, base_elevation_m=50.))
    r = solve_hydraulics(**{**NOMINAL,'u':(.6,.6,.6)},params=p)
    assert r.status == HydraulicStatus.INFEASIBLE_PHYSICAL
    assert r.q_edges is None

def test_pressure_violation_not_feasible():
    p = replace(NetworkParameters(), max_internal_pressure_pa=100.)
    r = solve_hydraulics(**NOMINAL,params=p)
    assert r.status == HydraulicStatus.INFEASIBLE_PHYSICAL
    assert any(x.startswith('PRESSURE_NODE_') for x in r.constraint_violations)

def test_velocity_violation_not_feasible():
    p = replace(NetworkParameters(), max_velocity_m_s=.01)
    r = solve_hydraulics(**NOMINAL,params=p)
    assert r.status == HydraulicStatus.INFEASIBLE_PHYSICAL
    assert 'VELOCITY_LIMIT' in r.constraint_violations

@pytest.mark.parametrize('field,value', [('viscosity',0.),('viscosity',float('nan')),
                                         ('V0',100.),('health',(1.2,1.,1.)),
                                         ('u',(1.5,.8,.8))])
def test_invalid_inputs_classified(field,value):
    r = solve_hydraulics(**{**NOMINAL,field:value})
    assert r.status == HydraulicStatus.INFEASIBLE_PHYSICAL
    assert r.q_edges is None

def test_deterministic_repeat():
    a,b = solve_hydraulics(**NOMINAL),solve_hydraulics(**NOMINAL)
    np.testing.assert_array_equal(a.q_edges,b.q_edges)
    np.testing.assert_array_equal(a.powers,b.powers)
