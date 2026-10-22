"""Run: python examples/compare_s210.py --seeds 10 --output results/s210_demo1"""
import argparse
from pathlib import Path
from hydro_lab.teaching_comparison import run_teaching_comparison, save_teaching_comparison

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--seeds',type=int,default=10)
    parser.add_argument('--steps',type=int,default=96)
    parser.add_argument('--output',type=Path,default=Path('results/s210_demo1'))
    args=parser.parse_args()
    if not 1<=args.seeds<=1000:parser.error('seeds must be 1..1000')
    report=run_teaching_comparison(range(args.seeds),steps=args.steps)
    directory=save_teaching_comparison(report,args.output)
    print('Resultados:',directory)
    for regime, group in report['summary'].items():
        print(regime, 'efecto pareado:',group['paired_robust_value_minus_robust_off']['mean_um'],'UM')

if __name__=='__main__':main()
