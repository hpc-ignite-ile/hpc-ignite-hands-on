# 05 แสดงผล Mini Innovation ด้วย Jupyter Notebook และ Gnuplot

หน้านี้สร้าง dashboard สำหรับผลลัพธ์ของ mini innovation ทั้งสอง track: **LANTA EpiSprint** และ **Twin-B MicroCosim** ผู้ใช้สามารถดูผลผ่าน Jupyter Notebook หรือสร้างรูปแบบ headless ด้วย Matplotlib และ gnuplot

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `module use`, `module load`, `python - <<'PY'`, `python -m json.tool`, `command -v`, `gnuplot`, `sbatch`, `squeue`, `tail`, และ `sacct`

## เลือกวิธีแสดงผล

| วิธี | เครื่องมือ | ผลลัพธ์ | เหมาะกับงาน |
|---|---|---|---|
| Jupyter Notebook | JupyterLab + Matplotlib | notebook interactive และ PNG | อธิบายผลสดกับผู้เรียน |
| Headless Matplotlib | Python script | PNG จาก batch job | รันบน compute node แล้วเปิดไฟล์ทีหลัง |
| Gnuplot | `gnuplot` | PNG จาก TSV | เครื่องเบา อ่าน script plot ง่าย |

ผลตรวจด้วยบัญชี `tn642` เมื่อ 2026-08-03 พบว่า `hpc-mesa/2.3.4` มี Matplotlib พร้อมใช้ ส่วน `gnuplot` ยังว่างจาก default PATH และ module list ของ session ที่ตรวจ ดังนั้นหน้านี้ใช้ Matplotlib เป็น path หลัก และให้ gnuplot เป็น optional path เมื่อผู้ดูแลเปิด executable หรือ module ให้ในรอบอบรม

## Copy-Paste จากเครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: Login เข้า LANTA

block นี้เปิด shell บน login node เพื่อสร้าง notebook, script และ plot

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

ผู้ใช้ที่ตั้ง alias ตาม [../docs/SSH_PRIVATE_KEY_LANTA_TH.md](../docs/SSH_PRIVATE_KEY_LANTA_TH.md) สามารถใช้ `ssh lanta`

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม Workspace

block นี้สร้าง workspace สำหรับ dashboard และ folder สำหรับ source, notebook, plot script, result table และรูป

```bash
mkdir -p "$HOME/lanta-mini-display"
cd "$HOME/lanta-mini-display"
mkdir -p configs jobs logs notes notebooks plots results figures src
pwd
```

### ขั้นที่ 2: โหลด Environment

block นี้โหลด `hpc-mesa/2.3.4` และตรวจ package ที่ใช้วาดกราฟ

```bash
if [ -f "$HOME/lanta-episprint/notes/session-env.sh" ]; then
    source "$HOME/lanta-episprint/notes/session-env.sh"
fi
if [ -z "${LANTA_PROJECT:-}" ]; then
    read -rp "Project directory เช่น /project/ltXXXXXX-name หรือ /project/tn999996-north: " LANTA_PROJECT
    export LANTA_PROJECT
fi
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-$LANTA_PROJECT/modules}"
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
```

### ขั้นที่ 3: ตรวจ Python Plotting Stack

block นี้ยืนยันว่า pandas และ Matplotlib มาจาก environment ของกิจกรรม

```bash
which python
python - <<'PY'
import pandas, matplotlib
print("pandas", pandas.__version__)
print("matplotlib", matplotlib.__version__)
PY
```

### ขั้นที่ 4: ตั้ง Result Directory

block นี้ชี้ไปยังผลลัพธ์ของ EpiSprint และ Twin-B MicroCosim ที่สร้างจากหน้าก่อนหน้า

```bash
export EPI_RESULTS="${EPI_RESULTS:-$HOME/lanta-episprint/results}"
export TWINB_RESULTS="${TWINB_RESULTS:-$HOME/lanta-twinb-micro/results}"
echo "EPI_RESULTS=$EPI_RESULTS"
echo "TWINB_RESULTS=$TWINB_RESULTS"
```

### ขั้นที่ 5: สร้าง Script เตรียมตารางสำหรับ Plot

block นี้สร้างครึ่งแรกของ `src/prepare_display_tables.py` เพื่ออ่านผล EpiSprint และสร้าง fallback table สำหรับสาธิต

```bash
cat > src/prepare_display_tables.py <<'PY'
import os
from pathlib import Path

import pandas as pd

Path("results").mkdir(exist_ok=True)
epi_dir = Path(os.environ.get("EPI_RESULTS", str(Path.home() / "lanta-episprint" / "results"))).expanduser()
twinb_dir = Path(os.environ.get("TWINB_RESULTS", str(Path.home() / "lanta-twinb-micro" / "results"))).expanduser()

def latest(paths):
    paths = sorted(paths)
    return paths[-1] if paths else None

def build_epi_table():
    policy_file = latest(epi_dir.glob("epi_*_policy_compare.csv"))
    if policy_file:
        df = pd.read_csv(policy_file)
    else:
        summary_files = sorted(epi_dir.glob("epi_summary_*.csv"))
        if summary_files:
            raw = pd.concat([pd.read_csv(p) for p in summary_files], ignore_index=True)
            df = raw.groupby("policy", as_index=False).agg(
                mean_peak_I=("peak_I", "mean"),
                mean_attack_rate=("attack_rate", "mean"),
            )
        else:
            df = pd.DataFrame([
                {"policy": "baseline", "mean_peak_I": 126, "mean_attack_rate": 0.288},
                {"policy": "mask", "mean_peak_I": 44.5, "mean_attack_rate": 0.148},
                {"policy": "isolation", "mean_peak_I": 39, "mean_attack_rate": 0.130},
                {"policy": "combined", "mean_peak_I": 19, "mean_attack_rate": 0.060},
            ])
PY
```

### ขั้นที่ 6: เติม Script สำหรับ Twin-B และเขียน TSV

block นี้เติมส่วนอ่านผล Twin-B MicroCosim แล้วเขียน TSV ที่ Matplotlib และ gnuplot ใช้ร่วมกัน

```bash
cat >> src/prepare_display_tables.py <<'PY'
    keep = ["policy", "mean_peak_I", "mean_attack_rate"]
    df = df[keep].sort_values("mean_peak_I")
    df.to_csv("results/display_epi_policy.tsv", sep="\t", index=False)
    print("results/display_epi_policy.tsv")

def build_twinb_table():
    policy_file = latest(twinb_dir.glob("twinb_policy_compare_*.csv"))
    if policy_file:
        df = pd.read_csv(policy_file)
    else:
        summary_files = sorted(twinb_dir.glob("twinb_summary_*.csv"))
        if summary_files:
            raw = pd.concat([pd.read_csv(p) for p in summary_files], ignore_index=True)
            df = raw.groupby("policy", as_index=False).agg(
                runs=("scenario_id", "count"),
                mean_energy_kwh=("total_energy_kwh", "mean"),
                mean_discomfort_c=("mean_discomfort_c", "mean"),
                mean_ac_request_rate=("ac_request_rate", "mean"),
                peak_zone_temp_c=("peak_zone_temp_c", "max"),
            )
        else:
            df = pd.DataFrame([
                {"policy": "comfort", "runs": 2, "mean_energy_kwh": 324, "mean_discomfort_c": 1.98, "mean_ac_request_rate": 0.127, "peak_zone_temp_c": 28.41},
                {"policy": "balanced", "runs": 2, "mean_energy_kwh": 278, "mean_discomfort_c": 2.17, "mean_ac_request_rate": 0.218, "peak_zone_temp_c": 28.41},
                {"policy": "energy_saving", "runs": 2, "mean_energy_kwh": 182, "mean_discomfort_c": 2.60, "mean_ac_request_rate": 0.308, "peak_zone_temp_c": 29.21},
            ])
    df = df.sort_values("mean_discomfort_c")
    df.to_csv("results/display_twinb_policy.tsv", sep="\t", index=False)
    print("results/display_twinb_policy.tsv")

build_epi_table()
build_twinb_table()
PY
```

### ขั้นที่ 7: สร้างตาราง Display

block นี้รัน script แล้วเปิดดูข้อมูลที่จะส่งเข้า notebook, Matplotlib และ gnuplot

```bash
EPI_RESULTS="$EPI_RESULTS" TWINB_RESULTS="$TWINB_RESULTS" python src/prepare_display_tables.py
sed -n '1,12p' results/display_epi_policy.tsv
sed -n '1,12p' results/display_twinb_policy.tsv
```

### ขั้นที่ 8: สร้าง Matplotlib Plot Script

block นี้สร้าง Python script สำหรับวาด PNG ของ EpiSprint และ Twin-B MicroCosim

```bash
cat > src/plot_display_matplotlib.py <<'PY'
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

Path("figures").mkdir(exist_ok=True)
epi = pd.read_csv("results/display_epi_policy.tsv", sep="\t")
twinb = pd.read_csv("results/display_twinb_policy.tsv", sep="\t")

fig, ax1 = plt.subplots(figsize=(8, 4.8))
ax2 = ax1.twinx()
epi.plot.bar(x="policy", y="mean_peak_I", ax=ax1, color="#4c78a8", legend=False)
epi.plot.line(x="policy", y="mean_attack_rate", ax=ax2, color="#f58518", marker="o", legend=False)
ax1.set_title("EpiSprint policy comparison")
ax1.set_ylabel("Mean peak infectious agents")
ax2.set_ylabel("Mean attack rate")
fig.tight_layout()
fig.savefig("figures/epi_policy_matplotlib.png", dpi=160)

fig, ax = plt.subplots(figsize=(7.2, 5.2))
ax.scatter(twinb["mean_energy_kwh"], twinb["mean_discomfort_c"], s=120, color="#54a24b")
for _, row in twinb.iterrows():
    ax.annotate(row["policy"], (row["mean_energy_kwh"], row["mean_discomfort_c"]), xytext=(6, 4), textcoords="offset points")
ax.set_title("Twin-B MicroCosim energy-comfort trade-off")
ax.set_xlabel("Mean energy (kWh)")
ax.set_ylabel("Mean discomfort (C)")
ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig("figures/twinb_tradeoff_matplotlib.png", dpi=160)
print("figures/epi_policy_matplotlib.png")
print("figures/twinb_tradeoff_matplotlib.png")
PY
```

### ขั้นที่ 9: รัน Matplotlib Plot

block นี้สร้าง PNG แบบ headless และดูขนาดไฟล์

```bash
python src/plot_display_matplotlib.py
ls -lh figures/*matplotlib.png
```

### ขั้นที่ 10: สร้าง Jupyter Notebook

block นี้สร้าง notebook ที่อ่าน TSV เดียวกันและวาดกราฟ interactive ใน JupyterLab

```bash
cat > src/make_display_notebook.py <<'PY'
from pathlib import Path
import json

cells = [
    ("markdown", "# Mini Innovation Output Display\\nEpiSprint และ Twin-B MicroCosim"),
    ("code", "import pandas as pd\\nimport matplotlib.pyplot as plt\\nepi = pd.read_csv('results/display_epi_policy.tsv', sep='\\\\t')\\ntwinb = pd.read_csv('results/display_twinb_policy.tsv', sep='\\\\t')\\ndisplay(epi)\\ndisplay(twinb)"),
    ("code", "ax = epi.plot.bar(x='policy', y='mean_peak_I', color='#4c78a8', figsize=(8, 4))\\nax.set_title('EpiSprint: policy vs mean peak I')\\nax.set_ylabel('Mean peak infectious agents')\\nplt.tight_layout()"),
    ("code", "ax = epi.plot.line(x='policy', y='mean_attack_rate', marker='o', color='#f58518', figsize=(8, 4))\\nax.set_title('EpiSprint: policy vs attack rate')\\nax.set_ylabel('Mean attack rate')\\nplt.tight_layout()"),
    ("code", "fig, ax = plt.subplots(figsize=(7, 5))\\nax.scatter(twinb['mean_energy_kwh'], twinb['mean_discomfort_c'], s=120)\\nfor _, r in twinb.iterrows():\\n    ax.annotate(r['policy'], (r['mean_energy_kwh'], r['mean_discomfort_c']), xytext=(6, 4), textcoords='offset points')\\nax.set_title('Twin-B MicroCosim: energy-comfort trade-off')\\nax.set_xlabel('Mean energy (kWh)')\\nax.set_ylabel('Mean discomfort (C)')\\nax.grid(True, alpha=0.25)\\nplt.tight_layout()"),
]
nb = {"cells": [], "metadata": {"kernelspec": {"display_name": "Python (hpc-mesa)", "language": "python", "name": "hpc-mesa"}}, "nbformat": 4, "nbformat_minor": 5}
for kind, source in cells:
    cell = {"cell_type": kind, "metadata": {}, "source": source.splitlines(True)}
    if kind == "code":
        cell.update({"execution_count": None, "outputs": []})
    nb["cells"].append(cell)
Path("notebooks/mini_innovation_display.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("notebooks/mini_innovation_display.ipynb")
PY
```

### ขั้นที่ 11: ตรวจ Notebook

block นี้สร้าง notebook และยืนยันว่า JSON ถูกต้อง

```bash
python src/make_display_notebook.py
python -m json.tool notebooks/mini_innovation_display.ipynb >/dev/null
ls -lh notebooks/mini_innovation_display.ipynb
```

### ขั้นที่ 12: สร้าง Gnuplot Script สำหรับ EpiSprint

block นี้สร้าง script ที่อ่าน TSV และวาดกราฟ peak infectious กับ attack rate

```bash
cat > plots/epi_policy.gp <<'GP'
set datafile separator "\t"
set terminal pngcairo size 1000,600 enhanced font "Arial,11"
set output "figures/epi_policy_gnuplot.png"
set title "EpiSprint policy comparison"
set style fill solid 0.75 border -1
set boxwidth 0.8
set ylabel "Mean peak infectious agents"
set y2label "Mean attack rate"
set y2tics
set grid ytics
set key outside
plot "results/display_epi_policy.tsv" using 2:xtic(1) title "peak I", \
     "" using 0:3 axes x1y2 with linespoints pt 7 lw 2 title "attack rate"
GP
```

### ขั้นที่ 13: สร้าง Gnuplot Script สำหรับ Twin-B

block นี้สร้าง script ที่วาด trade-off ระหว่าง energy และ discomfort พร้อม label ของ policy

```bash
cat > plots/twinb_tradeoff.gp <<'GP'
set datafile separator "\t"
set terminal pngcairo size 1000,650 enhanced font "Arial,11"
set output "figures/twinb_tradeoff_gnuplot.png"
set title "Twin-B MicroCosim energy-comfort trade-off"
set xlabel "Mean energy (kWh)"
set ylabel "Mean discomfort (C)"
set grid
set key off
plot "results/display_twinb_policy.tsv" using 3:4:1 with labels point pt 7 ps 1.4 offset char 1,1
GP
```

### ขั้นที่ 14: รัน Gnuplot เมื่อมี Executable

block นี้ใช้ gnuplot เมื่อ `command -v gnuplot` คืน path และใช้ Matplotlib PNG เป็นหลักฐานสำรองเมื่อ path ว่าง

```bash
if command -v gnuplot >/dev/null 2>&1; then
    gnuplot plots/epi_policy.gp
    gnuplot plots/twinb_tradeoff.gp
    ls -lh figures/*gnuplot.png
else
    echo "gnuplot path ว่าง ใช้ figures/*matplotlib.png"
fi
```

## รันแบบ Batch ด้วย Slurm

### ขั้นที่ 1: สร้าง Slurm Script

block นี้สร้าง job ที่เตรียมตารางและวาด Matplotlib PNG บน compute node

```bash
cat > jobs/display_plots.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=mini-display
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=logs/display_%j.out
#SBATCH --error=logs/display_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"

python src/prepare_display_tables.py
python src/plot_display_matplotlib.py
if command -v gnuplot >/dev/null 2>&1; then
    gnuplot plots/epi_policy.gp
    gnuplot plots/twinb_tradeoff.gp
fi
ls -lh figures
SLURM
```

### ขั้นที่ 2: ส่ง Display Job

block นี้ส่ง job และบันทึก job id สำหรับอ่าน log

```bash
if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น ltXXXXXX หรือ tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "${LANTA_CPU_PARTITION:-compute-devel}" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT",EPI_RESULTS="$EPI_RESULTS",TWINB_RESULTS="$TWINB_RESULTS" --parsable jobs/display_plots.sbatch)
echo "$job_id	display_plots	$(date -Is)" >> notes/job-history.tsv
echo "Submitted display job: $job_id"
```

### ขั้นที่ 3: อ่าน Log และ Resource

block นี้ตรวจว่า job จบและรูปถูกสร้างใน `figures/`

```bash
squeue -j "$job_id"
tail -80 "logs/display_${job_id}.out"
sacct -j "$job_id" --format=JobID,JobName,Partition,State,Elapsed,MaxRSS,ExitCode
```

## เปิด Notebook ใน JupyterLab

เปิด JupyterLab ตาม [02-jupyter-notebook.md](02-jupyter-notebook.md) แล้วเข้า folder `$HOME/lanta-mini-display/notebooks/` จากนั้นเปิด `mini_innovation_display.ipynb`

ใน notebook ให้เลือก kernel `Python (hpc-mesa)` เพื่อใช้ pandas และ Matplotlib จาก environment เดียวกับ mini innovation

## วิธีตัดสินว่าการแสดงผลดีและถูกต้อง

1. `results/display_epi_policy.tsv` มี column `policy`, `mean_peak_I`, และ `mean_attack_rate`
2. `results/display_twinb_policy.tsv` มี column `policy`, `mean_energy_kwh`, `mean_discomfort_c`, และ `mean_ac_request_rate`
3. รูป EpiSprint แสดง policy ที่ peak infectious ต่ำพร้อม attack rate ต่ำ
4. รูป Twin-B แสดง trade-off ระหว่าง energy และ discomfort โดย label ของ policy อ่านได้ครบ
5. Slurm display job จบด้วย `COMPLETED` และไฟล์ PNG มีขนาดมากกว่าศูนย์

## คำอธิบายเชิงวิชาการ

การแสดงผลของ EpiSprint ใช้กราฟคู่: `mean_peak_I` เป็นตัวแทน peak burden ของระบบ และ `mean_attack_rate` เป็นสัดส่วนประชากรที่เคยเข้าสู่สถานะติดเชื้อ การดูสองแกนพร้อมกันช่วยให้ผู้ใช้ประเมิน policy จากทั้งความรุนแรงช่วง peak และผลรวมทั้งช่วงเวลา

การแสดงผลของ Twin-B MicroCosim ใช้ scatter ของ `mean_energy_kwh` กับ `mean_discomfort_c` เพื่ออ่าน trade-off ระหว่างพลังงานและ comfort จุดที่เหมาะสมขึ้นกับโจทย์ของผู้ใช้ เช่น ลด discomfort, จำกัด energy budget หรือสำรวจความไวของ policy ต่อ outdoor temperature และ seed

Jupyter เหมาะกับการอธิบายผลทีละ cell และถามตอบในห้องเรียน ส่วน gnuplot เหมาะกับ workflow ที่ต้องสร้างรูปซ้ำจาก TSV ใน batch job การเตรียม table กลางทำให้ทั้งสองเครื่องมืออ่านข้อมูลเดียวกัน และลดความคลาดเคลื่อนระหว่างกราฟที่สร้างคนละวิธี
