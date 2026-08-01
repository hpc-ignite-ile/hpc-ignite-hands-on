# บทที่ 9: Apache Spark

Chapter 9: Apache Spark for Distributed Computing

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ Spark Architecture
2. ใช้ RDD และ Transformations
3. ประยุกต์ Spark DataFrame API
4. รัน Spark บน SLURM Cluster

## โครงสร้างไฟล์

```
chapter-09-spark/
├── README.md
├── spark_basics.py          # PySpark fundamentals
├── spark_dataframe.py       # DataFrame operations
├── spark_wordcount.py       # Classic word count
├── spark_ml_pipeline.py     # Machine learning pipeline
└── sbatch/
    └── spark_cluster.sbatch
```

## การใช้งาน

```bash
# On LANTA
module load Spark/3.3.0

# Run locally
python spark_basics.py

# Submit to SLURM
sbatch sbatch/spark_cluster.sbatch
```

## Spark Architecture

```
┌─────────────────────────────────────────────────┐
│                 Driver Program                  │
│              (SparkContext/Session)             │
└───────────────────────┬─────────────────────────┘
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
    ┌─────────┐   ┌─────────┐   ┌─────────┐
    │ Worker  │   │ Worker  │   │ Worker  │
    │  Node   │   │  Node   │   │  Node   │
    │ (Tasks) │   │ (Tasks) │   │ (Tasks) │
    └─────────┘   └─────────┘   └─────────┘
```

## Key Concepts

### Lazy Evaluation
```python
# These operations are lazy (not computed yet)
rdd = sc.textFile("data.txt")
filtered = rdd.filter(lambda x: "error" in x)
counts = filtered.map(lambda x: (x, 1))

# Action triggers computation
result = counts.collect()
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
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-09-spark/spark_basics.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-09-spark/spark_basics.py`
