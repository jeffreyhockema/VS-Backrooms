"""Level 3999, the Neon Paradise: items, the placeable neon lamp and the arcade salvage recipes (3999-plan.md 6.6 and
the user direction of 2026-10-09: the level's point is its theme-based resources). Called from gen_3999.py.

- Tickets: the arcade's currency, won from the machines, spent at prize counters and food stalls.
- Tray meals from the food stalls; snacks and Paradise Pop from the vending machines (one Almond Water each).
- Glow bracelets (a dim held light) and neon lamps (a placeable coloured light): prizes.
- Arcade salvage, from the dead machines of 3999.1 and the odd bin: neon tubing, circuit boards, coin mechanisms,
  plastic. Circuit boards melt down to copper and coin mechanisms to brass in a crucible; plastic burns; tubing, a
  board and plastic make a neon lamp in the colour of the glow bracelet you put in.
"""
import os

from detail_kit import ground_storable
from gen_3999_kit import (COLOURS, GLASS, LANG, SIDES, bx, hang, hsv, item, recipe, variants_block)

# What melts down in a crucible: the metallurgy storage flag (with general, 5, as vanilla's nuggets and bits) and a
# size the crucible takes (it holds nothing over 0.125 x 0.25 x 0.125; an item's size is half a block unless given)
CRUCIBLE = {"storageFlags": 5, "size": {"width": 0.125, "height": 0.0625, "length": 0.125}}

SPRITE = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}
INV = {"general": ["*"], "items": ["*"], "backrooms": ["*"]}


def sprite_item(code, english, desc, texture, extra=None, stack=64, comment=None, by_type=None, ground="Quadrants"):
    """A flat item; `ground` is its layout set down on the floor."""
    d = {"maxstacksize": stack, "creativeinventory": INV, "materialDensity": 400}
    if by_type:
        d["variantgroups"] = by_type[0]
        d["textureByType"] = by_type[1]
    else:
        d["texture"] = {"base": f"item/3999/{texture}"}
    d.update(SPRITE)
    if extra:
        d.update(extra)
    item(code, ground_storable(d, ground), comment or english)
    if english:
        LANG[f"item-{code}" + ("-*" if by_type else "")] = english
    if desc:
        LANG[f"itemdesc-{code}" + ("-*" if by_type else "")] = desc


def items():
    sprite_item("l3999-ticket", "Arcade Ticket",
                "Won from the machines of Level 3999. Each machine pays you once a day. Trade them at a prize counter for prizes, or at a "
                "food stall for a meal.", "ticket", stack=128, ground="Messy12",
                extra={"combustibleProps": {"burnTemperature": 300, "burnDuration": 2}, "materialDensity": 200},
                comment="Level 3999's currency: a red ticket, ADMIT ONE. Stack 128")

    meals = {"burger": ("Tray of Burger", 420, "Protein"), "pizza": ("Tray of Pizza", 420, "Grain"), "noodles": ("Tray of Noodles", 420, "Grain"),
             "taco": ("Tray of Tacos", 420, "Protein"), "icecream": ("Tray of Ice Cream", 240, "Dairy"), "pretzel": ("Tray of Pretzels", 420, "Grain")}
    item("l3999-traymeal", ground_storable(dict({
        "variantgroups": [{"code": "meal", "states": list(meals)}], "maxstacksize": 8, "creativeinventory": INV, "materialDensity": 600,
        "textureByType": {f"l3999-traymeal-{m}": {"base": f"item/3999/traymeal-{m}"} for m in meals},
        "nutritionPropsByType": {f"l3999-traymeal-{m}": {"satiety": sat, "foodcategory": cat, "health": 2} for m, (_, sat, cat) in meals.items()},
        "attributes": {"handbook": {"groupBy": ["l3999-traymeal-*"]}},
    }, **SPRITE)), "A tray meal from a food stall in the Neon Paradise (6 tickets): satiety 420 (ice cream 240) and +2 health")
    for m, (n, _, _) in meals.items():
        LANG[f"item-l3999-traymeal-{m}"] = n
    LANG["itemdesc-l3999-traymeal-*"] = "From a stall in the Neon Paradise. It tastes almost right: a little funky, a little artificial."

    item("l3999-glowband", ground_storable(dict({
        "variantgroups": [{"code": "colour", "states": ["magenta", "cyan", "lilac"]}], "maxstacksize": 16, "creativeinventory": INV,
        "materialDensity": 300, "textureByType": {f"l3999-glowband-{c}": {"base": f"item/3999/glowband-{c}"} for c in ("magenta", "cyan", "lilac")},
        "lightHsvByType": {f"l3999-glowband-{c}": hsv(c, 6) for c in ("magenta", "cyan", "lilac")},
        "attributes": {"handbook": {"groupBy": ["l3999-glowband-*"]}},
    }, **SPRITE)), "A glow bracelet (a prize): a dim coloured light while held, dimmer than a candle")
    LANG["item-l3999-glowband-*"] = "Glow Bracelet"
    LANG["itemdesc-l3999-glowband-*"] = "A prize from the Neon Paradise. It glows, a little, for good. Not enough to keep anything away."

    # Snacks and drinks from the vending machines
    sprite_item("l3999-popcorn", "Bucket of Popcorn", "Still warm, from a machine that takes Almond Water. Salty and buttery, more or less.",
                "popcorn", stack=8, extra={"nutritionProps": {"satiety": 200, "foodcategory": "Grain"}})
    sprite_item("l3999-cottoncandy", "Cotton Candy", "Pink and blue spun sugar on a paper cone. Gone in three bites.", "cottoncandy", stack=8,
                extra={"nutritionProps": {"satiety": 80, "foodcategory": "NoNutrition"}})
    flavours = {"cherry": "Cherry", "lime": "Lime", "grape": "Grape"}
    item("l3999-soda", ground_storable(dict({
        "variantgroups": [{"code": "flavour", "states": list(flavours)}], "maxstacksize": 8, "creativeinventory": INV, "materialDensity": 600,
        "textureByType": {f"l3999-soda-{f}": {"base": f"item/3999/soda-{f}"} for f in flavours},
        "nutritionPropsByType": {f"l3999-soda-{f}": {"satiety": 100, "foodcategory": "Fruit" if f == "cherry" else "NoNutrition"} for f in flavours},
        "attributes": {"handbook": {"groupBy": ["l3999-soda-*"]}},
    }, **SPRITE)), "Paradise Pop: a can of neon soda from the vending machines (cherry, lime, grape)")
    for f, n in flavours.items():
        LANG[f"item-l3999-soda-{f}"] = f"Paradise Pop ({n})"
    LANG["itemdesc-l3999-soda-*"] = "A can of soda in a flavour that only exists here. It fizzes like a memory of summer."

    # Arcade salvage
    sprite_item("l3999-neontubing", "Neon Tubing", "Glass tubing salvaged from dead neon, still holding a little gas. With a circuit board and "
                "some plastic it makes a neon lamp again; the glow bracelet you add decides its colour.", "neontubing", stack=32)
    sprite_item("l3999-circuitboard", "Circuit Board", "From the guts of an arcade machine. Its traces are copper: melt boards down in a "
                "crucible (ten to an ingot).", "circuitboard", stack=32, ground="Messy12",
                extra=dict(CRUCIBLE, combustibleProps={"meltingPoint": 1084, "meltingDuration": 30, "smeltedRatio": 10,
                                                       "smeltedStack": {"type": "item", "code": "game:ingot-copper"}}))
    sprite_item("l3999-coinmech", "Coin Mechanism", "The coin door's works, solid brass. Melt it down in a crucible: five make a brass ingot. "
                "Nobody in the Backrooms has coins anyway.", "coinmech", stack=16, ground="Messy12",
                extra=dict(CRUCIBLE, combustibleProps={"meltingPoint": 920, "meltingDuration": 30, "smeltedRatio": 5,
                                                       "smeltedStack": {"type": "item", "code": "game:ingot-brass"}}))
    sprite_item("l3999-plastic", "Plastic Scrap", "Bright moulded plastic from cabinets, bins and light diffusers. It burns hot and foul.",
                "plastic", stack=64, ground="Messy12", extra={"combustibleProps": {"burnTemperature": 700, "burnDuration": 20}})

    # The neon lamp: a placeable coloured light, given as a prize and made from salvage
    def lamp(v):
        c = v["colour"]
        return hang([bx("Rail", (1, 6, -1), (15, 10, 0), "darksteel"),
                     bx("BracketL", (2.5, 7, -3), (3.5, 9, -1), "darksteel"), bx("BracketR", (12.5, 7, -3), (13.5, 9, -1), "darksteel"),
                     bx("Tube", (1.5, 7, -4), (14.5, 9, -2), f"neon-{c}", glow=255),
                     bx("CapL", (0.8, 6.6, -4.4), (1.8, 9.4, -1.6), f"neondim-{c}"), bx("CapR", (14.2, 6.6, -4.4), (15.2, 9.4, -1.6), f"neondim-{c}"),
                     bx("Cord", (7.6, 0, -0.8), (8.4, 6, -0.2), "rubber")])

    variants_block("l3999-neonlamp", "Neon Lamp", [("colour", COLOURS), ("facing", SIDES)], lamp, rot="facing",
                   box=(0.05, 0.35, 0.72, 0.95, 0.62, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"behaviors": [{"name": "HorizontalOrientable", "properties": {"dropBlockFace": "north"}}],
                         "lightHsvByType": {f"*-{c}-*": hsv(c, 9) for c in COLOURS}, "resistance": 0.5,
                         "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
                         "drops": [{"type": "block", "code": "l3999-neonlamp-{colour}-north", "quantity": {"avg": 1, "var": 0}}]},
                   comment="Level 3999: a neon lamp, a short coloured tube on two brackets for a wall (light 9, the colour of its glass). A "
                           "prize, or made from arcade salvage; place it against a wall, it faces you",
                   names={f"l3999-neonlamp-{c}-*": f"Neon Lamp ({c.title()})" for c in COLOURS})

    recipe("l3999-neonlamp", {
        "ingredientPattern": "TGT,PCP", "width": 3, "height": 2,
        "ingredients": {"T": {"type": "item", "code": "l3999-neontubing", "quantity": 1},
                        "G": {"type": "item", "code": "l3999-glowband-*", "name": "colour", "quantity": 1},
                        "P": {"type": "item", "code": "l3999-plastic", "quantity": 1},
                        "C": {"type": "item", "code": "l3999-circuitboard", "quantity": 1}},
        "output": {"type": "block", "code": "l3999-neonlamp-{colour}-north", "quantity": 2},
    }, "Two neon lamps from salvaged tubing, a circuit board and plastic; the glow bracelet's gas decides their colour")
    recipe("l3999-glowband", {
        "ingredientPattern": "PT", "width": 2, "height": 1,
        "ingredients": {"P": {"type": "item", "code": "l3999-plastic", "quantity": 1},
                        "T": {"type": "item", "code": "l3999-neontubing", "quantity": 1}},
        "output": {"type": "item", "code": "l3999-glowband-lilac", "quantity": 2},
    }, "Two lilac glow bracelets: a scrap of plastic and a length of tubing, bent round and sealed")


def trueend_terminal():
    """The End's old computer while it runs TRUEEND.EXE (ThresholdNetwork.L3999TrueEnd): The End's own terminal model,
    its screen swapped for one of ours (neon on violet). EndSystem puts it in place of the computer turned on, and the
    computer dies after. Nothing else in The End's assets changes."""
    import random
    from PIL import Image
    from gen_3999_kit import ASSETS, block, centred, cuboid
    img = Image.new("RGBA", (32, 24), (20, 6, 30, 255))
    px = img.load()
    rng = random.Random(3999)
    for y in range(24):
        for x in range(32):
            r, g, b, a = px[x, y]
            k = (0.8 if y % 2 else 1.0) * rng.uniform(0.9, 1.1)
            px[x, y] = (min(255, int(r * k + y)), int(g * k), min(255, int(b * k + y * 2)), 255)
    centred(img, "TRUE", 3, (255, 80, 220, 255))
    centred(img, "END", 10, (255, 80, 220, 255))
    centred(img, ".EXE", 17, (90, 230, 255, 255))
    path = os.path.join(ASSETS, "textures", "block", "3999", "screen-trueend.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    rot = {"north": 0, "east": 270, "south": 180, "west": 90}
    block("l3999-trueendterminal", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "backrooms:block/end/end-terminal-party", "rotateY": a} for s, a in rot.items()},
        "textures": {"screen-party": {"base": "backrooms:block/3999/screen-trueend"}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "lightHsv": [50, 5, 6],
        "resistance": 20, "drops": [],
        "attributes": {"l3999structure": True},
        "collisionboxByType": {f"*-{s}": cuboid((0.12, 0, 0.25, 0.88, 0.75, 0.97), a) for s, a in rot.items()},
        "selectionboxByType": {f"*-{s}": cuboid((0.12, 0, 0.0, 0.88, 0.75, 0.97), a) for s, a in rot.items()},
    }, "The End's old computer running TRUEEND.EXE (Level 3999's way in, one-way): The End's terminal model with a neon "
       "screen. Put there by EndSystem for the three seconds before the computer takes its user and dies")
    LANG["block-l3999-trueendterminal-*"] = "Old Computer"
