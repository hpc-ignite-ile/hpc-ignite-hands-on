from __future__ import annotations

import csv
from pathlib import Path


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def latest(pattern: str) -> Path | None:
    files = sorted(Path("results").glob(pattern), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def karp_flatt(speedup: float, ranks: int) -> float:
    if ranks <= 1 or speedup <= 0:
        return 0.0
    return max(0.0, min(1.0, (1.0 / speedup - 1.0 / ranks) / (1.0 - 1.0 / ranks)))


def solver_summary(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    base = next((r for r in rows if int(r["ranks"]) == 1), rows[0])
    t1 = float(base["elapsed_sec"])
    summary = []
    notes = []
    for row in rows:
        ranks = int(row["ranks"])
        elapsed = float(row["elapsed_sec"])
        speedup = t1 / elapsed
        eff = speedup / ranks
        overhead = elapsed - t1 / ranks
        serial = karp_flatt(speedup, ranks)
        ai = float(row["arith_intensity"])
        wall = "memory bandwidth"
        if ranks > 1 and eff < 0.55:
            wall = "communication or synchronization"
        elif ai >= 1.0:
            wall = "compute throughput"
        summary.append(
            {
                "ranks": str(ranks),
                "elapsed_sec": f"{elapsed:.6f}",
                "speedup": f"{speedup:.3f}",
                "efficiency": f"{eff:.3f}",
                "overhead_sec": f"{overhead:.6f}",
                "karp_flatt_serial_fraction": f"{serial:.4f}",
                "observed_wall": wall,
            }
        )
    notes.append("Jacobi stencil has low arithmetic intensity, so memory traffic is the first roofline signal.")
    notes.append("Efficiency drop across ranks marks synchronization, halo exchange, and Allreduce overhead.")
    return summary, notes


def seir_note() -> str:
    compare = latest("seir_perf_compare.csv")
    if compare is None:
        return "Enhanced SEIR compare CSV is absent in this workspace; run TRAINING_SHEET_TH.md to connect GPU/DDP evidence."
    rows = read_rows(compare)
    engines = sorted({r.get("engine", "") for r in rows})
    return f"Enhanced SEIR compare CSV found: {compare}; engines={','.join(engines)}."


def main() -> None:
    Path("results").mkdir(exist_ok=True)
    solver_csv = latest("solver_roofline_*.csv")
    if solver_csv is None:
        raise SystemExit("run the roofline solver job first")
    rows = read_rows(solver_csv)
    summary, notes = solver_summary(rows)
    out_csv = Path("results/perf_workshop_summary.csv")
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    out_md = Path("results/perf_workshop_report.md")
    with out_md.open("w", encoding="utf-8") as handle:
        handle.write("# Performance Workshop Report\n\n")
        handle.write(f"source={solver_csv}\n\n")
        handle.write("| ranks | elapsed_sec | speedup | efficiency | overhead_sec | serial_fraction | wall |\n")
        handle.write("|---:|---:|---:|---:|---:|---:|---|\n")
        for row in summary:
            handle.write(
                f"| {row['ranks']} | {row['elapsed_sec']} | {row['speedup']} | {row['efficiency']} | "
                f"{row['overhead_sec']} | {row['karp_flatt_serial_fraction']} | {row['observed_wall']} |\n"
            )
        handle.write("\n## Interpretation\n\n")
        for note in notes:
            handle.write(f"- {note}\n")
        handle.write(f"- {seir_note()}\n")
        handle.write("- Next run decision: change one factor, then compare elapsed time, memory, and science result sanity checks.\n")
    print("wrote", out_csv)
    print("wrote", out_md)


if __name__ == "__main__":
    main()
