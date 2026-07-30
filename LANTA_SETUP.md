# LANTA Setup Guide

คู่มือการตั้งค่าสภาพแวดล้อมบน LANTA สำหรับ HPC Ignite Hands-On Labs

## การเชื่อมต่อ LANTA

```bash
# SSH เข้าสู่ระบบ
ssh username@lanta.nstda.or.th

# หรือใช้ SSH config
# ~/.ssh/config
Host lanta
    HostName lanta.nstda.or.th
    User your_username
    IdentityFile ~/.ssh/id_rsa
```

## โครงสร้างไฟล์ระบบ

| Path | ขนาด | ระยะเวลาเก็บ | การใช้งาน |
|------|------|-------------|----------|
| `$HOME` | 50 GB | ถาวร | Scripts, configs, source code |
| `$SCRATCH` | 5 TB | 30 วัน | ข้อมูลชั่วคราว, ผลลัพธ์ |
| `$PROJECT` | ตามโควต้า | ถาวร | ข้อมูลกลุ่ม, datasets ขนาดใหญ่ |

## การติดตั้ง

### 1. Clone Repository

```bash
cd $HOME
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on
```

### 2. ตั้งค่า Environment Variables

เพิ่มใน `~/.bashrc`:

```bash
# HPC Ignite Hands-On
export HPC_IGNITE_HOME=$HOME/hpc-ignite-hands-on
export PATH=$HPC_IGNITE_HOME/scripts:$PATH
export HPC_IGNITE_ACCOUNT=<project-account>
export HPC_IGNITE_PARTITION=compute-devel

# Aliases
alias hpc-ignite='cd $HPC_IGNITE_HOME'
alias sq='squeue -u $USER'
alias si='sinfo -p compute,gpu'
```

### 3. รันงานแรกแบบไม่ต้องติดตั้ง dependency

```bash
cd $HPC_IGNITE_HOME
bash scripts/lanta_submit_foundation.sh smoke
squeue -u $USER
ls -lh logs
```

อ่านบทเรียนเต็ม: `foundation/lanta-foundation/README.md`

### 4. สร้าง Conda/Mamba Environment แบบ optional

Foundation lab ใช้ Python standard library เท่านั้น จึงไม่ต้องสร้าง environment เพิ่ม แต่ถ้าต้องการ environment
แยกสำหรับบทถัดไป สามารถใช้ Mamba ได้:

```bash
module load Mamba/23.11.0-0

# สร้าง base environment
mamba env create -f environments/base.yaml
mamba activate hpc-ignite

# ตรวจสอบ
python --version
which python
```

## SLURM Partitions

| Partition | Nodes | Max Time | GPUs | ใช้สำหรับ |
|-----------|-------|----------|------|----------|
| `debug` | 2 | 15 min | - | ทดสอบ |
| `compute` | 346 | 48 hr | - | CPU jobs |
| `gpu` | 88 | 48 hr | A100 x4 | GPU jobs |
| `memory` | 10 | 48 hr | - | High memory |

สำหรับ smoke test แนะนำเริ่มจาก `compute-devel` เพราะ time limit สั้นและเหมาะกับงานทดสอบ หากคิวเต็มค่อยลอง `compute-limited` หรือ `compute`

## Module System

### ดู Modules ที่มี

```bash
module avail
module spider PyTorch
module spider cuda
```

### Modules ที่ใช้บ่อย

```bash
# Python พื้นฐาน
module load cray-python/3.10.10

# Conda/Mamba
module load Mamba/23.11.0-0

# Deep Learning
module load cudatoolkit/24.11_12.6

# MPI
module load OpenMPI/4.1.2

# CUDA
module load cuda/12.6

# Scientific
module load netCDF/4.8
module load HDF5/1.12.2
```

## ตัวอย่าง SLURM Job

### CPU Job

```bash
#!/bin/bash
#SBATCH --job-name=hpc-test
#SBATCH --partition=compute
#SBATCH --nodes=1
#SBATCH --ntasks=32
#SBATCH --time=01:00:00
#SBATCH --output=%x_%j.out

source slurm/module-loads/base.sh

python my_script.py
```

### GPU Job

```bash
#!/bin/bash
#SBATCH --job-name=gpu-test
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=1
#SBATCH --time=02:00:00
#SBATCH --output=%x_%j.out

source slurm/module-loads/pytorch.sh

python train_model.py
```

### MPI Job

```bash
#!/bin/bash
#SBATCH --job-name=mpi-test
#SBATCH --partition=compute
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=32
#SBATCH --time=04:00:00
#SBATCH --output=%x_%j.out

source slurm/module-loads/mpi.sh

srun python mpi_program.py
```

## การตรวจสอบ Job

```bash
# ดู jobs ของตัวเอง
squeue -u $USER

# ดูรายละเอียด job
scontrol show job JOB_ID

# ยกเลิก job
scancel JOB_ID

# ดูประวัติ
sacct -u $USER --starttime=2025-01-01
```

## Tips & Best Practices

### 1. ใช้ $SCRATCH สำหรับ I/O หนัก

```bash
# Copy data to scratch
cp -r $HOME/data $SCRATCH/

# Run job from scratch
cd $SCRATCH/project
sbatch job.sbatch

# Copy results back
cp -r results/ $HOME/
```

### 2. ใช้ Job Arrays สำหรับ Parameter Sweeps

```bash
#SBATCH --array=1-100

PARAM=$(sed -n "${SLURM_ARRAY_TASK_ID}p" params.txt)
python simulate.py --param $PARAM
```

### 3. ตรวจสอบ GPU ก่อนใช้

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

### 4. Monitor Resource Usage

```bash
# ดู memory usage
sstat -j JOB_ID --format=MaxRSS,MaxVMSize

# ดู GPU usage (ใน job)
nvidia-smi
```

## Troubleshooting

### Module ไม่เจอ

```bash
module spider PACKAGE_NAME
# ดู dependencies
module spider cudatoolkit
module spider Mamba
```

### Conda environment ช้า

```bash
# ใช้ mamba แทน conda
mamba install package_name
```

### Job ถูก kill

ตรวจสอบ:
- Memory limit (`--mem`)
- Time limit (`--time`)
- Partition ถูกต้องไหม

```bash
sacct -j JOB_ID --format=JobID,State,ExitCode,MaxRSS,Elapsed
```

## Resources

- [LANTA User Guide](https://docs.lanta.nstda.or.th)
- [SLURM Documentation](https://slurm.schedmd.com/documentation.html)
- [HPC Ignite Curriculum](https://github.com/wdiazcarballo/hpc-curriculum)
