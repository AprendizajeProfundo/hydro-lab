"""S2.11 Increment 04: episode-aware PPO training with independent validation.

Additive module: existing PPO trainer, simulator, reward, and checkpoint format unchanged.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import deque
from pathlib import Path

from .ppo_s211 import (PPOAgent, SeedCycleEnv, TRAIN_SEEDS, VALID_SEEDS,
                       check_splits)
from .agents import evaluate_episode

EPISODE_FIELDS = ('timesteps', 'episode', 'return_um', 'length', 'moving_mean_return_um')
VALIDATION_FIELDS = ('timesteps', 'seed', 'return_um', 'steps', 'early_termination',
                     'unserved_m3', 'energy_kwh', 'interventions')


def validate_parameters(timesteps, n_steps, batch_size, eval_every, validation_seeds):
    check_splits()
    if min(timesteps, n_steps, batch_size, eval_every) <= 0:
        raise ValueError('Training steps, rollout steps, batch size and evaluation interval must be positive')
    if n_steps % batch_size:
        raise ValueError('batch_size must divide n_steps')
    if not validation_seeds or len(set(validation_seeds)) != len(validation_seeds):
        raise ValueError('Validation seeds must be nonempty and unique')
    if not set(validation_seeds).issubset(VALID_SEEDS):
        raise ValueError('Validation seeds must belong to reserved validation partition')
    if set(validation_seeds) & set(TRAIN_SEEDS):
        raise ValueError('Training and validation seeds overlap')


def write_table(path, fields, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def train(output, *, timesteps=8192, seed=42, n_steps=256, batch_size=64,
          eval_every=1024, validation_count=8, max_steps=96):
    if not 1 <= validation_count <= len(VALID_SEEDS):
        raise ValueError('validation_count must be between 1 and 32')
    selected = tuple(VALID_SEEDS[:validation_count])
    validate_parameters(timesteps, n_steps, batch_size, eval_every, selected)
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
        from stable_baselines3.common.callbacks import BaseCallback
        from stable_baselines3.common.monitor import Monitor
    except ImportError as exc:
        raise RuntimeError('Install dependencies with python -m pip install -e ".[ppo]"') from exc

    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'Refusing to overwrite nonempty directory: {output}')
    output.mkdir(parents=True, exist_ok=True)
    vec = DummyVecEnv([lambda: Monitor(SeedCycleEnv(max_steps=max_steps))])
    normalizer = VecNormalize(vec, norm_obs=True, norm_reward=False, clip_obs=10.0)
    model = PPO('MlpPolicy', normalizer, seed=seed, verbose=0, device='cpu',
                n_steps=n_steps, batch_size=batch_size, gamma=.99, gae_lambda=.95,
                clip_range=.2, learning_rate=3e-4, ent_coef=0.,
                policy_kwargs={'net_arch': [64, 64]})
    episodes, validations, rollout_metrics = [], [], []

    class Instrumentation(BaseCallback):
        def __init__(self):
            super().__init__()
            self.recent = deque(maxlen=20)
            self.next_eval = eval_every
            self.last_rollout = 0

        def _on_step(self):
            for info in self.locals.get('infos', []):
                ep = info.get('episode')
                if ep is not None:
                    reward = float(ep['r'])
                    self.recent.append(reward)
                    episodes.append({'timesteps': int(self.num_timesteps),
                                     'episode': len(episodes) + 1,
                                     'return_um': reward, 'length': int(ep['l']),
                                     'moving_mean_return_um': sum(self.recent) / len(self.recent)})
            if self.num_timesteps >= self.next_eval:
                # PPOAgent normalizes with current *training* moments but never updates them
                # during evaluation; raw environment observations and raw UM rewards.
                agent = PPOAgent(self.model, normalizer)
                for scenario_seed in selected:
                    r = evaluate_episode(agent, seed=scenario_seed, max_steps=max_steps)
                    validations.append({'timesteps': int(self.num_timesteps),
                                        'seed': scenario_seed, 'return_um': r.return_um,
                                        'steps': r.steps,
                                        'early_termination': bool(r.terminated and r.steps < max_steps),
                                        'unserved_m3': r.unserved_m3, 'energy_kwh': r.energy_kwh,
                                        'interventions': r.interventions})
                # PPOAgent switches training off: restore normalization mode explicitly.
                normalizer.training = True
                self.next_eval += eval_every
            return True

        def _on_rollout_end(self):
            # PPO optimization diagnostics are logged AFTER _on_rollout_end;
            # record them at the next rollout (label as previous update).
            if self.last_rollout:
                row = {'timesteps_after_update': self.last_rollout}
                for k in ('train/approx_kl', 'train/clip_fraction', 'train/entropy_loss',
                          'train/value_loss', 'train/policy_gradient_loss',
                          'train/explained_variance'):
                    v = self.model.logger.name_to_value.get(k)
                    row[k.replace('/', '_')] = float(v) if v is not None and math.isfinite(float(v)) else None
                rollout_metrics.append(row)
            self.last_rollout = int(self.num_timesteps)

    callback = Instrumentation()
    try:
        model.learn(total_timesteps=int(timesteps), callback=callback)
        # Save the final update diagnostics too.
        if callback.last_rollout:
            row = {'timesteps_after_update': callback.last_rollout}
            for k in ('train/approx_kl', 'train/clip_fraction', 'train/entropy_loss',
                      'train/value_loss', 'train/policy_gradient_loss', 'train/explained_variance'):
                v = model.logger.name_to_value.get(k)
                row[k.replace('/', '_')] = float(v) if v is not None and math.isfinite(float(v)) else None
            if not rollout_metrics or rollout_metrics[-1]['timesteps_after_update'] != callback.last_rollout:
                rollout_metrics.append(row)
        model.save(str(output / 'ppo_model.zip'))
        normalizer.save(str(output / 'normalization.pkl'))
        metadata = {'generation': 'S2.11', 'increment': '04', 'algorithm': 'PPO',
                    'seed': int(seed), 'requested_timesteps': int(timesteps),
                    'actual_timesteps': int(model.num_timesteps), 'n_steps': int(n_steps),
                    'batch_size': int(batch_size), 'max_steps': int(max_steps),
                    'reward': 'S2.10 unchanged, UM', 'norm_obs': True,
                    'norm_reward': False, 'validation_seeds': list(selected),
                    'train_seed_range': [TRAIN_SEEDS[0], TRAIN_SEEDS[-1]],
                    'eval_every': int(eval_every), 'episodes_observed': len(episodes),
                    'status': 'trained_not_scientifically_validated'}
        (output / 'metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
        write_table(output / 'episodes_training.csv', EPISODE_FIELDS, episodes)
        write_table(output / 'validation_during_training.csv', VALIDATION_FIELDS, validations)
        diagnostic_fields = ('timesteps_after_update', 'train_approx_kl', 'train_clip_fraction',
                             'train_entropy_loss', 'train_value_loss',
                             'train_policy_gradient_loss', 'train_explained_variance')
        write_table(output / 'ppo_diagnostics.csv', diagnostic_fields, rollout_metrics)
        return metadata
    finally:
        normalizer.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description='S2.11 increment 04 instrumented PPO training')
    parser.add_argument('--output', required=True)
    parser.add_argument('--timesteps', type=int, default=8192)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--n-steps', type=int, default=256)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--eval-every', type=int, default=1024)
    parser.add_argument('--validation-count', type=int, default=8)
    args = parser.parse_args(argv)
    print(json.dumps(train(args.output, timesteps=args.timesteps, seed=args.seed,
                           n_steps=args.n_steps, batch_size=args.batch_size,
                           eval_every=args.eval_every,
                           validation_count=args.validation_count), indent=2))


if __name__ == '__main__':
    main()
