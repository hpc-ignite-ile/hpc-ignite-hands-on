# การประเมินตัวอย่างใน Repo เพื่อปรับเป็น Real Miniature LANTA Workflows

วันที่ตรวจ: 2026-08-02

Repo: `hpc-ignite-ile/hpc-ignite-hands-on`
เป้าหมาย: เปลี่ยนตัวอย่างทดสอบให้เป็น workflow ขนาดจิ๋วที่เหมือนงานจริง ใช้ module ที่มีบน LANTA ให้มากขึ้น และยังรันสั้นพอสำหรับ training

## สรุปสั้น

Repo นี้มีสองบุคลิก

1. `lanta-experience/`, `foundation/lanta-foundation/`, และ `mini-innovation/` เป็นรูปแบบที่ดีแล้ว: เริ่มจาก workspace, สร้างไฟล์ด้วย heredoc, ส่ง `sbatch`, เก็บ log/result/provenance, และใช้ runtime สั้น
2. `core-hpc/`, `ai-applications/`, และ `domain-science/` หลายบทมีเนื้อหาวิชาที่ดี แต่ runnable block มักเป็น `run_python_lab.sbatch` กลาง ๆ ที่ใช้ `base.sh` แล้วรัน Python synthetic script เพียงไฟล์เดียว ทำให้ยังไม่เห็นพลังของ LANTA module หรือ workflow จริงของแต่ละสาขา

ทิศทางที่ควรไปคือ **ไม่ทำให้ทุกบทเป็นงานใหญ่** แต่ให้ทุกบทมีอย่างน้อยหนึ่ง **real miniature workflow**:

- ใช้ module จริงของ LANTA
- ใช้ input/config ขนาดเล็ก
- รันบน `compute-devel` หรือ `gpu-devel`
- เก็บผลลัพธ์แยกตาม `SLURM_JOB_ID`
- มีขั้นตรวจ `module list`, `command -v`, log, CSV/PNG/summary
- ถ้าขยาย scale ได้ ให้เริ่มจาก smoke test ก่อน แล้วค่อยมี job array หรือ multi-node version

## หลักฐานจาก LANTA ที่ตรวจสด

ตรวจด้วย user `tn642` เมื่อ 2026-08-02

Partitions ที่เหมาะกับ training:

- `compute-devel`: idle, limit 2 ชั่วโมง
- `gpu-devel`: idle, limit 2 ชั่วโมง
- `compute`: สำหรับ instructor demo หรือ array ที่ใหญ่ขึ้น
- `gpu`: สำหรับ GPU demo ที่เกิน smoke test

Module และ shared data ที่ควรใช้ใน repo:

- Python/dev: `cray-python/3.10.10`, `cray-python/3.11.7`, `Mamba/23.11.0-0`, `Miniforge3/25.3.0-3`, `Apptainer/1.1.6`
- Compiler/MPI: `cpeCray/25.03`, Cray compiler wrapper `cc`, Slurm `srun`
- Data/geospatial/weather: `GDAL/3.6.4-cpeCray-23.03`, `WPS/4.6-DM-cpeCray-25.03`, `WRF/4.7.1-DMSM-cpeCray-25.03`, `WRFchem/4.7.1-DM-cpeCray-25.03`
- Materials/MD: `QuantumESPRESSO/7.3.1-libxc-6.2.2-cpu`, `QuantumESPRESSO/7.3.1-libxc-6.2.2-NV24.11-CUDA12.6`, `GROMACS/2024.6-cpeGNU-25.03-CUDA-12.6`, newer GROMACS versions also visible
- Bioinformatics: `BLAST+/2.14.0-cpeGNU-23.03`, `SAMtools/1.22.1-cpeGNU-25.03`, `BCFtools/1.22-cpeGNU-25.03`, `BEDTools/2.30.0-cpeGNU-23.03`, `BWA/0.7.17-cpeGNU-23.03`, `MAFFT/7.525-cpeGNU-25.03-with-extensions`, `Nextflow/25.04.6`
- Shared examples/data: `/project/common/GROMACS`, `/project/common/QuantumEspresso`, `/project/common/WRF`, `/project/common/WPS_Static`, `/project/common/AI-Guided-projects`, `/project/common/Mamba`, `/project/common/Miniforge3`

Python environment facts:

- `cray-python/3.10.10`: has `numpy`, `pandas`, `scipy`; does not have `matplotlib`
- `netcdf-py39`: has `numpy`, `pandas`, `scipy`, `xarray`, `netCDF4`, `matplotlib`; missing `sklearn`, `Bio`
- `pytorch-2.2.2`: has `torch`, `numpy`, `networkx`; missing `pandas`, `scipy`, `sklearn`, `transformers`, `datasets`, `accelerate`
- `tensorflow-2.12.1`: has `tensorflow`, `numpy`, `scipy`; missing `pandas`, `sklearn`

Implication:

- ใช้ `cray-python` สำหรับ standard library, NumPy, pandas, SciPy แบบไม่ plot
- ใช้ `netcdf-py39` สำหรับ data, NetCDF, xarray, Matplotlib
- ใช้ `pytorch-2.2.2` สำหรับ GPU/PyTorch smoke tests
- อย่าให้บทเรียนสดพึ่งการ `pip install` หรือสร้าง env ใหญ่ในห้อง ยกเว้นเป็นหน้า environment โดยเฉพาะ

## มาตรฐานใหม่ที่ควรใช้

### 1. Run taxonomy

| งาน | วิธีรันที่แนะนำ |
|---|---|
| Python เล็ก ไม่ plot | `module load cray-python/3.10.10` |
| Python data/plot/NetCDF | `module load Mamba/23.11.0-0`; `conda activate netcdf-py39` |
| PyTorch GPU | `module load Mamba/23.11.0-0`; `conda activate pytorch-2.2.2`; `gpu-devel` |
| C/OpenMP/MPI | `module reset`; `module load cpeCray/25.03`; compile with `cc`; run with `srun` |
| Domain CLI | load exact domain module in `jobs/*.sbatch`, run tiny input, parse log/result |
| Custom packages | project-prefix Mamba env under `/project/<account>/envs/...`, optional local Lmod module |

### 2. Minimum artifact set ต่อ workflow

ทุก real miniature workflow ควรมี

```text
configs/
jobs/
logs/
notes/
results/
src/
```

และหลังจบงานควรเห็น

- `logs/<job>_<jobid>.out`
- `logs/<job>_<jobid>.err`
- `results/<workflow>_<jobid>/`
- config หรือ input ที่ใช้จริง
- result summary เช่น CSV, text report, plot, หรือ parsed log
- `module list` หรือ `command -v <tool>` ใน log

### 3. สิ่งที่ควรเลี่ยง

- `module load Miniconda3` ในตัวอย่างใหม่ เพราะ live module ที่เห็นคือ `Mamba/23.11.0-0` และ `Miniforge3/25.3.0-3`
- ชื่อ module เก่า เช่น `PyTorch/2.0.1-CUDA-11.7.0`, `TensorFlow/2.11.0-CUDA-11.7.0`, `WRF-Chem/4.4`, `Spark/3.3.0`
- `mpirun` ใน Slurm job ถ้าไม่ได้มีเหตุผลเฉพาะ ใช้ `srun` เป็นค่าเริ่มต้นบน LANTA
- GPU examples ที่ submit ไป `compute-devel`
- Domain chapters ที่พูดถึงซอฟต์แวร์จริงแต่รันเฉพาะ synthetic Python
- การดาวน์โหลด dataset/model ตอน workshop สด

## Evaluation By Folder

### Root

| Path | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `README.md` | ดีสำหรับ event path และเพิ่ง link `mini-innovation/` | เพิ่ม link ไป audit นี้ และเพิ่มตาราง "recommended real workflow path" |
| `LANTA_SETUP.md` | เป็น setup reference | ปรับ module names ให้ใช้ `Mamba/23.11.0-0`, `cray-python/3.10.10`, `cpeCray/25.03`; แยก login/transfer/compute ให้ชัด |

### `docs/`

| Path | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `LAB_AUTHORING_GUIDE_TH.md` | ดีมาก เป็นมาตรฐาน heredoc-first | เพิ่ม rule ว่า domain lab ต้องมี real module-backed smoke workflow อย่างน้อย 1 งาน |
| `COPY_PASTE_ONLY_LABS_TH.md` | ดีสำหรับ template | เพิ่ม template สำหรับ `netcdf-py39`, `pytorch-2.2.2`, CPE/MPI, domain CLI |

### `slurm/`

| Path | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `module-loads/base.sh` | โหลด `cray-python` และ `Mamba`; ดีสำหรับ foundation | ระบุชัดว่าเหมาะกับ Python เบา ๆ เท่านั้น เพราะ `cray-python` ไม่มี Matplotlib |
| `module-loads/mpi.sh` | พยายามโหลด OpenMPI ก่อน | เปลี่ยน default เป็น `cpeCray/25.03` และ Cray MPI wrapper; `OpenMPI` เป็น fallback เท่านั้น |
| `module-loads/pytorch.sh` | โหลด CUDA/NCCL แต่ไม่ได้ activate env | เพิ่ม `conda activate pytorch-2.2.2` หรือสร้าง `pytorch-shared.sh` แยก |
| `module-loads/tensorflow.sh` | อ้าง module เก่า `TensorFlow/2.11.0-CUDA-11.7.0` | ปรับเป็น `Mamba/23.11.0-0` + `tensorflow-2.12.1`; หรือ mark legacy |
| `templates/` | มี shape พื้นฐาน | เพิ่ม template เฉพาะ `netcdf-postprocess.sbatch`, `qe-scf.sbatch`, `gromacs-gpu-smoke.sbatch`, `bio-cli-smoke.sbatch`, `apptainer-smoke.sbatch` |

### `environments/`

| Path | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `base.yaml` | ชื่อ env คือ `hpc-ignite` แต่ README หลายที่เรียก `hpc-ignite-base` | แก้ README หรือเปลี่ยนชื่อ env ให้ตรงกัน |
| `dask.yaml` | เหมาะกับ Dask | ใช้เฉพาะบท Dask และระบุ project-prefix env สำหรับ workshop |
| `ml-gpu.yaml` | pin CUDA 11.7 และ package เยอะ | สำหรับ smoke test ใช้ shared `pytorch-2.2.2`; ใช้ไฟล์นี้เฉพาะ custom training |
| `mpi.yaml` | ใช้ `mpi4py` จาก conda | ต้องทดสอบกับ LANTA MPI จริง ถ้าสอน MPI จริงให้เพิ่ม C MPI examples ที่ใช้ CPE ก่อน |
| `lanta-foundation.yaml` | เล็กดี | ใช้สำหรับ CI/local ไม่จำเป็นต้องใช้ใน LANTA ถ้า `cray-python` พอ |

### `requirements/`

| Path | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `base.txt`, `data.txt`, `ml.txt`, `mpi.txt` | เป็น pip dependency lists | ใส่ caveat ว่า LANTA training ควรใช้ module/shared env ก่อน pip; เพิ่ม mapping ไป module/env ที่ตรวจแล้ว |
| `ml.txt` | เสี่ยงชนกับ CUDA/module จริง | ชี้ไป `pytorch-2.2.2` สำหรับ smoke; custom env ควรสร้างล่วงหน้าบน transfer host |

### `scripts/`

สถานะ: folder นี้มีอยู่แต่ยังไม่มี script ในการตรวจครั้งนี้

วิธีที่ดีกว่า:

- ถ้าจะเพิ่ม automation ให้ใช้สำหรับ static validation หรือ instructor tooling เท่านั้น
- อย่าใช้ helper script ซ่อนการ submit job ใน learner-facing labs เพราะ repo มีมาตรฐาน heredoc-first แล้ว
- ตัวอย่างที่เหมาะสม: `scripts/check_readme_inventory.py`, `scripts/check_stale_modules.py`, `scripts/extract_tutorial_code.py`

### `tests/`

| Path | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `test_lanta_foundation.py` | ตรวจ foundation และ event docs บางส่วน | เพิ่ม static tests ว่า README ไม่อ้าง module เก่า, README-listed files มีจริง, GPU labs ใช้ `gpu-devel`, MPI labs ใช้ `srun -n >1`, domain chapters มี `jobs/*.sbatch` ที่ใช้ module จริง |

### `foundation/chapter-00/`

| Example | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `hello_lanta.py`, `hello_lanta.sbatch` | smoke test เก่า ใช้ `Miniconda3`, hard-code `compute` | เปลี่ยนไปใช้ `compute-devel`, optional `-A`, `cray-python/3.10.10`, `logs/%x_%j.out`; หรือให้ใช้ `foundation/lanta-foundation/` แทน |
| `amdahl_speedup.py`, `exercises/amdahl_exercise.py` | concept script มี plot | ถ้าจะรันบน LANTA ใช้ `netcdf-py39` หรือ project env ที่มี Matplotlib; save PNG/CSV ใน `results/<jobid>/` |
| `rice_production_analysis.py` | synthetic domain story | เปลี่ยนเป็น miniature agri workflow: config + generated input CSV + model + result/provenance; ใช้ `netcdf-py39` หาก plot |
| `wrf_chem_airquality.sbatch` | production-shaped placeholder, 32 nodes, module names stale, run line commented | แยกออกจาก foundation หรือเปลี่ยนเป็น WRF/WPS preflight: load `WRFchem/4.7.1-DM-cpeCray-25.03`, `WPS/4.6-DM-cpeCray-25.03`, check executable/shared data, `ncdump -h` tiny file; full WRF เป็น instructor demo เท่านั้น |

### `foundation/lanta-foundation/`

สถานะ: ควรเป็น canonical foundation path

| Example | สถานะปัจจุบัน | วิธีที่ดีกว่า |
|---|---|---|
| `verify_lanta.py` | real diagnostic | keep |
| `serial_sum.py` | toy compute แต่เหมาะกับ first Slurm smoke | keep, เพิ่ม provenance ถ้าจำเป็น |
| `array_task.py` | good miniature parameter sweep | keep |
| `jobs/*.sbatch` | short, visible, real Slurm | keep, เพิ่ม optional `sacct` summary หลัง run |

หมายเหตุ: มี `__pycache__/` ใน working tree ควร ignore/remove ถ้ายัง track อยู่

### `lanta-experience/`

สถานะ: เป็น path หลักที่ดีที่สุดสำหรับ training

| Page | วิธีที่ควรปรับ |
|---|---|
| `00-readiness.md` | เพิ่ม live module inventory: `module avail cray-python Mamba cpeCray WRF WPS QuantumESPRESSO GROMACS GDAL BLAST+` |
| `01-first-slurm-job.md` | ดีแล้ว; ใช้ optional `SBATCH_ACCOUNT=()` pattern ให้สอดคล้องกับบทอื่น |
| `02-cpu-array.md` | ดีแล้ว; เพิ่ม `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`; สอน array concurrency `%N` |
| `03-openmp-mpi.md` | ดีมาก; ปรับ MPI ให้ prefer `cpeCray/25.03` และ `srun`; เพิ่ม `OMP_PLACES=cores`, `OMP_PROC_BIND=close` |
| `04-science-data.md` | diffusion เป็น real miniature science workflow; sensor summary ควรมี Slurm version และ optional NetCDF preflight ด้วย `netcdf-py39` |
| `05-ai-gpu.md` | ดีสำหรับ GPU smoke; ควร centralize เป็น `module-loads/pytorch-shared.sh` |
| `06-run-logs.md` | ดีมาก; เพิ่ม robust case เมื่อ `sacct` delay หรือไม่มี input บางไฟล์ |

### `mini-innovation/`

สถานะ: เป็น template ที่ดีสำหรับ scaffolded innovation

ควรนำ pattern นี้ไปใช้กับ domain folders:

- หน้า connect แยก
- environment เป็น project-prefix
- สร้าง Lmod module เอง
- Jupyter ผ่าน Slurm allocation
- model script + config + job array + multicore
- AI scaffold เป็น prompt file ไม่ใช่คำตอบลอย ๆ

เพิ่มได้:

- `jobs/smoke.sbatch` ที่อยู่ใน repo จริง ไม่ใช่สร้างจาก tutorial อย่างเดียว
- static test ตรวจว่า Python heredoc ใน tutorial compile ได้

## `core-hpc/` Folder

### `chapter-02-environment/`

สถานะ: ดีเป็น environment audit แต่ README อ้างไฟล์ที่ไม่มี เช่น `slurm_basics.py`, `filesystem_demo.py`, `sbatch/environment_check.sbatch`

Better miniature workflow:

- `jobs/environment_audit.sbatch`
- load `cray-python/3.10.10`
- run `check_environment.py`
- capture `module list`, `conda env list`, `sinfo`, `myquota`, `sbalance`
- write `results/env_<jobid>/system.json`

### `chapter-03-parallel/`

สถานะ: มี MPI Python scripts จริง แต่ README copy-paste บอกว่าไม่มี script ขนาดเล็ก

Better miniature workflow:

- `jobs/mpi_rank_smoke.sbatch`
- ใช้ `cpeCray/25.03` หรือ tested MPI env
- run `srun -n 4 python mpi/hello_mpi.py`
- run `parallel_sum.py` หรือ `monte_carlo_pi.py` ขนาดเล็ก
- เก็บ CSV ว่า ranks, elapsed, result เป็นอย่างไร

ถ้า `mpi4py` ไม่เข้ากับ system MPI ให้มี C MPI hello เป็น fallback ที่ compile ด้วย `cc`

### `chapter-04-deep-learning/`

สถานะ: ควรเป็น real GPU smoke แต่ README/script บางจุดยังอ้าง PyTorch module เก่า

Better miniature workflow:

- `gpu-devel`, 1 GPU, 4-8 CPU, 5-10 นาที
- `module load Mamba/23.11.0-0`
- `conda activate pytorch-2.2.2`
- run `gpu_check.py` + tiny tensor benchmark
- optional `mnist_training.py --epochs 1` แต่ต้อง pre-stage/cache MNIST

### `chapter-05-big-data/`

สถานะ: synthetic pandas/chunking ดี แต่ยังไม่เป็น job-scoped data workflow

Better miniature workflow:

- generate input CSV under `input/<jobid>/`
- chunk process under Slurm
- write summary/provenance to `results/<jobid>/`
- use `netcdf-py39` ถ้าต้อง plot; `cray-python` ถ้า CSV only

### `chapter-06-visualization/`

สถานะ: Matplotlib example ต้องการ env ที่มี Matplotlib แต่ `base.sh` อาจไม่พอ

Better miniature workflow:

- `module load Mamba/23.11.0-0`
- `conda activate netcdf-py39` หรือ project env
- set `MPLBACKEND=Agg`
- run figure-generation job
- verify PNG files with `file` and `ls -lh`

### `chapter-07-dask/`

สถานะ: ต้องใช้ Dask env จริง; copy block ปัจจุบันใช้ `base.sh` และ memory 1G ซึ่งเสี่ยงไม่พอ

Better miniature workflow:

- prebuild project env from `environments/dask.yaml`
- `--cpus-per-task=4`, `--mem=8G`, `00:10:00`
- run `dask_basics.py` default small case
- avoid `--full` in workshop smoke

### `chapter-08-mpi/`

สถานะ: copy block ปัจจุบันผิดหลัก MPI เพราะ `--ntasks=1` และ plain `python`

Better miniature workflow:

- `#SBATCH --ntasks=4`
- load MPI/CPE or mpi4py env
- `srun -n "${SLURM_NTASKS}" python collective_ops.py`
- then `heat_equation.py --n <small> --steps <small>` as mini stencil workflow

### `chapter-09-spark/`

สถานะ: README อ้าง `Spark/3.3.0` แต่ live module list ของ `tn642` ไม่เห็น Spark

Better miniature workflow:

- ถ้า `module spider Spark` ไม่พบ ให้ mark chapter เป็น optional
- หรือเปลี่ยนเป็น local PySpark-in-one-allocation only ถ้ามี project env ที่ติดตั้ง PySpark แล้ว
- สำหรับ training จริง ให้ใช้ Dask chapter แทน Spark จนกว่า Spark module/env จะ verify

### `chapter-10-gpu/`

สถานะ: GPU story ดี แต่ CuPy ไม่มี shared env ที่ยืนยันแล้ว

Better miniature workflow:

- ใช้ PyTorch GPU smoke เป็น default
- ถ้าจะสอน CuPy ให้สร้าง project env ล่วงหน้า อย่า `pip install cupy` สด
- ใช้ `gpu-devel`, `nvidia-smi`, `torch.cuda.is_available()`, matrix multiply
- ถ้าจะสอน CUDA จริง ให้เพิ่ม C/CUDA kernel ที่ compile ด้วย site CUDA module เป็น optional

## `ai-applications/` Folder

### `chapter-11-containers/`

สถานะ: README ยังใช้คำว่า Singularity และ module `Singularity/3.8.3`

Better miniature workflow:

- ใช้ `Apptainer/1.1.6`
- pull/build บน `transfer.lanta.nstda.or.th`
- store `.sif` ใน `/project/<account>/containers`
- run smoke on compute node: `apptainer exec -B "$PWD:$PWD" image.sif python container_demo.py`
- GPU smoke: `apptainer exec --nv ...` บน `gpu-devel`

### `chapter-12-ai-development/`

สถานะ: README ส่ง PyTorch distributed script ผ่าน CPU wrapper ซึ่งไม่ตรงกับเป้าหมาย

Better miniature workflow:

- `gpu-devel`, 1 GPU ก่อน
- shared `pytorch-2.2.2`
- tiny training or tensor benchmark
- DDP only as instructor demo: 1 node, 2-4 GPUs, `srun` with proper env vars
- harden script so CPU/no-CUDA does not crash unexpectedly

### `chapter-13-prompts/`

สถานะ: เป็น concept chapter ไม่ควรต้องใช้ Slurm เสมอไป

Better miniature workflow:

- เปลี่ยนเป็น AI scaffold lab: generate Slurm review prompt from actual `jobs/*.sbatch`, compare AI suggestion with LANTA policy checklist
- ไม่ใส่ API key หรือบังคับ external API บน LANTA
- ถ้ารันบน LANTA ให้เป็น Python static prompt formatter ไม่ใช่ network call

### `chapter-28-llm-finetuning/`

สถานะ: บทใหญ่เกินสำหรับ live smoke ถ้าให้สร้าง env/download model สด

Better miniature workflow:

- use shared/project model cache under `/project`
- run offline tiny LoRA math demo first
- optional GPU smoke with shared small model only if model/license/cache already prepared
- document Hugging Face license acceptance and offline cache explicitly

### `chapter-29-security/`

สถานะ: concept/security checklist

Better miniature workflow:

- login-node workflow ไม่ต้อง submit Slurm
- create sample directory, set permissions, run file permission audit
- add secret-scan static exercise: detect fake token pattern in sample files
- avoid `ssh-copy-id` as default because LANTA login may use site-controlled auth/2FA

### `chapter-30-carbon/`

สถานะ: carbon calculator is useful but should be tied to real accounting

Better miniature workflow:

- after running real jobs, call `sacct`, `sbill`, `sbalance`
- estimate energy/SHr from actual elapsed/resource request
- label carbon intensity/PUE assumptions as assumptions, not official measurement

## `domain-science/` Folder

### `chapter-20-computational-chemistry/`

สถานะ: RDKit script is useful but RDKit is not a live shared module in the checked module list

Better miniature workflow:

- Default: `AutoDock-vina/1.2.5` tiny docking smoke if inputs can be included or generated
- Optional custom env: RDKit project-prefix env built before class
- Licensed tools: Gaussian/Amber only if `groups` confirms access

### `chapter-21-molecular-dynamics/`

สถานะ: synthetic Lennard-Jones script teaches MD concept, but LANTA has real GROMACS examples

Better miniature workflow:

- `gpu-devel`, 1 GPU, short time
- `module load GROMACS/2024.6-cpeGNU-25.03-CUDA-12.6`
- copy `/project/common/GROMACS/INPUTs/benchPEP.tpr`
- run short `gmx mdrun` with `-nsteps` small if feasible
- parse performance/energy/log into `results/gromacs_<jobid>/summary.txt`

### `chapter-22-climate-modeling/`

สถานะ: synthetic climate analysis, but LANTA has WRF/WPS/WRF-Chem data and `netcdf-py39`

Better miniature workflow:

- data-first smoke: use `/project/common/WRF` sample NetCDF/GRIB if available
- `module load Mamba/23.11.0-0`; `conda activate netcdf-py39`
- xarray/netCDF summary to CSV/PNG
- WRF/WPS preflight: load `WPS/4.6...`, `WRF/4.7.1...`, check executables and `namelist` examples
- full WRF run should be instructor demo, not participant smoke

### `chapter-23-materials-science/`

สถานะ: crystal visualization is concept-only; LANTA has QE examples

Better miniature workflow:

- `compute-devel`
- `module load QuantumESPRESSO/7.3.1-libxc-6.2.2-cpu`
- copy a tiny `/project/common/QuantumEspresso/CPU` or `Guided_project` input
- set `ESPRESSO_TMPDIR` under `/scratch/<account>/$USER/$SLURM_JOB_ID`
- `srun pw.x -inp input.in`
- parse final energy or convergence into CSV

### `chapter-24-ai-forest/`

สถานะ: NDVI script is synthetic arrays

Better miniature workflow:

- `module load GDAL/3.6.4-cpeCray-23.03`
- inspect real geospatial metadata from WPS static/geog or Thai shapefiles
- use `ogrinfo`/`gdalinfo` as smoke
- then Python `netcdf-py39` or project env for NDVI-like raster math on tiny generated GeoTIFF

### `chapter-25-bioinformatics/`

สถานะ: BioPython script is concept-only; live LANTA has many bio CLI modules

Better miniature workflow:

- `module load BLAST+/2.14.0-cpeGNU-23.03`
- generate tiny FASTA
- `makeblastdb` and `blastn`
- optional `BWA -> SAMtools flagstat` with tiny reads/reference
- write tabular output and tool versions

### `chapter-26-smart-agriculture/`

สถานะ: synthetic scikit-learn crop analysis; `netcdf-py39` missing sklearn

Better miniature workflow:

- use weather/geodata data path instead of ML first
- `netcdf-py39` for WRF/GFS rainfall summary
- GDAL + Thai shapefile for province/district metadata
- optional ML only with prebuilt project env containing scikit-learn

### `chapter-27-disaster-prevention/`

สถานะ: synthetic flood model

Better miniature workflow:

- use miniature hazard-grid workflow: WRF/GFS rainfall field summary or generated terrain + real Thai shapefile boundary
- `GDAL`, `netcdf-py39`, optional `ParFlow`/`OpenFOAM` only as advanced module preflight
- for live participants, keep simulation small and run array over warning/policy scenarios

## Priority Plan

### P0: Make existing examples honest and runnable

1. Replace stale module names in README/module snippets
2. Fix env-name drift: `hpc-ignite` vs `hpc-ignite-base`
3. Fix MPI copy blocks to use `srun -n >1`
4. Fix GPU/AI copy blocks to use `gpu-devel` and `pytorch-2.2.2`
5. Mark Spark, CuPy, RDKit, LLM finetuning, VASP/Gaussian/Amber as optional unless env/license is prepared

### P1: Add domain module smoke jobs

1. QE SCF smoke for materials
2. GROMACS GPU smoke for MD
3. NetCDF/xarray WRF data summary for climate
4. GDAL Thai shapefile/raster smoke for forest/agri/disaster
5. BLAST/SAMtools CLI smoke for bioinformatics
6. Apptainer CPU/GPU smoke for containers

### P2: Add static tests

1. README-listed files exist
2. No new docs refer to stale module names
3. GPU docs use `gpu-devel` or `gpu`
4. MPI docs use `srun`
5. Domain chapters include at least one `jobs/*.sbatch` real workflow
6. Tutorial Python heredocs compile

### P3: Instructor demo track

Build a separate `instructor-demos/` or `advanced-workflows/` path for examples that are real but too heavy for 40 participants:

- WRF/WRF-Chem mini case
- GROMACS performance comparison CPU vs GPU
- QE CPU vs GPU comparison
- PyTorch DDP 1-node 4-GPU
- LLM LoRA with pre-cached model

## Recommended Next Patch

The highest-value patch is not to rewrite every science script. It is to add a small set of reusable module-backed jobs:

```text
slurm/module-loads/
├── pytorch-shared.sh
├── netcdf-python.sh
├── cpe-mpi.sh
├── qe.sh
├── gromacs.sh
├── geodata.sh
├── bio.sh
└── apptainer.sh
```

Then update domain READMEs to call those snippets and add one tiny `jobs/*.sbatch` per chapter. That gives learners the real shape of LANTA scientific workflows without turning the workshop into a queue-management marathon.
