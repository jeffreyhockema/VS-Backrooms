"""Level 36, "Airport" (experimental): its surfaces, lights, windows, signs and screens, as block types, shapes and
textures (the props are gen_36_props.py's, the sounds another script's).

    l36-marble-{kind}                 white | grey | dark: polished marble floor tile, one tile a block; cube
    l36-carpet-{kind}                 blue | teal | red | grey: commercial carpet; cube
    l36-belt-{state}-{dir}            run | still, n|e|s|w: a baggage carousel's slat tread, a floor block topped at 15
                                      px (as l3999-walkway); run carries (l3999walkway speed 0.9) and clanks
    l36-carousel-{part}               island (the low stainless island) | flap-<side> (a wall cube whose <side> face is
                                      the belt's opening: a frame round a rubber-strip curtain); JSON
    l36-static-{kind}                 a..d: the Absolute Limit's TV static, glowing; cube
    l36-wall-{kind}                   plaster | panel | kick | tile | service | purple | column | stainless; cube
    l36-window-{row}-{side}           low | mid | horizon | sky: the painted runway view (plaster on the other faces),
                                      lit; a full JSON cube whose <side> face glows
    l36-cabinwall-{part}-{side}       plain | window | bin: the plane cabin's moulded walls; cube (window: JSON, glowing)
    l36-wallclock-{kind}-{side}       nohands | stopped: a panel wall with a station clock on its <side> face; cube
    l36-ceiling-{kind}                steel | tile | dark | cabin; cube
    l36-light-{state}                 on | lit | flicker | off: a diffuser panel in the steel ceiling (as l31-tube)
    l36-gatesign-{glyph}-{side}       a..z, 1..60: a hanging box sign, the glyph on both faces; hangs from the TOP of
                                      its block; no collision
    l36-sign-{glyph}-{side}           pictogram signs (same box): gatesl gatesr baggage exit meeting dutyfree food
                                      lounge toilets security checkin blank broken
    l36-shopsign-{shop}-{part}-{side} a three-block backlit shop fascia (l | m | r left to right as seen facing it)
    l36-fids-{text}-{half}-{side}     a two-block flight information screen (a..d boards, gate, c32), against the
                                      back of its block; no collision
    l36-fidspole                      a thin stainless pole through the block; no collision

Every oriented one is modelled facing north and turned as Level 3999's blocks are (east 270, south 180, west 90).
Run (from the repo root, under the asset lock):  bash tools/locked.sh run python tools/gen_36_surfaces.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from modelkit import box  # noqa: E402
import gen_36_surfaces_tex as T  # noqa: E402
import gen_36_surfaces_signs as G  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
SHAPES = os.path.join(ASSETS, "shapes", "block", "36")
BLOCKS = os.path.join(ASSETS, "blocktypes", "36")
SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90, "n": 0, "e": 270, "s": 180, "w": 90}

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe",
         "hit": "game:block/rock-hit-pickaxe"}
CLOTH = {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
GLASS = {"walk": "game:walk/stone", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit",
         "hit": "game:block/heavymetal-hit"}
INV = {"general": ["*"], "backrooms": ["*"]}
STRUCT = {"l36structure": True}

NAMES = {
    "block-l36-marble-white": "White Marble Tile",
    "block-l36-marble-grey": "Grey Marble Border",
    "block-l36-marble-dark": "Charcoal Marble Inlay",
    "block-l36-marble-*": "Marble Tile",
    "block-l36-carpet-blue": "Concourse Carpet",
    "block-l36-carpet-teal": "Gate Lounge Carpet",
    "block-l36-carpet-red": "First-Class Carpet",
    "block-l36-carpet-grey": "Office Carpet",
    "block-l36-carpet-*": "Airport Carpet",
    "block-l36-belt-run-*": "Baggage Belt",
    "block-l36-belt-still-*": "Stopped Baggage Belt",
    "block-l36-belt-*": "Baggage Belt",
    "block-l36-carousel-island": "Carousel Island",
    "block-l36-carousel-*": "Carousel Flap Opening",
    "block-l36-static-*": "The Absolute Limit",
    "block-l36-wall-plaster": "Terminal Plaster",
    "block-l36-wall-panel": "Terminal Wall Panel",
    "block-l36-wall-kick": "Terminal Kick Plate",
    "block-l36-wall-tile": "Restroom Tile",
    "block-l36-wall-service": "Painted Block Wall",
    "block-l36-wall-purple": "Travel Agency Panel",
    "block-l36-wall-column": "Column Cladding",
    "block-l36-wall-stainless": "Stainless Sheet",
    "block-l36-wall-*": "Terminal Wall",
    "block-l36-window-*": "Runway Window",
    "block-l36-cabinwall-plain-*": "Cabin Wall",
    "block-l36-cabinwall-window-*": "Cabin Window",
    "block-l36-cabinwall-bin-*": "Overhead Bin",
    "block-l36-cabinwall-*": "Cabin Wall",
    "block-l36-wallclock-nohands-*": "Clock With No Hands",
    "block-l36-wallclock-stopped-*": "Stopped Clock",
    "block-l36-wallclock-*": "Station Clock",
    "block-l36-ceiling-steel": "Metal Baffle Ceiling",
    "block-l36-ceiling-tile": "Acoustic Ceiling Tile",
    "block-l36-ceiling-dark": "Open Service Ceiling",
    "block-l36-ceiling-cabin": "Cabin Ceiling",
    "block-l36-ceiling-*": "Terminal Ceiling",
    "block-l36-light-*": "Terminal Ceiling Light",
    "block-l36-gatesign-*": "Gate Sign",
    "block-l36-sign-blank-*": "Blank Sign",
    "block-l36-sign-broken-*": "Broken Sign",
    "block-l36-sign-exit-*": "Exit Sign",
    "block-l36-sign-*": "Wayfinding Sign",
    "block-l36-shopsign-*": "Shop Fascia",
    "block-l36-fids-*": "Flight Information Display",
    "block-l36-fidspole": "Display Pole",
}


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def tex(name):
    return {"base": "backrooms:block/36/" + name}


def shape(name, elements, defaults=None):
    """Writes shapes/block/36/<name>.json; its texture keys show DEFAULT_TEX (or `defaults`) unless the block type
    overrides them."""
    keys = sorted({f["texture"][1:] for e in elements for f in e["faces"].values()})
    dt = dict(DEFAULT_TEX, **(defaults or {}))
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: "backrooms:block/36/" + dt.get(k, k) for k in keys},
            "elements": elements}
    write_json(os.path.join(SHAPES, name + ".json"), data)
    return "backrooms:block/36/" + name


# The shapes name their texture keys by role; these are what a shape shows unless its block type says otherwise
DEFAULT_TEX = {"front": "l36-window-mid", "side": "l36-wall-plaster", "signfront": "l36-gatesign-a",
               "signback": "l36-gatesign-a", "case": "l36-sign-case", "rod": "l36-sign-rod", "screen": "l36-fids-a-l",
               "bezel": "l36-fids-bezel", "pole": "l36-fidspole", "tread": "l36-belt-tread", "beltside": "l36-belt-side",
               "top": "l36-carousel-top", "islandside": "l36-carousel-side", "frame": "l36-carousel-frame",
               "curtain": "l36-carousel-curtain", "dark": "l36-carousel-dark", "panel": "l36-wall-panel"}


def cuboid(b, angle=0):
    x1, y1, z1, x2, y2, z2 = b
    out = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if angle:
        out["rotateY"] = angle
    return out


def by_side(prefix, fn):
    """{prefix-<side>: fn(side)} for the four sides (prefix ends in a wildcard)."""
    return {f"{prefix}-{s}": fn(s) for s in SIDES}


def rotated_shapes(prefix, base):
    return by_side(prefix, lambda s: {"base": base, "rotateY": ROT[s]} if ROT[s] else {"base": base})


def rotated_boxes(prefix, b):
    return by_side(prefix, lambda s: cuboid(b, ROT[s]))


def block(code, comment, data):
    data = dict({"code": code}, **data)
    data.setdefault("creativeinventory", INV)
    data.setdefault("drops", [])
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def cube(code, groups, textures, comment, material="Stone", sounds=STONE, extra=None, by_type=False):
    data = {"variantgroups": groups, ("texturesByType" if by_type else "textures"): textures,
            "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "sounds": sounds,
            "attributes": dict(STRUCT)}
    data.update(extra or {})
    block(code, comment, data)


# ======================================================================== Shapes

def faced_cube(name, glow, front, side):
    """A full cube whose north face is the key `front` (glowing) and whose other faces are `side`."""
    el = box("Cube", (0, 0, 0), (16, 16, 16), {"front": "front", "all": "side"})
    if glow:
        el["faces"]["north"]["glow"] = glow
    return shape(name, [el], {"front": front, "side": side})


def sign_shape(name, glow):
    """The hanging box sign, facing north: a charcoal box filling the block's width, 10 units tall and 4 deep, hung
    from the top of the block by two short rods; both broad faces lettered."""
    body = box("Box", (0, 4, 6), (16, 14, 10), {"front": "signfront", "back": "signback", "all": "case"})
    if glow:
        body["faces"]["north"]["glow"] = glow
        body["faces"]["south"]["glow"] = glow
    # (round 3) the whole picture on each broad face: the box is 10 units tall, its texture 16 x 10 units' worth, so map all
    # of it (the default 0-10 of 16 showed only the top five eighths: the lettering was cut off at the bottom)
    body["faces"]["north"]["uv"] = [0, 0, 16, 16]
    body["faces"]["south"]["uv"] = [0, 0, 16, 16]
    rods = [box("RodL", (3, 14, 7.5), (4, 16, 8.5), "rod", faces=("north", "east", "south", "west", "up")),
            box("RodR", (12, 14, 7.5), (13, 16, 8.5), "rod", faces=("north", "east", "south", "west", "up"))]
    return shape(name, [body] + rods)


def shapes():
    out = {}
    out["belt"] = shape("l36-belt", [box("Tread", (0, 0, 0), (16, 15, 16), {"top": "tread", "all": "beltside"})])
    out["island"] = shape("l36-carousel-island", [box("Island", (0, 0, 0), (16, 10, 16), {"top": "top", "all": "islandside"})])
    out["flap"] = shape("l36-carousel-flap", [
        box("Back", (0, 0, 3), (16, 16, 16), {"front": "dark", "all": "panel"}),
        box("Lintel", (0, 12, 0), (16, 16, 3), {"front": "frame", "bottom": "frame", "all": "panel"},
            faces=("north", "east", "west", "up", "down")),
        box("JambL", (0, 0, 0), (2, 12, 3), {"front": "frame", "all": "panel", "east": "frame"},
            faces=("north", "east", "west", "down")),
        box("JambR", (14, 0, 0), (16, 12, 3), {"front": "frame", "all": "panel", "west": "frame"},
            faces=("north", "east", "west", "down")),
        box("Floor", (2, 0, 0), (14, 0.5, 3), {"top": "tread", "all": "frame"}, faces=("north", "up", "down")),
        box("Curtain", (2, 1, 1.5), (14, 12, 2), "curtain", faces=("north", "south", "down")),
    ])
    out["window"] = faced_cube("l36-window", 70, "l36-window-mid", "l36-wall-plaster")
    out["shopsign"] = faced_cube("l36-shopsign", 140, "l36-shopsign-cafe-m", "l36-wall-panel")
    out["cabinglow"] = faced_cube("l36-cabinwall-window", 60, "l36-cabinwall-window", "l36-cabin-plastic")
    out["sign"] = sign_shape("l36-sign", 150)
    out["signdead"] = sign_shape("l36-sign-unlit", 0)
    screen = box("Screen", (0, 2, 14), (16, 14, 16), {"front": "screen", "all": "bezel"},
                 faces=("north", "east", "west", "up", "down", "south"))
    screen["faces"]["north"]["glow"] = 170
    screen["faces"]["north"]["uv"] = [0, 0, 16, 16]   # (round 3) the whole screen picture, as the signs
    out["fids"] = shape("l36-fids", [screen])
    out["pole"] = shape("l36-fidspole", [box("Pole", (7, 0, 7), (9, 16, 9), "pole")])
    return out


# ======================================================================== Block types

def blocktypes(sh):
    cube("l36-marble", [{"code": "kind", "states": ["white", "grey", "dark"]}],
         {"all": tex("l36-marble-{kind}")},
         "Level 36: polished marble floor tile, one tile a block (white; grey for borders; dark for the charcoal inlay)")
    cube("l36-carpet", [{"code": "kind", "states": ["blue", "teal", "red", "grey"]}],
         {"all": tex("l36-carpet-{kind}")},
         "Level 36: commercial airport carpet (blue: the concourses' navy; teal: gate seating; red: the first-class lounge; grey: back offices)",
         material="Cloth", sounds=CLOTH)

    # The baggage belt: a floor block topped at 15 px, as l3999-walkway; run carries whoever stands on it
    belt_box = cuboid((0, 0, 0, 1, 0.9375, 1))
    block("l36-belt", "Level 36: a baggage carousel's tread, overlapping slat plates between steel edges, a floor block topped at "
          "15 px (dir: the way it carries, n = toward -z); run carries whoever stands on it and clanks, still does not",
          {"variantgroups": [{"code": "state", "states": ["run", "still"]}, {"code": "dir", "states": ["n", "e", "s", "w"]}],
           "shapeByType": {f"*-{d}": ({"base": sh["belt"], "rotateY": ROT[d]} if ROT[d] else {"base": sh["belt"]})
                           for d in ("n", "e", "s", "w")},
           "creativeinventory": {"general": ["l36-belt-run-n", "l36-belt-still-n"], "backrooms": ["l36-belt-run-n", "l36-belt-still-n"]},
           "blockmaterial": "Metal", "drawtype": "json",
           "sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True},
           "lightAbsorption": 99, "resistance": 2,
           "soundsByType": {"*-run-*": dict(METAL, ambient="backrooms:ambient/36/belt", ambientBlockCount=48), "*": METAL},
           "selectionbox": belt_box, "collisionbox": belt_box,
           "attributesByType": {"*-run-*": {"l36structure": True, "l3999walkway": {"speed": 0.9}}, "*": dict(STRUCT)}})

    parts = ["island"] + [f"flap-{s}" for s in SIDES]
    island_box = cuboid((0, 0, 0, 1, 0.625, 1))
    shapes_ = {"*-island": {"base": sh["island"]}}
    solid, opaque = {"*-island": {"all": False, "down": True}}, {"*-island": {"all": False, "down": True}}
    for s in SIDES:
        shapes_[f"*-flap-{s}"] = {"base": sh["flap"], "rotateY": ROT[s]} if ROT[s] else {"base": sh["flap"]}
        solid[f"*-flap-{s}"] = {"all": True, s: False}
        opaque[f"*-flap-{s}"] = {"all": True, s: False}
    block("l36-carousel", "Level 36: a baggage carousel's parts: island (the low stainless island in the loop's middle) and "
          "flap-<side> (a wall cube whose <side> face is the opening where the belt runs into the wall: a stainless frame, "
          "a curtain of rubber strips, the slats just showing under it)",
          {"variantgroups": [{"code": "part", "states": parts}], "shapeByType": shapes_,
           "blockmaterial": "Metal", "drawtype": "json", "sidesolidByType": solid, "sideopaqueByType": opaque,
           "lightAbsorption": 99, "resistance": 6, "sounds": METAL,
           "selectionboxByType": {"*-island": island_box, "*": cuboid((0, 0, 0, 1, 1, 1))},
           "collisionboxByType": {"*-island": island_box, "*": cuboid((0, 0, 0, 1, 1, 1))},
           "attributes": dict(STRUCT)})

    cube("l36-static", [{"code": "kind", "states": ["a", "b", "c", "d"]}], {"all": tex("l36-static-{kind}")},
         "Level 36: the Absolute Limit, where the terminal dissolves into bright TV static (four tilings, so a wall of it "
         "does not repeat); glows a little", material="Glass", sounds=GLASS,
         extra={"lightHsv": [0, 0, 5], "vertexFlags": {"glowLevel": 120}, "lightAbsorption": 0})

    wall_kinds = ["plaster", "panel", "kick", "tile", "service", "purple", "column", "stainless"]
    wt = {}
    for k in wall_kinds:
        if k == "kick":
            wt["*-kick"] = {"all": tex("l36-wall-kick"), "up": tex("l36-wall-panel"), "down": tex("l36-wall-panel")}
        else:
            wt[f"*-{k}"] = {"all": tex("l36-wall-" + k)}
    cube("l36-wall", [{"code": "kind", "states": wall_kinds}], wt,
         "Level 36: the terminal's walls (plaster; panel: the main composite cladding; kick: a panel wall's bottom block "
         "with a steel kick plate; tile: restrooms; service: painted block, back of house; purple: the Backrooms Travel "
         "Agency's gloss panel; column: white column cladding; stainless: brushed steel sheet)",
         by_type=True, extra={"soundsByType": {"*-stainless": METAL, "*": STONE}})

    # The runway windows: a full cube whose <side> face is the painted view, glowing like daylight
    rows = ["low", "mid", "horizon", "sky"]
    block("l36-window", "Level 36: the runway view through unbreakable glass, painted: a wall cube (plaster on the other faces) "
          "whose <side> face is the glazing; rows stack bottom to top (low: the sill and the apron's taxi line; mid: the "
          "taxiway's blue edge lights; horizon: the runway lights and green-grey hills in fog; sky: overcast, repeat it "
          "upward) and each tiles left-right",
          {"variantgroups": [{"code": "row", "states": rows}, {"code": "side", "states": SIDES}],
           "shapeByType": rotated_shapes("*", sh["window"]),
           "texturesByType": {f"*-{r}-*": {"front": tex("l36-window-" + r), "side": tex("l36-wall-plaster")} for r in rows},
           "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
           "blockmaterial": "Glass", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
           "lightHsv": [20, 1, 7], "lightAbsorption": 0, "resistance": 6, "sounds": GLASS, "attributes": dict(STRUCT)})

    # The plane cabin's walls
    ct = {}
    for part in ("plain", "bin"):
        for s in SIDES:
            ct[f"*-{part}-{s}"] = {"all": tex("l36-cabin-plastic"), s: tex("l36-cabinwall-" + part)}
    ct["*-window-*"] = {"front": tex("l36-cabinwall-window"), "side": tex("l36-cabin-plastic")}
    block("l36-cabinwall", "Level 36: the plane cabin of a 'flight' (Sublevel 36.1): off-white moulded plastic, the <side> face "
          "a side panel (plain), an oval porthole onto cloud tops (window, glowing a little) or an overhead bin door (bin)",
          {"variantgroups": [{"code": "part", "states": ["plain", "window", "bin"]}, {"code": "side", "states": SIDES}],
           "drawtypeByType": {"*-window-*": "json", "*": "cube"},
           "shapeByType": rotated_shapes("*-window", sh["cabinglow"]),
           "texturesByType": ct,
           "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
           "blockmaterial": "Stone", "sidesolid": {"all": True}, "sideopaque": {"all": True},
           "lightAbsorption": 99, "resistance": 3, "sounds": STONE, "attributes": dict(STRUCT)})

    kt = {}
    for k in ("nohands", "stopped"):
        for s in SIDES:
            kt[f"*-{k}-{s}"] = {"all": tex("l36-wall-panel"), s: tex("l36-wallclock-" + k)}
    cube("l36-wallclock", [{"code": "kind", "states": ["nohands", "stopped"]}, {"code": "side", "states": SIDES}], kt,
         "Level 36: a panel wall with a round station clock on its <side> face: no hands at all, or stopped at 3:47 "
         "under cracked glass (clocks here freeze)", by_type=True,
         extra={"creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}})

    cube("l36-ceiling", [{"code": "kind", "states": ["steel", "tile", "dark", "cabin"]}], {"all": tex("l36-ceiling-{kind}")},
         "Level 36: ceilings (steel: the concourses' linear metal baffles; tile: offices and restrooms; dark: the open black "
         "ceiling of the service areas; cabin: the plane's, with reading lights and air nozzles)", material="Metal",
         sounds=METAL)

    # The ceiling lights, as l31-tube does its states
    states = ["on", "lit", "flicker", "off", "high"]
    side = tex("l36-light-side")
    block("l36-light", "Level 36: a square fluorescent diffuser panel flush in the steel ceiling (on: gives light; lit: looks "
          "on, gives none; flicker: a failing one; off: dead; high: as on, brighter, for the halls seven blocks high and more)",
          {"variantgroups": [{"code": "state", "states": states}],
           "texturesByType": {"*-off": {"all": side, "down": tex("l36-light-off")}, "*": {"all": side, "down": tex("l36-light-on")}},
           "blockmaterial": "Glass", "drawtype": "cube",
           # (round 2: brighter, and the tall halls' own brighter panel, so their light falls evenly, without dark wedges)
           "lightHsvByType": {"*-on": [8, 1, 18], "*-high": [8, 1, 20]},
           "vertexFlagsByType": {f"*-{st}": {"glowLevel": 160} for st in ("on", "lit", "flicker", "high")},
           "entityClassByType": {"*-flicker": "BackroomsFlicker"},
           "attributesByType": {"*-flicker": {"offBlock": "backrooms:l36-light-off"}},
           # Must be 0: a light source subtracts its own absorption before spreading
           "lightAbsorption": 0, "resistance": 0.8,
           "soundsByType": {**{f"*-{st}": dict(GLASS, ambient="backrooms:ambient/hum", ambientBlockCount=140) for st in ("on", "high")}, "*": GLASS}})

    # Hanging box signs
    sign_sel = (0, 0.25, 0.375, 1, 1, 0.625)
    common_sign = {"blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                   "lightAbsorption": 0, "resistance": 1.5, "sounds": METAL, "collisionbox": None}
    block("l36-gatesign", "Level 36: a hanging wayfinding box sign with a gate letter or number in airport yellow on charcoal "
          "on both broad faces; it hangs from the TOP of its block (place it just under the ceiling); no collision",
          dict(common_sign, **{
              "variantgroups": [{"code": "glyph", "states": G.GATE_GLYPHS}, {"code": "side", "states": SIDES}],
              "shapeByType": rotated_shapes("*", sh["sign"]),
              "texturesByType": {f"l36-gatesign-{g}-*": {"signfront": tex("l36-gatesign-" + g), "signback": tex("l36-gatesign-" + g)}
                                 for g in G.GATE_GLYPHS},
              "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
              "lightHsv": [8, 4, 6],
              "selectionboxByType": rotated_boxes("*", sign_sel)}))

    st = {}
    for g in G.SIGN_GLYPHS:
        back = G.SIGN_BACK.get(g, g)   # an arrow points the same way seen from behind (a wide sign's parts the other way round)
        st[f"l36-sign-{g}-*"] = {"signfront": tex("l36-sign-" + g), "signback": tex("l36-sign-" + back)}
    shp = {}
    for s in SIDES:
        shp[f"*-broken-{s}"] = {"base": sh["signdead"], "rotateY": ROT[s]} if ROT[s] else {"base": sh["signdead"]}
    shp.update(rotated_shapes("*", sh["sign"]))
    block("l36-sign", "Level 36: a hanging wayfinding box sign with a pictogram and a word (gates left/right, baggage, exit, "
          "meeting point, duty free, food, lounge, toilets, security, check-in), a lit sign with nothing on it (blank: "
          "no good) or a cracked dead one (broken); hangs from the TOP of its block; no collision. The gates arrows "
          "show the mirrored arrow on the back face, so both sides point the same way",
          dict(common_sign, **{
              "variantgroups": [{"code": "glyph", "states": G.SIGN_GLYPHS}, {"code": "side", "states": SIDES}],
              "shapeByType": shp, "texturesByType": st,
              "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
              "lightHsvByType": {"*-exit-*": [20, 5, 6], "*-wexit-*": [20, 5, 6], "*-info-*": [8, 5, 6], "*-blank-*": [8, 2, 6], "*-broken-*": [0, 0, 0], "*": [8, 4, 6]},
              "selectionboxByType": rotated_boxes("*", sign_sel)}))

    # Shop fascias
    ft = {}
    for shop in G.SHOPS:
        for part in "lmr":
            ft[f"l36-shopsign-{shop}-{part}-*"] = {"front": tex(f"l36-shopsign-{shop}-{part}"), "side": tex("l36-wall-panel")}
    block("l36-shopsign", "Level 36: a backlit shop fascia three blocks wide over a duty-free shop (part l, m, r: left to right "
          "as seen facing it), on a panel wall cube; invented brands",
          {"variantgroups": [{"code": "shop", "states": G.SHOPS}, {"code": "part", "states": ["l", "m", "r"]},
                             {"code": "side", "states": SIDES}],
           "shapeByType": rotated_shapes("*", sh["shopsign"]), "texturesByType": ft,
           "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
           "blockmaterial": "Stone", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True},
           "lightHsvByType": {f"l36-shopsign-{shop}-*": G.FASCIA_LIGHT[shop] for shop in G.SHOPS},
           "lightAbsorption": 0, "resistance": 6, "sounds": STONE, "attributes": dict(STRUCT)})

    # Flight information displays
    fx = {}
    for t in G.FIDS_TEXTS:
        for half in "lr":
            fx[f"l36-fids-{t}-{half}-*"] = {"screen": tex(f"l36-fids-{t}-{half}")}
    block("l36-fids", "Level 36: a flight information display two blocks wide (half l, r: left to right as seen facing it), "
          "12 px tall, its back flush with the block face opposite <side> so two hang back to back; departures boards a..d, "
          "Gate C32's, and a gate's screen for each level the gates' flights go to (to<level>); no collision",
          {"variantgroups": [{"code": "text", "states": G.FIDS_TEXTS}, {"code": "half", "states": ["l", "r"]},
                             {"code": "side", "states": SIDES}],
           "shapeByType": rotated_shapes("*", sh["fids"]), "texturesByType": fx,
           "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
           "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
           "lightHsv": [6, 3, 6], "lightAbsorption": 0, "resistance": 1.5, "sounds": METAL, "collisionbox": None,
           "selectionboxByType": rotated_boxes("*", (0, 0.125, 0.875, 1, 0.875, 1))})

    block("l36-fidspole", "Level 36: a thin stainless pole through the block, to hang screens and signs from the ceiling or stand "
          "a screen on the floor; no collision",
          {"shape": {"base": sh["pole"]}, "blockmaterial": "Metal", "drawtype": "json",
           "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1.5,
           "sounds": METAL, "collisionbox": None, "selectionbox": cuboid((0.375, 0, 0.375, 0.625, 1, 0.625))})


def main():
    T.generate()
    G.generate()
    sh = shapes()
    blocktypes(sh)
    print(f"Level 36 surfaces: {len(T.WRITTEN)} textures, block types in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
