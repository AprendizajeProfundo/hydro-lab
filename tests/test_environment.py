import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env
from hydro_lab.environment import HydroLabEnv
from hydro_lab.observations import HealthBelief, OBSERVATION_NAMES
from hydro_lab.scenarios import generate_scenario

def test_gymnasium_contract():
    env=HydroLabEnv(max_steps=4)
    check_env(env,skip_render_check=True)
    env.close()

def test_observation_contract():
    env=HydroLabEnv(max_steps=4)
    obs,info=env.reset(seed=14)
    assert obs.shape==(15,) and env.observation_space.contains(obs)
    assert len(OBSERVATION_NAMES)==15
    assert not any(x in OBSERVATION_NAMES for x in ('health','phase','viscosity','future_demand'))
    assert 'evaluation_truth' not in info
    for _ in range(4):
        obs,r,terminated,truncated,info=env.step(np.zeros(3,dtype=np.float32))
        assert env.observation_space.contains(obs)
        assert np.isfinite(r)
        assert r == pytest.approx(-sum(info['costs'].values()))
        assert abs(info['mass_error_m3'])<1e-8
        if terminated or truncated: break
    assert terminated or truncated

def test_reproducibility():
    def run():
        env=HydroLabEnv(max_steps=6)
        obs,info=env.reset(seed=99)
        trace=[obs.tolist()]
        for _ in range(6):
            obs,r,term,trunc,info=env.step(np.zeros(3,dtype=np.float32))
            trace.append((obs.tolist(),r,info['action_executed'],info['costs']))
            if term or trunc: break
        return trace
    assert run()==run()

def test_sensors_do_not_change_physical_process():
    scenario=generate_scenario(17,steps=5)
    a=HydroLabEnv(max_steps=5);b=HydroLabEnv(max_steps=5)
    a.reset(seed=17,options={'scenario':scenario})
    b.reset(seed=42,options={'scenario':scenario})
    for _ in range(5):
        oa,ra,ta,ua,ia=a.step(np.zeros(3,dtype=np.float32))
        ob,rb,tb,ub,ib=b.step(np.zeros(3,dtype=np.float32))
        assert ra==rb and ia['evaluation_truth']==ib['evaluation_truth']
        if ta or ua: break

def test_action_validation():
    env=HydroLabEnv(max_steps=2);env.reset(seed=4)
    for bad in ([1.1,0,0],[float('nan'),0,0],[0,0]):
        with pytest.raises(ValueError): env.step(bad)

def test_health_belief_uses_only_inspection():
    b=HealthBelief.initial()
    before=b.estimate.copy();b.predict()
    np.testing.assert_array_equal(before,b.estimate)
    b.inspect(1,.7)
    assert .65 <= b.estimate[1]<.95
    assert b.estimate[0]==.95
