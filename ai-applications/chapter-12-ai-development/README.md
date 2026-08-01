# บทที่ 12: AI Development บน HPC

Chapter 12: AI Development on HPC

## วัตถุประสงค์การเรียนรู้

1. ตั้งค่า AI Environment บน LANTA
2. ใช้ PyTorch/TensorFlow บน GPU
3. Distributed Training
4. Model Optimization

## โครงสร้างไฟล์

```
chapter-12-ai-development/
├── README.md
├── setup_environment.sh    # Environment setup
├── pytorch_distributed.py  # Multi-GPU PyTorch
├── data_loading.py         # Efficient data loading
├── mixed_precision.py      # AMP training
└── sbatch/
    └── distributed_train.sbatch
```

## การใช้งาน

```bash
# On LANTA
module load Miniconda3
module load CUDA/11.7.0

# Create environment
mamba create -n hpc-ai pytorch torchvision pytorch-cuda=11.7 -c pytorch -c nvidia
mamba activate hpc-ai

# Run distributed training
srun -p gpu -N 2 --gpus-per-node=4 python pytorch_distributed.py
```

## LANTA AI Resources

- GPUs: NVIDIA A100-SXM4-40GB
- GPU Memory: 40 GB HBM2e
- NVLink: 600 GB/s
- Available partitions: gpu, dgx

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-ai-applications/chapter-12-ai-development/pytorch_distributed.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=ai-applications/chapter-12-ai-development/pytorch_distributed.py`
