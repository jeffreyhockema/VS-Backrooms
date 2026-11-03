"""Level 47 round 4 (2026-11-02): the surfaces redone to the asset-quality bar, as relief.

Every bark, the moss and the stones are painted from a periodic height field (numpy, wrapped so they tile) and lit from
above-left the way matlib's rule 2 says: ridges lit on their upper-left flank and dark on the lower-right, furrows deep
and cool, a warm lift on the lit side. Moss grows over a surface as cushions with their own relief (a soft shadow
under each cushion's lower edge), lichen as rosettes with a pale rim. Called from tools/gen_47.py (main); used read-only.
"""
import math
import random

import numpy as np
from PIL import Image

import matlib as M

S = 32


# ---------------- Periodic fields ----------------

def vnoise(seed, cells, size=S):
    """Periodic value noise in [-1, 1], cells per side (divides size), bicubic-smooth."""
    rng = np.random.default_rng(seed)
    g = rng.uniform(-1, 1, (cells, cells))
    t = np.arange(size) * cells / size
    i0 = np.floor(t).astype(int)
    f = t - i0
    f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % cells
    a = g[np.ix_(i0, i0)]
    b = g[np.ix_(i0, i1)]
    c = g[np.ix_(i1, i0)]
    d = g[np.ix_(i1, i1)]
    fy, fx = f[:, None], f[None, :]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(seed, cells=(2, 4, 8, 16), gain=0.55, size=S):
    out = np.zeros((size, size))
    amp, tot = 1.0, 0.0
    for k, c in enumerate(cells):
        out += amp * vnoise(seed * 31 + k, c, size)
        tot += amp
        amp *= gain
    return out / tot


def worley(seed, n, size=S, sx=1.0, sy=1.0):
    """Periodic F1, F2 and the nearest point's index; sx/sy stretch the metric (scales taller than wide...)."""
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0, size, (n, 2))
    yy, xx = np.mgrid[0:size, 0:size].astype(float)
    best = np.full((size, size), 1e9)
    second = np.full((size, size), 1e9)
    idx = np.zeros((size, size), int)
    for k, (px, py) in enumerate(pts):
        dx = np.abs(xx + 0.5 - px)
        dx = np.minimum(dx, size - dx) * sx
        dy = np.abs(yy + 0.5 - py)
        dy = np.minimum(dy, size - dy) * sy
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        idx = np.where(closer, k, idx)
        best = np.where(closer, d, best)
    return best, second, idx, pts


def warp_x(field, amount, seed):
    """Shifts each row sideways by a slow periodic wander (so vertical ridges meander)."""
    w = vnoise(seed, 2) * amount + vnoise(seed + 1, 4) * amount * 0.4
    out = np.empty_like(field)
    for y in range(S):
        for x in range(S):
            sx = (x + w[y, x]) % S
            x0 = int(math.floor(sx))
            f = sx - x0
            out[y, x] = field[y, x0] * (1 - f) + field[y, (x0 + 1) % S] * f
    return out


# ---------------- Lighting ----------------

def light(h, base, albedo=None, relief=60.0, ao=40.0, grain=4.0, seed=0, warm=True):
    """Lights a height field (0 low .. 1 high): the slope toward the upper-left lit, away from it dark, low places
    darker still (occlusion); albedo is a per-pixel lift added first. Returns RGBA."""
    hx = (np.roll(h, 1, axis=1) - np.roll(h, -1, axis=1)) * 0.5
    hy = (np.roll(h, 1, axis=0) - np.roll(h, -1, axis=0)) * 0.5
    slope = -(hx * 0.6 + hy * 0.8)  # positive where the surface faces up-left
    rng = np.random.default_rng(seed)
    d = slope * relief - (1 - h) * ao + (albedo if albedo is not None else 0) + rng.uniform(-grain, grain, h.shape)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.lift(base, float(d[y, x])))
    return img


def tint_mix(img, colour, mask, seed=0, var=10):
    """Mixes a colour into an image where mask (0..1) says, with a little variation."""
    rng = random.Random(seed)
    px = img.load()
    for y in range(S):
        for x in range(S):
            k = float(mask[y, x])
            if k <= 0:
                continue
            c = M.lift(colour, rng.uniform(-var, var))
            px[x, y] = M.rgba(M.mix(px[x, y], c, min(1, k)))
    return img


# ---------------- Bark ----------------

def oak(seed, base=(108, 96, 80)):
    """Old oak: deep, meandering vertical furrows; the ridges between them rough and broken into long, irregular plates
    (their breaks soft and slanting, never a course of bricks); grey-brown, the ridges' faces paler and greyer
    (weathered), the furrows near black-brown."""
    rng = np.random.default_rng(seed)
    cols = 5
    xx = np.arange(S)
    ph = rng.uniform(0, 1)
    # Ridge widths vary: a wandering phase per row
    u = (xx / S * cols + ph) % 1.0
    prof = np.clip(np.sin(u * math.pi) * 1.6, 0, 1) ** 0.5
    ridge = np.repeat(prof[None, :], S, axis=0)
    # (a ragged wander, not a wave: the furrows split and jog)
    wob = fbm(seed + 1, (4, 8, 16), 0.7) * 2.6
    out = np.empty_like(ridge)
    for y in range(S):
        for x in range(S):
            sx = (x + wob[y, x]) % S
            x0 = int(sx)
            f = sx - x0
            out[y, x] = ridge[y, x0] * (1 - f) + ridge[y, (x0 + 1) % S] * f
    ridge = out
    # Plates: each ridge's height wanders along it, and now and then a short slanting crack
    along = 0.75 + 0.25 * fbm(seed + 2, (2, 4, 8))
    h = ridge * along
    col_of = ((np.arange(S)[None, :] / S * cols + ph) % cols).astype(int).repeat(S, 0)
    for c in range(cols):
        if rng.random() < 0.6:
            y0 = rng.integers(0, S)
            for k in range(3):
                yy = (y0 + k) % S
                m = col_of[yy] == c
                xs = np.where(m)[0]
                if len(xs):
                    x = xs[min(len(xs) - 1, k * len(xs) // 3)]
                    h[yy, x] *= 0.35
                    h[yy, (x + 1) % S] *= 0.55
    alb = 10 * fbm(seed + 3, (2, 4)) + 9 * (h > 0.72) - 4 * (h < 0.3)
    img = light(h, base, alb, relief=72, ao=50, grain=4, seed=seed + 4)
    M.hue_jitter(img, 3, seed + 5)
    return img


def fir(seed, base=(108, 72, 52)):
    """Old Douglas fir: thick corky red-brown ridges, three to a block side, furrows deep and dark, cross-checks on
    the ridges, the ridge tops paler and dusty."""
    rng = np.random.default_rng(seed)
    cols = 3
    xx = np.arange(S)
    ph = rng.uniform(0, 1)
    u = (xx / S * cols + ph) % 1.0
    prof = np.clip(np.sin(u * math.pi) * 1.3, 0, 1) ** 0.45
    h = np.repeat(prof[None, :], S, axis=0)
    h = warp_x(h, 3.0, seed + 1)
    checks = np.ones((S, S))
    for _ in range(9):
        y0, x0, L = rng.integers(0, S), rng.integers(0, S), rng.integers(3, 7)
        for k in range(L):
            checks[y0 % S, (x0 + k) % S] = 0.55
    h = h * checks * (0.8 + 0.2 * fbm(seed + 2, (4, 8, 16)))
    alb = 12 * (h > 0.8) + 8 * fbm(seed + 3, (2, 4))
    return light(h, base, alb, relief=64, ao=50, grain=4, seed=seed + 4)


def spruce(seed, base=(98, 86, 72)):
    """Spruce: grey-brown bark flaking in thin round scales, each scale's lower edge lifted (lit above, a dark gap below)."""
    f1, f2, idx, pts = worley(seed, 26, sx=1.0, sy=1.25)
    rng = np.random.default_rng(seed + 1)
    tone = rng.uniform(-14, 10, len(pts))
    yy = np.mgrid[0:S, 0:S][0].astype(float)
    py = pts[idx][..., 1]
    dy = (yy + 0.5 - py)
    dy = np.where(dy > S / 2, dy - S, np.where(dy < -S / 2, dy + S, dy))
    # The scale rises toward its lower edge
    h = np.clip(0.55 + dy / 7.0, 0, 1) * np.clip((f2 - f1) / 1.6, 0, 1) ** 0.4
    alb = tone[idx] + 4 * fbm(seed + 2, (4, 8))
    return light(h, base, alb, relief=55, ao=40, grain=3, seed=seed + 3)


def beech(seed, base=(138, 138, 130)):
    """Beech: smooth pale grey, faint undulations, dark horizontal lenticel dashes, a green film of algae down one side,
    an eye-shaped branch scar in some."""
    h = 0.6 + 0.25 * fbm(seed, (2, 4)) + 0.08 * fbm(seed + 1, (8, 16))
    img = light(h, base, 6 * fbm(seed + 2, (2, 4)), relief=40, ao=12, grain=3, seed=seed + 3)
    rng = random.Random(seed)
    for _ in range(26):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(2, 4)):
            M.touch(img, (x + k) % S, y, -0.13)
        M.touch(img, x, y + 1, 0.06)
    algae = np.clip(fbm(seed + 4, (2, 4, 8)) * 1.6 + 0.1, 0, 1) * 0.45
    tint_mix(img, (104, 128, 84), algae, seed + 5, 6)
    if seed % 2 == 0:
        px = img.load()
        cx, cy = rng.randrange(6, 26), rng.randrange(8, 24)
        for y in range(-2, 3):
            for x in range(-4, 5):
                e = (x / 4) ** 2 + (y / 1.6) ** 2
                if e < 1:
                    px[(cx + x) % S, (cy + y) % S] = M.rgba(M.lift((62, 58, 52), -10 * (1 - e)))
                elif e < 1.5 and y < 0:
                    M.touch(img, (cx + x) % S, (cy + y) % S, 0.1)
    return img


def dead(seed, base=(152, 146, 134)):
    """Dead wood: the bark mostly gone, silver-grey wood split along a wandering grain, a few strips of dark bark left in
    relief, a beetle gallery or two."""
    xx = np.arange(S)
    grain = np.cos(2 * math.pi * xx / 3.2)[None, :].repeat(S, 0) * 0.15 + 0.6
    h = warp_x(grain, 2.0, seed)
    rng = np.random.default_rng(seed + 1)
    for _ in range(4):  # splits
        x0 = rng.integers(0, S)
        for y in range(S):
            if rng.random() < 0.85:
                h[y, x0] = 0.05
    img = light(h, base, 6 * fbm(seed + 2, (2, 4)), relief=40, ao=60, grain=3, seed=seed + 3)
    px = img.load()
    r = random.Random(seed)
    for _ in range(3):  # strips of bark, raised
        x0, y0, hh, w = r.randrange(S), r.randrange(S), r.randint(7, 15), r.randint(3, 5)
        for y in range(y0, y0 + hh):
            for x in range(x0, x0 + w):
                edge = x == x0 or y == y0
                c = M.lift((72, 62, 52), r.uniform(-8, 6) + (14 if edge else 0))
                px[x % S, y % S] = M.rgba(c)
            px[(x0 + w) % S, y % S] = M.rgba(M.lift(px[(x0 + w) % S, y % S], -40))
    for _ in range(2):  # beetle galleries
        x, y = r.randrange(S), r.randrange(S)
        for k in range(10):
            x += r.choice((-1, 0, 1))
            y += 1
            M.touch(img, x % S, y % S, -0.3)
    return img


def green(seed, base=(70, 92, 54)):
    """A green giant's bark: oak-furrowed, green, moss deep in every furrow."""
    img = oak(seed, base)
    h = np.repeat(((np.arange(S) / S * 5) % 1.0)[None, :], S, 0)
    return img


# ---------------- Moss and lichen ----------------

MOSS_DARK, MOSS, MOSS_LIT = (44, 70, 30), (74, 108, 40), (138, 160, 70)


def moss_field(seed, scale=1.0):
    """The height of moss cushions: overlapping small domes, each a little different, fine stems over them."""
    f1, f2, idx, pts = worley(seed, int(22 * scale))
    dome = np.clip(1 - f1 / 4.2, 0, 1) ** 0.7
    stems = fbm(seed + 1, (16, 32 if S % 32 == 0 else 16), 0.7)
    return np.clip(dome * 0.85 + 0.15 * stems + 0.05, 0, 1)


def moss(seed, base=MOSS):
    """Thick moss: cushions of fine green stems, lit on top, the gaps between them dark; yellow-green tips catch light."""
    h = moss_field(seed)
    tone = 10 * fbm(seed + 2, (2, 4))
    img = light(h, base, tone, relief=50, ao=34, grain=6, seed=seed + 3)
    rng = random.Random(seed + 4)
    px = img.load()
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        if h[y, x] > 0.6:
            px[x, y] = M.rgba(M.lift(MOSS_LIT, rng.uniform(-14, 8)))
    return img


def overgrow(img, seed, cover=0.5, top_bias=0.0, side_bias=0.0, base=MOSS):
    """Moss grown over a surface as cushions: a soft-edged mask (more toward the top by top_bias, toward the left by
    side_bias), the moss lit with its own relief, a shadow under each cushion's lower edge, stray tufts past its edge."""
    mk = fbm(seed, (2, 4, 8)) + (cover - 0.5) * 1.6
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    mk = mk + top_bias * (0.5 - yy / S) + side_bias * (0.5 - xx / S)
    mask = mk > 0.0
    mossimg = moss(seed + 7, base)
    src = mossimg.load()
    px = img.load()
    rng = random.Random(seed + 8)
    for y in range(S):
        for x in range(S):
            if mask[y, x]:
                px[x, y] = src[x, y]
            else:
                above = mask[(y - 1) % S, x]
                if above:
                    px[x, y] = M.rgba(M.lift(px[x, y], -30))  # the cushion's shadow below its edge
                elif mk[y, x] > -0.12 and rng.random() < 0.28:
                    px[x, y] = M.rgba(M.lift(base, rng.uniform(-10, 14)))
    return img


def lichen(img, seed, colour=(168, 176, 132), n=4, rad=(2.0, 4.5)):
    """Crustose lichen in rosettes: a pale rim, a greyer middle, little dark fruiting dots."""
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        cx, cy, r = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(*rad)
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.1) / r
                d += 0.25 * (rng.random() - 0.5)
                if d < 0.7:
                    c = M.lift(colour, -12 + rng.uniform(-6, 6))
                elif d < 1.0:
                    c = M.lift(colour, 4 + rng.uniform(-4, 4))
                else:
                    continue
                px[x % S, y % S] = M.rgba(c)
        for _ in range(int(r)):
            px[int(cx + rng.uniform(-r / 2, r / 2)) % S, int(cy + rng.uniform(-r / 2, r / 2)) % S] = M.rgba(M.lift(colour, -60))
    return img


# ---------------- Stone ----------------

def granite(seed, base=(118, 116, 110)):
    """Granite boulder: rounded relief, feldspar and mica specks, a few crazing cracks, lichen rosettes."""
    h = 0.55 + 0.35 * fbm(seed, (2, 4, 8))
    img = light(h, base, 0, relief=60, ao=24, grain=5, seed=seed + 1)
    rng = random.Random(seed + 2)
    px = img.load()
    for _ in range(60):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(rng.choice([(172, 166, 156), (70, 68, 66), (150, 130, 118)]), rng.uniform(-8, 8)))
    for _ in range(2):
        x, y, a = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(0, math.pi)
        for k in range(rng.randint(6, 12)):
            a += rng.uniform(-0.5, 0.5)
            x, y = x + math.cos(a), y + math.sin(a)
            M.touch(img, int(x) % S, int(y) % S, -0.28)
    return lichen(img, seed + 3, (150, 156, 120), n=2, rad=(1.5, 3.0))


def rgba_save_ok(img):
    """(The opaque-pass rule: no translucent texels.) Forces alpha to 0 or 255."""
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= 128 else 0)
    return img
