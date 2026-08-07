from __future__ import annotations

import argparse
import csv
import hashlib
import math
from pathlib import Path

import pandas as pd


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_locations(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalise_power_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"YEAR", "MO", "DY", "HR", "T2M", "RH2M", "ALLSKY_SFC_SW_DWN", "WS10M"}
    missing = sorted(required.difference(df.columns))
    if missing:
        raise ValueError(f"missing NASA POWER columns: {missing}")
    df["timestamp"] = pd.to_datetime(
        {
            "year": df["YEAR"],
            "month": df["MO"],
            "day": df["DY"],
            "hour": df["HR"],
        },
        utc=True,
    )
    return df[["timestamp", "T2M", "RH2M", "ALLSKY_SFC_SW_DWN", "WS10M"]].rename(
        columns={
            "T2M": "temp_c",
            "RH2M": "rh_pct",
            "ALLSKY_SFC_SW_DWN": "solar_w_m2",
            "WS10M": "wind_m_s",
        }
    )


def write_staged_files(weather: pd.DataFrame, locations: list[dict[str, str]], out_dir: Path) -> list[dict[str, str]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for idx, loc in enumerate(locations):
        shifted = weather.copy()
        lat = float(loc["lat"])
        lon = float(loc["lon"])
        location_shift = (lat - 13.75) * 0.18 + (lon - 100.5) * 0.04
        hour_angle = shifted["timestamp"].dt.hour * math.pi / 12.0
        shifted["temp_c"] = shifted["temp_c"] + location_shift + 0.6 * hour_angle.map(math.sin)
        shifted["rh_pct"] = (shifted["rh_pct"] - 1.5 * idx).clip(lower=35.0, upper=95.0)
        shifted["solar_w_m2"] = (shifted["solar_w_m2"] * (1.0 - 0.03 * idx)).clip(lower=0.0)
        shifted["location_id"] = loc["location_id"]
        shifted["district"] = loc["district"]
        columns = ["timestamp", "location_id", "district", "temp_c", "rh_pct", "solar_w_m2", "wind_m_s"]
        out_path = out_dir / f"weather_{loc['location_id']}.csv"
        shifted[columns].to_csv(out_path, index=False)
        manifest.append(
            {
                "path": str(out_path),
                "location_id": loc["location_id"],
                "district": loc["district"],
                "rows": str(len(shifted)),
                "bytes": str(out_path.stat().st_size),
                "sha256": sha256(out_path),
            }
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/http/nasa_power_bangkok.csv")
    parser.add_argument("--locations", default="data/locations.csv")
    parser.add_argument("--out-dir", default="data/staged")
    parser.add_argument("--manifest", default="data/weather_manifest.csv")
    args = parser.parse_args()

    weather = normalise_power_csv(Path(args.input))
    locations = load_locations(Path(args.locations))
    manifest = write_staged_files(weather, locations, Path(args.out_dir))
    with Path(args.manifest).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    print(f"staged_files={len(manifest)}")
    print(f"manifest={args.manifest}")


if __name__ == "__main__":
    main()
