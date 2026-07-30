#!/usr/bin/env python3
"""Small LANTA smoke test for the HPC Ignite foundation lab."""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path


SLURM_KEYS = [
    "SLURM_JOB_ID",
    "SLURM_JOB_NAME",
    "SLURM_SUBMIT_DIR",
    "SLURM_NODELIST",
    "SLURM_NTASKS",
    "SLURM_CPUS_PER_TASK",
    "SLURM_MEM_PER_NODE",
    "SLURM_JOB_PARTITION",
    "SLURM_JOB_ACCOUNT",
]


def collect_info() -> dict[str, object]:
    hostname = socket.gethostname()
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hostname": hostname,
        "looks_like_lanta": hostname.startswith("x") or "lanta" in hostname.lower(),
        "platform": platform.platform(),
        "python": {
            "executable": sys.executable,
            "version": platform.python_version(),
        },
        "user": os.environ.get("USER", "unknown"),
        "working_directory": str(Path.cwd()),
        "slurm": {key: os.environ.get(key, "N/A") for key in SLURM_KEYS},
    }


def print_report(info: dict[str, object]) -> None:
    print("=" * 72)
    print("HPC Ignite: LANTA Foundation Smoke Test")
    print("=" * 72)
    print(f"เวลา UTC        : {info['timestamp_utc']}")
    print(f"โฮสต์           : {info['hostname']}")
    print(f"ผู้ใช้          : {info['user']}")
    print(f"Python          : {info['python']['version']} ({info['python']['executable']})")
    print(f"Working dir     : {info['working_directory']}")
    print(f"ดูเหมือน LANTA  : {info['looks_like_lanta']}")
    print("\nSlurm environment:")
    for key, value in info["slurm"].items():
        print(f"  {key:22s} {value}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a small LANTA Slurm job.")
    parser.add_argument("--write-json", type=Path, help="write collected system info to JSON")
    args = parser.parse_args()

    info = collect_info()
    print_report(info)

    if args.write_json:
        args.write_json.parent.mkdir(parents=True, exist_ok=True)
        args.write_json.write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote JSON report: {args.write_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
