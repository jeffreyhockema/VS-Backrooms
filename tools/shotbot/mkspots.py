"""Makes the graphics pass's per-level spot lists (review/spots/<level>.json) for tools/shotbot/batch.py.

    python tools/shotbot/mkspots.py discover --build <mods dir> [levels...]   in the client: where /backrooms nearest goes
    python tools/shotbot/mkspots.py make [levels...]                           write the spot lists

Levels by the names players type: 0-11, 6.1, 37, 94, run (Level !), fun, end, hub, 974, 3999, 188 (default: all).

Everything is worked out from the layout harness (`mapgen <seed> <cells> shotgrid <level>`, ShotGrid.cs) at the fixed
seed, so the lists stay valid for the review world (made with that seed by batch.py):
  * anchor: the level's first arrival (the one AT=L<level> uses; the Snackrooms' for 6.1);
  * wide-NN: the best long, furnished views round the anchor, from pick.py's scoring;
  * close-*: the level's most common wall, floor and ceiling and a light fixture, from about 1.5 blocks;
  * <target>-wide / <target>-close: every /backrooms nearest target found from the anchor, from ~6 and ~2 blocks
    (views that are not of an object, such as the castle on the horizon, keep the command's own spot and heading,
    and their -close shot narrows the field of view instead).
The targets come from `discover`, which runs the real command from the anchor in the client (the command needs the
game) and records where it put the player and what it said (review/spots/discovery.json, copied beside the lists in
docs/design/graphics-pass/spots/ so they can be remade without the client). Every spot in the lists is
an absolute /tp, so a list shoots the same frames every time.
Open-sky levels get /time set 12:00 before every shot; Levels 6 and 7 also get -inspection copies (daylight and a lantern in hand).
"""
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import pick  # noqa: E402
import batch  # noqa: E402

SEED = os.environ.get("SEED", "1672613597")
MAPGEN = os.environ.get("MAPGEN", os.path.join(os.environ["TEMP"], "backrooms-build", "mapgen-gfx", "mapgen.exe"))
SPOTS = os.path.join(REPO, "review", "spots")
DOCS = os.path.join(REPO, "docs", "design", "graphics-pass", "spots")
WORK = os.path.join(SPOTS, "_grids")
SPAWN = (512016, 512016)  # the world's default spawn column (ready.txt: spawn 512016.5 217 512016.5)

LEVELS = ["0", "1", "2", "3", "4", "5", "6", "6.1", "7", "8", "9", "10", "11", "37", "94",
          "run", "fun", "end", "hub", "974", "3999", "188"]
HARNESS_NAME = {"run": "!"}
INTERNAL = {"37": 12, "94": 13, "run": 14, "fun": 15, "end": 16, "hub": 17, "974": 18, "3999": 19, "188": 20, "6.1": 6}
OPEN_SKY = {"9", "10", "11", "94"}
NO_CEILING = OPEN_SKY | {"7"}
INSPECTION = {"6", "7"}

GENERIC = ["gate", "threshold", "cache", "refuge", "den", "tent", "sleepingbag"]
SPECIFIC = {
    "0": ["redroom"], "1": ["pipeend"], "2": ["tram", "pipecorner", "pipewrap", "pipeend"],
    "3": ["purpified", "pipecorner", "pipewrap", "pipeend"], "4": ["hotelturn"], "5": ["fronthall", "door666"],
    "6.1": ["vendingroom"], "7": ["seapillar", "shelter"], "8": ["glowcaps"],
    "9": ["l9house", "l9stairs", "streetname", "citysign"], "10": ["fieldthing"], "11": ["billboard", "adpillar"],
    "94": ["castle"], "run": ["runhall"], "fun": ["funparty"], "end": ["endwall", "endexit"],
    "3999": ["foodcourt", "neoncorner"], "188": ["courtdoor", "downpipe"],
}
# Searches that need more than the command's default radius from this seed's anchors
RADIUS = {("3", "pipeend"): 1024, ("6.1", "vendingroom"): 256}
# Targets whose reply gives the heading from the spot it found, and how far ahead along it the thing itself is
AHEAD = {"tent": 3, "tram": 3, "purpified": 2, "fieldthing": 4, "adpillar": 4.24, "l9stairs": 4, "streetname": 4.24,
         "citysign": 3, "endwall": 4, "courtdoor": 8}
# Views rather than things: keep the command's own spot and heading; the -close shot narrows the field of view
VIEWS = {"castle": 3, "billboard": 22, "downpipe": 35, "l9house": 2, "runhall": -4, "funparty": -8, "hotelturn": -4,
         "fronthall": -2, "door666": -3, "endexit": -3, "foodcourt": -6}  # target -> pitch
# How high the middle of the thing is above the floor, to aim at it
HEIGHT = {"seapillar": 3.5, "tram": 1.6, "tent": 0.9, "sleepingbag": 0.2, "cache": 0.5, "gate": 1.5, "threshold": 1.0,
          "den": 0.6, "refuge": 1.0, "redroom": 1.3, "purpified": 1.5, "fieldthing": 1.0, "adpillar": 2.2,
          "streetname": 2.6, "citysign": 2.6, "l9stairs": 2.2, "pipecorner": 2.4, "pipewrap": 2.4, "pipeend": 2.8,
          "neoncorner": 0.3, "glowcaps": 0.3, "shelter": 1.0, "vendingroom": 1.0, "courtdoor": 1.6, "endwall": 1.6}
EYE = 1.62
FLOOR, WALL, DOORWAY, ARCHWIN, ARCHDOOR, PIT, WATER, DOOR, BARS = range(9)
LIGHTS = [1, 2, 6, 7, 8, 58, 21, 4]  # LightOn, LightLit, LightWarm, Chandelier, LampRed, 3999 fluoro, Level ! safe light, LampDim


# ---------------------------------------------------------------- the harness grid

class Grid:
    def __init__(self, level, at=None, cells=10):
        os.makedirs(WORK, exist_ok=True)
        name = HARNESS_NAME.get(level, level)
        args = [MAPGEN, SEED, str(cells), "shotgrid", name] + ([str(at[0]), str(at[1])] if at else [])
        r = subprocess.run(args, cwd=WORK, check=True, capture_output=True, text=True)
        self.info = r.stdout
        m = re.search(r"arrival (\d+) (\d+) ([\d.]+)", r.stdout)
        self.arrival = (int(m.group(1)), int(m.group(2)), float(m.group(3))) if m else None
        d = open(os.path.join(WORK, "shotgrid.bin"), "rb").read()
        self.x0, self.z0, self.size, self.floor_y = struct.unpack_from("<iiii", d, 0)
        self.d = d
        self.level_key = level
        self.level = INTERNAL.get(level, int(level) if level.isdigit() else -1)
        self.snack = level == "6.1"
        # never stand on boxes, props or (sealed) locked rooms; but where the arrival itself is in a sealed room (Level
        # 974's houses are all sealed), sealed rooms are the level
        self.avoid = 1 | 2 | 128
        if self.arrival and (self.tile(self.arrival[0], self.arrival[1]) or {}).get("flags", 0) & 128:
            self.avoid = 1 | 2

    def tile(self, x, z):
        lx, lz = x - self.x0, z - self.z0
        if not (0 <= lx < self.size and 0 <= lz < self.size):
            return None
        o = 16 + (lz * self.size + lx) * 18
        b = self.d[o:o + 18]
        return {"kind": b[0], "floor": b[1], "ceiling": b[2], "flags": b[3], "level": b[4], "pattern": b[5],
                "variant": b[6] | (b[7] << 8), "zone": b[8], "height": b[9], "overhead": b[10], "roof": b[11],
                "depth": b[12], "stair": b[13], "pier": b[14], "pipe": b[15], "feet": (b[16] | (b[17] << 8)) / 100}

    def ours(self, t):
        if t is None or t["level"] != self.level:
            return False
        if self.level == 6:
            return (t["zone"] == 1) == self.snack
        return True

    def passable(self, t):
        return self.ours(t) and t["kind"] in (FLOOR, DOORWAY, ARCHDOOR)

    def standable(self, t):
        return (self.passable(t) and t["kind"] == FLOOR and t["variant"] == 0 and not (t["flags"] & self.avoid)
                and t["stair"] == 0)

    def pick_grid(self):
        """The grid as pick.py reads tiles.bin: (kind, floor, ceiling, flags, level, pattern, variant)."""
        g = {}
        for lz in range(self.size):
            for lx in range(self.size):
                x, z = self.x0 + lx, self.z0 + lz
                t = self.tile(x, z)
                lvl = 0 if self.ours(t) else 255
                flags = t["flags"] & 127
                if t["flags"] & 128 or t["stair"]:
                    flags |= 2  # sealed rooms and stairs: never stand there
                g[(x, z)] = (t["kind"], t["floor"], t["ceiling"], flags, lvl, t["pattern"], min(t["variant"], 255))
        return g


def heading_to(sx, sz, tx, tz):
    return (math.degrees(math.atan2(tx - sx, sz - tz)) + 360) % 360


def step(h):
    return math.sin(math.radians(h)), -math.cos(math.radians(h))


def spot(name, x, y, z, heading, pitch, **kw):
    s = {"name": name, "tp": [round(x, 2), round(y, 2), round(z, 2)], "look": [round(heading) % 360, round(pitch)]}
    s.update(kw)
    return s


def clear_line(g, x0, z0, x1, z1):
    n = int(max(abs(x1 - x0), abs(z1 - z0)) * 3) + 1
    for i in range(n + 1):
        f = i / n
        t = g.tile(int(math.floor(x0 + (x1 - x0) * f)), int(math.floor(z0 + (z1 - z0) * f)))
        if not g.passable(t):
            return False
    return True


# ---------------------------------------------------------------- wide shots

def wide_spots(g, count=8):
    ax, az, _ = g.arrival
    grid = g.pick_grid()
    pick.load = lambda level, cx, cz, n: (grid, (g.x0, g.z0, g.size))
    out = []
    for i, (s, x, z, a, length, props) in enumerate(pick.pick(0, ax, az, count=count)):
        t = g.tile(x, z)
        out.append(spot(f"wide-{i + 1:02d}", x + 0.5, t["feet"], z + 0.5, a, -4, score=round(s, 1)))
    if len(out) < count:
        # small rooms (Level 974's houses, the Snackrooms): pick.py wants rays of 10+ blocks; take the longest there are
        cands = []
        for z in range(az - 64, az + 64, 2):
            for x in range(ax - 64, ax + 64, 2):
                if g.standable(g.tile(x, z)):
                    a = best_ray(g, x + 0.5, z + 0.5)
                    dx, dz = step(a)
                    n = 0
                    while n < 30 and g.passable(g.tile(int(math.floor(x + 0.5 + dx * (n + 1))), int(math.floor(z + 0.5 + dz * (n + 1))))):
                        n += 1
                    if n >= 5:
                        cands.append((n, -(abs(x - ax) + abs(z - az)), x, z, a))
        cands.sort(reverse=True)
        taken = [(sp["tp"][0], sp["tp"][2]) for sp in out]
        for n, _, x, z, a in cands:
            if len(out) >= count:
                break
            if all(abs(x + 0.5 - ox) + abs(z + 0.5 - oz) > 12 for ox, oz in taken):
                out.append(spot(f"wide-{len(out) + 1:02d}", x + 0.5, g.tile(x, z)["feet"], z + 0.5, a, -4, ray=n))
                taken.append((x + 0.5, z + 0.5))
    return out


# ---------------------------------------------------------------- close-ups of the common surfaces

def nearest_first(g, cands):
    ax, az, _ = g.arrival
    return sorted(cands, key=lambda c: (abs(c[0] - ax) + abs(c[1] - az), c[0], c[1]))


def closeups(g):
    ax, az, _ = g.arrival
    r = 72
    walls, floors, ceilings = {}, {}, {}
    stand = []
    for z in range(az - r, az + r):
        for x in range(ax - r, ax + r):
            t = g.tile(x, z)
            if g.standable(t):
                stand.append((x, z))
                floors[t["floor"]] = floors.get(t["floor"], 0) + 1
                ceilings[t["ceiling"]] = ceilings.get(t["ceiling"], 0) + 1
                for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    w = g.tile(x + dx, z + dz)
                    if g.ours(w) and w["kind"] == WALL:
                        walls[w["pattern"]] = walls.get(w["pattern"], 0) + 1
    out = []
    stand = nearest_first(g, stand)
    # walls: the two most common patterns, faced square on from 1.5 blocks, the face three wide
    for rank, (pattern, _) in enumerate(sorted(walls.items(), key=lambda kv: -kv[1])[:2]):
        for x, z in stand:
            found = None
            for h, (dx, dz) in ((0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))):
                mid = g.tile(x + dx, z + dz)
                wall = [g.tile(x + 2 * dx + s * dz, z + 2 * dz + s * dx) for s in (-1, 0, 1)]
                if g.standable(mid) and all(g.ours(w) and w["kind"] == WALL and w["pattern"] == pattern and w["variant"] == 0 for w in wall):
                    found = h
                    break
            if found is not None:
                out.append(spot(f"close-wall{'' if rank == 0 else '2'}", x + 0.5, g.tile(x, z)["feet"], z + 0.5, found, 0,
                                surface=f"wall pattern {pattern}"))
                break
    # floor: the commonest kind, with a 5x5 of it round the spot (or 3x3, or just the spot)
    if floors:
        kind = max(floors.items(), key=lambda kv: kv[1])[0]
        for reach in (2, 1, 0):
            hit = next(((x, z) for x, z in stand if all(g.standable(g.tile(x + dx, z + dz)) and g.tile(x + dx, z + dz)["floor"] == kind
                        for dx in range(-reach, reach + 1) for dz in range(-reach, reach + 1))), None)
            if hit:
                x, z = hit
                out.append(spot("close-floor", x + 0.5, g.tile(x, z)["feet"], z + 0.5, 0, -62, surface=f"floor kind {kind}"))
                break
    # ceiling: the commonest plain kind (not a light), 3x3 of it
    if g.level_key not in NO_CEILING:
        plain = [kv for kv in sorted(ceilings.items(), key=lambda kv: -kv[1]) if kv[0] not in LIGHTS + [5]]
        if plain:
            kind = plain[0][0]
            for x, z in stand:
                if all(g.passable(g.tile(x + dx, z + dz)) and g.tile(x + dx, z + dz)["ceiling"] == kind
                       for dx in range(-1, 2) for dz in range(-1, 2)) and not g.tile(x, z)["flags"] & 64:
                    out.append(spot("close-ceiling", x + 0.5, g.tile(x, z)["feet"], z + 0.5, 0, 62, surface=f"ceiling kind {kind}"))
                    break
    # water, where a level has much of it (Level 7's sea, Level 37's pools): from the shore, looking down into it
    waters = [(x, z) for x, z in stand if any(g.ours(g.tile(x + dx, z + dz)) and g.tile(x + dx, z + dz)["kind"] == WATER
                                              for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    if len(waters) > 20:
        x, z = waters[0]
        for h, (dx, dz) in ((0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))):
            w = g.tile(x + dx, z + dz)
            if g.ours(w) and w["kind"] == WATER:
                out.append(spot("close-water", x + 0.5, g.tile(x, z)["feet"], z + 0.5, h, -45, surface="water"))
                break
    # props: the two commonest things standing on the floor (crops, furniture, clutter), from 1.5 blocks
    props = {}
    for z in range(az - r, az + r):
        for x in range(ax - r, ax + r):
            t = g.tile(x, z)
            if g.passable(t) and t["kind"] == FLOOR and t["variant"]:
                props.setdefault(t["variant"], []).append((x, z))
    for rank, (variant, where) in enumerate(sorted(props.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:2]):
        done = False
        for px, pz in nearest_first(g, where):
            for h, (dx, dz) in ((0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))):
                sx, sz = px - dx, pz - dz
                if g.standable(g.tile(sx, sz)):
                    out.append(spot(f"prop-{rank + 1}", sx + 0.5, g.tile(sx, sz)["feet"], sz + 0.5, h, -32,
                                    surface=f"floor prop variant {variant}"))
                    done = True
                    break
            if done:
                break
    # a light: the first of the usual fixtures found near the anchor, looked up at from beside it
    tall = 4 if g.level_key == "1" else 3
    for light in LIGHTS:
        done = False
        cands = [(x, z) for z in range(az - r, az + r) for x in range(ax - r, ax + r)
                 if g.passable(g.tile(x, z)) and g.tile(x, z)["ceiling"] == light]
        for lx, lz in nearest_first(g, cands):
            t = g.tile(lx, lz)
            height = tall + (1 if t["flags"] & 64 else 0)
            back = 2 if height >= 4 else 1
            for h, (dx, dz) in ((0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))):
                sx, sz = lx - back * dx, lz - back * dz
                if g.standable(g.tile(sx, sz)) and clear_line(g, sx + 0.5, sz + 0.5, lx + 0.5, lz + 0.5):
                    pitch = math.degrees(math.atan2(height - EYE - 0.1, back))
                    out.append(spot("close-light", sx + 0.5, g.tile(sx, sz)["feet"], sz + 0.5, h, pitch,
                                    surface=f"ceiling light kind {light}"))
                    done = True
                    break
            if done:
                break
        if done:
            break
    return out


# ---------------------------------------------------------------- /backrooms nearest targets

def parse_discovery(chat):
    """chat.txt from the discovery run -> {level: {target: {...}}}: what each nearest said and where it left you."""
    result = {}
    pending = []
    for line in chat.splitlines():
        if line.startswith("#mark "):
            parts = line.split()
            name = parts[1]
            if "|" in name:
                level, target = name.split("|")
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                reply = next((p for p in pending if "blocks from where you were" in p), None) or next(
                    (p for p in reversed(pending) if not p.startswith(("Ok, teleported", "Screenshot", "Teleported", "For help"))), "")
                result.setdefault(level, {})[target] = {"stand": [x, y, z], "reply": reply}
            pending = []
        else:
            pending.append(line.strip())
    return result


def discover_commands(levels):
    lines = list(batch.HEADER)
    for key in levels:
        g = Grid(key, cells=3)
        ax, az, ay = g.arrival
        lines.append(f"# ===== level {key}: anchor {ax} {az}")
        lines += [f"tp {ax + 0.5} {ay} {az + 0.5}", "ready 48", "wait 1500", f"mark {key}|anchor"]
        for target in GENERIC + SPECIFIC.get(key, []):
            lines += [f"tp {ax + 0.5} {ay} {az + 0.5}", "ready 32",
                      f"cmd /backrooms nearest {target}" + (f" {RADIUS[(key, target)]}" if (key, target) in RADIUS else ""),
                      "waitchat 120000", "wait 1500", "ready 32", "wait 500",
                      f"mark {key}|{target}"]
    lines += ["wait 2000", "mark __end__"]
    return lines


def found_point(reply):
    """The point the command found, from its reply's '(x, z)' relative to spawn (rounded half away from zero)."""
    m = re.search(r"\((-?\d+), (-?\d+)\)\s*$", reply)
    if not m:
        return None
    def back(v, s):
        return s + v + (1 if v < 0 else 0)
    return back(int(m.group(1)), SPAWN[0]), back(int(m.group(2)), SPAWN[1])


def target_spots(key, disc):
    out = []
    for target, rec in disc.items():
        if target == "anchor":
            continue
        reply = rec["reply"]
        if "blocks from where you were" not in reply:
            continue  # not in this level, or nothing within the command's radius
        sx, sy, sz = rec["stand"]
        hm = re.search(r"heading (\d+)", reply)
        heading = float(hm.group(1)) if hm else None
        om = re.search(r"(-?\d+), (-?\d+) away", reply)
        tx = tz = None
        if target in VIEWS:
            if heading is None:
                g = Grid(key, at=(int(sx), int(sz)), cells=3)
                heading = best_ray(g, sx, sz)
            pitch = VIEWS[target]
            out.append(spot(f"{target}-wide", sx, sy, sz, heading, pitch, target=target))
            out.append(spot(f"{target}-close", sx, sy, sz, heading, pitch, fov=35, target=target))
            continue
        if om and heading is not None:
            tx, tz = math.floor(sx) + int(om.group(1)) + 0.5, math.floor(sz) + int(om.group(2)) + 0.5
        elif heading is not None and target in AHEAD:
            fp = found_point(reply)
            bx, bz = (fp[0] + 0.5, fp[1] + 0.5) if fp else (sx, sz)
            dx, dz = step(heading)
            tx, tz = bx + dx * AHEAD[target], bz + dz * AHEAD[target]
        else:
            fp = found_point(reply)
            if fp:
                tx, tz = fp[0] + 0.5, fp[1] + 0.5
        if tx is None:
            print(f"  {key} {target}: cannot place it from '{reply}'")
            continue
        g = Grid(key, at=(int(math.floor(tx)), int(math.floor(tz))), cells=3)
        if g.level == 6:  # (a Level 6 refuge can be a Snackrooms cell)
            g.snack = (g.tile(int(math.floor(tx)), int(math.floor(tz))) or {}).get("zone") == 1
        if math.hypot(tx - sx, tz - sz) > 0.7:
            back_h = heading_to(tx, tz, sx, sz)  # from the thing back toward where the command stood you
        else:
            back_h = best_ray(g, sx, sz)  # standing on it: back off down the longest open line, and look back at it
        th = HEIGHT.get(target, 1.0)
        for label, want in (("wide", 6.0), ("close", 2.0)):
            cam = place_camera(g, tx, tz, back_h, want, sx, sz)
            if cam is None:
                print(f"  {key} {target}: no {label} spot")
                continue
            cx, cz = cam
            dist = math.hypot(tx - cx, tz - cz)
            feet = g.tile(int(math.floor(cx)), int(math.floor(cz)))["feet"]
            floor_t = g.tile(int(math.floor(tx)), int(math.floor(tz)))
            tfeet = floor_t["feet"] if floor_t and floor_t["level"] == g.level else feet
            pitch = math.degrees(math.atan2((tfeet + th) - (feet + EYE), max(dist, 0.5)))
            extra = {}
            wide = out[-1] if out and out[-1]["name"] == f"{target}-wide" else None
            if label == "close" and wide and math.hypot(wide["tp"][0] - cx, wide["tp"][2] - cz) < 1.0:
                extra["fov"] = 40  # no nearer place to stand: a narrower view from the same spot instead
            out.append(spot(f"{target}-{label}", cx, feet, cz, heading_to(cx, cz, tx, tz), max(-45, min(45, pitch)), **extra,
                            target=target, distance=round(dist, 1)))
    return out


def best_ray(g, x, z):
    best = (0, 0)
    for a in range(0, 360, 15):
        dx, dz = step(a)
        n = 0
        while n < 30 and g.passable(g.tile(int(math.floor(x + dx * (n + 1))), int(math.floor(z + dz * (n + 1))))):
            n += 1
        if n > best[0]:
            best = (n, a)
    return best[1]


def camera_back(g, tx, tz, h, want, least=1.5):
    """A standable spot as near `want` blocks from the thing at (tx, tz) as there is (no nearer than `least`), going
    out along heading h, with a clear line to it; or None."""
    dx, dz = step(h)
    for d in [want - k * 0.5 for k in range(int((want - least) / 0.5) + 1)]:
        cx, cz = tx + dx * d, tz + dz * d
        t = g.tile(int(math.floor(cx)), int(math.floor(cz)))
        if g.standable(t) and clear_line(g, cx, cz, tx + dx * 0.6, tz + dz * 0.6):
            return cx, cz
    return None


def place_camera(g, tx, tz, back_h, want, sx, sz):
    """Out along back_h if it can be done; else the nearest way round to it that reaches at least half as far (the
    wide shot) or any way (the close one); else the spot the command chose."""
    order = sorted(range(0, 360, 15), key=lambda h: (abs((h - back_h + 180) % 360 - 180), h))
    for least in ((want * 0.6, 1.5) if want > 3 else (1.5,)):
        for h in [back_h] + order:
            cam = camera_back(g, tx, tz, h, want, least)
            if cam is not None:
                return cam
    if math.hypot(tx - sx, tz - sz) >= 1.0:
        return sx, sz
    return None


# ---------------------------------------------------------------- main

def make(levels):
    disc = {}
    # what discover found (kept beside the lists in docs/, so the lists can be remade without the client)
    p = next((q for q in (os.path.join(SPOTS, "discovery.json"), os.path.join(DOCS, "discovery.json")) if os.path.exists(q)), None)
    if p:
        disc = json.load(open(p, encoding="utf-8"))
    os.makedirs(DOCS, exist_ok=True)
    summary = []
    for key in levels:
        g = Grid(key, cells=10)
        ax, az, ay = g.arrival
        spots = wide_spots(g) + closeups(g) + target_spots(key, disc.get(key, {}))
        names = set()
        for s in spots:
            assert s["name"] not in names, s["name"]
            names.add(s["name"])
        if key in OPEN_SKY:
            for s in spots:
                s["pre"] = ["/time set 12:00"]  # (VS 1.22 has no "noon": lunch, day, ... or hh:mm)
        if key in INSPECTION:
            extra = []
            for s in spots:
                if s["name"].startswith(("wide-01", "wide-02", "wide-03", "wide-04", "close-")) or s["name"].endswith("-close"):
                    extra.append(dict(s, name=s["name"] + "-inspection", inspection=True))
            spots += extra
        doc = {"level": key, "seed": int(SEED), "anchor": [ax + 0.5, ay, az + 0.5],
               "made_by": "tools/shotbot/mkspots.py make", "spots": spots}
        for folder in (SPOTS, DOCS):
            with open(os.path.join(folder, f"{key}.json"), "w", encoding="utf-8") as f:
                f.write(dump(doc))
        kinds = {"wide": sum(s["name"].startswith("wide-") for s in spots),
                 "close": sum(s["name"].startswith("close-") and not s.get("inspection") for s in spots),
                 "prop": sum(s["name"].startswith("prop-") and not s.get("inspection") for s in spots),
                 "target": sum("target" in s and not s.get("inspection") for s in spots),
                 "inspection": sum(bool(s.get("inspection")) for s in spots)}
        kinds["wide"] -= sum(s["name"].startswith("wide-") and bool(s.get("inspection")) for s in spots)
        summary.append((key, len(spots), kinds))
        print(f"level {key}: {len(spots)} spots {kinds}")
    return summary


def dump(doc):
    """JSON with one spot per line, so the lists diff well."""
    head = {k: v for k, v in doc.items() if k != "spots"}
    lines = ["{"] + [f'  {json.dumps(k)}: {json.dumps(v)},' for k, v in head.items()] + ['  "spots": [']
    lines += [("    " + json.dumps(s, ensure_ascii=False) + ("," if i < len(doc["spots"]) - 1 else "")) for i, s in enumerate(doc["spots"])]
    lines += ["  ]", "}"]
    return "\n".join(lines) + "\n"


def discover(levels, build):
    data = batch.DEFAULT_DATA
    batch.ensure_data_dir(data)
    batch.ensure_world(data, "gfxreview", build, SEED)
    batch.ensure_shotbot(build)
    lines = discover_commands(levels)
    botdir = os.path.join(data, "shotbot-run")
    proc, ok = batch.run_client(lines, data, build, "gfxreview", botdir)
    chat = batch.read(os.path.join(botdir, "chat.txt"))
    os.makedirs(SPOTS, exist_ok=True)
    shutil.copyfile(os.path.join(botdir, "chat.txt"), os.path.join(SPOTS, "discovery-chat.txt"))
    found = parse_discovery(chat)
    p = os.path.join(SPOTS, "discovery.json")
    old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    old.update(found)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(old, f, indent=1)
    os.makedirs(DOCS, exist_ok=True)
    shutil.copyfile(p, os.path.join(DOCS, "discovery.json"))
    batch.close_client(proc, botdir)
    for key in levels:
        for target, rec in found.get(key, {}).items():
            print(f"{key:5} {target:12} {rec['stand']}  {rec['reply']}")
    return ok


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("discover", "make"):
        sys.exit(__doc__)
    args = sys.argv[2:]
    build = None
    if "--build" in args:
        i = args.index("--build")
        build = os.path.abspath(args[i + 1])
        del args[i:i + 2]
    levels = args or LEVELS
    if sys.argv[1] == "discover":
        if not build:
            sys.exit("discover needs --build <mods dir>")
        discover(levels, build)
    else:
        make(levels)
