#!/bin/bash
#SBATCH --job-name=apptainer-smoke
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
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/apptainer.sh
OUT="results/apptainer_${SLURM_JOB_ID}"
mkdir -p "$OUT"

apptainer --version | tee "$OUT/version.txt"
python ai-applications/chapter-11-containers/container_demo.py | tee "$OUT/local_python_demo.txt"
