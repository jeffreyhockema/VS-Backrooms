"""Level 188, the Courtyard of Windows (tag `188`, id 20, blocks `l188-`): every asset of docs/design/new-levels/188-plan.md
section 4, as amended by the plan's "Manifest changes (phase 2)" (which wins where they differ).

    bash tools/locked.sh run python tools/gen_188.py [tex] [blocks] [models] [sounds] [lang]   (no argument: all)

Writes only Level 188's own folders: textures/block/188/, textures/item/188/, textures/gui/188/, shapes/block/188/,
blocktypes/188/, itemtypes/188/, shapes/entity/188/ and textures/entity/188/ (the arm), entities/l188-arm.json,
sounds/ambient/188/ and sounds/effect/188/; the level's lang keys are merged into lang/en.json in place (the scaffold's
placeholders for level 20 are replaced where they stand). Its own block, shape and item folders are emptied first,
so a renamed code leaves nothing stale behind.

Modules: gen_188_kit (files, boxes, block types), gen_188_tex (textures), gen_188_props (furniture, the windows into
188 in other levels, items), gen_188_models (the Window's arm), gen_188_sounds (sounds). This file: the courtyard,
the hotel's structure, the windows, doors and signs, the lang, and the final check.

Every model faces north (toward -Z) and is turned for the other sides. Real 3D detail: window frames, blinds and
their rolls, sills, the deck's boards cut along their arcs, the hatch's ring, door levers and card readers, the
fire door's push bar, skirting, downlights; only the places seen through windows are painted (they are not there).
"""
import json
import math
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
from gen_188_kit import (  # noqa: E402
    ALL, ASSETS, CLOTH, COUNT, GLASS, GRASS, GRAVEL, LANG, METAL, PARTS, ROTATE, SIDES, STONE, WOOD, WRITTEN,
    block, bx, bxa, bxf, clip, cube, cube_block, cuboid, cyl, drops, facing_faces, merge_lang, mirror_x, reg,
    retex, shape, split, split_boxes, tpath, vblock, vox, vx,
)

FIXED = {"attributes": {"l188structure": True}}
OPAQUE_JSON = {"sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 6, "drops": []}


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


def behaviours(*names):
    """The code's own behaviours, named only once the code registers them (an unknown name fails the block's load)."""
    return [{"name": n} for n in names if reg(n)]


def with_behaviours(data, *names):
    b = behaviours(*names)
    if b:
        data = dict(data)
        data["behaviors"] = data.get("behaviors", []) + b
    return data


# ======================================================================== Structure

def structure():
    # ---- Void, sky, shaft: dead black, no light
    for code, tex, eng, note in (("l188-nothing", "nothing", "Nothing", "Level 188: what lies round the building and behind its outer windows"),
                                 ("l188-sky", "sky", "Black Sky", "Level 188: the sky over the courtyard, rel 33, a black the eye cannot focus on"),
                                 ("l188-shaft", "shaft", "Black Shaft", "Level 188: the lining of the shaft under the hatch")):
        cube_block(code, eng, [], lambda v, t=tex: {"all": t}, data=dict(FIXED, resistance=999), comment=note)

    # ---- The courtyard ground (rel 0)
    cube_block("l188-paver", "Concrete Pavers", [("kind", ["plain", "moss", "cracked"])],
               lambda v: {"up": "paver-" + v["kind"], "down": "concrete", "north": "concrete", "east": "concrete", "south": "concrete", "west": "concrete"},
               data=FIXED, comment="Level 188: pale concrete pavers in running bond (moss in the joints; a hairline crack and a stain)",
               names={"l188-paver-*": "Concrete Pavers", "l188-paver-moss": "Mossy Pavers", "l188-paver-cracked": "Cracked Pavers"})
    cube_block("l188-turf", "Moss Turf", [("kind", ["a", "b"])],
               lambda v: {"up": "turf-" + v["kind"], "down": "soil", "north": "turf-side-" + v["kind"], "east": "turf-side-" + v["kind"],
                          "south": "turf-side-" + v["kind"], "west": "turf-side-" + v["kind"]},
               data=FIXED, sounds=GRASS, comment="Level 188: the lawns, dense moss-grass with damp patches (b a little yellower)")

    # ---- Façade render: on the front face and both ends, room white behind
    cube_block("l188-cladding", "Rendered Wall", [("kind", ["plain", "band", "streak"]), ("side", SIDES)],
               lambda v: facing_faces(v["side"], "cladding-" + v["kind"], "wall-room", "cladding-plain"),
               data=dict(FIXED, randomizeAxes="xyz"),
               comment="Level 188: the courtyard façade, pale warm render (band: a floor line; streak: rain below a sill); the side is the courtyard face",
               names={"l188-cladding-*": "Rendered Wall"})

    # ---- Cubes for floors that are not slabs (and for building with)
    for code, top, eng, snd in (("l188-roof", "roof", "Roof Membrane", STONE), ("l188-carpet-corridor", "carpet-corridor", "Corridor Carpet", CLOTH),
                                ("l188-carpet-room", "carpet-room", "Room Carpet", CLOTH), ("l188-tile-lobby", "tile-lobby", "Porcelain Tile", STONE),
                                ("l188-tile-bath", "tile-bath", "Bathroom Tile", STONE), ("l188-concrete-stair", "concrete-stair-edge", "Painted Concrete", STONE)):
        cube_block(code, eng, [], lambda v, t=top: {"up": t, "down": "concrete", "north": "concrete", "east": "concrete", "south": "concrete", "west": "concrete"},
                   data=FIXED, sounds=snd, comment=f"Level 188: {eng.lower()}")

    # ---- Walls
    cube_block("l188-wall-room", "Wall", [], lambda v: {"all": "wall-room"}, data=FIXED,
               comment="Level 188: room white on every face (partitions, outer façade, lobby)")
    cube_block("l188-wall-stair", "Painted Blockwork", [], lambda v: {"all": "wall-stair"}, data=FIXED,
               comment="Level 188: the stair hall's painted blockwork (also the fill under the flights)")
    cube_block("l188-wall-room-feature", "Feature Wall", [("side", SIDES)],
               lambda v: facing_faces(v["side"], "wall-feature", "wall-room", "wall-room"), data=FIXED,
               comment="Level 188: the slate-blue headboard wall on the side face, white behind")

    def corridor_wall(v):
        c = cube("wall-corridor", {"south": "wall-room"})
        els = [c]
        if v["kind"] == "base":
            els += [bx("Skirting", (0, 0, -1), (16, 2, 0), "skirting", faces=("north", "up", "east", "west")),
                    bx("SkirtingTop", (0, 2, -0.6), (16, 2.4, 0), "skirting", faces=("north", "up", "east", "west"))]
        return els

    vblock("l188-wall-corridor", "Corridor Wall", [("kind", ["plain", "base"]), ("side", SIDES)], corridor_wall, box=(0, 0, 0, 1, 1, 1),
           data=dict(OPAQUE_JSON, **FIXED), material="Stone", sounds=STONE,
           comment="Level 188: light grey vinyl wallpaper on the side face (toward the corridor), room white behind; base: a white 3D skirting")

    # ---- Slabs: one block is the ceiling below and the floor above
    zones = {"corridor": ("carpet-corridor", CLOTH), "room": ("carpet-room", CLOTH), "lobby": ("tile-lobby", STONE),
             "stair": ("concrete-stair", STONE), "bath": ("tile-bath", STONE), "roof": ("roof", STONE)}
    cube_block("l188-slab", "Floor Slab", [("zone", list(zones))],
               lambda v: {"up": zones[v["zone"]][0], "down": "ceiling", "north": "concrete", "east": "concrete", "south": "concrete", "west": "concrete"},
               data=dict(FIXED, soundsByType={f"l188-slab-{z}": s for z, (_, s) in zones.items()}),
               comment="Level 188: a storey slab, the floor on top (charcoal carpet, grey carpet, porcelain, painted concrete, white tile, roof membrane), white ceiling below")

    # ---- Downlights: the slab with a round recessed light in its underside
    def downlight(v):
        on = v["state"] != "off"
        g = 255 if on else 0
        lens = "lens-on" if on else "lens-off"
        top = zones[v["zone"]][0]
        c = cube("concrete", {"up": top, "down": "ceiling"})
        return [c,
                bx("Ring", (5, -0.25, 6.2), (11, 0, 9.8), "chrome", faces=("north", "east", "south", "west", "down")),
                bx("Ring2", (6.2, -0.25, 5), (9.8, 0, 11), "chrome", faces=("north", "east", "south", "west", "down")),
                bx("Lens", (5.5, -0.45, 6.6), (10.5, -0.25, 9.4), lens, glow=g, faces=("north", "east", "south", "west", "down")),
                bx("Lens2", (6.6, -0.45, 5.5), (9.4, -0.25, 10.5), lens, glow=g, faces=("north", "east", "south", "west", "down"))]

    dz = ["corridor", "room", "lobby", "stair", "roof"]  # roof: storey 4's ceiling, the roof membrane on top
    light = {}
    for z in dz:
        hsv = [7, 2, 14] if z == "lobby" else [7, 2, 12]
        light[f"l188-downlight-{z}-on"] = hsv
        light[f"l188-downlight-{z}-flicker"] = hsv
    vblock("l188-downlight", "Downlight", [("zone", dz), ("state", ["on", "off", "flicker"])], downlight, rot=None, box=(0, 0, 0, 1, 1, 1),
           data=dict(OPAQUE_JSON, **{
               "attributes": {"l188structure": True},
               "lightHsvByType": light,
               # A lit lamp must not absorb its own light, or worldgen lighting spreads none of it
               "lightAbsorptionByType": {"*-on": 0, "*-flicker": 0, "*": 99},
               "entityClassByType": {"*-flicker": "BackroomsFlicker"},
               "attributesByType": {f"l188-downlight-{z}-flicker": {"l188structure": True, "offBlock": f"backrooms:l188-downlight-{z}-off"} for z in dz} | {"*": {"l188structure": True}},
               "soundsByType": {f"l188-downlight-{z}-*": zones[z][1] for z in dz},
           }), material="Stone", sounds=STONE,
           comment="Level 188: a storey slab with a round recessed downlight in its underside (a 5-voxel disc in a chrome ring); flicker swaps to -off")
    LANG["block-l188-downlight-*"] = "Downlight"

    # ---- Sill under every courtyard window (rel 4s+1): render below, a concrete sill projecting toward the side
    def sill(v):
        return [cube("cladding-plain", {"south": "wall-room"}),
                bx("Sill", (-0.2, 14.6, -2), (16.2, 16.03, 1), "sillstone", faces=("north", "up", "down", "east", "west")),
                bx("Drip", (-0.2, 14, -2), (16.2, 14.6, -1.3), "sillstone", faces=("north", "down", "east", "west", "south"))]

    vblock("l188-sill", "Window Sill", [("side", SIDES)], sill, box=(0, 0, 0, 1, 1, 1), data=dict(OPAQUE_JSON, **FIXED),
           material="Stone", sounds=STONE, comment="Level 188: render under a courtyard window, a concrete sill with a drip groove projecting toward the side")

    # ---- Parapet coping (rel 21): render below, a cap overhanging both faces, its drip toward the side
    def coping(v):
        return [bx("Body", (0, 0, 0), (16, 14, 16), "cladding-plain", faces=("north", "east", "south", "west", "down")),
                bx("Cap", (0, 14, -1), (16, 16, 17), "sillstone"),
                bx("Drip", (0, 13.4, -1), (16, 14, -0.4), "sillstone", faces=("north", "down", "east", "west", "south"))]

    vblock("l188-coping", "Parapet Coping", [("side", SIDES)], coping, box=(0, 0, 0, 1, 1, 1), data=dict(OPAQUE_JSON, **FIXED),
           material="Stone", sounds=STONE, comment="Level 188: the parapet round the roof (rel 21), a concrete cap overhanging both faces, its drip toward the side")

    # ---- Roof gravel (rel 21): a loose layer, walked through
    def gravel(v):
        return [bx("Layer", (0, 0, 0), (16, 1.4, 16), "roofgravel"),
                bx("Heap1", (2, 1.4, 3), (7, 2, 8), "roofgravel"), bx("Heap2", (9, 1.4, 9), (14, 2, 13), "roofgravel"),
                bx("Heap3", (10, 1.4, 1), (13, 1.8, 4), "roofgravel")]

    vblock("l188-roofgravel", "Roof Gravel", [], gravel, rot=None, box=None, collide=False, sel=lambda v: (0, 0, 0, 1, 0.125, 1),
           data={"drops": [], "replaceable": 4000, "resistance": 1}, material="Gravel", sounds=GRAVEL,
           comment="Level 188: loose gravel on the roof membrane (rel 21), 2 voxels deep; walk through it")
    LANG["block-l188-roofgravel"] = "Roof Gravel"

    # ---- Moss tufts (rel 1 on the lawns): six little crossed tufts
    def tufts(v):
        els = []
        for i, (x, z, h) in enumerate(((3, 4, 5), (8, 2.5, 3.5), (12.5, 5, 6), (5, 11, 4), (10, 12.5, 5.5), (13.5, 10, 3))):
            w = h * 0.8
            els.append(bx(f"Tuft{i}a", (x - w / 2, 0, z), (x + w / 2, h, z), "mosstuft", faces=("north", "south"), full=True))
            els.append(bx(f"Tuft{i}b", (x, 0, z - w / 2), (x, h, z + w / 2), "mosstuft", faces=("east", "west"), full=True))
        return els

    vblock("l188-mosstuft", "Moss Tuft", [], tufts, rot=None, collide=False, sel=lambda v: (0.1, 0, 0.1, 0.9, 0.35, 0.9),
           data={"drops": [], "replaceable": 5000, "resistance": 0.2, "vertexFlags": {"windMode": "NormalWind"}}, material="Plant", sounds=GRASS,
           comment="Level 188: tufts of moss standing up out of the lawn (rel 1); no collision")
    LANG["block-l188-mosstuft"] = "Moss Tuft"

    # ---- Lawn edging (rel 1 on a lawn tile next to the paving): a timber board standing on the side edge
    def edging(v):
        els = [bx("Board", (0, 0, 0.2), (16, 3, 1.7), "timber", faces=("north", "south", "up")),
               bx("Peg1", (3, 0, 1.7), (4, 2, 2.4), "timber-end"), bx("Peg2", (12, 0, 1.7), (13, 2, 2.4), "timber-end")]
        if v.get("kind") == "corner":
            els = [bx("Board", (0.2, 0, 0.2), (16, 3, 1.7), "timber", faces=("north", "south", "up", "west")),
                   bx("BoardE", (14.3, 0, 1.7), (15.8, 3, 16), "timber", faces=("east", "west", "up")),
                   bx("Peg1", (4, 0, 1.7), (5, 2, 2.4), "timber-end"), bx("Peg2", (13.6, 0, 11), (14.3, 2, 12), "timber-end")]
        return els

    vblock("l188-edging", "Lawn Edging", [("side", SIDES)], edging, collide=False, sel=lambda v: (0, 0, 0, 1, 0.1875, 0.15),
           data={"drops": drops(("game:plank-aged", 0.5, 0)), "resistance": 1}, material="Wood", sounds=WOOD,
           comment="Level 188: a low timber board along the lawn's edge (rel 1, on the lawn tile, the board on the side edge toward the paving); walk over it")
    vblock("l188-edging-corner", "Lawn Edging", [("side", SIDES)], lambda v: edging({"kind": "corner"}), collide=False,
           sel=lambda v: (0, 0, 0, 1, 0.1875, 1), data={"drops": drops(("game:plank-aged", 0.5, 0)), "resistance": 1}, material="Wood", sounds=WOOD,
           comment="Level 188: a lawn's corner edging: boards on the side edge and the next edge clockwise (north: north and east)")

    deck()
    hatch()
    stairs()


def deck():
    """The wooden circle (rel 1): a slab 3 voxels high of weathered boards; round pieces cut along a quarter circle."""
    def slab_boxes(keep):
        els = []
        if keep is None:
            return [bxa("Deck", (0, 0, 0), (16, 3, 16), "deck", faces=("up", "down")),
                    bx("DeckN", (0, 0, 0), (16, 3, 0.01), "deck-side", faces=("north",)),
                    bx("DeckS", (0, 0, 15.99), (16, 3, 16), "deck-side", faces=("south",)),
                    bx("DeckW", (0, 0, 0), (0.01, 3, 16), "deck-side", faces=("west",)),
                    bx("DeckE", (15.99, 0, 0), (16, 3, 16), "deck-side", faces=("east",))]
        for i in range(8):
            x1, x2 = i * 2, i * 2 + 2
            z1, z2 = keep((x1 + x2) / 2)
            if z2 - z1 < 0.3:
                continue
            e = bxa(f"Strip{i}", (x1, 0, z1), (x2, 3, z2), "deck", faces=ALL)
            for f in ("north", "south", "east", "west"):
                retex(e, f, "deck-side")
            els.append(e)
        return els

    vblock("l188-deck", "Wooden Deck", [], lambda v: slab_boxes(None), rot=None, box=(0, 0, 0, 1, 3 / 16, 1),
           data=dict(FIXED, drops=[], resistance=4), material="Wood", sounds=WOOD,
           comment="Level 188: the round wooden deck in the middle of the courtyard (rel 1), weathered boards 3 voxels high")
    LANG["block-l188-deck"] = "Wooden Deck"

    corners = {"ne": (0, 16), "se": (0, 0), "sw": (16, 0), "nw": (16, 16)}  # the disc's centre: the corner opposite the cut one

    def round_piece(v):
        cx, cz = corners[v["corner"]]

        def keep(xm):
            dx = xm - cx
            if abs(dx) >= 16:
                return 0, 0
            h = math.sqrt(256 - dx * dx)
            return max(0, cz - h), min(16, cz + h)
        return slab_boxes(keep)

    vblock("l188-deck-round", "Wooden Deck", [("corner", list(corners))], round_piece, rot=None, box=(0, 0, 0, 1, 3 / 16, 1),
           data=dict(FIXED, drops=[], resistance=4), material="Wood", sounds=WOOD,
           comment="Level 188: the deck's edge: the named corner cut away along a quarter circle of radius 16 voxels (stepped boards)")


def hatch():
    """The iron hatch in the middle of the deck, 2 x 2 (rel 1): one riveted plate with a ring handle on its centre,
    hinged on the north edge for the north quarters and the south edge for the south ones."""
    quarters = {"nw": (0, 0), "ne": (16, 0), "sw": (0, 16), "se": (16, 16)}

    def composite():
        els = []
        for q, (x0, z0) in quarters.items():
            e = bx(f"Plate{q}", (x0, 0, z0), (x0 + 16, 3, z0 + 16), "iron")
            retex(e, "up", f"hatch-{q}", uv=[0, 0, 16, 16])
            els.append(e)
        # the ring handle, 6 across, lying flat on the plate's centre; its staple
        els += [bx("RingN", (14.5, 3, 13), (17.5, 3.6, 13.6), "ring"), bx("RingS", (14.5, 3, 18.4), (17.5, 3.6, 19), "ring"),
                bx("RingW", (13, 3, 14.5), (13.6, 3.6, 17.5), "ring"), bx("RingE", (18.4, 3, 14.5), (19, 3.6, 17.5), "ring"),
                bx("Staple", (15.2, 3, 15.2), (16.8, 3.9, 16.8), "ring")]
        for i, (cx, cz) in enumerate(((13.9, 13.9), (18.1, 13.9), (13.9, 18.1), (18.1, 18.1))):
            ang = 45 if (cx < 16) == (cz < 16) else -45
            els.append(bx(f"RingD{i}", (cx - 1.1, 3, cz - 0.3), (cx + 1.1, 3.6, cz + 0.3), "ring", rot=(0, ang, 0)))
        return els

    def part_els(q):
        x0, z0 = quarters[q]
        return clip(composite(), (x0, -16, z0), (x0 + 16, 32, z0 + 16), (x0, 0, z0))

    FACE_UP = {"up": "north", "down": "south", "north": "down", "south": "up", "east": "east", "west": "west"}
    FLIP_Z = {"north": "south", "south": "north"}

    def axis(els):
        return [e for e in els if not any(k in e for k in ("rotationX", "rotationY", "rotationZ"))]

    def flip_z(els):
        return [dict(e, **{"from": [e["from"][0], e["from"][1], 16 - e["to"][2]], "to": [e["to"][0], e["to"][1], 16 - e["from"][2]],
                           "faces": {FLIP_Z.get(k, k): fv for k, fv in e["faces"].items()}}) for e in els]

    def stand(els):
        """The plate swung up on a hinge along its z = 0 edge: (x, y, z) -> (x, z, 3 - y); its top now faces north."""
        out = []
        for e in els:
            (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
            out.append(dict(e, **{"from": [x1, z1, 3 - y2], "to": [x2, z2, 3 - y1], "faces": {FACE_UP[k]: fv for k, fv in e["faces"].items()}}))
        return out

    def build(v):
        q = v["part"]
        els = part_els(q)
        if v["state"] == "closed":
            return els
        if q[0] == "n":
            return stand(axis(els))
        # the south quarters hinge on their south edge: mirror, stand, mirror back
        return flip_z(stand(flip_z(axis(els))))

    def colbox(v):
        if v["state"] == "closed":
            return (0, 0, 0, 1, 3 / 16, 1)
        return (0, 0, 0, 1, 1, 0.2) if v["part"][0] == "n" else (0, 0, 0.8, 1, 1, 1)

    data = with_behaviours({"drops": [], "resistance": 999, "attributes": {"l188structure": True}}, "BackroomsL188Hatch")
    vblock("l188-hatch", "Iron Hatch", [("state", ["closed", "open"]), ("part", list(quarters))], build, rot=None, boxes=colbox,
           data=data, material="Metal", sounds=METAL,
           comment="Level 188: the iron hatch in the deck (rel 1), one quarter each; open, the plate stands up on its hinge edge (north quarters: the north edge, south quarters: the south edge) over the black shaft")
    LANG["block-l188-hatch-*"] = "Iron Hatch"


def stairs():
    def stair(v):
        low = bx("Low", (0, 0, 0), (16, 8, 16), "concrete")
        retex(low, "up", "concrete-stair")
        high = bx("High", (0, 8, 0), (16, 16, 8), "concrete")
        retex(high, "up", "concrete-stair")
        return [low, high,
                bx("NoseLow", (0, 7.4, 15.4), (16, 8.2, 16.2), "steel", faces=("south", "up", "east", "west")),
                bx("NoseHigh", (0, 15.4, 7.4), (16, 16.2, 8.2), "steel", faces=("south", "up", "east", "west"))]

    vblock("l188-stair", "Concrete Stair", [("side", SIDES)], stair,
           colboxes=lambda v: [(0, 0, 0, 1, 0.5, 1), (0, 0.5, 0, 1, 1, 0.5)],
           data={"sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True}, "drops": [], "resistance": 6,
                 "attributes": {"l188structure": True}}, material="Stone", sounds=STONE,
           comment="Level 188: a concrete stair with steel nosings, ascending toward the side (the scissor stair's flights)")


# ======================================================================== Windows

FRAME_Z = (1, 5)
GLASS_Z = (3, 3.5)


def frame_composite(tex="alu", z=FRAME_Z, outer=1.5, mull=0.5):
    """The 2 x 2 window's frame in composite space: outer edges, the mullion and the transom."""
    z1, z2 = z
    fr = ("north", "south", "east", "west", "up", "down")
    return [bx("FrameL", (32 - outer, 0, z1), (32, 32, z2), tex, faces=fr), bx("FrameR", (0, 0, z1), (outer, 32, z2), tex, faces=fr),
            bx("FrameB", (outer, 0, z1), (32 - outer, outer, z2), tex, faces=fr), bx("FrameT", (outer, 32 - outer, z1), (32 - outer, 32, z2), tex, faces=fr),
            bx("Mullion", (16 - mull, outer, z1), (16 + mull, 32 - outer, z2), tex, faces=fr),
            bx("Transom", (outer, 16 - mull, z1), (32 - outer, 16 + mull, z2), tex, faces=fr)]


# The side jambs only: with the bottom and top bars too the opening was 1.81 blocks high (sill top to head), under the
# player's 1.85, so nobody could climb through. The bars are still drawn; they just no longer stop anyone.
FRAME_BOXES = [(30.5, 0, 1, 32, 32, 5), (0, 0, 1, 1.5, 32, 5)]


def blind_composite(down, z=(13.5, 14), roll_tex="roll", glow_blind=False, cord_x=29.2, room_side=+1):
    """A white roller blind just inside the room face: down (covering the opening) or rolled up, with its roll, the
    bottom bar and a pull cord. room_side +1: the room is at +Z (courtyard windows); -1: at -Z (outer windows)."""
    z1, z2 = z
    rz1, rz2 = (z1 - 1, z2 + 0.6) if room_side > 0 else (z1 - 0.6, z2 + 1)
    els = []
    roll = bx("Roll", (1, 29 if down else 28.4, rz1), (31, 31.2, rz2), roll_tex)
    els.append(roll)
    els += [bx("RollCapL", (30.6, 28.6, rz1 - 0.2), (31.4, 31.4, rz2 + 0.2), "alu"), bx("RollCapR", (0.6, 28.6, rz1 - 0.2), (1.4, 31.4, rz2 + 0.2), "alu")]
    if down:
        tex = "blind"
        el = bxa("Blind", (1.5, 2.5, z1), (30.5, 29, z2), tex, faces=("north", "south"))
        els.append(el)
        els.append(bx("Bar", (1.5, 1.6, z1 - 0.3), (30.5, 2.5, z2 + 0.3), "alu"))
        cy1, cy2 = 6, 29
    else:
        els.append(bx("Bar", (1.5, 27.4, z1 - 0.3), (30.5, 28.4, z2 + 0.3), "alu"))
        cy1, cy2 = 14, 28.4
    cz = z2 + 0.5 if room_side > 0 else z1 - 0.8
    els += [bx("Cord", (cord_x, cy1, cz), (cord_x + 0.3, cy2, cz + 0.3), "cord"),
            bx("Pull", (cord_x - 0.25, cy1 - 1.2, cz - 0.25), (cord_x + 0.55, cy1, cz + 0.55), "cord")]
    if glow_blind:
        for e in els:
            if e["name"] == "Blind":
                for f in e["faces"].values():
                    f["glow"] = 170
    return els


def glass_composite(z=GLASS_Z, tex="glass"):
    return [bx("Glass", (0, 0, z[0]), (32, 32, z[1]), tex, faces=("north", "south"))]


def inner_board(z1=11.5, z2=17):
    return [bx("Board", (0, 0, z1), (32, 1.2, z2), "sillstone", faces=("up", "south", "north"))]


def windows():
    states = ["closed", "glow", "open", "lit", "figure", "beckon"]

    def courtyard_window(v):
        s, part = v["state"], v["part"]
        down = s in ("closed", "glow")
        roll = "roll-lit" if s == "lit" else "roll"
        els = frame_composite() + glass_composite() + inner_board()
        els += blind_composite(down, roll_tex=roll)
        out = split(els, part)
        if s == "glow":
            for e in out:
                if e["name"] == "Blind":
                    for fname, f in e["faces"].items():
                        f["texture"] = f"#blind-glow-{part}"
                        f["glow"] = 170
        if s == "lit":
            for e in out:
                if e["name"] == "Roll":
                    for f in e["faces"].values():
                        f["glow"] = 90
        if s in ("figure", "beckon"):
            out.append(bxf("Figure", (0, 0, 3.6), (16, 16, 4.4), f"{s}-{part}", faces=("north", "south"), back=f"{s}-back-{part}"))
        return out

    absorb = {"*-closed-*": 99, "*-glow-*": 0, "*": 1}
    data = with_behaviours({"renderpass": "Transparent", "drops": [], "resistance": 6, "lightAbsorptionByType": absorb,
                            "lightHsvByType": {"*-glow-*": [7, 3, 7]}, "attributes": {"l188structure": True, "l188window": True}},
                           "BackroomsL188Blind")
    vblock("l188-window", "Courtyard Window", [("state", states), ("part", list(PARTS)), ("side", SIDES)], courtyard_window,
           box=(0, 0, 0, 1, 1, 1), data=data, material="Glass", sounds=GLASS,
           comment="Level 188: a courtyard window, one quarter of the 2 x 2 (ll lr ul ur seen from the courtyard; side = the courtyard face). "
                   "closed: blind down; glow: blind down, lit warm from behind; open / lit: blind rolled up, the real room behind; figure / beckon: someone in it",
           names={"l188-window-*": "Courtyard Window", "l188-window-glow-*": "Window (lit)", "l188-window-lit-*": "Window (lit)",
                  "l188-window-open-*": "Window (blind up)", "l188-window-figure-*": "Window (someone in it)",
                  "l188-window-beckon-*": "Window (someone in it)"})

    scene_windows()

    # ---- Outer façade windows: the room is the front (the side); outside, black
    def outer(v):
        down = v["state"] == "closed"
        els = frame_composite(z=(11, 15)) + glass_composite(z=(12.5, 13)) + [bx("Board", (0, 0, -1), (32, 1.2, 4.5), "sillstone", faces=("up", "north", "south"))]
        els += blind_composite(down, z=(2, 2.5), room_side=-1)
        return split(els, v["part"])

    data = with_behaviours({"renderpass": "Transparent", "drops": [], "resistance": 6, "lightAbsorptionByType": {"*-closed-*": 99, "*": 1},
                            "attributes": {"l188structure": True}}, "BackroomsL188Blind")
    vblock("l188-outerwindow", "Window", [("state", ["closed", "open"]), ("part", list(PARTS)), ("side", SIDES)], outer, box=(0, 0, 0, 1, 1, 1),
           data=data, material="Glass", sounds=GLASS,
           comment="Level 188: a window in the outer façade (side = the room side; parts seen from the room); beyond the glass there is nothing")

    # ---- The stair hall's window on the upper storeys: wired glass, no blind
    def stairwindow(v):
        els = frame_composite() + glass_composite(tex="wiredglass") + inner_board()
        return split(els, v["part"])

    vblock("l188-stairwindow", "Wired Glass Window", [("part", list(PARTS)), ("side", SIDES)], stairwindow, box=(0, 0, 0, 1, 1, 1),
           data={"renderpass": "Transparent", "drops": [], "resistance": 6, "lightAbsorption": 1, "attributes": {"l188structure": True}},
           material="Glass", sounds=GLASS, comment="Level 188: the stair hall's courtyard window on the upper storeys, wired glass (side = the courtyard face)")


# Places seen through a window: (box wall, floor, ceiling, box glow, light, features in viewer coordinates)
# A feature is (name, vx1, y1, z1, vx2, y2, z2, texture, glow): vx runs 0-32 from the viewer's left, z from the front.
PLACES = {
    "l0": ("sc-yellow", "sc-carpet0", "sc-ceil0", 90, [9, 4, 10], [
        ("Troffer", 4, 29.6, 8, 28, 30.5, 11.5, "sc-troffer", 255), ("TrofferRim", 3.4, 30.2, 7.4, 28.6, 30.5, 12.1, "sc-ceil0", 0),
        ("JambL", 11, 1.5, 14, 12.4, 15, 15, "sc-desk", 60), ("JambR", 19.6, 1.5, 14, 21, 15, 15, "sc-desk", 60), ("Head", 11, 15, 14, 21, 16.4, 15, "sc-desk", 60)]),
    "l1": ("sc-concrete", "sc-concretedk", "sc-concrete", 60, [0, 0, 8], [
        ("Pillar", 5, 1.5, 9.5, 10, 30.5, 14, "sc-concrete", 50), ("Cord", 22, 25, 9.1, 22.4, 30.5, 9.5, "sc-cage", 0),
        ("Bulb", 21, 22, 8.3, 23.4, 24.6, 10.3, "sc-bulb", 255), ("CageA", 20.6, 21.6, 9.1, 23.8, 25, 9.5, "sc-cage", 0),
        ("CageB", 22, 21.6, 7.9, 22.4, 25, 10.7, "sc-cage", 0)]),
    "hub": ("sc-hubwall", "sc-dark", "sc-hubwall", 80, [5, 6, 11], [
        ("CurveL1", 1.5, 26, 5, 5, 30.5, 15, "sc-hubwall", 70), ("CurveL2", 1.5, 22.5, 5, 3, 26, 15, "sc-hubwall", 70),
        ("CurveR1", 27, 26, 5, 30.5, 30.5, 15, "sc-hubwall", 70), ("CurveR2", 29, 22.5, 5, 30.5, 26, 15, "sc-hubwall", 70),
        ("Lamp", 18, 26.5, 8, 22, 28.5, 11, "sc-sodium", 255), ("LampArm", 19.6, 28.5, 9.2, 20.4, 30.5, 9.8, "sc-cage", 0)]),
    "fun": ("sc-party", "sc-partyfloor", "sc-party", 100, [5, 4, 10], [
        ("BalloonR", 6, 17, 8, 10.5, 22.5, 12, "sc-red", 80), ("StringR", 8.1, 9, 9.9, 8.4, 17, 10.2, "sc-tablecloth", 0),
        ("BalloonY", 11, 19.5, 10, 14.6, 24, 13.5, "sc-yellowb", 80), ("StringY", 12.6, 9, 11.6, 12.9, 19.5, 11.9, "sc-tablecloth", 0),
        ("Table", 17, 7, 8, 30.5, 8.6, 14.5, "sc-tablecloth", 70), ("Cloth", 17, 3, 8, 30.5, 7, 8.4, "sc-tablecloth", 70)]),
    "l2": ("sc-dark", "sc-dark", "sc-dark", 40, [0, 5, 7], [
        ("PipeA", 1.5, 25, 7.5, 30.5, 27.6, 10.1, "sc-pipe", 30), ("PipeB", 1.5, 20.6, 11, 30.5, 22.6, 13, "sc-pipe2", 30),
        ("Flange", 14, 24.6, 7.1, 15.2, 28, 10.5, "sc-pipe2", 30)]),
    "l4": ("sc-office", "sc-officecarpet", "sc-office", 70, [0, 0, 9], [
        ("DeskTop", 14, 8, 7, 30.5, 9, 12, "sc-desk", 50), ("DeskSide", 28.5, 1.5, 7.5, 30, 8, 11.5, "sc-desk", 50),
        ("Monitor", 18, 10.5, 9.5, 25, 15.5, 10.2, "sc-monitor", 0), ("Stand", 21, 9, 9.7, 22, 10.5, 10.2, "sc-monitor", 0),
        ("Troffer", 8, 30, 7, 24, 30.5, 10, "sc-troffer", 255)]),
    "l5": ("sc-hotelred", "sc-hotelred", "sc-office", 60, [2, 5, 8], [
        ("JambL", 10, 1.5, 14, 11.5, 20, 15, "sc-gold", 60), ("JambR", 20.5, 1.5, 14, 22, 20, 15, "sc-gold", 60),
        ("Head", 10, 20, 14, 22, 21.5, 15, "sc-gold", 60), ("Sconce", 3.6, 18, 13, 6, 21, 15, "sc-porchlamp", 255),
        ("Sconce2", 26, 18, 13, 28.4, 21, 15, "sc-porchlamp", 255)]),
    "l6": ("sc-black", "sc-black", "sc-black", 0, None, []),
    "l9": ("sc-night", "sc-grassnight", "sc-night", 30, [6, 3, 6], [
        ("Post", 8, 1.5, 9, 9.6, 30.5, 10.6, "sc-post", 40), ("Rail", 1.5, 8, 9.4, 8, 9, 10.2, "sc-post", 40),
        ("Lamp", 20, 21.5, 13, 23, 25, 15, "sc-porchlamp", 255)]),
    "l37": ("sc-tile", "sc-tile", "sc-tile", 110, [30, 1, 11], [
        ("Coping", 1.5, 1.5, 5, 30.5, 3, 8, "sc-tile", 110), ("Water", 1.5, 1.5, 8, 30.5, 2, 15, "sc-water", 120)]),
    "l94": ("sc-skyblue", "sc-hill", "sc-skyblue", 120, [8, 3, 13], [
        ("Hill", 1.5, 1.5, 11, 21, 8, 15, "sc-hill", 110), ("Hill2", 16, 1.5, 12, 30.5, 5, 15, "sc-hill", 110)]),
    "end": ("sc-shelf", "sc-desk", "sc-office", 70, [7, 3, 9], [
        ("ShelfL", 1.5, 1.5, 6, 6.5, 26, 14, "sc-books", 60), ("ShelfR", 25.5, 1.5, 6, 30.5, 26, 14, "sc-books", 60)]),
    "void": ("sc-black", "sc-black", "sc-black", 0, None, []),
}


def scene_windows():
    """The link windows (and the windows of rooms whose blind was opened): the frame, no glass, and behind it a
    peep-box 10 voxels deep showing another place: real voxel features and a painted back wall, lit from its own side."""
    def scene(v):
        place, part = v["place"], v["part"]
        wall, floor, ceil, g, _, feats = PLACES[place]
        els = frame_composite()
        back = bxa("Back", (0, 0, 15), (32, 32, 15.5), "x", faces=("north",), glow=g)
        els.append(back)
        els += [bx("BoxFloor", (0, 0, 5), (32, 1.5, 15), floor, faces=("up",), glow=g),
                bx("BoxCeil", (0, 30.5, 5), (32, 32, 15), ceil, faces=("down",), glow=g),
                bx("BoxR", (0, 0, 5), (1.5, 32, 15), wall, faces=("east",), glow=g),
                bx("BoxL", (30.5, 0, 5), (32, 32, 15), wall, faces=("west",), glow=g)]
        for (nm, a, y1, z1, b, y2, z2, tex, fg) in feats:
            x1, x2 = vx(a, b)
            els.append(bx(nm, (x1, y1, z1), (x2, y2, z2), tex, glow=fg))
        out = split(els, part)
        for e in out:
            if e["name"] == "Back":
                e["faces"]["north"]["texture"] = f"#scene-{place}-{part}"
                e["faces"]["north"]["uv"] = [0, 0, 16, 16]
        return out

    lights, absorb = {}, {}
    for place, spec in PLACES.items():
        if spec[4]:
            lights[f"*-{place}-*"] = spec[4]
            absorb[f"*-{place}-*"] = 0
    absorb["*"] = 99
    data = with_behaviours({"drops": [], "resistance": 6, "lightHsvByType": lights, "lightAbsorptionByType": absorb,
                            "attributes": {"l188structure": True, "l188window": True}}, "BackroomsL188Blind")
    vblock("l188-window-scene", "Window onto Elsewhere", [("place", list(PLACES)), ("part", list(PARTS)), ("side", SIDES)], scene,
           colboxes=lambda v: split_boxes(FRAME_BOXES, v["part"]), selboxes=lambda v: [(0, 0, 0, 1, 1, 1)],
           data=data, material="Glass", sounds=GLASS,
           comment="Level 188: a window onto another place (link windows, and rooms whose blind was opened): the frame, no glass, a lit peep-box behind it. "
                   "Collision on the frame only: link windows are climbed into from the sill. Places: Level 0, 1, 2, 4, 5, 6, 9, 37, 94, the Hub, Level Fun, The End, and a void")
    LANG["block-l188-window-scene-*"] = "Window onto Elsewhere"


# ======================================================================== Doors and signs

def door_frame(top=True):
    """Jambs and head in composite Y (0-32), the frame lining the doorway right through the wall."""
    els = [bx("JambL", (14.4, 0, 0), (16, 32, 16), "doorframe", faces=("north", "south", "west", "up", "down")),
           bx("JambR", (0, 0, 0), (1.6, 32, 16), "doorframe", faces=("north", "south", "east", "up", "down"))]
    if top:
        els.append(bx("Head", (1.6, 30.4, 0), (14.4, 32, 16), "doorframe", faces=("north", "south", "down")))
    # architraves on both faces
    els += [bx("ArchL", (14.4, 0, -0.6), (16.4, 32, 0), "doorframe", faces=("north", "east", "west", "up")),
            bx("ArchR", (-0.4, 0, -0.6), (1.6, 32, 0), "doorframe", faces=("north", "east", "west", "up")),
            bx("ArchT", (1.6, 30.4, -0.6), (14.4, 32.4, 0), "doorframe", faces=("north", "down", "up"))]
    return els


def vsplit(els, part, absolute_uv=False):
    """A two-block-tall thing modelled in composite Y (0-32), clipped into its lower or upper block."""
    oy = 0 if part == "lower" else 16
    return clip(els, (-64, oy, -64), (64, oy + 16, 64), (0, oy, 0), absolute_uv=absolute_uv)


def swing(els, origin, angle):
    """Swings (already split) leaf pieces about a vertical hinge: +90 turns a leaf hinged on its +X edge into the
    room (+Z), -90 one hinged on its -X edge."""
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["rotationOrigin"] = [origin[0], 0, origin[1]]
        e["rotationY"] = angle
        out.append(e)
    return out


def guest_leaf(led):
    """A grey-oak laminate guest door, closed, hinge on the left seen from the corridor (+X): a lever, a card reader
    over it, a peephole; the room side has its own lever. No number."""
    els = [bx("Leaf", (1.6, 0, 7), (14.4, 30.4, 9), "laminate")]
    els += [bx("Rose", (2.6, 14.2, 6.6), (4.4, 16.2, 7), "chrome"), bx("Lever", (2.8, 14.8, 5.6), (7.2, 15.6, 6.6), "chrome"),
            bx("RoseIn", (2.6, 14.2, 9), (4.4, 16.2, 9.4), "chrome"), bx("LeverIn", (2.8, 14.8, 9.4), (7.2, 15.6, 10.4), "chrome"),
            bx("Reader", (2.4, 17.4, 6.3), (4.8, 21.4, 7), "reader"), bx("LED", (3.2, 20.4, 6.1), (4.0, 20.9, 6.3), led, glow=200 if led != "led-dark" else 0),
            bx("Slot", (3.3, 18, 6.2), (3.9, 19.8, 6.3), "ink"), bx("Peephole", (7.4, 23.6, 6.7), (8.6, 24.8, 7), "chrome"),
            bx("Kick", (1.8, 0.4, 6.8), (14.2, 2.4, 7), "steel", faces=("north",))]
    return els


def stair_leaf():
    els = [bx("Leaf", (1.6, 0, 7), (14.4, 30.4, 9), "firedoor"),
           bx("Vision", (5, 19, 6.9), (11, 27, 9.1), "wiredglass", faces=("north", "south")),
           bx("VisionTrim", (4.6, 18.6, 6.8), (11.4, 19, 9.2), "steel"), bx("VisionTrimT", (4.6, 27, 6.8), (11.4, 27.4, 9.2), "steel"),
           bx("Lever", (2.8, 14.8, 5.6), (7.2, 15.6, 6.6), "steel"), bx("LeverIn", (2.8, 14.8, 9.4), (7.2, 15.6, 10.4), "steel"),
           bx("Closer", (8, 28.4, 9), (13.6, 29.6, 10.4), "steel"), bx("CloserArm", (4, 28.8, 9.6), (8, 29.4, 10.2), "steel")]
    # the vision panel is see-through: the leaf behind it is cut away
    leaf = els[0]
    els[0:1] = [bx("LeafB", (1.6, 0, 7), (14.4, 19, 9), "firedoor"), bx("LeafT", (1.6, 27, 7), (14.4, 30.4, 9), "firedoor"),
                bx("LeafL", (11, 19, 7), (14.4, 27, 9), "firedoor"), bx("LeafR", (1.6, 19, 7), (5, 27, 9), "firedoor")]
    del leaf
    return els


def doors():
    def door_variants(code, english, leaf_fn, states, comment, extra=None, sounds=WOOD, material="Wood"):
        def build(v):
            st = v["state"]
            leaf = vsplit(leaf_fn(st), v["part"])
            if st == "open":
                leaf = swing(leaf, (14.4, 9), 90)
            return vsplit(door_frame(), v["part"]) + leaf

        def colb(v):
            if v["state"] == "open":
                return [(12.4 / 16, 0, 9 / 16, 14.4 / 16, 1, 1)]
            return [(0, 0, 7 / 16, 1, 1, 9 / 16)]

        data = with_behaviours(dict({"drops": [], "resistance": 6, "lightAbsorption": 0, "attributes": {"l188structure": True},
                                     "renderpass": "Transparent" if code in ("l188-stairdoor",) else "Opaque"}, **(extra or {})), "BackroomsL188Door")
        if data.get("renderpass") == "Opaque":
            data.pop("renderpass")
        vblock(code, english, [("state", states), ("part", ["lower", "upper"]), ("side", SIDES)], build,
               colboxes=colb, selboxes=lambda v: [(0, 0, 6 / 16, 1, 1, 10 / 16)] if v["state"] != "open" else [(12 / 16, 0, 9 / 16, 1, 1, 1)],
               data=data, material=material, sounds=sounds, comment=comment)

    leds = {"closed": "led-green", "open": "led-green", "locked": "led-red", "sealed": "led-dark"}
    door_variants("l188-guestdoor", "Guest Room Door", lambda st: guest_leaf(leds[st]), ["closed", "open", "locked", "sealed"],
                  "Level 188: a guest room door, grey-oak laminate, no number (side = the corridor face; hinge on the left seen from it). "
                  "Card reader LED: green (closed, open), red (locked), dark (sealed). Open: swung into the room")
    LANG.update({"block-l188-guestdoor-*": "Guest Room Door", "block-l188-guestdoor-locked-*": "Guest Room Door (locked)",
                 "block-l188-guestdoor-sealed-*": "Guest Room Door"})
    door_variants("l188-stairdoor", "Stair Door", lambda st: stair_leaf(), ["closed", "open"],
                  "Level 188: the stair hall's grey fire door with a wired-glass vision panel and a closer (side = the corridor face)",
                  sounds=METAL, material="Metal")

    # ---- Fire exit: grey steel, a real push bar, FIRE EXIT stencilled; it leads somewhere else
    def firedoor(v):
        els = door_frame()
        els += [bx("Leaf", (1.6, 0, 7), (14.4, 30.4, 9), "firedoor"),
                bxf("Stencil", (2.4, 18, 6.94), (13.6, 29.2, 6.96), "stencil-fireexit", faces=("north",)),
                bx("BarL", (11.6, 14, 5.2), (13.2, 17.4, 7), "steel"), bx("BarR", (2.8, 14, 5.2), (4.4, 17.4, 7), "steel"),
                bx("Bar", (3.2, 14.8, 4.4), (12.8, 16.6, 5.4), "pushbar-red"),
                bx("Kick", (1.8, 0.4, 6.8), (14.2, 3, 7), "steel", faces=("north",)),
                bx("Hinge1", (14.1, 3, 6.6), (14.6, 6, 7.2), "steel"), bx("Hinge2", (14.1, 24, 6.6), (14.6, 27, 7.2), "steel")]
        return vsplit(els, v["part"])

    vblock("l188-firedoor", "Fire Exit", [("part", ["lower", "upper"]), ("side", SIDES)], firedoor,
           colboxes=lambda v: [(0, 0, 7 / 16, 1, 1, 9 / 16)], selboxes=lambda v: [(0, 0, 4 / 16, 1, 1, 10 / 16)],
           data={"drops": [], "resistance": 999, "lightAbsorption": 0, "attributes": {"l188structure": True}, "behaviors": threshold("l188-fireexit")},
           material="Metal", sounds=METAL, comment="Level 188: a fire exit door, grey steel with a push bar (side = the corridor face). Threshold kind l188-fireexit: it opens onto somewhere else")

    # ---- The courtyard's glazed double door: aluminium leaves, push bars, kick plates; open leaves swing inward
    def courtyard_leaf(lr):
        # modelled for the left leaf (seen from the courtyard, its hinge on the outer +X edge); mirrored for the right
        els = [bx("StileO", (13, 0, 7), (15, 30.4, 9), "alu"), bx("StileI", (0, 0, 7), (2, 30.4, 9), "alu"),
               bx("RailB", (2, 0, 7), (13, 6, 9), "alu"), bx("RailM", (2, 14.6, 7), (13, 16.4, 9), "alu"), bx("RailT", (2, 28.4, 7), (13, 30.4, 9), "alu"),
               bx("GlassLo", (2, 6, 7.8), (13, 14.6, 8.2), "glass", faces=("north", "south")),
               bx("GlassHi", (2, 16.4, 7.8), (13, 28.4, 8.2), "glass", faces=("north", "south")),
               bx("Kick", (2, 0.4, 6.7), (13, 5, 7), "kickplate", faces=("north", "up")), bx("KickIn", (2, 0.4, 9), (13, 5, 9.3), "kickplate", faces=("south", "up")),
               bx("Push", (2.4, 15, 9.6), (12.4, 16, 10.4), "steel"),
               bx("PushBrkL", (3.0, 15.1, 9.0), (3.8, 15.9, 9.6), "steel", faces=("east", "west", "up", "down")),
               bx("PushBrkR", (11.0, 15.1, 9.0), (11.8, 15.9, 9.6), "steel", faces=("east", "west", "up", "down")), bx("Pull", (2.6, 10, 5.6), (3.6, 21, 6.4), "steel"),
               bx("PullS1", (2.8, 11, 6.4), (3.4, 11.8, 7), "steel"), bx("PullS2", (2.8, 19.2, 6.4), (3.4, 20, 7), "steel")]
        if lr == "r":
            els = mirror_x(els)
        return els

    def courtyard_frame(lr):
        els = [bx("Jamb", (15, 0, 0), (16, 32, 16), "alu", faces=("north", "south", "west", "up", "down")),
               bx("Head", (0, 30.4, 0), (15, 32, 16), "alu", faces=("north", "south", "down"))]
        return els if lr == "l" else mirror_x(els)

    def courtyard(v):
        lr = v["lr"]
        leaf = vsplit(courtyard_leaf(lr), v["part"])
        if v["state"] == "open":
            leaf = swing(leaf, (15, 9) if lr == "l" else (1, 9), 90 if lr == "l" else -90)
        return vsplit(courtyard_frame(lr), v["part"]) + leaf

    def ccol(v):
        if v["state"] == "open":
            return [(13 / 16, 0, 9 / 16, 15 / 16, 1, 1)] if v["lr"] == "l" else [(1 / 16, 0, 9 / 16, 3 / 16, 1, 1)]
        return [(0, 0, 7 / 16, 1, 1, 9 / 16)]

    data = with_behaviours({"renderpass": "Transparent", "drops": [], "resistance": 999, "lightAbsorption": 0, "attributes": {"l188structure": True}},
                           "BackroomsL188Door")
    vblock("l188-courtyarddoor", "Courtyard Door", [("state", ["closed", "open"]), ("lr", ["l", "r"]), ("part", ["lower", "upper"]), ("side", SIDES)],
           courtyard, colboxes=ccol, selboxes=lambda v: ccol(v) if v["state"] == "open" else [(0, 0, 6 / 16, 1, 1, 10 / 16)],
           data=data, material="Glass", sounds=GLASS,
           comment="Level 188: the glazed aluminium double door from the stair hall onto the courtyard (side = the courtyard face; l/r leaves seen from it; open leaves swing inward)")

    # ---- The lobby's front doors: frameless dark glass, long steel pulls; nothing beyond
    def front(v):
        lr = v["lr"]
        els = [bx("Glass", (0.6, 0, 7.6), (15.4, 31.4, 8.4), "glass-dark", faces=("north", "south", "east", "west", "up")),
               bx("PatchB", (0.6, 0, 7.4), (15.4, 1.6, 8.6), "steel"), bx("PatchT", (0.6, 30.4, 7.4), (15.4, 32, 8.6), "steel"),
               bx("Pull", (1.6, 6, 5), (2.6, 26, 6), "steel"), bx("PullS1", (1.8, 8, 6), (2.4, 9, 7.6), "steel"), bx("PullS2", (1.8, 23, 6), (2.4, 24, 7.6), "steel"),
               bx("PullIn", (1.6, 6, 10), (2.6, 26, 11), "steel"), bx("PullIn1", (1.8, 8, 8.4), (2.4, 9, 10), "steel"), bx("PullIn2", (1.8, 23, 8.4), (2.4, 24, 10), "steel")]
        if lr == "r":
            els = mirror_x(els)
        return vsplit(els, v["part"])

    vblock("l188-frontdoor", "Front Door", [("lr", ["l", "r"]), ("part", ["lower", "upper"]), ("side", SIDES)], front,
           colboxes=lambda v: [(0, 0, 7 / 16, 1, 1, 9 / 16)], selboxes=lambda v: [(0, 0, 5 / 16, 1, 1, 11 / 16)],
           data={"renderpass": "Transparent", "drops": [], "resistance": 999, "lightAbsorption": 0, "attributes": {"l188structure": True},
                 "behaviors": threshold("l188-frontdoor")}, material="Glass", sounds=GLASS,
           comment="Level 188: the lobby's frameless glass front doors (side = the lobby face); beyond the glass there is nothing at all. Threshold kind l188-frontdoor (it refuses)")

    signs()


def hung(els):
    """Wall-hung things are modelled with their back on the north face of a wall (z <= 0) and moved into the air cell
    in front of it, so they sit against that cell's south edge and face north (front = the side)."""
    from gen_188_kit import shift
    return shift(els, dz=16)


def signs():
    def exitsign(v):
        face = bxf("Face", (3, 7, -2.2), (13, 12, -2), "exitsign", faces=("north",), glow=220)
        return hung([bx("Box", (3, 7, -2), (13, 12, 0), "signbox"), face,
                     bx("Lip", (2.6, 6.6, -0.4), (13.4, 12.4, 0), "signbox", faces=("north", "east", "west", "up", "down"))])

    vblock("l188-exitsign", "Exit Sign", [("side", SIDES)], exitsign, collide=False, sel=lambda v: (0.15, 0.4, 0.85, 0.85, 0.8, 1),
           data={"drops": [], "resistance": 6, "lightHsv": [22, 5, 7], "lightAbsorption": 0, "attributes": {"l188structure": True}},
           material="Glass", sounds=GLASS, comment="Level 188: a green running-man exit sign, wall-hung over fire doors and stair doors (in the air cell, its back on the wall behind it; front = side)")

    def exitsign_shift(v):
        from gen_188_kit import shift
        return shift(exitsign(v), dx=8)

    vblock("l188-exitsignshift", "Exit Sign", [("side", SIDES)], exitsign_shift, collide=False, sel=lambda v: (0.65, 0.4, 0.85, 1, 0.8, 1),
           data={"drops": [], "resistance": 6, "lightHsv": [22, 5, 7], "lightAbsorption": 0, "attributes": {"l188structure": True}},
           material="Glass", sounds=GLASS, comment="Level 188: the exit sign drawn half a block to the left (as seen from in front), so that over "
           "the courtyard's double door it hangs over the middle")

    labels = ["1", "2", "3", "4", "5", "roof"]

    def floorsign(v):
        return hung([bx("Plate", (4, 4, -0.6), (12, 12, 0), "steel"),
                     bxf("Face", (4.2, 4.2, -0.62), (11.8, 11.8, -0.6), "floorsign-" + v["floor"], faces=("north",)),
                     bx("Screw1", (4.6, 10.8, -0.8), (5.2, 11.4, -0.6), "chrome"), bx("Screw2", (10.8, 4.6, -0.8), (11.4, 5.2, -0.6), "chrome")])

    vblock("l188-floorsign", "Floor Sign", [("floor", labels), ("side", SIDES)], floorsign, collide=False, sel=lambda v: (0.25, 0.25, 0.95, 0.75, 0.75, 1),
           data={"drops": [], "resistance": 6, "attributes": {"l188structure": True}}, material="Metal", sounds=METAL,
           comment="Level 188: a stencilled storey number on a grey plate, wall-hung beside the stair-landing doors (rel 4s+2)",
           names={f"l188-floorsign-{k}-*": (f"Floor Sign ({k})" if k != "roof" else "Floor Sign (Roof)") for k in labels})


# ======================================================================== Lang

def lang():
    LANG.update({
        "level-20": "Level 188: The Courtyard of Windows",
        "levelhint-20": "Count the windows. Never open a blind.",
        "levelname-20": "Level 188",
        "level-2001": "The Hotel",
        "levelhint-2001": "The doors have no numbers. Count them.",
        "levelname-2001": "Level 188, the Hotel",
        "level-2002": "The Roof",
        "levelhint-2002": "There is nothing out there at all.",
        "levelname-2002": "Level 188, the Roof",
        "l188-window-in": "You climb through the window.",
        "l188-window-arrive": "You climb down from a sill into a dark courtyard. Behind you, the window still shows where you came from.",
        "l188-taken": "You lift the blind.",
        "l188-taken-arrive": "The room is gone. There is no window behind you.",
        "l188-blind-outside": "The blind is on the inside.",
        "l188-sealed": "It will not open. Something holds it from the other side.",
        "l188-locked": "Locked. The card reader blinks red.",
        "l188-keycard-open": "The reader blinks green and the lock clicks.",
        "l188-keycard-sealed": "The card reader stays dark.",
        "l188-fireexit": "The push bar gives, and the door opens onto somewhere else.",
        "l188-fireexit-arrive": "The fire door bangs shut behind you.",
        "l188-frontdoor": "Beyond the glass there is nothing at all.",
        "l188-hatch-open": "The hatch grinds open onto black. Far below, water.",
        "l188-hatch-arrive": "You fall through cold black air into warm water.",
        "l188-grabbed": "Something has your arm.",
        "l188-brokefree": "It lets go and is gone back into the glass.",
        "l188-consumed": "{0} was pulled through a window",
        "l188-guestbook": ("A guest book: two hundred pages of names in different hands, every one checking in, none checking out. "
                           "The last page says only \"=)\" in red."),
        "blockhelp-l188-blind": "Open the blind",
        "blockhelp-l188-door": "Open / close",
        "blockhelp-l188-hatch": "Lift the hatch",
        "blockhelp-l188-window": "Climb through",
        "blockhelp-l188-guestbook": "Read the guest book",
        "l188-blind-up": "The blind is already up.",
        "l188-dispenser-empty": "Empty.",
        "item-creature-l188-arm": "A Window's arm",
        "prefixandcreature-l188-arm": "a Window's arm",
        "deadcreature-l188-arm": "Pulled through a window",
    })


# ======================================================================== Check

GAME = os.path.join(os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory")), "assets")


def asset_exists(kind, path, ext):
    domain, rel = path.split(":", 1) if ":" in path else ("backrooms", path)
    if domain == "backrooms":
        return os.path.exists(os.path.join(ASSETS, kind, rel + ext))
    return any(os.path.exists(os.path.join(GAME, d, kind, rel + ext)) for d in ("survival", "game", "creative"))


_GAME_CODES = {}


def game_codes(typ):
    if typ not in _GAME_CODES:
        names = set()
        for d in ("survival", "game"):
            for root, _, files in os.walk(os.path.join(GAME, d, "blocktypes" if typ == "block" else "itemtypes")):
                for fn in files:
                    try:
                        raw = open(os.path.join(root, fn), encoding="utf-8").read(400)
                    except OSError:
                        continue
                    m = re.search(r'code:\s*"([^"]+)"', raw)
                    if m:
                        names.add(m.group(1))
        _GAME_CODES[typ] = names
    return _GAME_CODES[typ]


def our_codes():
    out = set()
    for kind in ("blocktypes", "itemtypes"):
        for root, _, files in os.walk(os.path.join(ASSETS, kind)):
            for fn in files:
                raw = open(os.path.join(root, fn), encoding="utf-8").read()
                m = re.search(r'"?code"?\s*:\s*"([^"]+)"', raw)
                if m:
                    out.add(m.group(1))
    return out


def check(sounds_written):
    """Every texture a shape names exists and every face's texture key is defined; every shape, texture and sound a
    block, item or entity type names exists; every drop is a known item or block; no code clashes with another
    level's; every sound the plan lists was written."""
    problems = []
    for nm in WRITTEN["shapes"]:
        data = json.load(open(os.path.join(ASSETS, "shapes", "block", "188", nm + ".json"), encoding="utf-8"))
        used = set()

        def walk(e):
            for f in e["faces"].values():
                used.add(f["texture"][1:])
                uv = f.get("uv")
                if uv and (min(uv) < -1e-6 or max(uv) > 16 + 1e-6):
                    problems.append(f"shape {nm}: uv out of range {uv}")
            for c in e.get("children", []):
                walk(c)
        for e in data["elements"]:
            walk(e)
        for k in used:
            if k not in data["textures"]:
                problems.append(f"shape {nm}: #{k} undefined")
        for k, p in data["textures"].items():
            if not asset_exists("textures", p, ".png"):
                problems.append(f"shape {nm}: texture {k} -> {p}")
    ours = our_codes()
    mine = set(WRITTEN["blocktypes"]) | set(WRITTEN["itemtypes"])
    # a code of ours must not be another file's code anywhere
    seen = {}
    for kind in ("blocktypes", "itemtypes"):
        for root, _, files in os.walk(os.path.join(ASSETS, kind)):
            for fn in files:
                raw = open(os.path.join(root, fn), encoding="utf-8").read()
                m = re.search(r'"?code"?\s*:\s*"([^"]+)"', raw)
                if m:
                    seen.setdefault(m.group(1), []).append(os.path.relpath(os.path.join(root, fn), ASSETS))
    for c in mine:
        if len(seen.get(c, [])) > 1:
            problems.append(f"code {c} clashes: {seen[c]}")
    for kind, codes, folder in (("blocktypes", WRITTEN["blocktypes"], os.path.join(ASSETS, "blocktypes", "188")),
                                ("itemtypes", WRITTEN["itemtypes"], os.path.join(ASSETS, "itemtypes", "188")),
                                ("entities", WRITTEN["entities"], os.path.join(ASSETS, "entities"))):
        for code in codes:
            raw = open(os.path.join(folder, code + ".json"), encoding="utf-8").read()
            data = json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
            text = json.dumps(data)
            for m in re.finditer(r'"base": "([^"]+)"', text):
                p = m.group(1)
                rel = p.split(":", 1)[-1]
                if rel.startswith(("block/188/l188-", "entity/188/", "item/188/l188-")) and not rel.endswith(".png"):
                    ok = asset_exists("shapes", p, ".json") or asset_exists("textures", p, ".png")
                else:
                    ok = asset_exists("textures", p, ".png") or asset_exists("shapes", p, ".json")
                if not ok:
                    problems.append(f"{kind} {code}: {p}")
            for m in re.finditer(r'"(backrooms:(?:ambient|effect)/[^"*]+)\*?"', text):
                p = m.group(1).split(":", 1)[1]
                if not os.path.exists(os.path.join(ASSETS, "sounds", p + ".ogg")):
                    problems.append(f"{kind} {code}: sound {p}")
            for m in re.finditer(r'\{"type": "(item|block)", "code": "([^"]+)"', text):
                typ, c = m.groups()
                dom, path = c.split(":", 1) if ":" in c else ("backrooms", c)
                if dom == "game":
                    base = path.split("-")[0]
                    if not any(base == g.split("-")[0] for g in game_codes(typ)):
                        problems.append(f"{kind} {code}: drop {typ} {c} not in the game")
                elif path not in ours and not any(path.startswith(o + "-") for o in ours):
                    problems.append(f"{kind} {code}: drop {typ} {c} unknown")
            for m in re.finditer(r'"offBlock": "backrooms:([^"]+)"', text):
                if not any(m.group(1).startswith(o + "-") or m.group(1) == o for o in mine):
                    problems.append(f"{kind} {code}: offBlock {m.group(1)} unknown")
    for p in sounds_written.get("missing", []):
        problems.append(f"sound {p} not written")
    for p in problems:
        print("CHECK:", p)
    print(f"check: {len(WRITTEN['blocktypes'])} blocktypes ({COUNT['variants']} variants), {len(WRITTEN['shapes'])} shapes, "
          f"{len(WRITTEN['itemtypes'])} itemtypes, {len(WRITTEN['entities'])} entities, {len(sounds_written.get('written', []))} sounds, "
          f"{len(problems)} problems")
    return not problems


def clean():
    """Empties Level 188's own block, shape and item folders (only those), so renamed codes leave nothing stale."""
    for sub in (("blocktypes", "188"), ("shapes", "block", "188"), ("itemtypes", "188")):
        p = os.path.join(ASSETS, *sub)
        if os.path.isdir(p):
            shutil.rmtree(p)


def main():
    only = set(sys.argv[1:])
    everything = not only
    import gen_188_tex
    import gen_188_props
    if everything or "tex" in only:
        gen_188_tex.generate()
    if everything or "blocks" in only:
        clean()
        structure()
        windows()
        doors()
        gen_188_props.generate()
    if everything or "models" in only:
        import gen_188_models
        gen_188_models.generate()
    snd = {}
    if everything or "sounds" in only:
        import gen_188_sounds
        snd = gen_188_sounds.generate()
    else:
        import gen_188_sounds
        snd = gen_188_sounds.existing()
    if everything or "blocks" in only or "lang" in only:
        lang()
        merge_lang()
    ok = check(snd) if (everything or "blocks" in only) else True
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
