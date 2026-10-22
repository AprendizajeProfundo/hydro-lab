import numpy as np
import pytest
from hydro_lab.robot import InspectionRobot,choose_uncertainty_action
from hydro_lab.observations import HealthBelief
from hydro_lab.control_center import EpisodeSession

def test_logistics_graph_and_battery():
    r=InspectionRobot();b=HealthBelief.initial();rng=np.random.default_rng(10)
    assert r.shortest_route('PN')==('P0','PN')
    e=r.act('move_PN',health=(.8,.8,.8),belief=b,rng=rng)
    assert e['status']=='BLOCKED_ROUTE' and r.battery==100
    assert r.act('move_P0',health=(.8,.8,.8),belief=b,rng=rng)['status']=='MOVED'
    assert r.position=='P0' and r.battery==96

def test_inspection_is_information_not_repair():
    r=InspectionRobot(position='P0');b=HealthBelief.initial();rng=np.random.default_rng(1)
    truth=(.70,.8,.9);old=b.uncertainty[0]
    e=r.act('inspect',health=truth,belief=b,rng=rng)
    assert e['status']=='INSPECTED' and e['pump']=='P0'
    assert b.uncertainty[0]<old and b.estimate[0]<.95
    assert truth==(.70,.8,.9) and r.battery==92
    assert e['measurement'] != truth[0]

def test_deterministic_robot_sensor():
    def run():
        s=EpisodeSession(seed=123,robot_policy='manual',max_steps=4)
        s.step(robot_action='move_P0');s.step(robot_action='inspect')
        return s.report()
    a,b=run(),run()
    assert a['records'][1]['robot']['measurement']==b['records'][1]['robot']['measurement']
    assert a['robot_summary']['inspections']==1

def test_no_robot_preserves_original_reward():
    from hydro_lab.environment import HydroLabEnv
    from hydro_lab.benchmark import POLICIES
    env=HydroLabEnv(max_steps=2);obs,_=env.reset(seed=13)
    _,rew,_,_,_=env.step(POLICIES['constant'](obs))
    s=EpisodeSession(seed=13,policy_name='constant',robot_policy='off',max_steps=2)
    assert s.step()['reward']==pytest.approx(rew)

def test_robot_inspection_cost_is_charged():
    s=EpisodeSession(seed=13,robot_policy='manual',max_steps=4)
    s.step(robot_action='move_P0');r=s.step(robot_action='inspect')
    assert r['robot']['status']=='INSPECTED'
    assert r['costs']['inspection_um']==3
    assert r['reward']==pytest.approx(-sum(r['costs'].values()))

def test_heuristic_and_invalid_action():
    r=InspectionRobot();b=HealthBelief.initial();b.uncertainty[2]=.3
    assert choose_uncertainty_action(r,b)=='move_P0'
    with pytest.raises(ValueError):r.act('teleport',health=(.8,.8,.8),belief=b,rng=np.random.default_rng(1))
