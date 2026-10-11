"""Level 3999, the Neon Paradise: the arcade machines' art (block/3999/). Called from gen_3999.py.

Six invented games (GALAXIA 3999, NEON RALLY, DUNGEON BYTE, ROBO BRAWL, SKY JOUSTER, MAZE MUNCHER), each with its own
marquee logo (48 x 16), attract-mode screen (40 x 32, pixel art at its own size), side art (24 x 56, the side panel's
proportions), body paint and control panel; the twelve themed cabinets whose screens show other levels; the rusted
and the dead cabinets; and the art of the racer, the dance machine, the pinball table, the claw machine, skee-ball
and air hockey. All titles and pictures are original.
"""
import math
import random

from PIL import Image, ImageDraw

from gen_3999_kit import F3, F5, NEON, text_width, draw_text
from gen_3999_tex import clamp, fit_atlas_grid, mix, noisy, rgba, save, seed_of, shade, neon_core

C = {k: v[0] for k, v in NEON.items()}
WHITE = (250, 250, 255, 255)

GAMES = {
    # key: (title words [(text, font)], body colour, colour 1, colour 2)
    "a": ([("GALAXIA", F5), ("3999", F3)], (14, 10, 40), C["magenta"], C["cyan"]),
    "b": ([("NEON", F3), ("RALLY", F5)], (16, 12, 14), C["orange"], C["pink"]),
    "c": ([("DUNGEON", F5), ("BYTE", F3)], (34, 22, 18), C["lilac"], C["orange"]),
    "d": ([("ROBO", F3), ("BRAWL", F5)], (16, 24, 64), C["blue"], C["orange"]),
    "e": ([("SKY", F3), ("JOUSTER", F5)], (8, 36, 44), C["cyan"], C["orange"]),
    "f": ([("MAZE", F3), ("MUNCHER", F5)], (52, 8, 34), C["pink"], C["blue"]),
}

THEMED = {
    # key: (marquee words, colour 1, colour 2, side label)
    "l4": ([("CUBICLE", F5), ("CHAOS", F3)], (200, 200, 190), (90, 140, 230), "4"),
    "l5": ([("CHECK", F5), ("OUT", F3)], (220, 60, 50), (230, 190, 90), "5"),
    "l6": ([("LIGHTS", F5), ("OUT", F3)], (240, 240, 240), (120, 120, 130), "6"),
    "l7": ([("DEEP", F5), ("BLUE", F3)], (60, 140, 230), (160, 220, 250), "7"),
    "l9": ([("CUL-DE-SAC", F3), ("", F3)], (240, 200, 120), (120, 160, 230), "9"),
    "l10": ([("HARVEST", F5), ("", F3)], (230, 200, 90), (150, 150, 150), "10"),
    "l11": ([("METROPOLIS", F3), ("", F3)], (100, 232, 247), (255, 74, 0), "11"),
    "l37": ([("POOL", F5), ("PARTY", F3)], (90, 220, 220), (250, 250, 250), "37"),
    "l94": ([("CLAY", F5), ("MATION", F3)], (120, 200, 90), (250, 220, 120), "94"),
    "run": ([("RUN!", F5), ("", F3)], (255, 40, 40), (250, 250, 250), "!"),
    "fun": ([("=)", F5), ("", F3)], (250, 220, 40), (255, 42, 90), "=)"),
    "kitty": ([("KITTY", F5), ("", F3)], (255, 160, 200), (250, 250, 250), "974"),
}


def marquee(name, words, c1, c2, bg=(10, 6, 18), faded=0.0):
    img = Image.new("RGBA", (48, 16), rgba(bg))
    d = ImageDraw.Draw(img)
    for y in range(16):  # a glowing band behind the logo
        t = 1 - abs(y - 7.5) / 8
        d.line([0, y, 47, y], fill=rgba(mix(bg, shade(c1, 0.5), t * 0.5)))
    d.rectangle([0, 0, 47, 15], outline=rgba(shade(c2, 0.8)))
    words = [(w, f) for w, f in words if w]
    heights = [len(f["A"]) for _, f in words]
    total = sum(heights) + (len(words) - 1)
    y = (16 - total) // 2
    for (w, f), h, col in zip(words, heights, (c1, c2)):
        tw = text_width(w, f)
        x = (48 - tw) // 2
        draw_text(img, w, x + 1, y + 1, rgba(shade(col, 0.3)), f)
        draw_text(img, w, x, y, rgba(mix(col, (255, 255, 255), 0.25)), f)
        y += h + 1
    if faded:
        rng = random.Random(seed_of(name))
        px = img.load()
        for yy in range(16):
            for xx in range(48):
                r, g, b, a = px[xx, yy]
                k = faded * (0.6 + 0.4 * rng.random())
                px[xx, yy] = (clamp(r * (1 - k) + 90 * k), clamp(g * (1 - k) + 60 * k), clamp(b * (1 - k) + 40 * k), 255)
        for _ in range(4):  # peeling
            x0, y0 = rng.randrange(48), rng.randrange(16)
            d.rectangle([x0, y0, x0 + rng.randrange(3, 9), y0 + rng.randrange(2, 5)], fill=(150, 140, 120, 255))
    save(img, name)


def screen_canvas(bg):
    img = Image.new("RGBA", (40, 32), rgba(bg))
    return img, ImageDraw.Draw(img)


def scanlines(img, k=0.82):
    px = img.load()
    for y in range(1, img.size[1], 2):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k), a)
    return img


def score(d, img, text, col, x=1, y=1):
    draw_text(img, text, x, y, rgba(col), F3)


# ---------------- The six games' screens ----------------

def screen_a():
    img, d = screen_canvas((2, 2, 12))
    rng = random.Random(1)
    for _ in range(30):
        img.putpixel((rng.randrange(40), rng.randrange(32)), (200, 200, 255, 255))
    for row, col in enumerate((C["magenta"], C["cyan"], C["pink"])):  # an invader fleet (original shapes: crab-diamonds)
        for i in range(6):
            x, y = 4 + i * 6, 7 + row * 5
            d.polygon([(x, y + 1), (x + 2, y - 1), (x + 4, y + 1), (x + 2, y + 3)], fill=rgba(col))
            img.putpixel((x, y + 3), rgba(col))
            img.putpixel((x + 4, y + 3), rgba(col))
    d.polygon([(18, 29), (20, 24), (22, 29)], fill=WHITE)      # the ship
    d.rectangle([17, 28, 23, 29], fill=rgba(C["cyan"]))
    d.line([20, 18, 20, 22], fill=(255, 240, 120, 255))
    score(d, img, "03999", C["magenta"])
    score(d, img, "1UP", C["cyan"], 27)
    return scanlines(img)


def screen_b():
    img, d = screen_canvas((20, 8, 40))
    for y in range(13):  # dusk sky
        d.line([0, y, 39, y], fill=rgba(mix((60, 10, 70), (255, 80, 40), y / 13)))
    d.ellipse([14, 6, 26, 18], fill=rgba(C["orange"]))
    d.rectangle([0, 12, 39, 13], fill=(30, 10, 40, 255))
    for y in range(13, 32):  # road in perspective, neon kerbs
        t = (y - 13) / 19
        half = 2 + t * 22
        d.line([20 - half - 3, y, 20 + half + 3, y], fill=(30, 20, 50, 255))
        d.line([20 - half, y, 20 + half, y], fill=(50, 40, 70, 255))
        kerb = C["pink"] if (y // 2) % 2 else WHITE[:3]
        img.putpixel((max(0, int(20 - half)), y), rgba(kerb))
        img.putpixel((min(39, int(20 + half)), y), rgba(kerb))
        if (y // 3) % 2 == 0:
            img.putpixel((20, y), (255, 240, 120, 255))
    d.rectangle([15, 24, 25, 29], fill=rgba(C["orange"]))      # the car from behind
    d.rectangle([16, 22, 24, 24], fill=(40, 40, 60, 255))
    d.rectangle([15, 28, 17, 29], fill=(255, 30, 30, 255))
    d.rectangle([23, 28, 25, 29], fill=(255, 30, 30, 255))
    score(d, img, "LAP 3", WHITE[:3])
    return scanlines(img)


def screen_c():
    img, d = screen_canvas((10, 8, 8))
    for gy in range(6):
        for gx in range(8):
            x, y = gx * 5, 7 + gy * 4
            wall = (gx in (0, 7) or gy in (0, 5) or (gx == 3 and gy < 4) or (gy == 2 and gx > 4))
            d.rectangle([x, y, x + 4, y + 3], fill=(90, 70, 110, 255) if wall else (30, 24, 26, 255))
            if wall:
                d.line([x, y + 3, x + 4, y + 3], fill=(50, 40, 60, 255))
    d.rectangle([9, 18, 11, 21], fill=rgba(C["cyan"]))          # the hero
    img.putpixel((12, 18), (230, 230, 230, 255))
    d.rectangle([26, 12, 28, 14], fill=(220, 50, 50, 255))      # monsters
    d.rectangle([22, 22, 24, 24], fill=(220, 50, 50, 255))
    d.rectangle([30, 22, 31, 23], fill=rgba(C["orange"]))       # a chest
    score(d, img, "LV 2", C["lilac"])
    score(d, img, "HP", C["orange"], 24)
    d.rectangle([32, 2, 38, 4], fill=(220, 40, 40, 255))
    return scanlines(img)


def screen_d():
    img, d = screen_canvas((16, 16, 40))
    d.rectangle([0, 24, 39, 31], fill=(60, 50, 70, 255))
    for x in range(0, 40, 4):
        d.line([x, 24, x + 2, 31], fill=(80, 70, 90, 255))

    def robot(x, col, face_right):
        d.rectangle([x, 12, x + 6, 20], fill=rgba(col))         # body
        d.rectangle([x + 1, 8, x + 5, 12], fill=rgba(shade(col, 1.2)))  # head
        img.putpixel((x + (4 if face_right else 2), 10), (255, 255, 120, 255))
        d.rectangle([x + 1, 20, x + 2, 24], fill=rgba(shade(col, 0.7)))
        d.rectangle([x + 4, 20, x + 5, 24], fill=rgba(shade(col, 0.7)))
        ax = x + 7 if face_right else x - 4
        d.rectangle([ax, 13, ax + 3, 15], fill=rgba(shade(col, 1.1)))
    robot(8, C["blue"], True)
    robot(25, C["orange"], False)
    d.rectangle([1, 2, 16, 4], fill=(40, 200, 80, 255))
    d.rectangle([23, 2, 38, 4], fill=(40, 200, 80, 255))
    d.rectangle([30, 2, 38, 4], fill=(200, 40, 40, 255))
    draw_text(img, "VS", 17, 1, WHITE, F3)
    return scanlines(img)


def screen_e():
    img, d = screen_canvas((6, 10, 30))
    for y0 in (26, 18, 10):
        pass
    d.rectangle([0, 29, 39, 31], fill=(120, 60, 30, 255))
    d.rectangle([2, 20, 13, 21], fill=(140, 90, 50, 255))
    d.rectangle([24, 13, 37, 14], fill=(140, 90, 50, 255))
    d.rectangle([12, 25, 27, 26], fill=(140, 90, 50, 255))
    for (x, y, col) in ((6, 16, C["cyan"]), (29, 9, C["orange"]), (19, 6, C["pink"])):  # riders on birds
        d.polygon([(x, y + 2), (x + 5, y + 1), (x + 6, y + 3), (x + 1, y + 4)], fill=rgba(col))
        d.line([(x + 1, y + 1), (x - 1, y - 1)], fill=rgba(col))
        d.line([(x + 4, y + 1), (x + 6, y - 2)], fill=rgba(col))
        d.rectangle([x + 2, y - 1, x + 3, y], fill=WHITE)
        d.line([(x + 3, y - 1), (x + 6, y - 3)], fill=(230, 230, 230, 255))
    d.rectangle([0, 30, 39, 31], fill=(220, 60, 20, 255))       # lava
    score(d, img, "2450", C["cyan"])
    return scanlines(img)


def screen_f():
    img, d = screen_canvas((0, 0, 8))
    walls = ["1111111111", "1000010001", "1011010101", "1000000101", "1101101101", "1000000001", "1111111111"]
    for gy, row in enumerate(walls):
        for gx, ch in enumerate(row):
            x, y = gx * 4, 5 + gy * 4
            if ch == "1":
                d.rectangle([x, y, x + 3, y + 3], outline=rgba(C["blue"]))
            else:
                img.putpixel((x + 1, y + 1), (250, 220, 200, 255))
    d.rectangle([5, 25, 7, 27], fill=(80, 230, 90, 255))       # the muncher: a green cube with eyes
    img.putpixel((6, 25), (0, 0, 0, 255))
    for (x, y) in ((21, 13), (29, 21)):                         # spiky chasers
        d.polygon([(x, y), (x + 1, y - 2), (x + 2, y), (x + 3, y - 2), (x + 4, y), (x + 4, y + 3), (x, y + 3)], fill=rgba(C["pink"]))
    score(d, img, "0880", C["pink"])
    return scanlines(img)


# ---------------- The themed screens: the level on the marquee ----------------

def themed_screen(key):
    img, d = screen_canvas((0, 0, 0))
    rng = random.Random(seed_of(key))
    if key == "l4":
        d.rectangle([0, 0, 39, 31], fill=(170, 170, 160, 255))
        for gx in range(4):
            for gy in range(3):
                x, y = 2 + gx * 10, 3 + gy * 10
                d.rectangle([x, y, x + 8, y + 8], outline=(110, 110, 110, 255))
                d.rectangle([x + 2, y + 2, x + 6, y + 5], fill=(30, 40, 60, 255))
                img.putpixel((x + 3, y + 3), (120, 200, 255, 255))
    elif key == "l5":
        d.rectangle([0, 0, 39, 31], fill=(110, 20, 20, 255))
        d.polygon([(0, 31), (14, 12), (26, 12), (39, 31)], fill=(150, 30, 30, 255))
        for x in (16, 20, 24):
            d.rectangle([x - 1, 12, x, 16], fill=(230, 200, 120, 255))
        for k in range(4):
            y = 14 + k * 4
            d.rectangle([3 + k * 2, y, 5 + k * 2, y + 3], fill=(80, 50, 30, 255))
            d.rectangle([34 - k * 2, y, 36 - k * 2, y + 3], fill=(80, 50, 30, 255))
    elif key == "l6":
        d.rectangle([14, 12, 16, 14], fill=WHITE)
        d.rectangle([23, 12, 25, 14], fill=WHITE)
    elif key == "l7":
        d.rectangle([0, 0, 39, 9], fill=(110, 110, 112, 255))
        for x in range(0, 40, 8):
            d.rectangle([x, 9, x + 2, 13], fill=(90, 90, 92, 255))
        for y in range(10, 32):
            d.line([0, y, 39, y], fill=rgba(mix((30, 90, 170), (4, 10, 40), (y - 10) / 22)))
        for _ in range(12):
            x = rng.randrange(40)
            d.line([x, 12, x + 3, 12], fill=(120, 180, 230, 255))
    elif key == "l9":
        d.rectangle([0, 0, 39, 31], fill=(10, 12, 30, 255))
        d.ellipse([30, 2, 35, 7], fill=(240, 240, 220, 255))
        for i, x in enumerate((1, 14, 27)):
            d.rectangle([x, 16, x + 11, 27], fill=(70, 60, 80, 255))
            d.polygon([(x - 1, 16), (x + 5, 10), (x + 12, 16)], fill=(50, 40, 60, 255))
            d.rectangle([x + 2, 19, x + 4, 21], fill=(255, 210, 120, 255))
            d.rectangle([x + 7, 22, x + 9, 27], fill=(40, 30, 30, 255))
        d.rectangle([0, 28, 39, 31], fill=(40, 40, 46, 255))
    elif key == "l10":
        for y in range(14):
            d.line([0, y, 39, y], fill=rgba(mix((120, 120, 126), (170, 170, 170), y / 14)))
        for y in range(14, 32):
            d.line([0, y, 39, y], fill=(200, 170, 70, 255))
        for _ in range(120):
            x, y = rng.randrange(40), rng.randrange(14, 32)
            img.putpixel((x, y), (230, 200, 100, 255) if rng.random() < 0.6 else (160, 130, 50, 255))
        d.rectangle([28, 6, 30, 14], fill=(240, 240, 236, 255))   # a windmill far off, a red light
        d.line([(29, 6), (24, 1)], fill=(200, 200, 200, 255))
        d.line([(29, 6), (34, 1)], fill=(200, 200, 200, 255))
        img.putpixel((29, 5), (255, 40, 40, 255))
    elif key == "l11":
        for y in range(32):
            d.line([0, y, 39, y], fill=rgba(mix((10, 10, 40), (60, 30, 80), y / 32)))
        x = 0
        while x < 40:
            w, h = rng.randrange(3, 7), rng.randrange(8, 26)
            d.rectangle([x, 31 - h, x + w - 1, 31], fill=(20, 20, 30, 255))
            for wy in range(32 - h, 30, 2):
                for wx in range(x + 1, x + w - 1, 2):
                    if rng.random() < 0.5:
                        img.putpixel((wx, wy), (255, 220, 120, 255))
            x += w + 1
    elif key == "l37":
        d.rectangle([0, 0, 39, 31], fill=(236, 240, 240, 255))
        for x in range(0, 40, 4):
            d.line([x, 0, x, 31], fill=(210, 216, 216, 255))
        for y in range(0, 32, 4):
            d.line([0, y, 39, y], fill=(210, 216, 216, 255))
        d.rectangle([4, 14, 35, 31], fill=(60, 190, 190, 255))
        for _ in range(10):
            x, y = rng.randrange(5, 34), rng.randrange(15, 31)
            d.line([x, y, x + 2, y], fill=(150, 240, 240, 255))
    elif key == "l94":
        d.rectangle([0, 0, 39, 31], fill=(150, 200, 240, 255))
        d.ellipse([-10, 14, 22, 44], fill=(110, 190, 80, 255))
        d.ellipse([14, 18, 52, 50], fill=(90, 170, 70, 255))
        d.rectangle([22, 13, 32, 21], fill=(250, 236, 200, 255))
        d.polygon([(20, 13), (27, 7), (34, 13)], fill=(200, 80, 70, 255))
        d.rectangle([26, 17, 28, 21], fill=(120, 80, 50, 255))
        d.ellipse([4, 3, 12, 8], fill=(255, 255, 255, 255))
    elif key == "run":
        d.rectangle([0, 0, 39, 31], fill=(60, 4, 4, 255))
        d.polygon([(0, 0), (16, 12), (16, 22), (0, 31)], fill=(110, 10, 10, 255))
        d.polygon([(39, 0), (24, 12), (24, 22), (39, 31)], fill=(110, 10, 10, 255))
        d.rectangle([16, 12, 24, 22], fill=(20, 0, 0, 255))
        draw_text(img, "!", 19, 13, (255, 255, 255, 255), F5)
    elif key == "fun":
        d.rectangle([0, 0, 39, 31], fill=(255, 230, 120, 255))
        for (x, y, col) in ((5, 6, (230, 40, 50)), (31, 8, (60, 120, 230)), (9, 20, (60, 200, 90)), (30, 22, (230, 80, 200))):
            d.ellipse([x - 3, y - 4, x + 3, y + 3], fill=rgba(col))
            d.line([x, y + 3, x, y + 8], fill=(80, 80, 80, 255))
        d.ellipse([12, 8, 28, 24], fill=(250, 210, 30, 255), outline=(40, 30, 0, 255))
        d.line([16, 13, 19, 13], fill=(0, 0, 0, 255))
        d.line([16, 15, 19, 15], fill=(0, 0, 0, 255))
        d.arc([15, 12, 25, 22], 300, 60, fill=(0, 0, 0, 255))
    elif key == "kitty":
        d.rectangle([0, 0, 39, 31], fill=(255, 220, 230, 255))
        # a crayon cat: wobbly outline, round head, triangle ears
        d.ellipse([12, 8, 28, 22], outline=(40, 40, 40, 255))
        d.polygon([(13, 11), (14, 4), (19, 9)], outline=(40, 40, 40, 255))
        d.polygon([(27, 11), (26, 4), (21, 9)], outline=(40, 40, 40, 255))
        img.putpixel((17, 14), (0, 0, 0, 255))
        img.putpixel((23, 14), (0, 0, 0, 255))
        d.line([(19, 17), (21, 17)], fill=(240, 80, 120, 255))
        d.line([(16, 22), (14, 30)], fill=(40, 40, 40, 255))
        d.line([(24, 22), (26, 30)], fill=(40, 40, 40, 255))
        for k in range(5):
            d.point((4 + k * 8, 28), fill=(240, 120, 160, 255))
    return scanlines(img, 0.9)


def side_art(name, body, c1, c2, kind):
    """The side panel: body paint, and a big graphic in the game's two colours."""
    img = noisy(body, 3, name, 24, 56)
    d = ImageDraw.Draw(img)
    if kind == "a":
        rng = random.Random(1)
        for _ in range(40):
            img.putpixel((rng.randrange(24), rng.randrange(56)), (220, 220, 255, 255))
        d.ellipse([2, 6, 22, 26], fill=rgba(shade(c1, 0.8)))
        d.ellipse([-6, 13, 30, 19], outline=rgba(c2), width=1)
        d.polygon([(12, 32), (18, 46), (12, 42), (6, 46)], fill=rgba(c2))
    elif kind == "b":
        for y in range(0, 56, 4):
            for x in range(0, 24, 4):
                if (x // 4 + y // 4) % 2 == 0 and y < 12:
                    d.rectangle([x, y, x + 3, y + 3], fill=WHITE)
        d.polygon([(0, 56), (0, 40), (24, 20), (24, 30)], fill=rgba(c1))
        d.polygon([(0, 56), (0, 50), (24, 34), (24, 38)], fill=rgba(c2))
    elif kind == "c":
        for y in range(0, 56, 5):
            off = 3 if (y // 5) % 2 else 0
            for x in range(-3, 24, 6):
                d.rectangle([x + off, y, x + off + 4, y + 3], outline=rgba(shade(body, 1.8)))
        d.rectangle([11, 10, 13, 40], fill=(210, 210, 220, 255))   # a sword
        d.rectangle([6, 38, 18, 40], fill=rgba(c2))
        d.rectangle([11, 40, 13, 47], fill=rgba(c1))
        d.ellipse([3, 48, 21, 56], fill=rgba(shade(c2, 0.7)))
    elif kind == "d":
        d.rectangle([4, 14, 20, 34], fill=rgba(c1))               # a robot fist
        for y in (18, 23, 28):
            d.line([4, y, 20, y], fill=rgba(shade(c1, 0.6)))
        d.rectangle([8, 34, 16, 50], fill=rgba(shade(c1, 0.8)))
        for k in range(4):
            d.line([(12, 12), (12 + 10 * math.cos(k + 0.5), 12 - 10 * math.sin(k + 0.5))], fill=rgba(c2), width=2)
    elif kind == "e":
        d.polygon([(2, 30), (22, 18), (14, 34)], fill=rgba(c1))   # a wing
        d.polygon([(4, 34), (22, 28), (12, 40)], fill=rgba(shade(c1, 0.8)))
        d.polygon([(10, 12), (14, 4), (16, 14)], fill=rgba(c2))   # a lance
        d.line([(14, 4), (6, 50)], fill=rgba(c2), width=2)
    elif kind == "f":
        for y in range(4, 56, 8):
            d.line([2, y, 22, y], fill=rgba(c2))
            x = 4 + (y * 7) % 14
            d.line([x, y, x, y + 8], fill=rgba(c2))
        d.rectangle([7, 22, 16, 31], fill=(80, 230, 90, 255))
        d.rectangle([9, 24, 10, 25], fill=(0, 0, 0, 255))
        d.rectangle([13, 24, 14, 25], fill=(0, 0, 0, 255))
    save(img, name)


def themed_side(key, c1, c2, label):
    img = noisy((16, 14, 22), 3, f"cab-{key}-side", 24, 56)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 21, 53], outline=rgba(shade(c1, 0.7)))
    draw_text(img, "LEVEL", 2 + (20 - text_width("LEVEL", F3)) // 2, 6, rgba(c2), F3)
    f, sc = (F5, 2) if len(label) <= 2 else (F3, 2)
    w = text_width(label, f, sc)
    draw_text(img, label, (24 - w) // 2, 16, rgba(c1), f, sc)
    for y in range(36, 52, 3):
        d.line([4, y, 19, y], fill=rgba(shade(c1, 0.5)))
    save(img, f"cab-{key}-side")


def panel(name, body, c1, c2):
    img = noisy(shade(body, 1.4), 3, name, 32, 16)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 15], outline=rgba(c1))
    d.ellipse([4, 4, 11, 11], outline=rgba(c2))
    for k in range(4):
        x = 16 + (k % 2) * 6 + (k // 2) * 2
        y = 4 + (k // 2) * 5
        d.ellipse([x, y, x + 3, y + 3], outline=rgba(c1))
    draw_text(img, "1P", 26, 10, rgba(c2), F3)
    save(img, name)


def misc():
    # The coin door: two slots, lit, ONE CREDIT
    img = noisy((60, 60, 66), 3, "coindoor")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 31], outline=(110, 110, 118, 255))
    for x in (6, 20):
        d.rectangle([x, 6, x + 6, 14], fill=(200, 30, 30, 255))
        d.rectangle([x + 2, 8, x + 4, 12], fill=(20, 10, 10, 255))
    draw_text(img, "1 CREDIT", 1, 20, (230, 200, 120, 255), F3)
    save(img, "coindoor")
    save(noisy((210, 30, 30), 6, "joyball"), "joyball")
    save(noisy((20, 20, 22), 3, "stick"), "stick")
    save(noisy((10, 10, 12), 2, "screen-dark"), "screen-dark")
    # Rusted cabinet: corroded paint, a dark screen with dead pixels, the marquee peeling
    img = noisy((110, 56, 30), 14, "cab-rust-side", 24, 56)
    rng = random.Random(4)
    px = img.load()
    for _ in range(140):
        x, y = rng.randrange(24), rng.randrange(56)
        px[x, y] = rng.choice([(150, 80, 40, 255), (70, 36, 20, 255), (60, 50, 70, 255)])
    save(img, "cab-rust-side")
    save(noisy((100, 52, 28), 12, "cab-rust-body"), "cab-rust-body")
    img = noisy((8, 8, 10), 2, "screen-rust", 40, 32)
    for _ in range(9):
        img.putpixel((rng.randrange(40), rng.randrange(32)), rng.choice([(255, 0, 0, 255), (0, 255, 0, 255), (60, 60, 255, 255)]))
    save(img, "screen-rust")
    marquee("cab-rust-marquee", [("GALAXIA", F5), ("3999", F3)], C["magenta"], C["cyan"], faded=0.8)
    # The dead cabinets of 3999.1: dusty, the screen cracked, no light
    img = noisy((24, 20, 30), 4, "cab-dead-side", 24, 56)
    d = ImageDraw.Draw(img)
    d.ellipse([2, 6, 22, 26], fill=(60, 30, 70, 255))
    rng = random.Random(9)
    px = img.load()
    for _ in range(200):
        x, y = rng.randrange(24), rng.randrange(56)
        r, g, b, a = px[x, y]
        px[x, y] = (clamp(r + 40), clamp(g + 38), clamp(b + 34), 255)
    save(img, "cab-dead-side")
    save(noisy((26, 24, 30), 5, "cab-dead-body"), "cab-dead-body")
    img = noisy((6, 6, 8), 2, "screen-cracked", 40, 32)
    d = ImageDraw.Draw(img)
    for pts in (((22, 12), (4, 2)), ((22, 12), (39, 4)), ((22, 12), (12, 31)), ((22, 12), (39, 26)), ((22, 12), (0, 20)), ((22, 12), (30, 31))):
        d.line(pts, fill=(150, 150, 160, 255))
    d.ellipse([20, 10, 24, 14], outline=(200, 200, 210, 255))
    save(img, "screen-cracked")
    marquee("cab-dead-marquee", [("ROBO", F3), ("BRAWL", F5)], (70, 60, 80), (60, 50, 60), bg=(12, 10, 14))
    save(noisy((26, 24, 30), 4, "cpanel-dead", 32, 16), "cpanel-dead")


def racer():
    img = Image.new("RGBA", (48, 32), (20, 8, 40, 255))
    d = ImageDraw.Draw(img)
    for y in range(12):
        d.line([0, y, 47, y], fill=rgba(mix((50, 10, 80), (255, 90, 40), y / 12)))
    d.polygon([(0, 12), (8, 6), (16, 12)], fill=(40, 10, 60, 255))
    d.polygon([(30, 12), (40, 4), (48, 12)], fill=(40, 10, 60, 255))
    for y in range(12, 32):
        t = (y - 12) / 20
        half = 3 + t * 26
        d.line([24 - half - 4, y, 24 + half + 4, y], fill=(20, 60, 30, 255))
        d.line([24 - half, y, 24 + half, y], fill=(50, 46, 70, 255))
        if (y // 2) % 2:
            img.putpixel((24, y), (255, 240, 120, 255))
        img.putpixel((max(0, int(24 - half)), y), rgba(C["pink"]))
        img.putpixel((min(47, int(24 + half)), y), rgba(C["cyan"]))
    d.rectangle([30, 15, 34, 18], fill=rgba(C["cyan"]))
    d.rectangle([18, 24, 30, 30], fill=rgba(C["orange"]))
    d.rectangle([19, 22, 29, 24], fill=(40, 40, 60, 255))
    draw_text(img, "1ST", 1, 1, WHITE, F3)
    draw_text(img, "0:42", 30, 1, rgba(C["cyan"]), F3)
    save(scanlines(img), "racer-screen")
    marquee("racer-marquee", [("NEON", F3), ("RALLY", F5)], C["orange"], C["pink"])
    save(noisy((255, 74, 0), 6, "racer-body"), "racer-body")


def dance():
    img = Image.new("RGBA", (32, 32), (20, 18, 26, 255))
    d = ImageDraw.Draw(img)
    for gx in range(3):
        for gy in range(3):
            d.rectangle([gx * 11, gy * 11, gx * 11 + 9, gy * 11 + 9], fill=(50, 50, 60, 255))
    arrows = {(1, 0): "up", (1, 2): "down", (0, 1): "left", (2, 1): "right"}
    for (gx, gy), a in arrows.items():
        x, y = gx * 11 + 5, gy * 11 + 5
        col = C["pink"] if a in ("up", "down") else C["cyan"]
        pts = {"up": [(x, y - 4), (x + 4, y + 1), (x + 2, y + 1), (x + 2, y + 4), (x - 2, y + 4), (x - 2, y + 1), (x - 4, y + 1)]}
        if a == "up":
            p = pts["up"]
        elif a == "down":
            p = [(px_, 2 * y - py) for px_, py in pts["up"]]
        elif a == "left":
            p = [(x - (py - y), y + (px_ - x)) for px_, py in pts["up"]]
        else:
            p = [(x + (py - y), y + (px_ - x)) for px_, py in pts["up"]]
        d.polygon(p, fill=rgba(mix(col, (255, 255, 255), 0.3)))
    save(img, "arrowpad")
    img = Image.new("RGBA", (32, 40), (8, 4, 20, 255))
    d = ImageDraw.Draw(img)
    for k, col in enumerate((C["cyan"], C["pink"], C["pink"], C["cyan"])):
        x = 3 + k * 7
        d.rectangle([x, 2, x + 4, 5], outline=rgba(col))
        for j in range(3):
            y = 10 + j * 9 + k * 2
            d.rectangle([x, y, x + 4, y + 3], fill=rgba(col))
    draw_text(img, "GREAT", 7, 33, (255, 240, 120, 255), F3)
    save(scanlines(img), "dance-screen")
    marquee("dance-marquee", [("NEON", F5), ("STEP", F3)], C["pink"], C["cyan"])
    img = noisy((30, 30, 34), 3, "speaker")
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 27, 27], fill=(14, 14, 16, 255), outline=(80, 80, 90, 255))
    d.ellipse([12, 12, 19, 19], fill=(60, 60, 66, 255))
    save(img, "speaker")
    save(noisy((60, 20, 80), 4, "dance-body"), "dance-body")


def pinball():
    img = Image.new("RGBA", (32, 48), (20, 10, 40, 255))
    d = ImageDraw.Draw(img)
    for y in range(48):
        d.line([0, y, 31, y], fill=rgba(mix((40, 10, 70), (10, 20, 60), y / 48)))
    for (x, y, col) in ((10, 10, C["pink"]), (21, 10, C["cyan"]), (16, 17, C["orange"])):
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=rgba(col), outline=WHITE)
    d.line([(4, 30), (11, 40)], fill=WHITE, width=2)
    d.line([(27, 30), (20, 40)], fill=WHITE, width=2)
    d.line([(2, 2), (2, 34)], fill=rgba(C["lilac"]))
    d.line([(29, 2), (29, 34)], fill=rgba(C["lilac"]))
    d.ellipse([14, 26, 17, 29], fill=(220, 220, 230, 255))
    draw_text(img, "COMET", 6, 42, rgba(C["cyan"]), F3)
    save(img, "playfield")
    img = Image.new("RGBA", (32, 32), (10, 6, 24, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([18, 4, 28, 14], fill=rgba(C["orange"]))
    for k in range(5):
        d.line([(23 - k * 4, 9 + k * 2), (2, 20 + k)], fill=rgba(mix(C["orange"], C["pink"], k / 5)))
    draw_text(img, "COMET", 2, 2, rgba(C["cyan"]), F5)
    d.rectangle([2, 24, 29, 29], fill=(8, 8, 10, 255))
    draw_text(img, "120500", 3, 25, (255, 140, 40, 255), F3)
    save(img, "backbox")
    save(noisy((30, 20, 60), 4, "pinball-body"), "pinball-body")


def claw():
    marquee("claw-marquee", [("GRAB-A-PRIZE", F3), ("", F3)], C["lilac"], C["cyan"])
    save(noisy((200, 40, 120), 5, "claw-body"), "claw-body")
    img = noisy((20, 20, 24), 2, "chute")
    ImageDraw.Draw(img).rectangle([4, 4, 27, 27], outline=(150, 150, 160, 255))
    save(img, "chute")


def skeeball():
    img = Image.new("RGBA", (32, 44), (30, 20, 40, 255))
    d = ImageDraw.Draw(img)
    for r, col in ((15, (60, 30, 90)), (11, (90, 40, 130)), (7, (130, 60, 170)), (3, (20, 10, 20))):
        d.ellipse([16 - r, 22 - r, 16 + r, 22 + r], fill=rgba(col), outline=rgba(C["lilac"]))
    for (x, y) in ((4, 4), (27, 4)):
        d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(20, 10, 20, 255), outline=rgba(C["pink"]))
    draw_text(img, "100", 1, 9, rgba(C["pink"]), F3)
    draw_text(img, "100", 20, 9, rgba(C["pink"]), F3)
    draw_text(img, "50", 13, 9, WHITE, F3)
    draw_text(img, "10", 13, 38, WHITE, F3)
    save(fit_atlas_grid(img), "skee-target")
    img = Image.new("RGBA", (32, 8), (8, 4, 10, 255))
    draw_text(img, "0340", 8, 1, (255, 60, 60, 255), F3)
    save(img, "skee-score")
    save(noisy((150, 100, 60), 8, "skeeball-ball"), "skeeball-ball")
    save(noisy((60, 30, 90), 4, "skee-body"), "skee-body")


def airhockey():
    img = noisy((240, 244, 248), 2, "airtable")
    d = ImageDraw.Draw(img)
    for y in range(2, 32, 4):
        for x in range(2, 32, 4):
            d.point((x, y), fill=(170, 180, 190, 255))
    d.line([0, 31, 31, 31], fill=(255, 42, 90, 255))
    d.arc([8, 24, 24, 40], 180, 360, fill=(100, 160, 240, 255))
    save(img, "airtable")
    save(noisy((40, 80, 200), 5, "airrim"), "airrim")
    save(noisy((220, 30, 40), 5, "puck"), "puck")


def generate():
    for key, (words, body, c1, c2) in GAMES.items():
        marquee(f"cab-{key}-marquee", words, c1, c2)
        save({"a": screen_a, "b": screen_b, "c": screen_c, "d": screen_d, "e": screen_e, "f": screen_f}[key](), f"cab-{key}-screen")
        side_art(f"cab-{key}-side", body, c1, c2, key)
        save(noisy(body, 3, f"cab-{key}-body"), f"cab-{key}-body")
        panel(f"cpanel-{key}", body, c1, c2)
    for key, (words, c1, c2, label) in THEMED.items():
        marquee(f"cab-{key}-marquee", words, c1, c2)
        save(themed_screen(key), f"cab-{key}-screen")
        themed_side(key, c1, c2, label)
    save(noisy((16, 14, 22), 3, "cab-themed-body"), "cab-themed-body")
    panel("cpanel-themed", (16, 14, 22), (200, 200, 210), (255, 160, 255))
    misc()
    racer()
    dance()
    pinball()
    claw()
    skeeball()
    airhockey()
    print("3999 textures: arcade")


if __name__ == "__main__":
    generate()
