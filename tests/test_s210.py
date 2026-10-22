import numpy as np
import pytest
from hydro_lab.robot import InspectionRobot, choose_value_action
from hydro_lab.observations import HealthBelief
from hydro_lab.benchmark import health_robust_policy, demand_feedback_policy
from hydro_lab.control_center import EpisodeSession
from hydro_lab.teaching_comparison import run_teaching_comparison


def test_value_policy_may_wait_when_information_not_worth_cost():
    belief=HealthBelief.initial()
    belief.uncertainty[:]=.02
    assert choose_value_action(InspectionRobot(),belief)=='wait'


def test_value_policy_initially_goes_to_p0():
    assert choose_value_action(InspectionRobot(),HealthBelief.initial())=='move_P0'


def test_value_policy_respects_battery_and_budget():
    r=InspectionRobot(battery=3.)
    assert choose_value_action(r,HealthBelief.initial())=='wait'
    r=InspectionRobot(inspections=3)
    assert choose_value_action(r,HealthBelief.initial())=='wait'


def test_value_policy_uses_estimated_health_not_true_health():
    b=HealthBelief.initial()
    b.estimate[2]=.70
    b.uncertainty[:]=[.02,.02,.05]
    assert choose_value_action(InspectionRobot(),b)=='move_P0'  # shortest path toward PS


def test_robust_controller_bounds_health_adjustment():
    o=np.zeros(15,dtype=np.float32)
    o[0:3]=[700,700,.11]
    o[12:15]=[.65,.95,1.]
    diff=health_robust_policy(o)-demand_feedback_policy(o)
    assert np.max(np.abs(diff)) <= .0350001


def test_value_session_and_accounting():
    s=EpisodeSession(seed=2,policy_name='health_robust',robot_policy='value',max_steps=10)
    try:
        s.advance(10)
        assert len(s.records)>0
        assert s.robot.cost_um>=0
        assert s.robot.inspections<=3
        assert abs(s.reward_total-s.report()['reward_total'])<1e-10
    finally:s.close()


def test_teaching_comparison_small():
    r=run_teaching_comparison(seeds=(0,),regimes=('baseline',),steps=3)
    assert len(r['episodes'])==4
    assert 'paired_robust_value_minus_robust_off' in r['summary']['baseline']


def test_invalid_policy_parameters():
    with pytest.raises(ValueError):
        choose_value_action(InspectionRobot(),HealthBelief.initial(),threshold=-1)
