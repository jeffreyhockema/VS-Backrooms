"""Level 3999, the Neon Paradise: the building (docs/design/new-levels/3999-plan.md 6.1, 6.2, 6.4, 6.5). Called from
gen_3999.py. Surfaces, neon tubes and signs, the lobby, food court, concourse and service fittings, the Level 10
windmills. The arcade machines are in gen_3999_arcade.py.

Every block here is part of the building (attribute l3999structure: never broken) unless its comment says salvage.
Variant suffixes: `facing` is the way the front faces (props modelled facing north); wall-mounted things sit against
the south side of their block and face north at `north`; rails and balustrades stand on the edge their suffix names.
"""
import math

from gen_3999_kit import (ROTATE, shape, ALL, CLOTH, COLOURS, FIXED, GLASS, LANG, METAL, NEON, SIDE4, SIDES, STONE, WOOD, block, bx,
                          cube_block, cube_el, cuboid, cyl, drops, faces_box, glass, hang, hsv, mirror_x, move, picture,
                          rot, text_boxes, bitmap_boxes, threshold, tpath, turn, variants_block, with_class, COUNT, F5, F3,
                          text_rows)

import gen_3999_b16 as B16  # noqa: E402  (graphics pass B16: versions and model parts)

B16_FURNITURE = True  # (B16) the food court's chairs, tables and booths modelled (False: B0's boxes)
B16_VENDING = True    # (B16) the vending machines' window an opening with shelves and packs (False: B0's painted rows)

OPEN = {"sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0}
HUM = "backrooms:ambient/3999/neonhum"


def tex(key):
    return tpath(key).replace("backrooms:", "")


# ======================================================================== 6.1 Surfaces

def surfaces():
    # Carpet: three looks, each turned four ways as alternates so the pattern never lines up. The galaxy carpet is also a
    # unit's gallery slab, so its sides and underside are plain dark paint (the stars would band the gallery's fascia)
    tex_by = {}
    for k in ("cosmic", "galaxy", "rotten"):
        base = tex(f"carpet-{k}")
        tex_by[f"l3999-carpet-{k}"] = {"all": {"base": base, "alternates": [{"base": base, "rotation": r} for r in (90, 180, 270)]}}
    tex_by["l3999-carpet-galaxy"] = dict({f: {"base": tex("wall-midnight")} for f in ("north", "east", "south", "west", "down")},
                                         up=tex_by["l3999-carpet-galaxy"]["all"])
    block("l3999-carpet", {
        "variantgroups": [{"code": "kind", "states": ["cosmic", "galaxy", "rotten"]}],
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "texturesByType": tex_by, "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": CLOTH, "attributes": dict(FIXED),
    }, "Level 3999: black-light carpet (cosmic: 90s neon squiggles on black; galaxy: stars and ringed planets; rotten: "
       "the cosmic carpet faded and damp, toward 3999.1). The floor over concrete")
    LANG.update({"block-l3999-carpet-cosmic": "Black-Light Carpet", "block-l3999-carpet-galaxy": "Galaxy Carpet",
                 "block-l3999-carpet-rotten": "Rotten Carpet"})
    COUNT["variants"] += 3
    # (B16) four versions of each, every tile a different piece of one slab; picked by x, y and z, since the black one is
    # also the lobby's storey line on the walls
    cube_block("l3999-marble", "Marble Floor", {"white": "marble-white", "black": "marble-black"},
               "Level 3999: polished marble tiles, 2 x 2 to a block (white with grey veins, black with white-gold veins)",
               names={"l3999-marble-white": "White Marble", "l3999-marble-black": "Black Marble"},
               alternates={"white": B16.versions("marble-white")[1:], "black": B16.versions("marble-black")[1:]},
               extra={"randomizeAxes": "xyz"})
    cube_block("l3999-concrete", "Concrete", {"wall": "concrete-wall", "floor": "concrete-floor"},
               "Level 3999: smooth concrete walls with form-tie holes; the polished floors of the service corridors",
               alternates={"wall": ["concrete-wall2", "concrete-wall3"]}, extra={"randomizeAxes": "xyz"})  # (D4) by height too
    cube_block("l3999-wall", "Painted Wall", {"violet": "wall-violet", "midnight": "wall-midnight", "teal": "wall-teal"},
               "Level 3999: matt painted plaster (violet, midnight, teal)",
               alternates={k: B16.versions(f"wall-{k}")[1:] for k in ("violet", "midnight", "teal")}, extra={"randomizeAxes": "xyz"})
    cube_block("l3999-ceiling", "Ceiling", {"black": "ceiling-black", "acoustic": "ceiling-acoustic"},
               "Level 3999: the open black ceiling over the public areas; the acoustic tile of the service corridors",
               names={"l3999-ceiling-black": "Open Ceiling", "l3999-ceiling-acoustic": "Acoustic Ceiling"})
    cube_block("l3999-lanewood", "Bowling Lane", {None: "lanewood"}, "Level 3999: bowling-lane maple, boards running one way, glossy",
               material="Wood", sounds=WOOD, alternates={None: ["lanewood2"]})
    cube_block("l3999-asphalt", "Asphalt", {"plain": "asphalt-plain", "line-ns": "asphalt-line-ns", "line-we": "asphalt-line-we", "line-end": "asphalt-line-end"},
               "Level 3999 (the Level 10 arcade's car park): dark asphalt with white bay lines (line-ns runs north-south; line-end "
               "ends a line at the block's middle, coming from the south)",
               extra={"texturesByType": {f"l3999-asphalt-{k}": dict({f: {"base": tex("asphalt-plain")} for f in ("north", "east", "south", "west", "down")},
                                                                up={"base": tex(f"asphalt-{k}")})
                                         for k in ("plain", "line-ns", "line-we", "line-end")}})
    cube_block("l3999-pooltile", "Pool Tile", {"violet": "pooltile-violet", "lilac": "pooltile-lilac",
                                               "edge": {"up": "white", "down": "pooltile-violet", "north": "pooltile-edge", "east": "pooltile-edge",
                                                        "south": "pooltile-edge", "west": "pooltile-edge"}},
               "Level 3999's Neon Natatorium: violet and lilac mosaic; edge: white bullnose coping with a dark LED groove", material="Ceramic",
               names={"l3999-pooltile-edge": "Pool Coping"})
    cube_block("l3999-facade", "Façade", {"stucco": "facade-stucco", "brick": "facade-brick", "band": "facade-band"},
               "Level 3999 (the Level 10 arcade building): tan stucco, a red-brown brick plinth, a dark fascia band")
    # Glass: storefront glass (clear) and the Level 10 arcade's dark windows
    block("l3999-glass", {
        "variantgroups": [{"code": "kind", "states": ["clear", "dark"]}],
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Glass", "drawtype": "cube",
        "texturesByType": {"l3999-glass-clear": {"all": {"base": tex("glass-clear")}}, "l3999-glass-dark": {"all": {"base": tex("glass-dark")}}},
        "renderpass": "Transparent", "faceCullMode": "Merge", "lightAbsorption": 0, "sidesolid": {"all": True}, "sideopaque": {"all": False},
        "resistance": 6, "drops": [], "sounds": GLASS, "attributes": dict(FIXED),
    }, "Level 3999: unbreakable storefront glass with faint streaks; dark: black glass with magenta glints (the Level 10 arcade)")
    LANG.update({"block-l3999-glass-clear": "Storefront Glass", "block-l3999-glass-dark": "Dark Glass"})
    COUNT["variants"] += 2
    block("l3999-magentatile", {
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Ceramic", "drawtype": "cube",
        "textures": {"all": {"base": tex("magentatile")}}, "lightHsv": [54, 7, 7], "lightAbsorption": 0, "resistance": 6, "drops": [],
        "sounds": STONE, "attributes": dict(FIXED),
    }, "Level 37's way to 3999: glowing hot-magenta pool mosaic at the bottom of a deep end (dive to it)")
    LANG["block-l3999-magentatile"] = "Glowing Magenta Tile"
    COUNT["variants"] += 1
    block("l3999-glitchwall", {
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "textures": {"all": {"base": tex("glitchwall"), "alternates": [{"base": tex("glitchwall2")}, {"base": tex("glitchwall3")}]}},
        "lightHsv": [51, 7, 5], "lightAbsorption": 0, "collisionbox": None, "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "resistance": 6, "drops": [], "sounds": {"walk": "game:walk/stone*", "ambient": "backrooms:ambient/3999/glitch", "ambientBlockCount": 3},
        "attributes": dict(FIXED), "randomizeAxes": "xyz",  # (D4) its versions picked by height too
    }, "Level 11's way to 3999: a stretch of alley wall in purple static. It has no substance: walk into it")
    LANG["block-l3999-glitchwall"] = "Glitched Wall"
    COUNT["variants"] += 1

    # Windows onto the painted car park: the painting recessed 4 px, a glass pane at 2 px, a steel mullion round the face
    def window(v):
        col, row = v["col"], v["row"]
        body = bx("Body", (0, 0, 4), (16, 16, 16), "concrete-wall", faces=("east", "south", "west", "up", "down"))
        body = picture(body, f"window-{col}-{row}", glow=60)
        return [body,
                glass(picture(bx("Pane", (2, 2, 2), (14, 14, 2.05), "glasspane", faces=("north", "south")), "glasspane")),
                bx("MullionT", (0, 14, 0), (16, 16, 4), "darksteel", faces=("north", "down", "east", "west", "up")),
                bx("MullionB", (0, 0, 0), (16, 2, 4), "darksteel", faces=("north", "up", "east", "west", "down")),
                bx("MullionL", (14, 2, 0), (16, 14, 4), "darksteel", faces=("north", "west", "east")),
                bx("MullionR", (0, 2, 0), (2, 14, 4), "darksteel", faces=("north", "east", "west"))]

    variants_block("l3999-window", "Window", [("col", ["0", "1", "2", "3"]), ("row", ["0", "1", "2"]), ("facing", SIDES)], window, rot="facing",
                   box=(0, 0, 0, 1, 1, 1), material="Glass", sounds=GLASS, data={
                       "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 6, "drops": [],
                       "attributes": dict(FIXED)},
                   comment="Level 3999's rim and the Grand Lobby strips: an unbreakable window onto a lit car park at night (one painting, "
                           "4 x 3 blocks: col 0 is the left and row 0 the top as seen from the room; facing = the way it looks into the room)")


# ======================================================================== 6.2 Neon and light

def tube(name, frm, to, colour, glow=255):
    return bx(name, frm, to, f"neon-{colour}", glow=glow)


def neon():
    light_c = lambda v: {f"*-{c}-*": hsv(c, v) for c in COLOURS}

    def ceiling(v):
        els = [tube("Tube", (7, 13, 0), (9, 15, 16), v["colour"])]
        for z in (3, 11):
            els.append(bx(f"Clip{z}", (7.5, 15, z), (8.5, 16, z + 2), "darksteel"))
            els.append(bx(f"Band{z}", (6.6, 12.6, z + 0.5), (9.4, 15.2, z + 1.5), "darksteel"))
        return els

    variants_block("l3999-neonceiling", "Neon Tube", [("colour", COLOURS), ("axis", ["ns", "we"])], ceiling, rot="axis",
                   box=(0.4, 0.75, 0, 0.6, 1, 1), collide=False, material="Glass", sounds=dict(GLASS, ambient=HUM, ambientBlockCount=12),
                   data={"lightHsvByType": light_c(16), "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a glowing 2 x 2 neon tube 1 px under the ceiling (ns: running north-south), on two clips (light 16)")

    def wall(v):
        c = v["colour"]
        return hang([tube("Tube", (7, 0, -3), (9, 16, -1), c),
                     bx("ClipB", (6.5, 1, -3.4), (9.5, 2.5, 0), "darksteel"), bx("ClipT", (6.5, 13.5, -3.4), (9.5, 15, 0), "darksteel")])

    variants_block("l3999-neonwall", "Neon Tube", [("colour", COLOURS), ("facing", SIDES)], wall, rot="facing",
                   box=(0.35, 0, 0.75, 0.65, 1, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"lightHsvByType": light_c(13), "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a vertical neon tube 1 px off the wall behind it (the suffix is the way it faces), full height, stacked into arches")

    def rail(v):
        c = v["colour"]
        return hang([tube("Tube", (0, 1, -3), (16, 3, -1), c),
                     bx("Clip0", (3, 0.5, -3.4), (4.5, 3.5, 0), "darksteel"), bx("Clip1", (11.5, 0.5, -3.4), (13, 3.5, 0), "darksteel")])

    variants_block("l3999-neonrail", "Neon Base Strip", [("colour", COLOURS), ("facing", SIDES)], rail, rot="facing",
                   box=(0, 0, 0.75, 1, 0.25, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"lightHsvByType": light_c(12), "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a horizontal neon strip along the foot of the wall behind it (base glow, light 12)")

    def rail_corner(v):
        # In a unit's corner the strip along the side wall comes on to meet the one along the wall behind: hand "l" has
        # the side wall on the left (west of a north-facing strip), "r" on the right
        c = v["colour"]
        x0, cx = (1, 0) if v["hand"] == "l" else (13, 12.6)
        return rail(v) + [tube("SideTube", (x0, 1, 0), (x0 + 2, 3, 13), c),
                          bx("SideClip", (cx, 0.5, 3), (cx + 3.4, 3.5, 4.5), "darksteel")]

    variants_block("l3999-neonrailcorner", "Neon Base Strip", [("colour", COLOURS), ("hand", ["l", "r"]), ("facing", SIDES)], rail_corner,
                   rot="facing", box=(0, 0, 0.75, 1, 0.25, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"lightHsvByType": light_c(12), "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: the neon base strip in a unit's corner, along the wall behind it and on along the side wall")

    def dead(v):
        els = ceiling({"colour": "magenta"})
        for e in els:
            for f in e["faces"].values():
                if f["texture"] == "#neon-magenta":
                    f["texture"] = "#neon-dead"
                    f.pop("glow", None)
        els[0]["to"][2] = 11.5            # a broken end
        els.append(bx("Stub", (7.2, 13.2, 12.5), (8.8, 14.8, 16), "neon-dead"))
        return els

    variants_block("l3999-neondead", "Dead Neon Tube", [("axis", ["ns", "we"])], dead, rot="axis",
                   box=(0.4, 0.75, 0, 0.6, 1, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"drops": drops(("glassshard", 1, 0.5), ("scrapwire", 0.4, 0.3), ("l3999-neontubing", 0.6, 0.3))},
                   comment="Level 3999.1: a dead neon tube, dark grey glass, cracked and broken off. Salvage: glass, wire, neon tubing")

    # Neon signs: letters as raised tubes on a black backplate, three blocks wide, against the wall behind
    SIGNS = {"arcade": ("ARCADE", "magenta"), "prizes": ("PRIZES", "cyan"), "foodcourt": ("FOOD COURT", "orange"),
             "lobby": ("LOBBY", "lilac"), "open": ("OPEN", "pink"), "paradise": ("PARADISE", "magenta"), "exit": ("EXIT", "pink")}

    def sign(v):
        word, c = SIGNS[v["sign"]]
        rows = text_rows(word, F5)
        cell = min(42 / len(rows[0]), 9.5 / 7)
        els = [bx("Plate", (-15, 1, 15), (31, 15, 16), "black")]
        els += text_boxes(word, 8, 8 + 3.5 * cell, cell, 13.6, 15, f"neon-{c}", glow=255, name="L")
        frame = "cyan" if v["sign"] == "paradise" else c
        for nm, a, b in (("FT", (-14, 13.6, 14.2), (30, 14.4, 15)), ("FB", (-14, 1.6, 14.2), (30, 2.4, 15)),
                         ("FL", (29.2, 2.4, 14.2), (30, 13.6, 15)), ("FR", (-14, 2.4, 14.2), (-13.2, 13.6, 15))):
            els.append(tube(nm, a, b, frame))
        for x in (-12, 28):
            els.append(bx(f"Stand{x}", (x, 0, 15), (x + 1, 1, 16), "darksteel"))
        return els

    variants_block("l3999-neonsign", "Neon Sign", [("sign", list(SIGNS)), ("facing", SIDES)], sign, rot="facing",
                   box=(-0.9, 0.06, 0.85, 1.9, 0.94, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"lightHsvByType": {f"*-{k}-*": hsv(c, 12) for k, (_, c) in SIGNS.items()}, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a neon sign three blocks wide, drawn centred on its block, against the wall behind it (the suffix is "
                           "the way it faces): ARCADE magenta, PRIZES cyan, FOOD COURT orange, LOBBY lilac, OPEN pink, PARADISE magenta "
                           "in a cyan frame, EXIT pink (light 12)",
                   names={f"l3999-neonsign-{k}-*": f"Neon Sign ({w.title()})" for k, (w, _) in SIGNS.items()})
    # The same signs drawn half a block to the left or right of their block (as seen from in front), for a unit's
    # sign over its six-wide way in: there is no middle block over an even width, and drawn on its own block the sign
    # hung half a block off the middle of the doorway (layout version 4 on picks these there)
    variants_block("l3999-neonsignshift", "Neon Sign", [("sign", list(SIGNS)), ("shift", ["left", "right"]), ("facing", SIDES)],
                   lambda v: move(sign(v), dx=8 if v["shift"] == "left" else -8), rot="facing",
                   boxes=lambda v: (-0.4, 0.06, 0.85, 2.4, 0.94, 1) if v["shift"] == "left" else (-1.4, 0.06, 0.85, 1.4, 0.94, 1),
                   collide=False, material="Glass", sounds=GLASS,
                   data={"lightHsvByType": {f"*-{k}-*": hsv(c, 12) for k, (_, c) in SIGNS.items()}, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a neon sign three blocks wide, drawn half a block to the left or right of its block as seen "
                           "from in front, so that it hangs centred over a doorway an even number of blocks wide (otherwise as "
                           "l3999-neonsign)",
                   names={f"l3999-neonsignshift-{k}-*": f"Neon Sign ({w.title()})" for k, (w, _) in SIGNS.items()})

    # Stall signs: an icon and the word in neon, two blocks wide
    STALLS = {"burger": ("BURGERS", "orange"), "pizza": ("PIZZA", "pink"), "noodles": ("NOODLES", "cyan"),
              "taco": ("TACOS", "blue"), "icecream": ("ICE CREAM", "lilac"), "pretzel": ("PRETZELS", "magenta")}
    ICONS = {
        "burger": ["..#######..", ".#########.", "###########", ".#.#.#.#.#.", "###########", ".#########."],
        "pizza": ["###########", ".#.......#.", "..#.#..#.#.", "...#...#...", "....#.#....", ".....#....."],
        "noodles": ["....#...#..", "...#...#...", "###########", ".#.......#.", "..#.....#..", "...#####..."],
        "taco": ["...#####...", "..#.#.#.#..", ".#.......#.", "#.........#", "#.........#", "###########"],
        "icecream": ["...#####...", "..#######..", "...#####...", "...#...#...", "....#.#....", ".....#....."],
        "pretzel": ["..###.###..", ".#...#...#.", ".#..#.#..#.", "..##...##..", "..#.#.#.#..", "...#...#..."],
    }

    def stallsign(v):
        word, c = STALLS[v["stall"]]
        icon = [r.replace(".", "0").replace("#", "1") for r in ICONS[v["stall"]]]
        els = [bx("Plate", (-7, 0.5, 15), (23, 15.5, 16), "black")]
        els += bitmap_boxes(icon, 8, 14.5, 0.9, 13.8, 15, f"neon-{c}", glow=255, name="I")
        rows = text_rows(word, F5)
        cell = min(28 / len(rows[0]), 1.0)
        els += text_boxes(word, 8, 1.5 + 7 * cell, cell, 13.8, 15, f"neon-{c}", glow=255, name="W")
        return els

    variants_block("l3999-stallsign", "Stall Sign", [("stall", list(STALLS)), ("facing", SIDES)], stallsign, rot="facing",
                   box=(-0.45, 0.03, 0.85, 1.45, 0.97, 1), collide=False, material="Glass", sounds=GLASS,
                   data={"lightHsvByType": {f"*-{k}-*": hsv(c, 11) for k, (_, c) in STALLS.items()}, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's food courts: a neon sign two blocks wide over a stall, an icon and the word, against the wall behind it")

    # The junction sign: 3999 in pink and cyan tubes, 3 wide and 2 tall, hanging on four chains below its block; it
    # reads from both sides
    def sign3999(v):
        els = [bx("Plate", (-15, -28, 7.6), (31, 3, 8.4), "black")]
        cols = ["pink", "cyan", "pink", "cyan"]
        cell = 1.9
        for side, z1, z2, facing in (("N", 6.4, 7.6, "north"), ("S", 8.4, 9.6, "south")):
            # each digit its own colour: build them one at a time, laid out as in the whole word
            rows_all = text_rows("3999", F5)
            width = len(rows_all[0]) * cell
            x_left = 8 + width / 2 if facing == "north" else 8 - width / 2
            col0 = 0
            for i, ch in enumerate("3999"):
                g = text_rows(ch, F5)
                w = len(g[0]) * cell
                cxd = x_left - col0 * cell - w / 2 if facing == "north" else x_left + col0 * cell + w / 2
                # (a hair thinner than the frame tubes, which the outer digits touch)
                els += text_boxes(ch, cxd, -5.5, cell, z1 + 0.05, z2 - 0.05, f"neon-{cols[i]}", glow=255, name=f"D{side}{i}", facing=facing)
                col0 += len(g[0]) + 1
            for nm, a, b in (("FT", (-14, 1.6, 0), (30, 2.4, 0)), ("FB", (-14, -27.4, 0), (30, -26.6, 0)),
                             ("FL", (-14, -26.6, 0), (-13.2, 1.6, 0)), ("FR", (29.2, -26.6, 0), (30, 1.6, 0))):
                els.append(tube(nm + side, (a[0], a[1], z1), (b[0], b[1], z2), "pink"))
        for i, x in enumerate((-12, -4, 20, 28)):
            els.append(bx(f"Chain{i}", (x, 3, 7.5), (x + 1, 16, 8.5), "darksteel", faces=SIDE4))
        return els

    variants_block("l3999-sign3999", "3999 Sign", [], sign3999, box=(-0.9, -1.75, 0.38, 1.9, 1, 0.62), collide=False, material="Glass",
                   sounds=GLASS, data={"lightHsv": [62, 7, 14], "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: the giant 3999 sign of a junction plaza, 3 blocks wide and 2 tall, hanging on four chains below its "
                           "block (place it under the ceiling); it reads from the north and the south (light 14)")

    # Pillars: mirror steel, octagonal, a vertical neon tube down each of the four diagonal faces, full height, so a stack
    # of blocks reads as one lit column (rings stacked 17 high read as a ladder)
    def pillar(v):
        c = v["colour"]
        els = [bx("ShaftA", (2, 0, 4.5), (14, 16, 11.5), "mirror"), bx("ShaftB", (4.5, 0, 2), (11.5, 16, 14), "mirror"),
               rot(bx("ShaftC", (2, 0, 4.5), (14, 16, 11.5), "mirror"), ry=45, origin=(8, 0, 8)),
               rot(bx("ShaftD", (4.5, 0, 2), (11.5, 16, 14), "mirror"), ry=45, origin=(8, 0, 8))]
        for n, (frm, to) in enumerate((((13.5, 0, 7), (15, 16, 9)), ((1, 0, 7), (2.5, 16, 9)),
                                       ((7, 0, 13.5), (9, 16, 15)), ((7, 0, 1), (9, 16, 2.5)))):
            els.append(rot(tube(f"Tube{n}", frm, to, c), ry=45, origin=(8, 0, 8)))
        return els

    variants_block("l3999-pillar", "Mirror Pillar", [("colour", COLOURS)], pillar, box=(0.125, 0, 0.125, 0.875, 1, 0.875), material="Metal",
                   sounds=METAL, data={"lightHsvByType": {f"*-{c}": hsv(c, 15) for c in COLOURS}, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a mirror-steel octagonal column 12 px across with a vertical neon tube down each diagonal face "
                           "(stack one per block of height; the tubes run on into one lit column; light 15)")

    def poolled(v):
        return [faces_box("Edge", (0, 0, 0), (16, 16, 16), {"up": "white", "down": "pooltile-violet", "east": "pooltile-edge", "south": "pooltile-edge",
                                                            "west": "pooltile-edge"}),
                faces_box("Lower", (0, 0, 0), (16, 10, 0.01), {"north": "pooltile-edge"}),
                faces_box("Upper", (0, 13, 0), (16, 16, 0.01), {"north": "pooltile-edge"}),
                bx("Groove", (0, 10, 1), (16, 13, 1.5), "black", faces=("north",)),
                bx("Strip", (0, 10.8, 0.6), (16, 12.2, 1.2), "led-violet", glow=255, faces=("north", "up", "down"))]

    variants_block("l3999-poolled", "Pool Edge Light", [("facing", SIDES)], poolled, rot="facing", box=(0, 0, 0, 1, 1, 1), material="Ceramic",
                   sounds=STONE, data={"lightHsv": [51, 7, 10], "sidesolid": {"all": True}, "lightAbsorption": 0, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's Neon Natatorium: a pool's coping block with a violet LED strip in a groove on the side it faces (light 10)")

    # Sodium lamp (the Level 10 arcade's car park): a pole, and the head with its cobra arm
    pole = [bx("Pole", (6, 0, 6), (10, 16, 10), "lampsteel")]
    head = [bx("Pole", (6, 0, 6), (10, 10, 10), "lampsteel"), bx("Top", (6.5, 10, 6.5), (9.5, 12, 9.5), "lampsteel"),
            rot(bx("Arm", (7, 11, -6), (9, 13, 8), "lampsteel"), rx=-12, origin=(8, 12, 8)),
            bx("Head", (5, 11.5, -10), (11, 14, -3), "lampsteel"),
            bx("Lens", (5.5, 11, -9.5), (10.5, 11.5, -3.5), "sodium", glow=255, faces=("down", "north", "south", "east", "west"))]
    ps, hs = shape("l3999-lamppost-pole", pole), shape("l3999-lamppost-head", head)
    states = ["pole"] + [f"head-{s_}" for s_ in SIDES]
    shapes = {"l3999-lamppost-pole": {"base": ps}}
    for s_ in SIDES:
        shapes[f"l3999-lamppost-head-{s_}"] = dict({"base": hs}, **({"rotateY": ROTATE[s_]} if ROTATE[s_] else {}))
    block("l3999-lamppost", {
        "variantgroups": [{"code": "part", "states": states}], "shapeByType": shapes,
        "creativeinventory": {"general": ["l3999-lamppost-pole", "l3999-lamppost-head-north"], "backrooms": ["l3999-lamppost-pole"]},
        "blockmaterial": "Metal", "drawtype": "json", **OPEN, "resistance": 6, "sounds": METAL,
        "collisionbox": cuboid((0.375, 0, 0.375, 0.625, 1, 0.625)), "selectionbox": cuboid((0.375, 0, 0.375, 0.625, 1, 0.625)),
        "lightHsvByType": {"*-head-*": [5, 6, 15]}, "drops": [], "attributes": dict(FIXED),
    }, "The Level 10 arcade's car park: a steel lamp pole (stack poles), and its head with a cobra arm reaching 12 px out the way "
       "it faces, a sodium lens (light 15, orange)")
    COUNT["variants"] += 5

    def beacon(v):
        on = v["colour"]
        els = [bx("Base", (3, 0, 3), (13, 2, 13), "darksteel"),
               bx("Bulb", (5, 2, 5), (11, 8, 11), f"bulb-{on}", glow=255)]
        for i, (x, z) in enumerate(((4, 4), (11, 4), (4, 11), (11, 11))):
            els.append(bx(f"Bar{i}", (x, 2, z), (x + 1, 9, z + 1), "darksteel"))
        els += [bx("CapX", (4, 9, 7.5), (12, 10, 8.5), "darksteel"), bx("CapZ", (7.5, 9, 4), (8.5, 10, 12), "darksteel"),
                bx("Ring", (4, 5, 4), (12, 5.6, 12), "darksteel", faces=SIDE4)]
        return els

    variants_block("l3999-beacon", "Windmill Beacon", [("colour", ["red", "green"])], beacon, box=(0.19, 0, 0.19, 0.81, 0.63, 0.81),
                   material="Metal", sounds=METAL, data={"lightHsvByType": {"*-red": [0, 7, 15], "*-green": [21, 7, 15]}, "drops": [],
                                                       "attributes": dict(FIXED)},
                   comment="Level 10's windmills: a glowing bulb in a cage on the cap, red until someone throws the generator's lever, then green")


# ======================================================================== 6.4 Lobby, food court, concourse, service

def lobby():
    # The reception desk: a curved white top, a lilac front with a pink neon strip under the lip; a brass bell on mid.
    # The front faces the way named; left and right (as seen from the front) curve back toward the receptionist.
    def straight(x1, x2, bell=False):
        els = [bx("Front", (x1, 0, 2), (x2, 13, 4), "lilacpanel"), bx("Plinth", (x1, 0, 3), (x2, 1, 4.2), "black"),
               bx("Strip", (x1, 12.4, 1.4), (x2, 13, 2), "neon-pink", glow=255), bx("Top", (x1, 13, 1), (x2, 15, 10), "whitegloss"),
               bx("Body", (x1, 0, 4), (x2, 13, 9), "whitegloss"), bx("Work", (x1, 9, 9), (x2, 10, 15), "whitegloss")]
        if bell:
            els += cyl("Bell", 11, 5, 1.4, 15, 16, "brass") + [bx("Knob", (10.6, 16, 4.6), (11.4, 16.6, 5.4), "brass")]
            els += [bx("Pad", (3, 15, 3), (7, 15.2, 7), "black"), bx("Pen", (3.5, 15.2, 4), (6.5, 15.6, 4.4), "chrome")]
        return els

    def desk(v):
        part = v["part"]
        if part == "mid":
            return straight(0, 16, bell=True)
        # The left piece: from the joint with mid (x 0) it turns 45 degrees back, toward +X and south
        els = straight(0, 8)
        seg = [e for e in straight(0, 10) if e["name"] != "Work"]
        for e in seg:
            e2 = rot(move([e], dx=8)[0], ry=-45, origin=(8, 0, 2))
            e2["name"] = "C" + e["name"]
            els.append(e2)
        return els if part == "left" else mirror_x(els)

    variants_block("l3999-reception", "Reception Desk", [("part", ["left", "mid", "right"]), ("facing", SIDES)], desk, rot="facing",
                   box=(0, 0, 0.06, 1, 0.94, 0.94), material="Wood",
                   data={"lightHsv": [53, 3, 6], "drops": [], "attributes": dict(FIXED, l3999reception=True)},
                   comment="Level 3999's lobbies: a curved reception desk (left, mid, right as seen from the front, which faces the way named; "
                           "the ends curve back); a lilac front, a pink neon strip under the lip (light 6), a brass bell on mid")

    def couch(v):
        els = [bx("Base", (0, 1.5, 2), (16, 5, 15), "velvetdark"), bx("Seat", (0, 5, 1.5), (16, 8, 12), "velvet"),
               bx("Back", (0, 5, 12), (16, 17, 15.5), "velvet"), bx("BackTop", (0, 17, 12.5), (16, 18, 15.5), "velvet")]
        for i, x in enumerate((3, 8, 13)):
            for j, y in enumerate((9.5, 13.5)):
                els.append(bx(f"Button{i}{j}", (x - 0.4, y - 0.4, 11.6), (x + 0.4, y + 0.4, 12), "velvetdark"))
        els += [bx("Arm", (12.5, 5, 1.5), (16, 11, 15.5), "velvet"), bx("ArmTop", (12.2, 11, 1.2), (16, 12, 15.5), "velvet")]
        for x, z in ((1, 3), (13.5, 3), (1, 13), (13.5, 13)):
            els.append(bx(f"Foot{x}{z}", (x, 0, z), (x + 1.5, 1.5, z + 1.5), "chrome"))
        return els if v["part"] == "left" else mirror_x(els)

    variants_block("l3999-couch", "Velvet Couch", [("part", ["left", "right"]), ("facing", SIDES)], couch, rot="facing",
                   box=(0, 0, 0.06, 1, 0.56, 1), material="Cloth", sounds=CLOTH, data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's lobbies: a deep purple velvet couch two blocks long, buttoned back, chrome feet (left and right as "
                           "seen from the front; each has its arm on its outer end)")

    def coffeetable(v):
        els = [glass(bx("Top", (1, 7, 2), (15, 8, 14), "glasstop")), bx("RimN", (1, 6.5, 1.5), (15, 7, 2), "chrome"),
               bx("RimS", (1, 6.5, 14), (15, 7, 14.5), "chrome")]
        for x in (1.5, 13.5):
            els += [bx(f"Leg{x}", (x, 0, 2), (x + 1, 7, 3), "chrome"), bx(f"LegB{x}", (x, 0, 13), (x + 1, 7, 14), "chrome"),
                    bx(f"Rail{x}", (x, 0, 3), (x + 1, 1, 13), "chrome")]
        els.append(bx("Magazine", (4, 8, 5), (9, 8.3, 10), "lostfound"))
        return els

    variants_block("l3999-coffeetable", "Coffee Table", [], coffeetable, box=(0.06, 0, 0.1, 0.94, 0.5, 0.9), material="Glass", sounds=GLASS,
                   data={"drops": [], "attributes": dict(FIXED)}, comment="Level 3999's lobbies: a low glass table on a chrome frame")

    def lostfound(v):
        els = [faces_box("Bin", (2, 0, 3), (14, 13, 13), {"north": "lostfound", "east": "bluebin", "south": "bluebin", "west": "bluebin", "down": "bluebin"},
                         full=False),
               bx("Inside", (2.5, 12, 3.5), (13.5, 12.5, 12.5), "black", faces=("up",)),
               bx("Lid", (1.6, 13, 2.6), (14.4, 14, 13.4), "bluebin"), bx("Flap", (4, 14, 4), (12, 14.4, 8), "darksteel")]
        els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        # clothes spilling over the rim
        els += [bx("Shirt", (4, 13.6, 9), (9, 14.8, 12.5), "fur-white"), bx("Sleeve", (8, 12, 2.6), (9.5, 14.2, 3.2), "fur-white")]
        return els

    variants_block("l3999-lostfound", "Lost and Found", [("facing", SIDES)], lostfound, rot="facing", box=(0.12, 0, 0.18, 0.88, 0.88, 0.82),
                   material="Wood", data={"drops": drops(("game:clothes-upperbody-linen-tunic", 0.3, 0), ("game:clothes-lowerbody-commoner-trousers", 0.3, 0),
                                                         ("game:clothes-foot-commoner-boots", 0.25, 0), ("game:clothes-upperbody-woolen-shirt", 0.2, 0),
                                                         ("game:clothes-head-straw-hat", 0.15, 0), ("game:backpack-normal", 0.1, 0),
                                                         ("game:cloth-plain", 0.5, 0.5))},
                   comment="Level 3999's receptions: a blue LOST & FOUND bin, clothes spilling out. Salvage: 1-2 vanilla clothes, now and then a backpack")

    def planter(v):
        els = [bx("Box", (2, 0, 2), (14, 9, 14), "whitegloss"), bx("Rim", (1.5, 9, 1.5), (14.5, 10, 14.5), "whitegloss"),
               bx("Soil", (2.5, 9.6, 2.5), (13.5, 10.1, 13.5), "soil", faces=("up",))]
        for i in range(6):
            els.append(bx(f"Trunk{i}", (7.2 - i * 0.1, 10 + i * 3, 7.2), (8.8 - i * 0.1, 13 + i * 3, 8.8), "trunk"))
        for k in range(8):
            a = k * 45
            els.append(rot(bx(f"Frond{k}", (7.5, 28, 8), (8.5 + 0, 28.6, 17.5), "palm" if k % 2 else "palmdark"), rx=-25, ry=a, origin=(8, 28.3, 8)))
            els.append(rot(bx(f"Leaf{k}", (5.5, 28.1, 11), (10.5, 28.4, 16.5), "palm"), rx=-25, ry=a, origin=(8, 28.3, 8)))
        return els

    variants_block("l3999-planter", "Planter", [], planter, box=(0.12, 0, 0.12, 0.88, 0.62, 0.88), material="Wood",
                   data={"drops": [], "attributes": dict(FIXED)}, comment="Level 3999: a white box planter with a fake palm, fronds fanning out")

    def bench(v):
        els = []
        for x in (1, 14):
            els += [bx(f"LegF{x}", (x, 0, 3), (x + 1, 7, 4), "darksteel"), bx(f"LegB{x}", (x, 0, 11), (x + 1, 16, 12), "darksteel"),
                    bx(f"Frame{x}", (x, 6, 3), (x + 1, 7, 12), "darksteel")]
        for i in range(4):
            els.append(bx(f"Slat{i}", (0, 7, 3 + i * 2.2), (16, 8, 4.8 + i * 2.2), "slat"))
        for i in range(3):
            els.append(bx(f"Back{i}", (0, 9 + i * 2.2, 11.5), (16, 10.6 + i * 2.2, 12.5), "slat"))
        return els

    variants_block("l3999-bench", "Bench", [("facing", SIDES)], bench, rot="facing", box=(0, 0, 0.18, 1, 0.5, 0.8), material="Wood",
                   data={"drops": [], "attributes": dict(FIXED)}, comment="Level 3999's concourses: a bench, steel frame and wooden slats")

    def trashbin(v):
        return (cyl("Can", 8, 8, 4.5, 0, 12, "chrome") + cyl("Lid", 8, 8, 4.8, 12, 14, "rubber") +
                [bx("Mouth", (5, 12.5, 3), (11, 13.5, 3.4), "black"), bx("Knob", (7.4, 14, 7.4), (8.6, 14.8, 8.6), "rubber")])

    variants_block("l3999-trashbin", "Trash Bin", [], trashbin, box=(0.2, 0, 0.2, 0.8, 0.9, 0.8), material="Metal", sounds=METAL,
                   data={"drops": drops(("l3999-plastic", 0.8, 0.5), ("game:paper-parchment", 0.4, 0.4), ("l3999-ticket", 0.3, 0.3),
                                        ("l3999-popcorn", 0.08, 0), ("metalbracket", 0.3, 0.2))},
                   comment="Level 3999: a chrome bin with a black lid. Salvage: plastic, paper, a dropped ticket or two")

    def table(v):
        if B16_FURNITURE:
            return B16.table()
        return (cyl("Top", 8, 8, 6, 11, 12, "whitegloss") + cyl("Pedestal", 8, 8, 1, 1, 11, "chrome") + cyl("Foot", 8, 8, 4, 0, 1, "chrome"))

    variants_block("l3999-table", "Food Court Table", [], table, box=(0.12, 0, 0.12, 0.88, 0.75, 0.88), material="Wood",
                   data={"drops": [], "attributes": dict(FIXED)}, comment="Level 3999's food courts: a round pedestal table, white top")

    def chair(v):
        if B16_FURNITURE:
            return B16.chair(v["colour"])
        p = f"plastic-{v['colour']}"
        els = [bx("Seat", (3, 7, 3), (13, 8, 13), p), bx("SeatLip", (3, 6.5, 2.5), (13, 7.5, 3.5), p),
               rot(bx("Back", (3, 8, 12.5), (13, 17, 13.5), p), rx=-8, origin=(8, 8, 13))]
        for x, z in ((3.5, 3.5), (11.5, 3.5), (3.5, 11.5), (11.5, 11.5)):
            els.append(bx(f"Leg{x}{z}", (x, 0, z), (x + 1, 7, z + 1), "chrome"))
        return els

    variants_block("l3999-chair", "Plastic Chair", [("colour", ["white", "pink", "cyan"]), ("facing", SIDES)], chair, rot="facing",
                   box=(0.18, 0, 0.18, 0.82, 0.5, 0.85), material="Wood", data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's food courts: a moulded plastic chair on chrome legs (white, pink, cyan)")

    def booth(v):
        if B16_FURNITURE:
            return B16.booth()
        els = [bx("Base", (0, 0, 3), (16, 6, 15), "chrome"), bx("Seat", (0, 6, 2), (16, 9, 13), "vinyl-pink"),
               bx("Edge", (0, 5.5, 1.5), (16, 6.5, 2.5), "chrome"), bx("Back", (0, 6, 12.5), (16, 22, 16), "vinyl-pink"),
               bx("BackCap", (0, 22, 12), (16, 23, 16), "chrome")]
        return els

    variants_block("l3999-booth", "Diner Booth", [("facing", SIDES)], booth, rot="facing", box=(0, 0, 0.1, 1, 0.56, 1), material="Cloth",
                   sounds=CLOTH, data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's food courts: a diner booth seat, pink vinyl, chrome edge, a tall back (along the side walls)")


def food():
    STALLS = ["burger", "pizza", "noodles", "taco", "icecream", "pretzel"]

    def counter(v):
        st = v["stall"]
        front = faces_box("Front", (0, 0, 1), (16, 13, 3), {"north": f"stall-{st}"})
        front["faces"]["north"]["uv"] = [0, 0, 16, 13]
        els = [front, bx("Body", (0, 0, 3), (16, 13, 16), "counter", faces=("east", "west", "south")),
               bx("Top", (0, 13, 0.5), (16, 14.5, 16), "counter"), bx("Kick", (0, 0, 0.5), (16, 1, 1), "black"),
               bx("Till", (10, 14.5, 7), (15, 17, 12), "till"), rot(picture(bx("TillScreen", (10.5, 17, 9), (14.5, 20, 9.6), "till"), "tillscreen", glow=120), rx=-15, origin=(12.5, 17, 9.3)),
               bx("Drawer", (10, 14.5, 6.5), (15, 15.5, 7), "darksteel"),
               bx("Napkins", (2, 14.5, 3), (5.5, 18, 5.5), "chrome"), bx("Napkin", (2.6, 18, 3.6), (4.9, 19, 4.9), "napkin")]
        els += cyl("Cup", 7.5, 4.5, 1.2, 14.5, 17.5, "strawcup")
        for i, (dx, dz) in enumerate(((-0.4, 0), (0.4, 0.3), (0, -0.4))):
            els.append(rot(bx(f"Straw{i}", (7.4 + dx, 17, 4.4 + dz), (7.7 + dx, 21, 4.7 + dz), "white"), rz=8 * (i - 1), origin=(7.5, 17, 4.5)))
        return els

    variants_block("l3999-stallcounter", "Food Stall", [("stall", STALLS), ("facing", SIDES)], counter, rot="facing",
                   box=(0, 0, 0.03, 1, 0.9, 1), material="Wood",
                   data=with_class({"drops": [], "attributes": dict(FIXED, l3999stall={
                       st: {"meal": f"l3999-traymeal-{st}", "cost": 6} for st in STALLS})}, cls="BackroomsFoodStall", entity="BackroomsFoodStall"),
                   comment="Level 3999's food courts: a stall's counter (its colour on the front), a till, napkins and a cup of straws. "
                           "6 tickets buy that stall's tray meal (attributes.l3999stall)",
                   names={f"l3999-stallcounter-{st}-*": f"Food Stall ({n})" for st, n in zip(STALLS, ("Burgers", "Pizza", "Noodles", "Tacos", "Ice Cream", "Pretzels"))})

    def menuboard(v):
        face = picture(bx("Face", (-0.5, 2, -2), (16.5, 14, -1.5), "black", faces=("north",)), "menuboard", glow=200)
        return hang([bx("Frame", (-1, 1.5, -1.5), (17, 14.5, 0), "darksteel"), face,
                     bx("Wire0", (2, 14.5, -1), (2.5, 16, -0.5), "darksteel"), bx("Wire1", (13.5, 14.5, -1), (14, 16, -0.5), "darksteel")])

    variants_block("l3999-menuboard", "Menu Board", [("facing", SIDES)], menuboard, rot="facing", box=(0, 0.09, 0.88, 1, 0.91, 1), collide=False,
                   material="Wood", data={"lightHsv": [5, 2, 8], "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's food courts: a lit menu board over the stalls, prices in tickets, against the wall behind it (light 8)")

    def vending(v):
        kind = v["kind"]
        body = f"vendingbody-{kind}"
        if B16_VENDING:
            els = B16.vending_parts(kind)
        else:
            face = picture(bx("Face", (1.5, 1, 1.4), (14.5, 31, 1.5), body, faces=("north",)), f"vending-{kind}", glow=90)
            els = [bx("Body", (1, 0, 2), (15, 31, 15), body), face]
        front = [glass(bx("Glass", (2.2, 7.5, 0.6), (12, 29.5, 0.7), "glasspane", faces=("north",))),
                 bx("Keypad", (12.4, 16, 0.6), (14.2, 22, 1.4), "darksteel"),
                 picture(bx("Tape", (12.6, 12.5, 0.4), (14.2, 14.5, 1.4), "tape", faces=("north",)), "tape"),
                 bx("Flap", (2.5, 1.8, 0.8), (11.5, 5, 1.4), "darksteel")]
        if B16_VENDING:
            # (B16) B0 placed these as if the picture's left were at x 0; it is at x 16 on a north face. The glass and the
            # flap now cover the window and the painted flap; the keypad is a plate of keys and the taped coin slot a
            # label, on their painted places (x 2.3-4.8)
            front = mirror_x([front[0], front[3]]) + B16.vending_keypad()
        els += front + [
               bx("Top", (0.8, 31, 1.8), (15.2, 32, 15.2), body),
               tube("EdgeL", (14.6, 1, 1.2), (15.2, 31, 1.8), "cyan"), tube("EdgeR", (0.8, 1, 1.2), (1.4, 31, 1.8), "cyan")]
        return els

    variants_block("l3999-vending", "Vending Machine", [("kind", ["snack", "drink"]), ("facing", SIDES)], vending, rot="facing",
                   box=(0.06, 0, 0.06, 0.94, 1.9, 0.94), material="Metal", sounds=METAL,
                   data={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser", "lightHsv": [33, 4, 6], "drops": [],
                         "attributesByType": {
                             "*-snack-*": dict(FIXED, takes="backrooms:almondwater", stockless=True,
                                               dispenses=["backrooms:chips", "backrooms:candybar", "backrooms:l3999-popcorn", "backrooms:l3999-cottoncandy"]),
                             "*-drink-*": dict(FIXED, takes="backrooms:almondwater", stockless=True,
                                               dispenses=["backrooms:soda", "backrooms:cashewwater", "backrooms:l3999-soda-cherry",
                                                          "backrooms:l3999-soda-lime", "backrooms:l3999-soda-grape"])}},
                   comment="Level 3999: a tall vending machine (snacks or drinks), the coin slot taped over: ALMOND WATER ONLY. One bottle "
                           "in, one snack or drink out, never empty (attributes takes and stockless are for BackroomsDispenser; light 6)",
                   names={"l3999-vending-snack-*": "Snack Machine", "l3999-vending-drink-*": "Drinks Machine"})

    def directory(v):
        face = picture(bx("Face", (4.5, 3, 5.4), (11.5, 29, 5.5), "black", faces=("north",)), "directory", glow=180)
        return [bx("Base", (3, 0, 4), (13, 2, 12), "darksteel"), bx("Totem", (4, 2, 6), (12, 30, 10), "darksteel"), face,
                bx("Cap", (3.6, 30, 5.6), (12.4, 31, 10.4), "darksteel"), tube("Edge", (4, 29.95, 5.55), (12, 30.4, 6), "lilac")]

    variants_block("l3999-directory", "Mall Directory", [("facing", SIDES)], directory, rot="facing", box=(0.19, 0, 0.25, 0.81, 1.9, 0.75),
                   material="Metal", sounds=METAL,
                   data=with_class({"lightHsv": [5, 1, 8], "drops": [], "attributes": dict(FIXED)}, cls="BackroomsArcadeDirectory"),
                   comment="Level 3999: a lit YOU ARE HERE totem at junctions and in lobbies (light 8). Right-click: the way to the nearest food court and lobby")


def concourse():
    # The moving walkway: a recessed tread (its top at 15 px), ribs running along it, chevrons pointing the way it runs
    def walkway(v):
        els = [faces_box("Tread", (0, 0, 0), (16, 14.6, 16), {"up": "tread", "north": "darksteel", "east": "darksteel", "south": "darksteel",
                                                               "west": "darksteel", "down": "darksteel"})]
        els[0]["faces"]["up"]["uv"] = [0, 0, 16, 16]
        for i in range(7):
            x = 2 + i * 2
            els.append(bx(f"Rib{i}", (x, 14.6, 0), (x + 0.6, 15, 16), "darksteel", faces=("up", "east", "west")))
        return els

    variants_block("l3999-walkway", "Moving Walkway", [("dir", ["n", "e", "s", "w"])], walkway, rot="dir", box=(0, 0, 0, 1, 0.9375, 1),
                   material="Metal", sounds=dict(METAL, ambient="backrooms:effect/3999/walkway", ambientBlockCount=48),
                   data=with_class({"sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True}, "lightAbsorption": 99,
                                    "drops": [], "attributes": dict(FIXED, l3999walkway={"speed": 2.5})}, cls="BackroomsWalkway"),
                   comment="Level 3999's concourses: a moving walkway's tread, a floor block with its top at 15 px, ribbed, yellow edges and "
                           "chevrons pointing the way it runs (n: north). It carries whoever stands on it (BackroomsWalkway, 2.5 blocks a second)")

    def walkwayend(v):
        a = math.degrees(math.atan2(1, 16))
        els = [bx("Body", (0, 0, 0), (16, 14.6, 16), "darksteel"),
               rot(faces_box("Plate", (0, 14.5, 0), (16, 15.5, 16), {"up": "comb", "east": "steel", "west": "steel", "south": "steel", "north": "steel"}),
                   rx=a, origin=(8, 15, 8))]
        for i in range(10):
            x = 0.8 + i * 1.5
            els.append(bx(f"Tooth{i}", (x, 14.5, 16), (x + 0.8, 14.9, 17.5), "yellow"))
        return els

    variants_block("l3999-walkwayend", "Walkway Comb Plate", [("dir", ["n", "e", "s", "w"])], walkwayend, rot="dir", box=(0, 0, 0, 1, 1, 1),
                   material="Metal", sounds=METAL,
                   data={"sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True}, "lightAbsorption": 99, "drops": [],
                         "attributes": dict(FIXED)},
                   comment="Level 3999: a steel comb plate at the end of a moving walkway, ramping from the tread (15 px) up to the floor (16 px) "
                           "toward the side named (its yellow teeth reach over the tread on the opposite side)")

    def rail(skirt_neon, colour, handrail="rubber"):
        """A railing along the north edge of its block (its suffix names the edge it stands on)."""
        return [bx("Skirt", (0, 0, 0), (16, 3, 2), "steel"), tube("Neon", (0, 1, 2), (16, 1.8, 2.3), colour),
                glass(bx("Glass", (0, 3, 0.75), (16, 14, 1.25), "glasspane", faces=("north", "south", "up"))),
                bx("Post0", (0.2, 3, 0.4), (1.4, 14, 1.6), "chrome"), bx("Post1", (8.2, 3, 0.4), (9.4, 14, 1.6), "chrome"),
                bx("Handrail", (0, 14, 0), (16, 16, 2), handrail)]

    variants_block("l3999-walkwayrail", "Walkway Rail", [("facing", SIDES)], lambda v: rail(True, "cyan"), rot="facing",
                   box=(0, 0, 0, 1, 1, 0.125), material="Glass", sounds=GLASS,
                   data={"lightHsv": [33, 6, 5], "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a moving walkway's balustrade, standing on the edge of its block named by the suffix: a glass panel, "
                           "a black rubber handrail, a steel skirt with a cyan neon strip on its inner face (light 5)")

    variants_block("l3999-balustrade", "Balustrade", [("facing", SIDES)], lambda v: rail(True, "magenta", "chrome"), rot="facing",
                   box=(0, 0, 0, 1, 1, 0.125), material="Glass", sounds=GLASS,
                   data={"lightHsv": [51, 7, 5], "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's mezzanines: a railing on the gallery edge named by the suffix (the side the atrium is on): a glass "
                           "panel, a chrome handrail, a base channel with a magenta neon strip (light 5)")

    # Escalators: four steps a block climbing toward the side named; collision as stairs
    def escalator(v):
        els = []
        for k in range(4):
            z1, z2 = 12 - 4 * k, 16 - 4 * k
            els.append(faces_box(f"Step{k}", (0, max(0, 4 * k - 4), z1), (16, 4 * k + 4, z2),
                                 {"up": "stairtread", "south": "riser", "down": "darksteel", "east": "darksteel", "west": "darksteel"}))
        return els

    coll = [(0, 0, 0, 1, 0.5, 1), (0, 0.5, 0, 1, 1, 0.5)]
    variants_block("l3999-escalator", "Escalator", [("facing", SIDES)], escalator, rot="facing", box=coll, material="Metal", sounds=METAL,
                   data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: an escalator's steps, ribbed steel with yellow nosing, four steps a block climbing toward the side named "
                           "(one block up per block across); walked like stairs")

    L45 = 16 * math.sqrt(2)

    def incline(nm, x1, x2, a, b, texture, glowing=0):
        zc = 8 - (a + b) / 2
        el = bx(nm, (x1, 8 + a, zc - L45 / 2), (x2, 8 + b, zc + L45 / 2), texture, glow=glowing)
        return rot(el, rx=45, origin=((x1 + x2) / 2, 8, 8))

    def escrail(v):
        x1, x2 = (0, 2) if v["side"] == "left" else (14, 16)
        gx1, gx2 = x1 + 0.75, x1 + 1.25
        nx = (x2, x2 + 0.3) if v["side"] == "left" else (x1 - 0.3, x1)
        return [incline("Skirt", x1, x2, -11.4, 3, "steel"), incline("Neon", nx[0], nx[1], 0.5, 1.3, "neon-cyan", 255),
                glass(incline("Glass", gx1, gx2, 3, 13.5, "glasspane")), incline("Rail", x1, x2, 13.5, 15.5, "rubber")]

    variants_block("l3999-escalatorrail", "Escalator Rail", [("side", ["left", "right"]), ("facing", SIDES)], escrail, rot="facing",
                   boxes=lambda v: ((0, 0, 0, 0.125, 1, 1) if v["side"] == "left" else (0.875, 0, 0, 1, 1, 1)), material="Glass", sounds=GLASS,
                   data={"lightHsv": [33, 6, 5], "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: an escalator's sloped balustrade, rising toward the side named one block per block, on the left or "
                           "right edge of its block as you climb (left is the west edge when climbing north); a cyan strip on its inner face")


def service():
    # Roller shutters over closed units
    def shutter(v):
        els = []
        upper = v["part"] == "upper"
        top = 12 if upper else 16
        for i in range(int(top // 2)):
            y = i * 2
            els.append(faces_box(f"Slat{i}", (0, y, 6.5), (16, y + 2, 9.5), {"north": "shutter-stencil" if not upper else "shutter",
                                                                              "south": "shutter", "up": "shutter", "down": "shutter"}))
            els[-1]["faces"]["north"]["uv"] = [0, 16 - y - 2, 16, 16 - y]
            els.append(bx(f"Lip{i}", (0, y + 1.6, 6.1), (16, y + 2, 9.9), "steel", faces=("up", "down")))
        els += [bx("GuideL", (0, 0, 5), (1, 16, 11), "darksteel"), bx("GuideR", (15, 0, 5), (16, 16, 11), "darksteel")]
        if upper:
            els += [bx("Box", (0, 12, 3.5), (16, 16, 12.5), "darksteel"), bx("Lock", (7, 0.5, 5.6), (9, 2, 6.5), "chrome")]
        else:
            els += [bx("Handle", (6, 2, 5.6), (10, 2.8, 6.5), "chrome")]
        return els

    variants_block("l3999-shutter", "Roller Shutter", [("part", ["lower", "upper"]), ("facing", SIDES)], shutter, rot="facing",
                   box=(0, 0, 0.3, 1, 1, 0.7), material="Metal", sounds=METAL,
                   data={"lightAbsorption": 99, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999: a ribbed grey roller shutter over a closed unit, CLOSED FOR REFIT stencilled on the lower block "
                           "(the face named); the upper block has the shutter's housing")

    CLEAR = "clear"

    # The revolving door: the centre block draws all of it (oversized, 3 wide and 3 high); side and top are collision
    def revolving(v):
        part = v["part"]
        if part != "center":
            return [bx("Nothing", (7.9, 7.9, 7.9), (8.1, 8.1, 8.1), CLEAR, faces=("up",))]
        els = cyl("Post", 8, 8, 1, 0, 40, "chrome")
        for k in range(4):
            a = 45 + k * 90
            els.append(rot(glass(bx(f"Wing{k}", (7.6, 1, 9), (8.4, 38, 29), "glasspane")), ry=a, origin=(8, 0, 8)))
            els.append(rot(bx(f"WingEdge{k}", (7.4, 1, 28.4), (8.6, 38, 29.4), "chrome"), ry=a, origin=(8, 0, 8)))
            els.append(rot(bx(f"WingFoot{k}", (7.5, 0.5, 9), (8.5, 1.5, 29), "rubber"), ry=a, origin=(8, 0, 8)))
        # The curved drum walls on the east and west, open to the north and the south
        for side in (-1, 1):
            for j in range(5):
                a = -50 + j * 25
                panel_ = bx(f"Drum{side}{j}", (8 + side * 21.4 - 0.4, 0, 8 - 4.8), (8 + side * 21.4 + 0.4, 40, 8 + 4.8), "glasspane")
                els.append(rot(glass(panel_), ry=a, origin=(8, 0, 8)))
            els.append(rot(bx(f"Jamb{side}a", (8 + side * 21.6 - 0.8, 0, 8 - 0.8), (8 + side * 21.6 + 0.8, 40, 8 + 0.8), "chrome"), ry=62.5, origin=(8, 0, 8)))
            els.append(rot(bx(f"Jamb{side}b", (8 + side * 21.6 - 0.8, 0, 8 - 0.8), (8 + side * 21.6 + 0.8, 40, 8 + 0.8), "chrome"), ry=-62.5, origin=(8, 0, 8)))
        # Canopy and floor ring: octagons of boxes
        for k in range(4):
            els.append(rot(bx(f"Canopy{k}", (-14, 40, -1), (30, 48, 17), "canopy"), ry=k * 45, origin=(8, 40, 8)))
            els.append(rot(bx(f"Floor{k}", (-14, -0.01, -1), (30, 0.2, 17), "darksteel", faces=("up",)), ry=k * 45, origin=(8, 0, 8)))
        els.append(rot(tube("CanopyNeon", (-14.3, 41, 7), (30.3, 42, 9), "magenta"), ry=0, origin=(8, 41, 8)))
        return els

    def rev_box(v):
        return (0.4, 0, 0.4, 0.6, 1, 0.6) if v["part"] == "center" else (0, 0, 0, 1, 1, 1)

    variants_block("l3999-revolvingdoor", "Revolving Door", [("part", ["center", "side", "top"]), ("facing", SIDES)], revolving, rot="facing",
                   boxes=rev_box, material="Glass", sounds=GLASS,
                   data={"behaviors": threshold("l3999-revolving"), "drops": [], "attributes": dict(FIXED),
                         "lightHsvByType": {"*-center-*": [51, 7, 6]}},
                   comment="Level 3999's lobbies (and the Level 10 arcade): a revolving door 3 wide and 3 high. The center block (on the floor, "
                           "in the middle) draws the whole drum: four glass wings on a chrome post, curved glass walls east and west, a dark "
                           "canopy with a neon edge; side (left and right of it) and top (the six above) are invisible collision. Use it to go "
                           "through (threshold kind l3999-revolving)")

    def door_leaf(upper, sign_tex, leaf_tex, frame_tex="darksteel", glow_frame=0):
        els = [bx("JambL", (0, 0, 5), (2, 16, 11), frame_tex, glow=glow_frame), bx("JambR", (14, 0, 5), (16, 16, 11), frame_tex, glow=glow_frame)]
        if upper:
            els.append(bx("Head", (0, 12, 5), (16, 16, 11), frame_tex, glow=glow_frame))
        leaf_top = 12 if upper else 16
        leaf = faces_box("Leaf", (2, 0, 7), (14, leaf_top, 9), {"north": leaf_tex, "south": leaf_tex, "up": leaf_tex})
        els.append(leaf)
        return els

    def staffdoor(v):
        upper = v["part"] == "upper"
        els = door_leaf(upper, None, "doorsteel")
        if upper:
            els.append(picture(bx("Sign", (4, 3, 6.6), (12, 9, 7), "staffsign", faces=("north",)), "staffsign"))
        else:
            els += [bx("Plate", (11, 2, 6.4), (13, 10, 7), "chrome"), bx("PlateS", (11, 2, 9), (13, 10, 9.6), "chrome"),
                    bx("Kick", (2, 0, 6.6), (14, 2, 7), "steel")]
        return els

    variants_block("l3999-staffdoor", "STAFF ONLY Door", [("part", ["lower", "upper"]), ("facing", SIDES)], staffdoor, rot="facing",
                   box=(0, 0, 0.3, 1, 1, 0.7), material="Metal", sounds=METAL,
                   data={"behaviors": threshold("l3999-staff"), "lightAbsorption": 99, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's service corridors: a grey steel door with a push plate, STAFF ONLY on the upper block (the face named). "
                           "Most are locked; some lead to the Hub (threshold kind l3999-staff)")

    def elevator(v):
        upper = v["part"] == "upper"
        # (on the upper part the posts stop under the head, not running through it face to face)
        post = 14 if v["part"] == "upper" else 16
        els = [tube("FrameL", (0, 0, 5), (2, post, 7), "pink"), tube("FrameR", (14, 0, 5), (16, post, 7), "pink"),
               bx("Back", (0, 0, 7), (16, 16, 11), "darksteel", faces=("south", "east", "west", "up", "down"))]
        top = 12 if upper else 16
        els += [bx("DoorL", (8.1, 0, 6.6), (14, top, 7.6), "plumsteel"), bx("DoorR", (2, 0, 6.6), (7.9, top, 7.6), "plumsteel")]
        if upper:
            els += [tube("FrameT", (0, 12, 5), (16, 14, 7), "pink"), bx("Head", (0, 14, 5), (16, 16, 7), "darksteel"),
                    picture(bx("Floor", (6, 14.3, 4.7), (10, 15.7, 5), "lcd", faces=("north",)), "lcd", glow=200)]
        return els

    variants_block("l3999-elevator", "Arcade Elevator", [("part", ["lower", "upper"]), ("facing", SIDES)], elevator, rot="facing",
                   box=(0, 0, 0.3, 1, 1, 0.7), material="Metal", sounds=METAL,
                   data={"behaviors": threshold("l3999-elevator"), "lightHsv": [62, 7, 6], "lightAbsorption": 0, "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's mini arcades: brushed plum elevator doors in a neon-pink frame (the face named), a floor display above. "
                           "It goes to Level 0 (threshold kind l3999-elevator; light 6)")

    def keypad(v):
        els = [bx("Plate", (5, 5, -1), (11, 14, 0), "darksteel"),
               picture(bx("LCD", (6, 11.5, -1.3), (10, 13.2, -1), "lcd", faces=("north",)), "lcd", glow=200)]
        for r in range(3):
            for c in range(3):
                x, y = 6 + c * 1.5, 6.2 + r * 1.6
                els.append(bx(f"Key{r}{c}", (x, y, -1.6), (x + 1, y + 1, -1), "keybutton"))
        return hang(els)

    variants_block("l3999-keypad", "Keypad", [("facing", SIDES)], keypad, rot="facing", box=(0.3, 0.3, 0.9, 0.7, 0.9, 1), collide=False,
                   material="Metal", sounds=METAL, data={"lightHsv": [21, 4, 2], "drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's mini arcades: a 3 x 3 keypad with a tiny green display beside the elevator, on the wall behind it")

    def ticketpile(v):
        els = [bx("Tray", (1, 0, 1), (15, 1, 15), "tray"), bx("RimN", (1, 1, 1), (15, 2, 1.6), "tray"), bx("RimS", (1, 1, 14.4), (15, 2, 15), "tray")]
        heaps = [(3, 3, 6, 2.2), (8, 4, 5, 3.4), (5, 9, 7, 2.6), (10, 9, 4, 1.8)]
        for i, (x, z, w, h) in enumerate(heaps):
            els.append(bx(f"Heap{i}", (x, 1, z), (x + w, 1 + h, z + w * 0.8), "tickets"))
        for i, (x, z, a) in enumerate(((2, 12, 20), (11, 2, -30), (12, 12, 60))):
            els.append(rot(bx(f"Strip{i}", (x, 1, z), (x + 4, 1.3, z + 1.2), "tickets"), ry=a))
        return els

    variants_block("l3999-ticketpile", "Pile of Tickets", [], ticketpile, box=(0.06, 0, 0.06, 0.94, 0.3, 0.94), material="Cloth", sounds=CLOTH,
                   data={"drops": drops(("l3999-ticket", 4.5, 1.5))},
                   comment="Level 3999's mini arcades: a heap of red tickets on a tray (on a table). Salvage: 3-6 tickets")

    def debris(v):
        els = []
        for i, (x, z, a, rx_, y) in enumerate(((0, 1, 10, 8, 0), (6, 5, -25, -10, 1), (2, 8, 40, 14, 1.5), (8, 0, 70, 6, 2.2))):
            els.append(rot(bx(f"Panel{i}", (x, y, z), (x + 8, y + 0.8, z + 8), "debris"), rx=rx_, ry=a))
        els += [bx("Wire", (3, 0, 12), (13, 0.4, 12.4), "rubber"), rot(bx("Strut", (1, 0.5, 6), (15, 1.3, 6.8), "darksteel"), ry=15)]
        return els

    variants_block("l3999-ceilingdebris", "Fallen Ceiling", [], debris, box=(0, 0, 0, 1, 0.25, 1), material="Wood",
                   data={"drops": drops(("scrapwire", 0.4, 0.3), ("metalbracket", 0.3, 0.3), ("l3999-plastic", 0.4, 0.3), ("rottenwood", 0.2, 0.2))},
                   comment="Level 3999.1: a heap of fallen dark ceiling panels. Salvage: wire, brackets, plastic from the light diffusers")

    def lounger(v):
        els = []
        for i in range(5):
            els.append(bx(f"Slat{i}", (2, 6, 1 + i * 2), (14, 6.8, 2.6 + i * 2), "loungerslat"))
        for i in range(3):
            els.append(rot(bx(f"Back{i}", (2, 6, 11 + i * 1.6), (14, 6.8, 12.2 + i * 1.6), "loungerslat"), rx=35, origin=(8, 6, 11)))
        for x in (2, 13):
            els += [bx(f"Frame{x}", (x, 5, 0.5), (x + 1, 6, 15.5), "white"), bx(f"LegF{x}", (x, 0, 1), (x + 1, 5, 2), "white"),
                    bx(f"LegB{x}", (x, 0, 13.5), (x + 1, 5, 14.5), "white")]
        return els

    variants_block("l3999-lounger", "Pool Lounger", [("facing", SIDES)], lounger, rot="facing", box=(0.12, 0, 0, 0.88, 0.5, 1), material="Wood",
                   data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 3999's Neon Natatorium: a white slatted pool lounger, its back raised at the south end when it faces north")

    def drain(v):
        els = [bx("Pit", (0, 0, 0), (16, 13, 16), "drainhole", faces=("up",)),
               faces_box("Wall", (0, 0, 0), (16, 16, 16), {"north": "pooltile-violet", "east": "pooltile-violet", "south": "pooltile-violet",
                                                         "west": "pooltile-violet", "down": "pooltile-violet"}),
               bx("Frame", (0, 15, 0), (16, 16, 1.5), "grate"), bx("FrameS", (0, 15, 14.5), (16, 16, 16), "grate"),
               bx("FrameW", (0, 15, 1.5), (1.5, 16, 14.5), "grate"), bx("FrameE", (14.5, 15, 1.5), (16, 16, 14.5), "grate")]
        for i in range(6):
            x = 2.2 + i * 2.1
            els.append(bx(f"Bar{i}", (x, 15, 1.5), (x + 0.9, 16, 14.5), "grate"))
        return els

    variants_block("l3999-drain", "Pool Drain", [], drain, box=(0, 0, 0, 1, 1, 1), material="Metal", sounds=METAL,
                   data={"sidesolid": {"all": True, "up": False}, "sideopaque": {"all": True, "up": False}, "lightAbsorption": 99, "drops": [],
                         "attributes": dict(FIXED)},
                   comment="Level 3999's Neon Natatorium: a steel grate over black in a deep end's floor (the way down to Level 37: dive to it)")

    def curb(v):
        return [bx("Kerb", (0, 0, 2), (16, 4, 16), "curb"), bx("Lip", (0, 0, 0.5), (16, 3, 2), "curb"),
                bx("Round", (0, 3, 1), (16, 3.6, 2), "curb")]

    variants_block("l3999-curb", "Kerb", [("facing", SIDES)], curb, rot="facing", box=(0, 0, 0, 1, 0.25, 1), material="Stone", sounds=STONE,
                   data={"drops": [], "attributes": dict(FIXED)},
                   comment="The Level 10 arcade's car park: a concrete kerb 4 px high with a rounded lip on the side it faces")


# ======================================================================== 6.5 Level 10's windmills

def windmills():
    cube_block("l3999-windmill", "Windmill", {"wall": "weatherboard", "cap": "shingle"},
               "Level 10's windmills (the way to 3999): white-washed weatherboard walls; a dark shingled cap", material="Wood", sounds=WOOD,
               names={"l3999-windmill-wall": "Windmill Weatherboard", "l3999-windmill-cap": "Windmill Cap"})

    def sails(v):
        els = [bx("Hub", (6, 6, 6), (10, 10, 10), "sailwood"), bx("Shaft", (7, 7, 10), (9, 9, 16), "darksteel")]
        for k in range(4):
            a = 45 + k * 90
            arm = [bx(f"Stock{k}", (7.25, 10, 5.6), (8.75, 72, 7.1), "sailwood")]
            for side in (1,):
                x1, x2 = (8.75, 18.5)
                arm += [bx(f"RailO{k}", (x2 - 1, 22, 6), (x2, 72, 7), "sailwood"), bx(f"RailI{k}", (x1, 22, 6), (x1 + 0.6, 72, 7), "sailwood")]
                for j in range(13):
                    y = 23 + j * 4
                    arm.append(bx(f"Bar{k}{j}", (x1, y, 6.1), (x2, y + 0.7, 6.9), "sailwood"))
                for j in range(3):
                    y = 24 + j * 16
                    arm.append(bx(f"Cloth{k}{j}", (x1 + 0.6, y, 6.35), (x2 - 1, y + 14, 6.65), "canvas", faces=("north", "south")))
            for e in arm:
                els.append(rot(e, rz=a, origin=(8, 8, 6.35)))
        return els

    variants_block("l3999-windmillsails", "Windmill Sails", [("facing", SIDES)], sails, rot="facing", box=(0.25, 0.25, 0.25, 0.75, 0.75, 1),
                   material="Wood", sounds=dict(WOOD, ambient="backrooms:ambient/3999/windmill", ambientBlockCount=1),
                   data={"drops": [], "attributes": dict(FIXED)},
                   comment="Level 10's windmills: four lattice sails in an X, each 4 blocks long, canvas strips on a frame, on a hub drawn "
                           "from one block (oversized; static at 45 degrees); the sails face the way named, the shaft runs back into the cap")

    def generator(v):
        on = v["state"] == "on"
        els = [bx("Box", (3, 2, -6), (13, 14, 0), "gengreen"), bx("Lid", (2.6, 13.5, -6.4), (13.4, 14.5, 0), "gengreen"),
               picture(bx("Dial", (4.5, 9, -6.3), (8.5, 13, -6), "dial", faces=("north",)), "dial"),
               bx("Vent0", (4.5, 3.5, -6.2), (8.5, 4.2, -6), "black"), bx("Vent1", (4.5, 5, -6.2), (8.5, 5.7, -6), "black"),
               bx("Pivot", (9.5, 7, -7), (12, 9, -6), "darksteel"),
               bx("Lamp", (9.8, 11, -6.6), (11.8, 13, -6), "greenlight" if on else "bulb-red-off", glow=200 if on else 0)]
        a = -20 if on else 160
        els += [rot(bx("Lever", (10.25, 8, -9), (11.25, 17, -8), "redlight"), rx=a, origin=(10.75, 8, -8.5)),
                rot(bx("Knob", (9.9, 16, -9.4), (11.6, 18, -7.6), "rubber"), rx=a, origin=(10.75, 8, -8.5))]
        return hang(els)

    variants_block("l3999-generator", "Windmill Generator", [("state", ["off", "on"]), ("facing", SIDES)], generator, rot="facing",
                   box=(0.15, 0.1, 0.55, 0.85, 1, 1), material="Metal", sounds=METAL,
                   data=with_class({"drops": [], "attributes": dict(FIXED), "lightHsvByType": {"*-on-*": [21, 6, 4]}}, cls="BackroomsWindmillGenerator"),
                   comment="Level 10's windmills: a green steel generator on the wall behind it, a big red lever (down: off; up: on) and a dial. "
                           "Throwing it turns the windmill's beacon green, for good")


def generate():
    surfaces()
    neon()
    lobby()
    food()
    concourse()
    service()
    windmills()
    LANG.update({
        "block-l3999-revolvingdoor-*": "Revolving Door", "block-l3999-staffdoor-*": "STAFF ONLY Door", "block-l3999-elevator-*": "Arcade Elevator",
        "block-l3999-windmillsails-*": "Windmill Sails", "block-l3999-generator-*": "Windmill Generator", "block-l3999-beacon-*": "Windmill Beacon",
        "block-l3999-neonceiling-*": "Neon Tube", "block-l3999-neonwall-*": "Neon Tube", "block-l3999-neonrail-*": "Neon Base Strip",
        "block-l3999-lamppost-*": "Sodium Lamp", "blockhelp-l3999-directory": "Find the way", "blockhelp-l3999-generator": "Throw the lever",
        "blockhelp-l3999-stall": "Buy a meal (6 tickets)", "blockhelp-l3999-vending": "Insert Almond Water",
    })
