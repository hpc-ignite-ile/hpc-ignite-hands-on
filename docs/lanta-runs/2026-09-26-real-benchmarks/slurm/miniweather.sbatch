#!/bin/bash
#SBATCH --job-name=real-miniweather
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
set -euo pipefail
module reset
module load cpeCray/25.03 cray-parallel-netcdf
export OMP_NUM_THREADS=1
root="$PWD"
out="$root/results/miniweather-$SLURM_JOB_ID"
mkdir -p "$out/build"
module list 2> "$out/modules.txt"
git -C sources/miniWeather rev-parse HEAD > "$out/source-commit.txt"
for spec in THERMAL DENSITY_CURRENT; do
    for nx in 200 400; do
        nz=$((nx/2))
        exe="$out/build/${spec}-${nx}"
        /usr/bin/time -v -o "$exe-build-time.txt" CC -O3 -std=c++17 \
            -D_NX="$nx" -D_NZ="$nz" -D_SIM_TIME=1000 -D_OUT_FREQ=1000 -D_DATA_SPEC="DATA_SPEC_$spec" \
            "$root/sources/miniWeather/c/miniWeather_mpi.cpp" -lpnetcdf -o "$exe"
        for ranks in 1 2 4; do
            for repeat in 1 2 3; do
                run="$out/${spec}-n${nx}-p${ranks}-r${repeat}"
                mkdir -p "$run"
                cd "$run"
                /usr/bin/time -v -o time.txt srun --exact -n "$ranks" -c 1 "$exe" > solver.log 2>&1
                tail -4 solver.log
            done
        done
    done
done
