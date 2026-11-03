"""Level 73, "The Redlands" (experimental): its six blocks, their textures, the sconce's model, the moon's picture, and
its lang keys. Run under the asset lock: bash tools/locked.sh run python tools/gen_73.py

Writes assets/backrooms/blocktypes/73/l73-*.json, textures/block/73/*.png, shapes/block/73/*.json,
textures/environment/l73-moon.png, and the level's keys in lang/en.json (between the Level 73 lines, in place): the
castle's furnishings come from gen_73_castle.py, the messages, Coran's lines from gen_73_lore.py (the handbook page is gen_guide.py's).
Coran himself is tools/gen_73_coran.py; the level's notes are in gen_notes.py.

The island is crimson earth flecked with black and split by thin blood-red cracks; black basalt with a maroon sheen and
pale mineral veins on its outcrops; grey-pink ash sand on the beach; glossy red-brown mud in the gullies. The Silver
Castle is cool, bright silver-grey ashlar. The sconces are black iron round a dim amber glow.
"""
import json
import math
import os
import random
import re

from PIL import Image, ImageDraw, ImageFilter

import gen_73_castle as castle
import gen_73_interior as interior
import gen_73_links as links
import gen_73_lore as lore
import gen_73_r4_castle as r4castle
import gen_73_r4_props as r4props
import matlib as M
import texlib

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures")
S = 32


def save(img, rel):
    path = os.path.join(TEX, *rel.split("/")) + ".png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def blood_crack(img, seed, colour=(120, 20, 18), length=(10, 20)):
    """A thin wandering crack filled with dark blood red, a darker pixel beside it, wrapping."""
    rng = random.Random(seed)
    w, h = img.size
    px = img.load()
    x, y = rng.uniform(0, w), rng.uniform(0, h)
    a = rng.uniform(0, 2 * math.pi)
    for i in range(int(rng.uniform(*length))):
        X, Y = int(x) % w, int(y) % h
        px[X, Y] = M.rgba(M.mix(px[X, Y], colour, 0.85))
        M.touch(img, X + 1, Y, -0.12)
        a += rng.uniform(-0.6, 0.6)
        x += math.cos(a)
        y += math.sin(a)
    return img


def flecks(img, seed, n, colour, strength=0.8):
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        px[x, y] = M.rgba(M.mix(px[x, y], colour, strength * rng.uniform(0.6, 1.0)))
    return img


def clods(img, seed, n, strength=0.12):
    """Packed clods: Worley cells, their borders darkened, each face a shade of its own."""
    pts = M.points(S, n, seed)
    f1, f2, idx = M.worley(S, pts)
    rng = random.Random(seed + 1)
    shades = [rng.uniform(-strength, strength) for _ in pts]
    for y in range(S):
        for x in range(S):
            edge = f2[y][x] - f1[y][x]
            f = shades[idx[y][x]] * 0.6 - (strength * 1.4 if edge < 1.0 else 0)
            M.touch(img, x, y, f)
    return img


# ---------------- Textures ----------------

def redearth(seed):
    img = M.noise_hv((70, 22, 20), amp=4, seed=seed, mottle=9, hue=3)
    clods(img, seed + 2, 14, 0.1)
    flecks(img, seed + 3, 26, (14, 10, 12))
    blood_crack(img, seed + 4)
    blood_crack(img, seed + 5, length=(6, 12))
    return img


def blackrock(seed):
    img = texlib.marble((34, 28, 31), (150, 146, 142), seed, veins=1, sharpness=10, mottle=0.08, turbulence=3.5)
    sheen = M.fbm(S, seed + 1, (16, 8))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            t = max(0.0, sheen[y][x]) * 0.5
            px[x, y] = M.rgba(M.mix((r, g, b), (78, 22, 30), t))
    grain = M.noise_hv((0, 0, 0), amp=3, seed=seed + 2, mottle=0, hue=0)
    gp = grain.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            d = gp[x, y][0] - 0  # (the grain alone, about 0..3)
            px[x, y] = M.rgba((r + d, g + d, b + d))
    return img


def ashsand(seed):
    img = M.noise_hv((122, 106, 106), amp=6, seed=seed, mottle=7, hue=2)
    clods(img, seed + 1, 30, 0.08)
    flecks(img, seed + 2, 40, (70, 60, 62), 0.5)
    flecks(img, seed + 3, 20, (176, 162, 160), 0.4)
    return img


def bloodmud(seed):
    img = M.noise_hv((60, 22, 17), amp=3, seed=seed, mottle=8, hue=3)
    wet = M.fbm(S, seed + 1, (16, 8, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            t = wet[y][x]
            if t > 0.35:  # puddles: darker, redder, with a glint at their top edge
                px[x, y] = M.rgba(M.mix((r, g, b), (44, 8, 8), min(1.0, (t - 0.35) * 2.5)))
                if wet[(y - 1) % S][x] <= 0.35:
                    px[x, y] = M.rgba(M.mix(px[x, y], (150, 70, 62), 0.6))
    flecks(img, seed + 2, 10, (130, 60, 52), 0.5)
    return img


def burnt(seed):
    """The blackened fields: charred near-black earth, ashy grey flecks, a few dark crimson clods showing through."""
    img = M.noise_hv((36, 24, 23), amp=4, seed=seed, mottle=10, hue=2)
    clods(img, seed + 1, 18, 0.12)
    flecks(img, seed + 2, 34, (96, 90, 88), 0.55)
    flecks(img, seed + 3, 16, (98, 30, 26), 0.7)
    blood_crack(img, seed + 4, colour=(84, 18, 16), length=(5, 10))
    return img


def crust(seed):
    """A crust of dried blood over the earth: a dull crimson glaze, crazed by thin dark cracks into small irregular flakes,
    the earth showing through where it has flaked away."""
    img = redearth(seed + 9)
    px = img.load()
    pts = M.points(S, 26, seed, jitter=1.0)
    f1, f2, idx = M.worley(S, pts)
    cover = M.fbm(S, seed + 5, (16, 8))
    rng = random.Random(seed + 1)
    shades = [rng.uniform(-12, 8) for _ in pts]
    for y in range(S):
        for x in range(S):
            if cover[y][x] < -0.25:
                continue  # flaked away: the earth under it
            r, g, b, a = px[x, y]
            d = shades[idx[y][x]]
            glaze = (96 + d, 22 + d * 0.3, 20 + d * 0.3)
            c = M.mix((r, g, b), glaze, 0.75)
            edge = f2[y][x] - f1[y][x]
            if edge < 0.7:
                c = M.mix(c, (28, 10, 10), 0.75)
            px[x, y] = M.rgba(c)
    flecks(img, seed + 3, 10, (138, 46, 38), 0.45)
    return img


def deadgrass(seed, height):
    """Withered grass, 32 px, transparent: thin blades from the bottom, black-red at the root to a dry, ashy rust at the tip."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    n = {1: 9, 2: 12, 3: 14}[height]
    top = {1: 0.42, 2: 0.7, 3: 0.97}[height]
    for _ in range(n):
        x = rng.uniform(2, S - 3)
        h = S * top * rng.uniform(0.55, 1.0)
        lean = rng.uniform(-0.35, 0.35)
        tip = rng.choice([(112, 50, 38), (96, 66, 54), (86, 36, 30), (118, 78, 60)])
        bent = rng.random() < 0.3
        steps = int(h)
        for i in range(steps):
            t = i / max(1, steps - 1)
            X = int(round(x + lean * i + (0.08 * i * i / S * (1 if lean > 0 else -1) if bent else 0)))
            Y = S - 1 - i
            if not (0 <= X < S and 0 <= Y < S):
                break
            c = M.mix((24, 10, 10), tip, t ** 1.0)
            px[X, Y] = M.rgba(c)
            if i < steps * 0.4 and 0 <= X + 1 < S:  # thicker at the root
                px[X + 1, Y] = M.rgba(M.mix(c, (18, 8, 8), 0.4))
    return img


def bone(seed):
    """Old bone, bleached and weathered: ivory with long fibres along it, pores, and dark grime in its hollows."""
    img = M.noise_hv((146, 134, 110), amp=5, seed=seed, mottle=8, hue=2)
    px = img.load()
    fib = M.fbm(S, seed + 1, (16, 4))
    rng = random.Random(seed + 2)
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            # (fibres run along x: the noise is sampled stretched)
            f = fib[(y * 3) % S][(x // 4) % S] * 18
            px[x, y] = M.rgba((r + f, g + f, b + f * 0.8))
    flecks(img, seed + 3, 30, (112, 100, 82), 0.6)
    M.grime(img, 0.3, seed=seed + 4, color=(74, 56, 44), cover=0.55)
    for _ in range(3):
        blood_crack(img, rng.randrange(10000), colour=(96, 70, 58), length=(4, 9))
    return img


def wainscot(seed):
    """The keep's rooms below the chair rail: a raised mahogany panel in a frame of rails and stiles, a moulded rail on top."""
    img = M.wood_planks(seed=seed, base=(84, 36, 24), planks=1, direction="v", grain=4, contrast=1.0, per_plank=4, gap=(40, 18, 12))
    M.bevel(img, (0, 0, 31, 31), width=1, strength=0.18)
    M.inset(img, (4, 9, 27, 28), width=1, strength=0.25)
    M.bevel(img, (6, 11, 25, 26), width=1, strength=0.18)
    px = img.load()
    for x in range(S):  # the chair rail: a lit moulding over a shadowed bead
        for y, k in ((0, 0.28), (1, 0.18), (2, 0.05), (3, -0.12), (4, 0.06), (5, -0.22)):
            M.touch(img, x, y, k)
    return img


def damask(seed):
    """Red damask wallpaper above the panelling: a deep crimson ground and a small repeating fleuron (a lozenge with a
    stem and two leaves) in a darker, glossier red, a dot of dull gold at its heart; tiles on all sides (one block repeats
    up the wall)."""
    img = M.noise_hv((98, 18, 24), amp=3, seed=seed, mottle=6, hue=2)
    px = img.load()
    def mark(X, Y, colour, k):
        X, Y = X % S, Y % S
        r, g, b, a = px[X, Y]
        px[X, Y] = M.rgba(M.mix((r, g, b), colour, k))
    def fleuron(cx, cy):
        for y in range(-4, 5):
            for x in range(-3, 4):
                if abs(x) / 3.0 + abs(y) / 4.0 <= 1.0 and abs(x) / 3.0 + abs(y) / 4.0 > 0.55:
                    mark(cx + x, cy + y, (64, 8, 14), 0.7)  # the lozenge's outline
        for y in range(-2, 3):
            mark(cx, cy + y, (64, 8, 14), 0.5)
        for d in (-1, 1):
            mark(cx + 2 * d, cy + 4, (64, 8, 14), 0.6)
            mark(cx + 3 * d, cy + 5, (64, 8, 14), 0.5)
        mark(cx, cy, (156, 116, 56), 0.6)
    for cx, cy in ((8, 4), (24, 4), (0, 20), (16, 20)):
        fleuron(cx, cy)
    return img


def silverwall(seed):
    img = M.brick(seed=seed, base=(172, 176, 182), mortar=(112, 114, 120), course=8, length=16, offset=0.5, mortar_w=1,
                  jitter=9, hue=2, pits=0.04, chamfer=True, grain=4, mottle=7)
    M.grime(img, 0.08, seed=seed + 1, color=(84, 80, 84), cover=0.4)
    return img


def sconce_iron(seed):
    img = M.noise_hv((40, 37, 38), amp=3, seed=seed, mottle=5, hue=1)
    M.rust(img, 0.12, seed=seed + 1)
    return img


def sconce_glow(seed):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            t = y / (S - 1)  # brightest at the bottom, where the flame is
            c = M.mix((150, 70, 24), (255, 196, 110), t)
            d = rng.uniform(-8, 8)
            px[x, y] = M.rgba((c[0] + d, c[1] + d, c[2] + d * 0.5))
    # The cage's bars across the glass
    for x in (0, 1, 15, 16, 30, 31):
        for y in range(S):
            px[x, y] = M.rgba((34, 30, 30))
    return img


def moon():
    """The moon, 64 px: a pale disc, a little warm, its seas darker, the limb fading, transparent round it."""
    n = 64
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(7301)
    seas = [(rng.uniform(14, 50), rng.uniform(14, 50), rng.uniform(6, 13)) for _ in range(6)]
    craters = [(rng.uniform(8, 56), rng.uniform(8, 56), rng.uniform(1.5, 3.5)) for _ in range(14)]
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - n / 2, y + 0.5 - n / 2
            r = math.hypot(dx, dy) / (n / 2 - 1)
            if r > 1:
                continue
            c = (236, 226, 214)
            for sx, sy, sr in seas:
                d = math.hypot(x - sx, y - sy) / sr
                if d < 1:
                    c = M.mix(c, (176, 162, 156), 0.55 * (1 - d) ** 0.7)
            for cx, cy, cr in craters:
                d = math.hypot(x - cx, y - cy) / cr
                if d < 1:
                    c = M.mix(c, (160, 150, 146) if d < 0.7 else (250, 244, 236), 0.4)
            limb = 1 - 0.25 * r ** 3
            px[x, y] = M.rgba((c[0] * limb, c[1] * limb, c[2] * limb))
    return img


# ---------------- Blocktypes ----------------

def cube_block(code, comment, textures, material, walk, dig, resistance, extra=None):
    alts = [{"base": t} for t in textures[1:]]
    tex = {"base": textures[0]}
    if alts:
        tex["alternates"] = alts
    b = {
        "code": code,
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": material,
        "drawtype": "cube",
        "textures": {"all": tex},
        "resistance": resistance,
        "drops": [],
        "sounds": {"walk": walk, "place": dig, "break": dig, "hit": dig},
    }
    if extra:
        b.update(extra)
    return comment, b


def sconce_block():
    sides = ["north", "east", "south", "west"]
    rot = {"north": 0, "east": 270, "south": 180, "west": 90}
    box = {"x1": 0.3, "y1": 0.13, "z1": 0.45, "x2": 0.7, "y2": 0.9, "z2": 1}
    return ("// Level 73: an iron wall sconce in the Silver Castle (the wall to its back, south for -north), a dim amber glow", {
        "code": "l73-sconce",
        "variantgroups": [{"code": "side", "states": sides}],
        "shapeByType": {f"*-{s}": {"base": "block/73/sconce", "rotateY": rot[s]} for s in sides},
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal",
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "lightHsv": [6, 5, 8],
        "renderpass": "OpaqueNoCull",
        "resistance": 1.5,
        "collisionbox": None,
        "selectionboxByType": {f"*-{s}": dict(box, rotateY=rot[s]) for s in sides},
        "drops": [],
        "sounds": {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
    })


def deadgrass_block():
    heights = ["short", "mid", "tall"]
    return ("// Level 73: withered black-red grass on the fields (rel 1 over the ground); no collision, fixed colours (no climate tint)", {
        "code": "l73-deadgrass",
        "variantgroups": [{"code": "height", "states": heights}],
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Plant",
        "drawtype": "cross",
        "shape": {"base": "game:block/basic/cross"},
        "texturesByType": {f"*-{h}": {"north": {"base": f"block/73/deadgrass-{k + 1}"}, "south": {"base": f"block/73/deadgrass-{k + 1}"}}
                           for k, h in enumerate(heights)},
        "renderpass": "OpaqueNoCull",
        "randomDrawOffset": True,
        "randomizeRotations": True,
        "vertexFlags": {"windMode": "NormalWind", "windData": 2},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 0.2,
        "replaceable": 5000,
        "collisionbox": None,
        "selectionbox": {"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 0.5, "z2": 0.85},
        "drops": [],
        "sounds": {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
    })


LINED_FACES = ["north", "east", "south", "west"]


def lined_block(code, inner, comment):
    """A block of the keep's outer wall lined on one side (the room's, named by the variant: -south shows the lining on its
    south face) with the given lining, silver ashlar elsewhere; -all is lined all round (a partition between rooms)."""
    tex = {f"*-{f}": {"all": {"base": "block/73/silverwall"}, f: {"base": inner}} for f in LINED_FACES}
    tex["*-all"] = {"all": {"base": inner}}
    return (comment, {
        "code": code,
        "variantgroups": [{"code": "lined", "states": LINED_FACES + ["all"]}],
        "creativeinventory": {"general": ["*-all"], "backrooms": ["*-all"]},
        "blockmaterial": "Stone",
        "drawtype": "cube",
        "texturesByType": tex,
        "resistance": 1000,
        "attributes": {"l73Fixed": True},
        "drops": [],
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe", "hit": "game:block/planks"},
    })


def face(tex, uv, glow=0):
    f = {"texture": tex, "uv": uv}
    if glow:
        f["glow"] = glow
    return f


def box(name, frm, to, tex, glow=0):
    x1, y1, z1 = frm
    x2, y2, z2 = to
    return {
        "name": name, "from": frm, "to": to,
        "faces": {
            "north": face(tex, [x1, 16 - y2, x2, 16 - y1], glow), "south": face(tex, [x1, 16 - y2, x2, 16 - y1], glow),
            "east": face(tex, [z1, 16 - y2, z2, 16 - y1], glow), "west": face(tex, [z1, 16 - y2, z2, 16 - y1], glow),
            "up": face(tex, [x1, z1, x2, z2], glow), "down": face(tex, [x1, z1, x2, z2], glow),
        },
    }


def sconce_shape():
    """A wall candle-sconce (the wall to its back, south): a pointed iron back plate with a raised field, a gilt boss
    and rivets, C-scrolls either side; an arm out from the boss on a curled brace, curling down at its end; a drip pan
    with a lip, a socket, a candle with wax run down it and pooled on the pan, the flame (drawn from both sides:
    the block is OpaqueNoCull)."""
    import gen_73_r4_props as P
    from gen_73_interior import bb, octo
    els = [
        bb("Plate", (6.0, 3.0, 15.3), (10.0, 12.0, 16.0), "#iron"),
        bb("Field", (6.6, 3.6, 15.0), (9.4, 11.4, 15.3), "#iron"),
        bb("PlatePoint", (6.9, 10.9, 15.32), (9.1, 13.1, 16.0), "#iron", rot=("z", 45, (8, 12.0, 15.6))),
        bb("PlateDrop", (7.2, 2.2, 15.33), (8.8, 3.8, 16.0), "#iron", rot=("z", 45, (8, 3.0, 15.6))),
        bb("RivetTop", (7.7, 10.4, 14.75), (8.3, 11.0, 15.0), "#gold"),
        bb("RivetLow", (7.7, 4.0, 14.75), (8.3, 4.6, 15.0), "#gold"),
    ]
    els += octo("Boss", "z", (8, 7.3), 14.3, 15.0, 0.95, "#gold", n=2)
    for nm, x0, sg in (("L", 5.2, 1), ("R", 10.4, -1)):
        hx = (x0, x0 + 1.4) if sg > 0 else (x0 - 1.0, x0 + 0.4)
        els += [bb(f"Scroll{nm}", (x0, 6.0, 15.4), (x0 + 0.4, 9.8, 16.0), "#iron"),
                bb(f"Scroll{nm}Top", (hx[0], 9.4, 15.4), (hx[1], 9.8, 16.0), "#iron"),
                bb(f"Scroll{nm}Low", (hx[0], 6.0, 15.4), (hx[1], 6.4, 16.0), "#iron"),
                bb(f"Scroll{nm}Tip", (x0 + (0.4 if sg > 0 else -0.6), 8.6, 15.4), (x0 + (1.0 if sg > 0 else 0.0), 9.4, 16.0), "#iron")]
    els += [bb("Arm", (7.7, 6.9, 9.0), (8.3, 7.5, 14.3), "#iron"),
            bb("Brace", (7.75, 5.6, 11.8), (8.25, 6.0, 14.6), "#iron", rot=("x", 35, (8, 5.8, 13.2))),
            bb("BraceCurl", (7.75, 4.4, 14.2), (8.25, 5.3, 14.9), "#iron"),
            bb("ArmCurl", (7.75, 6.1, 8.5), (8.25, 7.4, 8.95), "#iron"),
            bb("ArmTip", (7.75, 5.8, 8.95), (8.25, 6.25, 9.6), "#iron")]
    els += P.candle("Candle", 8, 7.5, 9.6, 3.8, r=0.55, pan=1.9, cup=0.7, drip=0, blob=True, fw=1.25, fh=2.1)
    els += P.ring8("Lip", 8, 9.6, 7.75, 8.05, 1.75, 0.22, "#iron")
    return {
        "textureWidth": 16, "textureHeight": 16,
        "textures": {"iron": "backrooms:block/73/sconce-iron", "gold": "backrooms:block/73/gold", "wax": "backrooms:block/73/r4p-wax",
                     "flame": "backrooms:block/73/r4p-flame"},
        "elements": els,
    }


def write_json(path, comment, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write(comment + "\n")
        json.dump(obj, f, indent="\t")
        f.write("\n")


# ---------------- Lang ----------------

LANG = [
    ("level-21", "Level 73: The Redlands"),
    ("levelhint-21", "Run for the castle. Do not look around."),
    ("levelname-21", "Level 73"),
    ("level-2101", "The Silver Castle"),
    ("levelhint-2101", "He is the reason you are alive."),
    ("block-l73-redearth", "Crimson Earth"),
    ("block-l73-blackrock", "Black Rock"),
    ("block-l73-ash-sand", "Ash Sand"),
    ("block-l73-bloodmud", "Blood Mud"),
    ("block-l73-silverwall", "Silver Ashlar"),
    ("block-l73-sconce-*", "Iron Sconce"),
    ("block-l73-burnt", "Blackened Earth"),
    ("block-l73-crust", "Blood Crust"),
    ("block-l73-deadgrass-*", "Dead Grass"),
    ("block-l73-bone", "Great Hound's Bone"),
    ("block-l73-wainscot-*", "Mahogany Panelling"),
    ("block-l73-damask-*", "Damask-Papered Wall"),
] + castle.LANG + interior.LANG + r4castle.LANG + r4props.LANG + links.LANG + lore.LANG


def write_lang():
    """Replaces the level's lines in en.json in place (from its level-21 line to its levelname-21 line, and any of its
    keys elsewhere), keeping the file's line endings and everything else byte for byte."""
    path = os.path.join(ASSETS, "lang", "en.json")
    raw = open(path, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    ours = {k for k, _ in LANG}
    key_re = re.compile(rb'^\t"([^"]+)":')
    start = next(i for i, l in enumerate(lines) if l.startswith(b'\t"level-21":'))
    kept = []
    for i, l in enumerate(lines):
        m = key_re.match(l)
        if m and m.group(1).decode() in ours and i != start:
            continue
        kept.append(l)
    at = next(i for i, l in enumerate(kept) if l.startswith(b'\t"level-21":'))
    new = [b'\t' + json.dumps(k).encode() + b': ' + json.dumps(v, ensure_ascii=False).encode() + b',' for k, v in LANG]
    kept[at:at + 1] = new
    open(path, "wb").write(nl.join(kept))


def main():
    save(redearth(7310), "block/73/redearth")
    save(redearth(7311), "block/73/redearth-2")
    save(blackrock(7320), "block/73/blackrock")
    save(blackrock(7321), "block/73/blackrock-2")
    save(ashsand(7330), "block/73/ashsand")
    save(bloodmud(7340), "block/73/bloodmud")
    save(silverwall(7350), "block/73/silverwall")
    save(silverwall(7351), "block/73/silverwall-2")
    save(sconce_iron(7360), "block/73/sconce-iron")
    save(sconce_glow(7361), "block/73/sconce-glow")
    save(moon(), "environment/l73-moon")
    save(burnt(7380), "block/73/burnt")
    save(burnt(7381), "block/73/burnt-2")
    save(crust(7390), "block/73/crust")
    save(crust(7391), "block/73/crust-2")
    for k in (1, 2, 3):
        save(deadgrass(7400 + k, k), f"block/73/deadgrass-{k}")
    save(bone(7410), "block/73/bone")
    save(bone(7411), "block/73/bone-2")
    save(wainscot(7420), "block/73/wainscot")
    save(damask(7421), "block/73/damask")

    bt = os.path.join(ASSETS, "blocktypes", "73")
    blocks = [
        cube_block("l73-redearth", "// Level 73: the island's crimson-stained ground, packed and flecked with black",
                   ["block/73/redearth", "block/73/redearth-2"], "Soil", "game:walk/gravel*", "game:block/dirt*", 2.5),
        cube_block("l73-blackrock", "// Level 73: wet black basalt with a maroon sheen and pale veins (outcrops, hilltops, the courtyard)",
                   ["block/73/blackrock", "block/73/blackrock-2"], "Stone", "game:walk/stone*", "game:block/rock-hit-pickaxe", 6),
        cube_block("l73-ash-sand", "// Level 73: grey-pink ash sand on the beach",
                   ["block/73/ashsand"], "Sand", "game:walk/sand*", "game:block/sand", 1.5),
        cube_block("l73-bloodmud", "// Level 73: glossy red-brown mud in the gullies",
                   ["block/73/bloodmud"], "Soil", "game:walk/sludge*", "game:block/dirt*", 1.5),
        cube_block("l73-silverwall", "// Level 73: the Silver Castle's masonry, bright silver-grey ashlar",
                   ["block/73/silverwall", "block/73/silverwall-2"], "Stone", "game:walk/stone*", "game:block/rock-hit-pickaxe", 8,
                   {"attributes": {"l73Fixed": True}}),
        sconce_block(),
        cube_block("l73-burnt", "// Level 73: the blackened fields, charred near-black earth flecked with ash",
                   ["block/73/burnt", "block/73/burnt-2"], "Soil", "game:walk/gravel*", "game:block/dirt*", 2.5),
        cube_block("l73-crust", "// Level 73: a crust of dried blood on the earth, cracked into plates",
                   ["block/73/crust", "block/73/crust-2"], "Soil", "game:walk/gravel*", "game:block/dirt*", 2.5),
        deadgrass_block(),
        cube_block("l73-bone", "// Level 73: the Great Hound's bones, bleached and weathered (it never breaks)",
                   ["block/73/bone", "block/73/bone-2"], "Stone", "game:walk/stone*", "game:block/rock-hit-pickaxe", 6,
                   {"attributes": {"l73Fixed": True}}),
        lined_block("l73-wainscot", "block/73/wainscot", "// Level 73: the keep's walls at floor height, mahogany panelling on the room's side"),
        lined_block("l73-damask", "block/73/damask", "// Level 73: the keep's walls above the panelling, red damask wallpaper on the room's side"),
    ]
    for comment, b in blocks:
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    write_json(os.path.join(ASSETS, "shapes", "block", "73", "sconce.json"), None, sconce_shape())
    # The castle's furnishings (gen_73_castle.py)
    n_tex = castle.textures(save)
    for comment, b in castle.blocktypes():
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    n_shapes = castle.shapes(write_json, os.path.join(ASSETS, "shapes", "block", "73"))
    # Round 3's furnishings and landscape pieces (gen_73_interior.py)
    n_tex += interior.textures(save)
    for comment, b in interior.blocktypes():
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    n_shapes += interior.shapes(write_json, os.path.join(ASSETS, "shapes", "block", "73"))
    # Round 4's asset-quality pass (2026-11-02): the castle's outside (gen_73_r4_castle.py), the furnishings (gen_73_r4_props.py)
    for mod in (r4castle, r4props):
        n_tex += mod.textures(save)
        for comment, b in mod.blocktypes():
            write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
        n_shapes += mod.shapes(write_json, os.path.join(ASSETS, "shapes", "block", "73"))
    # The ways in and out (gen_73_links.py): the Gloom's ground and murk, the north door
    n_tex += links.textures(save)
    for comment, b in links.blocktypes():
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    n_shapes += links.shapes(write_json, os.path.join(ASSETS, "shapes", "block", "73"))
    write_lang()
    print(f"gen_73: {22 + n_tex} textures, {12 + len(castle.blocktypes()) + len(links.blocktypes())} blocktypes, {1 + n_shapes} shapes, lang")


if __name__ == "__main__":
    main()
