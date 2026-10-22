"""Run paired baseline comparisons. Never overwrite an existing report."""
from datetime import datetime, timezone
from pathlib import Path
from hydro_lab.benchmark import paired_benchmark, save_report

seeds=(20261019,20261020,20261021,20261022,20261023)
report=paired_benchmark(seeds)
name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
path=save_report(report,Path('results')/f'benchmark_s25_{name}.json')
for policy,metrics in report['summary'].items():
    print(f'{policy}: {metrics}')
print('Paired contrast:',report['comparison'])
print('Saved:',path)
