# บทที่ 26: เกษตรอัจฉริยะ

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/agri-risk` โดยตรง

## เป้าหมาย

1. สร้างข้อมูล plot เกษตรจำลอง
2. คำนวณ water-stress risk
3. บันทึก CSV สำหรับตัดสินใจเชิงข้อมูล

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/agri-risk"
cd "$HOME/hpc-ignite-standalone/agri-risk"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then
    export LANTA_CPU_PARTITION="compute-devel"
fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi

cat > src/agri_risk.py <<'PYCODE'
from pathlib import Path
import csv
Path("results").mkdir(exist_ok=True)
out = Path("results/agri_risk.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["plot", "soil_moisture", "rain_7d", "risk"])
    for plot, soil, rain in [("A", 0.31, 18), ("B", 0.18, 4), ("C", 0.42, 30), ("D", 0.22, 7)]:
        risk = "water_stress" if soil < 0.25 and rain < 10 else "stable"; writer.writerow([plot, soil, rain, risk])
print(f"result={out}")
PYCODE

cat > jobs/agri-risk.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=agri-risk
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load GDAL/3.6.4-cpeCray-23.03 2>/dev/null || module load cray-python/3.10.10 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/agri_risk.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/agri-risk.sbatch)
echo "$job_id	agri-risk	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/agri-risk_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/agri-risk"
cat results/agri_risk.csv
tail -50 logs/agri-risk_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
