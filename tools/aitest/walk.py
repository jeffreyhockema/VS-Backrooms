#!/usr/bin/env python3
"""Simulated player: one walker for N real minutes in one level, headless, reported like a real session.

    python tools/aitest/walk.py --mods <Mods dir> --level 1 [--armour none|leather|bronze|iron] [--light 7]
                                [--minutes 120] [--out <dir>] [--port 42813] [--data <dir>] [--keep]

Starts a dedicated server on its own data folder, runs `/backrooms walker start <level> ...` (src/Entities/MenaceSystem.Walker.cs:
a straw dummy walking the route arrival -> nearest gate -> through it, again and again, with health 15, hunger and an armour
tier, taking the director's encounters), waits the minutes out, stops the server and writes <out>/walk-<level>.md: felt bodies
per hour by band, time to first encounter, damage by source, deaths, blocks walked, caches opened, the walker's own final
status line, and the full tools/telemetry/report.py report of the session's jsonl after it.
"""
import argparse
import collections
import glob
import importlib.util
import os
import re
import shutil
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402  (the harness: Server, ServerDied)

ERR_RE = run.ERR_RE
FINAL_RE = re.compile(r"\[backrooms\] walker final \((.*?)\): (status: .*)")
STATUS_RE = re.compile(r"\[backrooms\] walker (status: .*)")
MENACING = ("Glimpse", "Stalk", "Hunt")
BANDS = ["Safe", "Heartland", "Approach", "Threshold"]


def load_report():
    path = os.path.join(HERE, "..", "telemetry", "report.py")
    spec = importlib.util.spec_from_file_location("telemetry_report", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def start_walker(srv, level, armour, light, minutes, wait=300):
    """Sends `walker start` (the first tries wait for the world to be ready); returns once it has put the dummy down."""
    mark = srv.mark()
    srv.cmd("/backrooms telemetry on")
    time.sleep(1)
    srv.cmd("/backrooms walker start %s %s %d %d" % (level, armour, light, minutes))
    got = srv.wait(lambda l: "walker placed" in l and l, mark, wait)
    return mark, got


def final_status(lines):
    last = None
    for l in lines:
        m = FINAL_RE.search(l) or STATUS_RE.search(l)
        if m:
            last = m.group(m.lastindex)
    return last


def find_jsonl(data):
    files = glob.glob(os.path.join(data, "vs", "ModData", "backroomsss", "telemetry", "*.jsonl"))
    return sorted(files, key=os.path.getmtime)[-1] if files else None


def hours(seconds):
    return seconds / 3600.0


def write_report(path, level, args, jsonl, status, errors, wall_minutes):
    rep = load_report()
    sessions = rep.load(jsonl)
    events = sessions[0][1]
    r = rep.analyse(events)
    me = sorted({e["p"] for e in events if e["p"].startswith("strawdummy#")})
    mine = [e for e in events if e["p"] in me]
    out = []
    out.append("# Walk report: Level %s, armour %s, light %d\n\n" % (level, args.armour, args.light))
    out.append("- %d real minutes asked, %.1f minutes of wall time including server start-up; telemetry file (%s), mod %s, layout %s\n" % (
        args.minutes, wall_minutes, os.path.basename(jsonl), r["info"].get("mod", "?"), r["info"].get("layout", "?")))
    out.append("- Menace %s, scarcity %s, thirst %s, fatigue %s (the world's settings; a walker has no thirst or fatigue of its own)\n" % (
        r["info"].get("backroomsMenace", "?"), r["info"].get("backroomsScarcity", "?"), r["info"].get("backroomsThirst", "?"), r["info"].get("backroomsFatigue", "?")))
    out.append("- Backrooms error lines in the server log: %d%s\n\n" % (len(errors), "".join("\n  - `%s`" % e[:160] for e in errors[:5])))

    out.append("## The walker's own status\n\n")
    out.append("`%s`\n\n" % (status or "no status line found"))

    # Time by band, from the walker's level / band / pos events
    band_seconds = collections.defaultdict(float)
    for (lvl, band), s in r["seconds"].items():
        band_seconds[band] += s
    total_s = sum(band_seconds.values())
    out.append("## Where it was\n\n")
    out.append("Played %.0f min in the telemetry's timeline: %s\n\n" % (total_s / 60, ", ".join("%s %.0f min" % (b, band_seconds.get(b, 0) / 60) for b in BANDS if band_seconds.get(b))))
    levels = sorted({l for l, _ in r["seconds"]}, key=str)
    out.append(rep.table(["Level"] + BANDS + ["Total min"],
                         [["Level " + str(l)] + [rep.f1(r["seconds"].get((l, b), 0) / 60) for b in BANDS] + [rep.f1(r["level_seconds"][l] / 60)] for l in levels]) + "\n")

    # Felt bodies per hour by band: spawns (director put-downs for the walker) of the menacing kinds, over the time in the band
    out.append("## Felt bodies per hour by band\n\n")
    rows = []
    for kind in sorted({k for k, _, _ in r["spawns"]}):
        cells = []
        for b in BANDS:
            n = sum(v for (k, bb, _), v in r["spawns"].items() if k == kind and bb == b)
            h = hours(band_seconds.get(b, 0))
            cells.append("%d (%s/h)" % (n, rep.f1(n / h)) if h > 0.02 else str(n))
        rows.append([kind + (" (menacing)" if kind in MENACING else "")] + cells)
    menacing = []
    for b in BANDS:
        n = sum(v for (k, bb, _), v in r["spawns"].items() if k in MENACING and bb == b)
        h = hours(band_seconds.get(b, 0))
        menacing.append("%d (%s/h)" % (n, rep.f1(n / h)) if h > 0.02 else str(n))
    rows.append(["**felt bodies** (Glimpse+Stalk+Hunt)"] + menacing)
    out.append(rep.table(["Kind"] + BANDS, rows) + "\n")
    byentity = collections.Counter()
    for (k, b, code), v in r["spawns"].items():
        byentity[(code, k)] += v
    out.append(rep.table(["Entity", "Kind", "Spawns"], [[c, k, v] for (c, k), v in sorted(byentity.items(), key=lambda kv: -kv[1])]) + "\n")

    # Time to first encounter: from the walker's start to the first menacing spawn
    start = next((e for e in mine if e["ev"] == "walker" and e.get("state") == "start"), None)
    first = next((e for e in mine if e["ev"] == "spawn" and e.get("kind") in MENACING), None)
    out.append("## Time to first encounter\n\n")
    if start and first:
        secs = (first["_t"] - start["_t"]).total_seconds()
        out.append("- %.0f s from the start to the first %s (%s, band %s)\n" % (secs, first["kind"], first["code"], first["band"]))
    else:
        out.append("- none in this walk\n")
    for lvl, vs in sorted(r["first_enc"].items(), key=lambda kv: str(kv[0])):
        out.append("- after arriving in Level %s: %s\n" % (lvl, ", ".join("%.0f s" % v for v in sorted(vs))))
    contacts = [e for e in mine if e["ev"] == "contact"]
    out.append("- contacts (an owned entity first sees the walker): %d\n" % len(contacts))
    flee = [e for e in mine if e["ev"] == "walker" and e.get("state") == "flee"]
    hides = [e for e in mine if e["ev"] == "walker" and e.get("state") == "hide"]
    out.append("- ran from a hunter %d times, hid from a stalker %d times\n\n" % (len(flee), len(hides)))

    # Damage, deaths
    out.append("## Damage and deaths\n\n")
    out.append(rep.table(["Source", "Hits", "Damage taken (after armour)"], [[s, n, rep.f1(a)] for s, (n, a) in sorted(r["damage"].items(), key=lambda kv: -kv[1][1])]) + "\n")
    raw = collections.defaultdict(float)
    for e in mine:
        if e["ev"] == "damage":
            raw[e["src"]] += e.get("raw", e["amount"])
    if raw:
        out.append("Before armour: " + ", ".join("%s %s" % (s, rep.f1(v)) for s, v in sorted(raw.items(), key=lambda kv: -kv[1])) + "\n\n")
    deaths = r["deaths"]
    out.append("Deaths: %d (%s per hour)\n\n" % (len(deaths), rep.f1(len(deaths) / max(hours(total_s), 1e-9))))
    out.append(rep.table(["Time", "Cause", "Level", "Band"], [[d["t"][11:19], d["cause"], d.get("level", ""), d.get("band", "")] for d in deaths]) + "\n")

    # Walking, caches
    out.append("## Walking and supplies\n\n")
    blocks = sum(r["walked"].values())
    caches = len(r["loot"])
    legs = [e for e in mine if e["ev"] == "walker" and e.get("state") in ("leg", "lap")]
    out.append("- Blocks walked: %d (%s per hour of play)\n" % (blocks, rep.f1(blocks / max(hours(total_s), 1e-9))))
    out.append("- Caches opened: %d (%s per 1000 blocks); eaten %d times\n" % (caches, rep.f1(caches / blocks * 1000) if blocks else "n/a", sum(r["eat"].values())))
    out.append("- Legs and laps logged: %d\n\n" % len(legs))

    out.append("## Telemetry report (tools/telemetry/report.py)\n\n")
    out.append(rep.render_session(jsonl, events).replace("\n## ", "\n### ").replace("## Session", "### Session", 1))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("".join(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mods", required=True, help="the Mods folder holding the built mod")
    ap.add_argument("--level", required=True, help="a level as /backrooms goto takes it (1, 3, 9, !, ...)")
    ap.add_argument("--armour", default="none")
    ap.add_argument("--light", type=int, default=7)
    ap.add_argument("--minutes", type=int, default=120)
    ap.add_argument("--out", default=None, help="where walk-<level>.md goes (default: review/walk)")
    ap.add_argument("--port", type=int, default=42813)
    ap.add_argument("--data", default=None)
    ap.add_argument("--keep", action="store_true", help="keep the server's data folder")
    a = ap.parse_args()
    out_dir = a.out or os.path.join(HERE, "..", "..", "review", "walk")
    os.makedirs(out_dir, exist_ok=True)
    data = a.data or tempfile.mkdtemp(prefix="walk-")
    os.makedirs(data, exist_ok=True)
    t0 = time.time()
    srv = run.Server(a.mods, os.path.join(data, "vs"), a.port)
    died = None
    try:
        if not srv.ready.wait(900):
            print("FAIL server never became ready")
            return 2
        time.sleep(5)
        mark, got = start_walker(srv, a.level, a.armour, a.light, a.minutes)
        if not got:
            print("FAIL the walker never got placed (see the log)")
            return 2
        print("walker placed: %s" % got.strip()[-120:], flush=True)
        walk_start = time.time()
        deadline = walk_start + a.minutes * 60 + 240
        next_note = walk_start + 300
        while time.time() < deadline:
            if srv.wait(lambda l: FINAL_RE.search(l), mark, 5):
                break
            if time.time() >= next_note:
                next_note += 300
                print("  %.0f min: %s" % ((time.time() - walk_start) / 60, final_status(srv.since(mark)) or "(no status yet)"), flush=True)
        else:
            srv.cmd("/backrooms walker stop")
            time.sleep(3)
    except run.ServerDied as e:
        died = str(e)
        print("FAIL SERVER DIED: " + died)
    finally:
        srv.stop()
        with open(os.path.join(data, "walk.log"), "w", encoding="utf-8") as f:
            f.write("\n".join(srv.lines))
    status = final_status(srv.lines)
    errors = [l for l in srv.lines if ERR_RE.search(l)]
    jsonl = find_jsonl(data)
    if not jsonl:
        print("FAIL no telemetry file under %s" % data)
        return 2
    label = re.sub(r"[^0-9A-Za-z!_-]", "_", a.level)
    path = os.path.join(out_dir, "walk-%s.md" % label)
    write_report(path, a.level, a, jsonl, status, errors, (time.time() - t0) / 60)
    shutil.copyfile(jsonl, os.path.join(out_dir, "walk-%s.jsonl" % label))
    print("wrote", path)
    print(status or "(no status)")
    if not a.keep and not a.data:
        shutil.rmtree(data, ignore_errors=True)
    return 1 if died else 0


if __name__ == "__main__":
    sys.exit(main())
