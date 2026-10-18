"""Generates block type definitions for Levels 3-5, which have many similar blocks.

Run from the repo root:  python tools/gen_blocktypes.py
Blocks for Levels 0-2 are hand-written in assets/backrooms/blocktypes, but for Level 2's fittings of layout version 9
(level2()).
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
    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.12, "var": 0}},
    {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0}},
]
CEILING_DROPS = [
    {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.12, "var": 0}},
    {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.04, "var": 0}},
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


def _retexture(folder, code, by_type=None, textures=None):
    """Rewrites a block type just written by cube(): its textures by type (`by_type`), or its one texture set."""
    path = os.path.join(OUT, folder, code + ".json")
    with open(path, encoding="utf-8") as f:
        lines = f.read()
    comment, _, body = lines.partition("\n") if lines.startswith("//") else ("", "", lines)
    block = json.loads(body)
    if by_type:
        block.pop("textures", None)
        out = {}
        for k, v in block.items():
            out[k] = v
            if k == "drawtype":
                out["texturesByType"] = by_type
        block = out
    else:
        block["textures"] = textures
    with open(path, "w", encoding="utf-8") as f:
        f.write((comment + "\n" if comment else "") + json.dumps(block, indent="\t") + "\n")


def turned(base, turns=(0, 90, 180, 270)):
    """Alternates of one texture: the texture at each of these turns (0 is the texture as it is)."""
    return [{"base": base, "rotation": r} if r else {"base": base} for r in turns]


def with_alternates(textures, alts):
    """{'all': {'base': ..., 'alternates': [...]}} for a cube: the first entry is the base, the rest its alternates."""
    first, rest = alts[0], alts[1:]
    return {"all": dict(first, alternates=rest)} if rest else {"all": first}


def level3():
    # (B6) Each wall in three versions that share their face and joint textures and differ only in which unit is
    # darker or warmer, so they mix without a patchwork. The blocks carrying fixtures and decorations use the first.
    # (D4) randomizeAxes xyz: the versions are picked by height as well (B13's lesson), so a column does not stack one
    cube("level3", "l3wall", "block/level3/l3wall-{type}", states=["glazed", "brick", "cinder"], randomizeAxes="xyz",
         comment="Level 3 walls: two-tone glazed structural tile, red brick, and cinder block in the machine rooms")
    walls = {}
    for t in ("glazed", "brick", "cinder"):
        walls[f"*-{t}"] = with_alternates(None, [{"base": f"block/level3/l3wall-{t}{v}"} for v in ("", "-2", "-3")])
    _retexture("level3", "l3wall", walls)
    fixture = {
        "code": "l3wallfixture",
        "variantgroups": [{"code": "material", "states": ["glazed", "brick", "cinder"]}, {"code": "fixture", "states": ["pipes", "panel", "fan", "pipesjoint", "pipesbracket"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Stone",
        "drawtype": "json",
        "shapeByType": {"*": {"base": "block/l3wall-{material}-{fixture}"}},
        "textures": {"wall": {"base": "block/level3/l3wall-{material}"}},
        "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE,
    }
    write("level3", "l3wallfixture", fixture, "Level 3 walls carrying 3D pipes (with a flanged joint, or a bracket), electrical panels or industrial fans")
    # (L3 placement) Level 3's fittings that lead somewhere, placed from layout version 9 (the shapes are
    # tools/gen_shapes.py's l3_fittings): the wall pipes with pressure gauges in them, and the junction box over a panel
    # that its conduit runs up into, with a cable run coming into its side (e, w) or both, or none
    fittings = ["pipesgauge", "panelbox", "panelboxe", "panelboxw", "panelboxew"]
    write("level3", "l3fitting", {
        "code": "l3fitting",
        "variantgroups": [{"code": "material", "states": ["glazed", "brick", "cinder"]}, {"code": "fitting", "states": fittings}],
        "creativeinventory": {"general": ["*-pipesgauge", "*-panelbox"], "construction": ["*-pipesgauge", "*-panelbox"]},
        "blockmaterial": "Stone",
        "drawtype": "json",
        "shapeByType": {"*": {"base": "block/l3fitting-{material}-{fitting}"}},
        "textures": {"wall": {"base": "block/level3/l3wall-{material}"}},
        "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE,
    }, "Level 3 walls with fittings that lead somewhere: pressure gauges in the wall pipes, and the junction box a panel's "
       "conduit runs up into")
    # The wall pipes of Levels 2 and 3 turning corners and ending: the state names the faces open to the tunnel and
    # what the pipes do at each corner (see tools/gen_shapes.py, wall_pipe_configs)
    from gen_shapes import wall_pipe_corner_states
    corner_states = wall_pipe_corner_states()
    write("level3", "wallpipecorner", {
        "code": "wallpipecorner",
        "variantgroups": [{"code": "wall", "states": ["tunnel", "glazed", "brick", "cinder"]}, {"code": "conf", "states": list(corner_states)}],
        "creativeinventory": {"general": ["*-tunnel-nesw-wwww", "*-tunnel-ne-wooo"], "construction": ["*-tunnel-nesw-wwww", "*-tunnel-ne-wooo"]},
        "blockmaterial": "Stone",
        "drawtype": "json",
        "shapeByType": {f"*-{state}": {"base": f"block/wallpipe/{shape}", "rotateY": rotate} for state, (shape, rotate) in corner_states.items()},
        "texturesByType": {"*-tunnel-*": {"wall": {"base": "block/level2/tunnelwall-plain"}}, "*": {"wall": {"base": "block/level3/l3wall-{wall}"}}},
        "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE,
    }, "Level 2 and 3 walls whose round pipes turn a corner (outer corners wrap round, inner corners meet) or end in a blind flange")
    # (B6) Floors and ceilings in versions turned at random that meet without a seam (gen_textures.dusty_floor,
    # plaster_ceiling): the floor's grit and scuff each in about one block in four, the ceiling's stains one in fourteen
    floor = turned("block/level3/dustyfloor") * 2 + turned("block/level3/dustyfloor-2") + turned("block/level3/dustyfloor-3")
    cube("level3", "dustyfloor", "block/level3/dustyfloor", comment="Dusty concrete floor")
    _retexture("level3", "dustyfloor", None, with_alternates(None, floor))
    ceiling = (turned("block/level3/plasterceiling") + turned("block/level3/plasterceiling-2")
               + turned("block/level3/plasterceiling-3") + [{"base": "block/level3/plasterceiling-4"}, {"base": "block/level3/plasterceiling-5"}])
    cube("level3", "plasterceiling", "block/level3/plasterceiling", comment="Peeling, stained plaster ceiling")
    _retexture("level3", "plasterceiling", None, with_alternates(None, ceiling))
    cube("level3", "roomsign", "block/level3/roomsign-{type}", states=[str(i) for i in range(8)],
         comment="White machine-room signs with a 3-digit number and illegible text beneath")
    cube("level3", "windowglow", "block/level3/windowglow", material="Glass", sounds=GLASS,
         comment="A window behind bars, glowing like a sunny day", lightHsv=[8, 2, 16], lightAbsorption=0,
         vertexFlags={"glowLevel": 200})

    cables = {
        "code": "cables",
        # "end-<side>": a tray ending with open hall beyond it on that side
        "variantgroups": [{"code": "type", "states": ["run-we", "run-ns", "hub", "end-north", "end-east", "end-south", "end-west"]}],
        "creativeinventory": {"general": ["*-run-we", "*-hub"], "decorative": ["*-run-we", "*-hub"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-hub": {"base": "block/cables-hub"}, "*-we": {"base": "block/cables-run", "rotateY": 0}, "*-ns": {"base": "block/cables-run", "rotateY": 90},
                        "*-end-east": {"base": "block/cables-end", "rotateY": 0}, "*-end-north": {"base": "block/cables-end", "rotateY": 90},
                        "*-end-west": {"base": "block/cables-end", "rotateY": 180}, "*-end-south": {"base": "block/cables-end", "rotateY": 270}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0.7, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0.7, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "lightAbsorption": 0, "resistance": 2, "sounds": METAL,
    }
    write("level3", "cables", cables, "Bundled cables in trays under the ceiling")

    light = {
        "code": "cablelight",
        # Along a tray ("we", "ns"), on no tray, hanging from the ceiling ("none"), or on a bundle of the tar pipes
        "variantgroups": [{"code": "state", "states": ["warm", "off", "flicker"]}, {"code": "axis", "states": ["we", "ns", "none", "tarwe", "tarns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Glass", "drawtype": "json",
        "shapeByType": {
            "*-off-none": {"base": "block/cablelight-plain-off"}, "*-none": {"base": "block/cablelight-plain-lit"},
            "*-off-tarwe": {"base": "block/tunnellight-bundle-off", "rotateY": 0}, "*-off-tarns": {"base": "block/tunnellight-bundle-off", "rotateY": 90},
            "*-tarwe": {"base": "block/tunnellight-bundle-warm", "rotateY": 0}, "*-tarns": {"base": "block/tunnellight-bundle-warm", "rotateY": 90},
            "*-off-we": {"base": "block/cablelight-off", "rotateY": 0}, "*-off-ns": {"base": "block/cablelight-off", "rotateY": 90},
            "*-we": {"base": "block/cablelight-lit", "rotateY": 0}, "*-ns": {"base": "block/cablelight-lit", "rotateY": 90},
        },
        "lightHsvByType": {"*-warm-*": [5, 5, 13]},
        "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
        "texturesByType": {"*-tarwe": {"rust": {"base": "block/level3/pipe-tar"}}, "*-tarns": {"rust": {"base": "block/level3/pipe-tar"}}},
        "attributesByType": {f"*-flicker-{a}": {"offBlock": f"backrooms:cablelight-off-{a}"} for a in ("we", "ns", "none", "tarwe", "tarns")},
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
    # Climbing out of Level 3's flooded tunnel: the game only climbs a climbable block's collision boxes, so the rungs
    # have a thin one, 3 px deep, and the manhole's 2 px frame is climbable too, carrying a player on up through the
    # hole to the floor (a player against the rungs is clear of the frame). Standing on the frame never climbs: the
    # game only looks for something to climb from the feet up.
    shaped("level3", "manhole", "block/manhole", material="Metal", sounds=METAL, oriented=False,
           comment="An open manhole: the frame is solid, the middle drops into the flooded tunnel below", climbable=True,
           collisionSelectionBoxes=[
               {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 0.125},
               {"x1": 0, "y1": 0, "z1": 0.875, "x2": 1, "y2": 1, "z2": 1},
               {"x1": 0, "y1": 0, "z1": 0.125, "x2": 0.125, "y2": 1, "z2": 0.875},
               {"x1": 0.875, "y1": 0, "z1": 0.125, "x2": 1, "y2": 1, "z2": 0.875}],
           resistance=8, requiredMiningTier=3)
    rungs = {"x1": 0.1875, "y1": 0, "z1": 0, "x2": 0.8125, "y2": 1, "z2": 0.1875}
    shaped("level3", "rungs", "block/rungs", material="Metal", sounds=METAL, oriented=False,
           comment="Ladder rungs down the manhole shaft", climbable=True, collisionbox=rungs, selectionbox=rungs)
    # Layout version 9's manholes (WorldLayout.AddManholeTunnel, gen_shapes.manhole_ladder): an opening two blocks long
    # with a ladder two wide down the side the corridor goes on past it, in halves (left and right as seen facing it),
    # the top half at the floor. The collision box is the vanilla ladder's, 3 px deep against the wall, from the
    # landing to the lip, so the opening is the whole two blocks bar the ladder, a player stepping in anywhere is
    # within the game's reach of the rungs (0.5 blocks) and stops, and climbing out goes straight off the top of the
    # ladder onto the floor behind it. The lip, rails above the floor and the open lid are drawn only.
    parts = ["topleft", "topright", "left", "right"]
    ladder_box = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 0.1875}
    write("level3", "manholeladder", {
        "code": "manholeladder",
        "variantgroups": [{"code": "part", "states": parts}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-topleft-north", "*-topright-north"], "decorative": ["*-topleft-north", "*-topright-north"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {f"*-{p}-{s}": {"base": f"block/manholeladder-{p}", "rotateY": ROTATE[s]} for p in parts for s in SIDES},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "climbable": True,
        "collisionboxByType": {f"*-{s}": dict(ladder_box, rotateY=ROTATE[s]) for s in SIDES},
        "selectionboxByType": {f"*-{s}": dict(ladder_box, rotateY=ROTATE[s]) for s in SIDES},
        "lightAbsorption": 0, "resistance": 8, "requiredMiningTier": 3, "sounds": METAL,
    }, "A manhole's ladder (layout version 9): the top half at the floor with its lip, rails and lid, or a length below")
    shaped("level3", "tunnelstep", "block/tunnelstep", material="Stone", sounds=STONE, oriented=False,
           comment="The half step out of a flooded tunnel onto the dry landing at the foot of a manhole's ladder",
           box=(0, 0, 0, 1, 0.5, 1), resistance=8, requiredMiningTier=3)


def level4():
    cube("level4", "officewall", "block/level4/officewall", comment="Off-white office drywall", randomizeAxes="xyz")  # (D4) by height too
    # (B7) The same paint in every version; the second (a filled nail hole or two, a touched-up patch) one block in six
    _retexture("level4", "officewall", textures=with_alternates(None, [{"base": "block/level4/officewall"}] * 5 +
                                                                    [{"base": "block/level4/officewall-2"}]))
    cube("level4", "officewindow", "block/level4/officewindow", material="Glass", sounds=GLASS,
         comment="A window onto rain and fog that never ends; its grey storm light is the main light on the floor",
         lightHsv=[36, 1, 7], lightAbsorption=0, drops=[], randomizeAxes="xyz",
         sounds_override=None)
    # (B7 round 2) two rain versions, so the runs are not the same on every pane
    _retexture("level4", "officewindow", textures=with_alternates(None, [{"base": "block/level4/officewindow"},
                                                                         {"base": "block/level4/officewindow-2"}]))
    glass = {
        "code": "officeglass", "creativeinventory": {"general": ["*"], "construction": ["*"]},
        # (Level 4 art) a model from detail/officeglass.json (gen_detail): the pane inset 0.05 from the floor and ceiling planes
        # it used to lie on (the shimmer against the carpet and the ceiling tiles)
        "blockmaterial": "Glass", "drawtype": "json", "renderpass": "Transparent",
        "shape": {"base": "block/detail/officeglass"},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "faceCullMode": "NeverCull",
        "lightAbsorption": 0, "resistance": 1, "sounds": GLASS,
    }
    write("level4", "officeglass", glass, "Glass conference-room partition")
    cube("level4", "officecarpet", "block/level4/officecarpet-{type}", material="Cloth", sounds=CLOTH, states=["plain", "ghost"],
         comment="Low-pile office carpet; 'ghost' has the darker mark of furniture that once stood there")
    # (B7) Loop pile in versions that meet without a step (gen_textures.office_carpet), each turned at random
    _retexture("level4", "officecarpet", {
        "*-plain": with_alternates(None, [a for v in ("", "-2", "-3") for a in turned(f"block/level4/officecarpet-plain{v}")]),
        "*-ghost": with_alternates(None, [a for v in ("", "-2") for a in turned(f"block/level4/officecarpet-ghost{v}")])})
    cube("level4", "officeceiling", "block/level4/officeceiling", material="Ceramic", sounds=GLASS,
         comment="2x4 drop-ceiling tiles; the void above sometimes hides wire, brackets and rotten battens", drops=CEILING_DROPS, resistance=1)
    # (B7) Level 0's ceiling module in the office's 2 x 4 layout, in three versions, each also turned half round
    _retexture("level4", "officeceiling", textures=with_alternates(
        None, [a for v in ("", "-2", "-3") for a in turned(f"block/level4/officeceiling{v}", (0, 180))]))
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
    # (L3 art) elevatordoor is a model now (a freight lift on all four sides): gen_detail.py writes it
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
         randomizeAxes="xyz",  # (D4) the panel's versions picked by height too
         comment="Hotel walls: mahogany wainscot, a red damask panel in a gilt frame, a cream frieze")
    # (B8) The damask panel cut from the roll at three places (and one in eight with an old water mark), picked at
    # random block by block
    L5 = "block/level5/"
    panel = [{"base": L5 + "hotelwall-panel" + v} for v in ("", "-2", "-3", "", "-2", "-3", "", "-4")]
    _retexture("level5", "hotelwall", by_type={
        "*-wainscot": {"all": {"base": L5 + "hotelwall-wainscot"}},
        "*-panel": with_alternates(None, panel),
        "*-frieze": {"all": {"base": L5 + "hotelwall-frieze"}}})
    fixture = {
        "code": "hotelfixture",
        "variantgroups": [{"code": "type", "states": ["sconce", "portrait", "beverly"]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {"*": {"base": "block/hotelfixture-{type}"}},
        # (B8) four portraits, picked at random
        "textures": {"panel": {"base": "block/level5/hotelwall-panel"},
                     "portrait": {"base": "block/level5/portrait",
                                  "alternates": [{"base": f"block/level5/portrait-{k}"} for k in (2, 3, 4)]}},
        "lightHsvByType": {"*-sconce": [6, 5, 11]},
        "resistance": 2, "lightAbsorption": 99, "lightAbsorptionByType": {"*-sconce": 0}, "sounds": WOOD,
        "particlePropertiesByType": {"*-sconce": _sconce_flames()},
    }
    write("level5", "hotelfixture", fixture, "Hotel wall panels with a candle sconce, a portrait, or The Beverly Room's placard")
    cube("level5", "hotelcarpet", "block/level5/hotelcarpet-{type}", material="Cloth", sounds=CLOTH, states=["damask", "maroon", "lobby"],
         comment="Red and gold damask, near-black ballroom maroon, and tan lobby carpet")
    # (B8) Three versions of each carpet, each turned at random (they share one ground: gen_textures.hotel_carpet)
    _retexture("level5", "hotelcarpet", by_type={
        f"*-{k}": with_alternates(None, [t for v in ("", "-2", "-3") for t in turned(f"{L5}hotelcarpet-{k}{v}")])
        for k in ("damask", "maroon", "lobby")})
    cube("level5", "hotelwood", "block/level5/hotelwood", material="Wood", sounds=WOOD, comment="Dark walnut floorboards")
    # (B8) Five versions of the boards (the plain one twice; each other has one butt joint, elsewhere), never turned:
    # the boards keep their direction
    _retexture("level5", "hotelwood", textures=with_alternates(None, [{"base": f"{L5}hotelwood{v}"} for v in ("", "-2", "-3", "", "-4", "-5")]))
    # The grand rooms' coffered ceiling is drawn from shapes (coffer, a beam along X or Z, two beams crossing) that let
    # light through, so the beams hanging under it are lit on their sides; "beams" is the old painted ceiling, kept
    # for rooms generated before
    beams = {"coffer": "block/hotelceiling-coffer", "beam-we": "block/hotelceiling-beam", "beam-cross": "block/hotelceiling-beamcross"}
    ceiling = {
        "code": "hotelceiling",
        "variantgroups": [{"code": "type", "states": ["cream", "beams", "coffer", "beam-we", "beam-ns", "beam-cross"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Wood",
        "drawtypeByType": {"*-cream": "cube", "*-beams": "cube", "*": "json"},
        "shapeByType": {**{f"*-{k}": {"base": v} for k, v in beams.items()},
                        "*-beam-ns": {"base": "block/hotelceiling-beam", "rotateY": 90}},
        "texturesByType": {"*-cream": {"all": {"base": "block/level5/hotelceiling-cream"}},
                           "*-beams": {"all": {"base": "block/level5/hotelceiling-beams"}}},
        "sideopaqueByType": {"*-cream": {"all": True}, "*-beams": {"all": True}, "*": {"all": False}},
        "resistance": 2,
        "lightAbsorptionByType": {"*-cream": 99, "*-beams": 99, "*": 0},
        "sounds": WOOD,
    }
    write("level5", "hotelceiling", ceiling, "Cream corridor ceiling, and the coffered ceiling and mahogany beams of the grand rooms")
    cube("level5", "marblecolumn", "block/level5/marble", comment="Red faux-marble column")
    cube("level5", "plasterwall", "block/level5/plaster", comment="Stained plaster of the boiler halls")
    cube("level5", "staffsign", "block/level5/staffsign", material="Wood", sounds=WOOD, comment="STAFF ONLY sign above the doors to the boiler halls")
    # (B8) The doors are geometry (gen_shapes.hotel_door): the same codes and parts; each upper part gives the shape's
    # brass plate its own number
    door = {
        "code": "hoteldoor",
        "variantgroups": [{"code": "part", "states": ["lower"] + [f"upper{i}" for i in range(10)]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {"*-lower": {"base": "block/hoteldoor-lower"}, "*": {"base": "block/hoteldoor-upper"}},
        "texturesByType": {f"*-upper{i}": {"plate": {"base": f"block/level5/hoteldoor-plate{i}"}} for i in range(10)},
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


def level2():
    """(L2 placement) Level 2's fittings that lead somewhere, placed from layout version 9 (the shapes are
    tools/gen_shapes.py's tunnel_fittings, machine_cabinet("up") and feed_pipe). The rest of Level 2's blocks are
    hand-written."""
    # Wall blocks like tunnelwall's, the fittings on every face that looks into the tunnel
    fittings = ["machinerytop", "pipesvalve", "riservalve"]
    write("level2", "tunnelfitting", {
        "code": "tunnelfitting",
        "variantgroups": [{"code": "type", "states": fittings}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Stone",
        "drawtype": "json",
        "shapeByType": {f"*-{t}": {"base": f"block/tunnelfitting-{t}"} for t in fittings},
        "textures": {"wall": {"base": "block/level2/tunnelwall-plain"}},
        "resistance": 8, "requiredMiningTier": 3, "lightAbsorption": 99, "sounds": STONE,
    }, "Level 2 tunnel walls with fittings that lead somewhere: a wall cabinet's conduits carried up into the ceiling, "
       "a gate valve in the wall pipes, a valve at the foot of a riser")
    # The machine cabinet (as the hand-written machinecabinet) with its feed pipe straight up out of its top, into the
    # pipe above it
    write("level2", "machinecabinetfeed", {
        "code": "machinecabinetfeed",
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Metal",
        "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "block/machinecabinet-feed", "rotateY": ROTATE[s]} for s in SIDES},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 3,
        # Wiring and windings: copper for the crucible (as machinecabinet)
        "drops": [
            {"type": "item", "code": "game:flaxtwine", "quantity": {"avg": 0.3, "var": 0.3}},
            {"type": "item", "code": "scrapwire", "quantity": {"avg": 1.5, "var": 1}},
            {"type": "item", "code": "game:metalbit-copper", "quantity": {"avg": 1.5, "var": 1}},
        ],
        "sounds": {"place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"},
    }, "A machine cabinet whose feed pipe rises out of its top into the pipe above it (feedpipe)")
    # The feed pipe above a machine cabinet, up into the overhead bundle (its model reaches into the block above)
    pipe_box = {"x1": 0.6875, "y1": 0, "z1": 0.625, "x2": 0.875, "y2": 1, "z2": 1}
    write("level2", "feedpipe", {
        "code": "feedpipe",
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Metal",
        "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "block/feedpipe", "rotateY": ROTATE[s]} for s in SIDES},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "resistance": 3,
        "collisionboxByType": {f"*-{s}": dict(pipe_box, rotateY=ROTATE[s]) for s in SIDES},
        "selectionboxByType": {f"*-{s}": dict(pipe_box, rotateY=ROTATE[s]) for s in SIDES},
        "sounds": METAL,
    }, "The feed pipe from a machine cabinet up into the overhead pipes")


def fix_ambients():
    """Adds ambient sounds to blocks that need them (done after writing, to keep the helpers simple)."""
    for folder, code, ambient, count in (("level3", "transformer", "backrooms:ambient/transformer", 4),
                                         ("level4", "officewindow", "backrooms:ambient/rain", 12)):
        # (Level 5's turntable and speakers carry no ambient sound: AtmosphereSystem.L5.cs plays one tune at a time)
        path = os.path.join(OUT, folder, code + ".json")
        with open(path, encoding="utf-8") as f:
            lines = f.read()
        comment, _, body = lines.partition("\n") if lines.startswith("//") else ("", "", lines)
        block = json.loads(body)
        block.pop("sounds_override", None)
        block["sounds"] = dict(block["sounds"], ambient=ambient, ambientBlockCount=count)
        with open(path, "w", encoding="utf-8") as f:
            f.write((comment + "\n" if comment else "") + json.dumps(block, indent="\t") + "\n")


if __name__ == "__main__":
    level2()
    level3()
    level4()
    level5()
    fix_ambients()
    import salvage
    salvage.apply()
    print("block types written")
