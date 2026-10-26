#!/usr/bin/env python3
"""Report on the play telemetry of Backrooms: Survival Story (src/Telemetry/TelemetrySystem.cs).

    python tools/telemetry/report.py <file.jsonl | folder> [--out report.md] [--compare docs/design/balance-spec.yaml]

The files are JSON Lines, one event per line (t, h, p, ev, fields); a folder means every *.jsonl in it. The report is
markdown: per session, per level, felt rates, damage, deaths, stability, supplies, loot, notes, trades and a timeline
of the F8 marks with their context. Time is real time. Time in a band is worked out between consecutive events of a
player (level, band, pos, join), with gaps over 90 s (nobody there, or a pause) not counted.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import sys

GAP = 90.0          # seconds: a longer silence than this is not play
BANDS = ["Safe", "Heartland", "Approach", "Threshold"]


def parse_time(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=dt.timezone.utc)


def load(path):
    files = sorted(glob.glob(os.path.join(path, "*.jsonl"))) if os.path.isdir(path) else [path]
    sessions = []
    for f in files:
        events = []
        with open(f, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    e["_t"] = parse_time(e["t"])
                    events.append(e)
                except (ValueError, KeyError):
                    print("warning: %s line %d is not an event" % (f, n), file=sys.stderr)
        sessions.append((f, events))
    return sessions


def table(head, rows):
    if not rows:
        return "_none_\n"
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out) + "\n"


def f1(x):
    return "%.1f" % x


def analyse(events):
    """Everything the report needs from one session's events."""
    r = {}
    first = events[0]["_t"] if events else None
    last = events[-1]["_t"] if events else None
    r["start"], r["end"] = first, last
    r["info"] = next((e for e in events if e["ev"] == "session" and e.get("state") == "start"), {})
    players = sorted({e["p"] for e in events if e["p"] != "-" and "#" not in e["p"]} or {e["p"] for e in events if e["p"] != "-"})
    r["players"] = players

    # Time by (level, band), blocks walked by level, from a per-player timeline of the events that say where they are
    seconds = collections.defaultdict(float)          # (level, band) -> s
    walked = collections.defaultdict(float)           # level -> blocks
    level_seconds = collections.defaultdict(float)
    arrivals = collections.defaultdict(list)          # level -> [time of arrival]
    state = {}                                        # player -> (time, level, band, survival)
    for e in events:
        p, ev = e["p"], e["ev"]
        t = e["_t"]
        if ev in ("leave", "death", "respawn") and p in state:
            state.pop(p)
            continue
        if ev not in ("level", "band", "pos", "join"):
            continue
        if p in state:
            t0, lvl, band, surv = state[p]
            dtm = (t - t0).total_seconds()
            if 0 < dtm <= GAP and surv and lvl is not None:
                seconds[(lvl, band)] += dtm
                level_seconds[lvl] += dtm
        lvl, band, surv = (state[p][1], state[p][2], state[p][3]) if p in state else (None, None, True)
        if ev == "level":
            lvl, band = e["to"], e["band"]
            arrivals[lvl].append((p, t))
        elif ev == "band":
            lvl, band = e["level"], e["to"]
        elif ev == "pos":
            lvl, band = e["level"], e["band"]
            walked[lvl] += e.get("d", 0)
            surv = e.get("gm", "Survival") == "Survival"
        elif ev == "join":
            surv = e.get("gm", "Survival") == "Survival"
        state[p] = (t, lvl, band, surv)
    r["seconds"], r["walked"], r["level_seconds"], r["arrivals"] = seconds, walked, level_seconds, arrivals

    # Spawns
    spawns = collections.Counter()
    for e in events:
        if e["ev"] == "spawn" and "#" not in e["p"]:
            spawns[(e["kind"], e["band"], e["code"])] += 1
    r["spawns"] = spawns

    # Time to first encounter per level: from the arrival to the first spawn of a stalk/hunt/glimpse for that player
    # (set pieces counted: they are encounters); first contact is used when there is one
    first_enc = {}
    cur_level = {}
    arrived_at = {}
    seen_enc = set()
    for e in events:
        p, ev, t = e["p"], e["ev"], e["_t"]
        if ev == "level":
            cur_level[p] = e["to"]
            arrived_at[p] = t
            seen_enc.discard(p)
        elif ev == "spawn" and p in cur_level and p not in seen_enc and e["kind"] in ("Glimpse", "Stalk", "Hunt"):
            seen_enc.add(p)
            first_enc.setdefault(cur_level[p], []).append((t - arrived_at[p]).total_seconds())
    r["first_enc"] = first_enc

    # Damage, deaths, stability, blackouts
    dmg = collections.defaultdict(lambda: [0, 0.0])
    armour = collections.Counter()
    for e in events:
        if e["ev"] == "damage":
            d = dmg[e["src"]]
            d[0] += 1
            d[1] += e["amount"]
            armour[e.get("armour", "?")] += e["amount"]
    r["damage"], r["armour"] = dmg, armour
    r["deaths"] = [e for e in events if e["ev"] == "death"]
    r["stab"] = collections.Counter(e["crossed"] for e in events if e["ev"] == "stab")
    r["blackouts"] = [e for e in events if e["ev"] == "blackout"]
    r["contacts"] = [e for e in events if e["ev"] == "contact"]
    r["kinds"] = collections.Counter((e["from"], e["to"]) for e in events if e["ev"] == "kind")

    # Supplies, loot, notes, trades, crossings
    r["eat"] = collections.Counter(e["item"] for e in events if e["ev"] == "eat")
    r["drink"] = collections.Counter(e["item"] for e in events if e["ev"] == "drink")
    r["loot"] = [e for e in events if e["ev"] == "loot"]
    r["notes"] = [e for e in events if e["ev"] == "note"]
    r["trades"] = [e for e in events if e["ev"] == "trade"]
    r["cross"] = [e for e in events if e["ev"] == "cross"]
    r["needs"] = collections.Counter((e["kind"], e["band"]) for e in events if e["ev"] == "need")
    r["marks"] = [e for e in events if e["ev"] == "mark"]
    r["throttled"] = sum(e.get("dropped", 0) for e in events if e["ev"] == "throttled")
    return r


def hours(s):
    return s / 3600.0


def render_session(path, events):
    r = analyse(events)
    out = []
    info = r["info"]
    out.append("## Session %s\n" % os.path.basename(path))
    if not events:
        return "".join(out) + "_empty_\n"
    total = (r["end"] - r["start"]).total_seconds()
    played = sum(r["seconds"].values())
    out.append("- World %s, seed %s, mod %s, layout %s; menace %s, scarcity %s, thirst %s, fatigue %s\n" % (
        info.get("world", "?"), info.get("seed", "?"), info.get("mod", "?"), info.get("layout", "?"), info.get("backroomsMenace", "?"),
        info.get("backroomsScarcity", "?"), info.get("backroomsThirst", "?"), info.get("backroomsFatigue", "?")))
    out.append("- %s UTC, %.0f min of server time, %.0f min of survival play, players: %s\n" % (
        r["start"].strftime("%Y-%m-%d %H:%M"), total / 60, played / 60, ", ".join(r["players"]) or "-"))
    if r["throttled"]:
        out.append("- %d events dropped by the 20 a second throttle\n" % r["throttled"])
    out.append("\n")

    out.append("### Minutes by level and band\n\n")
    levels = sorted({l for l, _ in r["seconds"]}, key=str)
    rows = []
    for l in levels:
        cells = [f1(r["seconds"].get((l, b), 0) / 60) for b in BANDS]
        extra = sum(v for (ll, b), v in r["seconds"].items() if ll == l and b not in BANDS)
        rows.append(["Level " + str(l)] + cells + [f1(r["level_seconds"][l] / 60)])
    out.append(table(["Level"] + BANDS + ["Total"], rows) + "\n")

    out.append("### Felt rates (spawns per hour in the band)\n\n")
    rows = []
    kinds = sorted({k for k, _, _ in r["spawns"]})
    for kind in kinds:
        cells = []
        for b in BANDS:
            n = sum(v for (k, bb, _), v in r["spawns"].items() if k == kind and bb == b)
            h = sum(v for (_, bb), v in r["seconds"].items() if bb == b) / 3600
            cells.append("%d (%s/h)" % (n, f1(n / h)) if h > 0.01 else str(n))
        rows.append([kind] + cells)
    out.append(table(["Kind"] + BANDS, rows) + "\n")
    byentity = collections.Counter()
    for (k, b, code), v in r["spawns"].items():
        byentity[(code, k)] += v
    out.append(table(["Entity", "Kind", "Spawns"], [[c, k, v] for (c, k), v in sorted(byentity.items(), key=lambda kv: -kv[1])]) + "\n")

    out.append("### Time to first encounter per level (seconds from arriving to the first glimpse, stalk or hunt)\n\n")
    rows = []
    for l, vs in sorted(r["first_enc"].items(), key=lambda kv: str(kv[0])):
        vs = sorted(vs)
        rows.append(["Level " + str(l), len(vs), "%.0f" % vs[len(vs) // 2], "%.0f" % vs[0], "%.0f" % vs[-1]])
    out.append(table(["Level", "Arrivals met something", "Median s", "Min s", "Max s"], rows) + "\n")
    if r["contacts"]:
        out.append("Contacts (an owned entity first sees the player): %d; median distance %.1f blocks\n\n" % (
            len(r["contacts"]), sorted(c["dist"] for c in r["contacts"])[len(r["contacts"]) // 2]))
    if r["kinds"]:
        out.append(table(["Kind change", "Count"], [["%s -> %s" % k, v] for k, v in sorted(r["kinds"].items(), key=lambda kv: -kv[1])]) + "\n")

    out.append("### Damage and deaths\n\n")
    out.append(table(["Source", "Hits", "Damage"], [[s, n, f1(a)] for s, (n, a) in sorted(r["damage"].items(), key=lambda kv: -kv[1][1])]) + "\n")
    if r["armour"]:
        out.append("Damage taken by armour worn: " + ", ".join("%s %s" % (k, f1(v)) for k, v in r["armour"].items()) + "\n\n")
    out.append(table(["Time", "Player", "Cause", "Level", "Band"], [[d["t"][11:19], d["p"], d["cause"], d.get("level", ""), d.get("band", "")] for d in r["deaths"]]) + "\n")

    out.append("### Stability, blackouts, needs\n\n")
    out.append("- Stability crossings: " + (", ".join("%s x%d" % (k, v) for k, v in sorted(r["stab"].items())) or "none") + "\n")
    out.append("- Blackouts: %d\n" % len(r["blackouts"]))
    out.append("- Need bands entered: " + (", ".join("%s %s x%d" % (k[0], k[1], v) for k, v in sorted(r["needs"].items())) or "none") + "\n\n")

    out.append("### Supplies, loot, notes, trades\n\n")
    ph = max(hours(played), 1e-9)
    out.append("- Eaten: %d (%s/h): %s\n" % (sum(r["eat"].values()), f1(sum(r["eat"].values()) / ph), ", ".join("%s x%d" % kv for kv in r["eat"].most_common(8)) or "-"))
    out.append("- Drunk: %d (%s/h): %s\n" % (sum(r["drink"].values()), f1(sum(r["drink"].values()) / ph), ", ".join("%s x%d" % kv for kv in r["drink"].most_common(8)) or "-"))
    blocks = sum(r["walked"].values())
    out.append("- Walked about %d blocks; loot opened or broken: %d (%s per 1000 blocks)\n" % (blocks, len(r["loot"]), f1(len(r["loot"]) / blocks * 1000) if blocks else "n/a"))
    lootrows = collections.defaultdict(lambda: [0, 0])
    for e in r["loot"]:
        lootrows[e.get("level", "?")][0] += 1
    for l, w in r["walked"].items():
        lootrows[l][1] = int(w)
    out.append("\n" + table(["Level", "Loot", "Blocks walked", "Loot per 1000 blocks"],
                            [["Level " + str(l), n, w, f1(n / w * 1000) if w else "n/a"] for l, (n, w) in sorted(lootrows.items(), key=lambda kv: str(kv[0]))]) + "\n")
    out.append("- Notes read: %d (%s)\n" % (len(r["notes"]), ", ".join(n["key"] for n in r["notes"][:12]) or "-"))
    out.append("- Class crossings announced: %s\n" % (", ".join("Level %s (class %s)" % (c["level"], c["class"]) for c in r["cross"]) or "none"))
    out.append("- Trades: %d\n" % len(r["trades"]))
    for t in r["trades"]:
        out.append("  - %s: %s (%s RG)\n" % (t["t"][11:19], t["item"], t["price"]))
    out.append("\n")

    if r["marks"]:
        out.append("### Marks\n\n")
        t0 = r["start"]
        for m in r["marks"]:
            out.append("#### %s  %s%s\n\n" % (m["t"][11:19], m["p"], (": " + m["text"]) if m.get("text") else ""))
            out.append("Level %s, band %s, menace %s, hp %s/%s, stability %s, thirst %s%%, rest %s%%, at %s %s %s\n\n" % (
                m.get("level"), m.get("band"), m.get("menace"), m.get("hp"), m.get("maxhp"), m.get("stability"),
                "off" if m.get("thirst", -1) < 0 else "%.0f" % m["thirst"], "off" if m.get("rest", -1) < 0 else "%.0f" % m["rest"],
                m.get("x"), m.get("y"), m.get("z")))
            if m.get("about"):
                out.append("About: " + ", ".join("%s %s %sm" % (a["code"], a["kind"], a["dist"]) for a in m["about"]) + "\n\n")
            if m.get("recent"):
                out.append("Last minute:\n\n")
                for e in m["recent"]:
                    fields = ", ".join("%s=%s" % (k, v) for k, v in e.items() if k not in ("t", "ev"))
                    out.append("- %s %s %s\n" % (e["t"][11:19], e["ev"], fields))
                out.append("\n")
    return "".join(out)


def compare(spec_path, sessions):
    """TODO: --compare <balance-spec.yaml>.

    Interface (the spec file does not exist yet): the YAML maps a measure to the range the design wants, e.g.

        felt_spawns_per_hour:        # per (level, band, kind): [low, high]
          "0":
            Heartland:
              Stalk: [0.5, 2.0]
        time_to_first_encounter_s:   # per level: [low, high]
          "1": [60, 240]
        damage_per_hour:             # per level: [low, high]
        supplies_per_hour:           # eat + drink: [low, high]
        loot_per_1000_blocks:        # per level: [low, high]

    The merged measures for all the sessions given (the same ones the report prints, computed by analyse()) are
    to be checked against these ranges and printed as a table: measure, level/band, observed, wanted, verdict
    (low / ok / high). Return the markdown for that table.
    """
    return "## Balance comparison\n\n_Not implemented yet: %s is a TODO (see compare() in tools/telemetry/report.py)._\n" % spec_path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="a .jsonl file, or a folder of them")
    ap.add_argument("--out", help="write the markdown here instead of printing it")
    ap.add_argument("--compare", metavar="SPEC.yaml", help="check the measures against a balance spec (TODO; the spec does not exist yet)")
    args = ap.parse_args()
    sessions = load(args.path)
    if not sessions:
        raise SystemExit("no .jsonl files in " + args.path)
    parts = ["# Play telemetry report\n\n%d session(s)\n\n" % len(sessions)]
    for path, events in sessions:
        parts.append(render_session(path, events))
    if args.compare:
        parts.append(compare(args.compare, sessions))
    text = "\n".join(parts)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote", args.out)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
