#!/bin/bash
#SBATCH --job-name=real-qe
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=02:00:00
set -euo pipefail
module purge
module load "${QE_MODULE:-QuantumESPRESSO/7.3.1-libxc-6.2.2-cpu}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
ulimit -s unlimited
export OMP_STACKSIZE=512M
root="$PWD"
out="$root/results/qe-$SLURM_JOB_ID"
mkdir -p "$out"
module list 2> "$out/modules.txt"
git -C sources/qe-benchmarks rev-parse HEAD > "$out/source-commit.txt"
/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926/envs/hpds/bin/python scripts/run_qe.py "$root" "$out"
