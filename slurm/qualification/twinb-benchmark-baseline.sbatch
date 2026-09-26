#!/bin/bash
#SBATCH --job-name=twinb-benchmark
#SBATCH --account=pv915002
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=7G
#SBATCH --time=00:20:00
set -euo pipefail
module load Mamba/23.11.0-0
old=/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926
source "$old/envs/twinb/bin/activate"
export ENERGYPLUS_HOME="$old/apps/energyplus-25.1.0"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
out="$PWD/results/$SLURM_JOB_ID"
mkdir -p "$out"
sha256sum scripts/*.py > "$out/source-sha256.txt"
python -m pip freeze > "$out/packages.txt"
for spec in fivezone:chicago school:denver; do
    model=${spec%:*}
    weather=${spec#*:}
    python scripts/prepare_twinb_benchmark.py "inputs/$model.idf" "$out/$model"
    python scripts/twinb_baseline_gate.py --idf "$out/$model/model.idf" --weather "inputs/$weather.epw" --output "$out/$model/baseline"
done
