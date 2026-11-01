"""Level 52, "The Greenfield Campus": the new textures (walls, lockers, facades, floors, ceilings, turf, courts, paving,
glass, mesh, plaque digits, the sun). Every function returns Pillow RGBA images (32 px) built on the shared material
kit (matlib); gen_52.py saves them and writes the blocks. Nothing here writes a file."""
import math
import random

import numpy as np
from PIL import Image

import matlib as M

S = 32


def fill(img, box, colour, rng=None, amp=0):
    """Fills box (x0, y0, x1, y1; end exclusive) with colour plus a little grain."""
    p = img.load()
    for y in range(box[1], box[3]):
        for x in range(box[0], box[2]):
            c = M.lift(colour, rng.uniform(-amp, amp)) if rng and amp else colour
            p[x % img.width, y % img.height] = M.rgba(c, p[x % img.width, y % img.height][3])
    return img


def hline(img, y, x0, x1, f):
    for x in range(x0, x1):
        M.touch(img, x, y, f)


def vline(img, x, y0, y1, f):
    for y in range(y0, y1):
        M.touch(img, x, y, f)


def rain(img, seed, strength=0.10, streaks=9):
    """Light rain streaks running down from the top of a panel (they wrap, so blocks stack without a break)."""
    rng = random.Random(seed)
    for _ in range(streaks):
        x, w = rng.randrange(S), rng.choice((1, 1, 2))
        y0, n = rng.randrange(S), rng.randint(10, 28)
        for k in range(n):
            f = -strength * (1 - k / n) ** 0.7 * rng.uniform(0.7, 1.0)
            for dx in range(w):
                M.touch(img, x + dx, y0 + k, f)
    return img


def tie_holes(img, spots, f=-0.3):
    for (x, y) in spots:
        M.touch(img, x, y, f)
        M.touch(img, x + 1, y, f * 0.5)
        M.touch(img, x, y + 1, f * 0.5)
        M.touch(img, x + 1, y + 1, -f * 0.25)


# ======================================================================== Walls

PAL = {
    "beige": dict(lower=(204, 186, 150), upper=(233, 229, 215), skirt=(72, 62, 54), rail=(168, 146, 108)),
    "white": dict(lower=(231, 229, 223), upper=(231, 229, 223), skirt=(176, 176, 172), rail=(212, 211, 205)),
    "blue": dict(lower=(78, 112, 156), upper=(232, 232, 228), skirt=(40, 48, 62), rail=(56, 84, 122)),
    "grey": dict(lower=(158, 150, 140), upper=(233, 229, 219), skirt=(78, 72, 68), rail=(122, 114, 104)),
}


def block_joints(img):
    """Faint mortar joints of 16 px painted blocks: courses at y 0 and 16, the head joints staggered."""
    for row in range(2):
        y0 = row * 16
        hline(img, y0, 0, S, -0.10)
        hline(img, y0 + 1, 0, S, 0.035)
        xj = 0 if row == 0 else 16
        vline(img, xj, y0 + 1, y0 + 16, -0.09)
        vline(img, xj + 1, y0 + 1, y0 + 16, 0.03)


def wall(palette, part, seed):
    c = PAL[palette]
    paint = c["upper"] if part == "upper" else c["lower"]
    blue = palette == "blue"
    img = M.plaster(seed, base=paint, grain=5 if blue else 3, mottle=6, roller=0.75 if blue else 0.5)
    if palette == "white":
        block_joints(img)
    rng = random.Random(seed + 7)
    if part == "base":
        M.grime(img, 0.08, seed, bias="bottom", cover=0.4)
        fill(img, (0, 28, S, S), c["skirt"], rng, 3)
        hline(img, 28, 0, S, 0.0)
        for x in range(S):  # the skirting's lit top edge, the paint's shadow above it
            p = img.load()
            p[x, 28] = M.rgba(M.lift(p[x, 28][:3], 12))
            M.touch(img, x, 27, -0.10)
            M.touch(img, x, 26, -0.04)
            M.touch(img, x, 31, -0.10)
    if part == "dado":
        p = img.load()
        for x in range(S):
            p[x, 1] = M.rgba(M.lift(c["rail"], 12 + rng.uniform(-2, 2)))
            p[x, 2] = M.rgba(M.lift(c["rail"], rng.uniform(-2, 2)))
            p[x, 3] = M.rgba(M.lift(c["rail"], -16 + rng.uniform(-2, 2)))
            M.touch(img, x, 4, -0.13)
            M.touch(img, x, 5, -0.05)
    return img


# ======================================================================== Lockers

LOCK = {"beige": (108, 130, 148), "white": (188, 192, 194), "blue": (44, 60, 104), "grey": (104, 116, 78)}


def slits(img, x0, x1, ys, dark):
    p = img.load()
    for y in ys:
        for x in range(x0 + 2, x1 - 1):
            p[x, y] = M.rgba(dark)
            p[x, y + 1] = M.rgba(M.lift(p[x, y + 1][:3], 12))


def locker(palette, part, seed):
    """Three steel locker doors across the block, seams between them; latches and a louvre below, vents and plates above."""
    steel = LOCK[palette]
    img = M.painted_metal(seed, base=steel, grain=3, mottle=4, panel=False, chips=3)
    p = img.load()
    rng = random.Random(seed)
    dark = M.shade_px(steel, -0.5)
    doors = [(1, 10), (12, 21), (23, 31)]
    for x0, x1 in doors:
        tint = rng.uniform(-3, 3)
        for y in range(S):
            for x in range(x0, x1 + 1):
                u = (x - x0) / (x1 - x0)
                p[x, y] = M.rgba(M.lift(p[x, y][:3], tint + 4 - 8 * abs(u - 0.35)))
        M.bevel(img, (x0, 0, x1 + 1, S), 1, 0.14)
    for sx in (0, 11, 22):
        for y in range(S):
            p[sx, y] = M.rgba(M.lift(dark, rng.uniform(-2, 2)))
    if part == "lower":
        fill(img, (0, 28, S, S), M.shade_px(steel, -0.55), rng, 2)
        hline(img, 27, 0, S, -0.35)
        for x in range(S):
            p[x, 28] = M.rgba(M.lift(p[x, 28][:3], 10))
        for x0, x1 in doors:
            fill(img, (x1 - 3, 2, x1, 8), M.shade_px(steel, -0.4), rng, 1)  # the latch recess
            fill(img, (x1 - 2, 3, x1 - 1, 7), (178, 184, 190), rng, 4)
            slits(img, x0, x1, (19, 21, 23), dark)
            for (hx, hy) in ((x0, 3), (x0, 22)):  # hinge pins
                p[hx + 1, hy] = M.rgba(M.lift(steel, -30))
    else:
        fill(img, (0, 0, S, 2), M.shade_px(steel, -0.28), rng, 2)
        for x0, x1 in doors:
            slits(img, x0, x1, (4, 6, 8, 10), dark)
            fill(img, (x0 + 3, 16, x1 - 2, 20), (208, 206, 194), rng, 3)  # the number plate
            M.bevel(img, (x0 + 3, 16, x1 - 2, 20), 1, 0.2)
            for k in range(rng.randint(2, 3)):
                fill(img, (x0 + 4 + 2 * k, 17, x0 + 5 + 2 * k, 19), (58, 58, 58))
    M.scratches(img, n=3, seed=seed, length=(3, 7), light=0.18)
    return img


# ======================================================================== Exterior

def formwork(img, seed, tie=True):
    M.emboss_lines(img, xs=(0,), ys=(0,), raised=False, strength=0.12)
    if tie:
        tie_holes(img, [(8, 8), (24, 8), (8, 24), (24, 24)])


def facade(kind, seed):
    if kind == "white":
        img = M.concrete(seed, base=(228, 226, 220), grain=3, mottle=5, aggregate=0.0, pores=0.012, patches=3, patch_hue=2)
        formwork(img, seed)
        rain(img, seed + 1, 0.09, 10)
    elif kind == "beige":
        img = M.plaster(seed, base=(208, 192, 160), grain=4, mottle=7, roller=1.0, bumps=0.02)
        M.emboss_lines(img, ys=(0,), raised=False, strength=0.08)
        M.grime(img, 0.06, seed + 2, color=(110, 98, 80), cover=0.4)
        rain(img, seed + 1, 0.07, 8)
    elif kind == "brick":
        img = M.brick(seed, base=(176, 140, 106), mortar=(200, 192, 176), jitter=10, hue=5)
        rain(img, seed + 1, 0.06, 6)
    elif kind == "grey":
        img = M.concrete(seed, base=(152, 152, 148), grain=3, mottle=6, aggregate=0.04, pores=0.015, patches=4, patch_hue=2)
        # Precast panel joints: a recessed caulked groove, and four fixings
        for k, f in ((0, -0.20), (1, -0.12)):
            hline(img, k, 0, S, f)
            vline(img, k, 0, S, f)
        hline(img, 2, 0, S, 0.04)
        vline(img, 2, 0, S, 0.04)
        for (x, y) in ((6, 6), (25, 6), (6, 25), (25, 25)):
            M.touch(img, x, y, 0.12)
            M.touch(img, x + 1, y + 1, -0.28)
        rain(img, seed + 1, 0.08, 9)
    elif kind == "blue":
        img = M.concrete(seed, base=(82, 116, 160), grain=3, mottle=5, aggregate=0.03, pores=0.02, patches=3, patch_hue=3)
        formwork(img, seed, tie=False)
        M.hue_jitter(img, 3, seed, 8)
        rain(img, seed + 1, 0.09, 10)
    return img


def coping(part, seed):
    if part == "top":
        img = M.concrete(seed, base=(168, 166, 160), grain=3, mottle=5, aggregate=0.05, pores=0.015, patches=3)
        M.bevel(img, None, 3, 0.16)
        M.emboss_lines(img, xs=(0,), raised=False, strength=0.10)
        vline(img, 16, 3, S - 3, -0.03)
        return img
    img = M.concrete(seed, base=(192, 190, 184), grain=3, mottle=5, aggregate=0.04, pores=0.015, patches=3)
    M.grime(img, 0.07, seed + 1, color=(104, 98, 88), bias="bottom", cover=0.4)
    for x in range(S):  # the drip groove
        M.touch(img, x, 26, -0.30)
        M.touch(img, x, 25, -0.08)
        M.touch(img, x, 27, 0.05)
    rain(img, seed + 2, 0.07, 6)
    return img


def barrier(part, seed):
    if part == "top":
        img = M.concrete(seed, base=(190, 186, 176), grain=3, mottle=5, aggregate=0.06, pores=0.02, patches=4)
        M.bevel(img, None, 3, 0.12)
        return img
    img = M.concrete(seed, base=(184, 180, 170), grain=3, mottle=6, aggregate=0.08, pores=0.025, patches=4, patch_hue=3)
    for x in range(S):  # a flat cap face, then the chamfer, lit, then the shadow under it
        M.touch(img, x, 1, 0.07)
        M.touch(img, x, 3, 0.12)
        M.touch(img, x, 4, 0.06)
        M.touch(img, x, 5, -0.26)
        M.touch(img, x, 6, -0.10)
        M.touch(img, x, 7, -0.03)
    M.grime(img, 0.14, seed + 1, color=(86, 80, 66), bias="bottom", cover=0.5)
    rain(img, seed + 2, 0.06, 6)
    return img


# Round 2: the trim that breaks up a façade (string courses and cornices, a plinth, entrance frames) and the entrance canopies

BAND_BASE = {"light": (230, 226, 216), "grey": (142, 143, 140), "stone": (198, 178, 142)}


def band(kind, seed):
    """A precast string course / cornice / door surround: a smooth band with a lit top arris and a drip groove near the bottom."""
    img = M.concrete(seed, base=BAND_BASE[kind], grain=2, mottle=4, aggregate=0.02, pores=0.01, patches=2)
    for x in range(S):
        M.touch(img, x, 0, 0.10)
        M.touch(img, x, 1, 0.05)
        M.touch(img, x, 27, -0.22)
        M.touch(img, x, 28, -0.08)
        M.touch(img, x, 31, -0.10)
    M.emboss_lines(img, xs=(0,), raised=False, strength=0.10)
    M.grime(img, 0.05, seed + 1, color=(100, 94, 84), bias="bottom", cover=0.35)
    return img


def plinth(seed):
    """The building's base course: dark grey honed stone panels with a joint, splashed a little by rain."""
    img = M.concrete(seed, base=(92, 92, 90), grain=3, mottle=5, aggregate=0.10, pores=0.02, patches=3)
    M.emboss_lines(img, xs=(0, 16), ys=(0,), raised=False, strength=0.14)
    for x in range(S):
        M.touch(img, x, 1, 0.14)
    M.grime(img, 0.08, seed + 1, color=(60, 56, 50), bias="bottom", cover=0.5)
    return img


def canopy_fascia(seed):
    """The edge of an entrance canopy: a powder-coated charcoal metal fascia with a lit top lip and panel joints."""
    img = M.painted_metal(seed, base=(66, 70, 74), grain=2, mottle=3, panel=False, chips=0)
    for x in range(S):
        M.touch(img, x, 0, 0.30)
        M.touch(img, x, 1, 0.12)
        M.touch(img, x, 30, -0.15)
        M.touch(img, x, 31, -0.25)
    M.emboss_lines(img, xs=(0,), raised=False, strength=0.18)
    return img


def canopy_soffit(seed):
    """The underside of a canopy: pale metal planks running across, a recessed downlight disc in the middle."""
    img = steel(seed, (196, 198, 196), 4)
    M.emboss_lines(img, ys=(0, 8, 16, 24), raised=False, strength=0.10)
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 15.5, y - 15.5)
            if d < 3.2:
                px[x, y] = (250, 246, 228, 255)
            elif d < 4.3:
                px[x, y] = (150, 150, 148, 255)
    return img


def slab_concrete(seed):
    img = M.concrete(seed, base=(158, 156, 150), grain=3, mottle=6, aggregate=0.05, pores=0.015, patches=3, patch_hue=2)
    M.ao_border(img, 1, 0.08)
    return img


# ======================================================================== Floors, ceilings, roof

CARPET = {
    "carpetblue": ((62, 82, 112), (82, 100, 128)),
    "carpetred": ((108, 48, 54), (130, 70, 70)),
    "carpetgreen": ((68, 98, 78), (88, 116, 92)),
    "carpetgrey": ((108, 110, 112), (128, 128, 126)),
}


def carpet_tiles(kind, seed):
    base, tone2 = CARPET[kind]
    img = M.carpet(seed, base=base, tone2=tone2, mix2=0.25, loop=True, nap="se", grain=4, mottle=6, wear=0.1)
    rng = random.Random(seed)
    p = img.load()
    for qx in range(2):  # each 16 px carpet tile its own shade, and the seams between
        for qy in range(2):
            d = rng.uniform(-4, 4)
            for y in range(qy * 16, qy * 16 + 16):
                for x in range(qx * 16, qx * 16 + 16):
                    p[x, y] = M.rgba(M.lift(p[x, y][:3], d))
    for k in (0, 16):
        hline(img, k, 0, S, -0.10)
        vline(img, k, 0, S, -0.10)
        hline(img, k + 1, 0, S, 0.02)
        vline(img, k + 1, 0, S, 0.02)
    return img


def lino(seed):
    img = M.noise_hv((172, 184, 170), 3, seed, S, 4, (8, 4), hue=1.5)
    rng = random.Random(seed)
    p = img.load()
    for _ in range(170):  # the fleck of a lab linoleum
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, rng.choice((-0.14, -0.09, 0.07, 0.10)))
    fb = M.fbm((S, S), seed + 3, (4, 2))
    for y in range(S):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y][:3], fb[y][x] * 5))
    hline(img, 0, 0, S, -0.05)  # the welded seam
    hline(img, 1, 0, S, 0.025)
    return img


def sealed_concrete(seed):
    img = M.concrete(seed, base=(138, 138, 134), grain=3, mottle=6, aggregate=0.02, pores=0.006, swirl=0.6, patches=3, patch_hue=2)
    M.emboss_lines(img, xs=(0,), ys=(0,), raised=False, strength=0.09)
    return img


def ceiling_tile(seed):
    """A suspended mineral-fibre ceiling: 2 x 2 tiles of 16 px in the grid bars."""
    img = Image.new("RGBA", (S, S))
    for i in range(4):
        t = M.ceiling_tile(seed + i, size=16, base=(232, 229, 218), fissures=0.5)
        img.paste(t, ((i % 2) * 16, (i // 2) * 16))
    return img


def troffer(on, seed):
    """The ceiling grid with a recessed 2 x 4 troffer in place of two tiles: a white diffuser (grey when dead)."""
    img = ceiling_tile(seed)
    p = img.load()
    rng = random.Random(seed)
    x0, y0, x1, y1 = 2, 9, 30, 23  # outer frame, end exclusive
    for y in range(y0 - 1, y1 + 1):  # the shadow ring round the opening
        for x in range(x0 - 1, x1 + 1):
            if x < x0 or x >= x1 or y < y0 or y >= y1:
                M.touch(img, x, y, -0.10)
    for y in range(y0, y1):
        for x in range(x0, x1):
            edge = x in (x0, x1 - 1) or y in (y0, y1 - 1)
            if edge:
                c = M.lift((222, 222, 216), (7 if (x == x0 or y == y0) else -9) + rng.uniform(-2, 2))
            else:
                v = (y - y0 - 0.5) / (y1 - y0 - 1)
                band = max(math.exp(-((v - c0) * 6.5) ** 2) for c0 in (0.3, 0.7))
                prism = 3 if (x + y) % 2 == 0 else -3
                if on:
                    c = M.lift((244, 244, 234), band * 9 + prism + rng.uniform(-1.5, 1.5), 0.08)
                else:
                    c = M.lift((168, 172, 170), -band * 7 + prism + rng.uniform(-1.5, 1.5), 0.05)
            p[x, y] = M.rgba(c)
    return img


def roof(seed):
    """A flat roof: grey bituminous membrane with scattered gravel ballast."""
    img = M.noise_hv((92, 95, 96), 3, seed, S, 4, (8, 4), hue=1.0)
    rng = random.Random(seed)
    p = img.load()
    for _ in range(95):
        x, y = rng.randrange(S), rng.randrange(S)
        base = rng.choice(((150, 148, 142), (118, 116, 112), (170, 164, 150), (96, 98, 100), (132, 126, 116)))
        big = rng.random() < 0.3
        cells = [(0, 0), (1, 0), (0, 1), (1, 1)] if big else [(0, 0)]
        for dx, dy in cells:
            p[(x + dx) % S, (y + dy) % S] = M.rgba(M.lift(base, rng.uniform(-4, 4)))
        M.touch(img, x, y, 0.12)
        M.touch(img, x + (2 if big else 1), y + (2 if big else 1), -0.22)
    return img


# ======================================================================== Turf and courts

def turf_top(worn, seed):
    img = M.noise_hv((84, 150, 62), 5, seed, S, 4, (16, 8), hue=2.0)
    rng = random.Random(seed)
    p = img.load()
    for y in range(S):  # faint rows of the turf
        d = 3.5 if (y // 4) % 2 == 0 else -3.5
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y][:3], d))
    for _ in range(150):  # blades: short vertical strokes, tips lit
        x, y, n = rng.randrange(S), rng.randrange(S), rng.randint(2, 4)
        tone = rng.uniform(-9, 9)
        for k in range(n):
            M.touch(img, x, y + k, (tone + (8 if k == 0 else 0)) / 190)
    if worn:
        mask = M.fbm((S, S), seed + 9, (4, 2), 0.5)
        for y in range(S):
            for x in range(S):
                t = max(0.0, min(1.0, (mask[y][x] - 0.18) / 0.35))
                if t > 0:
                    pale = M.lift((150, 170, 92), rng.uniform(-4, 4) + 2 * ((y // 4) % 2))
                    p[x, y] = M.rgba(M.mix(p[x, y][:3], pale, 0.6 * t))
    return img


def turf_side(seed):
    top = turf_top(False, seed)
    img = M.rubber(seed + 1, base=(46, 43, 41), grain=6, mottle=5)
    rng = random.Random(seed)
    p, tp = img.load(), top.load()
    for _ in range(190):  # crumb granules
        x, y = rng.randrange(S), rng.randrange(S)
        base = rng.choice(((30, 28, 28), (62, 58, 54), (74, 66, 58), (38, 38, 36), (84, 78, 70)))
        p[x, y] = M.rgba(M.lift(base, rng.uniform(-4, 4)))
    depth = [9 + rng.randint(-2, 2) for _ in range(S)]
    for x in range(S):
        if x > 0:
            depth[x] = max(6, min(12, (depth[x] + depth[x - 1] * 2) // 3 + rng.choice((-1, 0, 0, 1))))
    depth[S - 1] = depth[0]
    for x in range(S):
        for y in range(depth[x]):
            p[x, y] = M.rgba(M.lift(tp[x, (y + 3) % S][:3], -6 + 8 * (1 - y / depth[x])))
        M.touch(img, x, depth[x], -0.35)  # the shadow where the blades meet the crumb
        M.touch(img, x, depth[x] + 1, -0.12)
    return img


def court(line, seed):
    img = M.noise_hv((158, 88, 70), 4, seed, S, 6, (16, 8), hue=2.0)
    rng = random.Random(seed)
    p = img.load()
    for _ in range(120):  # acrylic sand
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((-0.10, -0.06, 0.07, 0.11)))
    if line:
        ref = M.lum((158, 88, 70))
        white = (232, 230, 222)
        for a in range(S):
            for k, t in ((14, 0.25), (15, 1.0), (16, 1.0), (17, 1.0), (18, 0.25)):
                x, y = (k, a) if line == "ns" else (a, k)
                under = p[x, y][:3]
                c = M.lift(white, (M.lum(under) - ref) * 0.45)
                p[x, y] = M.rgba(M.mix(under, c, 0.9 * t))
    return img


def paving(variant, seed):
    """Pale grey concrete slabs of 16 px with thin joints; b has a crack and a stain."""
    img = M.concrete(seed, base=(176, 175, 170), grain=3, mottle=5, aggregate=0.03, pores=0.015, patches=3, patch_hue=2)
    rng = random.Random(seed)
    p = img.load()
    for qx in range(2):
        for qy in range(2):
            d = rng.uniform(-5, 5)
            for y in range(qy * 16, qy * 16 + 16):
                for x in range(qx * 16, qx * 16 + 16):
                    p[x, y] = M.rgba(M.lift(p[x, y][:3], d))
    if variant == "b":
        M.stain(img, seed + 4, radius=7, color=(120, 108, 84), strength=0.30, at=(9, 22))
        M.crack(img, seed + 5, at=(20, 4), length=(10, 18), strength=0.30)
    for k in (0, 16):
        hline(img, k, 0, S, -0.22)
        vline(img, k, 0, S, -0.22)
        hline(img, k + 1, 0, S, 0.05)
        vline(img, k + 1, 0, S, 0.05)
    return img


# ======================================================================== Glass, mesh, frame, rail

def window_glass(seed):
    return M.glass(seed, base=(186, 216, 212), alpha=62, streaks=2, dust=0.02, edge=False, grain=2)


def window_frame(seed):
    return M.painted_metal(seed, base=(232, 234, 234), grain=2, mottle=3, panel=False, chips=0)


def chainlink_mesh(seed):
    gal = M.galvanised(seed, base=(176, 180, 182), spangle=10, grain=2)
    gp = gal.load()
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    p = img.load()
    for y in range(S):
        for x in range(S):
            a, b = (x + y) % 4 == 0, (x - y) % 4 == 0
            if a or b:
                c = gp[x, y][:3]
                d = 12 if (a and b) else (7 if a else -7)
                p[x, y] = M.rgba(M.lift(c, d), 255)
            else:
                p[x, y] = M.rgba(gp[x, y][:3], 0)
    return img


def chainlink_rail(seed):
    """A galvanised tube seen from the side: the sheen runs across it (rows), brightest a little above the middle."""
    img = M.galvanised(seed, base=(168, 172, 174), spangle=14, grain=2)
    p = img.load()
    for y in range(S):
        t = (y - 11) / 14.0
        d = 20 * math.exp(-t * t * 2.2) - 10 + (-12 if y > 24 else 0)
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y][:3], d))
    return img


# ======================================================================== Fountain

def steel(seed, base=(172, 176, 180), streak=7):
    return M.brushed_metal(seed, base=base, grain=3, direction="h", streak=streak, sheen=8, drift=0.05)


def fountain_basin(seed):
    img = steel(seed, (128, 132, 136), 5)
    rng = random.Random(seed)
    for _ in range(14):  # water spots
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((0.12, -0.12)))
    return img


def fountain_chrome(seed):
    img = steel(seed, (206, 210, 214), 10)
    p = img.load()
    for y in range(S):
        d = 22 * math.exp(-((y - 9) / 6.0) ** 2) - 12 * (y > 20)
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y][:3], d))
    return img


# ======================================================================== Plaque

FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}
PLATE = (46, 48, 52)
INK = (226, 222, 208)


def plaque_plate(seed):
    img = M.noise_hv(PLATE, 2, seed, S, 3, (8, 4), hue=0.5)
    M.bevel(img, None, 1, 0.3)
    return img


def digit(ch, seed):
    """A glyph of a 5 x 7 font on the plate colour; the texture covers a 2.35 x 3.4 unit face, so the cells are 5 x 3 px."""
    img = M.noise_hv(PLATE, 2, seed, S, 3, (8, 4), hue=0.5)
    p = img.load()
    rng = random.Random(seed + int(ch))
    for r, row in enumerate(FONT[ch]):
        for c, bit in enumerate(row):
            if bit == "1":
                for dy in range(3):
                    for dx in range(5):
                        shade = -10 if dy == 2 else (4 if dy == 0 else 0)
                        p[3 + c * 5 + dx, 5 + r * 3 + dy] = M.rgba(M.lift(INK, shade + rng.uniform(-2, 2)))
    return img


# ======================================================================== Sun

def sun():
    n = 64
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(xx - (n - 1) / 2, yy - (n - 1) / 2)
    r0 = 0.3 * n
    core = np.clip((r0 - d) / 1.8, 0, 1)
    glow = np.exp(-(np.maximum(d - r0, 0) / 6.5) ** 2) * 0.55
    window = np.clip((n / 2 - 0.5 - d) / 6.0, 0, 1)  # reaches zero at the image edge
    glow = glow * window
    alpha = np.clip(np.maximum(core, glow), 0, 1)
    mix = np.clip(core, 0, 1)
    out = np.zeros((n, n, 4), np.uint8)
    for k, (c, g) in enumerate(zip((255, 252, 240), (255, 232, 176))):
        out[..., k] = np.clip(g + (c - g) * mix, 0, 255)
    out[..., 3] = np.round(alpha * 255)
    return Image.fromarray(out, "RGBA")


# ======================================================================== The ways in, in other levels (links round)

def _text(img, s, box, colour, px, stroke=0):
    """Text centred in box (x0, y0, x1, y1), px high in capitals: drawn four times over and scaled down, so it stays crisp."""
    from PIL import ImageDraw, ImageFont
    x0, y0, x1, y1 = box
    k = 4
    big = Image.new("RGBA", ((x1 - x0) * k, (y1 - y0) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    size = px * k * 1.38
    while True:
        font = ImageFont.load_default(size=size)
        l, t, r, b = d.textbbox((0, 0), s, font=font, stroke_width=stroke * k)
        if r - l <= big.width * 0.96 and b - t <= big.height * 0.96 or size < 8:
            break
        size *= 0.94
    d.text(((big.width - (r - l)) / 2 - l, (big.height - (b - t)) / 2 - t), s, font=font, fill=tuple(colour) + (255,),
           stroke_width=stroke * k, stroke_fill=tuple(colour) + (255,))
    img.alpha_composite(big.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))


SIGN = 64  # the signs are drawn at 64 px a block, for letters that read from across the street


def school_sign(seed):
    """HIGH SCHOOL over a city high school's front doors, four blocks across (returned whole, 256 x 64): cast cream letters
    on a maroon panel framed in tarnished brass, the kind of sign a 1960s school board put up and nobody has cleaned."""
    w, h = SIGN * 4, SIGN
    img = M.noise_hv((112, 26, 34), 3, seed, (w, h), 5, (32, 16), hue=0.5)
    rng = random.Random(seed)
    p = img.load()
    brass = (150, 118, 62)
    for x in range(w):
        for y in list(range(0, 4)) + list(range(h - 4, h)):
            p[x, y] = M.rgba(M.lift(brass, rng.uniform(-8, 8) - (10 if y in (3, h - 4) else 0)))
    for y in range(h):
        for x in list(range(0, 4)) + list(range(w - 4, w)):
            p[x, y] = M.rgba(M.lift(brass, rng.uniform(-8, 8)))
    # Letters with a dark drop shadow: raised, not painted
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _text(shadow, "HIGH SCHOOL", (10, 12, w - 6, h - 8), (40, 8, 12), 30, stroke=1)
    img.alpha_composite(shadow)
    _text(img, "HIGH SCHOOL", (8, 10, w - 8, h - 10), (232, 220, 186), 30, stroke=1)
    # Weathering: a few streaks down from the letters
    for _ in range(14):
        x, y = rng.randrange(8, w - 8), rng.randrange(36, 50)
        for k in range(rng.randint(4, 10)):
            if y + k < h - 4:
                M.touch(img, x, y + k, -0.08)
    return img


def school_sign_back(seed):
    """The sign's edges and back: the same maroon panel's brass frame, plain."""
    img = M.noise_hv((120, 96, 52), 3, seed, S, 4, (8, 4), hue=0.5)
    M.bevel(img, None, 1, 0.25)
    return img


def exit_sign(wall, seed):
    """A green EMERGENCY EXIT sign on Level 4's office wall (64 px): EMERGENCY across the top, a figure running out through a
    door and EXIT below; dusty along its top edge. `wall` is the office wall texture it hangs on."""
    img = wall.convert("RGBA").resize((SIGN, SIGN), Image.NEAREST)
    rng = random.Random(seed)
    green, white = (22, 138, 70), (240, 246, 238)
    x0, y0, x1, y1 = 3, 12, SIGN - 3, 50
    p = img.load()
    for y in range(y0 - 1, y1 + 1):
        for x in range(x0 - 1, x1 + 1):
            edge = y in (y0 - 1, y1) or x in (x0 - 1, x1)
            p[x, y] = M.rgba((210, 214, 210) if edge else M.lift(green, rng.uniform(-6, 6) + (y1 - y) * 0.3))
    _text(img, "EMERGENCY", (x0 + 2, y0 + 1, x1 - 2, y0 + 13), white, 10, stroke=0)
    # The door frame and a figure running out through it, at the left of the lower half
    fy = y0 + 15
    for y in range(fy, y1 - 2):
        for x in (x0 + 3, x0 + 4):
            p[x, y] = M.rgba(white)
    for x in range(x0 + 3, x0 + 13):
        p[x, fy] = M.rgba(white)
    figure = [(8, 3), (9, 3), (8, 4), (9, 4), (7, 6), (8, 6), (9, 6), (10, 6), (6, 7), (8, 7), (11, 7), (8, 8), (8, 9), (7, 10), (9, 10),
              (6, 11), (10, 11), (5, 12), (11, 12), (11, 13)]
    for fx, fz in figure:
        for dy in range(2):
            for dx in range(2):
                p[x0 + fx * 2 - 6 + dx, fy + fz * 2 - 4 + dy] = M.rgba(white)
    _text(img, "EXIT", (x0 + 20, fy + 1, x1 - 2, y1 - 2), white, 18, stroke=1)
    for x in range(x0, x1):
        if rng.random() < 0.5:
            M.touch(img, x, y0, -0.12)
    return img
