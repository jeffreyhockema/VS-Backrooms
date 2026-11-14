"""Level 14, the Hospital: its three items (docs/design/experimental-levels/14-plan.md, section 2: the painkillers and the
antibiotics are ours, the soft drinks the page's). The reception desks, the medicine cabinets and the waiting-room seats drop
them (tools/gen_14_props.py).

- l14-painkillers: an amber pill bottle with a white cap. Heals 4 over ten seconds, as a horsetail poultice of linen does
  (vanilla's HealingItem behaviour; pills go down quicker than a poultice goes on).
- l14-antibiotics: a blister pack. Heals 2, and stops any poison still burning in whoever takes them (an Infecting Agent's
  bite): the behaviour BackroomsL14Antibiotics (src/Regions/L14Items.cs).
- l14-stalesoda: "musty soft drink bottles, some with stale contents inside": a brown glass bottle, flat and sour. A little
  hydration, no stability, one time in eight gut rot (the drinks' taintChance), and it leaves an empty bottle.

Writes itemtypes/14/*.json; their look (shapes, textures, transforms: the pill bottle, the blister card and the glass soda
bottle) is tools/gen_items_pantry.py's. Names and descriptions are in lang/en.json, Level 14's block.

    python tools/gen_14_items.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from detail_kit import ground_storable  # noqa: E402
import gen_items_pantry as pantry  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
INV = {"general": ["*"], "items": ["*"], "backrooms": ["*"]}


def write_json(path, data, comment):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = "// " + comment + "\n" + json.dumps(data, indent="\t")
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text + "\n")


# ---------------- Item types ----------------

def healing(health, seconds):
    """Vanilla's HealingItem (as the poultices): health over ten seconds, taken in `seconds`; pills rattle, they make no poultice sound."""
    return {"health": health, "applicationtimesec": seconds, "maxapplicationtimesec": seconds * 3, "effectdurationsec": 10, "ticks": 10,
            "cancelinair": False, "cancelwhileswimming": False, "delaytocancelsec": 0.5,
            "sound": "game:sounds/player/eat", "appliedsound": "game:sounds/player/collect1"}


def items():
    folder = os.path.join(ASSETS, "itemtypes", "14")
    pills = {"code": "l14-painkillers", "maxstacksize": 8, "creativeinventory": INV, "materialDensity": 400,
             "behaviors": [{"name": "HealingItem", "properties": healing(4, 1.5)}]}
    h = pantry.apply_look(pills, "l14-painkillers")
    write_json(os.path.join(folder, "l14-painkillers.json"), ground_storable(pills, height=h),
               "Level 14: a bottle of painkillers from a reception desk or a medicine cabinet. Heals 4 over ten seconds (vanilla HealingItem)")
    anti = {"code": "l14-antibiotics", "maxstacksize": 16, "creativeinventory": INV, "materialDensity": 300,
            "behaviors": [{"name": "BackroomsL14Antibiotics", "properties": healing(2, 1.5)}]}
    h = pantry.apply_look(anti, "l14-antibiotics")
    write_json(os.path.join(folder, "l14-antibiotics.json"), ground_storable(anti, "Messy12", height=h),
               "Level 14: a blister pack of antibiotics from a reception desk. Heals 2, and stops any poison burning in you "
               "(an Infecting Agent's bite): BackroomsL14Antibiotics, src/Regions/L14Items.cs")
    soda = {"code": "l14-stalesoda", "class": "BackroomsAlmondWater", "maxstacksize": 8, "creativeinventory": INV,
            "materialDensity": 1000, "nutritionProps": {"satiety": 40, "foodcategory": "NoNutrition"},
            "attributes": {"stabilityRestored": 0, "wardsDullers": False, "hydration": 200, "satietyWhenThirst": 20,
                           "taintChance": 0.125, "leavesBottle": "backrooms:emptybottle"}}
    h = pantry.apply_look(soda, "l14-stalesoda")
    write_json(os.path.join(folder, "l14-stalesoda.json"), ground_storable(soda, height=h),
               "Level 14: a musty soft-drink bottle with stale contents (the reception rooms). A little hydration, no stability, "
               "one time in eight gut rot; leaves an empty bottle")


if __name__ == "__main__":
    items()
    print("Level 14 items: l14-painkillers, l14-antibiotics, l14-stalesoda")
