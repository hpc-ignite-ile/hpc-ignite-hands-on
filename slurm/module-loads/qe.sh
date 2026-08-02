#!/bin/bash
# Quantum ESPRESSO CPU environment for miniature materials workflows.
# Usage: source slurm/module-loads/qe.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load QuantumESPRESSO/7.3.1-libxc-6.2.2-cpu 2>/dev/null || true

echo "Quantum ESPRESSO environment loaded:"
module list 2>&1
command -v pw.x 2>/dev/null || true
