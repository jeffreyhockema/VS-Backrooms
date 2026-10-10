"""The Hub's sigils: the crop-circle symbols carved over its doors and painted on the Level Keys.

Each sigil is a composition from a small vocabulary, as in docs/new-levels/hub-plan.md section 4.3: a central disc
(D), concentric rings (R), satellite circles (S), arcs (A), straight ridges (L) and dot spirals (P). Coordinates are
in a unit disc (radius 1 = the inside of the carved recess, +y up). `raster(n, size)` turns one into a boolean grid,
used both for the voxel relief over the doors (gen_hub.py) and for the keys' bows.

Ids are fixed in every world: 0 is the Hub's own, 1-18 one per level, 20 "178" (the open door to the Snackrooms,
Level 6.1), 21-44 the 24 dead doors. 19 (Level 3999, dropped for now) keeps its design here but is not built.
"""
import math
import random

from PIL import Image, ImageDraw

# Line widths in disc units (1 = disc radius): a ridge, a ring, a thin ring
W, THIN = 0.16, 0.11


def D(r, c=(0, 0)):
    return ("disc", c, r)


def R(r, w=W, c=(0, 0)):
    return ("ring", c, r, w)


def S(c, r):
    return ("disc", c, r)


def A(r, a0, a1, w=W, c=(0, 0)):
    """An arc from angle a0 to a1 (degrees, counter-clockwise from +x, +y up)."""
    return ("arc", c, r, a0, a1, w)


def L(p0, p1, w=W):
    return ("line", p0, p1, w)


def ring_of(n, radius, r, start=90.0, sizes=None):
    out = []
    for k in range(n):
        a = math.radians(start + 360.0 * k / n)
        out.append(S((radius * math.cos(a), radius * math.sin(a)), sizes[k % len(sizes)] if sizes else r))
    return out


def on_arc(c, r, items, gap=0.1):
    """Circles sitting on top of an arc: (angle, radius) each."""
    out = []
    for a, sr in items:
        rr = r + W / 2 + sr + gap
        out.append(S((c[0] + rr * math.cos(math.radians(a)), c[1] + rr * math.sin(math.radians(a))), sr))
    return out


def spiral(n, turns, r0, r1, d0, d1):
    out = []
    for k in range(n):
        t = k / (n - 1)
        a = 2 * math.pi * turns * t + math.pi / 2
        rr = r0 + (r1 - r0) * t
        out.append(S((rr * math.cos(a), rr * math.sin(a)), d0 + (d1 - d0) * t))
    return out


LIVE = {
    0: [D(0.2), R(0.6)] + ring_of(10, 0.6, 0.1),                                        # the Hub: ten tunnels round the Tower
    1: [D(0.28), R(0.68)],                                                               # Level 0
    2: [D(0.16), R(0.42), R(0.86)] + ring_of(4, 0.64, 0.1, start=45),                    # Level 1
    3: [L((-0.3, -0.82), (-0.3, 0.82)), L((0.3, -0.82), (0.3, 0.82))]
       + [S((0, y), 0.11) for y in (-0.5, 0, 0.5)],                                      # Level 2: a tunnel and its pipes
    4: [D(0.22)] + [A(0.64, a, a + 80) for a in (10, 130, 250)] + [L((-0.86, -0.5), (0.86, 0.5))],  # Level 3
    5: [R(0.36), R(0.62), R(0.88)] + [S((x, y), 0.07) for x in (-0.13, 0.13) for y in (-0.13, 0.13)],  # Level 4
    6: [D(0.2), R(0.48)] + ring_of(8, 0.76, 0, sizes=[0.14, 0.08]),                       # Level 5
    7: [R(0.72, THIN)],                                                                  # Level 6: almost nothing
    8: [A(r, 20, 160, c=(0, -0.42)) for r in (0.36, 0.7, 1.04)],                         # Level 7: waves
    9: spiral(9, 1.1, 0.0, 0.78, 0.1, 0.16),                                           # Level 8
    10: [D(0.22, (0, 0.36))] + [S((x, -0.4), 0.12) for x in (-0.62, -0.31, 0, 0.31, 0.62)],  # Level 9: houses along a street
    11: [S((x, y), 0.17) for x in (-0.4, 0.4) for y in (-0.4, 0.4)] + [L((0, -0.78), (0, 0.78))],  # Level 10: fields
    12: [D(0.15), R(0.4), R(0.62), R(0.86)] + [L((0, 0.2), (0, 0.9)), L((0, -0.2), (0, -0.9)),
                                                 L((0.2, 0), (0.9, 0)), L((-0.2, 0), (-0.9, 0))],  # Level 11: the city
    13: [R(0.46), R(0.86)] + ring_of(6, 0.66, 0.1),                                      # Level 37
    14: [A(0.92, 25, 155, c=(0, -0.72))] + on_arc((0, -0.72), 0.92, [(128, 0.21), (90, 0.15), (58, 0.1)]),  # Level 94: hills
    15: [L((0, 0.86), (0, -0.28), w=0.2), D(0.17, (0, -0.66))],                          # Level !: an exclamation mark
    16: [S((-0.4, 0.34), 0.2), S((0.4, 0.38), 0.2), S((0, 0.6), 0.2),
         L((-0.4, 0.12), (0, -0.74), w=0.09), L((0.4, 0.16), (0, -0.74), w=0.09), L((0, 0.38), (0, -0.74), w=0.09)],  # Fun: balloons
    17: [D(0.22), R(0.6), L((-0.88, 0.42), (0.88, -0.42))],                              # The End: the ring cut
    18: [S((-0.34, 0.24), 0.17), S((0.34, 0.24), 0.17), A(0.42, 200, 340, c=(0, -0.02))],  # Level 974: a face
    19: [R(0.24), R(0.46), R(0.68), R(0.9)],                                             # (Level 3999, for later)
}

# Which sigil each level's door and key bear; level tags as in the key item codes
LEVEL_SIGIL = {"hub": 0, "l0": 1, "l1": 2, "l2": 3, "l3": 4, "l4": 5, "l5": 6, "l6": 7, "l7": 8, "l8": 9, "l9": 10,
               "l10": 11, "l11": 12, "l37": 13, "l94": 14, "run": 15, "fun": 16, "end": 17, "974": 18, "l3999": 19, "l61": 20}

COUNT = 45
IDS = list(range(COUNT))  # every sigil is built (19, Level 3999 for later, too: the code looks it up)


def dead(n):
    """A random composition for a door to a level the mod lacks, from a fixed seed: the same in every world."""
    rng = random.Random(0x5161 + n * 7919)
    parts = []
    style = rng.choice(["rings", "orbit", "bars", "arcs", "scatter", "spiral"])
    if rng.random() < 0.6:
        parts.append(D(rng.uniform(0.12, 0.26)))
    if style == "rings":
        for r in sorted(rng.sample([0.36, 0.5, 0.64, 0.78, 0.9], rng.randint(1, 3))):
            parts.append(R(r))
        if rng.random() < 0.5:
            parts += ring_of(rng.randint(3, 7), rng.choice([0.5, 0.64]), rng.uniform(0.09, 0.12), start=rng.uniform(0, 90))
    elif style == "orbit":
        rr = rng.uniform(0.5, 0.72)
        parts.append(R(rr, THIN))
        parts += ring_of(rng.randint(2, 6), rr, rng.uniform(0.09, 0.16), start=rng.uniform(0, 360))
    elif style == "bars":
        k = rng.randint(2, 3)
        a = rng.uniform(0, math.pi)
        for i in range(k):
            o = (i - (k - 1) / 2) * 0.32
            dx, dy = math.cos(a), math.sin(a)
            px, py = -dy * o, dx * o
            parts.append(L((px - dx * 0.8, py - dy * 0.8), (px + dx * 0.8, py + dy * 0.8)))
        if rng.random() < 0.6:
            parts.append(R(0.9, THIN))
    elif style == "arcs":
        for r in (0.4, 0.66, 0.9)[: rng.randint(2, 3)]:
            a0 = rng.uniform(0, 360)
            parts.append(A(r, a0, a0 + rng.uniform(90, 250)))
    elif style == "scatter":
        for _ in range(rng.randint(3, 6)):
            a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 0.75)
            parts.append(S((rr * math.cos(a), rr * math.sin(a)), rng.uniform(0.1, 0.2)))
        parts.append(R(0.9, THIN))
    else:
        parts += spiral(rng.randint(6, 10), rng.uniform(0.7, 1.3), 0.1, 0.8, 0.09, 0.15)
        if rng.random() < 0.5:
            parts.append(R(0.92, THIN))
    return parts


def composition(n):
    return LIVE[n] if n in LIVE else dead(n)


def draw(n, size, ink=255, scale=8, margin=0.0):
    """The sigil drawn into a size x size greyscale image (0 = background, `ink` = relief), antialiased."""
    big = size * scale
    img = Image.new("L", (big, big), 0)
    d = ImageDraw.Draw(img)
    half = big / 2
    rad = half * (1 - margin)

    def P(p):
        return (half + p[0] * rad, half - p[1] * rad)

    for part in composition(n):
        kind = part[0]
        if kind == "disc":
            (cx, cy), r = P(part[1]), part[2] * rad
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ink)
        elif kind == "ring":
            (cx, cy), r, w = P(part[1]), part[2] * rad, part[3] * rad
            d.ellipse([cx - r - w / 2, cy - r - w / 2, cx + r + w / 2, cy + r + w / 2], outline=ink, width=max(1, int(round(w))))
        elif kind == "arc":
            (cx, cy), r, a0, a1, w = P(part[1]), part[2] * rad, part[3], part[4], part[5] * rad
            # PIL measures angles clockwise from +x in image space (y down): flip
            d.arc([cx - r - w / 2, cy - r - w / 2, cx + r + w / 2, cy + r + w / 2], -a1, -a0, fill=ink, width=max(1, int(round(w))))
            for a in (a0, a1):  # round the ends
                ex, ey = cx + r * math.cos(math.radians(a)), cy - r * math.sin(math.radians(a))
                d.ellipse([ex - w / 2, ey - w / 2, ex + w / 2, ey + w / 2], fill=ink)
        elif kind == "line":
            p0, p1, w = P(part[1]), P(part[2]), part[3] * rad
            d.line([p0, p1], fill=ink, width=max(1, int(round(w))))
            for p in (p0, p1):
                d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=ink)
    return img.resize((size, size), Image.LANCZOS)


def raster(n, size, threshold=110):
    """The sigil as a size x size grid of booleans (row 0 at the top)."""
    img = draw(n, size)
    px = img.load()
    return [[px[x, y] >= threshold for x in range(size)] for y in range(size)]
