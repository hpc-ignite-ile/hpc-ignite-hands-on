# บทที่ 11: Containers สำหรับ HPC

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-containers` โดยตรง

## เป้าหมาย

1. ตรวจ Apptainer module
2. รัน payload Python สั้นใน batch job
3. บันทึก version และ payload result

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-containers"
cd "$HOME/hpc-ignite-standalone/ai-containers"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then export LANTA_CPU_PARTITION="compute-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi

cat > src/container_demo.py <<'PYCODE'
from pathlib import Path
import json, os
Path("results").mkdir(exist_ok=True)
summary = {"job_id": os.environ.get("SLURM_JOB_ID", "manual"), "message": "local Python payload for Apptainer preflight"}
Path("results/container_payload.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PYCODE

cat > jobs/apptainer_preflight.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=apptainer-preflight
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load Apptainer/1.1.6 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
apptainer --version | tee "results/${SLURM_JOB_ID}/apptainer_version.txt"
python src/container_demo.py | tee "results/${SLURM_JOB_ID}/payload.txt"
cp results/container_payload.json "results/${SLURM_JOB_ID}/container_payload.json"
SLURM
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/apptainer_preflight.sbatch)
echo "$job_id	apptainer_preflight	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -80 logs/apptainer-preflight_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/ai-containers"
find results -maxdepth 2 -type f | sort
tail -80 logs/apptainer-preflight_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
