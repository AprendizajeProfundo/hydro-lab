"""Independent worker for didactic PPO training; no Streamlit dependencies."""
from __future__ import annotations
import argparse
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path
from hydro_lab.s211_train04 import train

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--timesteps', type=int, required=True)
    p.add_argument('--n-steps', type=int, required=True)
    p.add_argument('--batch-size', type=int, required=True)
    p.add_argument('--eval-every', type=int, required=True)
    p.add_argument('--validation-count', type=int, required=True)
    args = p.parse_args()
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    status = folder / 'dashboard_status.json'
    def write(state, detail=''):
        status.write_text(json.dumps({'state': state, 'detail': detail, 'updated_at': datetime.now(timezone.utc).isoformat()}, indent=2), encoding='utf-8')
    write('running')
    print('Entrenamiento iniciado', flush=True)
    try:
        train(folder / 'checkpoint', timesteps=args.timesteps, seed=args.seed, n_steps=args.n_steps,
              batch_size=args.batch_size, eval_every=args.eval_every,
              validation_count=args.validation_count)
        write('completed')
        print('Entrenamiento completado', flush=True)
    except Exception as exc:
        write('failed', str(exc))
        traceback.print_exc()
        raise

if __name__ == '__main__':
    main()
