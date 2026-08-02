#!/bin/bash
#SBATCH --job-name=blast-cli-smoke
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

REPO_ROOT="${SLURM_SUBMIT_DIR:-$PWD}"
if [ ! -d "$REPO_ROOT/slurm" ]; then
    REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
fi
cd "$REPO_ROOT"

source slurm/module-loads/bio.sh
OUT="results/blast_${SLURM_JOB_ID}"
mkdir -p "$OUT"

cat > "$OUT/reference.fasta" <<'EOF'
>ref_alpha
ACGTACGTACGTACGTACGT
>ref_beta
TTTTACGTGGGGACGTCCCC
EOF

cat > "$OUT/query.fasta" <<'EOF'
>query_1
ACGTACGT
EOF

makeblastdb -in "$OUT/reference.fasta" -dbtype nucl -out "$OUT/refdb" | tee "$OUT/makeblastdb.txt"
blastn -query "$OUT/query.fasta" -db "$OUT/refdb" -outfmt "6 qseqid sseqid pident length evalue bitscore" -out "$OUT/blast_hits.tsv"
blastn -version | tee "$OUT/blast_version.txt"
cat "$OUT/blast_hits.tsv"
