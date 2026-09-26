"""Prepare a bounded summer weekday benchmark without changing building physics."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from eppy.modeleditor import IDF


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("idf", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--days", type=int, default=1, choices=(1, 3))
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    IDF.setiddname(str(Path(os.environ["ENERGYPLUS_HOME"]) / "Energy+.idd"))
    idf = IDF(str(args.idf))
    for item in list(idf.idfobjects["RUNPERIOD"]):
        idf.removeidfobject(item)
    idf.newidfobject("RUNPERIOD", Name="Benchmark summer weekday", Begin_Month=7,
                     Begin_Day_of_Month=14, Begin_Year=2025, End_Month=7,
                     End_Day_of_Month=13 + args.days, End_Year=2025,
                     Day_of_Week_for_Start_Day="Monday",
                     Use_Weather_File_Holidays_and_Special_Days="No",
                     Use_Weather_File_Daylight_Saving_Period="No")
    # Common outputs allow CLI vs API comparison on the identical derived input.
    for kind in ("OUTPUT:VARIABLE", "OUTPUT:METER", "OUTPUT:METER:METERFILEONLY"):
        for item in list(idf.idfobjects[kind]):
            idf.removeidfobject(item)
    for variable in ("Zone Mean Air Temperature", "Zone Thermostat Cooling Setpoint Temperature"):
        idf.newidfobject("OUTPUT:VARIABLE", Key_Value="*", Variable_Name=variable, Reporting_Frequency="Timestep")
    idf.newidfobject("OUTPUT:METER", Key_Name="Electricity:Facility", Reporting_Frequency="Timestep")
    idf.newidfobject("OUTPUTCONTROL:FILES", Output_CSV="Yes")
    zones = [z.Name for z in idf.idfobjects["ZONE"]]
    zonelists = {z.Name.upper(): [v for v in z.fieldvalues[2:] if v] for z in idf.idfobjects["ZONELIST"]}
    controlled = []
    for thermostat in idf.idfobjects["ZONECONTROL:THERMOSTAT"]:
        key = thermostat.Zone_or_ZoneList_Name
        controlled.extend(zonelists.get(key.upper(), [key]))
    controlled = sorted(set(controlled))
    assert controlled and set(controlled).issubset(zones)
    schedules = {o.Name.upper(): o for kind in ("SCHEDULE:COMPACT", "SCHEDULE:CONSTANT") for o in idf.idfobjects[kind]}
    heating_maxima = []
    for kind in ("THERMOSTATSETPOINT:DUALSETPOINT", "THERMOSTATSETPOINT:SINGLEHEATING"):
        for item in idf.idfobjects[kind]:
            name = item.Heating_Setpoint_Temperature_Schedule_Name if kind.endswith("DUALSETPOINT") else item.Setpoint_Temperature_Schedule_Name
            schedule = schedules.get(name.upper())
            if schedule is None:
                raise ValueError(f"Heating schedule needs explicit bound support: {name}")
            values = []
            for value in schedule.fieldvalues[3:]:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    pass
            if not values:
                raise ValueError(f"No heating temperatures found: {name}")
            heating_maxima.append(max(values))
    cooling_floor = max(18.0, max(heating_maxima, default=17.5) + 0.5)
    assert cooling_floor <= 30, "Heating schedule incompatible with cooling safety bounds"
    metadata = {"source": str(args.idf.resolve()), "source_sha256": hashlib.sha256(args.idf.read_bytes()).hexdigest(),
                "zones": zones, "controlled_zones": controlled,
                "uncontrolled_zones": sorted(set(zones) - set(controlled)),
                "days": args.days, "expected_steps": args.days * 24 * int(idf.idfobjects["TIMESTEP"][0].Number_of_Timesteps_per_Hour),
                "changes": ["July 14 2025 Monday, one or three days; no holidays/DST", "timestep CSV diagnostics"],
                "geometry_materials_hvac_schedules_changed": False,
                "maximum_native_heating_schedule_C": max(heating_maxima, default=None),
                "minimum_cooling_command_C": cooling_floor,
                "deadband_guard": "Conservative global maximum heating schedule + 0.5 C; compact/constant schedules only"}
    idf.saveas(str(args.output / "model.idf"))
    metadata["derived_sha256"] = hashlib.sha256((args.output / "model.idf").read_bytes()).hexdigest()
    (args.output / "model.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
