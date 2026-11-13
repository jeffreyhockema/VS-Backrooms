"""Level 36, "Airport" (experimental): the textures of its surfaces (floors, walls, windows, cabin, ceilings, lights,
the belt and the static). The signs, screens, fascias and clocks are in gen_36_surfaces_signs.py; the block types in
gen_36_surfaces.py, which calls both. Every file is block/36/l36-*.png.

Palette: cool whites (marble, plaster, the column cladding), warm light greys (the composite panels), brushed steel
(ceiling baffles, kick plates, the carousel), navy/teal/red/grey carpet, BTA purple, painted grey block, and an
overcast runway view behind the glass. Light comes from above and the top-left, as everywhere in the mod.
"""
import math
import os
import random
import zlib

import numpy as np
from PIL import Image, ImageDraw

import matlib as M
import texlib

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures", "block", "36")
S = 32
WRITTEN = []


def seed_of(name):
    return zlib.crc32(("l36s/" + name).encode()) & 0xFFFFFF


def save(img, name):
    """Writes block/36/<name>.png (name starts l36-) and checks the atlas grid."""
    assert name.startswith("l36-"), name
    if img.width % 8 or img.height % 8:
        raise ValueError(f"{name} is {img.width}x{img.height}: block textures must be multiples of 8")
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))
    WRITTEN.append(name)
    return img


def clamp(v):
    return max(0, min(255, int(round(v))))


def from_array(a):
    a = np.clip(np.rint(a), 0, 255).astype(np.uint8)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.full(a.shape[:2] + (1,), 255, np.uint8)], axis=2)
    return Image.fromarray(a, "RGBA").copy()


def to_array(img):
    return np.asarray(img.convert("RGBA")).astype(np.float64)


def supersample(size, k=4):
    """An RGBA canvas k times the size, to draw on with ImageDraw and shrink with shrink() (soft edges)."""
    return Image.new("RGBA", (size[0] * k, size[1] * k), (0, 0, 0, 0))


def shrink(img, size):
    return img.resize(size, Image.LANCZOS)


# ======================================================================== Floors

MARBLE = {
    # base, vein, second faint vein
    "white": ((236, 236, 233), (200, 202, 206), (224, 224, 224)),
    "grey": ((170, 172, 176), (128, 130, 136), (160, 162, 166)),
    "dark": ((50, 52, 57), (112, 114, 120), (62, 64, 70)),
}


def marble(kind):
    base, vein, vein2 = MARBLE[kind]
    s = seed_of("marble-" + kind)
    img = texlib.marble(base, vein, s, veins=1, sharpness=7.0, mottle=0.035, turbulence=3.2)
    faint = texlib.marble(base, vein2, s + 17, veins=2, sharpness=9.0, mottle=0.02, turbulence=2.4)
    a, b = to_array(img), to_array(faint)
    a = np.minimum(a, b) * 0.35 + a * 0.65  # the faint veins only darken
    # soften the veins a touch (a wrapped 3x3 blur, half strength), so they read as stone, not drawn lines
    blur = sum(np.roll(np.roll(a, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)) / 9
    a = a * 0.6 + blur * 0.4
    # The polish: a soft broad sheen band across the tile (diagonal), wrapping, so the floor shimmers but tiles
    y, x = np.mgrid[0:S, 0:S]
    band = np.exp(-((((x - y) % S) - 16) / 7.0) ** 2) * (10 if kind != "dark" else 8)
    a[..., :3] += band[..., None]
    img = from_array(a)
    # One tile per block: a thin grout line at the block edge (right and bottom; the neighbour's lit edge meets it)
    grout = {"white": (206, 206, 202), "grey": (148, 150, 154), "dark": (34, 35, 38)}[kind]
    p = img.load()
    for i in range(S):
        p[S - 1, i] = M.rgba(M.mix(p[S - 1, i], grout, 0.75))
        p[i, S - 1] = M.rgba(M.mix(p[i, S - 1], grout, 0.75))
    M.bevel(img, (0, 0, S - 1, S - 1), 1, 0.07 if kind != "dark" else 0.12)
    return save(img, "l36-marble-" + kind)


def _motif(draw_fn, size=S):
    pat = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw_fn(pat.load())
    return pat


def carpet(kind):
    s = seed_of("carpet-" + kind)
    if kind == "blue":
        TEAL, ORANGE = (40, 150, 156), (226, 128, 52)

        def motif(p):
            for cx, cy in ((8, 8), (24, 24)):  # small teal diamonds on a 16 px lattice (offset rows: a diaper)
                for dy in range(-3, 4):
                    for dx in range(-3, 4):
                        if abs(dx) + abs(dy) == 3 or (abs(dx) + abs(dy) <= 1):
                            p[(cx + dx) % S, (cy + dy) % S] = TEAL + (255,)
            for cx, cy in ((24, 8), (8, 24)):  # and teal crosses between them
                for d in (-2, -1, 1, 2):
                    p[(cx + d) % S, cy] = TEAL + (200,)
                    p[cx, (cy + d) % S] = TEAL + (200,)
                p[cx, cy] = ORANGE + (255,)
            for cx, cy in ((0, 0), (16, 16)):  # orange specks at the lattice corners
                p[cx, cy] = ORANGE + (255,)
                p[(cx + 1) % S, cy] = ORANGE + (255,)
        img = M.carpet(s, base=(34, 42, 86), tone2=(28, 34, 72), mix2=0.35, nap="se", pile=8, grain=3, mottle=5,
                       pattern=_motif(motif))
    elif kind == "teal":
        DARK, AQUA, NAVY = (18, 64, 70), (96, 196, 190), (26, 34, 70)

        def motif(p):
            for i in range(S):  # a lattice of thin dark diagonals (lozenges two to a block)
                p[i, i] = DARK + (230,)
                p[i, (S - 1 - i)] = DARK + (230,)
            for cx, cy in ((16, 0), (0, 16)):  # small aqua squares where the lozenges' sides meet
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        if max(abs(dx), abs(dy)) == 2:
                            p[(cx + dx) % S, (cy + dy) % S] = AQUA + (255,)
                p[cx, cy] = NAVY + (255,)
            for cx, cy in ((16, 16),):
                p[cx, cy] = AQUA + (255,)
        img = M.carpet(s, base=(30, 104, 112), tone2=(26, 88, 96), mix2=0.35, nap="se", pile=8, grain=3, mottle=5,
                       pattern=_motif(motif))
    elif kind == "red":
        GOLD = (196, 160, 74)
        rng = random.Random(s)

        def motif(p):
            for _ in range(13):  # the gold fleck
                x, y = rng.randrange(S), rng.randrange(S)
                p[x, y] = GOLD + (255,)
                if rng.random() < 0.3:
                    p[(x + 1) % S, y] = GOLD + (170,)
        img = M.carpet(s, base=(122, 22, 34), tone2=(98, 16, 28), mix2=0.4, nap="se", pile=9, grain=3, mottle=6,
                       pattern=_motif(motif))
    else:  # grey: back-office loop pile, a faint tweed
        img = M.carpet(s, base=(112, 114, 120), tone2=(88, 90, 96), mix2=0.45, loop=True, pile=6, grain=3, mottle=5)
    return save(img, "l36-carpet-" + kind)


def belt():
    """A carousel tread seen from above, travel toward the top (-z): four overlapping slat plates across it (each a
    dark rubber-faced steel plate whose leading edge is a lit steel lip and whose trailing edge tucks in shadow under
    the next), between brushed steel edge strips."""
    s = seed_of("belt")
    rub = M.rubber(s, base=(40, 40, 42), grain=3, mottle=3)
    a = to_array(rub)
    rng = random.Random(s)
    for k in range(4):
        y0 = k * 8
        tone = rng.uniform(-3, 3)
        for yy in range(8):
            y = y0 + yy
            if yy == 0:      # the lip of the plate: steel, catching the light
                d = 48
            elif yy == 1:
                d = 18
            elif yy == 7:    # tucked under the next plate: shadow
                d = -18
            elif yy == 6:
                d = -8
            else:
                d = tone + (3 if yy in (2, 3) else 0)
            a[y, :, :3] += d
    # fine ribs along the plates (anti-slip), every 3 px across
    for x in range(2, 30, 3):
        for y in range(S):
            if y % 8 not in (0, 1, 7):
                a[y, x, :3] += 7
    # bolt heads near each plate's ends
    for k in range(4):
        for x in (4, 27):
            y = k * 8 + 3
            a[y, x, :3] += 34
            a[y + 1, x + 1, :3] -= 12
    img = from_array(a)
    steel = M.brushed_metal(seed_of("beltedge"), base=(156, 160, 164), direction="v", streak=7, sheen=6)
    sp = steel.load()
    p = img.load()
    for y in range(S):
        for x in (0, 1, 30, 31):
            p[x, y] = sp[x, y]
        p[2, y] = M.rgba(M.lift(p[2, y], -14))   # the gap between the plates and the edge strips
        p[29, y] = M.rgba(M.lift(p[29, y], -14))
    for y in range(S):
        p[0, y] = M.rgba(M.lift(p[0, y], 16))
        p[31, y] = M.rgba(M.lift(p[31, y], -16))
    save(img, "l36-belt-tread")
    side = M.painted_metal(seed_of("beltside"), base=(56, 58, 62), panel=False, chips=0)
    M.emboss_lines(side, ys=(2,), raised=True, strength=0.25)
    save(side, "l36-belt-side")


def carousel():
    s = seed_of("carousel")
    top = M.brushed_metal(s, base=(186, 190, 194), direction="h", streak=8, sheen=12)
    # The top slopes down toward its edges: a soft light ridge along the middle, darker toward the rims
    a = to_array(top)
    y = np.arange(S)
    a[..., :3] += (10 * np.cos((y - 15.5) / 16 * math.pi / 2) ** 2 - 5)[:, None, None]
    top = from_array(a)
    M.bevel(top, (0, 0, S, S), 1, 0.12)
    save(top, "l36-carousel-top")
    side = M.brushed_metal(s + 1, base=(172, 176, 180), direction="h", streak=7, sheen=8)
    p = side.load()
    rub = M.rubber(s + 2, base=(30, 30, 32)).load()
    for yy in range(S):
        for x in range(S):
            if yy < 3:  # the black rubber bumper round the top
                p[x, yy] = rub[x, yy]
            elif yy == 3:
                p[x, yy] = M.rgba(M.lift(p[x, yy], -30))
    M.ao_border(side, 3, 0.25, (0, 0, S, 20), "b")
    for x in range(0, S, 16):  # the panel joints
        for yy in range(4, 20):
            p[x, yy] = M.rgba(M.lift(p[x, yy], -22))
    save(side, "l36-carousel-side")
    # The flap opening: its stainless frame, the curtain of rubber strips and the dark inside
    frame = M.brushed_metal(s + 3, base=(176, 180, 184), direction="v", streak=8, sheen=8)
    M.bevel(frame, (0, 0, S, S), 1, 0.16)
    save(frame, "l36-carousel-frame")
    cur = M.rubber(s + 4, base=(32, 32, 34), grain=3, mottle=3)
    a = to_array(cur)
    for x in range(S):
        k = x % 4
        if k == 0:
            a[:, x, :3] += 26     # each strip's lit edge
        elif k == 3:
            a[:, x, :3] = a[:, x, :3] * 0.35   # the slit between strips: the dark behind
        elif k == 2:
            a[:, x, :3] -= 6
    # scuffed bottoms where bags push through
    rng = random.Random(s + 5)
    for x in range(S):
        if x % 4 != 3:
            for yy in range(S - rng.randint(2, 6), S):
                a[yy, x, :3] += 10
    save(from_array(a), "l36-carousel-curtain")
    dark = M.noise_hv((16, 16, 18), 2, s + 6, mottle=3)
    save(dark, "l36-carousel-dark")


def static(kind):
    """TV static: grey/white/black noise smeared a little along the scanlines, faint RGB fringes, a torn line or two.
    64 px (finer grain than the world), tileable (rows wrap round)."""
    s = seed_of("static-" + kind)
    rng = np.random.default_rng(s)
    W = 64
    v = rng.normal(140, 62, (W, W))
    v = 0.6 * v + 0.2 * np.roll(v, 1, 1) + 0.2 * np.roll(v, -1, 1)
    # bands of brighter and darker rows (the signal rolling)
    rows = rng.normal(0, 14, W)
    rows = 0.5 * rows + 0.25 * np.roll(rows, 1) + 0.25 * np.roll(rows, -1)
    v += rows[:, None]
    v = np.clip(v, 0, 255)
    a = np.stack([v, v, v], 2)
    # faint RGB fringes: red and blue shifted a pixel either way on some rows
    for y in range(W):
        if rng.random() < 0.22:
            a[y, :, 0] = a[y, :, 0] * 0.6 + np.roll(v[y], 1) * 0.42
            a[y, :, 2] = a[y, :, 2] * 0.6 + np.roll(v[y], -1) * 0.44
    # one or two torn scanlines: a row slid sideways and lit, with a dark line under it
    for _ in range(int(rng.integers(1, 3))):
        y = int(rng.integers(0, W))
        shift = int(rng.integers(5, 20))
        h = int(rng.integers(1, 3))
        for k in range(h):
            yy = (y + k) % W
            a[yy] = np.roll(a[yy], shift, 0) * 0.5 + 125
        a[(y + h) % W] *= 0.45
    # sparse pure-white and pure-black specks
    m = rng.random((W, W))
    a[m < 0.02] = 250
    a[m > 0.985] = 8
    return save(from_array(a), "l36-static-" + kind)


# ======================================================================== Walls

PANEL = (208, 204, 196)


def panel_img(seed=None, size=S):
    """The terminal's main wall: warm light-grey composite cladding, one large panel a block, recessed joints."""
    img = M.painted_metal(seed if seed is not None else seed_of("panel"), size=size, base=PANEL, grain=2, mottle=4,
                          panel=True, chips=0)
    a = to_array(img)
    y, x = np.mgrid[0:size, 0:size]
    a[..., :3] += (4 * np.cos((x + y) / size * math.pi))[..., None]  # a faint satin sheen
    return from_array(a)


def walls():
    s = seed_of("walls")
    pl = M.plaster(s, base=(234, 233, 229), grain=2, mottle=5, roller=0.4, bumps=0)
    p = pl.load()
    for y in range(S):  # a faint vertical joint (taped and painted): a pale line with a soft shadow beside it
        p[0, y] = M.rgba(M.lift(p[0, y], -7))
        p[1, y] = M.rgba(M.lift(p[1, y], 3))
    save(pl, "l36-wall-plaster")

    panel = panel_img()
    save(panel, "l36-wall-panel")

    kick = panel_img()
    steel = M.brushed_metal(s + 1, base=(170, 174, 178), direction="h", streak=9, sheen=8)
    kp, sp = kick.load(), steel.load()
    for y in range(22, S):
        for x in range(S):
            kp[x, y] = sp[x, y]
    M.bevel(kick, (0, 22, S, S), 1, 0.22)
    for x in range(S):  # the plate's top edge throws a hairline shadow on the panel
        kp[x, 21] = M.rgba(M.lift(kp[x, 21], -16))
    for x in (3, 28):
        M.screw(kick, x, 25)
    save(kick, "l36-wall-kick")

    tl = M.tile(s + 2, base=(238, 239, 238), grout=(172, 174, 176), pitch=8, jitter=3, uneven=3, glaze=True)
    save(tl, "l36-wall-tile")

    svc = M.brick(s + 3, base=(150, 152, 154), mortar=(140, 142, 144), course=8, length=16, offset=0.5, jitter=4,
                  hue=1, recess=0.8, pits=0.06, chamfer=True, grain=4, mottle=4)
    save(svc, "l36-wall-service")

    pur = M.painted_metal(s + 4, base=(88, 46, 134), grain=2, mottle=4, panel=True, chips=0)
    a = to_array(pur)
    y, x = np.mgrid[0:S, 0:S]
    a[..., :3] += (8 * np.exp(-(((x - y) % S - 10) / 5.0) ** 2))[..., None]  # the gloss
    pur = from_array(a)
    pp = pur.load()
    for x in range(S):  # a thin lilac pinstripe across the panel
        pp[x, 24] = M.rgba((170, 132, 214))
    save(pur, "l36-wall-purple")

    col = M.plaster(s + 5, base=(238, 238, 236), grain=2, mottle=3, roller=0.2, bumps=0)
    a = to_array(col)
    xs = np.arange(S)
    # Round cladding seen square: lit left of centre, falling off to both edges, a soft highlight line
    curve = 18 * np.cos((xs - 12) / 22 * math.pi / 2) - 14 + 10 * np.exp(-((xs - 10) / 1.6) ** 2)
    a[..., :3] += curve[None, :, None]
    col = from_array(a)
    cp = col.load()
    for x in range(S):  # the cladding's horizontal joint
        cp[x, 0] = M.rgba(M.lift(cp[x, 0], -18))
        cp[x, 1] = M.rgba(M.lift(cp[x, 1], 6))
    save(col, "l36-wall-column")

    st = M.brushed_metal(s + 6, base=(184, 188, 192), direction="v", streak=9, sheen=12)
    M.emboss_lines(st, xs=(31,), strength=0.18)
    save(st, "l36-wall-stainless")


# ======================================================================== The runway view

FOG = np.array((182, 188, 192), float)
SKY = np.array((150, 156, 163), float)


def _hz(x, freqs, seed, W=64):
    """A periodic 1D wave over W px (whole-number cycles), for hill lines that tile left-right."""
    rng = random.Random(seed)
    out = np.zeros_like(x, dtype=float)
    for f, amp in freqs:
        out += amp * np.sin(2 * math.pi * f * x / W + rng.uniform(0, 2 * math.pi))
    return out


def view():
    """The painted runway view, 64 px a block, four rows tall (sky, horizon, mid, low from the top), so the rows meet
    exactly. Each row tiles left-right (every feature repeats over 64 px); the sky row also tiles up and down."""
    W, H = 64, 256
    rng = np.random.default_rng(seed_of("view"))
    a = np.zeros((H, W, 3))
    xs = np.arange(W)
    # Sky (rows 0..63): flat overcast, a soft tileable cloud mottle
    cloud = np.array(M.fbm((W, 64), seed_of("cloud"), (32, 16, 8), 0.6))
    a[0:64] = SKY + cloud[..., None] * np.array((7, 7, 6))
    # Horizon row (64..127)
    hor = 96
    for y in range(64, hor):  # the sky brightening down to the horizon, into the fog
        t = ((y - 64) / (hor - 64)) ** 1.6
        a[y] = SKY * (1 - t) + FOG * t + cloud[y - 64][:, None] * (1 - t) * np.array((7, 7, 6))
    hill1 = hor - 9 - _hz(xs, ((1, 3.2), (2, 1.4), (3, 0.6)), 1)
    hill2 = hor - 4 - _hz(xs, ((1, 1.8), (2, 1.0), (4, 0.4)), 2)
    for y in range(70, hor + 6):
        for x in range(W):
            if y >= hill1[x]:   # the far hills: green-grey, nearly lost in the fog, darker toward their crests' feet
                k = min(1.0, (y - hill1[x]) / 10)
                a[y, x] = FOG * (0.80 - 0.06 * k) + np.array((104, 122, 104)) * (0.20 + 0.06 * k)
            if y >= hill2[x]:   # nearer, greener
                k = min(1.0, (y - hill2[x]) / 6)
                a[y, x] = FOG * (0.60 - 0.08 * k) + np.array((92, 116, 90)) * (0.40 + 0.08 * k)
    grass = np.array((104, 122, 96), float)
    for y in range(hor, 192):
        d = (y - hor) / (192 - hor)  # 0 far .. 1 near
        fog = 0.55 * (1 - d) ** 1.4
        g = grass * (0.92 + 0.12 * d)
        a[y] = g * (1 - fog) + FOG * fog
    # grass texture: horizontal streaks, finer far off
    gn = rng.normal(0, 1, (H, W))
    gn = 0.5 * gn + 0.25 * np.roll(gn, 1, 1) + 0.25 * np.roll(gn, -1, 1)
    for y in range(hor, 192):
        a[y] += gn[y][:, None] * (2 + 4 * (y - hor) / 96)
    # The runway: a dark band with white centre lights and pale edge lines
    r0, r1 = 104, 110
    for y in range(r0, r1 + 1):
        a[y] = np.array((92, 94, 96)) * 0.55 + FOG * 0.45
    a[r0] = a[r0] * 0.7 + np.array((220, 222, 220)) * 0.3
    a[r1] = a[r1] * 0.7 + np.array((220, 222, 220)) * 0.3
    for x in range(0, W, 8):  # centre lights
        a[107, x] = (250, 250, 244)
        a[107, (x + 1) % W] = a[107, (x + 1) % W] * 0.5 + 120
    # Mid row (128..191): grass verge, then a taxiway with blue edge lights, then the near apron's start
    t0, t1 = 150, 166
    for y in range(t0, t1 + 1):
        d = (y - hor) / 96
        fog = 0.4 * (1 - d) ** 1.4
        a[y] = np.array((82, 84, 86)) * (1 - fog) + FOG * fog + gn[y][:, None] * 2
    for y in (t0, t1):
        a[y] = a[y] * 0.75 + np.array((150, 140, 80)) * 0.25  # faint yellow edge stripes
    for y in range(t1 + 1, 172):  # a grass strip between taxiway and apron
        a[y] = grass * 0.85 + FOG * 0.15 + gn[y][:, None] * 3
    for x in range(4, W, 16):  # blue edge lights on both edges, with a soft halo
        for (yy, r) in ((t0 - 2, 1), (t1 + 2, 1)):
            for dy in range(-r - 1, r + 2):
                for dx in range(-r - 1, r + 2):
                    dd = math.hypot(dx, dy)
                    if dd < r + 1.5:
                        k = max(0.0, 1 - dd / (r + 1.5)) * 0.6
                        a[yy + dy, (x + dx) % W] = a[yy + dy, (x + dx) % W] * (1 - k) + np.array((80, 140, 255)) * k
            a[yy, x] = (150, 196, 255)
            a[yy, (x + 1) % W] = (120, 170, 255)
    # The apron, concrete, from 172 down to the sill; joints in perspective (wider apart nearer)
    conc = to_array(M.concrete(seed_of("apron"), size=(64, 64), base=(150, 150, 146), grain=3, mottle=5,
                               aggregate=0.03))[..., :3]
    for y in range(172, H):
        d = (y - 172) / (H - 172)
        fog = 0.3 * (1 - d) ** 1.5
        a[y] = conc[y % 64] * (1 - fog) + FOG * fog
    for jy in (180, 196, 220, 252):
        if jy < H:
            a[jy] *= 0.86
            if jy + 1 < H:
                a[jy + 1] = a[jy + 1] * 0.95 + 8
    for y in range(172, H):  # vertical joints, two to a block
        for jx in (20, 52):
            a[y, jx] *= 0.88
    # The faded yellow taxi line in the low row
    for y in (212, 213, 214):
        wear = rng.random(W)
        k = np.where(wear < 0.18, 0.15, 0.55)
        a[y] = a[y] * (1 - k[:, None]) + np.array((214, 176, 60)) * k[:, None]
    # A scatter of rubber marks on the apron
    for _ in range(6):
        x, y = int(rng.integers(0, W)), int(rng.integers(200, 244))
        for dx in range(int(rng.integers(3, 8))):
            a[y, (x + dx) % W] *= 0.88
    # The window frame at the bottom of the low row: a dark aluminium sill line and the lit sill under it
    a[246:250] = np.array((70, 74, 80))
    a[246] = np.array((96, 100, 106))
    a[250:256] = np.array((214, 214, 210))
    a[250] = np.array((236, 236, 232))
    a[255] = np.array((170, 170, 166))
    return a


def windows():
    a = view()
    W = 64
    rows = {"sky": (0, 64), "horizon": (64, 128), "mid": (128, 192), "low": (192, 256)}
    for name, (y0, y1) in rows.items():
        r = a[y0:y1].copy()
        # the glass: a faint cool tint and a soft diagonal reflection
        yy, xx = np.mgrid[0:64, 0:W]
        r = r * 0.94 + np.array((150, 166, 180)) * 0.06
        refl = np.exp(-((((xx + yy + y0) % 64) - 30) / 9.0) ** 2) * 7
        r += refl[..., None]
        # the mullion at the block's left edge: dark aluminium, a lit edge
        r[:, 0:3] = np.array((64, 68, 74))
        r[:, 0] = np.array((92, 96, 102))
        r[:, 3] = r[:, 3] * 0.7
        if name == "low":
            r[54:64, 0:3] = np.array((214, 214, 210))  # the sill runs across the mullion foot
            r[54, 0:3] = np.array((236, 236, 232))
        save(from_array(r), "l36-window-" + name)


# ======================================================================== The plane cabin

PLASTIC = (228, 226, 218)


def cabin():
    s = seed_of("cabin")
    base = M.plaster(s, base=PLASTIC, grain=2, mottle=3, roller=0.15, bumps=0)
    save(base, "l36-cabin-plastic")

    plain = base.copy()
    a = to_array(plain)
    y = np.arange(S)
    a[..., :3] += (6 - 12 * (y / S))[:, None, None]  # the side panel curves in toward the top
    plain = from_array(a)
    M.emboss_lines(plain, ys=(22,), strength=0.2)   # the dado seam
    pp = plain.load()
    for x in range(S):
        for yy in range(26, S):  # the lower trim, a little greyer
            pp[x, yy] = M.rgba(M.mix(pp[x, yy], (196, 196, 192), 0.4))
    save(plain, "l36-cabinwall-plain")

    # The porthole: drawn large and shrunk, so the oval is round
    K = 8
    big = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy, rx, ry = 16 * K, 14 * K, 8.5 * K, 11.5 * K
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=(206, 204, 198, 255))   # the moulded surround
    d.ellipse((cx - rx + 1.5 * K, cy - ry + 1.5 * K, cx + rx - 1.5 * K, cy + ry - 1.5 * K), fill=(150, 150, 150, 255))
    gx0, gy0, gx1, gy1 = cx - rx + 2.5 * K, cy - ry + 2.5 * K, cx + rx - 2.5 * K, cy + ry - 2.5 * K
    glass = Image.new("RGBA", big.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    for yy in range(int(gy0), int(gy1) + 1):  # blue sky, deeper at the top
        t = (yy - gy0) / (gy1 - gy0)
        c = tuple(int(v) for v in (np.array((62, 112, 200)) * (1 - t) + np.array((160, 200, 240)) * t))
        gd.line((gx0, yy, gx1, yy), fill=c + (255,))
    rr = random.Random(s)
    for k in range(9):  # bright cloud tops in the lower half
        bx = gx0 + rr.uniform(-0.2, 1.1) * (gx1 - gx0)
        by = cy + rr.uniform(0.15, 0.9) * (gy1 - cy)
        br = rr.uniform(2.2, 4.5) * K
        gd.ellipse((bx - br, by - br * 0.8, bx + br, by + br * 0.8), fill=(250, 250, 252, 255))
    gd.rectangle((gx0, cy + 0.75 * (gy1 - cy), gx1, gy1), fill=(244, 246, 250, 255))
    mask = Image.new("L", big.size, 0)
    ImageDraw.Draw(mask).ellipse((gx0, gy0, gx1, gy1), fill=255)
    big.paste(glass, (0, 0), mask)
    small = shrink(big, (S, S))
    win = plain.copy()
    win.alpha_composite(small)
    wp = win.load()
    for (x, yy) in ((12, 7), (12, 8), (13, 6), (13, 7)):  # the glint
        wp[x, yy] = M.rgba(M.lift(wp[x, yy], 40))
    M.inset(win, (9, 4, 24, 26), 1, 0.06)
    save(win, "l36-cabinwall-window")

    # The overhead bin door: a recessed rounded panel, a latch at the bottom, the bin's lip below
    binimg = base.copy()
    a = to_array(binimg)
    a[..., :3] += (8 * (1 - np.arange(S) / S))[:, None, None]
    binimg = from_array(a)
    big = Image.new("RGBA", (S * K, S * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rounded_rectangle((1.5 * K, 2 * K, 30.5 * K, 25 * K), radius=3 * K, fill=(236, 234, 228, 255),
                        outline=(176, 174, 168, 255), width=K)
    d.rounded_rectangle((13 * K, 21 * K, 19 * K, 24 * K), radius=K, fill=(92, 94, 98, 255))   # the latch
    d.rectangle((14 * K, 22 * K, 18 * K, 23 * K), fill=(150, 152, 156, 255))
    binimg.alpha_composite(shrink(big, (S, S)))
    bp = binimg.load()
    for x in range(S):
        for yy in range(27, S):  # the lip of the bin and the shadow under it
            bp[x, yy] = M.rgba(M.lift(bp[x, yy], -26 if yy == 27 else -8))
    save(binimg, "l36-cabinwall-bin")


# ======================================================================== Ceilings and lights

def ceilings():
    s = seed_of("ceil")
    # Linear metal baffles with shadow gaps: 6 px blades, 2 px gaps, running along x
    steel = M.brushed_metal(s, base=(176, 180, 184), direction="h", streak=8, sheen=8)
    p = steel.load()
    for y in range(S):
        k = y % 8
        for x in range(S):
            if k in (6, 7):
                p[x, y] = M.rgba((40, 42, 46) if k == 7 else (66, 68, 72))
            elif k == 0:
                p[x, y] = M.rgba(M.lift(p[x, y], 18))
            elif k == 5:
                p[x, y] = M.rgba(M.lift(p[x, y], -14))
    save(steel, "l36-ceiling-steel")

    tile = Image.new("RGBA", (S, S))
    for i in range(2):
        for j in range(2):
            t = M.ceiling_tile(s + 1 + i * 2 + j, size=16, base=(232, 232, 228), rail=(214, 214, 212), fissures=0.4)
            tile.paste(t, (i * 16, j * 16))
    save(tile, "l36-ceiling-tile")

    dark = M.noise_hv((22, 22, 25), 2, s + 5, mottle=3)
    a = to_array(dark)
    # A duct (a round shape, lit along its crown) and a cable tray (a ladder of rungs) running along x
    for y in range(4, 14):
        t = (y - 4) / 9
        a[y, :, :3] = np.array((44, 46, 50)) + 14 * math.sin(t * math.pi) ** 2
    for x in range(0, S, 8):
        a[4:14, x, :3] -= 10       # the duct's seams
    for y in (20, 26):
        a[y, :, :3] = np.array((52, 54, 58))
    for x in range(1, S, 4):
        a[21:26, x, :3] = np.array((46, 48, 52))
    for x in range(S):
        if (x * 7) % 5 < 2:
            a[23, x, :3] = np.array((30, 30, 36))  # cables
    save(from_array(a), "l36-ceiling-dark")

    cab = M.plaster(s + 6, base=(222, 220, 212), grain=2, mottle=3, roller=0.15, bumps=0)
    big = Image.new("RGBA", (S * 8, S * 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    K = 8
    d.rectangle((0, 11 * K, S * K, 21 * K), fill=(198, 198, 194, 255))   # the service strip
    for cx in (8, 24):   # a reading light and an air nozzle in each half
        d.ellipse(((cx - 4) * K, 12 * K, (cx - 1) * K, 15 * K), fill=(252, 242, 200, 255), outline=(150, 150, 146, 255), width=K // 2)
        d.ellipse(((cx + 1) * K, 12 * K, (cx + 4) * K, 15 * K), fill=(120, 122, 126, 255), outline=(170, 170, 168, 255), width=K // 2)
        d.ellipse(((cx + 2) * K, 13 * K, (cx + 3) * K, 14 * K), fill=(40, 40, 44, 255))
        d.rectangle(((cx - 3) * K, 17 * K, (cx + 3) * K, 19 * K), fill=(176, 176, 172, 255))  # the call/seat-belt sign slot
    cab.alpha_composite(shrink(big, (S, S)))
    M.emboss_lines(cab, ys=(10, 21), strength=0.14)
    # (cabin pass, 2026-11-13: l36-ceiling-cabin is now the aisle's lit diffuser, painted by tools/gen_36_cabin.py)


def lights():
    s = seed_of("light")
    steel = (176, 180, 184)
    for state, lit in (("on", 1.0), ("off", 0.0)):
        img = M.troffer_lens(s, lit=lit, lens=(214, 220, 228), frame=steel, frame_px=2, cell=2, tubes=2,
                             rail=(150, 154, 158), glow=(226, 234, 244))
        save(img, "l36-light-" + state)
    side = M.brushed_metal(s + 1, base=steel, direction="h", streak=7, sheen=6)
    M.bevel(side, (0, 0, S, S), 1, 0.14)
    save(side, "l36-light-side")


def generate():
    for k in MARBLE:
        marble(k)
    for k in ("blue", "teal", "red", "grey"):
        carpet(k)
    belt()
    carousel()
    for k in "abcd":
        static(k)
    walls()
    windows()
    cabin()
    ceilings()
    lights()
