#!/bin/bash
#SBATCH --job-name=real-mitgcm
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
set -euo pipefail
module reset
module load cpeGNU/25.03
export OMP_NUM_THREADS=1
root="$PWD"
out="$root/results/mitgcm-$SLURM_JOB_ID"
src="$root/sources/MITgcm"
mkdir -p "$out"
module list 2> "$out/modules.txt"
git -C "$src" rev-parse HEAD > "$out/source-commit.txt"
for ranks in 1 4; do
    build="$out/build-p$ranks"
    mkdir -p "$build/code"
    cp "$src/verification/tutorial_baroclinic_gyre/code/"* "$build/code/"
    "$root/envs/science/bin/python" "$root/scripts/prepare_mitgcm.py" "$build/code/SIZE.h" "$ranks"
    cd "$build"
    "$src/tools/genmake2" -rootdir "$src" -mods ./code -of "$root/slurm/mitgcm-options" -mpi -disable=mnc > configure.log 2>&1
    make depend > depend.log 2>&1
    /usr/bin/time -v -o build-time.txt make -j4 > build.log 2>&1
    for repeat in 1 2 3; do
        run="$out/gyre-p${ranks}-r${repeat}"
        mkdir -p "$run"
        cp "$src/verification/tutorial_baroclinic_gyre/input/"* "$run/"
        "$root/envs/science/bin/python" "$root/scripts/prepare_mitgcm.py" "$run/data" run
        cd "$run"
        /usr/bin/time -v -o time.txt srun --exact -n "$ranks" -c1 "$build/mitgcmuv" > solver.log 2>&1
    done
done
