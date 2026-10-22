import pytest
from hydro_lab.inventory import transition

def test_mass_conservation():
    r=transition(750.,500.,.11,.11,.11)
    assert r.V0_next==pytest.approx(750.)
    assert r.V4_next==pytest.approx(500.)
    assert abs(r.mass_error_m3)<1e-9

def test_served_when_pumps_stopped():
    r=transition(750.,500.,0.,.11,.11)
    assert r.served_m3_s==pytest.approx(.11)
    assert r.V4_next==pytest.approx(401.)

def test_partial_demand_to_reserve():
    r=transition(750.,205.,0.,0.,.11)
    assert r.served_m3_s==pytest.approx(5/900)
    assert r.V4_next==pytest.approx(200.)
    assert r.unserved_m3==pytest.approx(99-5)

def test_no_posthoc_clipping():
    with pytest.raises(ValueError,match='INVENTORY_INFEASIBLE'):
        transition(201.,500.,.15,0.,.11)
