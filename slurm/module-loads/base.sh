#!/bin/bash
# Base module loads for HPC Ignite on LANTA
# Usage: source slurm/module-loads/base.sh
#
# Keep this file light: foundation labs should run with the system Python
# available on LANTA and should not require downloading packages.

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge

module load cray-python/3.10.10 2>/dev/null || true
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true

echo "Base modules loaded for HPC Ignite:"
module list 2>&1
