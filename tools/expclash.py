"""Experimental levels: finds a value an experimental level shares with main or with another experimental level.

    python tools/expclash.py

Reads src/Worldgen/Tiles.cs. Reports (1) an enum value held by both an experimental name (L73, Basement, L52, L31,
L120, L36, L15, L23, L14, L47) and another name, or by two experimental levels, (2) a First/Last range of one side overlapping a
range or constant of the other (or of another experimental level), (3) a constant at or above its table's Limit, (4) an
experimental enum member, constant or range outside its own level's reserved block (RESERVED below, the table in
docs/design/experimental-levels/README.md) and the values it kept from before the widening (KEPT). Main's values are
released and never move: renumber the experimental side. Prints nothing but "clean" when there is nothing to fix;
exits 1 otherwise.
"""
import os
import re
import sys

LEVELS = ["L73", "Basement", "L52", "L31", "L120", "L36", "L15", "L23", "L14", "L47"]
EXP = re.compile(r"^(?:" + "|".join(LEVELS) + r")(?![0-9])")


def level_of(name):
    m = EXP.match(name)
    return m.group(0) if m else None


# One block of 32 per level past 255 in every widened table (in the order of LEVELS); Props one block of 100 from 700.
BLOCK32 = {lv: (256 + 32 * k, 287 + 32 * k) for k, lv in enumerate(LEVELS)}
PROPS = {"L31": (700, 799), "L120": (800, 899), "L73": (900, 999), "Basement": (1000, 1099), "L52": (1100, 1199),
         "L36": (1200, 1299), "L15": (1300, 1399), "L23": (1400, 1499), "L14": (1500, 1599), "L47": (1600, 1699)}
RESERVED = {"WallPattern": BLOCK32, "FloorKind": BLOCK32, "CeilingKind": BLOCK32, "Unders": BLOCK32, "Overheads": BLOCK32,
            "Pipes": BLOCK32, "Decor": BLOCK32, "Props": PROPS}
# Values kept from before the widening, outside the blocks (theirs; never reuse them for anything else)
KEPT = {
    "WallPattern": {"L52": [(224, 224)], "L31": [(240, 240)], "L120": [(242, 242)]},
    "FloorKind": {"Basement": [(228, 231)], "L52": [(244, 248)], "L31": [(249, 249)], "L120": [(251, 251)]},
    "CeilingKind": {"L52": [(88, 88)], "L31": [(96, 96)], "L120": [(112, 112)]},
    "Overheads": {"L31": [(140, 149)], "L120": [(160, 169)]},
    "Pipes": {"L120": [(140, 149)]},
}


def allowed(table, lv, a, b):
    spans = [RESERVED[table][lv]] + KEPT.get(table, {}).get(lv, [])
    return any(lo <= a and b <= hi for lo, hi in spans)


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
        if any(level_of(k) for k in ks) and any(not level_of(k) for k in ks):
            found.append(f"enum {m.group(1)}: {x} is {', '.join(ks)}")
        elif len({level_of(k) for k in ks}) > 1:
            found.append(f"enum {m.group(1)}: {x} is {', '.join(ks)} (two experimental levels)")
    if m.group(1) in RESERVED:
        for k, x in vals.items():
            lv = level_of(k)
            if lv and not allowed(m.group(1), lv, x, x):
                found.append(f"enum {m.group(1)}: {k} = {x} is outside {lv}'s block {RESERVED[m.group(1)][lv]}")

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
            if r < r2 and a <= d and c <= b:
                l1, l2 = level_of(r), level_of(r2)
                if bool(l1) != bool(l2) or (l1 and l2 and l1 != l2):
                    found.append(f"{m.group(1)}: {r} {a}-{b} overlaps {r2} {c}-{d}")
        for k, v in singles.items():
            if a <= v <= b and level_of(r) != level_of(k):
                found.append(f"{m.group(1)}: {k} = {v} lies in {r} {a}-{b}")
    if m.group(1) in RESERVED:
        for r, (a, b) in ranges.items():
            lv = level_of(r)
            if lv and not allowed(m.group(1), lv, a, b):
                found.append(f"{m.group(1)}: {r}First/Last {a}-{b} is outside {lv}'s block {RESERVED[m.group(1)][lv]}")
        for k, v in singles.items():
            lv = level_of(k)
            if lv and not allowed(m.group(1), lv, v, v):
                found.append(f"{m.group(1)}: {k} = {v} is outside {lv}'s block {RESERVED[m.group(1)][lv]}")
    if "Limit" in consts:
        top = max([b for _, b in ranges.values()] + list(singles.values()) + [0])
        if top >= consts["Limit"]:
            found.append(f"{m.group(1)}: {top} is at or above Limit {consts['Limit']}")

print("\n".join(found) if found else "clean")
sys.exit(1 if found else 0)
