# บทที่ 21: Molecular Dynamics

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/md-gromacs` โดยตรง

## เป้าหมาย

1. ตรวจ GROMACS module และ GPU allocation
2. ใช้ shared benchPEP เมื่อมีใน /project/common
3. บันทึก version, input และ performance summary

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/md-gromacs"
cd "$HOME/hpc-ignite-standalone/md-gromacs"
mkdir -p jobs logs notes results

if [ -z "${LANTA_GPU_PARTITION:-}" ]; then export LANTA_GPU_PARTITION="gpu-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi

cat > jobs/gromacs_preflight.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=gromacs-preflight
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load GROMACS/2024.6-cpeGNU-25.03-CUDA-12.6 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
OUT="results/${SLURM_JOB_ID}"; mkdir -p "$OUT"
gmx --version | tee "$OUT/gmx_version.txt"
TPR="$(find /project/common/GROMACS -name 'benchPEP.tpr' -print -quit 2>/dev/null || true)"
if [ -n "$TPR" ]; then echo "input_tpr=$TPR" | tee "$OUT/summary.txt"; gmx mdrun -s "$TPR" -deffnm "$OUT/benchPEP" -nsteps 100 -ntomp "${SLURM_CPUS_PER_TASK:-1}" | tee "$OUT/mdrun_stdout.txt"; grep -E "Performance|Finished mdrun|Writing final coordinates" "$OUT/benchPEP.log" > "$OUT/performance_summary.txt" || true; else echo "tpr_status=shared_benchpep_pending" | tee "$OUT/summary.txt"; fi
SLURM
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --parsable jobs/gromacs_preflight.sbatch)
echo "$job_id	gromacs_preflight	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -100 logs/gromacs-preflight_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/md-gromacs"
find results -maxdepth 2 -type f | sort
tail -100 logs/gromacs-preflight_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
