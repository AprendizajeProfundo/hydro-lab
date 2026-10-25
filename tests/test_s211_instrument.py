import csv
import json
import pytest
from hydro_lab.s211_instrument import read_evaluation, summarize, paired, generate


def _write(path, rows):
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def _row(seed, policy, value, terminated='False'):
    return dict(seed=seed, policy=policy, return_um=value, steps=50 if terminated=='True' else 96,
                terminated=terminated, truncated='False', energy_kwh=10,
                unserved_m3=2, interventions=1)


def test_paired_and_summary(tmp_path):
    p = tmp_path/'evaluation_validation.csv'
    _write(p, [_row(1,'PPO',-5), _row(2,'PPO',-8,'True'),
               _row(1,'constant',-9), _row(2,'constant',-7)])
    rows = read_evaluation(p)
    assert len(rows)==4
    assert next(x for x in summarize(rows) if x['policy']=='PPO')['early_terminations']==1
    result = paired(rows)[0]
    assert result['n_pairs']==2 and result['wins']==1 and result['losses']==1
    assert result['mean_delta_return_um']==1.5


def test_report_and_rollouts(tmp_path):
    _write(tmp_path/'evaluation_validation.csv', [_row(1,'PPO',-5), _row(1,'constant',-9)])
    (tmp_path/'rollouts.json').write_text(json.dumps([{'timesteps':256,'mean_episode_reward':-5}]))
    out=generate(tmp_path)
    assert (out/'informe.json').exists()
    assert (out/'curva_entrenamiento.csv').exists()


def test_duplicate_and_invalid(tmp_path):
    p=tmp_path/'evaluation_validation.csv'
    _write(p, [_row(1,'PPO',-5),_row(1,'PPO',-4)])
    with pytest.raises(ValueError, match='Duplicate'):
        read_evaluation(p)
    _write(p, [_row(1,'PPO','nan')])
    with pytest.raises(ValueError, match='Nonfinite'):
        read_evaluation(p)
