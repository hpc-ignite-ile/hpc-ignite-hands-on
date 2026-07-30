# บทที่ 26: เกษตรอัจฉริยะ

Chapter 26: Smart Agriculture

## วัตถุประสงค์การเรียนรู้

1. ใช้ IoT Data สำหรับการเกษตร
2. วิเคราะห์ข้อมูล Crop Yield
3. สร้าง Prediction Models
4. ประยุกต์ Remote Sensing

## โครงสร้างไฟล์

```
chapter-26-smart-agriculture/
├── README.md
├── crop_analysis.py        # Crop yield analysis
├── weather_impact.py       # Weather impact on crops
├── yield_prediction.py     # ML yield prediction
├── irrigation_scheduler.py # Smart irrigation
└── sbatch/
    └── agri_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-agri python=3.9 scikit-learn pandas numpy matplotlib
mamba activate hpc-agri

# Run examples
python crop_analysis.py
python yield_prediction.py
```

## Northern Thailand Crops

- **ข้าว (Rice)**: Main crop, rainy season
- **ลำไย (Longan)**: Major fruit export
- **ลิ้นจี่ (Lychee)**: Premium fruit
- **กาแฟ (Coffee)**: Highland crop

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-26-smart-agriculture.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-26-smart-agriculture/crop_analysis.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-26-smart-agriculture.sh
```
