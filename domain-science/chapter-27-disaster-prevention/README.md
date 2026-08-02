# บทที่ 27: การป้องกันภัยพิบัติ

Chapter 27: Disaster Prevention

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel domain-science/chapter-27-disaster-prevention/jobs/hazard_grid_smoke.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็น `hazard_grid.csv` จาก rainfall/slope assumptions เพื่อใช้คุยเรื่อง scenario และ policy ต่อ

## วัตถุประสงค์การเรียนรู้

1. วิเคราะห์ข้อมูลภัยพิบัติ
2. สร้าง Early Warning Systems
3. จำลองน้ำท่วมและดินถล่ม
4. ใช้ HPC สำหรับ Real-time Prediction

## โครงสร้างไฟล์

```
chapter-27-disaster-prevention/
├── README.md
├── disaster_data.py        # Disaster data analysis
├── flood_simulation.py     # Flood simulation
├── landslide_risk.py       # Landslide risk assessment
├── early_warning.py        # Early warning system
└── sbatch/
    └── disaster_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-disaster python=3.9 numpy scipy pandas matplotlib
mamba activate hpc-disaster

# Run examples
python disaster_data.py
python flood_simulation.py
```

## Northern Thailand Disasters

- **น้ำท่วม (Flood)**: Annual monsoon floods
- **ดินถล่ม (Landslide)**: Mountain regions
- **หมอกควัน (Haze)**: Burning season (Feb-Apr)
- **ภัยแล้ง (Drought)**: El Niño years

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-domain-science/chapter-27-disaster-prevention/flood_simulation.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=domain-science/chapter-27-disaster-prevention/flood_simulation.py`
