"""Level 23, "The Petrified Garden" (experimental): its blocks, their textures and models, and its lang keys.
Run under the asset lock: bash tools/locked.sh run python tools/gen_23.py   (its sounds: tools/gen_23_sounds.py)

Writes assets/backrooms/blocktypes/23/l23-*.json, textures/block/23/*.png, shapes/block/23/*.json, and the level's keys
in lang/en.json: one block, from its level-28 line to its last key (the handbook page from gen_guide.py's "level23",
the wanderers' notes from gen_notes.py's "l23" track), in place.

The Garden is petrified: its bark is stone with the grain of bark (grey, redwood red, pale oak, dark cypress; the Green
Giants green and mossy), its cut wood grey rings glinting with mineral. Underfoot humus, moss and leaf litter over dark
wet earth laced with roots; overhead a lid of leaves in three greens. The glow rooms have glowcaps and the Gardener's
Sorries (glowworm-like strands, teal, violet, amber or green). The Architects' ruins are pale weathered limestone, mossy,
with Latin cut into them and a bronze plaque; their pottery is red terracotta with a black band. A buried sentry is a
face pushed out of the bark.
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

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures")
S = 32


def save(img, rel):
    path = os.path.join(TEX, *rel.split("/")) + ".png"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def flecks(img, seed, n, colour, strength=0.8):
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.mix(px[x, y], colour, strength * rng.uniform(0.6, 1.0)))
    return img


def strand(img, seed, colour, width=2, length=(24, 40), dark=0.25, angle=None):
    """A wandering strand (a root, a fibre), wrapping, its middle lit and its edges dark."""
    rng = random.Random(seed)
    px = img.load()
    x, y = rng.uniform(0, S), rng.uniform(0, S)
    a = rng.uniform(0, 2 * math.pi) if angle is None else angle
    for _ in range(int(rng.uniform(*length) * 2)):
        for o in range(-width, width + 1):
            X, Y = int(x - math.sin(a) * o * 0.5) % S, int(y + math.cos(a) * o * 0.5) % S
            edge = abs(o) / max(1, width)
            c = M.lift(colour, 10 * (1 - edge) - 22 * dark * edge)
            px[X, Y] = M.rgba(c)
        a += rng.uniform(-0.25, 0.25)
        x += math.cos(a) * 0.5
        y += math.sin(a) * 0.5
    return img


# ---------------- Bark and wood ----------------

BARKS = {
    "grey": (112, 110, 104),
    "red": (122, 74, 58),
    "pale": (168, 160, 146),
    "dark": (60, 56, 52),
    "green": (66, 88, 52),
}


def bark(base, seed, mossy=0.0, wave=3.0):
    """Petrified bark: wandering vertical furrows (eight px apart, so they meet across the edges), plates broken across,
    the furrows dark, the ridges lit; mineral glints; on the Green Giants, moss in the furrows. A small wave keeps the
    furrows nearly straight (the grey bark, deep-furrowed like an old fir's); the Green Giants' wander."""
    dist = M.fbm(S, seed, (32, 16, 8) if wave < 2 else (16, 8, 4))
    plates = M.value_noise(S, (32, 4), seed + 1)
    img = M.noise_hv(base, 4, seed + 2, mottle=7, hue=2)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r = math.cos(2 * math.pi * (x + wave * dist[y][x]) / 8)
            d = 14 * r + 6 * plates[y][x]
            c = M.lift(px[x, y], d)
            if r < -0.72:
                c = M.lift(c, -24)
            if mossy and r < -0.3 and dist[y][x] > -0.2:
                c = M.mix(c, (88, 118, 52), mossy * (0.6 + 0.4 * dist[y][x]))
            px[x, y] = M.rgba(c)
    # Breaks across the plates: a dark line with a lit edge over it
    rng = random.Random(seed + 3)
    for _ in range(5):
        x0, y0, n = rng.randrange(S), rng.randrange(S), rng.randint(2, 5)
        for k in range(n):
            M.touch(img, x0 + k, y0, -0.22)
            M.touch(img, x0 + k, y0 - 1, 0.12)
    flecks(img, seed + 4, 14, (206, 210, 200), 0.45)
    return img


def redwood(base, seed):
    """Petrified redwood: long soft fibres in flat ridges, narrow deep furrows running nearly straight (a few px of
    wander), the ridges shredding into strings; no plates."""
    img = M.noise_hv(base, 4, seed, mottle=6, hue=2)
    px = img.load()
    rng = random.Random(seed + 1)
    wander = M.fbm(S, seed + 2, (32, 16))
    fibre = [rng.uniform(-12, 12) for _ in range(S)]  # each px column a fibre of its own
    furrows = sorted(rng.sample(range(S), 5))
    for y in range(S):
        for x in range(S):
            xs = (x + int(round(1.5 * wander[y][x]))) % S
            d = fibre[xs] * 0.7
            near = min(min(abs(xs - f), S - abs(xs - f)) for f in furrows)
            if near == 0:
                d -= 34
            elif near == 1:
                d -= 12
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    for k in range(10):  # loose strings over the ridges
        x, y0, n = rng.randrange(S), rng.randrange(S), rng.randint(4, 10)
        for j in range(n):
            M.touch(img, x + (j // 5), y0 + j, 0.14)
    flecks(img, seed + 4, 10, (210, 196, 180), 0.35)
    return img


def oak(base, seed):
    """Petrified pale oak: blocky plates, straight vertical cracks four to seven px apart crossed by short breaks at
    staggered heights; each plate shaded on its own; pale lichen in spots."""
    img = M.noise_hv(base, 4, seed, mottle=6, hue=2)
    px = img.load()
    rng = random.Random(seed + 1)
    cols, x = [], 0
    while x < S:
        w = min(rng.randint(4, 7), S - x)
        if S - x - w < 4:
            w = S - x
        cols.append((x, w))
        x += w
    wob = M.fbm(S, seed + 5, (16, 8))
    plate = {}
    for (x0, w) in cols:
        y, cuts = rng.randrange(10), []
        while len(cuts) < 4:
            cuts.append(y % S)
            y += rng.randint(8, 15)
            if y >= S + cuts[0]:
                break
        cuts = sorted(set(cuts))
        for yy in range(S):
            # which plate this px is in (the cuts wrap round the tile)
            k = sum(1 for c in cuts if c <= yy) % len(cuts)
            shade = plate.setdefault((x0, k), rng.uniform(-9, 9))
            edge = x0 + int(round(1.2 * wob[yy][x0]))  # the crack wanders a px either way
            for xx in range(x0 - 1, x0 + w + 1):
                X = xx % S
                if not (x0 <= xx < x0 + w):
                    continue
                d = shade + 5 * wob[yy][X]
                if X == edge % S:
                    d -= 28
                elif X == (edge + 1) % S:
                    d += 7
                if yy in cuts and (xx - x0) < w - 1:
                    d -= 16
                px[X, yy] = M.rgba(M.lift(px[X, yy], d))
    flecks(img, seed + 3, 22, (176, 186, 160), 0.55)  # lichen
    flecks(img, seed + 4, 8, (224, 226, 218), 0.4)
    return img


def cypress(base, seed):
    """Petrified cypress: thin shaggy strips twisting up round the trunk (a quarter turn of the furrows over the tile, so
    it still meets itself), fibrous, with dark gaps between the strips."""
    img = M.noise_hv(base, 4, seed, mottle=5, hue=2)
    px = img.load()
    dist = M.fbm(S, seed + 1, (16, 8))
    rng = random.Random(seed + 2)
    fibre = [rng.uniform(-8, 8) for _ in range(S)]
    for y in range(S):
        for x in range(S):
            t = x + 0.25 * y + 1.2 * dist[y][x]
            r = math.cos(2 * math.pi * t / 4)
            d = 12 * r + fibre[int(t * 2) % S]
            if r < -0.6:
                d -= 18
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    flecks(img, seed + 3, 8, (170, 164, 150), 0.4)
    return img


def lichened(img, seed, colour=(150, 162, 128), n=2):
    """The alternate of a bark: a ragged patch or two of lichen (or moss) grown over it, thinning out at its edge into
    specks, so a trunk is patched irregularly."""
    rng = random.Random(seed)
    px = img.load()
    noise = M.fbm(S, seed + 1, (8, 4, 2))
    for _ in range(n):
        cx, cy, rad = rng.randrange(S), rng.randrange(S), rng.uniform(5, 9)
        for y in range(S):
            for x in range(S):
                dx = min(abs(x - cx), S - abs(x - cx))
                dy = min(abs(y - cy), S - abs(y - cy)) * 0.8
                e = math.hypot(dx, dy) / rad + 0.9 * noise[y][x]
                if e < 0.75:
                    px[x, y] = M.rgba(M.mix(px[x, y], M.lift(colour, 16 * noise[y][x]), 0.6))
                elif e < 1.05 and rng.random() < 0.35:
                    px[x, y] = M.rgba(M.mix(px[x, y], colour, 0.45))
    return img


def heartwood(base, seed):
    """The cut face of a petrified trunk: grey growth rings round the middle, a few cracks out from it, glints."""
    n = M.fbm(S, seed, (16, 8))
    stone = M.mix(base, (150, 148, 140), 0.5)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - S / 2, y + 0.5 - S / 2
            r = math.hypot(dx, dy) + 1.6 * n[y][x]
            ring = math.cos(2 * math.pi * r / 3.4)
            c = M.lift(stone, 8 * ring + 4 * n[y][x])
            if r > 14.5:
                c = M.lift(base, -10)
            px[x, y] = M.rgba(c)
    rng = random.Random(seed + 1)
    for _ in range(3):  # drying cracks, wandering out from near the middle
        a, x, y = rng.uniform(0, 2 * math.pi), S / 2 + rng.uniform(-3, 3), S / 2 + rng.uniform(-3, 3)
        for k in range(rng.randint(5, 10)):
            a += rng.uniform(-0.5, 0.5)
            x, y = x + math.cos(a), y + math.sin(a)
            M.touch(img, int(x), int(y), -0.22)
    flecks(img, seed + 2, 18, (220, 222, 214), 0.5)
    return img


def root(seed):
    """Root wood: bark turned on its side, its fibres twisted."""
    img = bark((96, 84, 70), seed).transpose(Image.Transpose.ROTATE_90)
    return img


def tangle(seed):
    """The tangle round the forest: roots crossing every way over black earth."""
    img = M.noise_hv((30, 26, 22), 3, seed, mottle=5)
    rng = random.Random(seed)
    for k in range(9):
        c = rng.choice([(86, 76, 64), (72, 64, 56), (104, 92, 76), (64, 70, 52)])
        strand(img, seed + 10 + k, c, width=rng.randint(2, 4), length=(20, 36))
    return img


# ---------------- The ground ----------------

def humus(seed):
    img = M.noise_hv((54, 40, 28), 4, seed, mottle=8, hue=3)
    flecks(img, seed + 1, 30, (92, 74, 44), 0.6)
    flecks(img, seed + 2, 24, (30, 22, 16), 0.7)
    rng = random.Random(seed + 3)
    for _ in range(3):  # twigs
        x, y, a = rng.randrange(S), rng.randrange(S), rng.uniform(0, math.pi)
        for k in range(rng.randint(4, 8)):
            M.touch(img, int(x + math.cos(a) * k), int(y + math.sin(a) * k), 0.18)
    return img


def moss(seed):
    img = M.noise_hv((58, 78, 34), 5, seed, mottle=10, hue=4)
    pts = M.points(S, 22, seed + 1)
    f1, f2, idx = M.worley(S, pts)
    rng = random.Random(seed + 2)
    shades = [rng.uniform(-10, 12) for _ in pts]
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = shades[idx[y][x]] - (14 if f2[y][x] - f1[y][x] < 0.9 else 0) - 3 * f1[y][x]
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    flecks(img, seed + 3, 36, (138, 162, 74), 0.5)
    return img


def litter(seed, colours=None):
    """Leaf litter: grey-green, tan and rust leaves fallen over the humus, each with its midrib (round 3: an alternate in
    drier reds and browns, so the drifts are not one colour)."""
    img = humus(seed)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed + 5)
    colours = colours or [(104, 112, 78), (130, 108, 70), (120, 72, 44), (92, 96, 70), (146, 126, 84)]
    for _ in range(26):
        x, y = rng.randrange(S), rng.randrange(S)
        c = M.lift(rng.choice(colours), rng.uniform(-8, 8))
        w, h = rng.randint(2, 4), rng.randint(1, 2)
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.ellipse([x + ox, y + oy, x + ox + w, y + oy + h], fill=M.rgba(c))
        M.touch(img, x + w // 2, y + h // 2, -0.2)
    return img


def earth(seed):
    img = M.noise_hv((56, 42, 32), 4, seed, mottle=8, hue=2)
    pts = M.points(S, 16, seed + 1)
    f1, f2, idx = M.worley(S, pts)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if f2[y][x] - f1[y][x] < 0.8:
                px[x, y] = M.rgba(M.lift(px[x, y], -10))
    flecks(img, seed + 2, 12, (110, 104, 96), 0.6)  # pebbles
    return img


def rootearth(seed):
    img = earth(seed)
    rng = random.Random(seed + 7)
    for k in range(3):
        strand(img, seed + 20 + k, (96, 84, 70), width=rng.randint(1, 2), length=(18, 30))
    return img


# ---------------- Leaves ----------------

LEAF_TINTS = [(48, 74, 36), (62, 78, 34), (38, 70, 52)]


def leaves(tint, seed, dark=0):
    """A mass of leaves: overlapping leaf shapes over a dark depth, lit along their top edges."""
    img = M.noise_hv(M.lift(tint, -34 - dark), 3, seed, mottle=5)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(48):
        x, y = rng.randrange(S), rng.randrange(S)
        c = M.lift(tint, rng.uniform(-14, 12) - dark)
        w, h = rng.randint(3, 6), rng.randint(2, 4)
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.ellipse([x + ox, y + oy, x + ox + w, y + oy + h], fill=M.rgba(c))
                d.line([x + ox + 1, y + oy, x + ox + w - 1, y + oy], fill=M.rgba(M.lift(c, 12)))
    return img


# ---------------- The Architects' ruins ----------------

def ruinstone(seed, tones=None):
    img = M.brick(seed=seed, base=(172, 164, 140), mortar=(118, 112, 98), course=16, length=32, offset=0.5, mortar_w=1,
                  jitter=8, hue=3, pits=0.05, chamfer=True, grain=5, mottle=8, tones=tones)
    M.grime(img, 0.12, seed=seed + 1, color=(86, 84, 64), cover=0.5)
    return img


def ruinmoss(seed):
    img = ruinstone(seed)
    f = M.fbm(S, seed + 3, (16, 8, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = f[y][x] + 0.5 - y / S * 0.6  # thickest at the top
            if t > 0.15:
                px[x, y] = M.rgba(M.mix(px[x, y], M.lift((62, 86, 36), f[y][x] * 14), min(1, (t - 0.15) * 2.5)))
    return img


# Pixel letters for the inscriptions (3 wide, 5 high)
GLYPHS = {
    "A": ["010", "101", "111", "101", "101"], "C": ["011", "100", "100", "100", "011"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "G": ["011", "100", "101", "101", "011"], "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"], "L": ["100", "100", "100", "100", "111"], "M": ["101", "111", "111", "101", "101"],
    "N": ["101", "111", "111", "111", "101"], "O": ["010", "101", "101", "101", "010"], "P": ["110", "101", "110", "100", "100"],
    "R": ["110", "101", "110", "101", "101"], "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"],
    "V": ["101", "101", "101", "101", "010"], "X": ["101", "101", "010", "101", "101"], " ": ["000"] * 5,
}


def carve(img, lines, top, colour=(70, 66, 54)):
    """Cuts lines of capitals into stone: each stroke dark, its lower edge lit."""
    px = img.load()
    for row, text in enumerate(lines):
        width = len(text) * 4 - 1
        x0 = (S - width) // 2
        y0 = top + row * 7
        for i, ch in enumerate(text):
            g = GLYPHS[ch]
            for gy in range(5):
                for gx in range(3):
                    if g[gy][gx] == "1":
                        X, Y = x0 + i * 4 + gx, y0 + gy
                        px[X, Y] = M.rgba(M.mix(px[X, Y], colour, 0.8))
                        if Y + 1 < S and (gy == 4 or g[gy + 1][gx] == "0"):
                            M.touch(img, X, Y + 1, 0.15)
    return img


LATIN = {
    "a": ["HORTVS", "SACER"],
    "b": ["VENIAM", "PETIMVS"],
    "c": ["OCVLI", "VIRIDES"],
    "d": ["NON", "DELEMVR"],
}


def latin(key, seed):
    img = ruinstone(seed)
    return carve(img, LATIN[key], 3)


def plaque(seed):
    """The Great Sphere's plaque: a bronze plate let into the stone, green with age, lines of tiny letters on it."""
    img = ruinstone(seed)
    px = img.load()
    for y in range(5, 27):
        for x in range(4, 28):
            edge = x in (4, 27) or y in (5, 26)
            c = (120, 90, 52) if not edge else (84, 64, 40)
            c = M.lift(c, random.Random(seed + x * 31 + y).uniform(-6, 6))
            if (x + y * 3) % 11 == 0:
                c = M.mix(c, (70, 128, 104), 0.5)  # verdigris
            px[x, y] = M.rgba(c)
    for row in range(7):
        y = 8 + row * 2 + row // 3
        rng = random.Random(seed + row)
        x = 7
        while x < 25:
            n = rng.randint(1, 4)
            for k in range(n):
                if x + k < 25:
                    px[x + k, y] = M.rgba((62, 46, 30))
            x += n + 1
    return img


def sentry(seed):
    """A buried sentry: a face pushed out of grey bark, eyes shut tight, the mouth open in a scream."""
    img = bark(BARKS["grey"], seed)
    px = img.load()
    cx, cy = 16, 15
    for y in range(S):
        for x in range(S):
            dx, dy = (x + 0.5 - cx) / 8.5, (y + 0.5 - cy) / 11.0
            r = dx * dx + dy * dy
            if r < 1:
                # The face bulges out of the bark: lit above, shadowed below and at its rim
                c = M.lift(px[x, y], 16 * (1 - r) - 18 * max(0, dy) * r)
                if r > 0.82:
                    c = M.lift(c, -18)
                px[x, y] = M.rgba(c)
    dark = (24, 22, 20)
    for ex in (12, 20):  # eyes, shut and sunken
        for k in range(-2, 3):
            px[ex + k, 12] = M.rgba(dark)
            px[ex + k, 13 if abs(k) < 2 else 12] = M.rgba(M.lift(dark, 10))
        M.touch(img, ex, 10, 0.2)
    for y in range(18, 25):  # the mouth, open
        half = 3 - abs(y - 21) // 2
        for x in range(cx - half, cx + half):
            px[x, y] = M.rgba(M.lift(dark, -6 + 4 * (y - 21)))
    for x in range(cx - 1, cx + 1):  # the nose's shadow
        M.touch(img, x, 16, -0.2)
    return img


# ---------------- Glowcaps and Sorries ----------------

GLOW = {"teal": (90, 230, 210), "violet": (196, 120, 250), "amber": (250, 186, 80), "green": (150, 240, 110)}
# The light each gives (hue 0-63, saturation 0-7, brightness): VS's lightHsv
GLOW_HSV = {"teal": 32, "violet": 48, "amber": 7, "green": 20}


def glowcap(colour, seed):
    """A glowcap's cap: its colour, brightest in the middle, speckled."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x + 0.5 - S / 2, y + 0.5 - S / 2) / (S / 2)
            c = M.mix(colour, (255, 255, 240), max(0, 0.4 - r * 0.5))
            c = M.lift(c, rng.uniform(-10, 6) - 20 * r * r)
            px[x, y] = M.rgba(c)
    return img


def stem(seed):
    return M.noise_hv((196, 190, 170), 3, seed, mottle=4)


def sorry_bead(colour, seed):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            seg = (y // 4) % 2
            c = M.lift(colour, rng.uniform(-8, 8) + (10 if seg else -6))
            px[x, y] = M.rgba(c)
    return img


def sorry_strand(seed):
    img = M.noise_hv((150, 156, 140), 3, seed, mottle=3)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 210)
    return img


# ---------------- Pottery ----------------

def terracotta(seed):
    """Red terracotta, worn, a black band with a running meander painted round it."""
    img = M.noise_hv((156, 82, 52), 4, seed, mottle=7, hue=3)
    px = img.load()
    for y in range(12, 20):
        for x in range(S):
            px[x, y] = M.rgba(M.lift((34, 26, 22), random.Random(seed + x + y * 37).uniform(-4, 6)))
    for x in range(S):  # the meander, in the red of the clay
        if (x // 3) % 2 == 0:
            px[x, 14] = M.rgba((150, 80, 52))
        else:
            px[x, 17] = M.rgba((150, 80, 52))
        if x % 3 == 0:
            for y in range(14, 18):
                px[x, y] = M.rgba((150, 80, 52))
    M.grime(img, 0.18, seed=seed + 1, color=(70, 64, 50), cover=0.5)
    return img


# ---------------- Models ----------------

def face(tex, uv, glow=0):
    f = {"texture": tex, "uv": uv}
    if glow:
        f["glow"] = glow
    return f


def box(name, frm, to, tex, glow=0, faces="nsewud"):
    x1, y1, z1 = frm
    x2, y2, z2 = to
    all_faces = {
        "north": face(tex, [x1, 16 - y2, x2, 16 - y1], glow), "south": face(tex, [x1, 16 - y2, x2, 16 - y1], glow),
        "east": face(tex, [z1, 16 - y2, z2, 16 - y1], glow), "west": face(tex, [z1, 16 - y2, z2, 16 - y1], glow),
        "up": face(tex, [x1, z1, x2, z2], glow), "down": face(tex, [x1, z1, x2, z2], glow),
    }
    keys = {"n": "north", "s": "south", "e": "east", "w": "west", "u": "up", "d": "down"}
    return {"name": name, "from": frm, "to": to, "faces": {keys[k]: all_faces[keys[k]] for k in faces}}


def glowcap_shape(colour):
    return {
        "textureWidth": 16, "textureHeight": 16,
        "textures": {"cap": f"backrooms:block/23/glowcap-{colour}", "stem": "backrooms:block/23/glowstem"},
        "elements": [
            box("Stem1", [4, 0, 5], [5, 4, 6], "#stem"), box("Cap1", [2.5, 4, 3.5], [6.5, 5.2, 7.5], "#cap", 200),
            box("Stem2", [10, 0, 9], [11, 6, 10], "#stem"), box("Cap2", [8, 6, 7], [13, 7.4, 12], "#cap", 220),
            box("Stem3", [7, 0, 12], [7.8, 2.5, 12.8], "#stem"), box("Cap3", [5.9, 2.5, 11], [8.9, 3.4, 14], "#cap", 180),
            box("Stem4", [12, 0, 3], [12.7, 3, 3.7], "#stem"), box("Cap4", [11, 3, 2], [13.7, 3.8, 4.7], "#cap", 180),
        ],
    }


def sorry_shape(colour):
    """Gardener's Sorries: a pad on the roof, strands hanging from it, glowing beads down them and at their ends."""
    els = [box("Pad", [3, 15.4, 3], [13, 16, 13], "#strand", faces="nsewd")]
    rng = random.Random(len(colour) * 7 + 3)
    for k in range(7):
        x, z = rng.uniform(3.5, 12), rng.uniform(3.5, 12)
        length = rng.uniform(5, 13)
        els.append(box(f"Strand{k}", [x, 15.4 - length, z], [x + 0.35, 15.4, z + 0.35], "#strand", faces="nsew"))
        els.append(box(f"Bead{k}", [x - 0.45, 15.4 - length - 0.9, z - 0.45], [x + 0.8, 15.4 - length + 0.2, z + 0.8], "#bead", 255))
        if length > 8:
            m = 15.4 - length / 2
            els.append(box(f"Mid{k}", [x - 0.25, m - 0.6, z - 0.25], [x + 0.6, m, z + 0.6], "#bead", 230))
    return {"textureWidth": 16, "textureHeight": 16,
            "textures": {"strand": "backrooms:block/23/sorry-strand", "bead": f"backrooms:block/23/sorry-{colour}"}, "elements": els}


def amphora_shape():
    t = "#clay"
    return {
        "textureWidth": 16, "textureHeight": 16, "textures": {"clay": "backrooms:block/23/terracotta"},
        "elements": [
            box("Foot", [6.5, 0, 6.5], [9.5, 1, 9.5], t), box("Belly", [4.5, 1, 4.5], [11.5, 7, 11.5], t),
            box("Shoulder", [5.5, 7, 5.5], [10.5, 8.5, 10.5], t), box("Neck", [6.8, 8.5, 6.8], [9.2, 11.5, 9.2], t),
            box("RimN", [6.3, 11.5, 6.3], [9.7, 12.2, 7.0], t), box("RimS", [6.3, 11.5, 9.0], [8.2, 12.2, 9.7], t),
            box("RimW", [6.3, 11.5, 7.0], [7.0, 12.2, 9.0], t),
            box("HandleE", [9.2, 8, 7.6], [10.6, 11, 8.4], t), box("HandleW", [5.4, 8, 7.6], [6.8, 11, 8.4], t),
        ],
    }


def shards_shape():
    t = "#clay"
    return {
        "textureWidth": 16, "textureHeight": 16, "textures": {"clay": "backrooms:block/23/terracotta"},
        "elements": [
            box("Base", [5, 0, 5], [10, 1.5, 10], t), box("WallN", [5, 1.5, 5], [10, 3.5, 5.6], t), box("WallW", [5, 1.5, 5.6], [5.6, 2.6, 9], t),
            box("Shard1", [11, 0, 3], [13.5, 0.4, 5], t), box("Shard2", [2, 0, 10], [4.5, 0.4, 11.5], t),
            box("Shard3", [9, 0, 11.5], [11, 0.4, 13.5], t), box("Shard4", [3, 0, 3], [4.2, 0.4, 4.8], t),
        ],
    }


# ---------------- Blocktypes ----------------

def cube_block(code, comment, textures, material, walk, dig, resistance, drops=(), extra=None, faces=None):
    alts = [{"base": t} for t in textures[1:]]
    tex = {"base": textures[0]}
    if alts:
        tex["alternates"] = alts
    all_tex = {"all": tex}
    if faces:
        for f, t in faces.items():
            all_tex[f] = {"base": t}
    b = {
        "code": code,
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": material,
        "drawtype": "cube",
        "textures": all_tex,
        "resistance": resistance,
        "drops": list(drops),
        "sounds": {"walk": walk, "place": dig, "break": dig, "hit": dig},
    }
    if extra:
        b.update(extra)
    return comment, b


def drop(code, avg, var=0.0, kind="item"):
    return {"type": kind, "code": code, "quantity": {"avg": avg, "var": var}}


WOOD = ("game:walk/wood*", "game:block/planks")
SOIL = ("game:walk/grass*", "game:block/dirt*")


def bark_blocks():
    out = []
    names = {"grey": "petrified grey bark", "red": "petrified redwood bark", "pale": "petrified pale oak bark",
             "dark": "petrified cypress bark", "green": "a Green Giant's bark, green and mossy"}
    for kind in BARKS:
        out.append(cube_block(f"l23-bark-{kind}", f"// Level 23: {names[kind]}; its cut ends grey rings",
                              [f"block/23/bark-{kind}", f"block/23/bark-{kind}-2"], "Wood", *WOOD, 7 if kind != "green" else 12,
                              drops=[drop("game:firewood", 0.6, 0.4)] if kind != "green" else [],
                              faces={"up": f"block/23/heartwood-{kind}", "down": f"block/23/heartwood-{kind}"}))
    return out


def sentry_block():
    sides = ["north", "east", "south", "west"]
    tex_by = {}
    for s in sides:
        tex_by[f"*-{s}"] = {"all": {"base": "block/23/bark-grey"}, "up": {"base": "block/23/heartwood-grey"},
                            "down": {"base": "block/23/heartwood-grey"}, s: {"base": "block/23/sentry"}}
    return ("// Level 23: a buried sentry, a face in the bark (the face on the -side); says nothing until someone says it", {
        "code": "l23-sentry",
        "variantgroups": [{"code": "side", "states": sides}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Wood",
        "drawtype": "cube",
        "texturesByType": tex_by,
        "resistance": 9,
        "drops": [],
        "sounds": {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]},
    })


def latin_block():
    keys = list(LATIN)
    return ("// Level 23: a stone of the Architects' ruins with Latin cut into it", {
        "code": "l23-latin",
        "variantgroups": [{"code": "text", "states": keys}],
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Stone",
        "drawtype": "cube",
        "texturesByType": {f"*-{k}": {"all": {"base": f"block/23/latin-{k}"}} for k in keys},
        "resistance": 8,
        "drops": [],
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe",
                   "hit": "game:block/rock-hit-pickaxe"},
    })


def plant_json(code, comment, colours, shape, light_v, select, sounds, drops, glow_tex=True, hang=False):
    return (comment, {
        "code": code,
        "variantgroups": [{"code": "colour", "states": list(colours)}],
        "shapeByType": {f"*-{c}": {"base": f"block/23/{shape(c)}"} for c in colours},
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Plant",
        "drawtype": "json",
        "renderpass": "OpaqueNoCull",
        "faceCullMode": "NeverCull",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "lightHsvByType": {f"*-{c}": [GLOW_HSV[c], 6, light_v] for c in colours},
        "resistance": 0.5,
        "collisionbox": None,
        "selectionbox": select,
        "replaceable": 3000 if not hang else 100,
        "drops": drops,
        "sounds": sounds,
    })


def pottery_block():
    kinds = ["amphora", "shards"]
    return ("// Level 23: the Architects' pottery: a red amphora with a black band, or what is left of a pot", {
        "code": "l23-pottery",
        "variantgroups": [{"code": "kind", "states": kinds}],
        "shapeByType": {f"*-{k}": {"base": f"block/23/{k}"} for k in kinds},
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Ceramic",
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 0.8,
        "collisionboxByType": {"*-amphora": {"x1": 0.28, "y1": 0, "z1": 0.28, "x2": 0.72, "y2": 0.76, "z2": 0.72}, "*-shards": None},
        "selectionboxByType": {"*-amphora": {"x1": 0.28, "y1": 0, "z1": 0.28, "x2": 0.72, "y2": 0.76, "z2": 0.72},
                               "*-shards": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.25, "z2": 0.9}},
        "dropsByType": {
            "*-amphora": [drop("game:cloth-plain", 0.35, 0.35), drop("game:clay-red", 0.6, 0.4)],
            "*-shards": [drop("game:clay-red", 0.3, 0.3)],
        },
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/ceramicplace", "break": "game:block/ceramicbreak",
                   "hit": "game:block/ceramichit"},
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
    ("level-28", "Level 23: The Petrified Garden"),
    ("levelhint-28", "Keep quiet. Whatever you do, never say it is only a matter of time."),
    ("levelname-28", "Level 23"),
    ("level-2801", "The Heart of Water"),
    ("levelhint-2801", "The Green Giants hold up the sky. Leave them be."),
    ("level-2802", "Base Seedling"),
    ("levelhint-2802", "M.E.G. outpost. Water, yes. Food, ask."),
    ("level-2803", "Ruins of the Architects"),
    ("levelhint-2803", "Nothing here is the shape it should be."),
    ("block-l23-bark-grey", "Petrified Bark"),
    ("block-l23-bark-red", "Petrified Redwood Bark"),
    ("block-l23-bark-pale", "Petrified Oak Bark"),
    ("block-l23-bark-dark", "Petrified Cypress Bark"),
    ("block-l23-bark-green", "Green Giant's Bark"),
    ("blockdesc-l23-bark-green", "A Green Giant: one of the trees that hold up the Garden's sky. The M.E.G. say not to tamper with them, and nobody has asked why twice."),
    ("block-l23-root", "Petrified Root"),
    ("block-l23-tangle", "Root Tangle"),
    ("blockdesc-l23-tangle", "Roots fused with roots, bark with bark. The Garden goes on like this further than anyone has dug."),
    ("block-l23-humus", "Humus"),
    ("block-l23-moss", "Moss"),
    ("block-l23-litter", "Leaf Litter"),
    ("block-l23-earth", "Dark Earth"),
    ("block-l23-rootearth", "Rooted Earth"),
    ("block-l23-leaves", "Garden Leaves"),
    ("block-l23-leaves-dense", "Garden Canopy"),
    ("block-l23-ruinstone", "Architects' Stone"),
    ("block-l23-ruinmoss", "Mossy Architects' Stone"),
    ("block-l23-latin-*", "Inscribed Stone"),
    ("blockdesc-l23-latin-a", "Cut deep, in a hurry: HORTVS SACER. \"The garden is sacred.\""),
    ("blockdesc-l23-latin-b", "Cut deep, in a hurry: VENIAM PETIMVS. \"We ask forgiveness.\""),
    ("blockdesc-l23-latin-c", "Cut deep, in a hurry: OCVLI VIRIDES. \"Green eyes.\""),
    ("blockdesc-l23-latin-d", "Cut deep, in a hurry: NON DELEMVR. \"We are not wiped out.\""),
    ("block-l23-plaque", "Bronze Plaque"),
    ("blockdesc-l23-plaque", "In Latin, green with age. It reads: \"We dedicate this Great Sphere of Giza to the Great Gardener, in hopes of forgiveness for the great wrong we have committed. Already our purple eyes have turned green... Our only hope is that, alone and petrified, we will not disappear, as Architects of a failed project.\""),
    ("block-l23-sentry-*", "Buried Sentry"),
    ("blockdesc-l23-sentry-*", "A face in the bark, eyes shut. Someone was trapped here, or something was put here to keep watch. It is quiet. Keep it that way: never say, near one, that it's only a matter of time."),
    ("l23-sentry-scream", "The bark screams, like a rusty chainsaw biting into wood. Your ears ring, and something warm runs out of them."),
    ("block-l23-glowcap-*", "Glowcaps"),
    ("blockdesc-l23-glowcap-*", "Little mushrooms that glow in the Garden's caverns. Not food."),
    ("block-l23-sorry-*", "Gardener's Sorries"),
    ("blockdesc-l23-sorry-*", "Glowing strands hanging from the cavern roof, like glowworms. Listen and you can hear them, all of them, whispering \"sorry\"."),
    ("block-l23-pottery-amphora", "Amphora"),
    ("block-l23-pottery-shards", "Broken Pottery"),
    ("blockdesc-l23-pottery-*", "The Architects' pottery: like something from a museum, only worse made. Some still hold a scrap of cloth."),
    # The ways in and out (src/Thresholds/ThresholdNetwork.L23.cs)
    ("l23-tree-in", "You climb into the hollow, and up through the dark inside the trunk, further than the tree is tall. You come out of another trunk, into a forest of stone under a roof of leaves."),
    ("l23-tree-camp", "You climb up through the dark inside the trunk, and out of a hollow tree into lantern light. Tents, a spring, people: Base Seedling."),
    ("l23-tree-home", "You climb up into the hollow tree, into the dark, further than a light shows. You come out of a trunk standing in warm water, under white tile."),
    ("l23-well", "The water at the bottom of the well pulls, and keeps pulling. You come up in open sea, under a concrete sky."),
]


def lang_entries():
    """Every key of the level's block: the ones above, the handbook page, and the notes' track."""
    import gen_23_r3
    entries = list(LANG) + list(gen_23_r3.LANG)
    import gen_guide
    title, text = gen_guide.PAGES["level23"]
    entries.append(("guide-level23-title", title))
    entries.append(("guide-level23-text", gen_guide.to_vtml(text)))
    import gen_notes
    for t in gen_notes.TRACKS:
        if t.level == gen_notes.L23:
            entries.append((f"journal-track-{t.chapter}", t.title))
            for e in t.entries:
                entries.append((f"note-{e.key}", gen_notes.to_vtml(e.text)))
                entries.append((f"notetitle-{e.key}", e.title))
    # (The level's notes in another level's track: Level 37's, where its trees are)
    for t in gen_notes.TRACKS:
        if t.level != gen_notes.L23:
            for e in t.entries:
                if e.key.startswith("l23-"):
                    entries.append((f"note-{e.key}", gen_notes.to_vtml(e.text)))
                    entries.append((f"notetitle-{e.key}", e.title))
    return entries


def write_lang():
    """Replaces the level's block of lines in en.json (from its level-28 line on, and any of its keys found elsewhere) in
    place, keeping the file's line endings and everything else byte for byte."""
    entries = lang_entries()
    path = os.path.join(ASSETS, "lang", "en.json")
    raw = open(path, "rb").read()
    nl = b"\r\n" if b"\r\n" in raw else b"\n"
    lines = raw.split(nl)
    ours = {k for k, _ in entries}
    key_re = re.compile(rb'^\t"([^"]+)":')
    start = next(i for i, l in enumerate(lines) if l.startswith(b'\t"level-28":'))
    kept = []
    for i, l in enumerate(lines):
        m = key_re.match(l)
        if m and m.group(1).decode() in ours and i != start:
            continue
        kept.append(l)
    at = next(i for i, l in enumerate(kept) if l.startswith(b'\t"level-28":'))
    last = kept[at].rstrip().endswith(b'"')  # (the file's last key has no comma)
    new = [b'\t' + json.dumps(k).encode() + b': ' + json.dumps(v, ensure_ascii=False).encode() + b',' for k, v in entries]
    if last:
        new[-1] = new[-1][:-1]
    kept[at:at + 1] = new
    text = nl.join(kept)
    json.loads(text.decode("utf-8"))
    open(path, "wb").write(text)


def main():
    # Each bark its own grain (round 2: they were one wavy pattern in four tints); the alternate is the same bark with a
    # blotch of lichen or moss over it, so a trunk is patched rather than striped the same all the way up
    makers = {"grey": lambda b, s: bark(b, s, wave=1.3), "red": redwood, "pale": oak, "dark": cypress, "green": lambda b, s: bark(b, s, 0.55)}
    patches = {"grey": (146, 154, 128), "red": (134, 136, 108), "pale": (166, 172, 146), "dark": (92, 104, 72), "green": (96, 132, 54)}
    for kind, base in BARKS.items():
        seed = 2300 + len(kind) * 7
        save(makers[kind](base, seed), f"block/23/bark-{kind}")
        save(lichened(makers[kind](base, seed + 1), seed + 2, patches[kind]), f"block/23/bark-{kind}-2")
        save(heartwood(base, 2310 + len(kind)), f"block/23/heartwood-{kind}")
    save(root(2320), "block/23/root")
    save(root(2321), "block/23/root-2")
    save(tangle(2322), "block/23/tangle")
    save(tangle(2323), "block/23/tangle-2")
    save(humus(2330), "block/23/humus")
    save(humus(2331), "block/23/humus-2")
    save(moss(2332), "block/23/moss")
    save(moss(2333), "block/23/moss-2")
    save(litter(2334), "block/23/litter")
    save(litter(2338, [(138, 70, 40), (112, 58, 36), (150, 104, 56), (96, 70, 44), (160, 120, 70)]), "block/23/litter-2")
    save(earth(2335), "block/23/earth")
    save(earth(2336), "block/23/earth-2")
    save(rootearth(2337), "block/23/rootearth")
    for k, tint in enumerate(LEAF_TINTS):
        save(leaves(tint, 2340 + k), f"block/23/leaves-{k}")
        save(leaves(tint, 2345 + k, dark=14), f"block/23/leavesdense-{k}")
    save(ruinstone(2350), "block/23/ruinstone")
    save(ruinstone(2350, tones=2352), "block/23/ruinstone-2")
    save(ruinmoss(2353), "block/23/ruinmoss")
    save(ruinmoss(2354), "block/23/ruinmoss-2")
    for k in LATIN:
        save(latin(k, 2360 + ord(k)), f"block/23/latin-{k}")
    save(plaque(2370), "block/23/plaque")
    save(sentry(2371), "block/23/sentry")
    for c, rgb in GLOW.items():
        if c != "green":
            save(glowcap(rgb, 2380 + len(c)), f"block/23/glowcap-{c}")
        save(sorry_bead(rgb, 2390 + len(c)), f"block/23/sorry-{c}")
    save(stem(2385), "block/23/glowstem")
    save(sorry_strand(2386), "block/23/sorry-strand")
    save(terracotta(2387), "block/23/terracotta")

    stone_sounds = ("game:walk/stone*", "game:block/rock-hit-pickaxe")
    blocks = bark_blocks() + [
        cube_block("l23-root", "// Level 23: petrified root wood (the roots, the arches between the trees)", ["block/23/root", "block/23/root-2"],
                   "Wood", *WOOD, 6, drops=[drop("game:stick", 1, 1)]),
        cube_block("l23-tangle", "// Level 23: the tangle of fused roots round the forest and under it", ["block/23/tangle", "block/23/tangle-2"],
                   "Wood", *WOOD, 10, drops=[drop("game:stick", 0.5, 0.5)]),
        cube_block("l23-humus", "// Level 23: the forest floor's humus", ["block/23/humus", "block/23/humus-2"], "Soil", *SOIL, 1.6,
                   drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube_block("l23-moss", "// Level 23: moss over earth", ["block/23/moss", "block/23/moss-2"], "Soil", *SOIL, 1.6,
                   drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube_block("l23-litter", "// Level 23: leaf litter over the humus", ["block/23/litter", "block/23/litter-2"], "Soil", "game:walk/grass*", "game:block/dirt*", 1.4,
                   drops=[drop("game:soil-low-none", 1, kind="block"), drop("game:drygrass", 0.4, 0.4)]),
        cube_block("l23-earth", "// Level 23: dark, wet earth", ["block/23/earth", "block/23/earth-2"], "Soil", "game:walk/gravel*", "game:block/dirt*", 2,
                   drops=[drop("game:soil-low-none", 1, kind="block")]),
        cube_block("l23-rootearth", "// Level 23: earth laced with petrified roots", ["block/23/rootearth"], "Soil", "game:walk/gravel*", "game:block/dirt*", 3,
                   drops=[drop("game:soil-low-none", 1, kind="block"), drop("game:stick", 0.4, 0.4)]),
        cube_block("l23-leaves", "// Level 23: the lid's loose underside and the glow rooms' little trees (leaves; let the light by)",
                   ["block/23/leaves-0", "block/23/leaves-1", "block/23/leaves-2"], "Leaves", "game:walk/grass*", "game:block/plant", 0.5,
                   drops=[drop("game:stick", 0.15, 0.15)], extra={"lightAbsorption": 0}),
        cube_block("l23-leaves-dense", "// Level 23: the lid of leaves (each takes two of the sun's light: under eight the forest floor has about six)",
                   ["block/23/leavesdense-0", "block/23/leavesdense-1", "block/23/leavesdense-2"], "Leaves", "game:walk/grass*", "game:block/plant", 0.8,
                   drops=[drop("game:stick", 0.1, 0.1)], extra={"lightAbsorption": 2}),
        cube_block("l23-ruinstone", "// Level 23: the Architects' ruins, pale weathered limestone", ["block/23/ruinstone", "block/23/ruinstone-2"],
                   "Stone", *stone_sounds, 8),
        cube_block("l23-ruinmoss", "// Level 23: the Architects' ruins, mossed over", ["block/23/ruinmoss", "block/23/ruinmoss-2"], "Stone", *stone_sounds, 8),
        cube_block("l23-plaque", "// Level 23: the bronze plaque at the Great Sphere (its translation is its description)", ["block/23/plaque"],
                   "Stone", *stone_sounds, 12),
        latin_block(),
        sentry_block(),
        plant_json("l23-glowcap", "// Level 23: glowcaps on the glow rooms' floors", [c for c in GLOW if c != "green"], lambda c: f"glowcap-{c}", 7,
                   {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.5, "z2": 0.9},
                   {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
                   [drop("game:rot", 0.5, 0.5)]),
        plant_json("l23-sorry", "// Level 23: Gardener's Sorries, glowing strands hanging from the cavern roofs (they whisper: AtmosphereSystem.L23.cs)",
                   list(GLOW), lambda c: f"sorry-{c}", 11,
                   {"x1": 0.15, "y1": 0.2, "z1": 0.15, "x2": 0.85, "y2": 1, "z2": 0.85},
                   {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:effect/squish*", "hit": "game:effect/squish*"},
                   [], hang=True),
        pottery_block(),
    ]
    # Round 3 (2026-11-01): the forest floor's things, Base Seedling's, the signs (tools/gen_23_r3.py)
    import gen_23_r3
    gen_23_r3.textures(save)
    blocks += gen_23_r3.blocks()
    bt = os.path.join(ASSETS, "blocktypes", "23")
    for comment, b in blocks:
        write_json(os.path.join(bt, b["code"] + ".json"), comment, b)
    sh = os.path.join(ASSETS, "shapes", "block", "23")
    for c in GLOW:
        if c != "green":
            write_json(os.path.join(sh, f"glowcap-{c}.json"), None, glowcap_shape(c))
        write_json(os.path.join(sh, f"sorry-{c}.json"), None, sorry_shape(c))
    write_json(os.path.join(sh, "amphora.json"), None, amphora_shape())
    write_json(os.path.join(sh, "shards.json"), None, shards_shape())
    for name, shp in gen_23_r3.shapes().items():
        write_json(os.path.join(sh, name + ".json"), None, shp)
    write_lang()
    print(f"gen_23: {len(blocks)} blocktypes, shapes, textures, lang")


if __name__ == "__main__":
    main()
