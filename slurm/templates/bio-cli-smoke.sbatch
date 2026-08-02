#!/bin/bash
#SBATCH --job-name=bio-cli-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/module-loads/bio.sh
mkdir -p "results/bio_${SLURM_JOB_ID}"
blastn -version | tee "results/bio_${SLURM_JOB_ID}/blast_version.txt"
