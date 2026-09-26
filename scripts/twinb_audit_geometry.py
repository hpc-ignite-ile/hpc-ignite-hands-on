"""Read-only enclosure audit using the same pinned IDD as the simulator."""
import argparse
import json
import os
from pathlib import Path
from eppy.modeleditor import IDF

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("idf")
args = p.parse_args()
IDF.setiddname(str(Path(os.environ["ENERGYPLUS_HOME"]) / "Energy+.idd"))
idf = IDF(args.idf)
targets = {"F2-3_LOBBY", "F4_LOBBY", "F5_LOBBY"}
constructions = {obj.Name.upper(): obj for obj in idf.idfobjects["CONSTRUCTION"]}
materials = {obj.Name.upper(): obj for kind in ("MATERIAL", "MATERIAL:NOMASS", "MATERIAL:AIRGAP")
             for obj in idf.idfobjects[kind]}
result = {"building": [str(o) for o in idf.idfobjects["BUILDING"]], "zones": {}}
for target in sorted(targets):
    surfaces = []
    for surface in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if surface.Zone_Name.upper() != target and surface.Space_Name.upper() != target:
            continue
        construction = constructions.get(surface.Construction_Name.upper())
        layers = [v for v in construction.fieldvalues[2:] if v] if construction else []
        inner = materials.get(str(layers[-1]).upper()) if layers else None
        surfaces.append({"name": surface.Name, "type": surface.Surface_Type,
                         "zone": surface.Zone_Name, "space": surface.Space_Name,
                         "construction": surface.Construction_Name,
                         "boundary": surface.Outside_Boundary_Condition,
                         "inside_material": str(inner) if inner else None})
    result["zones"][target] = surfaces
print(json.dumps(result, indent=2))
