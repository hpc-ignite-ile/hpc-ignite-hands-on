"""Instrument fresh, extracted campaign jobs, never the source checkout.

Slurm directives are retained; the original body runs unchanged inside the
allocation under GNU time. Results are copied per job before a later repeat can
overwrite generic filenames. GPU sampling is best-effort, not a power meter.
"""
import argparse
import hashlib
import json
import re
import shlex
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root/'tutorials/manifest.json').is_file():
        raise SystemExit('Expected an extracted campaign, not a source checkout')
    manifest_path = root/'instrumentation.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    for section in ('tutorials', 'repo'):
        for job in sorted((root/section).rglob('*.sbatch')):
            if 'templates' in job.parts or 'qualification' in job.parts:
                continue
            body = job.with_suffix('.sbatch.body')
            if body.exists():
                continue
            original = job.read_text()
            directives = '\n'.join(line for line in original.splitlines() if line.startswith('#SBATCH'))
            body.write_text(original)
            wrapper = '''#!/bin/bash
DIRECTIVES
set -uo pipefail
run_key="${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID}}_${SLURM_ARRAY_TASK_ID:-single}"
measurement="$PWD/notes/measurement-$run_key"
mkdir -p "$measurement"
printf 'job=%s\nnode=%s\ncpus_per_task=%s\n' "$SLURM_JOB_ID" "$SLURM_JOB_NODELIST" "${SLURM_CPUS_PER_TASK:-1}" > "$measurement/context.txt"
date -Is >> "$measurement/context.txt"
sampler=""
if command -v nvidia-smi >/dev/null && [[ -n "${SLURM_JOB_GPUS:-}" || -n "${CUDA_VISIBLE_DEVICES:-}" ]]; then
    nvidia-smi --query-gpu=timestamp,index,uuid,utilization.gpu,memory.used,power.draw --format=csv -l 1 > "$measurement/gpu.csv" 2> "$measurement/gpu-sampling.err" &
    sampler=$!
fi
cleanup() { if [[ -n "$sampler" ]]; then kill "$sampler" 2>/dev/null || true; wait "$sampler" 2>/dev/null || true; fi; }
trap cleanup EXIT TERM INT
/usr/bin/time -v -o "$measurement/time.txt" bash BODY
status=$?
printf '%s\n' "$status" > "$measurement/exit-code.txt"
python3 SNAPSHOT "$measurement" "$PWD"
exit "$status"
'''.replace('DIRECTIVES', directives).replace('BODY', shlex.quote(str(body))).replace('SNAPSHOT', shlex.quote(str(root/'repo/scripts/snapshot_campaign_result.py')))
            job.write_text(wrapper)
            manifest.append({'script':str(job.relative_to(root)), 'original_sha256':hashlib.sha256(original.encode()).hexdigest()})
    (root/'instrumentation.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'instrumented {len(manifest)} jobs')


if __name__ == '__main__':
    main()
