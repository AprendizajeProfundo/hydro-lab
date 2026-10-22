import pytest
from hydro_lab.scenarios import generate_scenario,tariff

def test_repeatable_independent_streams():
    a=generate_scenario(42);b=generate_scenario(42);c=generate_scenario(43)
    assert a==b and a!=c
    assert len(a.demand)==96 and len(a.viscosity)==96
    assert all(0<=x<=.17 for x in a.demand)
    assert all(.008<=x<=.080 for x in a.viscosity)

def test_tariff_boundaries():
    for t,c in [(0,.12),(23,.12),(24,.18),(63,.18),(64,.30),(83,.30),(84,.15),(95,.15)]:
        assert tariff(t)==pytest.approx(c)
    with pytest.raises(ValueError): tariff(96)
