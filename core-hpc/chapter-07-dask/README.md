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

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-07-dask/dask_basics.py}"

mkdir -p jobs logs results/python-labs

cat > jobs/run_python_lab.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpcig-python-lab
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
if [ -f "slurm/module-loads/base.sh" ]; then
    source slurm/module-loads/base.sh
fi
mkdir -p "results/python-labs/${SLURM_JOB_ID}"
echo "script=${LAB_SCRIPT}"
python "$LAB_SCRIPT" | tee "results/python-labs/${SLURM_JOB_ID}/output.txt"
SLURM

SBATCH_ACCOUNT=()
if [ -n "${LANTA_ACCOUNT:-}" ]; then
    SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT")
fi
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --export=ALL,LAB_SCRIPT="$LAB_SCRIPT" --parsable jobs/run_python_lab.sbatch)
echo "Submitted job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Results: find results/python-labs/${job_id} -type f -maxdepth 2 -print"
```

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-07-dask/dask_basics.py`
