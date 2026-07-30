# บทที่ 27: การป้องกันภัยพิบัติ

Chapter 27: Disaster Prevention

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

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-27-disaster-prevention.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-27-disaster-prevention/flood_simulation.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-27-disaster-prevention.sh
```
