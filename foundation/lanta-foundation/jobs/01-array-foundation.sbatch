#!/bin/bash
#SBATCH --job-name=hpcig-foundation-array
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:05:00
#SBATCH --array=1-4
#SBATCH --output=logs/%x_%A_%a.out
#SBATCH --error=logs/%x_%A_%a.err

set -euo pipefail

REPO_ROOT="${HPC_IGNITE_REPO:-${SLURM_SUBMIT_DIR}}"
cd "$REPO_ROOT"

mkdir -p logs "results/foundation/${SLURM_ARRAY_JOB_ID}"

if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi

echo "Array job  : ${SLURM_ARRAY_JOB_ID}"
echo "Task       : ${SLURM_ARRAY_TASK_ID}/${SLURM_ARRAY_TASK_COUNT}"
echo "Node       : $(hostname)"

python foundation/lanta-foundation/array_task.py \
    --task-id "${SLURM_ARRAY_TASK_ID}" \
    --task-count "${SLURM_ARRAY_TASK_COUNT}" \
    --output "results/foundation/${SLURM_ARRAY_JOB_ID}/task-${SLURM_ARRAY_TASK_ID}.csv"
