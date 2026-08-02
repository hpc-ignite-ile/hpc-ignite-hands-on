#!/bin/bash
# Cray Programming Environment for compiled OpenMP/MPI jobs on LANTA.
# Usage: source slurm/module-loads/cpe-mpi.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load cpeCray/25.03 2>/dev/null || true
module load cray-python/3.10.10 2>/dev/null || true

echo "Cray CPE/MPI environment loaded:"
module list 2>&1
command -v cc 2>/dev/null || true
command -v srun 2>/dev/null || true
