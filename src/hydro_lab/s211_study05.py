"""S2.11 increment 05: paired hydraulic diagnostics and replicated PPO studies.

Additive: does not change simulator, rewards, prior trainers or checkpoints.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

from .agents import evaluate_episode
from .ppo_s211 import VALID_SEEDS, TEST_SEEDS, check_splits, load_agent
from .s211_train04 import train as train_instrumented

BASELINES = ('constant', 'demand_feedback', 'health_robust')
FIELDS = ('training_seed', 'scenario_seed', 'policy', 'return_um', 'steps',
          'early_termination', 'energy_kwh', 'served_m3', 'unserved_m3',
          'interventions', 'intervention_distance_total', 'energy_um',
          'deficit_um', 'maneuver_um', 'terminal_um')


def write_csv(path, fields, rows):
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _baseline(name):
    from .benchmark import POLICIES
    class Baseline:
        def act(self, observation, *, deterministic=True):
            return POLICIES[name](observation)
    return Baseline()


def episode_row(result, training_seed, policy):
    row = dict(training_seed=int(training_seed), scenario_seed=int(result.seed),
               policy=policy, return_um=float(result.return_um), steps=int(result.steps),
               early_termination=bool(result.terminated and result.steps < 96),
               energy_kwh=float(result.energy_kwh), served_m3=float(result.served_m3),
               unserved_m3=float(result.unserved_m3), interventions=int(result.interventions),
               intervention_distance_total=float(result.intervention_distance_total))
    row.update({k: float(result.costs_um.get(k, 0)) for k in
                ('energy_um', 'deficit_um', 'maneuver_um', 'terminal_um')})
    return row


def paired_deltas(rows, baseline):
    by_key = {(int(r['training_seed']), int(r['scenario_seed']), r['policy']): r for r in rows}
    out = []
    for row in rows:
        if row['policy'] != 'PPO':
            continue
        key = (int(row['training_seed']), int(row['scenario_seed']), baseline)
        if key not in by_key:
            raise ValueError(f'Missing matched baseline: {key}')
        other = by_key[key]
        out.append(dict(training_seed=int(row['training_seed']),
                        scenario_seed=int(row['scenario_seed']), baseline=baseline,
                        delta_return_um=float(row['return_um']) - float(other['return_um']),
                        delta_unserved_m3=float(row['unserved_m3']) - float(other['unserved_m3']),
                        delta_energy_kwh=float(row['energy_kwh']) - float(other['energy_kwh']),
                        delta_early_termination=int(str(row['early_termination']).lower() == 'true') -
                                                int(str(other['early_termination']).lower() == 'true')))
    return out


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(int(r['training_seed']), r['policy'])].append(r)
    output = []
    for (seed, policy), subset in sorted(groups.items()):
        values = [float(r['return_um']) for r in subset]
        output.append(dict(training_seed=seed, policy=policy, n=len(values),
                           mean_return_um=mean(values), median_return_um=median(values),
                           sd_return_um=stdev(values) if len(values) > 1 else 0.,
                           mean_unserved_m3=mean(float(r['unserved_m3']) for r in subset),
                           mean_energy_kwh=mean(float(r['energy_kwh']) for r in subset),
                           early_terminations=sum(str(r['early_termination']).lower() == 'true'
                                                  for r in subset)))
    return output


def confidence_across_training_seeds(paired):
    """Descriptive normal 95% interval over independent training-seed means.

    Not a confirmatory CI: 1.96 approximation is unreliable with few seeds.
    """
    groups = defaultdict(list)
    for r in paired:
        groups[(r['baseline'], int(r['training_seed']))].append(float(r['delta_return_um']))
    by_baseline = defaultdict(list)
    for (baseline, _), values in groups.items():
        by_baseline[baseline].append(mean(values))
    result = []
    for baseline, values in sorted(by_baseline.items()):
        n = len(values)
        avg = mean(values)
        se = stdev(values) / math.sqrt(n) if n > 1 else None
        result.append(dict(baseline=baseline, n_training_seeds=n,
                           mean_seed_level_delta_um=avg,
                           sd_seed_level_delta_um=stdev(values) if n > 1 else None,
                           normal_approx_low_um=avg - 1.96 * se if se is not None else None,
                           normal_approx_high_um=avg + 1.96 * se if se is not None else None))
    return result


def diagnose(checkpoints, *, output, split='validation', scenario_count=8,
             baselines=BASELINES):
    check_splits()
    if split not in ('validation', 'test'):
        raise ValueError('split must be validation or test')
    seeds = VALID_SEEDS if split == 'validation' else TEST_SEEDS
    if not 1 <= scenario_count <= len(seeds):
        raise ValueError('scenario_count out of range')
    if not checkpoints:
        raise ValueError('At least one checkpoint required')
    if len(set(map(str, checkpoints))) != len(checkpoints):
        raise ValueError('Duplicate checkpoints')
    if not set(baselines).issubset(BASELINES):
        raise ValueError('Unknown baseline')
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'Output directory is not empty: {output}')
    # Validate metadata before creating any output.
    loaded = []
    for checkpoint in checkpoints:
        path = Path(checkpoint)
        metadata = json.loads((path / 'metadata.json').read_text(encoding='utf-8'))
        if metadata.get('algorithm') != 'PPO' or 'seed' not in metadata:
            raise ValueError(f'Invalid checkpoint metadata: {path}')
        loaded.append((path, int(metadata['seed'])))
    if len({seed for _, seed in loaded}) != len(loaded):
        raise ValueError('Each checkpoint must have a distinct training seed')
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for path, train_seed in loaded:
        agent = load_agent(path)
        for scenario in seeds[:scenario_count]:
            for policy, candidate in [('PPO', agent)] + [(b, _baseline(b)) for b in baselines]:
                result = evaluate_episode(candidate, seed=scenario)
                rows.append(episode_row(result, train_seed, policy))
    paired = [r for b in baselines for r in paired_deltas(rows, b)]
    write_csv(output / 'episodes.csv', FIELDS, rows)
    write_csv(output / 'paired.csv', ('training_seed', 'scenario_seed', 'baseline',
              'delta_return_um', 'delta_unserved_m3', 'delta_energy_kwh',
              'delta_early_termination'), paired)
    summaries = summarize(rows)
    write_csv(output / 'summary_by_seed.csv', ('training_seed', 'policy', 'n',
              'mean_return_um', 'median_return_um', 'sd_return_um',
              'mean_unserved_m3', 'mean_energy_kwh', 'early_terminations'), summaries)
    uncertainty = confidence_across_training_seeds(paired)
    write_csv(output / 'between_seed_variability.csv', ('baseline', 'n_training_seeds',
              'mean_seed_level_delta_um', 'sd_seed_level_delta_um',
              'normal_approx_low_um', 'normal_approx_high_um'), uncertainty)
    report = dict(generation='S2.11', increment='05', split=split,
                  training_seeds=[seed for _, seed in loaded],
                  scenario_seeds=list(seeds[:scenario_count]),
                  n_episodes=len(rows), n_paired=len(paired),
                  interpretation='Exploratory only. Seeds are not independent hydraulic populations; '
                  'normal intervals with few training seeds are not confirmatory.',
                  note='No claim of robustness or safety without prespecified criteria.')
    (output / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def train_replicates(output, *, training_seeds=(41, 42, 43), timesteps=4096,
                     eval_every=1024, validation_count=8):
    if not training_seeds or len(set(training_seeds)) != len(training_seeds):
        raise ValueError('Training seeds must be nonempty and distinct')
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'Output directory not empty: {output}')
    output.mkdir(parents=True, exist_ok=True)
    completed = []
    for seed in training_seeds:
        folder = output / f'seed_{seed}'
        train_instrumented(folder, timesteps=timesteps, seed=seed,
                           eval_every=eval_every, validation_count=validation_count)
        completed.append(str(folder))
    (output / 'replicates.json').write_text(json.dumps({'training_seeds': list(training_seeds),
        'checkpoints': completed, 'timesteps_per_seed': timesteps}, indent=2), encoding='utf-8')
    return completed


def main(argv=None):
    parser = argparse.ArgumentParser(description='S2.11 increment 05: replicated PPO study')
    commands = parser.add_subparsers(dest='command', required=True)
    t = commands.add_parser('train-replicates')
    t.add_argument('--output', required=True)
    t.add_argument('--seeds', nargs='+', type=int, default=[41, 42, 43])
    t.add_argument('--timesteps', type=int, default=4096)
    t.add_argument('--eval-every', type=int, default=1024)
    t.add_argument('--validation-count', type=int, default=8)
    d = commands.add_parser('diagnose')
    d.add_argument('--checkpoint', nargs='+', required=True)
    d.add_argument('--output', required=True)
    d.add_argument('--split', choices=['validation', 'test'], default='validation')
    d.add_argument('--scenario-count', type=int, default=8)
    args = parser.parse_args(argv)
    if args.command == 'train-replicates':
        print(json.dumps(train_replicates(args.output, training_seeds=args.seeds,
             timesteps=args.timesteps, eval_every=args.eval_every,
             validation_count=args.validation_count), indent=2))
    else:
        print(json.dumps(diagnose(args.checkpoint, output=args.output,
             split=args.split, scenario_count=args.scenario_count), indent=2))


if __name__ == '__main__':
    main()
