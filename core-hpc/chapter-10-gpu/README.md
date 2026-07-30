# บทที่ 10: การเขียนโปรแกรม GPU

Chapter 10: GPU Programming with CUDA

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
module load CUDA/11.7.0
module load Miniconda3
mamba activate hpc-ignite-ml

# Check GPU
python gpu_info.py

# Run examples
python cupy_basics.py
python matrix_multiply.py

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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA แล้วเลือกหมายเลข script ที่ต้องการส่งเข้า Slurm:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-10-gpu.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

LABS=(
    "core-hpc/chapter-10-gpu/cupy_basics.py"
    "core-hpc/chapter-10-gpu/gpu_info.py"
)

echo "เลือก script ของบท core-hpc/chapter-10-gpu:"
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

bash /tmp/hpc_ignite_core-hpc-chapter-10-gpu.sh
```
