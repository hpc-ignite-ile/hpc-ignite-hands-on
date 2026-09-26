#!/bin/bash
#SBATCH --job-name=real-science
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:40:00
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export MPLBACKEND=Agg
out="$PWD/results/${EXPERIMENT:?}-$SLURM_JOB_ID"
mkdir -p "$out"
envs/science/bin/pip freeze > "$out/packages.txt"
/usr/bin/time -v -o "$out/time.txt" envs/science/bin/python scripts/science.py "$EXPERIMENT" "$PWD" "$out"
