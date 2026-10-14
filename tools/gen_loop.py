"""Assets for the survival loop (docs/design/survival-loop-plan.md): what has been picked over, what tells you where to go,
and what a home needs. Run on its own: python tools/gen_loop.py

- The sealed supply box's shape, torn supply boxes and prised-open crates: the three in four that wanderers went
  through before you.
- The anchor: the messages when a temporal gear will not take hold outside Level 0.
- Finding the way: wanderers' notes, and the names of the waypoints the Backrooms marks on your map.
- Dens: the Deathmoth hive that marks one.
- Needs: the pry bar that opens locked rooms, and seed packets for a farm at home.
"""
import json
import os
import random
import re

from PIL import Image, ImageDraw

from detail_kit import ground_storable
import matlib as M
from gen_textures import box, cardboard, crate, hexrgb, noise_fill, save, shade, sprite, S

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TAB, NL = "\t", "\n"

LANG = {}


# What each paper is about, in its name: notes of one kind stack (16), and this is how to tell the stacks apart
NOTE_KIND_NAMES = {"door": "a way through", "way": "a way out", "cache": "supplies", "refuge": "a refuge"}


def write_json(data, *rel, comment=None):
    path = os.path.join(ASSETS, *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False) + NL
    if comment:
        text = "// " + comment + NL + text
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)


def drops(*items):
    """(code, average, variance); codes without a domain are ours."""
    return [{"type": "item", "code": code, "quantity": {"avg": avg, "var": var}} for code, avg, var in items]


# ======================= Picked over =======================

def _proj(face, frm, to, top):
    """The UV of a face as the supply box always mapped its textures: projected straight onto the face (u along x or
    z, v down from the box's top `top`), so a bevel strip shows the same pixels as the face beside it."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    if face in ("north", "south"):
        return [x1, top - y2, x2, top - y1]
    if face in ("east", "west"):
        return [z1, top - y2, z2, top - y1]
    return [x1, z1, x2, z2]


def _el(name, frm, to, tex, top, faces=None, **extra):
    """One element with a texture key per face (`tex`: {face: key}) and projected UVs."""
    out = {}
    for f, k in tex.items():
        if faces and f not in faces:
            continue
        out[f] = {"texture": "#" + k, "uv": [round(v, 4) for v in _proj(f, frm, to, top)]}
    el = {"name": name, "from": list(frm), "to": list(to), "faces": out}
    el.update(extra)
    return el


def supply_box_shape():
    """The sealed supply box (graphics pass B3): the same 12 x 10 x 12 carton, now with its own faces
    (gen_textures.supply_box_faces: worn edges cut to these UVs, the tape over the top and down the north and south
    sides, the east and west sides plain). A version with bevelled edges (three crossed boxes) read in game as a lid
    sitting on a box, so it stays one box."""
    top = 10
    tex = {"north": "side", "south": "side", "east": "end", "west": "end", "up": "top", "down": "end"}
    els = [_el("Box", [2, 0, 2], [14, top, 14], tex, top)]
    els[0]["faces"]["up"]["uv"] = [2, 2, 14, 14]
    els[0]["faces"]["down"]["uv"] = [2, 2, 14, 14]
    write_json({"textureWidth": 16, "textureHeight": 16,
                "textures": {"side": "backrooms:block/supplybox-box-side", "end": "backrooms:block/supplybox-box-end",
                             "top": "backrooms:block/supplybox-box-top"},
                "elements": els}, "shapes", "block", "supplybox.json")


def torn_box_textures():
    """The torn box (graphics pass B3): the same cardboard, the tape slit and the walls' top edge torn ragged with the
    corrugation showing in it; a dark, empty inside; and the contents left behind (packing straw, a crackers wrapper)
    as their own textures for the small pieces of geometry that lie in it."""
    img = box(False)
    rng = random.Random(7101)
    px = img.load()
    for y in range(0, 8):  # the tape slit down its middle, its cut edges curling up
        px[16, y] = M.rgba(M.lift(px[16, y], -40))
        M.touch(img, 15, y, 0.1)
        M.touch(img, 17, y, 0.06)
    for x in range(S):  # the torn top edge (its teeth are geometry): pale, frayed fibre along the tear
        M.touch(img, x, 0, 0.12 + rng.uniform(0, 0.06))
        if rng.random() < 0.4:
            M.touch(img, x, 1, 0.06)
    for k in range(7):  # a crease where it was trodden on: a groove lit on its lower side
        x, y = 4 + k * 5 // 7, 14 + k
        M.touch(img, x, y, -0.14)
        M.touch(img, x + 1, y, 0.08)
    save(img, "block/supplybox-torn-side.png")

    # Inside: the cardboard seen from within, dark, with the flutes' lines and a water ring; the walls' shadow round it
    img = cardboard(7102, base=(112, 84, 54))
    M.ao_border(img, 4, 0.26)
    M.stain(img, 7104, radius=6, color=(52, 38, 24), strength=0.3, at=(19, 12))
    save(img, "block/supplybox-torn-inside.png")

    # The flaps: plain cardboard
    save(box(True), "block/supplybox-flap.png")

    # Packing straw: dry stalks along the texture, lit on top
    img = M.noise_hv((196, 170, 104), 5, 7105, mottle=6)
    for y in range(0, S, 2):
        for x in range(S):
            M.touch(img, x, y, 0.08)
            M.touch(img, x, y + 1, -0.1)
    save(img, "block/supplybox-straw.png")

    # A crackers wrapper, foil-backed red film: a band of print, crinkles catching the light
    img = M.noise_hv((176, 50, 40), 4, 7106, mottle=8)
    p = img.load()
    for y in range(12, 20):
        for x in range(S):
            p[x, y] = M.rgba(M.lift((232, 196, 120), rng.uniform(-6, 6)))
    M.scratches(img, n=10, seed=7107, length=(3, 7), light=0.3)
    save(img, "block/supplybox-wrapper.png")


def torn_box_shape():
    """A box with its lid torn back (B3): lower walls whose torn top is a row of ragged teeth (small boxes of
    different heights, not paint), an open top, two flaps lolling over the sides, and what was left in it as geometry:
    a few straws of packing, a crumpled wrapper, a wad of paper."""
    side, inside, flap = "#side", "#inside", "#flap"
    def face(tex, uv):
        return {"texture": tex, "uv": uv}
    H = 8  # the walls' height below the teeth
    elements = [
        {"name": "Floor", "from": [2, 0, 2], "to": [14, 1, 14],
         "faces": {"up": face(inside, [2, 2, 14, 14]), "down": face(side, [2, 2, 14, 14])}},
        {"name": "WallN", "from": [2, 0, 2], "to": [14, H, 3],
         "faces": {"north": face(side, [2, 1, 14, 1 + H]), "south": face(inside, [2, 1, 14, 1 + H]), "up": face(side, [2, 0, 14, 1]),
                   "east": face(side, [0, 1, 1, 1 + H]), "west": face(side, [0, 1, 1, 1 + H])}},
        {"name": "WallS", "from": [2, 0, 13], "to": [14, H, 14],
         "faces": {"south": face(side, [2, 1, 14, 1 + H]), "north": face(inside, [2, 1, 14, 1 + H]), "up": face(side, [2, 0, 14, 1]),
                   "east": face(side, [0, 1, 1, 1 + H]), "west": face(side, [0, 1, 1, 1 + H])}},
        {"name": "WallW", "from": [2, 0, 3], "to": [3, H, 13],
         "faces": {"west": face(side, [3, 1, 13, 1 + H]), "east": face(inside, [3, 1, 13, 1 + H]), "up": face(side, [3, 0, 13, 1])}},
        {"name": "WallE", "from": [13, 0, 3], "to": [14, H, 13],
         "faces": {"east": face(side, [3, 1, 13, 1 + H]), "west": face(inside, [3, 1, 13, 1 + H]), "up": face(side, [3, 0, 13, 1])}},
        # Flaps hinged on the east and west rims, folded back down over the outside
        {"name": "FlapE", "from": [14, H - 0.5, 2], "to": [19, H, 14], "rotationOrigin": [14, H, 8], "rotationZ": -60,
         "faces": {"up": face(flap, [2, 2, 7, 14]), "down": face(inside, [2, 2, 7, 14]), "east": face(side, [0, 0, 12, 1])}},
        {"name": "FlapW", "from": [-3, H - 0.5, 2], "to": [2, H, 14], "rotationOrigin": [2, H, 8], "rotationZ": 75,
         "faces": {"up": face(flap, [9, 2, 14, 14]), "down": face(inside, [9, 2, 14, 14]), "west": face(side, [0, 0, 12, 1])}},
    ]
    # The torn rim: teeth along the north and south walls (the flaps' walls keep a straight fold)
    rng = random.Random(7121)
    for wall, z1, z2, out, inn in (("N", 2, 3, "north", "south"), ("S", 13, 14, "south", "north")):
        x = 2.0
        k = 0
        while x < 14:
            w = min(14 - x, rng.choice((1.0, 1.5, 2.0, 2.5)))
            h = rng.choice((0.5, 0.5, 1.0))
            if rng.random() < 0.75:
                elements.append({"name": f"Tooth{wall}{k}", "from": [x, H, z1], "to": [x + w, H + h, z2],
                                 "faces": {out: face(side, [x, 0, x + w, h]), inn: face(inside, [x, 0, x + w, h]),
                                           "up": face(side, [x, 0, x + w, 1]), "east": face(side, [0, 0, 1, h]),
                                           "west": face(side, [0, 0, 1, h])}})
                k += 1
            x += w
    # What was left in it: lying on the floor (y 1), clear of the walls
    straw = {f: face("#straw", [0, 0, 8, 0.5]) for f in ("north", "south", "east", "west", "up")}
    for i, (x, z, ln, yaw) in enumerate(((3.5, 9.5, 6, 25), (4.5, 4, 5, -40), (8.5, 11, 4.5, 70), (4, 6.5, 5, 5),
                                         (7, 8, 5.5, -75), (5.5, 11.5, 4, 110))):
        elements.append({"name": f"Straw{i}", "from": [x, 1, z], "to": [x + ln, 1.5, z + 0.5],
                         "rotationOrigin": [x + ln / 2, 1, z + 0.25], "rotationY": yaw, "faces": straw})
    elements.append({"name": "Wrapper", "from": [8, 1, 5], "to": [12, 1.5, 8], "rotationOrigin": [10, 1, 6.5],
                     "rotationY": -20, "rotationX": 8,
                     "faces": {f: face("#wrapper", uv) for f, uv in (("up", [2, 4, 10, 10]), ("north", [2, 4, 10, 5]),
                                                                     ("south", [2, 4, 10, 5]), ("east", [2, 4, 8, 5]),
                                                                     ("west", [2, 4, 8, 5]))}})
    elements.append({"name": "PaperWad", "from": [9.5, 1, 9], "to": [11.5, 2.5, 11], "rotationOrigin": [10.5, 1, 10],
                     "rotationY": 30,
                     "faces": {f: face("#flap", [0, 0, 2, 1.5 if f not in ("up",) else 2]) for f in ("north", "south", "east", "west", "up")}})
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"side": "backrooms:block/supplybox-torn-side", "inside": "backrooms:block/supplybox-torn-inside",
                          "flap": "backrooms:block/supplybox-flap", "straw": "backrooms:block/supplybox-straw",
                          "wrapper": "backrooms:block/supplybox-wrapper"},
             "elements": elements}
    write_json(shape, "shapes", "block", "supplybox-torn.json")


def torn_box_block():
    write_json({
        "code": "supplybox-torn",
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood",
        "drawtype": "json",
        "shape": {"base": "block/supplybox-torn"},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "collisionbox": {"x1": 0.125, "y1": 0, "z1": 0.125, "x2": 0.875, "y2": 0.5625, "z2": 0.875},
        "selectionbox": {"x1": 0.125, "y1": 0, "z1": 0.125, "x2": 0.875, "y2": 0.5625, "z2": 0.875},
        "lightAbsorption": 0,
        "resistance": 0.3,
        # Someone got here first: the food is gone, and what is left is what they did not want
        "drops": drops(("carpetfibre", 0.6, 0.6), ("wallpaperstrip", 0.5, 0.5), ("game:paper-parchment", 0.4, 0.4),
                       ("game:drygrass", 0.3, 0.3), ("glassshard", 0.2, 0.2), ("game:flint", 0.02, 0),
                       ("wanderernote-door", 0.03, 0), ("wanderernote-way", 0.03, 0)),
        "sounds": {"place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
    }, "blocktypes", "supplybox-torn.json", comment="Generated by tools/gen_loop.py. A supply box someone else already went through.")
    LANG["block-supplybox-torn"] = "Torn Supply Box"
    LANG["blockdesc-supplybox-torn"] = "Torn open and gone through long ago. Whatever was worth eating is gone; the scraps they left might still be of use."


def open_crate():
    # Seen from above: the lid gone, a dark, empty crate with straw in the corners
    img = crate(1)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, S - 4, S - 4], fill=(40, 30, 18, 255))
    rng = random.Random(7111)
    for cx, cy in ((5, 5), (S - 7, S - 6), (6, S - 7)):
        for _ in range(9):
            x, y = cx + rng.randint(-2, 3), cy + rng.randint(-2, 3)
            d.line([x, y, x + rng.randint(-3, 3), y + rng.randint(-1, 1)], fill=shade((190, 160, 90), rng.uniform(0.7, 1.0)))
    for nx, ny in ((1, 1), (S - 2, 1), (1, S - 2), (S - 2, S - 2)):
        d.point((nx, ny), fill=(150, 150, 150, 255))  # the nails that held the lid, bent up
    save(img, "block/level1/crate-open-top.png")
    # The sides: one plank prised off, showing the dark inside
    img = crate(0)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 11, S - 4, 20], fill=(36, 26, 16, 255))
    d.line([3, 11, S - 4, 11], fill=(70, 50, 30, 255))
    save(img, "block/level1/crate-open-side.png")

    write_json({
        "code": "crate-open",
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood",
        "drawtype": "cube",
        "textures": {"all": {"base": "block/level1/crate-open-side"}, "up": {"base": "block/level1/crate-open-top"},
                     "down": {"base": "block/level1/crate-top"}},
        "resistance": 1.0,
        "lightAbsorption": 99,
        # Prised open and emptied; the boards are still good
        "drops": drops(("game:plank-aged", 1.5, 1), ("game:metalnailsandstrips-iron", 0.3, 0.3), ("game:stick", 0.5, 0.5)),
        "sounds": {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    }, "blocktypes", "level1", "crate-open.json", comment="Generated by tools/gen_loop.py. A crate someone else already emptied.")
    LANG["block-crate-open"] = "Emptied Crate"
    LANG["blockdesc-crate-open"] = "Prised open and emptied. The boards are still good."


# ======================= The anchor =======================

def anchor():
    # Shown when a temporal gear is used outside Level 0, and when a spawn point outside it is cleared
    LANG["anchor-refused"] = "Nothing here will hold you. Only the Lobby still remembers where you came from."
    LANG["anchor-lost"] = "You will wake in the Lobby again: nowhere else in the Backrooms remembers you."


# ======================= Finding the way =======================

def item(code, texture, cls=None, extra=None, variants=None, ground=None):
    """A flat item; `ground` is how it is set down on the floor (detail_kit.ground_storable's arguments)."""
    data = {"code": code}
    if cls:
        data["class"] = cls
    if variants:
        data["variantgroups"] = variants
    data.update({
        "maxstacksize": 16,
        "texture": {"base": texture},
        "creativeinventory": {"general": ["*"], "items": ["*"]},
        "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
        "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
        "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
    })
    if extra:
        data.update(extra)
    return ground_storable(data, **(ground or {}))


def notes():
    # A scrap of lined paper folded in two, a pencilled scrawl and an arrow showing through
    img = sprite()
    d = ImageDraw.Draw(img)
    paper, edge, line, pencil = (226, 218, 192, 255), (150, 138, 108, 255), (176, 190, 206, 255), (70, 66, 60, 255)
    d.polygon([(5, 7), (25, 4), (27, 25), (7, 28)], fill=paper, outline=edge)
    d.line([(6, 17), (26, 14)], fill=(198, 188, 160, 255))  # the fold
    for y in (9, 12, 20, 23):
        d.line([(8, y + 1), (24, y - 2)], fill=line)
    rng = random.Random(7201)
    for y in (10, 21):
        x = 9
        while x < 22:
            w = rng.randint(2, 4)
            d.line([(x, y + 1 - (x - 8) // 6), (x + w, y + 1 - (x + w - 8) // 6)], fill=pencil)
            x += w + 2
    d.line([(12, 25), (20, 24)], fill=pencil)  # an arrow at the foot
    d.polygon([(20, 22), (23, 24), (20, 26)], fill=pencil)
    save(img, "item/wanderernote.png")

    write_json(item("wanderernote", "item/wanderernote", cls="BackroomsWandererNote",
                    variants=[{"code": "kind", "states": ["door", "way", "cache", "refuge"]}],
                    extra={"creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 300,
                           "combustibleProps": {"burnTemperature": 600, "burnDuration": 3}}),
               "itemtypes", "wanderernote.json", comment="Generated by tools/gen_loop.py. Read it (right-click) and it marks a place on the map.")
    for kind in ("door", "way", "cache", "refuge"):
        LANG[f"item-wanderernote-{kind}"] = "Wanderer's Note (" + NOTE_KIND_NAMES[kind] + ")"
    LANG["itemdesc-wanderernote-door"] = "Directions in pencil, half rubbed out: something about a way through the wall. Right-click to read it."
    LANG["itemdesc-wanderernote-way"] = "Someone's directions to a way out of here, scrawled in a hurry. Right-click to read it."
    LANG["itemdesc-wanderernote-cache"] = "A list of supplies, crossed out, and a few words about where the rest were left. Right-click to read it."
    LANG["itemdesc-wanderernote-refuge"] = "A note about somewhere safe, underlined twice. Right-click to read it."

    # What the notes say. {0} is a direction in words, {1} a distance in paces
    LANG.update({
        "note-door-1": "\"The wall goes on for ever, but it doesn't. There's a way through, {0}, about {1} paces. I marked it.\"",
        "note-door-2": "\"Followed the wall for hours. Door at last, {0} of here. {1} paces, give or take. Don't run when you get near it.\"",
        "note-door-3": "\"If you're reading this you're lost like we were. The gap in the wall is {0}, maybe {1} paces. Go quiet.\"",
        "note-way-1": "\"There's another way out of here, {0}, {1} paces or so. It doesn't go where you'd think.\"",
        "note-way-2": "\"Lift (or stairs, or a hole, I don't remember) {0}, about {1} paces. Took it once. Never again.\"",
        "note-way-3": "\"{1} paces {0}. That's where it lets you out. Mark it.\"",
        "note-cache-1": "\"Left what we couldn't carry {0} of here, {1} paces. Still sealed. Take it, we won't be back.\"",
        "note-cache-2": "\"Supplies {0}, about {1} paces. Nobody's opened them. Yet.\"",
        "note-cache-3": "\"Box, sealed, {0}, {1} paces. Food in it, I think. Something was standing near it so I left.\"",
        "note-refuge-1": "\"Somewhere safe, {0}, about {1} paces. Nothing follows you in there.\"",
        "note-refuge-2": "\"If they're after you, go {0}. {1} paces. You can rest there.\"",
        "note-refuge-3": "\"Friendly faces {0} of here, {1} paces. Bring something to trade.\"",
        "note-nothing": "The note's directions don't fit anything round here. Perhaps it was written somewhere else.",
        "dir-n": "north", "dir-ne": "north-east", "dir-e": "east", "dir-se": "south-east",
        "dir-s": "south", "dir-sw": "south-west", "dir-w": "west", "dir-nw": "north-west",
        # Waypoints the Backrooms marks for you
        "levelname": "Level {0}",
        "levelname-6.1": "Level 6.1",
        "waypoint-way": "Way to {0}",
        "waypoint-oneway": "Way to {0} (one way)",
        "waypoint-back": "Way back to {0}",
        "waypoint-gate": "Gate: {0} / {1}",
        # (said instead where the map setting makes no waypoints: the place, which way and how far)
        "mapmark-told": "{0}: {1}, about {2} paces.",
        "waypoint-note-door": "Gate to {0} (a note)",
        "waypoint-note-way": "Way out (a note)",
        "waypoint-note-cache": "Something left (a note)",
        "waypoint-note-refuge": "Refuge (a note)",
    })


# ======================= Dens =======================

def moth_hive():
    # Grey, papery, layered like a wasps' nest, with dark holes where they come and go
    img = noise_fill(hexrgb(0x8C877C), 8, 7301)
    d = ImageDraw.Draw(img)
    rng = random.Random(7302)
    for y in range(1, S, 3):
        x0 = rng.randint(-4, 2)
        d.arc([x0, y - 2, x0 + S + 6, y + 4], 180, 360, fill=shade((110, 104, 94), rng.uniform(0.85, 1.1)))
    for _ in range(5):
        x, y = rng.randint(3, S - 5), rng.randint(3, S - 5)
        d.ellipse([x, y, x + 2, y + 3], fill=(30, 26, 22, 255))
    save(img, "block/detail/mothhive.png")

    tex = "#hive"
    def lump(name, a, b, rot=None):
        e = {"name": name, "from": list(a), "to": list(b),
             "faces": {f: {"texture": tex, "uv": [0, 0, 16, 16]} for f in ("north", "east", "south", "west", "up", "down")}}
        if rot:
            e["rotationOrigin"] = [(a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2]
            e["rotationY"] = rot
        return e
    write_json({"textureWidth": 16, "textureHeight": 16, "textures": {"hive": "backrooms:block/detail/mothhive"},
                "elements": [lump("Base", (2, 0, 3), (14, 5, 13)), lump("Mid", (3, 5, 4), (13, 10, 12), 20),
                             lump("Top", (5, 10, 5), (11, 13, 10), 40), lump("Bud", (10, 0, 11), (15, 6, 15), 15),
                             lump("Bud2", (1, 0, 1), (6, 4, 6), 30)]},
               "shapes", "block", "detail", "mothhive.json")
    write_json({
        "code": "mothhive",
        "shape": {"base": "block/detail/mothhive"},
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Plant",
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 1.0,
        "collisionbox": {"x1": 0.1, "y1": 0, "z1": 0.15, "x2": 0.9, "y2": 0.8, "z2": 0.85},
        "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.15, "x2": 0.9, "y2": 0.8, "z2": 0.85},
        "sounds": {"place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
        # Chewed paper and carpet, and what they lined it with
        "drops": drops(("game:paper-parchment", 1, 1), ("carpetfibre", 2, 1), ("game:cloth-plain", 0.3, 0.3)),
    }, "blocktypes", "detail", "mothhive.json", comment="Generated by tools/gen_loop.py. A Deathmoth hive, the mark of a den.")
    LANG["block-mothhive"] = "Deathmoth Hive"
    LANG["blockdesc-mothhive"] = "Grey paper chewed from walls and carpet, layered like a wasps' nest. Something rustles inside. Breaking it will not go unnoticed."


# ======================= Needs =======================

def write_recipe(data, name):
    write_json(data, "recipes", "grid", name + ".json")


def pry_bar():
    img = sprite()
    d = ImageDraw.Draw(img)
    steel, hi, lo = (120, 126, 134, 255), (190, 196, 204, 255), (64, 68, 74, 255)
    d.line([(7, 28), (24, 6)], fill=lo, width=4)  # the shaft
    d.line([(7, 27), (23, 6)], fill=steel, width=2)
    d.line([(8, 26), (22, 7)], fill=hi)
    d.line([(24, 6), (27, 4), (29, 6)], fill=steel, width=2)  # the claw, curled over
    d.point((29, 7), fill=lo)
    d.line([(6, 29), (4, 27)], fill=steel, width=2)  # the flattened chisel end
    d.rectangle([9, 21, 13, 25], fill=(150, 40, 30, 255))  # a scrap of red paint left on it
    save(img, "item/prybar.png")
    write_json(item("prybar", "item/prybar", cls="BackroomsPryBar", extra={
        "maxstacksize": 1,
        "durability": 24,
        "tags": ["weapon", "weapon-melee"],
        "damagedby": ["attacking"],
        "attackpower": 2,
        "attackRange": 2,
        "creativeinventory": {"general": ["*"], "items": ["*"], "tools": ["*"]},
    }, ground={"layout": "Halves", "ctrl": True}), "itemtypes", "prybar.json", comment="Generated by tools/gen_loop.py. Hold right-click on a locked door to force it.")
    write_recipe({
        "ingredientPattern": "BBN",
        "ingredients": {"B": {"type": "item", "code": "backrooms:metalbracket"},
                        "N": {"type": "item", "code": "game:metalnailsandstrips-iron"}},
        "width": 3, "height": 1, "shapeless": True,
        "output": {"type": "item", "code": "backrooms:prybar"},
    }, "prybar")
    LANG["item-prybar"] = "Pry Bar"
    LANG["itemdesc-prybar"] = ("Hold right-click on a locked door to force it. It gives for good if there is a room behind it, but everything "
                               "nearby will hear. Doors set in solid wall will not give, and cost nothing to try.")
    LANG["pry-solid"] = "It won't give. There's solid wall behind it."
    LANG["pry-notlocked"] = "It isn't locked. It goes somewhere."


SEED_CROPS = ("turnip", "carrot", "onion", "flax", "spelt")
SEED_COLOURS = {"turnip": (196, 120, 200), "carrot": (232, 128, 40), "onion": (210, 180, 110), "flax": (90, 130, 210), "spelt": (210, 176, 70)}


def seed_packets():
    for crop, colour in SEED_COLOURS.items():
        img = sprite()
        d = ImageDraw.Draw(img)
        d.rectangle([8, 4, 24, 28], fill=(232, 224, 200, 255), outline=(140, 128, 100, 255))  # the paper packet
        d.rectangle([9, 9, 23, 21], fill=colour + (255,))  # the picture on the front
        d.ellipse([12, 11, 20, 19], fill=shade(colour, 0.7))
        d.line([(8, 7), (24, 7)], fill=(170, 158, 128, 255))  # the folded top, torn at a corner
        d.polygon([(21, 4), (24, 4), (24, 7)], fill=(0, 0, 0, 0))
        d.line([(10, 24), (22, 24)], fill=(90, 84, 70, 255))  # the name, too faded to read
        save(img, f"item/seedpacket-{crop}.png")
    write_json(item("seedpacket", "item/seedpacket-{crop}", variants=[{"code": "crop", "states": list(SEED_CROPS)}],
                    extra={"maxstacksize": 32, "texture": {"base": "item/seedpacket-{crop}"}}),
               "itemtypes", "seedpacket.json", comment="Generated by tools/gen_loop.py. Opened in the crafting grid for four seeds.")
    write_recipe({
        "ingredientPattern": "P",
        "ingredients": {"P": {"type": "item", "code": "backrooms:seedpacket-*", "name": "crop"}},
        "width": 1, "height": 1,
        "output": {"type": "item", "code": "game:seeds-{crop}", "stacksize": 4},
    }, "seeds-from-packet")
    for crop in SEED_CROPS:
        LANG[f"item-seedpacket-{crop}"] = f"Seed Packet ({crop.capitalize()})"
    LANG["itemdesc-seedpacket-turnip"] = "An old packet of seeds, still sealed. Open it in the crafting grid."
    for crop in SEED_CROPS[1:]:
        LANG[f"itemdesc-seedpacket-{crop}"] = LANG["itemdesc-seedpacket-turnip"]


# ======================= Lang =======================

def merge_lang():
    """Adds the names to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_lines = []
    for key, value in LANG.items():
        line = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)
    json.loads(text)


def main():
    supply_box_shape()
    torn_box_textures()
    torn_box_shape()
    torn_box_block()
    open_crate()
    anchor()
    notes()
    moth_hive()
    pry_bar()
    seed_packets()
    merge_lang()
    print(f"gen_loop: {len(LANG)} names")


if __name__ == "__main__":
    main()
