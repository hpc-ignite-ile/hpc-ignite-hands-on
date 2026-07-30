# บทที่ 6: การสร้างภาพข้อมูล

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
mamba activate hpc-ignite-base

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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_core-hpc-chapter-06-visualization.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "core-hpc/chapter-06-visualization/matplotlib_basics.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_core-hpc-chapter-06-visualization.sh
```
