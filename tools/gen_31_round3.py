"""Level 31, "Roller Rink": round 3's signs, wall fittings and multi-block set pieces (beside gen_31.py, gen_31_props.py
and gen_31_walls.py; it writes only its own files).

    blocktypes/31/l31-plate.json   wall mounts: a thin sign or fitting against the wall behind its block (or hung from the
                                   ceiling in the middle of it), its face toward the side named (modelled facing north).
                                   A sign several blocks wide or high is one kind per block, "<sign><col><row>", col 0 the
                                   viewer's left, row 0 the top. The signs (SIGNS below) must match WorldLayout.L31Mounts.
    blocktypes/31/l31-stall.json   a toilet stall (partitions, its door ajar, the toilet inside), 28 units tall
    blocktypes/31/l31-vanity.json  a washroom vanity: a basin in a counter on a cabinet (the mirror is a plate over it)
    blocktypes/31/l31-photobooth.json  an arcade photo booth, 31 units tall (curtain, lit PHOTOS header, sample strips)
    blocktypes/31/l31-jukebox.json a 1990s jukebox, neon arch and record window, 22 units tall
    blocktypes/31/l31-trophycase.json  a trophy case, wood and glass, 30 units tall, cups on two shelves
    blocktypes/31/l31-mediacab.json    the cinema TV's low cabinet with a sound bar
    blocktypes/31/l31-riser.json   a cinema step: maroon carpet on top, a dark riser with amber aisle lights on its sides

Round 4 (tools/gen_31_round4.py, run after this one) rebuilds some of these blocks over this script's files; see its
docstring for which.

Every oriented block faces NORTH in its model, as the level's other props, with the variant group "side" last.
Run from the repo root:  bash tools/locked.sh run python tools/gen_31_round3.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

import matlib as M
from modelkit import DIRS, without
from texlib import S
from gen_31 import write_json, shape, save, SIDES, TEX, BLOCKS, SHAPES, STONE, WOOD, GLASS, CLOTH
from gen_31_props import B, prop_block, plastic, METAL

ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
P = 64  # px a block for the sign pictures
FONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")


def font(names, size):
    for n in names:
        for path in (os.path.join(FONTS, n), n):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default(size=size)


BOLD = ("arialbd.ttf", "DejaVuSans-Bold.ttf")
NARROW = ("ARIALNB.TTF", "arialbd.ttf")
IMPACT = ("impact.ttf", "arialbd.ttf")
SCRIPT = ("comicbd.ttf", "arialbd.ttf")
HAND = ("segoeprb.ttf", "comicbd.ttf", "arialbd.ttf")


def rgba(c, a=255):
    return tuple(c[:3]) + (a,)


def ctext(d, box, s, f, fill, stroke=0, stroke_fill=None, anchor_y=None):
    """Text centred in box (x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    x = (x0 + x1) / 2 - (l + r) / 2
    y = (y0 + y1) / 2 - (t + b) / 2 if anchor_y is None else anchor_y - t
    d.text((x, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)


def fit(s, names, w, h, start=60):
    """The biggest font of names that fits s in w x h."""
    size = start
    while size > 6:
        f = font(names, size)
        l, t, r, b = ImageDraw.Draw(Image.new("RGBA", (4, 4))).textbbox((0, 0), s, font=f)
        if r - l <= w and b - t <= h:
            return f
        size -= 1
    return font(names, 6)


def noise(img, amount, seed):
    rng = random.Random(seed)
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            k = rng.randint(-amount, amount)
            px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)), a)
    return img


# ======================================================================== Sign pictures

def lightbox(cols, rows, face, words, ink=(255, 255, 255), names=BOLD, rim=(40, 40, 46), margin=(10, 10)):
    """A backlit box sign: a coloured acrylic face in a dark rim, the words in white (one line or several)."""
    W, H = cols * P, rows * P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    mx, my = margin
    d.rectangle([0, my, W - 1, H - 1 - my], fill=rgba(rim))
    d.rectangle([3, my + 3, W - 4, H - 4 - my], fill=rgba(face))
    # (the face brighter in the middle, as a lightbox's tubes behind it)
    px = img.load()
    for y in range(my + 3, H - 3 - my):
        for x in range(3, W - 3):
            k = 1.0 + 0.12 * math.exp(-((y - H / 2) / (H / 3)) ** 2)
            r, g, b, a = px[x, y]
            px[x, y] = (min(255, int(r * k)), min(255, int(g * k)), min(255, int(b * k)), a)
    lines = words if isinstance(words, (list, tuple)) else [words]
    inner_h = H - 2 * my - 10
    lh = inner_h / len(lines)
    for i, ln in enumerate(lines):
        f = fit(ln, names, W - 16, int(lh * 0.78))
        ctext(d, (0, my + 5 + i * lh, W, my + 5 + (i + 1) * lh), ln, f, rgba(ink))
    return img


def neon(cols, rows, words, colour, back=(14, 12, 22), names=SCRIPT, frame=None, sub=None, sub_colour=None):
    """Neon tube lettering on a dark backing board, with a halo and white-hot cores."""
    W, H = cols * P, rows * P
    img = Image.new("RGBA", (W, H), rgba(back))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    main_h = H * (0.62 if sub else 0.8)
    f = fit(words, names, W - 20, int(main_h * 0.8))
    ctext(d, (0, 0, W, main_h + (4 if sub else H * 0.1)), words, f, rgba(colour))
    if sub:
        f2 = fit(sub, BOLD, W - 30, int(H * 0.22))
        ctext(d, (0, main_h, W, H - 4), sub, f2, rgba(sub_colour or colour))
    if frame:
        d.rounded_rectangle([4, 4, W - 5, H - 5], 8, outline=rgba(frame), width=3)
    halo = glow.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(halo)
    img.alpha_composite(halo)
    img.alpha_composite(glow)
    core = glow.filter(ImageFilter.MinFilter(3))
    px, cp = img.load(), core.load()
    for y in range(H):
        for x in range(W):
            if cp[x, y][3] > 200:
                r, g, b, a = px[x, y]
                px[x, y] = (min(255, r // 2 + 128), min(255, g // 2 + 128), min(255, b // 2 + 128), 255)
    return img


def plate(cols, rows, words, face=(214, 214, 206), ink=(30, 30, 34), margin=(14, 18), names=BOLD):
    """An engraved door plate (unlit)."""
    W, H = cols * P, rows * P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    mx, my = margin
    d.rectangle([mx, my, W - 1 - mx, H - 1 - my], fill=rgba(face))
    d.rectangle([mx, my, W - 1 - mx, my], fill=rgba(tuple(min(255, c + 20) for c in face)))
    d.rectangle([mx, H - 1 - my, W - 1 - mx, H - 1 - my], fill=rgba(tuple(int(c * 0.75) for c in face)))
    f = fit(words, names, W - 2 * mx - 10, H - 2 * my - 8)
    ctext(d, (mx, my, W - mx, H - my), words, f, rgba(ink))
    return noise(img, 4, len(words))


def exit_sign():
    img = Image.new("RGBA", (P, P), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 18, 59, 45], fill=(232, 232, 228, 255))
    d.rectangle([6, 20, 57, 43], fill=(250, 248, 244, 255))
    f = fit("EXIT", BOLD, 44, 18)
    ctext(d, (6, 20, 58, 44), "EXIT", f, (226, 28, 24, 255))
    return img


def rules():
    W, H = 2 * P, 2 * P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, W - 5, H - 5], fill=(24, 34, 92, 255))
    d.rectangle([7, 7, W - 8, H - 8], outline=(250, 210, 40, 255), width=2)
    ctext(d, (8, 10, W - 8, 30), "RINK RULES", fit("RINK RULES", IMPACT, W - 24, 18), (250, 210, 40, 255))
    lines = ["SKATE COUNTER-CLOCKWISE", "NO RUNNING", "NO FOOD OR DRINK ON RINK", "NO STREET SHOES",
             "NO SPEED SKATING", "IF YOU FALL, GET UP FAST", "HAVE FUN!"]
    for i, ln in enumerate(lines):
        s = f"{i + 1}. {ln}" if i < 6 else ln
        f = fit(s, NARROW, W - 26, 10, 11)
        d.text((13, 36 + i * 12), s, font=f, fill=(240, 240, 250, 255))
    return noise(img, 3, 31)


def norun():
    img = Image.new("RGBA", (P, P), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([10, 6, 53, 57], fill=(246, 246, 242, 255))
    d.ellipse([16, 9, 47, 40], outline=(210, 24, 24, 255), width=4)
    # a running figure, struck out
    d.ellipse([29, 13, 34, 18], fill=(20, 20, 22, 255))
    d.line([(31, 18), (29, 28)], fill=(20, 20, 22, 255), width=3)
    d.line([(29, 28), (23, 35)], fill=(20, 20, 22, 255), width=3)
    d.line([(29, 28), (35, 34)], fill=(20, 20, 22, 255), width=3)
    d.line([(30, 21), (37, 25)], fill=(20, 20, 22, 255), width=2)
    d.line([(30, 21), (24, 24)], fill=(20, 20, 22, 255), width=2)
    d.line([(20, 36), (43, 13)], fill=(210, 24, 24, 255), width=4)
    ctext(d, (10, 42, 54, 56), "NO RUNNING", fit("NO RUNNING", NARROW, 40, 11), (20, 20, 22, 255))
    return img


def whiteboard():
    W, H = 2 * P, P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 6, W - 3, H - 7], fill=(170, 172, 178, 255))
    d.rectangle([4, 8, W - 5, H - 9], fill=(246, 247, 244, 255))
    d.rectangle([20, H - 9, W - 21, H - 7], fill=(150, 152, 158, 255))  # the marker tray
    blue, red, green = (30, 60, 170, 255), (200, 30, 40, 255), (30, 140, 60, 255)
    f = font(HAND, 11)
    d.text((8, 9), "LESSONS TODAY", font=f, fill=blue)
    f2 = font(HAND, 9)
    d.text((10, 23), "beginners .... 2:00", font=f2, fill=blue)
    d.text((10, 33), "spins .......... 4:00", font=f2, fill=blue)
    d.text((10, 43), "ASK FOR COACH!", font=f2, fill=red)
    d.ellipse([100, 26, 118, 44], outline=green, width=2)  # a smiley
    d.point([(105, 32), (106, 32), (112, 32), (113, 32)], fill=green)
    d.arc([104, 31, 114, 40], 20, 160, fill=green, width=2)
    return img


def session():
    W, H = 2 * P, P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, W - 3, H - 5], fill=(18, 18, 22, 255))
    rows = [("ALL SKATE", (80, 255, 120), True), ("COUPLES SKATE", (255, 90, 190), False),
            ("SPEED SKATE", (255, 200, 60), False), ("LIMBO", (90, 200, 255), False)]
    f = font(NARROW, 11)
    for i, (s, c, lit) in enumerate(rows):
        y = 8 + i * 13
        col = c if lit else tuple(int(v * 0.42) for v in c)
        d.rectangle([8, y + 2, 14, y + 8], fill=rgba(col))
        d.text((20, y), s, font=f, fill=rgba(col))
    return img


def menu_window():
    """The rink-side snack window's board: SNACKS in neon over a short price list."""
    W, H = 2 * P, 2 * P
    top = neon(2, 1, "Snacks", (255, 170, 40), back=(20, 14, 10), names=SCRIPT)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(top, (0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, P + 2, W - 5, H - 6], fill=(22, 20, 18, 255))
    d.rectangle([6, P + 4, W - 7, H - 8], outline=(200, 200, 190, 255), width=1)
    items = [("PIZZA SLICE", "1.50"), ("HOT DOG", "1.25"), ("NACHOS", "2.00"), ("POPCORN", "1.00"), ("SODA", ".75")]
    f = font(NARROW, 9)
    for i, (n, p) in enumerate(items):
        y = P + 7 + i * 9
        d.text((10, y), n, font=f, fill=(250, 240, 220, 255))
        d.text((W - 32, y), p, font=f, fill=(255, 200, 80, 255))
    return img


def admission():
    W, H = 3 * P, P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 8, W - 3, H - 9], fill=(28, 24, 60, 255))
    d.rectangle([4, 10, W - 5, H - 11], outline=(255, 90, 190, 255), width=2)
    ctext(d, (6, 11, W - 6, 30), "ADMISSION", fit("ADMISSION", IMPACT, W - 30, 16), (90, 230, 255, 255))
    f = font(NARROW, 10)
    d.text((14, 32), "SKATING ...... $5.00", font=f, fill=(250, 250, 250, 255))
    d.text((100, 32), "SKATES ..... $2.00", font=f, fill=(250, 250, 250, 255))
    d.text((40, 43), "OPEN EVERY DAY  NOON - CLOSE", font=f, fill=(255, 200, 60, 255))
    return img


def poster(seed, title, lines, bg, ink, accent):
    img = Image.new("RGBA", (P, P), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 3, 55, 61], fill=rgba(bg))
    rng = random.Random(seed)
    for _ in range(14):  # confetti
        x, y = rng.randint(10, 52), rng.randint(5, 58)
        d.rectangle([x, y, x + 1, y + 1], fill=rgba(rng.choice([accent, ink, (255, 255, 255)])))
    ctext(d, (9, 5, 55, 26), title[0], fit(title[0], IMPACT, 42, 12), rgba(ink))
    if len(title) > 1:
        ctext(d, (9, 17, 55, 33), title[1], fit(title[1], IMPACT, 42, 12), rgba(accent))
    f = font(NARROW, 8)
    for i, ln in enumerate(lines):
        ctext(d, (9, 36 + i * 9, 55, 45 + i * 9), ln, f, (250, 250, 250, 255))
    return noise(img, 5, seed)


def nowshowing():
    """A lit poster case, 1 x 2: NOW SHOWING over the film the lore says it plays: yours."""
    W, H = P, 2 * P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([6, 4, W - 7, H - 5], fill=(170, 150, 90, 255))  # brass frame
    d.rectangle([9, 7, W - 10, H - 8], fill=(10, 10, 16, 255))
    ctext(d, (9, 9, W - 9, 22), "NOW SHOWING", fit("NOW SHOWING", NARROW, 42, 9), (255, 220, 120, 255))
    # the poster: a starry night, a spotlight beam, a question mark where the title should be
    for y in range(24, 104):
        t = (y - 24) / 80
        d.line([(11, y), (W - 12, y)], fill=(int(20 + 60 * t), int(16 + 20 * t), int(60 + 50 * t), 255))
    rng = random.Random(3131)
    for _ in range(20):
        x, y = rng.randint(12, 51), rng.randint(26, 70)
        d.point((x, y), fill=(255, 255, 230, 255))
    d.polygon([(32, 40), (20, 100), (44, 100)], fill=(255, 240, 180, 70))
    ctext(d, (11, 46, W - 11, 80), "?", font(IMPACT, 30), (255, 230, 140, 255))
    ctext(d, (9, 104, W - 9, 114), "YOUR FAVORITE", fit("YOUR FAVORITE", NARROW, 42, 8), (250, 250, 250, 255))
    ctext(d, (9, 112, W - 9, 121), "MOVIE  -  EVERY HOUR", fit("MOVIE  -  EVERY HOUR", NARROW, 44, 7), (200, 200, 210, 255))
    return img


def noticeboard():
    W, H = 2 * P, P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, W - 3, H - 5], fill=(120, 84, 50, 255))
    cork = Image.new("RGBA", (W - 10, H - 18), (186, 142, 92, 255))
    noise(cork, 12, 7)
    img.alpha_composite(cork, (5, 9))
    notes = [((10, 12, 44, 40), (250, 250, 240), ["STAFF", "ROTA"], -3),
             ((48, 10, 84, 42), (255, 245, 150), ["DO NOT", "TAKE THE", "SKATES"], 2),
             ((88, 14, 120, 38), (200, 230, 255), ["MOP AT", "CLOSE"], -2)]
    for (x0, y0, x1, y1), col, lines, rot in notes:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.rectangle([x0, y0, x1, y1], fill=rgba(col))
        f = font(HAND, 8)
        for i, ln in enumerate(lines):
            ctext(ld, (x0, y0 + 3 + i * 9, x1, y0 + 12 + i * 9), ln, f, (30, 30, 40, 255))
        ld.ellipse([(x0 + x1) // 2 - 2, y0 - 1, (x0 + x1) // 2 + 2, y0 + 3], fill=(220, 30, 30, 255))
        img.alpha_composite(layer.rotate(rot, center=((x0 + x1) / 2, (y0 + y1) / 2), resample=Image.BICUBIC))
    return img


def restroom_figures():
    img = Image.new("RGBA", (P, P), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([8, 10, 55, 53], fill=(30, 90, 160, 255))
    d.line([(32, 14), (32, 49)], fill=(240, 240, 240, 255), width=1)
    for cx, skirt in ((20, False), (44, True)):
        d.ellipse([cx - 3, 15, cx + 3, 21], fill=(250, 250, 250, 255))
        if skirt:
            d.polygon([(cx - 6, 37), (cx + 6, 37), (cx + 2, 23), (cx - 2, 23)], fill=(250, 250, 250, 255))
        else:
            d.rectangle([cx - 4, 23, cx + 4, 36], fill=(250, 250, 250, 255))
        d.rectangle([cx - 3, 36, cx - 1, 47], fill=(250, 250, 250, 255))
        d.rectangle([cx + 1, 36, cx + 3, 47], fill=(250, 250, 250, 255))
    return img


def mirror_pic():
    img = Image.new("RGBA", (P, P), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, 61, 59], fill=(196, 200, 208, 255))
    for y in range(7, 57):
        t = (y - 7) / 50
        d.line([(5, y), (58, y)], fill=(int(120 + 40 * t), int(140 + 40 * t), int(156 + 34 * t), 255))
    d.polygon([(10, 56), (30, 8), (36, 8), (16, 56)], fill=(220, 232, 240, 110))
    d.polygon([(24, 56), (42, 8), (45, 8), (27, 56)], fill=(220, 232, 240, 80))
    return img


def bigtv():
    """The cinema's one big TV, 5 x 3: a thin bezel round a lit screen showing a film (a sunset drive)."""
    W, H = 5 * P, 3 * P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 6, W - 3, H - 4], 6, fill=(20, 20, 24, 255))
    x0, y0, x1, y1 = 9, 13, W - 10, H - 12
    for y in range(y0, y1):
        t = (y - y0) / (y1 - y0)
        c = (int(250 - 120 * t), int(120 + 20 * t), int(60 + 110 * t)) if t < 0.62 else (int(40 - 20 * (t - 0.6)), 26, 44)
        if y % 2:
            c = tuple(int(v * 0.88) for v in c)
        d.line([(x0, y), (x1, y)], fill=c + (255,))
    sy = y0 + int((y1 - y0) * 0.6)
    d.ellipse([W // 2 - 26, sy - 34, W // 2 + 26, sy + 18], fill=(255, 226, 140, 255))
    d.rectangle([x0, sy, x1, y1], fill=(28, 18, 36, 255))
    # palms and a road to the horizon
    d.polygon([(W // 2 - 8, sy), (W // 2 + 8, sy), (W // 2 + 90, y1), (W // 2 - 90, y1)], fill=(52, 44, 60, 255))
    for k in range(5):
        yy = sy + 6 + k * 9
        d.line([(W // 2, yy), (W // 2, yy + 4)], fill=(255, 220, 120, 255), width=2)
    for px_, s in ((40, 1.0), (80, 0.7), (W - 50, 1.1)):
        d.line([(px_, y1), (px_ + 6 * s, sy - 50 * s)], fill=(16, 10, 20, 255), width=int(4 * s) + 1)
        for a in range(0, 360, 50):
            ex = px_ + 6 * s + math.cos(math.radians(a)) * 26 * s
            ey = sy - 50 * s + math.sin(math.radians(a)) * 12 * s + 6 * s
            d.line([(px_ + 6 * s, sy - 50 * s), (ex, ey)], fill=(16, 10, 20, 255), width=int(3 * s) + 1)
    d.rectangle([W // 2 - 10, H - 9, W // 2 + 10, H - 7], fill=(60, 220, 120, 255))  # power LED
    return img


def revolving(level, name):
    """The sign over a revolving door naming where it goes, as Level 36's gate screens: yellow on a dark grey screen."""
    W, H = 3 * P, P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([2, 6, W - 3, H - 7], 4, fill=(26, 27, 30, 255))
    d.rounded_rectangle([5, 9, W - 6, H - 10], 3, fill=(44, 45, 50, 255))
    noise(img, 3, level)
    ctext(d, (8, 9, W - 8, 40), f"TO LV{level}", fit(f"TO LV{level}", BOLD, W - 40, 26), (255, 206, 20, 255))
    ctext(d, (8, 40, W - 8, H - 11), name, fit(name, BOLD, W - 40, 9), (236, 236, 236, 255))
    return img


def hours():
    """The lobby's hours board by the front doors, 1 x 2: a white panel of black lettering."""
    W, H = P, 2 * P
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, W - 7, H - 7], fill=(30, 30, 34, 255))
    d.rectangle([8, 8, W - 9, H - 9], fill=(246, 244, 236, 255))
    ctext(d, (8, 10, W - 8, 24), "HOURS", fit("HOURS", IMPACT, 40, 12), (200, 30, 40, 255))
    rows = ["MON-THU", "NOON - 10", "FRI-SAT", "NOON - 1AM", "SUN", "NOON - 8", "", "SKATE AT", "YOUR OWN", "RISK"]
    for i, r in enumerate(rows):
        if r:
            ctext(d, (8, 26 + i * 9, W - 8, 35 + i * 9), r, fit(r, NARROW, 42, 8), (30, 30, 36, 255))
    return img


def extinguisher_tex():
    img = M.painted_metal(seed=3611, base=(196, 28, 26), panel=False, chips=1)
    return img


# ======================================================================== The plate kinds
# (name, cols, rows, style, picture or None, glow, light). Must match WorldLayout.L31Mounts (name, cols, rows).
SIGNS = []


def sign(name, cols, rows, pic, style="panel", glow=0, light=None, box=None):
    SIGNS.append((name, cols, rows, style, pic, glow, light, box))


def define():
    blue, red, teal, purple, grey = (30, 80, 190), (200, 40, 36), (20, 130, 140), (110, 40, 170), (70, 72, 78)
    # Over the rooms' doors, on the corridor side (2 wide over a 2-wide door, just under the ceiling)
    sign("rent", 2, 1, lightbox(2, 1, blue, "SKATE RENTAL"), glow=200, light=[42, 4, 5], box=(0, 2.5, 16, 13.5))
    sign("snack", 2, 1, lightbox(2, 1, red, "SNACK BAR"), glow=200, light=[3, 4, 5], box=(0, 2.5, 16, 13.5))
    sign("arc", 2, 1, neon(2, 1, "Arcade", (190, 90, 255), frame=(60, 230, 255)), glow=255, light=[48, 5, 6], box=(0, 1, 16, 15))
    sign("rest", 2, 1, lightbox(2, 1, teal, "RESTROOMS"), glow=180, light=[30, 3, 4], box=(0, 2.5, 16, 13.5))
    sign("cine", 2, 1, lightbox(2, 1, (110, 14, 20), "CINEMA", ink=(255, 222, 120), names=IMPACT), glow=200, light=[0, 4, 4],
         box=(0, 2.5, 16, 13.5))
    sign("staff", 2, 1, plate(2, 1, "EMPLOYEES ONLY", face=(200, 30, 30), ink=(255, 255, 255)), box=(0, 4.5, 16, 11.5))
    sign("store", 2, 1, plate(2, 1, "STORAGE"), box=(0, 4.5, 16, 11.5))
    sign("mech", 2, 1, plate(2, 1, "MECHANICAL", face=(230, 196, 30)), box=(0, 4.5, 16, 11.5))
    sign("exit", 1, 1, exit_sign(), glow=220, light=[0, 5, 4], box=(1, 4.5, 15, 11.5))
    # Inside
    sign("rentbig", 3, 1, lightbox(3, 1, blue, "SKATE RENTAL", names=IMPACT, margin=(10, 6)), glow=200, light=[42, 4, 6],
         box=(0, 1.5, 16, 14.5))
    for i, s in enumerate(("KIDS 10-13", "SIZES 1-4", "SIZES 5-8", "SIZES 9-13")):
        sign(f"sz{i}", 1, 1, plate(1, 1, s, face=(250, 220, 40), ink=(20, 20, 30), margin=(3, 20), names=NARROW), box=(0.5, 5, 15.5, 11))
    sign("wb", 2, 1, whiteboard(), box=(0, 1.5, 16, 14.5))
    sign("snackbig", 3, 1, neon(3, 1, "Snack Bar", (255, 120, 40), frame=(255, 220, 80)), glow=255, light=[6, 5, 7], box=(0, 1, 16, 15))
    sign("prizes", 2, 1, neon(2, 1, "PRIZES", (255, 230, 60), names=IMPACT, frame=(255, 80, 180)), glow=255, light=[10, 5, 6],
         box=(0, 1, 16, 15))
    sign("tokens", 1, 1, plate(1, 1, "GREEN CARDS", face=(30, 150, 70), ink=(255, 255, 255), margin=(3, 18), names=NARROW),
         box=(0.5, 4.5, 15.5, 11.5))
    sign("name", 5, 1, neon(5, 1, "Stardust", (255, 90, 200), names=SCRIPT, sub="ROLLER RINK", sub_colour=(90, 230, 255)),
         glow=255, light=[52, 6, 8], box=(0, 0.5, 16, 15.5))
    sign("arcbig", 3, 1, neon(3, 1, "Arcade", (190, 90, 255), frame=(60, 230, 255)), glow=255, light=[48, 5, 7], box=(0, 1, 16, 15))
    sign("rules", 2, 2, rules(), box=(0, 0.5, 16, 15.5))
    sign("norun", 1, 1, norun(), box=(2, 1, 14, 15))
    sign("session", 2, 1, session(), glow=160, light=[24, 3, 4], box=(0, 2.5, 16, 13.5))
    sign("snackwin", 2, 2, menu_window(), glow=200, light=[6, 4, 6], box=(0, 1, 16, 15))
    sign("admit", 3, 1, admission(), style="hang", glow=140, light=[50, 3, 5], box=(0, 2, 16, 14))
    sign("mw", 1, 1, restroom_figures(), box=(2, 2.5, 14, 13.5))
    sign("mirror", 1, 1, mirror_pic(), box=(0.5, 1, 15.5, 15))
    sign("dryer", 1, 1, None, style="dryer")
    sign("ext", 1, 1, None, style="extinguisher")
    sign("alarm", 1, 1, None, style="alarm")
    posters = [
        (("COUPLES", "SKATE"), ["FRIDAY NITE", "LIGHTS DOWN", "8 - 11 PM"], (60, 20, 90), (255, 120, 220), (90, 230, 255)),
        (("BIRTHDAY", "PARTIES!"), ["PIZZA + SKATES", "ASK AT THE", "FRONT DESK"], (250, 210, 40), (200, 30, 120), (30, 90, 200)),
        (("LEARN TO", "SKATE"), ["LESSONS DAILY", "WITH COACH", "ALL AGES"], (20, 110, 160), (255, 255, 255), (255, 220, 60)),
        (("RETRO", "NIGHT"), ["THROWBACK HITS", "THURSDAYS", "18 AND OVER"], (240, 90, 40), (255, 250, 220), (40, 20, 60)),
    ]
    for i, (t, ls, bg, ink, acc) in enumerate(posters):
        sign(f"poster{i}", 1, 1, poster(3141 + i, t, ls, bg, ink, acc), box=(2, 0.5, 14, 15.5))
    sign("nowshow", 1, 2, nowshowing(), glow=150, light=[40, 3, 4], box=(1.5, 1, 14.5, 15))
    sign("board", 2, 1, noticeboard(), box=(0, 1.5, 16, 14.5))
    sign("bigtv", 5, 3, bigtv(), glow=230, light=[30, 3, 9], box=(0, 0.5, 16, 15.75))
    sign("hours", 1, 2, hours(), box=(1.5, 1, 14.5, 15))
    for lv, nm in ((9, "THE SUBURBS"), (10, "BUMPER CROP"), (11, "THE ENDLESS CITY")):
        sign(f"rev{lv}", 3, 1, revolving(lv, nm), glow=200, light=[8, 3, 4], box=(0, 1.5, 16, 14.5))


def plate_shapes():
    """One shape per kind: the panel at the back (south) of its block, picture north; or hung, or a fitting."""
    save(M.painted_metal(seed=3601, base=(36, 36, 40), panel=False, chips=1), "plate-edge")
    save(extinguisher_tex(), "plate-red")
    save(M.brushed_metal(seed=3602, base=(200, 204, 210), sheen=14), "plate-chrome")
    save(M.painted_metal(seed=3603, base=(222, 222, 220), panel=False, chips=1), "plate-white")
    save(M.rubber(seed=3604, base=(30, 30, 32)), "plate-black")
    kinds, shapes, lights = [], {}, {}
    for name, cols, rows, style, pic, glow, light, box_ in SIGNS:
        for c in range(cols):
            for r in range(rows):
                kind = f"{name}{c}{r}"
                kinds.append(kind)
                if light:
                    lights[kind] = light
                tex = f"plate-{kind}"
                if pic is not None:
                    save(pic.crop((c * P, r * P, c * P + P, r * P + P)), tex)
                if style == "dryer":
                    els = [B("Body", (3, 6, 10), (13, 13, 16), "plate-white"),
                           B("Nozzle", (6.5, 4.5, 11), (9.5, 6, 14), "plate-chrome"),
                           B("Button", (7, 9, 9.6), (9, 11, 10), "plate-chrome")]
                elif style == "extinguisher":
                    els = [B("Bracket", (7, 3, 15.5), (9, 9, 16), "plate-black"),
                           B("Tank", (6.4, 0.5, 12.4), (9.6, 11, 15.5), "plate-red"),
                           B("TankX", (6, 1, 12.8), (10, 10.5, 15.1), "plate-red"),
                           B("Neck", (7.3, 11, 13.2), (8.7, 12.4, 14.6), "plate-black"),
                           B("Handle", (7.6, 12.4, 12.4), (8.4, 13, 15.2), "plate-black"),
                           B("Hose", (9.6, 3, 13.4), (10.4, 11.6, 14.2), "plate-black"),
                           B("Label", (6.9, 4, 12.3), (9.1, 7.5, 12.4), "plate-white", faces=("north",))]
                elif style == "alarm":
                    els = [B("Box", (5, 5, 14), (11, 12, 16), "plate-red"),
                           B("Pull", (6.5, 7, 13.2), (9.5, 9, 14), "plate-white")]
                else:
                    # (the picture's margin is cut off the outer columns and rows only)
                    x0, y0, x1, y1 = box_
                    xa, xb = (x0 if c == cols - 1 else 0), (x1 if c == 0 else 16)
                    ya, yb = (y0 if r == rows - 1 else 0), (y1 if r == 0 else 16)
                    uv = (16 - xb, 16 - yb, 16 - xa, 16 - ya)
                    zf = 7.5 if style == "hang" else 15.0
                    zb = 8.5 if style == "hang" else 16
                    els = [B("Panel", (xa, ya, zf), (xb, yb, zb), "plate-edge", faces=without(DIRS, "south") if style != "hang" else DIRS,
                             north=("art", uv, glow or None) if glow else ("art", uv))]
                    if style == "hang" and r == 0:
                        for x in (3, 13):
                            if xa <= x <= xb:
                                els.append(B(f"Rod{x}", (x - 0.3, yb, 7.7), (x + 0.3, 16, 8.3), "plate-chrome"))
                    if not glow:
                        els[0]["faces"]["north"].pop("glow", None)
                shapes[kind] = (els, tex)
    return kinds, shapes, lights


def plate_block(kinds, shapes, lights):
    shape_refs, textures, sels = {}, {}, {}
    for kind in kinds:
        els, tex = shapes[kind]
        keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
        data = {"textureWidth": 16, "textureHeight": 16,
                "textures": {k: "backrooms:block/31/" + (tex if k == "art" else k) for k in keys}, "elements": els}
        write_json(os.path.join(SHAPES, f"l31-plate-{kind}.json"), data)
        ref = "backrooms:block/31/l31-plate-" + kind
        # a selection box round what is there
        xs = [v for e in els for v in (e["from"][0], e["to"][0])]
        ys = [v for e in els for v in (e["from"][1], e["to"][1])]
        zs = [v for e in els for v in (e["from"][2], e["to"][2])]
        box_ = (min(xs) / 16, min(ys) / 16, min(zs) / 16, max(xs) / 16, max(ys) / 16, max(zs) / 16)
        for side in SIDES:
            key = f"l31-plate-{kind}-{side}"
            shape_refs[key] = {"base": ref, "rotateY": ROT[side]} if ROT[side] else {"base": ref}
            sel = {"x1": box_[0], "y1": box_[1], "z1": box_[2], "x2": box_[3], "y2": box_[4], "z2": box_[5]}
            if ROT[side]:
                sel["rotateY"] = ROT[side]
            sels[key] = sel
    data = {"code": "l31-plate",
            "variantgroups": [{"code": "kind", "states": kinds}, {"code": "side", "states": SIDES}],
            "shapeByType": shape_refs, "lightHsvByType": {f"l31-plate-{k}-*": v for k, v in lights.items()},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 3, "drops": [], "sounds": METAL,
            "selectionboxByType": sels, "collisionboxByType": sels}
    write_json(os.path.join(BLOCKS, "l31-plate.json"), data,
               "Level 31: wall mounts (round 3): signs over the rooms' doors and inside them, the rink's name, rules and session boards, "
               "posters, the Coach's whiteboard, the cinema's big TV, a washroom mirror, a hand dryer, a fire extinguisher and alarm; "
               "a thin panel against the wall behind its block (or hung from the ceiling), its face toward the side; "
               "kind <sign><col><row>, col 0 at the viewer's left, row 0 at the top")


# ======================================================================== Multi-block props

def porcelain():
    img = M.noise_hv((240, 240, 236), 2, 3621, S, 2, (8, 4))
    save(img, "porcelain")


def stall():
    """A toilet stall: two partitions and a door ajar on short legs, 28 units tall, the toilet against the wall inside."""
    save(M.painted_metal(seed=3622, base=(150, 186, 200), panel=False, chips=2), "stall-panel")
    els = [
        B("PartL", (0, 2, 0.5), (0.8, 28, 16), "stall-panel"),
        B("PartR", (15.2, 2, 0.5), (16, 28, 16), "stall-panel"),
        B("LegL", (0.1, 0, 1), (0.7, 2, 1.6), "plate-chrome"),
        B("LegR", (15.3, 0, 1), (15.9, 2, 1.6), "plate-chrome"),
        B("Rail", (0, 27.2, 0.5), (16, 28, 1.3), "plate-chrome"),
        # The door, hinged at the west post, a third open into the stall
        B("Door", (1, 2.5, 0.5), (14.6, 27, 1.2), "stall-panel", rot=(0, -28, 0), origin=(1, 14, 0.85)),
        B("Latch", (12.8, 13, 0.0), (13.8, 14.5, 0.5), "plate-chrome", rot=(0, -28, 0), origin=(1, 14, 0.85)),
        # The toilet
        B("Bowl", (5, 0, 7), (11, 6.5, 13.5), "porcelain"),
        B("Seat", (4.6, 6.5, 6.6), (11.4, 7.2, 13.6), "porcelain"),
        B("Tank", (4.2, 6.5, 13.5), (11.8, 12, 15.8), "porcelain"),
        B("Flush", (10, 11.2, 13.3), (11, 11.8, 13.6), "plate-chrome"),
        B("Roll", (13.6, 9, 9), (15.2, 10.6, 10.6), "plate-white"),
    ]
    return shape("l31-stall", els)


def vanity():
    save(M.wood_planks(seed=3623, base=(110, 80, 56), planks=1, direction="h", grain=3, flecks=0.4), "vanity-front")
    save(M.noise_hv((60, 62, 68), 3, 3624, S, 3, (6, 6)), "vanity-top")
    els = [
        B("Cabinet", (0, 0, 3), (16, 11, 16), "vanity-front"),
        B("Top", (0, 11, 2), (16, 12.5, 16), "vanity-top"),
        B("Basin", (4, 11.2, 4.5), (12, 12.6, 12), "porcelain"),
        B("Hole", (5, 12.6, 5.5), (11, 12.7, 11), "plate-black", faces=("up",)),
        B("Tap", (7.5, 12.5, 12.5), (8.5, 15, 13.5), "plate-chrome"),
        B("Spout", (7.6, 14.2, 10.6), (8.4, 14.9, 12.6), "plate-chrome"),
        B("Soap", (12.6, 12.5, 13), (14.2, 15, 14.6), "plate-white"),
        B("Back", (0, 12.5, 15.4), (16, 16, 16), "porcelain"),
    ]
    return shape("l31-vanity", els)


def photobooth():
    save(M.painted_metal(seed=3625, base=(40, 120, 200), panel=False, chips=1), "booth-body")
    save(M.noise_hv((170, 24, 40), 4, 3626, S, 3, (2, 10)), "booth-curtain")
    head = neon(1, 1, "PHOTO", (255, 240, 120), back=(150, 20, 60), names=IMPACT)
    save(head.resize((S, S), Image.LANCZOS), "booth-head")
    strip = Image.new("RGBA", (S, S), (30, 30, 34, 255))
    d = ImageDraw.Draw(strip)
    for i in range(4):
        d.rectangle([12, 2 + i * 7, 19, 7 + i * 7], fill=(230, 220, 200, 255))
        d.ellipse([14, 3 + i * 7, 17, 6 + i * 7], fill=(120, 90, 70, 255))
    d.text((3, 2), "4", fill=(255, 220, 80, 255))
    save(strip, "booth-strip")
    els = [
        B("Back", (0, 0, 14.5), (16, 30, 16), "booth-body"),
        B("SideL", (0, 0, 1), (1, 30, 14.5), "booth-body"),
        B("SideR", (15, 0, 1), (16, 30, 14.5), "booth-body"),
        B("Roof", (0, 30, 1), (16, 31, 16), "booth-body"),
        B("Head", (0, 25, 0.4), (16, 30, 1.4), "booth-body", north="booth-head", glow=None),
        B("PanelR", (9, 0, 0.6), (15, 25, 1.4), "booth-body", north="booth-strip"),
        B("Curtain", (1, 3, 1.0), (9, 24.6, 1.6), "booth-curtain"),
        B("Rod", (1, 24.6, 1.1), (9, 25, 1.5), "plate-chrome"),
        B("Seat", (3, 0, 7), (13, 7, 14), "plate-black"),
    ]
    els[4]["faces"]["north"]["glow"] = 200
    return shape("l31-photobooth", els)


def jukebox():
    front = Image.new("RGBA", (S * 2, S * 2), (40, 16, 30, 255))
    d = ImageDraw.Draw(front)
    W = S * 2
    d.rounded_rectangle([6, 6, W - 7, 30], 10, fill=(240, 220, 160, 255))  # the record window
    d.rounded_rectangle([9, 9, W - 10, 28], 8, fill=(20, 20, 26, 255))
    for k in range(5):
        d.ellipse([12 + k * 9, 14, 20 + k * 9, 22], fill=(30, 30, 30, 255), outline=(200, 160, 60, 255))
    for k in range(8):  # selection buttons
        d.rectangle([10 + k * 6, 34, 13 + k * 6, 37], fill=(250, 250, 240, 255))
    for y in range(42, 60, 3):  # the speaker grille
        d.line([(10, y), (W - 11, y)], fill=(170, 140, 70, 255))
    save(front, "juke-front")
    save(M.noise_hv((255, 90, 190), 2, 3627, S, 2, (8, 4)), "juke-neonpink")
    save(M.noise_hv((80, 220, 255), 2, 3628, S, 2, (8, 4)), "juke-neoncyan")
    save(M.wood_planks(seed=3629, base=(110, 40, 40), planks=1, direction="v", grain=3, flecks=0.3), "juke-body")
    els = [
        B("Body", (1, 0, 4), (15, 16, 13), "juke-body", north="juke-front"),
        B("Arch1", (2, 16, 4.5), (14, 19, 12.5), "juke-body"),
        B("Arch2", (4, 19, 5), (12, 21, 12), "juke-body"),
        B("Arch3", (6, 21, 5.5), (10, 22, 11.5), "juke-body"),
        B("TubeL", (1.2, 2, 3.4), (2.4, 17, 4.2), "juke-neonpink", glow=255),
        B("TubeR", (13.6, 2, 3.4), (14.8, 17, 4.2), "juke-neonpink", glow=255),
        B("TubeT1", (2.2, 17, 3.9), (13.8, 18.2, 4.7), "juke-neoncyan", glow=255),
        B("TubeT2", (4.2, 19.2, 4.4), (11.8, 20.2, 5.2), "juke-neonpink", glow=255),
        B("Foot", (0.6, 0, 3.6), (15.4, 1.2, 13.4), "plate-chrome"),
    ]
    return shape("l31-jukebox", els)


def trophycase():
    save(M.wood_planks(seed=3630, base=(96, 60, 36), planks=2, direction="h", grain=3, flecks=0.4), "case-wood")
    gold = M.brushed_metal(seed=3631, base=(230, 186, 60), sheen=24)
    save(gold, "case-gold")
    save(M.noise_hv((26, 30, 60), 3, 3632, S, 3, (4, 4)), "case-back")
    els = [
        B("Base", (0, 0, 3), (16, 9, 15), "case-wood"),
        B("Back", (0, 9, 14), (16, 29, 15), "case-back"),
        B("Top", (0, 29, 3), (16, 30.5, 15), "case-wood"),
        B("PostL", (0, 9, 3), (1, 29, 4), "case-wood"),
        B("PostR", (15, 9, 3), (16, 29, 4), "case-wood"),
        B("SideL", (0, 9, 4), (0.5, 29, 14), "case-back"),
        B("SideR", (15.5, 9, 4), (16, 29, 14), "case-back"),
        B("Shelf", (1, 18.5, 4), (15, 19.2, 14), "plate-chrome"),
    ]
    rng = random.Random(3633)
    for shelf, y in ((0, 9), (1, 19.2)):
        for k, x in enumerate((3, 8, 12.5)):
            h = rng.uniform(4.5, 8)
            els += [B(f"Cup{shelf}{k}", (x - 1.2, y + 1.6, 8), (x + 1.2, y + h, 10.4), "case-gold"),
                    B(f"Stem{shelf}{k}", (x - 0.4, y + 0.6, 8.8), (x + 0.4, y + 1.6, 9.6), "case-gold"),
                    B(f"Foot{shelf}{k}", (x - 1.4, y, 7.8), (x + 1.4, y + 0.6, 10.6), "case-wood")]
    return shape("l31-trophycase", els)


def mediacab():
    els = [
        B("Cabinet", (0, 0, 4), (16, 7, 15), "plate-black"),
        B("Doors", (1, 1, 3.6), (15, 6, 4), "plate-edge"),
        B("Bar", (1, 7, 9), (15, 9, 13), "plate-black"),
        B("Grille", (1.2, 7.3, 8.8), (14.8, 8.7, 9), "plate-chrome"),
    ]
    return shape("l31-mediacab", els)


def riser():
    """A cinema step: carpet on top, a dark riser with a row of small amber lights at its foot (lit), as a json cube."""
    carpet = M.noise_hv((92, 20, 32), 5, 3640, S, 3, (2, 2))
    save(carpet, "riser-carpet")
    side = Image.new("RGBA", (S, S), (22, 18, 22, 255))
    noise(side, 4, 3641)
    d = ImageDraw.Draw(side)
    d.rectangle([0, 0, S - 1, 3], fill=(70, 18, 28, 255))  # the carpet's nosing
    d.rectangle([0, S - 6, S - 1, S - 5], fill=(60, 60, 64, 255))
    for x in range(3, S, 8):
        d.rectangle([x, S - 9, x + 1, S - 8], fill=(255, 190, 80, 255))
    save(side, "riser-side")
    el = B("Step", (0, 0, 0), (16, 16, 16), "riser-side", up="riser-carpet", down="riser-carpet")
    for f in ("north", "east", "south", "west"):
        el["faces"][f]["glow"] = 60
    return shape("l31-riser", [el])


def truss():
    """A box truss of aluminium tube along X under the ceiling, with two par cans hanging from it (coloured lenses, lit)."""
    for n, c in (("lens-pink", (255, 80, 200)), ("lens-cyan", (60, 230, 255)), ("lens-amber", (255, 190, 60)), ("lens-violet", (170, 100, 255))):
        img = Image.new("RGBA", (S, S), rgba(c))
        d = ImageDraw.Draw(img)
        d.ellipse([6, 6, 25, 25], fill=rgba(tuple(min(255, v + 60) for v in c)))
        d.ellipse([12, 12, 19, 19], fill=(255, 255, 255, 255))
        save(img, "truss-" + n)
    els = []
    for i, (y, z) in enumerate(((12.5, 5.5), (12.5, 10), (15, 7.75))):
        els.append(B(f"Chord{i}", (0, y, z), (16, y + 0.6, z + 0.6), "plate-chrome"))
    for x in (0.2, 7.7, 15.2):
        els.append(B(f"V{x}a", (x, 12.5, 5.5), (x + 0.6, 15.6, 6.1), "plate-chrome"))
        els.append(B(f"V{x}b", (x, 12.5, 10), (x + 0.6, 15.6, 10.6), "plate-chrome"))
        els.append(B(f"V{x}c", (x, 12.5, 5.5), (x + 0.6, 13.1, 10.6), "plate-chrome"))
    for k, (x, lens) in enumerate(((4, "pink"), (12, "cyan"))):
        els += [B(f"Clamp{k}", (x - 0.4, 11, 7.6), (x + 0.4, 12.5, 8.4), "plate-black"),
                B(f"Yoke{k}", (x - 1.8, 9.6, 7.7), (x + 1.8, 11, 8.3), "plate-black"),
                B(f"Can{k}", (x - 1.4, 6.5, 6.6), (x + 1.4, 10.5, 9.4), "plate-black", down=("truss-lens-" + lens, None, 255))]
    return shape("l31-truss", els)


def blocks():
    porcelain()
    ref = truss()
    prop_block("l31-truss", "Level 31: a lighting truss of aluminium tube under a rink's ceiling, two coloured par cans hanging from it, along the axis",
               lambda k: {"base": ref} if k == "we" else {"base": ref, "rotateY": 90}, (0, 0.4, 0.3, 1, 1, 0.7), None,
               kinds=["we", "ns"], kindgroup="axis", oriented=False, resistance=3, extra={"lightHsv": [50, 3, 9]})
    full = (0, 0, 0, 1, 1, 1)
    ref = stall()
    prop_block("l31-stall", "Level 31: a toilet stall, partitions and a door ajar on short legs (28 units tall), the toilet against the wall; the door faces the side",
               lambda k: ref, full, full, resistance=3)
    ref = vanity()
    prop_block("l31-vanity", "Level 31: a washroom vanity, a basin set in a counter on a wooden cabinet; the basin faces the side (the mirror is an l31-plate over it)",
               lambda k: ref, (0, 0, 0.125, 1, 0.8, 1), (0, 0, 0.125, 1, 0.78, 1), resistance=3)
    ref = photobooth()
    prop_block("l31-photobooth", "Level 31: an arcade photo booth, 31 units tall, a red curtain and a lit PHOTO header toward the side",
               lambda k: ref, full, full, resistance=3)
    ref = jukebox()
    prop_block("l31-jukebox", "Level 31: a 1990s jukebox, neon tubes round a record window, 22 units tall, toward the side",
               lambda k: ref, (0.06, 0, 0.22, 0.94, 1, 0.84), (0.06, 0, 0.22, 0.94, 1, 0.84), resistance=3,
               extra={"lightHsv": [50, 4, 6]})
    ref = trophycase()
    prop_block("l31-trophycase", "Level 31: a trophy case, wood and glass, 30 units tall, cups on two shelves, open toward the side",
               lambda k: ref, (0, 0, 0.18, 1, 1, 0.94), (0, 0, 0.18, 1, 1, 0.94), material="Wood", sounds=WOOD, resistance=3)
    ref = mediacab()
    prop_block("l31-mediacab", "Level 31: the cinema TV's low black cabinet with a sound bar on it, toward the side",
               lambda k: ref, (0, 0, 0.22, 1, 0.57, 0.94), (0, 0, 0.22, 1, 0.57, 0.94), resistance=3)
    ref = riser()
    data = {"code": "l31-riser", "shape": {"base": ref}, "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Cloth", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
            "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": CLOTH, "lightHsv": [8, 3, 2]}
    write_json(os.path.join(BLOCKS, "l31-riser.json"), data,
               "Level 31: a cinema step, maroon carpet on top and a dark riser with a row of small amber aisle lights")


def main():
    define()
    kinds, shapes, lights = plate_shapes()
    plate_block(kinds, shapes, lights)
    blocks()
    print(f"Level 31 round 3: {len(kinds)} plate kinds;", "textures in", os.path.relpath(TEX), "; blocktypes in", os.path.relpath(BLOCKS))
    # (for WorldLayout.L31Mounts)
    print("mounts:", ", ".join(f'("{n}", {c}, {r})' for n, c, r, *_ in SIGNS))


if __name__ == "__main__":
    main()
