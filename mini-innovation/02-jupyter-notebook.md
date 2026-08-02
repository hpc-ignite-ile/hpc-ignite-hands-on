# 02 ใช้ Jupyter Notebook บน LANTA

หน้านี้เปิด Jupyter Lab บน compute node ผ่าน Slurm allocation แล้ว tunnel กลับมาเปิดใน browser บนเครื่อง local ใช้ environment และ module จาก [01-custom-python-env-module.md](01-custom-python-env-module.md)

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `sbatch`, `squeue`, `tail`, `scancel`, heredoc, `python - <<'PY'`, และ SSH tunnel `-L`

## Copy-Paste จากเครื่อง Local

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p configs jobs logs notes notebooks results src

if [ -f notes/session-env.sh ]; then
    source notes/session-env.sh
fi

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น ltXXXXXX หรือ tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi

if [ -z "${LANTA_PROJECT:-}" ]; then
    read -rp "Project directory เช่น /project/ltXXXXXX-name หรือ /project/tn999996-north: " LANTA_PROJECT
    export LANTA_PROJECT
fi

export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-$LANTA_PROJECT/modules}"

cat > notebooks/episprint_explore.ipynb <<'IPYNB'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# LANTA EpiSprint\\n",
    "\\n",
    "Notebook นี้ใช้สำรวจผลลัพธ์ epidemic ABS แบบสั้น เมื่อยังรอผลลัพธ์จริง cell จะสร้างข้อมูลตัวอย่างเพื่อสาธิตโครงสร้างข้อมูลก่อน"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from pathlib import Path\\n",
    "import pandas as pd\\n",
    "import matplotlib.pyplot as plt\\n",
    "\\n",
    "summary_files = sorted(Path('results').glob('epi_summary_*.csv'))\\n",
    "if summary_files:\\n",
    "    df = pd.concat([pd.read_csv(path) for path in summary_files], ignore_index=True)\\n",
    "else:\\n",
    "    df = pd.DataFrame([\\n",
    "        {'policy': 'baseline', 'peak_I': 540, 'attack_rate': 0.62},\\n",
    "        {'policy': 'mask', 'peak_I': 340, 'attack_rate': 0.41},\\n",
    "        {'policy': 'isolation', 'peak_I': 280, 'attack_rate': 0.35},\\n",
    "        {'policy': 'combined', 'peak_I': 180, 'attack_rate': 0.22},\\n",
    "    ])\\n",
    "df"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "ax = df.groupby('policy')[['peak_I', 'attack_rate']].mean().sort_values('peak_I').plot(kind='bar', secondary_y='attack_rate')\\n",
    "ax.set_title('EpiSprint policy comparison')\\n",
    "ax.set_ylabel('mean peak infectious agents')\\n",
    "plt.tight_layout()"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.10"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
IPYNB

cat > jobs/jupyter_episprint.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-jupyter
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:45:00
#SBATCH --output=logs/jupyter_%j.out
#SBATCH --error=logs/jupyter_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"

port=$(python - <<'PY'
import random
print(random.randint(7000, 9999))
PY
)
node=$(hostname -s)

echo "Jupyter node: ${node}"
echo "Jupyter port: ${port}"
echo
echo "Copy this command into a NEW LOCAL terminal:"
echo "ssh -N -L ${port}:${node}:${port} ${USER}@lanta.nstda.or.th"
echo
echo "Then open the URL printed by Jupyter below."

if [ -n "${SLURM_JOBTMP:-}" ]; then
    export XDG_RUNTIME_DIR="$SLURM_JOBTMP"
fi

jupyter lab --no-browser --ip="${node}" --port="${port}" --notebook-dir="$(pwd)"
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/jupyter_episprint.sbatch)
echo "$job_id	jupyter_episprint	$(date -Is)" >> notes/job-history.tsv
echo "Submitted Jupyter job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Wait 10-30 seconds, then read:"
echo "tail -80 logs/jupyter_${job_id}.out"
```

## Copy-Paste กลับไปที่เครื่อง Local

หลัง `tail -80 logs/jupyter_<jobid>.out` แสดงบรรทัด `ssh -N -L ...` ให้ copy บรรทัดนั้นมาเปิดใน terminal ใหม่บนเครื่อง local

```bash
ssh -N -L <port>:<node>:<port> <lanta-username>@lanta.nstda.or.th
```

จากนั้นเปิด URL ที่ Jupyter พิมพ์ไว้ เช่น

```text
http://127.0.0.1:<port>/lab?token=...
```

## คำอธิบาย

Jupyter ใน lab นี้รันภายใน Slurm allocation บน compute node เพราะ kernel ใช้ CPU และ memory ต่อเนื่องระหว่างวิเคราะห์ข้อมูล การส่ง `jobs/jupyter_episprint.sbatch` เข้า `compute-devel` ทำให้มีหลักฐานด้าน resource ใน queue และ log ส่วน SSH tunnel ทำให้ browser บนเครื่อง local เชื่อมไปยัง Jupyter ที่รันอยู่บน node ภายใน LANTA ได้อย่างปลอดภัย

ไฟล์ notebook ตัวอย่างอยู่ที่ `notebooks/episprint_explore.ipynb` ช่วงเริ่มกิจกรรม notebook ใช้ข้อมูลตัวอย่างเพื่อสาธิต schema และกราฟ หลังจากรันหน้า ABS แล้ว notebook จะอ่าน `results/epi_summary_*.csv` จริงเพื่อเปรียบเทียบ policy

## ปิดงานเมื่อใช้เสร็จ

บน LANTA ให้ยกเลิก job เพื่อคืนทรัพยากร

```bash
squeue -u "$USER"
scancel <jobid>
```

เมื่อต้องแก้ปัญหา browser ให้ตรวจสามจุดนี้ตามลำดับ: job ยังอยู่ใน `squeue`, tunnel command ใช้ port และ node ตรงกับ log, และ URL มี token ครบ
