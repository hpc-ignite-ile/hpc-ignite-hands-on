# Data Rescue: กู้ข้อมูล CADC FITS และเตรียมข้อมูล HPDA บน LANTA

คำสั่งในหน้านี้อธิบายรวมไว้ที่ [../../docs/BASH_COMMAND_REFERENCE_TH.md](../../docs/BASH_COMMAND_REFERENCE_TH.md).

หน้านี้เป็นแบบฝึกปฏิบัติที่จบได้ในหน้าเดียว สำหรับเหตุการณ์ที่แหล่งข้อมูลใกล้หมดอายุและการติดต่อจาก LANTA ไปยังปลายทางหมดเวลา กรณีศึกษาคือ CADC FITS URL ขนาดประมาณ 1.59 GB

URL อ้างอิงของผู้ให้บริการ: [CADC Direct Data Service](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/doc/data/)

## บทนำแบบ Verse

เมื่อเห็นการหมดเวลา ให้แยกชั้นการสื่อสารก่อนตัดสิน<br>
DNS, TCP, HTTP header, ช่วงไบต์ และอัตรารับข้อมูล คือหลักฐานคนละชั้น<br>
เมื่อคลัสเตอร์ออกไปยังปลายทางติดทาง ให้พักข้อมูลจากเครือข่ายที่เข้าถึงได้<br>
ให้ไฟล์ทุกชิ้นเดินทางพร้อม `.part`, checksum, manifest และบันทึกการตรวจรับ<br>
ส่งเข้า LANTA ด้วย `rsync` ที่ดาวน์โหลดต่อจากไฟล์ค้างได้ แล้วให้ Slurm อ่านข้อมูลจากพื้นที่พัก<br>
งาน HPDS ที่ดีมีเส้นทางข้อมูลชัด มีหลักฐานขนาดไฟล์ มีรอยประทับของไฟล์ และมีการตรวจความสมเหตุสมผลก่อนแบบจำลองอ่านข้อมูล

## สรุปทางแก้ที่เร็วสำหรับกรณี Chaipat

จากการทดสอบวันที่ 2026-08-07:

| จุดทดสอบ | ผล |
|---|---|
| เครื่องนอก LANTA | `curl -I -L` ได้ `HTTP 200`, `content-length=1706276160` |
| เครื่องนอก LANTA | `curl --range 0-1048575` ได้ `HTTP 206` และรับ 1 MiB สำเร็จ |
| LANTA login/transfer endpoint | `curl` ไป CADC port 443 ได้ `curl: (28)` และ `http=000` |
| LANTA ไป NASA POWER | `HTTP 200` |

ข้อสรุปเชิงปฏิบัติ: กรณีนี้เป็นปัญหาเส้นทางจาก LANTA ไป CADC เฉพาะปลายทางหรือเฉพาะเส้นทางเครือข่าย วิธีที่ใช้เวลาน้อยสุดคือดาวน์โหลดจากเครื่องผู้ใช้ เครื่องห้องปฏิบัติการ หรือ cloud VM ที่ CADC เปิดทาง แล้วส่งเข้า LANTA ด้วย `rsync --partial --append-verify`

## หลักตัดสินใจ

| อาการ | การกระทำที่เหมาะ |
|---|---|
| เครื่องผู้ใช้ได้ `200/206`, LANTA ได้ `http=000` | พักข้อมูลนอกคลัสเตอร์ แล้วส่งเข้า LANTA ด้วย SSH transfer |
| ได้ `401` | ใช้ CADC login/certificate/token ตามสิทธิ์ของ dataset |
| ได้ `403` | ตรวจสิทธิ์ dataset และขอ CADC support ช่วยดู policy หรือ whitelist |
| ได้ `404` | ตรวจ URL, archive name, filename และวันหมดอายุ |
| อัตรารับข้อมูลตกต่อเนื่อง | ใช้ `.part`, `curl -C -`, `--speed-time`, `--speed-limit`, retry แบบสุภาพ |
| มีไฟล์จำนวนมาก | รวมเป็น `tar`/`zip` ก่อนส่ง ลดภาระ inode และข้อมูลกำกับไฟล์ |

## แนวแก้ในโค้ดที่ใช้ `urllib.request`

โค้ดตัวอย่างมีโครงดีอยู่แล้ว: มี manifest, checksum, การตรวจ FITS และวาง `src` ลง `sys.path` จากตำแหน่ง repo แต่ส่วนดาวน์โหลดพื้นฐานควรเสริม 5 เรื่อง

1. ตั้งเวลาเชื่อมต่อและเวลาอ่านข้อมูลให้ชัดเจน
2. ส่ง `User-Agent` ที่มีชื่อโครงการและช่องทางติดต่อ
3. เขียนลง `.part` แล้วค่อย rename เมื่อครบ
4. ดาวน์โหลดต่อจากไฟล์ค้างด้วย `Range` หรือเรียก `curl -C -` จาก Python
5. บันทึก HTTP status, จำนวนไบต์, checksum และชนิดข้อผิดพลาดลง manifest/log

สำหรับเวลาจำกัด วิธีที่เสถียรสุดคือให้ Python เป็นตัวควบคุมงาน และให้ `curl` ทำหน้าที่ย้ายข้อมูล:

```python
import subprocess
from pathlib import Path

USER_AGENT = "m81-group-stellar-map/0.2 (contact: chaipat_ja@cmu.ac.th)"

def fetch_with_curl(url: str, outfile: Path) -> None:
    part = outfile.with_suffix(outfile.suffix + ".part")
    cmd = [
        "curl", "-fL", "-C", "-",
        "--retry", "8", "--retry-delay", "10", "--retry-all-errors",
        "--connect-timeout", "30",
        "--speed-time", "120", "--speed-limit", "1024",
        "-A", USER_AGENT,
        "-o", str(part),
        url,
    ]
    subprocess.run(cmd, check=True)
    part.replace(outfile)
```

หลัง `fetch_with_curl` จบ ให้ใช้ `check_fits(outfile)`, `sha256sum`, และ manifest เดิมของโครงการต่อได้ทันที

ผู้ใช้ที่คัดลอก repo ไว้อ้างอิงสามารถดูตัวช่วยขนาดเล็กได้ที่ `src/cadc_resumable_fetch.py` โค้ดนั้นใช้แนวเดียวกันคือทดสอบปลายทางก่อน ดาวน์โหลดเมื่อระบุ `--download` แล้วเขียน manifest กับ checksum หลังไฟล์เต็มผ่านการตรวจความสมเหตุสมผลของ FITS

## Copy-Paste บนเครื่องผู้ใช้หรือ WSL

### ขั้นที่ 1: ตั้งค่า URL และทดสอบจากเครือข่ายของเครื่องผู้ใช้

คำสั่งชุดนี้ตรวจว่าเครื่องผู้ใช้เห็นข้อมูลกำกับไฟล์และรับช่วงไบต์แรกได้

```bash
export CADC_URL='https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHTSG/G006.149.683%2B68.863.G.fits'
export CADC_FILE='G006.149.683+68.863.G.fits'
export CADC_USER_AGENT='m81-group-stellar-map/0.2 (contact: chaipat_ja@cmu.ac.th)'
export CADC_LOCAL_ROOT="${CADC_LOCAL_ROOT:-$HOME/cadc-rescue}"
mkdir -p "$CADC_LOCAL_ROOT"/{raw,logs,manifest}
cd "$CADC_LOCAL_ROOT"
curl -I -L --connect-timeout 20 --max-time 60 \
    -A "$CADC_USER_AGENT" "$CADC_URL" | tee logs/cadc_head.txt
curl -L --fail --range 0-1048575 --connect-timeout 20 --max-time 90 \
    -A "$CADC_USER_AGENT" -o raw/range_probe.bin \
    -w 'http=%{http_code} bytes=%{size_download} speed=%{speed_download} remote_ip=%{remote_ip}\n' \
    "$CADC_URL" | tee logs/cadc_range_status.txt
if [ -s raw/range_probe.bin ]; then
    ls -lh raw/range_probe.bin
else
    echo "range_probe=empty_or_failed"
fi
```

### ขั้นที่ 2: ดาวน์โหลดไฟล์เต็มแบบต่อจากไฟล์ค้างได้

คำสั่งชุดนี้ใช้ `.part` เป็นไฟล์พัก และใช้ `curl -C -` เพื่อดาวน์โหลดต่อจากไบต์ที่มีอยู่

```bash
cd "$CADC_LOCAL_ROOT"
curl -L --fail -C - --retry 8 --retry-delay 10 --retry-all-errors \
    --connect-timeout 30 --max-time 0 \
    --speed-time 120 --speed-limit 1024 \
    -A "$CADC_USER_AGENT" \
    -o "raw/${CADC_FILE}.part" "$CADC_URL"
mv "raw/${CADC_FILE}.part" "raw/${CADC_FILE}"
ls -lh "raw/${CADC_FILE}"
```

### ขั้นที่ 3: ตรวจ FITS header, checksum และ manifest

คำสั่งชุดนี้ตรวจ header 2880 ไบต์แรกของ FITS และสร้าง manifest ที่อ่านซ้ำได้บน LANTA

```bash
cd "$CADC_LOCAL_ROOT"
PYTHON_BIN="$(command -v python3 || command -v python)"
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import csv, datetime as dt, hashlib, os

root = Path.cwd()
path = root / "raw" / os.environ["CADC_FILE"]
url = os.environ["CADC_URL"]
head = path.read_bytes()[:2880]
first_card = head[:80].decode("ascii", "replace").rstrip()
if first_card[:9] not in {"SIMPLE  =", "XTENSION="}:
    raise SystemExit("FITS_HEADER_CHECK_FAILED")
h = hashlib.sha256()
with path.open("rb") as f:
    for block in iter(lambda: f.read(1024 * 1024), b""):
        h.update(block)
digest = h.hexdigest()
(root / "manifest").mkdir(exist_ok=True)
with (root / "manifest" / f"{path.name}.sha256").open("w", encoding="utf-8") as f:
    f.write(f"{digest}  raw/{path.name}\n")
with (root / "manifest" / "cadc_manifest.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["dataset_id","source_org","url","access_utc","path","bytes","sha256","first_card"])
    w.writerow(["cadc_cfhtsg_g006","CADC",url,dt.datetime.now(dt.timezone.utc).isoformat(),
                f"raw/{path.name}",path.stat().st_size,digest,first_card])
print("bytes", path.stat().st_size)
print("sha256", digest)
print("first_card", first_card)
PY
sed -n '1,5p' manifest/cadc_manifest.csv
```

### ขั้นที่ 4: ส่งชุดไฟล์กู้ข้อมูลเข้า LANTA ด้วย `rsync`

คำสั่งชุดนี้ส่งทั้งไฟล์ดิบ บันทึกงาน และ manifest เข้า home directory บน LANTA

```bash
rsync -avP --partial --append-verify "$CADC_LOCAL_ROOT"/ \
    <lanta-username>@lanta.nstda.or.th:~/cadc-rescue/
```

ถ้าใช้พื้นที่โครงการ ให้เปลี่ยนปลายทางเป็นเส้นทางที่ทีมมีสิทธิ์ เช่น `/project/<project-id>/users/<username>/data/cadc-rescue/`

## Copy-Paste บน LANTA

### ขั้นที่ 5: เข้าสู่ LANTA

คำสั่งชุดนี้เปิดเชลล์บนเครื่องเข้าใช้งานของ LANTA

```bash
ssh <lanta-username>@lanta.nstda.or.th
```

### ขั้นที่ 6: ทดสอบ CADC จาก LANTA เพื่อเก็บหลักฐาน

คำสั่งชุดนี้เก็บหลักฐานว่า LANTA เห็น DNS ทดสอบ CADC และทดสอบ endpoint สาธารณะอีกแห่งเพื่อเปรียบเทียบ

```bash
export CADC_URL='https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/data/pub/CFHTSG/G006.149.683%2B68.863.G.fits'
export CADC_USER_AGENT='m81-group-stellar-map/0.2 (contact: chaipat_ja@cmu.ac.th)'
export CADC_RESCUE_ROOT="${CADC_RESCUE_ROOT:-$HOME/cadc-rescue}"
mkdir -p "$CADC_RESCUE_ROOT"/logs
cd "$CADC_RESCUE_ROOT"
{
    echo "date=$(date -Is)"
    echo "host=$(hostname)"
    echo "dns"
    getent ahosts ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca
    echo "cadc_range_probe"
    curl -L --fail --range 0-1048575 --connect-timeout 30 --max-time 75 \
        -A "$CADC_USER_AGENT" -o /dev/null \
        -w 'http=%{http_code} bytes=%{size_download} remote_ip=%{remote_ip} local_ip=%{local_ip}\n' \
        "$CADC_URL"
    echo "nasa_https_probe"
    curl -I -L --connect-timeout 20 --max-time 50 -o /dev/null \
        -w 'http=%{http_code} remote_ip=%{remote_ip} local_ip=%{local_ip}\n' \
        https://power.larc.nasa.gov
} > logs/lanta_cadc_probe.txt 2>&1 || true
sed -n '1,120p' logs/lanta_cadc_probe.txt
```

### ขั้นที่ 7: ตรวจไฟล์ที่ส่งเข้ามา

คำสั่งชุดนี้ตรวจ checksum, FITS header และ manifest ที่มากับชุดไฟล์

```bash
export CADC_FILE='G006.149.683+68.863.G.fits'
export CADC_RESCUE_ROOT="${CADC_RESCUE_ROOT:-$HOME/cadc-rescue}"
cd "$CADC_RESCUE_ROOT"
sha256sum -c "manifest/${CADC_FILE}.sha256"
PYTHON_BIN="$(command -v python3 || command -v python)"
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
import os

path = Path("raw") / os.environ["CADC_FILE"]
head = path.read_bytes()[:2880]
first_card = head[:80].decode("ascii", "replace").rstrip()
if first_card[:9] not in {"SIMPLE  =", "XTENSION="}:
    raise SystemExit("FITS_HEADER_CHECK_FAILED")
print("bytes", path.stat().st_size)
print("first_card", first_card)
PY
sed -n '1,5p' manifest/cadc_manifest.csv
```

### ขั้นที่ 8: พักข้อมูลไปยัง project หรือ scratch

คำสั่งชุดนี้แยกไฟล์ดิบออกจากพื้นที่ฝึก และเตรียมเส้นทางให้คำสั่งในงาน Slurm อ่านบน LANTA

```bash
export PROJECT_ID="${PROJECT_ID:-tn999996-north}"
export CADC_RESCUE_ROOT="${CADC_RESCUE_ROOT:-$HOME/cadc-rescue}"
export CADC_STAGE="${CADC_STAGE:-/project/${PROJECT_ID}/users/$USER/data/cadc_cfhtsg}"
mkdir -p "$CADC_STAGE"/{raw,manifest,logs}
rsync -avP --partial --append-verify "$CADC_RESCUE_ROOT/raw/" "$CADC_STAGE/raw/"
rsync -avP --partial --append-verify "$CADC_RESCUE_ROOT/manifest/" "$CADC_STAGE/manifest/"
rsync -avP --partial "$CADC_RESCUE_ROOT/logs/" "$CADC_STAGE/logs/"
find "$CADC_STAGE" -maxdepth 2 -type f -print
```

## รายการตรวจรับผล

- `logs/cadc_head.txt` หรือ `logs/lanta_cadc_probe.txt` ระบุ HTTP status หรือ error class ชัด
- `manifest/cadc_manifest.csv` มี URL, เวลาเข้าถึง, path, bytes, sha256 และ first FITS card
- `sha256sum -c` ผ่านบน LANTA
- FITS first card เป็น `SIMPLE  =` หรือ `XTENSION=`
- ไฟล์ดิบอยู่ใน `/project/<project-id>/...` หรือเส้นทางพักข้อมูลที่ทีมเลือก
- งาน Slurm อ่านจากเส้นทางพักข้อมูล และบันทึกเส้นทางนั้นลงในสภาพแวดล้อมหรือบันทึกผลลัพธ์

## แนวเสริมใน HPDS Weather-Health ABS

ให้เพิ่มขั้น “คัดกรองแหล่งข้อมูล” ก่อนดาวน์โหลดทุกครั้ง:

1. `HEAD` เพื่อดูขนาดไฟล์และสิทธิ์เข้าถึง
2. `Range` 1 MiB เพื่อดูว่าปลายทางส่งไบต์จริง
3. `curl -C -` เพื่อรองรับ network หลุด
4. checksum/manifest ก่อนแตก archive หรือแปลงรูปแบบไฟล์
5. ย้ายไฟล์ดิบไปพื้นที่โครงการ และแปลงเป็นรูปแบบสำหรับวิเคราะห์บน `/scratch`

แนวนี้ใช้กับ CADC FITS, ERA5/NetCDF, GeoTIFF, Parquet และ archive ขนาดใหญ่ได้เหมือนกัน
