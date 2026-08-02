#!/bin/bash
#SBATCH --job-name=pytorch-gpu-smoke
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
OUT="results/pytorch_${SLURM_JOB_ID}"
mkdir -p "$OUT"

nvidia-smi | tee "$OUT/nvidia-smi.txt"
python core-hpc/chapter-04-deep-learning/gpu_check.py | tee "$OUT/gpu_check.txt"
python - <<'PY' | tee "$OUT/tensor_benchmark.txt"
import time
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
x = torch.randn((2048, 2048), device=device)
torch.cuda.synchronize() if device == "cuda" else None
start = time.perf_counter()
y = x @ x
torch.cuda.synchronize() if device == "cuda" else None
print({"device": device, "shape": list(y.shape), "elapsed_s": round(time.perf_counter() - start, 4)})
PY
