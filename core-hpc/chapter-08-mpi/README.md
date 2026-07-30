# บทที่ 8: การเขียนโปรแกรม MPI ขั้นสูง

Chapter 8: Advanced MPI Programming

## วัตถุประสงค์การเรียนรู้

1. ใช้ MPI Collective Operations (Scatter, Gather, Allreduce)
2. ประยุกต์ Domain Decomposition
3. จัดการ Ghost Cells สำหรับ Stencil Operations
4. Optimize การสื่อสารด้วย Non-blocking MPI

## โครงสร้างไฟล์

```
chapter-08-mpi/
├── README.md
├── collective_ops.py        # Collective operations demo
├── domain_decomposition.py  # 1D/2D decomposition
├── heat_equation.py         # Heat diffusion simulation
├── ghost_cells.py           # Ghost cell exchange
└── sbatch/
    └── mpi_heat.sbatch
```

## MPI Collective Operations

```python
from mpi4py import MPI

comm = MPI.COMM_WORLD

# Broadcast: one-to-all
data = comm.bcast(data, root=0)

# Scatter: distribute array
local = comm.scatter(global_array, root=0)

# Gather: collect from all
global_array = comm.gather(local, root=0)

# Allreduce: reduce + broadcast
total = comm.allreduce(local_sum, op=MPI.SUM)
```

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA แล้วเลือกหมายเลข script ที่ต้องการส่งเข้า Slurm:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-08-mpi.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

LABS=(
    "core-hpc/chapter-08-mpi/collective_ops.py"
    "core-hpc/chapter-08-mpi/heat_equation.py"
)

echo "เลือก script ของบท core-hpc/chapter-08-mpi:"
select LAB_SCRIPT in "${LABS[@]}"; do
    if [ -n "${LAB_SCRIPT:-}" ]; then
        bash scripts/lanta_submit_python_lab.sh "$LAB_SCRIPT"
        break
    fi
    echo "กรุณาเลือกหมายเลขจากรายการ"
done

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-08-mpi.sh
```
