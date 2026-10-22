import csv
import pytest
from hydro_lab.s211_train04 import validate_parameters, write_table, EPISODE_FIELDS


def test_valid_instrumented_training_settings():
    validate_parameters(4096, 256, 64, 1024, (20000, 20001))


def test_reject_nonvalidation_seeds():
    with pytest.raises(ValueError):
        validate_parameters(4096, 256, 64, 1024, (10000,))


def test_reject_invalid_batch_size():
    with pytest.raises(ValueError):
        validate_parameters(4096, 256, 70, 1024, (20000,))


def test_reject_duplicate_validation_seeds():
    with pytest.raises(ValueError):
        validate_parameters(4096, 256, 64, 1024, (20000, 20000))


def test_csv_writes_headers_even_without_episodes(tmp_path):
    path = tmp_path / 'episodes.csv'
    write_table(path, EPISODE_FIELDS, [])
    with path.open() as f:
        assert next(csv.reader(f)) == list(EPISODE_FIELDS)
