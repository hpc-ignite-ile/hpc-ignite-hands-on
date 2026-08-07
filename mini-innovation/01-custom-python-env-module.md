# 01 สร้างสภาพแวดล้อม Python และโมดูลสำหรับกลุ่ม

หน้านี้ใช้เตรียมสภาพแวดล้อม Python กลางสำหรับนวัตกรรมย่อยแบบโรคระบาดด้วย ABS บน LANTA โดยติดตั้ง Mesa, ชุดวิทยาศาสตร์ของ Python, ipykernel และ JupyterLab ลงในพื้นที่โครงการ แล้วสร้างโมดูล Lmod ให้ผู้ใช้โหลดซ้ำได้ทั้งบนเครื่องเข้าใช้งาน เครื่องคำนวณ และงาน Slurm

บทเรียนนี้แยกบทบาทเป็นสองส่วน `hpc-mesa` คือเคอร์เนล Python ที่มี Mesa และชุดโปรแกรมวิทยาศาสตร์ตามรุ่นของกิจกรรม ส่วน JupyterLab คือเซิร์ฟเวอร์ที่เปิดหน้าเว็บ ถ้า LANTA มี JupyterLab กลางในรอบอบรม ผู้ใช้สามารถใช้เซิร์ฟเวอร์กลางเป็นทางสำรอง และยังเลือกเคอร์เนล `Python (hpc-mesa)` เพื่อให้โค้ดจำลองใช้ชุดโปรแกรมเดียวกัน

สำหรับการเริ่มจากเครื่องผู้ใช้ ให้ดู [00-connect-to-lanta.md](00-connect-to-lanta.md) ก่อน หน้านี้ใช้เครื่องสำหรับถ่ายโอนข้อมูลเพราะมีการดาวน์โหลดชุดโปรแกรม

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `mamba create`, `conda run`, `python -m pip`, heredoc, Lua modulefile, `chmod`, `module use` และ `module load`

## Copy-Paste จากเครื่องผู้ใช้

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เข้าสู่เครื่องสำหรับถ่ายโอนข้อมูล

คำสั่งชุดนี้เปิดเชลล์บนเครื่องสำหรับถ่ายโอนข้อมูล ซึ่งเหมาะกับการสร้างสภาพแวดล้อมและดาวน์โหลดชุดโปรแกรม

```bash
ssh <lanta-username>@transfer.lanta.nstda.or.th
```

## Copy-Paste บน Transfer Host

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียมพื้นที่ทำงาน

คำสั่งชุดนี้สร้างพื้นที่ทำงาน และรับเส้นทางพื้นที่โครงการที่จะใช้เก็บสภาพแวดล้อม โมดูล และแคชของการติดตั้ง

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p logs notes

if [ -z "${LANTA_PROJECT:-}" ]; then
    read -rp "Project directory เช่น /project/ltXXXXXX-name หรือ /project/tn999996-north: " LANTA_PROJECT
    export LANTA_PROJECT
fi
```

### ขั้นที่ 2: ตั้งเส้นทางของสภาพแวดล้อม

คำสั่งชุดนี้กำหนดเส้นทางแบบใช้ซ้ำ เพื่อให้สมาชิกกลุ่มโหลดโมดูลเดียวกันและใช้แคชในพื้นที่โครงการร่วมกัน

```bash
export EPI_ENV_NAME="${EPI_ENV_NAME:-hpc-mesa}"
export EPI_ENV_PREFIX="${EPI_ENV_PREFIX:-$LANTA_PROJECT/envs/$EPI_ENV_NAME}"
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-$LANTA_PROJECT/modules}"
export EPI_MODULE_VERSION="${EPI_MODULE_VERSION:-2.3.4}"
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$LANTA_PROJECT/conda-pkgs}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$LANTA_PROJECT/pip-cache}"
```

### ขั้นที่ 3: สร้างโฟลเดอร์กลาง

คำสั่งชุดนี้สร้างไดเรกทอรีสำหรับเก็บสภาพแวดล้อม conda ไฟล์โมดูล และแคช

```bash
mkdir -p "$LANTA_PROJECT/envs"
mkdir -p "$EPI_MODULE_ROOT/hpc-mesa"
mkdir -p "$CONDA_PKGS_DIRS"
mkdir -p "$PIP_CACHE_DIR"
```

### ขั้นที่ 4: โหลด Mamba

คำสั่งชุดนี้โหลดตัวจัดการแพ็กเกจที่ใช้สร้างสภาพแวดล้อมบนเครื่องสำหรับถ่ายโอนข้อมูล

```bash
module purge
module load Mamba/23.11.0-0
mamba --version
```

### ขั้นที่ 5: สร้างสภาพแวดล้อมเมื่อเส้นทางยังว่าง

คำสั่งชุดนี้สร้างสภาพแวดล้อมด้วย Python 3.10 และชุดโปรแกรมวิทยาศาสตร์หลัก เมื่อเส้นทางมีสภาพแวดล้อมเดิมอยู่ คำสั่งจะแสดงเส้นทางเดิมเพื่อให้ตรวจต่อ

```bash
if [ ! -x "$EPI_ENV_PREFIX/bin/python" ]; then
    mamba create -y -p "$EPI_ENV_PREFIX" \
        --override-channels -c conda-forge \
        python=3.10 pip numpy pandas scipy matplotlib pyyaml networkx tqdm
else
    echo "Environment exists: $EPI_ENV_PREFIX"
fi
```

### ขั้นที่ 6: เติมแพ็กเกจสำหรับเคอร์เนลและเซิร์ฟเวอร์สำรอง

คำสั่งชุดนี้ติดตั้งหรือปรับให้มีแพ็กเกจที่นวัตกรรมย่อยใช้จริง แม้สภาพแวดล้อมจะถูกสร้างไว้ก่อนหน้าแล้ว ขั้นนี้ทำให้ `hpc-mesa` เป็นเคอร์เนลที่ครบถ้วน และเป็นเซิร์ฟเวอร์ JupyterLab สำรองเมื่อรอบใช้งานนั้นยังขาด JupyterLab กลาง

```bash
conda run -p "$EPI_ENV_PREFIX" python -m pip install --no-cache-dir \
    "mesa==$EPI_MODULE_VERSION" \
    "jupyterlab>=4,<5" \
    "notebook>=7,<8" \
    ipykernel
```

### ขั้นที่ 7: สร้าง Modulefile

คำสั่งชุดนี้สร้างไฟล์โมดูล Lua ชื่อ `hpc-mesa/2.3.4` เพื่อให้ผู้ใช้เรียกสภาพแวดล้อมด้วย `module load`

```bash
cat > "$EPI_MODULE_ROOT/hpc-mesa/$EPI_MODULE_VERSION.lua" <<'LUA'
help([[
hpc-mesa: Python environment for LANTA EpiSprint.
It provides Mesa, NumPy, pandas, SciPy, Matplotlib, NetworkX, PyYAML, and JupyterLab.
]])

whatis("Python/Mesa/JupyterLab environment for LANTA EpiSprint mini innovation")

local prefix = "__EPI_ENV_PREFIX__"
prepend_path("PATH", pathJoin(prefix, "bin"))
setenv("HPC_MESA_ENV", prefix)
setenv("PYTHONNOUSERSITE", "1")
LUA
```

### ขั้นที่ 8: ใส่เส้นทางจริงลง Modulefile

คำสั่งชุดนี้แทนค่า placeholder ในไฟล์โมดูลด้วยเส้นทางของสภาพแวดล้อมในพื้นที่โครงการ

```bash
python - "$EPI_MODULE_ROOT/hpc-mesa/$EPI_MODULE_VERSION.lua" "$EPI_ENV_PREFIX" <<'PY'
from pathlib import Path
import sys

modulefile = Path(sys.argv[1])
prefix = sys.argv[2]
text = modulefile.read_text(encoding="utf-8").replace("__EPI_ENV_PREFIX__", prefix)
modulefile.write_text(text, encoding="utf-8")
PY
```

### ขั้นที่ 9: ปรับสิทธิ์สำหรับกลุ่ม

คำสั่งชุดนี้ให้สมาชิกกลุ่มอ่านและใช้สภาพแวดล้อมกับไฟล์โมดูลได้ และตั้ง setgid bit ให้โฟลเดอร์ใหม่สืบทอดกลุ่มเดิม

```bash
chmod -R g+rwX "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT" "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR" 2>/dev/null || true
find "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT" -type d -exec chmod g+s {} \; 2>/dev/null || true
```

### ขั้นที่ 10: โหลด Module และตรวจ Package

คำสั่งชุดนี้ตรวจว่า `python` และ `jupyter` มาจากสภาพแวดล้อมกลาง และแพ็กเกจสำคัญนำเข้าได้ครบ

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load "hpc-mesa/$EPI_MODULE_VERSION"
which python
which jupyter
jupyter lab --version
```

### ขั้นที่ 11: ตรวจรุ่นของชุดโปรแกรมวิทยาศาสตร์

คำสั่งชุดนี้บันทึกรุ่นของแพ็กเกจหลักและ API ของ Mesa ที่บทเรียนใช้

```bash
python - <<'PY'
import sys
import mesa
import numpy
import pandas
import scipy
import matplotlib
import yaml
import networkx
from mesa.time import RandomActivation
from mesa.space import MultiGrid

print("python", sys.version.split()[0])
print("mesa", mesa.__version__)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scipy", scipy.__version__)
print("matplotlib", matplotlib.__version__)
print("pyyaml", yaml.__version__)
print("networkx", networkx.__version__)
print("jupyterlab_ready", "ok")
print("mesa_api", RandomActivation.__name__, MultiGrid.__name__)
PY
```

### ขั้นที่ 12: ลงทะเบียน Kernel สำหรับ JupyterLab

คำสั่งชุดนี้สร้าง kernelspec ชื่อ `hpc-mesa` ในพื้นที่ผู้ใช้ เพื่อให้ JupyterLab จากสภาพแวดล้อมนี้หรือจากระบบกลางแสดงเคอร์เนล `Python (hpc-mesa)`

```bash
python -m ipykernel install --user --name hpc-mesa --display-name "Python (hpc-mesa)"
jupyter kernelspec list
```

### ขั้นที่ 13: บันทึกค่าสภาพแวดล้อมสำหรับบทถัดไป

คำสั่งชุดนี้เขียนไฟล์ `notes/hpc-mesa-env.sh` เพื่อให้ผู้ใช้โหลดค่าชุดเดิมในหน้า Jupyter และหน้า ABS โรคระบาด

```bash
cat > notes/hpc-mesa-env.sh <<EOF
export LANTA_PROJECT="$LANTA_PROJECT"
export EPI_ENV_PREFIX="$EPI_ENV_PREFIX"
export EPI_MODULE_ROOT="$EPI_MODULE_ROOT"
export EPI_MODULE_VERSION="$EPI_MODULE_VERSION"
module use "$EPI_MODULE_ROOT"
module load "hpc-mesa/$EPI_MODULE_VERSION"
EOF
```

### ขั้นที่ 14: อ่านไฟล์ค่าสภาพแวดล้อมที่บันทึกไว้

คำสั่งชุดนี้เปิดดูไฟล์ที่บทถัดไปจะใช้ เพื่อยืนยันว่าเส้นทางตรงกับพื้นที่โครงการ

```bash
cat notes/hpc-mesa-env.sh
```

## ตรวจบนเครื่องเข้าใช้งาน

ออกจากเครื่องสำหรับถ่ายโอนข้อมูล แล้วเข้าเครื่องเข้าใช้งานเพื่อทดสอบโมดูลจากมุมมองเดียวกับการส่งงาน

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

### ขั้นที่ 1: เข้าพื้นที่ทำงานและโหลดค่าเดิม

คำสั่งชุดนี้กลับเข้าสู่พื้นที่ทำงานของนวัตกรรมย่อย และโหลดค่าที่บันทึกไว้จากเครื่องสำหรับถ่ายโอนข้อมูล

```bash
cd "$HOME/lanta-episprint"
source notes/hpc-mesa-env.sh 2>/dev/null || true
```

### ขั้นที่ 2: ระบุ Module Root เมื่อต้องกรอกเอง

คำสั่งชุดนี้รับค่า `EPI_MODULE_ROOT` เมื่อยังขาดการโหลดไฟล์จากขั้นก่อน หรือเมื่อเปิดเชลล์ใหม่

```bash
if [ -z "${EPI_MODULE_ROOT:-}" ]; then
    read -rp "Module root เช่น /project/ltXXXXXX-name/modules: " EPI_MODULE_ROOT
    export EPI_MODULE_ROOT
fi
```

### ขั้นที่ 3: ทดสอบโมดูลบนเครื่องเข้าใช้งาน

คำสั่งชุดนี้ยืนยันว่าเครื่องเข้าใช้งานเห็นโมดูลเดียวกับเครื่องสำหรับถ่ายโอนข้อมูล และ JupyterLab พร้อมใช้ภายในงาน Slurm

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
which python
jupyter lab --version
jupyter kernelspec list
python -c "import mesa; from mesa.time import RandomActivation; print('mesa', mesa.__version__, 'ok')"
```

## คำอธิบาย

ทีมสร้างสภาพแวดล้อมแบบ `--prefix` ในพื้นที่โครงการเพื่อให้ใช้ร่วมกันได้ทั้งกลุ่มและอ้างอิงเส้นทางกลางของโครงการ การแยกขั้นสร้างสภาพแวดล้อมออกจากขั้นเติมแพ็กเกจช่วยให้สภาพแวดล้อมเดิมที่มีอยู่แล้วได้รับ `jupyterlab`, `notebook`, `ipykernel` และ `mesa` ตามรุ่นที่บทเรียนใช้จริง

หลักฐานที่ใช้ตัดสินความพร้อมมีสี่ส่วน: `which python` ต้องชี้เข้า `$LANTA_PROJECT/envs/hpc-mesa`, `jupyter lab --version` ต้องแสดงเลขรุ่นเมื่อใช้สภาพแวดล้อมนี้เป็นเซิร์ฟเวอร์, `jupyter kernelspec list` ต้องมี `hpc-mesa`, และการนำเข้าแพ็กเกจใน Python ต้องรายงาน `mesa 2.3.4` พร้อม API `RandomActivation` กับ `MultiGrid` เมื่อครบสี่ส่วนนี้ บท Jupyter และบท ABS โรคระบาดจะใช้รันไทม์เดียวกันทั้งแบบโต้ตอบและแบบงานชุด

ผลตรวจด้วยบัญชี `tn642` เมื่อ 2026-08-02 พบว่า `jupyter lab` พร้อมใช้งานใน `hpc-mesa` หลังเติมแพ็กเกจตามขั้นที่ 6 ส่วน PATH เริ่มต้น, `cray-python/3.10.10`, และ `Mamba/23.11.0-0` ยังขาด executable `jupyter lab` ในรอบตรวจนั้น ดังนั้นเส้นทางหลักของการอบรมใช้ `hpc-mesa` เป็นทั้งเซิร์ฟเวอร์และเคอร์เนล ส่วน JupyterLab กลางของระบบใช้เป็นทางสำรองเมื่อผู้ดูแลเปิดให้ผ่านโมดูลหรือ PATH ของรอบอบรมนั้น
