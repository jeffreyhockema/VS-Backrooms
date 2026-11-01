"""Level 15, "Futuristic Halls" (experimental), round 3's blocks (the detailed visual pass, 2026-11-01): signs and the
furniture of the rooms added that round. Run after gen_15.py and
gen_15_links.py (it reads their textures, and redraws the ESCAPE panels deco-escape and deco-escapelive at 64 px):
    python tools/gen_15_r3.py      (under tools/locked.sh run)

    l15-sign        a white wall block with one face dressed (64 px a block where it carries text): the rooms' name
                    plates by their doors, AUTHORIZED PERSONNEL ONLY, DECONTAMINATION, HIGH VOLTAGE, a blank steel plate,
                    a service hatch, a grille with pipes behind it, the lift doors (left and right leaves, three high), the
                    lift's floor indicator (two halves) and call panel, the canteen's menu board (three wide), the halls'
                    band in each hall line's colour; cubes
    l15-floormark   the halls' ceramic floor with a line of the hall's colour down its middle, a chevron every 16 blocks
    l15-hangsign    a glowing sign hung from the ceiling across a main hall before each crossing, three blocks wide, the
                    hall's name on both faces (lit; off in the dark); JSON shapes
    l15-bunk        the upper bunk over a dormitory's cot (head, foot; posts down to the floor)
    l15-riser       the lecture hall's stepped floor (half, full); l15-seat: a row seat with a back and a writing tablet
                    (on the floor, or on a half step)
    l15-serve       the canteen's serving line: steel wells, trays, the till end; a glass sneeze guard over it
    l15-growrack    a hydroponics rack of dead plants under grow lights (lower, upper; lit, off)
    l15-dock        a robot charging dock with a powered-down Robo-Man standing in it (lower, upper; lit, dead)
    l15-tray        a cable tray hung along the top of a side corridor (we, ns)

Lettering: Bahnschrift (a DIN) bold, else Arial Narrow bold, else PIL's own. All text is the facility's, invented.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import matlib as M
from modelkit import box
from gen_15 import (BLOCKS, GRAPHITE, INK, METAL, ROOT, ROTATE, S, SHAPES, SIDES, STONE, TEX, CLOTH, WOOD, GLASS, WAYLINE,
                    blend, cuboid, json_block, rect, save, shape, tex, write_json)

FONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
B = 64  # px a block for the faces that carry text

# The hall lines' colours (the wayfinding: each main hall line its own, on its band, its floor line and chevrons)
LINE_COLOURS = [WAYLINE, (232, 172, 60), (112, 204, 122), (176, 136, 226)]

# The rooms' name plates, in the order of WorldLayout.L15Codes' letters (H e M D K C L S, then F R G)
PLATES = [("lab", "LABORATORY"), ("storage", "STORAGE"), ("machine", "MACHINE\nROOM"), ("dorm", "DORMITORY"),
          ("kitchen", "KITCHEN"), ("control", "CONTROL\nROOM"), ("lecture", "LECTURE\nHALL"), ("blank", ""),
          ("canteen", "CANTEEN"), ("medical", "MEDICAL"), ("hydro", "HYDRO-\nPONICS")]
# The hall signs' names (gen_15.HALLS, in the same order)
from gen_15 import HALLS  # noqa: E402


def font(size, condensed=False):
    names = (["bahnschrift.ttf", "ARIALNB.TTF", "arialbd.ttf"], b"Bold Condensed" if condensed else b"Bold")
    for n in names[0]:
        try:
            f = ImageFont.truetype(os.path.join(FONTS, n), size)
            try:
                f.set_variation_by_name(names[1])
            except Exception:
                pass
            return f
        except OSError:
            continue
    return ImageFont.load_default()


def draw_text(img, box_, s, colour, max_px, condensed=False, k=4):
    """Draws s (lines split on '\n') centred in box_ (x0, y0, x1, y1) of img, as large as fits (cap height at most
    max_px), drawn four times over and shrunk so the edges stay clean."""
    x0, y0, x1, y1 = box_
    lines = s.split("\n")
    px = max_px * k
    while px > 4:
        f = font(px, condensed)
        cap = f.getbbox("H")[3] - f.getbbox("H")[1]
        lh = cap * 1.5
        widths = [f.getlength(line) for line in lines]
        th = cap + lh * (len(lines) - 1)
        if max(widths) <= (x1 - x0) * k and th <= (y1 - y0) * k:
            break
        px -= 1
    W, H = (x1 - x0) * k, (y1 - y0) * k
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    top = (H - th) / 2
    for i, line in enumerate(lines):
        d.text(((W - widths[i]) / 2, top + i * lh - f.getbbox("H")[1]), line, font=f, fill=255)
    m = m.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    layer = Image.new("RGBA", m.size, tuple(colour[:3]) + (255,))
    region = img.crop((x0, y0, x1, y1)).convert("RGBA")
    region.paste(layer, (0, 0), m)
    img.paste(region.convert(img.mode), (x0, y0))


def big_panel():
    """The white wall panel at 64 px a block (the 32 px one doubled, so it meets the walls round it)."""
    return Image.open(os.path.join(TEX, "wall-panel.png")).convert("RGBA").resize((B, B), Image.NEAREST)


def bevel(img, b, s=0.2):
    M.bevel(img, b, strength=s)


# ======================================================================== l15-sign textures

def plate_textures():
    for i, (code, name) in enumerate(PLATES):
        img = big_panel()
        if code == "blank":
            # A brushed steel plate with nothing on it (the bare rooms, the crematorium, the star door: no one named them)
            steel = M.brushed_metal(seed=15700, size=64, base=(170, 176, 182), direction="h", streak=3, sheen=6).crop((0, 0, 44, 20))
            img.paste(steel, (10, 20))
            bevel(img, (10, 20, 54, 40), 0.25)
            for sx, sy in ((12, 22), (51, 22), (12, 37), (51, 37)):
                rect(img, sx, sy, sx + 1, sy + 1, (110, 114, 118))
            save(img, "sign-plate-blank")
            continue
        rect(img, 6, 14, 57, 49, (36, 40, 46))
        rect(img, 7, 15, 56, 48, (236, 240, 242))
        bevel(img, (6, 14, 58, 50), 0.22)
        rect(img, 7, 15, 56, 19, (48, 54, 62))
        rect(img, 7, 19, 56, 20, WAYLINE)
        if code == "medical":
            # A red cross beside the word
            rect(img, 11, 27, 22, 30, (196, 36, 32))
            rect(img, 15, 23, 18, 34, (196, 36, 32))
            draw_text(img, (24, 22, 55, 36), name, INK, 9, condensed=True)
        else:
            draw_text(img, (9, 22, 55, 47), name, (28, 30, 34), 9 if "\n" not in name else 8, condensed=True)
        save(img, "sign-plate-" + code)


def warning_textures():
    # AUTHORIZED PERSONNEL ONLY: a yellow plate, a black border
    img = big_panel()
    rect(img, 6, 10, 57, 53, (20, 20, 22))
    rect(img, 8, 12, 55, 51, (244, 200, 40))
    bevel(img, (6, 10, 58, 54), 0.2)
    draw_text(img, (10, 14, 54, 50), "AUTHORIZED\nPERSONNEL\nONLY", (18, 18, 20), 8, condensed=True)
    save(img, "sign-auth")
    # DECONTAMINATION: a hazard band over a white plate
    img = big_panel()
    rect(img, 6, 12, 57, 51, (36, 40, 46))
    rect(img, 7, 13, 56, 50, (236, 240, 242))
    for x in range(7, 57):
        for y in range(13, 21):
            if ((x + y) // 4) % 2 == 0:
                img.putpixel((x, y), (244, 196, 30, 255))
            else:
                img.putpixel((x, y), (24, 24, 26, 255))
    bevel(img, (6, 12, 58, 52), 0.2)
    draw_text(img, (9, 23, 55, 48), "DECON-\nTAMINATION", (28, 30, 34), 8, condensed=True)
    save(img, "sign-decon")
    # HIGH VOLTAGE: a yellow triangle with a bolt, the words under it
    img = big_panel()
    rect(img, 12, 6, 51, 57, (240, 240, 236))
    bevel(img, (12, 6, 52, 58), 0.18)
    d = ImageDraw.Draw(img)
    d.polygon([(32, 9), (48, 36), (16, 36)], fill=(20, 20, 22))
    d.polygon([(32, 13), (44.5, 34), (19.5, 34)], fill=(246, 202, 30))
    d.polygon([(33, 17), (28, 27), (32, 27), (30, 33), (36, 24), (32, 24), (35, 17)], fill=(20, 20, 22))
    draw_text(img, (14, 38, 50, 55), "HIGH\nVOLTAGE", (20, 20, 22), 6, condensed=True)
    save(img, "sign-hv")


def service_textures():
    # A service hatch: a recessed steel panel, a flush handle, a hazard corner, a small stencilled number
    img = big_panel()
    rect(img, 8, 8, 55, 55, (178, 184, 190))
    bevel(img, (8, 8, 56, 56), 0.3)
    rect(img, 11, 11, 52, 52, (196, 202, 206))
    bevel(img, (11, 11, 53, 53), -0.15)
    rect(img, 44, 28, 47, 37, (60, 64, 70))
    for k in range(10):
        for j in range(10 - k):
            if ((k + j) // 3) % 2 == 0:
                img.putpixel((12 + j, 12 + k), (230, 180, 30, 255))
            else:
                img.putpixel((12 + j, 12 + k), (30, 30, 32, 255))
    for sx, sy in ((13, 49), (49, 13), (49, 49)):
        rect(img, sx, sy, sx + 1, sy + 1, (100, 104, 110))
    draw_text(img, (16, 40, 40, 50), "SVC 15", (60, 64, 70), 5, condensed=True)
    save(img, "sign-hatch")
    # A grille with the pipes behind it: dark void, three pipes (white, green, copper), slats over them
    img = big_panel()
    rect(img, 6, 6, 57, 57, (30, 32, 36))
    for x0, c in ((10, (210, 214, 216)), (24, (76, 140, 96)), (38, (176, 110, 64))):
        for x in range(x0, x0 + 9):
            t = (x - x0) / 8
            shade = 0.55 + 0.45 * np.sin(np.pi * t)
            for y in range(7, 57):
                img.putpixel((x, y), tuple(int(v * shade) for v in c) + (255,))
    for y in range(8, 56, 5):
        rect(img, 6, y, 57, y + 1, (150, 156, 162))
        rect(img, 6, y + 2, 57, y + 2, (96, 100, 106))
    rect(img, 4, 4, 59, 5, (170, 176, 182))
    rect(img, 4, 58, 59, 59, (120, 126, 132))
    rect(img, 4, 4, 5, 59, (170, 176, 182))
    rect(img, 58, 4, 59, 59, (120, 126, 132))
    save(img, "sign-pipes")


def lift_textures():
    """The lift doors (left and right leaves as seen from the hall, rows 0-2 from the floor), the indicator over them (two
    halves) and the call panel: brushed stainless steel in a dark frame."""
    steel = M.brushed_metal(seed=15710, size=B, base=(184, 190, 196), direction="v", streak=3, sheen=8)
    for side in ("l", "r"):
        for row in range(3):
            img = steel.copy()
            # The frame on the outer edge, the seam on the inner
            outer = (0, 7) if side == "l" else (56, 63)
            rect(img, outer[0], 0, outer[1], B - 1, (70, 74, 80))
            rect(img, outer[0] + 2, 0, outer[1] - 2, B - 1, (150, 156, 162))
            seam = 63 if side == "l" else 0
            rect(img, seam, 0, seam, B - 1, (40, 42, 46))
            if row == 2:
                rect(img, 0, 0, B - 1, 6, (70, 74, 80))
                rect(img, 0, 2, B - 1, 4, (150, 156, 162))
            if row == 0:
                rect(img, 0, 60, B - 1, B - 1, (90, 94, 100))
            # A faint reflection
            for y in range(B):
                blend(img, (20 + y // 3) % B if side == "l" else (44 - y // 3) % B, y, (230, 236, 240), 0.25)
            save(img, f"sign-lift{side}{row}")
    # The indicator over the doors: a dark header strip with a small amber display ("B3") and the arrows
    img = Image.new("RGBA", (2 * B, B), (0, 0, 0))
    img.paste(big_panel(), (0, 0))
    img.paste(big_panel(), (B, 0))
    rect(img, 4, 22, 2 * B - 5, 46, (36, 40, 46))
    bevel(img, (4, 22, 2 * B - 4, 47), 0.2)
    rect(img, 50, 26, 77, 42, (14, 10, 6))
    draw_text(img, (52, 27, 76, 41), "B3", (255, 168, 40), 10)
    d = ImageDraw.Draw(img)
    d.polygon([(36, 30), (42, 38), (30, 38)], fill=(90, 70, 40))
    d.polygon([(86, 30), (98, 30), (92, 38)], fill=(90, 70, 40))
    save(img.crop((0, 0, B, B)), "sign-liftind0")
    save(img.crop((B, 0, 2 * B, B)), "sign-liftind1")
    # The call panel: a steel plate, two round buttons (the up one lit: called, and nothing comes)
    img = big_panel()
    rect(img, 22, 10, 41, 53, (176, 182, 188))
    bevel(img, (22, 10, 42, 54), 0.25)
    for cy, lit in ((24, True), (40, False)):
        for y in range(cy - 5, cy + 6):
            for x in range(26, 38):
                dd = ((x - 31.5) ** 2 + (y - cy) ** 2) ** 0.5
                if dd < 5:
                    img.putpixel((x, y), (255, 190, 80, 255) if lit and dd < 3.6 else (90, 94, 100, 255) if dd > 3.6 else (120, 124, 130, 255))
    d = ImageDraw.Draw(img)
    d.polygon([(31.5, 21), (34, 26), (29, 26)], fill=(120, 60, 10))
    d.polygon([(29, 38), (34, 38), (31.5, 43)], fill=(40, 42, 46))
    save(img, "sign-liftcall")


def menu_textures():
    """The canteen's menu board, three blocks wide, over the serving line: a dark board, the dishes, the service stopped."""
    W = 3 * B
    img = Image.new("RGBA", (W, B), (0, 0, 0))
    for k in range(3):
        img.paste(big_panel(), (k * B, 0))
    rect(img, 4, 6, W - 5, 57, (22, 26, 30))
    bevel(img, (4, 6, W - 4, 58), 0.25)
    rect(img, 6, 8, W - 7, 17, (40, 46, 54))
    draw_text(img, (8, 9, W - 8, 17), "CANTEEN  -  LEVEL 15  -  SECTOR SERVICES", (220, 230, 236), 6, condensed=True)
    rows = [("PROTEIN RATION A", "0.00"), ("PROTEIN RATION B", "0.00"), ("NUTRIENT PASTE", "0.00"), ("COFFEE", "0.00"),
            ("WATER", "FREE")]
    for i, (dish, price) in enumerate(rows):
        y = 20 + i * 6
        draw_text(img, (14, y, 120, y + 5), dish, (200, 214, 220), 4, condensed=True)
        draw_text(img, (150, y, 182, y + 5), price, (130, 210, 230), 4, condensed=True)
    rect(img, 6, 50, W - 7, 55, (60, 12, 10))
    draw_text(img, (8, 50, W - 8, 55), "SERVICE SUSPENDED", (250, 110, 90), 4, condensed=True)
    for k in range(3):
        save(img.crop((k * B, 0, (k + 1) * B, B)), f"sign-menu{k}")


def escape_textures():
    """The ESCAPE panels redrawn at 64 px with their labels (gen_15's and gen_15_links' are 32 px with the word only): a
    steel panel, ESCAPE over a red mushroom button in a yellow collar, EMERGENCY EGRESS and the small print; the live one
    (its button lit, its green lamp on) and the dead one."""
    for name, live in (("deco-escape", False), ("deco-escapelive", True)):
        img = big_panel()
        rect(img, 8, 6, 55, 57, (168, 174, 180))
        bevel(img, (8, 6, 56, 58), 0.25)
        rect(img, 10, 8, 53, 15, (34, 38, 44))
        draw_text(img, (11, 8, 53, 15), "EMERGENCY EGRESS", (230, 234, 238), 5, condensed=True)
        draw_text(img, (11, 17, 53, 25), "ESCAPE", (170, 24, 20), 8)
        d = ImageDraw.Draw(img)
        d.ellipse((20, 27, 43, 50), fill=(232, 190, 30, 255))
        d.ellipse((23, 30, 40, 47), fill=(255, 80, 60, 255) if live else (150, 26, 22, 255))
        if live:
            d.ellipse((27, 32, 34, 38), fill=(255, 196, 180, 255))
        else:
            d.ellipse((27, 32, 33, 37), fill=(190, 70, 60, 255))
        d.ellipse((46, 44, 51, 49), fill=(110, 255, 140, 255) if live else (40, 60, 46, 255))
        draw_text(img, (11, 51, 45, 56), "LEVEL 5 CLEARANCE", (60, 64, 70), 3, condensed=True)
        save(img, name)


def bigscreen_textures():
    """A control room's big display over its wall of panels, three blocks wide and two high: the radar of the levels
    (Wikidot's "Avalon 2.4": the levels as shapes, green lines between them), large."""
    W, H = 3 * B, 2 * B
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    rect(img, 0, 0, W - 1, H - 1, (40, 44, 50))
    rect(img, 4, 4, W - 5, H - 5, (4, 16, 8))
    d = ImageDraw.Draw(img)
    green, dim = (70, 230, 110, 255), (26, 90, 46, 255)
    cx, cy = W // 2, H // 2 + 6
    for r in (18, 36, 54):
        d.ellipse((cx - r * 1.4, cy - r, cx + r * 1.4, cy + r), outline=dim)
    d.line((cx - 80, cy, cx + 80, cy), fill=dim)
    d.line((cx, cy - 56, cx, cy + 56), fill=dim)
    rng = np.random.default_rng(15740)
    nodes = [(cx, cy)] + [(int(cx + rng.uniform(-80, 80)), int(cy + rng.uniform(-48, 48))) for _ in range(11)]
    for i, (x, y) in enumerate(nodes[1:], 1):
        j = int(rng.integers(0, i))
        d.line((x, y, nodes[j][0], nodes[j][1]), fill=green, width=1)
    for i, (x, y) in enumerate(nodes):
        s_ = 3 if i else 5
        if i % 3 == 0:
            d.rectangle((x - s_, y - s_, x + s_, y + s_), fill=(200, 255, 200, 255))
        elif i % 3 == 1:
            d.polygon([(x, y - s_), (x + s_, y + s_), (x - s_, y + s_)], fill=(200, 255, 200, 255))
        else:
            d.ellipse((x - s_, y - s_, x + s_, y + s_), fill=(200, 255, 200, 255))
    # The sweep
    d.line((cx, cy, cx + 70, cy - 40), fill=(150, 255, 170, 255), width=2)
    draw_text(img, (8, 6, 70, 16), "AVALON 2.4", (110, 250, 140), 7)
    draw_text(img, (120, 6, W - 8, 14), "LEVEL MAP  -  LINKS 214", (60, 170, 90), 5, condensed=True)
    draw_text(img, (8, H - 14, W - 8, H - 7), "ACCESS DENIED: LEVEL 5 CLEARANCE REQUIRED TO CHANGE REALITY", (250, 90, 80), 5, condensed=True)
    for row in range(2):
        for k in range(3):
            save(img.crop((k * B, (1 - row) * B, (k + 1) * B, (2 - row) * B)), f"sign-big{row}{k}")


def slide_textures():
    """The lecture hall's projection screen over the stage, three blocks wide and three high: a pale screen on a dark frame,
    a slide still on it (the facility's induction, invented), the projector's light falling off at the corners."""
    W = H = 3 * B
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    rect(img, 0, 0, W - 1, H - 1, (44, 48, 54))
    rect(img, 5, 5, W - 6, H - 6, (226, 232, 238))
    for y in range(5, H - 5):
        for x in range(5, W - 5):
            d = ((x - W / 2) ** 2 + (y - H / 2) ** 2) ** 0.5 / (W * 0.7)
            blend(img, x, y, (150, 160, 176), min(0.6, d * d * 1.2))
    rect(img, 16, 20, W - 17, 46, (40, 70, 110))
    draw_text(img, (20, 22, W - 20, 44), "INDUCTION  -  DAY 1", (236, 242, 248), 12, condensed=True)
    lines = ["1. REMAIN IN LIT AREAS", "2. REPORT ANY LOSS OF POWER", "3. KEEP TO YOUR WING", "4. DO NOT ENTER THE STAR ROOM"]
    for line, y in zip(lines, (70, 94, 134, 158)):  # (clear of the seams between the blocks at 64 and 128)
        draw_text(img, (22, y, W - 22, y + 14), line, (40, 46, 56), 9, condensed=True)
    draw_text(img, (W - 70, H - 26, W - 14, H - 16), "AVALON 2.4", (40, 70, 110), 6)
    for row in range(3):
        for k in range(3):
            save(img.crop((k * B, (2 - row) * B, (k + 1) * B, (3 - row) * B)), f"sign-slide{row}{k}")


def map_textures():
    """A facility map by a crossing, two blocks wide and two high: the halls as a cyan grid, the wings as blocks, a red YOU
    ARE HERE, and across it a band of static where the map has failed (nobody's map is to be trusted here)."""
    W = H = 2 * B
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    rect(img, 0, 0, W - 1, H - 1, (44, 48, 54))
    rect(img, 4, 4, W - 5, H - 5, (10, 20, 28))
    rect(img, 6, 6, W - 7, 17, (30, 44, 56))
    draw_text(img, (8, 7, W - 8, 16), "SECTOR MAP", (200, 236, 246), 7, condensed=True)
    d = ImageDraw.Draw(img)
    for k in range(5):
        x = 14 + k * 25
        d.rectangle((x, 22, x + 2, H - 10), fill=(70, 170, 190, 255))
        y = 22 + k * 22
        if y < H - 12:
            d.rectangle((10, y, W - 10, y + 2), fill=(70, 170, 190, 255))
    rng = np.random.default_rng(15750)
    for _ in range(14):
        x, y = int(rng.integers(18, W - 26)), int(rng.integers(26, H - 26))
        d.rectangle((x, y, x + int(rng.integers(4, 10)), y + int(rng.integers(3, 8))), fill=(40, 70, 86, 255))
    d.ellipse((60, 64, 68, 72), fill=(240, 60, 50, 255))
    draw_text(img, (70, 64, 118, 72), "YOU ARE HERE", (240, 110, 100), 5, condensed=True)
    # The static band
    for y in range(84, 104):
        for x in range(5, W - 5):
            v = int(rng.integers(30, 200))
            img.putpixel((x, y), (v, v, v, 255))
    rect(img, 30, 89, 98, 99, (10, 10, 12))
    draw_text(img, (32, 90, 96, 98), "SIGNAL LOST", (230, 230, 230), 5, condensed=True)
    for row in range(2):
        for k in range(2):
            save(img.crop((k * B, (1 - row) * B, (k + 1) * B, (2 - row) * B)), f"sign-map{row}{k}")


def extinguisher_texture():
    """A fire extinguisher in its wall cabinet: a red steel frame, a glass door, the extinguisher behind it."""
    img = big_panel()
    rect(img, 16, 6, 47, 59, (170, 30, 26))
    bevel(img, (16, 6, 48, 60), 0.25)
    rect(img, 19, 9, 44, 56, (36, 30, 30))
    rect(img, 26, 18, 37, 52, (196, 34, 28))
    rect(img, 29, 13, 34, 18, (40, 40, 44))
    rect(img, 34, 14, 40, 16, (40, 40, 44))
    rect(img, 27, 26, 36, 33, (236, 236, 230))
    for y in range(9, 57):
        for x in range(19, 45):
            if (x + y) % 9 == 0:
                blend(img, x, y, (220, 230, 240), 0.35)
    draw_text(img, (18, 2, 46, 6), "FIRE", (190, 30, 26), 4, condensed=True)
    save(img, "sign-extinguisher")


def band_textures():
    """The halls' band (gen_15's deco-band) in each hall line's colour, at the same 32 px."""
    base = Image.open(os.path.join(TEX, "deco-band.png")).convert("RGBA")
    for i, c in enumerate(LINE_COLOURS):
        img = base.copy()
        rect(img, 0, 15, S - 1, 16, c)
        save(img, f"sign-band{i}")


# ======================================================================== l15-floormark textures

def floormark_textures():
    base = Image.open(os.path.join(TEX, "floor-ceramic.png")).convert("RGBA")
    for i, c in enumerate(LINE_COLOURS):
        # The line along north-south (the image's up is north); the other way is the same turned
        img = base.copy()
        for y in range(S):
            for x in range(13, 19):
                blend(img, x, y, c, 0.85 if 14 <= x <= 17 else 0.45)
        save(img, f"mark-line{i}-ns")
        save(img.rotate(90), f"mark-line{i}-we")
        # A chevron pointing north over the line
        img = base.copy()
        for y in range(S):
            for x in range(13, 19):
                blend(img, x, y, c, 0.85 if 14 <= x <= 17 else 0.45)
        d = ImageDraw.Draw(img)
        d.polygon([(16, 3), (29, 16), (29, 22), (16, 10), (3, 22), (3, 16)], fill=tuple(c) + (255,))
        d.polygon([(16, 13), (29, 26), (29, 30), (16, 19), (3, 30), (3, 26)], fill=tuple(int(v * 0.8) for v in c) + (255,))
        for dname, ang in (("n", 0), ("w", 90), ("s", 180), ("e", 270)):
            save(img.rotate(ang), f"mark-chev{i}-{dname}")


# ======================================================================== l15-hangsign textures

def hangsign_textures():
    """Each hall's sign, three blocks wide (64 x 40 a block): a dark glass panel, a cyan glow round it, the hall's name;
    off: the same, unlit."""
    W, H = 3 * B, 40
    for n, code in enumerate(HALLS):
        for lit in (True, False):
            img = Image.new("RGBA", (W, H), (8, 22, 30) if lit else (26, 30, 34))
            glow = (120, 230, 250) if lit else (70, 80, 88)
            rect(img, 0, 0, W - 1, 1, glow)
            rect(img, 0, H - 2, W - 1, H - 1, glow)
            if lit:
                for y in range(3, H - 3, 3):
                    for x in range(2, W - 2):
                        blend(img, x, y, (30, 70, 86), 0.5)
            draw_text(img, (12, 6, 66, 34), "HALL", (170, 236, 250) if lit else (96, 104, 110), 12, condensed=True)
            draw_text(img, (68, 4, 126, 36), code, (236, 252, 255) if lit else (120, 128, 134), 22)
            # Arrows both ways along the cross hall
            d = ImageDraw.Draw(img)
            c = glow
            d.polygon([(140, 20), (152, 10), (152, 16), (178, 16), (178, 10), (190, 20), (178, 30), (178, 24), (152, 24), (152, 30)],
                      fill=tuple(c) + (255,))
            for k in range(3):
                save(img.crop((k * B, 0, (k + 1) * B, H)), f"hang{n}-{'lit' if lit else 'off'}-{k}")


# ======================================================================== Prop textures

def floor_textures():
    """The medical bays' and labs' pale blue-grey vinyl (big soft tiles), the canteens' warm terrazzo."""
    save(M.tile(seed=15730, base=(194, 204, 210), grout=(170, 180, 186), pitch=16, grout_w=1, jitter=2, uneven=1, glaze=False,
                speckle=0.15), "floor-vinyl")
    img = M.concrete(seed=15731, base=(206, 196, 182), grain=2, mottle=4, aggregate=0.35, pores=0.0, hue=3.0)
    M.emboss_lines(img, xs=(0,), ys=(0,), strength=0.12)
    save(img, "floor-terrazzo")


def prop_textures():
    save(M.fabric(seed=15720, base=(52, 74, 112)) if hasattr(M, "fabric") else M.rubber(seed=15720, base=(52, 74, 112)), "seatcloth")
    save(M.fabric(seed=15721, base=(96, 112, 132)) if hasattr(M, "fabric") else M.rubber(seed=15721, base=(96, 112, 132)), "mattress")
    img = M.new((S, S), (232, 64, 220))
    for x in range(S):
        for y in range(S):
            if (x // 4 + y // 8) % 2 == 0:
                blend(img, x, y, (255, 160, 250), 0.5)
    save(img, "growlight")
    save(M.fabric(seed=15723, base=(150, 186, 184)), "curtain")
    save(M.new((S, S), (66, 40, 64)), "growlightoff")
    # Dry leaves: olive gone yellow and brown, a darker vein down the middle
    img = M.new((S, S), (128, 120, 60))
    rng = np.random.default_rng(15722)
    for _ in range(220):
        x, y = rng.integers(0, S, 2)
        blend(img, int(x), int(y), [(150, 130, 66), (104, 98, 46), (120, 84, 44), (160, 146, 90)][int(rng.integers(0, 4))], 0.7)
    for x in range(S):
        blend(img, x, 15, (82, 70, 36), 0.6)
    save(img, "deadplant")
    img = M.new((S, S), (96, 88, 50))
    for _ in range(120):
        x, y = rng.integers(0, S, 2)
        blend(img, int(x), int(y), (70, 60, 34), 0.6)
    save(img, "deadstalk")
    img = M.new((S, S), (40, 36, 30))
    for _ in range(120):
        x, y = rng.integers(0, S, 2)
        blend(img, int(x), int(y), (70, 60, 46), 0.7)
    save(img, "soil")
    img = M.new((S, S), (60, 220, 120))
    save(img, "docklit")
    save(M.new((S, S), (40, 50, 46)), "dockdead")
    # The dock's plate ("DOCK" and a number): drawn at 64
    img = Image.new("RGBA", (B, B), (40, 44, 50))
    rect(img, 2, 2, B - 3, B - 3, (52, 58, 66))
    draw_text(img, (6, 10, 58, 54), "DOCK\nR-07", (210, 220, 228), 12, condensed=True)
    save(img, "dockplate")
    # Cables: black, grey, a blue and a yellow in a bundle
    img = M.new((S, S), (28, 30, 32))
    for y in range(S):
        c = [(28, 30, 32), (60, 62, 66), (40, 70, 140), (28, 30, 32), (200, 170, 40), (50, 52, 56), (28, 30, 32), (120, 30, 30)][y // 4]
        for x in range(S):
            img.putpixel((x, y), tuple(int(v * (0.8 + 0.2 * ((y % 4) in (1, 2)))) for v in c) + (255,))
    save(img, "cables")
    img = Image.open(os.path.join(TEX, "glass-clear.png")).convert("RGBA")
    save(img, "guardglass")


# ======================================================================== Shapes

def hangsign_shape(part, axis):
    """One of the three blocks of a hanging sign: a thin panel low in the block (y 4-14), faces both ways along the hall;
    rods up to the ceiling on the outer blocks. we: the panel across x (faces north and south), ns: across z."""
    els = []
    if axis == "we":
        els.append(box("Panel", (0, 4, 7.5), (16, 14, 8.5), {"north": "back", "south": "front", "up": "rim", "down": "rim",
                                                              "east": "rim", "west": "rim"}, glow=0))
        rx = 4 if part == 0 else 12
        if part != 1:
            els.append(box("Rod", (rx - 0.25, 14, 7.75), (rx + 0.25, 16, 8.25), "rim"))
    else:
        els.append(box("Panel", (7.5, 4, 0), (8.5, 14, 16), {"east": "back", "west": "front", "up": "rim", "down": "rim",
                                                              "north": "rim", "south": "rim"}, glow=0))
        rz = 4 if part == 0 else 12
        if part != 1:
            els.append(box("Rod", (7.75, 14, rz - 0.25), (8.25, 16, rz + 0.25), "rim"))
    for e in els:
        for f in e["faces"].values():
            f["uv"] = [0, 0, 16, 16]
    return els


def write_shape(name, elements, textures, extra=None):
    data = {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": elements}
    data.update(extra or {})
    path = os.path.join(SHAPES, name + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    return "backrooms:block/15/" + name


def T(name):
    return "backrooms:block/15/" + name


def bunk_shape(part):
    """The upper bunk over a cot, modelled head to the north: a steel frame on four posts (down to the floor below), a
    mattress, a guard rail on the east side; the head part a head board and a pillow, the foot part a ladder."""
    head = part == "head"
    els = [
        box("RailW", (0.5, 3, 0), (1.5, 5, 16), "steelgrey"),
        box("RailE", (14.5, 3, 0), (15.5, 5, 16), "steelgrey"),
        box("Slats", (1.5, 3.5, 0), (14.5, 4, 16), "steelgrey", faces=("down",)),
        box("Mattress", (1.5, 4, 0.25 if head else 0), (14.5, 6.5, 16 if head else 15.75), "mattress"),
        box("Guard", (15, 6.5, 2 if head else 0), (15.5, 10, 16 if head else 10), "steelgrey"),
    ]
    zs = (0.5, 1.5) if head else (14.5, 15.5)
    for x in (0.5, 14.5):
        els.append(box(f"Post{x}", (x, -16, zs[0]), (x + 1, 11, zs[1]), "steelgrey"))
    if head:
        els += [box("Board", (1.5, 5, 0.5), (14.5, 11, 1.5), "steelgrey"),
                box("Pillow", (3, 6.5, 1.5), (13, 8, 5), "white")]
    else:
        els += [box("Footboard", (1.5, 5, 14.5), (14.5, 9, 15.5), "steelgrey")]
        for y in (-12, -7, -2, 3):
            els.append(box(f"Rung{y}", (-0.5, y, 13.5), (0.5, y + 0.75, 15.5), "steelgrey"))
    return write_shape("l15-bunk-" + part, els, {k: T(k) for k in ("steelgrey", "mattress", "white")})


def riser_shape(kind):
    h = 8 if kind == "half" else 16
    els = [box("Step", (0, 0, 0), (16, h, 16), {"top": "carpet", "side": "dark"})]
    if kind == "half":
        els.append(box("Nosing", (0, h - 1, -0.01), (16, h, 0.5), "steelgrey", faces=("north", "up")))
    return write_shape("l15-riser-" + kind, els, {"carpet": T("floor-carpet"), "dark": T("dark"), "steelgrey": T("steelgrey")})


def seat_shape(kind):
    """A row seat facing north (its sitter looks north): a steel pedestal, an upholstered pan and back, arms, a writing
    tablet folded down by the right arm. hi: on a half step (the step under it, everything 8 up)."""
    up = 8 if kind == "hi" else 0
    els = []
    if up:
        els.append(box("Step", (0, 0, 0), (16, 8, 16), {"top": "carpet", "side": "dark"}))
        els.append(box("Nosing", (0, 7, -0.01), (16, 8, 0.5), "steelgrey", faces=("north", "up")))
    els += [
        box("Pedestal", (6.5, up, 7), (9.5, up + 5, 11), "steelgrey"),
        box("Pan", (2, up + 5, 4), (14, up + 7, 12), "seatcloth"),
        box("Back", (2, up + 6, 12), (14, up + 16, 14), "seatcloth", rot=(-8, 0, 0), origin=(8, up + 6, 13)),
        box("Shell", (2, up + 6, 14), (14, up + 15.5, 14.5), "steelgrey", rot=(-8, 0, 0), origin=(8, up + 6, 13)),
        box("ArmW", (0.5, up + 5, 5), (2, up + 10, 12), "steelgrey"),
        box("ArmE", (14, up + 5, 5), (15.5, up + 10, 12), "steelgrey"),
        box("Tablet", (14, up + 2, 5), (15.25, up + 9.5, 11), "epoxy"),
    ]
    return write_shape("l15-seat-" + kind, els, {"carpet": T("floor-carpet"), "dark": T("dark"), "steelgrey": T("steelgrey"),
                                                 "seatcloth": T("seatcloth"), "epoxy": T("epoxy")})


def serve_shape(kind):
    """The serving line, the customer's side to the north: a steel counter with a tray slide along its front; on it steel
    wells, a stack of trays or the till; a glass guard over it on two posts (not over the till)."""
    els = [
        box("Body", (0, 0, 2.5), (16, 13, 16), {"all": "steelgrey", "front": "lockerdoor"}),
        box("Kick", (0, 0, 2), (16, 1, 2.5), "dark", faces=("north",)),
        box("Top", (0, 13, 2), (16, 14, 16), "sinksteel"),
        box("Slide", (0, 11.5, 0), (16, 12.25, 2.5), "sinksteel"),
        box("SlideRail0", (0, 11.75, 0.25), (16, 12.5, 0.75), "steelgrey", faces=("north", "up")),
    ]
    if kind == "wells":
        for i, x in enumerate((1.5, 8.5)):
            els.append(box(f"Well{i}", (x, 13.6, 6), (x + 6, 14.05, 13), "dark", faces=("up",)))
            els.append(box(f"Lid{i}", (x + 0.5, 14, 11.5), (x + 5.5, 15, 13), "sinksteel"))
    elif kind == "trays":
        for k in range(5):
            els.append(box(f"Tray{k}", (3 + 0.3 * (k % 2), 14 + k * 0.6, 5), (12 + 0.3 * (k % 2), 14.5 + k * 0.6, 12), "epoxy"))
    else:
        els += [box("Till", (4, 14, 7), (12, 17, 13), {"all": "dark", "top": "steelgrey"}),
                box("TillScreen", (5, 17, 11), (11, 21, 12), {"all": "dark", "north": "console-dead"})]
    if kind != "till":
        els += [box("PostW", (0.25, 14, 4), (1, 22.5, 5), "steelgrey"),
                box("PostE", (15, 14, 4), (15.75, 22.5, 5), "steelgrey"),
                box("Guard", (1, 16, 4.25), (15, 22, 4.75), "guardglass"),
                box("Shelf", (0, 22.5, 3), (16, 23, 8), "sinksteel")]
    return write_shape("l15-serve-" + kind, els, {k: T(k) for k in ("steelgrey", "lockerdoor", "dark", "sinksteel", "epoxy",
                                                                     "console-dead", "guardglass")})


def growrack_shape(part, lit):
    """A hydroponics rack, its aisle side to the north: four steel posts, two shelves of trays of dead plants, a grow light
    under each shelf above them (glowing magenta, or off)."""
    light = "growlight" if lit else "growlightoff"
    els = []
    for x in (0.5, 14.5):
        for z in (2, 13):
            els.append(box(f"Post{x}{z}", (x, 0, z), (x + 1, 16, z + 1), "steelgrey"))
    for i, y in enumerate((1, 9)):
        els.append(box(f"Shelf{i}", (0.5, y - 1, 2), (15.5, y, 14), "steelgrey"))
        els.append(box(f"Tray{i}", (1.5, y, 3), (14.5, y + 1.5, 13), {"all": "dark", "top": "soil"}))
        # Dead plants: a thin stalk each, two or three dry leaves hanging off it, a few fallen on the soil
        for j, (px, pz, h) in enumerate(((3, 5, 4), (6.5, 9, 5), (10, 4.5, 3.5), (12.5, 9.5, 4.5), (4.5, 10.5, 3), (8.5, 6, 2.5))):
            els.append(box(f"Stalk{i}{j}", (px, y + 1.5, pz), (px + 0.5, y + 1.5 + h, pz + 0.5), "deadstalk"))
            for q, (dy, ang, droop) in enumerate(((0.45, 20 + 40 * j, 35), (0.75, 140 + 40 * j, -40), (0.95, 260 + 40 * j, 50))[: 2 + j % 2]):
                ly = y + 1.5 + h * dy
                els.append(box(f"Leaf{i}{j}{q}", (px + 0.25, ly, pz + 0.1), (px + 2.25, ly + 0.1, pz + 0.85), "deadplant",
                               rot=(0, ang % 360 - 180, droop), origin=(px + 0.25, ly, pz + 0.25)))
            els.append(box(f"Fallen{i}{j}", (px + 1, y + 1.5, pz + 1), (px + 2.5, y + 1.55, pz + 2), "deadplant"))
        ly = 7.5 if i == 0 else 15.5
        els.append(box(f"Lamp{i}", (1.5, ly - 0.5, 6), (14.5, ly, 10), light, glow=220 if lit else 0))
        els.append(box(f"LampHousing{i}", (1.5, ly, 5.5), (14.5, ly + 0.5, 10.5), "steelgrey"))
    if part == "upper":
        els.append(box("Top", (0.5, 15.5, 2), (15.5, 16, 14), "steelgrey", faces=("up", "north", "south", "east", "west")))
    return write_shape(f"l15-growrack-{part}-{'lit' if lit else 'off'}", els,
                       {k: T(k) for k in ("steelgrey", "dark", "soil", "deadplant", "deadstalk", light)})


def dock_shape(part, lit):
    """A robot charging dock against a wall (behind it, to the south), its open side to the north: a back plate with two
    contact rails, side cheeks with a strip of status light, a floor plate; in the lower block a Robo-Man standing in it
    powered down, head hung (the creature's own model, turned to face out); in the upper block the hood, the dock's plate
    and its lamp."""
    lamp = "docklit" if lit else "dockdead"
    els = [box("Back", (1, 0, 14), (15, 16, 16), "steelgrey"),
           box("CheekW", (0, 0, 9), (1.5, 16, 16), "steelgrey"),
           box("CheekE", (14.5, 0, 9), (16, 16, 16), "steelgrey"),
           box("StripW", (1.5, 2 if part == "lower" else 0, 13), (1.75, 16 if part == "lower" else 10, 14), lamp, glow=200 if lit else 0,
               faces=("east",)),
           box("StripE", (14.25, 2 if part == "lower" else 0, 13), (14.5, 16 if part == "lower" else 10, 14), lamp,
               glow=200 if lit else 0, faces=("west",))]
    textures = {k: T(k) for k in ("steelgrey", "dark", lamp, "dockplate")}
    extra = None
    if part == "lower":
        els += [box("Floor", (1, 0, 4), (15, 0.5, 14), {"all": "dark", "top": "steelgrey"}),
                box("ContactL", (4, 8, 13.5), (6, 12, 14), "dark"),
                box("ContactR", (10, 8, 13.5), (12, 12, 14), "dark")]
        robot = json.load(open(os.path.join(ROOT, "assets", "backrooms", "shapes", "entity", "roboman.json"), encoding="utf-8"))
        # The creature's model, flattened (each part placed where its parents put it; its slight arm swing dropped) and
        # turned a quarter clockwise seen from above (it faces west, -x, in its own model): it faces north, out of the dock
        flat = []

        def walk(es, ox, oy, oz):
            for e in es:
                (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
                ax, ay, az = ox + x1, oy + y1, oz + z1
                f = e["faces"]
                flat.append({"name": "Robot" + e["name"],
                             "from": [16 - (oz + z2), ay + 0.5, ax], "to": [16 - az, oy + y2 + 0.5, ox + x2],
                             "faces": {k: v for k, v in {"east": f.get("north"), "south": f.get("east"), "west": f.get("south"),
                                                         "north": f.get("west"), "up": f.get("up"), "down": f.get("down")}.items() if v}})
                walk(e.get("children", []), ax, ay, az)
        walk(robot["elements"], 0, 0, 0)
        els += flat
        textures["skin"] = "backrooms:entity/roboman"
        extra = {"textureSizes": {"skin": [robot.get("textureWidth", 64), robot.get("textureHeight", 64)]}}
    else:
        els += [box("Hood", (0, 12, 6), (16, 16, 16), {"all": "steelgrey", "north": "steelgrey"}),
                box("Plate", (5, 12.5, 5.75), (11, 15.5, 6), "dockplate", faces=("north",)),
                box("Lamp", (12, 13, 5.5), (13.5, 14.5, 6), lamp, glow=255 if lit else 0)]
        els[-2]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    return write_shape(f"l15-dock-{part}-{'lit' if lit else 'dead'}", els, textures, extra)


def appliance_shape(kind):
    """An appliance left on a counter or a bench (its base 1.5 below the block, on the worktop), stripped of its insides
    (Fandom: coffee machines and 3D printers emptied of their machinery), its front to the north. coffee: a housing, its
    front panel gone, the cavity empty, a cut tube hanging; printer: an open frame and its gantry, no head, no bed."""
    y = -1.5
    if kind == "coffee":
        els = [box("Back", (4, y, 10), (12, y + 9, 12), "white"),
               box("SideW", (4, y, 4), (5, y + 9, 10), "white"),
               box("SideE", (11, y, 4), (12, y + 9, 10), "white"),
               box("Top", (4, y + 8, 4), (12, y + 9, 10), "white"),
               box("Base", (4, y, 3.5), (12, y + 1, 10), "steelgrey"),
               box("Inside", (5, y + 1, 9.9), (11, y + 8, 10), "dark", faces=("north",)),
               box("Tube", (7.5, y + 4, 8), (8.25, y + 8, 8.75), "dark"),
               box("Cup", (6.5, y + 1, 5), (8.5, y + 3, 7), "white")]
        tex_ = ("white", "steelgrey", "dark")
    else:
        els = []
        for x in (2.5, 12.5):
            for z in (3.5, 12.5):
                els.append(box(f"Post{x}{z}", (x, y, z), (x + 1, y + 12, z + 1), "steelgrey"))
        els += [box("Bottom", (2.5, y, 3.5), (13.5, y + 1, 13.5), "dark"),
                box("TopN", (2.5, y + 11, 3.5), (13.5, y + 12, 4.5), "steelgrey"),
                box("TopS", (2.5, y + 11, 12.5), (13.5, y + 12, 13.5), "steelgrey"),
                box("Gantry", (3.5, y + 8, 7.5), (12.5, y + 9, 8.5), "steelgrey"),
                box("Cable", (11, y + 1, 12), (11.5, y + 8, 12.5), "dark")]
        tex_ = ("steelgrey", "dark")
    return write_shape("l15-appliance-" + kind, els, {k: T(k) for k in tex_})


def curtain_shape(part):
    """A medical bay's curtain between two beds, along the north edge of the block, hung from a steel rail (upper: the rail
    and its hangers up into the block above, the curtain's top; lower: the rest of it, its hem a little above the floor
    below). Folded: strips of cloth in and out."""
    els = []
    y0, y1 = (-6, 16) if part == "lower" else (0, 14)
    for i in range(4):
        z0 = 0.4 if i % 2 == 0 else 1.0
        els.append(box(f"Fold{i}", (i * 4, y0, z0), (i * 4 + 4, y1, z0 + 0.5), "curtain"))
    if part == "upper":
        els.append(box("Rail", (0, 14, 0.25), (16, 15, 1.25), "steelgrey"))
        for x in (3.75, 11.75):
            els.append(box(f"Hanger{x}", (x, 15, 0.5), (x + 0.5, 32, 1), "steelgrey"))
    return write_shape("l15-curtain-" + part, els, {k: T(k) for k in ("curtain", "steelgrey")})


def tray_shape():
    """A ladder cable tray along x near the top of a block, hung on rods from the ceiling, a bundle of cables in it."""
    els = [box("RailN", (0, 10, 4), (16, 12, 4.5), "steelgrey"),
           box("RailS", (0, 10, 11.5), (16, 12, 12), "steelgrey")]
    for x in (1, 5, 9, 13):
        els.append(box(f"Rung{x}", (x, 10, 4.5), (x + 1, 10.5, 11.5), "steelgrey"))
    els.append(box("Cables", (0, 10.5, 5), (16, 12.5, 11), {"all": "cables", "up": "cables"}))
    for x in (3.5, 11.5):
        for z in (3.75, 12.25):
            els.append(box(f"Hanger{x}{z}", (x, 12, z - 0.25), (x + 0.5, 16, z + 0.25), "steelgrey"))
    return write_shape("l15-tray", els, {k: T(k) for k in ("steelgrey", "cables")})


# ======================================================================== Block types

def sign_kinds():
    k = {}
    for code, _ in PLATES:
        k["plate" + code] = "sign-plate-" + code
    for name in ("auth", "decon", "hv", "hatch", "pipes", "liftcall", "liftind0", "liftind1"):
        k[name] = "sign-" + name
    for side in ("l", "r"):
        for row in range(3):
            k[f"lift{side}{row}"] = f"sign-lift{side}{row}"
    for i in range(3):
        k[f"menu{i}"] = f"sign-menu{i}"
    for i in range(len(LINE_COLOURS)):
        k[f"band{i}"] = f"sign-band{i}"
    for row in range(2):
        for i in range(3):
            k[f"big{row}{i}"] = f"sign-big{row}{i}"
    for row in range(3):
        for i in range(3):
            k[f"slide{row}{i}"] = f"sign-slide{row}{i}"
    for row in range(2):
        for i in range(2):
            k[f"map{row}{i}"] = f"sign-map{row}{i}"
    k["extinguisher"] = "sign-extinguisher"
    return k


def blocktypes():
    kinds = sign_kinds()
    tbt = {}
    for k, t in kinds.items():
        for s in SIDES:
            tbt[f"*-{k}-{s}"] = {"all": tex("wall-panel"), s: tex(t)}
    data = {"code": "l15-sign", "variantgroups": [{"code": "kind", "states": list(kinds)}, {"code": "side", "states": SIDES}],
            "texturesByType": tbt, "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
            "blockmaterial": "Stone", "drawtype": "cube", "resistance": 6, "drops": [], "sounds": STONE, "lightAbsorption": 99,
            "vertexFlagsByType": {"*-liftcall-*": {"glowLevel": 40}, "*-liftind0-*": {"glowLevel": 40}, "*-liftind1-*": {"glowLevel": 40},
                                  "*-menu0-*": {"glowLevel": 50}, "*-menu1-*": {"glowLevel": 50}, "*-menu2-*": {"glowLevel": 50},
                                  "*-big*": {"glowLevel": 90}, "*-slide*": {"glowLevel": 70}, "*-map*": {"glowLevel": 60}},
            "lightHsvByType": {"*-big01-*": [23, 4, 5]}}
    write_json(os.path.join(BLOCKS, "l15-sign.json"), data,
               "Level 15: a white wall block with one face dressed (toward its side): the rooms' name plates, AUTHORIZED PERSONNEL ONLY, "
               "DECONTAMINATION, HIGH VOLTAGE, a service hatch, a grille with pipes behind it, the lift doors that do not open (left and "
               "right leaves, rows 0-2), the lift's indicator and call panel, the canteen's menu board, the halls' coloured band")

    states = []
    tbt = {}
    for i in range(len(LINE_COLOURS)):
        for m in ("line", "chev"):
            for d in (("ns", "we") if m == "line" else ("n", "e", "s", "w")):
                st = f"{m}{i}{d}"
                states.append(st)
                tbt[f"*-{st}"] = {"all": tex("floor-ceramic"), "up": tex(f"mark-{m}{i}-{d}")}
    data = {"code": "l15-floormark", "variantgroups": [{"code": "kind", "states": states}], "texturesByType": tbt,
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
            "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": STONE}
    write_json(os.path.join(BLOCKS, "l15-floormark.json"), data,
               "Level 15: the main halls' ceramic floor with the hall line's colour down its middle (line ns, we) and a chevron (n e s w)")

    # The hanging signs
    shapes, tbt, states_code = {}, {}, [str(n) for n in range(len(HALLS))]
    for axis in ("we", "ns"):
        for part in range(3):
            base = write_shape(f"l15-hangsign-{part}-{axis}", hangsign_shape(part, axis),
                               {"front": T("hang0-lit-0"), "back": T("hang0-lit-0"), "rim": T("dark")})
            for n in range(len(HALLS)):
                for st in ("lit", "off"):
                    key = f"*-{n}-{st}-{part}-{axis}"
                    shapes[key] = {"base": base}
                    # Each block's two faces: its slice as seen from either side, so the sign reads from both ways
                    tbt[key] = {"front": {"base": T(f"hang{n}-{st}-{part}")}, "back": {"base": T(f"hang{n}-{st}-{2 - part}")},
                                "rim": {"base": T("dark")}}
    hb = {"we": (0, 0.25, 0.44, 1, 0.9, 0.56), "ns": (0.44, 0.25, 0, 0.56, 0.9, 1)}
    json_block("l15-hangsign", [{"code": "hall", "states": states_code}, {"code": "state", "states": ["lit", "off"]},
                                {"code": "part", "states": ["0", "1", "2"]}, {"code": "axis", "states": ["we", "ns"]}], shapes,
               "Level 15: a sign hung from the ceiling across a main hall before a crossing (three blocks, parts 0-2), the hall's name on "
               "both faces, glowing (off in the dark)",
               {"collisionbox": cuboid((0, 0, 0, 0, 0, 0)),
                "selectionboxByType": {"*-we": cuboid(hb["we"]), "*-ns": cuboid(hb["ns"])}},
               extra={"texturesByType": tbt, "vertexFlagsByType": {"*-lit-*": {"glowLevel": 200}},
                      "lightHsvByType": {"*-lit-1-*": [33, 3, 5]}},
               inventory="l15-hangsign-0-lit-1-we")

    # The upper bunk
    shapes = {}
    for part in ("head", "foot"):
        base = bunk_shape(part)
        for s in SIDES:
            shapes[f"l15-bunk-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-bunk", [{"code": "part", "states": ["head", "foot"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: the upper bunk over a dormitory's cot (head, foot; head toward its side), its posts down to the floor",
               {"collisionbox": cuboid((0, 0.18, 0, 1, 0.42, 1)), "selectionbox": cuboid((0, 0.18, 0, 1, 0.65, 1))},
               extra={"drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.4, "var": 0.3}}]}, inventory="l15-bunk-head-north")

    # The lecture hall's steps and seats
    shapes = {}
    for k in ("half", "full"):
        shapes[f"*-{k}"] = {"base": riser_shape(k)}
    data = {"code": "l15-riser", "variantgroups": [{"code": "kind", "states": ["half", "full"]}], "shapeByType": shapes,
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Wood", "drawtype": "json",
            "sidesolidByType": {"*-full": {"all": True}, "*": {"all": False, "down": True}},
            "sideopaqueByType": {"*-full": {"all": True}, "*": {"all": False, "down": True}},
            "lightAbsorption": 0, "resistance": 3, "drops": [], "sounds": CLOTH,
            "collisionboxByType": {"*-half": cuboid((0, 0, 0, 1, 0.5, 1)), "*": cuboid((0, 0, 0, 1, 1, 1))},
            "selectionboxByType": {"*-half": cuboid((0, 0, 0, 1, 0.5, 1)), "*": cuboid((0, 0, 0, 1, 1, 1))}}
    write_json(os.path.join(BLOCKS, "l15-riser.json"), data, "Level 15: the lecture hall's stepped floor, carpeted (half a block, a whole one)")
    shapes = {}
    for k in ("lo", "hi"):
        base = seat_shape(k)
        for s in SIDES:
            shapes[f"l15-seat-{k}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-seat", [{"code": "kind", "states": ["lo", "hi"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: a lecture hall's row seat, facing its side (lo on the floor, hi on a half step): a back, arms, a writing tablet",
               {"collisionboxByType": {"*-lo-*": cuboid((0, 0, 0, 1, 0.45, 1)), "*": cuboid((0, 0, 0, 1, 0.95, 1))},
                "selectionboxByType": {"*-lo-*": cuboid((0, 0, 0, 1, 1, 1)), "*": cuboid((0, 0, 0, 1, 1, 1))}},
               sounds=CLOTH, material="Cloth",
               extra={"drops": [{"type": "item", "code": "game:flaxtwine", "quantity": {"avg": 0.3, "var": 0.3}}]}, inventory="l15-seat-lo-north")

    # The serving line
    shapes = {}
    for k in ("wells", "trays", "till"):
        base = serve_shape(k)
        for s in SIDES:
            shapes[f"l15-serve-{k}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-serve", [{"code": "kind", "states": ["wells", "trays", "till"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: the canteen's serving line, its customer side toward its side: steel wells, a stack of trays, the till; a glass "
               "guard over it",
               {"collisionbox": cuboid((0, 0, 0, 1, 0.9, 1)), "selectionbox": cuboid((0, 0, 0, 1, 1, 1))},
               extra={"renderpass": "Transparent",
                      "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0.3}}]}, inventory="l15-serve-wells-north")

    # The hydroponics racks
    shapes = {}
    for part in ("lower", "upper"):
        for lit in (True, False):
            base = growrack_shape(part, lit)
            for s in SIDES:
                shapes[f"l15-growrack-{part}-{'lit' if lit else 'off'}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-growrack", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": ["lit", "off"]},
                                {"code": "side", "states": SIDES}], shapes,
               "Level 15: a hydroponics rack two blocks high, its aisle side toward its side: trays of dead plants under grow lights (lit, off)",
               {"collisionbox": cuboid((0.03, 0, 0.1, 0.97, 1, 0.9)), "selectionbox": cuboid((0.03, 0, 0.1, 0.97, 1, 0.9))},
               extra={"lightHsvByType": {"*-upper-lit-*": [54, 5, 7]},
                      "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0.3}}]},
               inventory="l15-growrack-lower-lit-north")

    # The robot docks
    shapes = {}
    for part in ("lower", "upper"):
        for lit in (True, False):
            base = dock_shape(part, lit)
            for s in SIDES:
                shapes[f"l15-dock-{part}-{'lit' if lit else 'dead'}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-dock", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": ["lit", "dead"]},
                            {"code": "side", "states": SIDES}], shapes,
               "Level 15: a robot charging dock against a wall, open toward its side, a Robo-Man standing in it powered down (lower); its "
               "hood, plate and lamp (upper); lit or dead",
               {"collisionbox": cuboid((0, 0, 0.3, 1, 1, 1)), "selectionbox": cuboid((0, 0, 0.3, 1, 1, 1))},
               extra={"lightHsvByType": {"*-upper-lit-*": [22, 4, 4]},
                      "dropsByType": {"*-lower-*": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 1, "var": 0.5}},
                                                    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.5, "var": 0.5}}],
                                      "*": []}},
               inventory="l15-dock-lower-lit-north")

    # The stripped appliances on the worktops
    shapes = {}
    for k in ("coffee", "printer"):
        base = appliance_shape(k)
        for s in SIDES:
            shapes[f"l15-appliance-{k}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-appliance", [{"code": "kind", "states": ["coffee", "printer"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: an appliance left on a worktop, stripped of its insides (coffee: a coffee machine; printer: a 3D printer's frame)",
               {"collisionbox": cuboid((0.15, 0, 0.15, 0.85, 0.5, 0.85)), "selectionbox": cuboid((0.15, 0, 0.15, 0.85, 0.7, 0.85))},
               extra={"drops": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0.3}}]}, inventory="l15-appliance-coffee-north")

    # The medical bays' curtains
    shapes = {}
    for part in ("lower", "upper"):
        base = curtain_shape(part)
        for s in SIDES:
            shapes[f"l15-curtain-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-curtain", [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: a medical bay's curtain on its rail, along the block's edge toward its side (lower, upper)",
               {"collisionbox": cuboid((0, 0, 0, 0, 0, 0)), "selectionbox": cuboid((0, 0, 0, 1, 1, 0.12))},
               sounds=CLOTH, material="Cloth",
               extra={"drops": [{"type": "item", "code": "game:flaxtwine", "quantity": {"avg": 0.5, "var": 0.3}}]}, inventory="l15-curtain-lower-north")

    # The cable tray
    base = tray_shape()
    json_block("l15-tray", [{"code": "axis", "states": ["we", "ns"]}], {"*-we": {"base": base}, "*-ns": {"base": base, "rotateY": 90}},
               "Level 15: a cable tray hung along the top of a side corridor, a bundle of cables in it (we, ns)",
               {"collisionbox": cuboid((0, 0.62, 0, 1, 1, 1)), "selectionbox": cuboid((0, 0.62, 0, 1, 1, 1))},
               extra={"drops": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.6, "var": 0.4}}]}, inventory="l15-tray-we")


def main():
    plate_textures()
    warning_textures()
    service_textures()
    lift_textures()
    menu_textures()
    band_textures()
    bigscreen_textures()
    slide_textures()
    map_textures()
    extinguisher_texture()
    escape_textures()
    floor_textures()
    floormark_textures()
    hangsign_textures()
    prop_textures()
    blocktypes()
    print("Level 15 round 3: textures, shapes and blocktypes written")


if __name__ == "__main__":
    main()
