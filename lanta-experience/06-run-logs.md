# 06 Data Summary And Resource Logs

<!-- resource-learning:start -->
## จากงานเล็กสู่การทดลองที่วัดผลได้ / Resource lab

Booklet flow: pages **5–18** of the [LANTA handbook](../docs/lanta-hpc-experience-handbook.pdf). [Full learning sequence and worksheet](../docs/RESOURCE_ESTIMATION_WORKBOOK.md).

<details><summary>ภาพแนวคิดจาก booklet / workflow illustration</summary>

![Booklet workflow: orientation](../docs/images/booklet/Part1-FirstDayKnowingHPC.png)

Original booklet illustration, not a run screenshot. [Source and limitations](../docs/images/booklet/README.md).

</details>

### 1. ขอบเขตและการประมาณก่อนรัน

Access, filesystem and environment checks; not a compute benchmark.

No GPU is needed. File/module checks need no compute allocation; use the existing one-CPU Slurm smoke job to prove compute-node access. Budget storage from input + output + checkpoints, not input alone.

### 2. ทรัพยากรที่ใช้จริงและตัวอย่าง output

Archived LANTA evidence, **2026-09-26**, account `pv915002`; these are historical measurements, not a new run or a future performance promise.

No page-specific Slurm run is recorded for this setup/reading page. Do not invent usage numbers or a successful-run screenshot. Collect evidence from the next executable lesson using the worksheet.

### 3. ขยายงานทีละแกนและตรวจความถูกต้อง

Record account, quota, module versions and a small job ID before moving to CPU scaling. Do not run a CPU stress test on a login node.

**Correctness gate:** Confirm the compute hostname, intended account, output file and exit status. Redact tokens and private keys from evidence.

[Public applications and research-backed experiments](../docs/REAL_APPLICATION_EXPERIMENTS.md#miniweather) provide the next workload. Proposed resource budgets there are not measured requirements.

Before the next run, write down input size, expected time/RAM, requested CPUs/GPUs, and a stop condition. Afterwards record job ID, actual allocation, elapsed, CPU time, memory, result check and one change for the next run. Use three repeats and report spread; do not claim speedup from one short smoke run.

<!-- resource-learning:end -->

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

ใช้หลังจากรัน lab ครบแล้ว เพื่อรวมหลักฐานของข้อมูล ผลลัพธ์ และทรัพยากรที่ใช้ไว้ใน `notes/`.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `date`, `tee`, `find`, `head`, `wc`, `sha256sum`, `cut`, `paste`, `sacct`, `sbalance` และ `sbill`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน block เตรียมพื้นที่ใน [README.md](README.md) สำหรับ workspace ของกิจกรรม

## Copy-Paste

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-experience"
mkdir -p notes results

RUN_STAMP=$(date +%Y%m%d-%H%M%S)
DATA_LOG="notes/data-summary-${RUN_STAMP}.txt"
SPENT_LOG="notes/resource-spent-${RUN_STAMP}.tsv"

{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo
    echo "job history"
    cat notes/job-history.tsv 2>/dev/null || echo "notes/job-history.tsv not found"
    echo
    echo "result files"
    find results -maxdepth 2 -type f | sort
    echo
    echo "sensor summary"
    if [ -f results/sensor_summary.csv ]; then
        cat results/sensor_summary.csv
    else
        echo "missing results/sensor_summary.csv"
    fi
```

### ขั้นที่ 2: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
    echo
    echo "diffusion summaries"
    for file in results/diffusion_*.csv; do
        [ -f "$file" ] || continue
        echo "$file"
        head -5 "$file"
        echo "lines=$(wc -l < "$file")"
    done
    echo
    echo "checksums"
    sha256sum input/sensor.csv results/sensor_summary.csv 2>/dev/null || true
    sha256sum results/hello_*.txt results/pi_*.txt results/diffusion_*.csv 2>/dev/null || true
} | tee "$DATA_LOG"
```

### ขั้นที่ 3: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
if [ -s notes/job-history.tsv ]; then
    JOB_IDS=$(cut -f1 notes/job-history.tsv | paste -sd, -)
    sacct -j "$JOB_IDS" --format=JobID,JobName%24,Partition,Account,State,ExitCode,Elapsed,AllocCPUS,ReqMem,MaxRSS,AllocTRES%80 -P > "$SPENT_LOG"
else
    echo "No job history yet" > "$SPENT_LOG"
fi

sbalance 2>&1 | tee "notes/balance-${RUN_STAMP}.txt" || true
sbill 2>&1 | tee "notes/bill-${RUN_STAMP}.txt" || true
```

### ขั้นที่ 4: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
echo "Data summary: $DATA_LOG"
echo "Resource spent: $SPENT_LOG"
head -30 "$SPENT_LOG"
```

### คำอธิบาย

หลังจากรัน lab หลายงานแล้ว ให้ผู้ใช้รวมหลักฐานไว้ใน `notes/` คำสั่งนี้อ่าน `notes/job-history.tsv`, แสดงรายชื่อไฟล์ใน `results/`, สรุปไฟล์ sensor และ diffusion และสร้าง checksum ให้ผลลัพธ์สำคัญ

จากนั้น block ใช้ `sacct` เพื่อดึงข้อมูลทรัพยากรของ job เช่น partition, state, elapsed time, CPU, memory และ exit code และบันทึก `sbalance` กับ `sbill` พร้อม timestamp

เมื่อสำเร็จ ผู้ใช้จะได้ไฟล์ `notes/data-summary-<เวลา>.txt`, `notes/resource-spent-<เวลา>.tsv`, `notes/balance-<เวลา>.txt`, และ `notes/bill-<เวลา>.txt` เมื่อ resource log ว่าง ให้ตรวจว่า `notes/job-history.tsv` มี job id เมื่อ `sacct` ยังรอข้อมูล job ใหม่ ให้รอสักครู่แล้วรันซ้ำ
