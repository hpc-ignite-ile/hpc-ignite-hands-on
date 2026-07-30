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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_ai-applications-chapter-12-ai-development.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "ai-applications/chapter-12-ai-development/pytorch_distributed.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_ai-applications-chapter-12-ai-development.sh
```
