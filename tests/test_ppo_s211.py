import numpy as np
import pytest
from hydro_lab.ppo_s211 import check_splits, SeedCycleEnv, PPOAgent, TRAIN_SEEDS, VALID_SEEDS, TEST_SEEDS


def test_disjoint_splits():
    check_splits()
    assert not (set(TRAIN_SEEDS) & set(VALID_SEEDS))
    assert not (set(TRAIN_SEEDS) & set(TEST_SEEDS))
    with pytest.raises(ValueError):
        check_splits([1,2], [2,3], [4])
    with pytest.raises(ValueError):
        check_splits([1,1], [2], [3])


def test_seed_cycle():
    env = SeedCycleEnv(seeds=(10,11), max_steps=2)
    try:
        assert env.reset()[1]['scenario_seed'] == 10
        assert env.reset()[1]['scenario_seed'] == 11
        assert env.reset()[1]['scenario_seed'] == 10
    finally:
        env.close()


def test_ppo_agent_observations_only():
    class Normalizer:
        training = True
        norm_reward = True
        def normalize_obs(self, x):
            return x / 2
    class Model:
        def predict(self, obs, deterministic=True):
            assert obs.shape == (15,)
            assert np.all(obs == .5)
            return np.array([1.2, 0., -1.2]), None
    normalizer = Normalizer()
    agent = PPOAgent(Model(), normalizer)
    assert normalizer.training is False
    assert normalizer.norm_reward is False
    assert np.allclose(agent.act(np.ones(15)), [1.,0.,-1.])
    with pytest.raises(ValueError):
        agent.act(np.ones(14))
