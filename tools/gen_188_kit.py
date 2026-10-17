"""Level 188: the shared kit for gen_188*.py (files, shapes, block types, boxes in block space, lang).

Conventions as in detail_kit.py: boxes in block space (0-16, may reach outside the block); every model is built with
its front facing north (-Z) and turned for the other sides with rotateY (north 0, east 270, south 180, west 90).
`l`/`r` in a part name = left/right as seen by someone standing in front of the front face, looking at it; with the
front facing north that viewer looks south, so their left is +X.

Two-by-two things (windows, the hatch) are modelled whole in "composite" space (X 0-32, Y 0-32) and clipped into
their four parts, so frames, rolls and features run on across the joints.
"""
import itertools
import json
import os
import re

from detail_kit import bx, turn, shift  # noqa: F401  (re-exported)

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
SRC = os.path.join(ROOT, "src")
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
ALL = ("north", "east", "south", "west", "up", "down")

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CERAMIC = {"walk": "game:walk/stone*", "place": "game:block/ceramicplace", "break": "game:block/ceramicbreak", "hit": "game:block/ceramichit"}
GRASS = {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}
GRAVEL = {"walk": "game:walk/gravel*", "place": "game:block/gravel", "break": "game:block/gravel", "hit": "game:block/gravel"}

LANG = {}
WRITTEN = {"blocktypes": [], "shapes": [], "itemtypes": [], "entities": []}
COUNT = {"variants": 0}


# ================================================================ Files

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def tpath(key):
    if ":" in key:
        return key
    if key.startswith("item/"):
        return "backrooms:item/188/" + key[5:]
    return "backrooms:block/188/" + key


def _flat(els):
    for e in els:
        yield e
        yield from _flat(e.get("children", []))


def shape(name, elements):
    keys = sorted({face["texture"][1:] for e in _flat(elements) for face in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in keys}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", "block", "188", name + ".json"), data)
    WRITTEN["shapes"].append(name)
    return "backrooms:block/188/" + name


def block(code, data, comment=None):
    write_json(os.path.join(ASSETS, "blocktypes", "188", code + ".json"), dict({"code": code}, **data), comment)
    WRITTEN["blocktypes"].append(code)


def registered(name):
    """True once the code has registered a class or behaviour of this name in src/ (so a JSON file may name it)."""
    pat = re.compile(r'Register\w*\(\s*"' + re.escape(name) + r'"')
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            if f.endswith(".cs"):
                with open(os.path.join(dirpath, f), encoding="utf-8", errors="ignore") as fh:
                    if pat.search(fh.read()):
                        return True
    return False


_REG = {}


def reg(name):
    if name not in _REG:
        _REG[name] = registered(name)
    return _REG[name]


def drops(*items):
    out = []
    for code, avg, var in items:
        kind = "item"
        if code.startswith("block:"):
            kind, code = "block", code[6:]
        out.append({"type": kind, "code": code, "quantity": {"avg": avg, "var": var}})
    return out


def cuboid(box, angle=0):
    x1, y1, z1, x2, y2, z2 = box
    c = {"x1": round(x1, 4), "y1": round(y1, 4), "z1": round(z1, 4), "x2": round(x2, 4), "y2": round(y2, 4), "z2": round(z2, 4)}
    if angle:
        c["rotateY"] = angle
    return c


def vox(box):
    """A box in voxels (0-16) as a block-unit box."""
    return tuple(v / 16 for v in box)


# ================================================================ Boxes

def bxa(name, frm, to, tex, faces=ALL, glow=0):
    """A box whose UVs follow its position in the block, so textures run on across neighbouring boxes (boards cut
    along an arc, a picture split over several boxes). UVs are kept inside 0-16."""
    (x1, y1, z1), (x2, y2, z2) = frm, to

    def fit(a, b):
        lo = min(a, b)
        k = 0
        while lo + k < 0:
            k += 16
        while lo + k >= 16:
            k -= 16
        a, b = a + k, b + k
        return max(0, min(16, a)), max(0, min(16, b))

    uvs = {
        "up": (fit(x1, x2), fit(z1, z2)), "down": (fit(x1, x2), fit(16 - z2, 16 - z1)),
        "north": (fit(16 - x2, 16 - x1), fit(16 - y2, 16 - y1)), "south": (fit(x1, x2), fit(16 - y2, 16 - y1)),
        "east": (fit(16 - z2, 16 - z1), fit(16 - y2, 16 - y1)), "west": (fit(z1, z2), fit(16 - y2, 16 - y1)),
    }
    out = {}
    for f in faces:
        (u1, u2), (v1, v2) = uvs[f]
        face = {"texture": "#" + tex, "uv": [round(u1, 4), round(v1, 4), round(u2, 4), round(v2, 4)]}
        if glow:
            face["glow"] = glow
        out[f] = face
    return {"name": name, "from": [x1, y1, z1], "to": [x2, y2, z2], "faces": out}


def bxf(name, frm, to, tex, faces=ALL, glow=0, back=None):
    """A box with the whole texture stretched over each face (pictures, signs); `back` puts another texture on the
    south face."""
    el = bx(name, frm, to, tex, glow=glow, faces=faces, full=True)
    if back and "south" in el["faces"]:
        el["faces"]["south"]["texture"] = "#" + back
    return el


def retex(el, face, tex, glow=None, uv=None):
    el["faces"][face]["texture"] = "#" + tex
    if glow is not None:
        if glow:
            el["faces"][face]["glow"] = glow
        else:
            el["faces"][face].pop("glow", None)
    if uv is not None:
        el["faces"][face]["uv"] = uv
    return el


def cube(tex, faces=None):
    """A full cube; `faces` overrides the texture on some faces."""
    c = bx("Cube", (0, 0, 0), (16, 16, 16), tex)
    for f, t in (faces or {}).items():
        c["faces"][f]["texture"] = "#" + t
    return c


def mirror_x(els):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [16 - x2, y1, z1], [16 - x1, y2, z2]
        f = e["faces"]
        east, west = f.pop("east", None), f.pop("west", None)
        if west is not None:
            f["east"] = west
        if east is not None:
            f["west"] = east
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [16 - o[0], o[1], o[2]]
            for k in ("rotationY", "rotationZ"):
                if k in e:
                    e[k] = -e[k]
        if "children" in e:
            e["children"] = mirror_x(e["children"])
        out.append(e)
    return out


def cyl(name, cx, cz, r, y1, y2, tex, glow=0, k=0.62):
    """A rough round post: a cross of two boxes."""
    return [bx(name, (cx - r, y1, cz - r * k), (cx + r, y2, cz + r * k), tex, glow),
            bx(name + "b", (cx - r * k, y1, cz - r), (cx + r * k, y2, cz + r), tex, glow)]


def clip(els, lo, hi, offset=(0, 0, 0), absolute_uv=False):
    """Clips unrotated boxes to the region lo..hi (composite space) and moves them by -offset. Faces cut open by the
    clip are dropped (the neighbouring part carries on the box). Boxes that fall outside are left out."""
    out = []
    for e in els:
        if any(k in e for k in ("rotationX", "rotationY", "rotationZ")):
            c = [(e["from"][i] + e["to"][i]) / 2 for i in range(3)]
            if all(lo[i] <= c[i] <= hi[i] for i in range(3)):
                e = json.loads(json.dumps(e))
                e["from"] = [e["from"][i] - offset[i] for i in range(3)]
                e["to"] = [e["to"][i] - offset[i] for i in range(3)]
                e["rotationOrigin"] = [e["rotationOrigin"][i] - offset[i] for i in range(3)]
                out.append(e)
            continue
        f0, t0 = e["from"], e["to"]
        f1 = [max(f0[i], lo[i]) for i in range(3)]
        t1 = [min(t0[i], hi[i]) for i in range(3)]
        if any(t1[i] - f1[i] <= 1e-6 for i in range(3)):
            continue
        e = json.loads(json.dumps(e))
        cut = {"west": f1[0] > f0[0] + 1e-6, "east": t1[0] < t0[0] - 1e-6, "down": f1[1] > f0[1] + 1e-6,
               "up": t1[1] < t0[1] - 1e-6, "north": f1[2] > f0[2] + 1e-6, "south": t1[2] < t0[2] - 1e-6}
        faces = {k: v for k, v in e["faces"].items() if not cut.get(k)}
        if not faces:
            continue
        nf = [f1[i] - offset[i] for i in range(3)]
        nt = [t1[i] - offset[i] for i in range(3)]
        if absolute_uv:
            tex = {k: v["texture"][1:] for k, v in faces.items()}
            glow = {k: v.get("glow", 0) for k, v in faces.items()}
            ne = bxa(e["name"], nf, nt, "x", faces=tuple(faces))
            for k in ne["faces"]:
                ne["faces"][k]["texture"] = "#" + tex[k]
                if glow[k]:
                    ne["faces"][k]["glow"] = glow[k]
            # pictures stretched over the whole part keep their own full UVs
            for k, v in faces.items():
                if v.get("uv") == [0, 0, 16, 16] and nf[0] <= 0.01 and nt[0] >= 15.99 and nf[1] <= 0.01 and nt[1] >= 15.99:
                    ne["faces"][k]["uv"] = [0, 0, 16, 16]
            out.append(ne)
            continue
        e["faces"] = faces
        # keep the texture scale: UV spans follow the clipped size
        for k, v in faces.items():
            if v.get("uv") and v["uv"] != [0, 0, 16, 16]:
                w, h, d = nt[0] - nf[0], nt[1] - nf[1], nt[2] - nf[2]
                a, b = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[k]
                v["uv"] = [0, 0, round(min(16, max(a, 0.25)), 4), round(min(16, max(b, 0.25)), 4)]
        e["from"], e["to"] = nf, nt
        out.append(e)
    return out


PARTS = ("ll", "lr", "ul", "ur")


def part_offset(part):
    """Where a part of a 2 x 2 sits in composite space (front facing north: the viewer's left is +X)."""
    return (16 if part[1] == "l" else 0, 0 if part[0] == "l" else 16, 0)


def split(els, part, zlo=-64, zhi=64, absolute_uv=True):
    ox, oy, _ = part_offset(part)
    return clip(els, (ox, oy, zlo), (ox + 16, oy + 16, zhi), (ox, oy, 0), absolute_uv=absolute_uv)


def split_boxes(boxes, part):
    """Collision boxes (composite voxels) clipped into a part, as block units."""
    ox, oy, _ = part_offset(part)
    out = []
    for (x1, y1, z1, x2, y2, z2) in boxes:
        a, b = max(x1, ox), min(x2, ox + 16)
        c, d = max(y1, oy), min(y2, oy + 16)
        if b - a > 1e-6 and d - c > 1e-6:
            out.append(vox((a - ox, c - oy, z1, b - ox, d - oy, z2)))
    return out


def vx(x1, x2):
    """Viewer's left-to-right x (0-32 across a 2 x 2 seen from its front) to composite X (left is +X)."""
    return 32 - x2, 32 - x1


# ================================================================ Block types

def vblock(code, english, groups, build, rot="side", box=None, boxes=None, collide=True, data=None, comment=None,
           names=None, creative=None, sel=None, colboxes=None, selboxes=None, material="Wood", sounds=WOOD):
    """A block type over every combination of `groups` [(group, states)]. build(v) returns the elements for a
    variant (dict group -> state), modelled facing north; the group named `rot` turns it. `box` (block units) is the
    collision and selection box of the unturned model, or `boxes(v)`. `colboxes(v)` / `selboxes(v)` give lists."""
    combos = list(itertools.product(*[states for _, states in groups])) if groups else [()]
    shapes, col, sel_ = {}, {}, {}
    cols, sels = {}, {}
    cache = {}
    for combo in combos:
        v = dict(zip([g for g, _ in groups], combo))
        key = tuple(s for (g, _), s in zip(groups, combo) if g != rot)
        if key not in cache:
            els = build(v)
            nm = code + ("-" + "-".join(key) if key else "")
            cache[key] = shape(nm, els)
        full = code + ("-" + "-".join(combo) if combo else "")
        angle = ROTATE[v[rot]] if rot else 0
        shapes[full] = {"base": cache[key], "rotateY": angle} if angle else {"base": cache[key]}
        b = boxes(v) if boxes else box
        if b is not None:
            col[full] = cuboid(b, angle)
        sb = sel(v) if sel else None
        if sb is not None:
            sel_[full] = cuboid(sb, angle)
        if colboxes:
            cols[full] = [cuboid(c, angle) for c in colboxes(v)]
        if selboxes:
            sels[full] = [cuboid(c, angle) for c in selboxes(v)]
    COUNT["variants"] += len(combos)
    out = {}
    if groups:
        out["variantgroups"] = [{"code": g, "states": list(s)} for g, s in groups]
    if len(shapes) == 1:
        out["shape"] = next(iter(shapes.values()))
    else:
        out["shapeByType"] = shapes
    first = code + ("-" + "-".join(c[0] for _, c in groups) if groups else "")
    out["creativeinventory"] = creative or {"general": [first], "backrooms": [first]}
    out.update({"blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                "lightAbsorption": 0, "resistance": 1.5, "sounds": sounds})

    def put(name, d):
        if not d:
            return
        vals = list(d.values())
        if len(set(json.dumps(x, sort_keys=True) for x in vals)) == 1:
            out[name] = vals[0]
        else:
            out[name + "ByType"] = d

    if cols:
        put("collisionboxes", cols)
    elif collide:
        put("collisionbox", col)
    else:
        out["collisionbox"] = None
    if sels:
        put("selectionboxes", sels)
    else:
        put("selectionbox", sel_ or col)
    if data:
        out.update(data)
    block(code, out, comment or english)
    for pat, eng in (names or {}).items():
        LANG["block-" + pat] = eng
    LANG.setdefault(f"block-{code}-*" if groups else f"block-{code}", english)


def _tex_entry(key):
    """A cube face's texture, with the surface's graphics-pass (B16) versions as alternates when it has any."""
    import gen_188_b16
    keys = gen_188_b16.versions(key)
    e = {"base": tpath(key).replace("backrooms:", "")}
    if len(keys) > 1:
        e["alternates"] = [{"base": tpath(k).replace("backrooms:", "")} for k in keys[1:]]
    return e


def cube_block(code, english, groups, faces, data=None, comment=None, names=None, material="Stone", sounds=STONE):
    """A cube block type: faces(v) gives the texture key of each face (a dict with 'all' and/or face names)."""
    combos = list(itertools.product(*[states for _, states in groups])) if groups else [()]
    tex = {}
    for combo in combos:
        v = dict(zip([g for g, _ in groups], combo))
        full = code + ("-" + "-".join(combo) if combo else "")
        tex[full] = {f: _tex_entry(t) for f, t in faces(v).items()}
    COUNT["variants"] += len(combos)
    out = {}
    if groups:
        out["variantgroups"] = [{"code": g, "states": list(s)} for g, s in groups]
    if len(tex) == 1:
        out["textures"] = next(iter(tex.values()))
    else:
        out["texturesByType"] = tex
    first = code + ("-" + "-".join(c[0] for _, c in groups) if groups else "")
    out.update({"creativeinventory": {"general": [first], "backrooms": [first]}, "blockmaterial": material, "drawtype": "cube",
                "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds})
    if data:
        out.update(data)
    block(code, out, comment or english)
    for pat, eng in (names or {}).items():
        LANG["block-" + pat] = eng
    LANG.setdefault(f"block-{code}-*" if groups else f"block-{code}", english)


def facing_faces(side, front, back, ends, up=None, down=None):
    """Cube faces for a block with a front: `front` on the side it faces, `back` opposite, `ends` on the other two."""
    opp = {"north": "south", "south": "north", "east": "west", "west": "east"}
    f = {s: ends for s in SIDES}
    f[side] = front
    f[opp[side]] = back
    f["up"] = up or ends
    f["down"] = down or ends
    return f


# ================================================================ Lang

TAB, NL = "\t", "\n"


def merge_lang():
    """Updates the level's keys in lang/en.json in place: existing keys (the scaffold's placeholders among them) are
    rewritten where they stand, new ones go right after the last of the level's keys already there, so nothing else
    in the shared file moves."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    index = {}
    for i, line in enumerate(lines):
        m = re.match(r'^\s*"((?:[^"\\]|\\.)*)"\s*:', line)
        if m:
            index[json.loads('"' + m.group(1) + '"')] = i
    new = []
    for key, value in LANG.items():
        enc = "\t" + json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False)
        if key in index:
            i = index[key]
            comma = "," if lines[i].rstrip().endswith(",") else ""
            lines[i] = enc + comma
        else:
            new.append(enc)
    if new:
        mine = [index[k] for k in LANG if k in index]
        anchor = max(mine) if mine else index["levelname-20"]
        trailing = lines[anchor].rstrip().endswith(",")
        if not trailing:
            lines[anchor] = lines[anchor].rstrip() + ","
        block_lines = [ln + "," for ln in new[:-1]] + [new[-1] + ("," if trailing else "")]
        lines[anchor + 1:anchor + 1] = block_lines
    out = "\n".join(lines)
    json.loads(re.sub(r"^\s*//.*$", "", out, flags=re.M))  # still valid
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(f"lang: {len(LANG)} keys ({len(new)} new)")
