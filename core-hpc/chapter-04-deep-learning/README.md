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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA แล้วเลือกหมายเลข script ที่ต้องการส่งเข้า Slurm:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-04-deep-learning.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

LABS=(
    "core-hpc/chapter-04-deep-learning/gpu_check.py"
    "core-hpc/chapter-04-deep-learning/mnist_training.py"
    "core-hpc/chapter-04-deep-learning/pytorch_basics.py"
)

echo "เลือก script ของบท core-hpc/chapter-04-deep-learning:"
select LAB_SCRIPT in "${LABS[@]}"; do
    if [ -n "${LAB_SCRIPT:-}" ]; then
        bash scripts/lanta_submit_python_lab.sh "$LAB_SCRIPT"
        break
    fi
    echo "กรุณาเลือกหมายเลขจากรายการ"
done

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-04-deep-learning.sh
```
