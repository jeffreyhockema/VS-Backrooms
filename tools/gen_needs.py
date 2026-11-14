"""Water and drinks for the Needs feature (docs/design/needs/README.md section 3).

Writes, idempotently (run it as often as you like, under `tools/locked.sh run python tools/gen_needs.py`):

  * the item types in itemtypes/needs/: almondwaterblue, almondwatergreen, emptybottle, bottledwater (variants clean, murky,
    salt). They share Almond Water's bottle (shapes/item/pantry/bottle.json) with their own textures: the look (shape,
    textures, transforms) is tools/gen_items_pantry.py's, which paints the textures;
  * their lang keys, and the strings the drinks and the water behaviour use, merged into lang/en.json in place (existing keys
    updated where they are, new ones appended at the end).

The existing drinks (almondwater, cashewwater, waterbottle, the sodas, ...) are not written here: their own generators or files
carry the new `hydration` attributes.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_items_pantry as pantry  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
ITEMS = os.path.join(ASSETS, "itemtypes", "needs")
LANG_PATH = os.path.join(ASSETS, "lang", "en.json")

# ---------------------------------------------------------------- items

GROUND = {"name": "GroundStorable", "properties": {
    "layout": "Quadrants",
    "collisionBox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.125, "z2": 1}}}
BOTTLE = "backrooms:emptybottle"


def write_item(code, data, comment, look=None):
    """look: the pantry look to take (the code's own by default)."""
    os.makedirs(ITEMS, exist_ok=True)
    data = dict(data)
    textures = data.pop("textures", None)
    height = pantry.apply_look(data, look or code)
    if textures:
        data["textures"] = textures       # a variant type names its textures by variant
    ground = json.loads(json.dumps(GROUND))
    ground["properties"]["selectionBox"] = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": height, "z2": 1}
    data["behaviors"] = [ground]
    data["creativeinventory"] = {"general": ["*"], "items": ["*"]}
    text = "// " + comment + "\n" + json.dumps(data, indent="\t") + "\n"
    with open(os.path.join(ITEMS, code + ".json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def items():
    # Blue and Green Almond Water: the plain kind's hydration; satiety only while thirst is off (as the other drinks)
    write_item("almondwaterblue", {
        "code": "almondwaterblue", "class": "BackroomsAlmondWater", "maxstacksize": 8,
        "nutritionProps": {"satiety": 120, "health": 1, "foodcategory": "NoNutrition"}, "materialDensity": 1000,
        "attributes": {"stabilityRestored": 0.25, "hydration": 600, "satietyWhenThirst": 0, "sleepAid": True, "leavesBottle": BOTTLE},
    }, "Blue Almond Water: hydrates like the plain kind, restores more stability, and makes you drowsy at once (sleep in a bed)")
    write_item("almondwatergreen", {
        "code": "almondwatergreen", "class": "BackroomsAlmondWater", "maxstacksize": 8,
        "nutritionProps": {"satiety": 120, "health": 1, "foodcategory": "NoNutrition"}, "materialDensity": 1000,
        "attributes": {"stabilityRestored": 0.1, "hydration": 600, "satietyWhenThirst": 0, "caffeineHours": 10, "leavesBottle": BOTTLE},
    }, "Green Almond Water: hydrates, restores a little stability, holds tiredness off for ten game hours and then lands it at once")
    write_item("emptybottle", {
        "code": "emptybottle", "class": "BackroomsEmptyBottle", "maxstacksize": 16,
        "materialDensity": 1000, "liquidSelectable": True,
    }, "An empty bottle, left by a drink (with thirst on). Right-click water to fill it by the water's class")

    # Bottled water: three variants by the class of the water it was filled from. A murky bottle boils clean in a firepit
    bottled_common = {"leavesBottle": BOTTLE, "satietyWhenThirst": 0, "wardsDullers": False,
                      "handbook": {"groupBy": ["bottledwater-*"]}}
    write_item("bottledwater", {
        "code": "bottledwater", "class": "BackroomsAlmondWater", "maxstacksize": 8,
        "variantgroups": [{"code": "kind", "states": ["clean", "murky", "salt"]}],
        "textures": {"tex": {"base": "item/pantry/bottledwater-{kind}"}},
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
    }, "Bottled water by the class of the water it came from: clean, murky (boil it in a firepit to make it clean) and salt (never)",
        look="bottledwater-clean")


# ---------------------------------------------------------------- lang

LANG = {
    "item-almondwaterblue": "Blue Almond Water",
    "itemdesc-almondwaterblue": "Almond Water with a blue cap, cold to the touch. It steadies you more than the plain kind, and your eyelids go heavy at once. Drink it when you mean to sleep.",
    "item-almondwatergreen": "Green Almond Water",
    "itemdesc-almondwatergreen": "Almond Water with a green cap, bitter under the sweetness. It steadies you a little and keeps the tiredness off for about twenty minutes. When it wears off, about sixteen minutes of it arrives at once.",
    "item-emptybottle": "Empty Bottle",
    "itemdesc-emptybottle": "A glass bottle with nothing in it. Right-click water to fill it.",
    "item-bottledwater-clean": "Bottle of Clean Water",
    "itemdesc-bottledwater-clean": "Clear and cold. Safe to drink.",
    "item-bottledwater-murky": "Bottle of Murky Water",
    "itemdesc-bottledwater-murky": "Brown, with a skin of silt. It will hydrate you, a little, and your stomach may not forgive it. Boil it in a firepit to make it clean.",
    "item-bottledwater-salt": "Bottle of Salt Water",
    "itemdesc-bottledwater-salt": "Brine from the sea. Drinking it dries you out. Boiling does not help.",
    "heldhelp-fillbottle": "Fill with water",
    "iteminfo-hydration": "Water: {0}%",
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
    items()
    merge_lang()
    print(f"needs: 4 item types, {len(LANG)} lang keys")
    sys.exit(0)
