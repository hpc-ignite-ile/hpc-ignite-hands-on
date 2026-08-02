#!/bin/bash
#SBATCH --job-name=gromacs-gpu-smoke
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
cd "$SLURM_SUBMIT_DIR"
source slurm/module-loads/gromacs.sh
mkdir -p "results/gromacs_${SLURM_JOB_ID}"
gmx --version | tee "results/gromacs_${SLURM_JOB_ID}/gmx_version.txt"
