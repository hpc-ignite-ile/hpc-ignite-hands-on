# บทที่ 4: การเรียนรู้เชิงลึกบนระบบ HPC

Chapter 4: Deep Learning with PyTorch on HPC

## วัตถุประสงค์การเรียนรู้

1. ใช้งาน PyTorch บน GPU (NVIDIA A100)
2. เขียนโปรแกรม training loop พื้นฐาน
3. ใช้ Distributed Data Parallel (DDP) สำหรับ Multi-GPU
4. Optimize performance ด้วย Mixed Precision

## โครงสร้างไฟล์

```
chapter-04-deep-learning/
├── README.md
├── pytorch_basics.py          # PyTorch tensor operations
├── gpu_check.py               # Check GPU availability
├── mnist_training.py          # MNIST classification
├── multi_gpu_ddp.py           # Distributed Data Parallel
└── sbatch/
    ├── single_gpu.sbatch
    └── multi_gpu.sbatch
```

## การใช้งาน

### On LANTA

```bash
# Load PyTorch module
source ../../slurm/module-loads/pytorch.sh

# Run GPU check
python gpu_check.py

# Submit training job
sbatch sbatch/single_gpu.sbatch
```

### On Local Machine (CPU)

```bash
# Create environment
mamba env create -f ../../environments/ml-gpu.yaml
mamba activate hpc-ignite-ml

# Run with CPU
python pytorch_basics.py
python mnist_training.py --device cpu
```

## แนวคิดหลัก

### GPU Memory Hierarchy

```
┌─────────────────────────────────────┐
│           Global Memory (40GB)       │  ← Large, slower
├─────────────────────────────────────┤
│        Shared Memory (per SM)        │  ← Fast, limited
├─────────────────────────────────────┤
│         Registers (per thread)       │  ← Fastest
└─────────────────────────────────────┘
```

### PyTorch to GPU

```python
import torch

# Check GPU
device = "cuda" if torch.cuda.is_available() else "cpu"

# Move tensor to GPU
x = torch.randn(1000, 1000).to(device)

# Move model to GPU
model = MyModel().to(device)
```

### Mixed Precision Training

```python
from torch.cuda.amp import autocast, GradScaler

scaler = GradScaler()

with autocast():
    output = model(input)
    loss = criterion(output, target)

scaler.scale(loss).backward()
scaler.step(optimizer)
scaler.update()
```

## NVIDIA A100 Specifications (LANTA)

| Feature | Value |
|---------|-------|
| Memory | 40 GB HBM2e |
| FP32 Performance | 19.5 TFLOPS |
| FP16 Performance | 312 TFLOPS |
| Tensor Core | 3rd Gen |

## เอกสารอ้างอิง

- [Curriculum Book - Chapter 4](https://github.com/wdiazcarballo/hpc-curriculum/blob/main/docs/curriculum-book/chapters/chapter-04-deep-learning.md)
- [PyTorch Documentation](https://pytorch.org/docs/)
- [PyTorch DDP Tutorial](https://pytorch.org/tutorials/intermediate/ddp_tutorial.html)

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-04-deep-learning/gpu_check.py}"

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
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_GPU_PARTITION" --export=ALL,LAB_SCRIPT="$LAB_SCRIPT" --parsable jobs/run_python_lab.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Results: find results/python-labs/${job_id} -type f -maxdepth 2 -print"
```

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-04-deep-learning/gpu_check.py`
