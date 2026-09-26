#!/usr/bin/env python3
"""Check or migrate a disposable Twin-B checkout from Mesa 2 to Mesa 3.5.1."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TRANSFORMS = (
    (r"^from mesa\.time import RandomActivation\s*\n", ""),
    (r"^([ \t]*)self\.schedule = RandomActivation\(self\)\s*\n", ""),
    (r"^([ \t]*)self\.schedule\.add\(agent\)\s*\n", ""),
    (r"self\.schedule\.agents", "self.agents"),
    (r"self\.schedule\.step\(\)", 'self.agents.shuffle_do("step")'),
    (r"super\(\)\.__init__\(unique_id, model\)", "super().__init__(model)"),
)


def migrate_text(text: str) -> str:
    for pattern, replacement in TRANSFORMS:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--apply", action="store_true", help="write changes to the disposable checkout")
    args = parser.parse_args()

    root = args.repo.resolve()
    targets = [root / "agent.py", root / "model.py", root / "requirements.txt"]
    missing = [str(path) for path in targets if not path.exists()]
    if missing:
        raise SystemExit(f"missing Twin-B files: {', '.join(missing)}")

    changed = []
    for path in targets:
        before = path.read_text(encoding="utf-8")
        if path.name == "requirements.txt":
            after = re.sub(r"^mesa[^\n]*$", "mesa==3.5.1", before, flags=re.MULTILINE)
        else:
            after = migrate_text(before)
        if before != after:
            changed.append(path)
            if args.apply:
                path.write_text(after, encoding="utf-8")

    mode = "applied" if args.apply else "would-change"
    for path in changed:
        print(f"{mode}: {path.relative_to(root)}")
    if not changed:
        print("no changes needed")

    if args.apply:
        active = "\n".join((root / name).read_text(encoding="utf-8") for name in ("agent.py", "model.py"))
        markers = [marker for marker in ("from mesa.time", "RandomActivation(self)", "self.schedule.agents", "self.schedule.step()") if marker in active]
        if markers:
            raise SystemExit(f"legacy Mesa markers remain: {', '.join(markers)}")


if __name__ == "__main__":
    main()
