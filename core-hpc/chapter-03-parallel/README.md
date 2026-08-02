# บทที่ 3: การเขียนโปรแกรมแบบขนาน

Chapter 3: Parallel Programming with MPI and Multiprocessing

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel core-hpc/chapter-03-parallel/jobs/mpi_rank_smoke.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็น log ที่มี 4 MPI ranks จากคำสั่ง `srun -n 4` ก่อนขยายไป Python `mpi4py`

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ Shared Memory vs Distributed Memory
2. เขียนโปรแกรม MPI พื้นฐานด้วย mpi4py
3. ใช้ Python multiprocessing สำหรับงาน CPU-bound
4. ประยุกต์ใช้ Domain Decomposition

## โครงสร้างไฟล์

```
chapter-03-parallel/
├── README.md
├── mpi/
│   ├── hello_mpi.py           # MPI Hello World
│   ├── parallel_sum.py        # Parallel summation
│   ├── monte_carlo_pi.py      # Monte Carlo π estimation
│   ├── domain_decomposition.py # Domain decomposition example
│   └── collective_ops.py      # MPI collective operations
├── multiprocessing/
│   ├── pool_example.py        # Process pool
│   └── shared_memory.py       # Shared memory example
└── sbatch/
    ├── mpi_single_node.sbatch
    └── mpi_multi_node.sbatch
```

## การใช้งาน

### MPI Examples

```bash
# Load modules
source ../../slurm/module-loads/mpi.sh

# Create environment
mamba env create -f ../../environments/mpi.yaml
mamba activate hpc-ignite-mpi

# Run locally (4 processes)
mpirun -np 4 python mpi/hello_mpi.py

# Submit to LANTA
sbatch sbatch/mpi_single_node.sbatch
```

### Multiprocessing Examples

```bash
# No special modules needed
python multiprocessing/pool_example.py
```

## แนวคิดหลัก

### Shared Memory vs Distributed Memory

| Feature | Shared Memory | Distributed Memory |
|---------|--------------|-------------------|
| Memory | Single shared space | Separate memory per process |
| Communication | Direct memory access | Message passing (MPI) |
| Scalability | Limited to single node | Scales across nodes |
| Programming | Easier (OpenMP, threading) | More complex (MPI) |

### MPI Basic Operations

```python
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()  # Process ID
size = comm.Get_size()  # Total processes

# Point-to-point
comm.send(data, dest=1)
data = comm.recv(source=0)

# Collective
total = comm.reduce(local_sum, op=MPI.SUM, root=0)
data = comm.bcast(data, root=0)
```

## เอกสารอ้างอิง

- [Curriculum Book - Chapter 3](https://github.com/wdiazcarballo/hpc-curriculum/blob/main/docs/curriculum-book/chapters/chapter-03-parallel-programming.md)
- [mpi4py Documentation](https://mpi4py.readthedocs.io/)

## Copy-paste only บน LANTA

บทนี้เป็นแนวคิดหรือ configuration เป็นหลัก จึงไม่มี Python script ขนาดเล็กให้ส่งทันที ใช้ template ใน `docs/LAB_AUTHORING_GUIDE_TH.md` เพื่อสร้าง `src/*.py` และ `jobs/*.sbatch` ด้วย heredoc แล้วส่งด้วย `sbatch` โดยตรง
