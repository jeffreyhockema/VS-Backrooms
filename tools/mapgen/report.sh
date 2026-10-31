#!/usr/bin/env bash
# Renders the middle of each level's ring and prints its layout metrics (see metrics.py).
# Usage: tools/mapgen/report.sh [seed] [cells] [angle] [levels...]
#   e.g. tools/mapgen/report.sh 56693014 12 40 0 3 6
# Writes report-l<N>.png next to this script. Build first: dotnet build tools/mapgen -c Release -o tools/mapgen/out
set -e
cd "$(dirname "$0")"
seed=${1:-56693014}; cells=${2:-12}; angle=${3:-40}
shift 3 2>/dev/null || shift $#
levels=${*:-0 1 2 3 4 5 6 7 8 9 10}
for lv in $levels; do
  ./out/mapgen "$seed" "$cells" region "$lv" "$angle" > /dev/null
  python render.py 1 > /dev/null
  mv map.png "report-l$lv.png"
  python metrics.py "$lv"
done
