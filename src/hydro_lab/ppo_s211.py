"""S2.11 optional Stable-Baselines3 PPO integration (no changes to S2.10 physics).

Stable-Baselines3 is imported lazily: base simulator/tests remain usable without it.
"""
from __future__ import annotations
import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
import numpy as np
from .agents import evaluate_episode
from .benchmark import POLICIES

TRAIN_SEEDS = tuple(range(10000, 11000))
VALID_SEEDS = tuple(range(20000, 20032))
TEST_SEEDS = tuple(range(30000, 30032))


def check_splits(train=TRAIN_SEEDS, valid=VALID_SEEDS, test=TEST_SEEDS):
    sets = [set(map(int, s)) for s in (train, valid, test)]
    if any(not s for s in sets) or any(len(s) != len(seq) for s, seq in zip(sets, (train, valid, test))):
        raise ValueError('Seed partitions must be nonempty and internally unique')
    if any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError('Training, validation and test seeds must be disjoint')


def _sb3():
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
        from stable_baselines3.common.callbacks import BaseCallback
        return PPO, DummyVecEnv, VecNormalize, BaseCallback
    except ImportError as exc:
        raise RuntimeError('Install PPO dependencies: python -m pip install -e ".[ppo]"') from exc


from gymnasium import Wrapper

class SeedCycleEnv(Wrapper):
    """Gymnasium-compatible wrapper cycling only training scenario seeds.

    Delegates observation/action spaces; episode seeds never come from validation/test.
    """
    def __init__(self, seeds=TRAIN_SEEDS, max_steps=96):
        from .environment import HydroLabEnv
        super().__init__(HydroLabEnv(max_steps=max_steps))
        self.seeds = tuple(int(x) for x in seeds)
        if not self.seeds:
            raise ValueError('Need at least one training seed')
        self.cursor = 0
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space

    def reset(self, *, seed=None, options=None):
        # Explicit seed (used by SB3 seeding) is intentionally ignored: the
        # experiment protocol, not SB3 internals, owns scenario partitioning.
        chosen = self.seeds[self.cursor % len(self.seeds)]
        self.cursor += 1
        return self.env.reset(seed=chosen, options=options)

    def step(self, action):
        return self.env.step(action)

    def close(self):
        self.env.close()



class PPOAgent:
    """Inference-only policy; normalize observation with frozen training statistics."""
    def __init__(self, model, normalizer):
        self.model = model
        self.normalizer = normalizer
        self.normalizer.training = False
        self.normalizer.norm_reward = False

    def act(self, observation, *, deterministic=True):
        obs = np.asarray(observation, dtype=np.float32)
        if obs.shape != (15,) or not np.isfinite(obs).all():
            raise ValueError('Expected 15 finite observable features')
        normalized = self.normalizer.normalize_obs(obs.reshape(1, -1)).reshape(-1)
        action, _ = self.model.predict(normalized, deterministic=deterministic)
        return np.clip(np.asarray(action, dtype=np.float32), -1, 1)


def load_agent(folder):
    PPO, DummyVecEnv, VecNormalize, _ = _sb3()
    folder = Path(folder)
    if not (folder / 'metadata.json').exists():
        raise FileNotFoundError('Missing metadata.json: not a complete S2.11 checkpoint')
    from .environment import HydroLabEnv
    vec = DummyVecEnv([lambda: HydroLabEnv()])
    normalizer = VecNormalize.load(str(folder / 'normalization.pkl'), vec)
    model = PPO.load(str(folder / 'ppo_model.zip'), device='cpu')
    return PPOAgent(model, normalizer)


def train(folder, *, timesteps=4096, seed=42, n_steps=256, batch_size=64, max_steps=96):
    check_splits()
    if timesteps <= 0 or n_steps <= 0 or batch_size <= 0 or n_steps % batch_size:
        raise ValueError('Positive timesteps, n_steps and a batch_size dividing n_steps required')
    PPO, DummyVecEnv, VecNormalize, BaseCallback = _sb3()
    folder = Path(folder)
    if folder.exists() and any(folder.iterdir()):
        raise FileExistsError(f'Checkpoint directory not empty: {folder}')
    folder.mkdir(parents=True, exist_ok=True)
    vec = DummyVecEnv([lambda: SeedCycleEnv(max_steps=max_steps)])
    normalizer = VecNormalize(vec, norm_obs=True, norm_reward=False, clip_obs=10.0)
    model = PPO('MlpPolicy', normalizer, seed=seed, verbose=0, device='cpu',
                n_steps=n_steps, batch_size=batch_size, gamma=.99, gae_lambda=.95,
                clip_range=.2, learning_rate=3e-4, ent_coef=0.,
                policy_kwargs={'net_arch': [64, 64]})
    history = []
    class RolloutLog(BaseCallback):
        def _on_step(self):
            return True
        def _on_rollout_end(self):
            history.append({'timesteps': int(self.num_timesteps),
                            'mean_episode_reward': float(self.model.ep_info_buffer[-1]['r'])
                            if self.model.ep_info_buffer else None})
    try:
        model.learn(total_timesteps=int(timesteps), callback=RolloutLog())
        model.save(str(folder / 'ppo_model.zip'))
        normalizer.save(str(folder / 'normalization.pkl'))
        metadata = {'generation': 'S2.11', 'algorithm': 'PPO', 'seed': int(seed),
                    'requested_timesteps': int(timesteps), 'actual_timesteps': int(model.num_timesteps),
                    'n_steps': int(n_steps), 'batch_size': int(batch_size),
                    'max_steps': int(max_steps), 'reward': 'S2.10 unchanged, UM',
                    'norm_obs': True, 'norm_reward': False,
                    'train_seed_range': [TRAIN_SEEDS[0], TRAIN_SEEDS[-1]],
                    'validation_seeds': list(VALID_SEEDS), 'test_seeds': list(TEST_SEEDS),
                    'status': 'trained_not_scientifically_validated'}
        (folder / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        (folder / 'rollouts.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
    finally:
        normalizer.close()
    return metadata


class _BaselineAgent:
    def __init__(self, name):
        self.policy = POLICIES[name]
    def act(self, observation, *, deterministic=True):
        return self.policy(observation)


def evaluate(folder, *, split='validation', baselines=('constant', 'demand_feedback', 'health_robust')):
    check_splits()
    if split not in ('validation', 'test'):
        raise ValueError('split must be validation or test')
    seeds = VALID_SEEDS if split == 'validation' else TEST_SEEDS
    agent = load_agent(folder)
    rows = []
    for seed in seeds:
        for name, candidate in [('PPO', agent)] + [(n, _BaselineAgent(n)) for n in baselines]:
            result = evaluate_episode(candidate, seed=seed)
            row = {'seed': seed, 'policy': name, 'return_um': result.return_um,
                   'steps': result.steps, 'terminated': result.terminated,
                   'truncated': result.truncated, 'energy_kwh': result.energy_kwh,
                   'served_m3': result.served_m3, 'unserved_m3': result.unserved_m3,
                   'interventions': result.interventions,
                   'intervention_distance_total': result.intervention_distance_total}
            row.update(result.costs_um)
            rows.append(row)
    output = Path(folder) / f'evaluation_{split}.csv'
    with output.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description='Hydro-Lab S2.11 PPO training and evaluation')
    sub = parser.add_subparsers(dest='command', required=True)
    t = sub.add_parser('train')
    t.add_argument('--output', required=True)
    t.add_argument('--timesteps', type=int, default=4096)
    t.add_argument('--seed', type=int, default=42)
    t.add_argument('--n-steps', type=int, default=256)
    t.add_argument('--batch-size', type=int, default=64)
    e = sub.add_parser('evaluate')
    e.add_argument('--checkpoint', required=True)
    e.add_argument('--split', choices=['validation', 'test'], default='validation')
    args = parser.parse_args(argv)
    if args.command == 'train':
        print(json.dumps(train(args.output, timesteps=args.timesteps, seed=args.seed,
                               n_steps=args.n_steps, batch_size=args.batch_size), indent=2))
    else:
        print(evaluate(args.checkpoint, split=args.split))

if __name__ == '__main__':
    main()
