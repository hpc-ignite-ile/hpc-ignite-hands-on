# 02 CPU And Job Array

ต่อจากงานแรกด้วยงาน CPU ที่ใช้หลาย worker และ job array สำหรับหลายชุดพารามิเตอร์.

## Copy-Paste CPU Baseline

```bash
cd "$HOME/lanta-experience"
mkdir -p configs jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

cat > src/parallel_pi.py <<'PY'
import argparse
import math
import multiprocessing as mp
import os
import random
import time
from pathlib import Path

def count_inside(seed_and_n):
    seed, n = seed_and_n
    rng = random.Random(seed)
    inside = 0
    for _ in range(n):
        x, y = rng.random(), rng.random()
        inside += (x * x + y * y) <= 1.0
    return inside

parser = argparse.ArgumentParser()
parser.add_argument("--samples", type=int, default=1_000_000)
parser.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
args = parser.parse_args()

workers = max(1, args.workers)
chunk = math.ceil(args.samples / workers)
t0 = time.time()
with mp.Pool(processes=workers) as pool:
    inside = sum(pool.map(count_inside, [(1000 + i, min(chunk, args.samples - i * chunk)) for i in range(workers)]))
pi = 4.0 * inside / args.samples

Path("results").mkdir(exist_ok=True)
job_id = os.environ.get("SLURM_JOB_ID", "manual")
Path(f"results/pi_{job_id}.txt").write_text(
    f"samples={args.samples}\nworkers={workers}\npi={pi}\nelapsed={time.time() - t0:.3f}\n",
    encoding="utf-8",
)
print(f"pi={pi} workers={workers}")
PY

cat > jobs/parallel_pi.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=parallel_pi
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/pi_%j.out
#SBATCH --error=logs/pi_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=1
python src/parallel_pi.py --samples 500000 --workers "${SLURM_CPUS_PER_TASK:-1}"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/parallel_pi.sbatch)
echo "$job_id	parallel_pi	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -50 logs/pi_${job_id}.out && cat results/pi_${job_id}.txt"
```

## Copy-Paste Job Array

```bash
cd "$HOME/lanta-experience"
mkdir -p configs jobs logs notes results src

cat > configs/pi-params.csv <<'EOF'
100000,1
200000,2
400000,4
800000,4
EOF

cat > src/array_pi.py <<'PY'
import argparse
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("--line", required=True)
args = parser.parse_args()
samples, workers = args.line.split(",")
subprocess.check_call([
    "python", "src/parallel_pi.py",
    "--samples", samples,
    "--workers", workers,
])
PY

cat > jobs/pi_array.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=pi_array
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --array=1-4
#SBATCH --output=logs/pi_array_%A_%a.out
#SBATCH --error=logs/pi_array_%A_%a.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
LINE=$(sed -n "${SLURM_ARRAY_TASK_ID}p" configs/pi-params.csv)
python src/array_pi.py --line "$LINE"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "${LANTA_CPU_PARTITION:-compute-devel}" --parsable jobs/pi_array.sbatch)
echo "$job_id	pi_array	$(date -Is)" >> notes/job-history.tsv
echo "Submitted array job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: ls logs/pi_array_${job_id}_*.out results/pi_*.txt"
```
