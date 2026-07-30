#!/bin/bash
# Submit a simple Python lab script to Slurm on LANTA.

set -euo pipefail

usage() {
    cat <<'USAGE'
Usage:
  bash scripts/lanta_submit_python_lab.sh path/to/lab.py [-- lab args...]

Environment variables:
  HPC_IGNITE_ACCOUNT    Slurm account/project. If unset, sbatch uses site default.
  HPC_IGNITE_PARTITION  Slurm partition, default: compute-devel
  HPC_IGNITE_TIME       Slurm time limit, default: 00:05:00
  HPC_IGNITE_MEM        Slurm memory, default: 1G

Example:
  export HPC_IGNITE_ACCOUNT=<project-account>
  bash scripts/lanta_submit_python_lab.sh foundation/chapter-00/hello_lanta.py
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "help" ]; then
    usage
    exit 0
fi

if [ $# -lt 1 ]; then
    usage >&2
    exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

LAB_SCRIPT="$1"
shift || true
if [ "${1:-}" = "--" ]; then
    shift || true
fi

cd "$REPO_ROOT"

if [ ! -f "$LAB_SCRIPT" ]; then
    echo "Lab script not found: $LAB_SCRIPT" >&2
    exit 1
fi

ACCOUNT="${HPC_IGNITE_ACCOUNT:-}"
PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"
TIME_LIMIT="${HPC_IGNITE_TIME:-00:05:00}"
MEMORY="${HPC_IGNITE_MEM:-1G}"

SBATCH_ACCOUNT_ARGS=()
if [ -n "$ACCOUNT" ]; then
    SBATCH_ACCOUNT_ARGS=(-A "$ACCOUNT")
fi

LAB_NAME="$(basename "$LAB_SCRIPT" .py)"
SAFE_NAME="$(printf '%s' "$LAB_NAME" | tr -c 'A-Za-z0-9_-' '-' | cut -c1-32)"
JOB_NAME="hpcig-${SAFE_NAME}"
GENERATED_DIR=".hpc-ignite/generated"
SBATCH_FILE="${GENERATED_DIR}/${JOB_NAME}.sbatch"
mkdir -p "$GENERATED_DIR" logs results/python-labs

LAB_ARGS=""
for arg in "$@"; do
    printf -v quoted '%q' "$arg"
    LAB_ARGS="${LAB_ARGS} ${quoted}"
done

cat > "$SBATCH_FILE" <<SBATCH
#!/bin/bash
#SBATCH --job-name=${JOB_NAME}
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=${MEMORY}
#SBATCH --time=${TIME_LIMIT}
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

cd "${REPO_ROOT}"

if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi

mkdir -p "results/python-labs/\${SLURM_JOB_ID}"

echo "Lab script : ${LAB_SCRIPT}"
echo "Job ID     : \${SLURM_JOB_ID}"
echo "Node       : \$(hostname)"
echo "Start      : \$(date -Is)"

python "${LAB_SCRIPT}"${LAB_ARGS} | tee "results/python-labs/\${SLURM_JOB_ID}/${SAFE_NAME}.txt"

echo "Finish     : \$(date -Is)"
SBATCH

echo "Submitting Python lab"
echo "  repo      : $REPO_ROOT"
echo "  account   : ${ACCOUNT:-site default}"
echo "  partition : $PARTITION"
echo "  script    : $LAB_SCRIPT"
echo "  sbatch    : $SBATCH_FILE"

sbatch \
    "${SBATCH_ACCOUNT_ARGS[@]}" \
    -p "$PARTITION" \
    "$SBATCH_FILE"

echo
echo "Monitor:"
echo "  squeue -u \$USER"
echo
echo "Results:"
echo "  ls -lh logs"
echo "  find results/python-labs -maxdepth 3 -type f | sort"
