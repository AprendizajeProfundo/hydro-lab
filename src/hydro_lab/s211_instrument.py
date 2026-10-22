"""S2.11 G0.1: reproducible, dependency-light PPO experimental reports.

Read-only analysis: does not alter simulator, policy, or reward.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

FIELDS = ('return_um', 'steps', 'energy_kwh', 'served_m3', 'unserved_m3',
          'interventions', 'intervention_distance_total', 'energy_um',
          'deficit_um', 'maneuver_um', 'terminal_um')


def read_evaluation(path):
    path = Path(path)
    with path.open(newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        required = {'seed', 'policy', 'return_um', 'steps', 'terminated', 'truncated',
                    'energy_kwh', 'unserved_m3', 'interventions'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f'Missing columns: {sorted(required - set(reader.fieldnames or []))}')
        rows = []
        for i, raw in enumerate(reader, 2):
            row = dict(raw)
            row['seed'] = int(row['seed'])
            for key in FIELDS:
                if key in row and row[key] not in ('', None):
                    row[key] = float(row[key])
                    if not math.isfinite(row[key]):
                        raise ValueError(f'Nonfinite {key} on line {i}')
            for key in ('terminated', 'truncated'):
                value = str(row[key]).strip().lower()
                if value not in ('true', 'false', '1', '0'):
                    raise ValueError(f'Invalid {key} on line {i}')
                row[key] = value in ('true', '1')
            rows.append(row)
    if not rows:
        raise ValueError('Empty evaluation CSV')
    pairs = [(r['seed'], r['policy']) for r in rows]
    if len(set(pairs)) != len(pairs):
        raise ValueError('Duplicate (seed, policy) pairs')
    return rows


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['policy']].append(row)
    report = []
    for policy, items in sorted(groups.items()):
        returns = [r['return_um'] for r in items]
        entry = {'policy': policy, 'n': len(items),
                 'mean_return_um': statistics.mean(returns),
                 'median_return_um': statistics.median(returns),
                 'sd_return_um': statistics.stdev(returns) if len(returns)>1 else None,
                 'early_terminations': sum(r['terminated'] and r['steps'] < 96 for r in items),
                 'mean_unserved_m3': statistics.mean(r['unserved_m3'] for r in items),
                 'mean_energy_kwh': statistics.mean(r['energy_kwh'] for r in items),
                 'mean_interventions': statistics.mean(r['interventions'] for r in items)}
        report.append(entry)
    return report


def paired(rows, target='PPO'):
    by_policy = defaultdict(dict)
    for row in rows:
        by_policy[row['policy']][row['seed']] = row
    if target not in by_policy:
        raise ValueError(f'Missing target policy: {target}')
    result = []
    for baseline in sorted(set(by_policy) - {target}):
        seeds = sorted(set(by_policy[target]) & set(by_policy[baseline]))
        if not seeds:
            continue
        delta = [by_policy[target][s]['return_um'] - by_policy[baseline][s]['return_um'] for s in seeds]
        result.append({'target': target, 'baseline': baseline, 'n_pairs': len(seeds),
                       'mean_delta_return_um': statistics.mean(delta),
                       'median_delta_return_um': statistics.median(delta),
                       'wins': sum(x > 0 for x in delta), 'ties': sum(x == 0 for x in delta),
                       'losses': sum(x < 0 for x in delta),
                       'sd_delta_return_um': statistics.stdev(delta) if len(delta)>1 else None})
    return result


def write_csv(path, rows):
    if not rows:
        return
    with Path(path).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def generate(folder, *, output=None, split='validation'):
    folder = Path(folder)
    output = Path(output) if output else folder / 'instrumentacion'
    output.mkdir(parents=True, exist_ok=True)
    source = folder / f'evaluation_{split}.csv'
    rows = read_evaluation(source)
    summary, comparisons = summarize(rows), paired(rows)
    write_csv(output / f'resumen_{split}.csv', summary)
    write_csv(output / f'pareadas_{split}.csv', comparisons)
    report = {'source': str(source), 'split': split, 'summary': summary, 'paired': comparisons,
              'caution': 'Descriptive results only; no confidence intervals or scientific validation.'}
    rollouts = folder / 'rollouts.json'
    if rollouts.exists():
        data = json.loads(rollouts.read_text(encoding='utf-8'))
        if not isinstance(data, list):
            raise ValueError('rollouts.json must contain a list')
        curve = []
        for entry in data:
            curve.append({'timesteps': int(entry['timesteps']),
                          'mean_episode_reward': entry.get('mean_episode_reward')})
        write_csv(output / 'curva_entrenamiento.csv', curve)
        report['rollout_points'] = len(curve)
        report['rollout_note'] = ('S2.11 increment 02 records the most recent episode reward per rollout, '
                                  'not a rolling mean; this is not a robust learning curve.')
    (output / 'informe.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return output


def main(argv=None):
    p = argparse.ArgumentParser(description='Hydro-Lab S2.11 experimental instrumentation')
    p.add_argument('--checkpoint', required=True, help='Folder containing evaluation_validation.csv')
    p.add_argument('--split', choices=['validation', 'test'], default='validation')
    p.add_argument('--output', default=None)
    a = p.parse_args(argv)
    print(generate(a.checkpoint, output=a.output, split=a.split))


if __name__ == '__main__':
    main()
