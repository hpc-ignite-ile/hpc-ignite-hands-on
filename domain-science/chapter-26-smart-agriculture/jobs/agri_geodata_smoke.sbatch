#!/bin/bash
#SBATCH --job-name=agri-geodata-smoke
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
OUT="results/agri_${SLURM_JOB_ID}"
mkdir -p "$OUT"
export OUT

python - <<'PY'
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd

out = Path(os.environ["OUT"])
rain_mm = np.array([12.0, 3.0, 0.0, 24.0, 7.0])
soil_score = np.array([0.7, 0.4, 0.2, 0.8, 0.5])
risk = np.where(rain_mm < 5, "dry", np.where(rain_mm > 20, "wet", "ok"))
df = pd.DataFrame({"plot": range(1, 6), "rain_mm": rain_mm, "soil_score": soil_score, "irrigation_risk": risk})
df.to_csv(out / "plot_risk.csv", index=False)
(out / "summary.json").write_text(json.dumps(df["irrigation_risk"].value_counts().to_dict(), indent=2), encoding="utf-8")
print(df)
PY
