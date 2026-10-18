"""Textures for the Level 11 props of the "l11art" round: the basement door, the directory board, the fire hydrant,
the mailbox on the street corner (postbox) and the one at a suburban gate (mailbox), the grand piano, the phone
booth, the medical cabinet and the pantry shelf (models: l11art.py).

Every key starts with `l11a-` (all props share textures/block/detail/, so a plain name can overwrite another
level's texture). Structure first (the real parts are geometry), then shading, then a low grain; paints are
painted metal / enamel / lacquer from matlib, steels are brushed. Lettering is drawn in a pixel face (`FONT`),
never scaled type. Nothing here changes an old key. `generate()` is called from gen_city.generate().
"""
import math
import random

from PIL import Image

import matlib as M
from detail_kit import seed_of
from detail_textures import S, save

# 3x5 capitals and digits for plates, labels and signs
FONT = {
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"), "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"), "E": ("111", "100", "110", "100", "111"), "F": ("111", "100", "110", "100", "100"),
    "G": ("011", "100", "101", "101", "011"), "H": ("101", "101", "111", "101", "101"), "I": ("111", "010", "010", "010", "111"),
    "J": ("001", "001", "001", "101", "010"), "K": ("101", "101", "110", "101", "101"), "L": ("100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101"), "N": ("110", "101", "101", "101", "101"), "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"), "Q": ("010", "101", "101", "111", "011"), "R": ("110", "101", "110", "101", "101"),
    "S": ("011", "100", "010", "001", "110"), "T": ("111", "010", "010", "010", "010"), "U": ("101", "101", "101", "101", "111"),
    "V": ("101", "101", "101", "101", "010"), "W": ("101", "101", "111", "111", "101"), "X": ("101", "101", "010", "101", "101"),
    "Y": ("101", "101", "010", "010", "010"), "Z": ("111", "001", "010", "100", "111"),
    "0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"), "2": ("110", "001", "010", "100", "111"),
    "3": ("110", "001", "010", "001", "110"), "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "110", "001", "110"),
    "6": ("011", "100", "110", "101", "010"), "7": ("111", "001", "010", "010", "010"), "8": ("010", "101", "010", "101", "010"),
    "9": ("010", "101", "011", "001", "110"), "-": ("000", "000", "111", "000", "000"), "?": ("110", "001", "010", "000", "010"),
    " ": ("00", "00", "00", "00", "00"), "$": ("011", "110", "010", "011", "110"),
}


def word_width(word, gap=1):
    return sum(len(FONT[c][0]) for c in word) + gap * (len(word) - 1)


def draw_word(img, word, x, y, ink, gap=1, shadow=None):
    """A word in the pixel face with its top-left at (x, y); `shadow` gives a drop shadow one px down and right."""
    p = img.load()
    w, h = img.size
    for ch in word:
        g = FONT[ch]
        for r in range(5):
            for c, bit in enumerate(g[r]):
                if bit == "1":
                    if shadow and 0 <= x + c + 1 < w and 0 <= y + r + 1 < h:
                        p[x + c + 1, y + r + 1] = M.rgba(shadow)
                    if 0 <= x + c < w and 0 <= y + r < h:
                        p[x + c, y + r] = M.rgba(ink)
        x += len(g[0]) + gap
    return x


def centred(img, word, y, ink, gap=1, shadow=None, x0=0, x1=None):
    x1 = x1 if x1 is not None else img.size[0]
    draw_word(img, word, x0 + (x1 - x0 - word_width(word, gap)) // 2, y, ink, gap, shadow)


def paint(seed_name, base, chips=3, under=(70, 68, 66), grain=2, mottle=3, rust=0.0):
    seed = seed_of(seed_name)
    img = M.painted_metal(seed, base=base, grain=grain, mottle=mottle, panel=False, chips=chips, under=under)
    if rust:
        M.rust(img, rust, seed + 2, color=(138, 74, 40), dark=(84, 48, 30), cells=(4, 2, 1))
    return img


def sheen(img, strength=14, seed=0, vertical=True):
    """A broad soft highlight band down (or across) a glossy surface, so lacquer and enamel read as lit."""
    w, h = img.size
    rng = random.Random(seed)
    c = rng.uniform(0.25, 0.5) * (w if vertical else h)
    wd = (w if vertical else h) * 0.14
    p = img.load()
    for y in range(h):
        for x in range(w):
            d = abs((x if vertical else y) - c) / wd
            if d < 1:
                p[x, y] = M.rgba(M.lift(p[x, y], strength * (1 - d) ** 2))
    return img


# ---------------- Shared ----------------

def metals():
    save(M.brushed_metal(seed_of("l11a-steel"), base=(176, 180, 184), grain=3, direction="h", streak=8, sheen=10), "l11a-steel")
    save(M.brushed_metal(seed_of("l11a-steelv"), base=(170, 174, 178), grain=3, direction="v", streak=8, sheen=10), "l11a-steelv")
    img = M.brushed_metal(seed_of("l11a-brass"), base=(190, 152, 70), grain=3, direction="h", streak=7, sheen=12)
    M.scratches(img, 3, 11, length=(2, 5), light=0.2)
    save(img, "l11a-brass")
    img = M.noise_hv((40, 42, 46), 3, seed_of("l11a-darksteel"), mottle=4)
    M.scratches(img, 3, 12, length=(2, 5), light=0.2)
    save(img, "l11a-darksteel")
    save(M.rubber(seed_of("l11a-rubber"), base=(34, 34, 36)), "l11a-rubber")


# ---------------- Fire hydrant ----------------

def hydrant():
    seed = seed_of("l11a-hydrant")
    img = M.painted_metal(seed, base=(176, 36, 28), grain=2, mottle=3, panel=False, chips=7, under=(58, 52, 50))
    p = img.load()
    for y in range(S):  # a casting seam down the barrel, one lit lip beside a dark groove
        p[15, y] = M.rgba(M.lift(p[15, y], -22))
        p[16, y] = M.rgba(M.lift(p[16, y], 12))
    M.rust(img, 0.14, seed + 3, color=(150, 78, 40), dark=(86, 46, 30), cells=(4, 2, 1))
    M.drips(img, 2, seed + 4, color=(104, 40, 30), length=(5, 12), strength=0.35)
    M.grime(img, 0.14, seed + 5, color=(70, 52, 40), bias="bottom")
    sheen(img, 12, seed + 6)
    save(img, "l11a-hydrant")
    img = M.noise_hv((58, 54, 52), 3, seed_of("l11a-hydrantiron"), mottle=5)  # bare cast iron: caps, flange rims
    M.rust(img, 0.25, 71, color=(130, 72, 40), dark=(80, 46, 30), cells=(4, 2, 1))
    M.scratches(img, 4, 72, length=(2, 5), light=0.18)
    save(img, "l11a-hydrantiron")
    img = M.brushed_metal(seed_of("l11a-chain"), base=(112, 114, 118), grain=3, direction="h", streak=5, sheen=8)
    M.rust(img, 0.18, 73, color=(130, 72, 40), dark=(80, 46, 30), cells=(4, 2, 1))
    save(img, "l11a-chain")


# ---------------- Mailboxes ----------------

def postbox():
    seed = seed_of("l11a-postblue")
    img = M.painted_metal(seed, base=(34, 62, 124), grain=2, mottle=3, panel=False, chips=5, under=(92, 94, 96))
    p = img.load()
    for x in (0, 16):  # standing seams: a dark groove with a lit lip
        for y in range(S):
            p[x % S, y] = M.rgba(M.lift(p[x % S, y], -22))
            p[(x + 1) % S, y] = M.rgba(M.lift(p[(x + 1) % S, y], 10))
    for y in range(3, S, 8):  # a row of rivets along each band
        for x in range(2, S, 4):
            M.screw(img, x, y, slot=False)
    M.grime(img, 0.12, seed + 3, color=(60, 56, 48), bias="bottom")
    M.scratches(img, 3, seed + 4, length=(3, 7), light=0.16)
    sheen(img, 12, seed + 5)
    save(img, "l11a-postblue")
    # the front: plain enamel, a gold stripe, the box's name in white pixel capitals
    img = M.painted_metal(seed_of("l11a-postfront"), base=(34, 62, 124), grain=2, mottle=3, panel=False, chips=4, under=(92, 94, 96))
    p = img.load()
    for x in range(S):
        for y in (4, 5):
            p[x, y] = M.rgba(M.lift((196, 160, 70), -14 if y == 5 else 4))
    pass
    M.grime(img, 0.12, 21, color=(60, 56, 48), bias="bottom")
    sheen(img, 10, 22)
    save(img, "l11a-postfront")
    save(M.noise_hv((8, 8, 10), 2, seed_of("l11a-postslot"), mottle=1), "l11a-postslot")
    # a collection-times plate (tiny: a pattern of rules and print): white enamel, a red rule, two lines of dark print
    img = Image.new("RGBA", (S, S), M.rgba((228, 224, 212)))
    p = img.load()
    for y in range(S):
        for x in range(S):
            c = M.lift((228, 224, 212), ((x * 3 + y * 5) % 4) - 1.5)
            if y % 4 == 0:
                c = (190, 40, 34)
            elif y % 4 == 1 and x % 5 != 4:
                c = (44, 44, 48)
            elif y % 4 == 2 and x % 7 != 6:
                c = (110, 108, 102)
            p[x, y] = M.rgba(c)
    save(img, "l11a-postplate")
    # the name plate, 8 x 2.6 units (16 x 5 px window): gold capitals on navy enamel
    img = M.noise_hv((20, 36, 80), 2, seed_of("l11a-postname"), mottle=2)
    draw_word(img, "MAIL", 0, 0, (226, 190, 96), gap=1)
    save(img, "l11a-postname")


def mailbox():
    seed = seed_of("l11a-mailbox")
    img = M.painted_metal(seed, base=(46, 62, 96), grain=2, mottle=3, panel=False, chips=6, under=(116, 116, 112))
    M.rust(img, 0.1, seed + 2, color=(138, 74, 40), dark=(84, 48, 30), cells=(4, 2, 1))
    M.grime(img, 0.1, seed + 3, color=(60, 56, 48), bias="bottom")
    sheen(img, 12, seed + 4)
    save(img, "l11a-mailbox")
    img = M.painted_metal(seed_of("l11a-flag"), base=(190, 36, 28), grain=2, mottle=2, panel=False, chips=2, under=(90, 80, 76))
    save(img, "l11a-flag")
    img = M.wood_planks(seed_of("l11a-post"), base=(120, 94, 66), planks=2, direction="v", grain=3, contrast=0.9, flecks=0.7, per_plank=6,
                        gap=(70, 52, 36))
    M.grime(img, 0.18, 31, color=(70, 58, 44), bias="bottom")
    save(img, "l11a-post")


# ---------------- Phone booth ----------------

def booth():
    seed = seed_of("l11a-boothframe")
    img = M.painted_metal(seed, base=(64, 70, 72), grain=2, mottle=3, panel=False, chips=7, under=(150, 152, 150))
    M.rust(img, 0.08, seed + 2, color=(130, 76, 42), dark=(80, 48, 32), cells=(4, 2, 1))
    M.scratches(img, 4, seed + 3, length=(3, 8), light=0.16)
    M.grime(img, 0.12, seed + 4, color=(54, 50, 44), bias="bottom")
    save(img, "l11a-boothframe")
    img = M.painted_metal(seed_of("l11a-boothback"), base=(168, 170, 164), grain=2, mottle=4, panel=False, chips=3, under=(100, 98, 92))
    M.grime(img, 0.2, 41, color=(86, 76, 60), bias="bottom")
    M.stain(img, 42, radius=7, color=(110, 96, 70), strength=0.2)
    M.scratches(img, 5, 43, length=(3, 9), light=0.16)
    save(img, "l11a-boothback")
    img = M.glass(seed_of("l11a-boothglass"), base=(170, 200, 196), alpha=70, streaks=2, dust=0.03, edge=False)
    save(img, "l11a-boothglass")
    img = M.noise_hv((58, 60, 62), 3, seed_of("l11a-boothfloor"), mottle=4)
    p = img.load()
    for y in range(S):
        for x in range(S):
            if x % 4 == 0 or y % 4 == 0:
                p[x, y] = M.rgba(M.lift(p[x, y], -14))
    save(img, "l11a-boothfloor")
    # the lit sign, 12 x 3 units at 4 px a unit: dark blue capitals on a milky panel, a ruled border
    img = Image.new("RGBA", (48, 16), M.rgba((226, 230, 224)))
    p = img.load()
    for y in range(16):
        for x in range(48):
            p[x, y] = M.rgba(M.lift((226, 230, 224), (((x * 7 + y * 3) % 5) - 2) * 0.8 + (3 if y < 8 else -3)))
    for x in range(48):
        for y in (0, 15):
            p[x, y] = M.rgba((40, 70, 140))
    for y in range(16):
        for x in (0, 47):
            p[x, y] = M.rgba((40, 70, 140))
    centred(img, "TELEPHONE", 5, (30, 58, 124), gap=1)
    save(img, "l11a-boothsign")
    # the phone: a dark enamel housing, a steel faceplate, the handset in black moulded plastic
    img = M.painted_metal(seed_of("l11a-phonehousing"), base=(44, 48, 52), grain=2, mottle=2, panel=False, chips=3, under=(120, 122, 120))
    sheen(img, 12, 51)
    save(img, "l11a-phonehousing")
    img = M.noise_hv((26, 26, 28), 2, seed_of("l11a-handset"), mottle=2)
    sheen(img, 18, 52)
    save(img, "l11a-handset")
    save(M.brushed_metal(seed_of("l11a-keyplate"), base=(150, 154, 158), grain=2, direction="h", streak=5, sheen=8), "l11a-keyplate")
    save(M.noise_hv((200, 200, 194), 2, seed_of("l11a-key"), mottle=2), "l11a-key")
    # a telephone directory: a yellow cover, a printed band
    img = M.noise_hv((214, 176, 52), 3, seed_of("l11a-book"), mottle=3)
    p = img.load()
    for y in range(S):
        for x in range(S):
            if y > 20:
                p[x, y] = M.rgba(M.lift((214, 176, 52), -22))
    for y in range(2, 6):
        for x in range(2, 30):
            if (x + y) % 3:
                p[x, y] = M.rgba((60, 44, 20))
    save(img, "l11a-book")
    img = M.noise_hv((226, 222, 206), 2, seed_of("l11a-pages"), mottle=2)  # the page block's edges
    p = img.load()
    for y in range(0, S, 2):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y], -8))
    save(img, "l11a-pages")


# ---------------- Medical cabinet ----------------

def medcab():
    seed = seed_of("l11a-enamel")
    img = M.painted_metal(seed, base=(216, 216, 208), grain=2, mottle=3, panel=False, chips=3, under=(110, 108, 100))
    M.grime(img, 0.12, seed + 2, color=(120, 108, 80), bias="bottom")
    sheen(img, 10, seed + 3)
    save(img, "l11a-enamel")
    img = M.painted_metal(seed_of("l11a-enameldoor"), base=(238, 238, 230), grain=2, mottle=3, panel=False, chips=4, under=(120, 116, 106))
    M.scratches(img, 3, 61, length=(3, 8), light=0.14, dark_side=True)
    M.grime(img, 0.1, 62, color=(130, 116, 86), bias="bottom")
    sheen(img, 12, 63)
    save(img, "l11a-enameldoor")
    img = M.painted_metal(seed_of("l11a-medframe"), base=(150, 154, 150), grain=2, mottle=3, panel=False, chips=0)
    save(img, "l11a-medframe")
    img = M.painted_metal(seed_of("l11a-redcross"), base=(196, 28, 26), grain=2, mottle=2, panel=False, chips=2, under=(120, 100, 96))
    save(img, "l11a-redcross")
    img = M.painted_metal(seed_of("l11a-enamelplate"), base=(240, 240, 234), grain=1, mottle=2, panel=False, chips=1, under=(160, 150, 140))
    save(img, "l11a-enamelplate")


# ---------------- Grand piano ----------------

def piano():
    seed = seed_of("l11a-lacquer")
    img = M.noise_hv((26, 26, 31), 2, seed, mottle=3, hue=1.0)
    p = img.load()
    for y in range(S):  # a faint straight grain under the lacquer, and a long highlight
        for x in range(S):
            g = ((x * 5 + (y // 3) * 3) % 7) - 3
            p[x, y] = M.rgba(M.lift(p[x, y], g * 0.7))
    sheen(img, 26, seed + 1)
    M.scratches(img, 3, seed + 2, length=(3, 8), light=0.3)
    save(img, "l11a-lacquer")
    img = M.noise_hv((22, 22, 27), 2, seed_of("l11a-lacquerhi"), mottle=3, hue=1.0)  # sides: a broad sheen band the other way
    sheen(img, 30, 91, vertical=False)
    save(img, "l11a-lacquerhi")
    # the white keys' tops, 16 keys over a block: each a pale ivory a little different, a dark gap between
    rng = random.Random(seed_of("l11a-keys"))
    img = Image.new("RGBA", (S, S), M.rgba((244, 240, 228)))
    p = img.load()
    for k in range(16):
        c = M.lift((244, 240, 226), rng.uniform(-5, 3))
        for y in range(S):
            for x in (2 * k, 2 * k + 1):
                p[x, y] = M.rgba(M.lift(c, 2 if x % 2 == 0 else -2))
        for y in range(S):
            p[(2 * k + 1) % S, y] = M.rgba(M.lift(c, -26))
    for y in range(S):
        for x in range(S):
            if y > 24:
                p[x, y] = M.rgba(M.lift(p[x, y], -4))
    save(img, "l11a-keys")
    img = M.noise_hv((218, 214, 200), 2, seed_of("l11a-keyfront"), mottle=2)  # the keys' fronts
    p = img.load()
    for x in range(1, S, 2):
        for y in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y], -26))
    save(img, "l11a-keyfront")
    img = M.noise_hv((14, 14, 16), 2, seed_of("l11a-ebony"), mottle=1, hue=0)
    sheen(img, 24, 77)
    save(img, "l11a-ebony")
    # the harp, seen from above: the gold cast-iron plate, long strings running front to back, tuning pins at the end
    img = M.noise_hv((170, 134, 66), 3, seed_of("l11a-plate"), mottle=6)
    p = img.load()
    for x in range(S):
        if x % 2 == 0:
            for y in range(S):
                p[x, y] = M.rgba(M.lift((196, 192, 180), ((y + x) % 3) - 1) if (x // 2) % 3 else M.lift((168, 118, 70), 0))
    for x in range(S):
        for y in (0, 1):
            p[x, y] = M.rgba((46, 36, 20))
    for y in range(4, S, 9):  # two cross struts, a dark rib with a lit lip
        for x in range(S):
            p[x, y] = M.rgba(M.lift((150, 112, 50), -24))
            p[x, (y + 1) % S] = M.rgba(M.lift((200, 160, 80), 8))
    save(img, "l11a-plate")
    img = M.wood_planks(seed_of("l11a-sound"), base=(176, 138, 88), planks=4, direction="v", grain=3, contrast=0.8, flecks=0.5, per_plank=6,
                        gap=(120, 90, 54))
    save(img, "l11a-sound")
    img = M.fabric(seed_of("l11a-velvet"), base=(120, 24, 34), weave="twill", contrast=6, grain=2, mottle=5, thread=2)
    p = img.load()
    for y in range(S):
        for x in range(S):
            if 8 <= x < 24 and 8 <= y < 24 and (x + y) % 4 == 0:  # a tufted button
                pass
    save(img, "l11a-velvet")
    # sheet music: paper with five-line staves
    img = M.noise_hv((232, 226, 206), 2, seed_of("l11a-sheet"), mottle=3)
    p = img.load()
    for top in (4, 14, 24):
        for k in range(5):
            for x in range(2, S - 2):
                p[x, top + k] = M.rgba((88, 84, 78))
        rng2 = random.Random(top)
        for x in range(4, S - 3, 4):
            ny = top + rng2.randint(0, 4)
            p[x, ny] = M.rgba((24, 24, 26))
            p[x + 1, ny] = M.rgba((24, 24, 26))
    save(img, "l11a-sheet")


# ---------------- Pantry shelf ----------------

def pantry():
    img = M.wood_planks(seed_of("l11a-pine"), base=(178, 138, 86), planks=3, direction="h", grain=3, contrast=1.0, flecks=0.8, per_plank=7,
                        gap=(104, 74, 44))
    M.grime(img, 0.1, 21, color=(100, 76, 48), bias="bottom")
    save(img, "l11a-pine")
    img = M.wood_planks(seed_of("l11a-pinev"), base=(168, 128, 80), planks=2, direction="v", grain=3, contrast=1.0, flecks=0.8, per_plank=7,
                        gap=(96, 68, 40))
    save(img, "l11a-pinev")
    img = M.wood_planks(seed_of("l11a-bead"), base=(196, 186, 156), planks=8, direction="v", grain=2, contrast=0.6, flecks=0.2, per_plank=3,
                        gap=(126, 116, 92))
    M.grime(img, 0.14, 22, color=(110, 96, 70), bias="bottom")
    save(img, "l11a-bead")

    def tin(key, base, label, kind):
        """A can's wrapper: a lid rim in the top rows, then the label band; drawn so the top 8 rows (a 4-unit can)
        carry the whole can."""
        seed = seed_of(key)
        img = M.brushed_metal(seed, base=base, grain=2, direction="v", streak=4, sheen=10)
        p = img.load()
        for y in range(1, 7):
            for x in range(S):
                p[x, y] = M.rgba(M.lift(label, ((x * 5 + y * 3) % 5) - 2))
        for x in range(S):
            p[x, 0] = M.rgba(M.lift(base, 8))
            p[x, 1] = M.rgba(M.lift(base, -22))
            p[x, 6] = M.rgba(M.lift(label, -22))
            p[x, 7] = M.rgba(M.lift(base, -16))
        if kind == "tomato":
            for x in range(10, 22):
                p[x, 3] = M.rgba((236, 220, 120))
        elif kind == "beans":
            for x in range(8, 24):
                p[x, 3] = M.rgba((240, 230, 200))
        return img

    save(tin("l11a-tintomato", (178, 180, 178), (188, 44, 34), "tomato"), "l11a-tintomato")
    save(tin("l11a-tinbeans", (178, 180, 178), (150, 90, 40), "beans"), "l11a-tinbeans")
    save(tin("l11a-tinpeas", (178, 180, 178), (58, 124, 62), "beans"), "l11a-tinpeas")
    save(tin("l11a-tintea", (186, 168, 112), (150, 40, 40), "none"), "l11a-tintea")
    save(M.brushed_metal(seed_of("l11a-tinlid"), base=(188, 190, 188), grain=2, direction="h", streak=4, sheen=10), "l11a-tinlid")

    def jar(key, fill):
        """A jar: glass edge, the contents showing through (`fill`), a paper label across the middle; top 10 rows."""
        seed = seed_of(key)
        img = M.noise_hv(fill, 3, seed, mottle=5)
        p = img.load()
        for y in range(10):
            p[0, y] = M.rgba(M.lift(fill, 22))
            p[1, y] = M.rgba(M.lift(fill, 12))
            p[S - 2, y] = M.rgba(M.lift(fill, -16))
            p[S - 1, y] = M.rgba(M.lift(fill, -26))
        for y in range(3, 7):
            for x in range(4, S - 4):
                p[x, y] = M.rgba(M.lift((226, 218, 190), ((x + y) % 3) - 1))
        for x in range(6, S - 6):
            p[x, 4] = M.rgba((120, 60, 50))
        return img

    save(jar("l11a-jarjam", (150, 34, 40)), "l11a-jarjam")
    save(jar("l11a-jarpickle", (112, 128, 52)), "l11a-jarpickle")
    save(jar("l11a-jarhoney", (206, 140, 36)), "l11a-jarhoney")
    img = M.brushed_metal(seed_of("l11a-jarlid"), base=(196, 162, 70), grain=2, direction="h", streak=4, sheen=10)
    save(img, "l11a-jarlid")
    img = M.noise_hv((150, 100, 30), 3, seed_of("l11a-oil"), mottle=5)  # a bottle of oil: amber glass, a highlight
    p = img.load()
    for y in range(S):
        p[1, y] = M.rgba((236, 200, 120))
        p[2, y] = M.rgba((200, 150, 60))
        p[S - 2, y] = M.rgba((90, 56, 18))
    save(img, "l11a-oil")
    img = M.fabric(seed_of("l11a-sack"), base=(214, 204, 178), weave="basket", contrast=8, grain=2, mottle=5, thread=3)
    p = img.load()
    for x in range(S):
        for y in (14, 15):
            p[x, y] = M.rgba((60, 86, 150))
    save(img, "l11a-sack")
    img = M.fabric(seed_of("l11a-sackfront"), base=(214, 204, 178), weave="basket", contrast=8, grain=2, mottle=5, thread=3)
    p = img.load()
    for y in range(S):
        for x in range(S):
            if 2 <= x < 30 and 6 <= y < 22 and (x in (2, 29) or y in (6, 21)):
                p[x, y] = M.rgba((60, 86, 150))
    centred(img, "FLOUR", 11, (60, 86, 150), gap=1)
    save(img, "l11a-sackfront")
    img = M.noise_hv((196, 150, 90), 3, seed_of("l11a-sacktie"), mottle=3)
    save(img, "l11a-sacktie")

    def carton(key, base, band, word):
        img = M.noise_hv(base, 3, seed_of(key), mottle=3)
        p = img.load()
        for y in range(S):
            for x in range(S):
                if 3 <= y < 13:
                    p[x, y] = M.rgba(M.lift(band, ((x + y) % 3) - 1))
        centred(img, word, 6, (250, 244, 226), gap=1, shadow=(60, 30, 20))
        for x in range(S):
            p[x, 0] = M.rgba(M.lift(base, 10))
            p[x, S - 1] = M.rgba(M.lift(base, -16))
        return img

    save(carton("l11a-cereal", (226, 190, 70), (190, 56, 40), "OATS"), "l11a-cereal")
    save(carton("l11a-tea", (60, 100, 70), (40, 80, 54), "TEA"), "l11a-tea")
    save(M.noise_hv((206, 182, 120), 3, seed_of("l11a-cartonside"), mottle=3), "l11a-cartonside")
    save(M.noise_hv((190, 164, 104), 3, seed_of("l11a-cartontop"), mottle=3), "l11a-cartontop")


# ---------------- Basement door ----------------

def door():
    for part in ("lower", "upper"):
        seed = seed_of("l11a-doorleaf" + part)
        img = M.painted_metal(seed, base=(98, 108, 102), grain=2, mottle=4, panel=False, chips=0)
        p = img.load()
        for y in ((6, 22) if part == "lower" else (4, 18)):  # a pressed stiffener rib across the leaf
            for x in range(S):
                p[x, y] = M.rgba(M.lift(p[x, y], -24))
                p[x, y + 1] = M.rgba(M.lift(p[x, y + 1], 9))
        M.rust(img, 0.1 if part == "lower" else 0.04, seed + 5, color=(138, 74, 40), dark=(84, 48, 30), cells=(4, 2, 1))
        M.scratches(img, 5, seed + 6, length=(3, 8), light=0.16)
        M.grime(img, 0.18, seed + 7, color=(54, 50, 44), bias="bottom" if part == "lower" else None)
        sheen(img, 9, seed + 8)
        save(img, f"l11a-doorleaf-{part}")
        img = M.painted_metal(seed_of("l11a-doorpanel" + part), base=(110, 120, 114), grain=2, mottle=3, panel=False, chips=3, under=(150, 150, 146))
        M.rust(img, 0.08 if part == "lower" else 0.03, 33, color=(138, 74, 40), dark=(84, 48, 30), cells=(4, 2, 1))
        sheen(img, 9, 34)
        save(img, f"l11a-doorpanel-{part}")
    img = M.painted_metal(seed_of("l11a-doorframe"), base=(70, 78, 74), grain=2, mottle=3, panel=False, chips=4, under=(130, 128, 122))
    M.rust(img, 0.12, 35, color=(138, 74, 40), dark=(84, 48, 30), cells=(4, 2, 1))
    save(img, "l11a-doorframe")
    img = M.galvanised(seed_of("l11a-doorkick"), base=(150, 152, 150), spangle=10)
    M.scratches(img, 6, 36, length=(3, 8), light=0.2)
    M.grime(img, 0.2, 37, color=(70, 62, 52), bias="bottom")
    save(img, "l11a-doorkick")
    # the stencilled sign plate: 12 x 3 units at 4 px a unit, off-white capitals on dark green enamel, drawn in 48 x 12
    img = M.noise_hv((34, 56, 44), 2, seed_of("l11a-doorsign"), mottle=2)
    p = img.load()
    for x in range(S):
        pass
    big = Image.new("RGBA", (48, 16), M.rgba((34, 56, 44)))
    q = big.load()
    for y in range(16):
        for x in range(48):
            q[x, y] = M.rgba(M.lift((34, 56, 44), (((x * 5 + y * 7) % 5) - 2) * 0.8))
    for x in range(48):
        q[x, 0] = M.rgba((200, 196, 184))
        q[x, 11] = M.rgba((200, 196, 184))
    for y in range(12):
        q[0, y] = M.rgba((200, 196, 184))
        q[47, y] = M.rgba((200, 196, 184))
    centred(big, "BASEMENT", 3, (232, 228, 214), gap=2, shadow=(14, 26, 20))
    M.grime(big, 0.1, 38, color=(24, 36, 28))
    save(big, "l11a-doorsign")
    save(M.brushed_metal(seed_of("l11a-lever"), base=(190, 192, 194), grain=2, direction="h", streak=5, sheen=10), "l11a-lever")
    img = M.brushed_metal(seed_of("l11a-louvre"), base=(88, 94, 90), grain=2, direction="h", streak=5, sheen=6)
    save(img, "l11a-louvre")


# ---------------- Directory board ----------------

def directory():
    img = M.wood_planks(seed_of("l11a-walnut"), base=(92, 58, 34), planks=2, direction="h", grain=3, contrast=0.9, flecks=0.8, per_plank=5,
                        gap=(50, 30, 18))
    sheen(img, 18, 5, vertical=False)
    save(img, "l11a-walnut")
    img = M.fabric(seed_of("l11a-felt"), base=(24, 38, 54), weave="plain", contrast=4, grain=2, mottle=3, thread=2)
    save(img, "l11a-felt")
    save(M.brushed_metal(seed_of("l11a-ledge"), base=(196, 198, 196), grain=2, direction="h", streak=5, sheen=10), "l11a-ledge")
    rows = ("1 LOBBY", "2-11 ----", "12 ?????")
    for i, line in enumerate(rows):  # 10 x 2 unit strips at 4 px a unit: white letters on felt, a lit edge above and a shadow below
        img = Image.new("RGBA", (40, 8), M.rgba((28, 44, 62)))
        p = img.load()
        for y in range(8):
            for x in range(40):
                p[x, y] = M.rgba(M.lift((28, 44, 62), (((x * 3 + y * 5 + i) % 4) - 1.5) * 0.9))
        for x in range(40):
            p[x, 0] = M.rgba((52, 72, 96))
            p[x, 7] = M.rgba((12, 20, 30))
        draw_word(img, line, 3, 1, (236, 232, 220), gap=1, shadow=(10, 16, 24))
        save(img, f"l11a-dirrow{i}")
    img = Image.new("RGBA", (40, 8), M.rgba((176, 140, 60)))  # the header: engraved on a brass plate
    p = img.load()
    for y in range(8):
        for x in range(40):
            p[x, y] = M.rgba(M.lift((184, 148, 66), (((x * 7 + y * 3) % 5) - 2) * 0.8 + (6 if y < 3 else -4 if y > 5 else 0)))
    for x in range(40):
        p[x, 0] = M.rgba((222, 188, 104))
        p[x, 7] = M.rgba((110, 80, 30))
    centred(img, "DIRECTORY", 1, (52, 34, 12), gap=1, shadow=(222, 190, 110))
    save(img, "l11a-dirhead")


def generate():
    metals()
    hydrant()
    postbox()
    mailbox()
    booth()
    medcab()
    piano()
    pantry()
    door()
    directory()
