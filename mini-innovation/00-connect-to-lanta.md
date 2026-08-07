# 00 เชื่อมต่อ LANTA และเตรียมพื้นที่ทำงาน

หน้านี้เป็นหน้าอ้างอิงร่วมสำหรับทุกบทใน `mini-innovation/` เมื่อบทอื่นระบุให้เริ่มจากเครื่องผู้ใช้ ให้กลับมาใช้คำสั่งพื้นฐานจากหน้านี้ได้ทันที

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../docs/BASH_COMMAND_REFERENCE_TH.md](../docs/BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `mkdir -p`, `tee`, `read -rp`, `export` และ `source`

เมื่อต้องตั้งค่า private key หรือ alias `ssh lanta` ให้ดู [../docs/SSH_PRIVATE_KEY_LANTA_TH.md](../docs/SSH_PRIVATE_KEY_LANTA_TH.md)

## Copy-Paste จากเครื่องผู้ใช้

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

แทน `<lanta-username>` ด้วยบัญชี LANTA ของตนเอง

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

ถ้าต้องสร้างสภาพแวดล้อม Python หรือดาวน์โหลดชุดโปรแกรมจากภายนอก ให้เข้าเครื่องสำหรับถ่ายโอนข้อมูล

```bash
ssh <lanta-username>@transfer.lanta.nstda.or.th
```

## Copy-Paste บน LANTA

คัดลอกทีละชุดคำสั่งตามลำดับ แต่ละชุดทำงานหลักหนึ่งเรื่องและแสดงหลักฐานให้ตรวจทันทีหลังรัน

### ขั้นที่ 1: สร้างพื้นที่ทำงานและตรวจบัญชี

ขั้นนี้สร้างโฟลเดอร์มาตรฐานของชุดฝึก แล้วบันทึกชื่อผู้ใช้ ชื่อเครื่อง เวลา โควตา และคิวงานไว้ในไฟล์เดียว เพื่อใช้ตรวจย้อนกลับเมื่อเกิดปัญหา

```bash
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
```

### ขั้นที่ 2: ระบุบัญชีโครงการและพื้นที่โครงการ

ขั้นนี้รับค่าโครงการที่ Slurm ใช้คิดทรัพยากรและที่เก็บไฟล์กลางของกลุ่ม ผู้ใช้ควรกรอกค่าที่ผู้สอนหรือผู้ดูแลระบบแจ้งไว้

```bash
if [ -z "${LANTA_ACCOUNT:-}" ]; then
    read -rp "Slurm project account เช่น ltXXXXXX หรือ tn999996: " LANTA_ACCOUNT
    export LANTA_ACCOUNT
fi

if [ -z "${LANTA_PROJECT:-}" ]; then
    read -rp "Project directory เช่น /project/ltXXXXXX-name หรือ /project/tn999996-north: " LANTA_PROJECT
    export LANTA_PROJECT
fi
```

### ขั้นที่ 3: บันทึกค่าที่ใช้ซ้ำในบทถัดไป

ขั้นนี้ตั้งพาร์ทิชัน CPU และตำแหน่งโมดูลของกิจกรรม แล้วเขียนลง `notes/session-env.sh` เพื่อให้บทถัดไปโหลดค่าชุดเดียวกัน

```bash
export LANTA_CPU_PARTITION="${LANTA_CPU_PARTITION:-compute-devel}"
export EPI_MODULE_ROOT="${EPI_MODULE_ROOT:-$LANTA_PROJECT/modules}"

cat > notes/session-env.sh <<EOF
export LANTA_ACCOUNT="$LANTA_ACCOUNT"
export LANTA_PROJECT="$LANTA_PROJECT"
export LANTA_CPU_PARTITION="$LANTA_CPU_PARTITION"
export EPI_MODULE_ROOT="$EPI_MODULE_ROOT"
EOF
```

### ขั้นที่ 4: ตรวจไฟล์ค่ากลาง

ขั้นนี้เปิดดูค่าที่บันทึกไว้ ผู้ใช้ควรเห็นชื่อบัญชีโครงการ พื้นที่โครงการ พาร์ทิชัน และตำแหน่งโมดูลตรงกับที่ตั้งใจใช้

```bash
cat notes/session-env.sh
```

## คำอธิบาย

ก่อนเริ่มนวัตกรรมย่อย ผู้ใช้ควรแยกบทบาทของเครื่องให้ชัดเจน เครื่องผู้ใช้คือโน้ตบุ๊กหรือเดสก์ท็อปสำหรับเปิด SSH และเว็บเบราว์เซอร์ ส่วน `lanta.nstda.or.th` ใช้เข้าสู่ระบบ แก้ไฟล์ ส่งงาน และดูคิวงาน ส่วน `transfer.lanta.nstda.or.th` ใช้เมื่อต้องดาวน์โหลดชุดโปรแกรมหรือย้ายข้อมูล

คำสั่งชุดนี้สร้างพื้นที่ทำงานชื่อ `$HOME/lanta-episprint` และบันทึกผลตรวจระบบไว้ใน `notes/connect-check.txt` จากนั้นบันทึกค่า `LANTA_ACCOUNT`, `LANTA_PROJECT`, `LANTA_CPU_PARTITION`, และ `EPI_MODULE_ROOT` ลงใน `notes/session-env.sh` เพื่อใช้ซ้ำในหน้าถัดไป

เมื่อต้องเปิดเทอร์มินัลใหม่บน LANTA ให้กลับเข้าโฟลเดอร์เดิมแล้วโหลดค่าชุดเดิมด้วย

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

เมื่อสำเร็จ ผู้ใช้ควรเห็นเส้นทางที่ลงท้ายด้วย `lanta-episprint`, เห็นข้อมูลใน `notes/connect-check.txt`, และเห็นคำสั่ง `export` ใน `notes/session-env.sh` หาก `myquota` หรือ `sbalance` แสดงข้อผิดพลาด ให้เก็บข้อความนั้นไว้ แล้วให้ผู้ดูแลช่วยตรวจบัญชีโครงการและเส้นทางพื้นที่โครงการ
