#!/bin/bash
#SBATCH --job-name=twinb-reference
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:30:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
: "${TWINB_VENV:?กำหนดเส้นทางสภาพแวดล้อม Python ก่อนส่งงาน}"
: "${ENERGYPLUS_HOME:?กำหนดเส้นทาง EnergyPlus 25.1.0 ก่อนส่งงาน}"
source "$TWINB_VENV/bin/activate"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
sha256sum -c inputs/SHA256SUMS
out="$PWD/results/$SLURM_JOB_ID"
mkdir -p "$out"
python scripts/prepare_twinb_benchmark.py inputs/fivezone.idf "$out/model" --days 1
/usr/bin/time -v -o "$out/time.txt" python scripts/qualify_twinb_benchmark.py \
    --model "$out/model" --weather inputs/chicago.epw --output "$out/comparison" --agents 50
