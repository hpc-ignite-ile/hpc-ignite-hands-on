#!/bin/bash
#SBATCH --job-name=hpds-weather
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=00:08:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs notes results figures
module purge
module use /project/tn999996-north/modules 2>/dev/null || true
module load hpc-mesa/2.3.4
. "${HPDS_ENV_PREFIX:?set HPDS_ENV_PREFIX before sbatch}/bin/activate"
{
    echo "job_id=$SLURM_JOB_ID"
    echo "host=$(hostname)"
    echo "workspace=$(pwd)"
    echo "python=$(command -v python)"
    python - <<'PY'
import dask, distributed, pandas, numpy
print("dask="+dask.__version__)
print("distributed="+distributed.__version__)
print("pandas="+pandas.__version__)
print("numpy="+numpy.__version__)
PY
} > "notes/environment_${SLURM_JOB_ID}.txt"
/usr/bin/time -v python src/hpds_weather_abs.py \
    --workers "$SLURM_CPUS_PER_TASK" \
    --out results/hpds_weather_abs_summary.csv \
    2> "notes/time_hpds_weather_abs_${SLURM_JOB_ID}.txt"
python src/plot_hpds_summary.py
python src/partition_mobility_graph.py
sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode \
    > "notes/sacct_${SLURM_JOB_ID}.txt"
