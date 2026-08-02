# บทที่ 22: การจำลองภูมิอากาศ

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/climate-grid` โดยตรง

## เป้าหมาย

1. สร้าง grid ภูมิอากาศจำลอง
2. คำนวณ temperature และ rain summary
3. บันทึก CSV สำหรับ postprocess

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/climate-grid"
cd "$HOME/hpc-ignite-standalone/climate-grid"
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

cat > src/climate_grid.py <<'PYCODE'
from pathlib import Path
import csv, math
Path("results").mkdir(exist_ok=True)
out = Path("results/climate_grid_summary.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["lat", "lon", "temperature_c", "rain_mm"])
    for lat in range(16, 21):
        for lon in range(98, 103): writer.writerow([lat, lon, f"{30 - 0.4 * (lat - 16) + math.sin(lon):.2f}", f"{4 + 0.5 * (lat - 16) + 0.1 * (lon - 98):.2f}"])
print(f"result={out}")
PYCODE

cat > jobs/climate-grid.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=climate-grid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load Mamba/23.11.0-0 2>/dev/null || module load cray-python/3.10.10 2>/dev/null || true
conda activate netcdf-py39 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/climate_grid.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/climate-grid.sbatch)
echo "$job_id	climate-grid	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/climate-grid_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/climate-grid"
head results/climate_grid_summary.csv
tail -50 logs/climate-grid_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
