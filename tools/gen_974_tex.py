"""Level 974, Kitty's House: every texture (block/974/ and item/974/). Called from gen_974.py.

Baker-Miller pink paint, white trim, blush carpet, a pink-and-white kitchen checker, white hexagon bath tile, a
mint square tile, and the soft things: duvets, plush fur, posters of original mascots (a round grey cat, a bunny
with a strawberry, a smiling star, a smiling slice of toast, a frog in a mushroom hat, a rainbow), and the four
paintings behind the windows. Pictures are drawn large and scaled down, so they stay soft at 32 px.
"""
import math
import os
import random
import zlib

import iconkit  # B17: finishing for 2D item icons

from PIL import Image, ImageDraw, ImageFilter

import texlib

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures")
S = 32


def hexc(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


PINK = hexc(0xFAA9BF)        # the wall paint: canon's #F09AB0 lifted 8% so the lit wall lands near it in game
PINK_DARK = hexc(0xED97AE)
PINK_LIGHT = hexc(0xF7AEC1)
PAINT_LIGHT = hexc(0xFDBFD0)
TRIM = hexc(0xF8F3F0)
CARPET = hexc(0xEDD5D2)
CARPET_FLECK = hexc(0xE2C4C2)
CHECK_PINK = hexc(0xF4B6C6)
CHECK_WHITE = hexc(0xFBF6F4)
HEX_WHITE = hexc(0xFAF7F5)
HEX_PINK = hexc(0xF2BFCB)
CEILING = hexc(0xFAF6F4)
MINT = hexc(0xBFE8D7)
LILAC = hexc(0xD9C6F0)
BUTTER = hexc(0xFBEBA8)
SKY = hexc(0xBCD8F2)
KITTY = hexc(0x0A0A0C)
CHROME = (204, 210, 216)
GREY_CAT = (176, 176, 186)
BEAR = (216, 182, 146)
STRAWBERRY = (226, 64, 86)
LEAF = (110, 186, 104)
INK = (70, 52, 62)
BLUSH = (246, 150, 170)

PASTELS = {"pink": PINK_LIGHT, "mint": MINT, "lilac": LILAC, "sky": SKY}


def seed_of(name):
    return zlib.crc32(name.encode()) & 0xFFFFFF


def clamp(v):
    return max(0, min(255, int(round(v))))


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(clamp(v * k) for v in c[:3])


def save(img, name):
    path = os.path.join(TEX, "block", "974", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def save_item(img, name):
    if iconkit.is_icon(f"item/974/{name}"):
        img = iconkit.finish(img, seed=f"item/974/{name}")   # B17: lit and outlined as vanilla's icons are
    path = os.path.join(TEX, "item", "974", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def flat(c, a=255, size=S):
    return Image.new("RGBA", (size, size), tuple(c) + (a,))


def noisy(base, amount, key, size=S):
    rng = random.Random(seed_of(key))
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            d = rng.uniform(-amount, amount)
            px[x, y] = tuple(clamp(v + d) for v in base) + (255,)
    return img


def soft(img, key, amount, octaves=3):
    """Adds tileable soft variation (a periodic noise field) to an image, +-amount in brightness."""
    field = texlib._periodic_noise(seed_of(key), octaves)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            d = field[y][x] * amount
            px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d), a)
    return img


def big(size=S, scale=4, bg=(0, 0, 0, 0)):
    """A canvas drawn at scale x the final size, to be reduced (soft edges for pictures)."""
    img = Image.new("RGBA", (size * scale, size * scale), bg)
    return img, ImageDraw.Draw(img), scale


def reduce(img, size=S):
    return img.resize((size, size), Image.LANCZOS)


# ======================================================================== Structure

def paint(key):
    """Baker-Miller pink, rolled on: a fine stipple and soft, wide unevenness."""
    img = noisy(PINK, 3, key)
    rng = random.Random(seed_of(key + "s"))
    px = img.load()
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        c = PAINT_LIGHT if rng.random() < 0.5 else PINK_DARK
        r, g, b, a = px[x, y]
        px[x, y] = mix((r, g, b), c, 0.45) + (255,)
    return soft(img, key + "f", 4)


def trim():
    """White trim paint over wood: almost flat (moulding boxes overlap at corners, so it must not shimmer)."""
    img = flat(TRIM)
    px = img.load()
    rng = random.Random(seed_of("trim"))
    for x in range(S):
        d = rng.uniform(-1.2, 1.2)
        for y in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d), 255)
    return img


def ceiling():
    img = noisy(CEILING, 2, "ceiling")
    return soft(img, "ceilingf", 3)


def carpet(key):
    """A soft blush cut-pile carpet: loops in short diagonal rows, flecked a shade darker."""
    rng = random.Random(seed_of(key))
    img = noisy(CARPET, 4, key)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + 2 * y) % 5 == 0:
                r, g, b, a = px[x, y]
                px[x, y] = mix((r, g, b), CARPET_FLECK, 0.5) + (255,)
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = CARPET_FLECK + (255,)
    for _ in range(25):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = mix(CARPET, (255, 255, 255), 0.35) + (255,)
    return soft(img, key + "f", 3)


def checker():
    """Kitchen checker: 4 x 4 tiles to a block, pink and white, thin pale grout, glazed."""
    img = flat((226, 214, 214))
    px = img.load()
    rng = random.Random(seed_of("checker"))
    for ty in range(4):
        for tx in range(4):
            c = CHECK_PINK if (tx + ty) % 2 == 0 else CHECK_WHITE
            f = rng.uniform(0.985, 1.01)
            for y in range(ty * 8, ty * 8 + 8):
                for x in range(tx * 8, tx * 8 + 8):
                    if x % 8 == 0 or y % 8 == 0:
                        continue
                    k = f * (1.03 if (x % 8 == 1 or y % 8 == 1) else 1.0)
                    n = rng.uniform(-1.5, 1.5)
                    px[x, y] = tuple(clamp(v * k + n) for v in c) + (255,)
    return img


def bathhex():
    """White hexagon tile, now and then a pink one: pointy-topped hexagons in staggered rows, drawn at 4x with their
    grout and repeated across the edges so the block tiles."""
    k = 4
    W = S * k
    img = Image.new("RGBA", (W, W), (210, 204, 204, 255))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("hex"))
    w, h = 8, 8                      # cell pitch: 4 per row, 4 rows (each row of height 8)
    r = 4.55                         # circumradius in block px
    pink = {(1, 1), (3, 2)}
    for j in range(-1, 5):
        for i in range(-1, 5):
            cx = (i * w + (w / 2 if j % 2 else 0) + w / 2) * k
            cy = (j * h + h / 2) * k
            ii, jj = i % 4, j % 4
            c = HEX_PINK if (ii, jj) in pink else HEX_WHITE
            c = tuple(clamp(v + random.Random(ii * 7 + jj).uniform(-2, 2)) for v in c)
            pts = [(cx + (r - 0.3) * k * math.cos(math.radians(90 + 60 * t)), cy + (r - 0.3) * k * math.sin(math.radians(90 + 60 * t)) * 0.93) for t in range(6)]
            d.polygon(pts, fill=c + (255,))
    img = img.resize((S, S), Image.LANCZOS)
    return canvas_grain(img, "hexg", 1.2)


def subway_into(img, y0, y1):
    """White subway tile (8 x 4 px, half-bond) from row y0 to y1."""
    px = img.load()
    rng = random.Random(seed_of("subway"))
    for y in range(y0, y1):
        row = (y - y0) // 4
        off = 4 if row % 2 else 0
        for x in range(S):
            if (y - y0) % 4 == 0 or (x + off) % 8 == 0:
                px[x, y] = (214, 208, 208, 255)
            else:
                hi = 6 if (y - y0) % 4 == 1 else 0
                v = 246 + hi + rng.uniform(-1.5, 1.5)
                px[x, y] = (clamp(v), clamp(v - 2), clamp(v - 3), 255)


def backsplash():
    img = paint("paint-bs")
    subway_into(img, 12, 32)
    return img


def squaretile(base, grout, key):
    """Square glazed tile, 4 x 4 to a block."""
    img = flat(grout)
    px = img.load()
    rng = random.Random(seed_of(key))
    for ty in range(4):
        for tx in range(4):
            f = rng.uniform(0.985, 1.012)
            for y in range(ty * 8 + 1, ty * 8 + 8):
                for x in range(tx * 8 + 1, tx * 8 + 8):
                    k = f * (1.04 if (x % 8 == 1 or y % 8 == 1) else 1.0)
                    px[x, y] = tuple(clamp(v * k + rng.uniform(-1.2, 1.2)) for v in base) + (255,)
    return img


# ======================================================================== The window paintings (64 x 64, flat on purpose)

def canvas_grain(img, key, amount=3):
    rng = random.Random(seed_of(key))
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            d = rng.uniform(-amount, amount) + (1.2 if (x + y) % 3 == 0 else 0)
            px[x, y] = (clamp(r + d), clamp(g + d), clamp(b + d), a)
    return img


def sky_gradient(d, size, top, bottom, upto=1.0):
    for y in range(int(size * upto)):
        d.line([0, y, size, y], fill=mix(top, bottom, y / (size * upto)) + (255,))


def cloud(d, cx, cy, r, col, shade_col, k=1.0):
    """A puffy cartoon cloud: overlapping circles, a soft shaded underside."""
    blobs = [(-1.0, 0.3, 0.7), (-0.45, -0.2, 0.9), (0.2, -0.45, 1.05), (0.85, 0.0, 0.8), (1.35, 0.35, 0.55), (0.3, 0.35, 0.85)]
    for bx_, by_, br in blobs:
        rr = r * br
        d.ellipse([cx + bx_ * r - rr, cy + by_ * r - rr + r * 0.12, cx + bx_ * r + rr, cy + by_ * r + rr + r * 0.12], fill=shade_col + (255,))
    for bx_, by_, br in blobs:
        rr = r * br * 0.95
        d.ellipse([cx + bx_ * r - rr, cy + by_ * r - rr, cx + bx_ * r + rr, cy + by_ * r + rr], fill=col + (255,))


def painting(kind):
    N = 64
    img, d, k = big(N, 4)
    W = N * k
    if kind == "clouds":
        # The Wikidot photo: a clean sky blue and one towering white cumulus
        # (deep enough to read through the glass and the sheers: paler, the window looked frosted)
        sky_gradient(d, W, (64, 138, 224), (150, 198, 244))
        # The tower: stacked puffs, rising from the lower left
        for (cx, cy, r) in ((0.42, 0.72, 0.17), (0.6, 0.66, 0.15), (0.5, 0.5, 0.15), (0.58, 0.36, 0.12), (0.47, 0.24, 0.1), (0.3, 0.8, 0.12), (0.75, 0.8, 0.12)):
            cloud(d, cx * W, cy * W, r * W, (255, 255, 255), (172, 186, 220))
        cloud(d, 0.12 * W, 0.2 * W, 0.05 * W, (250, 252, 255), (196, 208, 234))
        cloud(d, 0.88 * W, 0.3 * W, 0.04 * W, (250, 252, 255), (196, 208, 234))
    elif kind == "hills":
        # (deep enough to read through the glass and the sheers, as the clouds' sky)
        sky_gradient(d, W, (84, 150, 228), (184, 204, 242))
        # A heart-shaped cloud
        hx, hy, hr = 0.68 * W, 0.24 * W, 0.075 * W
        d.ellipse([hx - 2 * hr, hy - hr, hx, hy + hr], fill=(255, 255, 255, 255))
        d.ellipse([hx, hy - hr, hx + 2 * hr, hy + hr], fill=(255, 255, 255, 255))
        d.polygon([(hx - 1.93 * hr, hy + 0.3 * hr), (hx + 1.93 * hr, hy + 0.3 * hr), (hx, hy + 2.3 * hr)], fill=(255, 255, 255, 255))
        cloud(d, 0.2 * W, 0.18 * W, 0.06 * W, (255, 255, 255), (200, 206, 236))
        # Rolling hills: pink behind, greens in front
        d.ellipse([-0.3 * W, 0.52 * W, 0.7 * W, 1.4 * W], fill=(244, 170, 190, 255))
        d.ellipse([0.35 * W, 0.56 * W, 1.4 * W, 1.5 * W], fill=(236, 150, 176, 255))
        d.ellipse([-0.5 * W, 0.7 * W, 0.6 * W, 1.6 * W], fill=(150, 214, 150, 255))
        d.ellipse([0.2 * W, 0.76 * W, 1.3 * W, 1.7 * W], fill=(128, 200, 136, 255))
        for i in range(14):
            rng = random.Random(i * 7 + 3)
            x, y = rng.uniform(0.05, 0.95) * W, rng.uniform(0.82, 0.97) * W
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=(255, 250, 252, 255))
    elif kind == "rainbow":
        sky_gradient(d, W, (166, 210, 246), (220, 236, 252))
        cx, cy = 0.5 * W, 0.86 * W
        bands = [(246, 160, 172), (250, 198, 150), (252, 236, 160), (180, 228, 170), (170, 206, 246), (206, 182, 240)]
        for i, c in enumerate(bands):
            r = (0.62 - i * 0.055) * W
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c + (255,))
        r = (0.62 - 6 * 0.055) * W
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(206, 228, 250, 255))
        cloud(d, 0.16 * W, 0.78 * W, 0.08 * W, (255, 255, 255), (228, 232, 246))
        cloud(d, 0.84 * W, 0.78 * W, 0.08 * W, (255, 255, 255), (228, 232, 246))
        # The flower field
        d.rectangle([0, 0.82 * W, W, W], fill=(150, 210, 140, 255))
        rng = random.Random(97)
        for _ in range(60):
            x, y = rng.uniform(0, W), rng.uniform(0.84 * W, W)
            c = rng.choice([(255, 255, 255), (250, 190, 210), (252, 236, 150), (220, 196, 246)])
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=c + (255,))
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=(250, 214, 110, 255))
    elif kind == "sunset":
        for y in range(W):
            t = y / W
            c = mix((250, 196, 168), (246, 160, 182), min(1, t * 1.4)) if t < 0.7 else mix((246, 160, 182), (196, 150, 196), (t - 0.7) / 0.3)
            d.line([0, y, W, y], fill=c + (255,))
        # A soft pink sun, low, with a glow round it
        sx, sy = 0.5 * W, 0.66 * W
        for i in range(6, 0, -1):
            r = 0.12 * W + i * 6
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=mix((250, 186, 186), (246, 168, 184), i / 6) + (255,))
        r = 0.12 * W
        d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(252, 128, 160, 255))
        # Banded clouds across the sun
        for (y, x0, x1) in ((0.6, 0.18, 0.62), (0.7, 0.42, 0.9), (0.46, 0.6, 0.86)):
            d.rounded_rectangle([x0 * W, y * W, x1 * W, (y + 0.035) * W], radius=0.017 * W, fill=(252, 214, 214, 255))
        # Hills, dusky
        d.ellipse([-0.4 * W, 0.78 * W, 0.7 * W, 1.5 * W], fill=(176, 120, 168, 255))
        d.ellipse([0.3 * W, 0.8 * W, 1.4 * W, 1.6 * W], fill=(150, 104, 154, 255))
        # One star
        star(d, 0.8 * W, 0.16 * W, 0.04 * W, (255, 250, 220))
    img = reduce(img, N)
    return canvas_grain(img, "paint" + kind, 2.5)


def star(d, cx, cy, r, col, inner=0.45, rot=-90):
    pts = []
    for i in range(10):
        a = math.radians(rot + i * 36)
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col + (255,))


def heart(d, cx, cy, r, col):
    d.ellipse([cx - 2 * r, cy - r, cx, cy + r], fill=col + (255,))
    d.ellipse([cx, cy - r, cx + 2 * r, cy + r], fill=col + (255,))
    d.polygon([(cx - 1.95 * r, cy + 0.25 * r), (cx + 1.95 * r, cy + 0.25 * r), (cx, cy + 2.35 * r)], fill=col + (255,))


def windows():
    for kind in ("clouds", "hills", "rainbow", "sunset"):
        img = painting(kind)
        # Quadrants as seen from the room: bl, br, tl, tr
        for name, (x0, y0) in {"tl": (0, 0), "tr": (32, 0), "bl": (0, 32), "br": (32, 32)}.items():
            save(img.crop((x0, y0, x0 + 32, y0 + 32)), f"painting-{kind}-{name}")
    # Glass: clear, with a few glints (cut out: only the glints are drawn)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for (x, y, l) in ((5, 4, 7), (8, 4, 4), (20, 18, 6), (23, 19, 3)):
        d.line([x, y + l, x + l, y], fill=(255, 255, 255, 200), width=1)
    save(img, "glass")
    # Sheer curtains: white with soft vertical folds
    img = flat((250, 248, 248))
    px = img.load()
    for x in range(S):
        k = 0.94 + 0.06 * math.cos(2 * math.pi * x / 5.33)
        for y in range(S):
            px[x, y] = tuple(clamp(v * k) for v in (252, 249, 249)) + (255,)
    save(img, "curtain")
    # A valance with a row of eyelet holes, and a cream ribbon
    img = flat((252, 250, 250))
    d = ImageDraw.Draw(img)
    for x in range(2, S, 6):
        for y in (6, 20):
            d.ellipse([x, y, x + 2, y + 2], fill=(236, 226, 228, 255))
    save(img, "valance")
    img = noisy(hexc(0xF6E7C8), 3, "ribbon")
    ImageDraw.Draw(img).line([0, 15, S, 15], fill=hexc(0xE9D3AA) + (255,), width=2)
    save(img, "ribbon")


# ======================================================================== Lights

def lights():
    # A downlight's lens: warm white, brightest in the middle, faintly pink at the rim
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 15.5, y - 15.5) / 16
            px[x, y] = mix((255, 252, 246), (255, 226, 232), min(1, r)) + (255,)
    save(img, "lens")
    save(noisy((214, 206, 206), 2, "lensoff"), "lens-off")
    # Fairy light bulbs, lit and dark
    for name, c in (("pink", (255, 150, 186)), ("butter", (255, 236, 150)), ("white", (255, 250, 240))):
        img = flat(c)
        ImageDraw.Draw(img).rectangle([4, 4, 12, 14], fill=mix(c, (255, 255, 255), 0.6) + (255,))
        save(img, f"bulb-{name}")
        save(flat(shade(c, 0.62)), f"bulb-{name}-off")
    save(flat((236, 236, 232)), "wire")
    # The night light: a soft white-blue cloud with a sleepy face
    img, d, k = big()
    d.rectangle([0, 0, S * k, S * k], fill=(236, 244, 255, 255))
    d.arc([9 * k, 13 * k, 13 * k, 16 * k], 0, 180, fill=(120, 130, 170, 255), width=k)
    d.arc([19 * k, 13 * k, 23 * k, 16 * k], 0, 180, fill=(120, 130, 170, 255), width=k)
    d.arc([14 * k, 17 * k, 18 * k, 20 * k], 0, 180, fill=(200, 130, 160, 255), width=k)
    d.ellipse([6 * k, 17 * k, 9 * k, 19 * k], fill=(250, 200, 220, 255))
    d.ellipse([23 * k, 17 * k, 26 * k, 19 * k], fill=(250, 200, 220, 255))
    save(reduce(img), "nightlight-face")
    save(flat((236, 244, 255)), "nightlight")
    save(flat((248, 246, 244)), "plug")


# ======================================================================== Soft things

def fabric(base, key, amount=4, weave=0.03):
    img = noisy(base, amount, key)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 2 == 0:
                r, g, b, a = px[x, y]
                px[x, y] = shade((r, g, b), 1 - weave) + (255,)
    return img


def fur(base, key, amount=7):
    """Short plush fur: per-pixel noise in little vertical tufts."""
    rng = random.Random(seed_of(key))
    img = noisy(base, amount * 0.5, key + "n")
    px = img.load()
    for _ in range(90):
        x, y = rng.randrange(S), rng.randrange(S - 1)
        c = shade(base, rng.uniform(0.9, 1.08))
        px[x, y] = c + (255,)
        px[x, y + 1] = c + (255,)
    return img


def duvet(kind):
    img, d, k = big(S, 4)
    W = S * k
    d.rectangle([0, 0, W, W], fill=PINK_LIGHT + (255,))
    rng = random.Random(seed_of("duvet" + kind))
    # A tiled motif: on a 4 x 4 staggered grid so the pattern tiles
    for j in range(4):
        for i in range(4):
            cx = (i * 8 + (4 if j % 2 else 0) + 4) * k
            cy = (j * 8 + 4) * k
            if kind == "hearts":
                heart(d, cx, cy - 1.0 * k, 1.35 * k, (250, 250, 252) if (i + j) % 2 else (232, 96, 128))
            elif kind == "strawberries":
                d.polygon([(cx - 2.2 * k, cy - 1.2 * k), (cx + 2.2 * k, cy - 1.2 * k), (cx, cy + 2.6 * k)], fill=STRAWBERRY + (255,))
                d.ellipse([cx - 2.2 * k, cy - 2.4 * k, cx + 2.2 * k, cy + 0.6 * k], fill=STRAWBERRY + (255,))
                d.polygon([(cx - 1.8 * k, cy - 1.8 * k), (cx + 1.8 * k, cy - 1.8 * k), (cx, cy - 0.6 * k)], fill=LEAF + (255,))
                for sx, sy in ((-0.8, -0.4), (0.8, -0.4), (0, 0.6), (-0.3, -1.0), (0.4, 1.4)):
                    d.point([cx + sx * k, cy + sy * k], fill=(255, 236, 160, 255))
            else:
                star(d, cx, cy, 2.4 * k, (255, 240, 170) if (i + j) % 2 else (255, 255, 255))
    img = reduce(img)
    return canvas_grain(img, "duvetg" + kind, 2)


def soft_things():
    for kind in ("hearts", "strawberries", "stars"):
        save(duvet(kind), f"duvet-{kind}")
    img = fabric((252, 250, 250), "pillow", 2)
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=PINK_LIGHT + (255,), width=2)
    save(img, "pillow")
    # The mattress side: white, quilted
    img = fabric((246, 244, 244), "mattress", 2)
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.line([x, 0, x, S], fill=(226, 222, 224, 255))
    d.line([0, 2, S, 2], fill=(232, 226, 228, 255))
    save(img, "mattress")
    # Plush fur in the pastel palette, and the four mascots' faces
    for name, c in (("grey", GREY_CAT), ("white", (250, 248, 246)), ("bear", BEAR), ("butter", BUTTER),
                    ("pink", PINK_LIGHT), ("mint", MINT), ("lilac", LILAC), ("sky", SKY)):
        save(fur(c, "fur" + name), f"fur-{name}")
    save(fur((236, 214, 186), "furmuzzle", 4), "fur-muzzle")
    save(fur((250, 196, 210), "furear", 3), "fur-earpink")
    save(fur(STRAWBERRY, "furberry", 5), "fur-berry")
    save(fur(LEAF, "furleaf", 5), "fur-leaf")
    for name, c in (("grey", GREY_CAT), ("white", (250, 248, 246)), ("bear", BEAR), ("butter", BUTTER),
                    ("pink", PINK_LIGHT), ("mint", MINT), ("lilac", LILAC), ("sky", SKY)):
        save(plush_face(c, "cat" if name in ("grey", "pink", "lilac") else "bunny" if name in ("white", "sky") else
                        "bear" if name in ("bear", "mint") else "star", name), f"face-{name}")
    # Pastel garments (the closet), cloth for the dresser's insides, the plush backpack's straps
    for name, c in PASTELS.items():
        img = fabric(c, "garment" + name, 3)
        if name in ("pink", "sky"):
            d = ImageDraw.Draw(img)
            for j in range(0, S, 6):
                for i in range(0, S, 6):
                    d.point([i + (3 if (j // 6) % 2 else 0), j + 2], fill=(255, 255, 255, 255))
        save(img, f"garment-{name}")
    save(fur((250, 246, 246), "catbedwhite", 4), "catbed-white")
    save(fur(PINK_LIGHT, "catbedpink", 4), "catbed-pink")
    save(fur(hexc(0xF49AB6), "fluffy", 9), "fluffy-pink")
    img = fabric(hexc(0xF4A3BA), "towel", 4)
    ImageDraw.Draw(img).rectangle([0, 22, S, 25], fill=(255, 255, 255, 255))
    save(img, "towel")
    save(fabric(hexc(0xE87FA0), "chairfabric", 4, 0.05), "chairfabric")
    img = fabric(PINK_LIGHT, "cushion", 3)
    d = ImageDraw.Draw(img)
    for j in range(4, S, 8):
        for i in range(4, S, 8):
            d.ellipse([i - 1, j - 1, i + 1, j + 1], fill=shade(PINK_LIGHT, 0.86) + (255,))
    save(img, "cushion")


def plush_face(base, kind, key):
    """A plush's face: the fur, two dot eyes, a blush, a nose or a little smile. Drawn for a square face."""
    img, d, k = big()
    W = S * k
    src = fur(base, "face" + key).resize((W, W), Image.NEAREST)
    img.paste(src, (0, 0))
    ey = 15 * k
    for ex in (10, 22):
        d.ellipse([(ex - 2.2) * k, ey - 2.4 * k, (ex + 2.2) * k, ey + 2.4 * k], fill=INK + (255,))
        d.ellipse([(ex - 1.2) * k, ey - 1.8 * k, (ex - 0.2) * k, ey - 0.6 * k], fill=(255, 255, 255, 255))
    for ex in (6.5, 25.5):
        d.ellipse([(ex - 2.6) * k, 20 * k, (ex + 2.6) * k, 23 * k], fill=BLUSH + (255,))
    if kind == "cat":
        d.polygon([(14.5 * k, 19 * k), (17.5 * k, 19 * k), (16 * k, 20.6 * k)], fill=(232, 120, 150, 255))
        d.arc([12.5 * k, 19.5 * k, 16 * k, 23 * k], 20, 160, fill=INK + (255,), width=k)
        d.arc([16 * k, 19.5 * k, 19.5 * k, 23 * k], 20, 160, fill=INK + (255,), width=k)
    elif kind == "bear":
        d.ellipse([11 * k, 18 * k, 21 * k, 26 * k], fill=(240, 220, 196, 255))
        d.ellipse([14.3 * k, 18.8 * k, 17.7 * k, 21 * k], fill=INK + (255,))
        d.line([16 * k, 21 * k, 16 * k, 23 * k], fill=INK + (255,), width=k)
    elif kind == "bunny":
        d.ellipse([14.8 * k, 19 * k, 17.2 * k, 20.6 * k], fill=(232, 120, 150, 255))
        d.arc([13.5 * k, 19.5 * k, 18.5 * k, 23.5 * k], 30, 150, fill=INK + (255,), width=k)
    else:
        d.arc([12 * k, 17 * k, 20 * k, 23 * k], 20, 160, fill=INK + (255,), width=k)
    return reduce(img)


# ======================================================================== Pictures: posters (original mascots), frames, rug

def poster(kind):
    img, d, k = big()
    W = S * k
    if kind == "cat":
        # A round grey cat in a pink heart
        d.rectangle([0, 0, W, W], fill=(255, 246, 240, 255))
        for j in range(0, S, 6):
            for i in range(0, S, 6):
                d.ellipse([(i + 1) * k, (j + 1) * k, (i + 2) * k, (j + 2) * k], fill=(250, 214, 222, 255))
        heart(d, 16 * k, 13 * k, 7.4 * k, (246, 150, 178))
        d.ellipse([8.5 * k, 9 * k, 23.5 * k, 23 * k], fill=GREY_CAT + (255,))
        d.polygon([(9.5 * k, 12 * k), (11 * k, 6.5 * k), (14.5 * k, 10 * k)], fill=GREY_CAT + (255,))
        d.polygon([(22.5 * k, 12 * k), (21 * k, 6.5 * k), (17.5 * k, 10 * k)], fill=GREY_CAT + (255,))
        d.polygon([(10.6 * k, 11 * k), (11.3 * k, 8.2 * k), (13 * k, 10 * k)], fill=(250, 196, 210, 255))
        d.polygon([(21.4 * k, 11 * k), (20.7 * k, 8.2 * k), (19 * k, 10 * k)], fill=(250, 196, 210, 255))
        for ex in (12.8, 19.2):
            d.ellipse([(ex - 1.1) * k, 14.5 * k, (ex + 1.1) * k, 17 * k], fill=INK + (255,))
        d.ellipse([9.8 * k, 17.5 * k, 12.4 * k, 19 * k], fill=BLUSH + (255,))
        d.ellipse([19.6 * k, 17.5 * k, 22.2 * k, 19 * k], fill=BLUSH + (255,))
        d.polygon([(15.2 * k, 17.2 * k), (16.8 * k, 17.2 * k), (16 * k, 18.2 * k)], fill=(232, 120, 150, 255))
        d.arc([13.8 * k, 17.6 * k, 16 * k, 19.8 * k], 20, 160, fill=INK + (255,), width=k)
        d.arc([16 * k, 17.6 * k, 18.2 * k, 19.8 * k], 20, 160, fill=INK + (255,), width=k)
    elif kind == "bunny":
        d.rectangle([0, 0, W, W], fill=MINT + (255,))
        for (x, y) in ((4, 5), (27, 8), (6, 26), (26, 27)):
            heart(d, x * k, y * k, 1.2 * k, (255, 255, 255))
        for ex in (12.5, 19.5):
            d.ellipse([(ex - 2) * k, 2 * k, (ex + 2) * k, 13 * k], fill=(255, 255, 255, 255))
            d.ellipse([(ex - 1) * k, 4 * k, (ex + 1) * k, 11 * k], fill=(250, 196, 210, 255))
        d.ellipse([9 * k, 10 * k, 23 * k, 22 * k], fill=(255, 255, 255, 255))
        d.ellipse([10 * k, 19 * k, 22 * k, 30 * k], fill=(255, 255, 255, 255))
        for ex in (13.4, 18.6):
            d.ellipse([(ex - 0.9) * k, 14.5 * k, (ex + 0.9) * k, 16.5 * k], fill=INK + (255,))
        d.ellipse([10.5 * k, 17 * k, 12.6 * k, 18.2 * k], fill=BLUSH + (255,))
        d.ellipse([19.4 * k, 17 * k, 21.5 * k, 18.2 * k], fill=BLUSH + (255,))
        d.ellipse([15.2 * k, 16.6 * k, 16.8 * k, 17.6 * k], fill=(232, 120, 150, 255))
        # The strawberry, held in both paws
        d.ellipse([12.5 * k, 20 * k, 19.5 * k, 26 * k], fill=STRAWBERRY + (255,))
        d.polygon([(12.6 * k, 23 * k), (19.4 * k, 23 * k), (16 * k, 28.5 * k)], fill=STRAWBERRY + (255,))
        d.polygon([(13.5 * k, 19.6 * k), (18.5 * k, 19.6 * k), (16 * k, 21.6 * k)], fill=LEAF + (255,))
        for sx, sy in ((14.5, 23), (17.5, 23), (16, 25.5), (15, 21.8), (17.2, 21.8)):
            d.point([sx * k, sy * k], fill=(255, 236, 160, 255))
        d.ellipse([10.5 * k, 21 * k, 13.5 * k, 24 * k], fill=(255, 255, 255, 255))
        d.ellipse([18.5 * k, 21 * k, 21.5 * k, 24 * k], fill=(255, 255, 255, 255))
    elif kind == "rainbow":
        d.rectangle([0, 0, W, W], fill=(214, 234, 252, 255))
        bands = [(246, 160, 172), (250, 198, 150), (252, 236, 160), (180, 228, 170), (170, 206, 246), (206, 182, 240)]
        for i, c in enumerate(bands):
            r = (13 - i * 1.4) * k
            d.ellipse([16 * k - r, 22 * k - r, 16 * k + r, 22 * k + r], fill=c + (255,))
        r = (13 - 6 * 1.4) * k
        d.ellipse([16 * k - r, 22 * k - r, 16 * k + r, 22 * k + r], fill=(214, 234, 252, 255))
        d.rectangle([0, 22 * k, W, W], fill=(214, 234, 252, 255))
        cloud(d, 5.5 * k, 22 * k, 3 * k, (255, 255, 255), (232, 236, 248))
        cloud(d, 26 * k, 22 * k, 3 * k, (255, 255, 255), (232, 236, 248))
        for (x, y) in ((6, 6), (25, 5), (28, 13)):
            star(d, x * k, y * k, 1.6 * k, (255, 240, 170))
    elif kind == "star":
        d.rectangle([0, 0, W, W], fill=LILAC + (255,))
        for (x, y, r) in ((5, 6, 1.2), (27, 6, 1.5), (5, 26, 1.4), (27, 27, 1.0), (16, 3, 0.9)):
            star(d, x * k, y * k, r * k, (255, 255, 255))
        star(d, 16 * k, 17 * k, 12 * k, (255, 230, 140), inner=0.5)
        star(d, 16 * k, 17 * k, 10.6 * k, BUTTER, inner=0.5)
        for ex in (13.5, 18.5):
            d.ellipse([(ex - 1) * k, 15 * k, (ex + 1) * k, 17.4 * k], fill=INK + (255,))
        d.arc([13.8 * k, 16.5 * k, 18.2 * k, 21 * k], 20, 160, fill=INK + (255,), width=k)
        d.ellipse([10.8 * k, 18.2 * k, 12.8 * k, 19.4 * k], fill=BLUSH + (255,))
        d.ellipse([19.2 * k, 18.2 * k, 21.2 * k, 19.4 * k], fill=BLUSH + (255,))
    elif kind == "toast":
        d.rectangle([0, 0, W, W], fill=PINK_LIGHT + (255,))
        for j in range(0, S, 8):
            for i in range(0, S, 8):
                d.ellipse([(i + 2) * k, (j + 2) * k, (i + 3) * k, (j + 3) * k], fill=(255, 255, 255, 255))
        # A slice of toast: a crust, a bread-shaped top, and a pat of butter
        d.rounded_rectangle([7 * k, 11 * k, 25 * k, 28 * k], radius=2 * k, fill=(206, 146, 86, 255))
        d.ellipse([6 * k, 5 * k, 16.5 * k, 15 * k], fill=(206, 146, 86, 255))
        d.ellipse([15.5 * k, 5 * k, 26 * k, 15 * k], fill=(206, 146, 86, 255))
        d.rounded_rectangle([8.5 * k, 12 * k, 23.5 * k, 26.5 * k], radius=1.5 * k, fill=(250, 226, 170, 255))
        d.ellipse([7.5 * k, 6.5 * k, 16 * k, 14.5 * k], fill=(250, 226, 170, 255))
        d.ellipse([16 * k, 6.5 * k, 24.5 * k, 14.5 * k], fill=(250, 226, 170, 255))
        d.rounded_rectangle([17 * k, 8 * k, 22 * k, 11.5 * k], radius=0.8 * k, fill=(255, 240, 150, 255))
        for ex in (13, 19):
            d.ellipse([(ex - 1) * k, 16 * k, (ex + 1) * k, 18.4 * k], fill=INK + (255,))
        d.arc([14 * k, 17 * k, 18 * k, 21 * k], 20, 160, fill=INK + (255,), width=k)
        d.ellipse([9.8 * k, 19 * k, 12 * k, 20.4 * k], fill=BLUSH + (255,))
        d.ellipse([20 * k, 19 * k, 22.2 * k, 20.4 * k], fill=BLUSH + (255,))
    elif kind == "frog":
        d.rectangle([0, 0, W, W], fill=BUTTER + (255,))
        for (x, y) in ((4, 26), (27, 25), (5, 6)):
            d.ellipse([(x - 1.5) * k, (y - 1.5) * k, (x + 1.5) * k, (y + 1.5) * k], fill=(255, 255, 255, 255))
        # The frog, round and green, with a red mushroom cap for a hat
        d.ellipse([8 * k, 13 * k, 24 * k, 28 * k], fill=(140, 204, 120, 255))
        d.ellipse([9 * k, 10 * k, 15 * k, 16 * k], fill=(140, 204, 120, 255))
        d.ellipse([17 * k, 10 * k, 23 * k, 16 * k], fill=(140, 204, 120, 255))
        for ex in (12, 20):
            d.ellipse([(ex - 1.8) * k, 11.2 * k, (ex + 1.8) * k, 14.8 * k], fill=(255, 255, 255, 255))
            d.ellipse([(ex - 0.9) * k, 12.2 * k, (ex + 0.9) * k, 14.2 * k], fill=INK + (255,))
        d.arc([12 * k, 16 * k, 20 * k, 22 * k], 20, 160, fill=INK + (255,), width=k)
        d.ellipse([9.6 * k, 18.6 * k, 12.4 * k, 20 * k], fill=BLUSH + (255,))
        d.ellipse([19.6 * k, 18.6 * k, 22.4 * k, 20 * k], fill=BLUSH + (255,))
        d.pieslice([7 * k, 1 * k, 25 * k, 17 * k], 180, 360, fill=(226, 70, 76, 255))
        d.rectangle([12.5 * k, 9 * k, 19.5 * k, 11.5 * k], fill=(250, 244, 230, 255))
        for (x, y, r) in ((11, 5.5, 1.3), (16, 3.6, 1.1), (20.5, 6, 1.4), (14, 7.5, 0.8)):
            d.ellipse([(x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k], fill=(255, 255, 255, 255))
    img = reduce(img)
    return canvas_grain(img, "poster" + kind, 1.5)


def pictures():
    for kind in ("cat", "bunny", "rainbow", "star", "toast", "frog"):
        save(poster(kind), f"poster-{kind}")
    save(flat((248, 240, 200), 210), "tape")
    save(noisy((214, 176, 92), 6, "gilt"), "gilt")
    save(noisy((216, 212, 212), 2, "mat"), "mat")
    save(noisy((238, 236, 234), 2, "matback"), "matback")
    # The heart rug: 64 x 64 drawn, split in quarters (0 NW, 1 NE, 2 SW, 3 SE); outside the heart is cut away
    img, d, k = big(64, 4)
    W = 64 * k
    heart(d, 32 * k, 22 * k, 15.5 * k, (255, 255, 255))
    heart(d, 32 * k, 23 * k, 13.6 * k, hexc(0xF29BB4))
    heart(d, 32 * k, 23.5 * k, 10.5 * k, hexc(0xF6B4C6))
    img = img.resize((64, 64), Image.LANCZOS)
    px = img.load()
    for y in range(64):
        for x in range(64):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a > 110 else 0)
    img = canvas_grain(img, "rug", 3)
    for i, (x0, y0) in enumerate(((0, 0), (32, 0), (0, 32), (32, 32))):
        save(img.crop((x0, y0, x0 + 32, y0 + 32)), f"rug-{i}")
    # The placemat: a white heart on pink check
    img, d, k = big()
    heart(d, 16 * k, 10 * k, 7.5 * k, (255, 255, 255))
    heart(d, 16 * k, 10.6 * k, 6.4 * k, (246, 170, 192))
    img = reduce(img)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a > 110 else 0)
    save(img, "placemat")
    # The heart pillow of the cat bed
    img, d, k = big()
    d.rectangle([0, 0, S * k, S * k], fill=(240, 108, 140, 255))
    heart(d, 16 * k, 13 * k, 5 * k, (255, 236, 242))
    save(reduce(img), "heartpillow")


# ======================================================================== Hard things

def hard_things():
    # Porcelain: white with a faint cool shading
    save(soft(noisy((246, 246, 246), 1.5, "porcelain"), "porcelainf", 3), "porcelain")
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            v = 200 + 34 * math.sin(math.pi * ((x + y * 0.3) % 32) / 32) ** 2
            px[x, y] = (clamp(v - 4), clamp(v), clamp(v + 6), 255)
    save(img, "chrome")
    save(noisy((176, 182, 190), 3, "steel"), "steel")
    save(noisy((226, 196, 104), 4, "brass"), "brass")
    # Pink enamel (the fridge and the stove): glossy, with a soft vertical highlight
    img = Image.new("RGBA", (S, S))
    px = img.load()
    base = hexc(0xF4A6BC)
    for y in range(S):
        for x in range(S):
            k = 1 + 0.05 * math.exp(-((x - 10) / 5) ** 2)
            px[x, y] = tuple(clamp(v * k) for v in base) + (255,)
    save(img, "enamel")
    save(noisy(hexc(0xE890A8), 3, "pinkwood"), "pinkwood")
    img = noisy(hexc(0xE58DA5), 2, "panel")
    save(img, "cupboard")
    save(noisy((250, 236, 240), 2, "knob"), "knob-white")
    save(noisy(hexc(0xEE7FA0), 4, "knobpink"), "knob-pink")
    # The countertop: white, faintly veined
    save(texlib.marble((248, 246, 244), (226, 220, 222), seed_of("counter"), veins=1, sharpness=7, mottle=0.02), "countertop")
    save(noisy((58, 58, 62), 4, "coil"), "coil")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        d.line([0, y, S, y], fill=mix((46, 34, 44), (90, 70, 84), y / S) + (255,))
    d.line([4, 26, 14, 8], fill=(120, 104, 116, 255), width=2)
    save(img, "ovenglass")
    # Mirror glass: pale blue-grey with a diagonal sheen
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / 64
            v = mix((206, 220, 230), (236, 244, 248), 0.5 + 0.5 * math.sin(t * 7))
            px[x, y] = v + (255,)
    save(img, "mirror")
    # A wooden spoon, a whisk's wire, canisters' labels
    save(noisy((222, 186, 132), 5, "spoonwood"), "spoonwood")
    for name, c in (("mint", MINT),):
        img = noisy(c, 2, "crock" + name)
        ImageDraw.Draw(img).rectangle([0, 6, S, 8], fill=(255, 255, 255, 255))
        save(img, f"crock-{name}")
    for i, (c, word) in enumerate(((MINT, "SUGAR"), (LILAC, "FLOUR"), (BUTTER, "TEA"))):
        img = noisy(c, 2, f"can{i}")
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([5, 10, 27, 22], radius=3, fill=(255, 255, 255, 255))
        heart(d, 16, 14.5, 2.4, (240, 128, 160))
        save(img, f"canister-{i}")
    # The old computer: beige plastic, a dark screen with a faintly pink-lit desktop, a keyboard
    save(noisy((232, 224, 204), 2, "beige"), "beige")
    img = Image.new("RGBA", (S, S), (46, 58, 76, 255))
    d = ImageDraw.Draw(img)
    for y in range(S):
        d.line([0, y, S, y], fill=mix((60, 78, 100), (44, 54, 72), y / S) + (255,))
    d.rectangle([0, 27, S, S], fill=(176, 172, 178, 255))
    d.rectangle([1, 28, 7, 30], fill=(232, 160, 184, 255))
    for i, y in enumerate((3, 9, 15)):
        d.rectangle([2, y, 5, y + 3], fill=[(250, 220, 120), (170, 210, 246), (246, 170, 196)][i] + (255,))
    d.rectangle([10, 6, 28, 22], fill=(244, 188, 206, 255))
    d.rectangle([10, 6, 28, 8], fill=(214, 120, 160, 255))
    d.rectangle([12, 10, 26, 20], fill=(255, 246, 248, 255))
    heart(d, 19, 13.5, 2.2, (240, 128, 160))
    for y in range(0, S, 2):
        d.line([0, y, S, y], fill=(0, 0, 0, 30))
    save(img, "screen")
    # Little things: a water bottle, vitamins, a lamp shade (glows), lamp ceramic, the clock face, the duck
    img = Image.new("RGBA", (S, S), (176, 216, 240, 255))
    ImageDraw.Draw(img).rectangle([0, 10, S, 22], fill=(255, 255, 255, 255))
    save(img, "bottle")
    img = flat((250, 250, 248))
    ImageDraw.Draw(img).rectangle([0, 12, S, 22], fill=MINT + (255,))
    save(img, "vitamins")
    img = fabric(hexc(0xF7A6BE), "shade", 2)
    d = ImageDraw.Draw(img)
    d.line([0, 1, S, 1], fill=(255, 255, 255, 255), width=2)
    d.line([0, 30, S, 30], fill=(255, 255, 255, 255), width=2)
    save(img, "lampshade")
    save(noisy((250, 246, 240), 2, "ceramic"), "ceramic")
    img, d, k = big()
    d.ellipse([0, 0, S * k - 1, S * k - 1], fill=(255, 255, 255, 255))
    for i in range(12):
        a = math.radians(i * 30)
        r0, r1 = (12.5 if i % 3 else 11) * k, 14 * k
        d.line([16 * k + r0 * math.cos(a), 16 * k + r0 * math.sin(a), 16 * k + r1 * math.cos(a), 16 * k + r1 * math.sin(a)], fill=INK + (255,), width=k)
    d.line([16 * k, 16 * k, 16 * k, 7 * k], fill=INK + (255,), width=2 * k)
    d.line([16 * k, 16 * k, 22 * k, 19 * k], fill=INK + (255,), width=2 * k)
    heart(d, 16 * k, 22 * k, 1.4 * k, (240, 128, 160))
    save(reduce(img), "clockface")
    img, d, k = big()
    d.rectangle([0, 0, S * k, S * k], fill=CHECK_PINK + (255,))
    for ex in (10, 22):
        d.ellipse([(ex - 2.5) * k, 12 * k, (ex + 2.5) * k, 19 * k], fill=(255, 255, 255, 255))
        d.ellipse([(ex - 1.3) * k, 13.5 * k, (ex + 1.3) * k, 18 * k], fill=INK + (255,))
    d.polygon([(14.5 * k, 21 * k), (17.5 * k, 21 * k), (16 * k, 23 * k)], fill=(232, 110, 140, 255))
    save(reduce(img), "catclock-face")
    save(noisy(CHECK_PINK, 2, "catclock"), "catclock")
    save(noisy((255, 214, 72), 3, "duck"), "duck")
    save(flat((246, 140, 50)), "beak")
    save(flat(INK), "ink")
    save(noisy((236, 232, 228), 2, "pedestal"), "pedestal")
    # Boxed figures on a shelf: pastel boxes with a clear window and a little figure inside
    for i, c in enumerate((LILAC, MINT, SKY)):
        img, d, k = big()
        d.rectangle([0, 0, S * k, S * k], fill=c + (255,))
        d.rectangle([5 * k, 6 * k, 27 * k, 27 * k], fill=(236, 244, 250, 255))
        fc = [(246, 170, 196), BUTTER, (255, 255, 255)][i]
        d.ellipse([10 * k, 9 * k, 22 * k, 19 * k], fill=fc + (255,))
        d.ellipse([11 * k, 17 * k, 21 * k, 26 * k], fill=fc + (255,))
        for ex in (13.5, 18.5):
            d.ellipse([(ex - 0.9) * k, 13 * k, (ex + 0.9) * k, 15 * k], fill=INK + (255,))
        d.rectangle([0, 0, S * k, 4 * k], fill=(255, 255, 255, 255))
        heart(d, 16 * k, 1.5 * k, 1.1 * k, (240, 128, 160))
        save(reduce(img), f"figbox-{i}")
        save(noisy(c, 2, f"figside{i}"), f"figbox-side-{i}")
    # Flowers and their stems, a glass vase
    save(flat((246, 140, 176)), "petal")
    save(flat((255, 238, 160)), "petalheart")
    save(flat((112, 176, 100)), "stem")
    save(flat((214, 236, 240), 255), "vase")


# ======================================================================== Items (sprites)

def items():
    # Greasy Marshmallows: a glossy paper bag, pink and white stripes, marshmallows peeking out
    img, d, k = big()
    d.polygon([(7 * k, 9 * k), (25 * k, 9 * k), (27 * k, 30 * k), (5 * k, 30 * k)], fill=(255, 255, 255, 255))
    for i in range(5):
        x = 7 + i * 4
        d.polygon([(x * k, 9 * k), ((x + 2) * k, 9 * k), ((x + 2.4) * k, 30 * k), ((x - 0.2) * k, 30 * k)], fill=(246, 160, 186, 255))
    for (x, y) in ((10, 7), (15, 5), (20, 7)):
        d.rounded_rectangle([(x - 3) * k, (y - 2.5) * k, (x + 3) * k, (y + 2.5) * k], radius=1.5 * k, fill=(255, 250, 244, 255), outline=(230, 214, 210, 255), width=k // 2)
    d.rounded_rectangle([9 * k, 16 * k, 23 * k, 24 * k], radius=2 * k, fill=(255, 255, 255, 255))
    heart(d, 16 * k, 19 * k, 2.2 * k, (240, 110, 150))
    d.line([8 * k, 11 * k, 9 * k, 28 * k], fill=(255, 255, 255, 160), width=k)
    save_item(reduce(img), "marshmallow")
    # Pastel candy: three wrapped sweets
    img, d, k = big()
    for (x, y, c) in ((11, 11, MINT), (21, 14, LILAC), (14, 22, BUTTER)):
        d.polygon([((x - 9) * k, (y - 3) * k), ((x - 4) * k, y * k), ((x - 9) * k, (y + 3) * k)], fill=c + (255,))
        d.polygon([((x + 9) * k, (y - 3) * k), ((x + 4) * k, y * k), ((x + 9) * k, (y + 3) * k)], fill=c + (255,))
        d.ellipse([(x - 5) * k, (y - 4) * k, (x + 5) * k, (y + 4) * k], fill=shade(c, 0.94) + (255,))
        d.arc([(x - 3.5) * k, (y - 3) * k, (x + 1) * k, (y + 1) * k], 180, 270, fill=(255, 255, 255, 255), width=k)
    save_item(reduce(img), "candy")
    # Strawberry milk: a little carton
    img, d, k = big()
    d.polygon([(9 * k, 10 * k), (16 * k, 4 * k), (23 * k, 10 * k)], fill=(255, 236, 242, 255))
    d.rectangle([14 * k, 2 * k, 18 * k, 5 * k], fill=(255, 236, 242, 255))
    d.rectangle([9 * k, 10 * k, 23 * k, 30 * k], fill=(246, 150, 180, 255))
    d.rectangle([9 * k, 10 * k, 23 * k, 13 * k], fill=(255, 255, 255, 255))
    d.ellipse([12 * k, 16 * k, 20 * k, 23 * k], fill=STRAWBERRY + (255,))
    d.polygon([(12.4 * k, 20 * k), (19.6 * k, 20 * k), (16 * k, 27 * k)], fill=STRAWBERRY + (255,))
    d.polygon([(13 * k, 16 * k), (19 * k, 16 * k), (16 * k, 18.5 * k)], fill=LEAF + (255,))
    save_item(reduce(img), "strawberrymilk")
    # Remembered meals
    def plate(d, k):
        d.ellipse([2 * k, 14 * k, 30 * k, 30 * k], fill=(244, 244, 244, 255))
        d.ellipse([6 * k, 16.5 * k, 26 * k, 27.5 * k], fill=(252, 252, 252, 255))
        d.arc([2 * k, 14 * k, 30 * k, 30 * k], 20, 160, fill=(246, 170, 192, 255), width=k)

    img, d, k = big()
    plate(d, k)
    for i in range(4):
        y = 22 - i * 3
        d.ellipse([7 * k, (y - 3) * k, 25 * k, (y + 3) * k], fill=(214, 156, 84, 255))
        d.ellipse([7.5 * k, (y - 3.4) * k, 24.5 * k, (y + 1.6) * k], fill=(236, 192, 120, 255))
    d.rounded_rectangle([13 * k, 7 * k, 19 * k, 10 * k], radius=k, fill=(255, 240, 150, 255))
    d.line([10 * k, 10 * k, 12 * k, 20 * k], fill=(160, 90, 30, 200), width=k)
    save_item(reduce(img), "meal-pancakes")
    img, d, k = big()
    d.pieslice([3 * k, 6 * k, 29 * k, 30 * k], 0, 180, fill=(250, 250, 250, 255))
    d.ellipse([3 * k, 13 * k, 29 * k, 21 * k], fill=(236, 196, 110, 255))
    for (x, y, c) in ((10, 16, (240, 150, 70)), (17, 15, (250, 250, 240)), (21, 17, (120, 180, 90)), (13, 18, (250, 250, 240))):
        d.rectangle([x * k, y * k, (x + 2) * k, (y + 1.5) * k], fill=c + (255,))
    d.arc([3 * k, 6 * k, 29 * k, 30 * k], 30, 150, fill=(246, 170, 192, 255), width=k)
    save_item(reduce(img), "meal-soup")
    img, d, k = big()
    plate(d, k)
    rng = random.Random(5)
    for _ in range(26):
        x, y = rng.uniform(9, 23), rng.uniform(15, 25)
        d.arc([(x - 2) * k, (y - 1.4) * k, (x + 2) * k, (y + 1.4) * k], rng.randint(0, 90), rng.randint(200, 330), fill=(250, 200, 80, 255), width=int(1.4 * k))
    save_item(reduce(img), "meal-macaroni")


def generate():
    for i in (1, 2):
        save(paint(f"paint-{i}"), f"paint-{i}")
    save(trim(), "trim")
    save(ceiling(), "ceiling")
    save(carpet("carpet"), "carpet")
    save(checker(), "checker")
    save(bathhex(), "bathhex")
    save(backsplash(), "backsplash")
    save(squaretile(MINT, (246, 242, 236), "bathtile"), "bathtile")
    windows()
    lights()
    soft_things()
    pictures()
    hard_things()
    items()
    import gen_974_b16  # graphics pass B16: its painters run last, under the same keys (and new version keys)
    gen_974_b16.textures()
