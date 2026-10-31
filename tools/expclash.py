"""Experimental levels: after merging main, finds a value an experimental level shares with one of main's.

    python tools/expclash.py

Reads src/Worldgen/Tiles.cs. Reports (1) an enum value held by both an experimental name (L73, Basement, L52, L31,
L120, L36, L15, L23) and another name, (2) a First/Last range of one side overlapping a range or constant of the other, (3) a
constant at or above its table's Limit. Main's values are released and never move: renumber the experimental side.
Prints nothing but "clean" when there is nothing to fix; exits 1 otherwise.
"""
import os
import re
import sys

EXP = re.compile(r"L73|Basement|L52|L31|L120|L36|L15|L23")
src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "Worldgen", "Tiles.cs")
t = re.sub(r"//[^\n]*", "", open(src, encoding="utf-8").read())
found = []

for m in re.finditer(r"enum\s+(\w+)\s*:\s*\w+\s*\{(.*?)\}", t, re.S):
    v, vals = -1, {}
    for part in m.group(2).split(","):
        mm = re.match(r"\s*(\w+)(?:\s*=\s*(\w+))?", part)
        if not mm or not mm.group(1):
            continue
        g = mm.group(2)
        v = (int(g, 0) if re.match(r"^\d", g) else vals.get(g, v)) if g else v + 1
        vals[mm.group(1)] = v
    by = {}
    for k, x in vals.items():
        by.setdefault(x, []).append(k)
    for x, ks in by.items():
        if any(EXP.search(k) for k in ks) and any(not EXP.search(k) for k in ks):
            found.append(f"enum {m.group(1)}: {x} is {', '.join(ks)}")

for m in re.finditer(r"class\s+(\w+)\s*\{", t):
    i, depth = m.end(), 1
    while depth and i < len(t):
        depth += {"{": 1, "}": -1}.get(t[i], 0)
        i += 1
    consts = {}
    for c in re.finditer(r"const\s+(?:byte|ushort|int)\s+([^;]+);", t[m.end():i]):
        for a in c.group(1).split(","):
            mm = re.match(r"\s*(\w+)\s*=\s*(\d+)\s*$", a)
            if mm:
                consts[mm.group(1)] = int(mm.group(2))
    ranges = {k[:-5]: (v, consts[k[:-5] + "Last"]) for k, v in consts.items() if k.endswith("First") and k[:-5] + "Last" in consts}
    singles = {k: v for k, v in consts.items() if not k.endswith(("First", "Last")) and k != "Limit"}
    for r, (a, b) in ranges.items():
        for r2, (c, d) in ranges.items():
            if r < r2 and a <= d and c <= b and bool(EXP.search(r)) != bool(EXP.search(r2)):
                found.append(f"{m.group(1)}: {r} {a}-{b} overlaps {r2} {c}-{d}")
        for k, v in singles.items():
            if a <= v <= b and bool(EXP.search(r)) != bool(EXP.search(k)):
                found.append(f"{m.group(1)}: {k} = {v} lies in {r} {a}-{b}")
    if "Limit" in consts:
        top = max([b for _, b in ranges.values()] + list(singles.values()) + [0])
        if top >= consts["Limit"]:
            found.append(f"{m.group(1)}: {top} is at or above Limit {consts['Limit']}")

print("\n".join(found) if found else "clean")
sys.exit(1 if found else 0)
