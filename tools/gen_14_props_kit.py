"""Level 14 "The Hospital": the shared helpers of the furniture and equipment generator (tools/gen_14_props.py):
boxes (modelkit's, with this level's texture keys), turned and tilted parts, octagonal prisms, arcs, cutting a two-block
model into its halves, and the shape and block type writers. Every shape here is modelled facing north (its front
toward -Z) and turned with rotateY (north 0, east 270, south 180, west 90); seen from the north, the viewer's left is +X.
"""
import itertools
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modelkit as MK  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
SHAPES = os.path.join(ASSETS, "shapes", "block", "14")
BLOCKS = os.path.join(ASSETS, "blocktypes", "14")
TEXPATH = "backrooms:block/14/"

SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
DIRS = MK.DIRS

WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
PLANT = {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}
SOFT = {"walk": "game:walk/cloth", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}

CODES = []
SHAPE_FILES = []


# ======================================================================== Elements

def B(name, frm, to, tex, faces=None, glow=0, rot=None, origin=None, uv=None):
    """A box (modelkit.box): tex is one key or a dict by role (top, side, front, back, bottom) or by face."""
    return MK.box(name, frm, to, tex, faces=faces or DIRS, glow=glow, rot=rot, origin=origin, uv=uv)


def no(*drop):
    return tuple(f for f in DIRS if f not in drop)


def pic(el, face, key, glow=0, uv=(0, 0, 16, 16)):
    """Stretches a whole picture texture over one face."""
    el["faces"][face] = {"texture": "#" + key, "uv": list(uv)}
    if glow:
        el["faces"][face]["glow"] = glow
    return el


def glow(els, g):
    for e in els:
        for f in e["faces"].values():
            f["glow"] = g
    return els


def turned(els, rx=0, ry=0, rz=0, origin=(8, 0, 8)):
    """Sets one rotation about `origin` on elements that have none (a part tilted or turned as a whole)."""
    for e in els:
        assert not any(k in e for k in ("rotationX", "rotationY", "rotationZ")), e["name"]
        e["rotationOrigin"] = [round(v, 4) for v in origin]
        for k, a in (("rotationX", rx), ("rotationY", ry), ("rotationZ", rz)):
            if a:
                e[k] = a
    return els


def transparent(el):
    el["renderPass"] = 3
    return el


def rename(els, prefix):
    for e in els:
        e["name"] = prefix + e["name"]
    return els


def octagon(name, cx, cz, r, y1, y2, tex, faces=None, step=0.02):
    """A regular octagonal prism of inradius r standing on y1: two crossed boxes and the same turned 45 degrees, each
    a hair shorter than the last so no two tops share a plane."""
    a = r * math.tan(math.pi / 8)
    els = []
    for k, (hx, hz, ry) in enumerate(((r, a, 0), (a, r, 0), (r, a, 45), (a, r, 45))):
        d = k * step
        els.append(B(f"{name}{k}", (cx - hx, y1 + d, cz - hz), (cx + hx, y2 - d, cz + hz), tex, faces=faces,
                     rot=(0, ry, 0) if ry else None, origin=(cx, y1, cz)))
    return els


def octagon_x(name, cx, cy, cz, r, x1, x2, tex, step=0.02):
    """An octagonal prism lying along x (a wheel, a roll, a drum on its side): crossed boxes turned about x."""
    a = r * math.tan(math.pi / 8)
    els = []
    for k, (hy, hz, rx) in enumerate(((r, a, 0), (a, r, 0), (r, a, 45), (a, r, 45))):
        d = k * step
        els.append(B(f"{name}{k}", (x1 + d, cy - hy, cz - hz), (x2 - d, cy + hy, cz + hz), tex,
                     rot=(rx, 0, 0) if rx else None, origin=(x1, cy, cz)))
    return els


def octagon_z(name, cx, cy, cz, r, z1, z2, tex, step=0.02):
    """An octagonal prism lying along z."""
    a = r * math.tan(math.pi / 8)
    els = []
    for k, (hx, hy, rz) in enumerate(((r, a, 0), (a, r, 0), (r, a, 45), (a, r, 45))):
        d = k * step
        els.append(B(f"{name}{k}", (cx - hx, cy - hy, z1 + d), (cx + hx, cy + hy, z2 - d), tex,
                     rot=(0, 0, rz) if rz else None, origin=(cx, cy, z1)))
    return els


def rod(name, axis, c1, c2, r, a, b, tex, faces=None):
    """A round bar or bottle body as a cross of two boxes (no rotation of its own, so it can be turned as a whole):
    along `axis` ("x", "y" or "z") from a to b, centred on (c1, c2) in the other two axes (x/z for y, y/z for x,
    x/y for z), of half-width r; the narrow box is 0.414 r, so the cross reads as an octagon's outline."""
    s = r * 0.62
    out = []
    for k, (h1, h2) in enumerate(((r, s), (s, r))):
        h1 -= k * 0.02
        if axis == "y":
            frm, to = (c1 - h1, a, c2 - h2), (c1 + h1, b - k * 0.02, c2 + h2)
        elif axis == "x":
            frm, to = (a, c1 - h1, c2 - h2), (b - k * 0.02, c1 + h1, c2 + h2)
        else:
            frm, to = (c1 - h1, c2 - h2, a), (c1 + h1, c2 + h2, b - k * 0.02)
        out.append(B(f"{name}{k}", frm, to, tex, faces=faces))
    return out


def arc(name, cx, cz, r1, r2, y1, y2, a1, a2, n, tex, faces=None, dy=0.015):
    """A ring segment about (cx, cz) between radii r1 and r2, from angle a1 to a2 (degrees: 0 points north (-z), 90
    west (-x)), as n boxes each turned to its own angle; alternate boxes stand a hair apart in height so their
    overlapping tops do not fight."""
    els = []
    da = (a2 - a1) / n
    half = r2 * math.tan(math.radians(abs(da)) / 2) + 0.04
    for k in range(n):
        ang = a1 + da * (k + 0.5)
        e = (k % 2) * dy
        els.append(B(f"{name}{k}", (cx - half, y1 + e, cz - r2), (cx + half, y2 + e, cz - r1), tex, faces=faces,
                     rot=(0, round(ang, 3), 0), origin=(cx, y1, cz)))
    return els


def mirror_x(els):
    """The elements mirrored left to right (x -> 16 - x), east and west faces swapped, Y/Z rotations negated."""
    out = []
    for e in json.loads(json.dumps(els)):
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [round(16 - x2, 4), y1, z1], [round(16 - x1, 4), y2, z2]
        f = e["faces"]
        east, west = f.pop("east", None), f.pop("west", None)
        if west is not None:
            f["east"] = west
        if east is not None:
            f["west"] = east
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [round(16 - o[0], 4), o[1], o[2]]
            for k in ("rotationY", "rotationZ"):
                if k in e:
                    e[k] = -e[k]
        out.append(e)
    return out


def move(els, dx=0.0, dy=0.0, dz=0.0):
    return MK.move(els, dx, dy, dz)


def turn(els, times):
    return MK.turn(els, times)


def clip_z(els, z1, z2, shift):
    """The part of a model between z1 and z2, moved by `shift` along z: boxes wholly inside are kept, boxes across a
    cut are cut there (losing the face at the cut), rotated boxes must lie wholly on one side."""
    out = []
    for e in els:
        a, b = e["from"][2], e["to"][2]
        if b <= z1 + 1e-6 or a >= z2 - 1e-6:
            continue
        rotated = any(k in e for k in ("rotationX", "rotationY", "rotationZ"))
        e = json.loads(json.dumps(e))
        if a < z1 - 1e-6 or b > z2 + 1e-6:
            assert not rotated, ("a rotated box across a cut", e["name"])
            if a < z1:
                e["from"][2] = z1
                e["faces"].pop("north", None)
            if b > z2:
                e["to"][2] = z2
                e["faces"].pop("south", None)
            if not e["faces"]:
                continue
            for f, face in e["faces"].items():
                (x1, y1, zz1), (x2, y2, zz2) = e["from"], e["to"]
                size = {"north": (x2 - x1, y2 - y1), "south": (x2 - x1, y2 - y1), "east": (zz2 - zz1, y2 - y1),
                        "west": (zz2 - zz1, y2 - y1), "up": (x2 - x1, zz2 - zz1), "down": (x2 - x1, zz2 - zz1)}[f]
                if face["uv"][2] <= 16 and face["uv"][3] <= 16 and face["uv"][0] == 0 and face["uv"][1] == 0:
                    face["uv"] = [0, 0, round(min(16, max(size[0], 0.5)), 4), round(min(16, max(size[1], 0.5)), 4)]
        out.append(e)
    return move(out, dz=shift)


# ======================================================================== Files

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def shape(name, els):
    keys = sorted({f["texture"][1:] for e in els for f in e["faces"].values()})
    names = [e["name"] for e in els]
    assert len(names) == len(set(names)), (name, [n for n in names if names.count(n) > 1])
    write_json(os.path.join(SHAPES, name + ".json"),
               {"textureWidth": 16, "textureHeight": 16, "textures": {k: TEXPATH + k for k in keys}, "elements": els})
    SHAPE_FILES.append(name)
    return "backrooms:block/14/" + name


def cuboid(b, angle=0):
    x1, y1, z1, x2, y2, z2 = b
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if angle and not (abs(x1 + x2 - 1) < 1e-9 and abs(z1 + z2 - 1) < 1e-9 and (angle == 180 or abs(x2 - x1 - (z2 - z1)) < 1e-9)):
        c["rotateY"] = angle
    return c


def drops(*items):
    """[(code, avg, var)] as a drops list."""
    return [{"type": "item", "code": c, "quantity": {"avg": a, "var": v}} for c, a, v in items]


def block(code, groups, build, comment, boxes=None, sel=None, rot="side", material="Wood", sounds=WOOD, data=None,
          inventory=None):
    """A block type over every combination of `groups` [(group, states)]. build(v) gives a variant's elements, modelled
    facing north; the group named `rot` turns it. boxes / sel are the collision / selection boxes (lists of 6-tuples in
    block units, unturned), or functions of v; None (or a function returning None) means none. sel defaults to boxes."""
    combos = list(itertools.product(*[s for _, s in groups])) if groups else [()]
    shapes, coll, sels, cache = {}, {}, {}, {}
    for combo in combos:
        v = dict(zip([g for g, _ in groups], combo))
        key = tuple(s for (g, _), s in zip(groups, combo) if g != rot)
        if key not in cache:
            cache[key] = shape(code + ("-" + "-".join(key) if key else ""), build(v))
        full = code + ("-" + "-".join(combo) if combo else "")
        angle = ROTATE.get(v[rot], 0) if rot in v else 0
        shapes[full] = {"base": cache[key], "rotateY": angle} if angle else {"base": cache[key]}
        cb = boxes(v) if callable(boxes) else boxes
        sb = sel(v) if callable(sel) else sel
        if sb is None:
            sb = cb
        coll[full] = [cuboid(b, angle) for b in cb] if cb else None
        sels[full] = [cuboid(b, angle) for b in sb] if sb else None
    out = {"code": code}
    if groups:
        out["variantgroups"] = [{"code": g, "states": list(s)} for g, s in groups]
    if len(shapes) == 1:
        out["shape"] = next(iter(shapes.values()))
    else:
        out["shapeByType"] = {("*-" + k[len(code) + 1:]) if k != code else "*": s for k, s in shapes.items()}
    if inventory:
        pattern = inventory
    else:
        pattern = ["*-north"] if rot in [g for g, _ in groups] else ["*"]
    out["creativeinventory"] = {"general": pattern, "backrooms": pattern}
    out.update({"blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                "lightAbsorption": 0, "resistance": 2, "sounds": sounds})
    for key, table in (("collisionbox", coll), ("selectionbox", sels)):
        table = {("*-" + k[len(code) + 1:]) if k != code else "*": x for k, x in table.items()}
        values = list(table.values())
        if all(json.dumps(x) == json.dumps(values[0]) for x in values):
            one = values[0]
            if one is None:
                out[key] = None
            elif len(one) == 1:
                out[key] = one[0]
            else:
                out[key + "es"] = one
        elif any(x is None for x in values) or all(len(x) == 1 for x in values if x):
            assert all(x is None or len(x) == 1 for x in values), (code, key, "None mixed with several boxes")
            out[key + "ByType"] = {k: (x[0] if x else None) for k, x in table.items()}
        else:
            out[key + "esByType"] = table
    out["drops"] = []
    if data:
        out.update(data)
    write_json(os.path.join(BLOCKS, code + ".json"), out, comment)
    CODES.append(code)
