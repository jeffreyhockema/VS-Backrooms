"""Level 120, "Broken Servos": round 3's detail blocks (the data centre's furniture, its signs and its wall dressing).

    l120-ups        a UPS cabinet, two high (lower, upper), whole or torn open; the upper has its dead display and warning plate
    l120-battery    a battery cabinet, two high: strings of sealed batteries behind a mesh door, the acid warning
    l120-crac       a cooling unit (CRAC), two high and its duct (lower, upper, duct): louvres, a control panel, the duct up into the ceiling
    l120-kvm        a KVM cart: a trolley with a monitor and keyboard, a cable trailing
    l120-mop        a mop bucket with its wringer and mop
    l120-debris     a ceiling tile fallen to the floor in pieces (walked over)
    l120-paper      a sheet of paper on the floor (walked over; the White Voids' one misplaced thing)
    l120-rowend     the end panel of a bank of racks, two high; the upper carries the row's letter (A-H)
    l120-shelf      steel shelving, two high, boxed drives and caddies on it
    l120-floorhole  a raised-floor panel lifted out: the plenum under it, pedestals and cables (a half-block step down)
    l120-walldeco   the wall (yellow paper, or a White Void's white) with something on its face, by kind: room plates, the DATA
                    HALL plates, AUTHORIZED PERSONNEL ONLY, taped notes, a fire point (extinguisher and its sign), cable bundles down
                    the wall, the terminal room's wall of screens, an evacuation plan, the hall's stencilled letter, conduit, EXIT
                    signs over doorways, an electrical panel; in the voids a crack and a smudge

Every block faces north in its shape and is turned for its side. Run from the repo root after gen_120.py (it reuses its
textures):  python tools/gen_120_detail.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

from modelkit import box
from gen_120 import (S, SIDES, ROTATE, BLOCKS, TEX, METAL, WOOD, STONE, PAPER, write_json, clamp, shade, canvas, rect, grain,
                     save, shape, cuboid, json_block, drops, SIDED, FULL)

LETTERS = "ABCDEFGH"
# The plates (Tile.Detail of WorldLayout.L120DecoPlate): SERVER ROOM A-H, the other rooms, DATA HALL A-H
PLATES = [f"SERVER ROOM {c}" for c in LETTERS] + ["TERMINAL ROOM", "UPS / BATTERY", "CABLE ROOM", "STORAGE"] + [f"DATA HALL {c}" for c in LETTERS]
NOTES = [["DON'T", "BOOT", "THEM"], ["WALK", "ONE WAY"], ["NOT", "AGAIN"], ["IT GETS UP", "WHERE", "YOU FALL"]]


def font(size):
    return ImageFont.load_default(size=size)


def text_center(d, box_, text, size, fill):
    x0, y0, x1, y1 = box_
    f = font(size)
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    d.text(((x0 + x1 - (r - l)) / 2 - l, (y0 + y1 - (b - t)) / 2 - t), text, font=f, fill=fill)


def hires(name, w, h, draw):
    """A texture drawn at four times its size and scaled down (crisp text at 32 px a block)."""
    k = 4
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 255))
    draw(img, ImageDraw.Draw(img), k)
    img = img.resize((w, h), Image.LANCZOS)
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def screws(d, k, w, h, colour=(120, 120, 116)):
    for x, y in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):
        d.ellipse([x * k - k, y * k - k, x * k + k, y * k + k], fill=colour)


# ======================================================================== Textures

def plate_textures():
    """Engraved plates: dark text on a worn off-white plate (the SERVER ROOM door's style); DATA HALL on blue."""
    for i, text in enumerate(PLATES):
        hall = text.startswith("DATA HALL")
        # (Round 4: the room plates are photoluminescent, a pale yellow-green that glows faintly in the dark, dark text on it)
        bg, fg = ((34, 62, 112), (232, 232, 222)) if hall else ((206, 214, 180), (26, 26, 30))

        def draw(img, d, k, text=text, bg=bg, fg=fg, hall=hall):
            w, h = img.width // k, img.height // k
            d.rectangle([0, 0, img.width, img.height], fill=(60, 60, 58))
            d.rectangle([k, k, img.width - k - 1, img.height - k - 1], fill=bg)
            if hall:
                text_center(d, (0, 3 * k, img.width, 16 * k), "DATA HALL", 12 * k, fg)
                text_center(d, (0, 14 * k, img.width, img.height - 3 * k), text[-1], 38 * k, fg)
            else:
                text_center(d, (3 * k, 0, img.width - 3 * k, img.height), text, 10 * k, fg)
            screws(d, k, w, h)
        hires(f"plate-{i}", 96, 64 if hall else 36, draw)
        # Grime over the plate
        img = Image.open(os.path.join(TEX, f"plate-{i}.png")).convert("RGBA")
        rng = random.Random(12300 + i)
        px = img.load()
        for _ in range(img.width * img.height // 9):
            x, y = rng.randrange(img.width), rng.randrange(img.height)
            r, g, b, a = px[x, y]
            k = rng.uniform(0.8, 0.95)
            px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k * 0.95), a)
        img.save(os.path.join(TEX, f"plate-{i}.png"))
        if hall:
            # (Round 4) The DATA HALL plate's letters are photoluminescent: their own cut-out layer, glowing faintly
            def glow(img, d, k, text=text):
                d.rectangle([0, 0, img.width, img.height], fill=(0, 0, 0, 0))
                text_center(d, (0, 3 * k, img.width, 16 * k), "DATA HALL", 12 * k, (206, 236, 196, 255))
                text_center(d, (0, 14 * k, img.width, img.height - 3 * k), text[-1], 38 * k, (206, 236, 196, 255))
            gk = 4
            g = Image.new("RGBA", (96 * gk, 64 * gk), (0, 0, 0, 0))
            glow(g, ImageDraw.Draw(g), gk)
            g = g.resize((96, 64), Image.LANCZOS)
            gp = g.load()
            for y in range(g.height):
                for x in range(g.width):
                    r, gg, b, a = gp[x, y]
                    gp[x, y] = (206, 236, 196, 255) if a >= 110 else (0, 0, 0, 0)
            g.save(os.path.join(TEX, f"plate-{i}-glow.png"))

    def auth(img, d, k):
        d.rectangle([0, 0, img.width, img.height], fill=(232, 228, 216))
        d.rectangle([0, 0, img.width, 14 * k], fill=(176, 30, 30))
        text_center(d, (0, 0, img.width, 14 * k), "AUTHORIZED", 7 * k, (250, 246, 236))
        text_center(d, (0, 15 * k, img.width, 30 * k), "PERSONNEL ONLY", 6 * k, (20, 20, 22))
        text_center(d, (0, 30 * k, img.width, 44 * k), "SERVER ROOMS", 5 * k, (70, 70, 72))
        screws(d, k, 64, 48)
    hires("plate-auth", 64, 48, auth)

    def fire(img, d, k):
        d.rectangle([0, 0, img.width, img.height], fill=(196, 30, 30))
        # The pictogram: an extinguisher, white
        d.rounded_rectangle([12 * k, 10 * k, 20 * k, 30 * k], radius=3 * k, fill=(250, 246, 240))
        d.rectangle([14 * k, 6 * k, 18 * k, 10 * k], fill=(250, 246, 240))
        d.line([18 * k, 7 * k, 25 * k, 12 * k], fill=(250, 246, 240), width=2 * k)
        text_center(d, (0, 31 * k, img.width, 39 * k), "FIRE", 7 * k, (250, 246, 240))
        text_center(d, (0, 38 * k, img.width, 46 * k), "EXTINGUISHER", 3 * k, (250, 246, 240))
    hires("sign-fire", 32, 48, fire)

    def evac(img, d, k):
        w, h = 64, 48
        d.rectangle([0, 0, img.width, img.height], fill=(70, 66, 60))
        d.rectangle([2 * k, 2 * k, (w - 2) * k, (h - 2) * k], fill=(236, 232, 220))
        d.rectangle([2 * k, 2 * k, (w - 2) * k, 9 * k], fill=(40, 120, 70))
        text_center(d, (0, 2 * k, img.width, 9 * k), "EVACUATION PLAN", 6 * k, (250, 250, 244))
        # A floor plan: the passages, the hall, the rooms in it, the way out in green, YOU ARE HERE in red
        line = (60, 60, 64)
        d.rectangle([6 * k, 13 * k, 58 * k, 44 * k], outline=line, width=k)
        for x in (18, 30, 44):
            d.line([x * k, 13 * k, x * k, 44 * k], fill=line, width=k)
        for y in (24, 34):
            d.line([6 * k, y * k, 58 * k, y * k], fill=line, width=k)
        d.line([8 * k, 42 * k, 8 * k, 16 * k], fill=(40, 150, 80), width=2 * k)
        d.line([8 * k, 16 * k, 28 * k, 16 * k], fill=(40, 150, 80), width=2 * k)
        d.ellipse([34 * k, 28 * k, 38 * k, 32 * k], fill=(200, 30, 30))
        d.text((39 * k, 27 * k), "YOU ARE HERE", font=font(4 * k), fill=(200, 30, 30))
    hires("sign-evac", 64, 48, evac)

    def exit_sign(lit):
        def draw(img, d, k):
            d.rectangle([0, 0, img.width, img.height], fill=(224, 224, 216))
            green = (60, 230, 120) if lit else (36, 70, 48)
            text_center(d, (0, 0, img.width - 10 * k, img.height), "EXIT", 12 * k, green)
            # The running man's arrow
            d.polygon([(img.width - 9 * k, 5 * k), (img.width - 3 * k, img.height // 2), (img.width - 9 * k, img.height - 5 * k)], fill=green)
        return draw
    hires("sign-exit-lit", 48, 20, exit_sign(True))
    hires("sign-exit-dead", 48, 20, exit_sign(False))

    def panel(img, d, k):
        d.rectangle([0, 0, img.width, img.height], fill=(150, 152, 150))
        d.rectangle([k, k, img.width - k - 1, img.height - k - 1], outline=(90, 92, 90), width=k)
        d.rectangle([5 * k, 4 * k, 27 * k, 13 * k], fill=(236, 200, 40))
        d.polygon([(8 * k, 12 * k), (11 * k, 5 * k), (14 * k, 12 * k)], outline=(20, 20, 20), width=k)
        text_center(d, (14 * k, 4 * k, 27 * k, 9 * k), "DANGER", 4 * k, (20, 20, 20))
        text_center(d, (14 * k, 8 * k, 27 * k, 13 * k), "480 V", 4 * k, (20, 20, 20))
        text_center(d, (0, 15 * k, img.width, 21 * k), "PDU-2  MAIN", 4 * k, (30, 30, 34))
        d.rectangle([24 * k, 26 * k, 26 * k, 34 * k], fill=(60, 60, 62))  # the latch
    hires("panel-pdu", 32, 40, panel)

    # The UPS: a dead LCD and its plate; the batteries' warning
    def ups(img, d, k):
        d.rectangle([0, 0, img.width, img.height], fill=(46, 48, 52))
        d.rectangle([6 * k, 4 * k, 26 * k, 12 * k], fill=(24, 30, 26))  # the LCD, dead
        d.rectangle([6 * k, 4 * k, 26 * k, 12 * k], outline=(90, 92, 96), width=k)
        for i, c in enumerate(((60, 40, 30), (40, 60, 30), (60, 60, 30))):
            d.ellipse([(8 + 5 * i) * k, 15 * k, (10 + 5 * i) * k, 17 * k], fill=c)
        d.rectangle([5 * k, 20 * k, 27 * k, 29 * k], fill=(236, 200, 40))
        text_center(d, (5 * k, 20 * k, 27 * k, 25 * k), "UPS 2", 4 * k, (20, 20, 20))
        text_center(d, (5 * k, 24 * k, 27 * k, 29 * k), "HIGH VOLTAGE", 3 * k, (20, 20, 20))
    hires("ups-upper", 32, 32, ups)

    def battery(img, d, k):
        d.rectangle([0, 0, img.width, img.height], fill=(40, 42, 46))
        for row in range(3):
            y = 3 + row * 9
            for col in range(3):
                x = 3 + col * 9
                d.rectangle([x * k, y * k, (x + 7) * k, (y + 7) * k], fill=(22, 22, 24))
                d.rectangle([(x + 1) * k, y * k, (x + 2) * k, (y + 1) * k], fill=(170, 40, 40))
                d.rectangle([(x + 5) * k, y * k, (x + 6) * k, (y + 1) * k], fill=(30, 30, 30))
        for i in range(0, 32, 2):  # the mesh door
            d.line([i * k, 0, i * k, img.height], fill=(70, 72, 76), width=k // 2)
    hires("battery-front", 32, 32, battery)

    def battery_upper(img, d, k):
        battery(img, d, k)
        d.rectangle([4 * k, 2 * k, 28 * k, 10 * k], fill=(236, 200, 40))
        text_center(d, (4 * k, 2 * k, 28 * k, 10 * k), "BATTERY - ACID", 3 * k, (20, 20, 20))
    hires("battery-upper", 32, 32, battery_upper)

    def crac(img, d, k):
        d.rectangle([0, 0, img.width, img.height], fill=(196, 194, 184))
        d.rectangle([4 * k, 3 * k, 18 * k, 11 * k], fill=(26, 30, 30))
        d.rectangle([4 * k, 3 * k, 18 * k, 11 * k], outline=(110, 110, 106), width=k)
        d.rectangle([21 * k, 3 * k, 28 * k, 11 * k], fill=(80, 82, 80))
        d.rectangle([4 * k, 15 * k, 28 * k, 21 * k], fill=(236, 232, 220))
        text_center(d, (4 * k, 15 * k, 28 * k, 21 * k), "CRAC 3", 5 * k, (20, 20, 24))
        for y in range(24, 31, 2):
            d.line([3 * k, y * k, 29 * k, y * k], fill=(110, 108, 100), width=k)
    hires("crac-upper", 32, 32, crac)

    for c in LETTERS:
        def rowend(img, d, k, c=c):
            d.rectangle([0, 0, img.width, img.height], fill=(40, 43, 48))
            d.rectangle([6 * k, 4 * k, 26 * k, 26 * k], fill=(226, 222, 208))
            text_center(d, (6 * k, 4 * k, 26 * k, 11 * k), "ROW", 5 * k, (30, 30, 34))
            text_center(d, (6 * k, 9 * k, 26 * k, 27 * k), c, 15 * k, (30, 30, 34))
        hires(f"rowend-{c.lower()}", 32, 32, rowend)


def note_textures():
    """Paper taped to the wall, in pencil: what someone wanted the next one to know."""
    for i, lines in enumerate(NOTES):
        def draw(img, d, k, lines=lines, i=i):
            d.rectangle([0, 0, img.width, img.height], fill=(222, 216, 196))
            for y in range(10, 64, 6):
                d.line([2 * k, y * k, 46 * k, y * k], fill=(186, 196, 210), width=k // 2)
            rng = random.Random(12400 + i)
            y = 8
            for ln in lines:
                f = font(9 * k if len(ln) <= 7 else 7 * k)
                d.text((4 * k + rng.uniform(-1, 1) * k, y * k), ln, font=f, fill=(48, 46, 50))
                y += 13
            d.rectangle([16 * k, 0, 32 * k, 4 * k], fill=(200, 196, 170))  # the tape
        hires(f"note-{i}", 48, 64, draw)


def flat_textures():
    rng = random.Random(12500)
    base = Image.open(os.path.join(TEX, "wall-base.png")).convert("RGBA")
    # The hall's letter stencilled on the paper in black, an arrow under it
    for c in LETTERS:
        img = base.copy().resize((128, 128), Image.NEAREST)
        d = ImageDraw.Draw(img)
        text_center(d, (0, 4, 128, 30), "HALL", 22, (30, 28, 26, 255))
        text_center(d, (0, 26, 128, 98), c, 66, (30, 28, 26, 255))
        d.rectangle([34, 104, 94, 112], fill=(30, 28, 26, 255))
        # Worn: speckle the paint back to the paper
        px = img.load()
        bpx = base.resize((128, 128), Image.NEAREST).load()
        for _ in range(1600):
            x, y = rng.randrange(128), rng.randrange(128)
            px[x, y] = bpx[x, y]
        img.save(os.path.join(TEX, f"stencil-{c.lower()}.png"))
    # The White Voids: a hairline crack, a grey smudge like a hand dragged down the wall
    white = Image.open(os.path.join(TEX, "void-white.png")).convert("RGBA")
    crack = white.copy().resize((64, 64), Image.NEAREST)
    px = crack.load()
    x, y = 30.0, 2.0
    while y < 62:
        for dx in range(2):
            xi = int(x) + dx
            if 0 <= xi < 64:
                px[xi, int(y)] = (64, 64, 66, 255) if dx == 0 else (150, 150, 152, 255)
        x += rng.uniform(-1.4, 1.4)
        y += 1
        if rng.random() < 0.08:  # a branch
            bx, by = x, y
            for _ in range(rng.randint(4, 10)):
                bx += rng.choice((-1, 1))
                by += 1
                if 0 <= bx < 64 and by < 64:
                    px[int(bx), int(by)] = (96, 96, 98, 255)
    crack.save(os.path.join(TEX, "void-crack.png"))
    smudge = white.copy().resize((64, 64), Image.NEAREST)
    px = smudge.load()
    for y in range(64):
        for x in range(64):
            for fx in (22, 28, 34, 40):
                d = abs(x - fx - (y - 10) * 0.05)
                if 10 < y < 54 and d < 2.2:
                    r, g, b, a = px[x, y]
                    k = 0.82 + 0.1 * (y - 10) / 44 + 0.03 * d
                    px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k), 255)
    smudge.save(os.path.join(TEX, "void-smudge.png"))
    # A glitched tile: a block of the white floor gone to coloured pixels
    floor = Image.open(os.path.join(TEX, "void-floor.png")).convert("RGBA")
    glitch = floor.copy()
    px = glitch.load()
    for y in range(6, 26):
        for x in range(4, 28):
            if rng.random() < 0.55:
                px[x, y] = rng.choice(((240, 30, 60), (30, 230, 90), (40, 60, 240), (10, 10, 10), (250, 250, 250))) + (255,)
    glitch.save(os.path.join(TEX, "void-glitch.png"))
    dead = canvas((168, 168, 166))
    rect(dead, 0, 0, 31, 0, (120, 120, 118))
    save(grain(dead, 12501, 3), "void-paneldead")

    # The skirting: a dark wooden board along the foot of the paper (and of the torn paper)
    for src, name in (("wall-base", "wall-skirt"), ("wall-rot", "wall-skirtrot"), ("wall-stained", "wall-skirtstain")):
        img = Image.open(os.path.join(TEX, src + ".png")).convert("RGBA")
        px = img.load()
        for y in range(25, 32):
            for x in range(32):
                c = (74, 50, 32) if y > 25 else (110, 80, 52)
                k = 1 + rng.uniform(-0.08, 0.08) - (0.25 if (x + 3 * y) % 17 == 0 else 0)
                if name == "wall-skirtrot" and 10 < x < 19 and y > 27:
                    c, k = (30, 24, 18), 1
                px[x, y] = shade(c, k) + (255,)
        img.save(os.path.join(TEX, name + ".png"))

    # The floor: a cable port (a brush grommet, cable tails), and a wet patch under a leak
    clean = Image.open(os.path.join(TEX, "floor-clean.png")).convert("RGBA")
    port = clean.copy()
    px = port.load()
    for y in range(20, 27):
        for x in range(5, 12):
            px[x, y] = (18, 18, 20, 255) if (x + y) % 2 else (34, 34, 38, 255)
    for x in range(5, 12):
        px[x, 19] = (90, 90, 92, 255)
        px[x, 27] = (90, 90, 92, 255)
    for (x, c) in ((7, (40, 70, 160)), (9, (190, 150, 40)), (10, (150, 150, 150))):
        for y in range(23, 29):
            px[x, y] = c + (255,)
    port.save(os.path.join(TEX, "floor-port.png"))
    dirty = Image.open(os.path.join(TEX, "floor-dirty.png")).convert("RGBA")
    wet = dirty.copy()
    px = wet.load()
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 15, (y - 17) * 1.3) + 2.5 * math.sin(x * 0.7) * math.cos(y * 0.5)
            if d < 13:
                r, g, b, a = px[x, y]
                k = 0.82 if d < 11 else 0.7
                px[x, y] = (clamp(r * k * (0.95 if d < 11 else 1.0)), clamp(g * k * (0.97 if d < 11 else 0.9)), clamp(b * k * (1.0 if d < 11 else 0.75)), 255)
                if d < 9 and (x * 7 + y * 3) % 23 == 0:
                    px[x, y] = (200, 200, 196, 255)  # a glint
    wet.save(os.path.join(TEX, "floor-wet.png"))


def prop_textures():
    rng = random.Random(12600)
    save(grain(canvas((46, 48, 52)), 12601, 4), "ups-side")
    low = canvas((46, 48, 52))
    for y in range(4, 26, 2):
        rect(low, 4, y, 27, y, (24, 25, 28))
    rect(low, 0, 29, 31, 31, (28, 29, 32))
    save(grain(low, 12602, 3), "ups-lower")
    gutted = canvas((20, 20, 22))
    for row in range(4):
        rect(gutted, 3, 3 + row * 7, 28, 7 + row * 7, (30, 30, 34))
        for col in range(3):
            if rng.random() < 0.7:
                rect(gutted, 4 + col * 8, 4 + row * 7, 9 + col * 8, 7 + row * 7, (16, 16, 18))
                rect(gutted, 5 + col * 8, 4 + row * 7, 5 + col * 8, 4 + row * 7, (170, 40, 40))
    save(gutted, "ups-open")
    louvre = canvas((196, 194, 184))
    for y in range(3, 30, 3):
        rect(louvre, 3, y, 28, y + 1, (90, 90, 86))
    save(grain(louvre, 12604, 3), "crac-lower")
    # Behind the panel: the coil's fins and a fan, dust on everything
    coil = canvas((60, 66, 64))
    for x in range(2, 30, 2):
        rect(coil, x, 2, x, 14, (120, 128, 124))
    for y in range(17, 30):
        for x in range(6, 26):
            d = math.hypot(x - 15.5, y - 23.5)
            if d < 6.5:
                coil.load()[x, y] = ((30, 30, 32) if int(math.atan2(y - 23.5, x - 15.5) * 3) % 2 else (90, 92, 94)) + (255,)
    save(grain(coil, 12615, 4), "crac-open")
    duct = canvas((150, 154, 156))
    for y in range(0, S, 8):
        rect(duct, 0, y, 31, y, (110, 114, 116))
    save(grain(duct, 12605, 5, 6), "duct")
    save(grain(canvas((168, 34, 30)), 12606, 6), "extinguisher")
    save(grain(canvas((92, 92, 90)), 12614, 6, 10), "plenum")
    # The CRAC's sides: panels with seams, a latch and a vent strip
    side = canvas((196, 194, 184))
    rect(side, 15, 0, 15, 31, (150, 148, 140))
    rect(side, 0, 0, 31, 0, (150, 148, 140))
    for x in (13, 17):
        rect(side, x, 14, x, 17, (90, 90, 86))
    for y in range(24, 30, 2):
        rect(side, 3, y, 12, y, (120, 118, 110))
    save(grain(side, 12603, 4, 6), "crac-side")
    save(grain(canvas((24, 24, 26)), 12607, 3), "black")
    save(grain(canvas((214, 182, 40)), 12608, 6), "bucket")
    mop = canvas((196, 190, 170))
    for x in range(0, S, 3):
        rect(mop, x, 0, x, 31, (150, 144, 126))
    save(mop, "mophead")
    save(grain(canvas((140, 112, 70)), 12609, 5), "wood-handle")
    save(grain(canvas((128, 130, 132)), 12610, 5), "steel-grey")
    paper = canvas((230, 226, 214))
    for y in range(5, 30, 3):
        rect(paper, 3, y, rng.randint(14, 28), y, (120, 120, 130))
    save(grain(paper, 12611, 3), "paper-sheet")
    box_ = canvas((168, 128, 82))
    rect(box_, 0, 14, 31, 17, (196, 180, 140))
    rect(box_, 6, 22, 25, 27, (236, 232, 220))
    save(grain(box_, 12612, 5), "box-cardboard")
    conduit = canvas((156, 158, 160))
    for x in range(0, S, 16):
        rect(conduit, x, 0, x + 1, 31, (110, 112, 114))
    save(grain(conduit, 12613, 4), "conduit")
    # A corridor seen on a wall screen, a few frames torn sideways by noise (the brief's corrupted screen)
    img = canvas((8, 12, 10))
    px = img.load()
    for y in range(S):
        for x in range(S):
            # A one-point perspective of a corridor: the floor and ceiling lines converge on the middle
            dx, dy = abs(x - 16), abs(y - 15)
            c = (40, 52, 44)
            if dy > dx * 0.7:
                c = (70, 90, 76) if y > 15 else (52, 66, 56)
            if dx < 3 and dy < 3:
                c = (6, 8, 6)
            px[x, y] = c + (255,)
    for _ in range(6):  # torn bands
        y0, shift = rng.randrange(S), rng.randint(-8, 8)
        row = [px[(x - shift) % S, y0] for x in range(S)]
        for x in range(S):
            px[x, y0] = row[x]
            if rng.random() < 0.2:
                px[x, y0] = rng.choice(((200, 40, 60), (40, 220, 120), (230, 230, 230))) + (255,)
    for y in range(0, S, 2):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * 0.7), clamp(g * 0.7), clamp(b * 0.7), 255)
    save(img, "screen-glitch")


# ======================================================================== Shapes

def ups_shape(part, state):
    front = "ups-lower" if part == "lower" else "ups-upper"
    if state == "open":
        front = "ups-open"
    els = [box("Body", (1, 0, 2), (15, 16 if part == "lower" else 15, 15), {"front": front, "side": "ups-side", "top": "ups-side", "back": "ups-side", "bottom": "ups-side"})]
    if state == "open" and part == "lower":
        # The front panel torn off, leaning against the cabinet
        els.append(box("Door", (1.5, 0, -2), (14.5, 15, -1), {"front": "ups-lower", "back": "ups-side", "side": "ups-side", "top": "ups-side", "bottom": "ups-side"},
                       rot=(-14, 0, 0), origin=(8, 0, -1.5)))
    return shape(f"l120-ups-{part}-{state}", els)


def battery_shape(part):
    return shape(f"l120-battery-{part}", [
        box("Body", (1, 0, 2), (15, 16 if part == "lower" else 14, 15),
            {"front": "battery-front" if part == "lower" else "battery-upper", "side": "ups-side", "top": "ups-side", "back": "ups-side", "bottom": "ups-side"}),
        box("Handle", (12.5, 6, 1.4), (13.5, 10, 2), "steel-grey", faces=("north", "east", "west", "up", "down")),
    ])


def crac_shape(part):
    if part == "duct":
        return shape("l120-crac-duct", [box("Duct", (3, 0, 4), (13, 16, 13), "duct", faces=("north", "east", "south", "west"))])
    front = {"lower": "crac-lower", "loweropen": "crac-open"}.get(part, "crac-upper")
    els = [box("Body", (0.5, 0, 2), (15.5, 16, 15.5), {"front": front, "side": "crac-side", "top": "crac-side", "back": "crac-side", "bottom": "crac-side"})]
    if part == "loweropen":
        # Its louvred panel pulled off and dropped in front of it
        els.append(box("Panel", (1, 0, -3), (15, 0.8, 12), {"top": "crac-lower", "side": "crac-side", "bottom": "crac-side"},
                       faces=("up", "north", "east", "west"), rot=(0, 9, 0)))
    if part == "upper":
        els.append(box("Collar", (2.5, 15.9, 3.5), (13.5, 16, 13.5), "duct", faces=("up",)))
    else:
        els.append(box("Plinth", (0.5, 0, 1.5), (15.5, 1, 2), "black", faces=("north", "east", "west", "up")))
    return shape("l120-crac-" + part, els)


def kvm_shape():
    els = []
    for i, (x, z) in enumerate(((2, 3), (13, 3), (2, 12), (13, 12))):
        els.append(box(f"Post{i}", (x, 1.5, z), (x + 1, 11, z + 1), "steel-grey", faces=("north", "east", "south", "west")))
        els.append(box(f"Wheel{i}", (x - 0.2, 0, z - 0.2), (x + 1.2, 1.5, z + 1.2), "black"))
    els += [
        box("Low", (2, 3, 3), (14, 3.6, 13), "steel-grey"),
        box("Top", (2, 10.4, 3), (14, 11, 13), "steel-grey"),
        box("Monitor", (3.5, 11, 8), (12.5, 16, 12), {"front": "screen-dead", "side": "crt-case", "back": "crt-case", "top": "crt-case", "bottom": "crt-case"}, uv=None),
        box("Keyboard", (4, 11, 4), (12, 11.6, 6.5), {"top": "keyboard", "side": "crt-case", "bottom": "crt-case"}),
        box("Box", (3, 3.6, 4), (10, 7, 11), "box-cardboard"),
        box("Cable", (6, 0, -4), (6.6, 0.4, 4), "tray-cable", faces=("up", "east", "west", "north")),
    ]
    return shape("l120-kvm", els)


def mop_shape():
    return shape("l120-mop", [
        box("Bucket", (4, 0, 4), (12, 6, 12), "bucket", faces=("north", "east", "south", "west", "down")),
        box("Water", (4.5, 4.5, 4.5), (11.5, 5, 11.5), "black", faces=("up",)),
        box("Wringer", (4.5, 6, 4.5), (11.5, 8, 7), "bucket"),
        box("Head", (6, 2.5, 7.5), (10, 5.5, 11), "mophead"),
        box("Handle", (7.7, 5, 8.8), (8.5, 22, 9.6), "wood-handle", faces=("north", "east", "south", "west", "up"), rot=(10, 0, -8), origin=(8, 5, 9)),
    ])


def debris_shape():
    rng = random.Random("debris")
    els = []
    for i in range(3):
        x, z, w, d = rng.uniform(1, 7), rng.uniform(1, 8), rng.uniform(5, 8), rng.uniform(4, 7)
        els.append(box(f"Piece{i}", (x, 0, z), (x + w, 0.6, z + d), {"top": "ceiling-tile", "bottom": "ceiling-tile", "side": "ceiling-broken"},
                       rot=(0, rng.choice((-30, 12, 40)), rng.choice((0, 0, 6))), faces=("up", "north", "south", "east", "west")))
    for i in range(5):
        x, z = rng.uniform(1, 14), rng.uniform(1, 14)
        els.append(box(f"Bit{i}", (x, 0, z), (x + 1, 0.5, z + 1), "ceiling-tile", faces=("up", "north", "east")))
    return shape("l120-debris", els)


def paper_shape():
    return shape("l120-paper", [box("Sheet", (5, 0, 4), (11, 0.1, 12), "paper-sheet", faces=("up",), rot=(0, 23, 0), uv=(0, 0, 16, 16))])


def rowend_shape(part, letter=None):
    els = [box("Body", (0.5, 0, 0.5), (15.5, 16, 15.5), {"front": f"rowend-{letter.lower()}" if letter else "rack-side", "side": "rack-side",
                                                            "top": "rack-top", "back": "rack-side", "bottom": "rack-top"}, uv=None)]
    if letter:
        els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    return shape(f"l120-rowend-{part}" + (f"-{letter.lower()}" if letter else ""), els)


def shelf_shape(part):
    rng = random.Random("shelf-" + part)
    els = []
    for i, (x, z) in enumerate(((0.5, 1), (14.5, 1), (0.5, 14), (14.5, 14))):
        els.append(box(f"Post{i}", (x, 0, z), (x + 1, 16, z + 1), "steel-grey", faces=("north", "east", "south", "west")))
    for j, y in enumerate((1, 8) if part == "lower" else (0, 7, 14)):
        els.append(box(f"Shelf{j}", (0.5, y, 1), (15.5, y + 0.6, 15), "steel-grey"))
        if y < 14:
            x = 1.5
            while x < 13:
                w = rng.uniform(3, 5)
                if rng.random() < 0.75:
                    tex_ = rng.choice(("box-cardboard", "box-cardboard", "rack-front"))
                    h = rng.uniform(3, 5.5)
                    els.append(box(f"Box{j}{int(x)}", (x, y + 0.6, rng.uniform(2, 4)), (min(14.5, x + w), y + 0.6 + h, 14), tex_))
                x += w + 0.4
    return shape("l120-shelf-" + part, els)


def floorhole_shape():
    els = [
        # The plenum's floor (the slab), cables run across it, pedestals at the corners, the stringers round the top
        box("Slab", (0, 0, 0), (16, 0.2, 16), "plenum", faces=("up",)),
        box("CablesA", (0, 0.2, 3), (16, 2.2, 7), "tray-cable", faces=("up", "north", "south")),
        box("CablesB", (6, 0.2, 0), (9, 1.6, 16), "wire-blue", faces=("up", "east", "west")),
        box("CablesC", (11, 0.2, 9), (16, 1.2, 12), "wire-grey", faces=("up", "north", "south", "west")),
    ]
    for i, (x, z) in enumerate(((0, 0), (14, 0), (0, 14), (14, 14))):
        els.append(box(f"Ped{i}", (x, 0, z), (x + 2, 14.5, z + 2), "steel-grey", faces=("north", "east", "south", "west")))
    els += [
        box("LipN", (0, 14.5, 0), (16, 16, 1), {"top": "floor-clean", "side": "steel-grey"}, faces=("up", "south")),
        box("LipS", (0, 14.5, 15), (16, 16, 16), {"top": "floor-clean", "side": "steel-grey"}, faces=("up", "north")),
        box("LipW", (0, 14.5, 1), (1, 16, 15), {"top": "floor-clean", "side": "steel-grey"}, faces=("up", "east")),
        box("LipE", (15, 14.5, 1), (16, 16, 15), {"top": "floor-clean", "side": "steel-grey"}, faces=("up", "west")),
        # The sides of the hole, facing into it
        box("SideN", (0, 0.2, 0), (16, 14.5, 0.05), "plenum", faces=("south",)),
        box("SideS", (0, 0.2, 15.95), (16, 14.5, 16), "plenum", faces=("north",)),
        box("SideW", (0, 0.2, 0), (0.05, 14.5, 16), "plenum", faces=("east",)),
        box("SideE", (15.95, 0.2, 0), (16, 14.5, 16), "plenum", faces=("west",)),
    ]
    return shape("l120-floorhole", els)


# ---- The wall dressing: the wall block itself with something on its face (north) ----

def wall(base, front=None):
    return box("Wall", (0, 0, 0), (16, 16, 16), {"north": front or base, "east": base, "south": base, "west": base, "up": base, "down": base}, uv=(0, 0, 16, 16))


def deco_elements(kind):
    """(base wall texture, front face texture, elements on the north face) of a decoration kind."""
    if kind.startswith("plate-"):
        i = int(kind[6:])
        hall = i >= 12
        y0, y1 = (3, 11) if hall else (6, 10.5)
        els = [box("Plate", (2, y0, -0.4), (14, y1, 0), f"plate-{i}", faces=("north", "east", "west", "up", "down"), uv=(0, 0, 16, 16))]
        if hall:
            els.append(box("Glow", (2, y0, -0.45), (14, y1, -0.4), f"plate-{i}-glow", faces=("north",), uv=(0, 0, 16, 16), glow=90))
        else:
            els[0]["faces"]["north"]["glow"] = 60
        return "wall-base", None, els
    if kind == "auth":
        return "wall-base", None, [box("Plate", (3, 4, -0.4), (13, 11.5, 0), "plate-auth", faces=("north", "east", "west", "up", "down"), uv=(0, 0, 16, 16))]
    if kind.startswith("note-"):
        return "wall-base", None, [box("Note", (5, 3, -0.15), (11, 11, 0), kind, faces=("north",), uv=(0, 0, 16, 16), rot=(0, 0, 4 if kind[-1] in "02" else -5))]
    if kind == "fire-lower":
        return "wall-base", None, [
            box("Bracket", (6.5, 4, -0.6), (9.5, 6, 0), "black"),
            box("Body", (6, 4.5, -3.6), (10, 14, -0.6), "extinguisher", faces=("north", "east", "west", "up", "down")),
            box("Valve", (7, 14, -2.6), (9, 15.5, -1.6), "steel-grey"),
            box("Handle", (7.5, 15.5, -3.6), (8.5, 16, -0.8), "black"),
            box("Hose", (9.6, 6, -2.6), (10.4, 15, -1.8), "black", faces=("north", "east", "west")),
        ]
    if kind == "fire-upper":
        return "wall-base", None, [box("Sign", (5, 2, -0.3), (11, 11, 0), "sign-fire", faces=("north", "east", "west", "up", "down"), uv=(0, 0, 16, 16))]
    if kind.startswith("cables-"):
        part = kind[7:]
        els = []
        for i, (x, t) in enumerate(((5.5, "tray-cable"), (6.6, "wire-blue"), (7.7, "tray-cable"), (8.8, "wire-grey"), (9.9, "tray-cable"))):
            y0 = 0 if part != "lower" else 0.5
            els.append(box(f"C{i}", (x, y0, -1.4 + 0.15 * (i % 2)), (x + 1, 16, -0.2), t, faces=("north", "east", "west")))
            if part == "lower":
                els.append(box(f"F{i}", (x, 0, -3 - i * 0.6), (x + 1, 0.5, -0.2), t, faces=("up", "east", "west", "north")))
        for y in ((4, 12) if part != "lower" else (6, 13)):
            els.append(box(f"Tie{y}", (5.3, y, -1.6), (11, y + 0.5, -0.1), "black", faces=("north", "east", "west", "up", "down")))
        if part == "upper":
            els.append(box("Clamp", (4.5, 13, -2), (11.5, 14, 0), "steel-grey"))
        return "wall-base", None, els
    if kind.startswith("screens-"):
        _, look, part = kind.split("-")
        screen = {"glitch": "screen-glitch", "smashed": "screen-smashed"}.get(look, "screen-dead")
        y0, y1 = (2, 15.5) if part == "lower" else (0.5, 14)
        return "wall-base", None, [
            box("Bezel", (0, y0, -1), (16, y1, 0), "black", faces=("north", "east", "west", "up", "down")),
            box("Screen", (0.8, y0 + 0.8, -1.05), (15.2, y1 - 0.8, -1), screen, faces=("north",), uv=(0, 0, 16, 16), glow=120 if look == "glitch" else 0),
            box("Mount", (6, y0 + 3, -0.01), (10, y1 - 3, 0), "steel-grey", faces=("north",)),
        ]
    if kind == "evac":
        return "wall-base", None, [box("Frame", (2, 3, -0.5), (14, 12, 0), "sign-evac", faces=("north", "east", "west", "up", "down"), uv=(0, 0, 16, 16))]
    if kind.startswith("stencil-"):
        return "wall-base", f"stencil-{kind[-1]}", []
    if kind == "conduit":
        return "wall-base", None, [
            box("Pipe", (0, 11, -1.4), (16, 12.4, -0.2), "conduit", faces=("north", "up", "down")),
            box("Pipe2", (0, 8.8, -1.0), (16, 9.8, -0.2), "conduit", faces=("north", "up", "down")),
            box("Clip", (7, 8.5, -1.6), (8, 12.8, 0), "steel-grey", faces=("north", "east", "west", "up", "down")),
        ]
    if kind.startswith("exit-"):
        lit = kind == "exit-lit"
        return "wall-base", None, [
            box("Box", (3, 1, -2.2), (13, 6, -0.2), {"front": "sign-exit-lit" if lit else "sign-exit-dead", "side": "crac-side", "top": "crac-side", "bottom": "crac-side"},
                faces=("north", "east", "west", "up", "down"), glow=200 if lit else 0, uv=None),
            box("Back", (3.5, 1.5, -0.2), (12.5, 5.5, 0), "steel-grey", faces=("north",)),
        ]
    if kind == "panel":
        return "wall-base", None, [
            box("Panel", (3, 1, -1.6), (13, 14, 0), {"front": "panel-pdu", "side": "steel-grey", "top": "steel-grey", "bottom": "steel-grey"}, faces=("north", "east", "west", "up", "down"), uv=None),
            box("Conduit", (7, 14, -1.2), (9, 16, -0.2), "conduit", faces=("north", "east", "west")),
        ]
    if kind == "crack":
        return "void-white", "void-crack", []
    if kind == "smudge":
        return "void-white", "void-smudge", []
    raise ValueError(kind)


DECO_KINDS = ([f"plate-{i}" for i in range(len(PLATES))] + ["auth"] + [f"note-{i}" for i in range(len(NOTES))]
              + ["fire-lower", "fire-upper", "cables-lower", "cables-mid", "cables-upper"]
              + [f"screens-{look}-{part}" for look in ("dead", "glitch", "smashed") for part in ("lower", "upper")]
              + ["evac"] + [f"stencil-{c.lower()}" for c in LETTERS] + ["conduit", "exit-dead", "exit-lit", "panel", "crack", "smudge"])


def fix_uvs(els):
    """Faces whose uv was left to box(): a face with a whole texture of its own (signs, labels) maps it whole."""
    for el in els:
        for f in el["faces"].values():
            if f["texture"][1:] in ("sign-exit-lit", "sign-exit-dead", "panel-pdu") and f is el["faces"].get("north"):
                f["uv"] = [0, 0, 16, 16]
    return els


def blocktypes():
    # The UPS, battery and cooling cabinets: two high, the duct a third
    shapes = {}
    for part in ("lower", "upper"):
        for state in ("whole", "open"):
            base = ups_shape(part, state)
            for s in SIDES:
                shapes[f"l120-ups-{part}-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l120-ups", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": ["whole", "open"]}] + SIDED, shapes,
               "Level 120: a UPS cabinet, two high, its front to the side: whole (a dead display, UPS 2, HIGH VOLTAGE) or torn open "
               "(the batteries showing, the front panel against it). Salvage: wire, brackets",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("scrapwire", 0.5, 0.4), ("metalbracket", 0.5, 0.4))}, inventory="l120-ups-lower-whole-north")
    shapes = {}
    for part in ("lower", "upper"):
        base = battery_shape(part)
        for s in SIDES:
            shapes[f"l120-battery-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l120-battery", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: a battery cabinet, two high: strings of sealed batteries behind a mesh door, BATTERY - ACID. Salvage: brackets",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("metalbracket", 0.5, 0.4))}, inventory="l120-battery-lower-north")
    shapes = {}
    for part in ("lower", "loweropen", "upper", "duct"):
        base = crac_shape(part)
        for s in SIDES:
            shapes[f"l120-crac-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    duct = (0.18, 0, 0.25, 0.82, 1, 0.82)
    json_block("l120-crac", [{"code": "part", "states": ["lower", "loweropen", "upper", "duct"]}] + SIDED, shapes,
               "Level 120: a cooling unit (CRAC 3), two high, louvres below and its control panel above, and its duct up into the ceiling. Salvage: brackets, wire",
               {"collisionboxByType": {"*-duct-*": cuboid(duct), "*": cuboid(FULL)}, "selectionboxByType": {"*-duct-*": cuboid(duct), "*": cuboid(FULL)}},
               extra={"drops": drops(("metalbracket", 0.5, 0.4), ("scrapwire", 0.3, 0.3))}, inventory="l120-crac-lower-north")

    one = (0.1, 0, 0.1, 0.9, 1, 0.9)
    json_block("l120-kvm", SIDED, {f"l120-kvm-{s}": {"base": kvm_shape(), "rotateY": ROTATE[s]} for s in SIDES},
               "Level 120: a KVM cart, a trolley with a monitor and keyboard on it and a box underneath, a cable trailing. Salvage: glass, wire",
               {"collisionbox": cuboid(one), "selectionbox": cuboid(one)},
               extra={"drops": drops(("glassshard", 0.4, 0.3), ("scrapwire", 0.3, 0.3))}, inventory="l120-kvm-north")
    low = (0.25, 0, 0.25, 0.75, 0.5, 0.75)
    json_block("l120-mop", SIDED, {f"l120-mop-{s}": {"base": mop_shape(), "rotateY": ROTATE[s]} for s in SIDES},
               "Level 120: a yellow mop bucket, its wringer and mop: a cleaner's, left behind",
               {"collisionbox": cuboid(low), "selectionbox": cuboid((0.25, 0, 0.25, 0.75, 1, 0.75))},
               extra={"resistance": 1}, inventory="l120-mop-north")
    json_block("l120-debris", SIDED, {f"l120-debris-{s}": {"base": debris_shape(), "rotateY": ROTATE[s]} for s in SIDES},
               "Level 120: a ceiling tile fallen to the floor in pieces (walked over), the hole it left above",
               {"collisionbox": None, "selectionbox": cuboid((0, 0, 0, 1, 0.1, 1))},
               extra={"resistance": 0.5}, sounds=STONE, inventory="l120-debris-north")
    json_block("l120-paper", SIDED, {f"l120-paper-{s}": {"base": paper_shape(), "rotateY": ROTATE[s]} for s in SIDES},
               "Level 120: a sheet of paper on the floor, a few lines on it nobody can read (walked over)",
               {"collisionbox": None, "selectionbox": cuboid((0.25, 0, 0.2, 0.75, 0.05, 0.8))},
               extra={"resistance": 0.2}, sounds=WOOD, inventory="l120-paper-north")
    shapes = {}
    for s in SIDES:
        shapes[f"l120-rowend-lower-{s}"] = {"base": rowend_shape("lower"), "rotateY": ROTATE[s]}
        for c in LETTERS:
            shapes[f"l120-rowend-{c.lower()}-{s}"] = {"base": rowend_shape("upper", c), "rotateY": ROTATE[s]}
    json_block("l120-rowend", [{"code": "part", "states": ["lower"] + [c.lower() for c in LETTERS]}] + SIDED, shapes,
               "Level 120: the end panel of a bank of racks, two high (lower; the upper with its row letter, a-h, to the side). Salvage: brackets",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("metalbracket", 0.4, 0.3))}, inventory="l120-rowend-a-north")
    shapes = {}
    for part in ("lower", "upper"):
        base = shelf_shape(part)
        for s in SIDES:
            shapes[f"l120-shelf-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l120-shelf", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: steel shelving, two high, boxed drives and caddies on it. Salvage: brackets, wire",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"drops": drops(("metalbracket", 0.5, 0.4), ("scrapwire", 0.3, 0.3))}, inventory="l120-shelf-lower-north")
    hole = (0, 0, 0, 1, 0.5, 1)
    json_block("l120-floorhole", [{"code": "kind", "states": ["open"]}], {"*": {"base": floorhole_shape()}},
               "Level 120: a raised-floor panel lifted out, the plenum under it (pedestals, cables): half a block down",
               {"collisionbox": cuboid(hole), "selectionbox": cuboid((0, 0, 0, 1, 1, 1))},
               extra={"resistance": 6, "drops": drops(("scrapwire", 0.3, 0.3))}, inventory="l120-floorhole-open")

    # The wall dressing
    shapes = {}
    for kind in DECO_KINDS:
        base, front, els = deco_elements(kind)
        name = shape(f"l120-walldeco-{kind}", fix_uvs([wall(base, front)] + els))
        for s in SIDES:
            shapes[f"l120-walldeco-{kind}-{s}"] = {"base": name, "rotateY": ROTATE[s]}
    full = cuboid((0, 0, 0, 1, 1, 1))
    data_extra = {
        "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorptionByType": {"*-exit-lit-*": 0, "*-screens-glitch-*": 0, "*": 99},
        "lightHsvByType": {"*-exit-lit-*": [0, 6, 2], "*-screens-glitch-*": [24, 3, 1]}, "resistance": 6,
        "dropsByType": {"*-fire-lower-*": drops(("metalbracket", 0.3, 0)), "*-screens-*": drops(("glassshard", 0.5, 0.3)), "*": []},
    }
    json_block("l120-walldeco", [{"code": "kind", "states": DECO_KINDS}] + SIDED, shapes,
               "Level 120: the wall (yellow paper on rotting boards, or a White Void's white) with something on its face, to the side: the plates "
               "beside the doors, AUTHORIZED PERSONNEL ONLY, notes taped up, a fire point, cables down the wall, a wall of screens, an evacuation "
               "plan, the hall's stencilled letter, conduit, EXIT signs over the doorways, an electrical panel; a crack, a smudge",
               {"collisionbox": full, "selectionbox": full}, sounds=WOOD, extra=data_extra, inventory="l120-walldeco-plate-0-north")


def main():
    plate_textures()
    note_textures()
    flat_textures()
    prop_textures()
    blocktypes()
    print("Level 120 round 3:", len(DECO_KINDS), "wall dressings; textures in", os.path.relpath(TEX))


if __name__ == "__main__":
    main()
