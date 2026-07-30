# LANTA Foundation Lab: งานแรกที่รันได้จริง

บทนี้เป็นฐานสำหรับผู้เรียน HPC Ignite ที่ต้องการเริ่มจากศูนย์บน LANTA โดยเน้นลำดับเดียวกับ handbook ล่าสุด:
login, files, modules, job script, monitoring, results และ next experiment

เป้าหมายคือให้ผู้เรียนส่งงาน Slurm ที่รันได้จริงภายในเวลาไม่กี่นาที โดยยังไม่ต้องติดตั้ง package หนักหรือใช้ GPU

## สิ่งที่จะได้ฝึก

1. ตรวจว่าอยู่บน login node หรือ compute node
2. อ่านตัวแปร Slurm เช่น `SLURM_JOB_ID`, `SLURM_CPUS_PER_TASK`, `SLURM_SUBMIT_DIR`
3. โหลด environment พื้นฐานด้วย Lmod
4. ส่งงาน batch ด้วย `sbatch`
5. ติดตามงานด้วย `squeue`
6. อ่านผลลัพธ์ใน `logs/` และ `results/`
7. เปลี่ยนจากงานเดียวเป็น job array ขนาดเล็ก

## Quick Start บน LANTA

### Copy-paste only

เหมาะสำหรับผู้เรียนที่ยังไม่ต้องการเปิด editor หรือแก้ไฟล์เอง ให้แปะ block นี้ใน terminal บน LANTA:

```bash
cat > /tmp/hpc_ignite_foundation_copy_paste.sh <<'BASH'
#!/bin/bash
set -euo pipefail

REPO="$HOME/hpc-ignite-hands-on"
cd "$REPO"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm, เช่น pv915002: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

echo "ใช้ account   : $HPC_IGNITE_ACCOUNT"
echo "ใช้ partition : $HPC_IGNITE_PARTITION"

bash scripts/lanta_submit_foundation.sh smoke

echo
echo "ดูคิว:"
echo "  squeue -u $USER"
echo
echo "ดูผลลัพธ์หลังงานจบ:"
echo "  ls -lh logs"
echo "  find results/foundation -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_foundation_copy_paste.sh
```

ถ้าต้องการส่งทั้งสามงาน foundation ในครั้งเดียว ให้เปลี่ยนบรรทัด submit เป็น:

```bash
bash scripts/lanta_submit_foundation.sh smoke
bash scripts/lanta_submit_foundation.sh array
bash scripts/lanta_submit_foundation.sh env
```

### แบบ command ปกติ

```bash
cd $HOME/hpc-ignite-hands-on

# ตั้ง project account ให้ตรงกับบัญชีของทีม
export HPC_IGNITE_ACCOUNT=<project-account>
export HPC_IGNITE_PARTITION=compute-devel

# ส่งงาน smoke test ขนาดเล็ก
bash scripts/lanta_submit_foundation.sh smoke

# ดูคิว
squeue -u $USER

# อ่านผลลัพธ์หลังงานจบ
ls -lh logs
find results/foundation -maxdepth 3 -type f | sort
```

ถ้า project ของคุณใช้ account อื่น ให้เปลี่ยน `HPC_IGNITE_ACCOUNT` ก่อน submit เช่น

```bash
export HPC_IGNITE_ACCOUNT=<project-account>
```

ดู copy-paste blocks เพิ่มเติมได้ที่ `docs/COPY_PASTE_ONLY_LABS_TH.md`

## งานที่เตรียมไว้

| คำสั่ง | Slurm job | ใช้สำหรับ |
|---|---|---|
| `bash scripts/lanta_submit_foundation.sh smoke` | `jobs/00-smoke-cpu.sbatch` | ตรวจระบบ, Python, Slurm variables และเขียนผลลัพธ์ JSON |
| `bash scripts/lanta_submit_foundation.sh array` | `jobs/01-array-foundation.sbatch` | ทดลอง job array 4 tasks แบบเบา |
| `bash scripts/lanta_submit_foundation.sh env` | `jobs/02-env-report.sbatch` | เก็บรายงาน module, Python, filesystem และ partition |

## โครงสร้างไฟล์

```text
foundation/lanta-foundation/
├── README.md
├── array_task.py
├── serial_sum.py
├── verify_lanta.py
└── jobs/
    ├── 00-smoke-cpu.sbatch
    ├── 01-array-foundation.sbatch
    └── 02-env-report.sbatch
```

## อ่านผลลัพธ์

หลังจาก job จบ ให้เริ่มจากไฟล์ log:

```bash
ls -lh logs
tail -n +1 logs/hpcig-foundation-*.out
```

แล้วอ่าน result ที่เป็น machine-readable:

```bash
find results/foundation -type f | sort
python -m json.tool results/foundation/<job-id>/system.json
```

## Flow การสอน

1. ให้ผู้เรียนดูว่า source code อยู่ใน `$HOME` แต่ผลลัพธ์ถูกแยกไปใน `results/`
2. เปิด `jobs/00-smoke-cpu.sbatch` แล้วชี้ให้เห็น `#SBATCH` แต่ละบรรทัด
3. ส่งงานด้วย wrapper เพื่อให้ account/partition ปรับได้โดยไม่แก้ไฟล์ job
4. ใช้ `squeue -u $USER` ระหว่างรอ
5. อ่าน log และ JSON หลังงานจบ
6. ส่ง `array` เพื่อให้เห็นว่า experiment หลายชุดไม่จำเป็นต้องเขียน script ซ้ำ

## หมายเหตุสำหรับ LANTA

- ค่า default ของ partition ใน wrapper ตั้งเป็น `compute-devel` เพื่อใช้เป็น smoke test ขนาดเล็กที่จบเร็ว
- ควรตั้ง `HPC_IGNITE_ACCOUNT` ให้ตรงกับ project account ของทีมก่อน submit
- ถ้า partition นี้ไม่เปิดให้ account ของคุณใช้ ให้ลอง `HPC_IGNITE_PARTITION=compute-limited` หรือ `compute`
- งาน foundation ไม่ใช้ GPU และไม่ติดตั้ง dependency เพิ่ม
- เมื่อต่อยอดไปบท GPU/AI ให้ใช้ devel/limited partition ก่อน full run เสมอ
