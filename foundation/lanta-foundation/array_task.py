#!/usr/bin/env python3
"""Parameter-sweep task for the LANTA foundation job-array demo."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

from serial_sum import estimate_pi


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one small task from a Slurm job array.")
    parser.add_argument("--task-id", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_ID", "1")))
    parser.add_argument("--task-count", type=int, default=int(os.environ.get("SLURM_ARRAY_TASK_COUNT", "1")))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    n = 50_000 * args.task_id
    pi_value = estimate_pi(n)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_id", "task_count", "n", "pi_estimate"])
        writer.writeheader()
        writer.writerow(
            {
                "task_id": args.task_id,
                "task_count": args.task_count,
                "n": n,
                "pi_estimate": f"{pi_value:.12f}",
            }
        )

    print(f"Task {args.task_id}/{args.task_count}: n={n}, pi={pi_value:.12f}")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
