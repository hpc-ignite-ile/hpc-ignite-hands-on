# Copy-Paste Only Labs สำหรับ LANTA

เอกสารนี้ใช้กับผู้ใช้เริ่มต้น Linux CLI: ให้ copy-paste เป็นหลัก พร้อมเห็นไฟล์จริงและคำสั่งที่ใช้ส่งงาน. แต่ละ block ควรทำหนึ่ง semantic task เช่น เตรียม workspace, สร้าง source, สร้าง Slurm script, ส่งงาน, หรืออ่านผล

ดูคำอธิบายคำสั่งและ syntax ที่ใช้ใน block ได้ที่ [BASH_COMMAND_REFERENCE_TH.md](BASH_COMMAND_REFERENCE_TH.md)

## กติกาของ lab แบบ copy-paste only

- หนึ่ง code block ควรมีหนึ่งเป้าหมายหลัก และมีคำอธิบายก่อน block
- ใช้ `cat > file <<'EOF'` เพื่อสร้างไฟล์ที่ผู้ใช้เปิดอ่านต่อได้
- สร้าง `src/`, `jobs/`, `configs/`, `logs/`, `results/`, `notes/` ให้เห็นชัด
- ส่งงานด้วย `sbatch` โดยตรง พร้อมแสดงรายละเอียดใน `jobs/*.sbatch`
- ถ้าต้องใช้ project account ให้ถามผ่าน `read -rp` แล้วส่งด้วย `sbatch -A "$LANTA_ACCOUNT"`
- ใช้ `compute-devel` หรือ `gpu-devel` สำหรับ smoke test ก่อน
- หลัง submit ต้องพิมพ์คำสั่ง monitor และผลลัพธ์ที่ควรอ่านต่อ
- ใช้คำสั่งลบไฟล์เฉพาะใน instructor demo หรือ cleanup ที่อธิบายผลกระทบชัดเจน

## Block A: First Slurm Job จาก booklet

แปะบน login node ของ LANTA:

### ขั้นย่อย 1: เตรียม workspace และตัวแปร

block นี้เตรียม path, folder และตัวแปรที่คำสั่งถัดไปต้องใช้

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
```

### ขั้นย่อย 2: สร้าง source code `src/hello_lanta.py`

block นี้สร้างไฟล์หนึ่งไฟล์ เพื่อให้ผู้ใช้อ่านเนื้อหาและแก้ค่าที่เกี่ยวข้องก่อนรันงาน

```bash
cat > src/hello_lanta.py <<'PY'
from pathlib import Path
import os
import platform
import time

Path("results").mkdir(exist_ok=True)
job_id = os.environ.get("SLURM_JOB_ID", "manual")
out = Path("results") / f"hello_{job_id}.txt"
out.write_text(
    "\n".join([
        f"job_id={job_id}",
        f"host={platform.node()}",
        f"user={os.environ.get('USER', 'unknown')}",
        f"submit_dir={os.environ.get('SLURM_SUBMIT_DIR', os.getcwd())}",
        f"time={time.strftime('%Y-%m-%d %H:%M:%S')}",
    ]) + "\n",
    encoding="utf-8",
)
print(out)
PY
```

### ขั้นย่อย 3: สร้าง Slurm script `jobs/hello_lanta.sbatch`

block นี้โฟกัสเฉพาะ resource, module และคำสั่งที่ compute node จะรัน

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

### ขั้นย่อย 4: ส่งงานเข้า Slurm

block นี้ส่ง job script ที่สร้างไว้และบอกวิธีอ่าน job id กับ log

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

✅ เมื่อสำเร็จ ผู้ใช้จะได้ job id จาก `sbatch`, log ใน `logs/hello_<jobid>.out`, และผลลัพธ์ใน `results/hello_<jobid>.txt`

## Block B: GPU Check

### ขั้นย่อย 1: เตรียม workspace และตัวแปร

block นี้เตรียม path, folder และตัวแปรที่คำสั่งถัดไปต้องใช้

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"
```

### ขั้นย่อย 2: สร้าง Slurm script `jobs/gpu_check.sbatch`

block นี้โฟกัสเฉพาะ resource, module และคำสั่งที่ compute node จะรัน

```bash
cat > jobs/gpu_check.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=gpu_check
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:10:00
#SBATCH --output=logs/gpu_%j.out
#SBATCH --error=logs/gpu_%j.err

set -euo pipefail
module purge
module load Mamba/23.11.0-0
conda activate pytorch-2.2.2
export PATH="/lustrefs/disk/modules/easybuild/software/Mamba/23.11.0-0/envs/pytorch-2.2.2/bin:${PATH}"
cd "$SLURM_SUBMIT_DIR"
nvidia-smi
python - <<'PY'
import torch

print("torch", torch.__version__)
print("cuda_version", torch.version.cuda)
print("cuda_available", torch.cuda.is_available())
print("gpu_count", torch.cuda.device_count())
if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
    raise SystemExit("PyTorch cannot see the allocated GPU")

x = torch.randn(2000, 2000, device="cuda")
y = x @ x
torch.cuda.synchronize()
print("gpu_name", torch.cuda.get_device_name(0))
print("matrix_sum", float(y.sum().cpu()))
print("status", "ok")
PY
SLURM
```

### ขั้นย่อย 3: ส่งงานเข้า Slurm

block นี้ส่ง job script ที่สร้างไว้และบอกวิธีอ่าน job id กับ log

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_GPU_PARTITION" --parsable jobs/gpu_check.sbatch)
echo "Submitted GPU check: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/gpu_${job_id}.out"
```

✅ เมื่อสำเร็จ log ต้องมีผลจาก `nvidia-smi`, ค่า `cuda_available True`, และข้อความ `status ok`

## Block C: Data Summary And Resource Logs

รันหลัง job จบ เพื่อรวมหลักฐานข้อมูลและทรัพยากรไว้ใน `notes/`.

### ขั้นย่อย 1: เตรียม workspace และตัวแปร

block นี้เตรียม path, folder และตัวแปรที่คำสั่งถัดไปต้องใช้

```bash
cd "$HOME/lanta-experience"
mkdir -p notes results

RUN_STAMP=$(date +%Y%m%d-%H%M%S)
DATA_LOG="notes/data-summary-${RUN_STAMP}.txt"
SPENT_LOG="notes/resource-spent-${RUN_STAMP}.tsv"
```

### ขั้นย่อย 2: ตรวจหลักฐาน

block นี้อ่านหลักฐานหลังรันเพื่อใช้ตัดสินว่า workflow เดินครบ

```bash
{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo
    echo "job history"
    cat notes/job-history.tsv 2>/dev/null || echo "notes/job-history.tsv not found"
    echo
    echo "result files"
    find results -maxdepth 2 -type f | sort
    echo
    echo "sensor summary"
    if [ -f results/sensor_summary.csv ]; then
        cat results/sensor_summary.csv
    else
        echo "missing results/sensor_summary.csv"
    fi
    echo
    echo "checksums"
    sha256sum input/sensor.csv results/sensor_summary.csv 2>/dev/null || true
    sha256sum results/hello_*.txt results/pi_*.txt results/diffusion_*.csv 2>/dev/null || true
} | tee "$DATA_LOG"
```

### ขั้นย่อย 3: ตรวจหลักฐาน

block นี้อ่านหลักฐานหลังรันเพื่อใช้ตัดสินว่า workflow เดินครบ

```bash
if [ -s notes/job-history.tsv ]; then
    JOB_IDS=$(cut -f1 notes/job-history.tsv | paste -sd, -)
    sacct -j "$JOB_IDS" --format=JobID,JobName%24,Partition,Account,State,ExitCode,Elapsed,AllocCPUS,ReqMem,MaxRSS,AllocTRES%80 -P > "$SPENT_LOG"
else
    echo "No job history yet" > "$SPENT_LOG"
fi
```

### ขั้นย่อย 4: ตรวจหลักฐาน

block นี้อ่านหลักฐานหลังรันเพื่อใช้ตัดสินว่า workflow เดินครบ

```bash
sbalance 2>&1 | tee "notes/balance-${RUN_STAMP}.txt" || true
sbill 2>&1 | tee "notes/bill-${RUN_STAMP}.txt" || true

echo "Data summary: $DATA_LOG"
echo "Resource spent: $SPENT_LOG"
head -30 "$SPENT_LOG"
```

✅ เมื่อสำเร็จ ผู้ใช้จะได้ไฟล์สรุปข้อมูลใน `notes/data-summary-<เวลา>.txt` และไฟล์ทรัพยากรใน `notes/resource-spent-<เวลา>.tsv`

## Block D: Real Mini Workflow แบบ Standalone

ตัวอย่างนี้สร้าง environment audit ขนาดเล็กจากหน้าเอกสารโดยตรง แล้วส่งเข้า `compute-devel`:

### ขั้นย่อย 1: เตรียม workspace และตัวแปร

block นี้เตรียม path, folder และตัวแปรที่คำสั่งถัดไปต้องใช้

```bash
mkdir -p "$HOME/hpc-ignite-standalone/environment-audit"
cd "$HOME/hpc-ignite-standalone/environment-audit"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
```

### ขั้นย่อย 2: สร้าง source code `src/environment_audit.py`

block นี้สร้างไฟล์หนึ่งไฟล์ เพื่อให้ผู้ใช้อ่านเนื้อหาและแก้ค่าที่เกี่ยวข้องก่อนรันงาน

```bash
cat > src/environment_audit.py <<'PY'
from pathlib import Path
import json
import os
import platform
import sys

Path("results").mkdir(exist_ok=True)
summary = {
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "job_id": os.environ.get("SLURM_JOB_ID", "manual"),
    "submit_dir": os.environ.get("SLURM_SUBMIT_DIR", ""),
}
out = Path("results") / f"environment_{summary['job_id']}.json"
out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
PY
```

### ขั้นย่อย 3: สร้าง Slurm script `jobs/environment_audit.sbatch`

block นี้โฟกัสเฉพาะ resource, module และคำสั่งที่ compute node จะรัน

```bash
cat > jobs/environment_audit.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=env-audit
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
python src/environment_audit.py | tee "results/output_${SLURM_JOB_ID}.txt"
SLURM
```

### ขั้นย่อย 4: ส่งงานเข้า Slurm

block นี้ส่ง job script ที่สร้างไว้และบอกวิธีอ่าน job id กับ log

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/environment_audit.sbatch)
echo "$job_id	environment_audit	$(date -Is)" >> notes/job-history.tsv
echo "Submitted environment audit: $job_id"
echo "Read: tail -80 logs/env-audit_${job_id}.out"
```

✅ เมื่อสำเร็จ ผู้ใช้ควรอ่าน log ของ job นั้นก่อน แล้วเปิด `results/environment_<jobid>.json`
