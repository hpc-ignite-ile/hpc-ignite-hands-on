"""Submit a reviewed auxiliary job and append the standard campaign receipt."""
import argparse
import datetime
import json
import os
import subprocess
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, required=True)
p.add_argument('--cwd', type=Path, required=True)
p.add_argument('--name', required=True)
p.add_argument('--dependency', default='')
p.add_argument('script', type=Path)
p.add_argument('options', nargs=argparse.REMAINDER)
a = p.parse_args()
(a.cwd/'logs').mkdir(parents=True, exist_ok=True)
command = ['sbatch', '--parsable', '-A', 'pv915002', '-p', 'compute-devel',
           '--output=logs/%x_%j.out', '--error=logs/%x_%j.err']
if a.dependency:
    command += ['--dependency=afterany:' + a.dependency]
command += a.options + [str(a.script.resolve())]
r = subprocess.run(command, cwd=a.cwd, capture_output=True, text=True)
row = dict(workflow=a.name, cwd=str(a.cwd.resolve()), command=command,
           context={k: os.environ[k] for k in ('BENCHMARK_DAYS','INCLUDE_THAI') if k in os.environ},
           submitted_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
           stderr=r.stderr, job_id=r.stdout.strip().split(';')[0] if r.returncode == 0 else None)
with (a.root/'submissions.jsonl').open('a') as handle:
    handle.write(json.dumps(row)+'\n')
print(json.dumps(row))
raise SystemExit(r.returncode)
