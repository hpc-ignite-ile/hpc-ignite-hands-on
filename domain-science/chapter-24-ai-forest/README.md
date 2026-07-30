# บทที่ 24: AI สำหรับการปกป้องป่า

Chapter 24: AI for Forest Protection

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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-24-ai-forest.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-24-ai-forest/ndvi_analysis.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-24-ai-forest.sh
```
