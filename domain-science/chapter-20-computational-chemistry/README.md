# บทที่ 20: เคมีคำนวณ

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/chemistry-preflight` โดยตรง

## เป้าหมาย

1. คำนวณ molecular mass ขนาดเล็ก
2. บันทึก result เป็น JSON
3. ใช้เป็น preflight ก่อน software chemistry จริง

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/chemistry-preflight"
cd "$HOME/hpc-ignite-standalone/chemistry-preflight"
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

cat > src/molecular_mass.py <<'PYCODE'
from pathlib import Path
import json
Path("results").mkdir(exist_ok=True)
weights = {"H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999}
molecules = {"water": {"H": 2, "O": 1}, "methane": {"C": 1, "H": 4}, "glycine": {"C": 2, "H": 5, "N": 1, "O": 2}}
summary = {name: sum(weights[e] * c for e, c in formula.items()) for name, formula in molecules.items()}
out = Path("results/molecular_mass.json"); out.write_text(json.dumps(summary, indent=2), encoding="utf-8"); print(json.dumps(summary, indent=2))
PYCODE

cat > jobs/chem-mass.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=chem-mass
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
python src/molecular_mass.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM

job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/chem-mass.sbatch)
echo "$job_id	chem-mass	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/chem-mass_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/chemistry-preflight"
cat results/molecular_mass.json
tail -50 logs/chem-mass_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
