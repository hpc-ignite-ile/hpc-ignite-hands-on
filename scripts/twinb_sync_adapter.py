"""Single-process CPU EnergyPlus/Mesa benchmark adapter (not a Boonchoo calibration)."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

from twinb_baseline_gate import error_counts


def safe_setpoint(value):
    if value is None:
        return None
    if not math.isfinite(value) or not 18 <= value <= 30:
        raise ValueError(f"invalid cooling setpoint: {value}")
    return float(value)


def cooling_request(temp, preferred, tolerance, occupied):
    if not all(math.isfinite(v) for v in (temp, preferred, tolerance)):
        raise ValueError("non-finite agent state")
    return safe_setpoint(preferred) if occupied and temp > preferred + tolerance else None


def respect_deadband(value, floor):
    return None if value is None else safe_setpoint(max(safe_setpoint(value), floor))


class StepClock:
    def __init__(self):
        self.last = None
        self.count = 0

    def accept(self, stamp):
        if stamp == self.last:
            return False
        if self.last is not None and stamp < self.last:
            raise ValueError("simulation clock moved backwards")
        self.last = stamp
        self.count += 1
        return True


def make_population(zones, count, seed):
    import mesa

    class RequestAgent(mesa.Agent):
        def __init__(self, model, zone):
            super().__init__(model)
            self.zone = zone
            # Synthetic thermostat preferences, not calibrated occupant measurements.
            self.preferred = model.random.uniform(22, 26)
            self.tolerance = model.random.uniform(0.5, 1.5)

        def step(self):
            self.request = cooling_request(self.model.temps[self.zone], self.preferred,
                                           self.tolerance, self.model.occupied)

    class Population(mesa.Model):
        def __init__(self):
            super().__init__(seed=seed)
            for index in range(count):
                RequestAgent(self, zones[index % len(zones)])

        def step(self):
            self.agents.do("step")

        def decide(self, temps, occupied):
            self.temps, self.occupied = temps, occupied
            self.step()
            commands = dict.fromkeys(zones)
            for agent in self.agents:
                if agent.request is not None:
                    prior = commands[agent.zone]
                    commands[agent.zone] = agent.request if prior is None else min(prior, agent.request)
            return commands

    return Population()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--weather", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--mode", choices=("readonly", "reset", "fixed", "mesa"), required=True)
    p.add_argument("--agents", type=int, default=50)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()
    if args.agents < 1:
        p.error("agents must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, os.environ["ENERGYPLUS_HOME"])
    from pyenergyplus.api import EnergyPlusAPI
    meta = json.loads((args.model / "model.json").read_text())
    api = EnergyPlusAPI()
    ex = api.exchange
    state = api.state_manager.new_state()
    zones = meta["zones"]
    controlled = meta["controlled_zones"]
    population = make_population(controlled, args.agents, args.seed) if args.mode == "mesa" else None
    clock = StepClock()
    temperatures, actuators, setpoints = {}, {}, {}
    commands = dict.fromkeys(controlled)
    cooling_floor = meta["minimum_cooling_command_C"]
    failures = []
    stats = {"mode": args.mode, "seed": args.seed, "agents": args.agents if population else 0,
             "set_calls": 0, "reset_calls": 0, "callback_seconds": 0.0,
             "minimum_cooling_command_C": cooling_floor,
             "job_id": os.getenv("SLURM_JOB_ID"), "expected_steps": meta["expected_steps"],
             "idf_sha256": hashlib.sha256((args.model / "model.idf").read_bytes()).hexdigest(),
             "weather_sha256": hashlib.sha256(args.weather.read_bytes()).hexdigest()}
    for zone in zones:
        ex.request_variable(state, "Zone Mean Air Temperature", zone)
    for zone in controlled:
        ex.request_variable(state, "Zone Thermostat Cooling Setpoint Temperature", zone)
    records = (args.output / "trace.csv").open("w", newline="")
    writer = csv.writer(records)
    writer.writerow(["step", "day_of_year", "hour", "zone_timestep", "zone", "temperature_C",
                     "cooling_setpoint_C", "command_C"])

    def eligible(s):
        return ex.api_data_fully_ready(s) and not ex.warmup_flag(s) and ex.kind_of_sim(s) == 3

    def initialize(s):
        if temperatures:
            return
        (args.output / "api-inventory.csv").write_bytes(ex.list_available_api_data_csv(s))
        for zone in zones:
            temperatures[zone] = ex.get_variable_handle(s, "Zone Mean Air Temperature", zone)
        for zone in controlled:
            actuators[zone] = ex.get_actuator_handle(s, "Zone Temperature Control", "Cooling Setpoint", zone)
            setpoints[zone] = ex.get_variable_handle(s, "Zone Thermostat Cooling Setpoint Temperature", zone)
        if any(h < 0 for h in [*temperatures.values(), *actuators.values(), *setpoints.values()]):
            raise RuntimeError("required handle missing; inspect api-inventory.csv")
        (args.output / "handles.json").write_text(json.dumps({"temperatures": temperatures,
            "cooling_actuators": actuators, "setpoints": setpoints,
            "uncontrolled_zones": meta["uncontrolled_zones"]}, indent=2))

    def guarded(callback):
        def wrapped(s):
            if failures:
                return
            start = time.monotonic()
            try:
                if not eligible(s):
                    return
                initialize(s)
                callback(s)
                if ex.api_error_flag(s):
                    raise RuntimeError("EnergyPlus API error flag set")
            except Exception:
                failures.append(traceback.format_exc())
                api.runtime.stop_simulation(s)
            finally:
                stats["callback_seconds"] += time.monotonic() - start
        return wrapped

    def apply_commands(s):
        if args.mode == "readonly":
            return
        for zone, handle in actuators.items():
            value = safe_setpoint(commands[zone])
            if value is None:
                ex.reset_actuator(s, handle)
                stats["reset_calls"] += 1
            else:
                ex.set_actuator_value(s, handle, value)
                stats["set_calls"] += 1

    def finish_zone(s):
        stamp = (ex.current_environment_num(s), ex.day_of_year(s), ex.hour(s), ex.zone_time_step_number(s))
        if not clock.accept(stamp):
            raise RuntimeError("duplicate end-zone callback")
        temps = {zone: ex.get_variable_value(s, handle) for zone, handle in temperatures.items()}
        if not all(math.isfinite(t) for t in temps.values()):
            raise RuntimeError("non-finite zone temperatures")
        for zone in zones:
            sp = ex.get_variable_value(s, setpoints[zone]) if zone in setpoints else None
            if sp is not None and not math.isfinite(sp):
                raise RuntimeError("non-finite thermostat setpoint")
            writer.writerow([clock.count, *stamp[1:], zone, temps[zone], sp, commands.get(zone)])
        # Initial interval is native control. Completed state drives NEXT interval.
        hour = ex.hour(s) + ex.zone_time_step_number(s) * ex.zone_time_step(s)
        occupied = 8 <= hour < 17
        if args.mode == "mesa":
            commands.update(population.decide(temps, occupied))
        elif args.mode == "fixed":
            commands.update(dict.fromkeys(controlled, 26.0 if 8 <= hour < 12 else None))
        commands.update({zone: respect_deadband(value, cooling_floor) for zone, value in commands.items()})
        records.flush()
        (args.output / "heartbeat.json").write_text(json.dumps({"step": clock.count, "stamp": stamp}))

    # Thermostat override flags must be set BEFORE GetZoneAirSetPoints.
    api.runtime.callback_begin_system_timestep_before_predictor(state, guarded(apply_commands))
    api.runtime.callback_end_zone_timestep_after_zone_reporting(state, guarded(finish_zone))
    start = time.monotonic()
    try:
        code = api.runtime.run_energyplus(state, ["-d", str(args.output.resolve()), "-w",
                  str(args.weather.resolve()), str((args.model / "model.idf").resolve())])
    finally:
        records.close()
        api.state_manager.delete_state(state)
    stats.update(returncode=code, elapsed_seconds=time.monotonic() - start,
                 steps=clock.count, mesa_steps=population.steps if population else 0, failures=failures)
    err = args.output / "eplusout.err"
    stats["errors"] = error_counts(err.read_text()) if err.exists() else None
    stats["passed"] = (code == 0 and not failures and clock.count == meta["expected_steps"]
                       and stats["errors"] is not None and not stats["errors"]["Severe"]
                       and not stats["errors"]["Fatal"]
                       and (population is None or population.steps == clock.count))
    (args.output / "summary.json").write_text(json.dumps(stats, indent=2) + "\n")
    print(json.dumps(stats, indent=2))
    raise SystemExit(0 if stats["passed"] else 1)


if __name__ == "__main__":
    main()
