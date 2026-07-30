# บทที่ 23: วัสดุศาสตร์

Chapter 23: Materials Science

## วัตถุประสงค์การเรียนรู้

1. เข้าใจหลักการ DFT Calculations
2. วิเคราะห์ Crystal Structures
3. คำนวณ Electronic Properties
4. ศึกษา Material Databases

## โครงสร้างไฟล์

```
chapter-23-materials-science/
├── README.md
├── crystal_structures.py   # Crystal structure analysis
├── band_structure.py       # Band structure concepts
├── material_properties.py  # Calculate properties
└── sbatch/
    └── dft_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-materials python=3.9 ase pymatgen numpy matplotlib
mamba activate hpc-materials

# Run examples
python crystal_structures.py
python material_properties.py
```

## Key Concepts

- **DFT**: Density Functional Theory
- **Band Gap**: Energy gap between valence and conduction bands
- **Crystal Systems**: Cubic, hexagonal, tetragonal, etc.

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-23-materials-science.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-23-materials-science/crystal_structures.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-23-materials-science.sh
```
