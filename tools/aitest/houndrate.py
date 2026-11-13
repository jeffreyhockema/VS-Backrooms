"""Hound packs and all encounters per 10 real minutes, headless (feedback round 2026-11, package "late").

Starts a dedicated server with a build, puts straw dummies down at fixed spots (one per level and band, from
`tools/mapgen` mode `bandspots`, seed 12345), has the director direct them as players (`/backrooms dummies on`) with the
play telemetry on, waits, and counts what was put down for each dummy from the telemetry's spawn events: the bodies (a
glimpse, a stalker, a hunter or a pack of them, set pieces left out) and the Hound packs among them (Hounds put down to
stalk or hunt). Headless entities never walk, so a pack never reaches its dummy: it hunts until its time runs out and
leaves, as a pack that loses its quarry would (the Hound's hunt is 180 s, its whole encounter 300 s).

    python tools/aitest/houndrate.py --mods <Mods dir> [--data DIR] [--port 43252] [--minutes 40] [--label new]

Prints one line per spot and writes <data>/houndrate.json. Run the old build and the new one side by side (two ports) to
compare. The spots are those of seed 12345; another seed needs `mapgen <seed> 16000 bandspots <level>`.
"""
import argparse
import glob
import json
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import Server, ServerDied  # noqa: E402

# (name, x, z): seed 12345, layout 15 and 16 alike (only Levels 10 and 11 differ)
SPOTS = [
    ("L3 approach", 509717, 509182),
    ("L8 road", 514005, 517660),
    ("L8 off-road", 516363, 506968),
    ("L9 approach", 514124, 503952),
    ("L9 threshold", 505333, 506511),
]
LIST_RE = re.compile(r"#(\d+) at (-?\d+) (-?\d+) (-?\d+): Level (\S+), band (\w+)")


def place(srv, x, z, tries=10):
    for attempt in range(tries):
        m = srv.mark()
        srv.cmd("/backrooms encounter faceling ambient %d %d" % (x, z))
        r = srv.wait(lambda l: ("put down" in l and l) or ("not loaded" in l.lower() and l) or ("No floor" in l and l)
                     or ("Found nowhere" in l and l), m, 30)
        if r and "put down" in r:
            return True
        if r and "No floor" in r:
            return False
        time.sleep(8)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods", required=True)
    ap.add_argument("--data")
    ap.add_argument("--port", type=int, default=43252)
    ap.add_argument("--minutes", type=float, default=40)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    data = a.data or tempfile.mkdtemp(prefix="houndrate-")
    os.makedirs(data, exist_ok=True)
    srv = Server(a.mods, os.path.join(data, "vs"), a.port)
    try:
        if not srv.ready.wait(900):
            sys.exit("server never became ready")
        time.sleep(5)
        srv.cmd("/backrooms telemetry on")
        placed = []
        for name, x, z in SPOTS:
            ok = place(srv, x, z)
            print("%s %s at %d %d" % ("placed" if ok else "COULD NOT PLACE", name, x, z), flush=True)
            if ok:
                placed.append((name, x, z))
        time.sleep(3)
        m = srv.mark()
        srv.cmd("/backrooms dummies on")
        time.sleep(3)
        dummies = {}
        for l in srv.since(m):
            r = LIST_RE.search(l)
            if r:
                dx, dz = int(r.group(2)), int(r.group(4))
                near = min(placed, key=lambda s: abs(s[1] - dx) + abs(s[2] - dz))
                dummies[r.group(1)] = dict(spot=near[0], x=dx, z=dz, level=r.group(5), band=r.group(6))
        print("dummies: " + "; ".join("#%s %s (Level %s, %s)" % (k, v["spot"], v["level"], v["band"]) for k, v in dummies.items()), flush=True)
        started = time.time()
        while time.time() - started < a.minutes * 60:
            time.sleep(20)
            if srv.p.poll() is not None:
                raise ServerDied("server exited")
        minutes = (time.time() - started) / 60
        srv.cmd("/backrooms dummies off")
        time.sleep(2)
    finally:
        srv.stop()
    files = sorted(glob.glob(os.path.join(data, "vs", "ModData", "backroomsss", "telemetry", "*.jsonl")))
    events = []
    for f in files:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                try:
                    events.append(json.loads(line))
                except ValueError:
                    pass
    # Bodies: one per (dummy, code, kind) burst of spawn events within 2 s (a pack is put down at once)
    per = defaultdict(lambda: dict(bodies=0, packs=0, codes=defaultdict(int)))
    last = {}
    for e in events:
        if e.get("ev") != "spawn" or e.get("setpiece") in (True, "True", "true") or e.get("kind") == "Ambient":
            continue
        who = str(e.get("p", ""))
        if not who.startswith("strawdummy#"):
            continue
        did = who.split("#", 1)[1]
        t = datetime.strptime(e["t"], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()
        key = (did, e.get("code"), e.get("kind"))
        if key in last and t - last[key] < 2.0:
            last[key] = t
            continue
        last[key] = t
        rec = per[did]
        rec["bodies"] += 1
        rec["codes"][e.get("code")] += 1
        if e.get("code") == "hound" and e.get("kind") in ("Stalk", "Hunt"):
            rec["packs"] += 1
    rows = []
    for did, d in sorted(dummies.items(), key=lambda kv: kv[1]["spot"]):
        rec = per[did]
        rows.append(dict(spot=d["spot"], level=d["level"], band=d["band"], minutes=round(minutes, 1),
                         hound_packs_per_10=round(rec["packs"] * 10 / minutes, 2), bodies_per_10=round(rec["bodies"] * 10 / minutes, 2),
                         packs=rec["packs"], bodies=rec["bodies"], codes=dict(rec["codes"])))
        print("%-13s %s Level %s %-9s: %5.2f Hound packs / 10 min, %5.2f bodies / 10 min (%d packs, %d bodies in %.0f min; %s)" % (
            a.label, d["spot"], d["level"], d["band"], rows[-1]["hound_packs_per_10"], rows[-1]["bodies_per_10"], rec["packs"], rec["bodies"], minutes,
            ", ".join("%s %d" % kv for kv in sorted(rec["codes"].items()))), flush=True)
    with open(os.path.join(data, "houndrate.json"), "w", encoding="utf-8") as f:
        json.dump(dict(label=a.label, minutes=minutes, rows=rows), f, indent=1)


if __name__ == "__main__":
    main()
