"""Level 9's houses from layout version 9 (WorldLayout.PlanExteriorV9): tall windows (a sash window, the same with
shutters, a picture window three wide), front and back doors that open and close, the garage door cased in trim, the
cap on a brick chimney stack, and the house stairs' steps with a balustrade. Textures, shapes, block types and names.
Called from gen_deep.generate() (python tools/gen_detail.py runs it).

Every model is built as the whole thing, facing north (its outside to the north, z = 0 the wall's outer face, z = 16 its
inner face), then cut into the blocks it spans: a window is two blocks high (rel 2-3 over the floor), a picture window
three wide, a door two high, a garage door three wide and two high. Parts are named by where they lie in the model as
it faces north: w the west end (x = 0), m between, e the east end; the world generator reads which part a block is from
its neighbours along the wall (WorldGenerator.Deep.cs, AlongWall) and turns it by its side. Trim stands proud of the
wall (no face lies on a neighbour's), hardware is geometry, and the siding round them is the neighbouring blocks'.
"""
import json
import math
import os
import random

from PIL import Image

import matlib as M
import modelkit as K
from detail_kit import ASSETS, GLASS, LANG, ROTATE, SIDES, STONE, WOOD, block, cuboid, name, seed_of, tpath, write_json
from detail_textures import S, save

PX = 0.5
TRIM = (236, 234, 226)
INSIDE = "plaster-interior"  # the inner faces of a house wall (gen_deep: housewall)
NO_FRONT = ("east", "west", "up", "down", "south")


# ---------------- Element helpers ----------------

def bx(name, frm, to, tex, faces=K.DIRS, glow=0, uv=None):
    return K.box(name, frm, to, tex, faces=faces, glow=glow, uv=uv)


def _clip(els, axis, lo, hi):
    """The unrotated elements cut to lo..hi along an axis (0 x, 1 y) and moved down by lo, their pictures cut in the same
    proportion (a north face's u runs east to west, every other face's west to east; a side face's v runs top to
    bottom); a face left lying on a cut is dropped."""
    out = []
    for e in json.loads(json.dumps(els)):
        assert not any(k in e for k in ("rotationX", "rotationY", "rotationZ")), e["name"]
        a, b = e["from"][axis], e["to"][axis]
        n1, n2 = max(a, lo), min(b, hi)
        if n2 - n1 < 1e-6:
            continue
        for k, f in list(e["faces"].items()):
            u1, v1, u2, v2 = f["uv"]
            if axis == 0 and k in ("north", "south", "up", "down"):
                def at(x):
                    t = (b - x) / (b - a) if k == "north" else (x - a) / (b - a)
                    return round(u1 + t * (u2 - u1), 4)
                f["uv"] = [at(n2), v1, at(n1), v2] if k == "north" else [at(n1), v1, at(n2), v2]
            if axis == 1 and k in ("north", "south", "east", "west"):
                def at(y):
                    return round(v1 + (b - y) / (b - a) * (v2 - v1), 4)
                f["uv"] = [u1, at(n2), u2, at(n1)]
        if n1 > a + 1e-6:
            e["faces"].pop("west" if axis == 0 else "down", None)
        if n2 < b - 1e-6:
            e["faces"].pop("east" if axis == 0 else "up", None)
        if not e["faces"]:
            continue
        # (the other axes keep their extent: parts reaching out of the block, like proud trim, stay as they are)
        e["from"][axis], e["to"][axis] = round(n1 - lo, 4), round(n2 - lo, 4)
        out.append(e)
    return out


def cut(els, cols, rows):
    """The model cut into blocks: {(col, row): elements}, col 0 the west block, row 0 the lowest. Parts proud of the
    model's outline (trim, a sill) go with the block whose span holds them; past the ends, the end blocks."""
    parts = {}
    for c in range(cols):
        x_lo, x_hi = (-99 if c == 0 else 16 * c), (99 if c == cols - 1 else 16 * (c + 1))
        cx = _clip(els, 0, x_lo, x_hi)
        for e in cx:  # (_clip moved them by x_lo; put back what was moved by -99 and take off this block's start)
            shift = (16 * c) - x_lo
            e["from"][0] = round(e["from"][0] - shift, 4)
            e["to"][0] = round(e["to"][0] - shift, 4)
        for r in range(rows):
            y_lo, y_hi = (-99 if r == 0 else 16 * r), (99 if r == rows - 1 else 16 * (r + 1))
            cy = _clip(cx, 1, y_lo, y_hi)
            for e in cy:
                shift = (16 * r) - y_lo
                e["from"][1] = round(e["from"][1] - shift, 4)
                e["to"][1] = round(e["to"][1] - shift, 4)
            parts[(c, r)] = cy
    return parts


def mirror_x(els):
    """The elements mirrored west to east (x -> 16 - x): east and west faces swap, the rest mirror their pictures."""
    out = []
    for e in json.loads(json.dumps(els)):
        x1, x2 = e["from"][0], e["to"][0]
        e["from"][0], e["to"][0] = round(16 - x2, 4), round(16 - x1, 4)
        if "rotationOrigin" in e:
            e["rotationOrigin"][0] = round(16 - e["rotationOrigin"][0], 4)
            if "rotationY" in e:
                e["rotationY"] = -e["rotationY"]
            if "rotationZ" in e:
                e["rotationZ"] = -e["rotationZ"]
        faces = {}
        for k, f in e["faces"].items():
            k2 = {"east": "west", "west": "east"}.get(k, k)
            if k in ("north", "south", "up", "down"):
                u1, v1, u2, v2 = f["uv"]
                f["uv"] = [u2, v1, u1, v2]
            faces[k2] = f
        e["faces"] = faces
        out.append(e)
    return out


def flip_back(el):
    """A pane whose picture must read the same from inside as from outside: its inside (south) face mirrored."""
    f = el["faces"].get("south")
    if f:
        u1, v1, u2, v2 = f["uv"]
        f["uv"] = [u2, v1, u1, v2]
    return el


def write_shape(name_, els, textures):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    table = {k: textures.get(k, tpath(k)) for k in keys}
    write_json(os.path.join(ASSETS, "shapes", "block", "detail", "suburbs", name_ + ".json"),
               {"textureWidth": 16, "textureHeight": 16, "textures": table, "elements": els})
    return "block/detail/suburbs/" + name_


TEX = {"brass": "backrooms:block/level5/brass"}


# ---------------- Textures ----------------

def _glass(state, curtains, seed):
    """Window glass by night: dark with the sky's faint sheen, or lit warm from inside; curtains drawn back at the
    sides named ("l" the left of the picture, "r" its right)."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            fold = 0.85 + 0.15 * math.sin(x * 1.9)
            edge_l, edge_r = x, S - 1 - x
            if state == "dark":
                sheen = max(0.0, 1 - abs((x + y * 0.6) - 18) / 6) * 0.3
                c = M.mix((12, 16, 24), (42, 52, 66), 0.25 * (1 - y / S) + sheen)
                curtain = (58, 48, 40)
            else:
                glow = 1 - abs(x - S / 2) / (S / 2) * 0.3 - y / S * 0.1
                c = M.shade_px((255, 216, 144), glow - 1)
                curtain = (216, 144, 74)
            for side, d in (("l", edge_l), ("r", edge_r)):
                if side in curtains and d < 6:
                    c = M.mix(c, M.shade_px(curtain, (fold - 1) * 0.6 - 0.05 * (6 - d) / 6), 0.6 if state == "dark" else 0.85)
            k = rng.uniform(0.96, 1.04)
            px[x, y] = M.rgba(tuple(v * k for v in c))
    return img


def textures():
    for state in ("dark", "lit"):
        for kind, curtains in (("c", "lr"), ("l", "l"), ("r", "r"), ("p", "")):
            save(_glass(state, curtains, seed_of(f"suburbglass-{state}-{kind}")), f"suburbglass-{state}-{kind}")
    # Louvred shutters, painted a dark green: slats every 3 px, lit along their top, in shadow under the one above
    img = M.noise_hv((50, 74, 58), amp=3, seed=seed_of("shutter"), mottle=3, hue=1)
    for y in range(S):
        f = (0.14, 0.02, -0.22)[y % 3]
        for x in range(S):
            M.touch(img, x, y, f)
    save(img, "shutterlouvre")
    save(M.noise_hv((50, 74, 58), amp=2, seed=seed_of("shutterframe"), mottle=2, hue=1), "shutterpaint")
    # The front door's paint (as B11's painted door) on wood with a faint upright grain
    img = M.noise_hv((136, 48, 36), amp=3, seed=seed_of("doorpaint"), mottle=3, hue=1.5)
    rng = random.Random(seed_of("doorgrain"))
    for x in range(S):
        if rng.random() < 0.25:
            for y in range(S):
                M.touch(img, x, y, -0.05)
    save(img, "doorpaint")
    # The garage door: white painted steel, a faint roll grain across it; the dark gap between its sections
    img = M.painted_metal(seed=seed_of("garagepaint"), base=(226, 224, 214), panel=False, chips=0)
    save(img, "garagepaint")
    save(M.noise_hv((70, 70, 68), amp=2, seed=seed_of("garagegap"), mottle=2), "garagegap")
    # The chimney: a poured crown and a terracotta flue pot, its throat black with soot
    save(M.concrete(seed=seed_of("chimneycrown"), base=(150, 146, 138), grain=3, mottle=5, aggregate=0.05), "chimneycrown")
    img = M.noise_hv((164, 88, 58), amp=4, seed=seed_of("fluepot"), mottle=4, hue=2)
    for y in (3, 4, 27, 28):
        for x in range(S):
            M.touch(img, x, y, -0.12 if y in (4, 28) else 0.08)
    M.grime(img, 0.25, seed=seed_of("flueSoot"), color=(40, 34, 30), cover=0.3)
    save(img, "fluepot")
    save(M.noise_hv((24, 22, 20), amp=2, seed=seed_of("fluethroat"), mottle=2), "fluethroat")


# ---------------- Windows ----------------

def _sash(name, x1, x2, y1, y2, z1, z2, glass, glow, bars=True, flip=False):
    """A sash: stiles and rails round a pane, glazing bars across it (two over two)."""
    els = [bx(name + "StileW", (x1, y1, z1), (x1 + 1.25, y2, z2), "windowtrim"),
           bx(name + "StileE", (x2 - 1.25, y1, z1), (x2, y2, z2), "windowtrim"),
           bx(name + "RailB", (x1 + 1.25, y1, z1), (x2 - 1.25, y1 + 1.5, z2), "windowtrim", faces=("north", "south", "up", "down")),
           bx(name + "RailT", (x1 + 1.25, y2 - 1.25, z1), (x2 - 1.25, y2, z2), "windowtrim", faces=("north", "south", "up", "down"))]
    zc = (z1 + z2) / 2
    pane = bx(name + "Pane", (x1 + 1.25, y1 + 1.5, zc - 0.125), (x2 - 1.25, y2 - 1.25, zc + 0.125), glass, faces=("north", "south"),
              glow=glow, uv=[0, 0, 16, 16])
    els.append(flip_back(pane) if flip else pane)
    if bars:
        mx, my = (x1 + x2) / 2, (y1 + 1.5 + y2 - 1.25) / 2
        for side, (za, zb) in (("O", (z1 - 0.01 + 0.0, zc - 0.125)), ("I", (zc + 0.125, z2))):
            els += [bx(f"{name}Bar{side}V", (mx - 0.375, y1 + 1.5, za), (mx + 0.375, y2 - 1.25, zb), "windowtrim", faces=("north", "south", "east", "west")),
                    bx(f"{name}Bar{side}H", (x1 + 1.25, my - 0.375, za), (mx - 0.375, my + 0.375, zb), "windowtrim", faces=("north", "south", "up", "down")),
                    bx(f"{name}Bar{side}H2", (mx + 0.375, my - 0.375, za), (x2 - 1.25, my + 0.375, zb), "windowtrim", faces=("north", "south", "up", "down"))]
    return els


def window_model(width, kind, glow, state):
    """A window `width` blocks wide and two high (rel 2-3), facing north. kind: "sash", "shutter" or "picture"."""
    W, H = 16 * width, 32
    g = f"suburbglass-{state}"
    els = [
        # the opening's linings: its sides, head and the sill, trim in the opening and the house's plaster inside
        bx("LiningW", (0, 2, 0), (2, 30, 16), {"east": "windowtrim", "all": INSIDE}, faces=("east", "south")),
        bx("LiningE", (W - 2, 2, 0), (W, 30, 16), {"west": "windowtrim", "all": INSIDE}, faces=("west", "south")),
        bx("LiningHead", (0, 30, 0), (W, 32, 16), {"down": "windowtrim", "all": INSIDE}, faces=("down", "south")),
        bx("LiningSill", (0, 0, 0), (W, 2, 16), {"up": "windowtrim", "all": INSIDE}, faces=("up", "south")),
        # outside: the casing proud of the siding, a drip cap over its head, the sill
        bx("CasingW", (-0.5, 2, -0.75), (2.5, 30, 0), "windowtrim", faces=("north", "east", "west")),
        bx("CasingE", (W - 2.5, 2, -0.75), (W + 0.5, 30, 0), "windowtrim", faces=("north", "east", "west")),
        bx("CasingHead", (-1, 30, -1), (W + 1, 33, 0), "windowtrim", faces=("north", "east", "west", "down")),
        bx("DripCap", (-1.5, 33, -1.75), (W + 1.5, 33.75, 0), "windowtrim", faces=("north", "east", "west", "up", "down")),
        bx("Sill", (-1, 0, -2.25), (W + 1, 2, 0), "windowtrim", faces=("north", "east", "west", "up", "down")),
        # inside: a casing round the opening and the stool under it
        bx("InCasingW", (-0.5, 2, 16), (2, 31, 16.6), "windowtrim", faces=("south", "east", "west", "up")),
        bx("InCasingE", (W - 2, 2, 16), (W + 0.5, 31, 16.6), "windowtrim", faces=("south", "east", "west", "up")),
        bx("InCasingHead", (2, 30, 16), (W - 2, 31, 16.6), "windowtrim", faces=("south", "down")),
        bx("Stool", (-0.5, 1.25, 16), (W + 0.5, 2, 17.25), "windowtrim", faces=("south", "east", "west", "up", "down")),
    ]
    if kind in ("sash", "shutter"):
        # Double hung: the upper sash in the outer track, the lower in the inner, their meeting rails crossing
        els += _sash("Upper", 2, 14, 15.5, 30, 3, 4.5, g + "-c", glow)
        els += _sash("Lower", 2, 14, 2, 16.5, 4.5, 6, g + "-c", glow)
        if kind == "shutter":
            # Louvred shutters either side, held open against the wall, proud of it on their hinges
            for side, (a, b) in (("W", (-6, -0.75)), ("E", (W + 0.75, W + 6))):
                els += [bx(f"Shutter{side}StileA", (a, 2.5, -1.75), (a + 1, 29.5, -0.5), "shutterpaint"),
                        bx(f"Shutter{side}StileB", (b - 1, 2.5, -1.75), (b, 29.5, -0.5), "shutterpaint")]
                for k, (y1, y2) in enumerate(((2.5, 4), (15, 16.5), (28, 29.5))):
                    els.append(bx(f"Shutter{side}Rail{k}", (a + 1, y1, -1.75), (b - 1, y2, -0.5), "shutterpaint", faces=("north", "up", "down")))
                for k, (y1, y2) in enumerate(((4, 15), (16.5, 28))):
                    els.append(bx(f"Shutter{side}Louvre{k}", (a + 1, y1, -1.25), (b - 1, y2, -0.75), "shutterlouvre", faces=("north",)))
                for k, y in enumerate((6, 25)):
                    hx = -1.0 if side == "W" else W + 0.5
                    els.append(bx(f"Shutter{side}Hinge{k}", (hx, y, -2.0), (hx + 0.5, y + 1, -0.25), "metaldark",
                                  faces=("north", "up", "down", "east", "west")))
    else:
        # A picture window: a fixed light in the middle between two double-hung ones, mullions between
        for k, x in enumerate((16, 32)):
            els.append(bx(f"Mullion{k}", (x - 1, 2, -0.75), (x + 1, 30, 9), "windowtrim", faces=("north", "east", "west", "south")))
        els += _sash("WUpper", 2, 15, 15.5, 30, 3, 4.5, g + "-r", glow, flip=True)
        els += _sash("WLower", 2, 15, 2, 16.5, 4.5, 6, g + "-r", glow, flip=True)
        els += _sash("EUpper", 33, 46, 15.5, 30, 3, 4.5, g + "-l", glow, flip=True)
        els += _sash("ELower", 33, 46, 2, 16.5, 4.5, 6, g + "-l", glow, flip=True)
        els += _sash("Fixed", 17, 31, 2, 30, 4, 5.5, g + "-p", glow, bars=False)
    return els


WINDOW_PARTS = ["sashlower", "sashupper", "shutterlower", "shutterupper", "picwlower", "picmlower", "picelower",
                "picwupper", "picmupper", "piceupper"]


def windows():
    shape_by = {}
    for state in ("dark", "lit"):
        glow = 200 if state == "lit" else 0
        paths = {}
        for kind in ("sash", "shutter"):
            parts = cut(window_model(1, kind, glow, state), 1, 2)
            for r, half in enumerate(("lower", "upper")):
                paths[f"{kind}{half}"] = write_shape(f"window-{state}-{kind}{half}", parts[(0, r)], TEX)
        parts = cut(window_model(3, "picture", glow, state), 3, 2)
        for c, end in enumerate("wme"):
            for r, half in enumerate(("lower", "upper")):
                paths[f"pic{end}{half}"] = write_shape(f"window-{state}-pic{end}{half}", parts[(c, r)], TEX)
        for p in WINDOW_PARTS:
            for s in SIDES:
                shape_by[f"*-{state}-{p}-{s}"] = {"base": paths[p], "rotateY": ROTATE[s]}
    block("suburbwindow", {
        "variantgroups": [{"code": "glass", "states": ["dark", "lit"]}, {"code": "part", "states": WINDOW_PARTS},
                          {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-dark-sashlower-north", "*-dark-shutterlower-north", "*-dark-picmlower-north"],
                              "construction": ["*-dark-sashlower-north", "*-dark-shutterlower-north", "*-dark-picmlower-north"]},
        "blockmaterial": "Glass", "drawtype": "json", "shapeByType": shape_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 4, "drops": [],
        "lightHsvByType": {"*-lit-*": [6, 4, 9]}, "sounds": GLASS,
    }, "A Suburbs house's tall window (layout version 9): a sash window, the same with shutters, or a part of a picture window three wide")
    name("suburbwindow-lit-*", "Lit Window")
    name("suburbwindow-*", "Window")


# ---------------- Doors ----------------

def door_frame():
    """The doorway's linings, casing and threshold (the parts that stay when the door swings)."""
    return [
        bx("LiningW", (0, 0, 0), (1.25, 30.5, 16), {"east": "windowtrim", "all": INSIDE}, faces=("east", "south")),
        bx("LiningE", (14.75, 0, 0), (16, 30.5, 16), {"west": "windowtrim", "all": INSIDE}, faces=("west", "south")),
        bx("LiningHead", (0, 30.5, 0), (16, 32, 16), {"down": "windowtrim", "all": INSIDE}, faces=("down", "south")),
        bx("Threshold", (1.25, 0, 0), (14.75, 0.5, 16), "dresserwood", faces=("up", "north", "south")),
        bx("CasingW", (-1.5, 3, -0.75), (1.25, 30.5, 0), "windowtrim", faces=("north", "east", "west")),
        bx("CasingE", (14.75, 3, -0.75), (17.5, 30.5, 0), "windowtrim", faces=("north", "east", "west")),
        bx("PlinthW", (-1.75, 0, -1), (1.25, 3, 0), "windowtrim", faces=("north", "east", "west", "up")),
        bx("PlinthE", (14.75, 0, -1), (17.75, 3, 0), "windowtrim", faces=("north", "east", "west", "up")),
        bx("CasingHead", (-2, 30.5, -1), (18, 33.5, 0), "windowtrim", faces=("north", "east", "west", "down")),
        bx("DripCap", (-2.5, 33.5, -1.75), (18.5, 34.25, 0), "windowtrim", faces=("north", "east", "west", "up", "down")),
        bx("InCasingW", (-1, 0, 16), (1.25, 32.5, 16.6), "windowtrim", faces=("south", "east", "west", "up")),
        bx("InCasingE", (14.75, 0, 16), (17, 32.5, 16.6), "windowtrim", faces=("south", "east", "west", "up")),
        bx("InCasingHead", (1.25, 30.5, 16), (14.75, 32.5, 16.6), "windowtrim", faces=("south", "down")),
    ]


def door_leaf():
    """The leaf, shut, hinged at its west edge: six raised panels, the top two glazed, a brass knob and deadbolt on
    either face at its east edge, a kick plate outside, three hinges inside."""
    x1, x2, y1, y2, z1, z2 = 1.35, 14.65, 0.6, 30.4, 2.0, 3.75
    els = K.frame_and_panel("Leaf", (x1, y1, z1), (x2, y2, z2), "doorpaint", border=1.75, depth=0.5, grid=(2, 3), raised=0.5)
    openings = K.frame_and_panel.openings
    top = max(o[3] for o in openings)
    glazed = [i for i, o in enumerate(openings) if o[3] == top]
    els = [e for e in els if not any(e["name"] in (f"LeafPanel{i}", f"LeafField{i}", f"LeafFieldB{i}") for i in glazed)]
    for i in glazed:
        a, b, c, d = openings[i]
        els += K.inset_window(f"Lite{i}", a, b, c, d, z1, z2, "doorpaint", glass="suburbglass-dark-p")
    # the knob, its rose, the deadbolt over it, both faces
    for face, (za, zb, zc, zd) in (("O", (z1 - 0.5, z1, z1 - 2.0, z1 - 0.5)), ("I", (z2, z2 + 0.5, z2 + 0.5, z2 + 2.0))):
        els += [bx(f"Rose{face}", (12.0, 14.5, za), (13.5, 16.0, zb), "brass"),
                bx(f"Knob{face}", (12.25, 14.75, zc), (13.25, 15.75, zd), "brass"),
                bx(f"Bolt{face}", (12.25, 18.0, za), (13.25, 19.0, zb), "brass")]
    els.append(bx("Kick", (2.0, 0.75, z1 - 0.25), (14.0, 3.5, z1), "brass", faces=("north", "east", "west", "up", "down")))
    for k, y in enumerate((3.0, 14.0, 26.0)):
        els.append(bx(f"Hinge{k}", (1.35, y, z2), (2.35, y + 2.5, z2 + 0.25), "brass", faces=("south", "east", "up", "down")))
    return els


def door_open(leaf):
    """The leaf swung in a quarter turn on its hinges: lying against the west lining, its outside facing east."""
    turned = K.turn(leaf, 1)  # (north -> east, about the block's middle)
    # the hinge edge's inner corner (1.35, 3.75) goes to (16 - 3.75, 1.35) = (12.25, 1.35); put it back at the hinge,
    # standing clear of the lining by the depth of the leaf's raised fields
    return K.move(turned, dx=1.35 + 0.5 - 12.25, dz=3.75 - 1.35)


def doors():
    shape_by, coll_by = {}, {}
    closed = door_frame() + door_leaf()
    opened = door_frame() + door_open(door_leaf())
    for state, els in (("closed", closed), ("open", opened)):
        for hinge in ("w", "e"):
            model = els if hinge == "w" else mirror_x(els)
            parts = cut(model, 1, 2)
            for r, half in enumerate(("lower", "upper")):
                path = write_shape(f"door-{state}-{hinge}{half}", parts[(0, r)], TEX)
                for st in ((state, "locked") if state == "closed" else (state,)):
                    for s in SIDES:
                        shape_by[f"*-{st}-{hinge}-{half}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    # The leaf is what stops you: shut, across the doorway; open, along its hinge side
    for st in ("closed", "open", "locked"):
        for hinge in ("w", "e"):
            box = (0, 0, 2 / 16, 1, 1, 3.75 / 16) if st != "open" else (1.35 / 16, 0, 3.75 / 16, 4 / 16, 1, 1)
            if hinge == "e":
                box = (1 - box[3], box[1], box[2], 1 - box[0], box[4], box[5])
            for s in SIDES:
                coll_by[f"*-{st}-{hinge}-*-{s}"] = [cuboid(box, s)]
    block("suburbdoor", {
        "variantgroups": [{"code": "state", "states": ["closed", "open", "locked"]}, {"code": "hinge", "states": ["w", "e"]},
                          {"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-closed-w-lower-north"], "construction": ["*-closed-w-lower-north"]},
        "behaviors": [{"name": "BackroomsSuburbDoor"}],
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by,
        "collisionSelectionBoxesByType": coll_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 3, "drops": [],
        "sounds": WOOD,
    }, "A Suburbs house's front or back door (layout version 9): right-click to open or shut it; a locked one stays shut")
    name("suburbdoor-*", "Front Door")
    LANG["blockhelp-suburbdoor"] = "Open / close"
    LANG["suburbdoor-locked"] = "Locked. Nobody has been in since."


# ---------------- The cased garage door ----------------

def garage_model():
    """A sectional garage door three blocks wide and two high, set back in its opening, cased in trim."""
    W = 48
    els = [
        bx("LiningW", (0, 0, 0), (1.5, 30.5, 16), {"east": "windowtrim", "all": INSIDE}, faces=("east", "south")),
        bx("LiningE", (W - 1.5, 0, 0), (W, 30.5, 16), {"west": "windowtrim", "all": INSIDE}, faces=("west", "south")),
        bx("LiningHead", (0, 30.5, 0), (W, 32, 16), {"down": "windowtrim", "all": INSIDE}, faces=("down", "south")),
        bx("CasingW", (-2.5, 0, -1), (1.5, 30.5, 0), "windowtrim", faces=("north", "east", "west", "up")),
        bx("CasingE", (W - 1.5, 0, -1), (W + 2.5, 30.5, 0), "windowtrim", faces=("north", "east", "west", "up")),
        bx("CasingHead", (-3, 30.5, -1.25), (W + 3, 34.5, 0), "windowtrim", faces=("north", "east", "west", "down")),
        bx("DripCap", (-3.5, 34.5, -2), (W + 3.5, 35.25, 0), "windowtrim", faces=("north", "east", "west", "up", "down")),
        # the stops the door closes against, down its sides and across its head
        bx("StopW", (1.5, 0, 1.25), (2.25, 30.5, 2.5), "windowtrim", faces=("north", "east")),
        bx("StopE", (W - 2.25, 0, 1.25), (W - 1.5, 30.5, 2.5), "windowtrim", faces=("north", "west")),
        bx("StopHead", (2.25, 29.75, 1.25), (W - 2.25, 30.5, 2.5), "windowtrim", faces=("north", "down")),
        bx("Weatherstrip", (1.5, 0, 2.25), (W - 1.5, 0.6, 3.75), "rubber", faces=("north", "up", "south")),
        bx("Backer", (1.5, 0.6, 3.5), (W - 1.5, 30.5, 3.75), "garagegap", faces=("north", "south")),
    ]
    # Four sections, a narrow gap between each; the lower three with eight raised panels, the top with four lights
    rows = [(0.6, 8.0), (8.0, 15.5), (15.5, 23.0), (23.0, 30.5)]
    xa, xb = 1.5, W - 1.5
    for r, (y1, y2) in enumerate(rows):
        ya, yb = y1 + 0.15, y2 - 0.15
        if r < 3:
            els.append(bx(f"Section{r}", (xa, ya, 2.5), (xb, yb, 3.5), "garagepaint"))
            n, gap = 8, 0.9
            w = (xb - xa - gap * (n + 1)) / n
            for k in range(n):
                px1 = xa + gap + k * (w + gap)
                els.append(bx(f"Panel{r}x{k}", (px1, ya + 1.2, 2.0), (px1 + w, yb - 1.2, 2.5), "garagepaint", faces=("north", "east", "west", "up", "down")))
        else:
            n = 4
            lw = (xb - xa) / n
            els.append(bx(f"Section{r}RailB", (xa, ya, 2.5), (xb, ya + 1.5, 3.5), "garagepaint"))
            els.append(bx(f"Section{r}RailT", (xa, yb - 1.5, 2.5), (xb, yb, 3.5), "garagepaint"))
            for k in range(n + 1):
                sx = xa + k * lw
                s1, s2 = max(xa, sx - 1.0), min(xb, sx + 1.0)
                els.append(bx(f"Section{r}Stile{k}", (s1, ya + 1.5, 2.5), (s2, yb - 1.5, 3.5), "garagepaint", faces=("north", "south", "east", "west")))
            for k in range(n):
                l1, l2 = xa + k * lw + 1.0, xa + (k + 1) * lw - 1.0
                els.append(bx(f"Lite{k}", (l1, ya + 1.5, 3.0), (l2, yb - 1.5, 3.25), "suburbglass-dark-p", faces=("north", "south"), uv=[0, 0, 16, 16]))
    els += [bx("HandleBase", (22.5, 3.0, 1.6), (25.5, 4.0, 2.0), "metaldark", faces=("north", "up", "down", "east", "west")),
            bx("Handle", (22.75, 2.25, 0.8), (25.25, 2.75, 1.6), "metaldark", faces=("north", "up", "down", "east", "west"))]
    return els


GARAGE_PARTS = ["lowerw", "lowerm", "lowere", "upperw", "upperm", "uppere"]


def garage():
    parts = cut(garage_model(), 3, 2)
    shape_by = {}
    for r, half in enumerate(("lower", "upper")):
        for c, end in enumerate("wme"):
            path = write_shape(f"garage-{half}{end}", parts[(c, r)], TEX)
            for s in SIDES:
                shape_by[f"*-{half}{end}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("garagedoorcased", {
        "variantgroups": [{"code": "part", "states": GARAGE_PARTS}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-lowerm-north"], "construction": ["*-lowerm-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shape_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 99, "resistance": 4, "drops": [],
        "sounds": {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
    }, "A Suburbs house's garage door (layout version 9): sectional, set back in its opening and cased in trim; shut for good")
    name("garagedoorcased-*", "Garage Door")


# ---------------- The chimney's cap ----------------

def chimney_cap(joined):
    """The top of a brick chimney stack: a corbelled course, a poured crown with a wash, and a terracotta flue pot. With
    `joined` the stack's other half lies to the north, so nothing overhangs that side."""
    n = 0 if joined else 1  # how far the corbel and crown reach past the north face
    els = [bx("Brick", (0, 0, 0), (16, 5, 16), "siding-brick", faces=("north", "east", "south", "west") if not joined else ("east", "south", "west")),
           bx("Corbel", (-0.75, 5, -0.75 * n), (16.75, 7, 16.75), "siding-brick", faces=("north", "east", "south", "west", "down") if not joined else ("east", "south", "west", "down")),
           bx("Crown", (-1.25, 7, -1.25 * n), (17.25, 8.5, 17.25), "chimneycrown", faces=("north", "east", "south", "west", "up", "down") if not joined else ("east", "south", "west", "up", "down")),
           bx("Wash", (1, 8.5, 1 if not joined else 0), (15, 9.25, 15), "chimneycrown", faces=("north", "east", "south", "west", "up") if not joined else ("east", "south", "west", "up")),
           bx("PotA", (5.5, 9.25, 6.5), (10.5, 15, 9.5), "fluepot", faces=("north", "east", "south", "west")),
           bx("PotB", (6.5, 9.25, 5.5), (9.5, 15, 10.5), "fluepot", faces=("north", "east", "south", "west")),
           bx("Rim", (5.75, 15, 5.75), (10.25, 16, 10.25), "fluepot", faces=("north", "east", "south", "west", "down")),
           bx("Throat", (6.5, 15.5, 6.5), (9.5, 16, 9.5), "fluethroat", faces=("up",)),
           bx("RimTop", (5.75, 16, 5.75), (10.25, 16.25, 6.5), "fluepot", faces=("up", "north", "east", "west")),
           bx("RimTopS", (5.75, 16, 9.5), (10.25, 16.25, 10.25), "fluepot", faces=("up", "south", "east", "west")),
           bx("RimTopW", (5.75, 16, 6.5), (6.5, 16.25, 9.5), "fluepot", faces=("up", "west")),
           bx("RimTopE", (9.5, 16, 6.5), (10.25, 16.25, 9.5), "fluepot", faces=("up", "east"))]
    return els


def chimney():
    alone = write_shape("chimneycap-none", chimney_cap(False), TEX)
    joined = write_shape("chimneycap-joined", chimney_cap(True), TEX)
    shape_by = {"*-none": {"base": alone}}
    for s in SIDES:
        shape_by[f"*-{s}"] = {"base": joined, "rotateY": ROTATE[s]}
    block("chimneycap", {
        "variantgroups": [{"code": "join", "states": ["none"] + SIDES}],
        "creativeinventory": {"general": ["*-none"], "construction": ["*-none"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": shape_by,
        "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.6, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 4, "sounds": STONE,
    }, "The cap on a Suburbs house's brick chimney stack (layout version 9): a corbelled course, a crown and a flue pot; join: the side its stack's other half is on")
    name("chimneycap-*", "Chimney")


# ---------------- The stairs' balustrade ----------------

def stair_steps():
    """The house stairs' wooden step with its carpet runner, climbing north (as gen_deep's housestairs)."""
    return [bx("Lower", (0, 0, 0), (16, 8, 16), "housefloor-wood"), bx("Upper", (0, 8, 0), (16, 16, 8), "housefloor-wood"),
            bx("RunLower", (4, 8, 8), (12, 8.3, 16), "housefloor-carpet", faces=("up", "east", "west")),
            bx("RunRiser", (4, 8.3, 8), (12, 16, 8.3), "housefloor-carpet", faces=("south", "east", "west")),
            bx("RunUpper", (4, 16, 0), (12, 16.3, 8), "housefloor-carpet", faces=("up", "east", "west", "south")),
            bx("RunFoot", (4, 0, 16), (12, 8.3, 16.3), "housefloor-carpet", faces=("south", "east", "west", "up"))]


def stair_rail(foot):
    """A step with a balustrade along its west side: a turned spindle on each tread, a handrail at 14 above the
    nosings on the stairs' pitch, and on the first step a newel post that the handrail starts from."""
    els = stair_steps()
    els += [bx("SpindleA", (0.5, 8, 11.5), (1.5, 18.75, 12.5), "windowtrim", faces=("north", "east", "south", "west")),
            bx("SpindleB", (0.5, 16, 3.5), (1.5, 26.75, 4.5), "windowtrim", faces=("north", "east", "south", "west"))]
    # the handrail's line: 14 over the nosings (y = 30 - z), from the step's south edge, or from the newel's face
    z_lo = 12.75 if foot else 16.0
    length = z_lo * math.sqrt(2)
    zc, yc = z_lo / 2, 30 - z_lo / 2
    rail = bx("Handrail", (0.25, yc - 0.75, zc - length / 2), (1.75, yc + 0.75, zc + length / 2), "dresserwood")
    rail["rotationOrigin"] = [1.0, yc, zc]
    rail["rotationX"] = 45
    els.append(rail)
    if foot:
        els += [bx("Newel", (0.1, 8, 12.75), (2.9, 19.5, 15.25), "windowtrim", faces=("north", "east", "south", "west")),
                bx("NewelCap", (0.05, 19.5, 12.5), (3.2, 21, 15.5), "dresserwood")]
    return els


def stairs():
    shape_by, coll_by = {}, {}
    base = [(0, 0, 0, 1, 0.5, 1), (0, 0.5, 0, 1, 1, 0.5)]
    for part in ("foot", "flight"):
        for end in ("w", "e"):
            els = stair_rail(part == "foot")
            path = write_shape(f"stairsrail-{part}-{end}", els if end == "w" else mirror_x(els), TEX)
            rail = (0, 0, 0, 0.125, 1.5, 1) if end == "w" else (0.875, 0, 0, 1, 1.5, 1)
            for s in SIDES:
                shape_by[f"*-{part}-{end}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
                coll_by[f"*-{part}-{end}-{s}"] = [cuboid(b, s) for b in base + [rail]]
    block("housestairsrail", {
        "variantgroups": [{"code": "part", "states": ["foot", "flight"]}, {"code": "end", "states": ["w", "e"]},
                          {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-foot-w-north", "*-flight-w-north"], "construction": ["*-foot-w-north", "*-flight-w-north"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by, "collisionSelectionBoxesByType": coll_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 4, "sounds": WOOD,
    }, "A Suburbs house's stairs with a balustrade on the open side (layout version 9): the variant the way they climb, end the side the balustrade is on as modelled climbing north")
    name("housestairsrail-*", "Stairs")


def generate():
    textures()
    windows()
    doors()
    garage()
    chimney()
    stairs()
