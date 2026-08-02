# แนวทางเขียน Lab แบบ Heredoc-First

ทุก lab ใหม่ควรมีหัวข้อ `Copy-paste only` เพื่อให้ผู้ใช้เริ่มจาก terminal ได้ทันที เห็นไฟล์จริงที่ตนเองสร้าง และเข้าใจว่าแต่ละ block ทำงานส่วนใดของ workflow

ดูคำอธิบายคำสั่ง Bash, Slurm และ syntax ที่ใช้ใน template ได้ที่ [BASH_COMMAND_REFERENCE_TH.md](BASH_COMMAND_REFERENCE_TH.md)

## หลักการเขียน

1. หนึ่ง code block ทำหนึ่ง semantic task เช่น เตรียม workspace, สร้าง source, สร้าง config, สร้าง Slurm script, ส่งงาน, หรืออ่านผล
2. ก่อน code block ต้องมีคำอธิบายสั้น ๆ ว่า block นี้ทำอะไร ใช้ไฟล์ใด และผู้ใช้ควรตรวจหลักฐานใดหลังรัน
3. หลังสร้างไฟล์สำคัญ ให้ผู้ใช้เปิดอ่านหรือบอกจุดที่ควรสังเกต เช่น output path, parameter, module, และ resource request
4. ส่งงานด้วย `sbatch` จาก `jobs/*.sbatch` ที่สร้างในหน้า hand-on นั้นโดยตรง
5. ใช้ `compute-devel` หรือ `gpu-devel` สำหรับ smoke test ก่อนขยายขนาดงาน
6. เก็บ job id, log, result, config และ version ให้ใช้ตรวจซ้ำได้

## Template แบบ Block สั้น

### ขั้นที่ 1: เตรียม Workspace

block นี้สร้าง path และ folder มาตรฐานของ lab

```bash
mkdir -p "$HOME/hpc-ignite-standalone/<lab-id>"
cd "$HOME/hpc-ignite-standalone/<lab-id>"
mkdir -p configs input jobs logs notes results src
```

### ขั้นที่ 2: ตั้งค่า Account และ Partition

block นี้รับ account และกำหนด partition สำหรับ smoke job

```bash
if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
```

### ขั้นที่ 3: สร้าง Source File

block นี้สร้างโปรแกรมหลัก ผู้ใช้ควรอ่าน output path ก่อนส่งงาน

```bash
cat > src/main.py <<'PY'
from pathlib import Path
import os

Path("results").mkdir(exist_ok=True)
job_id = os.environ.get("SLURM_JOB_ID", "manual")
out = Path(f"results/output_{job_id}.txt")
out.write_text("Hello from HPC Ignite\n", encoding="utf-8")
print(out)
PY
```

### ขั้นที่ 4: สร้าง Slurm Script

block นี้กำหนด resource, module และคำสั่งที่ compute node จะรัน

```bash
cat > jobs/main.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-main
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
```

### ขั้นที่ 5: ส่งงานและอ่าน Log

block นี้ส่งงาน บันทึก job id และพิมพ์คำสั่งตรวจหลักฐาน

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/main.sbatch)
echo "$job_id	hpcig-main	$(date -Is)" >> notes/job-history.tsv
echo "Monitor: squeue -j $job_id"
echo "Log: tail -n +1 logs/hpcig-main_${job_id}.out"
```

## Checkpoint

- เมื่อ submit สำเร็จ ผู้ใช้เห็น job id จาก `sbatch`
- เมื่อ job จบ ผู้ใช้เห็น `COMPLETED` และ `ExitCode` เป็น `0:0` จาก `sacct`
- ใน `logs/` มี stdout/stderr ของ job id นั้น
- ใน `results/` มีไฟล์ output ที่ source file ระบุไว้

## Checklist ก่อน Merge Lab ใหม่

- มีขั้นจาก SSH หรือ link ไปหน้า SSH setup
- ทุก Bash code block มีเป้าหมายเดียวและมีคำอธิบายอยู่ก่อน block
- Bash code block ใน tutorial ควรสั้นพอสำหรับสอนสด โดยตั้งเป้า 60 บรรทัดหรือน้อยกว่า
- ใช้ terminal และ heredoc แทนขั้นตอน `nano`, `vim`, หรือแก้ไฟล์ด้วยมือ
- สร้างไฟล์งานใน workspace ของ lab เช่น `jobs/*.sbatch`, `src/*.py`, `configs/*`, `input/*`
- เขียน `jobs/*.sbatch` ให้ผู้ใช้เปิดอ่านและส่งด้วย `sbatch` โดยตรง
- heredoc marker ใช้ quoted form เช่น `<<'PY'` เพื่อกัน shell expand โค้ด
- ใช้ partition devel/limited เป็นค่าเริ่มต้นสำหรับ smoke test
- รับ account ผ่าน `LANTA_ACCOUNT` หรือค่าที่ผู้ใช้ตั้งเอง
- ใช้ placeholder หรือ fake token สำหรับตัวอย่างด้าน secret/security
- มีคำสั่งดูคิวและดูผลลัพธ์หลัง submit
- ถ้า lab ต้องใช้ package เฉพาะ ให้บอก environment ที่ต้อง activate อย่างชัดเจน
- ถ้าเป็น domain science lab ต้องมี real module-backed smoke workflow อย่างน้อย 1 งาน โดย `jobs/*.sbatch` ใน hand-on page โหลด module จริงโดยตรง เช่น `module load QuantumESPRESSO`, `module load GROMACS`, `module load GDAL`, `module load BLAST+`, `module load Apptainer`, หรือ NetCDF/Python stack; wrapper ใน `slurm/module-loads/` เป็น reference สำหรับผู้สอน
- หัวข้อใหญ่ที่หนักหรือมี license เช่น WRF full run, VASP, Gaussian, Amber, LLM finetuning ให้แยกเป็น instructor demo หรือ optional preflight สำหรับช่วงสาธิต
