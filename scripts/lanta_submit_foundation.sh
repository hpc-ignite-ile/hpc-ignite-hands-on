#!/bin/bash
# Submit the first runnable HPC Ignite foundation jobs on LANTA.

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash scripts/lanta_submit_foundation.sh [smoke|array|env]

Environment variables:
  HPC_IGNITE_ACCOUNT    Slurm account/project, required unless your site has a default account
  HPC_IGNITE_PARTITION  Slurm partition, default: compute-devel

Examples:
  export HPC_IGNITE_ACCOUNT=<project-account>
  export HPC_IGNITE_PARTITION=compute-devel
  bash scripts/lanta_submit_foundation.sh smoke
  bash scripts/lanta_submit_foundation.sh array
USAGE
}

JOB_KIND="${1:-smoke}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

ACCOUNT="${HPC_IGNITE_ACCOUNT:-}"
PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

SBATCH_ACCOUNT_ARGS=()
if [ -n "$ACCOUNT" ]; then
    SBATCH_ACCOUNT_ARGS=(-A "$ACCOUNT")
fi

case "$JOB_KIND" in
    smoke)
        JOB_FILE="foundation/lanta-foundation/jobs/00-smoke-cpu.sbatch"
        ;;
    array)
        JOB_FILE="foundation/lanta-foundation/jobs/01-array-foundation.sbatch"
        ;;
    env)
        JOB_FILE="foundation/lanta-foundation/jobs/02-env-report.sbatch"
        ;;
    -h|--help|help)
        usage
        exit 0
        ;;
    *)
        echo "Unknown job kind: $JOB_KIND" >&2
        usage >&2
        exit 2
        ;;
esac

cd "$REPO_ROOT"
mkdir -p logs results/foundation

echo "Submitting HPC Ignite foundation job"
echo "  repo      : $REPO_ROOT"
echo "  account   : ${ACCOUNT:-site default}"
echo "  partition : $PARTITION"
echo "  job       : $JOB_FILE"

sbatch \
    "${SBATCH_ACCOUNT_ARGS[@]}" \
    -p "$PARTITION" \
    --export=ALL,HPC_IGNITE_REPO="$REPO_ROOT" \
    "$JOB_FILE"

echo
echo "Monitor:"
echo "  squeue -u \$USER"
echo
echo "Results:"
echo "  ls -lh logs"
echo "  find results/foundation -maxdepth 3 -type f | sort"
