# บทที่ 20: เคมีคอมพิวเตอร์

Chapter 20: Computational Chemistry

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ Molecular Structure และ Energy Calculations
2. ใช้ RDKit สำหรับ Cheminformatics
3. คำนวณ Molecular Properties
4. วิเคราะห์ Drug-like Properties

## โครงสร้างไฟล์

```
chapter-20-computational-chemistry/
├── README.md
├── molecular_basics.py      # Basic molecular structures
├── property_calculation.py  # Calculate molecular properties
├── similarity_search.py     # Molecular similarity
├── drug_analysis.py         # Drug-likeness analysis
└── sbatch/
    └── chem_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-chem python=3.9 rdkit numpy pandas matplotlib
mamba activate hpc-chem

# Run examples
python molecular_basics.py
python property_calculation.py
```

## Dependencies

- RDKit: Cheminformatics
- NumPy: Numerical computing
- Pandas: Data handling
- Matplotlib: Visualization

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-20-computational-chemistry.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-20-computational-chemistry/molecular_basics.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-20-computational-chemistry.sh
```
