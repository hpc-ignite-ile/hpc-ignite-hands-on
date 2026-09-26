"""Run an isolated EnergyPlus baseline; reject severe errors even with exit code 0."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time


def error_counts(text):
    return {name: len(re.findall(r"\*\*\s*" + name + r"\s*\*\*", text, re.I))
            for name in ("Warning", "Severe", "Fatal")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--idf", type=Path, required=True)
    p.add_argument("--weather", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--timeout", type=int, default=480)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    runtime = Path(os.environ["ENERGYPLUS_HOME"])
    command = [str(runtime / "energyplus"), "-x", "-d", str(args.output.resolve()),
               "-w", str(args.weather.resolve()), str(args.idf.resolve())]
    metadata = {"command": command, "job_id": os.getenv("SLURM_JOB_ID"),
                "inputs": {str(f.resolve()): hashlib.sha256(f.read_bytes()).hexdigest()
                           for f in (args.idf, args.weather)}, "timeout_seconds": args.timeout}
    start = time.monotonic()
    with (args.output / "console.log").open("w") as log:
        try:
            result = subprocess.run(["/usr/bin/time", "-v", "-o", str(args.output / "time.txt"),
                                     "timeout", "--kill-after=10", str(args.timeout), *command],
                                    stdout=log, stderr=subprocess.STDOUT, check=False)
            metadata["returncode"] = result.returncode
        finally:
            metadata["elapsed_seconds"] = time.monotonic() - start
    errors = args.output / "eplusout.err"
    metadata["errors"] = error_counts(errors.read_text()) if errors.exists() else None
    metadata["passed"] = (metadata["returncode"] == 0 and errors.exists()
                          and metadata["errors"]["Severe"] == 0
                          and metadata["errors"]["Fatal"] == 0
                          and "EnergyPlus Completed Successfully" in errors.read_text())
    (args.output / "gate.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))
    raise SystemExit(0 if metadata["passed"] else 1)


if __name__ == "__main__":
    main()
