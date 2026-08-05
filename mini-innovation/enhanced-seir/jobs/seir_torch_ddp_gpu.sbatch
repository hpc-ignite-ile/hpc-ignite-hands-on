#!/bin/bash
#SBATCH --job-name=seir-ddp
#SBATCH --partition=gpu-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gpus-per-node=1
#SBATCH --mem=12G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs notes results

module purge
module load Mamba/23.11.0-0 2>/dev/null || module load Mamba 2>/dev/null || true
if command -v conda >/dev/null 2>&1; then
    CONDA_BASE="$(conda info --base 2>/dev/null || true)"
    if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
        source "$CONDA_BASE/etc/profile.d/conda.sh"
    fi
fi
conda activate pytorch-2.2.2 2>/dev/null || true
export PATH="/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/envs/pytorch-2.2.2/bin:${PATH}"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"

module list 2> "notes/modules_${SLURM_JOB_ID}.txt"
nvidia-smi > "notes/nvidia-smi_${SLURM_JOB_ID}.txt"

nproc_per_node="${SLURM_GPUS_ON_NODE:-${SLURM_GPUS_PER_NODE:-1}}"
/usr/bin/time -v torchrun --standalone --nproc_per_node="$nproc_per_node" torch_ddp/seir_torch_ddp.py \
    --ddp \
    --device cuda \
    --scenario-file data/scenarios.csv \
    --patches data/patches.csv \
    --mobility data/mobility.csv \
    --contact data/age_contact_4x4.csv \
    --out "results/seir_torch_summary_${SLURM_JOB_ID}.csv"

sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode \
    > "notes/sacct_${SLURM_JOB_ID}.txt"
