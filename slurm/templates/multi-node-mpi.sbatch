#!/bin/bash
#SBATCH --job-name=hpc-mpi-job
#SBATCH --partition=compute
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# ============================================================
# HPC Ignite - Multi-Node MPI Template
# ============================================================

echo "Job started at: $(date)"
echo "Running on nodes: $SLURM_JOB_NODELIST"
echo "Total tasks: $SLURM_NTASKS"

# Load modules
source slurm/module-loads/mpi.sh

# Run MPI program
srun python your_mpi_script.py

echo "Job finished at: $(date)"
