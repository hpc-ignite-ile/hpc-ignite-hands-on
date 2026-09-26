# บทเริ่มต้น: ส่งงานแรกบน LANTA

## ก่อนลงมือ

ส่งงานแรกและอ่านผลที่เครื่องสร้างขึ้น

- **ใช้เครื่องเท่าไร:** เริ่มจาก CPU 1 คอร์ตามตัวอย่าง งานสั้นอาจเสียเวลาส่วนใหญ่ไปกับการเริ่มโปรแกรม
- **ตรวจผลและลองปรับ:** ตรวจไฟล์ผลลัพธ์และสถานะงานก่อนเพิ่มขนาด อย่าใช้เวลาของงานทักทายมาสรุปความเร็วของเครื่อง

จดเวลาที่ใช้และหน่วยความจำหลังงานจบ แล้วดู [วิธีประมาณและอ่านการใช้ทรัพยากร](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md) เพื่อวางแผนรอบถัดไป

![ส่งคำสั่งผ่าน login และ Slurm; งานคำนวณเกิดบน เครื่องคำนวณ](../../docs/images/beginners/lanta-job-workflow.png)

ภาพแนวคิด: ส่งด้วย sbatch แล้วรอ allocation ก่อนคำนวณ จบแล้วตรวจ exit code, log และ output ไม่ใช่ดูเพียงว่า job หายจาก queue. อ่าน [คู่มือเริ่มต้นด้วยภาพ](../../docs/BEGINNER_VISUAL_GUIDE_TH.md) สำหรับคำอธิบายทีละขั้น


คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ ชุดคำสั่ง ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น บทฝึกที่ทำตามได้ในหน้าเดียว ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ พื้นที่ทำงาน, source file, ไฟล์งาน Slurm, log และ result ครบใน `$HOME/hpc-ignite-standalone/foundation-first-job` โดยตรง

## เป้าหมาย

1. สร้าง Python source และ ไฟล์งาน Slurm จากหน้าเดียว
2. ส่งงาน CPU การทดสอบเบื้องต้น
3. ตรวจ log และ result

## ลงมือทำบน LANTA

แปะทีละ ชุดคำสั่ง ตามลำดับ แต่ละ ชุดคำสั่ง ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม พื้นที่ทำงาน และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง โฟลเดอร์ มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/foundation-first-job"
cd "$HOME/hpc-ignite-standalone/foundation-first-job"
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

### ขั้นที่ 2: สร้าง โค้ดโปรแกรม `src/hello_lanta.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/hello_lanta.py <<'PYCODE'
from pathlib import Path
import os
Path("results").mkdir(exist_ok=True)
out = Path("results") / f"hello_{os.environ.get('SLURM_JOB_ID', 'manual')}.txt"
out.write_text("hello from standalone LANTA hand-on\n", encoding="utf-8")
print(out)
PYCODE
```


### ขั้นที่ 3: สร้าง ไฟล์งาน Slurm `jobs/hello-lanta.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, โฟลเดอร์ทำงาน และคำสั่งที่รันบน เครื่องคำนวณ

```bash
cat > jobs/hello-lanta.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hello-lanta
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/hello_lanta.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง ไฟล์งาน ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก หมายเลขงาน เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/hello-lanta.sbatch)
echo "$job_id	hello-lanta	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/hello-lanta_${job_id}.out"
```

## ตรวจผล

```bash
cd "$HOME/hpc-ignite-standalone/foundation-first-job"
find results -maxdepth 2 -type f | sort
tail -50 logs/hello-lanta_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี ข้อความผลและข้อผิดพลาด ของ หมายเลขงาน นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ดูไฟล์ตัวอย่างเพิ่มเติม

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ ชุดคำสั่ง ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
