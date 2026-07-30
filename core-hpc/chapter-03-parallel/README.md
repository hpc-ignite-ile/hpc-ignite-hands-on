# บทที่ 3: การเขียนโปรแกรมแบบขนาน

Chapter 3: Parallel Programming with MPI and Multiprocessing

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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

บทนี้ยังไม่มี Python script แบบ standalone ในโฟลเดอร์เดียวกัน แต่ผู้เรียนสามารถเปิดเนื้อหาแบบไม่ใช้ editor ได้ด้วย block นี้:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-03-parallel.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

echo "อ่าน lab: core-hpc/chapter-03-parallel"
echo "ไฟล์ในบทนี้:"
find "core-hpc/chapter-03-parallel" -maxdepth 1 -type f | sort
echo
echo "README preview:"
sed -n '1,180p' "core-hpc/chapter-03-parallel/README.md"
echo
echo "ถ้าจะเพิ่ม runnable Slurm lab ให้ใช้ template: docs/LAB_AUTHORING_GUIDE_TH.md"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-03-parallel.sh
```
