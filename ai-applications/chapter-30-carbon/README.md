# บทที่ 30: Carbon Footprint และ HPC

Chapter 30: Carbon Verification with HPC

## วัตถุประสงค์การเรียนรู้

1. คำนวณ Carbon Footprint ของ HPC Jobs
2. เข้าใจ Green Computing
3. ใช้ Blockchain สำหรับ Carbon Verification
4. Optimize for Energy Efficiency

## โครงสร้างไฟล์

```
chapter-30-carbon/
├── README.md
├── carbon_calculator.py    # Carbon footprint calculator
├── energy_efficiency.py    # Energy optimization
├── green_scheduling.py     # Green job scheduling
└── sbatch/
    └── carbon_tracked.sbatch
```

## การใช้งาน

```bash
# Calculate carbon footprint
python carbon_calculator.py --job-id 12345

# Optimize for energy
python energy_efficiency.py --gpu-hours 100
```

## LANTA Energy Facts

- Power Usage Effectiveness (PUE): ~1.3
- Cooling: Liquid cooling for GPU nodes
- Location: Thailand (grid carbon intensity varies)

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_ai-applications-chapter-30-carbon.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "ai-applications/chapter-30-carbon/carbon_calculator.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_ai-applications-chapter-30-carbon.sh
```
