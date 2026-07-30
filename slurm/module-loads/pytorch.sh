#!/bin/bash
# PyTorch module loads for GPU training on LANTA
# Usage: source slurm/module-loads/pytorch.sh
#
# LANTA user environments commonly use Mamba/Conda plus CUDA modules. This file
# prepares CUDA/NCCL and leaves the Python environment selection to the caller.

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true
module load cudatoolkit/24.11_12.6 2>/dev/null || module load cuda/12.6 2>/dev/null || true
module load nccl/2.18.1-1+cuda11.0 2>/dev/null || true

echo "PyTorch GPU modules loaded:"
module list 2>&1

# Verify Python/PyTorch if the active environment already provides torch.
python - <<'PY' 2>/dev/null || true
try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU count: {torch.cuda.device_count()}")
        print(f"GPU 0: {torch.cuda.get_device_name(0)}")
except Exception as exc:
    print(f"PyTorch check skipped: {exc}")
PY
