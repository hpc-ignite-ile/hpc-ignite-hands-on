#!/bin/bash
#SBATCH --job-name=real-evidence
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
set -euo pipefail
runner=/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926/envs/hpds/bin/python
"$runner" scripts/collect.py "$PWD"
"$runner" scripts/report.py evidence
