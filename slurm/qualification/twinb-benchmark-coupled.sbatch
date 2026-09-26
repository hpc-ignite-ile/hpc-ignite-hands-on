#!/bin/bash
#SBATCH --job-name=twinb-coupled
#SBATCH --account=pv915002
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1800M
#SBATCH --time=00:30:00
set -euo pipefail
sha256sum -c inputs/SHA256SUMS
module purge
module load Mamba/23.11.0-0
old=/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926
source "$old/envs/twinb/bin/activate"
export ENERGYPLUS_HOME="$old/apps/energyplus-25.1.0"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
out="$PWD/results/$SLURM_JOB_ID"
mkdir -p "$out"
sha256sum scripts/*.py > "$out/source-sha256.txt"
python -m pip freeze > "$out/packages.txt"
for spec in fivezone:chicago:50 school:denver:1875; do
    IFS=: read -r model weather agents <<< "$spec"
    python scripts/prepare_twinb_benchmark.py "inputs/$model.idf" "$out/$model-model" --days "${BENCHMARK_DAYS:-1}"
    python scripts/qualify_twinb_benchmark.py --model "$out/$model-model" --weather "inputs/$weather.epw" --output "$out/$model" --agents "$agents"
done
if [[ "${INCLUDE_THAI:-0}" == 1 ]]; then
    # Weather-only sensitivity: preserve Chicago design-day sizing assumptions.
    # This is not a Thai code-compliant or climate-resized building model.
    weather="$old/twinb/innovation/generated/heatlab_sweep/000_baseline_lampang/weather.epw"
    python scripts/prepare_twinb_benchmark.py inputs/fivezone.idf "$out/fivezone-lampang-model" --days "${BENCHMARK_DAYS:-1}"
    python scripts/qualify_twinb_benchmark.py --model "$out/fivezone-lampang-model" --weather "$weather" --output "$out/fivezone-lampang" --agents 50
fi
