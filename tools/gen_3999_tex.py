"""Level 3999, the Neon Paradise: textures of the building, its fittings and its items (block/3999/, item/3999/).
The arcade machines' art is in gen_3999_tex_arcade.py. Called from gen_3999.py.

Palette: the level's six neons (cyan #64E8F7, blue #4567ED, violet #D13BF7, hot pink #FF2A5A, orange #FF4A00, pink
glow #FFA0FF) over black-light carpet, marble, plum and midnight paint. Pictures are drawn large and scaled down so
they stay soft at 32 px; pixel-art screens are drawn at their own size.
"""
import math
import os
import random
import zlib

from PIL import Image, ImageDraw, ImageFilter

import texlib
from gen_3999_kit import ASSETS, COLOURS, F3, F5, NEON, centred, draw_text, text_width

TEX = os.path.join(ASSETS, "textures")
S = 32


def seed_of(name):
    return zlib.crc32(name.encode()) & 0xFFFFFF


def clamp(v):
    return max(0, min(255, int(round(v))))


def hexc(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def rgba(c, a=255):
    return (c[0], c[1], c[2], a)


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    return tuple(clamp(v * k) for v in c[:3])


def save(img, name):
    path = os.path.join(TEX, "block", "3999", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def save_item(img, name):
    path = os.path.join(TEX, "item", "3999", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def noisy(c, amt, key, w=S, h=S, alpha=255):
    rng = random.Random(seed_of(key))
    img = Image.new("RGBA", (w, h))
    px = img.load()
    for y in range(h):
        for x in range(w):
            n = rng.uniform(-amt, amt)
            px[x, y] = (clamp(c[0] + n), clamp(c[1] + n), clamp(c[2] + n), alpha)
    return img


def flat(name, c, amt=5, w=S, h=S, alpha=255):
    img = noisy(c, amt, name, w, h, alpha)
    save(img, name)
    return img


def soft_noise(img, key, amt):
    """Low-frequency mottling (seamless)."""
    field = texlib._periodic_noise(seed_of(key), 3)
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            n = amt * field[y % S][x % S]
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), a)
    return img


def wrapped(size, k, draw_fn, bg=(0, 0, 0, 0)):
    """Draws at k times the size with every shape repeated across the edges, then scales down: seamless and soft."""
    big = Image.new("RGBA", (size * k, size * k), bg)
    d = ImageDraw.Draw(big)
    for ox in (-size * k, 0, size * k):
        for oy in (-size * k, 0, size * k):
            draw_fn(d, ox, oy, k)
    return big.resize((size, size), Image.LANCZOS)


def neon_core(c):
    """The colour of a lit tube's core: the hue run toward white."""
    return mix(c, (255, 255, 255), 0.45)


# ======================================================================== Floors, walls, ceilings

def carpets():
    cols = [NEON[c][0] for c in COLOURS]
    rng = random.Random(3999)
    shapes = []
    for i in range(30):
        shapes.append((rng.choice(["squiggle", "tri", "ring", "zig", "dot", "dot", "bolt"]), rng.uniform(0, 32), rng.uniform(0, 32),
                       rng.uniform(3, 8), rng.choice(cols), rng.uniform(0, math.tau)))

    def cosmic_shapes(d, ox, oy, k):
        for kind, x, y, sz, col, a in shapes:
            X, Y, R = x * k + ox, y * k + oy, sz * k / 2
            w = max(1, int(k * 0.9))
            c = rgba(col)
            if kind == "dot":
                d.ellipse([X - k * 0.8, Y - k * 0.8, X + k * 0.8, Y + k * 0.8], fill=c)
            elif kind == "ring":
                d.ellipse([X - R, Y - R, X + R, Y + R], outline=c, width=w)
            elif kind == "tri":
                pts = [(X + R * math.cos(a + j * math.tau / 3), Y + R * math.sin(a + j * math.tau / 3)) for j in range(3)]
                d.polygon(pts, outline=c, width=w)
            elif kind == "zig":
                pts = [(X - R + j * R / 2, Y + (R / 2 if j % 2 else -R / 2)) for j in range(5)]
                d.line(pts, fill=c, width=w)
            elif kind == "bolt":
                d.line([(X - R, Y - R), (X, Y - R * 0.2), (X - R * 0.3, Y + R * 0.2), (X + R, Y + R)], fill=c, width=w)
            else:  # squiggle
                pts = [(X - R + j * R / 4, Y + R * 0.5 * math.sin(a + j * 1.3)) for j in range(9)]
                d.line(pts, fill=c, width=w)

    def fibre(img, key, amt):
        rng2 = random.Random(seed_of(key))
        px = img.load()
        for y in range(S):
            for x in range(S):
                r, g, b, a = px[x, y]
                n = rng2.uniform(-amt, amt)
                px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), 255)
        return img

    base = Image.new("RGBA", (S, S), rgba(hexc(0x0B0618)))
    layer = wrapped(S, 6, cosmic_shapes)
    layer = layer.filter(ImageFilter.GaussianBlur(0.35))
    cosmic = base.copy()
    cosmic.alpha_composite(layer)
    fibre(cosmic, "carpet-cosmic", 7)
    save(cosmic, "carpet-cosmic")

    # Galaxy: deep violet, stars, two ringed planets, swirls
    def galaxy_shapes(d, ox, oy, k):
        r2 = random.Random(77)
        for _ in range(4):
            cx, cy, rad = r2.uniform(0, 32), r2.uniform(0, 32), r2.uniform(5, 10)
            for j in range(40):
                t = j / 40
                a = t * 4.5 + r2.uniform(0, 0.1)
                x, y = cx + rad * t * math.cos(a), cy + rad * t * math.sin(a)
                d.ellipse([x * k + ox - k * 0.6, y * k + oy - k * 0.6, x * k + ox + k * 0.6, y * k + oy + k * 0.6], fill=(120, 60, 190, 90))
        for (px_, py_, rad, col) in ((8, 9, 2.6, (100, 230, 247)), (23, 22, 2.0, (255, 140, 60))):
            X, Y = px_ * k + ox, py_ * k + oy
            d.ellipse([X - rad * k, Y - rad * k, X + rad * k, Y + rad * k], fill=rgba(col))
            d.ellipse([X - rad * 2.0 * k, Y - rad * 0.6 * k, X + rad * 2.0 * k, Y + rad * 0.6 * k], outline=(230, 200, 255, 230), width=max(1, k // 2))
        for _ in range(26):
            x, y = r2.uniform(0, 32), r2.uniform(0, 32)
            c = r2.choice([(255, 255, 255), (255, 200, 255), (180, 240, 255)])
            d.rectangle([x * k + ox, y * k + oy, x * k + ox + k - 1, y * k + oy + k - 1], fill=rgba(c))

    gal = Image.new("RGBA", (S, S), rgba(hexc(0x160A2E)))
    gal.alpha_composite(wrapped(S, 6, galaxy_shapes))
    fibre(gal, "carpet-galaxy", 6)
    save(gal, "carpet-galaxy")

    # Rotten: the cosmic carpet faded, darker, damp blotches and grime
    rot = cosmic.copy()
    px = rot.load()
    rng3 = random.Random(5)
    blotches = [(rng3.uniform(0, 32), rng3.uniform(0, 32), rng3.uniform(4, 9)) for _ in range(5)]
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            grey = (r + g + b) / 3
            r, g, b = (grey + (r - grey) * 0.4) * 0.7, (grey + (g - grey) * 0.4) * 0.7, (grey + (b - grey) * 0.4) * 0.7
            for bx_, by_, rad in blotches:
                for dx in (-32, 0, 32):
                    for dy in (-32, 0, 32):
                        dd = math.hypot(x - bx_ - dx, y - by_ - dy) / rad
                        if dd < 1:
                            t = (1 - dd) * 0.75
                            r, g, b = r + (0x2E - r) * t, g + (0x3A - g) * t, b + (0x26 - b) * t
            n = rng3.uniform(-6, 6)
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), 255)
    save(rot, "carpet-rotten")


def marbles():
    for name, base, vein, joint in (("marble-white", (0xE9, 0xE6, 0xEE), (150, 146, 160), (200, 196, 206)),
                                    ("marble-black", (0x14, 0x10, 0x18), (214, 190, 130), (40, 34, 44))):
        img = texlib.marble(base, vein, seed_of(name), veins=1, sharpness=6.0, mottle=0.05)
        d = ImageDraw.Draw(img)
        for k in (0, 16):
            d.line([0, k, S - 1, k], fill=rgba(joint))
            d.line([k, 0, k, S - 1], fill=rgba(joint))
        # A faint gloss band, diagonal
        px = img.load()
        for y in range(S):
            for x in range(S):
                t = math.exp(-((x - y - 6) % 32 - 16) ** 2 / 18)
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r + 16 * t), clamp(g + 16 * t), clamp(b + 18 * t), 255)
        save(img, name)


def concretes():
    img = noisy((0x9A, 0x97, 0x9E), 4, "concrete-wall")
    soft_noise(img, "cw", 6)
    d = ImageDraw.Draw(img)
    d.line([0, 15, S - 1, 15], fill=(140, 137, 145, 255))
    for x, y in ((8, 7), (24, 7), (8, 23), (24, 23)):
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(108, 104, 112, 255))
        img.putpixel((x, y), (82, 80, 86, 255))
    save(img, "concrete-wall")
    img = noisy((0x7D, 0x7A, 0x80), 5, "concrete-floor")
    soft_noise(img, "cf", 10)
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = math.exp(-((x + y) % 32 - 12) ** 2 / 30)
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r + 10 * t), clamp(g + 10 * t), clamp(b + 12 * t), 255)
    save(img, "concrete-floor")


def walls():
    for name, c in (("wall-violet", 0x3B1E5A), ("wall-midnight", 0x12122A), ("wall-teal", 0x0E3A44)):
        img = noisy(hexc(c), 2, name)
        rng = random.Random(seed_of(name))
        px = img.load()
        for x in range(S):  # roller streaks: faint vertical bands
            k = rng.uniform(-3, 3)
            for y in range(S):
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r + k), clamp(g + k), clamp(b + k), 255)
        soft_noise(img, name + "s", 3)
        save(img, name)


def ceilings():
    img = noisy((0x0A, 0x0A, 0x10), 2, "ceiling-black")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 0, 11, S - 1], fill=(16, 16, 22, 255))      # a duct's shadow
    d.line([4, 0, 4, S - 1], fill=(22, 22, 30, 255))
    d.rectangle([0, 22, S - 1, 24], fill=(14, 14, 20, 255))
    save(img, "ceiling-black")
    img = noisy((0x4A, 0x4A, 0x50), 4, "ceiling-acoustic")
    rng = random.Random(9)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if rng.random() < 0.08:
                px[x, y] = (54, 54, 60, 255)
    d = ImageDraw.Draw(img)
    for k in (0, 16):
        d.line([0, k, S - 1, k], fill=(84, 84, 90, 255))
        d.line([k, 0, k, S - 1], fill=(84, 84, 90, 255))
    save(img, "ceiling-acoustic")


def lanewood():
    for name, seed in (("lanewood", 1), ("lanewood2", 2)):
        rng = random.Random(seed)
        img = Image.new("RGBA", (S, S))
        px = img.load()
        boards = [rng.uniform(0.9, 1.08) for _ in range(16)]
        for y in range(S):
            for x in range(S):
                b = boards[x // 2]
                base = (222 * b, 182 * b, 128 * b)
                n = rng.uniform(-6, 6) + 5 * math.sin(y * 0.6 + x * 3 + seed)
                c = [clamp(base[i] + n) for i in range(3)]
                if x % 2 == 1 and rng.random() < 0.5:
                    c = [clamp(v - 14) for v in c]
                px[x, y] = tuple(c) + (255,)
        # Gloss: a soft light band
        for y in range(S):
            for x in range(S):
                t = math.exp(-((y - 10) % 32 - 16) ** 2 / 40) * 0.5
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r + 26 * t), clamp(g + 24 * t), clamp(b + 20 * t), 255)
        save(img, name)


def asphalts():
    def base(name):
        img = noisy((0x2A, 0x2A, 0x2C), 9, name)
        rng = random.Random(seed_of(name))
        px = img.load()
        for _ in range(40):
            x, y = rng.randrange(S), rng.randrange(S)
            px[x, y] = (70, 70, 72, 255)
        if "plain" in name:
            for y in range(S):
                for x in range(S):
                    d = math.hypot(x - 20, y - 12) / 6
                    if d < 1:
                        r, g, b, a = px[x, y]
                        px[x, y] = (clamp(r * 0.7 + 4), clamp(g * 0.7), clamp(b * 0.7 + 8), 255)
        return img
    white = (214, 212, 200, 255)
    save(base("asphalt-plain"), "asphalt-plain")
    img = base("asphalt-line-ns")
    ImageDraw.Draw(img).rectangle([15, 0, 16, S - 1], fill=white)
    save(img, "asphalt-line-ns")
    img = base("asphalt-line-we")
    ImageDraw.Draw(img).rectangle([0, 15, S - 1, 16], fill=white)
    save(img, "asphalt-line-we")
    img = base("asphalt-line-end")
    d = ImageDraw.Draw(img)
    d.rectangle([15, 15, 16, S - 1], fill=white)
    d.rectangle([9, 15, 22, 16], fill=white)
    save(img, "asphalt-line-end")
    flat("curb", (150, 148, 142), 7)


def mosaic(tile, grout, key, glow=False):
    rng = random.Random(seed_of(key))
    img = Image.new("RGBA", (S, S), grout + (255,))
    px = img.load()
    for ty in range(8):
        for tx in range(8):
            f = rng.uniform(0.94, 1.06)
            base = tuple(min(255, int(c * f)) for c in tile)
            for y in range(ty * 4 + 1, ty * 4 + 4):
                for x in range(tx * 4 + 1, tx * 4 + 4):
                    c = list(base)
                    if y == ty * 4 + 1 or x == tx * 4 + 1:
                        c = [min(255, v + (24 if glow else 12)) for v in c]
                    n = rng.uniform(-3, 3)
                    px[x, y] = (clamp(c[0] + n), clamp(c[1] + n), clamp(c[2] + n), 255)
    return img


def pools():
    save(mosaic((0x5A, 0x2D, 0x8C), (0x3A, 0x1C, 0x5C), "pooltile-violet"), "pooltile-violet")
    save(mosaic((0xB4, 0x8C, 0xE0), (0x8C, 0x6A, 0xB0), "pooltile-lilac"), "pooltile-lilac")
    img = noisy((240, 238, 242), 3, "pooltile-edge")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 3], fill=(252, 252, 255, 255))
    d.rectangle([0, 10, S - 1, 13], fill=(30, 18, 44, 255))       # the LED groove
    d.line([0, 14, S - 1, 14], fill=(200, 196, 206, 255))
    for x in range(0, S, 8):
        d.line([x, 15, x, S - 1], fill=(214, 210, 220, 255))
    save(img, "pooltile-edge")
    save(mosaic((0xFF, 0x3B, 0xD5), (0xB0, 0x20, 0x90), "magentatile", glow=True), "magentatile")
    flat("led-violet", neon_core(NEON["magenta"][0]), 4)
    flat("grate", (120, 124, 128), 6)
    flat("drainhole", (8, 8, 10), 2)


def facades():
    img = noisy((0xC9, 0xB4, 0x8E), 8, "facade-stucco")
    soft_noise(img, "stucco", 8)
    save(img, "facade-stucco")
    img = Image.new("RGBA", (S, S), (150, 140, 130, 255))
    rng = random.Random(4)
    d = ImageDraw.Draw(img)
    for row in range(8):
        off = 4 if row % 2 else 0
        for col in range(-1, 5):
            x0 = col * 8 + off
            c = (clamp(128 + rng.uniform(-18, 14)), clamp(56 + rng.uniform(-10, 10)), clamp(42 + rng.uniform(-8, 8)), 255)
            d.rectangle([x0, row * 4, x0 + 6, row * 4 + 2], fill=c)
    save(img, "facade-brick")
    img = noisy((0x24, 0x22, 0x28), 3, "facade-band")
    d = ImageDraw.Draw(img)
    d.line([0, 2, S - 1, 2], fill=(60, 58, 64, 255))
    d.line([0, 29, S - 1, 29], fill=(60, 58, 64, 255))
    save(img, "facade-band")


def window_painting():
    """One 128x96 painting, cut into 4 x 3 tiles: a car park at night seen through glass."""
    K = 4
    W, H = 128 * K, 96 * K
    img = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(img)
    hor = int(H * 0.42)
    for y in range(hor):           # sky: deep navy to a faint orange glow at the horizon
        t = y / hor
        c = mix((8, 10, 30), (52, 36, 60), t ** 2.2)
        d.line([0, y, W, y], fill=rgba(c))
    rng = random.Random(42)
    for _ in range(22):
        x, y = rng.uniform(0, W), rng.uniform(0, hor * 0.7)
        d.ellipse([x, y, x + K * 0.7, y + K * 0.7], fill=(230, 230, 255, 255))
    # Distant town: a dark band with lit windows
    for i in range(30):
        x0 = rng.uniform(-10, W)
        bw, bh = rng.uniform(20, 70), rng.uniform(8, 40)
        d.rectangle([x0, hor - bh, x0 + bw, hor], fill=(18, 16, 26, 255))
        for _ in range(int(bw * bh / 120)):
            wx, wy = rng.uniform(x0 + 2, x0 + bw - 4), rng.uniform(hor - bh + 2, hor - 4)
            d.rectangle([wx, wy, wx + 3, wy + 3], fill=rgba(rng.choice([(255, 210, 120), (255, 230, 170), (200, 220, 255)])))
    # The car park: asphalt in perspective, bay lines, a road along the back
    for y in range(hor, H):
        t = (y - hor) / (H - hor)
        d.line([0, y, W, y], fill=rgba(mix((22, 22, 26), (40, 38, 40), t)))
    d.rectangle([0, hor + 6, W, hor + 22], fill=(30, 30, 34, 255))
    for x in range(0, W, 60):
        d.rectangle([x, hor + 13, x + 28, hor + 15], fill=(190, 170, 90, 255))
    vx = W / 2
    # Two rows of bays: a line along the back of each row, short dividers in perspective
    for (y0, y1, spread) in ((hor + 40, hor + 78, 0.35), (hor + 150, hor + 230, 1.0)):
        d.line([(0, y0), (W, y0)], fill=(190, 188, 180, 255), width=2 if spread < 0.5 else 3)
        for i in range(-12, 13):
            xa = vx + i * 64 * (0.55 + 0.45 * spread)
            xb = vx + i * 64 * (0.55 + 0.45 * spread) * (1 + 0.25 * spread)
            d.line([(xa, y0), (xb, y1)], fill=(190, 188, 180, 255), width=2 if spread < 0.5 else 3)
    # Sodium lamps: poles and pools of orange light
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for lx in (70, 260, 450):
        top = hor - 70
        d.rectangle([lx - 2, top, lx + 2, hor + 60], fill=(40, 40, 44, 255))
        d.line([(lx, top), (lx + 30, top - 6)], fill=(40, 40, 44, 255), width=4)
        for r in range(90, 0, -6):
            a = int(60 * (1 - r / 90))
            gd.ellipse([lx + 30 - r * 1.6, hor + 70 - r * 0.5, lx + 30 + r * 1.6, hor + 70 + r * 0.5], fill=(255, 150, 40, a))
        gd.ellipse([lx + 24, top - 10, lx + 36, top], fill=(255, 210, 120, 255))
        for r in range(26, 0, -3):
            gd.ellipse([lx + 30 - r, top - 5 - r, lx + 30 + r, top - 5 + r], fill=(255, 170, 60, int(40 * (1 - r / 26))))
    img.alpha_composite(glow)
    # Five parked cars: boxy silhouettes with a sheen
    car_cols = [(120, 30, 40), (40, 60, 110), (180, 180, 186), (30, 30, 34), (70, 100, 70)]
    for i, (cx, cy, s) in enumerate(((90, hor + 74, 0.9), (215, hor + 76, 0.95), (330, hor + 205, 1.3), (465, hor + 74, 0.9), (120, hor + 210, 1.35))):
        col = car_cols[i]
        w, h = 90 * s, 34 * s
        d.rounded_rectangle([cx - w / 2, cy - h, cx + w / 2, cy], radius=8 * s, fill=rgba(shade(col, 0.8)))
        d.polygon([(cx - w * 0.3, cy - h), (cx - w * 0.18, cy - h * 1.65), (cx + w * 0.22, cy - h * 1.65), (cx + w * 0.34, cy - h)], fill=rgba(shade(col, 0.7)))
        d.polygon([(cx - w * 0.24, cy - h * 1.05), (cx - w * 0.15, cy - h * 1.55), (cx + w * 0.19, cy - h * 1.55), (cx + w * 0.28, cy - h * 1.05)], fill=(50, 60, 80, 255))
        d.line([(cx - w / 2 + 6, cy - h + 6), (cx + w / 2 - 6, cy - h + 6)], fill=rgba(mix(col, (255, 200, 140), 0.5)), width=2)
        for wx in (cx - w * 0.3, cx + w * 0.3):
            d.ellipse([wx - 9 * s, cy - 9 * s, wx + 9 * s, cy + 9 * s], fill=(10, 10, 12, 255))
        d.rectangle([cx + w / 2 - 6, cy - h * 0.7, cx + w / 2, cy - h * 0.5], fill=(255, 40, 40, 255))
    img = img.resize((128, 96), Image.LANCZOS)
    # Reflection streaks on the glass
    over = Image.new("RGBA", (128, 96), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    for x0, w in ((10, 6), (22, 2), (70, 9), (86, 3)):
        od.polygon([(x0, 0), (x0 + w, 0), (x0 + w - 60, 96), (x0 - 60, 96)], fill=(200, 210, 255, 22))
    img.alpha_composite(over)
    for col in range(4):
        for row in range(3):
            save(img.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)), f"window-{col}-{row}")
    flat("glasspane", (200, 220, 255), 4, alpha=48)


def glasses():
    img = noisy((210, 230, 240), 3, "glass-clear", alpha=46)
    d = ImageDraw.Draw(img)
    for x0 in (4, 18, 23):
        d.line([(x0, 0), (x0 - 10, S - 1)], fill=(240, 250, 255, 80))
    save(img, "glass-clear")
    img = noisy((8, 6, 12), 2, "glass-dark", alpha=235)
    px = img.load()
    rng = random.Random(3)
    for _ in range(10):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = (200, 60, 220, 240)
    d = ImageDraw.Draw(img)
    d.line([(26, 0), (14, S - 1)], fill=(60, 30, 80, 240))
    save(img, "glass-dark")


def glitch():
    for k in range(3):
        rng = random.Random(100 + k)
        img = Image.new("RGBA", (S, S))
        px = img.load()
        for y in range(S):
            shift_ = rng.choice([0, 0, 0, 1, -1, 3])
            band = rng.random() < 0.2
            for x in range(S):
                v = rng.random()
                if v < 0.45:
                    c = (10, 2, 18)
                elif v < 0.8:
                    c = (110, 30, 170)
                else:
                    c = (200, 90, 255)
                if band:
                    c = mix(c, (240, 120, 255), 0.5)
                if y % 3 == 0:
                    c = shade(c, 0.6)
                px[(x + shift_) % S, y] = rgba(c)
        # RGB split: a red and a cyan ghost of a bright band
        for y in range(rng.randrange(4, 28), S, 11):
            for x in range(S):
                if rng.random() < 0.6:
                    px[x, y] = (255, 40, 80, 255)
                    px[(x + 2) % S, min(S - 1, y + 1)] = (40, 230, 255, 255)
        save(img, f"glitchwall{'' if k == 0 else k + 1}")


# ======================================================================== Neon, metals, small stuff

def neons():
    for c in COLOURS:
        col = NEON[c][0]
        img = Image.new("RGBA", (16, 16))
        px = img.load()
        for y in range(16):
            for x in range(16):
                t = abs(((x + y) % 8) - 3.5) / 3.5
                px[x, y] = rgba(mix(neon_core(col), col, 0.3 + 0.4 * t))
        save(img, f"neon-{c}")
        flat(f"neondim-{c}", shade(col, 0.55), 6)   # a coloured part that is not itself lit (a cap, a skirt)
    img = noisy((58, 58, 64), 6, "neon-dead")
    d = ImageDraw.Draw(img)
    d.line([(2, 3), (7, 9), (12, 8)], fill=(110, 110, 118, 255))
    d.line([(20, 20), (26, 30)], fill=(110, 110, 118, 255))
    save(img, "neon-dead")
    # Metals
    img = noisy((150, 152, 158), 3, "steel")
    px = img.load()
    rng = random.Random(1)
    for y in range(S):
        k = rng.uniform(-8, 8)
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r + k), clamp(g + k), clamp(b + k), 255)
    save(img, "steel")
    img = noisy((210, 214, 222), 2, "chrome")
    d = ImageDraw.Draw(img)
    for y in (4, 5, 20):
        d.line([0, y, S - 1, y], fill=(250, 252, 255, 255))
    d.line([0, 12, S - 1, 12], fill=(140, 144, 154, 255))
    save(img, "chrome")
    # Mirror steel for pillars: dark, catching streaks of the neons
    img = noisy((70, 66, 80), 3, "mirror")
    d = ImageDraw.Draw(img)
    for x, c in ((4, "magenta"), (13, "cyan"), (22, "pink"), (27, "blue")):
        d.line([x, 0, x, S - 1], fill=rgba(mix(NEON[c][0], (255, 255, 255), 0.3)))
        d.line([x + 1, 0, x + 1, S - 1], fill=rgba(shade(NEON[c][0], 0.6)))
    d.line([9, 0, 9, S - 1], fill=(220, 220, 230, 255))
    save(img, "mirror")
    flat("black", (10, 9, 12), 2)
    flat("brass", (190, 150, 70), 10)
    flat("rubber", (24, 24, 26), 3)
    flat("yellow", (240, 196, 30), 6)
    flat("darksteel", (60, 62, 68), 4)
    flat("white", (238, 236, 240), 3)
    flat("redlight", (255, 50, 40), 4)
    flat("greenlight", (60, 255, 120), 4)
    flat("amberlight", (255, 170, 40), 4)
    flat("canopy", (26, 22, 34), 3)
    save(Image.new("RGBA", (16, 16), (0, 0, 0, 0)), "clear")


def mall():
    # Reception and lounge
    flat("whitegloss", (244, 242, 248), 2)
    img = noisy((0xC8, 0xA8, 0xE8), 3, "lilacpanel")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.line([x, 0, x, S - 1], fill=(176, 148, 210, 255))
    save(img, "lilacpanel")
    img = noisy((0x5A, 0x1E, 0x70), 6, "velvet")
    soft_noise(img, "velvet2", 8)
    save(img, "velvet")
    flat("velvetdark", (0x3A, 0x10, 0x4A), 5)
    flat("glasstop", (200, 230, 240), 3, alpha=70)
    # Lost and found: a blue bin with a white label
    img = noisy((40, 80, 180), 5, "lostfound")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 9, 28, 22], fill=(236, 236, 230, 255))
    centred(img, "LOST", 10, (30, 40, 90, 255), F3)
    centred(img, "& FOUND", 16, (30, 40, 90, 255), F3)
    save(img, "lostfound")
    flat("bluebin", (40, 80, 180), 5)
    flat("palm", (60, 150, 70), 10)
    flat("palmdark", (40, 110, 50), 8)
    flat("trunk", (120, 90, 60), 10)
    flat("soil", (40, 30, 24), 6)
    img = noisy((168, 120, 72), 6, "slat")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 4):
        d.line([0, y, S - 1, y], fill=(130, 90, 54, 255))
    save(img, "slat")
    for nm, c in (("plastic-white", (236, 236, 232)), ("plastic-pink", (255, 120, 170)), ("plastic-cyan", (90, 220, 230))):
        img = noisy(c, 3, nm)
        d = ImageDraw.Draw(img)
        d.line([0, 3, S - 1, 3], fill=rgba(mix(c, (255, 255, 255), 0.5)))
        save(img, nm)
    img = noisy((240, 110, 160), 4, "vinyl-pink")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.line([x, 0, x, S - 1], fill=(200, 80, 128, 255))
    save(img, "vinyl-pink")
    flat("vinyl-black", (30, 28, 32), 4)
    # Food stalls: each its own colour band and pattern
    stalls = {"burger": (255, 74, 0), "pizza": (255, 42, 90), "noodles": (100, 232, 247), "taco": (240, 196, 30),
              "icecream": (255, 160, 255), "pretzel": (209, 59, 247)}
    for st, c in stalls.items():
        img = noisy(shade(c, 0.85), 4, "stall-" + st)
        d = ImageDraw.Draw(img)
        for x in range(-S, S, 6):
            d.line([(x, S), (x + S, 0)], fill=rgba(shade(c, 0.7)), width=2)
        d.rectangle([0, 0, S - 1, 4], fill=rgba(mix(c, (255, 255, 255), 0.4)))
        save(img, "stall-" + st)
    flat("till", (44, 44, 50), 4)
    img = noisy((30, 60, 40), 3, "tillscreen")
    draw_text(img, "06", 4, 4, (120, 255, 150, 255), F5, 2)
    save(img, "tillscreen")
    flat("napkin", (246, 246, 240), 3)
    flat("strawcup", (230, 70, 90), 5)
    flat("counter", (230, 228, 222), 3)
    menuboard()
    vending()
    directory()
    # Walkways and escalators
    img = noisy((44, 44, 48), 3, "tread")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 2):
        d.line([x, 0, x, S - 1], fill=(30, 30, 34, 255))
    for k in range(2):
        y0 = 6 + k * 16
        d.line([(8, y0 + 6), (16, y0), (24, y0 + 6)], fill=(250, 200, 40, 255), width=2)
    d.rectangle([0, 0, 1, S - 1], fill=(240, 196, 30, 255))
    d.rectangle([S - 2, 0, S - 1, S - 1], fill=(240, 196, 30, 255))
    save(img, "tread")
    img = noisy((160, 162, 168), 3, "comb")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 3):
        d.line([x, 0, x, 7], fill=(240, 196, 30, 255))
    for y in range(10, S, 4):
        d.line([0, y, S - 1, y], fill=(120, 122, 128, 255))
    save(img, "comb")
    img = noisy((120, 122, 128), 3, "stairtread")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 2):
        d.line([x, 0, x, S - 1], fill=(90, 92, 98, 255))
    d.rectangle([0, 0, S - 1, 2], fill=(240, 196, 30, 255))
    save(img, "stairtread")
    flat("riser", (70, 72, 78), 3)
    # Shutters, doors
    img = noisy((150, 152, 156), 4, "shutter")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 4):
        d.line([0, y, S - 1, y], fill=(110, 112, 116, 255))
        d.line([0, y + 1, S - 1, y + 1], fill=(176, 178, 182, 255))
    save(img, "shutter")
    img = Image.open(os.path.join(TEX, "block", "3999", "shutter.png")).copy()
    centred(img, "CLOSED", 8, (40, 40, 46, 255), F3)
    centred(img, "FOR", 15, (40, 40, 46, 255), F3)
    centred(img, "REFIT", 22, (40, 40, 46, 255), F3)
    save(img, "shutter-stencil")
    img = noisy((128, 132, 136), 3, "doorsteel")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(110, 114, 118, 255))
    save(img, "doorsteel")
    img = noisy((128, 132, 136), 3, "staffsign")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 8, 29, 23], fill=(214, 196, 40, 255))
    centred(img, "STAFF", 10, (20, 20, 20, 255), F3)
    centred(img, "ONLY", 17, (20, 20, 20, 255), F3)
    save(img, "staffsign")
    img = noisy((0x6A, 0x3A, 0x6E), 3, "plumsteel")
    px = img.load()
    rng = random.Random(8)
    for y in range(S):
        k = rng.uniform(-6, 6)
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r + k), clamp(g + k), clamp(b + k), 255)
    save(img, "plumsteel")
    img = noisy((26, 30, 26), 2, "lcd")
    draw_text(img, "--", 6, 10, (90, 255, 120, 255), F5, 2)
    save(img, "lcd")
    flat("keybutton", (200, 200, 206), 4)
    # Tickets on a tray, fallen panels, a lounger, a lamp, beacons
    img = noisy((200, 30, 40), 10, "tickets")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 4):
        d.line([0, y, S - 1, y], fill=(150, 20, 30, 255))
    for x in range(0, S, 6):
        d.line([x, 0, x, S - 1], fill=(236, 200, 200, 255))
    save(img, "tickets")
    flat("tray", (60, 40, 80), 4)
    img = noisy((30, 30, 34), 5, "debris")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], outline=(50, 50, 56, 255))
    d.line([(3, 20), (20, 28)], fill=(60, 60, 64, 255))
    save(img, "debris")
    img = noisy((240, 240, 236), 3, "loungerslat")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 4):
        d.line([0, y, S - 1, y], fill=(190, 190, 186, 255))
    save(img, "loungerslat")
    flat("sodium", (255, 190, 90), 4)
    flat("lampsteel", (80, 84, 90), 4)
    flat("bulb-red", (255, 40, 30), 4)
    flat("bulb-green", (60, 255, 90), 4)
    flat("bulb-red-off", (90, 20, 20), 4)
    # Windmills
    img = noisy((236, 234, 226), 4, "weatherboard")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y + 7, S - 1, y + 7], fill=(170, 168, 160, 255))
        d.line([0, y, S - 1, y], fill=(250, 250, 246, 255))
    save(img, "weatherboard")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    rng = random.Random(11)
    for row in range(8):
        off = 4 if row % 2 else 0
        for col in range(-1, 5):
            c = clamp(48 + rng.uniform(-10, 10))
            d.rectangle([col * 8 + off, row * 4, col * 8 + off + 7, row * 4 + 3], fill=(c, c - 4, c - 2, 255))
            d.line([col * 8 + off, row * 4 + 3, col * 8 + off + 7, row * 4 + 3], fill=(24, 22, 22, 255))
    save(img, "shingle")
    flat("sailwood", (140, 110, 80), 8)
    img = noisy((226, 216, 190), 5, "canvas")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x, S - 1], fill=(206, 196, 170, 255))
    save(img, "canvas")
    flat("gengreen", (50, 110, 60), 5)
    img = noisy((236, 232, 220), 2, "dial")
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], outline=(30, 30, 30, 255), width=2)
    for a in range(-120, 121, 30):
        r = math.radians(a - 90)
        d.line([(16 + 10 * math.cos(r), 16 + 10 * math.sin(r)), (16 + 13 * math.cos(r), 16 + 13 * math.sin(r))], fill=(30, 30, 30, 255))
    d.line([(16, 16), (24, 9)], fill=(200, 30, 30, 255), width=2)
    save(img, "dial")


def menuboard():
    img = Image.new("RGBA", (64, 32), (16, 10, 26, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 63, 31], outline=(255, 160, 255, 255))
    centred(img, "MENU", 2, (255, 210, 120, 255), F5)
    rows = [("BURGER", "6"), ("PIZZA", "6"), ("NOODLES", "6"), ("TACOS", "6")]
    for i, (n, p) in enumerate(rows):
        draw_text(img, n, 3, 11 + i * 5, (240, 240, 250, 255), F3)
        draw_text(img, p, 50, 11 + i * 5, (100, 232, 247, 255), F3)
        # A tiny ticket icon
        d.rectangle([55, 11 + i * 5, 60, 14 + i * 5], fill=(220, 40, 50, 255))
    save(img, "menuboard")


def products(d, x0, y0, w, h, kind, rng):
    """Rows of products behind glass: chip bags and bars, or cans and bottles."""
    rows = 5
    for r in range(rows):
        y = y0 + 2 + r * (h - 4) / rows
        d.line([x0, y + (h - 4) / rows - 1, x0 + w, y + (h - 4) / rows - 1], fill=(160, 160, 170, 255))
        for c in range(4):
            x = x0 + 2 + c * (w - 4) / 4
            if kind == "snack":
                col = rng.choice([(255, 74, 0), (240, 196, 30), (209, 59, 247), (100, 232, 247), (255, 42, 90), (90, 200, 90)])
                d.rectangle([x, y + 1, x + (w - 4) / 4 - 2, y + (h - 4) / rows - 3], fill=rgba(col))
                d.line([x, y + 2, x + (w - 4) / 4 - 2, y + 2], fill=(255, 255, 255, 255))
            else:
                col = rng.choice([(200, 30, 40), (60, 200, 90), (120, 60, 200), (240, 240, 230), (255, 160, 255)])
                d.rectangle([x + 0.5, y + 2, x + (w - 4) / 4 - 1.5, y + (h - 4) / rows - 2], fill=rgba(col))
                d.line([x + 0.5, y + 2, x + (w - 4) / 4 - 1.5, y + 2], fill=(220, 220, 230, 255))


def vending():
    for kind, body in (("snack", (40, 30, 60)), ("drink", (20, 50, 90))):
        rng = random.Random(seed_of(kind))
        img = Image.new("RGBA", (32, 64), rgba(body))
        d = ImageDraw.Draw(img)
        d.rectangle([2, 4, 22, 50], fill=(20, 22, 30, 255))
        products(d, 3, 5, 19, 44, kind, rng)
        # glass sheen
        d.polygon([(4, 5), (9, 5), (3, 30), (3, 20)], fill=(255, 255, 255, 40))
        # keypad, coin slot taped over, delivery flap
        for r in range(4):
            for c in range(3):
                d.rectangle([24 + c * 2, 14 + r * 3, 24 + c * 2, 15 + r * 3], fill=(220, 220, 226, 255))
        d.rectangle([24, 9, 29, 11], fill=(90, 255, 120, 255))
        d.rectangle([23, 28, 30, 34], fill=(236, 220, 150, 255))
        d.line([23, 31, 30, 31], fill=(120, 100, 60, 255))
        d.rectangle([4, 53, 20, 60], fill=(10, 10, 12, 255))
        d.line([4, 53, 20, 53], fill=(120, 120, 130, 255))
        title = "SNACKS" if kind == "snack" else "DRINKS"
        centred(img, title, 0, rgba(NEON["cyan"][0] if kind == "drink" else NEON["orange"][0]), F3, x0=0, x1=24)
        save(img, f"vending-{kind}")
        flat(f"vendingbody-{kind}", body, 3)
    img = noisy((236, 220, 150), 3, "tape")
    centred(img, "ALMOND", 6, (60, 40, 20, 255), F3)
    centred(img, "WATER", 13, (60, 40, 20, 255), F3)
    centred(img, "ONLY", 20, (60, 40, 20, 255), F3)
    save(img, "tape")


def directory():
    img = Image.new("RGBA", (24, 64), (14, 12, 24, 255))
    d = ImageDraw.Draw(img)
    centred(img, "MALL", 2, (255, 160, 255, 255), F3)
    centred(img, "MAP", 8, (255, 160, 255, 255), F3)
    # A strict grid of concourses and units, a red dot: you are here
    d.rectangle([2, 15, 21, 50], fill=(30, 26, 48, 255))
    cols = [NEON[c][0] for c in COLOURS]
    rng = random.Random(6)
    for gy in range(4):
        for gx in range(2):
            d.rectangle([3 + gx * 10, 16 + gy * 9, 10 + gx * 10, 22 + gy * 9], fill=rgba(shade(rng.choice(cols), 0.8)))
    d.line([12, 15, 12, 50], fill=(240, 240, 250, 255))
    d.line([2, 33, 21, 33], fill=(240, 240, 250, 255))
    d.ellipse([10, 31, 14, 35], fill=(255, 40, 40, 255))
    draw_text(img, "YOU", 2, 53, (240, 240, 250, 255), F3)
    draw_text(img, "ARE", 2, 58, (240, 240, 250, 255), F3)
    draw_text(img, "HERE", 13, 55, (255, 80, 80, 255), F3)
    save(img, "directory")


# ======================================================================== Plush and prizes

PLUSH = {"bear": (150, 100, 60), "cat": (240, 140, 50), "alien": (110, 210, 90), "smiley": (250, 220, 40),
         "pink": (255, 140, 200), "blue": (90, 140, 240), "purple": (170, 100, 230), "white": (240, 236, 230)}


def plush_tex():
    for name, c in PLUSH.items():
        img = noisy(c, 10, "fur-" + name)
        rng = random.Random(seed_of(name))
        px = img.load()
        for _ in range(60):  # tufts
            x, y = rng.randrange(S), rng.randrange(S)
            px[x, y] = rgba(mix(c, (255, 255, 255), 0.3))
        save(img, "fur-" + name)
    # Faces (32 px, the whole face of the head box)
    def face(name, c, draw):
        img = noisy(c, 8, "face-" + name)
        d = ImageDraw.Draw(img)
        draw(d)
        save(img, "face-" + name)
    face("bear", PLUSH["bear"], lambda d: (d.ellipse([9, 14, 23, 28], fill=(220, 190, 150, 255)), d.ellipse([8, 8, 12, 12], fill=(10, 10, 10, 255)),
                                             d.ellipse([20, 8, 24, 12], fill=(10, 10, 10, 255)), d.ellipse([13, 16, 19, 20], fill=(40, 20, 10, 255)),
                                             d.arc([12, 18, 20, 25], 20, 160, fill=(40, 20, 10, 255), width=1)))
    face("cat", PLUSH["cat"], lambda d: (d.ellipse([7, 10, 12, 16], fill=(20, 60, 20, 255)), d.ellipse([20, 10, 25, 16], fill=(20, 60, 20, 255)),
                                           d.polygon([(14, 18), (18, 18), (16, 20)], fill=(255, 120, 150, 255)),
                                           d.line([(3, 20), (11, 21)], fill=(250, 240, 230, 255)), d.line([(21, 21), (29, 20)], fill=(250, 240, 230, 255)),
                                           d.arc([12, 19, 20, 24], 20, 160, fill=(80, 30, 10, 255))))
    face("alien", PLUSH["alien"], lambda d: (d.ellipse([4, 8, 14, 20], fill=(10, 10, 20, 255)), d.ellipse([18, 8, 28, 20], fill=(10, 10, 20, 255)),
                                               d.ellipse([7, 10, 9, 12], fill=(255, 255, 255, 255)), d.ellipse([21, 10, 23, 12], fill=(255, 255, 255, 255)),
                                               d.line([(13, 25), (19, 25)], fill=(30, 80, 30, 255))))
    face("smiley", PLUSH["smiley"], lambda d: (d.ellipse([9, 8, 13, 15], fill=(20, 20, 20, 255)), d.ellipse([19, 8, 23, 15], fill=(20, 20, 20, 255)),
                                                 d.arc([6, 10, 26, 27], 20, 160, fill=(20, 20, 20, 255), width=2)))
    # Boxed toys
    for i, (c, label) in enumerate(((NEON["cyan"][0], "ROBO"), (NEON["pink"][0], "STAR"), (NEON["orange"][0], "YO-YO"))):
        img = noisy(c, 4, f"toybox-{i}")
        d = ImageDraw.Draw(img)
        d.rectangle([4, 8, 27, 24], fill=(20, 20, 30, 255))
        d.rectangle([6, 10, 25, 22], fill=(200, 220, 240, 255))
        centred(img, label, 26, (255, 255, 255, 255), F3)
        save(img, f"toybox-{i}")
    img = noisy((214, 196, 160), 4, "pegboard")
    d = ImageDraw.Draw(img)
    for y in range(2, S, 4):
        for x in range(2, S, 4):
            d.point((x, y), fill=(90, 70, 50, 255))
    save(img, "pegboard")
    img = noisy((0x6A, 0x2A, 0x8C), 4, "laminate")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=(0x8A, 0x4A, 0xAC, 255))
    save(img, "laminate")
    img = noisy((0x6A, 0x2A, 0x8C), 4, "laminate-dusty")
    soft_noise(img, "dust", 10)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * 0.6 + 40), clamp(g * 0.6 + 36), clamp(b * 0.6 + 34), 255)
    save(img, "laminate-dusty")
    img = noisy((200, 220, 230), 3, "glass-cracked", alpha=70)
    d = ImageDraw.Draw(img)
    for pts in (((16, 14), (2, 4)), ((16, 14), (30, 2)), ((16, 14), (10, 31)), ((16, 14), (31, 22)), ((16, 14), (0, 20))):
        d.line(pts, fill=(255, 255, 255, 170))
    save(img, "glass-cracked")
    flat("dust", (110, 104, 100), 8)


# ======================================================================== Items

def items_tex():
    # The ticket: a red strip, notched and perforated at the ends, ADMIT ONE
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 9, 29, 22], fill=(206, 30, 44, 255))
    d.rectangle([4, 11, 27, 20], outline=(255, 206, 110, 255))
    for (x, y) in ((2, 15), (2, 16), (29, 15), (29, 16)):
        img.putpixel((x, y), (0, 0, 0, 0))
    for y in range(10, 22, 2):
        img.putpixel((6, y), (150, 18, 28, 255))
        img.putpixel((25, y), (150, 18, 28, 255))
    centred(img, "ADMIT", 12, (255, 240, 210, 255), F3)
    centred(img, "ONE", 17, (255, 240, 210, 255), F3, x0=0, x1=32)
    d.line([3, 23, 30, 23], fill=(120, 14, 22, 255))
    save_item(img, "ticket")

    # Tray meals: a paper tray, and on it the food
    def tray(name, draw):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.polygon([(2, 20), (16, 26), (30, 20), (16, 14)], fill=(240, 230, 210, 255))
        d.polygon([(2, 20), (16, 26), (16, 29), (2, 23)], fill=(200, 60, 60, 255))
        d.polygon([(16, 26), (30, 20), (30, 23), (16, 29)], fill=(230, 80, 80, 255))
        draw(d)
        save_item(img, "traymeal-" + name)
    tray("burger", lambda d: (d.ellipse([9, 8, 23, 16], fill=(214, 150, 60, 255)), d.rectangle([9, 14, 23, 16], fill=(90, 200, 70, 255)),
                              d.rectangle([9, 16, 23, 18], fill=(110, 50, 30, 255)), d.ellipse([9, 17, 23, 22], fill=(200, 140, 60, 255)),
                              d.point((14, 10), (255, 240, 200, 255)), d.point((18, 11), (255, 240, 200, 255))))
    tray("pizza", lambda d: (d.polygon([(8, 12), (24, 10), (16, 23)], fill=(250, 200, 80, 255)), d.line([(8, 12), (24, 10)], fill=(190, 120, 50, 255), width=2),
                             d.ellipse([12, 13, 15, 16], fill=(200, 40, 40, 255)), d.ellipse([17, 13, 20, 16], fill=(200, 40, 40, 255)),
                             d.ellipse([15, 17, 18, 20], fill=(200, 40, 40, 255))))
    tray("noodles", lambda d: (d.ellipse([7, 11, 25, 22], fill=(255, 255, 255, 255)), d.ellipse([9, 12, 23, 18], fill=(240, 210, 120, 255)),
                               d.arc([10, 12, 18, 18], 0, 180, fill=(220, 180, 90, 255)), d.line([(20, 4), (14, 15)], fill=(150, 90, 40, 255), width=1),
                               d.line([(23, 5), (16, 15)], fill=(150, 90, 40, 255), width=1)))
    tray("taco", lambda d: (d.chord([7, 9, 25, 27], 180, 360, fill=(240, 200, 90, 255)), d.rectangle([9, 15, 23, 17], fill=(90, 200, 70, 255)),
                            d.point((12, 15), (220, 40, 40, 255)), d.point((18, 15), (220, 40, 40, 255))))
    tray("icecream", lambda d: (d.polygon([(13, 14), (19, 14), (16, 23)], fill=(220, 170, 100, 255)), d.ellipse([11, 6, 21, 15], fill=(255, 160, 255, 255)),
                                d.ellipse([13, 3, 19, 9], fill=(255, 240, 200, 255)), d.point((16, 2), (220, 30, 40, 255))))
    tray("pretzel", lambda d: (d.arc([8, 8, 24, 22], 0, 360, fill=(170, 100, 40, 255), width=3), d.line([(10, 18), (22, 11)], fill=(170, 100, 40, 255), width=3),
                               d.line([(10, 11), (22, 18)], fill=(170, 100, 40, 255), width=3), d.point((12, 10), (255, 255, 255, 255)),
                               d.point((19, 17), (255, 255, 255, 255))))
    # Glow bracelets
    for c in ("magenta", "cyan", "lilac"):
        col = NEON[c][0]
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([5, 9, 27, 25], outline=rgba(shade(col, 0.6), 140), width=5)
        d.ellipse([6, 10, 26, 24], outline=rgba(col), width=3)
        d.arc([7, 11, 25, 23], 200, 300, fill=rgba(neon_core(col)), width=1)
        d.rectangle([14, 22, 18, 25], fill=(230, 230, 230, 255))
        save_item(img, "glowband-" + c)
    # Popcorn: a striped bucket heaped white
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(8, 12), (24, 12), (22, 30), (10, 30)], fill=(240, 240, 240, 255))
    for x in range(9, 24, 4):
        d.polygon([(x, 12), (x + 2, 12), (x + 1.6, 30), (x - 0.2, 30)], fill=(220, 40, 50, 255))
    rng = random.Random(3)
    for _ in range(26):
        x, y = rng.uniform(8, 24), rng.uniform(3, 13)
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=rgba(rng.choice([(255, 250, 230), (250, 230, 150), (255, 255, 255)])))
    centred(img, "POP", 20, (30, 30, 80, 255), F3)
    save_item(img, "popcorn")
    # Cotton candy on a paper cone
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(14, 18), (18, 18), (16, 31)], fill=(240, 236, 220, 255))
    for (x, y, r, c) in ((16, 10, 8, (255, 170, 220)), (11, 12, 5, (200, 170, 255)), (21, 9, 5, (255, 190, 230)), (16, 5, 5, (255, 200, 240))):
        d.ellipse([x - r, y - r, x + r, y + r], fill=rgba(c))
    save_item(img, "cottoncandy")
    # Paradise Pop: cans in three flavours
    for flav, c in (("cherry", (200, 30, 50)), ("lime", (70, 200, 80)), ("grape", (130, 60, 200))):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([10, 5, 22, 29], radius=2, fill=rgba(c))
        d.rectangle([10, 5, 22, 7], fill=(200, 200, 206, 255))
        d.rectangle([10, 27, 22, 29], fill=(180, 180, 186, 255))
        d.line([12, 8, 12, 26], fill=rgba(mix(c, (255, 255, 255), 0.5)))
        d.ellipse([12, 11, 20, 19], fill=(255, 255, 255, 255))
        d.ellipse([13, 12, 19, 18], fill=rgba(NEON["pink"][0]))
        draw_text(img, "POP", 12, 21, (255, 255, 255, 255), F3)
        save_item(img, "soda-" + flav)
    # Salvage: neon tubing (a coil of glass), a circuit board, a coin mechanism, plastic scrap
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, c in enumerate(((180, 200, 210), (220, 230, 240))):
        d.arc([4 + k, 6 + k, 28 - k, 26 - k], 0, 330, fill=rgba(c, 220), width=3)
    d.arc([8, 10, 24, 22], 30, 360, fill=(240, 240, 250, 230), width=2)
    d.rectangle([24, 14, 29, 17], fill=(60, 60, 64, 255))
    save_item(img, "neontubing")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 6, 28, 25], fill=(30, 110, 60, 255))
    for y in range(8, 24, 3):
        d.line([4, y, 27, y], fill=(200, 170, 70, 255))
    d.rectangle([8, 10, 16, 18], fill=(20, 20, 24, 255))
    for x in range(8, 17, 2):
        d.point((x, 9), (210, 210, 210, 255))
        d.point((x, 19), (210, 210, 210, 255))
    d.rectangle([19, 9, 25, 12], fill=(20, 20, 24, 255))
    d.ellipse([19, 15, 24, 20], fill=(60, 100, 200, 255))
    d.rectangle([3, 26, 28, 27], fill=(220, 190, 60, 255))
    save_item(img, "circuitboard")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([7, 4, 25, 28], fill=(190, 160, 80, 255))
    d.rectangle([8, 5, 24, 27], outline=(230, 200, 120, 255))
    d.rectangle([14, 7, 17, 15], fill=(20, 20, 20, 255))
    d.rectangle([10, 18, 22, 22], fill=(200, 40, 40, 255))
    centred(img, "1", 18, (255, 255, 255, 255), F3, x0=10, x1=22)
    d.ellipse([12, 23, 20, 27], fill=(120, 110, 90, 255))
    save_item(img, "coinmech")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(4, 10), (18, 4), (28, 14), (22, 26), (8, 24)], fill=(80, 200, 220, 255))
    d.polygon([(12, 14), (20, 10), (24, 18), (16, 22)], fill=(255, 120, 190, 255))
    d.line([(4, 10), (18, 4), (28, 14)], fill=(200, 250, 255, 255))
    save_item(img, "plastic")


def generate():
    carpets()
    marbles()
    concretes()
    walls()
    ceilings()
    lanewood()
    asphalts()
    pools()
    facades()
    window_painting()
    glasses()
    glitch()
    neons()
    mall()
    plush_tex()
    items_tex()
    print("3999 textures: building, fittings, items")


if __name__ == "__main__":
    generate()
