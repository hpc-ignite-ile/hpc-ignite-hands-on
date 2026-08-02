# บทที่ 3: การเขียนโปรแกรมแบบขนาน

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/core-mpi-rank` โดยตรง

## เป้าหมาย

1. compile โปรแกรม MPI ขนาดเล็ก
2. รัน 4 ranks ด้วย srun
3. ตรวจจำนวน rank จาก log

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/core-mpi-rank"
cd "$HOME/hpc-ignite-standalone/core-mpi-rank"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then export LANTA_CPU_PARTITION="compute-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi
```

### ขั้นที่ 2: สร้างไฟล์ `src/mpi_hello.c`

ขั้นนี้ทำงานหนึ่งส่วนของ workflow ให้แปะและตรวจผลก่อนขยับไปขั้นถัดไป

```bash
cat > src/mpi_hello.c <<'C_CODE'
#include <mpi.h>
#include <stdio.h>
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size; char name[MPI_MAX_PROCESSOR_NAME]; int len = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size); MPI_Get_processor_name(name, &len);
    printf("rank %d of %d on %s\n", rank, size, name);
    MPI_Finalize(); return 0;
}
C_CODE
```


### ขั้นที่ 3: สร้าง Slurm script `jobs/mpi_rank.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/mpi_rank.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=mpi-rank
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load cpeCray/25.03 2>/dev/null || module load cray-mpich 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p "results/${SLURM_JOB_ID}"
cc src/mpi_hello.c -o "results/${SLURM_JOB_ID}/mpi_hello"
srun -n "$SLURM_NTASKS" "results/${SLURM_JOB_ID}/mpi_hello" | sort | tee "results/${SLURM_JOB_ID}/ranks.txt"
SLURM
```

### ขั้นที่ 4: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/mpi_rank.sbatch)
echo "$job_id	mpi_rank	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -50 logs/mpi-rank_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/core-mpi-rank"
find results -maxdepth 2 -type f | sort
tail -50 logs/mpi-rank_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
