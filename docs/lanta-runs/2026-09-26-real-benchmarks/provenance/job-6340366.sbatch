#!/bin/bash
#SBATCH --job-name=real-gpu-python
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gpus-per-node=1
#SBATCH --mem=32G
#SBATCH --time=02:00:00
set -euo pipefail
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
out="$PWD/results/${EXPERIMENT:?}-$SLURM_JOB_ID"
mkdir -p "$out"
envs/physicsnemo/bin/pip freeze > "$out/packages.txt"
nvidia-smi > "$out/gpu-device.txt"
nvidia-smi --query-gpu=timestamp,uuid,utilization.gpu,memory.used,power.draw --format=csv -l 1 > "$out/gpu.csv" &
sampler=$!
trap 'kill "$sampler" 2>/dev/null || true' EXIT
/usr/bin/time -v -o "$out/time.txt" envs/physicsnemo/bin/python "scripts/${EXPERIMENT}.py" "$PWD" "$out"
