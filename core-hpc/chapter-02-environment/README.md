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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-02-environment.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "core-hpc/chapter-02-environment/check_environment.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-02-environment.sh
```
