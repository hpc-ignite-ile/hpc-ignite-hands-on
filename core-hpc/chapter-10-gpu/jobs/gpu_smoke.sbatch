#!/bin/bash
#SBATCH --job-name=gpu-info-smoke
#SBATCH --partition=gpu-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
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

source slurm/module-loads/pytorch-shared.sh
OUT="results/gpu_${SLURM_JOB_ID}"
mkdir -p "$OUT"

nvidia-smi | tee "$OUT/nvidia-smi.txt"
python core-hpc/chapter-10-gpu/gpu_info.py | tee "$OUT/gpu_info.txt"
