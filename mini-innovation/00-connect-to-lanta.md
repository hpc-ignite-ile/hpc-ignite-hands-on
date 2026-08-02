# 00 เชื่อมต่อ LANTA และเตรียม Workspace

หน้านี้เป็นหน้าอ้างอิงร่วมสำหรับทุกหน้าใน `mini-innovation/` ถ้าหน้าอื่นบอกให้ "เริ่มจากเครื่อง local" ให้กลับมาดูคำสั่งพื้นฐานจากหน้านี้ได้

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `git clone`, `git pull`, `mkdir -p`, `tee`, `read -rp`, `export` และ `source`

## Copy-Paste จากเครื่อง Local

แทน `<lanta-username>` ด้วยบัญชี LANTA ของตนเอง

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

ถ้าต้องสร้าง environment หรือดาวน์โหลด package จากภายนอก ให้ใช้ transfer host แทน

```bash
ssh <lanta-username>@transfer.lanta.nstda.or.th
```

## Copy-Paste บน LANTA

```bash
mkdir -p "$HOME/hpc-ignite-hands-on"
cd "$HOME"

if [ ! -d "$HOME/hpc-ignite-hands-on/.git" ]; then
    git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git
fi

cd "$HOME/hpc-ignite-hands-on"
git pull --ff-only || true

mkdir -p "$HOME/lanta-episprint"/{configs,jobs,logs,notes,notebooks,prompts,results,src}
cd "$HOME/lanta-episprint"

{
    echo "user=$(whoami)"
    echo "host=$(hostname)"
    echo "date=$(date -Is)"
    echo "workspace=$(pwd)"
    echo
    echo "== quota =="
    myquota 2>&1 || true
    echo
    echo "== balance =="
    sbalance 2>&1 || true
    echo
    echo "== queue =="
    squeue -u "$USER" 2>&1 || true
} | tee notes/connect-check.txt

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

cat > notes/session-env.sh <<EOF
export LANTA_ACCOUNT="$LANTA_ACCOUNT"
export LANTA_PROJECT="$LANTA_PROJECT"
export LANTA_CPU_PARTITION="$LANTA_CPU_PARTITION"
export EPI_MODULE_ROOT="$EPI_MODULE_ROOT"
EOF

cat notes/session-env.sh
```

## คำอธิบาย

ก่อนเริ่ม mini innovation ให้ผู้ใช้แยกบทบาทของเครื่องให้ชัดเจน เครื่อง local คือ notebook หรือ desktop ของผู้ใช้ ส่วน `lanta.nstda.or.th` ใช้ login, แก้ไฟล์, submit job และดู queue ส่วน `transfer.lanta.nstda.or.th` ใช้เมื่อต้องดาวน์โหลด package หรือย้ายข้อมูล

คำสั่งนี้สร้าง workspace ชื่อ `$HOME/lanta-episprint` และบันทึกผลตรวจระบบไว้ใน `notes/connect-check.txt` จากนั้นบันทึกค่า `LANTA_ACCOUNT`, `LANTA_PROJECT`, `LANTA_CPU_PARTITION`, และ `EPI_MODULE_ROOT` ลงใน `notes/session-env.sh` เพื่อใช้ซ้ำในหน้าถัดไป

ถ้าต้องเริ่ม terminal ใหม่บน LANTA ให้กลับเข้า workspace แล้วโหลดค่าชุดเดิมด้วย

```bash
cd "$HOME/lanta-episprint"
source notes/session-env.sh
```

## Check

```bash
cd "$HOME/lanta-episprint"
pwd
cat notes/connect-check.txt | head -20
cat notes/session-env.sh
```

เมื่อสำเร็จ ผู้ใช้ควรเห็น path ที่ลงท้ายด้วย `lanta-episprint`, เห็นข้อมูลใน `notes/connect-check.txt`, และเห็นคำสั่ง export ใน `notes/session-env.sh` หาก `myquota` หรือ `sbalance` แสดง error ให้เก็บข้อความนั้นไว้ก่อน แล้วให้ผู้ดูแลช่วยตรวจ account และ project path เมื่อ `git pull --ff-only` มี conflict ให้ใช้ repo ที่ clone ไว้เดิมสำหรับ lab สด แล้วให้ผู้ดูแล update repo หลังจบกิจกรรม
