# บทที่ 5: การประมวลผล Big Data

<!-- resource-learning:start -->
## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab

Booklet flow: pages **24–27** of the [LANTA handbook](../../docs/lanta-hpc-experience-handbook.pdf). [Full learning sequence and worksheet](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md).

<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>

![Booklet workflow: stream](../../docs/images/booklet/Part3-A-ProgrammingMatrix.png)

Original booklet illustration, not a run screenshot. [Source and limitations](../../docs/images/booklet/README.md).

</details>

### 1. ขอบเขตและการประมาณก่อนรัน

50,000-row generated CSV and serial streaming group aggregation; not a distributed Big Data engine.

Memory is mainly the parser and group dictionary, O(number of groups), rather than O(rows), because the loop streams records. Disk grows with row count × measured bytes/row. Measure generation, read/aggregate and write separately; use rows/second for throughput.

### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output

Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6339641 | COMPLETED | 1 | 3 | 0.802 | 0.001667 | 2.01 |

Elapsed is summed across array elements, not array makespan. CPU used is `TotalCPU`; reserved CPU-hours include idle allocation time. MaxRSS is the largest sampled task/step value, **not total node RAM**. Missing GPU/energy telemetry must not be interpreted as zero.

![Screenshot of archived job accounting and stdout](../../docs/images/run-evidence/core-hpc-chapter-05-big-data-readme.png)

Browser screenshot of the [archived evidence viewer](../../docs/tutorial-evidence/core-hpc-chapter-05-big-data-readme.html); not a live terminal capture. Open the viewer for exact requested/allocated resources and job-specific log excerpts.

**Read the numbers:** job `6339641` used 0.802 CPU-seconds over 3 summed elapsed seconds: about **0.27 busy CPU cores per running element on average**. This describes CPU work across the whole allocation, including setup; it does not measure GPU utilization. For a seconds-long run, startup and coarse memory sampling can dominate. Do not reduce RAM to the displayed RSS or claim scaling without a longer pilot.

<details><summary>ตัวอย่าง output ที่บันทึกจริง / archived stdout excerpt</summary>

Job `6339641` · archive member `tutorials/core-hpc/chapter-05-big-data/README/logs/bigdata-chunk_6339641.out`

```text
input_rows=50000
result=results/chunk_summary.csv
```

</details>

### 3. ขยายงานทีละแกนและตรวจความถูกต้อง

Change the generator's row count from 50k to 500k to 5M, updating the printed count too. Keep eight groups and seed 42 fixed. Compare streaming to a bounded in-memory version only after estimating memory. Extra CPUs will not accelerate this serial loop automatically.

**Correctness gate:** Sum group counts to the input row count; compare group means to the baseline within the printed rounding tolerance.

[Public applications and research-backed experiments](../../docs/REAL_APPLICATION_EXPERIMENTS.md#data-analytics) provide the next workload. Proposed resource budgets there are not measured requirements.

Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. Use three repeats and report spread; do not claim speedup from one short smoke run.

<!-- resource-learning:end -->

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/core-big-data` โดยตรง

## เป้าหมาย

1. สร้างข้อมูลจำลอง 50,000 แถว
2. ประมวลผลแบบ chunk
3. ตรวจ summary แยกตาม group

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/core-big-data"
cd "$HOME/hpc-ignite-standalone/core-big-data"
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

### ขั้นที่ 2: สร้าง source code `src/chunk_summary.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/chunk_summary.py <<'PYCODE'
from pathlib import Path
import csv
import random
Path("input").mkdir(exist_ok=True)
Path("results").mkdir(exist_ok=True)
random.seed(42)
source = Path("input/events.csv")
with source.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["event_id", "group", "value"])
    for i in range(50000): writer.writerow([i, f"G{i % 8}", f"{random.random() * 100:.4f}"])
sums, counts = {}, {}
with source.open(encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    for row in reader:
        group = row["group"]; sums[group] = sums.get(group, 0.0) + float(row["value"]); counts[group] = counts.get(group, 0) + 1
out = Path("results/chunk_summary.csv")
with out.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle); writer.writerow(["group", "count", "mean"])
    for group in sorted(sums): writer.writerow([group, counts[group], f"{sums[group] / counts[group]:.4f}"])
print("input_rows=50000"); print(f"result={out}")
PYCODE
```


### ขั้นที่ 3: สร้าง Slurm script `jobs/bigdata-chunk.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/bigdata-chunk.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=bigdata-chunk
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/chunk_summary.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/bigdata-chunk.sbatch)
echo "$job_id	bigdata-chunk	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/bigdata-chunk_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/core-big-data"
cat results/chunk_summary.csv
tail -50 logs/bigdata-chunk_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
