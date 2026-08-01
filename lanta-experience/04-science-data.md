# 04 Science And Data Workflow

ใช้รูปแบบงานวิทยาศาสตร์ใน booklet: input, parameter, model script, result, evidence.

## Copy-Paste Diffusion Model

```bash
cd "$HOME/lanta-experience"
mkdir -p configs jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

cat > configs/diffusion-small.env <<'EOF'
N=300
STEPS=600
ALPHA=0.15
EOF

cat > src/diffusion_1d.py <<'PY'
import argparse
import csv
import math
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=200)
parser.add_argument("--steps", type=int, default=500)
parser.add_argument("--alpha", type=float, default=0.15)
parser.add_argument("--output", default="results/diffusion.csv")
args = parser.parse_args()

u = [0.0] * args.n
for i in range(args.n):
    x = i / (args.n - 1)
    u[i] = math.exp(-200.0 * (x - 0.5) ** 2)

t0 = time.time()
for _ in range(args.steps):
    v = u[:]
    for i in range(1, args.n - 1):
        v[i] = u[i] + args.alpha * (u[i - 1] - 2 * u[i] + u[i + 1])
    u = v

Path(args.output).parent.mkdir(parents=True, exist_ok=True)
with open(args.output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["i", "value"])
    for i, value in enumerate(u):
        writer.writerow([i, f"{value:.8f}"])
print(f"output={args.output} elapsed={time.time() - t0:.3f}")
PY

cat > jobs/diffusion.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=diffusion
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/diffusion_%j.out
#SBATCH --error=logs/diffusion_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
source configs/diffusion-small.env
python src/diffusion_1d.py --n "$N" --steps "$STEPS" --alpha "$ALPHA" --output "results/diffusion_${SLURM_JOB_ID}.csv"
RUN="diffusion_${SLURM_JOB_ID}"
mkdir -p "results/$RUN"
cp configs/diffusion-small.env "results/$RUN/"
cp jobs/diffusion.sbatch "results/$RUN/"
cat > "results/$RUN/README.txt" <<EOF
question: 1D diffusion baseline
workspace: $(pwd)
date: $(date -Is)
job: ${SLURM_JOB_ID}
result: results/diffusion_${SLURM_JOB_ID}.csv
validation: CSV has header i,value and N rows
EOF
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/diffusion.sbatch)
echo "$job_id	diffusion	$(date -Is)" >> notes/job-history.tsv
echo "Submitted diffusion job: $job_id"
echo "Read:"
echo "  head results/diffusion_${job_id}.csv"
echo "  cat results/diffusion_${job_id}/README.txt"
```

## Copy-Paste Small Data Summary

```bash
cd "$HOME/lanta-experience"
mkdir -p input results src

cat > src/make_sensor_data.py <<'PY'
import csv
import math
import random
from pathlib import Path

Path("input").mkdir(exist_ok=True)
random.seed(7)
with open("input/sensor.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["minute", "station", "pm25"])
    for minute in range(1440):
        for station in range(5):
            value = 18 + 10 * math.sin(minute / 1440 * 6.283) + random.random() * 5 + station
            writer.writerow([minute, f"S{station}", f"{value:.2f}"])
PY

cat > src/summarize_sensor.py <<'PY'
import csv
import statistics
from collections import defaultdict
from pathlib import Path

groups = defaultdict(list)
with open("input/sensor.csv", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        groups[row["station"]].append(float(row["pm25"]))

Path("results").mkdir(exist_ok=True)
with open("results/sensor_summary.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["station", "count", "mean", "max"])
    for station, values in sorted(groups.items()):
        writer.writerow([station, len(values), f"{statistics.mean(values):.2f}", f"{max(values):.2f}"])
print("results/sensor_summary.csv")
PY

python src/make_sensor_data.py
python src/summarize_sensor.py
head results/sensor_summary.csv
sha256sum input/sensor.csv results/sensor_summary.csv > notes/sensor-checksums.txt
```
