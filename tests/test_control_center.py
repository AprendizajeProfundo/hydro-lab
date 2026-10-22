import json
import numpy as np
import pytest
from hydro_lab.control_center import EpisodeSession, normalized_action, safe_filename, run_comparison, persist_episode


def test_normalization():
    assert np.allclose(normalized_action((.6,.8,1.)), (-1.,0.,1.))

@pytest.mark.parametrize('speeds', [(0.5,.8,.8), (.8,1.1,.8), (float('nan'),.8,.8), (.8,.8)])
def test_invalid_speed(speeds):
    with pytest.raises(ValueError): normalized_action(speeds)


def test_stepping_and_json():
    e=EpisodeSession(42,max_steps=3)
    try:
        e.advance(3)
        assert e.finished and e.truncated and not e.terminated
        assert len(e.records)==3
        r=json.loads(e.json_bytes())
        assert r['steps']==3 and r['schema']=='hydro-lab-s2.8-episode-v1'
        assert np.isclose(r['reward_total'],sum(x['reward'] for x in r['records']))
        with pytest.raises(RuntimeError):e.step()
    finally:e.close()


def test_reproducible():
    a=EpisodeSession(123,max_steps=8)
    b=EpisodeSession(123,max_steps=8)
    try:
        a.advance(8);b.advance(8)
        assert a.json_bytes()==b.json_bytes()
    finally:a.close();b.close()


def test_manual_policy():
    e=EpisodeSession(2,policy_name='manual',max_steps=2)
    try:
        rec=e.step((.7,.8,.9))
        assert np.allclose(rec['action_requested'],(.7,.8,.9),atol=1e-6)
    finally:e.close()


def test_no_policy_truth_input(monkeypatch):
    import hydro_lab.control_center as cc
    seen=[]
    def spy(obs):
        seen.append(obs.copy())
        assert obs.shape==(15,)
        return np.zeros(3,dtype=np.float32)
    monkeypatch.setitem(cc.POLICIES,'constant',spy)
    e=EpisodeSession(1,policy_name='constant',max_steps=1)
    try:e.step();assert len(seen)==1
    finally:e.close()


def test_report_no_overwrite(tmp_path):
    e=EpisodeSession(42,max_steps=1)
    try:
        e.advance(1)
        path=persist_episode(e,tmp_path)
        assert path.exists()
        assert json.loads(path.read_text())['seed']==42
    finally:e.close()


def test_filename():
    assert safe_filename('test',7).startswith('test_seed_7_')


def test_paired_comparison():
    result=run_comparison((10,11))
    assert result['comparison']['n_pairs']==2
    assert len(result['episodes'])==4


def test_invalid_policy():
    with pytest.raises(ValueError): EpisodeSession(1,policy_name='missing')
