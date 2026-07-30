#!/bin/bash
#SBATCH --job-name=hpc-array-job
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --array=1-10
#SBATCH --output=array_%A_%a.out
#SBATCH --error=array_%A_%a.err

# ============================================================
# HPC Ignite - Job Array Template
# ============================================================

echo "Job array task: $SLURM_ARRAY_TASK_ID of $SLURM_ARRAY_TASK_COUNT"
echo "Array job ID: $SLURM_ARRAY_JOB_ID"

# Load modules
source slurm/module-loads/base.sh

# Method 1: Use task ID directly
python process.py --task-id $SLURM_ARRAY_TASK_ID

# Method 2: Read parameters from file
# PARAM=$(sed -n "${SLURM_ARRAY_TASK_ID}p" params.txt)
# python simulate.py --param "$PARAM"

echo "Task $SLURM_ARRAY_TASK_ID finished at: $(date)"
