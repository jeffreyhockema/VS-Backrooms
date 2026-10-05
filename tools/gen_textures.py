"""Generates the placeholder textures and mod icon procedurally.

Colours and patterns follow the original 2002 Backrooms photos: dingy pale yellow wallpaper with alternating
columns of beaded lines and stacked chevrons (or a dot grid on some walls), brownish-beige Berber carpet,
fissured drop-ceiling tiles and prismatic troffer lights.

Run from the repo root:  python tools/gen_textures.py
Re-running overwrites the PNGs, so once a texture has been hand-painted, remove it from this script.
"""
import os
import random

import texlib

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures")
S = 32  # block texture size


def save(img, rel):
    path = os.path.join(TEX, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def hexrgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, f):
    return tuple(clamp(v * f) for v in c[:3]) + (255,)


def noise_fill(base, amount, seed, size=S):
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            d = rng.randint(-amount, amount)
            px[x, y] = tuple(clamp(v + d) for v in base) + (255,)
    return img


def blotch(img, center, radius, color, strength, seed):
    """Tints a soft irregular blob, e.g. a water stain."""
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    cx, cy = center
    for y in range(h):
        for x in range(w):
            # Wrap so stains stay seamless across tiles
            dx = min(abs(x - cx), w - abs(x - cx))
            dy = min(abs(y - cy), h - abs(y - cy))
            d = (dx * dx + dy * dy) ** 0.5 / radius + rng.uniform(-0.2, 0.2)
            if d < 1:
                t = strength * (1 - d)
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r + (color[0] - r) * t), clamp(g + (color[1] - g) * t), clamp(b + (color[2] - b) * t), a)


# ---------------- Wallpaper ----------------

GROUND = hexrgb(0xD7D48A)
CHEVRON = hexrgb(0xB3AE7A)
BEAD = hexrgb(0xE8E4BE)


def pattern_chevron(seed):
    """Columns of beaded lines alternating with columns of stacked upward chevrons, offset by half a step."""
    img = noise_fill(GROUND, 3, seed)
    px = img.load()
    for col in range(S // 8):
        x0 = col * 8
        offset = (col % 2) * 4
        for y in range(S):
            if (y // 2) % 2 == 0:
                px[x0, y] = BEAD + (255,)  # beaded / dashed line
            row = (y + offset) % 8
            # "^" three rows tall, five pixels wide, centred in the column
            for dx, r in ((4, 0), (3, 1), (5, 1), (2, 2), (6, 2)):
                if row == r:
                    px[x0 + dx, y] = CHEVRON + (255,)
    return img


def pattern_dotted(seed):
    img = noise_fill(hexrgb(0xDCD89C), 3, seed)
    px = img.load()
    for y in range(0, S, 4):
        for x in range(0, S, 4):
            px[(x + (2 if (y // 4) % 2 else 0)) % S, y] = hexrgb(0xB5AE78) + (255,)
    return img


def pattern_cream(seed):
    return noise_fill(hexrgb(0xE4DDC2), 4, seed)


def pattern_manila(seed):
    img = noise_fill(hexrgb(0xD5BE8A), 4, seed)
    px = img.load()
    for y in range(1, S, 5):
        for x in range(1, S, 5):
            px[(x + (y // 5) % 2 * 2) % S, y] = hexrgb(0xBDA470) + (255,)
    return img


def pattern_stripped(seed):
    img = noise_fill(hexrgb(0xC9C3B2), 5, seed)
    rng = random.Random(seed + 7)
    d = ImageDraw.Draw(img)
    for _ in range(7):  # dried glue streaks
        x = rng.randrange(S)
        d.line([x, rng.randrange(S), x + rng.randint(-2, 2), rng.randrange(S)], fill=(176, 168, 146, 255))
    for _ in range(5):  # scraps of yellow paper that would not come away
        x, y = rng.randrange(S - 4), rng.randrange(S - 3)
        d.rectangle([x, y, x + rng.randint(1, 4), y + rng.randint(1, 2)], fill=GROUND + (255,))
    return img


def pattern_red(seed):
    """The Red Rooms: the same beaded lines and chevrons as the yellow paper, in dried-blood red."""
    ground, chevron, bead = hexrgb(0x8A2A22), hexrgb(0x5A1412), hexrgb(0xB45C4A)
    img = noise_fill(ground, 4, seed)
    px = img.load()
    for col in range(S // 8):
        x0 = col * 8
        offset = (col % 2) * 4
        for y in range(S):
            if (y // 2) % 2 == 0:
                px[x0, y] = bead + (255,)
            row = (y + offset) % 8
            for dx, r in ((4, 0), (3, 1), (5, 1), (2, 2), (6, 2)):
                if row == r:
                    px[x0 + dx, y] = chevron + (255,)
    return img


PATTERNS = {"stripped": pattern_stripped, "chevron": pattern_chevron, "dotted": pattern_dotted, "cream": pattern_cream, "manila": pattern_manila,
            "red": pattern_red}


def add_baseboard(img):
    d = ImageDraw.Draw(img)
    d.rectangle([0, S - 3, S - 1, S - 1], fill=(74, 63, 46, 255))  # dark vinyl
    d.line([0, S - 4, S - 1, S - 4], fill=(96, 84, 64, 255))
    return img


def add_rail(img):
    # Thin brown chair rail about 0.4 m up the wall
    d = ImageDraw.Draw(img)
    d.rectangle([0, 19, S - 1, 20], fill=(122, 90, 54, 255))
    d.line([0, 18, S - 1, 18], fill=(150, 116, 74, 255))
    return img


def add_outlet(img, name):
    # Same trim as the wall it sits on: under the rail on dotted paper, above the baseboard elsewhere
    if name == "dotted":
        add_rail(img)
    else:
        add_baseboard(img)
    d = ImageDraw.Draw(img)
    d.rectangle([13, 21, 18, 28], fill=(236, 232, 218, 255), outline=(190, 186, 170, 255))
    for y in (23, 26):
        d.line([15, y, 15, y], fill=(80, 76, 70, 255))
        d.line([17, y, 17, y], fill=(80, 76, 70, 255))
    return img


def damp(img, seed):
    """The same wall, older: a faint water stain run down from the ceiling, and a tide mark of yellowed paste."""
    img = img.copy()
    rng = random.Random(seed)
    px = img.load()
    x0, w = rng.randrange(2, S - 10), rng.randint(5, 10)
    for y in range(S):
        for x in range(x0, min(S, x0 + w)):
            t = 0.16 * (1 - abs((x - x0 - w / 2) / (w / 2))) * (1 - y / (S * 1.8))
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * (1 - t) + 118 * t), clamp(g * (1 - t) + 102 * t), clamp(b * (1 - t) + 58 * t), a)
    blotch(img, (rng.randrange(S), rng.randrange(S)), rng.randint(4, 8), (160, 148, 92), 0.22, seed + 1)
    return img


def wallpapers():
    for i, (name, fn) in enumerate(PATTERNS.items()):
        parts = {"upper": fn(100 + i), "plain": fn(110 + i), "baseboard": add_baseboard(fn(120 + i)),
                 "rail": add_rail(fn(130 + i)), "outlet": add_outlet(fn(140 + i), name)}
        for part, img in parts.items():
            save(img, f"block/wallpaper/{name}-{part}.png")
            # An older, damp-stained stretch of the same wall, mixed in at random
            save(damp(img, 300 + i * 10 + len(part)), f"block/wallpaper/{name}-{part}-damp.png")


# ---------------- Floor, ceiling, lights ----------------

def carpet(variant):
    base = {"normal": 0xA8956A, "stained": 0xA8956A, "soaked": 0x857356}[variant]
    img = noise_fill(hexrgb(base), 9, 1)
    rng = random.Random(2)
    px = img.load()
    # Berber loops: a faint diagonal weave plus darker flecks
    for y in range(S):
        for x in range(S):
            if (x + y) % 4 == 0:
                px[x, y] = shade(px[x, y], 0.93)
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = shade(px[x, y], 0.8)
    if variant == "stained":
        blotch(img, (12, 18), 12, (96, 80, 50), 0.6, 3)
        blotch(img, (27, 5), 6, (110, 92, 58), 0.4, 4)
    if variant == "soaked":
        blotch(img, (16, 16), 18, (92, 82, 62), 0.4, 5)
    return img


def carpet_threadbare():
    """The pile cut away: grey-brown backing mesh with a few tufts left."""
    img = noise_fill(hexrgb(0x7C6F58), 6, 40)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if x % 3 == 0 or y % 3 == 0:
                px[x, y] = shade(px[x, y], 0.82)
    rng = random.Random(41)
    for _ in range(18):
        x, y = rng.randrange(S - 1), rng.randrange(S - 1)
        px[x, y] = px[x + 1, y] = hexrgb(0xA8956A) + (255,)
    return img


def sprite():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def salvage_items():
    """Flat item sprites; the game extrudes them into 3D."""
    glass, glass_hi, glass_lo = (196, 226, 232, 235), (240, 250, 252, 255), (120, 160, 170, 255)
    wrap, steel, steel_lo = (200, 190, 110, 255), (150, 156, 162, 255), (96, 102, 108, 255)

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(6, 27), (12, 6), (20, 3), (25, 14), (16, 28)], fill=glass, outline=glass_lo)
    d.line([(13, 8), (10, 24)], fill=glass_hi)
    save(img, "item/salvage/glassshard.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(14, 16), (22, 3), (27, 6), (19, 20)], fill=glass, outline=glass_lo)  # blade
    d.line([(21, 6), (16, 16)], fill=glass_hi)
    d.polygon([(5, 27), (13, 16), (18, 20), (9, 30)], fill=wrap, outline=(140, 130, 70, 255))  # bound handle
    for k in range(3):
        d.line([(8 + k * 3, 24 - k * 3), (11 + k * 3, 27 - k * 3)], fill=(140, 124, 84, 255))
    save(img, "item/salvage/glassshiv.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(12, 18), (22, 4), (28, 4), (28, 9), (18, 22)], fill=steel, outline=steel_lo)  # ground edge
    d.line([(23, 5), (14, 18)], fill=(214, 220, 224, 255))
    d.polygon([(4, 27), (12, 17), (18, 22), (9, 31)], fill=wrap, outline=(140, 130, 70, 255))
    for k in range(3):
        d.line([(7 + k * 3, 25 - k * 3), (10 + k * 3, 28 - k * 3)], fill=(140, 124, 84, 255))
    save(img, "item/salvage/scraper.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    rng = random.Random(50)
    for _ in range(26):  # a tangle of beige threads
        x, y = rng.randint(6, 24), rng.randint(8, 24)
        d.line([(x, y), (x + rng.randint(-6, 6), y + rng.randint(-5, 5))], fill=rng.choice([(168, 149, 106, 255), (142, 124, 84, 255), (190, 172, 128, 255)]))
    save(img, "item/salvage/carpetfibre.png")

    img = sprite()
    strip = pattern_chevron(51).crop((0, 0, 9, 26))
    img.paste(strip, (9, 3))
    d = ImageDraw.Draw(img)
    d.polygon([(9, 26), (18, 26), (22, 30), (13, 30)], fill=(190, 186, 120, 255))  # curled end
    d.rectangle([9, 3, 17, 28], outline=(150, 146, 92, 255))
    save(img, "item/salvage/wallpaperstrip.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(6, 5), (11, 5), (11, 21), (26, 21), (26, 26), (6, 26)], fill=steel, outline=steel_lo)  # L bracket
    for hole in ((8, 9), (8, 16), (16, 23), (22, 23)):
        d.point(hole, fill=(40, 42, 46, 255))
    save(img, "item/salvage/metalbracket.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    for k in range(4):  # coils of copper wire
        d.ellipse([7 + k, 8 + k * 2, 24 - k, 22 - k], outline=(184, 115, 51, 255))
    d.line([(22, 20), (28, 27)], fill=(184, 115, 51, 255), width=1)
    d.line([(9, 12), (4, 5)], fill=(150, 90, 40, 255), width=1)
    save(img, "item/salvage/scrapwire.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(4, 20), (25, 8), (28, 13), (27, 15), (7, 26)], fill=(84, 60, 40, 255), outline=(52, 36, 24, 255))
    d.line([(8, 21), (24, 12)], fill=(110, 82, 56, 255))
    for x, y in ((12, 21), (18, 17), (22, 14)):  # rot
        d.point((x, y), fill=(40, 52, 30, 255))
    save(img, "item/salvage/rottenwood.png")


def portrait(seed):
    """A dark, unsettling oil portrait: a figure in black against murky brown, the face lit from one side, the eyes
    lost in shadow, the varnish gone yellow."""
    img = texlib.vertical_gradient((52, 40, 28), (28, 22, 16))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-6, 6)
            # shoulders and a dark coat
            if y > 20 and abs(x - 16) < 6 + (y - 20) * 0.9:
                r, g, b = 22, 18, 20
                if abs(x - 16) < 2 and y < 26:
                    r, g, b = 150, 140, 120  # a white collar
            # the face: an oval, lit from the left, shadowed on the right
            dx, dy = (x - 16) / 5.0, (y - 13) / 6.5
            if dx * dx + dy * dy < 1:
                light = 0.55 + 0.45 * max(0.0, -dx)
                r, g, b = int(176 * light), int(142 * light), int(110 * light)
                if 10 <= y <= 12 and (13 <= x <= 14 or 18 <= x <= 19):
                    r, g, b = 40, 30, 24  # eyes in shadow
            # hair, dark and close
            if 0.75 < dx * dx + dy * dy < 1.25 and y < 12:
                r, g, b = 34, 26, 20
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), 255)
    # the varnish, yellowed toward the middle
    blotch(img, (16, 14), 14, (120, 96, 40), 0.18, seed + 1)
    return img


def ceiling_tile(seed=6, stain=False):
    img = noise_fill(hexrgb(0xD6CFA6), 4, seed)
    rng = random.Random(seed + 1)
    px = img.load()
    # Fissured mineral fibre: short dark worm-like marks
    for _ in range(26):
        x, y = rng.randrange(2, S - 2), rng.randrange(2, S - 2)
        for _ in range(rng.randint(1, 3)):
            px[x, y] = hexrgb(0xB2AA84) + (255,)
            x = min(S - 3, max(2, x + rng.choice((-1, 0, 1))))
            y = min(S - 3, max(2, y + rng.choice((0, 1))))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(150, 144, 118, 255))  # grid T-bar
    d.line([1, S - 2, S - 2, S - 2], fill=(184, 177, 146, 255))  # tegular edge shadow
    d.line([S - 2, 1, S - 2, S - 2], fill=(184, 177, 146, 255))
    if stain:
        # A brown ring where water came through from above, and the paler tile inside it
        blotch(img, (12 + seed % 9, 13 + seed % 7), 10, (186, 160, 104), 0.35, seed + 2)
        blotch(img, (12 + seed % 9, 13 + seed % 7), 6, (214, 206, 168), 0.4, seed + 3)
    return img


def troffer(state):
    lens = {"on": (255, 253, 240), "off": (168, 166, 152), "dim": (246, 196, 128), "red": (236, 58, 40)}[state]
    img = Image.new("RGBA", (S, S), (204, 200, 184, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, S - 3, S - 3], fill=lens + (255,))
    px = img.load()
    # Prismatic lens texture
    for y in range(3, S - 3):
        for x in range(3, S - 3):
            if (x + y) % 3 == 0:
                px[x, y] = shade(px[x, y], 0.95)
    d.rectangle([0, 0, S - 1, S - 1], outline=(150, 144, 118, 255))
    return img


def concrete():
    img = noise_fill(hexrgb(0x80807C), 12, 10)
    rng = random.Random(11)
    px = img.load()
    for _ in range(25):
        px[rng.randrange(S), rng.randrange(S)] = (96, 96, 94, 255)
    return img


def box(top):
    img = noise_fill(hexrgb(0xAA8052), 7, 12 if top else 13)
    d = ImageDraw.Draw(img)
    tape = (206, 180, 130, 255)
    if top:
        d.rectangle([13, 0, 18, 31], fill=tape)
        d.line([0, 16, 31, 16], fill=(140, 102, 62, 255))
    else:
        d.rectangle([13, 0, 18, 7], fill=tape)
        d.rectangle([0, 0, 31, 31], outline=(140, 102, 62, 255))
    return img


# ---------------- Level 1: concrete car park ----------------

# 5x7 bitmap glyphs for painted bay letters and signs
GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
}


def draw_glyph(img, ch, x0, y0, scale, color):
    px = img.load()
    for gy, row in enumerate(GLYPHS[ch]):
        for gx, bit in enumerate(row):
            if bit == "1":
                for sy in range(scale):
                    for sx in range(scale):
                        px[x0 + gx * scale + sx, y0 + gy * scale + sy] = color


def concrete_base(base, seed, holes=True):
    img = noise_fill(hexrgb(base), 10, seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(40):  # pores and aggregate
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = shade(px[x, y], 0.82)
    if holes:  # form-tie holes from the casting
        for (x, y) in ((6, 8), (25, 8), (6, 24), (25, 24)):
            px[x, y] = shade(px[x, y], 0.55)
            px[x + 1, y] = shade(px[x + 1, y], 0.7)
    return img


def concrete_floor(kind):
    base = {"plain": 0x5C5D59, "wet": 0x454642, "dark": 0x43484C}[kind]
    img = concrete_base(base, {"plain": 300, "wet": 301, "dark": 302}[kind], holes=False)
    px = img.load()
    if kind == "plain":
        for y in range(S):  # faint tyre-wear band
            for x in range(10, 16):
                px[x, y] = shade(px[x, y], 0.92)
    if kind == "wet":
        rng = random.Random(9)
        for _ in range(30):  # glints on standing water
            px[rng.randrange(S), rng.randrange(S)] = (120, 124, 122, 255)
    if kind == "dark":
        blotch(img, (8, 20), 9, (70, 84, 72), 0.4, 11)  # mould
    return img


def concrete_wall(damaged):
    img = concrete_base(0x8E9191, 310)
    if damaged:
        d = ImageDraw.Draw(img)
        d.line([4, 3, 10, 14, 8, 22], fill=(70, 72, 72, 255))  # cracks
        d.line([20, 0, 22, 9, 27, 13], fill=(70, 72, 72, 255))
        for x in (12, 18):  # exposed rebar with a rust run
            d.line([x, 18, x, 26], fill=(122, 74, 46, 255), width=2)
            d.line([x, 27, x, 31], fill=(150, 104, 80, 255))
    return img


def pillar(letter):
    img = concrete_base(0x9A9D9D, 320, holes=False)
    d = ImageDraw.Draw(img)
    d.line([0, 0, 0, S - 1], fill=(120, 122, 122, 255))  # arris highlight
    if letter:
        d.rectangle([7, 5, 24, 27], fill=(226, 224, 214, 255))
        draw_glyph(img, letter.upper(), 9, 6, 3, (40, 58, 96, 255))
    return img


def pillar_light():
    img = pillar(None)
    d = ImageDraw.Draw(img)
    d.rectangle([12, 0, 19, S - 1], fill=(70, 72, 72, 255))  # housing
    d.rectangle([14, 0, 17, S - 1], fill=(240, 248, 252, 255))  # tube
    return img


def concrete_ceiling():
    img = concrete_base(0x747673, 330, holes=False)
    d = ImageDraw.Draw(img)
    for y in (9, 12):  # white conduit
        d.line([0, y, S - 1, y], fill=(216, 218, 218, 255))
        d.line([0, y + 1, S - 1, y + 1], fill=(170, 172, 172, 255))
    return img


def strip_light(state):
    img = concrete_base(0x747673, 331, holes=False)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, S - 1, 21], fill=(150, 152, 150, 255))  # housing
    tube = {"on": (240, 248, 252), "off": (150, 154, 156)}[state]
    d.rectangle([0, 13, S - 1, 18], fill=tube + (255,))
    return img


def exit_sign():
    img = Image.new("RGBA", (S, S), (24, 60, 32, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(14, 30, 18, 255), width=2)
    x = 3
    for ch in "EXIT":
        draw_glyph(img, ch, x, 12, 1, (120, 255, 140, 255))
        x += 7
    return img


def crate(top):
    img = noise_fill(hexrgb(0x9C7444), 8, 340 + top)
    d = ImageDraw.Draw(img)
    for y in (10, 21):  # plank seams
        d.line([0, y, S - 1, y], fill=(110, 78, 44, 255))
    d.rectangle([0, 0, S - 1, S - 1], outline=(92, 64, 34, 255), width=3)  # frame
    if not top:
        d.line([3, 3, S - 4, S - 4], fill=(110, 80, 46, 255), width=2)  # brace
    return img


# ---------------- Level 2: utility tunnels ----------------

def tunnel_wall(variant):
    img = concrete_base(0x4F555B, 350 + len(variant))
    blotch(img, (24, 26), 10, (110, 120, 108), 0.35, 12)  # grime
    d = ImageDraw.Draw(img)
    if variant == "pipes":
        for y, h, col in ((3, 5, (107, 62, 42)), (11, 7, (226, 225, 215)), (22, 4, (90, 70, 56))):
            d.rectangle([0, y, S - 1, y + h], fill=col + (255,))
            d.line([0, y, S - 1, y], fill=shade(col, 1.15))
            d.line([0, y + h, S - 1, y + h], fill=shade(col, 0.6))
        for x in (8, 24):  # brackets
            d.rectangle([x, 2, x + 1, 27], fill=(60, 62, 64, 255))
    elif variant == "machinery":
        d.rectangle([2, 3, 29, 28], fill=(84, 92, 86, 255), outline=(40, 44, 42, 255))
        for cx in (9, 21):  # gauges
            d.ellipse([cx - 4, 7, cx + 4, 15], fill=(220, 214, 196, 255), outline=(30, 30, 30, 255))
            d.line([cx, 11, cx + 2, 8], fill=(160, 30, 20, 255))
        d.rectangle([6, 19, 25, 24], fill=(52, 56, 54, 255))  # vent slots
        for x in range(8, 25, 3):
            d.line([x, 20, x, 23], fill=(28, 30, 30, 255))
    elif variant == "brick":
        img = Image.new("RGBA", (S, S), (42, 36, 34, 255))
        d = ImageDraw.Draw(img)
        rng = random.Random(360)
        for row in range(4):
            off = 4 if row % 2 else 0
            for col in range(-1, 3):
                x0 = col * 16 + off
                c = rng.choice([(74, 58, 46), (62, 48, 40), (52, 44, 40)])
                d.rectangle([x0 + 1, row * 8 + 1, x0 + 14, row * 8 + 6], fill=c + (255,))
    return img


def tunnel_ceiling():
    img = concrete_base(0x3E4348, 370, holes=False)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 20, S - 1, 25], fill=(107, 62, 42, 255))
    return img


def cage_light(state):
    img = concrete_base(0x3E4348, 371, holes=False)
    d = ImageDraw.Draw(img)
    bulb = {"white": (255, 248, 230), "warm": (255, 176, 96), "off": (90, 86, 78)}[state]
    d.ellipse([9, 9, 22, 22], fill=bulb + (255,))
    for i in range(8, 25, 4):  # wire cage
        d.line([i, 7, i, 24], fill=(30, 30, 30, 255))
        d.line([7, i, 24, i], fill=(30, 30, 30, 255))
    return img


def pipe_tex(kind):
    """A pipe's skin, shaded like a cylinder lit from above in two 16-pixel bands: a highlight a third of the way
    down each band, falling to shadow at its bottom. Pipe models stretch one band over the pipe's height, so a
    square pipe reads as round."""
    import math
    base = {"rust": 0xA5582E, "red": 0xA8302A, "lagging": 0xE2E1D7}[kind]
    img = noise_fill(hexrgb(base), 10 if kind != "lagging" else 5, {"rust": 380, "red": 382, "lagging": 381}[kind])
    px = img.load()
    rng = random.Random({"rust": 21, "red": 22, "lagging": 23}[kind])
    for y in range(S):
        p = (y % 16 + 0.5) / 16
        light = 0.66 + 0.52 * math.exp(-((p - 0.3) / 0.2) ** 2) - 0.22 * max(0.0, (p - 0.6) / 0.4) ** 1.5
        for x in range(S):
            px[x, y] = shade(px[x, y], light)
    d = ImageDraw.Draw(img)
    if kind == "lagging":
        # Insulation wrapped in cloth: a strap every quarter, a seam along the top, a brown water stain
        for x in range(3, S, 8):
            for y in range(S):
                px[x, y] = shade(px[x, y], 0.72)
                px[x + 1, y] = shade(px[x + 1, y], 1.06)
        blotch(img, (22, 13), 5, (150, 120, 70), 0.35, 24)
        blotch(img, (9, 29), 4, (150, 120, 70), 0.3, 25)
    else:
        # A flanged joint with its bolts, and for the bare pipe, pits and streaks of rust
        for x in (14, 17):
            for y in range(S):
                px[x, y] = shade(px[x, y], 0.6)
        for x in (15, 16):
            for y in range(S):
                px[x, y] = shade(px[x, y], 1.15)
        for y in (2, 7, 12, 18, 23, 28):
            d.point((15, y), fill=(40, 34, 30, 255))
        if kind == "rust":
            for _ in range(26):
                x, y = rng.randrange(S), rng.randrange(S)
                px[x, y] = shade(px[x, y], rng.choice((0.55, 0.65, 1.3)))
            for _ in range(5):
                x, y = rng.randrange(S), rng.randrange(0, S, 16) + rng.randint(4, 9)
                for k in range(rng.randint(3, 6)):
                    if y + k < S:
                        px[x, y + k] = shade(px[x, y + k], 0.72)
    return img


def drum(top):
    img = noise_fill(hexrgb(0x2E4A6E), 8, 390 + top)
    d = ImageDraw.Draw(img)
    if top:
        d.ellipse([3, 3, 28, 28], outline=(20, 34, 52, 255))
        d.ellipse([20, 8, 24, 12], fill=(30, 30, 30, 255))
    else:
        for y in (8, 22):
            d.line([0, y, S - 1, y], fill=(20, 34, 52, 255), width=2)
        blotch(img, (10, 28), 7, (110, 70, 40), 0.6, 13)  # rust
    return img


def props_textures():
    """Small textures for 3D props: metal, tubes, valve, cabinet front, hazard sign, floor lines."""
    save(noise_fill(hexrgb(0x8C9196), 8, 400), "block/props/metal.png")
    save(noise_fill(hexrgb(0x3A3E42), 6, 401), "block/props/metal-dark.png")
    save(noise_fill(hexrgb(0xA8261E), 10, 402), "block/props/valve.png")
    save(noise_fill(hexrgb(0xF4F8FA), 2, 403), "block/props/tube-white.png")
    save(noise_fill(hexrgb(0xFFB868), 3, 404), "block/props/tube-warm.png")
    save(noise_fill(hexrgb(0x8E9294), 4, 405), "block/props/tube-off.png")
    save(noise_fill(hexrgb(0xD8DADA), 3, 406), "block/props/conduit.png")

    front = noise_fill(hexrgb(0x55605A), 6, 407)
    d = ImageDraw.Draw(front)
    d.rectangle([2, 2, S - 3, S - 3], outline=(30, 34, 32, 255))
    for x in range(6, 27, 3):  # vent slots
        d.line([x, 20, x, 27], fill=(28, 30, 30, 255))
    d.rectangle([6, 6, 12, 10], fill=(180, 40, 30, 255))  # warning label
    d.rectangle([18, 6, 26, 10], fill=(220, 214, 196, 255))
    save(front, "block/props/cabinet-front.png")

    sign = concrete_base(0x4F555B, 408)
    d = ImageDraw.Draw(sign)
    d.rectangle([6, 8, 25, 23], fill=(232, 192, 40, 255))
    for k in range(-16, 32, 6):  # hazard stripes
        d.line([6 + k, 23, 6 + k + 15, 8], fill=(30, 30, 30, 255), width=2)
    d.rectangle([6, 8, 25, 23], outline=(30, 30, 30, 255))
    sign = sign.crop((0, 0, S, S))
    save(sign, "block/level2/tunnelwall-warning.png")

    for axis in ("ns", "we"):
        img = concrete_floor("plain")
        d = ImageDraw.Draw(img)
        if axis == "ns":
            d.rectangle([15, 0, 16, S - 1], fill=(222, 222, 210, 255))
        else:
            d.rectangle([0, 15, S - 1, 16], fill=(222, 222, 210, 255))
        save(img, f"block/level1/concretefloor-line{axis}.png")


def parking_textures():
    for axis in ("we", "ns"):
        img = concrete_floor("plain")
        d = ImageDraw.Draw(img)
        if axis == "we":
            d.rectangle([0, 14, S - 1, 17], fill=(222, 186, 40, 255))
        else:
            d.rectangle([14, 0, 17, S - 1], fill=(222, 186, 40, 255))
        save(img, f"block/level1/concretefloor-dash{axis}.png")

    stop = concrete_base(0x9A9D9D, 420, holes=False)
    d = ImageDraw.Draw(stop)
    for x in range(0, S, 8):  # yellow-and-grey striped wheel stop
        d.rectangle([x, 0, x + 3, S - 1], fill=(214, 180, 50, 255))
    save(stop, "block/level1/wheelstop.png")

    for name, colour in (("red", 0x8E2222), ("blue", 0x2A4A7E), ("white", 0xD8D8D2), ("black", 0x26282A)):
        img = noise_fill(hexrgb(colour), 6, 430 + len(name))
        blotch(img, (8, 24), 7, (90, 80, 70), 0.35, 22)  # dust and grime
        save(img, f"block/level1/car-{name}.png")
    glass = noise_fill(hexrgb(0x1C2428), 4, 440)
    d = ImageDraw.Draw(glass)
    d.line([4, 2, 14, 12], fill=(70, 84, 92, 255), width=2)  # reflection
    save(glass, "block/level1/car-glass.png")


def text_img(img, text, box, color, size):
    """Draws centred text into the given box, rendered large and scaled down for crisp pixels."""
    from PIL import ImageFont
    x0, y0, x1, y1 = box
    scale = 4
    big = Image.new("RGBA", ((x1 - x0) * scale, (y1 - y0) * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    font = ImageFont.load_default(size=size * scale)
    w, h = d.textbbox((0, 0), text, font=font)[2:]
    d.text(((big.width - w) / 2, (big.height - h) / 2 - scale), text, font=font, fill=color)
    small = big.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.alpha_composite(small, (x0, y0))


def level3_textures():
    # Two-tone glazed structural tile: darker ochre glaze below, lighter above, dark grout lines
    img = noise_fill(hexrgb(0x8B7056), 6, 500)
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=(63, 46, 21, 255))
    for row in range(4):
        off = 8 if row % 2 else 0
        for x in range(off, S + 16, 16):
            d.line([x % S, row * 8, x % S, row * 8 + 7], fill=(63, 46, 21, 255))
    for y in range(0, 16):
        for x in range(S):
            r, g, b, a = img.getpixel((x, y))
            if (y % 8) != 0:
                img.putpixel((x, y), (clamp(r * 0.88), clamp(g * 0.85), clamp(b * 0.75), a))
    save(img, "block/level3/l3wall-glazed.png")

    img = Image.new("RGBA", (S, S), (60, 30, 18, 255))
    d = ImageDraw.Draw(img)
    rng = random.Random(501)
    for row in range(8):
        off = 4 if row % 2 else 0
        for col in range(-1, 5):
            c = rng.choice([(118, 39, 5), (112, 56, 26), (96, 40, 20), (130, 60, 30)])
            d.rectangle([col * 8 + off + 1, row * 4 + 1, col * 8 + off + 7, row * 4 + 3], fill=c + (255,))
    save(img, "block/level3/l3wall-brick.png")

    img = noise_fill(hexrgb(0x36311A), 7, 502)
    d = ImageDraw.Draw(img)
    for row in range(2):
        off = 8 if row % 2 else 0
        d.line([0, row * 16, S - 1, row * 16], fill=(28, 25, 12, 255))
        for x in range(off, S + 16, 16):
            d.line([x % S, row * 16, x % S, row * 16 + 15], fill=(28, 25, 12, 255))
    save(img, "block/level3/l3wall-cinder.png")

    img = noise_fill(hexrgb(0x8C7F6E), 9, 503)
    blotch(img, (20, 10), 8, (76, 72, 56), 0.4, 504)
    save(img, "block/level3/dustyfloor.png")
    img = noise_fill(hexrgb(0x5E594F), 8, 505)
    blotch(img, (12, 18), 10, (61, 53, 41), 0.5, 506)
    save(img, "block/level3/plasterceiling.png")
    save(noise_fill(hexrgb(0x1E1E20), 5, 507), "block/level3/cable.png")
    img = noise_fill(hexrgb(0x5A6458), 6, 508)
    d = ImageDraw.Draw(img)
    for x in range(2, S, 4):
        d.line([x, 0, x, S - 1], fill=(70, 78, 70, 255))
    d.rectangle([10, 10, 21, 16], fill=(220, 200, 40, 255))  # warning label
    save(img, "block/level3/transformer.png")
    save(noise_fill(hexrgb(0x8A5A3A), 8, 509), "block/level3/insulator.png")
    img = noise_fill(hexrgb(0x7C8084), 5, 510)
    d = ImageDraw.Draw(img)
    for i in range(4):  # breakers
        d.rectangle([4 + i * 6, 8, 7 + i * 6, 14], fill=(30, 30, 30, 255))
        d.rectangle([5 + i * 6, 9, 6 + i * 6, 11], fill=(200, 200, 200, 255))
    d.rectangle([6, 20, 25, 24], fill=(180, 30, 25, 255))
    save(img, "block/level3/panel.png")
    img = Image.new("RGBA", (S, S), (40, 42, 44, 255))
    d = ImageDraw.Draw(img)
    for i in range(0, S, 4):
        d.line([i, 0, i, S - 1], fill=(120, 124, 128, 255))
        d.line([0, i, S - 1, i], fill=(120, 124, 128, 255))
    save(img, "block/level3/fan.png")
    img = noise_fill(hexrgb(0x98948F), 6, 511)
    blotch(img, (8, 24), 7, (44, 33, 21), 0.7, 512)
    blotch(img, (26, 6), 5, (44, 33, 21), 0.6, 513)
    save(img, "block/level3/bars.png")
    img = noise_fill(hexrgb(0x2E2C2A), 6, 514)
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], outline=(70, 66, 60, 255), width=2)
    for i in range(6, 27, 5):
        d.line([i, 6, i, 25], fill=(60, 56, 52, 255))
    save(img, "block/level3/manhole.png")
    img = Image.new("RGBA", (S, S), (255, 248, 222, 255))  # daylight through a window
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(120, 110, 90, 255), width=2)
    d.line([16, 0, 16, S - 1], fill=(120, 110, 90, 255), width=2)
    d.line([0, 16, S - 1, 16], fill=(120, 110, 90, 255), width=2)
    save(img, "block/level3/windowglow.png")
    for i, number in enumerate(("447", "112", "318", "905", "563", "274", "781", "036")):
        img = Image.new("RGBA", (S, S), (236, 234, 226, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=(90, 90, 90, 255))
        text_img(img, number, (2, 4, 30, 18), (20, 20, 20, 255), 11)
        for y in (21, 25):  # illegible text beneath
            d.line([6, y, 26, y], fill=(120, 120, 120, 255))
        save(img, f"block/level3/roomsign-{i}.png")


def level4_textures():
    save(noise_fill(hexrgb(0xD8D5D4), 4, 520), "block/level4/officewall.png")
    img = noise_fill(hexrgb(0x5A6068), 8, 521)  # a rainy, foggy nowhere
    rng = random.Random(522)
    px = img.load()
    for _ in range(60):
        x, y = rng.randrange(S), rng.randrange(S - 6)
        for k in range(rng.randint(3, 6)):
            px[x, y + k] = (150, 160, 172, 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(40, 42, 46, 255), width=2)
    d.line([16, 0, 16, S - 1], fill=(40, 42, 46, 255), width=1)
    save(img, "block/level4/officewindow.png")
    img = Image.new("RGBA", (S, S), (180, 210, 220, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(110, 114, 118, 255), width=2)
    save(img, "block/level4/officeglass.png")
    save(noise_fill(hexrgb(0x85837D), 7, 523), "block/level4/officecarpet-plain.png")
    save(noise_fill(hexrgb(0x6E6C67), 7, 523), "block/level4/officecarpet-ghost.png")
    img = noise_fill(hexrgb(0xD8D4CF), 3, 524)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(150, 148, 144, 255))
    d.line([0, 15, S - 1, 15], fill=(150, 148, 144, 255))  # 2x4 tiles
    save(img, "block/level4/officeceiling.png")
    for state, lens in (("on", (252, 252, 248)), ("off", (150, 150, 146))):
        img = Image.new("RGBA", (S, S), (200, 198, 194, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([2, 2, S - 3, S - 3], fill=lens + (255,))
        for x in range(4, S - 3, 3):
            d.line([x, 3, x, S - 4], fill=shade(lens, 0.93))
        save(img, f"block/level4/officelight-{state}.png")
    save(noise_fill(hexrgb(0x575A62), 6, 525), "block/level4/partition.png")
    save(noise_fill(hexrgb(0xB49C78), 5, 526), "block/level4/laminate.png")
    save(noise_fill(hexrgb(0xC9C2AE), 4, 527), "block/level4/crt.png")
    img = noise_fill(hexrgb(0x16241A), 4, 528)
    ImageDraw.Draw(img).text((3, 4), "C:\\>_", fill=(80, 200, 100, 255))
    save(img, "block/level4/crt-screen.png")
    save(noise_fill(hexrgb(0x33363C), 5, 529), "block/level4/chairfabric.png")
    img = noise_fill(hexrgb(0x8E9296), 4, 530)
    d = ImageDraw.Draw(img)
    for y in (10, 21):
        d.line([0, y, S - 1, y], fill=(60, 62, 66, 255))
    save(img, "block/level4/filing.png")
    img = noise_fill(hexrgb(0xA82820), 6, 531)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 21, 26], fill=(30, 34, 40, 255))
    for row in range(4):
        for col in range(3):
            d.rectangle([5 + col * 6, 5 + row * 6, 8 + col * 6, 9 + row * 6], fill=(236, 228, 205, 255))  # bottles
    d.rectangle([24, 8, 28, 16], fill=(40, 40, 40, 255))
    save(img, "block/level4/vending.png")
    save(noise_fill(hexrgb(0xE6E6E2), 3, 532), "block/level4/cooler.png")
    save(noise_fill(hexrgb(0x9CC8E6), 5, 533), "block/level4/coolerbottle.png")
    for part in ("lower", "upper"):
        img = noise_fill(hexrgb(0x9EA4A8), 4, 534)
        d = ImageDraw.Draw(img)
        d.line([15, 0, 15, S - 1], fill=(50, 52, 56, 255), width=2)
        if part == "upper":
            d.rectangle([12, 2, 19, 7], fill=(40, 40, 40, 255))
            d.text((13, 1), "^", fill=(240, 200, 80, 255))
        save(img, f"block/level4/elevatordoor-{part}.png")


def level5_textures():
    # Hotel walls: mahogany wainscot, red damask panel in a gilt frame on cream, cream frieze with a cornice
    img = noise_fill(hexrgb(0x452518), 6, 540)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 4, 28, 27], outline=(115, 74, 48, 255), width=2)
    d.line([0, 1, S - 1, 1], fill=(140, 100, 60, 255))
    save(img, "block/level5/hotelwall-wainscot.png")
    img = noise_fill(hexrgb(0xD9C3A0), 4, 541)
    d = ImageDraw.Draw(img)
    d.rectangle([4, 2, 27, 29], fill=(94, 6, 4, 255), outline=(196, 160, 72, 255), width=2)
    for y in range(6, 28, 6):  # damask motif
        for x in range(8, 26, 6):
            d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(130, 30, 16, 255))
    save(img, "block/level5/hotelwall-panel.png")
    img = noise_fill(hexrgb(0xD9C3A0), 4, 542)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 5], fill=(232, 214, 180, 255))
    d.line([0, 6, S - 1, 6], fill=(160, 120, 70, 255))
    save(img, "block/level5/hotelwall-frieze.png")

    img = noise_fill(hexrgb(0x5E260C), 6, 543)
    d = ImageDraw.Draw(img)
    for cx, cy in ((8, 8), (24, 24), (24, 8), (8, 24)):  # gold medallions
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=(196, 150, 60, 255))
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(160, 40, 20, 255))
    save(img, "block/level5/hotelcarpet-damask.png")
    save(noise_fill(hexrgb(0x2E0C0A), 5, 544), "block/level5/hotelcarpet-maroon.png")
    img = noise_fill(hexrgb(0xB5874E), 6, 545)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, S - 3, S - 3], outline=(150, 40, 24, 255))
    save(img, "block/level5/hotelcarpet-lobby.png")
    img = noise_fill(hexrgb(0x4E2C1C), 6, 546)
    d = ImageDraw.Draw(img)
    for y in range(0, S, 6):
        d.line([0, y, S - 1, y], fill=(36, 20, 12, 255))
    save(img, "block/level5/hotelwood.png")
    save(noise_fill(hexrgb(0xE2D2B4), 3, 547), "block/level5/hotelceiling-cream.png")
    img = noise_fill(hexrgb(0x9E5720), 6, 548)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 6], fill=(221, 163, 65, 255))
    d.rectangle([0, 25, S - 1, S - 1], fill=(78, 23, 6, 255))
    for x in range(4, S, 8):
        d.rectangle([x, 10, x + 3, 20], fill=(180, 60, 30, 255))
    save(img, "block/level5/hotelceiling-beams.png")
    # Red faux marble (the lobby columns): deep oxblood with pale, wandering veins
    save(texlib.marble((150, 52, 34), (214, 150, 118), 549, mottle=0.12), "block/level5/marble.png")
    img = noise_fill(hexrgb(0x8C6E48), 9, 551)
    blotch(img, (16, 28), 12, (60, 44, 26), 0.5, 552)
    save(img, "block/level5/plaster.png")

    img = noise_fill(hexrgb(0x452518), 5, 553)
    d = ImageDraw.Draw(img)
    d.rectangle([4, 3, 27, 28], outline=(115, 74, 48, 255), width=2)
    d.rectangle([24, 10, 27, 13], fill=(196, 160, 72, 255))  # knob
    save(img, "block/level5/hoteldoor-lower.png")
    for i, number in enumerate(("214", "308", "117", "421", "236", "509", "382", "113")):
        img = noise_fill(hexrgb(0x452518), 5, 554)
        d = ImageDraw.Draw(img)
        d.rectangle([4, 3, 27, 31], outline=(115, 74, 48, 255), width=2)
        d.rectangle([9, 8, 22, 15], fill=(200, 164, 80, 255))
        text_img(img, number, (9, 8, 23, 16), (60, 36, 10, 255), 7)
        save(img, f"block/level5/hoteldoor-upper{i}.png")
    for part in ("lower", "upper"):
        img = Image.new("RGBA", (S, S), (40, 24, 14, 255))
        d = ImageDraw.Draw(img)
        for k in range(-S, S, 6):  # copper lattice
            d.line([k, 0, k + S, S], fill=(184, 115, 51, 255))
            d.line([k + S, 0, k, S], fill=(184, 115, 51, 255))
        d.rectangle([0, 0, S - 1, S - 1], outline=(150, 90, 40, 255), width=2)
        save(img, f"block/level5/cagedoor-{part}.png")
    img = noise_fill(hexrgb(0xD9C3A0), 4, 555)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 9, 28, 22], fill=(30, 30, 30, 255))
    text_img(img, "STAFF", (3, 9, 29, 16), (230, 200, 120, 255), 6)
    text_img(img, "ONLY", (3, 15, 29, 22), (230, 200, 120, 255), 6)
    save(img, "block/level5/staffsign.png")
    img = noise_fill(hexrgb(0xB8BCC0), 4, 556)
    text_img(img, "THE", (0, 0, S, 11), (40, 30, 20, 255), 7)
    text_img(img, "BEVERLY", (0, 10, S, 21), (40, 30, 20, 255), 7)
    text_img(img, "ROOM", (0, 20, S, 31), (40, 30, 20, 255), 7)
    save(img, "block/level5/beverly.png")
    save(portrait(557), "block/level5/portrait.png")
    save(noise_fill(hexrgb(0xC9A040), 8, 558), "block/level5/gilt.png")
    save(noise_fill(hexrgb(0xB08A3C), 6, 559), "block/level5/brass.png")
    save(noise_fill(hexrgb(0xFFF0C8), 3, 560), "block/level5/domeglass.png")
    save(noise_fill(hexrgb(0xF0F4FF), 6, 561), "block/level5/crystal.png")
    save(noise_fill(hexrgb(0x5A2E1A), 5, 562), "block/level5/mahogany.png")
    save(noise_fill(hexrgb(0xEDE8DC), 3, 563), "block/level5/linen.png")
    save(noise_fill(hexrgb(0x7A1A14), 5, 564), "block/level5/blanket.png")
    save(noise_fill(hexrgb(0x6E1420), 6, 565), "block/level5/velvet.png")
    save(noise_fill(hexrgb(0x3E6A2A), 10, 566), "block/level5/palmleaf.png")
    save(noise_fill(hexrgb(0x8A5A3A), 6, 567), "block/level5/pot.png")
    save(noise_fill(hexrgb(0x1E5A30), 5, 568), "block/level5/felt.png")
    save(noise_fill(hexrgb(0xEEE6D0), 3, 569), "block/level5/mahjong.png")
    img = noise_fill(hexrgb(0x654729), 10, 570)
    d = ImageDraw.Draw(img)
    for y in range(4, S, 9):
        for x in range(3, S, 7):
            d.point((x, y), fill=(175, 146, 93, 255))  # rivets
    save(img, "block/level5/boiler.png")
    img = noise_fill(hexrgb(0xFF8A2A), 18, 571)
    save(img, "block/level5/fire.png")
    save(noise_fill(hexrgb(0xE8C890), 4, 572), "block/level5/lampshade.png")


def level_textures():
    props_textures()
    level3_textures()
    level4_textures()
    level5_textures()
    for k in ("plain", "wet", "dark"):
        save(concrete_floor(k), f"block/level1/concretefloor-{k}.png")
    save(concrete_wall(False), "block/level1/concretewall-plain.png")
    save(concrete_wall(True), "block/level1/concretewall-damaged.png")
    save(pillar(None), "block/level1/concretepillar-plain.png")
    for letter in "abcdef":
        save(pillar(letter), f"block/level1/concretepillar-{letter}.png")
    save(pillar_light(), "block/level1/pillarlight.png")
    save(concrete_ceiling(), "block/level1/concreteceiling.png")
    save(exit_sign(), "block/level1/exitsign.png")
    save(crate(1), "block/level1/crate-top.png")
    save(crate(0), "block/level1/crate-side.png")
    for v in ("plain", "machinery", "brick"):
        save(tunnel_wall(v), f"block/level2/tunnelwall-{v}.png")
    save(tunnel_ceiling(), "block/level2/tunnelceiling.png")
    save(pipe_tex("rust"), "block/level2/pipe-rust.png")
    save(pipe_tex("lagging"), "block/level2/pipe-lagging.png")
    save(pipe_tex("red"), "block/level2/pipe-red.png")
    parking_textures()
    save(drum(1), "block/level2/oildrum-top.png")
    save(drum(0), "block/level2/oildrum-side.png")


# ---------------- Items (16x16 atlases, layout matches the shapes) ----------------

def almond_water():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 7, 15], fill=(236, 228, 205, 255))
    d.rectangle([0, 5, 7, 10], fill=(196, 160, 104, 255))
    d.line([0, 7, 7, 7], fill=(120, 84, 44, 255))
    d.line([1, 0, 1, 15], fill=(250, 248, 240, 255))
    d.rectangle([8, 0, 11, 3], fill=(225, 232, 236, 255))
    d.rectangle([12, 0, 15, 3], fill=(60, 110, 170, 255))
    d.rectangle([8, 8, 15, 15], fill=(236, 228, 205, 255))
    return img


def crackers():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 11], fill=(196, 52, 40, 255))
    d.rectangle([3, 3, 12, 8], fill=(232, 196, 120, 255))
    for x in (5, 8, 11):
        d.point((x, 5), fill=(170, 130, 70, 255))
    d.rectangle([0, 12, 15, 15], fill=(170, 40, 32, 255))
    return img


def canned_beans():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 11], fill=(176, 180, 186, 255))
    d.rectangle([0, 3, 15, 8], fill=(214, 120, 40, 255))
    d.rectangle([5, 4, 10, 7], fill=(150, 70, 30, 255))
    d.rectangle([0, 12, 15, 15], fill=(150, 154, 160, 255))
    return img


# ---------------- Mod icon ----------------

def mod_icon():
    s = 128
    img = Image.new("RGBA", (s, s), (40, 36, 20, 255))
    d = ImageDraw.Draw(img)
    vp = (64, 60)
    d.polygon([(0, 0), (s, 0), vp], fill=hexrgb(0xD6CFA6))
    d.polygon([(0, s), (s, s), vp], fill=hexrgb(0xA8956A))
    d.polygon([(0, 0), (0, s), vp], fill=hexrgb(0xD7D48A))
    d.polygon([(s, 0), (s, s), vp], fill=hexrgb(0xC4C07C))
    for t in (0.0, 0.45, 0.7):
        y = int(t * vp[1])
        half = int((1 - t) * 18)
        d.rectangle([64 - half, y + 2, 64 + half, y + 4 + int((1 - t) * 4)], fill=(255, 253, 235, 255))
    d.rectangle([56, 48, 72, 72], fill=(30, 26, 14, 255))
    return img


if __name__ == "__main__":
    wallpapers()
    for v in ("normal", "stained", "soaked"):
        save(carpet(v), f"block/carpet-{v}.png")
    save(carpet_threadbare(), "block/carpet-threadbare.png")
    salvage_items()
    save(ceiling_tile(), "block/ceilingtile.png")
    save(ceiling_tile(8), "block/ceilingtile2.png")
    save(ceiling_tile(9), "block/ceilingtile3.png")
    save(ceiling_tile(11, stain=True), "block/ceilingtile-stain.png")
    for st in ("on", "off", "dim", "red"):
        save(troffer(st), f"block/fluorescentlight-{st}.png")
    save(concrete(), "block/concrete.png")
    save(box(True), "block/supplybox-top.png")
    save(box(False), "block/supplybox-side.png")
    level_textures()
    save(almond_water(), "item/almondwater.png")
    save(crackers(), "item/crackers.png")
    save(canned_beans(), "item/cannedbeans.png")
    mod_icon().save(os.path.join(ROOT, "modicon.png"))
    print("textures written")
