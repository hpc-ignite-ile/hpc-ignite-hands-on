#!/bin/bash
#SBATCH --job-name=real-cfd
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=01:30:00
set -euo pipefail
module reset
module load Apptainer/1.1.6
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
export APPTAINER_BIND=/project:/project,/scratch:/scratch
out="$PWD/results/cfd-$SLURM_JOB_ID"
mkdir -p "$out"
/usr/bin/time -v -o "$out/time.txt" envs/science/bin/python scripts/cfd.py "$PWD" "$out"
