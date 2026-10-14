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
        x1 = round(d - a, 3) if left == "w" else 0.0
        x2 = round(16 + a + d, 3) if right == "w" else round(16 - a - d, 3) if right == "j" else 16.0
        # The block's own part, and what reaches past its edges round an outer corner
        for part, p, q in (("L", x1, 0.0), ("", max(x1, 0.0), min(x2, 16.0)), ("R", 16.0, x2)):
            if q - p < 0.01:
                continue
            fs = ["north"] + (["up"] if hi > 0 else []) + (["down"] if lo < 0 else [])
            # Only the end of a turn shows; "o" runs on into the next block's pipe (as the straight blocks) and a
            # blind flange covers "c" (an end face there would fight with the flange's face in the same plane)
            if q == x2 and right == "w":
                fs.append("east")
            b = box(f"{name}{part}{i}", (p, yc + lo * r, zc - d), (q, yc + hi * r, zc + d), tex, faces=tuple(fs))
            u1, u2 = (p + 16, q + 16) if part == "L" else (p - 16, q - 16) if part == "R" else (p, q)
            b["faces"]["north"]["uv"] = [u1, v(hi), u2, v(lo)]
            if "up" in b["faces"]:
                b["faces"]["up"]["uv"] = [u1, 0, u2, 1.2] if hi >= 1 else [u1, v(hi), u2, v(hi) + 0.3]
            if "down" in b["faces"]:
                b["faces"]["down"]["uv"] = [u1, 14.8, u2, 16] if lo <= -1 else [u1, v(lo) - 0.3, u2, v(lo)]
            if "east" in b["faces"]:
                # Round an outer corner the end is the front of the turn: shaded like the next face's pipe
                b["faces"]["east"]["uv"] = [0, v(hi), round(2 * d, 3), v(lo)]
            out.append(b)
    return out


def wall_pipe_cap(name, end):
    """A blind flange on the end of both wall pipes, flush with the block's edge ("left" end x 0, "right" x 16). The
    steel pipe's flange is wider than the pipe stands off the wall, so its back is cut flat a hair in front of the
    wall (else its face at the block's edge shows a sliver in the wall's own face where that shows, beside a door)."""
    out = []
    for nm, (yc, zc, r), grow, tex, t in (("CapA", WALL_PIPE_RUST, 0.7, "flange", 0.8), ("CapB", WALL_PIPE_LAG, 0.35, "metal", 0.6)):
        x1, x2 = (0.0, t) if end == "left" else (16 - t, 16.0)
        for b in round_pipe(f"{name}{nm}", yc, zc, r + grow, tex, x1, x2, shaded=False, faces=("east", "west")):
            b["to"][2] = min(b["to"][2], -0.02)
            out.append(b)
    return out


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
    cap; a conduit in a gland and a rusty pipe run on up into the ceiling."""
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


def machine_cabinet():
    """The free-standing machine cabinet (Levels 2 and 3), front to the north: carcass and cap, a framed front with an
    instrument panel (two gauges, two lamps) over a louvred door with a bar handle, on a toe-recessed plinth; a pipe
    stub out of the top at the back."""
    els = [K.box("Toe", (2.0, 0, 5.25), (14.0, 1.0, 15.5), "cabdark", faces=("north", "east", "west", "south")),
           K.box("Body", (1.0, 1.0, 4.5), (15.0, 14.25, 16), CAB, faces=("north", "east", "west", "south", "down")),
           K.box("Cap", (0.75, 14.25, 4.0), (15.25, 15.0, 16), {"all": "cabpaint", "top": "cabtop"})]
    els += cab_frame("Front", 1.0, 1.0, 15.0, 14.25, 4.0, 4.5, 1.0, grid=(1, 2))[0]
    els += K.dial("DialL", 4.6, 10.7, 4.5, r=1.75, angle=-30, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += K.dial("DialR", 11.4, 10.7, 4.5, r=1.75, angle=40, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += cab_lamp("LampR", 8.0, 11.9, 4.5, "cablampred") + cab_lamp("LampA", 8.0, 9.6, 4.5, "cablampamber")
    els += louvre("Vent", 2.75, 2.5, 9.75, 6.625, 4.5, 3)
    els += K.handle("Handle", 12.0, 4.5, 4.5, length=3.0, axis="y", standoff=0.75, thick=0.75, tex="cabbezel")
    els.append(K.box("Pipe", (11, 15.0, 11), (14, 16, 14), "rust", faces=("north", "east", "west", "south", "up")))
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
    save("machinecabinet", dict(CABINET_TEX, metal="backrooms:block/props/metal", rust=PIPE_TEX["rust"]), machine_cabinet())


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

    for colour in ("red", "blue", "white", "black"):
        textures = {"body": f"backrooms:block/level1/car-{colour}", "glass": "backrooms:block/level1/car-glass",
                    "tyre": "backrooms:block/props/metal-dark", "metal": "backrooms:block/props/metal",
                    "lamp": "backrooms:block/props/tube-white", "tail": "backrooms:block/props/valve"}
        clean = [
            # The body under the beltline (bonnet and boot lid on top), its sides added round the wheel arches
            box("Body", (4, 3, 1), (28, 11, 63), "body"),
            *side(1, 4, 1),
            *side(28, 31, 31),
            *glasshouse(),
            box("BumperFront", (1, 3, 0), (31, 6.5, 1), "metal"),
            box("BumperRear", (1, 3, 63), (31, 6.5, 64), "metal"),
            box("Grille", (10, 6.5, 0.7), (22, 9.5, 1), "tyre"),
            box("LampLeft", (3, 7, 0.6), (8, 9.5, 1), "lamp", glow=60),
            box("LampRight", (24, 7, 0.6), (29, 9.5, 1), "lamp", glow=60),
            box("TailLeft", (3, 7.5, 63), (8, 9.5, 63.4), "tail"),
            box("TailRight", (24, 7.5, 63), (29, 9.5, 63.4), "tail"),
        ]
        save(f"car-{colour}", textures, clean)

    # Level 1's abandoned cars are wrecks of the same car: sat down on flat tyres, the side glass gone (the seats show
    # through), the windscreen crazed round a hole and the rear window out, a headlamp smashed, the bonnet sprung, a
    # hub cap missing, the paint faded and rusting through; the black one burnt out. Same 2x4 footprint
    sag = 1.5

    def wrecked():
        els = []
        for e in json.loads(json.dumps(clean)):
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
        els += [box("SeatFL", (6, floor, 26.5), (14, floor + 2, 31), "seat"), box("SeatFLBack", (6, floor, 31), (14, floor + 7, 32.5), "seat"),
                box("SeatFR", (18, floor, 26.5), (26, floor + 2, 31), "seat"), box("SeatFRBack", (18, floor, 31), (26, floor + 7, 32.5), "seat"),
                box("Bench", (5, floor, 37), (27, floor + 2, 40.5), "seat"), box("BenchBack", (5, floor, 40.5), (27, floor + 6, 42), "seat"),
                box("Wheelhub", (19.5, floor + 3, 23.5), (22.5, floor + 6, 24.5), "tyre"),
                dict(box("Bonnet", (5, floor, 1.5), (27, floor + 0.7, 15), "body"), rotationOrigin=[16, floor, 15], rotationX=-7)]
        return els

    for state, base in (("redwreck", "red"), ("bluewreck", "blue"), ("whitewreck", "white"), ("burnt", "black")):
        textures = {"body": f"backrooms:block/level1/car-{state}", "glass": "backrooms:block/level1/car-glass",
                    "glassbroken": "backrooms:block/level1/car-glass-broken", "seat": "backrooms:block/level1/car-seat"
                    if state != "burnt" else "backrooms:block/level1/car-burnt", "rim": PIPE_TEX["rust"],
                    "tyre": "backrooms:block/props/metal-dark", "metal": "backrooms:block/props/metal",
                    "lamp": "backrooms:block/props/tube-white", "tail": "backrooms:block/props/valve"}
        if state == "burnt":
            textures.update(metal=PIPE_TEX["rust"], lamp="backrooms:block/props/metal-dark", tail="backrooms:block/props/metal-dark")
        save(f"car-{state}", textures, wrecked())


def oriented(name, textures, elements):
    """Props that face a direction are modelled facing north; block variants rotate them."""
    save(name, textures, elements)


def level3():
    cables = {"cable": "backrooms:block/level3/cable", "metal": "backrooms:block/props/metal",
              "tube": "backrooms:block/props/tube-warm", "tubeoff": "backrooms:block/props/tube-off"}

    def cable_x():
        out = []
        for i, (y, z, r) in enumerate(((12.5, 2, 1.5), (13, 5, 1), (12, 8, 2), (13.5, 11.5, 1), (12.5, 13.5, 1.5))):
            out.append(box(f"Cable{i}", (0, y, z), (16, y + r, z + r), "cable", faces=("north", "south", "up", "down")))
        out.append(box("Tray", (0, 11.5, 1), (16, 12, 15.5), "metal", faces=("north", "south", "up", "down")))
        out.append(box("Hanger", (7.5, 12, 0.5), (8.5, 16, 1), "metal"))
        out.append(box("Hanger2", (7.5, 12, 15.5), (8.5, 16, 16), "metal"))
        return out

    save("cables-run", cables, cable_x())
    save("cables-hub", cables, cable_x() + thinner([dict(rot(b, 1), name=b["name"] + "Z") for b in cable_x()]) + [
        box("Box", (4.95, 9, 4.95), (11.05, 16, 11.05), "metal")])  # (a hair wider than the trays' cables meeting it)
    # A tray ending with open hall beyond it (east end): an end plate the cables run into
    save("cables-end", cables, cable_x() + [box("EndPlate", (15.5, 11.5, 0.8), (16, 15, 15.7), "metal")])
    for state, tex in (("lit", "tube"), ("off", "tubeoff")):
        save(f"cablelight-{state}", cables, cable_x() + [
            box("Housing", (2, 9.5, 6.5), (14, 11, 9.5), "metal"),
            box("Tube", (2, 8.8, 7), (14, 9.5, 9), tex, glow=255 if state == "lit" else 0),
            box("Chain1", (4, 11, 7.75), (4.5, 11.5, 8.25), "metal"),
            box("Chain2", (11.5, 11, 7.75), (12, 11.5, 8.25), "metal"),
        ])
        # The same fixture hanging on its chains from the ceiling, with no tray (the middle of a gallery)
        save(f"cablelight-plain-{state}", cables, [
            box("Housing", (2, 9.5, 6.5), (14, 11, 9.5), "metal"),
            box("Tube", (2, 8.8, 7), (14, 9.5, 9), tex, glow=255 if state == "lit" else 0),
            box("Chain1", (4, 11, 7.75), (4.5, 16, 8.25), "metal"),
            box("Chain2", (11.5, 11, 7.75), (12, 16, 8.25), "metal"),
            box("Rose1", (3.5, 15.5, 7.25), (5, 16, 8.75), "metal"),
            box("Rose2", (11, 15.5, 7.25), (12.5, 16, 8.75), "metal"),
        ])

    save("transformer", {"body": "backrooms:block/level3/transformer", "metal": "backrooms:block/props/metal-dark",
                         "insulator": "backrooms:block/level3/insulator"}, [
        box("Tank", (2, 0, 3), (14, 12, 13), "body"),
        box("FinsWest", (0.5, 1, 4), (2, 11, 12), "metal"),
        box("FinsEast", (14, 1, 4), (15.5, 11, 12), "metal"),
        box("Lid", (1.5, 12, 2.5), (14.5, 13, 13.5), "metal"),
        box("Insulator1", (4, 13, 7), (6, 16, 9), "insulator"),
        box("Insulator2", (7, 13, 7), (9, 16, 9), "insulator"),
        box("Insulator3", (10, 13, 7), (12, 16, 9), "insulator"),
    ])

    for material in ("glazed", "brick", "cinder"):
        tex = {"wall": f"backrooms:block/level3/l3wall-{material}", **PIPE_TEX, **WALL_PIPE_TEX,
               "panel": "backrooms:block/level3/panel", "fan": "backrooms:block/level3/fan"}
        save(f"l3wall-{material}-pipes", tex, [CUBE("wall")] + all_sides(WALL_PIPES))
        save(f"l3wall-{material}-pipesjoint", tex, [CUBE("wall")] + all_sides(WALL_PIPES + wall_pipe_joint()))
        save(f"l3wall-{material}-pipesbracket", tex, [CUBE("wall")] + all_sides(WALL_PIPES + wall_pipe_bracket()))
        save(f"l3wall-{material}-panel", tex, [CUBE("wall")] + all_sides([
            box("Panel", (3, 2, -2.5), (13, 14, 0), "panel", faces=("north", "east", "west", "up", "down")),
            box("Conduit", (7, 14, -1.5), (9, 16, 0), "metal", faces=("north", "east", "west")),
        ]))
        save(f"l3wall-{material}-fan", tex, [CUBE("wall")] + all_sides([
            box("Housing", (2, 2, -3), (14, 14, -0.5), "metal", faces=("east", "west", "up", "down")),
            box("Grille", (2.5, 2.5, -3), (13.5, 13.5, -2.5), "fan", faces=("north",)),
            box("Back", (2, 2, -0.5), (14, 14, 0), "metal", faces=("north",)),
            box("Hub", (7, 7, -2.5), (9, 9, -1), "metal"),
            box("BladeV", (7.5, 3.5, -2), (8.5, 12.5, -1.5), "metal"),
            box("BladeH", (3.5, 7.5, -2), (12.5, 8.5, -1.5), "metal"),
        ]))

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


def level4():
    t = {"wood": "backrooms:block/level4/laminate", "metal": "backrooms:block/props/metal",
         "plastic": "backrooms:block/level4/crt", "screen": "backrooms:block/level4/crt-screen",
         "fabric": "backrooms:block/level4/chairfabric", "dark": "backrooms:block/props/metal-dark",
         "partition": "backrooms:block/level4/partition", "filing": "backrooms:block/level4/filing",
         "vending": "backrooms:block/level4/vending", "cooler": "backrooms:block/level4/cooler",
         "water": "backrooms:block/level4/coolerbottle"}
    # Cubicle partition running west-east, about 1.5 m tall, fabric under a 1 px aluminium top rail
    save("partition", t, [box("Panel", (0, 0, 6.5), (16, 23, 9.5), "partition"),
                          box("Rail", (0, 23, 6.2), (16, 24, 9.8), "metal")])
    oriented("desk", t, [
        box("Top", (0, 11.5, 2), (16, 12.5, 14), "wood"),
        box("LegL", (1, 0, 3), (2, 11.5, 13), "wood"),
        box("LegR", (14, 0, 3), (15, 11.5, 13), "wood"),
        box("Modesty", (2, 4, 12), (14, 11.5, 13), "wood"),
        box("Crt", (4, 12.5, 6), (12, 19.5, 13), "plastic"),
        box("Screen", (5, 13.5, 5.6), (11, 18.5, 6), "screen", glow=30, faces=("north",)),
        box("Keyboard", (4, 12.5, 2.5), (12, 13, 5), "plastic"),
    ])
    oriented("officechair", t, [
        box("Seat", (3, 6, 3), (13, 8, 13), "fabric"),
        box("Back", (3.5, 8, 11), (12.5, 17, 13), "fabric"),
        box("Post", (7, 2, 7), (9, 6, 9), "dark"),
        box("BaseX", (2, 0.5, 7.5), (14, 1.5, 8.5), "dark"),
        box("BaseZ", (7.5, 0.5, 2), (8.5, 1.5, 14), "dark"),
    ])
    oriented("filingcabinet", t, [
        box("Body", (2, 0, 2), (14, 16, 14), "filing"),
        box("Handle1", (6, 12, 1.5), (10, 12.8, 2), "metal"),
        box("Handle2", (6, 7, 1.5), (10, 7.8, 2), "metal"),
        box("Handle3", (6, 2, 1.5), (10, 2.8, 2), "metal"),
    ])
    oriented("vendingmachine", t, [
        box("Body", (0.5, 0, 2), (15.5, 28, 15), "vending"),
        box("Glow", (2, 9, 1.8), (11, 26, 2), "water", glow=90, faces=("north",)),
    ])
    oriented("watercooler", t, [
        box("Body", (4, 0, 4), (12, 14, 12), "cooler"),
        box("Bottle", (5, 14, 5), (11, 22, 11), "water"),
        box("Tap", (7, 9, 3), (9, 10.5, 4), "dark"),
    ])
    save("conferencetable", t, [
        box("Top", (0, 11, 0), (16, 12.5, 16), "wood"),
        box("Leg", (6, 0, 6), (10, 11, 10), "dark"),
    ])


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

    save("hotelfixture-sconce", t, [CUBE("panel")] + all_sides([
        box("Plate", (6.5, 4, -0.5), (9.5, 10, 0), "brass", faces=("north", "east", "west", "up", "down")),
        box("Arm", (7.5, 7, -3), (8.5, 8, -0.5), "brass"),
        box("Cup", (6.5, 8, -4), (9.5, 9, -2), "brass"),
        box("Candle", (7.25, 9, -3.25), (8.75, 12, -2.75), "candle", glow=180),
    ]))
    save("hotelfixture-portrait", t, [CUBE("panel")] + all_sides([
        box("Frame", (2, 2, -1), (14, 15, 0), "gilt", faces=("east", "west", "up", "down")),
        box("Canvas", (3, 3, -1), (13, 14, -0.8), "portrait", faces=("north",)),
        box("FrameFront", (2, 2, -1.1), (14, 15, -1), "gilt", faces=("north",)),
    ]))
    # Portrait canvas sits behind the frame front: draw the frame as four strips instead
    portrait = [CUBE("panel")] + all_sides([
        box("Canvas", (3, 3, -0.8), (13, 14, -0.5), "portrait", faces=("north",)),
        box("FrameTop", (2, 14, -1.2), (14, 15, 0), "gilt"),
        box("FrameBottom", (2, 2, -1.2), (14, 3, 0), "gilt"),
        box("FrameLeft", (2, 3, -1.2), (3, 14, 0), "gilt"),
        box("FrameRight", (13, 3, -1.2), (14, 14, 0), "gilt"),
    ])
    save("hotelfixture-portrait", t, portrait)
    save("hotelfixture-beverly", t, [CUBE("panel")] + all_sides([
        box("Placard", (2, 5, -0.6), (14, 11, 0), "placard", faces=("north", "east", "west", "up", "down")),
    ]))

    for state, glow in (("lit", 200), ("off", 0)):
        save(f"domelight-{state}", t, [CUBE("cream"),
            box("Base", (5, -0.5, 5), (11, 0, 11), "brass"),
            box("Dome", (5.5, -3, 5.5), (10.5, -0.5, 10.5), "glass", glow=glow)])

    # The grand rooms' coffered ceiling: cream slabs, and every fourth row and column a mahogany beam hanging 4 px
    # under them with a moulded bead along its foot. Only the faces that can be seen are drawn; the blocks let light
    # through, so the beams' sides are lit by the room rather than by the dark slab beside them.
    slab = box("Slab", (0, 0, 0), (16, 16, 16), "cream", faces=("down",))

    def beam_x(x1=0, x2=16):
        return [box("Beam", (x1, -4, 5.5), (x2, 0, 10.5), "wood", faces=("north", "south", "down")),
                box("Bead", (x1, -4.6, 6.5), (x2, -4, 9.5), "wood", faces=("north", "south", "down"))]

    save("hotelceiling-coffer", t, [slab])
    save("hotelceiling-beam", t, [slab] + beam_x())
    # Where two beams cross, the one along Z stops at the sides of the one along X
    save("hotelceiling-beamcross", t, [slab] + beam_x() + [
        dict(rot(b, 1), name=b["name"] + "Z" + str(i)) for i, (x1, x2) in enumerate(((0, 5.5), (10.5, 16))) for b in beam_x(x1, x2)])

    # A great chandelier hanging from the grand ceilings (drawn larger than its block)
    chandelier = [box("Chain", (7.5, 8, 7.5), (8.5, 16, 8.5), "brass"),
                  box("Hub", (6, 4, 6), (10, 8, 10), "brass"),
                  box("Ring", (-4, 5, -4), (20, 6, 20), "brass", faces=("up", "down", "north", "south", "east", "west"))]
    for i, (x, z) in enumerate(((-3, -3), (8, -4), (19, -3), (-4, 8), (20, 8), (-3, 19), (8, 20), (19, 19))):
        chandelier.append(box(f"Candle{i}", (x - 0.75, 6, z - 0.75), (x + 0.75, 8.5, z + 0.75), "candle", glow=220))
    for i, (x, z) in enumerate(((2, 2), (14, 2), (2, 14), (14, 14))):
        chandelier.append(box(f"Crystal{i}", (x - 1, 0, z - 1), (x + 1, 4, z + 1), "crystal", glow=120))
    save("chandelier", t, chandelier)

    # A front hall's grand staircase (layout 5), climbing toward the north like the concrete stairs: white marble
    # steps, and on the middle one of a flight a red runner over treads and risers, held by brass stair rods
    stairs = {"marble": "backrooms:block/detail/marble", "carpet": "backrooms:block/level5/hotelcarpet-damask",
              "brass": "backrooms:block/level5/brass"}
    steps = [box("Lower", (0, 0, 0), (16, 8, 16), "marble"), box("Upper", (0, 8, 0), (16, 16, 8), "marble")]
    save("hotelstairs-marble", stairs, steps)
    save("hotelstairs-runner", stairs, steps + [
        box("TreadLower", (2, 8, 8.4), (14, 8.4, 16), "carpet", faces=("up", "east", "west")),
        box("RiserLower", (2, 0, 16), (14, 8.4, 16.4), "carpet", faces=("south", "up", "east", "west")),
        box("RiserUpper", (2, 8, 8), (14, 16.4, 8.4), "carpet", faces=("south", "up", "east", "west")),
        box("TreadUpper", (2, 16, 0), (14, 16.4, 8), "carpet", faces=("up", "east", "west")),
        box("RodUpper", (1.5, 8.4, 8.4), (14.5, 9, 9), "brass"),
        box("RodLower", (1.5, 0, 16.4), (14.5, 0.6, 17), "brass"),
    ])

    oriented("bed-head", t, [
        box("Frame", (1, 2, 0), (15, 6, 16), "wood"),
        box("Mattress", (1.5, 6, 0.5), (14.5, 9, 16), "linen"),
        box("Pillow", (3, 9, 1.5), (13, 10.5, 5), "linen"),
        box("Headboard", (0.5, 0, -0.5), (15.5, 16, 1), "wood"),
        box("Blanket", (1.3, 6.5, 6), (14.7, 9.3, 16), "blanket"),
    ])
    oriented("bed-foot", t, [
        box("Frame", (1, 2, 0), (15, 6, 15), "wood"),
        box("Mattress", (1.5, 6, 0), (14.5, 9, 14.5), "linen"),
        box("Blanket", (1.3, 6.5, 0), (14.7, 9.3, 14.7), "blanket"),
        box("Footboard", (0.5, 0, 14.5), (15.5, 11, 16), "wood"),
    ])
    oriented("nightstand", t, [
        box("Body", (2, 0, 4), (14, 10, 14), "wood"),
        box("LampBase", (6.5, 10, 7.5), (9.5, 11, 10.5), "brass"),
        box("LampStem", (7.5, 11, 8.5), (8.5, 15, 9.5), "brass"),
        box("Shade", (5, 14, 6.5), (11, 19, 12.5), "lampshade", glow=90),
    ])
    oriented("wardrobe", t, [
        box("Body", (1, 0, 5), (15, 30, 16), "wood"),
        box("Seam", (7.8, 2, 4.8), (8.2, 28, 5), "brass"),
        box("Handle1", (6.5, 14, 4.5), (7.5, 17, 5), "brass"),
        box("Handle2", (8.5, 14, 4.5), (9.5, 17, 5), "brass"),
    ])
    oriented("wingchair", t, [
        box("Seat", (2, 4, 2), (14, 8, 14), "velvet"),
        box("Back", (2, 8, 12), (14, 22, 15), "velvet"),
        box("WingL", (1, 8, 6), (3, 18, 15), "velvet"),
        box("WingR", (13, 8, 6), (15, 18, 15), "velvet"),
        box("Legs", (3, 0, 3), (13, 4, 13), "wood"),
    ])
    oriented("sofa", t, [
        box("Seat", (0, 4, 3), (16, 8, 14), "velvet"),
        box("Back", (0, 8, 12), (16, 17, 15), "velvet"),
        box("Base", (0.5, 0, 3.5), (15.5, 4, 14.5), "wood"),
    ])
    palm = [box("Pot", (4, 0, 4), (12, 8, 12), "pot"), box("Trunk", (7, 8, 7), (9, 20, 9), "wood")]
    for i, (dx, dz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        palm.append(box(f"Frond{i}", (8 + min(0, dx * 9) if dx else 6, 18, 8 + min(0, dz * 9) if dz else 6),
                        (8 + max(0, dx * 9) if dx else 10, 19, 8 + max(0, dz * 9) if dz else 10), "leaf"))
    save("pottedpalm", t, palm)
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
    oriented("boiler", t, [
        box("Body", (1, 0, 2), (15, 26, 15), "boiler"),
        box("Hatch", (5, 6, 1.5), (11, 12, 2), "iron"),
        box("Gauge", (6.5, 17, 1.5), (9.5, 20, 2), "iron"),
        box("Flue", (6, 26, 7), (10, 32, 11), "rust"),
    ])
    oriented("furnace", t, [
        box("Body", (1, 0, 2), (15, 14, 15), "iron"),
        box("Door", (4, 2, 1.6), (12, 9, 2), "fire", glow=200, faces=("north",)),
        box("Hood", (0, 14, 1), (16, 16, 16), "iron"),
    ])


if __name__ == "__main__":
    parking()
    level3()
    level4()
    level5()
    level2()
    level1()
    print("shapes written")
