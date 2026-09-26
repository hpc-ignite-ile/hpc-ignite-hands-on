#!/bin/bash
#SBATCH --job-name=cfd-performance
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:20:00
set -euo pipefail
module reset
module load Apptainer/1.1.6
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export APPTAINER_BIND=/project:/project,/scratch:/scratch
mkdir -p "results/$SLURM_JOB_ID"
sha256sum /project/pv915002-hpcign/wdiazcar/containers/openfoam-dev-2512.sif > "results/$SLURM_JOB_ID/container.sha256"
/usr/bin/time -v -o "results/$SLURM_JOB_ID/campaign-time.txt" ../envs/hpds/bin/python ../repo/scripts/run_cfd_campaign.py
