# บทที่ 7: Dask สำหรับการประมวลผลแบบขนาน

Chapter 7: Dask for Parallel Computing

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ Lazy Evaluation และ Task Graphs
2. ใช้ Dask Arrays และ DataFrames
3. ตั้งค่า Dask Distributed บน SLURM
4. ประมวลผลข้อมูลขนาดใหญ่กว่า RAM

## โครงสร้างไฟล์

```
chapter-07-dask/
├── README.md
├── dask_basics.py          # Dask fundamentals
├── dask_dataframe.py       # Large CSV processing
├── dask_array.py           # Large array operations
├── dask_slurm_cluster.py   # SLURM cluster setup
└── sbatch/
    └── dask_distributed.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba env create -f ../../environments/dask.yaml
mamba activate hpc-ignite-dask

# Run examples
python dask_basics.py
python dask_dataframe.py

# On SLURM cluster
sbatch sbatch/dask_distributed.sbatch
```

## แนวคิดหลัก

### Lazy Evaluation

```python
import dask.array as da

# This doesn't compute yet
x = da.random.random((10000, 10000), chunks=(1000, 1000))
y = x + x.T
z = y.mean()

# This triggers computation
result = z.compute()
```

### Dask on SLURM

```python
from dask_jobqueue import SLURMCluster
from dask.distributed import Client

cluster = SLURMCluster(
    cores=32,
    memory="64GB",
    walltime="01:00:00"
)
cluster.scale(jobs=4)  # 4 SLURM jobs
client = Client(cluster)
```

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-07-dask.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "core-hpc/chapter-07-dask/dask_basics.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-07-dask.sh
```
