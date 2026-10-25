import math
import pytest
from hydro_lab.paired_statistics import paired_inference, holm_adjust, fixed_feedback_differences, interpretation


def test_mean_interval_and_p():
    r = paired_inference([1, 2, 3, 4, 5])
    assert r['mean'] == 3
    assert r['df'] == 4
    assert r['ci_low'] < 3 < r['ci_high']
    assert r['p'] < .05


def test_zero_variance_is_not_significant_by_decree():
    r = paired_inference([2, 2, 2])
    assert r['p'] is None and r['status'] == 'zero_variance'


def test_one_pair():
    assert paired_inference([2])['status'] == 'insufficient'


def test_holm():
    assert holm_adjust([.01, .03, .02]) == pytest.approx([.03, .04, .04])
    assert holm_adjust([None, .04, .02]) == [None, .04, .04]


def test_pairing_by_seed_not_row_order():
    report = {'seeds': [10, 11], 'episodes': [
        {'seed': 11, 'policy': 'constant', 'reward': 4},
        {'seed': 10, 'policy': 'demand_feedback', 'reward': 8},
        {'seed': 11, 'policy': 'demand_feedback', 'reward': 6},
        {'seed': 10, 'policy': 'constant', 'reward': 5},
    ]}
    assert fixed_feedback_differences(report) == [3, 2]


def test_non_significance_not_equivalence():
    r = paired_inference([1, -1, 2, -2, 0])
    assert 'NO demuestra igualdad' in interpretation(r)
