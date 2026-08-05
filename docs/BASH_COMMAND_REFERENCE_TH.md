# อ้างอิงคำสั่ง Bash และ Slurm ที่ใช้ใน Repo

เอกสารนี้อธิบายคำสั่งและ syntax ที่ปรากฏใน `hpc-ignite-hands-on` เพื่อให้ผู้ใช้เข้าใจว่าแต่ละบรรทัดทำอะไร เหตุผลที่ใช้ และหลักฐานที่ควรตรวจหลังรันงานบน LANTA

## วิธีอ่าน Command Block

| รูปแบบ | ความหมาย | ใช้ตรวจอะไร |
|---|---|---|
| `# ข้อความ` | comment สำหรับคนอ่าน shell จะข้ามบรรทัดนี้ | ใช้บอกเจตนาของขั้นตอน เช่น เปิด lab, สร้าง workspace |
| `<username>` | placeholder ให้แทนด้วยค่าจริง | ตรวจว่าผู้ใช้แทนค่าก่อนแปะคำสั่ง |
| `"$HOME"` | ตัวแปร home directory ของผู้ใช้ พร้อม quote เพื่อรองรับ path ที่มีช่องว่าง | ตรวจด้วย `echo "$HOME"` หรือ `pwd` |
| `"${VAR:-default}"` | ใช้ค่า `VAR` ถ้ามีค่า หรือใช้ `default` เมื่อยังว่าง | ใช้ตั้ง partition เริ่มต้น เช่น `compute-devel` |
| `"${VAR:?message}"` | บังคับให้ `VAR` มีค่า ถ้าว่าง shell จะหยุดพร้อมข้อความ | ใช้กับค่าที่ job ต้องมี เช่น `EPI_MODULE_ROOT` |
| `$(command)` | command substitution นำผลลัพธ์ของ command มาใส่ในตัวแปรหรือข้อความ | เช่น `job_id=$(sbatch --parsable ...)` |
| `\` ท้ายบรรทัด | ต่อคำสั่งยาวให้เขียนหลายบรรทัด | ใช้กับ `python ... --option ...` และ `mamba create ...` |

## `sed`

`sed` คือ stream editor ใช้อ่านหรือแก้ข้อความแบบเป็นบรรทัด ใน repo นี้ใช้เพื่อเปิดดูช่วงหนึ่งของไฟล์ผ่าน terminal

```bash
sed -n '1,120p' lanta-experience/README.md
```

- `-n` ให้ `sed` เงียบไว้ก่อน จึงพิมพ์เฉพาะช่วงที่สั่ง
- `'1,120p'` หมายถึงพิมพ์บรรทัดที่ 1 ถึง 120
- `lanta-experience/README.md` คือไฟล์ที่จะอ่าน

ผลที่ถูกต้องคือเห็นหัวข้อและคำสั่งเริ่มต้นของ lab หลัก เมื่อ `sed` เปิดไฟล์ error ให้ตรวจตำแหน่งด้วย `pwd` และดูชื่อไฟล์ด้วย `ls`

## การเข้าเครื่องและย้ายไฟล์

| คำสั่ง | ความหมาย | ตัวอย่างใน repo | หลักฐานที่ควรเห็น |
|---|---|---|---|
| `ssh` | เปิด shell บนเครื่องระยะไกล | `ssh <username>@lanta.nstda.or.th` | prompt เปลี่ยนเป็นเครื่อง LANTA |
| `ssh -i KEY` | ระบุ private key ที่ใช้กับ host นี้ | `ssh -i ~/.ssh/id_rsa_lanta <username>@lanta.nstda.or.th` | client เสนอ key ที่เลือกไว้ |
| `ssh -N -L LOCAL:HOST:REMOTE` | เปิด SSH tunnel โดยส่ง local port ไปยัง service ภายใน LANTA | `ssh -N -L 8877:lanta-c-065:8731 <username>@lanta.nstda.or.th` | terminal ค้างเพื่อรักษา tunnel และ browser เปิดผ่าน `127.0.0.1` |
| `ssh -o NAME=value` | ตั้ง option เฉพาะครั้งให้ OpenSSH | `ssh -o ExitOnForwardFailure=yes ...` | tunnel fail ทันทีเมื่อ forward port ขัดข้อง |
| `ssh-keygen` | สร้างคู่กุญแจ private/public สำหรับ SSH | `ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_lanta -C "lanta-$(whoami)"` | มีไฟล์ key และ `.pub` |
| `ssh-copy-id` | ติดตั้ง public key ไปยัง `authorized_keys` บน server | `ssh-copy-id -i ~/.ssh/id_rsa_lanta.pub <username>@lanta.nstda.or.th` | login รอบถัดไปใช้ key ได้ |
| `ssh -G HOST` | แสดง config ที่ OpenSSH ใช้จริงกับ host | `ssh -G lanta | grep identityfile` | เห็น key path ที่ alias ใช้ |
| `scp` | copy ไฟล์หนึ่งชุดผ่าน SSH | `scp local-file <username>@transfer.lanta.nstda.or.th:/project/<project-id>/` | ไฟล์ปลายทางมีขนาดตรงกับต้นทาง |
| `rsync -rvz` | sync folder ผ่าน SSH พร้อมรายงานรายการไฟล์ | `rsync -rvz ./local-folder/ ...` | output แสดงไฟล์ที่ส่ง และปลายทางเปิดอ่านได้ |
| `git clone` | download repo ครั้งแรกสำหรับสำเนา reference ของผู้สอน | `git clone https://github.com/hpc-ignite-ile/hpc-ignite-hands-on.git` | มี folder `hpc-ignite-hands-on/` |
| `git pull --ff-only` | update repo เมื่อมี remote commit แบบ fast-forward | `git pull --ff-only || true` | repo อยู่บน commit ล่าสุด หรือใช้สำเนาเดิมต่อได้ |

## การเดินทางใน Filesystem

| คำสั่ง | ความหมาย | แนวใช้ที่ดี |
|---|---|---|
| `cd` | เปลี่ยน working directory | ใช้ `cd "$HOME/hpc-ignite-standalone/<lab-id>"` ก่อนสร้างไฟล์และส่ง job ของบทนั้น |
| `pwd` | พิมพ์ path ปัจจุบัน | ใช้ยืนยันว่าอยู่ใน workspace ที่ถูกต้อง |
| `ls` | แสดงรายชื่อไฟล์แบบสั้น | ใช้ดูว่า repo หรือ folder ถูกสร้างแล้ว |
| `find` | ค้นหาไฟล์หรือ folder ตามเงื่อนไข | `find results -maxdepth 1 -type f` ใช้ตรวจผลลัพธ์ |
| `mkdir -p` | สร้าง folder และยอมรับ folder ที่มีอยู่แล้ว | ใช้สร้าง `jobs logs results src notes configs` |
| `cp` | copy ไฟล์ | ใช้เก็บ input/config สำเนาก่อนรันงาน |

## การอ่านและสร้างไฟล์

| คำสั่งหรือ syntax | ความหมาย | แนวใช้ใน repo |
|---|---|---|
| `cat file` | พิมพ์ทั้งไฟล์ | ใช้อ่าน config หรือ result สั้น ๆ |
| `cat > file <<'EOF'` | heredoc สร้างไฟล์จากข้อความหลายบรรทัด | ใช้สร้าง `.py`, `.sbatch`, `.env`, `.lua` ผ่าน terminal |
| `<<'PY'` หรือ `<<'SLURM'` | quoted heredoc marker | shell จะเก็บ `$VAR` ภายใน block ไว้ตามตัวอักษรก่อนเขียนไฟล์ |
| `~/.ssh/config` | config ของ OpenSSH client | ใช้สร้าง alias เช่น `Host lanta` |
| `~/.ssh/authorized_keys` | รายการ public key ที่ server ยอมรับ | ใช้ฝั่ง LANTA เพื่ออนุญาต key ของผู้ใช้ |
| `head -20 file` | อ่าน 20 บรรทัดแรก | ใช้ตรวจหัวไฟล์ log หรือ CSV |
| `tail -50 file` | อ่าน 50 บรรทัดท้าย | ใช้อ่าน error หรือผลท้าย job |
| `tail -n +1 file` | พิมพ์ไฟล์ตั้งแต่บรรทัดแรก | ใช้ให้เห็นไฟล์ทั้งชุดพร้อมชื่อคำสั่งชัดเจน |
| `tee file` | พิมพ์ออกจอและเขียนลงไฟล์พร้อมกัน | ใช้เก็บหลักฐานจาก `python`, `nvidia-smi`, `gmx` |
| `sha256sum file` | คำนวณ fingerprint ของไฟล์ | ใช้ตรวจว่าไฟล์ input/result รุ่นเดิมยังเหมือนเดิม |

## Text Processing

| คำสั่ง | ความหมาย | ตัวอย่างการใช้ใน repo |
|---|---|---|
| `sort` | เรียงบรรทัดข้อความ | ใช้เรียงรายชื่อไฟล์จาก `find` หรือ output ของ MPI rank |
| `grep -E "pattern" file` | ค้นบรรทัดด้วย regular expression | ใช้ดึง `total energy`, `Performance`, หรือข้อความ convergence จาก log |
| `awk` | อ่านและแปลงข้อความเป็นคอลัมน์ | เหมาะกับการสรุป TSV/CSV สั้น ๆ ใน shell |
| `wc -l file` | นับจำนวนบรรทัด | ใช้ตรวจจำนวนแถวของ CSV เทียบกับจำนวนวันหรือจำนวน scenario |
| `cut -f1 file` | เลือกคอลัมน์จาก TSV | ใช้ดึง job id จาก `notes/job-history.tsv` |
| `paste -sd, -` | รวมหลายบรรทัดเป็นบรรทัดเดียวคั่นด้วย comma | ใช้สร้างรายการ job id สำหรับ `sacct -j` |

## Shell Safety และตัวแปร

| รูปแบบ | ความหมาย | เหตุผลที่ใช้ |
|---|---|---|
| `set -euo pipefail` | ให้ script หยุดเมื่อ command error, ใช้ตัวแปรว่าง, หรือ pipeline ล้มเหลว | ลดโอกาสได้ผลลัพธ์เงียบ ๆ จาก job ที่พังกลางทาง |
| `export VAR=value` | ตั้ง environment variable ให้ command ลูกเห็นด้วย | ใช้ส่ง account, partition, path ไปยัง job |
| `read -rp "prompt" VAR` | ถามค่าจากผู้ใช้ใน terminal | ใช้กรอก `LANTA_ACCOUNT` หรือ project path |
| `if [ -z "${VAR:-}" ]; then ... fi` | ตรวจว่าตัวแปรว่าง | ใช้ถามค่าเฉพาะครั้งแรก |
| `if [ -n "${VAR:-}" ]; then ... fi` | ตรวจว่าตัวแปรมีค่า | ใช้เพิ่ม option เช่น `-A "$LANTA_ACCOUNT"` |
| `[ -f file ]` | ตรวจว่า path เป็นไฟล์ | ใช้ก่อนอ่าน config, log หรือ result |
| `[ -d dir ]` | ตรวจว่า path เป็น folder | ใช้ก่อนเตรียม workspace หรืออ่านผลลัพธ์ |
| `for file in pattern; do ... done` | loop ผ่านไฟล์หลายไฟล์ | ใช้สรุป CSV หลายชุดหรือ log หลาย task |
| `continue` | ข้ามรอบ loop ปัจจุบัน | ใช้เมื่อ pattern ยังว่างจากไฟล์ที่ตรงเงื่อนไข |
| `exit 1` | จบ script พร้อมรหัส error | ใช้หยุดเมื่อ prerequisite สำคัญขาด |
| `echo "text"` | พิมพ์ข้อความลง stdout | ใช้สร้าง log ที่อ่านง่ายและบอกคำสั่งถัดไป |
| `printf "format" ...` | พิมพ์ข้อความตาม format | ใช้ใน C examples และ shell ที่ต้องควบคุมรูปแบบ output |
| `SBATCH_ACCOUNT=()` | Bash array ว่าง | ใช้ประกอบ option ของ `sbatch` อย่างปลอดภัย |
| `"${SBATCH_ACCOUNT[@]}"` | ขยาย array เป็น argument หลายชิ้น | รักษา quoting ของ account option |
| `source file.sh` | รัน script ใน shell ปัจจุบัน | ใช้กับ helper script ของผู้สอนหรือ session env; standalone lab เขียน `module load` ใน `jobs/*.sbatch` โดยตรง |
| `chmod -R g+rwX path` | ให้ group อ่าน/เขียน และเข้า folder ได้ | ใช้กับ project environment ที่หลายคนใช้ร่วมกัน |
| `chmod u+x file` | เพิ่มสิทธิ์ execute ให้เจ้าของไฟล์ | ใช้กับ script ที่ต้องการเปิดอ่านหรือรันโดยตรง |
| `chmod 700 ~/.ssh` | ให้เจ้าของเข้า folder `.ssh` ได้คนเดียว | ใช้ก่อนติดตั้ง `authorized_keys` |
| `chmod 600 private_key` | ให้เจ้าของอ่าน/เขียน private key ได้คนเดียว | ใช้กับ `~/.ssh/id_rsa_lanta` และ `~/.ssh/config` |
| `chmod 644 public_key.pub` | ให้ public key อ่านได้ตามปกติ | ใช้กับ `~/.ssh/id_rsa_lanta.pub` |
| `2>/dev/null` | ส่ง stderr ทิ้ง | ใช้ลดเสียงรบกวนเมื่อ probe module fallback |
| `2>&1` | รวม stderr เข้ากับ stdout | ใช้เก็บ error และ output ลง log เดียวกัน |
| `|| true` | ให้ script เดินต่อเมื่อ command probe ล้มเหลว | ใช้กับคำสั่งตรวจระบบที่เป็นข้อมูลประกอบ |
| `|` | pipe ส่ง output จาก command แรกเข้า command ถัดไป | เช่น `python ... | tee result.txt` |
| `>` และ `>>` | เขียนทับไฟล์ และเขียนต่อท้ายไฟล์ | ใช้สร้างไฟล์ใหม่หรือเพิ่มบรรทัดใน `notes/job-history.tsv` |

## Lmod Modules

| คำสั่ง | ความหมาย | แนวใช้ที่ดี |
|---|---|---|
| `module purge` | ล้าง module ที่โหลดไว้ | ใช้ต้น `.sbatch` เพื่อให้ environment reproducible |
| `module load NAME` | โหลด software stack | ใช้กับ `cray-python`, `Mamba`, `GROMACS`, `QuantumESPRESSO` |
| `module list` | แสดง module ที่โหลดอยู่ | เก็บใน log เพื่อยืนยัน runtime |
| `module avail NAME` | ดู module ที่มีชื่อใกล้เคียง | ใช้สำรวจว่าระบบมี package ใด |
| `module spider NAME` | ค้น module แบบละเอียด | ใช้หา version และ dependency |
| `module use PATH` | เพิ่ม path ของ module ส่วนตัว | ใช้กับ `EPI_MODULE_ROOT` สำหรับ `hpc-mesa/2.3.4` |

ผลที่ถูกต้องคือ `module list` แสดง software version ที่ lab ต้องใช้ และ `command -v <tool>` หรือ `which python` ชี้ไปยัง executable ที่สอดคล้องกับ module นั้น

## Lua Modulefile Syntax

ไฟล์ `mini-innovation/01-custom-python-env-module.md` สร้าง modulefile ชื่อ `hpc-mesa/2.3.4.lua` เพื่อให้ Lmod โหลด environment ของ Mesa ได้เหมือน software module อื่นบน LANTA

| Syntax | ความหมาย | ผลที่ควรตรวจ |
|---|---|---|
| `help([[ ... ]])` | ข้อความช่วยเหลือเมื่อผู้ใช้เรียก `module help` | อธิบาย package สำคัญของ environment |
| `whatis("...")` | คำอธิบายสั้นสำหรับ `module whatis` | บอกหน้าที่ของ module ในหนึ่งบรรทัด |
| `local prefix = "..."` | ตัวแปรใน Lua modulefile | ชี้ไปยัง root ของ environment ใน project |
| `prepend_path("PATH", pathJoin(prefix, "bin"))` | เพิ่ม `PREFIX/bin` ไว้หน้าสุดของ `PATH` | `which python` ชี้ไปที่ environment นี้ |
| `setenv("NAME", "value")` | ตั้ง environment variable เมื่อโหลด module | `echo "$HPC_MESA_ENV"` แสดง prefix ที่ถูกต้อง |

## Python, Mamba, Conda, Jupyter

| คำสั่ง | ความหมาย | หลักฐานที่ควรเห็น |
|---|---|---|
| `mamba create -p PREFIX ...` | สร้าง Conda environment ใน path ที่กำหนด | มี `PREFIX/bin/python` |
| `conda activate ENV` | เปิด environment ใน shell ปัจจุบัน | `which python` ชี้ไปที่ environment |
| `conda run -p PREFIX command` | รัน command ด้วย environment ตาม prefix | package ถูกติดตั้งใน project env |
| `python script.py` | รัน Python script | stdout/log แสดงผลลัพธ์และไฟล์ output ถูกสร้าง |
| `python -c "code"` | รัน Python สั้น ๆ จาก command line | ใช้ตรวจ import หรือ version |
| `python - <<'PY' ... PY` | ส่ง Python program ผ่าน heredoc | ใช้สร้าง smoke test ที่อ่านง่ายใน `.sbatch` |
| `python -m json.tool file` | ตรวจและ format JSON ด้วย standard library | ใช้ตรวจว่าไฟล์ `.ipynb` เป็น JSON ที่อ่านได้ |
| `python -m pip install ...` | ใช้ pip ผ่าน interpreter ที่เลือกไว้ | package เข้า environment เดียวกับ `python` |
| `python -m cProfile -s cumulative script.py` | ใช้ profiler ใน Python standard library แล้วเรียงตามเวลาสะสม | ใช้ดู call-level timing ของ script สั้นก่อนเลือกจุดปรับปรุง |
| `python -m ipykernel install --user --name NAME --display-name "..."` | ลงทะเบียน Python interpreter เป็น Jupyter kernel ของผู้ใช้ | JupyterLab เห็น kernel ชื่อที่ตั้งไว้ |
| `jupyter lab` | เปิด Jupyter server | log แสดง URL พร้อม token และ node ที่รัน |
| `jupyter kernelspec list` | แสดงรายการ kernel ที่ JupyterLab เปิดใช้ได้ | มี kernel เช่น `hpc-mesa` |
| `VAR=value command` | ตั้ง environment variable เฉพาะ command หนึ่งครั้ง | ใช้ส่ง result directory ให้ script โดยกระทบ shell ถัดไปน้อย |
| `torchrun --standalone --nproc_per_node=N script.py` | เปิด PyTorch distributed processes ในหนึ่ง node | rank, world size และ output ต่อ rank ครบ |
| `which command` | แสดง executable ที่ shell จะเรียกใช้ | ใช้ยืนยันว่า `python` หรือ `jupyter` มาจาก environment ที่ต้องการ |

สำหรับ training สด ให้ทดสอบ import package สำคัญทันที เช่น `import mesa`, `import torch`, หรือ `import netCDF4` แล้วบันทึก version ลง log

## Plot และ Visualization

| คำสั่งหรือ syntax | ความหมาย | หลักฐานที่ควรเห็น |
|---|---|---|
| `gnuplot script.gp` | รัน plot script ของ gnuplot | ได้ไฟล์รูปตาม `set output` |
| `set datafile separator "\t"` | บอก gnuplot ว่า input เป็น TSV | column ถูกอ่านตรงกับตาราง |
| `set terminal pngcairo size W,H` | กำหนด output เป็น PNG และขนาดภาพ | รูปมี resolution เหมาะกับ slide หรือ notebook |
| `set output "figures/name.png"` | กำหนดไฟล์รูปปลายทาง | มี PNG ใน folder `figures/` |
| `plot "file.tsv" using X:Y title "..."` | เลือก column X และ Y จากตารางเพื่อวาดกราฟ | แกนและ legend ตรงกับตัวชี้วัด |
| `with linespoints` | วาดเส้นพร้อม marker | เหมาะกับค่าที่เรียงตาม policy หรือ timestep |
| `with labels point` | วาดจุดพร้อม label จาก column ข้อความ | เหมาะกับ scatter ที่ต้องอ่านชื่อ policy |
| `matplotlib.use("Agg")` | ใช้ backend สำหรับสร้างรูปใน batch job | Python สร้าง PNG ได้บน compute node แบบ headless |
| `plt.savefig("figures/name.png", dpi=160)` | เขียนรูปจาก Matplotlib ลงไฟล์ | PNG มีขนาดมากกว่าศูนย์และเปิดดูได้ |

## Slurm

| คำสั่งหรือ directive | ความหมาย | หลักฐานที่ควรเห็น |
|---|---|---|
| `sbatch job.sbatch` | ส่ง batch job เข้า queue | ได้ job id |
| `sbatch --parsable` | ให้ output เป็น job id แบบอ่านง่าย | ตัวแปร `job_id` มีเลข job |
| `sbatch -A ACCOUNT` | ระบุ project account | job เข้า queue ด้วย account ที่ถูกต้อง |
| `sbatch -p compute-devel` | เลือก partition | `squeue` แสดง partition ตรงกัน |
| `squeue -j JOBID` | ดูสถานะ job | เห็น state และ reason |
| `squeue -u "$USER"` | ดู job ของผู้ใช้ปัจจุบัน | เห็น job ที่เพิ่ง submit |
| `sacct -j JOBID --format=...` | ดูประวัติและ resource หลัง job จบ | state เป็น `COMPLETED` และ exit code เป็น `0:0` |
| `scancel JOBID` | ยกเลิก job | job หายจาก queue หรือ state เป็น cancelled |
| `sinfo` | ดู partition/node status | เลือก partition ที่เปิดใช้และเหมาะกับ smoke test |
| `srun -n N command` | launch parallel tasks ภายใน allocation | MPI rank count ตรงกับ `N` |

## `#SBATCH` ในไฟล์ `.sbatch`

| Directive | ความหมาย | แนวใช้ใน repo |
|---|---|---|
| `#!/bin/bash` | shebang ระบุ interpreter ของ script | ให้ Slurm รันด้วย Bash |
| `#SBATCH --job-name=NAME` | ตั้งชื่องาน | ใช้สร้างชื่อ log ด้วย `%x` |
| `#SBATCH --partition=compute-devel` | ระบุ partition เริ่มต้น | smoke test เริ่มจาก partition สั้น |
| `#SBATCH --nodes=1` | จำนวน node | lab ส่วนใหญ่เริ่มที่หนึ่ง node |
| `#SBATCH --ntasks=4` | จำนวน task/rank | ใช้กับ MPI หรือ job ที่ต้องมีหลาย process |
| `#SBATCH --cpus-per-task=4` | CPU cores ต่อ task | ใช้กับ OpenMP หรือ Python multicore |
| `#SBATCH --gpus-per-node=1` | ขอ GPU ต่อ node | ใช้กับ PyTorch/GROMACS GPU smoke |
| `#SBATCH --mem=8G` | memory รวมของ job | เลือกตามขนาด input |
| `#SBATCH --time=00:05:00` | wall time limit | training ใช้เวลาสั้นเพื่อให้ queue หมุนเร็ว |
| `#SBATCH --array=1-12%4` | job array task 1 ถึง 12 จำกัดพร้อมกัน 4 task | ใช้รัน scenario หลายแถว |
| `#SBATCH --output=logs/%x_%j.out` | stdout log | `%x` คือ job name, `%j` คือ job id |
| `#SBATCH --error=logs/%x_%j.err` | stderr log | ใช้อ่าน error แยกจาก output |

ตัวแปร Slurm ที่พบใน repo ได้แก่ `SLURM_JOB_ID`, `SLURM_ARRAY_JOB_ID`, `SLURM_ARRAY_TASK_ID`, `SLURM_NTASKS`, `SLURM_CPUS_PER_TASK`, `SLURM_SUBMIT_DIR`, `SLURM_NODELIST`, และ `CUDA_VISIBLE_DEVICES`

## คำสั่งตรวจระบบและทรัพยากร

| คำสั่ง | ความหมาย | ใช้ตัดสินอย่างไร |
|---|---|---|
| `whoami` | แสดง user ปัจจุบัน | user ตรงกับบัญชีที่ใช้ submit |
| `hostname` | แสดงชื่อเครื่อง/node | job log ควรเป็น compute node |
| `date -Is` | เวลาแบบ ISO 8601 | ใช้ทำ timestamp ใน notes |
| `/usr/bin/time -v command` | วัดเวลา wall-clock, CPU และ memory ของ command | ใช้เทียบ run baseline, MPI และ GPU |
| `myquota` | quota ของ LANTA | พื้นที่พอสำหรับ input/result |
| `sbalance` | balance หรือ allocation | project มี resource สำหรับส่งงาน |
| `sbill` | สรุปการใช้ resource | ใช้หลัง training เพื่อดูค่าใช้จ่าย job |
| `df -h` | พื้นที่ filesystem แบบอ่านง่าย | path ที่ใช้งานมีพื้นที่เหลือ |
| `du -sh path` | ขนาด folder | result หรือ env มีขนาดสมเหตุสมผล |
| `nvidia-smi` | สถานะ GPU NVIDIA | job เห็น GPU ที่ Slurm จัดให้ |
| `which command` | path ของ executable | ตรวจว่า `python` หรือ tool มาจาก environment ที่ถูกต้อง |
| `command -v command` | ตรวจว่า shell หา command เจอ | ใช้ใน module wrapper และ preflight |

## Compiler, MPI, GPU และ Domain Tools

| คำสั่ง | ความหมาย | หลักฐานที่ควรเห็น |
|---|---|---|
| `cc file.c -o program` | compiler wrapper ของ Cray CPE | ได้ binary และ compile log จบสำเร็จ |
| `CC file.cpp -o program` | compiler wrapper สำหรับ C++ ของ Cray CPE | ได้ binary C++ ที่ link MPI ได้ |
| `srun -n "$SLURM_NTASKS" program` | รัน MPI ranks ผ่าน Slurm | log มีจำนวน rank ตรงกับ `SLURM_NTASKS` |
| `gmx --version` / `gmx mdrun` | GROMACS version และ MD run | log มี version, performance, และ output prefix |
| `pw.x -inp input.in` | Quantum ESPRESSO SCF run | output มี total energy หรือ convergence |
| `gdalinfo` / `ogrinfo` | ตรวจ raster/vector geospatial data | เห็น projection, layer, หรือ metadata |
| `blastn` / `makeblastdb` | ค้น sequence และสร้าง BLAST database | TSV hit มี `pident`, `length`, `evalue` |
| `apptainer --version` | ตรวจ container runtime | version ถูกบันทึกใน result |

## หลักฐานว่าผลลัพธ์ดีและตรวจสอบได้

งาน training ที่ดีควรมีหลักฐาน 5 ชั้น:

1. **Environment evidence**: log มี `module list`, `which python`, `command -v <tool>`, หรือ version ของ package
2. **Scheduler evidence**: `sbatch` คืน job id, `squeue` แสดง partition ที่ตั้งไว้, `sacct` จบด้วย `COMPLETED`
3. **Input evidence**: config หรือ input ที่ใช้จริงถูกเก็บใน `configs/`, `input/`, หรือ result folder ของ job
4. **Output evidence**: `results/` มีไฟล์ที่มี header, จำนวนบรรทัด, checksum, หรือ summary ที่คาดไว้
5. **Scientific evidence**: ค่า output ผ่าน sanity check ของแบบจำลอง เช่น conservation, rank count, GPU count, convergence, หรือค่าเฉลี่ยจากหลาย seed

สำหรับ agent-based simulation ให้ตรวจเพิ่มว่าใช้ seed ที่บันทึกไว้, จำนวน agent ต่อวันคงรูปตามกติกา model, และการเปรียบเทียบ policy ใช้หลาย scenario หรือหลาย seed แทนการสรุปจาก run เดียว
