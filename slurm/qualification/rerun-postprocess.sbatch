#!/bin/bash
#SBATCH --job-name=rerun-postprocess
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
campaign="$(dirname "$SLURM_SUBMIT_DIR")"
module purge
module use "${EPI_MODULE_ROOT:?}"
module load hpc-mesa/3.5.1
export MPLBACKEND=Agg
export OPENBLAS_NUM_THREADS=1
latest_array() {
    python - "$campaign/submissions.jsonl" "$1" <<'PY'
import json, sys
rows = [json.loads(line) for line in open(sys.argv[1])]
print([r['job_id'] for r in rows if r['job_id'] and r['workflow'].endswith(sys.argv[2])][-1])
PY
}
epi_array=$(latest_array 'jobs/epi_array.sbatch')
twinb_array=$(latest_array 'jobs/twinb_array.sbatch')
export EPI_RESULTS="$campaign/selected/epi-$epi_array"
export TWINB_RESULTS="$campaign/selected/twinb-$twinb_array"
mkdir -p "$EPI_RESULTS" "$TWINB_RESULTS"
cp "$campaign/tutorials/mini-innovation/03-epidemic-abs-examples/results/epi_summary_${epi_array}_"*.csv "$EPI_RESULTS/"
cp "$campaign/tutorials/mini-innovation/04-building-cosimulation-twinb/results/twinb_summary_${twinb_array}_"*.csv "$TWINB_RESULTS/"
cd "$campaign/tutorials/mini-innovation/03-epidemic-abs-examples"
python src/merge_results.py --pattern "$EPI_RESULTS/epi_summary_*.csv" --output-prefix "$EPI_RESULTS/epi_selected"
cd "$campaign/tutorials/mini-innovation/04-building-cosimulation-twinb"
python src/merge_twinb_results.py --pattern "$TWINB_RESULTS/twinb_summary_*.csv" --output "$TWINB_RESULTS/twinb_policy_compare_selected.csv"
cd "$campaign/tutorials/ai-applications/chapter-29-security/README"
chmod 600 input/private.env
python - <<'PY'
import csv, stat
from pathlib import Path
with open('results/security_audit.csv', 'w') as handle:
    writer = csv.writer(handle)
    writer.writerow(['path','mode','has_fake_secret_pattern'])
    for path in sorted(Path('input').glob('*')):
        text = path.read_text()
        mode = stat.S_IMODE(path.stat().st_mode)
        writer.writerow([str(path),oct(mode),'TOKEN' in text or 'SECRET' in text])
        if path.name == 'private.env':
            assert mode == 0o600
print(Path('results/security_audit.csv').read_text())
PY
cd "$campaign/tutorials/mini-innovation/05-output-display-jupyter-gnuplot"
python src/prepare_display_tables.py
python src/plot_display_matplotlib.py
python src/make_display_notebook.py
/usr/bin/time -v jupyter nbconvert --execute --to notebook --ExecutePreprocessor.timeout=120 --output executed.ipynb notebooks/*.ipynb
echo "security_and_notebook=PASS"
cd "$campaign/tutorials/mini-innovation/enhanced-seir/TRAINING_SHEET_TH"
python src/compare_perf.py
cp results/seir_perf_compare.csv "$campaign/tutorials/mini-innovation/enhanced-seir/PERFORMANCE_WORKSHOP_TH/results/"
cd "$campaign/tutorials/mini-innovation/enhanced-seir/PERFORMANCE_WORKSHOP_TH"
python performance/perf_theory.py
"$campaign/envs/twinb/bin/python" performance/python_stack_overhead.py
python performance/perf_workshop_report.py
python performance/perf_summary_plot.py
echo "performance_postprocess=PASS"
cd "$campaign/tutorials/mini-innovation/02-jupyter-notebook"
mkdir -p notebooks
cp "$campaign/tutorials/mini-innovation/03-epidemic-abs-examples/results/"epi_summary_*.csv results/
python - "$campaign/repo/mini-innovation/02-jupyter-notebook.md" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
blocks = re.findall(r"python - <<'PY'\n(.*?)\nPY", text, re.S)
block = next(block for block in blocks if 'episprint_explore.ipynb' in block)
exec(compile(block, sys.argv[1], 'exec'))
PY
/usr/bin/time -v jupyter nbconvert --execute --to notebook --ExecutePreprocessor.timeout=120 --output executed.ipynb notebooks/episprint_explore.ipynb
echo "episprint_notebook=PASS"
