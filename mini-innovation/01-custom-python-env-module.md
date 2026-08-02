# 01 สร้าง Custom Python Environment และ Module

หน้านี้ใช้เตรียม environment กลางสำหรับ mini innovation แบบ epidemic ABS บน LANTA โดยติดตั้ง Mesa, scientific Python และ JupyterLab ลงใน project space แล้วสร้าง Lmod module ให้ผู้ใช้โหลดซ้ำได้ทั้งบน login node, compute node และ Slurm job

สำหรับการเริ่มจากเครื่อง local ให้ดู [00-connect-to-lanta.md](00-connect-to-lanta.md) ก่อน หน้านี้ใช้ transfer host เพราะมีการดาวน์โหลด package

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `mamba create`, `conda run`, `python -m pip`, heredoc, Lua modulefile, `chmod`, `module use` และ `module load`

## Copy-Paste จากเครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: Login เข้า Transfer Host

block นี้เปิด shell บน transfer host ซึ่งเหมาะกับการสร้าง environment และดาวน์โหลด package

```bash
ssh <lanta-username>@transfer.lanta.nstda.or.th
```

## Copy-Paste บน Transfer Host

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม Workspace

block นี้สร้าง workspace และรับ project directory ที่ใช้เก็บ environment, modulefile และ cache

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p logs notes

if [ -z "${LANTA_PROJECT:-}" ]; then
    read -rp "Project directory เช่น /project/ltXXXXXX-name หรือ /project/tn999996-north: " LANTA_PROJECT
    export LANTA_PROJECT
fi
```

### ขั้นที่ 2: ตั้ง Path ของ Environment

block นี้กำหนด path แบบใช้ซ้ำ เพื่อให้ทุกคนในกลุ่มโหลด module เดียวกันและใช้ cache ใน project space

```bash
export EPI_ENV_NAME="${EPI_ENV_NAME:-hpc-mesa}"
export EPI_ENV_PREFIX="${EPI_ENV_PREFIX:-$LANTA_PROJECT/envs/$EPI_ENV_NAME}"
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-$LANTA_PROJECT/modules}"
export EPI_MODULE_VERSION="${EPI_MODULE_VERSION:-2.3.4}"
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$LANTA_PROJECT/conda-pkgs}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$LANTA_PROJECT/pip-cache}"
```

### ขั้นที่ 3: สร้าง Folder กลาง

block นี้สร้าง directory ที่ใช้เก็บ conda environment, modulefile และ cache

```bash
mkdir -p "$LANTA_PROJECT/envs"
mkdir -p "$EPI_MODULE_ROOT/hpc-mesa"
mkdir -p "$CONDA_PKGS_DIRS"
mkdir -p "$PIP_CACHE_DIR"
```

### ขั้นที่ 4: โหลด Mamba

block นี้โหลด package manager ที่ใช้สร้าง environment บน transfer host

```bash
module purge
module load Mamba/23.11.0-0
mamba --version
```

### ขั้นที่ 5: สร้าง Environment เมื่อ Path ยังว่าง

block นี้สร้าง environment ด้วย Python 3.10 และ scientific packages หลัก เมื่อ path มี environment เดิมอยู่ คำสั่งจะแสดง path เดิมเพื่อให้ตรวจต่อ

```bash
if [ ! -x "$EPI_ENV_PREFIX/bin/python" ]; then
    mamba create -y -p "$EPI_ENV_PREFIX" \
        --override-channels -c conda-forge \
        python=3.10 pip numpy pandas scipy matplotlib pyyaml networkx tqdm
else
    echo "Environment exists: $EPI_ENV_PREFIX"
fi
```

### ขั้นที่ 6: เติม Package ที่ Tutorial ใช้จริง

block นี้ติดตั้งหรือปรับให้มี package ที่ mini innovation ใช้จริง แม้ environment จะถูกสร้างไว้ก่อนหน้าแล้ว ขั้นนี้จึงทำให้ Mesa และ JupyterLab พร้อมกันใน env เดียว

```bash
conda run -p "$EPI_ENV_PREFIX" python -m pip install --no-cache-dir \
    "mesa==$EPI_MODULE_VERSION" \
    "jupyterlab>=4,<5" \
    "notebook>=7,<8" \
    ipykernel
```

### ขั้นที่ 7: สร้าง Modulefile

block นี้สร้างไฟล์ Lua module ชื่อ `hpc-mesa/2.3.4` เพื่อให้ผู้ใช้เรียก environment ด้วย `module load`

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

### ขั้นที่ 8: ใส่ Path จริงลง Modulefile

block นี้แทนค่า placeholder ใน modulefile ด้วย path ของ environment ใน project space

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

block นี้ให้สมาชิกกลุ่มอ่านและใช้ environment/modulefile ได้ และตั้ง setgid bit ให้ folder ใหม่สืบทอด group เดิม

```bash
chmod -R g+rwX "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT" "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR" 2>/dev/null || true
find "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT" -type d -exec chmod g+s {} \; 2>/dev/null || true
```

### ขั้นที่ 10: โหลด Module และตรวจ Package

block นี้ตรวจว่า `python` และ `jupyter` มาจาก environment กลาง และ package สำคัญ import ได้ครบ

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load "hpc-mesa/$EPI_MODULE_VERSION"
which python
which jupyter
jupyter lab --version
```

### ขั้นที่ 11: ตรวจ Version ของ Scientific Stack

block นี้บันทึก version ของ package หลักและ API ของ Mesa ที่ tutorial ใช้

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

### ขั้นที่ 12: บันทึกค่า Environment สำหรับบทถัดไป

block นี้เขียนไฟล์ `notes/hpc-mesa-env.sh` เพื่อให้ผู้ใช้ source ค่าเดิมในหน้า Jupyter และหน้า epidemic ABS

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

### ขั้นที่ 13: อ่านไฟล์ Environment ที่บันทึกไว้

block นี้เปิดดูไฟล์ที่บทถัดไปจะใช้ เพื่อยืนยันว่า path ตรงกับ project space

```bash
cat notes/hpc-mesa-env.sh
```

## Check บน Login Host

ออกจาก transfer host แล้วเข้า login host เพื่อทดสอบ module จากมุมมองที่ใช้ submit job

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

### ขั้นที่ 1: เข้า Workspace และโหลดค่าเดิม

block นี้กลับเข้าสู่ workspace ของ mini innovation และโหลดค่าที่บันทึกไว้จาก transfer host

```bash
cd "$HOME/lanta-episprint"
source notes/hpc-mesa-env.sh 2>/dev/null || true
```

### ขั้นที่ 2: ระบุ Module Root เมื่อต้องกรอกเอง

block นี้รับ `EPI_MODULE_ROOT` เมื่อลืม source ไฟล์จากขั้นก่อน หรือเปิด shell ใหม่

```bash
if [ -z "${EPI_MODULE_ROOT:-}" ]; then
    read -rp "Module root เช่น /project/ltXXXXXX-name/modules: " EPI_MODULE_ROOT
    export EPI_MODULE_ROOT
fi
```

### ขั้นที่ 3: ทดสอบ Module บน Login Host

block นี้ยืนยันว่า login host เห็น module เดียวกับ transfer host และ JupyterLab พร้อมสำหรับ Slurm job

```bash
module purge
module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
which python
jupyter lab --version
python -c "import mesa; from mesa.time import RandomActivation; print('mesa', mesa.__version__, 'ok')"
```

## คำอธิบาย

ทีมสร้าง environment แบบ `--prefix` ใน project space เพื่อให้ใช้ร่วมกันได้ทั้งกลุ่มและอ้างอิง path กลางของ project การแยกขั้นสร้าง environment ออกจากขั้นเติม package ช่วยให้ env เดิมที่มีอยู่แล้วได้รับ `jupyterlab`, `notebook`, `ipykernel` และ `mesa` ตาม version ที่บทเรียนใช้จริง

หลักฐานที่ใช้ตัดสินความพร้อมมีสามส่วน: `which python` และ `which jupyter` ต้องชี้เข้า `$LANTA_PROJECT/envs/hpc-mesa`, `jupyter lab --version` ต้องแสดงเลข version, และ Python import ต้องรายงาน `mesa 2.3.4` พร้อม API `RandomActivation` กับ `MultiGrid` เมื่อครบสามส่วนนี้ บท Jupyter และบท epidemic ABS จะใช้ runtime เดียวกันทั้งแบบ interactive และ batch job
