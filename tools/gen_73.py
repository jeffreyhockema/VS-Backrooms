"""Level 73, "The Redlands" (experimental): its six blocks, their textures, the sconce's model, the moon's picture, and
its lang keys. Run under the asset lock: bash tools/locked.sh run python tools/gen_73.py

Writes assets/backrooms/blocktypes/73/l73-*.json, textures/block/73/*.png, shapes/block/73/sconce.json,
textures/environment/l73-moon.png, and the level's keys in lang/en.json (between the Level 73 lines, in place).

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
    box = {"x1": 0.3, "y1": 0.25, "z1": 0.5, "x2": 0.7, "y2": 0.8, "z2": 1}
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
        "resistance": 1.5,
        "collisionbox": None,
        "selectionboxByType": {f"*-{s}": dict(box, rotateY=rot[s]) for s in sides},
        "drops": [],
        "sounds": {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
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
    return {
        "textureWidth": 16, "textureHeight": 16,
        "textures": {"iron": "backrooms:block/73/sconce-iron", "glow": "backrooms:block/73/sconce-glow"},
        "elements": [
            box("Plate", [6, 4, 15], [10, 12, 16], "#iron"),
            box("Arm", [7.5, 9, 12.5], [8.5, 10, 15], "#iron"),
            box("Base", [5.5, 4.5, 8.5], [10.5, 5.5, 13.5], "#iron"),
            box("Glass", [6.5, 5.5, 9.5], [9.5, 10, 12.5], "#glow", glow=180),
            box("Cap", [5.5, 10, 8.5], [10.5, 11, 13.5], "#iron"),
            box("Finial", [7.5, 11, 10.5], [8.5, 12.5, 11.5], "#iron"),
        ],
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
]


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
                   ["block/73/silverwall", "block/73/silverwall-2"], "Stone", "game:walk/stone*", "game:block/rock-hit-pickaxe", 8),
        sconce_block(),
    ]
    for comment, b in blocks:
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    write_json(os.path.join(ASSETS, "shapes", "block", "73", "sconce.json"), None, sconce_shape())
    write_lang()
    print("gen_73: 11 textures, 6 blocktypes, 1 shape, lang")


if __name__ == "__main__":
    main()
