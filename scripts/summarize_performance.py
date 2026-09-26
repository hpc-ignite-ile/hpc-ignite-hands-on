#!/usr/bin/env python3
"""Summarize repeated HPC Ignite performance measurements using the stdlib."""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


FIELDS = {
    "workflow",
    "variant",
    "repeat",
    "problem_size",
    "cpus",
    "gpus",
    "elapsed_s",
    "throughput",
    "result_digest",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=Path("performance_summary.csv"))
    return parser.parse_args()


def resource_units(row: dict[str, str]) -> float:
    gpus = float(row["gpus"])
    return gpus if gpus > 0 else max(1.0, float(row["cpus"]))


def main() -> None:
    args = parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = FIELDS.difference(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"missing columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["workflow"], row["problem_size"], row["variant"])].append(row)

    baselines: dict[tuple[str, str], tuple[float, float]] = {}
    for (workflow, problem_size, _variant), group in groups.items():
        elapsed = statistics.mean(float(row["elapsed_s"]) for row in group)
        units = resource_units(group[0])
        key = (workflow, problem_size)
        if key not in baselines or units < baselines[key][1]:
            baselines[key] = (elapsed, units)

    output_rows = []
    for (workflow, problem_size, variant), group in sorted(groups.items()):
        elapsed_values = [float(row["elapsed_s"]) for row in group]
        throughput_values = [float(row["throughput"]) for row in group]
        digests = {row["result_digest"] for row in group}
        units = resource_units(group[0])
        baseline_elapsed, baseline_units = baselines[(workflow, problem_size)]
        mean_elapsed = statistics.mean(elapsed_values)
        speedup = baseline_elapsed / mean_elapsed
        efficiency = speedup / (units / baseline_units)
        output_rows.append(
            {
                "workflow": workflow,
                "problem_size": problem_size,
                "variant": variant,
                "repeats": len(group),
                "cpus": group[0]["cpus"],
                "gpus": group[0]["gpus"],
                "mean_elapsed_s": f"{mean_elapsed:.6f}",
                "stdev_elapsed_s": f"{statistics.stdev(elapsed_values) if len(group) > 1 else 0.0:.6f}",
                "mean_throughput": f"{statistics.mean(throughput_values):.6f}",
                "speedup": f"{speedup:.6f}",
                "parallel_efficiency": f"{efficiency:.6f}",
                "result_consistent": str(len(digests) == 1).lower(),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_rows[0].keys() if output_rows else [])
        if output_rows:
            writer.writeheader()
            writer.writerows(output_rows)
    print(f"wrote {len(output_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
