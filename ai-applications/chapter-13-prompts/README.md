# บทที่ 13: Prompt Engineering

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/ai-prompts` โดยตรง

## เป้าหมาย

1. สร้าง prompt scaffold เป็นไฟล์
2. สร้าง checklist CSV จาก prompt review
3. ฝึกแยก prompt, input และ result

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/ai-prompts"
cd "$HOME/hpc-ignite-standalone/ai-prompts"
mkdir -p configs input jobs logs notes results src prompts

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

cat > src/prompt_scaffold.py <<'PYCODE'
from pathlib import Path
Path("prompts").mkdir(exist_ok=True); Path("results").mkdir(exist_ok=True)
prompt = """[System]
คุณเป็นผู้ช่วยตรวจ Slurm script สำหรับ training บน LANTA

[Task]
ประเมิน resource request ของ job สั้น ๆ โดยดู account, partition, walltime, output log และ reproducibility
"""
Path("prompts/slurm-review-th.txt").write_text(prompt, encoding="utf-8")
report = """checklist,status
account,needs user value
partition,compute-devel for smoke
walltime,short
logs,stdout and stderr separated
reproducibility,record module list and command versions
"""
Path("results/slurm_prompt_check.csv").write_text(report, encoding="utf-8")
print("prompts/slurm-review-th.txt"); print("results/slurm_prompt_check.csv")
PYCODE

cat > jobs/prompt-scaffold.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=prompt-scaffold
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
python src/prompt_scaffold.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/prompt-scaffold.sbatch)
echo "$job_id	prompt-scaffold	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/prompt-scaffold_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/ai-prompts"
cat prompts/slurm-review-th.txt
cat results/slurm_prompt_check.csv
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
