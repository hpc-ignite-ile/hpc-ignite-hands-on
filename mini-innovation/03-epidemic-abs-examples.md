# 03 พัฒนาและรัน Epidemic ABS ด้วย Mesa

หน้านี้สร้าง agent-based simulation แบบ SEIR สำหรับ mini innovation `LANTA EpiSprint` แล้วรัน 3 วิธีที่ใช้แนวคิดจาก lab หลักของหนังสือ: single Slurm job, job array และ multicore ensemble ภายในหนึ่ง node

ถ้ายังไม่ได้สร้าง environment ให้ทำ [01-custom-python-env-module.md](01-custom-python-env-module.md) ก่อน

## Copy-Paste จากเครื่อง Local

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

## Copy-Paste เตรียม Code และ Scenario บน LANTA

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

if [ ! -f "$EPI_MODULE_ROOT/hpc-mesa/2.3.4.lua" ]; then
    echo "ไม่พบ module: $EPI_MODULE_ROOT/hpc-mesa/2.3.4.lua"
    echo "ให้ทำหน้า 01-custom-python-env-module.md ก่อน"
    exit 1
fi

cat > src/epi_model.py <<'PY'
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation

S = "S"
E = "E"
I = "I"
R = "R"


class Person(Agent):
    def __init__(self, unique_id: int, model: "EpiModel", age_group: str, compliance: float):
        super().__init__(unique_id, model)
        self.age_group = age_group
        self.compliance = compliance
        self.state = S
        self.days_in_state = 0

    def step(self) -> None:
        if self.state in (E, I):
            self.days_in_state += 1

        if self.state == E and self.days_in_state >= self.model.incubation_days:
            self.state = I
            self.days_in_state = 0
        elif self.state == I and self.days_in_state >= self.model.recovery_days:
            self.state = R
            self.days_in_state = 0

        should_isolate = (
            self.state == I
            and self.model.policy in {"isolation", "combined"}
            and self.model.random.random() < self.model.isolation_strength * self.compliance
        )
        if not should_isolate:
            x, y = self.pos
            dx = self.model.random.choice([-1, 0, 1])
            dy = self.model.random.choice([-1, 0, 1])
            self.model.grid.move_agent(self, ((x + dx) % self.model.width, (y + dy) % self.model.height))


@dataclass
class Scenario:
    scenario_id: str
    policy: str
    beta: float
    compliance: float
    seed: int
    agents: int
    days: int


class EpiModel(Model):
    def __init__(
        self,
        scenario: Scenario,
        width: int = 70,
        height: int = 70,
        initial_infected_fraction: float = 0.01,
        incubation_days: int = 3,
        recovery_days: int = 7,
    ):
        super().__init__()
        self.random.seed(scenario.seed)
        self.scenario = scenario
        self.policy = scenario.policy
        self.beta = scenario.beta
        self.compliance = scenario.compliance
        self.width = width
        self.height = height
        self.incubation_days = incubation_days
        self.recovery_days = recovery_days
        self.isolation_strength = 0.75
        self.grid = MultiGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.new_exposures = 0

        age_choices = ["child", "adult", "older"]
        age_weights = [0.20, 0.65, 0.15]
        for i in range(scenario.agents):
            age_group = self.random.choices(age_choices, weights=age_weights, k=1)[0]
            compliance = min(1.0, max(0.0, self.random.gauss(scenario.compliance, 0.12)))
            person = Person(i, self, age_group, compliance)
            self.schedule.add(person)
            self.grid.place_agent(person, (self.random.randrange(width), self.random.randrange(height)))

        initial_infected = max(1, int(scenario.agents * initial_infected_fraction))
        for person in self.random.sample(self.schedule.agents, initial_infected):
            person.state = I

    def effective_beta(self, source: Person) -> float:
        beta = self.beta
        if self.policy in {"mask", "combined"}:
            beta *= 0.55
        if self.policy in {"school_close", "combined"} and source.age_group == "child":
            beta *= 0.45
        return beta

    def spread(self) -> None:
        exposed = []
        for source in self.schedule.agents:
            if source.state != I:
                continue
            if self.policy in {"isolation", "combined"} and self.random.random() < self.isolation_strength * source.compliance:
                continue
            beta = self.effective_beta(source)
            contacts = self.grid.get_neighbors(source.pos, moore=True, include_center=True)
            for other in contacts:
                if other is source or other.state != S:
                    continue
                if self.random.random() < beta:
                    exposed.append(other)

        seen = set()
        self.new_exposures = 0
        for person in exposed:
            if person.unique_id in seen or person.state != S:
                continue
            person.state = E
            person.days_in_state = 0
            seen.add(person.unique_id)
            self.new_exposures += 1

    def step(self) -> None:
        self.spread()
        self.schedule.step()

    def counts(self, day: int) -> Dict[str, int]:
        count = Counter(person.state for person in self.schedule.agents)
        return {
            "day": day,
            "S": count.get(S, 0),
            "E": count.get(E, 0),
            "I": count.get(I, 0),
            "R": count.get(R, 0),
            "new_exposures": self.new_exposures,
        }


def run_scenario(scenario: Scenario) -> List[Dict[str, int]]:
    model = EpiModel(scenario)
    records = [model.counts(day=0)]
    for day in range(1, scenario.days + 1):
        model.step()
        records.append(model.counts(day=day))
    return records
PY

cat > src/run_scenario.py <<'PY'
import argparse
import csv
import os
from pathlib import Path

from epi_model import Scenario, run_scenario


def default_run_id(scenario_id: str) -> str:
    array_job = os.environ.get("SLURM_ARRAY_JOB_ID")
    array_task = os.environ.get("SLURM_ARRAY_TASK_ID")
    job_id = os.environ.get("SLURM_JOB_ID", "manual")
    if array_job and array_task:
        return f"{array_job}_{array_task}_{scenario_id}"
    return f"{job_id}_{scenario_id}"


parser = argparse.ArgumentParser()
parser.add_argument("--scenario-id", required=True)
parser.add_argument("--policy", required=True, choices=["baseline", "mask", "isolation", "school_close", "combined"])
parser.add_argument("--beta", type=float, required=True)
parser.add_argument("--compliance", type=float, required=True)
parser.add_argument("--seed", type=int, required=True)
parser.add_argument("--agents", type=int, default=5000)
parser.add_argument("--days", type=int, default=90)
args = parser.parse_args()

scenario = Scenario(
    scenario_id=args.scenario_id,
    policy=args.policy,
    beta=args.beta,
    compliance=args.compliance,
    seed=args.seed,
    agents=args.agents,
    days=args.days,
)

records = run_scenario(scenario)
run_id = default_run_id(args.scenario_id)
Path("results").mkdir(exist_ok=True)
daily_path = Path(f"results/epi_daily_{run_id}.csv")
summary_path = Path(f"results/epi_summary_{run_id}.csv")

with daily_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["day", "S", "E", "I", "R", "new_exposures"])
    writer.writeheader()
    writer.writerows(records)

peak = max(records, key=lambda row: row["I"])
final = records[-1]
summary = {
    "scenario_id": scenario.scenario_id,
    "policy": scenario.policy,
    "beta": scenario.beta,
    "compliance": scenario.compliance,
    "seed": scenario.seed,
    "agents": scenario.agents,
    "days": scenario.days,
    "peak_day": peak["day"],
    "peak_I": peak["I"],
    "attack_rate": round((final["E"] + final["I"] + final["R"]) / scenario.agents, 6),
    "daily_file": str(daily_path),
}

with summary_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(summary))
    writer.writeheader()
    writer.writerow(summary)

print(f"summary={summary_path}")
print(f"daily={daily_path}")
print(f"peak_I={summary['peak_I']} attack_rate={summary['attack_rate']}")
PY

cat > src/merge_results.py <<'PY'
from pathlib import Path
import pandas as pd

files = sorted(Path("results").glob("epi_summary_*.csv"))
if not files:
    raise SystemExit("ไม่พบไฟล์ results/epi_summary_*.csv")

df = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
Path("results").mkdir(exist_ok=True)
merged = Path("results/epi_summary_all.csv")
df.to_csv(merged, index=False)

table = (
    df.groupby("policy", as_index=False)
    .agg(runs=("scenario_id", "count"), mean_peak_I=("peak_I", "mean"), mean_attack_rate=("attack_rate", "mean"))
    .sort_values("mean_peak_I")
)
table.to_csv("results/epi_policy_compare.csv", index=False)
print(table.to_string(index=False))
print(f"merged={merged}")
print("compare=results/epi_policy_compare.csv")
PY

cat > src/run_many.py <<'PY'
import argparse
import csv
import multiprocessing as mp
import os
import subprocess


def run(row):
    cmd = [
        "python", "src/run_scenario.py",
        "--scenario-id", row["scenario_id"],
        "--policy", row["policy"],
        "--beta", row["beta"],
        "--compliance", row["compliance"],
        "--seed", row["seed"],
        "--agents", row["agents"],
        "--days", row["days"],
    ]
    subprocess.check_call(cmd)
    return row["scenario_id"]


parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="configs/epi_scenarios.csv")
parser.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "1")))
args = parser.parse_args()

with open(args.csv, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

workers = max(1, min(args.workers, len(rows)))
print(f"running {len(rows)} scenarios with workers={workers}")
with mp.Pool(processes=workers) as pool:
    for scenario_id in pool.imap_unordered(run, rows):
        print(f"done {scenario_id}")
PY

cat > configs/epi_scenarios.csv <<'EOF'
scenario_id,policy,beta,compliance,seed,agents,days
baseline_1,baseline,0.18,0.40,101,5000,90
baseline_2,baseline,0.18,0.55,102,5000,90
baseline_3,baseline,0.20,0.40,103,5000,90
mask_1,mask,0.18,0.40,201,5000,90
mask_2,mask,0.18,0.55,202,5000,90
mask_3,mask,0.20,0.40,203,5000,90
isolation_1,isolation,0.18,0.40,301,5000,90
isolation_2,isolation,0.18,0.55,302,5000,90
isolation_3,isolation,0.20,0.40,303,5000,90
combined_1,combined,0.18,0.40,401,5000,90
combined_2,combined,0.18,0.55,402,5000,90
combined_3,combined,0.20,0.40,403,5000,90
EOF

cat > prompts/ai-scaffold-th.md <<'EOF'
# Prompt สำหรับ AI Scaffold

ใช้ prompt นี้กับ AI assistant เพื่อช่วยคิดการทดลอง ไม่ใช่เพื่อให้ AI ตัดสินใจแทนผล simulation

## Scenario coach

เรากำลังทำ LANTA EpiSprint ด้วย SEIR agent-based simulation บน LANTA
ช่วยสร้าง scenario เพิ่ม 6 แถวในรูปแบบ CSV โดยให้เปลี่ยนทีละปัจจัย
คอลัมน์คือ scenario_id,policy,beta,compliance,seed,agents,days
ขอให้ runtime สั้นพอสำหรับ compute-devel และอธิบายว่าปัจจัยใดถูกควบคุม

## Slurm reviewer

ตรวจ Slurm script นี้ว่าขอ resource เหมาะกับงานสด 40 คนหรือไม่
เน้น account, partition, walltime, cpus-per-task, array concurrency, output log และ reproducibility

## Results tutor

จาก epi_policy_compare.csv ช่วยอธิบายเป็นภาษาไทยว่า policy ใดลด peak_I ได้ดีที่สุด
ให้พูดถึง uncertainty, random seed, attack_rate และข้อจำกัดของแบบจำลอง synthetic
EOF

module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4

python -m py_compile src/epi_model.py src/run_scenario.py src/merge_results.py src/run_many.py
echo "สร้าง source, scenario, และ prompt เรียบร้อย"
```

## Example 1: Single Slurm Job

วิธีนี้เหมือนงานแรกในหนังสือ เหมาะกับ smoke test ก่อนให้ทั้งห้องรัน array

```bash
cd "$HOME/lanta-episprint"

cat > jobs/epi_single.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-single
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:10:00
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
    --agents 5000 \
    --days 90
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/epi_single.sbatch)
echo "$job_id	epi_single	$(date -Is)" >> notes/job-history.tsv
echo "Submitted single job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -60 logs/epi_single_${job_id}.out"
```

## Example 2: Slurm Job Array

วิธีนี้ใช้ตาราง scenario แล้วให้ Slurm แตกงานย่อย เหมาะกับกิจกรรมสดเพราะแต่ละทีมรัน array สั้น ๆ ของตนเองได้

```bash
cd "$HOME/lanta-episprint"

cat > jobs/epi_array.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-array
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:12:00
#SBATCH --array=1-12%4
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
python src/merge_results.py | tee notes/epi-policy-compare.txt
cat results/epi_policy_compare.csv
```

## Example 3: Multicore Ensemble ในหนึ่ง Node

วิธีนี้ใช้ `SLURM_CPUS_PER_TASK` เพื่อให้ Python เปิดหลาย process ภายในหนึ่ง allocation เหมาะกับการสอนความต่างระหว่าง "หลาย task ใน array" กับ "หลาย worker ใน job เดียว"

```bash
cd "$HOME/lanta-episprint"

cat > jobs/epi_multicore.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=epi-multicore
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=00:15:00
#SBATCH --output=logs/epi_multicore_%j.out
#SBATCH --error=logs/epi_multicore_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"
export OMP_NUM_THREADS=1

python src/run_many.py --csv configs/epi_scenarios.csv --workers "${SLURM_CPUS_PER_TASK:-1}"
python src/merge_results.py
SLURM

job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/epi_multicore.sbatch)
echo "$job_id	epi_multicore	$(date -Is)" >> notes/job-history.tsv
echo "Submitted multicore job: $job_id"
echo "Monitor: squeue -j $job_id"
echo "Read: tail -80 logs/epi_multicore_${job_id}.out"
```

## คำอธิบาย

แบบจำลองนี้ใช้ SEIR เป็นแกนวิทยาศาสตร์ โดยแต่ละ agent มีสถานะ `S`, `E`, `I`, หรือ `R` และมีพฤติกรรมเคลื่อนที่บน `MultiGrid` ของ Mesa นโยบายแต่ละแบบไม่ได้เป็นคำแนะนำทางสาธารณสุขจริง แต่เป็นกลไก synthetic เพื่อให้ผู้เรียนเห็นว่า parameter และ behavior เปลี่ยน curve ได้อย่างไร

Example 1 เป็น smoke test แบบ single Slurm job ถ้าขั้นนี้ล้มเหลว ไม่ควรปล่อยทั้งห้องรัน array เพราะ error เดียวกันจะถูกคูณเป็นหลายงาน Example 2 ใช้ job array ซึ่งเป็นวิธีสำคัญของ HPC สำหรับ scenario sweep หลาย seed หลายนโยบาย และหลายค่าพารามิเตอร์ Example 3 ใช้ multicore ภายในหนึ่ง node เพื่อให้เห็นอีกรูปแบบของ parallelism ที่ต่างจาก job array

AI scaffold อยู่ใน `prompts/ai-scaffold-th.md` หน้าที่ของ AI คือช่วยตรวจ scenario, ตรวจ Slurm และช่วยอธิบายผลจาก CSV โดยต้องย้ำข้อจำกัดของ synthetic model เสมอ หลักฐานของ simulation ยังมาจาก code, config, job log และ result file ไม่ใช่จากคำตอบของ AI

## Check

```bash
cd "$HOME/lanta-episprint"
find results -maxdepth 1 -type f | sort | tail -30
cat notes/job-history.tsv 2>/dev/null || true
cat notes/epi-policy-compare.txt 2>/dev/null || true
```

สัญญาณที่ดีคือมีไฟล์ `epi_daily_*.csv`, `epi_summary_*.csv`, `epi_summary_all.csv` และ `epi_policy_compare.csv` หากไม่มีผลลัพธ์ ให้เปิด error log เฉพาะ job หรือ array task นั้นก่อน เช่น `tail -80 logs/epi_array_<jobid>_<taskid>.err` หาก import Mesa ไม่สำเร็จ ให้ตรวจว่าโหลด module ด้วย `module use "$EPI_MODULE_ROOT"` และ `module load hpc-mesa/2.3.4` แล้วจริงหรือไม่
