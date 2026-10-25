import pytest
from hydro_lab.s211_study05 import paired_deltas, summarize, confidence_across_training_seeds, episode_row, diagnose
from hydro_lab.agents import EpisodeResult


def test_episode_row_preserves_costs():
    r = EpisodeResult(seed=20000, return_um=-25, steps=12, terminated=True)
    r.costs_um['deficit_um'] = 15
    out = episode_row(r, 42, 'PPO')
    assert out['early_termination'] is True
    assert out['deficit_um'] == 15


def test_pairing_uses_seed_and_scenario():
    rows = [dict(training_seed=42, scenario_seed=20000, policy='PPO', return_um=-4,
                 unserved_m3=1, energy_kwh=3, early_termination=False),
            dict(training_seed=42, scenario_seed=20000, policy='constant', return_um=-8,
                 unserved_m3=2, energy_kwh=4, early_termination=True)]
    pair = paired_deltas(rows, 'constant')
    assert pair[0]['delta_return_um'] == 4
    assert pair[0]['delta_early_termination'] == -1


def test_missing_pair_fails():
    with pytest.raises(ValueError, match='Missing matched baseline'):
        paired_deltas([dict(training_seed=1, scenario_seed=2, policy='PPO')], 'constant')


def test_summary_separates_training_seeds():
    rows = [dict(training_seed=s, policy='PPO', return_um=-s, unserved_m3=0,
                 energy_kwh=1, early_termination=False) for s in (41, 42)]
    assert len(summarize(rows)) == 2


def test_single_seed_no_confidence_interval():
    rows = [dict(training_seed=42, baseline='constant', delta_return_um=3)]
    result = confidence_across_training_seeds(rows)
    assert result[0]['normal_approx_low_um'] is None


def test_diagnose_rejects_invalid_split(tmp_path):
    with pytest.raises(ValueError, match='split'):
        diagnose(['fake'], output=tmp_path / 'out', split='training')
