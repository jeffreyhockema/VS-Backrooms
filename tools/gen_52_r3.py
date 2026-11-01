"""Level 52, "The Greenfield Campus": round 3's blocks (2026-11-01), called from gen_52.py's main (it saves and writes
through gen_52's own helpers, so its stale-file sweep and its check cover these too).

    l52-sign-{kind}-{side}         a plate or fitting hung on the wall behind its block: EXIT signs, restroom pictograms,
                                   floor numbers and directories in the stairwells, notice boards, posters, fire hose
                                   cabinets and extinguishers, mirrors, the M.E.G.'s outpost sign, COOL MART CO., building
                                   numbers on the entrance canopies, the tower clocks' dials, a wall clock, J. Barry's alarm
                                   bells, the roof doors, lift doors, classroom door leaves standing open; JSON shapes
    l52-stall-{part}-{side}        a toilet stall (the pan, the partition on its left), two blocks high
    l52-fumehood-{part}-{side}     a lab's fume hood on its cabinet, two blocks high
    l52-bleacher-{side}            one row of aluminium bleachers (seat plank, foot plank, frame)
    l52-goal-{part}-{half}-{side}  a football goal three blocks wide, two high (posts, crossbar, net)
    l52-flagpole-{part}-{side}     a flagpole: its base, the pole, the top with a flag
    l52-post-{kind}-{part}-{half}-{side}   a board on two posts, two blocks wide and two high: the campus map at a gap, the
                                   M.E.G.'s stencilled campus names, the abandoned bases' boards
    l52-jet                        a fountain's middle: a bowl on a column, a spout of water
    l52-vent                       a roof vent
    l52-hvac-{part}                an air-handling unit's casing (louvres) and its top (fan grilles); cubes
    l52-track-{kind}               a running track's red rubber (plain, a white lane line north-south or west-east); cubes

Signs keep to what the lore allows: numbers, the words every building has, and the people's own signs (see the plan's
round 3 section)."""
import math
import os
import random

from PIL import Image, ImageDraw

import gen_52_tex as T
import matlib as M
from modelkit import box

G = None  # gen_52, set by build()
SIDES = ["north", "east", "south", "west"]
FACADES = ["white", "beige", "brick", "grey", "blue"]
PALETTES = ["beige", "white", "blue", "grey"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
FULL = (0, 0, 16, 16)
P = 64  # sign faces: 64 px a block

# ======================================================================== drawing helpers


def plate(w, h, colour, seed, amp=3, mottle=3):
    return M.noise_hv(colour, amp, seed, (w, h), mottle, (16, 8), hue=0.5)


def frame(img, colour, width=2):
    p = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            if x < width or y < width or x >= w - width or y >= h - width:
                p[x, y] = M.rgba(colour)


def text(img, s, box_, colour, px, stroke=0):
    T._text(img, s, box_, colour, px, stroke)


def square(img):
    """Resized to 64 x 64: the face's UV covers the whole texture, so a sign drawn at its plate's aspect comes back true."""
    return img.resize((P, P), Image.LANCZOS)


def tri(img, cx, cy, r, up, colour):
    d = ImageDraw.Draw(img)
    pts = [(cx - r, cy + r * 0.8), (cx + r, cy + r * 0.8), (cx, cy - r * 0.9)] if up else [(cx - r, cy - r * 0.8), (cx + r, cy - r * 0.8), (cx, cy + r * 0.9)]
    d.polygon(pts, fill=tuple(colour) + (255,))


def man(img, cx, top, k, colour):
    d = ImageDraw.Draw(img)
    c = tuple(colour) + (255,)
    d.ellipse((cx - 3 * k, top, cx + 3 * k, top + 6 * k), fill=c)
    d.rectangle((cx - 4 * k, top + 7 * k, cx + 4 * k, top + 19 * k), fill=c)
    d.rectangle((cx - 4 * k, top + 19 * k, cx - 1 * k, top + 30 * k), fill=c)
    d.rectangle((cx + 1 * k, top + 19 * k, cx + 4 * k, top + 30 * k), fill=c)


def woman(img, cx, top, k, colour):
    d = ImageDraw.Draw(img)
    c = tuple(colour) + (255,)
    d.ellipse((cx - 3 * k, top, cx + 3 * k, top + 6 * k), fill=c)
    d.polygon([(cx - 2.5 * k, top + 7 * k), (cx + 2.5 * k, top + 7 * k), (cx + 6 * k, top + 21 * k), (cx - 6 * k, top + 21 * k)], fill=c)
    d.rectangle((cx - 3 * k, top + 21 * k, cx - 1 * k, top + 30 * k), fill=c)
    d.rectangle((cx + 1 * k, top + 21 * k, cx + 3 * k, top + 30 * k), fill=c)


# ======================================================================== sign faces (drawn at the plate's aspect)

def exit_face(seed):
    img = plate(96, 56, (238, 240, 234), seed, 2, 2)
    green = (20, 150, 72)
    text(img, "EXIT", (6, 6, 90, 42), green, 34, stroke=1)
    d = ImageDraw.Draw(img)
    d.polygon([(70, 46), (84, 46), (84, 43), (90, 48), (84, 53), (84, 50), (70, 50)], fill=green + (255,))
    d.polygon([(26, 46), (12, 46), (12, 43), (6, 48), (12, 53), (12, 50), (26, 50)], fill=green + (255,))
    frame(img, (196, 200, 196), 2)
    return img


def restroom_face(kind, seed):
    img = plate(64, 64, (40, 66, 120) if kind == "men" else (138, 40, 62), seed, 2, 2)
    white = (240, 242, 244)
    (man if kind == "men" else woman)(img, 32, 6, 1.6, white)
    frame(img, (200, 204, 210), 2)
    M.bevel(img, None, 1, 0.2)
    return img


def floor_face(n, seed):
    """A stairwell's floor number, the way they are painted on the landing wall: a big black numeral on a yellow panel."""
    img = plate(64, 72, (226, 190, 62), seed, 3, 4)
    text(img, str(n), (8, 4, 56, 52), (24, 24, 26), 46, stroke=1)
    text(img, "FLOOR", (6, 54, 58, 68), (24, 24, 26), 11)
    rng = random.Random(seed)
    for _ in range(40):
        M.touch(img, rng.randrange(64), rng.randrange(72), rng.uniform(-0.12, 0.05))
    return img


def directory_face(n, seed):
    """A floor directory by a stairwell door: the floor, which way the stairs go, the way out, and how the room numbers read."""
    img = plate(72, 72, (52, 56, 62), seed, 2, 2)
    white, amber = (236, 238, 240), (232, 186, 70)
    text(img, f"FLOOR {n}", (6, 4, 66, 22), white, 16, stroke=0)
    for x in range(6, 66):
        img.putpixel((x, 25), M.rgba(white))
    tri(img, 14, 34, 5, True, amber)
    text(img, "STAIRS UP", (24, 28, 68, 40), white, 9)
    tri(img, 14, 48, 5, False, amber)
    text(img, "STAIRS DOWN", (24, 42, 68, 54), white, 9)
    text(img, "EXIT  FLOOR 1" if n > 1 else "EXIT  THIS FLOOR", (6, 57, 66, 68), (126, 214, 150), 9)
    frame(img, (150, 154, 160), 2)
    return img


def notice_face(seed):
    """A cork notice board two blocks wide in an aluminium frame: sheets pinned up, curled, some torn away (128 x 56)."""
    w, h = 128, 56
    img = plate(w, h, (176, 132, 84), seed, 6, 6)
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(11):
        pw, ph = rng.randint(12, 22), rng.randint(14, 22)
        x, y = rng.randint(5, w - pw - 5), rng.randint(5, h - ph - 5)
        paper = rng.choice([(240, 238, 228), (236, 230, 196), (214, 228, 238), (238, 214, 214), (226, 236, 210)])
        d.rectangle((x, y, x + pw, y + ph), fill=paper + (255,))
        for ly in range(y + 4, y + ph - 2, 3):
            d.line((x + 2, ly, x + pw - rng.randint(2, 8), ly), fill=(130, 130, 140, 255))
        pin = rng.choice([(200, 40, 40), (40, 90, 200), (230, 200, 40), (40, 160, 70)])
        d.rectangle((x + pw // 2 - 1, y + 1, x + pw // 2, y + 2), fill=pin + (255,))
    frame(img, (182, 186, 190), 3)
    return img


def poster_face(kind, seed):
    rng = random.Random(seed)
    if kind == "run":
        img = plate(48, 64, (236, 232, 218), seed, 2, 2)
        d = ImageDraw.Draw(img)
        d.ellipse((8, 6, 40, 38), outline=(196, 40, 40, 255), width=4)
        man(img, 24, 10, 0.8, (40, 40, 44))
        d.line((12, 34, 36, 10), fill=(196, 40, 40, 255), width=4)
        text(img, "NO RUNNING", (3, 42, 45, 50), (40, 40, 44), 8)
        text(img, "IN THE HALLS", (3, 51, 45, 59), (40, 40, 44), 8)
    elif kind == "fire":
        img = plate(48, 64, (244, 244, 240), seed, 2, 2)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, 47, 10), fill=(196, 40, 40, 255))
        text(img, "FIRE EXIT PLAN", (2, 1, 46, 10), (250, 250, 250), 7)
        # A floor plan: rooms either side of a corridor, the way out in green
        for k in range(4):
            d.rectangle((5 + k * 10, 15, 13 + k * 10, 27), outline=(70, 70, 76, 255))
            d.rectangle((5 + k * 10, 35, 13 + k * 10, 47), outline=(70, 70, 76, 255))
        d.line((5, 31, 44, 31), fill=(30, 150, 70, 255), width=2)
        d.polygon([(44, 27), (47, 31), (44, 35)], fill=(30, 150, 70, 255))
        d.ellipse((18, 28, 23, 33), fill=(200, 40, 40, 255))
        text(img, "YOU ARE HERE", (3, 51, 45, 59), (60, 60, 64), 7)
    elif kind == "hands":
        img = plate(48, 64, (226, 238, 244), seed, 2, 2)
        d = ImageDraw.Draw(img)
        for k in range(6):
            x, y = rng.randint(10, 34), rng.randint(8, 30)
            d.ellipse((x, y, x + 5, y + 5), outline=(90, 150, 200, 255))
        d.rounded_rectangle((12, 20, 36, 38), 6, fill=(232, 196, 166, 255))
        text(img, "WASH YOUR", (3, 42, 45, 50), (30, 70, 120), 8)
        text(img, "HANDS", (3, 51, 45, 59), (30, 70, 120), 8)
    else:  # quiet
        img = plate(48, 64, (40, 54, 92), seed, 2, 2)
        d = ImageDraw.Draw(img)
        d.ellipse((14, 8, 34, 28), fill=(232, 210, 170, 255))
        d.rectangle((23, 12, 25, 26), fill=(40, 54, 92, 255))
        text(img, "QUIET", (3, 36, 45, 48), (240, 236, 220), 11)
        text(img, "PLEASE", (3, 50, 45, 59), (240, 236, 220), 8)
    M.bevel(img, None, 1, 0.12)
    return img


def hose_face(seed):
    """The glazed door of a fire hose cabinet: a red frame, the reel of red hose behind the glass, FIRE HOSE across the top."""
    img = plate(48, 64, (180, 30, 30), seed, 3, 3)
    d = ImageDraw.Draw(img)
    d.rectangle((5, 14, 42, 55), fill=(150, 168, 176, 255))
    d.ellipse((10, 18, 37, 45), fill=(170, 28, 28, 255))
    d.ellipse((17, 25, 30, 38), fill=(120, 130, 136, 255))
    for k in range(4):
        d.arc((10 + k, 18 + k, 37 - k, 45 - k), 0, 360, fill=(140, 20, 20, 255))
    d.line((6, 15, 18, 52), fill=(220, 236, 240, 255), width=1)
    text(img, "FIRE HOSE", (3, 2, 45, 12), (250, 246, 240), 8)
    return img


def mirror_face(seed):
    img = plate(64, 48, (178, 194, 200), seed, 2, 6)
    d = ImageDraw.Draw(img)
    for k in range(3):
        d.line((10 + k * 16, 44, 24 + k * 16, 4), fill=(214, 226, 230, 255), width=3)
    frame(img, (196, 198, 200), 2)
    return img


def meg_face(seed):
    """The M.E.G.'s sign on Marshall David's top floor, two blocks wide (128 x 48): the M.E.G.'s blue on white, a stencil
    feel, like the placards it puts up at thresholds."""
    w, h = 128, 48
    img = plate(w, h, (236, 236, 230), seed, 3, 3)
    d = ImageDraw.Draw(img)
    blue = (28, 58, 120)
    d.rectangle((0, 0, w - 1, 20), fill=blue + (255,))
    text(img, "M.E.G. OUTPOST", (6, 2, w - 6, 19), (240, 240, 236), 15, stroke=0)
    text(img, "AUTHORIZED PERSONNEL ONLY", (6, 23, w - 6, 33), (30, 30, 34), 9)
    text(img, "VISITORS REPORT TO FLOOR BELOW", (6, 35, w - 6, 45), (150, 40, 36), 8)
    frame(img, (160, 162, 166), 2)
    rng = random.Random(seed)
    for _ in range(60):
        M.touch(img, rng.randrange(w), rng.randrange(h), rng.uniform(-0.1, 0.02))
    return img


def cool_face(seed):
    """COOL MART CO. over J. Barry's warehouse doors (the lore's trader), three blocks wide (192 x 56)."""
    w, h = 192, 56
    img = plate(w, h, (30, 84, 156), seed, 3, 4)
    white = (244, 246, 248)
    text(img, "COOL MART CO.", (12, 6, w - 12, 36), white, 26, stroke=1)
    text(img, "WAREHOUSE  -  TRADE  -  SUPPLIES", (12, 38, w - 12, 50), (196, 226, 250), 9)
    frame(img, (210, 214, 220), 3)
    rng = random.Random(seed)
    for _ in range(18):
        x = rng.randrange(6, w - 6)
        for k in range(rng.randint(4, 10)):
            M.touch(img, x, 40 + k if 40 + k < h - 3 else h - 4, -0.08)
    return img


def bnum_face(n, seed):
    img = plate(48, 64, (54, 56, 60), seed, 2, 2)
    text(img, str(n), (4, 4, 44, 60), (238, 238, 232), 52, stroke=1)
    return img


def clock_dial(seed):
    """A tower clock's dial three blocks across (192 x 192): white enamel, black Roman-less batons, the hands stopped at
    eight minutes to four (the level has no day or night to keep)."""
    n = 192
    img = plate(n, n, (196, 192, 180), seed, 3, 4)  # the stone round the dial
    d = ImageDraw.Draw(img)
    c = n / 2
    d.ellipse((6, 6, n - 6, n - 6), fill=(30, 32, 36, 255))
    d.ellipse((12, 12, n - 12, n - 12), fill=(240, 238, 228, 255))
    for k in range(60):
        a = k * math.pi / 30
        r0 = 78 if k % 5 == 0 else 82
        x0, y0 = c + r0 * math.sin(a), c - r0 * math.cos(a)
        x1, y1 = c + 86 * math.sin(a), c - 86 * math.cos(a)
        d.line((x0, y0, x1, y1), fill=(30, 30, 34, 255), width=5 if k % 5 == 0 else 2)
    for ang, length, width in ((((3 + 52 / 60) / 12) * 2 * math.pi, 50, 8), ((52 / 60) * 2 * math.pi, 72, 5)):
        d.line((c, c, c + length * math.sin(ang), c - length * math.cos(ang)), fill=(24, 24, 28, 255), width=width)
    d.ellipse((c - 6, c - 6, c + 6, c + 6), fill=(24, 24, 28, 255))
    return img


def wallclock_face(seed):
    n = 64
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((1, 1, n - 2, n - 2), fill=(36, 38, 44, 255))
    d.ellipse((5, 5, n - 6, n - 6), fill=(246, 246, 240, 255))
    c = n / 2
    for k in range(12):
        a = k * math.pi / 6
        d.line((c + 22 * math.sin(a), c - 22 * math.cos(a), c + 26 * math.sin(a), c - 26 * math.cos(a)), fill=(30, 30, 34, 255), width=2)
    d.line((c, c, c + 14 * math.sin(2.1), c - 14 * math.cos(2.1)), fill=(20, 20, 24, 255), width=3)
    d.line((c, c, c + 22 * math.sin(5.2), c - 22 * math.cos(5.2)), fill=(20, 20, 24, 255), width=2)
    d.line((c, c, c + 23 * math.sin(3.4), c - 23 * math.cos(3.4)), fill=(200, 40, 40, 255), width=1)
    bg = plate(n, n, (40, 42, 48), seed, 2, 2)
    bg.alpha_composite(img)
    return bg


def door_face(part, seed):
    """A grey steel door (a roof door or a store's), with a push bar (lower) and a small wired window (upper)."""
    img = plate(48, 64, (126, 132, 138), seed, 3, 3)
    d = ImageDraw.Draw(img)
    if part == "lo":
        d.rectangle((6, 18, 42, 24), fill=(70, 74, 80, 255))
        d.rectangle((8, 19, 40, 22), fill=(180, 184, 188, 255))
    else:
        d.rectangle((14, 10, 34, 40), fill=(60, 70, 76, 255))
        d.rectangle((16, 12, 32, 38), fill=(150, 170, 178, 255))
        for k in range(16, 33, 4):
            d.line((k, 12, k, 38), fill=(110, 116, 120, 255))
        for k in range(12, 39, 4):
            d.line((16, k, 32, k), fill=(110, 116, 120, 255))
    frame(img, (90, 94, 100), 2)
    return img


def lift_face(part, leaf, seed):
    """A lift's brushed steel doors (two blocks wide, two high: 128 x 128 in all): the seam between the leaves, the frame;
    above, the floor indicator, unlit."""
    w, h = 128, 128
    img = M.noise_hv((176, 180, 184), 2, seed, (w, h), 3, (16, 8), hue=0.3)
    p = img.load()
    rng = random.Random(seed)
    for y in range(h):
        streak = rng.uniform(-3, 3)
        for x in range(w):
            p[x, y] = M.rgba(M.lift(p[x, y][:3], streak * 0.5))
    d = ImageDraw.Draw(img)
    d.line((64, 20, 64, h), fill=(60, 62, 66, 255), width=2)
    d.rectangle((0, 0, w - 1, 18), fill=(80, 84, 88, 255))
    d.rectangle((50, 4, 78, 14), fill=(20, 18, 16, 255))
    frame(img, (110, 114, 118), 4)
    quarter = img.crop(((0 if leaf == "l" else 64), (64 if part == "lo" else 0), (64 if leaf == "l" else 128), (128 if part == "lo" else 64)))
    return quarter


def leaf_face(part, seed):
    """A classroom door standing open against the corridor wall: wood veneer, a narrow vision panel (upper), a kick plate (lower)."""
    img = plate(40, 64, (164, 120, 74), seed, 4, 4)
    d = ImageDraw.Draw(img)
    for x in range(0, 40, 3):
        d.line((x, 0, x, 63), fill=(150, 108, 66, 255))
    if part == "lo":
        d.rectangle((2, 50, 37, 62), fill=(170, 172, 176, 255))
        d.rectangle((30, 2, 35, 6), fill=(190, 192, 196, 255))
    else:
        d.rectangle((14, 8, 24, 52), fill=(60, 64, 70, 255))
        d.rectangle((15, 9, 23, 51), fill=(170, 190, 200, 255))
    frame(img, (120, 88, 56), 2)
    return img


def alarm_face(seed):
    img = plate(32, 32, (196, 30, 30), seed, 3, 3)
    d = ImageDraw.Draw(img)
    d.ellipse((4, 4, 28, 28), fill=(210, 36, 32, 255), outline=(120, 16, 16, 255))
    d.ellipse((13, 13, 19, 19), fill=(60, 60, 64, 255))
    return img


def ext_face(seed):
    img = plate(32, 64, (200, 32, 30), seed, 3, 3)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 31, 8), fill=(40, 40, 44, 255))
    d.rectangle((6, 22, 26, 40), fill=(240, 236, 226, 255))
    text(img, "CO2", (7, 24, 25, 38), (30, 30, 34), 8)
    return img


def edge(seed, colour):
    return M.noise_hv(colour, 2, seed, (32, 32), 2, (16, 8), hue=0.3)


# ======================================================================== boards on posts

BOARDS = {
    # kind: (lines, panel colour, letter colour, stencil?)
    "md": (["MARSHALL DAVID", "CAMPUS"], (232, 228, 214), (28, 58, 120)),
    "barry": (["J. BARRY", "CAMPUS"], (232, 228, 214), (28, 58, 120)),
    "turner": (["J. TURNER", "CAMPUS"], (232, 228, 214), (28, 58, 120)),
    "sunfire": (["BASE SUNFIRE", "B. COLONISTS"], (170, 132, 88), (250, 214, 120)),
    "ember": (["BASE EMBERWATCH", "PARTY CRASHERS"], (150, 116, 80), (240, 236, 226)),
    "blackcross": (["BASE BLACKCROSS", "B.R.C. AID POST"], (226, 222, 210), (30, 30, 32)),
}
BOARD_KINDS = ["map"] + list(BOARDS)


def board_face(kind, seed):
    """A board two blocks wide, two high (128 x 128; the lower half's bottom third is the posts' gap, drawn on the shape)."""
    n = 128
    rng = random.Random(seed)
    if kind == "map":
        img = plate(n, n, (238, 236, 228), seed, 2, 2)
        d = ImageDraw.Draw(img)
        d.rectangle((0, 0, n - 1, 16), fill=(30, 70, 60, 255))
        text(img, "CAMPUS MAP", (6, 2, n - 6, 15), (240, 240, 236), 12)
        # Lawns, a fence round, paths, the buildings as grey blocks with their numbers, YOU ARE HERE
        d.rectangle((6, 20, n - 7, n - 7), fill=(178, 210, 150, 255), outline=(120, 120, 120, 255), width=2)
        d.rectangle((14, 28, 70, 84), fill=(150, 150, 156, 255))
        d.rectangle((30, 44, 54, 68), fill=(150, 196, 120, 255))
        d.line((62, 120, 62, 86), fill=(226, 226, 220, 255), width=4)
        d.line((14, 96, 114, 96), fill=(226, 226, 220, 255), width=4)
        d.rectangle((80, 28, 112, 52), fill=(150, 150, 156, 255))
        d.rectangle((80, 60, 112, 88), fill=(150, 150, 156, 255))
        d.rectangle((14, 102, 50, 116), fill=(150, 150, 156, 255))
        for (x0, y0, x1, y1), s in (((14, 28, 30, 44), "1"), ((80, 28, 112, 52), "2"), ((80, 60, 112, 88), "3"), ((14, 102, 50, 116), "4")):
            text(img, s, (x0 + 2, y0 + 2, x0 + 14, y0 + 14), (30, 30, 34), 10)
        d.ellipse((57, 110, 67, 120), fill=(210, 40, 40, 255))
        text(img, "YOU ARE HERE", (70, 108, 124, 120), (150, 30, 30), 7)
        frame(img, (60, 64, 70), 3)
        return img
    lines, panel, ink = BOARDS[kind]
    img = plate(n, n, panel, seed, 5, 6)
    d = ImageDraw.Draw(img)
    # Plywood or painted boards: horizontal planks
    for y in range(0, n, 21):
        d.line((0, y, n, y), fill=M.rgba(M.lift(panel, -26)))
    text(img, lines[0], (6, 18, n - 6, 54), ink, 24, stroke=1)
    text(img, lines[1], (10, 58, n - 10, 80), ink, 13)
    if kind in ("md", "barry", "turner"):
        text(img, "M.E.G.", (40, 88, 88, 104), (150, 40, 36), 11)
    else:
        text(img, "ABANDONED", (24, 88, 104, 104), (150, 40, 36), 11)
        for _ in range(26):
            x, y = rng.randrange(n), rng.randrange(n)
            d.ellipse((x, y, x + rng.randint(2, 6), y + rng.randint(2, 5)), fill=M.rgba(M.lift(panel, -40)))
    frame(img, tuple(M.lift(panel, -50)), 3)
    return img


# ======================================================================== shapes

def sign_shape(name, x0, y0, x1, y1, depth, face_key, edge_key, glow=0):
    """A plate against the wall to the south (the block faces north): its face drawn whole on the front."""
    els = [box("Face", (x0, y0, 16 - depth), (x1, y1, 16), {"north": face_key, "side": edge_key, "up": edge_key, "down": edge_key},
               faces=("north", "east", "west", "up", "down"), uv=None, glow=glow)]
    els[0]["faces"]["north"]["uv"] = list(FULL)
    return G.shape(name, els)


# kind: (x0, y0, x1, y1, depth, face texture, edge texture, glow)
SIGNS = {}


def sign_kinds():
    k = {}
    k["exit"] = (2, 4, 14, 11, 2.5, "sign-exit", "sign-edge-white", 90)
    k["men"] = (4.5, 3, 11.5, 10, 0.4, "sign-men", "sign-edge-steel", 0)
    k["women"] = (4.5, 3, 11.5, 10, 0.4, "sign-women", "sign-edge-steel", 0)
    for n in range(1, 9):
        k[f"floor{n}"] = (3, 1, 13, 14, 0.2, f"sign-floor{n}", "sign-edge-yellow", 0)
        k[f"dir{n}"] = (2, 2, 14, 14, 0.5, f"sign-dir{n}", "sign-edge-steel", 0)
    k["notice-l"] = (0, 3, 15, 14, 0.8, "sign-notice-l", "sign-edge-steel", 0)
    k["notice-r"] = (1, 3, 16, 14, 0.8, "sign-notice-r", "sign-edge-steel", 0)
    for p in ("run", "fire", "hands", "quiet"):
        k["poster-" + p] = (4, 1, 12, 12, 0.15, "sign-poster-" + p, "sign-edge-white", 0)
    k["hose"] = (3, 0, 13, 13, 3, "sign-hose", "sign-edge-red", 0)
    k["ext"] = (6, 1, 10, 9, 2.5, "sign-ext", "sign-edge-red", 0)
    k["mirror"] = (1, 2, 15, 12, 0.3, "sign-mirror", "sign-edge-steel", 0)
    k["meg-l"] = (0, 4, 15, 12, 0.6, "sign-meg-l", "sign-edge-white", 0)
    k["meg-r"] = (1, 4, 16, 12, 0.6, "sign-meg-r", "sign-edge-white", 0)
    k["cool-l"] = (0, 2, 15, 13, 1.5, "sign-cool-l", "sign-edge-blue", 0)
    k["cool-m"] = (0, 2, 16, 13, 1.5, "sign-cool-m", "sign-edge-blue", 0)
    k["cool-r"] = (1, 2, 16, 13, 1.5, "sign-cool-r", "sign-edge-blue", 0)
    for n in range(1, 10):
        k[f"bnum{n}"] = (4, 1, 12, 15, 0.5, f"sign-bnum{n}", "sign-edge-dark", 0)
    for i in range(9):
        k[f"clock{i}"] = (0, 0, 16, 16, 0.8, f"sign-clock{i}", "sign-edge-stone", 0)
    k["wallclock"] = (5, 3, 11, 9, 1, "sign-wallclock", "sign-edge-dark", 0)
    k["alarm"] = (5.5, 6, 10.5, 11, 2.5, "sign-alarm", "sign-edge-red", 0)
    k["door-lo"] = (2, 0, 14, 16, 1, "sign-door-lo", "sign-edge-steel", 0)
    k["door-hi"] = (2, 0, 14, 13, 1, "sign-door-hi", "sign-edge-steel", 0)
    for part in ("lo", "hi"):
        for leaf in ("l", "r"):
            x0, x1 = (0, 15) if leaf == "l" else (1, 16)
            k[f"lift{part}-{leaf}"] = (x0, 0, x1, 16, 0.6, f"sign-lift{part}-{leaf}", "sign-edge-steel", 0)
    k["leaf-lo"] = (0.5, 0, 12.5, 16, 1.5, "sign-leaf-lo", "sign-edge-wood", 0)
    k["leaf-hi"] = (0.5, 0, 12.5, 15, 1.5, "sign-leaf-hi", "sign-edge-wood", 0)
    return k


def textures():
    s = G.save
    s(square(exit_face(6001)), "sign-exit")
    s(square(restroom_face("men", 6002)), "sign-men")
    s(square(restroom_face("women", 6003)), "sign-women")
    for n in range(1, 9):
        s(square(floor_face(n, 6010 + n)), f"sign-floor{n}")
        s(square(directory_face(n, 6020 + n)), f"sign-dir{n}")
    nb = notice_face(6030)
    s(square(nb.crop((0, 0, 64, 56))), "sign-notice-l")
    s(square(nb.crop((64, 0, 128, 56))), "sign-notice-r")
    for i, p in enumerate(("run", "fire", "hands", "quiet")):
        s(square(poster_face(p, 6040 + i)), "sign-poster-" + p)
    s(square(hose_face(6050)), "sign-hose")
    s(square(ext_face(6051)), "sign-ext")
    s(square(mirror_face(6052)), "sign-mirror")
    mg = meg_face(6060)
    s(square(mg.crop((0, 0, 64, 48))), "sign-meg-l")
    s(square(mg.crop((64, 0, 128, 48))), "sign-meg-r")
    cm = cool_face(6070)
    for i, part in enumerate("lmr"):
        s(square(cm.crop((i * 64, 0, (i + 1) * 64, 56))), f"sign-cool-{part}")
    for n in range(1, 10):
        s(square(bnum_face(n, 6080 + n)), f"sign-bnum{n}")
    dial = clock_dial(6090)
    for i in range(9):
        r, c = divmod(i, 3)
        s(dial.crop((c * 64, r * 64, (c + 1) * 64, (r + 1) * 64)), f"sign-clock{i}")
    s(wallclock_face(6091), "sign-wallclock")
    s(square(alarm_face(6092)), "sign-alarm")
    s(square(door_face("lo", 6093)), "sign-door-lo")
    s(square(door_face("hi", 6094)), "sign-door-hi")
    for part in ("lo", "hi"):
        for leaf in ("l", "r"):
            s(lift_face(part, leaf, 6095), f"sign-lift{part}-{leaf}")
    s(square(leaf_face("lo", 6097)), "sign-leaf-lo")
    s(square(leaf_face("hi", 6098)), "sign-leaf-hi")
    for name, colour in (("white", (232, 232, 228)), ("steel", (150, 154, 160)), ("yellow", (220, 186, 70)), ("red", (170, 30, 30)),
                         ("blue", (40, 70, 130)), ("dark", (50, 52, 56)), ("stone", (190, 186, 174)), ("wood", (140, 100, 62))):
        s(edge(6100 + len(name), colour), "sign-edge-" + name)
    # Boards on posts
    for i, kind in enumerate(BOARD_KINDS):
        img = board_face(kind, 6200 + i * 3)
        for part, x in (("l", 0), ("r", 64)):
            for half, y in (("upper", 0), ("lower", 64)):
                s(img.crop((x, y, x + 64, y + 64)), f"board-{kind}-{part}-{half}")
    s(M.noise_hv((92, 96, 100), 3, 6300, (32, 32), 3, (16, 8)), "post-steel")
    s(M.noise_hv((140, 108, 70), 5, 6301, (32, 32), 5, (16, 8)), "post-wood")
    # Props
    s(M.noise_hv((240, 240, 236), 2, 6310, (32, 32), 2, (16, 8)), "porcelain")
    s(M.noise_hv((152, 160, 150), 3, 6311, (32, 32), 3, (16, 8)), "partition")
    s(M.noise_hv((84, 88, 92), 3, 6312, (32, 32), 3, (16, 8)), "hood-dark")
    s(M.noise_hv((210, 212, 214), 2, 6313, (32, 32), 2, (16, 8)), "hood-steel")
    glass = Image.new("RGBA", (32, 32), (190, 214, 222, 110))
    s(glass, "hood-glass")
    s(M.noise_hv((196, 200, 204), 3, 6314, (32, 32), 3, (16, 8)), "alu")
    s(M.noise_hv((242, 242, 240), 1, 6315, (32, 32), 1, (16, 8)), "goal-white")
    net = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    pn = net.load()
    for y in range(32):
        for x in range(32):
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                pn[x, y] = (236, 236, 232, 230)
    s(net, "goal-net")
    s(M.noise_hv((234, 234, 230), 2, 6316, (32, 32), 2, (16, 8)), "pole")
    flag = M.noise_hv((40, 84, 160), 3, 6317, (32, 32), 4, (16, 8))
    fd = ImageDraw.Draw(flag)
    fd.ellipse((10, 10, 22, 22), outline=(240, 240, 236, 255), width=2)
    fd.line((16, 8, 16, 24), fill=(240, 240, 236, 255), width=2)
    s(flag, "flag")
    s(M.noise_hv((198, 192, 178), 3, 6318, (32, 32), 4, (16, 8)), "fountain-stone")
    water = M.noise_hv((92, 150, 190), 4, 6319, (32, 32), 8, (16, 8))
    wp = water.load()
    for y in range(32):
        for x in range(32):
            r, g, b, _ = wp[x, y]
            wp[x, y] = (r, g, b, 200)
    s(water, "fountain-water")
    # The air handler: louvres on the sides, fan grilles on top; the roof vent
    louvre = M.noise_hv((176, 180, 178), 2, 6320, (32, 32), 2, (16, 8))
    d = ImageDraw.Draw(louvre)
    for y in range(3, 30, 3):
        d.line((2, y, 29, y), fill=(110, 114, 112, 255))
    frame(louvre, (140, 144, 142), 1)
    s(louvre, "hvac-side")
    top = M.noise_hv((170, 174, 172), 2, 6321, (32, 32), 2, (16, 8))
    d = ImageDraw.Draw(top)
    d.ellipse((4, 4, 27, 27), fill=(60, 62, 64, 255))
    for k in range(4, 28, 3):
        d.line((4, k, 27, k), fill=(150, 154, 152, 255))
    d.ellipse((13, 13, 18, 18), fill=(120, 124, 122, 255))
    frame(top, (140, 144, 142), 1)
    s(top, "hvac-top")
    # A courtyard's glazed roof: pale glass, white glazing bars every half block
    sky = Image.new("RGBA", (32, 32), (214, 232, 236, 70))
    d = ImageDraw.Draw(sky)
    for k in (0, 15, 16, 31):
        d.line((k, 0, k, 31), fill=(236, 238, 238, 255))
        d.line((0, k, 31, k), fill=(236, 238, 238, 255))
    s(sky, "skylight")
    # The running track: red rubber, white lane lines
    for kind in ("plain", "linens", "linewe"):
        img = M.noise_hv((156, 70, 54), 5, 6330, (32, 32), 5, (16, 8))
        d = ImageDraw.Draw(img)
        if kind == "linens":
            d.rectangle((15, 0, 16, 31), fill=(236, 232, 226, 255))
        if kind == "linewe":
            d.rectangle((0, 15, 31, 16), fill=(236, 232, 226, 255))
        s(img, "track-" + kind)
    for kind in ("linens", "linewe"):
        img = T.turf_top(False, 5600)
        d = ImageDraw.Draw(img)
        if kind == "linens":
            d.rectangle((14, 0, 17, 31), fill=(236, 238, 230, 255))
        else:
            d.rectangle((0, 14, 31, 17), fill=(236, 238, 230, 255))
        s(img, "turf-" + kind)


def oriented(code, groups, shapes, comment, material, sounds, coll, sel=None, creative=None, extra=None, resistance=2):
    """A json block by side, its shape turned for each (shapes: {prefix: shape}; coll: a box in the north-facing frame or None)."""
    shape_by, cb, sb = {}, {}, {}
    for prefix, shp in shapes.items():
        for s in SIDES:
            shape_by[f"{prefix}-{s}"] = {"base": shp, "rotateY": ROTATE[s]}
            if coll:
                cb[f"{prefix}-{s}"] = G.cuboid(coll(prefix), ROTATE[s])
            sbox = (sel or coll)
            if sbox:
                sb[f"{prefix}-{s}"] = G.cuboid(sbox(prefix), ROTATE[s])
    ex = dict(extra or {})
    if not coll:
        ex["collisionbox"] = None
    G.json_block(code, groups, shape_by, comment, material, sounds, cb or None, sb or None,
                 creative=creative or (next(iter(shapes)) + "-north",), extra=ex, resistance=resistance)


def blocktypes():
    global SIGNS
    SIGNS = sign_kinds()
    shapes = {}
    for kind, (x0, y0, x1, y1, depth, face, edge_, glow) in SIGNS.items():
        shapes[f"l52-sign-{kind}"] = sign_shape(f"l52-sign-{kind}", x0, y0, x1, y1, depth, face, edge_, glow)
    sel = {f"l52-sign-{k}": (v[0] / 16, v[1] / 16, 1 - v[4] / 16 - 0.01, v[2] / 16, v[3] / 16, 1) for k, v in SIGNS.items()}
    shape_by, sb = {}, {}
    for kind in SIGNS:
        for s in SIDES:
            shape_by[f"l52-sign-{kind}-{s}"] = {"base": shapes[f"l52-sign-{kind}"], "rotateY": ROTATE[s]}
            sb[f"l52-sign-{kind}-{s}"] = G.cuboid(sel[f"l52-sign-{kind}"], ROTATE[s])
    G.json_block("l52-sign", [G.group("kind", list(SIGNS)), G.group("side", SIDES)], shape_by,
                 "Level 52: a plate or fitting hung on the wall behind its block (side: the way it faces): EXIT, the restroom pictograms, a "
                 "stairwell's floor number and directory, a notice board (two halves), posters, a fire hose cabinet, an extinguisher, a mirror, "
                 "the M.E.G.'s outpost sign (two halves), COOL MART CO. (three parts), a building's number on its canopy, a tower clock's dial "
                 "(nine parts), a wall clock, an alarm bell, a steel door's leaf, a lift's doors (four quarters), a classroom door standing open",
                 "Metal", G.METAL, None, sb, creative=("*-exit-north", "*-men-north", "*-women-north", "*-notice-l-north", "*-hose-north"),
                 resistance=1, extra={"collisionbox": None, "lightHsvByType": {"*-exit-*": [7, 4, 6]}})

    # A toilet stall: the pan against the wall behind, the partition on its left (-X seen from in front is the right... the
    # partition stands along x = 15-16, which is the stall's left as seen from in front)
    por, par = "porcelain", "partition"
    lower = [box("Pan", (4.5, 0, 6), (11.5, 6, 13), por), box("Seat", (4, 6, 5.5), (12, 6.8, 13), por),
             box("Cistern", (4, 4, 13), (12, 12, 16), por), box("Wall", (15, 1, 0), (16, 16, 16), par),
             box("Foot", (14.6, 0, 1), (16, 1, 2.4), "alu")]
    upper = [box("Wall", (15, 0, 0), (16, 12, 16), par), box("Rail", (14.6, 12, 0), (16, 12.8, 16), "alu")]
    st = {"l52-stall-lower": G.shape("l52-stall-lower", lower), "l52-stall-upper": G.shape("l52-stall-upper", upper)}
    oriented("l52-stall", [G.group("part", ["lower", "upper"]), G.group("side", SIDES)],
             {"l52-stall-lower": st["l52-stall-lower"], "l52-stall-upper": st["l52-stall-upper"]},
             "Level 52: a toilet stall facing the way of its side: the pan and cistern against the wall behind, the partition on its left "
             "(lower), the partition's top and rail (upper)", "Stone", G.STONE,
             lambda p: (0.25, 0, 0.35, 0.75, 0.45, 1) if p.endswith("lower") else (0.9, 0, 0, 1, 0.8, 1))

    # A fume hood
    hl = [box("Cabinet", (0.5, 0, 4), (15.5, 13, 16), "hood-dark"), box("Top", (0, 13, 3), (16, 16, 16), "hood-steel")]
    hu = [box("Back", (0.5, 0, 14), (15.5, 16, 16), "hood-steel"), box("SideL", (0.5, 0, 4), (1.5, 16, 14), "hood-steel"),
          box("SideR", (14.5, 0, 4), (15.5, 16, 14), "hood-steel"), box("Sash", (1.5, 4, 4.5), (14.5, 14, 5), "hood-glass", faces=("north", "south")),
          box("Head", (0.5, 14, 3.5), (15.5, 16, 14), "hood-dark")]
    oriented("l52-fumehood", [G.group("part", ["lower", "upper"]), G.group("side", SIDES)],
             {"l52-fumehood-lower": G.shape("l52-fumehood-lower", hl), "l52-fumehood-upper": G.shape("l52-fumehood-upper", hu)},
             "Level 52: a lab's fume hood: the cabinet and worktop (lower), the glass sash and the hood's casing (upper), its back to the wall",
             "Metal", G.METAL, lambda p: (0, 0, 0.2, 1, 1, 1), extra={"renderpass": "Transparent"})

    # A row of bleachers: the seat plank at the back, the foot plank in front, the frame
    bl = [box("Seat", (0, 12, 9), (16, 13.5, 15), "alu"), box("Riser", (0, 0, 15), (16, 13.5, 16), "alu"),
          box("Foot", (0, 5, 1), (16, 6, 8), "alu"), box("LegL", (1, 0, 2), (2, 12, 3), "hood-dark"), box("LegR", (14, 0, 2), (15, 12, 3), "hood-dark"),
          box("BraceL", (1, 5, 3), (2, 6, 15), "hood-dark"), box("BraceR", (14, 5, 3), (15, 6, 15), "hood-dark")]
    oriented("l52-bleacher", [G.group("side", SIDES)], {"l52-bleacher": G.shape("l52-bleacher", bl)},
             "Level 52: one row of aluminium bleachers facing the way of its side (the seat at the back, the foot plank in front); rows "
             "stacked a block up and a block back make a stand", "Metal", G.METAL, lambda p: (0, 0, 0, 1, 0.85, 1))

    # A football goal, three blocks wide and two high, the net behind
    gw, net = "goal-white", "goal-net"
    goal = {}
    for part in ("l", "m", "r"):
        for half in ("lower", "upper"):
            els = []
            if half == "upper":
                els.append(box("Bar", (0, 13, 1), (16, 15, 3), gw))
                els.append(box("NetTop", (0, 14.5, 3), (16, 14.6, 16), net, faces=("up", "down"), uv=FULL))
            els.append(box("NetBack", (0, 0, 15.9), (16, 15 if half == "upper" else 16, 16), net, faces=("north", "south"), uv=FULL))
            if part in ("l", "r"):
                x0 = 14 if part == "l" else 0
                els.append(box("Post", (x0, 0, 1), (x0 + 2, 16 if half == "lower" else 15, 3), gw))
                sx = 15.9 if part == "l" else 0
                els.append(box("NetSide", (sx, 0, 3), (sx + 0.1, 16 if half == "lower" else 14.5, 15.9), net, faces=("east", "west"), uv=FULL))
            goal[f"l52-goal-{part}-{half}"] = G.shape(f"l52-goal-{part}-{half}", els)
    oriented("l52-goal", [G.group("part", ["l", "m", "r"]), G.group("half", ["lower", "upper"]), G.group("side", SIDES)], goal,
             "Level 52: a football goal three blocks wide and two high, facing the way of its side: posts (l, r as seen from the pitch), "
             "the crossbar (upper), the net behind", "Metal", G.METAL, None,
             sel=lambda p: (0, 0, 0, 1, 1, 1), extra={"renderpass": "OpaqueNoCull"})

    # A flagpole: base, pole, the top with its flag flying off to the east of the pole as seen from in front
    pb = [box("Base", (5, 0, 5), (11, 3, 11), "fountain-stone"), box("Pole", (7.3, 3, 7.3), (8.7, 16, 8.7), "pole")]
    pp = [box("Pole", (7.3, 0, 7.3), (8.7, 16, 8.7), "pole")]
    pt = [box("Pole", (7.3, 0, 7.3), (8.7, 14, 8.7), "pole"), box("Ball", (7, 14, 7), (9, 16, 9), "fountain-chrome-r3"),
          box("Flag", (-6, 6, 7.9), (7.3, 13.5, 8.1), "flag", faces=("north", "south"), uv=FULL)]
    oriented("l52-flagpole", [G.group("part", ["base", "pole", "top"]), G.group("side", SIDES)],
             {"l52-flagpole-base": G.shape("l52-flagpole-base", pb), "l52-flagpole-pole": G.shape("l52-flagpole-pole", pp),
              "l52-flagpole-top": G.shape("l52-flagpole-top", pt)},
             "Level 52: a flagpole (base, pole, top with a pale blue flag that carries no name), facing the way of its side",
             "Metal", G.METAL, lambda p: (0.3, 0, 0.3, 0.7, 1, 0.7), extra={"renderpass": "OpaqueNoCull"})

    # Boards on two posts
    shapes_b = {}
    for kind in BOARD_KINDS:
        post = "post-steel" if kind in ("map", "md", "barry", "turner") else "post-wood"
        for part in ("l", "r"):
            for half in ("lower", "upper"):
                face = f"board-{kind}-{part}-{half}"
                px0, px1 = (13, 15) if part == "l" else (1, 3)
                if half == "lower":
                    els = [box("Board", (0, 0, 9), (16, 16, 11), {"north": face, "side": post}, faces=("north", "south", "up", "down"), uv=None),
                           box("Post", (px0, 0, 11), (px1, 16, 13), post)]
                else:
                    els = [box("Board", (0, 0, 9), (16, 15, 11), {"north": face, "side": post}, faces=("north", "south", "up", "down"), uv=None),
                           box("Post", (px0, 0, 11), (px1, 16, 13), post), box("Cap", (0, 15, 8.5), (16, 16, 11.5), post)]
                els[0]["faces"]["north"]["uv"] = list(FULL)
                els[0]["faces"]["south"]["texture"] = "#" + post
                if part == "l":
                    els[0]["faces"]["east"] = {"texture": "#" + post, "uv": [0, 0, 2, 16]}
                else:
                    els[0]["faces"]["west"] = {"texture": "#" + post, "uv": [0, 0, 2, 16]}
                name = f"l52-post-{kind}-{part}-{half}"
                shapes_b[name] = G.shape(name, els)
    oriented("l52-post", [G.group("kind", BOARD_KINDS), G.group("part", ["l", "r"]), G.group("half", ["lower", "upper"]), G.group("side", SIDES)],
             shapes_b,
             "Level 52: a board two blocks wide and two high on two posts, facing the way of its side (part l: its left as seen from in "
             "front): the campus map at a gap in a fence; the M.E.G.'s stencilled boards naming Marshall David, J. Barry and J. Turner; the "
             "abandoned bases' boards (Sunfire, Emberwatch, Blackcross)", "Wood", G.WOOD, lambda p: (0, 0, 0.55, 1, 1, 0.8))

    # A bike rack: three steel hoops standing across the block, their feet in a rail
    hoops = [box("Rail", (0, 0, 7), (16, 0.8, 9), "hood-dark")]
    for k, x in enumerate((2.5, 7.5, 12.5)):
        hoops += [box(f"PostA{k}", (x - 0.5, 0.8, 2), (x + 0.5, 11, 3), "pole"), box(f"PostB{k}", (x - 0.5, 0.8, 13), (x + 0.5, 11, 14), "pole"),
                  box(f"Top{k}", (x - 0.5, 11, 2), (x + 0.5, 12, 14), "pole"), box(f"FootA{k}", (x - 0.5, 0, 2), (x + 0.5, 0.8, 7), "hood-dark"),
                  box(f"FootB{k}", (x - 0.5, 0, 9), (x + 0.5, 0.8, 14), "hood-dark")]
    oriented("l52-bikerack", [G.group("side", SIDES)], {"l52-bikerack": G.shape("l52-bikerack", hoops)},
             "Level 52: a bike rack, three steel hoops on a rail (nothing locked to them)", "Metal", G.METAL, lambda p: (0.1, 0, 0.1, 0.9, 0.75, 0.9))

    # The fountain's middle and a roof vent
    jet = [box("Column", (6, 0, 6), (10, 9, 10), "fountain-stone"), box("Bowl", (3, 9, 3), (13, 11, 13), "fountain-stone"),
           box("Water", (3.5, 11, 3.5), (12.5, 11.2, 12.5), "fountain-water", faces=("up",)),
           box("Spout", (7.2, 11, 7.2), (8.8, 16, 8.8), "fountain-water")]
    G.json_block("l52-jet", [], {"*": {"base": G.shape("l52-jet", jet)}},
                 "Level 52: the middle of a courtyard fountain: a stone bowl on a column, a jet of water rising from it", "Stone", G.STONE,
                 {"*": G.cuboid((0.2, 0, 0.2, 0.8, 0.7, 0.8))}, {"*": G.cuboid((0.2, 0, 0.2, 0.8, 1, 0.8))}, creative=("*",),
                 extra={"renderpass": "Transparent"})
    vent = [box("Stem", (6, 0, 6), (10, 6, 10), "hood-steel"), box("Cap", (4, 6, 4), (12, 9, 12), "hood-steel")]
    G.json_block("l52-vent", [], {"*": {"base": G.shape("l52-vent", vent)}},
                 "Level 52: a roof vent, a steel mushroom cap on a stem", "Metal", G.METAL,
                 {"*": G.cuboid((0.25, 0, 0.25, 0.75, 0.56, 0.75))}, {"*": G.cuboid((0.25, 0, 0.25, 0.75, 0.56, 0.75))}, creative=("*",))
    # The air handler and the track
    G.cube_block("l52-hvac", [G.group("part", ["body", "top"])],
                 {"l52-hvac-body": G.faces(sides="hvac-side", up="hvac-side", down="hvac-side"),
                  "l52-hvac-top": G.faces(sides="hvac-side", up="hvac-top", down="hvac-side")},
                 "Level 52: an air-handling unit's casing on a roof (body: louvred panels; top: fan grilles on its top face)", material="Metal",
                 sounds=G.METAL)
    G.cube_block("l52-skylight", [], {"*": G.faces(all_="skylight")},
                 "Level 52: a courtyard's glazed roof (the lore's \"translucent ceiling\"): pale glass in a grid of white steel glazing bars",
                 material="Glass", sounds=G.GLASS, resistance=2,
                 extra={"lightAbsorption": 0, "renderpass": "Transparent", "sideopaque": {"all": False}, "sideao": {"all": False}})
    G.cube_block("l52-wallpatch", [], {"*": G.faces(all_="wall-blue-patch")},
                 "Level 52: J. Barry's blue corridor wall where bullet holes were filled and painted over, the paint a shade fresher in a patch")
    # An outside wall seen from both sides: the façade on every face but the inward one, which is the room's paint
    opp = {"north": "south", "south": "north", "east": "west", "west": "east"}
    ext = {}
    for f in FACADES:
        for p in PALETTES:
            for part in ("base", "dado", "upper"):
                for side in SIDES:
                    faces_ = G.faces(all_=f"facade-{f}")
                    faces_[opp[side]] = G.tex(f"wall-{p}-{part}")
                    ext[f"l52-extwall-{f}-{p}-{part}-{side}"] = faces_
    G.cube_block("l52-extwall", [G.group("facade", FACADES), G.group("paint", PALETTES), G.group("part", ["base", "dado", "upper"]), G.group("side", SIDES)],
                 ext, "Level 52: an outside wall, the façade outward (side: the way the façade faces; its other faces too) and the room's paint "
                 "on the face inward (palette, part as l52-wall)")
    G.cube_block("l52-track", [G.group("kind", ["plain", "linens", "linewe"])],
                 {f"l52-track-{k}": G.faces(sides="slab-concrete", up=f"track-{k}", down="slab-concrete") for k in ("plain", "linens", "linewe")},
                 "Level 52: a running track's red rubber, plain or with a white lane line north-south (linens) or west-east (linewe)")


def worn_hall():
    """Marshall David's corridors now (the lore: "dirt prints, cracks, rubbish"): the hall's checks, scuffed grey, shoe prints
    in dirt and a crack across."""
    img = Image.open(os.path.join(G.TEX, "tile-hall.png")).convert("RGBA")
    M.grime(img, 0.22, 6400, (96, 86, 70), (8, 4, 2), cover=0.6)
    rng = random.Random(6401)
    d = ImageDraw.Draw(img)
    for _ in range(4):
        x, y = rng.randrange(2, 26), rng.randrange(2, 24)
        d.ellipse((x, y, x + 3, y + 5), fill=(118, 106, 88, 150))
        d.ellipse((x + 4, y + 3, x + 7, y + 8), fill=(118, 106, 88, 130))
    x, y = rng.randrange(0, 10), rng.randrange(4, 28)
    for k in range(26):
        x += 1
        y += rng.choice((-1, 0, 0, 1))
        if 0 <= x < 32 and 0 <= y < 32:
            img.putpixel((x, y), (92, 86, 76, 255))
    return img


def extra_textures_for_shapes():
    # (A chrome finial borrows the fountain's chrome under its own key)
    G.save(T.fountain_chrome(5672), "fountain-chrome-r3")


def expected():
    codes = set()
    for k in sign_kinds():
        for s in SIDES:
            codes.add(f"l52-sign-{k}-{s}")
    for s in SIDES:
        for p in ("lower", "upper"):
            codes.add(f"l52-stall-{p}-{s}")
            codes.add(f"l52-fumehood-{p}-{s}")
            for part in "lmr":
                codes.add(f"l52-goal-{part}-{p}-{s}")
            for kind in BOARD_KINDS:
                for part in "lr":
                    codes.add(f"l52-post-{kind}-{part}-{p}-{s}")
        codes.add(f"l52-bleacher-{s}")
        codes.add(f"l52-bikerack-{s}")
        for part in ("base", "pole", "top"):
            codes.add(f"l52-flagpole-{part}-{s}")
    codes |= {"l52-jet", "l52-vent", "l52-hvac-body", "l52-hvac-top", "l52-skylight", "l52-wallpatch"}
    for k in ("plain", "linens", "linewe"):
        codes.add(f"l52-track-{k}")
    for k in ("linens", "linewe"):
        codes.add(f"l52-turf-{k}")
    for f in FACADES:
        for p in PALETTES:
            for part in ("base", "dado", "upper"):
                for s in SIDES:
                    codes.add(f"l52-extwall-{f}-{p}-{part}-{s}")
    return codes


def build(gen):
    global G
    G = gen
    textures()
    G.save(worn_hall(), "tile-hallworn")
    # J. Barry's walls where the Crash's holes were filled and painted over: the paint a shade fresher in a patch
    patch = Image.open(os.path.join(G.TEX, "wall-blue-dado.png")).convert("RGBA")
    pp = patch.load()
    rng = random.Random(6420)
    x0, y0, x1, y1 = rng.randint(4, 9), rng.randint(3, 8), rng.randint(20, 27), rng.randint(17, 24)
    for y in range(y0, y1):
        for x in range(x0, x1):
            r, g, b, a = pp[x, y]
            pp[x, y] = (min(255, r + 14), min(255, g + 14), min(255, b + 12), a)
    for (hx, hy) in [(rng.randint(x0 + 2, x1 - 3), rng.randint(y0 + 2, y1 - 3)) for _ in range(5)]:
        pp[hx, hy] = tuple(min(255, v + 22) for v in pp[hx, hy][:3]) + (255,)
    G.save(patch, "wall-blue-patch")
    mat = M.noise_hv((58, 60, 62), 3, 6410, (32, 32), 3, (16, 8))
    dm = ImageDraw.Draw(mat)
    for y in range(2, 30, 3):
        dm.line((2, y, 29, y), fill=(44, 46, 48, 255))
    frame(mat, (90, 92, 94), 2)
    G.save(mat, "floor-mat")
    extra_textures_for_shapes()
    blocktypes()
