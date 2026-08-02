# 01 สร้าง Custom Python Environment และ Module

หน้านี้ใช้เมื่อทีมต้องเตรียม environment กลางสำหรับ mini innovation แบบ epidemic ABS โดยติดตั้ง Mesa, scientific Python และ Jupyter ลงใน project space แล้วสร้าง Lmod module เพื่อให้ผู้ใช้โหลดได้ง่าย

สำหรับการเริ่มจากเครื่อง local ให้ดู [00-connect-to-lanta.md](00-connect-to-lanta.md) ก่อน หน้านี้ใช้ transfer host เพราะมีการดาวน์โหลด package

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `mamba create`, `conda run`, `python -m pip`, heredoc, Lua modulefile, `chmod`, `module use` และ `module load`

## Copy-Paste จากเครื่อง Local

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

```bash
ssh <lanta-username>@transfer.lanta.nstda.or.th
```

## Copy-Paste บน Transfer Host

แปะทีละ block ตามลำดับ แต่ละ block ทำหนึ่งงานหลักและมีหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
mkdir -p "$HOME/lanta-episprint"
cd "$HOME/lanta-episprint"
mkdir -p logs notes

if [ -z "${LANTA_PROJECT:-}" ]; then
    read -rp "Project directory เช่น /project/ltXXXXXX-name หรือ /project/tn999996-north: " LANTA_PROJECT
    export LANTA_PROJECT
fi
```

### ขั้นที่ 2: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
export EPI_ENV_NAME="${EPI_ENV_NAME:-hpc-mesa}"
export EPI_ENV_PREFIX="${EPI_ENV_PREFIX:-$LANTA_PROJECT/envs/$EPI_ENV_NAME}"
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-$LANTA_PROJECT/modules}"
export EPI_MODULE_VERSION="${EPI_MODULE_VERSION:-2.3.4}"
export CONDA_PKGS_DIRS="${CONDA_PKGS_DIRS:-$LANTA_PROJECT/conda-pkgs}"
export PIP_CACHE_DIR="${PIP_CACHE_DIR:-$LANTA_PROJECT/pip-cache}"

mkdir -p "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT/hpc-mesa" "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR"
```

### ขั้นที่ 3: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
module purge
module load Mamba/23.11.0-0

if [ ! -x "$EPI_ENV_PREFIX/bin/python" ]; then
    mamba create -y -p "$EPI_ENV_PREFIX" \
        --override-channels -c conda-forge \
        python=3.10 pip numpy pandas scipy matplotlib pyyaml networkx tqdm \
        jupyterlab notebook ipykernel
else
    echo "Environment exists: $EPI_ENV_PREFIX"
fi
```

### ขั้นที่ 4: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
conda run -p "$EPI_ENV_PREFIX" python -m pip install --no-cache-dir "mesa==$EPI_MODULE_VERSION"
```

### ขั้นที่ 5: สร้างไฟล์ `$EPI_MODULE_ROOT/hpc-mesa/$EPI_MODULE_VERSION.lua`

ขั้นนี้ทำงานหนึ่งส่วนของ workflow ให้แปะและตรวจผลก่อนขยับไปขั้นถัดไป

```bash
cat > "$EPI_MODULE_ROOT/hpc-mesa/$EPI_MODULE_VERSION.lua" <<'LUA'
help([[
hpc-mesa: Python environment for LANTA EpiSprint.
It provides Mesa, NumPy, pandas, SciPy, Matplotlib, NetworkX, PyYAML, and Jupyter.
]])

whatis("Python/Mesa environment for LANTA EpiSprint mini innovation")

local prefix = "__EPI_ENV_PREFIX__"
prepend_path("PATH", pathJoin(prefix, "bin"))
setenv("HPC_MESA_ENV", prefix)
setenv("PYTHONNOUSERSITE", "1")
LUA
```

### ขั้นที่ 6: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

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

### ขั้นที่ 7: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
chmod -R g+rwX "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT" "$CONDA_PKGS_DIRS" "$PIP_CACHE_DIR" 2>/dev/null || true
find "$LANTA_PROJECT/envs" "$EPI_MODULE_ROOT" -type d -exec chmod g+s {} \; 2>/dev/null || true

module use "$EPI_MODULE_ROOT"
module load "hpc-mesa/$EPI_MODULE_VERSION"

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
```

### ขั้นที่ 8: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

```bash
print("python", sys.version.split()[0])
print("mesa", mesa.__version__)
print("numpy", numpy.__version__)
print("pandas", pandas.__version__)
print("scipy", scipy.__version__)
print("matplotlib", matplotlib.__version__)
print("pyyaml", yaml.__version__)
print("networkx", networkx.__version__)
print("mesa_api", "RandomActivation and MultiGrid OK")
PY
```

### ขั้นที่ 9: เตรียม workspace และตัวแปร

ขั้นนี้กำหนดพื้นที่ทำงานของบท สร้าง folder มาตรฐาน และตั้งค่า account/partition ที่ใช้ซ้ำในขั้นถัดไป

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

### ขั้นที่ 10: ตรวจไฟล์และ log

ขั้นนี้อ่านหลักฐานหลังรัน เช่นรายชื่อไฟล์ ผลลัพธ์ท้าย log หรือสถานะงาน เพื่อยืนยันว่า workflow เดินครบ

```bash
cat notes/hpc-mesa-env.sh
```

## คำอธิบาย

ในขั้นตอนนี้ ทีมจะสร้าง environment แบบ `--prefix` ใน project space เพื่อให้ใช้ร่วมกันได้ทั้งกลุ่มและอ้างอิง path กลางของ project

คำสั่งนี้ตั้ง `CONDA_PKGS_DIRS` และ `PIP_CACHE_DIR` ไปที่ project เพื่อให้ cache เขียนได้ และติดตั้ง `mesa==2.3.4` เพราะ tutorial ใช้ API เช่น `mesa.time.RandomActivation` และ `mesa.space.MultiGrid`

เมื่อสร้างเสร็จ ผู้ใช้จะได้ module file ที่ `$EPI_MODULE_ROOT/hpc-mesa/2.3.4.lua` หลังจาก `module use` และ `module load hpc-mesa/2.3.4` คำสั่ง `python` จะชี้ไปยัง environment ที่เตรียมไว้ และใช้ได้ทั้ง batch job กับ Jupyter

## Check บน Login Host

ออกจาก transfer host แล้วเข้า login host เพื่อทดสอบ module จากมุมมองที่ใช้ submit job

```bash
ssh <lanta-username>@lanta.nstda.or.th
cd "$HOME/lanta-episprint"
source notes/hpc-mesa-env.sh 2>/dev/null || true

if [ -z "${EPI_MODULE_ROOT:-}" ]; then
    read -rp "Module root เช่น /project/ltXXXXXX-name/modules: " EPI_MODULE_ROOT
    export EPI_MODULE_ROOT
fi

module use "$EPI_MODULE_ROOT"
module load hpc-mesa/2.3.4
which python
python -c "import mesa; from mesa.time import RandomActivation; print('mesa', mesa.__version__, 'ok')"
```

เมื่อ `module load hpc-mesa/2.3.4` แจ้ง module error ให้ตรวจว่า `EPI_MODULE_ROOT` ชี้ไปที่ project เดียวกับที่สร้าง environment เมื่อ `which python` ชี้ออกนอก project ให้ `module purge` แล้ว `module use ...` และ `module load ...` ใหม่
