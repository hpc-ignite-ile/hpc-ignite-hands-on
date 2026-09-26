"""Extract literal teaching heredocs into isolated per-page workspaces.

Does not execute shell commands or expand variables. Review the manifest and
prepare external dependencies before submitting any extracted job.
"""
import argparse
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    records = []
    for section in ("foundation", "core-hpc", "ai-applications", "domain-science", "lanta-experience", "mini-innovation"):
        for page in sorted((root / section).rglob("*.md")):
            relative = page.relative_to(root)
            workspace = args.destination / relative.with_suffix("")
            files = []
            for block in re.findall(r"```bash\n(.*?)\n```", page.read_text(), re.S):
                lines = block.splitlines(keepends=True)
                i = 0
                while i < len(lines):
                    match = re.match(r"^cat (>>?) ([^\s]+) <<['\"]?(\w+)['\"]?\s*$", lines[i])
                    i += 1
                    if not match:
                        continue
                    mode, name, delimiter = match.groups()
                    body = []
                    while i < len(lines) and lines[i].strip() != delimiter:
                        body.append(lines[i])
                        i += 1
                    i += 1
                    name = name.strip("\"'")
                    path = Path(name)
                    if "$" in name or path.is_absolute() or ".." in path.parts:
                        continue
                    target = workspace / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("a" if mode == ">>" else "w") as handle:
                        handle.write("".join(body))
                    files.append(name)
            if files:
                for folder in ("logs", "results", "notes", "figures", "input", "data", "build"):
                    (workspace / folder).mkdir(exist_ok=True)
                records.append({"page": str(relative), "workspace": str(relative.with_suffix("")), "files": sorted(set(files)), "jobs": sorted(set(f for f in files if f.endswith(".sbatch")))})
    args.destination.mkdir(parents=True, exist_ok=True)
    (args.destination / "manifest.json").write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps({"pages": len(records), "jobs": sum(len(r["jobs"]) for r in records)}, indent=2))


if __name__ == "__main__":
    main()
