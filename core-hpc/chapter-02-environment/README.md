# บทที่ 2: สภาพแวดล้อม HPC และระบบ LANTA

Chapter 2: HPC Environment and LANTA System

## วัตถุประสงค์การเรียนรู้

1. ใช้ระบบ Module บน LANTA
2. สร้างและจัดการ Conda/Mamba environments
3. ส่งงานด้วย SLURM (sbatch, srun, squeue)
4. จัดการไฟล์บน Lustre filesystem

## โครงสร้างไฟล์

```
chapter-02-environment/
├── README.md
├── check_environment.py    # ตรวจสอบสภาพแวดล้อม
├── slurm_basics.py         # SLURM job information
├── filesystem_demo.py      # File system operations
└── sbatch/
    └── environment_check.sbatch
```

## การใช้งานบน LANTA

```bash
# 1. ตรวจสอบ modules ที่มี
module avail
module spider PyTorch

# 2. โหลด module
module load Miniconda3
module load PyTorch/2.0.1-CUDA-11.7.0

# 3. สร้าง environment
mamba create -n myenv python=3.10
mamba activate myenv

# 4. ส่งงาน
sbatch sbatch/environment_check.sbatch
squeue -u $USER
```

## File Systems

| Path | Usage | Quota | Retention |
|------|-------|-------|-----------|
| `$HOME` | Scripts, configs | 50 GB | Permanent |
| `$SCRATCH` | Data, outputs | 5 TB | 30 days |
| `$PROJECT` | Shared data | Group | Permanent |

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-02-environment/check_environment.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-02-environment/check_environment.py`
