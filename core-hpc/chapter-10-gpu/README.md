# บทที่ 10: การเขียนโปรแกรม GPU

Chapter 10: GPU Programming with CUDA

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p gpu-devel core-hpc/chapter-10-gpu/jobs/gpu_smoke.sbatch
```

ใช้ PyTorch GPU smoke เป็น default ก่อน ส่วน CuPy/CUDA kernel ให้ใช้เมื่อมี project environment หรือ compiler module ที่เตรียมไว้แล้ว.

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ GPU Architecture และ CUDA Model
2. ใช้ CuPy สำหรับ GPU Arrays
3. เขียน Custom CUDA Kernels
4. Optimize Memory Access Patterns

## โครงสร้างไฟล์

```
chapter-10-gpu/
├── README.md
├── gpu_info.py              # GPU detection and info
├── cupy_basics.py           # CuPy array operations
├── numba_cuda.py            # Custom CUDA kernels with Numba
├── memory_patterns.py       # Memory access optimization
├── matrix_multiply.py       # GPU matrix multiplication
└── sbatch/
    └── gpu_job.sbatch
```

## การใช้งาน

```bash
# On LANTA
source ../../slurm/module-loads/pytorch-shared.sh

# Check GPU
python gpu_info.py

# Run examples
python gpu_info.py
# CuPy examples require a prebuilt project environment; do not pip install CuPy live.

# Submit job
sbatch sbatch/gpu_job.sbatch
```

## GPU vs CPU

| Aspect | CPU | GPU |
|--------|-----|-----|
| Cores | 16-128 | 1000s |
| Threads | 2 per core | 32 per SM |
| Best for | Sequential, complex | Parallel, simple |
| Memory | Large, fast | Smaller, very fast |

## LANTA GPUs

- **Model**: NVIDIA A100-SXM4-40GB
- **Tensor Cores**: 3rd Gen
- **Memory**: 40 GB HBM2e
- **Bandwidth**: 1.6 TB/s

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-10-gpu/gpu_info.py}"

mkdir -p jobs logs results/python-labs

cat > jobs/run_python_lab.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-python-lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gpus-per-node=1
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
if [ -f "slurm/module-loads/pytorch-shared.sh" ]; then
    source slurm/module-loads/pytorch-shared.sh
fi
mkdir -p "results/python-labs/${SLURM_JOB_ID}"
echo "script=${LAB_SCRIPT}"
python "$LAB_SCRIPT" | tee "results/python-labs/${SLURM_JOB_ID}/output.txt"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --export=ALL,LAB_SCRIPT="$LAB_SCRIPT" --parsable jobs/run_python_lab.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Results: find results/python-labs/${job_id} -type f -maxdepth 2 -print"
```

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-10-gpu/cupy_basics.py`
