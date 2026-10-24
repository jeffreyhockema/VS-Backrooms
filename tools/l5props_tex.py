"""Textures for the Level 5 props rebuilt as geometry (graphics pass, "Level 5 art": furnace, curio cabinet, ice machine,
nightstand, bed, grandfather clock, gilt mirror).

Called from `detail_textures.level5`. Every key here is new and starts with `l5`; the shared keys (`mahogany`, `brass`,
`gilt`, `lampshade`, `silver`, `china`...) are used by other props and stay as they were. Each model part's face shows its
texture from the corner (UV from the part's own size, 2 px per unit), so wear is scattered and printed art sits in the
top-left of the 32x32 texture. Lettering is the 3x5 pixel face of `l1props_tex.FONT`, drawn crisp and doubled, never scaled
type. Glass that must show what is behind it is a cut-out texture (opaque glints and a rim, transparent elsewhere), so no
blocktype needs a transparent render pass.
"""
import math
import random

import matlib as M
from PIL import Image

from detail_kit import T, seed_of
from l1props_tex import FONT, word_width

S = 32


def save(img, name):
    T.save(img, f"block/detail/{name}.png")


def rgb(c, a=255):
    c = tuple(M.clamp(v) for v in c[:3])
    return c + (a if len(c) < 4 else c[3],)


def clear():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def put(img, x, y, c):
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        img.putpixel((x, y), rgb(c))


def big_word(img, s, x, y, ink, scale=2, gap=1):
    """A word in the 3x5 face at `scale` (a whole number of px per font px); returns the x after it."""
    for ch in s:
        g = FONT[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == "1":
                    for a in range(scale):
                        for b in range(scale):
                            put(img, x + i * scale + a, y + j * scale + b, ink)
        x += (len(g[0]) + gap) * scale
    return x


# ======================= Glass =======================

def cutout_glass(seed, streaks=((5, 6, 9), (14, 4, 6)), rim=True, tone=(190, 214, 220)):
    """A pane that shows what is behind it: transparent, with a few short diagonal glints (a lit core and a fainter
    edge), a lit rim along the top and left edge and a shaded one along the bottom and right, and some dust."""
    img = clear()
    rng = random.Random(seed)
    if rim:
        for i in range(S):
            put(img, i, 0, rgb(M.lift(tone, 8)))
            put(img, 0, i, rgb(M.lift(tone, 4)))
            put(img, i, S - 1, rgb(M.lift(tone, -48)))
            put(img, S - 1, i, rgb(M.lift(tone, -40)))
    for (x0, y0, ln) in streaks:  # long diagonals read as rods in front of what is behind: a few short glints
        for k in range(ln):
            put(img, x0 + k, y0 + k, rgb(M.lift(tone, 20)))
            if k % 3 != 2:
                put(img, x0 + k + 1, y0 + k, rgb(M.lift(tone, -12)))
    for _ in range(14):
        put(img, rng.randrange(2, S - 2), rng.randrange(2, S - 2), rgb(M.lift(tone, -26)))
    return img


def glass_textures():
    # the curio cabinet's panes: seen across a door two blocks tall, so the glints are spread
    save(cutout_glass(seed_of("l5glass"), streaks=((3, 4, 7), (17, 12, 8), (6, 21, 5))), "l5glass")
    save(cutout_glass(seed_of("l5clockglass"), streaks=((3, 2, 4),), rim=False, tone=(200, 218, 222)), "l5clockglass")

    # a glass shelf: pale green-grey, its edge a darker green as the sheet's thickness shows
    img = M.noise_hv((176, 202, 196), 2, seed_of("l5shelf"), S, 3, (16, 8), hue=0.5)
    for x in range(S):
        M.touch(img, x, 0, 0.12)
        M.touch(img, x, 1, 0.05)
        M.touch(img, x, S - 1, -0.2)
        M.touch(img, x, S - 2, -0.1)
    save(img, "l5shelf")

    # the gilt mirror: silvering with a faint blue-green cast, darker toward the foxed edges, one broad soft band of
    # light and a thin bright line beside it, and a few specks of foxing in the corners
    seed = seed_of("l5mirror")
    base = M.noise_hv((164, 182, 188), 2, seed, S, 3, (16, 8), hue=0.4)
    px = base.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            d = (x + y) % 32
            f = 0
            if 5 <= d <= 12:
                f += 14 * (1 - abs(d - 8.5) / 4.0)  # the broad band
            if d in (15, 16):
                f += 20 if d == 15 else 10
            if 21 <= d <= 23:
                f += 6
            edge = min(x, y, S - 1 - x, S - 1 - y)
            if edge < 3:
                f -= (3 - edge) * 8
            px[x, y] = M.rgba(M.lift(px[x, y], f))
    for _ in range(10):  # foxing
        x, y = rng.choice((rng.randrange(0, 6), rng.randrange(26, 32))), rng.choice((rng.randrange(0, 6), rng.randrange(26, 32)))
        base.putpixel((x, y), M.rgba(M.lift(base.getpixel((x, y))[:3], -22)))
    save(base, "l5mirror")

    # the bevel round the glass: a polished slope, lit along its top and left, in shadow along its bottom and right
    img = M.noise_hv((206, 224, 228), 2, seed_of("l5mirrorbevel"), S, 2, (16, 8), hue=0.3)
    save(img, "l5mirrorbevel")


# ======================= Curios =======================

def curio_textures():
    img = M.noise_hv((84, 18, 28), 4, seed_of("l5curioback"), S, 4, (8, 4), hue=1.0)  # velvet lining, ruched a little
    px = img.load()
    for x in range(S):
        for y in range(S):
            if (x // 4) % 2 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], 4))
    M.ao_border(img, 3, 0.12)
    save(img, "l5curioback")

    # cobalt porcelain with a white band and a gold line
    img = M.noise_hv((38, 70, 136), 3, seed_of("l5vase"), S, 4, (16, 8), hue=1.0)
    px = img.load()
    for x in range(S):
        for y in (8, 9, 10, 11):
            px[x, y] = M.rgba(M.mix(px[x, y][:3], (226, 228, 232), 0.85))
        px[x, 7] = M.rgba((196, 160, 72))
        px[x, 12] = M.rgba((196, 160, 72))
        for y in (16, 17):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], 12))
    save(img, "l5vase")

    # white china with a gold edge line
    img = M.noise_hv((238, 236, 228), 2, seed_of("l5china"), S, 2, (16, 8), hue=0.4)
    for i in range(S):
        for k in (0, S - 1):
            img.putpixel((i, k), M.rgba((200, 164, 76)))
            img.putpixel((k, i), M.rgba((200, 164, 76)))
    save(img, "l5china")

    img = M.brushed_metal(seed_of("l5silver"), base=(206, 210, 214), grain=2, direction="h", streak=4, sheen=12)
    M.grime(img, 0.12, seed_of("l5silvertarnish"), color=(120, 118, 112), cells=(4, 2), cover=0.4)
    save(img, "l5silver")

    # a leather book: dark green cover with gilt bands across the spine
    img = M.noise_hv((44, 70, 52), 3, seed_of("l5leather"), S, 4, (8, 4), hue=1.0)
    for y in (3, 4, 12, 13, 21, 22):
        for x in range(S):
            img.putpixel((x, y), M.rgba((190, 156, 70)))
    save(img, "l5leather")


# ======================= The grandfather clock =======================

def clock_textures():
    # the dial, 32 px over a 6.8-unit face: ivory, a black minute ring, ticks, and 12 3 6 9 in the pixel face
    img = Image.new("RGBA", (S, S), rgb((232, 222, 196)))
    px = img.load()
    cx = cy = 15.5
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - cx, y - cy)
            tone = 0
            if d > 14.5:
                px[x, y] = rgb((196, 160, 72))
            elif d > 13.2:
                px[x, y] = rgb((36, 30, 26))
            else:
                n = ((x * 7 + y * 13) % 5) - 2
                px[x, y] = rgb(M.lift((232, 222, 196), n + (-4 if d > 11 else 0)))
    ink = (30, 24, 20)
    for k in range(12):  # the hour ticks: three px long on the hours, one px on the minutes' ring
        a = math.radians(k * 30)
        for r in range(10, 13):
            put(img, round(cx + math.sin(a) * r), round(cy - math.cos(a) * r), ink)
    for k in range(60):
        if k % 5:
            a = math.radians(k * 6)
            put(img, round(cx + math.sin(a) * 12.4), round(cy - math.cos(a) * 12.4), (92, 80, 62))
    big_word(img, "12", 12, 5, ink, 1)
    big_word(img, "6", 14, 22, ink, 1)
    big_word(img, "3", 23, 14, ink, 1)
    big_word(img, "9", 6, 14, ink, 1)
    for i, (x, y) in enumerate(((10, 7), (21, 7), (7, 10), (24, 10), (7, 21), (24, 21), (10, 24), (21, 24))):
        put(img, x, y, ink)  # the other numerals' places: small pips
    save(img, "l5clockface")

    # inside the trunk: dark walnut-black, a lit vertical strip behind the pendulum's swing
    img = M.noise_hv((26, 18, 14), 3, seed_of("l5clockinner"), S, 3, (8, 4), hue=0.8)
    px = img.load()
    for y in range(S):
        for x in range(10, 22):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], 6))
    save(img, "l5clockinner")

    img = M.brushed_metal(seed_of("l5hand"), base=(30, 26, 24), grain=2, direction="h", streak=3, sheen=4)
    save(img, "l5hand")


# ======================= The bed =======================

def bed_textures():
    # percale: a tight plain weave, near white, warm
    img = M.fabric(seed_of("l5sheet"), base=(236, 232, 220), weave="plain", contrast=3, grain=2, mottle=3, thread=1)
    save(img, "l5sheet")
    img = M.fabric(seed_of("l5pillow"), base=(238, 234, 224), weave="plain", contrast=3, grain=2, mottle=3, thread=1)
    M.ao_border(img, 3, 0.10)
    save(img, "l5pillow")

    # the coverlet: burgundy, quilted in diamonds (a lighter thread along the stitching, a puff between)
    cov = M.fabric(seed_of("l5coverlet"), base=(112, 24, 22), weave="twill", contrast=5, grain=3, mottle=4, thread=2)
    px = cov.load()
    for y in range(S):
        for x in range(S):
            u, v = (x + y) % 16, (x - y) % 16
            if u in (0,) or v in (0,):
                px[x, y] = M.rgba(M.mix(px[x, y][:3], (178, 140, 70), 0.5))
            else:
                du, dv = min(u, 16 - u), min(v, 16 - v)
                px[x, y] = M.rgba(M.lift(px[x, y][:3], min(du, dv) * 1.1 - 4))
    save(cov, "l5coverlet")

    # the mattress's side: cream ticking with a fine grey-blue stripe, a welt (piping seam) top and bottom
    t = M.fabric(seed_of("l5mattress"), base=(224, 218, 202), weave="plain", contrast=3, grain=2, mottle=3, thread=1)
    px = t.load()
    for x in range(S):
        if x % 4 in (0, 1):
            for y in range(S):
                px[x, y] = M.rgba(M.mix(px[x, y][:3], (150, 160, 176), 0.45))
    for x in range(S):
        for y, f in ((0, 0.10), (1, -0.12), (6, -0.14), (7, 0.06)):
            M.touch(t, x, y, f)
    save(t, "l5mattress")

    # the bed skirt: burgundy velvet in box pleats (a lit fold, a shaded one, every 4 px)
    sk = M.noise_hv((92, 20, 26), 3, seed_of("l5skirt"), S, 4, (8, 4), hue=1.0)
    px = sk.load()
    for y in range(S):
        for x in range(S):
            k = x % 8
            f = (0.10, 0.06, 0.0, -0.08, -0.16, -0.10, -0.02, 0.04)[k]
            px[x, y] = M.rgba(M.shade_px(px[x, y][:3], f))
    save(sk, "l5skirt")


# ======================= The ice machine =======================

def ice_textures():
    st = M.brushed_metal(seed_of("l5icesteel"), base=(176, 180, 182), grain=3, direction="v", streak=8, sheen=8)
    M.scratches(st, 5, seed_of("l5icescratch"), length=(3, 7), light=0.12)
    save(st, "l5icesteel")
    dk = M.rubber(seed_of("l5icedark"), base=(40, 42, 44))
    save(dk, "l5icedark")
    pvc = M.painted_metal(seed_of("l5icepvc"), base=(206, 206, 196), panel=False, chips=1, under=(160, 160, 150))
    save(pvc, "l5icepvc")

    # the nameplate (24 x 12 px at the top-left: 12 x 6 units): navy, a pale rim, ICE in doubled pixel letters
    img = M.brushed_metal(seed_of("l5icelabel"), base=(176, 180, 182), grain=3, direction="v", streak=8, sheen=8)
    for y in range(12):
        for x in range(24):
            put(img, x, y, (226, 232, 238) if 0 < x < 23 and 0 < y < 11 else (34, 62, 112))
    big_word(img, "ICE", 1, 1, (34, 62, 112), 2)
    save(img, "l5icelabel")

    # the bin door's window: a dark bin with frost, white cubes in its lower half, a lit rim top and left
    img = clear()
    rng = random.Random(seed_of("l5icewin"))
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), rgb(M.lift((34, 46, 58), rng.uniform(-3, 3))))
    for k in range(60):
        x, y = rng.randrange(1, 31), rng.randrange(12, 31)
        w = rng.choice((2, 2, 3))
        c = M.lift((196, 220, 232), rng.uniform(-30, 8))
        for a in range(w):
            for b in range(w):
                put(img, x + a, y + b, c)
    for x in range(S):
        put(img, x, 0, (96, 112, 124))
        put(img, 0, x, (84, 100, 112))
    for k in range(4):
        put(img, 4 + k, 3 + k, (150, 176, 190))
    save(img, "l5icewin")


def furnace_textures():
    """Cast iron for the furnace's door frame, hinges, latch and ash door: darker than the plates, grey with a faint
    warmth, a few chips down to bare metal; it stands out against the plates by its lit edges (the game's face shading)."""
    img = M.painted_metal(seed_of("l5castiron"), base=(96, 90, 86), grain=3, mottle=5, panel=False, chips=3, under=(132, 126, 120))
    M.grime(img, 0.14, seed_of("l5castirongrime"), color=(40, 36, 34), cells=(8, 4), cover=0.5)
    save(img, "l5castiron")


# ======================= The turntable and the room service tray =======================

def turntable_textures():
    # the record: a cut-out disc 19 px across in the top-left (9.5 units, the top face's size). Shellac black with
    # fine groove bands (a lit lead-in, three tracks parted by smooth gaps, a dead-wax ring), a wedge of sheen and a
    # label: oxblood red with a gold rim, two lines of lettering and the spindle hole
    img = clear()
    rng = random.Random(seed_of("l5record"))
    c = 9.5
    for y in range(19):
        for x in range(19):
            dx, dy = x + 0.5 - c, y + 0.5 - c
            r = math.hypot(dx, dy)
            if r > 9.5:
                continue
            if r > 9.0:
                col = (58, 56, 58)  # the edge catches the light
            elif r > 3.6:
                band = int(r * 1.0) % 2
                gap = 5.6 < r < 6.1 or 7.3 < r < 7.7 or 3.6 < r < 4.2
                col = (30, 30, 33) if gap else (22 + 5 * band, 22 + 5 * band, 25 + 5 * band)
                # a soft wedge of light across the upper-left and a fainter one opposite
                ang = (math.degrees(math.atan2(dy, dx)) + 360) % 360
                for centre, amt in ((225, 20), (45, 8)):
                    d = min(abs(ang - centre), 360 - abs(ang - centre))
                    if d < 26:
                        col = M.lift(col, amt * (1 - d / 26) * (0.6 + 0.4 * band))
                col = M.lift(col, rng.uniform(-1.5, 1.5))
            elif r > 1.0:
                col = (150, 34, 30) if r < 3.1 else (196, 160, 72)
                col = M.lift(col, rng.uniform(-3, 3))
            else:
                col = (12, 10, 10)
            put(img, x, y, col)
    for x in range(6, 13):  # the label's lettering: two rows, one px high
        if x % 3 != 0:
            put(img, x, 7, (214, 184, 100))
    for x in range(7, 12):
        if x != 9:
            put(img, x, 12, (214, 184, 100))
    save(img, "l5record")

    # its edge and the platter's: black shellac / a turned steel platter, both with a lit top and shaded bottom
    img = M.rubber(seed_of("l5vinylside"), base=(26, 26, 28))
    save(img, "l5vinylside")
    img = M.brushed_metal(seed_of("l5platter"), base=(132, 134, 134), grain=2, direction="h", streak=5, sheen=12)
    save(img, "l5platter")

    # the speaker cloth: old gold-brown basket weave over a dark lattice every 4 px, faded in a band across the middle
    img = M.fabric(seed_of("l5ttcloth"), base=(136, 104, 58), weave="plain", contrast=6, grain=2, mottle=4, thread=2)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                px[x, y] = M.rgba(M.shade_px(px[x, y][:3], -0.28))
            elif (x % 4 == 2 and y % 4 == 2):
                px[x, y] = M.rgba(M.shade_px(px[x, y][:3], 0.10))
    M.ao_border(img, 2, 0.14)
    save(img, "l5ttcloth")


def tray_textures():
    # silver plate gone through at the edges and corners to the copper beneath, a little tarnish in the corners
    img = M.brushed_metal(seed_of("l5trayplate"), base=(204, 208, 212), grain=2, direction="h", streak=5, sheen=10)
    M.grime(img, 0.14, seed_of("l5traytarnish"), color=(112, 108, 102), cells=(4, 2), cover=0.35)
    rng = random.Random(seed_of("l5traywear"))
    for _ in range(9):
        x, y = rng.choice((rng.randrange(0, 2), rng.randrange(30, 32))), rng.choice((rng.randrange(0, 6), rng.randrange(26, 32)))
        if rng.random() < 0.5:
            x, y = y, x
        put(img, x, y, M.lift((176, 118, 84), rng.uniform(-14, 8)))
    M.scratches(img, 6, seed_of("l5trayscratch"), length=(3, 7), light=0.14)
    save(img, "l5trayplate")

    # the napkin: starched white linen, one navy line a px in from the edge
    img = M.fabric(seed_of("l5napkin"), base=(240, 237, 228), weave="plain", contrast=3, grain=2, mottle=3, thread=1)
    for i in range(S):
        for k in (2, S - 3):
            put(img, i, k, (60, 74, 112))
            put(img, k, i, (60, 74, 112))
    save(img, "l5napkin")

    # a red rose, its petals in curled rings of two reds, a dark heart
    img = M.noise_hv((150, 20, 34), 4, seed_of("l5rose"), S, 5, (8, 4), hue=1.0)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r = max(abs(x - 15.5), abs(y - 15.5))
            f = (-0.30, -0.10, -0.38, 0.06, -0.22, 0.12, -0.12, 0.0)[int(r / 2) % 8]
            px[x, y] = M.rgba(M.shade_px(px[x, y][:3], f))
    save(img, "l5rose")
    img = M.noise_hv((46, 84, 40), 3, seed_of("l5stem"), S, 4, (8, 4), hue=1.0)
    save(img, "l5stem")
    # coffee with a pale crema ring
    img = M.noise_hv((52, 30, 18), 2, seed_of("l5coffee"), S, 3, (8, 4), hue=0.6)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if abs(math.hypot(x - 15.5, y - 15.5) - 12) < 1.5:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], 22))
    save(img, "l5coffee")


def generate():
    furnace_textures()
    glass_textures()
    curio_textures()
    clock_textures()
    bed_textures()
    ice_textures()
    turntable_textures()
    tray_textures()
