# บทที่ 20: เคมีคอมพิวเตอร์

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

Chapter 20: Computational Chemistry

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel domain-science/chapter-20-computational-chemistry/jobs/chemistry_preflight.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็นรายชื่อ group/module สำหรับเครื่องมือ chemistry ที่อาจมี license และผลจาก concept script ขนาดเล็ก

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

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-domain-science/chapter-20-computational-chemistry/molecular_basics.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=domain-science/chapter-20-computational-chemistry/molecular_basics.py`
