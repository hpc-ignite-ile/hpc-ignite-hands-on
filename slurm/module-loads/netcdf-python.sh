#!/bin/bash
# Shared Python data environment for NetCDF/xarray/Matplotlib workflows.
# Usage: source slurm/module-loads/netcdf-python.sh

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

conda activate netcdf-py39 2>/dev/null || true
export MPLBACKEND="${MPLBACKEND:-Agg}"

echo "NetCDF Python environment loaded:"
module list 2>&1
python - <<'PY' 2>/dev/null || true
for name in ["numpy", "pandas", "xarray", "netCDF4", "matplotlib"]:
    try:
        module = __import__(name)
        print(f"{name}: {getattr(module, '__version__', 'available')}")
    except Exception as exc:
        print(f"{name}: unavailable ({exc})")
PY
