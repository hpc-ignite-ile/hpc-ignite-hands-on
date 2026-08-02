#!/bin/bash
#SBATCH --job-name=hazard-grid-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/geodata.sh
OUT="results/hazard_${SLURM_JOB_ID}"
mkdir -p "$OUT"
export OUT

python - <<'PY'
from pathlib import Path
import os
import numpy as np
import pandas as pd

out = Path(os.environ["OUT"])
rain = np.array([[5, 12, 30], [8, 18, 45], [0, 10, 22]], dtype=float)
slope = np.array([[1, 4, 9], [2, 6, 11], [1, 3, 7]], dtype=float)
hazard = rain * 0.7 + slope * 1.5
rows = []
for y in range(hazard.shape[0]):
    for x in range(hazard.shape[1]):
        rows.append({"x": x, "y": y, "rain_mm": rain[y, x], "slope": slope[y, x], "hazard_score": round(float(hazard[y, x]), 2)})
df = pd.DataFrame(rows)
df.to_csv(out / "hazard_grid.csv", index=False)
print(df.sort_values("hazard_score", ascending=False).head(5))
PY
