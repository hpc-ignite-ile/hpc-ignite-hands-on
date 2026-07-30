#!/bin/bash
# MPI module loads for distributed computing on LANTA
# Usage: source slurm/module-loads/mpi.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load OpenMPI/4.1.2 2>/dev/null || module load cray-mpich/8.1.27 2>/dev/null || true
module load cray-python/3.10.10 2>/dev/null || true

echo "MPI modules loaded:"
module list 2>&1

# Verify MPI
command -v mpirun 2>/dev/null || command -v srun 2>/dev/null || true
mpirun --version 2>/dev/null | head -1 || true
