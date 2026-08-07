#!/usr/bin/env python3
"""Resumable public-data fetch helper for HPDS rescue workflows."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import subprocess
from pathlib import Path


def run(cmd: list[str], log_path: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fits_first_card(path: Path) -> str:
    card = path.read_bytes()[:80].decode("ascii", "replace").rstrip()
    if card[:9] not in {"SIMPLE  =", "XTENSION="}:
        raise SystemExit("FITS_HEADER_CHECK_FAILED")
    return card


def curl_base(args: argparse.Namespace) -> list[str]:
    return [
        "curl",
        "-L",
        "--connect-timeout",
        str(args.connect_timeout),
        "--max-time",
        str(args.max_time),
        "-A",
        args.user_agent,
    ]


def write_manifest(args: argparse.Namespace, digest: str, first_card: str) -> None:
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["dataset_id", "source_org", "url", "access_utc", "path", "bytes", "sha256", "first_card"])
        writer.writerow(
            [
                args.dataset_id,
                "CADC",
                args.url,
                dt.datetime.now(dt.timezone.utc).isoformat(),
                str(args.outfile),
                args.outfile.stat().st_size,
                digest,
                first_card,
            ]
        )
    args.manifest.with_suffix(".sha256").write_text(f"{digest}  {args.outfile}\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("outfile", type=Path)
    parser.add_argument("--dataset-id", default="cadc_dataset")
    parser.add_argument("--manifest", type=Path, default=Path("manifest/cadc_manifest.csv"))
    parser.add_argument("--user-agent", default="hpc-ignite-hpds/0.1 (contact: training)")
    parser.add_argument("--connect-timeout", type=int, default=30)
    parser.add_argument("--max-time", type=int, default=0)
    parser.add_argument("--probe-bytes", type=int, default=1048576)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    args.outfile.parent.mkdir(parents=True, exist_ok=True)
    probe = args.outfile.with_suffix(args.outfile.suffix + ".probe")
    run(
        curl_base(args)
        + [
            "--fail",
            "--range",
            f"0-{args.probe_bytes - 1}",
            "-o",
            str(probe),
            "-w",
            "http=%{http_code} bytes=%{size_download} speed=%{speed_download}\\n",
            args.url,
        ],
        args.manifest.with_name("cadc_range_probe.log"),
    )
    print(f"probe_bytes={probe.stat().st_size}")

    if args.download:
        part = args.outfile.with_suffix(args.outfile.suffix + ".part")
        run(
            curl_base(args)
            + [
                "--fail",
                "-C",
                "-",
                "--retry",
                "8",
                "--retry-delay",
                "10",
                "--retry-all-errors",
                "--speed-time",
                "120",
                "--speed-limit",
                "1024",
                "-o",
                str(part),
                args.url,
            ],
            args.manifest.with_name("cadc_download.log"),
        )
        part.replace(args.outfile)
        digest = sha256_file(args.outfile)
        first_card = fits_first_card(args.outfile)
        write_manifest(args, digest, first_card)
        print(f"downloaded={args.outfile}")
        print(f"sha256={digest}")


if __name__ == "__main__":
    main()
