import json
import pytest
from dataclasses import replace
from hydro_lab.dynamics import run_episode
from hydro_lab.scenarios import generate_scenario

def test_reproducible_episode():
    a=run_episode(44,steps=12);b=run_episode(44,steps=12)
    assert a==b
    assert len(a.records)>0

def test_conservation_and_costs():
    a=run_episode(20261018,steps=12)
    for r in a.records:
        assert abs(r.mass_error_m3)<1e-8
        assert r.total_cost_um>=0
        assert r.volume0_next_m3>=200 and r.volume4_next_m3>=200
        assert r.volume0_next_m3<=1500 and r.volume4_next_m3<=1500
        assert r.energy_kwh>=0 and r.unserved_m3>=0

def test_fail_p0_safe_stop():
    s=generate_scenario(1,steps=3)
    failure=list(s.failure_uniform)
    failure[0]=(0.,1.,1.)
    s=replace(s,failure_uniform=tuple(failure))
    result=run_episode(scenario=s,steps=3)
    assert result.records[1].availability[0] is False
    assert result.records[1].flow_m3_s==0.
    assert result.records[1].hydraulic_status=='SAFE_SHUTDOWN'

def test_immutable_json(tmp_path):
    a=run_episode(9,steps=3)
    target=tmp_path/'result.json'
    a.save_json(target)
    data=json.loads(target.read_text())
    assert data['summary']['steps']==3
    with pytest.raises(FileExistsError):a.save_json(target)

def test_full_horizon_and_explicit_contingency():
    full=run_episode(20261019)
    assert len(full.records)==96 and not full.terminated
    contingency=run_episode(20261018)
    assert contingency.terminated and contingency.reason=='NO_SAFE_ACTION_OR_STOP'
    assert contingency.records[-1].terminal_cost_um==200.
