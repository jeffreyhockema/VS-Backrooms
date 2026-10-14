"""Material kit for the graphics pass: structured, seamless surfaces and the operations that finish them.

Every level generator that paints a surface should start here instead of `gen_textures.noise_fill` (which stays as
it is for the textures nobody has redone yet). Nothing in this module writes a file: each function returns a Pillow
RGBA image (or changes the one it is given and returns it), and the caller saves it with its own `save`, which
checks the atlas grid.

    import matlib as M
    wall = M.concrete(seed=11, base=(132, 130, 124), joints=(16,))      # form-board concrete, joint every 16 px
    M.grime(wall, 0.12, seed=12, bias="bottom")                          # a dirty foot, for a bottom-row block only
    floor = M.alternates(lambda s, at: M.stain(M.concrete(seed=s), s, at=at), seed=40, n=3)
    tile = M.ceiling_tile(seed=3)                                        # ceiling module, see the end of the file

THE RULES EVERY PRIMITIVE FOLLOWS (and that a level batch keeps when it adds to them)

1. Structure first, then shading, then grain. A surface is built from elements (aggregate, planks, bricks, tiles,
   threads, tufts, panels); each element is shaded; a fine grain of 3 to 6 levels goes on last. Grain is never the
   structure. `noise_hv` is the base layer: a soft, tileable mottle plus that grain.

2. Shading convention: light comes from above (and a little from the left).
   - The top edge of an element is lit (1 px lighter), its bottom edge dark (1 px darker), and the joint below it
     darker still, because the element above overhangs it (`bevel`, `emboss_lines`, the per-element code in each
     surface). A recess is the reverse: dark along its top and left, lit along its bottom and right (`inset`).
   - Borders between elements are darkened (`ao_border`); highlights sit on bevels and edges.
   - Warm light, cool shadow: every lightening drifts the hue warm (more red, less blue) and every darkening drifts
     it cool, by `DRIFT` (0.18) per level unless a function is given its own `drift`. `lift(c, d)` is the one place
     this happens; use it (or `shade_px`) rather than adding to the three channels alike. That is rubric check 3:
     hue varies with value, so nothing reads as a pure grey.
   - The engine shades faces only by direction, so all of this is baked into the texture.

3. Tiling rule. Every surface tiles seamlessly: noise fields are periodic (`value_noise`, `fbm`, `worley` wrap),
   and anything drawn near an edge wraps to the opposite one. A feature a player would recognise a second time (a
   stain, a crack, a knot, a scuff, a swirl) must not sit at the same place in every block: either it is small and
   frequent enough to read as texture, or it goes at a seed-chosen offset in two or three `alternates` (the blocktype
   lists them under `alternates`), so no two neighbouring blocks repeat it. `stain`, `tideline` and the knots and
   cracks take `at=` / a seed for exactly that, and `alternates(fn, seed, n)` spreads the offsets.

4. Grid rule. Sizes are multiples of 8 px on both sides (`GRID`), 32 px to a block side as vanilla has; a surface
   asked for another size raises. Element pitches divide the size (bricks 16x8, tiles 8 or 4, planks of 10-11 px in
   three per 32) so they meet themselves across the edge. A picture that is not on the grid goes through
   `gen_textures.fit_atlas_grid` / `pad_to_atlas_grid` before it is saved, never through here.

5. Determinism. Every function takes a `seed` and uses only `random.Random(seed)` and the periodic fields built from
   it, so a generator run twice writes the same bytes.

Colour: vanilla's palette is desaturated and mid-warm. The defaults here are, too; give a lore colour (EXIT red,
3999 neon) explicitly. Boxes are (x0, y0, x1, y1) with the end exclusive, as in Pillow's crop.
"""
import math
import random
import zlib

from PIL import Image

S = 32      # a block side, in px
GRID = 8    # the atlas mipmap grid
DRIFT = 0.18  # warm/cool hue shift per level of lift (see lift)
DRIFT_CAP = 6.0  # the most the drift moves a channel, in levels, however strong the lift


# ---------------- Colour ----------------

def clamp(v):
    return 0 if v < 0 else 255 if v > 255 else int(v + 0.5)


def rgba(c, a=255):
    return (clamp(c[0]), clamp(c[1]), clamp(c[2]), a if len(c) < 4 else c[3])


def lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def lift(c, d, drift=DRIFT):
    """c lightened by d levels (darkened when d < 0). Light drifts warm (red up more, blue less), shadow cool; the
    drift is d * drift levels, capped at DRIFT_CAP so a deep shadow stays a shadow and does not turn blue."""
    t = max(-DRIFT_CAP, min(DRIFT_CAP, d * drift))
    return (c[0] + d + t, c[1] + d + t * 0.3, c[2] + d - t)


def shade_px(c, f, drift=DRIFT):
    """c lit (f > 0) or shaded (f < 0) by a fraction f of its own brightness, with the warm/cool drift.
    A dark colour still gets a visible change: the scale never drops below 64 levels."""
    return lift(c, f * (0.5 * lum(c) + 64), drift)


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def hue_shift(c, h):
    """A pure hue nudge of h levels toward warm (h > 0) or cool, keeping the brightness."""
    return (c[0] + h, c[1] + h * 0.15, c[2] - h * 1.1)


# ---------------- Sizes, seeds, pixels ----------------

def wh(size):
    w, h = (size, size) if isinstance(size, int) else size
    if w % GRID or h % GRID:
        raise ValueError(f"{w}x{h}: surfaces must be multiples of {GRID} px on both sides (the grid rule)")
    return w, h


def sub(seed, tag):
    """A seed for one layer of a surface, so layers stay independent and stable."""
    return (int(seed) * 1000003 + zlib.crc32(tag.encode())) & 0x7FFFFFFF


def new(size, colour=(0, 0, 0), alpha=255):
    w, h = wh(size)
    return Image.new("RGBA", (w, h), rgba(colour, alpha))


def put(px, w, h, x, y, c):
    """Writes c at (x, y), wrapped round the texture, keeping the alpha already there."""
    x, y = x % w, y % h
    px[x, y] = rgba(c, px[x, y][3])


def get(px, w, h, x, y):
    return px[x % w, y % h]


def touch(img, x, y, f, drift=DRIFT):
    """Shades one pixel (wrapped) by a fraction f, as shade_px."""
    px, (w, h) = img.load(), img.size
    put(px, w, h, x, y, shade_px(get(px, w, h, x, y), f, drift))


def roll(img, dx, dy):
    """The image shifted by (dx, dy), wrapping: a tileable texture stays tileable."""
    w, h = img.size
    out = Image.new(img.mode, img.size)
    dx, dy = dx % w, dy % h
    for (sx, sy, tx, ty, cw, ch) in ((0, 0, dx, dy, w - dx, h - dy), (w - dx, 0, 0, dy, dx, h - dy),
                                     (0, h - dy, dx, 0, w - dx, dy), (w - dx, h - dy, 0, 0, dx, dy)):
        if cw and ch:
            out.paste(img.crop((sx, sy, sx + cw, sy + ch)), (tx, ty))
    return out


# ---------------- Periodic fields ----------------

def _divisor(n, c):
    c = max(1, min(n, int(round(c))))
    while n % c:
        c -= 1
    return c


def _smooth(t):
    return t * t * (3 - 2 * t)


def value_noise(size, cell, seed):
    """A tileable smooth noise field in about -1..1: random values on a lattice of `cell` px (or (cx, cy) for a
    stretched field, e.g. (32, 1) for streaks along x), smoothly interpolated, wrapping at the edges."""
    w, h = (size, size) if isinstance(size, int) else size
    cx, cy = (cell, cell) if isinstance(cell, (int, float)) else cell
    cx, cy = _divisor(w, cx), _divisor(h, cy)
    gw, gh = w // cx, h // cy
    rng = random.Random(seed)
    g = [[rng.uniform(-1, 1) for _ in range(gw)] for _ in range(gh)]
    phx, phy = rng.random() * cx, rng.random() * cy
    out = []
    for y in range(h):
        fy = (y + phy) / cy
        j0 = int(fy)
        ty = _smooth(fy - j0)
        r0, r1 = g[j0 % gh], g[(j0 + 1) % gh]
        row = []
        for x in range(w):
            fx = (x + phx) / cx
            i0 = int(fx)
            tx = _smooth(fx - i0)
            a0, a1 = r0[i0 % gw], r0[(i0 + 1) % gw]
            b0, b1 = r1[i0 % gw], r1[(i0 + 1) % gw]
            a = a0 + (a1 - a0) * tx
            b = b0 + (b1 - b0) * tx
            row.append(a + (b - a) * ty)
        out.append(row)
    return out


def fbm(size, seed, cells=(16, 8, 4), gain=0.55):
    """Octaves of value_noise summed and scaled so the field spans -1..1. Tileable."""
    w, h = wh(size)
    acc = [[0.0] * w for _ in range(h)]
    amp = 1.0
    for i, c in enumerate(cells):
        f = value_noise((w, h), c, sub(seed, f"oct{i}"))
        for y in range(h):
            ry, fy = acc[y], f[y]
            for x in range(w):
                ry[x] += amp * fy[x]
        amp *= gain
    m = max(1e-6, max(abs(v) for row in acc for v in row))
    return [[v / m for v in row] for row in acc]


def points(size, n, seed, jitter=0.9):
    """About n points spread evenly (one per cell of a jittered grid), for aggregate, stones, spangle."""
    w, h = wh(size)
    rng = random.Random(seed)
    cols = max(1, round(math.sqrt(n * w / h)))
    rows = max(1, round(n / cols))
    cw, ch = w / cols, h / rows
    pts = []
    for j in range(rows):
        for i in range(cols):
            pts.append(((i + 0.5 + rng.uniform(-0.5, 0.5) * jitter) * cw % w,
                        (j + 0.5 + rng.uniform(-0.5, 0.5) * jitter) * ch % h))
    return pts


def worley(size, pts):
    """For each pixel: distance to the nearest point (f1), to the second (f2), and the nearest point's index,
    measured across the wrap so the cells tile."""
    w, h = wh(size)
    f1 = [[0.0] * w for _ in range(h)]
    f2 = [[0.0] * w for _ in range(h)]
    idx = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            best, second, bi = 1e9, 1e9, 0
            for i, (px_, py_) in enumerate(pts):
                dx = abs(x + 0.5 - px_)
                dy = abs(y + 0.5 - py_)
                dx, dy = min(dx, w - dx), min(dy, h - dy)
                d = dx * dx + dy * dy
                if d < best:
                    best, second, bi = d, best, i
                elif d < second:
                    second = d
            f1[y][x], f2[y][x], idx[y][x] = math.sqrt(best), math.sqrt(second), bi
    return f1, f2, idx


def wrapdist(ax, ay, bx, by, w, h):
    dx, dy = abs(ax - bx), abs(ay - by)
    return math.hypot(min(dx, w - dx), min(dy, h - dy))


# ---------------- The base layer ----------------

def noise_hv(base, amp=4, seed=0, size=S, mottle=6, cells=(16, 8), drift=DRIFT, hue=2.0):
    """The hue-aware replacement for noise_fill: base colour, a soft tileable mottle of +-`mottle` levels (the low
    frequencies vanilla's plain textures have), a slow hue wander of +-`hue` levels, and a per-pixel grain of
    +-`amp` levels (keep it 3..6). Lighter pixels drift warm and darker ones cool."""
    w, h = wh(size)
    rng = random.Random(sub(seed, "grain"))
    mot = fbm((w, h), sub(seed, "mottle"), cells) if mottle else None
    hf = fbm((w, h), sub(seed, "hue"), (16, 8)) if hue else None
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            d = (mot[y][x] * mottle if mot else 0) + rng.uniform(-amp, amp)
            c = lift(base, d, drift)
            if hf:
                c = hue_shift(c, hf[y][x] * hue)
            px[x, y] = rgba(c)
    return img


# ---------------- Operations ----------------

def _box(img, box):
    return box if box is not None else (0, 0, img.width, img.height)


def ao_border(img, px=2, strength=0.22, box=None, sides="tblr", drift=DRIFT):
    """Darkens toward the edges of `box` (the whole image by default) over `px` pixels, strongest at the edge:
    the ambient occlusion where an element meets its neighbour. `sides` picks the edges (t, b, l, r)."""
    x0, y0, x1, y1 = _box(img, box)
    p, (w, h) = img.load(), img.size
    for y in range(y0, y1):
        for x in range(x0, x1):
            d = min([v for k, v in (("t", y - y0), ("b", y1 - 1 - y), ("l", x - x0), ("r", x1 - 1 - x)) if k in sides] or [px])
            if d < px:
                f = -strength * (1 - d / px) ** 1.5
                put(p, w, h, x, y, shade_px(get(p, w, h, x, y), f, drift))
    return img


def bevel(img, box=None, width=1, strength=0.2, light_from_top=True, drift=DRIFT):
    """A raised edge round `box`: top and left lit, bottom and right shaded (the reverse with light_from_top=False,
    for a face seen from below). Corners go to the lit side at top-left and the dark side at bottom-right."""
    x0, y0, x1, y1 = _box(img, box)
    s = 1 if light_from_top else -1
    for k in range(width):
        f = strength * (1 - k / max(1, width)) if width > 1 else strength
        for x in range(x0 + k, x1 - k):
            touch(img, x, y0 + k, s * f, drift)
            touch(img, x, y1 - 1 - k, -s * f * 1.15, drift)
        for y in range(y0 + k + 1, y1 - k - 1):
            touch(img, x0 + k, y, s * f * 0.6, drift)
            touch(img, x1 - 1 - k, y, -s * f * 0.8, drift)
    return img


def inset(img, box, width=1, strength=0.22, drift=DRIFT):
    """A recess: the top and left walls in shadow, the bottom and right ones catching the light."""
    return bevel(img, box, width, strength, light_from_top=False, drift=drift)


def hue_jitter(img, amount=4, seed=0, cell=8, boxes=None):
    """Hue (not brightness) varies: over a tileable field of `cell` px, or one random nudge per box in `boxes`
    (per brick, per tile, per plank). amount in levels."""
    p, (w, h) = img.load(), img.size
    if boxes:
        rng = random.Random(sub(seed, "hj"))
        for (x0, y0, x1, y1) in boxes:
            v = rng.uniform(-amount, amount)
            for y in range(y0, y1):
                for x in range(x0, x1):
                    put(p, w, h, x, y, hue_shift(get(p, w, h, x, y), v))
        return img
    f = fbm((w, h), sub(seed, "hj"), (cell, max(2, cell // 2)))
    for y in range(h):
        for x in range(w):
            p[x, y] = rgba(hue_shift(p[x, y], f[y][x] * amount), p[x, y][3])
    return img


def grime(img, amount=0.15, seed=0, color=(74, 66, 54), cells=(8, 4, 2), bias=None, cover=0.5):
    """Dirt: a patchy tileable mottle pulling toward `color`. bias="bottom"/"top" makes it gather at one edge
    (for a bottom-row block or a skirting band; that breaks vertical tiling on purpose). cover 0..1 is how much of
    the surface the patches reach."""
    p, (w, h) = img.load(), img.size
    f = fbm((w, h), sub(seed, "grime"), cells)
    for y in range(h):
        g = 1.0
        if bias == "bottom":
            g = (y / (h - 1)) ** 2
        elif bias == "top":
            g = (1 - y / (h - 1)) ** 2
        for x in range(w):
            t = (f[y][x] + 1) / 2 - (1 - cover)
            if t > 0:
                c = p[x, y]
                p[x, y] = rgba(mix(c, color, min(1.0, t * 2) * amount * g * 2), c[3])
    return img


def _line(x0, y0, x1, y1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    return [(round(x0 + (x1 - x0) * i / max(1, n - 1)), round(y0 + (y1 - y0) * i / max(1, n - 1))) for i in range(n)]


def scratches(img, n=6, seed=0, length=(3, 8), light=0.22, angle=None, dark_side=True):
    """Thin scratches: bright lines (bare metal or a lighter layer under the finish) with a dark pixel along their
    lower side. angle in degrees (0 = along x), None for random. Wrapping."""
    rng = random.Random(sub(seed, "scr"))
    w, h = img.size
    for _ in range(n):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = math.radians(angle if angle is not None else rng.uniform(0, 180)) + rng.uniform(-0.2, 0.2)
        L = rng.uniform(*length)
        pts = _line(x, y, x + math.cos(a) * L, y + math.sin(a) * L)
        for i, (px_, py_) in enumerate(pts):
            t = math.sin(math.pi * (i + 0.5) / len(pts))  # fades in and out
            touch(img, px_, py_, light * (0.5 + 0.5 * t))
            if dark_side and rng.random() < 0.6:
                touch(img, px_, py_ + 1, -light * 0.5 * t)
    return img


def drips(img, n=3, seed=0, color=(70, 60, 46), length=(6, 20), strength=0.45, start=None, width=1):
    """Run marks down the surface from y=`start` (random if None), fading as they go, with a darker bead where
    each stops. Wrapping, so they tile."""
    rng = random.Random(sub(seed, "drip"))
    p, (w, h) = img.load(), img.size
    for _ in range(n):
        x = rng.randrange(w)
        y0 = start if start is not None else rng.randrange(h)
        L = int(rng.uniform(*length))
        for i in range(L):
            t = (1 - i / L) ** 0.7 * strength
            if rng.random() < 0.15:
                x += rng.choice((-1, 1))
            for k in range(width):
                c = get(p, w, h, x + k, y0 + i)
                put(p, w, h, x + k, y0 + i, mix(c, color, t))
        c = get(p, w, h, x, y0 + L)
        put(p, w, h, x, y0 + L, mix(c, lift(color, -10), strength * 0.8))
    return img


def rust(img, amount=0.3, seed=0, color=(138, 72, 38), dark=(84, 46, 30), edges=False, pits=True, cells=(8, 4, 2)):
    """Rust patches: a tileable mask past a threshold set by `amount` (0..1 of the surface), coloured between an
    orange-brown and a dark crust, with pits, and a faint orange halo where it bleeds into the paint. edges=True
    makes it gather along the image edges (the seams of a plate)."""
    p, (w, h) = img.load(), img.size
    f = fbm((w, h), sub(seed, "rust"), cells)
    tone = fbm((w, h), sub(seed, "rusttone"), (4, 2))
    rng = random.Random(sub(seed, "rustpit"))
    thr = 1 - 2 * amount
    for y in range(h):
        for x in range(w):
            v = f[y][x]
            if edges:
                e = min(x, w - 1 - x, y, h - 1 - y)
                v += 0.6 * max(0, 1 - e / 4)
            c = p[x, y]
            if v > thr:
                t = min(1.0, (v - thr) * 4)
                rc = mix(color, dark, (tone[y][x] + 1) / 2)
                rc = lift(rc, rng.uniform(-6, 6))
                out = mix(c, rc, 0.35 + 0.65 * t)
                if pits and t > 0.6 and rng.random() < 0.08:
                    out = lift(out, -28)
                p[x, y] = rgba(out, c[3])
            elif v > thr - 0.12:
                p[x, y] = rgba(mix(c, color, 0.12), c[3])
    return img


def chip_edges(img, box=None, seed=0, n=5, under=(72, 70, 68), size=(1, 3)):
    """Paint chipped off along the edges of `box`: small clusters of the `under` colour (bare metal, primer, wood)
    with a lit lower rim, where the paint edge catches the light."""
    x0, y0, x1, y1 = _box(img, box)
    rng = random.Random(sub(seed, "chip"))
    p, (w, h) = img.load(), img.size
    per = 2 * (x1 - x0) + 2 * (y1 - y0)
    for _ in range(n):
        t = rng.uniform(0, per)
        if t < x1 - x0:
            cx, cy = x0 + t, y0
        elif t < 2 * (x1 - x0):
            cx, cy = x0 + t - (x1 - x0), y1 - 1
        elif t < 2 * (x1 - x0) + (y1 - y0):
            cx, cy = x0, y0 + t - 2 * (x1 - x0)
        else:
            cx, cy = x1 - 1, y0 + t - 2 * (x1 - x0) - (y1 - y0)
        k = rng.randint(*size)
        cells = {(int(cx), int(cy))}
        for _ in range(k * 2):
            ax, ay = rng.choice(sorted(cells))
            nx, ny = ax + rng.choice((-1, 0, 1)), ay + rng.choice((-1, 0, 1))
            if x0 <= nx < x1 and y0 <= ny < y1:
                cells.add((nx, ny))
        for (ax, ay) in cells:
            put(p, w, h, ax, ay, lift(under, rng.uniform(-6, 6)))
        for (ax, ay) in cells:
            if (ax, ay + 1) not in cells and y0 <= ay + 1 < y1:
                touch(img, ax, ay + 1, 0.16)
    return img


def emboss_lines(img, xs=(), ys=(), raised=False, strength=0.2, box=None):
    """Seams and ribs drawn as relief. A groove (raised=False) is a dark line with a lit line below it (or to its
    right); a rib (raised=True) is a lit line with a dark one below. Coordinates wrap, so a line at 0 meets 31."""
    x0, y0, x1, y1 = _box(img, box)
    s = 1 if raised else -1
    for y in ys:
        for x in range(x0, x1):
            touch(img, x, y, s * strength)
            touch(img, x, y + 1, -s * strength * 0.55)
    for x in xs:
        for y in range(y0, y1):
            touch(img, x, y, s * strength * 0.8)
            touch(img, x + 1, y, -s * strength * 0.45)
    return img


def stain(img, seed=0, radius=9, color=(120, 98, 62), strength=0.35, at=None, ring=0.5):
    """One soft irregular blotch (a water or oil stain) centred at `at`, or at a seed-chosen offset, wrapping across
    the edges, with a darker tide ring round its rim. For alternates: give each its own `at` (see alternates)."""
    w, h = img.size
    rng = random.Random(sub(seed, "stain"))
    cx, cy = at if at is not None else (rng.uniform(0, w), rng.uniform(0, h))
    wob = fbm((w, h), sub(seed, "stainwob"), (8, 4))
    p = img.load()
    for y in range(h):
        for x in range(w):
            d = wrapdist(x + 0.5, y + 0.5, cx, cy, w, h) / radius + 0.28 * wob[y][x]
            if d < 1.0:
                t = strength * (1 - d) ** 0.6
                if d > 0.82:
                    t += ring * strength * (1 - abs(d - 0.91) / 0.09)
                c = p[x, y]
                p[x, y] = rgba(mix(c, color, min(1.0, t)), c[3])
    return img


def tideline(img, y, seed=0, color=(132, 108, 66), amount=0.3, wave=1.5, below=0.5, fade=None):
    """A water line across the surface at height y: a sharp darker rim along a wavy line, and the surface below it
    stained (`below` of `amount`), fading over `fade` px (None: to the bottom). Wraps horizontally."""
    w, h = img.size
    rng = random.Random(sub(seed, "tide"))
    k1, k2 = rng.choice((1, 2)), rng.choice((3, 4, 5))
    ph1, ph2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
    p = img.load()
    for x in range(w):
        yl = y + wave * math.sin(2 * math.pi * k1 * x / w + ph1) + 0.5 * wave * math.sin(2 * math.pi * k2 * x / w + ph2)
        for yy in range(h):
            dy = yy - yl
            t = 0.0
            if -0.5 <= dy < 1.5:
                t = amount * (1.0 if dy < 0.5 else 0.6)
            elif dy >= 1.5:
                f = 1.0 if fade is None else max(0.0, 1 - (dy - 1.5) / fade)
                t = amount * below * f
            if t > 0:
                c = p[x, yy]
                p[x, yy] = rgba(mix(c, color, t), c[3])
    return img


def multiply(img, overlay, strength=1.0):
    """Multiplies an overlay (same size, or tiled to it) into the image: white leaves it, darker colours tint it."""
    p, (w, h) = img.load(), img.size
    o, (ow, oh) = overlay.convert("RGBA").load(), overlay.size
    for y in range(h):
        for x in range(w):
            c, m = p[x, y], o[x % ow, y % oh]
            a = strength * m[3] / 255
            p[x, y] = rgba(tuple(c[i] * (1 - a + a * m[i] / 255) for i in range(3)), c[3])
    return img


def dye(img, pattern, base, strength=1.0):
    """Prints a coloured pattern (an RGBA image, transparent where there is none) into a structured surface,
    keeping its shading: each dyed pixel is the pattern colour times the surface's brightness relative to `base`.
    How a motif goes onto carpet pile or wallpaper fibre."""
    p, (w, h) = img.load(), img.size
    o, (ow, oh) = pattern.convert("RGBA").load(), pattern.size
    bl = max(1.0, lum(base))
    for y in range(h):
        for x in range(w):
            m = o[x % ow, y % oh]
            if m[3]:
                c = p[x, y]
                k = lum(c) / bl
                t = strength * m[3] / 255
                p[x, y] = rgba(mix(c, tuple(m[i] * k for i in range(3)), t), c[3])
    return img


def spread(seed, n, size=S):
    """n offsets spread over the texture (golden-ratio steps from a seed-chosen start), far from each other."""
    w, h = wh(size)
    rng = random.Random(sub(seed, "spread"))
    u, v = rng.random(), rng.random()
    return [(((u + k * 0.618034) % 1) * w, ((v + k * 0.381966 + (k % 2) * 0.5) % 1) * h) for k in range(n)]


def alternates(fn, seed, n=3, size=S):
    """n variants of a texture whose distinctive feature sits at a different offset in each: calls fn(seed_k, at_k)
    with a fresh seed and an offset from `spread`. The blocktype lists them under `alternates` (the tiling rule)
    beside two or three plain variants, so the feature lands in about one block in three and at a different place each
    time; a feature in every block reads as a polka-dot grid however it is placed."""
    return [fn(sub(seed, f"alt{k}"), at) for k, at in enumerate(spread(seed, n, size))]


# ---------------- Surfaces ----------------

def concrete(seed=0, size=S, base=(130, 128, 122), grain=4, mottle=7, aggregate=0.07, pores=0.012, cracks=0,
             border=0, joints=(), swirl=0, drift=DRIFT):
    """Concrete: a mottled cement ground with aggregate (1-2 px stones, each lit on top with a shadow under it, some
    warm, some cool), pin-hole pores, `cracks` hairline cracks (random walks with a lit lower edge: a crack repeats
    visibly block after block, so give them only to alternates), darker borders (`border` px of ao_border, for slabs),
    form-board `joints` (grooves at these y) and power-trowel `swirl` (0..1, faint arcs, for floors)."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8, 4), drift)
    rng = random.Random(sub(seed, "agg"))
    p = img.load()
    if swirl:
        for _ in range(int(3 + 3 * swirl)):
            cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(8, 18)
            a0 = rng.uniform(0, 6.3)
            for i in range(int(r * 2.2)):
                a = a0 + i / r
                touch(img, cx + math.cos(a) * r, cy + math.sin(a) * r, 0.035 * swirl)
    for _ in range(int(aggregate * w * h * 1.6)):  # fines: single low-contrast specks
        x, y = rng.randrange(w), rng.randrange(h)
        put(p, w, h, x, y, hue_shift(lift(get(p, w, h, x, y), rng.choice((-1, 1)) * rng.uniform(3, 7), drift), rng.uniform(-3, 3)))
    for _ in range(int(aggregate * w * h)):
        x, y = rng.randrange(w), rng.randrange(h)
        off = rng.choice((-1, 1, 1)) * rng.uniform(6, 15)
        hue = rng.uniform(-5, 5)
        r = rng.random()
        cells = [(x, y)] if r < 0.55 else [(x, y), (x + 1, y)] if r < 0.75 else [(x, y), (x, y + 1)] if r < 0.88 else \
            [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)][:rng.choice((3, 4))]
        for (cx, cy) in cells:
            c = hue_shift(lift(base, off + rng.uniform(-3, 3), drift), hue)
            put(p, w, h, cx, cy, c)
        top = min(c[1] for c in cells)
        for (cx, cy) in cells:
            if cy == top and off > 0:
                touch(img, cx, cy, 0.05)
        for (cx, cy) in cells:
            if (cx, cy + 1) not in cells:
                touch(img, cx, cy + 1, -0.07)
    for _ in range(int(pores * w * h)):
        x, y = rng.randrange(w), rng.randrange(h)
        touch(img, x, y, -0.22)
        touch(img, x, y - 1, -0.06)
        touch(img, x, y + 1, 0.05)
    for k in range(int(cracks)):
        crack(img, sub(seed, f"crack{k}"))
    for y in joints:
        emboss_lines(img, ys=(y,), strength=0.2)
        for x in range(w):
            if rng.random() < 0.15:
                touch(img, x, y + 2, rng.uniform(0.02, 0.06))  # cement bleed along the joint
    if border:
        ao_border(img, border, 0.22)
    return img


def crack(img, seed, at=None, length=(10, 22), strength=0.28):
    """One hairline crack: a wandering dark line with a lit pixel under it, thinning at both ends; wrapping."""
    w, h = img.size
    rng = random.Random(seed)
    x, y = at if at is not None else (rng.uniform(0, w), rng.uniform(0, h))
    a = rng.uniform(0, 2 * math.pi)
    L = int(rng.uniform(*length))
    for i in range(L):
        t = math.sin(math.pi * (i + 0.5) / L) ** 0.5
        touch(img, round(x), round(y), -strength * t)
        if t > 0.6:
            touch(img, round(x), round(y) + 1, strength * 0.25)
        a += rng.uniform(-0.5, 0.5)
        x += math.cos(a)
        y += math.sin(a)
    return img


def plaster(seed=0, size=S, base=(212, 206, 194), grain=3, mottle=8, roller=0.5, bumps=0.01, drift=DRIFT):
    """Painted plaster or drywall: broad soft mottling (vanilla plaster's clouds), a fine roller stipple of `roller`
    (0..1), and the odd tiny lump, lit on top and shadowed under."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8, 4), drift)
    if roller:
        st = fbm((w, h), sub(seed, "roll"), (2, 1), 0.7)
        p = img.load()
        for y in range(h):
            for x in range(w):
                p[x, y] = rgba(lift(p[x, y], st[y][x] * 3.5 * roller, drift))
    rng = random.Random(sub(seed, "bump"))
    for _ in range(int(bumps * w * h)):
        x, y = rng.randrange(w), rng.randrange(h)
        touch(img, x, y, 0.05)
        touch(img, x, y + 1, -0.06)
    return img


def paper(seed=0, size=S, base=(214, 206, 160), grain=3, mottle=5, fibre=0.6, seams=16, strip=3.0, drift=DRIFT,
          seam=1.0):
    """Wallpaper or paper: a fine fibre grain (short pale and dark fibres in all directions), soft mottle, and, with
    `seams` (px between strips, None for none), a butt seam: a dark line with the paper edge beside it lifted (lit),
    and each strip a touch different in hue and value (+-`strip` levels), as rolls from different batches are.
    `seam` scales how strongly the butt seam shows (1.0 a fresh hang seen close; about 0.5 for a large wall, where
    a seam every half block would otherwise read as a stripe). Print a motif on it with `dye` (it keeps the fibre)."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (8, 4), drift, hue=1.5)
    rng = random.Random(sub(seed, "fibre"))
    for _ in range(int(fibre * w * h / 6)):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(1.5, 4)
        f = rng.choice((0.035, -0.04))
        for (px_, py_) in _line(x, y, x + math.cos(a) * L, y + math.sin(a) * L):
            touch(img, px_, py_, f)
    if seams:
        p = img.load()
        for s0 in range(0, w, seams):
            v, hu = rng.uniform(-strip, strip), rng.uniform(-strip, strip) * 0.6
            for y in range(h):
                for x in range(s0, min(w, s0 + seams)):
                    p[x, y] = rgba(hue_shift(lift(p[x, y], v, drift), hu))
            for y in range(h):
                touch(img, s0, y, -0.12 * seam)
                touch(img, s0 + 1, y, (0.06 if rng.random() < 0.85 else 0.1) * seam)
                touch(img, s0 - 1, y, -0.03 * seam)
    return img


def painted_metal(seed=0, size=S, base=(120, 128, 126), grain=3, mottle=5, panel=True, chips=4, under=(84, 80, 76),
                  screws=False, drift=DRIFT):
    """Painted sheet metal: an even paint with a slight orange-peel grain; with `panel`, the texture is one panel
    whose seam is at its right and bottom edge (so tiled panels meet at a groove) and whose edges are bevelled, lit
    on top; chips of `under` (bare metal, primer) along the panel edges; screws=True puts a screw head in each
    corner. Without a panel, chips become small worn spots over the face (for parts of models, whose faces show
    the texture from its corner, so edge chips would land mid-face)."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8), drift)
    peel = fbm((w, h), sub(seed, "peel"), (2, 1))
    p = img.load()
    for y in range(h):
        for x in range(w):
            p[x, y] = rgba(lift(p[x, y], peel[y][x] * 2.5, drift))
    if panel:
        inner = (0, 0, w - 1, h - 1)
        bevel(img, inner, 1, 0.16)
        ao_border(img, 3, 0.08, inner, "br")
        for x in range(w):
            touch(img, x, h - 1, -0.32)
        for y in range(h):
            touch(img, w - 1, y, -0.3)
        if chips:
            chip_edges(img, inner, sub(seed, "chips"), chips, under)
        if screws:
            for (sx, sy) in ((2, 2), (w - 4, 2), (2, h - 4), (w - 4, h - 4)):
                screw(img, sx, sy)
    elif chips:  # no panel edges to chip: small worn spots scattered over the face instead
        rng = random.Random(sub(seed, "spots"))
        for _ in range(chips):
            x, y = rng.randrange(w), rng.randrange(h)
            cells = [(x, y)] + ([(x + 1, y)] if rng.random() < 0.5 else [])
            for (cx, cy) in cells:
                put(p, w, h, cx, cy, mix(get(p, w, h, cx, cy), under, 0.7))
                touch(img, cx, cy + 1, 0.1)
    return img


def screw(img, x, y, slot=True):
    """A 2x2 screw or rivet head at (x, y): lit top-left, shaded bottom-right, a shadow under it."""
    touch(img, x, y, 0.32)
    touch(img, x + 1, y, 0.12)
    touch(img, x, y + 1, 0.04 if not slot else -0.1)
    touch(img, x + 1, y + 1, -0.18)
    touch(img, x + 1, y + 2, -0.14)
    touch(img, x + 2, y + 1, -0.1)
    return img


def brushed_metal(seed=0, size=S, base=(158, 160, 162), grain=4, direction="h", streak=9, sheen=10, drift=0.1):
    """Brushed steel or aluminium: fine streaks along `direction` ("h" or "v") from a stretched noise, plus a broad
    soft sheen band across them. Cool, low drift."""
    w, h = wh(size)
    W, H = (w, h) if direction == "h" else (h, w)
    rng = random.Random(sub(seed, "brush"))
    st = value_noise((W, H), (W // 2, 1), sub(seed, "st1"))
    st2 = value_noise((W, H), (W // 4, 1), sub(seed, "st2"))
    sh = value_noise((W, H), (W, H // 2), sub(seed, "sheen"))
    hf = fbm((W, H), sub(seed, "hue"), (16, 8))
    img = Image.new("RGBA", (W, H))
    p = img.load()
    for y in range(H):
        for x in range(W):
            d = st[y][x] * streak * 0.6 + st2[y][x] * streak * 0.4 + sh[y][x] * sheen + rng.uniform(-grain, grain) * 0.7
            p[x, y] = rgba(hue_shift(lift(base, d, drift), hf[y][x] * 1.5))
    return img if direction == "h" else img.transpose(Image.TRANSPOSE)


def galvanised(seed=0, size=S, base=(150, 154, 156), spangle=12, grain=3, cells=None, white_rust=0.0, drift=0.1):
    """Hot-dip galvanised steel: zinc spangle, crystals of a few px each a flat facet at its own brightness with a
    slight tilt across it and a faint boundary; optional white_rust (0..1) speckle."""
    w, h = wh(size)
    pts = points((w, h), cells or (w * h) // 48, sub(seed, "spangle"), 1.0)
    f1, f2, idx = worley((w, h), pts)
    rng = random.Random(sub(seed, "facets"))
    facet = [(rng.uniform(-1, 1), rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25)) for _ in pts]
    img = noise_hv(base, grain, seed, (w, h), 3, (16, 8), drift, hue=1.0)
    p = img.load()
    for y in range(h):
        for x in range(w):
            i = idx[y][x]
            v, gx, gy = facet[i]
            dx, dy = x + 0.5 - pts[i][0], y + 0.5 - pts[i][1]
            dx -= w * round(dx / w)
            dy -= h * round(dy / h)
            d = spangle * (v + gx * dx + gy * dy) * 0.8
            if f2[y][x] - f1[y][x] < 0.7:
                d -= 4
            p[x, y] = rgba(lift(p[x, y], d, drift))
    if white_rust:
        for _ in range(int(white_rust * w * h * 0.08)):
            x, y = rng.randrange(w), rng.randrange(h)
            put(p, w, h, x, y, mix(p[x, y], (214, 214, 206), 0.6))
    return img


def riveted_plate(seed=0, size=S, base=(112, 106, 100), grain=4, mottle=7, pitch=4, layout="edges", seam=True,
                  rust_amount=0.0, drift=DRIFT):
    """Riveted plate: plates meeting at a seam on the texture edge (a groove, lit below), rows of rivet heads `pitch`
    px apart 2 px in from each seam (layout="edges") or all over (layout="grid", like vanilla's riveted iron), each
    lit top-left with a shadow under it; optional rust gathering at the seams."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8, 4), drift)
    if rust_amount:
        rust(img, rust_amount, sub(seed, "rust"), edges=True)
    if seam:
        emboss_lines(img, xs=(w - 1,), ys=(h - 1,), strength=0.24)
        ao_border(img, 2, 0.1, (0, 0, w - 1, h - 1))
    if layout == "grid":
        for y in range(1, h, pitch):
            for x in range(1 + (y // pitch) % 2 * (pitch // 2), w, pitch):
                screw(img, x, y, slot=False)
    else:
        for x in range(1, w - 2, pitch):
            screw(img, x, 1, slot=False)
            screw(img, x, h - 4, slot=False)
        for y in range(1 + pitch, h - 4, pitch):
            screw(img, 1, y, slot=False)
            screw(img, w - 4, y, slot=False)
    return img


def _plank_heights(h, planks):
    if isinstance(planks, (list, tuple)):
        assert sum(planks) == h, "plank heights must add up to the texture height"
        return list(planks)
    base, extra = divmod(h, planks)
    return [base + (1 if i < extra else 0) for i in range(planks)]


def wood_planks(seed=0, size=S, base=(146, 106, 66), planks=3, direction="h", grain=4, contrast=1.0, knots=0,
                joints=0.0, flecks=1.0, per_plank=10, gap=(52, 38, 26), drift=DRIFT):
    """Planks: each board its own shade and hue (+-`per_plank`), grain streaks and wavy grain lines along it that
    bend round the odd knot, a lit top edge, a dark gap under it, and butt joints on a `joints` share of the boards
    (0 for none: every board longer than the block). `planks` is a count
    (heights spread evenly, 3 to 32 px as vanilla) or a list of heights. direction="v" turns them upright (lit edge
    on the left). knots (expected per board) and joints are features a player spots repeating block after block: keep
    them 0 on a tiled surface and give them to two or three alternates (the tiling rule). flecks (0..1) is the density
    of short dark and pale streaks in the grain, the texture vanilla's planks have."""
    w, h = wh(size)
    W, H = (w, h) if direction == "h" else (h, w)
    rng = random.Random(sub(seed, "planks"))
    img = Image.new("RGBA", (W, H))
    p = img.load()
    streak = value_noise((W, H), (W // 2, 1), sub(seed, "streak"))
    streak2 = value_noise((W, H), (W // 8, 1), sub(seed, "streak2"))
    fine = random.Random(sub(seed, "fine"))
    y0 = 0
    for j, ph in enumerate(_plank_heights(H, planks)):
        pc = hue_shift(lift(base, rng.uniform(-per_plank, per_plank), drift), rng.uniform(-3, 3))
        kn = []
        for _ in range(knots):
            if rng.random() < 0.6:
                kn.append((rng.uniform(0, W), y0 + rng.uniform(2, ph - 3), rng.uniform(1.2, 2.0)))
        rowv = [rng.uniform(-6, 6) for _ in range(ph)]  # each fibre row its own shade: the grain's streaks
        lines = []
        for _ in range(max(3, ph // 2)):
            lines.append((y0 + rng.uniform(0, ph), rng.uniform(0.3, 1.2), rng.choice((1, 2)), rng.uniform(0, 6.3),
                          rng.uniform(8, 16) * contrast))
        for yy in range(y0, y0 + ph):
            for x in range(W):
                d = (streak[yy][x] * 12 + streak2[yy][x] * 7 + rowv[yy - y0]) * contrast + fine.uniform(-grain, grain)
                for (ly, amp, k, phs, dark) in lines:
                    yl = ly + amp * math.sin(2 * math.pi * k * x / W + phs)
                    for (kx, ky, kr) in kn:  # grain swerves round a knot
                        dx = min(abs(x - kx), W - abs(x - kx))
                        yl += (3.0 * kr) * math.exp(-(dx * dx) / (2 * (2.2 * kr) ** 2)) * (1 if ly > ky else -1)
                    dist = abs(yy - yl)
                    if dist < 0.8:
                        d -= dark * (1 - dist / 0.8)
                p[x, yy] = rgba(lift(pc, d, drift))
        for (kx, ky, kr) in kn:
            for yy in range(int(ky - kr - 1), int(ky + kr + 2)):
                for xx in range(int(kx - kr * 1.6 - 1), int(kx + kr * 1.6 + 2)):
                    dd = math.hypot(min(abs(xx - kx), W - abs(xx - kx)) / 1.6, yy - ky) / kr
                    if dd < 1.0 and y0 <= yy < y0 + ph:
                        put(p, W, H, xx, yy, lift(get(p, W, H, xx, yy), -34 if dd < 0.5 else -16, drift))
        for _ in range(int(flecks * W * ph / 7)):  # short streaks along the grain
            fx, fy = rng.uniform(0, W), rng.randrange(y0 + 1, y0 + ph - 1)
            L, dk = rng.randint(2, 6), rng.choice((-1, -1, -1, 1)) * rng.uniform(10, 22) * contrast
            for i in range(L):
                put(p, W, H, int(fx) + i, fy, lift(get(p, W, H, int(fx) + i, fy), dk * math.sin(math.pi * (i + 0.5) / L), drift))
        # lit top edge, dark gap at the bottom
        for x in range(W):
            touch(img, x, y0, 0.14)
            touch(img, x, y0 + 1, 0.04)
            touch(img, x, y0 + ph - 2, -0.08)
            put(p, W, H, x, y0 + ph - 1, lift(gap, fine.uniform(-4, 4), drift))
        jx = rng.uniform(0, W) if j == 0 else (prev_jx + W * rng.uniform(0.3, 0.7)) % W
        prev_jx = jx
        if rng.random() < joints:
            for yy in range(y0, y0 + ph - 1):
                put(p, W, H, int(jx), yy, lift(gap, 12, drift))
                touch(img, int(jx) + 1, yy, 0.1)
                touch(img, int(jx) - 1, yy, -0.06)
        y0 += ph
    return img if direction == "h" else img.transpose(Image.TRANSPOSE)


def fabric(seed=0, size=S, base=(110, 124, 92), weave="plain", tone2=None, contrast=10, grain=3, mottle=6,
           thread=3, drift=DRIFT):
    """Woven cloth. weave: "plain" (a checker of warp over weft, as vanilla linen), "twill" (diagonal ribs),
    "basket" (2x2, canvas and burlap), "ripstop" (plain with a heavier thread every 8 px, tents and bags).
    tone2 colours the weft (two-tone cloth); each thread varies +-`thread` levels along its length."""
    w, h = wh(size)
    tone2 = tone2 or hue_shift(lift(base, -4), -3)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8), drift)
    rng = random.Random(sub(seed, "threads"))
    warp = [rng.uniform(-thread, thread) for _ in range(w)]
    weft = [rng.uniform(-thread, thread) for _ in range(h)]
    p = img.load()
    for y in range(h):
        for x in range(w):
            if weave == "twill":
                over = (x + y) % 4 < 2
            elif weave == "basket":
                over = ((x // 2) + (y // 2)) % 2 == 0
            else:
                over = (x + y) % 2 == 0
            c = p[x, y]
            if over:  # warp on top: lit, with the thread's own variation
                c = lift(c, contrast * 0.5 + warp[x], drift)
            else:
                c = lift(mix(c, tone2, 0.6), -contrast * 0.5 + weft[y], drift)
            p[x, y] = rgba(c)
    if weave == "ripstop":
        for k in range(0, w, 8):
            for y in range(h):
                touch(img, k, y, 0.05)
                touch(img, k + 1, y, -0.03)
        for k in range(0, h, 8):
            for x in range(w):
                touch(img, x, k, 0.05)
                touch(img, x, k + 1, -0.035)
    return img


NAPS = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0), "ne": (1, -1), "nw": (-1, -1), "se": (1, 1), "sw": (-1, 1)}


def carpet(seed=0, size=S, base=(150, 128, 98), tone2=None, mix2=0.3, nap="se", pile=10, grain=4, mottle=7,
           loop=False, pattern=None, pattern_strength=1.0, wear=0.0, drift=DRIFT):
    """Cut-pile (or loop=True: Berber) carpet. The pile is tufts on a 2 px lattice, offset row to row; each tuft is
    one fibre colour (base, or tone2 for `mix2` of them: two-tone heathering), lit at its tip on the `nap` side and
    shaded at its root, so the pile reads as brushed one way; a soft mottle of trodden and fluffed patches over it.
    `pattern` (an RGBA picture, transparent where there is none) is dyed in, keeping the pile; wear (0..1) adds
    lighter, flatter lanes."""
    w, h = wh(size)
    tone2 = tone2 or hue_shift(lift(base, -14), 4)
    rng = random.Random(sub(seed, "tufts"))
    nx, ny = NAPS[nap]
    mot = fbm((w, h), sub(seed, "mot"), (16, 8, 4))
    wearf = fbm((w, h), sub(seed, "wear"), (16, 8)) if wear else None
    tuft = {}
    rshift = [rng.randrange(2) for _ in range(h // 2)]
    for ty in range(0, h, 2):
        for tx in range(0, w, 2):
            tuft[(tx, ty)] = (tone2 if rng.random() < mix2 else base, rng.uniform(-pile, pile))
    img = Image.new("RGBA", (w, h))
    p = img.load()
    for y in range(h):
        for x in range(w):
            ty = y - y % 2
            sx = (x - rshift[ty // 2]) % w  # rows of tufts shifted at random, so no diagonal lattice shows
            tx = sx - sx % 2
            c, v = tuft[(tx, ty)]
            if loop and rng.random() < mix2 * 0.5:  # loop pile: the two yarns twist, so the tone changes within a tuft
                c = tone2 if c is base else base
            u, vv = sx - tx, y - ty  # 0/1 within the tuft
            if loop:
                d = v * 0.6 + (4 if (u + vv) % 2 == 0 else -5)
            else:
                along = (u - 0.5) * nx + (vv - 0.5) * ny  # +0.5..1 at the tip, negative at the root
                d = v + along * pile * 0.6
            d += mot[y][x] * mottle + rng.uniform(-grain, grain)
            if wearf and wearf[y][x] > 0.35:
                d = d * 0.5 + 8 * wear * (wearf[y][x] - 0.35)
            p[x, y] = rgba(lift(c, d, drift))
    if pattern is not None:
        dye(img, pattern, base, pattern_strength)
    return img


def tile(seed=0, size=S, base=(200, 196, 184), grout=(150, 144, 132), pitch=8, grout_w=1, jitter=6, uneven=4,
         glaze=True, mosaic=None, offset=0, crazing=0.0, speckle=0.0, drift=DRIFT):
    """Tiles in grout. pitch is tile plus grout (8: 7 px tiles; 4: 3 px mosaic; (w, h) for oblong). Each tile gets its
    own shade (+-`jitter`) and hue, a slight tilt across it (+-`uneven`: tiles are never quite flat), a lit top and
    left edge, a dark bottom and right edge, and with `glaze` a small highlight up and to the left. The grout is
    recessed: darker under each tile. mosaic is a list of colours picked per tile instead of base; offset shifts
    alternate rows (0.5 for a running bond); crazing (0..1) adds fine glaze cracks; speckle (0..1) gives unglazed
    stone or terrazzo tiles a body of light and dark specks."""
    w, h = wh(size)
    pw, ph = (pitch, pitch) if isinstance(pitch, int) else pitch
    assert w % pw == 0 and h % ph == 0, "the tile pitch must divide the texture"
    rng = random.Random(sub(seed, "tiles"))
    img = noise_hv(grout, 3, sub(seed, "grout"), (w, h), 3, (8, 4), drift)
    gp = noise_hv(base, 3, seed, (w, h), 3, (16, 8), drift)
    p, g = img.load(), gp.load()
    for r in range(h // ph):
        shift = int(round((r * offset * pw) % pw)) if offset else 0
        for c in range(w // pw):
            x0, y0 = c * pw + shift, r * ph
            col = rng.choice(mosaic) if mosaic else base
            v, hu = rng.uniform(-jitter, jitter), rng.uniform(-2.5, 2.5)
            ax, ay = rng.uniform(-uneven, uneven), rng.uniform(-uneven, uneven)
            tw, th = pw - grout_w, ph - grout_w
            for yy in range(th):
                for xx in range(tw):
                    gx = (xx / max(1, tw - 1) - 0.5) * ax + (yy / max(1, th - 1) - 0.5) * ay
                    gpx = g[(x0 + xx) % w, (y0 + yy) % h]
                    cc = lift(col, (lum(gpx) - lum(base)) + v + gx, drift)
                    put(p, w, h, x0 + xx, y0 + yy, hue_shift(cc, hu))
            bevel(img, (x0, y0, x0 + tw, y0 + th), 1, 0.12 if glaze else 0.08)
            if glaze and tw >= 3:
                touch(img, x0 + 1, y0 + 1, 0.2)
                touch(img, x0 + 2, y0 + 1, 0.12)
                if th >= 5:
                    touch(img, x0 + 1, y0 + 2, 0.1)
            for xx in range(-grout_w, tw):  # grout in the shadow of the tile above
                touch(img, x0 + xx, y0 + th, -0.14)
            for yy in range(th):
                touch(img, x0 + tw, y0 + yy, -0.07)
    if speckle:
        for _ in range(int(speckle * w * h * 0.25)):
            x, y = rng.randrange(w), rng.randrange(h)
            if (x % pw) < pw - grout_w and (y % ph) < ph - grout_w:
                touch(img, x, y, rng.choice((-0.14, -0.08, 0.08)))
    if crazing:
        for k in range(int(crazing * w * h / 128)):
            crack(img, sub(seed, f"craze{k}"), length=(3, 7), strength=0.12)
    return img


def glass(seed=0, size=S, base=(196, 214, 216), alpha=72, streaks=2, dust=0.02, edge=True, grain=2):
    """Window glass: a faint tint at `alpha`, soft diagonal reflection bands (brighter and more opaque), a little
    dust, and with `edge` a greener rim 1 px in, where the pane's thickness shows. Needs a transparent render
    pass to show as glass (alpha under 128 is cut out in the opaque pass)."""
    w, h = wh(size)
    rng = random.Random(sub(seed, "glass"))
    img = noise_hv(base, grain, seed, (w, h), 3, (16, 8), 0.05, hue=0)
    p = img.load()
    bands = [(rng.uniform(0, w), rng.uniform(1.0, 3.0), rng.uniform(0.5, 1.0)) for _ in range(streaks)]
    for y in range(h):
        for x in range(w):
            c = p[x, y]
            a, d = alpha, 0.0
            for (b0, bw, bs) in bands:
                t = ((x + y) - b0) % w
                t = min(t, w - t)
                if t < bw:
                    k = (1 - t / bw) * bs
                    d += 26 * k
                    a += 48 * k
            if edge and (x in (0, w - 1) or y in (0, h - 1)):
                c, a = mix(c, (150, 186, 170), 0.5), a + 40
            if rng.random() < dust:
                d += rng.uniform(-14, 10)
                a += 30
            p[x, y] = rgba(lift(c, d, 0.05), min(255, int(a)))
    return img


def rubber(seed=0, size=S, base=(48, 46, 46), grain=3, mottle=4, pattern=None, pitch=8, drift=0.08):
    """Rubber: dark, matte, low contrast. pattern: None, "studs" (round studs on a `pitch` grid, lit on top),
    "ribs" (horizontal ribs), "diamond" (a tread of small diamonds)."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8), drift, hue=1.0)
    if pattern == "studs":
        for y in range(pitch // 2, h + pitch // 2, pitch):
            for x in range(pitch // 2 - 1 + (y // pitch % 2) * (pitch // 2), w + pitch, pitch):
                for (dx, dy, f) in ((0, -1, 0.3), (1, -1, 0.22), (-1, 0, 0.2), (0, 0, 0.26), (1, 0, 0.12), (2, 0, -0.04),
                                    (-1, 1, 0.06), (0, 1, 0.04), (1, 1, -0.02), (0, 2, -0.1), (1, 2, -0.1)):
                    touch(img, x + dx, y + dy, f, drift)
    elif pattern == "ribs":
        emboss_lines(img, ys=tuple(range(0, h, max(2, pitch // 2))), raised=True, strength=0.28)
    elif pattern == "diamond":
        for y in range(0, h, pitch // 2):
            for x in range((y // (pitch // 2)) % 2 * (pitch // 2), w, pitch):
                for (dx, dy, f) in ((0, 0, 0.3), (-1, 1, 0.18), (1, 1, -0.05), (0, 2, -0.25)):
                    touch(img, x + dx, y + dy, f, drift)
    return img


def asphalt(seed=0, size=S, base=(66, 65, 64), grain=5, mottle=6, aggregate=0.32, binder=0.4, cracks=0, drift=DRIFT):
    """Asphalt: dense aggregate (1 px chips, mostly pale grey, some warm), each with a shadow pixel under it, binder-
    rich darker patches (`binder` 0..1), small pits, and optional hairline cracks."""
    w, h = wh(size)
    img = noise_hv(base, grain, seed, (w, h), mottle, (16, 8, 4), drift)
    rng = random.Random(sub(seed, "asph"))
    bf = fbm((w, h), sub(seed, "binder"), (8, 4))
    p = img.load()
    for y in range(h):
        for x in range(w):
            if bf[y][x] > 1 - binder:
                p[x, y] = rgba(lift(p[x, y], -7 * (bf[y][x] - (1 - binder)) / max(0.01, binder), drift))
    for _ in range(int(aggregate * w * h)):
        x, y = rng.randrange(w), rng.randrange(h)
        if bf[y][x] > 1 - binder * 0.5 and rng.random() < 0.6:
            continue
        v = rng.uniform(8, 30)
        c = hue_shift(lift(base, v, drift), rng.choice((-3, 0, 2, 5)))
        put(p, w, h, x, y, c)
        if rng.random() < 0.5:
            touch(img, x, y + 1, -0.12)
    for _ in range(int(0.01 * w * h)):
        x, y = rng.randrange(w), rng.randrange(h)
        touch(img, x, y, -0.25)
    for k in range(cracks):
        crack(img, sub(seed, f"acrack{k}"), length=(12, 26), strength=0.35)
    return img


def brick(seed=0, size=S, base=(150, 82, 62), mortar=(176, 168, 154), course=8, length=16, offset=0.5, mortar_w=1,
          jitter=12, hue=5, recess=1.0, pits=0.03, chamfer=False, grain=5, mottle=9, drift=DRIFT):
    """Brick or block courses: each unit its own shade (+-`jitter`) and hue (+-`hue`), a fine face texture, a lit top
    edge and a darker bottom edge; the mortar recessed (`recess` 0..1: darker under each unit, lighter at the top of
    each bed joint). course/length are the unit pitch with mortar (8x16 brick; 16x32 or 8x16 for a block wall with
    chamfer=True for a bevelled face); offset is the stagger per course (0.5 running bond, 0 stack bond, 0.25 raking).
    The stagger must come round over the texture: (h / course) * offset * length is a whole number of lengths."""
    w, h = wh(size)
    rows = h // course
    assert h % course == 0 and w % length == 0, "course and length must divide the texture"
    assert abs((rows * offset * length) % length) < 1e-6, "the stagger must come back round over the texture height"
    rng = random.Random(sub(seed, "bricks"))
    img = noise_hv(mortar, 3, sub(seed, "mortar"), (w, h), 4, (8, 4), drift)
    face = noise_hv(base, grain, seed, (w, h), mottle, (8, 4, 2), drift, hue=3)
    p, fp = img.load(), face.load()
    boxes = []
    for r in range(rows):
        y0 = r * course
        shift = int(round(r * offset * length)) % length
        for k in range(w // length + 1):
            x0 = shift + k * length - length
            v, hu = rng.uniform(-jitter, jitter), rng.uniform(-hue, hue)
            bw, bh = length - mortar_w, course - mortar_w
            if x0 + bw <= 0 or x0 >= w:
                continue
            for yy in range(bh):
                for xx in range(bw):
                    X = (x0 + xx) % w
                    c = fp[X, (y0 + yy) % h]
                    put(p, w, h, X, y0 + yy, hue_shift(lift(c, v, drift), hu))
            boxes.append((x0, y0, x0 + bw, y0 + bh))
    for (x0, y0, x1, y1) in boxes:
        for _ in range(int(pits * (x1 - x0) * (y1 - y0))):
            touch(img, rng.randrange(x0, x1), rng.randrange(y0 + 1, y1), -0.18)
        if chamfer:
            bevel(img, (x0, y0, x1, y1), 1, 0.16)
        else:
            for x in range(x0, x1):
                touch(img, x, y0, 0.12)
                touch(img, x, y1 - 1, -0.1)
            for y in range(y0 + 1, y1 - 1):
                touch(img, x0, y, 0.04)
                touch(img, x1 - 1, y, -0.04)
        for x in range(x0, x1 + mortar_w):  # bed joint under the unit: in its shadow
            touch(img, x, y1, -0.16 * recess)
        for y in range(y0, y1):  # head joint
            touch(img, x1, y, -0.06 * recess)
    return img


# ---------------- Ceiling module (textures; B3 kept the T-bar and the troffer painted, see gen_textures) ----------------

TBAR = (198, 196, 190)


def tbar(img, colour=TBAR, rail_px=1, split=True):
    """Paints the T-bar grid rail round the texture's edge. With split (the default) the 2 px rail is shared: the
    right and bottom `rail_px` columns carry its first half and the left and top ones its second, so tiled blocks
    meet in one rail; the lit half (the rolled edge of the flange) is at the left and top. split=False paints the
    whole 2*rail_px rail on the left and top edges only."""
    w, h = img.size
    rng = random.Random(7)
    p = img.load()
    lit, base = lift(colour, 16), colour
    k = rail_px
    cols = ([(x, base) for x in range(w - k, w)] + [(x, lit) for x in range(k)]) if split else \
        ([(x, lit if x < k else base) for x in range(2 * k)])
    rows = ([(y, base) for y in range(h - k, h)] + [(y, lit) for y in range(k)]) if split else \
        ([(y, lit if y < k else base) for y in range(2 * k)])
    for (x, c) in cols:
        for y in range(h):
            p[x, y] = rgba(lift(c, rng.uniform(-2, 2)))
    for (y, c) in rows:
        for x in range(w):
            p[x, y] = rgba(lift(c, rng.uniform(-2, 2)))
    return img


def ceiling_tile(seed=0, size=S, base=(220, 212, 186), rail=TBAR, fissures=0.6, recess=2, rail_px=1, at=None,
                 stain_color=None, drift=DRIFT):
    """A lay-in mineral-fibre ceiling tile in its T-bar grid: the board's fissures (short worm-like dark pits with a
    lit lip, and pin-holes), a soft recess where the tile's edge steps up into the grid (`recess` px, shadowed on
    the top and left, lit on the bottom and right), and the 2 px rail (see tbar). stain_color puts one water stain
    at `at` (or a seed-chosen place) inside the tile, never across the rail: use it in an alternate."""
    w, h = wh(size)
    img = noise_hv(base, 3, seed, (w, h), 4, (16, 8), drift)
    rng = random.Random(sub(seed, "fissure"))
    k = rail_px
    inner = (k, k, w - k, h - k)
    for _ in range(int(fissures * w * h / 14)):
        x, y = rng.uniform(k, w - k), rng.uniform(k, h - k)
        a = rng.uniform(0, 2 * math.pi)
        for i in range(rng.choice((1, 1, 2, 2, 3))):
            xi, yi = int(x) % w, int(y) % h
            if k <= xi < w - k and k <= yi < h - k:
                touch(img, xi, yi, -0.09)
                if yi + 1 < h - k:
                    touch(img, xi, yi + 1, 0.04)
            a += rng.uniform(-1.2, 1.2)
            x, y = x + math.cos(a), y + math.sin(a)
    for _ in range(int(fissures * w * h / 40)):
        touch(img, rng.randrange(k, w - k), rng.randrange(k, h - k), -0.07)
    if stain_color:  # kept inside the tile: it fades out before the recess rather than being cut by it
        st = img.copy()
        if at is None:
            r2 = random.Random(sub(seed, "stainat"))
            at = (r2.uniform(0.3, 0.7) * w, r2.uniform(0.3, 0.7) * h)
        stain(st, sub(seed, "stain"), radius=min(w, h) * 0.3, color=stain_color, strength=0.4, at=at, ring=0.7)
        sp, p = st.load(), img.load()
        for y in range(k, h - k):
            for x in range(k, w - k):
                e = min(x - k, w - k - 1 - x, y - k, h - k - 1 - y)
                t = max(0.0, min(1.0, (e - recess) / 3))
                if t:
                    p[x, y] = rgba(mix(p[x, y], sp[x, y], t))
    if recess:
        inset(img, inner, recess, 0.12, drift)
        ao_border(img, recess + 1, 0.06, inner, "tl")
    tbar(img, rail, rail_px)
    return img


def troffer_lens(seed=0, size=S, lit=1.0, lens=(238, 238, 228), frame=(212, 210, 204), frame_px=2, cell=2,
                 tubes=2, rail=TBAR, rail_px=1, glow=(255, 250, 232)):
    """A 2x2 troffer seen from below: the T-bar rail, a bevelled housing frame (`frame_px`, its outer px a light rim
    and its inner px the dark step down to the lens) and a prismatic lens: a grid of `cell` px prisms, each a bright
    facet and a dim one, brighter over the `tubes` behind it. lit 1.0 is on, 0.5 dim, 0 off (a grey lens with the
    prisms still showing). Give a red `lens`/`glow` for the Red Rooms."""
    w, h = wh(size)
    img = new((w, h), frame)
    p = img.load()
    rng = random.Random(sub(seed, "lens"))
    k = rail_px
    x0, y0, x1, y1 = k + frame_px, k + frame_px, w - k - frame_px, h - k - frame_px
    off = mix(lens, (150, 152, 150), 0.55)
    col = mix(off, glow, lit) if lit < 1 else mix(lens, glow, 0.35)
    for y in range(y0, y1):
        for x in range(x0, x1):
            u = (x - x0 + 0.5) / (x1 - x0)
            band = max(math.exp(-((u - (i + 0.5) / tubes) * tubes * 2.2) ** 2) for i in range(tubes))
            v = (y - y0 + 0.5) / (y1 - y0)
            fall = 1 - 0.35 * (2 * v - 1) ** 4
            d = (band * 22 - 10) * lit * fall
            cx, cy = (x - x0) % cell, (y - y0) % cell
            if cell == 2:
                d += (9, -4)[cx ^ cy] if (cx, cy) == (0, 0) or (cx ^ cy) else -9
            else:
                d += 10 if (cx, cy) == (0, 0) else -9 if (cx, cy) == (cell - 1, cell - 1) else 0
            d *= 0.6 + 0.4 * max(lit, 0.4)
            p[x, y] = rgba(lift(col, d + rng.uniform(-1.5, 1.5), 0.08))
    for y in range(k, h - k):
        for x in range(k, w - k):
            if not (x0 <= x < x1 and y0 <= y < y1):
                p[x, y] = rgba(lift(frame, rng.uniform(-2, 2)))
    bevel(img, (k, k, w - k, h - k), 1, 0.12)
    inset(img, (x0, y0, x1, y1), 1, 0.2 if lit < 0.6 else 0.12)
    tbar(img, rail, rail_px)
    return img
