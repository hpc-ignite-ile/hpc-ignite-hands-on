# 00 เชื่อมต่อ LANTA และเตรียม Workspace

หน้านี้เป็นหน้าอ้างอิงร่วมสำหรับทุกหน้าใน `mini-innovation/` ถ้าหน้าอื่นบอกให้ "เริ่มจากเครื่อง local" ให้กลับมาดูคำสั่งพื้นฐานจากหน้านี้ได้

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

การทำงานบน LANTA แยกเครื่อง local, login host, transfer host และ compute node ออกจากกันอย่างชัดเจน เครื่อง local คือ notebook หรือ desktop ของผู้เรียน ส่วน `lanta.nstda.or.th` ใช้ login, จัดไฟล์, แก้ script, submit job และดู queue ส่วน `transfer.lanta.nstda.or.th` เหมาะกับงานที่ต้องดาวน์โหลด package หรือย้ายข้อมูล

Block นี้สร้าง workspace ชื่อ `$HOME/lanta-episprint` และบันทึกหลักฐานไว้ใน `notes/connect-check.txt` เพื่อให้ตรวจย้อนกลับได้ว่าใช้ user ใด เครื่องใด quota เป็นอย่างไร และมี job ใดค้างอยู่ การเก็บ `LANTA_ACCOUNT`, `LANTA_PROJECT`, `LANTA_CPU_PARTITION`, และ `EPI_MODULE_ROOT` ลง `notes/session-env.sh` ช่วยให้หน้าอื่นนำค่ากลับมาใช้ซ้ำได้

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

ถ้าคำสั่ง `myquota` หรือ `sbalance` แสดง error ให้เก็บข้อความนั้นไว้ก่อน ไม่จำเป็นต้องหยุด lab ทันที แต่ให้ผู้สอนช่วยดู account และ project path ก่อนส่งงานใหญ่ ถ้า `git pull --ff-only` ไม่สำเร็จเพราะเครื่องไม่มี network ให้ใช้ repo ที่ clone ไว้เดิมได้
