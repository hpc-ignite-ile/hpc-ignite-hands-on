#!/bin/bash
#SBATCH --job-name=hpcig-foundation-smoke
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:03:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${HPC_IGNITE_REPO:-${SLURM_SUBMIT_DIR}}"
cd "$REPO_ROOT"

mkdir -p logs "results/foundation/${SLURM_JOB_ID}"

if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi

echo "Repository : $REPO_ROOT"
echo "Job ID     : ${SLURM_JOB_ID}"
echo "Node       : $(hostname)"
echo "Start      : $(date -Is)"

python foundation/lanta-foundation/verify_lanta.py \
    --write-json "results/foundation/${SLURM_JOB_ID}/system.json"

python foundation/lanta-foundation/serial_sum.py \
    --n "${HPC_IGNITE_FOUNDATION_N:-200000}" \
    | tee "results/foundation/${SLURM_JOB_ID}/serial_sum.txt"

echo "Finish     : $(date -Is)"
