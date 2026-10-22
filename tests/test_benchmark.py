"""S2.5 scientific acceptance tests: paired comparison and leakage boundaries."""
import json
import numpy as np
import pytest
from hydro_lab.benchmark import (
    POLICIES, constant_policy, demand_feedback_policy, run_episode,
    paired_benchmark, save_report,
)
from hydro_lab.environment import HydroLabEnv


def test_constant_baseline_action():
    assert np.array_equal(constant_policy(np.zeros(15)),np.zeros(3,dtype=np.float32))


def test_feedback_action_bounds():
    for d in (0.,.11,.17):
        obs=np.array([500.,700.,d]+[0.]*12)
        a=demand_feedback_policy(obs)
        assert a.shape==(3,) and np.all(np.isfinite(a)) and np.all(np.abs(a)<=1)


def test_policy_does_not_receive_truth_or_info():
    observations=[]
    def probe(obs):
        assert isinstance(obs,np.ndarray) and obs.shape==(15,)
        observations.append(obs.copy())
        return np.zeros(3,dtype=np.float32)
    result=run_episode(20261019,'probe',max_steps=3,policy=probe)
    assert len(observations)==3 and result.steps==3


def test_episode_reproducible():
    a=run_episode(20261019,max_steps=8)
    b=run_episode(20261019,max_steps=8)
    assert a==b


def test_episode_reward_accounting():
    r=run_episode(20261019,max_steps=8)
    assert r.reward == pytest.approx(-sum((r.energy_cost_um,r.deficit_cost_um,r.maneuver_cost_um,r.terminal_cost_um)))


def test_episode_ends_at_horizon():
    r=run_episode(20261019,max_steps=4)
    assert 1<=r.steps<=4
    assert r.terminated or r.truncated


def test_mass_error_bounded():
    r=run_episode(20261019,max_steps=12)
    assert r.max_mass_error_m3 < 1e-7


def test_paired_benchmark_reproducible():
    a=paired_benchmark((20261019,20261020))
    b=paired_benchmark((20261019,20261020))
    assert a==b
    assert len(a['episodes'])==4
    assert a['comparison']['n_pairs']==2


def test_paired_benchmark_rejects_duplicate_seeds():
    with pytest.raises(ValueError): paired_benchmark((5,5))


def test_paired_benchmark_rejects_one_policy():
    with pytest.raises(ValueError): paired_benchmark((5,),('constant',))


def test_unknown_policy_rejected():
    with pytest.raises(ValueError): run_episode(1,'unknown')


def test_report_no_overwrite(tmp_path):
    report=paired_benchmark((20261019,))
    path=tmp_path/'report.json'
    assert save_report(report,path)==path
    assert json.loads(path.read_text())==report
    with pytest.raises(FileExistsError): save_report(report,path)


def test_observation_no_future_demand():
    e=HydroLabEnv(max_steps=4)
    obs,_=e.reset(seed=20261019)
    assert obs.shape==(15,)
    assert e.observation_space.contains(obs)
    assert 'evaluation_truth' not in _
    assert 'scenario' not in _


def test_evaluation_truth_not_in_observation():
    e=HydroLabEnv(max_steps=2)
    obs,_=e.reset(seed=20261019)
    obs2,_,_,_,info=e.step(np.zeros(3,dtype=np.float32))
    assert 'evaluation_truth' in info
    assert obs2.shape==(15,)
    assert 'health' in info['evaluation_truth']


def test_different_seeds_produce_distinct_scenarios():
    a=HydroLabEnv(max_steps=4);b=HydroLabEnv(max_steps=4)
    a.reset(seed=20261019);b.reset(seed=20261020)
    assert a.scenario.demand != b.scenario.demand
