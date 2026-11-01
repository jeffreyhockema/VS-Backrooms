"""Level 36 "Airport": the textures of the level's prop models (called from tools/gen_36_props.py).

Every texture here lives in textures/block/36/props/ (so no key can collide with the surfaces' own textures in
block/36/), 32 px a block; pictures (logos, signs, screens) are bigger and mapped over a whole face. Palette: cool
whites, warm greys, brushed steel, navy fabric, BTA purple; desolate but spotless, so no grime, only wear and AO.
"""
import math
import os
import random
import zlib

from PIL import Image, ImageDraw

import matlib as M
from gen_textures import check_atlas_grid
from gen_3999_kit import F3, F5, draw_text, text_width

S = 32
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures", "block", "36", "props")
WRITTEN = []

# The palette
NAVY = (44, 56, 104)
CHARCOAL = (68, 70, 76)
STEEL = (184, 188, 194)
CHROME = (206, 210, 218)
DARKSTEEL = (92, 96, 104)
LAMINATE = (168, 162, 154)     # warm-grey laminate (check-in fronts)
TERMGREY = (158, 158, 156)     # the terminal's grey (gate podium)
WHITE = (238, 238, 236)
PURPLE = (96, 50, 146)         # BTA purple
PANEL = (206, 202, 194)        # warm light-grey composite cladding


def seed_of(name):
    return zlib.crc32(("l36p-" + name).encode()) & 0xFFFF


def save(img, name):
    check_atlas_grid(img, f"block/36/props/{name}.png")
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))
    WRITTEN.append(name)


def rgba(c, a=255):
    return M.rgba(c, a)


def gloss(c, seed, side=False, sheen=(9, 7), amp=1.5, size=S):
    """Moulded plastic or a gloss finish: the colour, a broad soft sheen up and to the left, a fine grain; a side face
    is a step darker and has no sheen (as Level 3999's furniture)."""
    base = M.lift(c, -14) if side else c
    img = M.noise_hv(base, amp, seed, size, mottle=2, cells=(16, 8), hue=0.8)
    px = img.load()
    if not side:
        w, h = img.size
        for y in range(h):
            for x in range(w):
                t = math.exp(-(((x - sheen[0]) / 14.0) ** 2 + ((y - sheen[1]) / 10.0) ** 2))
                px[x, y] = rgba(M.lift(px[x, y], 6 * t), 255)
    return img


def fleck(img, seed, n=18, dark=(-7, -3), light=(3, 6)):
    """A solid-surface or laminate fleck: single pixels a little darker or lighter."""
    rng = random.Random(seed)
    w, h = img.size
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        M.touch(img, x, y, rng.uniform(*dark) / 100 if rng.random() < 0.6 else rng.uniform(*light) / 100)
    return img


def text(img, s, x, y, col, font=F5, scale=1, gap=1):
    return draw_text(img, s, x, y, col, font, scale, gap)


def centre_text(img, s, y, col, font=F5, scale=1, gap=1, x0=0, x1=None):
    x1 = img.size[0] if x1 is None else x1
    text(img, s, x0 + (x1 - x0 - text_width(s, font, scale, gap)) // 2, y, col, font, scale, gap)


# ======================================================================== Materials

def materials():
    save(M.brushed_metal(seed=seed_of("steel"), base=STEEL, streak=7, sheen=8), "steel")
    save(M.brushed_metal(seed=seed_of("steelv"), base=STEEL, direction="v", streak=7, sheen=9), "steelv")
    save(M.brushed_metal(seed=seed_of("chrome"), base=CHROME, direction="v", streak=6, sheen=16), "chrome")
    save(M.brushed_metal(seed=seed_of("darksteel"), base=DARKSTEEL, streak=5, sheen=6), "darksteel")
    save(M.noise_hv((36, 36, 40), 2, seed_of("black"), S, mottle=2, hue=0.5), "black")
    save(M.rubber(seed=seed_of("rubber"), base=(40, 40, 42)), "rubber")
    # diamond tread plate (the scale's platform)
    img = M.brushed_metal(seed=seed_of("tread"), base=(170, 174, 180), streak=5, sheen=6)
    for y in range(0, S, 4):
        for x in range((y // 4) % 2 * 4, S, 8):
            for (dx, dy, f) in ((0, 0, 0.26), (1, 0, 0.18), (-1, 1, 0.14), (0, 1, 0.08), (1, 1, -0.12), (2, 1, -0.18), (0, 2, -0.22), (1, 2, -0.24)):
                M.touch(img, (x + dx) % S, (y + dy) % S, f)
    save(img, "tread")
    # conveyor belt rubber, ribs across (the scale's belt, the X-ray belt)
    save(M.rubber(seed=seed_of("beltrubber"), base=(46, 46, 48), pattern="ribs", pitch=6), "beltrubber")
    # laminates and solid surfaces
    img = M.noise_hv(LAMINATE, 2, seed_of("laminate"), S, mottle=3, hue=1.0)
    save(fleck(img, seed_of("laminatef"), 22), "laminate")
    img = M.noise_hv(M.lift(LAMINATE, -16), 2, seed_of("laminateside"), S, mottle=3, hue=1.0)
    save(fleck(img, seed_of("laminatesf"), 16), "laminate-side")
    img = M.noise_hv((216, 212, 204), 1.5, seed_of("worktop"), S, mottle=2, hue=0.8)
    save(fleck(img, seed_of("worktopf"), 30), "worktop")
    save(gloss(TERMGREY, seed_of("termgrey"), amp=1.5), "termgrey")
    save(gloss(TERMGREY, seed_of("termgreyside"), side=True), "termgrey-side")
    save(gloss(WHITE, seed_of("white"), amp=1.0), "white")
    save(gloss(WHITE, seed_of("whiteside"), side=True, amp=1.0), "white-side")
    save(gloss((200, 202, 204), seed_of("lightplastic"), amp=1.5), "lightplastic")
    save(gloss((70, 72, 78), seed_of("darkplastic"), amp=1.5), "darkplastic")


def fabrics():
    for name, c in (("navy", NAVY), ("charcoal", CHARCOAL)):
        save(M.fabric(seed=seed_of(name), base=c, weave="twill", contrast=8, grain=2, mottle=4), name)
        save(M.fabric(seed=seed_of(name + "side"), base=M.lift(c, -14), weave="twill", contrast=6, grain=2, mottle=3), name + "-side")
    # cabin seat cloth: navy with a small woven dot motif every 8 px
    img = M.fabric(seed=seed_of("cabin"), base=(40, 54, 112), weave="plain", contrast=6, grain=2, mottle=3)
    for y in range(2, S, 8):
        for x in range((y // 8) % 2 * 4 + 2, S, 8):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                px = img.load()
                px[(x + dx) % S, (y + dy) % S] = rgba(M.lift((96, 120, 170), (dx - dy) * 6))
    save(img, "cabin")
    save(M.fabric(seed=seed_of("cabinside"), base=(30, 40, 86), weave="plain", contrast=5, grain=2, mottle=3), "cabin-side")
    save(M.fabric(seed=seed_of("headcover"), base=(232, 232, 226), weave="plain", contrast=5, grain=2, mottle=3), "headcover")
    save(M.fabric(seed=seed_of("jacket"), base=(150, 128, 92), weave="twill", contrast=10, grain=2, mottle=6), "jacket")
    save(M.fabric(seed=seed_of("jacketdark"), base=(112, 94, 66), weave="twill", contrast=8, grain=2, mottle=5), "jacket-dark")
    save(M.fabric(seed=seed_of("shirt"), base=(172, 192, 216), weave="plain", contrast=6, grain=2, mottle=4), "shirt")
    save(M.fabric(seed=seed_of("pack"), base=(166, 50, 46), weave="ripstop", contrast=6, grain=2, mottle=4), "pack")
    save(M.fabric(seed=seed_of("packdark"), base=(116, 34, 32), weave="ripstop", contrast=5, grain=2, mottle=3), "pack-dark")
    save(M.fabric(seed=seed_of("strap"), base=(42, 42, 46), weave="twill", contrast=6, grain=2, mottle=2), "strap")
    save(M.fabric(seed=seed_of("duffel"), base=(92, 104, 70), weave="basket", contrast=8, grain=2, mottle=5), "duffel")
    save(M.fabric(seed=seed_of("umbrella"), base=(34, 36, 44), weave="plain", contrast=5, grain=2, mottle=3), "umbrella")
    # queue belts: navy webbing with a lighter edge thread
    img = M.fabric(seed=seed_of("beltnavy"), base=(36, 46, 96), weave="twill", contrast=6, grain=2, mottle=2)
    for x in range(S):
        for y in (0, 1, S - 2, S - 1):
            M.touch(img, x, y, 0.16 if y in (1, S - 2) else -0.1)
    save(img, "beltnavy")
    # seatbelt webbing (grey) and leather
    img = M.fabric(seed=seed_of("webgrey"), base=(116, 118, 124), weave="twill", contrast=8, grain=2, mottle=2)
    save(img, "webgrey")
    img = M.noise_hv((112, 70, 42), 3, seed_of("leather"), S, mottle=6, hue=1.5)
    save(fleck(img, seed_of("leatherf"), 30), "leather")


def door_parts():
    # The holdroom's composite cladding: warm light-grey panels, one a block, a fine groove at the joint
    img = M.noise_hv(PANEL, 1.5, seed_of("panel"), S, mottle=3, hue=0.8)
    M.bevel(img, (0, 0, S - 1, S - 1), 1, 0.10)
    for x in range(S):
        M.touch(img, x, S - 1, -0.34)
    for y in range(S):
        M.touch(img, S - 1, y, -0.3)
    M.ao_border(img, 3, 0.06, (0, 0, S - 1, S - 1), "br")
    save(img, "panel")
    # the door: heavy grey painted steel, a little worn
    save(M.painted_metal(seed=seed_of("door"), base=(116, 120, 126), grain=2, mottle=4, panel=False, chips=2, under=(150, 152, 156)), "door")
    # wired glass, dark behind: a diamond wire mesh and one soft reflection band
    img = M.noise_hv((28, 34, 40), 2, seed_of("wiredglass"), S, mottle=3, hue=0.5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            c = px[x, y]
            t = ((x + y) - 18) % S
            t = min(t, S - t)
            if t < 4:
                c = M.lift(c, 24 * (1 - t / 4))
            if ((x + y) % 8 == 0) or ((x - y) % 8 == 0):
                c = M.mix(c, (96, 100, 104), 0.4)
            px[x, y] = rgba(c)
    save(img, "wiredglass")
    # GATE plate: brushed steel, black letters
    img = M.brushed_metal(seed=seed_of("gateplate"), base=(196, 198, 204), size=(48, 16), streak=5, sheen=6)
    centre_text(img, "GATE", 4, (24, 24, 28, 255), F5, 1, 2)
    M.bevel(img, (0, 0, 48, 16), 1, 0.2)
    save(img, "gateplate")
    # the status lamp: a dark red lens with a small hot spot
    img = M.noise_hv((112, 22, 20), 2, seed_of("lampred"), S, mottle=3, hue=0.5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = math.exp(-(((x - 11) / 6.0) ** 2 + ((y - 10) / 5.0) ** 2))
            px[x, y] = rgba(M.lift(px[x, y], 46 * t))
    save(img, "lampred")


def screens():
    # The agent's monitor: a dim check-in app (navy, a header bar, rows of fields)
    img = Image.new("RGBA", (32, 32), (18, 30, 62, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 4], fill=(40, 120, 160, 255))
    rng = random.Random(seed_of("screen"))
    for i, y in enumerate(range(7, 30, 3)):
        x1 = 2 + rng.randrange(0, 2)
        d.line([2, y, 2 + rng.randrange(5, 10), y], fill=(150, 180, 210, 255))
        d.line([14, y, 14 + rng.randrange(6, 15), y], fill=(220, 226, 236, 255) if i % 3 else (240, 200, 90, 255))
    d.rectangle([22, 26, 29, 29], fill=(60, 170, 110, 255))
    save(img, "screen")
    # The gate desk's screen: a boarding list, a big flight number line
    img = Image.new("RGBA", (32, 32), (14, 22, 40, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 31, 6], fill=(28, 52, 96, 255))
    draw_text(img, "GATE", 2, 1, (240, 210, 90, 255), F3)
    for y in range(10, 30, 4):
        d.line([2, y, 2 + rng.randrange(8, 26), y], fill=(170, 196, 220, 255))
    save(img, "gatescreen")
    # The scale's weight display: green digits, 0.0 KG
    img = Image.new("RGBA", (32, 16), (16, 22, 18, 255))
    draw_text(img, "00.0", 3, 5, (90, 240, 120, 255), F3)
    draw_text(img, "KG", 22, 5, (60, 160, 80, 255), F3)
    M.inset(img, (0, 0, 32, 16), 1, 0.3)
    save(img, "display")
    # The airline's backlit logo strip: LIMINAL AIR, a swoosh, on deep teal
    img = Image.new("RGBA", (96, 16))
    px = img.load()
    for y in range(16):
        for x in range(96):
            t = 1 - abs(y - 7.5) / 8
            px[x, y] = rgba(M.lift((18, 92, 120), 18 * t))
    d = ImageDraw.Draw(img)
    # the swoosh: a white arc and a tail fin
    for k in range(14):
        a = math.pi * (0.9 + k / 13 * 0.9)
        x, y = 10 + 7 * math.cos(a), 9 + 4 * math.sin(a)
        d.point([round(x), round(y)], fill=(255, 255, 255, 255))
        d.point([round(x), round(y) + 1], fill=(200, 236, 246, 255))
    d.polygon([(12, 3), (16, 3), (13, 9)], fill=(255, 200, 80, 255))
    draw_text(img, "LIMINAL", 22, 2, (255, 255, 255, 255), F5)
    draw_text(img, "AIR", 64, 2, (255, 200, 80, 255), F5)
    d.line([22, 12, 88, 12], fill=(120, 200, 220, 255))
    save(img, "logostrip")
    # The X-ray monitor: a false-colour bag (orange organics, blue metal, green plastics) on white
    img = Image.new("RGBA", (32, 32), (226, 230, 236, 255))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 7, 27, 25], 3, fill=(240, 180, 110, 255), outline=(60, 100, 200, 255))
    d.rectangle([7, 10, 14, 15], fill=(80, 170, 110, 255))
    d.rectangle([17, 11, 24, 13], fill=(40, 70, 170, 255))
    d.ellipse([16, 16, 23, 22], fill=(200, 120, 60, 255))
    d.line([6, 22, 13, 18], fill=(30, 50, 140, 255), width=2)
    d.rectangle([0, 0, 31, 3], fill=(40, 44, 52, 255))
    draw_text(img, "XR2", 1, 0, (240, 240, 240, 255), F3)
    save(img, "xrayscreen")
    # The scanner's indicator strip: a column of LEDs, green below amber below red
    img = Image.new("RGBA", (8, 32), (20, 20, 24, 255))
    d = ImageDraw.Draw(img)
    for i, y in enumerate(range(1, 32, 3)):
        c = (230, 60, 50) if i < 2 else (240, 180, 50) if i < 4 else (80, 230, 110)
        d.rectangle([2, y, 5, y + 1], fill=c + (255,))
    save(img, "scanlight")
    # The meeting column's lit seam
    img = M.noise_hv((226, 236, 250), 1.5, seed_of("seam"), (8, 32), mottle=2, hue=0)
    save(img, "seamlight")


def machines():
    # Scanner panels: light grey moulded panels; X-ray body: off-white painted steel in panels
    save(gloss((182, 184, 186), seed_of("scangrey"), amp=1.5), "scangrey")
    save(gloss((182, 184, 186), seed_of("scangreyside"), side=True, amp=1.5), "scangrey-side")
    save(M.painted_metal(seed=seed_of("xraybody"), base=(196, 196, 190), grain=2, mottle=3, panel=True, chips=0), "xraybody")
    save(M.painted_metal(seed=seed_of("xraydark"), base=(76, 84, 96), grain=2, mottle=3, panel=False, chips=0), "xraydark")
    # lead-strip curtain: dark grey rubber strips with dark gaps
    img = M.rubber(seed=seed_of("curtain"), base=(70, 72, 70))
    px = img.load()
    for y in range(S):
        for x in range(0, S, 4):
            px[x, y] = rgba((34, 34, 36))
            M.touch(img, (x + 1) % S, y, 0.12)
    for x in range(S):
        M.touch(img, x, S - 1, -0.2)
    save(img, "curtain")
    # control panel: dark grey with a key grid, two big buttons and a key switch
    img = M.painted_metal(seed=seed_of("ctrl"), base=(60, 64, 72), grain=2, mottle=2, panel=True, chips=0)
    d = ImageDraw.Draw(img)
    for r in range(3):
        for c in range(4):
            d.rectangle([3 + c * 4, 4 + r * 4, 5 + c * 4, 6 + r * 4], fill=(170, 174, 180, 255))
    d.rectangle([21, 5, 26, 10], fill=(40, 160, 70, 255))
    d.rectangle([21, 14, 26, 19], fill=(190, 40, 36, 255))
    d.rectangle([4, 20, 18, 27], fill=(24, 26, 30, 255))
    draw_text(img, "XR", 6, 21, (120, 200, 230, 255), F3)
    save(img, "ctrlpanel")
    # radiation sticker: yellow, black trefoil
    img = Image.new("RGBA", (16, 16), (240, 200, 40, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 15], outline=(24, 24, 24, 255))
    for k in range(3):
        a0 = -90 + k * 120 - 30
        d.pieslice([2, 2, 13, 13], a0, a0 + 60, fill=(24, 24, 24, 255))
    d.ellipse([6, 6, 9, 9], fill=(240, 200, 40, 255))
    d.ellipse([7, 7, 8, 8], fill=(24, 24, 24, 255))
    save(img, "radsticker")
    # roller bed seen from above: rollers across, lit tops, dark gaps
    img = M.brushed_metal(seed=seed_of("rollers"), base=(176, 180, 186), streak=5, sheen=6)
    px = img.load()
    for y in range(S):
        k = y % 4
        f = {0: 0.18, 1: 0.06, 2: -0.1, 3: -0.55}[k]
        for x in range(S):
            M.touch(img, x, y, f)
    save(img, "rollers")
    # security tray: grey plastic, and its darker inside
    save(gloss((118, 122, 130), seed_of("tray"), amp=1.5), "tray")
    save(gloss((96, 100, 108), seed_of("trayin"), side=True, amp=1.5), "tray-in")


def bta():
    save(gloss(PURPLE, seed_of("purple"), amp=1.5), "purple")
    save(gloss(PURPLE, seed_of("purpleside"), side=True, amp=1.5), "purple-side")
    save(gloss((236, 234, 242), seed_of("btawhite"), amp=1.0), "btawhite")
    # the logo: a white doorway, a plane flying out through it, BTA under
    big = Image.new("RGBA", (64, 64), PURPLE + (255,))
    for y in range(64):
        for x in range(64):
            big.putpixel((x, y), rgba(M.lift(PURPLE, 8 * math.exp(-(((x - 22) / 30.0) ** 2 + ((y - 18) / 24.0) ** 2)))))
    logo(big, 9, 3, 46, (250, 248, 255, 255))
    centre_text(big, "BTA", 54, (250, 248, 255, 255), F5, 1, 2)
    save(big, "btalogo")
    # brochure leaflets: a title band, a picture block, text lines, each its own colour
    cols = [(220, 70, 60), (60, 140, 210), (240, 190, 60), (90, 180, 110), (150, 90, 200), (240, 130, 170)]
    rng = random.Random(seed_of("leaflets"))
    for i, c in enumerate(cols):
        img = M.noise_hv((240, 238, 232), 1.5, seed_of(f"leaf{i}"), S, mottle=2, hue=0)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 31, 9], fill=c + (255,))
        d.rectangle([3, 3, 3 + rng.randrange(12, 26), 5], fill=(255, 255, 255, 255))
        d.rectangle([3, 12, 28, 21], fill=M.rgba(M.lift(c, -30)))
        d.ellipse([18, 13, 26, 20], fill=M.rgba(M.lift(c, 40)))
        for y in (24, 27, 30):
            d.line([3, y, 3 + rng.randrange(14, 26), y], fill=(110, 110, 120, 255))
        save(img, f"leaflet-{i}")
    # the fascia sign: BACKROOMS TRAVEL AGENCY with the logo, 192 x 40 px over three blocks (64 x 40 each)
    W, H = 192, 40
    sign = Image.new("RGBA", (W, H))
    px = sign.load()
    for y in range(H):
        for x in range(W):
            t = 1 - abs(y - H / 2) / (H / 2)
            px[x, y] = rgba(M.lift(PURPLE, 14 * t + 4))
    d = ImageDraw.Draw(sign)
    d.rectangle([0, 0, W - 1, 1], fill=(246, 244, 250, 255))
    d.rectangle([0, H - 2, W - 1, H - 1], fill=(246, 244, 250, 255))
    logo(sign, 14, 3, 34, (255, 255, 255, 255))
    centre_text(sign, "BACKROOMS", 7, (255, 255, 255, 255), F5, 2, 1, x0=66, x1=W - 2)
    centre_text(sign, "TRAVEL AGENCY", 26, (226, 210, 250, 255), F5, 1, 3, x0=66, x1=W - 2)
    for i, part in enumerate(("l", "m", "r")):
        save(sign.crop((i * 64, 0, i * 64 + 64, H)), f"btasign-{part}")


def logo(img, x0, y0, size, col):
    """The BTA mark at (x0, y0), `size` px square: a doorway (an open frame, a threshold) with an airliner climbing out
    through it to the upper right. Drawn at 4x and scaled down, so the edges blend into the ground behind."""
    k = 4
    n = size * k
    m = Image.new("L", (n, n), 0)
    d = ImageDraw.Draw(m)
    u = n / 48.0

    def P(pts):
        return [(x * u, y * u) for x, y in pts]
    # the doorway: two posts, a lintel, a threshold step
    d.rectangle(P([(9, 7), (13, 43)]), fill=255)
    d.rectangle(P([(9, 4), (33, 8)]), fill=255)
    d.rectangle(P([(29, 7), (33, 20)]), fill=255)   # the right post stops where the plane breaks out
    d.rectangle(P([(29, 33), (33, 43)]), fill=255)
    d.rectangle(P([(4, 42), (40, 46)]), fill=255)
    # the plane: fuselage along (16, 36) -> (45, 9), swept wings, a tail
    ax, ay, bx, by = 15.0, 37.0, 45.0, 9.0
    L = math.hypot(bx - ax, by - ay)
    fx, fy = (bx - ax) / L, (by - ay) / L      # forward
    px_, py = -fy, fx                          # to the right of the nose... (perpendicular)

    def at(t, w):
        return (ax + fx * t + px_ * w, ay + fy * t + py * w)
    body = [at(0, -1.6), at(L - 5, -2.0), at(L, 0), at(L - 5, 2.0), at(0, 1.6)]
    d.polygon(P(body), fill=255)
    for sgn in (-1, 1):
        wing = [at(L * 0.52, sgn * 1.5), at(L * 0.30, sgn * 14), at(L * 0.22, sgn * 14), at(L * 0.34, sgn * 1.5)]
        d.polygon(P(wing), fill=255)
        tail = [at(5.5, sgn * 1.2), at(1.5, sgn * 6), at(-0.5, sgn * 6), at(2, sgn * 1.2)]
        d.polygon(P(tail), fill=255)
    # a clear gap round the plane where it crosses the doorway (it flies in front of the frame)
    small = m.resize((size, size), Image.LANCZOS)
    cpx, ipx = small.load(), img.load()
    W, H = img.size
    for y in range(size):
        for x in range(size):
            a = cpx[x, y] / 255.0
            X, Y = x0 + x, y0 + y
            if a > 0 and 0 <= X < W and 0 <= Y < H:
                b = ipx[X, Y]
                ipx[X, Y] = tuple(int(b[i] + (col[i] - b[i]) * a) for i in range(3)) + (255,)


def duty_free():
    save(M.glass(seed=seed_of("glasstop"), base=(206, 222, 226), alpha=70, streaks=2, dust=0.0), "glass")
    for name, c in (("pink", (232, 120, 170)), ("amber", (214, 140, 40)), ("blue", (70, 130, 220)), ("green", (90, 180, 110))):
        img = M.noise_hv(c, 1.5, seed_of("bottle" + name), S, mottle=2, hue=0.5)
        px = img.load()
        for y in range(S):
            for x in range(S):
                k = x % 8
                f = 30 if k == 1 else 14 if k == 2 else -10 if k >= 6 else 0
                px[x, y] = rgba(M.lift(px[x, y], f), 225)
        save(img, f"bottle-{name}")
    save(M.brushed_metal(seed=seed_of("gold"), base=(206, 172, 92), direction="v", streak=6, sheen=12), "gold")
    img = M.noise_hv((246, 244, 240), 1, seed_of("tester"), (32, 16), mottle=1, hue=0)
    centre_text(img, "TESTER", 5, (60, 60, 70, 255), F3, 1, 1)
    save(img, "tester")


def food():
    save(M.noise_hv((244, 244, 242), 1.2, seed_of("tabletop"), S, mottle=1, hue=0.4), "tabletop")
    save(M.brushed_metal(seed=seed_of("tableedge"), base=(150, 154, 160), streak=6, sheen=8), "tableedge")
    save(gloss((150, 54, 40), seed_of("foodtray"), amp=1.5), "foodtray")
    img = M.noise_hv((200, 140, 72), 3, seed_of("bun"), S, mottle=6, hue=1.5)
    rng = random.Random(seed_of("sesame"))
    for _ in range(16):
        x, y = rng.randrange(S), rng.randrange(S)
        img.putpixel((x, y), (244, 230, 190, 255))
    save(img, "bun")
    save(M.noise_hv((92, 58, 40), 5, seed_of("patty"), S, mottle=8, hue=1.5), "patty")
    save(M.noise_hv((120, 168, 66), 5, seed_of("lettuce"), S, mottle=8, hue=2.0), "lettuce")
    img = M.paper(seed=seed_of("napkin"), base=(238, 236, 228), seams=None)
    save(img, "napkin")
    # paper cup: white, a blue band and a little wordmark
    img = M.noise_hv((240, 240, 236), 1.2, seed_of("cup"), S, mottle=2, hue=0)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, 31, 19], fill=(40, 90, 170, 255))
    d.line([0, 11, 31, 11], fill=(90, 140, 210, 255))
    for x in range(2, 32, 8):
        d.rectangle([x, 13, x + 3, 16], fill=(240, 200, 80, 255))
    save(img, "cup")
    # paper straw: red and white spiral stripes, soggy
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            c = (200, 60, 60) if ((x + y) // 4) % 2 else (236, 228, 214)
            px[x, y] = rgba(M.lift(c, -8 * ((x * 7 + y * 3) % 5) / 4))
    save(img, "straw")
    save(gloss((242, 240, 234), seed_of("plate"), amp=1.0), "plate")
    # mould: green-grey fuzz with white bloom and dark spots
    img = M.noise_hv((122, 136, 104), 7, seed_of("mould"), S, mottle=10, hue=3.0)
    rng = random.Random(seed_of("mouldspots"))
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        c = (214, 220, 204) if rng.random() < 0.5 else (54, 64, 46)
        img.putpixel((x, y), c + (255,))
    save(img, "mould")


def meeting():
    # the converging arrows: four white arrows pointing at a white dot, on red
    n = 64
    img = Image.new("RGBA", (n, n))
    px = img.load()
    for y in range(n):
        for x in range(n):
            t = math.exp(-(((x - 26) / 40.0) ** 2 + ((y - 24) / 40.0) ** 2))
            px[x, y] = rgba(M.lift((200, 30, 36), 22 * t))
    d = ImageDraw.Draw(img)
    W = (255, 255, 255, 255)
    c = n / 2
    d.ellipse([c - 6, c - 6, c + 5, c + 5], fill=W)
    # one arrow pointing in from the top, then turned to the four sides
    arrow = [(c - 3, 4), (c + 2, 4), (c + 2, 15), (c + 7, 15), (c - 0.5, 23), (c - 8, 15), (c - 3, 15)]
    for k in range(4):
        pts = []
        for (x, y) in arrow:
            dx, dy = x - c, y - c
            for _ in range(k):
                dx, dy = -dy, dx
            pts.append((c + dx, c + dy))
        d.polygon(pts, fill=W)
    d.rectangle([0, 0, n - 1, n - 1], outline=(246, 246, 246, 255), width=2)
    save(img, "meetsign")


def lost_found():
    save(M.painted_metal(seed=seed_of("shelf"), base=(108, 116, 126), grain=2, mottle=3, panel=False, chips=3, under=(160, 162, 166)), "shelf")
    for name, c in (("red", (170, 44, 48)), ("blue", (44, 84, 150)), ("black", (46, 46, 52)), ("silver", (178, 182, 188)), ("teal", (40, 130, 130))):
        img = gloss(c, seed_of("case" + name), amp=1.5)
        M.emboss_lines(img, xs=(5, 11, 20, 26), raised=True, strength=0.2)
        save(img, f"case-{name}")
    img = M.noise_hv((240, 236, 214), 1.5, seed_of("tag"), (16, 16), mottle=1, hue=0)
    d = ImageDraw.Draw(img)
    d.line([2, 6, 13, 6], fill=(120, 120, 130, 255))
    d.line([2, 9, 10, 9], fill=(120, 120, 130, 255))
    d.rectangle([0, 0, 15, 2], fill=(220, 120, 40, 255))
    save(img, "tag")
    # the shelf's placard: LOST & FOUND, white on navy
    img = Image.new("RGBA", (64, 16), (34, 46, 92, 255))
    centre_text(img, "LOST & FOUND", 4, (246, 246, 246, 255), F5, 1, 1)
    M.bevel(img, (0, 0, 64, 16), 1, 0.2)
    save(img, "lfsign")


# ======================================================================== The links (2026-10-31)

def _plane(d, cx, cy, w, fill):
    """An airliner from above, nose up and a little to the right (as the terminal's own Gates signs draw it)."""
    pts = [(0, -0.46), (0.045, -0.40), (0.05, -0.12), (0.44, 0.08), (0.44, 0.15), (0.05, 0.04), (0.04, 0.30),
           (0.17, 0.40), (0.17, 0.46), (0, 0.42)]
    pts = pts + [(-u, v) for u, v in reversed(pts[1:-1])]
    a = math.radians(35)
    d.polygon([(cx + (u * math.cos(a) - v * math.sin(a)) * w, cy + (u * math.sin(a) + v * math.cos(a)) * w) for u, v in pts], fill=fill)


def links():
    """The door under the airplane sign (in the baggage wall, and found in walls of the city and the Suburbs) and the
    restroom sink."""
    # The door's glazing: dark tinted glass, a cool reflection band, a faint frosted strip at hand height
    img = M.noise_hv((30, 38, 46), 2, seed_of("airglass"), S, mottle=3, hue=0.5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            c = px[x, y]
            t = ((x + y) - 20) % S
            t = min(t, S - t)
            if t < 5:
                c = M.lift(c, 22 * (1 - t / 5))
            if 13 <= y <= 15:
                c = M.mix(c, (150, 160, 168), 0.35)
            px[x, y] = rgba(c)
    save(img, "airglass")
    # The sign: a backlit charcoal box, an aluminium rim, the terminal's yellow tile with the airplane knocked out of it,
    # a small arrow pointing down at the door (supersampled four times and shrunk, so the edges stay clean)
    K, W = 4, 64
    big = Image.new("RGBA", (W * K, W * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    d.rectangle((0, 0, W * K, W * K), fill=(40, 42, 47, 255))
    d.rounded_rectangle((12 * K, 6 * K, 52 * K, 46 * K), radius=5 * K, fill=(255, 200, 20, 255))
    _plane(d, 32 * K, 26 * K, 34 * K, (40, 42, 47, 255))
    d.polygon([(26 * K, 50 * K), (38 * K, 50 * K), (32 * K, 59 * K)], fill=(238, 238, 232, 255))
    img = big.resize((W, W), Image.LANCZOS)
    px = img.load()
    for y in range(W):
        for x in range(W):
            r, g, b, a = px[x, y]
            glow = 6 * math.exp(-(((y - W / 2) / (W / 2.2)) ** 2))
            if (r, g, b) == (40, 42, 47):
                px[x, y] = (int(r + glow), int(g + glow), int(b + glow), 255)
    for i in range(W):
        for (x, y, c) in ((i, 0, (128, 132, 138)), (i, 1, (112, 116, 122)), (i, W - 1, (86, 88, 94)), (i, W - 2, (96, 98, 104)),
                          (0, i, (106, 110, 116)), (1, i, (100, 104, 110)), (W - 1, i, (92, 96, 102)), (W - 2, i, (98, 102, 108))):
            px[x, y] = c + (255,)
    save(img, "airsign")
    # The sink: white vitreous china, the basin's inside a shade darker toward the drain, and water (still, and running over)
    img = M.noise_hv((214, 218, 220), 1.5, seed_of("basin"), S, mottle=2, hue=0.5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            dd = math.hypot(x - S / 2 + 0.5, y - S / 2 + 0.5) / (S / 2)
            c = M.lift(px[x, y], -26 * max(0.0, 1 - dd))
            if dd < 0.14:
                c = M.mix(c, (150, 154, 160), 0.7)
            px[x, y] = rgba(c)
    save(img, "basin")
    for name, base, amp in (("water", (78, 140, 164), 3), ("waterfall", (110, 168, 190), 4)):
        img = M.noise_hv(base, amp, seed_of(name), S, mottle=4, cells=(8, 4), hue=1.0)
        px = img.load()
        for y in range(S):
            for x in range(S):
                c = px[x, y]
                streak = (math.sin((x * 1.7 + y * (0.3 if name == "water" else 3.1)) * 0.9) + 1) / 2
                c = M.lift(c, 18 * streak ** 6)
                px[x, y] = rgba(c)
        save(img, name)


def textures():
    WRITTEN.clear()
    materials()
    fabrics()
    door_parts()
    screens()
    machines()
    bta()
    duty_free()
    food()
    meeting()
    lost_found()
    links()
    return list(WRITTEN)
