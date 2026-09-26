"""Fail-fast CLI/API/control/repeat qualification; each simulation is a fresh process."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time


def load_csv(path):
    with path.open() as f:
        return list(csv.reader(f))


def equivalent(a, b, tolerance=1e-7):
    if len(a) != len(b) or a[0] != b[0]:
        return False
    for left, right in zip(a[1:], b[1:]):
        if len(left) != len(right):
            return False
        for x, y in zip(left, right):
            if x == y:
                continue
            try:
                if not math.isclose(float(x), float(y), rel_tol=tolerance, abs_tol=tolerance):
                    return False
            except ValueError:
                return False
    return True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--weather", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--agents", type=int, required=True)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    scripts = Path(__file__).resolve().parent
    report = {"job_id": os.getenv("SLURM_JOB_ID"), "passed": False, "checks": {}, "runs": {}}
    def execute(name, command):
        with (args.output / f"{name}.log").open("w") as log:
            start = time.monotonic()
            result = subprocess.run(["/usr/bin/time", "-v", "-o", str(args.output / f"{name}-time.txt"),
                "timeout", "--kill-after=10", "480", *command], stdout=log, stderr=subprocess.STDOUT)
            report["runs"][name] = {"returncode": result.returncode, "wall_seconds": time.monotonic() - start}
            if result.returncode:
                raise RuntimeError(f"{name} failed ({result.returncode}); inspect log")
    try:
        execute("baseline", [sys.executable, str(scripts / "twinb_baseline_gate.py"), "--idf",
                str(args.model / "model.idf"), "--weather", str(args.weather), "--output", str(args.output / "baseline")])
        baseline = load_csv(args.output / "baseline/eplusout.csv")
        expected = json.loads((args.model / "model.json").read_text())["expected_steps"]
        report["checks"]["baseline_rows"] = len(baseline) - 1 == expected
        if not report["checks"]["baseline_rows"]:
            raise RuntimeError("unexpected baseline CSV row count")
        cases = [("readonly", "readonly", 1), ("reset", "reset", 1), ("fixed", "fixed", 1),
                 ("mesa-small", "mesa", 5), *[(f"mesa-{i}", "mesa", args.agents) for i in range(3)]]
        for name, mode, count in cases:
            execute(name, [sys.executable, str(scripts / "twinb_sync_adapter.py"), "--model", str(args.model),
                   "--weather", str(args.weather), "--output", str(args.output / name), "--mode", mode,
                   "--agents", str(count)])
            if mode in ("readonly", "reset"):
                report["checks"][f"{mode}_equals_cli"] = equivalent(baseline, load_csv(args.output / name / "eplusout.csv"))
                if not report["checks"][f"{mode}_equals_cli"]:
                    raise RuntimeError(f"{mode} differs from CLI baseline")
            if mode == "fixed":
                with (args.output / name / "trace.csv").open() as f:
                    trace = list(csv.DictReader(f))
                commanded = [r for r in trace if r["command_C"]]
                report["checks"]["fixed_actuator_tracks_26C"] = bool(commanded) and all(
                    abs(float(r["cooling_setpoint_C"]) - 26) < 1e-6 for r in commanded)
                report["checks"]["fixed_changes_output"] = not equivalent(baseline, load_csv(args.output / name / "eplusout.csv"))
                with (args.output / "readonly/trace.csv").open() as f:
                    native = {(r["step"], r["zone"]): r for r in csv.DictReader(f)}
                released = [r for r in trace if not r["command_C"] and r["cooling_setpoint_C"] and int(r["hour"]) >= 13]
                report["checks"]["release_restores_native_setpoints"] = bool(released) and all(
                    abs(float(r["cooling_setpoint_C"]) - float(native[r["step"], r["zone"]]["cooling_setpoint_C"])) < 1e-6 for r in released)
                if not all(report["checks"].values()):
                    raise RuntimeError("fixed/reset intervention failed")
        hashes = [hashlib.sha256((args.output / f"mesa-{i}/trace.csv").read_bytes()).hexdigest() for i in range(3)]
        report["checks"]["three_seeded_traces_identical"] = len(set(hashes)) == 1
        report["trace_sha256"] = hashes
        report["checks"]["mesa_exercises_actuator"] = json.loads((args.output / "mesa-0/summary.json").read_text())["set_calls"] > 0
        report["passed"] = all(report["checks"].values())
    except Exception as error:
        report["failure"] = str(error)
    finally:
        (args.output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
