#!/bin/bash
#SBATCH --job-name=real-gromacs
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=24G
#SBATCH --time=01:00:00
set -euo pipefail
module purge
module load GROMACS/2026.3-cpeGNU-25.03-CUDA-12.6
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
out="$PWD/results/gromacs-$SLURM_JOB_ID"
mkdir -p "$out"
module list 2> "$out/modules.txt"
gmx --version > "$out/version.txt"
sha256sum inputs/benchMEM.tpr > "$out/input.sha256"
gmx dump -s inputs/benchMEM.tpr > "$out/input-dump.txt" 2>&1
sampler=""
if [[ "${MODE:-cpu}" == gpu ]]; then
    nvidia-smi --query-gpu=timestamp,uuid,utilization.gpu,memory.used,power.draw --format=csv -l 1 > "$out/gpu.csv" &
    sampler=$!
    flags=(-nb gpu -pme gpu -bonded cpu -update cpu)
else
    flags=(-nb cpu -pme cpu -bonded cpu -update cpu)
fi
trap 'if [[ -n "$sampler" ]]; then kill "$sampler" 2>/dev/null || true; fi' EXIT
reset=()
if (( ${STEPS:-50000} >= 5000 )); then reset=(-resethway); fi
for repeat in $(seq 1 "${REPEATS:-3}"); do
    run="$out/repeat-$repeat"
    mkdir -p "$run"
    /usr/bin/time -v -o "$run/time.txt" gmx mdrun -s inputs/benchMEM.tpr \
        -deffnm "$run/md" -nsteps "${STEPS:-50000}" -ntmpi 1 -ntomp "$SLURM_CPUS_PER_TASK" \
        -pin on -noconfout "${reset[@]}" "${flags[@]}" > "$run/stdout.txt" 2> "$run/stderr.txt"
    printf 'Potential\nTemperature\n0\n' | gmx energy -f "$run/md.edr" -o "$run/energy.xvg" > "$run/energy-summary.txt" 2>&1
    grep 'Performance:' "$run/md.log"
done
