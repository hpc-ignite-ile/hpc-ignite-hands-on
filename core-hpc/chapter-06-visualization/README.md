# บทที่ 6: การสร้างภาพข้อมูล

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

Chapter 6: Data Visualization

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ Data-Ink Ratio
2. ใช้ Matplotlib สร้างกราฟพื้นฐาน
3. สร้าง Interactive Visualization
4. เลือกประเภทกราฟที่เหมาะสม

## โครงสร้างไฟล์

```
chapter-06-visualization/
├── README.md
├── matplotlib_basics.py     # Basic plotting
├── chart_types.py           # Different chart types
├── hpc_dashboard.py         # HPC monitoring visualization
├── publication_quality.py   # Publication-ready figures
└── sbatch/
    └── viz_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba env create -f ../../environments/base.yaml
mamba activate hpc-ignite

# Run examples
python matplotlib_basics.py
python chart_types.py

# Generate figures (saves to PNG)
python hpc_dashboard.py --output dashboard.png
```

## หลักการ Data-Ink Ratio

> "Above all else, show the data" - Edward Tufte

Data-Ink Ratio = (ink used for data) / (total ink)

เป้าหมาย: ลด "chartjunk" ให้เหลือน้อยที่สุด

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-core-hpc/chapter-06-visualization/matplotlib_basics.py}"

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
if [ -f "slurm/module-loads/netcdf-python.sh" ]; then
    source slurm/module-loads/netcdf-python.sh
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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=core-hpc/chapter-06-visualization/matplotlib_basics.py`
