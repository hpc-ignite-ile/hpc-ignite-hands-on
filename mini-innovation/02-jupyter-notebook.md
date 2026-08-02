# 02 ใช้ Jupyter Notebook บน LANTA ผ่าน Slurm และ SSH Tunnel

หน้านี้เปิด JupyterLab บน compute node ของ LANTA ผ่าน Slurm allocation แล้วส่ง port กลับมาเปิดใน browser บนเครื่อง local ด้วย SSH tunnel ใช้ environment และ module จาก [01-custom-python-env-module.md](01-custom-python-env-module.md)

บทนี้ใช้ `hpc-mesa` เป็น path หลัก เพราะ server และ kernel อยู่ใน environment เดียวกัน จึงลดความคลาดเคลื่อนของ package ระหว่างผู้เรียน ถ้า LANTA มี site/default JupyterLab ในรอบอบรม ให้ใช้เป็น fallback ได้ โดยเลือก kernel `Python (hpc-mesa)` ในหน้า JupyterLab เพื่อให้ notebook ใช้ Mesa, pandas และ matplotlib จาก environment ของกิจกรรม

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `sbatch`, `squeue`, `tail`, `scancel`, `python - <<'PY'`, `jupyter lab`, `chmod`, SSH tunnel `-L` และ option `-o`

## ภาพรวม

```text
เครื่อง Local -> LANTA Login Node -> Slurm Allocation -> Compute Node
      ^                                                    |
      |---------------- SSH Tunnel ไปยัง Jupyter ----------|
```

Jupyter kernel ใช้ CPU และ memory ต่อเนื่องระหว่างอ่านข้อมูล สร้างกราฟ หรือทดลอง model จึงให้ Slurm จัดสรรทรัพยากรบน compute node แล้วเก็บหลักฐานใน queue, log และ job history

บทนี้เหมาะกับการสำรวจ `results/epi_summary_*.csv`, ตรวจ output ของ epidemic ABS, สร้างกราฟ policy comparison และดูข้อมูล resource ที่ notebook ใช้จริง

## เลือกวิธีเปิด JupyterLab

| วิธี | JupyterLab server | Python kernel | เหมาะกับสถานการณ์ |
|---|---|---|---|
| Training path | `hpc-mesa/2.3.4` | `Python (hpc-mesa)` | ใช้ package ชุดเดียวกันทั้ง server และ kernel |
| Site fallback | site/default JupyterLab | `Python (hpc-mesa)` | ใช้เมื่อ LANTA session มี JupyterLab จาก module หรือ PATH กลาง |

ก่อนใช้ site fallback ให้รันหน้า [01-custom-python-env-module.md](01-custom-python-env-module.md) ถึงขั้น `python -m ipykernel install --user --name hpc-mesa ...` เพื่อให้ server กลางเห็น kernel ของกิจกรรม

## Copy-Paste จากเครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: Login เข้า LANTA

block นี้เปิด shell บน login node เพื่อสร้างไฟล์และส่ง Slurm job

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

ผู้ใช้ที่ตั้ง alias ตาม [../docs/SSH_PRIVATE_KEY_LANTA_TH.md](../docs/SSH_PRIVATE_KEY_LANTA_TH.md) สามารถใช้ `ssh lanta`

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม Workspace

block นี้สร้างพื้นที่ทำงานและ folder สำหรับ config, Slurm script, log, notebook และผลลัพธ์

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p configs jobs logs notes notebooks results src
pwd
```

### ขั้นที่ 2: โหลดค่า Session เดิม

block นี้โหลด account, project และ module root จากหน้า 00 เมื่อเคยบันทึกไว้

```bash
if [ -f notes/session-env.sh ]; then
    source notes/session-env.sh
fi
```

### ขั้นที่ 3: ตั้งค่า Account และ Project

block นี้รับค่า Slurm account และ project directory ที่ใช้หา module `hpc-mesa/2.3.4`

```bash
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
```

### ขั้นที่ 4: ตรวจ Module และ JupyterLab จาก `hpc-mesa`

block นี้ยืนยันว่า Python, JupyterLab, pandas และ matplotlib มาจาก environment ที่เตรียมไว้

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
which python
python --version
which jupyter
jupyter lab --version
python - <<'PY'
import pandas, matplotlib
print("pandas", pandas.__version__)
print("matplotlib", matplotlib.__version__)
PY
```

### ขั้นที่ 5: ตรวจ Site JupyterLab Fallback

block นี้ตรวจว่า session ปัจจุบันมี JupyterLab กลางจาก PATH หรือ module ของ LANTA หรือใช้ `hpc-mesa` เป็น server หลักต่อไป

```bash
module purge
command -v jupyter || true
jupyter lab --version 2>/dev/null || true
module -t avail 2>&1 | grep -Ei 'jupyter|notebook|lab' | head -20 || true
```

ผลที่ใช้ site fallback ได้คือมี path ของ `jupyter` และ `jupyter lab --version` แสดงเลข version หรือผู้ดูแลแจ้งชื่อ module ที่เปิด JupyterLab ให้ เช่นตั้งค่า `LANTA_JUPYTER_MODULE`

### ขั้นที่ 6: กลับไปใช้ `hpc-mesa`

block นี้โหลด environment หลักอีกครั้งก่อนสร้าง notebook และ Slurm script

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
jupyter kernelspec list
```

### ขั้นที่ 7: สร้าง Notebook ตัวอย่าง

block นี้สร้าง notebook สำหรับอ่านผล epidemic ABS, สร้าง policy summary, วาดกราฟ และตรวจ resource จาก Slurm environment

```bash
python - <<'PY'
from pathlib import Path
import json

cells = [
    ("markdown", "# LANTA EpiSprint\\nสำรวจผล epidemic ABS และ resource ของ Slurm"),
    ("code", """from pathlib import Path
import pandas as pd

files = sorted(Path('results').glob('epi_summary_*.csv'))
df = pd.concat([pd.read_csv(p) for p in files], ignore_index=True) if files else pd.DataFrame([
    {'policy': 'baseline', 'peak_I': 540, 'attack_rate': 0.62},
    {'policy': 'mask', 'peak_I': 340, 'attack_rate': 0.41},
    {'policy': 'isolation', 'peak_I': 280, 'attack_rate': 0.35},
    {'policy': 'combined', 'peak_I': 180, 'attack_rate': 0.22},
])
policy_summary = df.groupby('policy')[['peak_I', 'attack_rate']].mean().sort_values('peak_I')
policy_summary"""),
    ("code", """from pathlib import Path
import matplotlib.pyplot as plt
Path('results').mkdir(exist_ok=True)
ax = policy_summary.plot(kind='bar', secondary_y='attack_rate', figsize=(9, 5))
ax.set_title('EpiSprint policy comparison')
ax.set_ylabel('Mean peak infectious agents')
ax.right_ax.set_ylabel('Mean attack rate')
plt.tight_layout()
policy_summary.to_csv('results/policy_summary.csv')"""),
    ("code", """from pathlib import Path
import os, socket
print('hostname', socket.gethostname())
print('cwd', Path.cwd())
print('SLURM_JOB_ID', os.environ.get('SLURM_JOB_ID'))
print('SLURM_CPUS_PER_TASK', os.environ.get('SLURM_CPUS_PER_TASK'))
print('SLURM_SUBMIT_DIR', os.environ.get('SLURM_SUBMIT_DIR'))"""),
]

nb = {"cells": [], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 5}
for kind, source in cells:
    cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(True)}
    if kind == "code":
        cell.update({"execution_count": None, "outputs": []})
    nb["cells"].append(cell)
Path("notebooks/episprint_explore.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("notebooks/episprint_explore.ipynb")
PY
```

### ขั้นที่ 8: ตรวจ Notebook JSON

block นี้ตรวจว่าไฟล์ `.ipynb` เป็น JSON ที่ Jupyter อ่านได้

```bash
python -m json.tool notebooks/episprint_explore.ipynb >/dev/null
ls -lh notebooks/episprint_explore.ipynb
```

### ขั้นที่ 9: สร้าง Slurm Script สำหรับ JupyterLab

block นี้สร้าง job script ที่ขอ CPU และ memory, เลือก server source, เลือก port, พิมพ์ tunnel command, จำกัด thread ของ numerical libraries และเริ่ม JupyterLab

```bash
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
if [ "${JUPYTER_SERVER_SOURCE:-hpc-mesa}" = "site" ]; then
    if [ -n "${LANTA_JUPYTER_MODULE:-}" ]; then
        module load "$LANTA_JUPYTER_MODULE"
    fi
else
    module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
    module load hpc-mesa/2.3.4
fi
cd "$SLURM_SUBMIT_DIR"
command -v jupyter
jupyter kernelspec list | sed -n '1,80p'

port=$(python - <<'PY'
import random
print(random.randint(7000, 9999))
PY
)
node=$(hostname -s)
export XDG_RUNTIME_DIR="${SLURM_JOBTMP:-/tmp/${USER}-jupyter-${SLURM_JOB_ID}}"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export NUMEXPR_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"

echo "JupyterLab on LANTA"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Compute node: ${node}"
echo "Port: ${port}"
echo "Working dir: $(pwd)"
echo "Local tunnel:"
echo "ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -L ${port}:${node}:${port} ${USER}@lanta.nstda.or.th"
echo "Browser URL appears below. Use 127.0.0.1 with the token from Jupyter."

jupyter lab --no-browser --ip="${node}" --port="${port}" --ServerApp.port_retries=0 --notebook-dir="$(pwd)"
SLURM
```

### ขั้นที่ 10: ตรวจ Slurm Script

block นี้ตรวจสิทธิ์และเปิดดูส่วนต้นของ job script ก่อน submit

```bash
chmod u+x jobs/jupyter_episprint.sbatch
sed -n '1,140p' jobs/jupyter_episprint.sbatch
```

### ขั้นที่ 11: ส่ง Jupyter Job ด้วย `hpc-mesa`

block นี้ส่ง job เข้า Slurm และบันทึก job id ลง `notes/job-history.tsv`

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/jupyter_episprint.sbatch)
printf "%s\t%s\t%s\n" "$job_id" "jupyter_episprint" "$(date -Is)" >> notes/job-history.tsv
echo "Submitted Jupyter job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read log: tail -80 logs/jupyter_${job_id}.out"
```

### ขั้นที่ 12: ส่ง Jupyter Job ด้วย Site Fallback

ใช้ขั้นนี้เมื่อขั้นตรวจ fallback พบ JupyterLab จาก module หรือ PATH กลางของ LANTA โดยให้ `LANTA_JUPYTER_MODULE` เป็นค่าว่างเมื่อ `jupyter` อยู่ใน PATH อยู่แล้ว

```bash
export LANTA_JUPYTER_MODULE="${LANTA_JUPYTER_MODULE:-}"
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,JUPYTER_SERVER_SOURCE=site,LANTA_JUPYTER_MODULE="$LANTA_JUPYTER_MODULE" --parsable jobs/jupyter_episprint.sbatch)
printf "%s\t%s\t%s\n" "$job_id" "jupyter_episprint_site" "$(date -Is)" >> notes/job-history.tsv
echo "Submitted site Jupyter job: $job_id"
```

### ขั้นที่ 13: อ่าน Log เพื่อหา Node, Port และ URL

block นี้ใช้เมื่อ job เริ่มเป็น `R` แล้ว เพื่ออ่าน tunnel command และ URL ที่มี token

```bash
squeue -j "$job_id"
tail -80 "logs/jupyter_${job_id}.out"
grep -E 'Compute node:|Port:|127.0.0.1|token=' "logs/jupyter_${job_id}.out" || true
```

## Copy-Paste กลับไปที่เครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เปิด SSH Tunnel

เปิด terminal ใหม่บนเครื่อง local แล้วใช้ command ที่ log พิมพ์ให้ โดยแทน `<port>` และ `<node>` จาก log ของ job ปัจจุบัน

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -L <port>:<node>:<port> <lanta-username>@lanta.nstda.or.th
```

terminal ที่รัน tunnel จะค้างอยู่เป็นปกติ เพราะ `-N` ใช้ connection สำหรับ port forwarding อย่างเดียว

### ขั้นที่ 2: เปิด Browser

ใช้ URL จาก log โดยเปลี่ยน host เป็น `127.0.0.1` และใช้ token ให้ครบ

```text
http://127.0.0.1:<port>/lab?token=<token-from-log>
```

เมื่อ JupyterLab เปิดแล้ว ให้เข้า folder `notebooks/` และเปิด `episprint_explore.ipynb`

### กรณี Local Port ชนกัน

ใช้ local port อื่นได้ โดยคง remote port จาก log ไว้เหมือนเดิม

```bash
ssh -N -o ExitOnForwardFailure=yes -L 8877:<node>:<remote-port-from-log> <lanta-username>@lanta.nstda.or.th
```

จากนั้นเปิด `http://127.0.0.1:8877/lab?token=<token-from-log>`

## ปิดงานเมื่อใช้เสร็จ

### ขั้นที่ 1: ยกเลิก Slurm Job บน LANTA

block นี้คืนทรัพยากร compute node หลังจบ session

```bash
squeue -u "$USER"
scancel <jobid>
squeue -j <jobid>
```

### ขั้นที่ 2: ปิด Tunnel บนเครื่อง Local

กด `Ctrl+C` ใน terminal ที่รัน `ssh -N -L ...`

## ตรวจผลและปรับทรัพยากร

หลังจบงาน ใช้ `sacct` เพื่ออ่านทรัพยากรที่ใช้จริง

```bash
sacct -j <jobid> --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,ReqMem,MaxRSS,ExitCode
```

สถานะ `CANCELLED` หลังผู้ใช้สั่ง `scancel` ถือเป็นรูปแบบปกติของ interactive Jupyter session ที่ปิดด้วยตนเอง ถ้า `MaxRSS` ต่ำกว่า `ReqMem` มาก ให้ลด `#SBATCH --mem` รอบถัดไป ถ้าเห็น `OUT_OF_MEMORY` ให้เพิ่ม memory ทีละระดับ

## Debug Checklist

| อาการ | ตรวจด้วยคำสั่ง | หลักฐานที่ต้องตรงกัน |
|---|---|---|
| Browser เชื่อมต่อขัดข้อง | `squeue -j <jobid>` | job ยังเป็น `R` |
| Tunnel ใช้ค่าคนละ session | `tail -80 logs/jupyter_<jobid>.out` | node และ port ตรงกับ tunnel |
| Token ขาด | `grep -E 'token=' logs/jupyter_<jobid>.out` | URL มี `?token=` ครบ |
| Module หา JupyterLab ขาด | `module use "$EPI_MODULE_ROOT"; module load hpc-mesa/2.3.4; which jupyter` | path ชี้เข้า custom environment |
| Site fallback หา kernel ขาด | `jupyter kernelspec list` | มี `hpc-mesa` หรือ `Python (hpc-mesa)` |
| Job pending นาน | `squeue -j <jobid> -o "%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R"` | reason อธิบาย queue, account หรือ partition |
| Kernel เปิดขัดข้อง | `tail -100 logs/jupyter_<jobid>.err` | error ชี้ runtime, package หรือ quota |

## แนวปฏิบัติ

- เก็บ token และ URL ไว้เฉพาะ session ของผู้ใช้
- รัน JupyterLab ผ่าน Slurm allocation บน compute node
- ใช้ notebook สำหรับสำรวจข้อมูล สร้างกราฟ และ debug แบบ interactive
- ย้ายงานที่รันยาวหรือรันซ้ำหลาย scenario ไปเป็น Python script แล้วส่งด้วย `sbatch`
- เก็บผลลัพธ์ขนาดใหญ่ใน project storage และให้ notebook อ่านจาก path หรือ symbolic link ที่ควบคุมได้
