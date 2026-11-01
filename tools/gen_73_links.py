"""Level 73, "The Redlands": the blocks of its ways in and out, called from gen_73.py (run that, under the asset lock).

docs/design/experimental-levels/LINKS.md and the plan's "Links": the Gloom in Level 9 ("stay near the Gloom for too long on
Level 9.1", Wikidot), a pool of darkness light does not reach in a yard or a street; and the north door in the castle's
curtain wall, which Coran opens for whoever asks him to lead them out (our invention: the page knows no way out).

Writes, under blocktypes/73, shapes/block/73 and textures/block/73:
  l73-gloom                         the Gloom's ground: black, flat, dull (it never breaks)
  l73-gloomair                      the black murk over the Gloom's heart: no body, drawn from inside as well as out
                                    (BlendNoCull), the faces between two of it left out, so it reads as one dark pool
  l73-postern-{shut,open}-{wb,eb,wt,et}  the north door, two leaves of black iron-bound oak two high, a chain and a padlock
                                    across (class BackroomsL73Door, l73Door "postern"); open: the leaves swung out against
                                    the wall, the doorway's sides, sill and head black
  l73-postern-back                  the wall's inner course behind the door: silver ashlar, black on its north face
"""
import os
import random

from PIL import Image, ImageDraw

import matlib as M


# ---------------- Textures ----------------

def gloom_ground(seed):
    """32x32: almost black, the faintest cold mottle, no detail to catch the eye."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (32, 32))
    px = img.load()
    f = M.fbm(32, seed, cells=(8, 4))
    for y in range(32):
        for x in range(32):
            v = 4 + int(3 * f[y][x]) + rng.randrange(0, 2)
            px[x, y] = (v, v, v + 2, 255)
    return img


def gloom_murk(seed):
    """32x32: black, a little see-through, thickening and thinning in slow patches."""
    img = Image.new("RGBA", (32, 32))
    px = img.load()
    f = M.fbm(32, seed, cells=(16, 8))
    for y in range(32):
        for x in range(32):
            px[x, y] = (2, 2, 4, 212 + int(30 * f[y][x]))
    return img


def void():
    """16x16: the dark beyond the north door. Nothing at all."""
    return Image.new("RGBA", (16, 16), (1, 1, 2, 255))


def postern_out(seed):
    """32x32: the north door from outside, both leaves (16 wide each) two blocks high: black oak, iron straps, a chain."""
    img = M.wood_planks(seed=seed, size=32, base=(30, 22, 18), planks=8, direction="v", grain=3, per_plank=6, gap=(10, 7, 6))
    M.grime(img, 0.2, seed=seed + 1, color=(14, 10, 8), cover=0.6)
    d = ImageDraw.Draw(img)
    strap, stud = (24, 24, 26, 255), (96, 94, 92, 255)
    for y in (4, 26):
        d.rectangle([1, y, 30, y + 1], fill=strap)
        for x in range(3, 31, 4):
            d.point((x, y), fill=stud)
    d.line([(15, 0), (15, 31)], fill=(6, 4, 4, 255))
    d.rectangle([0, 0, 31, 31], outline=(10, 8, 6, 255))
    # The chain across at hand height (the seam of the two blocks), links of dull brass and iron, and the padlock
    for i in range(8):
        x, y = 1 + i * 4, 15 + (1 if i in (3, 4) else 0)
        if i % 2:
            d.ellipse([x, y - 1, x + 3, y + 1], outline=(110, 100, 78, 255))
        else:
            d.line([(x, y), (x + 3, y)], fill=(80, 78, 74, 255), width=2)
    d.rectangle([13, 17, 18, 21], fill=(64, 58, 48, 255))
    d.point((15, 19), fill=(6, 4, 4, 255))
    # Gouges where things have clawed at it, low down
    rng = random.Random(seed + 5)
    px = img.load()
    for _ in range(10):
        x0, y0 = rng.randrange(2, 28), rng.randrange(18, 30)
        for i in range(rng.randrange(2, 5)):
            x, y = x0 + i, y0 + i // 2
            if 0 <= x < 32 and 0 <= y < 32:
                r, g, b, a = px[x, y]
                px[x, y] = (min(255, r + 26), min(255, g + 20), min(255, b + 14), a)
    return img


def postern_in(seed):
    return M.wood_planks(seed=seed, size=32, base=(36, 26, 20), planks=8, direction="v", grain=3, per_plank=6, gap=(12, 8, 6))


# ---------------- Shapes ----------------

def _face(tex, uv):
    return {"texture": tex, "uv": [round(v, 3) for v in uv]}


POSTERN_PARTS = ["wb", "eb", "wt", "et"]


def postern_shape(part, state):
    """One block of the north door (its outside faces north). Seen from the north the east leaf is on the left, so it takes
    the left half of the picture. Shut: a leaf four thick in the middle of the wall. Open: swung out (north) against the
    wall, hinged at its outer edge, and the doorway black all round."""
    east = part[0] == "e"
    top = part[1] == "t"
    u0 = 0 if east else 16
    v0 = 0 if top else 16
    outer = [u0, v0, u0 + 16, v0 + 16]
    inner = [16 - u0, v0, 32 - u0, v0 + 16]
    tex = {"out": "backrooms:block/73/postern-out", "in": "backrooms:block/73/postern-in", "void": "backrooms:block/73/void"}
    edge = [0, 0, 4, 16]
    els = []
    if state == "shut":
        els.append({"name": "Leaf", "from": [0, 0, 6], "to": [16, 16, 10], "faces": {
            "north": _face("#out", outer), "south": _face("#in", inner),
            "east": _face("#in", edge), "west": _face("#in", edge), "up": _face("#in", [0, 0, 16, 4]), "down": _face("#in", [0, 0, 16, 4])}})
    else:
        x0 = 12 if east else 0
        # (Swung out on its hinge at the wall's face: its outside now against the wall, its inside toward the doorway)
        els.append({"name": "Leaf", "from": [x0, 0, -15], "to": [x0 + 4, 16, 0], "faces": {
            ("east" if east else "west"): _face("#out", outer), ("west" if east else "east"): _face("#in", inner),
            "north": _face("#in", edge), "south": _face("#in", edge), "up": _face("#in", [0, 0, 4, 15]), "down": _face("#in", [0, 0, 4, 15])}})
        # The doorway: nothing but dark at its sides, sill and head, and at its back
        side = {"name": "Side", "from": [15.9, 0, 0] if east else [0, 0, 0], "to": [16, 16, 16] if east else [0.1, 16, 16],
                "faces": {("west" if east else "east"): _face("#void", [0, 0, 16, 16])}}
        els.append(side)
        if top:
            els.append({"name": "Head", "from": [0, 15.9, 0], "to": [16, 16, 16], "faces": {"down": _face("#void", [0, 0, 16, 16])}})
        else:
            els.append({"name": "Sill", "from": [0, 0, 0], "to": [16, 0.1, 16], "faces": {"up": _face("#void", [0, 0, 16, 16])}})
        els.append({"name": "Back", "from": [0, 0, 15.9], "to": [16, 16, 16], "faces": {"north": _face("#void", [0, 0, 16, 16])}})
    return {"textureWidth": 32, "textureHeight": 32, "textures": tex, "elements": els}


# ---------------- Blocktypes ----------------

def blocktypes():
    out = []
    out.append(("// Level 73's way in from Level 9: the Gloom's ground, black and dull, a pool of darkness light does not reach (it never breaks)", {
        "code": "l73-gloom",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Soil",
        "drawtype": "cube",
        "textures": {"all": {"base": "block/73/gloom"}},
        "attributes": {"l73Fixed": True},
        "resistance": 1000,
        "drops": [],
        "sounds": {"walk": "game:walk/sludge*", "place": "game:block/dirt*", "break": "game:block/dirt*", "hit": "game:block/dirt*"},
    }))
    out.append(("// Level 73's way in from Level 9: the black murk over the Gloom's heart (no body; seen from inside as well as out)", {
        "code": "l73-gloomair",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Air",
        "drawtype": "cube",
        "renderpass": "BlendNoCull",
        "faceCullMode": "Merge",
        "textures": {"all": {"base": "block/73/gloom-murk"}},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "emitSideAo": {"all": False},
        "lightAbsorption": 6,
        "collisionbox": None,
        "selectionbox": None,
        "replaceable": 6000,
        "rainPermeable": True,
        "attributes": {"l73Fixed": True},
        "resistance": 1000,
        "drops": [],
        "sounds": {},
    }))
    out.append(("// Level 73's way out: the north door in the castle's curtain wall, chained; only CORAN opens it (Regions.L73System.Links)", {
        "code": "l73-postern",
        "class": "BackroomsL73Door",
        "variantgroups": [{"code": "state", "states": ["shut", "open"]}, {"code": "part", "states": POSTERN_PARTS}],
        "creativeinventory": {"general": ["*-shut-wb"], "backrooms": ["*-shut-wb"]},
        "blockmaterial": "Wood",
        "drawtype": "json",
        "shapeByType": {f"*-{st}-{p}": {"base": f"block/73/postern-{st}-{p}"} for st in ("shut", "open") for p in POSTERN_PARTS},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 1,
        "collisionboxByType": {"*-open-*": None, "*-shut-*": {"x1": 0, "y1": 0, "z1": 0.375, "x2": 1, "y2": 1, "z2": 0.625}},
        "selectionboxByType": {"*-open-w*": {"x1": 0, "y1": 0, "z1": -0.9375, "x2": 0.25, "y2": 1, "z2": 0},
                               "*-open-e*": {"x1": 0.75, "y1": 0, "z1": -0.9375, "x2": 1, "y2": 1, "z2": 0},
                               "*-shut-*": {"x1": 0, "y1": 0, "z1": 0.375, "x2": 1, "y2": 1, "z2": 0.625}},
        "attributes": {"l73Door": "postern", "l73Fixed": True},
        "resistance": 1000,
        "drops": [],
        "sounds": {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    }))
    out.append(("// Level 73: the curtain wall's inner course behind the north door, silver ashlar, its north face the dark beyond the door", {
        "code": "l73-postern-back",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Stone",
        "drawtype": "cube",
        "textures": {"all": {"base": "block/73/silverwall"}, "north": {"base": "block/73/void"}},
        "attributes": {"l73Fixed": True},
        "resistance": 1000,
        "drops": [],
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe", "hit": "game:block/rock-hit-pickaxe"},
    }))
    return out


def textures(save):
    save(gloom_ground(7460), "block/73/gloom")
    save(gloom_murk(7461), "block/73/gloom-murk")
    save(void(), "block/73/void")
    save(postern_out(7462), "block/73/postern-out")
    save(postern_in(7463), "block/73/postern-in")
    return 5


def shapes(write_json, shape_dir):
    n = 0
    for st in ("shut", "open"):
        for p in POSTERN_PARTS:
            write_json(os.path.join(shape_dir, f"postern-{st}-{p}.json"), None, postern_shape(p, st))
            n += 1
    return n


LANG = [
    ("block-l73-gloom", "The Gloom"),
    ("block-l73-gloomair", "The Gloom"),
    ("block-l73-postern-*", "North Door"),
    ("block-l73-postern-back", "Silver Ashlar"),
]
