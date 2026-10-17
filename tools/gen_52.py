"""Level 52, "School Halls" (experimental): its six blocks, their textures and shapes, and its one sound.

    l52-wall        the school's two-tone painted wall: base (mint, dark skirting), dado (mint, the dark rail at its top),
                    upper (off-white); cubes
    l52-locker      a bank of three steel lockers on one face of a wall block (lower: latches and a louvre; upper: vents
                    and number plates), the other faces the wall's paint; cubes, by part and side
    l52-tile        vinyl floor tile: hall (beige and cream checks), room (plain speckled tile); cubes
    l52-gymfloor    maple boards: plain, and with a painted court line north-south or west-east; cubes
    l52-desk        a student desk with its chair joined on, the student facing the side (north 0); JSON shape
    l52-chalkboard  a piece of chalkboard hung on the wall behind it: lower (with the chalk ledge) and upper, the
                    board's left end, middle or right end (as seen from in front), by side; JSON shape
    sounds/ambient/52/bell.ogg   a school bell ringing somewhere far down the halls

Textures are 32 px a block (block/52/), shapes 16 units (block/52/); every shape names its texture keys one by one
and its blocktype names no textures, so nothing overrides them (a blocktype's `textures: { all }` would override every
key of a shape). Run from the repo root:  python tools/gen_52.py
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

from modelkit import box
from oggutil import write_ogg
from gen_entity_sounds import RATE, band, reverb, seconds

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "52")
SHAPES = os.path.join(ASSETS, "shapes", "block", "52")
BLOCKS = os.path.join(ASSETS, "blocktypes", "52")
S = 32
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}

MINT = (156, 194, 174)
WHITE = (228, 224, 211)
RAIL = (74, 92, 84)
SKIRT = (62, 70, 67)
STEEL = (112, 133, 150)
SEAM = (52, 62, 72)


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


# ======================================================================== Textures

def canvas(colour):
    return Image.new("RGBA", (S, S), tuple(colour) + (255,))


def noise(img, seed, amount=6, mottle=0.0):
    """Fine grain over everything, and (mottle) a soft blotchiness."""
    rng = random.Random(seed)
    px = img.load()
    blot = [[0.0] * S for _ in range(S)]
    if mottle:
        for _ in range(6):
            cx, cy, r, d = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(5, 12), rng.uniform(-1, 1)
            for y in range(S):
                for x in range(S):
                    # Wrapped distance so the blotches tile
                    dx = min(abs(x - cx), S - abs(x - cx))
                    dy = min(abs(y - cy), S - abs(y - cy))
                    blot[y][x] += d * max(0.0, 1 - math.hypot(dx, dy) / r)
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount) + mottle * blot[y][x]
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), a)
    return img


def clamp(v):
    return max(0, min(255, int(round(v))))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def rect(img, x0, y0, x1, y1, colour):
    px = img.load()
    for y in range(max(0, y0), min(S, y1 + 1)):
        for x in range(max(0, x0), min(S, x1 + 1)):
            px[x, y] = tuple(colour) + (255,)


def save(img, name):
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def wall_textures():
    # The mint base with its dark skirting, the dado with the rail along its top, the off-white above
    base = canvas(MINT)
    rect(base, 0, 27, 31, 31, SKIRT)
    rect(base, 0, 26, 31, 26, shade(MINT, 0.82))
    rect(base, 0, 27, 31, 27, shade(SKIRT, 1.25))
    save(noise(base, 5201, 4, 5), "wall-base")
    dado = canvas(MINT)
    rect(dado, 0, 0, 31, 2, RAIL)
    rect(dado, 0, 1, 31, 1, shade(RAIL, 1.3))
    rect(dado, 0, 3, 31, 3, shade(MINT, 0.85))
    save(noise(dado, 5202, 4, 5), "wall-dado")
    upper = canvas(WHITE)
    save(noise(upper, 5203, 3, 4), "wall-upper")


def locker(part):
    """Three locker doors across the block, seams between them; latches and a louvre below, vents and plates above."""
    img = canvas(STEEL)
    px = img.load()
    rng = random.Random(5210 + (part == "upper"))
    # A soft vertical sheen down each door
    doors = [(1, 10), (12, 21), (23, 31)]
    for x0, x1 in doors:
        tint = rng.uniform(0.94, 1.06)
        for y in range(S):
            for x in range(x0, x1 + 1):
                k = tint * (1.04 - 0.08 * abs((x - x0) / max(1, x1 - x0) - 0.35))
                px[x, y] = shade(STEEL, k) + (255,)
    for sx in (0, 11, 22):
        rect(img, sx, 0, sx, 31, SEAM)
    if part == "lower":
        rect(img, 0, 28, 31, 31, (44, 52, 58))  # the kick base
        rect(img, 0, 27, 31, 27, SEAM)
        for x0, x1 in doors:
            # The latch: a recessed lift handle near the top of the lower half, on the door's right
            rect(img, x1 - 3, 2, x1 - 1, 7, (58, 66, 74))
            rect(img, x1 - 2, 3, x1 - 2, 6, (176, 182, 188))
            # A louvre near the foot
            for y in (20, 22, 24):
                rect(img, x0 + 2, y, x1 - 2, y, SEAM)
                rect(img, x0 + 2, y + 1, x1 - 2, y + 1, shade(STEEL, 1.15))
    else:
        rect(img, 0, 0, 31, 1, SEAM)  # the top of the bank
        for i, (x0, x1) in enumerate(doors):
            for y in (5, 7, 9, 11):
                rect(img, x0 + 2, y, x1 - 2, y, SEAM)
                rect(img, x0 + 2, y + 1, x1 - 2, y + 1, shade(STEEL, 1.15))
            # The number plate
            rect(img, x0 + 3, 16, x1 - 3, 18, (206, 204, 192))
            for k in range(rng.randint(2, 3)):
                rect(img, x0 + 4 + 2 * k, 17, x0 + 4 + 2 * k, 17, (60, 60, 60))
    # A scratch or two
    for _ in range(3):
        x, y = rng.randint(1, 30), rng.randint(3, 25)
        for k in range(rng.randint(3, 6)):
            if 0 <= x + k < S and 0 <= y + k // 2 < S:
                px[x + k, y + k // 2] = shade(STEEL, 1.25) + (255,)
    save(noise(img, 5212 + (part == "upper"), 3), "locker-" + part)


def floor_textures():
    # The halls: 16 px checks of beige and cream with grout, scuffed by a century of shoes
    hall = Image.new("RGBA", (S, S))
    px = hall.load()
    beige, cream, grout = (214, 202, 176), (238, 232, 216), (180, 170, 150)
    for y in range(S):
        for x in range(S):
            c = beige if ((x // 16) + (y // 16)) % 2 == 0 else cream
            if x % 16 == 0 or y % 16 == 0:
                c = grout
            px[x, y] = c + (255,)
    rng = random.Random(5220)
    for _ in range(9):
        x, y, n = rng.randint(0, 31), rng.randint(0, 31), rng.randint(2, 5)
        for k in range(n):
            px[(x + k) % S, (y + (k // 2)) % S] = (128, 122, 112, 255)
    save(noise(hall, 5221, 4, 3), "tile-hall")
    # The classrooms: plain speckled tile, the grout barely there
    room = canvas((204, 198, 186))
    px = room.load()
    for _ in range(140):
        x, y = rng.randint(0, 31), rng.randint(0, 31)
        px[x, y] = (shade((204, 198, 186), rng.choice((0.8, 0.86, 1.08)))) + (255,)
    for i in range(S):
        for (x, y) in ((i, 0), (0, i), (i, 16), (16, i)):
            px[x, y] = shade(px[x, y][:3], 0.93) + (255,)
    save(noise(room, 5222, 3, 4), "tile-room")
    # The gym: maple boards along X, the joints staggered, a varnished sheen; and its court lines
    for kind in ("plain", "linens", "linewe"):
        img = Image.new("RGBA", (S, S))
        px = img.load()
        rng = random.Random(5230)
        for board in range(8):
            tone = rng.uniform(0.9, 1.08)
            joint = rng.randint(0, 31)
            for y in range(board * 4, board * 4 + 4):
                for x in range(S):
                    c = shade((214, 172, 112), tone * (1 + 0.04 * math.sin(x * 0.7 + board)))
                    if y == board * 4 or x == joint:
                        c = shade(c, 0.7)
                    px[x, y] = c + (255,)
        if kind == "linens":
            rect(img, 13, 0, 18, 31, (44, 76, 156))
        if kind == "linewe":
            rect(img, 0, 13, 31, 18, (44, 76, 156))
        save(noise(img, 5231, 3), "gymfloor-" + kind)


def prop_textures():
    rng = random.Random(5240)
    # The slate, chalk ghosts of old lessons on it
    slate = canvas((44, 70, 58))
    px = slate.load()
    for _ in range(7):
        x, y = rng.uniform(2, 28), rng.uniform(3, 28)
        length, slope = rng.uniform(4, 12), rng.uniform(-0.3, 0.3)
        for k in range(int(length)):
            xi, yi = int(x + k), int(y + k * slope + 0.6 * math.sin(k * 1.3))
            if 0 <= xi < S and 0 <= yi < S:
                r, g, b, a = px[xi, yi]
                px[xi, yi] = (clamp(r + 34), clamp(g + 36), clamp(b + 34), 255)
    save(noise(slate, 5241, 3, 6), "slate")
    save(noise(canvas((140, 104, 66)), 5242, 6), "frame")
    save(noise(canvas((172, 176, 180)), 5243, 4), "ledge")
    save(noise(canvas((236, 236, 228)), 5244, 3), "chalk")
    # The desk: a light wood-look laminate, black steel tube, blue moulded plastic
    top = canvas((206, 176, 132))
    px = top.load()
    for y in range(S):
        for x in range(S):
            k = 1 + 0.05 * math.sin(y * 0.9 + 2 * math.sin(x * 0.2))
            px[x, y] = shade(px[x, y][:3], k) + (255,)
    save(noise(top, 5245, 3), "desktop")
    save(noise(canvas((58, 60, 64)), 5246, 4), "tube")
    save(noise(canvas((62, 96, 146)), 5247, 4), "plastic")
    save(noise(canvas((96, 100, 106)), 5248, 4), "tray")


# ======================================================================== Shapes

def shape(name, elements):
    keys = sorted({face["texture"][1:] for e in elements for face in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: "backrooms:block/52/" + k for k in keys}, "elements": elements}
    write_json(os.path.join(SHAPES, name + ".json"), data)
    return "backrooms:block/52/" + name


def desk_shape():
    # The student faces north: the desk top before them, the chair behind, joined by a runner along the floor
    els = [
        box("Top", (1.5, 11, 1), (14.5, 11.8, 8.5), "desktop"),
        box("Tray", (2.5, 9.4, 1.8), (13.5, 11, 7.8), "tray", faces=("north", "east", "west", "down")),
        box("LegL", (2.2, 0, 2), (3.2, 11, 3), "tube"),
        box("LegR", (12.8, 0, 2), (13.8, 11, 3), "tube"),
        box("FootL", (2, 0, 1.2), (3.4, 0.8, 7.8), "tube"),
        box("FootR", (12.6, 0, 1.2), (14, 0.8, 7.8), "tube"),
        box("Runner", (7.4, 0.2, 7.8), (8.6, 1.2, 13), "tube"),
        box("Post", (7.4, 1.2, 11.4), (8.6, 7, 12.6), "tube"),
        box("Seat", (3.5, 7, 9.2), (12.5, 8, 14.2), "plastic"),
        box("Back", (3.8, 9.6, 14.4), (12.2, 14.6, 15.2), "plastic"),
        box("BackPostL", (4.6, 8, 14.5), (5.4, 9.6, 15), "tube"),
        box("BackPostR", (10.6, 8, 14.5), (11.4, 9.6, 15), "tube"),
    ]
    return shape("l52-desk", els)


def board_shape(part, end):
    """A piece of chalkboard against the wall to its south, modelled facing north (left = +X as seen from in front)."""
    els = []
    if part == "lower":
        els += [box("Slate", (0, 2, 15), (16, 16, 16), "slate", faces=("north",)),
                box("FrameB", (0, 1, 14.5), (16, 2.2, 16), "frame", faces=("north", "up", "down")),
                box("Ledge", (0, 1.2, 12.6), (16, 1.8, 14.5), "ledge", faces=("north", "up", "down", "east", "west"))]
        if end == "m":
            els += [box("Chalk", (5, 1.8, 13), (7.5, 2.3, 13.6), "chalk"),
                    box("Eraser", (10, 1.8, 12.9), (12.6, 2.8, 14), "frame")]
        y0, y1 = 1, 16
    else:
        els += [box("Slate", (0, 0, 15), (16, 13, 16), "slate", faces=("north",)),
                box("FrameT", (0, 13, 14.5), (16, 14.5, 16), "frame", faces=("north", "up", "down"))]
        y0, y1 = 0, 14.5
    if end == "l":
        els.append(box("FrameL", (14.8, y0, 14.5), (16, y1, 16), "frame", faces=("north", "east", "west", "up", "down")))
    if end == "r":
        els.append(box("FrameR", (0, y0, 14.5), (1.2, y1, 16), "frame", faces=("north", "east", "west", "up", "down")))
    return shape(f"l52-chalkboard-{part}-{end}", els)


# ======================================================================== Block types

def cuboid(b, angle=0):
    c = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if angle:
        c["rotateY"] = angle
    return c


def tex(name):
    return {"base": "block/52/" + name}


def cube_block(code, groups, textures_by_type, comment, material="Stone", sounds=STONE, extra=None):
    data = {"code": code, "variantgroups": groups, "texturesByType": textures_by_type,
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds}
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def blocktypes():
    walls = {"base": "wall-base", "dado": "wall-dado", "upper": "wall-upper"}
    cube_block("l52-wall", [{"code": "kind", "states": list(walls)}],
               {f"*-{k}": {"all": tex(v)} for k, v in walls.items()},
               "Level 52: the school's two-tone painted wall (base: mint with a dark skirting; dado: mint, the rail at its top; upper: off-white)")

    lockers = {}
    for part in ("lower", "upper"):
        back = "wall-base" if part == "lower" else "wall-dado"
        for side in SIDES:
            faces = {f: tex(back) for f in SIDES}
            faces[side] = tex("locker-" + part)
            faces["up"] = faces["down"] = tex("wall-upper")
            lockers[f"l52-locker-{part}-{side}"] = faces
    cube_block("l52-locker", [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}], lockers,
               "Level 52: a bank of three steel lockers on the side face of a wall block (lower: latches, louvres, the kick base; upper: vents and "
               "number plates); its other faces are the wall's paint", material="Metal", sounds=METAL)

    cube_block("l52-tile", [{"code": "kind", "states": ["hall", "room"]}],
               {"*-hall": {"all": tex("tile-hall")}, "*-room": {"all": tex("tile-room")}},
               "Level 52: vinyl floor tile (hall: beige and cream checks, scuffed; room: plain speckled tile)")

    cube_block("l52-gymfloor", [{"code": "kind", "states": ["plain", "linens", "linewe"]}],
               {f"*-{k}": {"all": tex("gymfloor-" + k)} for k in ("plain", "linens", "linewe")},
               "Level 52: the gym's maple boards, plain or with a painted court line north-south or west-east",
               material="Wood", sounds=WOOD)

    # The desk
    desk = desk_shape()
    box_ = (0.06, 0, 0.06, 0.94, 0.75, 0.94)
    data = {"code": "l52-desk", "variantgroups": [{"code": "side", "states": SIDES}],
            "shapeByType": {f"*-{s}": {"base": desk, "rotateY": ROTATE[s]} for s in SIDES},
            "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
            "blockmaterial": "Wood", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 1.5, "sounds": METAL,
            "collisionboxByType": {f"*-{s}": cuboid(box_, ROTATE[s]) for s in SIDES},
            "selectionboxByType": {f"*-{s}": cuboid(box_, ROTATE[s]) for s in SIDES},
            "drops": [{"type": "item", "code": "game:stick", "quantity": {"avg": 1, "var": 1}},
                      {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0.3}}]}
    write_json(os.path.join(BLOCKS, "l52-desk.json"), data,
               "Level 52: a student desk with its chair joined on (light laminate, black tube, blue plastic); the student faces the side")

    # The chalkboard
    shapes = {}
    for part in ("lower", "upper"):
        for end in ("l", "m", "r"):
            base = board_shape(part, end)
            for s in SIDES:
                shapes[f"l52-chalkboard-{part}-{end}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    thin = (0, 0, 0.875, 1, 1, 1)
    data = {"code": "l52-chalkboard",
            "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "end", "states": ["l", "m", "r"]}, {"code": "side", "states": SIDES}],
            "shapeByType": shapes,
            "creativeinventory": {"general": ["l52-chalkboard-lower-m-north"], "backrooms": ["l52-chalkboard-lower-m-north"]},
            "blockmaterial": "Wood", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 1.5, "sounds": WOOD,
            "collisionboxByType": {f"*-{s}": cuboid(thin, ROTATE[s]) for s in SIDES},
            "selectionboxByType": {f"*-{s}": cuboid(thin, ROTATE[s]) for s in SIDES},
            "drops": [{"type": "item", "code": "game:plank-aged", "quantity": {"avg": 0.5, "var": 0.5}}]}
    write_json(os.path.join(BLOCKS, "l52-chalkboard.json"), data,
               "Level 52: a piece of green chalkboard in a wooden frame, hung on the wall behind it (lower: the chalk ledge; upper; the left end, "
               "middle or right end as seen from in front)")


# ======================================================================== Sound

def bell():
    """An electric school bell somewhere far down the halls: a hammer drumming on a gong for two and a half seconds,
    heard through a long corridor (the highs gone, a hallway's reflections)."""
    rng = np.random.default_rng(5250)
    t = seconds(3.6)
    ring = np.zeros(len(t))
    for f, a, d in ((1180, 1.0, 1.6), (2730, 0.55, 2.4), (3990, 0.35, 3.2), (620, 0.3, 1.0)):
        ring += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * d * 0.2)
    # The hammer: 22 strikes a second while the current is on, then the gong rings down
    on = (t < 2.6).astype(float)
    hammer = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 22 * t))
    env = on * hammer * np.minimum(1, t / 0.03) + (1 - on) * np.exp(-(t - 2.6) * 5)
    sig = ring * env
    sig += 0.04 * band(rng.normal(size=len(t)), 300, 2000) * on
    far = reverb(band(sig, 250, 2600), decay=0.6)
    n = int(0.01 * RATE)
    far[:n] *= np.linspace(0, 1, n)
    far[-n:] *= np.linspace(1, 0, n)
    far = 0.6 * far / max(1e-9, np.max(np.abs(far)))
    path = os.path.join(ASSETS, "sounds", "ambient", "52", "bell.ogg")
    if write_ogg(path, far, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def main():
    wall_textures()
    locker("lower")
    locker("upper")
    floor_textures()
    prop_textures()
    blocktypes()
    bell()
    print("Level 52: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
