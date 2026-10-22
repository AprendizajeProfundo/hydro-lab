from dataclasses import replace
import numpy as np
import pytest
from hydro_lab.scientific_validation import scenario_for,run_validation,save_validation
from hydro_lab.control_center import EpisodeSession


def test_scenario_reproducible_and_stress_exogenous():
    base=scenario_for(9,'baseline',12)
    stress=scenario_for(9,'accelerated_wear',12)
    assert base==scenario_for(9,'baseline',12)
    assert stress.initial_health==(.75,.90,.90)
    assert stress.demand==base.demand
    assert stress.failure_uniform==base.failure_uniform
    assert np.isclose(stress.health_noise[0][0]-base.health_noise[0][0],-.001)


def test_scenario_injection_validation():
    s=scenario_for(1,'degraded',5)
    with pytest.raises(ValueError):EpisodeSession(seed=2,scenario=s,max_steps=5)
    with pytest.raises(ValueError):EpisodeSession(seed=1,scenario=s,nominal=True,max_steps=5)


def test_benchmark_factorial_and_accounting():
    r=run_validation((1,2),regimes=('baseline',),steps=8)
    assert len(r['episodes'])==8
    assert r['schema'].endswith('v1')
    for row in r['episodes']:
        assert np.isclose(row['net_reward_um']+row['robot_cost_um'],row['hydraulic_reward_um'])
    a=r['summary']['baseline']['health_aware']
    assert a['net_reward_difference_um']['n']==2
    assert a['robot_cost_um']['mean']>=0


def test_determinism_and_output(tmp_path):
    a=run_validation((3,),regimes=('degraded',),steps=6)
    assert a==run_validation((3,),regimes=('degraded',),steps=6)
    paths=save_validation(a,tmp_path)
    assert all(p.exists() for p in paths)
    with pytest.raises(FileExistsError):save_validation(a,tmp_path)


def test_invalid_design():
    with pytest.raises(ValueError):run_validation((1,1))
    with pytest.raises(ValueError):run_validation((1,),regimes=('unknown',))
    with pytest.raises(ValueError):run_validation((1,),steps=0)
