"""Gymnasium API smoke demo, not PPO training."""
import numpy as np
from hydro_lab.environment import HydroLabEnv

env=HydroLabEnv()
obs,info=env.reset(seed=20261019)
total=0.;steps=0
while True:
    obs,reward,terminated,truncated,info=env.step(np.zeros(3,dtype=np.float32))
    total+=reward;steps+=1
    if terminated or truncated:
        break
print(f'steps={steps} reward={total:.3f} terminated={terminated} truncated={truncated}')
print(f'last costs={info["costs"]}')
