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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_ai-applications-chapter-11-containers.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "ai-applications/chapter-11-containers/container_demo.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_ai-applications-chapter-11-containers.sh
```
