"""Generates the 3D block models (shapes) for pipes, light fixtures and props.

Models are built from boxes in block space (0-16 per axis); helpers mirror and rotate boxes so that, for
example, wall pipes can stick out of all four faces of a wall block. Run from the repo root:

    python tools/gen_shapes.py
"""
import json
import math
import os

import modelkit as K

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "shapes", "block")

DIRS = ("north", "east", "south", "west", "up", "down")


def box(name, frm, to, tex, glow=0, faces=DIRS):
    """A box with UVs taken from its own size, so textures keep a consistent scale."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, d = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)

    def uv(a, b):
        a, b = max(a, 0.5), max(b, 0.5)
        return [0, 0, min(16, a), min(16, b)]

    sizes = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}
    out = {}
    for f in faces:
        face = {"texture": "#" + tex, "uv": uv(*sizes[f])}
        if glow:
            face["glow"] = glow
        out[f] = face
    return {"name": name, "from": [x1, y1, z1], "to": [x2, y2, z2], "faces": out}


def pipe(name, frm, to, tex, faces=("north", "south", "up", "down")):
    """A horizontal pipe along X: its side faces stretch one shaded band of the pipe texture (8 units) over its
    height, whatever that is, so it reads as round; its top shows the highlight and its underside the shadow."""
    b = box(name, frm, to, tex, faces=faces)
    w = abs(to[0] - frm[0])
    for f, uv in (("north", [0, 0, w, 8]), ("south", [0, 0, w, 8]), ("up", [0, 1.5, w, 3.5]), ("down", [0, 6.5, w, 8])):
        if f in b["faces"]:
            b["faces"][f]["uv"] = uv
    return b


def rot(b, times):
    """Rotates a box 90 degrees clockwise (seen from above) around the block centre, `times` times."""
    b = json.loads(json.dumps(b))
    for _ in range(times % 4):
        (x1, y1, z1), (x2, y2, z2) = b["from"], b["to"]
        nx1, nz1 = 16 - z2, x1
        nx2, nz2 = 16 - z1, x2
        b["from"], b["to"] = [nx1, y1, nz1], [nx2, y2, nz2]
        f = b["faces"]
        b["faces"] = {k: v for k, v in {
            "east": f.get("north"), "south": f.get("east"), "west": f.get("south"), "north": f.get("west"),
            "up": f.get("up"), "down": f.get("down"),
        }.items() if v is not None}
    return b


def all_sides(boxes):
    """Copies boxes that stick out of the north face onto all four faces."""
    out = []
    for i in range(4):
        out += [dict(rot(b, i), name=f"{b['name']}{i}") for b in boxes]
    return out


def save(name, textures, elements, compact=False):
    os.makedirs(OUT, exist_ok=True)
    shape = {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": elements}
    with open(os.path.join(OUT, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(shape, f, **({"separators": (",", ":")} if compact else {"indent": 1}))


CUBE = lambda tex: box("Cube", (0, 0, 0), (16, 16, 16), tex)

PIPE_TEX = {
    "rust": "backrooms:block/level2/pipe-rust",
    "lagging": "backrooms:block/level2/pipe-lagging",
    "red": "backrooms:block/level2/pipe-red",
    "metal": "backrooms:block/props/metal",
    "dark": "backrooms:block/props/metal-dark",
}
# The round pipes along the walls (see round_pipe)
WALL_PIPE_TEX = {
    "wallrust": "backrooms:block/level2/wallpipe-rust",
    "walllag": "backrooms:block/level2/wallpipe-lagging",
    "flange": "backrooms:block/level2/wallpipe-flange",
}


# ---------------- Level 2 pipe bundles (in the top block of a tunnel, along X) ----------------

def bundle_x():
    return [
        pipe("Lagged", (0, 10, 1), (16, 15, 6), "lagging"),
        pipe("Rusty", (0, 11, 10), (16, 14, 13), "rust"),
        pipe("FireLine", (0, 13.5, 13.5), (16, 15.5, 15.5), "red"),
        box("Strap", (7.5, 15, 0.5), (8.5, 16, 15.55), "metal"),  # (proud of the fire line's side, not in its plane)
        box("Hanger1", (7.5, 9.5, 0.5), (8.5, 15, 1), "metal"),
        box("Hanger2", (7.5, 10.5, 13), (8.5, 14, 13.5), "metal"),
    ]


def bundle_z():
    return [dict(rot(b, 1), name=b["name"] + "Z") for b in bundle_x()]


def fixture_x(tube_tex):
    return [
        box("Housing", (1, 14, 6.5), (15, 16, 9.5), "metal"),
        box("Tube", (1, 13.3, 7), (15, 14, 9), tube_tex, glow=0 if tube_tex == "tubeoff" else 255, faces=("north", "south", "down", "east", "west")),
    ]


def round_pipe(name, yc, zc, r, tex, x1=0.0, x2=16.0, shaded=True, faces=None):
    """A pipe along X in front of a wall (on the north side), round in section: seven slabs stepped like a circle of
    radius `r` about (yc, zc). With `shaded`, each slab's front takes the band of a wall-pipe texture (U along the
    pipe, V once round it from its top to its underside) that its part of the circle stands for, and the step on its
    top or underside the texels at its own edge (the game lights tops brighter and undersides darker already), so the
    light falls round the pipe instead of across a box."""
    cuts = (-1.0, -0.86, -0.6, -0.28, 0.28, 0.6, 0.86, 1.0)

    def v(f):
        return round(16 * (0.5 - math.asin(max(-1.0, min(1.0, f))) / math.pi), 3)
    out = []
    for i in range(len(cuts) - 1):
        lo, hi = cuts[i], cuts[i + 1]
        mid = 0.0 if lo < 0 < hi else (abs(lo) + abs(hi)) / 2
        d = r * math.sqrt(1 - mid * mid)
        fs = ["north"] + (["up"] if hi > 0 else []) + (["down"] if lo < 0 else [])
        if faces:
            fs += [f for f in faces if f not in fs]
        b = box(f"{name}{i}", (x1, yc + lo * r, zc - d), (x2, yc + hi * r, zc + d), tex, faces=tuple(fs))
        if shaded:
            b["faces"]["north"]["uv"] = [x1, v(hi), x2, v(lo)]
            if "up" in b["faces"]:
                b["faces"]["up"]["uv"] = [x1, 0, x2, 1.2] if hi >= 1 else [x1, v(hi), x2, v(hi) + 0.3]
            if "down" in b["faces"]:
                b["faces"]["down"]["uv"] = [x1, 14.8, x2, 16] if lo <= -1 else [x1, v(lo) - 0.3, x2, v(lo)]
            for f in ("east", "west"):
                if f in b["faces"]:
                    b["faces"][f]["uv"] = [7, 7, 9, 9]
        out.append(b)
    return out


def round_riser(name, xc, zc, r, tex, y1=0.0, y2=16.0, shaded=True, faces=None):
    """(B6) round_pipe stood upright in front of a wall's north face: seven slabs stepped like a circle of radius `r`
    about (xc, zc) across X, from y1 to y2. With `shaded`, each slab's front takes the band of a riser texture (the
    wall-pipe skin turned: U once round the pipe from its east side, the lit one, to its west; V along it, following
    the block height so a riser runs on from block to block) that its part of the circle stands for."""
    cuts = (-1.0, -0.86, -0.6, -0.28, 0.28, 0.6, 0.86, 1.0)

    def u(f):  # f = +1 at the east side (x high), seen from the north on the viewer's left
        return round(16 * (0.5 - math.asin(max(-1.0, min(1.0, f))) / math.pi), 3)
    out = []
    for i in range(len(cuts) - 1):
        lo, hi = cuts[i], cuts[i + 1]
        mid = 0.0 if lo < 0 < hi else (abs(lo) + abs(hi)) / 2
        d = r * math.sqrt(1 - mid * mid)
        fs = ["north"] + (["east"] if hi > 0 else []) + (["west"] if lo < 0 else [])
        if faces:
            fs += [f for f in faces if f not in fs]
        b = box(f"{name}{i}", (xc + lo * r, y1, zc - d), (xc + hi * r, y2, zc + d), tex, faces=tuple(fs))
        if shaded:
            v1, v2 = 16 - y2, 16 - y1
            b["faces"]["north"]["uv"] = [u(hi), v1, u(lo), v2]
            if "east" in b["faces"]:
                b["faces"]["east"]["uv"] = [0, v1, 1.2, v2] if hi >= 1 else [u(hi), v1, u(hi) + 0.3, v2]
            if "west" in b["faces"]:
                b["faces"]["west"]["uv"] = [14.8, v1, 16, v2] if lo <= -1 else [u(lo) - 0.3, v1, u(lo), v2]
            for f in ("up", "down"):
                if f in b["faces"]:
                    b["faces"][f]["uv"] = [7, 7, 9, 9]
        out.append(b)
    return out


# Horizontal pipes bolted to a wall: a rust-red steel pipe above, a canvas-lagged one below, both round and standing
# half a pixel off the wall. Plain lengths; "joint" has the steel pipe's flanged joint (bolted flanges with a gasket
# between) and a cladding band round the lagging; "bracket" a channel strut on the wall with a clamp round each pipe.
# The generator puts a joint every four blocks along a wall and a bracket half way between.
# The straight blocks carry the pipes on all four faces, so the runs on faces that are not open lie inside the next
# wall block. Their ends have no faces: an end face there lies exactly on that wall's face where it shows round a
# corner (two pipe-coloured discs fighting with the wall), and on an open face the run always goes on into the next
# block's pipe, or into a wall in an inner corner, so an end face is never seen.
WALL_PIPE_RUST = (12.0, -2.0, 1.5)    # centre y, centre z, radius
WALL_PIPE_LAG = (4.5, -2.25, 1.75)
WALL_PIPES = (round_pipe("PipeA", *WALL_PIPE_RUST, "wallrust")
              + round_pipe("PipeB", *WALL_PIPE_LAG, "walllag"))


def wall_pipe_joint():
    yc, zc, r = WALL_PIPE_RUST
    out = []
    for i, (x1, x2) in enumerate(((6.9, 7.65), (8.35, 9.1))):
        out += round_pipe(f"Flange{i}", yc, zc, r + 0.75, "flange", x1, x2, shaded=False, faces=("east", "west"))
    out += round_pipe("Gasket", yc, zc, r + 0.45, "dark", 7.65, 8.35, shaded=False)
    for i, a in enumerate((60, 20, -20, -60)):
        y, z = yc + (r + 0.42) * math.sin(math.radians(a)), zc - (r + 0.42) * math.cos(math.radians(a))
        out.append(box(f"Bolt{i}", (6.5, y - 0.25, z - 0.25), (9.5, y + 0.25, z + 0.25), "metal"))
    ly, lz, lr = WALL_PIPE_LAG
    out += round_pipe("Cladding", ly, lz, lr + 0.25, "metal", 7.4, 8.6, shaded=False, faces=("east", "west"))
    return out


def wall_pipe_bracket():
    out = [box("Strut", (7.25, 1.5, -0.7), (8.75, 15.5, 0), "flange", faces=("north", "east", "west", "up", "down"))]
    for nm, (yc, zc, r) in (("ClampA", WALL_PIPE_RUST), ("ClampB", WALL_PIPE_LAG)):
        out += round_pipe(nm, yc, zc, r + 0.3, "flange", 7.55, 8.45, shaded=False, faces=("east", "west"))
    return out


# ---------------- Wall pipes round corners and at the ends of a run ----------------
# A wall block carrying the pipes has a pipe along each face that looks into the open. Where a run reaches the end of
# a face it either runs on into the next block (the straight blocks above), or the block is one of these, named
# "<faces>-<corners>": the faces that look into the open (of "nesw"), then what happens at each corner in turn (north-
# east, south-east, south-west, north-west): "o" nothing (the run goes on into the next block), "w" the run turns the
# outer corner (both faces at that corner are open), "c" a blind flange ends it (the next wall carries no pipes, or a
# door, or it runs into a bare wall in an inner corner), "j" it stops against the pipe coming out of an inner corner (the
# wall it runs into carries the pipes too). Seen from the open side, going along a face with the wall on your right,
# a face's run starts at its "left" corner and ends at its "right" one; a face's right corner is the one with its own
# number (north: north-east), so corner c joins face c's right end to face c+1's left end.

def wall_pipe_turning(name, yc, zc, r, tex, left, right):
    """One wall pipe along the north face (as round_pipe), its ends shaped for its corners: the right end "w" runs
    on round the outer corner as far as the far side of the next face's pipe, its end shaded as that pipe's front,
    and the left end "w" starts behind the previous face's turning pipe (so the two make a mitred elbow); the right end
    "j" stops at the front of the pipe it meets in an inner corner. Parts outside the block keep their UVs in 0-16."""
    cuts = (-1.0, -0.86, -0.6, -0.28, 0.28, 0.6, 0.86, 1.0)
    a = -zc  # how far the pipe's axis stands off the wall

    def v(f):
        return round(16 * (0.5 - math.asin(max(-1.0, min(1.0, f))) / math.pi), 3)
    out = []
    for i in range(len(cuts) - 1):
        lo, hi = cuts[i], cuts[i + 1]
        mid = 0.0 if lo < 0 < hi else (abs(lo) + abs(hi)) / 2
        d = r * math.sqrt(1 - mid * mid)
        x1 = round(d - a, 3) if left == "w" else round(16 - elbow_x(r) - ELBOW_CHAMFER * d, 3) if left == "c" else 0.0
        x2 = (round(16 + a + d, 3) if right == "w" else round(16 - a - d, 3) if right == "j"
              else round(elbow_x(r) + ELBOW_CHAMFER * d, 3) if right == "c" else 16.0)
        # The block's own part, and what reaches past its edges round an outer corner
        for part, p, q in (("L", x1, 0.0), ("", max(x1, 0.0), min(x2, 16.0)), ("R", 16.0, x2)):
            if q - p < 0.01:
                continue
            fs = ["north"] + (["up"] if hi > 0 else []) + (["down"] if lo < 0 else [])
            # Only the end of a turn shows; "o" runs on into the next block's pipe (as the straight blocks) and a
            # blind flange covers "c" (an end face there would fight with the flange's face in the same plane)
            if q == x2 and right in ("w", "c"):
                fs.append("east")
            if p == x1 and left == "c":
                fs.append("west")
            b = box(f"{name}{part}{i}", (p, yc + lo * r, zc - d), (q, yc + hi * r, zc + d), tex, faces=tuple(fs))
            u1, u2 = (p + 16, q + 16) if part == "L" else (p - 16, q - 16) if part == "R" else (p, q)
            b["faces"]["north"]["uv"] = [u1, v(hi), u2, v(lo)]
            if "up" in b["faces"]:
                b["faces"]["up"]["uv"] = [u1, 0, u2, 1.2] if hi >= 1 else [u1, v(hi), u2, v(hi) + 0.3]
            if "down" in b["faces"]:
                b["faces"]["down"]["uv"] = [u1, 14.8, u2, 16] if lo <= -1 else [u1, v(lo) - 0.3, u2, v(lo)]
            if "east" in b["faces"]:
                # Round an outer corner the end is the front of the turn: shaded like the next face's pipe
                b["faces"]["east"]["uv"] = [0, v(hi), round(2 * d, 3), v(lo)] if right == "w" else [7, 7, 9, 9]
            if "west" in b["faces"]:
                b["faces"]["west"]["uv"] = [7, 7, 9, 9]
            out.append(b)
    return out


ELBOW_CHAMFER = 0.7  # the elbow's outer corner is cut: the pipe's round end steps in over this fraction of its radius
ELBOW_PLATE = 1.1    # the escutcheon plate stands this far out round the pipe


def elbow_x(r):
    """Where the elbow into the wall sits along a pipe of radius r that ends at a block's right edge: its escutcheon
    plate (radius r + ELBOW_PLATE) stops 0.05 short of the edge (four-sided hardware, as the straight blocks' flanges)."""
    return round(15.95 - (r + ELBOW_PLATE), 3)


def wall_pipe_cap(name, end):
    """(Level 2 art) Where a wall pipe's run ends, it turns 90 degrees into the wall instead of ending in a blind
    flange: the pipe runs on to the elbow's centre, its outer corner cut (`wall_pipe_turning` shortens it), a short
    stepped knuckle carries on to the wall, and a round escutcheon plate with four bolt heads covers where it goes in.
    The plate's back is cut flat a hair in front of the wall (else its face lies in the wall's own plane where that
    shows, beside a door). "right" ends the run at x 16, "left" is that mirrored."""
    out = []
    cuts = (-1.0, -0.86, -0.6, -0.28, 0.28, 0.6, 0.86, 1.0)

    def v(f):
        return round(16 * (0.5 - math.asin(max(-1.0, min(1.0, f))) / math.pi), 3)
    for nm, (yc, zc, r), tex in (("A", WALL_PIPE_RUST, "wallrust"), ("B", WALL_PIPE_LAG, "walllag")):
        xe, pr = elbow_x(r), r + ELBOW_PLATE
        for i in range(len(cuts) - 1):
            lo, hi = cuts[i], cuts[i + 1]
            mid = 0.0 if lo < 0 < hi else (abs(lo) + abs(hi)) / 2
            d = r * math.sqrt(1 - mid * mid)
            # the knuckle: the step the pipe's end gives up to its cut corner, running on to the plate
            p, q = round(xe + ELBOW_CHAMFER * d, 3), round(xe + d, 3)
            fs = ["north", "east"] + (["up"] if hi > 0 else []) + (["down"] if lo < 0 else [])
            b = box(f"{name}K{nm}{i}", (p, yc + lo * r, zc - ELBOW_CHAMFER * d), (q, yc + hi * r, -0.3), tex, faces=tuple(fs))
            b["faces"]["north"]["uv"] = [p, v(hi), q, v(lo)]
            if "up" in b["faces"]:
                b["faces"]["up"]["uv"] = [p, 0, q, 1.2] if hi >= 1 else [p, v(hi), q, v(hi) + 0.3]
            if "down" in b["faces"]:
                b["faces"]["down"]["uv"] = [p, 14.8, q, 16] if lo <= -1 else [p, v(lo) - 0.3, q, v(lo)]
            b["faces"]["east"]["uv"] = [7, 7, 9, 9]
            out.append(b)
        # a union ring behind the bend marks it as a fitting
        out += round_pipe(f"{name}Ring{nm}", yc, zc, r + 0.35, "flange", round(xe - r - 0.5, 3), round(xe - r + 0.4, 3),
                          shaded=False, faces=("east", "west"))
        # the plate, a stepped disc on the wall, and its bolts
        for i in range(len(cuts) - 1):
            lo, hi = cuts[i], cuts[i + 1]
            mid = 0.0 if lo < 0 < hi else (abs(lo) + abs(hi)) / 2
            d = pr * math.sqrt(1 - mid * mid)
            fs = ["north", "east", "west"] + (["up"] if hi > 0 else []) + (["down"] if lo < 0 else [])
            out.append(box(f"{name}Plate{nm}{i}", (xe - d, yc + lo * pr, -1.0), (xe + d, yc + hi * pr, -0.02), "flange", faces=tuple(fs)))
        for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
            bx_, by_ = xe + sx * pr * 0.68, yc + sy * pr * 0.68
            out.append(box(f"{name}Bolt{nm}{k}", (bx_ - 0.3, by_ - 0.3, -1.35), (bx_ + 0.3, by_ + 0.3, -1.0), "metal",
                           faces=("north", "east", "west", "up", "down")))
    if end == "left":
        out = [mirror_x(b) for b in out]
    return out


def mirror_x(b):
    """A box mirrored across the block's middle (x to 16 - x), its east and west faces swapped and its U turned."""
    b = json.loads(json.dumps(b))
    (x1, y1, z1), (x2, y2, z2) = b["from"], b["to"]
    b["from"], b["to"] = [round(16 - x2, 3), y1, z1], [round(16 - x1, 3), y2, z2]
    faces = {}
    for f, v in b["faces"].items():
        if f in ("north", "south", "up", "down"):
            u1, v1, u2, v2 = v["uv"]
            v["uv"] = [round(16 - u2, 3), v1, round(16 - u1, 3), v2]
        faces[{"east": "west", "west": "east"}.get(f, f)] = v
    b["faces"] = faces
    return b


def wall_pipe_configs():
    """Every corner block that can occur: (state name, {face: (left end, right end)}). Runs with nothing happening at
    any corner are the straight blocks (tunnelwall-pipes and the rest), so they are left out."""
    import itertools
    configs = []
    for mask in range(1, 16):
        faces = [f for f in range(4) if mask >> f & 1]
        options = []
        for c in range(4):
            here, nxt = c in faces, (c + 1) % 4 in faces
            options.append("w" if here and nxt else "ocj" if here else "oc" if nxt else "o")
        for corners in itertools.product(*options):
            if all(k == "o" for k in corners):
                continue
            # (A "c" at a corner where only one face is open is that face's; "j" only ever ends a face's right end)
            ends = {f: (corners[(f + 3) % 4], corners[f]) for f in faces}
            name = "".join("nesw"[f] for f in faces) + "-" + "".join(corners)
            configs.append((name, ends))
    return configs


def wall_pipe_corner(ends):
    """The pipes of a corner block, without the wall."""
    out = []
    for f, (left, right) in ends.items():
        face = (wall_pipe_turning("PipeA", *WALL_PIPE_RUST, "wallrust", left, right)
                + wall_pipe_turning("PipeB", *WALL_PIPE_LAG, "walllag", left, right))
        if right == "c":
            face += wall_pipe_cap("R", "right")
        if left == "c":
            face += wall_pipe_cap("L", "left")
        out += [dict(rot(b, f), name=f"{b['name']}{f}") for b in face]
    return out


def wall_pipe_turned(name, k):
    """A corner block's state name turned k times clockwise (seen from above): north's face and corners become east's."""
    faces, corners = name.split("-")
    faces = "".join(sorted(("nesw"["nesw".index(f) + k & 3] for f in faces), key="nesw".index))
    return faces + "-" + "".join(corners[(c - k) % 4] for c in range(4))


def wall_pipe_corner_states():
    """{state: (shape, rotateY)} for wallpipecorner: one shape for each state up to turning. VS turns a shape
    anticlockwise by rotateY, so a shape turned k times clockwise is rotateY 360 - 90k (as the blocks facing east use
    270). tools/gen_blocktypes.py writes the blocktype from this."""
    states = {}
    for name, _ in wall_pipe_configs():
        shape = min(wall_pipe_turned(name, k) for k in range(4))
        k = next(k for k in range(4) if wall_pipe_turned(shape, k) == name)
        states[name] = (shape, (360 - 90 * k) % 360)
    return states


def wall_pipe_corners():
    """Writes block/wallpipe/<shape>.json for wallpipecorner (the wall texture is the blocktype's)."""
    tex = {"wall": "backrooms:block/level2/tunnelwall-plain", **PIPE_TEX, **WALL_PIPE_TEX}
    configs = dict(wall_pipe_configs())
    os.makedirs(os.path.join(OUT, "wallpipe"), exist_ok=True)
    states = wall_pipe_corner_states()
    for shape in sorted({s for s, _ in states.values()}):
        save(os.path.join("wallpipe", shape), tex, [CUBE("wall")] + wall_pipe_corner(configs[shape]), compact=True)
    return states


def thinner(boxes, by=0.05):
    """The same boxes a hair thinner top and bottom: where two runs cross at the same height, the one along Z then
    passes inside the one along X instead of their tops and undersides fighting over the same plane."""
    out = []
    for b in boxes:
        b = json.loads(json.dumps(b))
        b["from"][1] += by
        b["to"][1] -= by
        out.append(b)
    return out


def bundle_end():
    """A bundle along X ending at its east end (x 16): a canvas-lagging end cap, a blind flange on the rusty pipe, a
    cap on the fire line."""
    return bundle_x() + [
        box("LaggedCap", (15.2, 9.7, 0.7), (16, 15.3, 6.3), "metal"),
        box("RustyFlange", (15, 10.5, 9.5), (15.8, 14.5, 13.5), "dark"),
        box("RustyBlank", (15.8, 10.8, 9.8), (16, 14.2, 13.2), "dark"),
        box("FireCap", (15.3, 13.2, 13.2), (16, 15.8, 15.8), "red"),
    ]


def bundle_stub():
    """A length of bundle on its own, capped at both ends (a leaking stub over a pump room)."""
    out = bundle_end()
    for b in out[len(bundle_x()):]:
        m = json.loads(json.dumps(b))
        m["name"] += "W"
        m["from"][0], m["to"][0] = 16 - b["to"][0], 16 - b["from"][0]
        out.append(m)
    return out


def hub_pipes():
    """Both bundles crossing at the same height, with a junction box where they meet."""
    return bundle_x() + thinner(bundle_z()) + [
        box("JunctionBox", (4, 8, 4), (12, 16, 12), "dark"),
        box("Lid", (4.5, 7.5, 4.5), (11.5, 8, 11.5), "metal"),
    ]


def fixture_hub(tube_tex):
    """A fixture hanging from the junction box."""
    return [
        box("Housing", (2, 6, 6.5), (14, 7.5, 9.5), "metal"),
        box("Tube", (2, 5.3, 7), (14, 6, 9), tube_tex, glow=255 if tube_tex != "tubeoff" else 0, faces=("north", "south", "down", "east", "west")),
    ]


# ---------------- Level 2 machine cabinets (B5: hardware as geometry, from tools/modelkit.py) ----------------

CABINET_TEX = {k: f"backrooms:block/level2/cabinet-{v}" for k, v in (
    ("cabpaint", "paint"), ("cabpanel", "panel"), ("cabdark", "dark"), ("cabvent", "vent"), ("cabbezel", "bezel"),
    ("cabneedle", "needle"), ("cabdial", "dial"), ("cablampred", "lampred"), ("cablampamber", "lampamber"),
    ("cablabel", "label"), ("cabwarn", "warning"), ("cabtop", "top"))}
CAB = {"all": "cabpaint", "north": "cabpanel"}  # the carcass: the darker panel shows on its front, in the frame's recess
FRONT_ONLY = ("north", "east", "west", "up", "down")


def sides_turned(els):
    """all_sides for parts with rotations (the dials' bezels and needles): modelkit.turn carries them round."""
    out = []
    for i in range(4):
        out += [dict(e, name=f"{e['name']}{i}") for e in K.turn(els, i)]
    return out


def cab_lamp(name, cx, cy, z, tex):
    """An indicator lamp on a panel face at z: a bezel ring 1 px proud, a domed lens a further 1 px proud."""
    return [K.box(name + "Bezel", (cx - 0.75, cy - 0.75, z - K.PX), (cx + 0.75, cy + 0.75, z), "cabbezel", faces=FRONT_ONLY),
            K.box(name + "Lens", (cx - 0.5, cy - 0.5, z - 1.0), (cx + 0.5, cy + 0.5, z - K.PX), tex, faces=FRONT_ONLY,
                  uv=[0, 0, 16, 16])]


def cab_plate(name, x1, y1, x2, y2, z, tex, t=0.25):
    """A label or decal plate `t` proud of a face at z, its whole texture on its front."""
    return [K.box(name, (x1, y1, z - t), (x2, y2, z), tex, faces=FRONT_ONLY, uv=[0, 0, 16, 16])]


def louvre(name, x1, y1, x2, y2, z, n, tex="cabpaint", back="cabvent", frame=0.5, proud=1.0):
    """A louvred vent on a front face at z: a frame `frame` wide standing `proud` out, a dark backing, and n blades
    tilted 40 degrees across the opening, so each shows a lit top and a dark underside over the gap behind it."""
    els, openings = K.frame_members(name, x1, y1, x2, y2, z - proud, z, frame, tex)
    for e in els:
        e["faces"].pop("south", None)
    ox1, oy1, ox2, oy2 = openings[0]
    els.append(K.box(name + "Back", (ox1, oy1, z - 0.25), (ox2, oy2, z), back, faces=("north",)))
    pitch = (oy2 - oy1) / n
    for i in range(n):
        cy, cz = oy1 + (i + 0.5) * pitch, z - proud / 2 - 0.1
        els.append(K.box(f"{name}Blade{i}", (ox1, cy - 0.25, cz - 0.4), (ox2, cy + 0.25, cz + 0.4), tex,
                         faces=("north", "up", "down", "south"), rot=(-40, 0, 0), origin=(ox1, cy, cz)))
    return els


def cab_frame(name, x1, y1, x2, y2, z1, z2, border, grid=(1, 1), mid=None):
    els, openings = K.frame_members(name, x1, y1, x2, y2, z1, z2, border, "cabpaint", grid, mid)
    for e in els:
        e["faces"].pop("south", None)  # against the carcass
    return els, openings


def machinery_head():
    """The wall cabinet's upper block, its front to the north (z < 0 is out of the wall, in the tunnel): a framed
    instrument panel with two dial gauges in chrome bezels, a red and an amber lamp and an equipment plate, under a
    cap; a conduit in a gland and a rusty pipe run up out of it (from layout version 9 the block above carries them on
    into the ceiling, machinery_top)."""
    els = [K.box("Body", (1.5, 0, -2.0), (14.5, 11.5, 0), CAB, faces=("north", "east", "west"))]
    frame = cab_frame("Bezel", 1.5, 0, 14.5, 11.5, -2.5, -2.0, 1.0)[0]
    frame[0]["faces"].pop("down")  # on the door's top rail, at the block seam
    els += frame
    els.append(K.box("Cap", (1.25, 11.5, -2.75), (14.75, 12.25, 0), {"all": "cabpaint", "top": "cabtop"}, faces=FRONT_ONLY))
    els += K.dial("DialL", 5.0, 7.25, -2.0, r=2.25, angle=-35, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += K.dial("DialR", 11.0, 7.25, -2.0, r=2.25, angle=28, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += cab_lamp("LampR", 3.5, 2.75, -2.0, "cablampred") + cab_lamp("LampA", 5.5, 2.75, -2.0, "cablampamber")
    els += cab_plate("Plate", 8.0, 1.75, 13.0, 4.0, -2.0, "cablabel")
    els += [K.box("Gland", (3.75, 12.25, -1.75), (5.75, 12.75, 0), "metal", faces=("north", "east", "west", "up")),
            K.box("Conduit", (4.0, 12.75, -1.5), (5.5, 16, 0), "metal", faces=("north", "east", "west")),
            K.box("Conduit2", (10.0, 12.25, -1.2), (11.0, 16, 0), "rust", faces=("north", "east", "west"))]
    return els


def machinery_door():
    """The wall cabinet's lower block: a door of frame and recessed panel with a louvred vent, a bar handle, a lock and
    a warning decal, over a toe-recessed plinth."""
    els = [K.box("Toe", (2.0, 0, -1.75), (14.0, 1.0, 0), "cabdark", faces=("north", "east", "west")),
           K.box("Body", (1.5, 1.0, -2.0), (14.5, 16, 0), CAB, faces=("north", "east", "west", "down"))]
    frame = cab_frame("Door", 1.5, 1.0, 14.5, 16, -2.5, -2.0, 1.25)[0]
    frame[1]["faces"].pop("up")  # the top rail meets the instrument head's bottom rail at the block seam
    els += frame
    els += louvre("Vent", 3.75, 8.5, 10.75, 13.75, -2.0, 5)
    els += K.handle("Handle", 12.25, 8.0, -2.0, length=4.0, axis="y", standoff=0.75, thick=0.75, tex="cabbezel")
    els += cab_plate("Warn", 4.5, 4.0, 7.5, 7.0, -2.0, "cabwarn")
    els.append(K.box("Lock", (11.75, 4.5, -2.5), (12.75, 5.5, -2.0), "cabbezel", faces=FRONT_ONLY))
    return els


# The free-standing cabinet's feed pipe (Levels 2 and 3), in the cabinet's frame (front north, its back and the wall
# behind it at z 16): 2.5 square, its back 3.25 off the wall. That clears the wall pipes behind it at body height
# (they stand 4 off the wall at most: it passes in front of them) and lies inside the near pipe of the overhead bundle
# above the cabinet, whichever wall it stands against (the rusty pipe 3-6 off the wall, or the lagged one 1-6), without
# a face in the plane of either.
FEED_X = (11.25, 13.75)
FEED_Z = (10.25, 12.75)


def cabinet_feed(top):
    """The feed pipe's gland on the cabinet's cap (y 15) and the pipe out of it, up to `top`."""
    (x1, x2), (z1, z2) = FEED_X, FEED_Z
    return [K.box("Gland", (x1 - 0.75, 15.0, z1 - 0.75), (x2 + 0.75, 15.5, z2 + 0.75), "metal", faces=("north", "east", "west", "south", "up")),
            K.box("GlandNut", (x1 - 0.4, 15.5, z1 - 0.4), (x2 + 0.4, 16.25, z2 + 0.4), "metal", faces=("north", "east", "west", "south", "up")),
            K.box("Pipe", (x1, 15.5, z1), (x2, top, z2), "rust", faces=("north", "east", "west", "south"))]


def cabinet_feed_elbow():
    """(L2 placement) Where nothing carries the feed on (Level 3, and Level 2 worlds made before layout version 9): the
    pipe rises out of its gland to waist height of the block above, between the wall pipes there (the lagged one tops
    out at y 6.25 of that block, the rusty one starts at 10.5), and turns back into the wall through a wall plate."""
    (x1, x2), (z1, z2) = FEED_X, FEED_Z
    y1, y2 = 23.25, 25.75  # the horizontal run, 7.25-9.75 up the block above
    return cabinet_feed(y2) + [
        # The elbow: a fitting a little fatter than the pipe round the turn, then the run back into the wall
        K.box("Elbow", (x1 - 0.3, y1 - 0.3, z1 - 0.3), (x2 + 0.3, y2 + 0.3, z2 + 0.3), "rust", faces=("north", "east", "west", "up", "down")),
        K.box("Run", (x1, y1, z2 + 0.3), (x2, y2, 16), "rust", faces=("east", "west", "up", "down")),
        K.box("WallPlate", (x1 - 0.9, y1 - 0.9, 15.5), (x2 + 0.9, y2 + 0.9, 16), "metal", faces=("north", "east", "west", "up", "down")),
    ]


def feed_pipe():
    """(L2 placement) The feed pipe carried on above a machine cabinet (cabinet frame, block above the cabinet): up
    from the cabinet's gland, held to the wall by a clamp and a strut between the wall pipes, into the overhead
    bundle's near pipe, whose middle is 12.5 up the block above this one."""
    (x1, x2), (z1, z2) = FEED_X, FEED_Z
    return [K.box("Pipe", (x1, 0, z1), (x2, 28.5, z2), "rust", faces=("north", "east", "west", "south")),
            K.box("Clamp", (x1 - 0.5, 7.5, z1 - 0.5), (x2 + 0.5, 9.0, z2 + 0.5), "metal"),
            K.box("Strut", (12.0, 7.75, z2 + 0.5), (13.0, 8.75, 16), "metal", faces=("east", "west", "up", "down")),
            K.box("Foot", (11.25, 7.0, 15.5), (13.75, 9.5, 16), "metal", faces=("north", "east", "west", "up", "down"))]


def machine_cabinet(feed="elbow"):
    """The free-standing machine cabinet (Levels 2 and 3), front to the north: carcass and cap, a framed front with an
    instrument panel (two gauges, two lamps) over a louvred door with a bar handle, on a toe-recessed plinth; the feed
    pipe out of a gland on the top at the back. With feed "elbow" the pipe turns back into the wall above the cabinet
    (cabinet_feed_elbow); with "up" (L2 placement, machinecabinetfeed) it rises out of the block into the feed pipe
    above (feedpipe). The old open stub led nowhere."""
    els = [K.box("Toe", (2.0, 0, 5.25), (14.0, 1.0, 15.5), "cabdark", faces=("north", "east", "west", "south")),
           K.box("Body", (1.0, 1.0, 4.5), (15.0, 14.25, 16), CAB, faces=("north", "east", "west", "south", "down")),
           K.box("Cap", (0.75, 14.25, 4.0), (15.25, 15.0, 16), {"all": "cabpaint", "top": "cabtop"})]
    els += cab_frame("Front", 1.0, 1.0, 15.0, 14.25, 4.0, 4.5, 1.0, grid=(1, 2))[0]
    els += K.dial("DialL", 4.6, 10.7, 4.5, r=1.75, angle=-30, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += K.dial("DialR", 11.4, 10.7, 4.5, r=1.75, angle=40, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += cab_lamp("LampR", 8.0, 11.9, 4.5, "cablampred") + cab_lamp("LampA", 8.0, 9.6, 4.5, "cablampamber")
    els += louvre("Vent", 2.75, 2.5, 9.75, 6.625, 4.5, 3)
    els += K.handle("Handle", 12.0, 4.5, 4.5, length=3.0, axis="y", standoff=0.75, thick=0.75, tex="cabbezel")
    els += cabinet_feed_elbow() if feed == "elbow" else cabinet_feed(16)
    return els


def level2():
    save("pipes-run", PIPE_TEX, bundle_x())
    save("pipes-hub", PIPE_TEX, hub_pipes())
    # Where a run ends with open tunnel beyond it (the generator turns the shape to the end's side)
    save("pipes-end", PIPE_TEX, bundle_end())
    save("pipes-stub", PIPE_TEX, bundle_stub())

    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        textures = dict(PIPE_TEX, tube="backrooms:block/props/tube-white", tubeoff="backrooms:block/props/tube-off")
        save(f"tunnellight-bundle-{state}", textures, bundle_x() + fixture_x(tex))
        save(f"tunnellight-plain-{state}", textures, fixture_x(tex))
        save(f"tunnellight-hub-{state}", textures, hub_pipes() + fixture_hub(tex))
    textures = dict(PIPE_TEX, tube="backrooms:block/props/tube-warm")
    save("tunnellight-bundle-warm", textures, bundle_x() + fixture_x("tube"))
    save("tunnellight-plain-warm", textures, fixture_x("tube"))
    save("tunnellight-hub-warm", textures, hub_pipes() + fixture_hub("tube"))

    wall = {"wall": "backrooms:block/level2/tunnelwall-plain", **PIPE_TEX, **WALL_PIPE_TEX,
            "valve": "backrooms:block/props/valve", "panel": "backrooms:block/props/cabinet-front",
            "gauge": "backrooms:block/detail/gauge"}
    # Horizontal pipes bolted to the wall, sticking out a few pixels into the tunnel
    save("tunnelwall-pipes", wall, [CUBE("wall")] + all_sides(WALL_PIPES))
    save("tunnelwall-pipesjoint", wall, [CUBE("wall")] + all_sides(WALL_PIPES + wall_pipe_joint()))
    save("tunnelwall-pipesbracket", wall, [CUBE("wall")] + all_sides(WALL_PIPES + wall_pipe_bracket()))
    # The same pipes turning corners and ending (Levels 2 and 3 share them: blocktype wallpipecorner)
    wall_pipe_corners()
    # A vertical riser from floor to ceiling, and where it crosses the horizontal wall pipes
    riser = [
        # (a hair deeper than the lagged pipe, whose front would otherwise lie in the riser's front where it crosses)
        box("Riser", (6, 0, -4.05), (10, 16, 0), "rust", faces=("north", "east", "west")),
        box("Clamp", (5.5, 7, -4.5), (10.5, 8.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
    ]
    save("tunnelwall-riser", wall, [CUBE("wall")] + all_sides(riser))
    save("tunnelwall-riserjoint", wall, [CUBE("wall")] + all_sides(riser + WALL_PIPES))
    # A valve wheel on a short stem
    save("tunnelwall-valve", wall, [CUBE("wall")] + all_sides([
        box("Stem", (7.5, 7.5, -3), (8.5, 8.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
        box("RimTop", (5, 10.5, -4), (11, 11.5, -3), "valve"),
        box("RimBottom", (5, 4.5, -4), (11, 5.5, -3), "valve"),
        box("RimLeft", (4.5, 5, -4), (5.5, 11, -3), "valve"),
        box("RimRight", (10.5, 5, -4), (11.5, 11, -3), "valve"),
        box("Spoke", (7.5, 5, -3.8), (8.5, 11, -3.2), "valve"),
        box("SpokeH", (5, 7.5, -3.8), (11, 8.5, -3.2), "valve"),
    ]))

    # A control cabinet bolted to the wall, two blocks high (B5: its hardware is geometry, tools/modelkit.py). The
    # upper block is the instrument head: a framed panel with two dial gauges in bezels, two indicator lamps and an
    # equipment plate, under a cap with conduits up into the ceiling. The lower block is the door: frame and recessed
    # panel, a louvred vent, a bar handle and a warning decal, on a toe-recessed plinth.
    mwall = dict(wall, **CABINET_TEX)
    save("tunnelwall-machinery", mwall, [CUBE("wall")] + sides_turned(machinery_head()))
    save("tunnelwall-machinerybase", mwall, [CUBE("wall")] + sides_turned(machinery_door()))

    # Machine cabinet, front panel facing north, back against the wall to the south
    cab = dict(CABINET_TEX, metal="backrooms:block/props/metal", rust=PIPE_TEX["rust"])
    save("machinecabinet", cab, machine_cabinet())
    # (L2 placement, layout version 9) Level 2's cabinets feed the overhead bundle: the cabinet with its pipe straight
    # up, and the pipe carried on above it (blocktypes machinecabinetfeed and feedpipe, from gen_blocktypes.py)
    save("machinecabinet-feed", cab, machine_cabinet("up"))
    save("feedpipe", {"metal": "backrooms:block/props/metal", "rust": PIPE_TEX["rust"]}, feed_pipe())
    tunnel_fittings(wall)


# ---------------- (L2 placement) Level 2's fittings that lead somewhere, from layout version 9 ----------------
# Blocktype tunnelfitting (gen_blocktypes.py): wall blocks like tunnelwall's, with their fittings on all four faces.

def machinery_top():
    """Above the wall cabinet's instrument head: its two conduits (bright steel, and the copper-coloured one) carried on
    up the wall from the head's gland into the ceiling, each held by a saddle clip and ending in a ceiling plate where
    it goes through. They pass behind the overhead bundle's near pipe where one runs along the wall (as the risers do)."""
    els = [K.box("Conduit", (4.0, 0, -1.5), (5.5, 16, 0), "metal", faces=("north", "east", "west")),
           K.box("Conduit2", (10.0, 0, -1.2), (11.0, 16, 0), "rust", faces=("north", "east", "west")),
           K.box("Clip", (3.5, 6.0, -1.85), (6.0, 7.0, 0), "metal", faces=("north", "east", "west", "up", "down")),
           K.box("Clip2", (9.5, 6.5, -1.55), (11.5, 7.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
           K.box("Plate", (3.25, 15.4, -2.25), (6.25, 16, 0), "metal", faces=("north", "east", "west", "down")),
           K.box("Plate2", (9.25, 15.4, -1.95), (11.75, 16, 0), "metal", faces=("north", "east", "west", "down"))]
    return els


def valve_wheel(name, cx, cy, z):
    """The red hand wheel, as the old tunnelwall-valve's: a square rim 7 across with two spokes, its back face at z
    (the wheel 1 deep in front of it)."""
    return [box(f"{name}RimTop", (cx - 3, cy + 2.5, z - 1), (cx + 3, cy + 3.5, z), "valve"),
            box(f"{name}RimBottom", (cx - 3, cy - 3.5, z - 1), (cx + 3, cy - 2.5, z), "valve"),
            box(f"{name}RimLeft", (cx - 3.5, cy - 3, z - 1), (cx - 2.5, cy + 3, z), "valve"),
            box(f"{name}RimRight", (cx + 2.5, cy - 3, z - 1), (cx + 3.5, cy + 3, z), "valve"),
            box(f"{name}Spoke", (cx - 0.5, cy - 3, z - 0.8), (cx + 0.5, cy + 3, z - 0.2), "valve"),
            box(f"{name}SpokeH", (cx - 3, cy - 0.5, z - 0.8), (cx + 3, cy + 0.5, z - 0.2), "valve")]


def pipe_valve():
    """A gate valve in the steel wall pipe (WALL_PIPE_RUST): bolted flanges either side of a fat body, a bonnet out of
    its front and the hand wheel on the spindle, facing the tunnel at about head height."""
    yc, zc, r = WALL_PIPE_RUST
    out = []
    for i, (x1, x2) in enumerate(((4.75, 5.5), (10.5, 11.25))):
        out += round_pipe(f"VFlange{i}", yc, zc, r + 0.75, "flange", x1, x2, shaded=False, faces=("east", "west"))
    out += round_pipe("VBody", yc, zc, r + 0.5, "flange", 5.5, 10.5, shaded=False)
    front = zc - r - 0.5  # the body's front
    wheel = front - 1.25  # the wheel's back
    out += [box("Bonnet", (6.75, yc - 1.25, front - 0.75), (9.25, yc + 1.25, front + 0.5), "flange", faces=("north", "east", "west", "up", "down")),
            # (on into the spokes, so its end never shows between them and the bonnet)
            box("Spindle", (7.5, yc - 0.5, wheel - 0.5), (8.5, yc + 0.5, front - 0.75), "metal", faces=("north", "east", "west", "up", "down"))]
    return out + valve_wheel("Wheel", 8, yc, wheel)


def riser_valve():
    """The riser (as tunnelwall-riser's) with a valve in it at its foot: flanges, a body, a bonnet and the hand wheel,
    a little below knee height."""
    out = [box("Riser", (6, 0, -4.05), (10, 16, 0), "rust", faces=("north", "east", "west")),
           box("FlangeLow", (5.25, 3.75, -4.8), (10.75, 4.5, 0), "flange", faces=("north", "east", "west", "up", "down")),
           box("FlangeHigh", (5.25, 10.5, -4.8), (10.75, 11.25, 0), "flange", faces=("north", "east", "west", "up", "down")),
           box("Body", (5.5, 4.5, -4.6), (10.5, 10.5, 0), "flange", faces=("north", "east", "west")),
           box("Bonnet", (6.75, 6.25, -5.35), (9.25, 8.75, -4.6), "flange", faces=("north", "east", "west", "up", "down")),
           box("Spindle", (7.5, 7.0, -6.1), (8.5, 8.0, -5.35), "metal", faces=("north", "east", "west", "up", "down"))]
    return out + valve_wheel("Wheel", 8, 7.5, -5.6)


def tunnel_fittings(wall):
    save("tunnelfitting-machinerytop", wall, [CUBE("wall")] + sides_turned(machinery_top()))
    save("tunnelfitting-pipesvalve", wall, [CUBE("wall")] + all_sides(WALL_PIPES + pipe_valve()))
    save("tunnelfitting-riservalve", wall, [CUBE("wall")] + all_sides(riser_valve()))


# ---------------- Level 1 fixtures and props ----------------

def level1():
    tubes = {"metal": "backrooms:block/props/metal", "chain": "backrooms:block/props/metal-dark",
             "tube": "backrooms:block/props/tube-white", "tubeoff": "backrooms:block/props/tube-off"}
    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        save(f"hanginglight-{state}", tubes, [
            box("Chain1", (3, 10, 7.75), (3.5, 16, 8.25), "chain"),
            box("Chain2", (12.5, 10, 7.75), (13, 16, 8.25), "chain"),
            box("Housing", (0.5, 8.5, 5.5), (15.5, 10, 10.5), "metal"),
            box("Tube1", (1, 7.7, 6.2), (15, 8.5, 7.6), tex, glow=255 if state == "lit" else 0),
            box("Tube2", (1, 7.7, 8.4), (15, 8.5, 9.8), tex, glow=255 if state == "lit" else 0),
        ])
    bulbs = {"chain": "backrooms:block/props/metal-dark", "socket": "backrooms:block/props/metal",
             "bulb": "backrooms:block/props/tube-warm", "bulboff": "backrooms:block/props/tube-off"}
    for state, tex in (("lit", "bulb"), ("off", "bulboff")):
        save(f"hangingbulb-{state}", bulbs, [
            box("Cord", (7.75, 8, 7.75), (8.25, 16, 8.25), "chain"),
            box("Socket", (7, 6.5, 7), (9, 8, 9), "socket"),
            box("Bulb", (6.5, 3.5, 6.5), (9.5, 6.5, 9.5), tex, glow=255 if state == "lit" else 0),
        ])

    pillar = {"pillar": "backrooms:block/level1/concretepillar-plain", "metal": "backrooms:block/props/metal",
              "tube": "backrooms:block/props/tube-white"}
    save("pillarlight", pillar, [CUBE("pillar")] + all_sides([
        box("Housing", (6, 0.5, -1.5), (10, 15.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
        box("Tube", (7, 1, -2.2), (9, 15, -1.5), "tube", glow=255, faces=("north", "east", "west", "up", "down")),
    ]))

    save("concretewall-damaged", {"wall": "backrooms:block/level1/concretewall-damaged", "rust": PIPE_TEX["rust"]},
         [CUBE("wall")] + all_sides([
             box("Rebar1", (4, 6, -4), (5, 7, 0), "rust"),
             box("Rebar2", (10, 9, -3), (11, 10, 0), "rust"),
             box("Rebar3", (12, 3, -2), (13, 4, 0), "rust"),
         ]))

    save("conduit", {"conduit": "backrooms:block/props/conduit", "metal": "backrooms:block/props/metal"}, [
        # (End faces too: where a light interrupts the run the conduit ends solid, not hollow)
        box("Conduit1", (0, 14.5, 4), (16, 15.5, 5), "conduit", faces=("north", "south", "down", "east", "west")),
        box("Conduit2", (0, 14.5, 6), (16, 15.5, 7), "conduit", faces=("north", "south", "down", "east", "west")),
        box("Clip", (7.5, 14, 3.5), (8.5, 16, 7.5), "metal"),
    ])

    # Where a run of the conduit ends (WorldLayout.ConduitEnds, from layout version 9) it is finished off, so the tubes
    # are never open: "cap" where there is open space or a light beyond (a collar on each tube and a plate over both),
    # "box" where it meets a wall or a beam (the tubes go into a junction box, with a lid and screws, mounted on it).
    # Modelled for the east end; the blocks turn them (conduitend-<side>-<kind>) and the "stub" blocks have an end at
    # each side of a length on its own (conduit-stub-<west><east>, c = cap, b = box)
    ctex = {"conduit": "backrooms:block/props/conduit", "metal": "backrooms:block/props/metal",
            "dark": "backrooms:block/props/metal-dark"}
    all6 = ("north", "south", "down", "east", "west")

    def conduit_end(kind, west):
        """The fitting at one end of a run: the east end, or the west one (the same turned about the block's middle)."""
        if kind == "cap":
            els = [box("Collar1", (13.2, 14.1, 3.5), (14.8, 15.9, 5.5), "metal", faces=all6 + ("up",)),
                   box("Collar2", (13.2, 14.1, 5.5), (14.8, 15.9, 7.5), "metal", faces=all6 + ("up",)),
                   box("EndPlate", (15.2, 13.8, 3.2), (16, 15.9, 7.8), "metal")]
        else:
            els = [box("JBox", (12.2, 12.6, 2.6), (16, 16, 8.4), "metal", faces=("north", "south", "down", "west")),
                   box("Lid", (12.8, 12.1, 3.2), (15.4, 12.6, 7.8), "dark", faces=("north", "south", "down", "west", "east")),
                   box("Screw1", (13.1, 11.7, 3.4), (13.7, 12.1, 4.0), "metal"), box("Screw2", (14.5, 11.7, 3.4), (15.1, 12.1, 4.0), "metal"),
                   box("Screw3", (13.1, 11.7, 7.0), (13.7, 12.1, 7.6), "metal"), box("Screw4", (14.5, 11.7, 7.0), (15.1, 12.1, 7.6), "metal"),
                   box("Nipple1", (11.0, 14.2, 3.6), (12.2, 15.8, 5.4), "metal", faces=("north", "south", "down", "up", "west")),
                   box("Nipple2", (11.0, 14.2, 5.6), (12.2, 15.8, 7.4), "metal", faces=("north", "south", "down", "up", "west"))]
        if west:
            for i, e in enumerate(els):
                x1, x2 = e["from"][0], e["to"][0]
                e["from"][0], e["to"][0] = 16 - x2, 16 - x1
                f = e["faces"]
                e["faces"] = {k: v for k, v in {"east": f.get("west"), "west": f.get("east"), "north": f.get("north"), "south": f.get("south"),
                                                "up": f.get("up"), "down": f.get("down")}.items() if v is not None}
                e["name"] += "W"
        return els

    def conduit_tubes(x0, x1):
        # (their ends are closed by the fitting, or by the next block's tube)
        return [box("Conduit1", (x0, 14.5, 4), (x1, 15.5, 5), "conduit", faces=("north", "south", "down")),
                box("Conduit2", (x0, 14.5, 6), (x1, 15.5, 7), "conduit", faces=("north", "south", "down"))]

    for kind in ("cap", "box"):
        run = conduit_tubes(0, 15.2 if kind == "cap" else 12.5) + [box("Clip", (4.5, 14, 3.5), (5.5, 16, 7.5), "metal")]  # (the tubes run into the fitting)
        save(f"conduit-end-{kind}", ctex, run + conduit_end(kind, False))
    for w, e in (("c", "c"), ("c", "b"), ("b", "c"), ("b", "b")):
        els = conduit_tubes(0.8 if w == "c" else 3.5, 15.2 if e == "c" else 12.5)
        save(f"conduit-stub-{w}{e}", ctex, els + conduit_end("cap" if w == "c" else "box", True) + conduit_end("cap" if e == "c" else "box", False))

    # Metal shelving with boxes, open side facing north
    shelf = [
        box("Post1", (0.5, 0, 0.5), (1.5, 16, 1.5), "metal"),
        box("Post2", (14.5, 0, 0.5), (15.5, 16, 1.5), "metal"),
        box("Post3", (0.5, 0, 14.5), (1.5, 16, 15.5), "metal"),
        box("Post4", (14.5, 0, 14.5), (15.5, 16, 15.5), "metal"),
    ]
    for i, y in enumerate((1, 8, 15)):
        shelf.append(box(f"Shelf{i}", (0.5, y, 0.5), (15.5, y + 0.6, 15.5), "metal"))
    shelf += [
        box("BoxA", (2, 1.6, 3), (8, 6.6, 13), "cardboard"),
        box("BoxB", (9, 1.6, 5), (14, 5.6, 13), "cardboard"),
        box("BoxC", (3, 8.6, 4), (10, 12.6, 14), "cardboard"),
    ]
    save("metalshelf", {"metal": "backrooms:block/props/metal", "cardboard": "backrooms:block/supplybox-side"}, shelf)

    # Stair climbing toward the north
    save("concretestairs", {"concrete": "backrooms:block/level1/concretefloor-plain"}, [
        box("Lower", (0, 0, 0), (16, 8, 16), "concrete"),
        box("Upper", (0, 8, 0), (16, 16, 8), "concrete"),
    ])


def parking():
    save("wheelstop", {"stop": "backrooms:block/level1/wheelstop"}, [
        box("Stop", (0, 0, 6), (16, 2.5, 10), "stop"),
    ])

    # An abandoned saloon car, 2 blocks wide and 4 long, nose to the north, drawn from its corner block: wheels set in
    # arches cut out of the body sides, a raked windscreen and rear window, a glasshouse narrower than the body, door
    # seams and handles. It stays inside its 2x4 footprint (the rest of which is invisible hull, so breaking any of it
    # breaks the car: BlockBehaviorWreck) and only a little over a block tall
    def tilted(b, origin, rx):
        b["rotationOrigin"], b["rotationX"] = list(origin), rx
        return b

    rake = math.degrees(math.atan2(6, 7.5))  # the glass leans 6 back over its 7.5 rise
    glass_len = math.hypot(6, 7.5)
    front_arch, rear_arch = 12.5, 51.5  # wheel centres along the car

    def side(x1, x2, sx):
        """One side of the car: the panels round the arches, wheels, door seams and handles, a mirror. sx is the outer
        face (x 1 or 31), its outward direction given by which end of x1..x2 it is."""
        out_ = -1 if sx == x1 else 1
        tag = "L" if out_ < 0 else "R"
        els = [
            box(f"Side{tag}Front", (x1, 3, 1), (x2, 11, 7), "body"),
            box(f"Side{tag}Doors", (x1, 3, 18), (x2, 11, 46), "body"),
            box(f"Side{tag}Rear", (x1, 3, 57), (x2, 11, 63), "body"),
        ]
        for nm, c in (("Front", front_arch), ("Rear", rear_arch)):
            a, b = c - 5.5, c + 5.5
            els += [box(f"Arch{tag}{nm}", (x1, 9.5, a), (x2, 11, b), "body"),
                    box(f"Arch{tag}{nm}A", (x1, 8, a), (x2, 9.5, a + 1.5), "body"),
                    box(f"Arch{tag}{nm}B", (x1, 8, b - 1.5), (x2, 9.5, b), "body")]
            # A round-ish wheel: two crossed boxes, and a hub cap on its outer face
            wx1, wx2 = (1.6, 4) if out_ < 0 else (28, 30.4)
            hx = (1.3, 1.6) if out_ < 0 else (30.4, 30.7)
            els += [box(f"Wheel{tag}{nm}", (wx1, 1.5, c - 4.5), (wx2, 7.5, c + 4.5), "tyre"),
                    box(f"Wheel{tag}{nm}B", (wx1, 0, c - 3), (wx2, 9, c + 3), "tyre"),
                    box(f"Hub{tag}{nm}", (hx[0], 3, c - 1.5), (hx[1], 6, c + 1.5), "metal")]
        seam = (sx - 0.1, sx) if out_ < 0 else (sx, sx + 0.1)
        for i, z in enumerate((19.8, 32.6, 45)):
            els.append(box(f"Seam{tag}{i}", (seam[0], 3.5, z), (seam[1], 10.8, z + 0.3), "tyre"))
        handle = (sx - 0.3, sx) if out_ < 0 else (sx, sx + 0.3)
        for i, z in enumerate((29, 41.5)):
            els.append(box(f"Handle{tag}{i}", (handle[0], 9, z), (handle[1], 9.6, z + 2), "metal"))
        mirror = (0, 3.6) if out_ < 0 else (28.4, 32)
        els.append(box(f"Mirror{tag}", (mirror[0], 11, 21), (mirror[1], 12.6, 22.5), "body"))
        return els

    def glasshouse():
        els = [
            # The cabin's sides between the pillars, stepped down to the raked glass at either end
            box("Cabin", (4, 11, 26), (28, 18.5, 39), "glass", faces=("east", "west")),
            box("Roof", (3.6, 18.5, 25.5), (28.4, 19.5, 39.5), "body"),
            box("PillarBL", (3.7, 11, 32), (4.3, 18.5, 33.5), "body"),
            box("PillarBR", (27.7, 11, 32), (28.3, 18.5, 33.5), "body"),
            tilted(box("Windscreen", (4, 11, 19.7), (28, 11 + glass_len, 20.3), "glass"), (16, 11, 20), rake),
            tilted(box("RearWindow", (4, 11, 44.7), (28, 11 + glass_len, 45.3), "glass"), (16, 11, 45), -rake),
        ]
        for nm, x1, x2 in (("L", 3.6, 5), ("R", 27, 28.4)):
            # (a hair longer than the glass, so their ends are not in the glass's planes)
            els += [tilted(box(f"PillarA{nm}", (x1, 10.95, 19.4), (x2, 11.05 + glass_len, 20.6), "body"), (16, 11, 20), rake),
                    tilted(box(f"PillarC{nm}", (x1, 10.95, 44.2), (x2, 11.05 + glass_len, 45.8), "body"), (16, 11, 45), -rake)]
        for i, (y1, y2, zf, zr) in enumerate(((11, 13, 20.5, 44.5), (13, 15, 22, 43), (15, 17, 23.5, 41.5), (17, 18.5, 25, 40))):
            els += [box(f"QuarterF{i}", (4, y1, zf), (28, y2, 26), "glass", faces=("east", "west")),
                    box(f"QuarterR{i}", (4, y1, 39), (28, y2, zr), "glass", faces=("east", "west"))]
        return els

    # ---- The inside, seen through the glass ----
    # The cabin's floor is a long way under the beltline (the body's top at 11), so there is room for seats you could
    # sit in: a front pair facing forward, a bench behind, the dashboard under the windscreen with an instrument
    # hood over the driver's dials, a steering wheel on its column, door cards with armrests and pulls, a gear lever
    # on the tunnel between the seats, a headliner and a mirror. The driver is on the east side of a north-facing car
    # (right-hand drive). The wrecks have the same parts, torn and dirty: a split cushion with the foam out, a missing
    # headrest, a folded seat back, a pulled-out radio, a bent wheel, a door card hanging off, the headliner sagging,
    # glass and litter on the floor. Every part is in the 1/16-block units of the rest of the car
    FLOOR = 5.5
    SEAT_X = {"pass": (6.6, 14.8), "drive": (17.2, 25.4)}

    def part(name, frm, to, tex, faces=DIRS, spin=None, uv=None):
        """A box, turned by spin = (origin, rotationX, rotationZ) where it is, with its faces' UV fixed by uv."""
        b = box("In" + name, frm, to, tex, faces=faces)
        if spin:
            b["rotationOrigin"] = list(spin[0])
            if spin[1]:
                b["rotationX"] = spin[1]
            if spin[2]:
                b["rotationZ"] = spin[2]
        if uv:
            for f in b["faces"].values():
                f["uv"] = list(uv)
        return b

    def front_seat(tag, who, torn):
        x1, x2 = SEAT_X[who]
        cx = (x1 + x2) / 2
        back = ((cx, 8.2, 35.8), 8, 0)
        els = [
            part(f"Seat{tag}Rail", (x1 + 1.2, FLOOR, 30.4), (x2 - 1.2, 6.8, 34.6), "trim"),
            part(f"Seat{tag}Cushion", (x1, 6.8, 29.6), (x2, 8.2, 35.4), "seat"),
            part(f"Seat{tag}BolsterL", (x1, 8.2, 30.2), (x1 + 1.2, 8.9, 35.4), "seat"),
            part(f"Seat{tag}BolsterR", (x2 - 1.2, 8.2, 30.2), (x2, 8.9, 35.4), "seat"),
            part(f"Seat{tag}Back", (x1, 8.2, 35.0), (x2, 15.0, 36.7), "seat", spin=back),
            part(f"Seat{tag}WingL", (x1, 9.4, 34.4), (x1 + 1.2, 14.2, 35.0), "seat", spin=back),
            part(f"Seat{tag}WingR", (x2 - 1.2, 9.4, 34.4), (x2, 14.2, 35.0), "seat", spin=back),
        ]
        posts = [(cx - 1.9, 15.0, 35.5), (cx + 1.4, 15.0, 35.5)]
        if torn and who == "pass":
            # The headrest is gone: two bare posts, one bent
            els.append(part(f"Seat{tag}PostL", posts[0], (posts[0][0] + 0.5, 16.8, posts[0][2] + 0.6), "metal", spin=back))
            els.append(part(f"Seat{tag}PostR", posts[1], (posts[1][0] + 0.5, 16.2, posts[1][2] + 0.6), "metal", spin=((posts[1][0], 15.0, 35.5), 8 + 30, 0)))
        else:
            els += [part(f"Seat{tag}PostL", posts[0], (posts[0][0] + 0.5, 16.2, posts[0][2] + 0.6), "metal", spin=back),
                    part(f"Seat{tag}PostR", posts[1], (posts[1][0] + 0.5, 16.2, posts[1][2] + 0.6), "metal", spin=back)]
            head = part(f"Seat{tag}Head", (x1 + 2.2, 16.0, 35.1), (x2 - 2.2, 18.2, 36.7), "seat", spin=back)
            if torn:  # slumped to one side
                head = part(f"Seat{tag}Head", (x1 + 2.2, 15.6, 35.1), (x2 - 2.2, 17.8, 36.7), "seat", spin=((cx, 15.6, 35.9), 8, 22))
            els.append(head)
        if torn and who == "pass":
            els.append(part(f"Seat{tag}Foam", (x1 + 2.0, 8.2, 31.0), (x1 + 5.6, 8.7, 34.0), "foam", faces=("up", "north", "east", "west", "south")))
        if torn and who == "drive":
            els.append(part(f"Seat{tag}Split", (cx - 2.8, 9.6, 34.5), (cx - 1.4, 13.6, 35.0), "foam", spin=back))
            els.append(part(f"Seat{tag}Foam", (cx + 0.6, 8.2, 31.4), (cx + 3.4, 8.7, 33.4), "foam"))
        return els

    def rear_bench(torn):
        els = [part("BenchRail", (6.5, FLOOR, 39.4), (26.5, 6.8, 42.0), "trim"),
               part("BenchCushion", (5.0, 6.8, 38.8), (27.0 if not torn else 18.0, 8.3, 42.8), "seat"),
               part("BenchBack", (5.0, 8.3, 42.3), (27.0 if not torn else 18.0, 12.8, 43.4), "seat")]
        if torn:
            # The right-hand part of the back has folded forward onto where its cushion was
            els.append(part("BenchBackFolded", (18.0, 8.3, 42.3), (27.0, 12.8, 43.4), "seat", spin=((22.5, 8.3, 42.8), -62, 0)))
            els.append(part("BenchFoam", (8.0, 8.3, 39.6), (11.4, 8.8, 41.8), "foam"))
        return els

    def wheel(torn):
        cx, cy, z0, a, length, t = 21.3, 8.7, 27.4, 2.55, 2.7, 0.8
        els = []
        for i in range(8):
            if torn and i == 5:
                continue  # a piece of the rim snapped off
            th = math.radians(i * 45)
            mx, my = cx + a * math.cos(th), cy + a * math.sin(th)
            if i % 2 == 0:  # the straight sides: top, bottom, left, right
                half = (t / 2, length / 2) if i in (0, 4) else (length / 2, t / 2)
                els.append(part(f"WheelRim{i}", (mx - half[0], my - half[1], z0), (mx + half[0], my + half[1], z0 + t), "trim"))
            else:
                els.append(part(f"WheelRim{i}", (mx - length / 2, my - t / 2, z0), (mx + length / 2, my + t / 2, z0 + t), "trim",
                                spin=((mx, my, z0 + t / 2), 0, -45 if i in (1, 5) else 45)))
        els += [part("WheelSpokeH", (cx - a, cy - 0.4, z0 + 0.1), (cx + a, cy + 0.4, z0 + 0.7), "trim"),
                part("WheelSpokeV", (cx - 0.4, cy - a, z0 + 0.1), (cx + 0.4, cy, z0 + 0.7), "trim"),
                part("WheelHub", (cx - 1.1, cy - 1.1, z0 - 0.1), (cx + 1.1, cy + 1.1, z0 + 1.0), "trim"),
                part("WheelCap", (cx - 0.6, cy - 0.6, z0 + 1.0), (cx + 0.6, cy + 0.6, z0 + 1.4), "metal"),
                part("WheelColumn", (cx - 0.7, 8.0, 24.6), (cx + 0.7, 9.4, z0), "trim", faces=("north", "east", "west", "up", "down"))]
        return els

    def doorcards(torn):
        els = []
        for east in (False, True):
            def X(a, b):
                return (32 - b, 32 - a) if east else (a, b)
            tag = "E" if east else "W"
            inner = "west" if east else "east"
            c0, c1 = X(4.0, 5.2)
            card_faces = (inner, "up", "north", "south")
            if torn and not east:
                # The lower half of this card has come away and hangs from the armrest by a strip of vinyl
                els.append(part(f"Card{tag}Upper", (c0, 8.2, 21.0), (c1, 10.9, 44.2), "doorcard", faces=card_faces))
                els.append(part(f"Card{tag}Flap", (c0 + 1.0, 5.8, 25.0), (c1 + 1.0, 8.2, 36.0), "doorcard", faces=("east", "west", "north", "south", "down"),
                                spin=((c0 + 1.0, 8.2, 30.5), 0, 28)))
                els.append(part(f"Card{tag}Bare", (c0, 5.8, 21.0), (c0 + 0.5, 8.2, 44.2), "tyre", faces=(inner,)))
            else:
                els.append(part(f"Card{tag}", (c0, 5.8, 21.0), (c1, 10.9, 44.2), "doorcard", faces=card_faces))
            a0, a1 = X(5.2, 6.6)
            els.append(part(f"Armrest{tag}", (a0, 9.4, 27.0), (a1, 10.4, 37.0), "trim"))
            p0, p1 = X(5.2, 6.0)
            els.append(part(f"Pull{tag}", (p0, 8.0, 36.5), (p1, 8.6, 40.0), "metal"))
            s0, s1 = X(5.2, 5.7)
            els.append(part(f"Speaker{tag}", (s0, 6.4, 24.0), (s1, 8.0, 28.0), "tyre", faces=(inner, "up", "down", "north", "south")))
        return els

    def dashboard(torn):
        els = [
            part("DashPad", (4.0, 9.0, 20.3), (28.0, 11.0, 26.0), "trim", faces=("up", "south", "down")),
            part("DashKnee", (4.0, 6.8, 20.3), (28.0, 9.0, 24.6), "trim", faces=("south", "down")),
            # The binnacle over the driver's dials, with its hood
            part("DashHump", (16.6, 9.0, 22.6), (25.6, 12.4, 26.4), "trim", faces=("north", "east", "west")),
            # (the dials' plate: just the top-left 16 x 6 px of its texture, which is where they are painted)
            part("DashDials", (16.6, 9.0, 26.4), (25.6, 12.4, 26.9), "dials", faces=("south",), uv=(0, 0, 8, 3)),
            part("DashDialsSides", (16.6, 9.0, 26.4), (25.6, 12.4, 26.9), "trim", faces=("east", "west", "down")),
            part("DashHood", (16.2, 12.4, 22.6), (26.0, 13.1, 27.2), "trim"),
            part("Glovebox", (6.6, 7.2, 24.6), (13.2, 8.8, 25.1), "doorcard", faces=("south", "east", "west", "up", "down")),
            part("GloveHandle", (9.4, 8.3, 25.1), (10.4, 8.7, 25.4), "metal"),
            part("Tunnel", (15.0, FLOOR, 23.0), (17.0, 6.9, 41.0), "trim", faces=("up", "north", "south", "east", "west")),
            part("Console", (15.0, 6.9, 30.5), (17.0, 8.3, 36.5), "trim", faces=("up", "north", "south", "east", "west")),
            part("GearLever", (15.75, 6.9, 26.4), (16.25, 9.7, 26.9), "metal", spin=((16.0, 6.9, 26.6), -10, 0)),
            part("GearKnob", (15.55, 9.6, 26.2), (16.45, 10.6, 27.1), "trim"),
            part("PedalA", (17.6, FLOOR, 22.4), (19.0, 6.4, 24.0), "tyre"),
            part("PedalB", (19.8, FLOOR, 22.4), (21.2, 6.4, 24.0), "tyre"),
            part("PedalC", (22.4, FLOOR, 22.4), (23.6, 6.2, 23.8), "tyre"),
        ]
        if torn:
            # The radio has been pulled out of its slot, leaving the hole
            els.append(part("RadioHole", (13.0, 9.2, 26.0), (16.2, 10.8, 26.3), "tyre", faces=("south",)))
        else:
            els.append(part("Radio", (13.0, 9.2, 26.0), (16.2, 10.8, 26.3), "radio", faces=("south",), uv=(0, 0, 6, 3)))
        # The mirror hanging from the roof
        if not torn:
            els += [part("MirrorStem", (15.7, 17.6, 25.7), (16.3, 18.5, 26.2), "metal"),
                    part("Mirror", (14.0, 15.8, 25.8), (18.0, 17.6, 26.4), "trim"),
                    part("MirrorGlass", (14.4, 16.0, 26.4), (17.6, 17.4, 26.6), "glass", faces=("south",))]
        return els

    def roofliner(torn):
        els = [part("Visor", (6.0, 17.6, 25.8), (13.4, 18.5, 27.4), "trim"),
               part("VisorDrive", (18.6, 17.6, 25.8), (26.0, 18.5, 27.4), "trim"),
               part("DomeLamp", (15.0, 18.0, 31.0), (17.4, 18.5, 33.4), "lamp")]
        if torn:
            # The headliner has come unglued and sags from the back
            els.append(part("LinerSag", (5.5, 17.9, 26.8), (26.5, 18.5, 37.8), "liner", faces=("up", "down", "north", "east", "west"),
                            spin=((16.0, 18.5, 37.8), -9, 0)))
        return els

    def litter():
        # Glass crumbs on the seats and floor, a rusted can, a mound of mud and leaves, paper
        return [part("GlassA", (6.9, 8.2, 31.2), (8.3, 8.7, 32.6), "glass"),
                part("GlassB", (20.0, FLOOR, 29.0), (21.8, 6.0, 30.4), "glass"),
                part("GlassC", (24.0, FLOOR, 24.6), (25.6, 6.0, 25.5), "glass"),
                part("GlassD", (10.0, FLOOR, 36.0), (11.2, 6.0, 37.0), "glass"),
                part("Can", (22.0, FLOOR, 24.8), (23.6, 7.0, 26.4), "rim"),
                part("Mud", (6.0, FLOOR, 35.0), (10.4, 6.6, 38.4), "carpet"),
                part("Paper", (12.0, FLOOR, 25.5), (14.6, 6.0, 27.8), "liner")]

    def interior(torn):
        els = [
            part("Carpet", (4.0, 5.0, 20.0), (28.0, FLOOR, 45.0), "carpet", faces=("up",)),
            part("Shelf", (4.0, 10.0, 43.4), (28.0, 10.6, 45.0), "trim", faces=("up", "down", "north")),
        ]
        els += dashboard(torn) + wheel(torn) + front_seat("P", "pass", torn) + front_seat("D", "drive", torn)
        els += rear_bench(torn) + doorcards(torn) + roofliner(torn)
        if torn:
            els += litter()
        return els

    def shell():
        """The car without its inside: the body is open above the floor between the dashboard and the rear shelf."""
        front = box("Body", (4, 3, 1), (28, 11, 20), "body")
        front["faces"]["south"]["texture"] = "#trim"
        rear = box("BodyRear", (4, 3, 45), (28, 11, 63), "body")
        rear["faces"]["north"]["texture"] = "#trim"
        els = [front, rear,
               box("BodyFloor", (4, 3, 20), (28, FLOOR, 45), "body", faces=("down",)),
               *side(1, 4, 1),
               *side(28, 31, 31),
               *glasshouse(),
               box("BumperFront", (1, 3, 0), (31, 6.5, 1), "metal"),
               box("BumperRear", (1, 3, 63), (31, 6.5, 64), "metal"),
               box("Grille", (10, 6.5, 0.7), (22, 9.5, 1), "tyre"),
               box("LampLeft", (3, 7, 0.6), (8, 9.5, 1), "lamp", glow=60),
               box("LampRight", (24, 7, 0.6), (29, 9.5, 1), "lamp", glow=60),
               box("TailLeft", (3, 7.5, 63), (8, 9.5, 63.4), "tail"),
               box("TailRight", (24, 7.5, 63), (29, 9.5, 63.4), "tail")]
        for e in els:
            if e["name"] == "Roof":
                e["faces"]["down"]["texture"] = "#liner"  # (the headliner, from inside)
        return els

    def interior_textures(worn):
        """The texture keys the inside uses: clean, or the wrecks' (worn, stained, split)."""
        t = "backrooms:block/level1/car-"
        if not worn:
            return {"seat": t + "cloth", "trim": t + "trim", "carpet": t + "carpet", "liner": t + "liner", "doorcard": t + "doorcard",
                    "dials": t + "dials", "radio": t + "radio", "foam": t + "foam"}
        return {"seat": t + "seat", "trim": t + "trimworn", "carpet": t + "carpetworn", "liner": t + "linerworn",
                "doorcard": t + "doorcardworn", "dials": t + "dials", "radio": t + "radio", "foam": t + "foam"}

    for colour in ("red", "blue", "white", "black"):
        textures = {"body": f"backrooms:block/level1/car-{colour}", "glass": "backrooms:block/level1/car-glass",
                    "tyre": "backrooms:block/props/metal-dark", "metal": "backrooms:block/props/metal",
                    "lamp": "backrooms:block/props/tube-white", "tail": "backrooms:block/props/valve",
                    **interior_textures(False)}
        save(f"car-{colour}", textures, shell() + interior(False))

    # Level 1's abandoned cars are wrecks of the same car: sat down on flat tyres, the side glass gone (the seats show
    # through), the windscreen crazed round a hole and the rear window out, a headlamp smashed, the bonnet sprung, a
    # hub cap missing, the paint faded and rusting through; the black one burnt out. Same 2x4 footprint
    sag = 1.5

    def wrecked():
        els = []
        for e in json.loads(json.dumps(shell() + interior(True))):
            n = e["name"]
            if n.startswith(("Cabin", "Quarter", "Wheel", "Hub", "RearWindow")):
                continue
            e["from"][1] -= sag
            e["to"][1] -= sag
            if "rotationOrigin" in e:
                e["rotationOrigin"][1] -= sag
            if n == "Windscreen":
                for f in e["faces"].values():
                    f["texture"] = "#glassbroken"
            if n == "LampLeft":
                for f in e["faces"].values():
                    f["texture"] = "#tyre"
                    f.pop("glow", None)
            els.append(e)
        for out_, wx1, wx2 in ((-1, 1.6, 4), (1, 28, 30.4)):
            for nm, c in (("Front", front_arch), ("Rear", rear_arch)):
                tag = ("L" if out_ < 0 else "R") + nm
                els += [box(f"Flat{tag}", (wx1, 0.5, c - 4.5), (wx2, 6, c + 4.5), "tyre"),
                        box(f"Flat{tag}B", (wx1, 0, c - 3.5), (wx2, 7, c + 3.5), "tyre"),
                        box(f"Bulge{tag}", (wx1 - 0.35, 0, c - 4.9), (wx2 + 0.35, 1.3, c + 4.9), "tyre")]
                if tag != "RRear":
                    hx = (1.3, 1.6) if out_ < 0 else (30.4, 30.7)
                    els.append(box(f"Rim{tag}", (hx[0], 2, c - 1.5), (hx[1], 5, c + 1.5), "rim"))
        floor = 11 - sag
        els.append(dict(box("Bonnet", (5, floor, 1.5), (27, floor + 0.7, 15), "body"), rotationOrigin=[16, floor, 15], rotationX=-7))
        return els

    for state, base in (("redwreck", "red"), ("bluewreck", "blue"), ("whitewreck", "white"), ("burnt", "black")):
        textures = {"body": f"backrooms:block/level1/car-{state}", "glass": "backrooms:block/level1/car-glass",
                    "glassbroken": "backrooms:block/level1/car-glass-broken", "rim": PIPE_TEX["rust"],
                    "tyre": "backrooms:block/props/metal-dark", "metal": "backrooms:block/props/metal",
                    "lamp": "backrooms:block/props/tube-white", "tail": "backrooms:block/props/valve",
                    **interior_textures(True)}
        if state == "burnt":
            ash = "backrooms:block/level1/car-burnt"
            textures.update(metal=PIPE_TEX["rust"], lamp="backrooms:block/props/metal-dark", tail="backrooms:block/props/metal-dark",
                            seat=ash, trim=ash, carpet=ash, liner=ash, doorcard=ash)
        save(f"car-{state}", textures, wrecked())


def oriented(name, textures, elements):
    """Props that face a direction are modelled facing north; block variants rotate them."""
    save(name, textures, elements)


# ---------------- Level 3 fixtures (B6: hardware as geometry, from tools/modelkit.py) ----------------

L3_TEX = {k: f"backrooms:block/level3/{v}" for k, v in (
    ("l3paint", "panel-paint"), ("l3face", "panel-face"), ("breaker", "breaker"), ("toggle", "toggle"),
    ("fanhousing", "fan-housing"), ("fanwell", "fan-well"), ("fanblade", "fan-blade"), ("fanguard", "fan-guard"),
    ("tray", "tray"), ("cable", "cable"), ("warn3", "warning"))}


def breaker_panel():
    """A breaker panel on a wall's north face (z < 0 is out of the wall): a grey enamel box with a raised rim round a
    dead front, two columns of five bakelite breakers either side of a bus cover, each toggle pointing in toward the
    bus (on) or out (two have tripped), a label plate and a warning decal; a red main-switch handle on its right side
    and a conduit in a gland up into the wall above. The old panel painted its breakers on a flat box."""
    els = [K.box("Box", (3, 1.5, -2.5), (13, 13.5, 0), {"all": "l3paint", "north": "l3face"}, faces=FRONT_ONLY)]
    rim, _ = K.frame_members("Rim", 3, 1.5, 13, 13.5, -3.0, -2.5, 0.75, "l3paint")
    for e in rim:
        e["faces"].pop("south", None)
    els += rim
    els.append(K.box("Bus", (7.5, 3.25, -2.75), (8.5, 10.75, -2.5), "l3paint", faces=FRONT_ONLY))
    tripped = {2, 6}
    for col, cx in enumerate((5.75, 10.25)):
        inward = 1 if col == 0 else -1
        for row in range(5):
            k, y = col * 5 + row, 4.0 + row * 1.5
            els.append(K.box(f"Breaker{k}", (cx - 1.5, y - 0.5, -3.0), (cx + 1.5, y + 0.5, -2.5), "breaker", faces=FRONT_ONLY))
            tx = cx + 0.5 * (-inward if k in tripped else inward)
            els.append(K.box(f"Toggle{k}", (tx - 0.4, y - 0.25, -3.5), (tx + 0.4, y + 0.25, -3.0), "toggle", faces=FRONT_ONLY))
    els += cab_plate("Label", 5.0, 11.4, 11.0, 12.6, -2.5, "cablabel")
    els += cab_plate("Warn", 4.0, 2.4, 5.25, 3.65, -2.5, "warn3")
    els.append(K.box("SwitchBoss", (13, 7, -2.0), (13.75, 9.5, -0.5), "l3paint", faces=("north", "east", "up", "down")))
    els.append(K.box("SwitchHandle", (13.75, 7.75, -1.75), (14.5, 12.0, -0.75), "cabneedle"))
    els.append(K.box("Gland", (6.75, 13.5, -2.25), (9.25, 14.25, 0), "metal", faces=("north", "east", "west", "up")))
    els.append(K.box("Conduit", (7.25, 14.25, -1.75), (8.75, 16, -0.25), "metal", faces=("north", "east", "west")))
    return els


# ---------------- (L3 placement) Level 3's fittings that lead somewhere, from layout version 9 ----------------
# Blocktype l3fitting (gen_blocktypes.py): Level 3 wall blocks like l3wallfixture's, their fittings on all four faces.

def pipe_gauges():
    """Two pressure gauges in the wall pipes (WALL_PIPE_RUST, WALL_PIPE_LAG), on the north face: one standing on a stem
    out of the top of the lagged pipe, through a steel band round the lagging, the other hanging on a stem from a clamp
    on the steel pipe, both in the gap between the pipes with their dials to the room. In 1-8 the gauges were a
    decoration with a length of pipe of their own, at another height from the wall pipes beside them."""
    ly, lz, lr = WALL_PIPE_LAG
    ry, rz, rr = WALL_PIPE_RUST
    f = ("north", "east", "west", "up", "down")
    out = round_pipe("GABand", ly, lz, lr + 0.3, "flange", 4.1, 5.9, shaded=False, faces=("east", "west"))
    out.append(K.box("GAStem", (4.6, ly + lr - 0.25, lz - 0.4), (5.4, 6.7, lz + 0.4), "flange", faces=f))
    out += K.gauge("GaugeA", 5.0, 8.4, lz + 0.65, r=1.8, angle=-50, face="cabdial", body="cabbezel", needle="cabneedle",
                   depth=1.3, stem=False)
    out += round_pipe("GBClamp", ry, rz, rr + 0.3, "flange", 10.4, 11.6, shaded=False, faces=("east", "west"))
    out.append(K.box("GBStem", (10.6, 9.8, rz - 0.4), (11.4, ry - rr + 0.25, rz + 0.4), "flange", faces=f))
    out += K.gauge("GaugeB", 11.0, 8.15, rz + 0.65, r=1.7, angle=30, face="cabdial", body="cabbezel", needle="cabneedle",
                   depth=1.3, stem=False)
    return out


CABLE_HEIGHTS = ((4.75, 0.8), (7.0, 1.0), (9.5, 0.65))  # gen_detail.wall_cables: each cable's centre height and radius


def panel_box(east=False, west=False):
    """Over a breaker panel (breaker_panel): its conduit carried on up the wall from the panel's gland, in a saddle
    clip, into a cast junction box with a lid screwed on at the corners. With `east` or `west` a cable run along the wall
    comes into the box's side there (gen_detail.wall_cables: three cables, each in a gland reaching to the block's edge,
    where the run's own cables end). In 1-8 the conduit stopped at the wall block above the panel."""
    f = ("north", "east", "west", "up", "down")
    out = [K.box("Conduit", (7.25, 0, -1.75), (8.75, 3.0, -0.25), "metal", faces=("north", "east", "west")),
           K.box("Clip", (6.75, 1.0, -2.0), (9.25, 1.75, 0), "metal", faces=f),
           K.box("Coupling", (6.9, 3.0, -2.0), (9.1, 3.5, 0), "metal", faces=f),
           K.box("Box", (2.75, 3.5, -2.75), (13.25, 12.0, 0), "l3paint", faces=f),
           K.box("Lid", (2.5, 3.25, -3.25), (13.5, 12.25, -2.75), "l3paint", faces=f)]
    for i, (x, y) in enumerate(((3.1, 3.6), (12.3, 3.6), (3.1, 11.3), (12.3, 11.3))):
        out.append(K.box(f"Screw{i}", (x, y, -3.5), (x + 0.6, y + 0.6, -3.25), "metal", faces=f))
    out += cab_plate("Label", 5.0, 9.25, 11.0, 10.75, -3.25, "cablabel")
    for side, on in (("E", east), ("W", west)):
        if not on:
            continue
        for i, (yc, r) in enumerate(CABLE_HEIGHTS):
            zc = -r - 0.05
            x1, x2 = (13.25, 15.95) if side == "E" else (0.05, 2.75)
            out.append(K.box(f"Gland{side}{i}", (x1, yc - r - 0.2, zc - r - 0.2), (x2, yc + r + 0.2, 0), "metal", faces=f))
    return out


def l3_fittings(tex):
    """The l3fitting shapes for one Level 3 wall (tex: the wall's texture dict)."""
    material = tex["wall"].rsplit("-", 1)[1]
    gtex = dict(tex, **CABINET_TEX)
    save(f"l3fitting-{material}-pipesgauge", gtex, [CUBE("wall")] + sides_turned(WALL_PIPES + pipe_gauges()))
    for name, east, west in (("panelbox", False, False), ("panelboxe", True, False), ("panelboxw", False, True), ("panelboxew", True, True)):
        save(f"l3fitting-{material}-{name}", gtex, [CUBE("wall")] + sides_turned(panel_box(east, west)))


def wall_fan():
    """An extract fan set in a wall's north face: a square housing standing 3 px out, its opening rounded by corner
    fillets, four galvanised blades pitched on a hub over a dark well, behind a guard of crossed wire bars. The old
    fan painted its guard on a flat plate."""
    els, openings = K.frame_members("Housing", 2, 2, 14, 14, -3.0, -0.5, 1.5, "fanhousing")
    for e in els:
        e["faces"].pop("south", None)
    els.append(K.box("Flange", (1.5, 1.5, -0.5), (14.5, 14.5, 0), "fanhousing", faces=FRONT_ONLY))
    els.append(K.box("Well", (3.5, 3.5, -0.75), (12.5, 12.5, -0.5), "fanwell", faces=("north",)))
    for i, (cx, cy) in enumerate(((3.5, 3.5), (12.5, 3.5), (3.5, 12.5), (12.5, 12.5))):
        els.append(K.box(f"Fillet{i}", (cx - 1.5, cy - 0.6, -2.75), (cx + 1.5, cy + 0.6, -0.75), "fanhousing",
                         faces=("north", "up", "down"), rot=(0, 0, 45 if (cx - 8) * (cy - 8) < 0 else -45), origin=(cx, cy, -1.75)))
    els.append(K.box("Motor", (6.25, 6.25, -1.25), (9.75, 9.75, -0.75), "fanguard", faces=FRONT_ONLY))
    els += K.bevelled_box("Hub", (7, 7, -2.25), (9, 9, -1.25), "fanguard", b=0.25)
    for name, frm, to, rot in (("BladeUp", (7.25, 9, -1.95), (8.75, 12.25, -1.55), (0, 28, 0)),
                               ("BladeDown", (7.25, 3.75, -1.95), (8.75, 7, -1.55), (0, -28, 0)),
                               ("BladeLeft", (3.75, 7.25, -1.95), (7, 8.75, -1.55), (-28, 0, 0)),
                               ("BladeRight", (9, 7.25, -1.95), (12.25, 8.75, -1.55), (28, 0, 0))):
        els.append(K.box(name, frm, to, "fanblade", rot=rot))
    # the guard: two square rings of wire (rounded at the corners by the fillets behind) and a cross of two bars
    els.append(K.box("GuardV", (7.75, 3.5, -3.3), (8.25, 12.5, -3.05), "fanguard", faces=("north", "east", "west")))
    els.append(K.box("GuardH", (3.5, 7.75, -3.05), (12.5, 8.25, -2.8), "fanguard", faces=("north", "up", "down")))
    for i, (a, b) in enumerate(((4.75, 11.25),)):
        z1, z2 = -3.55, -3.3
        els += [K.box(f"Ring{i}T", (a, b - 0.5, z1), (b, b, z2), "fanguard", faces=("north", "up", "down", "east", "west")),
                K.box(f"Ring{i}B", (a, a, z1), (b, a + 0.5, z2), "fanguard", faces=("north", "up", "down", "east", "west")),
                K.box(f"Ring{i}L", (a, a + 0.5, z1), (a + 0.5, b - 0.5, z2), "fanguard", faces=("north", "east", "west")),
                K.box(f"Ring{i}R", (b - 0.5, a + 0.5, z1), (b, b - 0.5, z2), "fanguard", faces=("north", "east", "west"))]
    return els


def tray_x(cables=True):
    """A cable tray along X under the ceiling: a galvanised trough (a solid bottom and two low side rails; round 2:
    the first cut's ladder of rungs and tall rails made every ceiling a lattice) with five cables of three sizes in
    it, round in section (two crossed boxes each); hung on a strut trapeze from two rods into the ceiling."""
    t = "tray"
    out = [K.box("Bottom", (0, 11.5, 1.0), (16, 12.0, 15.0), t, faces=("north", "south", "up", "down")),
           K.box("RailN", (0, 12.0, 1.0), (16, 12.75, 1.5), t, faces=("north", "south", "up")),
           K.box("RailS", (0, 12.0, 14.5), (16, 12.75, 15.0), t, faces=("north", "south", "up"))]
    if cables:
        for i, (zc, r) in enumerate(((3.25, 1.2), (5.75, 1.0), (8.5, 1.45), (11.25, 1.0), (13.0, 0.7))):
            out.append(K.box(f"Cable{i}", (0, 12.0, zc - r * 0.65), (16, 12.0 + 2 * r, zc + r * 0.65), "cable", faces=("up", "down")))
            out.append(K.box(f"Cable{i}b", (0, 12.0 + 0.35 * r, zc - r), (16, 12.0 + 1.65 * r, zc + r), "cable",
                             faces=("north", "south", "up", "down")))
    out += [K.box("Strut", (7.25, 10.75, 0.25), (8.75, 11.5, 15.75), t),
            K.box("Rod1", (7.75, 11.5, 0.25), (8.25, 16, 0.75), "metal", faces=("north", "south", "east", "west")),
            K.box("Rod2", (7.75, 11.5, 15.25), (8.25, 16, 15.75), "metal", faces=("north", "south", "east", "west"))]
    return out


def cable_light(tube_tex, hung):
    """The dim fluorescent fitting under a tray (or, with `hung`, on chains from the ceiling): a galvanised housing
    with bevelled edges and a lamp holder at each end, and the tube under it (the same tube as before: the light comes
    from the blocktype, not the shape)."""
    lit = tube_tex == "tube"
    els = K.bevelled_box("Housing", (2, 9.5, 6.5), (14, 11, 9.5), "tray", b=0.25)
    els += [K.box("HolderW", (1.5, 8.6, 6.9), (2, 10.75, 9.1), "metal"), K.box("HolderE", (14, 8.6, 6.9), (14.5, 10.75, 9.1), "metal"),
            box("Tube", (2, 8.8, 7), (14, 9.5, 9), tube_tex, glow=255 if lit else 0)]
    top = 16 if hung else 11.5
    els += [K.box("Chain1", (4, 11, 7.75), (4.5, top, 8.25), "metal"), K.box("Chain2", (11.5, 11, 7.75), (12, top, 8.25), "metal")]
    if hung:
        els += [K.box("Rose1", (3.5, 15.5, 7.25), (5, 16, 8.75), "metal"), K.box("Rose2", (11, 15.5, 7.25), (12.5, 16, 8.75), "metal")]
    return els


def transformer():
    """Level 3's humming transformer: a tank on a skid with a bolted lid, banks of cooling fins on both sides on
    header pipes (the old texture painted its fins over flat ones), three porcelain bushings on the lid, each a stem
    with three sheds and a terminal, a nameplate and a warning decal on the front, and a cable box low down."""
    body = {"all": "body", "top": "top"}
    els = [K.box("Skid", (1.5, 0, 2.5), (14.5, 1, 13.5), "fin"),
           K.box("Tank", (2.5, 1, 3.5), (13.5, 11.5, 12.5), body, faces=("north", "east", "west", "south")),
           K.box("Lid", (2, 11.5, 3), (14, 12.5, 13), body)]
    for i, x in enumerate((3, 5.5, 8, 10.5, 13)):
        for j, z in enumerate((3.25, 12.25)):
            els.append(K.box(f"Bolt{i}{j}", (x - 0.25, 12.5, z), (x + 0.25, 12.75, z + 0.5), "metal", faces=("north", "south", "east", "west", "up")))
    for side, xa, xb, (ha, hb) in (("W", 0.25, 1.75, (1.0, 2.5)), ("E", 14.25, 15.75, (13.5, 15.0))):
        els.append(K.box(f"Header{side}Lo", (ha, 1.75, 4.25), (hb, 2.5, 11.75), "fin"))
        els.append(K.box(f"Header{side}Hi", (ha, 9.75, 4.25), (hb, 10.5, 11.75), "fin"))
        for i in range(6):
            z = 4.5 + i * 1.35
            els.append(K.box(f"Fin{side}{i}", (xa, 2.0, z), (xb, 10.75, z + 0.5), "fin"))
    for i, x in enumerate((5, 8, 11)):
        z = 8
        els.append(K.box(f"Stem{i}", (x - 0.5, 12.5, z - 0.5), (x + 0.5, 16.5, z + 0.5), "insulator", faces=("north", "south", "east", "west")))
        for k, y in enumerate((13.25, 14.5, 15.75)):
            els.append(K.box(f"Shed{i}{k}", (x - 1.1, y, z - 1.1), (x + 1.1, y + 0.5, z + 1.1), "insulator"))
        els.append(K.box(f"Terminal{i}", (x - 0.3, 16.5, z - 0.3), (x + 0.3, 17.25, z + 0.3), "metal"))
    els += cab_plate("Plate", 4.5, 6.5, 8.5, 8.5, 3.5, "cablabel")
    els += cab_plate("Warn", 9.75, 6.5, 11.75, 8.5, 3.5, "warn3")
    els.append(K.box("CableBox", (9.5, 1.75, 2.75), (12.5, 4.5, 3.5), body, faces=FRONT_ONLY))
    els.append(K.box("Gland", (10.5, 1, 2.9), (11.5, 1.75, 3.4), "metal", faces=("north", "east", "west")))
    return els


def level3():
    cables = {"cable": "backrooms:block/level3/cable", "metal": "backrooms:block/props/metal",
              "tray": "backrooms:block/level3/tray",
              "tube": "backrooms:block/props/tube-warm", "tubeoff": "backrooms:block/props/tube-off"}

    save("cables-run", cables, tray_x())
    # Where two trays cross: the one along X runs through, the other's cables cross over its rails into a junction box
    # (its own rails stop at the neighbouring blocks)
    cross = [b for b in tray_x() if b["name"].startswith("Cable")]
    save("cables-hub", cables, tray_x() + thinner([dict(rot(b, 1), name=b["name"] + "Z") for b in cross]) +
         K.bevelled_box("Box", (4.95, 9, 4.95), (11.05, 16, 11.05), "tray", b=0.5))  # (a hair wider than the cables)
    # A tray ending with open hall beyond it (east end): an end plate the cables run into
    save("cables-end", cables, tray_x() + [box("EndPlate", (15.5, 11.5, 0.8), (16, 15, 15.7), "tray")])
    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        save(f"cablelight-{state}", cables, tray_x() + cable_light(tex, False))
        # The same fixture hanging on its chains from the ceiling, with no tray (the middle of a gallery)
        save(f"cablelight-plain-{state}", cables, cable_light(tex, True))

    save("transformer", {"body": "backrooms:block/level3/transformer", "fin": "backrooms:block/level3/transformer-fin",
                         "top": "backrooms:block/level3/transformer-top", "metal": "backrooms:block/props/metal-dark",
                         "insulator": "backrooms:block/level3/insulator", "cablabel": CABINET_TEX["cablabel"],
                         "warn3": L3_TEX["warn3"]}, transformer())

    for material in ("glazed", "brick", "cinder"):
        tex = {"wall": f"backrooms:block/level3/l3wall-{material}", **PIPE_TEX, **WALL_PIPE_TEX}
        save(f"l3wall-{material}-pipes", tex, [CUBE("wall")] + all_sides(WALL_PIPES))
        save(f"l3wall-{material}-pipesjoint", tex, [CUBE("wall")] + all_sides(WALL_PIPES + wall_pipe_joint()))
        save(f"l3wall-{material}-pipesbracket", tex, [CUBE("wall")] + all_sides(WALL_PIPES + wall_pipe_bracket()))
        ftex = dict(tex, **L3_TEX, cablabel=CABINET_TEX["cablabel"], cabneedle=CABINET_TEX["cabneedle"])
        save(f"l3wall-{material}-panel", ftex, [CUBE("wall")] + sides_turned(breaker_panel()))
        save(f"l3wall-{material}-fan", ftex, [CUBE("wall")] + sides_turned(wall_fan()))
        # (L3 placement, layout version 9) gauges in the wall pipes, and the junction box over a panel
        l3_fittings(ftex)

    # Bars standing in a west-east plane across the middle of the block: round steel (two crossed boxes each), every
    # face showing the whole width of the bar texture's shading so the specular stripe runs down each; the rails take
    # the texture's other half, turned
    def steel(b, uv):
        for f in b["faces"].values():
            f["uv"] = list(uv)
        return b
    bars = []
    for i, x in enumerate((0.5, 3.5, 6.5, 9.5, 12.5)):
        bars.append(steel(box(f"Bar{i}", (x, 0, 7.45), (x + 1.5, 16, 8.55), "bars", faces=("north", "south")), (0, 0, 8, 16)))
        bars.append(steel(box(f"Bar{i}b", (x + 0.2, 0, 7.25), (x + 1.3, 16, 8.75), "bars", faces=("north", "south", "east", "west")), (0, 0, 8, 16)))
    bars += [steel(box("RailTop", (0, 14, 7), (16, 15.5, 9), "bars"), (8, 0, 16, 16)),
             steel(box("RailBottom", (0, 1, 7), (16, 2.5, 9), "bars"), (8, 0, 16, 16))]
    save("ironbars", {"bars": "backrooms:block/level3/bars"}, bars)

    # The frame is 2 px: the hole (12 px) takes a player (9.6 px) climbing up against the rungs, which stand 3 px off
    # the north wall, clear of the frame's north side (gen_blocktypes.py gives both their collision boxes)
    save("manhole", {"iron": "backrooms:block/level3/manhole", "floor": "backrooms:block/level3/dustyfloor"}, [
        box("North", (0, 0, 0), (16, 16, 2), "floor"),
        box("South", (0, 0, 14), (16, 16, 16), "floor"),
        box("West", (0, 0, 2), (2, 16, 14), "floor"),
        box("East", (14, 0, 2), (16, 16, 14), "floor"),
        box("Rim", (2.5, 15.5, 2.5), (13.5, 16.2, 13.5), "iron", faces=("up",)),
    ])
    save("rungs", {"metal": PIPE_TEX["rust"]}, [
        box(f"Rung{i}", (4, y, 2), (12, y + 1, 3), "metal") for i, y in enumerate((2, 6, 10, 14))
    ] + [box("RailL", (3, 0, 0.5), (4, 16, 3), "metal"), box("RailR", (12, 0, 0.5), (13, 16, 3), "metal")])
    manhole_ladder()



# ---------------- Level 3: the manholes of layout version 9 ----------------

MANHOLE_TEX = {"ladder": "backrooms:block/level3/manholeladder", "iron": "backrooms:block/level3/manhole",
               "lip": "backrooms:block/level3/hazardlip", "lid": "backrooms:block/level3/hatchlid",
               "concrete": "backrooms:block/concrete"}


def manhole_ladder():
    """Layout version 9's manhole (WorldLayout.AddManholeTunnel): an opening two blocks long with a ladder two wide
    down one side of it, from the dry landing at the foot to the lip, in two halves (left and right as seen facing
    the ladder; the blocktype turns them to the side they are on). Modelled on the north face: the ladder stands off
    the wall at z 0-3.5 (its collision box is the vanilla ladder's, 3 px deep), the opening runs on to z 16. The
    rails are at the two outer ends only and the rungs run on across the join, so the pair reads as one ladder.

    The top half (at the floor) carries the lip: a hazard-striped steel frame half a pixel proud of the floor round
    the opening, drawn only (the opening is the whole two blocks, nothing to stand on but the ladder's own top);
    the rails standing on above the floor and hooking over the opening, as a manhole's grab rails do; and the open
    lid, a chequer-plate leaf standing up on its hinges along the far edge. None of these has a collision box, so
    nothing narrows the way in."""
    def half(left, top):
        def X(a, b):  # a span across the half, measured from its outer end (mirrored for the right half)
            return (a, b) if left else (16 - b, 16 - a)

        def bx(name, x, y, z, tex, faces=DIRS):
            (x1, x2) = X(*x)
            return box(name, (x1, y[0], z[0]), (x2, y[1], z[1]), tex, faces=faces)

        outer = ("west",) if left else ("east",)
        inner = ("east",) if left else ("west",)
        els = [bx("Rail", (1, 2.5), (0, 16), (1, 3.5), "ladder"),
               bx("BracketLow", (1.25, 2.25), (3, 4), (0, 1), "iron", faces=("east", "west", "up", "down")),
               bx("BracketHigh", (1.25, 2.25), (11, 12), (0, 1), "iron", faces=("east", "west", "up", "down")),
               # The stay in the middle of the span, against the wall (half of it in each half)
               bx("Stay", (15, 16), (5.5, 6.5), (0, 1.75), "iron", faces=outer + ("south", "up", "down"))]
        for i, y in enumerate((1.5, 5.5, 9.5, 13.5)):
            els.append(bx(f"Rung{i}", (2.5, 16), (y, y + 1), (1.75, 3.25), "ladder", faces=("north", "south", "up", "down")))
        if not top:
            return els
        # The lip round the opening: along the far edge, the outer end and the ladder's own edge
        els += [bx("LipFar", (0, 16), (15, 16.5), (14.5, 16), "lip", faces=("up", "north")),
                bx("LipEnd", (0, 1.5), (15, 16.5), (1, 14.5), "lip", faces=("up",) + inner),
                bx("LipNear", (0, 16), (15, 16.5), (0, 1), "lip", faces=("up", "south"))]
        # The rails stand on above the floor and hook over the opening
        els += [bx("RailTop", (1, 2.5), (16, 27), (1, 3.5), "ladder"),
                bx("RailHook", (1, 2.5), (25.5, 27), (3.5, 8), "ladder", faces=("east", "west", "up", "down", "south")),
                bx("RailHookDrop", (1, 2.5), (21, 25.5), (6.5, 8), "ladder", faces=("east", "west", "down", "north", "south"))]
        # The open lid, standing up along the far edge on two hinges, a pull handle on the face toward the opening
        lid = bx("Lid", (1, 16), (16.5, 29.5), (13, 14), "lid", faces=("north", "south", "up") + outer)
        lid["rotationOrigin"], lid["rotationX"] = [8, 16.5, 13.5], -5
        els += [lid,
                bx("HingeA", (4, 6.5), (15.5, 17.5), (13, 15), "iron"),
                bx("HingeB", (11, 13.5), (15.5, 17.5), (13, 15), "iron"),
                bx("Handle", (12, 16), (24, 25), (11.8, 12.8), "iron", faces=("north", "up", "down") + outer)]
        return els

    for top in (True, False):
        for left in (True, False):
            name = ("top" if top else "") + ("left" if left else "right")
            save(f"manholeladder-{name}", MANHOLE_TEX, half(left, top))
    # The half step up out of the flooded tunnel onto the landing, its edges painted
    save("tunnelstep", MANHOLE_TEX, [
        box("Step", (0, 0, 0), (16, 8, 16), "concrete"),
        box("NoseN", (0, 8, 0), (16, 8.2, 1.5), "lip", faces=("up", "north")),
        box("NoseS", (0, 8, 14.5), (16, 8.2, 16), "lip", faces=("up", "south")),
        box("NoseW", (0, 8, 1.5), (1.5, 8.2, 14.5), "lip", faces=("up", "west")),
        box("NoseE", (14.5, 8, 1.5), (16, 8.2, 14.5), "lip", faces=("up", "east")),
    ])

# ---------------- Level 4: the office furniture (graphics pass B7, hardware and furniture from tools/modelkit.py) ----------------

L4_TEX = {k: f"backrooms:block/level4/{v}" for k, v in (
    ("lam", "laminate"), ("lamv", "laminate-v"), ("lamedge", "laminate-edge"), ("crt", "crt"), ("screen", "crt-screen"),
    ("keys", "keys"), ("chairfabric", "chairfabric"), ("chairplastic", "chairplastic"), ("filing", "filing"),
    ("filingtop", "filing-top"), ("partition", "partition"), ("prail", "partitionrail"), ("prailtop", "partitionrail-top"),
    ("pbase", "partitionbase"), ("vending", "vending"), ("vendglow", "vending-glow"), ("vendbottle", "vending-bottle"),
    ("vendpanel", "vending-panel"), ("cooler", "cooler"), ("water", "coolerbottle"))}
L4_TEX.update({"metal": "backrooms:block/props/metal", "metaldark": "backrooms:block/props/metal-dark",
               "paper": "backrooms:block/detail/paper", "filinglabel": "backrooms:block/detail/filinglabel",
               "cablampred": "backrooms:block/level2/cabinet-lampred"})


def top_side(top, side, bottom=None):
    return {"top": top, "side": side, "bottom": bottom or top}


def world_v(el, faces=("north", "south")):
    """Sets a box's side faces to world-aligned UVs (u along x, v = 16 - y within its 16-unit band), so a texture runs
    on across stacked boxes and from block to block (the partition's fabric). The box must lie in one band."""
    (x1, y1, _), (x2, y2, _) = el["from"], el["to"]
    band = 16 * math.floor((y2 - 0.001) / 16)
    for f in faces:
        if f in el["faces"]:
            el["faces"][f]["uv"] = [x1 % 16, 16 - (y2 - band), x1 % 16 + (x2 - x1), 16 - (y1 - band)]
    return el


def partition():
    """A cubicle panel running west-east, 1.5 blocks tall: the fabric panel between aluminium posts at its two ends
    (where it meets the next panel of a run they make one joint), an aluminium top cap with bevelled edges whose sides
    carry a lit rolled edge, and a dark base raceway at its foot. The fabric runs on from panel to panel (world UVs).
    The old one was a grey box with a 1 px rail. Inside the old collision box (z 6-10)."""
    els = [K.box("Base", (0, 0, 6.5), (16, 1.5, 9.5), "pbase", faces=("north", "south", "east", "west", "down"))]
    for nm, (y1, y2) in (("Fabric", (1.5, 16)), ("Fabric2", (16, 22.5))):
        els.append(world_v(K.box(nm, (0.5, y1, 6.75), (15.5, y2, 9.25), "partition", faces=("north", "south"))))
    for nm, x1 in (("PostW", 0), ("PostE", 15.5)):
        els.append(K.box(nm, (x1, 1.5, 6.5), (x1 + 0.5, 22.5, 9.5), "prailtop", faces=("north", "south", "east", "west")))
    els += K.bevelled_box("Cap", (0, 22.5, 6.25), (16, 24, 9.75), top_side("prailtop", "prail"), b=0.25)
    return els


def crt(x1, y1, z1, tex="crt", screen="screen"):
    """A beige CRT terminal standing on a desk at y1, its front to the north at z1: a bezel as a frame of four parts
    round the screen set back in it (glowing faintly, as the old one did), a power lamp, the case behind with
    bevelled edges, and the tube's hump at the back."""
    x2 = x1 + 8
    y0 = y1 + 0.5
    els = [K.box("CrtFoot", (x1 + 1.5, y1, z1 + 1.5), (x2 - 1.5, y0, z1 + 6), tex, faces=("north", "south", "east", "west", "up"))]
    els += K.bevelled_box("CrtCase", (x1, y0, z1 + 0.5), (x2, y0 + 6.5, z1 + 6.5), tex, b=0.5)
    els += [K.box("CrtBezelT", (x1 + 0.25, y0 + 5.25, z1), (x2 - 0.25, y0 + 6.25, z1 + 0.5), tex, faces=("north", "up", "down", "east", "west")),
            K.box("CrtBezelB", (x1 + 0.25, y0 + 0.25, z1), (x2 - 0.25, y0 + 1.5, z1 + 0.5), tex, faces=("north", "up", "down", "east", "west")),
            K.box("CrtBezelL", (x1 + 0.25, y0 + 1.5, z1), (x1 + 1.25, y0 + 5.25, z1 + 0.5), tex, faces=("north", "east", "west")),
            K.box("CrtBezelR", (x2 - 1.25, y0 + 1.5, z1), (x2 - 0.25, y0 + 5.25, z1 + 0.5), tex, faces=("north", "east", "west")),
            K.box("CrtScreen", (x1 + 1.25, y0 + 1.5, z1 + 0.4), (x2 - 1.25, y0 + 5.25, z1 + 0.5), screen, faces=("north",), glow=30,
                  uv=[1, 2, 15, 14]),
            K.box("CrtLed", (x2 - 2, y0 + 0.5, z1 - 0.25), (x2 - 1.5, y0 + 1, z1), "cablampred", faces=("north", "up", "east", "west")),
            K.box("CrtHump", (x1 + 1.5, y0 + 0.75, z1 + 6.5), (x2 - 1.5, y0 + 5.5, z1 + 8.5), tex, faces=("south", "east", "west", "up", "down"))]
    return els


def desk():
    """An office desk facing north: a laminate top (grain on top, dark edge-banding round it) on two end panels, a
    modesty panel at the back, a pedestal of three drawers under the right-hand end (inset fronts, bar pulls), the old
    beige terminal with its keyboard, a mouse and a stack of paper. The old one was boxes in one flat texture."""
    lam = top_side("lam", "lamedge")
    end = {"side": "lamv", "front": "lamedge", "back": "lamedge", "bottom": "lamedge"}
    els = [K.box("Top", (0, 11.5, 1.5), (16, 12.5, 14.5), lam),
           K.box("EndL", (0.75, 0, 2.25), (1.75, 11.5, 14), end, faces=("north", "south", "east", "west", "down")),
           K.box("EndR", (14.25, 0, 2.25), (15.25, 11.5, 14), end, faces=("north", "south", "east", "west", "down")),
           K.box("Modesty", (1.75, 3.5, 12.75), (14.25, 11.5, 13.5), "lamv", faces=("north", "south", "down")),
           K.box("Pedestal", (10.25, 0.5, 2.75), (14.25, 11.5, 12.75), "lamv", faces=("north", "west", "down"))]
    for i, (y1, y2) in enumerate(((0.75, 4.25), (4.5, 7.75), (8.0, 11.25))):
        els += K.bevelled_box(f"Drawer{i}", (10.5, y1, 2.0), (14, y2, 2.75), "lamv", b=0.25)
        els += K.handle(f"Pull{i}", 12.25, y2 - 1.0, 2.0, length=2.0, axis="x", standoff=0.5, thick=0.5, tex="metal")
    els += crt(4, 12.5, 5.5)
    els += [K.box("Keyboard", (4, 12.5, 2.25), (12, 13, 4.75), "crt", faces=("north", "south", "east", "west", "up")),
            K.box("Keys", (4.5, 13, 2.5), (11.5, 13.5, 4.5), {"top": "keys", "side": "crt"}, faces=("up", "north", "east", "west", "south")),
            K.box("Mouse", (13, 12.5, 3), (14, 13, 4.5), "crt", faces=("north", "south", "east", "west", "up")),
            K.box("Papers", (0.75, 12.5, 7.5), (3.75, 13, 11.5), "paper", faces=("north", "south", "east", "west", "up"))]
    return els


def office_chair(fabric="chairfabric", plastic="chairplastic", metal="metaldark"):
    """A swivel office chair facing north: an upholstered seat and back cushion (bevelled), a plastic seat pan and back
    shell, the bar joining them, two T-armrests, the gas lift, and a five-star base on casters (each arm turned 72
    degrees about the column). The old one was a seat, a back and a cross of two bars. Shared with the tipped chair
    in gen_detail, whose keys are the same."""
    els = []
    els += K.bevelled_box("Seat", (3.5, 6.5, 3), (12.5, 8.5, 12), fabric, b=0.5)
    els += [K.box("Pan", (4, 5.75, 3.5), (12, 6.5, 11.5), plastic, faces=("north", "south", "east", "west", "down"))]
    els += K.bevelled_box("Back", (4, 9.5, 12.25), (12, 17.5, 13.75), fabric, b=0.5)
    els += [K.box("Shell", (4.5, 10, 13.75), (11.5, 17, 14.25), plastic, faces=("south", "east", "west", "up", "down")),
            K.box("Spine", (7.25, 6, 12), (8.75, 9.5, 14.5), plastic, faces=("south", "east", "west", "down", "north")),
            K.box("Lift", (7.4, 1.5, 7.15), (8.6, 5.75, 8.35), metal, faces=("north", "south", "east", "west")),
            K.box("Hub", (7, 1, 6.75), (9, 1.5, 8.75), plastic, faces=("north", "south", "east", "west", "up"))]
    for side, x in (("L", 3), ("R", 12)):
        els += [K.box("ArmPost" + side, (x, 6.5, 6.75), (x + 1, 11, 7.75), plastic, faces=("north", "south", "east", "west")),
                K.box("ArmPad" + side, (x - 0.25, 11, 5), (x + 1.25, 11.75, 10), plastic)]
    for k in range(5):
        a = k * 72
        els += [K.box(f"Leg{k}", (7.5, 0.75, 2), (8.5, 1.5, 7.75), plastic, rot=(0, a, 0), origin=(8, 1, 7.75),
                      faces=("north", "east", "west", "up", "down")),
                K.box(f"Caster{k}", (7.25, 0, 1.5), (8.75, 0.75, 2.75), metal, rot=(0, a, 0), origin=(8, 1, 7.75))]
    return els


def filing_cabinet():
    """A three-drawer steel filing cabinet: the carcass in blue-grey enamel with a dustier top, three drawer fronts
    standing proud on a recessed plinth, each with a bar pull and a label holder with its card, a lock in the top
    drawer. The old one painted the drawers' seams."""
    els = [K.box("Carcass", (2, 0.75, 2.5), (14, 15.5, 14), "filing", faces=("north", "south", "east", "west")),
           K.box("Plinth", (2.5, 0, 3), (13.5, 0.75, 13.5), "metaldark", faces=("north", "south", "east", "west")),
           K.box("Lid", (1.75, 15.5, 2.25), (14.25, 16, 14.25), {"top": "filingtop", "side": "filing", "bottom": "filing"})]
    for i, (y1, y2) in enumerate(((1.0, 5.25), (5.5, 10.25), (10.5, 15.25))):
        els += K.bevelled_box(f"Drawer{i}", (2.25, y1, 1.75), (13.75, y2, 2.5), "filing", b=0.25)
        els += K.handle(f"Pull{i}", 8, y2 - 2.5, 1.75, length=3.5, axis="x", standoff=0.5, thick=0.5, tex="metal")
        els += [K.box(f"Label{i}", (6.75, y2 - 1.5, 1.5), (9.25, y2 - 0.75, 1.75), {"front": "filinglabel", "side": "metal"},
                      faces=("north", "east", "west", "up", "down"), uv=[0.5, 0.5, 7.5, 3.5])]
    els.append(K.box("Lock", (11.5, 13.75, 1.25), (12.5, 14.75, 1.75), "metal", faces=("north", "east", "west", "up", "down")))
    return els


def conference_table():
    """A block of the long conference table: the laminate top runs on block to block with no edge between them (its
    edge-banding shows only where a side is open), on a steel column with a cross foot under each block."""
    return [K.box("Top", (0, 11, 0), (16, 12.5, 16), top_side("lam", "lamedge")),
            K.box("Spider", (5, 10.5, 5), (11, 11, 11), "metaldark", faces=("north", "south", "east", "west", "down")),
            K.box("Column", (6.75, 1, 6.75), (9.25, 10.5, 9.25), "metaldark", faces=("north", "south", "east", "west")),
            K.box("FootX", (2, 0, 7), (14, 1, 9), "metaldark"),
            K.box("FootZ", (7, 0, 2), (9, 0.99, 14), "metaldark", faces=("north", "south", "east", "west", "up"))]


def water_cooler():
    """The water cooler full of Almond Water: a white enamel cabinet with bevelled edges, a recessed dispensing bay with
    a drip grille, a hot (red) and a cold (blue) tap, a collar on top, and the bottle upside down in it: an octagonal
    body with two ribs, a shoulder and a neck down into the collar."""
    els = K.bevelled_box("Body", (4, 0, 4), (12, 13, 12), "cooler", b=0.5)
    els += [K.box("Bay", (5, 6, 3.5), (11, 10.5, 4), "metaldark", faces=("north", "up", "down", "east", "west")),
            K.box("Grille", (5.5, 6, 2.75), (10.5, 6.5, 3.5), "metal"),
            K.box("TapHot", (5.75, 9.5, 3), (7, 10.5, 3.5), "cablampred", faces=("north", "east", "west", "up", "down")),
            K.box("TapCold", (9, 9.5, 3), (10.25, 10.5, 3.5), "water", faces=("north", "east", "west", "up", "down")),
            K.box("Collar", (5, 13, 5), (11, 14, 11), "cooler", faces=("north", "south", "east", "west", "up")),
            K.box("Neck", (7, 14, 7), (9, 15, 9), "water", faces=("north", "south", "east", "west"))]
    els += octagon("Shoulder", 8, 8, 2.5, 15, 16, "water", faces=("north", "east", "south", "west", "down"), lift=0.01)
    els += octagon("Bottle", 8, 8, 3.5, 16, 22.5, "water", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    for k, y in enumerate((18, 20.5)):
        els += octagon(f"Rib{k}", 8, 8, 3.75, y, y + 0.5, "water", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    return els


def vending_machine():
    """The vending machine that still sells Almond Water: a red enamel cabinet, the window set back into its front (a
    frame of four parts round it), lit from the back wall inside (the old glow), four shelves with rows of bottles
    standing on them, a dark selection panel with a keypad and a coin slot to the right, and the delivery flap at
    the foot. The old one painted all of it on one box."""
    els = [K.box("Core", (0.5, 0, 4.5), (15.5, 28, 15), "vending"),
           K.box("FrameB", (0.5, 0, 2), (15.5, 9, 4.5), "vending", faces=("north", "east", "west", "up", "down")),
           K.box("FrameT", (0.5, 26, 2), (15.5, 28, 4.5), "vending", faces=("north", "east", "west", "up", "down")),
           K.box("FrameL", (0.5, 9, 2), (2, 26, 4.5), "vending", faces=("north", "east", "west")),
           K.box("FrameR", (11, 9, 2), (15.5, 26, 4.5), "vending", faces=("north", "east", "west")),
           K.box("Glow", (2, 9, 4.4), (11, 26, 4.5), "vendglow", faces=("north",), glow=90),
           K.box("Panel", (11.75, 12, 1.75), (14.75, 24, 2), "vendpanel", faces=("north", "east", "west", "up", "down")),
           K.box("Flap", (2.5, 3, 1.75), (10.5, 6.5, 2), "metaldark", faces=("north", "east", "west", "up", "down")),
           K.box("Slot", (12.75, 21, 1.5), (13.75, 22.5, 1.75), "metal", faces=("north", "east", "west", "up", "down"))]
    els += K.keypad("Keys", 12.25, 13, 1.75, cols=3, rows=4, key=0.5, gap=0.25, border=0.25, plate="vendpanel", keys="metal")
    for r, y in enumerate((9, 13.25, 17.5, 21.75)):
        if r:
            els.append(K.box(f"Shelf{r}", (2, y, 2.5), (11, y + 0.5, 4.4), "metal", faces=("north", "up", "down")))
        for c in range(4):
            x = 2.5 + c * 2.15
            els += [K.box(f"Bottle{r}{c}", (x, y + 0.5, 3), (x + 1.25, y + 3, 4.25), "vendbottle", faces=("north", "east", "west", "up")),
                    K.box(f"Cap{r}{c}", (x + 0.25, y + 3, 3.25), (x + 1, y + 3.5, 4), "vendpanel", faces=("north", "east", "west", "up"))]
    return els


def level4():
    t = dict(L4_TEX)
    for name, els in (("partition", partition()), ("desk", desk()), ("officechair", office_chair()),
                      ("filingcabinet", filing_cabinet()), ("vendingmachine", vending_machine()),
                      ("watercooler", water_cooler()), ("conferencetable", conference_table())):
        used = K.textures(els)
        save(name, {k: v for k, v in t.items() if k in used}, els)


# ---------------- The boiler (Level 5's boiler bays and Level 3's boiler rooms; B6) ----------------

BOILER_TEX = {"shell": "backrooms:block/level5/boiler", "band": "backrooms:block/level5/boiler-band",
              "door": "backrooms:block/level5/boiler-door", "cabdial": CABINET_TEX["cabdial"],
              "cabneedle": CABINET_TEX["cabneedle"], "cabbezel": CABINET_TEX["cabbezel"], "cablabel": CABINET_TEX["cablabel"]}


def octagon(name, cx, cz, a, y1, y2, tex, faces=("north", "east", "south", "west"), lift=0.0):
    """A regular octagonal prism of apothem `a` about (cx, cz), from y1 to y2: two crossed boxes and the same two
    turned 45 degrees. Each box's top and bottom sit `lift` x its index higher, so where they overlap their caps do
    not lie in one plane."""
    w = a * math.tan(math.radians(22.5))
    out = []
    for i, (hx, hz, r) in enumerate(((a, w, 0), (w, a, 0), (a, w, 45), (w, a, 45))):
        out.append(K.box(f"{name}{i}", (cx - hx, y1 + lift * i, cz - hz), (cx + hx, y2 + lift * i, cz + hz), tex, faces=faces,
                         rot=(0, r, 0) if r else None, origin=(cx, y1, cz)))
    return out


def boiler():
    """A vertical coal-fired boiler, front to the north: a round riveted shell (an octagon of plates, in two lifts so
    the plate texture keeps its scale) on a cast plinth, three iron bands, a stepped crown and the flue rising from it
    (where the blocktype's steam leaves, 26/16 up at 8, 9), a safety valve; on the front a firebox door on hinges with
    a latch and a peep slot, a nameplate and a pressure gauge as geometry. The old one was a box with a painted rivet
    grid and a flat plate for the gauge."""
    cx, cz, a = 8.0, 8.5, 6.5
    els = octagon("Plinth", cx, cz, 7.2, 0, 1.5, "band", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("ShellLo", cx, cz, a, 1.5, 13.5, "shell")
    els += octagon("ShellHi", cx, cz, a, 13.5, 24, "shell")
    for k, y in enumerate((6.5, 13.1, 19.5)):
        els += octagon(f"Band{k}", cx, cz, a + 0.3, y, y + 0.8, "band", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    els += octagon("Crown", cx, cz, a - 0.75, 24, 25, "band", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Dome", cx, cz, a - 2.25, 25, 26, "shell", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += [K.box("Collar", (5.5, 26, 6.5), (10.5, 27, 11.5), "band"),
            K.box("Flue", (6, 27, 7), (10, 32, 11), "rust", faces=("north", "east", "south", "west")),
            K.box("ValveBody", (10.75, 26, 4.75), (12.25, 28, 6.25), "band"),
            K.box("ValveLever", (9.5, 28, 5.25), (13.5, 28.5, 5.75), "rust"),
            K.box("ValveWeight", (9, 27.25, 5), (10, 28.25, 6), "band")]
    z = cz - a  # the front plate
    els += K.bevelled_box("Door", (5, 3.25, z - 0.75), (11, 9.75, z), "door", b=0.25)
    els += K.hinge("Hinge1", 11, 3.75, 5.25, z - 0.75, tex="band", side="right")
    els += K.hinge("Hinge2", 11, 7.75, 9.25, z - 0.75, tex="band", side="right")
    els += K.handle("Latch", 6.5, 6.5, z - 0.75, length=2.5, axis="x", standoff=0.6, thick=0.6, tex="band")
    els.append(K.box("Peep", (7.25, 8.0, z - 1.0), (8.75, 8.75, z - 0.75), "band", faces=("north", "east", "west", "up", "down")))
    els += cab_plate("Plate", 5.5, 11.0, 10.5, 12.75, z, "cablabel")
    els += K.gauge("Gauge", 8, 17.25, z, r=2.0, angle=-25, face="cabdial", body="cabbezel", needle="cabneedle", depth=1.25)
    return els


D4_BOILER = True  # (graphics pass D4) facet plates of riveted iron, strap hoops, a round flue; False: B6's boiler()
BOILER_D4_TEX = {"strap": "backrooms:block/level5/boiler-strap", "flue": "backrooms:block/level5/boiler-flue"}


def octo_plates(name, cx, cz, a, y1, y2, tex, scale=1.5, course=0, t=0.05):
    """(D4) The eight faces of an octagonal prism of apothem `a` about (cx, cz) as eight thin plates, each facing out:
    four square to the axes, four turned 45 degrees about the axis. Unlike `octagon`, whose crossed boxes show only the
    middle of each face's texture, every plate maps its own window of the texture onto itself: 8 units across (a
    16 px plate of the boiler's iron) by its height at `scale` texels per unit, at a height and a column chosen per
    plate from `course`, so neighbouring faces show different plates and runs. Faces out only; the caller closes the
    prism's top and bottom."""
    w = a * math.tan(math.radians(22.5))
    hh = round(min(16.0, (y2 - y1) * scale), 3)
    out = []
    for k in range(8):
        axis, diag = k // 2, k % 2
        if axis == 0:
            frm, to, face = (cx - w, y1, cz - a), (cx + w, y2, cz - a + t), "north"
        elif axis == 1:
            frm, to, face = (cx + a - t, y1, cz - w), (cx + a, y2, cz + w), "east"
        elif axis == 2:
            frm, to, face = (cx - w, y1, cz + a - t), (cx + w, y2, cz + a), "south"
        else:
            frm, to, face = (cx - a, y1, cz - w), (cx - a + t, y2, cz + w), "west"
        u0 = 8.0 * ((k + course) % 2)
        room = max(0.0, 16.0 - hh)
        v0 = round(room * (((k * 5 + course * 3) % 7) / 6.0) * 2) / 2 if room else 0.0
        e = K.box(f"{name}{k}", frm, to, tex, faces=(face,), uv=[u0, v0, u0 + 8, round(v0 + hh, 3)],
                  rot=(0, 45, 0) if diag else None, origin=(cx, y1, cz))
        out.append(e)
    return out


def boiler_d4():
    """(D4) The boiler again, after B8 graded B6's C in the hotel's boiler bays (a clay-orange shell at a low density,
    a box for a flue). Same footprint, height, front and steam point. The shell is eight riveted iron plates a course
    (`octo_plates`: each face its own plate at one and a half times the block's density, the rivets of a lap seam down
    every corner), in four courses, with a strap hoop of rivets over each course joint (octagonal, proud 0.3, its
    caps lit and shaded by the game); the crown and dome as before; the flue an octagonal column with a collar at its
    foot and a lip at its top. The firebox door, hinges, latch, peep slot, nameplate, gauge and safety valve as B6's."""
    cx, cz, a = 8.0, 8.5, 6.5
    els = octagon("Plinth", cx, cz, 7.2, 0, 1.5, "band", faces=("north", "east", "south", "west", "up"), lift=0.01)
    joints = (6.9, 13.5, 19.9)
    edges = (1.5,) + joints + (24.0,)
    for c, (y1, y2) in enumerate(zip(edges, edges[1:])):
        els += octo_plates(f"Shell{c}", cx, cz, a, y1, y2, "shell", course=c)
    els += octagon("ShellTop", cx, cz, a, 23.9, 24, "shell", faces=("up",), lift=0.01)
    for k, y in enumerate(joints):
        y1, y2 = y - 0.5, y + 0.5
        els += octagon(f"Strap{k}", cx, cz, a + 0.3, y1, y2, "band", faces=("up", "down"), lift=0.01)
        for e in octo_plates(f"StrapFace{k}", cx, cz, a + 0.3, y1, y2, "strap", course=k):
            f = next(iter(e["faces"].values()))
            f["uv"] = [f["uv"][0], 4.0 * k + 0.0, f["uv"][0] + 8, 4.0 * k + 2.0]  # one strap of the 4 px pattern
            els.append(e)
    els += octagon("Crown", cx, cz, a - 0.75, 24, 25, "band", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Dome", cx, cz, a - 2.25, 25, 26, "shell", faces=("north", "east", "south", "west", "up"), lift=0.01)
    # the flue: an octagonal column on a collar, a lip round its mouth (its end is the steam point's, 8, 9)
    els += octagon("Collar", 8, 9, 2.6, 26, 27, "band", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Flue", 8, 9, 1.9, 27, 31.3, "flue", faces=("north", "east", "south", "west"))
    els += octagon("FlueLip", 8, 9, 2.2, 31.3, 31.9, "band", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    els += [K.box("ValveBody", (10.75, 26, 4.75), (12.25, 28, 6.25), "band"),
            K.box("ValveLever", (9.5, 28, 5.25), (13.5, 28.5, 5.75), "rust"),
            K.box("ValveWeight", (9, 27.25, 5), (10, 28.25, 6), "band")]
    z = cz - a  # the front plate
    els += K.bevelled_box("Door", (5, 3.25, z - 0.75), (11, 9.75, z), "door", b=0.25)
    els += K.hinge("Hinge1", 11, 3.75, 5.25, z - 0.75, tex="band", side="right")
    els += K.hinge("Hinge2", 11, 7.75, 9.25, z - 0.75, tex="band", side="right")
    els += K.handle("Latch", 6.5, 6.5, z - 0.75, length=2.5, axis="x", standoff=0.6, thick=0.6, tex="band")
    els.append(K.box("Peep", (7.25, 8.0, z - 1.0), (8.75, 8.75, z - 0.75), "band", faces=("north", "east", "west", "up", "down")))
    els += cab_plate("Plate", 5.5, 11.0, 10.5, 12.75, z, "cablabel")
    els += K.gauge("Gauge", 8, 17.25, z, r=2.0, angle=-25, face="cabdial", body="cabbezel", needle="cabneedle", depth=1.25)
    return els


# ---------------- Level 5 (graphics pass B8) ----------------

def four_sides(els):
    """Parts modelled on the north face of a block, copied onto all four faces (modelkit.turn: rotated parts, such as
    an octagon's turned boxes, keep their rotation about their own moved origin)."""
    out = []
    for i in range(4):
        out += [dict(e, name=f"{e['name']}{i}") for e in K.turn(els, i)]
    return out


HOTEL_DOOR_TEX = {k: f"backrooms:block/level5/{v}" for k, v in (
    ("doorwood", "hoteldoor-wood"), ("doorrail", "hoteldoor-rail"), ("casing", "hoteldoor-casing"),
    ("doordark", "hoteldoor-dark"), ("plate", "hoteldoor-plate0"), ("brass", "brass"))}


def slim_hinge(name, y1, y2):
    """(B8 round 2) A door's butt hinge seen from the front: two slim barrels at the hinge edge, between the casing and
    the stile, with a pin cap (modelkit.hinge's leaf and knuckles read as a brass patch on the door from a few blocks)."""
    mid = (y1 + y2) / 2
    return [K.box(name + "BarrelA", (1.5, y1, -0.95), (1.95, mid - 0.15, -0.5), "brass", faces=("north", "east", "west", "up", "down")),
            K.box(name + "BarrelB", (1.5, mid + 0.15, -0.95), (1.95, y2, -0.5), "brass", faces=("north", "east", "west", "up", "down")),
            K.box(name + "Pin", (1.6, y2, -0.85), (1.85, y2 + 0.3, -0.6), "brass", faces=("north", "east", "west", "up"))]


def door_knob(name, x, y, z):
    """(B8 round 2) A round brass knob as one piece: a thin rose, a short neck, and a head of two crossed boxes (an
    eight-sided round) with a smaller face on it, so it reads as a knob and not as stacked cubes."""
    return [K.box(name + "Rose", (x - 0.55, y - 0.55, z - 0.15), (x + 0.55, y + 0.55, z), "brass", faces=("north", "east", "west", "up", "down")),
            K.box(name + "Neck", (x - 0.2, y - 0.2, z - 0.7), (x + 0.2, y + 0.2, z - 0.15), "brass", faces=("east", "west", "up", "down")),
            K.box(name + "HeadA", (x - 0.65, y - 0.35, z - 1.5), (x + 0.65, y + 0.35, z - 0.7), "brass"),
            K.box(name + "HeadB", (x - 0.35, y - 0.65, z - 1.45), (x + 0.35, y + 0.65, z - 0.75), "brass"),
            K.box(name + "Face", (x - 0.3, y - 0.3, z - 1.6), (x + 0.3, y + 0.3, z - 1.5), "brass", faces=("north", "east", "west", "up", "down"))]


def hotel_door(part):
    """(B8) A guest-room door, two blocks high, as geometry (it was a cube with its mouldings and brass plate painted
    on). A mahogany casing round the opening, with plinth blocks at its foot and a capped head; a frame-and-panel leaf:
    stiles and rails standing out of the leaf, a raised field in each of its two panels; a brass kick plate with its
    screws, a knob on a tall escutcheon with a keyhole, two butt hinges, a peephole, and on the upper field the brass
    number plate (its face, `plate`, is the number: the blocktype gives each door its own, gen_blocktypes).
    The block has no facing (it stands in the wall line between a corridor and a room), so, as Level 2's steel doors
    (B5), the leaf is the cube itself and everything else stands out of it on all four sides; on the two sides along
    the wall it is buried in the wall blocks."""
    # (round 2) The casing stops E short of the block's sides: the copies of it on the buried sides would otherwise put
    # a face exactly on the neighbouring wall's face, which shimmered beside every door
    E = 0.05
    hw = []
    if part == "lower":
        hw += [K.box("CasingL", (E, 3.5, -1), (1.5, 16, 0), "casing", faces=("north", "east", "west")),
               K.box("CasingR", (14.5, 3.5, -1), (16 - E, 16, 0), "casing", faces=("north", "east", "west")),
               K.box("PlinthL", (E, 0, -1.25), (1.75, 3.5, 0), "casing", faces=("north", "east", "west", "up")),
               K.box("PlinthR", (14.25, 0, -1.25), (16 - E, 3.5, 0), "casing", faces=("north", "east", "west", "up")),
               K.box("StileL", (1.75, 0, -0.5), (3.25, 16, 0), "doorwood", faces=("north", "east")),
               K.box("StileR", (12.75, 0, -0.5), (14.25, 16, 0), "doorwood", faces=("north", "west")),
               K.box("RailBottom", (3.25, 0, -0.5), (12.75, 3.5, 0), "doorrail", faces=("north", "up")),
               K.box("RailLock", (3.25, 12.5, -0.5), (12.75, 15, 0), "doorrail", faces=("north", "up", "down")),
               K.box("Field", (4.25, 4.5, -0.25), (11.75, 11.5, 0), "doorwood", faces=("north", "east", "west", "up", "down"))]
        hw += K.kick_plate("Kick", 2.0, 14.0, 0.5, 3.0, -0.5, tex="brass")
        hw += [K.box("Escutcheon", (13.05, 11.25, -0.75), (14.15, 15.25, -0.5), "brass", faces=("north", "east", "west", "up", "down")),
               K.box("Keyhole", (13.45, 11.8, -0.8), (13.75, 12.6, -0.75), "doordark", faces=("north",))]
        hw += door_knob("Knob", 13.6, 13.9, -0.75)
        hw += slim_hinge("Hinge", 4.0, 6.5)
    else:
        hw += [K.box("CasingL", (E, 0, -1), (1.5, 14.5, 0), "casing", faces=("north", "east", "west")),
               K.box("CasingR", (14.5, 0, -1), (16 - E, 14.5, 0), "casing", faces=("north", "east", "west")),
               K.box("Head", (E, 14.5, -1), (16 - E, 15.25, 0), "casing", faces=("north", "east", "west", "down")),
               K.box("HeadCap", (E, 15.25, -1.5), (16 - E, 16, 0), "casing", faces=("north", "east", "west", "up", "down")),
               K.box("StileL", (1.75, 0, -0.5), (3.25, 14.5, 0), "doorwood", faces=("north", "east")),
               K.box("StileR", (12.75, 0, -0.5), (14.25, 14.5, 0), "doorwood", faces=("north", "west")),
               K.box("RailTop", (3.25, 11, -0.5), (12.75, 14.5, 0), "doorrail", faces=("north", "down")),
               K.box("Field", (4.25, 0, -0.25), (11.75, 10, 0), "doorwood", faces=("north", "east", "west", "up", "down")),
               K.box("Plate", (4, 5.5, -0.75), (12, 9.5, -0.25), "plate", faces=("north",), uv=[0, 0, 16, 16]),
               K.box("PlateEdge", (4, 5.5, -0.75), (12, 9.5, -0.25), "brass", faces=("east", "west", "up", "down")),
               K.box("Peephole", (7.6, 12.35, -0.75), (8.4, 13.15, -0.5), "brass", faces=("north", "east", "west", "up", "down")),
               K.box("PeepLens", (7.8, 12.55, -0.8), (8.2, 12.95, -0.75), "doordark", faces=("north",))]
        for i, (x, y) in enumerate(((4.3, 5.8), (11.3, 5.8), (4.3, 8.8), (11.3, 8.8))):
            hw.append(K.box(f"Screw{i}", (x, y, -0.85), (x + 0.4, y + 0.4, -0.75), "brass", faces=("north", "east", "west", "up", "down")))
        hw += slim_hinge("Hinge", 9.0, 11.5)
    leaf = box("Leaf", (0, 0, 0), (16, 16, 16), "doorwood")
    return [leaf] + four_sides(hw)


def chandelier():
    """(B8) The grand rooms' chandelier (drawn larger than its block, the flames where they were: gen_blocktypes
    `_chandelier_flames`): a canopy at the ceiling, a chain of links, a turned brass column with knops over a bowl and
    a crystal finial; eight arms out from the hub (two straight across and two diagonals), each turning up at its end
    into a drip pan and a candle cup; crystal drops hanging from the arms. It was a flat gold plate with candles on it."""
    els = octagon("Canopy", 8, 8, 2.0, 15.25, 16, "brass", faces=("north", "east", "south", "west", "down"), lift=0.01)
    for i, y in enumerate((14.0, 12.6, 11.2, 9.8)):  # chain links, alternately across and along
        if i % 2:
            els.append(K.box(f"Link{i}", (7.65, y, 7.2), (8.35, y + 1.4, 8.8), "brass", faces=("north", "east", "south", "west")))
        else:
            els.append(K.box(f"Link{i}", (7.2, y, 7.65), (8.8, y + 1.4, 8.35), "brass", faces=("north", "east", "south", "west")))
    els.append(K.box("Ring", (7.5, 9.2, 7.5), (8.5, 9.8, 8.5), "brass"))
    els += octagon("Knop", 8, 8, 1.1, 8.4, 9.2, "brass", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    els += octagon("Stem", 8, 8, 0.55, 6.6, 8.4, "brass", lift=0.01)
    els += octagon("Hub", 8, 8, 1.7, 4.4, 6.6, "brass", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Bowl", 8, 8, 1.2, 3.2, 4.4, "brass", faces=("north", "east", "south", "west", "down"), lift=0.01)
    els += octagon("Finial", 8, 8, 0.7, 1.4, 3.2, "crystal", faces=("north", "east", "south", "west", "down"), lift=0.01)
    els.append(K.box("Drop", (7.6, 0.4, 7.6), (8.4, 1.4, 8.4), "crystal", glow=120, faces=("north", "east", "south", "west", "down")))
    # the arms: two straight across, two diagonals (their ends at the diagonal candles, 15.56 out)
    els += [K.box("ArmX", (-4, 4.8, 7.6), (20, 5.4, 8.4), "brass"),
            K.box("ArmZ", (7.6, 4.81, -4), (8.4, 5.39, 20), "brass")]
    d = 15.56
    for k, r in enumerate((45, -45)):
        els.append(K.box(f"ArmD{k}", (8 - d, 4.82 + 0.01 * k, 7.6), (8 + d, 5.38 - 0.01 * k, 8.4), "brass", rot=(0, r, 0), origin=(8, 5.1, 8)))
    for i, (x, z) in enumerate(((-3, -3), (8, -4), (19, -3), (-4, 8), (20, 8), (-3, 19), (8, 20), (19, 19))):
        els.append(K.box(f"Riser{i}", (x - 0.35, 5.4, z - 0.35), (x + 0.35, 5.6, z + 0.35), "brass", faces=("north", "east", "south", "west")))
        els += octagon(f"Pan{i}", x, z, 1.3, 5.6, 5.85, "brass", faces=("north", "east", "south", "west", "up", "down"), lift=0.005)
        els += octagon(f"Cup{i}", x, z, 0.85, 5.85, 6.3, "brass", faces=("north", "east", "south", "west"), lift=0.005)
        els.append(K.box(f"Candle{i}", (x - 0.6, 6, z - 0.6), (x + 0.6, 8.5, z + 0.6), "candle", glow=220))
        # a crystal drop hanging from the arm halfway out
        mx, mz = 8 + (x - 8) * 0.5, 8 + (z - 8) * 0.5
        els.append(K.box(f"Drop{i}", (mx - 0.4, 2.8, mz - 0.4), (mx + 0.4, 4.8, mz + 0.4), "crystal", glow=90,
                         faces=("north", "east", "south", "west", "down"), rot=(0, 45, 0), origin=(mx, 2.8, mz)))
    return els



# ---------------- Graphics pass B10: the furniture of Fort Surrender (also Level 5's) ----------------
#
# Level 7's shelters are built from Level 5's furniture, held together with tar (WorldLayout.Level7.Shelter), so the
# wardrobe and the wing chair are re-made here as geometry; they keep their codes, footprints and collision boxes
# (gen_blocktypes.level5) and stand in Level 5's rooms too. Front to the north, as every oriented prop.

def wardrobe_b10():
    """A mahogany wardrobe: a plinth with a toe recess, side panels, a cornice in two steps, and two doors, each a frame
    round two raised and fielded panels, meeting at the middle with a brass pull on each and an escutcheon on the right
    door. (Was a box with a painted seam and two brass bars.)"""
    w = "wood"
    els = [box("Plinth", (1, 0, 5.5), (15, 2, 16), w),
           box("PlinthFront", (1.25, 0.25, 5), (14.75, 2, 5.5), w, faces=("north", "east", "west", "up")),
           box("SideL", (1, 2, 5), (2, 28, 16), w), box("SideR", (14, 2, 5), (15, 28, 16), w),
           box("Carcass", (2, 2, 6), (14, 28, 16), w, faces=("north", "south")),  # (round 2: its back closed)
           box("Rail", (2, 2, 5), (14, 2.75, 6), w, faces=("north", "up")),
           box("Head", (2, 27.25, 5), (14, 28, 6), w, faces=("north", "down")),
           box("Cornice", (0.75, 28, 4.6), (15.25, 29, 16), w),
           box("Cap", (0.5, 29, 4.2), (15.5, 30, 16), w)]
    for side, (x1, x2) in (("L", (2.25, 7.9)), ("R", (8.1, 13.75))):
        els += K.frame_and_panel("Door" + side, (x1, 2.75, 5.25), (x2, 27.25, 6.25), w, border=1.5, depth=0.5, grid=(1, 2),
                                 raised=0.25, mid=1.5, both_sides=False)
    els += K.handle("PullL", 7.25, 15, 5.25, length=2.5, standoff=0.6, thick=0.5, tex="brass")
    els += K.handle("PullR", 8.75, 15, 5.25, length=2.5, standoff=0.6, thick=0.5, tex="brass")
    els += [K.box("Escutcheon", (8.6, 12.4, 5.0), (9.1, 13.4, 5.25), "brass", faces=("north", "east", "west", "up", "down"))]
    return els


def wing_chair_b10():
    """A wingback armchair in the hotel's red velvet: four short mahogany legs under a skirted seat, a cushion with a
    soft front edge, a back with a rolled top, and on each side a wing that sweeps forward into a rolled arm. (Was five
    boxes.)"""
    v, w = "velvet", "wood"
    els = []
    for i, (x, z) in enumerate(((3, 3), (11.5, 3), (3, 12.5), (11.5, 12.5))):
        els += [box(f"Leg{i}", (x + 0.25, 0, z + 0.25), (x + 1.25, 2.5, z + 1.25), w),
                box(f"LegTop{i}", (x, 2.5, z), (x + 1.5, 3, z + 1.5), w, faces=("north", "east", "south", "west", "down"))]
    els += [box("Skirt", (2.5, 3, 2.5), (13.5, 6, 14.5), v)]
    els += K.bevelled_box("Cushion", (3.5, 6, 2.25), (12.5, 8.25, 12.5), v, b=0.5)
    els += [box("Back", (3.5, 6, 12.5), (12.5, 20, 14.5), v)]
    els += K.bevelled_box("BackRoll", (3.25, 19.5, 12.25), (12.75, 21.5, 14.75), v, b=0.5)
    for side, (xa, xb) in (("L", (1.75, 3.5)), ("R", (12.5, 14.25))):
        els += [box("Arm" + side, (xa, 6, 3.5), (xb, 10, 14.5), v),
                box("Wing" + side, (xa, 10, 8), (xb, 19, 14.5), v),
                box("WingFront" + side, (xa + 0.25, 10, 6), (xb - 0.25, 15, 8), v, faces=("north", "east", "west", "up"))]
        els += K.bevelled_box("ArmRoll" + side, (xa - 0.25, 8.5, 2.75), (xb + 0.25, 10.75, 13), v, b=0.5)
    return els


def palm_b14():
    """(B14) The potted palm: a round terracotta pot (an octagon) with a rolled rim and soil in it, a trunk of stub rings
    narrowing as it climbs, and eight fronds: each a blade stepping out and down from the crown in three narrowing
    pieces, four along the axes and four turned 45 degrees about the trunk. (Was a box pot, a stick and four flat plates.)
    Inside its block's 0.5-wide collision column up to the crown; the fronds reach out over the neighbours."""
    els = octagon("Pot", 8, 8, 3.4, 0, 6.0, "pot", faces=("north", "east", "south", "west", "down"), lift=0.01)
    els += octagon("Rim", 8, 8, 4.0, 6.0, 7.4, "pot", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    els += octagon("Soil", 8, 8, 3.5, 7.2, 7.45, "soil", faces=("up",), lift=0.01)
    for k, (r, y1, y2) in enumerate(((1.3, 7.3, 10.5), (1.15, 10.5, 13.5), (1.0, 13.5, 16.5), (0.9, 16.5, 19.5))):
        els.append(box(f"Trunk{k}", (8 - r, y1, 8 - r), (8 + r, y2, 8 + r), "palmtrunk"))
    els.append(box("Crown", (6.8, 19.5, 6.8), (9.2, 20.6, 9.2), "palmtrunk"))
    # A frond along +x from the crown: blades end to end, each tipped down further than the last (one rotation each,
    # about its inner end); four along the axes (turned with modelkit.turn), four under a parent turned 45 degrees
    def frond(pre, y0, phis, lens, hws):
        out, sx, sy = [], 9.0, y0
        for k, (phi, L, hw) in enumerate(zip(phis, lens, hws)):
            e = box(f"{pre}S{k}", (sx, sy - 0.18, 8 - hw), (sx + L, sy + 0.18, 8 + hw), "leaf")
            e["rotationOrigin"], e["rotationZ"] = [sx, sy, 8], phi
            out.append(e)
            sx, sy = sx + L * math.cos(math.radians(phi)), sy + L * math.sin(math.radians(phi))
        return out
    for i in range(4):
        els += K.turn(frond(f"Frond{i}", 20.2, (20, -5, -30, -55), (3.5, 3.2, 2.8, 2.2), (1.5, 1.4, 1.1, 0.6)), i)
        els.append({"name": f"FrondDiag{i}", "from": [0, 0, 0], "to": [0, 0, 0], "rotationOrigin": [8, 0, 8], "rotationY": 45,
                    "faces": {}, "children": K.turn(frond(f"FrondD{i}", 19.6, (35, 10, -20, -45), (3.0, 3.0, 2.6, 2.0),
                                                          (1.3, 1.2, 1.0, 0.5)), i)})
    els.append(box("Spear", (7.4, 20.6, 7.6), (8.6, 23.6, 8.4), "leaf"))
    return els


def level5():
    t = {"panel": "backrooms:block/level5/hotelwall-panel", "brass": "backrooms:block/level5/brass",
         "candle": "backrooms:block/props/tube-warm", "gilt": "backrooms:block/level5/gilt",
         "portrait": "backrooms:block/level5/portrait", "placard": "backrooms:block/level5/beverly",
         "cream": "backrooms:block/level5/hotelceiling-cream", "glass": "backrooms:block/level5/domeglass",
         "crystal": "backrooms:block/level5/crystal", "wood": "backrooms:block/level5/mahogany",
         "linen": "backrooms:block/level5/linen", "blanket": "backrooms:block/level5/blanket",
         "velvet": "backrooms:block/level5/velvet", "leaf": "backrooms:block/level5/palmleaf",
         "pot": "backrooms:block/level5/pot", "felt": "backrooms:block/level5/felt", "tile": "backrooms:block/level5/mahjong",
         "record": "backrooms:block/props/metal-dark", "boiler": "backrooms:block/level5/boiler",
         "iron": "backrooms:block/props/metal-dark", "fire": "backrooms:block/level5/fire", "rust": PIPE_TEX["rust"],
         "lampshade": "backrooms:block/level5/lampshade", "bottle": "backrooms:block/detail/bankergreen"}

    # (B8) The sconce: a bevelled brass backplate with a boss, an arm out from it turning up under a drip pan, a cup,
    # and the candle with a run of wax down its side (the candle stays where it was: the flames are placed there,
    # gen_blocktypes._sconce_flames)
    sconce = K.bevelled_box("Plate", (6.25, 3.5, -0.75), (9.75, 10.5, 0), "brass", b=0.25)
    sconce += [K.box("Boss", (7.25, 6.25, -1.5), (8.75, 7.75, -0.75), "brass", faces=("north", "east", "west", "up", "down")),
               K.box("Arm", (7.6, 6.6, -3.4), (8.4, 7.4, -1.5), "brass", faces=("north", "east", "west", "up", "down")),
               K.box("Riser", (7.6, 7.4, -3.4), (8.4, 8.0, -2.6), "brass", faces=("north", "east", "south", "west"))]
    sconce += octagon("Pan", 8, -3, 1.6, 8.0, 8.4, "brass", faces=("north", "east", "south", "west", "up", "down"), lift=0.01)
    sconce += octagon("Cup", 8, -3, 0.95, 8.45, 9.2, "brass", faces=("north", "east", "south", "west"), lift=0.01)
    sconce += [K.box("Candle", (7.5, 9.2, -3.5), (8.5, 12, -2.5), "candle", glow=180),
               K.box("Drip", (8.5, 10.1, -3.25), (8.8, 11.7, -2.95), "candle", glow=180, faces=("north", "east", "south", "down")),
               K.box("Wick", (7.9, 12, -3.1), (8.1, 12.5, -2.9), "wick", faces=("north", "east", "south", "west", "up"))]
    save("hotelfixture-sconce", dict(t, wick="backrooms:block/level5/hoteldoor-dark"), [CUBE("panel")] + four_sides(sconce))

    # (B8) The portrait's frame as a moulding in three steps: the frame proud of the wall, a bead along its middle and
    # an inner lip, the canvas set back behind them. The canvas key has other prints as alternates (gen_blocktypes)
    def frame(name, x1, y1, x2, y2, w, z1, z2, tex):
        return [K.box(name + "T", (x1, y2 - w, z1), (x2, y2, z2), tex, faces=("north", "east", "west", "up", "down")),
                K.box(name + "B", (x1, y1, z1), (x2, y1 + w, z2), tex, faces=("north", "east", "west", "up", "down")),
                K.box(name + "L", (x1, y1 + w, z1), (x1 + w, y2 - w, z2), tex, faces=("north", "east", "west")),
                K.box(name + "R", (x2 - w, y1 + w, z1), (x2, y2 - w, z2), tex, faces=("north", "east", "west"))]
    portrait = frame("Frame", 2, 2, 14, 15, 1.25, -1.0, 0, "gilt") + frame("Bead", 2.4, 2.4, 13.6, 14.6, 0.5, -1.35, -1.0, "gilt")
    portrait += frame("Lip", 3.25, 3.25, 12.75, 13.75, 0.5, -0.6, 0, "gilt")
    portrait.append(K.box("Canvas", (3.75, 3.75, -0.35), (12.25, 13.25, -0.25), "portrait", faces=("north",), uv=[0, 0, 16, 16]))
    save("hotelfixture-portrait", t, [CUBE("panel")] + four_sides(portrait))
    # (B8) The Beverly Room's placard: an engraved nickel plate on a bevelled mahogany mount, four brass screws
    beverly = K.bevelled_box("Mount", (1.5, 4.5, -0.5), (14.5, 11.5, 0), "wood", b=0.2)
    beverly += [K.box("Placard", (2.25, 5.25, -0.85), (13.75, 10.75, -0.5), "placard", faces=("north",), uv=[0, 0, 16, 16]),
                K.box("PlacardEdge", (2.25, 5.25, -0.85), (13.75, 10.75, -0.5), "placard", faces=("east", "west", "up", "down"),
                      uv=[0, 0, 0.5, 0.5])]
    for i, (x, y) in enumerate(((2.6, 5.6), (13.0, 5.6), (2.6, 10.0), (13.0, 10.0))):
        beverly.append(K.box(f"Screw{i}", (x, y, -0.95), (x + 0.4, y + 0.4, -0.85), "brass", faces=("north", "east", "west", "up", "down")))
    save("hotelfixture-beverly", t, [CUBE("panel")] + four_sides(beverly))

    for state, glow in (("lit", 200), ("off", 0)):
        save(f"domelight-{state}", t, [CUBE("cream"),
            box("Base", (5, -0.5, 5), (11, 0, 11), "brass"),
            box("Dome", (5.5, -3, 5.5), (10.5, -0.5, 10.5), "glass", glow=glow)])

    # The grand rooms' coffered ceiling: cream slabs, and every fourth row and column a mahogany beam hanging 4 px
    # under them with a moulded bead along its foot. Only the faces that can be seen are drawn; the blocks let light
    # through, so the beams' sides are lit by the room rather than by the dark slab beside them.
    # (B8) A fillet runs along both sides of each beam where it meets the slab, so every coffer has a moulding round
    # it; the beams' mahogany has grain along them (gen_textures.wood_grain)
    slab = box("Slab", (0, 0, 0), (16, 16, 16), "cream", faces=("down",))

    def beam_x(x1=0, x2=16, f1=None, f2=None):
        f1, f2 = x1 if f1 is None else f1, x2 if f2 is None else f2
        return [box("Beam", (x1, -4, 5.5), (x2, 0, 10.5), "wood", faces=("north", "south", "down")),
                box("Bead", (x1, -4.6, 6.5), (x2, -4, 9.5), "wood", faces=("north", "south", "down")),
                box("FilletN", (f1, -0.75, 4.75), (f2, 0, 5.5), "wood", faces=("north", "down")),
                box("FilletS", (f1, -0.75, 10.5), (f2, 0, 11.25), "wood", faces=("south", "down"))]

    save("hotelceiling-coffer", t, [slab])
    save("hotelceiling-beam", t, [slab] + beam_x())
    # Where two beams cross, the one along Z stops at the sides of the one along X (its fillets at the X beam's)
    save("hotelceiling-beamcross", t, [slab] + beam_x() + [
        dict(rot(b, 1), name=b["name"] + "Z" + str(i)) for i, (x1, x2, f1, f2) in enumerate(((0, 5.5, 0, 4.75), (10.5, 16, 11.25, 16)))
        for b in beam_x(x1, x2, f1, f2)])

    save("chandelier", t, chandelier())

    # A front hall's grand staircase (layout 5), climbing toward the north like the concrete stairs: white marble
    # steps, and on the middle one of a flight a red runner over treads and risers, held by brass stair rods
    # (B8) Plain veined marble (the floor's black keystones showed as dark triangles on the steps), a rounded nosing
    # standing out over each riser, and the stair rods with finials at their ends
    stairs = {"marble": "backrooms:block/detail/marbletop", "carpet": "backrooms:block/level5/hotelcarpet-damask",
              "brass": "backrooms:block/level5/brass"}
    steps = [box("Lower", (0, 0, 0), (16, 8, 16), "marble"), box("Upper", (0, 8, 0), (16, 16, 8), "marble")]

    def nosing(x1, x2, y, z, tag):
        return [box("Nosing" + tag, (x1, y - 0.75, z), (x2, y, z + 0.6), "marble", faces=("south", "up", "down", "east", "west")),
                box("NosingRound" + tag, (x1, y - 0.5, z + 0.6), (x2, y - 0.25, z + 0.75), "marble", faces=("south", "up", "down", "east", "west"))]
    save("hotelstairs-marble", stairs, steps + nosing(0, 16, 8, 16, "L") + nosing(0, 16, 16, 8, "U"))

    def rod(tag, y, z):
        return [box("Rod" + tag, (1.5, y, z), (14.5, y + 0.6, z + 0.6), "brass"),
                box("FinialL" + tag, (1.0, y - 0.1, z - 0.1), (1.5, y + 0.7, z + 0.7), "brass"),
                box("FinialR" + tag, (14.5, y - 0.1, z - 0.1), (15.0, y + 0.7, z + 0.7), "brass")]
    save("hotelstairs-runner", stairs, steps + [
        box("TreadLower", (2, 8, 8.4), (14, 8.4, 16), "carpet", faces=("up", "east", "west")),
        box("RiserLower", (2, 0, 16), (14, 8.4, 16.4), "carpet", faces=("south", "up", "east", "west")),
        box("RiserUpper", (2, 8, 8), (14, 16.4, 8.4), "carpet", faces=("south", "up", "east", "west")),
        box("TreadUpper", (2, 16, 0), (14, 16.4, 8), "carpet", faces=("up", "east", "west")),
    ] + rod("Upper", 8.4, 8.4) + rod("Lower", 0, 16.4)
        + nosing(0, 1.6, 8, 16, "LW") + nosing(14.4, 16, 8, 16, "LE") + nosing(0, 1.6, 16, 8, "UW") + nosing(14.4, 16, 16, 8, "UE"))

    for part in ("lower", "upper"):
        save(f"hoteldoor-{part}", dict(t, **HOTEL_DOOR_TEX), hotel_door(part))

    import l5props as L5  # (Level 5 art)
    l5 = dict(t, **{k: f"backrooms:block/detail/{k}" for k in (
        "l5sheet", "l5pillow", "l5coverlet", "l5mattress", "l5skirt")})
    l5["mahogany"] = t["wood"]
    oriented("bed-head", l5, L5.bed_head())
    oriented("bed-foot", l5, L5.bed_foot())
    oriented("nightstand", l5, L5.nightstand())
    oriented("wardrobe", t, wardrobe_b10())  # (B10)
    oriented("wingchair", t, wing_chair_b10())  # (B10)
    oriented("sofa", t, [
        box("Seat", (0, 4, 3), (16, 8, 14), "velvet"),
        box("Back", (0, 8, 12), (16, 17, 15), "velvet"),
        box("Base", (0.5, 0, 3.5), (15.5, 4, 14.5), "wood"),
    ])
    save("pottedpalm", dict(t, palmtrunk="backrooms:block/level5/palmtrunk", soil="backrooms:block/level5/potsoil"),
         palm_b14())  # (B14)
    save("mahjongtable", t, [
        box("Top", (0, 11, 0), (16, 12.5, 16), "felt"),
        box("Rim", (-0.5, 11, -0.5), (16.5, 12, 16.5), "wood", faces=("north", "south", "east", "west", "down")),
        box("Leg", (6, 0, 6), (10, 11, 10), "wood"),
    ] + [box(f"Tiles{i}", (x, 12.5, z), (x + w, 13.5, z + d), "tile") for i, (x, z, w, d) in
         enumerate(((2, 2, 12, 1.5), (2, 12.5, 12, 1.5), (2, 4, 1.5, 8), (12.5, 4, 1.5, 8), (6, 7, 4, 2)))] + [
        # Drinks nobody has touched: a bottle and glasses at the corners
        box("Bottle", (13.5, 12.5, 13.5), (15, 17, 15), "bottle"), box("Neck", (13.9, 17, 13.9), (14.6, 19, 14.6), "bottle"),
        box("Glass1", (0.8, 12.5, 0.8), (2, 14.5, 2), "crystal"), box("Glass2", (14, 12.5, 0.8), (15.2, 14.5, 2), "crystal"),
        box("Glass3", (0.8, 12.5, 14), (2, 14.5, 15.2), "crystal"), box("Ashtray", (7, 12.5, 14.2), (9, 13, 15.6), "crystal")])
    save("turntable", t, [
        box("Base", (2, 0, 2), (14, 10, 14), "wood"),
        box("Platter", (3.5, 10, 3.5), (12.5, 10.6, 12.5), "record"),
        box("Arm", (11, 10.5, 4), (12, 11.5, 11), "brass"),
        box("Horn", (10, 10.5, 10), (15, 17, 15), "brass"),
    ])
    if D4_BOILER:
        oriented("boiler", dict(t, **BOILER_TEX, **BOILER_D4_TEX), boiler_d4())
    else:
        oriented("boiler", dict(t, **BOILER_TEX), boiler())
    oriented("furnace", dict(t, **BOILER_TEX, **BOILER_D4_TEX, l5castiron="backrooms:block/detail/l5castiron"), L5.furnace())  # (Level 5 art)


if __name__ == "__main__":
    parking()
    level3()
    level4()
    level5()
    level2()
    level1()
    print("shapes written")
