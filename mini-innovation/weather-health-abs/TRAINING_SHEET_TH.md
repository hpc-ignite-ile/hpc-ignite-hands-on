# แผ่นงาน: HPDS Weather-Health ABS บน LANTA

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

หน้านี้เป็นแบบฝึกปฏิบัติที่จบได้ในหน้าเดียวสำหรับผู้เรียน 40 คน ผู้ใช้เริ่มจากเครื่องของตนเอง ย้ายหรือดึงข้อมูลเข้า LANTA จัดแฟ้มรวม อ่านหลักฐานของ Lustre สร้างสภาพแวดล้อม Dask เพิ่มเติม รันแบบจำลองอากาศ-อาคาร-ตัวแทนด้วย Slurm แล้วสรุปผลเป็นชุดหลักฐาน

## บทนำแบบ Verse

ย้ายข้อมูลให้มีหลักฐาน ก่อนเปิดแบบจำลอง<br>
นับไฟล์ นับแถว นับไบต์ แล้วค่อยถามเรื่องความเร็ว<br>
ให้ก้อนข้อมูลสัมพันธ์กับหน่วยความจำ worker และคำถามวิเคราะห์<br>
ให้อากาศเป็นแรงขับ ให้อาคารเป็นตัวกรอง ให้ตัวแทนเป็นผู้รับผลกระทบ<br>
เมื่อผลออกมา ให้ดูทั้งนโยบาย การสัมผัสความร้อน การทำความเย็น ความเสี่ยง และเวลาที่ใช้<br>
AI ช่วยอ่านหลักฐานได้ดี เมื่อหลักฐานครบและขอบเขตคำถามชัดเจน

## สิ่งที่ผู้ใช้จะฝึก

- `rsync` ผ่าน SSH สำหรับย้ายโฟลเดอร์จากเครื่องผู้ใช้ไปยัง LANTA
- `curl`, `wget` และรูปแบบคำสั่ง `lftp` สำหรับดึงข้อมูล HTTP/FTP
- `zip`, `unzip`, `tar`, `gzip`, `pigz` สำหรับจัดแฟ้มรวมและลดปัญหาไฟล์ย่อยจำนวนมาก
- `df`, `lfs getstripe`, `du`, `find`, `sha256sum` สำหรับเก็บหลักฐานของระบบแฟ้มขนาน
- Dask `LocalCluster` ภายในการจัดสรรทรัพยากรหนึ่งโหนดของ Slurm
- ตัวแปรที่คำนวณจากข้อมูลอากาศ แบบจำลองอาคารขนาดย่อ และแบบจำลองตัวแทนด้านการเดินทางกับการสัมผัสความร้อน
- ชุดหลักฐานแบบงานประชุม SC สำหรับรันซ้ำ ตรวจทาน และอภิปรายผล

## Copy-Paste จากเครื่องผู้ใช้

### ขั้นที่ 1: เข้าสู่ LANTA

คำสั่งนี้เปิดเชลล์บนเครื่องเข้าใช้งานของ LANTA

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

### ขั้นที่ 2: ทดลอง `rsync --dry-run` จากเครื่องผู้ใช้

คำสั่งชุดนี้สร้างโฟลเดอร์ตัวอย่างบนเครื่องผู้ใช้ แล้วซ้อมคำสั่งย้ายข้อมูลผ่าน SSH ก่อนส่งไฟล์จริง

```bash
mkdir -p hpds-transfer-demo/raw
printf "city,temp_c\nBangkok,32.1\nChiangMai,29.4\n" > hpds-transfer-demo/raw/weather_sample.csv
rsync -avP --dry-run hpds-transfer-demo/ <lanta-username>@lanta.nstda.or.th:~/incoming-hpds-transfer-demo/
```

### ขั้นที่ 3: ส่งโฟลเดอร์ตัวอย่างด้วย `rsync`

คำสั่งนี้ส่งไฟล์จริงและใช้ `--partial` เพื่อเก็บไฟล์ที่ส่งค้างไว้เมื่อเครือข่ายหลุดกลางทาง

```bash
rsync -avP --partial hpds-transfer-demo/ <lanta-username>@lanta.nstda.or.th:~/incoming-hpds-transfer-demo/
```

## Copy-Paste บน LANTA

### ขั้นที่ 1: เตรียมพื้นที่ทำงานและตัวแปร

คำสั่งชุดนี้สร้างพื้นที่ทำงานสำหรับงาน HPDS และตั้งค่าบัญชีโครงการกับพาร์ทิชัน

```bash
export HPDS_WORKSPACE="${HPDS_WORKSPACE:-$HOME/lanta-hpds-weather}"
mkdir -p "$HPDS_WORKSPACE"
cd "$HPDS_WORKSPACE"
mkdir -p data/http data/staged data/small_files archives src jobs logs notes results figures plots envs

if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export HPDS_ENV_PREFIX="${HPDS_ENV_PREFIX:-$PWD/envs/hpds-dask}"
pwd
```

### ขั้นที่ 2: สร้างสภาพแวดล้อม Dask เพิ่มเติม

คำสั่งชุดนี้โหลด `hpc-mesa` เป็นฐาน แล้วสร้าง `venv` เฉพาะพื้นที่ทำงานเพื่อเพิ่ม Dask โดยแยกจากสภาพแวดล้อมกลาง

```bash
module purge
module use /project/tn999996-north/modules 2>/dev/null || true
module load hpc-mesa/2.3.4

if [ ! -x "$HPDS_ENV_PREFIX/bin/python" ]; then
    python -m venv --system-site-packages "$HPDS_ENV_PREFIX"
fi
. "$HPDS_ENV_PREFIX/bin/activate"
python -m pip install --no-cache-dir "dask==2024.8.0" "distributed==2024.8.0"
python - <<'PY'
import dask, distributed, pandas, numpy
print("dask", dask.__version__)
print("distributed", distributed.__version__)
print("pandas", pandas.__version__)
print("numpy", numpy.__version__)
PY
```

### ขั้นที่ 3: ตรวจเครื่องมือ transfer และ filesystem

คำสั่งชุดนี้บันทึกเครื่องมือที่ใช้ย้ายข้อมูล และเก็บหลักฐานว่าพื้นที่ทำงานอยู่บน Lustre

```bash
{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "host=$(hostname)"
    for tool in rsync zip unzip tar gzip pigz curl wget lftp sha256sum lfs; do
        if command -v "$tool" >/dev/null 2>&1; then
            echo "$tool=$(command -v "$tool")"
        else
            echo "$tool=missing"
        fi
    done
    df -Th "$PWD" "$HOME" /lustrefs 2>/dev/null || true
    lfs getstripe "$PWD" 2>/dev/null || true
} > notes/filesystem_evidence.txt
sed -n '1,40p' notes/filesystem_evidence.txt
```

### ขั้นที่ 4: ดาวน์โหลดข้อมูลอากาศจริงด้วย `curl`

คำสั่งชุดนี้ดึง CSV รายชั่วโมงจาก NASA POWER สำหรับกรุงเทพฯ 2 วัน แล้วบันทึก checksum

```bash
POWER_URL="https://power.larc.nasa.gov/api/temporal/hourly/point?parameters=T2M,RH2M,ALLSKY_SFC_SW_DWN,WS10M&community=SB&longitude=100.5018&latitude=13.7563&start=20260101&end=20260102&format=CSV&header=false&time-standard=UTC"
curl -L --fail -C - --connect-timeout 20 --max-time 120 \
    -o data/http/nasa_power_bangkok.csv "$POWER_URL"
sha256sum data/http/nasa_power_bangkok.csv > notes/nasa_power_bangkok.sha256
wc -l data/http/nasa_power_bangkok.csv
sed -n '1,5p' data/http/nasa_power_bangkok.csv
```

### ขั้นที่ 5: บันทึก pattern สำหรับ `wget` และ `lftp`

คำสั่งชุดนี้เก็บตัวอย่างคำสั่งสำหรับแหล่งข้อมูลขนาดใหญ่ไว้ใน `notes` ผู้ใช้สามารถปรับกับปลายทาง FTP/HTTP จริงของตนเอง

```bash
cat > notes/transfer_patterns.txt <<'TXT'
# HTTP resumable download
wget -c -O data/http/file.csv "https://example.org/path/file.csv"
curl -L -C - -o data/http/file.csv "https://example.org/path/file.csv"

# FTP/HTTP directory mirror with lftp
lftp -c 'open https://example.org/data; mirror --continue --parallel=4 remote_dir data/raw'

# SSH-enabled rsync from local machine to LANTA
rsync -avP --partial local_data/ <user>@lanta.nstda.or.th:~/project_data/
TXT
sed -n '1,20p' notes/transfer_patterns.txt
```

### ขั้นที่ 6: สร้างตารางพื้นที่และสถานการณ์ทดลอง

คำสั่งชุดนี้สร้างตารางข้อมูลเข้าแบบสั้นที่แบบจำลองวิทยาศาสตร์และ ABS ใช้ร่วมกัน

```bash
cat > data/locations.csv <<'CSV'
location_id,district,lat,lon
0,BangkokCore,13.7563,100.5018
1,Thonburi,13.7200,100.4700
2,PathumWan,13.7460,100.5340
3,Nonthaburi,13.8620,100.5140
CSV

cat > data/scenarios.csv <<'CSV'
scenario_id,policy,agents,seed,outdoor_reduction,crowding_factor,cooling_setpoint_c,thermal_tau_h,solar_gain,cooling_power,initial_indoor_c
101,baseline,240,20260807,0.00,0.05,27.5,6.0,0.70,0.55,29.0
102,cooling_center,240,20260807,0.15,0.08,26.0,5.5,0.58,0.70,28.0
103,outdoor_shift,240,20260807,0.35,0.03,28.5,6.5,0.65,0.45,29.5
CSV
```

### ขั้นที่ 7: สร้างสคริปต์พักข้อมูลอากาศ

คำสั่งชุดนี้สร้างสคริปต์ที่แปลง NASA POWER CSV หนึ่งไฟล์เป็นชุดข้อมูลอากาศหลายพื้นที่พร้อม manifest

```bash
cat > src/stage_weather_data.py <<'PY'
from pathlib import Path
import csv, hashlib, math
import pandas as pd

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

weather=pd.read_csv("data/http/nasa_power_bangkok.csv")
weather["timestamp"]=pd.to_datetime({
    "year":weather["YEAR"],"month":weather["MO"],
    "day":weather["DY"],"hour":weather["HR"]}, utc=True)
weather=weather.rename(columns={"T2M":"temp_c","RH2M":"rh_pct",
    "ALLSKY_SFC_SW_DWN":"solar_w_m2","WS10M":"wind_m_s"})
locations=list(csv.DictReader(open("data/locations.csv",encoding="utf-8")))
Path("data/staged").mkdir(parents=True,exist_ok=True)
manifest=[]
for idx,loc in enumerate(locations):
    df=weather[["timestamp","temp_c","rh_pct","solar_w_m2","wind_m_s"]].copy()
    lat=float(loc["lat"]); lon=float(loc["lon"])
    shift=(lat-13.75)*0.18+(lon-100.5)*0.04
    angle=df["timestamp"].dt.hour*math.pi/12.0
    df["temp_c"]=df["temp_c"]+shift+0.6*angle.map(math.sin)
    df["rh_pct"]=(df["rh_pct"]-1.5*idx).clip(35,95)
    df["solar_w_m2"]=(df["solar_w_m2"]*(1-0.03*idx)).clip(lower=0)
    df["location_id"]=loc["location_id"]; df["district"]=loc["district"]
    cols=["timestamp","location_id","district","temp_c","rh_pct","solar_w_m2","wind_m_s"]
    out=Path(f"data/staged/weather_{loc['location_id']}.csv")
    df[cols].to_csv(out,index=False)
    manifest.append([str(out),loc["location_id"],loc["district"],len(df),out.stat().st_size,sha256(out)])
with open("data/weather_manifest.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["path","location_id","district","rows","bytes","sha256"]); w.writerows(manifest)
print("staged_files",len(manifest))
PY
```

### ขั้นที่ 8: รัน staging และตรวจ manifest

คำสั่งชุดนี้สร้างชุดข้อมูลพักไว้ แล้วตรวจจำนวนไฟล์ จำนวนแถว และ checksum

```bash
python src/stage_weather_data.py
sed -n '1,10p' data/weather_manifest.csv
find data/staged -type f -name 'weather_*.csv' -print
```

### ขั้นที่ 9: ทดลอง many-small-files และ archive

คำสั่งชุดนี้สร้างไฟล์เล็กจำนวนมาก แล้วเปรียบเทียบการรวมแฟ้มด้วย `zip` และ `tar` + `pigz`

```bash
python - <<'PY'
from pathlib import Path
base=Path("data/small_files")
base.mkdir(parents=True,exist_ok=True)
for i in range(120):
    (base/f"sensor_{i:03d}.csv").write_text("hour,value\n0,1.0\n1,2.0\n",encoding="utf-8")
PY
find data/small_files -type f | wc -l
/usr/bin/time -v zip -qr archives/small_files.zip data/small_files 2> notes/time_zip.txt
unzip -t archives/small_files.zip > notes/unzip_test.txt
/usr/bin/time -v tar -I pigz -cf archives/small_files.tar.gz data/small_files 2> notes/time_tar_pigz.txt
du -sh data/small_files archives/small_files.zip archives/small_files.tar.gz
```

### ขั้นที่ 10: สร้างโค้ดกระบวนการ Dask ส่วนที่ 1

คำสั่งชุดนี้สร้างส่วน import ฟังก์ชันช่วย และสูตรดัชนีความร้อน

```bash
cat > src/hpds_weather_abs.py <<'PY'
from pathlib import Path
import argparse, csv, glob, time
import numpy as np
import pandas as pd
from dask import delayed
from dask.distributed import Client, LocalCluster

def read_rows(path):
    with open(path,encoding="utf-8") as f:
        return list(csv.DictReader(f))

def heat_index_c(temp_c,rh_pct):
    tf=temp_c*9/5+32; rh=rh_pct
    hi=-42.379+2.04901523*tf+10.14333127*rh-0.22475541*tf*rh
    hi+=-0.00683783*tf*tf-0.05481717*rh*rh
    hi+=0.00122874*tf*tf*rh+0.00085282*tf*rh*rh
    hi+=-0.00000199*tf*tf*rh*rh
    return (hi-32)*5/9
PY
```

### ขั้นที่ 11: เติมโค้ดกระบวนการ Dask ส่วนที่ 2

คำสั่งชุดนี้เติมแบบจำลองอาคารขนาดย่อและการจำลอง ABS

```bash
cat >> src/hpds_weather_abs.py <<'PY'
def building_response(weather,sc):
    indoor=float(sc["initial_indoor_c"]); peak=indoor; cooling_kwh=0; hot_hours=0
    setpoint=float(sc["cooling_setpoint_c"]); tau=float(sc["thermal_tau_h"])
    gain=float(sc["solar_gain"]); power=float(sc["cooling_power"])
    for row in weather.itertuples(index=False):
        cooling=max(0,indoor-setpoint)*power
        indoor += (row.temp_c-indoor)/tau + gain*row.solar_w_m2/1000 - 0.25*cooling
        peak=max(peak,indoor); cooling_kwh+=cooling; hot_hours+=max(0,indoor-30)
    return peak,cooling_kwh,hot_hours

def simulate(weather_path,loc,sc):
    t0=time.perf_counter()
    weather=pd.read_csv(weather_path,parse_dates=["timestamp"])
    temp=weather["temp_c"].to_numpy(float); rh=weather["rh_pct"].to_numpy(float)
    hi=heat_index_c(temp,rh)
    peak,cooling,hot_hours=building_response(weather,sc)
    rng=np.random.default_rng(int(sc["seed"])+int(loc["location_id"]))
    n=int(sc["agents"]); vuln=rng.beta(2,7,size=n); pref=rng.uniform(0.15,0.85,size=n)
    exposure=0.0; contact=0.0; risk=0.0; strength=float(sc["outdoor_reduction"])
    for value in hi:
        pressure=max(0,value-32)/10
        outside=rng.random(n)<np.clip(pref-strength*pressure,0.02,0.95)
        exp=np.where(outside,max(0,value-30),max(0,peak-30))
        mult=1+0.12*pressure+float(sc["crowding_factor"])*(~outside)
        exposure+=float(exp.sum()); contact+=float(mult.sum())
        risk+=float((mult*(1+vuln*exp/20)).sum())
    return {"location_id":loc["location_id"],"district":loc["district"],"scenario_id":sc["scenario_id"],
        "policy":sc["policy"],"rows":len(weather),"agents":n,"mean_temp_c":f"{temp.mean():.4f}",
        "max_heat_index_c":f"{hi.max():.4f}","peak_indoor_c":f"{peak:.4f}",
        "cooling_kwh":f"{cooling:.4f}","indoor_hot_hours":f"{hot_hours:.4f}",
        "exposure_agent_hours":f"{exposure:.4f}","contact_hours":f"{contact:.4f}",
        "infection_risk_proxy":f"{risk/max(n,1):.4f}","elapsed_sec":f"{time.perf_counter()-t0:.6f}"}
PY
```

### ขั้นที่ 12: เติมโค้ดกระบวนการ Dask ส่วนที่ 3

คำสั่งชุดนี้เติมส่วนหลักของโปรแกรม สร้างงานย่อยของ Dask และเขียน CSV

```bash
cat >> src/hpds_weather_abs.py <<'PY'
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--out",default="results/hpds_weather_abs_summary.csv")
    args=p.parse_args()
    locations={r["location_id"]:r for r in read_rows("data/locations.csv")}
    scenarios=read_rows("data/scenarios.csv")
    files=sorted(glob.glob("data/staged/weather_*.csv"))
    if len(files)==0:
        raise SystemExit("no staged weather files")
    tasks=[]
    for path in files:
        loc_id=Path(path).stem.split("_")[-1]
        for sc in scenarios:
            tasks.append(delayed(simulate)(path,locations[loc_id],sc))
    cluster=LocalCluster(n_workers=args.workers,threads_per_worker=1,dashboard_address=None)
    with Client(cluster) as client:
        rows=list(client.gather(client.compute(tasks)))
    Path("results").mkdir(exist_ok=True)
    with open(args.out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("tasks",len(tasks)); print("workers",args.workers); print("wrote",args.out)

if __name__=="__main__":
    main()
PY
```

### ขั้นที่ 13: สร้างสคริปต์วาดรูป

คำสั่งชุดนี้สร้างรูปสรุปเชิงนโยบายด้วย Matplotlib ในงานแบบแบตช์

```bash
cat > src/plot_hpds_summary.py <<'PY'
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import pandas as pd
from matplotlib import pyplot as plt

df=pd.read_csv("results/hpds_weather_abs_summary.csv")
g=df.groupby("policy",as_index=False).agg(
    max_heat_index_c=("max_heat_index_c","mean"),
    exposure_agent_hours=("exposure_agent_hours","mean"),
    cooling_kwh=("cooling_kwh","mean"),
    infection_risk_proxy=("infection_risk_proxy","mean")).sort_values("policy")
g.to_csv("results/hpds_policy_summary.csv",index=False)
Path("figures").mkdir(exist_ok=True)
fig,axes=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
panels=[("max_heat_index_c","Mean max heat index C","#2563eb"),
        ("exposure_agent_hours","Exposure agent-hours","#dc2626"),
        ("cooling_kwh","Cooling proxy kWh","#0f766e"),
        ("infection_risk_proxy","Risk proxy","#7c3aed")]
for ax,(col,title,color) in zip(axes.ravel(),panels):
    ax.bar(g["policy"],g[col],color=color)
    ax.set_title(title); ax.tick_params(axis="x",labelrotation=25); ax.grid(axis="y",alpha=0.25)
fig.suptitle("Weather-Health ABS HPDS Summary")
fig.savefig("figures/hpds_weather_abs_summary.png",dpi=160)
print("wrote figures/hpds_weather_abs_summary.png")
PY
```

### ขั้นที่ 14: สร้างแบบฝึกย่อยเรื่องการแบ่งกราฟ

คำสั่งชุดนี้เปรียบเทียบการแบ่งกราฟแบบง่าย เพื่ออธิบายแนวคิด METIS/ParMETIS เรื่องสมดุลภาระงานและน้ำหนักขอบที่ถูกตัด

```bash
cat > src/partition_mobility_graph.py <<'PY'
from pathlib import Path
import csv
nodes={"campus":4200,"market":2600,"clinic":1100,"transit":3600,"residential":5200,"industrial":3100}
edges=[("campus","market",80),("campus","clinic",30),("campus","transit",120),
       ("market","transit",90),("market","residential",70),("clinic","residential",45),
       ("transit","industrial",110),("industrial","residential",60)]
def score(parts):
    loads=[0,0]; cuts=0
    for node,weight in nodes.items():
        loads[parts[node]]+=weight
    for left,right,weight in edges:
        if parts[left] != parts[right]:
            cuts+=weight
    return loads[0],loads[1],max(loads)/max(1,min(loads)),cuts
cases=[
    ("naive_round_robin",{node:i%2 for i,node in enumerate(nodes)}),
    ("locality_partition",{"campus":0,"market":0,"clinic":0,"transit":1,"residential":1,"industrial":1}),
]
Path("results").mkdir(exist_ok=True)
with open("results/mobility_partition_summary.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["partitioner","load_part_0","load_part_1","imbalance","edge_cut_weight"])
    for name,parts in cases:
        w.writerow([name,*score(parts)])
print("wrote results/mobility_partition_summary.csv")
PY
```

### ขั้นที่ 15: ตรวจ ParMETIS และ SCOTCH บน LANTA

คำสั่งชุดนี้ตรวจว่าเครื่องมือแบ่งกราฟระดับ HPC มีโมดูลให้เรียกใช้ในระบบ

```bash
{
    module avail 2>&1 | grep -Ei 'ParMETIS|SCOTCH' || true
    module purge
    module load ParMETIS/4.0.3-cpeCray-23.03 2>/dev/null || true
    module list 2>&1
    command -v parmetis || true
} > notes/partitioning_modules.txt
sed -n '1,80p' notes/partitioning_modules.txt
```

### ขั้นที่ 16: สร้างไฟล์ Slurm สำหรับกระบวนการ Dask

คำสั่งชุดนี้สร้างงานที่ใช้ CPU 4 แกนในทรัพยากรชุดเดียว แล้วให้ Dask สร้าง worker ตามค่า `SLURM_CPUS_PER_TASK`

```bash
cat > jobs/hpds_weather_abs.sbatch <<'SLURM'
#!/bin/bash
#SBATCH --job-name=hpds-weather
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=4G
#SBATCH --time=00:08:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs notes results figures
module purge
module use /project/tn999996-north/modules 2>/dev/null || true
module load hpc-mesa/2.3.4
. "${HPDS_ENV_PREFIX:?set HPDS_ENV_PREFIX before sbatch}/bin/activate"
{
    echo "job_id=$SLURM_JOB_ID"
    echo "host=$(hostname)"
    echo "workspace=$(pwd)"
    echo "python=$(command -v python)"
    python - <<'PY'
import dask, distributed, pandas, numpy
print("dask="+dask.__version__)
print("distributed="+distributed.__version__)
print("pandas="+pandas.__version__)
print("numpy="+numpy.__version__)
PY
} > "notes/environment_${SLURM_JOB_ID}.txt"
/usr/bin/time -v python src/hpds_weather_abs.py --workers "$SLURM_CPUS_PER_TASK" \
    --out results/hpds_weather_abs_summary.csv 2> "notes/time_hpds_weather_abs_${SLURM_JOB_ID}.txt"
python src/plot_hpds_summary.py
python src/partition_mobility_graph.py
sacct -j "$SLURM_JOB_ID" --format=JobID,JobName,Partition,State,Elapsed,AllocCPUS,MaxRSS,ExitCode \
    > "notes/sacct_${SLURM_JOB_ID}.txt"
SLURM
```

### ขั้นที่ 17: ส่งงานเข้า Slurm

คำสั่งชุดนี้ส่งงานเข้า Slurm และบันทึกหมายเลขงาน

```bash
job_id=$(sbatch -A "$LANTA_ACCOUNT" -p "$LANTA_CPU_PARTITION" --export=ALL,HPDS_ENV_PREFIX="$HPDS_ENV_PREFIX" --parsable jobs/hpds_weather_abs.sbatch)
echo "hpds_weather_job=$job_id" | tee -a notes/filesystem_evidence.txt
squeue -j "$job_id"
```

### ขั้นที่ 18: อ่านผลหลังงานจบ

คำสั่งชุดนี้อ่านหลักฐานจาก Slurm เวลาที่ใช้ CSV สรุป และรูปที่สร้างจากผลจริง

```bash
sacct -j "$job_id" --format=JobID,JobName,State,Elapsed,AllocCPUS,MaxRSS,ExitCode
sed -n '1,80p' "logs/hpds-weather_${job_id}.out"
sed -n '1,30p' "notes/time_hpds_weather_abs_${job_id}.txt"
sed -n '1,12p' results/hpds_weather_abs_summary.csv
sed -n '1,10p' results/hpds_policy_summary.csv
ls -lh figures/hpds_weather_abs_summary.png
```

### ขั้นที่ 19: สร้าง prompt สำหรับให้ AI อ่านหลักฐาน

คำสั่งชุดนี้รวมหลักฐานให้ AI ช่วยจัดกลุ่มคอขวด และเสนอการรันครั้งถัดไปโดยอ้างอิงเฉพาะไฟล์ในพื้นที่ทำงาน

```bash
{
    echo "# AI HPDS Evidence Review Prompt"
    echo
    echo "Use only the evidence below. Classify data-transfer, archive, Dask, filesystem, model, and Slurm bottlenecks."
    echo "Propose one next run and one correctness check."
    echo
    echo "## Filesystem Evidence"
    sed -n '1,80p' notes/filesystem_evidence.txt
    echo
    echo "## Weather Manifest"
    sed -n '1,12p' data/weather_manifest.csv
    echo
    echo "## Slurm Environment"
    sed -n '1,80p' "notes/environment_${job_id}.txt"
    echo
    echo "## Results"
    sed -n '1,20p' results/hpds_policy_summary.csv
    sed -n '1,20p' results/mobility_partition_summary.csv
} > notes/ai_hpds_review_prompt.md
sed -n '1,120p' notes/ai_hpds_review_prompt.md
```

## วิธีอภิปรายผลในห้อง

1. `filesystem_evidence.txt` บอกว่าพื้นที่ทำงานอยู่บนระบบแฟ้มชนิดใด และมีเครื่องมือย้ายข้อมูล/จัดแฟ้มรวมครบเพียงใด
2. `weather_manifest.csv` บอก path จำนวนแถว จำนวนไบต์ และ checksum ของข้อมูลที่พักไว้แล้ว
3. `time_zip.txt` และ `time_tar_pigz.txt` ชี้ให้เห็นต้นทุนของการจัดแฟ้มรวมเมื่อมีไฟล์เล็กจำนวนมาก
4. `environment_<jobid>.txt` บอกว่างานใช้ Python/Dask รุ่นใด
5. `hpds_weather_abs_summary.csv` แสดงผลรายพื้นที่และนโยบาย
6. `hpds_policy_summary.csv` ใช้ตอบการแลกเปลี่ยนระหว่างการสัมผัสความร้อน การทำความเย็น และตัวแทนความเสี่ยง
7. `mobility_partition_summary.csv` ใช้อธิบายว่าการตัดกราฟมีผลต่อต้นทุนการสื่อสารอย่างไร

## เกณฑ์ตัดสินว่าผลดีและถูกต้อง

- checksum ของข้อมูล HTTP มีอยู่ใน `notes/nasa_power_bangkok.sha256`
- ไฟล์ข้อมูลอากาศที่พักไว้มีจำนวนเท่ากับจำนวนพื้นที่
- งาน Slurm จบด้วย `COMPLETED` และ `ExitCode=0:0`
- Dask stdout มีจำนวน `tasks` เท่ากับ `locations x scenarios`
- `max_heat_index_c`, `peak_indoor_c`, `cooling_kwh`, `exposure_agent_hours` เป็นค่าจำนวนจริง
- นโยบายที่เพิ่มการทำความเย็นลดภาระความร้อนในอาคาร พร้อมแลกด้วยค่าตัวแทนพลังงานทำความเย็นที่สูงขึ้น
- การแบ่งกราฟที่ลดน้ำหนักขอบที่ถูกตัดมีเหตุผลด้านการสื่อสาร และต้องตรวจสมดุลภาระงานร่วมกัน
