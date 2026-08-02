# บทที่ 30: Carbon Footprint และ HPC

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-carbon` โดยตรง

## เป้าหมาย

1. รัน workload CPU สั้น
2. บันทึก proxy metric ของงาน
3. ใช้ sacct ต่อกับ elapsed และ CPU allocation

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-carbon"
cd "$HOME/hpc-ignite-standalone/ai-carbon"
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

cat > src/carbon_proxy.py <<'PYCODE'
from pathlib import Path
import json, math, os
Path("results").mkdir(exist_ok=True)
total = sum(math.sqrt(i) for i in range(1, 200000))
summary = {"job_id": os.environ.get("SLURM_JOB_ID", "manual"), "cpu_count": os.environ.get("SLURM_CPUS_PER_TASK", "1"), "work_units": 199999, "checksum": round(total, 4), "resource_note": "combine this file with sacct elapsed and AllocCPUS"}
out = Path("results/carbon_proxy.json"); out.write_text(json.dumps(summary, indent=2), encoding="utf-8"); print(json.dumps(summary, indent=2))
PYCODE

cat > jobs/carbon-proxy.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=carbon-proxy
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
python src/carbon_proxy.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/carbon-proxy.sbatch)
echo "$job_id	carbon-proxy	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/carbon-proxy_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/ai-carbon"
cat results/carbon_proxy.json
JOB_IDS=$(cut -f1 notes/job-history.tsv | paste -sd, -)
sacct -j "$JOB_IDS" --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
