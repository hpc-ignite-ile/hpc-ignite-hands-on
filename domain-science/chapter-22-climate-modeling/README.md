# บทที่ 22: การจำลองภูมิอากาศ

**Beyond this synthetic grid:** follow the [weather, climate and ocean experiment track](../../docs/CFD_CLIMATE_OCEAN_EXPERIMENTS.md)
for miniWeather thermal/density-current cases, WRF baroclinic waves, climlab energy
balance, CMIP6 analysis, MITgcm gyres/channels and Oceananigans CPU/GPU dynamics.
The new protocols are proposed pilots, not measurements from the grid exercise below.

<!-- resource-learning:start -->
## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab

Booklet flow: pages **33–36** of the [LANTA handbook](../../docs/lanta-hpc-experience-handbook.pdf). [Full learning sequence and worksheet](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md).

<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>

![Booklet workflow: climate](../../docs/images/booklet/Part5-ScientificWorkload.png)

Original booklet illustration, not a run screenshot. [Source and limitations](../../docs/images/booklet/README.md).

</details>

### 1. ขอบเขตและการประมาณก่อนรัน

Synthetic climate grid / NetCDF summary; not a WRF forecast.

Array storage lower bound = Nx×Ny×Nz×variables×bytes/value, multiplied by simultaneously live time levels and temporaries. Output volume adds retained timesteps. Python object grids need more than raw numeric-array bytes.

### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output

Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6339753 | COMPLETED | 1 | 3 | 0.768 | 0.000833 | 16.53 |

Elapsed is summed across array elements, not array makespan. CPU used is `TotalCPU`; reserved CPU-hours include idle allocation time. MaxRSS is the largest sampled task/step value, **not total node RAM**. Missing GPU/energy telemetry must not be interpreted as zero.

![Screenshot of archived job accounting and stdout](../../docs/images/run-evidence/domain-science-chapter-22-climate-modeling-readme.png)

Browser screenshot of the [archived evidence viewer](../../docs/tutorial-evidence/domain-science-chapter-22-climate-modeling-readme.html); not a live terminal capture. Open the viewer for exact requested/allocated resources and job-specific log excerpts.

**Read the numbers:** job `6339753` used 0.768 CPU-seconds over 3 summed elapsed seconds: about **0.26 busy CPU cores per running element on average**. This describes CPU work across the whole allocation, including setup; it does not measure GPU utilization. For a seconds-long run, startup and coarse memory sampling can dominate. Do not reduce RAM to the displayed RSS or claim scaling without a longer pilot.

<details><summary>ตัวอย่าง output ที่บันทึกจริง / archived stdout excerpt</summary>

Job `6339753` · archive member `tutorials/domain-science/chapter-22-climate-modeling/README/logs/climate-grid_6339753.out`

```text
result=results/climate_grid_summary.csv
```

</details>

### 3. ขยายงานทีละแกนและตรวจความถูกต้อง

Scale the synthetic grid side length by 2 then 4 (2-D cells grow 4× then 16×). Time read, compute and write separately. A real WRF benchmark additionally needs matching WPS inputs, domain/nesting and timestep-stability validation.

**Correctness gate:** Check dimensions, units, finite values and known synthetic statistics. A valid NetCDF file does not establish a valid weather forecast.

[Public applications and research-backed experiments](../../docs/REAL_APPLICATION_EXPERIMENTS.md#miniweather) provide the next workload. Proposed resource budgets there are not measured requirements.

Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. Use three repeats and report spread; do not claim speedup from one short smoke run.

<!-- resource-learning:end -->

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/climate-grid` โดยตรง

## เป้าหมาย

1. สร้าง grid ภูมิอากาศจำลอง
2. คำนวณ temperature และ rain summary
3. บันทึก CSV สำหรับ postprocess

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/climate-grid"
cd "$HOME/hpc-ignite-standalone/climate-grid"
mkdir -p configs input jobs logs notes results src

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then
    export LANTA_CPU_PARTITION="compute-devel"
fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
```

### ขั้นที่ 2: สร้าง source code `src/climate_grid.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/climate_grid.py <<'PYCODE'
from pathlib import Path
import csv, math
Path("results").mkdir(exist_ok=True)
out = Path("results/climate_grid_summary.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["lat", "lon", "temperature_c", "rain_mm"])
    for lat in range(16, 21):
        for lon in range(98, 103): writer.writerow([lat, lon, f"{30 - 0.4 * (lat - 16) + math.sin(lon):.2f}", f"{4 + 0.5 * (lat - 16) + 0.1 * (lon - 98):.2f}"])
print(f"result={out}")
PYCODE
```


### ขั้นที่ 3: สร้าง Slurm script `jobs/climate-grid.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/climate-grid.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=climate-grid
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load Mamba/23.11.0-0 2>/dev/null || module load cray-python/3.10.10 2>/dev/null || true
set +u  # GDAL activation reads optional unset variables
conda activate netcdf-py39
set -u
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/climate_grid.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/climate-grid.sbatch)
echo "$job_id	climate-grid	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/climate-grid_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/climate-grid"
head results/climate_grid_summary.csv
tail -50 logs/climate-grid_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง

<!-- performance-rerun:start -->
## Fresh measured rerun — 26 September 2026

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6340179 | COMPLETED | 1 | 3 | 0.842 | 0.000833 | 1.75 |

These are new measured jobs, not estimates. One campaign pass does not establish scaling or runtime variance. Allocated CPU-hours are not billed SHr; sampled RSS is not total node memory.

[Accounting, output archive and measurement limitations](../../docs/lanta-runs/2026-09-26-performance/README.md)

![Browser capture of fresh measured accounting and recorded output](../../docs/lanta-runs/2026-09-26-performance/domain-science-chapter-22-climate-modeling-readme.png)
<!-- performance-rerun:end -->
