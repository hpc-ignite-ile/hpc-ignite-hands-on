# บทที่ 25: ชีวสารสนเทศศาสตร์

Chapter 25: Bioinformatics

## วัตถุประสงค์การเรียนรู้

1. เข้าใจ DNA/Protein Sequences
2. ทำ Sequence Alignment
3. วิเคราะห์ Genomic Data
4. ใช้ BioPython

## โครงสร้างไฟล์

```
chapter-25-bioinformatics/
├── README.md
├── sequence_basics.py      # DNA/RNA/Protein basics
├── alignment.py            # Sequence alignment
├── blast_analysis.py       # BLAST search
├── phylogenetics.py        # Phylogenetic trees
└── sbatch/
    └── bioinfo_job.sbatch
```

## การใช้งาน

```bash
# Create environment
mamba create -n hpc-bioinfo python=3.9 biopython numpy matplotlib
mamba activate hpc-bioinfo

# Run examples
python sequence_basics.py
python alignment.py
```

## Key Concepts

- **DNA**: A, T, G, C nucleotides
- **RNA**: A, U, G, C (transcription)
- **Protein**: 20 amino acids (translation)
- **BLAST**: Basic Local Alignment Search Tool

## Copy-paste only บน LANTA

หมายเหตุ: block นี้ช่วยลดการพิมพ์คำสั่งและสร้าง/ส่งงานให้แบบ no-editor; ถ้า script ของบทนี้ต้องใช้ package เฉพาะ ให้เตรียม environment ตามคำอธิบายของบทก่อน submit

แปะ block นี้ใน terminal บน LANTA เพื่อส่ง script ของบทนี้เข้า Slurm โดยไม่ต้องเปิด editor:

```bash
cat > /tmp/hpc_ignite_domain-science-chapter-25-bioinformatics.sh <<'BASH'
#!/bin/bash
set -euo pipefail

cd "$HOME/hpc-ignite-hands-on"

if [ -z "${HPC_IGNITE_ACCOUNT:-}" ]; then
    read -rp "Project account for Slurm: " HPC_IGNITE_ACCOUNT
    export HPC_IGNITE_ACCOUNT
fi

export HPC_IGNITE_PARTITION="${HPC_IGNITE_PARTITION:-compute-devel}"

bash scripts/lanta_submit_python_lab.sh "domain-science/chapter-25-bioinformatics/sequence_basics.py"

echo
echo "Monitor: squeue -u $USER"
echo "Results: find results/python-labs -maxdepth 3 -type f | sort"
BASH

bash /tmp/hpc_ignite_domain-science-chapter-25-bioinformatics.sh
```
