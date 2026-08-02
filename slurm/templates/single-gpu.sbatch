#!/bin/bash
#SBATCH --job-name=hpc-gpu-job
#SBATCH --partition=gpu-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# ============================================================
# HPC Ignite - Single GPU Template
# ============================================================

echo "Job started at: $(date)"
echo "Running on node: $(hostname)"

# Load modules
source slurm/module-loads/pytorch-shared.sh

# Check GPU
python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"

# Your code here
# python train_model.py

echo "Job finished at: $(date)"
