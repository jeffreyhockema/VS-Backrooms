"""Assets for the survival loop (docs/design/survival-loop-plan.md): what has been picked over, what tells you where to go,
and what a home needs. Run on its own: python tools/gen_loop.py

- Torn supply boxes and prised-open crates: the three in four that wanderers went through before you.
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
from gen_textures import box, crate, hexrgb, noise_fill, save, shade, sprite, S

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

def torn_box_textures():
    # The side: the same cardboard, the tape slit and a flap's edge torn ragged
    img = box(False)
    d = ImageDraw.Draw(img)
    rng = random.Random(7101)
    d.rectangle([13, 0, 18, 7], fill=(140, 102, 62, 255))  # tape cut through
    for x in range(0, S):
        y = 2 + int(2.5 * abs(((x * 7) % 11) / 5.5 - 1)) + rng.randint(0, 1)
        d.line([x, 0, x, y], fill=(64, 46, 28, 255))  # ragged top edge, the dark inside showing
    d.line([4, 14, 9, 22], fill=(120, 86, 52, 255))  # a crease where it was trodden on
    save(img, "block/supplybox-torn-side.png")

    # Inside: an empty box, a little packing straw and a torn wrapper
    img = noise_fill(hexrgb(0x3E2C1A), 6, 7102)
    d = ImageDraw.Draw(img)
    rng = random.Random(7103)
    for _ in range(26):
        x, y = rng.randint(2, S - 3), rng.randint(2, S - 3)
        d.line([x, y, x + rng.randint(-4, 4), y + rng.randint(-2, 2)], fill=shade((196, 168, 96), rng.uniform(0.7, 1.05)))
    d.polygon([(19, 20), (26, 18), (27, 24), (21, 26)], fill=(176, 50, 40, 255))  # an empty crackers wrapper
    d.rectangle([0, 0, S - 1, S - 1], outline=(140, 102, 62, 255), width=2)  # the cardboard walls, seen from above
    save(img, "block/supplybox-torn-inside.png")

    # The flaps: plain cardboard, inside face darker
    save(box(True), "block/supplybox-flap.png")


def torn_box_shape():
    """A box with its lid torn back: lower walls, an open top, two flaps lolling over the sides."""
    side, inside, flap = "#side", "#inside", "#flap"
    def face(tex, uv):
        return {"texture": tex, "uv": uv}
    elements = [
        {"name": "Floor", "from": [2, 0, 2], "to": [14, 1, 14],
         "faces": {"up": face(inside, [2, 2, 14, 14]), "down": face(side, [2, 2, 14, 14])}},
        {"name": "WallN", "from": [2, 0, 2], "to": [14, 9, 3],
         "faces": {"north": face(side, [2, 1, 14, 10]), "south": face(inside, [2, 1, 14, 10]), "up": face(side, [2, 0, 14, 1]),
                   "east": face(side, [0, 1, 1, 10]), "west": face(side, [0, 1, 1, 10])}},
        {"name": "WallS", "from": [2, 0, 13], "to": [14, 9, 14],
         "faces": {"south": face(side, [2, 1, 14, 10]), "north": face(inside, [2, 1, 14, 10]), "up": face(side, [2, 0, 14, 1]),
                   "east": face(side, [0, 1, 1, 10]), "west": face(side, [0, 1, 1, 10])}},
        {"name": "WallW", "from": [2, 0, 3], "to": [3, 9, 13],
         "faces": {"west": face(side, [3, 1, 13, 10]), "east": face(inside, [3, 1, 13, 10]), "up": face(side, [3, 0, 13, 1])}},
        {"name": "WallE", "from": [13, 0, 3], "to": [14, 9, 13],
         "faces": {"east": face(side, [3, 1, 13, 10]), "west": face(inside, [3, 1, 13, 10]), "up": face(side, [3, 0, 13, 1])}},
        # Flaps hinged on the east and west rims, folded back down over the outside
        {"name": "FlapE", "from": [14, 8.5, 2], "to": [19, 9, 14], "rotationOrigin": [14, 9, 8], "rotationZ": -60,
         "faces": {"up": face(flap, [2, 2, 7, 14]), "down": face(inside, [2, 2, 7, 14]), "east": face(side, [0, 0, 12, 1])}},
        {"name": "FlapW", "from": [-3, 8.5, 2], "to": [2, 9, 14], "rotationOrigin": [2, 9, 8], "rotationZ": 75,
         "faces": {"up": face(flap, [9, 2, 14, 14]), "down": face(inside, [9, 2, 14, 14]), "west": face(side, [0, 0, 12, 1])}},
    ]
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"side": "backrooms:block/supplybox-torn-side", "inside": "backrooms:block/supplybox-torn-inside",
                          "flap": "backrooms:block/supplybox-flap"},
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
                       ("game:drygrass", 0.3, 0.3), ("glassshard", 0.2, 0.2), ("game:flint", 0.1, 0),
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
