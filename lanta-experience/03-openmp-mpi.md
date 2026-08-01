# 03 OpenMP And MPI

ใช้เมื่อต้องการให้ผู้เรียนเห็นความต่างระหว่าง thread ใน node เดียวกับหลาย process ที่สื่อสารผ่าน MPI.

## Copy-Paste OpenMP

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
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
srun -c "${SLURM_CPUS_PER_TASK:-1}" results/omp_hello | sort
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/omp_hello.sbatch)
echo "$job_id	omp_hello	$(date -Is)" >> notes/job-history.tsv
echo "Submitted OpenMP job: $job_id"
echo "Read: tail -50 logs/omp_${job_id}.out"
```

### คำอธิบายเชิงเรื่องเล่า

OpenMP เป็นบทเรียนเรื่องความขนานภายใน node เดียว โปรแกรม C ขนาดเล็กนี้ให้แต่ละ thread แนะนำตัวเอง แล้ว Slurm script ขอ 4 CPU cores เพื่อให้จำนวน thread ที่เกิดขึ้นมีพื้นฐานจากทรัพยากรที่ระบบจัดสรร ไม่ใช่จากความบังเอิญของ shell ที่ผู้ใช้เปิดอยู่

การ compile ด้วย `cc -fopenmp` สะท้อนแนวปฏิบัติบน LANTA ที่ควรใช้ compiler wrapper หรือ compiler จาก module ที่ตั้งใจโหลดไว้ การตั้ง `OMP_NUM_THREADS` จาก `SLURM_CPUS_PER_TASK` ทำให้ code เคารพคำขอทรัพยากร และ `srun -c` ทำให้ Slurm เห็นการใช้ CPU ต่อ task อย่างสอดคล้องกัน

เมื่อสำเร็จ log จะมีข้อความจาก thread หลายบรรทัด โดยจำนวนควรสัมพันธ์กับ CPU ที่ขอไว้ และ binary `results/omp_hello` จะถูกสร้าง หากเจอปัญหา `omp.h` ให้ตรวจ module compiler ด้วย `module avail gcc` หรือใช้ `cpeCray` หากได้ thread เพียงตัวเดียว ให้กลับไปอ่านค่า `OMP_NUM_THREADS` และ `#SBATCH --cpus-per-task` เพราะสองค่านี้คือสะพานระหว่าง Slurm กับโปรแกรม

## Copy-Paste MPI

```bash
cd "$HOME/lanta-experience"
mkdir -p jobs logs notes results src

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
module load cpeCray/25.03 2>/dev/null || module load cray-mpich 2>/dev/null || module load OpenMPI 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
mkdir -p results
if command -v mpicc >/dev/null 2>&1; then
    mpicc src/mpi_hello.c -o results/mpi_hello
else
    cc src/mpi_hello.c -o results/mpi_hello
fi
srun -n "${SLURM_NTASKS:-4}" results/mpi_hello | sort
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "${LANTA_CPU_PARTITION:-compute-devel}" --parsable jobs/mpi_hello.sbatch)
echo "$job_id	mpi_hello	$(date -Is)" >> notes/job-history.tsv
echo "Submitted MPI job: $job_id"
echo "Read: tail -50 logs/mpi_${job_id}.out"
```

### คำอธิบายเชิงเรื่องเล่า

เมื่อ OpenMP อยู่ภายใน node เดียว MPI คือการเปิดประตูสู่หลาย process ที่อาจกระจายไปหลาย node ได้ โปรแกรมนี้ให้แต่ละ rank บอกลำดับของตน จำนวน process ทั้งหมด และชื่อเครื่องที่ตนรันอยู่ จึงเป็นหลักฐานแรกของ distributed-memory execution ที่จับต้องได้

การใช้ `srun` ภายใน Slurm allocation เป็นแนวทางที่เหมาะกับ LANTA เพราะ Slurm เป็นผู้ถือข้อมูลว่าจัดสรร task ไว้ที่ใด การเริ่มจาก 1 node และ 4 tasks ทำให้ผู้เรียนตรวจจำนวน rank ได้ง่ายก่อนขยายไปหลาย node การ load compiler และ MPI module ภายใน job script ช่วยให้การ compile และ run เกิดภายใต้ environment เดียวกับที่บันทึกใน log

งานสำเร็จเมื่อ log มี 4 บรรทัดจาก `rank 0 of 4` ถึง rank สุดท้าย และจำนวนบรรทัดตรงกับ `SLURM_NTASKS` หาก compile ไม่พบ `mpi.h` ให้ตรวจ module MPI หรือ Cray Programming Environment หากจำนวน rank ไม่ตรงกับที่ขอ ให้ย้อนดู `#SBATCH --ntasks` และคำสั่ง `srun -n` หากข้าม node แล้วประสิทธิภาพไม่ดี ให้กลับมาวัด baseline บน node เดียวก่อน เพื่อแยกปัญหา computation ออกจาก communication
