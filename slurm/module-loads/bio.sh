#!/bin/bash
# Bioinformatics CLI modules for miniature LANTA workflows.
# Usage: source slurm/module-loads/bio.sh

if ! command -v module >/dev/null 2>&1; then
    echo "Lmod 'module' command not found; using current shell environment."
    return 0 2>/dev/null || exit 0
fi

module purge
module load BLAST+/2.14.0-cpeGNU-23.03 2>/dev/null || true
module load SAMtools/1.22.1-cpeGNU-25.03 2>/dev/null || true
module load BWA/0.7.17-cpeGNU-23.03 2>/dev/null || true

echo "Bioinformatics modules loaded:"
module list 2>&1
command -v blastn 2>/dev/null || true
command -v makeblastdb 2>/dev/null || true
command -v samtools 2>/dev/null || true
command -v bwa 2>/dev/null || true
