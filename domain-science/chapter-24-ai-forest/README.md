# บทที่ 24: AI สำหรับการปกป้องป่า

Chapter 24: AI for Forest Protection

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel domain-science/chapter-24-ai-forest/jobs/gdal_forest_smoke.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็น metadata shapefile ไทยจาก shared WPS static data ถ้ามี และไฟล์ CSV ของ NDVI grid จิ๋ว

## วัตถุประสงค์การเรียนรู้

1. ใช้ Computer Vision สำหรับ Remote Sensing
2. วิเคราะห์ภาพถ่ายดาวเทียม
3. ตรวจจับการเปลี่ยนแปลงพื้นที่ป่า
4. สร้าง Early Warning System

## โครงสร้างไฟล์

```
chapter-24-ai-forest/
├── README.md
├── satellite_basics.py     # Satellite image processing
├── forest_change.py        # Forest change detection
├── ndvi_analysis.py        # NDVI vegetation index
├── fire_detection.py       # Fire hotspot detection
└── sbatch/
    └── forest_gpu.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-forest python=3.9 rasterio pytorch torchvision numpy matplotlib
mamba activate hpc-forest

# Run examples
python ndvi_analysis.py
python forest_change.py
```

## Key Vegetation Indices

- **NDVI** = (NIR - Red) / (NIR + Red)
- **EVI** = Enhanced Vegetation Index
- **NDWI** = Normalized Difference Water Index

## Copy-paste only บน LANTA

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-domain-science/chapter-24-ai-forest/ndvi_analysis.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=domain-science/chapter-24-ai-forest/ndvi_analysis.py`
