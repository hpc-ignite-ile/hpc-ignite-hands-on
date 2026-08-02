# แนวทางเขียน Lab แบบ Heredoc-First

ทุก lab ใหม่ควรมีหัวข้อ `Copy-paste only` เพื่อให้ผู้ใช้เริ่มได้โดยไม่ต้องเปิด editor แต่ยังเห็นไฟล์ที่ตนเองสร้างจริง ไม่ใช้ helper script ที่ซ่อนรายละเอียดงาน

## โครงสร้างที่แนะนำ

1. เปิดด้วยเป้าหมายสั้น ๆ ว่าผู้ใช้จะทำอะไร
2. ให้ copy-paste block ก่อนคำอธิบายละเอียด
3. ใน block ให้สร้างไฟล์ด้วย heredoc
4. ส่งงานด้วย `sbatch` โดยตรง
5. พิมพ์คำสั่งดูคิวและดูผลลัพธ์
6. หลัง block ให้บอก checkpoint ว่าควรเห็นไฟล์หรือข้อความใด
7. ถ้ามี error ให้บอกคำสั่งแรกที่ควรตรวจ เช่น `tail`, `squeue`, `sacct`, หรือ `module avail`

## Template

```bash
mkdir -p "$HOME/lanta-experience/<lab-id>"
cd "$HOME/lanta-experience/<lab-id>"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

cat > src/main.py <<'PY'
from pathlib import Path
import os

Path("results").mkdir(exist_ok=True)
job_id = os.environ.get("SLURM_JOB_ID", "manual")
Path(f"results/output_{job_id}.txt").write_text("Hello from HPC Ignite\n", encoding="utf-8")
print(f"results/output_{job_id}.txt")
PY

cat > jobs/main.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-<lab-id>
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
python src/main.py
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/main.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Output : tail -n +1 logs/hpcig-<lab-id>_${job_id}.out"
```

หลัง code block ให้เขียน checkpoint แบบสั้น:

- ✅ เมื่อสำเร็จ ผู้ใช้จะเห็น job id จาก `sbatch`
- ✅ เมื่อ job จบ ผู้ใช้จะเห็นไฟล์ `results/output_<jobid>.txt`
- ⚠️ หาก submit ไม่ผ่าน ให้ตรวจ `LANTA_ACCOUNT` และ partition ด้วย `sinfo`

## Checklist ก่อน merge lab ใหม่

- มีหัวข้อ `Copy-paste only`
- ไม่มีขั้นตอนที่ต้อง `nano`, `vim`, หรือแก้ไฟล์ด้วยมือ
- ไม่สร้าง `/tmp/*.sh` แล้วสั่ง `bash /tmp/...`
- ไม่เรียก helper submit script แทนการเขียน `jobs/*.sbatch`
- heredoc marker ใช้ quoted form เช่น `<<'PY'` เพื่อกัน shell expand โค้ด
- ใช้ partition devel/limited เป็นค่าเริ่มต้นสำหรับ smoke test
- ไม่ hard-code account project ของผู้สอน
- ไม่ hard-code token, password, SSH key หรือ secret
- มีคำสั่งดูคิวและดูผลลัพธ์หลัง submit
- ถ้า lab ต้องใช้ package เฉพาะ ให้บอก environment ที่ต้อง activate อย่างชัดเจน
- ถ้าเป็น domain science lab ต้องมี real module-backed smoke workflow อย่างน้อย 1 งาน เช่น `jobs/*.sbatch` ที่ source `slurm/module-loads/qe.sh`, `gromacs.sh`, `geodata.sh`, `bio.sh`, `netcdf-python.sh`, หรือ `apptainer.sh`
- หัวข้อใหญ่ที่หนักหรือมี license เช่น WRF full run, VASP, Gaussian, Amber, LLM finetuning ให้แยกเป็น instructor demo หรือ optional preflight ไม่ใช่ default live exercise
