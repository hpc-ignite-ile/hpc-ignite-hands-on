#!/bin/bash
# Shared PyTorch environment for LANTA GPU smoke tests.
# Usage: source slurm/module-loads/pytorch-shared.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true

if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base 2>/dev/null || true)"
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
    fi
fi

conda activate pytorch-2.2.2 2>/dev/null || true

echo "PyTorch shared environment loaded:"
module list 2>&1
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
