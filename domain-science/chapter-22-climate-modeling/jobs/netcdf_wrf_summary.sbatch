#!/bin/bash
#SBATCH --job-name=netcdf-wrf-summary
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

source slurm/module-loads/netcdf-python.sh
OUT="results/climate_${SLURM_JOB_ID}"
mkdir -p "$OUT"

SAMPLE="$(find /project/common/WRF -type f \( -name '*.nc' -o -name 'wrfout*' \) -print -quit 2>/dev/null || true)"
export SAMPLE OUT

python - <<'PY'
from pathlib import Path
import json
import os
import numpy as np
import xarray as xr

out = Path(os.environ["OUT"])
sample = os.environ.get("SAMPLE", "")

if sample:
    ds = xr.open_dataset(sample, decode_times=False)
    summary = {
        "source": sample,
        "dims": {k: int(v) for k, v in ds.sizes.items()},
        "variables": list(ds.data_vars)[:20],
    }
    ds.close()
else:
    y = np.arange(6)
    x = np.arange(8)
    rain = xr.DataArray(np.outer(y + 1, x + 1) / 10.0, dims=("y", "x"), coords={"y": y, "x": x})
    ds = xr.Dataset({"rain_mm": rain})
    generated = out / "generated_rainfall.nc"
    ds.to_netcdf(generated)
    summary = {"source": str(generated), "dims": {k: int(v) for k, v in ds.sizes.items()}, "variables": list(ds.data_vars)}

(out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PY
