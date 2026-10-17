"""Level 55, "Land of Ice" (experimental): its six blocks, their textures and its lang keys. Run under the asset lock:
bash tools/locked.sh run python tools/gen_55.py

Writes assets/backrooms/blocktypes/55/l55-*.json, textures/block/55/*.png, and the level's keys in lang/en.json (between
its level-25 line and the next level's, in place). The lamp reuses Level 73's sconce model (shapes/block/73/sconce.json)
with textures of its own.

Wind crust is white snow packed into fine ripples by the wind, faint blue shadow in the grooves. Blue ice is deep glacier
blue-green with white bubble streaks and hairline cracks (the cave's glowing walls a paler, brighter cut of it). The rim
is grey rock furred with white rime. The hut is weathered grey planks with frost in the grain. The lamp is black iron
round a warm yellow glow.
"""
import json
import math
import os
import random
import re

from PIL import Image

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


def over(img, field, colour, lo, hi, strength=1.0):
    """Mixes `colour` in where a field in -1..1 rises from lo to hi."""
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (field[y][x] - lo) / (hi - lo)
            if t <= 0:
                continue
            r, g, b, a = px[x, y]
            px[x, y] = M.rgba(M.mix((r, g, b), colour, min(1.0, t) * strength))
    return img


def flecks(img, seed, n, colour, strength=0.8):
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.mix(px[x, y], colour, strength * rng.uniform(0.6, 1.0)))
    return img


def hairline(img, seed, colour, length=(10, 22), strength=0.7):
    """A thin wandering crack, lighter than the ice round it, wrapping."""
    rng = random.Random(seed)
    px = img.load()
    x, y = rng.uniform(0, S), rng.uniform(0, S)
    a = rng.uniform(0, 2 * math.pi)
    for _ in range(int(rng.uniform(*length))):
        X, Y = int(x) % S, int(y) % S
        px[X, Y] = M.rgba(M.mix(px[X, Y], colour, strength))
        a += rng.uniform(-0.5, 0.5)
        x += math.cos(a)
        y += math.sin(a)
    return img


# ---------------- Textures ----------------

def windcrust(seed):
    """Packed snow in fine ripples (whole-number frequencies across the block so it tiles), blue in the grooves."""
    img = M.noise_hv((230, 236, 242), amp=3, seed=seed, mottle=5, hue=1)
    warp = M.fbm(S, seed + 1, (16, 8))
    rng = random.Random(seed + 2)
    k, tilt = rng.choice((3, 4)), rng.choice((0, 1))
    px = img.load()
    for y in range(S):
        for x in range(S):
            w = math.sin(2 * math.pi * (k * y + tilt * x) / S + 2.2 * warp[y][x])
            r, g, b, a = px[x, y]
            if w > 0.55:  # the groove's shadow
                px[x, y] = M.rgba(M.mix((r, g, b), (182, 200, 224), (w - 0.55) * 1.6))
            elif w < -0.75:  # the ripple's sunlit crest
                px[x, y] = M.rgba(M.mix((r, g, b), (250, 252, 255), 0.6))
    flecks(img, seed + 3, 14, (204, 216, 232), 0.5)
    return img


def blueice(seed, glow=False):
    base = (122, 190, 222) if glow else (72, 142, 178)
    img = M.noise_hv(base, amp=3, seed=seed, mottle=10, hue=3)
    depth = M.fbm(S, seed + 1, (16, 8, 4))
    over(img, depth, (40, 98, 140) if not glow else (86, 160, 204), 0.25, 0.9, 0.7)  # darker, deeper patches
    # Bubble streaks: short white runs along one direction, the way air is trapped in glacier ice
    rng = random.Random(seed + 2)
    px = img.load()
    for _ in range(9):
        x, y, L = rng.uniform(0, S), rng.uniform(0, S), rng.randint(3, 8)
        for i in range(L):
            X, Y = int(x + i) % S, int(y + 0.3 * i) % S
            px[X, Y] = M.rgba(M.mix(px[X, Y], (236, 246, 252), rng.uniform(0.4, 0.8)))
    flecks(img, seed + 3, 18, (226, 242, 250), 0.6)
    hairline(img, seed + 4, (196, 228, 244))
    hairline(img, seed + 5, (196, 228, 244), length=(6, 12), strength=0.5)
    return img


def rimecliff(seed):
    img = texlib.marble((112, 116, 122), (164, 170, 176), seed, veins=1, sharpness=7, mottle=0.08, turbulence=3.0)
    M.grime(img, 0.12, seed=seed + 1, color=(70, 72, 78), cover=0.5)
    rime = M.fbm(S, seed + 2, (16, 8, 4))
    over(img, rime, (226, 232, 238), 0.05, 0.45, 0.95)
    flecks(img, seed + 3, 30, (240, 244, 248), 0.7)
    return img


def frostplank(seed):
    img = M.wood_planks(seed=seed, base=(124, 118, 110), planks=4, grain=4, contrast=0.8, flecks=0.8, per_plank=9,
                        gap=(58, 56, 56))
    frost = M.fbm(S, seed + 1, (16, 8, 4))
    over(img, frost, (214, 222, 230), 0.15, 0.8, 0.75)
    px = img.load()
    for y in range(S):  # frost gathers along each board's lower edge
        if y % 8 in (6, 7):
            for x in range(S):
                r, g, b, a = px[x, y]
                px[x, y] = M.rgba(M.mix((r, g, b), (232, 238, 244), 0.35))
    flecks(img, seed + 2, 24, (244, 248, 252), 0.6)
    return img


def lamp_iron(seed):
    img = M.noise_hv((36, 36, 40), amp=3, seed=seed, mottle=5, hue=1)
    flecks(img, seed + 1, 20, (190, 200, 212), 0.35)  # rime on the iron
    return img


def lamp_glow(seed):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            t = y / (S - 1)
            c = M.mix((196, 120, 40), (255, 226, 150), t)
            d = rng.uniform(-6, 6)
            px[x, y] = M.rgba((c[0] + d, c[1] + d, c[2] + d * 0.5))
    for x in (0, 1, 15, 16, 30, 31):
        for y in range(S):
            px[x, y] = M.rgba((30, 30, 34))
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


def lamp_block():
    sides = ["north", "east", "south", "west"]
    rot = {"north": 0, "east": 270, "south": 180, "west": 90}
    box = {"x1": 0.3, "y1": 0.25, "z1": 0.5, "x2": 0.7, "y2": 0.8, "z2": 1}
    return ("// Level 55: an iron wall lamp in the research hut (the wall to its back, south for -north), a warm yellow glow (Level 73's sconce model)", {
        "code": "l55-lamp",
        "variantgroups": [{"code": "side", "states": sides}],
        "shapeByType": {f"*-{s}": {"base": "block/73/sconce", "rotateY": rot[s]} for s in sides},
        "textures": {"iron": {"base": "block/55/lamp-iron"}, "glow": {"base": "block/55/lamp-glow"}},
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal",
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "lightHsv": [7, 4, 9],
        "resistance": 1.5,
        "collisionbox": None,
        "selectionboxByType": {f"*-{s}": dict(box, rotateY=rot[s]) for s in sides},
        "drops": [],
        "sounds": {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
    })


def write_json(path, comment, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write(comment + "\n")
        json.dump(obj, f, indent="\t")
        f.write("\n")


# ---------------- Lang ----------------

LANG = [
    ("level-25", "Level 55: Land of Ice"),
    ("levelhint-25", "Do not stop walking. The cold does not."),
    ("levelname-25", "Level 55"),
    ("level-2501", "The Research Hut"),
    ("levelhint-2501", "Someone left in a hurry. The stove is still warm."),
    ("levelname-2501", "Level 55, the Research Hut"),
    ("level-2502", "The Ice Cave"),
    ("levelhint-2502", "Blue light, no wind. Nothing here is alive."),
    ("levelname-2502", "Level 55, the Ice Cave"),
    ("block-l55-windcrust", "Wind Crust"),
    ("block-l55-blueice", "Blue Glacier Ice"),
    ("block-l55-glowice", "Glowing Blue Ice"),
    ("block-l55-rimecliff", "Rime-Coated Rock"),
    ("block-l55-frostplank", "Frosted Planks"),
    ("block-l55-lamp-*", "Iron Lamp"),
]


def write_lang():
    """Replaces the level's lines in en.json in place (at its level-25 line; any of its keys elsewhere are dropped),
    keeping the file's line endings and everything else byte for byte."""
    path = os.path.join(ASSETS, "lang", "en.json")
    raw = open(path, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    ours = {k for k, _ in LANG}
    key_re = re.compile(rb'^\t"([^"]+)":')
    start = next(i for i, l in enumerate(lines) if l.startswith(b'\t"level-25":'))
    kept = []
    for i, l in enumerate(lines):
        m = key_re.match(l)
        if m and m.group(1).decode() in ours and i != start:
            continue
        kept.append(l)
    at = next(i for i, l in enumerate(kept) if l.startswith(b'\t"level-25":'))
    new = [b'\t' + json.dumps(k).encode() + b': ' + json.dumps(v, ensure_ascii=False).encode() + b',' for k, v in LANG]
    kept[at:at + 1] = new
    open(path, "wb").write(nl.join(kept))


def main():
    save(windcrust(5510), "block/55/windcrust")
    save(windcrust(5511), "block/55/windcrust-2")
    save(blueice(5520), "block/55/blueice")
    save(blueice(5521), "block/55/blueice-2")
    save(blueice(5522, glow=True), "block/55/glowice")
    save(rimecliff(5530), "block/55/rimecliff")
    save(rimecliff(5531), "block/55/rimecliff-2")
    save(frostplank(5540), "block/55/frostplank")
    save(lamp_iron(5550), "block/55/lamp-iron")
    save(lamp_glow(5551), "block/55/lamp-glow")

    bt = os.path.join(ASSETS, "blocktypes", "55")
    ice_sounds = {"walk": "game:walk/ice*", "place": "game:block/ice", "break": "game:block/ice", "hit": "game:block/ice"}
    blocks = [
        cube_block("l55-windcrust", "// Level 55: snow packed hard into fine ripples by the wind (the common walkable crust)",
                   ["block/55/windcrust", "block/55/windcrust-2"], "Snow", "game:walk/snow*", "game:block/snow", 2.0),
        cube_block("l55-blueice", "// Level 55: deep glacier blue ice (crevasse walls, steep faces, the cave's dome); slippery as vanilla ice",
                   ["block/55/blueice", "block/55/blueice-2"], "Ice", "game:walk/ice*", "game:block/ice", 3.0,
                   {"dragMultiplier": 0.02, "sounds": ice_sounds}),
        cube_block("l55-glowice", "// Level 55: the ice cave's walls and ceiling, a paler blue that glows faintly",
                   ["block/55/glowice"], "Ice", "game:walk/ice*", "game:block/ice", 3.0,
                   {"dragMultiplier": 0.02, "sounds": ice_sounds, "lightHsv": [40, 3, 4], "lightAbsorption": 0, "vertexFlags": {"glowLevel": 40}}),
        cube_block("l55-rimecliff", "// Level 55: grey rock furred with white rime (the region's rim)",
                   ["block/55/rimecliff", "block/55/rimecliff-2"], "Stone", "game:walk/stone*", "game:block/rock-hit-pickaxe", 8),
        cube_block("l55-frostplank", "// Level 55: the research hut's weathered grey planks, frost in the grain",
                   ["block/55/frostplank"], "Wood", "game:walk/wood*", "game:block/planks", 2.5),
        lamp_block(),
    ]
    for comment, b in blocks:
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    write_lang()
    print("gen_55: 10 textures, 6 blocktypes, lang")


if __name__ == "__main__":
    main()
