# 00 Readiness

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

ใช้ก่อนส่งงานจริงเพื่อให้ผู้ใช้เห็น shell, filesystem, quota, account, module และ queue ตามลำดับใน booklet.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `mkdir -p`, `pwd`, `date`, `whoami`, `hostname`, `find`, `sort`, `myquota`, `sbalance`, `squeue`, `module`, `tee`, `cat` และ `tail`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน block เตรียมพื้นที่ใน [README.md](README.md) สำหรับ workspace ของกิจกรรม

## Copy-Paste

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo "host=$(hostname)"
    echo "home=$HOME"
} > notes/readiness.txt
```

### ขั้นที่ 2: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
{
    echo "== files =="
    find . -maxdepth 2 -type d | sort
    echo
    echo "== quota =="
    myquota 2>&1 || true
    echo
    echo "== balance =="
    sbalance 2>&1 || true
    echo
    echo "== queue =="
    squeue -u "$USER" 2>&1 || true
    echo
    echo "== modules =="
    module list 2>&1 || true
    module avail python 2>&1 | head -80 || true
    echo
    echo "== live module probes for real mini workflows =="
    module avail cray-python Mamba cpeCray WPS WRF WRFchem QuantumESPRESSO GROMACS GDAL BLAST+ Apptainer 2>&1 || true
} | tee notes/system-check.txt
```

### ขั้นที่ 3: สร้าง config `configs/run-small.env`

ขั้นนี้สร้างค่ากำกับการทดลอง เพื่อให้ parameter แยกจาก code และตรวจซ้ำได้

```bash
cat > configs/run-small.env <<'EOF'
INPUT=input/sample.csv
OUTPUT=results/sample-summary.csv
WORKERS=4
MODE=small
EOF
```

### ขั้นที่ 4: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
cat notes/readiness.txt
cat configs/run-small.env
```

### คำอธิบาย

ก่อนส่งงานแรก ให้ผู้ใช้ตรวจชื่อเครื่อง โฟลเดอร์ปัจจุบัน และสถานะ quota/account คำสั่งนี้จะบันทึกข้อมูลพื้นฐานลงใน `notes/readiness.txt` และบันทึก quota, balance, queue, module ลงใน `notes/system-check.txt`

จากนั้น block จะสร้าง `configs/run-small.env` เป็นไฟล์กำกับการทดลองตัวอย่าง ผู้ใช้จะเห็นรูปแบบ `KEY=value` ซึ่งใช้ซ้ำได้ในงานวิทยาศาสตร์จริง เช่น input, output, จำนวน worker และ mode ของการรัน

เมื่อสำเร็จ ผู้ใช้ควรเห็นไฟล์ `notes/readiness.txt`, `notes/system-check.txt`, และ `configs/run-small.env` หาก `myquota` หรือ `sbalance` แสดง error ให้เก็บข้อความนั้นไว้ก่อน แล้วตรวจต่อด้วย `df -h` หรือ `squeue -u "$USER"` เมื่อคำสั่ง `module` error ให้ logout แล้ว login ใหม่ก่อนเริ่มส่ง job

## Check

```bash
find notes configs -maxdepth 2 -type f | sort
tail -40 notes/system-check.txt
```

### คำอธิบาย

หลังจากรัน block แรกแล้ว ให้ผู้ใช้ตรวจไฟล์ที่สร้างขึ้นด้วย `find` และอ่านท้ายไฟล์ `notes/system-check.txt` ด้วย `tail`

จุดสำคัญคือผู้ใช้ต้องอ่านหลักฐานในไฟล์นี้ เพราะ quota, account, queue และ module มีผลต่อ job ถัดไปโดยตรง

เมื่อรายการไฟล์ยังขาด ให้ตรวจ `pwd` ก่อน เพราะสาเหตุที่พบบ่อยคือแปะคำสั่งในคนละโฟลเดอร์ หาก `tail` แจ้งว่าไฟล์หาย ให้กลับไปรัน block เตรียม readiness ใหม่ให้ครบก่อนเดินต่อ
