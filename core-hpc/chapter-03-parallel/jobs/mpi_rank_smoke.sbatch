#!/bin/bash
#SBATCH --job-name=mpi-rank-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/cpe-mpi.sh
OUT="results/mpi_${SLURM_JOB_ID}"
mkdir -p "$OUT"

cat > "$OUT/hello_mpi.c" <<'C'
#include <mpi.h>
#include <stdio.h>

int main(int argc, char **argv) {
    int rank, size;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    printf("rank=%d size=%d\n", rank, size);
    MPI_Finalize();
    return 0;
}
C

cc "$OUT/hello_mpi.c" -o "$OUT/hello_mpi"
srun -n "$SLURM_NTASKS" "$OUT/hello_mpi" | tee "$OUT/ranks.txt"

python - <<'PY' > "$OUT/mpi4py_available.txt" || true
try:
    import mpi4py
    print("mpi4py available", mpi4py.__version__)
except Exception as exc:
    print("mpi4py unavailable", exc)
PY
