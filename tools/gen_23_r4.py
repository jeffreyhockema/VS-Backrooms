"""Level 23, "The Petrified Garden": round 4's blocks (2026-11-02, the asset-quality pass), called from tools/gen_23.py.

The trunks stay voxel (a trunk is 4-14 wide and 48 high); round 4 dresses their skin with model blocks:
- `l23-barkface-<bark>-<side>`: the outermost bark near eye height as relief (fissures and ridges, plates broken across,
  stringy redwood, smooth aspen with its eyes, moss cushions), facing out; full collision, the trunk's own block.
- `l23-flare-<kind>-<shape>-<side>`: the air at a trunk's foot, a concave slope of mossy bark from the trunk down into
  the ground (a root flare), or a lower slope with a root running out.
- `l23-limb-<bark>-<kind>-<side>`: a broken petrified limb or stub out of a trunk's side, tilted up (rotated elements).
- `l23-logpart-<bark>-<part>-<axis>`: a fallen log's cell as a slice of its round section (one, two or three blocks
  across), the rings on its ends, moss along its top.
- `l23-caprim-<part>-<side>`: a stone mushroom cap's rim (a drooping lip, gills under) and its upper layer's sloped edge.
- `l23-boulderpart-<part>-<side>`: a boulder's rounded top and edges.

Oriented models face NORTH (their front at low z; what they grow from on their south side) and have the variant group
"side" last: -east is rotateY 270, -south 180, -west 90, as round 3's (tools/gen_23_r3.py).
"""
import math
import os
import random

from PIL import Image, ImageDraw

import matlib as M
import gen_23 as G

S = G.S
SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
WOOD = G.WOOD
STONE = ("game:walk/stone*", "game:block/rock-hit-pickaxe")
TEXDIR = os.path.join(G.TEX, "block", "23")


# ---------------- Model helpers ----------------

def _span(a, b):
    """A uv span inside 0..16 for a box edge from a to b (shifted in; longer than a block, the whole texture)."""
    lo, hi = min(a, b), max(a, b)
    if hi - lo >= 16:
        return 0, 16
    if lo < 0:
        return 0, hi - lo
    if hi > 16:
        return 16 - (hi - lo), 16
    return lo, hi


def uv_of(side, frm, to):
    x1, y1, z1 = frm
    x2, y2, z2 = to
    if side in ("north", "south"):
        u1, u2 = _span(x1, x2)
        v1, v2 = _span(16 - y2, 16 - y1)
    elif side in ("east", "west"):
        u1, u2 = _span(z1, z2)
        v1, v2 = _span(16 - y2, 16 - y1)
    else:
        u1, u2 = _span(x1, x2)
        v1, v2 = _span(z1, z2)
    return [round(u1, 3), round(v1, 3), round(u2, 3), round(v2, 3)]


def E(name, frm, to, faces, rot=None, glow=0):
    """An element: faces maps a side (north..down) to a texture key, or to (key, rotation)."""
    frm = [round(v, 3) for v in frm]
    to = [round(v, 3) for v in to]
    fs = {}
    for side, spec in faces.items():
        tex, r = (spec, 0) if isinstance(spec, str) else spec
        f = {"texture": tex, "uv": uv_of(side, frm, to)}
        if r:
            f["rotation"] = r
        if glow:
            f["glow"] = glow
        fs[side] = f
    e = {"name": name, "from": frm, "to": to, "faces": fs}
    if rot:
        e.update(rot)
    return e


ALL = ("north", "east", "south", "west", "up", "down")


def every(tex, skip=()):
    return {s: tex for s in ALL if s not in skip}


def shape(textures, elements):
    return {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": elements}


# ---------------- Textures ----------------

def load(name):
    return Image.open(os.path.join(TEXDIR, name + ".png")).convert("RGBA")


def deep(img, amount=-46, seed=0):
    """A bark's fissure walls and floors: the same bark, darker and greyer, with a little damp."""
    out = img.copy()
    px = out.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            c = px[x, y][:3]
            g = sum(c) / 3
            c = tuple(int(0.8 * v + 0.2 * g) for v in c)
            px[x, y] = M.rgba(M.lift(c, amount + rng.uniform(-5, 5)))
    return out


def opaque(img):
    """Every texel fully opaque (round 4 rule: no translucent texels in the opaque pass)."""
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= 128 else 0)
    return img


def moss_cushion(seed):
    """Moss as a cushion: bright tips, dark hollows, a few spore stalks."""
    img = M.noise_hv((66, 96, 40), 6, seed, mottle=9, hue=3)
    px = img.load()
    rng = random.Random(seed + 1)
    for _ in range(90):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((22, 30, -26))))
    for _ in range(10):
        x, y = rng.randrange(S), rng.randrange(1, S)
        px[x, y] = M.rgba((150, 140, 60))
        px[x, y - 1] = M.rgba((122, 112, 52))
    return img


# ---------------- Bark relief (the trunks' skin) ----------------

CORE = 3.5  # the fissures' floor (z); ridges come out to 0


def ridges_of(profile):
    """The ridges of a relief profile as (x1, x2, depth, [breaks]) with depth how far proud of the floor (to CORE)."""
    if profile == "furrow":  # grey: broad ridges interlacing, plates broken across now and then
        return [(0, 2.5, 3.0, [11]), (4, 7.5, 3.5, [5]), (9, 11, 2.5, []), (12.5, 16, 3.2, [9])]
    if profile == "fibre":  # redwood: many narrow soft ridges, shallow fissures, no plates
        return [(0, 1.5, 2.5, []), (2.5, 4.5, 3.0, []), (5.5, 6.5, 2.0, []), (7.5, 10, 3.2, []), (11, 12.5, 2.2, []), (13.5, 16, 2.8, [])]
    if profile == "plate":  # oak: blocky plates, broken across into short tiles
        return [(0, 3.5, 3.0, [4, 10]), (5, 9.5, 3.4, [7, 13]), (11, 16, 2.8, [3, 10])]
    if profile == "string":  # cypress: stringy strips, narrow and close, deep slots
        return [(0, 1.2, 3.2, []), (2, 3.6, 2.6, [8]), (4.6, 5.6, 3.4, []), (6.6, 8.8, 2.4, []), (9.8, 11, 3.0, [12]), (12, 13.4, 2.6, []),
                (14.4, 16, 3.2, [])]
    if profile == "smooth":  # aspen: smooth, faint ridges, a black eye
        return [(0, 16, 1.0, [6.5])]
    if profile == "giant":  # the Green Giants: deep wide furrows
        return [(0, 4.5, 3.5, [12]), (6.5, 10, 3.5, [4]), (12, 16, 3.5, [])]
    raise ValueError(profile)


def barkface_shape(profile, bark, flip=False):
    """A cell of a trunk's outer bark, facing north: the floor of the fissures at z=CORE, the ridges standing out to z=0.
    With flip, the ridges' breaks are mirrored top to bottom (a second pattern that still meets the cells above and below)."""
    els = [E("Core", (0, 0, CORE), (16, 16, 16), {"north": "#deep", "east": "#bark", "west": "#bark", "south": "#bark", "up": "#bark", "down": "#bark"})]
    for k, (x1, x2, d, breaks) in enumerate(ridges_of(profile)):
        cuts = sorted(16 - b if flip else b for b in breaks)
        y = 0
        for n, c in enumerate(cuts + [16]):
            y2 = c - 0.6 if c < 16 else 16
            if y2 - y > 0.5:
                dd = d - (0.6 if (n + k) % 2 else 0)
                els.append(E(f"Ridge{k}_{n}", (x1, y, CORE - dd), (x2, y2, CORE),
                             {"north": "#bark", "east": "#deep", "west": "#deep", "up": "#deep", "down": "#deep"}))
                # A plate's top edge chipped back (the light catches it)
                if c < 16 and profile in ("plate", "furrow", "giant"):
                    els.append(E(f"Lip{k}_{n}", (x1 + 0.4, y2 - 0.8, CORE - dd - 0.4), (x2 - 0.4, y2, CORE - dd),
                                 {"north": "#bark", "up": "#bark", "east": "#deep", "west": "#deep"}))
            y = c
    if profile == "smooth":  # the aspen's eye: a dark scar with a lip round it
        els += [E("EyeLip", (5, 9, -0.6), (11, 12.5, 2.5), {"north": "#bark", "up": "#bark", "down": "#bark", "east": "#bark", "west": "#bark"}),
                E("Eye", (6.2, 9.6, -0.9), (9.8, 11.9, -0.6), {"north": "#eye"})]
    if bark == "moss":  # cushions of moss over the ridges' feet
        for k, (x, y, w, h) in enumerate([(1, 0, 6, 4), (8, 0, 7, 6), (4, 3, 5, 3)]):
            els.append(E(f"Moss{k}", (x, y, -0.8), (x + w, y + h, CORE), {"north": "#moss", "up": "#moss", "east": "#moss", "west": "#moss"}))
    return els


BARK_PROFILES = {"grey": "furrow", "red": "fibre", "pale": "plate", "dark": "string", "green": "giant", "aspen": "smooth", "moss": "furrow"}
FACE_BARKS = list(BARK_PROFILES)


def bark_textures(bark):
    t = {"bark": f"backrooms:block/23/{'mossbark' if bark == 'moss' else 'bark-' + bark}",
         "deep": f"backrooms:block/23/barkdeep-{bark}"}
    if bark == "aspen":
        t["eye"] = "backrooms:block/23/aspen-eye"
    if bark == "moss":
        t["moss"] = "backrooms:block/23/moss-cushion"
    return t


# ---------------- Root flares ----------------

def flare_shape(kind, form):
    """The air at a trunk's foot (the trunk on the south side): a concave slope of bark from the trunk's face down to the
    ground, its top mossed. "root": the slope lower, a root running out along the middle to the cell's far edge."""
    top, side = "#top", "#side"
    els = []
    scale = 1.0 if form == "full" else 0.55
    for k in range(8):
        z1, z2 = 2 * k, 2 * k + 2
        h = 16 * scale * ((z2 - 0.5) / 16) ** 1.9
        if h < 0.4:
            continue
        els.append(E(f"Slope{k}", (0, 0, z1), (16, h, z2), {"north": side, "up": top, "east": side, "west": side}))
    if form == "root":
        prof = [(0, 3, 2.2), (3, 6, 3.2), (6, 10, 4.4), (10, 13, 6), (13, 16, 8)]
        for k, (z1, z2, h) in enumerate(prof):
            w = 2.6 + k * 0.35
            els.append(E(f"Root{k}", (8 - w, 0, z1), (8 + w, h, z2), {"north": side, "up": top, "east": side, "west": side}))
        els.append(E("RootTip", (6.2, 0, -1.5), (9.8, 1.6, 0.5), {"north": side, "up": top, "east": side, "west": side}))
    return els


FLARE_KINDS = {"moss": ("backrooms:block/23/moss", "backrooms:block/23/mossbark"),
               "green": ("backrooms:block/23/moss-2", "backrooms:block/23/bark-green")}


# ---------------- Limbs ----------------

def limb_shape(kind):
    """A broken limb out of the trunk's face (on the south side), tilted up toward the north: an octagonal section, a collar
    of bark where it leaves the trunk, the broken end showing rings. "stub": short and thick; "limb": long, a fork."""
    sideb = ("#bark", 90)
    long_faces = {"east": sideb, "west": sideb, "up": "#bark", "down": "#bark", "north": "#ring"}
    els = [E("Collar", (3.5, 3.5, 13.5), (12.5, 12.5, 16), {"north": "#bark", "east": "#bark", "west": "#bark", "up": "#bark", "down": "#bark"}),
           E("CollarX", (2.5, 5, 14.5), (13.5, 11, 16), {"north": "#bark", "east": "#bark", "west": "#bark", "up": "#bark", "down": "#bark"})]
    if kind == "stub":
        length, r, tilt = 13, 3.4, 22
    else:
        length, r, tilt = 26, 2.6, 34
    z0 = 16 - length
    rot = {"rotationOrigin": [8, 8, 16], "rotationX": tilt}
    q = r * 0.42
    els += [E("LimbA", (8 - r, 8 - q, z0), (8 + r, 8 + q, 16), long_faces, rot),
            E("LimbB", (8 - q, 8 - r, z0), (8 + q, 8 + r, 16), long_faces, rot),
            E("LimbC", (8 - r * 0.72, 8 - r * 0.72, z0 + 0.3), (8 + r * 0.72, 8 + r * 0.72, 16), long_faces, rot)]
    # The broken end: jagged splinters
    els += [E("Jag1", (8 - r * 0.6, 8, z0 - 2.2), (8, 8 + r * 0.7, z0), long_faces, rot),
            E("Jag2", (8 + 0.4, 8 - r * 0.6, z0 - 1.2), (8 + r * 0.6, 8 + 0.6, z0), long_faces, rot)]
    if kind == "limb":
        # A fork halfway out, up and to one side
        fork = {"rotationOrigin": [8, 8, 16 - length * 0.45], "rotationX": tilt + 22, "rotationY": 28}
        fz = 16 - length * 0.45
        els += [E("ForkA", (8 - 1.4, 8 - 0.6, fz - 11), (8 + 1.4, 8 + 0.6, fz), long_faces, fork),
                E("ForkB", (8 - 0.6, 8 - 1.4, fz - 11), (8 + 0.6, 8 + 1.4, fz), long_faces, fork)]
    return els


LIMB_BARKS = ["grey", "red", "pale", "dark", "aspen"]


# ---------------- Fallen logs: slices of a round section ----------------

def section(cc, cy, R, slabs=8):
    """The slabs of a disc (centre cc, cy; radius R, cell units) inside one cell: (y1, y2, c1, c2, above_centre)."""
    out = []
    h = 16 / slabs
    for k in range(slabs):
        y1, y2 = k * h, (k + 1) * h
        ym = (y1 + y2) / 2
        dy = ym - cy
        if abs(dy) >= R:
            continue
        w = math.sqrt(R * R - dy * dy)
        c1, c2 = max(0, cc - w), min(16, cc + w)
        if c2 - c1 < 0.3:
            continue
        out.append((y1, y2, c1, c2, ym > cy))
    return out


# The pieces of a log's cross-section: (size, offset across, level up from its line's ground) -> (centre c, centre y, R)
LOG_PARTS = {
    "s1": (1, 0, 1, 8, 8, 8),
    "s2a": (2, 0, 1, 16, 16, 16), "s2b": (2, 1, 1, 0, 16, 16), "s2c": (2, 0, 2, 16, 0, 16), "s2d": (2, 1, 2, 0, 0, 16),
    "s3a": (3, -1, 1, 24, 24, 24), "s3b": (3, 1, 1, -8, 24, 24), "s3c": (3, -1, 2, 24, 8, 24), "s3d": (3, 1, 2, -8, 8, 24),
    "s3e": (3, 0, 3, 8, -8, 24), "s3f": (3, 0, 1, 8, 24, 24),
}


def is_full(slabs):
    return len(slabs) == 8 and all(c1 <= 0.01 and c2 >= 15.99 for (_, _, c1, c2, _) in slabs)


def logpart_shape(part, axis):
    _, _, _, cc, cy, R = LOG_PARTS[part]
    els = []
    for k, (y1, y2, c1, c2, upper) in enumerate(section(cc, cy, R)):
        if axis == "x":
            frm, to = (0, y1, c1), (16, y2, c2)
            faces = {"north": ("#bark", 90), "south": ("#bark", 90), "up": ("#moss" if upper else "#bark", 90),
                     "down": ("#bark", 90), "east": "#ring", "west": "#ring"}
        else:
            frm, to = (c1, y1, 0), (c2, y2, 16)
            faces = {"east": ("#bark", 90), "west": ("#bark", 90), "up": "#moss" if upper else "#bark", "down": "#bark",
                     "north": "#ring", "south": "#ring"}
        els.append(E(f"Slab{k}", frm, to, faces))
    return els


# ---------------- Stone mushroom caps and boulders ----------------

RIM = [(0, 4, 2.0, 8.5), (4, 8, 2.8, 11.5), (8, 12, 3.4, 14), (12, 16, 3.8, 16)]  # z1, z2, bottom, top (outward north)


def caprim_shape(part):
    """A stone mushroom cap's edge cell (outward north / north-east): "side" a drooping lip; "corner" the same, rounded in
    plan; "upper"/"uppercorner" the cap's upper layer, sloping down to its edge."""
    els = []
    faces = {"north": "#side", "east": "#side", "west": "#side", "up": "#top", "down": "#gills"}
    if part == "side":
        for k, (z1, z2, b, t) in enumerate(RIM):
            els.append(E(f"Rim{k}", (0, b, z1), (16, t, z2), faces))
        els.append(E("Under", (0, 0, 12), (16, 3.8, 16), {"north": "#gills", "east": "#gills", "west": "#gills", "down": "#gills"}))
    elif part == "corner":
        for i in range(4):
            for k in range(4):
                x1, x2, z1, z2 = i * 4, i * 4 + 4, k * 4, k * 4 + 4
                r = math.hypot((x1 + x2) / 2, 16 - (z1 + z2) / 2)
                if r > 16.5:
                    continue
                n = min(3, max(0, int((16 - r) / 4 + 0.5)))
                _, _, b, t = RIM[n]
                els.append(E(f"Rim{i}{k}", (x1, b, z1), (x2, t, z2), faces))
    elif part == "upper":
        for k, h in enumerate((3.5, 7.5, 11.5, 15)):
            els.append(E(f"Dome{k}", (0, 0, 4 * k), (16, h, 4 * k + 4), {"north": "#side", "east": "#side", "west": "#side", "up": "#top"}))
    else:  # uppercorner
        for i in range(4):
            for k in range(4):
                x1, x2, z1, z2 = i * 4, i * 4 + 4, k * 4, k * 4 + 4
                r = math.hypot((x1 + x2) / 2, 16 - (z1 + z2) / 2)
                if r > 16.5:
                    continue
                h = (3.5, 7.5, 11.5, 15)[min(3, max(0, int((16 - r) / 4 + 0.5)))]
                els.append(E(f"Dome{i}{k}", (x1, 0, z1), (x2, h, z2), {"north": "#side", "east": "#side", "west": "#side", "up": "#top"}))
    return els


def boulder_shape(part):
    """A boulder's top cell: "cap" bevelled round its top on every side; "edge" (outward north) rounding down to the ground;
    "corner" (outward north-east) rounded in plan as well."""
    stone, moss = "#stone", "#moss"
    els = []
    if part == "cap":
        els += [E("Body", (0, 0, 0), (16, 9, 16), {"north": stone, "east": stone, "west": stone, "south": stone, "up": moss, "down": stone}),
                E("Mid", (1.5, 9, 1.5), (14.5, 12.5, 14.5), {"north": stone, "east": stone, "west": stone, "south": stone, "up": moss}),
                E("Top", (4, 12.5, 3), (12.5, 14.5, 13), {"north": stone, "east": stone, "west": stone, "south": stone, "up": moss}),
                E("Lump", (2, 9, 9), (7, 13.5, 14), {"north": stone, "east": stone, "west": stone, "south": stone, "up": moss},
                  {"rotationOrigin": [4.5, 9, 11.5], "rotationY": 25})]
    elif part == "edge":
        for k, (z1, z2, h) in enumerate([(0, 3, 4.5), (3, 6, 8.5), (6, 10, 11.5), (10, 16, 13.5)]):
            els.append(E(f"Step{k}", (0, 0, z1), (16, h, z2), {"north": stone, "east": stone, "west": stone, "up": moss if k >= 2 else stone}))
        els.append(E("Chunk", (3, 0, -0.8), (9, 3.5, 3), {"north": stone, "east": stone, "west": stone, "up": stone},
                     {"rotationOrigin": [6, 0, 1], "rotationY": -18}))
    else:  # corner
        for i in range(4):
            for k in range(4):
                x1, x2, z1, z2 = i * 4, i * 4 + 4, k * 4, k * 4 + 4
                r = math.hypot((x1 + x2) / 2, 16 - (z1 + z2) / 2)
                if r > 17:
                    continue
                h = (4.5, 8.5, 11.5, 13.5)[min(3, max(0, int((17 - r) / 4.25)))]
                els.append(E(f"Step{i}{k}", (x1, 0, z1), (x2, h, z2), {"north": stone, "east": stone, "west": stone, "south": stone,
                                                                         "up": moss if h > 10 else stone}))
    return els


# ---------------- Blocktypes ----------------

def sided(code, comment, groups, shape_of, tex_of, material, sounds, drops=(), collision="full", selection=None, extra=None):
    """A json-model block with variant groups (name, states) and "side" last; shape_of(states) gives a shape path,
    tex_of(states) its textures (or None)."""
    import itertools
    shape_by, tex_by = {}, {}
    names = [g[0] for g in groups]
    for states in itertools.product(*[g[1] for g in groups]):
        key = "*-" + "-".join(states)
        for side in SIDES:
            shape_by[f"{key}-{side}"] = {"base": f"block/23/{shape_of(dict(zip(names, states)))}", "rotateY": ROT[side]}
        t = tex_of(dict(zip(names, states)))
        if t:
            tex_by[f"{key}-*"] = {k: {"base": v.replace("backrooms:", "")} for k, v in t.items()}
    first = "*-" + "-".join(g[1][0] for g in groups) + "-north"
    b = {"code": code, "variantgroups": [{"code": n, "states": s} for n, s in groups] + [{"code": "side", "states": SIDES}],
         "creativeinventory": {"general": [first], "backrooms": [first]},
         "blockmaterial": material, "drawtype": "json", "shapeByType": shape_by,
         "sidesolid": {"all": False}, "sideopaque": {"all": False}, "resistance": 4, "drops": list(drops), "sounds": sounds}
    if tex_by:
        b["texturesByType"] = tex_by
    if collision != "full":
        if collision is None:
            b["collisionbox"] = None
        else:
            b["collisionboxByType"] = {f"*-{s}": dict(collision, rotateY=ROT[s]) for s in SIDES}
    if selection:
        b["selectionboxByType"] = {f"*-{s}": dict(selection, rotateY=ROT[s]) for s in SIDES}
    if extra:
        b.update(extra)
    return comment, b


WOOD_SOUNDS = {"walk": "game:walk/stone*", "place": WOOD[1], "break": "game:block/rock-hit-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
STONE_SOUNDS = {"walk": STONE[0], "place": STONE[1], "break": STONE[1], "hit": STONE[1]}


def blocks():
    out = []
    out.append(sided("l23-barkface", "// Level 23 (round 4): a trunk's outer bark near eye height in relief (fissures, ridges, plates), facing out; the trunk's own block",
                     [("bark", FACE_BARKS), ("pattern", ["a", "b"])],
                     lambda s: f"barkface-{BARK_PROFILES[s['bark']]}{'-moss' if s['bark'] == 'moss' else ''}-{s['pattern']}",
                     lambda s: bark_textures(s["bark"]), "Wood", WOOD_SOUNDS, drops=[G.drop("game:firewood", 0.6, 0.4)],
                     extra={"lightAbsorption": 99, "resistance": 7}))
    out.append(sided("l23-flare", "// Level 23 (round 4): a root flare at a trunk's foot (the trunk on its back), its slope mossed; a step",
                     [("kind", list(FLARE_KINDS)), ("form", ["full", "root"])],
                     lambda s: f"flare-{s['form']}", lambda s: {"top": FLARE_KINDS[s["kind"]][0], "side": FLARE_KINDS[s["kind"]][1]},
                     "Wood", WOOD_SOUNDS, drops=[G.drop("game:firewood", 0.3, 0.3)],
                     collision={"x1": 0, "y1": 0, "z1": 0.35, "x2": 1, "y2": 0.5, "z2": 1},
                     selection={"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.6, "z2": 1}, extra={"lightAbsorption": 0, "resistance": 7}))
    out.append(sided("l23-limb", "// Level 23 (round 4): a broken petrified limb out of a trunk's side (the trunk on its back)",
                     [("bark", LIMB_BARKS), ("kind", ["stub", "limb"])],
                     lambda s: f"limb-{s['kind']}",
                     lambda s: {"bark": f"backrooms:block/23/bark-{s['bark']}", "ring": f"backrooms:block/23/heartwood-{s['bark']}"},
                     "Wood", WOOD_SOUNDS, drops=[G.drop("game:firewood", 0.5, 0.3)], collision=None,
                     selection={"x1": 0.2, "y1": 0.2, "z1": 0.1, "x2": 0.8, "y2": 0.9, "z2": 1}, extra={"lightAbsorption": 0, "resistance": 7}))
    # Fallen logs' pieces: no side; bark x part x axis
    shape_by, tex_by = {}, {}
    for part in LOG_PARTS:
        for axis in ("x", "z"):
            shape_by[f"*-{part}-{axis}"] = {"base": f"block/23/logpart-{part}-{axis}"}
    for bark in LIMB_BARKS:
        tex_by[f"*-{bark}-*"] = {"bark": {"base": f"block/23/bark-{bark}"}, "ring": {"base": f"block/23/heartwood-{bark}"},
                                 "moss": {"base": "block/23/moss-cushion"}}
    out.append(("// Level 23 (round 4): a fallen log's cell, a slice of its round section (one, two or three blocks across), rings on its ends", {
        "code": "l23-logpart",
        "variantgroups": [{"code": "bark", "states": LIMB_BARKS}, {"code": "part", "states": list(LOG_PARTS)}, {"code": "axis", "states": ["x", "z"]}],
        "creativeinventory": {"general": ["*-s1-x"], "backrooms": ["*-s1-x"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by, "texturesByType": tex_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 7,
        "drops": [G.drop("game:firewood", 0.6, 0.4)], "sounds": WOOD_SOUNDS}))
    cap_tex = {"top": "backrooms:block/23/mushcap-top", "side": "backrooms:block/23/mushcap-side", "gills": "backrooms:block/23/mushcap-gills"}
    out.append(sided("l23-caprim", "// Level 23 (round 4): a stone mushroom cap's edge (a drooping lip with gills under, or the upper layer's slope), facing out",
                     [("part", ["side", "corner", "upper", "uppercorner"])], lambda s: f"caprim-{s['part']}", lambda s: None,
                     "Stone", STONE_SOUNDS, extra={"textures": {k: {"base": v.replace("backrooms:", "")} for k, v in cap_tex.items()}}))
    out.append(sided("l23-boulderpart", "// Level 23 (round 4): a boulder's rounded top and edges, mossed on top",
                     [("part", ["cap", "edge", "corner"])], lambda s: f"boulder-{s['part']}", lambda s: None,
                     "Stone", STONE_SOUNDS, drops=[G.drop("game:stone-granite", 2, 1)],
                     extra={"textures": {"stone": {"base": "block/23/boulder"}, "moss": {"base": "block/23/moss-cushion"}}}))
    return out


def shapes():
    out = {}
    for bark, prof in BARK_PROFILES.items():
        for pat in ("a", "b"):
            name = f"barkface-{prof}{'-moss' if bark == 'moss' else ''}-{pat}"
            if name not in out:
                out[name] = shape(bark_textures(bark), barkface_shape(prof, bark, flip=pat == "b"))
    for form in ("full", "root"):
        out[f"flare-{form}"] = shape({"top": FLARE_KINDS["moss"][0], "side": FLARE_KINDS["moss"][1]}, flare_shape("moss", form))
    for kind in ("stub", "limb"):
        out[f"limb-{kind}"] = shape({"bark": "backrooms:block/23/bark-grey", "ring": "backrooms:block/23/heartwood-grey"}, limb_shape(kind))
    for part in LOG_PARTS:
        for axis in ("x", "z"):
            out[f"logpart-{part}-{axis}"] = shape({"bark": "backrooms:block/23/bark-grey", "ring": "backrooms:block/23/heartwood-grey",
                                                   "moss": "backrooms:block/23/moss-cushion"}, logpart_shape(part, axis))
    cap_tex = {"top": "backrooms:block/23/mushcap-top", "side": "backrooms:block/23/mushcap-side", "gills": "backrooms:block/23/mushcap-gills"}
    for part in ("side", "corner", "upper", "uppercorner"):
        out[f"caprim-{part}"] = shape(cap_tex, caprim_shape(part))
    for part in ("cap", "edge", "corner"):
        out[f"boulder-{part}"] = shape({"stone": "backrooms:block/23/boulder", "moss": "backrooms:block/23/moss-cushion"}, boulder_shape(part))
    return out


def aspen_eye(seed):
    img = M.noise_hv((30, 28, 26), 3, seed, mottle=4)
    return img


def textures(save):
    for bark in FACE_BARKS:
        src = load("mossbark" if bark == "moss" else f"bark-{bark}")
        save(opaque(deep(src, -40 if bark != "aspen" else -60, seed=2440 + len(bark))), f"block/23/barkdeep-{bark}")
    save(aspen_eye(2450), "block/23/aspen-eye")
    save(moss_cushion(2451), "block/23/moss-cushion")


LANG = [
    ("block-l23-barkface-grey-*", "Petrified Bark"),
    ("block-l23-barkface-red-*", "Petrified Redwood Bark"),
    ("block-l23-barkface-pale-*", "Petrified Oak Bark"),
    ("block-l23-barkface-dark-*", "Petrified Cypress Bark"),
    ("block-l23-barkface-aspen-*", "Petrified Aspen Bark"),
    ("block-l23-barkface-green-*", "Green Giant's Bark"),
    ("block-l23-barkface-moss-*", "Mossy Petrified Bark"),
    ("block-l23-flare-*", "Root Flare"),
    ("blockdesc-l23-flare-*", "Where the trunk goes into the ground it spreads, like something poured and set."),
    ("block-l23-limb-*", "Broken Limb"),
    ("block-l23-logpart-*", "Fallen Petrified Log"),
    ("blockdesc-l23-logpart-*", "A tree of the Garden that came down, a long time ago, and turned to stone where it lay."),
    ("block-l23-caprim-*", "Stone Mushroom Cap"),
    ("block-l23-boulderpart-*", "Mossy Boulder"),
]
