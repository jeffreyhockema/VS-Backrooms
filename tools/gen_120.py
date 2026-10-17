"""Level 120, "Server Room" (experimental): its five blocks, their textures and shapes, and its one sound.

    l120-wall       dirty yellow wallpaper over rotting boards: base (yellowed, faint stripes), stained (brown water
                    streaks), rot (the paper torn away, the boards black with rot); cubes
    l120-floor      raised-floor panels, four to a block: clean, dirty, vent (perforated, the cold aisles), hole (one
                    panel lifted, cables under it); cubes
    l120-rack       a server rack, two blocks high (lower and upper), its front to the side: a dark steel cabinet of 1U
                    units with vent slits, posts either side, a column of status LEDs; off, leda (green), ledb (amber),
                    both (green and blue), gutted (the units ripped out, wires hanging); a lit upper block gives a
                    little light; JSON shape
    l120-tray       an overhead cable tray (a yellow-grey mesh channel with a black cable bundle) hung on two rods,
                    along x (we) or z (ns), and the rods alone (rodwe, rodns) for a great hall's lower trays; JSON shape
    l120-terminal   a CRT terminal on a grey desk, its screen to the side: dead or lit (cyan text, a little light); JSON shape
    sounds/ambient/120/serverhum.ogg   the fans: a seamless drone of brown noise, the mains hum and a faint whine

Textures are 32 px a block (block/120/), shapes 16 units (block/120/); every shape names its texture keys one by one
and its blocktype names no textures, so nothing overrides them (a blocktype's `textures: { all }` would override every
key of a shape). Run from the repo root:  python tools/gen_120.py
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

from modelkit import box
from oggutil import write_ogg
from texlib import _periodic_noise
from gen_entity_sounds import RATE

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "120")
SHAPES = os.path.join(ASSETS, "shapes", "block", "120")
BLOCKS = os.path.join(ASSETS, "blocktypes", "120")
S = 32
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
RACK_STATES = ["off", "leda", "ledb", "both", "gutted"]

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}

PAPER = (186, 168, 104)
PANEL = (190, 192, 188)
STEEL = (40, 43, 48)
UNIT = (52, 55, 61)


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


# ======================================================================== Textures

def clamp(v):
    return max(0, min(255, int(round(v))))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def canvas(colour):
    return Image.new("RGBA", (S, S), tuple(colour) + (255,))


def rect(img, x0, y0, x1, y1, colour):
    px = img.load()
    for y in range(max(0, y0), min(S, y1 + 1)):
        for x in range(max(0, x0), min(S, x1 + 1)):
            px[x, y] = tuple(colour) + (255,)


def grain(img, seed, amount=5, mottle=0.0):
    """Fine grain over everything and, with mottle, a soft tileable blotchiness (texlib's periodic noise)."""
    rng = random.Random(seed)
    px = img.load()
    field = _periodic_noise(seed, 3) if mottle else None
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount) + (mottle * field[y][x] if field else 0)
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), a)
    return img


def save(img, name):
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def wall_textures():
    # Yellowed paper with faint vertical stripes and a small diamond print, dirt in blotches
    base = canvas(PAPER)
    px = base.load()
    for y in range(S):
        for x in range(S):
            k = 1.0
            if x % 8 in (0, 1):
                k *= 0.93
            if (x % 8 == 4) and (y % 8 in (2, 6)) or (x % 8 in (3, 5)) and (y % 8 == 4):
                k *= 0.88
            px[x, y] = shade(px[x, y][:3], k) + (255,)
    grain(base, 12001, 4, 14)
    save(base, "wall-base")
    # Stained: brown streaks running down the whole height (so they carry on from block to block)
    stained = base.copy()
    px = stained.load()
    rng = random.Random(12002)
    for _ in range(4):
        x0, w, depth = rng.randint(0, 31), rng.randint(2, 6), rng.uniform(0.62, 0.82)
        for y in range(S):
            wob = int(round(1.2 * math.sin(2 * math.pi * y / S + x0)))
            for dx in range(w):
                x = (x0 + dx + wob) % S
                edge = 1 - abs(dx - (w - 1) / 2) / (w / 2 + 0.5)
                r, g, b, a = px[x, y]
                k = 1 - (1 - depth) * edge
                px[x, y] = (clamp(r * k * 0.97), clamp(g * k * 0.9), clamp(b * k * 0.8), 255)
    save(grain(stained, 12003, 3), "wall-stained")
    # Rot: the boards behind, black-brown and soft, the paper hanging in a ragged edge
    rot = base.copy()
    px = rot.load()
    rng = random.Random(12004)
    left = [int(6 + 4 * math.sin(2 * math.pi * y / S) + rng.uniform(-1.5, 1.5)) for y in range(S)]
    right = [int(26 + 3 * math.sin(2 * math.pi * 2 * y / S + 1) + rng.uniform(-1.5, 1.5)) for y in range(S)]
    for y in range(S):
        for x in range(left[y], right[y]):
            plank = (x // 8) % 2
            c = (58, 42, 30) if plank else (70, 50, 34)
            if x % 8 == 0:
                c = (30, 22, 16)
            k = 0.85 + 0.25 * math.sin(y * 0.7 + x * 0.3) * 0.5
            px[x, y] = shade(c, k) + (255,)
        for x in (left[y] - 1, right[y]):
            if 0 <= x < S:
                px[x, y] = shade(PAPER, 1.08) + (255,)
    save(grain(rot, 12005, 4, 8), "wall-rot")


def floor_textures():
    def panels(colour, seed):
        img = canvas(colour)
        px = img.load()
        for y in range(S):
            for x in range(S):
                c = px[x, y][:3]
                if x % 16 == 0 or y % 16 == 0:
                    c = shade(colour, 0.55)
                elif x % 16 == 1 or y % 16 == 1:
                    c = shade(colour, 1.08)
                elif x % 16 == 15 or y % 16 == 15:
                    c = shade(colour, 0.85)
                px[x, y] = c + (255,)
        return grain(img, seed, 3, 5)

    save(panels(PANEL, 12010), "floor-clean")
    dirty = panels(shade(PANEL, 0.86), 12011)
    px = dirty.load()
    rng = random.Random(12012)
    for _ in range(26):
        x, y, n = rng.randint(0, 31), rng.randint(0, 31), rng.randint(2, 6)
        for k in range(n):
            xx, yy = (x + k) % S, (y + (k // 2)) % S
            px[xx, yy] = shade(px[xx, yy][:3], 0.72) + (255,)
    save(grain(dirty, 12013, 3, 10), "floor-dirty")
    vent = panels(shade(PANEL, 0.95), 12014)
    px = vent.load()
    for y in range(S):
        for x in range(S):
            if 3 <= x % 16 <= 13 and 3 <= y % 16 <= 13 and x % 2 == 1 and y % 2 == 1:
                px[x, y] = (34, 36, 38, 255)
    save(vent, "floor-vent")
    hole = panels(shade(PANEL, 0.88), 12015)
    px = hole.load()
    rng = random.Random(12016)
    for y in range(1, 16):
        for x in range(1, 16):
            px[x, y] = (14, 15, 17, 255)
    for colour in ((40, 60, 120), (150, 150, 150), (180, 140, 40), (30, 30, 30), (130, 40, 40)):
        y0 = rng.randint(3, 12)
        for x in range(1, 16):
            y = y0 + int(round(1.5 * math.sin(x * 0.5 + y0)))
            if 1 <= y < 16:
                px[x, y] = colour + (255,)
                if y + 1 < 16:
                    px[x, y + 1] = shade(colour, 0.6) + (255,)
    save(hole, "floor-hole")


def rack_textures():
    rng = random.Random(12020)
    # The front: eight 1U units, each a faceplate with a handle, vent slits and a little label; some blank panels
    front = canvas(STEEL)
    px = front.load()
    for u in range(8):
        y0 = u * 4
        blank = rng.random() < 0.2
        tone = rng.uniform(0.9, 1.1)
        rect(front, 0, y0, 31, y0 + 3, shade(UNIT, tone))
        rect(front, 0, y0, 31, y0, shade(UNIT, tone * 1.25))
        rect(front, 0, y0 + 3, 31, y0 + 3, (18, 19, 22))
        if blank:
            continue
        rect(front, 1, y0 + 1, 2, y0 + 2, (150, 152, 156))  # the pull handle
        rect(front, 29, y0 + 1, 30, y0 + 2, (150, 152, 156))
        for x in range(5, 20, 2):
            rect(front, x, y0 + 1, x, y0 + 2, (16, 17, 20))  # vent slits
        if rng.random() < 0.6:
            rect(front, 21, y0 + 1, 24, y0 + 1, (200, 198, 186))  # a label
        rect(front, 22, y0 + 2, 23, y0 + 2, (24, 25, 28))  # the drive's slot
    save(grain(front, 12021, 3), "rack-front")
    # Gutted: most units torn out, black voids, a few faceplates left hanging, wires dropping out
    gutted = front.copy()
    px = gutted.load()
    for u in range(8):
        if rng.random() < 0.7:
            rect(gutted, 2, u * 4, 29, u * 4 + 3, (9, 9, 11))
    for colour in ((60, 90, 170), (170, 60, 50), (190, 170, 60), (120, 120, 120)):
        x = rng.randint(4, 27)
        for y in range(rng.randint(0, 10), S):
            px[x, y] = colour + (255,)
            if rng.random() < 0.2:
                x = max(3, min(28, x + rng.choice((-1, 1))))
    save(grain(gutted, 12022, 2), "rack-gutted")
    # The back: a tangle of patch cables and power leads, two fan grilles
    back = canvas((30, 32, 36))
    px = back.load()
    for cx, cy in ((9, 9), (23, 23)):
        for y in range(S):
            for x in range(S):
                d = math.hypot(x - cx, y - cy)
                if d < 6:
                    px[x, y] = ((22, 23, 26) if int(d) % 2 else (64, 66, 70)) + (255,)
    for colour in ((40, 70, 150), (200, 200, 200), (190, 160, 40), (30, 30, 30), (40, 140, 70), (150, 40, 40)):
        for _ in range(2):
            x = rng.randint(0, 31)
            for y in range(S):
                px[x % S, y] = colour + (255,)
                if rng.random() < 0.35:
                    x += rng.choice((-1, 1))
    save(grain(back, 12023, 3), "rack-back")
    side = canvas((48, 51, 57))
    for x in (0, 31):
        rect(side, x, 0, x, 31, (30, 32, 36))
    for y in (2, 29):
        for x in (3, 28):
            rect(side, x, y, x, y, (90, 94, 100))
    save(grain(side, 12024, 3, 4), "rack-side")
    top = canvas((44, 47, 52))
    px = top.load()
    for y in range(4, 28, 2):
        for x in range(4, 28, 2):
            px[x, y] = (20, 21, 24, 255)
    save(grain(top, 12025, 2), "rack-top")
    post = canvas((26, 27, 30))
    px = post.load()
    for y in range(1, S, 4):
        px[15, y] = px[16, y] = (90, 92, 96, 255)  # the rack's screw holes
    save(grain(post, 12026, 2), "rack-post")
    for name, colour in (("led-green", (90, 255, 120)), ("led-amber", (255, 176, 60)), ("led-blue", (90, 170, 255)), ("led-dead", (40, 44, 40))):
        img = canvas(colour)
        rect(img, 12, 12, 19, 19, shade(colour, 1.15) if name != "led-dead" else colour)
        save(img, name)
    save(grain(canvas((150, 150, 150)), 12027, 6), "wire-grey")
    save(grain(canvas((60, 90, 170)), 12028, 6), "wire-blue")


def prop_textures():
    rng = random.Random(12030)
    # The tray: yellow-grey wire mesh
    mesh = canvas((150, 146, 116))
    px = mesh.load()
    for y in range(S):
        for x in range(S):
            if x % 4 != 0 and y % 4 != 0:
                px[x, y] = (54, 54, 50, 255)
    save(mesh, "tray-mesh")
    cable = canvas((24, 24, 26))
    px = cable.load()
    for y in range(S):
        for x in range(S):
            if (y + int(2 * math.sin(x * 0.4))) % 5 == 0:
                px[x, y] = (46, 46, 50, 255)
    for _ in range(3):
        y = rng.randint(0, 31)
        rect(cable, 0, y, 31, y, (40, 70, 150))
    save(grain(cable, 12031, 3), "tray-cable")
    save(grain(canvas((110, 112, 114)), 12032, 5), "tray-rod")
    # The terminal: a beige CRT case, its screen dead (grey-green glass) or lit (cyan text on blue-black), a grey desk
    save(grain(canvas((176, 168, 146)), 12033, 4, 6), "crt-case")
    dead = canvas((34, 42, 38))
    px = dead.load()
    for y in range(S):
        for x in range(S):
            d = math.hypot((x - 15.5) / 16, (y - 15.5) / 16)
            px[x, y] = shade((34, 42, 38), 1.15 - 0.35 * d) + (255,)
    save(grain(dead, 12034, 2), "screen-dead")
    lit = canvas((6, 22, 30))
    px = lit.load()
    for row in range(3, 29, 3):
        n = rng.randint(6, 26)
        for x in range(3, 3 + n):
            if rng.random() < 0.8:
                px[x, row] = (90, 230, 230, 255)
    for y in range(0, S, 2):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * 0.8), clamp(g * 0.8), clamp(b * 0.8), 255)
    save(lit, "screen-lit")
    keys = canvas((196, 190, 172))
    for y in range(2, 30, 6):
        for x in range(2, 30, 5):
            rect(keys, x, y, x + 3, y + 4, (150, 146, 132))
    save(grain(keys, 12035, 3), "keyboard")
    save(grain(canvas((126, 128, 130)), 12036, 4, 5), "desk-top")
    save(grain(canvas((80, 82, 86)), 12037, 4), "desk-frame")


# ======================================================================== Shapes

def shape(name, elements):
    keys = sorted({face["texture"][1:] for e in elements for face in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: "backrooms:block/120/" + k for k in keys}, "elements": elements}
    write_json(os.path.join(SHAPES, name + ".json"), data)
    return "backrooms:block/120/" + name


def rack_shape(part, state):
    """A rack block with its front to the north (low z): the cabinet, a post either side of the front, a column of LEDs."""
    gutted = state == "gutted"
    els = [
        box("Body", (0.5, 0, 1), (15.5, 16, 15.5), {"front": "rack-gutted" if gutted else "rack-front", "back": "rack-back",
                                                   "side": "rack-side", "top": "rack-top", "bottom": "rack-top"}),
        box("PostL", (0.5, 0, 0.5), (1.5, 16, 1), "rack-post", faces=("north", "east", "west")),
        box("PostR", (14.5, 0, 0.5), (15.5, 16, 1), "rack-post", faces=("north", "east", "west")),
    ]
    if gutted:
        # Wires hanging out of the empty bays
        els += [box("WireA", (5, 1, 0.5), (5.5, 9, 1), "wire-blue", faces=("north", "east", "west")),
                box("WireB", (10, 3, 0.5), (10.5, 12, 1), "wire-grey", faces=("north", "east", "west"))]
        return shape(f"l120-rack-{part}-{state}", els)
    rng = random.Random(f"{part}-{state}")
    a_on = state in ("leda", "both")
    b_on = state in ("ledb", "both")
    for u in range(8):
        y = u * 2 + 0.75
        lit_a = a_on and rng.random() < 0.8
        lit_b = b_on and rng.random() < 0.7
        colour_b = "led-blue" if state == "both" else "led-amber"
        els.append(box(f"LedA{u}", (12.5, y, 0.5), (13.5, y + 0.5, 1), "led-green" if lit_a else "led-dead",
                       faces=("north",), glow=255 if lit_a else 0))
        els.append(box(f"LedB{u}", (11, y, 0.5), (12, y + 0.5, 1), colour_b if lit_b else "led-dead",
                       faces=("north",), glow=255 if lit_b else 0))
    return shape(f"l120-rack-{part}-{state}", els)


def tray_shape(rods_only):
    """A tray along x hung from the top of its block on two rods (or the rods alone, for a tray hung from higher up)."""
    els = []
    for i, x in enumerate((2, 13.5)):
        for j, z in enumerate((5, 10.5)):
            els.append(box(f"Rod{i}{j}", (x, 0 if rods_only else 14, z), (x + 0.5, 16, z + 0.5), "tray-rod",
                           faces=("north", "east", "south", "west")))
    if not rods_only:
        els += [
            box("Floor", (0, 12, 5), (16, 12.5, 11), "tray-mesh", faces=("up", "down")),
            box("SideN", (0, 12, 5), (16, 14, 5.5), "tray-mesh", faces=("north", "south", "up")),
            box("SideS", (0, 12, 10.5), (16, 14, 11), "tray-mesh", faces=("north", "south", "up")),
            box("Cables", (0, 12.5, 5.5), (16, 13.6, 10.5), "tray-cable", faces=("up",)),
            box("Bar0", (1.5, 11.5, 4.5), (2.5, 12, 11.5), "tray-rod", faces=("east", "west", "down", "north", "south")),
            box("Bar1", (13, 11.5, 4.5), (14, 12, 11.5), "tray-rod", faces=("east", "west", "down", "north", "south")),
        ]
    return shape("l120-tray-rods" if rods_only else "l120-tray", els)


def terminal_shape(lit):
    """A CRT terminal on a desk, its screen and keyboard to the north."""
    els = [
        box("Top", (0.5, 10.5, 0.5), (15.5, 11.5, 15.5), {"top": "desk-top", "side": "desk-frame", "bottom": "desk-frame"}),
        box("SideL", (1, 0, 1.5), (2, 10.5, 14.5), "desk-frame", faces=("north", "east", "south", "west")),
        box("SideR", (14, 0, 1.5), (15, 10.5, 14.5), "desk-frame", faces=("north", "east", "south", "west")),
        box("Modesty", (2, 3, 13.5), (14, 10.5, 14.5), "desk-frame", faces=("north", "south")),
        box("Case", (3, 11.5, 3.5), (13, 16, 13), "crt-case", faces=("east", "south", "west", "up")),
        box("Bezel", (3, 11.5, 3), (13, 16, 3.5), "crt-case", faces=("north", "east", "west", "up")),
        box("Screen", (4, 12.5, 2.6), (12, 15.5, 3), "screen-lit" if lit else "screen-dead", faces=("north",), glow=200 if lit else 0),
        box("Keyboard", (4, 11.5, 0.8), (12, 12, 2.6), "keyboard", faces=("up", "north", "east", "west")),
    ]
    return shape("l120-terminal-lit" if lit else "l120-terminal-dead", els)


# ======================================================================== Block types

def cuboid(b, angle=0):
    c = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if angle:
        c["rotateY"] = angle
    return c


def tex(name):
    return {"base": "block/120/" + name}


def cube_block(code, kinds, comment, material="Stone", sounds=STONE):
    data = {"code": code, "variantgroups": [{"code": "kind", "states": list(kinds)}],
            "texturesByType": {f"*-{k}": {"all": tex(v)} for k, v in kinds.items()},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds}
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def json_block(code, groups, shapes, comment, collision, sounds=METAL, extra=None, inventory=None):
    data = {"code": code, "variantgroups": groups, "shapeByType": shapes,
            "creativeinventory": {"general": [inventory], "backrooms": [inventory]},
            "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 3, "sounds": sounds, "drops": []}
    data.update(collision)
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def blocktypes():
    cube_block("l120-wall", {"base": "wall-base", "stained": "wall-stained", "rot": "wall-rot"},
               "Level 120: dirty yellow wallpaper over rotting boards (base; stained with brown streaks; rot: the paper torn off)",
               material="Wood", sounds=WOOD)
    cube_block("l120-floor", {k: "floor-" + k for k in ("clean", "dirty", "vent", "hole")},
               "Level 120: raised-floor panels, four to a block (clean; dirty; vent: perforated; hole: one panel lifted, the cables under it)",
               sounds=METAL)

    # The rack
    shapes, light = {}, {}
    for part in ("lower", "upper"):
        for state in RACK_STATES:
            base = rack_shape(part, state)
            for s in SIDES:
                shapes[f"l120-rack-{part}-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    light = {"*-upper-leda-*": [21, 6, 5], "*-upper-ledb-*": [7, 6, 4], "*-upper-both-*": [30, 5, 6]}
    full = (0.03, 0, 0.03, 0.97, 1, 0.97)
    json_block("l120-rack", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": RACK_STATES},
                             {"code": "side", "states": SIDES}], shapes,
               "Level 120: a server rack, two blocks high (lower, upper), its front to the side; dark, its LEDs on (bank A green, bank B amber, "
               "both green and blue: the upper block gives a little light), or gutted",
               {"collisionbox": cuboid(full), "selectionbox": cuboid(full)},
               extra={"lightHsvByType": light}, inventory="l120-rack-lower-leda-north")

    # The tray
    tray, rods = tray_shape(False), tray_shape(True)
    shapes = {"*-we": {"base": tray}, "*-ns": {"base": tray, "rotateY": 90},
              "*-rodwe": {"base": rods}, "*-rodns": {"base": rods, "rotateY": 90}}
    tb = (0, 0.7, 0.28, 1, 1, 0.72)
    rb = (0.1, 0, 0.28, 0.9, 1, 0.72)
    json_block("l120-tray", [{"code": "kind", "states": ["we", "ns", "rodwe", "rodns"]}], shapes,
               "Level 120: an overhead cable tray, a mesh channel full of black cable hung on rods, along x (we) or z (ns); or the rods alone",
               {"collisionboxByType": {"*-we": cuboid(tb), "*-ns": cuboid(tb, 90), "*-rodwe": cuboid(rb), "*-rodns": cuboid(rb, 90)},
                "selectionboxByType": {"*-we": cuboid(tb), "*-ns": cuboid(tb, 90), "*-rodwe": cuboid(rb), "*-rodns": cuboid(rb, 90)}},
               inventory="l120-tray-we")

    # The terminal
    shapes = {}
    for state, lit in (("dead", False), ("lit", True)):
        base = terminal_shape(lit)
        for s in SIDES:
            shapes[f"l120-terminal-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    json_block("l120-terminal", [{"code": "state", "states": ["dead", "lit"]}, {"code": "side", "states": SIDES}], shapes,
               "Level 120: a CRT terminal on a grey desk, its screen to the side: dead, or lit (cyan text; a little light)",
               {"collisionbox": cuboid(full), "selectionbox": cuboid(full)},
               extra={"lightHsvByType": {"*-lit-*": [33, 5, 6]}}, inventory="l120-terminal-lit-north")


# ======================================================================== Sound

def serverhum():
    """The fans, a seamless 8 s loop: brown-ish noise for the air, the 100 Hz mains hum and its harmonics, a blade tone
    and a faint high whine, every component whole cycles in the loop (the noise made in the frequency domain)."""
    rng = np.random.default_rng(12040)
    n = int(8.0 * RATE)
    t = np.arange(n) / RATE
    f = np.fft.rfftfreq(n, 1 / RATE)
    spectrum = rng.normal(size=len(f)) + 1j * rng.normal(size=len(f))
    shape_ = 1 / np.maximum(f, 30) ** 0.9 * np.exp(-(f / 2600) ** 2)
    shape_ += 0.004 * np.exp(-((f - 1100) / 500) ** 2)  # the rush of air through the grilles
    spectrum *= shape_
    spectrum[0] = 0
    air = np.fft.irfft(spectrum, n=n)
    air /= np.max(np.abs(air))
    hum = sum(a * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6)) for fr, a in ((100, 0.22), (200, 0.12), (300, 0.06), (400, 0.03)))
    blade = 0.05 * np.sin(2 * np.pi * 147.25 * t) * (1 + 0.3 * np.sin(2 * np.pi * 0.5 * t))
    whine = 0.012 * np.sin(2 * np.pi * 3600 * t + 3 * np.sin(2 * np.pi * 0.25 * t))
    # A slow swell in whole cycles, as fans hunt for speed
    sig = air * (0.85 + 0.15 * np.sin(2 * np.pi * t / 4)) + hum + blade + whine
    sig = 0.5 * sig / np.max(np.abs(sig))
    path = os.path.join(ASSETS, "sounds", "ambient", "120", "serverhum.ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def main():
    wall_textures()
    floor_textures()
    rack_textures()
    prop_textures()
    blocktypes()
    serverhum()
    print("Level 120: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
