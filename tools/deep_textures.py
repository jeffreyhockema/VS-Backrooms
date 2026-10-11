"""Textures for Levels 6 to 10 and Level 6.1 (32x32, in block/detail/ and item/)."""
import math
import random

from PIL import Image, ImageDraw

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

def level9():
    img = noise(0x2A2C2E, 6, "asphalt")
    specks(img, [0x3E4042, 0x1E2022, 0x4A4A48], 90, "asphalt")
    save(img, "asphalt")
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
    img = noise(0x9A9890, 5, "sidewalk")
    d = ImageDraw.Draw(img)
    d.line([0, 0, S - 1, 0], fill=rgb(0x6E6C66))
    d.line([0, 0, 0, S - 1], fill=rgb(0x6E6C66))
    d.line([0, 16, S - 1, 16], fill=rgb(0x7E7C76))
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
    for name, c in (("white", 0xE4E2DA), ("blue", 0x7A98B8), ("yellow", 0xE0CC88), ("green", 0x8AA88A)):
        img = noise(c, 3, "siding" + name)
        d = ImageDraw.Draw(img)
        for y in range(0, S, 5):
            d.line([0, y, S - 1, y], fill=T.shade(T.hexrgb(c), 0.72))
            d.line([0, y + 1, S - 1, y + 1], fill=T.shade(T.hexrgb(c), 1.08))
        save(img, f"siding-{name}")
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
    for name, c in (("grey", 0x55575C), ("brown", 0x5E4430), ("red", 0x7A3328)):
        save(shingles(c, "roof" + name), f"houseroof-{name}")
    img = noise(0xF0EEE8, 6, "popcorn")
    save(img, "houseceiling")
    for part in ("lower", "upper"):
        img = noise(0x7A2A20, 3, "housedoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xE8E4DA), width=2)
        d.rectangle([6, 4, 14, 26 if part == "lower" else 28], outline=rgb(0x5A1E16))
        d.rectangle([18, 4, 26, 26 if part == "lower" else 28], outline=rgb(0x5A1E16))
        if part == "lower":
            d.ellipse([22, 1, 25, 4], fill=rgb(0xD8B050))
        else:
            d.rectangle([10, 6, 22, 14], fill=rgb(0x1A2028))
            text(img, "4312"[random.Random(5).randint(0, 3):], (8, 18, 24, 26), 0xD8B050, 5)
        save(img, f"housedoor-{part}")
        img = noise(0xE4E2DA, 3, "garage" + part)
        d = ImageDraw.Draw(img)
        for y in range(0, S, 8):
            d.line([0, y, S - 1, y], fill=rgb(0xA8A6A0))
            d.rectangle([3, y + 2, S - 4, y + 6], outline=rgb(0xC8C6C0))
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
    flat("mailbox", 0x2A3A5A, 4)
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
    for name, c in (("red", 0x8A2A1E), ("grey", 0x8A8478)):
        img = noise(c, 6, "barn" + name)
        d = ImageDraw.Draw(img)
        for x in range(0, S, 6):
            d.line([x, 0, x, S - 1], fill=T.shade(T.hexrgb(c), 0.7))
        save(img, f"barnwall-{name}")
    img = noise(0x3A3C3E, 5, "barnroof")
    for y in range(0, S, 4):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x2A2C2E))
    save(img, "barnroof")
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

def shingles(color, key):
    """Asphalt shingles: courses of tabs, each a little different in shade, the slots between them and the shadow
    under each course, over a gritty surface."""
    rng = random.Random(seed_of(key))
    base = T.hexrgb(color)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        course = y // 8
        offset = 5 if course % 2 else 0
        for x in range(S):
            tab = (x + offset) // 10
            tab_shade = 0.86 + 0.28 * random.Random(seed_of(f"{key}-{course}-{tab}")).random()
            yy = y % 8
            f = tab_shade * (0.72 if yy == 7 else 0.86 if yy == 6 else 1.0)  # the shadow at the foot of each course
            if (x + offset) % 10 == 0 and yy < 6:
                f *= 0.6  # the slot between two tabs
            grit = 0.9 + 0.2 * rng.random()
            px[x, y] = tuple(max(0, min(255, int(c * f * grit))) for c in base) + (255,)
    return img


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
    asphalt = noise(0x2A2C2E, 6, "asphalt")
    specks(asphalt, [0x3E4042, 0x1E2022, 0x4A4A48], 90, "asphalt")
    line = asphalt.copy()
    ImageDraw.Draw(line).rectangle([0, 13, S - 1, 18], fill=rgb(0xD8B830))
    save(line, "asphalt-line")
    save(line.rotate(90), "asphalt-linens")
    zebra = asphalt.copy()
    ImageDraw.Draw(zebra).rectangle([0, 2, S - 1, 15], fill=rgb(0xD8D8D2))
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
    flat("tractorgreen", 0x2E6A2A, 5)
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
    img = noise(0xB0A8A0, 5, "silo")
    for x in range(0, S, 3):
        ImageDraw.Draw(img).line([x, 0, x, S - 1], fill=rgb(0x8A847C))
    save(img, "silo")
    flat("silotop", 0x6A6E72, 4)
    img = noise(0xA88A52, 8, "stubble")
    d = ImageDraw.Draw(img)
    rng = random.Random(207)
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S - 2)
        d.line([x, y, x, y + 2], fill=rgb(rng.choice([0xD8C070, 0xC8B060, 0xE8D890])))
    save(img, "stubble")


def generate():
    refinements()
    level6()
    level61()
    level7()
    level8()
    level9()
    level10()
