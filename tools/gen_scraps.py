"""Food Scraps item texture (backrooms:foodscraps): a crushed cracker packet, a half-eaten tin, crumbs.

Run from the repo root:  python tools/gen_scraps.py     (deterministic; fixed seeds)

One 16x16 atlas, in the palette of crackers.png and cannedbeans.png:
    x 0-7,  y 0-5    crumpled packet: wrapper red, creased, a torn window of cracker cream (y 6-7: its edge strip)
    x 8-15, y 0-7    tin side: grey steel, a worn orange label band, a dent
    x 8-15, y 8-15   tin inside: rim, scraped-out beans, and the bent lid's underside (y 13-15)
    x 0-7,  y 8-15   crumbs: cracker cream and brown flecks
"""
import os
import random

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "textures", "item", "foodscraps.png")

RED = (196, 52, 40)
RED_D = (170, 40, 32)
RED_DD = (140, 32, 28)
RED_L = (214, 78, 60)
CREAM = (232, 196, 120)
CREAM_D = (200, 160, 92)
CRUMB = (170, 130, 70)
STEEL = (176, 180, 186)
STEEL_D = (150, 154, 160)
STEEL_DD = (118, 122, 130)
STEEL_L = (204, 207, 212)
ORANGE = (214, 120, 40)
ORANGE_D = (176, 94, 34)
BEANS = (150, 70, 30)
BEANS_D = (112, 52, 26)
GRIME = (88, 70, 50)


def grub(px, rng, x0, y0, x1, y1, n):
    """Darkens n random pixels of a box a little: the grubby, handled look."""
    for _ in range(n):
        x, y = rng.randint(x0, x1), rng.randint(y0, y1)
        r, g, b, a = px[x, y]
        px[x, y] = (int(r * 0.84), int(g * 0.82), int(b * 0.8), a)


def build():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()

    def fill(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                px[x, y] = c + (255,)

    def dot(x, y, c):
        px[x, y] = c + (255,)

    # --- crumpled packet ---
    rng = random.Random(7101)
    fill(0, 0, 7, 5, RED)
    for x in range(8):  # creases run across, a little crooked
        y = 1 + (x // 3)
        dot(x, y, RED_DD)
        if x % 2 == 0:
            dot(x, y + 2, RED_L)
    for x in range(1, 5):
        dot(x, 4, RED_D)
    for (x, y) in ((4, 1), (5, 1), (6, 2), (5, 2)):  # the torn window, cracker showing through
        dot(x, y, CREAM)
    dot(6, 1, CREAM_D)
    dot(0, 0, RED_DD)
    dot(7, 5, RED_DD)
    grub(px, rng, 0, 0, 7, 5, 7)
    fill(0, 6, 7, 7, RED_D)
    for (x, y) in ((2, 7), (5, 6), (6, 7)):
        dot(x, y, RED_DD)

    # --- tin side ---
    rng = random.Random(7102)
    fill(8, 0, 15, 7, STEEL)
    fill(8, 2, 15, 5, ORANGE)
    fill(10, 3, 13, 4, ORANGE_D)
    fill(8, 0, 15, 0, STEEL_L)
    fill(8, 7, 15, 7, STEEL_D)
    dot(12, 1, STEEL_D)
    dot(13, 1, STEEL_D)
    dot(13, 2, ORANGE_D)
    dot(9, 6, STEEL_DD)
    grub(px, rng, 8, 0, 15, 7, 8)

    # --- tin inside: rim, scraped-out beans; lid underside at the bottom ---
    rng = random.Random(7103)
    fill(8, 8, 15, 15, STEEL_D)
    fill(9, 9, 14, 12, BEANS)
    for (x, y) in ((10, 10), (12, 11), (13, 9), (11, 12)):
        dot(x, y, BEANS_D)
    dot(9, 9, STEEL_DD)
    dot(14, 12, GRIME)
    fill(8, 13, 15, 15, STEEL)
    fill(8, 13, 15, 13, STEEL_DD)
    dot(11, 14, GRIME)
    grub(px, rng, 8, 8, 15, 15, 6)

    # --- crumbs: cracker cream with brown flecks ---
    rng = random.Random(7104)
    fill(0, 8, 7, 15, CREAM)
    for _ in range(16):
        dot(rng.randint(0, 7), rng.randint(8, 15), rng.choice((CREAM_D, CRUMB)))
    for (x, y) in ((1, 9), (5, 11), (3, 14)):
        dot(x, y, CRUMB)
    grub(px, rng, 0, 8, 7, 15, 5)
    return img


if __name__ == "__main__":
    # The item's look is a model now (gen_items_pantry.py writes textures/item/pantry/foodscraps.png); this flat atlas is no
    # longer used, so it is not written: pass --write to get the old sheet.
    import sys
    if "--write" in sys.argv:
        build().save(OUT)
        print("wrote", OUT)
    else:
        print("gen_scraps.py: superseded by gen_items_pantry.py; nothing written (--write for the old flat atlas)")
