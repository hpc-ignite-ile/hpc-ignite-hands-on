# บทที่ 25: ชีวสารสนเทศศาสตร์

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

เริ่มจาก SSH ตาม [../../LANTA_SETUP.md#1-ssh-to-lanta](../../LANTA_SETUP.md#1-ssh-to-lanta) แล้วแปะ block ในหัวข้อ Copy-Paste บน LANTA

หน้านี้เป็น standalone hand-on ผู้ใช้แปะคำสั่งบน LANTA แล้วได้ workspace, source file, Slurm script, log และ result ครบใน `$HOME/hpc-ignite-standalone/bio-blast` โดยตรง

## เป้าหมาย

1. สร้าง FASTA reference และ query
2. สร้าง BLAST database ขนาดเล็ก
3. ตรวจ hit table และ BLAST version

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/hpc-ignite-standalone/bio-blast"
cd "$HOME/hpc-ignite-standalone/bio-blast"
mkdir -p jobs logs notes results

if [ -z "${LANTA_CPU_PARTITION:-}" ]; then export LANTA_CPU_PARTITION="compute-devel"; fi
if [ -z "${LANTA_ACCOUNT:-}" ]; then read -rp "Slurm project account, blank for site default: " LANTA_ACCOUNT; export LANTA_ACCOUNT; fi
SBATCH_ACCOUNT=(); if [ -n "${LANTA_ACCOUNT:-}" ]; then SBATCH_ACCOUNT=(-A "$LANTA_ACCOUNT"); fi
```

### ขั้นที่ 2: สร้าง Slurm script `jobs/blast_smoke.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/blast_smoke.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=blast-smoke
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
set -euo pipefail
module purge
module load BLAST+/2.14.0-cpeGNU-23.03 2>/dev/null || true
cd "$SLURM_SUBMIT_DIR"
OUT="results/${SLURM_JOB_ID}"; mkdir -p "$OUT"
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
SLURM
```

### ขั้นที่ 3: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch "${SBATCH_ACCOUNT[@]}" -p "$LANTA_CPU_PARTITION" --parsable jobs/blast_smoke.sbatch)
echo "$job_id	blast_smoke	$(date -Is)" >> notes/job-history.tsv
echo "Submitted job: $job_id"
echo "Read: tail -80 logs/blast-smoke_${job_id}.out"
```

## Check

```bash
cd "$HOME/hpc-ignite-standalone/bio-blast"
find results -maxdepth 2 -type f | sort
cat results/*/blast_hits.tsv
```

## การตรวจผล

หลัง job จบ ให้ผู้ใช้ตรวจสามชั้นหลักฐาน:

1. `sacct` แสดง `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `logs/` มี stdout/stderr ของ job id นั้น
3. `results/` มีไฟล์ output ที่ระบุในหัวข้อ Check

## ใช้ Repo เป็น Reference

ถ้าผู้ใช้ clone repo แล้ว สามารถเทียบแนวคิดกับไฟล์ใน repo ได้ เช่น `slurm/`, `requirements/`, `environments/` และ `jobs/` ของแต่ละบท แต่ block ด้านบนออกแบบให้รันได้จากหน้า hand-on นี้โดยตรง
