"""Assets for the survival loop (docs/design/survival-loop-plan.md): what has been picked over, what tells you where to go,
and what a home needs. Run on its own: python tools/gen_loop.py

- The sealed supply box's shape, torn supply boxes and prised-open crates: the three in four that wanderers went
  through before you.
- The anchor: the messages when a temporal gear will not take hold outside Level 0.
- Finding the way: wanderers' notes, and the names of the waypoints the Backrooms marks on your map.
- Dens: the Deathmoth hive that marks one.
- Needs: the pry bar that opens locked rooms, and seed packets for a farm at home.
"""
import json
import math
import os
import random
import re

from PIL import Image, ImageDraw

from detail_kit import ground_storable
import matlib as M
from gen_textures import (CRATE_WOOD, KRAFT, cardboard, hexrgb, match_mean, noise_fill, save, shade, sprite,
                          supply_box_faces, S)

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TAB, NL = "\t", "\n"

LANG = {}


# What each paper is about, in its name: notes of one kind stack (16), and this is how to tell the stacks apart
NOTE_KIND_NAMES = {"door": "a way through", "way": "a way out", "cache": "supplies", "refuge": "a refuge"}


def write_json(data, *rel, comment=None):
    path = os.path.join(ASSETS, *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False) + NL
    if comment:
        text = "// " + comment + NL + text
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)


def drops(*items):
    """(code, average, variance); codes without a domain are ours."""
    return [{"type": "item", "code": code, "quantity": {"avg": avg, "var": var}} for code, avg, var in items]


# ======================= Picked over =======================

def _proj(face, frm, to, top):
    """The UV of a face as the supply box always mapped its textures: projected straight onto the face (u along x or
    z, v down from the box's top `top`), so a bevel strip shows the same pixels as the face beside it."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    if face in ("north", "south"):
        return [x1, top - y2, x2, top - y1]
    if face in ("east", "west"):
        return [z1, top - y2, z2, top - y1]
    return [x1, z1, x2, z2]


def _el(name, frm, to, tex, top, faces=None, **extra):
    """One element with a texture key per face (`tex`: {face: key}) and projected UVs."""
    out = {}
    for f, k in tex.items():
        if faces and f not in faces:
            continue
        out[f] = {"texture": "#" + k, "uv": [round(v, 4) for v in _proj(f, frm, to, top)]}
    el = {"name": name, "from": list(frm), "to": list(to), "faces": out}
    el.update(extra)
    return el


def supply_box_shape():
    """The sealed supply box (graphics pass B3): the same 12 x 10 x 12 carton, now with its own faces
    (gen_textures.supply_box_faces: worn edges cut to these UVs, the tape over the top and down the north and south
    sides, the east and west sides plain). A version with bevelled edges (three crossed boxes) read in game as a lid
    sitting on a box, so it stays one box."""
    top = 10
    tex = {"north": "side", "south": "side", "east": "end", "west": "end", "up": "top", "down": "end"}
    els = [_el("Box", [2, 0, 2], [14, top, 14], tex, top)]
    els[0]["faces"]["up"]["uv"] = [2, 2, 14, 14]
    els[0]["faces"]["down"]["uv"] = [2, 2, 14, 14]
    write_json({"textureWidth": 16, "textureHeight": 16,
                "textures": {"side": "backrooms:block/supplybox-box-side", "end": "backrooms:block/supplybox-box-end",
                             "top": "backrooms:block/supplybox-box-top"},
                "elements": els}, "shapes", "block", "supplybox.json")


def _box(name, frm, to, faces, **extra):
    """One element; `faces` is {face: (texture key, uv)}, uv None for the game's own (the element's extent on that face,
    preview_shapes.auto_uv), so neighbouring faces continue one texture."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    auto = {"north": [16 - x1, 16 - y1, 16 - x0, 16 - y0], "south": [x0, 16 - y1, x1, 16 - y0],
            "west": [z0, 16 - y1, z1, 16 - y0], "east": [16 - z1, 16 - y1, 16 - z0, 16 - y0],
            "up": [x0, z0, x1, z1], "down": [x0, 16 - z1, x1, 16 - z0]}
    out = {f: {"texture": "#" + k, "uv": [round(v, 4) for v in (uv if uv is not None else auto[f])]}
           for f, (k, uv) in faces.items()}
    el = {"name": name, "from": list(frm), "to": list(to), "faces": out}
    el.update(extra)
    return el


def _all(key, uv=None, skip=()):
    return {f: (key, uv) for f in ("north", "south", "east", "west", "up", "down") if f not in skip}


def straw_bits(prefix, spots, y, bounds):
    """Packing straw as geometry: for each spot a heap of it (a low clump, and a smaller one on top) with loose stalks
    lying on and beside it, each stalk a 0.5 x 0.5 stick turned at its own angle, kept inside `bounds` (x0, z0, x1,
    z1: the inside of the box or crate). spots: (x, z, w, d, yaw, stalks)."""
    els = []
    rng = random.Random(len(prefix) * 31 + len(spots))
    bx0, bz0, bx1, bz1 = bounds
    for i, (x, z, w, d, yaw, n) in enumerate(spots):
        for j, (dx, dz, ww, dd, h) in enumerate(((0, 0, w, d, 0.75), (w * 0.2, d * 0.25, w * 0.55, d * 0.5, 0.5))):
            y0 = y + (0.75 if j else 0)
            els.append(_box(f"{prefix}Heap{i}{j}", [x + dx, y0, z + dz], [x + dx + ww, y0 + h, z + dz + dd],
                            {f: ("straw", [0, 0, ww, h] if f not in ("up", "down") else [0, 0, ww, dd])
                             for f in ("north", "south", "east", "west", "up")},
                            rotationOrigin=[x + w / 2, y, z + d / 2], rotationY=yaw + j * 25))
        for k in range(n):
            for _ in range(40):  # a stalk whose two ends both lie inside
                ln = rng.uniform(3, 5)
                cx, cz = x + rng.uniform(0, w), z + rng.uniform(0, d)
                a = math.radians(yaw + rng.uniform(-70, 70))
                ex, ez = math.cos(a) * ln / 2, math.sin(a) * ln / 2
                if all(bx0 + 0.4 <= px <= bx1 - 0.4 and bz0 + 0.4 <= pz <= bz1 - 0.4
                       for px, pz in ((cx + ex, cz - ez), (cx - ex, cz + ez))):
                    break
            sy = y + (1.25 if rng.random() < 0.5 else 0.75 if rng.random() < 0.5 else 0)
            els.append(_box(f"{prefix}Stalk{i}{k}", [cx - ln / 2, sy, cz - 0.25], [cx + ln / 2, sy + 0.5, cz + 0.25],
                            {f: ("straw", [0, k * 2 % 14, ln, k * 2 % 14 + 0.5]) for f in ("north", "south", "east", "west", "up")},
                            rotationOrigin=[cx, sy, cz], rotationY=math.degrees(a), rotationZ=rng.uniform(-8, 8)))
    return els


def rim_straw(prefix, rim, top, tufts):
    """Straw pulled up over a rim as the box or crate was gone through: tufts lying across the top of a wall (a flat
    clump on the rim and its end drooping down the inside), with a stalk standing out of each. rim: "north" or
    "west" (the wall's outer side); `top`: the rim's height and the wall's inner face; tufts: (position along the
    wall, width, how far onto the rim it reaches from the inner face, droop length)."""
    y, inner = top
    els = []
    for k, (u, w, on, droop) in enumerate(tufts):
        lean = 38 - 9 * (k % 3)  # how far the droop leans in from the wall, at its foot
        # (along the wall, up, across it into the box): built for the north rim, swapped for the west
        parts = [("On", (u, y, inner - on), (u + w, y + 0.5, inner + 0.5), None, 0),
                 ("Droop", (u + 0.2, y - droop, inner), (u + w - 0.2, y, inner + 0.5), (u + w / 2, y, inner + 0.25), lean),
                 ("Stalk", (u + w * 0.4, y + 0.25, inner - on * 0.6), (u + w * 0.4 + 0.5, y + 0.75, inner + 3.5),
                  (u + w * 0.4, y + 0.5, inner), -18)]
        for name, f, t, org, tilt in parts:
            if rim == "west":
                f, t = (f[2], f[1], f[0]), (t[2], t[1], t[0])
                org = (org[2], org[1], org[0]) if org else None
            faces = {fc: ("straw", [0, 2 * k + 2, 4, 2 * k + 6]) for fc in ("north", "south", "east", "west", "up", "down")
                     if not (name == "On" and fc == "down")}  # the clump's underside lies on the rim, unseen
            extra = {}
            if org:
                # north rim: a turn about x (negative swings the foot of the droop in), the west rim about z
                extra = {"rotationOrigin": list(org),
                         ("rotationX" if rim == "north" else "rotationZ"): (-tilt if rim == "north" else tilt)}
                if name == "Stalk":
                    extra["rotationY"] = (k * 37) % 50 - 25
            els.append(_box(f"{prefix}Rim{rim}{name}{k}", list(f), list(t), faces, **extra))
    return els


def paper_wad(prefix, x, y, z, s, yaw, key="paper"):
    """A crumpled ball of paper: two blocks of it at odd angles, one through the other, so it reads lumpy."""
    return [_box(f"{prefix}A", [x, y, z], [x + s, y + s * 0.75, z + s], _all(key, [0, 0, s, s], ("down",)),
                 rotationOrigin=[x + s / 2, y, z + s / 2], rotationY=yaw, rotationX=6),
            _box(f"{prefix}B", [x + s * 0.2, y + s * 0.2, z + s * 0.15], [x + s * 0.9, y + s * 0.95, z + s * 0.85],
                 _all(key, [4, 4, 4 + s * 0.7, 4 + s * 0.7], ("down",)),
                 rotationOrigin=[x + s / 2, y, z + s / 2], rotationY=yaw + 40, rotationZ=14)]


def torn_box_textures():
    """The opened supply box (D1): the sealed box's own cardboard (gen_textures.supply_box_faces), opened the way it
    was sealed: the tape slit along the seam where the two top flaps met, a ragged half of it left on each flap's
    edge, and the stub of it on each side cut through. The inside is plain kraft liner, darker toward the floor, with
    the bottom flaps' seam across the floor; the contents left behind (straw, a wrapper, a wad of paper) are geometry
    with textures of their own."""
    side, end, top = supply_box_faces()
    rng = random.Random(7101)
    px = side.load()
    for y in range(0, 8):  # the tape stub on the side, slit down the seam line, its cut edges lifting
        px[16, y] = M.rgba(M.lift(px[16, y], -34 + y * 2))
        M.touch(side, 15, y, 0.08)
        M.touch(side, 17, y, 0.05)
    for x in range(4, 28):  # the top edge: the cut board, a pale line of fibre where the flap was folded off it
        M.touch(side, x, 0, 0.1 + rng.uniform(0, 0.05))
    save(side, "block/supplybox-torn-side.png")

    # The flaps' outer face: the sealed top, the tape torn along the seam (x 16): each half ragged where it tore,
    # a pale fibre line where the board's skin came away with it
    flap = top.copy()
    p = flap.load()
    for y in range(S):
        p[16, y] = M.rgba(M.lift(p[16, y], -26))  # the slit
        r = rng.random()
        if r < 0.35:  # the tape tore short of the cut: board shows, its skin torn pale
            for x in ((14, 15) if rng.random() < 0.5 else (17, 18)):
                p[x, y] = M.rgba(M.lift(KRAFT, 18 + rng.uniform(-4, 4)))
        elif r < 0.6:
            M.touch(flap, 15 if rng.random() < 0.5 else 17, y, 0.1)  # a lifted tape edge
    save(flap, "block/supplybox-flap.png")

    # The flaps' inner face: unprinted liner, a little paler than the outside, a crease along the hinge (x 0-1 and
    # 30-31 of the texture are the hinge on the two major flaps)
    img = cardboard(7108, base=M.lift(KRAFT, 8), flutes=False)
    for y in range(S):
        for x, f in ((0, -0.1), (1, 0.05), (S - 1, -0.1), (S - 2, 0.05)):
            M.touch(img, x, y, f)
    save(img, "block/supplybox-torn-flapin.png")

    # Inside walls: the same liner in shadow, darkest at the foot (dark inside, as the pre-B3 box the user preferred);
    # the cut top edge lit (rows 0-20 are what shows)
    img = cardboard(7109, base=M.lift(KRAFT, -30))
    for y in range(S):
        f = -0.06 - 0.42 * min(1.0, y / 20) ** 1.2
        for x in range(S):
            M.touch(img, x, y, f)
    for x in range(S):
        M.touch(img, x, 0, 0.14)
    save(img, "block/supplybox-torn-inner.png")

    # The floor, seen from above (x and z 5-27 show): the bottom flaps' seam down the middle, the walls' shadow round
    # it, and an old water ring
    img = cardboard(7102, base=M.lift(KRAFT, -44))
    for y in range(S):
        M.touch(img, 16, y, -0.12)
        M.touch(img, 17, y, 0.04)
    M.ao_border(img, 4, 0.34, (5, 5, 27, 27))
    M.stain(img, 7104, radius=5, color=(52, 38, 24), strength=0.3, at=(20, 12))
    save(img, "block/supplybox-torn-inside.png")

    # Packing straw: dry stalks along the texture, lit on top
    img = M.noise_hv((184, 160, 100), 6, 7105, mottle=8)
    for y in range(0, S, 2):
        for x in range(S):
            M.touch(img, x, y, 0.08)
            M.touch(img, x, y + 1, -0.1)
    save(img, "block/supplybox-straw.png")

    # A crackers wrapper, foil-backed red film: a band of print, crinkles catching the light
    img = M.noise_hv((176, 50, 40), 4, 7106, mottle=8)
    p = img.load()
    for y in range(12, 20):
        for x in range(S):
            p[x, y] = M.rgba(M.lift((232, 196, 120), rng.uniform(-6, 6)))
    M.scratches(img, n=10, seed=7107, length=(3, 7), light=0.3)
    save(img, "block/supplybox-wrapper.png")

    # Crumpled newsprint (the box's wad and the crate's packing): grey-white paper, faint lines of print, creases
    img = M.paper(7110, base=(206, 202, 188), grain=3, mottle=6, fibre=0.4, seams=None)
    p = img.load()
    for y in range(2, S, 3):
        for x in range(S):
            if (x // 5 + y) % 7 and rng.random() < 0.8:
                p[x, y] = M.rgba(M.lift(p[x, y], -24))
    M.scratches(img, n=14, seed=7111, length=(3, 8), light=0.22)
    save(img, "block/supplybox-paper.png")


def torn_box_shape():
    """The opened supply box (D1). The sealed box (12 x 10 x 12, supply_box_shape) opened as it was closed: its two
    taped top flaps (hinged on the east and west rims, meeting under the tape at x 8) slit along the tape and folded
    back, the east one standing up and leaning out, a corner of it torn away, the west one hanging down the side; the
    two short inner flaps (north and south) bent up. Same footprint, the same faces as the sealed box outside; inside,
    the liner in shadow, and what was left in it as geometry: packing straw, a crumpled wrapper, a wad of paper.
    Everything stays inside the block."""
    T = 10      # wall height, as the sealed box
    W = 0.5     # board thickness (1 px)
    side = {"north": "side", "south": "side", "east": "end", "west": "end"}

    def wall(name, frm, to, out, inn):
        faces = {out: (side[out], _proj(out, frm, to, T)), inn: ("inner", _proj(inn, frm, to, T)),
                 "up": ("side", [frm[0] if out in ("north", "south") else frm[2], 0,
                                 to[0] if out in ("north", "south") else to[2], W]),
                 "down": ("end", None)}
        if out in ("north", "south"):  # the north and south walls run the full width: their ends are the box's corners
            faces["east"] = ("end", _proj("east", frm, to, T))
            faces["west"] = ("end", _proj("west", frm, to, T))
        return _box(name, frm, to, faces)

    els = [
        wall("WallN", [2, 0, 2], [14, T, 2 + W], "north", "south"),
        wall("WallS", [2, 0, 14 - W], [14, T, 14], "south", "north"),
        wall("WallW", [2, 0, 2 + W], [2 + W, T, 14 - W], "west", "east"),
        wall("WallE", [14 - W, 0, 2 + W], [14, T, 14 - W], "east", "west"),
        _box("Floor", [2 + W, 0, 2 + W], [14 - W, W, 14 - W], {"up": ("inside", None), "down": ("end", None)}),
    ]
    # The major flaps, modelled laid flat outward from their hinge (their liner up, the printed face down) and turned
    # about the hinge. The printed face's UVs are the sealed top's, mirrored about the hinge, so the tape's torn half
    # sits on each flap's free edge.
    def major(name, x0, x1, z0, z1, hinge, rot, uv):
        return _box(name, [x0, T - W, z0], [x1, T, z1],
                    {"down": ("flap", uv), "up": ("flapin", [x0 - hinge + 8, z0, x1 - hinge + 8, z1]),
                     "north": ("flapin", [0, 0, x1 - x0, W]), "south": ("flapin", [0, 0, x1 - x0, W]),
                     "east": ("flapin", [0, 0, z1 - z0, W]), "west": ("flapin", [0, 0, z1 - z0, W])},
                    rotationOrigin=[hinge, T, 8], rotationZ=rot)
    els += [
        # east: up and leaning out; the corner at the south end torn away (the tape went with the torn piece)
        major("FlapE", 14, 20, 2, 10.5, 14, 72, [14, 10.5, 8, 2]),
        major("FlapEtorn", 14, 17, 10.5, 14, 14, 72, [14, 14, 11, 10.5]),
        major("FlapEtorn2", 17, 18.5, 10.5, 12, 14, 72, [11, 12, 9.5, 10.5]),
        # west: folded right back, hanging down the outside
        major("FlapW", -4, 2, 2.05, 13.95, 2, 72, [8, 13.95, 2, 2.05]),  # a hair short of the corners (no z-fight)
    ]

    # The two inner flaps (shorter, unprinted), hinged on the north and south rims and bent up
    def minor(name, z0, z1, hinge, rot):
        return _box(name, [2.5, T - W, z0], [13.5, T, z1],
                    {"up": ("flapin", [2.5, 0, 13.5, z1 - z0]), "down": ("end", [2.5, 4, 13.5, 4 + z1 - z0]),
                     "north": ("flapin", [0, 0, 11, W]), "south": ("flapin", [0, 0, 11, W]),
                     "east": ("flapin", [0, 0, z1 - z0, W]), "west": ("flapin", [0, 0, z1 - z0, W])},
                    rotationOrigin=[8, T, hinge], rotationX=rot)
    els += [minor("FlapN", -3, 2, 2, 80), minor("FlapS", 14, 19, 14, -105)]

    # What was left in it, lying on the floor (y 0.5)
    y = W
    els += straw_bits("Box", [(3.2, 9.2, 4.5, 3.5, 20, 4), (9.5, 3.3, 3, 2.5, -30, 3)], y, (2.5, 2.5, 13.5, 13.5))
    els += rim_straw("Box", "north", (T, 2.5), ((4.2, 2.2, 0.5, 3), (9.8, 1.8, 0.5, 2.5)))
    for k, (x, z, ln, yaw) in enumerate(((3, 14.6, 4, 12), (8.5, 15.1, 3.5, -20), (6, 15.4, 3, 40))):
        els.append(_box(f"Dropped{k}", [x, 0, z], [x + ln, 0.5, z + 0.5],
                        {f: ("straw", [0, 4 * k, ln, 4 * k + 0.5]) for f in ("north", "south", "east", "west", "up")},
                        rotationOrigin=[x + ln / 2, 0, z + 0.25], rotationY=yaw))
    els += [
        _box("WrapperA", [8, y, 8], [11.5, y + 0.5, 11], _all("wrapper", [2, 4, 9, 10], ("down",)),
             rotationOrigin=[9.75, y, 9.5], rotationY=-25, rotationX=10),
        _box("WrapperB", [9.5, y + 0.4, 9.5], [12.5, y + 1.1, 12], _all("wrapper", [10, 10, 16, 15], ("down",)),
             rotationOrigin=[11, y, 10.75], rotationY=15, rotationZ=-20),
    ]
    els += paper_wad("Wad", 4, y, 4, 2.6, 30)
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"side": "backrooms:block/supplybox-torn-side", "end": "backrooms:block/supplybox-box-end",
                          "inner": "backrooms:block/supplybox-torn-inner", "inside": "backrooms:block/supplybox-torn-inside",
                          "flap": "backrooms:block/supplybox-flap", "flapin": "backrooms:block/supplybox-torn-flapin",
                          "straw": "backrooms:block/supplybox-straw", "wrapper": "backrooms:block/supplybox-wrapper",
                          "paper": "backrooms:block/supplybox-paper"},
             "elements": els}
    write_json(shape, "shapes", "block", "supplybox-torn.json")


def torn_box_block():
    write_json({
        "code": "supplybox-torn",
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood",
        "drawtype": "json",
        "shape": {"base": "block/supplybox-torn"},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "collisionbox": {"x1": 0.125, "y1": 0, "z1": 0.125, "x2": 0.875, "y2": 0.625, "z2": 0.875},
        "selectionbox": {"x1": 0.125, "y1": 0, "z1": 0.125, "x2": 0.875, "y2": 0.625, "z2": 0.875},
        "lightAbsorption": 0,
        "resistance": 0.3,
        # Someone got here first: the food is gone, and what is left is what they did not want
        "drops": drops(("carpetfibre", 0.6, 0.6), ("wallpaperstrip", 0.5, 0.5), ("game:paper-parchment", 0.4, 0.4),
                       ("game:drygrass", 0.3, 0.3), ("glassshard", 0.2, 0.2), ("game:flint", 0.02, 0),
                       ("wanderernote-door", 0.03, 0), ("wanderernote-way", 0.03, 0)),
        "sounds": {"place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
    }, "blocktypes", "supplybox-torn.json", comment="Generated by tools/gen_loop.py. A supply box someone else already went through.")
    LANG["block-supplybox-torn"] = "Torn Supply Box"
    LANG["blockdesc-supplybox-torn"] = "Torn open and gone through long ago. Whatever was worth eating is gone; the scraps they left might still be of use."


def open_crate_textures():
    """The emptied crate's own textures (D1): the backs of the boards seen from inside (the same three boards as the
    outside, in shadow, darkest toward the floor, the nail points through at the frame), the floor inside, fresh pale
    wood where a board split, and nail steel. The outside, the rim and the bottom are the closed crate's own faces."""
    inner = M.wood_planks(3450, base=M.lift(CRATE_WOOD, -12), planks=3, grain=3, contrast=0.8, per_plank=8, flecks=0.8)
    for y in range(S):
        f = -0.06 - 0.4 * (y / (S - 1)) ** 1.2
        for x in range(S):
            M.touch(inner, x, y, f)
    for x in range(S):
        M.touch(inner, x, 0, 0.12)  # the top edge of the boards catches the light
    p = inner.load()
    for (nx, ny) in ((2, 1), (S - 3, 1), (2, 15), (S - 3, 15), (2, S - 2), (S - 3, S - 2)):  # nail points
        p[nx, ny] = M.rgba((70, 66, 62))
        M.touch(inner, nx, ny + 1, -0.1)
    save(match_mean(inner, 62), "block/level1/crate-open-side.png")

    # The floor inside (x and z 3-29 show): boards across it, the walls' shadow round it, dust and loose straw
    floor = M.wood_planks(3460, base=M.lift(CRATE_WOOD, -18), planks=3, grain=3, contrast=0.8, per_plank=8,
                          direction="v", flecks=0.8)
    M.ao_border(floor, 5, 0.42, (3, 3, 29, 29))
    M.grime(floor, 0.18, 3461, color=(70, 56, 38), cells=(8, 4), cover=0.5)
    rng = random.Random(3462)
    for _ in range(26):  # stray straw, too short to model
        x, y = rng.randrange(4, 28), rng.randrange(4, 28)
        dx = rng.choice((-1, 1))
        for k in range(rng.randint(2, 4)):
            p = floor.load()
            p[x + k * dx, y + (k // 2)] = M.rgba(M.lift((178, 152, 92), rng.uniform(-16, 6)))
    save(floor, "block/level1/crate-open-top.png")

    # Split wood: fresh and pale where a board broke or a lid board was torn off, the fibres along it
    split = M.wood_planks(3470, base=M.lift(CRATE_WOOD, 34), planks=[8, 8, 8, 8], grain=4, contrast=1.2, per_plank=5)
    save(split, "block/level1/crate-open-split.png")

    # Nail steel: dark, a little rust, a lit edge
    img = M.painted_metal(3480, base=(86, 84, 80), panel=False, chips=0)
    M.rust(img, 0.25, 3481)
    save(img, "block/level1/crate-open-nail.png")


def open_crate_shape():
    """The emptied crate (D1): the closed crate (gen_textures.crate, still a cube) with its lid prised off. The same
    four sides outside, now walls 1.5 thick (the frame's width); their tops are the closed crate's own top frame, so
    from above the crate reads as the same box with the boards of the lid gone. Inside: the backs of the boards in
    shadow and a floor, one lid board thrown back in and leaning against the north wall, packing straw and a ball of
    newspaper left behind, and two of the lid's nails bent up on the rim. The middle board of the north side is broken
    out at its west end (clear of the brace painted across it), so you see into the crate there. Nothing stands
    above the block (crates are stacked), except the nail tips, which go into the crate above."""
    T = 1.5  # wall thickness: the frame's width on the closed crate's textures (3 px)
    out = {"north": "side", "south": "side", "east": "side", "west": "side"}
    els = []

    def wall(name, frm, to, outer, inner, ends=()):
        faces = {outer: (out[outer], None), inner: ("inside", None), "up": ("top", None), "down": ("top", None)}
        for e in ends:
            faces[e] = ("side", None)
        return _box(name, frm, to, faces)
    # North wall, with the broken board: the middle board (y 5-10.5) is gone from x 1.5 to 4 below y 7.5 and to 5
    # above it (a stepped break), a splinter left standing on the board under it
    els += [
        wall("WallN", [5, 0, 0], [16, 16, T], "north", "south", ("east",)),
        wall("WallNcorner", [0, 0, 0], [1.5, 16, T], "north", "south", ("west",)),
        wall("WallNlow", [1.5, 0, 0], [5, 5, T], "north", "south"),
        wall("WallNhigh", [1.5, 10.5, 0], [5, 16, T], "north", "south"),
        _box("WallNstub", [4, 5, 0], [5, 7.5, T], {"north": ("side", None), "south": ("inside", None),
                                                    "west": ("split", None), "up": ("split", None)}),
        _box("Splinter", [2.5, 5, 0.25], [3.5, 6, 1], {"north": ("split", None), "south": ("split", None),
                                                       "east": ("split", None), "west": ("split", None),
                                                       "up": ("split", None)}, rotationOrigin=[3, 5, 0.6], rotationZ=-12),
    ]
    # The faces round the break: the cut ends of the boards above and below, pale split wood
    els[2]["faces"]["up"] = {"texture": "#split", "uv": [1.5, 0, 5, 1.5]}
    els[3]["faces"]["down"] = {"texture": "#split", "uv": [1.5, 14.5, 5, 16]}
    els[0]["faces"]["west"] = {"texture": "#split", "uv": [0, 0, 1.5, 16]}
    els += [
        wall("WallS", [0, 0, 16 - T], [16, 16, 16], "south", "north", ("east", "west")),
        wall("WallW", [0, 0, T], [T, 16, 16 - T], "west", "east"),
        wall("WallE", [16 - T, 0, T], [16, 16, 16 - T], "east", "west"),
        _box("Floor", [T, 0, T], [16 - T, 1, 16 - T], {"up": ("floor", None), "down": ("top", None)}),
    ]
    # A lid board thrown back in, its foot on the floor and its head against the east wall: one of the closed crate's
    # top boards (crate-top, the middle board), its torn-off ends pale
    L, a = 14, 55
    x0 = 14.3 - L * math.cos(math.radians(a))
    els.append(_box("LidBoard", [x0, 1, 3], [x0 + L, 2, 7.4],
                    {"up": ("top", [1.5, 5.75, 13.5, 10.15]), "down": ("inside", [1.5, 1, 13.5, 5.4]),
                     "north": ("split", [0, 0, L, 1]), "south": ("split", [0, 0, L, 1]),
                     "east": ("split", [0, 0, 4.4, 1]), "west": ("split", [0, 0, 4.4, 1])},
                    rotationOrigin=[x0, 1, 5.2], rotationZ=a))
    # Packing straw (a heap in the south-west corner, a little under the break) and a ball of newspaper
    els += straw_bits("Crate", [(2.2, 9.5, 5, 4, 15, 5), (9.5, 11.8, 3.5, 2.2, -20, 3)], 1, (T, T, 16 - T, 16 - T))
    # straw pulled up over the north and west rims as it was gone through (it lies in the crate above in a stack)
    els += rim_straw("Crate", "north", (16, T), ((3.2, 2.6, 1.2, 4), (10.8, 2.0, 0.9, 3)))
    els += rim_straw("Crate", "west", (16, T), ((6.2, 2.4, 1.1, 3.5),))
    els += paper_wad("Wad", 8, 1, 8.2, 3, -25)
    # Two of the lid's nails, bent over on the rim
    for i, (x, z, rot) in enumerate(((7.75, 15, 28), (15, 6.5, -24))):
        els.append(_box(f"Nail{i}", [x, 16, z], [x + 0.5, 17.2, z + 0.5], _all("nail", [0, 0, 0.5, 1.2], ("down",)),
                        rotationOrigin=[x + 0.25, 16, z + 0.25], rotationZ=rot))
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"side": "backrooms:block/level1/crate-side", "top": "backrooms:block/level1/crate-top",
                          "inside": "backrooms:block/level1/crate-open-side", "floor": "backrooms:block/level1/crate-open-top",
                          "split": "backrooms:block/level1/crate-open-split", "nail": "backrooms:block/level1/crate-open-nail",
                          "straw": "backrooms:block/supplybox-straw", "paper": "backrooms:block/supplybox-paper"},
             "elements": els}
    write_json(shape, "shapes", "block", "crate-open.json")


def open_crate():
    open_crate_textures()
    open_crate_shape()
    write_json({
        "code": "crate-open",
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood",
        # (D1) a shape now: the lid prised off, the inside and what was left in it modelled (open_crate_shape). The
        # shape names its own textures: a blocktype "all" here would paint every part with one
        "drawtype": "json",
        "shape": {"base": "block/crate-open"},
        "sidesolid": {"all": False, "down": True},
        "sideopaque": {"all": False},
        "resistance": 1.0,
        "lightAbsorption": 99,
        # Prised open and emptied; the boards are still good
        "drops": drops(("game:plank-aged", 1.5, 1), ("game:metalnailsandstrips-iron", 0.3, 0.3), ("game:stick", 0.5, 0.5)),
        "sounds": {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    }, "blocktypes", "level1", "crate-open.json", comment="Generated by tools/gen_loop.py. A crate someone else already emptied.")
    LANG["block-crate-open"] = "Emptied Crate"
    LANG["blockdesc-crate-open"] = "Prised open and emptied. The boards are still good."


# ======================= The anchor =======================

def anchor():
    # Shown when a temporal gear is used outside Level 0, and when a spawn point outside it is cleared
    LANG["anchor-refused"] = "Nothing here will hold you. Only the Lobby still remembers where you came from."
    LANG["anchor-lost"] = "You will wake in the Lobby again: nowhere else in the Backrooms remembers you."


# ======================= Finding the way =======================

def item(code, texture, cls=None, extra=None, variants=None, ground=None):
    """A flat item; `ground` is how it is set down on the floor (detail_kit.ground_storable's arguments)."""
    data = {"code": code}
    if cls:
        data["class"] = cls
    if variants:
        data["variantgroups"] = variants
    data.update({
        "maxstacksize": 16,
        "texture": {"base": texture},
        "creativeinventory": {"general": ["*"], "items": ["*"]},
        "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
        "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
        "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
    })
    if extra:
        data.update(extra)
    return ground_storable(data, **(ground or {}))


def notes():
    # A scrap of lined paper folded in two, a pencilled scrawl and an arrow showing through
    img = sprite()
    d = ImageDraw.Draw(img)
    paper, edge, line, pencil = (226, 218, 192, 255), (150, 138, 108, 255), (176, 190, 206, 255), (70, 66, 60, 255)
    d.polygon([(5, 7), (25, 4), (27, 25), (7, 28)], fill=paper, outline=edge)
    d.line([(6, 17), (26, 14)], fill=(198, 188, 160, 255))  # the fold
    for y in (9, 12, 20, 23):
        d.line([(8, y + 1), (24, y - 2)], fill=line)
    rng = random.Random(7201)
    for y in (10, 21):
        x = 9
        while x < 22:
            w = rng.randint(2, 4)
            d.line([(x, y + 1 - (x - 8) // 6), (x + w, y + 1 - (x + w - 8) // 6)], fill=pencil)
            x += w + 2
    d.line([(12, 25), (20, 24)], fill=pencil)  # an arrow at the foot
    d.polygon([(20, 22), (23, 24), (20, 26)], fill=pencil)
    save(img, "item/wanderernote.png")

    write_json(item("wanderernote", "item/wanderernote", cls="BackroomsWandererNote",
                    variants=[{"code": "kind", "states": ["door", "way", "cache", "refuge"]}],
                    extra={"creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 300,
                           "combustibleProps": {"burnTemperature": 600, "burnDuration": 3}}),
               "itemtypes", "wanderernote.json", comment="Generated by tools/gen_loop.py. Read it (right-click) and it marks a place on the map.")
    for kind in ("door", "way", "cache", "refuge"):
        LANG[f"item-wanderernote-{kind}"] = "Wanderer's Note (" + NOTE_KIND_NAMES[kind] + ")"
    LANG["itemdesc-wanderernote-door"] = "Directions in pencil, half rubbed out: something about a way through the wall. Right-click to read it."
    LANG["itemdesc-wanderernote-way"] = "Someone's directions to a way out of here, scrawled in a hurry. Right-click to read it."
    LANG["itemdesc-wanderernote-cache"] = "A list of supplies, crossed out, and a few words about where the rest were left. Right-click to read it."
    LANG["itemdesc-wanderernote-refuge"] = "A note about somewhere safe, underlined twice. Right-click to read it."

    # What the notes say. {0} is a direction in words, {1} a distance in paces
    LANG.update({
        "note-door-1": "\"The wall goes on for ever, but it doesn't. There's a way through, {0}, about {1} paces. I marked it.\"",
        "note-door-2": "\"Followed the wall for hours. Door at last, {0} of here. {1} paces, give or take. Don't run when you get near it.\"",
        "note-door-3": "\"If you're reading this you're lost like we were. The gap in the wall is {0}, maybe {1} paces. Go quiet.\"",
        "note-way-1": "\"There's another way out of here, {0}, {1} paces or so. It doesn't go where you'd think.\"",
        "note-way-2": "\"Lift (or stairs, or a hole, I don't remember) {0}, about {1} paces. Took it once. Never again.\"",
        "note-way-3": "\"{1} paces {0}. That's where it lets you out. Mark it.\"",
        "note-cache-1": "\"Left what we couldn't carry {0} of here, {1} paces. Still sealed. Take it, we won't be back.\"",
        "note-cache-2": "\"Supplies {0}, about {1} paces. Nobody's opened them. Yet.\"",
        "note-cache-3": "\"Box, sealed, {0}, {1} paces. Food in it, I think. Something was standing near it so I left.\"",
        "note-refuge-1": "\"Somewhere safe, {0}, about {1} paces. Nothing follows you in there.\"",
        "note-refuge-2": "\"If they're after you, go {0}. {1} paces. You can rest there.\"",
        "note-refuge-3": "\"Friendly faces {0} of here, {1} paces. Bring something to trade.\"",
        "note-nothing": "The note's directions don't fit anything round here. Perhaps it was written somewhere else.",
        "dir-n": "north", "dir-ne": "north-east", "dir-e": "east", "dir-se": "south-east",
        "dir-s": "south", "dir-sw": "south-west", "dir-w": "west", "dir-nw": "north-west",
        # Waypoints the Backrooms marks for you
        "levelname": "Level {0}",
        "levelname-6.1": "Level 6.1",
        "waypoint-way": "Way to {0}",
        "waypoint-oneway": "Way to {0} (one way)",
        "waypoint-back": "Way back to {0}",
        "waypoint-gate": "Gate: {0} / {1}",
        # (said instead where the map setting makes no waypoints: the place, which way and how far)
        "mapmark-told": "{0}: {1}, about {2} paces.",
        "waypoint-note-door": "Gate to {0} (a note)",
        "waypoint-note-way": "Way out (a note)",
        "waypoint-note-cache": "Something left (a note)",
        "waypoint-note-refuge": "Refuge (a note)",
    })


# ======================= Dens =======================

def moth_hive():
    # Grey, papery, layered like a wasps' nest, with dark holes where they come and go
    img = noise_fill(hexrgb(0x8C877C), 8, 7301)
    d = ImageDraw.Draw(img)
    rng = random.Random(7302)
    for y in range(1, S, 3):
        x0 = rng.randint(-4, 2)
        d.arc([x0, y - 2, x0 + S + 6, y + 4], 180, 360, fill=shade((110, 104, 94), rng.uniform(0.85, 1.1)))
    for _ in range(5):
        x, y = rng.randint(3, S - 5), rng.randint(3, S - 5)
        d.ellipse([x, y, x + 2, y + 3], fill=(30, 26, 22, 255))
    save(img, "block/detail/mothhive.png")

    tex = "#hive"
    def lump(name, a, b, rot=None):
        e = {"name": name, "from": list(a), "to": list(b),
             "faces": {f: {"texture": tex, "uv": [0, 0, 16, 16]} for f in ("north", "east", "south", "west", "up", "down")}}
        if rot:
            e["rotationOrigin"] = [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2]
            e["rotationY"] = rot
        return e
    write_json({"textureWidth": 16, "textureHeight": 16, "textures": {"hive": "backrooms:block/detail/mothhive"},
                "elements": [lump("Base", (2, 0, 3), (14, 5, 13)), lump("Mid", (3, 5, 4), (13, 10, 12), 20),
                             lump("Top", (5, 10, 5), (11, 13, 10), 40), lump("Bud", (10, 0, 11), (15, 6, 15), 15),
                             lump("Bud2", (1, 0, 1), (6, 4, 6), 30)]},
               "shapes", "block", "detail", "mothhive.json")
    write_json({
        "code": "mothhive",
        "shape": {"base": "block/detail/mothhive"},
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Plant",
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 1.0,
        "collisionbox": {"x1": 0.1, "y1": 0, "z1": 0.15, "x2": 0.9, "y2": 0.8, "z2": 0.85},
        "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.15, "x2": 0.9, "y2": 0.8, "z2": 0.85},
        "sounds": {"place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
        # Chewed paper and carpet, and what they lined it with
        "drops": drops(("game:paper-parchment", 1, 1), ("carpetfibre", 2, 1), ("game:cloth-plain", 0.3, 0.3)),
    }, "blocktypes", "detail", "mothhive.json", comment="Generated by tools/gen_loop.py. A Deathmoth hive, the mark of a den.")
    LANG["block-mothhive"] = "Deathmoth Hive"
    LANG["blockdesc-mothhive"] = "Grey paper chewed from walls and carpet, layered like a wasps' nest. Something rustles inside. Breaking it will not go unnoticed."


# ======================= Needs =======================

def write_recipe(data, name):
    write_json(data, "recipes", "grid", name + ".json")


def pry_bar():
    img = sprite()
    d = ImageDraw.Draw(img)
    steel, hi, lo = (120, 126, 134, 255), (190, 196, 204, 255), (64, 68, 74, 255)
    d.line([(7, 28), (24, 6)], fill=lo, width=4)  # the shaft
    d.line([(7, 27), (23, 6)], fill=steel, width=2)
    d.line([(8, 26), (22, 7)], fill=hi)
    d.line([(24, 6), (27, 4), (29, 6)], fill=steel, width=2)  # the claw, curled over
    d.point((29, 7), fill=lo)
    d.line([(6, 29), (4, 27)], fill=steel, width=2)  # the flattened chisel end
    d.rectangle([9, 21, 13, 25], fill=(150, 40, 30, 255))  # a scrap of red paint left on it
    save(img, "item/prybar.png")
    write_json(item("prybar", "item/prybar", cls="BackroomsPryBar", extra={
        "maxstacksize": 1,
        "durability": 24,
        "tags": ["weapon", "weapon-melee"],
        "damagedby": ["attacking"],
        "attackpower": 2,
        "attackRange": 2,
        "creativeinventory": {"general": ["*"], "items": ["*"], "tools": ["*"]},
    }, ground={"layout": "Halves", "ctrl": True}), "itemtypes", "prybar.json", comment="Generated by tools/gen_loop.py. Hold right-click on a locked door to force it.")
    write_recipe({
        "ingredientPattern": "BBN",
        "ingredients": {"B": {"type": "item", "code": "backrooms:metalbracket"},
                        "N": {"type": "item", "code": "game:metalnailsandstrips-iron"}},
        "width": 3, "height": 1, "shapeless": True,
        "output": {"type": "item", "code": "backrooms:prybar"},
    }, "prybar")
    LANG["item-prybar"] = "Pry Bar"
    LANG["itemdesc-prybar"] = ("Hold right-click on a locked door to force it. It gives for good if there is a room behind it, but everything "
                               "nearby will hear. Doors set in solid wall will not give, and cost nothing to try.")
    LANG["pry-solid"] = "It won't give. There's solid wall behind it."
    LANG["pry-notlocked"] = "It isn't locked. It goes somewhere."


SEED_CROPS = ("turnip", "carrot", "onion", "flax", "spelt")
SEED_COLOURS = {"turnip": (196, 120, 200), "carrot": (232, 128, 40), "onion": (210, 180, 110), "flax": (90, 130, 210), "spelt": (210, 176, 70)}


def seed_packets():
    for crop, colour in SEED_COLOURS.items():
        img = sprite()
        d = ImageDraw.Draw(img)
        d.rectangle([8, 4, 24, 28], fill=(232, 224, 200, 255), outline=(140, 128, 100, 255))  # the paper packet
        d.rectangle([9, 9, 23, 21], fill=colour + (255,))  # the picture on the front
        d.ellipse([12, 11, 20, 19], fill=shade(colour, 0.7))
        d.line([(8, 7), (24, 7)], fill=(170, 158, 128, 255))  # the folded top, torn at a corner
        d.polygon([(21, 4), (24, 4), (24, 7)], fill=(0, 0, 0, 0))
        d.line([(10, 24), (22, 24)], fill=(90, 84, 70, 255))  # the name, too faded to read
        save(img, f"item/seedpacket-{crop}.png")
    write_json(item("seedpacket", "item/seedpacket-{crop}", variants=[{"code": "crop", "states": list(SEED_CROPS)}],
                    extra={"maxstacksize": 32, "texture": {"base": "item/seedpacket-{crop}"}}),
               "itemtypes", "seedpacket.json", comment="Generated by tools/gen_loop.py. Opened in the crafting grid for four seeds.")
    write_recipe({
        "ingredientPattern": "P",
        "ingredients": {"P": {"type": "item", "code": "backrooms:seedpacket-*", "name": "crop"}},
        "width": 1, "height": 1,
        "output": {"type": "item", "code": "game:seeds-{crop}", "stacksize": 4},
    }, "seeds-from-packet")
    for crop in SEED_CROPS:
        LANG[f"item-seedpacket-{crop}"] = f"Seed Packet ({crop.capitalize()})"
    LANG["itemdesc-seedpacket-turnip"] = "An old packet of seeds, still sealed. Open it in the crafting grid."
    for crop in SEED_CROPS[1:]:
        LANG[f"itemdesc-seedpacket-{crop}"] = LANG["itemdesc-seedpacket-turnip"]


# ======================= Lang =======================

def merge_lang():
    """Adds the names to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_lines = []
    for key, value in LANG.items():
        line = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)
    json.loads(text)


def main():
    supply_box_shape()
    torn_box_textures()
    torn_box_shape()
    torn_box_block()
    open_crate()
    anchor()
    notes()
    moth_hive()
    pry_bar()
    seed_packets()
    merge_lang()
    print(f"gen_loop: {len(LANG)} names")


if __name__ == "__main__":
    main()
