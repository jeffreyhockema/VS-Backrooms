"""Generates the detail added to Levels 1, 3, 4 and 5: props, wall decorations, signs, doors, elevators and floor
variants, with their textures, 3D shapes, block types and English names.

Run from the repo root:  python tools/gen_detail.py
Everything is written to block/detail/ folders (textures, shapes, blocktypes); names are merged into lang/en.json.
"""
import json
import math
import os
import random

import detail_textures
import fire_fx
import l1props as L1
import l4props as L4
import modelkit as K
from gen_shapes import louvre, octagon, office_chair, round_pipe, round_riser
from detail_kit import (ASSETS, CEILING_DROPS, CLOTH, DEAD_LIGHT_DROPS, GLASS, LANG, MANIFEST, METAL, ROTATE, SIDES,
                        STONE, WOOD, Decor, block, bx, cube, cuboid, cyl, name, prop, seam_halves, shape, shift, tpath, turn, wall_family,
                        write_json)


def plate(nm, frm, to, front, side, glow=0):
    """A flat panel with a picture on its front (north) face and plain sides."""
    return [bx(nm, frm, to, front, glow=glow, faces=("north",), full=True),
            bx(nm + "Sides", frm, to, side, faces=("east", "west", "up", "down"))]


def gilt_frame(nm, x1, y1, x2, y2, w, z1, z2, tex="gilt"):
    """(B8) A picture frame's member ring: four boxes w wide round x1..x2, y1..y2, from z1 to z2 (as gen_shapes
    level5's portrait frame)."""
    return [bx(nm + "T", (x1, y2 - w, z1), (x2, y2, z2), tex, faces=("north", "east", "west", "up", "down")),
            bx(nm + "B", (x1, y1, z1), (x2, y1 + w, z2), tex, faces=("north", "east", "west", "up", "down")),
            bx(nm + "L", (x1, y1 + w, z1), (x1 + w, y2 - w, z2), tex, faces=("north", "east", "west")),
            bx(nm + "R", (x2 - w, y1 + w, z1), (x2, y2 - w, z2), tex, faces=("north", "east", "west"))]


def hospital_bed_b14():
    """(B14) The hospital bed's textures (hospbed-*, matlib) and its two halves: {"head": boxes, "foot": boxes}."""
    import matlib as M
    from detail_kit import seed_of as sd
    tube = M.brushed_metal(sd("hospbedtube"), base=(206, 208, 206), grain=3, direction="h", sheen=10)
    detail_textures.save(tube, "hospbed-tube")
    detail_textures.save(M.painted_metal(sd("hospbeddeck"), base=(98, 102, 106), panel=False, chips=2, under=(150, 150, 146)), "hospbed-deck")
    panel = M.noise_hv((234, 230, 216), 2, sd("hospbedpanel"), mottle=3, cells=(16, 8))
    detail_textures.save(panel, "hospbed-panel")
    recess = M.noise_hv((222, 218, 204), 2, sd("hospbedrecess"), mottle=3, cells=(16, 8))
    detail_textures.save(recess, "hospbed-recess")
    mat = M.noise_hv((214, 222, 228), 2, sd("hospbedmattress"), mottle=3, cells=(16, 8))
    for x in range(32):  # the welt seams along the side: the box is 3.7 units high, so rows 0-7 show
        for y, f in ((0, 0.06), (1, -0.10), (6, -0.10), (7, 0.05)):
            M.touch(mat, x, y, f)
    detail_textures.save(mat, "hospbed-mattress")
    detail_textures.save(M.fabric(sd("hospbedsheet"), base=(236, 238, 236), weave="plain", contrast=3, grain=2, mottle=3), "hospbed-sheet")
    blanket = M.fabric(sd("hospbedblanket"), base=(206, 220, 230), weave="basket", contrast=4, grain=2, mottle=3)
    for y in range(32):
        for x in range(32):
            if x % 4 == 0 and y % 4 == 0:  # the cellular blanket's open weave
                M.touch(blanket, x, y, -0.06)
    detail_textures.save(blanket, "hospbed-blanket")
    pillow = M.fabric(sd("hospbedpillow"), base=(240, 240, 236), weave="plain", contrast=3, grain=2, mottle=2)
    M.ao_border(pillow, 3, 0.10)
    detail_textures.save(pillow, "hospbed-pillow")
    detail_textures.save(M.rubber(sd("hospbedrubber"), base=(46, 46, 48)), "hospbed-rubber")

    T_, D_, P_, R_ = "hospbed-tube", "hospbed-deck", "hospbed-panel", "hospbed-recess"
    els = []

    def board(nm, z0, z1, y0, y1):
        """A moulded board between two tube posts: a frame round a recessed panel, a tube rail along the top."""
        out = [bx(nm + "Back", (1.6, y0, z0 + 0.3), (14.4, y1, z1), P_, faces=("north", "south", "east", "west", "up", "down")),
               bx(nm + "Panel", (3.0, y0 + 1.6, z0 + 0.15), (13.0, y1 - 1.6, z0 + 0.3), R_, faces=("north",)),
               bx(nm + "PanelS", (3.0, y0 + 1.6, z1), (13.0, y1 - 1.6, z1 + 0.15), R_, faces=("south",)),
               bx(nm + "FrameT", (1.6, y1 - 1.6, z0), (14.4, y1, z0 + 0.3), P_, faces=("north", "east", "west", "up", "down")),
               bx(nm + "FrameB", (1.6, y0, z0), (14.4, y0 + 1.6, z0 + 0.3), P_, faces=("north", "east", "west", "up", "down")),
               bx(nm + "FrameL", (1.6, y0 + 1.6, z0), (3.0, y1 - 1.6, z0 + 0.3), P_, faces=("north", "east", "west")),
               bx(nm + "FrameR", (13.0, y0 + 1.6, z0), (14.4, y1 - 1.6, z0 + 0.3), P_, faces=("north", "east", "west")),
               bx(nm + "Rail", (0.6, y1, z0 + 0.1), (15.4, y1 + 0.9, z1 + 0.2), T_)]
        for k, x in enumerate((0.6, 14.4)):
            out.append(bx(f"{nm}Post{k}", (x, 2.2, z0 + 0.1), (x + 1.0, y1, z1 + 0.2), T_))
        return out
    els += board("Head", 0.2, 1.2, 6.5, 18.5) + board("Foot", 30.6, 31.6, 6.5, 14.5)
    # The deck: tube side rails, a steel platform, a spine, and castors under each post
    els += [bx("SideW", (1.0, 7.0, 1.2), (2.0, 8.0, 30.6), T_), bx("SideE", (14.0, 7.0, 1.2), (15.0, 8.0, 30.6), T_),
            bx("Deck", (2.0, 7.2, 1.2), (14.0, 7.8, 30.6), D_),
            bx("Spine", (6.5, 4.0, 4.0), (9.5, 7.2, 28.0), D_),
            bx("StrutN", (2.0, 5.0, 5.5), (14.0, 6.0, 6.5), D_), bx("StrutS", (2.0, 5.0, 25.5), (14.0, 6.0, 26.5), D_)]
    for k, (x, z) in enumerate(((1.1, 0.7), (14.9, 0.7), (1.1, 31.1), (14.9, 31.1))):
        els += [bx(f"Fork{k}", (x - 0.5, 1.2, z - 0.5), (x + 0.5, 2.2, z + 0.5), D_),
                bx(f"Wheel{k}", (x - 0.35, 0, z - 0.85), (x + 0.35, 1.5, z + 0.85), "hospbed-rubber")]
    # The mattress, the sheet over it, the blanket turned down with its sides hanging, the pillow, the folded quilt
    els += [bx("Mattress", (2.0, 7.8, 1.4), (14.0, 11.5, 30.5), "hospbed-mattress", faces=("north", "south", "east", "west")),
            bx("Sheet", (1.9, 11.5, 1.35), (14.1, 11.7, 30.55), "hospbed-sheet", faces=("north", "south", "east", "west", "up")),
            bx("Blanket", (1.7, 11.7, 8.0), (14.3, 12.2, 30.75), "hospbed-blanket", faces=("north", "south", "up")),
            bx("DrapeW", (1.5, 9.0, 8.0), (1.7, 12.2, 30.75), "hospbed-blanket", faces=("north", "south", "west", "down")),
            bx("DrapeE", (14.3, 9.0, 8.0), (14.5, 12.2, 30.75), "hospbed-blanket", faces=("north", "south", "east", "down")),
            bx("Turndown", (1.6, 12.2, 8.0), (14.4, 12.6, 10.0), "hospbed-sheet"),
            bx("Pillow", (3.5, 11.7, 1.9), (12.5, 13.4, 6.4), "hospbed-pillow"),
            bx("PillowTop", (4.2, 13.4, 2.5), (11.8, 14.0, 5.8), "hospbed-pillow", faces=("north", "south", "east", "west", "up")),
            bx("QuiltTop", (3.0, 12.2, 23.5), (13.0, 14.2, 29.5), "hospitalquilt", faces=("up",)),
            bx("Quilt", (3.0, 12.2, 23.5), (13.0, 14.2, 29.5), "hospitalquiltfold", faces=("north", "east", "south", "west"), full=True),
            bx("Chart", (6.0, 9.5, 31.8), (10.0, 13.6, 32.1), "paper", faces=("south", "east", "west", "up", "down")),
            bx("Clip", (7.4, 13.2, 32.1), (8.6, 13.9, 32.35), T_)]
    # The drop rails at the head, either side: two tube rails on two posts
    for side, (x0, x1) in (("W", (0.2, 1.0)), ("E", (15.0, 15.8))):
        els += [bx(f"RailTop{side}", (x0, 15, 3), (x1, 15.8, 14), T_), bx(f"RailMid{side}", (x0, 12.6, 3), (x1, 13.2, 14), T_),
                bx(f"RailPost1{side}", (x0, 8, 4), (x1, 15, 4.8), T_), bx(f"RailPost2{side}", (x0, 8, 12.2), (x1, 15, 13), T_)]

    def half(lo, hi):
        out = []
        for e in els:
            z1, z2 = e["from"][2], e["to"][2]
            if z2 <= lo or z1 >= hi:
                continue
            e = json.loads(json.dumps(e))
            e["from"][2], e["to"][2] = max(z1, lo) - lo, min(z2, hi) - lo
            if hi == 32 and z2 > 32:
                e["to"][2] = z2 - lo  # the chart stands a little proud of the foot block, as before
            if lo == 16 and z1 < 16:
                e["faces"].pop("north", None)  # cut at the block edge: the head half carries on there
            if hi == 16 and z2 > 16:
                e["faces"].pop("south", None)
            for f, face in e["faces"].items():
                if face["uv"][0] == 0 and face["uv"][1] == 0 and face["uv"] != [0, 0, 16, 16]:
                    (x1, y1, zz1), (x2, y2, zz2) = e["from"], e["to"]
                    w, h, d = x2 - x1, y2 - y1, zz2 - zz1
                    a, b = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[f]
                    face["uv"] = [0, 0, round(min(16, max(a, 0.5)), 4), round(min(16, max(b, 0.5)), 4)]
            out.append(e)
        return out
    return {"head": half(0, 16), "foot": half(16, 32)}


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


def _default_uv(e, face):
    """The UVs bx() gives a plain face of this box (its own size, so the texture keeps its scale)."""
    (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
    w, h, d = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)
    a, b = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]
    return [0, 0, min(16, max(a, 0.5)), min(16, max(b, 0.5))]


def split_blocks(els, width, depth):
    """Cuts a model that spans width x depth blocks (modelled facing north from x, z = 0: x across, z from the front
    back) into one model per block, each moved into its own block: {(i, j): boxes}, i the column from the west, j the
    row from the front. Boxes are cut along the seams (the faces left on a seam are dropped, plain faces keep their
    texture's scale); a box turned about one axis can still be cut along that axis, and anything else turned goes
    whole to the block holding its turning point (reaching over the seam a little is fine)."""
    out = {(i, j): [] for j in range(depth) for i in range(width)}
    for e in els:
        rx, ry, rz = e.get("rotationX", 0), e.get("rotationY", 0), e.get("rotationZ", 0)
        o = e.get("rotationOrigin")
        cuts = {0: not ry and not rz, 2: not rx and not ry}
        spans = {}
        for axis, n in ((0, width), (2, depth)):
            a, b = e["from"][axis], e["to"][axis]
            if cuts[axis]:
                spans[axis] = [k for k in range(n) if b > 16 * k and a < 16 * k + 16]
            else:
                at = o[axis] if o else (a + b) / 2
                spans[axis] = [min(n - 1, max(0, int(at // 16)))]
        for i in spans[0]:
            for j in spans[2]:
                c = json.loads(json.dumps(e))
                plain = {f: face["uv"] == _default_uv(e, f) for f, face in c["faces"].items()}
                for axis, k, lo_face, hi_face in ((0, i, "west", "east"), (2, j, "north", "south")):
                    if not cuts[axis]:
                        continue
                    a, b = c["from"][axis], c["to"][axis]
                    if a < 16 * k:
                        c["from"][axis] = 16 * k
                        c["faces"].pop(lo_face, None)
                    if b > 16 * k + 16:
                        c["to"][axis] = 16 * k + 16
                        c["faces"].pop(hi_face, None)
                for f, face in c["faces"].items():
                    if plain[f]:
                        face["uv"] = _default_uv(c, f)
                c = shift([c], dx=-16 * i, dz=-16 * j)[0]
                out[(i, j)].append(c)
    return out


def multiblock_prop(code, english, els, width, depth, parts, boxes, material="Wood", sounds=WOOD, comment=None):
    """
    A prop as big as the real thing, over width x depth blocks: one model (facing north, see split_blocks) cut into a
    block per part, `parts` named row by row from the front-left (west) corner, each with its own box (`boxes`, by
    part, as the block it is in sees it). The layout lays the parts out together (WorldLayout.PartTile); breaking any
    of them breaks the whole thing (BackroomsPartnered), and only the first part holds what it gives (salvage.py).
    """
    cut = split_blocks(els, width, depth)
    by_type, boxes_by_type = {}, {}
    for n, part in enumerate(parts):
        path = shape(f"{code}-{part}", cut[(n % width, n // width)])
        for s in SIDES:
            by_type[f"*-{part}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
            boxes_by_type[f"*-{part}-{s}"] = cuboid(boxes[part], s)
    block(code, {
        "variantgroups": [{"code": "part", "states": list(parts)}, {"code": "side", "states": SIDES}],
        "behaviors": [{"name": "BackroomsPartnered", "properties": {"parts": list(parts), "width": width}}],
        "shapeByType": by_type,
        "creativeinventory": {"general": [f"*-{parts[0]}-north"], "decorative": [f"*-{parts[0]}-north"]},
        "blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "lightAbsorption": 0, "resistance": 1.5, "sounds": sounds,
        "collisionboxByType": boxes_by_type, "selectionboxByType": boxes_by_type,
    }, comment or english)
    name(code + "-*", english)


TURNED = {"asphalt", "asphalt-leaves", "asphalt-wet", "housefloor-carpet", "housefloor-garage", "housefloor-driveway", "l6floor",
          "l6floor-wet", "dirtroad", "stubble", "jetty", "pool-coping", "snackfloor-terrazzo", "islandrock", "l3stone", "oceanceiling",
          "l1hallfloor", "officecarpet-papers", "officecarpet-stain"}
# Textures with other versions drawn beside them (graphics pass B4): a feature such as a scuff sits in one version
# only, and the block picks among them (each turned too, when the texture is in TURNED), so it lands in about one
# block in three and at a different place each time
ALTS = {"l1hallfloor": ["l1hallfloor-2", "l1hallfloor-3"],
        # (B6) the Sanctum's ashlar and flagstones: versions that differ only in which stone is darker
        "sanctumwall": ["sanctumwall-2", "sanctumwall-3"],
        # (B7) Level 4's carpet with papers on it (three arrangements) and with a spill (two places)
        "officecarpet-papers": ["officecarpet-papers-2", "officecarpet-papers-3"],
        "officecarpet-stain": ["officecarpet-stain-2"],
        # (B9) Level 6's cold walls, floor and ceiling (a damp run, a crack and a damp mark one block in eight or six);
        # the Snackrooms' terrazzo, chequered and quarry floors and their ceiling (a heel mark and a chip one in eight)
        "l6wall": ["l6wall"] * 5 + ["l6wall-2", "l6wall-3"], "l6floor": ["l6floor-2", "l6floor-3"],
        "l6ceiling": ["l6ceiling"] * 4 + ["l6ceiling-2"],
        "l6floor-wet": ["l6floor-wet-2", "l6floor-wet-3"],
        "snackfloor-terrazzo": ["snackfloor-terrazzo-2", "snackfloor-terrazzo-3"],
        "snackfloor-checker": ["snackfloor-checker"] * 5 + ["snackfloor-checker-2", "snackfloor-checker-3"],
        "snackfloor-quarry": ["snackfloor-quarry-2", "snackfloor-quarry-3"],
        "snackceiling-grid": ["snackceiling-grid-2", "snackceiling-grid-3"],
        # (B10) Level 7's island rock: three versions of its facets on one ground, and a fourth with a faint fracture
        # and lichen one block in eight; the ceiling over the sea, a damp stain and a few runs one block in seven each
        "islandrock": ["islandrock-2", "islandrock-3", "islandrock", "islandrock-2", "islandrock-3", "islandrock-4", "islandrock-2"],
        "oceanceiling": ["oceanceiling"] * 4 + ["oceanceiling-2", "oceanceiling-3"]}


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
        if isinstance(t, str) and t in ALTS:
            turns = (0, 90, 180, 270) if t in TURNED else (0,)
            tex.setdefault("alternates", []).extend(
                {"base": f"block/detail/{a}", "rotation": r} if r else {"base": f"block/detail/{a}"} for a in ALTS[t] for r in turns)
        data["texturesByType"][f"*-{k}"] = {"all": tex}
    data.update(extra)
    block(code, data, comment or (english if isinstance(english, str) else None))
    for k in kinds:
        name(f"{code}-{k}", english if isinstance(english, str) else english[k])


# Flames, fire and embers on the props that burn (offsets from the top middle of each prop's collision box)
# Burn barrel: licking flames rising out of the drum over the embers sunk inside it (the rim 13/16 up; the box tops
# out at 0.84), and sparks
BURNBARREL_FIRE = [fire_fx.fire(0, -0.08, 0, spread=(0.18, 0, 0.18), quantity=0.5, size=0.3),
                   fire_fx.embers(0, -0.1, 0, spread=(0.16, 0, 0.16), quantity=0.012)]
# Candelabra: a flame on each of its three candles (tops 18/16, 19/16 and 18/16 up; the box tops out at 1.1)
CANDELABRA_FLAMES = [fire_fx.flame(-0.28125, 0.025, 0), fire_fx.flame(0, 0.0875, 0), fire_fx.flame(0.28125, 0.025, 0)]
# Dining table: the candle in the middle (its top 16/16 up; the box tops out at 0.78)
DININGTABLE_FLAMES = [fire_fx.flame(0, 0.22, 0)]


# ======================= Signs and doors =======================

# The halves of a two-faced sign over a two-wide doorway (from detail_kit.seam_halves), by which block of the pair
# they are in: "lo" the one with the smaller coordinate along the wall (west, or north), "hi" the other. The models
# face north and south; "we" (a wall running west-east) leaves them so, "ns" turns them 90 degrees (anticlockwise
# from above: their north face looks west, their west end goes south). Seen from the north the left half is in the
# east block, so a west-east wall's west block takes the right half; turned, the left half is in the north block.
PAIR_MODELS = {("lo", "we"): ("r", 0), ("hi", "we"): ("l", 0), ("lo", "ns"): ("l", 90), ("hi", "ns"): ("r", 90)}


def exit_signs():
    face = [bx("Housing", (2, 3, -2.5), (14, 11, 0), "exithousing", faces=("north", "east", "west", "up", "down")),
            bx("Face", (2.4, 3.4, -2.6), (13.6, 10.6, -2.5), "exitface", glow=200, faces=("north",), uv=[0, 4, 16, 12])]
    sign = face + [turn(e, 2) for e in face]
    left, right = seam_halves(sign)
    by_type, pair_by_type = {}, {}
    # (The painted block's lintel, with the dark head of the door frame along its foot, as over a doorway without one)
    for material, wall in (("concrete", "concretewall"), ("whiteblock", "whiteblock-lintel"), ("drywall", "drywall")):
        path = shape(f"exitlintel-{material}", [cube(wall)] + sign)
        by_type[f"*-{material}-we"] = {"base": path, "rotateY": 0}
        by_type[f"*-{material}-ns"] = {"base": path, "rotateY": 90}
        halves = {"l": shape(f"exitlintelpair-{material}-l", [cube(wall)] + left),
                  "r": shape(f"exitlintelpair-{material}-r", [cube(wall)] + right)}
        for (half, axis), (model, rot) in PAIR_MODELS.items():
            pair_by_type[f"*-{material}-{half}-{axis}"] = {"base": halves[model], "rotateY": rot}
    lit = {"lightHsv": [0, 6, 6], "lightAbsorption": 0, "resistance": 4, "sounds": STONE}
    block("exitlintel", dict({
        "variantgroups": [{"code": "material", "states": ["concrete", "whiteblock", "drywall"]}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type}, **lit),
        "Lintel over a doorway with a lit EXIT sign on both faces")
    name("exitlintel-*", "EXIT Sign")
    # Over a two-wide doorway: the same sign in two halves, one in each block over the doorway, so that it hangs
    # centred over the doorway (see PAIR_MODELS). Both halves are lit as one whole sign is
    block("exitlintelpair", dict({
        "variantgroups": [{"code": "material", "states": ["concrete", "whiteblock", "drywall"]}, {"code": "half", "states": ["lo", "hi"]},
                          {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": pair_by_type}, **lit),
        "Lintel over a two-wide doorway with half of a lit EXIT sign on both faces: two side by side make one sign over its middle")
    name("exitlintelpair-*", "EXIT Sign")

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


def staff_plaques():
    """STAFF ONLY over the doors into Level 5's boiler halls, on the hotel's frieze (or plaster) above the doorway: a
    plate on both faces, centred over a one-wide doorway ("single") or, in halves, over a two-wide one ("lo", "hi":
    see PAIR_MODELS). Replaces the old all-over painted block (staffsign) in worlds from layout version 4 on."""
    plate_ = [bx("Plate", (2, 4, -0.6), (14, 12.25, 0), "staffplaque", faces=("north",), uv=[0, 2.5, 16, 13.5]),
              bx("Edge", (2, 4, -0.6), (14, 12.25, 0), "brass", faces=("east", "west", "up", "down"))]
    sign = plate_ + [turn(e, 2) for e in plate_]
    left, right = seam_halves(sign)
    by_type = {}
    for wall in ("frieze", "plaster"):
        models = {"single": shape(f"staffplaque-{wall}", [cube(wall)] + sign),
                  "l": shape(f"staffplaque-{wall}-l", [cube(wall)] + left), "r": shape(f"staffplaque-{wall}-r", [cube(wall)] + right)}
        by_type[f"*-{wall}-single-we"] = {"base": models["single"], "rotateY": 0}
        by_type[f"*-{wall}-single-ns"] = {"base": models["single"], "rotateY": 90}
        for (half, axis), (model, rot) in PAIR_MODELS.items():
            by_type[f"*-{wall}-{half}-{axis}"] = {"base": models[model], "rotateY": rot}
    block("staffplaque", {
        "variantgroups": [{"code": "wall", "states": ["frieze", "plaster"]}, {"code": "part", "states": ["single", "lo", "hi"]},
                          {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-single-we"], "decorative": ["*-single-we"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": by_type,
        "lightAbsorption": 99, "resistance": 2, "sounds": WOOD,
    }, "STAFF ONLY plate over a doorway into the boiler halls, on both faces (in halves over a two-wide doorway)")
    name("staffplaque-*", "Staff Only Sign")


def lift_leaf_panels(part, half):
    """(B8) A modern lift leaf's two inset panels as geometry: stiles, rails and a mid rail of brushed steel standing
    0.4 out of the leaf, the panels the leaf's face between them (the leaf of a 2-wide lift is one block wide; `half`
    l is the west leaf seen from the front, its jamb on the east). The leaf's face texture is plain brushed steel."""
    jamb_lo, jamb_hi = (0, 14.5) if half == "l" else (1.5, 16)
    x1, x2 = (jamb_lo + 0.5, jamb_hi - 0.25) if half == "l" else (jamb_lo + 0.25, jamb_hi - 0.5)
    z1, z2 = -0.9, -0.5
    els = [bx("StileA", (x1, 0, z1), (x1 + 1.5, 16 if part == "lower" else 14.5, z2), "liftsteel", faces=("north", "east", "west")),
           bx("StileB", (x2 - 1.5, 0, z1), (x2, 16 if part == "lower" else 14.5, z2), "liftsteel", faces=("north", "east", "west"))]
    if part == "lower":
        els += [bx("RailBottom", (x1 + 1.5, 0, z1), (x2 - 1.5, 2.5, z2), "liftsteel", faces=("north", "up")),
                bx("RailMid", (x1 + 1.5, 12.5, z1), (x2 - 1.5, 14.5, z2), "liftsteel", faces=("north", "up", "down"))]
    else:
        els += [bx("RailTop", (x1 + 1.5, 12, z1), (x2 - 1.5, 14.5, z2), "liftsteel", faces=("north", "down"))]
    return els


def knife_switch():
    """(L3 art) A double-pole knife switch on its slate base, closed: porcelain pedestals carry brass hinge lugs
    (with ears and a pin) at the foot and jaws (two cheeks each) at the head, a copper blade in each, a phase barrier
    of slate between the poles, a bakelite crossbar across both blades and a ribbed bakelite grip standing out of it.
    Footprint as before: the slate 3..13 by 1..15, nothing deeper than about 4.4 in front of the wall."""
    P, BR, CU, BK, SL = "ksporcelain", "ksbrass", "kscopper", "ksbakelite", "ksslate"
    els = K.bevelled_box("Slate", (3, 1, -1), (13, 15, 0), SL, b=0.25)
    for i, (x, y) in enumerate(((3.9, 1.9), (11.6, 1.9), (3.9, 13.4), (11.6, 13.4))):
        els.append(bx(f"Screw{i}", (x, y, -1.3), (x + 0.5, y + 0.5, -1), BR, faces=("north", "east", "west", "up", "down")))
    for pole, x in (("L", 4.25), ("R", 8.75)):
        for end, (y1, y2) in (("Foot", (1.75, 4.25)), ("Head", (11.25, 13.75))):
            n = pole + end
            z0 = -3.0 if end == "Head" else -2.75
            els += [K.box(n + "Pedestal", (x, y1, -1.5), (x + 3, y2, -1), P),
                    K.box(n + "Plate", (x + 0.25, y1 + 0.25, -1.75), (x + 2.75, y2 - 0.25, -1.5), BR),
                    K.box(n + "CheekA", (x + 0.25, y1 + 0.25, z0), (x + 0.75, y2 - 0.25, -1.75), BR),
                    K.box(n + "CheekB", (x + 2.25, y1 + 0.25, z0), (x + 2.75, y2 - 0.25, -1.75), BR)]
        els += [K.box(pole + "Blade", (x + 0.75, 2.75, -2.5), (x + 2.25, 13.0, -2.0), CU),
                K.box(pole + "PinA", (x - 0.1, 2.9, -2.45), (x + 0.25, 3.5, -2.05), BR),
                K.box(pole + "PinB", (x + 2.75, 2.9, -2.45), (x + 3.1, 3.5, -2.05), BR)]
    els += [K.box("Barrier", (7.75, 2.5, -2.25), (8.25, 14.0, -1.0), SL),
            K.box("Crossbar", (4.75, 8.25, -3.3), (11.25, 10.0, -2.45), BK),
            K.box("CrossbarRivetL", (5.4, 8.8, -3.55), (6.0, 9.4, -3.3), BR, faces=("north", "east", "west", "up", "down")),
            K.box("CrossbarRivetR", (10.0, 8.8, -3.55), (10.6, 9.4, -3.3), BR, faces=("north", "east", "west", "up", "down")),
            K.box("Shaft", (7.5, 8.75, -3.9), (8.5, 9.5, -3.3), BK)]
    els += K.bevelled_box("Grip", (6.75, 8.0, -4.4), (9.25, 10.25, -3.4), "ksgrip", b=0.25)
    return els


def mirror_z(els):
    """(L3 art) The same elements seen from the other side of the block (z -> 16 - z, north faces south), so a door
    set in a wall is a door from behind as well."""
    out = []
    for e in json.loads(json.dumps(els)):
        e["from"][2], e["to"][2] = round(16 - e["to"][2], 4), round(16 - e["from"][2], 4)
        f = e["faces"]
        e["faces"] = {k: v for k, v in {"north": f.get("south"), "south": f.get("north"), "east": f.get("east"), "west": f.get("west"),
                                        "up": f.get("up"), "down": f.get("down")}.items() if v is not None}
        e["name"] += "Back"
        out.append(e)
    return out


def l3_lift(part):
    """(L3 art) Level 3's freight elevator, one block wide and two high, doors on all four sides (the corridor wall
    has no facing to turn it by): a frame of dark painted steel, two steel leaves, each with raised stiles and rails
    round an inset panel, a hazard stripe across the foot, the call plate on the right jamb and, in the upper block,
    a lit floor indicator in the header."""
    top = 16 if part == "lower" else 13.0
    front = [bx("JambL", (0, 0, -0.9), (2.5, 16, 0), "l3liftframe", faces=("north", "east", "west", "up", "down")),
             bx("JambR", (13.5, 0, -0.9), (16, 16, 0), "l3liftframe", faces=("north", "east", "west", "up", "down"))]
    if part == "upper":
        front += [bx("Header", (2.5, 13.0, -0.9), (13.5, 16, 0), "l3liftframe", faces=("north", "up", "down")),
                  bx("IndBezel", (3.0, 13.4, -1.15), (13.0, 15.6, -0.9), "l3liftframe", faces=("north", "east", "west", "up", "down")),
                  bx("Indicator", (3.5, 13.9, -1.2), (12.5, 15.1, -1.15), "l3liftind", glow=90, faces=("north",), full=True)]
    for k, (x1, x2) in enumerate(((2.5, 7.9), (8.1, 13.5))):
        front += [bx(f"Leaf{k}", (x1, 0, -0.45), (x2, top, -0.05), "l3liftleaf", faces=("north", "east", "west", "up")),
                  bx(f"StileA{k}", (x1 + 0.4, 0, -0.9), (x1 + 1.6, top, -0.45), "l3liftframe", faces=("north", "east", "west")),
                  bx(f"StileB{k}", (x2 - 1.6, 0, -0.9), (x2 - 0.4, top, -0.45), "l3liftframe", faces=("north", "east", "west")),
                  bx(f"RailMid{k}", (x1 + 1.6, 7.0, -0.9), (x2 - 1.6, 8.0, -0.45), "l3liftframe", faces=("north", "up", "down"))]
        if part == "lower":
            front += [bx(f"Kick{k}", (x1 + 1.6, 0, -0.9), (x2 - 1.6, 2.5, -0.45), "l3liftframe", faces=("north", "up")),
                      bx(f"Stripe{k}", (x1 + 1.6, 3.0, -0.9), (x2 - 1.6, 4.5, -0.45), "l3liftstripe", faces=("north",), full=True)]
        else:
            front.append(bx(f"RailTop{k}", (x1 + 1.6, top - 1.2, -0.9), (x2 - 1.6, top - 0.2, -0.45), "l3liftframe", faces=("north", "down")))
    if part == "lower":
        front += [bx("CallPlate", (13.6, 6.5, -1.3), (15.4, 11.5, -0.9), "l3liftcall", faces=("north",), full=True),
                  bx("CallRim", (13.6, 6.5, -1.3), (15.4, 11.5, -0.9), "l3liftframe", faces=("east", "west", "up", "down")),
                  bx("PullL", (6.1, 6.0, -1.5), (6.7, 9.5, -0.9), "ksbrass", faces=("north", "east", "west", "up", "down")),
                  bx("PullR", (9.3, 6.0, -1.5), (9.9, 9.5, -0.9), "ksbrass", faces=("north", "east", "west", "up", "down"))]
    els = [bx("Core", (0, 0, 0), (16, 16, 16), "l3liftframe")]
    for t in range(4):
        els += [dict(e, name=f"{e['name']}{t}") for e in K.turn(front, t)]
    return els


def cage_gate(half):
    """(B8) The antique lift's brass scissor gate as geometry: upright bars every 4 units and between each pair two
    diagonal straps crossing, so the gate is a lattice of diamonds; behind it the dark of the shaft (it was a picture of
    a lattice on a plate)."""
    els = [bx("Shaft", (0, 0, -0.8), (16, 16, -0.7), "cageshaft", faces=("north",), full=True)]
    for i, x in enumerate((0.25, 4, 8, 12, 15.75)):
        a, b = max(0, x - 0.3), min(16, x + 0.3)
        els.append(bx(f"Bar{i}", (a, 0, -1.4), (b, 16, -0.9), "brass", faces=("north", "east", "west")))
    L = math.hypot(4, 8) - 0.5  # (a little short, so the turned straps' corners stay inside the block)
    ang = math.degrees(math.atan2(8, 4))
    for c in range(4):
        cx = c * 4 + 2
        for r, cy in enumerate((4, 12)):
            for k, sgn in enumerate((1, -1)):
                els.append(bx(f"Strap{c}{r}{k}", (cx - L / 2, cy - 0.25, -1.3 + 0.1 * k), (cx + L / 2, cy + 0.25, -1.0 + 0.1 * k), "brass",
                              faces=("north", "up", "down"), rot=(0, 0, sgn * ang), origin=(cx, cy, -1.15)))
    return els


def doors():
    for code, english, tex in (("metaldoor", "Steel Door", "metaldoor"), ("officedoor", "Office Door", "officedoor")):
        if code == "metaldoor":
            # (Level 1 props) Drawn from a shape (the leaf and its hardware on all four sides), as Level 2's tunnel doors;
            # same code, groups and drawn size. No `textures` here: that would override every key of the shape.
            shapes = {part: shape(f"metaldoor-{part}", L1.steel_door(part)) for part in ("lower", "upper")}
            block(code, {
                "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
                "creativeinventory": {"general": ["*"], "construction": ["*"]},
                "blockmaterial": "Metal", "drawtype": "json",
                "shapeByType": {f"*-{part}": {"base": path} for part, path in shapes.items()},
                "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL,
            }, f"{english}, locked")
            name(f"{code}-*", english)
            continue
        # (Level 4 art) Drawn from a shape as the steel door: a veneer leaf and its hardware on all four sides. Still locked
        # (a pry bar forces it, see PryBar.cs); same code, groups and drawn size. No `textures`: they would override the shape's.
        shapes = {part: shape(f"officedoor-{part}", L4.office_door(part)) for part in ("lower", "upper")}
        block(code, {
            "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": "Wood", "drawtype": "json",
            "shapeByType": {f"*-{part}": {"base": path} for part, path in shapes.items()},
            "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": WOOD,
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
                    front = parts_fn(part, half)
                    # (L3 art) The back of a lift is a lift too: someone who arrives behind the wall sees doors, not drywall
                    els = [cube(wall_tex[part])] + front + mirror_z(front)
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
        return els + lift_leaf_panels(part, half)

    lift("liftdoor", "Elevator", {
        "drywall": {"lower": "drywall-base", "upper": "drywall", "header": "drywall"},
        "hotel": {"lower": "wainscot", "upper": "hotelpanel", "header": "frieze"},
    }, header, "Modern elevator doors, two blocks wide. Use them: each elevator leads to one fixed place")

    # (L3 art) Level 3's freight elevator (the old block was a cube with one painted line)
    lift_shapes = {part: shape(f"l3lift-{part}", l3_lift(part)) for part in ("lower", "upper")}
    block("elevatordoor", {
        "variantgroups": [{"code": "type", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {f"*-{part}": {"base": path} for part, path in lift_shapes.items()},
        "resistance": 2, "lightAbsorption": 99, "sounds": METAL, "drops": [],
        "behaviors": [{"name": "BackroomsThreshold", "properties": {"kind": "elevator"}}],
    }, "Freight elevator doors. Use them: each elevator leads to one fixed place, usually another elevator on another level")

    def dial(part, half):
        outer = (14, 16) if half == "l" else (0, 2)
        if part == "dial":
            return [bx("Dial", (0, 2, -0.8), (16, 15, 0), f"cagedial-{half}", glow=20, faces=("north",), full=True),
                    bx("Rim", (0, 1.5, -1.2), (16, 2.5, 0), "brass")]
        els = cage_gate(half) + [bx("Column", (outer[0], 0, -2), (outer[1], 16, 0), "brass")]
        els.append(bx("Rail", (0, 0 if part == "lower" else 14.5, -1.8), (16, 1.5 if part == "lower" else 16, -0.5), "brass"))
        if part == "lower":
            els.append(bx("Handle", (6 if half == "r" else 9, 7, -2.6), (7 if half == "r" else 10, 11, -1.4), "brass"))
        return els

    lift("cagelift", "Cage Elevator", {
        "hotel": {"lower": "wainscot", "upper": "hotelpanel", "dial": "frieze"},
        "plaster": {"lower": "plaster", "upper": "plaster", "dial": "plaster"},
    }, dial, "Antique copper-cage elevator, two blocks wide, with a floor dial above. Use it to ride")


# ======================= Level 1 =======================

def camp_tent():
    """
    A two-person ridge tent, two blocks by two (layout version 6 on; the old one-block "tent" stays for older worlds):
    green ripstop fly from the ground to a ridge pole 22/16 up (crouching height), on an upright pole at each end, the
    front laced shut but for the door, its flap rolled up and tied over it, a guy line from the ridge to a peg in front;
    inside on the orange groundsheet, a sleeping bag with its pillow at the back and a rolled bedroll. Facing north
    (the door), parts nw, ne (the front) and sw, se.
    """
    ridge, base_l, base_r = 22.0, 2.0, 30.0
    slope = math.hypot(16 - base_l, ridge)
    lean = math.degrees(math.atan2(16 - base_l, ridge))
    els = []
    # The fly, each side in two lengths up the slope (so its texture keeps its scale), its inside darker
    for nm, x, sign in (("FlyL", base_l, -1), ("FlyR", base_r, 1)):
        for k, (y1, y2) in enumerate(((0, slope / 2), (slope / 2, slope + 0.3))):
            e = bx(f"{nm}{k}", (x - 0.3, y1, 0.4), (x + 0.3, y2, 31.6), "tentfly", rot=(0, 0, sign * lean), origin=(x, 0, 16))
            e["faces"]["east" if sign < 0 else "west"]["texture"] = "#tentinside"
            els.append(e)
    els += [bx("RidgeCap", (14.8, 21.9, 0.45), (17.2, 22.7, 31.55), "tentfly"),
            bx("Ridge", (15.4, 21.1, 0.1), (16.6, 22.1, 31.9), "wood"),
            bx("PoleF", (15.6, 0, 1.5), (16.4, 21.1, 2.3), "wood"), bx("PoleB", (15.6, 0, 29.7), (16.4, 21.1, 30.5), "wood"),
            bx("Floor", (2.6, 0, 1.2), (29.4, 0.25, 30.8), "tarporange", faces=("up", "north", "south", "east", "west"))]

    # The ends: stepped to the slope of the fly, each step's top corners just inside the fly's thickness (so neither
    # they show through it nor the gaps under them much). (B4) One texture pixel to a step, so the edge reads as the
    # cloth's own edge and not as a staircase
    def gable(nm, z1, z2, door):
        out, steps = [], 44
        for k in range(steps):
            y1, y2 = ridge * k / steps, ridge * (k + 1) / steps
            hw = (16 - base_l) * (1 - y2 / ridge) + 0.3
            if hw <= 0.4:
                continue
            if door and y2 <= door[1] + 0.01:
                for side, (a, b) in (("L", (16 - hw, 16 - door[0])), ("R", (16 + door[0], 16 + hw))):
                    if b - a > 0.2:
                        out.append(bx(f"{nm}{k}{side}", (a, y1, z1), (b, y2, z2), "tentfly"))
            else:
                out.append(bx(f"{nm}{k}", (16 - hw, y1, z1), (16 + hw, y2, z2), "tentfly"))
        for e in out:
            e["faces"]["south" if door else "north"]["texture"] = "#tentinside"
        return out
    els += gable("Back", 30.6, 31.1, None)
    els += gable("Front", 0.9, 1.4, (5.0, ridge * 12 / 16))
    # The door flap rolled up and tied over the doorway, and the dark inside seen through it
    els += [bx("Roll", (10.6, 15.6, 0.1), (21.4, 17.4, 1.3), "tentfly"),
            bx("TieL", (12.2, 15.3, 0.05), (12.8, 17.7, 1.4), "string"), bx("TieR", (19.2, 15.3, 0.05), (19.8, 17.7, 1.4), "string")]
    # Pegs at the foot of the fly, and the guy line from the front of the ridge
    for x in (base_l - 1.2, base_r + 0.6):
        for z in (0.5, 30.9):
            els.append(bx("Peg", (x, 0, z), (x + 0.6, 1.4, z + 0.6), "wood"))
    rope = math.hypot(ridge, 3.2)
    els += [bx("Guy", (15.85, 0, -2.45), (16.15, rope, -2.15), "string", rot=(math.degrees(math.atan2(3.2, ridge)), 0, 0), origin=(16, 0, -2.3)),
            bx("GuyPeg", (15.6, 0, -2.8), (16.4, 1.3, -2.0), "wood")]
    # Inside: a sleeping bag along the left, its pillow at the back; a rolled bedroll and a pack on the right
    els += [bx("Bag", (5, 0.25, 6), (13, 1.6, 28.5), "sleepingbag"), bx("BagFold", (5, 1.6, 6), (13, 2.1, 10), "sleepingbaglining"),
            bx("Pillow", (6, 1.2, 25.5), (12, 3, 29.5), "bedrollpillow"),
            bx("Rolled", (18.5, 0.25, 25), (26.5, 3.6, 28.6), "bedroll"),
            bx("Pack", (19.5, 0.25, 19), (25.5, 7, 23.5), "toolboxred")]
    multiblock_prop("camptent", "Tent", els, 2, 2, ("nw", "ne", "sw", "se"), {
        "nw": (0.1, 0, 0.03, 1, 1.4, 1), "ne": (0, 0, 0.03, 0.9, 1.4, 1),
        "sw": (0.1, 0, 0, 1, 1.4, 0.97), "se": (0, 0, 0, 0.9, 1.4, 0.97)}, material="Cloth", sounds=CLOTH,
        comment="A two-person ridge tent two blocks by two, its door to the north (nw, ne the front; sw, se the back)")


def sleeping_bag():
    """A sleeping bag two blocks long (layout version 6 on; the old one-block "bedroll" stays for older worlds): faded red
    quilted nylon, its top turned back at the head to show the flannel lining, a pillow on the hood, a zip down one side.
    Head to the north (parts head, foot)."""
    els = [bx("Hood", (3, 0, 1.2), (13, 1.6, 4.2), "sleepingbag"),
           bx("Body", (2.5, 0, 4), (13.5, 1.8, 31), "sleepingbag"),
           bx("Turned", (2.5, 1.8, 4), (13.5, 2.5, 10.4), "sleepingbaglining"),
           bx("FoldEdge", (2.45, 1.8, 10), (13.55, 2.9, 11.2), "sleepingbag"),
           bx("Top", (3, 1.8, 11.2), (13, 2.4, 30.5), "sleepingbag"),
           bx("Zip", (13.5, 0.3, 11.2), (13.7, 1.7, 30.6), "sleepingbagzip", faces=("east", "up")),
           bx("Pillow", (4, 1.4, 1.5), (12, 3.8, 5.8), "bedrollpillow")]
    multiblock_prop("sleepingbag", "Sleeping Bag", els, 1, 2, ("head", "foot"), {
        "head": (0.15, 0, 0.07, 0.85, 0.16, 1), "foot": (0.15, 0, 0, 0.85, 0.16, 0.97)}, material="Cloth", sounds=CLOTH,
        comment="A sleeping bag two blocks long, head to the north (head, foot)")


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
        Decor("powerbox", "Power Box", {2: L1.power_box(), 3: L1.power_riser3(), 4: L1.power_riser4()}),
        Decor("breaker", "Breaker Panel", {2: L1.breaker_panel()}),
        Decor("outlet", "Wall Outlet", {1: plate("Outlet", (6, 4, -0.4), (10, 9, 0), "outlet", "white")}),
        Decor("extinguisher", "Fire Extinguisher", {2: L1.extinguisher()}),
        Decor("alarm", "Fire Alarm", {2: L1.fire_alarm()}),
        Decor("hosecab", "Fire Hose Cabinet", {2: L1.hose_cabinet()}),
        Decor("levelsign", "Level Marking", {2: [bx("Paint", (1, 1, -0.1), (15, 15, 0), "levelsign", faces=("north",), full=True)]}),
        Decor("stairsign", "Stairs Sign", {2: plate("Sign", (3, 5, -0.4), (13, 12, 0), "stairsign", "steel")}),
        Decor("note", "Note", {2: [bx("Paper", (6, 4, -0.15), (11, 10, 0), "note", faces=("north",), full=True)]}),
        Decor("graffiti", "Graffiti", {2: [bx("Paint", (0, 1, -0.1), (16, 15, 0), "graffiti", faces=("north",), full=True)]}),
        Decor("pipes", "Wall Pipes", {3: pipes}),
        Decor("standpipe", "Fire Standpipe", {rel: L1.standpipe(rel) for rel in (1, 2, 3, 4)}),
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
    # The painted floor of each of Level 1's stairwells from layout version 4 (the plain "levelsign" is P2, as before)
    floors = [Decor(f"levelsign{label}", "Level Marking", {2: [bx("Paint", (1, 1, -0.1), (15, 15, 0), f"levelsign-{label}", faces=("north",), full=True)]})
              for label in ("p5", "p4", "p3", "p2", "p1", "b1", "b2", "b3")]
    wall_family("l1deco", "Painted Block Wall", walls_white, decors + paintings + banners + floors)
    wall_family("concretedeco", "Concrete Wall", {1: "concretewall"}, decors + banners)
    wall_family("pillardeco", "Concrete Pillar", {1: "pillar"},
                [Decor(f"banner{i}", "Group Landmark", {3: [bx("Cloth", (2, -8, -0.6), (14, 15, -0.3), f"banner{i}", faces=("north", "south"), full=True),
                                                            bx("Cord", (1, 15, -0.8), (15, 15.6, 0), "string")]}) for i in range(4)])

    # ---- props ----
    prop("cardboardboxes", "Cardboard Boxes", carton("A", (1, 0, 1), (9, 7, 9)) + carton("B", (9.5, 0, 2), (15, 5, 8.5)) +
         carton("C", (2, 0, 9.5), (10, 6, 15)) + carton("D", (2, 7, 2), (8, 12, 8)) + carton("E", (10.5, 0, 10), (15, 9, 14.5)) +
         carton("F", (11, 9, 10.5), (14.5, 13, 14)), box=(0.06, 0, 0.06, 0.94, 0.8, 0.94), oriented=False, sounds=CLOTH)
    L1.write_drum()
    prop("workbench", "Workbench", L1.workbench(), box=(0, 0, 0.125, 1, 0.95, 0.94))
    prop("toolbox", "Toolbox", L1.toolbox(), box=(0.18, 0, 0.3, 0.82, 0.5, 0.7), material="Metal", sounds=METAL)
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
    camp_tent()
    sleeping_bag()
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
    # Burn barrel: an open steel drum, eight-sided, with a rolled rim, two hoops and a chime at the foot; the fire
    # burns low inside it on a bed of embers and charred brands, so it shows only over the rim
    def ring(nm, y1, y2, apothem, thick, tex, faces, inside=None, uv=None):
        """Eight plates round the drum's axis, each facing out (north before it is turned)."""
        side = 2 * apothem * math.tan(math.pi / 8) + 0.06
        out = []
        for k in range(8):
            el = bx(f"{nm}{k}", (8 - side / 2, y1, 8 - apothem), (8 + side / 2, y2, 8 - apothem + thick), tex, faces=faces,
                    rot=(0, k * 45, 0), origin=(8, (y1 + y2) / 2, 8),
                    uv=None if uv is None else [uv * k % 11, 0, uv * k % 11 + side, y2 - y1])
            if inside:
                el["faces"]["south"] = dict(el["faces"]["south"], texture="#" + inside)
            out.append(el)
        return out
    bed_side = 2 * 4.5 * math.tan(math.pi / 8)
    prop("burnbarrel", "Burn Barrel",
         ring("Wall", 0, 12.5, 5, 0.5, "burnbarrel", ("north", "south", "up"), inside="burnbarrelinside", uv=3.7)
         + ring("Rim", 12.3, 13.3, 5.3, 0.9, "burnbarrelrim", ("north", "south", "up", "down"))
         + ring("Hoop", 4, 4.8, 5.2, 0.3, "burnbarrelrim", ("north", "up", "down"))
         + ring("Chime", 0, 0.6, 5.15, 0.3, "burnbarrelrim", ("north", "up"))
         # The bed of embers: four strips across the drum at 45 degrees make its eight-sided floor (stepped a hair
         # apart so they do not fight), and two charred brands leaning in it
         + [bx(f"Embers{k}", (3.5, 9.6, 8 - bed_side / 2), (12.5, 9.8 + 0.02 * k, 8 + bed_side / 2), "embers", glow=255,
               faces=("up",), rot=(0, k * 45, 0), origin=(8, 9.7, 8)) for k in range(4)]
         + [bx("Brand1", (4.5, 9.4, 7), (11, 10.6, 8.2), "burnbarrelinside", rot=(0, 30, 14)),
            bx("Brand2", (6, 9.4, 6), (7.2, 10.4, 11.5), "burnbarrelinside", rot=(-10, -20, 0))],
         box=(0.18, 0, 0.18, 0.82, 0.84, 0.82), oriented=False, material="Metal", sounds=METAL, light=[3, 7, 12],
         extra={"particleProperties": smoke + BURNBARREL_FIRE, "behaviors": [fire_fx.heat(7)]})
    # Hospital bed (B14): a steel bed on castors, a moulded head- and footboard (a recessed panel in a frame between
    # tube posts), a mattress in wipe-clean vinyl under a sheet, a cellular blanket turned down and hanging over the
    # sides, a pillow, a quilt folded at the foot, drop rails both sides at the head and the chart on the footboard.
    # Modelled head to the north across two blocks (head, foot), as before; its own texture keys (hospbed-*)
    hospital = hospital_bed_b14()
    prop("hospitalbed", "Hospital Bed", hospital, box=(0, 0, 0, 1, 0.85, 1), material="Cloth", sounds=CLOTH)
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
    prop("wetfloorsign", "Wet Floor Sign", L1.caution_sign(), box=(0.19, 0, 0.25, 0.81, 0.95, 0.75), material="Cloth", sounds=CLOTH)
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
    # (Where the run ends with open space beyond, "end-<side>" is capped on that side; "stub-<axis>" is a length on its own,
    # capped at both ends)
    for side, axis in (("north", "ns"), ("east", "we"), ("south", "ns"), ("west", "we")):
        drips[f"*-end-{side}"] = drips[f"*-{axis}"]
    block("drippipe", {
        "variantgroups": [{"code": "axis", "states": ["we", "ns", "end-north", "end-east", "end-south", "end-west", "stub-we", "stub-ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-end-east": {"base": "block/pipes-end", "rotateY": 0}, "*-end-north": {"base": "block/pipes-end", "rotateY": 90},
                        "*-end-west": {"base": "block/pipes-end", "rotateY": 180}, "*-end-south": {"base": "block/pipes-end", "rotateY": 270},
                        "*-stub-we": {"base": "block/pipes-stub", "rotateY": 0}, "*-stub-ns": {"base": "block/pipes-stub", "rotateY": 90},
                        "*-we": {"base": "block/pipes-run", "rotateY": 0}, "*-ns": {"base": "block/pipes-run", "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "collisionbox": {"x1": 0, "y1": 0.55, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0.55, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "lightAbsorption": 0, "resistance": 3, "sounds": METAL, "particlePropertiesByType": drips,
    }, "Overhead pipes with a leaking joint, dripping Almond Water onto the floor")
    name("drippipe-*", "Leaking Pipes")


# ======================= Level 3 =======================

def rivets(nm, x1, y1, x2, y2, z, inset=0.75, size=0.6, tex="steel"):
    """(B6) A screw or rivet head 0.25 proud in each corner of a plate whose front is at z: geometry, where the old
    signs painted them."""
    out = []
    for i, (x, y) in enumerate(((x1 + inset, y1 + inset), (x2 - inset - size, y1 + inset), (x1 + inset, y2 - inset - size),
                                (x2 - inset - size, y2 - inset - size))):
        out.append(bx(f"{nm}Rivet{i}", (x, y, z - 0.25), (x + size, y + size, z), tex, faces=("north", "east", "west", "up", "down")))
    return out


def cab_plate(nm, x1, y1, x2, y2, z, tex, t=0.25):
    return [bx(nm, (x1, y1, z - t), (x2, y2, z), tex, faces=("north", "east", "west", "up", "down"), uv=[0, 0, 16, 16])]


def wall_cables():
    """Three cables along a wall's north face, round in section, and a saddle clip over each at x 4 and 12."""
    out = []
    for i, (yc, r) in enumerate(((4.75, 0.8), (7.0, 1.0), (9.5, 0.65))):
        zc = -r - 0.05
        out += [bx(f"C{i}", (0, yc - r, zc - r * 0.6), (16, yc + r, zc + r * 0.6), "cable", faces=("north", "up", "down")),
                bx(f"C{i}b", (0, yc - r * 0.6, zc - r), (16, yc + r * 0.6, zc + r * 0.6), "cable", faces=("north", "up", "down"))]
        for j, x in enumerate((4, 12)):
            out.append(bx(f"Clip{i}{j}", (x - 0.5, yc - r - 0.3, zc - r - 0.25), (x + 0.5, yc + r + 0.3, 0), "metal",
                          faces=("north", "east", "west", "up", "down")))
    return out


def risers(y0, foot=False, strut=False):
    """Level 3's hot pipes up a wall: a lagged pipe and a bare one, round (gen_shapes.round_riser); with `foot` the
    flanged feet they stand in, with `strut` a channel strut across the wall and a clamp round each pipe."""
    out = round_riser("Hot", 6.0, -2.1, 2.0, "riserlag", y0) + round_riser("Rusty", 11.25, -1.5, 1.3, "riserrust", y0)
    if foot:
        out += round_riser("FootHot", 6.0, -2.1, 2.6, "flange", 0, 1, shaded=False, faces=("up",))
        out += round_riser("FootRusty", 11.25, -1.5, 1.9, "flange", 0, 1, shaded=False, faces=("up",))
    if strut:
        out.append(bx("Strut", (2.75, 9, -0.75), (14.25, 10.5, 0), "flange", faces=("north", "east", "west", "up", "down")))
        out += round_riser("ClampHot", 6.0, -2.1, 2.3, "flange", 9.1, 10.4, shaded=False, faces=("up", "down"))
        out += round_riser("ClampRusty", 11.25, -1.5, 1.6, "flange", 9.1, 10.4, shaded=False, faces=("up", "down"))
    return out


D4_BAY_PIPES = True  # (graphics pass D4) Level 5's boiler-bay pipes round; False: the old boxes with painted roundness


def bay_risers(y0, foot=False, strut=False):
    """(D4) Level 5's boiler bays: the bare and the lagged pipe up the plaster walls, round (gen_shapes.round_riser, in
    Level 3's riser skins, B6), where they stood (bare at x 2-5, lagged at 9-13); with `foot` the flanges they stand
    in, with `strut` a channel strut and a clamp round each, as Level 3's `risers`."""
    out = round_riser("Rusty", 3.5, -1.7, 1.5, "riserrust", y0) + round_riser("Lagged", 11.0, -2.2, 2.0, "riserlag", y0)
    if foot:
        out += round_riser("FootRusty", 3.5, -1.7, 2.1, "flange", 0, 1, shaded=False, faces=("up",))
        out += round_riser("FootLagged", 11.0, -2.2, 2.6, "flange", 0, 1, shaded=False, faces=("up",))
    if strut:
        out.append(bx("Strut", (1.25, 8, -0.75), (13.75, 9.5, 0), "flange", faces=("north", "east", "west", "up", "down")))
        out += round_riser("ClampRusty", 3.5, -1.7, 1.8, "flange", 8.1, 9.4, shaded=False, faces=("up", "down"))
        out += round_riser("ClampLagged", 11.0, -2.2, 2.3, "flange", 8.1, 9.4, shaded=False, faces=("up", "down"))
    return out


def cab_lamp(nm, cx, cy, z, tex, glow=0):
    """An indicator lamp on a front face at z: a bezel ring and a domed lens (as gen_shapes.cab_lamp)."""
    f = ("north", "east", "west", "up", "down")
    return [bx(nm + "Bezel", (cx - 0.75, cy - 0.75, z - 0.5), (cx + 0.75, cy + 0.75, z), "cabbezel", faces=f),
            bx(nm + "Lens", (cx - 0.5, cy - 0.5, z - 1.0), (cx + 0.5, cy + 0.5, z - 0.5), tex, glow=glow, faces=f, uv=[0, 0, 16, 16])]


def frame_front(nm, x1, y1, x2, y2, z, border, tex="switchgear"):
    """A raised frame round a recessed front panel at z (its front at z - 0.5)."""
    els, _ = K.frame_members(nm, x1, y1, x2, y2, z - 0.5, z, border, tex)
    for e in els:
        e["faces"].pop("south", None)
    return els


def switchgear():
    """(B6) Level 3's switchgear cabinet, two blocks tall, front to the north: a carcass on a toe-recessed plinth under
    a cap; the upper half an instrument panel in a frame, three meters as geometry (printed dials in octagonal bezels
    with needles), a row of indicator lamps (two lit), a selector switch and a plate; the lower half a door with a
    louvred vent, a bar handle, a lock and a warning decal. The old one painted all of that on its front."""
    f = ("north", "east", "west", "up", "down")
    els = [bx("Toe", (1.5, 0, 4.5), (14.5, 1, 15), "metaldark", faces=("north", "east", "west", "south")),
           bx("Body", (0.5, 1, 4), (15.5, 29.5, 15.5), "switchgear", faces=("east", "west", "south", "down")),
           bx("Panel", (0.5, 1, 4), (15.5, 29.5, 15.5), "switchgearpanel", faces=("north",)),
           bx("Cap", (0, 29.5, 3.5), (16, 30.5, 16), "switchgeartop")]
    els += frame_front("Upper", 0.5, 15.25, 15.5, 29.5, 4, 1.0) + frame_front("Lower", 0.5, 1, 15.5, 15.25, 4, 1.0)
    for i, (x, a) in enumerate(((4.0, -40), (8.0, 15), (12.0, 55))):
        els += K.dial(f"Meter{i}", x, 24.75, 4, r=2.25, angle=a, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += cab_lamp("LampA", 3.5, 20.25, 4, "cablampred", 120) + cab_lamp("LampB", 5.75, 20.25, 4, "lampgreen", 120)
    els += cab_lamp("LampC", 8.0, 20.25, 4, "cablampamber")
    els += K.knob("Selector", 11.75, 20.25, 4, r=1.0, depth=1.5, tex="cabbezel")
    els += [bx("SelectorBar", (10.9, 20.0, 1.95), (12.6, 20.5, 2.35), "metaldark", faces=f)]
    els += cab_plate("Plate", 3.0, 16.75, 13.0, 18.5, 4, "cablabel")
    els += louvre("Vent", 3.0, 9.0, 10.0, 13.5, 4, 5, tex="switchgear", back="fanwell")
    els += K.handle("Handle", 13.0, 8.0, 4, length=4.0, axis="y", standoff=0.75, thick=0.75, tex="cabbezel")
    els += cab_plate("Warn", 4.5, 3.5, 7.0, 6.0, 4, "warn3")
    els.append(bx("Lock", (12.5, 4.5, 3.0), (13.5, 5.5, 3.5), "cabbezel", faces=f))
    return els


def floor_fan():
    """(B6) A floor-standing industrial fan: a motor and hub on a post and a cross foot, four pitched blades, and a
    guard of round-cornered wire rings and a cross of bars before and behind (the old one painted its guards)."""
    els = [bx("Feet", (3, 0, 7), (13, 1, 9), "metaldark"), bx("FeetZ", (7, 0, 4.5), (9, 1, 11.5), "metaldark"),
           bx("Post", (7.3, 1, 7.3), (8.7, 6, 8.7), "metaldark"),
           bx("Motor", (6, 9, 8.5), (10, 13, 12.5), "metaldark"), bx("MotorCap", (6.5, 9.5, 12.5), (9.5, 12.5, 13.25), "metaldark")]
    els += K.bevelled_box("Hub", (7, 10, 6.25), (9, 12, 8.25), "metal", b=0.25)
    for nm, frm, to, rot in (("BladeUp", (7.25, 12, 6.9), (8.75, 16, 7.4), (0, 28, 0)), ("BladeDown", (7.25, 6, 6.9), (8.75, 10, 7.4), (0, -28, 0)),
                             ("BladeLeft", (3, 10.25, 6.9), (7, 11.75, 7.4), (-28, 0, 0)), ("BladeRight", (9, 10.25, 6.9), (13, 11.75, 7.4), (28, 0, 0))):
        els.append(K.box(nm, frm, to, "fanblade", rot=rot))
    for side, (z1, z2) in (("F", (5.5, 5.75)), ("B", (9.25, 9.5))):
        els += [bx(f"Rim{side}T", (2, 16.5, z1), (14, 17, z2), "metaldark"), bx(f"Rim{side}B", (2, 5, z1), (14, 5.5, z2), "metaldark"),
                bx(f"Rim{side}L", (2, 5.5, z1), (2.5, 16.5, z2), "metaldark"), bx(f"Rim{side}R", (13.5, 5.5, z1), (14, 16.5, z2), "metaldark"),
                bx(f"Bar{side}V", (7.75, 5.5, z1 + 0.05), (8.25, 16.5, z2 - 0.05), "metaldark"),
                bx(f"Bar{side}H", (2.5, 10.75, z1 + 0.05), (13.5, 11.25, z2 - 0.05), "metaldark")]
        for i, (a, b) in enumerate(((4.0, 12.0), (6.0, 10.0))):
            ya, yb = a + 3, b + 3
            els += [bx(f"Ring{side}{i}T", (a, yb - 0.5, z1 - 0.05), (b, yb, z2 + 0.05), "metaldark"),
                    bx(f"Ring{side}{i}B", (a, ya, z1 - 0.05), (b, ya + 0.5, z2 + 0.05), "metaldark"),
                    bx(f"Ring{side}{i}L", (a, ya + 0.5, z1 - 0.05), (a + 0.5, yb - 0.5, z2 + 0.05), "metaldark"),
                    bx(f"Ring{side}{i}R", (b - 0.5, ya + 0.5, z1 - 0.05), (b, yb - 0.5, z2 + 0.05), "metaldark")]
    els += [bx("Strut1", (2, 5, 5.75), (2.5, 5.5, 9.25), "metaldark"), bx("Strut2", (13.5, 16.5, 5.75), (14, 17, 9.25), "metaldark")]
    return els


def generator_panel():
    """(B6) The generator's control panel as geometry: a plate in a frame, two meters, a row of toggle switches and a
    red stop button (the old one was a painted picture)."""
    f = ("north", "east", "west", "up", "down")
    els = [bx("Panel", (4, 4, 1.5), (12, 10.5, 2), "generatorpanel", faces=f)]
    els += K.dial("MeterL", 6.0, 8.5, 1.5, r=1.4, angle=-30, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += K.dial("MeterR", 10.0, 8.5, 1.5, r=1.4, angle=40, face="cabdial", bezel="cabbezel", needle="cabneedle")
    for i, x in enumerate((5.25, 6.75, 8.25, 9.75)):
        els += [bx(f"SwitchBase{i}", (x - 0.5, 5.5, 1.25), (x + 0.5, 6.5, 1.5), "metaldark", faces=f),
                bx(f"Switch{i}", (x - 0.2, 5.9 if i % 3 else 5.3, 0.75), (x + 0.2, 6.7 if i % 3 else 6.1, 1.25), "steel", faces=f)]
    els += [bx("StopRing", (10.75, 4.75, 1.25), (11.75, 5.75, 1.5), "metaldark", faces=f),
            bx("Stop", (10.9, 4.9, 0.85), (11.6, 5.6, 1.25), "redmetal", faces=f)]
    return els


def control_desk():
    """(B6) An operator's desk: the body and a sloping panel as before, but its buttons, switches and lamps are boxes
    on the slope and its meters are dials on the backboard (the old ones were painted on)."""
    rot, org = (-20, 0, 0), (8, 11, 4)
    f = ("north", "east", "west", "up", "down")
    els = [bx("Body", (0, 0, 4), (16, 11, 16), "switchgear"),
           bx("Panel", (0, 11, 4), (16, 12, 14), "switchgearpanel", faces=("up",), rot=rot, origin=org),
           bx("PanelSides", (0, 11, 4), (16, 12, 14), "metaldark", faces=("north", "east", "west", "down"), rot=rot, origin=org),
           bx("Backboard", (0, 11, 14), (16, 22, 16), "switchgear", faces=("east", "west", "up", "south")),
           bx("BackPanel", (0, 11, 14), (16, 22, 16), "switchgearpanel", faces=("north",))]
    for i in range(8):  # a row of buttons
        x = 1.5 + i * 1.75
        els.append(bx(f"Button{i}", (x, 12, 5.0), (x + 1.0, 12.5, 6.0), "steel" if i % 3 else "metaldark", faces=f, rot=rot, origin=org))
    for i in range(5):  # toggles
        x = 2.5 + i * 2.75
        els.append(bx(f"Toggle{i}", (x, 12, 8.0), (x + 0.5, 13.0, 8.5), "steel", faces=f, rot=rot, origin=org))
    for i, (x, tex) in enumerate(((3, "cablampred"), (6.5, "lampgreen"), (10, "lampgreen"), (13, "cablampamber"))):
        els.append(bx(f"Lamp{i}", (x - 0.5, 12, 11.0), (x + 0.5, 12.5, 12.0), tex, glow=100 if tex == "lampgreen" else 0,
                      faces=f, rot=rot, origin=org, uv=[0, 0, 16, 16]))
    for i, (x, a) in enumerate(((2.75, -30), (6.25, 20), (9.75, -10), (13.25, 45))):
        els += K.dial(f"Meter{i}", x, 18.0, 14, r=1.5, angle=a, face="cabdial", bezel="cabbezel", needle="cabneedle")
    els += cab_plate("Plate", 4.0, 13.0, 12.0, 14.75, 14, "cablabel")
    return els


def coal_lumps():
    """Lumps of coal on and round the heap: small boxes of a few sizes, each turned a little about its upright."""
    import random as _r
    from detail_kit import seed_of
    rng = _r.Random(seed_of("coallumps"))
    out = []
    spots = [(rng.uniform(2, 14), 3, rng.uniform(2, 14)) for _ in range(9)] + [(rng.uniform(4, 12), 6, rng.uniform(4, 11)) for _ in range(5)]
    spots += [(rng.uniform(5.5, 9.5), 8, rng.uniform(5.5, 9.5)) for _ in range(2)] + [(x, 0, z) for x, z in ((0.5, 6), (15.2, 10), (9, 15.3))]
    for i, (x, y, z) in enumerate(spots):
        a = rng.uniform(0.6, 1.4)
        h = a * rng.uniform(0.6, 0.9)
        x, z = min(15.6 - a / 2, max(0.4 + a / 2, x)), min(15.6 - a / 2, max(0.4 + a / 2, z))
        out.append(bx(f"Lump{i}", (x - a / 2, y, z - a / 2), (x + a / 2, y + h, z + a / 2), "coal", rot=(0, rng.choice((-22.5, 22.5, 45)), 0),
                      origin=(x, y, z)))
    return out


def level3():
    cube_block("sanctumstone", "Ashlar Stone", ["plain"], {"plain": "sanctumwall"}, comment="Pale ashlar masonry of a Sanctum",
               randomizeAxes="xyz")  # (D4) the ashlar's versions picked by height too
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
    # (The gauges' length of pipe is on its own: blind flanges close both its ends.) (B6) The pipe is round, as the
    # wall pipes are, and the gauges are geometry: a bevelled case, a printed dial in an octagonal bezel, a needle and
    # hub, each on a stem from the pipe (the old ones were painted on plates)
    gauges = (round_pipe("Pipe", 3.5, -1.6, 1.5, "wallrust", 0.75, 15.25)
              + round_pipe("FlangeW", 3.5, -1.6, 2.2, "flange", 0.25, 0.75, shaded=False, faces=("east", "west"))
              + round_pipe("FlangeE", 3.5, -1.6, 2.2, "flange", 15.25, 15.75, shaded=False, faces=("east", "west"))
              + [bx("Stem1", (4.5, 4.9, -1.85), (5.25, 7.05, -1.1), "flange"), bx("Stem2", (10.9, 4.9, -1.85), (11.65, 7.65, -1.1), "flange")]
              + K.gauge("Gauge1", 4.875, 9.25, -0.4, r=2.2, angle=-50, face="cabdial", body="cabbezel", needle="cabneedle", depth=1.6, stem=False)
              + K.gauge("Gauge2", 11.275, 10.25, -0.4, r=2.6, angle=35, face="cabdial", body="cabbezel", needle="cabneedle", depth=1.6, stem=False))
    decors = [
        Decor("dangersign", "Danger Sign", {2: plate("Sign", (3, 3, -0.4), (13, 13, 0), "dangersign", "steel") + rivets("Sign", 3, 3, 13, 13, -0.4)}),
        Decor("gauges", "Pressure Gauges", {2: gauges}),
        Decor("knifeswitch", "Knife Switch", {2: knife_switch()}),
        # (B6) A cast box with a lid a size larger screwed on at the corners, the conduits in couplings
        Decor("junctionbox", "Junction Box", {
            2: [bx("Box", (4.25, 2.25, -2.5), (11.75, 10.75, 0), "l3paint", faces=("north", "east", "west", "up", "down")),
                bx("Lid", (4, 2, -3), (12, 11, -2.5), "l3paint", faces=("north", "east", "west", "up", "down"))]
            + rivets("Lid", 4, 2, 12, 11, -3, inset=0.6)
            + cab_plate("Label", 5.5, 8.25, 10.5, 9.75, -3, "cablabel")
            + [bx("CouplingL", (4.75, 10.75, -1.75), (6.75, 11.75, 0), "metal", faces=("north", "east", "west", "up", "down")),
               bx("CouplingR", (9.25, 10.75, -1.75), (11.25, 11.75, 0), "metal", faces=("north", "east", "west", "up", "down")),
               bx("ConduitL", (5, 11.75, -1.5), (6.5, 16, 0), "metal", faces=("north", "east", "west")),
               bx("ConduitR", (9.5, 11.75, -1.5), (11, 16, 0), "metal", faces=("north", "east", "west"))],
            3: [bx("ConduitL", (5, 0, -1.5), (6.5, 16, 0), "metal", faces=("north", "east", "west")),
                bx("ConduitR", (9.5, 0, -1.5), (11, 16, 0), "metal", faces=("north", "east", "west")),
                bx("StrapL", (4.5, 7.5, -1.75), (7, 8.5, 0), "metal", faces=("north", "east", "west", "up", "down")),
                bx("StrapR", (9, 7.5, -1.75), (11.5, 8.5, 0), "metal", faces=("north", "east", "west", "up", "down"))]}),
        Decor("sparkoutlet", "Sparking Outlet", {1: plate("Outlet", (5.5, 4, -0.5), (10.5, 10, 0), "outletburnt", "metaldark") +
                                                 [bx("Wire", (8, 0, -1), (8.6, 4, -0.4), "cable"), bx("Tip", (7.9, -0.3, -1.1), (8.7, 0.3, -0.3), "copper")]},
              particles=sparks),
        # A round-ish glass (two crossed boxes and a domed front) behind a heavy three-bar cage
        Decor("bulkhead", "Bulkhead Light", {2: [bx("Base", (4.5, 4, -1), (11.5, 11, 0), "metaldark"),
                                                 bx("GlassV", (6, 4.5, -3), (10, 10.5, -1), "bulkheadglass", glow=160, full=True),
                                                 bx("GlassH", (5, 5.5, -3), (11, 9.5, -1), "bulkheadglass", glow=160, full=True),
                                                 bx("Dome", (6.5, 6, -3.6), (9.5, 9, -3), "bulkheadglass", glow=160, full=True),
                                                 bx("CageL", (6.1, 4.2, -4.1), (6.9, 10.8, -1), "metaldark"),
                                                 bx("CageM", (7.6, 4.2, -4.1), (8.4, 10.8, -1), "metaldark"),
                                                 bx("CageR", (9.1, 4.2, -4.1), (9.9, 10.8, -1), "metaldark"),
                                                 bx("CageRing", (4.7, 7.1, -3.4), (11.3, 7.9, -1), "metaldark")]}, light=[6, 5, 9]),
        Decor("alarmbell", "Alarm Bell", {3: [bx("Plate", (6, 4, -0.6), (10, 11, 0), "metaldark")] + cyl("Bell", 8, -2.2, 3, 5, 10, "redmetal") +
                                          [bx("Striker", (7.5, 4, -2.5), (8.5, 5, -1.5), "metal")]}),
        # (The cables' ends are closed: where the run stops beside a fitting they end solid, not hollow)
        # (B6) Round cables (two crossed boxes each), held to the wall by saddle clips every half block
        Decor("wallcables", "Cable Run", {3: wall_cables() + [bx("Droop", (11, 1, -1.8), (12, 3.95, -0.8), "cable")]}),
        # (From a flanged foot on the floor up into the ceiling: a gallery's taller wall gets a fourth length)
        # (B6) Round, in the wall pipes' own skins: a lagged pipe and a bare one, standing in flanged feet, held by a
        # strut with a clamp round each half way up the room
        Decor("risers", "Hot Pipes", {1: risers(1, foot=True), 2: risers(0, strut=True), 3: risers(0), 4: risers(0)}),
        # Purpification (layout version 5): a dead thing, a hound by its build, half noclipped into the wall at the
        # floor, its head, shoulders and forelegs out, and it and the wall round it "completely purple" (Wikidot),
        # glowing faintly
        Decor("purpified", "Purpified Remains", {
            1: [bx("Stain", (0, 0, -0.06), (16, 16, 0), "purpwall-lower", glow=40, faces=("north",), full=True),
                bx("Ribs", (4.5, 2.5, -4), (11.5, 9, 0), "purpskin", glow=70),
                bx("Spine", (7, 9, -3), (9, 10.2, 0), "purpskin", glow=70),
                bx("Neck", (6.5, 3, -6.5), (9.5, 6.5, -4), "purpskin", glow=70),
                bx("Skull", (5.8, 0.5, -10), (10.2, 4.8, -6.5), "purpskin", glow=90),
                bx("Snout", (6.8, 0, -13.5), (9.2, 2.8, -10), "purpskin", glow=90),
                bx("EarL", (5.8, 4.8, -8), (6.8, 7, -7), "purpskin", glow=70), bx("EarR", (9.2, 4.8, -8), (10.2, 7, -7), "purpskin", glow=70),
                bx("LegL", (3.5, 0, -9), (5, 1.4, -2.5), "purpskin", glow=70), bx("PawL", (3, 0, -10.8), (5.4, 1, -9), "purpskin", glow=70),
                bx("LegR", (11, 2, -5), (12.5, 7.5, -3.5), "purpskin", glow=70),
                bx("ForeR", (11, 0, -8.5), (12.5, 2.5, -4), "purpskin", glow=70), bx("PawR", (10.6, 0, -10.2), (13, 1, -8.5), "purpskin", glow=70),
                # (B6) the growth: swellings on the ribs and skull, and pores that glow
                bx("LumpA", (5.5, 6.5, -4.6), (8, 8.6, -3.5), "purpskin", glow=80), bx("LumpB", (9, 3.5, -4.5), (11, 5.5, -3.6), "purpskin", glow=80),
                bx("LumpC", (7.2, 4.8, -9.2), (9.6, 5.6, -7.2), "purpskin", glow=95), bx("LumpD", (3.8, 1.4, -6.2), (5.2, 2.6, -4.2), "purpskin", glow=80),
                bx("Pore1", (6.4, 7.6, -4.85), (7.1, 8.3, -4.6), "purpglow", glow=200), bx("Pore2", (9.7, 4.4, -4.75), (10.3, 5.0, -4.5), "purpglow", glow=200),
                bx("Pore3", (8.0, 3.2, -10.25), (8.7, 3.9, -10.0), "purpglow", glow=220),
                bx("WallLump1", (1.5, 9.5, -0.6), (4, 12, 0), "purpskin", glow=60, faces=("north", "east", "west", "up", "down")),
                bx("WallLump2", (12, 10.5, -0.5), (14.5, 12.5, 0), "purpskin", glow=60, faces=("north", "east", "west", "up", "down"))],
            2: [bx("Stain", (0, 0, -0.06), (16, 16, 0), "purpwall-upper", glow=40, faces=("north",), full=True)]},
            light=[50, 6, 5]),
    ] + [Decor(f"roomsign{i}", "Room Sign", {2: plate("Sign", (3, 4, -0.3), (13, 13, 0), f"l3plaque{i}", "white") + rivets("Sign", 3, 4, 13, 13, -0.3)})
         for i in range(8)]
    for material in ("glazed", "brick", "cinder"):
        wall_family(f"l3deco{material}", "Level 3 Wall", {1: material}, decors)
    wall_family("l3decostone", "Ashlar Stone", {1: "sanctumwall"}, [d for d in decors if d.code == "bulkhead"])

    prop("coilunit", "Conductor Coil", [
        bx("Base", (2, 0, 2), (14, 3, 14), "metaldark")] + cyl("Coil", 8, 8, 4.5, 3, 14, "coil") + [
        bx("Cap", (3, 14, 3), (13, 15, 13), "insulator"), bx("Insulator", (7, 15, 7), (9, 20, 9), "insulator"),
        bx("Ring1", (6.5, 16, 6.5), (9.5, 16.8, 9.5), "insulator"), bx("Ring2", (6.5, 18, 6.5), (9.5, 18.8, 9.5), "insulator"),
        bx("Terminal", (7.5, 20, 7.5), (8.5, 22, 8.5), "copper")], box=(0.12, 0, 0.12, 0.88, 1.35, 0.88), oriented=False,
         material="Metal", sounds=METAL, extra={"sounds": dict(METAL, ambient="backrooms:ambient/transformer", ambientBlockCount=6)})
    prop("switchgear", "Switchgear Cabinet", switchgear(), box=(0.03, 0, 0.22, 0.97, 1.9, 0.97), material="Metal", sounds=METAL)
    prop("floorfan", "Industrial Fan", floor_fan(), box=(0.12, 0, 0.3, 0.88, 1.1, 0.85), material="Metal", sounds=METAL)
    prop("generator", "Generator", [
        bx("Skid", (0, 0, 1), (16, 2, 15), "metaldark"), bx("Body", (1, 2, 2), (15, 12, 14), "generator"),
        bx("Exhaust", (12, 12, 10), (14, 18, 12), "rust"), bx("Cap", (11.5, 18, 9.5), (14.5, 18.6, 12.5), "rust"),
        bx("Filler", (3, 12, 9), (5, 13.5, 11), "metaldark")] + generator_panel() +
        K.turn(louvre("Grille", 4.5, 4, 11.5, 10.5, 1.0, 4, tex="metaldark", back="fanwell"), 3),
         box=(0, 0, 0.06, 1, 0.85, 0.94), material="Metal", sounds=METAL,
         extra={"sounds": dict(METAL, ambient="backrooms:ambient/transformer", ambientBlockCount=4)})
    prop("cablespool", "Cable Spool", [
        bx("FlangeL1", (0, 1, 3), (1.5, 14, 13), "spoolwood"), bx("FlangeL2", (0, 3, 1), (1.5, 12, 15), "spoolwood"),
        bx("FlangeR1", (14.5, 1, 3), (16, 14, 13), "spoolwood"), bx("FlangeR2", (14.5, 3, 1), (16, 12, 15), "spoolwood"),
        bx("Drum", (1.5, 2, 3), (14.5, 13, 13), "cable")], box=(0, 0, 0.06, 1, 0.88, 0.94), oriented=False)
    prop("controldesk", "Control Desk", control_desk(),
         box=(0, 0, 0.25, 1, 1.35, 1), material="Metal", sounds=METAL)
    conveyor = [bx("SideL", (0, 6, 2), (16, 9, 3), "metaldark"), bx("SideR", (0, 6, 13), (16, 9, 14), "metaldark"),
                bx("Belt", (0, 8.2, 3), (16, 9, 13), "conveyorbelt"),
                bx("Leg1", (1, 0, 2.2), (2.5, 6, 3.5), "metaldark"), bx("Leg2", (1, 0, 12.5), (2.5, 6, 13.8), "metaldark"),
                bx("Leg3", (13.5, 0, 2.2), (15, 6, 3.5), "metaldark"), bx("Leg4", (13.5, 0, 12.5), (15, 6, 13.8), "metaldark"),
                bx("Brace", (1, 2, 3), (2.5, 3, 13), "metaldark"), bx("Brace2", (13.5, 2, 3), (15, 3, 13), "metaldark")]
    prop("conveyor", "Conveyor Belt", {"empty": conveyor, "box": conveyor + carton("Parcel", (4, 9, 4), (12, 15, 12))},
         box=(0, 0, 0.125, 1, 0.56, 0.875), material="Metal", sounds=METAL)
    # (B6) A stepped foot, a stem with two knops, arms that turn up into a drip pan under each candle, wax run down the
    # candles; the candles themselves are where they were (the flames are placed on their tops)
    prop("candelabra", "Candelabra", [
        bx("Foot", (5.25, 0, 5.25), (10.75, 0.75, 10.75), "brass"), bx("FootStep", (6.25, 0.75, 6.25), (9.75, 1.5, 9.75), "brass"),
        bx("Stem", (7.5, 1.5, 7.5), (8.5, 15, 8.5), "brass", faces=("north", "east", "south", "west")),
        bx("Knop1", (7, 4.5, 7), (9, 5.5, 9), "brass"), bx("Knop2", (7.1, 10, 7.1), (8.9, 10.75, 8.9), "brass"),
        bx("Arms", (3.5, 12.5, 7.6), (12.5, 13.25, 8.4), "brass"),
        bx("RiserL", (3.1, 12.5, 7.6), (3.9, 13.5, 8.4), "brass"), bx("RiserR", (12.1, 12.5, 7.6), (12.9, 13.5, 8.4), "brass"),
        bx("PanL", (2.25, 13.5, 6.75), (4.75, 14, 9.25), "brass"), bx("PanR", (11.25, 13.5, 6.75), (13.75, 14, 9.25), "brass"),
        bx("PanM", (6.75, 14.5, 6.75), (9.25, 15, 9.25), "brass"),
        bx("CandleL", (3, 14, 7.5), (4, 18, 8.5), "tubewarm", glow=180), bx("CandleM", (7.5, 15, 7.5), (8.5, 19, 8.5), "tubewarm", glow=180),
        bx("CandleR", (12, 14, 7.5), (13, 18, 8.5), "tubewarm", glow=180),
        bx("WaxL", (2.8, 14, 7.3), (3.4, 16.2, 7.6), "wax"), bx("WaxM", (8.1, 15, 7.3), (8.7, 16.6, 7.6), "wax"),
        bx("WaxR", (12.6, 14, 8.4), (13.2, 15.6, 8.7), "wax")],
         box=(0.3, 0, 0.3, 0.7, 1.1, 0.7), oriented=False, material="Metal", sounds=METAL, light=[6, 5, 10],
         extra={"particleProperties": CANDELABRA_FLAMES})
    # The Sanctum's angel: nearly three blocks tall on a darker pedestal, so it reads down the length of the nave: a
    # robed figure with its hands together, head a little bowed, great wings raised behind it in three tiers of
    # feathers, and a gilt halo glowing faintly ("a large statue of said deity ... elevated on a pedestal in an
    # altar-like fashion", Wikidot)
    wing = [bx("WingA", (-1, 20, 10.5), (4.5, 41, 12), "stonewing"), bx("WingB", (-4.5, 25, 11), (0, 45, 12.5), "stonewing"),
            bx("WingC", (-7, 30, 11.5), (-3.5, 46.5, 13), "stonewing"), bx("WingTip", (-8, 38, 12), (-6, 46, 13.2), "stonewing"),
            bx("WingLow", (-2, 13, 10.8), (3.5, 21, 11.8), "stonewing")]
    angel = [
        bx("Pedestal", (1, 0, 1), (15, 9, 15), "pedestal"), bx("Base", (0.5, 0, 0.5), (15.5, 1.5, 15.5), "pedestal"),
        bx("Cornice", (0.5, 9, 0.5), (15.5, 10.5, 15.5), "pedestal"),
        bx("Hem", (3.5, 10.5, 4), (12.5, 14, 12), "stonefold"), bx("Robe", (4, 14, 4.8), (12, 25, 11.2), "stonefold"),
        bx("Waist", (4.6, 25, 5.4), (11.4, 27, 10.6), "stone"), bx("Torso", (4.4, 27, 5.6), (11.6, 33, 10.4), "stone"),
        bx("Shoulders", (3.4, 31, 6), (12.6, 33.5, 10), "stone"),
        bx("ArmL", (3, 25.5, 6.2), (4.6, 32, 9.6), "stone"), bx("ArmR", (11.4, 25.5, 6.2), (13, 32, 9.6), "stone"),
        bx("ForearmL", (4, 25.5, 3.6), (7.8, 27.5, 6.4), "stone", rot=(0, -12, 0), origin=(4.5, 26.5, 6)),
        bx("ForearmR", (8.2, 25.5, 3.6), (12, 27.5, 6.4), "stone", rot=(0, 12, 0), origin=(11.5, 26.5, 6)),
        bx("Hands", (7, 26, 2.6), (9, 31, 4.4), "stone"),
        bx("Neck", (7, 33.5, 7.2), (9, 35, 9.2), "stone"),
        bx("Head", (6, 35, 6.2), (10, 39.5, 10.2), "stone", rot=(-6, 0, 0), origin=(8, 35, 8.2)),
        bx("Veil", (5.6, 35.5, 7.4), (10.4, 40.2, 10.8), "stonefold", rot=(-6, 0, 0), origin=(8, 35, 8.2)),
        bx("HaloTop", (5.5, 42.4, 11), (10.5, 43.2, 11.6), "gilt", glow=150), bx("HaloBottom", (5.5, 34.8, 11), (10.5, 35.6, 11.6), "gilt", glow=150),
        bx("HaloL", (4.2, 36, 11), (5, 42, 11.6), "gilt", glow=150), bx("HaloR", (11, 36, 11), (11.8, 42, 11.6), "gilt", glow=150)]
    angel += wing + mirror_x(wing)
    prop("angelstatue", "Statue", angel, box=(0.06, 0, 0.06, 0.94, 1.95, 0.94), material="Stone", sounds=STONE, light=[8, 2, 5])

    # A Sanctum's ceiling: a shallow vault cell in every block, ashlar ribs along its edges and across its
    # diagonals meeting at a boss, so the ceiling reads as vaulted stone over the nave and not as Level 3's plaster.
    # Hung from the block over the room; lit like the room (lightAbsorption 0)
    diag = 16 * 2 ** 0.5
    # (The cell rises from its ribs to its crown in two steps: the haunches low by the ribs, the crown highest)
    vault = [bx("Crown", (0, 15, 0), (16, 16, 16), "sanctumvault", faces=("down",))]
    for i, (lo, hi, y) in enumerate(((1, 4.5, 13.4), (4.5, 7, 14.3))):
        for j, (frm, to) in enumerate((((lo, y, lo), (16 - lo, 15, hi)), ((lo, y, 16 - hi), (16 - lo, 15, 16 - lo)),
                                       ((lo, y, hi), (hi, 15, 16 - hi)), ((16 - hi, y, hi), (16 - lo, 15, 16 - hi)))):
            vault.append(bx(f"Haunch{i}{j}", frm, to, "sanctumvault", faces=("down", "north", "south", "east", "west")))
    for i, (frm, to) in enumerate((((0, 12, 0), (16, 16, 1)), ((0, 12, 15), (16, 16, 16)), ((0, 12, 1), (1, 16, 15)), ((15, 12, 1), (16, 16, 15)))):
        vault.append(bx(f"Rib{i}", frm, to, "sanctumwall", faces=("down", "north", "south", "east", "west")))
    for i, a in enumerate((45, -45)):
        vault.append(bx(f"Diag{i}", (8 - diag / 2, 13, 7.4), (8 + diag / 2, 14.4, 8.6), "sanctumwall", faces=("down", "north", "south"),
                        rot=(0, a, 0), origin=(8, 13, 8)))
    boss = vault + [bx("Boss", (6.5, 12.2, 6.5), (9.5, 13.2, 9.5), "gilt"), bx("BossRing", (5.8, 12.8, 5.8), (10.2, 13.2, 10.2), "sanctumwall")]
    block("sanctumceiling", {
        "variantgroups": [{"code": "kind", "states": ["vault", "boss"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {"*-vault": {"base": shape("sanctumceiling-vault", vault)}, "*-boss": {"base": shape("sanctumceiling-boss", boss)}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 4, "sounds": STONE},
        "The vaulted stone ceiling of a Sanctum")
    name("sanctumceiling-*", "Vaulted Ceiling")
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
        bx("Dangle", (12, 2, 10), (12.8, 11.5, 10.8), "cable"), bx("Tip", (12, 1.4, 10), (12.8, 2, 10.8), "copper")],
        # Level 4: in the gap of a missing ceiling tile (the block above the room), the tray up in the dark with a few
        # thin cables on it, and only a loop and one loose end hanging down out of the gap
        "gap": [bx("Tray", (0, 13.5, 4), (16, 14, 12), "metal", faces=("north", "south", "up", "down"))] +
        [bx(f"Cable{i}", (0, 14, z), (16, 14 + r, z + r), "cable", faces=("north", "south", "up", "down"))
         for i, (z, r) in enumerate(((4.8, 1), (6.6, 0.8), (8.4, 1.2), (10.4, 0.8)))] + [
        bx("Hanger", (7.5, 14, 3.5), (8.5, 16, 4), "metal"), bx("Hanger2", (7.5, 14, 12), (8.5, 16, 12.5), "metal"),
        bx("LoopL", (3, -4, 3.4), (3.5, 14.5, 3.9), "cable"), bx("LoopB", (3, -4.5, 3.4), (10, -4, 3.9), "cable"),
        bx("LoopR", (9.5, -4, 3.4), (10, 14.5, 3.9), "cable"),
        bx("Dangle", (12, -7.5, 12.1), (12.5, 14.5, 12.6), "cable"), bx("Tip", (11.95, -8.1, 12.05), (12.55, -7.5, 12.65), "copper")]},
         box=(0, 0.7, 0, 1, 1, 1), material="Metal", sounds=METAL)


# ======================= Level 4 =======================

def shape_tree(nm, elements):
    """(B7) detail_kit.shape for a model whose elements have children: the textures table takes the children's keys too."""
    keys = set()

    def walk(els):
        for e in els:
            keys.update(f["texture"][1:] for f in e["faces"].values())
            walk(e.get("children", []))
    walk(elements)
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in sorted(keys)}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", "block", "detail", nm + ".json"), data)
    return "block/detail/" + nm


def diffuser():
    """(B7) A square ceiling diffuser under a plain office tile: a white enamel face plate a little proud of the tile,
    its concentric air slots in crisp pixels on its face (the slots are openings, not relief), and the centre cone
    standing a step lower. Round 1 stepped three cones down in geometry with a smooth texture: at a distance they
    smeared, and their sides, lit by the ceiling blocks round them, made the rings look broken."""
    plate = K.box("Plate", (1, -0.5, 1), (15, 0, 15), {"bottom": "diffuser-face", "side": "diffuser"},
                  faces=("down", "north", "south", "east", "west"))
    plate["faces"]["down"]["uv"] = [0, 0, 16, 16]  # the face is one picture of the whole plate
    return [cube("officeceiling-vent"), plate,
            K.box("Cone", (6, -1.0, 6), (10, -0.5, 10), "diffuser", faces=("down", "north", "south", "east", "west"))]


def sprinkler():
    """(B7) A pendant sprinkler head in the middle of one of the block's two tiles: a chrome escutcheon cup, the body,
    the two arms of its frame down to the deflector, and the red glass bulb between them. The old one was a painted
    dot."""
    cx, cz = 8, 12
    els = [cube("officeceiling-sprinkler"),
           K.box("Cup", (cx - 1.25, -0.5, cz - 1.25), (cx + 1.25, 0, cz + 1.25), "sprinklerchrome", faces=("down", "north", "south", "east", "west")),
           K.box("Body", (cx - 0.75, -1.0, cz - 0.5), (cx + 0.75, -0.5, cz + 0.5), "sprinklerchrome", faces=("down", "north", "south", "east", "west")),
           K.box("ArmW", (cx - 1.25, -2.0, cz - 0.25), (cx - 0.75, -1.0, cz + 0.25), "sprinklerchrome", faces=("north", "south", "east", "west")),
           K.box("ArmE", (cx + 0.75, -2.0, cz - 0.25), (cx + 1.25, -1.0, cz + 0.25), "sprinklerchrome", faces=("north", "south", "east", "west")),
           K.box("Bulb", (cx - 0.25, -1.75, cz - 0.25), (cx + 0.25, -1.0, cz + 0.25), "sprinklerbulb", faces=("north", "south", "east", "west")),
           K.box("Deflector", (cx - 1.0, -2.5, cz - 1.0), (cx + 1.0, -2.0, cz + 1.0), "sprinklerchrome")]
    return els


def ceiling_alt():
    """(B7) The office ceiling's odd blocks. The diffuser and the sprinkler are models now (`drawtypeByType`: json),
    the water-stained tile a cube in two versions; codes and kinds as they were."""
    paths = {"vent": shape("officeceilingalt-vent", diffuser()), "sprinkler": shape("officeceilingalt-sprinkler", sprinkler())}
    block("officeceilingalt", {
        "variantgroups": [{"code": "kind", "states": ["vent", "sprinkler", "stain"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Ceramic", "drawtypeByType": {"*-stain": "cube", "*": "json"},
        "shapeByType": {f"*-{k}": {"base": p} for k, p in paths.items()},
        "texturesByType": {"*-stain": {"all": {"base": "block/detail/officeceiling-stain",
                                               "alternates": [{"base": "block/detail/officeceiling-stain-2"}]}}},
        "lightAbsorption": 99, "resistance": 1, "sounds": GLASS, "drops": CEILING_DROPS,
    }, "Drop-ceiling tiles with air diffusers, sprinkler heads and water stains")
    for k, english in (("vent", "Air Diffuser"), ("sprinkler", "Ceiling Tile"), ("stain", "Stained Ceiling Tile")):
        name(f"officeceilingalt-{k}", english)


def extinguisher_cabinet():
    """(B7) The fire extinguisher cabinet as geometry (the old one was a picture of one on a plate, and read as a red
    painting): a white enamel tub on the wall with its pale back, a bead round its open front, and in it a red
    extinguisher (octagonal, its label band), the black valve and lever, and the hose down its side to the nozzle."""
    els = [bx("Back", (4.75, 1.75, -0.5), (11.25, 13.25, 0), "extcabinet", faces=("north",)),
           bx("TubL", (4, 1, -2.5), (4.75, 14, 0), "extsteel", faces=("north", "east", "west", "up", "down")),
           bx("TubR", (11.25, 1, -2.5), (12, 14, 0), "extsteel", faces=("north", "east", "west", "up", "down")),
           bx("TubT", (4.75, 13.25, -2.5), (11.25, 14, 0), "extsteel", faces=("north", "up", "down")),
           bx("TubB", (4.75, 1, -2.5), (11.25, 1.75, 0), "extsteel", faces=("north", "up", "down")),
           bx("BeadT", (3.75, 13.75, -3), (12.25, 14.25, -2.5), "steel"), bx("BeadB", (3.75, 0.75, -3), (12.25, 1.25, -2.5), "steel"),
           bx("BeadL", (3.75, 1.25, -3), (4.25, 13.75, -2.5), "steel", faces=("north", "east", "west")),
           bx("BeadR", (11.75, 1.25, -3), (12.25, 13.75, -2.5), "steel", faces=("north", "east", "west"))]
    els += octagon("Ext", 8, -1.4, 1.4, 1.75, 10, "extred", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += octagon("ExtNeck", 8, -1.4, 0.75, 10, 10.75, "metaldark", faces=("north", "east", "south", "west", "up"), lift=0.01)
    els += [bx("Valve", (7.5, 10.75, -1.9), (8.5, 12, -0.9), "metaldark"),
            bx("Lever", (7, 12, -1.65), (9.75, 12.5, -1.15), "metaldark"),
            bx("Hose", (9.5, 5, -2.0), (10, 11, -1.5), "rubber"),
            bx("HoseTop", (8.5, 11, -2.0), (10, 11.5, -1.5), "rubber"),
            bx("Nozzle", (9.4, 4.25, -2.1), (10.1, 5, -1.4), "metaldark")]
    return els


def framed(nm, x1, y1, x2, y2, z, tex="metaldark", w=0.5, proud=0.5):
    """(B7) A frame of four strips `w` wide standing `proud` off a face at z, round (x1, y1)-(x2, y2)."""
    return [bx(nm + "T", (x1, y2 - w, z - proud), (x2, y2, z), tex, faces=("north", "up", "down", "east", "west")),
            bx(nm + "B", (x1, y1, z - proud), (x2, y1 + w, z), tex, faces=("north", "up", "down", "east", "west")),
            bx(nm + "L", (x1, y1 + w, z - proud), (x1 + w, y2 - w, z), tex, faces=("north", "east", "west")),
            bx(nm + "R", (x2 - w, y1 + w, z - proud), (x2, y2 - w, z), tex, faces=("north", "east", "west"))]


def level4():
    ceiling_alt()
    shape("officeglass", L4.glass_partition())  # (Level 4 art) the partition glass, inset from the floor and ceiling (blocktype: gen_blocktypes)
    # (Level 4 art) The blacked-out window is a model (a framed pane painted black, recessed, taped), the blinds stay a cube
    # (a light: its glow needs the cube) in four versions: down, half drawn up (two), slats tilted open. Codes and kinds as
    # they were; the rain picture on the clear window (officewindow, a cube too) is gone, see gen_textures.office_window.
    blackout = shape("officewindowalt-blackout", L4.blackout_window())
    block("officewindowalt", {
        "variantgroups": [{"code": "kind", "states": ["blackout", "blinds"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Glass", "drawtypeByType": {"*-blackout": "json", "*": "cube"},
        "shapeByType": {"*-blackout": {"base": blackout}},
        "texturesByType": {"*-blinds": {"all": {"base": "block/detail/officewindow-blinds", "alternates": [
            {"base": f"block/detail/officewindow-blinds-{k}"} for k in (2, 3, 4)]}}},
        "sideopaqueByType": {"*-blackout": {"all": False}}, "randomizeAxes": "xyz",
        "lightAbsorptionByType": {"*-blinds": 0, "*": 99}, "lightHsvByType": {"*-blinds": [36, 1, 4]},
        "resistance": 4, "sounds": GLASS, "drops": [],
    }, "Windows papered over or shut behind blinds. Most of Level 4's windows are")
    name("officewindowalt-blackout", "Blacked-Out Window")
    name("officewindowalt-blinds", "Window with Blinds")
    cube_block("officecarpetalt", {"papers": "Office Carpet", "stain": "Stained Office Carpet"}, ["papers", "stain"],
               {"papers": "officecarpet-papers", "stain": "officecarpet-stain"}, material="Cloth", sounds=CLOTH)
    cube_block("drywallbase", "Office Wall", ["plain"], {"plain": "drywall-base"}, comment="Office drywall with a dark vinyl skirting")

    decors = [
        # (Level 4 art) the fountain at a real height (rim 0.89 m, bubbler 0.975 m) and the clock as geometry
        Decor("fountain", "Drinking Fountain", {1: L4.fountain()}, cls=("BackroomsDispenser", "BackroomsDispenser")),
        Decor("clock", "Wall Clock", {3: L4.wall_clock()}),
        # (B7) the board in an aluminium frame (geometry), on a tray with a marker
        Decor("whiteboard", "Whiteboard", {2: plate("Board", (0, 1, -0.8), (16, 14, 0), "whiteboard", "steel") +
                                           framed("Frame", 0, 1, 16, 14, -0.8, "alu") +
                                           [bx("Tray", (1, 0.25, -2.25), (15, 1, -0.8), "alu"), bx("Marker", (3, 1, -1.8), (6, 1.6, -1.35), "redmetal")]}),
        Decor("corkboard", "Corkboard", {2: plate("Board", (2, 2, -0.8), (14, 13, 0), "corkboard", "wood")}),
        Decor("evacmap", "Evacuation Map", {2: plate("Map", (4, 3, -0.6), (12, 13, 0), "evacmap", "metaldark")}),
        Decor("extinguisher", "Fire Extinguisher Cabinet", {2: extinguisher_cabinet()}),
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
    ] + [Decor(f"poster{i}", "Framed Poster", {2: plate("Poster", (2, 1, -0.8), (14, 15, 0), f"poster{i}", "metaldark") +
                                                framed("Frame", 2, 1, 14, 15, -0.8)}) for i in range(3)]
    # (B7) each poster with two more prints, so a corridor of them is not the same three pictures (the layout still
    # places three kinds; the block picks a print for each)
    prints = {f"poster{i}": {"base": f"block/detail/poster{i}",
                             "alternates": [{"base": f"block/detail/poster{i}-{k}"} for k in (2, 3)]} for i in range(3)}
    wall_family("officedeco", "Office Wall", {1: "drywall-base", 2: "drywall"}, decors, textures=prints)

    # (B7) the swivel chair from gen_shapes, on its side (the whole chair turned as one: a parent element with the
    # chair's parts as its children, so the turned base arms keep their own turn)
    tipped = [{"name": "Tipped", "from": [0, 0, 0], "to": [0, 0, 0], "rotationOrigin": [8, 6, 8], "rotationZ": 90,
               "faces": {}, "children": office_chair()}]
    prop("officechairtipped", "Office Chair", [], box=(0.1, 0, 0.1, 0.9, 0.85, 0.9), material="Cloth", sounds=CLOTH)
    shape_tree("officechairtipped", tipped)  # prop() wrote an empty model under the same name: write the real one over it
    prop("ficus", "Dead Ficus", L4.ficus(), box=(0.3, 0, 0.3, 0.7, 1.8, 0.7), oriented=False, material="Plant", sounds=CLOTH)
    prop("chairstack", "Stacked Chairs", L4.chair_stack(), box=(0.18, 0, 0.18, 0.82, 1.5, 0.82), oriented=False)
    # (B7) the copier: drawers as inset fronts with grips, the control panel's buttons and the paper output as geometry
    copier = K.bevelled_box("Body", (1, 0.5, 3), (15, 13, 15), "copier", b=0.5)
    copier += [bx("Plinth", (1.5, 0, 3.5), (14.5, 0.5, 14.5), "metaldark", faces=("north", "south", "east", "west")),
               bx("Lid", (1, 13, 3.5), (15, 14, 15), "metaldark"),
               bx("Panel", (1.5, 13, 2.5), (8, 14.5, 6), "copierpanel", faces=("up", "north", "east", "west")),
               bx("Tray", (15, 8, 6), (17, 8.5, 12), "copier"), bx("Paper", (15.2, 8.5, 6.5), (16.8, 9, 11.5), "paper")]
    for i, (y1, y2) in enumerate(((1, 5), (5.5, 9.5))):
        copier += K.bevelled_box(f"Drawer{i}", (2, y1, 2.25), (14, y2, 3), "copier", b=0.25)
        copier += K.handle(f"Grip{i}", 8, y2 - 1, 2.25, length=4, axis="x", standoff=0.5, thick=0.5, tex="metaldark")
    for r in range(2):
        for c in range(3):
            copier.append(bx(f"Button{r}{c}", (5 + c * 0.9, 14.5, 3 + r * 1.25), (5.5 + c * 0.9, 15, 3.5 + r * 1.25), "crt",
                             faces=("up", "north", "east", "west", "south")))
    prop("copier", "Photocopier", copier, box=(0.06, 0, 0.18, 0.94, 0.95, 0.94), material="Metal", sounds=METAL)
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
    # (B7) the counter's two doors are inset panels with bar pulls (they were a picture of doors), on a recessed kick
    counter = [bx("Cabinet", (0, 1, 4.5), (16, 13, 16), "white", faces=("north", "east", "west", "south")),
               bx("Kick", (0, 0, 5), (16, 1, 16), "rubber"),
               bx("Top", (0, 13, 3.5), (16, 14.5, 16), "countertop"), bx("Splash", (0, 14.5, 15), (16, 18, 16), "countertop")]
    for i, (x1, x2) in enumerate(((0.25, 7.875), (8.125, 15.75))):
        counter += K.bevelled_box(f"Door{i}", (x1, 1.25, 3.75), (x2, 12.75, 4.5), "cabinetwhite", b=0.25)
    counter += K.handle("PullL", 7, 10.5, 3.75, length=2.5, axis="y", standoff=0.5, thick=0.5, tex="steel")
    counter += K.handle("PullR", 9, 10.5, 3.75, length=2.5, axis="y", standoff=0.5, thick=0.5, tex="steel")
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
    # (B7) the break room's round table is round (an octagon), its laminate top edged, on a column and a cross foot
    table = octagon("TopEdge", 8, 8, 6.75, 12, 13, "lamedge", faces=("north", "east", "south", "west", "down"), lift=0.01)
    table += octagon("Top", 8, 8, 6.75, 12.95, 13, "lamfleck", faces=("up",), lift=0.01)
    table += [bx("Post", (7.25, 1, 7.25), (8.75, 12, 8.75), "metaldark", faces=("north", "south", "east", "west")),
              bx("FootX", (3, 0, 7.25), (13, 1, 8.75), "metaldark"),
              bx("FootZ", (7.25, 0, 3), (8.75, 0.99, 13), "metaldark", faces=("north", "south", "east", "west", "up"))]
    prop("roundtable", "Break Room Table", table, box=(0.06, 0, 0.06, 0.94, 0.82, 0.94), oriented=False)
    prop("receptiondesk", "Reception Desk", L4.reception_desk(), box=(0, 0, 0.06, 1, 1.15, 1))
    # (B7) the wastebasket is open: four mesh walls round a floor, paper balls in it and one on top
    prop("wastebasket", "Wastebasket", [
        bx("WallN", (5, 0, 5), (11, 6, 5.5), "wastebin"), bx("WallS", (5, 0, 10.5), (11, 6, 11), "wastebin"),
        bx("WallW", (5, 0, 5.5), (5.5, 6, 10.5), "wastebin"), bx("WallE", (10.5, 0, 5.5), (11, 6, 10.5), "wastebin"),
        bx("Floor", (5.5, 0, 5.5), (10.5, 0.5, 10.5), "wastebin", faces=("up",)),
        bx("Ball1", (6, 0.5, 6), (8, 2.5, 8), "paper"), bx("Ball2", (7.5, 0.5, 7.75), (9.75, 2.25, 10), "paper"),
        bx("Ball", (6.5, 5, 7), (8.5, 7, 9), "paper")],
         oriented=False, collide=False, extra={"selectionbox": {"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 0.4, "z2": 0.7}})
    prop("coatstand", "Coat Stand", L4.coat_stand(), box=(0.3, 0, 0.3, 0.7, 1.8, 0.7), oriented=False)
    prop("bench", "Bench", [bx("Seat", (0, 6, 5), (16, 7.5, 11), "benchwood"),
                            bx("LegL", (1, 0, 5.5), (2.5, 6, 10.5), "metaldark"), bx("LegR", (13.5, 0, 5.5), (15, 6, 10.5), "metaldark")],
         box=(0, 0, 0.3, 1, 0.47, 0.7))


# ======================= Level 5 =======================

def long_sofa():
    """The hotel's velvet sofa as long as a real one, two blocks (layout version 6; the one-block "sofa" stays for older
    worlds): a three-seat Chesterfield-ish sofa on turned mahogany feet, rolled arms, two seat and two back cushions.
    Facing north (its seat to the north), parts l and r (left and right as you sit on it)."""
    els = [bx(f"Foot{k}", (x, 0, z), (x + 1.6, 2, z + 1.6), "mahogany") for k, (x, z) in
           enumerate(((2, 4), (28.4, 4), (2, 12.4), (28.4, 12.4)))]
    els += [bx("Skirt", (1, 2, 3.5), (31, 5.5, 14.5), "velvet"),
            bx("Back", (1, 5.5, 12.4), (31, 13.5, 14.8), "velvet"), bx("BackRoll", (0.8, 13.2, 12.2), (31.2, 14.6, 15), "velvet"),
            bx("ArmL", (1, 5.5, 3.5), (3.6, 10, 12.4), "velvet"), bx("ArmR", (28.4, 5.5, 3.5), (31, 10, 12.4), "velvet"),
            bx("ArmRollL", (0.4, 9.2, 3), (4, 11.4, 12.6), "velvet"), bx("ArmRollR", (28, 9.2, 3), (31.6, 11.4, 12.6), "velvet"),
            bx("SeatL", (3.6, 5.5, 3.2), (15.9, 8, 12.4), "velvet"), bx("SeatR", (16.1, 5.5, 3.2), (28.4, 8, 12.4), "velvet"),
            bx("CushionL", (4, 8, 10.4), (15.8, 13, 12.4), "velvet"), bx("CushionR", (16.2, 8, 10.4), (28, 13, 12.4), "velvet"),
            bx("Button", (15.6, 9.5, 12.3), (16.4, 10.3, 12.5), "brass")]
    multiblock_prop("longsofa", "Sofa", els, 2, 1, ("l", "r"), {
        "l": (0.04, 0, 0.18, 1, 0.55, 0.94), "r": (0, 0, 0.18, 0.96, 0.55, 0.94)}, material="Cloth", sounds=CLOTH,
        comment="The hotel's velvet sofa, two blocks long, its seat to the north (l, r: left and right as you sit on it)")



# ======================= Graphics pass B10: the furniture of Fort Surrender =======================
#
# Level 7's shelters (and its entry rooms) are furnished from Level 5: the side chair, the bookshelf and the coffee
# table, held together with tar. They are re-made here as geometry and keep their codes, footprints and boxes, so
# Level 5's rooms get them too. (The wardrobe and the wing chair are in gen_shapes, wardrobe_b10 and wing_chair_b10.)

def _book(name, x1, x2, y1, h, z1, z2, col, rot=None, origin=None):
    """One book standing on a shelf, its spine to the north: the spine and boards from column `col` of the
    hotelbookspines atlas (two rows of eight colours, a spine 6 units tall in each row), the top the page block."""
    u = (col % 8) * 2
    v = 0 if col < 8 else 8
    cover = {"texture": "#hotelbookspines", "uv": [u, v, u + 2, v + 6]}
    faces = {"north": dict(cover), "east": dict(cover), "west": dict(cover),
             "up": {"texture": "#hotelbookpages", "uv": [0, 0, round(x2 - x1, 4), round(z2 - z1, 4)]}}
    el = {"name": name, "from": [round(x1, 4), round(y1, 4), round(z1, 4)], "to": [round(x2, 4), round(y1 + h, 4), round(z2, 4)],
          "faces": faces}
    if rot:
        el["rotationOrigin"] = [round(v, 4) for v in origin]
        el["rotationZ"] = rot
    return el


def shelf_books(seed, y, x1=1.0, x2=15.0, z1=9.25, z2=15.25, top=6.5):
    """A row of books on a shelf at height y: widths and heights of their own, a gap now and then with the last book
    before it leaning into it, and a short stack lying flat in one row in three."""
    rng = random.Random(seed)
    out = []
    x = x1 + rng.uniform(0, 0.5)
    k = 0
    flat_at = rng.uniform(x1 + 3, x2 - 5) if rng.random() < 0.4 else None
    while x < x2 - 0.75:
        if flat_at is not None and x >= flat_at:
            for j in range(rng.randint(2, 3)):  # a few lying flat, one on another
                wdt = rng.uniform(3.2, 4.2)
                out.append(_book(f"Flat{seed}_{j}", x, min(x2, x + wdt), y + j * 0.9, 0.9, z1 + 0.5, z2 - 0.25 - j * 0.3,
                                 rng.randrange(16)))
            x += 4.4
            flat_at = None
            continue
        w = rng.choice((0.75, 1.0, 1.0, 1.25, 1.5))
        if x + w > x2:
            break
        h = rng.uniform(4.6, top - 0.2)
        gap = rng.random() < 0.12 and x + w + 3.4 < x2
        if gap:
            # the book before a gap leans over into it, resting on its neighbour
            out.append(_book(f"Book{seed}_{k}", x + 0.6, x + 0.6 + w, y, min(h, top - 1.2), z1 + rng.uniform(0, 0.6), z2,
                             rng.randrange(16), rot=-22.5, origin=(x + 0.6 + w, y, 12)))
            x += w + 3.0
        else:
            out.append(_book(f"Book{seed}_{k}", x, x + w, y, h, z1 + rng.uniform(0, 0.75), z2, rng.randrange(16)))
            x += w
        k += 1
    return out


def hotel_bookshelf_b10():
    """The hotel's open bookcase: mahogany sides, back and crown, four shelves with a lip, and the books as geometry, each
    its own colour, height and depth, a gap here and there with a book leaning into it (was a painted picture of books
    on each shelf)."""
    m = "mahogany"
    els = [bx("SideL", (0, 0, 8), (1, 30, 16), m), bx("SideR", (15, 0, 8), (16, 30, 16), m),
           bx("Back", (1, 0, 15.5), (15, 30, 16), m, faces=("north", "south")),
           bx("Crown", (-0.5, 30, 7.5), (16.5, 31, 16), m), bx("CrownTop", (0, 31, 8), (16, 31.5, 16), m, faces=("north", "east", "west", "up")),
           bx("Plinth", (1, 0, 8), (15, 1, 15.5), m)]
    for i, y in enumerate((7.5, 15, 22.5)):
        els += [bx(f"Shelf{i}", (1, y, 8.5), (15, y + 0.75, 15.5), m), bx(f"Lip{i}", (1, y, 8), (15, y + 1, 8.5), m)]
    for i, y in enumerate((1, 8.5, 16, 23.5)):
        els += shelf_books(1460 + i, y, top=6.5 if i < 3 else 6.5)
    return els


def hotel_chair_b10():
    """The hotel's side chair: mahogany legs tapering to the floor, seat rails, a padded red velvet seat with a soft edge,
    and a back of two stiles (the back legs carried up), a shaped crest rail and an upholstered panel in a frame."""
    m, v = "mahogany", "velvet"
    els = []
    for i, (x, z) in enumerate(((3.5, 3.5), (11.25, 3.5))):
        els += [bx(f"LegF{i}", (x, 2.5, z), (x + 1.25, 6.5, z + 1.25), m),
                bx(f"FootF{i}", (x + 0.15, 0, z + 0.15), (x + 1.1, 2.5, z + 1.1), m)]
    for i, x in enumerate((3.5, 11.25)):
        els += [bx(f"LegB{i}", (x, 0, 11.5), (x + 1.25, 21, 12.75), m)]
    els += [bx("RailF", (4.75, 5.25, 3.6), (11.25, 6.75, 4.6), m), bx("RailB", (4.75, 5.25, 11.6), (11.25, 6.75, 12.6), m),
            bx("RailL", (3.6, 5.25, 4.75), (4.6, 6.75, 11.5), m), bx("RailR", (11.4, 5.25, 4.75), (12.4, 6.75, 11.5), m)]
    els += K.bevelled_box("Seat", (3.25, 6.75, 3.25), (12.75, 8.5, 12.25), v, b=0.5)
    els += [bx("Crest", (4.75, 19, 11.6), (11.25, 20.5, 12.6), m), bx("CrestTop", (6, 20.5, 11.6), (10, 21.25, 12.6), m,
                                                                   faces=("north", "south", "east", "west", "up")),
            bx("BackRail", (4.75, 10.5, 11.75), (11.25, 11.5, 12.5), m),
            bx("BackPad", (5.25, 11.5, 11.4), (10.75, 18.5, 12.4), v)]
    return els


def coffee_table_b10():
    """The low mahogany table: a top with a moulded edge round its marble inlay, an apron, and four square legs tapering
    to the floor (the ashtray stays)."""
    m = "mahogany"
    els = K.bevelled_box("Top", (1, 7, 3), (15, 8, 13), m, b=0.25)
    els += [bx("Inlay", (3, 8, 5), (13, 8.05, 11), "marbletop", faces=("up",)),
            bx("ApronN", (2.5, 5.5, 4), (13.5, 7, 4.75), m), bx("ApronS", (2.5, 5.5, 11.25), (13.5, 7, 12), m),
            bx("ApronW", (2.5, 5.5, 4.75), (3.25, 7, 11.25), m), bx("ApronE", (12.75, 5.5, 4.75), (13.5, 7, 11.25), m),
            bx("Ashtray", (9, 8, 6), (11, 8.6, 8), "crystal")]
    for i, (x, z) in enumerate(((2, 3.5), (12.75, 3.5), (2, 11.25), (12.75, 11.25))):
        els += [bx(f"Leg{i}", (x, 3, z), (x + 1.25, 7, z + 1.25), m),
                bx(f"Foot{i}", (x + 0.2, 0, z + 0.2), (x + 1.05, 3, z + 1.05), m)]
    return els


def level5():
    long_sofa()
    cube_block("hotelfloor", {"marble": "Marble Floor", "runnerns": "Carpet Runner", "runnerwe": "Carpet Runner", "rug": "Rug"},
               ["marble", "runnerns", "runnerwe", "rug"], {"marble": "marble", "runnerns": "runner-ns", "runnerwe": "runner-we", "rug": "rug"},
               material="Stone", sounds=STONE, comment="Hotel floors: white marble, runners over walnut, and Persian rugs")
    # (The gauges' length of pipe is on its own: blind flanges close both its ends)
    gauges = [bx("Pipe", (0.6, 2, -3), (15.4, 5, 0), "rust", faces=("north", "up", "down")),
              bx("FlangeW", (0, 1.5, -3.5), (0.6, 5.5, 0), "metal"), bx("FlangeE", (15.4, 1.5, -3.5), (16, 5.5, 0), "metal"),
              bx("Stem1", (4.5, 5, -2), (5.5, 7, -1), "metal")] + plate("Gauge1", (2.5, 7, -2.6), (7.5, 12, -1.4), "gauge", "metaldark")
    # The key board behind a front desk: a mahogany board with a moulded top, three rows of brass hooks, and on most of
    # them a room key with its brass tag hanging down (the keys of rooms whose guests are out: nearly all of them)
    # (B8) A moulded frame round the board, a stepped cornice, each hook turned up at its tip, and on the keys oval
    # brass fobs with the room number stamped on (`keytag`)
    keyrack = [bx("Board", (1, 1, -1), (15, 14.5, 0), "mahogany"),
               bx("Cornice", (0.5, 14.5, -2), (15.5, 15.25, 0), "mahogany"), bx("CorniceCap", (0.25, 15.25, -2.4), (15.75, 16, 0), "mahogany"),
               bx("Rail", (0.5, 0.5, -1.6), (15.5, 1.5, 0), "mahogany")]
    keyrack += [bx("FrameL", (1, 1.5, -1.4), (1.75, 14.5, -1), "mahogany", faces=("north", "east", "west")),
                bx("FrameR", (14.25, 1.5, -1.4), (15, 14.5, -1), "mahogany", faces=("north", "east", "west"))]
    for row, y in enumerate((13, 9, 5)):
        for col, x in enumerate((3, 6.3, 9.7, 13)):
            keyrack += [bx(f"Hook{row}{col}", (x - 0.25, y - 0.25, -2.2), (x + 0.25, y + 0.25, -1), "brass"),
                        bx(f"HookTip{row}{col}", (x - 0.25, y + 0.25, -2.45), (x + 0.25, y + 0.85, -2.0), "brass")]
            if (row * 4 + col) % 5 == 2:
                continue  # an empty hook
            keyrack += [bx(f"Key{row}{col}", (x - 0.25, y - 2.2, -1.9), (x + 0.25, y - 0.2, -1.5), "brass"),
                        bx(f"Tag{row}{col}", (x - 0.8, y - 3.4, -1.8), (x + 0.8, y - 2.2, -1.4), "keytag",
                           uv=[0, 0, 8, 8] if (row + col) % 2 else [8, 8, 16, 16])]
    decors = [
        Decor("mirror", "Gilt Mirror", {2: [bx("Frame", (3, 0, -1), (13, 16, 0), "gilt"),
                                            bx("Glass", (3.8, 0.8, -1.1), (12.2, 15.2, -1), "mirrorglass", faces=("north",), full=True)]}),
        Decor("speaker", "Speaker", {3: [bx("Box", (4, 3, -1.5), (12, 11, 0), "mahogany"),
                                         bx("Grille", (4.5, 3.5, -1.6), (11.5, 10.5, -1.5), "speakergrille", faces=("north",), full=True)]}),  # no ambient sound: the music is AtmosphereSystem.L5.cs
        Decor("housephone", "House Phone", {2: [bx("Plate", (5, 2, -1), (11, 13, 0), "bakelite"),
                                                bx("Dial", (6.2, 3, -1.4), (9.8, 6.6, -1), "phonedial", faces=("north",), full=True),
                                                bx("Handset", (4, 8, -2.6), (12, 9.6, -1.2), "bakelite"),
                                                bx("EarL", (4, 6.5, -2.6), (5.5, 8, -1.2), "bakelite"), bx("EarR", (10.5, 6.5, -2.6), (12, 8, -1.2), "bakelite")]}),
        Decor("firehose", "Fire Hose Cabinet", {2: plate("Cabinet", (2, 0, -2), (14, 15, 0), "hotelhosecab", "brass")}),
        Decor("clock", "Wall Clock", {3: plate("Clock", (4, 1, -1.5), (12, 12, 0), "ornateclock", "gilt")}),
        Decor("keyrack", "Key Rack", {2: keyrack}),
        # (B8) The call plate's two buttons are geometry: ivory pushes in brass bezels on a bevelled plate
        Decor("callplate", "Elevator Call Plate", {2: K.bevelled_box("Plate", (6, 3, -0.6), (10, 11, 0), "brass", b=0.2) + [
            e for y in (8.5, 5.5) for e in (K.box(f"Bezel{y}", (6.9, y - 1.1, -0.95), (9.1, y + 1.1, -0.6), "brass"),
                                             K.box(f"Push{y}", (7.35, y - 0.65, -1.25), (8.65, y + 0.65, -0.95), "callbutton"))]}),
        # (B8) The painting's frame as the portraits' (gen_shapes level5): a frame, a bead along it and an inner lip
        Decor("landscape", "Painting", {2: [bx("Canvas", (3.5, 3.5, -0.35), (12.5, 12.5, -0.25), "landscape", faces=("north",), full=True)]
                                        + gilt_frame("Frame", 2, 2, 14, 14, 1.25, -1.0, 0) + gilt_frame("Bead", 2.4, 2.4, 13.6, 13.6, 0.5, -1.35, -1.0)
                                        + gilt_frame("Lip", 3.0, 3.0, 13.0, 13.0, 0.5, -0.6, 0)}),
    ]
    wall_family("hoteldeco", "Hotel Wall", {1: "wainscot", 2: "hotelpanel", 3: "frieze"}, decors, material="Wood", sounds=WOOD)
    pipesv = [bx("Rusty", (2, 0, -4), (5, 16, 0), "rust", faces=("north", "east", "west")),
              bx("Lagged", (9, 0, -3.5), (13, 16, 0), "lagging", faces=("north", "east", "west"))]
    wheel = [bx("Stem", (7.5, 9.5, -5), (8.5, 10.5, -3), "metal"),
             bx("RimT", (5, 12.5, -6), (11, 13.5, -5), "valve"), bx("RimB", (5, 6.5, -6), (11, 7.5, -5), "valve"),
             bx("RimL", (4.5, 7, -6), (5.5, 13, -5), "valve"), bx("RimR", (10.5, 7, -6), (11.5, 13, -5), "valve"),
             bx("Spoke", (7.5, 7, -5.8), (8.5, 13, -5.2), "valve"), bx("SpokeH", (5, 9.5, -5.8), (11, 10.5, -5.2), "valve")]
    if D4_BAY_PIPES:
        pipesv_by_rel = {1: bay_risers(1, foot=True), 2: bay_risers(0, strut=True), 3: bay_risers(0), 4: bay_risers(0)}
        valve = (round_pipe("Pipe", 10, -1.9, 1.6, "wallrust")
                 + [e for e in wheel if e["name"] != "Stem"] + [bx("Stem", (7.5, 9.5, -5), (8.5, 10.5, -3.4), "metal")])
        cluster = (round_pipe("P1", 3.5, -1.7, 1.5, "wallrust") + round_pipe("P2", 8.0, -2.2, 2.0, "walllag")
                   + round_pipe("P3", 12.6, -1.4, 1.2, "wallrust")
                   + [bx("Strut", (7.25, 0.75, -0.75), (8.75, 15.25, 0), "flange", faces=("north", "east", "west", "up", "down"))]
                   + round_pipe("ClampP1", 3.5, -1.7, 1.8, "flange", 7.4, 8.6, shaded=False, faces=("east", "west"))
                   + round_pipe("ClampP2", 8.0, -2.2, 2.3, "flange", 7.4, 8.6, shaded=False, faces=("east", "west"))
                   + round_pipe("ClampP3", 12.6, -1.4, 1.5, "flange", 7.4, 8.6, shaded=False, faces=("east", "west")))
    else:
        pipesv_by_rel = {1: pipesv, 2: pipesv + [bx("Clamp", (1.5, 8, -4.5), (13.5, 9.5, 0), "metal")], 3: pipesv, 4: pipesv}
        valve = [bx("Pipe", (0, 8, -3), (16, 12, 0), "rust", faces=("north", "up", "down"))] + wheel
        cluster = [bx("P1", (0, 2, -3), (16, 5, 0), "rust", faces=("north", "up", "down")),
                   bx("P2", (0, 6, -4), (16, 10, 0), "lagging", faces=("north", "up", "down")),
                   bx("P3", (0, 11, -2.5), (16, 13.5, 0), "redpipe", faces=("north", "up", "down")),
                   bx("Bracket", (7, 1, -4.5), (9, 15, 0), "metal")]
    wall_family("plasterdeco", "Plaster Wall", {1: "plaster"}, [
        Decor("pipesv", "Pipes", pipesv_by_rel),
        Decor("valve", "Valve", {1: valve}),
        Decor("gauges", "Pressure Gauge", {2: gauges}),
        Decor("pipecluster", "Pipes", {3: cluster}),
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
    prop("hotelbookshelf", "Bookshelf", hotel_bookshelf_b10(), box=(0, 0, 0.5, 1, 1.95, 1))  # (B10)
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
    prop("hotelchair", "Side Chair", hotel_chair_b10(),  # (B10)
         box=(0.18, 0, 0.18, 0.82, 1.25, 0.82))
    prop("floorlamp", "Floor Lamp", [
        bx("Base", (5, 0, 5), (11, 1, 11), "brass"), bx("Pole", (7.5, 1, 7.5), (8.5, 24, 8.5), "brass"),
        bx("Shade", (4, 22, 4), (12, 29, 12), "lampshade", glow=120)],
         box=(0.25, 0, 0.25, 0.75, 1.8, 0.75), oriented=False, light=[6, 5, 10])
    prop("suitcase", "Suitcase", [
        bx("Case", (2, 0, 4), (14, 10, 12), "suitcaseleather"), bx("Handle", (6, 10, 7.5), (10, 11.5, 8.5), "bakelite"),
        bx("ClaspL", (4, 7, 3.7), (5, 8.5, 4), "brass"), bx("ClaspR", (11, 7, 3.7), (12, 8.5, 4), "brass")],
         box=(0.12, 0, 0.25, 0.88, 0.7, 0.75), material="Cloth", sounds=CLOTH)
    prop("coffeetable", "Coffee Table", coffee_table_b10(),  # (B10)
         box=(0.06, 0, 0.18, 0.94, 0.5, 0.82), oriented=False)
    prop("grandfatherclock", "Grandfather Clock", [
        bx("Base", (3, 0, 6), (13, 10, 14), "mahogany"), bx("Trunk", (4, 10, 6.5), (12, 24, 13.5), "mahogany"),
        bx("Window", (5, 12, 6.3), (11, 22, 6.5), "clockpendulum", faces=("north",), full=True),
        bx("Hood", (3, 24, 6), (13, 32, 14), "mahogany"),
        bx("Face", (4.5, 25, 5.8), (11.5, 31, 6), "clockface-old", faces=("north",), full=True),
        bx("Finial", (7.5, 32, 9.5), (8.5, 34, 10.5), "brass")],
         box=(0.18, 0, 0.36, 0.82, 1.95, 0.88), extra={"sounds": dict(WOOD, ambient="backrooms:ambient/clock", ambientBlockCount=1)})
    # (B8) The front desk's front is frame and panel as geometry (it was painted): a toe-recessed plinth, two raised and
    # fielded panels per block between stiles that meet the next block's, a brass rail under the counter's edge
    front = K.inset_panel("Front", (0, 1.5, 2), (16, 15.75, 5), "mahogany", border=1.25, depth=0.5, grid=(2, 1), mid=2.0)
    front = [e for e in front if not e["name"].startswith("FrontBody")] + [
        bx("FrontBody", (0, 1.5, 2.5), (16, 15.75, 5), "mahogany", faces=("north", "east", "west", "south"))]
    fields = [bx(f"Field{i}", (a + 0.75, b + 0.75, 2.25), (c - 0.75, d - 0.75, 2.5), "mahogany", faces=("north", "east", "west", "up", "down"))
              for i, (a, b, c, d) in enumerate(K.inset_panel.openings)]
    # a brass bead round each field, where the old front had its painted gold lines
    fields += [e for i, (a, b, c, d) in enumerate(K.inset_panel.openings)
               for e in gilt_frame(f"Inlay{i}", a + 0.2, b + 0.2, c - 0.2, d - 0.2, 0.35, 2.4, 2.5, "brass")]
    prop("hotelreception", "Front Desk", front + fields + [
        bx("Plinth", (0, 0, 2.75), (16, 1.5, 5), "mahoganydark", faces=("north", "east", "west", "south", "up")),
        bx("Frieze", (0, 15.75, 1.75), (16, 17, 5), "mahogany", faces=("north", "east", "west", "south", "down")),
        bx("Rail", (0, 16.1, 1.45), (16, 16.6, 1.75), "brass", faces=("north", "up", "down", "east", "west")),
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
         box=(0.03, 0, 0.03, 0.97, 0.78, 0.97), oriented=False, light=[6, 5, 7], extra={"particleProperties": DININGTABLE_FLAMES})
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
    # (B6) The heap's three tiers now have lumps of coal on and round them, each its own box, turned a little
    prop("coalpile", "Coal", [
        bx("Heap1", (1, 0, 1), (15, 3, 15), "coal"), bx("Heap2", (3, 3, 3), (13, 6, 12), "coal"), bx("Heap3", (5, 6, 5), (10, 8, 10), "coal")]
        + coal_lumps() + [
        bx("Handle", (11, 4, 10), (12, 16, 11), "wood", rot=(0, 0, 15), origin=(11.5, 4, 10.5)),
        bx("Blade", (10, 2, 9.5), (13, 6, 10.1), "metaldark")], box=(0.06, 0, 0.06, 0.94, 0.5, 0.94), oriented=False, sounds=STONE)


# ======================= Vanilla machinery =======================

# Vintage Story's own machinery and clutter shapes, wrapped as our props so they break down like the rest of the
# building (Breakdown.cs: metal, a bracket now and then) and need no block entity. Every texture is named with its
# game: path; the bright tin bronze and the temporal glow of the ruins are swapped for tarnished metal and smoky glass.
GAME_TEX = {
    "tinbronze": "block/metal/tarnished/tarnished-bronze", "bituminous": "block/coal/bituminous", "quartz": "block/glass/quartz",
    "copper1": "block/metal/tarnished/tarnished-copper", "plainoak": "block/wood/debarked/oak", "tempglow": "block/glass/smoky",
    "anthracite": "block/coal/anthracite", "iron1": "block/metal/sheet/iron1", "aged": "block/wood/debarked/oak",
    "copper5": "block/metal/tarnished/rusty-iron1", "device-plate": "block/machine/device-plate", "smoky": "block/glass/smoky",
    "rusty-iron": "block/metal/tarnished/rusty-iron", "brass": "block/metal/tarnished/brass", "silver": "block/metal/tarnished/silver",
}
VANILLA_TEX_KEYS = {
    "devastation/machinery/gauge3": ["bituminous", "tinbronze"],
    "devastation/machinery/gauge4": ["bituminous", "quartz", "tinbronze"],
    "devastation/machinery/valve2": ["copper1", "plainoak", "tinbronze"],
    "devastation/machinery/sightglass2": ["tempglow", "tinbronze"],
    "devastation/machinery/lever1": ["aged", "anthracite", "iron1", "tinbronze"],
    "devastation/machinery/lever2": ["aged", "anthracite", "iron1", "tinbronze"],
    "clutter/tank-metal1": ["copper5"],
    "clutter/tank-metal2": ["copper5"],
    "clutter/machine6": ["brass", "device-plate", "rusty-iron", "smoky"],
    "clutter/machine7": ["brass", "device-plate", "rusty-iron", "silver", "smoky"],
}
# Which way, in a north-facing frame, each side pushes a model: toward the wall behind it (south once turned)
_BACK = {"north": (0, 1), "east": (-1, 0), "south": (0, -1), "west": (1, 0)}


def vanilla_prop(code, english, kinds, box, back=0.0, turn=0, material="Metal", sounds=METAL, comment=None, extra=None):
    """A prop drawn with vanilla shapes: `kinds` maps a kind to a shape under game:shapes/block/. Like our own props it
    faces north (Tile.Pier) and turns with its side; `turn` first turns the vanilla model (180 for the wall pieces,
    which vanilla models with their back to the north), and `back` pushes it that far toward the wall behind it."""
    by_type, textures = {}, {}
    for k, sp in kinds.items():
        for key in VANILLA_TEX_KEYS[sp]:
            textures[key] = {"base": "game:" + GAME_TEX[key]}
        for s in SIDES:
            shp = {"base": "game:block/" + sp, "rotateY": (ROTATE[s] + turn) % 360}
            if back:
                dx, dz = _BACK[s]
                if dx:
                    shp["offsetX"] = dx * back
                if dz:
                    shp["offsetZ"] = dz * back
            by_type[f"*-{k}-{s}"] = shp
    first = next(iter(kinds))
    block(code, {
        "variantgroups": [{"code": "kind", "states": list(kinds)}, {"code": "side", "states": SIDES}],
        "shapeByType": by_type,
        "textures": dict(sorted(textures.items())),
        "creativeinventory": {"general": [f"*-{first}-north"], "decorative": [f"*-{first}-north"]},
        "blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "lightAbsorption": 0, "resistance": 3, "sounds": sounds,
        "collisionboxByType": {f"*-{s}": cuboid(box, s) for s in SIDES},
        "selectionboxByType": {f"*-{s}": cuboid(box, s) for s in SIDES},
        **(extra or {}),
    }, comment or english)
    for k in kinds:
        name(f"{code}-{k}-*", english if isinstance(english, str) else english[k])


def machinery():
    # Gauge boards, a valve manifold and a sight glass on their pipes, standing against a wall (only their back third
    # is solid, so a tunnel stays as wide as it was)
    vanilla_prop("gaugeframe", {"gauges": "Pressure Gauges", "manifold": "Pressure Gauges", "valve": "Valve Manifold",
                                "sightglass": "Sight Glass"}, {
        "gauges": "devastation/machinery/gauge3", "manifold": "devastation/machinery/gauge4",
        "valve": "devastation/machinery/valve2", "sightglass": "devastation/machinery/sightglass2"},
        box=(0.05, 0, 0.62, 0.95, 1, 1), back=0.4, turn=180, comment="Gauges, valves and sight glasses on their pipework, against a wall",
        # The valve's packing has given: a thin hiss of steam from round its spindle (the wheel stands 0.3 below the
        # top middle of the solid back third, right over it)
        extra={"particlePropertiesByType": {"*-valve-*": [fire_fx.steam(0, -0.3, 0, quantity=0.04, velocity=(0, 0.25, 0))]}})
    # Rusted pressure vessels, plain and with their outlets
    vanilla_prop("pressuretank", "Pressure Tank", {"plain": "clutter/tank-metal1", "valved": "clutter/tank-metal2"},
                 box=(0.19, 0, 0.19, 0.81, 1, 0.95), comment="Rusted pressure vessels")
    # What is left of the pumps and governors of some long-stopped machine
    vanilla_prop("rustmachine", "Old Machinery", {"pump": "clutter/machine6", "governor": "clutter/machine7"},
                 box=(0.1, 0, 0.1, 0.9, 0.85, 0.9), comment="Rusted pumps and governors of some long-stopped machine")
    # Floor levers for a boiler's dampers and feed, one handle or two
    vanilla_prop("floorlever", "Floor Lever", {"single": "devastation/machinery/lever1", "double": "devastation/machinery/lever2"},
                 box=(0.2, 0, 0.12, 0.8, 1, 0.9), comment="Floor levers, one handle or two")


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
    staff_plaques()
    doors()
    level1()
    level3()
    level4()
    level5()
    machinery()
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
