#!/bin/bash
#SBATCH --job-name=hpc-multigpu-job
#SBATCH --partition=gpu-devel
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=8
#SBATCH --gpus=4
#SBATCH --mem=32G
#SBATCH --time=00:20:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# ============================================================
# HPC Ignite - Multi-GPU (Single Node) Template
# ============================================================

echo "Job started at: $(date)"
echo "Running on node: $(hostname)"
echo "GPUs available: $SLURM_GPUS"

# Load modules
source slurm/module-loads/pytorch-shared.sh

# Check GPUs
python -c "import torch; print(f'GPUs: {torch.cuda.device_count()}')"

# For PyTorch DDP
export MASTER_ADDR=$(hostname)
export MASTER_PORT=29500

# Run distributed training
# torchrun --nproc_per_node=4 train_ddp.py

echo "Job finished at: $(date)"
