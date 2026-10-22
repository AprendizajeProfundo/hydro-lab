"""Run from project root: python examples/nominal_hydraulics.py"""
from hydro_lab.hydraulics import solve_hydraulics

r = solve_hydraulics(V0=750, V4=500, viscosity=0.020,
                     health=(1.,1.,1.), availability=(True,True,True),
                     u=(.8,.8,.8))
print('Status:', r.status.value)
print('Violations:', r.constraint_violations)
if r.q_edges is not None:
    print('Flows [m3/s] (01,12,24,13,34):', r.q_edges)
    print('Heads [m]:', r.heads)
    print('Pressures [Pa]:', r.pressures)
    print('Pump power [W] (P0,PN,PS):', r.powers)
    print('Maximum hydraulic residual [m]:', r.residual_max)
    print('Inventory constraints checked:', r.diagnostics['inventory_feasibility_checked'])
