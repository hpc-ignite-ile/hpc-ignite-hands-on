#!/bin/bash
#SBATCH --job-name=qe-scf-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/module-loads/qe.sh
mkdir -p "results/qe_${SLURM_JOB_ID}"

cat > "results/qe_${SLURM_JOB_ID}/README.txt" <<'EOF'
Template only. Copy or generate a tiny Quantum ESPRESSO input, then run:
srun -n "$SLURM_NTASKS" pw.x -inp input.in
EOF
