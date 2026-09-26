"""Compare scientific fields, not timing, before making CPU/GPU speedup claims."""
import argparse
import csv
import json
import math
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('cpu', type=Path)
parser.add_argument('gpu', type=Path)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--rtol', type=float, default=1e-4)
parser.add_argument('--atol', type=float, default=1e-4)
args = parser.parse_args()
def read(path):
    with path.open() as handle:
        return {r['scenario_id']: r for r in csv.DictReader(handle)}
cpu, gpu = read(args.cpu), read(args.gpu)
fields = ['total_population','peak_infectious','peak_hospitalized','attack_rate','final_deaths','final_recovered']
comparisons = []
for scenario in sorted(cpu.keys() & gpu.keys()):
    for field in fields:
        a, b = float(cpu[scenario][field]), float(gpu[scenario][field])
        comparisons.append({'scenario':scenario,'field':field,'cpu':a,'gpu':b,'absolute_error':abs(a-b),
                            'pass':math.isclose(a,b,rel_tol=args.rtol,abs_tol=args.atol)})
passed = cpu.keys() == gpu.keys() and bool(cpu) and all(r['pass'] for r in comparisons)
report = {'pass':passed,'rtol':args.rtol,'atol':args.atol,'cpu_source':str(args.cpu),'gpu_source':str(args.gpu),
          'cpu_scenarios':len(cpu),'gpu_scenarios':len(gpu),'comparisons':comparisons}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'pass':passed,'comparisons':len(comparisons),'failed':sum(not r['pass'] for r in comparisons)}))
raise SystemExit(0 if passed else 1)
