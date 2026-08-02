#!/bin/bash
#SBATCH --job-name=mpi-collective-smoke
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
OUT="results/mpi_collective_${SLURM_JOB_ID}"
mkdir -p "$OUT"

cat > "$OUT/reduce.c" <<'C'
#include <mpi.h>
#include <stdio.h>

int main(int argc, char **argv) {
    int rank, size, sum;
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Reduce(&rank, &sum, 1, MPI_INT, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        printf("size=%d rank_sum=%d\n", size, sum);
    }
    MPI_Finalize();
    return 0;
}
C

cc "$OUT/reduce.c" -o "$OUT/reduce"
srun -n "$SLURM_NTASKS" "$OUT/reduce" | tee "$OUT/reduce.txt"
