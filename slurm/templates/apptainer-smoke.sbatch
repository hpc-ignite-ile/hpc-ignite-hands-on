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
cd "$SLURM_SUBMIT_DIR"
source slurm/module-loads/apptainer.sh
mkdir -p "results/apptainer_${SLURM_JOB_ID}"
apptainer --version | tee "results/apptainer_${SLURM_JOB_ID}/apptainer_version.txt"
