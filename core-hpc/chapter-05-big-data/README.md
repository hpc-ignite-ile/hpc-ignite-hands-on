# บทที่ 5: การประมวลผล Big Data

Chapter 5: Big Data Processing

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ 5V ของ Big Data
2. ใช้ Pandas สำหรับข้อมูลขนาดกลาง
3. ประยุกต์ Chunk Processing สำหรับข้อมูลใหญ่
4. ใช้ Out-of-Core Computing

## โครงสร้างไฟล์

```
chapter-05-big-data/
├── README.md
├── pandas_basics.py         # Pandas fundamentals
├── chunk_processing.py      # Processing large files in chunks
├── memory_efficient.py      # Memory-efficient techniques
├── generate_large_data.py   # Generate test data
└── sbatch/
    └── big_data_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba env create -f ../../environments/base.yaml
mamba activate hpc-ignite-base

# Generate sample data
python generate_large_data.py --size 1000000

# Run examples
python pandas_basics.py
python chunk_processing.py

# On SLURM
sbatch sbatch/big_data_job.sbatch
```

## แนวคิดหลัก: 5V ของ Big Data

1. **Volume** - ปริมาณข้อมูล
2. **Velocity** - ความเร็วในการสร้างข้อมูล
3. **Variety** - ความหลากหลายของข้อมูล
4. **Veracity** - ความถูกต้องของข้อมูล
5. **Value** - มูลค่าของข้อมูล

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-05-big-data/chunk_processing.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-05-big-data/chunk_processing.py`
