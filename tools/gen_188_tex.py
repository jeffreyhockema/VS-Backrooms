"""Level 188, the Courtyard of Windows: every texture (block/188/, item/188/, gui/188/). Called from gen_188.py.

Pale warm render and small square windows with white roller blinds, mossy lawns and a weathered wooden deck under a
black sky; inside, a budget hotel in greys: charcoal loop-pile corridors, grey cut-pile rooms, white walls with one
slate-blue headboard wall, grey-oak laminate doors. Pictures (the places seen through the windows, the courtyard
seen from elsewhere, the figures) are drawn large and reduced, so they stay soft at 32 px a block.
"""
import math
import os
import random
import zlib

from PIL import Image, ImageDraw, ImageFilter

import texlib

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures")
S = 32
WRITTEN = []


def hexc(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# The manifest's palette
PAVER = hexc(0xA8A49B)
MOSS = hexc(0x4E6B35)
TURF = hexc(0x3B5530)
BLADE = hexc(0x5F7F45)
DECK = hexc(0x7A5A3C)
IRON = hexc(0x3E3F42)
SHAFT = hexc(0x050506)
RENDER = hexc(0xC9C4B8)
ROOF = hexc(0x3B3C3E)
NOTHING = hexc(0x030304)
SKY = hexc(0x020203)
CARPET_C = hexc(0x3A3D42)
LATTICE = hexc(0x55595F)
CARPET_R = hexc(0x6E6F70)
PORCELAIN = hexc(0x9C9A95)
STAIRPAINT = hexc(0x8C8C88)
VINYL = hexc(0xB9B8B3)
ROOMWHITE = hexc(0xE3E1DC)
FEATURE = hexc(0x4D5D6E)
CEILING = hexc(0xEDEDEA)
ALU = hexc(0x3D4043)
BLIND = hexc(0xECE9E0)
FIGURE = hexc(0x0B0B0D)
LAMINATE = hexc(0x8A7D6E)
FASCIA = hexc(0xB49A78)
SKIN = hexc(0x1C1C20)


def seed_of(name):
    return zlib.crc32(name.encode()) & 0xFFFFFF


def clamp(v):
    return max(0, min(255, int(round(v))))


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(clamp(v * k) for v in c[:3])


def _save(img, rel):
    path = os.path.join(TEX, *rel.split("/")) + ".png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    WRITTEN.append(rel)


def save(img, name):
    _save(img, "block/188/" + name)


def save_item(img, name):
    _save(img, "item/188/" + name)


def flat(c, a=255, size=S):
    return Image.new("RGBA", (size, size), tuple(c[:3]) + (a,))


def noisy(base, amount, key, size=S, alpha=255):
    rng = random.Random(seed_of(key))
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            d = rng.uniform(-amount, amount)
            px[x, y] = tuple(clamp(v + d) for v in base[:3]) + (alpha,)
    return img


def soft(img, key, amount, octaves=3):
    """Tileable soft unevenness (a periodic noise field), +-amount in brightness."""
    field = texlib._periodic_noise(seed_of(key), octaves)
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            d = field[y % S][x % S] * amount
            px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d), a)
    return img


def speckle(img, key, cols, count, alpha=1.0):
    rng = random.Random(seed_of(key))
    px = img.load()
    w, h = img.size
    for _ in range(count):
        x, y = rng.randrange(w), rng.randrange(h)
        c = rng.choice(cols)
        r, g, b, a = px[x, y]
        px[x, y] = mix((r, g, b), c, alpha) + (a,)
    return img


def hline(img, y, col, alpha=1.0, x0=0, x1=None):
    px = img.load()
    w = img.size[0]
    for x in range(x0, w if x1 is None else x1):
        r, g, b, a = px[x, y]
        px[x, y] = mix((r, g, b), col, alpha) + (a,)


def vline(img, x, col, alpha=1.0, y0=0, y1=None):
    px = img.load()
    h = img.size[1]
    for y in range(y0, h if y1 is None else y1):
        r, g, b, a = px[x, y]
        px[x, y] = mix((r, g, b), col, alpha) + (a,)


def big(w, h=None, scale=4, bg=(0, 0, 0, 0)):
    h = w if h is None else h
    img = Image.new("RGBA", (w * scale, h * scale), bg)
    return img, ImageDraw.Draw(img), scale


def reduce(img, w, h=None):
    return img.resize((w, w if h is None else h), Image.LANCZOS)


def quadrants(img):
    """Splits a 64x64 picture of a 2 x 2 window, as seen from its front, into the four parts' textures."""
    h = img.size[0] // 2
    return {"ul": img.crop((0, 0, h, h)), "ur": img.crop((h, 0, 2 * h, h)),
            "ll": img.crop((0, h, h, 2 * h)), "lr": img.crop((h, h, 2 * h, 2 * h))}


def save_quads(img, key):
    for part, q in quadrants(img).items():
        save(q, f"{key}-{part}")


# ---------------------------------------------------------------- a small stencil font (3 x 5)

FONT = {
    "A": ["010", "101", "111", "101", "101"], "C": ["011", "100", "100", "100", "011"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"], "G": ["011", "100", "101", "101", "011"],
    "H": ["101", "101", "111", "101", "101"], "I": ["111", "010", "010", "010", "111"], "K": ["101", "110", "100", "110", "101"],
    "N": ["101", "111", "111", "111", "101"], "O": ["010", "101", "101", "101", "010"], "P": ["110", "101", "110", "100", "100"],
    "R": ["110", "101", "110", "101", "101"], "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "011"], "X": ["101", "101", "010", "101", "101"], "Y": ["101", "101", "010", "010", "010"],
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "110", "001", "110"],
    " ": ["000", "000", "000", "000", "000"],
}


def text(img, s, x, y, col, scale=1, gap=1):
    d = ImageDraw.Draw(img)
    for ch in s:
        g = FONT[ch]
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    d.rectangle([x + gx * scale, y + gy * scale, x + (gx + 1) * scale - 1, y + (gy + 1) * scale - 1], fill=tuple(col[:3]) + (255,))
        x += (3 + gap) * scale


def text_width(s, scale=1, gap=1):
    return len(s) * (3 + gap) * scale - gap * scale


# ================================================================ The courtyard

def pavers():
    def base(key):
        img = noisy(PAVER, 5, key)
        rng = random.Random(seed_of(key + "slab"))
        px = img.load()
        # Two slabs a face, laid in running bond: joints at y 0 and 16, the vertical joint offset by half a slab
        for (y0, xj) in ((0, 8), (16, 24)):
            k = rng.uniform(0.95, 1.05)
            for y in range(y0, y0 + 16):
                for x in range(S):
                    r, g, b, a = px[x, y]
                    px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k), a)
        soft(img, key + "s", 5)
        speckle(img, key + "grit", [shade(PAVER, 0.82), shade(PAVER, 1.12)], 60, 0.6)
        joint = shade(PAVER, 0.72)
        hline(img, 0, joint)
        hline(img, 16, joint)
        vline(img, 8, joint, y0=0, y1=16)
        vline(img, 24, joint, y0=16, y1=32)
        return img

    save(base("paver-plain"), "paver-plain")

    img = base("paver-moss")
    rng = random.Random(seed_of("pavermoss"))
    px = img.load()
    joints = [(x, 0) for x in range(S)] + [(x, 16) for x in range(S)] + [(8, y) for y in range(16)] + [(24, y) for y in range(16, 32)]
    for (x, y) in joints:
        for dx, dy in ((0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)):
            if (dx, dy) != (0, 0) and rng.random() > 0.45:
                continue
            xx, yy = (x + dx) % S, (y + dy) % S
            c = mix(MOSS, BLADE, rng.random() * 0.5) if rng.random() < 0.8 else shade(MOSS, 0.7)
            px[xx, yy] = c + (255,)
    for _ in range(4):  # a few cushions of moss spreading from the joints
        cx, cy = rng.choice(joints)
        for _ in range(10):
            xx, yy = (cx + rng.randint(-2, 2)) % S, (cy + rng.randint(-2, 2)) % S
            px[xx, yy] = mix(MOSS, BLADE, rng.random() * 0.4) + (255,)
    save(img, "paver-moss")

    img = base("paver-cracked")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("crack"))
    x, y = 3, 20
    for _ in range(14):  # a hairline crack wandering across
        nx, ny = x + rng.randint(1, 3), y + rng.randint(-2, 1)
        d.line([(x, y), (nx, ny)], fill=shade(PAVER, 0.55) + (255,))
        x, y = nx, ny
    px = img.load()
    for yy in range(S):  # a dark stain, soft
        for xx in range(S):
            dd = math.hypot(xx - 21, yy - 9) / 7.5
            if dd < 1:
                r, g, b, a = px[xx, yy]
                k = 1 - 0.28 * (1 - dd) ** 1.5
                px[xx, yy] = (clamp(r * k), clamp(g * k * 1.01), clamp(b * k), a)
    save(img, "paver-cracked")


def turf():
    def top(key, base, blade):
        img = noisy(base, 6, key)
        soft(img, key + "s", 9)
        rng = random.Random(seed_of(key + "b"))
        px = img.load()
        for _ in range(240):  # blades and moss fronds, lighter
            x, y = rng.randrange(S), rng.randrange(S)
            c = mix(blade, base, rng.random() * 0.4)
            px[x, y] = c + (255,)
            if rng.random() < 0.5:
                px[x, (y + 1) % S] = mix(c, base, 0.4) + (255,)
        for _ in range(3):  # damp darker patches
            cx, cy, r = rng.randrange(S), rng.randrange(S), rng.uniform(3, 6)
            for yy in range(S):
                for xx in range(S):
                    dx = min(abs(xx - cx), S - abs(xx - cx))
                    dy = min(abs(yy - cy), S - abs(yy - cy))
                    dd = math.hypot(dx, dy) / r
                    if dd < 1:
                        rr, g, b, a = px[xx, yy]
                        k = 1 - 0.22 * (1 - dd)
                        px[xx, yy] = (clamp(rr * k), clamp(g * k), clamp(b * k), a)
        return img

    save(top("turf-a", TURF, BLADE), "turf-a")
    save(top("turf-b", mix(TURF, (88, 86, 44), 0.25), mix(BLADE, (150, 140, 70), 0.3)), "turf-b")
    for k, base in (("a", TURF), ("b", mix(TURF, (88, 86, 44), 0.25))):
        img = noisy((70, 54, 40), 7, "soil" + k)
        soft(img, "soils" + k, 6)
        speckle(img, "soilgrit" + k, [(96, 82, 66), (48, 38, 30)], 70, 0.7)
        px = img.load()
        rng = random.Random(seed_of("fringe" + k))
        for x in range(S):  # the turf's fringe over the top of the side
            depth = 3 + rng.randint(0, 3)
            for y in range(depth):
                px[x, y] = mix(base, BLADE, rng.random() * 0.4) + (255,)
        save(img, "turf-side-" + k)
    save(soft(speckle(noisy((70, 54, 40), 7, "soil"), "soilg", [(96, 82, 66), (48, 38, 30)], 70, 0.7), "soilb", 6), "soil")

    # A moss tuft: fronds on alpha, drawn large
    img, d, s = big(S, scale=4)
    rng = random.Random(seed_of("tuft"))
    for i in range(22):
        x = rng.uniform(4, 28) * s
        h = rng.uniform(10, 30) * s
        lean = rng.uniform(-5, 5) * s
        c = mix(BLADE, TURF, rng.random() * 0.6)
        d.line([(x, S * s), (x + lean, S * s - h)], fill=c + (255,), width=int(rng.uniform(1.2, 2.4) * s))
        d.ellipse([x + lean - 1.6 * s, S * s - h - 1.6 * s, x + lean + 1.6 * s, S * s - h + 1.6 * s], fill=mix(c, (140, 160, 90), 0.3) + (255,))
    img = reduce(img, S)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a > 110 else 0)
    save(img, "mosstuft")


def timber():
    def boards(key, base, n=4, along_x=True, grey_end=True):
        img = noisy(base, 6, key)
        rng = random.Random(seed_of(key + "g"))
        px = img.load()
        w = S // n
        for i in range(n):
            k = rng.uniform(0.88, 1.08)
            for a in range(i * w, (i + 1) * w):
                for b in range(S):
                    x, y = (b, a) if along_x else (a, b)
                    r, g, bb, al = px[x, y]
                    px[x, y] = (clamp(r * k), clamp(g * k), clamp(bb * k), al)
            for _ in range(5):  # grain lines along the board
                a = rng.randint(i * w + 1, (i + 1) * w - 2)
                b0 = rng.randint(0, S - 1)
                for b in range(b0, b0 + rng.randint(6, 18)):
                    x, y = (b % S, a) if along_x else (a, b % S)
                    r, g, bb, al = px[x, y]
                    px[x, y] = (clamp(r * 0.86), clamp(g * 0.86), clamp(bb * 0.86), al)
            gap = (i + 1) * w - 1
            for b in range(S):  # 1 px dark gap between boards
                x, y = (b, gap) if along_x else (gap, b)
                px[x, y] = shade(base, 0.35) + (255,)
            # A staggered end joint with two bolt heads
            j = (rng.randint(4, 27) + i * 11) % S
            for a in range(i * w, (i + 1) * w - 1):
                x, y = (j, a) if along_x else (a, j)
                px[x, y] = shade(base, 0.45) + (255,)
            for side in (-2, 2):
                bx_ = (j + side) % S
                by_ = i * w + w // 2 - 1
                x, y = (bx_, by_) if along_x else (by_, bx_)
                px[x, y] = (150, 146, 140, 255)
            if grey_end:  # weathered silver toward one end of each board
                for a in range(i * w, (i + 1) * w - 1):
                    for b in range(S):
                        t = max(0.0, (b - 18) / 14) * 0.55
                        x, y = (b, a) if along_x else (a, b)
                        r, g, bb, al = px[x, y]
                        gr = (r + g + bb) / 3 * 1.12
                        px[x, y] = mix((r, g, bb), (gr, gr, gr * 1.02), t) + (al,)
        return img

    save(boards("deck", DECK), "deck")
    side = noisy(shade(DECK, 0.8), 6, "deckside")
    for y in (5, 11, 17, 23, 29):
        hline(side, y, shade(DECK, 0.5), 0.6)
    save(side, "deck-side")
    save(boards("timber", mix(DECK, (110, 100, 90), 0.35), n=2, grey_end=False), "timber")
    endg = noisy(shade(DECK, 0.9), 5, "timberend")
    d = ImageDraw.Draw(endg)
    for r in (3, 7, 11, 15):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=shade(DECK, 0.7) + (255,))
    save(endg, "timber-end")


def iron():
    # The hatch plate: one 64 x 64 picture over the 2 x 2 (as seen from above, north up), riveted, rust at the rim
    W = 64
    img = noisy(IRON, 5, "hatchplate", size=W)
    soft(img, "hatchsoft", 6)
    px = img.load()
    rng = random.Random(seed_of("rust"))
    for y in range(W):
        for x in range(W):
            edge = min(x, y, W - 1 - x, W - 1 - y)
            t = max(0.0, 1 - edge / 7) * 0.75 + (0.15 if rng.random() < 0.08 else 0)
            r, g, b, a = px[x, y]
            px[x, y] = mix((r, g, b), (112, 62, 34), min(1, t * rng.uniform(0.6, 1.1))) + (a,)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, W - 3, W - 3], outline=shade(IRON, 0.6) + (255,))
    for i in range(6, W - 4, 7):  # rivets round the rim
        for (x, y) in ((i, 4), (i, W - 5), (4, i), (W - 5, i)):
            d.rectangle([x, y, x + 1, y + 1], fill=(92, 92, 96, 255))
            px[x, y + 1] = (34, 34, 36, 255)
    # A diamond tread pattern, faint
    for y in range(8, W - 8, 4):
        for x in range(8 + (y // 4 % 2) * 2, W - 8, 4):
            px[x, y] = shade(px[x, y][:3], 1.25) + (255,)
    d.line([(W // 2, 0), (W // 2, W)], fill=(24, 24, 26, 255))  # the seam between the two leaves... drawn faint
    for part, q in (("nw", (0, 0)), ("ne", (32, 0)), ("sw", (0, 32)), ("se", (32, 32))):
        save(img.crop((q[0], q[1], q[0] + 32, q[1] + 32)), f"hatch-{part}")
    save(soft(noisy(shade(IRON, 0.9), 6, "ironside"), "ironside2", 4), "iron")
    save(noisy((58, 56, 54), 8, "ring"), "ring")
    save(noisy(SHAFT, 1.5, "shaft"), "shaft")


def facade():
    def render(key):
        img = noisy(RENDER, 3, key)
        soft(img, key + "s", 4)
        rng = random.Random(seed_of(key + "trowel"))
        px = img.load()
        for _ in range(26):  # faint trowel sweeps
            x, y = rng.randrange(S), rng.randrange(S)
            ln = rng.randint(4, 10)
            k = rng.choice((0.97, 1.03))
            for i in range(ln):
                xx = (x + i) % S
                yy = (y + int(i * rng.uniform(-0.3, 0.3))) % S
                r, g, b, a = px[xx, yy]
                px[xx, yy] = (clamp(r * k), clamp(g * k), clamp(b * k), a)
        vline(img, 0, shade(RENDER, 0.93), 0.35)  # a panel joint once a block, barely there
        return img

    save(render("cladding-plain"), "cladding-plain")
    img = render("cladding-band")
    hline(img, 15, shade(RENDER, 0.82))
    hline(img, 16, shade(RENDER, 1.06))
    save(img, "cladding-band")
    img = render("cladding-streak")
    px = img.load()
    rng = random.Random(seed_of("streak"))
    for x in range(9, 23):  # a grey rain streak running down from the sill above
        strength = (1 - abs(x - 16) / 7.5) * 0.18
        for y in range(S):
            k = 1 - strength * (1 - y / 40) * rng.uniform(0.7, 1.2)
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k * 0.99), a)
    save(img, "cladding-streak")
    save(noisy(ROOMWHITE, 2, "roomwhite"), "wall-room")
    save(soft(noisy(mix(RENDER, (230, 228, 222), 0.4), 3, "sill"), "sills", 3), "sillstone")
    img = noisy(ROOF, 4, "roof")
    soft(img, "roofs", 4)
    hline(img, 0, shade(ROOF, 0.75))
    hline(img, 1, shade(ROOF, 1.15))
    vline(img, 20, shade(ROOF, 0.8), 0.6)
    save(img, "roof")
    img = noisy((112, 110, 106), 12, "gravel")
    speckle(img, "gravel2", [(150, 148, 142), (70, 68, 66), (128, 118, 104)], 260, 0.8)
    save(img, "roofgravel")
    save(noisy(NOTHING, 1.2, "nothing"), "nothing")
    save(noisy(SKY, 1.0, "sky"), "sky")


# ================================================================ The hotel

def floors():
    # Corridor: charcoal loop pile under a lighter grey lattice
    img = noisy(CARPET_C, 5, "carpetc")
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 2 == 0:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r * 0.9), clamp(g * 0.9), clamp(b * 0.9), a)
    for i in range(S):  # a diamond lattice, 16 px
        for (x, y) in ((i, i), (i, S - 1 - i), ((i + 16) % S, i), ((i + 16) % S, S - 1 - i)):
            px[x % S, y % S] = mix(px[x % S, y % S][:3], LATTICE, 0.8) + (255,)
    save(img, "carpet-corridor")
    img = noisy(CARPET_R, 6, "carpetr")
    speckle(img, "carpetrf", [shade(CARPET_R, 0.8), shade(CARPET_R, 1.18), (96, 98, 104)], 160, 0.7)
    save(soft(img, "carpetrs", 3), "carpet-room")
    img = soft(noisy(PORCELAIN, 3, "porc"), "porcs", 4)
    for p in (0, 16):
        hline(img, p, shade(PORCELAIN, 0.78))
        vline(img, p, shade(PORCELAIN, 0.78))
    save(img, "tile-lobby")
    img = noisy((240, 240, 238), 3, "bath")
    for p in range(0, S, 8):
        hline(img, p, (176, 178, 178))
        vline(img, p, (176, 178, 178))
    save(img, "tile-bath")
    img = soft(noisy(STAIRPAINT, 4, "stairpaint"), "stairs", 4)
    speckle(img, "stairscuff", [shade(STAIRPAINT, 0.8)], 30, 0.6)
    save(img, "concrete-stair")
    edge = img.copy()
    d = ImageDraw.Draw(edge)
    d.rectangle([0, 0, S - 1, 3], fill=(214, 182, 46, 255))
    speckle(edge, "edgescuff", [(170, 150, 60)], 20, 0.5)
    save(edge, "concrete-stair-edge")
    save(soft(noisy(CEILING, 2, "ceiling"), "ceils", 2), "ceiling")
    img = soft(noisy((128, 126, 122), 7, "slabside"), "slabsides", 5)
    speckle(img, "slabpits", [(96, 94, 90)], 30, 0.7)
    save(img, "concrete")


def walls():
    img = noisy(VINYL, 3, "vinyl")
    px = img.load()
    for y in range(S):  # a fine linen weave
        for x in range(S):
            if y % 2 == 0 and x % 3 == 0 or x % 2 == 0 and y % 3 == 1:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r * 0.965), clamp(g * 0.965), clamp(b * 0.965), a)
    save(soft(img, "vinyls", 2), "wall-corridor")
    save(noisy((246, 246, 244), 2, "skirting"), "skirting")
    save(soft(noisy(FEATURE, 3, "feature"), "features", 3), "wall-feature")
    img = noisy((206, 206, 202), 4, "blockwork")
    for y in (0, 8, 16, 24):
        hline(img, y, (168, 168, 164))
        off = 0 if y % 16 == 0 else 8
        for x in (off, off + 16):
            vline(img, x % S, (168, 168, 164), y0=y, y1=y + 8)
    save(soft(img, "blockworks", 3), "wall-stair")


def lights():
    save(soft(noisy((255, 246, 224), 2, "lens"), "lenss", 2), "lens-on")
    save(noisy((176, 176, 172), 3, "lensoff"), "lens-off")
    save(noisy((206, 210, 214), 4, "chrome"), "chrome")
    img = noisy((96, 220, 120), 4, "bulkhead")
    save(img, "bulkhead-on")


# ================================================================ Windows

def window_parts():
    save(noisy(ALU, 3, "alu"), "alu")
    img = Image.new("RGBA", (S, S), (180, 196, 204, 40))
    px = img.load()
    for y in range(S):  # a faint diagonal reflection streak
        for x in range(S):
            t = abs((x + y) - 20)
            if t < 3:
                px[x, y] = (220, 230, 236, 70 - t * 12)
    save(img, "glass")
    wired = img.copy()
    d = ImageDraw.Draw(wired)
    for p in range(3, S, 8):
        d.line([(p, 0), (p, S)], fill=(70, 74, 76, 120))
        d.line([(0, p), (S, p)], fill=(70, 74, 76, 120))
    save(wired, "wiredglass")
    img = noisy(BLIND, 2, "blind")
    for y in range(0, S, 4):
        hline(img, y, shade(BLIND, 0.95), 0.6)
    save(img, "blind")
    save(noisy(shade(BLIND, 0.93), 3, "roll"), "roll")
    save(noisy((214, 210, 200), 3, "cord"), "cord")
    # The glowing blind: a lamp low behind it, warm, brightest low and toward the bed side
    pic, d, s = big(64, scale=2)
    px = pic.load()
    for y in range(128):
        for x in range(128):
            dd = math.hypot((x - 46) / 128, (y - 100) / 110)
            t = max(0.0, 1 - dd * 1.5)
            c = mix((228, 196, 140), (255, 236, 196), t)
            px[x, y] = c + (255,)
    pic = reduce(pic, 64)
    for y in range(0, 64, 4):
        hline(pic, y, (210, 178, 124), 0.25)
    save_quads(pic, "blind-glow")
    # A dimmer warm cast on the roll for lit rooms
    save(noisy((236, 214, 170), 3, "rolllit"), "roll-lit")


def figures():
    """The silhouettes standing in a predatory window (64 x 64 over the 2 x 2, seen from the courtyard). Tall and
    thin: the head is high in the upper panes, the shoulders at the transom, the arms too long. Soft edges (alpha
    falling off over 2 px). Beckon: the arm on the viewer's right (in the upper-right pane) raised, the hand bent over,
    curling."""
    def draw(beckon):
        W, sc = 64, 8
        img = Image.new("L", (W * sc, W * sc), 0)
        d = ImageDraw.Draw(img)

        def P(x, y):
            # The figure stands a little to the left of the mullion, so the cross of the frame doesn't cut its head
            return ((x - 9) * sc, y * sc)
        # head (a slightly long oval), neck, shoulders sloping
        d.ellipse([P(27.2, 9), P(36.8, 22)], fill=255)
        d.rectangle([P(30, 20), P(34, 27)], fill=255)
        d.polygon([P(21, 31), P(26, 26.5), P(38, 26.5), P(43, 31), P(41.5, 64), P(22.5, 64)], fill=255)
        # left arm (viewer's left): hanging, too long, past the bottom
        d.polygon([P(21, 31), P(23.5, 30), P(22.5, 64), P(19.4, 64)], fill=255)
        if beckon:
            # right arm (viewer's right) raised: upper arm out and up, forearm up, the hand bent over beckoning
            d.polygon([P(40.5, 29), P(43, 31.5), P(49.5, 21), P(47.4, 19.5)], fill=255)
            d.polygon([P(47.4, 19.5), P(49.5, 21), P(50.4, 9.5), P(48.4, 9.4)], fill=255)
            d.ellipse([P(47.2, 6.2), P(51.6, 10.6)], fill=255)
            for i, (a, b) in enumerate(((50.6, 6.8), (51.6, 8.0), (52.0, 9.4))):
                d.line([P(a - 1.8, b - 0.6), P(a, b), P(a + 0.4, b + 2.2)], fill=255, width=int(0.9 * sc))
        else:
            d.polygon([P(40.5, 31), P(43, 31), P(44.6, 64), P(41.5, 64)], fill=255)
        small = img.resize((W, W), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.9))
        rgba = Image.new("RGBA", (W, W), FIGURE + (0,))
        px, sp = rgba.load(), small.load()
        for y in range(W):
            for x in range(W):
                a = sp[x, y]
                a = 0 if a < 24 else min(255, int(a * 1.25))
                px[x, y] = FIGURE + (a,)
        return rgba

    for kind, beckon in (("figure", False), ("beckon", True)):
        pic = draw(beckon)
        save_quads(pic, kind)
        # From inside the room the same panes show the figure's back: the picture mirrored left to right
        # Seen from inside, the courtyard's left panes are on the right: each pane's back is the mirror of its own front
        for part, q in quadrants(pic).items():
            save(q.transpose(Image.FLIP_LEFT_RIGHT), f"{kind}-back-{part}")


# ---------------------------------------------------------------- the places seen through link windows

def _scene_canvas():
    return big(64, scale=4, bg=(0, 0, 0, 255))


def _persp_room(d, s, wall, floor, ceil, back, depth=0.38):
    """A box room in one-point perspective filling the window: back wall rectangle in the middle, floor, ceiling and
    two side walls converging on it. Returns the back wall's rectangle in canvas pixels."""
    W = 64 * s
    m = W * depth / 2
    bx0, by0, bx1, by1 = m, m * 0.9, W - m, W - m * 1.1
    d.polygon([(0, 0), (W, 0), (bx1, by0), (bx0, by0)], fill=ceil)
    d.polygon([(0, W), (W, W), (bx1, by1), (bx0, by1)], fill=floor)
    d.polygon([(0, 0), (bx0, by0), (bx0, by1), (0, W)], fill=shade(wall, 0.82))
    d.polygon([(W, 0), (bx1, by0), (bx1, by1), (W, W)], fill=shade(wall, 0.9))
    d.rectangle([bx0, by0, bx1, by1], fill=back)
    return bx0, by0, bx1, by1


def scene_pictures():
    """The back wall of each peep-box: another place in perspective, emissive (it is lit from its own side)."""
    pics = {}

    # Level 0: mono-yellow wallpaper, damp brown carpet, ceiling tiles and a long fluorescent troffer, a doorway
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (206, 186, 104), (150, 128, 76), (216, 206, 168), (214, 194, 110))
    for i in range(8):  # ceiling tile grid converging
        t = i / 8
        d.line([(t * 256, 0), (bx0 + t * (bx1 - bx0), by0)], fill=(190, 180, 146), width=2)
    d.rectangle([bx0 + 40, by0 + 22, bx0 + 90, by1], fill=(70, 58, 34))  # a doorway into more yellow
    d.rectangle([bx0 + 46, by0 + 34, bx0 + 84, by1], fill=(160, 140, 78))
    for x in range(int(bx0), int(bx1), 6):  # wallpaper stripes
        d.line([(x, by0), (x, by1)], fill=(196, 176, 98), width=1)
    pics["l0"] = img

    # Level 1: grey concrete, a pillar, puddles, a caged light
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (120, 120, 116), (92, 92, 90), (104, 104, 102), (126, 126, 122), depth=0.3)
    d.rectangle([bx0 + 60, by0, bx0 + 84, by1], fill=(140, 140, 136))  # a pillar far off
    d.ellipse([60, 220, 150, 236], fill=(70, 74, 78))
    d.ellipse([bx0 + 30, by0 + 8, bx0 + 50, by0 + 20], fill=(250, 244, 220))
    pics["l1"] = img

    # The Hub: an orange-lit tunnel of old concrete, curving away
    img, d, s = _scene_canvas()
    for i in range(14):
        t = i / 14
        r = 128 * (1 - t * 0.8)
        c = mix((210, 120, 48), (60, 34, 20), t)
        d.ellipse([128 - r + t * 30, 128 - r * 0.9, 128 + r + t * 30, 128 + r * 0.9], fill=c)
    d.rectangle([0, 190, 256, 256], fill=(60, 52, 46))
    d.polygon([(0, 256), (256, 256), (170, 170), (130, 170)], fill=(78, 70, 62))
    d.ellipse([150, 60, 170, 76], fill=(255, 196, 110))
    pics["hub"] = img

    # Level Fun: an orange party room, bunting, balloons, confetti
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (226, 150, 70), (170, 70, 60), (236, 196, 150), (236, 164, 84))
    rng = random.Random(seed_of("funscene"))
    pts = [(bx0 + i * (bx1 - bx0) / 6, by0 + 18 + (10 if i % 2 else 0)) for i in range(7)]
    d.line(pts, fill=(80, 60, 40), width=2)
    for i in range(6):
        x0, y0 = pts[i]
        d.polygon([(x0, y0), (x0 + 14, y0), (x0 + 7, y0 + 16)], fill=rng.choice([(214, 69, 65), (242, 198, 65), (60, 125, 217), (76, 175, 106)]))
    for _ in range(90):
        x, y = rng.randrange(256), rng.randrange(256)
        d.rectangle([x, y, x + 3, y + 2], fill=rng.choice([(214, 69, 65), (242, 198, 65), (60, 125, 217), (76, 175, 106), (142, 91, 196)]))
    d.ellipse([bx0 + 10, by1 - 50, bx0 + 60, by1 - 10], fill=(240, 230, 210))  # a cake on a table
    pics["fun"] = img

    # Level 2: dark maintenance tunnel, pipes, a red glow
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (54, 50, 48), (40, 38, 36), (46, 42, 40), (70, 40, 34), depth=0.5)
    for y, c in ((by0 + 10, (120, 90, 70)), (by0 + 26, (90, 96, 100)), (by1 - 16, (110, 70, 50))):
        d.rectangle([bx0, y, bx1, y + 6], fill=c)
    d.ellipse([bx0 + 20, by0 + 40, bx1 - 20, by1], fill=(140, 44, 30))
    pics["l2"] = img

    # Level 4: an empty office, drop ceiling with troffers, a desk and a dark monitor
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (200, 198, 188), (118, 120, 128), (220, 218, 212), (206, 204, 196))
    for t in (0.25, 0.5, 0.75):
        d.polygon([(t * 256 - 14, 10), (t * 256 + 14, 10), (bx0 + t * (bx1 - bx0) + 4, by0 + 4), (bx0 + t * (bx1 - bx0) - 4, by0 + 4)], fill=(250, 250, 244))
    d.rectangle([bx0 + 10, by1 - 40, bx1 - 30, by1 - 32], fill=(130, 110, 86))
    pics["l4"] = img

    # Level 5: a red hotel corridor, gold sconces, a dark door
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (130, 34, 36), (90, 26, 28), (170, 140, 110), (120, 32, 34), depth=0.62)
    for x in (40, 216):
        d.ellipse([x - 8, 70, x + 8, 92], fill=(255, 210, 130))
    d.rectangle([bx0 + 6, by0 + 10, bx1 - 6, by1], fill=(60, 30, 22))
    pics["l5"] = img

    # Level 6: nothing at all
    img, d, s = _scene_canvas()
    pics["l6"] = img

    # Level 9: a suburban street at night, a porch light, a house front, black windows
    img, d, s = _scene_canvas()
    d.rectangle([0, 0, 256, 256], fill=(14, 16, 26))
    d.polygon([(20, 120), (128, 50), (236, 120)], fill=(38, 36, 40))
    d.rectangle([40, 120, 216, 230], fill=(70, 64, 58))
    d.rectangle([70, 150, 110, 190], fill=(12, 12, 14))
    d.rectangle([146, 140, 186, 230], fill=(40, 30, 24))
    d.ellipse([190, 128, 206, 144], fill=(255, 220, 150))
    d.rectangle([0, 230, 256, 256], fill=(30, 32, 30))
    pics["l9"] = img

    # Level 37: white tile, a pool, wavering light
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (226, 232, 234), (200, 214, 218), (236, 240, 242), (230, 236, 238))
    d.polygon([(0, 256), (256, 256), (bx1, by1 - 10), (bx0, by1 - 10)], fill=(90, 180, 200))
    for k in range(10):
        y = 200 + k * 6
        d.line([(10, y), (246, y + 3)], fill=(140, 210, 226), width=2)
    for x in range(0, 256, 16):
        d.line([(x, 0), (bx0 + x / 256 * (bx1 - bx0), by0)], fill=(206, 214, 216))
    pics["l37"] = img

    # Level 94: a green hill and a bright blue sky
    img, d, s = _scene_canvas()
    for y in range(256):
        d.line([(0, y), (256, y)], fill=mix((92, 156, 232), (196, 226, 250), y / 256))
    d.ellipse([-80, 150, 340, 420], fill=(96, 176, 70))
    d.ellipse([140, 120, 420, 380], fill=(110, 190, 80))
    d.ellipse([40, 30, 90, 60], fill=(250, 250, 255))
    d.ellipse([70, 24, 120, 58], fill=(250, 250, 255))
    pics["l94"] = img

    # The End: rows of library shelving under warm light
    img, d, s = _scene_canvas()
    bx0, by0, bx1, by1 = _persp_room(d, s, (120, 88, 60), (96, 74, 56), (200, 190, 170), (110, 82, 58), depth=0.5)
    rng = random.Random(seed_of("endbooks"))
    for row in range(5):
        y = by0 + 6 + row * (by1 - by0 - 12) / 5
        x = bx0 + 4
        while x < bx1 - 6:
            w = rng.randint(3, 7)
            d.rectangle([x, y, x + w, y + 14], fill=rng.choice([(120, 40, 36), (40, 70, 110), (60, 100, 60), (180, 160, 110), (90, 60, 40)]))
            x += w + 1
    pics["end"] = img

    # Void: black with a faint shimmer
    img, d, s = _scene_canvas()
    rng = random.Random(seed_of("void"))
    for _ in range(140):
        x, y = rng.randrange(256), rng.randrange(256)
        c = rng.randint(14, 40)
        d.point((x, y), fill=(c, c, c + 8))
    pics["void"] = img

    for place, pic in pics.items():
        save_quads(reduce(pic, 64), f"scene-{place}")
    return list(pics)


def scene_materials():
    """Small surfaces for the peep-boxes' real voxel features (floors, walls, things)."""
    mats = {
        "sc-yellow": ((206, 186, 104), 4), "sc-carpet0": ((150, 128, 76), 6), "sc-ceil0": ((216, 206, 168), 3),
        "sc-troffer": ((250, 250, 238), 2), "sc-concrete": ((120, 120, 116), 6), "sc-concretedk": ((92, 92, 90), 6),
        "sc-cage": ((70, 70, 70), 4), "sc-bulb": ((255, 246, 210), 2), "sc-hubwall": ((150, 96, 52), 6),
        "sc-sodium": ((255, 186, 90), 2), "sc-party": ((236, 164, 84), 4), "sc-partyfloor": ((170, 70, 60), 5),
        "sc-red": ((214, 69, 65), 3), "sc-yellowb": ((242, 198, 65), 3), "sc-tablecloth": ((240, 236, 226), 3),
        "sc-pipe": ((110, 82, 64), 6), "sc-pipe2": ((90, 96, 100), 5), "sc-dark": ((40, 38, 36), 4),
        "sc-office": ((200, 198, 188), 3), "sc-officecarpet": ((118, 120, 128), 6), "sc-desk": ((140, 118, 92), 4),
        "sc-monitor": ((30, 30, 32), 3), "sc-hotelred": ((120, 32, 34), 4), "sc-gold": ((206, 170, 90), 6),
        "sc-door": ((60, 30, 22), 4), "sc-night": ((14, 16, 26), 3), "sc-post": ((210, 206, 196), 4),
        "sc-porchlamp": ((255, 220, 150), 2), "sc-tile": ((230, 236, 238), 3), "sc-water": ((90, 180, 200), 8),
        "sc-hill": ((96, 176, 70), 6), "sc-shelf": ((110, 82, 58), 5), "sc-black": ((4, 4, 5), 1),
        "sc-courtnight": ((10, 12, 16), 2), "sc-skyblue": ((140, 190, 240), 3), "sc-grassnight": ((22, 32, 22), 4), "sc-decknight": ((40, 32, 24), 4),
    }
    for k, (c, n) in mats.items():
        save(soft(noisy(c, n, k), k + "s", n * 0.6), k)
    # Books on a shelf
    img = noisy((110, 82, 58), 3, "sc-books")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("books"))
    x = 0
    while x < S:
        w = rng.randint(2, 4)
        d.rectangle([x, 4, x + w - 1, 28], fill=rng.choice([(120, 40, 36), (40, 70, 110), (60, 100, 60), (180, 160, 110), (90, 60, 40)]) + (255,))
        x += w
    save(img, "sc-books")
    return list(mats) + ["sc-books"]


def courtyard_view():
    """What the windows into 188 show: the courtyard at night, seen from a ground-floor sill. Dark moss, the near
    edge of the round deck, and across it the opposite façade in faint blue light: rows of small square windows,
    three of them lit warm behind their blinds, one with its blind up and a dark shape in it."""
    img, d, s = big(64, scale=4, bg=(6, 7, 10, 255))
    d.rectangle([0, 0, 256, 120], fill=(7, 8, 11))
    # the opposite façade
    d.rectangle([0, 30, 256, 176], fill=(46, 48, 54))
    for row in range(4):
        y = 40 + row * 34
        for col in range(7):
            x = 10 + col * 36
            d.rectangle([x, y, x + 18, y + 18], fill=(30, 32, 36))
            d.rectangle([x + 2, y + 2, x + 16, y + 16], fill=(70, 72, 78))
    lit = [(1, 0), (4, 2), (5, 1)]
    for col, row in lit:
        x, y = 10 + col * 36, 40 + row * 34
        d.rectangle([x + 2, y + 2, x + 16, y + 16], fill=(250, 210, 140))
    d.rectangle([10 + 2 * 36 + 2, 40 + 3 * 34 + 2, 10 + 2 * 36 + 16, 40 + 3 * 34 + 16], fill=(120, 90, 60))
    d.ellipse([10 + 2 * 36 + 7, 40 + 3 * 34 + 4, 10 + 2 * 36 + 11, 40 + 3 * 34 + 9], fill=(8, 8, 10))
    d.rectangle([10 + 2 * 36 + 6, 40 + 3 * 34 + 9, 10 + 2 * 36 + 12, 40 + 3 * 34 + 16], fill=(8, 8, 10))
    # ground: paving, then moss, then the deck's curved edge near the bottom
    d.rectangle([0, 176, 256, 256], fill=(30, 32, 34))
    d.rectangle([0, 196, 256, 256], fill=(20, 30, 20))
    d.ellipse([-40, 226, 300, 400], fill=(54, 42, 30))
    for x in range(-40, 300, 14):
        d.line([(128, 330), (x, 226)], fill=(40, 30, 22), width=2)
    pic = reduce(img, 64)
    save_quads(pic, "courtview")


# ================================================================ Doors and signs

def doors():
    img = noisy(LAMINATE, 3, "laminate")
    rng = random.Random(seed_of("lamgrain"))
    px = img.load()
    for _ in range(22):  # long straight grain lines (vertical)
        x = rng.randrange(S)
        y0 = rng.randrange(S)
        for y in range(y0, y0 + rng.randint(10, 30)):
            r, g, b, a = px[x, y % S]
            px[x, y % S] = (clamp(r * 0.92), clamp(g * 0.92), clamp(b * 0.92), a)
    save(img, "laminate")
    save(noisy((58, 56, 54), 3, "doorframe"), "doorframe")
    save(noisy((44, 46, 50), 3, "reader"), "reader")
    save(flat((80, 230, 110)), "led-green")
    save(flat((240, 60, 50)), "led-red")
    save(flat((30, 30, 30)), "led-dark")
    save(noisy((150, 152, 156), 4, "steel"), "steel")
    img = noisy((142, 146, 148), 3, "firesteel")
    soft(img, "firesteels", 3)
    save(img, "firedoor")
    # The FIRE EXIT stencil (a 32 x 32 decal on the door's upper part, red letters on alpha)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for i, word in enumerate(("FIRE", "EXIT")):
        w = text_width(word)
        text(img, word, (S - w) // 2, 6 + i * 8, (200, 40, 36))
    save(img, "stencil-fireexit")
    save(noisy((196, 40, 36), 3, "pushbarred"), "pushbar-red")
    # Exit sign face: green, a white running figure and an arrow toward a door
    img, d, s = big(S, scale=4, bg=(30, 160, 80, 255))
    d.rectangle([4, 4, 124, 124], outline=(230, 250, 236), width=4)
    d.ellipse([38, 22, 54, 38], fill=(240, 255, 244))
    d.polygon([(46, 40), (60, 44), (52, 74), (40, 72)], fill=(240, 255, 244))
    d.line([(52, 50), (70, 60)], fill=(240, 255, 244), width=7)
    d.line([(48, 52), (32, 62)], fill=(240, 255, 244), width=7)
    d.line([(46, 72), (34, 98)], fill=(240, 255, 244), width=8)
    d.line([(50, 72), (66, 86), (60, 104)], fill=(240, 255, 244), width=8)
    d.rectangle([80, 30, 108, 104], outline=(240, 255, 244), width=5)
    d.polygon([(72, 66), (86, 56), (86, 76)], fill=(240, 255, 244))
    save(reduce(img, S), "exitsign")
    save(noisy((236, 238, 236), 2, "signbox"), "signbox")
    # Floor numbers, stencilled on grey plates
    for label in ("1", "2", "3", "4", "5", "roof"):
        img = noisy((120, 124, 126), 3, "plate" + label)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=(90, 92, 94, 255))
        word = label.upper()
        if label == "roof":
            text(img, word, (S - text_width(word)) // 2, 13, (238, 236, 228))
        else:
            text(img, word, (S - text_width(word, scale=4)) // 2, 6, (238, 236, 228), scale=4)
        save(img, "floorsign-" + label)
    # Glass: dark glass for the front doors (nothing beyond), clear-ish for the courtyard door
    save(Image.new("RGBA", (S, S), (20, 22, 24, 200)), "glass-dark")
    save(noisy((140, 136, 128), 4, "kickplate"), "kickplate")


# ================================================================ Rooms and lobby

def props():
    mats = {
        "upholstery": ((112, 114, 118), 4), "duvet": ((242, 242, 240), 2), "throw": ((86, 90, 98), 4),
        "pillow": ((248, 248, 246), 2), "headfabric": ((126, 128, 132), 4), "button": ((96, 98, 102), 3),
        "oak": (LAMINATE, 3), "lampbase": ((60, 60, 62), 3), "shade-off": ((226, 220, 206), 3),
        "shade-on": ((255, 236, 196), 2), "screen-off": ((16, 18, 20), 2), "chairfabric": ((70, 72, 76), 4),
        "teal": ((46, 116, 118), 5), "robe": ((210, 210, 206), 4), "safe": ((60, 62, 64), 3),
        "iron-white": ((230, 230, 228), 2), "fridge": ((26, 26, 28), 2), "bottle-green": ((60, 120, 70), 6),
        "bottle-amber": ((180, 120, 50), 6), "label": ((236, 230, 210), 3), "strap": ((56, 58, 64), 3),
        "frosted": ((226, 232, 234), 2), "frame-white": ((246, 246, 244), 2), "porcelain": ((244, 244, 242), 2),
        "mirror": ((170, 186, 196), 6), "cartgrey": ((96, 100, 104), 4), "towel": ((246, 246, 244), 3),
        "linenbag": ((200, 196, 186), 5), "bottle-blue": ((70, 120, 180), 6), "mophead": ((190, 186, 172), 8),
        "fascia": (FASCIA, 4), "desktop": ((232, 230, 224), 2), "backlit": ((255, 240, 210), 2),
        "pigeon": ((150, 132, 108), 4), "cardwhite": ((244, 244, 240), 2), "loungefabric": ((92, 96, 104), 5),
        "tabletop": ((226, 222, 214), 2), "cereal": ((214, 168, 80), 14), "tube": ((220, 230, 234), 2),
        "juice": ((236, 140, 40), 6), "drumclear": ((200, 210, 214), 2), "downpipe": ((112, 116, 118), 3),
        "bracket": ((80, 82, 84), 3), "puddle": ((14, 18, 22), 3), "bollard": ((52, 54, 58), 3),
        "bollardlight": ((255, 236, 200), 2), "benchwood": (DECK, 5), "concrete-leg": ((150, 148, 142), 6),
        "vent": ((138, 142, 144), 4), "ink": ((20, 20, 22), 2), "white": ((246, 246, 244), 2),
        "drain": ((40, 40, 42), 4), "black": ((8, 8, 9), 1), "rubber": ((34, 34, 36), 3),
        "confetti-paper": ((240, 236, 226), 3), "balloon-red": ((214, 44, 50), 6), "string": ((236, 232, 222), 2),
        "woodwhite": ((240, 238, 232), 3), "sash": ((248, 246, 240), 2), "blindwarm": ((236, 224, 200), 3),
        "nightblue": ((70, 90, 130), 4),
    }
    for k, (c, n) in mats.items():
        save(noisy(c, n, k), k)
    # A few with patterns
    img = noisy((212, 210, 204), 3, "drawerfront")
    hline(img, 15, (170, 166, 160))
    save(img, "drawerfront")
    img = noisy((26, 28, 30), 2, "minibardoor")
    d = ImageDraw.Draw(img)
    for i, c in enumerate(((60, 120, 70), (180, 120, 50), (236, 230, 210), (70, 120, 180))):
        d.rectangle([4 + i * 7, 10, 8 + i * 7, 26], fill=c + (255,))
    save(img, "minibar-door")
    img = noisy((40, 42, 46), 2, "tvsnow")
    save(img, "tv")
    img = noisy((40, 40, 42), 6, "grate")
    d = ImageDraw.Draw(img)
    for x in range(2, S, 4):
        d.line([(x, 0), (x, S)], fill=(14, 14, 16, 255), width=2)
    save(img, "grate")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))  # confetti on a sill
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("confetti"))
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        d.rectangle([x, y, x + 1, y], fill=rng.choice([(214, 69, 65), (242, 198, 65), (60, 125, 217), (76, 175, 106), (142, 91, 196)]) + (255,))
    save(img, "confetti")
    # Linen: folded sheets seen edge-on
    img = noisy((236, 236, 232), 2, "sheets")
    for y in range(0, S, 4):
        hline(img, y, (200, 200, 196))
    save(img, "sheets")


# ================================================================ Items, GUI

def items():
    # Keycard: white plastic, a grey stripe, a small blue logo, HOUSEKEEPING in tiny letters
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 8, 28, 23], radius=2, fill=(244, 244, 240, 255), outline=(160, 160, 156, 255))
    d.rectangle([3, 11, 28, 13], fill=(120, 122, 126, 255))
    d.rectangle([6, 16, 9, 19], fill=(70, 110, 170, 255))
    for i, x in enumerate(range(11, 27, 2)):
        d.point((x, 17), fill=(90, 90, 92, 255))
        if i % 2 == 0:
            d.point((x, 19), fill=(90, 90, 92, 255))
    save_item(img, "keycard")
    # Cereal: a small portion cup of flakes
    img, d, s = big(S, scale=4)
    d.polygon([(28, 56), (100, 56), (92, 112), (36, 112)], fill=(240, 236, 226, 255))
    d.rectangle([32, 64, 96, 74], fill=(70, 110, 170, 255))
    rng = random.Random(seed_of("flakes"))
    for _ in range(40):
        x, y = rng.uniform(30, 96), rng.uniform(34, 58)
        d.ellipse([x - 6, y - 4, x + 6, y + 4], fill=mix((214, 168, 80), (180, 120, 50), rng.random()) + (255,))
    save_item(reduce(img, S), "cereal")
    # Juice box: an orange carton with a straw
    img, d, s = big(S, scale=4)
    d.polygon([(40, 30), (88, 30), (96, 40), (96, 116), (40, 116)], fill=(236, 140, 40, 255))
    d.polygon([(88, 30), (96, 40), (96, 116), (88, 108)], fill=(200, 110, 30, 255))
    d.ellipse([52, 60, 80, 88], fill=(250, 196, 70, 255))
    d.rectangle([62, 8, 66, 34], fill=(250, 250, 250, 255))
    d.line([(64, 10), (74, 4)], fill=(250, 250, 250, 255), width=4)
    save_item(reduce(img, S), "juicebox")


def gui():
    """Peripherals: three soft black shapes for the edge of the screen (128 x 256): standing straight, leaning out
    from a corner, the head tilted. A blurred silhouette, alpha 0.85 at the core falling to 0 over 24 px."""
    W, H = 128, 256

    def figure(kind):
        m = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(m)
        cx = 64
        if kind == 1:
            d.ellipse([cx - 11, 30, cx + 11, 58], fill=255)
            d.polygon([(cx - 22, 66), (cx + 22, 66), (cx + 18, 200), (cx + 10, 240), (cx - 10, 240), (cx - 18, 200)], fill=255)
            d.rectangle([cx - 5, 54, cx + 5, 68], fill=255)
            d.polygon([(cx - 22, 66), (cx - 28, 70), (cx - 26, 180), (cx - 20, 180)], fill=255)
            d.polygon([(cx + 22, 66), (cx + 28, 70), (cx + 26, 180), (cx + 20, 180)], fill=255)
        elif kind == 2:
            # leaning out from behind a corner on the right: half a body, the head tipped out
            d.ellipse([cx - 4, 40, cx + 18, 68], fill=255)
            d.polygon([(cx + 2, 72), (cx + 60, 72), (cx + 60, 250), (cx + 10, 250), (cx - 2, 120)], fill=255)
            d.rectangle([cx + 6, 62, cx + 16, 76], fill=255)
        else:
            # standing, the head tilted hard to one side, hunched
            d.ellipse([cx + 2, 36, cx + 24, 62], fill=255)
            d.polygon([(cx - 20, 72), (cx + 18, 66), (cx + 20, 200), (cx + 12, 244), (cx - 10, 244), (cx - 18, 200)], fill=255)
            d.polygon([(cx + 4, 60), (cx + 14, 58), (cx + 10, 72), (cx, 72)], fill=255)
            d.polygon([(cx - 20, 72), (cx - 27, 78), (cx - 30, 190), (cx - 23, 190)], fill=255)
            d.polygon([(cx + 18, 66), (cx + 25, 72), (cx + 27, 186), (cx + 20, 186)], fill=255)
        # Soft: blur so the alpha falls off over about 24 px
        m = m.filter(ImageFilter.GaussianBlur(9))
        out = Image.new("RGBA", (W, H))
        px, mp = out.load(), m.load()
        for y in range(H):
            for x in range(W):
                a = mp[x, y] / 255
                a = min(0.85, a * 1.15) * 255
                px[x, y] = (6, 6, 8, clamp(a))
        return out

    for k in (1, 2, 3):
        _save(figure(k), f"gui/188/peripheral-{k}")


def generate():
    pavers()
    turf()
    timber()
    iron()
    facade()
    floors()
    walls()
    lights()
    window_parts()
    figures()
    places = scene_pictures()
    mats = scene_materials()
    courtyard_view()
    doors()
    props()
    items()
    gui()
    print(f"188 textures: {len(WRITTEN)}")
    return places


if __name__ == "__main__":
    generate()
