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

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/qe.sh
OUT="results/qe_${SLURM_JOB_ID}"
mkdir -p "$OUT"

PSEUDO_FILE="$(find /project/common/QuantumEspresso -iname 'Si*.UPF' -print -quit 2>/dev/null || true)"
if [ -z "$PSEUDO_FILE" ]; then
    echo "No Si pseudopotential found under /project/common/QuantumEspresso; module smoke completed." | tee "$OUT/summary.txt"
    pw.x -h > "$OUT/pw_help.txt" 2>&1 || true
    exit 0
fi

PSEUDO_DIR="$(dirname "$PSEUDO_FILE")"
PSEUDO_NAME="$(basename "$PSEUDO_FILE")"
export ESPRESSO_TMPDIR="${ESPRESSO_TMPDIR:-${SCRATCH:-/tmp}/qe_${SLURM_JOB_ID}}"
mkdir -p "$ESPRESSO_TMPDIR"

cat > "$OUT/si_scf.in" <<EOF
&CONTROL
  calculation = 'scf',
  prefix = 'si_smoke',
  pseudo_dir = '$PSEUDO_DIR',
  outdir = '$ESPRESSO_TMPDIR'
/
&SYSTEM
  ibrav = 2,
  celldm(1) = 10.20,
  nat = 2,
  ntyp = 1,
  ecutwfc = 18.0
/
&ELECTRONS
  conv_thr = 1.0d-6
/
ATOMIC_SPECIES
Si 28.0855 $PSEUDO_NAME
ATOMIC_POSITIONS alat
Si 0.00 0.00 0.00
Si 0.25 0.25 0.25
K_POINTS automatic
2 2 2 0 0 0
EOF

srun -n "$SLURM_NTASKS" pw.x -inp "$OUT/si_scf.in" | tee "$OUT/si_scf.out"
grep -E "total energy|convergence has been achieved" "$OUT/si_scf.out" > "$OUT/qe_summary.txt" || true
