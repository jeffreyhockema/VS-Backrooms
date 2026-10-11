"""Level 974, Kitty's House: every asset (docs/new-levels/974-plan.md section 5).

    bash tools/locked.sh run python tools/gen_974.py

Writes textures (block/974/, item/974/), shapes (block/974/, item/974/, entity/974/), block types (blocktypes/974/),
item types (itemtypes/974/), Kitty (entities/974/), the sounds (sounds/ambient/974/, sounds/creature/974/), the
patch marking vanilla flowers and seashells cute (patches/l974-cute.json) and the level's lang keys (merged into
lang/en.json in place, next to the level's other keys; nothing else in that file is touched).

Conventions as in detail_kit.py: boxes in block space (0-16), props modelled with their front facing north (-Z),
wall decorations sticking out of the north face of a wall block; variants turn them with rotateY
(north 0, east 270, south 180, west 90). Real 3D detail: mouldings, frames, knobs, curtains and plush toys are boxes.
"""
import itertools
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from detail_kit import bx, turn, shift  # noqa: E402

import gen_974_tex  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90, "n": 0, "e": 270, "s": 180, "w": 90, "ns": 0, "we": 90}
ALL = ("north", "east", "south", "west", "up", "down")

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
CERAMIC = {"walk": "game:walk/stone*", "place": "game:block/ceramicplace", "break": "game:block/ceramicbreak", "hit": "game:block/ceramichit"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}

PLANK, STICK, NAILS, CLOTHI = "game:plank-aged", "game:stick", "game:metalnailsandstrips-iron", "game:cloth-plain"

LANG = {}
COUNT = {"blocktypes": 0, "shapes": 0, "variants": 0}


# ======================================================================== Files

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def tpath(key):
    return key if ":" in key else f"backrooms:block/974/{key}"


_written_shapes = {}


def shape(name, elements, folder="block/974"):
    """Writes a block (or item) shape; textures are named by their key in block/974/ unless the key is a path."""
    keys = sorted({face["texture"][1:] for e in _flat(elements) for face in e["faces"].values()})
    textures = {}
    for k in keys:
        textures[k] = tpath(k) if not k.startswith("item.") else f"backrooms:item/974/{k[5:]}"
    data = {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", *folder.split("/"), name + ".json"), data)
    COUNT["shapes"] += 1
    return f"backrooms:{folder}/{name}"


def _flat(els):
    for e in els:
        yield e
        yield from _flat(e.get("children", []))


def block(code, data, comment=None):
    write_json(os.path.join(ASSETS, "blocktypes", "974", code + ".json"), dict({"code": code}, **data), comment)
    COUNT["blocktypes"] += 1


def drops(*items):
    out = []
    for code, avg, var in items:
        kind = "item"
        if code.startswith("block:"):
            kind, code = "block", code[6:]
        out.append({"type": kind, "code": code, "quantity": {"avg": avg, "var": var}})
    return out


def cuboid(box, angle=0):
    x1, y1, z1, x2, y2, z2 = box
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if angle:
        c["rotateY"] = angle
    return c


# ======================================================================== A generic block with variant groups

def variants_block(code, english, groups, build, rot=None, box=None, boxes=None, collide=True, data=None, comment=None,
                   names=None, creative=None, rot_offset=0):
    """A block type over every combination of `groups` [(group, states)]. build(v) returns the elements for a
    variant (a dict group -> state), modelled unturned; the group named `rot` turns it (ROTATE of its state, plus
    rot_offset). `box` is the collision/selection box for the unturned model (or build-dependent via `boxes(v)`)."""
    combos = list(itertools.product(*[states for _, states in groups])) if groups else [()]
    shapes, sel = {}, {}
    cache = {}
    for combo in combos:
        v = dict(zip([g for g, _ in groups], combo))
        key = tuple(s for (g, _), s in zip(groups, combo) if g != rot)
        if key not in cache:
            els = build(v)
            nm = code + ("-" + "-".join(key) if key else "")
            cache[key] = shape(nm, els)
        full = code + ("-" + "-".join(combo) if combo else "")
        angle = ((ROTATE[v[rot]] if rot else 0) + rot_offset) % 360
        shapes[full] = {"base": cache[key], "rotateY": angle} if angle else {"base": cache[key]}
        b = boxes(v) if boxes else box
        if b is not None:
            sel[full] = cuboid(b, angle)
    COUNT["variants"] += len(combos)
    out = {}
    if groups:
        out["variantgroups"] = [{"code": g, "states": list(s)} for g, s in groups]
    if len(shapes) == 1:
        out["shape"] = next(iter(shapes.values()))
    else:
        out["shapeByType"] = shapes
    first = code + ("-" + "-".join(c[0] for _, c in groups) if groups else "")
    out["creativeinventory"] = creative or {"general": [first], "backrooms": [first]}
    out.update({"blockmaterial": "Wood", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                "lightAbsorption": 0, "resistance": 1.5, "sounds": WOOD})
    if sel:
        if len(set(json.dumps(s, sort_keys=True) for s in sel.values())) == 1:
            one = next(iter(sel.values()))
            out["selectionbox"] = one
            if collide:
                out["collisionbox"] = one
        else:
            out["selectionboxByType"] = sel
            if collide:
                out["collisionboxByType"] = sel
    if not collide:
        out["collisionbox"] = None
    if data:
        out.update(data)
    block(code, out, comment or english)
    if names:
        for pat, eng in names.items():
            LANG["block-" + pat] = eng
    LANG.setdefault(f"block-{code}-*" if groups else f"block-{code}", english)


# ======================================================================== Pieces

def cube(tex, down=None):
    c = bx("Wall", (0, 0, 0), (16, 16, 16), tex)
    if down:
        c["faces"]["down"]["texture"] = "#" + down
    return c


def four(els):
    """Copies boxes on the north face onto all four faces."""
    out = []
    for i in range(4):
        for e in els:
            t = turn(e, i)
            t["name"] = f"{e['name']}{i}"
            out.append(t)
    return out


def baseboard():
    return [bx("Base", (0, 0, -1), (16, 5, 0), "trim", faces=("north", "up", "east", "west")),
            bx("Shoe", (0, 0, -1.5), (16, 0.8, -1), "trim", faces=("north", "up", "east", "west"))]


def crown():
    return [bx("Crown", (0, 13, -1), (16, 16, 0), "trim", faces=("north", "down", "east", "west")),
            bx("Cove", (0, 14.6, -2), (16, 16, -1), "trim", faces=("north", "down", "east", "west"))]


def rail():
    return [bx("Rail", (0, 7.4, -0.8), (16, 9, 0), "knob-pink", faces=("north", "up", "down", "east", "west"))]


def wall_with(kind):
    """The wall cube for a decoration's height: plain paint, baseboard (rel 1), crown (rel 4), bath tile with its rail."""
    if kind == "base":
        return [cube("paint-1")] + four(baseboard())
    if kind == "crown":
        return [cube("paint-1")] + four(crown())
    if kind == "bathtilecap":
        return [cube("bathtile")] + four(rail())
    return [cube("paint-1")]


def hang(els):
    """A wall hanging modelled on the north face of a wall (z < 0) moved into the room-side block: it then sits
    against that block's south side and faces north (the suffix is the way it faces, as the level's code expects)."""
    return shift(els, dz=16)


HUNG = {"blockmaterial": "Wood", "lightAbsorption": 0, "resistance": 1.5, "sidesolid": {"all": False}, "sideopaque": {"all": False}}


def cyl(name, cx, cz, r, y1, y2, tex, glow=0):
    """A rough round post: a cross of two boxes."""
    return [bx(name, (cx - r, y1, cz - r * 0.62), (cx + r, y2, cz + r * 0.62), tex, glow),
            bx(name + "b", (cx - r * 0.62, y1, cz - r), (cx + r * 0.62, y2, cz + r), tex, glow)]


def picture(el, tex, face="north", glow=0):
    """Stretches a whole texture over one face of a box."""
    el["faces"][face] = {"texture": "#" + tex, "uv": [0, 0, 16, 16]}
    if glow:
        el["faces"][face]["glow"] = glow
    return el


def mirror_x(els):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [16 - x2, y1, z1], [16 - x1, y2, z2]
        f = e["faces"]
        if "east" in f or "west" in f:
            east, west = f.pop("east", None), f.pop("west", None)
            if west is not None:
                f["east"] = west
            if east is not None:
                f["west"] = east
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [16 - o[0], o[1], o[2]]
            if "rotationY" in e:
                e["rotationY"] = -e["rotationY"]
            if "rotationZ" in e:
                e["rotationZ"] = -e["rotationZ"]
        out.append(e)
    return out


def scale_els(els, s, at=(8, 0, 8), roty=0):
    """Scales boxes modelled round (0, 0, 0) and moves them to `at`; roty turns the group about its own centre."""
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["from"] = [at[i] + e["from"][i] * s for i in range(3)]
        e["to"] = [at[i] + e["to"][i] * s for i in range(3)]
        for f in e["faces"].values():
            if f.get("uv") and f["uv"] != [0, 0, 16, 16]:
                f["uv"] = [round(min(16, v * s), 3) for v in f["uv"]]
        if "rotationOrigin" in e:
            e["rotationOrigin"] = [at[i] + e["rotationOrigin"][i] * s for i in range(3)]
        elif roty:
            e["rotationOrigin"] = list(at)
        if roty and "rotationZ" not in e and "rotationX" not in e:
            e["rotationOrigin"] = list(at)
            e["rotationY"] = roty
        out.append(e)
    return out


# ======================================================================== Plush mascots (modelled facing north, round x=z=0, feet at y=0)

def plush(kind, colour="grey"):
    fur, face = f"fur-{colour}", f"face-{colour}"
    if kind == "cat":
        head = picture(bx("Head", (-3, 3.2, -2.5), (3, 8.4, 2.5), fur), face)
        return [bx("Body", (-2.4, 0, -1.9), (2.4, 3.6, 2.1), fur), head,
                bx("EarL", (-2.8, 8.4, -0.6), (-1.2, 9.8, 0.6), fur), bx("EarR", (1.2, 8.4, -0.6), (2.8, 9.8, 0.6), fur),
                bx("EarLin", (-2.5, 8.4, -0.75), (-1.5, 9.4, -0.6), "fur-earpink", faces=("north",)),
                bx("EarRin", (1.5, 8.4, -0.75), (2.5, 9.4, -0.6), "fur-earpink", faces=("north",)),
                bx("PawL", (-2.0, 0, -2.6), (-0.6, 1.2, -1.6), fur), bx("PawR", (0.6, 0, -2.6), (2.0, 1.2, -1.6), fur),
                bx("Tail", (2.2, 0.4, 1.0), (3.2, 3.4, 2.0), fur), bx("TailTip", (2.6, 3.4, 1.1), (3.6, 4.4, 1.9), fur)]
    if kind == "bunny":
        head = picture(bx("Head", (-2.6, 3.2, -2.3), (2.6, 7.8, 2.3), fur), face)
        return [bx("Body", (-2.2, 0, -1.8), (2.2, 3.6, 2.0), fur), head,
                bx("EarL", (-2.0, 7.6, -0.5), (-0.8, 11.6, 0.5), fur), bx("EarR", (0.8, 7.6, -0.5), (2.0, 11.6, 0.5), fur),
                bx("EarLin", (-1.7, 8.2, -0.65), (-1.1, 11, -0.5), "fur-earpink", faces=("north",)),
                bx("EarRin", (1.1, 8.2, -0.65), (1.7, 11, -0.5), "fur-earpink", faces=("north",)),
                bx("Berry", (-1.1, 1.0, -2.9), (1.1, 3.0, -1.7), "fur-berry"), bx("BerryLeaf", (-0.8, 3.0, -2.7), (0.8, 3.5, -1.9), "fur-leaf"),
                bx("PawL", (-2.0, 1.6, -2.3), (-0.9, 2.6, -1.4), fur), bx("PawR", (0.9, 1.6, -2.3), (2.0, 2.6, -1.4), fur),
                bx("Tail", (-0.8, 0.6, 2.0), (0.8, 2.2, 2.8), "fur-white")]
    if kind == "bear":
        head = picture(bx("Head", (-2.8, 3.4, -2.4), (2.8, 8.2, 2.4), fur), face)
        return [bx("Body", (-2.5, 0, -2.0), (2.5, 3.8, 2.2), fur), head,
                bx("EarL", (-3.0, 7.4, -0.6), (-1.5, 9.0, 0.6), fur), bx("EarR", (1.5, 7.4, -0.6), (3.0, 9.0, 0.6), fur),
                bx("ArmL", (-3.4, 1.0, -1.0), (-2.4, 3.4, 0.6), fur), bx("ArmR", (2.4, 1.0, -1.0), (3.4, 3.4, 0.6), fur),
                bx("LegL", (-2.4, 0, -3.0), (-0.8, 1.4, -1.8), fur), bx("LegR", (0.8, 0, -3.0), (2.4, 1.4, -1.8), fur),
                bx("Tummy", (-1.4, 0.8, -2.2), (1.4, 3.0, -2.0), "fur-muzzle", faces=("north",))]
    # A smiling star, standing on two of its points
    body = picture(bx("Body", (-2.2, 2.2, -1.1), (2.2, 6.2, 1.1), fur), face)
    arms = []
    for i, a in enumerate((0, 72, 144, -144, -72)):
        arms.append(bx(f"Arm{i}", (-1.3, 5.0, -0.9), (1.3, 9.0, 0.9), fur, rot=(0, 0, a), origin=(0, 4.2, 0)))
    return [body] + arms


# ======================================================================== Structure

def structure():
    # Walls: plain paint (two alternates), baseboard, crown, kitchen backsplash, bath tile with and without its rail
    kinds = ["plain", "base", "crown", "backsplash", "bathtile", "bathtilecap"]

    def build(v):
        k = v["kind"]
        if k == "plain":
            return [cube("paint-1")]
        if k == "bathtile":
            return [cube("bathtile")]
        if k == "backsplash":
            return [cube("backsplash")] + four([bx("Bullnose", (0, 11.2, -0.7), (16, 12.4, 0), "trim", faces=("north", "up", "down", "east", "west"))])
        return wall_with(k)

    variants_block("l974-wall", "Pink Wall", [("kind", kinds)], build, data={
        "blockmaterial": "Stone", "sounds": STONE, "lightAbsorption": 99, "resistance": 6, "sidesolid": {"all": True},
        "sideopaque": {"all": True}, "drops": [],
        "drawtypeByType": {"l974-wall-plain": "cube", "l974-wall-bathtile": "cube", "*": "json"},
        "texturesByType": {"l974-wall-plain": {"all": {"base": "block/974/paint-1", "alternates": [{"base": "block/974/paint-2"}]}},
                           "l974-wall-bathtile": {"all": {"base": "block/974/bathtile"}}},
        "attributes": {"l974structure": True},
    }, comment="Level 974: Baker-Miller pink walls, with white baseboards and crown moulding, a subway-tile backsplash, mint bath tile with a pink rail",
        names={"l974-wall-*": "Pink Wall", "l974-wall-backsplash": "Pink Wall with Tile Backsplash",
               "l974-wall-bathtile": "Bathroom Tile", "l974-wall-bathtilecap": "Bathroom Tile with Rail"})

    # Floors and ceiling: plain cubes
    block("l974-floor", {
        "variantgroups": [{"code": "kind", "states": ["carpet", "checker", "bathhex"]}],
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Stone", "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [],
        "texturesByType": {
            "l974-floor-carpet": {"all": {"base": "block/974/carpet", "alternates": [{"base": "block/974/carpet", "rotation": r} for r in (90, 180, 270)]}},
            "l974-floor-checker": {"all": {"base": "block/974/checker"}},
            "l974-floor-bathhex": {"all": {"base": "block/974/bathhex"}},
        },
        "soundsByType": {"l974-floor-carpet": CLOTH, "*": STONE},
        "attributes": {"l974structure": True},
    }, "Level 974: blush carpet, the kitchen's pink-and-white checker, white hexagon bath tile")
    LANG.update({"block-l974-floor-carpet": "Carpet", "block-l974-floor-checker": "Checkered Floor", "block-l974-floor-bathhex": "Bathroom Tile"})
    block("l974-ceiling", {
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Stone", "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": STONE,
        "textures": {"all": {"base": "block/974/ceiling"}}, "attributes": {"l974structure": True},
    }, "Level 974: flat white plaster ceiling")
    LANG["block-l974-ceiling"] = "Ceiling"

    # The attic slope over the bed alcove: a smooth 45-degree plane, low edge toward the state's side (n: north)
    def slope(v):
        els = [bx("Plane", (0, 7.5, -3.314), (16, 8.5, 19.314), "paint-1", rot=(-45, 0, 0), origin=(8, 8, 8))]
        for i in range(8):
            els.append(bx(f"Step{i}", (0, 2 * i + 1.5, 2 * i), (16, 16, 2 * i + 2), "paint-1", faces=("east", "west", "up")))
        els.append(bx("Crown", (0, 0, -0.9), (16, 1.6, 0.9), "trim", faces=("north", "up", "down", "east", "west"), rot=(-45, 0, 0), origin=(8, 0.8, 0)))
        return els

    variants_block("l974-slope", "Sloped Ceiling", [("side", SIDES)], slope, rot="side", data={
        "blockmaterial": "Stone", "sounds": STONE, "lightAbsorption": 99, "resistance": 6, "drops": [], "sidesolid": {"all": False},
        "collisionSelectionBoxesByType": {f"l974-slope-{s}": [cuboid((0, 0.5, 0, 1, 1, 1), ROTATE[s]), cuboid((0, 0, 0, 1, 0.5, 0.5), ROTATE[s])] for s in SIDES},
        "attributes": {"l974structure": True},
    }, comment="Level 974: the attic slope over the bed alcove (the suffix is the side it descends toward: its low edge)")

    # Lintels over doorways (rel 4): a crown wall with a white header on both faces and a white soffit
    def lintel(v):
        head = bx("Header", (-2.5, 0, -1.7), (18.5, 3, 0), "trim", faces=("north", "down", "up", "east", "west"))
        return [cube("paint-1", down="trim")] + four(crown()) + [head, dict(turn(head, 2), name="Header2")]

    variants_block("l974-lintel", "Doorway Lintel", [("axis", ["ns", "we"])], lintel,
                   rot="axis", data={"blockmaterial": "Stone", "sounds": STONE, "lightAbsorption": 99, "resistance": 6, "drops": [],
                                     "sidesolid": {"all": True}, "sideopaque": {"all": False}, "attributes": {"l974structure": True}},
                   comment="Level 974: over a doorway (ns: the opening passes north-south), white header boards on both faces")

    # Door casings (rel 1-3 in each doorway): jamb liners and architraves on both faces; no collision
    def jamb(west=True):
        els = [bx("Liner", (0, 0, 0), (0.75, 16, 16), "trim", faces=("east",)),
               bx("ArchN", (-2.5, 0, -1.7), (1.5, 16, 0), "trim", faces=("north", "east", "west")),
               bx("ArchS", (-2.5, 0, 16), (1.5, 16, 17.7), "trim", faces=("south", "east", "west"))]
        return els if west else mirror_x(els)

    variants_block("l974-casing", "Door Casing", [("axis", ["ns", "we"])], lambda v: jamb(True) + jamb(False), rot="axis", box=(0, 0, 0, 1, 1, 1), collide=False,
                   data={"drops": [], "resistance": 6, "attributes": {"l974structure": True}},
                   comment="Level 974: a doorway's white casing (ns: the opening passes north-south); walk through it")
    # Windows: 2 x 2 blocks at rel 2-3, each quadrant (as seen from the room: bl, br, tl, tr) a wall block with the
    # window in its north face; behind the glass a painting of a sky.
    paintings = ["clouds", "hills", "rainbow", "sunset"]

    def window(v):
        q, paint_kind = v["part"], v["painting"]
        left = q[1] == "l"           # seen from the room (looking south), left is +x
        bottom = q[0] == "b"
        ox0, ox1 = (0, 12) if left else (4, 16)
        oy0, oy1 = (4, 16) if bottom else (0, 12)
        body = bx("Body", (0, 0, 3), (16, 16, 16), "paint-1", faces=("north", "east", "south", "west", "up", "down"))
        picture(body, f"painting-{paint_kind}-{q}", glow=40)
        els = [body]
        # The wall round the opening, its reveals in the opening
        if left:
            els.append(bx("SurrSide", (12, 0, 0), (16, 16, 3), "paint-1", faces=("north", "west", "east", "up", "down")))
        else:
            els.append(bx("SurrSide", (0, 0, 0), (4, 16, 3), "paint-1", faces=("north", "east", "west", "up", "down")))
        if bottom:
            els.append(bx("SurrEnd", (ox0, 0, 0), (ox1, 4, 3), "paint-1", faces=("north", "up")))
        else:
            els.append(bx("SurrEnd", (ox0, 12, 0), (ox1, 16, 3), "paint-1", faces=("north", "down")))
        # The white frame (2 px), the mullion and the transom where the quadrants meet
        if left:
            els.append(bx("FrameSide", (10, oy0, 0.4), (12, oy1, 3), "trim", faces=("north", "west", "up", "down")))
            els.append(bx("Mullion", (0, oy0, 0.8), (1, oy1, 3), "trim", faces=("north", "east")))
        else:
            els.append(bx("FrameSide", (4, oy0, 0.4), (6, oy1, 3), "trim", faces=("north", "east", "up", "down")))
            els.append(bx("Mullion", (15, oy0, 0.8), (16, oy1, 3), "trim", faces=("north", "west")))
        if bottom:
            els.append(bx("FrameEnd", (ox0, 4, 0.4), (ox1, 6, 3), "trim", faces=("north", "up")))
            els.append(bx("Transom", (ox0, 15, 0.8), (ox1, 16, 3), "trim", faces=("north", "down")))
        else:
            els.append(bx("FrameEnd", (ox0, 10, 0.4), (ox1, 12, 3), "trim", faces=("north", "down")))
            els.append(bx("Transom", (ox0, 0, 0.8), (ox1, 1, 3), "trim", faces=("north", "up")))
        els.append(picture(bx("Glass", (ox0, oy0, 1.8), (ox1, oy1, 1.85), "glass", faces=("north",)), "glass"))
        # Curtains, sheer, gathered at the outer edge; a cream bow ties them at the bottom of the top quadrant.
        # Modelled for a left quadrant (outer edge at x 16) and mirrored for the right.
        cur = []
        if bottom:
            cur += [bx("Curtain1", (13.6, 11.0, -1.8), (17, 16, -0.6), "curtain"),
                    bx("Curtain2", (12.8, 7.0, -1.9), (17, 11.0, -0.6), "curtain"),
                    bx("Curtain3", (12.0, 4.4, -2.0), (17, 7.0, -0.6), "curtain")]
            # The sill, a little apron under it, and a pastel pony figurine standing on it
            cur += [bx("Sill", (-0.01, 2.6, -3.0), (17.5, 4.1, 0.4), "trim", faces=("north", "up", "down", "east", "west")),
                    bx("Apron", (0, 1.2, -1.2), (17, 2.6, 0), "trim", faces=("north", "down", "east", "west"))]
            pc = "fur-lilac" if q == "bl" else "fur-mint"
            px0 = 4.0
            cur += [bx("PonyBody", (px0, 5.0, -2.2), (px0 + 3.2, 6.6, -1.0), pc), bx("PonyHead", (px0 - 1.0, 6.2, -2.3), (px0 + 0.6, 7.8, -0.9), pc),
                    bx("PonyMane", (px0 - 0.2, 6.4, -2.0), (px0 + 0.8, 8.0, -1.2), "fur-pink"),
                    bx("PonyTail", (px0 + 3.2, 5.0, -1.9), (px0 + 4.0, 6.6, -1.3), "fur-pink"),
                    bx("PonyLeg1", (px0 + 0.2, 4.1, -2.1), (px0 + 0.8, 5.0, -1.6), pc), bx("PonyLeg2", (px0 + 2.4, 4.1, -2.1), (px0 + 3.0, 5.0, -1.6), pc),
                    bx("PonyLeg3", (px0 + 0.2, 4.1, -1.6), (px0 + 0.8, 5.0, -1.1), pc), bx("PonyLeg4", (px0 + 2.4, 4.1, -1.6), (px0 + 3.0, 5.0, -1.1), pc)]
        else:
            cur += [bx("Curtain1", (11.4, 8.0, -1.8), (17, 13.0, -0.6), "curtain"),
                    bx("Curtain2", (12.6, 4.0, -1.8), (17, 8.0, -0.6), "curtain"),
                    bx("Curtain3", (13.6, 0, -1.8), (17, 4.0, -0.6), "curtain"),
                    bx("Bow", (13.2, 1.0, -2.5), (15.8, 2.6, -1.7), "ribbon"),
                    bx("BowLoopA", (11.9, 1.4, -2.4), (13.3, 3.0, -1.9), "ribbon", rot=(0, 0, 20), origin=(13.2, 1.8, -2.1)),
                    bx("BowLoopB", (15.7, 1.4, -2.4), (17.1, 3.0, -1.9), "ribbon", rot=(0, 0, -20), origin=(15.8, 1.8, -2.1)),
                    bx("BowTail", (13.8, -1.8, -2.3), (14.5, 1.0, -1.9), "ribbon", rot=(0, 0, 10), origin=(14.1, 1.0, -2.1)),
                    bx("Valance", (-0.01, 12.4, -2.4), (17.4, 16, -0.3), "valance", faces=("north", "down", "east", "west", "up"))]
            for i in range(5):
                x = 0.6 + i * 3.4
                cur.append(bx(f"Scallop{i}", (x, 11.6, -2.3), (x + 2.2, 12.4, -0.4), "valance", faces=("north", "down", "east", "west")))
        els += cur if left else mirror_x(cur)
        return els

    variants_block("l974-window", "Window", [("part", ["bl", "br", "tl", "tr"]), ("painting", paintings), ("side", SIDES)], window, rot="side",
                   data={"blockmaterial": "Stone", "sounds": STONE, "lightAbsorption": 99, "resistance": 6, "drops": [],
                         "sidesolid": {"all": True}, "attributes": {"l974structure": True}},
                   comment="Level 974: a 2 x 2 window in a wall (part as seen from the room; side = the way it faces). Behind the glass is a painting of a sky")

# ======================================================================== Lights

def lights():
    def downlight(v):
        on = v["state"] == "on"
        lens = "lens" if on else "lens-off"
        g = 255 if on else 0
        return [cube("ceiling"),
                bx("Ring", (4, -0.5, 5.2), (12, 0, 10.8), "trim", faces=("north", "east", "south", "west", "down")),
                bx("Ring2", (5.2, -0.5, 4), (10.8, 0, 12), "trim", faces=("north", "east", "south", "west", "down")),
                bx("Lens", (5.2, -1, 6.2), (10.8, -0.5, 9.8), lens, glow=g, faces=("north", "east", "south", "west", "down")),
                bx("Lens2", (6.2, -1, 5.2), (9.8, -0.5, 10.8), lens, glow=g, faces=("north", "east", "south", "west", "down"))]

    variants_block("l974-downlight", "Ceiling Light", [("state", ["on", "off"])], downlight, data={
        "blockmaterial": "Stone", "sounds": STONE, "lightAbsorption": 99, "resistance": 6, "drops": [], "sidesolid": {"all": True},
        # A lit lamp must not absorb its own light, or worldgen lighting spreads none of it
        "lightAbsorptionByType": {"l974-downlight-on": 0, "*": 99},
        "lightHsvByType": {"l974-downlight-on": [4, 2, 15]}, "attributes": {"l974structure": True, "l974light": True},
    }, comment="Level 974: a round recessed downlight in the ceiling (on: light 15, warm white, faintly pink)")

    def fairy(v):
        on = v["state"] == "on"
        els = []
        pins = [0, 16 / 3, 32 / 3, 16]
        wy = 11.4
        for i in range(3):
            x0, x1 = pins[i], pins[i + 1]
            xm = (x0 + x1) / 2
            for j, (a, b, ya, yb) in enumerate(((x0, xm, wy, wy - 1), (xm, x1, wy - 1, wy))):
                ln = math.hypot(b - a, yb - ya)
                ang = math.degrees(math.atan2(yb - ya, b - a))
                els.append(bx(f"Wire{i}{j}", (a, ya - 0.15, -1.0), (a + ln, ya + 0.15, -0.7), "wire", rot=(0, 0, ang), origin=(a, ya, -0.85)))
        for i, x in enumerate(pins):
            els.append(bx(f"Pin{i}", (x - 0.3, wy - 0.3, -0.8), (x + 0.3, wy + 0.4, 0), "wire"))
        cols = ["pink", "butter", "white"]
        for i in range(7):
            x = 1.15 + i * 2.28
            # Where the wire is at x (it sags between pins)
            span = int(x // (16 / 3))
            t = (x - pins[span]) / (16 / 3)
            y = wy - (1 - abs(2 * t - 1))
            c = cols[i % 3]
            tex = f"bulb-{c}" if on else f"bulb-{c}-off"
            els.append(bx(f"Bulb{i}", (x - 0.5, y - 1.8, -1.35), (x + 0.5, y - 0.3, -0.35), tex, glow=220 if on else 0))
        return hang(els)

    variants_block("l974-fairylights", "Fairy Lights", [("state", ["on", "off"]), ("side", SIDES)], fairy, rot="side",
                   box=(0, 0.55, 0.88, 1, 0.75, 1), collide=False, data=dict(HUNG, **{
                       "drops": [], "resistance": 6, "lightHsvByType": {"l974-fairylights-on-*": [58, 3, 8]},
                       "attributes": {"l974structure": True, "l974light": True}}),
                   comment="Level 974: fairy lights strung under the crown moulding (rel 4), in the room-side block; the suffix is the way they face")

    def nightlight(v):
        face = picture(bx("Cloud", (5.4, 6.6, -1.6), (10.6, 9.6, -0.3), "nightlight", glow=200), "nightlight-face", glow=200)
        return hang([
            bx("Plate", (6.2, 6.0, -0.3), (9.8, 10.2, 0), "plug"), face,
            bx("PuffL", (6.0, 9.6, -1.4), (8.2, 10.6, -0.5), "nightlight", glow=200),
            bx("PuffR", (7.8, 9.6, -1.4), (10.0, 11.0, -0.5), "nightlight", glow=200),
            bx("PuffS", (4.8, 7.2, -1.4), (5.4, 9.0, -0.5), "nightlight", glow=200),
            bx("PuffE", (10.6, 7.2, -1.4), (11.2, 9.0, -0.5), "nightlight", glow=200)])

    variants_block("l974-nightlight", "Night Light", [("side", SIDES)], nightlight, rot="side", box=(0.3, 0.35, 0.88, 0.7, 0.72, 1), collide=False,
                   data=dict(HUNG, **{"drops": [], "resistance": 6, "lightHsv": [38, 2, 6], "attributes": {"l974structure": True}}),
                   comment="Level 974: a cloud-shaped night light plugged in above the baseboard (rel 1), in the room-side block; it stays on")


# ======================================================================== Furniture (breakable: an offence)

FURNITURE = {"l974furniture": True}


def furniture():
    # ---- The bed: a real bed (vanilla BlockBed); variants end in -{head|feet}-{side} as BlockBed requires.
    # side = the way from the head to the foot. Modelled with the foot toward north.
    def bed(v):
        head = v["part"] == "head"
        cov = f"duvet-{v['bedding']}"
        els = []
        if head:
            for x0 in (0, 14.4):
                els += [bx(f"Post{x0}", (x0, 0, 14.4), (x0 + 1.6, 19, 16), "trim"), bx(f"Finial{x0}", (x0 + 0.2, 19, 14.6), (x0 + 1.4, 20.2, 15.8), "trim")]
            els += [bx("TopRail", (1.6, 17, 14.7), (14.4, 18.6, 15.7), "trim"), bx("LowRail", (1.6, 8, 14.7), (14.4, 9.4, 15.7), "trim")]
            for i, x in enumerate((4.2, 7.5, 10.8)):
                els.append(bx(f"Spindle{i}", (x, 9.4, 14.8), (x + 1, 17, 15.6), "trim"))
            els += [bx("RailL", (0.6, 3, 0), (1.6, 6, 14.4), "trim"), bx("RailR", (14.4, 3, 0), (15.4, 6, 14.4), "trim"),
                    bx("Mattress", (1.6, 5, 0), (14.4, 9, 14.4), "mattress"),
                    bx("Duvet", (0.8, 9, 0), (15.2, 10, 7.2), cov),
                    bx("DrapeL", (0.6, 5.6, 0), (1.0, 10, 7.2), cov), bx("DrapeR", (15.0, 5.6, 0), (15.4, 10, 7.2), cov),
                    bx("Fold", (0.9, 10, 6.0), (15.1, 11.2, 8.4), cov),
                    bx("PillowL", (1.8, 9, 9.2), (7.6, 11.8, 14.2), "pillow"), bx("PillowR", (8.4, 9, 9.2), (14.2, 11.8, 14.2), "pillow")]
            els += scale_els(plush("cat", "grey"), 0.55, at=(4.6, 10.6, 11.0))
            els += scale_els(plush("bunny", "white"), 0.5, at=(11.4, 10.8, 11.4), roty=-20)
            els += scale_els(plush("star", "butter"), 0.45, at=(8.0, 11.0, 7.4))
        else:
            for x0 in (0, 14.4):
                els += [bx(f"Post{x0}", (x0, 0, 0), (x0 + 1.6, 12, 1.6), "trim"), bx(f"Finial{x0}", (x0 + 0.2, 12, 0.2), (x0 + 1.4, 13.2, 1.4), "trim")]
            els += [bx("TopRail", (1.6, 10.4, 0.3), (14.4, 11.8, 1.3), "trim"), bx("LowRail", (1.6, 5, 0.3), (14.4, 6.2, 1.3), "trim")]
            for i, x in enumerate((4.2, 7.5, 10.8)):
                els.append(bx(f"Spindle{i}", (x, 6.2, 0.4), (x + 1, 10.4, 1.2), "trim"))
            els += [bx("RailL", (0.6, 3, 1.6), (1.6, 6, 16), "trim"), bx("RailR", (14.4, 3, 1.6), (15.4, 6, 16), "trim"),
                    bx("Mattress", (1.6, 5, 1.6), (14.4, 9, 16), "mattress"),
                    bx("Duvet", (0.8, 9, 1.4), (15.2, 10, 16), cov),
                    bx("DrapeL", (0.6, 5.6, 1.6), (1.0, 10, 16), cov), bx("DrapeR", (15.0, 5.6, 1.6), (15.4, 10, 16), cov),
                    bx("DrapeF", (1.0, 5.6, 1.4), (15.0, 10, 1.8), cov)]
            els += scale_els(plush("bear", "bear"), 0.5, at=(11.0, 10.0, 5.0), roty=25)
        return els

    variants_block("l974-bed", "Little Bed", [("bedding", ["hearts", "strawberries", "stars"]), ("part", ["head", "feet"]), ("side", SIDES)], bed,
                   rot="side", box=(0, 0, 0, 1, 0.5625, 1), data={
                       "class": "BlockBed", "entityClassByType": {"*-head-*": "Bed"}, "blockmaterial": "Cloth", "sounds": CLOTH,
                       "attributes": dict(FURNITURE, sleepEfficiency=0.85), "resistance": 2, "maxStackSize": 1,
                       "creativeinventory": {"general": ["l974-bed-hearts-head-north"], "backrooms": ["l974-bed-hearts-head-north"]},
                   }, comment="Level 974: a narrow white bed heaped with plushies, a real bed (vanilla BlockBed: -{head|feet}-{side}, side = head toward foot)",
                   names={"l974-bed-*": "Little Bed"})

    # ---- Bedside table with its pink lamp (on/off: the lights go out when Kitty is offended), a water bottle, vitamins
    def nightstand(v):
        on = True
        els = [bx("Body", (2, 0.8, 2), (14, 10, 14), "trim")]
        for x, z in ((2.2, 2.2), (12.6, 2.2), (2.2, 12.6), (12.6, 12.6)):
            els.append(bx(f"Leg{x}{z}", (x, 0, z), (x + 1.2, 0.8, z + 1.2), "trim"))
        els += [bx("Top", (1.6, 10, 1.6), (14.4, 10.8, 14.4), "trim"),
                bx("Drawer", (3, 6, 1.6), (13, 9.2, 2), "trim"), bx("Knob", (7.4, 7, 1.0), (8.6, 8.2, 1.6), "knob-pink"),
                bx("Shelf", (3, 1.6, 1.8), (13, 2.2, 2.2), "trim")]
        els += [bx("LampFoot", (4.5, 10.8, 8), (7.5, 11.4, 11), "ceramic")] + cyl("LampBody", 6, 9.5, 0.9, 11.4, 14.2, "ceramic")
        g = 220 if on else 0
        els += [bx("ShadeLow", (3, 14, 6.4), (9, 16.2, 12.6), "lampshade", glow=g), bx("ShadeTop", (3.8, 16.2, 7.2), (8.2, 18.2, 11.8), "lampshade", glow=g)]
        els += [bx("Bottle", (10, 10.8, 3), (11.6, 15, 4.6), "bottle"), bx("Cap", (10.3, 15, 3.3), (11.3, 15.8, 4.3), "knob-white"),
                bx("Jar1", (10.2, 10.8, 8), (11.6, 12.6, 9.4), "vitamins"), bx("Lid1", (10.1, 12.6, 7.9), (11.7, 13.1, 9.5), "fur-mint"),
                bx("Jar2", (12.0, 10.8, 10), (13.2, 12.2, 11.2), "vitamins"), bx("Lid2", (11.9, 12.2, 9.9), (13.3, 12.7, 11.3), "fur-lilac")]
        return els

    variants_block("l974-nightstand", "Bedside Table", [("side", SIDES)], nightstand, rot="side",
                   box=(0.1, 0, 0.1, 0.9, 0.68, 0.9), data={"lightHsv": [4, 3, 10], "attributes": FURNITURE,
                                                           "drops": drops((PLANK, 1, 0.5), ("game:candle", 0.3, 0.3))},
                   comment="Level 974: a small white bedside table, a pink-shaded lamp (light 10), a water bottle and vitamins")

    # ---- A heap of plushies on the floor (a, b)
    def heap(v):
        if v["kind"] == "a":
            return (scale_els(plush("cat", "grey"), 1.0, at=(5.4, 0, 6.0), roty=15) + scale_els(plush("bunny", "white"), 0.8, at=(11.4, 0, 5.2), roty=-25)
                    + scale_els(plush("bear", "bear"), 0.85, at=(10.8, 0, 11.6), roty=-10) + scale_els(plush("star", "butter"), 0.7, at=(4.4, 0, 12.2))
                    + scale_els(plush("cat", "lilac"), 0.55, at=(8.2, 0, 2.4), roty=5))
        return (scale_els(plush("bear", "mint"), 1.0, at=(6.0, 0, 7.0), roty=-12) + scale_els(plush("bunny", "sky"), 0.85, at=(11.6, 0, 9.4), roty=20)
                + scale_els(plush("cat", "pink"), 0.7, at=(4.6, 0, 12.6), roty=30) + scale_els(plush("star", "butter"), 0.6, at=(12.0, 0, 3.6)))

    variants_block("l974-plushheap", "Plushies", [("kind", ["a", "b"]), ("side", SIDES)], heap, rot="side", box=(0.1, 0, 0.1, 0.9, 0.56, 0.9), data={
        "blockmaterial": "Cloth", "sounds": CLOTH, "attributes": FURNITURE,
        "dropsByType": {"*-a-*": drops(("l974-plush-cat", 1, 0), ("l974-plush-bunny", 1, 0), ("l974-plush-bear", 1, 0), ("l974-plush-star", 1, 0)),
                        "*-b-*": drops(("l974-plush-bear", 1, 0), ("l974-plush-bunny", 1, 0), ("l974-plush-cat", 1, 0), ("l974-plush-star", 1, 0))},
    }, comment="Level 974: a heap of plush toys on the bedroom floor (they are Kitty's: the code marks what it drops)")

    # ---- Desks: plain, or with the old computer
    def desk(v):
        els = [bx("Top", (0, 12, 1), (16, 13.5, 15), "trim"), bx("PanelL", (0.6, 0, 1.6), (2, 12, 14.4), "trim"),
               bx("Pedestal", (10, 0, 1.6), (15.4, 12, 14.4), "trim"), bx("Modesty", (2, 5, 13), (10, 12, 14), "trim")]
        for i, (y0, y1) in enumerate(((0.8, 4.2), (4.6, 8.0), (8.4, 11.6))):
            els += [bx(f"Drawer{i}", (10.4, y0, 1.1), (15.0, y1, 1.6), "trim"), bx(f"Knob{i}", (12.2, (y0 + y1) / 2 - 0.5, 0.5), (13.2, (y0 + y1) / 2 + 0.5, 1.1), "knob-pink")]
        if v["kind"] == "computer":
            screen = picture(bx("Screen", (4.5, 15, 5.6), (11.5, 20.5, 6), "screen", faces=("north",)), "screen", glow=90)
            els += [bx("Stand", (5.5, 13.5, 7), (10.5, 14.2, 12), "beige"), bx("Monitor", (3.5, 14.2, 6), (12.5, 22, 12.6), "beige"),
                    bx("Back", (5, 15, 12.6), (11, 20.6, 15.2), "beige"), screen,
                    bx("Bezel", (3.9, 14.6, 5.7), (12.1, 15, 6), "beige", faces=("north", "up")),
                    bx("Power", (11, 14.4, 5.6), (11.8, 14.9, 6), "fur-mint", faces=("north",)),
                    bx("Keyboard", (3, 13.5, 1.4), (12, 14.3, 4.8), "keyboard"), bx("Mouse", (13, 13.5, 2.2), (14.6, 14.3, 4.2), "beige"),
                    bx("Cable", (13.6, 13.5, 4.2), (14.0, 13.7, 9), "beige")]
        else:
            els += cyl("Cup", 3, 11, 1.1, 13.5, 16.2, "crock-mint")
            els += [bx("Pencil1", (2.6, 14, 10.6), (3.0, 18, 11.0), "knob-pink", rot=(0, 0, 8), origin=(2.8, 14, 10.8)),
                    bx("Pencil2", (3.1, 14, 11.2), (3.5, 17.6, 11.6), "fur-sky", rot=(-6, 0, -6), origin=(3.3, 14, 11.4)),
                    bx("Notebook", (5, 13.5, 3), (10, 14.1, 8), "fur-pink"), bx("Pages", (5.2, 13.5, 3.2), (9.8, 13.95, 7.8), "trim", faces=("north", "east", "west"))]
            els += scale_els(plush("cat", "lilac"), 0.45, at=(13.0, 13.5, 10.5), roty=-30)
        return els

    variants_block("l974-desk", "Desk", [("kind", ["plain", "computer"]), ("side", SIDES)], desk, rot="side", box=(0, 0, 0.06, 1, 0.85, 0.94),
                   data={"attributes": FURNITURE, "classByType": {"*-computer-*": "BackroomsL974Computer"},
                         "drops": drops((PLANK, 2, 1), ("scrapwire", 0.5, 0.5))},
                   comment="Level 974: a white desk; the computer one carries an old beige computer (front: where you sit)",
                   names={"l974-desk-plain-*": "Desk", "l974-desk-computer-*": "Old Computer"})

    # ---- Chairs: a pink swivel chair at the desk, white dining chairs with pink cushions (they face north: the sitter looks north)
    def chair(v):
        if v["kind"] == "desk":
            els = [bx("LegX", (3, 0.6, 7.4), (13, 1.4, 8.6), "chrome"), bx("LegZ", (7.4, 0.6, 3), (8.6, 1.4, 13), "chrome")]
            for x, z in ((3, 7.4), (12, 7.4), (7.4, 3), (7.4, 12)):
                els.append(bx(f"Caster{x}{z}", (x, 0, z), (x + 1.2, 0.6, z + 1.2), "ink"))
            els += [bx("Post", (7.3, 1.4, 7.3), (8.7, 6, 8.7), "chrome"),
                    bx("Seat", (3, 6, 3), (13, 8, 13), "chairfabric"), bx("SeatEdge", (3.6, 6.4, 2.5), (12.4, 7.6, 13.5), "chairfabric"),
                    bx("Spine", (7.4, 6, 12.6), (8.6, 9.4, 13.6), "chrome"),
                    bx("Back", (3.5, 9, 12.4), (12.5, 17, 14), "chairfabric"), bx("BackTop", (4.2, 17, 12.5), (11.8, 17.8, 13.9), "chairfabric")]
            return els
        els = []
        for x, z in ((3, 3), (11.8, 3), (3, 11.8), (11.8, 11.8)):
            els.append(bx(f"Leg{x}{z}", (x, 0, z), (x + 1.2, 7, z + 1.2), "trim"))
        els += [bx("Seat", (2.8, 7, 2.8), (13.2, 8, 13.2), "trim"), bx("Cushion", (3.4, 8, 3.4), (12.6, 9.2, 12.4), "cushion"),
                bx("PostL", (3, 8, 11.8), (4.2, 18, 13), "trim"), bx("PostR", (11.8, 8, 11.8), (13, 18, 13), "trim"),
                bx("TopRail", (4.2, 15.6, 12), (11.8, 18, 12.8), "trim"),
                bx("Slat1", (6, 9.2, 12.1), (7, 15.6, 12.7), "trim"), bx("Slat2", (9, 9.2, 12.1), (10, 15.6, 12.7), "trim"),
                bx("Heart", (7.4, 16.2, 11.8), (8.6, 17.4, 12), "knob-pink", faces=("north",))]
        return els

    variants_block("l974-chair", "Chair", [("kind", ["desk", "dining"]), ("side", SIDES)], chair, rot="side", box=(0.18, 0, 0.18, 0.82, 0.56, 0.82),
                   data={"attributes": FURNITURE, "drops": drops((STICK, 2, 1), (CLOTHI, 0.3, 0.3))},
                   comment="Level 974: a pink swivel chair, a white dining chair with a pink cushion (the sitter faces the side)",
                   names={"l974-chair-desk-*": "Swivel Chair", "l974-chair-dining-*": "Dining Chair"})

    # ---- The dresser in the open closet: three drawers, pink knobs, a little plush on top. It gives cute clothes.
    def dresser(v):
        els = [bx("Body", (1, 1, 6), (15, 14, 16), "trim"), bx("Top", (0.6, 14, 5.6), (15.4, 15, 16), "trim"),
               bx("Plinth", (1.4, 0, 6.4), (14.6, 1, 15.6), "trim")]
        for i, (y0, y1) in enumerate(((1.6, 5.6), (6.0, 10.0), (10.4, 13.6))):
            els += [bx(f"Drawer{i}", (1.6, y0, 5.6), (14.4, y1, 6), "trim"),
                    bx(f"KnobL{i}", (4.2, (y0 + y1) / 2 - 0.6, 5.0), (5.4, (y0 + y1) / 2 + 0.6, 5.6), "knob-pink"),
                    bx(f"KnobR{i}", (10.6, (y0 + y1) / 2 - 0.6, 5.0), (11.8, (y0 + y1) / 2 + 0.6, 5.6), "knob-pink")]
        els += scale_els(plush("bunny", "pink"), 0.5, at=(4.5, 15, 11), roty=20)
        els += [bx("Tray", (9, 15, 8.5), (13.5, 15.4, 12.5), "fur-lilac"), bx("Comb", (9.6, 15.4, 9.4), (12.8, 15.9, 10.2), "knob-pink")]
        return els

    variants_block("l974-dresser", "Dresser", [("side", SIDES)], dresser, rot="side", box=(0.04, 0, 0.35, 0.96, 0.94, 1),
                   data={"attributes": dict(FURNITURE, l974clothes=[
                       "game:clothes-upperbody-kirtlepink", "game:clothes-upperbody-chemiseshort", "game:clothes-lowerbody-skirt",
                       "game:clothes-lowerbody-hosebluepink", "game:clothes-head-wreathflower", "game:clothes-shoulder-apronpink"]),
                         "class": "BackroomsL974Dresser", "drops": drops((PLANK, 2, 1), (CLOTHI, 0.5, 0.5))},
                   comment="Level 974: a white dresser in the open closet; it holds cute clothes in your size (attribute l974clothes)")

    # ---- The closet rod (rel 3): pastel clothes on hangers, and a bunny backpack hanging at the end. Walk through it.
    def closetrod(v):
        els = [bx("BracketL", (0.4, 11, 9), (1.4, 13, 16), "trim"), bx("BracketR", (14.6, 11, 9), (15.6, 13, 16), "trim"),
               bx("Rod", (0, 11.6, 9.6), (16, 12.4, 10.4), "chrome")]
        garments = [("pink", "dress"), ("mint", "shirt"), ("lilac", "dress"), ("sky", "shirt")]
        for i, (c, kind) in enumerate(garments):
            x = 2 + i * 3
            g = f"garment-{c}"
            els += [bx(f"Hook{i}", (x - 0.2, 11.4, 9.8), (x + 0.2, 13.0, 10.2), "chrome"),
                    bx(f"Hanger{i}", (x - 0.25, 10.4, 6.2), (x + 0.25, 11.0, 13.8), "chrome")]
            if kind == "dress":
                els += [bx(f"Bodice{i}", (x - 0.5, 3, 7.2), (x + 0.5, 10.4, 12.8), g), bx(f"Skirt{i}", (x - 0.6, -5, 6.0), (x + 0.6, 3, 14.0), g)]
            else:
                els += [bx(f"Shoulders{i}", (x - 0.5, 7, 5.6), (x + 0.5, 10.4, 14.4), g), bx(f"Shirt{i}", (x - 0.5, 0, 7.0), (x + 0.5, 7, 13.0), g)]
        face = picture(bx("Pack", (12.2, 3.6, 9.4), (15.8, 9, 11.6), "fur-white"), "face-white")
        els += [face, bx("PackEarL", (12.7, 9, 10.0), (13.5, 11.4, 10.9), "fur-white"), bx("PackEarR", (14.5, 9, 10.0), (15.3, 11.4, 10.9), "fur-white"),
                bx("Strap", (13.8, 9, 10.6), (14.2, 11.8, 11.0), "fur-pink"), bx("Pocket", (12.8, 3.8, 9.1), (15.2, 5.6, 9.4), "fur-pink")]
        return els

    variants_block("l974-closetrod", "Closet Rod", [("side", SIDES)], closetrod, rot="side", box=(0, 0.6, 0.3, 1, 0.85, 0.75), collide=False,
                   data={"blockmaterial": "Cloth", "sounds": CLOTH, "attributes": FURNITURE,
                         "drops": drops((CLOTHI, 1, 0.5), ("game:clothes-upperbody-chemiseshort", 0.3, 0))},
                   comment="Level 974: a clothes rod at rel 3 over the closet's second tile, pastel clothes hanging down into rel 2; walk through")

    # ---- Wall shelves (decorations on a plain wall at rel 3): two plushies, or three boxed figures
    def shelf(v):
        els = [bx("Board", (0, 4, -5), (16, 5.5, 0), "trim")]
        if v["kind"] == "plush":
            els += scale_els(plush("cat", "pink"), 0.6, at=(4.5, 5.5, -2.6), roty=10) + scale_els(plush("bear", "bear"), 0.6, at=(11.5, 5.5, -2.6), roty=-10)
        else:
            for i, x in enumerate((1.6, 6.5, 11.4)):
                b = bx(f"Box{i}", (x, 5.5, -3.8), (x + 3, 10.4, -1.8), f"figbox-side-{i}")
                els.append(picture(b, f"figbox-{i}"))
        return hang(els)

    variants_block("l974-shelf", "Wall Shelf", [("kind", ["plush", "figures"]), ("side", SIDES)], shelf, rot="side",
                   box=(0, 0.25, 0.68, 1, 0.66, 1), collide=False, data=dict(HUNG, **{"sounds": WOOD,
                         "attributes": FURNITURE, "drops": drops((PLANK, 1, 0))}),
                   comment="Level 974: a white floating shelf (rel 3) hung on the wall behind it: plushies, or boxed figures (the suffix is the way it faces)")

    # ---- Posters of original mascots (rel 2), taped at the corners
    def poster(v):
        p = picture(bx("Poster", (1, 1, -0.5), (15, 15, 0), "trim", faces=("north", "east", "west", "up", "down")), f"poster-{v['kind']}")
        els = [p]
        for i, (x, y) in enumerate(((0.6, 13.6), (13.8, 13.6), (0.6, 0.6), (13.8, 0.6))):
            els.append(bx(f"Tape{i}", (x, y, -0.62), (x + 1.6, y + 1.8, -0.5), "tape", faces=("north",)))
        return hang(els)

    variants_block("l974-poster", "Poster", [("kind", ["cat", "bunny", "rainbow", "star", "toast", "frog"]), ("side", SIDES)], poster, rot="side",
                   box=(0.06, 0.06, 0.96, 0.94, 0.94, 1), collide=False, data=dict(HUNG, **{"sounds": WOOD,
                         "attributes": FURNITURE, "drops": drops(("game:paper-parchment", 1, 0))}),
                   comment="Level 974: a cute poster (rel 2) taped to the wall behind it (the suffix is the way it faces)",
                   names={"l974-poster-cat-*": "Poster (Round Cat)", "l974-poster-bunny-*": "Poster (Strawberry Bunny)",
                          "l974-poster-rainbow-*": "Poster (Rainbow)", "l974-poster-star-*": "Poster (Smiling Star)",
                          "l974-poster-toast-*": "Poster (Happy Toast)", "l974-poster-frog-*": "Poster (Mushroom Frog)"})

    # ---- Empty photo frames in the hall (rel 2)
    def frame(v):
        t = "trim" if v["kind"] == "white" else "gilt"
        return hang([
            bx("Top", (3, 12.6, -1.2), (13, 14, 0), t), bx("Bottom", (3, 2, -1.2), (13, 3.4, 0), t),
            bx("Left", (3, 3.4, -1.2), (4.4, 12.6, 0), t), bx("Right", (11.6, 3.4, -1.2), (13, 12.6, 0), t),
            bx("Mat", (4.4, 3.4, -0.6), (11.6, 12.6, 0), "mat", faces=("north",)),
            bx("Back", (6, 5.4, -0.66), (10, 10.6, -0.6), "matback", faces=("north",))])

    variants_block("l974-frame", "Photo Frame", [("kind", ["white", "gold"]), ("side", SIDES)], frame, rot="side",
                   box=(0.18, 0.12, 0.92, 0.82, 0.88, 1), collide=False, data=dict(HUNG, **{"sounds": WOOD,
                         "attributes": FURNITURE, "drops": drops((STICK, 1, 0))}),
                   comment="Level 974: an empty photo frame (rel 2) on the wall behind it (the suffix is the way it faces)")

    # ---- The heart rug (2 x 2: nw, ne, sw, se)
    variants_block("l974-rug", "Heart Rug", [("part", ["nw", "ne", "sw", "se"])],
                   lambda v: [bx("Rug", (0, 0, 0), (16, 0.6, 16), "rug-" + str(["nw", "ne", "sw", "se"].index(v["part"])), faces=("up",), full=True)], box=(0, 0, 0, 1, 0.04, 1),
                   collide=False, data={"blockmaterial": "Cloth", "sounds": CLOTH, "attributes": FURNITURE, "drops": drops((CLOTHI, 0.5, 0)),
                                        "replaceable": 100},
                   comment="Level 974: a quarter of a pink heart rug (nw, ne, sw, se)")
    # ---- Kitchen: the pink fridge and the pantry (2 tall, food that comes back), counters, the stove, the banquette, the table
    def fridge(v):
        if v["part"] == "lower":
            els = [bx("Kick", (2, 0, 1.6), (14, 1.5, 14), "chrome"), bx("Body", (1.6, 1.5, 1.2), (14.4, 16, 15), "enamel"),
                   bx("BodyR", (1, 1.5, 1.8), (15, 16, 14.4), "enamel"),
                   bx("Door", (1.8, 2, 0.8), (14.2, 16, 1.2), "enamel", faces=("north", "east", "west", "down")),
                   bx("Handle", (12.1, 12, -0.6), (13.1, 16, 0.2), "chrome"), bx("Standoff", (12.2, 12.4, 0.2), (13.0, 13.2, 0.8), "chrome")]
            return els
        return [bx("Body", (1.6, 0, 1.2), (14.4, 14, 15), "enamel"), bx("BodyR", (1, 0, 1.8), (15, 14, 14.4), "enamel"),
                bx("Cap1", (2.2, 14, 1.8), (13.8, 15, 14.4), "enamel"), bx("Cap2", (3.2, 15, 2.6), (12.8, 15.6, 13.6), "enamel"),
                bx("Door", (1.8, 0, 0.8), (14.2, 5.6, 1.2), "enamel", faces=("north", "east", "west", "up")),
                bx("Freezer", (1.8, 6.4, 0.8), (14.2, 13.4, 1.2), "enamel", faces=("north", "east", "west", "up", "down")),
                bx("Handle", (12.1, 0, -0.6), (13.1, 4.0, 0.2), "chrome"), bx("Standoff", (12.2, 2.8, 0.2), (13.0, 3.6, 0.8), "chrome"),
                bx("FHandle", (12.1, 8, -0.6), (13.1, 12, 0.2), "chrome"), bx("FStand1", (12.2, 8.4, 0.2), (13.0, 9.2, 0.8), "chrome"),
                bx("FStand2", (12.2, 10.8, 0.2), (13.0, 11.6, 0.8), "chrome"),
                bx("Badge", (5.5, 10.2, 0.5), (10.5, 11.2, 0.8), "chrome", faces=("north", "up", "down", "east", "west")),
                bx("Heart", (7.4, 8.4, 0.6), (8.6, 9.6, 0.8), "knob-pink", faces=("north",))]

    variants_block("l974-fridge", "Pink Fridge", [("part", ["lower", "upper"]), ("side", SIDES)], fridge, rot="side", box=(0.06, 0, 0.06, 0.94, 1, 0.94),
                   data={"blockmaterial": "Metal", "sounds": METAL, "attributes": dict(FURNITURE, l974food="fridge"),
                         "class": "BackroomsL974Food", "drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 0.5, 0.5))},
                   comment="Level 974: a rounded 1950s pink fridge, two blocks tall; it hands out food that comes back (l974food: fridge)")

    def pantry(v):
        if v["part"] == "lower":
            els = [bx("Plinth", (1, 0, 1.6), (15, 0.8, 15.6), "trim"), bx("Body", (0.5, 0.8, 1), (15.5, 16, 16), "trim"),
                   bx("DoorL", (1, 1.2, 0.6), (7.85, 16, 1), "trim"), bx("DoorR", (8.15, 1.2, 0.6), (15, 16, 1), "trim"),
                   bx("PanelL", (2.2, 2.4, 0.3), (6.65, 16, 0.6), "trim"), bx("PanelR", (9.35, 2.4, 0.3), (13.8, 16, 0.6), "trim"),
                   bx("KnobL", (6.4, 14.6, -0.2), (7.4, 15.6, 0.6), "knob-pink"), bx("KnobR", (8.6, 14.6, -0.2), (9.6, 15.6, 0.6), "knob-pink")]
            return els
        return [bx("Body", (0.5, 0, 1), (15.5, 15, 16), "trim"), bx("Cornice", (0, 15, 0.4), (16, 16, 16), "trim"),
                bx("DoorL", (1, 0, 0.6), (7.85, 14.4, 1), "trim"), bx("DoorR", (8.15, 0, 0.6), (15, 14.4, 1), "trim"),
                bx("PanelL", (2.2, 0, 0.3), (6.65, 13.2, 0.6), "trim"), bx("PanelR", (9.35, 0, 0.3), (13.8, 13.2, 0.6), "trim"),
                bx("Heart", (7.4, 15.2, 0.2), (8.6, 15.8, 0.4), "knob-pink", faces=("north",))]

    variants_block("l974-pantry", "Pantry", [("part", ["lower", "upper"]), ("side", SIDES)], pantry, rot="side", box=(0.03, 0, 0.04, 0.97, 1, 1),
                   data={"attributes": dict(FURNITURE, l974food="pantry"), "class": "BackroomsL974Food", "drops": drops((PLANK, 3, 1), (NAILS, 0.5, 0.5))},
                   comment="Level 974: a tall white pantry cupboard, two blocks tall; it hands out food that comes back (l974food: pantry)")

    def counter(v):
        k = v["kind"]
        els = [bx("Plinth", (0, 0, 2.2), (16, 1.6, 16), "cupboard"), bx("Body", (0, 1.6, 1.2), (16, 14, 16), "cupboard")]
        if k == "sink":
            els += [bx("TopF", (0, 14, 0.4), (16, 15.6, 3), "countertop"), bx("TopB", (0, 14, 13), (16, 15.6, 16), "countertop"),
                    bx("TopL", (0, 14, 3), (3, 15.6, 13), "countertop"), bx("TopR", (13, 14, 3), (16, 15.6, 13), "countertop"),
                    bx("Basin", (3, 9, 3), (13, 9.6, 13), "steel", faces=("up",)),
                    bx("BasinN", (3, 9, 3), (13, 14, 3.3), "steel", faces=("south",)), bx("BasinS", (3, 9, 12.7), (13, 14, 13), "steel", faces=("north",)),
                    bx("BasinW", (3, 9, 3), (3.3, 14, 13), "steel", faces=("east",)), bx("BasinE", (12.7, 9, 3), (13, 14, 13), "steel", faces=("west",)),
                    bx("Drain", (7.2, 9.6, 7.2), (8.8, 9.7, 8.8), "ink", faces=("up",)),
                    bx("TapBase", (7, 15.6, 13.4), (9, 16.4, 15.4), "chrome"), bx("Riser", (7.5, 16.4, 13.9), (8.5, 21, 14.9), "chrome"),
                    bx("Spout", (7.5, 20, 9.4), (8.5, 21, 13.9), "chrome"), bx("Tip", (7.6, 18.8, 9.5), (8.4, 20, 10.3), "chrome"),
                    bx("HandleL", (4.6, 15.6, 13.8), (6.4, 17, 15), "chrome"), bx("HandleR", (9.6, 15.6, 13.8), (11.4, 17, 15), "chrome")]
        else:
            els.append(bx("Top", (0, 14, 0.4), (16, 15.6, 16), "countertop"))
        if k == "corner":
            els.append(bx("Front", (0.6, 2.4, 0.9), (15.4, 13.2, 1.2), "cupboard"))
        else:
            els += [bx("Drawer", (1.2, 11, 0.9), (14.8, 13.4, 1.2), "cupboard"), bx("DKnob", (7.4, 11.7, 0.3), (8.6, 12.7, 0.9), "knob-white"),
                    bx("Door", (1.2, 2.4, 0.9), (14.8, 10.6, 1.2), "cupboard"), bx("Field", (2.6, 3.8, 0.6), (13.4, 9.2, 0.9), "cupboard"),
                    bx("Knob", (12.2, 8.4, 0.0), (13.2, 9.4, 0.6), "knob-white")]
        if k == "canisters":
            for i, (x, r, h) in enumerate(((4, 1.9, 6.4), (8.3, 1.7, 5.0), (12, 1.5, 4.0))):
                els += cyl(f"Can{i}", x, 11.5, r, 15.6, 15.6 + h, f"canister-{i}")
                els += [bx(f"Lid{i}", (x - r * 0.8, 15.6 + h, 11.5 - r * 0.8), (x + r * 0.8, 16.3 + h, 11.5 + r * 0.8), "knob-white"),
                        bx(f"LidKnob{i}", (x - 0.4, 16.3 + h, 11.1), (x + 0.4, 17 + h, 11.9), "knob-pink")]
        if k.startswith("utensils"):
            c = "mint"
            els += cyl("Crock", 12, 11.5, 2.0, 15.6, 20.6, f"crock-{c}")
            els += [bx("SpoonHandle", (11.0, 19, 11.0), (11.6, 25.6, 11.6), "spoonwood", rot=(0, 0, 10), origin=(11.3, 19, 11.3)),
                    bx("SpoonBowl", (10.5, 25.4, 10.7), (12.1, 27.8, 11.9), "spoonwood", rot=(0, 0, 10), origin=(11.3, 19, 11.3)),
                    bx("WhiskHandle", (12.4, 19, 10.4), (12.9, 23.6, 10.9), "chrome", rot=(-8, 0, -6), origin=(12.6, 19, 10.6)),
                    bx("Whisk", (11.9, 23.6, 9.9), (13.4, 27.2, 11.4), "chrome", rot=(-8, 0, -6), origin=(12.6, 19, 10.6)),
                    bx("SpatHandle", (11.8, 19, 12.2), (12.3, 24.8, 12.7), "trim", rot=(8, 0, -2), origin=(12, 19, 12.4)),
                    bx("SpatHead", (11.2, 24.8, 12.0), (12.9, 27.6, 12.9), "knob-pink", rot=(8, 0, -2), origin=(12, 19, 12.4))]
        return els

    kinds = ["plain", "corner", "sink", "canisters", "utensils"]
    variants_block("l974-counter", "Kitchen Counter", [("kind", kinds), ("side", SIDES)], counter, rot="side", box=(0, 0, 0.02, 1, 0.98, 1),
                   data={"attributes": FURNITURE, "classByType": {"*-sink-*": "BackroomsL974Tap"},
                         "drops": drops((PLANK, 2, 1), (NAILS, 0.3, 0.3))},
                   comment="Level 974: white-topped counters with pink cupboards: plain, a blind corner, the sink (a tap), cute canisters, a mint utensil crock",
                   names={"l974-counter-*": "Kitchen Counter", "l974-counter-sink-*": "Kitchen Sink"})

    def stove(v):
        els = [bx("Plinth", (1, 0, 1.6), (15, 1.5, 15), "steel"), bx("Body", (0.5, 1.5, 1), (15.5, 14, 15.5), "enamel"),
               bx("Cooktop", (0, 14, 0.6), (16, 15, 16), "porcelain"),
               bx("Backguard", (0, 15, 14), (16, 20, 16), "enamel"),
               bx("Door", (1.5, 2.5, 0.6), (14.5, 12.5, 1), "enamel"),
               picture(bx("Window", (3.5, 5, 0.5), (12.5, 10, 0.6), "ovenglass", faces=("north",)), "ovenglass"),
               bx("Handle", (2.5, 11.2, -0.6), (13.5, 12, 0.0), "chrome"), bx("HS1", (3, 11.3, 0), (3.8, 11.9, 0.6), "chrome"),
               bx("HS2", (12.2, 11.3, 0), (13, 11.9, 0.6), "chrome")]
        for i, (cx, cz) in enumerate(((4.5, 4.5), (11.5, 4.5), (4.5, 11), (11.5, 11))):
            r = 2.6 if i % 3 == 0 else 2.1
            els += [bx(f"CoilN{i}", (cx - r, 15, cz - r), (cx + r, 15.4, cz - r + 0.8), "coil"),
                    bx(f"CoilS{i}", (cx - r, 15, cz + r - 0.8), (cx + r, 15.4, cz + r), "coil"),
                    bx(f"CoilW{i}", (cx - r, 15, cz - r + 0.8), (cx - r + 0.8, 15.4, cz + r - 0.8), "coil"),
                    bx(f"CoilE{i}", (cx + r - 0.8, 15, cz - r + 0.8), (cx + r, 15.4, cz + r - 0.8), "coil"),
                    bx(f"CoilC{i}", (cx - 0.6, 15, cz - 0.6), (cx + 0.6, 15.4, cz + 0.6), "coil")]
        for i, x in enumerate((2.2, 5.6, 10.4, 13.8)):
            els.append(bx(f"Knob{i}", (x - 0.7, 16.6, 13.4), (x + 0.7, 18.0, 14), "knob-white"))
        els.append(bx("Clock", (7, 16.4, 13.8), (9, 18.4, 14), "trim", faces=("north",)))
        return els

    variants_block("l974-stove", "Stove", [("side", SIDES)], stove, rot="side", box=(0, 0, 0.04, 1, 0.94, 1),
                   data={"blockmaterial": "Metal", "sounds": METAL, "attributes": FURNITURE, "drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 0.5, 0.5))},
                   comment="Level 974: a pink retro stove, four coil rings, an oven window")

    def banquette(v):
        els = [bx("Base", (0, 0, 3), (16, 6, 16), "pinkwood"), bx("Seat", (0, 6, 3), (16, 8, 13.6), "cushion"),
               bx("Lip", (0, 6.4, 2.6), (16, 7.6, 3), "cushion", faces=("north", "east", "west")),
               bx("BackBoard", (0, 6, 14), (16, 18, 16), "pinkwood"), bx("Cap", (0, 18, 13.6), (16, 18.8, 16), "pinkwood"),
               bx("BackCushion", (0.4, 8.4, 12.4), (15.6, 17.4, 14), "cushion")]
        if v["kind"] == "corner":
            els = [bx("Base", (0, 0, 3), (16, 6, 16), "pinkwood"), bx("BaseN", (3, 0, 0), (16, 6, 3), "pinkwood"),
                   bx("Seat", (0, 6, 3), (14, 8, 13.6), "cushion"), bx("SeatN", (3, 6, 0), (13.6, 8, 3), "cushion"),
                   bx("BackBoard", (0, 6, 14), (16, 18, 16), "pinkwood"), bx("Cap", (0, 18, 13.6), (16, 18.8, 16), "pinkwood"),
                   bx("BackCushion", (0.4, 8.4, 12.4), (12.4, 17.4, 14), "cushion"),
                   bx("SideBoard", (14, 6, 0), (16, 18, 14), "pinkwood"), bx("SideCap", (13.6, 18, 0), (16, 18.8, 13.6), "pinkwood"),
                   bx("SideCushion", (12.4, 8.4, 0.4), (14, 17.4, 14), "cushion")]
        return els

    variants_block("l974-banquette", "Banquette", [("kind", ["straight", "corner"]), ("side", SIDES)], banquette, rot="side",
                   boxes=lambda v: (0, 0, 0.19, 1, 0.5, 1) if v["kind"] == "straight" else (0, 0, 0, 1, 0.5, 1),
                   data={"attributes": FURNITURE, "drops": drops((PLANK, 2, 1), (CLOTHI, 0.5, 0.5))},
                   comment="Level 974: pink-painted banquette seating (front = side; the back against the opposite edge; corner: backs along the south and east edges at side north)")

    def table(v):
        els = [bx("Top", (1, 11, 1), (15, 12.5, 15), "trim"), bx("Apron", (1.6, 9.6, 1.6), (14.4, 11, 14.4), "trim")]
        for x, z in ((2, 2), (12.6, 2), (2, 12.6), (12.6, 12.6)):
            els += [bx(f"Leg{x}{z}", (x, 4, z), (x + 1.4, 9.6, z + 1.4), "trim"), bx(f"Foot{x}{z}", (x + 0.2, 0, z + 0.2), (x + 1.2, 4, z + 1.2), "trim")]
        els.append(bx("Placemat", (3, 12.5, 3.5), (13, 12.6, 13.5), "placemat", faces=("up",), full=True))
        els += cyl("Vase", 8, 8.5, 1.0, 12.6, 15.2, "vase")
        for i, (dx, dz, h, rz) in enumerate(((0, 0, 18.2, 0), (-0.8, 0.4, 17.4, 14), (0.8, -0.3, 17.6, -12))):
            o = (8, 15, 8.5)
            els += [bx(f"Stem{i}", (8 + dx - 0.15, 15, 8.5 + dz - 0.15), (8 + dx + 0.15, h, 8.5 + dz + 0.15), "stem", rot=(0, 0, rz), origin=o),
                    bx(f"Bloom{i}", (8 + dx - 0.8, h, 8.5 + dz - 0.8), (8 + dx + 0.8, h + 1.2, 8.5 + dz + 0.8), "petal", rot=(0, 0, rz), origin=o),
                    bx(f"Heart{i}", (8 + dx - 0.3, h + 1.2, 8.5 + dz - 0.3), (8 + dx + 0.3, h + 1.4, 8.5 + dz + 0.3), "petalheart", rot=(0, 0, rz), origin=o)]
        return els

    variants_block("l974-table", "Dining Table", [], table, box=(0.06, 0, 0.06, 0.94, 0.78, 0.94),
                   data={"attributes": FURNITURE, "drops": drops((PLANK, 3, 1))},
                   comment="Level 974: a square white dining table with a heart placemat and a little vase of pink flowers (remembered meals appear here)")
    LANG["block-l974-table"] = "Dining Table"

    def catclock(v):
        face = picture(bx("Head", (4.8, 9, -1.6), (11.2, 14, 0), "catclock"), "catclock-face")
        dial = picture(bx("Dial", (6, 2.4, -1.7), (10, 6.8, -1.4), "clockface", faces=("north",)), "clockface")
        return hang([
            bx("Body", (5.5, 1, -1.4), (10.5, 9, 0), "catclock"), face, dial,
            bx("EarL", (5.0, 14, -1.2), (6.8, 15.6, -0.2), "catclock"), bx("EarR", (9.2, 14, -1.2), (11.0, 15.6, -0.2), "catclock"),
            bx("Bow", (7.2, 8.6, -1.9), (8.8, 9.6, -1.5), "knob-pink"),
            bx("Tail", (7.4, -4, -1.0), (8.6, 1.2, -0.4), "catclock", rot=(0, 0, 10), origin=(8, 1.2, -0.7)),
            bx("TailTip", (7.2, -5.2, -1.1), (8.8, -3.8, -0.3), "knob-white", rot=(0, 0, 10), origin=(8, 1.2, -0.7))])

    variants_block("l974-catclock", "Cat Clock", [("side", SIDES)], catclock, rot="side",
                   box=(0.3, 0, 0.88, 0.7, 1, 1), collide=False, data=dict(HUNG, **{"sounds": WOOD,
                         "attributes": FURNITURE, "drops": drops(("game:gear-rusty", 0.3, 0), ("scrapwire", 0.3, 0))}),
                   comment="Level 974: a pink cat-shaped clock (rel 3) on the wall behind it, its tail hanging below (the suffix is the way it faces)")

    # ---- Bathrooms
    def toilet(v):
        return (cyl("Pedestal", 8, 8, 2.6, 0, 5, "porcelain") +
                [bx("Bowl", (4, 5, 2), (12, 8.4, 12), "porcelain"), bx("BowlR", (4.6, 5, 1.4), (11.4, 8.4, 12.6), "porcelain"),
                 bx("Seat", (4, 8.4, 2), (12, 9, 12), "porcelain"),
                 bx("Lid", (4.2, 9, 2.2), (11.8, 10.2, 11.6), "fluffy-pink"),
                 bx("Tank", (3, 7, 11.8), (13, 16.5, 15.8), "porcelain"), bx("TankLid", (2.6, 16.5, 11.4), (13.4, 17.4, 16), "porcelain"),
                 bx("Flush", (3.6, 14.6, 11.2), (5.2, 15.2, 11.8), "chrome")])

    variants_block("l974-toilet", "Toilet", [("side", SIDES)], toilet, rot="side", box=(0.18, 0, 0.08, 0.82, 0.62, 1),
                   data={"blockmaterial": "Ceramic", "sounds": CERAMIC, "attributes": FURNITURE, "drops": drops(("glassshard", 0.5, 0.5))},
                   comment="Level 974: a white toilet with a fluffy pink lid cover (front = side)")

    def basin(v):
        return ([bx("Foot", (5.4, 0, 8.4), (10.6, 1.2, 13.6), "pedestal")] + cyl("Pedestal", 8, 11, 2.0, 1.2, 10, "pedestal") +
                [bx("Under", (3, 9.5, 4), (13, 12, 14.6), "porcelain"),
                 bx("RimF", (2, 12, 3), (14, 14, 5), "porcelain"), bx("RimB", (2, 12, 12), (14, 14, 15.6), "porcelain"),
                 bx("RimL", (2, 12, 5), (4, 14, 12), "porcelain"), bx("RimR", (12, 12, 5), (14, 14, 12), "porcelain"),
                 bx("Bowl", (4, 11.2, 5), (12, 11.6, 12), "porcelain", faces=("up",)), bx("Drain", (7.4, 11.65, 8.0), (8.6, 11.7, 9.2), "chrome", faces=("up",)),
                 bx("TapBase", (7.2, 14, 13), (8.8, 14.8, 14.6), "chrome"), bx("Riser", (7.5, 14.8, 13.4), (8.5, 17.2, 14.2), "chrome"),
                 bx("Spout", (7.5, 16.4, 10.6), (8.5, 17.2, 13.4), "chrome"), bx("Tip", (7.6, 15.6, 10.7), (8.4, 16.4, 11.4), "chrome"),
                 bx("HandleL", (5, 14, 13.2), (6.4, 15.2, 14.4), "chrome"), bx("HandleR", (9.6, 14, 13.2), (11, 15.2, 14.4), "chrome")])

    variants_block("l974-basin", "Basin", [("side", SIDES)], basin, rot="side", box=(0.12, 0, 0.18, 0.88, 0.88, 1),
                   data={"blockmaterial": "Ceramic", "sounds": CERAMIC, "attributes": FURNITURE, "class": "BackroomsL974Tap",
                         "drops": drops(("glassshard", 0.5, 0.5), ("game:metalbit-copper", 0.3, 0.3))},
                   comment="Level 974: a white pedestal basin with a chrome tap (a tap: fills a held container with water)")

    def bathtub(v):
        head = v["part"] == "head"
        els = [bx("Under", (2.2, 1.6, 0), (13.8, 2.6, 16), "porcelain"),
               bx("WallL", (1.5, 2.5, 0), (3, 11.6, 16), "porcelain"), bx("WallR", (13, 2.5, 0), (14.5, 11.6, 16), "porcelain"),
               bx("RimL", (1.2, 11.6, 0), (3.2, 12.6, 16), "porcelain"), bx("RimR", (12.8, 11.6, 0), (14.8, 12.6, 16), "porcelain"),
               bx("Floor", (3, 2.5, 0), (13, 4, 16), "porcelain")]
        if head:
            els = [e for e in els]
            for e in els:
                e["to"][2] = min(e["to"][2], 14)
            els += [bx("End", (1.5, 2.5, 13.6), (14.5, 12.4, 15.6), "porcelain"), bx("EndRim", (1.2, 12.4, 13.4), (14.8, 13.4, 15.9), "porcelain"),
                    bx("FootL", (2, 0, 11.6), (3.6, 2.2, 13.2), "brass"), bx("FootR", (12.4, 0, 11.6), (14, 2.2, 13.2), "brass"),
                    bx("Duck", (10, 13.4, 13.9), (12.4, 14.9, 15.4), "duck"), bx("DuckHead", (9.6, 14.6, 14.1), (11, 16, 15.2), "duck"),
                    bx("Beak", (9.0, 15.0, 14.4), (9.6, 15.4, 14.9), "beak")]
        else:
            for e in els:
                e["from"][2] = max(e["from"][2], 2)
            els += [bx("End", (1.5, 2.5, 0.4), (14.5, 11.6, 2.4), "porcelain"), bx("EndRim", (1.2, 11.6, 0.2), (14.8, 12.6, 2.6), "porcelain"),
                    bx("FootL", (2, 0, 2.6), (3.6, 2.2, 4.2), "brass"), bx("FootR", (12.4, 0, 2.6), (14, 2.2, 4.2), "brass"),
                    bx("TapBase", (7.2, 12.6, 0.8), (8.8, 13.6, 2.0), "chrome"), bx("Spout", (7.5, 12.8, 2.0), (8.5, 13.8, 4.6), "chrome"),
                    bx("Tip", (7.6, 12.0, 3.8), (8.4, 12.8, 4.6), "chrome"),
                    bx("HandleL", (5, 12.6, 1.0), (6.6, 13.8, 2.0), "chrome"), bx("HandleR", (9.4, 12.6, 1.0), (11, 13.8, 2.0), "chrome"),
                    bx("Drain", (7.2, 4.0, 3.2), (8.8, 4.1, 4.8), "chrome", faces=("up",))]
        return els

    variants_block("l974-bathtub", "Bathtub", [("part", ["head", "foot"]), ("side", SIDES)], bathtub, rot="side", box=(0.07, 0, 0, 0.93, 0.78, 1),
                   data={"blockmaterial": "Ceramic", "sounds": CERAMIC, "attributes": FURNITURE, "class": "BackroomsL974Tap",
                         "drops": drops(("glassshard", 0.5, 0.5), ("game:metalbit-copper", 0.3, 0.3))},
                   comment="Level 974: a white clawfoot tub, two blocks long (side = head toward foot); a rubber duck on the head's rim, the tap at the foot")

    def mirror(v):
        els = []
        for i, (x0, y0, x1, y1) in enumerate(((2, 4.6, 14, 12.4), (3.8, 2.6, 12.2, 14.4), (2.7, 3.3, 13.3, 13.7))):
            els.append(bx(f"Frame{i}", (x0, y0, -1.2), (x1, y1, 0), "knob-pink"))
            els.append(bx(f"Glass{i}", (x0 + 1, y0 + 1, -1.35), (x1 - 1, y1 - 1, -1.2), "mirror", faces=("north",)))
        return hang(els)

    variants_block("l974-mirror", "Mirror", [("side", SIDES)], mirror, rot="side",
                   box=(0.12, 0.15, 0.9, 0.88, 0.92, 1), collide=False, data=dict(HUNG, **{"sounds": CERAMIC,
                         "attributes": FURNITURE, "drops": drops(("glassshard", 1, 0.5))}),
                   comment="Level 974: a round, pink-framed mirror (rel 2) on the wall behind it (the suffix is the way it faces)")

    def towelrail(v):
        return hang([
            bx("BracketL", (2, 9, -2.6), (3, 10, 0), "chrome"), bx("BracketR", (13, 9, -2.6), (14, 10, 0), "chrome"),
            bx("Rail", (1.5, 9.2, -2.6), (14.5, 10, -1.8), "chrome"),
            bx("TowelFront", (3.4, 3, -3.1), (12.6, 10.2, -2.6), "towel"), bx("TowelBack", (3.4, 5, -1.8), (12.6, 10.2, -1.3), "towel"),
            bx("TowelFold", (3.4, 10, -3.1), (12.6, 10.6, -1.3), "towel")])

    variants_block("l974-towelrail", "Towel Rail", [("side", SIDES)], towelrail, rot="side",
                   box=(0.08, 0.18, 0.8, 0.92, 0.68, 1), collide=False, data=dict(HUNG, **{"sounds": CERAMIC,
                         "attributes": FURNITURE, "drops": drops((CLOTHI, 1, 0))}),
                   comment="Level 974: a chrome rail with a folded pink towel (rel 2) on the wall behind it (the suffix is the way it faces)")

    def catbed(v):
        els = [bx("Base", (2, 0, 2), (14, 2, 14), "catbed-pink"), bx("BaseX", (1.4, 0, 3), (14.6, 2, 13), "catbed-pink"),
               bx("BaseZ", (3, 0, 1.4), (13, 2, 14.6), "catbed-pink"),
               bx("RimN", (3, 2, 1.6), (13, 5, 4), "catbed-pink"), bx("RimS", (3, 2, 12), (13, 5, 14.4), "catbed-pink"),
               bx("RimW", (1.6, 2, 3), (4, 5, 13), "catbed-pink"), bx("RimE", (12, 2, 3), (14.4, 5, 13), "catbed-pink"),
               bx("Cushion", (4, 2, 4), (12, 3, 12), "catbed-white")]
        for i, (x, z) in enumerate(((2.4, 2.4), (11.6, 2.4), (2.4, 11.6), (11.6, 11.6))):
            els.append(bx(f"Corner{i}", (x, 2, z), (x + 2, 4.6, z + 2), "catbed-pink"))
        els.append(picture(bx("Pillow", (8.4, 3, 8.4), (11.6, 5.8, 9.6), "heartpillow", rot=(-15, 0, 0), origin=(10, 3, 9)), "heartpillow"))
        return els

    variants_block("l974-catbed", "Cat Bed", [], catbed, box=(0.1, 0, 0.1, 0.9, 0.32, 0.9),
                   data={"blockmaterial": "Cloth", "sounds": CLOTH, "attributes": FURNITURE, "drops": drops((CLOTHI, 1, 0.5))},
                   comment="Level 974: a round pink and white cushion bed by the master bedroom's back wall, a small heart pillow in it")
    LANG["block-l974-catbed"] = "Cat Bed"


# ======================================================================== Items

ITEM_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": -20, "y": -140, "z": 0}, "origin": {"x": 0.5, "y": 0.28, "z": 0.5}, "scale": 2.6},
    "fpHandTransform": {"translation": {"x": 0.05, "y": 0.1, "z": 0.3}, "rotation": {"x": 0, "y": 140, "z": 0}, "scale": 1.9},
    "tpHandTransform": {"translation": {"x": -0.8, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": 135, "z": 0}, "scale": 0.8},
    "groundTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.6},
}
SPRITE_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}


def items():
    folder = os.path.join(ASSETS, "itemtypes", "974")
    plushes = {"cat": ("cat", "grey"), "bunny": ("bunny", "white"), "bear": ("bear", "bear"), "star": ("star", "butter")}
    shapes = {}
    for k, (kind, colour) in plushes.items():
        shapes[f"l974-plush-{k}"] = {"base": shape(f"plush-{k}", scale_els(plush(kind, colour), 0.8, at=(8, 0, 8)), folder="item/974")}
    data = {"code": "l974-plush", "variantgroups": [{"code": "type", "states": list(plushes)}], "maxstacksize": 4,
            "shapeByType": shapes, "creativeinventory": {"general": ["*"], "items": ["*"], "backrooms": ["*"]},
            "attributes": {"backroomsCute": True, "handbook": {"groupBy": ["l974-plush-*"]}}, "materialDensity": 200,
            "heldTpIdleAnimation": "holdbothhandslarge"}
    data.update(ITEM_TRANSFORMS)
    write_json(os.path.join(folder, "l974-plush.json"), data, "Plush toys: a round grey cat, a bunny holding a strawberry, a teddy bear, a smiling star. Cute (backroomsCute)")
    LANG.update({"item-l974-plush-cat": "Cat Plush", "item-l974-plush-bunny": "Bunny Plush", "item-l974-plush-bear": "Teddy Bear",
                 "item-l974-plush-star": "Star Plush",
                 "itemdesc-l974-plush-*": "Soft, a little worn, and cute. Something in the Backrooms likes cute things."})

    def food(code, english, satiety, category, desc, tex=None, extra=None, stack=16):
        d = {"code": code, "maxstacksize": stack, "texture": {"base": f"item/974/{tex or code[5:]}"},
             "creativeinventory": {"general": ["*"], "items": ["*"], "backrooms": ["*"]},
             "nutritionProps": {"satiety": satiety, "foodcategory": category}, "materialDensity": 600}
        d.update(SPRITE_TRANSFORMS)
        if extra:
            d.update(extra)
        write_json(os.path.join(folder, code + ".json"), d, english)
        LANG[f"item-{code}"] = english
        if desc:
            LANG[f"itemdesc-{code}"] = desc

    food("l974-marshmallow", "Greasy Marshmallows", 80, "NoNutrition", "Sweet, slick and filling for about a minute.")
    food("l974-candy", "Pastel Candy", 50, "NoNutrition", "Mint, lilac and butter yellow. They all taste of sugar.")
    food("l974-strawberrymilk", "Strawberry Milk", 160, "Dairy", "A little carton, cold from the pink fridge. Pinker than milk ought to be.")
    # Remembered meals: three variants, each its own food category and satiety
    d = {"code": "l974-meal", "variantgroups": [{"code": "meal", "states": ["pancakes", "soup", "macaroni"]}], "maxstacksize": 4,
         "textureByType": {f"l974-meal-{m}": {"base": f"item/974/meal-{m}"} for m in ("pancakes", "soup", "macaroni")},
         "creativeinventory": {"general": ["*"], "items": ["*"], "backrooms": ["*"]},
         "nutritionPropsByType": {"l974-meal-pancakes": {"satiety": 520, "foodcategory": "Grain"},
                                  "l974-meal-soup": {"satiety": 480, "foodcategory": "Vegetable"},
                                  "l974-meal-macaroni": {"satiety": 480, "foodcategory": "Dairy"}},
         "materialDensity": 600}
    d.update(SPRITE_TRANSFORMS)
    write_json(os.path.join(folder, "l974-meal.json"), d, "A Remembered Meal: pancakes, chicken soup, macaroni and cheese, from Kitty's kitchen table")
    LANG.update({"item-l974-meal-pancakes": "A Remembered Meal (pancakes)", "item-l974-meal-soup": "A Remembered Meal (chicken soup)",
                 "item-l974-meal-macaroni": "A Remembered Meal (macaroni and cheese)",
                 "itemdesc-l974-meal-*": "Exactly the way it used to be made for you."})


# ======================================================================== The patch: vanilla cute things

def patch():
    # Checked against 1.22.7: flowers are blocktypes/plant/flower.json and flower-lupine.json (both code "flower"),
    # seashells blocktypes/aquatic/seashell.json; each already has an attributes object.
    ops = [{"op": "add", "path": "/attributes/backroomsCute", "value": True, "file": f"game:blocktypes/{f}.json"}
           for f in ("plant/flower", "plant/flower-lupine", "aquatic/seashell")]
    write_json(os.path.join(ASSETS, "patches", "l974-cute.json"), ops,
               "Level 974: vanilla flowers and seashells are cute (backroomsCute): carrying one may get you taken to Kitty's House")


# ======================================================================== Lang

def lang():
    LANG.update({
        "level-18": "Level 974: Kitty's House",
        "levelhint-18": "You are a guest here. Be a good one.",
        "levelname-18": "Level 974",
        "l974-arrive": "You wake in a pink bedroom that feels as if it has always been yours. Somewhere, a music box is playing.",
        "l974-call": "\"Here Kitty, Kitty, Kitty!\"",
        "l974-ask": "Kitty holds out a long black arm.",
        "l974-gift-taken": "Kitty takes the {0}. You are suddenly, overwhelmingly sleepy.",
        "l974-gift-wrong": "Kitty does not want that. It wants what you brought.",
        "l974-gift-refused": "Kitty does not come. Not today.",
        "l974-wake": "You wake somewhere else, rested. For a while, you feel watched over.",
        "l974-wake-home": "You wake in the Lobby, rested, with less in your pockets than you remember.",
        "l974-offended": "The lights go out. The house is very quiet now.",
        "l974-forgiven": "Somewhere in the house, a light comes back on.",
        "l974-pink-1": "The pink is very calming.",
        "l974-pink-2": "The pink is starting to feel close.",
        "l974-pink-3": "You can't remember the last colour you saw that wasn't pink.",
        "l974-sugar": "The food in the cupboards is all sweets now.",
        "l974-smell-1": "You smell pancakes, the way someone used to make them for you.",
        "l974-smell-2": "You smell chicken soup, the kind you were given when you were ill.",
        "l974-smell-3": "You smell macaroni and cheese, straight from the pot.",
        "l974-smell-4": "You smell birthday cake.",
        "l974-smell-5": "You smell hot cocoa, and a little burnt milk.",
        "l974-meal": "There is a plate on the table that was not there before.",
        "l974-memory-1": "A memory surfaces, soft at the edges: a kitchen table, and someone humming.",
        "l974-memory-2": "A memory surfaces, soft at the edges: a night light, and a door left open a crack.",
        "l974-memory-3": "A memory surfaces, soft at the edges: a toy you lost, and never stopped looking for.",
        "l974-memory-4": "A memory surfaces, soft at the edges: being carried up to bed, half asleep.",
        "l974-pc-title": "Guest",
        "l974-pc-mail": "Mail",
        "l974-pc-internet": "Internet",
        "l974-pc-dreamsleep": "DreamSleep",
        "l974-pc-owner": "Owner: password required.",
        "l974-mail-from": "From: Microsoft · To: New Windows Customer · Subject: Welcome!",
        "l974-mail-body": ("Greetings, wanderer. If you are reading this, you picked up something cute on your travels, and Kitty liked it. "
                           "Whatever you found is Kitty's now.<br><br>Kitty is the tall dark shape at the edge of your eye, the one that watches you "
                           "sleep. It will not hurt you. You are its guest: do not hurt it, do not break its things, and try not to scream when it "
                           "comes up behind you.<br><br>Kitty keeps the fridge and the cupboards full. Do not stay too long. The food turns to sugar, "
                           "and the pink stops being kind.<br><br>When you want to leave, hold out the thing you brought and call: Here Kitty, Kitty, "
                           "Kitty! It will take its gift, and you will wake somewhere just as safe."),
        "l974-internet-1": "Searching… 1 result. A place to start lies near where you will wake.",
        "l974-internet-2": "Searching… ▒▒▒ ▒▒ ▒▒▒▒▒▒ ▒▒▒▒▒.",
        "l974-internet-3": "Searching… The page cannot be displayed.",
        "l974-internet-4": "Searching… ᚲᛁᛏᛏᛁ ᛁᛋ ᚺᛟᛗᛖ.",
        "l974-dreamsleep": "Your dreams are ready. Sleep to start.",
        "l974-dream": "You dream of rooms you have never been in, and some you have. You wake steadier.",
        "item-creature-l974-kitty": "Kitty",
        "prefixandcreature-l974-kitty": "Kitty",
        "blockhelp-l974-call": "Call Kitty, or give it what you brought (something cute in hand)",
        "blockhelp-l974-tap": "Fill with water",
        "l974-gift-none": "You have nothing cute to give.",
        "l974-detour": "Something takes an interest in what you are carrying, and the world goes pink.",
        "l974-waypoint": "Where Kitty will let you wake",
        "l974-internet-searching": "Searching… (it takes a while)",
    })
    # Block names not set where the block was made
    LANG.update({
        "block-l974-slope-*": "Sloped Ceiling", "block-l974-lintel-*": "Doorway Lintel", "block-l974-casing-*": "Door Casing",
        "block-l974-window-*": "Window",
        "block-l974-downlight-*": "Ceiling Light", "block-l974-fairylights-*": "Fairy Lights", "block-l974-nightlight-*": "Night Light",
        "block-l974-nightstand-*": "Bedside Table", "block-l974-plushheap-*": "Plushies", "block-l974-dresser-*": "Dresser",
        "block-l974-closetrod-*": "Closet Rod", "block-l974-shelf-*": "Wall Shelf", "block-l974-frame-*": "Photo Frame",
        "block-l974-rug-*": "Heart Rug", "block-l974-fridge-*": "Pink Fridge", "block-l974-pantry-*": "Pantry",
        "block-l974-stove-*": "Stove", "block-l974-banquette-*": "Banquette", "block-l974-catclock-*": "Cat Clock",
        "block-l974-toilet-*": "Toilet", "block-l974-basin-*": "Basin", "block-l974-bathtub-*": "Bathtub", "block-l974-mirror-*": "Mirror",
        "block-l974-towelrail-*": "Towel Rail",
    })


def merge_lang():
    """Updates the level's keys in lang/en.json in place; new keys go after the last of the level's keys already there
    (the first time, after "levelname-18"), so nothing else in the shared file moves."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    index = {}
    for i, line in enumerate(lines):
        m = re.match(r'^\t"((?:[^"\\]|\\.)*)":', line)
        if m:
            index[json.loads('"' + m.group(1) + '"')] = i
    new = []
    for key, value in LANG.items():
        enc = "\t" + json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)
        if key in index:
            i = index[key]
            comma = "," if lines[i].rstrip().endswith(",") else ""
            lines[i] = enc + comma
        else:
            new.append(enc)
    if new:
        mine = [index[k] for k in LANG if k in index]
        anchor = max(mine) if mine else index["levelname-18"]
        if not lines[anchor].rstrip().endswith(","):
            lines[anchor] = lines[anchor].rstrip() + ","
            trailing = False
        else:
            trailing = True
        block_lines = [l + "," for l in new[:-1]] + [new[-1] + ("," if trailing else "")]
        lines[anchor + 1:anchor + 1] = block_lines
    out = "\n".join(lines)
    json.loads(out)  # still valid
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(f"lang: {len(LANG)} keys ({len(new)} new)")


def main():
    only = set(sys.argv[1:])
    if not only or "tex" in only:
        gen_974_tex.generate()
    if not only or "blocks" in only:
        structure()
        lights()
        furniture()
        items()
        patch()
    if not only or "kitty" in only:
        import gen_974_kitty
        gen_974_kitty.generate(LANG)
    if not only or "sounds" in only:
        import gen_974_sounds
        gen_974_sounds.generate()
    lang()
    if not only or "lang" in only or "blocks" in only:
        merge_lang()
    print(f"974: {COUNT['blocktypes']} block types, {COUNT['variants']} variants, {COUNT['shapes']} shapes")


if __name__ == "__main__":
    main()
