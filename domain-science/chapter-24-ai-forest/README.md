# บทที่ 24: AI สำหรับป่าไม้

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/forest-ndvi` โดยตรง

## เป้าหมาย

1. สร้าง NDVI grid จำลอง
2. จัดชั้นสภาพพืชพรรณ
3. บันทึก CSV เพื่อใช้ต่อกับ geospatial workflow

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/forest-ndvi"
cd "$HOME/hpc-ignite-standalone/forest-ndvi"
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
```

### ขั้นที่ 2: สร้าง source code `src/ndvi_grid.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/ndvi_grid.py <<'PYCODE'
from pathlib import Path
import csv
Path("results").mkdir(exist_ok=True)
out = Path("results/ndvi_grid.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["cell", "red", "nir", "ndvi", "class"])
    for cell, (red, nir) in enumerate([(0.12, 0.52), (0.22, 0.48), (0.30, 0.35), (0.10, 0.60)]):
        ndvi = (nir - red) / (nir + red); klass = "dense" if ndvi > 0.5 else "mixed" if ndvi > 0.25 else "sparse"
        writer.writerow([cell, red, nir, f"{ndvi:.3f}", klass])
print(f"result={out}")
PYCODE
```


### ขั้นที่ 3: สร้าง Slurm script `jobs/forest-ndvi.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/forest-ndvi.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=forest-ndvi
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
python src/ndvi_grid.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/forest-ndvi.sbatch)
echo "$job_id	forest-ndvi	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/forest-ndvi_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/forest-ndvi"
cat results/ndvi_grid.csv
tail -50 logs/forest-ndvi_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
