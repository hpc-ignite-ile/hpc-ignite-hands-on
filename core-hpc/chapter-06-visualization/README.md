# บทที่ 6: การสร้างภาพข้อมูล

## ก่อนลงมือ

เปลี่ยนข้อมูลเป็นกราฟและตรวจภาพผลลัพธ์

- **ใช้เครื่องเท่าไร:** เริ่มด้วย CPU 1 คอร์ ภาพที่กว้างหรือสูงขึ้นใช้หน่วยความจำมากขึ้น
- **ตรวจผลและลองปรับ:** เปรียบเทียบจำนวนจุดหรือความละเอียดภาพทีละอย่าง ตรวจหน่วยบนแกนและค่าจากไฟล์ข้อมูลเสมอ

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ ชุดคำสั่ง ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น บทฝึกที่ทำตามได้ในหน้าเดียว ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ พื้นที่ทำงาน, source file, ไฟล์งาน Slurm, log และ result ครบใน `$HOME/hpc-ignite-standalone/core-visualization` โดยตรง

## เป้าหมาย

1. สร้าง CSV สัญญาณจำลอง
2. สร้าง plot ด้วย Matplotlib ใน batch job
3. ตรวจไฟล์ PNG และ CSV

## ลงมือทำบน LANTA

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/core-visualization"
cd "$HOME/hpc-ignite-standalone/core-visualization"
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

### ขั้นที่ 2: สร้าง โค้ดโปรแกรม `src/make_plot.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/make_plot.py <<'PYCODE'
from pathlib import Path
import csv
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
Path("results").mkdir(exist_ok=True)
csv_path = Path("results/signal.csv")
with csv_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["x", "value"])
    for i in range(120): writer.writerow([i, math.sin(i / 12) + 0.2 * math.cos(i / 5)])
xs, ys = [], []
with csv_path.open(encoding="utf-8") as handle:
    next(handle)
    for line in handle:
        x, y = line.strip().split(","); xs.append(float(x)); ys.append(float(y))
plt.figure(figsize=(7, 3)); plt.plot(xs, ys); plt.xlabel("sample"); plt.ylabel("value"); plt.title("Standalone signal plot"); plt.tight_layout()
png = Path("results/signal.png"); plt.savefig(png, dpi=140)
print(f"csv={csv_path}"); print(f"png={png}")
PYCODE
```


### ขั้นที่ 3: สร้าง ไฟล์งาน Slurm `jobs/viz-plot.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, โฟลเดอร์ทำงาน และคำสั่งที่รันบน เครื่องคำนวณ

```bash
cat > jobs/viz-plot.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=viz-plot
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load Mamba/23.11.0-0 2>/dev/null || true
set +u  # GDAL activation reads optional unset variables
conda activate netcdf-py39
set -u
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/make_plot.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง ไฟล์งาน ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก หมายเลขงาน เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/viz-plot.sbatch)
echo "$job_id	viz-plot	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/viz-plot_${job_id}.out"
```

## ตรวจผล

```bash
cd "$HOME/hpc-ignite-standalone/core-visualization"
find results -maxdepth 2 -type f | sort
ls -lh results/signal.png
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี ข้อความผลและข้อผิดพลาด ของ หมายเลขงาน นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ดูไฟล์ตัวอย่างเพิ่มเติม

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ ชุดคำสั่ง ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
