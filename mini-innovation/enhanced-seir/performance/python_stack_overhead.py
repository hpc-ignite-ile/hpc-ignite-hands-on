from __future__ import annotations

import csv
import subprocess
import sys
import time
from pathlib import Path


def timed_subprocess(label: str, code: str) -> dict[str, str]:
    t0 = time.perf_counter()
    proc = subprocess.run([sys.executable, "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elapsed = time.perf_counter() - t0
    return {"case": label, "elapsed_sec": f"{elapsed:.6f}", "status": str(proc.returncode)}


def timed_loop() -> dict[str, str]:
    t0 = time.perf_counter()
    acc = 0.0
    for i in range(700000):
        acc += (i % 17) * 0.125
    elapsed = time.perf_counter() - t0
    return {"case": "pure_python_loop_700k", "elapsed_sec": f"{elapsed:.6f}", "status": f"{acc:.1f}"}


def timed_numpy() -> dict[str, str]:
    code = "import numpy as np; x=np.arange(700000,dtype=np.float64); float((x%17).sum())"
    return timed_subprocess("numpy_import_and_vector_op", code)


def main() -> None:
    Path("results").mkdir(exist_ok=True)
    rows = [
        timed_subprocess("interpreter_startup", "pass"),
        timed_subprocess("stdlib_imports", "import csv,json,math,statistics"),
        timed_subprocess("torch_import", "import torch"),
        timed_loop(),
        timed_numpy(),
    ]
    out = Path("results/python_stack_overhead.csv")
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["case", "elapsed_sec", "status"])
        writer.writeheader()
        writer.writerows(rows)
    print("wrote", out)
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
