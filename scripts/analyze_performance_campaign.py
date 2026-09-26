"""Summarize recorded CFD repeats and GPU samples; no fabricated measurements."""
import argparse
import csv
import json
from pathlib import Path
import re
import statistics
import shutil

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('unpacked', type=Path)
p.add_argument('destination', type=Path)
a = p.parse_args()
gpu = []
for path in sorted(a.unpacked.rglob('gpu.csv')):
    rows = list(csv.DictReader(path.open(), skipinitialspace=True))
    def values(key):
        return [float(re.search(r'[\d.]+', r[key])[0]) for r in rows if re.fullmatch(r'[\d.]+(?: %| MiB| W)?', r.get(key,''))]
    util, memory, power = (values(k) for k in ('utilization.gpu [%]', 'memory.used [MiB]', 'power.draw [W]'))
    gpu.append(dict(source=str(path.relative_to(a.unpacked)), samples=len(rows),
                    mean_sampled_utilization_percent=statistics.mean(util) if util else None,
                    max_sampled_memory_MiB=max(memory) if memory else None,
                    mean_sampled_board_power_W=statistics.mean(power) if power else None))
(a.destination/'gpu-samples-summary.json').write_text(json.dumps(gpu,indent=2)+'\n')
rows = list(csv.DictReader((a.unpacked/'cfd/results/6340268/performance.csv').open()))
summary = []
for cells in (400,1600,6400):
    baseline = statistics.median(float(r['elapsed_s']) for r in rows if int(r['cells'])==cells and r['ranks']=='1')
    for ranks in (1,2):
        times = [float(r['elapsed_s']) for r in rows if int(r['cells'])==cells and int(r['ranks'])==ranks]
        median = statistics.median(times)
        summary.append(dict(cells=cells,ranks=ranks,repeats=len(times),median_elapsed_s=median,
                            stdev_s=statistics.stdev(times),observed_runtime_ratio=baseline/median,
                            note='Includes container startup, excludes meshing; numerical field equivalence not yet checked.'))
(a.destination/'cfd-performance-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9,5),layout='constrained')
for ranks in (1,2):
    data = [r for r in summary if r['ranks']==ranks]
    ax.errorbar([r['cells'] for r in data],[r['median_elapsed_s'] for r in data],
                yerr=[r['stdev_s'] for r in data],marker='o',capsize=4,label=f'{ranks} MPI rank(s)')
ax.set(xlabel='Mesh cells (20², 40², 80²)',ylabel='Solver + container elapsed seconds',
       title='Actual LANTA OpenFOAM v2512 timings · job 6340268\n3 repeats; error bars ±1 sample standard deviation')
ax.legend()
ax.grid(alpha=.25)
fig.savefig(a.destination/'cfd-measured-performance.png',dpi=140)
source = a.unpacked/'benchmarks/results'
shutil.copy2(source/'performance-summary.json', a.destination/'twinb-performance-summary.json')
for image in source.glob('*actual-traces.png'):
    shutil.copy2(image, a.destination/image.name)
print(json.dumps({'GPU_jobs_with_samples':len(gpu),'CFD_trials':len(rows),'CFD_summary':summary},indent=2))
