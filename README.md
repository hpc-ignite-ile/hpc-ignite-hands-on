# HPC Ignite Hands-On Labs

[![LANTA Compatible](https://img.shields.io/badge/LANTA-Compatible-blue.svg)](https://docs.lanta.nstda.or.th)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Runnable code examples and hands-on exercises for the HPC Ignite curriculum, designed for execution on Thailand's LANTA supercomputer.

## Quick Start on LANTA

```bash
# 1. Clone the repository
cd $HOME
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on

# 2. ตั้งค่า project account และ partition สำหรับงานแรก
export HPC_IGNITE_ACCOUNT=<project-account>
export HPC_IGNITE_PARTITION=compute-devel

# 3. ส่งงาน foundation smoke test ที่ไม่ต้องติดตั้ง package เพิ่ม
bash scripts/lanta_submit_foundation.sh smoke

# 4. ดูผลลัพธ์
squeue -u $USER
ls -lh logs
find results/foundation -maxdepth 3 -type f | sort
```

เริ่มจากบทภาษาไทยที่รันได้จริงบน LANTA: [`foundation/lanta-foundation/README.md`](foundation/lanta-foundation/README.md)

## Repository Structure

```
hpc-ignite-hands-on/
├── foundation/              # บทที่ 0-1: HPC 101, Linux พื้นฐาน
├── core-hpc/                # บทที่ 2-10: MPI, PyTorch, Dask, Spark, GPU
├── ai-development/          # บทที่ 11-13: Containers, AI Dev, Prompts
├── applications/            # บทที่ 14-19: แอปพลิเคชันภาคเหนือ
├── domain-science/          # บทที่ 20-27: Chemistry, Climate, Bio
├── advanced/                # บทที่ 28-30: LLM, Security, Carbon
├── environments/            # Conda/Mamba environment files
├── slurm/                   # Slurm templates and module loads
├── scripts/                 # Submit wrappers for LANTA
├── requirements/            # pip requirements files
└── tests/                   # Validation scripts
```

## Chapter Overview

| Track | Chapters | Topics |
|-------|----------|--------|
| **Foundation** | 0-1 | HPC 101, Linux Basics |
| **Core HPC** | 2-10 | Environment, Parallel, PyTorch, Dask, MPI, Spark, GPU |
| **AI Development** | 11-13 | Containers, AI Development, Prompt Engineering |
| **Applications** | 14-19 | 3D Design, Educational AI, Smart Home, Health, Dashboard |
| **Domain Science** | 20-27 | Chemistry, MD, Climate, Materials, Bio, Agriculture, Disaster |
| **Advanced** | 28-30 | LLM Fine-tuning, Security, Carbon Verification |

## LANTA System Requirements

### Compute Resources

| Configuration | Nodes | CPUs | GPUs | Memory | Partition |
|---------------|-------|------|------|--------|-----------|
| CPU Small | 1 | 32 | 0 | 64G | compute |
| CPU Large | 4 | 128 | 0 | 256G | compute |
| GPU Single | 1 | 32 | 1 | 128G | gpu |
| GPU Multi | 1 | 128 | 4 | 512G | gpu |

### File Systems

```bash
$HOME      # 50 GB - Scripts, configs (persistent)
$SCRATCH   # 5 TB - Data, outputs (30-day retention)
$PROJECT   # Group storage - Shared datasets
```

### Module Environment

```bash
module load cray-python/3.10.10
module load Mamba/23.11.0-0
module load cudatoolkit/24.11_12.6
module load OpenMPI/4.1.2
```

## Environment Setup

### Option 1: Conda (Recommended)

```bash
# Base environment (optional; foundation lab does not require this)
mamba env create -f environments/base.yaml
mamba env create -f environments/lanta-foundation.yaml

# ML/GPU environment
mamba env create -f environments/ml-gpu.yaml

# MPI environment
mamba env create -f environments/mpi.yaml
```

### Option 2: pip

```bash
pip install -r requirements/base.txt
pip install -r requirements/ml.txt  # For ML chapters
pip install -r requirements/mpi.txt # For MPI chapters
```

## Running Examples

### CPU Jobs

```bash
cd core-hpc/chapter-03-parallel/mpi
sbatch parallel_sum.sbatch
```

### GPU Jobs

```bash
cd core-hpc/chapter-04-deep-learning
sbatch mnist_training.sbatch
```

### Interactive Session

```bash
srun --partition=gpu --gpus=1 --time=01:00:00 --pty bash
source slurm/module-loads/pytorch.sh
python pytorch_basics.py
```

For the currently tested foundation path, prefer:

```bash
export HPC_IGNITE_ACCOUNT=<project-account>
export HPC_IGNITE_PARTITION=compute-devel
bash scripts/lanta_submit_foundation.sh smoke
bash scripts/lanta_submit_foundation.sh array
```

## Related Resources

- **Curriculum Book**: [HPC Ignite Curriculum](https://github.com/wdiazcarballo/hpc-curriculum/tree/main/docs/curriculum-book)
- **SCORM Modules**: [Interactive Learning Modules](https://github.com/wdiazcarballo/hpc-curriculum/tree/main/scorm-modules)
- **LANTA Documentation**: [docs.lanta.nstda.or.th](https://docs.lanta.nstda.or.th)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-example`)
3. Test on LANTA or compatible HPC system
4. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**HPC Ignite Project** | Thailand National HPC Training Initiative
