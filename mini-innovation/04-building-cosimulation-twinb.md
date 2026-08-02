# 04 Co-Simulation: Scientific Thermal Model กับ ABS แบบ Twin-B

หน้านี้สร้าง mini innovation ชื่อ **Twin-B MicroCosim** โดยย่อแนวคิดจาก [wdiazcarballo/hpcignite-twinb](https://github.com/wdiazcarballo/hpcignite-twinb) ให้เหมาะกับกิจกรรมสดบน LANTA สำหรับผู้ใช้ประมาณ 40 คน

ต้นฉบับ Twin-B ใช้ EnergyPlus เป็น scientific building-energy model และใช้ Mesa เป็น agent-based simulation ของผู้ใช้อาคาร การสื่อสารหลักคือ scientific model ส่งอุณหภูมิราย zone ให้ agent ส่วน agent ส่ง cooling setpoint request กลับไปควบคุม model อาคาร

หน้านี้ใช้ **thermal surrogate model** แบบ first-order heat balance แทน EnergyPlus เต็ม เพื่อให้รันสั้นบน `compute-devel` และยังรักษาสัญญา data exchange เดียวกัน: `zone_temperature -> occupant comfort -> setpoint request -> cooling energy -> next zone_temperature`

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `module use`, `module load`, `cat > file <<'PY'`, `sbatch`, `squeue`, `tail`, `sacct`, `sed`, และ job array

## ภาพรวม

```text
Scientific model: zone heat balance + outdoor weather
        | sends zone temperature
        v
ABS model: Mesa occupants decide AC demand and preferred setpoint
        | sends setpoint request by zone
        v
Scientific model: updates cooling energy and next temperature
```

## Mapping จาก Twin-B ต้นฉบับ

| Twin-B เต็ม | Twin-B MicroCosim ในบทนี้ | เหตุผลสำหรับ training |
|---|---|---|
| EnergyPlus IDF + EPW | first-order thermal surrogate + synthetic hot-day weather | job จบในระดับวินาทีและตรวจสมการได้ |
| `BuildingModel` ใน Mesa | `TwinBCosim` ใน Mesa | เก็บ agent comfort และ setpoint request |
| EnergyPlus callback | loop co-simulation ราย timestep | เห็น data contract ชัดใน CSV |
| distributed setpoint aggregation | Slurm array หลาย scenario | เห็น HPC workflow และ reproducibility |

## Copy-Paste จากเครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: Login เข้า LANTA

block นี้เปิด shell บน login node เพื่อสร้าง source และส่ง Slurm job

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

ผู้ใช้ที่ตั้ง alias ตาม [../docs/SSH_PRIVATE_KEY_LANTA_TH.md](../docs/SSH_PRIVATE_KEY_LANTA_TH.md) สามารถใช้ `ssh lanta`

## Copy-Paste บน LANTA

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม Workspace และตัวแปร

block นี้สร้างพื้นที่ทำงานของ co-simulation และตั้งค่า account, partition, และ module root

```bash
mkdir -p "$HOME/lanta-twinb-micro"
cd "$HOME/lanta-twinb-micro"
mkdir -p configs jobs logs notes prompts results src

if [ -f "$HOME/lanta-episprint/notes/session-env.sh" ]; then
    source "$HOME/lanta-episprint/notes/session-env.sh"
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

### ขั้นที่ 2: ตรวจ Environment

block นี้โหลด `hpc-mesa/2.3.4` และตรวจ package ที่ใช้สร้าง co-simulation

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
python - <<'PY'
import mesa, pandas, yaml
print("mesa", mesa.__version__)
print("pandas", pandas.__version__)
print("pyyaml", yaml.__version__)
PY
```

### ขั้นที่ 3: สร้าง Config ของ Scientific Model

block นี้กำหนด zone, timestep, weather synthetic และ policy ของ cooling setpoint

```bash
cat > configs/twinb_micro.yaml <<'EOF'
simulation:
  scenario_id: balanced_101
  policy: balanced
  seed: 101
  steps: 48
  dt_hours: 0.25
weather:
  base_c: 31.5
  amplitude_c: 5.5
  peak_hour: 15.0
zones:
  - {name: Studio_A, initial_temp_c: 27.8, area_m2: 45, tau_hours: 4.5}
  - {name: Classroom_B, initial_temp_c: 28.4, area_m2: 70, tau_hours: 5.5}
  - {name: Office_C, initial_temp_c: 27.2, area_m2: 36, tau_hours: 6.0}
  - {name: Lab_D, initial_temp_c: 28.0, area_m2: 60, tau_hours: 5.0}
policies:
  comfort: {min_setpoint_c: 23.0, max_setpoint_c: 26.0, cooling_gain: 0.80}
  balanced: {min_setpoint_c: 24.5, max_setpoint_c: 27.0, cooling_gain: 0.65}
  energy_saving: {min_setpoint_c: 26.0, max_setpoint_c: 28.0, cooling_gain: 0.50}
EOF
```

### ขั้นที่ 4: สร้าง Config ของ Occupant Agents

block นี้กำหนดประชากรจำลองตามแนวคิดของ Twin-B: student, staff และ visitor มี preferred temperature และ comfort tolerance ต่างกัน

```bash
cat > configs/occupants.json <<'EOF'
{
  "agent_types": {
    "student": {
      "count": 120,
      "preferred_temp": {"min": 24.0, "max": 26.0},
      "comfort_tolerance": {"min": 1.0, "max": 1.8}
    },
    "staff": {
      "count": 28,
      "preferred_temp": {"min": 24.5, "max": 26.5},
      "comfort_tolerance": {"min": 1.2, "max": 2.2}
    },
    "visitor": {
      "count": 20,
      "preferred_temp": {"min": 24.0, "max": 27.0},
      "comfort_tolerance": {"min": 0.8, "max": 1.5}
    }
  }
}
EOF
```

### ขั้นที่ 5: เขียน Scientific Thermal Model

block นี้สร้างครึ่งแรกของ `src/thermal_surrogate.py` สำหรับเก็บ state ของ zone และคำนวณ outdoor temperature ตามชั่วโมง

```bash
cat > src/thermal_surrogate.py <<'PY'
import math


class ThermalSurrogate:
    def __init__(self, config):
        sim = config["simulation"]
        self.dt_hours = float(sim["dt_hours"])
        self.weather = config["weather"]
        self.zones = {z["name"]: dict(z) for z in config["zones"]}
        self.temps = {
            name: float(zone["initial_temp_c"])
            for name, zone in self.zones.items()
        }
        self.total_energy_kwh = 0.0

    def outdoor_temp(self, step):
        hour = (step * self.dt_hours) % 24.0
        base = float(self.weather["base_c"])
        amp = float(self.weather["amplitude_c"])
        peak = float(self.weather["peak_hour"])
        angle = 2.0 * math.pi * (hour - peak) / 24.0
        return base + amp * math.cos(angle)
PY
```

### ขั้นที่ 6: เติม Coupling Step ของ Scientific Model

block นี้เติมสมการ heat balance และรับ setpoint request จาก ABS ราย zone

```bash
cat >> src/thermal_surrogate.py <<'PY'

    def advance(self, step, setpoints, occupancy, policy):
        outdoor = self.outdoor_temp(step)
        rows = []
        for name, zone in self.zones.items():
            temp = self.temps[name]
            tau = float(zone["tau_hours"])
            area = float(zone["area_m2"])
            occ = int(occupancy.get(name, 0))
            setpoint = setpoints.get(name)

            passive = (outdoor - temp) / tau
            internal_gain = 0.012 * occ
            cooling = 0.0
            if setpoint is not None and temp > setpoint:
                gap = temp - setpoint
                cooling = min(3.0, gap * float(policy["cooling_gain"]))

            next_temp = temp + self.dt_hours * (passive + internal_gain - cooling)
            energy_kwh = cooling * area * 0.18 * self.dt_hours
            self.temps[name] = round(next_temp, 4)
            self.total_energy_kwh += energy_kwh
            rows.append({
                "step": step, "hour": round((step * self.dt_hours) % 24.0, 2),
                "zone": name, "outdoor_temp_c": round(outdoor, 3),
                "zone_temp_c": round(temp, 3), "next_temp_c": round(next_temp, 3),
                "occupants": occ, "setpoint_c": setpoint,
                "cooling_rate_c_per_h": round(cooling, 4),
                "energy_kwh": round(energy_kwh, 6),
            })
        return rows
PY
```

### ขั้นที่ 7: เขียน Mesa Agent

block นี้สร้าง agent ที่อ่านอุณหภูมิห้องแล้วตัดสินใจขอเปิด cooling ตาม preferred temperature และ tolerance

```bash
cat > src/twinb_agents.py <<'PY'
from mesa import Agent, Model
from mesa.time import RandomActivation
from thermal_surrogate import ThermalSurrogate


class OccupantAgent(Agent):
    def __init__(self, unique_id, model, agent_type, preferred_temp, tolerance):
        super().__init__(unique_id, model)
        self.agent_type = agent_type
        self.preferred_temp = preferred_temp
        self.tolerance = tolerance
        self.room = self.model.random.choice(self.model.zone_names)
        self.using_ac = False
        self.requested_setpoint = None
        self.discomfort_c = 0.0

    def step(self):
        if self.model.random.random() < 0.04:
            self.room = self.model.random.choice(self.model.zone_names)
        present = self.model.is_present(self.agent_type)
        temp = self.model.zone_temps[self.room]
        self.discomfort_c = abs(temp - self.preferred_temp)
        self.using_ac = bool(present and temp > self.preferred_temp + self.tolerance)
        self.requested_setpoint = self.preferred_temp if self.using_ac else None
PY
```

### ขั้นที่ 8: เขียน Mesa Model

block นี้สร้าง `TwinBCosim` ให้รวม agent request เป็น setpoint ราย zone แล้วส่งกลับ scientific model

```bash
cat >> src/twinb_agents.py <<'PY'

class TwinBCosim(Model):
    def __init__(self, config, occupants):
        super().__init__()
        self.config = config
        self.random.seed(int(config["simulation"]["seed"]))
        self.science = ThermalSurrogate(config)
        self.zone_names = list(self.science.temps)
        self.zone_temps = dict(self.science.temps)
        self.policy_name = config["simulation"]["policy"]
        self.policy = config["policies"][self.policy_name]
        self.current_step = 0
        self.schedule = RandomActivation(self)
        self.agent_records = []
        self.zone_records = []
        self._create_agents(occupants)

    def sample_range(self, cfg):
        return self.random.uniform(float(cfg["min"]), float(cfg["max"]))

    def _create_agents(self, occupants):
        uid = 0
        for agent_type, cfg in occupants["agent_types"].items():
            for _ in range(int(cfg["count"])):
                agent = OccupantAgent(
                    uid, self, agent_type,
                    self.sample_range(cfg["preferred_temp"]),
                    self.sample_range(cfg["comfort_tolerance"]),
                )
                self.schedule.add(agent)
                uid += 1
PY
```

### ขั้นที่ 9: เติม Logic ของ Co-Simulation

block นี้กำหนดเวลาที่ agent แต่ละประเภทอยู่ในอาคาร, การ clip setpoint ตาม policy และการบันทึก evidence ราย timestep

```bash
cat >> src/twinb_agents.py <<'PY'

    def hour(self):
        return (self.current_step * float(self.config["simulation"]["dt_hours"])) % 24.0

    def is_present(self, agent_type):
        hour = self.hour()
        windows = {
            "student": (8.0, 17.0),
            "staff": (7.5, 18.0),
            "visitor": (10.0, 15.5),
        }
        start, end = windows.get(agent_type, (0.0, 24.0))
        return start <= hour <= end

    def aggregate_setpoints(self):
        per_zone = {zone: [] for zone in self.zone_names}
        for agent in self.schedule.agents:
            if agent.requested_setpoint is not None:
                per_zone[agent.room].append(agent.requested_setpoint)
        out = {}
        for zone, requests in per_zone.items():
            if requests:
                raw = min(requests)
                lo = float(self.policy["min_setpoint_c"])
                hi = float(self.policy["max_setpoint_c"])
                out[zone] = round(min(max(raw, lo), hi), 3)
        return out
PY
```

### ขั้นที่ 10: เติม Step และ Export Records

block นี้ทำให้หนึ่ง timestep เดินครบวงจร scientific model -> ABS -> scientific model และเก็บ CSV-ready records

```bash
cat >> src/twinb_agents.py <<'PY'

    def step(self):
        self.zone_temps = dict(self.science.temps)
        self.schedule.step()
        occupancy = {zone: 0 for zone in self.zone_names}
        for agent in self.schedule.agents:
            if self.is_present(agent.agent_type):
                occupancy[agent.room] += 1
            self.agent_records.append({
                "step": self.current_step, "hour": round(self.hour(), 2),
                "agent_id": agent.unique_id, "agent_type": agent.agent_type,
                "room": agent.room, "zone_temp_c": round(self.zone_temps[agent.room], 3),
                "preferred_temp_c": round(agent.preferred_temp, 3),
                "tolerance_c": round(agent.tolerance, 3),
                "using_ac": int(agent.using_ac),
                "requested_setpoint_c": agent.requested_setpoint,
                "discomfort_c": round(agent.discomfort_c, 3),
            })
        setpoints = self.aggregate_setpoints()
        rows = self.science.advance(self.current_step, setpoints, occupancy, self.policy)
        for row in rows:
            row["scenario_id"] = self.config["simulation"]["scenario_id"]
            row["policy"] = self.policy_name
            self.zone_records.append(row)
        self.current_step += 1
PY
```

### ขั้นที่ 11: สร้าง Runner

block นี้สร้าง command line runner ที่อ่าน config, รัน co-simulation และเขียน agent/zone CSV

```bash
cat > src/run_twinb_cosim.py <<'PY'
import argparse
import json
import os
from pathlib import Path

import pandas as pd
import yaml

from twinb_agents import TwinBCosim


p = argparse.ArgumentParser()
p.add_argument("--config", default="configs/twinb_micro.yaml")
p.add_argument("--occupants", default="configs/occupants.json")
a = p.parse_args()

config = yaml.safe_load(Path(a.config).read_text(encoding="utf-8"))
occupants = json.loads(Path(a.occupants).read_text(encoding="utf-8"))
model = TwinBCosim(config, occupants)
for _ in range(int(config["simulation"]["steps"])):
    model.step()

job = os.environ.get("SLURM_ARRAY_JOB_ID", os.environ.get("SLURM_JOB_ID", "manual"))
task = os.environ.get("SLURM_ARRAY_TASK_ID", "0")
scenario = config["simulation"]["scenario_id"]
run_id = f"{job}_{task}_{scenario}"
Path("results").mkdir(exist_ok=True)
pd.DataFrame(model.agent_records).to_csv(f"results/twinb_agent_{run_id}.csv", index=False)
pd.DataFrame(model.zone_records).to_csv(f"results/twinb_zone_{run_id}.csv", index=False)
PY
```

### ขั้นที่ 12: เติม Summary Output

block นี้ต่อท้าย runner เพื่อเขียน summary CSV ที่ใช้เปรียบเทียบ policy

```bash
cat >> src/run_twinb_cosim.py <<'PY'

agent_df = pd.DataFrame(model.agent_records)
zone_df = pd.DataFrame(model.zone_records)
summary = {
    "scenario_id": scenario,
    "policy": config["simulation"]["policy"],
    "seed": config["simulation"]["seed"],
    "steps": config["simulation"]["steps"],
    "agents": len(model.schedule.agents),
    "zones": len(model.zone_names),
    "total_energy_kwh": round(float(zone_df["energy_kwh"].sum()), 6),
    "mean_discomfort_c": round(float(agent_df["discomfort_c"].mean()), 6),
    "ac_request_rate": round(float(agent_df["using_ac"].mean()), 6),
    "peak_zone_temp_c": round(float(zone_df["zone_temp_c"].max()), 6),
    "mean_zone_temp_c": round(float(zone_df["zone_temp_c"].mean()), 6),
}
pd.DataFrame([summary]).to_csv(f"results/twinb_summary_{run_id}.csv", index=False)
print("summary", f"results/twinb_summary_{run_id}.csv")
print("zone", f"results/twinb_zone_{run_id}.csv")
print("agent", f"results/twinb_agent_{run_id}.csv")
print(summary)
PY
```

### ขั้นที่ 13: สร้างตัวรวมผลลัพธ์

block นี้รวม summary หลาย scenario และคำนวณค่าเฉลี่ยราย policy

```bash
cat > src/merge_twinb_results.py <<'PY'
import argparse
import glob
from pathlib import Path

import pandas as pd

p = argparse.ArgumentParser()
p.add_argument("--pattern", default="results/twinb_summary_*.csv")
p.add_argument("--output", default="results/twinb_policy_compare.csv")
a = p.parse_args()

files = [Path(path) for path in sorted(glob.glob(a.pattern))]
if not files:
    raise SystemExit(f"missing files for pattern: {a.pattern}")

df = pd.concat([pd.read_csv(path) for path in files], ignore_index=True)
table = df.groupby("policy", as_index=False).agg(
    runs=("scenario_id", "count"),
    mean_energy_kwh=("total_energy_kwh", "mean"),
    mean_discomfort_c=("mean_discomfort_c", "mean"),
    mean_ac_request_rate=("ac_request_rate", "mean"),
    peak_zone_temp_c=("peak_zone_temp_c", "max"),
).sort_values("mean_discomfort_c")
table.to_csv(a.output, index=False)
print(table.to_string(index=False))
PY
```

### ขั้นที่ 14: สร้าง AI Scaffold

block นี้สร้าง prompt ให้ AI ช่วยตรวจ coupling, scenario และผลลัพธ์ โดยอ้างอิง code/log/CSV

```bash
cat > prompts/twinb-ai-scaffold-th.md <<'EOF'
# AI Scaffold สำหรับ Twin-B MicroCosim

Coupling reviewer: ตรวจว่า zone_temperature, occupancy, setpoint และ energy_kwh เชื่อมกันครบทุก timestep

Scenario coach: เสนอ policy เพิ่มโดยเปลี่ยน min_setpoint_c, max_setpoint_c หรือ cooling_gain ทีละปัจจัย

Result tutor: อ่าน twinb_policy_compare.csv แล้วอธิบาย trade-off ระหว่าง energy_kwh, discomfort_c และ ac_request_rate
EOF
```

### ขั้นที่ 15: ตรวจ Syntax และรัน Smoke บน Login Node

block นี้ compile source และรัน smoke ขนาดเล็กเพื่อจับ error ก่อนส่ง Slurm

```bash
python -m py_compile src/thermal_surrogate.py src/twinb_agents.py src/run_twinb_cosim.py src/merge_twinb_results.py
python src/run_twinb_cosim.py
ls -lh results/twinb_summary_manual_0_balanced_101.csv
```

## Example 1: Single Slurm Job

single job ใช้ตรวจว่า co-simulation, account, partition และ module ใช้งานพร้อมกัน

### ขั้นที่ 1: สร้าง Slurm Script

block นี้สร้าง job ที่รัน scenario เดียวด้วย resource ขนาดเล็ก

```bash
cat > jobs/twinb_single.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=twinb-single
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:06:00
#SBATCH --output=logs/twinb_single_%j.out
#SBATCH --error=logs/twinb_single_%j.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"

python src/run_twinb_cosim.py \
    --config configs/twinb_micro.yaml \
    --occupants configs/occupants.json
SLURM
```

### ขั้นที่ 2: ส่ง Single Job

block นี้ส่ง job และบันทึก job id เพื่ออ่าน log และ summary

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/twinb_single.sbatch)
echo "$job_id	twinb_single	$(date -Is)" >> notes/job-history.tsv
echo "Submitted single job: $job_id"
echo "Read: tail -80 logs/twinb_single_${job_id}.out"
```

## Example 2: Slurm Job Array

job array ใช้เปรียบเทียบ policy หลายแบบในเวลาอบรมสั้น แต่ละ task เปลี่ยน scenario และ seed

### ขั้นที่ 1: สร้าง Scenario Table

block นี้กำหนด 6 scenario เพื่อให้ LANTA กระจายเป็นงานย่อย

```bash
cat > configs/twinb_scenarios.csv <<'EOF'
scenario_id,policy,seed,outdoor_base_c
comfort_101,comfort,101,31.5
comfort_102,comfort,102,32.5
balanced_201,balanced,201,31.5
balanced_202,balanced,202,32.5
saving_301,energy_saving,301,31.5
saving_302,energy_saving,302,32.5
EOF
```

### ขั้นที่ 2: สร้าง Array Slurm Script

block นี้อ่านหนึ่งแถวจาก CSV ต่อหนึ่ง array task แล้วสร้าง config ย่อยของ scenario นั้น

```bash
cat > jobs/twinb_array.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=twinb-array
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:08:00
#SBATCH --array=1-6%2
#SBATCH --output=logs/twinb_array_%A_%a.out
#SBATCH --error=logs/twinb_array_%A_%a.err

set -euo pipefail
module purge
module use "${EPI_MODULE_ROOT:?set EPI_MODULE_ROOT before sbatch}"
module load hpc-mesa/2.3.4
cd "$SLURM_SUBMIT_DIR"

line_number=$((SLURM_ARRAY_TASK_ID + 1))
line=$(sed -n "${line_number}p" configs/twinb_scenarios.csv)
IFS=, read -r scenario_id policy seed outdoor_base_c <<< "$line"
run_config="configs/twinb_${scenario_id}.yaml"
python - "$scenario_id" "$policy" "$seed" "$outdoor_base_c" "$run_config" <<'PY'
import sys
from pathlib import Path
import yaml
scenario_id, policy, seed, outdoor_base_c, out = sys.argv[1:]
cfg = yaml.safe_load(Path("configs/twinb_micro.yaml").read_text())
cfg["simulation"]["scenario_id"] = scenario_id
cfg["simulation"]["policy"] = policy
cfg["simulation"]["seed"] = int(seed)
cfg["weather"]["base_c"] = float(outdoor_base_c)
Path(out).write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
PY
python src/run_twinb_cosim.py --config "$run_config" --occupants configs/occupants.json
SLURM
```

### ขั้นที่ 3: ส่ง Array Job

block นี้ส่ง array job และบันทึก job id

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,EPI_MODULE_ROOT="$EPI_MODULE_ROOT" --parsable jobs/twinb_array.sbatch)
echo "$job_id	twinb_array	$(date -Is)" >> notes/job-history.tsv
echo "Submitted array job: $job_id"
echo "Monitor: squeue -j $job_id"
```

### ขั้นที่ 4: รวมผล Array

block นี้รวมเฉพาะ summary ของ array job ปัจจุบัน และสร้าง policy comparison

```bash
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
python src/merge_twinb_results.py \
    --pattern "results/twinb_summary_${job_id}_*.csv" \
    --output "results/twinb_policy_compare_${job_id}.csv"
cat "results/twinb_policy_compare_${job_id}.csv"
```

## Check

### ขั้นที่ 1: ตรวจ Job Evidence

block นี้ดู queue, accounting และ log ของ job ที่เพิ่งส่ง

```bash
squeue -u "$USER"
sacct -j <jobid> --format=JobID,JobName,Partition,State,Elapsed,MaxRSS,ExitCode
tail -80 logs/twinb_array_<jobid>_1.out
```

### ขั้นที่ 2: ตรวจ Result Evidence

block นี้เปิดดูไฟล์ผลลัพธ์หลักของ co-simulation

```bash
find results -maxdepth 1 -type f -name 'twinb_*csv' | sort | tail -30
head -5 results/twinb_policy_compare_<jobid>.csv
head -5 results/twinb_zone_<jobid>_1_comfort_101.csv
```

## วิธีตัดสินว่าผลดีและถูกต้อง

ผลลัพธ์ที่ใช้สอนได้ควรมีหลักฐานครบห้าส่วน

1. Slurm state เป็น `COMPLETED` และ `ExitCode` เป็น `0:0`
2. `twinb_zone_*.csv` มีจำนวนแถวเท่ากับ `steps x zones`
3. `energy_kwh` เป็นค่าศูนย์หรือบวก และสูงขึ้นเมื่อ cooling ทำงานถี่
4. `setpoint_c` อยู่ในช่วง policy เช่น comfort, balanced หรือ energy_saving
5. `twinb_policy_compare_*.csv` แสดง trade-off ระหว่าง energy และ discomfort จากหลาย seed

## คำอธิบายเชิงวิชาการ

Twin-B MicroCosim เป็น co-simulation แบบ time-stepped coupling ระหว่าง model เชิงฟิสิกส์และ ABS โดย state variable หลักคืออุณหภูมิราย zone ส่วน control variable คือ cooling setpoint ที่ได้จากการรวม decision ของ occupant agents

scientific model ใช้สมการสมดุลความร้อนอันดับหนึ่งเพื่ออัปเดต `next_temp_c` จาก outdoor temperature, thermal inertia, internal heat gain จากจำนวนคน และ cooling rate จาก setpoint ส่วน ABS ใช้ Mesa สร้างประชากรที่มี preferred temperature และ comfort tolerance ต่างกัน Agent ประเมิน comfort จากอุณหภูมิที่ scientific model ส่งมา แล้วส่ง request กลับผ่าน `requested_setpoint_c`

การออกแบบนี้เหมาะกับ LANTA เพราะผู้ใช้เห็นความหมายของ HPC ผ่านการกระจาย scenario มากกว่าการรัน simulation เดี่ยว งานหนึ่งชิ้นมี config, source, scheduler evidence, output CSV และ summary table ครบวงจร จึงใช้สอน reproducibility, coupling contract, policy sensitivity และการตรวจผลแบบ evidence-based ได้ในเวลาสั้น

## ต่อกับ Twin-B เต็ม

เมื่อทีมมี EnergyPlus, `pyenergyplus`, IDF และ EPW พร้อมใช้งาน ให้แทน `ThermalSurrogate.advance()` ด้วย callback จาก EnergyPlus แล้วคง interface เดิมไว้ ได้แก่ `zone_temp_c`, `occupants`, `setpoint_c` และ `energy_kwh` วิธีนี้ช่วยให้ tutorial ขนาดเล็กขยายไปสู่ digital twin อาคารเต็มรูปแบบตามแนวทางของ Twin-B ได้โดยรักษาโครงสร้าง experiment เดิม
