#!/bin/bash
#SBATCH --job-name=real-athena
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:40:00
set -euo pipefail
module reset
module load cpeCray/25.03
export OMP_NUM_THREADS=1
root="$PWD"
out="$root/results/athena-$SLURM_JOB_ID"
mkdir -p "$out/source"
cp -r sources/athena/. "$out/source/"
git -C sources/athena rev-parse HEAD > "$out/source-commit.txt"
module list 2> "$out/modules.txt"
cd "$out/source"
python3 configure.py --prob=shock_tube --cxx=cray -mpi --mpiccmd=CC
/usr/bin/time -v -o "$out/build-time.txt" make -j4
"$root/envs/science/bin/python" "$root/scripts/prepare_athena.py" "$out/source/inputs/hydro/athinput.sod" "$out/sod.in"
for n in 128 256 512; do
    for p in 1 2 4; do
        for repeat in 1 2 3; do
            run="$out/sod-n${n}-p${p}-r${repeat}"
            mkdir -p "$run"
            cd "$run"
            /usr/bin/time -v -o time.txt srun --exact -n "$p" -c1 "$out/source/bin/athena" \
                -i "$out/sod.in" mesh/nx1="$n" meshblock/nx1=32 \
                problem/compute_error=1 > solver.log 2>&1
            grep -q 'zone-cycles/cpu_second' solver.log
            test -s shock-errors.dat
            tail -5 solver.log
        done
    done
done
