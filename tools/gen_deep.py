"""Blocks, props, items and names for Levels 6 to 10 and Level 6.1. Called from gen_detail.py, which writes them out
along with everything else (python tools/gen_detail.py)."""
import json
import math
import os

import deep_textures
import bonekit as BK
import deepprops as DP
import l11art as L11
import deepprops_tex
import l5props as L5
import modelkit as MK
from detail_kit import (ASSETS, CLOTH, GLASS, LANG, METAL, ROTATE, SIDES, STONE, WOOD, Decor, block, bx, cuboid, cyl, ground_storable,
                        name, prop, shape, wall_family, write_json)
from gen_detail import carton, cube_block, plate
from gen_shapes import louvre, octagon


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


def drops(*items):
    """Drops for salvage: (code, average, variance); codes without a domain are ours."""
    return [{"type": "item", "code": c, "quantity": {"avg": a, "var": v}} for c, a, v in items]


def door_json(code, english, geometry, kind, material="Metal", sounds=METAL, comment=None):
    """(deep props) A door of the Snackrooms as geometry: `geometry` is {"lower": elements, "upper": elements}. The block
    has no facing, so the parts are built for all four sides (deepprops). Codes, parts and footprint are the old cube's."""
    paths = {part: shape(f"{code}-{part}", els) for part, els in geometry.items()}
    data = {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": material, "drawtype": "json",
        "shapeByType": {f"*-{part}": {"base": path} for part, path in paths.items()},
        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": sounds,
    }
    if kind:
        data["behaviors"] = threshold(kind)
    block(code, data, comment or english)
    name(f"{code}-*", english)


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
    ground_storable(data)
    write_json(os.path.join(ASSETS, "itemtypes", "deep", code + ".json"), data, english)
    LANG[f"item-{code}"] = english
    LANG[f"itemdesc-{code}"] = desc


def siding_tex(siding):
    """A house's siding on one face: the painted lap siding comes in three versions (one with chipped paint), the
    brick in one. The gables over the walls use the same (pitch_textures)."""
    t = {"base": f"block/detail/siding-{siding}"}
    if siding != "brick":
        t["alternates"] = [{"base": f"block/detail/siding-{siding}-{n}"} for n in (2, 3)]
    return t


def tractor_wheel(name, x1, x2, yc, zc, r):
    """A tyre seen side on as an octagon (three crossed boxes) with a green hub (graphics pass B11; the wheels were
    square)."""
    k = r * 0.41  # an octagon's half side
    return [bx(f"{name}A", (x1, yc - r, zc - k), (x2, yc + r, zc + k), "rubber"),
            bx(f"{name}B", (x1 + 0.15, yc - k, zc - r), (x2 - 0.15, yc + k, zc + r), "rubber"),
            bx(f"{name}C", (x1 + 0.3, yc - r * 0.77, zc - r * 0.77), (x2 - 0.3, yc + r * 0.77, zc + r * 0.77), "rubber"),
            bx(f"{name}Hub", (x1 - 0.3, yc - r * 0.4, zc - r * 0.4), (x2 + 0.3, yc + r * 0.4, zc + r * 0.4), "tractorgreen")]


def porch_post():
    """A painted porch post: a plinth at its foot, a plain square shaft, and a capital of two steps under the roof
    (graphics pass B11; it was a bare square post)."""
    return [bx("Plinth", (5, 0, 5), (11, 1.5, 11), "windowtrim"), bx("PlinthCap", (5.25, 1.5, 5.25), (10.75, 2, 10.75), "windowtrim"),
            bx("Post", (5.75, 2, 5.75), (10.25, 14, 10.25), "windowtrim"),
            bx("Neck", (5.5, 14, 5.5), (10.5, 14.5, 10.5), "windowtrim"), bx("Capital", (5, 14.5, 5), (11, 16, 11), "windowtrim")]


# ======================= Level 6 =======================

def level6():
    cube_block("l6block", {"wall": "Cold Wall", "floor": "Cold Floor", "ceiling": "Cold Ceiling", "wet": "Wet Cold Floor"}, ["wall", "floor", "ceiling", "wet"],
               {"wall": "l6wall", "floor": "l6floor", "ceiling": "l6ceiling", "wet": "l6floor-wet"},
               comment="The smooth, cold material of Level 6's hallways", randomizeAxes="xyz")  # (D4) the wall's versions by height too
    wall_family("l6deco", "Cold Wall", {1: "l6wall"}, [
        Decor("megexit", "Chalk Marking", {2: [bx("Chalk", (0, 0, -0.05), (16, 16, 0), "chalk-megexit", faces=("north",), full=True)]}),
        Decor("megcross", "Chalk Marking", {2: [bx("Chalk", (0, 0, -0.05), (16, 16, 0), "chalk-megcross", faces=("north",), full=True)]}),
        Decor("meglogo", "Chalk Marking", {2: [bx("Chalk", (0, 0, -0.05), (16, 16, 0), "chalk-meglogo", faces=("north",), full=True)]}),
        Decor("handprints", "Handprints", {2: [bx("Prints", (0, 0, -0.05), (16, 16, 0), "handprints", faces=("north",), full=True)]}),
        Decor("scratches", "Scratches", {2: [bx("Scratches", (0, 0, -0.05), (16, 16, 0), "scratches", faces=("north",), full=True)]}),
        # A light switch, the only one anybody has found. It does nothing (B9: modelled, dead_switch)
        Decor("deadswitch", "Light Switch", {2: dead_switch()}),
    ])
    prop("tripwire", "Tripwire", tripwire(), box=(0, 0, 0.4, 1, 0.15, 0.6), collide=False, material="Metal", sounds=METAL,
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
    ground_storable(data, "Halves", ctrl=True)  # a tool: set down with ctrl + shift, as vanilla's are
    write_json(os.path.join(ASSETS, "itemtypes", "deep", "chalk.json"), data, "Surveyor's chalk: marks walls. The one thing in Level 6 that stays where you left it")
    LANG["item-chalk"] = "Surveyor's Chalk"
    LANG["itemdesc-chalk"] = "Right-click a wall to leave a mark: an arrow, a cross or a circle. Choose which with the tool mode key (F). Marks show on your map, if the world has one. Found in crumbled ceiling tiles, or made from a chalk stone."
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
    door_json("rustydoor", "Rusty Steel Door", {"lower": DP.exit_door(False), "upper": DP.exit_door(True)}, "rustydoor",
              comment="A rusty steel door marked EXIT. It leads back into Level 6, somewhere")
    door_block("glassdoors", "Sliding Glass Doors", "glassdoors", "glassdoor", material="Glass", sounds=GLASS, comment="Sliding glass doors onto somewhere else entirely")
    door_json("kitchendoor", "Kitchen Door", {"lower": DP.kitchen_door(False), "upper": DP.kitchen_door(True)}, "kitchendoor",
              comment="A swinging kitchen door. It opens into another restaurant")
    block("ventgrate", {"creativeinventory": {"general": ["*"]}, "blockmaterial": "Metal", "drawtype": "cube",
                        "textures": {"all": {"base": "block/detail/ventgrate"}}, "behaviors": threshold("vent"),
                        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL}, "A vent big enough to crawl into")
    name("ventgrate", "Vent")

    wall_family("snackdeco", "Mall Wall", {1: "snackwall-mall"}, [
        # (deep props) the sign is a case on the wall, and the wall under it is the restaurants' wood panelling
        Decor(code, english, {3: DP.sign(code)}, light=[0, 4, 8], wall="snackwall-panel")
        for code, english in (("signburger", "Neon Sign"), ("signpizza", "Neon Sign"), ("signtaco", "Neon Sign"), ("signdonut", "Neon Sign"))
    ] + [
        Decor("menuboard", "Menu Board", {3: plate("Board", (1, 2, -0.6), (15, 14, 0), "menuboard", "wooddark", glow=60)}),
        Decor("mallmap", "Mall Directory", {2: plate("Map", (2, 1, -1), (14, 15, 0), "mallmap", "chrome", glow=40)}),
    ], material="Stone", sounds=STONE)

    snacks = drops(("chips", 0.8, 0.6), ("candybar", 0.8, 0.6), ("soda", 0.5, 0.5), ("crackers", 0.4, 0.4))
    prop("cafetable", "Cafeteria Table", cafe_table(),  # (B9: the furniture and fixtures below are modelled; see their functions)
         box=(0.06, 0, 0.06, 0.94, 0.78, 0.94), oriented=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5))})
    prop("cafechair", "Cafeteria Chair", cafe_chair(),
         box=(0.22, 0, 0.22, 0.78, 1, 0.78), material="Metal", sounds=METAL, extra={"drops": drops(("metalbracket", 0.6, 0.4))})
    prop("snackcounter", "Snack Bar Counter", {k: snack_counter(k) for k in ("plain", "register", "display")},
         box=(0, 0, 0.12, 1, 0.94, 1), material="Metal", sounds=METAL)
    prop("stove", "Griddle", griddle(),
         box=(0, 0, 0.12, 1, 0.88, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 0.8, 0.5), ("game:fat", 0.3, 0.3))})
    prop("fryer", "Deep Fryer", fryer(),
         box=(0.06, 0, 0.12, 0.94, 0.88, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1, 0.5), ("scrapwire", 0.6, 0.4), ("game:fat", 0.6, 0.4))})
    prop("snackshelf", "Snack Shelf", snack_shelf(),
         box=(0.03, 0, 0.47, 0.97, 1.75, 1), material="Metal", sounds=METAL,
         extra={"drops": snacks,  # (B9 round 2) three arrangements of the packs, so a row of shelves does not repeat one
                "textures": {"snackpacks": {"base": "block/detail/snackpacks",
                                            "alternates": [{"base": "block/detail/snackpacks-2"}, {"base": "block/detail/snackpacks-3"}]}}})
    # The snack machine: a blue cabinet with a lit header, a coin panel standing proud of it, and a deep glass front;
    # behind the glass, four shelves of packets on their spirals, three columns to a shelf. (Facing north, its west
    # side is on the right as you face it: the panel is there.) B9: the spirals, the price display, the keypad, the
    # coin plate, the bill slot and the coin return are geometry (the panel was a painting of them)
    vend_rows = []
    for r, y in enumerate((8, 12.3, 16.6, 20.9)):
        vend_rows.append(bx(f"Shelf{r}", (5, y, 3), (13.5, y + 0.5, 8), "snackchrome", faces=("north", "up")))
        for c in range(3):
            x = 5.3 + c * 2.75
            band = (r + c) % 4 * 4
            vend_rows.append(bx(f"Packets{r}{c}", (x, y + 0.5, 4), (x + 2.4, y + 3.3, 7.8), "snackvendrows", glow=60,
                                faces=("north", "up"), uv=[band, 0, band + 2.4, 2.8]))
            vend_rows.append(bx(f"Coil{r}{c}", (x - 0.05, y + 0.5, 3.6), (x + 2.45, y + 3.3, 3.75), "vendspiral", faces=("north",),
                                uv=[0, 0, 2.5, 2.8]))
    vend_panel = [bx("Lcd", (1.75, 22, 0.75), (4.25, 23.5, 1), "vendlcd", faces=FRONT, glow=80, uv=[0, 0, 7, 3.5]),
                  bx("Coin", (2, 19, 0.6), (4, 21.25, 1), "coinplate", faces=FRONT, full=True),
                  bx("Bill", (1.75, 12, 0.7), (4.25, 13.25, 1), "snackchrome", faces=FRONT),
                  bx("BillSlot", (2.25, 12.5, 0.65), (3.75, 12.75, 0.7), "metaldark", faces=("north",)),
                  bx("Return", (2.25, 8.5, 0.5), (3.75, 10.5, 1), "snackchrome", faces=FRONT),
                  bx("ReturnCup", (2.5, 8.75, 0.45), (3.5, 9.75, 0.5), "metaldark", faces=("north",))]
    vend_panel += vend_keypad("Keys", 1.75, 14.75, 1)
    prop("snackvending", "Snack Machine", [
        bx("Body", (1, 0, 8), (15, 29, 15), "snackvending", faces=("east", "west", "up", "south")),
        bx("Inside", (5, 7, 8), (13.5, 25, 8.5), "snackvendinside", faces=("north",), glow=40),
        bx("Header", (1, 25, 1.4), (15, 29, 8), "snackvending", faces=("east", "west", "up", "down")),
        bx("HeaderFace", (1, 25, 1.4), (15, 29, 8), "snackvendhead", faces=("north",), glow=80, uv=[0, 0, 16, 4.5]),
        bx("Stile", (13.5, 7, 1.4), (15, 25, 8), "snackvending", faces=("north", "east", "west")),
        bx("Panel", (1, 7, 1), (5, 25, 8), "snackvending", faces=("east", "west", "up", "down")),
        bx("PanelFace", (1, 7, 1), (5, 25, 8), "snackvendpanel", faces=("north",), uv=[6, 0, 10, 16]),
        bx("Base", (1, 0, 1.4), (15, 7, 8), "snackvending", faces=("north", "east", "west", "up")),
        bx("Flap", (5.5, 2, 1.1), (13.5, 5.5, 1.4), "metaldark", faces=("north", "up", "east", "west")),
        bx("Glass", (5, 7, 2.2), (13.5, 25, 2.3), "snackvendglass", faces=("north",), full=True)] + vend_rows + vend_panel,
         box=(0.06, 0, 0.06, 0.94, 1.8, 0.94), material="Metal", sounds=METAL, light=[8, 2, 7],
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:chips", "backrooms:candybar", "backrooms:crackers", "backrooms:soda"], "restock": True}})
    # (snackvend) The broken snack machine that stands in the doorway of a vending room: the same cabinet, dented and
    # rusted, its sign dark and its display dead, the glass smashed out at the top corner and the pane hanging ajar,
    # most of the packets gone from their coils, a few fallen to the bottom, the delivery flap bent down. Nothing in it
    # glows. It breaks with a little effort (salvage.py gives it what such a machine held).
    broken_rows = []
    for r, y in enumerate((8, 12.3, 16.6, 20.9)):
        broken_rows.append(bx(f"Shelf{r}", (5, y, 3), (13.5, y + 0.5, 8), "snackchrome", faces=("north", "up")))
        for c in range(3):
            x = 5.3 + c * 2.75
            band = (r + c) % 4 * 4
            broken_rows.append(bx(f"Coil{r}{c}", (x - 0.05, y + 0.5, 3.6), (x + 2.45, y + 3.3, 3.75), "vendspiral", faces=("north",),
                                  uv=[0, 0, 2.5, 2.8]))
            if (r, c) in ((0, 0), (1, 0), (1, 2), (2, 1), (2, 2)):  # the packets that are left
                broken_rows.append(bx(f"Packets{r}{c}", (x, y + 0.5, 4), (x + 2.4, y + 3.3, 7.8), "snackvendrows",
                                      faces=("north", "up"), uv=[band, 0, band + 2.4, 2.8]))
    fallen = [bx("Fallen0", (5.6, 7, 4.2), (8.2, 8.1, 7), "snackvendrows", faces=("north", "up", "east", "west"), uv=[0, 0, 2.4, 2.8], rot=(0, 0, 8)),
              bx("Fallen1", (8.6, 7, 3.6), (11.2, 8.1, 6.6), "snackvendrows", faces=("north", "up", "east", "west"), uv=[8, 0, 10.4, 2.8], rot=(0, 18, -6)),
              bx("Fallen2", (10.6, 7, 5), (13.2, 8.1, 7.6), "snackvendrows", faces=("north", "up", "east", "west"), uv=[12, 0, 14.4, 2.8], rot=(0, -12, 4)),
              bx("Fallen3", (7.2, 8.1, 4.6), (9.8, 9.2, 7.2), "snackvendrows", faces=("north", "up", "east", "west"), uv=[4, 0, 6.4, 2.8], rot=(0, 25, 3))]
    broken_panel = [bx("Lcd", (1.75, 22, 0.75), (4.25, 23.5, 1), "brokenvlcd", faces=FRONT, uv=[0, 0, 7, 3.5]),
                    bx("Coin", (2, 19, 0.6), (4, 21.25, 1), "coinplate", faces=FRONT, full=True),
                    bx("Bill", (1.75, 12, 0.7), (4.25, 13.25, 1), "snackchrome", faces=FRONT),
                    bx("BillSlot", (2.25, 12.5, 0.65), (3.75, 12.75, 0.7), "metaldark", faces=("north",)),
                    bx("Return", (2.25, 8.5, 0.5), (3.75, 10.5, 1), "snackchrome", faces=FRONT),
                    bx("ReturnCup", (2.5, 8.75, 0.45), (3.5, 9.75, 0.5), "metaldark", faces=("north",))]
    broken_panel += vend_keypad("Keys", 1.75, 14.75, 1)
    prop("brokenvending", "Broken Vending Machine", [
        bx("Body", (1, 0, 8), (15, 29, 15), "brokenvbody", faces=("east", "west", "up", "south")),
        bx("Inside", (5, 7, 8), (13.5, 25, 8.5), "snackvendinside", faces=("north",)),
        bx("Header", (1, 25, 1.4), (15, 29, 8), "brokenvbody", faces=("east", "west", "up", "down")),
        bx("HeaderFace", (1, 25, 1.4), (15, 29, 8), "brokenvhead", faces=("north",), uv=[0, 0, 16, 4.5]),
        bx("Stile", (13.5, 7, 1.4), (15, 25, 8), "brokenvbody", faces=("north", "east", "west")),
        bx("Panel", (1, 7, 1), (5, 25, 8), "brokenvbody", faces=("east", "west", "up", "down")),
        bx("PanelFace", (1, 7, 1), (5, 25, 8), "snackvendpanel", faces=("north",), uv=[6, 0, 10, 16]),
        bx("Base", (1, 0, 1.4), (15, 7, 8), "brokenvbody", faces=("north", "east", "west", "up")),
        bx("Flap", (5.5, 2, 1.1), (13.5, 5.5, 1.4), "metaldark", faces=("north", "up", "east", "west"), rot=(35, 0, 0), origin=(9.5, 2, 1.25)),
        bx("Glass", (5, 7, 2.2), (13.5, 25, 2.3), "brokenvglass", faces=("north",), full=True, rot=(0, 14, 0), origin=(13.5, 16, 2.25))]
        + broken_rows + fallen + broken_panel,
         box=(0.06, 0, 0.06, 0.94, 1.8, 0.94), material="Metal", sounds=METAL,
         extra={"resistance": 4})
    # The drinks fridge: a white cabinet with a lit header and a kick-plate grille; a glass door in a dark frame with a
    # bar handle; behind it, lit cold white, four wire shelves of cans and bottles, five to a shelf. B9: the kick grille
    # is a louvre, the bottles have necks and caps
    drinks = []
    for r, y in enumerate((4.2, 9.6, 15, 20.4)):
        drinks.append(bx(f"Shelf{r}", (2, y, 2.6), (14, y + 0.4, 13.5), "snackchrome", faces=("north", "up")))
        tall = r % 2 == 1  # bottles on every other shelf, cans on the rest
        for c in range(5):
            x = 2.6 + c * 2.25
            band = (r * 2 + c) % 4 * 4
            drinks.append(bx(f"Drink{r}{c}", (x, y + 0.4, 3.4), (x + 1.7, y + (4.2 if tall else 3), 5.1), "drinkcans", glow=40,
                             faces=("north", "up", "east", "west"), uv=[band, 0, band + 1.7, 4 if tall else 2.6]))
            if tall:
                drinks += [bx(f"Neck{r}{c}", (x + 0.5, y + 4.2, 3.9), (x + 1.2, y + 4.8, 4.6), "drinkcans", glow=40,
                              faces=("north", "up", "east", "west"), uv=[band, 0, band + 0.7, 0.6]),
                           bx(f"Cap{r}{c}", (x + 0.45, y + 4.8, 3.85), (x + 1.25, y + 5.15, 4.65), "white",
                              faces=("north", "up", "east", "west"))]
    prop("drinkfridge", "Drinks Fridge", [
        bx("Body", (1, 0, 2), (15, 30, 15), "fridgebody", faces=("east", "west", "up", "south")),
        bx("Inside", (2, 4, 13.4), (14, 25, 13.5), "fridgeinside", faces=("north",), glow=60),
        bx("InsideL", (2, 4, 2), (2.1, 25, 13.5), "fridgeinside", faces=("east",), glow=40),
        bx("InsideR", (13.9, 4, 2), (14, 25, 13.5), "fridgeinside", faces=("west",), glow=40),
        bx("Header", (1, 26, 1.4), (15, 30, 2), "drinkhead", faces=("north",), glow=90, uv=[0, 0, 16, 4.5]),
        bx("HeaderEdge", (1, 26, 1.4), (15, 30, 2), "fridgebody", faces=("east", "west", "up", "down")),
        *louvre("Kick", 1, 0, 15, 3, 2, 3, tex="fridgebody", back="fridgegrille", frame=0.5, proud=0.4),
        bx("FrameL", (1, 3, 1.2), (2, 26, 2), "metaldark"), bx("FrameR", (14, 3, 1.2), (15, 26, 2), "metaldark"),
        bx("FrameT", (2, 25, 1.2), (14, 26, 2), "metaldark"), bx("FrameB", (2, 3, 1.2), (14, 4, 2), "metaldark"),
        bx("Handle", (12.4, 9, 0.3), (13, 20, 0.8), "snackchrome"),
        bx("HandleTop", (12.4, 19.4, 0.8), (13, 20, 1.2), "snackchrome"), bx("HandleFoot", (12.4, 9, 0.8), (13, 9.6, 1.2), "snackchrome"),
        bx("Glass", (2, 4, 1.5), (14, 25, 1.6), "fridgeglass", faces=("north",), full=True)] + drinks,
         box=(0.06, 0, 0.06, 0.94, 1.88, 0.94), material="Metal", sounds=METAL, light=[30, 1, 6],
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:soda", "backrooms:waterbottle", "backrooms:almondwater", "backrooms:cashewwater"], "restock": True}})

    # The heap of a vending machine room ("unenterable due to the sheer amount of vending machines piled on top of each
    # other"): dead machines standing, toppled onto their backs, and lying across the tops of the standing ones
    prop("vendingpile", "Vending Machine", {"standing": dead_machine("stand"), "toppled": dead_machine("floor"), "ontop": dead_machine("top")},
         box=(0.06, 0, 0.06, 0.94, 1, 0.94), material="Metal", sounds=METAL)

    food("chips", "Bag of Chips", 160, "Grain", "Salty, crisp, and from nowhere.")
    food("candybar", "Chocolate Bar", 200, "Dairy", "Sweet enough to make you forget where you are, almost.")
    food("soda", "Can of Soda", 90, "NoNutrition", "Fizzy and far too sweet. Nobody knows who stocks the fridges.", stack=8)
    food("cashewwater", "Cashew Water", 140, "NoNutrition", "Like Almond Water, but nuttier. It steadies you a little, though not as much.",
         health=1, stack=8, extra={"class": "BackroomsAlmondWater", "attributes": {"stabilityRestored": 0.08}})
    food("waterbottle", "Bottle of Water", 100, "NoNutrition", "Plain water. Down here, that's rare.", health=1, stack=8)


def dead_machine(pose):
    """A dead drinks machine of a Level 6.1 vending room, standing ("stand"), on its back on the floor ("floor") or
    lying across the top of a standing one below ("top", in the block above it). Built standing, front to the north,
    in its own (u across, v up, w back) frame, then laid down: on its back the front faces up and its length runs
    west-east (shortened a little to keep to its own tile), a little askew."""
    rows = []
    for r, y in enumerate((6, 10.5, 15, 19.5)):
        rows.append(((2.8, y, 3.2), (11.2, y + 0.4, 7), "snackchrome", ("north", "up")))
        for c in range(3):
            x = 3 + c * 2.75
            band = (r + c + 1) % 4 * 4
            rows.append(((x, y + 0.4, 4), (x + 2.4, y + 3.2, 6.8), "snackvendrows", ("north", "up"), [band, 0, band + 2.4, 2.8]))
    parts = [((1, 0, 7), (15, 29, 15), "vendpilebody", ("east", "west", "up", "south", "down")),
             ((2.5, 4, 7), (11.5, 24, 7.2), "snackvendinside", ("north",)),
             ((1, 24, 1.4), (15, 29, 7), "vendpilebody", ("east", "west", "up", "down")),
             ((1, 24, 1.4), (15, 29, 7), "vendpilehead", ("north",), [0, 0, 16, 4.5]),
             ((1, 4, 1.4), (2.5, 24, 7), "vendpilebody", ("north", "east", "west")),
             ((11.5, 4, 1), (15, 24, 7), "vendpilebody", ("east", "west", "up", "down")),
             ((11.5, 4, 1), (15, 24, 7), "vendpilepanel", ("north",), [6, 0, 9.5, 16]),
             ((1, 0, 1.4), (15, 4, 7), "vendpilebody", ("north", "east", "west", "up")),
             ((3, 1, 1.1), (11, 3.4, 1.4), "metaldark", ("north", "up", "east", "west")),
             ((2.5, 4, 2.2), (11.5, 24, 2.3), "vendpileglass", ("north",), [0, 0, 16, 16]),
             # (B9) the dead panel's display, coin plate and keypad as geometry
             ((12, 20, 0.75), (14.5, 21.5, 1), "vendpilelcd", ("north", "east", "west", "up", "down")),
             ((12.5, 17, 0.6), (14, 19, 1), "coinplate", ("north", "east", "west", "up", "down"), [0, 0, 16, 16]),
             ((12, 12.5, 0.75), (14.5, 15.75, 1), "vendpilepanel", ("north", "east", "west", "up", "down"))] + rows + [
             ((12.25 + i * 0.75, 12.75 + j * 0.75, 0.4), (12.75 + i * 0.75, 13.25 + j * 0.75, 0.75), "snackkey",
              ("north", "east", "west", "up", "down")) for j in range(4) for i in range(3)]
    turn = {"stand": None, "floor": (15, 0), "top": (-11, 13)}[pose]
    out = []
    to_world = {"north": "up", "south": "down", "up": "east", "down": "west", "east": "south", "west": "north"}
    for i, part in enumerate(parts):
        (u1, v1, w1), (u2, v2, w2), tex, faces = part[:4]
        uv = part[4] if len(part) > 4 else None
        full = uv == [0, 0, 16, 16]
        if turn is None:
            out.append(bx(f"P{i}", (u1, v1, w1), (u2, v2, w2), tex, faces=faces, uv=None if full else uv, full=full))
            continue
        # On its back: up the machine (v) runs east, out of its front (-w) is up, across it (u) is south
        angle, base = turn
        k = 0.78
        frm = (-3.3 + v1 * k, base + 15 - w2, u1)
        to = (-3.3 + v2 * k, base + 15 - w1, u2)
        out.append(bx(f"P{i}", frm, to, tex, faces=tuple(to_world[f] for f in faces), uv=None if full else uv, full=full,
                      rot=(0, angle, 0), origin=(8, base, 8)))
    return out


# ======================= Graphics pass B9: Level 6's switch and wire, Level 6.1's fixtures =======================
#
# The shapes below replace boxes with flat or painted faces (the burners, knobs, till, pastries and packets were
# painted on): hardware is geometry, built with tools/modelkit.py, and every material has its own texture key
# (deep_textures.snack_materials and its neighbours), so no key is shared by two materials. The codes, kinds, sides,
# collision and selection boxes are unchanged. Front to the north, as every prop here.

FRONT = ("north", "east", "west", "up", "down")  # a part on a wall or a carcass: its back is never seen


def dead_switch():
    """The dead light switch: a yellowed bakelite plate stepped out from the wall, two screws, the dark slot and the
    toggle in it, left down (off). It does nothing."""
    return [bx("Plate", (6.25, 4.75, -0.35), (9.75, 10.25, 0), "l6switchplate", faces=FRONT),
            bx("Face", (6.5, 5, -0.6), (9.5, 10, -0.35), "l6switchplate", faces=FRONT),
            bx("ScrewT", (7.75, 8.95, -0.85), (8.25, 9.45, -0.6), "steel", faces=FRONT),
            bx("ScrewB", (7.75, 5.55, -0.85), (8.25, 6.05, -0.6), "steel", faces=FRONT),
            bx("Slot", (7.5, 6.75, -0.65), (8.5, 8.25, -0.6), "l6switchslot", faces=("north",)),
            bx("Toggle", (7.65, 7.15, -1.7), (8.35, 7.85, -0.62), "l6switchtoggle", faces=FRONT, rot=(28, 0, 0),
               origin=(8, 7.5, -0.62))]


def tripwire():
    """A wire strung low across a passage: a steel anchor plate bolted to the floor at each side, an eye bolt standing
    on it, and the wire (1 px, the thinnest a model part may be; dark, so in the dark you still won't see it) between
    the eyes."""
    els = []
    for side, x in (("L", 1.0), ("R", 15.0)):
        els += [bx(f"Base{side}", (x - 0.75, 0, 7.25), (x + 0.75, 0.25, 8.75), "metaldark", faces=("north", "east", "south", "west", "up")),
                bx(f"Bolt{side}", (x - 0.25, 0.25, 7.75), (x + 0.25, 1.6, 8.25), "steel", faces=("north", "east", "south", "west")),
                bx(f"EyeT{side}", (x - 0.5, 2.1, 7.75), (x + 0.5, 2.35, 8.25), "steel"),
                bx(f"EyeL{side}", (x - 0.5, 1.6, 7.75), (x - 0.25, 2.1, 8.25), "steel", faces=("north", "east", "south", "west")),
                bx(f"EyeR{side}", (x + 0.25, 1.6, 7.75), (x + 0.5, 2.1, 8.25), "steel", faces=("north", "east", "south", "west"))]
    els.append(bx("Wire", (1.5, 1.75, 7.75), (14.5, 2.25, 8.25), "metaldark", faces=("north", "south", "up", "down")))
    return els


def snack_counter(kind):
    """The snack-bar counter: a cream laminate front over a recessed black kick, a stainless band at the foot and a
    chrome rail near the top, a brushed stainless top overhanging the front; on the register kind a cash register,
    on the display kind a glass case of pastries. Counters stand in a row, so the front's parts run the full width
    and meet the next counter's."""
    els = [bx("Kick", (0, 0, 3.75), (16, 1, 16), "snackkick", faces=("north",)),
           bx("Body", (0, 1, 3), (16, 14, 16), "counterfront", faces=("north",)),
           bx("BodySides", (0, 0, 3), (16, 14, 16), "counterfront", faces=("east", "west", "south")),
           bx("Band", (0, 1, 2.75), (16, 2.5, 3), "snackcountertop", faces=("north", "up")),
           bx("Rail", (0, 11.5, 2.6), (16, 12.25, 3), "snackchrome", faces=("north", "up", "down")),
           bx("Top", (0, 14, 2), (16, 15, 16), "snackcountertop")]
    if kind == "register":
        els += cash_register()
    elif kind == "display":
        els += food_case()
    return els


def cash_register():
    """A cash register on the counter, facing the customer: a charcoal base whose front is the cash drawer (a pull and
    a lock), a keyboard deck of pale keys as geometry, and a back tower with the green display ($0.00) toward the
    customer; a roll of receipt paper at its side."""
    els = [bx("Base", (4.5, 15, 6.5), (11.5, 16.75, 12.5), "registerbody"),
           bx("Drawer", (4.75, 15.2, 6.25), (11.25, 16.5, 6.5), "registerbody", faces=FRONT),
           bx("Pull", (7, 15.6, 5.9), (9, 16.0, 6.25), "snackchrome", faces=FRONT),
           bx("Lock", (10.25, 15.6, 6.0), (10.75, 16.1, 6.25), "snackchrome", faces=FRONT),
           bx("Tower", (5.5, 16.75, 10.5), (10.5, 19.5, 12.5), "registerbody"),
           bx("Display", (6, 17.5, 10.25), (10, 19, 10.5), "registerdisp", faces=("north",), glow=60, uv=[0, 0, 10, 4]),
           bx("Roll", (11.5, 15, 10.5), (12.5, 16.5, 12), "white", faces=("north", "east", "south", "up"))]
    for j in range(3):
        for i in range(4):
            x, z = 5.25 + i * 1.5, 7.0 + j * 1.15
            els.append(bx(f"Key{j}{i}", (x, 16.75, z), (x + 1, 17.1, z + 0.75), "snackkey", faces=("north", "east", "west", "up")))
    return els


def food_case():
    """A glass case of pastries on the counter: a chrome base and corner posts, a glass front and top and a glass back
    toward the staff (see-through but for their glints), a white deck and a glass shelf, and on them rows of
    doughnuts, croissants and muffins as small boxes (the old case painted them on its glass)."""
    els = [bx("Base", (1, 15, 3), (15, 15.75, 15), "snackchrome"),
           bx("Deck", (1.5, 15.75, 3.5), (14.5, 16, 14.5), "caseinside", faces=("up",)),
           bx("Shelf", (1.5, 18.5, 6), (14.5, 18.75, 14.5), "snackchrome", faces=("up", "down", "north")),
           bx("Back", (1.5, 15.75, 14.4), (14.5, 20.75, 14.5), "caseglass", faces=("north", "south")),
           bx("Front", (1.5, 15.75, 3.5), (14.5, 20.75, 3.6), "caseglass", faces=("north", "south")),
           bx("Glass", (1.5, 20.75, 3.5), (14.5, 20.85, 14.5), "caseglass", faces=("up", "down")),
           bx("CapN", (1, 20.85, 3), (15, 21.35, 3.5), "snackchrome"), bx("CapS", (1, 20.85, 14.5), (15, 21.35, 15), "snackchrome"),
           bx("CapW", (1, 20.85, 3.5), (1.5, 21.35, 14.5), "snackchrome", faces=("east", "west", "up", "down")),
           bx("CapE", (14.5, 20.85, 3.5), (15, 21.35, 14.5), "snackchrome", faces=("east", "west", "up", "down"))]
    for n, (x, z) in enumerate(((1, 3), (14.5, 3), (1, 14.5), (14.5, 14.5))):
        els.append(bx(f"Post{n}", (x, 15.75, z), (x + 0.5, 20.85, z + 0.5), "snackchrome", faces=("north", "east", "south", "west")))
    # pastries: (band, width, height, depth) as the atlas lays them out (deep_textures.fixture_textures)
    kinds = {"pink": (0, 2.2, 0.8, 2.2, 6), "choc": (1, 2.2, 0.8, 2.2, 6), "croissant": (2, 2.6, 1.0, 1.4, 6),
             "muffin": (3, 1.8, 1.7, 1.8, 8)}
    rows = ((16.0, 4.5, ("pink", "choc", "pink", "croissant", "croissant")),
            (16.0, 8.5, ("muffin", "muffin", "choc", "pink", "muffin")),
            (18.75, 8.0, ("croissant", "pink", "choc", "croissant")),
            (18.75, 11.5, ("muffin", "choc", "muffin", "pink")))
    for r, (y, z, row) in enumerate(rows):
        x = 2.0
        for c, k in enumerate(row):
            band, w, h, d, v2 = kinds[k]
            u = band * 4
            els.append(bx(f"Pastry{r}{c}", (x, y, z), (x + w, y + h, z + d), "pastries", faces=("north", "east", "west", "up", "south"),
                          uv=[u, 4, u + 4, v2]))
            els[-1]["faces"]["up"]["uv"] = [u, 0, u + 4, 4]
            x += w + 0.35
    return els


def griddle():
    """The griddle range: a stainless carcass on four short legs, a control rail with four black knobs, an oven door
    with a window and a bar handle; on top a griddle plate on the left between splash guards and two burners with
    cast-iron grates on the right; a backsplash with a shelf (the old one painted its burners, knobs and door)."""
    els = [bx("Body", (0.5, 1.5, 2.5), (15.5, 12.5, 16), "stovesteel"),
           bx("Rail", (0.5, 10.5, 1.5), (15.5, 12.5, 2.5), "stovesteel", faces=FRONT),
           bx("Deck", (0, 12.5, 1.5), (16, 13.25, 16), "stovesteel"),
           bx("Door", (1.5, 2.5, 2), (14.5, 9.75, 2.5), "stovesteel", faces=FRONT),
           bx("Window", (4, 5, 1.9), (12, 8.5, 2), "ovenwindow", faces=("north",)),
           bx("Splash", (0, 13.25, 14.5), (16, 18, 16), "stovesteel"),
           bx("Ledge", (0, 17.5, 13.5), (16, 18.25, 14.5), "stovesteel"),
           bx("Plate", (1, 13.25, 3), (8, 13.75, 14.5), "griddleplate"),
           bx("GuardW", (0.5, 13.25, 3), (1, 15, 14.5), "stovesteel"),
           bx("GuardE", (8, 13.25, 3), (8.5, 15, 14.5), "stovesteel"),
           bx("Trough", (1, 13.25, 2), (8, 13.6, 3), "metaldark", faces=("north", "up", "east", "west"))]
    els += MK.handle("Handle", 8, 9, 2, length=10, axis="x", standoff=0.75, thick=0.75, tex="snackchrome")
    for i, x in enumerate((2.5, 6, 10, 13.5)):
        els += MK.knob(f"Knob{i}", x, 11.5, 1.5, r=0.6, depth=1.0, tex="stoveknob")
    for g, (z1, z2) in enumerate(((3, 8.5), (9, 14.5))):
        x1, x2 = 9, 15.25
        els.append(bx(f"Cap{g}", (11.25, 13.25, (z1 + z2) / 2 - 1), (13.25, 13.6, (z1 + z2) / 2 + 1), "burnergrate"))
        els += [bx(f"Grate{g}N", (x1, 13.75, z1), (x2, 14.25, z1 + 0.5), "burnergrate"),
                bx(f"Grate{g}S", (x1, 13.75, z2 - 0.5), (x2, 14.25, z2), "burnergrate"),
                bx(f"Grate{g}W", (x1, 13.75, z1 + 0.5), (x1 + 0.5, 14.25, z2 - 0.5), "burnergrate", faces=("east", "west", "up", "down")),
                bx(f"Grate{g}E", (x2 - 0.5, 13.75, z1 + 0.5), (x2, 14.25, z2 - 0.5), "burnergrate", faces=("east", "west", "up", "down")),
                bx(f"Grate{g}X", (x1 + 0.5, 13.75, (z1 + z2) / 2 - 0.25), (x2 - 0.5, 14.25, (z1 + z2) / 2 + 0.25), "burnergrate",
                   faces=("north", "south", "up", "down")),
                bx(f"Grate{g}Z", ((x1 + x2) / 2 - 0.25, 13.73, z1 + 0.5), ((x1 + x2) / 2 + 0.25, 14.3, z2 - 0.5), "burnergrate",
                   faces=("east", "west", "up", "down"))]
        for k, (fx, fz) in enumerate(((x1, z1), (x2 - 0.5, z1), (x1, z2 - 0.5), (x2 - 0.5, z2 - 0.5))):
            els.append(bx(f"Grate{g}Foot{k}", (fx, 13.25, fz), (fx + 0.5, 13.75, fz + 0.5), "burnergrate", faces=("north", "east", "south", "west")))
    for k, (x, z) in enumerate(((1, 3), (14, 3), (1, 14.5), (14, 14.5))):
        els.append(bx(f"Leg{k}", (x, 0, z), (x + 1, 1.5, z + 1), "snackchrome", faces=("north", "east", "south", "west", "down")))
    return els


def fryer():
    """The deep fryer: a stainless carcass on legs, a door with a bar handle and a control strip (a thermostat knob and
    an amber pilot lamp); on top a rim round the vat, the oil set down inside it, and two wire baskets (cut-out mesh,
    seen through) hanging on a rail at the back, their handles reaching forward; a flue at the back."""
    els = [bx("Body", (1.5, 1.5, 2.5), (14.5, 11.25, 16), "stovesteel"),
           bx("Strip", (1.5, 10, 2), (14.5, 11.25, 2.5), "stovesteel", faces=FRONT),
           bx("Door", (2, 2, 2), (14, 9.5, 2.5), "stovesteel", faces=FRONT),
           bx("Lamp", (11.5, 10.25, 1.75), (12.25, 11, 2), "lens-amber", faces=FRONT, glow=120),
           bx("RimN", (1, 11.25, 2), (15, 13, 4), "stovesteel"), bx("RimS", (1, 11.25, 13.5), (15, 13, 16), "stovesteel"),
           bx("RimW", (1, 11.25, 4), (3, 13, 13.5), "stovesteel", faces=("east", "west", "up")),
           bx("RimE", (13, 11.25, 4), (15, 13, 13.5), "stovesteel", faces=("east", "west", "up")),
           bx("Oil", (3, 11.25, 4), (13, 11.5, 13.5), "fryeroil", faces=("up",)),
           bx("Flue", (1, 13, 14.5), (15, 17.5, 16), "stovesteel"),
           bx("Hanger", (2.5, 16, 13.75), (13.5, 16.5, 14.5), "snackchrome")]
    els += MK.handle("Handle", 8, 8.5, 2, length=8, axis="x", standoff=0.75, thick=0.75, tex="snackchrome")
    els += MK.knob("Knob", 4, 10.6, 2, r=0.5, depth=1.0, tex="stoveknob")
    for b, x1 in enumerate((3.5, 8.5)):
        x2 = x1 + 4
        z1, z2, y1, y2 = 5, 11.5, 11.75, 15
        mesh = "fryerbasket"
        els += [bx(f"Basket{b}Floor", (x1, y1, z1), (x2, y1 + 0.1, z2), mesh, faces=("up", "down")),
                bx(f"Basket{b}N", (x1, y1, z1), (x2, y2, z1 + 0.1), mesh, faces=("north", "south")),
                bx(f"Basket{b}S", (x1, y1, z2 - 0.1), (x2, y2, z2), mesh, faces=("north", "south")),
                bx(f"Basket{b}W", (x1, y1, z1), (x1 + 0.1, y2, z2), mesh, faces=("east", "west")),
                bx(f"Basket{b}E", (x2 - 0.1, y1, z1), (x2, y2, z2), mesh, faces=("east", "west")),
                bx(f"Basket{b}Lip", (x1, y2, z1), (x2, y2 + 0.5, z1 + 0.5), "snackchrome"),
                bx(f"Basket{b}Hook", (x1 + 1.5, y2 - 0.5, z2), (x2 - 1.5, y2 + 1.5, z2 + 2.25), "snackchrome", faces=("east", "west", "up", "south")),
                bx(f"Basket{b}Arm", (x1 + 1.5, y2, z1 - 3), (x2 - 1.5, y2 + 0.5, z1), "snackchrome", faces=("north", "east", "west", "up", "down")),
                bx(f"Basket{b}Grip", (x1 + 1.25, y2 - 0.25, z1 - 4.5), (x2 - 1.25, y2 + 0.75, z1 - 2.5), "rubber")]
    for k, (x, z) in enumerate(((2, 3), (13, 3), (2, 14.5), (13, 14.5))):
        els.append(bx(f"Leg{k}", (x, 0, z), (x + 1, 1.5, z + 1), "snackchrome", faces=("north", "east", "south", "west", "down")))
    return els


SHELF_LEVELS = (2.5, 9.5, 16.5, 23.5)


def snack_shelf():
    """A store's gondola shelf, one block wide and 1.75 high, its front to the north: a painted base with a kick plate,
    a pegboard back on two uprights, four shelves on brackets with a price strip along each front edge, and on them
    rows of packs as geometry: bags of chips, boxes of crackers, cookies and candy, cartons of soda, each a box whose
    faces take one pack from the atlas (deep_textures.snack_packs; the old shelf was one painted picture). The rows
    are full, as the lore has them; each row its own order."""
    els = [bx("Kick", (0.5, 0, 8.25), (15.5, 2, 15), "shelfmetal", faces=("north", "east", "west")),
           bx("Base", (0.5, 2, 8.25), (15.5, 2.5, 15), "shelfmetal", faces=("east", "west", "up", "down")),
           bx("Back", (0.5, 0, 15), (15.5, 27, 16), "shelfpegboard", faces=("north",)),
           bx("BackFace", (0.5, 0, 15), (15.5, 27, 16), "shelfmetal", faces=("south", "up", "east", "west")),
           bx("PostW", (0, 0, 14.5), (0.5, 28, 16), "shelfmetal"),
           bx("PostE", (15.5, 0, 14.5), (16, 28, 16), "shelfmetal"),
           bx("Cap", (0.5, 27, 14.5), (15.5, 28, 16), "shelfmetal")]
    rng = __import__("random").Random(6190)
    for s, y in enumerate(SHELF_LEVELS):
        if s:
            els += [bx(f"Shelf{s}", (0.5, y - 0.5, 8.25), (15.5, y, 15), "shelfmetal"),
                    bx(f"BracketW{s}", (0.5, y - 2, 13.5), (1, y - 0.5, 15), "shelfmetal", faces=("east", "west", "north", "down")),
                    bx(f"BracketE{s}", (15, y - 2, 13.5), (15.5, y - 0.5, 15), "shelfmetal", faces=("east", "west", "north", "down"))]
        els.append(bx(f"Price{s}", (0.5, y - 1, 7.25), (15.5, y + 0.25, 8.25), "pricestrip", faces=("north", "up", "down", "east", "west"),
                      uv=[0, 0, 15, 1.5]))
        room = (SHELF_LEVELS[s + 1] - 0.5 - y) if s + 1 < len(SHELF_LEVELS) else 28 - y
        x = 1.0
        while x < 14.6:
            pack = rng.randrange(8)
            bag = pack < 4
            w = min(rng.choice((2.25, 2.5, 2.75)) if bag else rng.choice((1.75, 2.25, 3.0)), 15.0 - x)
            if w < 1.25:
                break
            h = min(room - 0.75, rng.uniform(4.5, 5.75) if bag else rng.uniform(3.5, 5.5))
            z1 = 9.0 + (rng.uniform(0, 0.75) if bag else 0)
            u, v = (pack % 4) * 4, (pack // 4) * 8
            el = bx(f"Pack{s}_{len(els)}", (x, y, z1), (x + w, y + h, 14.5), "snackpacks", faces=("north", "east", "west", "up"),
                    uv=[u, v, u + 4, v + 8])
            el["faces"]["east"]["uv"] = el["faces"]["west"]["uv"] = [u + 3, v, u + 4, v + 8]
            el["faces"]["up"]["uv"] = [u, v, u + 4, v + 1]
            els.append(el)
            x += w + 0.2
    return els


def vend_keypad(name, x1, y1, z, tex_keys="snackkey", tex_plate="snackvendpanel"):
    return MK.keypad(name, x1, y1, z, cols=3, rows=4, key=0.5, gap=0.25, border=0.25, plate=tex_plate, keys=tex_keys)


def cafe_chair():
    """A food-court chair: a chrome tube frame (front legs, rear legs running up into the back posts, a top rail) on
    black glides, a padded navy vinyl seat with a welt round it on a dark pan, and a padded back cushion on a
    navy panel between the posts (the old one was two flat navy boards on four sticks)."""
    els = []
    for k, (x, z) in enumerate(((4.25, 4.5), (11.75, 4.5))):
        els += [bx(f"Leg{k}", (x - 0.375, 0.4, z - 0.375), (x + 0.375, 6.5, z + 0.375), "snackchrome", faces=("north", "east", "south", "west")),
                bx(f"Glide{k}", (x - 0.5, 0, z - 0.5), (x + 0.5, 0.4, z + 0.5), "snackkick", faces=("north", "east", "south", "west", "up"))]
    for k, x in enumerate((3.75, 11.5)):
        els += [bx(f"Post{k}", (x, 0.4, 11.25), (x + 0.75, 15.25, 12), "snackchrome", faces=("north", "east", "south", "west")),
                bx(f"PostGlide{k}", (x - 0.125, 0, 11.125), (x + 0.875, 0.4, 12.125), "snackkick", faces=("north", "east", "south", "west", "up"))]
    els += [bx("Pan", (4, 6.5, 4), (12, 7, 11.25), "metaldark", faces=("north", "east", "west", "down")),
            bx("Welt", (3.9, 7.4, 3.9), (12.1, 7.9, 11.25), "snackvinyl", faces=("north", "east", "west", "up", "down")),
            bx("BackPanel", (4.5, 8.75, 12), (11.5, 15.25, 12.25), "snackvinyl", faces=("north", "east", "west", "south", "down")),
            bx("Rail", (3.75, 15.25, 11.25), (12.25, 16, 12), "snackchrome")]
    els += MK.bevelled_box("Seat", (4, 7, 4), (12, 8.5, 11.25), "snackvinyl")
    els += MK.bevelled_box("Back", (4.75, 9, 10.75), (11.25, 15, 12), "snackvinyl")
    return els


def cafe_table():
    """A food-court table: a navy laminate top with a ribbed chrome edge band, a dark spider under it, a chrome column
    with a collar, and a round (octagonal) chrome foot (the old one was a navy board on a square post)."""
    els = [MK.box("Top", (1, 11, 1), (15, 12.25, 15), {"top": "snacktabletop", "side": "snackchrome", "bottom": "snackkick"}),
           bx("Spider", (5, 10.5, 5), (11, 11, 11), "metaldark", faces=("north", "east", "south", "west", "down"))]
    els += octagon("Column", 8, 8, 0.9, 1.25, 10.5, "snackchrome")
    els += octagon("Collar", 8, 8, 1.4, 0.75, 1.25, "snackchrome", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("Foot", 8, 8, 4.25, 0, 0.75, "snackchrome", faces=("north", "east", "south", "west", "up"), lift=0.01)
    return els



# ======================= Level 7 =======================

TAR_TOP = {"base": "block/detail/tar", "alternates": [{"base": f"block/detail/{k}"} for k in ("tar", "tar-2", "tar", "tar-3")]}
TAR_SIDE = {"base": "block/detail/tar-side", "alternates": [{"base": f"block/detail/{k}"} for k in ("tar-side-2", "tar-side-3")]}


def level7():
    cube_block("oceanceiling", {"plain": "Concrete Ceiling", "glow": "Concrete Ceiling"}, ["plain", "glow"],
               {"plain": "oceanceiling", "glow": "oceanceiling"}, lightHsvByType={"*-glow": [34, 1, 8]},
               lightAbsorptionByType={"*-glow": 0, "*": 99}, comment="The ceiling over the sea. The dim light seems to come from nowhere")
    # Layout version 9: the high ceiling over the sea, 36 blocks up, with nothing over it. It lets the world's light
    # through (absorbs none), which is the lore's "dim natural light" from nowhere (AtmosphereSystem holds it the same at
    # every hour and dims it); its glowing patches glow by themselves (glowLevel), too far up for their light to reach
    # anything. It never breaks (src/Salvage/Breakdown.cs): over it is the top of the world.
    cube_block("seaceiling", {"plain": "High Concrete Ceiling", "glow": "High Concrete Ceiling"}, ["plain", "glow"],
               {"plain": "oceanceiling", "glow": "oceanceiling"}, lightHsvByType={"*-glow": [34, 1, 8]}, lightAbsorption=0,
               vertexFlagsByType={"*-glow": {"glowLevel": 72}},
               comment="The high ceiling over the sea (layout version 9): it lets through a dim light from nowhere")
    cube_block("islandrock", "Strange Rock", ["plain"], {"plain": "islandrock"}, comment="The unknown rock of Level 7's islands",
               randomizeAxes="xyz",  # (D4) a stack's or pillar's blocks pick their versions by height too
               drops=[{"type": "item", "code": "game:stone-basalt", "quantity": {"avg": 3, "var": 1}}], resistance=6)
    block("tar", {"class": "BackroomsTar", "creativeinventory": {"general": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
                  # (B10) versions: a rising bubble in one block in four, two small ones in another; the drips of the
                  # sides at other places
                  "textures": {"up": TAR_TOP, "down": {"base": "block/detail/tar"}, "horizontals": TAR_SIDE}, "lightAbsorption": 99, "resistance": 3, "drops": [],
                  "sounds": {"walk": "game:walk/sludge*", "place": "game:effect/squish*", "break": "game:effect/squish*", "hit": "game:effect/squish*"},
                  "particleProperties": [{
                      "hsvaColor": [{"avg": 0, "var": 0}, {"avg": 0, "var": 0}, {"avg": 30, "var": 10}, {"avg": 200, "var": 40}],
                      "gravityEffect": {"avg": -0.02, "var": 0}, "posOffset": [{"avg": 0, "var": 0.4}, {"avg": 0.05, "var": 0}, {"avg": 0, "var": 0.4}],
                      "velocity": [{"avg": 0, "var": 0.02}, {"avg": 0.05, "var": 0.02}, {"avg": 0, "var": 0.02}], "quantity": {"avg": 0.05},
                      "size": {"avg": 0.2, "var": 0.1}, "sizeEvolve": {"transform": "linear", "factor": 0.5}, "particleModel": "Cube",
                      "lifeLength": {"avg": 0.8, "var": 0.3}, "selfPropelled": True}]},
          "Scalding, steadily bubbling tar")
    name("tar", "Tar")

    prop("bonepile", "Bones", BK.bonepile(), box=(0.1, 0, 0.1, 0.9, 0.25, 0.9), oriented=False, collide=False,
         material="Stone", sounds=STONE, extra={"drops": drops(("game:bone", 2, 1))})
    prop("scrapmetal", "Rusted Scrap", [
        bx("Plate1", (1, 0, 2), (12, 1, 10), "scrap", rot=(0, 20, 8)), bx("Plate2", (5, 0, 7), (15, 2, 14), "scrap", rot=(6, -15, 0)),
        bx("Rod", (2, 0.5, 12), (14, 1.5, 13), "rust")], box=(0.06, 0, 0.06, 0.94, 0.2, 0.94), oriented=False, collide=False,
         material="Metal", sounds=METAL, extra={"drops": drops(("metalbracket", 0.8, 0.5), ("scrapwire", 0.5, 0.5))})
    prop("jawskeleton", "Skeleton", BK.jawskeleton(), box=(0.1, 0, 0, 0.9, 0.25, 1), collide=False, material="Stone", sounds=STONE,
         extra={"drops": drops(("game:bone", 3, 1))})
    prop("ribcage", "Enormous Ribs", BK.ribcage(), box=(0, 0, 0, 1, 0.25, 1), collide=False,
         material="Stone", sounds=STONE)
    prop("backpack", "Lost Backpack", [
        bx("Bag", (4, 0, 5), (12, 9, 11), "canvas"), bx("Flap", (4, 7, 4.5), (12, 10, 11), "canvas"),
        bx("Pocket", (5, 1, 4), (11, 5, 5), "canvas"), bx("StrapL", (5, 0, 11), (6, 8, 12), "rubber"), bx("StrapR", (10, 0, 11), (11, 8, 12), "rubber")],
         box=(0.25, 0, 0.25, 0.75, 0.62, 0.75), material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("almondwater", 1, 0.8), ("crackers", 0.6, 0.5), ("game:candle", 0.4, 0.4), ("game:rope", 0.3, 0.3),
                                ("game:knife-generic-copper", 0.1, 0), ("game:bandage-clean", 0.4, 0.4), ("chalk", 0.2, 0),
                                ("game:fishingbait-dough", 0.5, 0.3))})
    prop("wreckcrate", "Waterlogged Crate", wreck_crate(),  # (B10)
         box=(0.06, 0, 0.06, 0.94, 0.82, 0.94), oriented=False, sounds=WOOD,
         extra={"drops": drops(("game:plank-aged", 2, 1), ("game:rope", 0.6, 0.4), ("game:metalnailsandstrips-iron", 0.5, 0.4),
                                ("game:boat-raft-aged", 0.06, 0), ("game:fishingpole-simple-wood", 0.08, 0), ("cannedbeans", 0.5, 0.5))})
    # Layout version 9: the chest in a sunken room on the seabed (WorldLayout.AddSunkenRoom), its loot better the deeper
    # it lies. The twilight zone's is a sailor's sea chest of what the drowned carried; the midnight zone's a riveted
    # strongbox of the kind expeditions sealed their best in (metal, the good tools, temporal gears)
    prop("seachest", "Sea Chest", {"twilight": sea_chest(), "midnight": strongbox()},
         box=(0.05, 0, 0.12, 0.95, 0.75, 0.88), material="Wood", sounds=WOOD,
         comment="A chest in a sunken room on Level 7's seabed: the deeper, the better what is in it",
         extra={"dropsByType": {
             "*-twilight-*": drops(("almondwater", 1, 0.8), ("cannedbeans", 0.8, 0.5), ("crackers", 0.6, 0.5), ("game:rope", 1, 0.6),
                                   ("game:bandage-clean", 0.6, 0.4), ("chalk", 0.6, 0.3), ("game:candle", 0.8, 0.6), ("game:flint", 0.5, 0.5),
                                   ("scrapwire", 1, 0.8), ("game:metalbit-copper", 2, 1.5), ("game:knife-generic-copper", 0.15, 0),
                                   ("game:pickaxe-copper", 0.08, 0), ("game:gear-rusty", 0.25, 0), ("game:gear-temporal", 0.03, 0),
                                   ("wanderernote-cache", 0.06, 0), ("wanderernote-way", 0.06, 0), ("seedpacket-carrot", 0.04, 0)),
             "*-midnight-*": drops(("almondwater", 1.5, 1), ("cannedbeans", 1, 0.6), ("game:rope", 1.2, 0.6), ("game:bandage-clean", 1, 0.5),
                                   ("chalk", 0.6, 0.3), ("game:ingot-copper", 0.7, 0.4), ("game:ingot-tinbronze", 0.35, 0.25),
                                   ("game:metalbit-silver", 1.5, 1), ("game:metalbit-gold", 0.8, 0.8), ("game:pickaxe-tinbronze", 0.12, 0),
                                   ("game:prospectingpick-copper", 0.1, 0), ("game:knife-generic-tinbronze", 0.15, 0),
                                   ("game:gear-rusty", 0.6, 0.4), ("game:gear-temporal", 0.15, 0),
                                   ("wanderernote-refuge", 0.08, 0), ("wanderernote-door", 0.08, 0))}})
    LANG.pop("block-seachest-*", None)
    name("seachest-twilight-*", "Sea Chest")
    name("seachest-midnight-*", "Sunken Strongbox")


def sea_chest():
    """A sailor's sea chest, swollen with water: wet boards and a domed lid, two rusted iron straps over it, a brass
    hasp on the front (north), rope beckets at the ends."""
    w, b, r = "wetwood", "l7wreckboards", "rust"
    els = [bx("Body", (1.5, 0, 3), (14.5, 8, 13), b),
           bx("Lid", (1.25, 8, 2.75), (14.75, 10.5, 13.25), w),
           bx("LidTop", (1.75, 10.5, 3.75), (14.25, 11.5, 12.25), w, faces=("up", "north", "south", "east", "west")),
           bx("Hasp", (7, 6, 2.5), (9, 9.5, 3), "brass", faces=("north", "east", "west", "up", "down")),
           bx("BecketW", (0.5, 5, 7), (1.5, 6, 9), "canvas"), bx("BecketE", (14.5, 5, 7), (15.5, 6, 9), "canvas")]
    for i, x in enumerate((3.5, 11.5)):
        els += [bx(f"StrapF{i}", (x, 0, 2.5), (x + 1, 10.5, 3), r, faces=("north", "east", "west")),
                bx(f"StrapB{i}", (x, 0, 13), (x + 1, 10.5, 13.5), r, faces=("south", "east", "west")),
                bx(f"StrapT{i}", (x, 11.5, 3.25), (x + 1, 11.75, 12.75), r, faces=("up", "north", "south", "east", "west"))]
    return els


def strongbox():
    """A riveted steel strongbox, dark with the deep: a body and a flat lid with a rusted seam band between them, corner
    straps, a carrying handle on top, a brass combination dial on the front (north)."""
    m, r = "metaldark", "rust"
    els = [bx("Body", (2, 0, 3.5), (14, 7, 12.5), m),
           bx("Seam", (1.75, 7, 3.25), (14.25, 7.75, 12.75), r),
           bx("Lid", (2, 7.75, 3.5), (14, 10, 12.5), m),
           bx("HandleL", (6, 10, 7.5), (6.75, 11.25, 8.5), "metal"), bx("HandleR", (9.25, 10, 7.5), (10, 11.25, 8.5), "metal"),
           bx("Grip", (6, 11.25, 7.5), (10, 12, 8.5), "metal"),
           bx("Dial", (7, 3, 3), (9, 5, 3.5), "brass", faces=("north", "east", "west", "up", "down"))]
    for i, (x, z) in enumerate(((1.5, 3), (13.5, 3), (1.5, 12), (13.5, 12))):
        els.append(bx(f"Corner{i}", (x, 0, z), (x + 1, 10.25, z + 1), r))
    return els


def wreck_crate():
    """(B10) The waterlogged crate: three wet boards to each side and the lid, inside a frame of battens standing proud
    of them (corner posts, top and bottom rails on every side), one lid board split short; the frame and the boards
    are geometry, where the old crate was one box with its frame and brace painted on."""
    b, w = "l7wreckboards", "wetwood"
    els = [bx("Body", (1.5, 0.5, 1.5), (14.5, 12.5, 14.5), b, faces=("north", "east", "south", "west", "down")),
           bx("LidA", (1.5, 12.4, 1.5), (14.5, 12.9, 5.75), b, faces=("up", "north", "south", "east", "west")),
           bx("LidB", (1.5, 12.4, 6), (10, 12.9, 10), b, faces=("up", "north", "south", "east", "west")),
           bx("LidC", (1.5, 12.4, 10.25), (14.5, 12.9, 14.5), b, faces=("up", "north", "south", "east", "west")),
           bx("Inside", (1.5, 12.3, 1.5), (14.5, 12.4, 14.5), "wetwood", faces=("up",))]
    for i, (x, z) in enumerate(((1, 1), (13.5, 1), (1, 13.5), (13.5, 13.5))):
        els.append(bx(f"Post{i}", (x, 0, z), (x + 1.5, 13, z + 1.5), w))
    for i, (y1, y2) in enumerate(((0, 1.5), (11.25, 12.75))):
        els += [bx(f"RailN{i}", (2.5, y1, 1), (13.5, y2, 1.5), w, faces=("north", "up", "down")),
                bx(f"RailS{i}", (2.5, y1, 14.5), (13.5, y2, 15), w, faces=("south", "up", "down")),
                bx(f"RailW{i}", (1, y1, 2.5), (1.5, y2, 13.5), w, faces=("west", "up", "down")),
                bx(f"RailE{i}", (14.5, y1, 2.5), (15, y2, 13.5), w, faces=("east", "up", "down"))]
    return els


# ======================= Graphics pass B10: Level 8's road lamp, M.E.G. marker and glowcaps =======================

def road_lantern():
    """(B10) The road lamp's lantern, hung at (12, 8): a glass box between four corner posts, a top band, a base plate
    with a drip cone under it, a cap stepped up into a pyramid, a ring and the hook. The glass is where the old one was
    (its light and glow unchanged); the iron is old black paint (l8lampiron)."""
    i = "l8lampiron"
    els = [bx("Glass", (10.5, 19.6, 6.5), (13.5, 23, 9.5), "l8lampglass", glow=230, faces=("north", "east", "south", "west")),
           bx("Band", (10.1, 23, 6.1), (13.9, 23.4, 9.9), i, faces=("north", "east", "south", "west", "down")),
           bx("Plate", (9.8, 19, 5.8), (14.2, 19.6, 10.2), i),
           bx("Cone", (10.8, 18.5, 6.8), (13.2, 19, 9.2), i, faces=("north", "east", "south", "west", "down")),
           bx("Drop", (11.5, 18, 7.5), (12.5, 18.5, 8.5), i, faces=("north", "east", "south", "west", "down")),
           bx("Cap", (9.7, 23.4, 5.7), (14.3, 23.9, 10.3), i),
           bx("Cap2", (10.3, 23.9, 6.3), (13.7, 24.3, 9.7), i, faces=("north", "east", "south", "west", "up")),
           bx("Cap3", (10.9, 24.3, 6.9), (13.1, 24.6, 9.1), i, faces=("north", "east", "south", "west", "up")),
           bx("Ring", (11.5, 24.6, 7.5), (12.5, 24.9, 8.5), i, faces=("north", "east", "south", "west", "up")),
           bx("Hook", (11.75, 24.9, 7.75), (12.25, 26, 8.25), i, faces=("north", "east", "south", "west"))]
    els += [bx(f"Post{k}", (x, 19.6, z), (x + 0.6, 23, z + 0.6), i, faces=("north", "east", "south", "west"))
            for k, (x, z) in enumerate(((10, 6), (13.4, 6), (10, 9.4), (13.4, 9.4)))]
    return els


def road_post():
    """(B10) The road lamp's post: a stepped base and a collar, the pole, a collar and a finial with a ball on top."""
    i = "l8lampiron"
    return [bx("Base", (6, 0, 6), (10, 1, 10), i), bx("Step", (6.6, 1, 6.6), (9.4, 1.8, 9.4), i, faces=("north", "east", "south", "west", "up")),
            bx("Collar", (7.2, 1.8, 7.2), (8.8, 3.4, 8.8), i, faces=("north", "east", "south", "west", "up")),
            bx("Pole", (7.5, 3.4, 7.5), (8.5, 25.4, 8.5), i, faces=("north", "east", "south", "west")),
            bx("CollarTop", (7.25, 25.4, 7.25), (8.75, 26.8, 8.75), i),
            bx("Finial", (7.45, 26.8, 7.45), (8.55, 27.5, 8.55), i, faces=("north", "east", "south", "west", "up")),
            bx("Ball", (7.7, 27.5, 7.7), (8.3, 28.1, 8.3), i, faces=("north", "east", "south", "west", "up"))]


def road_arm():
    """(B10) The arm out to the east over the lantern: the arm with a turned-down end, a diagonal brace under it, and a
    foot where the brace meets the pole (round 2: a scroll there stood in front of the glass and read as a notch)."""
    i = "l8lampiron"
    return [bx("Arm", (8.75, 25.9, 7.65), (12.9, 26.6, 8.35), i),
            bx("ArmEnd", (12.9, 25.6, 7.6), (13.4, 26.7, 8.4), i),
            bx("Brace", (8.5, 23.6, 7.7), (11, 24.2, 8.3), i, rot=(0, 0, 40), origin=(8.5, 23.9, 8)),
            bx("BraceFoot", (8.5, 23.2, 7.75), (9.1, 23.9, 8.25), i, faces=("north", "east", "south", "west", "down"))]


def meg_marker():
    """(B10) The M.E.G. marker: a post with a cap, and the enamel plate (megplate, crisp pixel lettering) in a rim with
    four bolts, set a little forward of the post; its back plain iron."""
    els = [bx("Post", (7, 0, 7.5), (9, 22.5, 9.5), "wood"),
           bx("PostCap", (6.75, 22.5, 7.25), (9.25, 23, 9.75), "wood"),
           bx("Plate", (2, 10, 6.75), (14, 24, 7.5), "megplate", faces=("north",), uv=[0, 0, 12, 14]),
           bx("PlateBack", (2, 10, 6.75), (14, 24, 7.5), "l8lampiron", faces=("south", "east", "west", "up", "down")),
           bx("RimT", (2, 23.5, 6.5), (14, 24, 6.75), "l8lampiron", faces=("north", "east", "west", "up", "down")),
           bx("RimB", (2, 10, 6.5), (14, 10.5, 6.75), "l8lampiron", faces=("north", "east", "west", "up", "down")),
           bx("RimL", (2, 10.5, 6.5), (2.5, 23.5, 6.75), "l8lampiron", faces=("north", "east", "west")),
           bx("RimR", (13.5, 10.5, 6.5), (14, 23.5, 6.75), "l8lampiron", faces=("north", "east", "west"))]
    for k, (x, y) in enumerate(((3.25, 22.75), (12.75, 22.75), (3.25, 11.25), (12.75, 11.25))):
        els.append(bx(f"Bolt{k}", (x - 0.4, y - 0.4, 6.25), (x + 0.4, y + 0.4, 6.75), "l8lampiron", faces=("north", "east", "west", "up", "down")))
    return els


# ======================= Level 8 =======================

def level8():
    prop("megmarker", "M.E.G. Marker", meg_marker(),  # (B10)
         box=(0.4, 0, 0.4, 0.6, 1.5, 0.6), comment="An M.E.G. marker on the 9th Road")
    # Road lamp: a caged lantern hung on a hook from an arm off the top of its post, all inside the block (B10: the post,
    # arm and lantern re-made as geometry in old black iron, road_post, road_arm, road_lantern)
    prop("roadlamp", "Road Lamp", road_post() + road_arm() + road_lantern(),
         box=(0.4, 0, 0.4, 0.6, 1.75, 0.6), oriented=False, material="Metal", sounds=METAL, light=[7, 4, 13])
    # The same lamp with its arm reaching out to the north (the side it is turned to), for a lamp that knows which
    # side the road is on (layout version 5)
    def north_arm(el):
        turned = dict(el)
        (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
        turned["from"], turned["to"] = [z1, y1, 16 - x2], [z2, y2, 16 - x1]
        names = {"east": "north", "north": "west", "west": "south", "south": "east", "up": "up", "down": "down"}
        turned["faces"] = {names[f]: v for f, v in el["faces"].items()}
        if "rotationOrigin" in el:  # a tilt about z (the brace) becomes the same tilt about x
            ox, oy, oz = el["rotationOrigin"]
            turned["rotationOrigin"] = [oz, oy, 16 - ox]
            turned["rotationX"] = turned.pop("rotationZ")
        return turned
    prop("roadlamparm", "Road Lamp", road_post() + [north_arm(el) for el in road_arm() + road_lantern()],
         box=(0.4, 0, 0.4, 0.6, 1.75, 0.6), material="Metal", sounds=METAL, light=[7, 4, 13])
    # Bioluminescent fungi of the caves (Wikidot: "enveloped in a blood-red glow", "multicolored bioluminescent
    # mushrooms"): blood-red glowcaps, and clusters of many colours; on the floor, or growing out from the foot of a
    # wall (on the side the block is turned to)
    for code, english, caps, light in (("glowcapred", "Blood-Red Glowcaps", ["glowcapred"] * 3, [0, 7, 5]),
                                       ("glowcapmixed", "Glowing Mushrooms", ["glowcapblue", "glowcapviolet", "glowcapgreen"], [44, 4, 5])):
        prop(code, english, {"floor": glowcap_floor(caps), "wall": glowcap_wall(caps)}, box=(0.1, 0, 0.1, 0.9, 0.45, 0.9),
             collide=False, material="Plant", sounds=PLANT, light=light,
             extra={"drops": drops(("game:rot", 0.5, 0.5))}, comment="Bioluminescent fungi of Level 8's caves")
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


PLANT = {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}


def glowcap(name, x, z, stem, cap_w, cap, glow=150, lean=0):
    """One mushroom: a pale stem, a cap that glows, a skirt of gills under it."""
    r = cap_w / 2
    g = max(r - 0.4, 0.5)  # the gills' half width: always wider than the stem, so their sides never lie in its sides
    rot = (lean, 0, lean / 2) if lean else None
    # (B10) the cap domed in two tiers (a brim, then a crown half its width higher up), its gills a texture of their own
    t = max(0.75, cap_w / 4.4)
    k = max(0.5, r * 0.62)
    return [bx(name + "Stem", (x - 0.4, 0, z - 0.4), (x + 0.4, stem, z + 0.4), "glowstem", rot=rot, origin=(x, 0, z)),
            bx(name + "Cap", (x - r, stem, z - r), (x + r, stem + t, z + r), cap + "rim", glow=glow, rot=rot, origin=(x, 0, z),
               faces=("north", "south", "east", "west", "up")),
            bx(name + "Crown", (x - k, stem + t, z - k), (x + k, stem + t + max(0.5, t * 0.7), z + k), cap, glow=glow,
               rot=rot, origin=(x, 0, z), faces=("north", "south", "east", "west", "up")),
            bx(name + "Gills", (x - g, stem - 0.5, z - g), (x + g, stem, z + g), cap + "gills", glow=glow // 2,
               faces=("down", "north", "south", "east", "west"), rot=rot, origin=(x, 0, z))]


def glowcap_floor(caps):
    """A cluster on the floor: a patch of mycelium and six mushrooms of different heights."""
    out = [bx("Mycelium", (3, 0, 3.5), (12, 0.2, 13.5), "mycelium", faces=("up",)),  # (round 2: three patches, not a square)
           bx("Mycelium2", (1.5, 0, 6.5), (3, 0.15, 12), "mycelium", faces=("up",)),
           bx("Mycelium3", (12, 0, 2.5), (14, 0.15, 10.5), "mycelium", faces=("up",))]
    for i, (x, z, stem, w, lean) in enumerate(((6, 7, 6, 4.4, 0), (10.5, 9.5, 4, 3.4, 10), (4, 11.5, 2.6, 2.6, -12),
                                               (11.5, 4.5, 3, 2.8, 14), (8.5, 12.5, 1.6, 2, 0), (3.5, 4, 1.4, 1.8, -8))):
        out += glowcap(f"M{i}", x, z, stem, w, caps[i % len(caps)], lean=lean)
    return out


def glowcap_wall(caps):
    """A cluster at the foot of the wall on the north side: brackets growing out of the rock in tiers, and a few small
    caps on the floor in front."""
    out = [bx("Mycelium", (1, 0, 0), (15, 0.2, 6), "mycelium", faces=("up",)),
           bx("Crust", (1.5, 0, 0), (14.5, 9, 0.3), "mycelium", faces=("south",))]
    for i, (x, y, w, d) in enumerate(((5, 7.5, 5, 4), (10.5, 5, 4, 3.4), (3.5, 3, 3.4, 3), (8, 2, 3, 2.6), (12.5, 9.5, 3, 2.4))):
        cap = caps[i % len(caps)]
        out += [bx(f"B{i}", (x - w / 2, y, 0), (x + w / 2, y + 0.8, d), cap + "rim", glow=160, faces=("south", "east", "west", "up", "down")),
                bx(f"B{i}Top", (x - w / 2 + 0.5, y + 0.8, 0), (x + w / 2 - 0.5, y + 1.3, d - 0.6), cap, glow=160,
                   faces=("south", "east", "west", "up")),
                bx(f"B{i}Gills", (x - w / 2 + 0.4, y - 0.4, 0), (x + w / 2 - 0.4, y, d - 0.4), cap + "gills", glow=70,
                   faces=("down", "south", "east", "west"))]
    for i, (x, z, stem, w) in enumerate(((4, 5, 1.6, 2), (11, 4, 2.2, 2.4), (7.5, 6.5, 1.2, 1.6))):
        out += glowcap(f"F{i}", x, z, stem, w, caps[(i + 1) % len(caps)])
    return out


def stop_sign():
    """The STOP sign (l94fence; the street's sign in Levels 1, 9 and 94): an octagonal plate as thin geometry, 12 units
    across and 0.3 thick, its octagon cut by the textures' alpha (deep_textures.stopsign_textures) and its edges
    closed by strips along the flats (the textures' edge pixels, so only the flats show) and four turned strips along
    the cut corners; a plain aluminium back; a galvanised square post behind it; two bolts through the plate into the
    post, their nuts on the back of the post."""
    x0, x1, y0, y1, z0, z1 = 2, 14, 24, 36, 7.0, 7.3
    cut = 12 * (1 - 1 / (1 + math.sqrt(2))) / 2
    side = 12 - 2 * cut
    back = "stopsignback"
    e = 0.3  # the edge faces take the textures' outermost row or column of pixels (0.9 px of 48)

    def face(tex, uv):
        return {"texture": "#" + tex, "uv": [round(v, 4) for v in uv]}

    plate = {"name": "Plate", "from": [x0, y0, z0], "to": [x1, y1, z1], "faces": {
        "north": face("stopsign", (0, 0, 16, 16)), "south": face(back, (0, 0, 16, 16)),
        "up": face(back, (0, 0, 16, e)), "down": face(back, (0, 16 - e, 16, 16)),
        "east": face(back, (16 - e, 0, 16, 16)), "west": face(back, (0, 0, e, 16))}}
    els = [bx("Post", (7.375, 0, z1), (8.625, 33.5, z1 + 1.25), "stopsignpost", uv=(0, 0, 1.25, 16)), plate]
    cx, cy, t = 8, 30, 0.12
    for sx in (-1, 1):
        for sy in (-1, 1):
            mx, my = cx + sx * (6 - cut / 2), cy + sy * (6 - cut / 2)
            lo, hi = (my - t, my) if sy > 0 else (my, my + t)
            strip = bx(f"Edge{'N' if sy > 0 else 'S'}{'E' if sx > 0 else 'W'}", (mx - side / 2, lo, z0), (mx + side / 2, hi, z1),
                       back, faces=("up" if sy > 0 else "down",), uv=(4, 8, 12, 8.3),
                       rot=(0, 0, -45 * sx * sy), origin=(mx, my, (z0 + z1) / 2))
            els.append(strip)
    for y in (y0 + 1.2, y1 - 1.2):  # the bolt heads on the face, the nuts on the back of the post
        els.append(bx(f"Bolt{int(y)}", (7.65, y - 0.35, z0 - 0.25), (8.35, y + 0.35, z0), "stopsignpost",
                      faces=("north", "east", "west", "up", "down")))
        els.append(bx(f"Nut{int(y)}", (7.6, y - 0.4, z1 + 1.25), (8.4, y + 0.4, z1 + 1.5), "stopsignpost",
                      faces=("south", "east", "west", "up", "down")))
    return els


# ======================= Level 9 =======================

def level9():
    road = {"plain": "Asphalt", "leaves": "Asphalt", "wet": "Wet Asphalt", "line": "Road Marking", "linens": "Road Marking",
            "crossing": "Zebra Crossing", "crossingns": "Zebra Crossing", "manhole": "Manhole Cover",
            # Level 11's avenues and streets
            "doublens": "Road Marking", "doublewe": "Road Marking", "bayns": "Road Marking", "baywe": "Road Marking",
            "cracked": "Cracked Asphalt"}
    cube_block("asphalt", road, list(road), {k: "asphalt" if k == "plain" else f"asphalt-{k}" for k in road})
    _p = os.path.join(ASSETS, "blocktypes", "detail", "asphalt.json")
    with open(_p, encoding="utf-8") as f:
        _data = json.load(f)
    # (B7, at the user's request after B11) three plain versions sharing one ground, each at four turns, and the crack
    # (asphalt-2) and the patch (asphalt-3) one block in sixteen each
    _data["texturesByType"]["*-plain"]["all"]["alternates"] += [
        {"base": f"block/detail/asphalt-{v}", "rotation": r} if r else {"base": f"block/detail/asphalt-{v}"}
        for v in (4, 5) for r in (0, 90, 180, 270)] + [
        {"base": "block/detail/asphalt", "rotation": 180}, {"base": "block/detail/asphalt-4", "rotation": 90},
        {"base": "block/detail/asphalt-2"}, {"base": "block/detail/asphalt-3", "rotation": 90}]
    block("asphalt", {k: v for k, v in _data.items() if k != "code"})  # (graphics pass B11)
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
            faces[s] = siding_tex(siding)
            tex_by[f"*-{siding}-{s}"] = faces
    block("housewall", {"variantgroups": [{"code": "siding", "states": ["white", "blue", "yellow", "green", "brick"]}, {"code": "side", "states": SIDES}],
                        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]}, "blockmaterial": "Wood", "drawtype": "cube",
                        "texturesByType": tex_by, "lightAbsorption": 99, "resistance": 4, "sounds": WOOD,
                        "randomizeAxes": "xyz"},  # (D4) the siding's versions picked by height too
          "House walls: siding outside, plaster inside")
    name("housewall-*", "House Wall")
    cube_block("houseinterior", {"floral": "Wallpaper", "stripe": "Wallpaper", "beige": "Wallpaper", "green": "Wallpaper", "tile": "Tiled Wall"},
               ["floral", "stripe", "beige", "green", "tile"],
               {k: f"houseinterior-{k}" for k in ("floral", "stripe", "beige", "green", "tile")}, material="Wood", sounds=WOOD)
    # A house window, its outside to the north: a painted frame the depth of the wall, the glass a pixel in from the
    # outside, glazing bars across it outside and in, a sill under it outside and a narrow one inside. Lit, the glass
    # glows (in the one house in ten that still has power)
    def window(glass, glow):
        bars = []
        for side, z1, z2 in (("Out", 0.5, 1), ("In", 1.25, 1.75)):
            bars += [bx(f"Bar{side}V", (7.6, 2.5, z1), (8.4, 13.5, z2), "windowtrim"),
                     bx(f"Bar{side}H", (2, 7.6, z1), (14, 8.4, z2), "windowtrim")]
        return [bx("Head", (0, 13.5, 0), (16, 16, 16), "windowtrim"), bx("Rail", (0, 0, 0), (16, 2.5, 16), "windowtrim"),
                bx("JambL", (0, 2.5, 0), (2, 13.5, 16), "windowtrim"), bx("JambR", (14, 2.5, 0), (16, 13.5, 16), "windowtrim"),
                bx("Glass", (2, 2.5, 1), (14, 13.5, 1.25), glass, glow=glow, faces=("north", "south"), full=True),
                bx("Sill", (-0.5, 1, -1.5), (16.5, 2.5, 0), "windowtrim"), bx("Apron", (1, 0, -0.6), (15, 1, 0), "windowtrim"),
                bx("Stool", (1, 2, 16), (15, 2.5, 17), "windowtrim")] + bars
    prop("housewindow", "Window", {"dark": window("housewindow-dark", 0), "lit": window("housewindow-lit", 200)},
         box=(0, 0, 0, 1, 1, 1), material="Glass", sounds=GLASS,
         extra={"resistance": 4, "drops": [], "lightHsvByType": {"*-lit-*": [6, 4, 9]}},
         comment="A house window: frame, glass and glazing bars, a sill outside")
    for s in SIDES:
        name(f"housewindow-lit-{s}", "Lit Window")
    cube_block("houseroof", {"grey": "Roof Shingles", "brown": "Roof Shingles", "red": "Roof Shingles"}, ["grey", "brown", "red"],
               {"grey": "houseroof-grey", "brown": "houseroof-brown", "red": "houseroof-red"}, material="Wood", sounds=WOOD)
    cube_block("houseceiling", {"plain": "Ceiling", "lightoff": "Ceiling Light", "lighton": "Ceiling Light"}, ["plain", "lightoff", "lighton"],
               {"plain": "houseceiling", "lightoff": "houseceiling-lightoff", "lighton": "houseceiling-lighton"}, material="Wood", sounds=WOOD,
               lightHsvByType={"*-lighton": [6, 3, 12]}, vertexFlagsByType={"*-lighton": {"glowLevel": 120}})
    door_block("housedoor", "Front Door", "housedoor", "locked", material="Wood", sounds=WOOD, comment="A front door, locked")
    door_block("garagedoor", "Garage Door", "garagedoor", "locked", comment="A closed garage door, locked")
    # Layout version 5's houses. The floor between two storeys: boards on top, the ceiling of the room below underneath
    # (its light, dead or lit, in the middle of the room)
    storey = {}
    for kind, ceiling in (("plain", "houseceiling"), ("lightoff", "houseceiling-lightoff"), ("lighton", "houseceiling-lighton")):
        storey[f"*-{kind}"] = {"up": {"base": "block/detail/housefloor-wood"}, "down": {"base": f"block/detail/{ceiling}"},
                               "horizontals": {"base": "block/detail/houseceiling"}}
    block("housestorey", {"variantgroups": [{"code": "kind", "states": ["plain", "lightoff", "lighton"]}],
                          "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Wood", "drawtype": "cube",
                          "texturesByType": storey, "lightAbsorption": 99, "resistance": 4, "sounds": WOOD,
                          "lightHsvByType": {"*-lighton": [6, 3, 12]}},
          "The floor between a house's storeys: floorboards over the ceiling of the room below")
    name("housestorey-*", "Floorboards")
    # Wooden stairs with a carpet runner, climbing north (as the concrete ones)
    stair_boxes = [bx("Lower", (0, 0, 0), (16, 8, 16), "housefloor-wood"), bx("Upper", (0, 8, 0), (16, 16, 8), "housefloor-wood"),
                   bx("RunLower", (4, 8, 8), (12, 8.3, 16), "housefloor-carpet", faces=("up", "east", "west")),
                   bx("RunRiser", (4, 8.3, 8), (12, 16, 8.3), "housefloor-carpet", faces=("south", "east", "west")),
                   bx("RunUpper", (4, 16, 0), (12, 16.3, 8), "housefloor-carpet", faces=("up", "east", "west", "south")),
                   bx("RunFoot", (4, 0, 16), (12, 8.3, 16.3), "housefloor-carpet", faces=("south", "east", "west", "up"))]
    path = shape("housestairs", stair_boxes)
    block("housestairs", {"variantgroups": [{"code": "side", "states": SIDES}],
                          "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]}, "blockmaterial": "Wood", "drawtype": "json",
                          "shapeByType": {f"*-{s}": {"base": path, "rotateY": ROTATE[s]} for s in SIDES},
                          "collisionSelectionBoxesByType": {f"*-{s}": [cuboid((0, 0, 0, 1, 0.5, 1), s), cuboid((0, 0.5, 0, 1, 1, 0.5), s)] for s in SIDES},
                          "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 4, "sounds": WOOD},
          "Wooden stairs with a carpet runner, the variant the way they climb")
    name("housestairs-*", "Stairs")
    # A porch: its deck of boards a little off the ground with a painted skirt, the concrete step up to it, the posts
    # holding up its roof, and the lamp by the door (on the wall to the south of its block, facing north)
    prop("porchdeck", "Porch Deck", {
        "deck": [bx("Boards", (0, 0, 0), (16, 2, 16), "housefloor-porch", faces=("up",)),
                 bx("Skirt", (0, 0, 0), (16, 2, 16), "windowtrim", faces=("north", "east", "south", "west"))],
        "step": [bx("Step", (0, 0, 0), (16, 1, 16), "porchstep")]},
         box=(0, 0, 0, 1, 0.125, 1), oriented=False, comment="A porch's deck of boards, and the step up to it")
    name("porchdeck-step", "Porch Step")
    prop("porchpost", "Porch Post", porch_post(),
         box=(0.31, 0, 0.31, 0.69, 1, 0.69), oriented=False, comment="A painted post holding up a porch roof")
    # Its foot where it stands in the railing: the railing's two rails (vanilla aged fence wood) come in to the post from
    # the sides the railing goes on to (kinds named like the vanilla fence's)
    import detail_kit
    detail_kit.EXT["fencewood"] = "game:block/wood/debarked/aged"

    def post_rails(sides):
        els = porch_post()
        for side in sides:
            k = "nesw".index(side)
            for y in (1, 13):
                els.append(detail_kit.turn(bx(f"Rail{side}{y}", (7, y, 0), (9, y + 2, 5.5), "fencewood", faces=("east", "west", "up", "down")), k))
        return els
    rail_kinds = ["n", "e", "ne", "s", "ns", "es", "nes", "w", "nw", "ew", "new", "sw", "nsw", "esw", "nesw"]
    prop("porchpostrail", "Porch Post", {k: post_rails(k) for k in rail_kinds},
         box=(0.31, 0, 0.31, 0.69, 1, 0.69), oriented=False, comment="A porch post's foot in the railing, the rails coming in from the sides named")
    lamp = [bx("Plate", (6, 5, 15.3), (10, 13, 16), "metaldark"), bx("Arm", (7.5, 6, 12.2), (8.5, 7, 15.3), "metaldark"),
            bx("Base", (6, 6.5, 10.2), (10, 7, 14.2), "metaldark"), bx("Cap", (5.4, 13, 9.6), (10.6, 13.8, 14.8), "metaldark"),
            bx("Finial", (7.4, 13.8, 11.6), (8.6, 14.8, 12.8), "metaldark")]
    lamp += [bx(f"Post{i}", (x, 7, z), (x + 0.6, 13, z + 0.6), "metaldark") for i, (x, z) in
             enumerate(((5.8, 10), (9.6, 10), (5.8, 13.8), (9.6, 13.8)))]
    prop("porchlamp", "Porch Light", {
        "off": lamp + [bx("Glass", (6.1, 7, 10.3), (9.9, 13, 14.1), "porchglass-off", faces=("north", "east", "south", "west"))],
        "on": lamp + [bx("Glass", (6.1, 7, 10.3), (9.9, 13, 14.1), "lampglass", glow=230, faces=("north", "east", "south", "west"))]},
         box=(0.34, 0.3, 0.6, 0.66, 0.92, 1), collide=False, material="Metal", sounds=METAL,
         extra={"lightHsvByType": {"*-on-*": [6, 4, 11]}}, comment="A coach lamp on the wall by a front door")
    # The Suburbs' street signs: a green blade naming the west-east street on a pole, and (the block over it) the
    # blade naming the north-south one; and the guide sign toward the city, its arrow pointing north as modelled
    streets_we = ("elm", "oak", "maple", "pine", "cedar", "birch", "walnut", "ash")
    streets_ns = ("willow", "linden", "aspen", "poplar", "holly", "laurel", "spruce", "cherry")
    prop("suburbsign", "Street Sign", {k: [
        bx("Pole", (7.5, 0, 7.5), (8.5, 41, 8.5), "streetgreen"),
        bx("Blade", (-8, 36, 7.6), (24, 40, 8.4), f"suburbsign-{k}", faces=("north", "south"), full=True),
        bx("BladeEdge", (-8, 36, 7.6), (24, 40, 8.4), "streetgreen", faces=("east", "west", "up", "down"))] for k in streets_we},
         box=(0.44, 0, 0.44, 0.56, 2, 0.56), oriented=False, material="Metal", sounds=METAL,
         comment="A street-name sign on a corner of the Suburbs")
    prop("suburbsignblade", "Street Sign", {k: [
        bx("Blade", (7.6, 15, -8), (8.4, 19, 24), f"suburbsignblade-{k}", faces=("east", "west"), full=True),
        bx("BladeEdge", (7.6, 15, -8), (8.4, 19, 24), "streetgreen", faces=("north", "south", "up", "down"))] for k in streets_ns},
         box=(0.44, 0, 0.44, 0.56, 1, 0.56), oriented=False, collide=False, material="Metal", sounds=METAL,
         comment="The second blade of a Suburbs street sign, naming the street that runs north-south")
    prop("citysign", "Guide Sign", [
        bx("PostA", (7.5, 0, 2.5), (8.5, 30, 3.5), "metaldark"), bx("PostB", (7.5, 0, 12.5), (8.5, 30, 13.5), "metaldark"),
        bx("PlateE", (8.5, 18, -1), (8.8, 30, 17), "citysign-right", faces=("east",), full=True),
        bx("PlateW", (7.2, 18, -1), (7.5, 30, 17), "citysign-left", faces=("west",), full=True),
        bx("PlateEdge", (7.2, 18, -1), (8.8, 30, 17), "streetgreen", faces=("north", "south", "up", "down"))],
         box=(0.44, 0, 0.1, 0.56, 1.9, 0.9), material="Metal", sounds=METAL,
         comment="A guide sign at a Suburbs junction: DOWNTOWN, and an arrow toward the city")

    kitchen = drops(("game:salt", 0.5, 0.5), ("game:flour-spelt", 0.5, 0.5), ("cannedbeans", 0.6, 0.5), ("game:knife-generic-copper", 0.12, 0),
                    ("game:fat", 0.3, 0.3), ("crackers", 0.4, 0.4), ("game:candle", 0.2, 0.2))
    prop("kitchencabinet", "Kitchen Cupboard", [
        bx("Base", (0, 0, 3), (16, 14, 16), "cabinetfront", faces=("north",), full=True),
        bx("Sides", (0, 0, 3), (16, 14, 16), "dresserwood", faces=("east", "west", "south")),
        bx("Top", (0, 14, 2), (16, 15, 16), "formica")], box=(0, 0, 0.12, 1, 0.94, 1), extra={"drops": kitchen})
    prop("pantryshelf", "Pantry Shelf", L11.pantryshelf(), box=(0.03, 0, 0.47, 0.97, 1.75, 1),
         extra={"drops": drops(("cannedbeans", 1.2, 0.8), ("game:flour-spelt", 0.6, 0.5), ("game:salt", 0.6, 0.5), ("game:honeycomb", 0.15, 0))})
    prop("toolshelf", "Tool Shelf", DP.tool_shelf(), box=(0.03, 0, 0.53, 0.97, 1.75, 1),
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
    # (graphics pass B12, for Level 11's avenues; also the Suburbs') a stepped cast base with an access door, a pole
    # tapering at a collar, a capped top, an arm with a brace, and a cobra head: a housing over a skirt round the lens,
    # which sits flush in it (no dark gap). The lens and the light are where they were.
    street = [bx("Plinth", (5.5, 0, 5.5), (10.5, 1.5, 10.5), "metaldark", faces=("north", "east", "south", "west", "up")),
              bx("Base", (6, 1.5, 6), (10, 7, 10), "metaldark", faces=("north", "east", "south", "west", "up")),
              bx("Door", (6.75, 2.5, 5.5), (9.25, 5.5, 6), "metaldark", faces=("north", "east", "west", "up", "down")),
              bx("Pole", (7, 7, 7), (9, 40, 9), "metaldark", faces=("north", "east", "south", "west")),
              bx("Collar", (6.75, 39.5, 6.75), (9.25, 41, 9.25), "metaldark", faces=("north", "east", "south", "west", "up", "down")),
              bx("Pole2", (7.25, 41, 7.25), (8.75, 62, 8.75), "metaldark", faces=("north", "east", "south", "west")),
              bx("Cap", (6.9, 62, 6.9), (9.1, 63, 9.1), "metaldark", faces=("north", "east", "south", "west", "up")),
              bx("Arm", (7.5, 60, -2), (8.5, 61.5, 7.25), "metaldark", faces=("east", "west", "up", "down")),
              bx("Brace", (7.6, 57, 2), (8.4, 57.75, 7.25), "metaldark", rot=(-32, 0, 0), origin=(8, 57.4, 7.25)),
              bx("Head", (5.5, 58.75, -6.5), (10.5, 60.75, 1.5), "metaldark", faces=("north", "east", "south", "west", "up")),
              bx("Hood", (6, 60.75, -5.5), (10, 61.25, 0.5), "metaldark", faces=("north", "east", "south", "west", "up")),
              bx("SkirtN", (5.5, 58, -6.5), (10.5, 58.75, -5.5), "metaldark", faces=("north", "east", "west", "down")),
              bx("SkirtS", (5.5, 58, 0.5), (10.5, 58.75, 1.5), "metaldark", faces=("south", "east", "west", "down")),
              bx("SkirtW", (5.5, 58, -5.5), (6, 58.75, 0.5), "metaldark", faces=("west", "down")),
              bx("SkirtE", (10, 58, -5.5), (10.5, 58.75, 0.5), "metaldark", faces=("east", "down"))]
    prop("streetlight", "Street Light", {
        "on": street + [bx("Lens", (6, 58.1, -5.5), (10, 58.75, 0.5), "streetlamp", glow=240, faces=("down",))],
        "off": street + [bx("Lens", (6, 58.1, -5.5), (10, 58.75, 0.5), "streetlampoff", faces=("down",))],
        "flicker": street + [bx("Lens", (6, 58.1, -5.5), (10, 58.75, 0.5), "streetlamp", glow=240, faces=("down",))]},
         box=(0.4, 0, 0.4, 0.6, 2, 0.6), material="Metal", sounds=METAL,
         extra={"lightHsvByType": {"*-on-*": [6, 3, 15]}, "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
                "attributesByType": {f"*-flicker-{s}": {"offBlock": f"backrooms:streetlight-off-{s}"} for s in SIDES}})
    prop("mailbox", "Mailbox", L11.mailbox(), box=(0.3, 0, 0.25, 0.7, 1.1, 0.8), material="Metal", sounds=METAL,
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
    # Board and batten in three versions, the third gone thin at the foot (graphics pass B11); otherwise as cube_block
    block("barnwall", {"variantgroups": [{"code": "kind", "states": ["red", "grey"]}],
                       "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Wood", "drawtype": "cube",
                       "texturesByType": {f"*-{k}": {"all": {"base": f"block/detail/barnwall-{k}", "alternates": [
                           {"base": f"block/detail/barnwall-{k}-{n}"} for n in (2, 3)]}} for k in ("red", "grey")},
                       "lightAbsorption": 99, "resistance": 4, "sounds": WOOD, "randomizeAxes": "xyz"})  # (D4) by height too
    name("barnwall-red", "Barn Boards")
    name("barnwall-grey", "Weathered Boards")
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
    prop("feedtrough", "Feed Trough", DP.feed_trough(),
         box=(0, 0, 0.25, 1, 0.44, 0.75), sounds=WOOD, extra={"drops": [{"type": "block", "code": "game:trough-genericwood-small-ns", "quantity": {"avg": 1, "var": 0}}]
                            + drops(("game:drygrass", 1, 1))})  # (from layout version 10 a vanilla trough stands here)
    prop("toolrack", "Tool Rack", DP.tool_rack(),
         box=(0, 0, 0.7, 1, 1.75, 1), extra={"drops": drops(("game:hoe-copper", 0.3, 0), ("game:scythe-copper", 0.2, 0), ("game:shovel-copper", 0.2, 0),
                                                              ("game:rope", 0.5, 0.4))})
    prop("nailbarrel", "Barrel of Nails", DP.nail_barrel(), box=(0.12, 0, 0.12, 0.88, 0.88, 0.88), oriented=False,
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
    # the side named. Since graphics pass B11 the world generator places "pitchroof" (roofs(), below); this old block
    # stays for the roofs of saved worlds, with the new roofing over its boarded gable fill
    materials = {"grey": "houseroof-grey", "brown": "houseroof-brown", "red": "houseroof-red", "barn": "barnroof"}
    shapes = roofslope_shapes()
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
                tex[f] = siding_tex(siding)
            corner_by[f"*-{siding}-{corner}"] = tex
    block("housecorner", {"variantgroups": [{"code": "siding", "states": ["white", "blue", "yellow", "green", "brick"]}, {"code": "corner", "states": ["ne", "nw", "se", "sw"]}],
                          "creativeinventory": {"general": ["*-ne"], "construction": ["*-ne"]}, "blockmaterial": "Wood", "drawtype": "cube",
                          "texturesByType": corner_by, "lightAbsorption": 99, "resistance": 4, "sounds": WOOD,
                          "randomizeAxes": "xyz"},  # (D4) the siding's versions picked by height too
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
    prop("firehydrant", "Fire Hydrant", L11.hydrant(), box=(0.3, 0, 0.3, 0.7, 0.81, 0.7), material="Metal", sounds=METAL)
    prop("stopsign", "Stop Sign", stop_sign(),
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
    # (deep props) the pump works: it gives Almond Water like a seep, a few portions that come back (BackroomsDispenser)
    prop("waterpump", "Hand Pump", DP.hand_pump(),
         box=(0.3, 0, 0.3, 0.7, 1.06, 0.7), oriented=False, material="Metal", sounds=METAL,
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:almondwater"], "restock": True, "dispenseSound": "game:sounds/effect/water-pour"}})
    prop("tractor", "Old Tractor", [
        bx("Body", (8, 10, 6), (24, 22, 30), "tractorgreen"), bx("Hood", (10, 12, 0), (22, 20, 8), "tractorgreen"),
        bx("Grille", (10.5, 12.5, -0.2), (21.5, 19.5, 0), "grate", faces=("north",), full=True),
        *tractor_wheel("WheelRL", 0, 7, 11, 35, 11), *tractor_wheel("WheelRR", 25, 32, 11, 35, 11),
        *tractor_wheel("WheelFL", 3, 8, 5.5, 9, 5.5), *tractor_wheel("WheelFR", 24, 29, 5.5, 9, 5.5),
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
    # Out in the crops: a galvanised trough with rolled rims and ribbed sides, full of rainwater (a hand pump stands at
    # its east end), and a five-bar field gate off its hinges, lying flat, its hanging post still standing
    prop("watertrough", "Water Trough", [
        bx("Side1", (0.5, 1, 3), (15.5, 9, 4), "galvanised"), bx("Side2", (0.5, 1, 12), (15.5, 9, 13), "galvanised"),
        bx("End1", (0, 1, 3.5), (1, 9, 12.5), "galvanised"), bx("End2", (15, 1, 3.5), (16, 9, 12.5), "galvanised"),
        bx("Bottom", (1, 1, 4), (15, 2, 12), "galvanised"),
        bx("Water", (1, 7, 4), (15, 7.5, 12), "troughwater", faces=("up",)),
        bx("Rim1", (0, 9, 2.5), (16, 9.6, 4), "steel"), bx("Rim2", (0, 9, 12), (16, 9.6, 13.5), "steel"),
        bx("Skid1", (2, 0, 3), (4, 1, 13), "wooddark"), bx("Skid2", (12, 0, 3), (14, 1, 13), "wooddark")],
         box=(0, 0, 0.16, 1, 0.6, 0.84), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 2, 1), ("game:metalnailsandstrips-iron", 0.6, 0.4))},
         comment="A galvanised water trough out in a field, full of rainwater, a hand pump at its end")
    gate = [bx("Post", (0, 0, 13), (2.5, 22, 15.5), "wooddark"), bx("Hinge1", (2.5, 6, 13.6), (3.5, 7, 14.6), "metaldark"),
            bx("Hinge2", (2.5, 16, 13.6), (3.5, 17, 14.6), "metaldark"),
            bx("Stile1", (3, 0, 0), (5, 1.6, 15), "wood"), bx("Stile2", (37, 0, 0), (39, 1.6, 15), "wood")]
    for k, z in enumerate((0.5, 4, 7.5, 11, 13.5)):
        gate.append(bx(f"Bar{k}", (3, 0.3, z), (39, 1.5, z + 1.4), "wood"))
    gate.append(bx("Brace", (4, 0.4, 7), (38, 1.4, 8.4), "wood", rot=(0, 21, 0)))
    prop("fallengate", "Fallen Gate", gate, box=(0, 0, 0, 1, 0.12, 1), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:plank-aged", 3, 1), ("game:metalnailsandstrips-iron", 0.5, 0.4))},
         comment="A field gate off its hinges, lying flat in a trampled patch of the crops, its hanging post still standing")

    # Level 5: the corridors
    prop("icemachine", "Ice Machine", L5.ice_machine(),  # (Level 5 art)
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



# ======================= Graphics pass B11: pitched roofs, course by course =======================
#
# A roof rises half a block for each block in from its eaves (RoofBits in Tiles.cs), so every roof block holds one
# run of 16 across and 8 up, built here sloping down to the north (low edge at z = 0) and turned by the block's side.
# What the old roofslope block drew as one tilted slab is now:
#   - the roofing as courses: four tilted boards to the block, each pitched a little flatter than the roof so its
#     lower edge (the butt) stands proud of the course below, which gives a real shadow line every quarter block and a
#     stepped edge at the gables; their tops carry the shingle texture, a course to a quarter of it;
#   - a thin deck under them on the roof's true line, its underside the soffit (beadboard under a porch roof);
#   - at the eaves an overhang with a fascia board, a boxed soffit back to the wall and a gutter;
#   - at the ridge a cap, either split between the two blocks that meet there (form "peak") or, where the rows on
#     either side are half a block lower, a ridge of its own rising to a point in the middle of the block ("ridge");
#   - over a gable wall, the gable itself: the wall's own siding in fine steps up to the roof line, its texture laid
#     the way the wall below lays it so boards and bricks run on unbroken, and a rake board along the edge.
# The block "pitchroof" carries the cover (shingle colour, or the barns' tin), the gable siding ("none" inside the
# roof), the form and the side; the world generator picks the form from the neighbouring tiles (WorldGenerator.Deep.cs,
# RoofAt). The old "roofslope" block stays for saved worlds, with the new roofing over its old boarded gable fill.

ROOF_RISE = math.atan2(8, 16)
ROOF_RUN = math.hypot(16, 8)        # the length of the slope across one block
COURSES = 4                          # courses to a block of roof
COURSE = ROOF_RUN / COURSES
COURSE_T = 0.3                       # a course's thickness
COURSE_LIFT = 0.3                    # how far a course's butt stands off the one below
DECK_T = 0.3
PITCH_COVERS = ["grey", "brown", "red", "barn"]
PITCH_GABLES = ["none", "white", "blue", "yellow", "green", "brick", "barnred", "barngrey"]
PITCH_FORMS = ["eave", "lower", "upper", "peaklower", "peakupper", "ridgelower", "ridgeupper"]
PITCH_LOW = ("eave", "lower", "peaklower", "ridgelower")  # the forms in the lower half of their block


def _r(v):
    return round(v, 4)


def _slope_el(name, s0, s1, ya, y_lo, y_hi, x0, x1, faces, angle, about_hi=False):
    """A box lying along the slope from s0 to s1 (distances along the roof line from the block's low edge, where the
    line is at height ya), between y_lo and y_hi measured square to the line (negative below it), tilted by `angle`
    degrees about its lower end on the line (or its upper end with about_hi). faces: {face: (key, uv[, rotation])}."""
    c, s = math.cos(ROOF_RISE), math.sin(ROOF_RISE)
    pivot = s1 if about_hi else s0
    pz, py = pivot * c, ya + pivot * s
    length = s1 - s0
    z0 = pz - (length if about_hi else 0)
    el = {"name": name, "from": [_r(x0), _r(py + y_lo), _r(z0)], "to": [_r(x1), _r(py + y_hi), _r(z0 + length)],
          "rotationOrigin": [_r(x0), _r(py), _r(pz)], "rotationX": _r(-angle), "faces": {}}
    for f, spec in faces.items():
        face = {"texture": "#" + spec[0], "uv": [_r(v) for v in spec[1]]}
        if len(spec) > 2 and spec[2]:
            face["rotation"] = spec[2]
        el["faces"][f] = face
    return el


def _box_el(name, frm, to, faces):
    el = {"name": name, "from": [_r(v) for v in frm], "to": [_r(v) for v in to], "faces": {}}
    for f, spec in faces.items():
        face = {"texture": "#" + spec[0], "uv": [_r(v) for v in spec[1]]}
        el["faces"][f] = face
    return el


def _mirror_z(els):
    """The elements mirrored front to back (z -> 16 - z): a run sloping down to the north becomes one sloping down to
    the south. Up and down faces are turned half round so their textures still read from the low edge."""
    out = []
    for e in json.loads(json.dumps(els)):
        z1, z2 = e["from"][2], e["to"][2]
        e["from"][2], e["to"][2] = _r(16 - z2), _r(16 - z1)
        if "rotationOrigin" in e:
            e["rotationOrigin"][2] = _r(16 - e["rotationOrigin"][2])
            e["rotationX"] = -e["rotationX"]
        f = e["faces"]
        new = {}
        for k, v in f.items():
            k2 = {"north": "south", "south": "north"}.get(k, k)
            if k in ("up", "down"):
                v["rotation"] = (v.get("rotation", 0) + 180) % 360
            new[k2] = v
        e["faces"] = new
        out.append(e)
    return out


def _run(ya, s_from, s_to, tag, eave=False):
    """The roofing of one run sloping down to the north: the deck and the courses from s_from to s_to along the slope
    (s = 0 at z = 0, height ya there), each course a quarter of the shingle texture."""
    deg = math.degrees(ROOF_RISE)
    els = [_slope_el(f"Deck{tag}", s_from, s_to, ya, -DECK_T, 0, 0, 16,
                     {"down": ("deck", [0, 0, 16, min(16, s_to - s_from)])}, deg)]
    k = 0
    s = s_from
    while s < s_to - 0.01:
        s1 = min(s_to, s + COURSE)
        n = int(round(s / COURSE)) % COURSES
        tilt = deg - math.degrees(math.atan2(COURSE_LIFT, s1 - s))
        v0 = n * 16 / COURSES
        els.append(_slope_el(f"Course{tag}{k}", s, s1, ya, 0, COURSE_T, 0, 16, {
            "up": ("shingle", [0, v0, 16, v0 + 16 / COURSES]),
            "north": ("edge", [0, 0, 16, 1]), "east": ("edge", [0, 0, s1 - s, 1]), "west": ("edge", [0, 0, s1 - s, 1]),
            "down": ("edge", [0, 0, 16, s1 - s])},
            tilt, about_hi=True))
        s, k = s1, k + 1
    return els


def _eave():
    """The overhang under the lowest course: a fascia at its edge, a boxed soffit back to the wall, the gutter, and
    the ends of the box where a gable comes down to it."""
    c, s = math.cos(ROOF_RISE), math.sin(ROOF_RISE)
    ze, ye = -COURSE * c, -COURSE * s  # the overhang's edge on the roof line: z -4, y -2
    trim = lambda w, h: ("trim", [0, 0, min(16, w), min(16, h)])
    return [
        _box_el("Fascia", (0, ye - 1.6, ze - 0.5), (16, ye + COURSE_LIFT, ze), {
            "north": trim(16, 2.15), "up": trim(16, 0.5), "down": trim(16, 0.5), "east": trim(0.5, 2.15), "west": trim(0.5, 2.15)}),
        _box_el("Soffit", (0, ye - 1.6, ze), (16, ye - 1.3, 0), {
            "down": ("deck", [0, 0, 16, -ze]), "east": trim(-ze, 0.3), "west": trim(-ze, 0.3)}),
        _box_el("EaveEnd1", (0, ye - 1.3, ze), (16, ye - 0.3, 0), {"east": trim(-ze, 1), "west": trim(-ze, 1)}),
        _box_el("EaveEnd2", (0, ye - 0.3, ze / 2), (16, ye / 2 - 0.3, 0), {"east": trim(-ze / 2, 1), "west": trim(-ze / 2, 1)}),
        _box_el("Gutter", (0, ye - 1.5, ze - 2.0), (16, ye + 0.3, ze - 0.5), {
            "up": ("gutter", [0, 0, 16, 1.5]), "north": ("gutter", [0, 0, 16, 1.8]), "down": ("gutter", [0, 14, 16, 15.5]),
            "east": ("gutter", [0, 0, 1.5, 1.8]), "west": ("gutter", [0, 0, 1.5, 1.8])}),
    ]


def _gable(profile, yb_floor=0.0):
    """The gable under the roof line: the wall's siding in steps of 2 px, each square to the block grid with its texture
    laid as on the wall below (east u = 16 - z, west u = z, v = 16 - y), kept clear of the deck."""
    els = []
    for k in range(8):
        z1, z2 = 2.0 * k, 2.0 * k + 2
        top = min(profile(z1), profile(z2)) - DECK_T / math.cos(ROOF_RISE) - 0.1
        if top <= yb_floor + 0.05:
            continue
        els.append(_box_el(f"Gable{k}", (0, 0, z1), (16, top, z2), {
            "east": ("gable", [16 - z2, 16 - top, 16 - z1, 16]), "west": ("gable", [z1, 16 - top, z2, 16])}))
    return els


def _rake(ya, s_from, s_to, tag):
    """The rake boards along both ends of a run (the one at the gable shows; the other lies in the attic)."""
    deg = math.degrees(ROOF_RISE)
    L = s_to - s_from
    els = []
    for side, x0, x1 in (("W", -0.25, 0.75), ("E", 15.25, 16.25)):
        els.append(_slope_el(f"Rake{side}{tag}", s_from, s_to, ya, -1.6, -DECK_T, x0, x1, {
            "west" if side == "W" else "east": ("trim", [0, 0, min(16, L), 1.3]),
            "down": ("trim", [0, 0, 1, min(16, L)]), "north": ("trim", [0, 0, 1, 1.3])}, deg))
    return els


def pitch_shape(form, gable):
    """The elements of one pitched-roof block (see the section's note)."""
    yb = 8.0 if form.endswith("upper") else 0.0
    half = ROOF_RUN / 2
    if form.startswith("ridge"):
        north = _run(yb, 0, half, "N")
        els = north + _mirror_z(north)
        els.append(_box_el("Cap", (0, yb + 3.5, 5.8), (16, yb + 4.6, 10.2), {
            "up": ("cap", [0, 0, 16, 4.4]), "north": ("edge", [0, 0, 16, 1.1]), "south": ("edge", [0, 0, 16, 1.1]),
            "east": ("edge", [0, 0, 4.4, 1.1]), "west": ("edge", [0, 0, 4.4, 1.1])}))
        if gable:
            els += _gable(lambda z: yb + min(z, 16 - z) / 2, 0)
            rake = _rake(yb, 0, half, "N")
            els += rake + _mirror_z(rake)
        return els
    els = _run(yb, -COURSE if form == "eave" else 0, ROOF_RUN, "")
    if form == "eave":
        els += _eave()
    if form.startswith("peak"):
        els.append(_box_el("Cap", (0, yb + 7.5, 13.8), (16, yb + 8.6, 16), {
            "up": ("cap", [0, 0, 16, 2.2]), "north": ("edge", [0, 0, 16, 1.1]),
            "east": ("edge", [0, 0, 2.2, 1.1]), "west": ("edge", [0, 0, 2.2, 1.1])}))
    if gable:
        els += _gable(lambda z: yb + z / 2, 0)
        els += _rake(yb, 0, ROOF_RUN, "")
    return els


PITCH_DEFAULTS = {"shingle": "houseroof-grey", "edge": "roofedge-grey", "cap": "roofcap-grey", "deck": "soffit",
                  "trim": "windowtrim", "gutter": "gutter", "gable": "siding-white"}


def pitch_shape_file(name, els):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16,
            "textures": {k: f"backrooms:block/detail/{PITCH_DEFAULTS[k]}" for k in keys}, "elements": els}
    write_json(os.path.join(ASSETS, "shapes", "block", "detail", name + ".json"), data)
    return "block/detail/" + name


def _tex(base, alts=0):
    t = {"base": f"block/detail/{base}"}
    if alts:
        t["alternates"] = [{"base": f"block/detail/{base}-{k}"} for k in range(2, alts + 2)]
    return t


def pitch_textures(cover, gable):
    if cover == "barn":
        t = {"shingle": _tex("barnroof", 2), "edge": _tex("roofedge-barn"), "cap": _tex("roofcap-barn"),
             "deck": _tex("barndeck"), "trim": _tex("wooddark"), "gutter": _tex("wooddark")}
    else:
        t = {"shingle": _tex(f"houseroof-{cover}", 2), "edge": _tex(f"roofedge-{cover}"), "cap": _tex(f"roofcap-{cover}"),
             "deck": _tex("soffit"), "trim": _tex("windowtrim"), "gutter": _tex("gutter")}
    if gable in ("barnred", "barngrey"):
        t["gable"] = _tex(f"barnwall-{gable[4:]}", 2)
    elif gable == "brick":
        t["gable"] = _tex("siding-brick")
    elif gable != "none":
        t["gable"] = _tex(f"siding-{gable}", 2)
    return t


def roofs():
    """The pitched roofs of the Suburbs' houses and the farms' barns and sheds (see the section's note)."""
    shapes = {}
    for form in PITCH_FORMS:
        for g in (False, True):
            shapes[(form, g)] = pitch_shape_file(f"pitchroof-{form}" + ("-gable" if g else ""), pitch_shape(form, g))
    allowed, shape_by, tex_by = [], {}, {}
    for cover in PITCH_COVERS:
        gables = ["none", "barnred", "barngrey"] if cover == "barn" else ["none", "white", "blue", "yellow", "green", "brick"]
        for g in gables:
            allowed.append(f"pitchroof-{cover}-{g}-*")
            tex_by[f"*-{cover}-{g}-*"] = pitch_textures(cover, g)
    # (first match wins: the roof's own blocks, then the ones over a gable)
    for form in PITCH_FORMS:
        for s in SIDES:
            shape_by[f"*-none-{form}-{s}"] = {"base": shapes[(form, False)], "rotateY": ROTATE[s]}
    for form in PITCH_FORMS:
        for s in SIDES:
            shape_by[f"*-{form}-{s}"] = {"base": shapes[(form, True)], "rotateY": ROTATE[s]}
    half = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}
    full = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}
    boxes = {f"*-{f}-*": half for f in PITCH_LOW}
    boxes["*"] = full
    block("pitchroof", {
        "variantgroups": [{"code": "cover", "states": PITCH_COVERS}, {"code": "gable", "states": PITCH_GABLES},
                          {"code": "form", "states": PITCH_FORMS}, {"code": "side", "states": SIDES}],
        "allowedVariants": allowed,
        "creativeinventory": {"general": ["*-none-lower-north", "*-none-eave-north"],
                              "construction": ["*-none-lower-north", "*-none-eave-north"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by, "texturesByType": tex_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 2,
        "collisionboxByType": boxes, "selectionboxByType": boxes, "sounds": WOOD},
        "Pitched roofs (from the graphics pass): shingled in courses, with eaves, ridges and gables in the house's siding")
    name("pitchroof-barn-*", "Barn Roof")
    name("pitchroof-*", "Roof Shingles")


def roofslope_shapes():
    """New roofing for the old roofslope block (saved worlds): the courses and deck above, and under them its boarded
    gable fill, now in fine steps, in the trim it always had."""
    paths = {}
    for mat in ("grey", "brown", "red", "barn"):
        tex = pitch_textures(mat, "none")
        trim = "block/detail/wooddark" if mat == "barn" else "block/detail/white"
        for half, yb in (("lower", 0.0), ("upper", 8.0)):
            els = _run(yb, 0, ROOF_RUN, "")
            for e in _gable(lambda z: yb + z / 2, 0):
                e["faces"] = {f: dict(v, texture="#fill") for f, v in e["faces"].items()}
                e["faces"]["north"] = {"texture": "#fill", "uv": [0, 0, 16, min(16, e["to"][1])]}
                els.append(e)
            keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
            table = {k: ("backrooms:" + (trim if k == "fill" else tex[k]["base"])) for k in keys}
            data = {"textureWidth": 16, "textureHeight": 16, "textures": table, "elements": els}
            write_json(os.path.join(ASSETS, "shapes", "block", "detail", f"roofslope-{mat}-{half}.json"), data)
            paths[(mat, half)] = f"block/detail/roofslope-{mat}-{half}"
    return paths


def generate():
    deep_textures.generate()
    deepprops_tex.generate()  # (deep props) the signs, doors, shelf, rack, barrel, trough and pump
    refinements()
    roofs()
    level6()
    level61()
    level7()
    level8()
    level9()
    import gen_suburbs  # (Level 9's houses from layout version 9)
    gen_suburbs.generate()
    level10()
