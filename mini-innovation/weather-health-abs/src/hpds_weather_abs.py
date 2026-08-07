from __future__ import annotations

import argparse
import csv
import glob
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd
from dask import delayed
from dask.distributed import Client, LocalCluster


def heat_index_c(temp_c: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    temp_f = temp_c * 9.0 / 5.0 + 32.0
    rh = rh_pct
    hi_f = (
        -42.379
        + 2.04901523 * temp_f
        + 10.14333127 * rh
        - 0.22475541 * temp_f * rh
        - 0.00683783 * temp_f * temp_f
        - 0.05481717 * rh * rh
        + 0.00122874 * temp_f * temp_f * rh
        + 0.00085282 * temp_f * rh * rh
        - 0.00000199 * temp_f * temp_f * rh * rh
    )
    return (hi_f - 32.0) * 5.0 / 9.0


def read_csv_rows(path: str) -> list[dict[str, str]]:
    with open(path, encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def building_response(weather: pd.DataFrame, scenario: dict[str, str]) -> tuple[float, float, float]:
    setpoint = float(scenario["cooling_setpoint_c"])
    thermal_tau = float(scenario["thermal_tau_h"])
    solar_gain = float(scenario["solar_gain"])
    indoor = float(scenario["initial_indoor_c"])
    peak_indoor = indoor
    cooling_kwh = 0.0
    indoor_hours = 0.0
    for row in weather.itertuples(index=False):
        drift = (row.temp_c - indoor) / thermal_tau
        solar = solar_gain * row.solar_w_m2 / 1000.0
        cooling = max(0.0, indoor - setpoint) * float(scenario["cooling_power"])
        indoor = indoor + drift + solar - 0.25 * cooling
        peak_indoor = max(peak_indoor, indoor)
        cooling_kwh += cooling
        indoor_hours += max(0.0, indoor - 30.0)
    return peak_indoor, cooling_kwh, indoor_hours


def simulate_agents(weather_path: str, location: dict[str, str], scenario: dict[str, str]) -> dict[str, str]:
    start = time.perf_counter()
    weather = pd.read_csv(weather_path, parse_dates=["timestamp"])
    temp = weather["temp_c"].to_numpy(dtype=float)
    rh = weather["rh_pct"].to_numpy(dtype=float)
    heat_index = heat_index_c(temp, rh)
    peak_indoor, cooling_kwh, indoor_hot_hours = building_response(weather, scenario)
    rng = np.random.default_rng(int(scenario["seed"]) + int(location["location_id"]))
    agents = int(scenario["agents"])
    vulnerability = rng.beta(2.0, 7.0, size=agents)
    outdoor_preference = rng.uniform(0.15, 0.85, size=agents)
    exposure_hours = 0.0
    contact_hours = 0.0
    infection_proxy = 0.0
    policy_strength = float(scenario["outdoor_reduction"])
    for hi in heat_index:
        heat_pressure = max(0.0, hi - 32.0) / 10.0
        outdoor_probability = np.clip(outdoor_preference - policy_strength * heat_pressure, 0.02, 0.95)
        outside = rng.random(agents) < outdoor_probability
        exposure = np.where(outside, max(0.0, hi - 30.0), max(0.0, peak_indoor - 30.0))
        exposure_hours += float(exposure.sum())
        contact_multiplier = 1.0 + 0.12 * heat_pressure + float(scenario["crowding_factor"]) * (~outside)
        contact_hours += float(contact_multiplier.sum())
        infection_proxy += float((contact_multiplier * (1.0 + vulnerability * exposure / 20.0)).sum())
    elapsed = time.perf_counter() - start
    return {
        "location_id": location["location_id"],
        "district": location["district"],
        "scenario_id": scenario["scenario_id"],
        "policy": scenario["policy"],
        "rows": str(len(weather)),
        "agents": str(agents),
        "mean_temp_c": f"{temp.mean():.4f}",
        "max_heat_index_c": f"{heat_index.max():.4f}",
        "peak_indoor_c": f"{peak_indoor:.4f}",
        "cooling_kwh": f"{cooling_kwh:.4f}",
        "indoor_hot_hours": f"{indoor_hot_hours:.4f}",
        "exposure_agent_hours": f"{exposure_hours:.4f}",
        "contact_hours": f"{contact_hours:.4f}",
        "infection_risk_proxy": f"{infection_proxy / max(agents, 1):.4f}",
        "elapsed_sec": f"{elapsed:.6f}",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--weather-glob", default="data/staged/weather_*.csv")
    parser.add_argument("--locations", default="data/locations.csv")
    parser.add_argument("--scenarios", default="data/scenarios.csv")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--out", default="results/hpds_weather_abs_summary.csv")
    args = parser.parse_args()

    weather_files = sorted(glob.glob(args.weather_glob))
    locations = {row["location_id"]: row for row in read_csv_rows(args.locations)}
    scenarios = read_csv_rows(args.scenarios)
    if not weather_files:
        raise SystemExit(f"no weather files matched {args.weather_glob}")
    tasks = []
    for weather_path in weather_files:
        location_id = Path(weather_path).stem.split("_")[-1]
        for scenario in scenarios:
            tasks.append(delayed(simulate_agents)(weather_path, locations[location_id], scenario))
    cluster = LocalCluster(n_workers=args.workers, threads_per_worker=1, dashboard_address=None)
    with Client(cluster) as client:
        rows = list(client.gather(client.compute(tasks)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"tasks={len(tasks)}")
    print(f"workers={args.workers}")
    print(f"wrote={out}")


if __name__ == "__main__":
    main()
