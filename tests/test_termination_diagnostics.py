from hydro_lab.termination_diagnostics import summarize_terminations
from hydro_lab.benchmark import paired_benchmark
from hydro_lab.active_benchmark import active_paired_benchmark


def test_denominators_and_empty():
    rows = [dict(terminated=True, termination_reason='NO_SAFE_ACTION_OR_STOP', steps=12),
            dict(terminated=False, termination_reason=None, steps=96),
            dict(terminated=True, termination_reason='NO_SAFE_ACTION_OR_STOP', steps=18)]
    s = summarize_terminations(rows)
    assert s['termination_rate'] == 2 / 3
    assert s['termination_reason_rates']['NO_SAFE_ACTION_OR_STOP'] == 2 / 3
    assert s['termination_reason_shares']['NO_SAFE_ACTION_OR_STOP'] == 1
    assert s['mean_steps_to_termination'] == 15
    assert summarize_terminations([])['termination_rate'] is None


def test_paired_diagnostics_present():
    report = paired_benchmark((1000, 1001))
    assert all(v['termination_diagnostics']['n_episodes'] == 2 for v in report['summary'].values())


def test_active_diagnostics_present():
    report = active_paired_benchmark((1000, 1001), max_steps=8)
    assert all(v['termination_diagnostics']['n_episodes'] == 2 for v in report['summary'].values())
