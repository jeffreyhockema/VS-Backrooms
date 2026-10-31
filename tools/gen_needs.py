"""Water and drinks for the Needs feature (docs/design/needs/README.md section 3).

Writes, idempotently (run it as often as you like, under `tools/locked.sh run python tools/gen_needs.py`):

  * the textures of the new bottles, tinted from the Almond Water texture (textures/item/almondwater.png, which this does not
    touch): almondwaterblue, almondwatergreen, emptybottle, bottledwater-clean / -murky / -salt. The label stays readable: only
    the colours are swapped, one palette entry per colour of the original (body, label light, label dark, highlight, neck, cap);
  * the item types in itemtypes/needs/: almondwaterblue, almondwatergreen, emptybottle, bottledwater (variants clean, murky,
    salt). They share Almond Water's bottle shape (shapes/item/almondwater.json) with their own texture;
  * their lang keys, and the strings the drinks and the water behaviour use, merged into lang/en.json in place (existing keys
    updated where they are, new ones appended at the end).

The existing drinks (almondwater, cashewwater, waterbottle, the sodas, ...) are not written here: their own generators or files
carry the new `hydration` attributes.
"""
import json
import os
import re
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "item")
ITEMS = os.path.join(ASSETS, "itemtypes", "needs")
LANG_PATH = os.path.join(ASSETS, "lang", "en.json")

# The colours of textures/item/almondwater.png and what each becomes. body: the bottle; label / label_dark: the band across it;
# highlight: the glint down its left edge; neck; cap.
ORIGINAL = {
    "body": (236, 228, 205), "label": (196, 160, 104), "label_dark": (120, 84, 44),
    "highlight": (250, 248, 240), "neck": (225, 232, 236), "cap": (60, 110, 170),
}
PALETTES = {
    # Blue: a cold pale blue bottle, a deep blue label, a dark blue cap
    "almondwaterblue": dict(body=(205, 222, 245), label=(88, 140, 214), label_dark=(36, 78, 150), highlight=(250, 250, 255),
                            neck=(222, 232, 246), cap=(24, 52, 128)),
    # Green: a pale green bottle, a leafy label, a dark green cap
    "almondwatergreen": dict(body=(208, 238, 206), label=(104, 172, 96), label_dark=(44, 108, 56), highlight=(250, 255, 248),
                             neck=(226, 242, 224), cap=(34, 96, 48)),
    # Bottled water, clean: clear glass with a pale blue tint and a white cap
    "bottledwater-clean": dict(body=(198, 230, 242), label=(168, 210, 230), label_dark=(128, 178, 208), highlight=(248, 252, 255),
                               neck=(216, 238, 246), cap=(236, 242, 246)),
    # Murky: brown with silt, a grey cap
    "bottledwater-murky": dict(body=(150, 118, 72), label=(122, 94, 54), label_dark=(84, 62, 34), highlight=(190, 160, 110),
                               neck=(170, 138, 90), cap=(96, 96, 92)),
    # Salt: grey-green, a white-grey cap
    "bottledwater-salt": dict(body=(150, 170, 152), label=(124, 148, 130), label_dark=(88, 112, 96), highlight=(206, 220, 208),
                              neck=(172, 188, 174), cap=(204, 208, 204)),
    # Empty: glass with nothing in it, the label gone, a grey cap
    "emptybottle": dict(body=(214, 224, 228), label=(214, 224, 228), label_dark=(188, 200, 206), highlight=(246, 250, 252),
                        neck=(228, 236, 240), cap=(160, 170, 176)),
}


def tinted(source, palette):
    """The source image with each of the original's colours swapped for the palette's."""
    lookup = {ORIGINAL[k]: palette[k] for k in ORIGINAL}
    out = source.copy()
    px = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a and (r, g, b) in lookup:
                nr, ng, nb = lookup[(r, g, b)]
                px[x, y] = (nr, ng, nb, a)
    return out


def textures():
    source = Image.open(os.path.join(TEX, "almondwater.png")).convert("RGBA")
    for code, palette in PALETTES.items():
        tinted(source, palette).save(os.path.join(TEX, code + ".png"))


# ---------------------------------------------------------------- items

TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 157.4, "y": -45.3, "z": 0}, "origin": {"x": 0.5, "y": 0.34, "z": 0.5}, "scale": 2.2},
    "fpHandTransform": {"translation": {"x": 0, "y": 0.1, "z": 0.4}, "rotation": {"x": 0, "y": -30, "z": 0}, "scale": 1.8},
    "tpHandTransform": {"translation": {"x": -0.85, "y": -0.5, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.7},
    "groundTransform": {"rotation": {"x": 0, "y": -45, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.5},
}
GROUND = {"name": "GroundStorable", "properties": {
    "layout": "Quadrants",
    "collisionBox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.125, "z2": 1},
    "selectionBox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.6875, "z2": 1}}}
BOTTLE = "backrooms:emptybottle"


def write_item(code, data, comment):
    os.makedirs(ITEMS, exist_ok=True)
    data = dict(data)
    data.update(TRANSFORMS)
    data["behaviors"] = [GROUND]
    data["creativeinventory"] = {"general": ["*"], "items": ["*"]}
    text = "// " + comment + "\n" + json.dumps(data, indent="\t") + "\n"
    with open(os.path.join(ITEMS, code + ".json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def items():
    shape = {"base": "item/almondwater"}
    # Blue and Green Almond Water: the plain kind's hydration; satiety only while thirst is off (as the other drinks)
    write_item("almondwaterblue", {
        "code": "almondwaterblue", "class": "BackroomsAlmondWater", "maxstacksize": 8, "shape": shape,
        "textures": {"tex": {"base": "item/almondwaterblue"}},
        "nutritionProps": {"satiety": 120, "health": 1, "foodcategory": "NoNutrition"}, "materialDensity": 1000,
        "attributes": {"stabilityRestored": 0.25, "hydration": 600, "satietyWhenThirst": 0, "sleepAid": True, "leavesBottle": BOTTLE},
    }, "Blue Almond Water: hydrates like the plain kind, restores more stability, and makes you drowsy at once (sleep in a bed)")
    write_item("almondwatergreen", {
        "code": "almondwatergreen", "class": "BackroomsAlmondWater", "maxstacksize": 8, "shape": shape,
        "textures": {"tex": {"base": "item/almondwatergreen"}},
        "nutritionProps": {"satiety": 120, "health": 1, "foodcategory": "NoNutrition"}, "materialDensity": 1000,
        "attributes": {"stabilityRestored": 0.1, "hydration": 600, "satietyWhenThirst": 0, "caffeineHours": 10, "leavesBottle": BOTTLE},
    }, "Green Almond Water: hydrates, restores a little stability, holds tiredness off for ten game hours and then lands it at once")
    write_item("emptybottle", {
        "code": "emptybottle", "class": "BackroomsEmptyBottle", "maxstacksize": 16, "shape": shape,
        "textures": {"tex": {"base": "item/emptybottle"}}, "materialDensity": 1000, "liquidSelectable": True,
    }, "An empty bottle, left by a drink (with thirst on). Right-click water to fill it by the water's class")

    # Bottled water: three variants by the class of the water it was filled from. A murky bottle boils clean in a firepit
    bottled_common = {"leavesBottle": BOTTLE, "satietyWhenThirst": 0, "wardsDullers": False,
                      "handbook": {"groupBy": ["bottledwater-*"]}}
    write_item("bottledwater", {
        "code": "bottledwater", "class": "BackroomsAlmondWater", "maxstacksize": 8, "shape": shape,
        "variantgroups": [{"code": "kind", "states": ["clean", "murky", "salt"]}],
        "textures": {"tex": {"base": "item/bottledwater-{kind}"}},
        "nutritionPropsByType": {
            "*-clean": {"satiety": 100, "foodcategory": "NoNutrition"},
            "*-murky": {"satiety": 50, "foodcategory": "NoNutrition"},
            "*-salt": {"satiety": 0, "foodcategory": "NoNutrition"},
        },
        "materialDensity": 1000,
        "attributesByType": {
            "*-clean": dict(bottled_common, hydration=600, stabilityRestored=0),
            "*-murky": dict(bottled_common, hydration=300, stabilityRestored=-0.05, taintChance=0.25),
            "*-salt": dict(bottled_common, hydration=-300, stabilityRestored=0),
        },
        "combustiblePropsByType": {
            "*-murky": {"meltingPoint": 100, "meltingDuration": 10, "smeltedRatio": 1,
                        "smeltedStack": {"type": "item", "code": "backrooms:bottledwater-clean"}, "requiresContainer": False},
        },
    }, "Bottled water by the class of the water it came from: clean, murky (boil it in a firepit to make it clean) and salt (never)")


# ---------------------------------------------------------------- lang

LANG = {
    "item-almondwaterblue": "Blue Almond Water",
    "itemdesc-almondwaterblue": "Almond Water with a blue cap, cold to the touch. It steadies you more than the plain kind, and your eyelids go heavy at once. Drink it when you mean to sleep.",
    "item-almondwatergreen": "Green Almond Water",
    "itemdesc-almondwatergreen": "Almond Water with a green cap, bitter under the sweetness. It steadies you a little and keeps the tiredness off for ten hours. When it wears off, all of it arrives at once.",
    "item-emptybottle": "Empty Bottle",
    "itemdesc-emptybottle": "A glass bottle with nothing in it. Right-click water to fill it.",
    "item-bottledwater-clean": "Bottle of Clean Water",
    "itemdesc-bottledwater-clean": "Clear and cold. Safe to drink.",
    "item-bottledwater-murky": "Bottle of Murky Water",
    "itemdesc-bottledwater-murky": "Brown, with a skin of silt. It will hydrate you, a little, and your stomach may not forgive it. Boil it in a firepit to make it clean.",
    "item-bottledwater-salt": "Bottle of Salt Water",
    "itemdesc-bottledwater-salt": "Brine from the sea. Drinking it dries you out. Boiling does not help.",
    "heldhelp-fillbottle": "Fill with water",
    "iteminfo-hydration": "Hydration: {0}%",
    "iteminfo-stability": "Stability: {0}%",
    "drink-clean": "Cool and clean. You feel better.",
    "drink-tainted": "It tastes of old pipes and dust.",
    "drink-sick": "Your stomach turns.",
    "drink-salt": "It's brine. Your throat burns.",
    "drink-scald": "The water is scalding!",
    "dispenser-restocks-slowly": "Sold out. It restocks once a fortnight.",
}


def merge_lang():
    """Updates these keys in lang/en.json in place and appends the new ones at the end (the file is otherwise untouched)."""
    with open(LANG_PATH, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    new_lines = []
    for key, value in LANG.items():
        line = "\t" + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^\t" + re.escape(json.dumps(key)) + r":.*?(,?)\r?$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + nl + nl + ("," + nl).join(new_lines) + nl + "}" + nl
    json.loads(text)  # still valid
    with open(LANG_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(text)


if __name__ == "__main__":
    textures()
    items()
    merge_lang()
    print(f"needs: {len(PALETTES)} textures, 4 item types, {len(LANG)} lang keys")
    sys.exit(0)
