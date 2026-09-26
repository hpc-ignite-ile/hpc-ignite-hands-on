#!/bin/bash
#SBATCH --job-name=twinb-gate
#SBATCH --account=pv915002
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=7G
#SBATCH --time=00:10:00
set -euo pipefail
old=/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926
export ENERGYPLUS_HOME="$old/apps/energyplus-25.1.0"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
module load Mamba/23.11.0-0
source "$old/envs/twinb/bin/activate"
out="$PWD/results/$SLURM_JOB_ID"
mkdir -p "$out"
idf="$old/twinb/innovation/generated/day-smoke/day.idf"
weather="$old/twinb/innovation/generated/heatlab_sweep/000_baseline_lampang/weather.epw"
python scripts/twinb_audit_geometry.py "$idf" > "$out/geometry.json"
"$ENERGYPLUS_HOME/energyplus" --version > "$out/runtime.txt"
python -m pip freeze > "$out/packages.txt"
sha256sum scripts/*.py > "$out/source-sha256.txt"
python scripts/twinb_baseline_gate.py --idf "$idf" --weather "$weather" --output "$out/baseline"
