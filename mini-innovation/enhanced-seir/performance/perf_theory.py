from __future__ import annotations

import csv
from pathlib import Path


def main() -> None:
    Path("results").mkdir(exist_ok=True)
    workers = [1, 2, 4, 8, 16, 32]
    serial_fractions = [0.02, 0.08, 0.18]
    rows = []
    for f_serial in serial_fractions:
        for p in workers:
            amdahl = 1.0 / (f_serial + (1.0 - f_serial) / p)
            gustafson = p - f_serial * (p - 1)
            rows.append(
                {
                    "workers": p,
                    "serial_fraction": f"{f_serial:.2f}",
                    "amdahl_speedup": f"{amdahl:.4f}",
                    "gustafson_speedup": f"{gustafson:.4f}",
                    "parallel_efficiency": f"{amdahl / p:.4f}",
                }
            )

    out = Path("results/amdahl_gustafson.csv")
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    taxonomy = [
        ("startup", "Python import, torchrun, MPI initialization", "measure with /usr/bin/time -v"),
        ("scheduler", "queue wait and allocation size", "capture sbatch id, squeue, sacct"),
        ("communication", "halo exchange, Allreduce, gather", "compare ranks and min/max timing"),
        ("memory", "low arithmetic intensity or high MaxRSS", "estimate bytes moved and residual"),
        ("gpu", "kernel launch, data movement, small batch", "compare GPU elapsed with CPU baseline"),
        ("io", "many files, metadata, checkpoint", "count files and check File system outputs"),
        ("python_stack", "interpreter startup, imports, pure Python loop", "measure startup and cProfile"),
    ]
    with Path("results/overhead_taxonomy.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["class", "typical_source", "evidence"])
        writer.writerows(taxonomy)

    print("wrote", out)
    for row in rows[:6]:
        print(row)
    print("wrote results/overhead_taxonomy.csv")


if __name__ == "__main__":
    main()
