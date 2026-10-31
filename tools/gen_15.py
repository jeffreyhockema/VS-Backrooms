"""Level 15, "Futuristic Halls" (experimental): its blocks, their textures and shapes, and its sounds.

    l15-wall        white panelled concrete (panel, panelb with a service plate, base: the steel kick plate of the
                    skirting row), the service passages' bare grey concrete (grey, greybase), scorched panels, and the
                    white steel of the pilasters (beam, etched: arabesque symbols cut into it); cubes
    l15-walldeco    a white wall block with one face dressed, toward the side in its code: a dead hand scanner, a dead
                    display, the radar ("AVALON 2.4"), the ESCAPE panel, three views of other places (Level 18's rainbow
                    halls, a storm, the Lobby), a vent grille, one with a code scrawled by it, a wooden door (lower and
                    upper) set in the wall, a smear of dried blood, sixteen room codes in black; cubes
    l15-glass       thick glass, clear or cracked, for the machine rooms' walls; cubes (transparent)
    l15-floor       ceramic tiles (ceramic, worn), a dark non-slip coating, carpet, steel grating, a floor light (strip:
                    lit to look at, giving no light; stripdead), dried blood, scorch, a gate's tread plate, dust; cubes
    l15-ceiling     a white ceiling panel, an LED panel (on: gives light; lit: looks it; flicker: fails now and then;
                    off), the service passages' concrete, an air handler's grille; cubes
    l15-rib         a white steel I-beam across the top of a hall (we, ns); l15-oddbeam: one set in at a wrong angle
    l15-gate        a security gate's shutter, rolled up into the lintel over a machine room's door; cube
    l15-machine     machine casing, stacked into machines: panel, vent, screen and lamp bank (dead or lit; the lit
                    ones hum), hatch, warning band, burnt, burnt vent, an incinerator's mouth, a press; cubes
    l15-console     a white console with its screen: dead, ACCESS DENIED, the radar; JSON shape, four sides
    l15-labbench    a lab bench: plain, sink, equipment, glassware; JSON shape, four sides
    l15-locker      a pair of steel lockers two blocks high (lower, upper), closed or ajar; JSON shape, four sides
    l15-corpse      a body in a lab coat, long dead: sitting against a wall, or lying (head, feet), with a makeshift
                    spear or without; JSON shape, four sides
    l15-rods        a heap of steel rods off the press, on two chocks; JSON shape, four sides
    l15-stage       the lecture hall's stage, half a block high
    l15-stardoor    a steel doorframe standing on its own, a night sky in it and a small blue star (lower, upper)
    sounds/ambient/15/  hum (the halls' constant machine drone and the engines far off), machine (a running machine,
                    on its lit casing blocks), airhandler (the service passages), heartbeat (a ticking like a slow
                    heart, where the power is out), beep1-3 (far-off beeps)

Textures are 32 px a block (block/15/), shapes 16 units (block/15/); every JSON shape names its texture keys one by one
and its blocktype names no textures. Run from the repo root:  python tools/gen_15.py   (under tools/locked.sh run)
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

import matlib as M
from modelkit import box, turn, textures as shape_keys
from oggutil import write_ogg
from gen_entity_sounds import RATE

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "15")
SHAPES = os.path.join(ASSETS, "shapes", "block", "15")
BLOCKS = os.path.join(ASSETS, "blocktypes", "15")
SOUNDS = os.path.join(ASSETS, "sounds", "ambient", "15")
S = 32
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CLOTH = {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}

WHITE = (222, 225, 224)      # the panels: a cool white, never pure
STEEL = (206, 211, 216)      # the white steel of the beams
GREY = (132, 132, 128)       # bare service concrete
INK = (14, 14, 16)           # vantablack-ish paint
CASE = (196, 200, 202)       # machine casing


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def save(img, name):
    assert img.size[0] % 8 == 0 and img.size[1] % 8 == 0, name
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def rect(img, x0, y0, x1, y1, c, a=255):
    """Fills x0..x1, y0..y1 inclusive."""
    px = img.load()
    for y in range(max(0, y0), min(img.size[1], y1 + 1)):
        for x in range(max(0, x0), min(img.size[0], x1 + 1)):
            px[x, y] = tuple(int(v) for v in c[:3]) + (a,)


def blend(img, x, y, c, t):
    px = img.load()
    if 0 <= x < img.size[0] and 0 <= y < img.size[1]:
        r, g, b, a = px[x, y]
        px[x, y] = (M.clamp(r + (c[0] - r) * t), M.clamp(g + (c[1] - g) * t), M.clamp(b + (c[2] - b) * t), a)


def soot(img, seed, dark=0.45, patches=0.35):
    """Fire's mark: the whole face darkened toward a sooty brown-black, then broad soft patches darker still."""
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (M.clamp(r + (34 - r) * dark), M.clamp(g + (31 - g) * dark), M.clamp(b + (28 - b) * dark), a)
    M.grime(img, patches, seed=seed, color=(20, 18, 16), cells=(16, 8, 4), cover=0.6)
    return img


# ---------------- A pixel font (5 x 7) for codes, labels and screens ----------------

FONT = {
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "e": ["00000", "00000", "01110", "10001", "11111", "10000", "01110"],
    "c": ["00000", "00000", "01110", "10000", "10000", "10001", "01110"],
    "o": ["00000", "00000", "01110", "10001", "10001", "10001", "01110"],
    "x": ["00000", "00000", "10001", "01010", "00100", "01010", "10001"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    " ": ["00000"] * 7,
}

# Small 3 x 5 glyphs for screens
SMALL = {
    "A": ["010", "101", "111", "101", "101"], "C": ["011", "100", "100", "100", "011"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "I": ["111", "010", "010", "010", "111"], "L": ["100", "100", "100", "100", "111"],
    "N": ["101", "111", "111", "111", "101"], "O": ["111", "101", "101", "101", "111"], "S": ["011", "100", "010", "001", "110"],
    "V": ["101", "101", "101", "101", "010"], "2": ["110", "001", "010", "100", "111"], "4": ["101", "101", "111", "001", "001"],
    "5": ["111", "100", "110", "001", "110"], "P": ["110", "101", "110", "100", "100"], ".": ["000", "000", "000", "000", "010"], " ": ["000"] * 5,
}


def text(img, x, y, s, c, font=FONT, sy=1, a=255):
    """Draws s with its top-left at (x, y); sy stretches each row (tall stencil letters). Returns the width drawn."""
    w = len(next(iter(font.values()))[0])
    cx = x
    for ch in s:
        g = font.get(ch, font[" "])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for k in range(sy):
                        blend(img, cx + gx, y + gy * sy + k, c, a / 255)
        cx += w + 1
    return cx - x - 1


# ======================================================================== Wall textures

def panel_wall(seed, plate=False):
    """White panelled concrete: a smooth cool-white ground, a recessed panel joint round the block (so blocks meet at a
    groove), a faint horizontal reveal at mid-height; the plate variant has a small screwed service plate."""
    img = M.concrete(seed=seed, base=WHITE, grain=2, mottle=3, aggregate=0.0, pores=0.004, hue=1.0)
    M.emboss_lines(img, xs=(0,), ys=(0,), strength=0.16)
    M.emboss_lines(img, ys=(16,), strength=0.05)
    if plate:
        x0, y0 = 9, 19
        rect(img, x0, y0, x0 + 13, y0 + 8, M.lift(WHITE, -6))
        M.bevel(img, (x0, y0, x0 + 14, y0 + 9), strength=0.12)
        for sx, sy in ((x0 + 1, y0 + 1), (x0 + 12, y0 + 1), (x0 + 1, y0 + 7), (x0 + 12, y0 + 7)):
            M.screw(img, sx, sy)
    M.grime(img, 0.03, seed=seed + 1, color=(150, 152, 150), cells=(8, 4))
    return img


def kickplate():
    img = panel_wall(15003)
    steel = M.brushed_metal(seed=15004, base=(176, 182, 188), direction="h", streak=5, sheen=6)
    px, sp = img.load(), steel.load()
    for y in range(22, S):
        for x in range(S):
            px[x, y] = sp[x, y]
    M.emboss_lines(img, ys=(22,), raised=True, strength=0.22)
    M.grime(img, 0.08, seed=15005, color=(96, 98, 100), bias="bottom")
    return img


def beam(seed, etched=False):
    """The white steel of a pilaster: brushed vertically, a flange either side (a groove, lit on its right), rivets."""
    img = M.brushed_metal(seed=seed, base=STEEL, direction="v", streak=6, sheen=8)
    M.emboss_lines(img, xs=(4, 27), strength=0.22)
    for y in (4, 12, 20, 28):
        for x in (2, 29):
            M.touch(img, x, y, 0.25)
            M.touch(img, x, y + 1, -0.2)
    if etched:
        # Arabesque symbols cut into the steel: loops, hooks and a spiral, a groove with a lit lower lip
        rng = random.Random(seed)
        for cx, cy in ((15.5, 9), (15.5, 23)):
            for t in np.linspace(0, 4 * math.pi, 120):
                r = 1.2 + 0.55 * t
                x, y = int(round(cx + r * math.cos(t))), int(round(cy + 0.8 * r * math.sin(t)))
                if 6 <= x <= 25:
                    M.touch(img, x, y, -0.3)
                    M.touch(img, x, y + 1, 0.12)
            for _ in range(3):
                a = rng.uniform(0, 2 * math.pi)
                x, y = int(cx + 6 * math.cos(a)), int(cy + 5 * math.sin(a))
                for k in range(4):
                    M.touch(img, x + k, y - (k % 2), -0.25)
        M.emboss_lines(img, ys=(16,), strength=0.12)
    return img


def wall_textures():
    save(panel_wall(15001), "wall-panel")
    save(panel_wall(15002, plate=True), "wall-panelb")
    save(kickplate(), "wall-base")
    grey = M.concrete(seed=15010, base=GREY, grain=4, mottle=7, aggregate=0.06, joints=(16,), patches=4)
    save(grey, "wall-grey")
    gb = grey.copy()
    M.grime(gb, 0.18, seed=15011, bias="bottom", color=(70, 66, 58))
    save(gb, "wall-greybase")
    sc = panel_wall(15012)
    soot(sc, 15013, dark=0.3, patches=0.3)
    M.drips(sc, n=4, seed=15014, color=(30, 28, 26), length=(10, 26), strength=0.5)
    save(sc, "wall-scorched")
    save(beam(15020), "wall-beam")
    save(beam(15021, etched=True), "wall-etched")


# ======================================================================== Wall decorations (one face of a wall block)

def deco_base():
    return panel_wall(15001)


def screen(img, x0, y0, x1, y1, bezel=(60, 64, 70), glass=(16, 18, 22)):
    rect(img, x0, y0, x1, y1, bezel)
    M.bevel(img, (x0, y0, x1 + 1, y1 + 1), strength=0.2)
    rect(img, x0 + 2, y0 + 2, x1 - 2, y1 - 2, glass)
    # A faint diagonal reflection on the dead glass
    for k in range(0, 6):
        blend(img, x0 + 4 + k, y0 + 3 + k // 2, (70, 76, 84), 0.25)


def deco_textures():
    # A dead hand scanner: a dark palm plate in a steel surround, the outline of a hand, a dead LED
    img = deco_base()
    rect(img, 9, 5, 22, 26, (176, 182, 188))
    M.bevel(img, (9, 5, 23, 27), strength=0.22)
    rect(img, 11, 7, 20, 22, (22, 26, 30))
    hand = ["0000110000", "0001111000", "0101111010", "0101111010", "0111111110", "0111111110", "0011111110",
            "0011111100", "0011111100", "0001111000", "0001111000", "0001111000"]
    for gy, row in enumerate(hand):
        for gx, b in enumerate(row):
            if b == "1":
                blend(img, 11 + gx, 9 + gy, (58, 70, 80), 0.6)
    rect(img, 15, 24, 16, 25, (70, 20, 18))
    save(img, "deco-scanner")
    # A dead display
    img = deco_base()
    screen(img, 3, 6, 28, 24)
    save(img, "deco-display")
    # The radar: levels as shapes joined by green lines, "AVALON 2.4" (Wikidot's terminals)
    img = deco_base()
    screen(img, 2, 4, 29, 27, glass=(4, 14, 8))
    green, dim = (70, 230, 110), (30, 110, 56)
    for r in (5, 9):
        for t in np.linspace(0, 2 * math.pi, 64):
            blend(img, int(round(15.5 + r * math.cos(t))), int(round(16 + r * 0.8 * math.sin(t))), dim, 0.8)
    nodes = [(9, 11), (21, 10), (12, 21), (22, 20), (16, 15)]
    for (ax, ay), (bx, by) in ((nodes[0], nodes[4]), (nodes[1], nodes[4]), (nodes[2], nodes[4]), (nodes[3], nodes[1]), (nodes[2], nodes[0])):
        for t in np.linspace(0, 1, 24):
            blend(img, int(round(ax + (bx - ax) * t)), int(round(ay + (by - ay) * t)), green, 0.7)
    for i, (nx, ny) in enumerate(nodes):
        shape_ = [(0, 0), (1, 0), (0, 1), (1, 1)] if i % 2 else [(0, -1), (-1, 0), (1, 0), (0, 1), (0, 0)]
        for dx, dy in shape_:
            blend(img, nx + dx, ny + dy, (200, 255, 200), 1.0)
    text(img, 5, 6, "AVALON 2.4", green, SMALL)
    save(img, "deco-radar")
    # The ESCAPE panel: a steel panel, a red button under "ESCAPE", a strip of small print
    img = deco_base()
    rect(img, 4, 4, 27, 27, (170, 176, 182))
    M.bevel(img, (4, 4, 28, 28), strength=0.22)
    text(img, 6, 6, "ESCAPE", INK, SMALL)
    for y in range(13, 22):
        for x in range(10, 22):
            d = math.hypot(x - 15.5, y - 17)
            if d < 5.2:
                blend(img, x, y, (186, 30, 26) if d < 4.2 else (90, 20, 18), 1.0)
                if d < 2.5 and y < 16:
                    blend(img, x, y, (240, 110, 100), 0.5)
    for y in (24, 26):
        for x in range(7, 25):
            if (x * 7 + y) % 5:
                blend(img, x, y, (70, 72, 76), 0.6)
    save(img, "deco-escape")
    # Views of elsewhere on the displays: Level 18's rainbow hallways, a storm on the plains, the Lobby
    for n, painter in enumerate((view_rainbow, view_storm, view_lobby)):
        img = deco_base()
        screen(img, 2, 5, 29, 26)
        painter(img, 4, 7, 27, 24)
        save(img, f"deco-view{n}")
    # A vent grille at the foot of the wall; one with a code scrawled beside it in marker (Fandom's "H15", "eco3x10c")
    for n, code in enumerate((None, "eco3")):
        img = deco_base()
        rect(img, 4, 14, 27, 29, (150, 156, 160))
        M.bevel(img, (4, 14, 28, 30), strength=0.2)
        for y in range(16, 28, 2):
            rect(img, 6, y, 25, y, (40, 44, 48))
            rect(img, 6, y + 1, 25, y + 1, (190, 196, 200))
        if code:
            text(img, 5, 3, code, (40, 40, 120), FONT, a=200)
            for k in range(6):
                blend(img, 26 + (k // 3), 4 + k, (40, 40, 120), 0.8)
        save(img, f"deco-vent{n}")
    # A wooden door set in the wall, opening on nothing (Fandom's "wooden doors in walls")
    for part in ("lower", "upper"):
        img = M.wood_planks(seed=15040, base=(128, 92, 58), planks=3, direction="v", knots=1)
        if part == "upper":
            M.emboss_lines(img, ys=(3,), strength=0.25)
            M.bevel(img, (5, 6, 27, 30), strength=0.18)
        else:
            M.bevel(img, (5, 2, 27, 26), strength=0.18)
            for y in range(4, 7):
                for x in (23, 24):
                    blend(img, x, 24 - y + 2, (200, 180, 90), 0.9)
        rect(img, 0, 0, 1, S - 1, WHITE)
        rect(img, 30, 0, 31, S - 1, WHITE)
        if part == "lower":
            rect(img, 24, 1, 26, 3, (190, 168, 80))  # the knob
        save(img, f"deco-wooddoor{part}")
    # Dried blood smeared down the wall
    img = deco_base()
    M.drips(img, n=5, seed=15050, color=(70, 18, 14), length=(10, 28), strength=0.75, start=2, width=2)
    M.stain(img, seed=15051, radius=7, color=(76, 20, 16), strength=0.55, at=(14, 10))
    save(img, "deco-blood")
    # The room codes: tall black stencil letters (Fandom: black numbers on the walls; H labs, e stores)
    for n, code in enumerate(CODES):
        img = deco_base()
        w = len(code) * 6 - 1
        text(img, (S - w) // 2, 9, code, INK, FONT, sy=2)
        save(img, f"deco-code{n}")


CODES = ["H15", "H04", "e03", "e10", "M12", "M27", "D21", "D06", "K09", "K02", "C07", "C11", "L02", "L14", "S30", "S08"]


def view_rainbow(img, x0, y0, x1, y1):
    """Level 18: a hallway of rainbow bands, drawn in one-point perspective."""
    cols = [(220, 60, 60), (230, 150, 50), (230, 220, 70), (70, 190, 90), (60, 120, 220), (150, 80, 200)]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = max(abs(x - cx) / ((x1 - x0) / 2), abs(y - cy) / ((y1 - y0) / 2))
            band = int(d * 6) % 6
            c = cols[band]
            k = 0.45 + 0.55 * d
            blend(img, x, y, tuple(v * k for v in c), 1.0)


def view_storm(img, x0, y0, x1, y1):
    """A storm on the plains: a dark sky, a funnel, a strip of grass (the Storm Chaser's)."""
    rng = random.Random(15060)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = (y - y0) / (y1 - y0)
            c = (40 + 30 * t, 46 + 30 * t, 56 + 26 * t) if y < y1 - 4 else (60, 90, 50)
            blend(img, x, y, c, 1.0)
    for y in range(y0 + 2, y1 - 3):
        w = 1 + (y - y0) // 5
        cx = 18 + int(2 * math.sin(y / 2.5))
        for x in range(cx - w, cx + w + 1):
            blend(img, x, y, (24, 26, 30), 0.85)
    for _ in range(3):
        x = rng.randint(x0 + 2, x1 - 2)
        for y in range(y0, y0 + 6):
            blend(img, x + (y % 2), y, (230, 230, 250), 0.7)


def view_lobby(img, x0, y0, x1, y1):
    """The Lobby: yellow walls and a lit ceiling down a hall."""
    cx = (x0 + x1) / 2
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            t = (y - y0) / (y1 - y0)
            if t < 0.3:
                c = (232, 226, 180) if (x + y) % 6 else (250, 248, 220)
            elif t > 0.75:
                c = (150, 126, 70)
            else:
                c = (200, 180, 100)
            if abs(x - cx) < 2 + (1 - abs(t - 0.5)) * 2 and 0.3 <= t <= 0.75:
                c = tuple(v * 0.6 for v in c)
            blend(img, x, y, c, 1.0)


# ======================================================================== Floors, ceilings, steel, glass

def ceramic(seed):
    return M.tile(seed=seed, base=(214, 218, 218), grout=(168, 172, 174), pitch=16, grout_w=1, jitter=3, uneven=2)


def floor_textures():
    save(ceramic(15100), "floor-ceramic")
    worn = ceramic(15101)
    M.scratches(worn, n=10, seed=15102, light=0.12)
    M.grime(worn, 0.1, seed=15103, color=(150, 146, 136))
    save(worn, "floor-worn")
    save(M.rubber(seed=15104, base=(70, 72, 76), pattern="diamond", pitch=8), "floor-coating")
    save(M.carpet(seed=15105, base=(92, 100, 114), tone2=(76, 84, 98), pile=8), "floor-carpet")
    # Steel grating over the dark: bars every 4 px one way, every 8 the other, lit on top
    g = M.new((S, S), (14, 15, 16))
    for x in range(0, S, 4):
        rect(g, x, 0, x, S - 1, (132, 136, 138))
    for y in range(0, S, 8):
        rect(g, 0, y, S - 1, y, (150, 154, 156))
        rect(g, 0, y + 1, S - 1, y + 1, (90, 92, 94))
    M.rust(g, 0.12, seed=15106)
    save(g, "floor-grating")
    # The floor lights along the foot of the halls' walls: a frosted lens in a steel frame (lit: glowing; dead: grey)
    for name, lens in (("floor-strip", (236, 244, 252)), ("floor-stripdead", (120, 126, 130))):
        img = ceramic(15100)
        rect(img, 3, 3, 28, 28, (170, 176, 180))
        M.bevel(img, (3, 3, 29, 29), strength=0.2)
        rect(img, 5, 5, 26, 26, lens)
        for y in range(5, 27):
            for x in range(5, 27):
                if (x + y) % 4 == 0:
                    blend(img, x, y, tuple(v * 0.93 for v in lens), 1.0)
        save(img, name)
    blood = ceramic(15110)
    M.stain(blood, seed=15111, radius=10, color=(84, 22, 16), strength=0.7, at=(12, 14), ring=0.3)
    M.stain(blood, seed=15112, radius=4, color=(70, 18, 14), strength=0.6, at=(24, 24))
    save(blood, "floor-blood")
    scorch = ceramic(15113)
    soot(scorch, 15114, dark=0.35, patches=0.35)
    save(scorch, "floor-scorch")
    # A gate's tread plate
    tread = M.brushed_metal(seed=15115, base=(150, 154, 158), direction="h")
    for y in range(2, S, 6):
        for x in range((y // 6) % 2 * 3, S, 6):
            for dx in range(3):
                M.touch(tread, x + dx, y - (dx == 1), 0.25)
                M.touch(tread, x + dx, y + 1, -0.15)
    save(tread, "floor-track")
    dust = ceramic(15116)
    M.grime(dust, 0.35, seed=15117, color=(168, 164, 156), cells=(16, 8), cover=0.9)
    save(dust, "floor-dust")


def ceiling_textures():
    # A white ceiling panel in a fine grid
    img = M.plaster(seed=15200, base=(228, 232, 234), grain=2, mottle=3, roller=0.2)
    M.emboss_lines(img, xs=(0, 16), ys=(0, 16), strength=0.12)
    save(img, "ceiling-panel")
    for name, lit in (("ceiling-led", 1.0), ("ceiling-off", 0.0)):
        save(M.troffer_lens(seed=15201, lit=lit, lens=(234, 240, 246), frame=(214, 218, 222), cell=2, tubes=4,
                            glow=(246, 250, 255)), name)
    save(M.concrete(seed=15202, base=(118, 118, 114), grain=4, mottle=6, aggregate=0.05, border=1), "ceiling-service")
    vent = M.plaster(seed=15203, base=(228, 232, 234), grain=2, mottle=3, roller=0.2)
    rect(vent, 3, 3, 28, 28, (180, 186, 190))
    M.bevel(vent, (3, 3, 29, 29), strength=0.2)
    for y in range(5, 27, 3):
        rect(vent, 5, y, 26, y, (30, 34, 38))
    save(vent, "ceiling-vent")


def steel_textures():
    rib = M.brushed_metal(seed=15300, base=STEEL, direction="h", streak=6, sheen=8)
    for x in range(2, S, 8):
        M.touch(rib, x, 3, 0.25)
        M.touch(rib, x, 4, -0.2)
        M.touch(rib, x, 27, 0.25)
        M.touch(rib, x, 28, -0.2)
    save(rib, "steel")
    gate = M.brushed_metal(seed=15301, base=(150, 156, 162), direction="h")
    M.emboss_lines(gate, ys=(4, 8, 12, 16, 20, 24, 28), raised=True, strength=0.2)
    for y in range(24, 31):
        for x in range(S):
            if ((x + y) // 4) % 2 == 0:
                blend(gate, x, y, (214, 176, 40), 0.9)
            else:
                blend(gate, x, y, (26, 26, 28), 0.9)
    save(gate, "gate")
    clear = M.glass(seed=15302, base=(196, 222, 228), alpha=80, streaks=2, dust=0.01)
    save(clear, "glass-clear")
    cracked = clear.copy()
    rng = random.Random(15303)
    px = cracked.load()
    cx, cy = 13, 15
    for _ in range(7):
        a = rng.uniform(0, 2 * math.pi)
        x, y = float(cx), float(cy)
        for _ in range(rng.randint(8, 18)):
            a += rng.uniform(-0.35, 0.35)
            x += math.cos(a)
            y += math.sin(a)
            ix, iy = int(round(x)) % S, int(round(y)) % S
            px[ix, iy] = (236, 244, 246, 210)
    for t in np.linspace(0, 2 * math.pi, 40):
        ix, iy = int(round(cx + 5 * math.cos(t))) % S, int(round(cy + 4 * math.sin(t))) % S
        px[ix, iy] = (230, 240, 242, 170)
    save(cracked, "glass-cracked")
    # The stage: dark grey boards
    save(M.wood_planks(seed=15304, base=(70, 70, 74), planks=4, direction="h", contrast=0.5), "stage")


# ======================================================================== Machine casing

def casing(seed, base=CASE):
    img = M.painted_metal(seed=seed, base=base, grain=2, mottle=3, panel=True, chips=1, under=(120, 124, 128), screws=True)
    return img


def machine_textures():
    save(casing(15400), "machine-panel")
    top = casing(15401)
    for y in range(8, 25, 3):
        rect(top, 8, y, 23, y, (60, 64, 68))
    save(top, "machine-top")
    vent = casing(15402)
    for y in range(5, 28, 3):
        rect(vent, 4, y, 27, y, (40, 44, 48))
        rect(vent, 4, y + 1, 27, y + 1, (226, 230, 232))
    save(vent, "machine-vent")
    for name, lit in (("machine-screen", False), ("machine-screenlit", True)):
        img = casing(15403)
        screen(img, 4, 5, 27, 22, glass=(6, 20, 14) if lit else (16, 18, 22))
        if lit:
            rng = random.Random(15404)
            for y in range(8, 20, 2):
                n = rng.randint(4, 16)
                for x in range(7, 7 + n):
                    if rng.random() < 0.8:
                        blend(img, x, y, (110, 240, 160), 1.0)
        for x in range(6, 26, 4):
            rect(img, x, 25, x + 2, 27, (60, 64, 68))
        save(img, name)
    for name, lit in (("machine-lights", False), ("machine-lightslit", True)):
        img = casing(15405)
        rng = random.Random(15406)
        cols = [(70, 230, 90), (240, 180, 40), (230, 60, 50), (80, 160, 240)]
        for y in range(5, 28, 5):
            for x in range(5, 28, 5):
                c = cols[rng.randint(0, 3)]
                on = lit and rng.random() < 0.7
                rect(img, x, y, x + 2, y + 2, c if on else tuple(v * 0.3 + 30 for v in c))
                if on:
                    blend(img, x, y, (255, 255, 255), 0.4)
        save(img, name)
    hatch = casing(15407)
    rect(hatch, 6, 4, 25, 29, M.lift(CASE, -5))
    M.bevel(hatch, (6, 4, 26, 30), strength=0.25)
    rect(hatch, 21, 14, 23, 19, (70, 74, 78))
    rect(hatch, 9, 7, 16, 10, (214, 176, 40))
    save(hatch, "machine-hatch")
    warn = casing(15408)
    for y in range(10, 22):
        for x in range(S):
            blend(warn, x, y, (214, 176, 40) if ((x + y) // 4) % 2 == 0 else (24, 24, 26), 0.95)
    save(warn, "machine-warning")
    burnt = casing(15409)
    soot(burnt, 15410, dark=0.6)
    M.rust(burnt, 0.2, seed=15411)
    save(burnt, "machine-burnt")
    bv = Image.open(os.path.join(TEX, "machine-vent.png")).convert("RGBA")
    soot(bv, 15412, dark=0.6)
    save(bv, "machine-burntvent")
    bt = top.copy()
    soot(bt, 15413, dark=0.6)
    save(bt, "machine-burnttop")
    furnace = M.riveted_plate(seed=15414, base=(70, 68, 66))
    rect(furnace, 5, 8, 26, 27, (14, 12, 12))
    M.bevel(furnace, (5, 8, 27, 28), strength=0.3)
    for x in range(7, 26, 3):
        rect(furnace, x, 10, x, 26, (54, 50, 48))
    M.grime(furnace, 0.4, seed=15415, color=(20, 18, 16))
    save(furnace, "machine-furnace")
    press = M.brushed_metal(seed=15416, base=(150, 156, 162), direction="v")
    rect(press, 11, 0, 20, 18, (186, 190, 194))
    M.bevel(press, (11, 0, 21, 19), strength=0.25)
    rect(press, 6, 19, 25, 23, (70, 74, 78))
    for x in range(6, 26):
        if (x // 3) % 2 == 0:
            blend(press, x, 25, (214, 176, 40), 1.0)
            blend(press, x, 26, (214, 176, 40), 1.0)
    save(press, "machine-press")


# ======================================================================== Prop textures

def prop_textures():
    save(M.painted_metal(seed=15500, base=(226, 228, 228), panel=False, chips=1), "white")
    save(M.painted_metal(seed=15501, base=(160, 166, 172), panel=False, chips=2), "steelgrey")
    save(M.rubber(seed=15502, base=(30, 32, 34)), "epoxy")
    for name, lit in (("console-dead", 0), ("console-denied", 1), ("console-radar", 2)):
        img = M.new((S, S), (18, 20, 24))
        if lit == 1:
            img = M.new((S, S), (40, 6, 6))
            text(img, 2, 6, "ACCESS", (250, 90, 80), SMALL)
            text(img, 2, 13, "DENIED", (250, 90, 80), SMALL)
            for y in (21, 24, 27):
                for x in range(2, 29):
                    if (x * 3 + y) % 7:
                        blend(img, x, y, (160, 60, 50), 0.6)
        elif lit == 2:
            img = M.new((S, S), (4, 16, 8))
            for r in (5, 10, 14):
                for t in np.linspace(0, 2 * math.pi, 80):
                    blend(img, int(round(16 + r * math.cos(t))), int(round(16 + r * math.sin(t))), (40, 140, 70), 0.8)
            for t in np.linspace(0, 1, 16):
                blend(img, int(16 + 13 * t), int(16 - 7 * t), (110, 250, 140), 1.0)
            for nx, ny in ((9, 10), (22, 21), (12, 23)):
                rect(img, nx, ny, nx + 1, ny + 1, (200, 255, 200))
        else:
            for k in range(8):
                blend(img, 6 + k, 5 + k // 2, (60, 66, 74), 0.4)
        save(img, name)
    save(M.painted_metal(seed=15503, base=(208, 212, 214), panel=True, chips=1), "lockerdoor")
    door = Image.open(os.path.join(TEX, "lockerdoor.png")).convert("RGBA")
    for y in (4, 6, 8, 10):
        rect(door, 4, y, 27, y, (60, 64, 68))
    save(door, "lockervents")
    save(M.new((S, S), (10, 10, 12)), "dark")
    # The dead: a lab coat gone grey with dust and stained; dark trousers; dried skin; bone
    coat = M.fabric(seed=15504, base=(206, 206, 198), weave="plain", contrast=6)
    M.stain(coat, seed=15505, radius=6, color=(90, 30, 20), strength=0.55, at=(10, 18))
    M.grime(coat, 0.18, seed=15506, color=(140, 136, 126))
    save(coat, "labcoat")
    save(M.fabric(seed=15507, base=(52, 56, 64), weave="twill", contrast=8), "trousers")
    save(M.noise_hv((122, 98, 76), amp=5, seed=15508, mottle=10), "skin")
    save(M.noise_hv((214, 206, 182), amp=4, seed=15509, mottle=6), "bone")
    save(M.rubber(seed=15510, base=(36, 32, 30)), "shoe")
    save(M.brushed_metal(seed=15511, base=(120, 124, 128), direction="h"), "pipe")
    save(M.glass(seed=15512, base=(200, 230, 236), alpha=170, streaks=1), "shard")
    save(M.fabric(seed=15513, base=(150, 130, 96), weave="plain"), "tape")
    rods = M.brushed_metal(seed=15514, base=(150, 156, 162), direction="h", streak=4)
    for y in range(0, S, 4):
        M.emboss_lines(rods, ys=(y,), strength=0.3)
    save(rods, "rods")
    save(M.wood_planks(seed=15515, base=(120, 90, 60), planks=2), "chock")
    # The star door: a night sky with small stars and one blue star
    sky = M.new((S, S), (4, 6, 14))
    rng = random.Random(15516)
    p = sky.load()
    for _ in range(26):
        x, y = rng.randint(0, 31), rng.randint(0, 31)
        b = rng.randint(120, 240)
        p[x, y] = (b, b, min(255, b + 20), 255)
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 15.5, y - 13.5)
            if d < 6:
                r, g, b, a = p[x, y]
                k = max(0.0, 1 - d / 6) ** 2
                p[x, y] = (M.clamp(r + 60 * k), M.clamp(g + 130 * k), M.clamp(b + 230 * k), 255)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        p[15 + dx, 13 + dy] = (220, 240, 255, 255)
    save(sky, "starsky")
    save(M.new((S, S), (150, 200, 255)), "starglow")
    # Lab bench parts: the sink's steel, glassware, an instrument's casing
    save(M.brushed_metal(seed=15517, base=(178, 182, 186), direction="h"), "sinksteel")
    save(M.glass(seed=15518, base=(210, 236, 240), alpha=140, streaks=1), "flask")
    save(M.painted_metal(seed=15519, base=(70, 84, 96), panel=False, chips=0), "instrument")


# ======================================================================== Shapes

def shape(name, elements):
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: "backrooms:block/15/" + k for k in shape_keys(elements)}, "elements": elements}
    write_json(os.path.join(SHAPES, name + ".json"), data)
    return "backrooms:block/15/" + name


def console_shape(state):
    """A white console, its screen to the north: a desk body, a sloped key panel, a screen housing at the back."""
    els = [
        box("Body", (1, 0, 3), (15, 9, 15), {"all": "white", "top": "steelgrey"}),
        box("Keys", (1.5, 9, 3.5), (14.5, 10, 9), {"all": "steelgrey", "top": "epoxy"}, rot=(-22.5, 0, 0), origin=(8, 9, 9)),
        box("Housing", (2, 9, 10), (14, 16, 14), "white"),
        box("Screen", (3, 10, 9.6), (13, 15, 10), "console-" + state, faces=("north",), glow=180 if state != "dead" else 0),
        box("Plinth", (1.5, 0, 2.5), (14.5, 1, 3), "steelgrey", faces=("north", "east", "west")),
    ]
    return shape("l15-console-" + state, els)


def bench_shape(kind):
    """A lab bench, its front (cupboard doors) to the north: a white carcase, a black epoxy top, and on it a sink, an instrument or glassware."""
    els = [
        box("Carcase", (0.5, 0, 1.5), (15.5, 13, 15.5), {"all": "white", "front": "lockerdoor"}),
        box("Top", (0, 13, 1), (16, 14.5, 16), "epoxy"),
        box("Kick", (0.5, 0, 1), (15.5, 1.5, 1.5), "dark", faces=("north", "east", "west")),
    ]
    if kind == "sink":
        els += [box("Basin", (4, 14.5, 4), (12, 14.75, 11), "sinksteel", faces=("up",)),
                box("Tap", (7.5, 14.5, 12), (8.5, 18, 13), "sinksteel"),
                box("Spout", (7.5, 17, 9.5), (8.5, 18, 12), "sinksteel")]
    elif kind == "equipment":
        els += [box("Instrument", (3, 14.5, 5), (11, 20, 13), {"all": "instrument", "front": "machine-lights"}),
                box("Arm", (11, 14.5, 7), (13, 19, 9), "steelgrey")]
    elif kind == "glassware":
        for i, (x, z, h) in enumerate(((3, 5, 4), (6.5, 9, 6), (10, 4, 3.5), (12, 10, 5))):
            els.append(box(f"Flask{i}", (x, 14.5, z), (x + 2, 14.5 + h, z + 2), "flask"))
    return shape("l15-labbench-" + kind, els)


def locker_shape(part, state):
    """Two steel lockers side by side, two blocks high (lower and upper), their doors to the north; ajar: the left door swung open."""
    lower = part == "lower"
    y0, y1 = (0, 16) if lower else (0, 15)
    els = [box("Carcase", (0.5, y0, 2), (15.5, y1, 15.5), "steelgrey")]
    if lower:
        els.append(box("Plinth", (0.5, 0, 1.6), (15.5, 1, 2), "dark", faces=("north",)))
    for i, x0 in enumerate((0.75, 8.25)):
        tex = "lockervents" if not lower else "lockerdoor"
        if state == "ajar" and i == 0:
            els.append(box("DoorOpen", (x0, y0 + (1 if lower else 0), -5), (x0 + 0.5, y1 - 0.25, 2), tex, faces=("east", "west", "up", "down")))
            els.append(box("Inside", (x0 + 0.25, y0 + 1, 2.1), (x0 + 6.75, y1, 2.2), "dark", faces=("north",)))
        else:
            els.append(box(f"Door{i}", (x0, y0 + (1 if lower else 0), 1.6), (x0 + 7, y1, 2), tex, faces=("north", "east", "west")))
            if lower:
                els.append(box(f"Handle{i}", (x0 + 5.5, 12, 1.1), (x0 + 6, 15, 1.6), "dark", faces=("north", "east", "west", "up", "down")))
    if not lower:
        els.append(box("Top", (0.5, 15, 2), (15.5, 16, 15.5), "steelgrey"))
    return shape(f"l15-locker-{part}-{state}", els)


def spear():
    """A makeshift spear lying on the floor along x: a length of pipe, a glass blade taped on."""
    return [box("Shaft", (0, 0, 13), (13, 0.75, 13.75), "pipe"),
            box("Tape", (12, 0, 12.9), (14, 0.9, 13.85), "tape"),
            box("Blade", (13.5, 0, 13), (16, 0.5, 13.75), "shard")]


def corpse_shape(pose, with_spear):
    """A body in a lab coat. Sitting: its back to the south (the wall), legs out to the north. Lying (head to the south,
    feet to the north, across two blocks): the head block holds the head and the trunk, the feet block the legs."""
    if pose == "sitting":
        els = [
            box("Trunk", (4, 2, 10), (12, 11, 14), {"all": "labcoat"}, rot=(-10, 0, 0), origin=(8, 2, 14)),
            box("Head", (5.5, 11, 9.5), (10.5, 15, 13.5), "skin", rot=(-20, 0, 0), origin=(8, 11, 12)),
            box("CoatSkirt", (3.5, 0, 6), (12.5, 3, 14), "labcoat"),
            box("LegL", (4.5, 0, 0.5), (7.5, 2.5, 7), "trousers"),
            box("LegR", (8.5, 0, 1.5), (11.5, 2.5, 7), "trousers"),
            box("ShoeL", (4.25, 0, -0.5), (7.75, 3, 1.5), "shoe"),
            box("ShoeR", (8.25, 0, 0.5), (11.75, 3, 2.5), "shoe"),
            box("ArmL", (2.5, 1, 7), (4.5, 8, 11), "labcoat"),
            box("ArmR", (11.5, 0, 4), (13.5, 2, 11), "labcoat"),
            box("HandR", (11.5, 0, 2.5), (13.5, 1.5, 4), "bone"),
        ]
    elif pose == "head":
        els = [
            box("Head", (5.5, 0, 11), (10.5, 4.5, 15.5), "skin"),
            box("Jaw", (6.5, 0, 10.2), (9.5, 1.5, 11), "bone"),
            box("Trunk", (3.5, 0, 0), (12.5, 4, 10.5), "labcoat"),
            box("ArmL", (1.5, 0, 1), (3.5, 2.5, 10), "labcoat"),
            box("ArmR", (12.5, 0, 0), (14.5, 2.5, 7), "labcoat"),
            box("HandR", (12.5, 0, -1.5), (14.5, 1.5, 0), "bone"),
        ]
    else:
        els = [
            box("CoatSkirt", (3.5, 0, 9), (12.5, 3, 16), "labcoat"),
            box("LegL", (4, 0, 2), (7.5, 2.5, 13), "trousers"),
            box("LegR", (8.5, 0, 1), (12, 2.5, 12), "trousers"),
            box("ShoeL", (3.75, 0, 0), (7.75, 3.5, 2), "shoe"),
            box("ShoeR", (8.25, 0, -0.5), (12.25, 3.5, 1.5), "shoe"),
        ]
    if with_spear:
        els += spear()
    return shape(f"l15-corpse-{pose}-{'spear' if with_spear else 'plain'}", els)


def rods_shape():
    els = [box("ChockA", (1, 0, 2), (15, 1.5, 4), "chock"), box("ChockB", (1, 0, 12), (15, 1.5, 14), "chock")]
    for i, (x, y) in enumerate(((2, 1.5), (4.5, 1.5), (7, 1.5), (9.5, 1.5), (12, 1.5), (3.25, 3.5), (5.75, 3.5), (8.25, 3.5), (10.75, 3.5), (6, 5.5))):
        els.append(box(f"Rod{i}", (x, y, 0), (x + 2, y + 2, 16), "rods"))
    return shape("l15-rods", els)


def rib_shape():
    """A white steel I-beam along x at the top of a block: top flange, web, bottom flange."""
    els = [
        box("Top", (0, 14.5, 4), (16, 16, 12), "steel", faces=("north", "south", "down")),
        box("Web", (0, 10.5, 7), (16, 14.5, 9), "steel", faces=("north", "south")),
        box("Bottom", (0, 9, 4), (16, 10.5, 12), "steel", faces=("north", "south", "up", "down")),
    ]
    return shape("l15-rib", els)


def oddbeam_shape():
    """The same beam, set in at an angle no one would build: turned on two axes, poking out of the ceiling."""
    els = [
        box("Top", (-2, 10.5, 6), (18, 12, 10), "steel", rot=(0, 22.5, 22.5), origin=(8, 12, 8)),
        box("Web", (-2, 8, 7.25), (18, 10.5, 8.75), "steel", rot=(0, 22.5, 22.5), origin=(8, 12, 8)),
        box("Bottom", (-2, 6.5, 6), (18, 8, 10), "steel", rot=(0, 22.5, 22.5), origin=(8, 12, 8)),
    ]
    return shape("l15-oddbeam", els)


def stage_shape():
    return shape("l15-stage", [box("Stage", (0, 0, 0), (16, 8, 16), {"all": "stage", "side": "dark"})])


def stardoor_shape(part):
    """A steel doorframe two blocks high standing on its own, facing north and south, a night sky with a blue star in it."""
    lower = part == "lower"
    els = [
        box("PostL", (0.5, 0, 6.5), (2.5, 16, 9.5), "steel"),
        box("PostR", (13.5, 0, 6.5), (15.5, 16, 9.5), "steel"),
        box("Sky", (2.5, 0 if lower else 0, 7.75), (13.5, 16 if lower else 12, 8.25), "starsky", faces=("north", "south"), glow=120),
    ]
    if not lower:
        els.append(box("Lintel", (0.5, 12, 6.5), (15.5, 15, 9.5), "steel"))
        els.append(box("Star", (7.5, 2.5, 7.25), (8.5, 3.5, 8.75), "starglow", glow=255))
    else:
        els.append(box("Sill", (2.5, 0, 6.5), (13.5, 0.5, 9.5), "steel", faces=("up", "north", "south")))
    return shape("l15-stardoor-" + part, els)


# ======================================================================== Block types

def cuboid(b, angle=0):
    c = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if angle:
        c["rotateY"] = angle
    return c


def tex(name):
    return {"base": "block/15/" + name}


def cube_block(code, kinds, comment, material="Stone", sounds=STONE, extra=None, faces=None, inventory="*"):
    """A cube block, one variant per kind; kinds maps a state to its texture (or to a dict by face)."""
    tbt = {}
    for k, v in kinds.items():
        tbt[f"*-{k}"] = {"all": tex(v)} if isinstance(v, str) else {f: tex(t) for f, t in v.items()}
    data = {"code": code, "variantgroups": [{"code": "kind", "states": list(kinds)}], "texturesByType": tbt,
            "creativeinventory": {"general": [inventory], "backrooms": [inventory]},
            "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds}
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def json_block(code, groups, shapes, comment, collision, sounds=METAL, extra=None, inventory=None, material="Metal"):
    data = {"code": code, "variantgroups": groups, "shapeByType": shapes,
            "creativeinventory": {"general": [inventory], "backrooms": [inventory]},
            "blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 3, "sounds": sounds, "drops": []}
    data.update(collision)
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def sided(base):
    return {s: {"base": base, "rotateY": ROTATE[s]} for s in SIDES}


def blocktypes():
    cube_block("l15-wall", {"panel": "wall-panel", "panelb": "wall-panelb", "base": "wall-base", "grey": "wall-grey",
                            "greybase": "wall-greybase", "scorched": "wall-scorched", "beam": "wall-beam", "etched": "wall-etched"},
               "Level 15: white panelled concrete (panel; panelb, a service plate; base, the skirting's kick plate), the service passages' bare "
               "grey concrete, scorched panels, and the white steel of the pilasters (beam; etched with arabesque symbols)")

    # The decorations: a white wall block with one face dressed
    deco = {"scanner": "deco-scanner", "display": "deco-display", "radar": "deco-radar", "escape": "deco-escape",
            "vent": "deco-vent0", "ventcode": "deco-vent1", "wooddoorlower": "deco-wooddoorlower", "wooddoorupper": "deco-wooddoorupper",
            "blood": "deco-blood"}
    for n in range(3):
        deco[f"view{n}"] = f"deco-view{n}"
    for n in range(len(CODES)):
        deco[f"code{n}"] = f"deco-code{n}"
    tbt, light = {}, {}
    for k, t in deco.items():
        for s in SIDES:
            tbt[f"*-{k}-{s}"] = {"all": tex("wall-panel"), s: tex(t)}
    data = {"code": "l15-walldeco", "variantgroups": [{"code": "kind", "states": list(deco)}, {"code": "side", "states": SIDES}],
            "texturesByType": tbt, "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
            "blockmaterial": "Stone", "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": STONE,
            "lightHsvByType": {"*-radar-*": [24, 4, 4], "*-view0-*": [10, 3, 4], "*-view1-*": [36, 2, 3], "*-view2-*": [9, 4, 4]},
            "vertexFlagsByType": {"*-radar-*": {"glowLevel": 60}, "*-view0-*": {"glowLevel": 60}, "*-view1-*": {"glowLevel": 50},
                                  "*-view2-*": {"glowLevel": 60}}}
    write_json(os.path.join(BLOCKS, "l15-walldeco.json"), data,
               "Level 15: a white wall block with one face dressed (toward its side): a dead hand scanner, a dead display, the radar, the "
               "ESCAPE panel, views of elsewhere (lit), vent grilles, a wooden door that opens on nothing, dried blood, the room codes")

    glass = {"code": "l15-glass", "variantgroups": [{"code": "kind", "states": ["clear", "cracked"]}],
             "texturesByType": {"*-clear": {"all": tex("glass-clear")}, "*-cracked": {"all": tex("glass-cracked")}},
             "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Glass", "drawtype": "cube",
             "renderpass": "Transparent", "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 4,
             "drops": [{"type": "item", "code": "glassshard", "quantity": {"avg": 2, "var": 1}}], "sounds": GLASS}
    write_json(os.path.join(BLOCKS, "l15-glass.json"), glass, "Level 15: the thick glass of the machine rooms' walls, clear or cracked (never broken through)")

    cube_block("l15-floor", {"ceramic": "floor-ceramic", "worn": "floor-worn", "coating": "floor-coating", "carpet": "floor-carpet",
                             "grating": "floor-grating", "strip": "floor-strip", "stripdead": "floor-stripdead", "blood": "floor-blood",
                             "scorch": "floor-scorch", "track": "floor-track", "dust": "floor-dust"},
               "Level 15: ceramic tiles (worn), a dark non-slip coating, carpet, steel grating, the floor lights along the halls' walls "
               "(strip: glowing to look at, giving no light; stripdead), dried blood, scorch, a gate's tread plate, dust",
               extra={"vertexFlagsByType": {"*-strip": {"glowLevel": 200}},
                      "soundsByType": {"*-carpet": CLOTH, "*-grating": METAL, "*-track": METAL, "*": STONE}})

    ceil = {"code": "l15-ceiling", "variantgroups": [{"code": "kind", "states": ["panel", "on", "lit", "flicker", "off", "service", "vent"]}],
            "texturesByType": {"*-panel": {"all": tex("ceiling-panel")}, "*-on": {"all": tex("ceiling-panel"), "down": tex("ceiling-led")},
                               "*-lit": {"all": tex("ceiling-panel"), "down": tex("ceiling-led")},
                               "*-flicker": {"all": tex("ceiling-panel"), "down": tex("ceiling-led")},
                               "*-off": {"all": tex("ceiling-panel"), "down": tex("ceiling-off")},
                               "*-service": {"all": tex("ceiling-service")}, "*-vent": {"all": tex("ceiling-panel"), "down": tex("ceiling-vent")}},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube", "resistance": 2,
            # The cool white of the halls: one panel in six gives light; the rest only look lit, so lighting stays cheap
            "lightHsvByType": {"*-on": [34, 1, 18]},
            "lightAbsorptionByType": {"*-on": 0, "*-lit": 0, "*-flicker": 0, "*": 99},
            "vertexFlagsByType": {"*-on": {"glowLevel": 200}, "*-lit": {"glowLevel": 200}, "*-flicker": {"glowLevel": 200}},
            "entityClassByType": {"*-flicker": "BackroomsFlicker"},
            "attributesByType": {"*-flicker": {"offBlock": "backrooms:l15-ceiling-off"}},
            "dropsByType": {"*-off": [{"type": "item", "code": "glassshard", "quantity": {"avg": 1, "var": 0.5}},
                                      {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0}}],
                            "*": []},
            "soundsByType": {"*-on": dict(GLASS, ambient="backrooms:ambient/hum", ambientBlockCount=140),
                             "*-lit": dict(GLASS, ambient="backrooms:ambient/hum", ambientBlockCount=140), "*": STONE}}
    write_json(os.path.join(BLOCKS, "l15-ceiling.json"), ceil,
               "Level 15: a white ceiling panel; an LED panel (on gives light; lit only looks it; flicker fails now and then; off); the service "
               "passages' concrete; an air handler's grille")

    # The steel rib and the odd beam
    rib, odd = rib_shape(), oddbeam_shape()
    rb = (0, 0.56, 0.25, 1, 1, 0.75)
    json_block("l15-rib", [{"code": "kind", "states": ["we", "ns"]}],
               {"*-we": {"base": rib}, "*-ns": {"base": rib, "rotateY": 90}},
               "Level 15: a white steel I-beam across the top of a hall, along x (we) or z (ns)",
               {"collisionboxByType": {"*-we": cuboid(rb), "*-ns": cuboid(rb, 90)}, "selectionboxByType": {"*-we": cuboid(rb), "*-ns": cuboid(rb, 90)}},
               inventory="l15-rib-we", extra={"resistance": 8})
    ob = (0, 0.4, 0, 1, 1, 1)
    json_block("l15-oddbeam", [{"code": "kind", "states": ["we", "ns"]}],
               {"*-we": {"base": odd}, "*-ns": {"base": odd, "rotateY": 90}},
               "Level 15: a steel beam set in at an angle nobody would build (we, ns)",
               {"collisionbox": cuboid(ob), "selectionbox": cuboid(ob)}, inventory="l15-oddbeam-we", extra={"resistance": 8})

    cube_block("l15-gate", {"shutter": "gate"}, "Level 15: a security gate's shutter, rolled up into the lintel over a machine room's door",
               material="Metal", sounds=METAL, extra={"resistance": 10})

    machine = {}
    for k in ("panel", "vent", "screen", "screenlit", "lights", "lightslit", "hatch", "warning", "furnace", "press"):
        machine[k] = {"all": "machine-" + k, "up": "machine-top", "down": "machine-top"}
    for k in ("burnt", "burntvent"):
        machine[k] = {"all": "machine-" + k, "up": "machine-burnttop", "down": "machine-burnttop"}
    cube_block("l15-machine", machine,
               "Level 15: machine casing, stacked into machines from cabinets to monoliths: panel, vent, screen and lamp bank (dead or lit; "
               "the lit ones hum), hatch, warning band, burnt, burnt vent, an incinerator's mouth, a press",
               material="Metal", sounds=METAL,
               extra={"resistance": 4,
                      "lightHsvByType": {"*-screenlit": [23, 4, 4], "*-lightslit": [14, 3, 4]},
                      "vertexFlagsByType": {"*-screenlit": {"glowLevel": 120}, "*-lightslit": {"glowLevel": 120}},
                      "soundsByType": {"*-lightslit": dict(METAL, ambient="backrooms:ambient/15/machine", ambientBlockCount=8),
                                       "*-press": dict(METAL, ambient="backrooms:ambient/15/machine", ambientBlockCount=4), "*": METAL},
                      "dropsByType": {"*-burnt": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.4, "var": 0.4}}],
                                      "*-burntvent": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.4, "var": 0.4}}],
                                      "*-furnace": [],
                                      "*": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.8, "var": 0.6}},
                                            {"type": "item", "code": "game:metalbit-copper", "quantity": {"avg": 0.4, "var": 0.4}},
                                            {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.12, "var": 0}}]}})

    full = (0.03, 0, 0.03, 0.97, 1, 0.97)
    shapes, glowing = {}, {}
    for st in ("dead", "denied", "radar"):
        base = console_shape(st)
        for s in SIDES:
            shapes[f"l15-console-{st}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-console", [{"code": "state", "states": ["dead", "denied", "radar"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: a white console, its screen to the side: dead, ACCESS DENIED (lit red), the radar (lit green)",
               {"collisionbox": cuboid(full), "selectionbox": cuboid(full)},
               extra={"lightHsvByType": {"*-denied-*": [0, 5, 4], "*-radar-*": [23, 5, 4]},
                      "drops": [{"type": "item", "code": "scrapwire", "quantity": {"avg": 1, "var": 0.5}},
                                {"type": "item", "code": "glassshard", "quantity": {"avg": 0.5, "var": 0.5}},
                                {"type": "item", "code": "game:metalbit-copper", "quantity": {"avg": 0.3, "var": 0.3}}]},
               inventory="l15-console-radar-north")

    shapes = {}
    for k in ("plain", "sink", "equipment", "glassware"):
        base = bench_shape(k)
        for s in SIDES:
            shapes[f"l15-labbench-{k}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l15-labbench", [{"code": "kind", "states": ["plain", "sink", "equipment", "glassware"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: a lab bench, a black top on white cupboards, its front to the side: plain, a sink, an instrument, glassware",
               {"collisionbox": cuboid((0, 0, 0.06, 1, 0.91, 1)), "selectionbox": cuboid((0, 0, 0.06, 1, 0.91, 1))},
               extra={"dropsByType": {"*-glassware-*": [{"type": "item", "code": "glassshard", "quantity": {"avg": 2, "var": 1}}],
                                      "*": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0.3}},
                                            {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0.3}}]}},
               inventory="l15-labbench-glassware-north")

    shapes = {}
    for part in ("lower", "upper"):
        for st in ("closed", "ajar"):
            base = locker_shape(part, st)
            for s in SIDES:
                shapes[f"l15-locker-{part}-{st}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    closed = [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.6, "var": 0.4}},
              {"type": "item", "code": "game:metalnailsandstrips-iron", "quantity": {"avg": 0.4, "var": 0.4}},
              {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.4, "var": 0.4}},
              {"type": "item", "code": "game:flaxtwine", "quantity": {"avg": 0.3, "var": 0.3}},
              {"type": "item", "code": "almondwater", "quantity": {"avg": 0.1, "var": 0}},
              {"type": "item", "code": "crackers", "quantity": {"avg": 0.15, "var": 0}},
              {"type": "item", "code": "game:candle", "quantity": {"avg": 0.06, "var": 0}},
              {"type": "item", "code": "wanderernote-cache", "quantity": {"avg": 0.03, "var": 0}}]
    ajar = [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.5, "var": 0.4}},
            {"type": "item", "code": "game:metalnailsandstrips-iron", "quantity": {"avg": 0.2, "var": 0.2}}]
    lb = (0.03, 0, 0.1, 0.97, 1, 0.97)
    json_block("l15-locker", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": ["closed", "ajar"]},
                              {"code": "side", "states": SIDES}], shapes,
               "Level 15: a pair of steel lockers, two blocks high, their doors to the side: shut (something may be left inside the lower "
               "half) or ajar (gone through)",
               {"collisionbox": cuboid(lb), "selectionbox": cuboid(lb)},
               extra={"dropsByType": {"*-lower-closed-*": closed, "*-lower-ajar-*": ajar, "*": []}}, inventory="l15-locker-lower-closed-north")

    shapes = {}
    for pose in ("sitting", "head", "feet"):
        for sp in (False, True):
            base = corpse_shape(pose, sp)
            for s in SIDES:
                shapes[f"l15-corpse-{pose}-{'spear' if sp else 'plain'}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    bones = {"type": "item", "code": "game:bone", "quantity": {"avg": 1.5, "var": 0.5}}
    cloth = {"type": "item", "code": "game:flaxtwine", "quantity": {"avg": 0.6, "var": 0.4}}
    json_block("l15-corpse", [{"code": "pose", "states": ["sitting", "head", "feet"]}, {"code": "gear", "states": ["plain", "spear"]},
                              {"code": "side", "states": SIDES}], shapes,
               "Level 15: the dead in lab coats, months gone: sitting against a wall (facing its side), or lying (head, feet; from the head "
               "toward its side), with a makeshift spear (pipe and glass) or without",
               {"collisionbox": cuboid((0.1, 0, 0.1, 0.9, 0.3, 0.9)), "selectionbox": cuboid((0.1, 0, 0.1, 0.9, 0.5, 0.9))},
               sounds=CLOTH, material="Cloth",
               extra={"dropsByType": {"*-spear-*": [bones, cloth, {"type": "item", "code": "glassspear", "quantity": {"avg": 1, "var": 0}}],
                                      "*-head-*": [bones, cloth], "*-sitting-*": [bones, cloth], "*": [bones]}, "resistance": 1},
               inventory="l15-corpse-sitting-spear-north")

    rods = rods_shape()
    json_block("l15-rods", [{"code": "side", "states": SIDES}], sided(rods),
               "Level 15: a heap of steel rods off the press, on two chocks, lying along the side",
               {"collisionbox": cuboid((0, 0, 0, 1, 0.47, 1)), "selectionbox": cuboid((0, 0, 0, 1, 0.47, 1))},
               extra={"drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 1, "var": 0.5}},
                                {"type": "item", "code": "game:metalnailsandstrips-iron", "quantity": {"avg": 1, "var": 0.5}}]},
               inventory="l15-rods-north")

    stage = stage_shape()
    data = {"code": "l15-stage", "shape": {"base": stage}, "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Wood", "drawtype": "json", "sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True},
            "lightAbsorption": 0, "resistance": 3, "drops": [], "sounds": WOOD,
            "collisionbox": cuboid((0, 0, 0, 1, 0.5, 1)), "selectionbox": cuboid((0, 0, 0, 1, 0.5, 1))}
    write_json(os.path.join(BLOCKS, "l15-stage.json"), data, "Level 15: the lecture hall's stage, half a block high")

    shapes = {}
    for part in ("lower", "upper"):
        base = stardoor_shape(part)
        for s in SIDES:
            shapes[f"l15-stardoor-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    sb = (0, 0, 0.38, 1, 1, 0.62)
    json_block("l15-stardoor", [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 15: the star door: a steel doorframe standing alone, a night sky in it and a small blue star (it leads nowhere you can go)",
               {"collisionboxByType": {"*-north": cuboid(sb), "*-south": cuboid(sb), "*": cuboid(sb, 90)},
                "selectionboxByType": {"*-north": cuboid(sb), "*-south": cuboid(sb), "*": cuboid(sb, 90)}},
               extra={"lightHsvByType": {"*-upper-*": [40, 6, 8], "*-lower-*": [40, 5, 5]}, "resistance": 100,
                      "vertexFlags": {"glowLevel": 80}}, inventory="l15-stardoor-lower-north")


# ======================================================================== Sounds

def periodic_noise(rng, n, shape_fn):
    f = np.fft.rfftfreq(n, 1 / RATE)
    spectrum = (rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))) * shape_fn(f)
    spectrum[0] = 0
    sig = np.fft.irfft(spectrum, n=n)
    return sig / np.max(np.abs(sig))


def write(name, sig, peak=0.5):
    sig = peak * sig / np.max(np.abs(sig))
    path = os.path.join(SOUNDS, name + ".ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def sounds():
    rng = np.random.default_rng(15600)
    # The halls: a constant drone of machinery everywhere (both wikis), engines far off, a slow beat between them; 12 s loop
    n = int(12.0 * RATE)
    t = np.arange(n) / RATE
    air = periodic_noise(rng, n, lambda f: 1 / np.maximum(f, 25) ** 1.1 * np.exp(-(f / 1400) ** 2))
    hum = sum(a * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6)) for fr, a in ((60, 0.25), (120, 0.16), (180, 0.07), (240, 0.04), (360, 0.02)))
    engine = 0.22 * np.sin(2 * np.pi * 31.5 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * t / 3))  # the engines' thrum, in whole cycles
    beat = 0.06 * np.sin(2 * np.pi * 61.25 * t)  # a second machine a little off the mains: the slow beat
    write("hum", 0.6 * air + hum + engine + beat, 0.45)
    # A running machine: a whir and a whine over a low hum; 6 s
    n = int(6.0 * RATE)
    t = np.arange(n) / RATE
    whir = periodic_noise(rng, n, lambda f: np.exp(-((f - 700) / 500) ** 2) + 0.4 / np.maximum(f, 40))
    sig = 0.5 * whir * (0.85 + 0.15 * np.sin(2 * np.pi * t * 2)) + 0.2 * np.sin(2 * np.pi * 120 * t) + 0.04 * np.sin(2 * np.pi * 2400.5 * t)
    write("machine", sig, 0.5)
    # The air handlers in the service passages: a broad whoosh, the duct's resonance; 8 s
    n = int(8.0 * RATE)
    t = np.arange(n) / RATE
    whoosh = periodic_noise(rng, n, lambda f: np.exp(-((f - 450) / 900) ** 2) + 0.2 * np.exp(-((f - 140) / 30) ** 2))
    write("airhandler", whoosh * (0.8 + 0.2 * np.sin(2 * np.pi * t / 4)), 0.5)
    # The ticking in the dark (Fandom: "a faint, persistent ticking sound that resembles a human heartbeat"): a double
    # tick every 1.2 s (lub-dub), 6 beats; slowed in the game by lowering its pitch the longer one stays
    n = int(7.2 * RATE)
    sig = np.zeros(n)
    tick_len = int(0.03 * RATE)
    tt = np.arange(tick_len) / RATE
    tick = np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt / 0.006) + 0.6 * np.sin(2 * np.pi * 420 * tt) * np.exp(-tt / 0.012)
    for k in range(6):
        for off, amp in ((0.0, 1.0), (0.24, 0.65)):
            i = int((k * 1.2 + off) * RATE)
            sig[i:i + tick_len] += amp * tick
    room = periodic_noise(rng, n, lambda f: 0.002 / np.maximum(f, 50))
    write("heartbeat", sig + room, 0.35)
    # Far-off beeps, each a little different
    for k, (fr, count, gap) in enumerate(((1250, 2, 0.32), (880, 3, 0.18), (1650, 1, 0.3)), 1):
        n = int((count * gap + 0.4) * RATE)
        sig = np.zeros(n)
        bl = int(0.12 * RATE)
        bt = np.arange(bl) / RATE
        beep = np.sin(2 * np.pi * fr * bt) * np.minimum(1, np.minimum(bt / 0.005, (0.12 - bt) / 0.01))
        for j in range(count):
            i = int(j * gap * RATE)
            sig[i:i + bl] += beep
        # A long, soft echo down the halls
        echo = np.zeros(n)
        d = int(0.09 * RATE)
        for e in range(1, 5):
            echo[e * d:] += sig[:n - e * d] * (0.45 ** e)
        write(f"beep{k}", sig + echo, 0.4)


def main():
    wall_textures()
    deco_textures()
    floor_textures()
    ceiling_textures()
    steel_textures()
    machine_textures()
    prop_textures()
    blocktypes()
    sounds()
    print("Level 15: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
