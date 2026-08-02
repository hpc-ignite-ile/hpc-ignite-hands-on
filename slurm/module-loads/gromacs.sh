#!/bin/bash
# GROMACS GPU environment for miniature MD workflows on LANTA.
# Usage: source slurm/module-loads/gromacs.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load GROMACS/2024.6-cpeGNU-25.03-CUDA-12.6 2>/dev/null || true

echo "GROMACS environment loaded:"
module list 2>&1
command -v gmx 2>/dev/null || true
