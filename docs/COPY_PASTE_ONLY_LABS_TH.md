# Copy-Paste Only Labs สำหรับ LANTA

เอกสารนี้ทำให้ผู้เรียนที่ยังไม่ถนัด Linux CLI สามารถเริ่มได้ด้วยการ copy-paste block เดียว
โดยใช้ heredoc เช่น `cat > file <<'EOF'` เพื่อสร้างไฟล์และส่งงาน Slurm โดยไม่ต้องเปิด editor

## กติกาของ lab แบบ copy-paste only

- หนึ่ง lab ต้องมี block เดียวที่ copy แล้ว paste ได้ทันที
- ถ้าต้องใช้ project account ให้ถามผ่าน `read -rp` แทนการให้ผู้เรียนแก้ไฟล์
- ใช้ `compute-devel` หรือ `gpu-devel` สำหรับ smoke test ก่อน
- สร้างไฟล์ด้วย heredoc และใช้ marker แบบ quoted เช่น `<<'PY'` หรือ `<<'SBATCH'`
- หลัง submit ต้องพิมพ์คำสั่ง monitor และผลลัพธ์ที่ควรอ่านต่อ
- หลีกเลี่ยงคำสั่ง destructive เช่น `rm -rf`

## Block A: รัน foundation lab จาก repo ที่ clone แล้ว

ใช้ block นี้เมื่อผู้เรียนมี repo อยู่ที่ `$HOME/hpc-ignite-hands-on`

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
bash scripts/lanta_submit_foundation.sh array
bash scripts/lanta_submit_foundation.sh env

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

## Block B: สร้าง foundation smoke lab แบบ standalone ด้วย heredoc

ใช้ block นี้เมื่ออยากสอนแนวคิด heredoc โดยไม่ต้องเปิด editor และไม่ต้องพึ่งไฟล์ใน repo

```bash
cat > /tmp/hpc_ignite_standalone_foundation.sh <<'BASH'
#!/bin/bash
set -euo pipefail

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm, เช่น pv915002: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

LAB_DIR="$HOME/hpc-ignite-copy-paste/foundation-smoke"
mkdir -p "$LAB_DIR/logs" "$LAB_DIR/results"
cd "$LAB_DIR"

cat > verify_lanta.py <<'PY'
#!/usr/bin/env python3
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
    "python_executable": os.sys.executable,
    "working_directory": str(Path.cwd()),
    "slurm": {key: os.environ.get(key, "N/A") for key in slurm_keys},
}

print("HPC Ignite standalone foundation smoke test")
print(json.dumps(info, ensure_ascii=False, indent=2))
Path("results").mkdir(exist_ok=True)
Path("results/system.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

cat > serial_sum.py <<'PY'
#!/usr/bin/env python3
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

cat > run.sbatch <<'SBATCH'
#!/bin/bash
#SBATCH --job-name=hpcig-copy-foundation
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=512M
#SBATCH --time=00:03:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

module purge
module load cray-python/3.10.10 2>/dev/null || true
module load Mamba/23.11.0-0 2>/dev/null || true

python verify_lanta.py
python serial_sum.py | tee "results/serial_sum_${SLURM_JOB_ID}.txt"
SBATCH

job_id=$(sbatch -A "$HPC_IGNITE_ACCOUNT" -p "$HPC_IGNITE_PARTITION" --parsable run.sbatch)

echo "Submitted job: $job_id"
echo "ดูคิว:"
echo "  squeue -j $job_id"
echo "ดู log หลังงานจบ:"
echo "  tail -n +1 $LAB_DIR/logs/hpcig-copy-foundation_${job_id}.out"
BASH

bash /tmp/hpc_ignite_standalone_foundation.sh
```

## Block C: เมนูเลือก Python lab จาก repo

ใช้ block นี้เมื่อผู้เรียน clone repo แล้ว แต่อยากเลือก lab โดยไม่ต้องพิมพ์ path เอง

```bash
cat > /tmp/hpc_ignite_lab_menu.sh <<'BASH'
#!/bin/bash
set -euo pipefail

REPO="$HOME/hpc-ignite-hands-on"
cd "$REPO"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm, เช่น pv915002: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

mapfile -t LABS < <(
    find foundation core-hpc domain-science ai-applications \
        -maxdepth 2 -type f -name '*.py' \
        ! -path '*/__pycache__/*' | sort
)

echo "เลือก lab ที่ต้องการส่งเข้า Slurm:"
select lab in "${LABS[@]}"; do
    if [ -n "${lab:-}" ]; then
        bash scripts/lanta_submit_python_lab.sh "$lab"
        break
    fi
    echo "กรุณาเลือกหมายเลขจากรายการ"
done
BASH

bash /tmp/hpc_ignite_lab_menu.sh
```

หมายเหตุ: block C เหมาะกับ lab ที่เป็น Python script และ dependency พร้อมใน environment แล้ว
สำหรับ lab ที่ต้องใช้ GPU, MPI หรือ package เฉพาะ ควรมี heredoc block เฉพาะของบทนั้นเพิ่มอีกชุด
