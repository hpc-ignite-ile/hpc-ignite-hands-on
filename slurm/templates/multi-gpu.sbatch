#!/bin/bash
#SBATCH --job-name=hpc-multigpu-job
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=32
#SBATCH --gpus=4
#SBATCH --mem=512G
#SBATCH --time=08:00:00
#SBATCH --output=%x_%j.out
#SBATCH --error=%x_%j.err

# ============================================================
# HPC Ignite - Multi-GPU (Single Node) Template
# ============================================================

echo "Job started at: $(date)"
echo "Running on node: $(hostname)"
echo "GPUs available: $SLURM_GPUS"

# Load modules
source slurm/module-loads/pytorch.sh

# Check GPUs
python -c "import torch; print(f'GPUs: {torch.cuda.device_count()}')"

# For PyTorch DDP
export MASTER_ADDR=$(hostname)
export MASTER_PORT=29500

# Run distributed training
# torchrun --nproc_per_node=4 train_ddp.py

echo "Job finished at: $(date)"
