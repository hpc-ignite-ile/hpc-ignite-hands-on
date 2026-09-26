"""Summarize archived benchmark runs and plot actual traces (never expected screenshots)."""
import argparse
import csv
import json
from pathlib import Path
import re
import statistics
from qualify_twinb_benchmark import equivalent, load_csv


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence", type=Path)
    p.add_argument("--compare-jobs", nargs=2, metavar=("REFERENCE", "CANDIDATE"))
    args = p.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    summaries = []
    for qualification in sorted(args.evidence.rglob("qualification.json")):
        q = json.loads(qualification.read_text())
        if not q["passed"]:
            continue
        root = qualification.parent
        stats = [json.loads((root / f"mesa-{i}/summary.json").read_text()) for i in range(3)]
        actuator_checks = []
        for i in range(3):
            with (root / f"mesa-{i}/trace.csv").open() as f:
                commanded = [r for r in csv.DictReader(f) if r["command_C"]]
            actuator_checks.append(bool(commanded) and all(
                abs(float(r["command_C"]) - float(r["cooling_setpoint_C"])) < 1e-6 for r in commanded))
        if not all(actuator_checks):
            raise ValueError(f"Mesa actuator tracking failed: {root}")
        rss = []
        for i in range(3):
            text = (root / f"mesa-{i}-time.txt").read_text()
            rss.append(int(re.search(r"Maximum resident set size \(kbytes\): (\d+)", text)[1]))
        energy = {}
        for case in ("baseline", "readonly", "reset", "fixed", "mesa-0"):
            with (root / case / "eplusout.csv").open() as f:
                rows = list(csv.DictReader(f))
            keys = [k for k in rows[0] if k.strip().startswith("Electricity:Facility [J]")]
            if len(keys) != 1:
                raise ValueError(f"expected one facility electricity meter: {root}")
            energy[case] = sum(float(r[keys[0]]) for r in rows) / 3_600_000
        summaries.append({"case": str(root.relative_to(args.evidence)), "job_id": q["job_id"],
                          "agents": stats[0]["agents"], "steps": stats[0]["steps"],
                          "median_process_wall_seconds": statistics.median(q["runs"][f"mesa-{i}"]["wall_seconds"] for i in range(3)),
                          "median_simulation_seconds": statistics.median(s["elapsed_seconds"] for s in stats),
                          "median_callback_seconds": statistics.median(s["callback_seconds"] for s in stats),
                          "max_process_RSS_KiB": max(rss), "facility_electricity_kWh": energy,
                          "warnings": stats[0]["errors"]["Warning"], "qualification_passed": True,
                          "mesa_actuator_tracks_all_three_repeats": actuator_checks})
        traces = {}
        for case in ("readonly", "fixed", "mesa-0"):
            with (root / case / "trace.csv").open() as f:
                traces[case] = list(csv.DictReader(f))
        controlled = [r["zone"] for r in traces["mesa-0"] if r["cooling_setpoint_C"]]
        zone = controlled[0]
        fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True, constrained_layout=True)
        for case, rows in traces.items():
            selected = [r for r in rows if r["zone"] == zone]
            x = [int(r["step"]) / 4 for r in selected]
            axes[0].plot(x, [float(r["temperature_C"]) for r in selected], label=case)
            axes[1].step(x, [float(r["cooling_setpoint_C"]) for r in selected], where="post", label=case)
        axes[0].set_ylabel("Zone air temperature (°C)")
        axes[1].set_ylabel("Cooling setpoint (°C)")
        axes[1].set_xlabel("Hours since run-period start")
        axes[0].set_title(f"Actual LANTA output — {root.name}, job {q['job_id']}\n{zone}")
        for ax in axes:
            ax.grid(alpha=0.25)
            ax.legend()
        fig.savefig(args.evidence / f"{q['job_id']}-{root.name}-actual-traces.png", dpi=140)
        plt.close(fig)
    (args.evidence / "performance-summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    if args.compare_jobs:
        reference, candidate = args.compare_jobs
        comparison = {"reference_job": reference, "candidate_job": candidate, "checks": {}}
        for model in ("fivezone", "school"):
            a, b = (args.evidence / job / model for job in (reference, candidate))
            for case in ("baseline", "readonly", "reset", "fixed", "mesa-small", "mesa-0", "mesa-1", "mesa-2"):
                comparison["checks"][f"{model}/{case}/timestep_outputs_equal"] = equivalent(
                    load_csv(a / case / "eplusout.csv"), load_csv(b / case / "eplusout.csv"))
            comparison["checks"][f"{model}/seeded_trace_hashes_equal"] = (
                json.loads((a / "qualification.json").read_text())["trace_sha256"] ==
                json.loads((b / "qualification.json").read_text())["trace_sha256"])
        comparison["passed"] = all(comparison["checks"].values())
        (args.evidence / "resource-comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")
        if not comparison["passed"]:
            raise ValueError("Resource optimization changed numerical outputs")
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
