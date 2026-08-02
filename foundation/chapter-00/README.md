# บทที่ 0: HPC 101 - บทนำสู่การประมวลผลสมรรถนะสูง

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

Chapter 0: Introduction to High-Performance Computing

## วัตถุประสงค์การเรียนรู้

1. อธิบายความหมายและความสำคัญของ HPC
2. เปรียบเทียบขีดความสามารถของอุปกรณ์ประมวลผลประเภทต่าง ๆ
3. วิเคราะห์หลักการทำงานแบบขนานและกฎของแอมดาห์ล
4. ระบุส่วนประกอบหลักของระบบ LANTA

## โครงสร้างไฟล์

```
chapter-00/
├── README.md                    # ไฟล์นี้
├── hello_lanta.py               # ตัวอย่างแรก - ทดสอบการเชื่อมต่อ
├── hello_lanta.sbatch           # SLURM script สำหรับ hello_lanta.py
├── rice_production_analysis.py  # ตัวอย่างการวิเคราะห์ผลผลิตข้าว
├── amdahl_speedup.py            # แบบฝึกหัด: กฎของแอมดาห์ล
├── wrf_chem_airquality.sbatch   # SLURM script สำหรับ WRF-Chem
└── exercises/
    └── amdahl_exercise.py       # แบบฝึกหัดให้นักศึกษาเติม
```

## การใช้งาน

### 1. Hello LANTA

```bash
# Login to LANTA
ssh username@lanta.nstda.or.th

# Clone repo เมื่อเริ่มครั้งแรก
cd $HOME
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on/foundation/chapter-00

# Run interactively
source ../../slurm/module-loads/base.sh
python hello_lanta.py

# Or submit as job
sbatch hello_lanta.sbatch
```

ถ้าต้องการ flow ที่ทดสอบกับ LANTA ปัจจุบันแล้ว แนะนำเริ่มจากบทใหม่:

```bash
cd $HOME/hpc-ignite-hands-on
sed -n '1,180p' lanta-experience/01-first-slurm-job.md
```

### 2. Rice Production Analysis

```bash
# Run locally (no HPC needed)
python rice_production_analysis.py
```

### 3. Amdahl's Law Exercise

```bash
# View solution
python amdahl_speedup.py

# Or complete the exercise yourself
python exercises/amdahl_exercise.py
```

### 4. WRF-Chem Air Quality (Advanced)

```bash
# This requires WRF-Chem module and data
# For demonstration only
sbatch wrf_chem_airquality.sbatch
```

## แนวคิดหลัก

### กฎของแอมดาห์ล (Amdahl's Law)

$$S = \frac{1}{(1-P) + \frac{P}{N}}$$

- $S$ = Speedup
- $P$ = สัดส่วนงานที่ทำแบบขนานได้
- $N$ = จำนวนหน่วยประมวลผล

### ระบบ LANTA

| รายการ | ข้อมูล |
|--------|-------|
| ความเร็วสูงสุด | 8.15 PetaFLOPS |
| CPU Nodes | 160 nodes (20,480 cores) |
| GPU Nodes | 176 nodes (704 NVIDIA A100) |
| Storage | 10 PB Lustre |

## เอกสารอ้างอิง

- [Curriculum Book - Chapter 0](https://github.com/wdiazcarballo/hpc-curriculum/blob/main/docs/curriculum-book/chapters/chapter-00-hpc-101.md)
- [LANTA User Guide](https://docs.lanta.nstda.or.th)

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-foundation/chapter-00/amdahl_speedup.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=foundation/chapter-00/amdahl_speedup.py`
