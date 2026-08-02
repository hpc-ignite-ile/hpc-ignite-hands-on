# บทที่ 8: MPI บน LANTA

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/core-mpi-collective` โดยตรง

## เป้าหมาย

1. compile โปรแกรม MPI
2. รันหลาย rank ด้วย Slurm
3. ตรวจ output ตามจำนวน rank

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-standalone/core-mpi-collective"
cd "$HOME/hpc-ignite-standalone/core-mpi-collective"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then export LANTA_CPU_PARTITION="compute-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi

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

cat > jobs/mpi_collective.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=mpi-collective
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
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/mpi_collective.sbatch)
echo "$job_id	mpi_collective	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -50 logs/mpi-collective_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/core-mpi-collective"
find results -maxdepth 2 -type f | sort
tail -50 logs/mpi-collective_*.out
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
