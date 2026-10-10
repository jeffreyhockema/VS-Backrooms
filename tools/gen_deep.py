"""Blocks, props, items and names for Levels 6 to 10 and Level 6.1. Called from gen_detail.py, which writes them out
along with everything else (python tools/gen_detail.py)."""
import math
import os

import deep_textures
from detail_kit import (ASSETS, CLOTH, GLASS, LANG, METAL, ROTATE, SIDES, STONE, WOOD, Decor, block, bx, cyl, name,
                        prop, shape, wall_family, write_json)
from gen_detail import carton, cube_block, plate


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


def drops(*items):
    """Drops for salvage: (code, average, variance); codes without a domain are ours."""
    return [{"type": "item", "code": c, "quantity": {"avg": a, "var": v}} for c, a, v in items]


def door_block(code, english, tex, kind, material="Metal", sounds=METAL, comment=None):
    data = {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": material, "drawtype": "cube",
        "textures": {"all": {"base": f"block/detail/{tex}-{{part}}"}},
        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": sounds,
    }
    if kind:
        data["behaviors"] = threshold(kind)
    block(code, data, comment or english)
    name(f"{code}-*", english)


TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}


def food(code, english, satiety, category, desc, health=0, stack=16, extra=None):
    data = {"code": code, "maxstacksize": stack, "texture": {"base": f"item/{code}"},
            "creativeinventory": {"general": ["*"], "items": ["*"]},
            "nutritionProps": dict({"satiety": satiety, "foodcategory": category}, **({"health": health} if health else {})),
            "materialDensity": 600}
    data.update(TRANSFORMS)
    if extra:
        data.update(extra)
    write_json(os.path.join(ASSETS, "itemtypes", "deep", code + ".json"), data, english)
    LANG[f"item-{code}"] = english
    LANG[f"itemdesc-{code}"] = desc


# ======================= Level 6 =======================

def level6():
    cube_block("l6block", {"wall": "Cold Wall", "floor": "Cold Floor", "ceiling": "Cold Ceiling", "wet": "Wet Cold Floor"}, ["wall", "floor", "ceiling", "wet"],
               {"wall": "l6wall", "floor": "l6floor", "ceiling": "l6ceiling", "wet": "l6floor-wet"},
               comment="The smooth, cold material of Level 6's hallways")
    wall_family("l6deco", "Cold Wall", {1: "l6wall"}, [
        Decor("megexit", "Chalk Marking", {2: [bx("Chalk", (0, 0, -0.05), (16, 16, 0), "chalk-megexit", faces=("north",), full=True)]}),
        Decor("megcross", "Chalk Marking", {2: [bx("Chalk", (0, 0, -0.05), (16, 16, 0), "chalk-megcross", faces=("north",), full=True)]}),
        Decor("meglogo", "Chalk Marking", {2: [bx("Chalk", (0, 0, -0.05), (16, 16, 0), "chalk-meglogo", faces=("north",), full=True)]}),
        Decor("handprints", "Handprints", {2: [bx("Prints", (0, 0, -0.05), (16, 16, 0), "handprints", faces=("north",), full=True)]}),
        Decor("scratches", "Scratches", {2: [bx("Scratches", (0, 0, -0.05), (16, 16, 0), "scratches", faces=("north",), full=True)]}),
        # A light switch, the only one anybody has found. It does nothing
        Decor("deadswitch", "Light Switch", {2: plate("Switch", (6.5, 5, -0.5), (9.5, 10, 0), "switchplate", "switchplate") +
                                                [bx("Toggle", (7.5, 6.5, -1), (8.5, 8, -0.5), "white")]}),
    ])
    prop("tripwire", "Tripwire", [
        bx("PinL", (0.5, 0, 7.6), (1.3, 2.5, 8.4), "metaldark"), bx("PinR", (14.7, 0, 7.6), (15.5, 2.5, 8.4), "metaldark"),
        bx("Wire", (0.5, 1.7, 7.9), (15.5, 1.95, 8.1), "steel")], box=(0, 0, 0.4, 1, 0.15, 0.6), collide=False, material="Metal", sounds=METAL,
         comment="A thin wire across a passage at ankle height. In the dark you won't see it")
    block("waveecho", {
        "blockmaterial": "Stone", "drawtype": "Empty",
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None, "selectionbox": None,
        "lightAbsorption": 0, "resistance": 999, "drops": [], "replaceable": 9000,
        "sounds": {"ambient": "backrooms:ambient/waves", "ambientBlockCount": 1},
    }, "Invisible: the faint sound of waves from below, the way down to Level 7")
    name("waveecho", "Sound of Waves")

    # Surveyor's chalk and the marks it leaves
    by_type = {}
    for symbol in ("left", "right", "cross", "circle"):
        path = shape(f"chalkmark-{symbol}", [bx("Mark", (0, 0, 15.85), (16, 16, 16), f"chalkmark-{symbol}", faces=("north",), full=True)])
        for s in SIDES:
            by_type[f"*-{symbol}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("chalkmark", {
        "variantgroups": [{"code": "symbol", "states": ["left", "right", "cross", "circle"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-left-north"]}, "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionboxByType": {f"*-{s}": {"x1": 0.1, "y1": 0.1, "z1": 0.9, "x2": 0.9, "y2": 0.9, "z2": 1, "rotateY": ROTATE[s]} for s in SIDES},
        "lightAbsorption": 0, "resistance": 0.2, "drops": [], "replaceable": 5000,
        "sounds": {"place": "game:block/loosestone", "break": "game:block/loosestone", "hit": "game:block/loosestone"},
    }, "A chalk mark on a wall, left by someone finding their way")
    name("chalkmark-*", "Chalk Mark")
    data = {"code": "chalk", "class": "BackroomsChalk", "maxstacksize": 1, "durability": 48,
            "texture": {"base": "item/chalk"}, "creativeinventory": {"general": ["*"], "items": ["*"]}}
    data.update(TRANSFORMS)
    write_json(os.path.join(ASSETS, "itemtypes", "deep", "chalk.json"), data, "Surveyor's chalk: marks walls. The one thing in Level 6 that stays where you left it")
    LANG["item-chalk"] = "Surveyor's Chalk"
    LANG["itemdesc-chalk"] = "Right-click a wall to leave a mark: an arrow, a cross or a circle. Choose which with the tool mode key (F). Marks show on your map. Found in crumbled ceiling tiles, or made from a chalk stone."
    write_json(os.path.join(ASSETS, "recipes", "grid", "chalk.json"), {
        "ingredientPattern": "T", "ingredients": {"T": {"type": "item", "code": "game:stone-chalk", "quantity": 1}},
        "width": 1, "height": 1, "output": {"type": "item", "code": "chalk", "quantity": 1}})
    for k, v in {"chalkmode-left": "Arrow pointing left", "chalkmode-right": "Arrow pointing right",
                 "chalkmode-cross": "Cross: dead end", "chalkmode-circle": "Circle: been here",
                 # Messages
                 "dispenser-stock": "{0} left",
                 "dispenser-restocks": "Sold out. It restocks once a week.",
                 "tripwire": "Something snags at your ankle. The floor gives way, and you smell fryer oil.",
                 "itemdesc-scrapwire": "Copper wire. Melted down in a crucible it casts like any copper: two copper bits' worth.",
                 "itemdesc-metalbracket": "Steel, from a ceiling grid or a light fixture. Two can be bent into nails and strips.",
                 "vending-snackrooms": "The machine swallows your hand to the elbow, whirs, and pulls. You smell fryer oil.",
                 "blockhelp-elevator": "Ride the elevator", "blockhelp-door": "Try the door",
                 "blockhelp-exit": "Go through",
                 # Names and descriptions the older content was missing
                 "block-concretefloor-linens": "Painted Concrete Floor", "block-concretefloor-linewe": "Painted Concrete Floor",
                 "block-concretefloor-dashwe": "Painted Concrete Floor", "block-concretefloor-dashns": "Painted Concrete Floor",
                 "itemdesc-crackers": "Dry, salty and years past their date. Still food.",
                 "itemdesc-cannedbeans": "A dented can of beans. Somebody always leaves one behind.",
                 # Shown as you enter each level
                 "level-0": "Level 0: The Lobby", "level-1": "Level 1: The Habitable Zone", "level-2": "Level 2: Pipe Dreams",
                 "level-3": "Level 3: The Electrical Station", "level-4": "Level 4: The Abandoned Office",
                 "level-5": "Level 5: The Terror Hotel", "level-6": "Level 6: Lights Out", "level-61": "Level 6.1: The Snackrooms",
                 "level-7": "Level 7: Thalassophobia", "level-8": "Level 8: Cave Systems", "level-9": "Level 9: The Suburbs",
                 "level-10": "Level 10: Bumper Crop",
                 "levelhint-6": "Light barely carries here. Hold the brightest light you have, and mark your way with chalk.",
                 "levelhint-61": "Bright, warm and safe, for now. Every way out leads somewhere different.",
                 "levelhint-7": "The deeper you dive, the darker and less stable it gets.",
                 "levelhint-8": "Stay near the lamps of the 9th Road. Things move in the dark.",
                 "levelhint-10": "The soil is thin. Don't dig too deep.",
                 }.items():
        LANG[k] = v


# ======================= Level 6.1 =======================

def level61():
    cube_block("snackfloor", {"terrazzo": "Terrazzo", "checker": "Chequered Tiles", "quarry": "Quarry Tiles"}, ["terrazzo", "checker", "quarry"],
               {"terrazzo": "snackfloor-terrazzo", "checker": "snackfloor-checker", "quarry": "snackfloor-quarry"})
    cube_block("snackwall", {"mall": "Mall Wall", "panel": "Wood Panelling", "tile": "Tiled Wall", "window": "Glowing Window"},
               ["mall", "panel", "tile", "window"],
               {"mall": "snackwall-mall", "panel": "snackwall-panel", "tile": "snackwall-tile", "window": "snackwall-window"},
               lightHsvByType={"*-window": [6, 3, 12]}, lightAbsorptionByType={"*-window": 0, "*": 99},
               vertexFlagsByType={"*-window": {"glowLevel": 200}},
               comment="Level 6.1's walls; its windows glow orange-white, like daylight")
    cube_block("snackceiling", {"grid": "Ceiling Panel", "skylight": "Skylight"}, ["grid", "skylight"],
               {"grid": "snackceiling-grid", "skylight": "snackceiling-skylight"},
               lightHsvByType={"*-skylight": [7, 2, 15]}, lightAbsorptionByType={"*-skylight": 0, "*": 99},
               comment="Skylights show only darkness above, yet light the food court like day")
    door_block("rustydoor", "Rusty Steel Door", "rustydoor", "rustydoor", comment="A rusty steel door marked EXIT. It leads back into Level 6, somewhere")
    door_block("glassdoors", "Sliding Glass Doors", "glassdoors", "glassdoor", material="Glass", sounds=GLASS, comment="Sliding glass doors onto somewhere else entirely")
    door_block("kitchendoor", "Kitchen Door", "kitchendoor", "kitchendoor", comment="A swinging kitchen door. It opens into another restaurant")
    block("ventgrate", {"creativeinventory": {"general": ["*"]}, "blockmaterial": "Metal", "drawtype": "cube",
                        "textures": {"all": {"base": "block/detail/ventgrate"}}, "behaviors": threshold("vent"),
                        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL}, "A vent big enough to crawl into")
    name("ventgrate", "Vent")

    wall_family("snackdeco", "Mall Wall", {1: "snackwall-mall"}, [
        Decor(code, english, {3: plate("Sign", (1, 3, -0.8), (15, 13, 0), code, "navy", glow=230)}, light=[0, 4, 8])
        for code, english in (("signburger", "Neon Sign"), ("signpizza", "Neon Sign"), ("signtaco", "Neon Sign"), ("signdonut", "Neon Sign"))
    ] + [
        Decor("menuboard", "Menu Board", {3: plate("Board", (1, 2, -0.6), (15, 14, 0), "menuboard", "wooddark", glow=60)}),
        Decor("mallmap", "Mall Directory", {2: plate("Map", (2, 1, -1), (14, 15, 0), "mallmap", "chrome", glow=40)}),
    ], material="Stone", sounds=STONE)

    snacks = drops(("chips", 0.8, 0.6), ("candybar", 0.8, 0.6), ("soda", 0.5, 0.5), ("crackers", 0.4, 0.4))
    prop("cafetable", "Cafeteria Table", [
        bx("Top", (1, 11, 1), (15, 12, 15), "navy"), bx("Post", (7, 1, 7), (9, 11, 9), "chrome"), bx("Foot", (4, 0, 4), (12, 1, 12), "chrome")],
         box=(0.06, 0, 0.06, 0.94, 0.78, 0.94), oriented=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5))})
    prop("cafechair", "Cafeteria Chair", [
        bx("Seat", (3.5, 7, 3.5), (12.5, 8, 12.5), "navy"), bx("Back", (3.5, 8, 11.5), (12.5, 16, 12.5), "navy"),
        bx("Leg1", (4, 0, 4), (5, 7, 5), "chrome"), bx("Leg2", (11, 0, 4), (12, 7, 5), "chrome"),
        bx("Leg3", (4, 0, 11), (5, 7, 12), "chrome"), bx("Leg4", (11, 0, 11), (12, 7, 12), "chrome")],
         box=(0.22, 0, 0.22, 0.78, 1, 0.78), material="Metal", sounds=METAL, extra={"drops": drops(("metalbracket", 0.6, 0.4))})
    counter = [bx("Base", (0, 0, 3), (16, 14, 16), "formica"), bx("Top", (0, 14, 2), (16, 15, 16), "chrome")]
    prop("snackcounter", "Snack Bar Counter", {
        "plain": counter,
        "register": counter + plate("Till", (4, 15, 6), (12, 20, 12), "register", "metaldark"),
        "display": counter + [bx("Case", (1, 15, 3), (15, 21, 15), "foodcase", faces=("north", "south", "up"), full=True),
                              bx("CaseSides", (1, 15, 3), (15, 21, 15), "chrome", faces=("east", "west"))]},
         box=(0, 0, 0.12, 1, 0.94, 1), material="Metal", sounds=METAL)
    prop("stove", "Griddle", [
        bx("Body", (0, 0, 2), (16, 14, 16), "chrome", faces=("east", "west", "south", "down")),
        bx("Front", (0, 0, 2), (16, 14, 16), "stovefront", faces=("north",), full=True),
        bx("Top", (0, 0, 2), (16, 14, 16), "stovetop", faces=("up",), full=True),
        bx("Splash", (0, 14, 14), (16, 18, 16), "chrome")], box=(0, 0, 0.12, 1, 0.88, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 0.8, 0.5), ("game:fat", 0.3, 0.3))})
    prop("fryer", "Deep Fryer", [
        bx("Body", (1, 0, 2), (15, 14, 16), "chrome", faces=("north", "east", "west", "south", "down")),
        bx("Oil", (1, 0, 2), (15, 14, 16), "fryertop", faces=("up",), full=True),
        bx("BasketL", (3, 14, 4), (7, 16, 10), "metaldark"), bx("BasketR", (9, 14, 4), (13, 16, 10), "metaldark"),
        bx("Handle", (4.5, 15, 1), (5.5, 16, 4), "rubber")], box=(0.06, 0, 0.12, 0.94, 0.88, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 0.6, 0.4), ("game:fat", 0.6, 0.4))})
    prop("snackshelf", "Snack Shelf", [
        bx("Stock", (1, 0, 8), (15, 28, 15), "snackshelf", faces=("north",), full=True),
        bx("Frame", (0.5, 0, 7.5), (15.5, 28, 16), "chrome", faces=("east", "west", "up", "south"))],
         box=(0.03, 0, 0.47, 0.97, 1.75, 1), material="Metal", sounds=METAL, extra={"drops": snacks})
    prop("snackvending", "Snack Machine", [
        bx("Body", (1, 0, 2), (15, 29, 15), "chrome", faces=("east", "west", "up", "south")),
        bx("Front", (1, 0, 2), (15, 29, 15), "snackvending", faces=("north",), full=True, glow=60)],
         box=(0.06, 0, 0.12, 0.94, 1.8, 0.94), material="Metal", sounds=METAL, light=[8, 2, 7],
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:chips", "backrooms:candybar", "backrooms:crackers", "backrooms:soda"], "restock": True}})
    prop("drinkfridge", "Drinks Fridge", [
        bx("Body", (1, 0, 2), (15, 30, 15), "chrome", faces=("east", "west", "up", "south")),
        bx("Door", (1, 0, 2), (15, 30, 15), "drinkfridge", faces=("north",), full=True, glow=50)],
         box=(0.06, 0, 0.12, 0.94, 1.88, 0.94), material="Metal", sounds=METAL, light=[30, 1, 6],
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:soda", "backrooms:waterbottle", "backrooms:almondwater", "backrooms:cashewwater"], "restock": True}})

    food("chips", "Bag of Chips", 160, "Grain", "Salty, crisp, and from nowhere.")
    food("candybar", "Chocolate Bar", 200, "Dairy", "Sweet enough to make you forget where you are, almost.")
    food("soda", "Can of Soda", 90, "NoNutrition", "Fizzy and far too sweet. Nobody knows who stocks the fridges.", stack=8)
    food("cashewwater", "Cashew Water", 140, "NoNutrition", "Like Almond Water, but nuttier. It steadies you a little, though not as much.",
         health=1, stack=8, extra={"class": "BackroomsAlmondWater", "attributes": {"stabilityRestored": 0.08}})
    food("waterbottle", "Bottle of Water", 100, "NoNutrition", "Plain water. Down here, that's rare.", health=1, stack=8)


# ======================= Level 7 =======================

def level7():
    cube_block("oceanceiling", {"plain": "Concrete Ceiling", "glow": "Concrete Ceiling"}, ["plain", "glow"],
               {"plain": "oceanceiling", "glow": "oceanceiling"}, lightHsvByType={"*-glow": [34, 1, 7]},
               lightAbsorptionByType={"*-glow": 0, "*": 99}, comment="The ceiling over the sea. The dim light seems to come from nowhere")
    cube_block("islandrock", "Strange Rock", ["plain"], {"plain": "islandrock"}, comment="The unknown rock of Level 7's islands",
               drops=[{"type": "item", "code": "game:stone-basalt", "quantity": {"avg": 3, "var": 1}}], resistance=6)
    block("tar", {"class": "BackroomsTar", "creativeinventory": {"general": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
                  "textures": {"all": {"base": "block/detail/tar"}}, "lightAbsorption": 99, "resistance": 3, "drops": [],
                  "sounds": {"walk": "game:walk/sludge*", "place": "game:effect/squish*", "break": "game:effect/squish*", "hit": "game:effect/squish*"},
                  "particleProperties": [{
                      "hsvaColor": [{"avg": 0, "var": 0}, {"avg": 0, "var": 0}, {"avg": 30, "var": 10}, {"avg": 200, "var": 40}],
                      "gravityEffect": {"avg": -0.02, "var": 0}, "posOffset": [{"avg": 0, "var": 0.4}, {"avg": 0.05, "var": 0}, {"avg": 0, "var": 0.4}],
                      "velocity": [{"avg": 0, "var": 0.02}, {"avg": 0.05, "var": 0.02}, {"avg": 0, "var": 0.02}], "quantity": {"avg": 0.05},
                      "size": {"avg": 0.2, "var": 0.1}, "sizeEvolve": {"transform": "linear", "factor": 0.5}, "particleModel": "Cube",
                      "lifeLength": {"avg": 0.8, "var": 0.3}, "selfPropelled": True}]},
          "Scalding, steadily bubbling tar")
    name("tar", "Tar")

    prop("bonepile", "Bones", [bx(f"Bone{i}", (x, 0, z), (x + w, 1.5, z + d), "bone") for i, (x, z, w, d) in
                               enumerate(((2, 3, 9, 1.5), (5, 8, 1.5, 7), (9, 6, 6, 1.5), (3, 11, 7, 1.2), (11, 10, 1.4, 5)))] +
         [bx("Skull", (10, 0, 2), (14, 4, 6), "bone")], box=(0.1, 0, 0.1, 0.9, 0.25, 0.9), oriented=False, collide=False,
         material="Stone", sounds=STONE, extra={"drops": drops(("game:bone", 2, 1))})
    prop("scrapmetal", "Rusted Scrap", [
        bx("Plate1", (1, 0, 2), (12, 1, 10), "scrap", rot=(0, 20, 8)), bx("Plate2", (5, 0, 7), (15, 2, 14), "scrap", rot=(6, -15, 0)),
        bx("Rod", (2, 0.5, 12), (14, 1.5, 13), "rust")], box=(0.06, 0, 0.06, 0.94, 0.2, 0.94), oriented=False, collide=False,
         material="Metal", sounds=METAL, extra={"drops": drops(("metalbracket", 0.8, 0.5), ("scrapwire", 0.5, 0.5))})
    prop("jawskeleton", "Skeleton", [
        bx("Spine", (7.5, 0.5, 2), (8.5, 1.5, 14), "bone"),
        bx("Ribs1", (4, 0, 5), (12, 2.5, 6), "bone"), bx("Ribs2", (4, 0, 7), (12, 2.5, 8), "bone"), bx("Ribs3", (4.5, 0, 9), (11.5, 2.2, 10), "bone"),
        bx("Skull", (5.5, 0, -2), (10.5, 4, 2), "bone"), bx("Jaw", (4.5, 0, -6), (11.5, 1.5, -1), "bone"),
        bx("Teeth", (5, 1.5, -6), (11, 2.3, -4), "bone"),
        bx("ArmL", (2, 0, 4), (3, 1, 12), "bone"), bx("ArmR", (13, 0, 4), (14, 1, 12), "bone"),
        bx("LegL", (6, 0, 14), (7, 1, 24), "bone"), bx("LegR", (9, 0, 14), (10, 1, 24), "bone")],
         box=(0.1, 0, 0, 0.9, 0.25, 1), collide=False, material="Stone", sounds=STONE, extra={"drops": drops(("game:bone", 3, 1))})
    rib = []
    for i, z in enumerate((2, 6, 10, 14)):
        rib += [bx(f"RibL{i}", (-2, 0, z), (0, 28, z + 1.5), "bone", rot=(0, 0, -12), origin=(-1, 0, z)),
                bx(f"RibR{i}", (16, 0, z), (18, 28, z + 1.5), "bone", rot=(0, 0, 12), origin=(17, 0, z))]
    prop("ribcage", "Enormous Ribs", rib + [bx("Spine", (4, 28, 0), (12, 31, 16), "bone")], box=(0, 0, 0, 1, 0.25, 1), collide=False,
         material="Stone", sounds=STONE)
    prop("backpack", "Lost Backpack", [
        bx("Bag", (4, 0, 5), (12, 9, 11), "canvas"), bx("Flap", (4, 7, 4.5), (12, 10, 11), "canvas"),
        bx("Pocket", (5, 1, 4), (11, 5, 5), "canvas"), bx("StrapL", (5, 0, 11), (6, 8, 12), "rubber"), bx("StrapR", (10, 0, 11), (11, 8, 12), "rubber")],
         box=(0.25, 0, 0.25, 0.75, 0.62, 0.75), material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("almondwater", 1, 0.8), ("crackers", 0.6, 0.5), ("game:candle", 0.4, 0.4), ("game:rope", 0.3, 0.3),
                                ("game:knife-generic-copper", 0.1, 0), ("game:bandage-clean", 0.4, 0.4), ("chalk", 0.2, 0),
                                ("game:fishingbait-dough", 0.5, 0.3))})
    prop("wreckcrate", "Waterlogged Crate", [bx("Crate", (1, 0, 1), (15, 13, 15), "wetwood")],
         box=(0.06, 0, 0.06, 0.94, 0.82, 0.94), oriented=False, sounds=WOOD,
         extra={"drops": drops(("game:plank-aged", 2, 1), ("game:rope", 0.6, 0.4), ("game:metalnailsandstrips-iron", 0.5, 0.4),
                                ("game:boat-raft-aged", 0.06, 0), ("game:fishingpole-simple-wood", 0.08, 0), ("cannedbeans", 0.5, 0.5))})


# ======================= Level 8 =======================

def level8():
    prop("megmarker", "M.E.G. Marker", [
        bx("Post", (7, 0, 7), (9, 22, 9), "wood"),
        bx("Plate", (2, 14, 6.4), (14, 24, 7), "megplate", faces=("north", "south"), full=True),
        bx("PlateEdge", (2, 14, 6.4), (14, 24, 7), "metaldark", faces=("east", "west", "up", "down"))],
         box=(0.4, 0, 0.4, 0.6, 1.5, 0.6), comment="An M.E.G. marker on the 9th Road")
    prop("roadlamp", "Road Lamp", [
        bx("Pole", (7.5, 0, 7.5), (8.5, 22, 8.5), "metaldark"), bx("Cap", (5.5, 27, 5.5), (10.5, 28, 10.5), "metaldark"),
        bx("Lantern", (6, 22, 6), (10, 27, 10), "lampglass", glow=230), bx("Base", (6, 0, 6), (10, 1, 10), "metaldark")],
         box=(0.4, 0, 0.4, 0.6, 1.75, 0.6), oriented=False, material="Metal", sounds=METAL, light=[7, 4, 13])
    prop("stonehand", "Stone Hand", [
        bx("Wrist", (6, 0, 6), (10, 8, 10), "cavestone"), bx("Palm", (5, 8, 6.5), (11, 15, 9.5), "cavestone"),
        bx("F1", (5, 15, 7), (6.4, 21, 8.6), "cavestone"), bx("F2", (6.7, 15, 7), (8.1, 22.5, 8.6), "cavestone"),
        bx("F3", (8.4, 15, 7), (9.8, 22, 8.6), "cavestone"), bx("F4", (10.1, 15, 7), (11.3, 20, 8.6), "cavestone"),
        bx("Thumb", (3, 10, 7), (5, 15, 8.6), "cavestone", rot=(0, 0, 25), origin=(5, 10, 8))],
         box=(0.3, 0, 0.35, 0.7, 1.4, 0.65), material="Stone", sounds=STONE, comment="A speleothem in the shape of a human hand, fingerprints and all")
    prop("stonestapler", "Stone Stapler", [
        bx("Base", (3, 0, 5), (13, 3, 11), "cavestone"), bx("Arm", (3, 3, 5.5), (13, 6, 10.5), "cavestone", rot=(0, 0, 6), origin=(13, 3, 8)),
        bx("Hinge", (11, 2, 6), (14, 6, 10), "cavestone")], box=(0.18, 0, 0.3, 0.88, 0.4, 0.7), oriented=False,
         material="Stone", sounds=STONE, comment="Rock that has formed, impossibly, into a stapler")


# ======================= Level 9 =======================

def level9():
    road = {"plain": "Asphalt", "leaves": "Asphalt", "wet": "Wet Asphalt", "line": "Road Marking", "linens": "Road Marking",
            "crossing": "Zebra Crossing", "crossingns": "Zebra Crossing", "manhole": "Manhole Cover",
            # Level 11's avenues and streets
            "doublens": "Road Marking", "doublewe": "Road Marking", "bayns": "Road Marking", "baywe": "Road Marking",
            "cracked": "Cracked Asphalt"}
    cube_block("asphalt", road, list(road), {k: "asphalt" if k == "plain" else f"asphalt-{k}" for k in road})
    cube_block("sidewalk", "Pavement", ["plain"], {"plain": "sidewalk"})
    floors = {"wood": "Floorboards", "carpet": "Carpet", "tile": "Bathroom Tiles", "lino": "Linoleum", "garage": "Concrete",
              "porch": "Porch Boards", "driveway": "Concrete", "rug": "Rug"}
    cube_block("housefloor", floors, list(floors), {k: f"housefloor-{k}" for k in floors},
               material="Wood", sounds=WOOD)
    # Exterior walls: siding on the outside face, plaster on the others
    tex_by = {}
    for siding in ("white", "blue", "yellow", "green", "brick"):
        for s in SIDES:
            faces = {f: {"base": "block/detail/plaster-interior"} for f in ("north", "east", "south", "west", "up", "down")}
            faces[s] = {"base": f"block/detail/siding-{siding}"}
            tex_by[f"*-{siding}-{s}"] = faces
    block("housewall", {"variantgroups": [{"code": "siding", "states": ["white", "blue", "yellow", "green", "brick"]}, {"code": "side", "states": SIDES}],
                        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]}, "blockmaterial": "Wood", "drawtype": "cube",
                        "texturesByType": tex_by, "lightAbsorption": 99, "resistance": 4, "sounds": WOOD},
          "House walls: siding outside, plaster inside")
    name("housewall-*", "House Wall")
    cube_block("houseinterior", {"floral": "Wallpaper", "stripe": "Wallpaper", "beige": "Wallpaper", "green": "Wallpaper", "tile": "Tiled Wall"},
               ["floral", "stripe", "beige", "green", "tile"],
               {k: f"houseinterior-{k}" for k in ("floral", "stripe", "beige", "green", "tile")}, material="Wood", sounds=WOOD)
    cube_block("housewindow", {"dark": "Window", "lit": "Lit Window"}, ["dark", "lit"], {"dark": "housewindow-dark", "lit": "housewindow-lit"},
               material="Glass", sounds=GLASS, lightHsvByType={"*-lit": [6, 4, 9]}, lightAbsorptionByType={"*": 0},
               vertexFlagsByType={"*-lit": {"glowLevel": 160}}, drops=[])
    cube_block("houseroof", {"grey": "Roof Shingles", "brown": "Roof Shingles", "red": "Roof Shingles"}, ["grey", "brown", "red"],
               {"grey": "houseroof-grey", "brown": "houseroof-brown", "red": "houseroof-red"}, material="Wood", sounds=WOOD)
    cube_block("houseceiling", {"plain": "Ceiling", "lightoff": "Ceiling Light", "lighton": "Ceiling Light"}, ["plain", "lightoff", "lighton"],
               {"plain": "houseceiling", "lightoff": "houseceiling-lightoff", "lighton": "houseceiling-lighton"}, material="Wood", sounds=WOOD,
               lightHsvByType={"*-lighton": [6, 3, 12]}, vertexFlagsByType={"*-lighton": {"glowLevel": 120}})
    door_block("housedoor", "Front Door", "housedoor", "locked", material="Wood", sounds=WOOD, comment="A front door, locked")
    door_block("garagedoor", "Garage Door", "garagedoor", "locked", comment="A closed garage door, locked")

    kitchen = drops(("game:salt", 0.5, 0.5), ("game:flour-spelt", 0.5, 0.5), ("cannedbeans", 0.6, 0.5), ("game:knife-generic-copper", 0.12, 0),
                    ("game:fat", 0.3, 0.3), ("crackers", 0.4, 0.4), ("game:candle", 0.2, 0.2))
    prop("kitchencabinet", "Kitchen Cupboard", [
        bx("Base", (0, 0, 3), (16, 14, 16), "cabinetfront", faces=("north",), full=True),
        bx("Sides", (0, 0, 3), (16, 14, 16), "dresserwood", faces=("east", "west", "south")),
        bx("Top", (0, 14, 2), (16, 15, 16), "formica")], box=(0, 0, 0.12, 1, 0.94, 1), extra={"drops": kitchen})
    prop("pantryshelf", "Pantry Shelf", [
        bx("Stock", (1, 0, 8), (15, 28, 15), "pantry", faces=("north",), full=True),
        bx("Frame", (0.5, 0, 7.5), (15.5, 28, 16), "wood", faces=("east", "west", "up", "south"))], box=(0.03, 0, 0.47, 0.97, 1.75, 1),
         extra={"drops": drops(("cannedbeans", 1.2, 0.8), ("game:flour-spelt", 0.6, 0.5), ("game:salt", 0.6, 0.5), ("game:honeycomb", 0.15, 0))})
    prop("toolshelf", "Tool Shelf", [
        bx("Tools", (1, 0, 9), (15, 28, 15), "toolwall", faces=("north",), full=True),
        bx("Frame", (0.5, 0, 8.5), (15.5, 28, 16), "metal", faces=("east", "west", "up", "south"))], box=(0.03, 0, 0.53, 0.97, 1.75, 1),
         material="Metal", sounds=METAL,
         extra={"drops": drops(("game:hammer-copper", 0.15, 0), ("game:saw-copper", 0.1, 0), ("game:shovel-copper", 0.12, 0),
                                ("game:metalnailsandstrips-iron", 0.8, 0.6), ("game:rope", 0.5, 0.4), ("scrapwire", 0.6, 0.5))})
    prop("dresser", "Dresser", [
        bx("Body", (1, 0, 4), (15, 15, 15), "dresserwood", faces=("east", "west", "up", "south")),
        bx("Front", (1, 0, 4), (15, 15, 15), "dresserfront", faces=("north",), full=True)], box=(0.06, 0, 0.25, 0.94, 0.94, 0.94),
         extra={"drops": drops(("game:cloth-plain", 0.8, 0.6), ("game:flaxtwine", 0.6, 0.5), ("game:candle", 0.2, 0.2))})
    prop("tv", "Television", [
        bx("Cabinet", (2, 0, 4), (14, 12, 14), "tvwood", faces=("east", "west", "up", "south")),
        bx("Screen", (2, 0, 4), (14, 12, 14), "tvscreen", faces=("north",), full=True),
        bx("AntennaL", (5, 12, 9), (5.6, 18, 9.6), "metal", rot=(0, 0, 20), origin=(5.3, 12, 9.3)),
        bx("AntennaR", (10.4, 12, 9), (11, 18, 9.6), "metal", rot=(0, 0, -20), origin=(10.7, 12, 9.3))], box=(0.12, 0, 0.25, 0.88, 0.75, 0.88),
         extra={"drops": drops(("glassshard", 1, 0.5), ("scrapwire", 1, 0.5), ("rottenwood", 0.5, 0.4))})
    tub = [bx("Bottom", (1, 0, 0), (15, 2, 16), "enamel"), bx("SideL", (1, 2, 0), (2, 8, 16), "enamel"), bx("SideR", (14, 2, 0), (15, 8, 16), "enamel")]
    prop("bathtub", "Bathtub", {"head": tub + [bx("End", (1, 2, 0), (15, 8, 1), "enamel"), bx("Tap", (7, 8, 0.5), (9, 10, 3), "chrome")],
                                "foot": tub + [bx("End", (1, 2, 15), (15, 8, 16), "enamel")]},
         box=(0.06, 0, 0, 0.94, 0.5, 1), material="Ceramic", sounds=STONE)
    prop("toilet", "Toilet", [
        bx("Base", (5, 0, 5), (11, 7, 12), "enamel"), bx("Seat", (4, 7, 3), (12, 8, 12), "enamel"),
        bx("Tank", (4, 7, 12), (12, 16, 15), "enamel"), bx("Lid", (3.5, 16, 11.5), (12.5, 17, 15.5), "enamel")],
         box=(0.22, 0, 0.18, 0.78, 1, 0.97), material="Ceramic", sounds=STONE, extra={"drops": []})
    street = [bx("Pole", (7, 0, 7), (9, 62, 9), "metaldark"), bx("Base", (6, 0, 6), (10, 3, 10), "metaldark"),
              bx("Arm", (7.5, 60, -2), (8.5, 61.5, 8), "metaldark"), bx("Head", (5.5, 58, -6), (10.5, 60.5, 1), "metaldark")]
    prop("streetlight", "Street Light", {
        "on": street + [bx("Lens", (6, 57.6, -5.5), (10, 58, 0.5), "streetlamp", glow=240)],
        "off": street + [bx("Lens", (6, 57.6, -5.5), (10, 58, 0.5), "streetlampoff")],
        "flicker": street + [bx("Lens", (6, 57.6, -5.5), (10, 58, 0.5), "streetlamp", glow=240)]},
         box=(0.4, 0, 0.4, 0.6, 2, 0.6), material="Metal", sounds=METAL,
         extra={"lightHsvByType": {"*-on-*": [6, 3, 15]}, "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
                "attributesByType": {f"*-flicker-{s}": {"offBlock": f"backrooms:streetlight-off-{s}"} for s in SIDES}})
    prop("mailbox", "Mailbox", [
        bx("Post", (7.5, 0, 7.5), (8.5, 12, 8.5), "wood"), bx("Box", (5, 12, 4), (11, 17, 13), "mailbox"),
        bx("Flag", (11, 14, 9), (11.5, 19, 10), "redmetal")], box=(0.3, 0, 0.25, 0.7, 1.1, 0.8), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 0.6, 0.4), ("game:paper-parchment", 0.4, 0.4))})
    prop("seedsacks", "Seed Sacks", [
        bx("Sack1", (1, 0, 2), (8, 9, 8), "burlap"), bx("Sack2", (8.5, 0, 3), (15, 8, 9), "burlap"), bx("Sack3", (3, 0, 9), (10, 7, 15), "burlap"),
        bx("Tie", (3.5, 9, 4), (5.5, 10.5, 6), "string")], box=(0.06, 0, 0.12, 0.94, 0.6, 0.94), oriented=False, material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("game:seeds-carrot", 1, 1), ("game:seeds-onion", 0.8, 0.8), ("game:seeds-turnip", 0.8, 0.8),
                                ("game:seeds-cabbage", 0.6, 0.6), ("game:seeds-spelt", 1, 1), ("game:seeds-flax", 0.8, 0.8), ("game:seeds-parsnip", 0.5, 0.5))})
    prop("fieldgate", "Field Gate", [
        bx("PostL", (0, 0, 7), (2, 18, 9), "wood"), bx("PostR", (14, 0, 7), (16, 18, 9), "wood"),
        bx("Rail1", (1, 4, 9), (2, 5, 23), "wood"), bx("Rail2", (1, 10, 9), (2, 11, 23), "wood"), bx("Rail3", (1, 15, 9), (2, 16, 23), "wood"),
        bx("Brace", (1, 4, 10), (2, 16, 11), "wood"), bx("End", (1, 3, 21.5), (2, 17, 23), "wood")],
         box=(0, 0, 0.4, 0.13, 1.1, 0.6), comment="A gate left open onto the fields. Walk through it and you'll be in Level 10")


# ======================= Level 10 =======================

def level10():
    cube_block("dirtroad", {"plain": "Dirt Road", "tracks": "Dirt Road"}, ["plain", "tracks"], {"plain": "dirtroad", "tracks": "dirtroad-tracks"},
               material="Soil", sounds={"walk": "game:walk/gravel", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"},
               comment="Packed dirt roads with tyre tracks; nothing grows on them")
    cube_block("barnwall", {"red": "Barn Boards", "grey": "Weathered Boards"}, ["red", "grey"], {"red": "barnwall-red", "grey": "barnwall-grey"},
               material="Wood", sounds=WOOD)
    cube_block("barnroof", "Barn Roof", ["dark"], {"dark": "barnroof"}, material="Wood", sounds=WOOD)
    # Ploughed soil under the crops. Its code must start with "farmland": vanilla crops stop growing (and so stay
    # ripe instead of cycling back to seedlings) only on blocks whose code does
    block("farmland", {"variantgroups": [{"code": "state", "states": ["old"]}], "creativeinventory": {"general": ["*"]},
                       "blockmaterial": "Soil", "drawtype": "cube",
                       "textures": {"all": {"base": "game:block/soil/fertmedium"}, "up": {"base": "game:block/soil/farmland/fertmedium-dry"}},
                       "lightAbsorption": 99, "resistance": 1, "fertility": 60,  # (or the flowers in the beds pop off)
                       "drops": [{"type": "block", "code": "game:soil-medium-none", "quantity": {"avg": 1, "var": 0}}],
                       "sounds": {"walk": "game:walk/grass", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"}},
          "Old ploughed soil under the crops of Level 10")
    name("farmland-*", "Ploughed Soil")
    block("wormmass", {"class": "BackroomsWorms", "creativeinventory": {"general": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
                       "textures": {"all": {"base": "block/detail/wormmass"}}, "lightAbsorption": 99, "resistance": 1.2,
                       "drops": [{"type": "item", "code": "game:creature-earthworm", "quantity": {"avg": 1, "var": 1}}],
                       "sounds": {"walk": "game:walk/sludge*", "place": "game:effect/squish*", "break": "game:effect/squish*", "hit": "game:effect/squish*"}},
          "The mass of worms writhing a metre under Level 10. Digging into it is a mistake")
    name("wormmass", "Writhing Worms")
    prop("feedtrough", "Feed Trough", [
        bx("Body", (0, 0, 4), (16, 7, 12), "wood", faces=("north", "east", "south", "west", "down")),
        bx("Feed", (1, 5, 5), (15, 6, 11), "feed", faces=("up",)), bx("Legs", (1, 0, 5), (15, 2, 11), "wooddark")],
         box=(0, 0, 0.25, 1, 0.44, 0.75), sounds=WOOD, extra={"drops": drops(("game:plank-aged", 1.5, 0.5), ("game:drygrass", 1, 1))})
    prop("toolrack", "Tool Rack", [
        bx("Board", (0, 4, 14), (16, 26, 16), "toolwall", faces=("north",), full=True),
        bx("BoardSides", (0, 4, 14), (16, 26, 16), "wood", faces=("east", "west", "up", "down", "south")),
        bx("Handle1", (3, 2, 12), (4, 26, 13), "wood"), bx("Head1", (1, 2, 11), (6, 4, 13), "metaldark"),
        bx("Handle2", (11, 6, 12), (12, 28, 13), "wood"), bx("Head2", (9, 24, 11.5), (16, 26, 13), "metaldark")],
         box=(0, 0, 0.7, 1, 1.75, 1), extra={"drops": drops(("game:hoe-copper", 0.3, 0), ("game:scythe-copper", 0.2, 0), ("game:shovel-copper", 0.2, 0),
                                                              ("game:rope", 0.5, 0.4))})
    prop("nailbarrel", "Barrel of Nails", [
        bx("Barrel", (2, 0, 2), (14, 14, 14), "barrelwood", faces=("north", "east", "south", "west", "down")),
        bx("Nails", (2.5, 12, 2.5), (13.5, 13, 13.5), "nails", faces=("up",))], box=(0.12, 0, 0.12, 0.88, 0.88, 0.88), oriented=False,
         extra={"drops": drops(("game:metalnailsandstrips-iron", 2, 1), ("game:plank-aged", 1, 1))})


# ======================= Refinements: Levels 5 to 10 in more detail =======================

def refinements():
    # Blocks
    cube_block("fieldstubble", "Stubble", ["plain"], {"plain": "stubble"}, material="Soil",
               sounds={"walk": "game:walk/grass", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"})
    cube_block("pool", {"floor": "Pool Tiles", "coping": "Pool Coping"}, ["floor", "coping"], {"floor": "pool-floor", "coping": "pool-coping"})
    cube_block("jetty", "Jetty Boards", ["planks"], {"planks": "jetty"}, material="Wood", sounds=WOOD)
    cube_block("silo", {"wall": "Silo", "top": "Silo Roof"}, ["wall", "top"], {"wall": "silo", "top": "silotop"}, material="Metal", sounds=METAL)
    cube_block("chimney", "Chimney", ["brick"], {"brick": "siding-brick"})

    # Pitched roofs: half a block of rise for every block of run, in a lower and an upper half, sloping down toward
    # the side named. A slab of shingles tilted to the slope, with a board under its edges.
    slope = math.degrees(math.atan2(8, 16))
    run = math.hypot(16, 8)
    materials = {"grey": "houseroof-grey", "brown": "houseroof-brown", "red": "houseroof-red", "barn": "barnroof"}
    shapes = {}
    for mat, tex in materials.items():
        trim = "wooddark" if mat == "barn" else "white"
        for half, y in (("lower", 0), ("upper", 8)):
            # Built sloping down to the north: low edge at z = 0, high edge at z = 16. Under the slab, boards fill
            # the gap down to the block below in steps, so a gable end reads as a boarded triangle
            fill = [bx(f"Fill{k}", (0, 0, 4 * k), (16, y + 2 * k, 4 * k + 4), trim, faces=("north", "east", "west", "up"))
                    for k in range(4) if y + 2 * k > 0]
            shapes[(mat, half)] = shape(f"roofslope-{mat}-{half}", fill + [
                bx("Slab", (0, y, 0), (16, y + 1.6, run), tex, faces=("up", "down"), rot=(-slope, 0, 0), origin=(0, y, 0)),
                bx("Edge", (0, y, 0), (16, y + 1.6, run), "wooddark", faces=("north", "south", "east", "west"), rot=(-slope, 0, 0), origin=(0, y, 0))])
    roof_by = {}
    for (mat, half), path in shapes.items():
        for s in SIDES:
            roof_by[f"*-{mat}-{half}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("roofslope", {"variantgroups": [{"code": "material", "states": list(materials)}, {"code": "half", "states": ["lower", "upper"]},
                                          {"code": "side", "states": SIDES}],
                        "creativeinventory": {"general": ["*-lower-north", "*-upper-north"], "construction": ["*-lower-north", "*-upper-north"]},
                        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": roof_by,
                        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 2,
                        "collisionboxByType": {"*-lower-*": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, "*": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
                        "selectionboxByType": {"*-lower-*": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, "*": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
                        "sounds": WOOD},
          "Pitched roofs over the Suburbs' houses and the farm buildings")
    name("roofslope-barn-*", "Barn Roof")
    name("roofslope-*", "Roof Shingles")

    # The corners of houses: siding on both outside faces
    corner_by = {}
    for siding in ("white", "blue", "yellow", "green", "brick"):
        for corner, faces in (("ne", ("north", "east")), ("nw", ("north", "west")), ("se", ("south", "east")), ("sw", ("south", "west"))):
            tex = {f: {"base": "block/detail/plaster-interior"} for f in ("north", "east", "south", "west", "up", "down")}
            for f in faces:
                tex[f] = {"base": f"block/detail/siding-{siding}"}
            corner_by[f"*-{siding}-{corner}"] = tex
    block("housecorner", {"variantgroups": [{"code": "siding", "states": ["white", "blue", "yellow", "green", "brick"]}, {"code": "corner", "states": ["ne", "nw", "se", "sw"]}],
                          "creativeinventory": {"general": ["*-ne"], "construction": ["*-ne"]}, "blockmaterial": "Wood", "drawtype": "cube",
                          "texturesByType": corner_by, "lightAbsorption": 99, "resistance": 4, "sounds": WOOD},
          "The corners of houses: siding on both outside faces")
    name("housecorner-*", "House Wall")

    # Pictures, clocks and mirrors on the inside walls of the houses, one family per wallpaper
    for paper in ("floral", "stripe", "beige", "green"):
        wall_family(f"housedeco-{paper}", "Wallpaper", {1: f"houseinterior-{paper}"}, [
            Decor("familyphoto", "Family Photo", {2: plate("Photo", (4, 3, -0.6), (12, 13, 0), "familyphoto", "wooddark")}),
            Decor("housepainting", "Painting", {2: plate("Picture", (2, 3, -0.6), (14, 13, 0), "landscape", "wooddark")}),
            Decor("houseclock", "Wall Clock", {2: plate("Clock", (4, 4, -0.8), (12, 12, 0), "clockface", "wooddark")}),
            Decor("housemirror", "Mirror", {2: plate("Mirror", (4, 1, -0.4), (12, 15, 0), "mirrorglass", "chrome")}),
        ], material="Wood", sounds=WOOD)

    # Level 9: the street and the yards
    prop("firehydrant", "Fire Hydrant", [
        bx("Body", (5, 0, 5), (11, 11, 11), "redmetal"), bx("Cap", (6, 11, 6), (10, 13, 10), "redmetal"),
        bx("NozzleL", (3, 6, 7), (5, 8.5, 9), "metaldark"), bx("NozzleR", (11, 6, 7), (13, 8.5, 9), "metaldark"),
        bx("Front", (7, 5, 3.5), (9, 8, 5), "metaldark")], box=(0.3, 0, 0.3, 0.7, 0.81, 0.7), material="Metal", sounds=METAL)
    prop("stopsign", "Stop Sign", [
        bx("Pole", (7.5, 0, 7.5), (8.5, 26, 8.5), "metal"),
        bx("Sign", (2, 24, 7), (14, 36, 7.6), "stopsign", faces=("north",), full=True),
        bx("Back", (2, 24, 7.6), (14, 36, 8), "metal", faces=("south", "east", "west", "up", "down"))],
         box=(0.42, 0, 0.42, 0.58, 2, 0.58), material="Metal", sounds=METAL)
    prop("wheeliebin", "Wheelie Bin", [
        bx("Body", (3, 1, 3), (13, 15, 13), "binplastic"), bx("Lid", (2.5, 15, 2.5), (13.5, 16, 14), "binplastic"),
        bx("WheelL", (3, 0, 12), (5, 2, 14), "rubber"), bx("WheelR", (11, 0, 12), (13, 2, 14), "rubber")],
         box=(0.18, 0, 0.18, 0.82, 1, 0.88), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:paper-parchment", 0.3, 0.3), ("rottenwood", 0.4, 0.3), ("scrapwire", 0.3, 0.3))})
    prop("basketballhoop", "Basketball Hoop", [
        bx("Pole", (7, 0, 12), (9, 48, 14), "metaldark"), bx("Arm", (7.5, 46, 9), (8.5, 47, 12), "metaldark"),
        bx("Board", (2, 44, 8.6), (14, 53, 9), "backboard", faces=("north",), full=True),
        bx("BoardBack", (2, 44, 9), (14, 53, 9.4), "white", faces=("south", "east", "west", "up", "down")),
        bx("RimN", (5, 44, 3), (11, 44.5, 3.5), "orange"), bx("RimS", (5, 44, 8), (11, 44.5, 8.6), "orange"),
        bx("RimW", (5, 44, 3), (5.5, 44.5, 8.6), "orange"), bx("RimE", (10.5, 44, 3), (11, 44.5, 8.6), "orange"),
        bx("Net", (5.5, 40, 3.5), (10.5, 44, 8), "string")],
         box=(0.43, 0, 0.75, 0.57, 2, 0.88), material="Metal", sounds=METAL)
    prop("swingset", "Swing Set", [
        bx("LegNW", (0.5, 0, 3), (1.5, 30, 4), "metaldark", rot=(-10, 0, 0), origin=(1, 0, 3.5)),
        bx("LegSW", (0.5, 0, 12), (1.5, 30, 13), "metaldark", rot=(10, 0, 0), origin=(1, 0, 12.5)),
        bx("LegNE", (14.5, 0, 3), (15.5, 30, 4), "metaldark", rot=(-10, 0, 0), origin=(15, 0, 3.5)),
        bx("LegSE", (14.5, 0, 12), (15.5, 30, 13), "metaldark", rot=(10, 0, 0), origin=(15, 0, 12.5)),
        bx("Bar", (0, 29, 7.5), (16, 30.5, 8.5), "metaldark"),
        bx("ChainA1", (3.5, 7, 7.8), (3.8, 29, 8.2), "steel"), bx("ChainA2", (6.2, 7, 7.8), (6.5, 29, 8.2), "steel"),
        bx("SeatA", (3, 6.5, 6.5), (7, 7, 9.5), "rubber"),
        bx("ChainB1", (9.5, 9, 7.8), (9.8, 29, 8.2), "steel"), bx("ChainB2", (12.2, 9, 7.8), (12.5, 29, 8.2), "steel"),
        bx("SeatB", (9, 8.5, 6.5), (13, 9, 9.5), "rubber")],
         box=(0, 0, 0.2, 1, 1.9, 0.8), material="Metal", sounds=METAL)
    prop("grill", "Barbecue Grill", [
        bx("Bowl", (4, 10, 4), (12, 15, 12), "blackmetal"), bx("Lid", (4.5, 15, 4.5), (11.5, 17.5, 11.5), "blackmetal"),
        bx("Handle", (7, 17.5, 7.5), (9, 18.5, 8.5), "wood"),
        bx("Leg1", (5, 0, 5), (6, 10, 6), "metal"), bx("Leg2", (10, 0, 5), (11, 10, 6), "metal"), bx("Leg3", (7.5, 0, 10), (8.5, 10, 11), "metal"),
        bx("Shelf", (4.5, 4, 4.5), (11.5, 4.5, 11.5), "metal")],
         box=(0.25, 0, 0.25, 0.75, 1.12, 0.75), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("game:charcoal", 1, 1))})
    laundry = [bx("Body", (1, 0, 2), (15, 15, 15), "fridgewhite", faces=("east", "west", "up", "south")),
               bx("Front", (1, 0, 2), (15, 15, 15), "washerfront", faces=("north",), full=True)]
    name("laundry-dryer-*", "Tumble Dryer")  # (before the general name, which would otherwise match first)
    prop("laundry", "Washing Machine", {"washer": laundry, "dryer": laundry},
         box=(0.06, 0, 0.12, 0.94, 0.94, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 1, 0.5), ("game:cloth-plain", 0.4, 0.4))})
    prop("toybox", "Toy Box", [
        bx("Box", (2, 0, 4), (14, 8, 12), "toybox", faces=("north", "south")), bx("Sides", (2, 0, 4), (14, 8, 12), "wood", faces=("east", "west", "down")),
        bx("Lid", (1.5, 8, 3.5), (14.5, 9, 12.5), "wood")],
         box=(0.12, 0, 0.25, 0.88, 0.56, 0.75), extra={"drops": drops(("game:cloth-plain", 0.5, 0.4), ("game:candle", 0.2, 0.2))})
    prop("doghouse", "Dog House", [
        bx("Body", (2, 0, 2), (14, 10, 14), "wood"), bx("Door", (6, 0, 1.8), (10, 7, 2), "blackmetal", faces=("north",)),
        bx("RoofW", (1, 9, 1), (8.5, 10.5, 15), "barnroof", rot=(0, 0, 30), origin=(8, 10, 8)),
        bx("RoofE", (7.5, 9, 1), (15, 10.5, 15), "barnroof", rot=(0, 0, -30), origin=(8, 10, 8)),
        bx("Bowl", (11, 0, -1), (14, 1, 1), "redmetal")],
         box=(0.12, 0, 0.12, 0.88, 0.85, 0.88))
    prop("patiochair", "Patio Chair", [
        bx("Seat", (3, 7, 3), (13, 8, 13), "white"), bx("Back", (3, 8, 12), (13, 17, 13), "white"),
        bx("Leg1", (3, 0, 3), (4, 7, 4), "white"), bx("Leg2", (12, 0, 3), (13, 7, 4), "white"),
        bx("Leg3", (3, 0, 12), (4, 7, 13), "white"), bx("Leg4", (12, 0, 12), (13, 7, 13), "white"),
        bx("ArmL", (3, 11, 4), (4, 12, 12), "white"), bx("ArmR", (12, 11, 4), (13, 12, 12), "white")],
         box=(0.18, 0, 0.18, 0.82, 0.6, 0.82), sounds=WOOD, extra={"drops": []})

    # Level 10: the fields and the farmyard
    prop("scarecrow", "Scarecrow", [
        bx("Post", (7.5, 0, 7.5), (8.5, 26, 8.5), "wood"), bx("Bar", (1, 21, 7.5), (15, 22, 8.5), "wood"),
        bx("Coat", (5, 11, 6.5), (11, 23, 9.5), "coat"), bx("SleeveL", (1.5, 19, 7), (5, 22.5, 9), "coat"),
        bx("SleeveR", (11, 19, 7), (14.5, 22.5, 9), "coat"),
        bx("Head", (5.5, 23, 6), (10.5, 28, 10), "burlap"), bx("Brim", (4, 28, 5), (12, 28.6, 11), "feed"),
        bx("Hat", (6, 28.6, 6.5), (10, 31, 9.5), "feed")],
         box=(0.4, 0, 0.4, 0.6, 1.8, 0.6), material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("game:cloth-plain", 1, 0.5), ("game:drygrass", 2, 1), ("game:stick", 2, 1))})
    prop("powerpole", "Telegraph Pole", [
        bx("Pole", (7, 0, 7), (9, 96, 9), "wooddark"), bx("Arm", (0, 88, 7.5), (16, 89.5, 8.5), "wooddark"),
        bx("InsL", (1.5, 89.5, 7.6), (2.5, 91.5, 8.4), "china"), bx("InsM", (7.6, 96, 7.6), (8.4, 98, 8.4), "china"),
        bx("InsR", (13.5, 89.5, 7.6), (14.5, 91.5, 8.4), "china")],
         box=(0.43, 0, 0.43, 0.57, 2, 0.57), material="Wood", sounds=WOOD, extra={"drops": []})
    prop("plough", "Old Plough", [
        bx("Beam", (7, 6, 0), (9, 8, 16), "steeldark"), bx("Frame", (2, 5, 4), (14, 6.5, 12), "steeldark"),
        bx("Share1", (3, 0, 5), (5, 6, 9), "metaldark", rot=(25, 0, 0), origin=(4, 3, 7)),
        bx("Share2", (11, 0, 5), (13, 6, 9), "metaldark", rot=(25, 0, 0), origin=(12, 3, 7)),
        bx("Wheel", (0.5, 0, 12), (1.5, 6, 16), "redmetal"), bx("Handle", (7.5, 8, 14), (8.5, 14, 16), "wood")],
         box=(0.06, 0, 0, 0.94, 0.5, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1.5, 0.5), ("game:metalnailsandstrips-iron", 0.8, 0.5))})
    prop("waterpump", "Hand Pump", [
        bx("Base", (5, 0, 5), (11, 3, 11), "stone"), bx("Body", (6.5, 3, 6.5), (9.5, 16, 9.5), "blackmetal"),
        bx("Spout", (7.5, 11, 3), (8.5, 12.5, 6.5), "blackmetal"), bx("Handle", (7.5, 16, 8), (8.5, 17, 15), "blackmetal", rot=(-20, 0, 0), origin=(8, 16, 8))],
         box=(0.3, 0, 0.3, 0.7, 1.06, 0.7), oriented=False, material="Metal", sounds=METAL)
    prop("tractor", "Old Tractor", [
        bx("Body", (8, 10, 6), (24, 22, 30), "tractorgreen"), bx("Hood", (10, 12, 0), (22, 20, 8), "tractorgreen"),
        bx("Grille", (10.5, 12.5, -0.2), (21.5, 19.5, 0), "grate", faces=("north",), full=True),
        bx("WheelRL", (0, 0, 26), (7, 22, 44), "rubber"), bx("WheelRR", (25, 0, 26), (32, 22, 44), "rubber"),
        bx("WheelFL", (3, 0, 4), (8, 11, 14), "rubber"), bx("WheelFR", (24, 0, 4), (29, 11, 14), "rubber"),
        bx("Fender", (0, 22, 26), (32, 23, 44), "tractorgreen"), bx("Rear", (8, 8, 30), (24, 22, 44), "tractorgreen"),
        bx("Seat", (12, 22, 34), (20, 25, 40), "blackmetal"), bx("SeatBack", (12, 25, 39), (20, 31, 40), "blackmetal"),
        bx("Column", (15.5, 22, 28), (16.5, 30, 29), "blackmetal"), bx("Wheel", (13, 30, 26), (19, 30.6, 32), "blackmetal"),
        bx("Exhaust", (10, 20, 4), (11.5, 34, 5.5), "blackmetal")],
         box=(0, 0, 0, 1, 1.4, 1), oriented=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 2, 1), ("scrapwire", 1.5, 1), ("game:metalnailsandstrips-iron", 1, 0.5))})
    prop("hayroll", "Round Bale", [
        bx("Bale", (0.5, 0, 1.5), (15.5, 14, 14.5), "hayroll-side", faces=("north", "south", "up", "down")),
        bx("Ends", (0.5, 0, 1.5), (15.5, 14, 14.5), "hayroll-end", faces=("east", "west"), full=True)],
         box=(0.03, 0, 0.09, 0.97, 0.88, 0.91), material="Plant", sounds=CLOTH,
         extra={"drops": [{"type": "block", "code": "game:hay-normal-ud", "quantity": {"avg": 2, "var": 1}}]})

    # Level 5: the corridors
    prop("icemachine", "Ice Machine", [
        bx("Body", (1, 0, 3), (15, 26, 15), "steel", faces=("east", "west", "up", "south")),
        bx("Front", (1, 0, 3), (15, 26, 15), "icemachine", faces=("north",), full=True)],
         box=(0.06, 0, 0.18, 0.94, 1.62, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 1, 0.5))})
    prop("roomservicetray", "Room Service Tray", [
        bx("Tray", (3, 0, 4), (13, 0.6, 12), "silver"), bx("Plate", (5, 0.6, 5.5), (10, 1, 10.5), "china"),
        bx("Cloche", (5.5, 1, 6), (9.5, 4, 10), "silver"), bx("Glass", (11, 0.6, 5), (12, 3, 6), "lanternglass")],
         box=(0.18, 0, 0.25, 0.82, 0.25, 0.75), collide=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("crackers", 0.5, 0.4), ("glassshard", 0.3, 0.3))})
    prop("laundrycart", "Laundry Cart", [
        bx("Bin", (2, 3, 3), (14, 14, 13), "canvas"), bx("Rim", (1.5, 14, 2.5), (14.5, 15, 13.5), "chrome"),
        bx("Wheel1", (3, 0, 4), (4, 3, 5), "rubber"), bx("Wheel2", (12, 0, 4), (13, 3, 5), "rubber"),
        bx("Wheel3", (3, 0, 11), (4, 3, 12), "rubber"), bx("Wheel4", (12, 0, 11), (13, 3, 12), "rubber")],
         box=(0.09, 0, 0.16, 0.91, 0.94, 0.84), material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("game:cloth-plain", 1.5, 1), ("metalbracket", 0.4, 0.3))})

    # Levels 6 and 7: what is left behind, and what floats
    prop("flashlight", "Dead Flashlight", [
        bx("Barrel", (6.5, 0, 5), (9.5, 2.5, 13), "blackmetal"), bx("Head", (6, 0, 3), (10, 3.2, 5), "blackmetal"),
        bx("Lens", (6.5, 0.3, 2.8), (9.5, 2.9, 3), "lampglass", faces=("north",))],
         box=(0.37, 0, 0.18, 0.63, 0.2, 0.82), collide=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("glassshard", 0.6, 0.4), ("scrapwire", 0.5, 0.4))})
    prop("driftwood", "Driftwood", [
        bx("Log", (1, 0, 6), (15, 3, 10), "wetwood"), bx("Branch", (5, 0, 9), (7, 2, 14), "wetwood", rot=(0, 30, 0), origin=(6, 1, 10))],
         box=(0.06, 0, 0.37, 0.94, 0.19, 0.63), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:firewood", 1, 0.5), ("game:stick", 1, 1))})
    prop("buoy", "Buoy", [
        bx("Float", (4, 0, 4), (12, 7, 12), "redmetal"), bx("Band", (3.8, 3, 3.8), (12.2, 5, 12.2), "white"),
        bx("Mast", (7.5, 7, 7.5), (8.5, 16, 8.5), "metaldark"), bx("Top", (6.5, 16, 6.5), (9.5, 18, 9.5), "redmetal")],
         box=(0.25, 0, 0.25, 0.75, 1.1, 0.75), oriented=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5))})


def generate():
    deep_textures.generate()
    refinements()
    level6()
    level61()
    level7()
    level8()
    level9()
    level10()
