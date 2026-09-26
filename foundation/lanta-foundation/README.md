# LANTA Foundation Lab: งานแรกที่รันได้จริง

<!-- resource-learning:start -->
## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab

Booklet flow: pages **19–23** of the [LANTA handbook](../../docs/lanta-hpc-experience-handbook.pdf). [Full learning sequence and worksheet](../../docs/RESOURCE_ESTIMATION_WORKBOOK.md).

<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>

![Booklet workflow: hello](../../docs/images/booklet/Part2-RunningJobs.png)

Original booklet illustration, not a run screenshot. [Source and limitations](../../docs/images/booklet/README.md).

</details>

### 1. ขอบเขตและการประมาณก่อนรัน

Small Slurm/environment smoke test; startup dominates its elapsed time.

One task and one CPU are sufficient for printing context and writing a small file. A 1 GiB / 5 minute initial ceiling is a teaching budget, not measured need. Reserved capacity at that ceiling is 1 × 300 / 3600 = 0.0833 CPU-hours.

### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output

Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6339637 | COMPLETED | 1 | 4 | 1.120 | 0.001111 | 4.34 |

Elapsed is summed across array elements, not array makespan. CPU used is `TotalCPU`; reserved CPU-hours include idle allocation time. MaxRSS is the largest sampled task/step value, **not total node RAM**. Missing GPU/energy telemetry must not be interpreted as zero.

![Screenshot of archived job accounting and stdout](../../docs/images/run-evidence/foundation-lanta-foundation-readme.png)

Browser screenshot of the [archived evidence viewer](../../docs/tutorial-evidence/foundation-lanta-foundation-readme.html); not a live terminal capture. Open the viewer for exact requested/allocated resources and job-specific log excerpts.

**Read the numbers:** job `6339637` used 1.120 CPU-seconds over 4 summed elapsed seconds: about **0.28 busy CPU cores per running element on average**. This describes CPU work across the whole allocation, including setup; it does not measure GPU utilization. For a seconds-long run, startup and coarse memory sampling can dominate. Do not reduce RAM to the displayed RSS or claim scaling without a longer pilot.

<details><summary>ตัวอย่าง output ที่บันทึกจริง / archived stdout excerpt</summary>

Job `6339637` · archive member `tutorials/foundation/lanta-foundation/README/logs/foundation-visible_6339637.out`

```text
{
  "commands": {
    "cc": "/usr/bin/cc",
    "python": "/opt/cray/pe/python/3.10.10/bin/python",
    "sbatch": "/usr/bin/sbatch",
    "srun": "/usr/bin/srun"
  },
  "cwd": "/lustrefs/disk/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926/tutorials/foundation/lanta-foundation/README",
[... excerpt; full log in archive ...]
    "SLURM_CPUS_PER_TASK": "1",
    "SLURM_JOB_ID": "6339637",
    "SLURM_JOB_NAME": "foundation-visible",
    "SLURM_SUBMIT_DIR": "/lustrefs/disk/project/pv915002-hpcign/wdiazcar/hpc-ignite-rerun-20260926/tutorials/foundation/lanta-foundation/README"
  }
}
result=results/environment_6339637.json
results/pi.txt
```

</details>

### 3. ขยายงานทีละแกนและตรวจความถูกต้อง

Run the unchanged job three times. Compare queue wait, job elapsed and program time separately; do not infer parallel speedup from a hello-world job.

**Correctness gate:** Match the job ID and compute hostname in the log and result. COMPLETED alone does not prove the intended program ran.

[Public applications and research-backed experiments](../../docs/REAL_APPLICATION_EXPERIMENTS.md#miniweather) provide the next workload. Proposed resource budgets there are not measured requirements.

Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. Use three repeats and report spread; do not claim speedup from one short smoke run.

<!-- resource-learning:end -->

![เส้นทางคำสั่งและข้อมูลก่อนรันงานแรกบน LANTA](../../docs/images/beginners/lanta-job-workflow.png)

ภาพแนวคิด: laptop เป็นจุดเริ่มต้น ส่วนงานหนักรันบน compute node ที่ได้รับจาก Slurm ไฟล์ผลลัพธ์ต้องอยู่ในพื้นที่ที่คุณหาและตรวจได้. อ่าน [คู่มือเริ่มต้นด้วยภาพ](../../docs/BEGINNER_VISUAL_GUIDE_TH.md) สำหรับคำอธิบายทีละขั้น

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/foundation-visible` โดยตรง

## เป้าหมาย

1. สร้างไฟล์ด้วย heredoc
2. ส่ง Slurm job แบบเห็น script
3. เก็บ JSON environment และค่า pi

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/foundation-visible"
cd "$HOME/hpc-ignite-standalone/foundation-visible"
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

### ขั้นที่ 2: สร้าง source code `src/foundation_visible.py`

ขั้นนี้สร้างไฟล์โปรแกรมหลัก ให้ผู้ใช้อ่านส่วน import, parameter, output path และ sanity check ก่อนส่งงาน

```bash
cat > src/foundation_visible.py <<'PYCODE'
from pathlib import Path
import json
import os
import platform
import shutil
import socket
import sys
Path("results").mkdir(exist_ok=True)
info = {
    "python": sys.version.split()[0],
    "executable": sys.executable,
    "host": socket.gethostname(),
    "platform": platform.platform(),
    "cwd": str(Path.cwd()),
    "slurm": {key: os.environ.get(key, "") for key in ["SLURM_JOB_ID", "SLURM_JOB_NAME", "SLURM_CPUS_PER_TASK", "SLURM_SUBMIT_DIR"]},
    "commands": {cmd: shutil.which(cmd) for cmd in ["python", "srun", "sbatch", "cc"]},
}
out = Path("results") / f"environment_{os.environ.get('SLURM_JOB_ID', 'manual')}.json"
out.write_text(json.dumps(info, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps(info, indent=2, sort_keys=True))
print(f"result={out}")
from pathlib import Path
Path("results/pi.txt").write_text("pi_smoke=3.14159\n", encoding="utf-8")
print("results/pi.txt")
PYCODE
```


### ขั้นที่ 3: สร้าง Slurm script `jobs/foundation-visible.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/foundation-visible.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=foundation-visible
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
module purge
module load cray-python/3.10.10 2>/dev/null || module load python 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
python src/foundation_visible.py | tee "results/${SLURM_JOB_ID}/output.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/foundation-visible.sbatch)
echo "$job_id	foundation-visible	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/foundation-visible_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/foundation-visible"
find results -maxdepth 2 -type f | sort
tail -80 logs/foundation-visible_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

เก็บสถิติทรัพยากรพร้อม step `.batch` ซึ่งเป็นแถวที่มี `MaxRSS`:

```bash
job_id=<jobid>
sacct -j "$job_id" -P \
  -o JobID,JobName,Account,Partition,State,ExitCode,Elapsed,TotalCPU,UserCPU,SystemCPU,AllocCPUS,ReqCPUS,ReqMem,MaxRSS,MaxVMSize,AveCPU,NodeList
```

## ตัวอย่างผลที่ตรวจบน LANTA

งาน repo smoke `6338432` รันจริงเมื่อ 2026-09-25 ด้วยบัญชี `pv915002` บน `compute-devel` และจบ `COMPLETED (0:0)` ใน 5 วินาที ขั้น `batch` ใช้ `MaxRSS=22572K` ค่า workload คือ `pi estimate=3.141592654564`, `abs error=9.742940e-10` และเวลาที่โปรแกรมวัดได้ 0.0632 วินาที ดู stdout และสถิติฉบับเต็มใน [run evidence](../../docs/lanta-runs/2026-09-25-pv915002/README.md#foundation-smoke-job-6338432)

ภาพต่อไปนี้เป็นภาพประกอบ expected result ที่สร้างจาก log จริง ไม่ใช่ภาพหลักฐานแทน raw log:

![Expected result ของ LANTA foundation smoke](../../docs/images/expected-foundation-smoke.png)

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง

<!-- performance-rerun:start -->
## Fresh measured rerun — 26 September 2026

| Job | State | Elements | Sum elapsed (s) | CPU used (s) | Reserved CPU-h | Max step/task RSS (MiB) |
|---|---|---:|---:|---:|---:|---:|
| 6340162 | COMPLETED | 1 | 4 | 1.053 | 0.001111 | 2.95 |

These are new measured jobs, not estimates. One campaign pass does not establish scaling or runtime variance. Allocated CPU-hours are not billed SHr; sampled RSS is not total node memory.

[Accounting, output archive and measurement limitations](../../docs/lanta-runs/2026-09-26-performance/README.md)

![Browser capture of fresh measured accounting and recorded output](../../docs/lanta-runs/2026-09-26-performance/foundation-lanta-foundation-readme.png)
<!-- performance-rerun:end -->
