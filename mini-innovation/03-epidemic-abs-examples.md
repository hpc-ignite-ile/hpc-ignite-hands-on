# 03 พัฒนาและรัน Epidemic ABS ด้วย Mesa

หน้านี้สร้าง agent-based simulation แบบ SEIR สำหรับ mini innovation `LANTA EpiSprint` แล้วรัน 3 วิธีที่ใช้แนวคิดจาก lab หลักของหนังสือ: single Slurm job, job array และ multicore ensemble ภายในหนึ่ง node

เตรียม environment ด้วย [01-custom-python-env-module.md](01-custom-python-env-module.md) ก่อนเริ่มหน้านี้

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `module use`, `module load`, `cat > file <<'PY'`, `sbatch`, `squeue`, `tail`, job array, `SLURM_ARRAY_TASK_ID`, และ multicore worker

## Copy-Paste จากเครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

## Copy-Paste เตรียม Code และ Scenario บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของ EpiSprint และตั้งค่า account, project, partition, และ module path ที่ใช้ร่วมกันทั้งหน้า

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p configs jobs logs notes prompts results src

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
```

### ขั้นที่ 2: ตรวจ Mesa module

ขั้นนี้ยืนยันว่า environment จากหน้า 01 พร้อมใช้ก่อนสร้างและส่ง simulation job

```bash
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT}"
module load hpc-mesa/2.3.4
python - <<'PY'
import mesa, pandas
print("mesa", mesa.__version__)
print("pandas", pandas.__version__)
PY
```

### ขั้นที่ 3: เขียน schema และ agent behavior

ขั้นนี้สร้างครึ่งแรกของ `src/epi_model.py`: กำหนดสถานะ SEIR, scenario, และพฤติกรรมของ agent หนึ่งคน

```bash
cat > src/epi_model.py <<'PY'
from collections import Counter
from dataclasses import dataclass

from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation

S, E, I, R = "S", "E", "I", "R"

@dataclass
class Scenario:
    scenario_id: str
    policy: str
    beta: float
    compliance: float
    seed: int
    agents: int
    days: int

class Person(Agent):
    def __init__(self, unique_id, model, compliance):
        super().__init__(unique_id, model)
        self.compliance = compliance
        self.state = S
        self.days = 0

    def step(self):
        if self.state in (E, I):
            self.days += 1
        if self.state == E and self.days >= self.model.incubation_days:
            self.state, self.days = I, 0
        elif self.state == I and self.days >= self.model.recovery_days:
            self.state, self.days = R, 0

        isolating = self.state == I and self.model.policy in {"isolation", "combined"}
        isolating = isolating and self.model.random.random() < 0.75 * self.compliance
        if isolating:
            return
        x, y = self.pos
        dx, dy = self.model.random.choice([-1, 0, 1]), self.model.random.choice([-1, 0, 1])
        self.model.grid.move_agent(self, ((x + dx) % self.model.width, (y + dy) % self.model.height))
PY
```

### ขั้นที่ 4: เติม model dynamics และ sanity count

ขั้นนี้เติมครึ่งหลังของ `src/epi_model.py`: สร้างประชากรบน grid, คำนวณการติดเชื้อ, และคืนจำนวน `S/E/I/R` รายวัน

```bash
cat >> src/epi_model.py <<'PY'

class EpiModel(Model):
    def __init__(self, scenario, width=70, height=70):
        super().__init__()
        self.random.seed(scenario.seed)
        self.scenario = scenario
        self.policy = scenario.policy
        self.beta = scenario.beta
        self.width, self.height = width, height
        self.incubation_days, self.recovery_days = 3, 7
        self.grid = MultiGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.new_exposures = 0
        for i in range(scenario.agents):
            compliance = min(1.0, max(0.0, self.random.gauss(scenario.compliance, 0.12)))
            person = Person(i, self, compliance)
            self.schedule.add(person)
            self.grid.place_agent(person, (self.random.randrange(width), self.random.randrange(height)))
        for person in self.random.sample(self.schedule.agents, max(1, scenario.agents // 100)):
            person.state = I

    def effective_beta(self):
        if self.policy == "baseline":
            return self.beta
        if self.policy in {"mask", "isolation"}:
            return self.beta * 0.60
        return self.beta * 0.40

    def spread(self):
        exposed = []
        for source in self.schedule.agents:
            if source.state == I:
                for other in self.grid.get_neighbors(source.pos, moore=True, include_center=True):
                    if other.state == S and self.random.random() < self.effective_beta():
                        exposed.append(other)
        self.new_exposures = 0
        for person in set(exposed):
            person.state, person.days = E, 0
            self.new_exposures += 1

    def step(self):
        self.spread()
        self.schedule.step()

    def counts(self, day):
        c = Counter(person.state for person in self.schedule.agents)
        return {"day": day, "S": c[S], "E": c[E], "I": c[I], "R": c[R], "new_exposures": self.new_exposures}

def run_scenario(scenario):
    model = EpiModel(scenario)
    records = [model.counts(0)]
    for day in range(1, scenario.days + 1):
        model.step()
        records.append(model.counts(day))
    return records
PY
```

### ขั้นที่ 5: สร้าง runner สำหรับหนึ่ง scenario

ขั้นนี้สร้าง `src/run_scenario.py` ให้รับ parameter จาก command line แล้วเขียน daily CSV และ summary CSV

```bash
cat > src/run_scenario.py <<'PY'
import argparse, csv, os
from pathlib import Path
from epi_model import Scenario, run_scenario

p = argparse.ArgumentParser()
p.add_argument("--scenario-id", required=True)
p.add_argument("--policy", required=True, choices=["baseline", "mask", "isolation", "combined"])
p.add_argument("--beta", type=float, required=True)
p.add_argument("--compliance", type=float, required=True)
p.add_argument("--seed", type=int, required=True)
p.add_argument("--agents", type=int, default=1200)
p.add_argument("--days", type=int, default=35)
a = p.parse_args()

scenario = Scenario(a.scenario_id, a.policy, a.beta, a.compliance, a.seed, a.agents, a.days)
records = run_scenario(scenario)
job = os.environ.get("SLURM_ARRAY_JOB_ID", os.environ.get("SLURM_JOB_ID", "manual"))
task = os.environ.get("SLURM_ARRAY_TASK_ID", "0")
run_id = f"{job}_{task}_{scenario.scenario_id}"
Path("results").mkdir(exist_ok=True)
daily = Path(f"results/epi_daily_{run_id}.csv")
summary = Path(f"results/epi_summary_{run_id}.csv")

with daily.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["day", "S", "E", "I", "R", "new_exposures"])
    w.writeheader(); w.writerows(records)
peak = max(records, key=lambda r: r["I"])
final = records[-1]
row = {"scenario_id": scenario.scenario_id, "policy": scenario.policy, "beta": scenario.beta,
       "compliance": scenario.compliance, "seed": scenario.seed, "agents": scenario.agents,
       "peak_day": peak["day"], "peak_I": peak["I"],
       "attack_rate": round((final["E"] + final["I"] + final["R"]) / scenario.agents, 6)}
with summary.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(row)); w.writeheader(); w.writerow(row)
print(f"summary={summary}")
print(f"daily={daily}")
print(f"peak_I={row['peak_I']} attack_rate={row['attack_rate']}")
PY
```

### ขั้นที่ 6: สร้างตัวรวมผลลัพธ์

ขั้นนี้สร้าง `src/merge_results.py` เพื่อรวม summary CSV หลายไฟล์และคำนวณค่าเฉลี่ยราย policy

```bash
cat > src/merge_results.py <<'PY'
import argparse
import glob
from pathlib import Path
import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--pattern", default="results/epi_summary_*.csv")
p.add_argument("--output-prefix", default="results/epi")
a = p.parse_args()

files = [Path(path) for path in sorted(glob.glob(a.pattern))]
if not files:
    raise SystemExit(f"missing files for pattern: {a.pattern}")

df = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
df.to_csv(f"{a.output_prefix}_summary_all.csv", index=False)
table = df.groupby("policy", as_index=False).agg(
    runs=("scenario_id", "count"),
    mean_peak_I=("peak_I", "mean"),
    mean_attack_rate=("attack_rate", "mean"),
).sort_values("mean_peak_I")
table.to_csv(f"{a.output_prefix}_policy_compare.csv", index=False)
print(table.to_string(index=False))
PY
```

### ขั้นที่ 7: สร้าง multicore runner

ขั้นนี้สร้าง `src/run_many.py` เพื่อรันหลาย scenario ใน allocation เดียวตามจำนวน CPU ที่ Slurm ให้มา

```bash
cat > src/run_many.py <<'PY'
import argparse, csv, multiprocessing as mp, os, subprocess

def run(row):
    cmd = ["python", "src/run_scenario.py"]
    for key in ["scenario_id", "policy", "beta", "compliance", "seed", "agents", "days"]:
        cmd += ["--" + key.replace("_", "-"), row[key]]
    subprocess.check_call(cmd)
    return row["scenario_id"]

p = argparse.ArgumentParser()
p.add_argument("--csv", default="configs/epi_scenarios.csv")
p.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
a = p.parse_args()
rows = list(csv.DictReader(open(a.csv, newline="", encoding="utf-8")))
workers = max(1, min(a.workers, len(rows)))
print(f"running {len(rows)} scenarios with workers={workers}")
with mp.Pool(processes=workers) as pool:
    for scenario_id in pool.imap_unordered(run, rows):
        print(f"done {scenario_id}")
PY
```

### ขั้นที่ 8: สร้างตาราง scenario

ขั้นนี้สร้าง input หลักของการทดลอง ทุกแถวคือหนึ่ง scenario ที่ Slurm array หรือ multicore runner จะอ่าน

```bash
cat > configs/epi_scenarios.csv <<'EOF'
scenario_id,policy,beta,compliance,seed,agents,days
baseline_1,baseline,0.18,0.40,101,1200,35
baseline_2,baseline,0.20,0.55,102,1200,35
mask_1,mask,0.18,0.40,201,1200,35
mask_2,mask,0.20,0.55,202,1200,35
isolation_1,isolation,0.18,0.40,301,1200,35
isolation_2,isolation,0.20,0.55,302,1200,35
combined_1,combined,0.18,0.40,401,1200,35
combined_2,combined,0.20,0.55,402,1200,35
EOF
```

### ขั้นที่ 9: สร้าง AI scaffold

ขั้นนี้สร้าง prompt สำหรับใช้ AI ช่วยตรวจ scenario, resource request และคำอธิบายผล โดยยึด log และ output เป็นหลักฐาน

```bash
cat > prompts/ai-scaffold-th.md <<'EOF'
# AI Scaffold สำหรับ LANTA EpiSprint

Scenario coach: สร้าง scenario เพิ่มในรูปแบบ CSV โดยเปลี่ยนทีละปัจจัย และอธิบายตัวแปรควบคุม

Slurm reviewer: ตรวจ account, partition, walltime, cpus-per-task, array concurrency, output log และ reproducibility ของ job script

Results tutor: อ่าน epi_policy_compare.csv แล้วอธิบาย policy, peak_I, attack_rate, random seed, uncertainty และข้อจำกัดของแบบจำลอง synthetic
EOF
```

### ขั้นที่ 10: ตรวจ syntax ก่อนส่งงาน

ขั้นนี้ใช้ Python compile check เพื่อจับ syntax error ตั้งแต่บน login node และยืนยันว่า module ที่ใช้คือ `hpc-mesa/2.3.4`

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
python -m py_compile src/epi_model.py src/run_scenario.py src/merge_results.py src/run_many.py
head -5 configs/epi_scenarios.csv
echo "source, scenario, prompt พร้อมสำหรับ Slurm"
```

## Example 1: Single Slurm Job

วิธีนี้ใช้สำหรับ smoke test ก่อนให้ผู้ใช้ทั้งห้องรัน array ให้รัน single job ให้ผ่านก่อนเสมอ

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-episprint"
```

### ขั้นที่ 2: สร้าง Slurm script `jobs/epi_single.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/epi_single.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-single
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:06:00
#SBATCH --output=logs/epi_single_%j.out
#SBATCH --error=logs/epi_single_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"

python src/run_scenario.py \
    --scenario-id single_baseline \
    --policy baseline \
    --beta 0.18 \
    --compliance 0.45 \
    --seed 42 \
    --agents 1500 \
    --days 45
SLURM
```

### ขั้นที่ 3: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/epi_single.sbatch)
echo "$job_id	epi_single	$(date -Is)" >> notes/job-history.tsv
echo "Submitted single job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -60 logs/epi_single_${job_id}.out"
```

## Example 2: Slurm Job Array

วิธีนี้ใช้ตาราง scenario แล้วให้ Slurm แตกงานย่อย ผู้ใช้แต่ละทีมสามารถรัน array สั้น ๆ ของตนเองได้

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-episprint"
```

### ขั้นที่ 2: สร้าง Slurm script `jobs/epi_array.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/epi_array.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-array
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:08:00
#SBATCH --array=1-8%2
#SBATCH --output=logs/epi_array_%A_%a.out
#SBATCH --error=logs/epi_array_%A_%a.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"

line_number=$((SLURM_ARRAY_TASK_ID + 1))
line=$(sed -n "${line_number}p" configs/epi_scenarios.csv)
IFS=, read -r scenario_id policy beta compliance seed agents days <<< "$line"

python src/run_scenario.py \
    --scenario-id "$scenario_id" \
    --policy "$policy" \
    --beta "$beta" \
    --compliance "$compliance" \
    --seed "$seed" \
    --agents "$agents" \
    --days "$days"
SLURM
```

### ขั้นที่ 3: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/epi_array.sbatch)
echo "$job_id	epi_array	$(date -Is)" >> notes/job-history.tsv
echo "Submitted array job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Logs: ls logs/epi_array_${job_id}_*.out"
echo "Results: ls results/epi_summary_${job_id}_*.csv"
```

เมื่อ array จบแล้ว merge ผลลัพธ์

```bash
cd "$HOME/lanta-episprint"
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
python src/merge_results.py \
    --pattern "results/epi_summary_${job_id}_*.csv" \
    --output-prefix "results/epi_array_${job_id}" \
    | tee notes/epi-policy-compare.txt
cat "results/epi_array_${job_id}_policy_compare.csv"
```

## Example 3: Multicore Ensemble ในหนึ่ง Node

วิธีนี้ใช้ `SLURM_CPUS_PER_TASK` เพื่อให้ Python เปิดหลาย process ภายในหนึ่ง allocation ผู้ใช้จะเห็นความต่างระหว่าง job array กับหลาย worker ใน job เดียว

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
cd "$HOME/lanta-episprint"
```

### ขั้นที่ 2: สร้าง Slurm script `jobs/epi_multicore.sbatch`

ขั้นนี้สร้างไฟล์ Slurm ที่ระบุ resource, module, working directory และคำสั่งที่รันบน compute node

```bash
cat > jobs/epi_multicore.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-multicore
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:08:00
#SBATCH --output=logs/epi_multicore_%j.out
#SBATCH --error=logs/epi_multicore_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=1

python src/run_many.py --csv configs/epi_scenarios.csv --workers "${SLURM_CPUS_PER_TASK:-1}"
python src/merge_results.py \
    --pattern "results/epi_summary_${SLURM_JOB_ID}_*.csv" \
    --output-prefix "results/epi_multicore_${SLURM_JOB_ID}"
SLURM
```

### ขั้นที่ 3: ส่งงานเข้า Slurm

ขั้นนี้ส่ง job script ที่เพิ่งสร้างไว้ด้วย `sbatch` แล้วบันทึก job id เพื่อใช้ตามคิวและอ่าน log ภายหลัง

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/epi_multicore.sbatch)
echo "$job_id	epi_multicore	$(date -Is)" >> notes/job-history.tsv
echo "Submitted multicore job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/epi_multicore_${job_id}.out"
```

## คำอธิบาย

ใน lab นี้ ผู้ใช้จะรันแบบจำลอง SEIR แบบ agent-based simulation แต่ละ agent มีสถานะ `S`, `E`, `I`, หรือ `R` และเคลื่อนที่บน `MultiGrid` ของ Mesa นโยบายในตัวอย่างเป็นข้อมูล synthetic สำหรับเรียนรู้การออกแบบ experiment, uncertainty และการอ่านหลักฐานจาก simulation

ตัวอย่างที่ 1 เป็น single Slurm job สำหรับตรวจว่า code, module, account และ partition ใช้งานได้ ตัวอย่างที่ 2 ใช้ job array เพื่อรันหลาย scenario จาก CSV ตัวอย่างที่ 3 ใช้หลาย worker ภายในหนึ่ง node เพื่อให้ผู้ใช้เห็น parallelism อีกรูปแบบหนึ่ง

แนวปฏิบัติที่ดีคือรัน smoke job ก่อนเพื่อยืนยัน environment แล้วค่อยขยายเป็น array หรือ multicore ensemble บันทึก seed และพารามิเตอร์ทุกครั้ง เก็บ log แยกตาม job id และสรุปผลจากหลาย scenario เพื่อแยก pattern ของ model ออกจากความผันผวนของ run เดี่ยว

ไฟล์ `prompts/ai-scaffold-th.md` เป็นตัวช่วยสำหรับถาม AI ให้ช่วยตรวจ scenario, ตรวจ Slurm script และช่วยอธิบาย CSV โดยให้คำตอบผูกกับหลักฐานหลักคือ code, config, job log และ result file

## Check

```bash
cd "$HOME/lanta-episprint"
find results -maxdepth 1 -type f | sort | tail -30
cat notes/job-history.tsv 2>/dev/null || true
cat notes/epi-policy-compare.txt 2>/dev/null || true
```

เมื่อสำเร็จ ผู้ใช้ควรเห็นไฟล์ `epi_daily_*.csv`, `epi_summary_*.csv`, `epi_array_<jobid>_summary_all.csv`, `epi_array_<jobid>_policy_compare.csv`, และ `epi_multicore_<jobid>_policy_compare.csv` ผลลัพธ์ที่ใช้ได้ควรมี header ครบ, จำนวนวันตรงกับค่า `days`, ค่า `peak_I` อยู่ในช่วง 0 ถึงจำนวน agent, และ policy comparison อ้างอิงหลาย scenario หรือหลาย seed เมื่อต้องแก้ปัญหา ให้เปิด error log เฉพาะ job หรือ array task นั้นก่อน เช่น `tail -80 logs/epi_array_<jobid>_<taskid>.err` เมื่อ import Mesa error ให้ตรวจ `module use "$EPI_MODULE_ROOT"` และ `module load hpc-mesa/2.3.4`
