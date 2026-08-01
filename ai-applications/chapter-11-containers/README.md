# บทที่ 11: Containers สำหรับ HPC

Chapter 11: Containers (Singularity/Apptainer)

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ Container Technology
2. ใช้ Singularity/Apptainer บน HPC
3. Build Custom Containers
4. จัดการ GPU Containers

## โครงสร้างไฟล์

```
chapter-11-containers/
├── README.md
├── singularity_basics.sh   # Basic commands
├── container_demo.py       # Python in container
├── pytorch.def             # PyTorch container definition
├── build_container.sh      # Build script
└── sbatch/
    └── container_gpu.sbatch
```

## การใช้งาน

```bash
# On LANTA
module load Singularity/3.8.3

# Pull container
singularity pull pytorch.sif docker://pytorch/pytorch:latest

# Run container
singularity exec pytorch.sif python script.py

# Run with GPU
singularity exec --nv pytorch.sif python gpu_script.py
```

## Why Containers on HPC?

- **Reproducibility**: Same environment everywhere
- **Portability**: Move between systems
- **Isolation**: No conflicts with system libraries
- **Performance**: Near-native speed

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-ai-applications/chapter-11-containers/container_demo.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=ai-applications/chapter-11-containers/container_demo.py`
