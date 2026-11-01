"""Level 47, "The Adderwood" (experimental): its blocks, their textures and models, its sky's textures, and its lang keys.
Run under the asset lock: bash tools/locked.sh run python tools/gen_47.py   (its creatures: tools/gen_47_creatures.py; its sounds:
tools/gen_47_sounds.py)

Writes assets/backrooms/blocktypes/47/l47-*.json, textures/block/47/*.png, shapes/block/47/*.json,
textures/environment/l47-*.png (the moon's far side, the stars, the aurora), and the level's keys in lang/en.json: one block,
from its level-30 line to its last key (the handbook page from gen_guide.py's "level47", the wanderers' notes from
gen_notes.py's "l47" track, if they are there), in place.

The Adderwood is a living old-growth forest: furrowed oak bark, smooth grey beech, deep red-brown fir, scaly spruce, grey
weathered dead wood, the green giants' green bark; moss over all of it, in thick cushions; humus, leaf litter, pebbled
stream beds. The glade's manor is grey ashlar on a dark plinth, timber and slate, leaded windows; its stones are sarsens,
lichened; the Order's banners crimson with a gold snake eating its tail.
"""
import json
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import matlib as M  # noqa: E402
import gen_23 as G  # noqa: E402  (the sibling forest's bark, leaf and ground painters, used read-only)

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures")
S = 32
SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}


def save(img, rel):
    path = os.path.join(TEX, *rel.split("/")) + ".png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


MOSS = (70, 104, 40)


def mossed(img, seed, cover=0.5, colour=MOSS, top_bias=0.0):
    """Cushions of moss grown over a texture: a soft-edged mask from noise (thicker toward the top by top_bias), each
    cushion lit on top and shaded under, tiny stems as specks."""
    f = M.fbm(S, seed, (16, 8, 4))
    px = img.load()
    rng = random.Random(seed + 1)
    for y in range(S):
        for x in range(S):
            t = f[y][x] + (cover - 0.5) + top_bias * (0.5 - y / S)
            if t > 0.05:
                k = min(1.0, (t - 0.05) * 4)
                c = M.lift(colour, 18 * f[y][x] + rng.uniform(-8, 8))
                px[x, y] = M.rgba(M.mix(px[x, y], c, k))
            elif t > -0.02 and rng.random() < 0.4:
                px[x, y] = M.rgba(M.mix(px[x, y], M.lift(colour, -14), 0.5))
    G.flecks(img, seed + 2, 10, (150, 176, 84), 0.5)
    return img


# ---------------- Bark ----------------

def oakbark(seed):
    """Old oak: deep vertical furrows broken into blocky ridges, grey-brown."""
    return G.oak((92, 82, 68), seed)


def beechbark(seed):
    """Beech: smooth pale grey, faint horizontal lenticels, a dark eye-shaped scar or two."""
    img = M.noise_hv((136, 136, 128), 3, seed, mottle=6, hue=2)
    rng = random.Random(seed)
    for _ in range(16):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(2, 4)):
            M.touch(img, x + k, y, -0.12)
    for _ in range(2):
        x, y = rng.randrange(S), rng.randrange(S)
        d = ImageDraw.Draw(img)
        for ox in (-S, 0, S):
            d.ellipse([x + ox - 3, y - 1, x + ox + 3, y + 1], fill=M.rgba((70, 68, 62)))
    G.flecks(img, seed + 1, 20, (170, 176, 160), 0.4)
    return img


def firbark(seed):
    """Old Douglas fir: thick red-brown bark in deep corky ridges."""
    return G.bark((104, 70, 52), seed, wave=1.6)


def sprucebark(seed):
    """Spruce: grey-brown, flaking in small round scales."""
    img = M.noise_hv((96, 84, 70), 4, seed, mottle=6, hue=2)
    pts = M.points(S, 30, seed + 1)
    f1, f2, idx = M.worley(S, pts)
    px = img.load()
    rng = random.Random(seed + 2)
    shade = [rng.uniform(-14, 10) for _ in pts]
    for y in range(S):
        for x in range(S):
            d = shade[idx[y][x]]
            if f2[y][x] - f1[y][x] < 0.9:
                d -= 22
            elif f1[y][x] < 1.2:
                d += 8
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    return img


def deadbark(seed):
    """Dead wood: bark mostly gone, the grey weathered wood under it split along the grain, a few strips of bark left."""
    img = M.noise_hv((150, 146, 136), 3, seed, mottle=7, hue=1)
    px = img.load()
    rng = random.Random(seed)
    wander = M.fbm(S, seed + 1, (32, 16))
    for y in range(S):
        for x in range(S):
            xs = x + 2 * wander[y][x]
            g = math.cos(2 * math.pi * xs / 3.2)
            px[x, y] = M.rgba(M.lift(px[x, y], 8 * g))
    for _ in range(4):  # splits
        x = rng.randrange(S)
        for y in range(S):
            if rng.random() < 0.8:
                M.touch(img, x + int(2 * wander[y][x]), y, -0.3)
    for _ in range(3):  # strips of old bark
        x0, y0, h = rng.randrange(S), rng.randrange(S), rng.randint(6, 14)
        for y in range(y0, y0 + h):
            for x in range(x0, x0 + rng.randint(3, 5)):
                px[x % S, y % S] = M.rgba(M.lift((74, 66, 58), rng.uniform(-8, 6)))
    return img


def greenbark(seed):
    """A green giant's bark: green, deep-furrowed, moss in every furrow."""
    return G.bark((66, 88, 52), seed, 0.55)


BARKS = {"oak": oakbark, "beech": beechbark, "fir": firbark, "spruce": sprucebark, "dead": deadbark, "green": greenbark}
RINGS = {"oak": (120, 96, 66), "beech": (168, 150, 120), "fir": (150, 100, 66), "spruce": (170, 140, 100), "dead": (150, 146, 136), "green": (120, 110, 80)}


def rings(base, seed):
    """A cut end: growth rings, a few cracks out from the middle."""
    n = M.fbm(S, seed, (16, 8))
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - S / 2, y + 0.5 - S / 2
            r = math.hypot(dx, dy) + 1.4 * n[y][x]
            c = M.lift(base, 9 * math.cos(2 * math.pi * r / 2.6) + 4 * n[y][x])
            if r > 14.5:
                c = M.lift(base, -30)
            px[x, y] = M.rgba(c)
    rng = random.Random(seed + 1)
    for _ in range(3):
        a, x, y = rng.uniform(0, 2 * math.pi), S / 2, S / 2
        for k in range(rng.randint(5, 10)):
            a += rng.uniform(-0.4, 0.4)
            x, y = x + math.cos(a), y + math.sin(a)
            M.touch(img, int(x), int(y), -0.25)
    return img


# ---------------- Leaves (cut out: light and sky through the gaps) ----------------

LEAVES = {"oak": (54, 84, 38), "beech": (78, 104, 44), "needle": (38, 62, 44)}


def leafmass(tint, seed, needles=False):
    """A mass of leaves (or needle sprays) with gaps cut through it, so a crown shows sky and depth rather than a green wall."""
    img = M.noise_hv(M.lift(tint, -30), 3, seed, mottle=5)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(56 if not needles else 90):
        x, y = rng.randrange(S), rng.randrange(S)
        c = M.lift(tint, rng.uniform(-16, 14))
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                if needles:
                    a = rng.uniform(0, math.pi)
                    L = rng.randint(3, 6)
                    d.line([x + ox, y + oy, x + ox + math.cos(a) * L, y + oy + math.sin(a) * L], fill=M.rgba(c), width=1)
                else:
                    w, h = rng.randint(3, 5), rng.randint(2, 4)
                    d.ellipse([x + ox, y + oy, x + ox + w, y + oy + h], fill=M.rgba(c))
                    d.line([x + ox + 1, y + oy, x + ox + w - 1, y + oy], fill=M.rgba(M.lift(c, 12)))
    # Gaps: clusters cut right through
    f = M.fbm(S, seed + 5, (8, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            if f[y][x] < -0.28 or rng.random() < 0.04:
                px[x, y] = (0, 0, 0, 0)
    return img


# ---------------- Ground ----------------

def trail(seed):
    """The trail: trodden bare earth, pale and packed, a few stones and leaves pressed into it."""
    img = M.noise_hv((104, 86, 64), 4, seed, mottle=7, hue=2)
    G.flecks(img, seed + 1, 18, (140, 130, 116), 0.6)
    G.flecks(img, seed + 2, 10, (64, 52, 40), 0.6)
    rng = random.Random(seed + 3)
    d = ImageDraw.Draw(img)
    for _ in range(4):
        x, y = rng.randrange(S), rng.randrange(S)
        d.ellipse([x, y, x + 2, y + 1], fill=M.rgba(rng.choice([(120, 90, 50), (100, 104, 64)])))
    return img


def pebbles(seed):
    img = M.noise_hv((90, 86, 78), 3, seed, mottle=5)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(70):
        x, y, r = rng.randrange(S), rng.randrange(S), rng.randint(1, 3)
        c = M.lift(rng.choice([(130, 126, 116), (104, 98, 90), (150, 140, 120), (86, 90, 84)]), rng.uniform(-10, 10))
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.ellipse([x + ox - r, y + oy - r, x + ox + r, y + oy + r], fill=M.rgba(c))
                d.point([x + ox - r + 1, y + oy - r + 1], fill=M.rgba(M.lift(c, 18)))
    return img


def granite(seed):
    """Boulder stone: grey granite, lichen in rosettes."""
    img = M.noise_hv((116, 114, 108), 4, seed, mottle=8, hue=1)
    G.flecks(img, seed + 1, 40, (160, 156, 150), 0.6)
    G.flecks(img, seed + 2, 30, (60, 58, 56), 0.6)
    G.lichened(img, seed + 3, (168, 172, 130), n=2)
    return img


def waystone(seed):
    """The Order's way-stone: dark granite, a snake carved coiling round it, its head up."""
    img = granite(seed)
    px = img.load()
    for t in range(0, 220):
        u = t / 220.0
        x = 16 + 9 * math.sin(u * math.pi * 4)
        y = 30 - u * 26
        for w in (-1, 0, 1):
            xx = int(x + w) % S
            yy = int(y)
            px[xx, yy] = M.rgba(M.lift(px[xx, yy], -38 if w == 0 else -22))
        if int(y) - 1 >= 0:
            M.touch(img, int(x) % S, int(y) - 1, 0.18)
    d = ImageDraw.Draw(img)
    d.ellipse([13, 2, 19, 6], fill=M.rgba((60, 58, 54)))
    return mossed(img, seed + 9, cover=0.2, top_bias=-0.8)


# ---------------- The manor and the stones ----------------

def manorstone(seed, tones=None):
    img = M.brick(seed=seed, base=(128, 126, 118), mortar=(92, 90, 84), course=8, length=16, offset=0.5, mortar_w=1,
                  jitter=10, hue=3, pits=0.06, chamfer=True, grain=5, mottle=8, tones=tones)
    M.grime(img, 0.18, seed=seed + 1, color=(70, 72, 60), cover=0.5)
    return img


def plinth(seed):
    img = M.brick(seed=seed, base=(88, 86, 80), mortar=(60, 58, 54), course=16, length=32, offset=0.5, mortar_w=1,
                  jitter=8, hue=2, pits=0.05, chamfer=True, grain=5, mottle=8)
    return mossed(img, seed + 3, cover=0.3, top_bias=-0.6)


def timber(seed):
    img = M.wood_planks(seed=seed, base=(64, 46, 32), planks=1, direction="h", grain=5, contrast=1.3, knots=1)
    return img


def slate(seed):
    """Slate roof: overlapping dark blue-grey tiles in courses, each a little different, edges lit."""
    img = M.brick(seed=seed, base=(66, 70, 78), mortar=(34, 36, 40), course=8, length=8, offset=0.5, mortar_w=1, jitter=10,
                  hue=3, pits=0.02, grain=4, mottle=6)
    return mossed(img, seed + 7, cover=0.12)


def boards(seed):
    return M.wood_planks(seed=seed, base=(98, 72, 48), planks=4, direction="h", grain=4, knots=1, joints=0.3)


def window(seed):
    """A leaded window: diamond panes of greenish old glass in dark lead, a little light caught in each."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            u, v = (x + y) % 8, (x - y) % 8
            if u == 0 or v == 0:
                px[x, y] = (40, 40, 44, 255)
            else:
                g = rng.uniform(-8, 8) + 10 * (1 - (u + v) / 14)
                px[x, y] = M.rgba(M.lift((120, 146, 132), g), 110)
    for x in range(S):
        px[x, 0] = px[x, S - 1] = (52, 40, 30, 255)
        px[0, x] = px[S - 1, x] = (52, 40, 30, 255)
    return img


def megalith(seed, moss=False):
    """A sarsen: pale grey-brown sandstone, pitted, weathered smooth, rosettes of lichen."""
    img = M.noise_hv((150, 140, 120), 4, seed, mottle=10, hue=2)
    f = M.fbm(S, seed + 1, (16, 8, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y], 14 * f[y][x]))
    G.flecks(img, seed + 2, 40, (96, 88, 74), 0.5)
    G.lichened(img, seed + 3, (186, 182, 120), n=2)
    G.lichened(img, seed + 4, (120, 136, 110), n=1)
    if moss:
        mossed(img, seed + 5, cover=0.35, top_bias=0.6)
    return img


def flagstone(seed):
    img = M.noise_hv((112, 108, 100), 4, seed, mottle=7)
    pts = M.points(S, 6, seed + 1)
    f1, f2, idx = M.worley(S, pts)
    px = img.load()
    rng = random.Random(seed + 2)
    shade = [rng.uniform(-12, 12) for _ in pts]
    for y in range(S):
        for x in range(S):
            if f2[y][x] - f1[y][x] < 1.0:
                px[x, y] = M.rgba(M.mix((56, 72, 36), (40, 46, 32), rng.random() * 0.5))
            else:
                px[x, y] = M.rgba(M.lift(px[x, y], shade[idx[y][x]]))
    return img


def shelf_front(seed):
    """The Order's shelves: old books, jars of something pale, a skull of a snake, scrolls."""
    img = M.wood_planks(seed=seed, base=(70, 50, 34), planks=1, direction="h", grain=4)
    px = img.load()
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for row, y0 in enumerate((2, 18)):
        d.rectangle([1, y0, 30, y0 + 12], fill=M.rgba((26, 20, 16)))
        x = 2
        while x < 29:
            kind = rng.random()
            if kind < 0.65:
                w, h = rng.randint(2, 3), rng.randint(8, 12)
                c = rng.choice([(110, 28, 26), (60, 40, 30), (40, 56, 40), (90, 70, 40), (120, 96, 60), (50, 40, 60)])
                d.rectangle([x, y0 + 12 - h, x + w - 1, y0 + 11], fill=M.rgba(M.lift(c, rng.uniform(-10, 10))))
                d.line([x, y0 + 12 - h + 2, x + w - 1, y0 + 12 - h + 2], fill=M.rgba((176, 150, 80)))
                x += w
            elif kind < 0.85:
                d.rectangle([x, y0 + 5, x + 3, y0 + 11], fill=M.rgba((150, 160, 140), 255))
                d.rectangle([x, y0 + 4, x + 3, y0 + 4], fill=M.rgba((80, 60, 40)))
                d.rectangle([x + 1, y0 + 7, x + 2, y0 + 10], fill=M.rgba((210, 204, 180)))
                x += 5
            else:
                d.ellipse([x, y0 + 7, x + 4, y0 + 11], fill=M.rgba((222, 214, 190)))
                d.point([x + 1, y0 + 9], fill=(30, 26, 20, 255))
                d.point([x + 3, y0 + 9], fill=(30, 26, 20, 255))
                x += 6
        d.rectangle([0, y0 + 13, 31, y0 + 15], fill=M.rgba((84, 60, 40)))
    return img


def ouroboros(d, cx, cy, r, colour, dark):
    """A snake eating its tail: a ring of scales, its head biting its tail at the top."""
    for t in range(0, 360, 4):
        a = math.radians(t)
        w = 1.6 if t < 330 else 1.6 - (t - 330) / 30.0
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        d.ellipse([x - w, y - w, x + w, y + w], fill=colour)
    for t in range(0, 330, 24):
        a = math.radians(t)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        d.point([x, y], fill=dark)
    hx, hy = cx + math.cos(math.radians(-90)) * r, cy + math.sin(math.radians(-90)) * r
    d.ellipse([hx - 2.5, hy - 2, hx + 2.5, hy + 2], fill=colour)
    d.point([hx + 1, hy - 1], fill=(160, 20, 20, 255))


def banner(seed, part):
    """The Order's banner: crimson cloth, gold hem; on the top half the snake eating its tail, on the foot a gold eye and the hem cut in points."""
    img = M.fabric(seed=seed, base=(128, 18, 24), weave="plain", contrast=8)
    d = ImageDraw.Draw(img)
    gold, dark = M.rgba((206, 164, 64)), M.rgba((110, 80, 24))
    d.rectangle([0, 0, 2, 31], fill=gold)
    d.rectangle([29, 0, 31, 31], fill=gold)
    if part == "top":
        d.rectangle([0, 0, 31, 2], fill=gold)
        ouroboros(d, 16, 18, 8, gold, dark)
    else:
        d.polygon([(16, 2), (21, 9), (16, 16), (11, 9)], outline=gold)
        d.ellipse([14, 7, 18, 11], fill=gold)
        for k in range(4):
            d.polygon([(k * 8, 24), (k * 8 + 8, 24), (k * 8 + 4, 31)], fill=gold)
        px = img.load()
        for y in range(25, 32):
            for x in range(S):
                k = x % 8
                if abs(k - 4) < (y - 24) * 4 / 7:
                    continue
                px[x, y] = (0, 0, 0, 0)
    return img


def hearth(seed):
    img = M.noise_hv((30, 28, 26), 3, seed, mottle=6)
    G.flecks(img, seed + 1, 40, (90, 84, 76), 0.6)
    G.flecks(img, seed + 2, 12, (150, 60, 20), 0.5)
    return img


def iron(seed):
    return M.noise_hv((44, 42, 40), 3, seed, mottle=5)


def coals(seed):
    img = M.noise_hv((200, 70, 20), 6, seed, mottle=12, hue=4)
    G.flecks(img, seed + 1, 50, (40, 20, 14), 0.8)
    G.flecks(img, seed + 2, 30, (255, 200, 90), 0.7)
    return img


def wax(seed):
    return M.noise_hv((220, 208, 176), 2, seed, mottle=4)


def flame(seed):
    img = Image.new("RGBA", (S, S), (255, 210, 110, 255))
    return img


# ---------------- The sky (AtmosphereSystem.L47.cs, Regions/L47Sky.cs) ----------------

def moon(seed, size=512):
    """The Moon's far side, full: bright grey highlands crowded with craters, almost no dark maria (Moscoviense a small dark
    patch, Tsiolkovskiy's dark floor), the great South Pole-Aitken basin a darker greyer stain over the south."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    c, R = size / 2, size / 2 - 2
    import numpy as np
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    dx, dy = (xx - c) / R, (yy - c) / R
    r2 = dx * dx + dy * dy
    inside = r2 < 1
    base = np.full((size, size), 188.0)
    # Large-scale tone
    def blob(x0, y0, rad, amt):
        d = np.sqrt((dx - x0) ** 2 + (dy - y0) ** 2)
        return amt * np.clip(1 - d / rad, 0, 1) ** 1.5
    base -= blob(0.05, 0.55, 0.75, 34)    # South Pole-Aitken
    base -= blob(-0.25, -0.45, 0.10, 70)  # Moscoviense
    base -= blob(0.35, 0.25, 0.06, 80)    # Tsiolkovskiy's floor
    base -= blob(-0.55, 0.15, 0.25, 14)
    # Craters: many, all sizes, each a dark floor, a lit rim on the sun side, a shadowed one away
    for _ in range(900):
        rad = 0.008 + 0.09 * rng.random() ** 3
        x0, y0 = rng.uniform(-1, 1), rng.uniform(-1, 1)
        if x0 * x0 + y0 * y0 > 1:
            continue
        d = np.sqrt((dx - x0) ** 2 + (dy - y0) ** 2) / rad
        m = d < 1.25
        if not m.any():
            continue
        floor = np.where(d < 0.85, -10 * (1 - d), 0)
        rim = np.where((d > 0.85) & (d < 1.25), 14 * (1 - abs(d - 1.0) / 0.25), 0)
        side = ((dx - x0) * 0.7 - (dy - y0) * 0.7) / rad
        base += np.where(m, floor + rim * (0.5 + 0.5 * np.clip(side, -1, 1)), 0)
        if rad > 0.05 and rng.random() < 0.3:  # rays
            base += np.where((d > 1.2) & (d < 3.5), 6 * np.clip(np.cos(np.arctan2(dy - y0, dx - x0) * 9) - 0.6, 0, 1) / d, 0)
    noise = np.array([[rng.uniform(-6, 6) for _ in range(size)] for _ in range(0)]) if False else np.random.default_rng(seed).normal(0, 4, (size, size))
    base += noise
    # Limb darkening, a little
    base *= np.where(inside, 0.82 + 0.18 * np.sqrt(np.clip(1 - r2, 0, 1)), 0)
    base = np.clip(base, 0, 255)
    alpha = np.clip((1 - np.sqrt(r2)) * R, 0, 1) * 255
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = np.clip(base * 1.0, 0, 255)
    arr[..., 1] = np.clip(base * 0.99, 0, 255)
    arr[..., 2] = np.clip(base * 0.95, 0, 255)
    arr[..., 3] = alpha
    return Image.fromarray(arr, "RGBA")


def stars(seed, w=2048, h=1024):
    """A night sky that matches no constellation of ours (Wikidot: the stars "do not match any constellations visible
    from The Frontrooms"): an equirectangular map, its top half the sky; stars of every brightness, a few coloured, and the
    Milky Way a broad faint band crossing it with dark lanes. Black where there is nothing (it is added onto the sky)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), dtype=float)
    # The Milky Way: a band along a great circle tilted across the sky
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    lon = xx / w * 2 * math.pi
    lat = (0.5 - yy / h) * math.pi
    vx, vy, vz = np.cos(lat) * np.cos(lon), np.sin(lat), np.cos(lat) * np.sin(lon)
    nx, ny, nz = 0.35, 0.55, 0.76
    nn = math.sqrt(nx * nx + ny * ny + nz * nz)
    band = np.abs(vx * nx / nn + vy * ny / nn + vz * nz / nn)
    glow = np.exp(-(band / 0.16) ** 2)
    fine = rng.normal(0, 1, (h // 8 + 1, w // 8 + 1))
    from PIL import Image as _I
    fine_img = _I.fromarray(((fine - fine.min()) / (fine.max() - fine.min()) * 255).astype(np.uint8)).resize((w, h), _I.BICUBIC)
    fine = np.asarray(fine_img).astype(float) / 255.0
    # (A soft lane of dust down the middle, not blotches)
    lanes = np.exp(-((band - 0.015) / 0.025) ** 2)
    mw = glow * (0.55 + 0.45 * fine) * (1 - 0.45 * lanes)
    img += mw[..., None] * np.array([46, 46, 54])
    # Stars: mostly faint, a few bright, more in the band
    n = 9000
    for k in range(n):
        x, y = rng.integers(0, w), rng.integers(0, h)
        if rng.random() > 0.35 + 0.65 * glow[y, x] and rng.random() < 0.5:
            continue
        mag = rng.random() ** 6
        b = 70 + 185 * mag
        col = np.array([1.0, 1.0, 1.0])
        t = rng.random()
        if t < 0.08:
            col = np.array([1.0, 0.78, 0.6])
        elif t < 0.16:
            col = np.array([0.75, 0.85, 1.0])
        img[y, x] += col * b
        if mag > 0.4:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                img[(y + oy) % h, (x + ox) % w] += col * b * 0.35
    img = np.clip(img, 0, 255).astype(np.uint8)
    # Below the horizon: nothing
    img[h // 2 + 8:, :, :] = 0
    return Image.fromarray(img, "RGB").convert("RGBA")


def aurora(seed, w=512, h=256):
    """Silvery-white aurora: soft vertical rays in a curtain, brightest at its lower edge, fading up (Wikidot: "rare
    silvery-white auroras")."""
    import numpy as np
    rng = np.random.default_rng(seed)
    xs = np.arange(w)
    edge = h * 0.72 + 14 * np.sin(xs / w * 2 * math.pi * 2 + 0.7) + 8 * np.sin(xs / w * 2 * math.pi * 5 + 2.1)
    rays = np.clip(rng.normal(0.6, 0.35, w), 0, 1.4)
    rays = np.convolve(rays, np.ones(5) / 5, mode="same")
    img = np.zeros((h, w, 3), dtype=float)
    for x in range(w):
        for y in range(h):
            above = edge[x] - y
            if above < -3:
                continue
            k = math.exp(-max(0, above) / (h * 0.28)) * (1 if above >= 0 else math.exp(above / 1.5))
            v = 255 * k * rays[x]
            img[y, x] = (v * 0.86, v * 0.95, v * 0.92)
    # fade the left and right ends
    fade = np.clip(np.minimum(xs, w - 1 - xs) / (w * 0.15), 0, 1)
    img *= fade[None, :, None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


# ---------------- Models ----------------

def face(tex, uv):
    return {"texture": tex, "uv": uv}


def box(name, frm, to, tex, faces="nsewud", uvs=None, glow=0):
    names = {"n": "north", "s": "south", "e": "east", "w": "west", "u": "up", "d": "down"}
    out = {"name": name, "from": frm, "to": to, "faces": {}}
    for f in faces:
        fn = names[f]
        if uvs and fn in uvs:
            uv = uvs[fn]
        elif f in "ns":
            uv = [frm[0], 16 - to[1], to[0], 16 - frm[1]]
        elif f in "ew":
            uv = [frm[2], 16 - to[1], to[2], 16 - frm[1]]
        else:
            uv = [frm[0], frm[2], to[0], to[2]]
        out["faces"][fn] = face(tex, uv)
        if glow:
            out["faces"][fn]["glow"] = glow
    return out


def banner_shape(part):
    t = "#cloth"
    return {"textureWidth": 16, "textureHeight": 16, "textures": {"cloth": f"backrooms:block/47/banner-{part}", "wood": "backrooms:block/47/timber"},
            "elements": [box("Cloth", [1, 0, 15], [15, 16, 15.6], t, uvs={"north": [1, 0, 15, 16], "south": [15, 0, 1, 16]})]
            + ([box("Rod", [0, 15, 14.8], [16, 16, 15.8], "#wood")] if part == "top" else [])}


def brazier_shape():
    return {"textureWidth": 16, "textureHeight": 16, "textures": {"iron": "backrooms:block/47/iron", "coals": "backrooms:block/47/coals"},
            "elements": [
                box("Leg1", [3, 0, 3], [4, 8, 4], "#iron"), box("Leg2", [12, 0, 3], [13, 8, 4], "#iron"),
                box("Leg3", [3, 0, 12], [4, 8, 13], "#iron"), box("Leg4", [12, 0, 12], [13, 8, 13], "#iron"),
                box("Bowl", [2, 8, 2], [14, 11, 14], "#iron"),
                box("Coals", [3, 11, 3], [13, 11.6, 13], "#coals", faces="u", glow=200),
                box("Ember1", [5, 11, 6], [8, 12.5, 9], "#coals", glow=255), box("Ember2", [9, 11, 8], [11, 12, 11], "#coals", glow=255),
            ]}


def candles_shape():
    els = [box("Plate", [3, 0, 3], [13, 0.5, 13], "#iron")]
    for k, (x, z, h) in enumerate([(4, 5, 5), (7, 8, 7), (10, 4, 4), (9, 10, 6), (5, 10, 3)]):
        els.append(box(f"Wax{k}", [x, 0.5, z], [x + 1.6, 0.5 + h, z + 1.6], "#wax"))
        els.append(box(f"Wick{k}", [x + 0.5, 0.5 + h, z + 0.5], [x + 1.1, 1.6 + h, z + 1.1], "#flame", glow=255))
    return {"textureWidth": 16, "textureHeight": 16, "textures": {"iron": "backrooms:block/47/iron", "wax": "backrooms:block/47/wax", "flame": "backrooms:block/47/flame"},
            "elements": els}


def lantern_shape():
    src = os.path.join(ASSETS, "shapes", "block", "23", "lantern.json")
    shp = json.load(open(src, encoding="utf-8"))
    shp["textures"] = {k: v.replace("block/23/charred", "block/47/iron").replace("block/23/lantern-glass", "block/47/lantern-glass")
                       for k, v in shp["textures"].items()}
    return shp


# ---------------- Blocktypes ----------------

def drop(code, avg, var=0.0, kind="item"):
    return {"type": kind, "code": code, "quantity": {"avg": avg, "var": var}}


WOOD = ("game:walk/wood*", "game:block/planks")
SOIL = ("game:walk/grass*", "game:block/dirt*")
STONE = ("game:walk/stone*", "game:block/rock-hit-pickaxe")
SNDS = lambda w, d: {"walk": w, "place": d, "break": d, "hit": d}  # noqa: E731


def cube(code, comment, textures, material, sounds, resistance, drops=(), extra=None, faces=None):
    tex = {"base": textures[0]}
    if len(textures) > 1:
        tex["alternates"] = [{"base": t} for t in textures[1:]]
    all_tex = {"all": tex}
    for f, t in (faces or {}).items():
        all_tex[f] = {"base": t}
    b = {"code": code, "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": material, "drawtype": "cube",
         "textures": all_tex, "resistance": resistance, "drops": list(drops), "sounds": SNDS(*sounds)}
    if extra:
        b.update(extra)
    return comment, b


def model(code, comment, shape, textures_by=None, material="Wood", sounds=WOOD, resistance=1.5, drops=(), sides=False, extra=None,
          box_=None):
    b = {"code": code, "creativeinventory": {"general": ["*-north"] if sides else ["*"], "backrooms": ["*-north"] if sides else ["*"]},
         "blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
         "resistance": resistance, "drops": list(drops), "sounds": SNDS(*sounds)}
    if sides:
        b["variantgroups"] = [{"code": "side", "states": SIDES}]
        b["shapeByType"] = {f"*-{s}": {"base": f"block/47/{shape}", "rotateY": ROT[s]} for s in SIDES}
        if box_:
            b["collisionboxByType"] = {f"*-{s}": dict(box_, rotateY=ROT[s]) for s in SIDES}
            b["selectionboxByType"] = {f"*-{s}": dict(box_, rotateY=ROT[s]) for s in SIDES}
    else:
        b["shape"] = {"base": f"block/47/{shape}"}
        if box_:
            b["collisionbox"] = box_
            b["selectionbox"] = box_
    if extra:
        b.update(extra)
    # (A *ByType key given as None means none at all: the plain key carries it)
    for k in [k for k, v in b.items() if v is None and k.endswith("ByType")]:
        b.pop(k)
    return comment, b


def blocks():
    out = []
    names = {"oak": "old oak", "beech": "beech", "fir": "old fir", "spruce": "spruce", "dead": "dead wood, weathered grey", "green": "a green giant's green bark"}
    for k in BARKS:
        ends = {"up": f"block/47/rings-{k}", "down": f"block/47/rings-{k}"}
        firewood = [drop("game:firewood", 0.5, 0.4)] if k != "green" else []
        out.append(cube(f"l47-bark-{k}", f"// Level 47: {names[k]}", [f"block/47/bark-{k}", f"block/47/bark-{k}-2"], "Wood", WOOD,
                        6 if k != "green" else 12, drops=firewood, faces=ends))
        out.append(cube(f"l47-mossbark-{k}", f"// Level 47: {names[k]}, mossed over", [f"block/47/mossbark-{k}", f"block/47/mossbark-{k}-2"], "Wood", WOOD,
                        6 if k != "green" else 12, drops=firewood + [drop("game:drygrass", 0.2, 0.2)], faces=ends))
    for k in LEAVES:
        out.append(("// Level 47: the crowns' " + ("needles" if k == "needle" else k + " leaves") + " (cut out; let a little light by)", {
            "code": f"l47-leaves-{k}", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Leaves", "drawtype": "cube",
            "renderpass": "OpaqueNoCull", "faceCullMode": "CollapseMaterial", "vertexFlags": {"zOffset": 4, "windMode": "Leaves"},
            "textures": {"all": {"base": f"block/47/leaves-{k}", "alternates": [{"base": f"block/47/leaves-{k}-2"}]}},
            "sideopaque": {"all": False}, "sidesolid": {"all": False}, "sideao": {"all": True}, "emitSideAo": {"all": False},
            "replaceable": 4000, "lightAbsorption": 1, "resistance": 0.5, "collisionbox": None,
            "drops": [drop("game:stick", 0.1, 0.1)], "sounds": SNDS("game:walk/grass*", "game:block/plant")}))
    for wood in ("oak", "dead"):
        for axis in ("x", "z"):
            side = f"block/47/log-{wood}"
            faces = {"east": f"block/47/rings-{wood}", "west": f"block/47/rings-{wood}"} if axis == "x" else {"north": f"block/47/rings-{wood}", "south": f"block/47/rings-{wood}"}
            faces["up"] = f"block/47/logtop-{wood}"
            out.append(cube(f"l47-log-{wood}-{axis}", f"// Level 47: a fallen {'dead' if wood == 'dead' else 'old'} trunk lying along {axis}, moss on top",
                            [side], "Wood", WOOD, 5, drops=[drop("game:firewood", 0.5, 0.4)], faces=faces))
    out += [
        cube("l47-humus", "// Level 47: the forest floor's humus", ["block/47/humus", "block/47/humus-2"], "Soil", SOIL, 1.6, drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube("l47-moss", "// Level 47: thick moss over the forest floor", ["block/47/moss", "block/47/moss-2"], "Soil", SOIL, 1.6, drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube("l47-litter", "// Level 47: leaf litter and needles over the humus", ["block/47/litter", "block/47/litter-2"], "Soil", SOIL, 1.4,
             drops=[drop("game:soil-low-none", 1, kind="block"), drop("game:drygrass", 0.4, 0.4)]),
        cube("l47-earth", "// Level 47: dark wet earth", ["block/47/earth", "block/47/earth-2"], "Soil", ("game:walk/gravel*", "game:block/dirt*"), 2,
             drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube("l47-trail", "// Level 47: the trail, trodden bare (it never moves)", ["block/47/trail", "block/47/trail-2"], "Soil", ("game:walk/gravel*", "game:block/dirt*"), 2.5,
             drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube("l47-pebbles", "// Level 47: a stream's bed of pebbles", ["block/47/pebbles"], "Gravel", ("game:walk/gravel*", "game:block/gravel"), 1.5,
             drops=[drop("game:stone-granite", 1.5, 1)]),
        cube("l47-boulder", "// Level 47: granite boulders, lichened", ["block/47/granite", "block/47/granite-2"], "Stone", STONE, 6, drops=[drop("game:stone-granite", 1.5, 1)]),
        cube("l47-boulder-moss", "// Level 47: a boulder's mossed-over top", ["block/47/granite-moss"], "Stone", STONE, 6, drops=[drop("game:stone-granite", 1.5, 1)],
             faces={"up": "block/47/moss"}),
        cube("l47-waystone", "// Level 47: the Ophion Order's way-stone beside the trail, a snake cut coiling round it (our invention)", ["block/47/waystone"],
             "Stone", STONE, 12),
        cube("l47-manorstone", "// Level 47: the manor's grey ashlar", ["block/47/manorstone", "block/47/manorstone-2"], "Stone", STONE, 10),
        cube("l47-manorstone-moss", "// Level 47: the manor's ashlar, moss creeping up it", ["block/47/manorstone-moss"], "Stone", STONE, 10),
        cube("l47-plinth", "// Level 47: the manor's dark plinth and quoins", ["block/47/plinth"], "Stone", STONE, 12),
        cube("l47-timber", "// Level 47: the manor's old dark timber", ["block/47/timber"], "Wood", WOOD, 6, faces={"up": "block/47/rings-oak", "down": "block/47/rings-oak"}),
        cube("l47-slate", "// Level 47: the manor's slate roof", ["block/47/slate", "block/47/slate-2"], "Stone", STONE, 6),
        cube("l47-boards", "// Level 47: the manor's floorboards", ["block/47/boards"], "Wood", WOOD, 4, drops=[drop("game:firewood", 0.5, 0.3)]),
        ("// Level 47: the manor's leaded windows (diamond panes, old greenish glass)", {
            "code": "l47-window", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Glass", "drawtype": "cube",
            "renderpass": "Transparent", "faceCullMode": "NeverCull", "textures": {"all": {"base": "block/47/window"}},
            "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1.5, "drops": [],
            "sounds": {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}}),
        cube("l47-megalith", "// Level 47: the glade's standing stones, sarsens lichened with age", ["block/47/megalith", "block/47/megalith-2"], "Stone", STONE, 20),
        cube("l47-megalith-moss", "// Level 47: a standing stone, mossed at its foot and in its hollows", ["block/47/megalith-moss"], "Stone", STONE, 20),
        cube("l47-flagstone", "// Level 47: the walk up to the manor's door, flagstones with moss between", ["block/47/flagstone"], "Stone", STONE, 8),
        cube("l47-hearth", "// Level 47: a cold hearth, soot and ash", ["block/47/hearth"], "Stone", STONE, 8),
        ("// Level 47: the Order's shelves: old books, jars, a snake's skull (the shelves on the -side's back wall)", {
            "code": "l47-shelf", "variantgroups": [{"code": "side", "states": SIDES}],
            "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}, "blockmaterial": "Wood", "drawtype": "cube",
            "texturesByType": {f"*-{s}": {"all": {"base": "block/47/timber"}, s: {"base": "block/47/shelf"}} for s in SIDES},
            "resistance": 3, "drops": [drop("game:firewood", 0.5, 0.3), drop("game:paper-parchment", 0.4, 0.4)], "sounds": SNDS(*WOOD)}),
        model("l47-lantern", "// Level 47: the Order's lanterns (breaks to nothing, as Level 23's)", "lantern", material="Metal",
              sounds=("game:walk/stone*", "game:block/glass"), resistance=1.5,
              box_={"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 0.65, "z2": 0.7}, extra={"lightHsv": [7, 4, 15]}),
        model("l47-brazier", "// Level 47: an iron brazier of coals by the manor's door (breaks to nothing)", "brazier", material="Metal",
              sounds=("game:walk/stone*", "game:block/anvil"), resistance=3,
              box_={"x1": 0.12, "y1": 0, "z1": 0.12, "x2": 0.88, "y2": 0.75, "z2": 0.88}, extra={"lightHsv": [5, 6, 16]}),
        model("l47-candles", "// Level 47: a dish of candles (breaks to nothing)", "candles", material="Wood", resistance=0.5,
              box_={"x1": 0.18, "y1": 0, "z1": 0.18, "x2": 0.82, "y2": 0.5, "z2": 0.82}, extra={"lightHsv": [8, 5, 9]}),
    ]
    for part in ("top", "foot"):
        out.append(model(f"l47-banner-{part}", f"// Level 47: the Order's banner ({part}): crimson, a gold snake eating its tail; the cloth at the block's back", f"banner-{part}",
                         material="Cloth", sounds=("game:walk/cloth*", "game:block/cloth"), resistance=0.6, sides=True,
                         box_={"x1": 0, "y1": 0, "z1": 0.9, "x2": 1, "y2": 1, "z2": 1}, drops=[drop("game:cloth-plain", 0.3, 0.3)],
                         extra={"collisionboxByType": None, "collisionbox": None}))
    return out


def write_json(path, comment, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write(comment + "\n")
        json.dump(obj, f, indent="\t")
        f.write("\n")


# ---------------- Lang ----------------

LANG = [
    ("level-30", "Level 47: The Adderwood"),
    ("levelhint-30", "Harm no snake. If the black dogs come at night, climb, and wait for the dawn."),
    ("levelname-30", "Level 47"),
    ("level-3001", "The Ophion Glade"),
    ("levelhint-3001", "A manor, and a ring of stones, in the same place. Neither of them is yours."),
    ("level-3002", "The Trail"),
    ("levelhint-3002", "The one thing here that stays where it is."),
]


def block_lang():
    names = {"oak": "Old Oak", "beech": "Beech", "fir": "Old Fir", "spruce": "Spruce", "dead": "Dead Wood", "green": "Green Giant's Bark"}
    out = []
    for k, n in names.items():
        out.append((f"block-l47-bark-{k}", n + (" Bark" if k not in ("dead", "green") else "")))
        out.append((f"block-l47-mossbark-{k}", "Mossy " + n + (" Bark" if k not in ("dead", "green") else "")))
    out += [
        ("blockdesc-l47-bark-green", "A green-barked giant, hollow at its heart. The M.E.G. say the hollow green trees lead into a forest of stone."),
        ("blockdesc-l47-mossbark-green", "A green-barked giant, hollow at its heart. The M.E.G. say the hollow green trees lead into a forest of stone."),
        ("block-l47-leaves-oak", "Oak Leaves"), ("block-l47-leaves-beech", "Beech Leaves"), ("block-l47-leaves-needle", "Needles"),
        ("block-l47-log-oak-*", "Fallen Trunk"), ("block-l47-log-dead-*", "Fallen Dead Trunk"),
        ("block-l47-humus", "Humus"), ("block-l47-moss", "Moss"), ("block-l47-litter", "Leaf Litter"), ("block-l47-earth", "Dark Earth"),
        ("block-l47-trail", "The Trail"),
        ("blockdesc-l47-trail", "Trodden bare by feet that are not yours. Unlike everything else here, it is where you left it."),
        ("block-l47-pebbles", "Stream Pebbles"), ("block-l47-boulder", "Granite Boulder"), ("block-l47-boulder-moss", "Mossy Boulder"),
        ("block-l47-waystone", "Way-Stone"),
        ("blockdesc-l47-waystone", "A post of dark granite by the trail, a snake cut coiling up it. Someone keeps the moss off the carving."),
        ("block-l47-manorstone", "Manor Stone"), ("block-l47-manorstone-moss", "Mossy Manor Stone"), ("block-l47-plinth", "Manor Plinth"),
        ("block-l47-timber", "Old Timber"), ("block-l47-slate", "Slate"), ("block-l47-boards", "Floorboards"), ("block-l47-window", "Leaded Window"),
        ("block-l47-megalith", "Standing Stone"), ("block-l47-megalith-moss", "Mossy Standing Stone"),
        ("blockdesc-l47-megalith", "Older than the house it stands through. Or the house is older than the stone. In the glade, both are true."),
        ("blockdesc-l47-megalith-moss", "Older than the house it stands through. Or the house is older than the stone. In the glade, both are true."),
        ("block-l47-flagstone", "Flagstones"), ("block-l47-hearth", "Cold Hearth"),
        ("block-l47-shelf-*", "The Order's Shelves"),
        ("blockdesc-l47-shelf-*", "Old books in no language you know, jars of something pale, a snake's skull, very large, polished by handling."),
        ("block-l47-lantern", "Lantern"), ("block-l47-brazier", "Brazier"), ("block-l47-candles", "Candles"),
        ("block-l47-banner-*", "The Order's Banner"),
        ("blockdesc-l47-banner-*", "Crimson cloth, a gold snake eating its own tail. The Ophion Occult Order's sign."),
    ]
    return out


def lang_entries():
    """Every key of the level's block: the ones above, the blocks', the creatures' and the level's texts
    (tools/gen_47_lore.py), the handbook page and the notes' track."""
    entries = list(LANG) + block_lang()
    try:
        import gen_47_lore
        entries += list(gen_47_lore.LANG)
    except ImportError:
        pass
    import gen_guide
    if "level47" in gen_guide.PAGES:
        title, text = gen_guide.PAGES["level47"]
        entries.append(("guide-level47-title", title))
        entries.append(("guide-level47-text", gen_guide.to_vtml(text)))
    import gen_notes
    if hasattr(gen_notes, "L47"):
        for t in gen_notes.TRACKS:
            if t.level == gen_notes.L47:
                entries.append((f"journal-track-{t.chapter}", t.title))
                for e in t.entries:
                    entries.append((f"note-{e.key}", gen_notes.to_vtml(e.text)))
                    entries.append((f"notetitle-{e.key}", e.title))
        for t in gen_notes.TRACKS:
            if t.level != gen_notes.L47:
                for e in t.entries:
                    if e.key.startswith("l47-"):
                        entries.append((f"note-{e.key}", gen_notes.to_vtml(e.text)))
                        entries.append((f"notetitle-{e.key}", e.title))
    return entries


def write_lang():
    """Replaces the level's block of lines in en.json (from its level-30 line on, and any of its keys found elsewhere) in
    place, keeping the file's line endings and everything else byte for byte."""
    entries = lang_entries()
    path = os.path.join(ASSETS, "lang", "en.json")
    raw = open(path, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    ours = {k for k, _ in entries}
    key_re = re.compile(rb'^\t"([^"]+)":')
    start = next(i for i, l in enumerate(lines) if l.startswith(b'\t"level-30":'))
    kept = []
    for i, l in enumerate(lines):
        m = key_re.match(l)
        if m and m.group(1).decode() in ours and i != start:
            continue
        kept.append(l)
    at = next(i for i, l in enumerate(kept) if l.startswith(b'\t"level-30":'))
    last = kept[at].rstrip().endswith(b'"')  # (the file's last key has no comma)
    new = [b'\t' + json.dumps(k).encode() + b': ' + json.dumps(v, ensure_ascii=False).encode() + b',' for k, v in entries]
    if last:
        new[-1] = new[-1][:-1]
    kept[at:at + 1] = new
    text = nl.join(kept)
    json.loads(text.decode("utf-8"))
    open(path, "wb").write(text)


def main():
    for k, fn in BARKS.items():
        seed = 4700 + len(k) * 13
        save(fn(seed), f"block/47/bark-{k}")
        save(G.lichened(fn(seed + 1), seed + 2, (150, 160, 128) if k != "dead" else (176, 180, 150)), f"block/47/bark-{k}-2")
        save(mossed(fn(seed), seed + 3, cover=0.55), f"block/47/mossbark-{k}")
        save(mossed(fn(seed + 1), seed + 4, cover=0.7), f"block/47/mossbark-{k}-2")
        save(rings(RINGS[k], seed + 5), f"block/47/rings-{k}")
    save(G.lichened(oakbark(4790), 4791, (120, 150, 80), n=3), "block/47/log-oak")
    save(mossed(oakbark(4792), 4793, cover=0.85), "block/47/logtop-oak")
    save(deadbark(4794).transpose(Image.Transpose.ROTATE_90), "block/47/log-dead")
    save(mossed(deadbark(4795), 4796, cover=0.5), "block/47/logtop-dead")
    for k, tint in LEAVES.items():
        save(leafmass(tint, 4710 + len(k), k == "needle"), f"block/47/leaves-{k}")
        save(leafmass(M.lift(tint, -8), 4720 + len(k), k == "needle"), f"block/47/leaves-{k}-2")
    save(G.humus(4730), "block/47/humus")
    save(G.humus(4731), "block/47/humus-2")
    save(mossed(G.moss(4732), 4733, cover=0.8), "block/47/moss")
    save(mossed(G.moss(4734), 4735, cover=0.7, colour=(80, 112, 44)), "block/47/moss-2")
    save(G.litter(4736, [(110, 84, 50), (140, 104, 60), (96, 70, 44), (76, 82, 52), (150, 120, 70)]), "block/47/litter")
    save(G.litter(4737, [(120, 72, 40), (104, 88, 56), (90, 96, 60), (60, 70, 46), (140, 110, 64)]), "block/47/litter-2")
    save(G.earth(4738), "block/47/earth")
    save(G.earth(4739), "block/47/earth-2")
    save(trail(4740), "block/47/trail")
    save(trail(4741), "block/47/trail-2")
    save(pebbles(4742), "block/47/pebbles")
    save(granite(4743), "block/47/granite")
    save(granite(4744), "block/47/granite-2")
    save(mossed(granite(4745), 4746, cover=0.45, top_bias=0.8), "block/47/granite-moss")
    save(waystone(4747), "block/47/waystone")
    save(manorstone(4750), "block/47/manorstone")
    save(manorstone(4750, tones=4751), "block/47/manorstone-2")
    save(mossed(manorstone(4752), 4753, cover=0.4, top_bias=-0.8), "block/47/manorstone-moss")
    save(plinth(4754), "block/47/plinth")
    save(timber(4755), "block/47/timber")
    save(slate(4756), "block/47/slate")
    save(slate(4757), "block/47/slate-2")
    save(boards(4758), "block/47/boards")
    save(window(4759), "block/47/window")
    save(megalith(4760), "block/47/megalith")
    save(megalith(4761), "block/47/megalith-2")
    save(megalith(4762, moss=True), "block/47/megalith-moss")
    save(flagstone(4763), "block/47/flagstone")
    save(hearth(4764), "block/47/hearth")
    save(shelf_front(4765), "block/47/shelf")
    save(banner(4766, "top"), "block/47/banner-top")
    save(banner(4767, "foot"), "block/47/banner-foot")
    save(iron(4768), "block/47/iron")
    save(coals(4769), "block/47/coals")
    save(wax(4770), "block/47/wax")
    save(flame(4771), "block/47/flame")
    glass = Image.open(os.path.join(TEX, "block", "23", "lantern-glass.png")).convert("RGBA")
    save(glass, "block/47/lantern-glass")
    # The sky
    env = os.path.join(TEX, "environment")
    os.makedirs(env, exist_ok=True)
    moon(4780).save(os.path.join(env, "l47-moon.png"))
    stars(4781).save(os.path.join(env, "l47-stars.png"))
    aurora(4782).save(os.path.join(env, "l47-aurora.png"))

    out = blocks()
    bt = os.path.join(ASSETS, "blocktypes", "47")
    for comment, b in out:
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    sh = os.path.join(ASSETS, "shapes", "block", "47")
    write_json(os.path.join(sh, "banner-top.json"), None, banner_shape("top"))
    write_json(os.path.join(sh, "banner-foot.json"), None, banner_shape("foot"))
    write_json(os.path.join(sh, "brazier.json"), None, brazier_shape())
    write_json(os.path.join(sh, "candles.json"), None, candles_shape())
    write_json(os.path.join(sh, "lantern.json"), None, lantern_shape())
    if "nolang" not in sys.argv:
        write_lang()
    print(f"gen_47: {len(out)} blocktypes, shapes, textures, lang")


if __name__ == "__main__":
    main()
