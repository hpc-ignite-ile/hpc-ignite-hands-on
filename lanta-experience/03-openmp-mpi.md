# 03 OpenMP And MPI

ในบทนี้ผู้ใช้จะรัน OpenMP เพื่อดู thread ใน node เดียว และรัน MPI เพื่อดูหลาย process ที่สื่อสารกันผ่าน `srun`.

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `cc`, `srun`, `module load cpeCray`, `OMP_NUM_THREADS`, `#SBATCH --ntasks` และ `#SBATCH --cpus-per-task`

เริ่มจาก SSH ตาม [../LANTA_SETUP.md#1-ssh-to-lanta](../LANTA_SETUP.md#1-ssh-to-lanta) แล้วรัน block เตรียมพื้นที่ใน [README.md](README.md) สำหรับ workspace ของกิจกรรม

## Copy-Paste OpenMP

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

cat > src/omp_hello.c <<'C'
#include <stdio.h>
#include <omp.h>

int main(void) {
    #pragma omp parallel
    {
        int tid = omp_get_thread_num();
        int nthreads = omp_get_num_threads();
        printf("hello from thread %d of %d\n", tid, nthreads);
    }
    return 0;
}
C

cat > jobs/omp_hello.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=omp_hello
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/omp_%j.out
#SBATCH --error=logs/omp_%j.err

set -euo pipefail
module purge
module load cpeCray/25.03 2>/dev/null || module load gcc 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p results
cc -fopenmp src/omp_hello.c -o results/omp_hello
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OMP_PLACES=cores
export OMP_PROC_BIND=close
srun -c "${SLURM_CPUS_PER_TASK:-1}" results/omp_hello | sort
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/omp_hello.sbatch)
echo "$job_id	omp_hello	$(date -Is)" >> notes/job-history.tsv
echo "Submitted OpenMP job: $job_id"
echo "Read: tail -50 logs/omp_${job_id}.out"
```

### คำอธิบาย

ในขั้นตอนนี้ ผู้ใช้จะ compile โปรแกรม C ที่ใช้ OpenMP แล้วรันบน node เดียว โปรแกรมจะพิมพ์ข้อความจากแต่ละ thread เพื่อให้เห็นจำนวน thread ที่เกิดขึ้นจริง

Slurm script ขอ `--cpus-per-task=4` แล้วตั้ง `OMP_NUM_THREADS` จากค่านี้ ผู้ใช้จึงเห็นความสัมพันธ์ระหว่าง CPU ที่ขอจาก Slurm กับ thread ที่โปรแกรมใช้จริง

เมื่อสำเร็จ log จะมีข้อความ `hello from thread ...` หลายบรรทัด และมีไฟล์ binary `results/omp_hello` เมื่อ compile error ที่ `omp.h` ให้ตรวจ compiler module เมื่อได้ thread เพียงตัวเดียว ให้ตรวจ `OMP_NUM_THREADS` และ `#SBATCH --cpus-per-task`

## Copy-Paste MPI

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"

cat > src/mpi_hello.c <<'C'
#include <mpi.h>
#include <stdio.h>

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    char name[MPI_MAX_PROCESSOR_NAME];
    int len = 0;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Get_processor_name(name, &len);
    printf("rank %d of %d on %s\n", rank, size, name);
    MPI_Finalize();
    return 0;
}
C

cat > jobs/mpi_hello.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=mpi_hello
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:10:00
#SBATCH --output=logs/mpi_%j.out
#SBATCH --error=logs/mpi_%j.err

set -euo pipefail
module purge
module load cpeCray/25.03 2>/dev/null || module load cray-mpich 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p results
cc src/mpi_hello.c -o results/mpi_hello
srun -n "${SLURM_NTASKS:-4}" results/mpi_hello | sort
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --parsable jobs/mpi_hello.sbatch)
echo "$job_id	mpi_hello	$(date -Is)" >> notes/job-history.tsv
echo "Submitted MPI job: $job_id"
echo "Read: tail -50 logs/mpi_${job_id}.out"
```

### คำอธิบาย

ในขั้นตอนนี้ ผู้ใช้จะ compile โปรแกรม MPI แล้วรันด้วย `srun -n 4` โปรแกรมจะให้แต่ละ rank พิมพ์ลำดับของตนเอง จำนวน process ทั้งหมด และชื่อเครื่องที่รันอยู่

ตัวอย่างนี้เริ่มจาก 1 node และ 4 tasks เพื่อให้ตรวจง่ายก่อนขยายไปหลาย node การใช้ `srun` ทำให้ Slurm เป็นผู้จัดการ rank และทรัพยากรของงานโดยตรง

เมื่อสำเร็จ log จะมี 4 บรรทัดจาก `rank 0 of 4` ถึง rank สุดท้าย เมื่อ compile error ที่ `mpi.h` ให้ตรวจ `cpeCray` หรือ MPI module เมื่อจำนวน rank คลาดจากที่ขอ ให้ตรวจ `#SBATCH --ntasks` และคำสั่ง `srun -n`
