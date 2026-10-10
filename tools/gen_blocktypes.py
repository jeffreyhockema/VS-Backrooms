"""Generates block type definitions for Levels 3-5, which have many similar blocks.

Run from the repo root:  python tools/gen_blocktypes.py
Blocks for Levels 0-2 are hand-written in assets/backrooms/blocktypes.
"""
import json
import os

import fire_fx

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets", "backrooms", "blocktypes")

SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}

STONE = {"walk": "game:walk/stone", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}


DEAD_LIGHT_DROPS = [
    {"type": "item", "code": "glassshard", "quantity": {"avg": 1.5, "var": 0.5}},
    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.25, "var": 0}},
    {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0}},
]
CEILING_DROPS = [
    {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.12, "var": 0}},
    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.08, "var": 0}},
    {"type": "item", "code": "rottenwood", "quantity": {"avg": 0.1, "var": 0}},
    # Crumbled gypsum: enough to mark a wall or two
    {"type": "item", "code": "chalk", "quantity": {"avg": 0.12, "var": 0}},
]


# ---- Flames, fire, smoke and steam (offsets from the top middle of each block's first collision box) ----

def _sconce_flames():
    """The hotel sconce panel carries a candle on each of its four faces, its top 12/16 up and 3/16 out."""
    return [fire_fx.flame(dx, -0.25, dz) for dx, dz in ((0, -0.6875), (0.6875, 0), (0, 0.6875), (-0.6875, 0))]


def _chandelier_flames():
    """The chandelier's eight candles on its ring, their tops 8.5/16 up (the box tops out at 1)."""
    return [fire_fx.flame(x / 16 - 0.5, 8.5 / 16 - 1, z / 16 - 0.5, quantity=0.08)
            for x, z in ((-3, -3), (8, -4), (19, -3), (-4, 8), (20, 8), (-3, 19), (8, 20), (19, 19))]


# Boilers and furnaces: the box (0.06-0.94, 0.125-0.94) puts the top middle at x 0.5, z 0.5325
_MID_Z = (0.125 + 0.94) / 2


def _furnace_fx(side):
    """Fire licking behind the glowing door (2-9/16 up, 1.6/16 from the north face), now and then a spark out of it,
    and a thin smoke off the hood."""
    x, z = fire_fx.turn(0.5, 0.06, side)
    out_x, out_z = fire_fx.turn(0.5, -0.5, side)
    out_x, out_z = (out_x - 0.5) * 0.3, (out_z - 0.5) * 0.3
    along = (0.17, 0.04, 0.01) if side in ("north", "south") else (0.01, 0.04, 0.17)
    return [fire_fx.fire(x - 0.5, -0.8, z - _MID_Z, spread=along, quantity=0.3, size=0.14, rise=0.06),
            fire_fx.embers(x - 0.5, -0.78, z - _MID_Z, spread=along, quantity=0.006, velocity=(out_x, 0.3, out_z)),
            fire_fx.smoke(0, 0, 0, spread=0.3, quantity=0.02, life=4, value=55, alpha=110)]


def _boiler_fx(side):
    """Steam wisping from the collar where the flue leaves the boiler (26/16 up, at 8, 9 on the north-facing model)."""
    x, z = fire_fx.turn(0.5, 9 / 16, side)
    return [fire_fx.steam(x - 0.5, 26 / 16 - 1, z - _MID_Z, quantity=0.05)]


def threshold(kind):
    """Using the block asks ThresholdSystem where it leads."""
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


def write(folder, code, block, comment=None):
    path = os.path.join(OUT, folder, code + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(block, indent="\t")
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def cube(folder, code, texture, material="Stone", sounds=STONE, states=None, comment=None, **extra):
    block = {"code": code}
    if states:
        block["variantgroups"] = [{"code": "type", "states": states}]
    block.update({
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": material,
        "drawtype": "cube",
        "textures": {"all": {"base": texture}},
        "resistance": 8 if material == "Stone" else 2,
        "lightAbsorption": 99,
        "sounds": sounds,
    })
    if material == "Stone":
        block["requiredMiningTier"] = 3
    block.update(extra)
    write(folder, code, block, comment)


def shaped(folder, code, shape, material="Wood", sounds=WOOD, oriented=True, box=None, comment=None, **extra):
    """A prop drawn from a shape, optionally with a north/east/south/west variant per facing."""
    block = {"code": code}
    if oriented:
        block["variantgroups"] = [{"code": "side", "states": SIDES}]
        block["shapeByType"] = {f"*-{s}": {"base": shape, "rotateY": ROTATE[s]} for s in SIDES}
        block["creativeinventory"] = {"general": ["*-north"], "decorative": ["*-north"]}
    else:
        block["shape"] = {"base": shape}
        block["creativeinventory"] = {"general": ["*"], "decorative": ["*"]}
    block.update({
        "blockmaterial": material,
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 2,
        "sounds": sounds,
    })
    if box:
        x1, y1, z1, x2, y2, z2 = box
        block["collisionbox"] = block["selectionbox"] = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    block.update(extra)
    write(folder, code, block, comment)


def level3():
    cube("level3", "l3wall", "block/level3/l3wall-{type}", states=["glazed", "brick", "cinder"],
         comment="Level 3 walls: two-tone glazed structural tile, red brick, and cinder block in the machine rooms")
    fixture = {
        "code": "l3wallfixture",
        "variantgroups": [{"code": "material", "states": ["glazed", "brick", "cinder"]}, {"code": "fixture", "states": ["pipes", "panel", "fan"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Stone",
        "drawtype": "json",
        "shapeByType": {"*": {"base": "block/l3wall-{material}-{fixture}"}},
        "textures": {"all": {"base": "block/level3/l3wall-{material}"}},
        "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE,
    }
    write("level3", "l3wallfixture", fixture, "Level 3 walls carrying 3D pipes, electrical panels or industrial fans")
    cube("level3", "dustyfloor", "block/level3/dustyfloor", comment="Dusty concrete floor")
    cube("level3", "plasterceiling", "block/level3/plasterceiling", comment="Peeling, stained plaster ceiling")
    cube("level3", "roomsign", "block/level3/roomsign-{type}", states=[str(i) for i in range(8)],
         comment="White machine-room signs with a 3-digit number and illegible text beneath")
    cube("level3", "windowglow", "block/level3/windowglow", material="Glass", sounds=GLASS,
         comment="A window behind bars, glowing like a sunny day", lightHsv=[8, 2, 16], lightAbsorption=0,
         vertexFlags={"glowLevel": 200})

    cables = {
        "code": "cables",
        "variantgroups": [{"code": "type", "states": ["run-we", "run-ns", "hub"]}],
        "creativeinventory": {"general": ["*-run-we", "*-hub"], "decorative": ["*-run-we", "*-hub"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-hub": {"base": "block/cables-hub"}, "*-we": {"base": "block/cables-run", "rotateY": 0}, "*-ns": {"base": "block/cables-run", "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0.7, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0.7, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "lightAbsorption": 0, "resistance": 2, "sounds": METAL,
    }
    write("level3", "cables", cables, "Bundled cables in trays under the ceiling")

    light = {
        "code": "cablelight",
        "variantgroups": [{"code": "state", "states": ["warm", "off", "flicker"]}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": {
            "*-off-we": {"base": "block/cablelight-off", "rotateY": 0}, "*-off-ns": {"base": "block/cablelight-off", "rotateY": 90},
            "*-we": {"base": "block/cablelight-lit", "rotateY": 0}, "*-ns": {"base": "block/cablelight-lit", "rotateY": 90},
        },
        "lightHsvByType": {"*-warm-*": [5, 5, 13]},
        "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
        "attributesByType": {"*-flicker-we": {"offBlock": "backrooms:cablelight-off-we"}, "*-flicker-ns": {"offBlock": "backrooms:cablelight-off-ns"}},
        "dropsByType": {"*-off-*": DEAD_LIGHT_DROPS, "*-flicker-*": [{"type": "block", "code": "cablelight-off-we"}]},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0.55, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0.55, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "lightAbsorption": 0, "resistance": 0.8, "sounds": GLASS,
    }
    write("level3", "cablelight", light, "Dim amber fluorescent fixtures hanging from the cable trays")

    shaped("level3", "transformer", "block/transformer", material="Metal", sounds=METAL, oriented=False,
           comment="Humming transformer", box=(0.05, 0, 0.15, 0.95, 1, 0.85),
           sounds_override=None)
    bars = {
        "code": "ironbars",
        "variantgroups": [{"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "construction": ["*-we"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-we": {"base": "block/ironbars", "rotateY": 0}, "*-ns": {"base": "block/ironbars", "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.4, "x2": 1, "y2": 1, "z2": 0.6}, "*-ns": {"x1": 0.4, "y1": 0, "z1": 0, "x2": 0.6, "y2": 1, "z2": 1}},
        "selectionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.4, "x2": 1, "y2": 1, "z2": 0.6}, "*-ns": {"x1": 0.4, "y1": 0, "z1": 0, "x2": 0.6, "y2": 1, "z2": 1}},
        "lightAbsorption": 0, "resistance": 4, "drops": [], "sounds": METAL,
    }
    write("level3", "ironbars", bars, "Indestructible bars: the way on is visible but out of reach")
    shaped("level3", "manhole", "block/manhole", material="Metal", sounds=METAL, oriented=False,
           comment="An open manhole: the frame is solid, the middle drops into the flooded tunnel below",
           collisionSelectionBoxes=[
               {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 0.1875},
               {"x1": 0, "y1": 0, "z1": 0.8125, "x2": 1, "y2": 1, "z2": 1},
               {"x1": 0, "y1": 0, "z1": 0.1875, "x2": 0.1875, "y2": 1, "z2": 0.8125},
               {"x1": 0.8125, "y1": 0, "z1": 0.1875, "x2": 1, "y2": 1, "z2": 0.8125}],
           resistance=8, requiredMiningTier=3)
    shaped("level3", "rungs", "block/rungs", material="Metal", sounds=METAL, oriented=False,
           comment="Ladder rungs down the manhole shaft", climbable=True,
           collisionbox=None, selectionbox={"x1": 0.1875, "y1": 0, "z1": 0, "x2": 0.8125, "y2": 1, "z2": 0.125})


def level4():
    cube("level4", "officewall", "block/level4/officewall", comment="Off-white office drywall")
    cube("level4", "officewindow", "block/level4/officewindow", material="Glass", sounds=GLASS,
         comment="A window onto rain and fog that never ends; its grey storm light is the main light on the floor",
         lightHsv=[36, 1, 7], lightAbsorption=0, drops=[],
         sounds_override=None)
    glass = {
        "code": "officeglass", "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Glass", "drawtype": "cube", "renderpass": "Transparent",
        "textures": {"all": {"base": "block/level4/officeglass"}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "faceCullMode": "NeverCull",
        "lightAbsorption": 0, "resistance": 1, "sounds": GLASS,
    }
    write("level4", "officeglass", glass, "Glass conference-room partition")
    cube("level4", "officecarpet", "block/level4/officecarpet-{type}", material="Cloth", sounds=CLOTH, states=["plain", "ghost"],
         comment="Low-pile office carpet; 'ghost' has the darker mark of furniture that once stood there")
    cube("level4", "officeceiling", "block/level4/officeceiling", material="Ceramic", sounds=GLASS,
         comment="2x4 drop-ceiling tiles; the void above sometimes hides wire, brackets and rotten battens", drops=CEILING_DROPS, resistance=1)
    light = {
        "code": "officelight",
        "variantgroups": [{"code": "state", "states": ["on", "lit", "off", "flicker"]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Glass", "drawtype": "cube",
        "texturesByType": {"*-off": {"all": {"base": "block/level4/officelight-off"}}, "*": {"all": {"base": "block/level4/officelight-on"}}},
        "lightHsvByType": {"*-on": [10, 1, 17]},
        "vertexFlagsByType": {"*-on": {"glowLevel": 160}, "*-lit": {"glowLevel": 160}, "*-flicker": {"glowLevel": 160}},
        "entityClassByType": {"*-flicker": "BackroomsFlicker"},
        "attributesByType": {"*-flicker": {"offBlock": "backrooms:officelight-off"}},
        "dropsByType": {"*-off": DEAD_LIGHT_DROPS},
        "lightAbsorption": 0, "resistance": 0.8, "sounds": GLASS,
    }
    write("level4", "officelight", light, "Fluorescent troffers; about half are dead and their switches are missing")
    cube("level4", "elevatordoor", "block/level4/elevatordoor-{type}", material="Metal", sounds=METAL, states=["lower", "upper"],
         comment="Elevator doors. Use them: each elevator leads to one fixed place, usually another elevator on another level",
         drops=[], behaviors=threshold("elevator"))
    partition = {
        "code": "partition", "variantgroups": [{"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Cloth", "drawtype": "json",
        "shapeByType": {"*-we": {"base": "block/partition", "rotateY": 0}, "*-ns": {"base": "block/partition", "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.375, "x2": 1, "y2": 1.5, "z2": 0.625}, "*-ns": {"x1": 0.375, "y1": 0, "z1": 0, "x2": 0.625, "y2": 1.5, "z2": 1}},
        "selectionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.375, "x2": 1, "y2": 1.5, "z2": 0.625}, "*-ns": {"x1": 0.375, "y1": 0, "z1": 0, "x2": 0.625, "y2": 1.5, "z2": 1}},
        "lightAbsorption": 0, "resistance": 1, "sounds": CLOTH,
    }
    write("level4", "partition", partition, "Blue-grey fabric cubicle partition, about 1.5 m tall")
    shaped("level4", "desk", "block/desk", comment="Desk with an old desktop computer", box=(0, 0, 0.125, 1, 0.8, 0.875))
    shaped("level4", "officechair", "block/officechair", material="Cloth", sounds=CLOTH, comment="Office chair", box=(0.2, 0, 0.2, 0.8, 0.5, 0.8))
    shaped("level4", "filingcabinet", "block/filingcabinet", material="Metal", sounds=METAL, comment="Filing cabinet", box=(0.125, 0, 0.125, 0.875, 1, 0.875))
    shaped("level4", "vendingmachine", "block/vendingmachine", material="Metal", sounds=METAL, comment="Vending machine that still sells Almond Water: use it",
           box=(0.03, 0, 0.125, 0.97, 1, 0.94), **{"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser", "lightHsv": [10, 2, 6]})
    shaped("level4", "watercooler", "block/watercooler", material="Metal", sounds=METAL, comment="Water cooler full of Almond Water: use it",
           box=(0.25, 0, 0.25, 0.75, 1, 0.75), **{"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser"})
    shaped("level4", "conferencetable", "block/conferencetable", oriented=False, comment="Conference table", box=(0, 0, 0, 1, 0.78, 1))


def level5():
    cube("level5", "hotelwall", "block/level5/hotelwall-{type}", material="Wood", sounds=WOOD, states=["wainscot", "panel", "frieze"],
         comment="Hotel walls: mahogany wainscot, a red damask panel in a gilt frame, a cream frieze")
    fixture = {
        "code": "hotelfixture",
        "variantgroups": [{"code": "type", "states": ["sconce", "portrait", "beverly"]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {"*": {"base": "block/hotelfixture-{type}"}},
        "textures": {"all": {"base": "block/level5/hotelwall-panel"}},
        "lightHsvByType": {"*-sconce": [6, 5, 11]},
        "resistance": 2, "lightAbsorption": 99, "lightAbsorptionByType": {"*-sconce": 0}, "sounds": WOOD,
        "particlePropertiesByType": {"*-sconce": _sconce_flames()},
    }
    write("level5", "hotelfixture", fixture, "Hotel wall panels with a candle sconce, a portrait, or The Beverly Room's placard")
    cube("level5", "hotelcarpet", "block/level5/hotelcarpet-{type}", material="Cloth", sounds=CLOTH, states=["damask", "maroon", "lobby"],
         comment="Red and gold damask, near-black ballroom maroon, and tan lobby carpet")
    cube("level5", "hotelwood", "block/level5/hotelwood", material="Wood", sounds=WOOD, comment="Dark walnut floorboards")
    cube("level5", "hotelceiling", "block/level5/hotelceiling-{type}", material="Wood", sounds=WOOD, states=["cream", "beams"],
         comment="Cream corridor ceiling and the painted beams of the grand rooms")
    cube("level5", "marblecolumn", "block/level5/marble", comment="Red faux-marble column")
    cube("level5", "plasterwall", "block/level5/plaster", comment="Stained plaster of the boiler halls")
    cube("level5", "staffsign", "block/level5/staffsign", material="Wood", sounds=WOOD, comment="STAFF ONLY sign above the doors to the boiler halls")
    door = {
        "code": "hoteldoor",
        "variantgroups": [{"code": "part", "states": ["lower"] + [f"upper{i}" for i in range(8)]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood", "drawtype": "cube",
        "textures": {"all": {"base": "block/level5/hoteldoor-{part}"}},
        "behaviors": threshold("door"),
        "resistance": 2, "drops": [], "lightAbsorption": 99, "sounds": WOOD,
    }
    write("level5", "hoteldoor", door, "Locked guest-room doors with brass number plaques. A few open after all, onto somewhere else")
    cube("level5", "cagedoor", "block/level5/cagedoor-{type}", material="Metal", sounds=METAL, states=["lower", "upper"],
         comment="Copper-cage elevator gate. Use it to ride", drops=[], behaviors=threshold("elevator"))
    dome = {
        "code": "domelight", "variantgroups": [{"code": "state", "states": ["on", "off", "flicker"]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": {"*-off": {"base": "block/domelight-off"}, "*": {"base": "block/domelight-lit"}},
        "lightHsvByType": {"*-on": [6, 4, 14]},
        "entityClassByType": {"*-flicker": "BackroomsFlicker"},
        "attributesByType": {"*-flicker": {"offBlock": "backrooms:domelight-off"}},
        "dropsByType": {"*-off": DEAD_LIGHT_DROPS},
        "lightAbsorption": 0, "resistance": 1, "sounds": GLASS,
    }
    write("level5", "domelight", dome, "Flush dome lights along the corridor ceilings")
    shaped("level5", "chandelier", "block/chandelier", material="Metal", sounds=GLASS, oriented=False,
           comment="Great chandelier in the grand rooms", box=(0.25, 0, 0.25, 0.75, 1, 0.75), lightHsv=[6, 4, 18],
           particleProperties=_chandelier_flames())
    shaped("level5", "bed-head", "block/bed-head", material="Cloth", sounds=CLOTH, comment="Guest bed, head end", box=(0, 0, 0, 1, 0.6, 1))
    shaped("level5", "bed-foot", "block/bed-foot", material="Cloth", sounds=CLOTH, comment="Guest bed, foot end", box=(0, 0, 0, 1, 0.6, 1))
    shaped("level5", "nightstand", "block/nightstand", comment="Nightstand with a lamp", box=(0.125, 0, 0.25, 0.875, 0.65, 0.875), lightHsv=[6, 5, 9])
    shaped("level5", "wardrobe", "block/wardrobe", comment="Mahogany wardrobe", box=(0.06, 0, 0.3, 0.94, 1, 1))
    shaped("level5", "wingchair", "block/wingchair", material="Cloth", sounds=CLOTH, comment="Wingback armchair", box=(0.1, 0, 0.1, 0.9, 0.6, 0.95))
    shaped("level5", "sofa", "block/sofa", material="Cloth", sounds=CLOTH, comment="Velvet sofa", box=(0, 0, 0.2, 1, 0.55, 0.95))
    shaped("level5", "pottedpalm", "block/pottedpalm", material="Plant", sounds=CLOTH, oriented=False, comment="Potted palm", box=(0.25, 0, 0.25, 0.75, 1, 0.75))
    shaped("level5", "mahjongtable", "block/mahjongtable", oriented=False, comment="The Beverly Room's Art Deco table, with an unfinished game of Mahjong", box=(0, 0, 0, 1, 0.85, 1))
    shaped("level5", "turntable", "block/turntable", oriented=False, comment="A turntable playing jazz that drifts nearer and farther",
           box=(0.125, 0, 0.125, 0.875, 0.65, 0.875), sounds_override=None)
    shaped("level5", "boiler", "block/boiler", material="Metal", sounds=METAL, comment="Boiler", box=(0.06, 0, 0.125, 0.94, 1, 0.94),
           particlePropertiesByType=fire_fx.by_side(_boiler_fx), behaviors=[fire_fx.heat(4)])
    shaped("level5", "furnace", "block/furnace", material="Metal", sounds=METAL, comment="Furnace with a glowing door",
           box=(0.06, 0, 0.125, 0.94, 1, 0.94), lightHsv=[4, 7, 12],
           particlePropertiesByType=fire_fx.by_side(_furnace_fx), behaviors=[fire_fx.heat(8)])


def fix_ambients():
    """Adds ambient sounds to blocks that need them (done after writing, to keep the helpers simple)."""
    for folder, code, ambient, count in (("level3", "transformer", "backrooms:ambient/transformer", 4),
                                         ("level4", "officewindow", "backrooms:ambient/rain", 12),
                                         ("level5", "turntable", "backrooms:ambient/jazz", 1)):
        path = os.path.join(OUT, folder, code + ".json")
        with open(path) as f:
            lines = f.read()
        comment, _, body = lines.partition("\n") if lines.startswith("//") else ("", "", lines)
        block = json.loads(body)
        block.pop("sounds_override", None)
        block["sounds"] = dict(block["sounds"], ambient=ambient, ambientBlockCount=count)
        with open(path, "w", encoding="utf-8") as f:
            f.write((comment + "\n" if comment else "") + json.dumps(block, indent="\t") + "\n")


if __name__ == "__main__":
    level3()
    level4()
    level5()
    fix_ambients()
    import salvage
    salvage.apply()
    print("block types written")
