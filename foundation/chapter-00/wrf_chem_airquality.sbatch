#!/bin/bash
#SBATCH --job-name=wrf-chem-preflight
#SBATCH --partition=compute-devel
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

# ============================================================
# WRF/WPS/WRF-Chem Preflight - Northern Thailand Air Quality
# Chapter 0: HPC 101 case-study scaffold
#
# This is intentionally a short preflight, not a full WRF-Chem forecast.
# Learners can run it during training to see real LANTA weather modules,
# shared WRF/WPS data paths, and provenance capture without occupying many
# nodes or requiring emissions/boundary-condition datasets.
# ============================================================

set -euo pipefail

echo "=========================================="
echo "WRF/WPS/WRF-Chem Preflight"
echo "Start time: $(date)"
echo "Job ID: ${SLURM_JOB_ID:-manual}"
echo "Node: $(hostname)"
echo "=========================================="

module purge
module load WPS/4.6-DM-cpeCray-25.03 2>/dev/null || true
module load WRF/4.7.1-DMSM-cpeCray-25.03 2>/dev/null || true
module load WRFchem/4.7.1-DM-cpeCray-25.03 2>/dev/null || true

echo "Modules loaded:"
module list 2>&1 || true

OUT="results/wrf_preflight_${SLURM_JOB_ID:-manual}"
mkdir -p "$OUT"

{
    echo "Executables"
    command -v geogrid.exe || true
    command -v ungrib.exe || true
    command -v metgrid.exe || true
    command -v real.exe || true
    command -v wrf.exe || true
    echo
    echo "Shared paths"
    ls -ld /project/common/WRF /project/common/WPS_Static 2>/dev/null || true
    echo
    echo "Candidate WRF files"
    find /project/common/WRF -maxdepth 4 -type f | head -20 2>/dev/null || true
} | tee "$OUT/preflight.txt"

echo "Preflight complete. Full WRF-Chem runs should be instructor demos with prepared data."
