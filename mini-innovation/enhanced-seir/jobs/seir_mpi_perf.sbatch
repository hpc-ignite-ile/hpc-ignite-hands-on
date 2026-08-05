#!/bin/bash
#SBATCH --job-name=seir-mpi
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs notes results

module purge
module load cpeCray/25.03 2>/dev/null || true
module list 2> "notes/modules_${SLURM_JOB_ID}.txt"

CC -O3 -std=c++17 cpp_mpi/seir_mpi.cpp -o "results/seir_mpi_${SLURM_JOB_ID}"

/usr/bin/time -v srun -n "$SLURM_NTASKS" "results/seir_mpi_${SLURM_JOB_ID}" \
    --scenario-file data/scenarios.csv \
    --patches data/patches.csv \
    --mobility data/mobility.csv \
    --contact data/age_contact_4x4.csv \
    --out "results/seir_mpi_summary_${SLURM_JOB_ID}.csv"

sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode \
    > "notes/sacct_${SLURM_JOB_ID}.txt"
