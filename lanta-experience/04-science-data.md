# 04 Science And Data Workflow

ใช้รูปแบบงานวิทยาศาสตร์ใน booklet: input, parameter, model script, result, evidence.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `source`, `command -v`, `python`, `head`, `sha256sum`, `module purge`, `module load` และ redirection

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน block เตรียมพื้นที่ใน [README.md](README.md) สำหรับ workspace ของกิจกรรม

## Copy-Paste Diffusion Model

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-experience"
mkdir -p configs jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
```

### ขั้นที่ 2: สร้าง config `configs/diffusion-small.env`

ขั้นนี้สร้างค่ากำกับการทดลอง เพื่อให้ parameter แยกจาก code และตรวจซ้ำได้

```bash
cat > configs/diffusion-small.env <<'EOF'
N=300
STEPS=600
ALPHA=0.15
EOF
```


### ขั้นที่ 3: สร้าง source code `src/diffusion_1d.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/diffusion_1d.py <<'PY'
import argparse
import csv
import math
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=200)
parser.add_argument("--steps", type=int, default=500)
parser.add_argument("--alpha", type=float, default=0.15)
parser.add_argument("--output", default="results/diffusion.csv")
args = parser.parse_args()

u = [0.0] * args.n
for i in range(args.n):
    x = i / (args.n - 1)
    u[i] = math.exp(-200.0 * (x - 0.5) ** 2)

t0 = time.time()
for _ in range(args.steps):
    v = u[:]
    for i in range(1, args.n - 1):
        v[i] = u[i] + args.alpha * (u[i - 1] - 2 * u[i] + u[i + 1])
    u = v

Path(args.output).parent.mkdir(parents=True, exist_ok=True)
with open(args.output, "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["i", "value"])
    for i, value in enumerate(u):
        writer.writerow([i, f"{value:.8f}"])
print(f"output={args.output} elapsed={time.time() - t0:.3f}")
PY
```


### ขั้นที่ 4: สร้าง Slurm script `jobs/diffusion.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/diffusion.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=diffusion
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/diffusion_%j.out
#SBATCH --error=logs/diffusion_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
source configs/diffusion-small.env
python src/diffusion_1d.py --n "$N" --steps "$STEPS" --alpha "$ALPHA" --output "results/diffusion_${SLURM_JOB_ID}.csv"
RUN="diffusion_${SLURM_JOB_ID}"
mkdir -p "results/$RUN"
cp configs/diffusion-small.env "results/$RUN/"
cp jobs/diffusion.sbatch "results/$RUN/"
cat > "results/$RUN/README.txt" <<EOF
question: 1D diffusion baseline
workspace: $(pwd)
date: $(date -Is)
job: ${SLURM_JOB_ID}
result: results/diffusion_${SLURM_JOB_ID}.csv
validation: CSV has header i,value and N rows
EOF
SLURM
```

### ขั้นที่ 5: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/diffusion.sbatch)
echo "$job_id	diffusion	$(date -Is)" >> notes/job-history.tsv
echo "Submitted diffusion job: $job_id"
echo "Read:"
echo "  head results/diffusion_${job_id}.csv"
echo "  cat results/diffusion_${job_id}/README.txt"
```

### คำอธิบาย

ในขั้นตอนนี้ ผู้ใช้จะรันแบบจำลอง diffusion ขนาดเล็ก โดยแยกไฟล์พารามิเตอร์ไว้ที่ `configs/diffusion-small.env`, แยก code ไว้ที่ `src/diffusion_1d.py`, และแยก job script ไว้ที่ `jobs/diffusion.sbatch`

เมื่อ job ทำงาน ระบบจะเขียนผลลัพธ์เป็น `results/diffusion_<job-id>.csv` และคัดลอก config กับ job script ไปไว้ใน `results/diffusion_<job-id>/` เพื่อให้ผู้ใช้ย้อนดูได้ว่ารอบนั้นใช้ค่าใด

เมื่อสำเร็จ ไฟล์ CSV ต้องมี header `i,value` และจำนวนบรรทัดควรสัมพันธ์กับค่า `N` เมื่อ `source configs/diffusion-small.env` error ให้ตรวจรูปแบบ `KEY=value` โดยเขียนเครื่องหมาย `=` ติดกับชื่อและค่า เมื่องานหมดเวลา ให้ลด `STEPS` ก่อนเพิ่มเวลาใน Slurm

## Copy-Paste Small Data Summary

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-experience"
mkdir -p input notes results src

if command -v module >/dev/null 2>&1; then
    module purge
    module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
fi
command -v python
```

### ขั้นที่ 2: สร้าง source code `src/make_sensor_data.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/make_sensor_data.py <<'PY'
import csv
import math
import random
from pathlib import Path

Path("input").mkdir(exist_ok=True)
random.seed(7)
with open("input/sensor.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["minute", "station", "pm25"])
    for minute in range(1440):
        for station in range(5):
            value = 18 + 10 * math.sin(minute / 1440 * 6.283) + random.random() * 5 + station
            writer.writerow([minute, f"S{station}", f"{value:.2f}"])
PY
```


### ขั้นที่ 3: สร้าง source code `src/summarize_sensor.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/summarize_sensor.py <<'PY'
import csv
import statistics
from collections import defaultdict
from pathlib import Path

groups = defaultdict(list)
with open("input/sensor.csv", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        groups[row["station"]].append(float(row["pm25"]))

Path("results").mkdir(exist_ok=True)
with open("results/sensor_summary.csv", "w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["station", "count", "mean", "max"])
    for station, values in sorted(groups.items()):
        writer.writerow([station, len(values), f"{statistics.mean(values):.2f}", f"{max(values):.2f}"])
print("results/sensor_summary.csv")
PY
```

### ขั้นที่ 4: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
python src/make_sensor_data.py
python src/summarize_sensor.py
head results/sensor_summary.csv
sha256sum input/sensor.csv results/sensor_summary.csv > notes/sensor-checksums.txt
```

### คำอธิบาย

ในขั้นตอนนี้ ผู้ใช้จะสร้างข้อมูล PM2.5 จำลองใน `input/sensor.csv` แล้วรัน `summarize_sensor.py` เพื่อสรุปค่าเฉลี่ยและค่าสูงสุดรายสถานี

ตัวอย่างนี้รันบน login node ได้เพราะข้อมูลมีขนาดเล็กมาก ใช้เพื่อฝึก format เท่านั้น หากข้อมูลใหญ่ขึ้นหรือใช้เวลานาน ให้ย้ายขั้นตอนนี้เข้า Slurm job ทันที

เมื่อสำเร็จ `head results/sensor_summary.csv` จะเห็น header `station,count,mean,max` และมีไฟล์ checksum ใน `notes/sensor-checksums.txt` เมื่อพบ `python: command not found` ให้โหลด `cray-python` เมื่อพบ `FileNotFoundError` ให้ตรวจว่าอยู่ใน `$HOME/lanta-experience` และรัน script สร้างข้อมูลก่อน
