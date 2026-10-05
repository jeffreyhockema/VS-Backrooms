"""Textures for the detail props, signs, doors and floors added to Levels 1, 3, 4 and 5 (32x32, in block/detail/).

Pictures meant to fill a face (signs, screens, paintings) are drawn edge to edge; materials are noise with a few
features so they keep their scale on boxes of any size.
"""
import math
import random

import texlib

from PIL import Image, ImageDraw

from detail_kit import T, seed_of

S = 32


def rgb(h, a=255):
    return T.hexrgb(h) + (a,)


def noise(color, n=5, key="x"):
    return T.noise_fill(T.hexrgb(color), n, seed_of(key))


def save(img, name):
    T.save(img, f"block/detail/{name}.png")


def flat(name, color, n=5):
    save(noise(color, n, name), name)


def text(img, s, box, color, size):
    T.text_img(img, s, box, rgb(color) if isinstance(color, int) else color, size)


def stripes(img, c1, c2, width=4, box=None, diagonal=True):
    x0, y0, x1, y1 = box or (0, 0, S, S)
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = ((x + y) if diagonal else x) // width
            px[x, y] = c1 if k % 2 == 0 else c2


def block_wall(base, mortar, key, rows=4):
    """Painted concrete block: courses of 16x8 px blocks, staggered."""
    img = noise(base, 3, key)
    d = ImageDraw.Draw(img)
    h = S // rows
    for r in range(rows):
        y = r * h
        d.line([0, y, S - 1, y], fill=rgb(mortar))
        off = 8 if r % 2 else 0
        for x in range(off, S + 16, 16):
            d.line([x % S, y, x % S, y + h - 1], fill=rgb(mortar))
    return img


def grime(img, key, strength=0.25, color=(90, 86, 70)):
    rng = random.Random(seed_of(key))
    T.blotch(img, (rng.randrange(S), S - 4), rng.randint(6, 10), color, strength, seed_of(key) + 1)
    return img


# ---------------- Shared ----------------

def shared():
    flat("steel", 0xB4B8BC, 4)
    flat("steeldark", 0x5C6064, 4)
    flat("blackmetal", 0x1C1E21, 3)
    flat("copper", 0xB8733A, 8)
    flat("wood", 0x8A6440, 6)
    flat("wooddark", 0x4A3220, 5)
    flat("paper", 0xF2EEE2, 2)
    flat("string", 0xC8B48C, 4)
    flat("exithousing", 0xE4E2DA, 2)
    flat("redmetal", 0xB42820, 6)
    flat("orange", 0xE8661C, 5)
    flat("white", 0xEEEEEA, 2)
    flat("rubber", 0x222224, 3)

    img = Image.new("RGBA", (S, S), rgb(0xF4F2EC))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xB8B6AE), width=1)
    text(img, "EXIT", (6, 9, 27, 23), 0xD8141E, 12)
    for x, sgn in ((2, 1), (29, -1)):  # chevron arrows either side
        d.line([x + 2 * sgn, 13, x, 16, x + 2 * sgn, 19], fill=rgb(0xD8141E), width=1)
    save(img, "exitface")

    img = Image.new("RGBA", (S, S))
    stripes(img, rgb(0xE8B81C), rgb(0x1C1C1C), 4)
    save(img, "hazard")


# ---------------- Level 1 ----------------

def level1():
    wall = grime(block_wall(0xE4E2DA, 0xC2C0B8, "whiteblock"), "whiteblock", 0.18)
    save(wall, "whiteblock")
    base = wall.copy()
    d = ImageDraw.Draw(base)
    base.paste(grime(block_wall(0x55595C, 0x45494C, "whiteblockbase"), "wbb", 0.2).crop((0, 16, S, S)), (0, 16))
    d.rectangle([0, 14, S - 1, 15], fill=rgb(0xE0B624))
    save(base, "whiteblock-base")
    lintel = wall.copy()
    ImageDraw.Draw(lintel).rectangle([0, 28, S - 1, S - 1], fill=rgb(0x2A2C2E))
    save(lintel, "whiteblock-lintel")
    img = noise(0x707370, 4, "l1hallfloor")
    rng = random.Random(3)
    for _ in range(6):
        x, y = rng.randrange(S - 6), rng.randrange(S)
        ImageDraw.Draw(img).line([x, y, x + rng.randint(3, 6), y], fill=rgb(0x5E605C))  # scuffs
    save(img, "l1hallfloor")

    for part in ("lower", "upper"):
        img = noise(0x1E2022, 3, "metaldoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x55585C), width=2)  # steel frame
        if part == "lower":
            d.rectangle([4, 18, 27, 30], outline=rgb(0x2E3134))
            d.rectangle([5, 2, 26, 4], fill=rgb(0xA8ACB0))  # push bar
            d.rectangle([24, 1, 26, 5], fill=rgb(0x7C8084))
        else:
            d.rectangle([9, 5, 22, 20], fill=rgb(0x1A2226))  # wired glass
            for k in range(-12, 16, 4):
                d.line([9 + max(0, k), 5 + max(0, -k), 22, 18 - k], fill=rgb(0x4A5258))
            d.rectangle([7, 24, 24, 29], fill=rgb(0xE0B624))
            text(img, "NO ENTRY", (7, 24, 25, 30), 0x1A1A1A, 5)
        save(img, f"metaldoor-{part}")
    img = noise(0x1E2022, 3, "firedoor")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, S - 2], outline=rgb(0x34373A))
    d.rectangle([4, 20, 27, 29], outline=rgb(0x2A2D30))
    save(img, "firedoor")

    img = T.concrete_base(0x9A9D9D, 320, holes=False)
    stripes(img, rgb(0xE0B020), rgb(0x1E1E1E), 4, (0, 20, S, S))
    save(img, "pillarbase")

    floor = T.concrete_floor("plain")
    img = floor.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([14, 12, 17, 28], fill=rgb(0xE8E8E0))  # arrow pointing north
    d.polygon([(9, 13), (22, 13), (15.5, 3)], fill=rgb(0xE8E8E0))
    save(img, "parkarrow")
    img = floor.copy()
    T.blotch(img, (16, 18), 9, (24, 24, 22), 0.75, 61)
    T.blotch(img, (10, 10), 4, (30, 28, 26), 0.6, 62)
    save(img, "parkoil")
    img = floor.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 23, 23], fill=rgb(0x2A2C2C), outline=rgb(0x7A7C7A))
    for x in range(10, 23, 3):
        d.line([x, 9, x, 22], fill=rgb(0x5E605E))
    save(img, "parkdrain")
    img = Image.new("RGBA", (S, S))
    stripes(img, rgb(0xE8C020), rgb(0x202020), 8, diagonal=False)
    save(img, "speedbump")

    flat("conewhite", 0xF0F0EA, 2)
    img = Image.new("RGBA", (S, S), rgb(0xF2C81C))
    d = ImageDraw.Draw(img)
    text(img, "CAUTION", (1, 2, 31, 10), 0x111111, 6)
    d.polygon([(16, 12), (26, 28), (6, 28)], outline=rgb(0x111111))
    d.ellipse([14, 16, 17, 19], fill=rgb(0x111111))  # slipping figure
    d.line([15, 19, 13, 24, 18, 26], fill=rgb(0x111111))
    save(img, "wetfloor")
    flat("paybody", 0x8E9296, 4)
    img = noise(0xC8A020, 4, "payface")
    d = ImageDraw.Draw(img)
    d.rectangle([5, 3, 26, 12], fill=rgb(0x1C3020))
    text(img, "PAY HERE", (5, 4, 27, 11), 0x7CE090, 4)
    d.rectangle([7, 16, 15, 18], fill=rgb(0x111111))  # ticket slot
    for r in range(3):
        for c in range(3):
            d.rectangle([18 + c * 3, 15 + r * 3, 19 + c * 3, 16 + r * 3], fill=rgb(0xDDDDDD))
    d.rectangle([8, 24, 23, 27], fill=rgb(0x222222))  # coin return
    save(img, "payface")
    img = noise(0x4A4E52, 4, "trashgrey")
    d = ImageDraw.Draw(img)
    for x in range(2, S, 6):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A3E42))
    save(img, "trashgrey")
    img = noise(0xB89C6C, 6, "palletwood")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x8A7048))
    save(img, "palletwood")
    img = noise(0xA87A48, 5, "benchtop")
    for y in range(0, S, 4):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x8E643A))
    save(img, "benchtop")
    img = noise(0x9A7A54, 4, "pegboard")
    d = ImageDraw.Draw(img)
    for y in range(2, S, 4):
        for x in range(2, S, 4):
            d.point((x, y), fill=rgb(0x4A3A28))
    d.rectangle([4, 6, 6, 18], fill=rgb(0x6A3A20))  # hammer handle
    d.rectangle([2, 4, 9, 7], fill=rgb(0x55585C))
    d.rectangle([14, 5, 15, 20], fill=rgb(0xC03020))  # screwdriver
    d.rectangle([20, 4, 27, 6], fill=rgb(0x8A8E92))  # wrench
    d.rectangle([22, 6, 24, 22], fill=rgb(0x8A8E92))
    d.ellipse([17, 22, 29, 30], outline=rgb(0x2A5A2A), width=2)  # coiled cord
    save(img, "pegboard")
    img = noise(0xB0261C, 5, "toolboxred")
    d = ImageDraw.Draw(img)
    d.line([0, 11, S - 1, 11], fill=rgb(0x701812))
    d.rectangle([5, 9, 8, 13], fill=rgb(0xC0C4C8))
    d.rectangle([23, 9, 26, 13], fill=rgb(0xC0C4C8))
    save(img, "toolboxred")
    img = noise(0xC8A472, 6, "plywood")
    rng = random.Random(seed_of("plywood"))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        y = rng.randrange(S)
        d.arc([rng.randint(-20, 10), y - 6, rng.randint(20, 50), y + 6], 0, 180, fill=rgb(0xA8844E))
    save(img, "plywood")
    for name, c in (("tarp", 0x2A5CA8), ("tarporange", 0xD8641C)):
        img = noise(c, 6, name)
        d = ImageDraw.Draw(img)
        for x in range(0, S, 8):
            d.line([x, 0, x, S - 1], fill=T.shade(T.hexrgb(c), 0.85))
        d.ellipse([2, 2, 4, 4], outline=rgb(0xC0C0C0))  # grommet
        save(img, name)
    img = noise(0x3E5A2E, 5, "bedroll")
    for y in range(0, S, 6):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x2E4422))
    save(img, "bedroll")
    flat("bedrollpillow", 0x8C8070, 4)
    img = noise(0xFFC060, 4, "lanternglass")
    ImageDraw.Draw(img).rectangle([12, 0, 19, S - 1], fill=rgb(0xFFF0C0))
    save(img, "lanternglass")
    img = noise(0x6A3A22, 10, "burnbarrel")
    d = ImageDraw.Draw(img)
    for x, y in ((6, 10), (16, 8), (26, 11), (11, 20), (22, 21)):
        d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=rgb(0xE86A18))
    save(img, "burnbarrel")
    img = noise(0xC8401C, 30, "embers")
    rng = random.Random(9)
    for _ in range(30):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(0xFFD060))
    save(img, "embers")
    flat("hospitalsheet", 0xDCE6EC, 3)
    flat("hospitalframe", 0xE8E8E2, 3)
    flat("tabletop", 0xD2C6A8, 3)
    flat("foldsteel", 0x6E7276, 4)
    flat("medcab", 0xECECE6, 2)
    img = noise(0xECECE6, 2, "medcabfront")
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, S - 1], fill=rgb(0xB0B0AA))
    d.rectangle([9, 8, 13, 20], fill=rgb(0xC8201C))
    d.rectangle([5, 12, 17, 16], fill=rgb(0xC8201C))
    d.rectangle([19, 12, 20, 18], fill=rgb(0x8A8A86))
    save(img, "medcabfront")

    img = noise(0x8C9094, 3, "powerbox")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x5A5E62), width=2)
    d.polygon([(16, 6), (24, 20), (8, 20)], fill=rgb(0xE8C020), outline=rgb(0x111111))
    d.line([16, 10, 14, 15, 18, 14, 16, 19], fill=rgb(0x111111))
    d.rectangle([22, 24, 26, 27], fill=rgb(0x3A3E42))
    save(img, "powerbox")
    img = noise(0x7E8286, 3, "breaker")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x4E5256), width=2)
    for r in range(6):
        for c in (6, 18):
            d.rectangle([c, 4 + r * 4, c + 7, 6 + r * 4], fill=rgb(0x222426))
            d.rectangle([c + (2 if (r + c) % 3 else 4), 4 + r * 4, c + (3 if (r + c) % 3 else 5), 6 + r * 4], fill=rgb(0xD8D8D0))
    save(img, "breaker")
    img = noise(0xE4DCC4, 2, "outlet")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xB8B09A))
    for y in (6, 19):
        d.rectangle([10, y, 11, y + 4], fill=rgb(0x2A2A2A))
        d.rectangle([20, y, 21, y + 4], fill=rgb(0x2A2A2A))
        d.ellipse([14, y + 5, 17, y + 7], fill=rgb(0x2A2A2A))
    save(img, "outlet")

    # Crude drawings: paper hung on a string, and one old canvas whose eyes seem to follow you
    img = noise(0xEDE6D2, 3, "painting0")
    d = ImageDraw.Draw(img)
    for i, x in enumerate((7, 16, 25)):
        d.ellipse([x - 3, 6, x + 3, 12], outline=rgb(0xA01818))
        d.line([x, 12, x, 21, x - 3, 28], fill=rgb(0xA01818))
        d.line([x, 21, x + 3, 28], fill=rgb(0xA01818))
        d.line([x - 4, 15, x + 4, 15], fill=rgb(0xA01818))
    d.line([2, 29, 30, 29], fill=rgb(0x303030))
    save(img, "painting0")
    img = noise(0xE8E2CE, 3, "painting1")
    d = ImageDraw.Draw(img)
    for x in (9, 23):
        d.ellipse([x - 6, 10, x + 6, 20], fill=rgb(0xF8F8F0), outline=rgb(0x202020))
        d.ellipse([x - 2, 13, x + 2, 17], fill=rgb(0x101010))
    text(img, "SEE", (4, 23, 28, 31), 0x202020, 6)
    save(img, "painting1")
    img = noise(0x2E241C, 5, "painting2")
    d = ImageDraw.Draw(img)
    d.ellipse([10, 6, 22, 20], fill=rgb(0x9C8468))
    d.ellipse([12, 11, 14, 13], fill=rgb(0xF0F0F0))
    d.ellipse([18, 11, 20, 13], fill=rgb(0xF0F0F0))
    d.point((13, 12), fill=rgb(0x000000))
    d.point((19, 12), fill=rgb(0x000000))
    d.rectangle([8, 20, 24, 31], fill=rgb(0x1E2A22))
    save(img, "painting2")
    img = noise(0xEAE4D0, 3, "painting3")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 18, S - 1, S - 1], fill=rgb(0x6A8E3A))
    d.rectangle([13, 8, 19, 20], fill=rgb(0x5A3A1E), outline=rgb(0x2A1A0E))  # a door standing in a field
    d.ellipse([3, 3, 9, 9], fill=rgb(0xE8C030))
    save(img, "painting3")
    img = noise(0xC22A20, 5, "extsign")
    d = ImageDraw.Draw(img)
    d.rectangle([12, 8, 19, 28], fill=rgb(0xF0F0F0))
    d.rectangle([13, 4, 18, 8], fill=rgb(0xF0F0F0))
    save(img, "extsign")
    flat("extinguisher", 0xC21C18, 6)
    img = noise(0xC21C18, 4, "firealarm")
    d = ImageDraw.Draw(img)
    text(img, "FIRE", (2, 2, 30, 11), 0xF4F4F0, 7)
    d.rectangle([9, 14, 22, 20], fill=rgb(0xF4F4F0))
    d.rectangle([12, 20, 19, 26], fill=rgb(0xE0E0DA))
    save(img, "firealarm")
    for i, (c, logo) in enumerate(((0xE86A10, "eagle"), (0x9ACD32, "circle"), (0x7A3AB0, "tri"), (0x2A8AD8, "star"))):
        img = noise(c, 6, f"banner{i}")
        d = ImageDraw.Draw(img)
        ink = rgb(0xF4F0E0)
        if logo == "eagle":
            d.polygon([(4, 14), (16, 10), (28, 14), (16, 18)], fill=ink)
            d.polygon([(13, 8), (19, 8), (16, 22)], fill=ink)
        elif logo == "circle":
            d.ellipse([7, 6, 25, 24], outline=ink, width=3)
            d.line([16, 4, 16, 26], fill=ink, width=2)
        elif logo == "tri":
            d.polygon([(16, 4), (28, 24), (4, 24)], outline=ink, width=2)
        else:
            pts = [(16 + 11 * math.sin(a * math.pi / 5) * (1 if a % 2 == 0 else 0.45),
                    15 - 11 * math.cos(a * math.pi / 5) * (1 if a % 2 == 0 else 0.45)) for a in range(10)]
            d.polygon(pts, fill=ink)
        d.line([0, 29, S - 1, 29], fill=T.shade(T.hexrgb(c), 0.7), width=2)
        save(img, f"banner{i}")
    img = noise(0xB82018, 4, "hosecab")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0x401410), outline=rgb(0x8A1810))
    d.ellipse([7, 7, 24, 24], outline=rgb(0xD84030), width=3)
    d.ellipse([13, 13, 18, 18], fill=rgb(0x9A9A9A))
    d.line([4, 4, 12, 12], fill=rgb(0xC8D8E0))  # glass glint
    save(img, "hosecab")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xE8C020))
    text(img, "P2", (4, 7, 28, 25), 0x1C1C1C, 15)
    save(img, "levelsign")
    img = noise(0x1E7A3A, 3, "stairsign")
    d = ImageDraw.Draw(img)
    text(img, "STAIRS", (1, 2, 31, 11), 0xF4F4F0, 7)
    d.line([5, 27, 11, 27, 11, 22, 17, 22, 17, 17, 23, 17, 23, 13], fill=rgb(0xF4F4F0), width=2)
    save(img, "stairsign")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 27, 29], fill=rgb(0xF4F0DC))
    for y in range(9, 27, 3):
        d.line([7, y, 7 + random.Random(y).randint(10, 18), y], fill=rgb(0x303060))
    d.rectangle([12, 2, 19, 5], fill=rgb(0xD8D0A0, 230))
    save(img, "note")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([26, 12, 6, 12], fill=rgb(0xC81818), width=3)
    d.polygon([(4, 12), (11, 6), (11, 18)], fill=rgb(0xC81818))
    for k in range(5):
        d.line([7 + k * 3, 21, 7 + k * 3, 29], fill=rgb(0x202020), width=1)
    d.line([5, 27, 21, 22], fill=rgb(0x202020))
    save(img, "graffiti")


# ---------------- Level 3 ----------------

def level3():
    img = noise(0xF0C818, 3, "dangersign")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x111111), width=2)
    d.rectangle([2, 2, S - 3, 11], fill=rgb(0xC81818))
    text(img, "DANGER", (2, 2, 30, 12), 0xF4F4F0, 7)
    text(img, "HIGH", (2, 13, 30, 20), 0x111111, 6)
    text(img, "VOLTAGE", (2, 20, 30, 28), 0x111111, 6)
    save(img, "dangersign")
    img = Image.new("RGBA", (S, S), rgb(0x1A1A1A))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xF0EEE4))
    for a in range(-120, 121, 30):
        r = math.radians(a)
        d.line([16 + 10 * math.sin(r), 16 - 10 * math.cos(r), 16 + 13 * math.sin(r), 16 - 13 * math.cos(r)], fill=rgb(0x222222))
    d.arc([5, 5, 26, 26], 40, 120, fill=rgb(0xC81818), width=2)
    d.line([16, 16, 24, 9], fill=rgb(0xC81818), width=2)
    save(img, "gauge")
    flat("slate", 0x2E3236, 3)
    img = noise(0x4A3020, 4, "outletburnt")
    d = ImageDraw.Draw(img)
    d.rectangle([6, 4, 25, 27], fill=rgb(0xC8BEA0))
    T.blotch(img, (16, 10), 10, (20, 18, 16), 0.85, 77)
    for y in (8, 18):
        d.rectangle([11, y, 12, y + 4], fill=rgb(0x1A1A1A))
        d.rectangle([19, y, 20, y + 4], fill=rgb(0x1A1A1A))
    save(img, "outletburnt")
    img = noise(0xFFB050, 4, "bulkheadglass")
    d = ImageDraw.Draw(img)
    for x in (8, 16, 24):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A3020))
    d.line([0, 16, S - 1, 16], fill=rgb(0x3A3020))
    save(img, "bulkheadglass")
    img = noise(0xB8733A, 6, "coil")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 2):
        d.line([0, y, S - 1, y], fill=rgb(0x8A5022))
    save(img, "coil")
    flat("switchgear", 0x7A8288, 3)
    img = noise(0x7A8288, 3, "switchgearfront")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x4A5258), width=1)
    d.line([0, 15, S - 1, 15], fill=rgb(0x4A5258))
    for i, x in enumerate((5, 13, 21)):
        d.ellipse([x, 3, x + 6, 9], fill=rgb(0xF0EEE4), outline=rgb(0x222222))
        d.line([x + 3, 6, x + 5, 4], fill=rgb(0xC81818))
        d.ellipse([x + 1, 11, x + 3, 13], fill=rgb(0xE83020 if i != 1 else 0x30D050))
    d.rectangle([24, 20, 27, 27], fill=rgb(0x1A1A1A))  # handle
    d.rectangle([4, 19, 18, 23], fill=rgb(0xF4F4F0))
    text(img, "No. 7", (4, 19, 19, 24), 0x111111, 4)
    save(img, "switchgearfront")
    img = Image.new("RGBA", (S, S), rgb(0x1E2022))
    d = ImageDraw.Draw(img)
    for r in range(3, 16, 3):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0x6A6E72))
    d.line([16, 1, 16, 31], fill=rgb(0x6A6E72))
    d.line([1, 16, 31, 16], fill=rgb(0x6A6E72))
    save(img, "fancage")
    img = noise(0xC8A030, 5, "generator")
    d = ImageDraw.Draw(img)
    for y in range(4, S, 6):
        d.line([0, y, S - 1, y], fill=rgb(0x9A7820))
    save(img, "generator")
    img = noise(0x2E3236, 3, "generatorpanel")
    d = ImageDraw.Draw(img)
    for x in (5, 17):
        d.ellipse([x, 4, x + 9, 13], fill=rgb(0xF0EEE4))
        d.line([x + 4, 9, x + 7, 6], fill=rgb(0xC81818))
    for x in range(5, 27, 5):
        d.rectangle([x, 19, x + 2, 24], fill=rgb(0xD8D8D0))
    d.ellipse([24, 26, 28, 30], fill=rgb(0xD82020))
    save(img, "generatorpanel")
    img = noise(0x8E6A40, 5, "spoolwood")
    d = ImageDraw.Draw(img)
    for r in (5, 10, 14):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0x6A4A28))
    save(img, "spoolwood")
    img = noise(0x5A6268, 3, "controlpanel")
    d = ImageDraw.Draw(img)
    for i in range(4):
        x = 3 + i * 7
        d.ellipse([x, 3, x + 5, 8], fill=rgb(0xF0EEE4))
        d.line([x + 2, 6, x + 4, 4], fill=rgb(0x111111))
    for i in range(8):
        d.rectangle([3 + i * 3, 13, 4 + i * 3, 17], fill=rgb(0xD8D8D0 if i % 3 else 0x222222))
    for i, c in enumerate((0xE83020, 0x30D050, 0xF0C020, 0x30D050, 0xE83020)):
        d.ellipse([4 + i * 5, 22, 6 + i * 5, 24], fill=rgb(c))
    save(img, "controlpanel")
    img = noise(0x26282A, 3, "conveyorbelt")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A3C3E))
    save(img, "conveyorbelt")
    img = noise(0xC8C4BA, 5, "stone")
    T.blotch(img, (8, 24), 7, (150, 146, 136), 0.3, 91)
    save(img, "stone")
    img = noise(0xC8C4BA, 5, "stonewing")
    d = ImageDraw.Draw(img)
    for y in range(3, S, 5):
        d.arc([-8, y - 6, 40, y + 6], 20, 160, fill=rgb(0xA8A498))
    save(img, "stonewing")
    img = Image.new("RGBA", (S, S), rgb(0x1E2022))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 4):
        d.line([k, 0, k, S - 1], fill=rgb(0x5A5E62))
        d.line([0, k, S - 1, k], fill=rgb(0x4A4E52))
    save(img, "grate")
    img = T.noise_fill(T.hexrgb(0x857868), 6, 505)
    stripes(img, rgb(0xE0B020), rgb(0x1E1E1E), 4, (0, 0, S, 6))
    stripes(img, rgb(0xE0B020), rgb(0x1E1E1E), 4, (0, S - 6, S, S))
    save(img, "l3hazard")
    img = noise(0x8C877C, 6, "l3stone")
    d = ImageDraw.Draw(img)
    for y, xs in ((0, (0, 18)), (11, (8, 26)), (21, (4, 20))):
        d.line([0, y, S - 1, y], fill=rgb(0x5E5A52))
        for x in xs:
            d.line([x, y, x, y + 10], fill=rgb(0x5E5A52))
    save(img, "l3stone")
    img = noise(0x7A1414, 4, "sanctumcarpet")
    d = ImageDraw.Draw(img)
    for x in (2, 29):
        d.rectangle([x, 0, x + 1, S - 1], fill=rgb(0xC8A040))
    save(img, "sanctumcarpet")
    img = noise(0xB8B0A0, 4, "sanctumwall")
    d = ImageDraw.Draw(img)
    for r in range(2):
        y = r * 16
        d.line([0, y, S - 1, y], fill=rgb(0x8A8274))
        off = 12 if r % 2 else 0
        for x in range(off, S + 24, 24):
            d.line([x % S, y, x % S, y + 15], fill=rgb(0x8A8274))
    save(img, "sanctumwall")


# ---------------- Level 4 ----------------

def level4():
    wall = noise(0xD8D5D4, 4, "officewall-x")
    base = wall.copy()
    d = ImageDraw.Draw(base)
    d.rectangle([0, 27, S - 1, S - 1], fill=rgb(0x3E3E40))
    d.line([0, 26, S - 1, 26], fill=rgb(0x555558))
    save(base, "drywall-base")
    tile = T.noise_fill(T.hexrgb(0xD8D4CF), 3, 524)
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x969490))
    d.line([0, 15, S - 1, 15], fill=rgb(0x969490))
    img = tile.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([7, 7, 24, 24], fill=rgb(0xE8E8E4), outline=rgb(0xA8A8A4))
    for k in (10, 13):
        d.rectangle([k, k, S - 1 - k, S - 1 - k], outline=rgb(0xB8B8B4))
    save(img, "officeceiling-vent")
    img = tile.copy()
    d = ImageDraw.Draw(img)
    d.ellipse([13, 20, 18, 25], fill=rgb(0xE0E0DC), outline=rgb(0x9A9A96))
    d.point((15, 22), fill=rgb(0xC8301C))
    save(img, "officeceiling-sprinkler")
    img = tile.copy()
    T.blotch(img, (18, 12), 11, (150, 120, 70), 0.55, 333)
    save(img, "officeceiling-stain")

    img = Image.new("RGBA", (S, S), rgb(0x141414))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x28292C), width=2)
    d.line([2, 2, S - 3, 2], fill=rgb(0x6A7078))  # light leaking round the paper
    d.line([2, S - 3, 12, S - 3], fill=rgb(0x5A6068))
    for x, y in ((3, 3), (25, 3), (3, 25), (25, 25)):
        d.rectangle([x, y, x + 4, y + 2], fill=rgb(0xC8C0A0))  # tape
    d.line([16, 0, 16, S - 1], fill=rgb(0x28292C))
    save(img, "officewindow-blackout")
    img = Image.new("RGBA", (S, S), rgb(0xC8C6C0))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 3):
        d.line([0, y, S - 1, y], fill=rgb(0x8A8884))
    d.line([8, 0, 8, S - 1], fill=rgb(0xE8E8E2))
    d.line([24, 0, 24, S - 1], fill=rgb(0xE8E8E2))
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x28292C), width=2)
    save(img, "officewindow-blinds")
    carpet = T.noise_fill(T.hexrgb(0x85837D), 7, 523)
    img = carpet.copy()
    d = ImageDraw.Draw(img)
    for x, y, a in ((4, 6, 0), (18, 14, 1), (9, 22, 0)):
        d.polygon([(x, y), (x + 8, y + a * 2), (x + 7, y + 10), (x - 1, y + 9 - a)], fill=rgb(0xF0EEE6))
        d.line([x + 1, y + 3, x + 6, y + 3], fill=rgb(0x9A9A9A))
    save(img, "officecarpet-papers")
    img = carpet.copy()
    T.blotch(img, (14, 16), 7, (70, 50, 30), 0.6, 334)
    save(img, "officecarpet-stain")
    for part in ("lower", "upper"):
        img = noise(0xA88458, 4, "officedoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=2)
        if part == "lower":
            d.rectangle([22, 0, 27, 2], fill=rgb(0xC0C4C8))  # lever
            d.rectangle([22, 0, 23, 4], fill=rgb(0xC0C4C8))
            d.rectangle([3, 26, 28, 29], fill=rgb(0x8A8E92))  # kick plate
        else:
            d.rectangle([5, 4, 9, 28], fill=rgb(0x3A4A52))  # narrow glass strip
            d.rectangle([14, 12, 26, 17], fill=rgb(0xC8B070))
            text(img, "ROOM", (14, 12, 27, 18), 0x2A2010, 4)
        save(img, f"officedoor-{part}")

    # Modern elevator: brushed steel leaves meeting in the middle of a 2-wide opening, an indicator above
    for half in ("l", "r"):
        seam, frame = (S - 1, 0) if half == "l" else (0, S - 1)
        for part in ("lower", "upper"):
            img = noise(0xA8ACB0, 3, f"lift{part}{half}")
            d = ImageDraw.Draw(img)
            for x in range(1, S, 3):
                d.line([x, 0, x, S - 1], fill=rgb(0x9CA0A4))
            d.line([seam, 0, seam, S - 1], fill=rgb(0x3A3E42))
            d.rectangle([frame - 1 if half == "r" else 0, 0, frame if half == "r" else 1, S - 1], fill=rgb(0x6A6E72))
            if part == "upper":
                d.rectangle([0, 0, S - 1, 1], fill=rgb(0x6A6E72))
            save(img, f"liftdoor-{part}-{half}")
        img = noise(0x6A6E72, 3, f"liftheader{half}")
        d = ImageDraw.Draw(img)
        d.rectangle([2, 8, S - 3, 23], fill=rgb(0x141414))
        if half == "l":
            d.polygon([(10, 20), (22, 20), (16, 11)], fill=rgb(0xF0A020))
        else:
            text(img, "13", (2, 8, S - 2, 24), 0xF0A020, 11)
        save(img, f"liftheader-{half}")
    flat("liftframe", 0x6A6E72, 3)
    img = noise(0xA8ACB0, 3, "callpanel")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x6A6E72), width=2)
    d.ellipse([11, 6, 20, 15], fill=rgb(0xF4F0E0), outline=rgb(0x4A4E52))
    d.ellipse([11, 18, 20, 27], fill=rgb(0xF0A020), outline=rgb(0x4A4E52))
    save(img, "callpanel")

    flat("fountainsteel", 0xBCC0C4, 4)
    img = Image.new("RGBA", (S, S), rgb(0xF4F2EC))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    for h in range(12):
        a = math.radians(h * 30)
        d.line([16 + 11 * math.sin(a), 16 - 11 * math.cos(a), 16 + 13 * math.sin(a), 16 - 13 * math.cos(a)], fill=rgb(0x222222))
    d.line([16, 16, 16, 7], fill=rgb(0x111111), width=2)  # stopped at 3:14
    d.line([16, 16, 23, 18], fill=rgb(0x111111), width=1)
    save(img, "clockface")
    img = noise(0xF6F6F4, 2, "whiteboard")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xA8ACB0), width=1)
    T.blotch(img, (12, 12), 8, (200, 204, 210), 0.5, 335)
    d.line([4, 8, 18, 8], fill=rgb(0x2A4AA8))
    d.line([4, 12, 14, 12], fill=rgb(0x2A4AA8))
    d.ellipse([20, 18, 28, 26], outline=rgb(0xC82020))
    save(img, "whiteboard")
    img = noise(0xB08A5A, 8, "corkboard")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x7A5A34), width=2)
    for x, y, c in ((5, 5, 0xF4F0E0), (18, 8, 0xF0E070), (8, 18, 0xF4F0E0)):
        d.rectangle([x, y, x + 8, y + 9], fill=rgb(c))
        d.point((x + 4, y + 1), fill=rgb(0xC82020))
    save(img, "corkboard")
    img = noise(0xF4F2EC, 2, "evacmap")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    for r in ((4, 6, 14, 14), (16, 6, 27, 14), (4, 17, 27, 26)):
        d.rectangle(r, outline=rgb(0x555555))
    d.line([8, 21, 26, 21], fill=rgb(0x2A9A3A))
    d.ellipse([7, 9, 10, 12], fill=rgb(0xD82020))
    text(img, "YOU ARE HERE", (2, 26, 30, 31), 0xD82020, 3)
    save(img, "evacmap")
    img = noise(0xE8E8E2, 2, "extcabinet")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0xB8C8CC), outline=rgb(0x8A8E92))
    d.rectangle([12, 8, 19, 26], fill=rgb(0xC21C18))
    d.rectangle([13, 5, 17, 8], fill=rgb(0x1A1A1A))
    d.line([5, 5, 10, 10], fill=rgb(0xF0F8FA))
    save(img, "extcabinet")
    img = noise(0xF0F0EA, 2, "strobe")
    ImageDraw.Draw(img).rectangle([6, 8, 25, 23], fill=rgb(0xF8E8E0))
    text(img, "FIRE", (4, 10, 28, 22), 0xD82020, 6)
    save(img, "strobe")
    flat("switchplate", 0xE8E2D0, 2)
    img = noise(0xE4DFD2, 2, "thermostat")
    d = ImageDraw.Draw(img)
    d.rectangle([6, 8, 25, 18], fill=rgb(0x9AB89A))
    text(img, "72", (6, 8, 26, 19), 0x1E2E1E, 7)
    save(img, "thermostat")
    for i, (word, sky, ground) in enumerate((("TEAMWORK", 0x6A8AB0, 0x5A6A4A), ("SUCCESS", 0xC88A50, 0x3A3A44), ("PERSEVERE", 0x2A3A5A, 0x6A7A8A))):
        img = Image.new("RGBA", (S, S), rgb(0x1A1A1A))
        d = ImageDraw.Draw(img)
        d.rectangle([2, 2, 29, 22], fill=rgb(sky))
        d.polygon([(2, 22), (12, 8), (18, 16), (22, 11), (29, 22)], fill=rgb(ground))
        text(img, word, (1, 23, 31, 30), 0xE8E4D8, 5)
        save(img, f"poster{i}")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], fill=rgb(0xE8E6E4))
    save(img, "frameghost")
    flat("wallphone", 0xD8D2C0, 3)
    img = noise(0xC8301C, 4, "stairsign-office")
    d = ImageDraw.Draw(img)
    text(img, "STAIR", (2, 4, 30, 14), 0xF4F4F0, 7)
    text(img, "3", (2, 15, 30, 29), 0xF4F4F0, 11)
    save(img, "stairsign-office")
    flat("planter", 0xE4E0D6, 3)
    img = noise(0x6A6A3A, 14, "ficusleaves")
    rng = random.Random(7)
    for _ in range(50):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(rng.choice([0x8A7040, 0x4A5A2A, 0xA08048])))
    save(img, "ficusleaves")
    flat("dryleaf", 0x8A6A3A, 8)
    flat("plasticchair", 0x5A6E86, 4)
    flat("copier", 0xD8D2C2, 3)
    img = noise(0x3A3E42, 3, "copierpanel")
    ImageDraw.Draw(img).rectangle([4, 6, 18, 14], fill=rgb(0x7AB07A))
    save(img, "copierpanel")
    img = Image.new("RGBA", (S, S), rgb(0x2A2622))
    d = ImageDraw.Draw(img)
    x = 0
    rng = random.Random(seed_of("binders"))
    while x < S:
        w = rng.randint(3, 5)
        c = rng.choice([0x2A4A8A, 0x1A1A1A, 0x8A2020, 0xE8E8E0, 0x2A6A3A])
        d.rectangle([x, 2, x + w - 1, S - 1], fill=rgb(c))
        d.rectangle([x + 1, 8, x + w - 2, 12], fill=rgb(0xF0F0EA))
        x += w + rng.choice([0, 0, 1, 6])
    save(img, "binders")
    img = Image.new("RGBA", (S, S), rgb(0x16181A))
    d = ImageDraw.Draw(img)
    rng = random.Random(4)
    for y in range(1, S, 4):
        d.line([1, y + 2, S - 2, y + 2], fill=rgb(0x2A2C2E))
        for x in range(3, S - 3, 3):
            if rng.random() < 0.3:
                d.point((x, y), fill=rgb(rng.choice([0x30E050, 0x30E050, 0xF0A020, 0x40A0F0])))
    save(img, "serverfront")
    img = noise(0xEEEEE8, 2, "cabinetwhite")
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, S - 1], fill=rgb(0xB8B8B2))
    d.rectangle([12, 4, 14, 5], fill=rgb(0x8A8E92))
    d.rectangle([18, 4, 20, 5], fill=rgb(0x8A8E92))
    save(img, "cabinetwhite")
    flat("countertop", 0x6E6A64, 3)
    img = noise(0xE8E8E4, 2, "microwave")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, 21, 27], fill=rgb(0x1E2224))
    for r in range(4):
        for c in range(2):
            d.rectangle([24 + c * 3, 6 + r * 4, 25 + c * 3, 7 + r * 4], fill=rgb(0x555555))
    d.rectangle([24, 23, 29, 26], fill=rgb(0x1A2A1A))
    save(img, "microwave")
    flat("fridgewhite", 0xF0F0EC, 2)
    img = noise(0x9A7A52, 4, "receptionfront")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 3], fill=rgb(0x6E6A64))
    d.rectangle([8, 10, 23, 20], fill=rgb(0xC8C4BA))
    text(img, "WELCOME", (8, 10, 24, 21), 0x2A2A2A, 4)
    save(img, "receptionfront")
    img = Image.new("RGBA", (S, S), rgb(0x2A2A2C))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 3):
        d.line([k, 0, k, S - 1], fill=rgb(0x3E3E40))
        d.line([0, k, S - 1, k], fill=rgb(0x3E3E40))
    save(img, "wastebin")
    flat("coat", 0x4A4E54, 5)
    img = noise(0xC8A878, 4, "benchwood")
    for x in range(0, S, 8):
        ImageDraw.Draw(img).line([0, x, S - 1, x], fill=rgb(0x9A7E54))
    save(img, "benchwood")


# ---------------- Level 5 ----------------

def level5():
    # Antique elevator: a brass scissor gate across a 2-wide opening, a dial above showing the floor
    for half in ("l", "r"):
        img = Image.new("RGBA", (S, S), rgb(0x1E120A))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], fill=rgb(0x2A1A10))
        for k in range(-S, 2 * S, 8):
            d.line([k, 0, k + S, S], fill=rgb(0xC89A40), width=1)
            d.line([k + S, 0, k, S], fill=rgb(0xC89A40), width=1)
        for x in range(0, S, 8):
            d.line([x, 0, x, S - 1], fill=rgb(0xA87A30))
        edge = 0 if half == "l" else S - 2
        d.rectangle([edge, 0, edge + 1, S - 1], fill=rgb(0x8A6020))
        save(img, f"cagegate-{half}")
    big = Image.new("RGBA", (2 * S, S), rgb(0x452518))
    d = ImageDraw.Draw(big)
    d.pieslice([6, 4, 58, 56], 180, 360, fill=rgb(0xC9A040), outline=rgb(0x8A6A20))
    d.pieslice([10, 8, 54, 52], 180, 360, fill=rgb(0xF0E6C8))
    for i in range(13):
        a = math.radians(180 + i * 15)
        d.line([32 + 18 * math.cos(a), 30 + 18 * math.sin(a), 32 + 21 * math.cos(a), 30 + 21 * math.sin(a)], fill=rgb(0x3A2A10))
    d.line([32, 30, 32 + 17 * math.cos(math.radians(318)), 30 + 17 * math.sin(math.radians(318))], fill=rgb(0x1A1A1A), width=2)
    d.rectangle([0, 0, 2 * S - 1, 1], fill=rgb(0x8A6A20))
    save(big.crop((0, 0, S, S)), "cagedial-l")
    save(big.crop((S, 0, 2 * S, S)), "cagedial-r")

    img = Image.new("RGBA", (S, S), rgb(0xC9A040))
    d = ImageDraw.Draw(img)
    d.ellipse([3, 1, 28, 30], fill=rgb(0x8A9AA4))
    d.ellipse([6, 4, 25, 27], fill=rgb(0xA8B8C2))
    d.line([10, 8, 16, 14], fill=rgb(0xE0EEF4), width=2)
    save(img, "mirrorglass")
    img = noise(0xB08A3C, 5, "speakergrille")
    d = ImageDraw.Draw(img)
    for r in range(3, 15, 3):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0x5A4418))
    save(img, "speakergrille")
    flat("bakelite", 0x18120E, 2)
    img = Image.new("RGBA", (S, S), rgb(0x18120E))
    d = ImageDraw.Draw(img)
    d.ellipse([3, 3, 28, 28], fill=rgb(0xE8E0C8))
    for i in range(10):
        a = math.radians(i * 30 + 30)
        d.ellipse([14 + 9 * math.cos(a), 14 + 9 * math.sin(a), 18 + 9 * math.cos(a), 18 + 9 * math.sin(a)], fill=rgb(0x18120E))
    save(img, "phonedial")
    img = noise(0x8A1C14, 4, "hotelhosecab")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 29, 29], outline=rgb(0xC9A040), width=2)
    d.rectangle([5, 5, 26, 26], fill=rgb(0x2A1410))
    d.ellipse([8, 8, 23, 23], outline=rgb(0xB8733A), width=3)
    d.line([6, 6, 12, 12], fill=rgb(0xE0E8EC))
    save(img, "hotelhosecab")
    img = Image.new("RGBA", (S, S), rgb(0xC9A040))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xF0E6C8), outline=rgb(0x8A6A20))
    for h in range(12):
        a = math.radians(h * 30)
        d.line([16 + 10 * math.sin(a), 16 - 10 * math.cos(a), 16 + 12 * math.sin(a), 16 - 12 * math.cos(a)], fill=rgb(0x2A1A0A), width=1)
    d.line([16, 16, 16, 6], fill=rgb(0x111111))
    d.line([16, 16, 10, 20], fill=rgb(0x111111), width=2)
    save(img, "ornateclock")
    img = noise(0x5A2E1A, 4, "keyrack")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x3A1C0E))
    for x in range(0, S, 8):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A1C0E))
    rng = random.Random(55)
    for y in range(0, S, 8):
        for x in range(0, S, 8):
            if rng.random() < 0.6:
                d.line([x + 4, y + 1, x + 4, y + 5], fill=rgb(0xD8B050))
                d.rectangle([x + 3, y + 5, x + 5, y + 7], fill=rgb(0xE8DCC0))
    save(img, "keyrack")
    img = noise(0xC9A040, 4, "callplate")
    d = ImageDraw.Draw(img)
    d.ellipse([11, 5, 20, 14], fill=rgb(0xF0E6C8), outline=rgb(0x6A4A10))
    d.ellipse([11, 18, 20, 27], fill=rgb(0xF0E6C8), outline=rgb(0x6A4A10))
    save(img, "callplate")
    # A pastoral landscape: an evening sky, a line of blue hills, green fields, a tree, a road toward a house
    img = texlib.vertical_gradient((232, 196, 140), (150, 170, 190), height=S)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 15), (6, 11), (12, 14), (19, 9), (26, 13), (31, 11), (31, 18), (0, 18)], fill=rgb(0x6A7A98))
    d.rectangle([0, 17, S - 1, S - 1], fill=rgb(0x6E8A3E))
    d.polygon([(0, 24), (31, 20), (31, 31), (0, 31)], fill=rgb(0x5A7832))
    d.polygon([(14, 31), (17, 18), (18, 18), (21, 31)], fill=rgb(0xB8A274))
    d.rectangle([22, 15, 25, 18], fill=rgb(0xE8E0D0))
    d.polygon([(21, 15), (23.5, 12), (26, 15)], fill=rgb(0x8A3A2A))
    d.ellipse([3, 9, 11, 17], fill=rgb(0x3A5A2A))
    d.rectangle([6, 16, 7, 22], fill=rgb(0x4A3220))
    d.ellipse([24, 3, 28, 7], fill=rgb(0xF8E8B0))
    save(img, "landscape")

    # White marble floor: grey veining, with small black diamonds set at the corners where four slabs meet
    img = texlib.marble((232, 228, 220), (150, 146, 140), 66, sharpness=6, mottle=0.05)
    d = ImageDraw.Draw(img)
    for x, y in ((0, 0), (S, 0), (0, S), (S, S)):
        d.polygon([(x - 4, y), (x, y - 4), (x + 4, y), (x, y + 4)], fill=rgb(0x1E1C1A))
    save(img, "marble")
    save(texlib.marble((236, 232, 224), (160, 154, 146), 67, sharpness=7, mottle=0.04), "marbletop")
    wood = T.noise_fill(T.hexrgb(0x3A2014), 5, 546)
    for axis in ("ns", "we"):
        img = wood.copy()
        d = ImageDraw.Draw(img)
        if axis == "ns":
            d.rectangle([3, 0, 28, S - 1], fill=rgb(0x8A1C14))
            d.rectangle([5, 0, 6, S - 1], fill=rgb(0xC9A040))
            d.rectangle([25, 0, 26, S - 1], fill=rgb(0xC9A040))
        else:
            d.rectangle([0, 3, S - 1, 28], fill=rgb(0x8A1C14))
            d.rectangle([0, 5, S - 1, 6], fill=rgb(0xC9A040))
            d.rectangle([0, 25, S - 1, 26], fill=rgb(0xC9A040))
        save(img, f"runner-{axis}")
    img = noise(0x7A1A18, 5, "rug")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x1E2A4A), width=3)
    d.polygon([(16, 5), (27, 16), (16, 27), (5, 16)], fill=rgb(0x1E2A4A), outline=rgb(0xC9A040))
    d.polygon([(16, 10), (22, 16), (16, 22), (10, 16)], fill=rgb(0xC9A040))
    save(img, "rug")

    img = noise(0xE8ECF4, 3, "vase")
    d = ImageDraw.Draw(img)
    for y in (6, 16, 26):
        d.line([0, y, S - 1, y], fill=rgb(0x2A4A9A), width=2)
    save(img, "vase")
    flat("driedflowers", 0x7A4A3A, 12)
    img = Image.new("RGBA", (S, S), rgb(0x2A1810))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("books"))
    for row in range(2):
        x = 0
        while x < S:
            w = rng.randint(2, 4)
            c = rng.choice([0x5A1A14, 0x1E3A2A, 0x2A2A4A, 0x6A4A2A, 0x3A1A2A])
            top = row * 16 + rng.randint(1, 4)
            d.rectangle([x, top, x + w - 1, row * 16 + 15], fill=rgb(c))
            d.line([x, top + 3, x + w - 1, top + 3], fill=rgb(0xC9A040))
            x += w
    save(img, "books")
    img = Image.new("RGBA", (S, S), rgb(0x1A2224))
    d = ImageDraw.Draw(img)
    d.line([4, 2, 12, 30], fill=rgb(0x5A6E74))
    d.line([18, 2, 26, 30], fill=rgb(0x3A4A50))
    save(img, "curioglass")
    flat("china", 0xF4F2EC, 2)
    flat("cartcarpet", 0x8A1C14, 4)
    img = noise(0x6A3A1E, 5, "suitcaseleather")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x3A1E0E), width=2)
    for x in (8, 23):
        d.rectangle([x, 0, x + 1, S - 1], fill=rgb(0x3A1E0E))
    save(img, "suitcaseleather")
    flat("suitcasetan", 0xB89060, 5)
    flat("tablecloth", 0xF2F0EA, 2)
    flat("silver", 0xD0D4D8, 4)
    img = noise(0xD8CCA8, 3, "radiator")
    for x in range(0, S, 4):
        ImageDraw.Draw(img).line([x, 0, x, S - 1], fill=rgb(0xA89A78))
    save(img, "radiator")
    flat("bankergreen", 0x1E7A44, 4)
    img = Image.new("RGBA", (S, S), rgb(0x1A120C))
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, 22], fill=rgb(0xC9A040), width=1)
    d.ellipse([12, 21, 20, 29], fill=rgb(0xC9A040))
    save(img, "clockpendulum")
    img = Image.new("RGBA", (S, S), rgb(0x5A2E1A))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xE8DCBC), outline=rgb(0xC9A040), width=2)
    for h in range(12):
        a = math.radians(h * 30)
        d.text((14 + 10 * math.sin(a), 13 - 10 * math.cos(a)), ".", fill=rgb(0x1A1A1A))
    d.line([16, 16, 16, 7], fill=rgb(0x111111))
    d.line([16, 16, 22, 19], fill=rgb(0x111111), width=2)
    save(img, "clockface-old")
    img = noise(0x5A2E1A, 4, "receptionmahogany")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 2], fill=rgb(0xC9A040))
    d.rectangle([3, 6, 13, 28], outline=rgb(0xC9A040))
    d.rectangle([18, 6, 28, 28], outline=rgb(0xC9A040))
    save(img, "receptionmahogany")
    img = noise(0x5A1A14, 3, "guestbook")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 29, 29], fill=rgb(0xF0E8D0))
    d.line([16, 2, 16, 29], fill=rgb(0x8A7A5A))
    for y in range(6, 28, 3):
        d.line([4, y, 13, y], fill=rgb(0x5A5A7A))
        d.line([19, y, 27, y], fill=rgb(0x5A5A7A))
    save(img, "guestbook")
    flat("pianoblack", 0x101012, 2)
    img = Image.new("RGBA", (S, S), rgb(0xF4F2EA))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 2):
        d.line([x, 0, x, S - 1], fill=rgb(0xB8B6AE))
    for x in range(1, S, 4):
        d.rectangle([x, 0, x + 1, 18], fill=rgb(0x111111))
    save(img, "pianokeys")
    img = noise(0x1A1A1C, 12, "coal")
    rng = random.Random(77)
    for _ in range(30):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(0x4A4A50))
    save(img, "coal")


def generate():
    shared()
    level1()
    level3()
    level4()
    level5()
