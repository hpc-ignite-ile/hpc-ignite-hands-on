# HPC Ignite Hands-On Labs

[![LANTA Compatible](https://img.shields.io/badge/LANTA-Compatible-blue.svg)](https://docs.lanta.nstda.or.th)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

คู่มือฝึกปฏิบัติบน LANTA Supercomputer แบบ copy-paste ได้ทันที ผู้ใช้จะสร้างไฟล์จริงด้วย heredoc, ส่งงานด้วย `sbatch`, แล้วตรวจ log และผลลัพธ์ด้วยตนเอง

คำสั่ง Bash, Slurm และ syntax ที่ใช้ใน repo นี้อธิบายรวมไว้ที่ [docs/BASH_COMMAND_REFERENCE_TH.md](docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `sed`, `ssh`, `module`, `sbatch`, heredoc, `#SBATCH`, pipe, redirection และตัวแปรของ shell

## เริ่มแบบ Standalone บน LANTA

ผู้ใช้ที่ต้องการตั้งค่า private key หรือ alias `ssh lanta` สามารถเริ่มจาก [docs/SSH_PRIVATE_KEY_LANTA_TH.md](docs/SSH_PRIVATE_KEY_LANTA_TH.md)

```bash
ssh <username>@lanta.nstda.or.th
mkdir -p "$HOME/hpc-ignite-standalone"
cd "$HOME/hpc-ignite-standalone"
pwd
```

ทุก hand-on page ในชุดนี้มี block ที่ผู้ใช้ copy-paste ได้โดยตรงจากหน้าเอกสาร เมื่อแปะบน LANTA แล้ว block จะสร้าง workspace ของบทนั้นเอง เช่น `jobs/`, `src/`, `configs/`, `logs/`, `results/` และส่งงานด้วย `sbatch` จากไฟล์ที่เพิ่งสร้างใน workspace นั้น

เริ่มจาก [lanta-experience/01-first-slurm-job.md](lanta-experience/01-first-slurm-job.md) ผู้ใช้จะสร้าง `src/hello_lanta.py`, สร้าง `jobs/hello_lanta.sbatch`, ส่งงานด้วย `sbatch`, แล้วอ่านหลักฐานใน `logs/` กับ `results/`

สำหรับผู้สอนที่มีสำเนา repo เพื่ออ่าน offline หรือปรับเอกสาร ใช้คำสั่งนี้จาก root ของ repo:

```bash
# เปิดเส้นทาง lab หลัก
sed -n '1,120p' lanta-experience/README.md
```

ตัวอย่าง `sed -n '1,120p' ...` ใช้เปิดดูบรรทัดที่ 1 ถึง 120 ของไฟล์ ดูคำอธิบายเต็มที่ [docs/BASH_COMMAND_REFERENCE_TH.md#sed](docs/BASH_COMMAND_REFERENCE_TH.md#sed)

## โฟลเดอร์ใน Repo

```text
hpc-ignite-hands-on/
├── lanta-experience/        # Main event path from the booklet
│   ├── 00-readiness.md      # Linux, shell, files, quota, modules
│   ├── 01-first-slurm-job.md
│   ├── 02-cpu-array.md
│   ├── 03-openmp-mpi.md
│   ├── 04-science-data.md
│   └── 05-ai-gpu.md
├── foundation/              # Reusable foundation scripts and older chapter material
├── core-hpc/                # Reference chapters: environment, parallel, data, MPI, GPU
├── ai-applications/         # Reference AI chapters
├── domain-science/          # Reference science/domain chapters
├── mini-innovation/         # Scaffolded epidemic ABS innovation labs
├── environments/            # Optional Conda/Mamba environment files
├── slurm/                   # Reusable Slurm templates and module-load snippets
├── docs/                    # Authoring guide and copy-paste conventions
├── requirements/            # Optional pip requirements
└── tests/                   # Local validation
```

## ลำดับ Lab หลัก

| Booklet section | Repo guide | Main activity |
|---|---|---|
| Linux, shell, files | [00-readiness.md](lanta-experience/00-readiness.md) | Create folders, configs, and system notes |
| First Slurm job | [01-first-slurm-job.md](lanta-experience/01-first-slurm-job.md) | Write `hello_lanta.py` and `hello_lanta.sbatch` using heredoc |
| CPU and arrays | [02-cpu-array.md](lanta-experience/02-cpu-array.md) | Run CPU pi baseline and a small job array |
| OpenMP and MPI | [03-openmp-mpi.md](lanta-experience/03-openmp-mpi.md) | Compile C examples and launch with `srun` |
| Science/data | [04-science-data.md](lanta-experience/04-science-data.md) | Run diffusion/data examples and capture evidence |
| AI/GPU | [05-ai-gpu.md](lanta-experience/05-ai-gpu.md) | Request one GPU and verify CUDA/PyTorch |

## Mini Innovation

ถ้าต้องการกิจกรรม live training แบบมี scientific model, agent-based simulation และ AI scaffold ให้เปิด [mini-innovation/README.md](mini-innovation/README.md) ผู้ใช้จะได้ทำ **LANTA EpiSprint** ด้วย Mesa, custom Python environment, Jupyter on Slurm, single job, job array และ multicore ensemble

## Audit สำหรับปรับ Repo

ถ้าต้องการดูเหตุผลของการปรับตัวอย่างให้เป็น workflow จิ๋วที่ใช้ module จริงบน LANTA ให้เปิด [docs/LANTA_REAL_MINI_WORKFLOW_AUDIT_TH.md](docs/LANTA_REAL_MINI_WORKFLOW_AUDIT_TH.md)

## แผนที่ Lab Standalone ที่ใช้ Module จริง

ผู้ใช้เลือกหน้าเดียวตามหัวข้อที่สนใจ แล้วแปะ block ในหน้านั้นบน LANTA ได้ทันที:

| Area | Standalone page |
|---|---|
| Environment audit | [core-hpc/chapter-02-environment/README.md](core-hpc/chapter-02-environment/README.md) |
| MPI/CPE | [core-hpc/chapter-03-parallel/README.md](core-hpc/chapter-03-parallel/README.md) |
| PyTorch GPU | [core-hpc/chapter-04-deep-learning/README.md](core-hpc/chapter-04-deep-learning/README.md) |
| Containers | [ai-applications/chapter-11-containers/README.md](ai-applications/chapter-11-containers/README.md) |
| Epidemic ABS | [mini-innovation/README.md](mini-innovation/README.md) |
| GROMACS MD | [domain-science/chapter-21-molecular-dynamics/README.md](domain-science/chapter-21-molecular-dynamics/README.md) |
| WRF/NetCDF data | [domain-science/chapter-22-climate-modeling/README.md](domain-science/chapter-22-climate-modeling/README.md) |
| Quantum ESPRESSO | [domain-science/chapter-23-materials-science/README.md](domain-science/chapter-23-materials-science/README.md) |
| GDAL/geodata | [domain-science/chapter-24-ai-forest/README.md](domain-science/chapter-24-ai-forest/README.md) |
| BLAST bioinformatics | [domain-science/chapter-25-bioinformatics/README.md](domain-science/chapter-25-bioinformatics/README.md) |

ไฟล์ใน `jobs/`, `slurm/`, `requirements/` และ `environments/` เป็น reference สำหรับผู้สอนและผู้ใช้ที่ต้องการดูตัวอย่างสำเร็จรูป ส่วน hand-on page จะสร้าง source และ job script ของตัวเองใน workspace ของผู้ใช้

```bash
# ตัวอย่าง workspace ที่ page แต่ละบทจะสร้าง
cd "$HOME/hpc-ignite-standalone"
find . -maxdepth 2 -type d | sort | head
```

## รูปแบบ Copy-Paste

ทุก lab ควรให้ผู้ใช้เห็นไฟล์ที่สร้างจริงและเห็นรายละเอียดการส่งงานใน `.sbatch` ตัวอย่างขั้นต่ำคือ:

```bash
mkdir -p jobs logs results src

cat > src/main.py <<'PY'
print("Hello from LANTA")
PY

cat > jobs/main.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-main
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
python src/main.py
SLURM

sbatch -p compute-devel jobs/main.sbatch
```

✅ เมื่อสำเร็จ ผู้ใช้จะเห็น job id จาก `sbatch` และอ่าน log ได้จาก `logs/`

ดู checklist สำหรับการเขียน lab เพิ่มเติมได้ที่ [docs/LAB_AUTHORING_GUIDE_TH.md](docs/LAB_AUTHORING_GUIDE_TH.md) และดูคำอธิบายคำสั่งใน block นี้ได้ที่ [docs/BASH_COMMAND_REFERENCE_TH.md](docs/BASH_COMMAND_REFERENCE_TH.md)

## LANTA Notes

- SSH login host: `lanta.nstda.or.th`
- Transfer host: `transfer.lanta.nstda.or.th`
- Use login nodes for editing, small checks, and job submission only.
- Start with `compute-devel` or `gpu-devel` smoke tests when available, then scale after the result is correct.
- Set `LANTA_ACCOUNT` only if your project requires explicit `sbatch -A`.

## เลือกบทต่อไปตามงานของผู้ใช้

หลังทำ lab หลักผ่านแล้ว ผู้ใช้สามารถเลือกบทอ้างอิงตามงานที่สนใจ:

| Track | Topics |
|---|---|
| `foundation/` | HPC basics and first runnable scripts |
| `core-hpc/` | Environment, parallel Python, Dask, MPI, Spark, GPU |
| `ai-applications/` | Containers, AI development, prompts, fine-tuning, security, carbon |
| `domain-science/` | Chemistry, MD, climate, materials, bioinformatics, agriculture, disaster |

## Related Resources

- LANTA User Guide: https://docs.lanta.nstda.or.th
- ThaiSC: https://www.thaisc.io
- Slurm: https://slurm.schedmd.com/documentation.html

## License

MIT License - See [LICENSE](LICENSE) for details.
