# HPC Ignite Hands-On Labs

[![LANTA Compatible](https://img.shields.io/badge/LANTA-Compatible-blue.svg)](https://docs.lanta.nstda.or.th)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

คู่มือฝึกปฏิบัติบน LANTA Supercomputer แบบ copy-paste ได้ทันที ผู้ใช้จะสร้างไฟล์จริงด้วย heredoc, ส่งงานด้วย `sbatch`, แล้วตรวจ log และผลลัพธ์ด้วยตนเอง

## เริ่มบน LANTA

```bash
cd "$HOME"
git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
cd hpc-ignite-hands-on

# เปิดเส้นทาง lab หลัก
sed -n '1,120p' lanta-experience/README.md
```

จากนั้นให้ผู้ใช้เปิด [lanta-experience/01-first-slurm-job.md](lanta-experience/01-first-slurm-job.md) แล้วแปะ block บน LANTA เพื่อสร้าง `src/hello_lanta.py`, สร้าง `jobs/hello_lanta.sbatch`, ส่งงานด้วย `sbatch`, และอ่านผลลัพธ์ใน `logs/` กับ `results/`

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

## งานจิ๋วที่ใช้ Module จริง

หลัง clone repo แล้ว ผู้ใช้สามารถเริ่มจาก job สั้น ๆ เหล่านี้ได้:

| Area | Starter job |
|---|---|
| Environment audit | `core-hpc/chapter-02-environment/jobs/environment_audit.sbatch` |
| MPI/CPE | `core-hpc/chapter-03-parallel/jobs/mpi_rank_smoke.sbatch` |
| PyTorch GPU | `core-hpc/chapter-04-deep-learning/jobs/gpu_smoke.sbatch` |
| Containers | `ai-applications/chapter-11-containers/jobs/apptainer_smoke.sbatch` |
| Epidemic ABS | `mini-innovation/jobs/epi_smoke.sbatch` |
| GROMACS MD | `domain-science/chapter-21-molecular-dynamics/jobs/gromacs_gpu_smoke.sbatch` |
| WRF/NetCDF data | `domain-science/chapter-22-climate-modeling/jobs/netcdf_wrf_summary.sbatch` |
| Quantum ESPRESSO | `domain-science/chapter-23-materials-science/jobs/qe_scf_smoke.sbatch` |
| GDAL/geodata | `domain-science/chapter-24-ai-forest/jobs/gdal_forest_smoke.sbatch` |
| BLAST bioinformatics | `domain-science/chapter-25-bioinformatics/jobs/blast_cli_smoke.sbatch` |

ก่อนส่ง job จาก repo ให้สร้างโฟลเดอร์ log และ result ก่อน:

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel core-hpc/chapter-02-environment/jobs/environment_audit.sbatch
```

## รูปแบบ Copy-Paste

ทุก lab ควรให้ผู้ใช้เห็นไฟล์ที่สร้างจริง ไม่ซ่อนงานไว้ใน helper script ตัวอย่างขั้นต่ำคือ:

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

ดู checklist สำหรับการเขียน lab เพิ่มเติมได้ที่ [docs/LAB_AUTHORING_GUIDE_TH.md](docs/LAB_AUTHORING_GUIDE_TH.md)

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
