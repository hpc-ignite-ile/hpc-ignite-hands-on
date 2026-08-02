#!/bin/bash
#SBATCH --job-name=hello-lanta
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=512M
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# ============================================================
# Hello LANTA - ตัวอย่างแรกสำหรับทดสอบการเชื่อมต่อ
# Chapter 0: HPC 101
# ============================================================

echo "Job started at: $(date)"
echo "Running on node: $(hostname)"
echo "Job ID: ${SLURM_JOB_ID:-manual}"

# Load Python module
set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true

# Run the script
python hello_lanta.py

echo "Job finished at: $(date)"
