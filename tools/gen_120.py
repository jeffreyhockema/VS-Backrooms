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
WHITE = (212, 208, 196)
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
    # Stained: water run down the paper in soft brown streaks, straight down the whole height so they carry on from block
    # to block (no shape of their own to repeat), heavier and lighter by turns
    stained = base.copy()
    px = stained.load()
    rng = random.Random(12002)
    streaks = [(rng.uniform(0, S), rng.uniform(1.2, 3.2), rng.uniform(0.18, 0.34), rng.uniform(0, 2 * math.pi)) for _ in range(5)]
    for y in range(S):
        for x in range(S):
            d = 0.0
            for cx, w, depth, ph in streaks:
                dx = min(abs(x - cx), S - abs(x - cx))
                d += depth * math.exp(-(dx / w) ** 2) * (0.7 + 0.3 * math.sin(2 * math.pi * y / S + ph))
            d = min(d, 0.45)
            r, g, b, a = px[x, y]
            k = 1 - d
            px[x, y] = (clamp(r * k * 0.98), clamp(g * k * 0.93), clamp(b * k * 0.82), 255)
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
    # Two more tears of other shapes, so the same hole is not stamped on wall after wall: a blob of paper gone low
    # down on one side, and the paper peeled away from the top, the boards showing above a ragged hem
    for name, seed, inside in (
            ("wall-rot2", 12007, lambda x, y, n: math.hypot((x - 21) / 10.5, (y - 21) / 9.0) + n * 0.22 < 1),
            ("wall-rot3", 12008, lambda x, y, n: y < 11 + 3.5 * math.sin(x * 0.45 + 1.3) + 2.5 * math.sin(x * 1.3) + n * 2.2)):
        img = base.copy()
        px = img.load()
        rng = random.Random(seed)
        noise = [[rng.uniform(-1, 1) for _ in range(S)] for _ in range(S)]
        mask = [[inside(x, y, (noise[y][x] + noise[y][(x + 1) % S] + noise[(y + 1) % S][x]) / 3) for x in range(S)] for y in range(S)]
        for y in range(S):
            for x in range(S):
                if mask[y][x]:
                    c = (58, 42, 30) if (x // 8) % 2 else (70, 50, 34)
                    if x % 8 == 0:
                        c = (30, 22, 16)
                    px[x, y] = shade(c, 0.85 + 0.12 * math.sin(y * 0.7 + x * 0.3)) + (255,)
                elif any(0 <= x + dx < S and 0 <= y + dy < S and mask[y + dy][x + dx] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    px[x, y] = shade(PAPER, 1.08) + (255,)  # the paper's torn edge, curling up pale
        save(grain(img, seed + 10, 4, 8), name)
    # Soot: the Pitch-Black Hallways' walls, the paper gone near black, its print just there
    soot = canvas((40, 36, 28))
    px = soot.load()
    for y in range(S):
        for x in range(S):
            k = 1.0
            if x % 8 in (0, 1):
                k *= 0.9
            if (x % 8 == 4) and (y % 8 in (2, 6)) or (x % 8 in (3, 5)) and (y % 8 == 4):
                k *= 1.12
            px[x, y] = shade(px[x, y][:3], k) + (255,)
    save(grain(soot, 12006, 3, 10), "wall-soot")


def floor_textures():
    """The lore's "dirty, white floor": off-white vinyl tiles, two to a block, scuffed and grimed; among the racks the
    raised floor's perforated vent panels and now and then a panel lifted out, the cables under it."""
    def tiles(colour, seed, grime):
        img = canvas(colour)
        px = img.load()
        rng = random.Random(seed)
        tone = {(i, j): rng.uniform(0.95, 1.04) for i in range(2) for j in range(2)}
        for y in range(S):
            for x in range(S):
                c = shade(colour, tone[(x // 16, y // 16)])
                if x % 16 == 0 or y % 16 == 0:
                    c = shade(colour, 0.62)  # the grimy seams
                elif x % 16 == 15 or y % 16 == 15:
                    c = shade(colour, 0.86)
                px[x, y] = c + (255,)
        # Scuffs and dark smears, heaviest along the seams
        for _ in range(grime):
            x, y, n = rng.randint(0, 31), rng.randint(0, 31), rng.randint(2, 7)
            k = rng.uniform(0.7, 0.88)
            for i in range(n):
                xx, yy = (x + i) % S, (y + (i // 3)) % S
                r, g, b, a = px[xx, yy]
                px[xx, yy] = (clamp(r * k), clamp(g * k * 0.99), clamp(b * k * 0.95), 255)
        return grain(img, seed + 1, 3, 9)

    save(tiles(WHITE, 12010, 18), "floor-clean")
    dirty = tiles(shade(WHITE, 0.9), 12011, 46)
    px = dirty.load()
    rng = random.Random(12012)
    # A brown water stain spreading over two tiles
    cx, cy = rng.randint(6, 26), rng.randint(6, 26)
    for y in range(S):
        for x in range(S):
            d = math.hypot((x - cx + 16) % 32 - 16, (y - cy + 16) % 32 - 16)
            if d < 9:
                r, g, b, a = px[x, y]
                k = 0.86 + 0.14 * d / 9
                px[x, y] = (clamp(r * k), clamp(g * k * 0.95), clamp(b * k * 0.82), 255)
    save(grain(dirty, 12013, 3, 12), "floor-dirty")
    vent = tiles(shade(WHITE, 0.93), 12014, 14)
    px = vent.load()
    for y in range(S):
        for x in range(S):
            if 3 <= x % 16 <= 13 and 3 <= y % 16 <= 13 and x % 2 == 1 and y % 2 == 1:
                px[x, y] = (30, 31, 33, 255)
    save(vent, "floor-vent")
    hole = tiles(shade(WHITE, 0.88), 12015, 26)
    px = hole.load()
    rng = random.Random(12016)
    for y in range(1, 16):
        for x in range(1, 16):
            px[x, y] = (12, 13, 14, 255)
    for colour in ((40, 60, 120), (150, 150, 150), (180, 140, 40), (30, 30, 30), (130, 40, 40)):
        y0 = rng.randint(3, 12)
        for x in range(1, 16):
            y = y0 + int(round(1.5 * math.sin(x * 0.5 + y0)))
            if 1 <= y < 16:
                px[x, y] = colour + (255,)
                if y + 1 < 16:
                    px[x, y + 1] = shade(colour, 0.6) + (255,)
    save(hole, "floor-hole")


def ceiling_textures():
    """Office ceiling tiles (the lore's "regular office ceiling tiles"): fissured off-white, a grey T-bar grid; one
    water-stained; one fallen through, black above; and a fitting smashed in its housing, glass stubs in the sockets."""
    tile = canvas((198, 194, 182))
    px = tile.load()
    rng = random.Random(12050)
    for y in range(S):
        for x in range(S):
            if x % 16 == 0 or y % 16 == 0:
                px[x, y] = (128, 128, 124, 255)
            elif rng.random() < 0.08:
                px[x, y] = shade((198, 194, 182), 0.82) + (255,)
    grain(tile, 12051, 3, 6)
    save(tile, "ceiling-tile")
    stained = tile.copy()
    px = stained.load()
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 20, y - 12)
            if d < 10:
                r, g, b, a = px[x, y]
                ring = 0.7 if 8.2 < d < 9.4 else 0.86
                px[x, y] = (clamp(r * ring), clamp(g * ring * 0.93), clamp(b * ring * 0.75), 255)
    save(stained, "ceiling-stained")
    broken = tile.copy()
    px = broken.load()
    for y in range(1, 16):
        edge = 3 + int(2.5 * math.sin(y * 0.9))
        for x in range(1 + edge, 16):
            px[x, y] = (8, 8, 9, 255)
    save(broken, "ceiling-broken")
    smashed = canvas((150, 150, 146))
    px = smashed.load()
    for y in range(S):
        for x in range(S):
            if 3 <= x <= 28 and 2 <= y <= 29:
                px[x, y] = (34, 34, 36, 255)  # the empty housing
    for x0 in (8, 22):
        for y in range(2, 30):
            px[x0, y] = px[x0 + 1, y] = (70, 70, 72, 255)  # the reflectors' ridges
        for y in list(range(2, 5 + rng.randint(0, 3))) + list(range(26 - rng.randint(0, 3), 30)):
            px[x0 - 1, y] = px[x0, y] = (214, 220, 214, 255)  # stubs of tube left in the sockets
    for _ in range(26):
        x, y = rng.randint(4, 27), rng.randint(3, 28)
        px[x, y] = (196, 204, 200, 255)  # shards
    save(grain(smashed, 12052, 3), "ceiling-smashed")


def void_textures():
    """The White Voids: white with no feature at all, the faintest grain so it is not a flat colour; black for the solid
    round them; a black door."""
    for name, base, amount in (("void-white", (246, 246, 244), 1.5), ("void-floor", (238, 238, 236), 2)):
        save(grain(canvas(base), 12060 + len(name), amount), name)
    save(canvas((4, 4, 5)), "void-black")
    door = canvas((14, 14, 16))
    px = door.load()
    for y in range(S):
        for x in range(S):
            if x in (1, 30) or y in (1, 30):
                px[x, y] = (24, 24, 27, 255)
    save(grain(door, 12063, 1.5), "void-door")


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
    # (Round 3: the leads' colours toned down; in the dark they read as cables, not as a rainbow)
    for colour in ((32, 50, 96), (112, 112, 110), (112, 96, 34), (30, 30, 30), (32, 86, 48), (96, 34, 34)):
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
            d = math.hypot((x - 15.5) / 16, (y - 5.5) / 6)
            px[x, y] = shade((34, 42, 38), 1.15 - 0.3 * d) + (255,)
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
    # Still whole: a green prompt on black, BOOT and a cursor (the one screen in a cluster that still glows). The screen
    # shows the texture's top twelve rows, the whole width
    boot = canvas((4, 12, 6))
    px = boot.load()
    glyphs = {"B": ["110", "101", "110", "101", "110"], "O": ["111", "101", "101", "101", "111"], "T": ["111", "010", "010", "010", "010"],
              "_": ["000", "000", "000", "000", "111"]}
    x0 = 2
    for ch in "BOOT":
        for gy, row in enumerate(glyphs[ch]):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for dy in range(2):
                        for dx in range(2):
                            px[x0 + gx * 2 + dx, 1 + gy * 2 + dy] = (110, 255, 140, 255)
        x0 += 7
    rect(boot, 30, 9, 31, 10, (110, 255, 140))  # the cursor
    for y in range(0, S, 2):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * 0.75), clamp(g * 0.75), clamp(b * 0.75), 255)
    save(boot, "screen-boot")
    # Smashed: the glass caved in, black behind, cracks running out from the hole
    smashed = canvas((30, 36, 34))
    px = smashed.load()
    cx, cy = 14, 6
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - cx, y - cy)
            if d < 5 + 1.5 * math.sin(math.atan2(y - cy, x - cx) * 5):
                px[x, y] = (5, 5, 6, 255)
    for a in range(9):
        ang = a * 0.7 + rng.uniform(-0.2, 0.2)
        for r in range(5, 22):
            x, y = int(cx + math.cos(ang) * r), int(cy + math.sin(ang) * r)
            if 0 <= x < S and 0 <= y < S:
                px[x, y] = (150, 160, 156, 255)
    save(smashed, "screen-smashed")
    # The broken window's frame (dirty white paint) and its glass
    save(grain(canvas((214, 210, 200)), 12038, 4, 6), "window-frame")
    glass = canvas((170, 196, 200))
    px = glass.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 11 == 0:
                px[x, y] = (226, 238, 240, 255)
    save(glass, "window-glass")
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


def terminal_shape(state):
    """A CRT terminal on a desk, its screen and keyboard to the north: dead, smashed, or whole and glowing (boot)."""
    screen = {"dead": "screen-dead", "smashed": "screen-smashed", "boot": "screen-boot"}[state]
    els = [
        box("Top", (0.5, 10.5, 0.5), (15.5, 11.5, 15.5), {"top": "desk-top", "side": "desk-frame", "bottom": "desk-frame"}),
        box("SideL", (1, 0, 1.5), (2, 10.5, 14.5), "desk-frame", faces=("north", "east", "south", "west")),
        box("SideR", (14, 0, 1.5), (15, 10.5, 14.5), "desk-frame", faces=("north", "east", "south", "west")),
        box("Modesty", (2, 3, 13.5), (14, 10.5, 14.5), "desk-frame", faces=("north", "south")),
        box("Case", (3, 11.5, 3.5), (13, 16, 13), "crt-case", faces=("east", "south", "west", "up")),
        box("Bezel", (3, 11.5, 3), (13, 16, 3.5), "crt-case", faces=("north", "east", "west", "up")),
        box("Screen", (4, 12.5, 2.6), (12, 15.5, 3), screen, faces=("north",), glow=220 if state == "boot" else 0, uv=(0, 0, 16, 6)),
        box("Keyboard", (4, 11.5, 0.8), (12, 12, 2.6), "keyboard", faces=("up", "north", "east", "west")),
    ]
    if state == "smashed":
        # The case knocked askew, glass on the desk
        els[4] = box("Case", (3, 11.5, 3.5), (13, 16, 13), "crt-case", faces=("east", "south", "west", "up"), rot=(0, 12, 0))
        els += [box("Shard0", (5, 11.5, 1), (6, 11.75, 2), "window-glass", faces=("up",)),
                box("Shard1", (9, 11.5, 0.6), (10.5, 11.75, 1.4), "window-glass", faces=("up",))]
    return shape("l120-terminal-" + state, els)


def toppled_shape():
    """A rack toppled onto its back: a cabinet lying nine high, its front of units staring at the ceiling, two units
    slid out onto the floor beside it."""
    els = [
        box("Body", (0.5, 0, 1), (15.5, 8.5, 15.5), {"top": "rack-gutted", "side": "rack-side", "front": "rack-top", "back": "rack-top", "bottom": "rack-top"}),
        box("Lip", (0.5, 8.5, 1), (15.5, 9, 2), "rack-post", faces=("north", "east", "west", "up")),
        box("Unit0", (2, 0, -0.0), (9, 1.5, 1), "rack-front", faces=("north", "east", "west", "up"), rot=(0, 18, 0)),
        box("WireA", (6, 8.5, 4), (6.5, 9, 14), "wire-blue", faces=("up", "east", "west")),
        box("WireB", (10, 8.5, 2), (10.5, 9, 11), "wire-grey", faces=("up", "east", "west")),
    ]
    return shape("l120-wreck-toppled", els)


def torn_shape(part):
    """A rack torn open, two high: the front ripped away, units hanging half out of their bays, wires down its face."""
    els = [
        box("Body", (0.5, 0, 2), (15.5, 16, 15.5), {"front": "rack-gutted", "back": "rack-back", "side": "rack-side", "top": "rack-top", "bottom": "rack-top"}),
        box("PostL", (0.5, 0, 0.5), (1.5, 16, 2), "rack-post", faces=("north", "east", "west")),
    ]
    rng = random.Random("torn-" + part)
    for i in range(2 if part == "lower" else 1):
        y = rng.uniform(3, 12)
        els.append(box(f"Unit{i}", (3, y, -2), (13, y + 1.8, 2), {"front": "rack-front", "side": "rack-side", "top": "rack-top", "bottom": "rack-top", "back": "rack-top"},
                       faces=("north", "east", "west", "up", "down"), rot=(0, 0, rng.choice((-12, 8)))))
    for name, tex_, x in (("WireA", "wire-blue", rng.uniform(3, 6)), ("WireB", "wire-grey", rng.uniform(9, 12))):
        els.append(box(name, (x, 0 if part == "upper" else 1, 1.4), (x + 0.5, 16, 1.9), tex_, faces=("north", "east", "west")))
    if part == "upper":
        els.append(box("DoorHalf", (14.5, 2, -6), (15.5, 15, 0.5), "rack-side", faces=("north", "east", "south", "west", "up"), rot=(0, -35, 0), origin=(15, 8, 0.5)))
    return shape("l120-wreck-torn" + part, els)


def spill_shape(variant):
    """Cables and drive caddies pulled out over the floor, a pixel or two high: walked over (and tripped on)."""
    rng = random.Random("spill-" + variant)
    els = []
    for i in range(5 if variant == "a" else 4):
        x, z = rng.uniform(1, 13), rng.uniform(1, 13)
        ln = rng.uniform(6, 12)
        tex_ = rng.choice(("wire-blue", "wire-grey", "tray-cable"))
        els.append(box(f"Cable{i}", (x, 0, z), (min(16, x + ln), 0.5, z + 0.5), tex_, faces=("up", "north", "south", "east", "west"),
                       rot=(0, rng.choice((-40, -22, 0, 22, 40)), 0)))
    for i in range(2 if variant == "a" else 3):
        x, z = rng.uniform(2, 12), rng.uniform(2, 12)
        els.append(box(f"Caddy{i}", (x, 0, z), (x + 2.5, 1, z + 4), {"top": "rack-front", "side": "rack-side", "front": "rack-post", "back": "rack-post", "bottom": "rack-top"},
                       faces=("up", "north", "south", "east", "west"), rot=(0, rng.choice((-30, 15, 60)), 0)))
    return shape("l120-spill-" + variant, els)


def voiddoor_shape(part):
    """A White Void's black door standing open, flat against the side of its doorway (the passage along x)."""
    return shape("l120-voiddoor-" + part, [
        box("Leaf", (0, 0, 0.5), (16, 16 if part == "lower" else 15, 2), "void-door", faces=("north", "south", "east", "west", "up")),
        box("Frame", (0, 0, 0), (16, 16, 0.5), "void-black", faces=("south", "east", "west")),
    ])


def window_shape(part):
    """A broken window in a wall, the room to the north: a dirty white frame round a hole, jagged glass left round its edges."""
    rng = random.Random("window-" + part)
    els = [
        box("PostL", (0, 0, 6), (2, 16, 10), "window-frame"),
        box("PostR", (14, 0, 6), (16, 16, 10), "window-frame"),
    ]
    if part == "lower":
        els.append(box("Sill", (2, 0, 5), (14, 1.5, 11), "window-frame"))
    else:
        els.append(box("Head", (2, 13.5, 6), (14, 16, 10), "window-frame"))
    # Shards of glass still in the frame, along its sides and bottom (lower) or top (upper)
    for i in range(7):
        side = rng.choice(("l", "r", "e"))
        size = rng.uniform(1.2, 3.2)
        if side == "l":
            x0, y0 = 2, rng.uniform(1, 14)
        elif side == "r":
            x0, y0 = 14 - size, rng.uniform(1, 14)
        else:
            x0, y0 = rng.uniform(2, 13), 1.5 if part == "lower" else 13.5 - size
        els.append(box(f"Shard{i}", (x0, y0, 7.8), (x0 + size, y0 + size, 8.2), "window-glass", faces=("north", "south"),
                       rot=(0, 0, rng.choice((-35, -15, 20, 45)))))
    return shape("l120-window-" + part, els)


# ======================================================================== Block types

def cuboid(b, angle=0):
    c = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if angle:
        c["rotateY"] = angle
    return c


def tex(name):
    return {"base": "block/120/" + name}


def cube_block(code, kinds, comment, material="Stone", sounds=STONE, extra=None):
    data = {"code": code, "variantgroups": [{"code": "kind", "states": list(kinds)}],
            "texturesByType": {f"*-{k}": {"all": tex(v)} for k, v in kinds.items()},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds}
    data.update(extra or {})
    if "dropsByType" in data:
        data.pop("drops")
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def json_block(code, groups, shapes, comment, collision, sounds=METAL, extra=None, inventory=None):
    data = {"code": code, "variantgroups": groups, "shapeByType": shapes,
            "creativeinventory": {"general": [inventory], "backrooms": [inventory]},
            "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 3, "sounds": sounds, "drops": []}
    data.update(collision)
    data.update(extra or {})
    if "dropsByType" in data:
        data.pop("drops")
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def drops(*items):
    """Salvage: (item code, average, variation), the item in this mod's domain unless it names one."""
    return [{"type": "item", "code": c, "quantity": {"avg": avg, "var": var}} for c, avg, var in items]


SIDED = [{"code": "side", "states": SIDES}]
FULL = (0.03, 0, 0.03, 0.97, 1, 0.97)


def sided_shapes(code, base_by_state):
    """shapeByType for a block whose last variant group is its side: each state's base shape turned to face that side."""
    out = {}
    for state, base in base_by_state.items():
        for s in SIDES:
            out[f"{code}-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    return out


def blocktypes():
    cube_block("l120-wall", {"base": "wall-base", "stained": "wall-stained", "rot": "wall-rot", "soot": "wall-soot",
                             "rot2": "wall-rot2", "rot3": "wall-rot3", "skirt": "wall-skirt", "skirtrot": "wall-skirtrot",
                             "skirtstain": "wall-skirtstain"},
               "Level 120: dirty yellow wallpaper over rotting boards (base; stained with brown streaks; rot: the paper torn off; soot: the "
               "Pitch-Black Hallways' near-black paper)", material="Wood", sounds=WOOD)
    cube_block("l120-floor", {k: "floor-" + k for k in ("clean", "dirty", "vent", "hole", "port", "wet")},
               "Level 120: the dirty white floor, two tiles to a block (clean; dirty; vent: a perforated raised-floor panel; hole: a panel "
               "lifted, the cables under it; port: a cable grommet; wet: a puddle under a leak)", sounds=METAL)
    cube_block("l120-ceiling", {"tile": "ceiling-tile", "stained": "ceiling-stained", "broken": "ceiling-broken", "smashed": "ceiling-smashed"},
               "Level 120: office ceiling tiles (plain; water-stained; one fallen through) and a smashed fitting in its housing", sounds=STONE,
               extra={"dropsByType": {"*-smashed": drops(("glassshard", 0.6, 0.4), ("metalbracket", 0.3, 0.3)), "*": drops(("metalbracket", 0.15, 0))}})

    # The White Voids: plain white surfaces, a glowing panel every third block of the ceiling, the black round them
    data = {"code": "l120-void", "variantgroups": [{"code": "kind", "states": ["floor", "wall", "ceiling", "panel", "black", "glitch", "paneldead"]}],
            "texturesByType": {"*-floor": {"all": tex("void-floor")}, "*-black": {"all": tex("void-black")}, "*-glitch": {"all": tex("void-glitch")},
                               "*-paneldead": {"all": tex("void-paneldead")}, "*": {"all": tex("void-white")}},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Stone", "drawtype": "cube", "resistance": 8, "drops": [], "sounds": STONE,
            # (The panel lets its own light out: the mod's lighting takes a source's absorption off its first step)
            "lightAbsorptionByType": {"*-panel": 0, "*": 99},
            "lightHsvByType": {"*-panel": [0, 0, 14]}, "vertexFlagsByType": {"*-panel": {"glowLevel": 255}}}
    write_json(os.path.join(BLOCKS, "l120-void.json"), data,
               "Level 120: the White Voids, white with nothing on it (floor, wall, ceiling; panel: the ceiling's glow, light 14) and the black round them")

    # The rack
    shapes = {}
    for part in ("lower", "upper"):
        for state in RACK_STATES:
            base = rack_shape(part, state)
            for s in SIDES:
                shapes[f"l120-rack-{part}-{state}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    # (Darker than the prototype: a lit rack is a small pool of light in a dark room, not a lamp)
    light = {"*-upper-leda-*": [21, 6, 3], "*-upper-ledb-*": [7, 6, 3], "*-upper-both-*": [30, 5, 4]}
    json_block("l120-rack", [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": RACK_STATES}] + SIDED, shapes,
               "Level 120: a server rack, two blocks high (lower, upper), its front to the side; dark, its LEDs on (bank A green, bank B amber, "
               "both green and blue: the upper block gives a little light), or gutted. Salvage: copper wire, brackets, now and then a circuit board",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"lightHsvByType": light, "dropsByType": {
                   "*-lower-gutted-*": drops(("scrapwire", 0.4, 0.4), ("metalbracket", 0.5, 0.4)),
                   "*-upper-gutted-*": drops(("scrapwire", 0.3, 0.3)),
                   "*-lower-*": drops(("scrapwire", 0.6, 0.5), ("metalbracket", 0.5, 0.4), ("l3999-circuitboard", 0.2, 0)),
                   "*-upper-*": drops(("scrapwire", 0.4, 0.4), ("l3999-circuitboard", 0.15, 0)),
               }}, inventory="l120-rack-lower-leda-north")

    # The wrecks
    shapes = sided_shapes("l120-wreck", {"toppled": toppled_shape(), "tornlower": torn_shape("lower"), "tornupper": torn_shape("upper")})
    low = (0.03, 0, 0.03, 0.97, 0.56, 0.97)
    json_block("l120-wreck", [{"code": "state", "states": ["toppled", "tornlower", "tornupper"]}] + SIDED, shapes,
               "Level 120: a rack ripped apart: toppled onto its back, or torn open (two high, lower and upper) with its units hanging out. "
               "Salvage: copper wire, brackets, circuit boards",
               {"collisionboxByType": {"*-toppled-*": cuboid(low), "*": cuboid(FULL)}, "selectionboxByType": {"*-toppled-*": cuboid(low), "*": cuboid(FULL)}},
               extra={"dropsByType": {"*-toppled-*": drops(("scrapwire", 0.7, 0.5), ("metalbracket", 0.6, 0.4), ("l3999-circuitboard", 0.15, 0)),
                                      "*": drops(("scrapwire", 0.5, 0.4), ("l3999-circuitboard", 0.25, 0), ("metalbracket", 0.3, 0.3))}},
               inventory="l120-wreck-toppled-north")

    # Cables over the floor: walked over
    json_block("l120-spill", [{"code": "kind", "states": ["a", "b"]}], {"*-a": {"base": spill_shape("a")}, "*-b": {"base": spill_shape("b")}},
               "Level 120: cables and drive caddies pulled out over the floor (walked over, and easy to trip on in the dark). Salvage: copper wire",
               {"collisionbox": None, "selectionbox": cuboid((0, 0, 0, 1, 0.08, 1))},
               extra={"drops": drops(("scrapwire", 0.4, 0.3))}, inventory="l120-spill-a")

    # The tray
    tray = tray_shape(False)
    tb = (0, 0.7, 0.28, 1, 1, 0.72)
    json_block("l120-tray", [{"code": "kind", "states": ["we", "ns"]}], {"*-we": {"base": tray}, "*-ns": {"base": tray, "rotateY": 90}},
               "Level 120: an overhead cable tray, a mesh channel full of black cable hung on rods, along x (we) or z (ns)",
               {"collisionboxByType": {"*-we": cuboid(tb), "*-ns": cuboid(tb, 90)},
                "selectionboxByType": {"*-we": cuboid(tb), "*-ns": cuboid(tb, 90)}},
               extra={"drops": drops(("scrapwire", 0.5, 0.4))}, inventory="l120-tray-we")

    # The terminal: booting a whole one is the way into the pockets (L120System)
    shapes = sided_shapes("l120-terminal", {s: terminal_shape(s) for s in ("dead", "smashed", "boot")})
    json_block("l120-terminal", [{"code": "state", "states": ["dead", "smashed", "boot"]}] + SIDED, shapes,
               "Level 120: a CRT terminal on a grey desk, its screen to the side: dead, smashed, or whole (a green BOOT prompt, a little light; "
               "right-click to boot it). Salvage: glass, wire, a circuit board",
               {"collisionbox": cuboid(FULL), "selectionbox": cuboid(FULL)},
               extra={"lightHsvByType": {"*-boot-*": [22, 6, 5]},
                      "behaviorsByType": {"*-boot-*": [{"name": "BackroomsL120Boot"}]},
                      "resistanceByType": {"*-boot-*": 40, "*": 3},
                      "dropsByType": {"*-boot-*": [], "*": drops(("glassshard", 0.6, 0.4), ("scrapwire", 0.3, 0.3), ("l3999-circuitboard", 0.25, 0))}},
               inventory="l120-terminal-boot-north")

    # A White Void's black door, standing open
    shapes = {}
    for part in ("lower", "upper"):
        base = voiddoor_shape(part)
        shapes[f"l120-voiddoor-{part}-we"] = {"base": base}
        shapes[f"l120-voiddoor-{part}-ns"] = {"base": base, "rotateY": 90}
    leaf = (0, 0, 0, 1, 1, 0.125)
    json_block("l120-voiddoor", [{"code": "part", "states": ["lower", "upper"]}, {"code": "way", "states": ["we", "ns"]}], shapes,
               "Level 120: a White Void's black door, standing open against the side of its doorway (two high; the way through along x or z)",
               {"collisionboxByType": {"*-we": cuboid(leaf), "*-ns": cuboid(leaf, 90)}, "selectionboxByType": {"*-we": cuboid(leaf), "*-ns": cuboid(leaf, 90)}},
               extra={"resistance": 40}, inventory="l120-voiddoor-lower-we")

    # The broken window: walk into it (L120System)
    shapes = sided_shapes("l120-window", {"lower": window_shape("lower"), "upper": window_shape("upper")})
    json_block("l120-window", [{"code": "part", "states": ["lower", "upper"]}] + SIDED, shapes,
               "Level 120: a broken window at the edge of a pocket, black beyond it (two high): walk into it to go back to the terminal that brought you",
               {"collisionbox": None, "selectionbox": cuboid((0, 0, 0.3, 1, 1, 0.7))},
               extra={"resistance": 40}, inventory="l120-window-lower-north")


# ======================================================================== The ways in and out (LINKS.md)

GLYPHS = {"S": ["111", "100", "111", "001", "111"], "E": ["111", "100", "110", "100", "111"], "R": ["110", "101", "110", "101", "101"],
          "V": ["101", "101", "101", "101", "010"], "O": ["111", "101", "101", "101", "111"], "M": ["101", "111", "101", "101", "101"]}


def pixel_text(img, word, x0, y0, colour):
    """A word in the 3 x 5 capitals above, one pixel apart."""
    px = img.load()
    for ch in word:
        for gy, row in enumerate(GLYPHS[ch]):
            for gx, bit in enumerate(row):
                if bit == "1":
                    px[x0 + gx, y0 + gy] = tuple(colour) + (255,)
        x0 += 4


def big_text(img, text, box_, colour, size):
    """Centred text in a box, drawn large and scaled down (as gen_textures.text_img)."""
    from PIL import ImageDraw, ImageFont
    x0, y0, x1, y1 = box_
    k = 4
    big = Image.new("RGBA", ((x1 - x0) * k, (y1 - y0) * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    font = ImageFont.load_default(size=size * k)
    w, h = d.textbbox((0, 0), text, font=font)[2:]
    d.text(((big.width - w) / 2, (big.height - h) / 2 - k), text, font=font, fill=tuple(colour) + (255,))
    img.alpha_composite(big.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))


def door_textures():
    """The steel door, both faces alike (the block has no facing): grey paint over steel, the frame's edge down both sides,
    a kick plate, the gap under it (the light strip is its own element); the upper half plain, or with the SERVER ROOM
    plate at eye height (Level 4's side). 'office' paint is clean, 'dark' (Level 120's side) grimed and scuffed."""
    for look, paint, grime in (("office", (124, 130, 134), False), ("dark", (96, 100, 102), True)):
        for part in ("lower", "upper"):
            img = grain(canvas(paint), 12090 + (part == "upper") + 2 * (look == "dark"), 3, 5)
            rect(img, 0, 0, 1, S - 1, shade(paint, 0.55))
            rect(img, S - 2, 0, S - 1, S - 1, shade(paint, 0.55))
            if part == "upper":
                rect(img, 0, 0, S - 1, 1, shade(paint, 0.55))
            else:
                rect(img, 2, 22, S - 3, 29, (150, 152, 148))
                for sx in (4, S - 5):
                    for sy in (23, 28):
                        rect(img, sx, sy, sx, sy, (96, 98, 96))
                rect(img, 2, 30, S - 3, S - 1, (10, 10, 12))
                rect(img, 22, 1, 25, 5, shade(paint, 0.7))  # the lock's escutcheon
                rect(img, 23, 4, 24, 4, (20, 20, 22))
                rect(img, 22, 7, 25, 10, shade(paint, 0.62))  # the lever's rose, and the lever
                rect(img, 13, 8, 23, 9, (178, 180, 176))
                rect(img, 13, 10, 23, 10, shade(paint, 0.6))
            if grime:
                rng = random.Random("door-grime-" + part)
                px = img.load()
                for _ in range(36):
                    x, y = rng.randrange(2, S - 2), rng.randrange(S)
                    r, g, b, a = px[x, y]
                    k = rng.uniform(0.8, 0.92)
                    px[x, y] = (clamp(r * k), clamp(g * k * 0.98), clamp(b * k * 0.95), a)
                for _ in range(2 if part == "lower" else 1):  # scuffs, as if kicked
                    x = rng.randrange(4, S - 10)
                    y = rng.randrange(15, 21) if part == "lower" else rng.randrange(6, 26)
                    rect(img, x, y, x + rng.randint(2, 4), y, shade(paint, 1.12))
            if look == "office" and part == "upper":
                marked = img  # (only ever with its plate)
            elif look == "dark" and part == "upper":
                # Round 3: Level 120's side carries its plate too, the same plate: EXIT, and where to
                rect(img, 2, 8, 29, 23, (60, 60, 58))
                rect(img, 3, 9, 28, 22, (214, 210, 196))
                big_text(img, "EXIT", (3, 9, 29, 17), (26, 26, 30), 8)
                big_text(img, "OFFICES", (3, 16, 29, 22), (26, 26, 30), 5)
                for sx in (3, 28):
                    rect(img, sx, 9, sx, 9, (120, 120, 116))
                save(img, f"door-{look}-{part}")
            else:
                save(img, f"door-{look}-{part}")
    # The plate on Level 4's side: SERVER ROOM in black on an off-white plate, screwed on
    img = marked
    rect(img, 2, 8, 29, 23, (60, 60, 58))
    rect(img, 3, 9, 28, 22, (222, 218, 204))
    pixel_text(img, "SERVER", 5, 10, (26, 26, 30))
    pixel_text(img, "ROOM", 9, 16, (26, 26, 30))
    for sx in (3, 28):
        rect(img, sx, 9, sx, 9, (120, 120, 116))
    save(img, "door-office-upper-marked")
    save(grain(canvas((86, 90, 94)), 12094, 3), "door-edge")
    # The light in the gap under the door: cold green from the racks behind it, warm office light from beyond it
    save(canvas((130, 255, 200)), "door-gap-office")
    save(canvas((255, 232, 186)), "door-gap-dark")
    # The M.E.G. placard (128 x 96, mapped whole onto the plate), in the style of the levels' own (tools/gen_lore.py)
    from PIL import ImageDraw
    plate = Image.new("RGBA", (128, 96), (0x2A, 0x30, 0x30, 255))
    d = ImageDraw.Draw(plate)
    d.rectangle([0, 0, 127, 95], outline=(0x8C, 0x94, 0x90))
    d.rectangle([3, 3, 124, 92], outline=(0x58, 0x5F, 0x5C))
    d.rectangle([6, 6, 121, 30], fill=(0xA8, 0xA8, 0x3C))
    big_text(plate, "M.E.G. - LEVEL 120 - CLASS 2", (8, 8, 120, 28), (0x14, 0x10, 0x0C), 7)
    big_text(plate, "PITCH DARK.", (6, 40, 122, 62), (0xE8, 0xE4, 0xD4), 8)
    big_text(plate, "DO NOT DIE HERE", (6, 64, 122, 86), (0xE8, 0xE4, 0xD4), 8)
    for sx, sy in ((10, 86), (117, 86)):
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(0x7A, 0x80, 0x7C))
    os.makedirs(TEX, exist_ok=True)
    plate.save(os.path.join(TEX, "megplacard-120.png"))


def door_shape(look, part):
    """A steel door filling its block, the same on all four sides (the block has no facing: whichever way its wall runs,
    the faces out of it are the door, the others are hidden in the wall); on the lower half the strip of light in the gap
    under it (glowing) on every side. The lever is painted on, beside the lock, so the two agree on every face."""
    face = f"door-{look}-{part}" + ("-marked" if look == "office" and part == "upper" else "")
    els = [box("Leaf", (0, 0, 0), (16, 16, 16), {"side": face, "top": "door-edge", "bottom": "door-edge"})]
    if part == "lower":
        gap = f"door-gap-{look}"
        els.append(box("GapNS", (2, 0, -0.05), (14, 0.9, 16.05), gap, faces=("north", "south"), glow=200))
        els.append(box("GapWE", (-0.05, 0, 2), (16.05, 0.9, 14), gap, faces=("east", "west"), glow=200))
    return shape(f"l120-door-{look}-{part}", els)


def placard_shape():
    """The M.E.G. placard: a steel plate flush on the wall to the south, its face to the north."""
    return shape("l120-megplacard", [
        box("Plate", (0, 4, 15), (16, 16, 16), "megplacard-120", faces=("north",), uv=(0, 0, 16, 16)),
        box("Back", (0, 4, 15.01), (16, 16, 16), "door-edge", faces=("south", "east", "west", "up", "down")),
    ])


def link_blocktypes():
    """The SERVER ROOM door (Level 4's side, kind l120-serverroom), the doors back (Level 120's side, kind l120-door), and
    the placard. The doors are thresholds: nothing to salvage, and not to be broken through."""
    shapes = {f"l120-door-{look}-{part}": {"base": door_shape(look, part)} for look in ("office", "dark") for part in ("lower", "upper")}
    full = cuboid((0, 0, 0, 1, 1, 1))
    data = {"code": "l120-door", "variantgroups": [{"code": "look", "states": ["office", "dark"]}, {"code": "part", "states": ["lower", "upper"]}],
            "shapeByType": shapes, "creativeinventory": {"general": ["*-lower"], "backrooms": ["*-lower"]},
            "blockmaterial": "Metal", "drawtype": "json", "collisionbox": full, "selectionbox": full,
            # (The lower half lets its own light out: the mod's lighting takes a source's absorption off its first step)
            "lightAbsorptionByType": {"*-lower": 0, "*": 99},
            "lightHsvByType": {"*-office-lower": [26, 4, 3], "*-dark-lower": [8, 2, 3]},
            "behaviorsByType": {"*-office-*": [{"name": "BackroomsThreshold", "properties": {"kind": "l120-serverroom"}}],
                                "*-dark-*": [{"name": "BackroomsThreshold", "properties": {"kind": "l120-door"}}]},
            "resistance": 99999, "drops": [], "sounds": METAL}
    write_json(os.path.join(BLOCKS, "l120-door.json"), data,
               "Level 120's doors (two high, alike on both faces): office, the door marked SERVER ROOM in Level 4's offices, a cold green light "
               "under it (kind l120-serverroom, into Level 120); dark, a door in a server room's or a hallway's wall in Level 120, a line of "
               "office light under it (kind l120-door, back to the offices)")
    sb = {"x1": 0, "y1": 0.25, "z1": 0.94, "x2": 1, "y2": 1, "z2": 1}
    json_block("l120-megplacard", SIDED, {f"l120-megplacard-{s}": {"base": placard_shape(), "rotateY": ROTATE[s]} for s in SIDES},
               "An M.E.G. placard beside Level 4's door marked SERVER ROOM: LEVEL 120, CLASS 2, PITCH DARK, DO NOT DIE HERE",
               {"collisionbox": None, "selectionboxByType": {f"*-{s}": dict(sb, **({"rotateY": ROTATE[s]} if ROTATE[s] else {})) for s in SIDES}},
               extra={"resistance": 1.5}, inventory="l120-megplacard-north")


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


# ======================================================================== The Misglitch

def misglitch_entity():
    """The Misglitch's entity type (its model and sounds: gen_120_misglitch.py, gen_120_sounds.py). Put down where a
    player dies in the level, by L120System; driven by AiTaskMisglitch (src/Regions/L120Misglitch.cs)."""
    anims = [("idle", "AddAverage", {"triggeredBy": {"defaultAnim": True}, "easeOutSpeed": 4}),
             ("lurk", "Average", {}), ("glitch", "AddAverage", {"weight": 4}), ("walk", "Average", {}), ("run", "Average", {}),
             ("attack", "Average", {"weight": 10}), ("hurt", "AddAverage", {"weight": 10}),
             ("die", "Average", {"weight": 10, "triggeredBy": {"onControls": ["dead"]}})]
    animations = []
    for code, blend, more in anims:
        a = {"code": code, "animation": code, "animationSpeed": 1.0, "blendMode": blend}
        a.update(more)
        animations.append(a)
    data = {
        "code": "l120-misglitch",
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": 60,
        "canClimb": True,
        "hitboxSize": {"x": 0.6, "y": 1.9},
        "deadHitboxSize": {"x": 0.6, "y": 0.5},
        "eyeHeight": 1.7,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-l120-misglitch"},
        "client": {
            "renderer": "Shape",
            "shape": {"base": "backrooms:entity/120/l120-misglitch"},
            "texture": {"base": "backrooms:entity/120/l120-misglitch", "alternates": [{"base": "backrooms:entity/120/l120-misglitch-black"}]},
            "size": 1.0,
            "behaviors": [{"code": "repulseagents", "movable": True}, {"code": "controlledphysics", "stepHeight": 1.1251},
                          {"code": "floatupwhenstuck", "onlyWhenDead": True}, {"code": "interpolateposition"}],
            "animations": animations,
        },
        "server": {
            "behaviors": [
                {"code": "repulseagents", "movable": True},
                {"code": "controlledphysics", "stepHeight": 1.1251},
                {"code": "health", "currenthealth": 20, "maxhealth": 20},
                {"code": "deaddecay", "hoursToDecay": 0.05},
                {"code": "floatupwhenstuck", "onlyWhenDead": True},
                {"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": [{
                    "code": "backrooms-l120-misglitch", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
                    "walkSpeed": 0.016, "runSpeed": 0.043,
                    "touch": 6, "sneakTouch": 3.5, "hearing": 18, "lightSight": 16, "leash": 32,
                    "attackRange": 2.4, "damage": 5, "damageTier": 2, "knockback": 0.35,
                    "attackDurationMs": 1000, "damageAtMs": 430, "attackCooldownMs": 1700,
                    "skipEveryMs": 4500, "skipDistance": 2.2, "patienceMs": 25000, "lifeHours": 24,
                    "staticSounds": ["backrooms:entity/120/misglitch-static1", "backrooms:entity/120/misglitch-static2", "backrooms:entity/120/misglitch-static3"],
                    "huntSound": "backrooms:entity/120/misglitch-hunt", "sliceSound": "backrooms:entity/120/misglitch-slice",
                    "skipSound": "backrooms:entity/120/misglitch-step"}]},
                {"code": "entitystatetags"},
            ],
        },
        "sounds": {"hurt": "backrooms:entity/120/misglitch-hurt", "death": "backrooms:entity/120/misglitch-death"},
    }
    path = os.path.join(ASSETS, "entities", "l120-misglitch.json")
    write_json(path, data, "Level 120's Misglitch: what someone who died here became (L120System puts one down where any player dies in the level). "
               "Texture 0 red marks, 1 all black (an internal death)")


def main():
    wall_textures()
    floor_textures()
    ceiling_textures()
    void_textures()
    rack_textures()
    prop_textures()
    door_textures()
    blocktypes()
    link_blocktypes()
    misglitch_entity()
    serverhum()
    # Round 3's detail blocks (tools/gen_120_detail.py, built on the textures above)
    import gen_120_detail
    gen_120_detail.main()
    print("Level 120: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
