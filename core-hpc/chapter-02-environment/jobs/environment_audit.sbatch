#!/bin/bash
#SBATCH --job-name=env-audit
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
OUT="results/env_${SLURM_JOB_ID}"
mkdir -p "$OUT"

python core-hpc/chapter-02-environment/check_environment.py --write-json "$OUT/system.json"
{
    echo "job_id=$SLURM_JOB_ID"
    echo "node=$(hostname)"
    echo "submit_dir=$SLURM_SUBMIT_DIR"
    echo "python=$(command -v python)"
    module list 2>&1 || true
    conda env list 2>/dev/null || true
    sinfo -s 2>/dev/null || true
    myquota 2>/dev/null || true
    sbalance 2>/dev/null || true
} | tee "$OUT/provenance.txt"
