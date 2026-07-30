#!/usr/bin/env python3
"""CPU-only baseline workload for a first Slurm job."""

from __future__ import annotations

import argparse
import math
import time


def estimate_pi(n: int) -> float:
    """Estimate pi with the midpoint rule over a quarter circle."""
    step = 1.0 / n
    total = 0.0
    for i in range(n):
        x = (i + 0.5) * step
        total += math.sqrt(1.0 - x * x)
    return 4.0 * step * total


def main() -> int:
    parser = argparse.ArgumentParser(description="Tiny CPU workload for LANTA foundation lab.")
    parser.add_argument("--n", type=int, default=200_000, help="number of integration intervals")
    args = parser.parse_args()

    start = time.perf_counter()
    pi_value = estimate_pi(args.n)
    elapsed = time.perf_counter() - start

    print("CPU baseline workload")
    print(f"n          : {args.n}")
    print(f"pi estimate: {pi_value:.12f}")
    print(f"abs error  : {abs(math.pi - pi_value):.6e}")
    print(f"elapsed sec: {elapsed:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
