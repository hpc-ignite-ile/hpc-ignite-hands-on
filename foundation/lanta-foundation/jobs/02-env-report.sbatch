#!/bin/bash
#SBATCH --job-name=hpcig-foundation-env
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:03:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${HPC_IGNITE_REPO:-${SLURM_SUBMIT_DIR}}"
cd "$REPO_ROOT"

mkdir -p logs "results/foundation/${SLURM_JOB_ID}"

if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi

{
    echo "HPC Ignite LANTA environment report"
    echo "Generated : $(date -Is)"
    echo "Repo      : $REPO_ROOT"
    echo "Host      : $(hostname)"
    echo
    echo "== Slurm =="
    env | sort | grep '^SLURM_' || true
    echo
    echo "== Modules =="
    module list 2>&1 || true
    echo
    echo "== Python =="
    command -v python || true
    python --version || true
    echo
    echo "== Partitions =="
    sinfo -s || true
    echo
    echo "== Filesystems =="
    df -h "$HOME" "$PWD" 2>/dev/null || true
} | tee "results/foundation/${SLURM_JOB_ID}/environment.txt"
