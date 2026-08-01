# 00 Readiness

ใช้ก่อนส่งงานจริงเพื่อให้ผู้เรียนเห็น shell, filesystem, quota, account, module และ queue ตามลำดับใน booklet.

## Copy-Paste

```bash
mkdir -p "$HOME/lanta-experience"
cd "$HOME/lanta-experience"
mkdir -p configs input jobs logs notes results src

{
    echo "workspace=$(pwd)"
    echo "date=$(date -Is)"
    echo "user=$(whoami)"
    echo "host=$(hostname)"
    echo "home=$HOME"
} > notes/readiness.txt

{
    echo "== files =="
    find . -maxdepth 2 -type d | sort
    echo
    echo "== quota =="
    myquota 2>&1 || true
    echo
    echo "== balance =="
    sbalance 2>&1 || true
    echo
    echo "== queue =="
    squeue -u "$USER" 2>&1 || true
    echo
    echo "== modules =="
    module list 2>&1 || true
    module avail python 2>&1 | head -80 || true
} | tee notes/system-check.txt

cat > configs/run-small.env <<'EOF'
INPUT=input/sample.csv
OUTPUT=results/sample-summary.csv
WORKERS=4
MODE=small
EOF

cat notes/readiness.txt
cat configs/run-small.env
```

## Check

```bash
find notes configs -maxdepth 2 -type f | sort
tail -40 notes/system-check.txt
```
