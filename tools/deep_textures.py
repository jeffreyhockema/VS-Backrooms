"""Textures for Levels 6 to 10 and Level 6.1 (32x32, in block/detail/ and item/)."""
import math
import random

from PIL import Image, ImageDraw

import matlib as M
from detail_kit import T, seed_of
from detail_textures import S, block_wall, flat, grime, noise, rgb, save, stripes, text


def save_item(img, name):
    T.save(img, f"item/{name}.png")


def sprite():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def specks(img, colors, count, key):
    rng = random.Random(seed_of(key))
    for _ in range(count):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(rng.choice(colors)))
    return img


def chalk_stroke(d, pts, width=2):
    d.line(pts, fill=(236, 236, 228, 235), width=width)


# ---------------- Level 6 ----------------

def level6():
    img = noise(0x3A3D42, 3, "l6wall")
    d = ImageDraw.Draw(img)
    for y in (0, 16):
        d.line([0, y, S - 1, y], fill=rgb(0x33363B))
    d.line([2, 3, 9, 3], fill=rgb(0x484B50))  # a faint, cold sheen
    save(img, "l6wall")
    save(noise(0x2C2E32, 2, "l6floor"), "l6floor")
    save(noise(0x303236, 2, "l6ceiling"), "l6ceiling")

    def chalk_decal(name, draw):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw(ImageDraw.Draw(img), img)
        save(img, name)

    chalk_decal("chalk-megexit", lambda d, img: (chalk_stroke(d, [4, 20, 26, 20]), chalk_stroke(d, [20, 14, 27, 20, 20, 26]),
                                                 text(img, "EXIT", (3, 4, 29, 14), (236, 236, 228, 235), 8)))
    chalk_decal("chalk-megcross", lambda d, img: (chalk_stroke(d, [6, 4, 26, 22], 3), chalk_stroke(d, [26, 4, 6, 22], 3),
                                                  text(img, "DEAD END", (1, 23, 31, 31), (236, 236, 228, 235), 5)))
    chalk_decal("chalk-meglogo", lambda d, img: (d.ellipse([3, 3, 28, 28], outline=(236, 236, 228, 235), width=2),
                                                 text(img, "M.E.G.", (4, 10, 28, 22), (236, 236, 228, 235), 7)))

    def hands(d, img):
        rng = random.Random(61)
        for (x, y) in ((6, 6), (18, 12), (9, 19)):
            d.ellipse([x, y + 4, x + 6, y + 11], fill=(26, 20, 18, 200))
            for k in range(4):
                d.line([x + 1 + k * 1.6, y + 4, x + rng.uniform(-1, 1) + k * 1.8, y], fill=(26, 20, 18, 200), width=1)
    chalk_decal("handprints", hands)

    def scratches(d, img):
        for k in range(6):
            d.line([6 + k * 3, 6, 5 + k * 3, 24], fill=(200, 200, 196, 210))
        d.line([4, 20, 25, 9], fill=(200, 200, 196, 210))
    chalk_decal("scratches", scratches)

    for name, draw in (("left", lambda d: (chalk_stroke(d, [27, 16, 5, 16], 3), chalk_stroke(d, [12, 8, 4, 16, 12, 24], 3))),
                       ("right", lambda d: (chalk_stroke(d, [5, 16, 27, 16], 3), chalk_stroke(d, [20, 8, 28, 16, 20, 24], 3))),
                       ("cross", lambda d: (chalk_stroke(d, [6, 6, 26, 26], 3), chalk_stroke(d, [26, 6, 6, 26], 3))),
                       ("circle", lambda d: d.ellipse([6, 6, 26, 26], outline=(236, 236, 228, 235), width=3))):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw(ImageDraw.Draw(img))
        save(img, f"chalkmark-{name}")
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(8, 26), (22, 6), (27, 10), (13, 29)], fill=(240, 238, 230, 255), outline=(170, 168, 160, 255))
    d.polygon([(8, 26), (13, 29), (10, 30), (6, 28)], fill=(200, 198, 190, 255))
    save_item(img, "chalk")


# ---------------- Level 6.1 ----------------

def level61():
    img = noise(0xE6D8C8, 4, "snackfloor-terrazzo")
    specks(img, [0xE88AA0, 0x7AC8C0, 0x9A8C7C, 0xF4F0E8], 70, "terrazzo")
    save(img, "snackfloor-terrazzo")
    img = Image.new("RGBA", (S, S))
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), rgb(0xF0F0EC if (x // 8 + y // 8) % 2 == 0 else 0x1C1C20))
    save(img, "snackfloor-checker")
    img = noise(0xA8442E, 6, "quarry")
    d = ImageDraw.Draw(img)
    for k in (0, 16):
        d.line([0, k, S - 1, k], fill=rgb(0x6A2A1C))
        d.line([k, 0, k, S - 1], fill=rgb(0x6A2A1C))
    save(img, "snackfloor-quarry")
    img = noise(0x7EC8BE, 3, "snackwall-mall")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 18, S - 1, 21], fill=rgb(0xE88AA0))
    d.rectangle([0, 23, S - 1, 23], fill=rgb(0xF4E8D0))
    save(img, "snackwall-mall")
    img = noise(0x8A5A34, 4, "snackwall-panel")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.line([x, 0, x, S - 1], fill=rgb(0x6A4224))
    save(img, "snackwall-panel")
    img = noise(0xF2F2EE, 2, "snackwall-tile")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0xC8C8C4))
        d.line([k, 0, k, S - 1], fill=rgb(0xC8C8C4))
    save(img, "snackwall-tile")
    img = Image.new("RGBA", (S, S), rgb(0xFFE6C0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xB8B4AC), width=2)
    d.line([16, 0, 16, S - 1], fill=rgb(0xB8B4AC), width=2)
    T.blotch(img, (16, 16), 14, (255, 250, 236), 0.6, 71)
    save(img, "snackwall-window")
    img = noise(0xEEEEEA, 2, "snackceiling-grid")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xB8B8B4))
    d.line([0, 16, S - 1, 16], fill=rgb(0xB8B8B4))
    save(img, "snackceiling-grid")
    # A skylight that shows nothing but darkness, though light comes from it: four near-black panes, a faint
    # sheen on the glass, between dark mullions, in a frame whose diffuser rim glows orange-white
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = ((x % 16) + (y % 16)) / 30.0
            sheen = 10 if abs((x % 16) - (y % 16) - 3) <= 1 else 0
            px[x, y] = (int(7 + 6 * t) + sheen, int(8 + 7 * t) + sheen, int(12 + 10 * t) + sheen, 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFE8C4), width=2)
    d.rectangle([2, 2, S - 3, S - 3], outline=rgb(0xE0B888))
    d.rectangle([15, 3, 16, S - 4], fill=rgb(0x4A4640))
    d.rectangle([3, 15, S - 4, 16], fill=rgb(0x4A4640))
    save(img, "snackceiling-skylight")
    for part in ("lower", "upper"):
        img = noise(0x6A4A3A, 12, "rusty" + part)
        T.blotch(img, (10, 20), 9, (150, 80, 40), 0.6, 72)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x3A2A20), width=2)
        if part == "lower":
            d.rectangle([22, 0, 27, 3], fill=rgb(0x9A9488))
        else:
            d.rectangle([8, 10, 23, 14], fill=rgb(0xC8B060))
            text(img, "EXIT", (8, 9, 24, 15), 0x3A2A10, 5)
        save(img, f"rustydoor-{part}")
        img = Image.new("RGBA", (S, S), rgb(0x9AB8C0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=2)
        d.line([4, 4, 12, 12] if part == "upper" else [18, 4, 26, 12], fill=rgb(0xE0F0F4), width=2)
        if part == "lower":
            d.rectangle([2, 0, 29, 2], fill=rgb(0x8A8E92))
        save(img, f"glassdoors-{part}")
        img = noise(0xC8C8C4, 3, "kitchendoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=2)
        if part == "upper":
            d.ellipse([9, 6, 22, 19], fill=rgb(0x2A3A42), outline=rgb(0x8A8E92), width=2)
        else:
            d.rectangle([4, 4, 27, 10], fill=rgb(0xA8ACB0))
        save(img, f"kitchendoor-{part}")
    img = Image.new("RGBA", (S, S), rgb(0x1A1C1E))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=3)
    for y in range(6, S - 4, 4):
        d.line([4, y, S - 5, y], fill=rgb(0x6A6E72), width=2)
    save(img, "ventgrate")

    flat("navy", 0x1E2E5A, 4)
    flat("chrome", 0xC8CCD0, 3)
    flat("formica", 0xE8DCC8, 3)
    img = noise(0x2A2E34, 3, "register")
    ImageDraw.Draw(img).rectangle([4, 4, 27, 12], fill=rgb(0x40D060))
    text(img, "$0.00", (4, 4, 28, 13), 0x0A2A0A, 5)
    save(img, "register")
    img = Image.new("RGBA", (S, S), rgb(0x2A1810))
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, S - 2], fill=rgb(0xB8D8E0))
    for x, c in ((4, 0xC88030), (12, 0xE0B040), (20, 0xA05030)):
        d.ellipse([x, 18, x + 7, 26], fill=rgb(c))
    save(img, "foodcase")
    img = noise(0x9A9EA2, 3, "stovetop")
    d = ImageDraw.Draw(img)
    for x, y in ((4, 4), (18, 4), (4, 18), (18, 18)):
        d.ellipse([x, y, x + 9, y + 9], outline=rgb(0x1A1A1A), width=2)
    save(img, "stovetop")
    img = noise(0x9A9EA2, 3, "stovefront")
    d = ImageDraw.Draw(img)
    for x in (5, 12, 19, 26):
        d.ellipse([x - 2, 3, x + 1, 6], fill=rgb(0x1A1A1A))
    d.rectangle([4, 10, 27, 27], fill=rgb(0x2A2E34), outline=rgb(0x6A6E72))
    d.rectangle([8, 12, 23, 14], fill=rgb(0xC8CCD0))
    save(img, "stovefront")
    img = noise(0x9A9EA2, 3, "fryertop")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0xC89A30))
    for k in range(4, 28, 4):
        d.line([4, k, 27, k], fill=rgb(0x8A6A20))
    save(img, "fryertop")
    img = Image.new("RGBA", (S, S), rgb(0x8A8E92))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("snackshelf"))
    for row in range(3):
        x = 1
        while x < S - 4:
            w = rng.randint(4, 6)
            c = rng.choice([0xE82020, 0xF0C020, 0x2060E0, 0x30A040, 0xE87020, 0xA040C0])
            d.rectangle([x, row * 11 + 2, x + w - 1, row * 11 + 9], fill=rgb(c))
            d.line([x + 1, row * 11 + 4, x + w - 2, row * 11 + 4], fill=rgb(0xF4F4F0))
            x += w + 1
        d.line([0, row * 11 + 10, S - 1, row * 11 + 10], fill=rgb(0x5A5E62))
    save(img, "snackshelf")
    # The snack machine: its blue cabinet, the lit header, the dark inside behind the glass, the packets on their
    # spirals (four 4-unit bands, one a column), a glint on the glass (the rest of it see-through), and the coin panel
    # (drawn in the middle 8 px, for a face 4 wide)
    save(noise(0x2A6AB0, 4, "snackvending"), "snackvending")
    img = noise(0x2A6AB0, 3, "snackvendhead")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, 8], fill=rgb(0xF4F0E4))
    text(img, "SNACKS", (1, 1, S - 1, 9), rgb(0xD02020), 7)
    save(img, "snackvendhead")
    save(noise(0x16191E, 3, "snackvendinside"), "snackvendinside")
    img = Image.new("RGBA", (S, S), rgb(0x1A1E24))
    d = ImageDraw.Draw(img)
    for band, (c, logo) in enumerate(((0xE82020, 0xF0C020), (0xF0C020, 0xC02020), (0x30A040, 0xF4F4F0), (0xE87020, 0x6A2A10))):
        x0 = band * 8
        d.rectangle([x0, 0, x0 + 5, S - 1], fill=rgb(c))
        d.line([x0, 0, x0 + 5, 0], fill=T.shade(T.hexrgb(c), 0.7))
        for y in range(2, S, 6):
            d.rectangle([x0 + 1, y, x0 + 4, y + 1], fill=rgb(logo))
        for y in range(0, S, 3):
            d.point((x0 + 5, y), fill=rgb(0xB8BCC0))  # the spiral's turns in front of the packets
            d.point((x0, y + 1), fill=rgb(0x8A8E92))
    save(img, "snackvendrows")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for x0 in (4, 20):
        d.line([x0, S - 1, x0 + 10, 0], fill=(214, 230, 240, 255))
    d.line([25, S - 1, 31, 12], fill=(214, 230, 240, 255))
    save(img, "snackvendglass")
    img = noise(0x3A3E44, 3, "snackvendpanel")
    d = ImageDraw.Draw(img)
    d.rectangle([12, 2, 19, 5], fill=rgb(0x1A2A1A))
    d.line([13, 3, 17, 3], fill=rgb(0x60E060))  # the price display
    for r in range(4):
        for c in range(3):
            d.point((13 + c * 2, 8 + r * 2), fill=rgb(0xD8D8D0))
    d.rectangle([14, 17, 17, 21], fill=rgb(0xB8BCC0))
    d.line([15, 18, 15, 20], fill=rgb(0x101010))  # the coin slot
    d.rectangle([13, 24, 18, 26], fill=rgb(0x8A8E92))
    d.rectangle([14, 25, 17, 25], fill=rgb(0x1A1A1A))  # coin return
    save(img, "snackvendpanel")
    img = Image.new("RGBA", (S, S), rgb(0xD8DCE0))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 2, 28, 29], fill=rgb(0x2A3A44))
    for r in range(4):
        for c in range(4):
            d.rectangle([5 + c * 6, 4 + r * 6, 8 + c * 6, 8 + r * 6], fill=rgb([0xE82020, 0x30A0E0, 0xF4F0E0, 0x40C040][(r + c) % 4]))
    d.rectangle([26, 10, 27, 20], fill=rgb(0xC8CCD0))
    save(img, "drinkfridge")
    # The drinks fridge in 3D: white enamel, a lit header, a kick-plate grille, cold white inside, frosted glass (see-
    # through but for its glints and a frosted rim), and the cans and bottles: four 4-unit bands, one a column
    save(noise(0xE6E8EA, 3, "fridgebody"), "fridgebody")
    img = noise(0x1E4A8A, 2, "drinkhead")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, 8], fill=rgb(0xF4F8FC))
    text(img, "DRINKS", (1, 1, S - 1, 9), rgb(0x1E4A9A), 7)
    save(img, "drinkhead")
    img = Image.new("RGBA", (S, S), rgb(0x2A2C30))
    d = ImageDraw.Draw(img)
    for y in range(1, S, 3):
        d.line([2, y, S - 3, y], fill=rgb(0x0E0F11))
    save(img, "fridgegrille")
    save(noise(0xDCE8F0, 2, "fridgeinside"), "fridgeinside")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for x0 in (3, 18):
        d.line([x0, S - 1, x0 + 9, 0], fill=(224, 238, 248, 200))
    d.rectangle([0, 0, S - 1, S - 1], outline=(220, 232, 240, 110), width=1)  # frost at the rim
    save(img, "fridgeglass")
    img = Image.new("RGBA", (S, S), rgb(0x1A1E24))
    d = ImageDraw.Draw(img)
    for band, (c, label) in enumerate(((0xC81E1E, 0xF4F0E8), (0x2E9A3A, 0xF0E040), (0x7AB8E8, 0x2A5AA8), (0xF08A1E, 0xFFFFFF))):
        x0 = band * 8
        d.rectangle([x0, 0, x0 + 5, S - 1], fill=rgb(c))
        d.line([x0 + 1, 0, x0 + 1, S - 1], fill=T.shade(T.hexrgb(c), 1.3))  # the shine down a can
        for y in range(3, S, 8):
            d.rectangle([x0, y, x0 + 5, y + 2], fill=rgb(label))
        d.line([x0, 0, x0 + 5, 0], fill=rgb(0xB8BCC0))  # the lids
    save(img, "drinkcans")
    # A dead machine of a vending room's heap: faded red, scuffed, its sign unlit, its glass cracked
    img = noise(0x8A2A24, 5, "vendpilebody")
    grime(img, "vendpilebody", 0.35, (60, 40, 30))
    d = ImageDraw.Draw(img)
    rng = random.Random(61)
    for _ in range(5):
        x, y = rng.randrange(S), rng.randrange(S)
        d.line([x, y, x + rng.randint(2, 6), y + rng.randint(-1, 1)], fill=rgb(0xB8B0A8))  # scuffs to the paint
    save(img, "vendpilebody")
    img = noise(0x6A2420, 3, "vendpilehead")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, 8], fill=rgb(0xB8B0A0))
    text(img, "COLA", (1, 1, S - 1, 9), rgb(0x7A1A14), 7)
    save(img, "vendpilehead")
    img = noise(0x3A3C40, 3, "vendpilepanel")
    d = ImageDraw.Draw(img)
    d.rectangle([12, 2, 19, 5], fill=rgb(0x141414))  # a dead display
    for r in range(4):
        for c in range(3):
            d.point((13 + c * 2, 8 + r * 2), fill=rgb(0x9A9A94))
    d.line([15, 18, 15, 20], fill=rgb(0x101010))
    save(img, "vendpilepanel")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for pts in (((20, 9), (13, 3), (9, 0)), ((20, 9), (27, 4)), ((20, 9), (24, 20), (22, 31)), ((20, 9), (8, 14), (0, 15))):
        d.line(pts, fill=(226, 232, 236, 210))  # cracks spreading from a blow
    d.line([4, S - 1, 12, 18], fill=(214, 230, 240, 150))
    save(img, "vendpileglass")
    for name, word, color in (("signburger", "BURGERS", 0xFF4060), ("signpizza", "PIZZA", 0x40FF90), ("signtaco", "TACOS", 0xFFC040), ("signdonut", "DONUTS", 0x60C0FF)):
        img = Image.new("RGBA", (S, S), rgb(0x141018))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(color), width=1)
        text(img, word, (1, 8, 31, 24), color, 8)
        save(img, name)
    img = Image.new("RGBA", (S, S), rgb(0x1A1A1A))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A6A3A), width=2)
    for y, w in ((5, 16), (10, 20), (15, 14), (20, 18), (25, 12)):
        d.line([4, y, 4 + w, y], fill=rgb(0xF0F0E8))
        d.line([26, y, 28, y], fill=rgb(0xF0C040))
    save(img, "menuboard")
    img = noise(0xF4F0E8, 2, "mallmap")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    d.rectangle([12, 4, 19, 27], fill=rgb(0xC8E8E4))
    d.rectangle([4, 12, 27, 19], fill=rgb(0xC8E8E4))
    for x, y, c in ((5, 5, 0xE88AA0), (21, 5, 0xF0C040), (5, 21, 0x7AC8C0), (21, 21, 0xA080D0)):
        d.rectangle([x, y, x + 5, y + 5], fill=rgb(c))
    d.ellipse([14, 14, 17, 17], fill=rgb(0xD82020))
    save(img, "mallmap")

    # Food: snacks and drinks
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(7, 5), (25, 5), (27, 27), (5, 27)], fill=rgb(0xE8C020), outline=rgb(0xA08010))
    d.rectangle([7, 12, 25, 20], fill=rgb(0xD82020))
    text(img, "CHIPS", (7, 12, 26, 21), 0xF4F0E0, 5)
    save_item(img, "chips")
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(4, 18), (24, 6), (28, 12), (8, 24)], fill=rgb(0x5A2A14), outline=rgb(0x2A1408))
    d.polygon([(10, 16), (20, 10), (23, 14), (13, 20)], fill=rgb(0xE8C040))
    save_item(img, "candybar")
    img = sprite()
    d = ImageDraw.Draw(img)
    d.rectangle([10, 6, 21, 27], fill=rgb(0xC82020), outline=rgb(0x801010))
    d.rectangle([10, 6, 21, 8], fill=rgb(0xC8CCD0))
    d.line([12, 14, 19, 18], fill=rgb(0xF4F0E8), width=2)
    save_item(img, "soda")
    for name, liquid in (("cashewwater", 0xE8D8B0), ("waterbottle", 0xB8D8F0)):
        img = sprite()
        d = ImageDraw.Draw(img)
        d.rectangle([13, 3, 18, 7], fill=rgb(0x3A6AB0 if name == "waterbottle" else 0x8A5A2A))
        d.polygon([(11, 8), (20, 8), (22, 12), (22, 28), (9, 28), (9, 12)], fill=rgb(liquid, 220), outline=rgb(0x8A9AA8))
        d.rectangle([9, 15, 22, 21], fill=rgb(0xF4F0E8))
        save_item(img, name)


# ---------------- Level 7 ----------------

def level7():
    img = noise(0x5E6466, 6, "oceanceiling")
    T.blotch(img, (10, 22), 8, (40, 56, 60), 0.35, 91)
    d = ImageDraw.Draw(img)
    for x in (5, 19, 27):
        d.line([x, 24, x, 31], fill=rgb(0x485052))  # water stains running down
    save(img, "oceanceiling")
    # The islands' unknown rock: dark grey-green basalt broken into angular facets, each its own shade, with dark
    # cracks between them, a pale edge where a facet catches the light, and a few specks of lichen
    rng = random.Random(seed_of("islandrock"))
    pts = [(rng.uniform(0, S), rng.uniform(0, S)) for _ in range(6)]
    shades = [rng.uniform(0.8, 1.1) for _ in pts]
    cracked = {(a, b): rng.random() < 0.55 for a in range(len(pts)) for b in range(len(pts))}
    img = noise(0x4A4F4C, 10, "islandrock")
    px = img.load()
    def nearest(x, y):
        best = []
        for i, (cx, cy) in enumerate(pts):
            for ox in (-S, 0, S):
                for oy in (-S, 0, S):
                    best.append(((x - cx - ox) ** 2 + (y - cy - oy) ** 2, i))
        best.sort()
        return best[0][1], math.sqrt(best[1][0]) - math.sqrt(best[0][0]), best[1][1]
    for y in range(S):
        for x in range(S):
            i, edge, other = nearest(x + 0.5, y + 0.5)
            c = px[x, y]
            k = shades[i] * (1 + 0.1 * ((x - pts[i][0]) + (y - pts[i][1])) / S)  # each facet lit from one side
            c = tuple(max(0, min(255, int(v * k))) for v in c[:3])
            if edge < 0.7 and cracked[min(i, other), max(i, other)]:
                c = (24, 27, 26)  # a crack (not every facet is split from its neighbour)
            elif edge < 1.8 and nearest(x - 0.5, y - 0.5)[0] != i:
                c = tuple(min(255, int(v * 1.25)) for v in c)  # the lit lip of a facet
            px[x, y] = c + (255,)
    specks(img, [0x6E7A5A, 0x8A946A, 0x2A302C], 14, "islandrock-lichen")
    save(img, "islandrock")
    # Tar: glossy near-black, a faint broad sheen across it; on top, a few soft domes where bubbles are rising, each
    # with a pinpoint highlight; down the sides, slow drips with a glint along them and a bead at the end
    def tar_base(key):
        img = noise(0x0A0A0C, 2, key)
        px = img.load()
        for y in range(S):
            for x in range(S):
                t = max(0.0, 1 - abs((x + y) - 26) / 9)
                c = px[x, y]
                px[x, y] = tuple(min(255, int(v + 12 * t)) for v in c[:3]) + (255,)
        return img
    img = tar_base("tar")
    px = img.load()
    for cx, cy, r in ((9, 22, 4.5), (23, 9, 3.5), (25, 25, 2.5)):
        for y in range(S):
            for x in range(S):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / r
                if d < 1:
                    c = px[x, y]
                    px[x, y] = tuple(min(255, int(v + 26 * (1 - d * d))) for v in c[:3]) + (255,)
        hx, hy = int(cx - r * 0.4), int(cy - r * 0.4)
        px[hx, hy] = (92, 92, 102, 255)
        px[hx + 1, hy] = (56, 56, 64, 255)
    save(img, "tar")
    img = tar_base("tar-side")
    px = img.load()
    rng = random.Random(93)
    for x0 in (3, 10, 19, 27):
        length = rng.randint(10, 26)
        for y in range(length):
            for x in (x0, x0 + 1):
                px[x, y] = (6, 6, 8, 255)
            px[x0 + 1, y] = (34, 34, 40, 255) if y % 7 != 3 else (52, 52, 60, 255)  # the glint along it
        for x in range(x0 - 1, x0 + 3):
            px[x, length] = (8, 8, 10, 255)
        px[x0, length + 1] = (8, 8, 10, 255)
        px[x0 + 1, length + 1] = (8, 8, 10, 255)
        px[x0 + 1, length] = (70, 70, 80, 255)  # the bead's highlight
    save(img, "tar-side")
    flat("bone", 0xE4D8BC, 6)
    flat("scrap", 0x7A4A2A, 14)
    img = noise(0x8A7A50, 5, "canvas")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 12, 27, 24], fill=rgb(0x6A5A38))
    d.line([4, 18, 27, 18], fill=rgb(0x4A3A20))
    save(img, "canvas")
    img = noise(0x3A2A1C, 8, "wetwood")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x221810), width=3)
    d.line([3, 3, S - 4, S - 4], fill=rgb(0x2A1E14), width=2)
    save(img, "wetwood")


# ---------------- Level 8 ----------------

def level8():
    img = noise(0xD8D0B8, 3, "megplate")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    d.ellipse([4, 3, 27, 18], outline=rgb(0x2A4A8A), width=2)
    text(img, "M.E.G.", (5, 5, 27, 16), 0x2A4A8A, 6)
    text(img, "9TH ROAD", (1, 20, 31, 29), 0x2A2A2A, 5)
    save(img, "megplate")
    img = noise(0xFFD890, 4, "lampglass")
    ImageDraw.Draw(img).rectangle([12, 0, 19, S - 1], fill=rgb(0xFFF4D0))
    save(img, "lampglass")
    flat("cavestone", 0x8A8478, 8)
    # Bioluminescent fungi: caps that glow from within (a brighter rim and gills, paler speckles), stems, and the
    # mycelium they grow from; blood-red, and the other colours of the mixed clusters
    for name, cap, rim in (("glowcapred", 0xB01818, 0xFF5A40), ("glowcapblue", 0x2A6AD8, 0x8AD8FF),
                           ("glowcapviolet", 0x8A2AC8, 0xE09AFF), ("glowcapgreen", 0x38B850, 0xB8FF8A)):
        img = noise(cap, 6, name)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(rim), width=2)
        rng = random.Random(seed_of(name))
        for _ in range(10):
            x, y = rng.randrange(3, S - 3), rng.randrange(3, S - 3)
            d.rectangle([x, y, x + 1, y + 1], fill=T.shade(T.hexrgb(rim), 1.15))
        save(img, name)
    img = noise(0xD8CCB8, 4, "glowstem")
    save(img, "glowstem")
    img = noise(0x3A1414, 5, "mycelium")
    specks(img, [0x7A2A20, 0xA03A2A, 0x1A0A0A], 40, "mycelium")
    save(img, "mycelium")


# ---------------- Level 9 ----------------

ASPHALT = (48, 49, 50)
ASPHALT_MEAN = (48.5, 49.0, 49.1)  # the road's tone before B7 (and before B11): kept


def asphalt_version(k=0):
    """(B7, at the user's request after B11) The Suburbs' road: a fine, even wearing course: dense 1 px aggregate that
    lifts the binder only a little (matlib.asphalt with a low `chip` range, few pits, faint shadows), almost no broad
    mottle and few binder-rich patches, so it reads as one smooth dark road rather than a speckle. Three versions
    (`k`) differ only in their chips; their broad field is one shared ground at the block edges (`matlib.turn_safe`), so
    the blocktype turns and mixes them without a patchwork. The tone is the old road's."""
    img = M.asphalt(seed=seed_of("asphalt") + 7 * k, base=ASPHALT, grain=2, mottle=2, aggregate=0.45, binder=0.2,
                    chip=(3, 11), pits=0.004, shadow=0.06)
    ground = M.noise_hv(ASPHALT, 0, seed_of("asphalt"), S, 2, (16,), hue=0)
    M.turn_safe(img, ground, band=8, keep=0.5)
    return T.match_rgb(img, ASPHALT_MEAN, "asphalt")


def asphalt_base():
    """The road every marking, the leaves and Level 11's streets (gen_city reads asphalt.png) are painted on."""
    return asphalt_version(0)


def _blob(cx, cy, r, seed, wobble=0.3):
    """A soft, irregular round mask (0..1) about (cx, cy): its radius wanders with the angle (a few lobes from a seeded
    sum of sines), its edge fades over 1.5 px. For patches that must not have straight sides."""
    rng = random.Random(seed)
    lobes = [(rng.randint(2, 5), rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 1.0)) for _ in range(3)]
    norm = sum(a for _, _, a in lobes)
    out = [[0.0] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) * 1.15
            ang = math.atan2(dy, dx)
            rr = r * (1 + wobble * sum(a * math.sin(n * ang + ph) for n, ph, a in lobes) / norm)
            out[y][x] = max(0.0, min(1.0, (rr - math.hypot(dx, dy)) / 1.5 + 0.5))
    return out


def asphalt_features():
    """asphalt-2, a crack wandering across the middle of the block, filled with tar (a dark line in a faint glossy
    band); asphalt-3, an old cold-mix patch: an irregular, soft-edged blob, smoother and a shade darker than the road,
    its rim sealed. Both kept inside the block (the versions are turned and mixed) and faint; each is listed one block
    in sixteen (gen_deep.level9). B11's were a straight full-height crack and a square patch."""
    plain = asphalt_version(1)
    img = plain.copy()
    rng = random.Random(seed_of("asphalt-crack"))
    x, y, a = 7.0, 10.0, rng.uniform(-0.3, 0.3)
    for i in range(24):
        xi, yi = int(x) % S, int(y) % S
        M.put(img.load(), S, S, xi, yi, (36, 37, 38))  # (round 2) fainter
        M.touch(img, xi, yi - 1, -0.06)
        M.touch(img, xi, yi + 1, -0.05)
        if i % 3 == 0:
            M.touch(img, xi, yi - 1, 0.08)  # the tar's gloss
        a = a * 0.7 + rng.uniform(-0.45, 0.45)  # wanders, but keeps on across the block
        x, y = x + math.cos(a) * 0.8, y + 0.45 + math.sin(a) * 0.5
    save(T.inside_block(plain, img, band=3), "asphalt-2")
    plain = asphalt_version(2)
    img = plain.copy()
    patch = M.asphalt(seed=seed_of("asphalt-patch"), base=(42, 43, 44), grain=2, mottle=2, aggregate=0.3, binder=0.4,
                      chip=(2, 8), pits=0.002, shadow=0.04)
    mask = _blob(16, 15, 8.5, seed_of("asphalt-patchshape"))
    p, q = img.load(), patch.load()
    for yy in range(S):
        for xx in range(S):
            m = mask[yy][xx]
            if m > 0:
                c = M.mix(p[xx, yy], q[xx, yy], m)
                if 0.15 < m < 0.75:  # the sealed rim: a dark seam of tar round the edge
                    c = M.lift(c, -4)
                p[xx, yy] = M.rgba(c)
    save(T.inside_block(plain, img), "asphalt-3")


def painted_mark(img, box, colour, k=0.55):
    """(B7) Road paint over the asphalt: the paint's colour taking the road's own light and dark (so the line has the
    grain under it), clean to the box's edges, which run to the block's edges, so a line meets the next one."""
    x0, y0, x1, y1 = box
    px = img.load()
    base = M.lum(ASPHALT)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = M.rgba(M.lift(colour, (M.lum(px[x, y]) - base) * k))
    return img


def level9():
    img = asphalt_base()
    save(img, "asphalt")
    save(asphalt_version(1), "asphalt-4")  # (B7) the plain road's other two versions
    save(asphalt_version(2), "asphalt-5")
    asphalt_features()
    leaves = img.copy()
    rng = random.Random(101)
    d = ImageDraw.Draw(leaves)
    for _ in range(14):
        x, y = rng.randrange(S - 3), rng.randrange(S - 3)
        d.ellipse([x, y, x + 3, y + 2], fill=rgb(rng.choice([0x8A5A1E, 0xB07A20, 0x6A3A14, 0x9A2A14])))
    save(leaves, "asphalt-leaves")
    # Wet asphalt: standing water, smoother and darker than the dry road, with the sky in it as a blue-grey sheen in
    # long ripples and a glint or two, so a puddle reads as water and not as a shadow. The ripples wrap round the tile
    # (it is turned at random from block to block, so they never line up)
    wet = noise(0x181C24, 2, "asphaltwet")
    px = wet.load()
    for y in range(S):
        for x in range(S):
            ripple = 0.5 + 0.5 * math.sin(2 * math.pi * (x + 3 * y) / S + 0.8 * math.sin(2 * math.pi * 2 * x / S))
            t = 0.06 + 0.22 * ripple ** 3
            r_, g_, b_, a_ = px[x, y]
            px[x, y] = (int(r_ + (78 - r_) * t), int(g_ + (90 - g_) * t), int(b_ + (112 - b_) * t), a_)
    rng = random.Random(102)
    for _ in range(5):
        wet.putpixel((rng.randrange(S), rng.randrange(S)), (128, 138, 156, 255))
    save(wet, "asphalt-wet")
    img = M.concrete(seed=seed_of("sidewalk"), base=(156, 153, 144), grain=3, mottle=5, aggregate=0.05, pores=0.01)
    M.emboss_lines(img, xs=(0,), ys=(0, 16), strength=0.3)
    save(img, "sidewalk")
    img = noise(0x8A5E38, 5, "housewood")
    for y in range(0, S, 5):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x6A4424))
    save(img, "housefloor-wood")
    save(noise(0x7A6A60, 5, "housecarpet"), "housefloor-carpet")
    img = noise(0xE8ECF0, 2, "housetile")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0xA8B0B8))
        d.line([k, 0, k, S - 1], fill=rgb(0xA8B0B8))
    save(img, "housefloor-tile")
    img = Image.new("RGBA", (S, S))
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), rgb(0xE8DCC0 if (x // 8 + y // 8) % 2 == 0 else 0xC89A6A))
    save(img, "housefloor-lino")
    save(T.concrete_floor("plain"), "housefloor-garage")
    # (the painted siding: exteriors_b11)
    save(grime(block_wall(0x9A4A34, 0xC8B8A8, "brick", rows=8), "brick", 0.15), "siding-brick")
    save(noise(0xE6DCC8, 2, "plaster-interior"), "plaster-interior")
    img = noise(0xE8DCC8, 2, "paper-floral")
    rng = random.Random(111)
    d = ImageDraw.Draw(img)
    for y in range(4, S, 10):
        for x in range(4 + (y // 10 % 2) * 5, S, 10):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=rgb(0xC87888))
            d.point((x + 3, y + 1), fill=rgb(0x6A9A5A))
    save(img, "houseinterior-floral")
    img = noise(0xD8D8E8, 2, "paper-stripe")
    for x in range(0, S, 6):
        ImageDraw.Draw(img).rectangle([x, 0, x + 1, S - 1], fill=rgb(0xA8A8C8))
    save(img, "houseinterior-stripe")
    save(noise(0xD8C8A8, 3, "paper-beige"), "houseinterior-beige")
    img = noise(0xA8C0A0, 3, "paper-green")
    for y in range(0, S, 8):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x98B090))
    save(img, "houseinterior-green")
    img = noise(0xF0F2F4, 2, "paper-tile")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0xB8C0C8))
        d.line([k, 0, k, S - 1], fill=rgb(0xB8C0C8))
    save(img, "houseinterior-tile")
    # The glass of a house window (the frame, the glazing bars and the sill are the block's own boxes): dark, with the
    # night sky's faint sheen across it and the curtains just showing at the sides; or lit, warm, the curtains drawn
    # back in folds either side
    def lerp(a, b, f):
        return tuple(p + (q - p) * f for p, q in zip(a[:3], b[:3]))

    for state in ("dark", "lit"):
        img = Image.new("RGBA", (S, S))
        px = img.load()
        rng = random.Random(seed_of("housewindow" + state))
        for y in range(S):
            for x in range(S):
                edge = min(x, S - 1 - x)
                fold = 0.85 + 0.15 * math.sin(x * 1.9)
                if state == "dark":
                    sheen = max(0.0, 1 - abs((x + y * 0.6) - 18) / 6) * 0.35
                    c = lerp(T.hexrgb(0x0C1018), T.hexrgb(0x2A3442), 0.25 * (1 - y / S) + sheen)
                    if edge < 5:
                        c = lerp(c, T.shade(T.hexrgb(0x3A3028), fold), 0.55)
                else:
                    glow = 1 - abs(x - S / 2) / (S / 2) * 0.35 - y / S * 0.1
                    c = T.shade(T.hexrgb(0xFFD890), glow)
                    if edge < 6:
                        c = T.shade(T.hexrgb(0xD8904A), fold * (0.8 + 0.04 * edge))
                k = rng.uniform(0.96, 1.04)
                px[x, y] = tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)
        save(img, f"housewindow-{state}")
    # Painted wood: the window frames, a porch's posts and the skirt round its deck
    img = noise(0xEEEDE6, 2, "windowtrim")
    d = ImageDraw.Draw(img)
    for y in (7, 19, 28):
        d.line([0, y, S - 1, y], fill=rgb(0xDCDAD0))
    save(img, "windowtrim")
    # A porch lamp with no power: dusty amber glass
    img = noise(0x5A4A30, 4, "porchglass-off")
    ImageDraw.Draw(img).line([4, 4, 12, 20], fill=rgb(0x7A6A50))
    save(img, "porchglass-off")
    # The concrete step up to a porch
    img = noise(0xB8B4AA, 4, "porchstep")
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xA09C92))
    save(img, "porchstep")
    # Street names on the Suburbs' corners, white on green; the same few over and over
    for street in ("elm", "oak", "maple", "pine", "cedar", "birch", "walnut", "ash"):
        img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
        text(img, f"{street.upper()} ST", (0, 6, S, 26), 0xFFFFFF, 5)
        ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFFFFF))
        save(img, f"suburbsign-{street}")
    for street in ("willow", "linden", "aspen", "poplar", "holly", "laurel", "spruce", "cherry"):
        img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
        text(img, f"{street.upper()} AV", (0, 6, S, 26), 0xFFFFFF, 5)
        ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFFFFF))
        save(img, f"suburbsignblade-{street}")
    # The guide sign toward the city: DOWNTOWN in plain block capitals (three pixels wide, doubled in height, to fill
    # the plate) and an arrow, as read from either side
    glyphs = {"D": ["110", "101", "101", "101", "110"], "O": ["111", "101", "101", "101", "111"],
              "W": ["101", "101", "111", "111", "101"], "N": ["110", "101", "101", "101", "101"], "T": ["111", "010", "010", "010", "010"]}
    for side in ("right", "left"):
        img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
        d = ImageDraw.Draw(img)
        d.line([0, 1, S - 1, 1], fill=rgb(0xFFFFFF))
        d.line([0, S - 2, S - 1, S - 2], fill=rgb(0xFFFFFF))
        for k, ch in enumerate("DOWNTOWN"):
            for gy, row in enumerate(glyphs[ch]):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        d.rectangle([k * 4 + gx, 5 + gy * 2, k * 4 + gx, 6 + gy * 2], fill=rgb(0xFFFFFF))
        # The arrow, drawn rather than lettered so it is the same in any font
        tip = S - 6 if side == "right" else 5
        tail = 6 if side == "right" else S - 7
        d.line([tail, 22, tip, 22], fill=rgb(0xFFFFFF), width=2)
        k = -1 if side == "right" else 1
        d.polygon([(tip - k, 22), (tip + k * 5, 17), (tip + k * 5, 27)], fill=rgb(0xFFFFFF))
        save(img, f"citysign-{side}")
    # (the roofing: exteriors_b11)
    img = noise(0xF0EEE8, 6, "popcorn")
    save(img, "houseceiling")
    for part in ("lower", "upper"):
        img = M.noise_hv((136, 48, 36), amp=3, seed=seed_of("housedoor" + part), mottle=4, hue=2)
        # the casing round the door, painted like the windows
        trim = M.noise_hv(TRIM, amp=2, seed=seed_of("doortrim" + part), mottle=2, hue=1)
        for y in range(S):
            for x in list(range(0, 2)) + list(range(S - 2, S)):
                img.putpixel((x, y), trim.getpixel((x, y)))
        if part == "upper":
            for x in range(S):
                for y in (0, 1):
                    img.putpixel((x, y), trim.getpixel((x, y)))
        M.inset(img, (2, 0 if part == "lower" else 2, S - 2, S), strength=0.3)
        panels = ((5, 3, 15, 28), (17, 3, 27, 28)) if part == "lower" else ((5, 18, 15, 30), (17, 18, 27, 30))
        for box in panels:
            M.inset(img, box, strength=0.24)
            M.bevel(img, (box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1), strength=0.14)
        if part == "lower":
            for x, y, f in ((22, 1, 0.5), (23, 1, 0.7), (22, 2, 0.3), (23, 2, 0.2), (24, 2, 0.0), (23, 3, -0.2)):
                img.putpixel((x, y), M.rgba(M.shade_px((200, 160, 70), f)))
        else:
            glass = Image.new("RGBA", (12, 10), (26, 32, 40, 255))
            for y in range(10):
                for x in range(12):
                    sheen = max(0.0, 1 - abs((x + y * 0.6) - 7) / 3) * 0.25
                    glass.putpixel((x, y), M.rgba(M.mix((26, 32, 40), (70, 84, 100), sheen + 0.1 * (1 - y / 10))))
            img.paste(glass, (10, 5))
            M.inset(img, (9, 4, 23, 16), strength=0.3)
        save(img, f"housedoor-{part}")
        img = M.noise_hv((226, 224, 214), amp=2, seed=seed_of("garage" + part), mottle=3, hue=1)
        for y0 in range(0, S, 8):
            M.emboss_lines(img, ys=(y0,), strength=0.28)
            for x0 in (2, 17):
                M.inset(img, (x0, y0 + 2, x0 + 13, y0 + 7), strength=0.2)
                M.bevel(img, (x0 + 1, y0 + 3, x0 + 12, y0 + 6), strength=0.16)
        save(img, f"garagedoor-{part}")
    flat("tvwood", 0x5A3A22, 4)
    img = Image.new("RGBA", (S, S), rgb(0x1A1A1C))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 4, 24, 26], 4, fill=rgb(0x2A3036))
    d.line([6, 8, 12, 12], fill=rgb(0x4A5258))
    for y in (8, 14, 20):
        d.ellipse([26, y, 29, y + 3], fill=rgb(0x8A8E92))
    save(img, "tvscreen")
    flat("enamel", 0xF0F0EC, 2)
    flat("dresserwood", 0x7A5232, 5)
    img = noise(0x7A5232, 5, "dresserfront")
    d = ImageDraw.Draw(img)
    for y in (2, 12, 22):
        d.rectangle([2, y, S - 3, y + 8], outline=rgb(0x4A3018))
        d.rectangle([13, y + 3, 18, y + 4], fill=rgb(0xC8A050))
    save(img, "dresserfront")
    img = noise(0xFFF0C0, 3, "streetlamp")
    save(img, "streetlamp")
    save(noise(0x8A9094, 3, "streetlampoff"), "streetlampoff")
    save(M.painted_metal(seed=seed_of("mailbox"), base=(44, 60, 92), panel=False, chips=0), "mailbox")
    img = noise(0xA88A5A, 10, "burlap")
    for k in range(0, S, 3):
        ImageDraw.Draw(img).line([0, k, S - 1, k], fill=rgb(0x8A6E44))
    save(img, "burlap")
    img = Image.new("RGBA", (S, S), rgb(0x6A4A2A))
    d = ImageDraw.Draw(img)
    rng = random.Random(121)
    for row in range(3):
        for x in range(2, S - 4, 6):
            c = rng.choice([0xC8B070, 0xA03020, 0x3A6AB0, 0xE8E0C8, 0x6A8A3A])
            d.rectangle([x, row * 11 + 3, x + 4, row * 11 + 9], fill=rgb(c))
        d.line([0, row * 11 + 10, S - 1, row * 11 + 10], fill=rgb(0x4A3018))
    save(img, "pantry")
    img = Image.new("RGBA", (S, S), rgb(0x5A5E62))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 9, 14], fill=rgb(0xB02018))
    d.rectangle([13, 4, 15, 15], fill=rgb(0x8A6A3A))
    d.rectangle([12, 3, 18, 6], fill=rgb(0x8A8E92))
    d.rectangle([20, 3, 29, 9], fill=rgb(0xE0B020))
    d.ellipse([3, 18, 14, 29], outline=rgb(0x2A6A2A), width=2)
    d.rectangle([18, 20, 29, 28], fill=rgb(0x8A8E92))
    save(img, "toolwall")
    img = noise(0xC89A6A, 4, "cabinetfront")
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, S - 1], fill=rgb(0x8A6A44))
    d.rectangle([2, 2, 14, S - 3], outline=rgb(0x8A6A44))
    d.rectangle([18, 2, 29, S - 3], outline=rgb(0x8A6A44))
    d.rectangle([12, 14, 13, 18], fill=rgb(0xC8CCD0))
    d.rectangle([19, 14, 20, 18], fill=rgb(0xC8CCD0))
    save(img, "cabinetfront")


# ---------------- Level 10 ----------------

def level10():
    img = noise(0x8A6E4A, 6, "dirtroad")
    specks(img, [0x6A5236, 0xA0845A, 0x5A4630], 60, "dirtroad")
    save(img, "dirtroad")
    tracks = img.copy()
    d = ImageDraw.Draw(tracks)
    for x in (5, 24):
        d.rectangle([x, 0, x + 3, S - 1], fill=rgb(0x5E4A32))
        for y in range(0, S, 4):
            d.line([x, y, x + 3, y + 1], fill=rgb(0x4E3C28))
    save(tracks, "dirtroad-tracks")
    # (the barns' boards and tin: exteriors_b11)
    img = noise(0x8A4A4A, 10, "wormmass")
    d = ImageDraw.Draw(img)
    rng = random.Random(131)
    for _ in range(26):
        x, y = rng.randrange(S), rng.randrange(S)
        pts = [(x, y)]
        for k in range(4):
            x, y = x + rng.randint(-3, 3), y + rng.randint(-3, 3)
            pts.append((x, y))
        d.line(pts, fill=rgb(rng.choice([0xC87878, 0xB06060, 0xD89090, 0x7A3A3A])), width=2)
    save(img, "wormmass")
    flat("feed", 0xC8A858, 10)
    img = noise(0x6A4A2A, 6, "barrelwood")
    d = ImageDraw.Draw(img)
    for y in (4, 27):
        d.rectangle([0, y, S - 1, y + 1], fill=rgb(0x3A3A3E))
    save(img, "barrelwood")
    img = noise(0x5A5E62, 10, "nails")
    specks(img, [0x9A9EA2, 0xB8BCC0, 0x3A3E42], 120, "nails")
    save(img, "nails")


# ---------------- Refinements: Levels 5 to 10 in more detail ----------------

def refinements():
    # Level 6: standing water on the cold floor
    img = noise(0x1E2024, 2, "l6wet")
    d = ImageDraw.Draw(img)
    for x, y, w in ((3, 6, 9), (16, 19, 12), (8, 27, 6)):
        d.line([x, y, x + w, y], fill=rgb(0x3A4048))
    save(img, "l6floor-wet")

    # Level 7: a weathered jetty
    img = noise(0x6A5A44, 5, "jetty")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x3E3226))
        d.point([(4, y + 3), (27, y + 4)], fill=rgb(0x2A2420))
    save(img, "jetty")

    # Level 9: road markings, a manhole, a porch, a drive, a rug, a drained pool, ceiling lights
    asphalt = asphalt_base()
    line = painted_mark(asphalt.copy(), (0, 13, S - 1, 18), T.hexrgb(0xD8B830))
    save(line, "asphalt-line")
    save(line.rotate(90), "asphalt-linens")
    zebra = painted_mark(asphalt.copy(), (0, 2, S - 1, 15), T.hexrgb(0xD8D8D2))
    save(zebra, "asphalt-crossing")
    save(zebra.rotate(90), "asphalt-crossingns")
    hole = asphalt.copy()
    d = ImageDraw.Draw(hole)
    d.ellipse([3, 3, 28, 28], fill=rgb(0x2E2A26), outline=rgb(0x141210))
    for k in range(7, 26, 4):
        d.line([7, k, 24, k], fill=rgb(0x403A34))
    save(hole, "asphalt-manhole")
    img = noise(0x8A8E92, 3, "porch")
    for y in range(0, S, 6):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x5E6266))
    save(img, "housefloor-porch")
    img = noise(0xB4B0A8, 3, "driveway")
    ImageDraw.Draw(img).line([0, 0, S - 1, 0], fill=rgb(0x8A8680))
    save(img, "housefloor-driveway")
    img = noise(0x8A2A2E, 3, "rug")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, S - 3, S - 3], outline=rgb(0xC8A060))
    d.rectangle([6, 6, S - 7, S - 7], outline=rgb(0x2A3A6A))
    d.polygon([(16, 9), (23, 16), (16, 23), (9, 16)], outline=rgb(0xC8A060))
    save(img, "housefloor-rug")
    img = noise(0x8AB8CC, 2, "poolfloor")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0x6A98AC))
        d.line([k, 0, k, S - 1], fill=rgb(0x6A98AC))
    rng = random.Random(201)
    for _ in range(5):  # dead leaves and grime in the bottom
        x, y = rng.randrange(S - 3), rng.randrange(S - 3)
        d.ellipse([x, y, x + 3, y + 2], fill=rgb(rng.choice([0x6A4A24, 0x4A3A20, 0x5A6A50])))
    save(img, "pool-floor")
    save(noise(0xD8D0BC, 3, "coping"), "pool-coping")
    for name, on in (("lightoff", False), ("lighton", True)):
        img = T.noise_fill(T.hexrgb(0xE8E4DA), 2, seed_of("houseceiling"))
        d = ImageDraw.Draw(img)
        d.ellipse([8, 8, 23, 23], fill=rgb(0xFFF4D0 if on else 0xD8D4CA), outline=rgb(0xB0A890))
        save(img, f"houseceiling-{name}")
    # Exterior things
    img = Image.new("RGBA", (S, S), rgb(0xE8E6E0))
    d = ImageDraw.Draw(img)
    d.polygon([(10, 2), (22, 2), (30, 10), (30, 22), (22, 30), (10, 30), (2, 22), (2, 10)], fill=rgb(0xB01818), outline=rgb(0xF0F0F0))
    text(img, "STOP", (4, 10, 28, 22), 0xF4F4F4, 9)
    save(img, "stopsign")
    flat("binplastic", 0x2A4A2E, 4)
    img = noise(0xF0F0EC, 2, "backboard")
    ImageDraw.Draw(img).rectangle([10, 14, 21, 25], outline=rgb(0xD04A18), width=2)
    save(img, "backboard")
    save(M.painted_metal(seed=seed_of("tractorgreen"), base=(62, 98, 54), panel=False, chips=4, under=(70, 66, 60)), "tractorgreen")
    img = noise(0xC8A850, 8, "hayside")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 3):
        d.line([0, y, S - 1, y + 1], fill=rgb(0xA88A3A))
    save(img, "hayroll-side")
    img = noise(0xC8A850, 8, "hayend")
    d = ImageDraw.Draw(img)
    for r in range(3, 16, 3):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0xA0823A))
    save(img, "hayroll-end")
    # A galvanised trough out in a field, ribbed, and the rainwater in it with a leaf floating
    img = noise(0x9AA2A4, 6, "galvanised")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x, S - 1], fill=rgb(0x848C8E))
    save(img, "galvanised")
    img = noise(0x3E5A5A, 4, "troughwater")
    d = ImageDraw.Draw(img)
    d.line([3, 20, 14, 18], fill=rgb(0x96AAAC))
    d.line([18, 9, 27, 8], fill=rgb(0x789296))
    d.ellipse([22, 22, 26, 25], fill=rgb(0x606E46))
    save(img, "troughwater")
    img = noise(0xB8BCC0, 3, "icemachine")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 14, 27, 28], fill=rgb(0x6A7076))
    text(img, "ICE", (6, 2, 26, 12), 0x2A5A9A, 9)
    save(img, "icemachine")
    img = Image.new("RGBA", (S, S), rgb(0x5A3A20))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0xC8C0A8))
    for cx, h in ((10, 13), (16, 10), (22, 14)):  # a family, smiling, faded
        d.ellipse([cx - 3, h, cx + 3, h + 6], fill=rgb(0xC09070))
        d.rectangle([cx - 4, h + 6, cx + 4, 27], fill=rgb(0x5A6A8A))
    save(img, "familyphoto")
    img = noise(0xDCDAD2, 2, "washer")
    d = ImageDraw.Draw(img)
    d.ellipse([7, 9, 24, 26], fill=rgb(0x3A4048), outline=rgb(0x9AA0A8), width=2)
    d.rectangle([3, 2, 28, 6], fill=rgb(0xB8B8B0))
    save(img, "washerfront")
    img = noise(0x8A2A2A, 4, "toybox")
    d = ImageDraw.Draw(img)
    for x, c in ((5, 0xD8C030), (14, 0x3A6AC8), (23, 0x3A9A4A)):
        d.rectangle([x, 12, x + 5, 20], fill=rgb(c))
    save(img, "toybox")
    img = corrugated((172, 168, 160), seed_of("silo"))
    save(img, "silo")
    flat("silotop", 0x6A6E72, 4)
    img = noise(0xA88A52, 8, "stubble")
    d = ImageDraw.Draw(img)
    rng = random.Random(207)
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S - 2)
        d.line([x, y, x, y + 2], fill=rgb(rng.choice([0xD8C070, 0xC8B060, 0xE8D890])))
    save(img, "stubble")



# ---------------- Graphics pass B11: the Suburbs' and the farms' outsides ----------------
#
# One material family per surface, shared by every block that shows it: the lap siding on a house's walls, corners and
# gable ends (the roof blocks over a gable wall carry the same siding: gen_deep.roofs), the roofing courses, the eave's
# soffit, fascia and gutter, and the barns' boards and tin. Built from tools/matlib.py: structure, then the light from
# above, then a low grain; seamless, with the odd feature (a paint chip, a rust streak) in one alternate of three.

SIDING = {"white": (226, 224, 214), "blue": (120, 150, 182), "yellow": (222, 202, 136), "green": (136, 166, 136)}
ROOFING = {"grey": (92, 90, 88), "brown": (96, 70, 50), "red": (124, 54, 42)}
TRIM = (236, 234, 226)


def lap_siding(base, seed, wear=0):
    """Painted lap siding: eight boards of 4 px to the block, each a touch its own shade and hue; under the butt of the
    board above, a dark shadow line, then the face catching more light toward its lower edge, which stands proud.
    `wear` scatters that many paint chips (for one alternate in three)."""
    img = M.noise_hv(base, amp=3, seed=seed, mottle=2, cells=(16, 8), hue=1.0)
    px = img.load()
    rng = random.Random(M.sub(seed, "boards"))
    streak = M.value_noise((S, S), (8, 1), M.sub(seed, "streak"))
    rows = (-0.26, -0.07, 0.0, 0.05)
    for b in range(S // 4):
        dv, dh = rng.uniform(-3, 3), rng.uniform(-2, 2)
        for r in range(4):
            y = b * 4 + r
            for x in range(S):
                c = M.hue_shift(M.lift(px[x, y], dv + streak[y][x] * 3), dh)
                px[x, y] = M.rgba(M.shade_px(c, rows[r]))
    for _ in range(wear):
        x, b = rng.randrange(S), rng.randrange(S // 4)
        y = b * 4 + 3  # paint lifts at the proud lower edge first
        for k in range(rng.randint(1, 3)):
            M.put(px, S, S, x + k, y, M.lift(M.mix(px[(x + k) % S, y], (150, 132, 104), 0.4), -4))
        M.touch(img, x, y - 1, -0.06)
    return img


def shingle_courses(base, seed, courses=4, dark_tabs=0.2):
    """Laminated roofing shingles for the course-by-course roof (gen_deep.roofs). Each band of 32/courses px is one
    course; its top row is the butt (the lower, down-slope edge: an up face's v runs north to south and the roof is
    built sloping down to the north), its last rows sit in the shadow of the next course's butt, which the shape raises
    as geometry. Tabs of uneven width (as dimensional shingles have) each take their own shade and hue, a slot of the
    dark underlayer between them, granules over all."""
    img = M.noise_hv(base, amp=5, seed=seed, mottle=4, cells=(16, 8), hue=2.5)
    px = img.load()
    rng = random.Random(M.sub(seed, "tabs"))
    ch = S // courses
    for c in range(courses):
        widths = []
        while sum(widths) < S:
            widths.append(rng.choice((6, 7, 8, 9, 10, 12)))
        widths[-1] -= sum(widths) - S
        if widths[-1] < 3:
            widths[-2] += widths.pop()
        x0 = rng.randrange(S)
        for w in widths:
            tone, hue = rng.uniform(-6, 6), rng.uniform(-3, 3)
            band = rng.random() < dark_tabs  # a darker laminate tab
            for r in range(ch):
                y = c * ch + r
                f = 0.06 if r == 0 else -0.10 if r == ch - 2 else -0.24 if r == ch - 1 else 0.0
                for k in range(w):
                    x = (x0 + k) % S
                    col = M.hue_shift(M.lift(px[x, y], tone - (10 if band and r >= ch // 2 else 0)), hue)
                    if k == 0 and r < ch - 1:
                        col = M.lift(col, -32)  # the slot
                    elif k == w - 1:
                        col = M.lift(col, -5)
                    px[x, y] = M.rgba(M.shade_px(col, f))
            x0 += w
    # granules: the odd light and dark grain
    g = random.Random(M.sub(seed, "granules"))
    for _ in range(90):
        M.touch(img, g.randrange(S), g.randrange(S), g.choice((-0.12, -0.08, 0.1)))
    return img


def roof_edge(base, seed):
    """The butt and cut ends of the courses, and the edge of a ridge cap: the shingle's thickness, in shade."""
    img = M.noise_hv(M.lift(base, -10), amp=4, seed=seed, mottle=3, hue=2)
    for y in range(0, S, 4):
        for x in range(S):
            M.touch(img, x, y, 0.08)
    return img


def ridge_cap(base, seed):
    """Cap shingles along a ridge, each lapping the next: a dark butt line every 8 px across the ridge (the cap's up
    face runs u along the ridge), lit on its upper side."""
    img = M.noise_hv(M.lift(base, -6), amp=5, seed=seed, mottle=3, hue=2)
    for x0 in range(0, S, 8):
        for y in range(S):
            M.touch(img, x0, y, -0.28)
            M.touch(img, x0 + 1, y, 0.08)
            M.touch(img, x0 + 7, y, -0.08)
    return img


def soffit(base, seed, board=16):
    """The painted soffit under the eaves and the porch roofs: light panels with a fine vent perforation in a band
    along each, a shallow joint every `board` px. It is seen from below and in shade, so it is painted light and
    keeps its lines faint, or it reads as more siding."""
    img = M.noise_hv(M.lift(base, 10), amp=2, seed=seed, mottle=2, hue=1)
    for y0 in range(0, S, board):
        for x in range(S):
            M.touch(img, x, y0, -0.1)
        for x in range(1, S, 2):
            for y in (y0 + 6, y0 + 9):
                M.touch(img, x, y, -0.12)
    return img


def gutter(seed):
    """A painted aluminium gutter: the rolled lip lit along the top, the face, its shadowed underside; seen from above
    (its up face), the dark trough between two lips."""
    img = M.noise_hv((214, 214, 206), amp=2, seed=seed, mottle=2, hue=1)
    shade = {0: 0.12, 1: 0.04, 2: -0.1, 13: -0.06, 14: -0.14, 15: -0.2}
    for y in range(S):
        f = shade.get(y % 16, 0.0)
        for x in range(S):
            M.touch(img, x, y, f)
    for x in range(0, S, 16):  # a joint strap now and then
        for y in range(S):
            M.touch(img, x, y, -0.08)
    return img


def corrugated(base, seed, rust=0):
    """Corrugated tin for the barns' roofs: ribs every 4 px running down the slope (along v), each lit on its left
    flank and dark on its right; galvanising worn to grey, a rust streak down from a nail line in `rust` places."""
    img = M.noise_hv(base, amp=3, seed=seed, mottle=6, cells=(16, 8), hue=1.5)
    prof = (0.12, 0.04, -0.06, -0.16)
    for x in range(S):
        for y in range(S):
            M.touch(img, x, y, prof[x % 4])
    for y in (0, 16):  # the nail lines across the sheets
        for x in range(1, S, 4):
            M.touch(img, x, y + 3, -0.3)
    if rust:
        M.drips(img, n=rust, seed=M.sub(seed, "rust"), color=(122, 70, 40), length=(8, 20), strength=0.35, width=1)
    return img


def barn_boards(base, seed, wear=False):
    """Board and batten for the barns and sheds: three boards to the block, grain upright, and a batten every
    10-11 px as a raised strip lit on its left edge and shadowed to its right; paint gone thin at the foot in one
    alternate."""
    img = M.wood_planks(seed=seed, base=base, planks=(12, 9, 11), direction="v", grain=3, contrast=0.4, flecks=0.4,
                        per_plank=5, gap=M.lift(base, -40))
    for x0 in (0, 12, 21):  # battens over the gaps
        for y in range(S):
            M.touch(img, (x0 - 1) % S, y, 0.16)
            M.touch(img, x0, y, 0.1)
            M.touch(img, (x0 + 2) % S, y, -0.18)
    if wear:
        M.grime(img, 0.18, seed=M.sub(seed, "wear"), color=(118, 104, 86), cover=0.35)
    return img


def exteriors_b11():
    """The Suburbs' siding (every colour, three alternates each), roofing, eaves, and the barns' boards and tin."""
    for name, c in SIDING.items():
        for k, wear in enumerate((0, 0, 0)):
            save(lap_siding(c, seed_of(f"siding-{name}-{k}"), wear), f"siding-{name}" + ("" if k == 0 else f"-{k + 1}"))
    for name, c in ROOFING.items():
        for k in range(3):
            save(shingle_courses(c, seed_of(f"roof-{name}-{k}")), f"houseroof-{name}" + ("" if k == 0 else f"-{k + 1}"))
        save(roof_edge(c, seed_of(f"roofedge-{name}")), f"roofedge-{name}")
        save(ridge_cap(c, seed_of(f"roofcap-{name}")), f"roofcap-{name}")
    save(soffit(TRIM, seed_of("soffit")), "soffit")
    save(gutter(seed_of("gutter")), "gutter")
    tin = (128, 130, 128)
    for k, rust in enumerate((0, 0, 3)):
        save(corrugated(tin, seed_of(f"barnroof-{k}"), rust), "barnroof" + ("" if k == 0 else f"-{k + 1}"))
    save(roof_edge(tin, seed_of("barnroofedge")), "roofedge-barn")
    img = M.brushed_metal(seed=seed_of("barnroofcap"), base=(140, 142, 140), direction="h")
    save(img, "roofcap-barn")
    save(M.wood_planks(seed=seed_of("barndeck"), base=(96, 82, 66), planks=4, grain=4, contrast=0.8, per_plank=8), "barndeck")
    for name, c in (("red", (124, 44, 34)), ("grey", (134, 128, 118))):
        for k in range(3):
            save(barn_boards(c, seed_of(f"barnwall-{name}-{k}"), wear=k == 2), f"barnwall-{name}" + ("" if k == 0 else f"-{k + 1}"))


def generate():
    refinements()
    level6()
    level61()
    level7()
    level8()
    level9()
    level10()
    exteriors_b11()
