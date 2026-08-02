# LANTA Foundation Lab: งานแรกที่รันได้จริง

บทนี้เป็นฐานสำหรับผู้ใช้ HPC Ignite ที่ต้องการเริ่มจากศูนย์บน LANTA โดยเน้นลำดับเดียวกับ booklet: login, files, modules, job script, monitoring, results และ next experiment.

แนวทางใหม่คือ copy-paste เป็นหลัก แต่ไม่ใช้ helper ที่ซ่อนรายละเอียดงาน. ผู้ใช้จะสร้างไฟล์ `.py` และ `.sbatch` ด้วย heredoc แล้วส่งด้วย `sbatch` โดยตรง

## สิ่งที่จะได้ฝึก

1. ตรวจว่าอยู่บน login node หรือ compute node
2. อ่านตัวแปร Slurm เช่น `SLURM_JOB_ID`, `SLURM_CPUS_PER_TASK`, `SLURM_SUBMIT_DIR`
3. โหลด environment พื้นฐานด้วย Lmod
4. สร้าง Slurm job script ด้วย heredoc
5. ส่งงาน batch ด้วย `sbatch`
6. ติดตามงานด้วย `squeue`
7. อ่านผลลัพธ์ใน `logs/` และ `results/`

## Copy-Paste Only บน LANTA

แปะ block นี้ใน terminal บน LANTA:

```bash
mkdir -p "$HOME/lanta-experience/foundation"
cd "$HOME/lanta-experience/foundation"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

cat > src/verify_lanta.py <<'PY'
import json
import os
import platform
import socket
from datetime import datetime, timezone
from pathlib import Path

slurm_keys = [
    "SLURM_JOB_ID",
    "SLURM_JOB_NAME",
    "SLURM_SUBMIT_DIR",
    "SLURM_NODELIST",
    "SLURM_NTASKS",
    "SLURM_CPUS_PER_TASK",
    "SLURM_JOB_PARTITION",
    "SLURM_JOB_ACCOUNT",
]

info = {
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "hostname": socket.gethostname(),
    "python_version": platform.python_version(),
    "user": os.environ.get("USER", "unknown"),
    "working_directory": str(Path.cwd()),
    "slurm": {key: os.environ.get(key, "N/A") for key in slurm_keys},
}

print("HPC Ignite foundation smoke test")
print(json.dumps(info, ensure_ascii=False, indent=2))
Path("results").mkdir(exist_ok=True)
Path(f"results/system_{os.environ.get('SLURM_JOB_ID', 'manual')}.json").write_text(
    json.dumps(info, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
PY

cat > src/serial_sum.py <<'PY'
import math
import time

n = 200000
step = 1.0 / n
start = time.perf_counter()
total = 0.0
for i in range(n):
    x = (i + 0.5) * step
    total += math.sqrt(1.0 - x * x)
pi_value = 4.0 * step * total
elapsed = time.perf_counter() - start

print(f"n          : {n}")
print(f"pi estimate: {pi_value:.12f}")
print(f"abs error  : {abs(math.pi - pi_value):.6e}")
print(f"elapsed sec: {elapsed:.4f}")
PY

cat > jobs/foundation_smoke.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-foundation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:03:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"

echo "Job ID : ${SLURM_JOB_ID}"
echo "Node   : $(hostname)"
python src/verify_lanta.py
python src/serial_sum.py | tee "results/serial_sum_${SLURM_JOB_ID}.txt"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/foundation_smoke.sbatch)
echo "$job_id	foundation_smoke	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "After completion:"
echo "  tail -50 logs/hpcig-foundation_${job_id}.out"
echo "  find results -type f | sort"
```

## Repo Reference Files

ไฟล์ในโฟลเดอร์นี้ยังเก็บตัวอย่าง reusable สำหรับทดสอบและสอน:

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

ถ้าจะใช้ไฟล์ที่เตรียมไว้ใน repo โดยตรง ให้ส่งด้วย `sbatch` เอง:

```bash
cd "$HOME/hpc-ignite-hands-on"
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi

sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" foundation/lanta-foundation/jobs/00-smoke-cpu.sbatch
```

## Flow การสอน

1. ให้ผู้ใช้แปะ heredoc block และดูว่าเกิด `src/` กับ `jobs/`
2. เปิด `jobs/foundation_smoke.sbatch` แล้วชี้ `#SBATCH` แต่ละบรรทัด
3. ส่งงานด้วย `sbatch` โดยตรง
4. ใช้ `squeue -j <job-id>` ระหว่างรอ
5. อ่าน log และ result หลังงานจบ
6. เปลี่ยนจำนวนงานหรือตัวอย่าง Python เพียงเล็กน้อย แล้วส่งซ้ำ

## หมายเหตุสำหรับ LANTA

- เริ่มจาก `compute-devel` สำหรับ smoke test ขนาดเล็ก
- ถ้า account ต้องระบุ project ให้ตั้ง `LANTA_ACCOUNT` ก่อน submit
- งาน foundation ไม่ใช้ GPU และไม่ติดตั้ง dependency เพิ่ม
- เมื่อต่อยอดไปบท GPU/AI ให้ใช้ `gpu-devel` ก่อน full run เสมอ
