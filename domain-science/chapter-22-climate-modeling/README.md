# บทที่ 22: การจำลองภูมิอากาศ

## ก่อนลงมือ

อ่านหรือสร้างข้อมูลบนตารางสำหรับเรียนรู้เรื่องภูมิอากาศ

- **ใช้เครื่องเท่าไร:** จำนวนช่องตาราง × จำนวนตัวแปร × ไบต์ต่อค่า เป็นเพียงขนาดข้อมูลพื้นฐาน ยังต้องเผื่อข้อมูลชั่วคราว
- **ตรวจผลและลองปรับ:** เพิ่มความกว้างและสูงสองเท่าจะได้ช่องเพิ่มสี่เท่า ตรวจหน่วยและค่าที่หายไป ตัวอย่างข้อมูลสมมติไม่ใช่พยากรณ์อากาศจริง

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

ต่อยอดจากข้อมูลสมมติได้ที่ [บทการไหล ภูมิอากาศ และทะเล](../../docs/CFD_CLIMATE_OCEAN_EXPERIMENTS.md) ซึ่งช่วยเลือกโจทย์และวิธีตรวจคำตอบก่อนเริ่มงานจริง


คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ ชุดคำสั่ง ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น บทฝึกที่ทำตามได้ในหน้าเดียว ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ พื้นที่ทำงาน, source file, ไฟล์งาน Slurm, log และ result ครบใน `$HOME/hpc-ignite-standalone/climate-grid` โดยตรง

## เป้าหมาย

1. สร้าง grid ภูมิอากาศจำลอง
2. คำนวณ temperature และ rain summary
3. บันทึก CSV สำหรับ postprocess

## ลงมือทำบน LANTA

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

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
```

### ขั้นที่ 2: สร้าง โค้ดโปรแกรม `src/climate_grid.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
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
```


### ขั้นที่ 3: สร้าง ไฟล์งาน Slurm `jobs/climate-grid.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, โฟลเดอร์ทำงาน และคำสั่งที่รันบน เครื่องคำนวณ

```bash
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
set +u  # GDAL activation reads optional unset variables
conda activate netcdf-py39
set -u
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/climate_grid.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง ไฟล์งาน ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก หมายเลขงาน เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/climate-grid.sbatch)
echo "$job_id	climate-grid	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/climate-grid_${job_id}.out"
```

## ตรวจผล

```bash
cd "$HOME/hpc-ignite-standalone/climate-grid"
head results/climate_grid_summary.csv
tail -50 logs/climate-grid_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี ข้อความผลและข้อผิดพลาด ของ หมายเลขงาน นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ดูไฟล์ตัวอย่างเพิ่มเติม

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ ชุดคำสั่ง ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
