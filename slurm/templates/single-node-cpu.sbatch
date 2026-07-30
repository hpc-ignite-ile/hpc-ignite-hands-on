#!/bin/bash
#SBATCH --job-name=hpc-cpu-job
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# ============================================================
# HPC Ignite - Single Node CPU Template
# ============================================================

echo "Job started at: $(date)"
echo "Running on node: $(hostname)"
echo "Working directory: $(pwd)"

# Load modules
source slurm/module-loads/base.sh

# Your code here
# python your_script.py

echo "Job finished at: $(date)"
