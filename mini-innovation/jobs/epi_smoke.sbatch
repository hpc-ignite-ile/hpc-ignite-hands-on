#!/bin/bash
#SBATCH --job-name=epi-abs-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/mini-innovation" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fi
cd "$REPO_ROOT"

EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-/project/tn999996-north/modules}"
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4

OUT="results/epi_smoke_${SLURM_JOB_ID}"
mkdir -p "$OUT"
python - <<'PY' | tee "$OUT/mesa_check.txt"
import mesa
from mesa.space import MultiGrid
from mesa.time import RandomActivation

print("mesa", mesa.__version__)
print("api", MultiGrid.__name__, RandomActivation.__name__)
PY
