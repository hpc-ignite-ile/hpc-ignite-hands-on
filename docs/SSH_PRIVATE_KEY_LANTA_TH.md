# ใช้ SSH Private Key เข้า LANTA

เอกสารนี้เป็น standalone tutorial สำหรับผู้ใช้ที่ต้องการเข้า LANTA จากเครื่อง local ด้วย SSH private key ครอบคลุม macOS, Linux และ Windows WSL พร้อมเหตุผลของแต่ละขั้นและแนวทาง debug ที่ใช้ได้ในห้อง training

คำสั่ง Bash และ SSH syntax ในหน้านี้อธิบายรวมไว้ที่ [BASH_COMMAND_REFERENCE_TH.md](BASH_COMMAND_REFERENCE_TH.md) เช่น `ssh`, `ssh-keygen`, `ssh-copy-id`, `chmod`, `cat`, heredoc, `~/.ssh/config`, redirection และ placeholder

## ภาพรวม

มี 3 วิธีหลักในการใช้ private key เข้า LANTA:

1. **ใช้ key ชื่อมาตรฐาน**: สร้าง key ที่ local แล้วติดตั้ง public key บน LANTA จากนั้นใช้ `ssh <user>@lanta.nstda.or.th`
2. **ใช้ `-i` ระบุ key**: เหมาะกับเครื่องที่มีหลาย key หรือใช้ชื่อเฉพาะ เช่น `id_rsa_lanta`
3. **ใช้ `~/.ssh/config` ทำ alias**: เหมาะกับ training เพราะผู้ใช้พิมพ์ `ssh lanta` และ `ssh lanta-transfer`

หลักการสำคัญคือ private key อยู่บนเครื่อง local ของผู้ใช้ ส่วน public key อยู่บน LANTA ใน `~/.ssh/authorized_keys` เมื่อเชื่อมต่อ LANTA จะใช้ public key ตรวจลายเซ็นที่สร้างจาก private key

## Main Path สำหรับ Training

ใช้ main path นี้เมื่อผู้ใช้มี terminal แบบ OpenSSH บน macOS, Linux หรือ Windows WSL

### ขั้นที่ 1: ตรวจ OpenSSH บนเครื่อง Local

block นี้ตรวจว่าเครื่อง local มี `ssh` พร้อมใช้งาน และเห็น folder `~/.ssh`

```bash
ssh -V
mkdir -p ~/.ssh
ls -ld ~/.ssh
```

ผลที่ดีคือ `ssh -V` แสดง OpenSSH version และ `~/.ssh` เป็น folder ของผู้ใช้ปัจจุบัน

### ขั้นที่ 2: สร้าง Key สำหรับ LANTA

block นี้สร้าง private/public key คู่ใหม่สำหรับ LANTA โดยใช้ RSA 4096 เพื่อ compatibility ใน training

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_lanta -C "lanta-$(whoami)"
```

ไฟล์ที่ได้มีสองไฟล์:

- `~/.ssh/id_rsa_lanta` คือ private key เก็บไว้บนเครื่อง local
- `~/.ssh/id_rsa_lanta.pub` คือ public key ใช้ติดตั้งบน LANTA

ตั้ง passphrase เมื่อใช้ key ระยะยาวหรือเครื่อง local เป็นเครื่องส่วนตัวหลายงาน สำหรับ training สด ผู้สอนอาจกำหนดนโยบาย passphrase ตามเวลาที่มีและระดับความเสี่ยงของห้องเรียน

### ขั้นที่ 3: ตั้ง Permission ของ Key

block นี้ตั้งสิทธิ์ไฟล์ให้ OpenSSH ยอมใช้ key และให้ private key อ่านได้เฉพาะเจ้าของไฟล์

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa_lanta
chmod 644 ~/.ssh/id_rsa_lanta.pub
ls -l ~/.ssh/id_rsa_lanta ~/.ssh/id_rsa_lanta.pub
```

ผลที่ดีคือ private key แสดง permission คล้าย `-rw-------` และ public key แสดง permission คล้าย `-rw-r--r--`

### ขั้นที่ 4: ติดตั้ง Public Key บน LANTA ด้วย `ssh-copy-id`

block นี้ส่ง public key จากเครื่อง local ไปเพิ่มใน `~/.ssh/authorized_keys` บน LANTA

```bash
ssh-copy-id -i ~/.ssh/id_rsa_lanta.pub <lanta-username>@lanta.nstda.or.th
```

ระหว่างขั้นนี้ LANTA อาจถามรหัสผ่านหรือ 2FA หนึ่งครั้ง หลังจากนั้น key จะใช้พิสูจน์ตัวตนแทนการพิมพ์รหัสผ่านซ้ำหลายรอบ

### ขั้นที่ 5: ทดสอบ Login ด้วย `-i`

block นี้ระบุ private key อย่างชัดเจน เหมาะกับผู้ใช้ที่มีหลาย key บนเครื่อง local

```bash
ssh -i ~/.ssh/id_rsa_lanta <lanta-username>@lanta.nstda.or.th
```

เมื่อเข้า LANTA ได้ ให้ตรวจชื่อเครื่องและออกจาก session

```bash
hostname
whoami
exit
```

### ขั้นที่ 6: สร้าง SSH Alias สำหรับ LANTA

block นี้สร้างไฟล์ config แยกใน `~/.ssh/config.d/lanta.conf` แล้วเพิ่ม `Include` ใน `~/.ssh/config` เพื่อให้ผู้ใช้พิมพ์คำสั้น ๆ ได้ แทน `<lanta-username>` ด้วยบัญชีจริงก่อนแปะ block

```bash
mkdir -p ~/.ssh/config.d
cat > ~/.ssh/config.d/lanta.conf <<'EOF'
Host lanta
    HostName lanta.nstda.or.th
    User <lanta-username>
    IdentityFile ~/.ssh/id_rsa_lanta
    IdentitiesOnly yes

Host lanta-transfer
    HostName transfer.lanta.nstda.or.th
    User <lanta-username>
    IdentityFile ~/.ssh/id_rsa_lanta
    IdentitiesOnly yes
EOF
touch ~/.ssh/config
grep -qxF 'Include ~/.ssh/config.d/*.conf' ~/.ssh/config || printf '\nInclude ~/.ssh/config.d/*.conf\n' >> ~/.ssh/config
chmod 600 ~/.ssh/config ~/.ssh/config.d/lanta.conf
```

เมื่อเครื่องมี config เดิมอยู่แล้ว วิธีนี้เก็บ LANTA profile แยกไว้ในไฟล์เฉพาะของ training

### ขั้นที่ 7: ใช้ Alias

block นี้ทดสอบ login host และ transfer host ด้วยชื่อ alias

```bash
ssh lanta
```

ใช้ transfer host เมื่อต้องย้ายไฟล์หรือเตรียม package ใน project space

```bash
ssh lanta-transfer
```

## วิธี Manual เมื่อติดตั้ง Public Key ด้วย `ssh-copy-id` แล้วติดขัด

ใช้วิธีนี้เมื่อเครื่อง local มี `ssh` แต่คำสั่ง `ssh-copy-id` ขาดจากระบบ

### ขั้นที่ 1: แสดง Public Key บนเครื่อง Local

block นี้พิมพ์ public key หนึ่งบรรทัดเพื่อให้ผู้ใช้ copy ทั้งบรรทัด

```bash
cat ~/.ssh/id_rsa_lanta.pub
```

public key จะขึ้นต้นด้วย `ssh-rsa` และลงท้ายด้วย comment เช่น `lanta-username`

### ขั้นที่ 2: Login เข้า LANTA ด้วยวิธีที่บัญชีรองรับอยู่

block นี้เปิด shell บน LANTA เพื่อเตรียม `authorized_keys`

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

### ขั้นที่ 3: เตรียม `authorized_keys` บน LANTA

block นี้สร้าง folder และไฟล์ฝั่ง LANTA พร้อม permission ที่เหมาะกับ OpenSSH server

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### ขั้นที่ 4: เพิ่ม Public Key ลงใน `authorized_keys`

block นี้เพิ่ม public key ที่ copy จากเครื่อง local ให้ LANTA รู้จัก key ของผู้ใช้ แทน `<paste-one-line-public-key-from-local>` ด้วย public key ทั้งบรรทัดก่อนแปะ block

```bash
printf '%s\n' '<paste-one-line-public-key-from-local>' >> ~/.ssh/authorized_keys
tail -1 ~/.ssh/authorized_keys
```

จากนั้นเปิด terminal local ใหม่แล้วทดสอบ `ssh -i ~/.ssh/id_rsa_lanta <lanta-username>@lanta.nstda.or.th`

## Windows WSL

บน Windows ให้ใช้ Ubuntu/WSL เป็น terminal หลักสำหรับ training เพราะ permission ของ Linux filesystem เข้ากับ OpenSSH ได้ตรงกว่า

### ขั้นที่ 1: ตรวจ OpenSSH ใน WSL

block นี้รันใน Ubuntu/WSL

```bash
ssh -V
mkdir -p ~/.ssh
ls -ld ~/.ssh
```

### ขั้นที่ 2: Copy Key จาก Windows Profile เข้า WSL

block นี้ใช้เมื่อ key อยู่ใน `C:\Users\<windows-username>\.ssh`

```bash
cp /mnt/c/Users/<windows-username>/.ssh/id_rsa_lanta ~/.ssh/id_rsa_lanta
cp /mnt/c/Users/<windows-username>/.ssh/id_rsa_lanta.pub ~/.ssh/id_rsa_lanta.pub
chmod 600 ~/.ssh/id_rsa_lanta
chmod 644 ~/.ssh/id_rsa_lanta.pub
```

การ copy เข้า `~/.ssh` ใน WSL ทำให้ OpenSSH อ่าน permission แบบ Linux ได้ชัดเจน

### ขั้นที่ 3: Login จาก WSL

block นี้ใช้ key ที่อยู่ใน WSL

```bash
ssh -i ~/.ssh/id_rsa_lanta <lanta-username>@lanta.nstda.or.th
```

เมื่อตั้ง alias ตาม main path แล้ว ผู้ใช้ WSL สามารถใช้ `ssh lanta` และ `ssh lanta-transfer` ได้เหมือน macOS/Linux

## Debug Checklist

| อาการ | ตรวจด้วยคำสั่ง | แนวแก้ |
|---|---|---|
| SSH ถามรหัสผ่านหลายรอบ | `ssh -vvv -i ~/.ssh/id_rsa_lanta <lanta-username>@lanta.nstda.or.th` | ดูบรรทัด `Offering public key` และตรวจว่า key path ถูกต้อง |
| Client ข้าม key เพราะ permission กว้าง | `ls -l ~/.ssh/id_rsa_lanta` | รัน `chmod 600 ~/.ssh/id_rsa_lanta` |
| Server ยังขาด key ชุดนี้ | `tail -1 ~/.ssh/authorized_keys` บน LANTA | เพิ่ม public key ให้ครบหนึ่งบรรทัด |
| Alias ใช้ key ผิดตัว | `ssh -G lanta | grep -E 'hostname|user|identityfile|identitiesonly'` | แก้ `~/.ssh/config.d/lanta.conf` |
| Transfer host เข้าอีกเครื่อง | `ssh -G lanta-transfer | grep hostname` | ตรวจว่า `HostName` เป็น `transfer.lanta.nstda.or.th` |

## แนวใช้ใน HPC Ignite

สำหรับกิจกรรมสด แนะนำให้ผู้ใช้เตรียม key และ alias ล่วงหน้า:

1. `ssh lanta` สำหรับ login, แก้ไฟล์, submit job และดู queue
2. `ssh lanta-transfer` สำหรับย้ายไฟล์ เตรียม package หรือทำงานที่เกี่ยวกับ project space
3. ใช้ `scp` หรือ `rsync` ผ่าน transfer host เมื่อต้องส่งข้อมูลจาก local ไป LANTA

เมื่อผู้ใช้มี alias แล้ว หน้า hand-on อื่นสามารถเริ่มด้วยคำสั้น ๆ เช่น `ssh lanta` แล้วเข้าสู่ workspace ของบทนั้นทันที ผู้ใช้จึงใช้เวลาในห้องเรียนกับ Slurm, module, model, data และการตรวจผลมากขึ้น
