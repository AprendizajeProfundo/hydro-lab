"""Run a synthetic 24h episode with a fixed seed and save its trace."""
from hydro_lab.dynamics import run_episode

if __name__=='__main__':
    result=run_episode(seed=20261019)
    print(result.summary())
    result.save_json('results/episode_s23_seed_20261019.json')
    print('Trace saved in results/episode_s23_seed_20261019.json')
