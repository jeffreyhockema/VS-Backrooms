"""Textures for the Level 1 props rebuilt as geometry (graphics pass, "Level 1 props": workbench, toolbox, steel door,
caution sign, power box, breaker panel, drum, fire hose cabinet, standpipe, fire alarm, security camera, extinguisher).

Called from `detail_textures.level1` (the detail props) and, for the drum, from `gen_textures.drum`. Every key here is
new and starts with `l1`, `cam` or `oildrum-`: the old shared keys (`wood`, `steel`, `redmetal`, `metal`, `firealarm`
...) are also used by other levels' props and are left as they were. Each model part's face shows its texture from the
corner, so wear is scattered (no edge chips) and printed art sits in the top-left of the 32x32 texture, sized to the
part (2 px per unit): a plate N units wide and M tall shows the top-left 2N x 2M px.

Lettering is drawn in a 3x5 pixel face (`FONT`), crisp, never scaled type.
"""
import math
import random

import matlib as M
from PIL import Image

from detail_kit import T, seed_of

S = 32

# A 3x5 capital face, 1 = ink (N, M and W are the usual compromises at this size)
FONT = {
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"), "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"), "E": ("111", "100", "110", "100", "111"), "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"), "H": ("101", "101", "111", "101", "101"), "I": ("111", "010", "010", "010", "111"),
    "K": ("101", "101", "110", "101", "101"), "L": ("100", "100", "100", "100", "111"), "M": ("101", "111", "111", "101", "101"),
    "N": ("110", "101", "101", "101", "101"), "O": ("010", "101", "101", "101", "010"), "P": ("110", "101", "110", "100", "100"),
    "R": ("110", "101", "110", "101", "101"), "S": ("011", "100", "010", "001", "110"), "T": ("111", "010", "010", "010", "010"),
    "U": ("101", "101", "101", "101", "111"), "V": ("101", "101", "101", "101", "010"), "W": ("101", "101", "111", "111", "101"),
    "X": ("101", "101", "010", "101", "101"), "Y": ("101", "101", "010", "010", "010"),
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"), "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"), "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"), "7": ("111", "001", "010", "010", "010"), "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"), " ": ("0", "0", "0", "0", "0"),
}


def save(img, name):
    T.save(img, f"block/detail/{name}.png")


def rgb(c, a=255):
    return tuple(c) + (a,)


def word_width(s, gap=1):
    return sum(len(FONT[c][0]) for c in s) + gap * (len(s) - 1)


def word(img, s, x, y, ink, gap=1):
    """Draws a word in the 3x5 face with its top-left at (x, y); returns the x after it."""
    px = img.load()
    for c in s:
        g = FONT[c]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == "1" and 0 <= x + i < img.size[0] and 0 <= y + j < img.size[1]:
                    px[x + i, y + j] = rgb(ink)
        x += len(g[0]) + gap
    return x


def rect(img, x1, y1, x2, y2, c):
    """Fills x1..x2, y1..y2 inclusive."""
    px = img.load()
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
                px[x, y] = rgb(c) if len(c) == 3 else c


def plate_edge(img, w, h, light=0.16, dark=-0.22):
    """A bevelled edge on the printed part of a plate (w x h px, top-left): lit top and left, shaded bottom and right."""
    for x in range(w):
        M.touch(img, x, 0, light)
        M.touch(img, x, h - 1, dark)
    for y in range(h):
        M.touch(img, 0, y, light * 0.6)
        M.touch(img, w - 1, y, dark * 0.6)


def enamel(key, base, chips=3, under=(150, 146, 140), grime=0.12, grime_color=(70, 64, 54), rust=0.0):
    img = M.painted_metal(seed_of(key), base=base, grain=2, mottle=3, panel=False, chips=chips, under=under)
    if rust:
        M.rust(img, rust, seed_of(key + "rust"), color=(128, 66, 36), dark=(80, 46, 30))
    if grime:
        M.grime(img, grime, seed_of(key + "grime"), color=grime_color, cover=0.5)
    return img


# ---------------- Materials ----------------

def materials():
    save(enamel("l1grey", (138, 142, 146), chips=3), "l1grey")
    save(enamel("l1greydark", (84, 88, 92), chips=2, under=(120, 120, 118)), "l1greydark")
    save(enamel("l1seam", (40, 42, 46), chips=0, grime=0.05), "l1seam")
    save(enamel("l1red", (176, 38, 30), chips=3, under=(120, 40, 34)), "l1red")
    save(enamel("l1reddark", (108, 24, 20), chips=2, under=(80, 30, 26)), "l1reddark")
    save(enamel("l1yellow", (226, 184, 30), chips=3, under=(170, 140, 40), grime=0.18), "l1yellow")
    save(enamel("l1white", (232, 230, 222), chips=2, under=(176, 174, 168), grime=0.12), "l1white")
    save(M.brushed_metal(seed_of("l1steel"), base=(164, 168, 172), grain=3), "l1steel")
    save(M.brushed_metal(seed_of("l1steeldark"), base=(98, 102, 106), grain=3), "l1steeldark")
    save(M.rubber(seed_of("l1black"), base=(30, 30, 33), grain=2, mottle=3), "l1black")
    save(M.rubber(seed_of("l1cord"), base=(40, 92, 50), grain=3, mottle=3), "l1cord")
    save(enamel("l1iron", (50, 62, 58), chips=4, under=(110, 112, 110), grime=0.1), "l1iron")
    save(enamel("l1toolred", (172, 36, 28), chips=5, under=(112, 112, 108), grime=0.16), "l1toolred")
    save(enamel("l1toolred2", (172, 36, 28), chips=1, under=(112, 112, 108), grime=0.1), "l1toolred2")

    # Wood: legs and rails upright, a worn top, plywood, hardboard
    wood = M.wood_planks(seed_of("l1wood"), base=(134, 98, 62), planks=4, direction="v", grain=3, flecks=1.0)
    M.grime(wood, 0.14, seed_of("l1woodgrime"), color=(70, 56, 40), cover=0.5)
    save(wood, "l1wood")
    wood = M.wood_planks(seed_of("l1woodh"), base=(134, 98, 62), planks=4, direction="h", grain=3, flecks=1.0)
    M.grime(wood, 0.14, seed_of("l1woodhgrime"), color=(70, 56, 40), cover=0.5)
    save(wood, "l1woodh")
    top = M.wood_planks(seed_of("l1benchtop"), base=(164, 122, 76), planks=[8, 8, 8, 8], direction="h", grain=3, flecks=1.2)
    M.grime(top, 0.3, seed_of("l1benchtopgrime"), color=(78, 62, 44), cover=0.6)
    M.stain(top, seed_of("l1benchstain"), radius=5, color=(58, 50, 40), strength=0.4, at=(20, 14))  # an oil ring
    M.scratches(top, 9, seed_of("l1benchscratch"), length=(4, 10), light=0.18)
    save(top, "l1benchtop")
    ply = M.wood_planks(seed_of("l1ply"), base=(200, 166, 112), planks=[32], direction="h", grain=3, flecks=0.7, per_plank=0)
    for x in range(S):  # the ply's edge ring is not wanted on the face
        ply.putpixel((x, 0), ply.getpixel((x, 3)))
        ply.putpixel((x, S - 1), ply.getpixel((x, S - 4)))
    M.grime(ply, 0.2, seed_of("l1plygrime"), color=(90, 74, 50), cover=0.5)
    save(ply, "l1ply")
    # Pegboard: hardboard with a hole every 4 px, each a lit lower lip
    peg = M.noise_hv((152, 122, 84), 3, seed_of("l1peg"), S, 5, (16, 8))
    for y in range(2, S, 4):
        for x in range(2, S, 4):
            M.touch(peg, x, y, -0.5)
            M.touch(peg, x, y + 1, 0.12)
    M.grime(peg, 0.22, seed_of("l1peggrime"), color=(84, 66, 46), cover=0.5)
    save(peg, "l1peg")
    # The hose: flax-white canvas in coils, a dark seam each turn
    hose = M.fabric(seed_of("l1hose"), base=(200, 184, 146), weave="twill", contrast=6, grain=2, mottle=4, thread=2)
    for y0 in range(0, S, 4):
        for x in range(S):
            M.touch(hose, x, y0, -0.3)
            M.touch(hose, x, y0 + 1, 0.1)
    M.grime(hose, 0.3, seed_of("l1hosegrime"), color=(90, 76, 54), cover=0.6)
    save(hose, "l1hose")
    # A canvas web strap and the hose's rubber
    save(M.rubber(seed_of("l1hoserubber"), base=(40, 38, 36), grain=2), "l1hoserubber")


# ---------------- Printed plates ----------------

def warning_decal():
    """The power box's decal: a black-edged yellow triangle with an exclamation mark, 10 x 9 px (5 x 4.5 units)."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    tri = ["....##....", "...#..#...", "...#..#...", "..#.##.#..", "..#.##.#..", ".#..##..#.", ".#......#.", "#...##...#", "##########"]
    for j, row in enumerate(tri):
        for i, c in enumerate(row):
            img.putpixel((i, j), rgb((22, 22, 20) if c == "#" else (232, 192, 32)))
    # outside the triangle the plate is the yellow of its sides
    for j, row in enumerate(tri):
        for i in range(10):
            edge = row.find("#"), row.rfind("#")
            if i < edge[0] or i > edge[1]:
                img.putpixel((i, j), rgb((232, 192, 32)))
    plate_edge(img, 10, 9, 0.1, -0.18)
    return img


def caution_sign():
    """The wet-floor sign's face: 28 x 30 px of yellow with CAUTION across the top, WET and FLOOR, and a figure on its back."""
    img = enamel("l1signyellow", (232, 190, 28), chips=0, under=(180, 150, 40), grime=0.1)
    ink = (22, 22, 20)
    word(img, "CAUTION", 0, 2, ink)  # 27 px: the face starts at the left edge, the sign is 14 units (28 px) wide
    for x in range(0, 27):
        img.putpixel((x, 8), rgb(ink))
    word(img, "WET", 8, 11, ink)
    word(img, "FLOOR", 4, 18, ink)
    # a figure losing its feet (a head, a leaning body, a leg each way, the floor)
    fig = [(14, 24), (13, 25), (14, 25), (15, 25), (13, 26), (15, 26), (12, 27), (16, 27), (11, 28), (17, 28)]
    px = img.load()
    for (x, y) in fig:
        px[x, y] = rgb(ink)
    for x in range(9, 20):
        px[x, 29] = rgb(ink)
    M.touch(img, 0, 0, 0.0)
    return img


def extinguisher_sign():
    """A red square with a white extinguisher: the plate is 3.5 x 3.5 units (7 x 7 px)."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rect(img, 0, 0, 6, 6, (190, 34, 28))
    w = (240, 236, 226)
    for (x, y) in [(3, 1), (2, 1), (2, 2), (3, 2), (2, 3), (3, 3), (2, 4), (3, 4), (2, 5), (3, 5), (4, 2), (5, 3), (4, 1)]:
        img.putpixel((x, y), rgb(w))
    plate_edge(img, 7, 7, 0.12, -0.2)
    return img


def label_plate(text, w, h, ground, ink, edge=True):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rect(img, 0, 0, w - 1, h - 1, ground)
    word(img, text, (w - word_width(text)) // 2, (h - 5) // 2, ink)
    if edge:
        plate_edge(img, w, h, 0.12, -0.2)
    return img


def wired_glass():
    """A door's wired glass seen dark: green-black, a wire diamond mesh every 4 px, a lit corner, a dirty foot."""
    img = M.noise_hv((26, 34, 34), 2, seed_of("l1wired"), S, 3, (16, 8))
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], 22))
            if 7 <= (x + (S - 1 - y)) % 32 <= 9 and 3 < x < 28:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], 12))
    M.grime(img, 0.35, seed_of("l1wiredgrime"), color=(44, 48, 40), bias="bottom", cover=0.7)
    return img


def cabinet_glass():
    """Glass for a cabinet door, cut out of the opaque pass: nearly all clear, a few short glints, a film of dust
    at the foot and a lit rim. 24 x 28 px of it is used."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for (x0, y0, L) in ((5, 4, 4), (9, 8, 3), (17, 18, 5), (21, 13, 3)):
        for i in range(L):
            px[x0 + i, y0 + L - i] = (230, 240, 240, 255)
    rng = random.Random(seed_of("l1cabglass"))
    for y in range(18, 28):  # dust, thicker toward the foot
        for x in range(0, 24):
            if rng.random() < (y - 16) * 0.035:
                px[x, y] = (150, 150, 138, 255)
    for x in range(0, 24):
        px[x, 0] = (190, 206, 202, 255)
    for y in range(0, 28):
        px[0, y] = (190, 206, 202, 255)
        px[23, y] = (120, 140, 136, 255)
    return img


def dial_face(r):
    """A small gauge face, 32 px across the whole texture (the dial uses all of it): ivory, ticks round a 240 degree
    arc, the low end red and the rest green."""
    img = Image.new("RGBA", (S, S), (236, 232, 218, 255))
    px = img.load()
    for k in range(13):
        a = math.radians(-120 + k * 20)
        for rr in (11, 12, 13) if k % 3 == 0 else (12, 13):
            x, y = 15.5 + rr * math.sin(a), 15.5 - rr * math.cos(a)
            px[int(round(x)), int(round(y))] = (190, 34, 28, 255) if k < 3 else (30, 110, 56, 255)
    for dx in (-1, 0, 1):
        px[16 + dx, 25] = (40, 40, 38, 255)
    return img


def door_plate():
    """The NO ENTRY plate on the steel door's upper leaf: 19 x 12 px, black on yellow, two lines."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rect(img, 0, 0, 18, 11, (216, 178, 34))
    for x in range(19):
        M.touch(img, x, 0, 0.1)
    word(img, "NO", 6, 2, (24, 24, 22))
    word(img, "ENTRY", 2, 7, (24, 24, 22))
    for y in range(12):
        M.touch(img, 0, y, 0.08)
        M.touch(img, 18, y, -0.12)
    for x in range(19):
        M.touch(img, x, 11, -0.18)
    return img


# ---------------- The steel door ----------------

def steel_door():
    """The locked steel door's leaf: dark painted steel, nothing but paint. The lever, bar, plate, hinges, bead and
    glass are geometry (`l1props.steel_door`); the 2 px frame round the edge is shaded paint under the raised frame."""
    for part in ("lower", "upper"):
        img = M.painted_metal(seed_of("metaldoor" + part), base=(36, 38, 40), grain=2, mottle=4, panel=False, chips=3,
                              under=(84, 86, 88))
        M.grime(img, 0.18, seed_of("l1doorgrime" + part), cover=0.5)
        if part == "lower":
            clean = img.copy()
            M.grime(img, 0.5, seed_of("l1doorrust"), color=(104, 60, 34), bias="bottom", cover=0.45)
            cp, px = clean.load(), img.load()
            for y in range(20):  # only on the lowest third, fading out
                t = max(0.0, (y - 12) / 8)
                for x in range(S):
                    px[x, y] = M.rgba(M.mix(cp[x, y][:3], px[x, y][:3], t))
        save(img, f"metaldoor-{part}")
    save(M.painted_metal(seed_of("l1doorframe"), base=(84, 86, 90), grain=2, mottle=3, panel=False, chips=2, under=(120, 120, 118)),
         "l1doorframe")
    save(wired_glass(), "l1wired")
    save(door_plate(), "l1doorplate")


# ---------------- The drum ----------------

def drum(top):
    """The drum's lid (top=1) or its wall (top=0): blue enamel gone to rust in scattered patches, heaviest at the
    foot and under the lid, dents and a faint scuff band; the lid pressed with a ring."""
    base = (44, 74, 112)
    img = M.painted_metal(seed_of("oildrum" + str(top)), base=base, grain=3, mottle=5, panel=False, chips=6, under=(96, 98, 100))
    if top:
        px = img.load()
        for (r, f) in ((12.5, -0.14), (11.5, 0.08), (7.0, -0.1), (6.0, 0.06)):
            seen = {(int(round(15.5 + r * math.cos(math.radians(k / 2)))), int(round(15.5 + r * math.sin(math.radians(k / 2)))))
                    for k in range(720)}
            for (x, y) in seen:
                M.touch(img, x, y, f)
        M.rust(img, 0.18, seed_of("oildrumlid"), color=(128, 68, 38), dark=(82, 46, 30))
    else:
        M.rust(img, 0.2, seed_of("oildrumside"), color=(130, 70, 38), dark=(84, 46, 30))
        clean = img.copy()
        M.grime(img, 0.5, seed_of("oildrumfoot"), color=(110, 66, 36), bias="bottom", cover=0.5)
        cp, px = clean.load(), img.load()
        for y in range(S):  # the foot dirtier than the shoulders
            t = max(0.0, (y - 14) / 18)
            for x in range(S):
                px[x, y] = M.rgba(M.mix(cp[x, y][:3], px[x, y][:3], t))
        M.drips(img, 5, seed_of("oildrumruns"), color=(112, 62, 36), length=(6, 14), strength=0.5, start=0)
        # a lit left edge and shaded right edge on every facet window (each is 5.5 units wide, 11 px)
        for x0 in (0, 11, 22):
            for y in range(S):
                M.touch(img, x0, y, 0.12)
                M.touch(img, x0 + 10, y, -0.14)
    return img


def drum_extras():
    rim = M.painted_metal(seed_of("oildrumrim"), base=(52, 82, 120), grain=3, mottle=4, panel=False, chips=6, under=(110, 110, 108))
    M.rust(rim, 0.22, seed_of("oildrumrimrust"), color=(130, 70, 38), dark=(84, 46, 30))
    T.save(rim, "block/level2/oildrum-rim.png")
    # The label: 5 x 6 units (10 x 12 px), pale paper with an orange band and rows of small print
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rect(img, 0, 0, 9, 11, (226, 218, 192))
    rect(img, 0, 0, 9, 2, (200, 90, 30))
    for y in (4, 6, 8):
        for x in range(1, 9):
            if (x + y) % 3:
                img.putpixel((x, y), rgb((60, 54, 46)))
    for x in range(1, 9):
        img.putpixel((x, 10), rgb((60, 54, 46)))
    plate_edge(img, 10, 12, 0.08, -0.18)
    T.save(img, "block/level2/oildrum-label.png")
    bung = M.brushed_metal(seed_of("oildrumbung"), base=(150, 152, 150), grain=3)
    M.rust(bung, 0.2, seed_of("oildrumbungrust"), color=(130, 70, 38), dark=(84, 46, 30))
    T.save(bung, "block/level2/oildrum-bung.png")


# ---------------- The camera ----------------

def camera():
    body = M.painted_metal(seed_of("l1cambody"), base=(216, 214, 204), grain=2, mottle=3, panel=False, chips=3, under=(160, 158, 150))
    M.grime(body, 0.35, seed_of("l1camgrime"), color=(104, 98, 84), cover=0.55)
    M.drips(body, 3, seed_of("l1camdrips"), color=(120, 112, 96), length=(4, 10), strength=0.3, start=0)
    save(body, "l1cambody")
    save(enamel("l1camdark", (28, 30, 32), chips=2, under=(80, 82, 84), grime=0.1), "l1camdark")
    # The lens: black glass, a lit ring and a pale reflection, 4 x 4 units of it
    lens = M.noise_hv((8, 10, 12), 1, seed_of("l1camlens"), S, 2, (16, 8))
    px = lens.load()
    for (x, y) in ((2, 2), (3, 2), (2, 3), (5, 5), (6, 5)):
        px[x, y] = rgb((90, 104, 116))
    save(lens, "l1camlens")


# ---------------- The standpipe ----------------

def red_riser():
    """A red enamel riser skin, as the wall pipes' (U once round the pipe, V along it, turned for the risers)."""
    import gen_textures as G
    W = 64
    paint, rust, dark = (168, 34, 28), (132, 44, 30), (84, 24, 22)
    mott = G.smooth_noise(W, W, 16, 731)
    fine = G.smooth_noise(W, W, 4, 733)
    blooms = G.smooth_noise(W, W, 8, 735)
    rng = random.Random(737)
    img = Image.new("RGBA", (W, W))
    px = img.load()
    for y in range(W):
        light, spec = G.pipe_light((y + 0.5) / W)
        for x in range(W):
            m = mott[y][x] * 0.7 + fine[y][x] * 0.3
            c = [paint[i] + (rust[i] - paint[i]) * max(0.0, min(1.0, (m - 0.55) * 2.2)) for i in range(3)]
            if blooms[y][x] > 0.75:
                t = min(1.0, (blooms[y][x] - 0.75) * 4) * (0.45 + 0.55 * fine[y][x])
                c = [c[i] + (dark[i] - c[i]) * t * 0.7 for i in range(3)]
            c = [G.clamp(c[i] * light + 255 * spec * 0.25) for i in range(3)]
            px[x, y] = tuple(c) + (255,)
    for _ in range(8):
        x, y = rng.randrange(W), rng.randrange(W // 2, W - 6)
        for k in range(rng.randint(4, 10)):
            if y + k < W:
                px[x, y + k] = G.shade(px[x, y + k], 0.8)
    return img.transpose(Image.Transpose.TRANSPOSE)


def generate():
    materials()
    steel_door()
    camera()
    save(warning_decal(), "l1decal")
    save(caution_sign(), "l1signface")
    save(extinguisher_sign(), "l1extsign")
    save(label_plate("PULL", 16, 7, (236, 232, 222), (190, 34, 28)), "l1pull")
    save(label_plate("FIRE", 16, 7, (176, 38, 30), (244, 240, 228)), "l1firelabel")
    save(label_plate("HOSE", 20, 6, (176, 38, 30), (244, 240, 228), edge=False), "l1hoselabel")
    save(cabinet_glass(), "l1cabglass")
    save(dial_face(2), "l1dial")
    save(red_riser(), "l1riserred")
    drum_extras()
    T.save(drum(1), "block/level2/oildrum-top.png")
    T.save(drum(0), "block/level2/oildrum-side.png")
