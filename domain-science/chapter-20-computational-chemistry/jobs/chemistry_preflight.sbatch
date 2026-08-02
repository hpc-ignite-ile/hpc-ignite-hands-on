#!/bin/bash
#SBATCH --job-name=chem-preflight
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/base.sh
OUT="results/chemistry_${SLURM_JOB_ID}"
mkdir -p "$OUT"

{
    echo "Groups for license-aware chemistry tools:"
    id -Gn
    echo
    echo "Visible chemistry/materials modules:"
    module avail AutoDock-vina Gaussian Amber VASP QuantumESPRESSO 2>&1 || true
} | tee "$OUT/module_preflight.txt"

python domain-science/chapter-20-computational-chemistry/molecular_basics.py | tee "$OUT/molecular_basics.txt"
