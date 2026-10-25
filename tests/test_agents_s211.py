import numpy as np
import pytest
from hydro_lab.agents import Agent, ConstantAgent, evaluate_episode


def test_constant_agent_protocol_and_action():
    agent = ConstantAgent()
    assert isinstance(agent, Agent)
    assert np.array_equal(agent.act(np.zeros(15)), np.zeros(3))


def test_evaluation_reproducible_and_no_privileged_state():
    a = evaluate_episode(ConstantAgent(), seed=17, max_steps=4)
    b = evaluate_episode(ConstantAgent(), seed=17, max_steps=4)
    assert a == b
    assert a.steps <= 4
    assert 'evaluation_truth' not in str(a.traces)
    assert a.return_um == pytest.approx(-sum(a.costs_um.values()))
    assert all('requested' in t and 'executed' in t for t in a.traces)


def test_reject_invalid_agent_actions():
    class BadAgent:
        def act(self, observation, *, deterministic=True):
            return np.array([np.nan, 0, 0])
    with pytest.raises(ValueError, match='Agent action'):
        evaluate_episode(BadAgent(), seed=4, max_steps=2)
