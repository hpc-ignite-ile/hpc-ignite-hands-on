# 01 ส่งงานแรกด้วย Slurm

## ก่อนลงมือ

ส่งงานแรกและอ่านผลที่เครื่องสร้างขึ้น

- **ใช้เครื่องเท่าไร:** เริ่มจาก CPU 1 คอร์ตามตัวอย่าง งานสั้นอาจเสียเวลาส่วนใหญ่ไปกับการเริ่มโปรแกรม
- **ตรวจผลและลองปรับ:** ตรวจไฟล์ผลลัพธ์และสถานะงานก่อนเพิ่มขนาด อย่าใช้เวลาของงานทักทายมาสรุปความเร็วของเครื่อง

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

สร้าง Python script และ Slurm ไฟล์งาน ด้วย heredoc แล้วส่งด้วย `sbatch` โดยตรง.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น heredoc, `sbatch`, `squeue`, `sacct`, `tail`, `cat`, `module purge`, `module load` และ `SLURM_SUBMIT_DIR`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน ชุดคำสั่ง เตรียมพื้นที่ใน [README.md](README.md) สำหรับ พื้นที่ทำงาน ของกิจกรรม

## ลงมือทำ

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
```

### ขั้นที่ 2: สร้าง โค้ดโปรแกรม `src/hello_lanta.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/hello_lanta.py <<'PY'
from pathlib import Path
import os
import platform
import time

Path("results").mkdir(exist_ok=True)
job_id = os.environ.get("SLURM_JOB_ID", "manual")
out = Path("results") / f"hello_{job_id}.txt"

lines = [
    f"job_id={job_id}",
    f"host={platform.node()}",
    f"user={os.environ.get('USER', 'unknown')}",
    f"submit_dir={os.environ.get('SLURM_SUBMIT_DIR', os.getcwd())}",
    f"time={time.strftime('%Y-%m-%d %H:%M:%S')}",
]
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(out)
PY
```


### ขั้นที่ 3: สร้าง ไฟล์งาน Slurm `jobs/hello_lanta.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, โฟลเดอร์ทำงาน และคำสั่งที่รันบน เครื่องคำนวณ

```bash
cat > jobs/hello_lanta.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hello_lanta
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:05:00
#SBATCH --output=logs/hello_%j.out
#SBATCH --error=logs/hello_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
python src/hello_lanta.py
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง ไฟล์งาน ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก หมายเลขงาน เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/hello_lanta.sbatch)
echo "$job_id	hello_lanta	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "After completion:"
echo "  sacct -j $job_id --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode"
echo "  tail -50 logs/hello_${job_id}.out"
echo "  cat results/hello_${job_id}.txt"
```

### คำอธิบาย

ในขั้นตอนนี้ ผู้ใช้จะสร้างไฟล์สองไฟล์ คือ `src/hello_lanta.py` สำหรับงาน Python และ `jobs/hello_lanta.sbatch` สำหรับบอก Slurm ว่าต้องใช้ทรัพยากรเท่าใด

เมื่อส่งด้วย `sbatch` งานจะเข้า queue เพื่อให้ Slurm จัดไปยัง เครื่องคำนวณ ไฟล์ log จะถูกเก็บใน `logs/` และผลลัพธ์ของ Python จะถูกเก็บใน `results/`

เมื่อสำเร็จ `sbatch` จะคืน หมายเลขงาน ให้ผู้ใช้ จากนั้นใช้ `squeue -j <job-id>` เพื่อตรวจสถานะ และใช้ `sacct` หลังงานจบเพื่อตรวจว่าเป็น `COMPLETED` เมื่อ submit error ให้ตรวจ `LANTA_ACCOUNT` เมื่อ job ค้างให้ดู reason ใน `squeue` เมื่อ log แจ้งว่า Python หาย ให้ตรวจ `module avail python` และส่งงาน Slurm ผ่าน `sbatch`

## ลองเปลี่ยนด้วยตัวเอง

เปลี่ยนข้อความที่เขียนใน `src/hello_lanta.py` หรือเปลี่ยน `--time` ใน `jobs/hello_lanta.sbatch` แล้วส่งใหม่.
