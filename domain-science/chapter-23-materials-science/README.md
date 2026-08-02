# บทที่ 23: วัสดุศาสตร์

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/materials-qe` โดยตรง

## เป้าหมาย

1. ตรวจ Quantum ESPRESSO module
2. สร้าง input Si SCF ขนาดเล็กเมื่อ pseudopotential พร้อม
3. บันทึก energy หรือ preflight summary

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/materials-qe"
cd "$HOME/hpc-ignite-standalone/materials-qe"
mkdir -p jobs logs notes results

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then export LANTA_CPU_PARTITION="compute-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi

cat > jobs/qe_si_preflight.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=qe-si-preflight
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load QuantumESPRESSO/7.3.1-libxc-6.2.2-cpu 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
OUT="results/${SLURM_JOB_ID}"; mkdir -p "$OUT"
command -v pw.x | tee "$OUT/pw_path.txt"
PSEUDO_FILE="$(find /project/common/QuantumEspresso -iname 'Si*.UPF' -print -quit 2>/dev/null || true)"
if [ -z "$PSEUDO_FILE" ]; then pw.x -h > "$OUT/pw_help.txt" 2>&1 || true; echo "pseudo_status=shared_si_pseudo_pending" | tee "$OUT/summary.txt"; exit 0; fi
PSEUDO_DIR="$(dirname "$PSEUDO_FILE")"; PSEUDO_NAME="$(basename "$PSEUDO_FILE")"; export ESPRESSO_TMPDIR="${ESPRESSO_TMPDIR:-${SCRATCH:-/tmp}/qe_${SLURM_JOB_ID}}"; mkdir -p "$ESPRESSO_TMPDIR"
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
SLURM
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/qe_si_preflight.sbatch)
echo "$job_id	qe_si_preflight	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -100 logs/qe-si-preflight_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/materials-qe"
find results -maxdepth 2 -type f | sort
tail -120 logs/qe-si-preflight_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
