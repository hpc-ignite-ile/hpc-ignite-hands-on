#!/bin/bash
#SBATCH --job-name=gdal-forest-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/geodata.sh
OUT="results/forest_${SLURM_JOB_ID}"
mkdir -p "$OUT"

SHAPE="$(find /project/common/WPS_Static -path '*THA*' -name '*.shp' -print -quit 2>/dev/null || true)"
if [ -n "$SHAPE" ]; then
    ogrinfo -so "$SHAPE" "$(basename "$SHAPE" .shp)" | tee "$OUT/thai_shape_info.txt" || true
else
    echo "No Thai shapefile found under /project/common/WPS_Static" | tee "$OUT/thai_shape_info.txt"
fi

python - <<'PY' | tee "$OUT/ndvi_smoke.csv"
import numpy as np
red = np.array([[0.20, 0.25], [0.30, 0.35]])
nir = np.array([[0.50, 0.55], [0.60, 0.70]])
ndvi = (nir - red) / (nir + red)
print("cell,ndvi")
for i, value in enumerate(ndvi.ravel()):
    print(f"{i},{value:.4f}")
PY
