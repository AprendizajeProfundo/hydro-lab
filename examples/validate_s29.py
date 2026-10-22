"""Usage: python examples/validate_s29.py --seeds 20 --output results/s29_run1"""
import argparse
from pathlib import Path
from hydro_lab.scientific_validation import run_validation,save_validation


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seeds',type=int,default=20,help='Number of predefined seeds 0..N-1')
    parser.add_argument('--steps',type=int,default=96)
    parser.add_argument('--output',type=Path,default=Path('results/s29_run1'))
    args=parser.parse_args()
    if not 1<=args.seeds<=1000:parser.error('--seeds must be between 1 and 1000')
    report=run_validation(tuple(range(args.seeds)),steps=args.steps)
    paths=save_validation(report,args.output)
    for path in paths:print(path)
    for regime,group in report['summary'].items():
        aware=group['health_aware']
        print(regime,'net effect:',round(aware['net_reward_difference_um']['mean'],4),
              'UM; action changes:',round(aware['requested_action_different_steps']['mean'],2))

if __name__=='__main__':main()
