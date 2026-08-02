#!/bin/bash
#SBATCH --job-name=gromacs-md-smoke
#SBATCH --partition=gpu-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/gromacs.sh
OUT="results/gromacs_${SLURM_JOB_ID}"
mkdir -p "$OUT"

gmx --version | tee "$OUT/gmx_version.txt"
TPR="$(find /project/common/GROMACS -name 'benchPEP.tpr' -print -quit 2>/dev/null || true)"

if [ -z "$TPR" ]; then
    echo "No shared benchPEP.tpr found under /project/common/GROMACS; version smoke completed." | tee "$OUT/summary.txt"
    exit 0
fi

echo "input_tpr=$TPR" | tee "$OUT/summary.txt"
gmx mdrun -s "$TPR" -deffnm "$OUT/benchPEP" -nsteps 100 -ntomp "${SLURM_CPUS_PER_TASK:-1}" | tee "$OUT/mdrun_stdout.txt"
grep -E "Performance|Finished mdrun|Writing final coordinates" "$OUT/benchPEP.log" > "$OUT/performance_summary.txt" || true
