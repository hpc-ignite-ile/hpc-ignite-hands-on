# 01 First Slurm Job

สร้าง Python script และ Slurm job script ด้วย heredoc แล้วส่งด้วย `sbatch` โดยตรง.

## Copy-Paste

```bash
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
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

เมื่อส่งด้วย `sbatch` งานจะไม่รันบน login node แต่เข้า queue เพื่อให้ Slurm จัดไปยัง compute node ไฟล์ log จะถูกเก็บใน `logs/` และผลลัพธ์ของ Python จะถูกเก็บใน `results/`

เมื่อสำเร็จ `sbatch` จะคืน job id ให้ผู้ใช้ จากนั้นใช้ `squeue -j <job-id>` เพื่อตรวจสถานะ และใช้ `sacct` หลังงานจบเพื่อตรวจว่าเป็น `COMPLETED` หาก submit ไม่ผ่านให้ตรวจ `LANTA_ACCOUNT` หาก job ค้างให้ดู reason ใน `squeue` หาก log แจ้งว่าไม่มี Python ให้ตรวจ `module avail python` และอย่ารัน `.sbatch` ด้วย `bash` เพราะงาน Slurm ต้องส่งผ่าน `sbatch`

## Modify

เปลี่ยนข้อความที่เขียนใน `src/hello_lanta.py` หรือเปลี่ยน `--time` ใน `jobs/hello_lanta.sbatch` แล้วส่งใหม่.
