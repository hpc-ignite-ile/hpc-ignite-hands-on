#!/bin/bash
#SBATCH --job-name=seir-roof
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:06:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs notes results

module purge
module load cpeCray/25.03 2>/dev/null || true
module list 2> "notes/modules_${SLURM_JOB_ID}.txt"

CC -O3 -std=c++17 performance/solver_roofline_mpi.cpp -o "results/solver_roofline_${SLURM_JOB_ID}"

out="results/solver_roofline_${SLURM_JOB_ID}.csv"
echo "label,ranks,n_global,iters,elapsed_sec,points_per_sec,gflop_s,gb_s,arith_intensity,residual" > "$out"
for ranks in 1 2 4; do
    /usr/bin/time -v srun -n "$ranks" "results/solver_roofline_${SLURM_JOB_ID}" \
        --n 1200000 \
        --iters 180 \
        --label "jacobi_${ranks}" \
        >> "$out" \
        2> "notes/time_solver_${SLURM_JOB_ID}_${ranks}.txt"
done

sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode \
    > "notes/sacct_${SLURM_JOB_ID}.txt"
