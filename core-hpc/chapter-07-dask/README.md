# บทที่ 7: Distributed Python ด้วย Dask

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/core-dask` โดยตรง

## เป้าหมาย

1. สร้าง task graph ขนาดเล็ก
2. รันด้วย Dask threads เมื่อ package พร้อม
3. บันทึก fallback summary สำหรับตรวจ environment

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/core-dask"
cd "$HOME/hpc-ignite-standalone/core-dask"
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

cat > src/dask_shape.py <<'PYCODE'
from pathlib import Path
import json
import math
Path("results").mkdir(exist_ok=True)
try:
    import dask
    from dask import delayed, compute
    tasks = [delayed(lambda i: sum(math.sin(j / 1000) for j in range(i * 1000, (i + 1) * 1000)))(i) for i in range(16)]
    values = compute(*tasks, scheduler="threads")
    summary = {"dask_available": True, "dask_version": dask.__version__, "task_count": len(values), "total": sum(values)}
except Exception as exc:
    values = [sum(math.sin(j / 1000) for j in range(i * 1000, (i + 1) * 1000)) for i in range(16)]
    summary = {"dask_available": False, "fallback_reason": repr(exc), "task_count": len(values), "total": sum(values)}
out = Path("results/dask_shape_summary.json"); out.write_text(json.dumps(summary, indent=2), encoding="utf-8"); print(json.dumps(summary, indent=2))
PYCODE

cat > jobs/dask-shape.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=dask-shape
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load Mamba/23.11.0-0 2>/dev/null || module load cray-python/3.10.10 2>/dev/null || true
conda activate netcdf-py39 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/dask_shape.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/dask-shape.sbatch)
echo "$job_id	dask-shape	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/dask-shape_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/core-dask"
cat results/dask_shape_summary.json
tail -60 logs/dask-shape_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
