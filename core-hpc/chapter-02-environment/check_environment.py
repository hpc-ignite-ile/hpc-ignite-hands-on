#!/usr/bin/env python3
"""
Check Environment - ตรวจสอบสภาพแวดล้อม HPC
Chapter 2: HPC Environment

ตรวจสอบ: Python, modules, environment variables, filesystem
"""

import argparse
import json
import os
import sys
import shutil
from pathlib import Path


def check_python():
    """ตรวจสอบ Python environment"""
    print("\n🐍 Python Environment:")
    print(f"   Version: {sys.version}")
    print(f"   Executable: {sys.executable}")
    print(f"   Prefix: {sys.prefix}")

    # Check if in conda environment
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "Not in conda")
    print(f"   Conda env: {conda_env}")


def check_hpc_variables():
    """ตรวจสอบ HPC environment variables"""
    print("\n📁 HPC Environment Variables:")

    hpc_vars = {
        "HOME": os.environ.get("HOME", "Not set"),
        "SCRATCH": os.environ.get("SCRATCH", "Not set"),
        "PROJECT": os.environ.get("PROJECT", "Not set"),
        "SLURM_JOB_ID": os.environ.get("SLURM_JOB_ID", "Not in SLURM job"),
        "SLURM_NODELIST": os.environ.get("SLURM_NODELIST", "N/A"),
        "SLURM_NTASKS": os.environ.get("SLURM_NTASKS", "N/A"),
    }

    for var, value in hpc_vars.items():
        print(f"   {var}: {value}")


def check_filesystem():
    """ตรวจสอบ filesystem"""
    print("\n💾 Filesystem Check:")

    paths = {
        "HOME": os.environ.get("HOME"),
        "SCRATCH": os.environ.get("SCRATCH"),
        "Current": os.getcwd(),
    }

    for name, path in paths.items():
        if path and Path(path).exists():
            total, used, free = shutil.disk_usage(path)
            print(f"   {name}: {path}")
            print(f"      Total: {total // (1024**3)} GB")
            print(f"      Used: {used // (1024**3)} GB")
            print(f"      Free: {free // (1024**3)} GB")


def check_packages():
    """ตรวจสอบ packages สำคัญ"""
    print("\n📦 Key Packages:")

    packages = ["numpy", "pandas", "torch", "mpi4py", "dask"]

    for pkg in packages:
        try:
            mod = __import__(pkg)
            version = getattr(mod, "__version__", "unknown")
            print(f"   ✅ {pkg}: {version}")
        except ImportError:
            print(f"   ❌ {pkg}: not installed")


def collect_summary():
    """Collect a machine-readable environment summary."""
    packages = {}
    for pkg in ["numpy", "pandas", "torch", "mpi4py", "dask"]:
        try:
            mod = __import__(pkg)
            packages[pkg] = getattr(mod, "__version__", "unknown")
        except ImportError:
            packages[pkg] = None

    return {
        "python": {
            "version": sys.version,
            "executable": sys.executable,
            "prefix": sys.prefix,
        },
        "env": {
            "conda_default_env": os.environ.get("CONDA_DEFAULT_ENV"),
            "home": os.environ.get("HOME"),
            "scratch": os.environ.get("SCRATCH"),
            "project": os.environ.get("PROJECT"),
            "cwd": os.getcwd(),
        },
        "slurm": {
            "job_id": os.environ.get("SLURM_JOB_ID"),
            "nodelist": os.environ.get("SLURM_NODELIST"),
            "ntasks": os.environ.get("SLURM_NTASKS"),
        },
        "packages": packages,
    }


def main():
    parser = argparse.ArgumentParser(description="Check LANTA environment")
    parser.add_argument("--write-json", help="Optional path for machine-readable summary")
    args = parser.parse_args()

    print("=" * 60)
    print("🔍 HPC Environment Check")
    print("   Chapter 2: HPC Environment and LANTA System")
    print("=" * 60)

    check_python()
    check_hpc_variables()
    check_filesystem()
    check_packages()

    if args.write_json:
        output = Path(args.write_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(collect_summary(), indent=2), encoding="utf-8")
        print(f"\nWrote JSON summary: {output}")

    print("\n" + "=" * 60)
    print("✅ Environment check complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
