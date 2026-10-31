"""Level 5's boiler plant (layout version 9): the pieces that connect a boiler bay's boilers and furnaces to each other.

Run from the repo root:  python tools/gen_plant.py

Along the back wall of a boiler bay stand a boiler and a furnace, both facing the aisle (WorldLayout.Level5.cs,
PlaceBoilerPlant). Over the row runs one header the length of the hall in the top block of the room: a flue duct, with
a steam main beside it on the wall side, hung from the ceiling and passing through the bay walls. The boiler's flue
and a steam pipe off its dome, and the furnace's flue, rise to it through the two blocks above them. Blocks, all in
blocktypes/level5:

    plantheader-<kind>-<end>-<side>   the header's top-block piece. kind: run (plain), flue (a furnace's flue rises into
                                      it), both (a boiler's flue and steam pipe rise into it); end: mid, west or east
                                      (the header ends against the wall on that side, with a blind flange); side:
                                      north or south, the side the steam main is on (the wall side of the bay).
    plantriser-<part>-<side>          the columns over a boiler or furnace, modelled like them (facing the aisle).
                                      furnace2: the furnace's flue off its hood (the block over it); steam2: the steam
                                      pipe off the boiler's dome (the block over it; the boiler's own flue stands in
                                      the same block, drawn by the boiler); both3 and flue3: the block above that.
    plantthru                         the plaster of a bay wall in the top block, with the header's flanges on its faces
    coalbin                           a wooden coal bin, for in front of a furnace
"""
import os

import gen_blocktypes as B
import gen_shapes as G
import modelkit as K

TEX = {
    "flue": "backrooms:block/level5/boiler-flue", "band": "backrooms:block/level5/boiler-band",
    "steam": G.WALL_PIPE_TEX["wallrust"], "lag": G.WALL_PIPE_TEX["walllag"], "flange": G.WALL_PIPE_TEX["flange"],
    "metal": "backrooms:block/props/metal", "plaster": "backrooms:block/level5/plaster",
    "wood": "backrooms:block/level5/mahogany", "coal": "backrooms:block/detail/coal", "dark": "backrooms:block/props/metal-dark",
}
ALL4 = ("north", "east", "south", "west")

# Model space is that of the boiler and furnace facing north (the front plate at low z). The boiler's flue and the
# furnace's flue stand at (8, 9); the steam pipe off the boiler's dome at (4, 13), 8.6 up in the block over the boiler.
FLUE_X, FLUE_Z = 8.0, 9.0
STEAM_X, STEAM_Z = 4.0, 13.0
DUCT = dict(yc=10.0, zc=8.0, r=3.5)  # the flue duct in the header block, round about z 8
MAIN_Y, MAIN_R = 11.5, 1.4           # the steam main's height and radius


def turned(x, z, north_bay):
    """A point of the north-facing model as it stands under a boiler facing the aisle: a north bay's boilers face
    south (turned half way round), a south bay's face north."""
    return (16 - x, 16 - z) if north_bay else (x, z)


def ring(name, cx, cz, a, y1, y2, tex="band"):
    return G.octagon(name, cx, cz, a, y1, y2, tex, faces=ALL4 + ("up", "down"), lift=0.01)


def riser(name, cx, cz, a, y1, y2, tex, collar_foot=False, collar_head=True):
    """An upright pipe with a flange ring at its head (and its foot): the joint where two blocks meet."""
    els = G.octagon(name, cx, cz, a, y1, y2, tex)
    if collar_head:
        els += ring(name + "Head", cx, cz, a + 0.6, y2 - 0.8, y2)
    if collar_foot:
        els += ring(name + "Foot", cx, cz, a + 0.6, y1, y1 + 0.8)
    return els


def plant_riser(part):
    """The columns over a boiler or furnace (model facing north)."""
    if part == "furnace2":    # the furnace's flue off its hood, which is flush with the top of the block below
        return riser("Flue", FLUE_X, FLUE_Z, 1.9, 0, 16, "flue", collar_foot=True)
    if part == "flue3":       # and on up
        return riser("Flue", FLUE_X, FLUE_Z, 1.9, 0, 16, "flue", collar_foot=True)
    if part == "steam2":      # off the dome (the boiler's crown tops out 9 up here, its dome 10), the boiler's own flue stands in this block
        return riser("Steam", STEAM_X, STEAM_Z, 0.9, 8.6, 16, "steam")
    if part == "both3":
        return riser("Flue", FLUE_X, FLUE_Z, 1.9, 0, 16, "flue", collar_foot=True) + riser("Steam", STEAM_X, STEAM_Z, 0.9, 0, 16, "steam", collar_foot=True)
    raise ValueError(part)


def header(kind, end, north_bay):
    """The header in the top block of the room: flue duct and steam main along X, hung from the ceiling, with a flange
    ring half way and the risers coming up into it from below. `end` closes it with a blind flange against the wall."""
    d = DUCT
    sz = 16 - STEAM_Z if north_bay else STEAM_Z       # the steam main on the wall side
    sx = 16 - STEAM_X if north_bay else STEAM_X
    fz = 16 - FLUE_Z if north_bay else FLUE_Z
    els = G.round_pipe("Duct", d["yc"], d["zc"], d["r"], "flue", 0, 16, shaded=False, faces=("south",))
    els += G.round_pipe("DuctJoint", d["yc"], d["zc"], d["r"] + 0.6, "flange", 7.2, 8.8, shaded=False, faces=("south", "east", "west"))
    els += G.round_pipe("Main", MAIN_Y, sz, MAIN_R, "lag", 0, 16, shaded=False, faces=("south",))
    els += G.round_pipe("MainJoint", MAIN_Y, sz, MAIN_R + 0.5, "flange", 7.2, 8.8, shaded=False, faces=("south", "east", "west"))
    els += [K.box("Hanger", (7.5, d["yc"] + d["r"] + 0.5, d["zc"] - 0.5), (8.5, 16, d["zc"] + 0.5), "metal", faces=ALL4),
            K.box("MainHanger", (11.5, MAIN_Y + MAIN_R, sz - 0.5), (12.5, 16, sz + 0.5), "metal", faces=ALL4)]
    if kind in ("flue", "both"):
        els += riser("FlueStub", 8, fz, 1.9, 0, 8.0, "flue", collar_foot=True, collar_head=False)
    if kind == "both":
        els += riser("SteamStub", sx, sz, 0.9, 0, 11.0, "steam", collar_foot=True, collar_head=False)
    if end:
        x1, x2 = (0.0, 0.8) if end == "west" else (15.2, 16.0)
        els += G.round_pipe("DuctEnd", d["yc"], d["zc"], d["r"] + 0.7, "flange", x1, x2, shaded=False, faces=("south", "east", "west"))
        els += G.round_pipe("MainEnd", MAIN_Y, sz, MAIN_R + 0.6, "flange", x1, x2, shaded=False, faces=("south", "east", "west"))
    return els


def through(north_bay):
    """A bay wall's plaster in the top block, the duct and the main passing through it with a flange on each face (the
    main at its own height on the wall side of its bay)."""
    d = DUCT
    sz = 16 - STEAM_Z if north_bay else STEAM_Z
    els = [K.box("Wall", (0, 0, 0), (16, 16, 16), "plaster")]
    for name, yc, zc, r in (("Main", MAIN_Y, sz, MAIN_R + 0.5), ("Duct", d["yc"], d["zc"], d["r"] + 0.6)):
        els += G.round_pipe(name, yc, zc, r, "flange", -0.6, 0, shaded=False, faces=("south", "east", "west"))
        els += G.round_pipe(name + "B", yc, zc, r, "flange", 16, 16.6, shaded=False, faces=("south", "east", "west"))
    return els


def coal_bin():
    """A wooden coal bin: corner posts, boards with gaps between them, the front board low so the heap shows over it,
    coal heaped inside and spilling over the front."""
    els = [K.box("Floor", (1, 0, 1), (15, 1, 15), "wood", faces=("up", "down", "north", "south", "east", "west"))]
    for i, (x, z) in enumerate(((0.5, 0.5), (13.5, 0.5), (0.5, 13.5), (13.5, 13.5))):
        els.append(K.box(f"Post{i}", (x, 0, z), (x + 2, 12, z + 2), "wood"))
    for k, (y1, y2) in enumerate(((1.5, 4), (5, 7.5), (8.5, 11))):
        top = k < 2  # the front is only two boards high
        els.append(K.box(f"Back{k}", (2.5, y1, 0.9), (13.5, y2, 1.7), "wood", faces=("north", "south", "up", "down")))
        els.append(K.box(f"West{k}", (0.9, y1, 2.5), (1.7, y2, 13.5), "wood", faces=("east", "west", "up", "down")))
        els.append(K.box(f"East{k}", (14.3, y1, 2.5), (15.1, y2, 13.5), "wood", faces=("east", "west", "up", "down")))
        if top:
            els.append(K.box(f"Front{k}", (2.5, y1, 14.3), (13.5, y2, 15.1), "wood", faces=("north", "south", "up", "down")))
    els += [K.box("CoalLow", (1.8, 1, 1.8), (14.2, 7, 14.2), "coal"),
            K.box("CoalMid", (2.5, 7, 2.5), (13.5, 10.5, 12.5), "coal"),
            K.box("CoalTop", (4.5, 10.5, 4.5), (11, 12.5, 10.5), "coal"),
            K.box("Spill", (3, 1, 15.1), (11.5, 3.2, 16), "coal", faces=("north", "east", "west", "up", "south"))]
    return els


def header_blocktype():
    kinds, ends, sides = ["run", "flue", "both"], ["mid", "west", "east"], ["north", "south"]
    shapes = {f"*-{k}-{e}-{s}": {"base": f"block/plantheader-{k}-{e}-{s}"} for k in kinds for e in ends for s in sides}
    B.write("level5", "plantheader", {
        "code": "plantheader",
        "variantgroups": [{"code": "kind", "states": kinds}, {"code": "end", "states": ends}, {"code": "side", "states": sides}],
        "creativeinventory": {"general": ["*-run-mid-north", "*-both-mid-north"], "decorative": ["*-run-mid-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shapes,
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0.35, "z1": 0.15, "x2": 1, "y2": 1, "z2": 0.85},
        "selectionbox": {"x1": 0, "y1": 0.35, "z1": 0.15, "x2": 1, "y2": 1, "z2": 0.85},
        "lightAbsorption": 0, "resistance": 3, "sounds": B.METAL,
        "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0}}],
    }, "The header over a boiler bay: a flue duct and a steam main hung from the ceiling, with the boilers' flues rising into it")


def riser_blocktype():
    parts = ["furnace2", "steam2", "both3", "flue3"]
    shapes = {f"*-{p}-{s}": {"base": f"block/plantriser-{p}", "rotateY": B.ROTATE[s]} for p in parts for s in B.SIDES}
    col = {"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7}
    B.write("level5", "plantriser", {
        "code": "plantriser",
        "variantgroups": [{"code": "part", "states": parts}, {"code": "side", "states": B.SIDES}],
        "creativeinventory": {"general": ["*-both3-north"], "decorative": ["*-both3-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shapes,
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": col, "selectionbox": col,
        "lightAbsorption": 0, "resistance": 3, "sounds": B.METAL,
        "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.3, "var": 0}}],
    }, "A flue and a steam pipe rising from a boiler or furnace to the header over the bay")


def main():
    for north_bay, side in ((True, "north"), (False, "south")):
        for kind in ("run", "flue", "both"):
            for end in ("mid", "west", "east"):
                G.save(f"plantheader-{kind}-{end}-{side}", TEX, header(kind, None if end == "mid" else end, north_bay))
    for part in ("furnace2", "steam2", "both3", "flue3"):
        G.save(f"plantriser-{part}", TEX, plant_riser(part))
    G.save("plantthru-north", TEX, through(True))
    G.save("plantthru-south", TEX, through(False))
    G.save("coalbin", TEX, coal_bin())
    header_blocktype()
    riser_blocktype()
    B.write("level5", "plantthru", {
        "code": "plantthru", "variantgroups": [{"code": "side", "states": ["north", "south"]}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {"*-north": {"base": "block/plantthru-north"}, "*-south": {"base": "block/plantthru-south"}},
        "resistance": 8, "lightAbsorption": 99, "sounds": B.STONE,
        "drops": [{"type": "item", "code": "chalk", "quantity": {"avg": 0.5, "var": 0.3}}],
    }, "A boiler bay's plaster wall in the top block, the header passing through it (north: the steam main on the north side)")
    B.write("level5", "coalbin", {
        "code": "coalbin", "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood", "drawtype": "json", "shape": {"base": "block/coalbin"},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2, "sounds": B.WOOD,
        "collisionbox": {"x1": 0.03, "y1": 0, "z1": 0.03, "x2": 0.97, "y2": 0.8, "z2": 0.97},
        "selectionbox": {"x1": 0.03, "y1": 0, "z1": 0.03, "x2": 0.97, "y2": 0.8, "z2": 0.97},
        "drops": [{"type": "item", "code": "game:ore-bituminouscoal", "quantity": {"avg": 3, "var": 1}},
                  {"type": "item", "code": "game:plank-aged", "quantity": {"avg": 1, "var": 0}}],
    }, "A wooden coal bin")
    merge_lang({"block-plantheader-*": "Boiler Header", "block-plantriser-*": "Flue", "block-plantthru-*": "Stained Plaster",
                "block-coalbin": "Coal Bin"})
    print("boiler plant written")


def merge_lang(names):
    """Appends the names to lang/en.json (existing lines are left alone, a name already there is updated in place)."""
    import json
    import re
    path = os.path.join(B.ROOT, "assets", "backrooms", "lang", "en.json")
    with open(path, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    new = []
    for key, value in names.items():
        line = "\t" + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^\t" + re.escape(json.dumps(key)) + r":.*?(,?)\r?$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new.append(line)
    if new:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + nl + nl + ("," + nl).join(new) + nl + "}" + nl
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    json.loads(text)


if __name__ == "__main__":
    main()
