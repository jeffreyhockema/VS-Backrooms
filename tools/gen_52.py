"""Level 52, "The Greenfield Campus" (experimental): its blocks, their textures and shapes, its sun and its one sound.

    l52-wall-{palette}-{part}      painted interior wall (beige, white, blue, grey; base with skirting, dado with rail, upper); cubes
    l52-locker-{palette}-{part}-{side}   a bank of three steel lockers on one face of a wall block; cubes
    l52-facade-{palette}           exterior wall (white, beige, brick, grey, blue); l52-coping parapet cap; l52-barrier fence base
    l52-band-{kind}, l52-plinth, l52-canopy   façade trim (string courses, cornice, door surrounds), base course, entrance canopy
    l52-window-{part}-{axis}       a two-block window, a glass pane in a white aluminium frame; JSON shape
    l52-slab-{kind}                floor finish above, suspended ceiling below; l52-roof; l52-light-{kind}-{state} troffer in the same
    l52-turf-{kind}, l52-court-{kind}, l52-paving-{kind}   outdoor surfaces
    l52-chainlink-{part}-{axis}    a chain-link fence panel, two blocks high; JSON shape
    l52-plaque-{half}-{a}-{b}-{side}   half of a four-digit door plate hung on the wall behind it; JSON shape
    l52-fountain-{side}            a wall-mounted drinking fountain that dispenses; JSON shape
    l52-tile, l52-gymfloor, l52-desk, l52-chalkboard   from the first prototype, unchanged
    textures/environment/l52-sun.png   the billboard sun
    sounds/ambient/52/bell.ogg     a school bell ringing somewhere far down the halls

Textures are 32 px a block (block/52/), shapes 16 units (block/52/); every shape names its texture keys one by one
and its blocktype names no `all` texture for a json shape, so nothing overrides them. Files this script no longer
writes are removed from the three asset folders. Run from the repo root:  python tools/gen_52.py
"""
import json
import math
import os
import random
import re

import numpy as np
from PIL import Image

import gen_52_tex as T
from modelkit import box
from oggutil import write_ogg
from gen_entity_sounds import RATE, band, reverb, seconds

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "52")
SHAPES = os.path.join(ASSETS, "shapes", "block", "52")
BLOCKS = os.path.join(ASSETS, "blocktypes", "52")
SUN = os.path.join(ASSETS, "textures", "environment", "l52-sun.png")
S = 32
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
PALETTES = ["beige", "white", "blue", "grey"]
KINDS = ["hall", "room", "carpetblue", "carpetred", "carpetgreen", "carpetgrey", "lino", "concrete", "wood"]
FLOOR = {"hall": "tile-hall", "room": "tile-room", "carpetblue": "floor-carpetblue", "carpetred": "floor-carpetred",
         "carpetgreen": "floor-carpetgreen", "carpetgrey": "floor-carpetgrey", "lino": "floor-lino",
         "concrete": "floor-concrete", "wood": "gymfloor-plain"}
WRITTEN = {"blocktypes": set(), "shapes": set(), "textures": set()}

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    folder = os.path.dirname(os.path.abspath(path))
    if folder == os.path.abspath(BLOCKS):
        WRITTEN["blocktypes"].add(os.path.basename(path))
    elif folder == os.path.abspath(SHAPES):
        WRITTEN["shapes"].add(os.path.basename(path))


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
    WRITTEN["textures"].add(name + ".png")


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



def new_textures():
    for pi, pal in enumerate(PALETTES):
        for i, part in enumerate(("base", "dado", "upper")):
            save(T.wall(pal, part, 5300 + pi * 10 + i), f"wall-{pal}-{part}")
        for i, part in enumerate(("lower", "upper")):
            save(T.locker(pal, part, 5340 + pi * 10 + i), f"locker-{pal}-{part}")
    for i, kind in enumerate(("white", "beige", "brick", "grey", "blue")):
        save(T.facade(kind, 5400 + i * 10), f"facade-{kind}")
    save(T.coping("top", 5460), "coping-top")
    save(T.coping("side", 5461), "coping-side")
    for i, kind in enumerate(("light", "grey", "stone")):
        save(T.band(kind, 5700 + i), "band-" + kind)
    save(T.plinth(5710), "plinth")
    save(T.canopy_fascia(5720), "canopy-fascia")
    save(T.canopy_soffit(5721), "canopy-soffit")
    save(T.barrier("side", 5470), "barrier")
    save(T.barrier("top", 5471), "barrier-top")
    save(T.slab_concrete(5480), "slab-concrete")
    for i, kind in enumerate(("carpetblue", "carpetred", "carpetgreen", "carpetgrey")):
        save(T.carpet_tiles(kind, 5500 + i * 10), "floor-" + kind)
    save(T.lino(5550), "floor-lino")
    save(T.sealed_concrete(5560), "floor-concrete")
    save(T.ceiling_tile(5570), "ceiling-tile")
    save(T.troffer(True, 5580), "ceiling-troffer-on")
    save(T.troffer(False, 5580), "ceiling-troffer-off")
    save(T.roof(5590), "roof-membrane")
    save(T.turf_top(False, 5600), "turf-plain")
    save(T.turf_top(True, 5600), "turf-worn")
    save(T.turf_side(5610), "turf-side")
    save(T.court(None, 5620), "court-plain")
    save(T.court("ns", 5620), "court-linens")
    save(T.court("we", 5620), "court-linewe")
    save(T.paving("a", 5630), "paving-a")
    save(T.paving("b", 5640), "paving-b")
    save(T.window_glass(5650), "window-glass")
    save(T.window_frame(5651), "window-frame")
    save(T.chainlink_mesh(5660), "chainlink-mesh")
    save(T.chainlink_rail(5661), "chainlink-rail")
    save(T.steel(5670), "fountain-steel")
    save(T.fountain_basin(5671), "fountain-basin")
    save(T.fountain_chrome(5672), "fountain-chrome")
    save(noise(canvas((36, 38, 40)), 5673, 3), "fountain-dark")
    save(T.plaque_plate(5680), "plaque-plate")
    for d in "0123456789":
        save(T.digit(d, 5690), "digit-" + d)
    os.makedirs(os.path.dirname(SUN), exist_ok=True)
    T.sun().save(SUN)


# ======================================================================== Shapes

def shape(name, elements, overrides=None):
    keys = sorted({face["texture"][1:] for e in elements for face in e["faces"].values()})
    overrides = overrides or {}
    data = {"textureWidth": 16, "textureHeight": 16,
            "textures": {k: "backrooms:block/52/" + overrides.get(k, k) for k in keys}, "elements": elements}
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


# ---------------------------------------------------------------------- the new shapes

FULL = (0, 0, 16, 16)


def window_shape(part):
    """A window pane in the plane x = 8 (axis ns) in a white aluminium frame: lower has the sill, bottom rail and both
    jambs; upper has the head rail and both jambs. The glass is two faces only, so it costs nothing when seen edge-on."""
    f, g = "window-frame", "window-glass"
    if part == "lower":
        els = [box("Sill", (5.2, 0, 0), (10.8, 1.2, 16), f),
               box("JambN", (6.8, 1.2, 0), (9.2, 16, 1.5), f),
               box("JambS", (6.8, 1.2, 14.5), (9.2, 16, 16), f),
               box("Rail", (6.8, 1.2, 1.5), (9.2, 2.5, 14.5), f, faces=("up", "east", "west")),
               box("Glass", (7.5, 2.5, 1.5), (8.5, 16, 14.5), g, faces=("east", "west"), uv=FULL)]
    else:
        els = [box("JambN", (6.8, 0, 0), (9.2, 16, 1.5), f),
               box("JambS", (6.8, 0, 14.5), (9.2, 16, 16), f),
               box("Head", (6.8, 13.5, 1.5), (9.2, 16, 14.5), f, faces=("up", "down", "east", "west")),
               box("Glass", (7.5, 0, 1.5), (8.5, 13.5, 14.5), g, faces=("east", "west"), uv=FULL)]
    return shape(f"l52-window-{part}", els)


def chainlink_shape(part):
    if part == "lower":
        els = [box("Mesh", (7.8, 0, 0), (8.2, 16, 16), "chainlink-mesh", faces=("east", "west"), uv=FULL)]
    else:
        els = [box("Mesh", (7.8, 0, 0), (8.2, 14.4, 16), "chainlink-mesh", faces=("east", "west"), uv=FULL),
               box("Rail", (7.2, 14.4, 0), (8.8, 16, 16), "chainlink-rail", uv=FULL)]
    return shape(f"l52-chainlink-{part}", els)


def plaque_shape(half):
    """Half of a 10 x 4 unit door plate, modelled facing north against the wall to its south. Seen from in front the
    left is +X, so the lo half (the plate's left) sits against the block's x = 0 edge and the hi half against x = 16,
    and in each the first digit (d1) is the one further from the seam."""
    if half == "lo":
        plate = box("Plate", (0, 9, 15.4), (5, 13, 16), "plaque-plate", faces=("north", "up", "down", "east"), uv=FULL)
        x1a, x1b, x2a, x2b = 2.35, 4.7, 0, 2.35
    else:
        plate = box("Plate", (11, 9, 15.4), (16, 13, 16), "plaque-plate", faces=("north", "up", "down", "west"), uv=FULL)
        x1a, x1b, x2a, x2b = 13.65, 16, 11.3, 13.65
    els = [plate,
           box("Digit1", (x1a, 9.3, 15.3), (x1b, 12.7, 15.4), "d1", faces=("north",), uv=FULL),
           box("Digit2", (x2a, 9.3, 15.3), (x2b, 12.7, 15.4), "d2", faces=("north",), uv=FULL)]
    return shape(f"l52-plaque-{half}", els, {"d1": "digit-0", "d2": "digit-0"})


def fountain_shape():
    """A wall-hung stainless drinking fountain, facing north, its back plate against the wall to the south."""
    st, ba, ch, dk = "fountain-steel", "fountain-basin", "fountain-chrome", "fountain-dark"
    els = [box("BackPlate", (3.5, 8.5, 15.4), (12.5, 14.5, 16), st, faces=("north", "up", "down", "east", "west")),
           box("Housing", (4.5, 5, 9.5), (11.5, 8.5, 15.4), st),
           box("BasinFloor", (4, 8.5, 6.5), (12, 9.2, 15.4), st, faces=("north", "east", "west", "down")),
           box("BasinFront", (4, 9.2, 6.5), (12, 10.8, 7.2), st),
           box("BasinL", (4, 9.2, 7.2), (4.7, 10.8, 15.4), st, faces=("up", "east", "west")),
           box("BasinR", (11.3, 9.2, 7.2), (12, 10.8, 15.4), st, faces=("up", "east", "west")),
           box("BasinIn", (4.7, 9.2, 7.2), (11.3, 9.3, 15.4), ba, faces=("up",)),
           box("BasinInFront", (4.7, 9.3, 7.2), (11.3, 10.8, 7.25), ba, faces=("south",)),
           box("Drain", (7.2, 9.3, 10.5), (8.8, 9.4, 12.1), dk, faces=("up",)),
           box("SpoutStem", (7.4, 9.3, 13.4), (8.6, 11.9, 14.6), ch),
           box("SpoutArm", (7.4, 11.0, 10.8), (8.6, 11.9, 13.4), ch, faces=("north", "up", "down", "east", "west")),
           box("SpoutTip", (7.7, 10.6, 10.8), (8.3, 11.0, 11.6), dk, faces=("north", "down", "east", "west")),
           box("Button", (9.9, 11.3, 14.8), (11.5, 12.9, 15.4), ch, faces=("north", "up", "down", "east", "west"))]
    return shape("l52-fountain", els)


# ======================================================================== Block types

def cuboid(b, angle=0):
    c = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if angle:
        c["rotateY"] = angle
    return c


def tex(name):
    return {"base": "block/52/" + name}


def cube_block(code, groups, textures_by_type, comment, material="Stone", sounds=STONE, extra=None, resistance=6):
    data = {"code": code}
    if groups:
        data["variantgroups"] = groups
    data.update({"texturesByType": textures_by_type,
                 "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
                 "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": resistance, "drops": [], "sounds": sounds})
    data.update(extra or {})
    for k in [k for k, v in data.items() if v is None and k != "collisionbox"]:
        del data[k]
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def faces(all_=None, up=None, down=None, sides=None):
    """A texture set for a cube: the named textures per face (sides covers the four horizontals)."""
    out = {}
    if all_:
        out["all"] = tex(all_)
    if sides:
        for s in SIDES:
            out[s] = tex(sides)
    if up:
        out["up"] = tex(up)
    if down:
        out["down"] = tex(down)
    return out


def group(code, states):
    return {"code": code, "states": list(states)}


def json_block(code, groups, shape_by_type, comment, material, sounds, collision=None, selection=None, creative=("*",), extra=None, resistance=2):
    data = {"code": code, "variantgroups": groups, "shapeByType": shape_by_type,
            "creativeinventory": {"general": list(creative), "backrooms": list(creative)},
            "blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": resistance, "sounds": sounds}
    if collision is not None:
        data["collisionboxByType"] = collision
    if selection is not None:
        data["selectionboxByType"] = selection
    data["drops"] = []
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def new_blocktypes():
    parts3 = ["base", "dado", "upper"]
    # Walls
    cube_block("l52-wall", [group("palette", PALETTES), group("part", parts3)],
               {f"l52-wall-{p}-{k}": faces(all_=f"wall-{p}-{k}") for p in PALETTES for k in parts3},
               "Level 52: interior painted wall (palette beige/white/blue/grey; base: lower paint with a dark skirting; dado: lower paint with a rail "
               "line near the top; upper: upper paint)")
    # Lockers
    lockers = {}
    for p in PALETTES:
        for part in ("lower", "upper"):
            back = f"wall-{p}-base" if part == "lower" else f"wall-{p}-dado"
            for side in SIDES:
                f = faces(sides=back, up=f"wall-{p}-upper", down=f"wall-{p}-upper")
                f[side] = tex(f"locker-{p}-{part}")
                lockers[f"l52-locker-{p}-{part}-{side}"] = f
    cube_block("l52-locker", [group("palette", PALETTES), group("part", ["lower", "upper"]), group("side", SIDES)], lockers,
               "Level 52: a bank of three steel lockers on the side face of a wall block (lower: latches, louvres, the kick base; upper: vents and "
               "number plates); its other faces are the palette's wall paint", material="Metal", sounds=METAL, resistance=4)
    # The prototype's palette-less lockers, kept by their old codes for Level 31, which borrows them (the beige palette's)
    for part in ("lower", "upper"):
        back = "wall-beige-base" if part == "lower" else "wall-beige-dado"
        legacy = {}
        for side in SIDES:
            f = faces(sides=back, up="wall-beige-upper", down="wall-beige-upper")
            f[side] = tex(f"locker-beige-{part}")
            legacy[f"l52-locker-{part}-{side}"] = f
        cube_block(f"l52-locker-{part}", [group("side", SIDES)], legacy,
                   "Level 52: the prototype's lockers under their old codes (Level 31 uses them): the beige palette's", material="Metal", sounds=METAL,
                   resistance=4)
    # Exterior
    fac = ["white", "beige", "brick", "grey", "blue"]
    cube_block("l52-facade", [group("palette", fac)], {f"l52-facade-{k}": faces(all_=f"facade-{k}") for k in fac},
               "Level 52: exterior wall (white concrete panels, beige render, pale brick, grey precast, blue-painted concrete)")
    cube_block("l52-coping", [], {"*": faces(sides="coping-side", up="coping-top", down="slab-concrete")},
               "Level 52: concrete coping cap for parapet tops (cap on top, drip line on the sides)")
    bands = ["light", "grey", "stone"]
    cube_block("l52-band", [group("kind", bands)], {f"l52-band-{k}": faces(sides=f"band-{k}", up="coping-top", down="slab-concrete") for k in bands},
               "Level 52: a precast band on a façade (string course at a floor line, cornice under the parapet, an entrance's surround and lintel): "
               "off-white, mid grey or pale sandstone")
    cube_block("l52-plinth", [], {"*": faces(sides="plinth", up="coping-top", down="slab-concrete")},
               "Level 52: the dark honed stone base course along the foot of an outside wall")
    cube_block("l52-canopy", [], {"*": faces(sides="canopy-fascia", up="roof-membrane", down="canopy-soffit")},
               "Level 52: an entrance canopy, a flat cantilevered slab over a doorway (charcoal fascia, pale soffit with downlights)", material="Metal",
               sounds=METAL)
    cube_block("l52-barrier", [], {"*": faces(sides="barrier", up="barrier-top", down="slab-concrete")},
               "Level 52: the low weathered concrete wall a fence stands on, a chamfered cap line near its top")
    # Slabs and lights
    cube_block("l52-slab", [group("kind", KINDS)],
               {f"l52-slab-{k}": faces(sides="slab-concrete", up=FLOOR[k], down="ceiling-tile") for k in KINDS},
               "Level 52: a storey's floor finish on top (hall/room vinyl, four carpets, lino, sealed concrete, maple) and the storey below's "
               "suspended mineral-fibre ceiling underneath")
    cube_block("l52-roof", [], {"*": faces(sides="slab-concrete", up="roof-membrane", down="ceiling-tile")},
               "Level 52: a flat roof (grey membrane, gravel) over the ceiling tile of the storey below")
    states = ["on", "lit", "off", "flicker"]
    lights = {f"l52-light-{k}-{s}": faces(sides="slab-concrete", up=FLOOR[k], down="ceiling-troffer-off" if s == "off" else "ceiling-troffer-on")
              for k in KINDS for s in states}
    hum = dict(GLASS, ambient="backrooms:ambient/hum", ambientBlockCount=140)
    cube_block("l52-light", [group("kind", KINDS), group("state", states)], lights,
               "Level 52: a slab with a fluorescent troffer in its ceiling face (on: lit and emits; lit: lit, emits nothing; off: dead; flicker: fails "
               "now and then). Conventions as fluorescentlight",
               material="Glass", sounds=GLASS, resistance=0.8, extra={
                   "lightAbsorption": 0,
                   "lightHsvByType": {"*-on": [10, 2, 21]},
                   "vertexFlagsByType": {"*-on": {"glowLevel": 160}, "*-lit": {"glowLevel": 160}, "*-flicker": {"glowLevel": 160}},
                   "entityClassByType": {"*-flicker": "BackroomsFlicker"},
                   "attributesByType": {f"l52-light-{k}-flicker": {"offBlock": f"backrooms:l52-light-{k}-off"} for k in KINDS},
                   "drops": None,
                   "dropsByType": dict(
                       {f"l52-light-{k}-off": [{"type": "item", "code": "glassshard", "quantity": {"avg": 1.5, "var": 0.5}},
                                               {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.12, "var": 0}},
                                               {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0}}] for k in KINDS},
                       **{f"l52-light-{k}-flicker": [{"type": "block", "code": f"l52-light-{k}-off"}] for k in KINDS},
                       **{f"l52-light-{k}-lit": [{"type": "block", "code": f"l52-light-{k}-on"}] for k in KINDS}),
                   "soundsByType": {"*-on": hum, "*-lit": hum, "*": GLASS}})
    # Outdoor surfaces
    cube_block("l52-turf", [group("kind", ["plain", "worn"])],
               {f"l52-turf-{k}": faces(sides="turf-side", up=f"turf-{k}", down="slab-concrete") for k in ("plain", "worn")},
               "Level 52: artificial grass over rubber crumb (plain; worn: paler flattened patches)",
               sounds={"walk": "game:walk/grass", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}, resistance=3)
    cube_block("l52-court", [group("kind", ["plain", "linens", "linewe"])],
               {f"l52-court-{k}": faces(sides="slab-concrete", up=f"court-{k}", down="slab-concrete") for k in ("plain", "linens", "linewe")},
               "Level 52: an outdoor sports court's terracotta acrylic surface, plain or with a white line north-south (linens) or west-east (linewe)")
    cube_block("l52-paving", [group("kind", ["a", "b"])],
               {f"l52-paving-{k}": faces(sides="slab-concrete", up=f"paving-{k}", down="slab-concrete") for k in ("a", "b")},
               "Level 52: campus sidewalk, pale grey concrete slabs (b: with a crack and a stain)")

    # Windows
    win = {p: window_shape(p) for p in ("lower", "upper")}
    sb = {}
    shape_by = {}
    for part in ("lower", "upper"):
        for axis, ang in (("ns", 0), ("we", 90)):
            d = {"base": win[part]}
            if ang:
                d["rotateY"] = ang
            shape_by[f"l52-window-{part}-{axis}"] = d
    thick = {"*-ns": cuboid((0.375, 0, 0, 0.625, 1, 1)), "*-we": cuboid((0, 0, 0.375, 1, 1, 0.625))}
    json_block("l52-window", [group("part", ["lower", "upper"]), group("axis", ["ns", "we"])], shape_by,
               "Level 52: a window two blocks high, a thin glass pane in a white aluminium frame (axis ns: the pane lies in x = 8; we: in z = 8); "
               "lower has the sill, upper the head", "Glass", GLASS, thick, thick, resistance=1.5,
               extra={"renderpass": "Transparent"})

    # Chain-link
    cl = {p: chainlink_shape(p) for p in ("lower", "upper")}
    shape_by = {}
    for part in ("lower", "upper"):
        for axis, ang in (("ns", 0), ("we", 90)):
            d = {"base": cl[part]}
            if ang:
                d["rotateY"] = ang
            shape_by[f"l52-chainlink-{part}-{axis}"] = d
    thin = {"*-ns": cuboid((0.4375, 0, 0, 0.5625, 1, 1)), "*-we": cuboid((0, 0, 0.4375, 1, 1, 0.5625))}
    json_block("l52-chainlink", [group("part", ["lower", "upper"]), group("axis", ["ns", "we"])], shape_by,
               "Level 52: a chain-link fence panel two blocks high, galvanised diamond mesh cut out of the block's middle plane (axis ns: x = 8; "
               "we: z = 8); upper carries the top rail tube", "Metal", METAL, thin, thin, resistance=3,
               extra={"renderpass": "OpaqueNoCull"})

    # Plaques
    pl = {h: plaque_shape(h) for h in ("lo", "hi")}
    shape_by, sel = {}, {}
    for half, (xa, xb) in (("lo", (0, 5)), ("hi", (11, 16))):
        for s in SIDES:
            shape_by[f"*-{half}-*-{s}"] = {"base": pl[half], "rotateY": ROTATE[s]}
            sel[f"*-{half}-*-{s}"] = cuboid((xa / 16, 9 / 16, 15.3 / 16, xb / 16, 13 / 16, 1), ROTATE[s])
    digits = "0123456789"
    json_block("l52-plaque", [group("half", ["lo", "hi"]), group("a", digits), group("b", digits), group("side", SIDES)], shape_by,
               "Level 52: half of a four-digit door-number plate (10 x 4 units, charcoal with off-white digits) hung on the wall behind the block; "
               "lo is the plate's left half as seen from in front (digits a b), hi the right half; side is the way it faces",
               "Metal", METAL, None, sel, creative=("*-lo-0-0-north", "*-hi-0-0-north"), resistance=0.5,
               extra={"textures": {"d1": tex("digit-{a}"), "d2": tex("digit-{b}")}, "collisionbox": None})

    # Fountain
    fs = fountain_shape()
    box_ = (0.2, 0.3, 0.4, 0.8, 0.92, 1)
    fshape = {f"*-{s}": {"base": fs, "rotateY": ROTATE[s]} for s in SIDES}
    json_block("l52-fountain", [group("side", SIDES)], fshape,
               "Level 52: a wall-mounted stainless steel drinking fountain hung on the wall behind it (waist-high bowl, push button, drain); a "
               "working dispenser like the water cooler",
               "Metal", METAL, {f"*-{s}": cuboid(box_, ROTATE[s]) for s in SIDES}, {f"*-{s}": cuboid(box_, ROTATE[s]) for s in SIDES},
               creative=("*-north",), resistance=4,
               extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser", "attributes": {"liquidSource": True}})


def old_blocktypes():
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


def expected_codes():
    """Every block code and variant the level's generator looks up, written out on its own (not derived from the
    blocktype files), to check what the blocktypes define."""
    codes = set()
    digits = "0123456789"
    for k in ("hall", "room"):
        codes.add(f"l52-tile-{k}")
    for k in ("plain", "linens", "linewe"):
        codes.add(f"l52-gymfloor-{k}")
    for s in SIDES:
        codes.add(f"l52-desk-{s}")
        codes.add(f"l52-fountain-{s}")
        for h in ("lower", "upper"):
            for e in "lmr":
                codes.add(f"l52-chalkboard-{h}-{e}-{s}")
        for p in PALETTES:
            for part in ("lower", "upper"):
                codes.add(f"l52-locker-{p}-{part}-{s}")
        for part in ("lower", "upper"):
            codes.add(f"l52-locker-{part}-{s}")
        for h in ("lo", "hi"):
            for a in digits:
                for b in digits:
                    codes.add(f"l52-plaque-{h}-{a}-{b}-{s}")
    for p in PALETTES:
        for part in ("base", "dado", "upper"):
            codes.add(f"l52-wall-{p}-{part}")
    for p in ("white", "beige", "brick", "grey", "blue"):
        codes.add(f"l52-facade-{p}")
    codes |= {"l52-coping", "l52-barrier", "l52-roof", "l52-plinth", "l52-canopy"}
    for k in ("light", "grey", "stone"):
        codes.add(f"l52-band-{k}")
    for part in ("lower", "upper"):
        for axis in ("ns", "we"):
            codes.add(f"l52-window-{part}-{axis}")
            codes.add(f"l52-chainlink-{part}-{axis}")
    for k in KINDS:
        codes.add(f"l52-slab-{k}")
        for st in ("on", "lit", "off", "flicker"):
            codes.add(f"l52-light-{k}-{st}")
    for k in ("plain", "worn"):
        codes.add(f"l52-turf-{k}")
    for k in ("plain", "linens", "linewe"):
        codes.add(f"l52-court-{k}")
    for k in ("a", "b"):
        codes.add(f"l52-paving-{k}")
    return codes


def strip_comment(text):
    return "\n".join(l for l in text.split("\n") if not l.lstrip().startswith("//"))


def expand(data):
    """The codes a blocktype defines (the product of its variant groups)."""
    codes = [data["code"]]
    for g in data.get("variantgroups", []):
        codes = [c + "-" + s for c in codes for s in g["states"]]
    return codes


def remove_stale():
    for folder, ext, key in ((BLOCKS, ".json", "blocktypes"), (SHAPES, ".json", "shapes"), (TEX, ".png", "textures")):
        for name in sorted(os.listdir(folder)):
            if name.endswith(ext) and name not in WRITTEN[key]:
                os.remove(os.path.join(folder, name))
                print("removed stale", os.path.relpath(os.path.join(folder, name), ROOT))


def check():
    problems = []
    defined = []
    refs = set()
    for name in sorted(os.listdir(BLOCKS)):
        with open(os.path.join(BLOCKS, name), encoding="utf-8") as f:
            data = json.loads(strip_comment(f.read()))
        defined += expand(data)
        text = json.dumps(data)
        for m in re.finditer(r'"(?:backrooms:)?block/52/([^"]+)"', text):
            refs.add(m.group(1))
    for name in sorted(os.listdir(SHAPES)):
        with open(os.path.join(SHAPES, name), encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data["textures"].items():
            refs.add(v.split("block/52/")[1])
        used = {face["texture"][1:] for e in data["elements"] for face in e["faces"].values()}
        if used != set(data["textures"]):
            problems.append(f"{name}: texture keys {used ^ set(data['textures'])}")
    for ref in sorted(refs):
        if "{" in ref:  # a variant placeholder: digit-{a}, digit-{b}
            for d in "0123456789":
                if not os.path.exists(os.path.join(TEX, ref.split("{")[0] + d + ".png")):
                    problems.append("missing texture " + ref)
            continue
        if os.path.exists(os.path.join(SHAPES, ref + ".json")):
            continue  # a shape a blocktype names
        if not os.path.exists(os.path.join(TEX, ref + ".png")):
            problems.append("missing texture " + ref)
    seen = set()
    for c in defined:
        if c in seen:
            problems.append("duplicate code " + c)
        seen.add(c)
    want = expected_codes()
    for c in sorted(want - seen):
        problems.append("missing code " + c)
    extra = sorted(seen - want)
    if extra:
        print("codes beyond the contract:", extra)
    if not os.path.exists(SUN):
        problems.append("missing sun")
    for p in problems:
        print("PROBLEM:", p)
    print(f"check: {len(seen)} codes defined, {len(want)} expected, {len(refs)} texture references, {len(problems)} problems")
    return not problems


def main():
    floor_textures()
    prop_textures()
    new_textures()
    old_blocktypes()
    new_blocktypes()
    bell()
    remove_stale()
    if not check():
        raise SystemExit(1)
    print("Level 52: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
