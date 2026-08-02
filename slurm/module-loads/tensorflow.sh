#!/bin/bash
# TensorFlow module loads for LANTA shared conda environment.
# Usage: source slurm/module-loads/tensorflow.sh

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

conda activate tensorflow-2.12.1 2>/dev/null || true

echo "TensorFlow modules loaded:"
module list 2>&1
python - <<'PY' 2>/dev/null || true
try:
    import tensorflow as tf
    print(f"TensorFlow: {tf.__version__}")
    print(f"GPUs: {len(tf.config.list_physical_devices('GPU'))}")
except Exception as exc:
    print(f"TensorFlow check skipped: {exc}")
PY
