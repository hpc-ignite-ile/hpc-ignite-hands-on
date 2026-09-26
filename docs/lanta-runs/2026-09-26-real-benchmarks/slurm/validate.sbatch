#!/bin/bash
#SBATCH --job-name=real-validation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
set -euo pipefail
export OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
envs/science/bin/python scripts/validate_native.py "$PWD"
