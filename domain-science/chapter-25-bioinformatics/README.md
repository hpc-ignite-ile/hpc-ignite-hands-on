# บทที่ 25: ชีวสารสนเทศศาสตร์

Chapter 25: Bioinformatics

## เริ่มรันงานจิ๋วบน LANTA

```bash
cd "$HOME/hpc-ignite-hands-on"
mkdir -p logs results
sbatch -p compute-devel domain-science/chapter-25-bioinformatics/jobs/blast_cli_smoke.sbatch
```

หลังส่ง job นี้ ผู้ใช้ควรเห็น FASTA จิ๋ว, log จาก `makeblastdb`, version ของ BLAST+ และผล `blastn` แบบ TSV

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

แปะ block นี้ใน terminal บน LANTA เพื่อสร้าง Slurm script แบบมองเห็นได้ แล้วส่ง Python example ของบทนี้เข้า queue:

```bash
cd "$HOME/hpc-ignite-hands-on"

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account, leave blank for site default: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export LAB_SCRIPT="${LAB_SCRIPT:-domain-science/chapter-25-bioinformatics/sequence_basics.py}"

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

เปลี่ยน script ได้เล็กน้อยโดยตั้ง `LAB_SCRIPT` ก่อนแปะ block เช่น `export LAB_SCRIPT=domain-science/chapter-25-bioinformatics/sequence_basics.py`
