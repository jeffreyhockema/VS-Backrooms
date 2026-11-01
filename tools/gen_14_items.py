"""Level 14, the Hospital: its three items (docs/design/experimental-levels/14-plan.md, section 2: the painkillers and the
antibiotics are ours, the soft drinks the page's). The reception desks, the medicine cabinets and the waiting-room seats drop
them (tools/gen_14_props.py).

- l14-painkillers: an amber pill bottle with a white cap. Heals 4 over ten seconds, as a horsetail poultice of linen does
  (vanilla's HealingItem behaviour; pills go down quicker than a poultice goes on).
- l14-antibiotics: a blister pack. Heals 2, and stops any poison still burning in whoever takes them (an Infecting Agent's
  bite): the behaviour BackroomsL14Antibiotics (src/Regions/L14Items.cs).
- l14-stalesoda: "musty soft drink bottles, some with stale contents inside": a brown glass bottle, flat and sour. A little
  hydration, no stability, one time in eight gut rot (the drinks' taintChance), and it leaves an empty bottle.

Writes itemtypes/14/*.json, shapes/item/14/pillbottle.json and textures/item/14/*.png. Names and descriptions are in
lang/en.json, Level 14's block.

    python tools/gen_14_items.py
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402

from detail_kit import ground_storable  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
INV = {"general": ["*"], "items": ["*"], "backrooms": ["*"]}


def write_json(path, data, comment):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = "// " + comment + "\n" + json.dumps(data, indent="\t")
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text + "\n")


def save(img, name):
    path = os.path.join(ASSETS, "textures", "item", "14", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


# ---------------- Textures (16 x 16) ----------------

def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3] if len(c) > 3 else 255,)


def stalesoda():
    """The almondwater bottle's layout: body sides 0-8 x 0-16, neck 8-12 x 0-4, cap 12-16 x 0-4, top and bottom 8-16 x 8-16.
    Brown glass gone dull, a label half peeled and faded to pink, flat brown dregs below a tide line, a rusted crown cap."""
    rnd = random.Random(1401)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    glass, dregs, label, paper = (92, 70, 44), (58, 38, 20), (176, 112, 104), (214, 200, 170)
    for y in range(16):
        for x in range(8):
            c = glass if y < 9 else dregs
            if y == 9:
                c = (120, 96, 60)  # the tide line
            if 4 <= y <= 7:
                c = label if (x + y) % 5 else paper
                if x >= 5 and y >= 6:
                    c = glass  # peeled off
            c = shade(c, 0.9 + rnd.random() * 0.2)
            if x == 1 and not 4 <= y <= 7:
                c = shade(c, 1.45)  # the shine
            px[x, y] = c
    for y in range(4):
        for x in range(8, 12):
            px[x, y] = shade(glass, 1.05 if x == 9 else 0.9)
        for x in range(12, 16):
            px[x, y] = shade((150, 84, 46) if (x + y) % 3 else (110, 58, 30), 0.9 + rnd.random() * 0.2)
    for y in range(8, 16):
        for x in range(8, 16):
            px[x, y] = shade(dregs if y >= 8 else glass, 0.85 + rnd.random() * 0.25)
    save(img, "stalesoda")


def pillbottle():
    """The pill bottle's shape: body sides 0-8 x 0-12, top and bottom 8-16 x 8-16, cap sides 8-16 x 0-4, cap top 8-16 x 4-8.
    Amber plastic, a white pharmacy label with lines of print, a white child-proof cap."""
    rnd = random.Random(1402)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    amber, label, ink, cap = (196, 110, 30), (236, 232, 222), (90, 96, 120), (238, 238, 232)
    for y in range(12):
        for x in range(8):
            c = amber
            if 2 <= y <= 8:
                c = label
                if y in (4, 6) and 1 <= x <= 6 - (y == 6) * 2:
                    c = ink
                if y == 3 and x in (1, 2):
                    c = (200, 40, 40)
            c = shade(c, 0.92 + rnd.random() * 0.12)
            if x == 1 and not 2 <= y <= 8:
                c = shade(c, 1.3)
            px[x, y] = c
    for y in range(12, 16):
        for x in range(8):
            px[x, y] = shade(amber, 0.8)
    for y in range(4):
        for x in range(8, 16):
            px[x, y] = shade(cap, 0.82 if x % 2 else 0.95)  # the grip ridges
    for y in range(4, 8):
        for x in range(8, 16):
            px[x, y] = shade(cap, 1.0 if (x - 12) ** 2 + (y - 6) ** 2 > 2 else 0.88)
    for y in range(8, 16):
        for x in range(8, 16):
            px[x, y] = shade(amber, 0.85 + rnd.random() * 0.15)
    save(img, "pillbottle")


def blister():
    """A flat blister pack of six: silver foil on a card, the bubbles white and pale yellow capsules, two already pushed out."""
    rnd = random.Random(1403)
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    px = img.load()
    foil = (186, 190, 196)
    for y in range(2, 15):
        for x in range(3, 13):
            c = shade(foil, 0.88 + rnd.random() * 0.2)
            if y in (2, 14) or x in (3, 12):
                c = shade(foil, 0.7)
            px[x, y] = c
    for y in range(2, 4):
        for x in range(4, 12):
            px[x, y] = (70, 120, 170, 255)  # the printed strip
    empty = {(1, 1), (0, 2)}
    for row in range(3):
        for col in range(2):
            bx, by = 5 + col * 4, 5 + row * 3
            for dx in range(2):
                gone = (col, row) in empty
                c = (120, 110, 100, 255) if gone else ((246, 244, 236, 255) if dx == 0 else (232, 214, 120, 255))
                px[bx + dx, by] = c
                px[bx + dx, by + 1] = shade(c, 0.8)
    save(img, "blister")


# ---------------- The pill bottle's shape ----------------

def pillbottle_shape():
    faces = lambda side, top: {**{f: {"texture": "#tex", "uv": side} for f in ("north", "east", "south", "west")},
                                **({"up": {"texture": "#tex", "uv": top}, "down": {"texture": "#tex", "uv": [8, 8, 16, 16]}} if top else {})}
    shape = {
        "textureWidth": 16, "textureHeight": 16,
        "textures": {"tex": "backrooms:item/14/pillbottle"},
        "elements": [
            {"name": "Body", "from": [6.25, 0, 6.25], "to": [9.75, 5, 9.75], "faces": faces([0, 0, 8, 12], [8, 8, 16, 16])},
            {"name": "Cap", "from": [6, 5, 6], "to": [10, 6.5, 10], "faces": faces([8, 0, 16, 4], [8, 4, 16, 8])},
        ],
    }
    path = os.path.join(ASSETS, "shapes", "item", "14", "pillbottle.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(json.dumps(shape, indent="\t") + "\n")


# ---------------- Item types ----------------

BOTTLE_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 157.4, "y": -45.3, "z": 0}, "origin": {"x": 0.5, "y": 0.34, "z": 0.5}, "scale": 2.2},
    "fpHandTransform": {"translation": {"x": 0, "y": 0.1, "z": 0.4}, "rotation": {"x": 0, "y": -30, "z": 0}, "scale": 1.8},
    "tpHandTransform": {"translation": {"x": -0.85, "y": -0.5, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.7},
    "groundTransform": {"rotation": {"x": 0, "y": -45, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.5},
}
PILLS_TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 157.4, "y": -45.3, "z": 0}, "origin": {"x": 0.5, "y": 0.2, "z": 0.5}, "scale": 2.8},
    "fpHandTransform": {"translation": {"x": 0, "y": 0.2, "z": 0.4}, "rotation": {"x": 0, "y": -30, "z": 0}, "scale": 2.2},
    "tpHandTransform": {"translation": {"x": -0.85, "y": -0.45, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.8},
    "groundTransform": {"rotation": {"x": 0, "y": -45, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 3},
}
SPRITE = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}


def healing(health, seconds):
    """Vanilla's HealingItem (as the poultices): health over ten seconds, taken in `seconds`; pills rattle, they make no poultice sound."""
    return {"health": health, "applicationtimesec": seconds, "maxapplicationtimesec": seconds * 3, "effectdurationsec": 10, "ticks": 10,
            "cancelinair": False, "cancelwhileswimming": False, "delaytocancelsec": 0.5,
            "sound": "game:sounds/player/eat", "appliedsound": "game:sounds/player/collect1"}


def items():
    folder = os.path.join(ASSETS, "itemtypes", "14")
    pills = dict({"code": "l14-painkillers", "maxstacksize": 8, "shape": {"base": "item/14/pillbottle"},
                  "textures": {"tex": {"base": "item/14/pillbottle"}}, "creativeinventory": INV, "materialDensity": 400,
                  "behaviors": [{"name": "HealingItem", "properties": healing(4, 1.5)}]}, **PILLS_TRANSFORMS)
    write_json(os.path.join(folder, "l14-painkillers.json"),
               ground_storable(pills, height=0.4, select=(0, 0, 0, 1, 0.4, 1)),
               "Level 14: a bottle of painkillers from a reception desk or a medicine cabinet. Heals 4 over ten seconds (vanilla HealingItem)")
    anti = dict({"code": "l14-antibiotics", "maxstacksize": 16, "texture": {"base": "item/14/blister"}, "creativeinventory": INV,
                 "materialDensity": 300,
                 "behaviors": [{"name": "BackroomsL14Antibiotics", "properties": healing(2, 1.5)}]}, **SPRITE)
    write_json(os.path.join(folder, "l14-antibiotics.json"), ground_storable(anti, "Messy12"),
               "Level 14: a blister pack of antibiotics from a reception desk. Heals 2, and stops any poison burning in you "
               "(an Infecting Agent's bite): BackroomsL14Antibiotics, src/Regions/L14Items.cs")
    soda = dict({"code": "l14-stalesoda", "class": "BackroomsAlmondWater", "maxstacksize": 8, "shape": {"base": "item/almondwater"},
                 "textures": {"tex": {"base": "item/14/stalesoda"}}, "creativeinventory": INV, "materialDensity": 1000,
                 "nutritionProps": {"satiety": 40, "foodcategory": "NoNutrition"},
                 "attributes": {"stabilityRestored": 0, "wardsDullers": False, "hydration": 200, "satietyWhenThirst": 20,
                                "taintChance": 0.125, "leavesBottle": "backrooms:emptybottle"}}, **BOTTLE_TRANSFORMS)
    write_json(os.path.join(folder, "l14-stalesoda.json"),
               ground_storable(soda, height=0.6875, select=(0, 0, 0, 1, 0.6875, 1)),
               "Level 14: a musty soft-drink bottle with stale contents (the reception rooms). A little hydration, no stability, "
               "one time in eight gut rot; leaves an empty bottle")


if __name__ == "__main__":
    stalesoda()
    pillbottle()
    blister()
    pillbottle_shape()
    items()
    print("Level 14 items: l14-painkillers, l14-antibiotics, l14-stalesoda")
