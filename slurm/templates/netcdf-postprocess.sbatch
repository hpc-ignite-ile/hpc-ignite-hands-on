#!/bin/bash
#SBATCH --job-name=netcdf-postprocess
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/module-loads/netcdf-python.sh
mkdir -p "results/netcdf_${SLURM_JOB_ID}"

python - <<'PY'
from pathlib import Path
import json
import numpy as np
import pandas as pd

out = Path("results") / f"netcdf_{__import__('os').environ['SLURM_JOB_ID']}"
values = np.linspace(0, 1, 25).reshape(5, 5)
pd.DataFrame(values).to_csv(out / "mini_grid.csv", index=False)
(out / "summary.json").write_text(json.dumps({"mean": float(values.mean())}, indent=2), encoding="utf-8")
print(out)
PY
