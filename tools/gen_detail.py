"""Generates the detail added to Levels 1, 3, 4 and 5: props, wall decorations, signs, doors, elevators and floor
variants, with their textures, 3D shapes, block types and English names.

Run from the repo root:  python tools/gen_detail.py
Everything is written to block/detail/ folders (textures, shapes, blocktypes); names are merged into lang/en.json.
"""
import json
import os

import detail_textures
from detail_kit import (ASSETS, CEILING_DROPS, CLOTH, DEAD_LIGHT_DROPS, GLASS, LANG, MANIFEST, METAL, ROTATE, SIDES,
                        STONE, WOOD, Decor, block, bx, cube, cuboid, cyl, name, prop, shape, shift, turn, wall_family)


def plate(nm, frm, to, front, side, glow=0):
    """A flat panel with a picture on its front (north) face and plain sides."""
    return [bx(nm, frm, to, front, glow=glow, faces=("north",), full=True),
            bx(nm + "Sides", frm, to, side, faces=("east", "west", "up", "down"))]


def carton(nm, frm, to):
    return [bx(nm, frm, to, "cardboard", faces=("north", "east", "south", "west", "down")),
            bx(nm + "Top", frm, to, "cardboardtop", faces=("up",))]


def mirror_x(els):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [16 - x2, y1, z1], [16 - x1, y2, z2]
        f = e["faces"]
        if "east" in f or "west" in f:
            east, west = f.pop("east", None), f.pop("west", None)
            if west:
                f["east"] = west
            if east:
                f["west"] = east
        out.append(e)
    return out


TURNED = {"asphalt", "asphalt-leaves", "asphalt-wet", "housefloor-carpet", "housefloor-garage", "housefloor-driveway", "l6floor",
          "l6floor-wet", "dirtroad", "stubble", "jetty", "pool-coping", "snackfloor-terrazzo", "islandrock", "l3stone"}


def cube_block(code, english, kinds, textures, material="Stone", sounds=STONE, comment=None, **extra):
    """A plain cube block with one texture per kind: `textures` maps a kind to a texture key or {base, rotation}.
    Textures without a direction (in TURNED) are turned at random from block to block, so they do not tile."""
    data = {"variantgroups": [{"code": "kind", "states": list(kinds)}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": material, "drawtype": "cube",
            "texturesByType": {}, "lightAbsorption": 99, "resistance": 4, "sounds": sounds}
    for k in kinds:
        t = textures[k]
        tex = {"base": f"block/detail/{t}"} if isinstance(t, str) else {"base": f"block/detail/{t[0]}", "rotation": t[1]}
        if isinstance(t, str) and t in TURNED:
            tex["alternates"] = [{"base": f"block/detail/{t}", "rotation": r} for r in (90, 180, 270)]
        data["texturesByType"][f"*-{k}"] = {"all": tex}
    data.update(extra)
    block(code, data, comment or (english if isinstance(english, str) else None))
    for k in kinds:
        name(f"{code}-{k}", english if isinstance(english, str) else english[k])


# ======================= Signs and doors =======================

def exit_signs():
    face = [bx("Housing", (2, 3, -2.5), (14, 11, 0), "exithousing", faces=("north", "east", "west", "up", "down")),
            bx("Face", (2.4, 3.4, -2.6), (13.6, 10.6, -2.5), "exitface", glow=200, faces=("north",), uv=[0, 4, 16, 12])]
    by_type = {}
    for material, wall in (("concrete", "concretewall"), ("whiteblock", "whiteblock"), ("drywall", "drywall")):
        path = shape(f"exitlintel-{material}", [cube(wall)] + face + [turn(e, 2) for e in face])
        by_type[f"*-{material}-we"] = {"base": path, "rotateY": 0}
        by_type[f"*-{material}-ns"] = {"base": path, "rotateY": 90}
    block("exitlintel", {
        "variantgroups": [{"code": "material", "states": ["concrete", "whiteblock", "drywall"]}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
        "lightHsv": [0, 6, 6], "lightAbsorption": 0, "resistance": 4, "sounds": STONE,
    }, "Lintel over a doorway with a lit EXIT sign on both faces")
    name("exitlintel-*", "EXIT Sign")

    hanging = [bx("RodL", (3.6, 8, 7.6), (4.4, 16, 8.4), "metal"), bx("RodR", (11.6, 8, 7.6), (12.4, 16, 8.4), "metal"),
               bx("Housing", (1.5, 1, 6.6), (14.5, 8, 9.4), "exithousing"),
               bx("FaceN", (1.9, 1.4, 6.5), (14.1, 7.6, 6.6), "exitface", glow=200, faces=("north",), uv=[0, 4, 16, 12]),
               bx("FaceS", (1.9, 1.4, 9.4), (14.1, 7.6, 9.5), "exitface", glow=200, faces=("south",), uv=[0, 4, 16, 12])]
    path = shape("exithanging", hanging)
    block("exithanging", {
        "variantgroups": [{"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": {"*-we": {"base": path, "rotateY": 0}, "*-ns": {"base": path, "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": None, "selectionbox": {"x1": 0.1, "y1": 0.05, "z1": 0.4, "x2": 0.9, "y2": 1, "z2": 0.6},
        "lightHsv": [0, 6, 5], "lightAbsorption": 0, "resistance": 1, "sounds": GLASS,
    }, "Double-sided EXIT sign hanging from the ceiling")
    name("exithanging-*", "EXIT Sign")


def doors():
    for code, english, tex in (("metaldoor", "Steel Door", "metaldoor"), ("officedoor", "Office Door", "officedoor")):
        block(code, {
            "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": "Metal" if code == "metaldoor" else "Wood", "drawtype": "cube",
            "textures": {"all": {"base": f"block/detail/{tex}-{{part}}"}},
            "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL if code == "metaldoor" else WOOD,
        }, f"{english}, locked")
        name(f"{code}-*", english)

    # Black fire doors propped wide open: a steel jamb in the doorway and the leaf folded back flat against the wall
    left = [bx("Jamb", (14.6, 0, -0.4), (16, 31, 16.4), "steeldark"),
            bx("Head", (0, 30, -0.4), (16, 32, 16.4), "steeldark"),
            bx("Leaf", (16.3, 0.2, -1.7), (31.8, 30, -0.3), "firedoor"),
            bx("Bar", (17.5, 13.5, -2.7), (30.5, 14.8, -1.7), "steel"),
            bx("BarEnd", (28.6, 12.8, -2.9), (30.8, 15.4, -1.7), "steel"),
            bx("Hinge1", (15.8, 4, -1.9), (16.8, 7, -0.2), "steel"),
            bx("Hinge2", (15.8, 23, -1.9), (16.8, 26, -0.2), "steel")]
    by_type = {}
    for half, els in (("l", left), ("r", mirror_x(left))):
        path = shape(f"firedoor-{half}", els)
        for s in SIDES:
            by_type[f"*-{half}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("firedoor", {
        "variantgroups": [{"code": "half", "states": ["l", "r"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-l-north"], "decorative": ["*-l-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionboxByType": {f"*-{h}-{s}": cuboid((0.9, 0, 0, 1, 1.9, 1) if h == "l" else (0, 0, 0, 0.1, 1.9, 1), s) for h in "lr" for s in SIDES},
        "lightAbsorption": 0, "resistance": 4, "drops": [], "sounds": METAL,
    }, "Black steel fire doors propped open: the way into Level 1's maintenance halls")
    name("firedoor-*", "Fire Door")

    # Elevators are two blocks wide: each half carries its own leaf, and the variant says which half it is
    def lift(code, english, walls, parts_fn, comment, light_part=None):
        by_type, states_wall = {}, list(walls)
        parts = ["lower", "upper", parts_fn.__name__]
        for wall_name, wall_tex in walls.items():
            for part in parts:
                for half in ("l", "r"):
                    els = [cube(wall_tex[part])] + parts_fn(part, half)
                    path = shape(f"{code}-{wall_name}-{part}-{half}", els)
                    for s in SIDES:
                        by_type[f"*-{wall_name}-{part}-{half}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
        block(code, {
            "variantgroups": [{"code": "wall", "states": states_wall}, {"code": "part", "states": parts},
                              {"code": "half", "states": ["l", "r"]}, {"code": "side", "states": SIDES}],
            "creativeinventory": {"general": ["*-lower-l-north"], "decorative": ["*-lower-l-north"]},
            "blockmaterial": "Metal", "drawtype": "json", "shapeByType": by_type,
            "behaviorsByType": {"*-lower-*": [{"name": "BackroomsThreshold", "properties": {"kind": "elevator"}}],
                                "*-upper-*": [{"name": "BackroomsThreshold", "properties": {"kind": "elevator"}}]},
            "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL,
        }, comment)
        name(f"{code}-*", english)

    def header(part, half):
        outer = (14.5, 16) if half == "l" else (0, 1.5)
        if part == "header":
            return plate("Indicator", (2, 3, -1), (14, 13, 0), f"liftheader-{half}", "liftframe", glow=60)
        els = [bx("Leaf", (0, 0, -0.5), (16, 16, 0), f"liftdoor-{part}-{half}", faces=("north",), full=True),
               bx("Jamb", (outer[0], 0, -1.2), (outer[1], 16, 0), "liftframe")]
        if part == "upper":
            els.append(bx("Head", (0, 14.5, -1.2), (16, 16, 0), "liftframe"))
        return els

    lift("liftdoor", "Elevator", {
        "drywall": {"lower": "drywall-base", "upper": "drywall", "header": "drywall"},
        "hotel": {"lower": "wainscot", "upper": "hotelpanel", "header": "frieze"},
    }, header, "Modern elevator doors, two blocks wide. Use them: each elevator leads to one fixed place")

    def dial(part, half):
        outer = (14, 16) if half == "l" else (0, 2)
        if part == "dial":
            return [bx("Dial", (0, 2, -0.8), (16, 15, 0), f"cagedial-{half}", glow=20, faces=("north",), full=True),
                    bx("Rim", (0, 1.5, -1.2), (16, 2.5, 0), "brass")]
        els = [bx("Gate", (0, 0, -1.4), (16, 16, -0.9), f"cagegate-{half}", faces=("north", "south"), full=True),
               bx("Column", (outer[0], 0, -2), (outer[1], 16, 0), "brass")]
        els.append(bx("Rail", (0, 0 if part == "lower" else 14.5, -1.8), (16, 1.5 if part == "lower" else 16, -0.5), "brass"))
        if part == "lower":
            els.append(bx("Handle", (6 if half == "r" else 9, 7, -2.6), (7 if half == "r" else 10, 11, -1.4), "brass"))
        return els

    lift("cagelift", "Cage Elevator", {
        "hotel": {"lower": "wainscot", "upper": "hotelpanel", "dial": "frieze"},
        "plaster": {"lower": "plaster", "upper": "plaster", "dial": "plaster"},
    }, dial, "Antique copper-cage elevator, two blocks wide, with a floor dial above. Use it to ride")


# ======================= Level 1 =======================

def level1():
    cube_block("whiteblock", "Painted Block Wall", ["upper", "base", "lintel"],
               {"upper": "whiteblock", "base": "whiteblock-base", "lintel": "whiteblock-lintel"},
               comment="White-painted block walls of Level 1's maintenance halls, with a grey dado and a yellow stripe")
    cube_block("l1hallfloor", "Painted Concrete Floor", ["plain"], {"plain": "l1hallfloor"})
    cube_block("pillarbase", "Concrete Pillar", ["plain"], {"plain": "pillarbase"}, comment="Foot of a parking column, striped for drivers")
    cube_block("parkfloor", {"arrown": "Concrete Floor", "arrowe": "Concrete Floor", "arrows": "Concrete Floor", "arroww": "Concrete Floor",
                             "oil": "Oil-Stained Concrete", "drain": "Floor Drain"},
               ["arrown", "arrowe", "arrows", "arroww", "oil", "drain"],
               {"arrown": ("parkarrow", 0), "arrowe": ("parkarrow", 90), "arrows": ("parkarrow", 180), "arroww": ("parkarrow", 270),
                "oil": "parkoil", "drain": "parkdrain"}, comment="Car park floor markings: lane arrows, oil stains and drains")

    walls_white = {1: "whiteblock-base", 2: "whiteblock"}
    pipes = [bx("PipeA", (0, 9, -3), (16, 13, 0), "rust", faces=("north", "up", "down")),
             bx("PipeB", (0, 3, -2.5), (16, 6.5, 0), "lagging", faces=("north", "up", "down")),
             bx("Bracket", (7, 2, -3.5), (9, 14, 0), "metal", faces=("north", "east", "west", "up", "down"))]
    riser = [bx("Riser", (6, 0, -4), (10, 16, 0), "redpipe", faces=("north", "east", "west"))]
    decors = [
        Decor("powerbox", "Power Box", {
            2: plate("Box", (3, 2, -3), (11, 12, 0), "powerbox", "steeldark") +
               [bx("Conduit", (6.25, 12, -1.75), (7.75, 16, -0.25), "metal"), bx("Small", (12, 5, -2), (15, 9, 0), "steeldark")],
            3: [bx("Conduit", (6.25, 0, -1.75), (7.75, 16, -0.25), "metal")]}),
        Decor("breaker", "Breaker Panel", {2: plate("Panel", (2, 0, -2), (14, 15, 0), "breaker", "steeldark")}),
        Decor("outlet", "Wall Outlet", {1: plate("Outlet", (6, 4, -0.4), (10, 9, 0), "outlet", "white")}),
        Decor("extinguisher", "Fire Extinguisher", {2: cyl("Body", 8, -2.5, 2, 0, 10, "extinguisher") + [
            bx("Head", (7, 10, -3.5), (9, 12, -1.5), "rubber"), bx("Hose", (9.8, 4, -2.2), (10.6, 10.5, -1.4), "rubber"),
            bx("Bracket", (6.5, 3, -0.6), (9.5, 4, 0), "metaldark")] + plate("Sign", (5.5, 12.5, -0.2), (10.5, 16, 0), "extsign", "redmetal")}),
        Decor("alarm", "Fire Alarm", {2: plate("Pull", (6, 4, -1.5), (10, 9, 0), "firealarm", "redmetal")}),
        Decor("hosecab", "Fire Hose Cabinet", {2: plate("Cabinet", (2, 0, -3), (14, 14, 0), "hosecab", "redmetal")}),
        Decor("levelsign", "Level Marking", {2: [bx("Paint", (1, 1, -0.1), (15, 15, 0), "levelsign", faces=("north",), full=True)]}),
        Decor("stairsign", "Stairs Sign", {2: plate("Sign", (3, 5, -0.4), (13, 12, 0), "stairsign", "steel")}),
        Decor("note", "Note", {2: [bx("Paper", (6, 4, -0.15), (11, 10, 0), "note", faces=("north",), full=True)]}),
        Decor("graffiti", "Graffiti", {2: [bx("Paint", (0, 1, -0.1), (16, 15, 0), "graffiti", faces=("north",), full=True)]}),
        Decor("pipes", "Wall Pipes", {3: pipes}),
        Decor("standpipe", "Fire Standpipe", {
            1: riser + [bx("Outlet", (5.5, 6, -6), (10.5, 10, -4), "brass"), bx("Cap", (6.5, 7, -7), (9.5, 9, -6), "brass"),
                        bx("Wheel", (4, 11.5, -5.5), (12, 12.5, -4.5), "valve")],
            2: riser + [bx("Clamp", (5.5, 7, -4.5), (10.5, 8.5, 0), "metal")], 3: riser, 4: riser}),
    ]
    paintings = []
    for i in range(4):
        if i == 2:  # an old portrait in a real frame
            els = [bx("Canvas", (4, 3, -0.6), (12, 13, -0.4), "painting2", faces=("north",), full=True),
                   bx("FrameT", (3, 13, -1), (13, 14, 0), "wooddark"), bx("FrameB", (3, 2, -1), (13, 3, 0), "wooddark"),
                   bx("FrameL", (3, 3, -1), (4, 13, 0), "wooddark"), bx("FrameR", (12, 3, -1), (13, 13, 0), "wooddark")]
        else:  # paper hung on a string from a nail
            els = [bx("Paper", (3, 2, -0.3), (13, 13, -0.1), f"painting{i}", faces=("north",), full=True),
                   bx("StringL", (4.5, 13, -0.25), (7.8, 13.6, -0.15), "string"), bx("StringR", (8.2, 13, -0.25), (11.5, 13.6, -0.15), "string"),
                   bx("Nail", (7.6, 13.4, -0.9), (8.4, 14.2, 0), "metaldark")]
        paintings.append(Decor(f"painting{i}", "Painting", {2: els}))
    banners = [Decor(f"banner{i}", "Group Landmark", {2: [bx("Cloth", (2, -6, -0.6), (14, 14, -0.3), f"banner{i}", faces=("north", "south"), full=True),
                                                           bx("NailL", (2.5, 13, -1), (3.5, 14, 0), "metaldark"),
                                                           bx("NailR", (12.5, 13, -1), (13.5, 14, 0), "metaldark")]}) for i in range(4)]
    wall_family("l1deco", "Painted Block Wall", walls_white, decors + paintings + banners)
    wall_family("concretedeco", "Concrete Wall", {1: "concretewall"}, decors + banners)
    wall_family("pillardeco", "Concrete Pillar", {1: "pillar"},
                [Decor(f"banner{i}", "Group Landmark", {3: [bx("Cloth", (2, -8, -0.6), (14, 15, -0.3), f"banner{i}", faces=("north", "south"), full=True),
                                                            bx("Cord", (1, 15, -0.8), (15, 15.6, 0), "string")]}) for i in range(4)])

    # ---- props ----
    prop("cardboardboxes", "Cardboard Boxes", carton("A", (1, 0, 1), (9, 7, 9)) + carton("B", (9.5, 0, 2), (15, 5, 8.5)) +
         carton("C", (2, 0, 9.5), (10, 6, 15)) + carton("D", (2, 7, 2), (8, 12, 8)) + carton("E", (10.5, 0, 10), (15, 9, 14.5)) +
         carton("F", (11, 9, 10.5), (14.5, 13, 14)), box=(0.06, 0, 0.06, 0.94, 0.8, 0.94), oriented=False, sounds=CLOTH)
    prop("workbench", "Workbench", [
        bx("Top", (0, 13, 2), (16, 15, 14), "benchtop"),
        bx("LegFL", (0.5, 0, 2.5), (2, 13, 4), "wood"), bx("LegFR", (14, 0, 2.5), (15.5, 13, 4), "wood"),
        bx("LegBL", (0.5, 0, 12), (2, 13, 13.5), "wood"), bx("LegBR", (14, 0, 12), (15.5, 13, 13.5), "wood"),
        bx("Shelf", (1, 3, 3), (15, 4, 13), "plywood"),
        bx("Pegboard", (0, 15, 13.5), (16, 31, 15), "pegboard", faces=("north",), full=True),
        bx("PegboardSides", (0, 15, 13.5), (16, 31, 15), "wood", faces=("east", "west", "up", "south")),
        bx("Vise", (12.5, 15, 2.5), (15, 18, 6), "metaldark"), bx("Screw", (13.4, 16, 1), (14.1, 16.7, 2.5), "steel"),
        bx("Handle", (5, 15, 5), (10, 15.8, 6), "wood"), bx("HammerHead", (9.5, 15, 4.5), (11, 16.4, 6.5), "metaldark"),
        bx("Toolbox", (4, 4, 5), (10, 7, 10), "toolboxred")], box=(0, 0, 0.125, 1, 0.95, 0.94))
    prop("toolbox", "Toolbox", [
        bx("Box", (3, 0, 5), (13, 6, 11), "toolboxred"), bx("Lid", (3, 6, 5), (13, 6.5, 11), "redmetal"),
        bx("PostL", (6, 6.5, 7.7), (6.6, 8, 8.3), "metaldark"), bx("PostR", (9.4, 6.5, 7.7), (10, 8, 8.3), "metaldark"),
        bx("Grip", (6, 7.6, 7.6), (10, 8.3, 8.4), "rubber")], box=(0.18, 0, 0.3, 0.82, 0.5, 0.7), material="Metal", sounds=METAL)
    prop("plywood", "Plywood Sheets", [
        bx("Sheet1", (1, 0, 8.5), (15, 30, 9.5), "plywood", rot=(12, 0, 0), origin=(8, 0, 9)),
        bx("Sheet2", (1.5, 0, 7), (14.5, 28, 8), "plywood", rot=(14, 0, 0), origin=(8, 0, 7.5)),
        bx("Batten", (3, 0, 6), (4.5, 26, 7.5), "wood", rot=(16, 0, 0), origin=(3.75, 0, 6.75))],
         box=(0.06, 0, 0.4, 0.94, 1.5, 1))
    prop("tent", "Tent", [
        bx("PanelL", (1.4, 0, 0.5), (2.2, 14.6, 15.5), "tarp", rot=(0, 0, -26.6), origin=(1.8, 0, 8)),
        bx("PanelR", (13.8, 0, 0.5), (14.6, 14.6, 15.5), "tarp", rot=(0, 0, 26.6), origin=(14.2, 0, 8)),
        bx("Ridge", (7.4, 12.6, 0), (8.6, 13.6, 16), "wood"),
        bx("Back1", (4, 0, 15.3), (12, 7, 15.8), "tarp"), bx("Back2", (5.5, 7, 15.3), (10.5, 10, 15.8), "tarp"),
        bx("Back3", (7, 10, 15.3), (9, 12.5, 15.8), "tarp"),
        bx("Ground", (1, 0, 0), (15, 0.2, 16), "tarporange"), bx("Pole", (7.6, 0, 0.2), (8.4, 13, 1), "wood"),
        bx("Bedroll", (4.5, 0.2, 3), (11.5, 1.5, 14), "bedroll")], box=(0.06, 0, 0, 0.94, 0.85, 1), material="Cloth", sounds=CLOTH)
    prop("bedroll", "Bedroll", [
        bx("Roll", (3, 0, 1.5), (13, 1.4, 14.5), "bedroll"), bx("Pillow", (3.5, 1.4, 2), (12.5, 3, 4.5), "bedrollpillow"),
        bx("Fold", (3, 1.4, 8), (13, 2, 14.5), "bedroll")], box=(0.19, 0, 0.09, 0.81, 0.15, 0.91), material="Cloth", sounds=CLOTH)
    prop("camplantern", "Camping Lantern", [
        bx("Base", (6, 0, 6), (10, 1, 10), "metaldark"),
        bx("Glass", (6.5, 1, 6.5), (9.5, 5.5, 9.5), "lanternglass", glow=220),
        bx("Post1", (6.2, 1, 6.2), (6.8, 5.5, 6.8), "metaldark"), bx("Post2", (9.2, 1, 6.2), (9.8, 5.5, 6.8), "metaldark"),
        bx("Post3", (6.2, 1, 9.2), (6.8, 5.5, 9.8), "metaldark"), bx("Post4", (9.2, 1, 9.2), (9.8, 5.5, 9.8), "metaldark"),
        bx("Cap", (5.8, 5.5, 5.8), (10.2, 6.5, 10.2), "metaldark"), bx("Top", (7, 6.5, 7), (9, 7, 9), "metaldark"),
        bx("Handle", (7.6, 7, 7.8), (8.4, 9, 8.2), "metal")], box=(0.36, 0, 0.36, 0.64, 0.45, 0.64), oriented=False,
         material="Metal", sounds=METAL, light=[8, 5, 11])
    smoke = [{
        "hsvaColor": [{"avg": 0, "var": 0}, {"avg": 0, "var": 0}, {"avg": 70, "var": 20}, {"avg": 120, "var": 30}],
        "opacityEvolve": {"transform": "linear", "factor": -100}, "gravityEffect": {"avg": -0.01, "var": 0},
        "posOffset": [{"avg": 0, "var": 0.25}, {"avg": -0.15, "var": 0}, {"avg": 0, "var": 0.25}],
        "velocity": [{"avg": 0, "var": 0.05}, {"avg": 0.25, "var": 0.05}, {"avg": 0, "var": 0.05}],
        "quantity": {"avg": 0.15}, "size": {"avg": 0.35, "var": 0.1}, "sizeEvolve": {"transform": "linear", "factor": 1},
        "particleModel": "Quad", "lifeLength": {"avg": 3, "var": 0.5}, "selfPropelled": True}]
    prop("burnbarrel", "Burn Barrel", [
        bx("Drum", (3, 0, 3), (13, 13, 13), "burnbarrel", faces=("north", "east", "south", "west")),
        bx("Rim", (2.8, 12.5, 2.8), (13.2, 13.5, 13.2), "rust", faces=("north", "east", "south", "west", "down")),
        bx("Hoop", (2.8, 1, 2.8), (13.2, 2, 13.2), "rust", faces=("north", "east", "south", "west")),
        bx("Embers", (3.3, 12.6, 3.3), (12.7, 13, 12.7), "embers", glow=255, faces=("up",))],
         box=(0.18, 0, 0.18, 0.82, 0.84, 0.82), oriented=False, material="Metal", sounds=METAL, light=[3, 7, 12],
         extra={"particleProperties": smoke})
    hospital = {
        "head": [bx("Frame", (1, 6, 0), (15, 8, 16), "hospitalframe"),
                 bx("Mattress", (1.5, 8, 0.5), (14.5, 11, 16), "white"), bx("Pillow", (3, 11, 1.5), (13, 12.5, 5), "white"),
                 bx("Headboard", (1, 4, -0.5), (15, 18, 1), "hospitalframe"),
                 bx("RailL", (0.2, 11, 4), (1, 14, 14), "steel"), bx("RailR", (15, 11, 4), (15.8, 14, 14), "steel"),
                 bx("Leg1", (1.5, 0, 1), (2.5, 6, 2), "steel"), bx("Leg2", (13.5, 0, 1), (14.5, 6, 2), "steel"),
                 bx("Blanket", (1.3, 8.5, 6), (14.7, 11.3, 16), "hospitalsheet")],
        "foot": [bx("Frame", (1, 6, 0), (15, 8, 15), "hospitalframe"),
                 bx("Mattress", (1.5, 8, 0), (14.5, 11, 14.5), "white"),
                 bx("Blanket", (1.3, 8.5, 0), (14.7, 11.3, 14.7), "hospitalsheet"),
                 bx("Footboard", (1, 4, 14.5), (15, 15, 16), "hospitalframe"),
                 bx("Chart", (6, 10, 16), (10, 14.5, 16.4), "paper"),
                 bx("Leg1", (1.5, 0, 13.5), (2.5, 6, 14.5), "steel"), bx("Leg2", (13.5, 0, 13.5), (14.5, 6, 14.5), "steel")]}
    prop("hospitalbed", "Hospital Bed", hospital, box=(0, 0, 0, 1, 0.75, 1), material="Cloth", sounds=CLOTH)
    prop("foldingtable", "Folding Table", [
        bx("Top", (0, 11, 1), (16, 12, 15), "tabletop"), bx("Edge", (0, 10.5, 1), (16, 11, 15), "foldsteel"),
        bx("Leg1", (1, 0, 2), (2, 10.5, 3), "foldsteel"), bx("Leg2", (14, 0, 2), (15, 10.5, 3), "foldsteel"),
        bx("Leg3", (1, 0, 13), (2, 10.5, 14), "foldsteel"), bx("Leg4", (14, 0, 13), (15, 10.5, 14), "foldsteel")],
         box=(0, 0, 0.06, 1, 0.75, 0.94), oriented=False)
    prop("foldingchair", "Folding Chair", [
        bx("Seat", (4, 7, 3.5), (12, 8, 11.5), "foldsteel"),
        bx("LegFL", (4, 0, 4), (5, 7, 5), "foldsteel"), bx("LegFR", (11, 0, 4), (12, 7, 5), "foldsteel"),
        bx("LegBL", (4, 0, 11), (5, 15, 12), "foldsteel"), bx("LegBR", (11, 0, 11), (12, 15, 12), "foldsteel"),
        bx("Back", (4.5, 10, 11), (11.5, 15, 12), "foldsteel")], box=(0.25, 0, 0.22, 0.75, 0.95, 0.78), material="Metal", sounds=METAL)
    prop("medcabinet", "Medical Cabinet", [
        bx("Body", (2, 0, 6), (14, 24, 15), "medcab"),
        bx("Front", (2.2, 0.5, 5.8), (13.8, 23.5, 6), "medcabfront", faces=("north",), full=True)],
         box=(0.125, 0, 0.375, 0.875, 1.5, 0.94), material="Metal", sounds=METAL)
    prop("trafficcone", "Traffic Cone", [
        bx("Base", (2.5, 0, 2.5), (13.5, 1, 13.5), "orange"), bx("T1", (4.5, 1, 4.5), (11.5, 4, 11.5), "orange"),
        bx("T2", (5.2, 4, 5.2), (10.8, 6.5, 10.8), "conewhite"), bx("T3", (5.9, 6.5, 5.9), (10.1, 9, 10.1), "orange"),
        bx("T4", (6.6, 9, 6.6), (9.4, 11, 9.4), "conewhite"), bx("T5", (7.2, 11, 7.2), (8.8, 13, 8.8), "orange")],
         box=(0.15, 0, 0.15, 0.85, 0.8, 0.85), oriented=False, material="Cloth", sounds=CLOTH)
    prop("wetfloorsign", "Wet Floor Sign", [
        bx("PanelN", (3, 0, 6.6), (13, 15, 7.2), "wetfloor", faces=("north", "south"), full=True, rot=(12, 0, 0), origin=(8, 15, 6.9)),
        bx("PanelS", (3, 0, 8.8), (13, 15, 9.4), "wetfloor", faces=("north", "south"), full=True, rot=(-12, 0, 0), origin=(8, 15, 9.1)),
        bx("Cap", (3, 14.5, 6.6), (13, 15.5, 9.4), "orange")], box=(0.19, 0, 0.25, 0.81, 0.95, 0.75), material="Cloth", sounds=CLOTH)
    prop("pallet", "Pallet", [bx(f"Deck{i}", (0, 3, z), (16, 4, z + 3.5), "palletwood") for i, z in enumerate((0, 6.25, 12.5))] +
         [bx(f"Stringer{i}", (x, 0, 0), (x + 2, 3, 16), "palletwood") for i, x in enumerate((0.5, 7, 13.5))],
         box=(0, 0, 0, 1, 0.25, 1), oriented=False)
    prop("trashcan", "Trash Can", [
        bx("Body", (4, 0, 4), (12, 12, 12), "trashgrey"), bx("Rim", (3.5, 11.5, 3.5), (12.5, 12.5, 12.5), "trashgrey"),
        bx("Lid", (4.5, 12.5, 4.5), (11.5, 13.5, 11.5), "trashgrey")], box=(0.22, 0, 0.22, 0.78, 0.85, 0.78), oriented=False,
         material="Metal", sounds=METAL)
    prop("paystation", "Pay Station", [
        bx("Body", (3, 1, 5), (13, 22, 13), "paybody"),
        bx("Face", (3.5, 6, 4.6), (12.5, 20, 5), "payface", faces=("north",), full=True),
        bx("Roof", (2.5, 22, 4), (13.5, 23.5, 13.5), "metaldark"), bx("Base", (2.5, 0, 4.5), (13.5, 1, 13.5), "metaldark")],
         box=(0.15, 0, 0.25, 0.85, 1.45, 0.85), material="Metal", sounds=METAL)
    prop("speedbump", "Speed Bump", [bx("Hump", (0, 0, 5), (16, 1.5, 11), "speedbump"), bx("Crown", (0, 1.5, 6.5), (16, 2.2, 9.5), "speedbump")],
         box=(0, 0, 0.3, 1, 0.12, 0.7), material="Stone", sounds=STONE)
    prop("sprinkler", "Sprinkler Pipe", [
        bx("Pipe", (0, 13.8, 7.3), (16, 15.2, 8.7), "redpipe"), bx("Hanger", (7.6, 15.2, 7.6), (8.4, 16, 8.4), "metal"),
        bx("Head", (7.4, 12.6, 7.4), (8.6, 13.8, 8.6), "brass"), bx("Deflector", (7, 12.2, 7), (9, 12.6, 9), "brass")],
         collide=False, material="Metal", sounds=METAL, extra={"selectionbox": {"x1": 0, "y1": 0.75, "z1": 0.4, "x2": 1, "y2": 1, "z2": 0.6}})
    prop("clearancebar", "Clearance Bar", [
        bx("ChainL", (3.5, 5, 7.7), (4.1, 16, 8.3), "metaldark"), bx("ChainR", (11.9, 5, 7.7), (12.5, 16, 8.3), "metaldark"),
        bx("Bar", (0, 2.5, 7), (16, 5, 9), "hazard")], collide=False, material="Metal", sounds=METAL,
         extra={"selectionbox": {"x1": 0, "y1": 0.15, "z1": 0.4, "x2": 1, "y2": 0.35, "z2": 0.6}})
    prop("wiredroop", "Hanging Wires", [
        bx("W1", (5, 6, 7), (5.6, 16, 7.6), "cable"), bx("W2", (5, 6, 7), (9, 6.6, 7.6), "cable"),
        bx("W3", (8.4, 6, 7), (9, 16, 7.6), "cable"), bx("Loose", (11, 3, 10), (11.6, 16, 10.6), "cable"),
        bx("Tip", (11, 2.4, 10), (11.6, 3, 10.6), "copper")], oriented=False, collide=False, material="Metal", sounds=METAL,
         extra={"selectionbox": {"x1": 0.3, "y1": 0.2, "z1": 0.4, "x2": 0.75, "y2": 1, "z2": 0.7}})

    drips = {}
    for axis, rot in (("we", 0), ("ns", 90)):
        drips[f"*-{axis}"] = [{
            "hsvaColor": [{"avg": 140, "var": 10}, {"avg": 40, "var": 10}, {"avg": 200, "var": 20}, {"avg": 200, "var": 30}],
            "gravityEffect": {"avg": 1, "var": 0},
            "posOffset": [{"avg": 0 if axis == "we" else -0.2, "var": 0.3 if axis == "we" else 0},
                          {"avg": -0.3, "var": 0}, {"avg": 0.2 if axis == "we" else 0, "var": 0 if axis == "we" else 0.3}],
            "velocity": [{"avg": 0, "var": 0}, {"avg": -0.1, "var": 0}, {"avg": 0, "var": 0}],
            "quantity": {"avg": 0.06}, "size": {"avg": 0.12, "var": 0.03}, "particleModel": "Cube",
            "lifeLength": {"avg": 1.2, "var": 0}, "selfPropelled": False}]
    block("drippipe", {
        "variantgroups": [{"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-we": {"base": "block/pipes-run", "rotateY": 0}, "*-ns": {"base": "block/pipes-run", "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0.55, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0.55, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "lightAbsorption": 0, "resistance": 3, "sounds": METAL, "particlePropertiesByType": drips,
    }, "Overhead pipes with a leaking joint, dripping Almond Water onto the floor")
    name("drippipe-*", "Leaking Pipes")


# ======================= Level 3 =======================

def level3():
    cube_block("sanctumstone", "Ashlar Stone", ["plain"], {"plain": "sanctumwall"}, comment="Pale ashlar masonry of a Sanctum")
    cube_block("l3floor", {"grate": "Steel Grating", "hazard": "Marked Concrete", "stone": "Flagstones", "carpet": "Red Carpet"},
               ["grate", "hazard", "stone", "carpet"], {"grate": "grate", "hazard": "l3hazard", "stone": "l3stone", "carpet": "sanctumcarpet"},
               comment="Level 3 floors: steel grating, hazard-striped concrete, and the flagstones and carpet of a Sanctum")

    sparks = lambda side: [{  # noqa: E731
        "hsvaColor": [{"avg": 30, "var": 10}, {"avg": 160, "var": 40}, {"avg": 255, "var": 0}, {"avg": 255, "var": 0}],
        "gravityEffect": {"avg": 0.6, "var": 0.2},
        "posOffset": [{"avg": {"east": 0.55, "west": -0.55}.get(side, 0), "var": 0.05},
                      {"avg": -0.55, "var": 0.05}, {"avg": {"north": -0.55, "south": 0.55}.get(side, 0), "var": 0.05}],
        "velocity": [{"avg": {"east": 0.6, "west": -0.6}.get(side, 0), "var": 0.6}, {"avg": 0.5, "var": 0.5},
                     {"avg": {"north": -0.6, "south": 0.6}.get(side, 0), "var": 0.6}],
        "quantity": {"avg": 0.05, "var": 0.05}, "size": {"avg": 0.08, "var": 0.03}, "particleModel": "Cube",
        "lifeLength": {"avg": 0.5, "var": 0.2}, "vertexFlags": 255, "selfPropelled": False}]
    gauges = [bx("Pipe", (0, 2, -3), (16, 5, 0), "rust", faces=("north", "up", "down")),
              bx("Stem1", (4.5, 5, -2), (5.5, 7, -1), "metal"), bx("Stem2", (11, 5, -2), (12, 8, -1), "metal")] + \
        plate("Gauge1", (2.5, 7, -2.6), (7.5, 12, -1.4), "gauge", "metaldark") + plate("Gauge2", (9, 8, -2.6), (14, 13, -1.4), "gauge", "metaldark")
    decors = [
        Decor("dangersign", "Danger Sign", {2: plate("Sign", (3, 3, -0.4), (13, 13, 0), "dangersign", "steel")}),
        Decor("gauges", "Pressure Gauges", {2: gauges}),
        Decor("knifeswitch", "Knife Switch", {2: [bx("Slate", (3, 1, -1), (13, 15, 0), "slate"),
                                                  bx("BladeL", (5, 4, -3), (6, 12, -1), "copper"), bx("BladeR", (10, 4, -3), (11, 12, -1), "copper"),
                                                  bx("Handle", (4, 11, -4), (12, 12.5, -3), "rubber"),
                                                  bx("ClipL", (4.5, 2, -1.8), (6.5, 4, -1), "copper"), bx("ClipR", (9.5, 2, -1.8), (11.5, 4, -1), "copper")]}),
        Decor("junctionbox", "Junction Box", {
            2: [bx("Box", (4, 2, -3), (12, 11, 0), "metaldark"), bx("ConduitL", (5, 11, -1.5), (6.5, 16, 0), "metal"),
                bx("ConduitR", (9.5, 11, -1.5), (11, 16, 0), "metal")],
            3: [bx("ConduitL", (5, 0, -1.5), (6.5, 16, 0), "metal"), bx("ConduitR", (9.5, 0, -1.5), (11, 16, 0), "metal")]}),
        Decor("sparkoutlet", "Sparking Outlet", {1: plate("Outlet", (5.5, 4, -0.5), (10.5, 10, 0), "outletburnt", "metaldark") +
                                                 [bx("Wire", (8, 0, -1), (8.6, 4, -0.4), "cable"), bx("Tip", (7.9, -0.3, -1.1), (8.7, 0.3, -0.3), "copper")]},
              particles=sparks),
        Decor("bulkhead", "Bulkhead Light", {2: [bx("Base", (5, 4, -1), (11, 11, 0), "metaldark"),
                                                 bx("Glass", (5.5, 4.5, -3), (10.5, 10.5, -1), "bulkheadglass", glow=220),
                                                 bx("CageH", (5.2, 7.3, -3.3), (10.8, 7.7, -1), "metaldark"),
                                                 bx("CageV", (7.8, 4.2, -3.3), (8.2, 10.8, -1), "metaldark")]}, light=[6, 5, 9]),
        Decor("alarmbell", "Alarm Bell", {3: [bx("Plate", (6, 4, -0.6), (10, 11, 0), "metaldark")] + cyl("Bell", 8, -2.2, 3, 5, 10, "redmetal") +
                                          [bx("Striker", (7.5, 4, -2.5), (8.5, 5, -1.5), "metal")]}),
        Decor("wallcables", "Cable Run", {3: [bx("C1", (0, 4, -1.5), (16, 5.5, 0), "cable", faces=("north", "up", "down")),
                                              bx("C2", (0, 6, -2), (16, 8, 0), "cable", faces=("north", "up", "down")),
                                              bx("C3", (0, 9, -1.2), (16, 10, 0), "cable", faces=("north", "up", "down")),
                                              bx("Clamp", (7, 3.5, -2.3), (9, 10.5, 0), "metal"),
                                              bx("Droop", (11, 1, -1.8), (12, 4, -0.8), "cable")]}),
        Decor("risers", "Hot Pipes", {2: [bx("Hot", (4, 0, -4), (8, 16, 0), "lagging", faces=("north", "east", "west")),
                                          bx("Rusty", (10, 0, -3), (12.5, 16, 0), "rust", faces=("north", "east", "west")),
                                          bx("Clamp", (3.5, 9, -4.5), (13, 10.5, 0), "metal")],
                                      3: [bx("Hot", (4, 0, -4), (8, 16, 0), "lagging", faces=("north", "east", "west")),
                                          bx("Rusty", (10, 0, -3), (12.5, 16, 0), "rust", faces=("north", "east", "west"))]}),
    ] + [Decor(f"roomsign{i}", "Room Sign", {2: plate("Sign", (3, 4, -0.3), (13, 13, 0), f"roomsign{i}", "white")}) for i in range(8)]
    for material in ("glazed", "brick", "cinder"):
        wall_family(f"l3deco{material}", "Level 3 Wall", {1: material}, decors)
    wall_family("l3decostone", "Ashlar Stone", {1: "sanctumwall"}, [d for d in decors if d.code == "bulkhead"])

    prop("coilunit", "Conductor Coil", [
        bx("Base", (2, 0, 2), (14, 3, 14), "metaldark")] + cyl("Coil", 8, 8, 4.5, 3, 14, "coil") + [
        bx("Cap", (3, 14, 3), (13, 15, 13), "insulator"), bx("Insulator", (7, 15, 7), (9, 20, 9), "insulator"),
        bx("Ring1", (6.5, 16, 6.5), (9.5, 16.8, 9.5), "insulator"), bx("Ring2", (6.5, 18, 6.5), (9.5, 18.8, 9.5), "insulator"),
        bx("Terminal", (7.5, 20, 7.5), (8.5, 22, 8.5), "copper")], box=(0.12, 0, 0.12, 0.88, 1.35, 0.88), oriented=False,
         material="Metal", sounds=METAL, extra={"sounds": dict(METAL, ambient="backrooms:ambient/transformer", ambientBlockCount=6)})
    prop("switchgear", "Switchgear Cabinet", [
        bx("Body", (0.5, 0, 4), (15.5, 30, 15.5), "switchgear"),
        bx("Front", (1, 1, 3.6), (15, 29, 4), "switchgearfront", glow=30, faces=("north",), full=True),
        bx("Top", (0, 30, 3.5), (16, 31, 16), "metaldark")], box=(0.03, 0, 0.22, 0.97, 1.9, 0.97), material="Metal", sounds=METAL)
    prop("floorfan", "Industrial Fan", [
        bx("Feet", (3, 0, 7), (13, 1, 9), "metaldark"), bx("Post", (7.3, 1, 7.3), (8.7, 6, 8.7), "metaldark"),
        bx("GrilleF", (2, 5, 5.5), (14, 17, 6), "fancage", faces=("north", "south"), full=True),
        bx("GrilleB", (2, 5, 9), (14, 17, 9.5), "fancage", faces=("north", "south"), full=True),
        bx("RimT", (2, 16.5, 5.5), (14, 17, 9.5), "metaldark"), bx("RimB", (2, 5, 5.5), (14, 5.5, 9.5), "metaldark"),
        bx("RimL", (2, 5, 5.5), (2.5, 17, 9.5), "metaldark"), bx("RimR", (13.5, 5, 5.5), (14, 17, 9.5), "metaldark"),
        bx("BladeH", (4, 10.5, 7), (12, 11.5, 7.5), "metal"), bx("BladeV", (7.5, 7, 7), (8.5, 15, 7.5), "metal"),
        bx("Hub", (7, 10, 6.5), (9, 12, 8), "metal"), bx("Motor", (6, 9, 9.5), (10, 13, 13), "metaldark")],
         box=(0.12, 0, 0.3, 0.88, 1.1, 0.85), material="Metal", sounds=METAL)
    prop("generator", "Generator", [
        bx("Skid", (0, 0, 1), (16, 2, 15), "metaldark"), bx("Body", (1, 2, 2), (15, 12, 14), "generator"),
        bx("Panel", (4, 4, 1.6), (12, 10, 2), "generatorpanel", faces=("north",), full=True),
        bx("Exhaust", (12, 12, 10), (14, 18, 12), "rust"), bx("Cap", (11.5, 18, 9.5), (14.5, 18.6, 12.5), "rust"),
        bx("Filler", (3, 12, 9), (5, 13.5, 11), "metaldark"), bx("Grille", (14.9, 4, 4), (15.2, 11, 12), "fancage", faces=("east",), full=True)],
         box=(0, 0, 0.06, 1, 0.85, 0.94), material="Metal", sounds=METAL,
         extra={"sounds": dict(METAL, ambient="backrooms:ambient/transformer", ambientBlockCount=4)})
    prop("cablespool", "Cable Spool", [
        bx("FlangeL1", (0, 1, 3), (1.5, 14, 13), "spoolwood"), bx("FlangeL2", (0, 3, 1), (1.5, 12, 15), "spoolwood"),
        bx("FlangeR1", (14.5, 1, 3), (16, 14, 13), "spoolwood"), bx("FlangeR2", (14.5, 3, 1), (16, 12, 15), "spoolwood"),
        bx("Drum", (1.5, 2, 3), (14.5, 13, 13), "cable")], box=(0, 0, 0.06, 1, 0.88, 0.94), oriented=False)
    prop("controldesk", "Control Desk", [
        bx("Body", (0, 0, 4), (16, 11, 16), "switchgear"),
        bx("Panel", (0, 11, 4), (16, 12, 14), "controlpanel", faces=("up",), full=True, rot=(-20, 0, 0), origin=(8, 11, 4)),
        bx("PanelSides", (0, 11, 4), (16, 12, 14), "metaldark", faces=("north", "east", "west", "down"), rot=(-20, 0, 0), origin=(8, 11, 4)),
        bx("Backboard", (0, 11, 14), (16, 22, 16), "switchgear", faces=("east", "west", "up", "south")),
        bx("Meters", (0, 11, 14), (16, 22, 16), "switchgearfront", faces=("north",), full=True)],
         box=(0, 0, 0.25, 1, 1.35, 1), material="Metal", sounds=METAL)
    conveyor = [bx("SideL", (0, 6, 2), (16, 9, 3), "metaldark"), bx("SideR", (0, 6, 13), (16, 9, 14), "metaldark"),
                bx("Belt", (0, 8.2, 3), (16, 9, 13), "conveyorbelt"),
                bx("Leg1", (1, 0, 2.2), (2.5, 6, 3.5), "metaldark"), bx("Leg2", (1, 0, 12.5), (2.5, 6, 13.8), "metaldark"),
                bx("Leg3", (13.5, 0, 2.2), (15, 6, 3.5), "metaldark"), bx("Leg4", (13.5, 0, 12.5), (15, 6, 13.8), "metaldark"),
                bx("Brace", (1, 2, 3), (2.5, 3, 13), "metaldark"), bx("Brace2", (13.5, 2, 3), (15, 3, 13), "metaldark")]
    prop("conveyor", "Conveyor Belt", {"empty": conveyor, "box": conveyor + carton("Parcel", (4, 9, 4), (12, 15, 12))},
         box=(0, 0, 0.125, 1, 0.56, 0.875), material="Metal", sounds=METAL)
    prop("candelabra", "Candelabra", [
        bx("Base", (6, 0, 6), (10, 1, 10), "brass"), bx("Stem", (7.5, 1, 7.5), (8.5, 14, 8.5), "brass"),
        bx("Arms", (3, 13, 7.5), (13, 14, 8.5), "brass"),
        bx("CandleL", (3, 14, 7.5), (4, 18, 8.5), "tubewarm", glow=180), bx("CandleM", (7.5, 15, 7.5), (8.5, 19, 8.5), "tubewarm", glow=180),
        bx("CandleR", (12, 14, 7.5), (13, 18, 8.5), "tubewarm", glow=180)],
         box=(0.3, 0, 0.3, 0.7, 1.1, 0.7), oriented=False, material="Metal", sounds=METAL, light=[6, 5, 10])
    prop("angelstatue", "Statue", [
        bx("Pedestal", (1, 0, 1), (15, 8, 15), "stone"), bx("Plinth", (0.5, 8, 0.5), (15.5, 9, 15.5), "stone"),
        bx("Robe", (4, 9, 5), (12, 25, 11), "stone"), bx("Hem", (3.5, 9, 4.5), (12.5, 12, 11.5), "stone"),
        bx("Head", (6, 25, 6), (10, 29.5, 10), "stone"),
        bx("WingL", (-3, 13, 10), (4, 30, 11), "stonewing", faces=("north", "south", "west", "up", "down")),
        bx("WingR", (12, 13, 10), (19, 30, 11), "stonewing", faces=("north", "south", "east", "up", "down")),
        bx("WingL2", (0, 17, 10.6), (5, 28, 11.6), "stonewing"), bx("WingR2", (11, 17, 10.6), (16, 28, 11.6), "stonewing"),
        bx("Hands", (6.5, 17, 3.5), (9.5, 21, 5), "stone"), bx("Arms", (4.5, 17, 4.5), (11.5, 19, 6), "stone"),
        bx("Halo", (5, 30.5, 7.5), (11, 31.3, 8.5), "gilt", glow=120)],
         box=(0.06, 0, 0.06, 0.94, 1.95, 0.94), material="Stone", sounds=STONE)
    prop("floorcable", "Floor Cables", [
        bx("C1", (0, 0, 5.5), (16, 0.8, 6.3), "cable"), bx("C2", (0, 0, 7.5), (16, 1, 8.6), "cable"),
        bx("C3", (0, 0, 9.8), (16, 0.7, 10.4), "cable")], collide=False, material="Metal", sounds=METAL,
         extra={"selectionbox": {"x1": 0, "y1": 0, "z1": 0.3, "x2": 1, "y2": 0.07, "z2": 0.7}})
    prop("pipestack", "Stacked Pipes", [bx(f"P{i}", (0, y, z), (16, y + 3, z + 3), "rust") for i, (y, z) in
                                        enumerate(((0, 2), (0, 6), (0, 10), (3, 4), (3, 8), (6, 6)))] +
         [bx("Chock1", (2, 0, 1), (3.5, 2, 15), "wood"), bx("Chock2", (12.5, 0, 1), (14, 2, 15), "wood")],
         box=(0, 0, 0.06, 1, 0.56, 0.94), material="Metal", sounds=METAL)
    prop("cabledroop", "Drooping Cables", {"plain": [
        bx("Tray", (0, 11.5, 1), (16, 12, 15.5), "metal", faces=("north", "south", "up", "down"))] +
        [bx(f"Cable{i}", (0, y, z), (16, y + r, z + r), "cable", faces=("north", "south", "up", "down"))
         for i, (y, z, r) in enumerate(((12.5, 2, 1.5), (13, 5, 1), (12, 8, 2), (13.5, 11.5, 1), (12.5, 13.5, 1.5)))] + [
        bx("Hanger", (7.5, 12, 0.5), (8.5, 16, 1), "metal"), bx("Hanger2", (7.5, 12, 15.5), (8.5, 16, 16), "metal"),
        bx("LoopL", (3, 5, 4), (4, 11.5, 5), "cable"), bx("LoopB", (3, 5, 4), (10, 6, 5), "cable"), bx("LoopR", (9, 5, 4), (10, 11.5, 5), "cable"),
        bx("Dangle", (12, 2, 10), (12.8, 11.5, 10.8), "cable"), bx("Tip", (12, 1.4, 10), (12.8, 2, 10.8), "copper")]},
         box=(0, 0.7, 0, 1, 1, 1), material="Metal", sounds=METAL)


# ======================= Level 4 =======================

def level4():
    cube_block("officeceilingalt", {"vent": "Air Diffuser", "sprinkler": "Ceiling Tile", "stain": "Stained Ceiling Tile"},
               ["vent", "sprinkler", "stain"], {"vent": "officeceiling-vent", "sprinkler": "officeceiling-sprinkler", "stain": "officeceiling-stain"},
               material="Ceramic", sounds=GLASS, comment="Drop-ceiling tiles with air diffusers, sprinkler heads and water stains",
               drops=CEILING_DROPS, resistance=1)
    cube_block("officewindowalt", {"blackout": "Blacked-Out Window", "blinds": "Window with Blinds"}, ["blackout", "blinds"],
               {"blackout": "officewindow-blackout", "blinds": "officewindow-blinds"}, material="Glass", sounds=GLASS,
               comment="Windows papered over or shut behind blinds. Most of Level 4's windows are", drops=[],
               lightHsvByType={"*-blinds": [36, 1, 4]}, lightAbsorptionByType={"*-blinds": 0, "*": 99})
    cube_block("officecarpetalt", {"papers": "Office Carpet", "stain": "Stained Office Carpet"}, ["papers", "stain"],
               {"papers": "officecarpet-papers", "stain": "officecarpet-stain"}, material="Cloth", sounds=CLOTH)
    cube_block("drywallbase", "Office Wall", ["plain"], {"plain": "drywall-base"}, comment="Office drywall with a dark vinyl skirting")

    decors = [
        Decor("fountain", "Drinking Fountain", {1: [
            bx("Back", (4, 2, -0.8), (12, 14, 0), "fountainsteel"), bx("Basin", (3, 8, -6), (13, 11, -0.8), "fountainsteel"),
            bx("Bowl", (4, 11, -5.5), (12, 11.05, -1.3), "steeldark", faces=("up",)),
            bx("Skirt", (5, 2, -3), (11, 8, -0.8), "fountainsteel"), bx("Spout", (7.5, 11, -4), (8.5, 12, -3), "steel"),
            bx("Button", (12.6, 9, -4), (13.4, 10, -3), "steel")]}, cls=("BackroomsDispenser", "BackroomsDispenser")),
        Decor("clock", "Wall Clock", {3: [bx("Rim", (4, 2, -1.5), (12, 10, 0), "metaldark", faces=("east", "west", "up", "down")),
                                          bx("Face", (4, 2, -1.5), (12, 10, -1.4), "clockface", faces=("north",), full=True)]}),
        Decor("whiteboard", "Whiteboard", {2: plate("Board", (0, 0.5, -0.8), (16, 14, 0), "whiteboard", "steel") +
                                           [bx("Tray", (1, 0, -2), (15, 1, -0.8), "steel"), bx("Marker", (3, 1, -1.8), (6, 1.6, -1.2), "redmetal")]}),
        Decor("corkboard", "Corkboard", {2: plate("Board", (2, 2, -0.8), (14, 13, 0), "corkboard", "wood")}),
        Decor("evacmap", "Evacuation Map", {2: plate("Map", (4, 3, -0.6), (12, 13, 0), "evacmap", "metaldark")}),
        Decor("extinguisher", "Fire Extinguisher Cabinet", {2: plate("Cabinet", (4, 0, -1), (12, 14, 0), "extcabinet", "steel")}),
        Decor("alarm", "Fire Alarm", {2: plate("Pull", (6, 2, -1.5), (10, 7, 0), "firealarm", "redmetal") +
                                      plate("Strobe", (5.5, 9, -1.5), (10.5, 13, 0), "strobe", "white")}),
        Decor("switch", "Light Switch", {2: plate("Switch", (2, 3, -0.4), (4.5, 7.5, 0), "switchplate", "switchplate") +
                                         [bx("Toggle", (2.9, 5, -0.8), (3.6, 6, -0.4), "white")] +
                                         plate("Thermostat", (8, 5, -0.9), (13, 9, 0), "thermostat", "switchplate")}),
        Decor("frameghost", "Faded Wall", {2: [bx("Mark", (3, 2, -0.05), (13, 14, 0), "frameghost", faces=("north",), full=True),
                                               bx("Nail", (7.7, 13.5, -0.6), (8.3, 14.1, 0), "metaldark")]}),
        Decor("phone", "Wall Phone", {2: [bx("Body", (5, 3, -2), (11, 12, 0), "wallphone"), bx("Handset", (3.6, 4, -3), (5.2, 11, -2), "wallphone"),
                                          bx("Cord", (4.1, 1, -2.8), (4.6, 4, -2.3), "rubber")]}),
        Decor("callbutton", "Elevator Call Button", {2: plate("Panel", (6, 4, -0.6), (10, 11, 0), "callpanel", "steel", glow=40)}),
        Decor("stairsign", "Stairwell Sign", {2: plate("Sign", (4, 4, -0.4), (12, 12, 0), "stairsign-office", "steel")}),
    ] + [Decor(f"poster{i}", "Framed Poster", {2: plate("Poster", (2, 1, -0.8), (14, 15, 0), f"poster{i}", "metaldark")}) for i in range(3)]
    wall_family("officedeco", "Office Wall", {1: "drywall-base", 2: "drywall"}, decors)

    chair = [bx("Seat", (3, 6, 3), (13, 8, 13), "chairfabric"), bx("Back", (3.5, 8, 11), (12.5, 17, 13), "chairfabric"),
             bx("Post", (7, 2, 7), (9, 6, 9), "metaldark"), bx("BaseX", (2, 0.5, 7.5), (14, 1.5, 8.5), "metaldark"),
             bx("BaseZ", (7.5, 0.5, 2), (8.5, 1.5, 14), "metaldark")]
    tipped = []
    for e in chair:
        e = json.loads(json.dumps(e))
        e["rotationOrigin"], e["rotationZ"] = [8, 6, 8], 90
        tipped.append(e)
    prop("officechairtipped", "Office Chair", tipped, box=(0.1, 0, 0.1, 0.9, 0.85, 0.9), material="Cloth", sounds=CLOTH)
    prop("ficus", "Dead Ficus", [
        bx("Pot", (5, 0, 5), (11, 7, 11), "planter"), bx("Soil", (5.5, 6.9, 5.5), (10.5, 7, 10.5), "wooddark", faces=("up",)),
        bx("Trunk", (7.5, 7, 7.5), (8.5, 18, 8.5), "wood"),
        bx("Leaves1", (3, 15, 4), (12, 22, 12), "ficusleaves"), bx("Leaves2", (5, 20, 3), (13, 26, 11), "ficusleaves"),
        bx("Leaves3", (4, 24, 6), (10, 29, 12), "ficusleaves"),
        bx("Fallen1", (2, 0, 10), (4, 0.2, 12), "dryleaf"), bx("Fallen2", (11, 0, 3), (13, 0.2, 4.5), "dryleaf")],
         box=(0.3, 0, 0.3, 0.7, 1.8, 0.7), oriented=False, material="Plant", sounds=CLOTH)
    stack = []
    for i in range(4):
        y = i * 2.2
        stack += [bx(f"Seat{i}", (3, 6 + y, 3), (13, 7 + y, 13), "plasticchair"), bx(f"Back{i}", (3, 7 + y, 12), (13, 15 + y, 13), "plasticchair")]
    stack += [bx(f"Leg{i}", (x, 0, z), (x + 1, 6, z + 1), "foldsteel") for i, (x, z) in enumerate(((3, 3), (12, 3), (3, 12), (12, 12)))]
    prop("chairstack", "Stacked Chairs", stack, box=(0.18, 0, 0.18, 0.82, 1.5, 0.82), oriented=False)
    prop("copier", "Photocopier", [
        bx("Body", (1, 0, 3), (15, 14, 15), "copier"), bx("Lid", (1, 14, 3), (15, 15, 15), "metaldark"),
        bx("Panel", (2, 14, 3), (8, 15.5, 5.5), "copierpanel", faces=("up", "north"), full=True),
        bx("Tray", (15, 8, 6), (17, 9, 12), "copier"), bx("Paper", (15.2, 9, 6.5), (16.8, 9.4, 11.5), "paper"),
        bx("Drawer", (2, 2, 2.7), (14, 6, 3), "metaldark"), bx("Drawer2", (2, 7, 2.7), (14, 11, 3), "metaldark")],
         box=(0.06, 0, 0.18, 0.94, 0.95, 0.94), material="Metal", sounds=METAL)
    shelf = [bx("SideL", (0, 0, 8), (1, 30, 16), "laminate"), bx("SideR", (15, 0, 8), (16, 30, 16), "laminate"),
             bx("Back", (1, 0, 15.5), (15, 30, 16), "laminate")] + \
        [bx(f"Shelf{i}", (1, y, 8), (15, y + 1, 16), "laminate") for i, y in enumerate((0, 7.5, 15, 22.5, 29))]
    prop("officebookshelf", "Bookshelf", shelf + [
        bx("Binders1", (2, 1, 9), (7, 7, 15), "binders", faces=("north",), full=True), bx("Binders1S", (2, 1, 9), (7, 7, 15), "laminate", faces=("east", "west", "up")),
        bx("Binders2", (8, 16, 9), (12, 22, 15), "binders", faces=("north",), full=True), bx("Binders2S", (8, 16, 9), (12, 22, 15), "laminate", faces=("east", "west", "up")),
        bx("Lying", (3, 23.5, 9), (9, 25, 15), "binders")], box=(0, 0, 0.5, 1, 1.9, 1))
    prop("serverrack", "Server Rack", [
        bx("Body", (2, 0, 2), (14, 30, 15), "metaldark"),
        bx("Front", (2.5, 1, 1.6), (13.5, 29, 2), "serverfront", glow=80, faces=("north",), full=True)],
         box=(0.12, 0, 0.1, 0.88, 1.9, 0.94), material="Metal", sounds=METAL,
         extra={"sounds": dict(METAL, ambient="backrooms:ambient/transformer", ambientBlockCount=10)})
    counter = [bx("Cabinet", (0, 1, 4), (16, 13, 16), "cabinetwhite", faces=("north",), full=True),
               bx("CabinetSides", (0, 1, 4), (16, 13, 16), "white", faces=("east", "west", "south")),
               bx("Kick", (0, 0, 4.3), (16, 1, 16), "rubber"),
               bx("Top", (0, 13, 3.5), (16, 14.5, 16), "countertop"), bx("Splash", (0, 14.5, 15), (16, 18, 16), "countertop")]
    prop("kitchencounter", "Kitchen Counter", {
        "plain": counter,
        "sink": counter + [bx("Basin", (3, 14.45, 6), (13, 14.6, 13), "steeldark", faces=("up",)),
                           bx("Faucet", (7.5, 14.5, 13.5), (8.5, 19, 14.5), "steel"), bx("Spout", (7.5, 18, 10.5), (8.5, 19, 13.5), "steel")],
        "micro": counter + [bx("Microwave", (2, 14.5, 7), (13, 21, 15), "white", faces=("east", "west", "up", "south")),
                            bx("Door", (2, 14.5, 7), (13, 21, 7.2), "microwave", faces=("north",), full=True)]},
         box=(0, 0, 0.22, 1, 0.9, 1))
    prop("fridge", "Refrigerator", [
        bx("Body", (1, 0, 3), (15, 30, 15), "fridgewhite"), bx("Seam", (1, 18, 2.7), (15, 18.5, 3), "steeldark"),
        bx("Handle1", (12, 20, 2), (13, 27, 2.7), "steel"), bx("Handle2", (12, 9, 2), (13, 16, 2.7), "steel")],
         box=(0.06, 0, 0.18, 0.94, 1.9, 0.94), material="Metal", sounds=METAL)
    prop("roundtable", "Break Room Table", [
        bx("Top", (1, 12, 1), (15, 13, 15), "laminate"), bx("Post", (7, 1, 7), (9, 12, 9), "metaldark"),
        bx("Foot", (4, 0, 4), (12, 1, 12), "metaldark")], box=(0.06, 0, 0.06, 0.94, 0.82, 0.94), oriented=False)
    prop("receptiondesk", "Reception Desk", [
        bx("Front", (0, 0, 2), (16, 17, 4), "receptionfront", faces=("north",), full=True),
        bx("FrontSides", (0, 0, 2), (16, 17, 4), "laminate", faces=("east", "west", "south")),
        bx("Counter", (0, 17, 1.5), (16, 18, 6.5), "countertop"), bx("Worktop", (0, 11, 4), (16, 12, 15), "laminate"),
        bx("Back", (0, 0, 14), (16, 11, 15), "laminate"), bx("Crt", (4, 12, 8), (10, 18, 14), "crt"),
        bx("Screen", (4.5, 13, 14), (9.5, 17, 14.2), "crtscreen", faces=("south",), full=True)],
         box=(0, 0, 0.06, 1, 1.15, 1))
    prop("wastebasket", "Wastebasket", [bx("Bin", (5, 0, 5), (11, 6, 11), "wastebin"), bx("Ball", (6, 5, 6), (8, 7, 8), "paper")],
         oriented=False, collide=False, extra={"selectionbox": {"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 0.4, "z2": 0.7}})
    prop("coatstand", "Coat Stand", [
        bx("Base", (5, 0, 5), (11, 1, 11), "wooddark"), bx("Pole", (7.5, 1, 7.5), (8.5, 28, 8.5), "wooddark"),
        bx("HookX", (5, 26, 7.5), (11, 27, 8.5), "wooddark"), bx("HookZ", (7.5, 26, 5), (8.5, 27, 11), "wooddark"),
        bx("Coat", (5.5, 14, 8.5), (10.5, 26, 11), "coat")], box=(0.3, 0, 0.3, 0.7, 1.8, 0.7), oriented=False)
    prop("bench", "Bench", [bx("Seat", (0, 6, 5), (16, 7.5, 11), "benchwood"),
                            bx("LegL", (1, 0, 5.5), (2.5, 6, 10.5), "metaldark"), bx("LegR", (13.5, 0, 5.5), (15, 6, 10.5), "metaldark")],
         box=(0, 0, 0.3, 1, 0.47, 0.7))


# ======================= Level 5 =======================

def level5():
    cube_block("hotelfloor", {"marble": "Marble Floor", "runnerns": "Carpet Runner", "runnerwe": "Carpet Runner", "rug": "Rug"},
               ["marble", "runnerns", "runnerwe", "rug"], {"marble": "marble", "runnerns": "runner-ns", "runnerwe": "runner-we", "rug": "rug"},
               material="Stone", sounds=STONE, comment="Hotel floors: white marble, runners over walnut, and Persian rugs")
    gauges = [bx("Pipe", (0, 2, -3), (16, 5, 0), "rust", faces=("north", "up", "down")),
              bx("Stem1", (4.5, 5, -2), (5.5, 7, -1), "metal")] + plate("Gauge1", (2.5, 7, -2.6), (7.5, 12, -1.4), "gauge", "metaldark")
    decors = [
        Decor("mirror", "Gilt Mirror", {2: [bx("Frame", (3, 0, -1), (13, 16, 0), "gilt"),
                                            bx("Glass", (3.8, 0.8, -1.1), (12.2, 15.2, -1), "mirrorglass", faces=("north",), full=True)]}),
        Decor("speaker", "Speaker", {3: [bx("Box", (4, 3, -1.5), (12, 11, 0), "mahogany"),
                                         bx("Grille", (4.5, 3.5, -1.6), (11.5, 10.5, -1.5), "speakergrille", faces=("north",), full=True)]},
              ambient=("backrooms:ambient/jazz", 3)),
        Decor("housephone", "House Phone", {2: [bx("Plate", (5, 2, -1), (11, 13, 0), "bakelite"),
                                                bx("Dial", (6.2, 3, -1.4), (9.8, 6.6, -1), "phonedial", faces=("north",), full=True),
                                                bx("Handset", (4, 8, -2.6), (12, 9.6, -1.2), "bakelite"),
                                                bx("EarL", (4, 6.5, -2.6), (5.5, 8, -1.2), "bakelite"), bx("EarR", (10.5, 6.5, -2.6), (12, 8, -1.2), "bakelite")]}),
        Decor("firehose", "Fire Hose Cabinet", {2: plate("Cabinet", (2, 0, -2), (14, 15, 0), "hotelhosecab", "brass")}),
        Decor("clock", "Wall Clock", {3: plate("Clock", (4, 1, -1.5), (12, 12, 0), "ornateclock", "gilt")}),
        Decor("keyrack", "Key Rack", {2: plate("Rack", (0, 0, -2), (16, 15, 0), "keyrack", "mahogany")}),
        Decor("callplate", "Elevator Call Plate", {2: plate("Plate", (6, 3, -0.6), (10, 11, 0), "callplate", "brass")}),
        Decor("landscape", "Painting", {2: [bx("Canvas", (3, 3, -0.6), (13, 13, -0.4), "landscape", faces=("north",), full=True),
                                            bx("FrameT", (2, 13, -1.2), (14, 14, 0), "gilt"), bx("FrameB", (2, 2, -1.2), (14, 3, 0), "gilt"),
                                            bx("FrameL", (2, 3, -1.2), (3, 13, 0), "gilt"), bx("FrameR", (13, 3, -1.2), (14, 13, 0), "gilt")]}),
    ]
    wall_family("hoteldeco", "Hotel Wall", {1: "wainscot", 2: "hotelpanel", 3: "frieze"}, decors, material="Wood", sounds=WOOD)
    pipesv = [bx("Rusty", (2, 0, -4), (5, 16, 0), "rust", faces=("north", "east", "west")),
              bx("Lagged", (9, 0, -3.5), (13, 16, 0), "lagging", faces=("north", "east", "west"))]
    wheel = [bx("Stem", (7.5, 9.5, -5), (8.5, 10.5, -3), "metal"),
             bx("RimT", (5, 12.5, -6), (11, 13.5, -5), "valve"), bx("RimB", (5, 6.5, -6), (11, 7.5, -5), "valve"),
             bx("RimL", (4.5, 7, -6), (5.5, 13, -5), "valve"), bx("RimR", (10.5, 7, -6), (11.5, 13, -5), "valve"),
             bx("Spoke", (7.5, 7, -5.8), (8.5, 13, -5.2), "valve"), bx("SpokeH", (5, 9.5, -5.8), (11, 10.5, -5.2), "valve")]
    wall_family("plasterdeco", "Plaster Wall", {1: "plaster"}, [
        Decor("pipesv", "Pipes", {1: pipesv, 2: pipesv + [bx("Clamp", (1.5, 8, -4.5), (13.5, 9.5, 0), "metal")], 3: pipesv, 4: pipesv}),
        Decor("valve", "Valve", {1: [bx("Pipe", (0, 8, -3), (16, 12, 0), "rust", faces=("north", "up", "down"))] + wheel}),
        Decor("gauges", "Pressure Gauge", {2: gauges}),
        Decor("pipecluster", "Pipes", {3: [bx("P1", (0, 2, -3), (16, 5, 0), "rust", faces=("north", "up", "down")),
                                           bx("P2", (0, 6, -4), (16, 10, 0), "lagging", faces=("north", "up", "down")),
                                           bx("P3", (0, 11, -2.5), (16, 13.5, 0), "redpipe", faces=("north", "up", "down")),
                                           bx("Bracket", (7, 1, -4.5), (9, 15, 0), "metal")]}),
    ])

    lamp = [bx("LampBase", (3, 13, 11), (5, 14, 13), "brass"), bx("LampStem", (3.6, 14, 11.6), (4.4, 18, 12.4), "brass"),
            bx("Shade", (2, 17, 10.5), (6, 21, 13.5), "lampshade", glow=90)]
    prop("consoletable", "Console Table", [
        bx("Top", (1, 12, 9), (15, 13, 15), "marbletop"), bx("Apron", (1.5, 10, 9.5), (14.5, 12, 14.5), "mahogany"),
        bx("Leg1", (2, 0, 10), (3, 10, 11), "mahogany"), bx("Leg2", (13, 0, 10), (14, 10, 11), "mahogany"),
        bx("Leg3", (2, 0, 13), (3, 10, 14), "mahogany"), bx("Leg4", (13, 0, 13), (14, 10, 14), "mahogany"),
        bx("Shelf", (2, 2, 10), (14, 2.8, 14), "mahogany"),
        bx("Vase", (10, 13, 11), (13, 18, 14), "vase"), bx("Flowers", (10.3, 18, 11.3), (12.7, 22, 13.7), "driedflowers")] + lamp,
         box=(0.06, 0, 0.55, 0.94, 0.82, 0.94), light=[6, 5, 8])
    books = [bx("Books1", (1, 1, 9), (15, 7, 15), "books", faces=("north",), full=True),
             bx("Books2", (1, 8.5, 9), (15, 14.5, 15), "books", faces=("north",), full=True),
             bx("Books3", (1, 16, 9), (15, 22, 15), "books", faces=("north",), full=True),
             bx("Books4", (1, 23.5, 9), (15, 29, 15), "books", faces=("north",), full=True)]
    hshelf = [bx("SideL", (0, 0, 8), (1, 30, 16), "mahogany"), bx("SideR", (15, 0, 8), (16, 30, 16), "mahogany"),
              bx("Back", (1, 0, 15.5), (15, 30, 16), "mahogany"), bx("Crown", (-0.5, 30, 7.5), (16.5, 31.5, 16), "mahogany")] + \
        [bx(f"Shelf{i}", (1, y, 8), (15, y + 1, 16), "mahogany") for i, y in enumerate((0, 7.5, 15, 22.5))]
    prop("hotelbookshelf", "Bookshelf", hshelf + books, box=(0, 0, 0.5, 1, 1.95, 1))
    curio = [bx("Frame", (1, 0, 8), (15, 30, 16), "mahogany", faces=("east", "west", "up", "down", "south")),
             bx("Glass", (2, 2, 8), (14, 28, 8.3), "curioglass", faces=("north",), full=True),
             bx("FrameT", (1, 28, 7.6), (15, 30, 8.3), "mahogany"), bx("FrameB", (1, 0, 7.6), (15, 2, 8.3), "mahogany"),
             bx("FrameL", (1, 2, 7.6), (2, 28, 8.3), "mahogany"), bx("FrameR", (14, 2, 7.6), (15, 28, 8.3), "mahogany"),
             bx("Knob", (12.5, 14, 7), (13.5, 15, 7.6), "brass")]
    prop("curiocabinet", "Curio Cabinet", curio, box=(0.06, 0, 0.47, 0.94, 1.9, 1))
    prop("luggagecart", "Luggage Cart", [
        bx("Deck", (1, 1, 1), (15, 2, 15), "cartcarpet"),
        bx("WheelA", (1.5, 0, 1.5), (3, 1, 3), "rubber"), bx("WheelB", (13, 0, 1.5), (14.5, 1, 3), "rubber"),
        bx("WheelC", (1.5, 0, 13), (3, 1, 14.5), "rubber"), bx("WheelD", (13, 0, 13), (14.5, 1, 14.5), "rubber"),
        bx("PostL", (1, 2, 7.5), (2, 28, 8.5), "brass"), bx("PostR", (14, 2, 7.5), (15, 28, 8.5), "brass"),
        bx("Rail", (1, 27, 7.5), (15, 28, 8.5), "brass"), bx("Hanger", (2, 25, 7.8), (14, 25.6, 8.2), "brass"),
        bx("Case1", (3, 2, 2.5), (13, 10, 7), "suitcaseleather"), bx("Case2", (3.5, 2, 9), (12.5, 9, 14), "suitcasetan"),
        bx("Case3", (4, 10, 3), (12, 15, 6.5), "suitcasetan"), bx("HatBox", (5, 9, 9.5), (10, 13, 13.5), "velvet")],
         box=(0.06, 0, 0.06, 0.94, 1.75, 0.94), oriented=False, material="Metal", sounds=METAL)
    prop("servicetrolley", "Room Service Trolley", [
        bx("Cloth", (1, 9, 2), (15, 12, 14), "tablecloth"),
        bx("Drape", (1, 4, 1.8), (15, 12, 2.1), "tablecloth"), bx("Drape2", (1, 4, 13.9), (15, 12, 14.2), "tablecloth"),
        bx("Shelf", (1.5, 2, 2.5), (14.5, 2.5, 13.5), "silver"),
        bx("LegA", (1.5, 0, 2.5), (2.5, 9, 3.5), "silver"), bx("LegB", (13.5, 0, 2.5), (14.5, 9, 3.5), "silver"),
        bx("LegC", (1.5, 0, 12.5), (2.5, 9, 13.5), "silver"), bx("LegD", (13.5, 0, 12.5), (14.5, 9, 13.5), "silver"),
        bx("Cloche", (5, 12, 5), (11, 14.5, 11), "silver"), bx("Knob", (7.5, 14.5, 7.5), (8.5, 15.3, 8.5), "silver"),
        bx("Plate", (11.5, 12, 3), (14, 12.3, 5.5), "china"), bx("Bottle", (2.5, 12, 10), (4, 17, 11.5), "bankergreen")],
         box=(0.06, 0, 0.12, 0.94, 0.8, 0.88), material="Cloth", sounds=CLOTH)
    prop("radiator", "Radiator", [bx(f"Fin{i}", (1.5 + 2 * i, 1, 11), (2.7 + 2 * i, 13, 15), "radiator") for i in range(7)] +
         [bx("Top", (1, 12, 11.5), (15, 13, 14.5), "radiator"), bx("Bottom", (1, 2, 11.5), (15, 3, 14.5), "radiator"),
          bx("FootL", (2, 0, 12), (3, 1, 14), "metaldark"), bx("FootR", (13, 0, 12), (14, 1, 14), "metaldark"),
          bx("Valve", (14.5, 2, 12.5), (16, 3.5, 14), "brass")], box=(0.06, 0, 0.66, 0.94, 0.82, 0.94), material="Metal", sounds=METAL)
    prop("writingdesk", "Writing Desk", [
        bx("Top", (0, 12, 5), (16, 13, 16), "mahogany"), bx("Drawers", (10, 1, 6), (15, 12, 15), "mahogany"),
        bx("Knob1", (12, 9, 5.5), (13, 10, 6), "brass"), bx("Knob2", (12, 4, 5.5), (13, 5, 6), "brass"),
        bx("LegL1", (1, 0, 6), (2, 12, 7), "mahogany"), bx("LegL2", (1, 0, 14), (2, 12, 15), "mahogany"),
        bx("LampBase", (2, 13, 11), (6, 14, 14), "brass"), bx("LampStem", (3.5, 14, 12.5), (4.5, 16, 13.5), "brass"),
        bx("Shade", (1.5, 16, 10.5), (6.5, 18, 13), "bankergreen", glow=80),
        bx("Paper", (8, 13, 8), (12, 13.2, 12), "paper"), bx("Ink", (12.5, 13, 9), (13.5, 14, 10), "bakelite")],
         box=(0, 0, 0.3, 1, 0.82, 1), light=[14, 4, 7])
    prop("hotelchair", "Side Chair", [
        bx("Seat", (3, 7, 3), (13, 8.5, 13), "velvet"),
        bx("LegFL", (3.5, 0, 3.5), (4.5, 7, 4.5), "mahogany"), bx("LegFR", (11.5, 0, 3.5), (12.5, 7, 4.5), "mahogany"),
        bx("LegBL", (3.5, 0, 11.5), (4.5, 20, 12.5), "mahogany"), bx("LegBR", (11.5, 0, 11.5), (12.5, 20, 12.5), "mahogany"),
        bx("Back", (4.5, 11, 11.8), (11.5, 19, 12.4), "velvet"), bx("Rail", (3.5, 19, 11.5), (12.5, 20.5, 12.5), "mahogany")],
         box=(0.18, 0, 0.18, 0.82, 1.25, 0.82))
    prop("floorlamp", "Floor Lamp", [
        bx("Base", (5, 0, 5), (11, 1, 11), "brass"), bx("Pole", (7.5, 1, 7.5), (8.5, 24, 8.5), "brass"),
        bx("Shade", (4, 22, 4), (12, 29, 12), "lampshade", glow=120)],
         box=(0.25, 0, 0.25, 0.75, 1.8, 0.75), oriented=False, light=[6, 5, 10])
    prop("suitcase", "Suitcase", [
        bx("Case", (2, 0, 4), (14, 10, 12), "suitcaseleather"), bx("Handle", (6, 10, 7.5), (10, 11.5, 8.5), "bakelite"),
        bx("ClaspL", (4, 7, 3.7), (5, 8.5, 4), "brass"), bx("ClaspR", (11, 7, 3.7), (12, 8.5, 4), "brass")],
         box=(0.12, 0, 0.25, 0.88, 0.7, 0.75), material="Cloth", sounds=CLOTH)
    prop("coffeetable", "Coffee Table", [
        bx("Top", (1, 7, 3), (15, 8, 13), "mahogany"), bx("Inlay", (3, 8, 5), (13, 8.05, 11), "marbletop", faces=("up",)),
        bx("Leg1", (2, 0, 4), (3, 7, 5), "mahogany"), bx("Leg2", (13, 0, 4), (14, 7, 5), "mahogany"),
        bx("Leg3", (2, 0, 11), (3, 7, 12), "mahogany"), bx("Leg4", (13, 0, 11), (14, 7, 12), "mahogany"),
        bx("Ashtray", (9, 8, 6), (11, 8.6, 8), "crystal")], box=(0.06, 0, 0.18, 0.94, 0.5, 0.82), oriented=False)
    prop("grandfatherclock", "Grandfather Clock", [
        bx("Base", (3, 0, 6), (13, 10, 14), "mahogany"), bx("Trunk", (4, 10, 6.5), (12, 24, 13.5), "mahogany"),
        bx("Window", (5, 12, 6.3), (11, 22, 6.5), "clockpendulum", faces=("north",), full=True),
        bx("Hood", (3, 24, 6), (13, 32, 14), "mahogany"),
        bx("Face", (4.5, 25, 5.8), (11.5, 31, 6), "clockface-old", faces=("north",), full=True),
        bx("Finial", (7.5, 32, 9.5), (8.5, 34, 10.5), "brass")],
         box=(0.18, 0, 0.36, 0.82, 1.95, 0.88), extra={"sounds": dict(WOOD, ambient="backrooms:ambient/clock", ambientBlockCount=1)})
    prop("hotelreception", "Front Desk", [
        bx("Front", (0, 0, 2), (16, 17, 5), "receptionmahogany", faces=("north",), full=True),
        bx("FrontSides", (0, 0, 2), (16, 17, 5), "mahogany", faces=("east", "west", "south")),
        bx("Top", (0, 17, 1), (16, 18.5, 8), "marbletop"), bx("Shelf", (0, 10, 5), (16, 11, 14), "mahogany"),
        bx("Bell", (11, 18.5, 3), (13, 19.5, 5), "brass"), bx("Button", (11.8, 19.5, 3.8), (12.2, 20, 4.2), "brass"),
        bx("Book", (3, 18.5, 2.5), (8, 19, 6), "guestbook", faces=("up",), full=True),
        bx("BookSides", (3, 18.5, 2.5), (8, 19, 6), "velvet", faces=("north", "south", "east", "west"))],
         box=(0, 0, 0.06, 1, 1.2, 0.9))
    prop("ashtraystand", "Ashtray Stand", [
        bx("Base", (5, 0, 5), (11, 1, 11), "brass"), bx("Pole", (7.5, 1, 7.5), (8.5, 14, 8.5), "brass"),
        bx("Dish", (5, 14, 5), (11, 15, 11), "brass"), bx("Sand", (5.5, 15, 5.5), (10.5, 15.1, 10.5), "paper", faces=("up",))],
         box=(0.3, 0, 0.3, 0.7, 0.95, 0.7), oriented=False, material="Metal", sounds=METAL)
    prop("diningtable", "Dining Table", [
        bx("Top", (0.5, 11, 0.5), (15.5, 12, 15.5), "tablecloth"), bx("Skirt", (0.5, 7, 0.5), (15.5, 11, 15.5), "tablecloth", faces=("north", "south", "east", "west")),
        bx("Post", (7, 0, 7), (9, 7, 9), "mahogany"), bx("Foot", (4, 0, 4), (12, 1, 12), "mahogany"),
        bx("PlateN", (6.5, 12, 1.5), (9.5, 12.3, 4.5), "china"), bx("PlateS", (6.5, 12, 11.5), (9.5, 12.3, 14.5), "china"),
        bx("PlateW", (1.5, 12, 6.5), (4.5, 12.3, 9.5), "china"), bx("PlateE", (11.5, 12, 6.5), (14.5, 12.3, 9.5), "china"),
        bx("Glass1", (10, 12, 3), (11, 14, 4), "crystal"), bx("Glass2", (5, 12, 12), (6, 14, 13), "crystal"),
        bx("Candle", (7.5, 12, 7.5), (8.5, 16, 8.5), "tubewarm", glow=180), bx("Holder", (7, 12, 7), (9, 12.8, 9), "silver")],
         box=(0.03, 0, 0.03, 0.97, 0.78, 0.97), oriented=False, light=[6, 5, 7])
    prop("grandpiano", "Grand Piano", [
        bx("Body", (0, 9, 1), (16, 13, 22), "pianoblack"), bx("Tail", (2, 9, 22), (13, 13, 28), "pianoblack"),
        bx("Lid", (0, 13, 4), (16, 13.6, 22), "pianoblack", rot=(-25, 0, 0), origin=(8, 13, 22)),
        bx("Prop", (13, 13, 8), (13.6, 21, 8.6), "pianoblack"),
        bx("Keys", (0, 10, -3), (16, 12, 1), "pianokeys", faces=("up",), uv=[0, 0, 16, 8]),
        bx("KeySides", (0, 10, -3), (16, 12, 1), "pianoblack", faces=("north", "east", "west", "down")),
        bx("Fallboard", (0, 12, 0), (16, 15, 1), "pianoblack"),
        bx("LegA", (1, 0, -1), (3, 9, 1), "pianoblack"), bx("LegB", (13, 0, -1), (15, 9, 1), "pianoblack"),
        bx("LegC", (6, 0, 24), (8, 9, 26), "pianoblack"), bx("Pedals", (6, 0, 0), (10, 2, 2), "brass"),
        bx("Bench", (3, 4, -10), (13, 7, -5), "velvet"), bx("BenchLegs", (3.5, 0, -9.5), (12.5, 4, -5.5), "pianoblack")],
         box=(0, 0, 0, 1, 0.85, 1), material="Wood", sounds=WOOD)
    prop("coalpile", "Coal", [
        bx("Heap1", (1, 0, 1), (15, 3, 15), "coal"), bx("Heap2", (3, 3, 3), (13, 6, 12), "coal"), bx("Heap3", (5, 6, 5), (10, 8, 10), "coal"),
        bx("Handle", (11, 4, 10), (12, 16, 11), "wood", rot=(0, 0, 15), origin=(11.5, 4, 10.5)),
        bx("Blade", (10, 2, 9.5), (13, 6, 10.1), "metaldark")], box=(0.06, 0, 0.06, 0.94, 0.5, 0.94), oriented=False, sounds=STONE)


def merge_lang():
    """Adds the names to lang/en.json without disturbing its hand-written layout: existing keys are updated in
    place, new ones appended at the end."""
    import re
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
    json.loads(text)  # still valid


def write_decor_table():
    """Writes the wall decorations as a C# table, so the generator always matches the blocks made here."""
    rows = []
    for family, decors in MANIFEST.items():
        for decor, rels in decors.items():
            for rel, state in rels.items():
                rows.append(f'        ("{family}", "{decor}", {rel}, "{state}"),')
    text = NL.join([
        "// <auto-generated>Written by tools/gen_detail.py; do not edit.</auto-generated>",
        "namespace Backrooms.Worldgen;",
        "",
        "internal static class DetailBlocks",
        "{",
        "    /// <summary>Every wall decoration block: its family (one per wall material), decoration, height above the floor and variant.</summary>",
        "    public static readonly (string Family, string Decor, int Rel, string State)[] Decorations =",
        "    {",
    ] + rows + ["    };", "}", ""])
    with open(os.path.join(os.path.dirname(__file__), "..", "src", "Worldgen", "DetailBlocks.g.cs"), "w", encoding="utf-8", newline=NL) as f:
        f.write(text)


TAB, NL = "\t", "\n"


if __name__ == "__main__":
    detail_textures.generate()
    exit_signs()
    doors()
    level1()
    level3()
    level4()
    level5()
    import gen_deep
    gen_deep.generate()
    import gen_city
    gen_city.generate()
    import gen_lore
    gen_lore.generate()
    import gen_pool
    gen_pool.generate()
    import gen_motion
    gen_motion.generate()
    import gen_guide
    gen_guide.fill()
    merge_lang()
    write_decor_table()
    import salvage
    salvage.apply()
    print(f"detail written: {len(LANG)} names")
