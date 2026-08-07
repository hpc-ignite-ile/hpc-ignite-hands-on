# 02 ใช้ Jupyter Notebook บน LANTA ผ่าน Slurm และ SSH Tunnel

หน้านี้เปิด JupyterLab บนเครื่องคำนวณของ LANTA ผ่านการจัดสรรทรัพยากรของ Slurm แล้วส่งพอร์ตกลับมาเปิดในเบราว์เซอร์บนเครื่องผู้ใช้ด้วย SSH tunnel โดยใช้สภาพแวดล้อมและโมดูลจาก [01-custom-python-env-module.md](01-custom-python-env-module.md)

บทนี้ใช้ `hpc-mesa` เป็นเส้นทางหลัก เพราะเซิร์ฟเวอร์และเคอร์เนลอยู่ในสภาพแวดล้อมเดียวกัน จึงลดความคลาดเคลื่อนของแพ็กเกจระหว่างผู้เรียน ถ้า LANTA มี JupyterLab กลางในรอบอบรม ให้ใช้เป็นทางสำรองได้ โดยเลือกเคอร์เนล `Python (hpc-mesa)` ในหน้า JupyterLab เพื่อให้สมุดบันทึกใช้ Mesa, pandas และ matplotlib จากสภาพแวดล้อมของกิจกรรม

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `sbatch`, `squeue`, `tail`, `scancel`, `python - <<'PY'`, `jupyter lab`, `chmod`, SSH tunnel `-L` และ option `-o`

## ภาพรวม

```text
เครื่องผู้ใช้ -> เครื่องเข้าใช้งานของ LANTA -> การจัดสรรทรัพยากรของ Slurm -> เครื่องคำนวณ
      ^                                                    |
      |---------------- SSH Tunnel ไปยัง Jupyter ----------|
```

เคอร์เนล Jupyter ใช้ CPU และหน่วยความจำต่อเนื่องระหว่างอ่านข้อมูล สร้างกราฟ หรือทดลองแบบจำลอง จึงให้ Slurm จัดสรรทรัพยากรบนเครื่องคำนวณ แล้วเก็บหลักฐานในคิวงาน บันทึกงาน และประวัติงาน

บทนี้เหมาะกับการสำรวจ `results/epi_summary_*.csv`, ตรวจผลลัพธ์ของ ABS โรคระบาด, สร้างกราฟเปรียบเทียบนโยบาย และดูข้อมูลทรัพยากรที่สมุดบันทึกใช้จริง

หลังมีผลจากทั้ง EpiSprint และ Twin-B MicroCosim แล้ว ใช้ [05-output-display-jupyter-gnuplot.md](05-output-display-jupyter-gnuplot.md) เพื่อสร้างสมุดบันทึกและรูปเปรียบเทียบจากตารางกลางชุดเดียวกัน

## เลือกวิธีเปิด JupyterLab

| วิธี | เซิร์ฟเวอร์ JupyterLab | เคอร์เนล Python | เหมาะกับสถานการณ์ |
|---|---|---|---|
| เส้นทางหลักของการอบรม | `hpc-mesa/2.3.4` | `Python (hpc-mesa)` | ใช้แพ็กเกจชุดเดียวกันทั้งเซิร์ฟเวอร์และเคอร์เนล |
| ทางสำรองของระบบกลาง | site/default JupyterLab | `Python (hpc-mesa)` | ใช้เมื่อรอบใช้งานของ LANTA มี JupyterLab จากโมดูลหรือ PATH กลาง |

ก่อนใช้ทางสำรองของระบบกลาง ให้รันหน้า [01-custom-python-env-module.md](01-custom-python-env-module.md) ถึงขั้น `python -m ipykernel install --user --name hpc-mesa ...` เพื่อให้เซิร์ฟเวอร์กลางเห็นเคอร์เนลของกิจกรรม

## Copy-Paste จากเครื่องผู้ใช้

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เข้าสู่ LANTA

คำสั่งชุดนี้เปิดเชลล์บนเครื่องเข้าใช้งานเพื่อสร้างไฟล์และส่งงาน Slurm

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

ผู้ใช้ที่ตั้ง alias ตาม [../docs/SSH_PRIVATE_KEY_LANTA_TH.md](../docs/SSH_PRIVATE_KEY_LANTA_TH.md) สามารถใช้ `ssh lanta`

## Copy-Paste บน LANTA

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียมพื้นที่ทำงาน

คำสั่งชุดนี้สร้างพื้นที่ทำงานและโฟลเดอร์สำหรับไฟล์กำหนดค่า สคริปต์ Slurm บันทึกงาน สมุดบันทึก และผลลัพธ์

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p configs jobs logs notes notebooks results src
pwd
```

### ขั้นที่ 2: โหลดค่า Session เดิม

คำสั่งชุดนี้โหลดบัญชีโครงการ พื้นที่โครงการ และตำแหน่งโมดูลจากหน้า 00 เมื่อเคยบันทึกไว้

```bash
if [ -f notes/session-env.sh ]; then
    source notes/session-env.sh
fi
```

### ขั้นที่ 3: ตั้งค่า Account และ Project

คำสั่งชุดนี้รับค่าบัญชี Slurm และเส้นทางพื้นที่โครงการที่ใช้หาโมดูล `hpc-mesa/2.3.4`

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

คำสั่งชุดนี้ยืนยันว่า Python, JupyterLab, pandas และ matplotlib มาจากสภาพแวดล้อมที่เตรียมไว้

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

### ขั้นที่ 5: ตรวจทางสำรอง JupyterLab ของระบบกลาง

คำสั่งชุดนี้ตรวจว่ารอบใช้งานปัจจุบันมี JupyterLab กลางจาก PATH หรือโมดูลของ LANTA แล้วบันทึกหลักฐานก่อนกลับไปใช้ `hpc-mesa` เป็นเส้นทางหลัก

```bash
module purge
command -v jupyter || true
jupyter lab --version 2>/dev/null || true
module -t avail 2>&1 | grep -Ei 'jupyter|notebook|lab' | head -20 || true
```

ผลที่ใช้ทางสำรองได้คือมีเส้นทางของ `jupyter` และ `jupyter lab --version` แสดงเลขรุ่น หรือผู้ดูแลแจ้งชื่อโมดูลที่เปิด JupyterLab ให้ เช่นตั้งค่า `LANTA_JUPYTER_MODULE`

### ขั้นที่ 6: กลับไปใช้ `hpc-mesa`

คำสั่งชุดนี้โหลดสภาพแวดล้อมหลักอีกครั้งก่อนสร้างสมุดบันทึกและสคริปต์ Slurm

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
jupyter kernelspec list
```

### ขั้นที่ 7: สร้าง Notebook ตัวอย่าง

คำสั่งชุดนี้สร้างสมุดบันทึกสำหรับอ่านผล ABS โรคระบาด สรุปนโยบาย วาดกราฟ และตรวจทรัพยากรจากสภาพแวดล้อม Slurm

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

คำสั่งชุดนี้ตรวจว่าไฟล์ `.ipynb` เป็น JSON ที่ Jupyter อ่านได้

```bash
python -m json.tool notebooks/episprint_explore.ipynb >/dev/null
ls -lh notebooks/episprint_explore.ipynb
```

### ขั้นที่ 9: สร้างสคริปต์ Slurm สำหรับ JupyterLab

คำสั่งชุดนี้สร้างสคริปต์งานที่ขอ CPU และหน่วยความจำ เลือกแหล่งของเซิร์ฟเวอร์ เลือกพอร์ต พิมพ์คำสั่ง tunnel จำกัดจำนวน thread ของไลบรารีเชิงตัวเลข และเริ่ม JupyterLab

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

### ขั้นที่ 10: ตรวจสคริปต์ Slurm

คำสั่งชุดนี้ตรวจสิทธิ์และเปิดดูส่วนต้นของสคริปต์งานก่อนส่งเข้าสู่คิว

```bash
chmod u+x jobs/jupyter_episprint.sbatch
sed -n '1,140p' jobs/jupyter_episprint.sbatch
```

### ขั้นที่ 11: ส่งงาน Jupyter ด้วย `hpc-mesa`

คำสั่งชุดนี้ส่งงานเข้า Slurm และบันทึกเลขงานลง `notes/job-history.tsv`

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/jupyter_episprint.sbatch)
printf "%s\t%s\t%s\n" "$job_id" "jupyter_episprint" "$(date -Is)" >> notes/job-history.tsv
echo "Submitted Jupyter job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read log: tail -80 logs/jupyter_${job_id}.out"
```

### ขั้นที่ 12: ส่งงาน Jupyter ด้วยทางสำรองของระบบกลาง

ใช้ขั้นนี้เมื่อขั้นตรวจทางสำรองพบ JupyterLab จากโมดูลหรือ PATH กลางของ LANTA โดยให้ `LANTA_JUPYTER_MODULE` เป็นค่าว่างเมื่อ `jupyter` อยู่ใน PATH อยู่แล้ว

```bash
export LANTA_JUPYTER_MODULE="${LANTA_JUPYTER_MODULE:-}"
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,JUPYTER_SERVER_SOURCE=site,LANTA_JUPYTER_MODULE="$LANTA_JUPYTER_MODULE" --parsable jobs/jupyter_episprint.sbatch)
printf "%s\t%s\t%s\n" "$job_id" "jupyter_episprint_site" "$(date -Is)" >> notes/job-history.tsv
echo "Submitted site Jupyter job: $job_id"
```

### ขั้นที่ 13: อ่านบันทึกเพื่อหา Node, Port และ URL

คำสั่งชุดนี้ใช้เมื่องานเริ่มเป็น `R` แล้ว เพื่ออ่านคำสั่ง tunnel และ URL ที่มี token

```bash
squeue -j "$job_id"
tail -80 "logs/jupyter_${job_id}.out"
grep -E 'Compute node:|Port:|127.0.0.1|token=' "logs/jupyter_${job_id}.out" || true
```

## Copy-Paste กลับไปที่เครื่องผู้ใช้

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เปิด SSH Tunnel

เปิดเทอร์มินัลใหม่บนเครื่องผู้ใช้ แล้วใช้คำสั่งที่บันทึกงานพิมพ์ให้ โดยแทน `<port>` และ `<node>` จากบันทึกของงานปัจจุบัน

```bash
ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -L <port>:<node>:<port> <lanta-username>@lanta.nstda.or.th
```

เทอร์มินัลที่รัน tunnel จะค้างอยู่ตามปกติ เพราะ `-N` ใช้การเชื่อมต่อสำหรับส่งต่อพอร์ตอย่างเดียว

### ขั้นที่ 2: เปิดเบราว์เซอร์

ใช้ URL จากบันทึกงาน โดยเปลี่ยน host เป็น `127.0.0.1` และใส่ token ให้ครบ

```text
http://127.0.0.1:<port>/lab?token=<token-from-log>
```

เมื่อ JupyterLab เปิดแล้ว ให้เข้า folder `notebooks/` และเปิด `episprint_explore.ipynb`

### กรณีพอร์ตบนเครื่องผู้ใช้ชนกัน

ใช้พอร์ตบนเครื่องผู้ใช้อื่นได้ โดยคงพอร์ตฝั่ง LANTA จากบันทึกงานไว้เหมือนเดิม

```bash
ssh -N -o ExitOnForwardFailure=yes -L 8877:<node>:<remote-port-from-log> <lanta-username>@lanta.nstda.or.th
```

จากนั้นเปิด `http://127.0.0.1:8877/lab?token=<token-from-log>`

## ปิดงานเมื่อใช้เสร็จ

### ขั้นที่ 1: ยกเลิกงาน Slurm บน LANTA

คำสั่งชุดนี้คืนทรัพยากรเครื่องคำนวณหลังจบการใช้งาน

```bash
squeue -u "$USER"
scancel <jobid>
squeue -j <jobid>
```

### ขั้นที่ 2: ปิด Tunnel บนเครื่องผู้ใช้

กด `Ctrl+C` ในเทอร์มินัลที่รัน `ssh -N -L ...`

## ตรวจผลและปรับทรัพยากร

หลังจบงาน ใช้ `sacct` เพื่ออ่านทรัพยากรที่ใช้จริง

```bash
sacct -j <jobid> --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,ReqMem,MaxRSS,ExitCode
```

สถานะ `CANCELLED` หลังผู้ใช้สั่ง `scancel` ถือเป็นรูปแบบปกติของการใช้งาน Jupyter แบบโต้ตอบที่ปิดด้วยตนเอง ถ้า `MaxRSS` ต่ำกว่า `ReqMem` มาก ให้ลด `#SBATCH --mem` ในรอบถัดไป ถ้าเห็น `OUT_OF_MEMORY` ให้เพิ่มหน่วยความจำทีละระดับ

## รายการตรวจแก้ปัญหา

| อาการ | ตรวจด้วยคำสั่ง | หลักฐานที่ต้องตรงกัน |
|---|---|---|
| เบราว์เซอร์เชื่อมต่อขัดข้อง | `squeue -j <jobid>` | งานยังเป็น `R` |
| Tunnel ใช้ค่าคนละรอบงาน | `tail -80 logs/jupyter_<jobid>.out` | node และ port ตรงกับ tunnel |
| Token ขาด | `grep -E 'token=' logs/jupyter_<jobid>.out` | URL มี `?token=` ครบ |
| โมดูลหา JupyterLab ขาด | `module use "$EPI_MODULE_ROOT"; module load hpc-mesa/2.3.4; which jupyter` | path ชี้เข้าสภาพแวดล้อมที่สร้างไว้ |
| ทางสำรองของระบบกลางหาเคอร์เนลขาด | `jupyter kernelspec list` | มี `hpc-mesa` หรือ `Python (hpc-mesa)` |
| งานรอคิวนาน | `squeue -j <jobid> -o "%.18i %.9P %.20j %.8u %.2t %.10M %.6D %R"` | reason อธิบายคิว บัญชี หรือพาร์ทิชัน |
| เคอร์เนลเปิดขัดข้อง | `tail -100 logs/jupyter_<jobid>.err` | error ชี้รันไทม์ แพ็กเกจ หรือโควตา |

## แนวปฏิบัติ

- เก็บ token และ URL ไว้เฉพาะรอบใช้งานของผู้ใช้
- รัน JupyterLab ผ่านการจัดสรรทรัพยากรของ Slurm บนเครื่องคำนวณ
- ใช้สมุดบันทึกสำหรับสำรวจข้อมูล สร้างกราฟ และตรวจข้อผิดพลาดแบบโต้ตอบ
- ย้ายงานที่รันยาวหรือรันซ้ำหลายสถานการณ์ไปเป็นสคริปต์ Python แล้วส่งด้วย `sbatch`
- เก็บผลลัพธ์ขนาดใหญ่ในพื้นที่โครงการ และให้สมุดบันทึกอ่านจากเส้นทางหรือ symbolic link ที่ควบคุมได้
