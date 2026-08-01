# Copy-Paste Only Labs สำหรับ LANTA

เอกสารนี้ใช้กับผู้เรียนที่ยังไม่ถนัด Linux CLI: ให้ copy-paste เป็นหลัก แต่ไม่ซ่อนงานไว้ใน helper script. Block ที่แปะควรสร้างไฟล์จริงด้วย heredoc แล้วส่งด้วย `sbatch` โดยตรง

## กติกาของ lab แบบ copy-paste only

- หนึ่งกิจกรรมควรมี block หลักที่แปะได้ทันที
- ใช้ `cat > file <<'EOF'` เพื่อสร้างไฟล์ที่ผู้เรียนเปิดอ่านต่อได้
- สร้าง `src/`, `jobs/`, `configs/`, `logs/`, `results/`, `notes/` ให้เห็นชัด
- ส่งงานด้วย `sbatch` โดยตรง ไม่เรียก helper ที่ซ่อนรายละเอียดงาน
- ถ้าต้องใช้ project account ให้ถามผ่าน `read -rp`
- ใช้ `compute-devel` หรือ `gpu-devel` สำหรับ smoke test ก่อน
- หลัง submit ต้องพิมพ์คำสั่ง monitor และผลลัพธ์ที่ควรอ่านต่อ
- หลีกเลี่ยงคำสั่ง destructive เช่น `rm -rf`

## Block A: First Slurm Job จาก booklet

แปะบน login node ของ LANTA:

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

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

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/hello_lanta.sbatch)
echo "$job_id	hello_lanta	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "After completion:"
echo "  sacct -j $job_id --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode"
echo "  tail -50 logs/hello_${job_id}.out"
echo "  cat results/hello_${job_id}.txt"
```

## Block B: ส่ง Python script ใน repo โดยตรง

ใช้เมื่อผู้เรียน clone repo แล้วและต้องการส่งตัวอย่าง Python หนึ่งไฟล์เข้า Slurm. เปลี่ยนแค่ `LAB_SCRIPT` ได้

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-foundation/lanta-foundation/serial_sum.py}"

mkdir -p jobs logs results/python-labs

cat > jobs/run_python_lab.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-python-lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi
mkdir -p "results/python-labs/${SLURM_JOB_ID}"
echo "script=${LAB_SCRIPT}"
python "$LAB_SCRIPT" | tee "results/python-labs/${SLURM_JOB_ID}/output.txt"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --export=ALL,LAB_SCRIPT="$LAB_SCRIPT" --parsable jobs/run_python_lab.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Results: find results/python-labs/${job_id} -type f -maxdepth 2 -print"
```

## Block C: GPU Check

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"

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

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --parsable jobs/gpu_check.sbatch)
echo "Submitted GPU check: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/gpu_${job_id}.out"
```
