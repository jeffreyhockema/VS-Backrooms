"""Level ! "Run For Your Life!": every asset in docs/design/new-levels/run-plan.md section 7 (and its "Manifest changes").

One long hospital hallway lit only by red EXIT signs: pale institutional walls with a wooden crash rail, white
speckled vinyl, white acoustic ceiling tiles, grey steel doors on both sides, red fire doors at the ends, a chained
door at the start, the furniture a hospital leaves in its corridors, and a blue Safe Zone. Plus the Energy Bar, the
sounds (the alarm, the horde, the doors) and the English names.

Run from the repo root, under the asset lock (it rewrites lang/en.json):
    bash tools/locked.sh run python tools/gen_run.py
Everything is written to the level's own folders (block/run/, blocktypes/run/, item/run/, sounds/*/run/).
"""
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from PIL import Image, ImageDraw

import detail_kit as K
from detail_kit import ASSETS, CLOTH, GLASS, LANG, METAL, ROTATE, SIDES, STONE, WOOD, T, bx, seed_of, turn, write_json
from gen_deep import TRANSFORMS, drops, threshold
import gen_detail
from gen_entity_sounds import RATE, band, place, seconds, thud, vowel
from gen_level_sounds import write as write_sound

S = 32
TAG = "run"
MINE = set()  # texture keys made here (block/run/<key>)


# ======================= Plumbing: our own folders =======================

def tpath(key):
    if key in MINE:
        return f"backrooms:block/{TAG}/{key}"
    if key in K.EXT:
        return K.EXT[key]
    return f"backrooms:block/detail/{key}"


def shape(name, elements):
    keys = set()
    for e in elements:
        for face in e["faces"].values():
            keys.add(face["texture"][1:])
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in sorted(keys)}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", "block", TAG, name + ".json"), data)
    return f"block/{TAG}/{name}"


def block(code, data, comment=None):
    data = dict({"code": code}, **data)
    write_json(os.path.join(ASSETS, "blocktypes", TAG, code + ".json"), data, comment)


# detail_kit's prop() looks these up at call time: point it at our folders
K.shape = shape
K.block = block
prop = K.prop
name = K.name


def save(img, key):
    T.save(img, f"block/{TAG}/{key}.png")
    MINE.add(key)


def tex(key):
    """The path of one of our textures, for a cube block."""
    return f"block/{TAG}/{key}"


def rgb(h, a=255):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255, a)


def clamp(v):
    return max(0, min(255, int(v)))


def noise(color, n, key, size=S):
    return T.noise_fill(rgb(color)[:3], n, seed_of(key), size)


def shade(c, f):
    return tuple(clamp(v * f) for v in c[:3]) + (c[3] if len(c) > 3 else 255,)


def mix(c1, c2, t):
    return tuple(clamp(c1[k] + (c2[k] - c1[k]) * t) for k in range(3)) + (255,)


def tint(img, color, t, box=None):
    """Blends a rectangle of the image toward a colour."""
    px = img.load()
    x0, y0, x1, y1 = box or (0, 0, img.width, img.height)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = mix(px[x, y], color, t)


def grain(img, key, amount=3, vertical=True, streak=0.35):
    """Brushed metal or wood grain: per-row (or per-column) offsets with a little noise."""
    rng = random.Random(seed_of(key))
    px = img.load()
    w, h = img.size
    lines = [rng.uniform(-amount, amount) for _ in range(w if vertical else h)]
    for y in range(h):
        for x in range(w):
            d = lines[x if vertical else y] * streak + rng.uniform(-amount, amount) * (1 - streak)
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d), a)
    return img


def speckle(img, key, share, color, size=1):
    rng = random.Random(seed_of(key))
    px = img.load()
    w, h = img.size
    for _ in range(int(w * h * share)):
        x, y = rng.randrange(w), rng.randrange(h)
        for dy in range(size):
            for dx in range(size):
                px[(x + dx) % w, (y + dy) % h] = color
    return img


# ======================= Textures =======================

WALL = 0xD8DDD3
SAFEWALL = 0xC4D6E8


def paint(color, key):
    """Institutional wall paint: flat, with the fine stipple a roller leaves and the faintest mottling."""
    img = noise(color, 2, key)
    rng = random.Random(seed_of(key + "s"))
    px = img.load()
    for _ in range(90):
        x, y = rng.randrange(S), rng.randrange(S)
        d = rng.choice((-3, -2, 3))
        r, g, b, a = px[x, y]
        px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d), a)
    T.blotch(img, (rng.randrange(S), rng.randrange(S)), 12, shade(rgb(color), 0.97)[:3], 0.5, seed_of(key + "m"))
    return img


def cove(img, color, key, scuffs=True):
    """A vinyl cove base 2 px high at the foot of the wall, and the scuffs of trolleys and shoes above it."""
    d = ImageDraw.Draw(img)
    d.rectangle([0, S - 2, S - 1, S - 1], fill=rgb(color))
    d.line([0, S - 3, S - 1, S - 3], fill=shade(rgb(color), 1.25))
    if scuffs:
        rng = random.Random(seed_of(key))
        for _ in range(5):
            x, y = rng.randrange(S), rng.randint(17, 26)
            n = rng.randint(2, 5)
            for k in range(n):
                xx = (x + k) % S
                img.putpixel((xx, y + (k // 3)), shade(img.getpixel((xx, y)), 0.86))
        for _ in range(3):  # a dark trolley rub low on the wall
            x = rng.randrange(S)
            for k in range(rng.randint(4, 9)):
                img.putpixel(((x + k) % S, 24 + rng.randint(0, 1)), (96, 96, 92, 255))
    return img


def vinyl(color, key, seam=True):
    """Speckled hospital sheet vinyl: 3 % dark chips, 2 % light ones, a faint seam where two sheets meet."""
    img = noise(color, 3, key)
    speckle(img, key + "d", 0.03, rgb(0x6E6E6A))
    speckle(img, key + "l", 0.02, rgb(0xF0F0EA))
    speckle(img, key + "c", 0.004, shade(rgb(color), 0.7), 2)
    if seam:
        d = ImageDraw.Draw(img)
        d.line([0, 0, 0, S - 1], fill=shade(rgb(color), 0.9))
    return img


GLYPHS = {
    "E": ["1111", "1000", "1000", "1110", "1000", "1000", "1111"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
}
# 3 x 5 capitals for the Energy Bar's wrapper
SMALL = {"E": ["111", "100", "110", "100", "111"], "N": ["101", "111", "111", "111", "101"], "R": ["110", "101", "110", "101", "101"],
         "G": ["011", "100", "101", "101", "011"], "Y": ["101", "101", "010", "010", "010"]}
CHEVRON_R = ["100", "110", "011", "001", "011", "110", "100"]
CHEVRON_L = [r[::-1] for r in CHEVRON_R]


def glyphs(img, rows_list, x, y, color, gap=1):
    px = img.load()
    for rows in rows_list:
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                if c == "1":
                    px[x + i, y + j] = color
        x += len(rows[0]) + gap
    return x


def exit_face(state):
    """The face of a lit EXIT sign: red letters on near-black, a chevron either side. Drawn in rows 9-22 (the face's
    UV band), letters 7 px high."""
    bg = {"lit": 0x1C0605, "dim": 0x120403, "bright": 0x260807, "off": 0x120707, "dead": 0x0C0B0A}[state]
    fg = {"lit": 0xFF2A1E, "dim": 0x961410, "bright": 0xFF5A48, "off": 0x4A1612, "dead": 0x2E1A16}[state]
    img = noise(bg, 2, "exitface" + state)
    x = glyphs(img, [CHEVRON_L], 2, 12, rgb(fg))
    if state == "dim":
        # (0.514.0) Over a false exit: "a little darker", and its X has burnt out, E IT, so it can be learnt
        dead = rgb({"dim": 0x3A100C}[state])
        for c in "EXIT":
            x = glyphs(img, [GLYPHS[c]], x, 12, dead if c == "X" else rgb(fg)) + 0
    else:
        x = glyphs(img, [GLYPHS[c] for c in "EXIT"], x, 12, rgb(fg))
    glyphs(img, [CHEVRON_R], x, 12, rgb(fg))
    px = img.load()
    if state in ("lit", "bright"):
        # A glow bleeding round the letters
        halo = shade(rgb(fg), 0.35)
        for y in range(10, 22):
            for x in range(3, 29):
                if px[x, y][0] < 80 and any(px[x + dx, y + dy][0] > 200 for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                    px[x, y] = mix(px[x, y], halo, 0.8)
    if state == "dead":
        # Soot and a cracked lens
        rng = random.Random(seed_of("exitdead"))
        T.blotch(img, (16, 12), 10, (8, 8, 8), 0.7, seed_of("soot"))
        x, y = 9, 9
        for _ in range(14):
            px[x, y] = (150, 146, 140, 255)
            x += rng.choice((0, 1, 1))
            y += 1
        x, y = 22, 22
        for _ in range(9):
            px[x, y] = (120, 116, 110, 255)
            x -= rng.choice((0, 1))
            y -= 1
    return img


def door_leaf(color, key, n=4, vertical=True):
    img = noise(color, 2, key)
    return grain(img, key + "g", n, vertical)


def split_tall(img):
    """A 32x64 picture of a two-block door into its lower and upper halves."""
    return img.crop((0, S, S, 2 * S)), img.crop((0, 0, S, S))


def textures():
    # ---- Walls ----
    wall = paint(WALL, "runwall")
    save(wall, "wall")
    save(cove(paint(WALL, "runwall"), 0x5E6A62, "runwallbase"), "wallbase")
    img = noise(0x1A1714, 6, "runvoid")
    T.blotch(img, (10, 22), 12, (40, 30, 24), 0.4, seed_of("runvoidb"))
    save(img, "void")
    # The crash rail: warm oak along the grain, a rounded highlight on top
    img = grain(noise(0x8A5A32, 4, "rail"), "railg", 5, vertical=False)
    save(img, "railwood")
    img = noise(0xA87442, 3, "railtop")
    save(grain(img, "railtopg", 4, vertical=False), "railtop")
    save(grain(noise(0x8E9396, 3, "steel"), "steelg", 4), "steel")
    save(noise(0x5C6164, 3, "steelframe"), "steelframe")
    save(grain(noise(0xB8BCC0, 3, "chrome"), "chromeg", 6, streak=0.6), "chrome")
    save(noise(0x1E1E1E, 3, "rubber"), "rubber")
    # Emergency beacons
    for state, c, hot in (("lit", 0xC81010, 0xFF6A50), ("dark", 0x3A0A0A, 0x4A1210)):
        img = noise(c, 3, "beacon" + state)
        T.blotch(img, (16, 10), 10, rgb(hot)[:3], 0.8, seed_of("beaconhot" + state))
        save(img, "beacon" + state)
    save(noise(0x2A2A2A, 3, "beaconbase"), "beaconbase")
    save(noise(0x4A4A4A, 4, "wire"), "wire")

    # ---- Floor ----
    save(vinyl(0xD4D4CC, "vinyl"), "vinyl")
    for side, box in (("north", (0, 0, S - 1, 7)), ("east", (S - 8, 0, S - 1, S - 1)),
                      ("south", (0, S - 8, S - 1, S - 1)), ("west", (0, 0, 7, S - 1))):
        img = vinyl(0xD4D4CC, "vinyl")
        band_ = vinyl(0x3E4A55, "border", seam=False)
        mask = Image.new("L", (S, S), 0)
        ImageDraw.Draw(mask).rectangle(box, fill=255)
        img.paste(band_, (0, 0), mask)
        # A darker line where the band meets the field
        d = ImageDraw.Draw(img)
        x0, y0, x1, y1 = box
        line = {"north": [0, 8, S - 1, 8], "south": [0, S - 9, S - 1, S - 9],
                "east": [S - 9, 0, S - 9, S - 1], "west": [8, 0, 8, S - 1]}[side]
        d.line(line, fill=rgb(0x2C343C))
        save(img, f"border-{side}")
    # Scuffed: heel marks, two drag smears, three claw scratches
    img = vinyl(0xD4D4CC, "vinyl")
    rng = random.Random(seed_of("scuffed"))
    px = img.load()
    for _ in range(9):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(2, 5)):
            px[(x + k) % S, (y + (k * k) // 6) % S] = (28, 28, 28, 255)
    for x0 in (7, 20):
        for y in range(S):
            for dx in range(-2, 3):
                x = (x0 + dx + y // 8) % S
                if rng.random() < 0.75 - abs(dx) * 0.2:
                    px[x, y] = mix(px[x, y], rgb(0x4A2A20), 0.6)
    for k in range(3):
        for t in range(18):
            x, y = 4 + k * 3 + t, 6 + t
            if 0 <= x < S and 0 <= y < S:
                px[x, y] = (246, 244, 238, 255)
                if x + 1 < S:
                    px[x + 1, y] = (120, 118, 112, 255)
    save(img, "scuffed")
    # Cracked: a dark branching crack with chipped edges, the warning before a hole
    img = vinyl(0xD4D4CC, "vinyl")
    rng = random.Random(seed_of("cracked"))
    px = img.load()

    def crack(x, y, dx, n, width):
        for _ in range(n):
            for w in range(width):
                xx, yy = int(x) % S, (int(y) + w) % S
                px[xx, yy] = (34, 32, 30, 255)
                for cx, cy in ((xx + 1, yy - 1), (xx - 1, yy + 1)):
                    if rng.random() < 0.3:
                        px[cx % S, cy % S] = (150, 148, 140, 255)
            x += 1
            y += dx + rng.uniform(-0.9, 0.9)
    crack(0, 14, 0.1, S, 2)
    crack(10, 15, -0.7, 12, 1)
    crack(20, 15, 0.8, 12, 1)
    crack(16, 14, -0.2, 8, 1)
    save(img, "cracked")
    save(vinyl(0xB4C2D2, "safefloor"), "safefloor")

    # ---- Ceiling: 2 x 2 white acoustic tiles to a block, a T-bar grid ----
    img = noise(0xE8E8E2, 3, "ceiltile")
    rng = random.Random(seed_of("ceilfiss"))
    px = img.load()
    for _ in range(46):
        x, y = rng.randrange(S), rng.randrange(S)
        for _ in range(rng.randint(1, 3)):
            px[x % S, y % S] = (206, 206, 198, 255)
            x += rng.choice((-1, 0, 1))
            y += rng.choice((0, 1))
    d = ImageDraw.Draw(img)
    for k in (0, 16):
        d.line([k, 0, k, S - 1], fill=rgb(0xCFCFC8))
        d.line([0, k, S - 1, k], fill=rgb(0xCFCFC8))
        d.line([k + 1, 1, k + 1, S - 1], fill=rgb(0xDADAD4))
    save(img, "ceiltile")
    img = noise(0x9A9C9A, 2, "diffuser")
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 3 == 0:
                px[x, y] = shade(px[x, y], 0.93)
    save(img, "diffuser")
    save(noise(0xDCDCD6, 2, "trofferframe"), "trofferframe")
    save(grain(noise(0x8C8F8C, 3, "ventmetal"), "ventg", 3, vertical=False), "ventmetal")
    save(noise(0x111111, 3, "duct"), "duct")
    save(noise(0xCFCFC8, 2, "tbar"), "tbar")

    # ---- EXIT signs ----
    save(noise(0x1A1A1A, 3, "exithousing"), "exithousing")
    for state in ("lit", "dim", "bright", "off", "dead"):
        save(exit_face(state), "exitface-" + state)

    # ---- Safe Zone ----
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dd = ((x - 15.5) ** 2 + (y - 15.5) ** 2) ** 0.5 / 22
            px[x, y] = mix(rgb(0xEEF6FF), rgb(0xC8DCF8), dd)
    save(img, "safelight")
    save(noise(0xE6EAEE, 2, "safepanelrim"), "safepanelrim")
    save(paint(SAFEWALL, "safewall"), "safewall")
    save(cove(paint(SAFEWALL, "safewall"), 0x5A6E86, "safewallbase", scuffs=False), "safewallbase")
    safe_sign()

    # ---- Doors ----
    for part in ("lower", "upper"):
        img = door_leaf(0x8E9396, "sidedoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x777C80))
        if part == "upper":
            d.rectangle([11, 5, 20, 18], fill=rgb(0x3A3F42))
            d.rectangle([12, 6, 19, 17], fill=rgb(0x1C2226))
            for k in range(12, 20, 3):
                d.line([k, 6, k, 17], fill=rgb(0x5A6368))
            for k in range(7, 18, 3):
                d.line([12, k, 19, k], fill=rgb(0x5A6368))
            d.line([13, 7, 15, 9], fill=rgb(0x4A565C))  # a glint
        else:
            d.rectangle([1, 24, S - 2, S - 2], fill=rgb(0xA7ABAE))
            for x in (3, S - 4):
                d.point([(x, 26), (x, S - 3)], fill=rgb(0x5C6164))
        save(img, f"sidedoor-{part}")
        dented = img.copy()
        rng = random.Random(seed_of("dent" + part))
        px = dented.load()
        if part == "lower":
            # The dents of blows from the other side: dark crescents, bright ridges, paint gone in scratches
            for cx, cy, r in ((16, 8, 7), (10, 14, 4), (21, 15, 5)):
                for y in range(S):
                    for x in range(S):
                        dd = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                        if r - 1.5 < dd < r:
                            px[x, y] = shade(px[x, y], 0.7 if y > cy else 1.15)
        for _ in range(7):
            x, y = rng.randrange(4, S - 4), rng.randrange(2, S - 6)
            for k in range(rng.randint(4, 9)):
                if 0 <= x + k < S and 0 <= y + k // 2 < S:
                    px[x + k, y + k // 2] = (196, 198, 196, 255)
        T.blotch(dented, (rng.randrange(S), rng.randrange(S)), 7, (106, 58, 32), 0.35, seed_of("dentrust" + part))
        save(dented, f"sidedoor-dented-{part}")
    save(door_leaf(0x878C8F, "sidedoorback"), "sidedoor-back")
    save(noise(0xA7ABAE, 2, "pushplate"), "pushplate")
    save(noise(0x0A0A0A, 2, "doorway"), "doorway")

    # Fire doors: red, scuffed to the primer, a stencilled EXIT
    big = Image.new("RGBA", (S, 2 * S))
    big.paste(door_leaf(0x9E1C18, "exitdoorhi", 3), (0, 0))
    big.paste(door_leaf(0x9E1C18, "exitdoorlo", 3), (0, S))
    rng = random.Random(seed_of("exitchips"))
    px = big.load()
    for _ in range(30):
        x, y = rng.randrange(S), rng.randrange(2 * S)
        for k in range(rng.randint(1, 3)):
            px[(x + k) % S, y] = (138, 132, 124, 255)
    d = ImageDraw.Draw(big)
    d.rectangle([0, 0, S - 1, 2 * S - 1], outline=rgb(0x7A1412))
    glyphs(big, [GLYPHS[c] for c in "EXIT"], 6, 10, (236, 230, 220, 255))
    d.rectangle([1, 2 * S - 8, S - 2, 2 * S - 2], fill=rgb(0x9C9FA2))  # kick plate
    lower, upper = split_tall(big)
    save(lower, "exitdoor-lower")
    save(upper, "exitdoor-upper")
    save(door_leaf(0x8E1814, "exitdoorback", 3), "exitdoor-back")
    # (0.514.0) The light under the real exit: pale warm daylight, brightest in the middle of the gap
    img = Image.new("RGBA", (S, 8))
    px = img.load()
    for y in range(8):
        for x in range(S):
            edge = min(x, S - 1 - x) / 6
            f = min(1.0, 0.72 + 0.28 * edge) * (1 - 0.06 * abs(y - 3.5) / 3.5)
            px[x, y] = (clamp(255 * f), clamp(246 * f), clamp(222 * f), 255)
    save(img, "exitdaylight")
    # The inside of the door you came in by: pale, with a huge red "!" painted across it, running
    big = Image.new("RGBA", (S, 2 * S))
    big.paste(door_leaf(0xD8D6CE, "markedhi", 2), (0, 0))
    big.paste(door_leaf(0xD8D6CE, "markedlo", 2), (0, S))
    T.blotch(big, (16, 50), 14, (180, 170, 150), 0.25, seed_of("markedgrime"))
    d = ImageDraw.Draw(big)
    red = rgb(0xE01810)
    d.polygon([(9, 4), (23, 4), (20, 38), (12, 38)], fill=red)
    d.ellipse([10, 44, 22, 56], fill=red)
    rng = random.Random(seed_of("drips"))
    for x0, y0 in ((13, 38), (17, 38), (19, 36), (14, 55), (19, 54), (10, 20), (22, 12)):
        n = rng.randint(3, 9)
        d.line([x0, y0, x0, min(2 * S - 2, y0 + n)], fill=red, width=1)
        d.point([(x0, min(2 * S - 2, y0 + n + 1))], fill=shade(red, 0.8))
    px = big.load()
    for _ in range(80):  # brush texture in the paint
        x, y = rng.randrange(S), rng.randrange(2 * S)
        if px[x, y][0] > 200 and px[x, y][1] < 60:
            px[x, y] = shade(px[x, y], rng.uniform(0.82, 1.08))
    d.rectangle([0, 0, S - 1, 2 * S - 1], outline=rgb(0x9A9890))
    lower, upper = split_tall(big)
    save(lower, "markeddoor-lower")
    save(upper, "markeddoor-upper")
    save(grain(noise(0xB4B8BC, 2, "panicbar"), "panicbarg", 5, vertical=False), "panicbar")

    # The chained door: steel run with rust from the top, battered
    big = Image.new("RGBA", (S, 2 * S))
    big.paste(door_leaf(0x8A8E90, "chainhi"), (0, 0))
    big.paste(door_leaf(0x8A8E90, "chainlo"), (0, S))
    rng = random.Random(seed_of("rust"))
    px = big.load()
    for _ in range(9):
        x, y, n = rng.randrange(S), rng.randrange(0, 20), rng.randint(10, 40)
        for k in range(n):
            if y + k < 2 * S:
                px[x, y + k] = mix(px[x, y + k], rgb(0x6A3A20), 0.7 * (1 - k / n))
    T.blotch(big, (8, 50), 9, (106, 58, 32), 0.4, seed_of("rustb"))
    d = ImageDraw.Draw(big)
    d.rectangle([0, 0, S - 1, 2 * S - 1], outline=rgb(0x5C6164))
    lower, upper = split_tall(big)
    save(lower, "chaindoor-lower")
    save(upper, "chaindoor-upper")
    img = noise(0x4A4A4A, 6, "chain")
    save(grain(img, "chaing", 5), "chain")
    save(noise(0x6E6A62, 4, "padlock"), "padlock")
    save(noise(0xB0A060, 3, "shackle"), "shackle")

    # The hallway door: a mid wood leaf (dark enough not to read as the lit hall beyond it), a dark steel frame; the
    # wired-glass vision panel, the kick plate and the lever are boxes of their own (hall_door)
    for part in ("lower", "upper"):
        img = door_leaf(0x8A6A48, "halldoor" + part, 4)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x5E4630))
        save(img, f"halldoor-{part}")
    save(door_leaf(0x84664A, "halldoorback", 4), "halldoor-back")
    save(noise(0x4A4E52, 3, "hallframe"), "hallframe")
    save(grain(noise(0xA4A8AA, 2, "hallkick"), "hallkickg", 3, vertical=False), "hallkick")
    # Wired glass: dark glass behind a diamond mesh of wire, in a steel bead
    img = noise(0x2A3236, 3, "wiredglass")
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                px[x, y] = rgb(0x8A9296)
    d = ImageDraw.Draw(img)
    d.line([4, 6, 10, 14], fill=rgb(0x5A666C))
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x9CA2A6), width=2)
    save(img, "wiredglass")

    # Medicine cabinet: white enamel, a mirror front with a streak, a small red cross
    img = noise(0xECECE6, 2, "cabinet")
    save(img, "cabinet")
    img = noise(0xECECE6, 2, "cabinetfront")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 9, S - 4, S - 3], fill=rgb(0xA8B4B8))
    for k in range(10):
        d.point([(8 + k, 26 - k), (9 + k, 26 - k)], fill=rgb(0xD0DADC))
    d.rectangle([14, 2, 17, 7], fill=rgb(0xD01818))
    d.rectangle([13, 3, 18, 6], fill=rgb(0xD01818))
    d.rectangle([3, 9, S - 4, S - 3], outline=rgb(0xC8C8C2))
    save(img, "cabinetfront")

    # ---- Props ----
    img = noise(0xE6E6E0, 2, "sheet")
    rng = random.Random(seed_of("sheetfold"))
    px = img.load()
    for _ in range(6):
        y = rng.randrange(S)
        for x in range(S):
            yy = (y + int(2 * math.sin(x / 5 + y))) % S
            px[x, yy] = shade(px[x, yy], 0.9)
    save(img, "sheet")
    save(noise(0x6E7276, 3, "gurneyframe"), "gurneyframe")
    save(grain(noise(0x202022, 3, "seatvinyl"), "seatv", 3, vertical=False), "seatvinyl")
    save(noise(0x4A4A4A, 4, "tyre"), "tyre")
    img = noise(0xDDEEEE, 3, "ivbag")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 9], fill=rgb(0xF0F6F6))
    d.rectangle([6, 14, 25, 24], fill=rgb(0xFFFFFF))
    d.line([8, 17, 22, 17], fill=rgb(0x3060A0))
    d.line([8, 20, 18, 20], fill=rgb(0x8A8A8A))
    save(img, "ivbag")
    img = noise(0x5E8C8A, 3, "chairplastic")
    T.blotch(img, (12, 10), 12, (120, 168, 164), 0.3, seed_of("chairhi"))
    save(img, "chairplastic")
    save(noise(0x3A3E42, 3, "beamsteel"), "beamsteel")
    # Crash cart: red drawers with yellow labels; its side; the defibrillator
    img = noise(0xB82820, 3, "cartfront")
    d = ImageDraw.Draw(img)
    for y in (6, 11, 16, 21, 26):
        d.line([1, y, S - 2, y], fill=rgb(0x7A1612))
        d.rectangle([3, y + 1, 8, y + 2], fill=rgb(0xF0C838))
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8C1C16))
    save(img, "cartfront")
    save(noise(0xB82820, 3, "cartside"), "cartside")
    img = noise(0x3A3A3A, 3, "defib")
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, 17, 14], fill=rgb(0x1A2A1E))
    d.line([7, 11, 9, 11, 10, 8, 11, 13, 12, 10, 16, 10], fill=rgb(0x40E060))
    d.rectangle([20, 7, 25, 12], fill=rgb(0xE0B020))
    save(img, "defib")
    # Steel shelving: blue powder coat with slotted uprights
    img = noise(0x2E5C9A, 3, "shelfblue")
    px = img.load()
    for y in range(1, S, 4):
        for x in range(S):
            if x % 8 in (3, 4):
                px[x, y] = shade(px[x, y], 0.6)
    save(img, "shelfblue")
    save(noise(0xA07A4A, 5, "runbox"), "runbox")
    img = noise(0xA07A4A, 5, "runboxtop")
    ImageDraw.Draw(img).rectangle([13, 0, 18, S - 1], fill=rgb(0xC8B080))
    save(img, "runboxtop")
    save(noise(0xC8201C, 3, "toyred"), "toyred")
    save(noise(0xF0C020, 3, "toyyellow"), "toyyellow")
    save(noise(0xE07020, 4, "cord"), "cord")
    save(noise(0x1A1A1A, 3, "plug"), "plug")
    # A runner's remains: a torn khaki pack, one sneaker, a smear on the floor
    img = noise(0x7A7048, 5, "pack")
    d = ImageDraw.Draw(img)
    d.line([5, 0, 5, S - 1], fill=rgb(0x4E4630), width=2)
    d.line([24, 0, 24, S - 1], fill=rgb(0x4E4630), width=2)
    d.polygon([(10, 14), (20, 12), (17, 22), (12, 20)], fill=rgb(0x2A2418))  # the tear
    save(img, "pack")
    save(noise(0x5A6A7E, 4, "sneaker"), "sneaker")
    save(noise(0xF0EEE8, 2, "sole"), "sole")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rng = random.Random(seed_of("smear"))
    px = img.load()
    for y in range(S):
        for x in range(S):
            # A long dark drag mark, ragged at its edges, darker where it starts
            w = 7 + 3 * math.sin(y / 4.0) + rng.uniform(-2, 2)
            cx = 14 + 4 * math.sin(y / 9.0)
            if abs(x - cx) < w * (0.5 + 0.5 * (1 - y / S)) and rng.random() < 0.9:
                t = 1 - y / S
                px[x, y] = (clamp(58 + 30 * (1 - t)), clamp(22 + 12 * (1 - t)), 18, 255)
    for k in range(4):  # finger streaks trailing off
        x = 8 + k * 5
        for y in range(22, S):
            if rng.random() < 0.8:
                px[x, y] = (70, 30, 22, 255)
    save(img, "smear")
    save(noise(0xC4C8CA, 3, "dish"), "dish")
    save(noise(0x2A2A2C, 3, "stoolseat"), "stoolseat")
    img = noise(0xD8CDB4, 3, "bedside")
    save(grain(img, "bedsideg", 3, vertical=False), "bedside")
    img = noise(0xD8CDB4, 3, "bedsidefront")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, S - 2], outline=rgb(0xB4A88E))
    save(img, "bedsidefront")
    # The privacy curtain: pale green, pleated; above it the open mesh band
    img = noise(0x9CC2A8, 3, "curtain")
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = shade(px[x, y], 0.9 + 0.12 * math.sin(x / S * 2 * math.pi * 2))
    save(img, "curtain")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 4):
        d.line([k, 0, k, S - 1], fill=rgb(0xE8ECE8))
        d.line([0, k, S - 1, k], fill=rgb(0xE8ECE8))
    save(img, "curtainmesh")
    # Wire shelving (white), and what is on it
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 3):
        d.line([k, 0, k, S - 1], fill=rgb(0xE4E4E0))
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xF0F0EC))
    save(img, "wireshelf")
    save(noise(0xE8E8E4, 2, "wirepost"), "wirepost")
    img = noise(0xE8DCC0, 3, "almondbottle")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, S - 1, 22], fill=rgb(0xF4F0E6))
    d.rectangle([0, 14, S - 1, 17], fill=rgb(0x6A8A3A))
    save(img, "almondbottle")
    save(noise(0x3A6AB8, 3, "bottlecap"), "bottlecap")
    img = noise(0x9AAAC0, 4, "foil")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 12, S - 1, 19], fill=rgb(0xE07A20))
    save(grain(img, "foilg", 5, vertical=False, streak=0.6), "foil")
    save(noise(0x7A7E80, 4, "cotblanket"), "cotblanket")
    img = noise(0xEDE9DC, 2, "pillow")
    save(img, "pillow")

    # ---- Level 2's wall that wasn't there: smooth new concrete, a thread of red light at its foot ----
    img = noise(0xB8B6B0, 2, "falsewall")
    save(img, "falsewall")
    img = Image.new("RGBA", (S, S), (255, 40, 24, 255))
    save(img, "redline")


def safe_sign():
    """WELCOME / to the safe zone. / Please take a break before / you continue running. White plate, blue letters,
    drawn at 4 px a voxel (the one place text has to be read) and cut in two for the two wall blocks."""
    W, H = 112, 48
    img = Image.new("RGBA", (W, H), (250, 252, 255, 255))
    d = ImageDraw.Draw(img)
    blue = (30, 74, 150, 255)
    d.rectangle([0, 0, W - 1, H - 1], outline=blue, width=2)
    d.rectangle([3, 3, W - 4, 15], fill=blue)
    T.text_img(img, "WELCOME", (3, 3, W - 3, 16), (255, 255, 255, 255), 11)
    T.text_img(img, "to the safe zone.", (3, 17, W - 3, 27), blue, 8)
    T.text_img(img, "Please take a break before", (3, 27, W - 3, 37), blue, 7)
    T.text_img(img, "you continue running.", (3, 36, W - 3, 46), blue, 7)
    for half, x0 in (("l", 0), ("r", W // 2)):
        out = Image.new("RGBA", (64, 64), (250, 252, 255, 255))
        out.paste(img.crop((x0, 0, x0 + W // 2, H)), (0, 0))
        save(out, f"safesign-{half}")


def item_textures():
    # The Energy Bar's wrapper: silver-blue foil, an orange stripe, ENERGY in small caps, crimped ends
    img = noise(0x9AAAC0, 4, "barfoil")
    grain(img, "barfoilg", 6, vertical=False, streak=0.6)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 7, S - 1, 9], fill=rgb(0xE07A20))
    glyphs(img, [SMALL[c] for c in "ENERGY"], 4, 1, rgb(0x1E2846))
    for x in range(0, S, 2):  # the crimp band at the bottom of the sheet
        d.line([x, 12, x, 15], fill=rgb(0xC0CCDA))
    d.rectangle([0, 16, S - 1, S - 1], fill=rgb(0x8A9AB0))
    T.save(img, f"item/{TAG}/energybar.png")


# ======================= Blocks: structure =======================

def cube_type(code, english, states, textures_by_state, comment, material="Stone", sounds=STONE, json_states=None, extra=None):
    """A block whose plain states are cubes and whose other states are json shapes (shapes: {state: path})."""
    data = {"variantgroups": [{"code": "kind", "states": states}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "texturesByType": {}, "lightAbsorption": 99,
            "resistance": 99999, "drops": [], "sounds": sounds}
    for st, t in textures_by_state.items():
        data["texturesByType"][f"*-{st}"] = t
    if json_states:
        data["drawtypeByType"] = dict({f"*-{st}": "json" for st in json_states}, **{"*": "cube"})
        data["shapeByType"] = {f"*-{st}": v for st, v in json_states.items()}
        data["sidesolidByType"] = dict({f"*-{st}": {"all": False} for st in json_states}, **{"*": {"all": True}})
        data["sideopaqueByType"] = dict({f"*-{st}": {"all": False} for st in json_states}, **{"*": {"all": True}})
    if extra:
        data.update(extra)
    block(code, data, comment)


def all6(t):
    return {"all": {"base": tex(t)}}


def sides6(side_tex, cap_tex):
    return {f: {"base": tex(side_tex)} for f in ("north", "east", "south", "west")} | {"up": {"base": tex(cap_tex)}, "down": {"base": tex(cap_tex)}}


def rail(x0=0, x1=16):
    """The crash rail on a wall's north face: a rounded oak bar at hip height on two steel brackets."""
    return [bx("Rail", (x0, 12, -3), (x1, 14, -1), "railwood"),
            bx("RailTop", (x0, 14, -2.7), (x1, 14.5, -1.3), "railtop", faces=("north", "south", "up", "east", "west")),
            bx("RailBottom", (x0, 11.6, -2.7), (x1, 12, -1.3), "railunder", faces=("north", "south", "down", "east", "west")),
            # (tops a hair under the rail's, the right one clear of the end of a rail stopped short at x 13)
            bx("Bracket1", (3, 11, -2), (4, 13.95, -0.4), "steelframe"), bx("Bracket2", (11.9, 11, -2), (12.9, 13.95, -0.4), "steelframe"),
            # (B14) the round wall plate each bracket is screwed to
            bx("Plate1", (2.4, 10.4, -0.4), (4.6, 13.2, 0), "steelframe", faces=("north", "east", "west", "up", "down")),
            bx("Plate2", (11.3, 10.4, -0.4), (13.5, 13.2, 0), "steelframe", faces=("north", "east", "west", "up", "down"))]


def walls():
    wall = bx("Wall", (0, 0, 0), (16, 16, 16), "wallbase")
    shapes = {}
    path = shape("run-wall-rail", [wall] + rail())
    for s in SIDES:
        shapes[f"rail-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    # An outside corner: rails on the north and east faces, meeting round the corner in a mitre (the north rail runs on
    # to the east rail's front, the east one starts behind it)
    north = rail(0, 19)
    for e in north:
        if e["name"] in ("RailTop", "RailBottom"):
            e["to"][0] = 18.7
    east = rail(-1, 16)
    for e in east:
        if e["name"] in ("RailTop", "RailBottom"):
            e["from"][0] = -1.3
        e["faces"].pop("west", None)
    corner = [wall] + north + [dict(turn(e, 1), name=e["name"] + "E") for e in east]
    path = shape("run-wall-railcorner", corner)
    for s in SIDES:
        shapes[f"railcorner-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    # In an inside corner the rail stops against the front of the other wall's rail (the generator gives this to the
    # rail whose clockwise end is in the corner; the other runs on into the corner)
    path = shape("run-wall-railshort", [wall] + rail(0, 13))
    for s in SIDES:
        shapes[f"railshort-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    cube_type("run-wall", "Hospital Wall", ["plain", "base", "void"] + list(shapes),
              {"plain": all6("wall"), "base": sides6("wallbase", "wall"), "void": all6("void")},
              "Level !: the hallway's walls. plain above, base (cove base) at the floor, rail-<side> with the crash rail on "
              "that face (rel 1), railcorner-<side> on that face and the next one clockwise (an outside corner), railshort-<side> "
              "stopping short of the other rail in an inside corner, void (matte black: "
              "the antechamber behind the chained door, the fake exits' closets)",
              json_states=shapes)
    b14_versions("run-wall", {"plain": ("wall", "all"), "base": ("wallbase", "sides")},
                 {"*-rail*": "wallbase"}, WALL_WEIGHTS)
    name("run-wall-plain", "Hospital Wall")
    name("run-wall-base", "Hospital Wall")
    name("run-wall-rail-*", "Hospital Wall with Crash Rail")
    name("run-wall-railcorner-*", "Hospital Wall with Crash Rail")
    name("run-wall-void", "Dark Wall")

    # Emergency beacons: a red dome on a bracket high on the wall, with a wire guard. They flash (glow only) while
    # the alarm sounds: the block entity swaps the lit and dark meshes
    def beacon(lit):
        g = 220 if lit else 0
        return [bx("Wall", (0, 0, 0), (16, 16, 16), "wall"),
                bx("Plate", (5.5, 10, -0.5), (10.5, 15, 0), "beaconbase"),
                bx("Base", (5.5, 10.5, -3.5), (10.5, 11.5, -0.5), "beaconbase"),
                bx("Dome", (6, 11.5, -3.2), (10, 14.5, -0.8), "beaconlit" if lit else "beacondark", glow=g),
                bx("Cap", (6.5, 14.5, -2.7), (9.5, 15.5, -1.3), "beaconlit" if lit else "beacondark", glow=g),
                bx("GuardX", (5.6, 15.5, -2.25), (10.4, 16, -1.75), "wire"),
                bx("GuardZ", (7.75, 15.5, -3.6), (8.25, 16, -0.5), "wire"),
                bx("GuardL", (5.6, 11.5, -2.25), (6.1, 15.5, -1.75), "wire"),
                bx("GuardR", (9.9, 11.5, -2.25), (10.4, 15.5, -1.75), "wire")]
    by_type = {}
    for state in ("lit", "dark"):
        path = shape(f"run-wall-beacon-{state}", beacon(state == "lit"))
        for s in SIDES:
            by_type[f"*-{state}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("run-wall-beacon", {
        "variantgroups": [{"code": "state", "states": ["lit", "dark"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-lit-north"], "decorative": ["*-lit-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "entityClassByType": {"*-lit-*": "BackroomsRunBeacon"},
        "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "lightAbsorption": 99, "resistance": 99999, "drops": [], "sounds": STONE,
    }, "Level !: a wall block (rel 3) with an emergency beacon on face <side>. lit is placed; its block entity draws the "
       "dark mesh except during the quarter second of each flash. No block light: the flashing is glow only")
    name("run-wall-beacon-*", "Emergency Beacon")

    # The floor
    states = ["vinyl", "border-north", "border-east", "border-south", "border-west", "scuffed", "cracked", "safe"]
    texs = {"vinyl": {"all": {"base": tex("vinyl")}}, "safe": {"all": {"base": tex("safefloor")}}}
    for s in SIDES:
        texs[f"border-{s}"] = {"all": {"base": tex("vinyl")}, "up": {"base": tex(f"border-{s}")}}
    for k in ("scuffed", "cracked"):
        texs[k] = {"all": {"base": tex("vinyl")},
                   "up": {"base": tex(k), "alternates": [{"base": tex(k), "rotation": r} for r in (90, 180, 270)]}}
    cube_type("run-floor", "Vinyl Floor", states, texs,
              "Level !: speckled hospital vinyl; border-<side> has the dark band along that edge; scuffed, cracked (before a "
              "hole), safe (the Safe Zone's blue-grey)", material="Stone")
    b14_floor_versions()
    name("run-floor-*", "Vinyl Floor")
    name("run-floor-safe", "Safe Zone Floor")

    # The ceiling
    tile = "ceiltile"
    body = lambda y0: bx("Body", (0, y0, 0), (16, 16, 16), tile, faces=("north", "east", "south", "west", "up"))
    rim = lambda h, t: [bx("RimN", (0, 0, 0), (16, h, 1), t), bx("RimS", (0, 0, 15), (16, h, 16), t),
                        bx("RimW", (0, 0, 1), (1, h, 15), t), bx("RimE", (15, 0, 1), (16, h, 15), t)]
    dead = [body(2), bx("Diffuser", (1, 2, 1), (15, 2.01, 15), "diffuser", faces=("down",))] + rim(2, "trofferframe") + [
        bx("LouvreA", (1, 0.3, 5.2), (15, 2, 5.6), "trofferframe"), bx("LouvreB", (1, 0.3, 10.4), (15, 2, 10.8), "trofferframe"),
        bx("LouvreC", (7.8, 0.3, 1), (8.2, 2, 15), "trofferframe")]
    slats = [bx(f"Slat{k}", (1, 1, 1.6 + k * 2.3), (15, 2, 3.4 + k * 2.3), "ventmetal", rot=(30, 0, 0)) for k in range(6)]
    duct = [body(3), bx("Duct", (1, 3, 1), (15, 3.01, 15), "duct", faces=("down",))] + rim(3, "ventmetal")
    vent = duct + slats
    grille = [bx("Grille", (1, 1.5, 1), (15, 2.3, 15), "ventmetal", rot=(-70, 0, 0), origin=(8, 2, 15)),
              bx("GrilleSlats", (1.5, 1.2, 1.5), (14.5, 1.5, 14.5), "duct", rot=(-70, 0, 0), origin=(8, 2, 15))]
    shapes = {"panel-dead": {"base": shape("run-ceiling-panel-dead", dead)},
              "vent": {"base": shape("run-ceiling-vent", vent)},
              "vent-burst": {"base": shape("run-ceiling-vent-burst", duct + grille)}}
    # (B14) three versions of the 2 x 2 tiles, a faint stain in one block in six; not turned (the T-bar's lit half is on
    # the top and left of every block, so a turned block would put two lit halves side by side)
    ceil = [tex(tile)] + [tex(f"{tile}-{k}") for k in (2, 3, 2, 2)] + [tex(tile)]
    cube_type("run-ceiling", "Ceiling Tile", ["tile"] + list(shapes),
              {"tile": {"all": {"base": tex(tile)}, "down": {"base": ceil[0], "alternates": [{"base": t} for t in ceil[1:]]}}},
              "Level !: white acoustic ceiling tiles in a T-bar grid; a dead troffer; a louvred air vent and one burst open",
              json_states=shapes)
    name("run-ceiling-tile", "Ceiling Tile")
    name("run-ceiling-panel-dead", "Dead Light Panel")
    name("run-ceiling-vent", "Air Vent")
    name("run-ceiling-vent-burst", "Air Vent")

    # Level 2's wall that wasn't there: smooth new concrete across the end of a tunnel, a thread of red light at its foot.
    # It has no substance
    by_type = {}
    for part in ("lower", "upper"):
        els = [bx("Wall", (0, 0, 0), (16, 16, 16), "falsewall")]
        if part == "lower":
            els += [bx("LineN", (0, 0, -0.15), (16, 0.6, 0), "redline", glow=255, faces=("north", "up")),
                    bx("LineS", (0, 0, 16), (16, 0.6, 16.15), "redline", glow=255, faces=("south", "up")),
                    bx("LineW", (-0.15, 0, 0), (0, 0.6, 16), "redline", glow=255, faces=("west", "up")),
                    bx("LineE", (16, 0, 0), (16.15, 0.6, 16), "redline", glow=255, faces=("east", "up"))]
        by_type[f"*-{part}"] = {"base": shape(f"run-falsewall-{part}", els)}
    block("run-falsewall", {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*-lower"], "construction": ["*-lower"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "collisionbox": None, "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "lightHsvByType": {"*-lower": [0, 7, 3]}, "lightAbsorption": 0, "resistance": 99999, "drops": [], "sounds": STONE,
    }, "Level 2: a smooth new concrete wall where a tunnel used to go on (Unders.RunFalseWall): lower at rel 1, a thread of "
       "red light round its foot; upper above. It has no substance: walk into it")
    name("run-falsewall-*", "Concrete Wall")


def signs():
    # Hanging double-sided EXIT signs, in the top block of air. Modelled across x (axis we: faces north and south)
    def hanging(state):
        g = {"lit": 255, "flicker": 255, "dim": 150, "bright": 255}.get(state, 0)
        face = "exitface-" + ("lit" if state == "flicker" else state)
        return [bx("RodL", (3.5, 14, 7.5), (4.5, 16, 8.5), "steelframe"), bx("RodR", (11.5, 14, 7.5), (12.5, 16, 8.5), "steelframe"),
                bx("Housing", (1, 7, 7), (15, 14, 9), "exithousing"),
                bx("FaceN", (1.3, 7.3, 6.9), (14.7, 13.7, 7), face, glow=g, faces=("north",), uv=[1, 4.5, 15, 11.5]),
                bx("FaceS", (1.3, 7.3, 9), (14.7, 13.7, 9.1), face, glow=g, faces=("south",), uv=[1, 4.5, 15, 11.5])] \
            + sign_lip(6.6, 7, "north") + sign_lip(9, 9.4, "south")
    states = ["lit", "dim", "bright", "flicker", "off", "dead"]
    by_type, attrs = {}, {}
    for st in states:
        path = shape(f"run-exitsign-{st}", hanging(st))
        by_type[f"*-{st}-ns"] = {"base": path, "rotateY": 0}
        by_type[f"*-{st}-we"] = {"base": path, "rotateY": 90}
    block("run-exitsign", {
        "variantgroups": [{"code": "state", "states": states}, {"code": "axis", "states": ["ns", "we"]}],
        "creativeinventory": {"general": ["*-lit-ns"], "decorative": ["*-lit-ns"]},
        "blockmaterial": "Glass", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionboxByType": {"*-ns": {"x1": 0.05, "y1": 0.42, "z1": 0.4, "x2": 0.95, "y2": 1, "z2": 0.6},
                               "*-we": {"x1": 0.4, "y1": 0.42, "z1": 0.05, "x2": 0.6, "y2": 1, "z2": 0.95}},
        "lightHsvByType": {"*-lit-*": [0, 7, 9], "*-flicker-*": [0, 7, 9], "*-dim-*": [0, 7, 5], "*-bright-*": [0, 7, 12]},
        "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
        "attributesByType": {"*-flicker-we": {"offBlock": "backrooms:run-exitsign-off-we"},
                             "*-flicker-ns": {"offBlock": "backrooms:run-exitsign-off-ns"}},
        "lightAbsorption": 0, "resistance": 1, "drops": [], "sounds": GLASS,
    }, "Level !: hanging EXIT signs, the hallway's only light. Axis ns: its faces look north and south (the board spans "
       "west-east); we: west and east. "
       "lit, dim (over a fake exit), bright (over the true exit), flicker (telegraphs a burst; glow only), off (its dark "
       "mesh), dead (burst)")
    name("run-exitsign-lit-*", "EXIT Sign")
    for st in states[1:]:
        name(f"run-exitsign-{st}-*", "EXIT Sign")

    # Wall EXIT signs over a door: the wall block above it (rel 3), the sign on face <side>. "concrete" is the bright
    # sign in Level 1's concrete wall, over the door that shouldn't be there
    def wallsign(state):
        g = {"dim": 150, "bright": 255, "lit": 255, "concrete": 255}[state]
        face = "exitface-" + ("bright" if state == "concrete" else state)
        return [bx("Wall", (0, 0, 0), (16, 16, 16), "concretewall" if state == "concrete" else "wall"),
                bx("BracketL", (2, 9, -1), (3, 13, 0), "steelframe"), bx("BracketR", (13, 9, -1), (14, 13, 0), "steelframe"),
                bx("Housing", (1, 8, -3), (15, 14, -1), "exithousing"),
                bx("Face", (1.3, 8.3, -3.1), (14.7, 13.7, -3), face, glow=g, faces=("north",), uv=[1, 5, 15, 11])] \
            + sign_lip(-3.4, -3, "north", 8)
    by_type = {}
    for st in ("dim", "lit", "bright", "concrete"):
        path = shape(f"run-exitsign-wall-{st}", wallsign(st))
        for s in SIDES:
            by_type[f"*-{st}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("run-exitsign-wall", {
        "variantgroups": [{"code": "state", "states": ["dim", "lit", "bright", "concrete"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-lit-north"], "decorative": ["*-lit-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "lightHsvByType": {"*-dim-*": [0, 7, 5], "*-lit-*": [0, 7, 9], "*-bright-*": [0, 7, 12], "*-concrete-*": [0, 7, 12]},
        "lightAbsorption": 0, "resistance": 99999, "drops": [], "sounds": STONE,
    }, "An EXIT sign on a wall block above a door (rel 3), on face <side>. dim over a fake exit, bright over the true one "
       "and the hospital-walled entrances, concrete (bright, in a Level 1 concrete wall) over the Level 1 entrance")
    name("run-exitsign-wall-*", "EXIT Sign")

    # The Safe Zone's light: an opal panel, the only blue light in the level
    els = [bx("Body", (0, 0, 0), (16, 16, 16), "ceiltile", faces=("north", "east", "south", "west", "up", "down")),
           bx("Rim", (0.5, -0.8, 0.5), (15.5, 0, 15.5), "safepanelrim", faces=("north", "east", "south", "west")),
           bx("Panel", (1, -0.8, 1), (15, -0.79, 15), "safelight", glow=160, faces=("down",))]
    block("run-safelight", {
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Glass", "drawtype": "json", "shape": {"base": shape("run-safelight", els)},
        "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "lightHsv": [42, 4, 14], "lightAbsorption": 0, "resistance": 99999, "drops": [], "sounds": GLASS,
    }, "Level !: a ceiling tile with the Safe Zone's blue-white light panel")
    name("run-safelight", "Ceiling Light")

    # Safe Zone walls, and the sign: WELCOME to the safe zone (two blocks: l on the viewer's left)
    shapes = {}
    for half in ("l", "r"):
        x0, x1 = (0, 14) if half == "l" else (2, 16)
        els = [bx("Wall", (0, 0, 0), (16, 16, 16), "safewall"),
               bx("Plate", (x0, 2, -0.8), (x1, 14, 0), f"safesign-{half}", faces=("north",), uv=[0, 0, 14, 12]),
               bx("PlateEdge", (x0, 2, -0.8), (x1, 14, 0), "safepanelrim", faces=("east", "west", "up", "down"))]
        path = shape(f"run-safewall-sign-{half}", els)
        for s in SIDES:
            shapes[f"sign-{s}-{half}"] = {"base": path, "rotateY": ROTATE[s]}
    cube_type("run-safewall", "Safe Zone Wall", ["plain", "base"] + list(shapes),
              {"plain": all6("safewall"), "base": sides6("safewallbase", "safewall")},
              "Level !: the Safe Zone's pale blue walls; sign-<side>-<l|r> carries half of the welcome sign at eye height "
              "(l is on the left as you face it)", json_states=shapes)
    b14_versions("run-safewall", {"plain": ("safewall", "all"), "base": ("safewallbase", "sides")}, {}, WALL_WEIGHTS)
    name("run-safewall-*", "Safe Zone Wall")


# ======================= Doors =======================

def frame(tex_, upper=True, z0=-1, z1=1):
    """A door frame standing proud of the wall, on the neighbouring wall blocks either side and above. Where it reaches
    into the wall its inner faces would lie in the doorway's reveals and soffit, so they stand a hair into the doorway."""
    els = [bx("JambL", (-1.5, 0, z0), (0.02, 16, z1), tex_), bx("JambR", (15.98, 0, z0), (17.5, 16, z1), tex_)]
    if upper:
        els.append(bx("Head", (-1.5, 15.98, z0), (17.5, 17.5, z1), tex_))
    return els


def leaf(front, back, z0=1, z1=3, x0=0, x1=16):
    return [bx("Leaf", (x0, 0, z0), (x1, 16, z1), front, faces=("north",), full=True),
            bx("LeafBack", (x0, 0, z0), (x1, 16, z1), back, faces=("south", "east", "west", "up", "down"))]


def behaviour(kind):
    """Every door kind is a BackroomsThreshold: ThresholdSystem hands those that lead nowhere (runside, runhall,
    runchained, runmarked, runfake) to RunSystem.UseDoor, and runentry / runexit to the network."""
    return threshold(kind)


def door_type(code, english, states, build, kind_by_state, comment, material="Metal", sounds=METAL,
              passable=(), selection=None, light=None):
    by_type = {}
    for st in states:
        for part in ("lower", "upper"):
            path = shape(f"{code}-{st}-{part}", build(st, part))
            for s in SIDES:
                by_type[f"*-{st}-{part}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    data = {
        "variantgroups": [{"code": "state", "states": states}, {"code": "part", "states": ["lower", "upper"]},
                          {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": [f"*-{states[0]}-lower-north"], "construction": [f"*-{states[0]}-lower-north"]},
        "blockmaterial": material, "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "behaviorsByType": {f"*-{st}-*": behaviour(k) for st, k in kind_by_state.items()},
        "lightAbsorption": 99, "resistance": 99999, "drops": [], "sounds": sounds,
    }
    coll = {}
    for st in passable:
        coll[f"*-{st}-*"] = None
    if selection:
        coll.update(selection)
    if coll:
        data["collisionboxByType"] = coll
    if light:
        data.update(light)
    block(code, data, comment)
    name(f"{code}-*", english)


def side_doors():
    def build(st, part):
        els = frame("steelframe", upper=part == "upper")
        if st in ("closed", "dented"):
            els += side_leaf(f"sidedoor-{'dented-' if st == 'dented' else ''}{part}", "sidedoor-back", part)
            if part == "lower":
                els += [bx("Rose", (12.5, 13, 0.4), (14.5, 15.5, 1), "chrome"),
                        bx("Lever", (10, 13.8, -0.6), (14, 14.8, 0.4), "chrome"),
                        bx("Kick", (1, 0.5, 0.6), (15, 4, 1), "pushplate", faces=("north", "up", "east", "west"))]
                if st == "dented":
                    # The leaf bulges out where something hit it from the other side
                    els += [bx("Bulge1", (3, 4, 0), (13, 16, 1), "sidedoor-dented-lower", faces=("north", "east", "west", "up", "down")),
                            bx("Bulge2", (5, 6, -1), (11, 14, 0), "sidedoor-dented-lower", faces=("north", "east", "west", "up", "down"))]
            else:
                els += [bx("PushPlate", (11.5, 0.5, 0.5), (15.5, 6.5, 1), "pushplate")]
        elif st == "open":
            els += [bx("Dark", (0, 0, 15.9), (16, 16, 16), "doorway", faces=("north",))]
            els += [bx("Hinge1" if part == "lower" else "Hinge2", (-0.3, 3, 0), (0.6, 6, 1.2), "steelframe")]
        else:  # leaf: flung open, standing in the hall tile in front of the door (same side as the door)
            # (B14) the closed leaf, window and kick plate included, turned to face east and moved against the west side
            flung = side_leaf(f"sidedoor-{part}", "sidedoor-back", part, z0=0, z1=2)
            if part == "lower":
                flung.append(bx("Kick", (1, 0.5, -0.4), (15, 4, 0), "pushplate", faces=("north", "up", "east", "west")))
            els = [dict(e, **{"from": [e["from"][0] - 13.8, e["from"][1], e["from"][2]],
                              "to": [e["to"][0] - 13.8, e["to"][1], e["to"][2]]}) for e in (turn(e, 1) for e in flung)]
            if part == "lower":
                els += [bx("Lever", (2.2, 13.8, 2), (3.2, 14.8, 6), "chrome")]
            else:
                els += [bx("PushPlate", (2.2, 0.5, 0.5), (2.7, 6.5, 4.5), "pushplate")]
        return els
    leafbox = {f"*-leaf-*-{sd}": K.cuboid((0, 0, 0, 0.15, 1, 1), sd) for sd in SIDES}
    door_type("run-sidedoor", "Steel Door", ["closed", "dented", "open", "leaf"], build, {"closed": "runside", "dented": "runside"},
              "Level !: the locked steel doors down both sides of the hall (runside). dented (something behind it, about to "
              "burst), open (burst or flung open: an empty frame, black beyond), leaf (the flung-open leaf, placed in the hall "
              "tile in front of the door with the door's own side; collision on the leaf only)",
              passable=("open",), selection=leafbox)
    path = os.path.join(ASSETS, "blocktypes", TAG, "run-sidedoor.json")
    with open(path, encoding="utf-8") as f:
        head, _, body = f.read().partition("\n")
    data = json.loads(body)
    data["selectionboxByType"] = leafbox
    write_json(path, data, head[3:])


def exit_doors():
    def panic(dz=0):
        return [bx("CaseL", (1.5, 12.5, -2 + dz), (3.5, 15.5, 1 + dz), "steelframe"),
                bx("CaseR", (12.5, 12.5, -2 + dz), (14.5, 15.5, 1 + dz), "steelframe"),
                bx("Bar", (3.5, 13, -1.8 + dz), (12.5, 15, -0.3 + dz), "panicbar")]

    def build(st, part):
        if st == "arrival":
            # Flush on the surface of a wall, in the air block in front of it, its back against the wall
            els = frame("steelframe", upper=part == "upper", z0=12, z1=16)
            els += leaf("markeddoor-" + part, "exitdoor-back", 13, 15)
            if part == "lower":
                els += panic(13)
            return els
        els = frame("steelframe", upper=part == "upper")
        if st == "fake-open":
            # Swung inward: the closet behind it is all there is
            els += [bx("Leaf", (0.2, 0, 3), (2.2, 16, 19), "exitdoor-back"),
                    bx("Hinge", (-0.3, 4, 1), (0.6, 7, 3), "steelframe")]
            return els
        front = "markeddoor-" + part if st == "marked" else "exitdoor-" + part
        if st == "true" and part == "lower":
            # (0.514.0) The real exit has light under it: the leaf stops short of the floor and daylight shows in the gap,
            # white in a red hall (the lore's way out leads somewhere lit and safe; a false exit's closet is dark). The
            # block gives off that light too (lightHsvByType), so the last steps of the dead end are lit white
            els += [bx("Leaf", (0, 1.25, 1), (16, 16, 3), front, faces=("north",), uv=[0, 0, 16, 14.75]),
                    bx("LeafBack", (0, 1.25, 1), (16, 16, 3), "exitdoor-back", faces=("south", "east", "west", "up", "down")),
                    bx("Daylight", (0.4, 0, 2.2), (15.6, 1.25, 2.4), "exitdaylight", glow=255, faces=("north",), uv=[0, 0, 16, 2]),
                    bx("Sill", (0, 0, 0.6), (16, 0.15, 2.2), "exitdaylight", glow=200, faces=("up",), uv=[0, 0, 16, 2])]
            els += panic() + [bx("Kick", (1, 1.75, 0.5), (15, 4.5, 1), "panicbar", faces=("north", "up", "down", "east", "west"))]
            return els
        els += leaf(front, "exitdoor-back")
        if part == "lower":
            els += panic() + [bx("Kick", (1, 0.5, 0.5), (15, 3.5, 1), "panicbar", faces=("north", "up", "east", "west"))]
        return els
    states = ["true", "fake", "fake-open", "marked", "entry", "arrival"]
    kinds = {"true": "runexit", "fake": "runfake", "marked": "runmarked", "entry": "runentry", "arrival": "runentry"}
    sel = {f"*-arrival-*-{sd}": K.cuboid((0, 0, 0.75, 1, 1, 1), sd) for sd in SIDES}
    door_type("run-exitdoor", "Exit Door", states, build, kinds,
              "Red fire doors with panic bars, facing <side>. true: the real exit (runexit). fake: a fake exit (runfake); "
              "fake-open: it swung inward onto an empty closet. marked: the door you came in by, a huge red '!' on its inside "
              "(runmarked). entry: the way in, set into a wall in Levels 1 and 37 (runentry). arrival: the door left where an "
              "escaped runner comes out, flush on a wall in the air block in front of it, '!' on its face (runentry). The "
              "true door's lower half shows light under it and gives off a pale daylight",
              passable=("fake-open",), selection=sel,
              light={"lightHsvByType": {"*-true-lower-*": [8, 2, 14]}, "lightAbsorptionByType": {"*-true-lower-*": 0, "*": 99}})


def chained_door():
    def chain_run(p0, p1, zc, part):
        """Links along a line from p0 to p1 in the door's 16 x 32 face; each link is drawn in the half it falls in."""
        (x0, y0), (x1, y1) = p0, p1
        length = math.hypot(x1 - x0, y1 - y0)
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        n = int(length / 1.9)
        els = []
        for k in range(n):
            t = (k + 0.5) / n
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            if (cy < 16) != (part == "lower"):
                continue
            cy -= 0 if part == "lower" else 16
            if k % 2 == 0:
                lo, hi = (cx - 1.2, cy - 0.5, zc - 0.25), (cx + 1.2, cy + 0.5, zc + 0.25)
            else:
                lo, hi = (cx - 1.2, cy - 0.25, zc - 0.5), (cx + 1.2, cy + 0.25, zc + 0.5)
            els.append(bx(f"Link{k}", lo, hi, "chain", rot=(0, 0, ang), origin=(cx, cy, zc)))
        return els

    def build(st, part):
        els = frame("steelframe", upper=part == "upper")
        bolt_y = (1, 2.5) if part == "lower" else (13.5, 15)
        els += [bx("BoltL", (-1.2, bolt_y[0], -1.8), (0.3, bolt_y[1], -0.6), "chain"),
                bx("BoltR", (15.7, bolt_y[0], -1.8), (17.2, bolt_y[1], -0.6), "chain")]
        if st == "broken":
            # Torn out: chain ends hanging from the bolts, the leaf flat on the floor in front of the doorway
            if part == "upper":
                for side_x, sgn in ((0, 1), (16, -1)):
                    els += chain_run((side_x, 30), (side_x + sgn * 2, 22), -1.2, "upper")
            else:
                els += [bx("Leaf", (0.5, 0, -29), (15.5, 2, 0), "chaindoor-lower", faces=("up",), uv=[0, 0, 16, 16]),
                        bx("LeafEdge", (0.5, 0, -29), (15.5, 2, 0), "steel", faces=("north", "south", "east", "west"))]
                els[-2]["rotationX"] = -8
                els[-2]["rotationOrigin"] = [8, 0, -29]
                els[-1]["rotationX"] = -8
                els[-1]["rotationOrigin"] = [8, 0, -29]
                els += chain_run((1, 4), (4, 1), -1.2, "lower") + [bx("Padlock", (5, 0, -6), (8, 2, -2), "padlock")]
            return els
        z = -0.4 if st == "intact" else -2.6
        els += leaf("chaindoor-" + part, "steel")
        if st == "bulging":
            # Bowed into the room: the middle of the leaf pushed out, the chains drawn taut over it
            if part == "lower":
                els += [bx("Bow1", (1.5, 2, -0.5), (14.5, 16, 1), "chaindoor-lower", faces=("north", "east", "west", "down")),
                        bx("Bow2", (4, 6, -2), (12, 16, -0.5), "chaindoor-lower", faces=("north", "east", "west", "down"))]
            else:
                els += [bx("Bow1", (1.5, 0, -0.5), (14.5, 14, 1), "chaindoor-upper", faces=("north", "east", "west", "up")),
                        bx("Bow2", (4, 0, -2), (12, 10, -0.5), "chaindoor-upper", faces=("north", "east", "west", "up"))]
        els += chain_run((0, 30), (16, 2), z, part) + chain_run((16, 30), (0, 2), z, part)
        if part == "lower":
            els += [bx("Padlock", (6.5, 11, z - 1.5), (9.5, 14.5, z + 0.5), "padlock"),
                    bx("Shackle", (7, 14.5, z - 1), (9, 16, z), "shackle")]
        return els
    door_type("run-chaineddoor", "Chained Door", ["intact", "bulging", "broken"], build,
              {"intact": "runchained", "bulging": "runchained"},
              "Level !: the start room's chained door, the horde behind it. intact, bulging (bowed into the room), broken "
              "(torn out, the leaf lying in front of the doorway)", passable=("broken",))


def hall_door():
    def build(st, part):
        # The frame stands two voxels proud of the wall, so the leaf reads as set back in it, not as an opening
        els = frame("hallframe", upper=part == "upper", z0=-2)
        if st == "closed":
            els += side_leaf("halldoor-" + part, "halldoor-back", part, window=HALL_WINDOW if part == "upper" else None,
                             bead="hallframe")
            if part == "lower":
                els += [bx("Kick", (1, 0.5, 0.4), (15, 5, 1), "hallkick", faces=("north", "up", "east", "west")),
                        bx("Rose", (12.5, 13, 0.4), (14.5, 15.5, 1), "chrome"), bx("Neck", (12.9, 13.6, -1), (14, 14.6, 0.4), "chrome"),
                        bx("Lever", (9.5, 13.6, -1.4), (14, 14.8, -0.4), "chrome")]
            # (B14) the vision panel is an opening in side_leaf now
        else:
            # Swung right round and flat against the wall beside the doorway
            els += [bx("Leaf", (17.5, 0, -2.2), (33.5, 16, -0.2), "halldoor-back"),
                    bx("Hinge", (16, 4 if part == "lower" else 10, -2.2), (17.5, 7 if part == "lower" else 13, -0.2), "steelframe")]
        return els
    door_type("run-halldoor", "Hospital Door", ["closed", "open"], build, {"closed": "runhall"},
              "Level !: the start room's door to the hallway, which sticks; open, it lies flat against the wall. Also the "
              "Safe Zone's side-room doors (open)", material="Wood", sounds=WOOD, passable=("open",))


# ======================= Props =======================

def octagon(name_, axis, c, r, half, t, glow=0):
    """A wheel or disc: a square and the same square turned 45 degrees, about an axis through c."""
    cx, cy, cz = c
    if axis == "x":
        a = bx(name_, (cx - half, cy - r, cz - r), (cx + half, cy + r, cz + r), t, glow)
        b = bx(name_ + "45", (cx - half, cy - r, cz - r), (cx + half, cy + r, cz + r), t, glow, rot=(45, 0, 0), origin=c)
    else:
        a = bx(name_, (cx - r, cy - r, cz - half), (cx + r, cy + r, cz + half), t, glow)
        b = bx(name_ + "45", (cx - r, cy - r, cz - half), (cx + r, cy + r, cz + half), t, glow, rot=(0, 0, 45), origin=c)
    return [a, b]


def castor(n, x, z):
    return [bx(f"Fork{n}", (x - 0.5, 1.5, z - 0.5), (x + 0.5, 3, z + 0.5), "chrome"),
            bx(f"Castor{n}", (x - 0.75, 0, z - 1.2), (x + 0.75, 1.8, z + 1.2), "rubber")]


def clip(els, axis, lo, hi, shift_by):
    """Keeps the parts of boxes between lo and hi on an axis, moved by shift_by (for props spanning two blocks)."""
    out = []
    i = "xyz".index(axis)
    for e in els:
        e = json.loads(json.dumps(e))
        a, b = e["from"][i], e["to"][i]
        if b <= lo or a >= hi:
            continue
        if "rotationOrigin" not in e:
            e["from"][i], e["to"][i] = max(a, lo), min(b, hi)
        e["from"][i] += shift_by
        e["to"][i] += shift_by
        if "rotationOrigin" in e:
            e["rotationOrigin"][i] += shift_by
        # Faces keep their texture scale: recompute plain UVs from the new size
        sizes = _sizes(e)
        for f, face in e["faces"].items():
            if face["uv"][0] == 0 and face["uv"][1] == 0:
                a2, b2 = sizes[f]
                face["uv"] = [0, 0, min(16, max(a2, 0.5)), min(16, max(b2, 0.5))]
        out.append(e)
    return out


def _sizes(e):
    (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
    w, h, d = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)
    return {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}


def gurney_parts():
    """A gurney, modelled head to the north across two blocks (z 0-32), like the hospital bed."""
    gurney = [bx("Mattress", (1, 9, 1), (15, 12, 31), "sheet"),
              bx("Pillow", (3, 12, 1.8), (13, 13.5, 6), "pillow"),
              bx("Fold", (1.2, 12, 22), (14.8, 13, 30), "sheet"),
              bx("Deck", (0.8, 8, 0.6), (15.2, 9, 31.4), "gurneyframe"),
              bx("RailUpper", (0.2, 15, 3), (1.2, 16, 29), "chrome"),
              bx("PostA", (0.2, 12, 4), (1.2, 15, 5), "chrome"), bx("PostB", (0.2, 12, 27), (1.2, 15, 28), "chrome"),
              bx("RailLowered", (15, 9.5, 3), (16, 10.5, 29), "chrome"),
              bx("PushBar", (2, 13, 0), (14, 14, 1), "chrome"), bx("PushPostL", (2, 9, 0), (3, 13, 1), "chrome"),
              bx("PushPostR", (13, 9, 0), (14, 13, 1), "chrome")]
    for n, (x, z) in enumerate(((2, 3), (14, 3), (2, 29), (14, 29))):
        gurney += [bx(f"Leg{n}", (x - 0.5, 3, z - 0.5), (x + 0.5, 8, z + 0.5), "chrome")] + castor(n, x, z)
    return gurney


def props():
    # Gurney: modelled head to the north across two blocks (head, foot), like the hospital bed
    gurney = gurney_parts()
    prop("run-gurney", "Gurney", {"head": clip(gurney, "z", 0, 16, 0), "foot": clip(gurney, "z", 16, 32, -16)},
         box=(0, 0, 0, 1, 0.8, 1), material="Metal", sounds=METAL,
         comment="A hospital gurney left in the hall, two blocks long (head, foot; head to the north). 0.8 high",
         extra={"drops": drops(("metalbracket", 1, 0.5), ("game:cloth-plain", 0.5, 0.5))})

    # Wheelchair, footplates to the north
    chair = [bx("Seat", (2.5, 7, 3), (13.5, 8, 13), "seatvinyl"),
             bx("Back", (2.5, 8, 13), (13.5, 16, 14), "seatvinyl"),
             bx("ArmL", (1.8, 11, 4), (2.6, 11.8, 13), "chrome"), bx("ArmR", (13.4, 11, 4), (14.2, 11.8, 13), "chrome"),
             bx("ArmPostL", (1.8, 7, 4.5), (2.6, 11, 5.3), "chrome"), bx("ArmPostR", (13.4, 7, 4.5), (14.2, 11, 5.3), "chrome"),
             bx("FrameL", (1.8, 6.2, 2), (2.6, 7, 14), "chrome"), bx("FrameR", (13.4, 6.2, 2), (14.2, 7, 14), "chrome"),
             bx("UprightL", (2, 7, 13.8), (2.8, 17, 14.6), "chrome"), bx("UprightR", (13.2, 7, 13.8), (14, 17, 14.6), "chrome"),
             bx("HandleL", (2, 16.2, 14.6), (2.8, 17, 16.6), "rubber"), bx("HandleR", (13.2, 16.2, 14.6), (14, 17, 16.6), "rubber"),
             bx("LegL", (3, 3, 1.8), (3.8, 7, 2.6), "chrome"), bx("LegR", (12.2, 3, 1.8), (13, 7, 2.6), "chrome"),
             bx("FootL", (3, 2.6, 0.2), (7.2, 3.2, 3), "beamsteel"), bx("FootR", (8.8, 2.6, 0.2), (13, 3.2, 3), "beamsteel")]
    chair += octagon("WheelL", "x", (1, 6.5, 10), 6.5, 0.6, "tyre") + octagon("WheelR", "x", (15, 6.5, 10), 6.5, 0.6, "tyre")
    chair += [bx("HubL", (0.2, 5.5, 9), (2, 7.5, 11), "chrome"), bx("HubR", (14, 5.5, 9), (15.8, 7.5, 11), "chrome")]
    chair += castor(0, 3.4, 3) + castor(1, 12.6, 3)
    prop("run-wheelchair", "Wheelchair", chair, box=(0, 0, 0, 1, 0.9, 1), material="Metal", sounds=METAL,
         comment="An empty wheelchair, footplates to the north. 0.9 high",
         extra={"drops": drops(("metalbracket", 1.5, 0.5), ("game:cloth-plain", 0.3, 0.3))})

    # IV stand: a tall chrome pole on a five-arm base, a bag on a hook
    iv = [bx("Pole", (7.5, 1, 7.5), (8.5, 28, 8.5), "chrome"),
          bx("HookBar", (5, 27, 7.6), (11, 27.7, 8.4), "chrome"),
          bx("Bag", (8.7, 19, 7.4), (11.7, 25, 8.6), "ivbag"),
          bx("Port", (9.9, 18, 7.8), (10.5, 19, 8.2), "ivbag"),
          bx("Line", (10, 4, 7.9), (10.4, 18, 8.3), "ivbag"),
          bx("Hub", (7, 0.5, 7), (9, 2, 9), "chrome")]
    for k in range(5):
        iv.append(bx(f"Arm{k}", (8, 0.6, 7.6), (14, 1.4, 8.4), "chrome", rot=(0, k * 72, 0), origin=(8, 1, 8)))
    prop("run-ivstand", "IV Stand", iv, box=(0.35, 0, 0.35, 0.65, 1, 0.65), material="Metal", sounds=METAL,
         comment="An IV stand with a bag still hanging", extra={"drops": drops(("metalbracket", 0.6, 0.4), ("scrapwire", 0.3, 0.3))})

    # Waiting room chairs: two moulded seats on one steel beam, facing north
    wc = [bx("Beam", (1, 5.5, 7), (15, 6.5, 9), "beamsteel")]
    for n, x in enumerate((1.2, 8.8)):
        wc += [bx(f"Seat{n}", (x, 6.5, 4.5), (x + 6, 7.5, 10.5), "chairplastic"),
               bx(f"Back{n}", (x, 7.5, 10.5), (x + 6, 13.5, 11.5), "chairplastic", rot=(-8, 0, 0), origin=(x + 3, 7.5, 11)),
               bx(f"Lip{n}", (x, 6, 4.2), (x + 6, 7.2, 4.8), "chairplastic")]
    wc += [bx("ArmMid", (7.5, 6.5, 6), (8.5, 10, 10), "beamsteel"), bx("ArmTop", (7.4, 10, 5.5), (8.6, 10.6, 10.5), "rubber")]
    for n, x in enumerate((2.5, 13.5)):
        wc += [bx(f"Leg{n}", (x - 0.5, 0.8, 7.5), (x + 0.5, 5.5, 8.5), "beamsteel"),
               bx(f"Foot{n}", (x - 0.6, 0, 4), (x + 0.6, 0.8, 12), "beamsteel")]
    prop("run-chairs", "Waiting Room Chairs", wc, box=(0.05, 0, 0.2, 0.95, 0.9, 0.8), material="Metal", sounds=METAL,
         comment="Two moulded seats on a steel beam, facing north", extra={"drops": drops(("metalbracket", 1, 0.5))})

    # Crash cart: red drawers to the north, a defibrillator on top
    cart = [bx("Body", (2, 2.5, 3), (14, 15, 13), "cartside"),
            bx("Defib", (4, 15, 5), (12, 18, 11), "defib"),
            bx("DefibScreen", (5, 18, 6), (10.5, 18.1, 10), "defibscreen", faces=("up",), uv=[0, 0, 16, 16]),
            bx("BezelN", (4.6, 18, 5.6), (10.9, 18.35, 6), "rubber"), bx("BezelS", (4.6, 18, 10), (10.9, 18.35, 10.4), "rubber"),
            bx("BezelW", (4.6, 18, 6), (5, 18.35, 10), "rubber"), bx("BezelE", (10.5, 18, 6), (10.9, 18.35, 10), "rubber"),
            bx("DefibKnob", (11, 18, 6.2), (11.6, 18.8, 6.8), "rubber"),
            bx("RailN", (1.5, 15, 2.5), (14.5, 16, 3.3), "chrome"), bx("RailS", (1.5, 15, 12.7), (14.5, 16, 13.5), "chrome"),
            bx("Handle", (14, 12, 4), (15, 13, 12), "chrome"), bx("HandlePostA", (14, 12, 4), (15.2, 13, 5), "chrome"),
            bx("Bin", (0.6, 9, 6), (2, 13, 10), "cartside")]
    # (B14) five drawers as boxes standing proud of the body, a label holder and a pull on each
    for k, (y0, y1) in enumerate(((2.8, 5.1), (5.3, 7.6), (7.8, 10.1), (10.3, 12.6), (12.8, 14.7))):
        cart += [bx(f"Drawer{k}", (2.3, y0, 2.6), (13.7, y1, 3), "cartdrawer", faces=("north", "east", "west", "up", "down")),
                 bx(f"Label{k}", (3.2, y1 - 0.9, 2.45), (6.2, y1 - 0.4, 2.6), "cartlabel", faces=("north",), uv=[0, 0, 16, 4]),
                 bx(f"Pull{k}", (7, y0 + 0.7, 1.9), (11, y0 + 1.3, 2.6), "chrome")]
    for n, (x, z) in enumerate(((3, 4), (13, 4), (3, 12), (13, 12))):
        cart += castor(n, x, z)
    prop("run-crashcart", "Crash Cart", cart, box=(0.06, 0, 0.12, 0.94, 1, 0.88), material="Metal", sounds=METAL,
         comment="A red crash cart with a defibrillator on top, drawers to the north",
         extra={"drops": drops(("game:bandage-clean", 0.5, 0.5), ("scrapwire", 1, 0.5), ("metalbracket", 1, 0.5))})

    # Steel shelving: standing in a door recess (two blocks), and toppled across the hall (two blocks along X)
    st = []
    for n, (x, z) in enumerate(((1, 10), (14, 10), (1, 15), (14, 15))):
        st.append(bx(f"Upright{n}", (x, 0, z), (x + 1, 32, z + 1), "shelfblue"))
    for n, y in enumerate((1, 11, 21, 30.5)):
        st.append(bx(f"Shelf{n}", (1, y, 10), (15, y + 1, 16), "shelfblue"))
    boxes = [bx("BoxA", (2, 2, 10.5), (7, 6.5, 15.5), "runbox"), bx("BoxB", (8, 2, 11), (13.5, 5, 15.5), "runbox"),
             bx("BoxC", (3, 12, 11), (8, 16.5, 15.5), "runbox"), bx("BoxD", (9.5, 12, 10.5), (13.5, 15, 15), "runbox"),
             bx("BoxE", (2.5, 22, 11), (6.5, 25, 15), "runbox")]
    standing = st + boxes
    # Toppled forward on its side, two blocks long: fallen-a where it stood and fallen-b one tile further on toward
    # <side>. Modelled for side north, so b lies north of a: the shelf's base at a's south edge, its top at b's north
    fallen = []
    for e in st:
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        fallen.append(bx(e["name"], (z1 - 5, x1 - 1, -y2), (z2 - 5, x2 - 1, -y1), "shelfblue"))
    spilled = [bx("SpillA", (0.5, 0, -4.5), (4.5, 3, -0.5), "runbox", rot=(0, 20, 0)), bx("SpillB", (12, 0, -13), (16, 3, -9), "runbox", rot=(0, -15, 0)),
               bx("SpillC", (0.8, 0, -23), (4.8, 3, -19), "runbox", rot=(0, 35, 0)), bx("SpillD", (11.5, 0, -30), (15.5, 2.5, -26), "runbox")]
    fallen += spilled
    shelf = {"standing-lower": clip(standing, "y", 0, 16, 0), "standing-upper": clip(standing, "y", 16, 32, -16),
             "fallen-a": clip(fallen, "z", -16, 0, 16), "fallen-b": clip(fallen, "z", -32, -16, 32)}
    prop("run-shelf", "Steel Shelving", shelf, box=(0.05, 0, 0.6, 0.95, 1, 1), material="Metal", sounds=METAL,
         comment="Blue steel shelving. standing-lower/upper: in a door recess, back to the wall, front to <side> (the way it "
                 "will fall). fallen-a/b: toppled on its side across the hall, 0.875 high (jump it); a where it stood, b the "
                 "next tile toward <side>",
         extra={"drops": drops(("metalbracket", 2, 1), ("game:paper-parchment", 0.5, 0.5))})
    data_path = os.path.join(ASSETS, "blocktypes", TAG, "run-shelf.json")
    with open(data_path, encoding="utf-8") as f:
        head, _, body = f.read().partition("\n")
    data = json.loads(body)
    coll = {f"*-standing-*-{sd}": K.cuboid((0.05, 0, 0.6, 0.95, 1, 1), sd) for sd in SIDES}
    coll.update({f"*-fallen-*-{sd}": K.cuboid((0.3, 0, 0, 0.7, 0.875, 1), sd) for sd in SIDES})
    data["collisionboxByType"] = coll
    data["selectionboxByType"] = coll
    write_json(data_path, data, head[3:])

    # (What trips a runner in the dark, the toys, boxes, cord and fallen ceiling, is trip_props(), after gauntlet(): it uses its rubble)
    sheets = [bx("Sheet", (1, 0, 1), (15, 0.6, 15), "sheet"), bx("Fold1", (2, 0.6, 2.5), (13, 1.5, 5), "sheet"),
              bx("Fold2", (3, 0.6, 6.5), (15, 1.9, 9.5), "sheet"), bx("Fold3", (1.5, 0.6, 10.5), (10, 1.3, 14), "sheet"),
              bx("Fold4", (5, 1.5, 7.2), (12, 2.4, 8.8), "sheet")]
    prop("run-sheets", "Bedsheets", sheets, box=(0.06, 0, 0.06, 0.94, 0.15, 0.94), collide=False, material="Cloth", sounds=CLOTH,
         comment="Rumpled bedsheets on the floor (fuel for a sign burst's fire)", extra={"drops": drops(("game:cloth-plain", 1, 0.5))})
    remains = [bx("Smear", (1, 0, 3), (15, 0.2, 15), "smear", faces=("up",), uv=[0, 0, 16, 16]),
               bx("Pack", (3, 0, 2), (9, 6, 6), "pack", rot=(0, 0, -12), origin=(3, 0, 4)),
               bx("PackFlap", (3.5, 5.5, 2.5), (8.5, 6.5, 6.5), "pack", rot=(-20, 0, -12), origin=(3, 0, 4)),
               bx("Strap", (4, 0.5, 6), (5, 4, 7.5), "pack"),
               bx("Sole", (10, 0, 9), (13, 0.8, 15), "sole", rot=(0, 25, 0), origin=(11.5, 0, 12)), bx("Shoe", (10.2, 0.8, 9.5), (12.8, 2.4, 14), "sneaker", rot=(0, 25, 0), origin=(11.5, 0, 12)),
               bx("Heel", (10.2, 0.8, 13), (12.8, 3, 14.6), "sneaker", rot=(0, 25, 0), origin=(11.5, 0, 12))]
    prop("run-remains", "A Runner's Remains", remains, box=(0.06, 0, 0.12, 0.94, 0.4, 0.94), collide=False, material="Cloth", sounds=CLOTH,
         comment="What is left of someone who didn't make it: a torn pack, one sneaker, a dark smear",
         extra={"drops": drops(("game:cloth-plain", 1, 0.5), ("almondwater", 0.2, 0), ("hub-key-run", 0.15, 0))})

    # Supply tray on a stool in a door recess, with an Energy Bar or a bottle of Almond Water on it
    stool = [bx("Seat", (4.5, 7, 4.5), (11.5, 8, 11.5), "stoolseat")] + [
        bx(f"Leg{n}", (x, 0, z), (x + 0.8, 7, z + 0.8), "chrome") for n, (x, z) in enumerate(((5, 5), (10.2, 5), (5, 10.2), (10.2, 10.2)))]
    stool += [bx("Dish", (4.8, 8, 6.4), (11.2, 9, 9.6), "dish"), bx("DishEndL", (4.2, 8, 7), (4.8, 9, 9), "dish"),
              bx("DishEndR", (11.2, 8, 7), (11.8, 9, 9), "dish")]
    tray = {"bar": stool + [bx("Bar", (6, 9, 7.2), (10, 9.9, 8.8), "foil", rot=(0, 15, 0))],
            "water": stool + [bx("Bottle", (7.2, 9, 7.2), (8.8, 13, 8.8), "almondbottle"),
                              bx("Neck", (7.6, 13, 7.6), (8.4, 14, 8.4), "almondbottle"),
                              bx("Cap", (7.5, 14, 7.5), (8.5, 14.7, 8.5), "bottlecap")]}
    prop("run-tray", "Supply Tray", tray, box=(0.25, 0, 0.25, 0.75, 0.6, 0.75), material="Metal", sounds=METAL,
         comment="A kidney dish on a stool in a door recess: an Energy Bar (bar) or Almond Water (water)",
         extra={"resistance": 0.2, "dropsByType": {"*-bar-*": drops(("run-energybar", 1, 0)), "*-water-*": drops(("almondwater", 1, 0))}})
    name("run-tray-*", "Supply Tray")

    bedside = [bx("Body", (2, 0.5, 2), (14, 14, 14), "bedside"),
               bx("Top", (1.5, 14, 1.5), (14.5, 15, 14.5), "bedside"),
               bx("Drawer", (2.5, 10, 1.4), (13.5, 13.5, 2), "bedsidefront", faces=("north",), full=True),
               bx("DrawerSides", (2.5, 10, 1.4), (13.5, 13.5, 2), "bedside", faces=("east", "west", "up", "down")),
               bx("Handle", (6, 11.3, 0.6), (10, 12.3, 1.4), "chrome"),
               bx("Door", (2.5, 1.5, 1.4), (13.5, 9.5, 2), "bedsidefront", faces=("north",), full=True),
               bx("DoorSides", (2.5, 1.5, 1.4), (13.5, 9.5, 2), "bedside", faces=("east", "west", "up", "down")),
               bx("Knob", (11, 5, 0.8), (12, 6, 1.4), "chrome"),
               bx("Plinth", (2.4, 0, 2.4), (13.6, 0.5, 13.6), "rubber"),
               bx("Cup", (9.5, 15, 9), (11.5, 17.5, 11), "dish")]
    prop("run-bedside", "Bedside Table", bedside, box=(0.125, 0, 0.125, 0.875, 0.94, 0.875), material="Wood", sounds=WOOD,
         comment="The start room's bedside table: 1 Almond Water and 1-2 Energy Bars inside",
         extra={"resistance": 1, "drops": drops(("almondwater", 1, 0), ("run-energybar", 1.5, 0.5))})

    # Medicine cabinet: a wall block (rel 2) with the cabinet on face <side>, at eye height
    cab = [bx("Wall", (0, 0, 0), (16, 16, 16), "wall"),
           bx("Box", (2, 0, -4), (14, 12, 0), "cabinet"),
           bx("Front", (2.2, 0.2, -4.4), (13.8, 11.8, -4), "cabinetfront", faces=("north",), full=True),
           bx("FrontSides", (2.2, 0.2, -4.4), (13.8, 11.8, -4), "cabinet", faces=("east", "west", "up", "down")),
           # (B14) the mirror: a pane set into the door behind a frame, no longer painted
           bx("Mirror", (3.6, 1.6, -4.5), (12.4, 7.6, -4.4), "cabmirror", faces=("north",), uv=[0, 0, 16, 11]),
           bx("MirrorFrameT", (3.2, 7.6, -4.7), (12.8, 8.0, -4.4), "cabinet", faces=("north", "east", "west", "up", "down")),
           bx("MirrorFrameB", (3.2, 1.2, -4.7), (12.8, 1.6, -4.4), "cabinet", faces=("north", "east", "west", "up", "down")),
           bx("MirrorFrameL", (3.2, 1.6, -4.7), (3.6, 7.6, -4.4), "cabinet", faces=("north", "east", "west")),
           bx("MirrorFrameR", (12.4, 1.6, -4.7), (12.8, 7.6, -4.4), "cabinet", faces=("north", "east", "west")),
           bx("Pin1", (1.6, 2, -4.4), (2.2, 3.5, -3.6), "chrome"), bx("Pin2", (1.6, 8.5, -4.4), (2.2, 10, -3.6), "chrome"),
           bx("Catch", (12.8, 5, -4.8), (13.6, 7, -4.4), "chrome")]
    by_type = {f"*-{sd}": {"base": shape("run-medcabinet", cab), "rotateY": ROTATE[sd]} for sd in SIDES}
    block("run-medcabinet", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "lightAbsorption": 99, "resistance": 1, "drops": drops(("game:bandage-clean", 1, 0)), "sounds": METAL,
    }, "Level !: a wall block (rel 2) with a medicine cabinet on face <side>; breaks in a second for a clean bandage")
    name("run-medcabinet-*", "Medicine Cabinet")

    # The privacy curtain on its ceiling track: pleats from the floor up, an open mesh band and the track at the top
    def pleats(y0, y1):
        out = []
        for k in range(8):
            z = 7 if k % 2 == 0 else 8
            out.append(bx(f"Pleat{k}", (2 * k, y0, z), (2 * k + 2, y1, z + 1), "curtain"))
        return out
    curtain = {"lower": pleats(1.5, 16), "middle": pleats(0, 16), "upper": pleats(0, 16),
               "top": [bx("Mesh", (0, 0, 7.6), (16, 13, 8.4), "curtainmesh", faces=("north", "south")),
                       bx("Track", (0, 15, 7), (16, 16, 9), "steelframe")] +
                      [bx(f"Hook{k}", (2 * k + 0.6, 13, 7.6), (2 * k + 1.4, 15, 8.4), "chrome") for k in range(0, 8, 2)]}
    by_type = {}
    for part, els in curtain.items():
        path = shape(f"run-curtain-{part}", els)
        by_type[f"*-{part}-we"] = {"base": path, "rotateY": 0}
        by_type[f"*-{part}-ns"] = {"base": path, "rotateY": 90}
    block("run-curtain", {
        "variantgroups": [{"code": "part", "states": list(curtain)}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-lower-we"], "decorative": ["*-lower-we"]},
        "blockmaterial": "Cloth", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.4, "x2": 1, "y2": 1, "z2": 0.6},
                               "*-ns": {"x1": 0.4, "y1": 0, "z1": 0, "x2": 0.6, "y2": 1, "z2": 1}},
        "lightAbsorption": 0, "resistance": 0.5, "drops": drops(("game:cloth-plain", 0.5, 0.5)), "sounds": CLOTH,
    }, "Level !: a pale green privacy curtain, walk-through. Stacked rel 1-4: lower, middle, upper, top (the mesh band and "
       "the ceiling track). Axis we: the curtain runs west-east (its faces look north and south)")
    name("run-curtain-*", "Privacy Curtain")

    # The Safe Zone: wire shelving with supplies (back to the wall), a cot (two blocks)
    ws = [bx(f"Post{n}", (x, 0, z), (x + 0.6, 16, z + 0.6), "wirepost") for n, (x, z) in enumerate(((1, 11), (14.4, 11), (1, 15.4), (14.4, 15.4)))]
    for n, y in enumerate((1.5, 7, 12.5)):
        ws.append(bx(f"Wire{n}", (1, y, 11), (15, y + 0.4, 16), "wireshelf", faces=("up", "down")))
        ws.append(bx(f"Lip{n}", (1, y + 0.4, 11), (15, y + 1, 11.4), "wirepost"))
    for n, x in enumerate((2.5, 5, 7.5)):
        ws += [bx(f"Bottle{n}", (x, 7.4, 12.5), (x + 1.6, 11.4, 14.1), "almondbottle"), bx(f"Cap{n}", (x + 0.4, 11.4, 12.9), (x + 1.2, 12, 13.7), "bottlecap")]
    for n, y in enumerate((1.9, 2.8, 13.0)):
        ws.append(bx(f"Bar{n}", (9.5 if n < 2 else 4, y, 12), (13.5 if n < 2 else 8, y + 0.9, 13.8), "foil", rot=(0, (-8, 12, 5)[n], 0)))
    prop("run-safeshelf", "Shelf", ws, box=(0.06, 0, 0.68, 0.94, 1, 1), material="Metal", sounds=METAL,
         comment="White wire shelving in a Safe Zone side room, back to the south wall: Almond Water and Energy Bars",
         extra={"resistance": 1, "drops": drops(("almondwater", 1, 0), ("run-energybar", 1.5, 0.5))})
    cot = [bx("Blanket", (1.2, 6, 1), (14.8, 8, 31), "cotblanket"), bx("Pillow", (3, 8, 1.6), (13, 9.3, 6), "pillow"),
           bx("RailL", (0.8, 5, 0.6), (1.6, 6, 31.4), "chrome"), bx("RailR", (14.4, 5, 0.6), (15.2, 6, 31.4), "chrome"),
           bx("EndN", (0.8, 5, 0.6), (15.2, 6, 1.4), "chrome"), bx("EndS", (0.8, 5, 30.6), (15.2, 6, 31.4), "chrome")]
    for n, z in enumerate((2, 16, 30)):
        cot += [bx(f"LegL{n}", (1, 0, z - 0.4), (1.8, 5, z + 0.4), "chrome"), bx(f"LegR{n}", (14.2, 0, z - 0.4), (15, 5, z + 0.4), "chrome"),
                bx(f"Brace{n}", (1.8, 0.4, z - 0.3), (14.2, 1, z + 0.3), "chrome")]
    prop("run-safecot", "Cot", {"head": clip(cot, "z", 0, 16, 0), "foot": clip(cot, "z", 16, 32, -16)},
         box=(0, 0, 0, 1, 0.5, 1), material="Cloth", sounds=CLOTH,
         comment="A cot in a Safe Zone side room, two blocks (head, foot; head to the north). Decor, not a bed",
         extra={"drops": drops(("game:cloth-plain", 1, 0.5), ("metalbracket", 1, 0.5))})


# ======================= What trips a sprinter =======================

def trip_props():
    """
    What trips a runner who sprints over it on the ground (RunSystem.Trip): toys spilled from a tipped crate, cardboard
    boxes, a tangle of extension cord, fallen ceiling. Walked through, not round, but (0.514.0, the user's play-test:
    "they only looked like a pile of papers") drawn as the heaps they are, up to half a block high and filling the tile,
    so they read as something in the way: jump them, or walk. They were flat (a toy car 4 voxels high, two small boxes,
    a cord a voxel thick, shards of ceiling tile 0.6 voxels thick) and in the red murk looked like litter. The codes,
    kinds and footprints are as before.
    """
    save(noise(0x2A5CB8, 3, "toyblue"), "toyblue")

    # Toys: a tipped toy crate, the car, building blocks and a ball spilled out of it
    car = [bx("Body", (2.5, 1.2, 3), (11.5, 4.4, 8.5), "toyred"), bx("Cab", (4, 4.4, 3.8), (9, 6.6, 7.7), "toyyellow"),
           bx("Window", (3.9, 5, 4.4), (4, 6.2, 7.1), "plug", faces=("west",)),
           bx("Bumper", (1.8, 1.2, 3.6), (2.5, 2.8, 7.9), "toyyellow"), bx("BumperB", (11.5, 1.2, 3.6), (12.2, 2.8, 7.9), "toyyellow")]
    for n, (x, z) in enumerate(((4.2, 2.6), (9.8, 2.6), (4.2, 8.9), (9.8, 8.9))):
        car.append(bx(f"Wheel{n}", (x - 1.3, 0, z - 0.5), (x + 1.3, 2.6, z + 0.5), "rubber"))
    car = [dict(e, rotationY=22, rotationOrigin=[7, 0, 6]) for e in car]
    crate = [bx("CrateBack", (9, 0, 15), (15.5, 6, 15.8), "plank"), bx("CrateBase", (9, 0, 10), (15.5, 0.8, 15), "plank"),
             bx("CrateL", (9, 0.8, 10), (9.8, 6, 15), "plank"), bx("CrateR", (14.7, 0.8, 10), (15.5, 6, 15), "plank"),
             bx("CrateLid", (9, 6, 10), (15.5, 6.8, 15.8), "plank")]
    blocks = [bx("Block1", (3, 0, 11), (5.4, 2.4, 13.4), "toyblue", rot=(0, 20, 0)),
              bx("Block2", (5.6, 0, 12.6), (8, 2.4, 15), "toyyellow", rot=(0, -35, 0)),
              bx("Block3", (3.4, 2.4, 11.4), (5.4, 4.4, 13.4), "toyred", rot=(0, 10, 0), origin=(4.2, 2.4, 12.2)),
              bx("Block4", (12, 0.8, 11), (14, 2.8, 13), "toyblue"), bx("Block5", (10.2, 0.8, 12.4), (11.8, 2.4, 14), "toyred"),
              bx("Block6", (12.6, 0, 6.5), (14.6, 2, 8.5), "toyyellow", rot=(0, 40, 0))]
    ball = octagon("Ball", "x", (1.9, 2.0, 7.0), 1.9, 1.5, "toyblue") + [bx("BallBand", (0.3, 1.6, 6.2), (3.5, 2.4, 7.8), "toyyellow")]
    prop("run-toycar", "Toys", car + crate + blocks + ball, box=(0.06, 0, 0.06, 0.94, 0.42, 0.94), collide=False,
         material="Wood", sounds=WOOD, comment="A toy crate tipped over in the hall, the car, the blocks and a ball strewn "
         "round it (walked through; trips a sprinter: jump it)", extra={"drops": []})

    # Boxes: one on its side with its flaps open, another on top of it, a third flattened and kicked aside
    flaps = ("north", "east", "south", "west", "down")
    bxs = [bx("Big", (1.5, 0, 2), (9.5, 7, 9), "runbox", faces=flaps),
           bx("BigTop", (1.5, 0, 2), (9.5, 7, 9), "runboxtop", faces=("up",), uv=[0, 0, 16, 16]),
           bx("FlapA", (1.5, 6.6, 1.2), (9.5, 7, 4.4), "runbox", rot=(-58, 0, 0), origin=(5.5, 6.8, 2)),
           bx("FlapB", (9.6, 3.6, 2), (10, 7, 9), "runbox", rot=(0, 0, -40), origin=(9.8, 7, 5.5)),
           bx("Top", (3, 7, 3.5), (8.5, 11, 8), "runbox", faces=flaps, rot=(0, -18, 8), origin=(5.75, 7, 5.75)),
           bx("TopTop", (3, 7, 3.5), (8.5, 11, 8), "runboxtop", faces=("up",), uv=[0, 0, 16, 16], rot=(0, -18, 8), origin=(5.75, 7, 5.75)),
           bx("Second", (9, 0, 9), (14.6, 5.5, 14.6), "runbox", faces=flaps, rot=(0, 24, 0)),
           bx("SecondTop", (9, 0, 9), (14.6, 5.5, 14.6), "runboxtop", faces=("up",), uv=[0, 0, 16, 16], rot=(0, 24, 0)),
           bx("Flat", (1, 0, 10.5), (8, 1, 15.5), "runbox", faces=("north", "east", "south", "west", "up"), rot=(0, 9, 0)),
           bx("Spill", (11, 0, 3), (14.6, 2.2, 6.5), "runbox", rot=(0, -30, 0))]
    prop("run-boxes", "Boxes", bxs, box=(0.06, 0, 0.1, 0.94, 0.7, 0.94), collide=False, material="Wood", sounds=CLOTH,
         comment="Cardboard boxes dumped in the hall, one on its side with its flaps open, one on top, one flattened "
                 "(walked through; trips a sprinter: jump it)", extra={"drops": drops(("game:paper-parchment", 0.5, 0.5))})

    # Cord: an orange extension cord in loops standing off the floor, a black cable with it, a power strip. It runs
    # along the model's Z, the whole tile, so a row of them crosses the hall; the ends meet the next tile's at x 7.5-8.5
    cord = [bx("RunA", (7.5, 0, 0), (8.5, 0.9, 2.6), "cord"), bx("RunB", (7.5, 0, 7.2), (8.5, 0.9, 9.4), "cord"),
            bx("RunC", (7.5, 0, 13.6), (8.5, 0.9, 16), "cord")]
    for n, (z0, z1, high, lean) in enumerate(((2.6, 7.2, 4.6, 18), (9.4, 13.6, 3.6, -24))):
        # A loop stood up off the floor, leaning a little: the thing a foot catches in
        o = (8, 0, (z0 + z1) / 2)
        cord += [bx(f"Loop{n}A", (7.5, 0, z0), (8.5, high, z0 + 1), "cord", rot=(0, 0, lean), origin=o),
                 bx(f"Loop{n}B", (7.5, high - 1, z0 + 1), (8.5, high, z1 - 1), "cord", rot=(0, 0, lean), origin=o),
                 bx(f"Loop{n}C", (7.5, 0, z1 - 1), (8.5, high, z1), "cord", rot=(0, 0, lean), origin=o)]
    cord += [bx("Black1", (3.5, 0, 1), (4.3, 0.8, 6), "cable", rot=(0, 25, 0), origin=(5, 0, 6)),
             bx("Black2", (4.6, 0, 6), (5.4, 2.6, 6.8), "cable", rot=(0, 25, 0), origin=(5, 0, 6)),
             bx("Black3", (4.6, 1.8, 6.8), (5.4, 2.6, 11), "cable", rot=(0, 25, 0), origin=(5, 0, 6)),
             bx("Black4", (4.6, 0, 11), (5.4, 2.6, 11.8), "cable", rot=(0, 25, 0), origin=(5, 0, 6)),
             bx("Coil1", (10.5, 0, 2), (14.5, 1, 6), "cord"), bx("Coil2", (11, 1, 2.5), (14, 2, 5.5), "cord"),
             bx("CoilHole", (11.6, 2, 3.1), (13.4, 2.05, 4.9), "plug", faces=("up",)),
             bx("Strip", (10, 0, 9.5), (13.5, 1.6, 15), "plug", rot=(0, -12, 0), origin=(11.75, 0, 12.25)),
             bx("StripLed", (11.2, 1.6, 10.2), (12.2, 1.75, 11.2), "toyred", glow=120, faces=("up",), rot=(0, -12, 0), origin=(11.75, 0, 12.25)),
             bx("Plug", (8.6, 0, 12), (10, 1.8, 13.8), "plug", rot=(0, -12, 0), origin=(11.75, 0, 12.25))]
    prop("run-cord", "Tangled Cords", cord, box=(0.06, 0, 0, 0.94, 0.3, 1), collide=False, material="Cloth", sounds=CLOTH,
         comment="An orange extension cord stretched across the hall in loops off the floor, a black cable and a power "
                 "strip with it, along the model's Z (north-south when facing north). Walked through; trips a sprinter: "
                 "jump it", extra={"drops": drops(("scrapwire", 1, 0.5))})

    # Fallen ceiling: a heap of broken deck and tile under the hole, tiles on it tipped up, a bent T-bar sticking out
    debris = [bx("Heap", (2.5, 0, 3), (13, 2.6, 13), "rubble"),
              bx("HeapTop", (4.5, 2.6, 5), (11, 4.4, 11), "rubbledark"),
              bx("Lump1", (0.8, 0, 10), (4.6, 2.2, 14.2), "rubble", rot=(0, 25, 0)),
              bx("Lump2", (11, 0, 1.2), (14.8, 1.8, 5), "rubbledark", rot=(0, -20, 0)),
              bx("Lump3", (12.4, 0, 11), (15, 1.4, 14.6), "rubble"),
              bx("Tile1", (1, 0, 1.5), (8.5, 0.8, 9), "ceiltile", rot=(0, 15, 24), origin=(1, 0, 5)),
              bx("Tile2", (8, 2.2, 7), (15, 3, 14), "ceiltile", rot=(-20, -10, 0), origin=(11.5, 2.6, 7)),
              bx("Tile3", (3, 3.6, 8), (8.5, 4.4, 13.5), "ceiltile", rot=(16, 30, -10), origin=(5.75, 4, 10.75)),
              bx("TbarA", (7.6, 2, 3), (8.4, 2.8, 11), "tbar", rot=(-32, 20, 0), origin=(8, 2.4, 11)),
              bx("TbarB", (1.5, 0, 13.6), (13.5, 0.8, 14.4), "tbar", rot=(0, -12, 12), origin=(1.5, 0, 14)),
              bx("WireA", (9.5, 3, 4.5), (10.1, 3.6, 13), "wire", rot=(14, 40, 0), origin=(9.8, 3.3, 8.75)),
              bx("Dust", (0.5, 0, 0.5), (15.5, 0.15, 15.5), "rubbledark", faces=("up",))]
    prop("run-debris", "Fallen Ceiling", debris, box=(0.06, 0, 0.06, 0.94, 0.4, 0.94), collide=False, material="Stone", sounds=STONE,
         comment="A heap of fallen ceiling: broken deck, tiles tipped up on it, a bent T-bar (walked through; trips a "
                 "sprinter: jump it)", extra={"drops": []})


# ======================= Layout version 6: what blocks the hall =======================

def kinds_block(code, parts, boxes, comment, material="Metal", sounds=METAL, extra=None):
    """A block of several kinds, each facing <side>: parts {kind: boxes}, boxes {kind: [collision boxes] or None}."""
    by_type, coll, sel = {}, {}, {}
    for kind, els in parts.items():
        path = shape(f"{code}-{kind}", els)
        for sd in SIDES:
            by_type[f"*-{kind}-{sd}"] = {"base": path, "rotateY": ROTATE[sd]}
            got = boxes.get(kind)
            coll[f"*-{kind}-{sd}"] = [K.cuboid(b, sd) for b in got] if got else None
            sel[f"*-{kind}-{sd}"] = [K.cuboid(b, sd) for b in (got or [(0.1, 0, 0.1, 0.9, 1, 0.9)])]
    first = f"*-{next(iter(parts))}-north"
    data = {"variantgroups": [{"code": "kind", "states": list(parts)}, {"code": "side", "states": SIDES}],
            "creativeinventory": {"general": [first], "decorative": [first]},
            "blockmaterial": material, "drawtype": "json", "shapeByType": by_type,
            "collisionboxesByType": coll, "selectionboxesByType": sel,
            "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1.5, "sounds": sounds}
    if extra:
        data.update(extra)
    block(code, data, comment)


def gauntlet():
    """
    Layout version 6 packs the hall (WorldLayout.PlanRunGauntlet): the ceiling come down (a slab hanging from the hole
    onto a heap of rubble, or a heap you can jump, live wires hanging over it: Fandom's "the walls and the ceiling may
    also collapse ... power lines may hang from above"), barricades of beds and chairs, tall supply cabinets with a door
    hanging open (the open cabinet of Escape the Backrooms' hallway), and gurneys tipped on their sides.
    """
    # ---- Textures ----
    img = noise(0x8C8A84, 6, "rubble")  # the concrete deck broken up: grey, chipped, dark cracks
    rng = random.Random(seed_of("rubblechips"))
    px = img.load()
    for _ in range(46):
        x, y, f = rng.randrange(S), rng.randrange(S), rng.choice((0.62, 0.75, 1.18))
        for dx in range(rng.randint(1, 3)):
            for dy in range(rng.randint(1, 2)):
                px[(x + dx) % S, (y + dy) % S] = shade(px[(x + dx) % S, (y + dy) % S], f)
    save(img, "rubble")
    img = noise(0x6A665E, 6, "rubbledark")
    speckle(img, "rubbledarksp", 0.05, rgb(0x4A463F), 2)
    save(img, "rubbledark")
    save(noise(0x6A4630, 4, "rebar"), "rebar")
    save(noise(0x1E1E20, 2, "cable"), "cable")
    save(noise(0xC87A3A, 3, "copper"), "copper")
    # A hospital mattress: blue-grey wipe-clean vinyl, a seam round it, a stain
    img = noise(0x5E7286, 3, "mattress")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x46566A))
    T.blotch(img, (20, 12), 7, (92, 84, 60), 0.35, seed_of("mattressstain"))
    save(img, "mattress")
    save(grain(noise(0x9A7650, 4, "plank"), "plankg", 6, vertical=False, streak=0.6), "plank")
    # Supply cabinet: pale green-grey enamelled steel; its doors with a label holder and vent slots
    save(grain(noise(0x9AA6A0, 2, "cabsteel"), "cabsteelg", 2), "cabsteel")
    img = grain(noise(0x9AA6A0, 2, "cabdoor"), "cabdoorg", 2)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x7A8680))
    d.rectangle([9, 6, 22, 10], fill=rgb(0xE8E6DA), outline=rgb(0x5A625E))
    d.line([11, 8, 20, 8], fill=rgb(0x8A8A86))
    for y in (22, 25, 28):
        d.line([8, y, 23, y], fill=rgb(0x6A7470))
    save(img, "cabdoor")
    save(noise(0x2E3432, 2, "cabin"), "cabin")

    # ---- Collapsed ceiling ----
    # The slab hangs from its hinge at the ceiling (south edge, rel 4's top) down onto the heap (north edge, rel 1):
    # leaning north. One straight plane, a segment of it in each block
    top_z, foot_z, foot_y = 13.5, 3.0, 11.0
    slope = (top_z - foot_z) / (64 - foot_y)
    tilt = math.degrees(math.atan(slope))

    def slab(k, y0=None):
        """The slab's segment in block k (0 = rel 1), from local height y0 (default: the whole block)."""
        lo = 16 * k + (y0 if y0 is not None else 0)
        yc = (lo + 16 * k + 16) / 2
        h = (16 * k + 16 - lo) / math.cos(math.radians(tilt))
        zc, y = foot_z + (yc - foot_y) * slope, yc - 16 * k
        o = (8, y, zc)
        out = [bx(f"Slab{k}", (1, y - h / 2, zc - 1.1), (15, y + h / 2, zc + 1.1), "rubble", rot=(tilt, 0, 0), origin=o),
               bx(f"SlabTiles{k}", (1.4, y - h / 2, zc - 1.6), (14.6, y + h / 2, zc - 1.1), "ceiltile", rot=(tilt, 0, 0), origin=o,
                  faces=("north", "east", "west", "up", "down"))]
        if k in (1, 2):
            # Rebar out of the broken edges
            out += [bx(f"RebarW{k}", (-1.5, y - 2, zc - 0.3), (1, y - 1.4, zc + 0.3), "rebar", rot=(tilt, 0, 0), origin=o),
                    bx(f"RebarE{k}", (15, y + 3, zc - 0.3), (17, y + 3.6, zc + 0.3), "rebar", rot=(tilt, 0, 12), origin=o)]
        return out

    def wires(drop):
        """Live wires hanging out of the hole, one with a bare copper end; a ceiling tile hanging by one edge."""
        return [bx("CableA", (5, 16 - drop, 6), (5.6, 16, 6.6), "cable", rot=(0, 0, 8), origin=(5.3, 16, 6.3)),
                bx("CableB", (9.5, 16 - drop * 0.6, 9), (10.1, 16, 9.6), "cable", rot=(-12, 0, 0), origin=(9.8, 16, 9.3)),
                bx("CableC", (11, 16 - drop * 0.85, 4), (11.6, 16, 4.6), "cable"),
                bx("Copper", (10.9, 15.2 - drop * 0.85, 3.9), (11.7, 16 - drop * 0.85, 4.7), "copper", glow=60),
                bx("Flap", (2, 7, 11), (9, 16, 11.6), "ceiltile", rot=(-24, 0, 0), origin=(5.5, 16, 11.3))]

    heap = [bx("Base", (0.3, 0, 0.3), (15.7, 5, 15.7), "rubble"),
            bx("Mound", (1.5, 5, 1), (15, 10, 14.5), "rubbledark"),
            bx("Crown", (3, 10, 2), (13, 14, 12), "rubble"),
            bx("Peak", (5, 14, 3.5), (11, 16, 9), "rubbledark"),
            bx("ChunkA", (0.5, 3, 10.5), (6, 8, 15.5), "rubbledark", rot=(0, 25, 0)),
            bx("ChunkB", (10, 4, 0.5), (15.5, 9, 5.5), "rubble", rot=(0, -20, 10)),
            bx("ChunkC", (11, 9, 9), (15.3, 13, 14), "rubble", rot=(15, 0, 0)),
            bx("ShardA", (1, 5.2, 2), (7, 5.8, 8), "ceiltile", rot=(0, 15, 12)),
            bx("ShardB", (8, 10.2, 12), (14, 10.8, 15.5), "ceiltile", rot=(-20, 0, 0)),
            bx("Tbar", (2, 8, 13), (14, 8.6, 13.6), "tbar", rot=(0, 20, -15))] + slab(0, foot_y)
    rubble = [bx("Base", (0.5, 0, 0.5), (15.5, 4, 15.5), "rubble"),
              bx("Mound", (2, 4, 2), (14, 8, 13.5), "rubbledark"),
              bx("Crown", (4, 8, 4), (11, 11, 10), "rubble"),
              bx("ChunkA", (1, 2, 11), (6.5, 7, 15.5), "rubbledark", rot=(0, 30, 0)),
              bx("ChunkB", (10.5, 3, 1), (15.5, 7.5, 5.5), "rubble", rot=(0, -15, 8)),
              bx("ShardA", (2, 4.2, 2.5), (8, 4.8, 8), "ceiltile", rot=(0, 20, 10)),
              bx("ShardB", (8, 8.2, 9), (14, 8.8, 14), "ceiltile", rot=(-15, 30, 0)),
              bx("Tbar", (1.5, 5, 12.5), (14.5, 5.6, 13.1), "tbar", rot=(0, -25, 12))]
    hang = slab(3) + [bx("Torn", (0.8, 15, 12.2), (15.2, 16, 15.8), "ceiltile")] + wires(8)
    parts = {"heap": heap, "slab": slab(1), "slabhigh": slab(2), "hang": hang, "rubble": rubble, "wires": wires(12)}

    def plane_box(k):
        """The slab's collision in block k: the depth of the tile it takes at that height."""
        z0 = foot_z + (16 * k - foot_y) * slope - 1.8
        z1 = foot_z + (16 * k + 16 - foot_y) * slope + 1.8
        return (1 / 16, 0, max(0, z0) / 16, 15 / 16, 1, min(16, z1) / 16)
    kinds_block("run-collapse", parts,
                {"heap": [(0, 0, 0, 1, 1, 1)], "slab": [plane_box(1)], "slabhigh": [plane_box(2)],
                 "rubble": [(0.03, 0, 0.03, 0.97, 0.75, 0.97)]},
                "Level ! (layout version 6): the ceiling come down, stacked rel 1-4. A slab hanging from the hole onto a heap of "
                "rubble, leaning toward <side>: heap (rel 1, a block high), slab, slabhigh, hang (its top, still hinged, and live "
                "wires); or rubble (rel 1, 0.75 high: jump it) under wires (rel 4). Fixed like the hallway",
                material="Stone", sounds=STONE, extra={"resistance": 99999, "drops": []})
    for kind, english in (("heap", "Collapsed Ceiling"), ("slab", "Collapsed Ceiling"), ("slabhigh", "Collapsed Ceiling"),
                          ("hang", "Collapsed Ceiling"), ("rubble", "Rubble"), ("wires", "Hanging Wires")):
        name(f"run-collapse-{kind}-*", english)

    # The ceiling over a collapse: a ragged hole into the dark above, a broken T-bar hanging
    hole = [bx("RingN", (0, 0, 0), (16, 16, 3.5), "ceiltile"), bx("RingS", (0, 0, 12), (16, 16, 16), "ceiltile"),
            bx("RingW", (0, 0, 3.5), (4, 16, 12), "ceiltile"), bx("RingE", (11, 0, 3.5), (16, 16, 12), "ceiltile"),
            bx("JagA", (4, 0, 3.5), (7, 1, 6), "ceiltile"), bx("JagB", (8, 0, 10), (11, 1, 12), "ceiltile"),
            bx("JagC", (10, 0, 5), (11, 1, 8), "ceiltile"),
            bx("Plenum", (4, 10, 3.5), (11, 16, 12), "duct", faces=("down",)),
            bx("Conduit", (3.8, 12, 7), (11.2, 13, 8), "ventmetal"),
            bx("TbarHang", (5, -6, 7.7), (5.6, 1, 8.3), "tbar", rot=(0, 0, 25), origin=(5.3, 1, 8))]
    block("run-ceilinghole", {
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Stone", "drawtype": "json", "shape": {"base": shape("run-ceilinghole", hole)},
        "sidesolid": {"all": False, "up": True}, "sideopaque": {"all": False}, "lightAbsorption": 99,
        "resistance": 99999, "drops": [], "sounds": STONE,
    }, "Level ! (layout version 6): the ceiling over a collapse, a ragged hole into the dark above, a broken T-bar hanging. "
       "Fixed like the hallway")
    name("run-ceilinghole", "Broken Ceiling")

    # ---- Barricades: beds and chairs piled up, a supply cabinet, a gurney on its side ----
    # A bed tipped on its side across the tile, the mattress on edge behind boards nailed across, another mattress
    # upright above it and a chair upside down on top. Front to the north
    beds = [bx("Mattress", (0.5, 1, 6), (15.5, 15, 10), "mattress"),
            bx("Deck", (0.3, 0.5, 10), (15.7, 15.5, 10.8), "gurneyframe"),
            bx("Rail", (0, 15, 5.5), (16, 16, 10.6), "chrome"),
            bx("ChairSeat", (2, 0, 1), (8, 1, 6), "chairplastic", rot=(0, 15, 0)),
            bx("ChairBack", (2, 1, 0.6), (8, 6, 1.6), "chairplastic", rot=(0, 15, 0), origin=(5, 1, 3)),
            bx("BoardA", (0, 4, 5), (16, 6.5, 6), "plank", rot=(0, 0, 4)),
            bx("BoardB", (0, 10, 5), (16, 12.5, 6), "plank", rot=(0, 0, -3)),
            bx("Upright", (1, 16, 6.5), (15, 30, 9.5), "mattress", rot=(-8, 0, 0), origin=(8, 16, 8)),
            bx("BoardC", (0, 20, 5), (16, 22.5, 6), "plank", rot=(0, 0, -5)),
            bx("TopSeat", (9.5, 25, 10), (15, 26, 15), "chairplastic"),
            bx("TopBack", (9.5, 20, 14.5), (15, 25, 15.5), "chairplastic")]
    for n, (x, y) in enumerate(((2, 3), (13, 3), (2, 11), (13, 11))):
        beds += [bx(f"Leg{n}", (x, y, 10.8), (x + 1, y + 1, 15.5), "chrome"),
                 bx(f"Castor{n}", (x - 0.5, y - 0.5, 15), (x + 1.5, y + 1.5, 16), "rubber")]
    for n, x in enumerate((10, 14)):
        beds += [bx(f"TopLeg{n}", (x, 26, 10.5), (x + 0.7, 31, 11.2), "beamsteel"),
                 bx(f"TopLegB{n}", (x, 26, 14), (x + 0.7, 31, 14.7), "beamsteel")]
    # A tall supply cabinet, back to the wall (south), the left door shut and the right one hanging open into the hall
    cab = [bx("Back", (1, 0, 15), (15, 31, 16), "cabsteel"), bx("Inside", (2, 1, 14.8), (14, 30, 15), "cabin", faces=("north",)),
           bx("SideW", (1, 0, 8), (2, 31, 15), "cabsteel"), bx("SideE", (14, 0, 8), (15, 31, 15), "cabsteel"),
           bx("Top", (1, 30, 8), (15, 31, 15), "cabsteel"), bx("Bottom", (1, 0, 8), (15, 1, 15), "cabsteel"),
           bx("DoorL", (2, 0.5, 7.4), (8, 30.5, 8), "cabdoor", full=True, faces=("north",)),
           bx("DoorLEdge", (2, 0.5, 7.4), (8, 30.5, 8), "cabsteel", faces=("east", "west", "up", "down", "south")),
           bx("PullL", (7, 13, 6.8), (7.6, 19, 7.4), "chrome"),
           bx("LabelL", (3.4, 24.6, 7.15), (6.6, 26.4, 7.4), "cablabel", faces=("north", "east", "west", "up", "down")),
           bx("DoorR", (14, 0.5, 1.5), (14.6, 30.5, 8), "cabdoor", full=True, faces=("west", "east")),
           bx("DoorREdge", (14, 0.5, 1.5), (14.6, 30.5, 8), "cabsteel", faces=("north", "south", "up", "down")),
           bx("PullR", (13.4, 13, 2), (14, 19, 2.6), "chrome"),
           bx("HingeA", (13.9, 3, 7.6), (14.8, 6, 8.4), "chrome"), bx("HingeB", (13.9, 25, 7.6), (14.8, 28, 8.4), "chrome"),
           bx("BoxA", (8.5, 1, 10), (13.5, 5, 14.5), "runbox"), bx("BoxB", (8.5, 25, 10), (13.5, 28, 14), "runbox"),
           bx("BottleA", (9, 9, 11), (10.5, 13, 12.5), "almondbottle"), bx("BottleB", (11, 9, 11), (12.5, 13, 12.5), "almondbottle"),
           bx("Bag", (9.5, 17, 11), (12.5, 22, 12), "ivbag")]
    for n, y in enumerate((8, 15.5, 24)):
        cab.append(bx(f"Shelf{n}", (2, y, 8.5), (14, y + 0.6, 14.8), "cabsteel"))
    # A gurney tipped on its side: the gurney turned so its raised rail lies on the floor, the mattress on edge, the
    # wheels in the air to the west
    tipped = []
    for e in gurney_parts():
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        tex_ = next(iter(e["faces"].values()))["texture"][1:]
        tipped.append(bx(e["name"], (y1, x1 * 0.94, z1), (y2, x2 * 0.94, z2), tex_))
    parts = {"beds-lower": clip(beds, "y", 0, 16, 0), "beds-upper": clip(beds, "y", 16, 32, -16),
             "cabinet-lower": clip(cab, "y", 0, 16, 0), "cabinet-upper": clip(cab, "y", 16, 32, -16),
             "tipped-head": clip(tipped, "z", 0, 16, 0), "tipped-foot": clip(tipped, "z", 16, 32, -16)}
    cab_boxes = lambda top: [(1 / 16, 0, 0.5, 15 / 16, top, 1), (13.4 / 16, 0, 1.5 / 16, 14.6 / 16, top, 0.5)]
    kinds_block("run-barricade", parts,
                {"beds-lower": [(0, 0, 0.3, 1, 1, 1)], "beds-upper": [(0, 0, 0.36, 1, 0.97, 1)],
                 "cabinet-lower": cab_boxes(1), "cabinet-upper": cab_boxes(0.97),
                 "tipped-head": [(0, 0, 0, 1, 0.94, 1)], "tipped-foot": [(0, 0, 0, 1, 0.94, 1)]},
                "Level ! (layout version 6): what blocks the hall, facing <side>. beds-lower/upper: a barricade of beds, "
                "mattresses and chairs, two blocks tall (go round it). cabinet-lower/upper: a tall supply cabinet, back to the "
                "wall, its right door hanging open (go round it). tipped-head/foot: a gurney on its side, two blocks long (head "
                "to the north), 0.94 high (jump it)",
                extra={"dropsByType": {
                    "*-beds-*": drops(("metalbracket", 1, 0.5), ("game:cloth-plain", 1, 0.5)),
                    "*-cabinet-*": drops(("metalbracket", 1.5, 0.5), ("game:bandage-clean", 0.3, 0.3), ("almondwater", 0.15, 0)),
                    "*-tipped-*": drops(("metalbracket", 1, 0.5), ("game:cloth-plain", 0.5, 0.5))}})
    name("run-barricade-beds-*", "Barricade")
    name("run-barricade-cabinet-*", "Supply Cabinet")
    name("run-barricade-tipped-*", "Overturned Gurney")


# ======================= Item: the Energy Bar =======================

def items():
    item_textures()
    els = [bx("Bar", (3, 0, 6), (13, 2, 10), "foil", faces=("north", "south", "down"), uv=[0, 8, 16, 11]),
           bx("Top", (3, 0, 6), (13, 2, 10), "foil", faces=("up",), uv=[0, 0, 16, 6]),
           bx("CrimpL", (2, 0.3, 6.2), (3, 1.7, 9.8), "foil", uv=[0, 6, 2, 8]),
           bx("CrimpR", (13, 0.3, 6.2), (14, 1.7, 9.8), "foil", uv=[0, 6, 2, 8]),
           bx("CrimpLTip", (1.5, 0.6, 6.4), (2, 1.4, 9.6), "foil", uv=[0, 6, 2, 8]),
           bx("CrimpRTip", (14, 0.6, 6.4), (14.5, 1.4, 9.6), "foil", uv=[0, 6, 2, 8])]
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {"foil": f"backrooms:item/{TAG}/energybar"}, "elements": els}
    write_json(os.path.join(ASSETS, "shapes", "item", TAG, "energybar.json"), data)
    data = {"code": "run-energybar", "class": "BackroomsEnergyBar", "maxstacksize": 16,
            "shape": {"base": f"item/{TAG}/energybar"}, "textures": {"foil": {"base": f"item/{TAG}/energybar"}},
            "creativeinventory": {"general": ["*"], "items": ["*"]},
            "nutritionProps": {"satiety": 160, "foodcategory": "Grain"}, "materialDensity": 600,
            "attributes": {"handbook": {"groupBy": ["run-energybar"]}}}
    data.update(TRANSFORMS)
    data["guiTransform"] = {"rotation": {"x": -30, "y": 40, "z": 0}, "origin": {"x": 0.5, "y": 0.1, "z": 0.5}, "scale": 2.6}
    data["fpHandTransform"] = {"translation": {"x": 0, "y": 0.1, "z": 0.3}, "rotation": {"x": 0, "y": 80, "z": 10}, "scale": 1.8}
    data["tpHandTransform"] = {"translation": {"x": -0.8, "y": -0.1, "z": -0.6}, "rotation": {"x": 0, "y": 0, "z": -10}, "scale": 0.8}
    data["groundTransform"] = {"translation": {"x": 0, "y": 0, "z": 0}, "rotation": {"x": 0, "y": 0, "z": 0},
                               "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.5}
    K.ground_storable(data, scale=0.6)  # (13 pixels long: shrunk to fit a quadrant)
    write_json(os.path.join(ASSETS, "itemtypes", TAG, "energybar.json"), data,
               "Level !'s Energy Bar: food (satiety 160, Grain), and a second wind when eaten (BackroomsEnergyBar)")


# ======================= Sounds =======================

def fftconv(signal, kernel):
    n = len(signal) + len(kernel)
    m = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(signal, m) * np.fft.rfft(kernel, m), m)[: len(signal)]


def corridor(signal, rt60=1.4, slap=0.06, wet=0.35, seed=1):
    """A long hard corridor: a slap echo off the far wall and a bright, long tail."""
    rng = np.random.default_rng(seed)
    out = np.copy(signal)
    d = int(slap * RATE)
    out[d:] += 0.45 * signal[:-d]
    out[2 * d:] += 0.2 * signal[:-2 * d]
    n = int(rt60 * RATE)
    t = np.arange(n) / RATE
    kernel = rng.normal(size=n) * np.exp(-6.9 * t / rt60)
    kernel = band(kernel, 200, 5000)
    kernel *= wet / np.sqrt(np.sum(kernel ** 2))
    return out + fftconv(signal, kernel) * 1.5


def periodic(make, period):
    """Builds a seamless loop: renders three periods of a periodic source, processes them, keeps the middle one."""
    full = make(3 * period)
    n = int(period * RATE)
    return full[n:2 * n]


def wrap_place(out, sound, at):
    i = int(at * RATE) % len(out)
    n = len(sound)
    end = i + n
    if end <= len(out):
        out[i:end] += sound
    else:
        k = len(out) - i
        out[i:] += sound[:k]
        out[: n - k] += sound[k:]


def alarm_tone(length):
    t = np.arange(int(length * RATE)) / RATE
    hi = (np.floor(t / 0.5) % 2) == 0
    f = np.where(hi, 880.0, 659.25)
    phase = 2 * np.pi * np.cumsum(f) / RATE
    # Square-ish: odd harmonics, then clipped hard through a cheap ceiling speaker
    tone = sum(np.sin(k * phase) / k for k in (1, 3, 5, 7, 9))
    tone = np.tanh(2.2 * tone)
    # Each tone starts with a click of the relay
    edge = (t % 0.5) < 0.004
    tone += 0.3 * edge * np.sign(np.sin(phase))
    tone = band(tone, 400, 3500)
    tone += 0.12 * np.sin(2 * np.pi * 120 * t) * band(tone, 400, 3500)  # the speaker buzzing on mains
    return tone


def alarm_signals():
    loud = periodic(lambda L: corridor(alarm_tone(L), 1.4, 0.06, 0.35, 11), 8.0)
    # Muffled in the walls, a boom of the wall resonating with it, but still the two tones of an alarm (both of them:
    # cut below 700 Hz, as it once was, it lost the high one and was only a dull thud)
    far = periodic(lambda L: band(corridor(alarm_tone(L), 1.8, 0.09, 0.5, 12), 200, 1400), 8.0)
    return loud, far


def horde():
    rng = np.random.default_rng(1401)
    L = 6.0
    n = int(L * RATE)
    out = np.zeros(n)
    # Feet and claws on vinyl, 20-30 a second
    at = 0.0
    while at < L:
        if rng.random() < 0.6:
            s = thud(0.08, rng.uniform(90, 160), rng, 0.9) * rng.uniform(0.3, 0.8)
        else:
            tt = seconds(0.03)
            s = band(rng.normal(size=len(tt)), 2000, 7000) * np.exp(-tt * 160) * rng.uniform(0.2, 0.5)
        wrap_place(out, s, at)
        at += rng.uniform(0.025, 0.05)
    # The growl bed: many low throats on an "oo"
    t = np.arange(n) / RATE
    bed = np.zeros(n)
    for k in range(5):
        f0 = rng.uniform(60, 120) * (1 + 0.04 * np.sin(2 * np.pi * (k + 1) / L * t + rng.uniform(0, 6)))
        bed += vowel(t, f0, ((300, 90, 1), (870, 120, 0.4)), 0.5, rng) * (0.6 + 0.4 * np.sin(2 * np.pi * (k % 3 + 1) / L * t) ** 2)
    out += 0.35 * bed / np.max(np.abs(bed))
    # Barks
    for b in range(3):
        tt = seconds(0.22)
        f0 = rng.uniform(320, 480) * (1 - 0.3 * tt / 0.22)
        bark = vowel(tt, f0, ((700, 150, 1), (1200, 200, 0.7)), 0.6, rng) * np.exp(-tt * 12) * np.minimum(1, tt / 0.01)
        wrap_place(out, 0.8 * bark / np.max(np.abs(bark)), rng.uniform(0, L))
    # Shrieks
    for s in range(2):
        tt = seconds(0.6)
        f = rng.uniform(2200, 3000) + 1200 * np.sin(np.pi * tt / 0.6)
        sh = np.sin(2 * np.pi * np.cumsum(f) / RATE) + 0.4 * band(rng.normal(size=len(tt)), 2000, 4500)
        wrap_place(out, 0.35 * sh * np.sin(np.pi * tt / 0.6) ** 2, rng.uniform(0, L))
    # Moth wings overhead: noise beating at 25 Hz
    flutter = band(rng.normal(size=n), 150, 1200) * (0.5 + 0.5 * np.sin(2 * np.pi * 25 * t)) ** 3
    out += 0.12 * flutter / np.max(np.abs(flutter))
    out = periodic_reverb(out, 0.8)
    return out


def periodic_reverb(loop, rt60):
    tiled = np.concatenate([loop, loop, loop])
    wet = corridor(tiled, rt60, 0.05, 0.25, 13)
    n = len(loop)
    return wet[n:2 * n]


def safezone(far):
    rng = np.random.default_rng(1402)
    L = 10.0
    n = int(L * RATE)
    t = np.arange(n) / RATE
    vent = band(rng.normal(size=n), 200, 2200) * 0.5 + 0.6 * np.sin(2 * np.pi * 120 * t) + 0.2 * np.sin(2 * np.pi * 240 * t)
    vent *= 0.85 + 0.15 * np.sin(2 * np.pi * t / 5) ** 2
    vent = periodic_reverb(vent, 0.3)
    vent /= np.max(np.abs(vent))
    ghost = np.tile(far, 2)[:n]  # the alarm is periodic in 1 s, so 10 s of it loops
    ghost /= np.max(np.abs(ghost))
    return 0.9 * vent + 0.1 * ghost


def metal_ring(length, partials, rng, decay=6):
    t = seconds(length)
    out = np.zeros(len(t))
    for f, a in partials:
        out += a * np.sin(2 * np.pi * f * rng.uniform(0.98, 1.02) * t + rng.uniform(0, 6)) * np.exp(-t * decay * (f / 400) ** 0.5)
    return out


def rattle_tail(length, rng, rate=40, lo=2000, hi=6000):
    t = seconds(length)
    out = np.zeros(len(t))
    at = 0.0
    while at < length:
        tt = seconds(0.012)
        click = band(rng.normal(size=len(tt)), lo, hi) * np.exp(-tt * 300)
        place(out, click * (1 - at / length) * rng.uniform(0.3, 1), at)
        at += rng.exponential(1 / rate)
    return out


def bang(k):
    rng = np.random.default_rng(1410 + k)
    out = np.zeros(int(0.9 * RATE))
    place(out, thud(0.5, rng.uniform(55, 75), rng, 1.2), 0.0)
    place(out, 0.5 * metal_ring(0.8, [(180 + 20 * k, 1), (410 + 15 * k, 0.6), (730, 0.4), (1180, 0.25)], rng, 7), 0.0)
    place(out, 0.35 * rattle_tail(0.65, rng), 0.05)
    return corridor(out, 0.5, 0.03, 0.15, 20 + k)


def doorbreak():
    rng = np.random.default_rng(1420)
    L = 2.2
    n = int(L * RATE)
    out = np.zeros(n)
    # Tearing metal: a screech sweeping up through noise, juddering
    tt = seconds(0.7)
    f = 700 + 1300 * tt / 0.7
    screech = np.sin(2 * np.pi * np.cumsum(f) / RATE) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 37 * tt)))
    screech += 0.6 * band(rng.normal(size=len(tt)), 900, 3500)
    place(out, 0.5 * screech * np.minimum(1, tt / 0.05), 0.0)
    # A chain snapping: a ping, the links rattling away
    place(out, 0.6 * metal_ring(0.6, [(2500, 1), (3900, 0.5)], rng, 4), 0.5)
    place(out, 0.4 * rattle_tail(0.7, rng, 60), 0.52)
    # The door slamming down onto the floor
    place(out, 1.4 * thud(0.7, 48, rng, 1.4), 0.9)
    place(out, 0.6 * metal_ring(1.0, [(140, 1), (330, 0.7), (610, 0.4)], rng, 4), 0.9)
    # And the roar, swelling
    t = seconds(1.4)
    f0 = 85 * (1 + 0.1 * np.sin(2 * np.pi * 3 * t))
    roar = vowel(t, f0, ((500, 200, 1), (900, 250, 0.6)), 0.9, rng) + 0.6 * band(rng.normal(size=len(t)), 200, 2500)
    place(out, 0.7 * roar / np.max(np.abs(roar)) * np.minimum(1, t / 1.2) ** 2, 0.8)
    return corridor(out, 0.9, 0.05, 0.2, 21)


def slam():
    rng = np.random.default_rng(1430)
    out = np.zeros(int(1.2 * RATE))
    place(out, 1.2 * thud(0.6, 52, rng, 1.2), 0.0)
    place(out, 0.4 * metal_ring(0.6, [(160, 1), (390, 0.5)], rng, 8), 0.0)
    tt = seconds(0.05)
    place(out, 0.5 * band(rng.normal(size=len(tt)), 1500, 6000) * np.exp(-tt * 120), 0.13)  # the latch
    return corridor(out, 0.8, 0.05, 0.2, 22)


def rattle():
    rng = np.random.default_rng(1440)
    out = np.zeros(int(0.7 * RATE))
    for at in (0.0, 0.18, 0.33):
        place(out, 0.6 * metal_ring(0.15, [(1400, 1), (2300, 0.6)], rng, 25), at)
        place(out, 0.5 * thud(0.1, 140, rng, 1.5), at + 0.01)
        place(out, 0.3 * rattle_tail(0.12, rng, 120), at + 0.02)
    return corridor(out, 0.4, 0.03, 0.1, 23)


def swing():
    rng = np.random.default_rng(1450)
    out = np.zeros(int(0.8 * RATE))
    tt = seconds(0.25)
    whoosh = band(rng.normal(size=len(tt)), 200, 1500) * np.sin(np.pi * tt / 0.25) ** 2
    place(out, 0.4 * whoosh, 0.0)
    place(out, 1.1 * thud(0.35, 70, rng, 1.2), 0.24)
    place(out, 0.5 * metal_ring(0.5, [(210, 1), (520, 0.5), (900, 0.3)], rng, 9), 0.24)
    return corridor(out, 0.6, 0.04, 0.15, 24)


def topple():
    rng = np.random.default_rng(1460)
    out = np.zeros(int(1.4 * RATE))
    tt = seconds(0.35)  # a groan of steel as it goes over
    groan = np.sin(2 * np.pi * np.cumsum(180 - 60 * tt / 0.35) / RATE) * band(rng.normal(size=len(tt)), 100, 800) * 2
    place(out, 0.3 * groan * np.sin(np.pi * tt / 0.35), 0.0)
    place(out, 1.3 * thud(0.5, 60, rng, 1.4), 0.38)
    for k in range(5):
        place(out, rng.uniform(0.3, 0.6) * metal_ring(0.5, [(rng.uniform(250, 700), 1), (rng.uniform(900, 1800), 0.5)], rng, 10), 0.38 + rng.uniform(0, 0.2))
    for k in range(6):  # boxes tumbling
        place(out, rng.uniform(0.2, 0.5) * band(thud(0.15, rng.uniform(90, 140), rng, 0.4), 60, 900), 0.5 + rng.uniform(0, 0.6))
    return corridor(out, 0.7, 0.04, 0.18, 25)


def signhiss():
    rng = np.random.default_rng(1470)
    L = 3.0
    n = int(L * RATE)
    t = np.arange(n) / RATE
    saw = sum(np.sin(2 * np.pi * 120 * k * t) / k for k in range(1, 30))
    buzz = np.tanh(3 * saw) * (0.6 + 0.4 * (rng.random(n) < 0.5))
    buzz = band(buzz, 100, 6000)
    out = 0.35 * buzz
    for _ in range(26):  # crackles of arcing
        tt = seconds(rng.uniform(0.005, 0.03))
        wrap_place(out, rng.uniform(0.3, 1.0) * band(rng.normal(size=len(tt)), 2000, 9000) * np.exp(-tt * 200), rng.uniform(0, L))
    # A whine rising and falling back, so the loop has no seam
    f = 2600 + 1800 * np.sin(np.pi * t / L) ** 2
    out += 0.12 * np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.sin(np.pi * t / L) ** 2
    return out


def signburst():
    rng = np.random.default_rng(1480)
    out = np.zeros(int(1.6 * RATE))
    tt = seconds(0.02)
    place(out, 1.5 * rng.normal(size=len(tt)) * np.exp(-tt * 200), 0.0)  # pop
    place(out, 1.0 * thud(0.25, 70, rng, 1.0), 0.0)
    for _ in range(40):  # glass
        tt = seconds(rng.uniform(0.05, 0.25))
        f = rng.uniform(3000, 9000)
        place(out, rng.uniform(0.1, 0.35) * np.sin(2 * np.pi * f * tt) * np.exp(-tt * rng.uniform(20, 50)), rng.uniform(0.02, 0.6))
    t = seconds(1.3)  # whoosh of flame, crackling
    flame = band(rng.normal(size=len(t)), 80, 1800) * np.minimum(1, t / 0.25) * np.exp(-np.maximum(0, t - 0.6) * 2)
    flame += 0.5 * rattle_tail(1.3, rng, 30, 1500, 5000)
    place(out, 0.6 * flame, 0.25)
    return corridor(out, 0.6, 0.04, 0.15, 26)


def ventburst():
    rng = np.random.default_rng(1490)
    out = np.zeros(int(1.0 * RATE))
    place(out, 0.8 * metal_ring(0.6, [(520, 1), (1250, 0.7), (2100, 0.4)], rng, 10), 0.0)
    place(out, 0.4 * rattle_tail(0.25, rng, 80), 0.02)
    place(out, 1.2 * thud(0.4, 58, rng, 0.8), 0.32)
    tt = seconds(0.25)
    place(out, 0.25 * band(rng.normal(size=len(tt)), 600, 4000) * np.sin(np.pi * tt / 0.25), 0.45)  # claws scrabbling
    return corridor(out, 0.6, 0.04, 0.15, 27)


def heartbeat():
    rng = np.random.default_rng(1500)
    L = 2.0
    out = np.zeros(int(L * RATE))
    for k in range(4):
        at = k * 0.5
        lub = seconds(0.14)
        place(out, np.sin(2 * np.pi * 50 * lub) * np.exp(-lub * 30) * np.minimum(1, lub / 0.01), at)
        dub = seconds(0.12)
        place(out, 0.65 * np.sin(2 * np.pi * 62 * dub) * np.exp(-dub * 34) * np.minimum(1, dub / 0.01), at + 0.14)
    out += 0.02 * band(rng.normal(size=len(out)), 40, 200)
    return band(out, 30, 400)


def trip():
    rng = np.random.default_rng(1510)
    out = np.zeros(int(0.5 * RATE))
    tt = seconds(0.09)
    place(out, 0.5 * band(rng.normal(size=len(tt)), 900, 4500) * np.sin(np.pi * tt / 0.09), 0.0)  # scuff
    place(out, 1.0 * thud(0.25, 85, rng, 0.7), 0.12)
    place(out, 0.6 * thud(0.2, 110, rng, 0.5), 0.27)
    return out


def sounds():
    loud, far = alarm_signals()
    write_sound("ambient/run", "alarm", loud, 0.55, fade=False)
    write_sound("ambient/run", "alarm-far", far, 0.45, fade=False)
    write_sound("ambient/run", "horde", horde(), 0.6, fade=False)
    write_sound("ambient/run", "safezone", safezone(far), 0.16, fade=False)
    for k in (1, 2, 3):
        write_sound("effect/run", f"bang{k}", bang(k), 0.7)
    write_sound("effect/run", "doorbreak", doorbreak(), 0.75)
    write_sound("effect/run", "slam", slam(), 0.75)
    write_sound("effect/run", "rattle", rattle(), 0.55)
    write_sound("effect/run", "swing", swing(), 0.65)
    write_sound("effect/run", "topple", topple(), 0.7)
    write_sound("effect/run", "signhiss", signhiss(), 0.4, fade=False)
    write_sound("effect/run", "signburst", signburst(), 0.7)
    write_sound("effect/run", "ventburst", ventburst(), 0.65)
    write_sound("effect/run", "heartbeat", heartbeat(), 0.6, fade=False)
    write_sound("effect/run", "trip", trip(), 0.55)


# ======================= Words =======================

def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def notice(kind):
    """A notice printed on white card, drawn at 4 px a voxel: PLEASE WASH YOUR HANDS (two hands under a drop), or
    VISITING HOURS under a red cross."""
    k, W, H = 4, 32, 40
    big = Image.new("RGBA", (W * k, H * k), (246, 246, 240, 255))
    d = ImageDraw.Draw(big)
    ink, white = (40, 40, 44, 255), (255, 255, 255, 255)
    if kind == "handwash":
        blue = (30, 90, 170, 255)
        d.rectangle([0, 0, W * k, 9 * k], fill=blue)
        d.text((W * k / 2, 4.6 * k), "PLEASE", fill=white, font=_font(6 * k), anchor="mm")
        d.polygon([(16 * k, 11 * k), (13.6 * k, 15.5 * k), (18.4 * k, 15.5 * k)], fill=blue)
        d.ellipse([13.6 * k, 13.6 * k, 18.4 * k, 18.2 * k], fill=blue)
        for x0 in (7, 17):  # two cupped hands
            d.rounded_rectangle([x0 * k, 19.5 * k, (x0 + 8) * k, 25.5 * k], radius=3 * k, fill=(232, 196, 170, 255), outline=ink, width=k // 2)
        d.text((W * k / 2, 30.5 * k), "WASH YOUR", fill=ink, font=_font(int(4.4 * k)), anchor="mm")
        d.text((W * k / 2, 36 * k), "HANDS", fill=blue, font=_font(6 * k), anchor="mm")
    else:
        red = (200, 30, 36, 255)
        d.rectangle([13.5 * k, 2 * k, 18.5 * k, 13 * k], fill=red)
        d.rectangle([10.5 * k, 5 * k, 21.5 * k, 10 * k], fill=red)
        d.text((W * k / 2, 17 * k), "VISITING", fill=ink, font=_font(5 * k), anchor="mm")
        d.text((W * k / 2, 22 * k), "HOURS", fill=ink, font=_font(5 * k), anchor="mm")
        for i, line in enumerate(("MON-FRI 2-8", "SAT-SUN 10-8")):
            d.text((W * k / 2, (27.5 + i * 4) * k), line, fill=(90, 90, 96, 255), font=_font(3 * k), anchor="mm")
        for i in range(2):  # the small print
            d.line([5 * k, (35 + i * 2) * k, 27 * k, (35 + i * 2) * k], fill=(160, 160, 164, 255), width=k // 2)
    return big.resize((W, H), Image.LANCZOS)


def startroom():
    """The start room's own fittings: its red ceiling lamp, two notices and a hand-sanitiser dispenser on its walls."""
    # The lamp: a ceiling tile with a red prismatic panel, all the light the room has ("a room illuminated by red light")
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            c = mix(rgb(0xFF8474), rgb(0xC42C24), ((x - 15.5) ** 2 + (y - 15.5) ** 2) ** 0.5 / 22)
            px[x, y] = shade(c, 0.93) if (x + y) % 3 == 0 else c
    save(img, "redlight")
    els = [bx("Body", (0, 0, 0), (16, 16, 16), "ceiltile", faces=("north", "east", "south", "west", "up", "down")),
           bx("Rim", (0.5, -0.8, 0.5), (15.5, 0, 15.5), "trofferframe", faces=("north", "east", "south", "west")),
           bx("Panel", (1, -0.8, 1), (15, -0.79, 15), "redlight", glow=140, faces=("down",))]
    block("run-redlight", {
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Glass", "drawtype": "json", "shape": {"base": shape("run-redlight", els)},
        "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "lightHsv": [0, 7, 14], "lightAbsorption": 0, "resistance": 99999, "drops": [], "sounds": GLASS,
    }, "Level !: the start room's ceiling lamp, a red light panel (brighter than the Red Rooms' lamp it replaced, so the "
       "room's bed, cabinet, curtain and doors read; still only red)")
    name("run-redlight", "Red Ceiling Light")

    # On the walls, at eye height (rel 2): notices on card, and the dispenser by the way out
    for kind in ("handwash", "visiting"):
        save(notice(kind), "notice-" + kind)
    save(noise(0xF2F2EE, 2, "dispenser"), "dispenser")
    img = noise(0xF2F2EE, 2, "dispenserfront", size=16)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 12, 5], fill=rgb(0x8C9AA6))  # the window onto the gel
    d.rectangle([3, 4, 12, 5], fill=rgb(0xC8E0EC))
    d.polygon([(8, 8), (6, 11), (10, 11)], fill=rgb(0x2A6AB8))
    d.ellipse([6, 9, 10, 13], fill=rgb(0x2A6AB8))
    save(img, "dispenserfront")
    save(noise(0x9A9EA4, 2, "dispenserlever"), "dispenserlever")
    wall = bx("Wall", (0, 0, 0), (16, 16, 16), "wall")
    card = lambda key: [bx("Card", (3, 2, -0.3), (13, 14.5, -0.05), key, faces=("north",), full=True),
                        bx("CardEdge", (3, 2, -0.3), (13, 14.5, -0.05), "dispenser", faces=("east", "west", "up", "down")),
                        # (B14) a pin in each top corner
                        bx("Pin1", (3.15, 13.6, -0.6), (3.85, 14.3, -0.3), "chrome"),
                        bx("Pin2", (12.15, 13.6, -0.6), (12.85, 14.3, -0.3), "chrome")]
    kinds = {
        "handwash": [wall] + card("notice-handwash"),
        "visiting": [wall] + card("notice-visiting") + [
            bx("HolderT", (2.6, 14.5, -0.6), (13.4, 15, 0), "chrome"), bx("HolderB", (2.6, 1.5, -0.6), (13.4, 2, 0), "chrome")],
        "sanitiser": [wall,
                      bx("Housing", (5, 1.5, -3.2), (11, 13, 0), "dispenser", faces=("north", "east", "west", "up", "down")),
                      bx("Front", (5.1, 1.6, -3.3), (10.9, 12.9, -3.2), "dispenserfront", faces=("north",), full=True),
                      # (B14) the window onto the gel, set into the front, and the push paddle's hinge
                      bx("Gel", (5.9, 9.4, -3.36), (10.1, 11.6, -3.3), "dispensergel", faces=("north",), uv=[0, 0, 16, 8]),
                      bx("GelRimT", (5.7, 11.6, -3.5), (10.3, 11.9, -3.3), "dispenser", faces=("north", "up", "down")),
                      bx("GelRimB", (5.7, 9.1, -3.5), (10.3, 9.4, -3.3), "dispenser", faces=("north", "up", "down")),
                      bx("Hinge", (5.4, 3.4, -3.6), (10.6, 4.0, -3.2), "dispenserlever"),
                      bx("Lever", (5.4, 1, -3.9), (10.6, 3.6, -2.8), "dispenserlever", rot=(-12, 0, 0), origin=(8, 3.6, -2.8)),
                      bx("Nozzle", (7.5, 0.3, -2.4), (8.5, 1.5, -1.6), "dispenserlever"),
                      bx("Drip", (7.6, 0, -2.2), (8.4, 0.3, -1.8), "chrome")],
    }
    by_type = {}
    for kind, els in kinds.items():
        path = shape(f"run-walldecor-{kind}", els)
        for sd in SIDES:
            by_type[f"*-{kind}-{sd}"] = {"base": path, "rotateY": ROTATE[sd]}
    block("run-walldecor", {
        "variantgroups": [{"code": "kind", "states": list(kinds)}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "lightAbsorption": 99, "resistance": 99999, "drops": [], "sounds": STONE,
    }, "Level !: a start-room wall block (rel 2) with, on face <side>, a notice (handwash: PLEASE WASH YOUR HANDS; visiting: "
       "VISITING HOURS) or a hand-sanitiser dispenser (sanitiser); fixed like the walls")
    name("run-walldecor-handwash-*", "Hand Hygiene Notice")
    name("run-walldecor-visiting-*", "Visiting Hours Notice")
    name("run-walldecor-sanitiser-*", "Hand Sanitiser Dispenser")


def lang():
    LANG.update({
        "level-14": "Level !: Run For Your Life!",
        "levelhint-14": "Out through the door under the lit EXIT sign, and run. Don't stop. A door with a turn beside it is not the way out; the real one has light under it.",
        "levelname-14": "Level !",
        "level-1401": "The Safe Zone",
        "levelhint-1401": "Please take a break before you continue running.",
        "run-arrive": "The door slams behind you: on its inside, a huge red exclamation mark. Something is beating on the chained door. The way out is the door under the lit EXIT sign. Run!",
        "run-stuck": "The door is stuck! Pull again!",
        "run-stuck2": "It gives a little. Once more!",
        "run-locked": "Locked.",
        "run-marked": "It won't budge. The way out is the door under the lit EXIT sign!",
        "run-chained": "Something on the other side wants in. Not this way: the door under the lit EXIT sign!",
        "run-fake": "An empty room, dark behind the door. This isn't the way out.",
        "run-trip": "You trip! Jump the junk on the floor at a sprint, or walk over it.",
        "run-escaped": "No turn either side. This was the real exit. The Backrooms will never send you there again.",
        "run-ranout": "You have run this hall before. The door lets you out somewhere else.",
        "run-rumble": "The walls shudder. You can't stay here much longer.",
        "run-fell": "The cracked floor gives way. You fall a long way, into rock and rubble.",
        "run-caught": "{0} was caught by the horde",
        "note-run": "Don't take the door if the hall turns beside it, or if its sign is dark. The real one is at a dead end, with light under it. Don't stop. They're still there.",
        "item-run-energybar": "Energy Bar",
        "itemdesc-run-energybar": "Dense, sweet, and gone in three bites. Keeps you running a little longer.",
    })


def clean():
    """Removes what an earlier run of this script wrote (only this level's own folders), so renamed blocks leave nothing behind."""
    import shutil
    for rel in (("shapes", "block", TAG), ("blocktypes", TAG), ("textures", "block", TAG)):
        shutil.rmtree(os.path.join(ASSETS, *rel), ignore_errors=True)


def prune_lang():
    """Drops block names of ours that this script no longer makes (block-run-*), keeping the file's layout."""
    import re
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        lines = f.read().split(NL)
    keep = []
    for line in lines:
        m = re.match(r'^\t"(block-run-[^"]*|level-141|levelhint-141)":', line)
        if m and m.group(1) not in LANG:
            continue
        keep.append(line)
    text = NL.join(keep)
    text = re.sub(r",(\s*)\}\s*$", r"\1}" + NL, text)  # no trailing comma before the closing brace
    json.loads(text)
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)


# ======================= B14 (graphics pass): models and versions =======================

WALL_WEIGHTS = {"plain": (0, 1, 2, 3), "base": (0, 0, 0, 1, 1, 1, 2, 3)}  # version indices; base: a scuff or a rub 1 in 8


def b14_versions(code, states, json_keys, weights):
    """Gives a wall blocktype's plain and base kinds their versions (`alternates`), the same for its JSON kinds' named
    key (`json_keys`: {type pattern: key}), and picks them by height as well (randomizeAxes xyz, B13's lesson)."""
    path = os.path.join(ASSETS, "blocktypes", TAG, code + ".json")
    with open(path, encoding="utf-8") as f:
        head, _, body = f.read().partition("\n")
    data = json.loads(body)

    def entry(key, which):
        names = [tex(key if k == 0 else f"{key}-{k + 1}") for k in weights[which]]
        return {"base": names[0], "alternates": [{"base": n} for n in names[1:]]}
    for st, (key, how) in states.items():
        t = data["texturesByType"][f"*-{st}"]
        if how == "all":
            t["all"] = entry(key, "plain")
        else:
            for f in ("north", "east", "south", "west"):
                t[f] = entry(key, "base")
    for pat, key in json_keys.items():
        data["texturesByType"][pat] = {key: entry(key, "base")}
    data["randomizeAxes"] = "xyz"
    write_json(path, data, head[3:])


def b14_floor_versions():
    """The vinyl's three versions, each turned at random; the border's two (not turned: the band has a side)."""
    path = os.path.join(ASSETS, "blocktypes", TAG, "run-floor.json")
    with open(path, encoding="utf-8") as f:
        head, _, body = f.read().partition("\n")
    data = json.loads(body)
    vin = [(tex(k), r) for k in ("vinyl", "vinyl-2", "vinyl-3") for r in (0, 90, 180, 270)]
    data["texturesByType"]["*-vinyl"]["up"] = {"base": vin[0][0], "alternates": [
        dict({"base": b}, **({"rotation": r} if r else {})) for b, r in vin[1:]]}
    for s_ in SIDES:
        data["texturesByType"][f"*-border-{s_}"]["up"] = {"base": tex(f"border-{s_}"), "alternates": [{"base": tex(f"border-{s_}-2")}]}
    for k in ("scuffed", "cracked"):  # (round 2) two versions, each turned
        alts = [(tex(n), r) for n in (k, f"{k}-2") for r in (0, 90, 180, 270)]
        data["texturesByType"][f"*-{k}"]["up"] = {"base": alts[0][0], "alternates": [
            dict({"base": b}, **({"rotation": r} if r else {})) for b, r in alts[1:]]}
    write_json(path, data, head[3:])


def sign_lip(z0, z1, facing, y0=7):
    """A lip round an EXIT sign's face, standing a little proud of it (the housing's paint, its top edge lit)."""
    out = []
    for nm, frm, to in (("T", (1, 13.5, z0), (15, 14, z1)), ("B", (1, y0, z0), (15, y0 + 0.5, z1)),
                        ("L", (1, y0 + 0.5, z0), (1.5, 13.5, z1)), ("R", (14.5, y0 + 0.5, z0), (15, 13.5, z1))):
        faces = tuple(f for f in ("north", "south", "east", "west", "up", "down")
                      if f != ("south" if facing == "north" else "north"))
        out.append(bx(f"Lip{nm}{facing[0].upper()}", frm, to, "exitlip", faces=faces))
    return out


def wbx(name_, frm, to, tex_, faces):
    """A box whose faces take world-aligned UVs (preview_shapes.auto_uv), so the pieces of a leaf cut round an opening
    show the leaf's texture continuing across them."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    uv = {"north": (16 - x1, 16 - y1, 16 - x0, 16 - y0), "south": (x0, 16 - y1, x1, 16 - y0),
          "west": (z0, 16 - y1, z1, 16 - y0), "east": (16 - z1, 16 - y1, 16 - z0, 16 - y0),
          "up": (x0, z0, x1, z1), "down": (x0, 16 - z1, x1, 16 - z0)}
    el = bx(name_, frm, to, tex_, faces=faces)
    for f in el["faces"]:
        el["faces"][f]["uv"] = [round(v, 4) for v in uv[f]]
    return el


SIDE_WINDOW = (5.5, 6.5, 10.5, 13.5)   # the steel door's vision panel, upper half (x0, y0, x1, y1): B0's painted one
HALL_WINDOW = (10, 3, 12.75, 14.5)     # the hall door's, high on the lock side


def side_leaf(front, back, part, z0=1, z1=3, window="side", bead="runbead"):
    """A door leaf (x 0-16, z z0-z1, its front to the north). In the upper half the vision panel is an opening: the
    leaf in four pieces round it, a wired-glass pane in the middle of its thickness, and a bead standing proud round it
    on the front. Every piece shows the leaf's texture where it lies (wbx)."""
    if part != "upper" or window is None:
        return [bx("Leaf", (0, 0, z0), (16, 16, z1), front, faces=("north",), full=True),
                bx("LeafBack", (0, 0, z0), (16, 16, z1), back, faces=("south", "east", "west", "up", "down"))]
    wx0, wy0, wx1, wy1 = SIDE_WINDOW if window == "side" else window
    pieces = [("L", (0, 0, z0), (wx0, 16, z1)), ("R", (wx1, 0, z0), (16, 16, z1)),
              ("B", (wx0, 0, z0), (wx1, wy0, z1)), ("T", (wx0, wy1, z0), (wx1, 16, z1))]
    els = []
    for nm, frm, to in pieces:
        els.append(wbx(f"Leaf{nm}", frm, to, front, ("north",)))
        els.append(wbx(f"LeafBack{nm}", frm, to, back, ("south", "east", "west", "up", "down")))
    zm = (z0 + z1) / 2
    els.append(bx("Glass", (wx0, wy0, zm - 0.1), (wx1, wy1, zm + 0.1), "wiredglass", faces=("north", "south"), full=True))
    b, d = 0.5, 0.4
    els += [bx("BeadT", (wx0 - b, wy1, z0 - d), (wx1 + b, wy1 + b, z0), bead, faces=("north", "east", "west", "up", "down")),
            bx("BeadB", (wx0 - b, wy0 - b, z0 - d), (wx1 + b, wy0, z0), bead, faces=("north", "east", "west", "up", "down")),
            bx("BeadL", (wx0 - b, wy0, z0 - d), (wx0, wy1, z0), bead, faces=("north", "east", "west")),
            bx("BeadR", (wx1, wy0, z0 - d), (wx1 + b, wy1, z0), bead, faces=("north", "east", "west"))]
    return els


# ======================= B14 (graphics pass): textures =======================
#
# Every B14 painter runs after textures() / gauntlet() / startroom() under the same keys (plus a few new ones), so a
# family reverts by dropping its call from b14_textures(). Means are matched to main's PNGs (OLD_MEAN), so the hall
# keeps its tones under the red light. Versions of a large surface share one low-frequency ground and differ only in
# fine grain and rare features (B5's lesson); walls pick theirs by height as well (randomizeAxes xyz, B13's).

import matlib as M  # noqa: E402
from gen_city import CITY_F3, CITY_F5  # noqa: E402  (the B12 pixel faces)

OLD_MEAN = {  # main's mean colours (measured on the PNGs before B14)
    "wall": (215, 220, 210), "wallbase": (202, 207, 198), "safewall": (195, 213, 231), "safewallbase": (186, 204, 223),
    "vinyl": (208, 208, 200), "border": (168, 171, 168), "scuffed": (188, 185, 177), "cracked": (194, 194, 186),
    "safefloor": (178, 191, 206), "ceiltile": (227, 227, 221), "railwood": (138, 90, 50), "railtop": (168, 116, 66),
    "steelframe": (92, 97, 100), "exithousing": (26, 26, 26), "sidedoor": (140, 145, 148), "sidedoor-back": (134, 139, 142),
    "exitdoor": (158, 38, 34), "exitdoor-back": (142, 24, 20), "halldoor": (132, 101, 69), "halldoor-back": (132, 102, 74),
    "hallframe": (74, 78, 82), "chaindoor": (132, 134, 135), "cartside": (184, 40, 32), "cabsteel": (154, 166, 160),
    "mattress": (91, 110, 129), "sheet": (226, 226, 220), "gurneyframe": (110, 114, 118), "chrome": (183, 187, 191),
    "cabinet": (236, 236, 230), "curtain": (140, 174, 151), "bedside": (216, 205, 180), "shelfblue": (45, 90, 150),
    "pillow": (237, 233, 220), "dispenser": (242, 242, 238), "beamsteel": (58, 62, 66),
}

# Keys B14 adds, known before the shapes that use them are written (their painters run last)
MINE.update({"cablabel", "scuffed-2", "cracked-2", "railunder", "exitlip", "runbead", "cartdrawer", "cartlabel", "defibscreen", "cabmirror", "dispensergel"}
            | {f"{k}-{n}" for k in ("wall", "safewall", "wallbase", "safewallbase") for n in (2, 3, 4)}
            | {"vinyl-2", "vinyl-3", "ceiltile-2", "ceiltile-3"} | {f"border-{s_}-2" for s_ in SIDES})

# A pixel face for the notices: B12's 3 x 5 capitals and a few marks of our own
RUN_F3 = dict(CITY_F3, **{"!": "1 1 1 0 1", "/": "001 001 010 100 100", ":": "0 1 0 1 0", "+": "000 010 111 010 000"})
RUN_F5 = dict(CITY_F5)


def pwidth(s, font=RUN_F3, gap=1):
    return sum(len(font[ch].split()[0]) + gap for ch in s.upper()) - gap


def ptext(img, s, x, y, col, font=RUN_F3, gap=1):
    """`s` in a pixel face at (x, y), every lit pixel `col`."""
    p = img.load()
    for ch in s.upper():
        rows = font[ch].split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1" and 0 <= x + c < img.width and 0 <= y + r < img.height:
                    p[x + c, y + r] = M.rgba(col)
        x += len(rows[0]) + gap
    return x


def ptext_c(img, s, y, col, font=RUN_F3, gap=1, x0=0, x1=None):
    x1 = img.width if x1 is None else x1
    return ptext(img, s, x0 + (x1 - x0 - pwidth(s, font, gap) + 1) // 2, y, col, font, gap)


def matched(img, key, target=None):
    return T.match_rgb(img, target or OLD_MEAN[key], key="b14run" + key)


def edges(img, sides="lrtb", lit=0.14, dark=0.18, width=1):
    """A raised edge on the named sides of a texture (a door leaf's outer edges): lit at the top and left, shaded at the
    bottom and right. Unlike matlib.bevel it leaves the other sides alone (a door's two halves meet without a line)."""
    w, h = img.size
    for k in range(width):
        f = 1 - k / width
        if "t" in sides:
            for x in range(w):
                M.touch(img, x, k, lit * f)
        if "b" in sides:
            for x in range(w):
                M.touch(img, x, h - 1 - k, -dark * f)
        if "l" in sides:
            for y in range(h):
                M.touch(img, k, y, lit * 0.7 * f)
        if "r" in sides:
            for y in range(h):
                M.touch(img, w - 1 - k, y, -dark * 0.85 * f)
    return img


def fine(img, seed, amp=2.0, roller=2.5):
    """A version's own fine grain and roller stipple over a shared ground."""
    rng = random.Random(seed)
    st = M.fbm(img.size, M.sub(seed, "roll"), (2, 1), 0.7)
    p = img.load()
    for y in range(img.height):
        for x in range(img.width):
            p[x, y] = M.rgba(M.lift(p[x, y], rng.uniform(-amp, amp) + st[y][x] * roller), p[x, y][3])
    return img


def smudge(img, seed, at, r=(3, 6), n=3, strength=0.05, color=(96, 92, 84), stretch=2.2):
    """A few soft scuffs: low, wide, faint smears, wrapped; for one version of a wall's foot in eight."""
    rng = random.Random(seed)
    w, h = img.size
    p = img.load()
    for _ in range(n):
        cx, cy = at[0] + rng.uniform(-6, 6), at[1] + rng.uniform(-2, 2)
        rx, ry = rng.uniform(*r) * stretch, rng.uniform(*r) * 0.45
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if d < 1:
                    t = strength * (1 - d) ** 1.5 * rng.uniform(0.7, 1.1)
                    M.put(p, w, h, x, y, M.mix(M.get(p, w, h, x, y), color, t))
    return img


def wall_versions(base, key):
    """Hospital wall paint over plaster: one calm ground, a fine roller stipple per version. Four versions, all plain."""
    ground = M.noise_hv(rgb(base)[:3], 0, seed_of("b14" + key + "ground"), mottle=2.0, cells=(16, 8), hue=1.0)
    out = []
    for k in range(4):
        img = fine(ground.copy(), seed_of(f"b14{key}fine{k}"), 1.6, 2.2)
        out.append(matched(img, key))
    return out


COVE = (0x5E, 0x6A, 0x62)


def cove_b14(img, colour, k, scuffs):
    """The vinyl cove base, 3 px: a lit roll on top, its body, a dark toe on the floor, and the faint shadow its lip
    throws on the wall; a dirty band above it (grime gathers at the foot of a wall); the odd scuff in a version."""
    w, h = img.size
    p = img.load()
    dirt = M.fbm((w, h), seed_of("b14covedirt"), (16, 8), 0.5)  # one field for every version: no block edges
    for y in range(h):
        t = max(0.0, (y - 12) / (h - 12)) ** 1.6
        for x in range(w):
            p[x, y] = M.rgba(M.mix(p[x, y], (150, 144, 128), t * (0.10 + 0.04 * dirt[y][x])))
    rng = random.Random(seed_of(f"b14covegrain{k}"))
    for x in range(w):
        c = colour
        p[x, h - 3] = M.rgba(M.lift(c, 16 + rng.uniform(-2, 2)))
        p[x, h - 2] = M.rgba(M.lift(c, rng.uniform(-3, 3)))
        p[x, h - 1] = M.rgba(M.lift(c, -14 + rng.uniform(-2, 2)))
        M.touch(img, x, h - 4, -0.06)
    if scuffs == "scuff":
        smudge(img, seed_of(f"b14scuff{k}"), (rng.uniform(8, 24), 24.5), n=3, strength=0.07)
    elif scuffs == "rub":  # a trolley's rubber bumper along the wall: one grey streak, fading at both ends
        x0, L = rng.randrange(4, 10), rng.randrange(12, 20)
        for i in range(L):
            t = math.sin(math.pi * (i + 0.5) / L) ** 0.6
            M.touch(img, x0 + i, 23, -0.06 * t)
            M.touch(img, x0 + i, 24, -0.08 * t)
            M.touch(img, x0 + i, 25, -0.03 * t)
    return img


def wallbase_versions(base, key, cove_colour, scuffs=True):
    walls = wall_versions(base, key.replace("base", ""))
    out = []
    for k, (img, feat) in enumerate(zip(walls, ("", "", "scuff", "scuff"))):
        img = cove_b14(img.copy(), cove_colour, k, feat if scuffs else "")
        out.append(matched(img, key))
    return out


def vinyl_ground(base, key):
    return M.noise_hv(base, 0, seed_of("b14" + key + "ground"), mottle=1.6, cells=(16, 8), hue=1.2)


CHIPS = [((110, 110, 106), 0.30), ((132, 130, 124), 0.18), ((160, 152, 138), 0.14), ((122, 128, 138), 0.10),
         ((242, 240, 232), 0.28)]


def vinyl_b14(base, key, k, chips=CHIPS, density=1.0):
    """Speckled hospital sheet vinyl: a calm ground (shared by every version), chips of two sizes in grey, warm and
    blue-grey and white, a few in small clusters; a faint satin grain. No seam: the sheet is welded."""
    img = vinyl_ground(base, key)
    w, h = img.size
    rng = random.Random(seed_of(f"b14{key}chips{k}"))
    p = img.load()
    for y in range(h):
        for x in range(w):
            p[x, y] = M.rgba(M.lift(p[x, y], rng.uniform(-2.2, 2.2)))
    cols, weights = zip(*chips)

    def chip(x, y, c, cells):
        c = M.lift(c, rng.uniform(-6, 6))
        for (cx, cy) in cells:
            M.put(p, w, h, x + cx, y + cy, M.rgba(c))
    for _ in range(int(w * h * 0.05 * density)):  # flecks
        chip(rng.randrange(w), rng.randrange(h), rng.choices(cols, weights)[0], [(0, 0)])
    for _ in range(int(w * h * 0.006 * density)):  # larger chips, 2-3 px
        cells = rng.choice(([(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 0), (0, 1)], [(0, 0), (1, 0), (1, 1)]))
        chip(rng.randrange(w), rng.randrange(h), rng.choices(cols[:4], weights[:4])[0], cells)
    for _ in range(int(3 * density)):  # a loose cluster of flecks
        x0, y0 = rng.randrange(w), rng.randrange(h)
        c = rng.choices(cols, weights)[0]
        for _ in range(rng.randint(3, 5)):
            chip(x0 + rng.randint(-2, 2), y0 + rng.randint(-2, 2), c, [(0, 0)])
    return img


def b14_walls():
    for key, base, cove_c, scuffs in (("wall", WALL, None, None), ("safewall", SAFEWALL, None, None)):
        for k, img in enumerate(wall_versions(base, key)):
            save(img, key if k == 0 else f"{key}-{k + 1}")
    for key, base, cove_c, scuffs in (("wallbase", WALL, COVE, True), ("safewallbase", SAFEWALL, (0x5A, 0x6E, 0x86), False)):
        for k, img in enumerate(wallbase_versions(base, key, cove_c, scuffs)):
            save(img, key if k == 0 else f"{key}-{k + 1}")


def b14_floor():
    vb = (212, 212, 204)
    for k in range(3):
        save(matched(vinyl_b14(vb, "vinyl", k), "vinyl"), "vinyl" if k == 0 else f"vinyl-{k + 1}")
    save(matched(vinyl_b14((182, 194, 210), "safefloor", 0), "safefloor"), "safefloor")
    # The dark border band along the hall's edges: the same sheet, a dark inlay 8 px wide welded on with a groove
    band_chips = [((92, 104, 116), 0.4), ((44, 52, 60), 0.35), ((150, 156, 160), 0.25)]
    for side, box in (("north", (0, 0, S, 8)), ("east", (S - 8, 0, S, S)), ("south", (0, S - 8, S, S)), ("west", (0, 0, 8, S))):
        for k in range(2):
            img = vinyl_b14(vb, "vinyl", 10 + k)
            band = vinyl_b14((62, 74, 85), "border", k + (4 if side in ("east", "west") else 0), band_chips, 0.8)
            mask = Image.new("L", (S, S), 0)
            ImageDraw.Draw(mask).rectangle([box[0], box[1], box[2] - 1, box[3] - 1], fill=255)
            img.paste(band, (0, 0), mask)
            # The weld: a dark groove on the field side of the band and a lit hair beside it
            line, hair = {"north": ((0, 8, S, 9), (0, 9, S, 10)), "south": ((0, S - 9, S, S - 8), (0, S - 10, S, S - 9)),
                          "east": ((S - 9, 0, S - 8, S), (S - 10, 0, S - 9, S)), "west": ((8, 0, 9, S), (9, 0, 10, S))}[side]
            for (x0, y0, x1, y1), f in ((line, -0.32), (hair, 0.05)):
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        M.touch(img, x, y, f)
            save(matched(img, "border"), f"border-{side}" + ("" if k == 0 else "-2"))
    # (round 2) two versions each of the scuffed and cracked sheet, so a patch of them is not the same marks in a grid
    for v, (sseed, cseed, cracks) in enumerate((("scuffed", "cracked", ((0, 14, 0.1, S, 2), (10, 15, -0.7, 12, 1), (20, 15, 0.8, 12, 1), (16, 14, -0.2, 8, 1))),
                                                ("scuffed2", "cracked2", ((0, 15, -0.05, S, 2), (6, 15, 0.7, 10, 1), (24, 14, -0.8, 9, 1))))):
        b14_scuffed_cracked(vb, v, sseed, cseed, cracks)


def b14_scuffed_cracked(vb, v, sseed, cseed, cracks):
    """Scuffed: B0's marks (heel marks, two drag smears, three claw scratches); cracked: a dark crack with chipped edges."""
    # Scuffed: B0's marks (the same places) on the new sheet: heel marks, two drag smears, three claw scratches
    img = vinyl_b14(vb, "vinyl", 20 + 2 * v)
    rng = random.Random(seed_of(sseed))
    px = img.load()
    for _ in range(9):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(2, 5)):
            xx, yy = (x + k) % S, (y + (k * k) // 6) % S
            px[xx, yy] = M.rgba(M.mix(px[xx, yy], (34, 32, 30), 0.85))
    for x0 in ((7, 20) if v == 0 else (12, 27)):
        for y in range(S):
            for dx in range(-2, 3):
                x = (x0 + dx + y // 8) % S
                if rng.random() < 0.75 - abs(dx) * 0.2:
                    px[x, y] = M.rgba(M.mix(px[x, y], (74, 42, 32), 0.45 - abs(dx) * 0.08))
    cx0, cy0, cl = (4, 6, 18) if v == 0 else (11, 13, 14)
    for k in range(3):
        for t in range(cl):
            x, y = cx0 + k * 3 + t, cy0 + t
            if 0 <= x < S and 0 <= y < S:
                px[x, y] = M.rgba(M.lift(px[x, y], 28))
                if x + 1 < S:
                    px[x + 1, y] = M.rgba(M.lift(px[x + 1, y], -60))
    save(matched(img, "scuffed"), "scuffed" if v == 0 else "scuffed-2")
    # Cracked: B0's crack (the same path) on the new sheet, its edges chipped and lit on the lower lip
    img = vinyl_b14(vb, "vinyl", 21 + 2 * v)
    rng = random.Random(seed_of(cseed))
    px = img.load()

    def crack(x, y, dx, n, width):
        for _ in range(n):
            for wd in range(width):
                xx, yy = int(x) % S, (int(y) + wd) % S
                px[xx, yy] = (36, 34, 32, 255)
                for cx, cy in ((xx + 1, yy - 1), (xx - 1, yy + 1)):
                    if rng.random() < 0.3:
                        px[cx % S, cy % S] = M.rgba(M.lift(px[cx % S, cy % S], -40))
            M.touch(img, int(x) % S, (int(y) + width) % S, 0.12)
            x += 1
            y += dx + rng.uniform(-0.9, 0.9)
    for c in cracks:
        crack(*c)
    save(matched(img, "cracked"), "cracked" if v == 0 else "cracked-2")


def b14_ceiling():
    """2 x 2 lay-in tiles to a block in their T-bar (matlib.ceiling_tile at 16 px: fissured board, a soft recess where it
    steps up into the grid, the rail shared between neighbours); three versions, a faint water stain in one."""
    for k in range(3):
        img = Image.new("RGBA", (S, S))
        for i, (ox, oy) in enumerate(((0, 0), (16, 0), (0, 16), (16, 16))):
            stain = (168, 150, 112) if (k == 2 and i == 1) else None
            t = M.ceiling_tile(seed_of(f"b14ceil{k}{i}"), 16, base=(232, 232, 226), rail=(208, 208, 202), fissures=0.55,
                               recess=1, stain_color=stain)
            img.paste(t, (ox, oy))
        save(matched(img, "ceiltile"), "ceiltile" if k == 0 else f"ceiltile-{k + 1}")
    save(matched(M.painted_metal(seed_of("b14tbar"), base=(208, 208, 202), panel=False, chips=0), "ceiltile", (207, 207, 200)), "tbar")


def b14_rail():
    """The crash rail: oak along its length. The front of the bar maps the texture's top rows, so those carry the
    round: lit at the top, falling into shade at the bottom; its underside has a key of its own (railunder)."""
    wood = M.wood_planks(seed_of("b14rail"), base=(146, 98, 56), planks=1, direction="h", grain=4, knots=0, joints=0,
                         flecks=0.3, per_plank=0)
    front = wood.copy()
    for y, d in enumerate((14, 7, 0, -9)):
        for x in range(S):
            M.touch(front, x, y, d / 100)
    for y in range(4, S):
        for x in range(S):
            M.touch(front, x, y, -0.04)
    save(matched(front, "railwood"), "railwood")
    top = M.wood_planks(seed_of("b14railtop"), base=(176, 124, 72), planks=1, direction="h", grain=3, knots=0, joints=0,
                        per_plank=0)
    for x in range(S):
        M.touch(top, x, 0, 0.10)
        M.touch(top, x, 2, -0.05)
    save(matched(top, "railtop"), "railtop")
    under = wood.copy()
    for y in range(S):
        for x in range(S):
            M.touch(under, x, y, -0.22)
    save(under, "railunder")
    save(matched(M.painted_metal(seed_of("b14steelframe"), base=(96, 101, 104), panel=False, chips=3, under=(132, 134, 134)),
                 "steelframe"), "steelframe")


def b14_signs():
    img = M.painted_metal(seed_of("b14exithousing"), base=(34, 33, 34), grain=2, mottle=3, panel=False, chips=0)
    save(matched(img, "exithousing", (32, 31, 32)), "exithousing")
    lip = M.painted_metal(seed_of("b14exitlip"), base=(40, 39, 40), grain=2, mottle=2, panel=False, chips=0)
    for x in range(S):
        M.touch(lip, x, 0, 0.35)
    save(lip, "exitlip")


def door_paint(base, key, part, chips=3, under=(112, 114, 114)):
    """A steel door leaf's paint: an even coat, orange-peel, a few worn spots; the leaf's outer edges raised (lower:
    the sides and bottom, upper: the sides and top), so the two halves meet without a line."""
    img = M.painted_metal(seed_of("b14" + key + part), base=base, grain=2, mottle=3, panel=False, chips=chips, under=under)
    M.grime(img, 0.05, seed_of("b14g" + key + part), cells=(8, 4), cover=0.4,
            bias="bottom" if part == "lower" else None)
    return edges(img, "lrb" if part == "lower" else "lrt", 0.12, 0.2)


def b14_doors():
    # The steel side doors: the window is now an opening with a pane and a bead (side_doors), the kick plate a plate
    for part in ("lower", "upper"):
        img = door_paint((144, 149, 152), "sidedoor", part)
        save(matched(img, "sidedoor"), f"sidedoor-{part}")
        dented = img.copy()
        rng = random.Random(seed_of("dent" + part))
        px = dented.load()
        if part == "lower":
            for cx, cy, r in ((16, 8, 7), (10, 14, 4), (21, 15, 5)):
                for y in range(S):
                    for x in range(S):
                        dd = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                        if r - 1.5 < dd < r:
                            M.touch(dented, x, y, -0.22 if y > cy else 0.12)
        for _ in range(7):
            x, y = rng.randrange(4, S - 4), rng.randrange(2, S - 6)
            for k in range(rng.randint(4, 9)):
                if 0 <= x + k < S and 0 <= y + k // 2 < S:
                    px[x + k, y + k // 2] = M.rgba(M.lift(px[x + k, y + k // 2], 40))
                    if y + k // 2 + 1 < S:
                        M.touch(dented, x + k, y + k // 2 + 1, -0.12)
        T.blotch(dented, (rng.randrange(S), rng.randrange(S)), 7, (106, 58, 32), 0.35, seed_of("dentrust" + part))
        save(dented, f"sidedoor-dented-{part}")
    save(matched(door_paint((136, 141, 144), "sidedoorback", "upper", chips=1), "sidedoor-back"), "sidedoor-back")
    save(matched(M.brushed_metal(seed_of("b14push"), base=(170, 174, 176), grain=3, direction="h"), "chrome", (167, 171, 174)), "pushplate")
    img = M.painted_metal(seed_of("b14bead"), base=(104, 109, 112), grain=2, panel=False, chips=0)
    save(img, "runbead")
    # Wired glass: dark glass, a diamond mesh of wire, a soft reflection; the bead round it is geometry now
    img = M.noise_hv((40, 48, 52), 2, seed_of("b14wired"), mottle=3, cells=(16, 8))
    p = img.load()
    for y in range(S):
        for x in range(S):
            g = 1 - abs(((x + y) % 32) - 9) / 7.0
            if g > 0:
                p[x, y] = M.rgba(M.lift(p[x, y], 14 * g))
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                p[x, y] = M.rgba(M.mix(p[x, y], (128, 136, 140), 0.75))
    save(img, "wiredglass")

    # Fire doors: red paint worn to the primer at the edges, a stencilled EXIT; the kick plate is the Kick box only
    for part in ("lower", "upper"):
        img = door_paint((160, 40, 36), "exitdoor", part, chips=6, under=(138, 132, 124))
        if part == "upper":
            ptext(img, "EXIT", 6, 10, (234, 228, 218), RUN_F5, 1)
        save(matched(img, "exitdoor") if part == "lower" else img, f"exitdoor-{part}")
    save(matched(door_paint((144, 26, 22), "exitdoorback", "upper", chips=2), "exitdoor-back"), "exitdoor-back")
    # The marked door: pale, a huge red "!" painted across it (B0's drawing on the new leaf)
    big = Image.new("RGBA", (S, 2 * S))
    big.paste(door_paint((216, 214, 206), "markeddoor", "upper", 2), (0, 0))
    big.paste(door_paint((216, 214, 206), "markeddoor", "lower", 2), (0, S))
    T.blotch(big, (16, 50), 14, (180, 170, 150), 0.25, seed_of("markedgrime"))
    d = ImageDraw.Draw(big)
    red = rgb(0xE01810)
    d.polygon([(9, 4), (23, 4), (20, 38), (12, 38)], fill=red)
    d.ellipse([10, 44, 22, 56], fill=red)
    rng = random.Random(seed_of("drips"))
    for x0, y0 in ((13, 38), (17, 38), (19, 36), (14, 55), (19, 54), (10, 20), (22, 12)):
        n = rng.randint(3, 9)
        d.line([x0, y0, x0, min(2 * S - 2, y0 + n)], fill=red, width=1)
        d.point([(x0, min(2 * S - 2, y0 + n + 1))], fill=shade(red, 0.8))
    px = big.load()
    for _ in range(80):
        x, y = rng.randrange(S), rng.randrange(2 * S)
        if px[x, y][0] > 200 and px[x, y][1] < 60:
            px[x, y] = shade(px[x, y], rng.uniform(0.82, 1.08))
    lower, upper = split_tall(big)
    save(lower, "markeddoor-lower")
    save(upper, "markeddoor-upper")
    # The chained door: steel, rust run down from the top
    big = Image.new("RGBA", (S, 2 * S))
    big.paste(door_paint((138, 142, 144), "chaindoor", "upper", 4), (0, 0))
    big.paste(door_paint((138, 142, 144), "chaindoor", "lower", 4), (0, S))
    rng = random.Random(seed_of("rust"))
    px = big.load()
    for _ in range(9):
        x, y, n = rng.randrange(S), rng.randrange(0, 20), rng.randint(10, 40)
        for k in range(n):
            if y + k < 2 * S:
                px[x, y + k] = M.rgba(M.mix(px[x, y + k], (106, 58, 32), 0.6 * (1 - k / n)))
    T.blotch(big, (8, 50), 9, (106, 58, 32), 0.4, seed_of("rustb"))
    lower, upper = split_tall(big)
    save(lower, "chaindoor-lower")
    save(upper, "chaindoor-upper")
    save(matched(door_paint((142, 146, 149), "steel", "upper", 3), "sidedoor-back", (141, 146, 149)), "steel")
    # The hall door: a flush wooden leaf in a dark steel frame (its vision panel an opening, hall_door)
    for part in ("lower", "upper"):
        img = M.wood_planks(seed_of("b14halldoor"), base=(140, 108, 74), planks=1, direction="v", grain=3, knots=0,
                            joints=0, per_plank=0, contrast=0.4, flecks=0.4)
        img = img.crop((0, 0, S, S)) if part == "upper" else img
        edges(img, "lrb" if part == "lower" else "lrt", 0.1, 0.18)
        save(matched(img, "halldoor"), f"halldoor-{part}")
    img = M.wood_planks(seed_of("b14halldoorback"), base=(140, 110, 80), planks=1, direction="v", grain=3, per_plank=0,
                        contrast=0.4, flecks=0.4)
    save(matched(img, "halldoor-back"), "halldoor-back")
    save(matched(M.painted_metal(seed_of("b14hallframe"), base=(78, 82, 86), panel=False, chips=3, under=(130, 132, 132)),
                 "hallframe"), "hallframe")
    save(matched(M.brushed_metal(seed_of("b14hallkick"), base=(166, 170, 172), grain=3, direction="h"), "chrome",
                 (163, 167, 169)), "hallkick")


def b14_props():
    # Chrome tube: a brushed sheen along the tube
    save(matched(M.brushed_metal(seed_of("b14chrome"), base=(186, 190, 194), grain=3, direction="h", sheen=14), "chrome"), "chrome")
    save(matched(M.painted_metal(seed_of("b14gurneyframe"), base=(112, 116, 120), panel=False, chips=2), "gurneyframe"), "gurneyframe")
    save(matched(M.painted_metal(seed_of("b14beamsteel"), base=(60, 64, 68), panel=False, chips=2), "beamsteel"), "beamsteel")
    # Sheets: cotton weave, soft fold shadows that bend across the bed
    img = M.fabric(seed_of("b14sheet"), base=(228, 228, 222), weave="plain", contrast=4, grain=2, mottle=3)
    rng = random.Random(seed_of("sheetfold"))
    for _ in range(4):
        y0 = rng.randrange(S)
        for x in range(S):
            yy = y0 + 2.2 * math.sin(x / 5 + y0)
            for dy, f in ((-1, 0.05), (0, -0.07), (1, -0.04)):
                M.touch(img, x, int(yy) + dy, f)
    save(matched(img, "sheet"), "sheet")
    save(matched(M.fabric(seed_of("b14pillow"), base=(238, 234, 222), weave="plain", contrast=3, grain=2, mottle=3), "pillow"), "pillow")
    # The mattress: wipe-clean blue-grey vinyl, a welt seam round it, a shallow quilting in a diamond, one old stain
    img = M.noise_hv((92, 112, 132), 2, seed_of("b14mattress"), mottle=4, cells=(16, 8))
    for y in range(S):
        for x in range(S):
            u, v = (x + y) % 16, (x - y) % 16
            if u == 0 or v == 0:
                M.touch(img, x, y, -0.12)
            elif u == 1 or v == 1:
                M.touch(img, x, y, 0.05)
    M.ao_border(img, 2, 0.16)
    M.stain(img, seed_of("mattressstain"), radius=6, color=(96, 88, 62), strength=0.3, at=(21, 11))
    save(matched(img, "mattress"), "mattress")
    # The crash cart: red powder coat; its drawers are boxes now (props_b14)
    save(matched(M.painted_metal(seed_of("b14cartside"), base=(184, 42, 34), panel=False, chips=3, under=(150, 146, 140)),
                 "cartside"), "cartside")
    img = M.painted_metal(seed_of("b14cartfront"), base=(176, 38, 30), panel=False, chips=2, under=(150, 146, 140))
    save(matched(img, "cartside", (176, 40, 32)), "cartdrawer")
    img = Image.new("RGBA", (S, S), (240, 200, 56, 255))
    img = M.noise_hv((240, 202, 60), 2, seed_of("b14cartlabel"), mottle=2)
    for x in range(4, 28, 3):
        M.touch(img, x, 3, -0.4)
    save(img, "cartlabel")
    # The defibrillator: dark grey case, the screen an inset plate of its own (defibscreen)
    save(M.painted_metal(seed_of("b14defib"), base=(58, 60, 56), grain=2, panel=False, chips=1), "defib")
    img = M.noise_hv((22, 38, 28), 2, seed_of("b14defibscr"), mottle=2)
    d = ImageDraw.Draw(img)
    d.line([1, 16, 7, 16, 9, 8, 11, 24, 13, 13, 15, 16, 22, 16, 24, 9, 26, 22, 28, 16, 31, 16], fill=(72, 230, 104, 255))
    save(img, "defibscreen")
    # Supply cabinet steel (enamel) and its door (the label holder and vents as before, crisper)
    save(matched(M.painted_metal(seed_of("b14cabsteel"), base=(156, 168, 162), grain=2, panel=False, chips=2), "cabsteel"), "cabsteel")
    img = M.painted_metal(seed_of("b14cabdoor"), base=(152, 164, 158), grain=2, panel=False, chips=2)
    edges(img, "lrtb", 0.1, 0.16)
    for y in (22, 25, 28):  # (round 2) the label holder is a box on the door now (gauntlet's LabelL)
        for x in range(8, 24):
            M.touch(img, x, y, -0.32)
            M.touch(img, x, y + 1, 0.10)
    save(img, "cabdoor")
    img = M.noise_hv((232, 230, 218), 2, seed_of("b14cablabel"), mottle=2)
    M.bevel(img, (0, 0, S, S), 2, 0.2)
    for x in range(6, 26):
        img.putpixel((x, 15), (130, 130, 126, 255))
    save(img, "cablabel")
    # Medicine cabinet: white enamel; its mirror is an inset pane now, the red cross a decal on the frame
    save(matched(M.painted_metal(seed_of("b14cabinet"), base=(236, 236, 230), grain=2, mottle=3, panel=False, chips=1,
                                 under=(190, 190, 186)), "cabinet"), "cabinet")
    img = M.noise_hv((168, 182, 188), 2, seed_of("b14mirror"), mottle=4, cells=(16, 8))
    p = img.load()
    for y in range(S):
        for x in range(S):
            g = 1 - abs(((x + y) % 40) - 14) / 6.0
            if g > 0:
                p[x, y] = M.rgba(M.lift(p[x, y], 22 * g))
    save(img, "cabmirror")
    img = M.painted_metal(seed_of("b14cabfront"), base=(236, 236, 230), grain=2, mottle=3, panel=False, chips=0)
    for (x0, y0, x1, y1) in ((14, 2, 18, 8), (12, 4, 20, 6)):
        for y in range(y0, y1):
            for x in range(x0, x1):
                img.putpixel((x, y), M.rgba(M.lift((206, 28, 30), random.Random(x * 3 + y).uniform(-4, 4))))
    save(img, "cabinetfront")
    # The privacy curtain: pale green cotton; the pleats' light and shade follow the folds (its pleats are boxes)
    img = M.fabric(seed_of("b14curtain"), base=(142, 176, 152), weave="plain", contrast=5, grain=2, mottle=4)
    for y in range(S):
        for x in range(S):
            M.touch(img, x, y, 0.08 * math.sin(x / S * 2 * math.pi * 2))
    save(matched(img, "curtain"), "curtain")
    # Bedside table: laminate on top and sides, a raised edge on the drawer and door fronts
    img = M.wood_planks(seed_of("b14bedside"), base=(218, 206, 180), planks=1, direction="h", grain=2, per_plank=0, contrast=0.5)
    save(matched(img, "bedside"), "bedside")
    img = M.noise_hv((214, 203, 178), 2, seed_of("b14bedsidefront"), mottle=3)
    M.bevel(img, (0, 0, S, S), 1, 0.12)
    save(img, "bedsidefront")
    # Blue steel shelving: powder coat, the uprights' slots as dark pits with a lit lower lip
    img = M.painted_metal(seed_of("b14shelfblue"), base=(46, 92, 152), panel=False, chips=3, under=(150, 150, 146))
    for y in range(1, S, 4):
        for x in range(S):
            if x % 8 in (3, 4):
                M.touch(img, x, y, -0.45)
                M.touch(img, x, y + 1, 0.08)
    save(matched(img, "shelfblue"), "shelfblue")


def b14_startroom():
    # Notices on white card, in a pixel face (B9's lesson: scaled-down type smears)
    ink, blue, red, grey = (40, 40, 46), (30, 90, 170), (200, 30, 36), (150, 150, 156)
    card = lambda key: M.paper(seed_of(key), (32, 40), base=(244, 244, 238), grain=2, mottle=2, fibre=0.3, seams=0, strip=0)
    img = card("b14handwash")
    for y in range(0, 8):
        for x in range(32):
            img.putpixel((x, y), M.rgba(M.lift(blue, random.Random(x * 13 + y).uniform(-3, 3))))
    ptext_c(img, "PLEASE", 1, (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.polygon([(16, 9), (14, 12), (18, 12)], fill=blue + (255,))  # the drop
    d.ellipse([14, 11, 18, 14], fill=blue + (255,))
    skin, line = (232, 196, 170, 255), (150, 110, 90, 255)
    for x0, flip in ((8, False), (18, True)):  # two hands under the drop: a palm, four fingers up, a thumb in
        d.rectangle([x0 + 1, 16, x0 + 5, 18], fill=skin)
        for f in range(4):
            d.line([x0 + 1 + f + (1 if flip else 0), 14 + (f in (0, 3)), x0 + 1 + f + (1 if flip else 0), 15], fill=skin)
        tx = x0 + 6 if not flip else x0
        d.line([tx, 16, tx, 17], fill=skin)
        d.line([x0 + 1, 19, x0 + 5, 19], fill=line)
    ptext_c(img, "WASH", 21, ink)
    ptext_c(img, "YOUR", 27, ink)
    ptext_c(img, "HANDS", 33, blue)
    M.bevel(img, (0, 0, 32, 40), 1, 0.06)
    save(img, "notice-handwash")
    img = card("b14visiting")
    d = ImageDraw.Draw(img)
    d.rectangle([14, 2, 17, 11], fill=red + (255,))
    d.rectangle([11, 5, 20, 8], fill=red + (255,))
    ptext_c(img, "VISITING", 14, ink)
    ptext_c(img, "HOURS", 20, ink)
    ptext_c(img, "2-8", 27, grey)
    for i, (x0, x1) in enumerate(((5, 27), (7, 25))):
        for x in range(x0, x1):
            if (x * 7 + i) % 5:
                img.putpixel((x, 34 + i * 2), (176, 176, 180, 255))
    M.bevel(img, (0, 0, 32, 40), 1, 0.06)
    save(img, "notice-visiting")
    # The dispenser: white ABS; its window and drop are a panel of their own now (dispenserfront: just the label)
    save(matched(M.painted_metal(seed_of("b14dispenser"), base=(240, 240, 236), grain=2, mottle=2, panel=False, chips=0),
                 "dispenser"), "dispenser")
    img = M.noise_hv((240, 240, 236), 1, seed_of("b14dispfront"), (16, 16), mottle=1)
    d = ImageDraw.Draw(img)
    d.polygon([(8, 7), (6, 10), (10, 10)], fill=(42, 106, 184, 255))
    d.ellipse([6, 8, 10, 12], fill=(42, 106, 184, 255))
    save(img, "dispenserfront")
    img = M.noise_hv((150, 196, 220), 1, seed_of("b14gel"), mottle=2)
    for x in range(S):
        for y in range(10):
            M.touch(img, x, y, 0.12)
    save(img, "dispensergel")


def b14_textures():
    b14_walls()
    b14_floor()
    b14_ceiling()
    b14_rail()
    b14_signs()
    b14_doors()
    b14_props()
    b14_startroom()


NL = "\n"


def generate():
    clean()
    textures()
    walls()
    signs()
    side_doors()
    exit_doors()
    chained_door()
    hall_door()
    props()
    gauntlet()
    trip_props()
    startroom()
    b14_textures()
    items()
    lang()
    gen_detail.merge_lang()
    prune_lang()
    print(f"run: {len(MINE)} textures, {len(LANG)} names")
    if "--no-sounds" not in sys.argv:
        sounds()


if __name__ == "__main__":
    generate()
