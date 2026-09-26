#!/bin/bash
# Run on transfer.lanta.nstda.or.th, from the isolated benchmark directory.
set -euo pipefail
mkdir -p inputs
base=https://raw.githubusercontent.com/NatLabRockies/EnergyPlus/v25.1.0
curl --fail --location "$base/testfiles/5ZoneAirCooled.idf" -o inputs/fivezone.idf
curl --fail --location "$base/testfiles/ASHRAE901_SchoolSecondary_STD2019_Denver.idf" -o inputs/school.idf
curl --fail --location "$base/LICENSE.txt" -o inputs/EnergyPlus-LICENSE.txt
curl --fail --location https://energyplus-weather.s3.amazonaws.com/north_and_central_america_wmo_region_4/USA/CO/USA_CO_Aurora-Buckley.Field.ANGB.724695_TMY3/USA_CO_Aurora-Buckley.Field.ANGB.724695_TMY3.epw -o inputs/denver.epw
: "${ENERGYPLUS_HOME:?Set ENERGYPLUS_HOME to your EnergyPlus 25.1.0 installation}"
cp "$ENERGYPLUS_HOME/WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw" inputs/chicago.epw
sha256sum inputs/* > inputs/SHA256SUMS
