"""Submit reviewed tutorial workspaces and preserve Slurm accounting receipts."""
import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["submit", "collect"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--include", default=".*")
    parser.add_argument("--retry", action="store_true", help="Resubmit selected terminal workflows, retaining old receipts")
    parser.add_argument("--variant", default="", help="Distinct receipt label for an explicitly prepared variant")
    args = parser.parse_args()
    root = args.root.resolve()
    receipt = root / "submissions.jsonl"
    previous = [json.loads(line) for line in receipt.read_text().splitlines()] if receipt.exists() else []
    if args.action == "collect":
        ids = [r["job_id"] for r in previous if r.get("job_id")]
        if not ids:
            return
        fields = "JobID,JobName%60,Account,Partition,State,ExitCode,Elapsed,ElapsedRaw,TotalCPU,UserCPU,SystemCPU,AllocCPUS,ReqCPUS,ReqMem,AllocTRES%120,MaxRSS,MaxVMSize,AveCPU,NodeList,Submit,Start,End"
        result = subprocess.run(["sacct", "-j", ",".join(ids), "-P", "-o", fields], text=True, capture_output=True, check=True)
        (root / "accounting.psv").write_text(result.stdout)
        print(result.stdout)
        return
    candidates = []
    for record in json.loads((root / "tutorials/manifest.json").read_text()):
        for job in record["jobs"]:
            cwd = root / "tutorials" / record["workspace"]
            script = str(cwd / job)
            if record["page"] == "mini-innovation/06-twinb-heatlab-repository.md":
                cwd = root / "twinb"
            candidates.append(("tutorial:" + record["page"] + ":" + job, cwd, script))
    repo = root / "repo"
    for path in sorted(repo.rglob("*.sbatch")):
        rel = path.relative_to(repo)
        if "templates" in rel.parts:
            continue
        cwd = repo
        if str(rel).startswith("foundation/chapter-00/"):
            cwd = path.parent
        if "enhanced-seir" in rel.parts or "weather-health-abs" in rel.parts:
            cwd = path.parent.parent
        candidates.append(("repo:" + str(rel), cwd, str(path)))
    done = set() if args.retry else {r["workflow"] for r in previous if r.get("job_id")}
    workspace_tail = {}
    lanes = {"cpu": [None] * 4, "gpu": [None]}
    indexes = {"cpu": 0, "gpu": 0}
    for name, cwd, job in candidates:
        if args.variant:
            name += "@" + args.variant
        if name in done or not re.search(args.include, name):
            continue
        script = Path(job) if Path(job).is_absolute() else cwd / job
        content = script.read_text()
        kind = "gpu" if re.search(r"^#SBATCH .*--gpus", content, re.M) else "cpu"
        index = indexes[kind] % len(lanes[kind])
        indexes[kind] += 1
        (cwd / "logs").mkdir(exist_ok=True)
        command = ["sbatch", "-A", args.account, "-p", "gpu-devel" if kind == "gpu" else "compute-devel", "--parsable", "--export=ALL,EPI_MODULE_ROOT=" + str(root.parent / "hpc-ignite-rerun-20260925/modulefiles")]
        dependencies = set(filter(None, (lanes[kind][index], workspace_tail.get(str(cwd)))))
        if dependencies:
            command += ["--dependency=afterany:" + ":".join(sorted(dependencies))]
        command += [job]
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
        import os
        context = {key: os.environ[key] for key in ("TWINB_EP_CONTROL", "TWINB_VENV", "ENERGYPLUS_HOME", "HPDS_ENV_PREFIX", "EPI_RESULTS", "TWINB_RESULTS") if key in os.environ}
        row = {"workflow": name, "cwd": str(cwd), "command": command, "context": context, "submitted_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "stderr": result.stderr, "job_id": result.stdout.strip().split(";")[0] if result.returncode == 0 else None}
        with receipt.open("a") as handle:
            handle.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)
        if row["job_id"]:
            lanes[kind][index] = row["job_id"]
            workspace_tail[str(cwd)] = row["job_id"]


if __name__ == "__main__":
    main()
