import numpy as np
import pytest
from hydro_lab.benchmark import demand_feedback_policy, health_aware_policy
from hydro_lab.control_center import EpisodeSession
from hydro_lab.active_benchmark import active_paired_benchmark


def test_equal_health_matches_feedback():
    obs=np.zeros(15,dtype=np.float32);obs[12:15]=.95
    np.testing.assert_allclose(health_aware_policy(obs),demand_feedback_policy(obs))


def test_observed_health_changes_action():
    obs=np.zeros(15,dtype=np.float32);obs[12:15]=(.95,.95,.95)
    a=health_aware_policy(obs)
    obs[12:15]=(.95,.70,.95)
    b=health_aware_policy(obs)
    assert not np.array_equal(a,b)
    assert b[1]<a[1]


def test_no_true_health_leak():
    obs=np.zeros(15,dtype=np.float32);obs[12:15]=.95
    assert health_aware_policy(obs).shape==(3,)
    with pytest.raises(ValueError): health_aware_policy(np.zeros(3))


def test_inspection_changes_next_controller_input():
    s=EpisodeSession(seed=2026,policy_name='health_aware',robot_policy='manual',max_steps=4)
    try:
        s.step(robot_action='move_P0')
        s.step(robot_action='inspect')
        assert s.records[1]['robot']['status']=='INSPECTED'
        expected=s.records[1]['robot']['belief_estimates']
        s.step(robot_action='wait')
        np.testing.assert_allclose(s.records[2]['controller_health_observation'],expected,rtol=1e-6)
    finally:s.close()


def test_paired_reproducible_and_costed():
    a=active_paired_benchmark((12,13),max_steps=8)
    b=active_paired_benchmark((12,13),max_steps=8)
    assert a==b
    assert len(a['episodes'])==8
    assert a['summary']['health_aware/off']['robot_cost_um']==0
    assert a['summary']['health_aware/uncertainty']['robot_cost_um']>0
