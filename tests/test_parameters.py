import pytest
from hydro_lab.parameters import NetworkParameters, TankParameters

def test_g24_nominal_heads_and_limits():
    p = NetworkParameters()
    assert p.origin.head_m(p.origin.initial_volume_m3) == pytest.approx(13.)
    assert p.receiver.head_m(p.receiver.initial_volume_m3) == pytest.approx(18.)
    assert p.receiver.head_m(500.) - p.origin.head_m(750.) == pytest.approx(5.)
    assert p.time_step_s == 900 and p.episode_steps == 96
    assert p.resistances_s2_m5 == (900., 800., 800., 1100., 1100.)
    assert tuple(p.name for p in p.pumps) == ("P0", "PN", "PS")
    assert tuple(p.a_m for p in p.pumps) == (25., 16., 16.)
    assert tuple(p.b_s2_m5 for p in p.pumps) == (250., 500., 500.)

def test_tank_rejects_invalid_geometry():
    with pytest.raises(ValueError):
        TankParameters(base_elevation_m=10., area_m2=0.)

def test_tank_rejects_out_of_range_inventory():
    with pytest.raises(ValueError):
        NetworkParameters().origin.head_m(100.)
