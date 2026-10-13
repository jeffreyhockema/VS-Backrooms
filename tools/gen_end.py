"""The End (level 16): the empty bookstore-library with THE END over its service desk.

Its blocks, 3D shapes, items, sounds, found books and English text, from docs/design/new-levels/end-plan.md section 4.
Run from the repo root, through the asset lock:

    bash tools/locked.sh run python tools/gen_end.py

Everything is written to its own folders (textures/block/end, textures/item/end, shapes/block/end, shapes/item/end,
blocktypes/end, itemtypes/end, sounds/ambient/end); English text is merged into lang/en.json in place. The found
books' texts live in the code (src/Regions/EndSystem.cs), not here.

The look is the photographs of a closed-down bookstore and the Wikidot render: pale maple shelving, empty; tapered slatwall
towers; sage and slate columns clad in slatwall to head height; a cream wall under a yellow band; grey-green
low-pile carpet with a field of navy patterned carpet; a curved maple desk with a beige CRT; a lowered soffit with
bronze letters; a 2x2 acoustic tile ceiling dense with troffers. Detail is modelled, not painted: shelves, books,
drawers, letters, neon tubes, louvres and push bars are boxes. Shapes face north (their front toward -Z) and are
turned for the other three sides.
"""
import json
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
from detail_kit import ASSETS, CLOTH, GLASS, METAL, ROTATE, SIDES, STONE, WOOD, T, bx, cuboid, ground_storable, seed_of, turn, write_json  # noqa: E402

S = 32
LANG = {}
SHAPES = []          # every shape written, for previews
CODES = []           # every block code written

# Vanilla codes used in drops (checked against the installed game's assets)
PLANK, STICK, FIREWOOD, NAILS = "game:plank-aged", "game:stick", "game:firewood", "game:metalnailsandstrips-iron"
PAPER, CLOTHV, INK = "game:paper-parchment", "game:cloth-plain", "game:inkandquill"
CHAIR, TABLE, SHELF, LADDER = "block:game:chair-plain", "block:game:table-normal", "block:game:shelf-normal-north", "block:game:ladder-wood-oak-north"

# Texture keys that live elsewhere; every other key is a texture of ours in block/end/
EXT = {
    "cardboard": "backrooms:block/supplybox-side",
    "cardboardtop": "backrooms:block/supplybox-top",
    "concretewall": "backrooms:block/level1/concretewall-plain",
    "membrane": "backrooms:block/end/membrane0",   # the doorframe's block type adds membrane1 and 2 as alternates
}


def H(h, a=255):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255, a)


def clamp(v):
    return max(0, min(255, int(v)))


def tpath(key):
    return EXT.get(key, f"backrooms:block/end/{key}")


# ======================= Pixel fonts =======================

F5 = {  # 5x7
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    ",": ["000", "000", "000", "000", "011", "010", "100"],
    ".": ["00", "00", "00", "00", "00", "11", "11"],
    ":": ["00", "11", "11", "00", "11", "11", "00"],
    "-": ["0000", "0000", "0000", "1111", "0000", "0000", "0000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    ")": ["100", "010", "001", "001", "001", "010", "100"],
    "!": ["1", "1", "1", "1", "1", "0", "1"],
    " ": ["000", "000", "000", "000", "000", "000", "000"],
}
F3 = {  # 3x5
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"], "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"], "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"], "H": ["101", "101", "111", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"], "K": ["101", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"], "N": ["110", "101", "101", "101", "101"], "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"], "Q": ["010", "101", "101", "110", "011"], "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"], "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"], "W": ["101", "101", "111", "111", "101"], "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"], "Z": ["111", "001", "010", "100", "111"], "&": ["010", "101", "010", "101", "011"],
    ",": ["0", "0", "0", "1", "1"], ".": ["0", "0", "0", "0", "1"], "-": ["000", "000", "111", "000", "000"],
    ":": ["0", "1", "0", "1", "0"], "=": ["000", "111", "000", "111", "000"], ")": ["10", "01", "01", "01", "10"],
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "110", "001", "110"],
    "6": ["011", "100", "110", "101", "010"], "7": ["111", "001", "010", "010", "010"], "8": ["010", "101", "010", "101", "010"],
    "9": ["010", "101", "011", "001", "110"], " ": ["00", "00", "00", "00", "00"],
}


def text_width(s, font=F5, scale=1, bold=False, gap=1):
    w = 0
    for ch in s.upper():
        g = font.get(ch, font[" "])
        w += (len(g[0]) + (1 if bold else 0)) * scale + gap * scale
    return max(0, w - gap * scale)


def draw_text(img, s, x, y, col, font=F5, scale=1, bold=False, gap=1):
    px = img.load()
    W, Hh = img.size
    for ch in s.upper():
        g = font.get(ch, font[" "])
        for ry, row in enumerate(g):
            for rx, c in enumerate(row):
                if c != "1":
                    continue
                for dx in range(scale * (2 if bold else 1)):
                    for dy in range(scale):
                        X, Y = x + rx * scale + dx, y + ry * scale + dy
                        if 0 <= X < W and 0 <= Y < Hh:
                            px[X, Y] = col
        x += (len(g[0]) + (1 if bold else 0)) * scale + gap * scale
    return x


def centred(img, s, y, col, font=F5, scale=1, bold=False, gap=1, x0=0, x1=None):
    x1 = img.size[0] if x1 is None else x1
    w = text_width(s, font, scale, bold, gap)
    draw_text(img, s, x0 + (x1 - x0 - w) // 2, y, col, font, scale, bold, gap)


# ======================= Texture helpers =======================

def save(img, name):
    T.save(img, f"block/end/{name}.png")


# The face UVs of the two pictures padded out to the atlas grid (see gen_textures.ATLAS_GRID), set when they are drawn
INFOSIGN_UV = [0, 0, 16, 16]
STAFFPLATE_UV = [0, 0, 16, 16]


def save_item(img, name):
    T.save(img, f"item/end/{name}.png")


def noisy(c, n, key, w=S, h=S, alpha=255):
    rng = random.Random(seed_of(key))
    img = Image.new("RGBA", (w, h))
    px = img.load()
    c = H(c) if isinstance(c, int) else c
    for y in range(h):
        for x in range(w):
            d = rng.randint(-n, n)
            px[x, y] = (clamp(c[0] + d), clamp(c[1] + d), clamp(c[2] + d), alpha)
    return img


def tint(img, f):
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f), a)
    return img


def grain(img, key, light, dark, count=14, horizontal=True, length=(5, 18), alpha=0.5):
    """Wood grain: soft streaks along the board, tiling."""
    rng = random.Random(seed_of(key + "grain"))
    px = img.load()
    w, h = img.size
    for _ in range(count):
        col = light if rng.random() < 0.5 else dark
        a, b = rng.randrange(w), rng.randrange(h)
        n = rng.randint(*length)
        for k in range(n):
            x, y = ((a + k) % w, b) if horizontal else (a, (b + k) % h)
            if rng.random() < 0.15:
                b = (b + rng.choice((-1, 1))) % h if horizontal else b
                a = a if horizontal else (a + rng.choice((-1, 1))) % w
            r, g, bb, al = px[x, y]
            px[x, y] = (clamp(r + (col[0] - r) * alpha), clamp(g + (col[1] - g) * alpha), clamp(bb + (col[2] - bb) * alpha), al)
    return img


def crack(img, key, col, start=None, length=26):
    rng = random.Random(seed_of(key + "crack"))
    px = img.load()
    w, h = img.size

    def walk(x, y, n, dx):
        for _ in range(n):
            px[x % w, y % h] = col
            y += 1
            x += rng.choice((dx, dx, 0, -dx)) if rng.random() < 0.6 else 0
            if rng.random() < 0.08 and n > 6:
                walk(x, y, n // 3, -dx)
    x0, y0 = start or (rng.randrange(6, w - 6), rng.randrange(0, 6))
    walk(x0, y0, length, rng.choice((-1, 1)))
    return img


def ring(img, key, col, strength=0.35):
    """A tan water ring: a soft disc, darker at its edge."""
    rng = random.Random(seed_of(key + "ring"))
    px = img.load()
    w, h = img.size
    cx, cy, r = rng.uniform(10, 22), rng.uniform(10, 22), rng.uniform(6, 9)
    for y in range(h):
        for x in range(w):
            dx = min(abs(x - cx), w - abs(x - cx))
            dy = min(abs(y - cy), h - abs(y - cy))
            d = math.hypot(dx, dy) / r
            if d < 1.15:
                t = strength * (0.35 + 0.65 * math.exp(-((d - 0.95) / 0.12) ** 2)) * (1 if d < 1 else (1.15 - d) / 0.15)
                t *= rng.uniform(0.8, 1.1)
                r0, g0, b0, a0 = px[x, y]
                px[x, y] = (clamp(r0 + (col[0] - r0) * t), clamp(g0 + (col[1] - g0) * t), clamp(b0 + (col[2] - b0) * t), a0)
    return img


def tiled_draw(size, draw_fn):
    """Draws on a 3x3 tiled canvas and crops the middle, so strokes wrap seamlessly."""
    w, h = size
    big = Image.new("RGBA", (w * 3, h * 3), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), w, h)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i in range(3):
        for j in range(3):
            out.alpha_composite(big.crop((i * w, j * h, i * w + w, j * h + h)))
    return out


# ======================= Textures =======================

CARPET, LOOP, DUST = 0x646B5F, 0x5A6155, 0x8C9086
MAPLE, MAPLE_L, MAPLE_D, GROOVE = 0xCD9A55, 0xDDB06C, 0xA9763A, 0x7A5428
WALL_LO, SCUFF, GHOST, BAND, BAND_E, WALL_UP, COVE = 0xEEEBE0, 0xD8D3C4, 0xF6F4EC, 0xDDB03A, 0xB88E22, 0xEBD69C, 0x45413B
SAGE, SLATE, CEIL, GRID, LENS = 0x9AAE86, 0x8B9AB1, 0xE8E5DC, 0xC2BDB0, 0xFBFCF8
BRONZE, BRONZE_H = 0x463B2C, 0x75664C
P_YEL, P_PINK, P_GREEN = 0xF2E43C, 0xF09CC2, 0xA6DE78
CRT, CRT_S, CRT_G, KICK = 0xCFC6AE, 0xA99F86, 0x1C2220, 0x2A2622


def carpet_tex(key, light=0, loops=True):
    rng = random.Random(seed_of(key))
    img = noisy(CARPET, 5, key)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            if loops and (x + 2 * ((y // 2) % 2)) % 4 == 0 and y % 2 == 0:
                c = H(LOOP)
                px[x, y] = (clamp(c[0] + rng.randint(-3, 3) + light), clamp(c[1] + rng.randint(-3, 3) + light), clamp(c[2] + rng.randint(-3, 3) + light), 255)
            else:
                px[x, y] = (clamp(r + light), clamp(g + light), clamp(b + light), 255)
    return img


def textures():
    # ---- Carpet: the grey-green low pile, dusty, worn flat, stained, half under snow
    save(carpet_tex("carpet"), "carpet-plain")
    img = carpet_tex("carpetd")
    rng = random.Random(seed_of("dusty"))
    px = img.load()
    for _ in range(int(S * S * 0.3)):
        x, y = rng.randrange(S), rng.randrange(S)
        c = H(DUST)
        px[x, y] = (clamp(c[0] + rng.randint(-6, 6)), clamp(c[1] + rng.randint(-6, 6)), clamp(c[2] + rng.randint(-6, 6)), 255)
    save(img, "carpet-dusty")
    img = carpet_tex("carpetw", light=9, loops=False)
    rng = random.Random(seed_of("worn"))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        y = rng.randrange(S)
        x = rng.randrange(S)
        d.line([x, y, x + rng.randint(4, 10), y], fill=(126, 132, 118, 255))
    save(img, "carpet-worn")
    save(ring(carpet_tex("carpets"), "carpets", (140, 118, 78), 0.55), "carpet-stained")
    # Powder snow over carpet: drifts, more snow than carpet, soft edges
    img = carpet_tex("carpetn")
    field = __import__("texlib")._periodic_noise(seed_of("snowfield"), 3)
    px = img.load()
    rng = random.Random(seed_of("snowy"))
    for y in range(S):
        for x in range(S):
            v = field[y][x] + 0.18
            if v > 0.05:
                s = 244 + rng.randint(-4, 4)
                px[x, y] = (clamp(s - 4), clamp(s - 2), clamp(s + 4), 255)
            elif v > -0.05:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp((r + 230) / 2), clamp((g + 234) / 2), clamp((b + 240) / 2), 255)
    save(img, "carpet-snowy")
    img = carpet_tex("carpetns")
    d = ImageDraw.Draw(img)
    for x in range(S):
        top = 3 + (1 if (x * 7) % 5 == 0 else 0)
        d.line([x, 0, x, top], fill=(240, 243, 248, 255))
    save(img, "carpet-snowyside")

    # ---- The runway: navy commercial carpet, small irregular squiggles and dots
    base = noisy(0x2E3968, 4, "runway")

    def squiggles(d, w, h):
        rng = random.Random(seed_of("squig"))
        for _ in range(16):
            x, y = rng.uniform(w, 2 * w), rng.uniform(h, 2 * h)
            pts = [(x, y)]
            ang = rng.uniform(0, 6.28)
            for _ in range(rng.randint(3, 6)):
                ang += rng.uniform(-1.4, 1.4)
                x += 1.6 * math.cos(ang)
                y += 1.6 * math.sin(ang)
                pts.append((x, y))
            d.line(pts, fill=H(0x5868A4), width=1)
        for _ in range(26):
            x, y = rng.randrange(w, 2 * w), rng.randrange(h, 2 * h)
            d.point((x, y), fill=H(0x98A2C6))
    base.alpha_composite(tiled_draw((S, S), squiggles))
    save(base, "runway")

    # ---- Stockroom concrete, sealed; with a yellow safety line either way
    field = __import__("texlib")._periodic_noise(seed_of("concrete"), 3)
    img = noisy(0x8C8A84, 3, "concrete")
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            f = 1 + 0.05 * field[y][x]
            px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f), 255)
    rng = random.Random(seed_of("pits"))
    for _ in range(10):
        px[rng.randrange(S), rng.randrange(S)] = (110, 108, 102, 255)
    save(img, "concrete")
    for axis in ("ns", "we"):
        line = img.copy()
        d = ImageDraw.Draw(line)
        if axis == "ns":
            d.rectangle([14, 0, 17, S - 1], fill=H(0xE2B92A))
        else:
            d.rectangle([0, 14, S - 1, 17], fill=H(0xE2B92A))
        rng = random.Random(seed_of("line" + axis))
        lp = line.load()
        for _ in range(30):  # worn through to the concrete here and there
            k, j = rng.randrange(S), rng.randrange(14, 18)
            x, y = (j, k) if axis == "ns" else (k, j)
            lp[x, y] = px[x, y]
        save(line, f"concrete-line{axis}")

    # ---- Walls: the stack in plan 3.3 (base with cove, off-white lower, the yellow band, yellow-cream upper)
    def lower(key):
        img = noisy(WALL_LO, 3, key)
        rng = random.Random(seed_of(key + "scuff"))
        d = ImageDraw.Draw(img)
        for _ in range(3):
            y = rng.randrange(16, S)
            x = rng.randrange(S)
            d.line([x, y, x + rng.randint(3, 8), y], fill=H(SCUFF))
        return img
    save(lower("walllower"), "wall-lower")
    img = lower("wallbase")
    d = ImageDraw.Draw(img)
    d.rectangle([0, S - 4, S - 1, S - 1], fill=H(COVE))
    d.line([0, S - 5, S - 1, S - 5], fill=H(0x5A554D))
    save(img, "wall-base")
    img = lower("wallghost")
    d = ImageDraw.Draw(img)
    d.rectangle([7, 9, 24, 20], fill=H(GHOST))
    for x, y in ((8, 10), (23, 10), (8, 19), (23, 19)):
        d.point((x, y), fill=H(0x8E8A80))
    d.line([7, 21, 24, 21], fill=H(0xE2DED2))
    save(img, "wall-ghost")
    save(crack(lower("wallcracked"), "wallcracked", H(0x8A8478), length=30), "wall-cracked")
    img = noisy(BAND, 3, "band")
    d = ImageDraw.Draw(img)
    d.line([0, 0, S - 1, 0], fill=H(BAND_E))
    d.line([0, S - 1, S - 1, S - 1], fill=H(BAND_E))
    save(img, "wall-band")
    save(noisy(WALL_UP, 3, "wallupper"), "wall-upper")
    save(crack(noisy(WALL_UP, 3, "wallupcr"), "wallupcr", H(0xA89A70), length=30), "wall-uppercracked")
    # Painted concrete block, stockrooms: 16x8 courses, staggered
    img = noisy(0xD9D5C9, 3, "block")
    d = ImageDraw.Draw(img)
    for r in range(4):
        y = r * 8
        d.line([0, y, S - 1, y], fill=H(0xBAB4A6))
        off = 8 if r % 2 else 0
        for x in range(off, S + 16, 16):
            d.line([x % S, y, x % S, y + 7], fill=H(0xBAB4A6))
    save(img, "wall-block")

    # ---- Columns: flat paint with a faint roller texture; maple slatwall
    for name, c in (("sage", SAGE), ("slate", SLATE)):
        img = noisy(c, 2, "col" + name)
        rng = random.Random(seed_of("roller" + name))
        px = img.load()
        for x in range(S):
            f = 1 + rng.uniform(-0.015, 0.015)
            for y in range(S):
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f), a)
        save(img, f"column-{name}")

    # ---- Maple: shelving, desk, tables; slatwall with its grooves every 4 px
    def maple(c, key):
        img = noisy(c, 3, key)
        return grain(img, key, tuple(min(255, v + 18) for v in H(c)[:3]), H(MAPLE_D)[:3], count=18)
    save(maple(MAPLE, "maple"), "maple")
    save(maple(MAPLE_L, "maplelight"), "maple-light")
    save(grain(noisy(MAPLE_D, 3, "mapledark"), "mapledark", (190, 140, 80), (130, 90, 44), 10), "maple-dark")
    img = maple(MAPLE, "maplev").rotate(90)
    save(img, "maple-vertical")
    img = maple(MAPLE, "slat")
    d = ImageDraw.Draw(img)
    for y in range(3, S, 4):
        d.line([0, y, S - 1, y], fill=H(GROOVE))
        d.line([0, y - 1, S - 1, y - 1], fill=H(0xB98848))
    save(img, "slatwall")
    save(noisy(KICK, 2, "kick"), "kick")
    save(noisy(0x9C9A92, 2, "pricechannel"), "pricechannel")
    save(noisy(0xC8B48C, 5, "particle"), "particleboard")

    # ---- Ceiling: 2x2 tiles to a block, fissured; stained; missing (the black plenum between the T-bars)
    def ceiling(key):
        img = noisy(CEIL, 2, key)
        rng = random.Random(seed_of(key + "f"))
        px = img.load()
        for _ in range(70):
            x, y = rng.randrange(S), rng.randrange(S)
            px[x, y] = H(0xCFCBC0)
            if rng.random() < 0.3:
                px[(x + 1) % S, y] = H(0xD6D2C8)
        d = ImageDraw.Draw(img)
        for k in (0, 16):
            d.line([0, k, S - 1, k], fill=H(GRID))
            d.line([k, 0, k, S - 1], fill=H(GRID))
        return img
    save(ceiling("ceiling"), "ceiling-plain")
    save(ring(ceiling("ceilings"), "ceilings", (176, 150, 100), 0.5), "ceiling-stained")
    img = noisy(0x1C1A18, 2, "plenum")
    d = ImageDraw.Draw(img)
    for k in (0, 16):
        d.rectangle([0, k, S - 1, k + 1], fill=H(0xC9C6BC))
        d.rectangle([k, 0, k + 1, S - 1], fill=H(0xC9C6BC))
    d.line([20, 2, 26, 15], fill=H(0x3A3630))  # a wire hanging in the dark
    save(img, "ceiling-missing")
    save(noisy(0x1C1A18, 2, "plenumflat"), "plenum")
    save(noisy(0xD8D6CE, 2, "tbar"), "tbar")

    # ---- Troffers: white frame, prismatic lens with a fine diamond pattern; a dead one
    # (The lit lens is near white with a faint prism, inside a 1 px white line, so it reads as light under the haze)
    for state, lens, prism in (("on", LENS, 0xF0F2EE), ("off", 0xB8BAB2, 0xAAACA4)):
        img = Image.new("RGBA", (S, S), H(0xF2F2EE))
        px = img.load()
        for y in range(3, S - 3):
            for x in range(3, S - 3):
                px[x, y] = H(prism) if (x + y) % 4 == 0 or (x - y) % 4 == 0 else H(lens)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=H(0xD8D8D2))
        if state == "on":
            d.rectangle([2, 2, S - 3, S - 3], outline=H(0xFFFFFF))
        d.rectangle([3, 15, S - 4, 16], fill=H(0xE6E6E0 if state == "off" else 0xF6F7F2))
        save(img, f"troffer-{state}")

    # ---- Soffit: yellow-cream face with the band along its foot; white underside
    img = noisy(WALL_UP, 3, "soffit")
    d = ImageDraw.Draw(img)
    d.rectangle([0, S - 7, S - 1, S - 2], fill=H(BAND))
    d.line([0, S - 7, S - 1, S - 7], fill=H(BAND_E))
    d.line([0, S - 1, S - 1, S - 1], fill=H(0xC9B47A))
    save(img, "soffit-face")
    save(noisy(0xF0EEE6, 2, "soffitunder"), "soffit-under")
    # Mezzanine fascia: white, maple trim top and bottom
    img = noisy(0xF2F0EA, 2, "fascia")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 3], fill=H(MAPLE))
    d.rectangle([0, S - 4, S - 1, S - 1], fill=H(MAPLE))
    d.line([0, 4, S - 1, 4], fill=H(MAPLE_D))
    save(img, "deck-fascia")

    # ---- Metals, glass, fabrics, small materials
    save(grain(noisy(0x463B2C, 4, "bronze"), "bronze", H(BRONZE_H)[:3], (52, 44, 32), 12, alpha=0.6), "bronze")
    save(grain(noisy(0xB9BDC0, 3, "brushed"), "brushed", (210, 214, 216), (150, 154, 158), 22, length=(8, 24)), "brushed")
    save(noisy(0x8E9196, 3, "steeldoor"), "steel")
    save(noisy(0xA8ADB0, 4, "galv"), "galvanised")
    save(noisy(0xC3C7CA, 2, "alu"), "aluminium")
    save(noisy(0x1E1E1E, 2, "rubber"), "rubber")
    save(noisy(0x151515, 2, "case"), "blackcase")
    save(noisy(0x2A2A2A, 3, "drum"), "drum")
    img = noisy(0xB8963E, 6, "brass")
    ImageDraw.Draw(img).line([0, 3, S - 1, 3], fill=(226, 200, 120, 255))
    save(img, "brass")
    save(noisy(0xDCEAF0, 3, "glass", alpha=70), "glass")
    img = noisy(0xD6E2E4, 3, "storeglass", alpha=90)
    d = ImageDraw.Draw(img)
    d.line([4, S - 4, S - 6, 6], fill=(255, 255, 255, 140))
    save(img, "storeglass")
    img = noisy(0x3E6E6A, 4, "teal")
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 3 == 0:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r - 8), clamp(g - 8), clamp(b - 8), a)
    save(img, "teal")
    img = noisy(0xB8913A, 4, "mustard")
    px = img.load()
    for y in range(0, S, 2):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r - 7), clamp(g - 7), clamp(b - 7), a)
    save(img, "mustard")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        d.line([0, y, S, y], fill=(clamp(46 + 30 * (1 - t)), clamp(122 + 40 * (1 - t)), clamp(78 + 30 * (1 - t)), 255))
    d.line([3, 4, S - 4, 4], fill=(170, 220, 180, 255))
    save(img, "greenglass")
    save(noisy(0xFFE6A8, 3, "lampglow"), "lampglow")
    save(noisy(0xFFF6E6, 2, "diffuser"), "diffuser")
    # Shrink wrap: milky, crinkled, catching the light; brown packing tape
    img = Image.new("RGBA", (S, S), (232, 236, 238, 110))
    rng = random.Random(seed_of("wrap"))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        x, y = rng.randrange(S), rng.randrange(S)
        d.line([x, y, x + rng.randint(-6, 6), y + rng.randint(4, 12)], fill=(255, 255, 255, 170))
    for _ in range(5):
        x, y = rng.randrange(S), rng.randrange(S)
        d.line([x, y, x + rng.randint(-5, 5), y + rng.randint(3, 8)], fill=(196, 204, 210, 140))
    save(img, "wrap")
    img = noisy(0xC9A46A, 4, "tape", alpha=225)
    save(img, "tape")
    save(noisy(0xEDEFEF, 3, "cleartape", alpha=120), "cleartape")
    img = noisy(0xC8A878, 7, "pallet")
    grain(img, "pallet", (220, 196, 150), (150, 120, 80), 16)
    save(img, "pallet")
    save(noisy(DUST, 6, "dust"), "dust")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(7):  # a corner web: spokes from the top-left, threads across them
        a = math.radians(k * 15)
        d.line([0, 0, 31 * math.cos(a), 31 * math.sin(a)], fill=(236, 236, 230, 200))
    for r in (7, 13, 19, 25):
        pts = [(r * math.cos(math.radians(k * 15)), r * math.sin(math.radians(k * 15))) for k in range(7)]
        d.line(pts, fill=(236, 236, 230, 180))
    save(img, "cobweb")
    # Book spines, six dull colours, a band and a title smudge on each
    for k, c in enumerate((0x6E2E2A, 0x2E4A3A, 0x2E3A5A, 0x6A5A3A, 0x4A3A4E, 0x7A6A52)):
        img = noisy(c, 4, f"book{k}")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 6, S - 1, 8], fill=H(0xC8B070) if k % 2 == 0 else H(0x1E1E1E))
        d.rectangle([0, 22, S - 1, 23], fill=H(0xC8B070) if k % 2 == 0 else H(0x1E1E1E))
        save(img, f"book{k}")
    save(noisy(0xF0EADA, 2, "pages"), "pages")
    # Golden oak for the card catalogue; its label cards
    img = noisy(0x8A5A30, 4, "oak")
    save(grain(img, "oak", (176, 120, 66), (100, 64, 30), 16), "oak")
    img = noisy(0x9E6A3A, 4, "oaklight")
    save(grain(img, "oaklight", (186, 132, 76), (110, 72, 36), 12), "oak-light")
    img = noisy(0xF1E8CF, 2, "label")
    d = ImageDraw.Draw(img)
    d.line([4, 14, 27, 14], fill=H(0x8A8070))
    d.line([4, 19, 20, 19], fill=H(0x8A8070))
    save(img, "label")
    img = noisy(0xF1E8CF, 2, "cards")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 3):
        d.line([0, y, S - 1, y], fill=H(0xD8CEB0))
    save(img, "cards")
    # Old aged oak for the free-standing doorframe, bark and snow for the Snowfield's trees
    img = noisy(0x7A5A3A, 5, "oakaged")
    save(grain(img, "oakaged", (150, 116, 80), (80, 56, 34), 18, horizontal=False), "oakaged")
    img = noisy(0x5E554C, 7, "bark")
    grain(img, "bark", (120, 110, 98), (40, 36, 32), 30, horizontal=False, alpha=0.7)
    save(img, "bark")
    save(noisy(0xF4F6FA, 3, "snow"), "snow")
    # The escalator: grooved treads, a comb plate with a yellow edge, steps' risers
    img = noisy(0x9EA2A6, 2, "tread")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 2):
        d.line([x, 0, x, S - 1], fill=H(0x6E7276))
    # The yellow demarcation along the step's nose and both sides (a tread maps uv 0..13 x 0..4: the nose is the
    # south edge, texture rows 5-7) so the edge of every step shows
    d.rectangle([0, 5, S - 1, 7], fill=H(0xE8C020))
    d.rectangle([0, 0, 1, 7], fill=H(0xE8C020))
    d.rectangle([24, 0, 25, 7], fill=H(0xE8C020))
    save(img, "tread")
    img = noisy(0x8E9296, 2, "riser")
    d = ImageDraw.Draw(img)
    for x in range(1, S, 2):
        d.line([x, 0, x, S - 1], fill=H(0x5E6266))
    save(img, "riser")
    img = noisy(0xB0B4B8, 2, "comb")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 3):
        d.line([x, 0, x, S - 1], fill=H(0x8A8E92))
    d.rectangle([0, S - 4, S - 1, S - 1], fill=H(0xE8C020))
    save(img, "comb")
    # The CRT: beige plastic, its shade, vents, keys, and the screens
    save(noisy(CRT, 3, "crt"), "crt")
    save(noisy(CRT_S, 3, "crtshade"), "crt-shade")
    img = noisy(CRT, 3, "crtvents")
    d = ImageDraw.Draw(img)
    for y in range(6, 26, 3):
        d.line([5, y, 26, y], fill=H(0x6E6656))
    save(img, "crt-vents")
    img = noisy(CRT_S, 2, "keys")
    d = ImageDraw.Draw(img)
    for row in range(5):
        for col in range(10):
            x, y = 1 + col * 3, 2 + row * 6
            d.rectangle([x, y, x + 1, y + 3], fill=H(0xE2DAC4))
    d.rectangle([8, 26, 22, 29], fill=H(0xE2DAC4))
    save(img, "keyboard")
    screens()
    signs()
    doors()
    posters()


def screen_base(key, c=CRT_G):
    """Dark glass, a curved reflection in one corner, scanlines."""
    img = noisy(c, 2, key, 32, 24)
    px = img.load()
    for y in range(24):
        for x in range(32):
            r, g, b, a = px[x, y]
            # vignette toward the corners of the tube
            dx, dy = (x - 15.5) / 16, (y - 11.5) / 12
            f = 1 - 0.35 * (dx * dx + dy * dy)
            if y % 2:
                f *= 0.9
            px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f), 255)
    return img


def screens():
    img = screen_base("scroff")
    d = ImageDraw.Draw(img)
    d.arc([2, 1, 40, 30], 190, 235, fill=(70, 82, 80, 255))
    save(img, "screen-off")
    # On: THE END in white 5-px pixel letters, a faint bloom round them
    img = screen_base("scron", 0x0C1010)
    glow = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
    centred(glow, "THE END", 8, (255, 255, 255, 255), F5, 1, gap=1)
    bloom = Image.new("RGBA", (32, 24), (0, 0, 0, 0))
    gp = glow.load()
    bp = bloom.load()
    for y in range(24):
        for x in range(32):
            if gp[x, y][3]:
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if 0 <= x + dx < 32 and 0 <= y + dy < 24:
                            bp[x + dx, y + dy] = (120, 140, 140, 120)
    img.alpha_composite(bloom)
    img.alpha_composite(glow)
    px = img.load()
    for y in range(1, 24, 2):
        for x in range(32):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * 0.88), clamp(g * 0.88), clamp(b * 0.88), 255)
    save(img, "screen-on")
    # Static: grey noise in bands
    rng = random.Random(seed_of("static"))
    img = Image.new("RGBA", (32, 24))
    px = img.load()
    for y in range(24):
        band = rng.uniform(0.6, 1.1)
        for x in range(32):
            v = clamp(rng.randint(30, 220) * band)
            px[x, y] = (v, v, clamp(v + 6), 255)
    save(img, "screen-static")
    # =) : the Partygoers' screen
    img = screen_base("scrparty", 0x0C1010)
    centred(img, "=)", 5, (255, 255, 255, 255), F5, 2, gap=1)
    save(img, "screen-party")
    # Dead: black, a faint crack across it, nothing behind
    img = screen_base("scrdead", 0x0A0C0C)
    d = ImageDraw.Draw(img)
    d.line([4, 3, 11, 9, 14, 8, 20, 15, 27, 20], fill=(54, 60, 60, 255))
    d.line([11, 9, 9, 15], fill=(44, 50, 50, 255))
    save(img, "screen-dead")


def neon(img, mask, col):
    """Neon tubes: the mask's pixels lit, with a soft halo round them."""
    w, h = img.size
    mp = mask.load()
    px = img.load()
    halo = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hp = halo.load()
    for y in range(h):
        for x in range(w):
            if mp[x, y][3]:
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        X, Y = x + dx, y + dy
                        if 0 <= X < w and 0 <= Y < h:
                            a = 90 if abs(dx) + abs(dy) <= 2 else 40
                            hp[X, Y] = (col[0], clamp(col[1] * 0.6), clamp(col[2] * 0.6), max(hp[X, Y][3], a))
    img.alpha_composite(halo)
    for y in range(h):
        for x in range(w):
            if mp[x, y][3]:
                px[x, y] = (255, clamp(col[1] + 150), clamp(col[2] + 130), 255)
    return img


def signs():
    save(noisy(0xFF3A28, 8, "neonred"), "neonred")
    save(noisy(0x5A1E1A, 4, "neondead"), "neondead")
    # INFORMATION: white on navy
    img = noisy(0x1E2A5A, 2, "infosign", 70, 25)
    centred(img, "INFORMATION", 9, (240, 240, 236, 255), F5, 1, gap=1)
    ImageDraw.Draw(img).rectangle([0, 0, 69, 24], outline=(200, 200, 196, 255))
    # (70 x 25 has no whole-number enlargement on the atlas grid: padded, and the sign's faces show only the picture)
    img, INFOSIGN_UV[:] = T.pad_to_atlas_grid(img)
    save(img, "infosign")
    # EMPLOYEES ONLY plate
    img = noisy(0xB9BDC0, 2, "staffplate", 60, 18)
    centred(img, "EMPLOYEES", 1, (30, 30, 30, 255), F5, 1, gap=1)
    centred(img, "ONLY", 10, (30, 30, 30, 255), F5, 1, gap=1)
    img, STAFFPLATE_UV[:] = T.pad_to_atlas_grid(img)
    save(img, "staffplate")
    # Vent: off-white sheet metal, and the dark behind
    save(noisy(0xD6D4CC, 2, "vent"), "vent")
    save(noisy(0x101010, 2, "ventdark"), "ventdark")
    save(noisy(0x16181A, 3, "shopdark"), "shopdark")
    save(noisy(0x4A4A48, 3, "duct"), "duct")
    # The doorway's membrane: a shimmer you can almost see through (three looks, chosen per block)
    for k in range(3):
        img = Image.new("RGBA", (S, S))
        px = img.load()
        rng = random.Random(seed_of(f"membrane{k}"))
        ph = rng.uniform(0, 6.28)
        for y in range(S):
            for x in range(S):
                v = math.sin(2 * math.pi * (x / S * 2 + 0.3 * math.sin(2 * math.pi * y / S + ph)) + ph)
                a = clamp(40 + 26 * v)
                c = clamp(226 + 20 * v)
                px[x, y] = (c, c, clamp(c + 10), a)
        save(img, f"membrane{k}")
    # Chain links
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 6):
        d.rectangle([12, y, 19, y + 4], outline=(150, 152, 150, 255))
    save(img, "chain")
    # The clock: a round cream dial in a black case (the corners are case, to sit on the round 3D body), a steel rim,
    # twelve ticks (bold at 12, 3, 6, 9), and the hands stopped at five to midnight (a minute to midnight would lay one
    # hand over the other at this size): the short broad hour hand just left of twelve, the long minute hand on 55,
    # the thin red seconds hand dead at 40
    K, c = 4, 15.5 * 4 + 2
    big = Image.new("RGBA", (S * K, S * K), H(0x151515))
    d = ImageDraw.Draw(big)
    d.ellipse([c - 62, c - 62, c + 62, c + 62], fill=(118, 120, 124, 255))      # the steel rim
    d.ellipse([c - 55, c - 55, c + 55, c + 55], fill=(36, 36, 38, 255))         # its inner lip
    d.ellipse([c - 51, c - 51, c + 51, c + 51], fill=(244, 240, 226, 255))      # the dial

    def ray(deg, r1, r2, width, colour):
        a = math.radians(deg)
        d.line([c + r1 * math.sin(a), c - r1 * math.cos(a), c + r2 * math.sin(a), c - r2 * math.cos(a)], fill=colour, width=width)
    for k in range(12):
        ray(k * 30, 36 if k % 3 == 0 else 41, 49, 7 if k % 3 == 0 else 4, (24, 24, 26, 255))
    def hand(deg, back, length, width, colour):  # a tapered hand: broad at the pin, pointed at its tip
        a = math.radians(deg)
        ux, uy, px_, py_ = math.sin(a), -math.cos(a), math.cos(a), math.sin(a)
        d.polygon([(c - back * ux + width * px_, c - back * uy + width * py_), (c + length * ux, c + length * uy),
                   (c - back * ux - width * px_, c - back * uy - width * py_)], fill=colour)
    hand(-2.5, 8, 27, 7, (20, 20, 22, 255))    # hour: short and broad, just left of twelve
    hand(-30, 10, 48, 3.5, (20, 20, 22, 255))  # minute: long and slim, on 55
    ray(240, -12, 44, 2, (190, 30, 30, 255))     # seconds
    d.ellipse([c - 6, c - 6, c + 6, c + 6], fill=(184, 150, 62, 255))
    img = big.resize((S, S), Image.LANCZOS)
    rng = random.Random(seed_of("clockface"))
    px = img.load()
    for y in range(S):  # a little grime on the dial
        for x in range(S):
            r, g, b, a = px[x, y]
            k = rng.randint(-5, 3)
            px[x, y] = (clamp(r + k), clamp(g + k), clamp(b + k), 255)
    save(img, "clockface")


def door_tex(key, base, n=3, vertical=False):
    img = noisy(base, n, key)
    if vertical:
        grain(img, key, (214, 170, 110), (160, 112, 56), 18, horizontal=False)
    return img


def doors():
    # The EXIT door: grey steel, a faint panel line; the staff door: maple veneer
    img = door_tex("exitdoor", 0x8E9196)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=H(0x7A7D82))
    save(img, "exitdoor")
    # Wired glass, dark behind
    img = noisy(0x2A3236, 3, "wireglass")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 5):
        d.line([k, 0, k, S - 1], fill=H(0x6A7276))
        d.line([0, k, S - 1, k], fill=H(0x6A7276))
    d.line([3, S - 5, S - 6, 4], fill=(150, 160, 164, 255))
    save(img, "wireglass")
    save(door_tex("staffdoor", 0xC8955A, 3, vertical=True), "staffdoor")


def posters():
    # Yellow: THE END in rows of black bold letters, like the render (3:4 sheet)
    img = noisy(P_YEL, 3, "poster-yellow", 48, 64)
    centred(img, "THE END", 2, (16, 16, 16, 255), F5, 1, bold=True, gap=1)
    ImageDraw.Draw(img).rectangle([3, 11, 44, 12], fill=(16, 16, 16, 255))
    for k in range(5):
        centred(img, "THE END", 16 + k * 9, (16, 16, 16, 255), F5, 1, gap=1)
    ImageDraw.Draw(img).rectangle([0, 0, 47, 63], outline=(214, 200, 40, 255))
    save(img, "poster-yellow")
    # Pink and green cards: THE END, three lines of scribble
    for name, c in (("pink", P_PINK), ("green", P_GREEN)):
        img = noisy(c, 3, "poster-" + name, 24, 32)
        centred(img, "THE END", 3, (30, 30, 30, 255), F3, 1, gap=1)
        rng = random.Random(seed_of("scrib" + name))
        d = ImageDraw.Draw(img)
        for row in range(3):
            y = 13 + row * 6
            pts = [(3 + k * 2, y + rng.choice((0, 0, 1, -1))) for k in range(rng.randint(6, 9))]
            d.line(pts, fill=(60, 50, 70, 255))
        save(img, f"poster-{name}")
    # The notice: FOR SALE, ALL FIXTURES, FURNITURE & EQUIPMENT
    img = noisy(0xF6F6F0, 2, "poster-notice", 36, 48)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 35, 10], fill=(200, 30, 30, 255))
    centred(img, "FOR SALE", 2, (255, 255, 255, 255), F3, 1, gap=1)
    centred(img, "THE END", 14, (20, 20, 20, 255), F3, 1, bold=True, gap=1)
    for k, line in enumerate(("ALL", "FIXTURES", "FURNITURE", "& EQUIPMENT")):
        centred(img, line, 22 + k * 6, (20, 20, 20, 255), F3, 1, gap=1)
    d.rectangle([0, 0, 35, 47], outline=(200, 200, 194, 255))
    save(T.fit_atlas_grid(img), "poster-notice")
    # The bookstore's door poster: THE END IS NEAR
    img = noisy(P_YEL, 3, "poster-near", 36, 44)
    centred(img, "THE END", 6, (16, 16, 16, 255), F5, 1, bold=True, gap=1)
    centred(img, "IS", 17, (16, 16, 16, 255), F5, 1, bold=True, gap=1)
    centred(img, "NEAR", 28, (16, 16, 16, 255), F5, 1, bold=True, gap=1)
    save(T.fit_atlas_grid(img), "poster-near")
    # Window posters: ALL FIXTURES FOR SALE (yellow), CLOSING (pink)
    img = noisy(P_YEL, 3, "poster-fixtures", 40, 44)
    centred(img, "ALL", 3, (16, 16, 16, 255), F5, 1, bold=True, gap=1)
    centred(img, "FIXTURES", 13, (16, 16, 16, 255), F3, 1, gap=1)
    centred(img, "FURNITURE", 20, (16, 16, 16, 255), F3, 1, gap=1)
    centred(img, "& EQUIPMENT", 27, (16, 16, 16, 255), F3, 1, gap=1)
    centred(img, "FOR SALE", 35, (190, 20, 20, 255), F3, 1, bold=True, gap=1)
    save(T.fit_atlas_grid(img), "poster-fixtures")
    img = noisy(P_PINK, 3, "poster-closing", 28, 36)
    centred(img, "STORE", 4, (30, 20, 40, 255), F3, 1, bold=True, gap=1)
    centred(img, "CLOSING", 12, (30, 20, 40, 255), F3, 1, bold=True, gap=1)
    centred(img, "THE END", 22, (30, 20, 40, 255), F3, 1, gap=1)
    save(T.fit_atlas_grid(img), "poster-closing")
    # A price sticker and a stock label
    img = noisy(P_YEL, 2, "sticker")
    centred(img, "50", 9, (20, 20, 20, 255), F5, 2, gap=1)
    save(img, "sticker")
    img = noisy(0xF6F6F0, 2, "stocklabel", 32, 24)
    centred(img, "FIXTURES", 3, (20, 20, 20, 255), F3, 1, gap=1)
    d = ImageDraw.Draw(img)
    for y in (11, 15, 19):
        d.line([4, y, 27, y], fill=(120, 120, 120, 255))
    save(img, "stocklabel")


def item_textures():
    # The catalogue card: cream, a red top rule, typed lines, the rod hole
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 7, 29, 25], fill=H(0xF1E8CF), outline=H(0xCFC4A8))
    d.line([3, 10, 28, 10], fill=H(0xC0282A))
    for y in (13, 16, 19):
        d.line([5, y, 5 + (20 if y != 19 else 13), y], fill=H(0x5A5248))
    d.line([5, 22, 12, 22], fill=H(0x2A3A8A))  # someone's underline, in biro
    d.line([5, 23, 12, 23], fill=H(0x2A3A8A))
    d.ellipse([14, 22, 17, 25], fill=(0, 0, 0, 0), outline=H(0xCFC4A8))
    save_item(img, "cataloguecard")
    # Memory Juice: cloudy amber glass, a cork
    img = noisy(0xC88A2E, 8, "juiceglass")
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            f = 1.15 if 6 <= x <= 9 else 1
            px[x, y] = (clamp(r * f), clamp(g * f), clamp(b * f), 255)
    save_item(img, "memoryjuice-glass")
    save_item(noisy(0xA88A60, 10, "cork"), "memoryjuice-cork")


# ======================= Shapes and block types =======================

def shp(name, elements):
    keys = set()
    for e in elements:
        for face in e["faces"].values():
            keys.add(face["texture"][1:])
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in sorted(keys)}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", "block", "end", name + ".json"), data)
    SHAPES.append(name)
    return "block/end/" + name


def blk(code, data, comment):
    write_json(os.path.join(ASSETS, "blocktypes", "end", code + ".json"), dict({"code": code}, **data), comment)
    CODES.append(code)


def name(pattern, english):
    LANG["block-" + pattern] = english


def faces_box(nm, frm, to, tex_by_face, glow_by_face=None, uv=None):
    """A box with a texture per face (only the faces given)."""
    el = bx(nm, frm, to, "x", faces=tuple(tex_by_face))
    for f, t in tex_by_face.items():
        el["faces"][f]["texture"] = "#" + t
        if uv:
            el["faces"][f]["uv"] = list(uv)
        if glow_by_face and f in glow_by_face:
            el["faces"][f]["glow"] = glow_by_face[f]
    return el


def cube_el(side, up=None, down=None):
    t = {f: side for f in ("north", "east", "south", "west")}
    t["up"] = up or side
    t["down"] = down or side
    return faces_box("Wall", (0, 0, 0), (16, 16, 16), t)


def rot(el, rx=0, ry=0, rz=0, origin=None):
    el = json.loads(json.dumps(el))
    (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
    el["rotationOrigin"] = list(origin) if origin else [(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2]
    for k, v in (("rotationX", rx), ("rotationY", ry), ("rotationZ", rz)):
        if v:
            el[k] = round(v, 3)
    return el


def rot_all(els, rx=0, ry=0, rz=0, origin=(8, 8, 8)):
    return [rot(e, rx, ry, rz, origin) for e in els]


def move(els, dx=0, dy=0, dz=0):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["from"] = [e["from"][0] + dx, e["from"][1] + dy, e["from"][2] + dz]
        e["to"] = [e["to"][0] + dx, e["to"][1] + dy, e["to"][2] + dz]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [o[0] + dx, o[1] + dy, o[2] + dz]
        out.append(e)
    return out


def by_side(pattern, path):
    """shapeByType entries for the four sides of one shape: pattern like '*-books-lower'."""
    return {f"{pattern}-{s}": {"base": path, "rotateY": ROTATE[s]} for s in SIDES}


def boxes_by_side(pattern, boxes):
    """Collision boxes for the four sides; `boxes` a list of (x1, y1, z1, x2, y2, z2) for the north-facing model."""
    return {f"{pattern}-{s}": [cuboid(b, s) for b in boxes] for s in SIDES}


def drops(*items):
    out = []
    for code, avg, var in items:
        kind = "item"
        if code.startswith("block:"):
            kind, code = "block", code[6:]
        out.append({"type": kind, "code": code, "quantity": {"avg": avg, "var": var}})
    return out


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


OPEN = {"sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0}


def inv(first):
    return {"general": [first], "decorative": [first]}


# ---------------- Text in boxes: letters, neon ----------------

def stroke_boxes(strokes, diags, ox, oy, s, z1, z2, tex, glow=0, mirror=True, nm="L"):
    """Strokes in viewer space (x right, y up, in units of s) on a face seen from the north (the viewer's right is
    -x), or from the south with mirror=False. Diagonals are (xa, ya, xb, yb, width)."""
    els = []
    sign = -1 if mirror else 1
    for k, (x1, y1, x2, y2) in enumerate(strokes):
        a, b = ox + sign * x1 * s, ox + sign * x2 * s
        els.append(bx(f"{nm}{k}", (min(a, b), oy + y1 * s, z1), (max(a, b), oy + y2 * s, z2), tex, glow=glow))
    for k, (xa, ya, xb, yb, w) in enumerate(diags):
        dX, dY = sign * (xb - xa) * s, (yb - ya) * s
        L = math.hypot(dX, dY)
        cx, cy = ox + sign * (xa + xb) / 2 * s, oy + (ya + yb) / 2 * s
        phi = math.degrees(math.atan2(-dX, dY))
        el = bx(f"{nm}d{k}", (cx - w * s / 2, cy - L / 2, z1), (cx + w * s / 2, cy + L / 2, z2), tex, glow=glow)
        els.append(rot(el, rz=phi, origin=(cx, cy, (z1 + z2) / 2)))
    return els


# Bronze letters, 10 tall, 2-wide strokes: (width, strokes, diagonals) in viewer space
LETTERS = {
    "t": (8, [(0, 8, 8, 10), (3, 0, 5, 8)], []),
    "h": (7, [(0, 0, 2, 10), (5, 0, 7, 10), (2, 4, 5, 6)], []),
    "e": (6, [(0, 0, 2, 10), (2, 8, 6, 10), (2, 4, 5.2, 6), (2, 0, 6, 2)], []),
    "n": (7.5, [(0, 0, 2, 10), (5.5, 0, 7.5, 10)], [(1.2, 9.6, 6.3, 0.4, 2)]),
    "d": (7, [(0, 0, 2, 10), (2, 8, 5.2, 10), (2, 0, 5.2, 2), (5, 1.6, 7, 8.4)], []),
    "i": (2, [(0, 0, 2, 10)], []),
    "s": (6.5, [(1.2, 8, 6.5, 10), (0, 5.2, 2, 8.8), (1.2, 4, 5.3, 6), (4.5, 1.2, 6.5, 4.8), (0, 0, 5.3, 2)], []),
    "a": (8, [(2.4, 3.2, 5.6, 5)], [(0.9, 0, 4, 9.6, 2), (7.1, 0, 4, 9.6, 2)]),
    "r": (7, [(0, 0, 2, 10), (2, 8, 5.2, 10), (5, 5.6, 7, 8.4), (2, 4.2, 5.2, 6.2)], [(4, 4.6, 6.5, 0.2, 2)]),
    "blank": (0, [], []),
}

# Neon EXIT, 3.4 tall, 0.7-wide tubes
NEON = {
    "E": (2.2, [(0, 0, 0.7, 3.4), (0.7, 2.7, 2.2, 3.4), (0.7, 1.35, 1.9, 2.05), (0.7, 0, 2.2, 0.7)], []),
    "X": (2.4, [], [(0.3, 3.4, 2.1, 0, 0.7), (2.1, 3.4, 0.3, 0, 0.7)]),
    "I": (0.7, [(0, 0, 0.7, 3.4)], []),
    "T": (2.4, [(0, 2.7, 2.4, 3.4), (0.85, 0, 1.55, 2.7)], []),
}


def neon_word(cx, cy, z1, z2, tex, glow, mirror=True):
    gap = 0.75
    width = sum(NEON[c][0] for c in "EXIT") + gap * 3
    x = -width / 2
    els = []
    for c in "EXIT":
        w, strokes, diags = NEON[c]
        els += stroke_boxes([(a + x, b, cc + x, d) for a, b, cc, d in strokes],
                            [(a + x, b, cc + x, d, ww) for a, b, cc, d, ww in diags],
                            cx, cy - 1.7, 1, z1, z2, tex, glow, mirror, nm="N" + c + ("" if mirror else "s"))
        x += w + gap
    return els


# ---------------- Backings: wall faces that carry a decoration ----------------

BACKINGS = {
    "lower": ("wall-lower", None, None), "upper": ("wall-upper", None, None), "band": ("wall-band", None, None),
    "block": ("wall-block", None, None), "sage": ("column-sage", None, None), "slate": ("column-slate", None, None),
    "soffit": ("soffit-face", "plenum", "soffit-under"), "wall": ("wall-band", None, None),
    "concrete": ("concretewall", None, None),
}


def backed_block(code, kinds, backings, comment, material="Stone", sounds=STONE, extra=None, light=None,
                 none_box=None, transparent=False, kind_group="kind", backing_group="backing", backing_first=False):
    """A decoration on the north face of a wall block (the block renders the wall behind it), for each backing; with
    the backing "none", the decoration alone against the south face of an air block. `kinds` maps a kind (None for
    no kind group) to (boxes in front of a wall, boxes for "none"). A single backing has no variant group of its own
    (backing_group None); backing_first puts its group before the kind's."""
    groups = []
    kg = [{"code": kind_group, "states": list(kinds)}] if list(kinds) != [None] else []
    bg = [{"code": backing_group, "states": list(backings)}] if backing_group else []
    groups = (bg + kg) if backing_first else (kg + bg)
    groups.append({"code": "side", "states": SIDES})
    shapes, opaque, absorb, coll, sel = {}, {}, {}, {}, {}
    for kind, (front, alone) in kinds.items():
        for b in backings:
            parts = [b] if backing_group else []
            if kind:
                parts = (parts + [kind]) if backing_first else ([kind] + parts)
            pat = "-".join(["*"] + parts)
            if b == "none":
                els = alone
            else:
                side, up, down = BACKINGS[b]
                els = [cube_el(side, up, down)] + front
            path = shp("-".join([code] + ([kind] if kind else []) + [b]), els)
            shapes.update(by_side(pat, path))
            if b == "none":
                opaque[pat + "-*"] = {"all": False}
                absorb[pat + "-*"] = 0
                coll[pat + "-*"] = None
                if none_box:
                    for s in SIDES:
                        sel[f"{pat}-{s}"] = cuboid(none_box, s)
    data = {"variantgroups": groups, "creativeinventory": inv("*-north"), "blockmaterial": material, "drawtype": "json",
            "shapeByType": shapes, "resistance": 4, "sounds": sounds}
    if opaque:
        data["sideopaqueByType"] = dict(opaque, **{"*": {"all": True}})
        data["sidesolidByType"] = dict(opaque, **{"*": {"all": True}})
        data["lightAbsorptionByType"] = dict(absorb, **{"*": 0 if light else 99})
        data["collisionboxByType"] = coll
        if sel:
            data["selectionboxByType"] = sel
    else:
        data["lightAbsorption"] = 0 if light else 99
    if light:
        data.update(light)
    if transparent:
        data["renderpass"] = "Transparent"
    if extra:
        data.update(extra)
    if "lightAbsorptionByType" in data:
        data.pop("lightAbsorption", None)
    blk(code, data, comment)
    return data


# ======================= Structure (cubes) =======================

def cube_kinds(code, kinds, comment, material="Stone", sounds=STONE, extra=None):
    """A cube block with one look per kind: kinds maps a kind to (English, {face or 'all': texture spec})."""
    data = {"variantgroups": [{"code": "kind", "states": list(kinds)}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "texturesByType": {},
            "lightAbsorption": 99, "resistance": 8, "sounds": sounds}
    for k, (eng, tex) in kinds.items():
        data["texturesByType"][f"*-{k}"] = tex
        name(f"{code}-{k}", eng)
    if extra:
        data.update(extra)
    blk(code, data, comment)


def turned(t):
    return {"base": f"block/end/{t}", "alternates": [{"base": f"block/end/{t}", "rotation": r} for r in (90, 180, 270)]}


def flat_(t):
    return {"base": f"block/end/{t}"}


CARPET_SOUNDS = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}


def structure():
    cube_kinds("end-carpet", {
        "plain": ("Library Carpet", {"all": turned("carpet-plain")}),
        "dusty": ("Library Carpet", {"all": turned("carpet-dusty")}),
        "worn": ("Library Carpet", {"all": turned("carpet-worn")}),
        "stained": ("Library Carpet", {"all": turned("carpet-stained")}),
        "snowy": ("Library Carpet under Snow", {"up": turned("carpet-snowy"), "horizontals": flat_("carpet-snowyside"), "down": flat_("carpet-plain")}),
    }, "The End: grey-green low-pile carpet; dusty, worn flat, stained, or half under the Snowfield's powder snow",
        material="Cloth", sounds=CARPET_SOUNDS,
        extra={"resistance": 1.5, "behaviors": [{"name": "BackroomsStrippable", "properties": {
            "result": "end-carpet-worn", "item": "carpetfibre", "variant": "kind", "allowed": ["plain", "dusty", "stained"]}}]})
    cube_kinds("end-runway", {"plain": ("Patterned Carpet", {"all": turned("runway")})},
               "The End: the navy patterned carpet of the racetrack aisle", material="Cloth", sounds=CARPET_SOUNDS,
               extra={"resistance": 1.5, "behaviors": [{"name": "BackroomsStrippable", "properties": {
                   "result": "end-carpet-worn", "item": "carpetfibre"}}]})
    cube_kinds("end-concrete", {
        "plain": ("Stockroom Concrete", {"all": turned("concrete")}),
        "line-ns": ("Stockroom Concrete", {"up": flat_("concrete-linens"), "horizontals": flat_("concrete"), "down": flat_("concrete")}),
        "line-we": ("Stockroom Concrete", {"up": flat_("concrete-linewe"), "horizontals": flat_("concrete"), "down": flat_("concrete")}),
    }, "The End: the stockrooms' sealed concrete floor, with a yellow safety line either way")
    cube_kinds("end-wall", {
        "base": ("Painted Wall", {"all": flat_("wall-base")}),
        "lower": ("Painted Wall", {"all": flat_("wall-lower")}),
        "ghost": ("Painted Wall", {"all": flat_("wall-ghost")}),
        "cracked": ("Cracked Wall", {"all": flat_("wall-cracked")}),
        "band": ("Painted Wall", {"all": flat_("wall-band")}),
        "upper": ("Painted Wall", {"all": flat_("wall-upper")}),
        "uppercracked": ("Cracked Wall", {"all": flat_("wall-uppercracked")}),
        "block": ("Painted Block Wall", {"all": flat_("wall-block")}),
    }, "The End: the wall stack (rel 1 base with its vinyl cove, 2 off-white, 3 the yellow band, 4+ yellow-cream); "
       "ghost = where a sign hung; block = the stockrooms' painted concrete block")
    cube_kinds("end-column", {
        "sage": ("Column", {"all": flat_("column-sage")}),
        "slate": ("Column", {"all": flat_("column-slate")}),
        "slat": ("Slatwall Column", {"all": flat_("slatwall")}),
    }, "The End: square columns painted sage or slate, clad in maple slatwall to head height (slat at rel 1-2)",
        extra={"soundsByType": {"*-slat": WOOD, "*": STONE}})
    cube_kinds("end-ceiling", {
        "plain": ("Ceiling Tile", {"all": flat_("ceiling-plain")}),
        "stained": ("Ceiling Tile", {"all": flat_("ceiling-stained")}),
        "missing": ("Missing Ceiling Tiles", {"all": flat_("ceiling-missing")}),
    }, "The End: 2x2 acoustic ceiling tiles; stained; missing, the black plenum showing between the T-bars",
        material="Plant", sounds={"walk": "game:walk/stone", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
        extra={"resistance": 0.6})

    # Troffers: on (emits), lit (looks on, emits nothing, as Level 0 does for speed), off, flicker
    blk("end-troffer", {
        "variantgroups": [{"code": "state", "states": ["on", "lit", "off", "flicker"]}],
        "creativeinventory": INV_ALL, "blockmaterial": "Glass", "drawtype": "cube",
        "texturesByType": {"*-off": {"all": flat_("troffer-off"), "up": flat_("plenum")},
                           "*": {"all": flat_("troffer-on"), "up": flat_("plenum")}},
        "lightHsvByType": {"*-on": [8, 2, 14]},
        "vertexFlagsByType": {"*-on": {"glowLevel": 220}, "*-lit": {"glowLevel": 220}, "*-flicker": {"glowLevel": 220}},
        "entityClassByType": {"*-flicker": "BackroomsFlicker"},
        "attributesByType": {"*-flicker": {"offBlock": "backrooms:end-troffer-off"}},
        "dropsByType": {"*-off": drops(("glassshard", 1.5, 0.5), ("metalbracket", 0.12, 0), ("scrapwire", 0.3, 0)),
                        "*-flicker": [{"type": "block", "code": "end-troffer-off"}],
                        "*-lit": [{"type": "block", "code": "end-troffer-on"}]},
        "lightAbsorption": 0, "resistance": 0.8, "sounds": GLASS,
    }, "The End: 2x4 fluorescent troffers in the acoustic tile; about 1 in 3 emits (on), the rest only glow (lit)")
    name("end-troffer-*", "Fluorescent Light")

    blk("end-soffit", {
        "variantgroups": [{"code": "kind", "states": ["plain", "edge-north", "edge-east", "edge-south", "edge-west"]}],
        "creativeinventory": {"general": ["*-plain"], "construction": ["*-plain"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "texturesByType": dict({"*-plain": {"all": flat_("soffit-face"), "up": flat_("plenum"), "down": flat_("soffit-under")}},
                               **{f"*-edge-{s}": {"all": flat_("wall-upper"), s: flat_("soffit-face"), "up": flat_("plenum"),
                                                  "down": flat_("soffit-under")} for s in SIDES}),
        "lightAbsorption": 99, "resistance": 8, "sounds": STONE,
    }, "The End: the lowered bulkhead at rel 4 over a service desk; its edge face (the side named) carries the band")
    name("end-soffit-*", "Soffit")

    blk("end-deck", {
        "variantgroups": [{"code": "kind", "states": ["plain", "troffer"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "texturesByType": {"*-plain": {"up": turned("carpet-plain"), "horizontals": flat_("deck-fascia"), "down": flat_("ceiling-plain")},
                           "*-troffer": {"up": turned("carpet-plain"), "horizontals": flat_("deck-fascia"), "down": flat_("troffer-on")}},
        "lightHsvByType": {"*-troffer": [8, 2, 13]}, "lightAbsorptionByType": {"*-troffer": 0, "*": 99},
        "vertexFlagsByType": {"*-troffer": {"glowLevel": 120}},
        "resistance": 8, "sounds": CARPET_SOUNDS,
    }, "The End: the atrium's mezzanine deck at rel 6: carpet on top, a white fascia, ceiling tiles (or a troffer) beneath")
    name("end-deck-*", "Mezzanine Floor")


INV_ALL = {"general": ["*"], "decorative": ["*"]}


# ======================= Shelving =======================

def lip(nm, x1, x2, ytop, zfront, north=True):
    """The grey price channel along a shelf's front edge."""
    if north:
        return bx(nm, (x1, ytop - 1.3, zfront - 0.3), (x2, ytop + 0.2, zfront), "pricechannel")
    return bx(nm, (x1, ytop - 1.3, zfront), (x2, ytop + 0.2, zfront + 0.3), "pricechannel")


def books(seed, y, zfront, x_lo=2.0, x_hi=14.0, count=None, depth=3.4, max_h=4.4, north=True):
    """A few books standing on a shelf, spines out, the last one leaning on its neighbour."""
    rng = random.Random(seed)
    n = count or rng.randint(3, 6)
    els = []
    x = rng.uniform(x_lo, x_hi - 6)
    for k in range(n):
        w, h = rng.uniform(0.9, 1.6), rng.uniform(max_h - 1.1, max_h)
        tex = f"book{rng.randrange(6)}"
        z1, z2 = (zfront + 0.3, zfront + 0.3 + depth) if north else (zfront - 0.3 - depth, zfront - 0.3)
        b = faces_box(f"Book{k}", (x, y, z1), (x + w, y + h, z2),
                      {"north": tex, "south": tex, "east": tex, "west": tex, "up": "pages", "down": tex})
        if k == n - 1 and x + w + 2 < x_hi:
            b = rot(b, rz=-20, origin=(x + w, y, (z1 + z2) / 2))
            b = move([b], dx=0.7)[0]
        els.append(b)
        x += w + rng.uniform(0, 0.15)
        if x > x_hi - 2:
            break
    return els


def gondola(part):
    """Double-faced gondola shelving, 2 tall, the run going east-west; shelves face north and south."""
    if part == "lower":
        els = [bx("SideW", (0, 0, 0), (1.5, 16, 16), "maple"), bx("SideE", (14.5, 0, 0), (16, 16, 16), "maple"),
               bx("Kick", (1.5, 0, 1), (14.5, 2.5, 15), "kick"), bx("Deck", (1.5, 2.5, 0.5), (14.5, 3.5, 15.5), "maple"),
               faces_box("Spine", (1.5, 3.5, 7), (14.5, 16, 9), {"north": "slatwall", "south": "slatwall", "up": "maple"})]
        for k, y in enumerate((8, 13.5)):
            els += [bx(f"ShelfN{k}", (1.5, y, 1.5), (14.5, y + 1, 7), "maple"), lip(f"LipN{k}", 1.5, 14.5, y + 1, 1.5),
                    bx(f"ShelfS{k}", (1.5, y, 9), (14.5, y + 1, 14.5), "maple"), lip(f"LipS{k}", 1.5, 14.5, y + 1, 14.5, False)]
        els += [lip("LipDN", 1.5, 14.5, 3.5, 0.5), lip("LipDS", 1.5, 14.5, 3.5, 15.5, False)]
    else:
        els = [bx("SideW", (0, 0, 1), (1.5, 13.5, 15), "maple"), bx("SideE", (14.5, 0, 1), (16, 13.5, 15), "maple"),
               faces_box("Spine", (1.5, 0, 7), (14.5, 13.5, 9), {"north": "slatwall", "south": "slatwall"}),
               bx("Cornice", (0, 13.5, 0.5), (16, 15, 15.5), "maple-dark"), bx("Cap", (0.5, 15, 1), (15.5, 15.6, 15), "maple")]
        for k, y in enumerate((3, 8.5)):
            els += [bx(f"ShelfN{k}", (1.5, y, 2.5), (14.5, y + 1, 7), "maple"), lip(f"LipN{k}", 1.5, 14.5, y + 1, 2.5),
                    bx(f"ShelfS{k}", (1.5, y, 9), (14.5, y + 1, 13.5), "maple"), lip(f"LipS{k}", 1.5, 14.5, y + 1, 13.5, False)]
    return els


def dust_and_web(part):
    els = []
    tops = ((3.5, 0.5, 15.5), (9, 1.5, 14.5), (14.5, 1.5, 14.5)) if part == "lower" else ((4, 2.5, 13.5), (9.5, 2.5, 13.5))
    for k, (y, z1, z2) in enumerate(tops):
        els.append(faces_box(f"Dust{k}", (1.5, y, z1), (14.5, y + 0.12, 7 if z1 < 7 else z2), {"up": "dust"}))
        els.append(faces_box(f"DustS{k}", (1.5, y, 9), (14.5, y + 0.12, z2), {"up": "dust"}))
    if part == "lower":
        els.append(faces_box("Web", (10, 9.1, 1.6), (14.5, 13.5, 1.6), {"north": "cobweb", "south": "cobweb"}, uv=(16, 0, 0, 16)))
    else:
        els.append(faces_box("Web", (1.5, 9.6, 2.6), (6, 13.5, 2.6), {"north": "cobweb", "south": "cobweb"}))
    return els


def shelving():
    # ---- end-shelf: kind (empty, books, dusty, endpanel, leaning) x part (lower, upper) x side
    shapes = {}
    for kind in ("empty", "books", "dusty", "endpanel", "leaning"):
        for part in ("lower", "upper"):
            els = gondola(part)
            if kind == "books":
                els += books(seed_of(f"shelfbooks{part}"), 9 if part == "lower" else 4, 1.5 if part == "lower" else 2.5,
                             max_h=4.4 if part == "lower" else 4.3)
            elif kind == "dusty":
                els += dust_and_web(part)
            elif kind == "endpanel":
                els = [turn(e, 1) for e in els]
                h = 16 if part == "lower" else 13.5
                els = [e for e in els if not (e["name"] == "SideW")]  # the panel replaces the turned side there
                els += [faces_box("EndPanel", (0.6, 0, 0), (15.4, h, 1.5), {"north": "slatwall", "up": "maple", "east": "maple", "west": "maple"}),
                        bx("EdgeW", (0, 0, -0.2), (0.6, h, 1.6), "maple-dark"), bx("EdgeE", (15.4, 0, -0.2), (16, h, 1.6), "maple-dark")]
                if part == "lower":
                    els.append(bx("EndKick", (0.6, 0, -0.1), (15.4, 2.5, 0.2), "kick"))
            elif kind == "leaning":
                els = rot_all(els, rx=-8, origin=(8, 0 if part == "lower" else -16, 0))
            path = shp(f"end-shelf-{kind}-{part}", els)
            shapes.update(by_side(f"*-{kind}-{part}", path))
    blk("end-shelf", {
        "variantgroups": [{"code": "kind", "states": ["empty", "books", "dusty", "endpanel", "leaning"]},
                          {"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-empty-lower-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 1.5, "sounds": WOOD,
        "classByType": {"*-leaning-*": "BackroomsFragileShelf"}, "resistanceByType": {"*-leaning-*": 0.3, "*": 1.5},
        "dropsByType": {"*-books-*": drops((STICK, 2, 0), (PLANK, 0.25, 0), ("game:book-normal-darkgreen", 0.3, 0),
                                           ("game:book-aged-brickred", 0.1, 0), (PAPER, 0.4, 0.3)),
                        "*-leaning-*": [], "*": drops((STICK, 2, 0), (PLANK, 0.25, 0))},
    }, "The End: double-faced gondola shelving, 2 tall (lower, upper), the run going east-west for side north; "
       "endpanel: the row's end, its slatwall panel facing the side named; leaning: tipped 8 degrees, it falls at a touch")
    for kind, eng in (("empty", "Empty Shelving"), ("books", "Shelving with a Few Books"), ("dusty", "Empty Shelving"),
                      ("endpanel", "Empty Shelving"), ("leaning", "Leaning Shelving")):
        name(f"end-shelf-{kind}-*", eng)

    # ---- end-tallshelf: single-faced library stack, 4 tall, against a back panel; and end-wallshelf, 2 tall
    def library(part, kind, seed):
        front = 5.0
        top = 12.5 if part in ("crown", "upper") else 16
        els = [bx("SideW", (0, 0, front), (1.5, top, 16), "maple"), bx("SideE", (14.5, 0, front), (16, top, 16), "maple"),
               faces_box("Back", (1.5, 0, 14.5), (14.5, top, 16), {"north": "maple-vertical", "south": "maple", "up": "maple"})]
        if part in ("base", "lower"):
            shelves = [(9, 10)]
            els += [bx("Kick", (1.5, 0, front + 0.6), (14.5, 2.5, 14.5), "kick"), bx("Deck", (1.5, 2.5, front), (14.5, 3.5, 14.5), "maple"),
                    lip("LipD", 1.5, 14.5, 3.5, front)]
            book_y = 3.5
        elif part in ("mid1", "mid2"):
            shelves = [(0.5, 1.5), (8, 9)]
            book_y = 9 if part == "mid1" else 1.5
        else:
            shelves = [(0.5, 1.5)]
            book_y = 1.5
            els += [bx("Cap", (0, 11, front - 0.5), (16, 12.5, 16), "maple"),
                    bx("Moulding", (-0.2, 12.5, front - 1.5), (16.2, 14, 16), "maple-dark"),
                    bx("Crown", (-0.4, 14, front - 2), (16.4, 16, 16), "maple")]
            if kind == "rail":
                els += [bx("Rail", (0, 13.5, front - 4.5), (16, 14.5, front - 3.5), "brass"),
                        bx("BracketW", (2.6, 13.7, front - 3.5), (3.4, 14.3, front - 2), "brass"),
                        bx("BracketE", (12.6, 13.7, front - 3.5), (13.4, 14.3, front - 2), "brass")]
        for k, (y1, y2) in enumerate(shelves):
            els += [bx(f"Shelf{k}", (1.5, y1, front + 0.5), (14.5, y2, 14.5), "maple"), lip(f"Lip{k}", 1.5, 14.5, y2, front + 0.5)]
        if kind == "books":
            els += books(seed, book_y, front + 0.5 if book_y != 3.5 else front, max_h=4.8, depth=4)
        return els

    shapes = {}
    for kind in ("empty", "books", "rail"):
        for part in ("base", "mid1", "mid2", "crown"):
            if kind == "rail" and part != "crown":
                path = f"block/end/end-tallshelf-empty-{part}"
            else:
                path = shp(f"end-tallshelf-{kind}-{part}", library(part, kind, seed_of(f"tall{kind}{part}")))
            shapes.update(by_side(f"*-{kind}-{part}", path))
    blk("end-tallshelf", {
        "variantgroups": [{"code": "kind", "states": ["empty", "books", "rail"]},
                          {"code": "part", "states": ["base", "mid1", "mid2", "crown"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-empty-base-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 2, "sounds": WOOD,
        "dropsByType": {"*-books-*": drops((SHELF, 0.2, 0), (PLANK, 1.2, 0.5), ("game:book-normal-darkolive", 0.35, 0),
                                           ("game:book-aged-darkbeige", 0.1, 0)),
                        "*": drops((SHELF, 0.2, 0), (PLANK, 1.2, 0.5))},
    }, "The End: a single-faced library stack 4 tall (base, mid1, mid2, crown), its shelves facing the side named; "
       "rail: a brass rail along the crown for the rolling ladders. Also the Turnaround's wall")
    for kind, eng in (("empty", "Library Stack"), ("books", "Library Stack"), ("rail", "Library Stack")):
        name(f"end-tallshelf-{kind}-*", eng)

    shapes = {}
    for kind in ("empty", "books"):
        for part in ("lower", "upper"):
            path = shp(f"end-wallshelf-{kind}-{part}", library(part, kind, seed_of(f"wall{kind}{part}")))
            shapes.update(by_side(f"*-{kind}-{part}", path))
    blk("end-wallshelf", {
        "variantgroups": [{"code": "kind", "states": ["empty", "books"]}, {"code": "part", "states": ["lower", "upper"]},
                          {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-empty-lower-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 1.5, "sounds": WOOD,
        "dropsByType": {"*-books-*": drops((STICK, 2, 0), (PLANK, 0.25, 0), ("game:book-normal-teal", 0.3, 0), (PAPER, 0.4, 0.3)),
                        "*": drops((STICK, 2, 0), (PLANK, 0.25, 0))},
    }, "The End: single-faced wall shelving 2 tall against the wall behind it (the shelves face the side named)")
    name("end-wallshelf-*", "Wall Shelving")

    # ---- end-endcap: the tapered slatwall pyramid towers of the photographs
    def pyramid(part, tagged):
        els = []
        if part == "lower":
            els.append(bx("Plinth", (0.6, 0, 0.6), (15.4, 1.2, 15.4), "kick"))
            y0, hw0, hw1, ys = 1.2, 7.0, 5.5, [1.2] + list(range(2, 17))
        else:
            y0, hw0, hw1, ys = 0.0, 5.5, 3.0, list(range(0, 17))

        def hw(y):
            return hw0 + (hw1 - hw0) * ((y - (1.2 if part == "lower" else 0)) / (16 - (1.2 if part == "lower" else 0)))
        for k in range(len(ys) - 1):
            a, b = ys[k], ys[k + 1]
            h = hw((a + b) / 2)
            u = min(16, 2 * h)
            uv = (0, 16 - b, u, 16 - a)
            els.append(faces_box(f"S{k}", (8 - h, a, 8 - h), (8 + h, b, 8 + h),
                                 {"north": "slatwall", "south": "slatwall", "east": "slatwall", "west": "slatwall"}, uv=uv))
        for k in range(8):
            a, b = 2 * k + (1.2 if part == "lower" and k == 0 else 0), 2 * k + 2
            h = hw((a + b) / 2) + 0.15
            for j, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                x, z = 8 + sx * h, 8 + sz * h
                els.append(bx(f"E{k}{j}", (x - 0.4, a, z - 0.4), (x + 0.4, b, z + 0.4), "maple-dark"))
        if part == "upper":
            els.append(bx("Cap", (4.5, 16, 4.5), (11.5, 17, 11.5), "maple-dark"))
        else:
            els.append(faces_box("Top", (8 - hw1, 15.9, 8 - hw1), (8 + hw1, 16, 8 + hw1), {"up": "maple"}))
        if tagged:
            y = 10 if part == "lower" else 6
            h = hw(y + 1) + 0.08
            els.append(faces_box("Sticker", (6.5, y, 8 - h - 0.05), (9.5, y + 2, 8 - h), {"north": "sticker"}, uv=(0, 4, 16, 12)))
        return els

    shapes = {}
    for kind in ("plain", "tagged"):
        for part in ("lower", "upper"):
            shapes[f"*-{kind}-{part}"] = {"base": shp(f"end-endcap-{kind}-{part}", pyramid(part, kind == "tagged"))}
    blk("end-endcap", {
        "variantgroups": [{"code": "kind", "states": ["plain", "tagged"]}, {"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": inv("*-plain-lower"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 1.5, "sounds": WOOD,
        "collisionboxByType": {"*-lower": cuboid((0.06, 0, 0.06, 0.94, 1, 0.94)), "*-upper": cuboid((0.15, 0, 0.15, 0.85, 1, 0.85))},
        "selectionboxByType": {"*-lower": cuboid((0.06, 0, 0.06, 0.94, 1, 0.94)), "*-upper": cuboid((0.15, 0, 0.15, 0.85, 1.06, 0.85))},
        "drops": drops((STICK, 2, 1), (PLANK, 1, 0.5)),
    }, "The End: a tapered slatwall display tower, 2 tall; tagged has a yellow price sticker on its north face")
    name("end-endcap-*", "Slatwall Display Tower")


# ======================= The service desk and its terminal =======================

DESK = [  # (name, from-front d1, d2, y1, y2, texture): the profile of the desk, measured back from its front face
    ("Kick", 0.6, 2.0, 0, 2, "kick"),
    ("Panel", 0, 2, 2, 14.5, "maple-vertical"),
    ("Top", -0.6, 12.4, 14.5, 16, "maple-light"),   # deep enough to carry the computer behind the ledge
    ("Ledge", -0.6, 3.4, 16, 19, "maple-light"),
    ("LedgeFace", -0.7, -0.6, 16.2, 18.8, "maple"),
    ("Shelf", 2, 9.5, 7, 8, "maple"),
]
FRONT = 3.0


def desk_straight(x1=0, x2=16):
    return [bx(n, (x1, y1, FRONT + d1), (x2, y2, FRONT + d2), t) for n, d1, d2, y1, y2, t in DESK]


def desk_arc(cx, cz, r_front, inward, ry0, ry1, n=4, tag="A"):
    """The desk profile swept round (cx, cz): segments pointing north, turned by rotationY (counter-clockwise from
    above) from ry0 to ry1. The front is the outer edge, or the inner one (inward)."""
    els = []
    step = abs(ry1 - ry0) / n
    half = math.radians(step / 2)
    for i in range(n):
        ry = ry0 + (ry1 - ry0) * (i + 0.5) / n
        for nm, d1, d2, y1, y2, t in DESK:
            ra, rb = (r_front + d1, r_front + d2) if inward else (r_front - d2, r_front - d1)
            ra = max(0, ra)
            if rb <= ra:
                continue
            w = 2 * rb * math.tan(half) * 1.06 + 0.06
            el = bx(f"{tag}{nm}{i}", (cx - w / 2, y1, cz - rb), (cx + w / 2, y2, cz - ra), t)
            els.append(rot(el, ry=ry, origin=(cx, y1, cz)))
    return els


def desks():
    kinds = {
        "straight": desk_straight(),
        # Convex corner: in through the west edge facing north, out through the south edge facing east
        "curveout": desk_arc(0, 16, 13, False, 0, -90, tag="O"),
        # Concave corner (the desk wraps round the customer): in through the west edge facing north, out through the
        # north edge facing west
        "curvein": desk_arc(0, 0, 3, True, -90, -180, tag="I"),
        # A rounded end: in through the west edge, the front turning round to the staff side
        "end": desk_straight(0, 3) + desk_arc(3, 13, 10, False, 0, -90, tag="E"),
        # The gate: the counter flap folded up, the half door swung back
        "gate": [bx("Kick", (0, 0, 3.6), (1, 2, 5), "kick"), bx("Kick2", (15, 0, 3.6), (16, 2, 5), "kick"),
                 rot(bx("Flap", (0.2, 14.5, 2.4), (15.8, 16, 13), "maple-light"), rx=90, origin=(8, 16, 13)),
                 rot(bx("HalfDoor", (1, 1, 3), (14, 13.5, 4.5), "maple-vertical"), ry=-80, origin=(1, 7, 4.5)),
                 bx("Hinge", (0.4, 2, 3.2), (1.2, 12.5, 4.6), "brushed")],
    }
    shapes = {}
    for kind, els in kinds.items():
        shapes.update(by_side(f"*-{kind}", shp(f"end-desk-{kind}", els)))
    boxes = {"straight": [(0, 0, 0.15, 1, 1, 0.97)], "curveout": [(0, 0, 0.15, 0.5, 1, 1), (0.5, 0, 0.4, 0.85, 1, 1)],
             "curvein": [(0, 0, 0, 0.85, 1, 0.85)], "end": [(0, 0, 0.15, 0.85, 1, 0.85)]}
    coll = {}
    for kind, b in boxes.items():
        coll.update(boxes_by_side(f"*-{kind}", b))
    blk("end-desk", {
        "variantgroups": [{"code": "kind", "states": list(kinds)}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-straight-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 2, "sounds": WOOD,
        "collisionboxesByType": dict(coll, **{"*-gate-*": []}),
        "selectionboxesByType": dict(coll, **{"*-gate-*": [cuboid((0, 0, 0.15, 1, 1, 0.85))]}),
        "drops": drops((PLANK, 2, 1), (STICK, 1, 1)),
    }, "The End: the curved maple service desk, 1 tall, its front (the customer's side) facing the side named. "
       "The band runs z 3-13 of the north-facing model. curveout: convex corner, in at the west edge, out at the south "
       "edge facing east; curvein: concave, in at the west edge, out at the north edge facing west; end: rounded end "
       "(in at the west); gate: the flap up and the half door open, walk-through")
    for kind, eng in (("straight", "Service Desk"), ("curveout", "Service Desk"), ("curvein", "Service Desk"),
                      ("end", "Service Desk"), ("gate", "Service Desk Gate")):
        name(f"end-desk-{kind}-*", eng)

    # The terminal: a beige 90s CRT on its desktop case, keyboard in front, a cable hanging off the back
    def terminal(screen, glow):
        # The desk's transaction ledge (3 high, z 2.4-6.4) stands on the customer's side of the block below: the
        # computer sits behind it, the keyboard and mouse on top of it
        els = [
            faces_box("Case", (2, 0, 6.6), (14, 3, 15.4), {"north": "crt", "east": "crt-shade", "west": "crt-shade", "south": "crt-shade", "up": "crt", "down": "crt-shade"}),
            bx("Floppy", (8.5, 1.1, 6.45), (12.5, 1.7, 6.6), "kick"), bx("Led", (3, 1.2, 6.45), (3.6, 1.7, 6.6), "greenglass"),
            faces_box("Monitor", (3, 3, 7), (13, 12, 14.4), {"north": "crt", "east": "crt-shade", "west": "crt-shade", "south": "crt-shade", "up": "crt-vents", "down": "crt-shade"}),
            faces_box("Tube", (4.5, 4, 14.4), (11.5, 11, 15.8), {"east": "crt-shade", "west": "crt-shade", "south": "crt-vents", "up": "crt-shade", "down": "crt-shade"}),
            bx("BezelT", (3.5, 10.5, 6.5), (12.5, 11.4, 7), "crt"), bx("BezelB", (3.5, 3.6, 6.5), (12.5, 4.5, 7), "crt"),
            bx("BezelL", (3.5, 4.5, 6.5), (4, 10.5, 7), "crt"), bx("BezelR", (12, 4.5, 6.5), (12.5, 10.5, 7), "crt"),
            faces_box("Screen", (4, 4.5, 6.7), (12, 10.5, 6.8), {"north": screen}, glow_by_face={"north": glow} if glow else None, uv=(0, 0, 16, 16)),
            bx("Badge", (10.5, 3.8, 6.4), (11.8, 4.3, 6.5), "brushed"),
            faces_box("Keyboard", (2.5, 3, 2.7), (13.5, 3.9, 6.1), {"up": "keyboard", "north": "crt-shade", "east": "crt-shade", "west": "crt-shade", "south": "crt-shade"}),
            bx("Mouse", (14.2, 3, 3.4), (15.4, 3.6, 5.2), "crt"),
            bx("Cable", (7.4, -9, 15.8), (8.2, 1.2, 16.4), "rubber"), bx("CableBox", (6.5, -11, 15.4), (9.5, -9, 16.6), "kick"),
        ]
        return els
    states = {"off": ("screen-off", 0), "on": ("screen-on", 220), "static": ("screen-static", 140), "party": ("screen-party", 220), "dead": ("screen-dead", 0)}
    shapes = {}
    for st, (scr, glow) in states.items():
        shapes.update(by_side(f"*-{st}", shp(f"end-terminal-{st}", terminal(scr, glow))))
    blk("end-terminal", {
        "variantgroups": [{"code": "state", "states": list(states)}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-off-north"), "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 20, "drops": [],
        "behaviors": [{"name": "BackroomsEndTerminal"}],
        "collisionboxByType": {f"*-{s}": cuboid((0.12, 0, 0.25, 0.88, 0.75, 0.97), s) for s in SIDES},
        "selectionboxByType": {f"*-{s}": cuboid((0.12, 0, 0.0, 0.88, 0.75, 0.97), s) for s in SIDES},
        "lightHsvByType": {"*-on-*": [0, 0, 4], "*-party-*": [0, 0, 4]},
        "soundsByType": {"*-off-*": dict(METAL, ambient="backrooms:ambient/end/crtbuzz", ambientBlockCount=1),
                         "*": METAL},
        "attributes": {"handbook": {"groupBy": ["end-terminal-*"]}},
    }, "The End: an old CRT computer on a service desk, its screen toward the side named. off buzzes; on shows THE END; "
       "static; party shows =); dead never turns on again. Indestructible")
    name("end-terminal-*", "Old Computer")


# ======================= Furniture =======================

def legs(x1, x2, z1, z2, h, w=1.5, tex="maple-dark"):
    return [bx(f"Leg{k}", (x, 0, z), (x + w, h, z + w), tex) for k, (x, z) in enumerate(((x1, z1), (x2 - w, z1), (x1, z2 - w), (x2 - w, z2 - w)))]


def chair_els():
    els = legs(2, 14, 2, 14, 7.5)
    els += [bx("SeatFrame", (2, 7, 2), (14, 8, 14), "maple"), bx("Seat", (2.5, 8, 2), (13.5, 9.5, 12.8), "teal"),
            bx("PostW", (2, 7.5, 12.5), (3.5, 17, 14), "maple-dark"), bx("PostE", (12.5, 7.5, 12.5), (14, 17, 14), "maple-dark"),
            bx("TopRail", (3.5, 14.8, 12.6), (12.5, 17, 13.9), "maple"), bx("LowRail", (3.5, 10.2, 12.6), (12.5, 11.2, 13.9), "maple"),
            bx("StretcherW", (2.3, 3, 3.5), (3.2, 3.8, 12.5), "maple-dark"), bx("StretcherE", (12.8, 3, 3.5), (13.7, 3.8, 12.5), "maple-dark"),
            bx("StretcherF", (3.5, 2.5, 2.3), (12.5, 3.3, 3.2), "maple-dark")]
    for k, x in enumerate((5, 7.5, 10)):
        els.append(bx(f"Slat{k}", (x, 11.2, 12.9), (x + 1.2, 14.8, 13.6), "maple"))
    return els


def table_els():
    return legs(0.8, 15.2, 0.8, 15.2, 12.5) + [
        faces_box("Top", (0, 12.5, 0), (16, 14, 16), {"up": "maple-light", "down": "maple", "north": "maple-dark", "south": "maple-dark", "east": "maple-dark", "west": "maple-dark"}),
        bx("ApronN", (2.3, 10.8, 1.2), (13.7, 12.5, 2), "maple"), bx("ApronS", (2.3, 10.8, 14), (13.7, 12.5, 14.8), "maple"),
        bx("ApronW", (1.2, 10.8, 2.3), (2, 12.5, 13.7), "maple"), bx("ApronE", (14, 10.8, 2.3), (14.8, 12.5, 13.7), "maple")]


def furniture():
    lamp = [bx("LampBase", (9.5, 14, 9), (13.5, 14.8, 12), "brass"), bx("LampStem", (11.1, 14.8, 10.1), (11.9, 19.6, 10.9), "brass"),
            faces_box("Shade", (8.5, 19.5, 9), (14.5, 22, 12), {"north": "greenglass", "south": "greenglass", "east": "greenglass", "west": "greenglass", "up": "greenglass"}),
            faces_box("ShadeGlow", (8.7, 19.45, 9.2), (14.3, 19.5, 11.8), {"down": "lampglow"}, glow_by_face={"down": 255}),
            bx("Chain", (13.6, 17.5, 10.4), (13.8, 19.5, 10.6), "brass")]
    wrap = [faces_box("Wrap", (1.4, 0, 1.4), (14.6, 17.6, 14.6), {"north": "wrap", "south": "wrap", "east": "wrap", "west": "wrap", "up": "wrap"})]
    for k, y in enumerate((5, 13)):
        wrap.append(faces_box(f"Tape{k}", (1.3, y, 1.3), (14.7, y + 1.2, 14.7), {"north": "tape", "south": "tape", "east": "tape", "west": "tape"}))
    armchair = [bx("FootFW", (1, 0, 1.5), (2.5, 3, 3), "maple-dark"), bx("FootFE", (13.5, 0, 1.5), (15, 3, 3), "maple-dark"),
                bx("FootBW", (1, 0, 13), (2.5, 3, 14.5), "maple-dark"), bx("FootBE", (13.5, 0, 13), (15, 3, 14.5), "maple-dark"),
                bx("Base", (0.5, 3, 1), (15.5, 8, 15), "mustard"), bx("Cushion", (3, 8, 1.4), (13, 10.2, 12.5), "mustard"),
                bx("ArmW", (0.5, 8, 1), (3, 13, 15), "mustard"), bx("ArmE", (13, 8, 1), (15.5, 13, 15), "mustard"),
                bx("Back", (0.5, 8, 12.5), (15.5, 20, 15), "mustard"), bx("BackCushion", (3, 10.2, 11), (13, 18.5, 12.5), "mustard"),
                bx("ArmCapW", (0.4, 13, 0.9), (3.1, 13.6, 15.1), "maple-dark"), bx("ArmCapE", (12.9, 13, 0.9), (15.6, 13.6, 15.1), "maple-dark")]
    carrel = [bx("SideW", (0, 0, 2), (1.2, 24, 16), "maple"), bx("SideE", (14.8, 0, 2), (16, 24, 16), "maple"),
              faces_box("Top", (1.2, 12, 2), (14.8, 13.5, 16), {"up": "maple-light", "north": "maple-dark", "down": "maple"}),
              faces_box("Back", (1.2, 13.5, 14.5), (14.8, 24, 16), {"north": "slatwall", "south": "maple", "up": "maple-dark"}),
              bx("Shelf", (1.2, 19, 10.5), (14.8, 20, 14.5), "maple"), bx("Modesty", (1.2, 4, 14.5), (14.8, 12, 15.5), "maple"),
              bx("CapW", (-0.2, 24, 1.8), (1.4, 24.6, 16), "maple-dark"), bx("CapE", (14.6, 24, 1.8), (16.2, 24.6, 16), "maple-dark"),
              bx("CapB", (1.2, 24, 14.3), (14.8, 24.6, 16), "maple-dark")]
    display = [bx("Plinth", (2, 0, 3), (14, 7, 13), "maple"), bx("PlinthKick", (2.4, 0, 3.4), (13.6, 1.2, 12.6), "kick"),
               faces_box("Top", (0, 7, 1), (16, 8.5, 15), {"up": "maple-light", "north": "maple-dark", "south": "maple-dark", "east": "maple-dark", "west": "maple-dark", "down": "maple"})]
    for k, x in enumerate((1.5, 6.5, 11.5)):
        display += [rot(bx(f"Stand{k}", (x, 8.5, 6), (x + 3, 12.5, 6.4), "glass"), rx=-18, origin=(x + 1.5, 8.5, 6.4)),
                    bx(f"StandLip{k}", (x, 8.5, 5.2), (x + 3, 9.1, 5.9), "glass"),
                    rot(bx(f"StandLeg{k}", (x + 1.1, 8.5, 6.4), (x + 1.9, 11, 6.8), "glass"), rx=25, origin=(x + 1.5, 8.5, 6.6))]
    magrack = [bx("SideW", (0, 0, 4), (1.2, 22, 16), "maple"), bx("SideE", (14.8, 0, 4), (16, 22, 16), "maple"),
               bx("Back", (1.2, 0, 14.5), (14.8, 22, 16), "maple-vertical"), bx("Kick", (1.2, 0, 4.5), (14.8, 1.5, 14.5), "kick")]
    for k in range(4):
        y = 2 + k * 5
        magrack += [rot(bx(f"Shelf{k}", (1.2, y, 5), (14.8, y + 0.8, 14.5), "maple"), rx=-25, origin=(8, y + 0.4, 14.5)),
                    rot(bx(f"Lip{k}", (1.2, y + 0.8, 5), (14.8, y + 2.4, 5.6), "maple-dark"), rx=-25, origin=(8, y + 0.4, 14.5))]
    kinds = {
        "table": table_els(),
        "lamptable": table_els() + lamp,
        "chair": chair_els(),
        "wrapped": chair_els() + wrap,
        "armchair": armchair,
        "carrel": carrel,
        "displaytable": display,
        "magrack": magrack,
    }
    shapes = {}
    for kind, els in kinds.items():
        shapes.update(by_side(f"*-{kind}", shp(f"end-furniture-{kind}", els)))
    boxes = {"table": [(0, 0, 0, 1, 0.875, 1)], "lamptable": [(0, 0, 0, 1, 0.875, 1)], "chair": [(0.12, 0, 0.12, 0.88, 0.6, 0.88)],
             "wrapped": [(0.09, 0, 0.09, 0.91, 1.1, 0.91)], "armchair": [(0.03, 0, 0.06, 0.97, 0.65, 0.94)],
             "carrel": [(0, 0, 0.12, 1, 1.5, 1)], "displaytable": [(0, 0, 0.06, 1, 0.55, 0.94)], "magrack": [(0, 0, 0.25, 1, 1.4, 1)]}
    sel = {}
    for kind, b in boxes.items():
        sel.update(boxes_by_side(f"*-{kind}", b))
    coll = dict(sel)
    for s in SIDES:
        coll[f"*-magrack-{s}"] = []
    blk("end-furniture", {
        "variantgroups": [{"code": "kind", "states": list(kinds)}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-table-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 1.5, "sounds": WOOD,
        "collisionboxesByType": coll, "selectionboxesByType": sel,
        "renderpassByType": {"*-wrapped-*": "Transparent"},
        "lightHsvByType": {"*-lamptable-*": [8, 4, 10]},
        "soundsByType": {"*-armchair-*": CLOTH, "*-wrapped-*": CLOTH, "*": WOOD},
        "dropsByType": {
            "*-table-*": drops((TABLE, 0.5, 0), (PLANK, 1.5, 0.5)),
            "*-lamptable-*": drops((TABLE, 0.5, 0), (PLANK, 1.5, 0.5), ("game:metalbit-brass", 0.6, 0.4), ("glassshard", 0.5, 0.5)),
            "*-chair-*": drops((CHAIR, 0.5, 0), (STICK, 1.5, 0.5)),
            "*-wrapped-*": drops((CHAIR, 1, 0)),
            "*-armchair-*": drops((CLOTHV, 1.5, 0.5), (PLANK, 1, 0.5), (STICK, 1, 0.5)),
            "*-carrel-*": drops((PLANK, 3, 1), (NAILS, 0.4, 0.4)),
            "*-displaytable-*": drops((PLANK, 2, 1), ("glassshard", 0.6, 0.4)),
            "*-magrack-*": drops((STICK, 2, 1), (PLANK, 1, 0.5)),
        },
    }, "The End: reading-room furniture, facing the side named (a chair's sitter faces it): study table, table with a "
       "banker's lamp, library chair, a chair still in its plastic, armchair, study carrel, display table, magazine rack")
    for kind, eng in (("table", "Study Table"), ("lamptable", "Study Table with Lamp"), ("chair", "Library Chair"),
                      ("wrapped", "Chair in Plastic"), ("armchair", "Armchair"), ("carrel", "Study Carrel"),
                      ("displaytable", "Display Table"), ("magrack", "Magazine Rack")):
        name(f"end-furniture-{kind}-*", eng)

    # ---- The card catalogue: 4 x 5 small drawers, brass pulls and label frames
    def catalogue(open_):
        els = legs(1, 15, 3.2, 15, 3.2, w=1.6, tex="oak")
        els += [faces_box("Cabinet", (0.5, 3, 3), (15.5, 15, 15), {"north": "oak", "south": "oak", "east": "oak", "west": "oak", "down": "oak"}),
                bx("Top", (0, 15, 2.4), (16, 16, 15.6), "oak-light"), bx("Rail", (0.45, 2.6, 2.8), (15.55, 3.4, 15.2), "oak-light")]
        for col in range(4):
            for row in range(5):
                x = 1.1 + col * 3.5
                y = 3.5 + row * 2.3
                z0 = 2.6
                if open_ and (col, row) == (2, 2):
                    z0 = -3.4
                    els += [bx("OpenL", (x + 0.1, y + 0.2, z0 + 0.4), (x + 0.3, y + 1.8, 3), "oak-light"),
                            bx("OpenR", (x + 2.8, y + 0.2, z0 + 0.4), (x + 3.0, y + 1.8, 3), "oak-light"),
                            bx("OpenB", (x + 0.1, y + 0.1, z0 + 0.4), (x + 3.0, y + 0.3, 3), "oak-light"),
                            faces_box("Cards", (x + 0.4, y + 0.3, z0 + 0.8), (x + 2.7, y + 1.7, z0 + 5.5), {"up": "cards", "north": "cards", "east": "cards", "west": "cards"})]
                els += [bx(f"D{col}{row}", (x, y, z0), (x + 3.1, y + 2.0, z0 + 0.4), "oak-light"),
                        faces_box(f"Lbl{col}{row}", (x + 0.85, y + 1.0, z0 - 0.15), (x + 2.25, y + 1.7, z0), {"north": "label"}, uv=(0, 8, 16, 16)),
                        bx(f"Fr{col}{row}", (x + 0.75, y + 0.95, z0 - 0.2), (x + 2.35, y + 1.05, z0), "brass"),
                        bx(f"P{col}{row}", (x + 1.2, y + 0.35, z0 - 0.5), (x + 1.9, y + 0.75, z0), "brass")]
        return els
    shapes = {}
    for kind in ("shut", "open"):
        shapes.update(by_side(f"*-{kind}", shp(f"end-catalogue-{kind}", catalogue(kind == "open"))))
    blk("end-catalogue", {
        "variantgroups": [{"code": "kind", "states": ["shut", "open"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-shut-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 2, "sounds": WOOD,
        "collisionboxByType": {f"*-{s}": cuboid((0, 0, 0.15, 1, 1, 0.97), s) for s in SIDES},
        "selectionboxByType": {f"*-{s}": cuboid((0, 0, 0.15, 1, 1, 0.97), s) for s in SIDES},
        "drops": drops(("end-cataloguecard", 1.5, 0.5), (PAPER, 1, 0), (PLANK, 2, 1), ("game:metalbit-brass", 0.5, 0.5)),
    }, "The End: a golden-oak card catalogue, its drawers toward the side named; open has one drawer pulled out")
    name("end-catalogue-*", "Card Catalogue")


# ======================= The stockroom =======================

def pallet_els():
    els = []
    for k, z in enumerate((0, 7.25, 14.5)):
        els.append(bx(f"Under{k}", (0, 0, z), (16, 0.5, z + 1.5), "pallet"))
        els.append(bx(f"Block{k}", (0, 0.5, z), (16, 1.6, z + 1.5), "pallet"))
    for k in range(5):
        x = k * 3.4
        els.append(bx(f"Board{k}", (x, 1.6, 0), (x + 2.6, 2, 16), "pallet"))
    return els


def stock():
    boxes = []
    for layer in range(3):
        for i, (x, z) in enumerate(((0.6, 0.6), (8.1, 0.6), (0.6, 8.1), (8.1, 8.1))):
            y = 2 + layer * 6
            boxes += [faces_box(f"Box{layer}{i}", (x, y, z), (x + 7.3, y + 5.9, z + 7.3),
                                {"north": "cardboard", "south": "cardboard", "east": "cardboard", "west": "cardboard", "up": "cardboardtop"})]
    wrap = [faces_box("Wrap", (0.4, 2, 0.4), (15.6, 20.2, 15.6), {"north": "wrap", "south": "wrap", "east": "wrap", "west": "wrap", "up": "wrap"}),
            faces_box("Label", (4, 12, 0.6), (12, 18, 0.62), {"north": "stocklabel"}, uv=(0, 0, 16, 16))]
    step = [bx("RailL", (3, 0, 7.4), (4.5, 30, 8.9), "pallet"), bx("RailR", (11.5, 0, 7.4), (13, 30, 8.9), "pallet"),
            bx("BackL", (3.2, 0, 9.4), (4.4, 27, 10.4), "pallet"), bx("BackR", (11.6, 0, 9.4), (12.8, 27, 10.4), "pallet"),
            bx("Top", (2.6, 30, 7), (13.4, 31.2, 10.6), "pallet")]
    for k in range(5):
        y = 4 + k * 5.5
        step.append(bx(f"Step{k}", (4.5, y, 6.6), (11.5, y + 1, 9.2), "pallet"))
    step += [faces_box("Wrap", (2.2, 0, 6.2), (13.8, 31.8, 11), {"north": "wrap", "south": "wrap", "east": "wrap", "west": "wrap", "up": "wrap"})]
    for k, y in enumerate((8, 22)):
        step.append(faces_box(f"Tape{k}", (2.1, y, 6.1), (13.9, y + 1.2, 11.1), {"north": "tape", "south": "tape", "east": "tape", "west": "tape"}))
    step = rot_all(step, rx=12, origin=(8, 0, 7))
    trolley = [bx("EndW", (0.5, 2, 1), (2, 20, 15), "maple"), bx("EndE", (14, 2, 1), (15.5, 20, 15), "maple"),
               bx("CapW", (0.3, 20, 0.8), (2.2, 20.8, 15.2), "maple-dark"), bx("CapE", (13.8, 20, 0.8), (15.7, 20.8, 15.2), "maple-dark"),
               bx("Bottom", (2, 2, 1.5), (14, 3, 14.5), "maple")]
    for k, y in enumerate((8, 14)):
        trolley += [rot(bx(f"ShelfN{k}", (2, y, 1.5), (14, y + 0.8, 8), "maple"), rx=10, origin=(8, y, 8)),
                    rot(bx(f"ShelfS{k}", (2, y, 8), (14, y + 0.8, 14.5), "maple"), rx=-10, origin=(8, y, 8))]
    trolley.append(bx("Divider", (2, 3, 7.6), (14, 19, 8.4), "maple"))
    for k, (x, z) in enumerate(((0.8, 1.5), (13.7, 1.5), (0.8, 12.5), (13.7, 12.5))):
        trolley += [bx(f"Castor{k}", (x, 0, z), (x + 1.5, 1.4, z + 2), "rubber"), bx(f"Fork{k}", (x - 0.1, 1.4, z + 0.3), (x + 1.6, 2, z + 1.7), "galvanised")]
    kit = pallet_els()
    for k in range(4):
        y = 2 + k * 2.6
        kit.append(faces_box(f"Pack{k}", (0.8 + (k % 2) * 0.6, y, 1 + (k % 2) * 0.4), (15.2 + (k % 2) * 0.3, y + 2.5, 7.4 + (k % 2) * 0.4),
                             {"north": "cardboard", "south": "cardboard", "east": "cardboard", "west": "cardboard", "up": "cardboardtop"}))
        kit.append(faces_box(f"PackB{k}", (0.6, y, 8.4), (15.4, y + 2.5, 15), {"north": "cardboard", "south": "cardboard", "east": "cardboard", "west": "cardboard", "up": "cardboardtop"}))
    kit.append(faces_box("KitLabel", (5, 9, 0.75), (11, 11.6, 0.8), {"north": "stocklabel"}, uv=(0, 0, 16, 16)))
    kinds = {"pallet": pallet_els() + boxes + wrap, "trolley": trolley, "ladderwrapped": step, "kit": kit}
    shapes = {}
    for kind, els in kinds.items():
        shapes.update(by_side(f"*-{kind}", shp(f"end-stock-{kind}", els)))
    boxes_ = {"pallet": [(0, 0, 0, 1, 1.27, 1)], "trolley": [(0.03, 0, 0.06, 0.97, 1.3, 0.94)],
              "ladderwrapped": [(0.12, 0, 0.35, 0.88, 1.9, 1)], "kit": [(0, 0, 0, 1, 0.8, 1)]}
    coll = {}
    for kind, b in boxes_.items():
        coll.update(boxes_by_side(f"*-{kind}", b))
    blk("end-stock", {
        "variantgroups": [{"code": "kind", "states": list(kinds)}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-pallet-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 1.5, "sounds": WOOD,
        "collisionboxesByType": coll, "selectionboxesByType": coll,
        "renderpassByType": {"*-pallet-*": "Transparent", "*-ladderwrapped-*": "Transparent"},
        "dropsByType": {
            "*-pallet-*": drops((PLANK, 3, 1), (NAILS, 0.5, 0.5), ("block:supplybox", 1, 0)),
            "*-trolley-*": drops((STICK, 2, 1), ("metalbracket", 1, 0.5), (PLANK, 1, 0.5)),
            "*-ladderwrapped-*": drops((LADDER, 2, 0)),
            "*-kit-*": drops((PLANK, 4, 0), (NAILS, 1, 0)),
        },
    }, "The End: back-of-house stock: a shrink-wrapped pallet of boxes, a book trolley, a step ladder still in its "
       "plastic leaning on the wall behind, flat-pack shelving on a pallet")
    for kind, eng in (("pallet", "Wrapped Stock"), ("trolley", "Book Trolley"), ("ladderwrapped", "Ladder in Plastic"), ("kit", "Shelving Kit")):
        name(f"end-stock-{kind}-*", eng)


# ======================= The atrium: escalator, railing, pendants, ladders =======================

L45 = 16 * math.sqrt(2)


def incline(nm, x1, x2, a, b, tex, length=L45):
    """A slab along the escalator's 45-degree line (through the block's centre, rising to the north), from a to b
    above it (measured square to the line). It is slid along the line so that its middle stands straight over the
    block's centre: each block's piece then covers its own block (its square-cut ends straddling the block's north and
    south edges), and the pieces of consecutive blocks (one up, one north) meet end to end."""
    zc = 8 - (a + b) / 2  # rotationX 45 maps (y 8 + p, z 8 - p) to (8 + p*sqrt2, 8): straight over the centre
    el = bx(nm, (x1, 8 + a, zc - length / 2), (x2, 8 + b, zc + length / 2), tex)
    return rot(el, rx=45, origin=((x1 + x2) / 2, 8, 8))


def balustrades(flat=None):
    """Both sides: brushed steel skirt, a glass panel, a black handrail. flat = (y0, z1, z2) for a landing."""
    els = []
    for side, (x1, x2) in (("W", (0, 1.5)), ("E", (14.5, 16))):
        gx1, gx2 = (x1 + 0.5, x1 + 1) if side == "W" else (x2 - 1, x2 - 0.5)
        if flat is None:
            # measured square to the line: the handrail tops out 16 px over the line (where it meets the landing's
            # rail); the skirt reaches down to the block's low corner, so it closes the space under the steps
            els += [incline(f"Skirt{side}", x1, x2, -11.4, 2.5, "brushed"), incline(f"Glass{side}", gx1, gx2, 2.5, 9.5, "glass"),
                    incline(f"Rail{side}", x1 - 0.2, x2 + 0.2, 9.5, 11.3, "rubber")]
        else:
            y0, z1, z2 = flat
            els += [bx(f"Skirt{side}", (x1, y0 - 3, z1), (x2, y0 + 2.5, z2), "brushed"), bx(f"Glass{side}", (gx1, y0 + 2.5, z1), (gx2, y0 + 14.5, z2), "glass"),
                    bx(f"Rail{side}", (x1 - 0.2, y0 + 14.5, z1), (x2 + 0.2, y0 + 16.3, z2), "rubber")]
    return els


def atrium():
    # Four steps a block, 4 px up and 4 px deep, climbing north; each runs down 4 px below its tread so its riser (the
    # south face, the one a climber sees) is solid down to the step before
    step = []
    for k in range(4):
        z1, z2 = 12 - 4 * k, 16 - 4 * k
        step.append(faces_box(f"Step{k}", (1.5, max(0, 4 * k - 4), z1), (14.5, 4 * k + 4, z2), {"up": "tread", "south": "riser", "down": "duct"}))
    step += balustrades()
    # The head of the flight: the last steps (it climbs like the others), the comb plate on the top step, newels
    top = [json.loads(json.dumps(e)) for e in step]
    top += [faces_box("Comb", (1.5, 16, 0), (14.5, 16.4, 4), {"up": "comb", "north": "brushed", "south": "brushed"}, uv=(0, 16, 16, 12)),
            bx("NewelW", (-0.2, 16, 0), (1.7, 32.3, 1.6), "rubber"), bx("NewelE", (14.3, 16, 0), (16.2, 32.3, 1.6), "rubber")]
    bottom = [faces_box("Comb", (1.5, 0, 0), (14.5, 0.8, 16), {"up": "comb", "north": "brushed", "south": "brushed"})]
    bottom += balustrades((0, 0, 14)) + [bx("NewelW", (-0.2, 6, 13.8), (1.7, 16.3, 15.6), "rubber"), bx("NewelE", (14.3, 6, 13.8), (16.2, 16.3, 15.6), "rubber"),
                                         bx("EndW", (0, 0, 14), (1.5, 6, 15), "brushed"), bx("EndE", (14.5, 0, 14), (16, 6, 15), "brushed")]
    shapes = {}
    for part, els in (("step", step), ("top", top), ("bottom", bottom)):
        shapes.update(by_side(f"*-{part}", shp(f"end-escalator-{part}", els)))
    coll = {}
    coll.update(boxes_by_side("*-step", [(0, 0, 0, 1, 0.5, 1), (0, 0.5, 0, 1, 1, 0.5)]))
    coll.update(boxes_by_side("*-top", [(0, 0, 0, 1, 0.5, 1), (0, 0.5, 0, 1, 1, 0.5)]))
    coll.update(boxes_by_side("*-bottom", [(0, 0, 0, 1, 0.05, 1)]))
    blk("end-escalator", {
        "variantgroups": [{"code": "part", "states": ["step", "top", "bottom"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-step-north"), "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 20, "drops": [], "sounds": METAL,
        "collisionboxesByType": coll, "selectionboxesByType": coll,
    }, "The End: a stopped escalator, 1 wide, rising toward the side named one block per block (step); bottom is the "
       "landing before the first step, top the last step with the comb plate at its head. Climbs like stairs. Indestructible")
    name("end-escalator-*", "Escalator (Stopped)")

    rail = [bx("Shoe", (0, 0, 0.45), (16, 1.5, 2.05), "aluminium"), faces_box("Glass", (0, 1.5, 1), (16, 14.5, 1.5), {"north": "glass", "south": "glass", "up": "glass"}),
            bx("Post0", (0.25, 0, 0.5), (1.75, 15, 2), "galvanised"), bx("Post1", (8.25, 0, 0.5), (9.75, 15, 2), "galvanised"),
            bx("Handrail", (0, 15, 0.25), (16, 16.5, 2.25), "maple")]
    blk("end-railing", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-north"), "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": by_side("*", shp("end-railing", rail)), **OPEN, "resistance": 4, "sounds": GLASS,
        "renderpass": "Transparent",
        "collisionboxByType": {f"*-{s}": cuboid((0, 0, 0, 1, 1.5, 0.16), s) for s in SIDES},
        "selectionboxByType": {f"*-{s}": cuboid((0, 0, 0, 1, 1.04, 0.16), s) for s in SIDES},
        "drops": drops(("glassshard", 2, 1), ("metalbracket", 1, 0.5)),
    }, "The End: the mezzanine's glass railing along the north edge of its block (the void lies toward the side named)")
    name("end-railing-*", "Mezzanine Railing")

    els = [bx("Rod", (7.6, 5, 7.6), (8.4, 16, 8.4), "rubber"), bx("Canopy", (6.5, 15, 6.5), (9.5, 16, 9.5), "drum"),
           faces_box("Drum", (3.5, 1, 3.5), (12.5, 5, 12.5), {"north": "drum", "south": "drum", "east": "drum", "west": "drum", "up": "drum"}),
           bx("Rim", (3.2, 0.6, 3.2), (12.8, 1.2, 12.8), "brass"),
           faces_box("Diffuser", (3.8, 0.9, 3.8), (12.2, 1, 12.2), {"down": "diffuser"}, glow_by_face={"down": 255})]
    blk("end-pendant", {
        "creativeinventory": INV_ALL, "blockmaterial": "Metal", "drawtype": "json",
        "shape": {"base": shp("end-pendant", els)}, **OPEN, "resistance": 2, "sounds": METAL, "lightHsv": [8, 2, 20],
        "collisionbox": None, "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.2, "x2": 0.8, "y2": 0.35, "z2": 0.8},
        "drops": drops(("glassshard", 1, 0.5), ("scrapwire", 1, 0.5), ("game:metalbit-brass", 0.4, 0.3)),
    }, "The End: a drum pendant hanging in the atrium void from the ceiling just above it")
    name("end-pendant", "Pendant Lamp")

    # Ladders, standing against the side named. The rolling library ladder, 2 tall, leans on the tall stack beyond that
    # side, hooked over its shelf at head height; the steel ladder is fixed to the wall there, one block per block
    z0, top_z = 7.0, -3.5
    slope = (z0 - top_z) / 32
    ang = math.degrees(math.atan(slope))
    shapes = {}
    for k, part in enumerate(("lower", "upper")):
        els = []
        for side, (x1, x2) in (("W", (2, 3.5)), ("E", (12.5, 14))):
            zc = z0 - slope * (16 * k + 8)
            el = bx(f"Rail{side}", (x1, 8 - 8.3, zc - 0.75), (x2, 8 + 8.3, zc + 0.75), "maple")
            els.append(rot(el, rx=-ang, origin=((x1 + x2) / 2, 8, zc)))
        for j, y in enumerate((2, 6, 10, 14)):
            zc = z0 - slope * (16 * k + y)
            els.append(bx(f"Rung{j}", (3.5, y - 0.5, zc - 0.6), (12.5, y + 0.5, zc + 0.6), "maple-dark"))
        if part == "lower":
            els += [bx("CastorW", (1.8, 0, 6.0), (3.7, 1.4, 8.4), "rubber"), bx("CastorE", (12.3, 0, 6.0), (14.2, 1.4, 8.4), "rubber"),
                    bx("AxleW", (2.2, 1.4, 6.6), (3.3, 2.2, 7.8), "brass"), bx("AxleE", (12.7, 1.4, 6.6), (13.8, 2.2, 7.8), "brass")]
        else:
            for side, (x1, x2) in (("W", (2.2, 3.3)), ("E", (12.7, 13.8))):
                zr = z0 - slope * 25.5
                els += [bx(f"Hook{side}", (x1, 9.2, -6.2), (x2, 10, zr), "brass"), bx(f"HookTab{side}", (x1, 7.6, -6.4), (x2, 10, -5.7), "brass")]
            els += [bx("CapW", (2, 15.6, top_z - 1.3), (3.5, 16.4, top_z + 0.4), "maple-dark"), bx("CapE", (12.5, 15.6, top_z - 1.3), (14, 16.4, top_z + 0.4), "maple-dark")]
        shapes.update(by_side(f"*-rolling-{part}", shp(f"end-ladder-rolling-{part}", els)))
    wall = [bx("RailW", (3, 0, 2.5), (4, 16, 3.5), "galvanised"), bx("RailE", (12, 0, 2.5), (13, 16, 3.5), "galvanised")]
    for j, y in enumerate((2, 6, 10, 14)):
        wall.append(bx(f"Rung{j}", (4, y - 0.45, 2.6), (12, y + 0.45, 3.4), "galvanised"))
    for j, y in enumerate((1, 9)):
        wall += [bx(f"StandW{j}", (3.1, y, 0), (3.9, y + 0.8, 2.5), "galvanised"), bx(f"StandE{j}", (12.1, y, 0), (12.9, y + 0.8, 2.5), "galvanised")]
    path = shp("end-ladder-wall", wall)
    for part in ("lower", "upper"):
        shapes.update(by_side(f"*-wall-{part}", path))
    coll = {}
    for k, part in enumerate(("lower", "upper")):
        za = max(0.0, (z0 - slope * 16 * (k + 1) - 1) / 16)
        zb = (z0 - slope * 16 * k + 1.4) / 16
        coll.update(boxes_by_side(f"*-rolling-{part}", [(0.12, 0, za, 0.88, 1, zb)]))
        coll.update(boxes_by_side(f"*-wall-{part}", [(0.15, 0, 0, 0.85, 1, 0.25)]))
    blk("end-ladder", {
        "variantgroups": [{"code": "kind", "states": ["rolling", "wall"]}, {"code": "part", "states": ["lower", "upper"]},
                          {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-rolling-lower-north", "*-wall-lower-north"], "decorative": ["*-rolling-lower-north", "*-wall-lower-north"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shapes, **OPEN, "resistance": 1.5,
        "climbable": True, "collisionboxesByType": coll, "selectionboxesByType": coll,
        "soundsByType": {"*-wall-*": METAL, "*": WOOD},
        "dropsByType": {"*-rolling-lower-*": drops((LADDER, 1.5, 0.5)), "*-rolling-*": drops((LADDER, 1, 0)),
                        "*-wall-*": drops(("metalbracket", 1, 0.5))},
    }, "The End: ladders standing against the side named. rolling: a maple library ladder, 2 tall (lower, upper), "
       "leaning onto the tall stack beyond that side (the stack facing back toward the ladder), hooked over its shelf; "
       "wall: a steel ladder fixed to the wall on that side (lower; upper is the same). Climbable")
    name("end-ladder-rolling-*", "Library Ladder")
    name("end-ladder-wall-*", "Steel Ladder")


# ======================= Words on the walls: letters, posters, signs, a clock =======================

def wall_words():
    # Bronze letters on standoffs, 10 tall, centred on the north face of a soffit or wall block
    kinds = {}
    for letter, (w, strokes, diags) in LETTERS.items():
        els = stroke_boxes(strokes, diags, 8 + w / 2, 3, 1, -1.6, -0.5, "bronze", nm="L")
        if strokes or diags:
            for k, (x1, y1, x2, y2) in enumerate(strokes[:3]):
                cx = 8 + w / 2 - (x1 + x2) / 2
                cy = 3 + (y1 + y2) / 2
                els.append(bx(f"Standoff{k}", (cx - 0.3, cy - 0.3, -0.5), (cx + 0.3, cy + 0.3, 0), "brushed"))
        kinds[letter] = (els, [])
    backed_block("end-letter", kinds, ["soffit", "wall"],
                 "The End: bronze metal letters standing off the side-named face of a soffit block (family soffit, rel 4) "
                 "or of the yellow band (family wall, rel 3). THE END = t h e blank e n d; THE END IS NEAR across 15 "
                 "blocks. Indestructible",
                 kind_group="letter", backing_group="family", backing_first=True, extra={"resistance": 20, "drops": []})
    name("end-letter-*", "Metal Letter")

    # Posters and notices: on a wall (the backing named) or alone against the wall behind an air block
    def sheet(kind, z1, z2, back=False):
        f = "south" if back else "north"
        if kind == "yellow":
            els = [faces_box("Sheet", (2, 1, z1), (14, 15, z2), {f: "poster-yellow", "up": "poster-yellow", "east": "poster-yellow", "west": "poster-yellow"}, uv=(0, 0, 16, 16))]
            corners = ((2.2, 13.6), (12.6, 13.6), (2.2, 1.2), (12.6, 1.2))
        elif kind == "notice":
            els = [faces_box("Sheet", (3.5, 2, z1), (12.5, 14, z2), {f: "poster-notice", "up": "poster-notice", "east": "poster-notice", "west": "poster-notice"}, uv=(0, 0, 16, 16))]
            corners = ((3.7, 12.6), (11.1, 12.6))
        else:
            tex = f"poster-{kind}"
            el = faces_box("Card", (5, 4, z1), (11, 12, z2), {f: tex, "up": tex, "east": tex, "west": tex}, uv=(0, 0, 16, 16))
            els = [rot(el, rz=5 if kind == "pink" else -4)]
            corners = ((7.2, 11), )
        dz = (z1 - 0.06) if not back else z2
        for k, (x, y) in enumerate(corners):
            els.append(faces_box(f"Tape{k}", (x, y, dz), (x + 1.2, y + 1.2, dz + 0.06), {f: "cleartape"}))
        return els
    kinds = {k: (sheet(k, -0.3, 0), sheet(k, 15.7, 16)) for k in ("yellow", "pink", "green", "notice")}
    backed_block("end-poster", kinds, ["lower"],
                 "The End: closing-down posters on the side-named face of an off-white wall block (rel 2): THE END "
                 "(yellow), small pink and green cards, a FOR SALE notice",
                 backing_group=None, extra={"drops": drops((PAPER, 0.5, 0))})
    for k, eng in (("yellow", "Poster"), ("pink", "Poster"), ("green", "Poster"), ("notice", "Notice")):
        name(f"end-poster-{k}-*", eng)

    # The neon EXIT sign: a black case on the wall over a door, the word in red neon tubes; or hung double-sided
    def exitsign(lit, alone):
        tex, glow = ("neonred", 255) if lit else ("neondead", 0)
        if not alone:
            els = [faces_box("Case", (2, 5, -2.4), (14, 10, -0.4), {"north": "blackcase", "east": "blackcase", "west": "blackcase", "up": "blackcase", "down": "blackcase"}),
                   bx("BracketW", (3, 7, -0.4), (4, 8, 0), "brushed"), bx("BracketE", (12, 7, -0.4), (13, 8, 0), "brushed")]
            els += neon_word(8, 7.5, -2.9, -2.4, tex, glow)
        else:
            els = [bx("Case", (2, 3, 7), (14, 8, 9), "blackcase"),
                   bx("RodW", (3.6, 8, 7.65), (4.3, 16, 8.35), "brushed"), bx("RodE", (11.7, 8, 7.65), (12.4, 16, 8.35), "brushed")]
            els += neon_word(8, 5.5, 6.5, 7, tex, glow) + neon_word(8, 5.5, 9, 9.5, tex, glow, mirror=False)
        return els
    kinds = {st: (exitsign(st == "lit", False), exitsign(st == "lit", True)) for st in ("lit", "dead")}
    backed_block("end-exitsign", kinds, ["band"],
                 "The End: a neon EXIT sign on the side-named face of the yellow band (rel 3) over a door. Also over "
                 "Level 1's EXIT doors into The End. Indestructible",
                 material="Glass", sounds=GLASS, backing_group=None, kind_group="state",
                 extra={"resistance": 20, "drops": [], "lightHsvByType": {"*-lit-*": [0, 7, 8]},
                        "lightAbsorptionByType": {"*-lit-*": 0, "*": 99}})
    name("end-exitsign-*", "EXIT Sign")

    # A dead wall clock, stopped at five to midnight: a round body (a stepped octagon of black case) standing 1.4 off
    # the wall, the painted dial (rim, ticks, hands) on its front, a brass pin through the middle
    def clock(zw):
        zf = zw - 1.4
        case = {f: "blackcase" for f in ("north", "east", "west", "up", "down")}
        els = [faces_box("Body", (4, 5, zf), (12, 13, zw), dict(case, north="clockface"), uv=(0, 0, 16, 16)),
               faces_box("BodyX", (3.2, 6, zf + 0.15), (12.8, 12, zw), case),
               faces_box("BodyY", (5, 4.2, zf + 0.15), (11, 13.8, zw), case),
               faces_box("BezelX", (3.5, 6.6, zf - 0.25), (4.1, 11.4, zf + 0.15), case),
               faces_box("BezelXE", (11.9, 6.6, zf - 0.25), (12.5, 11.4, zf + 0.15), case),
               faces_box("BezelY", (5.6, 4.5, zf - 0.25), (10.4, 5.1, zf + 0.15), case),
               faces_box("BezelYU", (5.6, 12.9, zf - 0.25), (10.4, 13.5, zf + 0.15), case),
               bx("Pin", (7.65, 8.65, zf - 0.35), (8.35, 9.35, zf), "brass")]
        return els
    backed_block("end-clock", {None: (clock(0), clock(16))}, ["lower", "upper", "band", "block", "sage", "slate", "none"],
                 "The End: a wall clock, stopped at five to midnight", none_box=(0.18, 0.24, 0.88, 0.82, 0.88, 1),
                 extra={"drops": drops(("scrapwire", 0.5, 0.5), ("glassshard", 0.5, 0.5))})
    name("end-clock-*", "Stopped Clock")

    # INFORMATION, hung on two chains over a desk
    els = [faces_box("Sign", (1, 4, 7.5), (15, 9, 8.5), {"north": "infosign", "south": "infosign"}, uv=INFOSIGN_UV),
           faces_box("Edge", (1, 4, 7.5), (15, 9, 8.5), {"east": "blackcase", "west": "blackcase", "up": "blackcase", "down": "blackcase"}),
           faces_box("ChainW", (3, 9, 8), (3.8, 16, 8), {"north": "chain", "south": "chain"}),
           faces_box("ChainE", (12.2, 9, 8), (13, 16, 8), {"north": "chain", "south": "chain"})]
    blk("end-hangsign", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-north"), "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": by_side("*", shp("end-hangsign", els)), **OPEN, "resistance": 2, "sounds": METAL,
        "collisionbox": None, "selectionboxByType": {f"*-{s}": cuboid((0.06, 0.25, 0.44, 0.94, 1, 0.56), s) for s in SIDES},
        "drops": drops(("metalbracket", 1, 0.5)),
    }, "The End: an INFORMATION sign hung from the ceiling on two chains over a desk, readable from both faces")
    name("end-hangsign-*", "INFORMATION Sign")


# ======================= Doors, the vent, the doorframe, the bookstore =======================

def all_faces(els):
    """For a block with no side variants that must fit a wall either way: its first element (the door) once, the
    fittings on its north face copied round to all four faces."""
    out = [els[0]]
    for k in range(4):
        for e in els[1:]:
            e = turn(e, k)
            e["name"] = f"{e['name']}{k}"
            out.append(e)
    return out


def doors_and_ways():
    # The EXIT door: grey steel; a push bar on the lower half, wired glass on the upper; the side named is the side the
    # push bar faces (The End's side)
    def exitdoor(part):
        els = [cube_el("exitdoor"),
               bx("JambW", (0, 0, -0.4), (1, 16, 0), "steel"), bx("JambE", (15, 0, -0.4), (16, 16, 0), "steel")]
        if part == "lower":
            els += [bx("Kick", (1.5, 0, -0.15), (14.5, 4, 0), "brushed"),
                    bx("BarHousingW", (2, 12.6, -1.6), (3.4, 15.6, 0), "brushed"), bx("BarHousingE", (12.6, 12.6, -1.6), (14, 15.6, 0), "brushed"),
                    bx("Bar", (3.4, 13.4, -1.5), (12.6, 14.9, -0.7), "brushed"), bx("BarStrip", (3.4, 13.2, -1.6), (12.6, 13.4, -0.6), "rubber"),
                    bx("Hinge0", (1, 3, -0.5), (1.6, 6, 0), "steel")]
        else:
            els += [bx("Head", (0, 15, -0.4), (16, 16, 0), "steel"),
                    faces_box("Window", (5, 3, -0.05), (11, 11, 0), {"north": "wireglass"}, uv=(0, 0, 16, 16)),
                    bx("GasketT", (4.6, 11, -0.3), (11.4, 11.4, 0), "rubber"), bx("GasketB", (4.6, 2.6, -0.3), (11.4, 3, 0), "rubber"),
                    bx("GasketW", (4.6, 3, -0.3), (5, 11, 0), "rubber"), bx("GasketE", (11, 3, -0.3), (11.4, 11, 0), "rubber"),
                    bx("Hinge1", (1, 8, -0.5), (1.6, 11, 0), "steel"), bx("Closer", (2, 12.6, -1.4), (7, 14.2, 0), "aluminium")]
        return els
    shapes = {f"*-{part}": {"base": shp(f"end-exitdoor-{part}", all_faces(exitdoor(part)))} for part in ("lower", "upper")}
    blk("end-exitdoor", {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": shapes, "lightAbsorption": 99, "resistance": 20, "drops": [], "sounds": METAL,
        "behaviors": threshold("endexit"),
    }, "The End: a grey steel door under an EXIT sign, a push bar and wired glass on every face (it fits a wall either "
       "way). Kind endexit; indestructible. Also used in Level 1, the Hub and Level !")
    name("end-exitdoor-*", "EXIT Door")

    def staffdoor(part):
        els = [cube_el("staffdoor"), bx("JambW", (0, 0, -0.4), (1, 16, 0), "maple-dark"), bx("JambE", (15, 0, -0.4), (16, 16, 0), "maple-dark")]
        if part == "lower":
            els += [bx("Kick", (1.2, 0, -0.15), (14.8, 4.5, 0), "brushed"),
                    bx("Rose", (12, 13.2, -0.3), (13.4, 15.4, 0), "brushed"), bx("Lever", (10, 14, -1.3), (13.2, 14.7, -0.6), "brushed"),
                    bx("LeverNeck", (12.4, 14, -0.9), (13, 14.7, -0.3), "brushed")]
        else:
            els += [bx("Head", (0, 15, -0.4), (16, 16, 0), "maple-dark"),
                    faces_box("Plate", (3, 6, -0.2), (13, 9, 0), {"north": "staffplate", "east": "brushed", "west": "brushed", "up": "brushed", "down": "brushed"}, uv=(0, 0, 16, 16))]
            els[-1]["faces"]["north"]["uv"] = list(STAFFPLATE_UV)
        return els
    shapes = {f"*-{part}": {"base": shp(f"end-staffdoor-{part}", all_faces(staffdoor(part)))} for part in ("lower", "upper")}
    blk("end-staffdoor", {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, "lightAbsorption": 99, "resistance": 20, "drops": [], "sounds": WOOD,
        "behaviors": threshold("locked"),
    }, "The End: a maple-veneer staff door marked EMPLOYEES ONLY (on every face). Locked; indestructible")
    name("end-staffdoor-*", "Staff Door")

    # The vent: a louvred grille 12 x 8, recessed 2 into a wall, dark behind
    def vent():
        els = [faces_box("Back", (0, 0, 2), (16, 16, 16), {"north": "ventdark"}),
               bx("RecessW", (2, 4, 0), (2.01, 12, 2), "duct"), bx("RecessE", (13.99, 4, 0), (14, 12, 2), "duct"),
               bx("RecessT", (2, 11.99, 0), (14, 12, 2), "duct"), bx("RecessB", (2, 4, 0), (14, 4.01, 2), "duct"),
               bx("FlangeT", (1.5, 12, -0.4), (14.5, 12.6, 0), "vent"), bx("FlangeB", (1.5, 3.4, -0.4), (14.5, 4, 0), "vent"),
               bx("FlangeW", (1.5, 4, -0.4), (2.1, 12, 0), "vent"), bx("FlangeE", (13.9, 4, -0.4), (14.5, 12, 0), "vent")]
        for k in range(6):
            y = 4.75 + k * 1.3
            els.append(rot(bx(f"Louvre{k}", (2, y - 0.2, 0.2), (14, y + 0.2, 1.8), "vent"), rx=-30, origin=(8, y, 1)))
        for k, (x, y) in enumerate(((2.3, 11.9), (13.2, 11.9), (2.3, 3.5), (13.2, 3.5))):
            els.append(bx(f"Screw{k}", (x, y, -0.55), (x + 0.5, y + 0.5, -0.4), "brushed"))
        return els
    front = vent()
    kinds = {}
    shapes = {}
    for b in ("block",):
        side = BACKINGS[b][0]
        frame = [faces_box("FaceW", (0, 0, 0), (2, 16, 2), {"north": side, "east": side, "west": side, "up": side, "down": side}),
                 faces_box("FaceE", (14, 0, 0), (16, 16, 2), {"north": side, "east": side, "west": side, "up": side, "down": side}),
                 faces_box("FaceT", (2, 12, 0), (14, 16, 2), {"north": side, "up": side, "down": side}),
                 faces_box("FaceB", (2, 0, 0), (14, 4, 2), {"north": side, "up": side, "down": side}),
                 faces_box("Body", (0, 0, 2), (16, 16, 16), {"east": side, "west": side, "south": side, "up": side, "down": side})]
        shapes.update(by_side("*", shp("end-vent", frame + front)))
    blk("end-vent", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-north"), "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": shapes, "lightAbsorption": 99, "resistance": 20, "drops": [], "sounds": METAL,
        "behaviors": threshold("endvent"),
    }, "The End: a louvred vent grille in the side-named face of a painted block wall (rel 3), at the top of a steel ladder: the way to Level 94. "
       "Kind endvent; indestructible")
    name("end-vent-*", "Vent")

    # The free-standing doorframe in Level 4: aged oak, a doorway with no door; something shimmers in it
    def frame(part):
        els = [bx("JambW", (0, 0, 6), (2, 16, 10), "oakaged"), bx("JambE", (14, 0, 6), (16, 16, 10), "oakaged"),
               bx("CasingWN", (-0.6, 0, 5.4), (2.6, 16, 6), "oakaged"), bx("CasingEN", (13.4, 0, 5.4), (16.6, 16, 6), "oakaged"),
               bx("CasingWS", (-0.6, 0, 10), (2.6, 16, 10.6), "oakaged"), bx("CasingES", (13.4, 0, 10), (16.6, 16, 10.6), "oakaged")]
        if part == "lower":
            els += [bx("PlinthW", (-0.8, 0, 5.2), (2.8, 3, 10.8), "oakaged"), bx("PlinthE", (13.2, 0, 5.2), (16.8, 3, 10.8), "oakaged"),
                    faces_box("Membrane", (2, 0, 8), (14, 16, 8), {"north": "membrane", "south": "membrane"}, glow_by_face={"north": 60, "south": 60})]
        else:
            els += [bx("Head", (0, 14, 6), (16, 16, 10), "oakaged"), bx("HeadCasingN", (-0.6, 13.4, 5.4), (16.6, 16.6, 6), "oakaged"),
                    bx("HeadCasingS", (-0.6, 13.4, 10), (16.6, 16.6, 10.6), "oakaged"),
                    faces_box("Membrane", (2, 0, 8), (14, 14, 8), {"north": "membrane", "south": "membrane"}, glow_by_face={"north": 60, "south": 60})]
        return els
    shapes = {}
    for part in ("lower", "upper"):
        shapes.update(by_side(f"*-{part}", shp(f"end-frame-{part}", frame(part))))
    coll = {}
    coll.update(boxes_by_side("*-lower", [(0, 0, 0.36, 0.13, 1, 0.64), (0.87, 0, 0.36, 1, 1, 0.64)]))
    coll.update(boxes_by_side("*-upper", [(0, 0, 0.36, 0.13, 1, 0.64), (0.87, 0, 0.36, 1, 1, 0.64), (0, 0.87, 0.36, 1, 1, 0.64)]))
    blk("end-frame", {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-lower-north"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "renderpass": "Transparent", "resistance": 20, "drops": [],
        "textures": {"membrane": {"base": "block/end/membrane0", "alternates": [{"base": "block/end/membrane1"}, {"base": "block/end/membrane2"}]}},
        "collisionbox": None, "selectionboxesByType": coll,
        "sounds": dict(WOOD, ambient="backrooms:ambient/end/roomtone", ambientBlockCount=1),
    }, "The End's way in from Level 4: a free-standing doorway of aged oak with no door, standing alone on the carpet, "
       "the room shimmering through it (its threshold is the tile, Unders.EndFrame). Indestructible")
    name("end-frame-*", "Doorway")

    # Level 11's closed-down bookstore: its glass door and its papered windows
    def storedoor(part):
        # The face of the door on its north side: aluminium stiles and rails, dark glass, the poster taped inside it
        els = [bx("StileW", (0, 0, -0.3), (2, 16, 0.6), "aluminium"), bx("StileE", (14, 0, -0.3), (16, 16, 0.6), "aluminium"),
               faces_box("Glass", (2, 0, 0.1), (14, 16, 0.2), {"north": "storeglass"})]
        if part == "lower":
            els += [bx("KickRail", (2, 0, -0.3), (14, 3.5, 0.6), "aluminium"), bx("Pull", (11.6, 8, -2.2), (12.4, 16, -1.4), "brushed"),
                    bx("PullFoot", (11.6, 8, -1.4), (12.4, 8.8, -0.3), "brushed")]
        else:
            els += [bx("TopRail", (2, 14, -0.3), (14, 16, 0.6), "aluminium"), bx("Pull", (11.6, 0, -2.2), (12.4, 6, -1.4), "brushed"),
                    bx("PullFoot", (11.6, 5.2, -1.4), (12.4, 6, -0.3), "brushed"),
                    faces_box("Poster", (3.5, 1.5, 0.3), (12.5, 12.5, 0.35), {"north": "poster-near"}, uv=(0, 0, 16, 16))]
        return els
    shapes = {}
    for part in ("lower", "upper"):
        core = faces_box("Shop", (0.6, 0, 0.6), (15.4, 16, 15.4), {f: "shopdark" for f in ("north", "east", "south", "west")})
        shapes[f"*-{part}"] = {"base": shp(f"end-storedoor-{part}", [core] + all_faces(storedoor(part))[1:])}
    blk("end-storedoor", {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": shapes, "lightAbsorption": 99, "renderpass": "Transparent", "resistance": 20, "drops": [], "sounds": GLASS,
        "behaviors": threshold("endbookstore"),
    }, "Level 11: the glass door of a closed-down bookstore, dark inside, a THE END IS NEAR poster taped behind the "
       "glass, a pull handle (on every face, so it fits a wall either way). Kind endbookstore; indestructible")
    name("end-storedoor-*", "Shop Door")

    window = [faces_box("Glass", (0, 0, 7.8), (16, 16, 8.2), {"north": "storeglass", "south": "storeglass"}),
              bx("Sill", (0, 0, 6.5), (16, 1.5, 9.5), "aluminium"), bx("Head", (0, 15, 7), (16, 16, 9), "aluminium"),
              faces_box("Poster", (1.5, 3, 8.25), (9.5, 12, 8.3), {"north": "poster-fixtures", "south": "pallet"}, uv=(0, 0, 16, 16)),
              rot(faces_box("Poster2", (10.5, 4, 8.25), (15, 10, 8.3), {"north": "poster-closing", "south": "pallet"}, uv=(0, 0, 16, 16)), rz=-3)]
    shapes = by_side("*", shp("end-storewindow", window))
    blk("end-storewindow", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": inv("*-north"), "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "renderpass": "Transparent", "resistance": 4, "sounds": GLASS,
        "collisionboxByType": {f"*-{s}": cuboid((0, 0, 0.4, 1, 1, 0.6), s) for s in SIDES},
        "selectionboxByType": {f"*-{s}": cuboid((0, 0, 0.4, 1, 1, 0.6), s) for s in SIDES},
        "drops": drops(("glassshard", 2, 1), (PAPER, 0.5, 0)),
    }, "Level 11: the bookstore's front window, papered inside with yellow and pink closing-down posters (read from the side named)")
    name("end-storewindow-*", "Shop Window")


# ======================= Decay and the Snowfield =======================

def decay():
    rng = random.Random(seed_of("rubble"))
    shelf = []
    for k in range(6):
        x, z = rng.uniform(1, 6), rng.uniform(1, 13)
        el = bx(f"Board{k}", (x, 0.2 + k * 0.7, z), (x + 10, 1.2 + k * 0.7, z + 2.2), "maple")
        shelf.append(rot(el, rx=rng.uniform(-8, 8), ry=rng.uniform(-60, 60), origin=(x + 5, 0.7 + k * 0.7, z + 1.1)))
    shelf.append(rot(bx("SidePanel", (1, 0, 3), (15, 1.5, 13), "maple"), rx=0, rz=8, origin=(1, 0, 8)))
    shelf.append(rot(bx("Broken", (6, 0, 1), (8, 3.5, 4), "particleboard"), ry=25))
    shelf.append(faces_box("Dust", (0.5, 0.02, 0.5), (15.5, 0.08, 15.5), {"up": "dust"}))
    ceiling = []
    for k, (x, z, ang, tilt) in enumerate(((1, 1, 10, 4), (7, 6, -25, -9), (3, 8, 40, 14))):
        el = faces_box(f"Tile{k}", (x, 0.2 + k * 0.6, z), (x + 7.5, 0.9 + k * 0.6, z + 7.5), {"up": "ceiling-plain", "down": "ceiling-plain", "north": "particleboard", "south": "particleboard", "east": "particleboard", "west": "particleboard"})
        ceiling.append(rot(el, rx=tilt, ry=ang, origin=(x + 3.75, 0.5 + k * 0.6, z + 3.75)))
    ceiling += [rot(bx("TbarA", (1, 0.4, 7.4), (11, 1.4, 8), "tbar"), ry=-15, rz=6, origin=(6, 0.9, 7.7)),
                rot(bx("TbarB", (10.6, 0.4, 7.4), (16, 1.4, 8), "tbar"), ry=35, origin=(10.8, 0.9, 7.7))]
    shapes = {"*-shelf": {"base": shp("end-rubble-shelf", shelf)}, "*-ceiling": {"base": shp("end-rubble-ceiling", ceiling)}}
    blk("end-rubble", {
        "variantgroups": [{"code": "kind", "states": ["shelf", "ceiling"]}],
        "creativeinventory": inv("*-shelf"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": shapes, **OPEN, "resistance": 1, "sounds": WOOD,
        "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.25, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.25, "z2": 1},
        "dropsByType": {"*-shelf": drops((STICK, 3, 1), (PLANK, 0.5, 0.5)), "*": drops((STICK, 1, 1), ("metalbracket", 0.3, 0.3), ("rottenwood", 0.3, 0.3))},
    }, "The End: collapsed shelving (boards, a fallen side panel), and fallen ceiling (broken tiles, a bent T-bar)")
    name("end-rubble-shelf", "Collapsed Shelving")
    name("end-rubble-ceiling", "Fallen Ceiling")

    trunk = [bx("Trunk", (6, 0, 6), (10, 16, 10), "bark"), bx("Knot", (9.9, 8.6, 7), (10.7, 9.2, 8.4), "bark"),
             faces_box("KnotSnow", (9.9, 9.2, 7), (10.8, 9.6, 8.4), {"up": "snow", "east": "snow", "north": "snow", "south": "snow"}),
             bx("Knot2", (5.4, 3.6, 8), (6.1, 4.2, 9.2), "bark"),
             faces_box("Knot2Snow", (5.3, 4.2, 8), (6.1, 4.6, 9.2), {"up": "snow", "west": "snow", "north": "snow", "south": "snow"})]
    top = [bx("Trunk", (6.4, 0, 6.4), (9.6, 9, 9.6), "bark"), bx("Leader", (7, 9, 7), (9, 15, 9), "bark"),
           faces_box("TopSnow", (6.9, 15, 6.9), (9.1, 15.8, 9.1), {"up": "snow", "north": "snow", "south": "snow", "east": "snow", "west": "snow"})]
    for k in range(6):
        ang = k * 60 + 15
        y = 2 + k * 2
        length = 8.5 - (k % 3)
        w = 1.5 if k < 3 else 1.0
        # VS turns an element about Z first, then Y, then X: tilt it out about Z, then swing it round about Y
        br = bx(f"Branch{k}", (8 - w / 2, y, 8 - w / 2), (8 + w / 2, y + length, 8 + w / 2), "bark")
        top.append(rot(br, rz=-55, ry=ang, origin=(8, y, 8)))
        tip = bx(f"Tuft{k}", (8 - 0.9, y + length - 1.6, 8 - 0.9), (8 + 0.9, y + length - 0.6, 8 + 0.9), "snow")
        top.append(rot(tip, rz=-55, ry=ang, origin=(8, y, 8)))
    blk("end-tree", {
        "variantgroups": [{"code": "part", "states": ["trunk", "top"]}],
        "creativeinventory": inv("*-trunk"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {"*-trunk": {"base": shp("end-tree-trunk", trunk)}, "*-top": {"base": shp("end-tree-top", top)}},
        **OPEN, "resistance": 3, "sounds": WOOD,
        "collisionbox": {"x1": 0.37, "y1": 0, "z1": 0.37, "x2": 0.63, "y2": 1, "z2": 0.63},
        "selectionboxByType": {"*-trunk": {"x1": 0.37, "y1": 0, "z1": 0.37, "x2": 0.63, "y2": 1, "z2": 0.63},
                               "*-top": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 1, "z2": 0.9}},
        "drops": drops((STICK, 3, 1), (FIREWOOD, 1, 0.5)),
    }, "The End's Snowfield: a bare tree standing between the shelves, snow on its ledges (trunk, any number; top)")
    name("end-tree-*", "Bare Tree")


# ======================= Items =======================

ITEM_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}
BOTTLE_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": -22.6, "y": -45.3, "z": 0}, "origin": {"x": 0.5, "y": 0.3, "z": 0.5}, "scale": 2.4},
    "fpHandTransform": {"translation": {"x": 0, "y": 0.1, "z": 0.4}, "rotation": {"x": 0, "y": -30, "z": 0}, "scale": 2},
    "tpHandTransform": {"translation": {"x": -0.85, "y": -0.5, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.8},
    "groundTransform": {"rotation": {"x": 0, "y": -45, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.8},
}
ITEMS = []


def itm(code, data, comment):
    write_json(os.path.join(ASSETS, "itemtypes", "end", code + ".json"), dict({"code": code}, **data), comment)
    ITEMS.append(code)


def items():
    item_textures()
    itm("end-cataloguecard", ground_storable(dict({
        "class": "BackroomsCatalogueCard", "maxstacksize": 16, "texture": {"base": "item/end/cataloguecard"},
        "creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 300,
        "combustibleProps": {"burnTemperature": 600, "burnDuration": 3},
    }, **ITEM_TRANSFORMS)), "A card from The End's card catalogue: read it (right-click) and it marks the nearest way out on the map")

    # Memory Juice: a small unlabelled bottle, cloudy amber, a cork; a few boxes in item space (0-16)
    def box(nm, frm, to, tex, top=True):
        faces = ("north", "east", "south", "west", "up", "down") if top else ("north", "east", "south", "west")
        return bx(nm, frm, to, tex, faces=faces)
    els = [box("Body", (6, 0, 6.5), (10, 6, 9.5), "glass"),
           box("Shoulder", (6.5, 6, 7), (9.5, 7, 9), "glass"),
           box("Neck", (7.3, 7, 7.3), (8.7, 8.6, 8.7), "glass", top=False),
           box("Lip", (7.1, 8.6, 7.1), (8.9, 9.1, 8.9), "glass", top=False),
           box("Cork", (7.4, 8.6, 7.4), (8.6, 10.2, 8.6), "cork")]
    write_json(os.path.join(ASSETS, "shapes", "item", "end", "memoryjuice.json"),
               {"textureWidth": 16, "textureHeight": 16,
                "textures": {"glass": "backrooms:item/end/memoryjuice-glass", "cork": "backrooms:item/end/memoryjuice-cork"},
                "elements": els})
    itm("end-memoryjuice", ground_storable(dict({
        "class": "BackroomsMemoryJuice", "maxstacksize": 8, "shape": {"base": "item/end/memoryjuice"},
        "creativeinventory": {"general": ["*"], "items": ["*"]},
        "nutritionProps": {"satiety": 20, "foodcategory": "NoNutrition"}, "materialDensity": 1000,
    }, **BOTTLE_TRANSFORMS), height=0.625), "Memory Juice: drink it for +0.2 stability and a while of feeling at home. The Junkies' currency")


# ======================= Sounds =======================

SOUNDS = []


def sounds():
    import numpy as np
    from gen_entity_sounds import RATE, band, place, reverb, seconds, thud
    from gen_level_sounds import write as write_ogg

    F = "ambient/end"

    def write(name, signal, peak, fade=True):
        write_ogg(F, name, signal, peak, fade)
        SOUNDS.append(name)

    def norm(x):
        return x / max(1e-9, np.max(np.abs(x)))

    rng = np.random.default_rng(1601)

    # Room tone: a 20 s loop of near silence. Every tone has a whole number of cycles in the loop, and the noise is
    # filtered round the loop (the FFT filter is circular), so it joins without a seam.
    t = seconds(20)
    tick = np.sin(2 * np.pi * 120 * t) + 0.35 * np.sin(2 * np.pi * 240 * t) + 0.15 * np.sin(2 * np.pi * 360 * t)
    tick *= 0.9 + 0.1 * np.sin(2 * np.pi * t / 5)
    hiss = norm(band(rng.normal(size=len(t)), 7000, 9000))
    write("roomtone", 0.12 * tick + 0.5 * hiss * (0.85 + 0.15 * np.sin(2 * np.pi * t / 4)), 0.3, fade=False)

    # The CRT's whine: an 11 kHz flyback line, a 60 Hz hum and its harmonics, a faint crackle; a 4 s loop
    t = seconds(4)
    hum = sum(a * np.sin(2 * np.pi * f * t) for f, a in ((60, 1.0), (120, 0.55), (180, 0.35), (240, 0.2), (300, 0.12)))
    whine = np.sin(2 * np.pi * 11000 * t) * (0.9 + 0.1 * np.sin(2 * np.pi * 2 * t))
    crackle = norm(band(rng.normal(size=len(t)), 2000, 6000))
    write("crtbuzz", 0.45 * hum + 0.35 * whine + 0.08 * crackle, 0.7, fade=False)

    # Switching on: the degauss thunk (a low boing pulsed at 60 Hz) and the whine rising into hearing
    t = seconds(1.2)
    thunk = np.sin(2 * np.pi * 55 * t) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 60 * t))) * np.exp(-t * 6)
    f = 1500 + 9500 * np.minimum(1, t / 0.9) ** 0.6
    rise = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.minimum(1, t / 0.5) * 0.3
    write("crton", thunk + rise + 0.1 * band(rng.normal(size=len(t)), 200, 2000) * np.exp(-t * 20), 0.8)

    # Static: noise in the 1-6 kHz band, wavering, fading, and a click as the tube dies
    t = seconds(2.5)
    st = norm(band(rng.normal(size=len(t)), 1000, 6000))
    st *= np.minimum(1, t / 0.05) * np.clip((2.3 - t) / 1.6, 0, 1) * (0.75 + 0.25 * np.sin(2 * np.pi * 7 * t))
    click = np.zeros(len(t))
    place(click, np.sin(2 * np.pi * 900 * seconds(0.02)) * np.exp(-seconds(0.02) * 250), 2.32)
    write("crtstatic", st + 0.8 * click, 0.6)

    # A shelf creaking: particle board flexing in stick-slip pulses at a slowly changing rate, then a tick
    t = seconds(1.5)
    out = np.zeros(len(t))
    pos = 0.1
    while pos < 1.15:
        rate = 40 + 30 * math.sin(pos * 5)
        g = np.exp(-seconds(0.02) * 300) * np.sin(2 * np.pi * rng.uniform(260, 420) * seconds(0.02))
        place(out, g * (0.5 + 0.5 * math.sin(math.pi * (pos - 0.1) / 1.05)), pos)
        pos += 1 / rate * rng.uniform(0.7, 1.3)
    out = band(out, 120, 2500)
    place(out, 0.8 * np.max(np.abs(out)) * norm(thud(0.08, 700, rng, 0.6)), 1.3)
    write("shelfcreak", reverb(out, 0.25), 0.55)

    # A book falling on carpet: a soft thump, the pages riffling as it settles
    t = seconds(0.8)
    out = np.zeros(len(t))
    place(out, band(thud(0.25, 85, rng, 0.15), 40, 1200), 0.03)
    n = int(0.012 * RATE)
    for k in range(9):
        burst = band(rng.normal(size=n), 2500, 8000) * np.hanning(n)
        place(out, 0.18 * burst * (1 - k / 10), 0.09 + k * 0.022 + rng.uniform(0, 0.006))
    write("bookfall", reverb(out, 0.2), 0.6)

    # A chair dragged a short way over carpet: muffled scraping in pulses, slowing to a stop
    t = seconds(1.2)
    scrape = band(rng.normal(size=len(t)), 250, 2200)
    pulses = 0.55 + 0.45 * np.abs(np.sin(2 * np.pi * (24 * t - 6 * t * t)))
    out = scrape * pulses * np.minimum(1, t / 0.08) * np.clip((1.0 - t) / 0.3, 0, 1)
    place(out, 0.4 * np.max(np.abs(out)) * norm(band(thud(0.1, 120, rng, 0.2), 60, 1500)), 1.02)
    write("chairscrape", reverb(out, 0.3), 0.5)

    # A page turning: a soft swoosh with a crinkle at the start and a flap at the end
    t = seconds(0.6)
    out = 0.6 * norm(band(rng.normal(size=len(t)), 1200, 9000)) * np.sin(np.pi * np.clip(t / 0.5, 0, 1)) ** 2
    for k in range(5):
        place(out, 0.3 * norm(band(rng.normal(size=int(0.004 * RATE)), 3000, 10000)), 0.03 + k * 0.03)
    n = int(0.03 * RATE)
    place(out, 0.4 * norm(band(rng.normal(size=n), 300, 3000)) * np.hanning(n), 0.48)
    write("pageturn", out, 0.45)

    # A gondola shelf coming down: a crack, the crash, boards clattering and settling
    t = seconds(2.0)
    out = np.zeros(len(t))
    place(out, norm(band(rng.normal(size=int(0.03 * RATE)), 1500, 9000)) * np.exp(-seconds(0.03) * 120), 0.02)
    place(out, 1.2 * thud(0.6, 60, rng, 0.8), 0.12)
    place(out, 0.7 * norm(band(rng.normal(size=int(0.5 * RATE)), 200, 5000)) * np.exp(-seconds(0.5) * 8), 0.12)
    when = 0.3
    for k in range(10):
        place(out, (0.7 - k * 0.055) * thud(0.12, rng.uniform(250, 700), rng, 0.6), when)
        when += rng.uniform(0.05, 0.16)
    write("shelfcrash", reverb(out, 0.4), 0.9)

    # A breaker: one big clunk, and the ballast tick under it stopping
    t = seconds(0.8)
    out = 0.15 * np.sin(2 * np.pi * 120 * t) * (t < 0.12)
    place(out, thud(0.3, 75, rng, 0.9), 0.1)
    place(out, 0.5 * np.sin(2 * np.pi * 2400 * seconds(0.03)) * np.exp(-seconds(0.03) * 150), 0.1)
    write("breaker", reverb(out, 0.5), 0.85)

    # A distortion: a rumble rising from 30 Hz, the shelves rattling, a swell of pressure, then silence all at once
    t = seconds(5)
    cut = 4.4
    f = 30 + 30 * (t / cut) ** 2
    rumble = norm(np.sin(2 * np.pi * np.cumsum(f) / RATE) + 0.4 * norm(band(rng.normal(size=len(t)), 20, 120)))
    swell = norm(band(rng.normal(size=len(t)), 40, 400))
    grow = np.clip(t / cut, 0, 1) ** 1.5
    out = (0.8 * rumble + 0.5 * swell) * grow
    when = 0.6
    while when < cut - 0.05:
        place(out, (0.15 + 0.45 * when / cut) * thud(0.05, rng.uniform(400, 900), rng, 0.8), when)
        when += rng.uniform(0.03, 0.25) * (1.2 - when / cut)
    c = int(cut * RATE)
    n = int(0.004 * RATE)
    out[c - n:c] *= np.linspace(1, 0, n)
    out[c:] = 0
    write("distortion", out, 0.9)

    # Wind over open snow: a 12 s loop, gusts on slow cycles that fit the loop exactly
    t = seconds(12)
    wind = norm(band(rng.normal(size=len(t)), 150, 1400))
    hiss = norm(band(rng.normal(size=len(t)), 2000, 6000))
    gust = 0.55 + 0.25 * np.sin(2 * np.pi * t / 6 + 0.7) + 0.15 * np.sin(2 * np.pi * t / 4 + 2.1) + 0.05 * np.sin(2 * np.pi * t / 1.5)
    write("snowwind", wind * gust + 0.2 * hiss * gust ** 2, 0.5, fade=False)

    # Echo steps: two or three soft footsteps on carpet, a little behind you, slightly late
    t = seconds(1.5)
    out = np.zeros(len(t))
    n = int(0.18 * RATE)
    for k, at in enumerate((0.05, 0.58, 1.1)):
        step = norm(band(thud(0.18, 70 + 8 * k, rng, 0.1), 40, 900)) + 0.15 * norm(band(rng.normal(size=n), 600, 2500)) * np.exp(-seconds(0.18) * 40)
        place(out, step * (1 - 0.25 * k), at + rng.uniform(0, 0.03))
    write("echostep", reverb(out, 0.35), 0.45)

    # A heavy bookcase set down on carpet: a deep thud, a woody knock, a shudder of shelves
    t = seconds(0.7)
    out = np.zeros(len(t))
    place(out, thud(0.45, 48, rng, 0.25), 0.02)
    place(out, 0.4 * thud(0.1, 320, rng, 0.5), 0.03)
    for k in range(4):
        place(out, 0.12 * thud(0.04, rng.uniform(500, 900), rng, 0.6), 0.12 + k * 0.05)
    write("turnaround", reverb(out, 0.3), 0.8)


# ======================= Lang =======================

TAB, NL = "\t", "\n"


def lang():
    LANG.update({
        "level-16": "The End",
        "levelhint-16": "You found the exit. Didn't you?",
        "levelname-16": "The End",
        "level-1601": "The End: a fake reality",
        "levelhint-1601": "This is not where you think it is.",
        "endexit-locked": "The EXIT sign glows. The door does not open.",
        "endexit-out": "The door opens. Somewhere else is on the other side.",
        "endexit-arrive": "You push the bar, and the door swings shut behind you on a library that goes on forever.",
        "endframe": "You step through the doorway. When you look back, there is nothing there.",
        "endbookstore": "The bell over the door doesn't ring. Inside, the shelves go back much further than the shop.",
        "endvent": "You crawl into the dark. The vent ends in open air, and you are falling.",
        "endterminal-on": "The screen flickers on with a low buzz. In white letters: THE END. Then static, and nothing.",
        "endterminal-marked": "Before it dies, the screen shows a plan of the floor. You remember where the doors were.",
        "endterminal-dead": "The screen stays dark. It will not turn on again.",
        "endterminal-party": "The screen flickers on. It does not say THE END. It says =)",
        "waypoint-endterminal": "A way out of The End (from a computer)",
        "endparty-taken": "Hands take you by the arms. Someone is laughing. \"Don't leave yet, friend! =)\"",
        "enddistortion": "The floor shakes. For a moment you are somewhere else.",
        "enddistortion-through": "You fall forward into the wall, and through it.",
        "endfake-door": "The door opens onto somewhere real.",
        "endfake-shut": "The door is painted shut. It was never a door.",
        "endjunkie-nojuice": "\"Got any juice? No? Then what are you doing here.\"",
        "endjunkie-greet": "\"Oh, you have some. Sit down. Stay a while.\"",
        "waypoint-note-endexit": "A way out of The End (from a catalogue card)",
        "note-endexit-1": "The card is typed: EXIT, {0}, about {1} paces. Someone has underlined it twice.",
        "note-endexit-2": "A catalogue card, filed under E: \"Exit: see {0}, {1} paces.\"",
        "note-endexit-3": "Someone has written on the back of the card: \"{0}. {1} paces. It opened for me.\"",
        "item-end-cataloguecard": "Catalogue Card",
        "itemdesc-end-cataloguecard": "From The End's card catalogue. Read it to mark the nearest way out on your map.",
        "item-end-memoryjuice": "Memory Juice",
        "itemdesc-end-memoryjuice": "An unlabelled bottle of something cloudy and amber. For a while after you drink it, everything feels like home. The Junkies of The End will trade with anyone who carries some.",
        "blockhelp-endterminal": "Turn on",
    })


def merge_lang():
    """Adds the names to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text_ = f.read()
    new_lines = []
    for key, value in LANG.items():
        line = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text_):
            text_ = pattern.sub(lambda m: line + m.group(1), text_, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text_.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text_ = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    json.loads(re.sub(r"^\s*//.*$", "", text_, flags=re.M))  # still valid
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text_)
    print(f"lang: {len(LANG)} keys merged ({len(new_lines)} new)")


# ======================= Checks =======================

GAME = os.path.join(os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory")), "assets")


def asset_exists(kind, path, ext):
    domain, rel = path.split(":", 1) if ":" in path else ("backrooms", path)
    if domain == "backrooms":
        return os.path.exists(os.path.join(ASSETS, kind, rel + ext))
    return any(os.path.exists(os.path.join(GAME, d, kind, rel + ext)) for d in ("survival", "game"))


_GAME_FILES = {}


def game_files(typ):
    """The base names of the game's block or item type files (a code's first segment is usually one of them)."""
    if typ not in _GAME_FILES:
        names = set()
        for d in ("survival", "game"):
            for root, _, files in os.walk(os.path.join(GAME, d, "blocktypes" if typ == "block" else "itemtypes")):
                names.update(os.path.splitext(fn)[0] for fn in files)
        _GAME_FILES[typ] = names
    return _GAME_FILES[typ]


def check():
    """Every texture a shape names resolves; every shape, texture and sound a block or item type names exists; every
    drop is a known block or item of ours or of the game's."""
    problems = []
    for nm in SHAPES:
        data = json.load(open(os.path.join(ASSETS, "shapes", "block", "end", nm + ".json"), encoding="utf-8"))
        used = {f["texture"][1:] for e in data["elements"] for f in e["faces"].values()}
        for k in used:
            if k not in data["textures"]:
                problems.append(f"shape {nm}: #{k} undefined")
        for k, p in data["textures"].items():
            if not asset_exists("textures", p, ".png"):
                problems.append(f"shape {nm}: texture {k} -> {p}")
    ours = set()
    for kind in ("blocktypes", "itemtypes"):
        for root, _, files in os.walk(os.path.join(ASSETS, kind)):
            for fn in files:
                raw = open(os.path.join(root, fn), encoding="utf-8").read()
                for m in re.finditer(r'^\s*"?code"?\s*:\s*"([^"]+)"', raw, re.M):
                    ours.add(m.group(1))
                    break
    for kind, codes in (("blocktypes", CODES), ("itemtypes", ITEMS)):
        for code in codes:
            raw = open(os.path.join(ASSETS, kind, "end", code + ".json"), encoding="utf-8").read()
            data = json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
            for m in re.finditer(r'"base":\s*"([^"]+)"', raw):
                p = m.group(1)
                rel = p.split(":", 1)[-1]
                is_shape = rel.startswith(("block/end/end-", "item/end/memoryjuice")) and not rel.startswith("item/end/memoryjuice-")
                ok = asset_exists("shapes", p, ".json") if is_shape else asset_exists("textures", p, ".png")
                if not ok:
                    problems.append(f"{kind} {code}: {p}")
            for m in re.finditer(r'"ambient":\s*"([^"]+)"', raw):
                p = m.group(1).split(":", 1)[-1]
                if not os.path.exists(os.path.join(ASSETS, "sounds", p + ".ogg")):
                    problems.append(f"{kind} {code}: sound {p}")
            for m in re.finditer(r'\{"type": "(item|block)", "code": "([^"]+)"', json.dumps(data)):
                typ, c = m.groups()
                dom, path = c.split(":", 1) if ":" in c else ("backrooms", c)
                if dom == "game":
                    if path.split("-")[0] not in game_files(typ):
                        problems.append(f"{kind} {code}: drop {typ} {c} not in the game")
                elif path not in ours and not any(path.startswith(o + "-") for o in ours):
                    problems.append(f"{kind} {code}: drop {typ} {c} unknown")
    for p in problems:
        print("CHECK:", p)
    print(f"check: {len(CODES)} blocktypes, {len(SHAPES)} shapes, {len(ITEMS)} itemtypes, {len(SOUNDS)} sounds, "
          f"{len(problems)} problems")
    return not problems


def generate():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    textures()
    structure()
    shelving()
    desks()
    furniture()
    stock()
    atrium()
    wall_words()
    doors_and_ways()
    decay()
    items()
    sounds()
    lang()
    merge_lang()
    return check()


if __name__ == "__main__":
    sys.exit(0 if generate() else 1)
