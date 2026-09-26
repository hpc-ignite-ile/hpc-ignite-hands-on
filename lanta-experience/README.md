# LANTA Experience Labs

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

![ภาพรวมการเรียนจากเชื่อมต่อจนถึงประเมินผล](../docs/images/beginners/tutorial-overview.png)

ภาพแนวคิดสำหรับผู้เริ่มต้น: Connect → Prepare → Submit → Run → Check → Improve ทำงานเล็กให้ครบวงจรก่อนเพิ่มขนาด. อ่าน [คู่มือเริ่มต้นด้วยภาพ](../docs/BEGINNER_VISUAL_GUIDE_TH.md) สำหรับคำอธิบายทีละขั้น

ผลรันซ้ำ LANTA บัญชี `pv915002` วันที่ 2026-09-26: [สถานะ ขอบเขต ผลลัพธ์ และ resource usage](../docs/lanta-runs/2026-09-26-pv915002/README.md) · [วิธีประเมินและปรับปรุง performance](../docs/PERFORMANCE_EVALUATION_OPTIMIZATION_TH.md)

ลำดับนี้ตาม booklet `LANTA HPC Handbook` สำหรับ LANTA HPC Experience Day: On the Move ให้ผู้ใช้แปะคำสั่งทีละ block และตรวจไฟล์จริงที่สร้างขึ้น เช่น `src/*.py`, `jobs/*.sbatch`, `configs/*`, `logs/*`, `results/*`, และ `notes/*`

คำสั่งและ syntax ใน lab ชุดนี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `cd`, `mkdir -p`, heredoc, `export`, `sbatch`, `squeue`, `sacct`, `srun`, `tail` และตัวแปร `SLURM_*`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน setup block ด้านล่างเพื่อเตรียม workspace กลางของกิจกรรม

## Event Flow

| ช่วงใน booklet | Lab ใน repo | ผลลัพธ์ที่ควรมี |
|---|---|---|
| Linux, Shell, files | [00-readiness.md](00-readiness.md) | workspace, input/config/log/result folders, environment notes |
| First Slurm job | [01-first-slurm-job.md](01-first-slurm-job.md) | `jobs/hello_lanta.sbatch`, job id, `results/hello_<jobid>.txt` |
| CPU and job array | [02-cpu-array.md](02-cpu-array.md) | CPU baseline, parameter CSV, Slurm array logs |
| OpenMP and MPI | [03-openmp-mpi.md](03-openmp-mpi.md) | compiled C examples launched by `srun` |
| Scientific/data workflow | [04-science-data.md](04-science-data.md) | model/data outputs with run evidence |
| AI/GPU check | [05-ai-gpu.md](05-ai-gpu.md) | GPU allocation log, `nvidia-smi`, PyTorch CUDA check |
| Data and resource logs | [06-run-logs.md](06-run-logs.md) | data summary, checksums, Slurm resource-spent report |

## Working Pattern

Every activity follows the same visible pattern:

1. `cd` to an event workspace.
2. Create folders with `mkdir -p`.
3. Create small scripts with `cat > file <<'EOF'`.
4. Submit directly with `sbatch -A "$LANTA_ACCOUNT"`.
5. Read `squeue`, `sacct`, `logs/`, `results/`, and `notes/`.
6. Finish with a data-summary log and a resource-spent log.

Use this setup once after SSH to LANTA:

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi

export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LANTA_GPU_PARTITION="${LANTA_GPU_PARTITION:-gpu-devel}"

mkdir -p configs input jobs logs notes results src
pwd
```

### คำอธิบาย

ก่อนเริ่ม lab ให้ผู้ใช้สร้างโฟลเดอร์ `lanta-experience` ไว้เป็นพื้นที่ทำงานหลัก จากนั้นสร้างโฟลเดอร์ย่อย `configs`, `input`, `jobs`, `logs`, `notes`, `results`, และ `src` ให้ครบ เพื่อแยกไฟล์คำสั่ง ไฟล์งาน ผลลัพธ์ และบันทึกออกจากกัน

ในขั้นตอนนี้ ผู้ใช้ตั้งค่า `LANTA_ACCOUNT`, `LANTA_CPU_PARTITION`, และ `LANTA_GPU_PARTITION` ให้พร้อมก่อนส่ง job ตัวแปรเหล่านี้จะถูกใช้ซ้ำใน lab ถัดไป ทำให้ account และ partition คงที่ตลอดกิจกรรม

เมื่อตรวจสอบ ให้ใช้ `pwd` เพื่อดูว่าผู้ใช้อยู่ใน path ที่ลงท้ายด้วย `lanta-experience` และใช้ `ls` หรือ `find . -maxdepth 1 -type d` เพื่อดูว่าโฟลเดอร์มาตรฐานถูกสร้างครบ หาก path คลาดจากที่ตั้งใจ ให้กลับไปตรวจ `$HOME` ด้วย `echo "$HOME"` แล้วรัน block เตรียมพื้นที่ใหม่อีกครั้ง

If your project policy requires a different partition, set it before submitting:

```bash
export LANTA_CPU_PARTITION=compute
export LANTA_GPU_PARTITION=gpu
```

### คำอธิบาย

หลังจาก smoke test สำเร็จแล้ว ผู้ใช้สามารถเปลี่ยน partition จาก `compute-devel` เป็น `compute` หรือจาก `gpu-devel` เป็น `gpu` ได้ ควรเปลี่ยนเฉพาะเมื่อ job เล็กทำงานถูกต้องแล้ว

ให้ผู้ใช้เพิ่มขนาดงานทีละอย่าง เช่น เปลี่ยน partition ก่อน แล้วค่อยเพิ่มเวลา CPU หรือ GPU ในรอบถัดไป วิธีนี้ช่วยให้รู้ว่าการเปลี่ยนค่าใดทำให้เวลารันหรือสถานะงานเปลี่ยนไป

การตั้งค่าสำเร็จเมื่อ `echo "$LANTA_CPU_PARTITION" "$LANTA_GPU_PARTITION"` แสดงค่าที่ต้องการ และ job ถัดไปปรากฏใน partition นั้นจริงจาก `squeue` หาก job ค้าง ให้ดู reason ด้วย `squeue -j <job-id> -o "%.18i %.9P %.20j %.8T %.20R"` ก่อนเพิ่มทรัพยากร
