import numpy as np
import pytest
from hydro_lab.topology import NODES, EDGES, PUMP_EDGES, PASSIVE_EDGES, incidence_matrix, edge_flows, boundary_balance

EXPECTED_B = np.array([
    [-1, 0, 0, 0, 0],
    [ 1,-1, 0,-1, 0],
    [ 0, 1,-1, 0, 0],
    [ 0, 0, 0, 1,-1],
    [ 0, 0, 1, 0, 1],
], dtype=int)

def test_exact_graph_and_pump_locations():
    assert NODES == (0, 1, 2, 3, 4)
    assert EDGES == ((0,1), (1,2), (2,4), (1,3), (3,4))
    assert PUMP_EDGES == {"P0":(0,1), "PN":(1,2), "PS":(1,3)}
    assert PASSIVE_EDGES == ((2,4), (3,4))

def test_incidence_exact_and_signs():
    b = incidence_matrix()
    assert b.shape == (5, 5)
    np.testing.assert_array_equal(b, EXPECTED_B)
    np.testing.assert_array_equal(b.sum(axis=0), np.zeros(5))

@pytest.mark.parametrize("north,south", [(0.,0.), (.06,.05), (.15,.15), (.011,.079)])
def test_mass_conservation(north, south):
    b = incidence_matrix()
    q = edge_flows(north, south)
    np.testing.assert_allclose(b @ q, boundary_balance(north, south), atol=1e-12, rtol=0)
    np.testing.assert_allclose((b @ q)[1:4], 0., atol=1e-12, rtol=0)
    assert abs((b @ q).sum()) <= 1e-12

@pytest.mark.parametrize("north,south", [(-0.1, 0.), (0., -0.01), (float("nan"), 0.), (float("inf"), 0.)])
def test_reject_invalid_flows(north, south):
    with pytest.raises(ValueError):
        edge_flows(north, south)
