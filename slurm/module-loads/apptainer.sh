#!/bin/bash
# Apptainer environment for container smoke tests on LANTA.
# Usage: source slurm/module-loads/apptainer.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load Apptainer/1.1.6 2>/dev/null || true

echo "Apptainer environment loaded:"
module list 2>&1
command -v apptainer 2>/dev/null || true
