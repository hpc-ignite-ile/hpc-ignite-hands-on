# LANTA Foundation Lab: งานแรกที่รันได้จริง

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/foundation-visible` โดยตรง

## เป้าหมาย

1. สร้างไฟล์ด้วย heredoc
2. ส่ง Slurm job แบบเห็น script
3. เก็บ JSON environment และค่า pi

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/foundation-visible"
cd "$HOME/hpc-ignite-standalone/foundation-visible"
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

cat > src/foundation_visible.py <<'PYCODE'
from pathlib import Path
import json
import os
import platform
import shutil
import socket
import sys
Path("results").mkdir(exist_ok=True)
info = {
    "python": sys.version.split()[0],
    "executable": sys.executable,
    "host": socket.gethostname(),
    "platform": platform.platform(),
    "cwd": str(Path.cwd()),
    "slurm": {key: os.environ.get(key, "") for key in ["SLURM_JOB_ID", "SLURM_JOB_NAME", "SLURM_CPUS_PER_TASK", "SLURM_SUBMIT_DIR"]},
    "commands": {cmd: shutil.which(cmd) for cmd in ["python", "srun", "sbatch", "cc"]},
}
out = Path("results") / f"environment_{os.environ.get('SLURM_JOB_ID', 'manual')}.json"
out.write_text(json.dumps(info, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(info, indent=2, sort_keys=True))
print(f"result={out}")
from pathlib import Path
Path("results/pi.txt").write_text("pi_smoke=3.14159\n", encoding="utf-8")
print("results/pi.txt")
PYCODE

cat > jobs/foundation-visible.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=foundation-visible
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
python src/foundation_visible.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/foundation-visible.sbatch)
echo "$job_id	foundation-visible	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/foundation-visible_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/foundation-visible"
find results -maxdepth 2 -type f | sort
tail -80 logs/foundation-visible_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
