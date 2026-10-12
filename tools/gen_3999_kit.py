"""Level 3999, the Neon Paradise: the shared kit for tools/gen_3999*.py (files, shapes, block types, text in boxes,
lang, checks). See tools/gen_3999.py.

Conventions as in detail_kit.py: boxes in block space (0-16 per axis, may reach outside the block); props are
modelled with their front facing north (toward -Z) and turned by the variant named `facing` (north 0, east 270,
south 180, west 90). Seen from the north, the viewer's left is +X: text runs from +X toward -X.
"""
import itertools
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from detail_kit import bx, turn, shift  # noqa: E402,F401

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "assets", "backrooms")
GAME = os.path.join(os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory")), "assets")
SRC = os.path.join(ROOT, "src")

SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90, "n": 0, "e": 270, "s": 180, "w": 90, "ns": 0, "we": 90}
ALL = ("north", "east", "south", "west", "up", "down")
SIDE4 = ("north", "east", "south", "west")

# The six neon colours of the level (the Fandom page's own palette) and their light hues on the game's 0-63 scale
COLOURS = ["magenta", "cyan", "blue", "pink", "orange", "lilac"]
NEON = {
    "magenta": ((0xD1, 0x3B, 0xF7), 51, 7),
    "cyan": ((0x64, 0xE8, 0xF7), 33, 6),
    "blue": ((0x45, 0x67, 0xED), 40, 7),
    "pink": ((0xFF, 0x2A, 0x5A), 62, 7),
    "orange": ((0xFF, 0x4A, 0x00), 3, 7),
    "lilac": ((0xFF, 0xA0, 0xFF), 53, 3),
}


def hsv(colour, v):
    _, h, s = NEON[colour]
    return [h, s, v]


STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
METAL = {"walk": "game:walk/stone*", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CERAMIC = {"walk": "game:walk/stone*", "place": "game:block/ceramicplace", "break": "game:block/ceramicbreak", "hit": "game:block/ceramichit"}

# Never broken (Protection): the building, its fixtures and its machines. The code reads this attribute.
FIXED = {"l3999structure": True}

LANG = {}
CODES = []        # block codes written
ITEMS = []        # item codes written
SHAPES = []       # shape paths written (folder/name)
SOUNDS = []       # sound paths written (folder/name)
RECIPES = []
COUNT = {"variants": 0}

# Texture keys that live elsewhere; any other key is ours in block/3999/
EXT = {
    "supplybox": "backrooms:block/supplybox-side",
    "supplyboxtop": "backrooms:block/supplybox-top",
    "fluorescent": "backrooms:block/props/tube-white",
}


# ======================================================================== Files

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def tpath(key):
    if key in EXT:
        return EXT[key]
    if key.startswith("item."):
        return f"backrooms:item/3999/{key[5:]}"
    return f"backrooms:block/3999/{key}"


def _flat(els):
    for e in els:
        yield e
        yield from _flat(e.get("children", []))


def shape(name, elements, folder="block/3999"):
    """Writes a shape; texture keys resolve with tpath()."""
    keys = sorted({face["texture"][1:] for e in _flat(elements) for face in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in keys}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", *folder.split("/"), name + ".json"), data)
    SHAPES.append(f"{folder}/{name}")
    return f"backrooms:{folder}/{name}"


def block(code, data, comment=None):
    write_json(os.path.join(ASSETS, "blocktypes", "3999", code + ".json"), dict({"code": code}, **data), comment)
    CODES.append(code)


def item(code, data, comment=None):
    write_json(os.path.join(ASSETS, "itemtypes", "3999", code + ".json"), dict({"code": code}, **data), comment)
    ITEMS.append(code)


def recipe(name, data, comment=None):
    write_json(os.path.join(ASSETS, "recipes", "grid", name + ".json"), data, comment)
    RECIPES.append(name)


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
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if angle:
        c["rotateY"] = angle
    return c


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


_registered = None


def registered(cls, kind="Block"):
    """True when the mod's code registers this class (block, block entity, behaviour or item): block types name a
    class only once it exists, so the game never logs a missing class. Run the generator again when the code lands."""
    global _registered
    if _registered is None:
        _registered = set()
        for root, _, files in os.walk(SRC):
            for fn in files:
                if fn.endswith(".cs"):
                    with open(os.path.join(root, fn), encoding="utf-8", errors="ignore") as f:
                        for m in re.finditer(r'Register(Block|BlockEntity|BlockBehavior|Item|Entity|EntityBehavior)Class\("([^"]+)"', f.read()):
                            _registered.add((m.group(1), m.group(2)))
    return (kind, cls) in _registered


def with_class(data, cls=None, entity=None, behavior=None, behavior_props=None):
    """Adds a block class, block entity class and behaviour to block-type data if the code has registered them."""
    if cls and registered(cls, "Block"):
        data["class"] = cls
    if entity and registered(entity, "BlockEntity"):
        data["entityClass"] = entity
    if behavior and registered(behavior, "BlockBehavior"):
        data.setdefault("behaviors", []).append({"name": behavior, **({"properties": behavior_props} if behavior_props else {})})
    return data


# ======================================================================== Element helpers

def rot(el, rx=0, ry=0, rz=0, origin=None):
    el = json.loads(json.dumps(el))
    (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
    el["rotationOrigin"] = list(origin) if origin else [(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2]
    for k, v in (("rotationX", rx), ("rotationY", ry), ("rotationZ", rz)):
        if v:
            el[k] = round(v, 3)
    return el


def glass(el):
    """Puts an element in the transparent render pass (glass, clear plastic)."""
    el["renderPass"] = 3
    return el


def picture(el, tex, face="north", glow=0):
    """Stretches a whole texture over one face of a box."""
    el["faces"][face] = {"texture": "#" + tex, "uv": [0, 0, 16, 16]}
    if glow:
        el["faces"][face]["glow"] = glow
    return el


def faces_box(nm, frm, to, tex_by_face, glow_by_face=None, full=False):
    """A box with a texture per face (only the faces given); full stretches each texture over its face."""
    el = bx(nm, frm, to, "x", faces=tuple(tex_by_face), full=full)
    for f, t in tex_by_face.items():
        el["faces"][f]["texture"] = "#" + t
        if glow_by_face and f in glow_by_face:
            el["faces"][f]["glow"] = glow_by_face[f]
    return el


def cube_el(side, up=None, down=None, name="Cube"):
    t = {f: side for f in SIDE4}
    t["up"] = up or side
    t["down"] = down or side
    return faces_box(name, (0, 0, 0), (16, 16, 16), t)


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
        out.append(e)
    return out


def move(els, dx=0, dy=0, dz=0):
    return shift(els, dx, dy, dz)


def rename(els, prefix):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["name"] = prefix + e["name"]
        out.append(e)
    return out


def scale_els(els, s, at=(8, 0, 8)):
    """Scales boxes modelled round (0, 0, 0) and moves them to `at`."""
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["from"] = [at[i] + e["from"][i] * s for i in range(3)]
        e["to"] = [at[i] + e["to"][i] * s for i in range(3)]
        for f in e["faces"].values():
            if f.get("uv") and f["uv"] != [0, 0, 16, 16]:
                f["uv"] = [round(min(16, max(0.5, v * s)), 3) for v in f["uv"]]
        if "rotationOrigin" in e:
            e["rotationOrigin"] = [at[i] + e["rotationOrigin"][i] * s for i in range(3)]
        out.append(e)
    return out


def cyl(name, cx, cz, r, y1, y2, tex, glow=0):
    """A rough round post: an octagon of two crossed boxes."""
    return [bx(name, (cx - r, y1, cz - r * 0.42), (cx + r, y2, cz + r * 0.42), tex, glow),
            bx(name + "b", (cx - r * 0.42, y1, cz - r), (cx + r * 0.42, y2, cz + r), tex, glow),
            rot(bx(name + "c", (cx - r * 0.42, y1, cz - r), (cx + r * 0.42, y2, cz + r), tex, glow), ry=45, origin=(cx, y1, cz)),
            rot(bx(name + "d", (cx - r, y1, cz - r * 0.42), (cx + r, y2, cz + r * 0.42), tex, glow), ry=45, origin=(cx, y1, cz))]


def four(els):
    out = []
    for i in range(4):
        for e in els:
            t = turn(e, i)
            t["name"] = f"{e['name']}{i}"
            out.append(t)
    return out


def hang(els):
    """A wall hanging modelled on the north face of a wall (z < 0), moved into the room-side block: it then sits
    against that block's south side and faces north."""
    return shift(els, dz=16)


# ======================================================================== Pixel fonts and text in boxes

F5 = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "10001", "11001", "10101", "10011", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    "&": ["01100", "10010", "10100", "01000", "10101", "10010", "01101"],
    "!": ["1", "1", "1", "1", "1", "0", "1"],
    "?": ["01110", "10001", "00001", "00010", "00100", "00000", "00100"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    ")": ["100", "010", "001", "001", "001", "010", "100"],
    "(": ["001", "010", "100", "100", "100", "010", "001"],
    "-": ["0000", "0000", "0000", "1111", "0000", "0000", "0000"],
    ".": ["0", "0", "0", "0", "0", "0", "1"],
    ",": ["00", "00", "00", "00", "00", "01", "10"],
    ":": ["0", "1", "1", "0", "1", "1", "0"],
    "'": ["1", "1", "0", "0", "0", "0", "0"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "#": ["01010", "11111", "01010", "01010", "01010", "11111", "01010"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    " ": ["000", "000", "000", "000", "000", "000", "000"],
}
F3 = {
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"], "C": ["011", "100", "100", "100", "011"],
    "D": ["110", "101", "101", "101", "110"], "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"], "H": ["101", "101", "111", "101", "101"], "I": ["111", "010", "010", "010", "111"],
    "J": ["001", "001", "001", "101", "010"], "K": ["101", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "M": ["101", "111", "111", "101", "101"], "N": ["110", "101", "101", "101", "101"], "O": ["010", "101", "101", "101", "010"],
    "P": ["110", "101", "110", "100", "100"], "Q": ["010", "101", "101", "110", "011"], "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"], "U": ["101", "101", "101", "101", "111"],
    "V": ["101", "101", "101", "101", "010"], "W": ["101", "101", "111", "111", "101"], "X": ["101", "101", "010", "101", "101"],
    "Y": ["101", "101", "010", "010", "010"], "Z": ["111", "001", "010", "100", "111"], "&": ["010", "101", "010", "101", "011"],
    ",": ["0", "0", "0", "1", "1"], ".": ["0", "0", "0", "0", "1"], "-": ["000", "000", "111", "000", "000"],
    ":": ["0", "1", "0", "1", "0"], "=": ["000", "111", "000", "111", "000"], ")": ["10", "01", "01", "01", "10"],
    "!": ["1", "1", "1", "0", "1"], "?": ["11", "01", "10", "00", "10"], "/": ["001", "001", "010", "100", "100"],
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"], "2": ["110", "001", "010", "100", "111"],
    "3": ["110", "001", "010", "001", "110"], "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "110", "001", "110"],
    "6": ["011", "100", "110", "101", "010"], "7": ["111", "001", "010", "010", "010"], "8": ["010", "101", "010", "101", "010"],
    "9": ["010", "101", "011", "001", "110"], " ": ["00", "00", "00", "00", "00"], "+": ["000", "010", "111", "010", "000"],
}


def text_rows(s, font=F5, gap=1):
    """A string as rows of '0'/'1' (font height rows), letters `gap` apart."""
    h = len(font["A"])
    rows = [""] * h
    for i, ch in enumerate(s.upper()):
        g = font.get(ch, font[" "])
        for r in range(h):
            rows[r] += g[r] + ("0" * gap if i < len(s) - 1 else "")
    return rows


def text_width(s, font=F5, scale=1, gap=1):
    return len(text_rows(s, font, gap)[0]) * scale


def draw_text(img, s, x, y, col, font=F5, scale=1, gap=1):
    px = img.load()
    W, H = img.size
    for r, row in enumerate(text_rows(s, font, gap)):
        for c, ch in enumerate(row):
            if ch == "1":
                for dx in range(scale):
                    for dy in range(scale):
                        X, Y = x + c * scale + dx, y + r * scale + dy
                        if 0 <= X < W and 0 <= Y < H:
                            px[X, Y] = col
    return x + text_width(s, font, scale, gap)


def centred(img, s, y, col, font=F5, scale=1, gap=1, x0=0, x1=None):
    x1 = img.size[0] if x1 is None else x1
    draw_text(img, s, x0 + (x1 - x0 - text_width(s, font, scale, gap)) // 2, y, col, font, scale, gap)


def rects(rows):
    """Greedy rectangles covering the '1's of a bitmap: (col, row, width, height)."""
    h, w = len(rows), max(len(r) for r in rows)
    used = [[False] * w for _ in range(h)]
    on = lambda r, c: c < len(rows[r]) and rows[r][c] == "1"
    out = []
    for r in range(h):
        for c in range(w):
            if used[r][c] or not on(r, c):
                continue
            c1 = c
            while c1 + 1 < w and on(r, c1 + 1) and not used[r][c1 + 1]:
                c1 += 1
            r1 = r
            while r1 + 1 < h and all(on(r1 + 1, x) and not used[r1 + 1][x] for x in range(c, c1 + 1)):
                r1 += 1
            for rr in range(r, r1 + 1):
                for cc in range(c, c1 + 1):
                    used[rr][cc] = True
            out.append((c, r, c1 - c + 1, r1 - r + 1))
    return out


def bitmap_boxes(rows, cx, ytop, cell, z1, z2, tex, glow=0, name="T", facing="north", faces=ALL):
    """Boxes for a bitmap seen from the north (facing north: text reads left to right for a viewer at -Z, so columns
    run from +X to -X) or from the south (facing south: columns run from -X to +X). cx is the bitmap's centre, ytop
    the top of its first row, cell the size of one bitmap pixel."""
    w = max(len(r) for r in rows) * cell
    els = []
    for k, (c, r, cw, rh) in enumerate(rects(rows)):
        y2 = ytop - r * cell
        y1 = y2 - rh * cell
        if facing == "north":
            x2 = cx + w / 2 - c * cell
            x1 = x2 - cw * cell
        else:
            x1 = cx - w / 2 + c * cell
            x2 = x1 + cw * cell
        els.append(bx(f"{name}{k}", (round(x1, 3), round(y1, 3), z1), (round(x2, 3), round(y2, 3), z2), tex, glow=glow, faces=faces))
    return els


def text_boxes(s, cx, ytop, cell, z1, z2, tex, glow=0, font=F5, gap=1, name="T", facing="north", faces=ALL):
    return bitmap_boxes(text_rows(s, font, gap), cx, ytop, cell, z1, z2, tex, glow, name, facing, faces)


# ======================================================================== A block type over variant groups

def variants_block(code, english, groups, build, rot=None, box=None, boxes=None, collide=True, data=None, comment=None,
                   names=None, creative=None, rot_offset=0, sel_boxes=None, material="Wood", sounds=WOOD):
    """A block type over every combination of `groups` [(group, states)]. build(v) returns the elements of a variant
    (v: group -> state), modelled unturned; the group named `rot` turns it (ROTATE[state]). `box` is the
    collision/selection box of the unturned model, a list of boxes, or `boxes(v)` per variant."""
    combos = list(itertools.product(*[states for _, states in groups])) if groups else [()]
    shapes, sel = {}, {}
    cache = {}
    for combo in combos:
        v = dict(zip([g for g, _ in groups], combo))
        key = tuple(s for (g, _), s in zip(groups, combo) if g != rot)
        if key not in cache:
            nm = code + ("-" + "-".join(key) if key else "")
            cache[key] = shape(nm, build(v))
        full = code + ("-" + "-".join(combo) if combo else "")
        angle = ((ROTATE[v[rot]] if rot else 0) + rot_offset) % 360
        shapes[full] = {"base": cache[key], "rotateY": angle} if angle else {"base": cache[key]}
        b = boxes(v) if boxes else box
        if b is not None:
            if isinstance(b[0], (list, tuple)):
                sel[full] = [cuboid(x, angle) for x in b]
            else:
                sel[full] = cuboid(b, angle)
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
                "lightAbsorption": 0, "resistance": 2, "sounds": sounds})
    if sel:
        many = any(isinstance(s, list) for s in sel.values())
        if len(set(json.dumps(s, sort_keys=True) for s in sel.values())) == 1:
            one = next(iter(sel.values()))
            out["selectionboxes" if many else "selectionbox"] = one
            if collide:
                out["collisionboxes" if many else "collisionbox"] = one
        else:
            out["selectionboxesByType" if many else "selectionboxByType"] = sel
            if collide:
                out["collisionboxesByType" if many else "collisionboxByType"] = sel
    if not collide:
        out["collisionbox"] = None
    if data:
        out.update(data)
    block(code, out, comment or english)
    if names:
        for pat, eng in names.items():
            LANG["block-" + pat] = eng
    LANG.setdefault(f"block-{code}-*" if groups else f"block-{code}", english)


def cube_block(code, english, kinds, comment, material="Stone", sounds=STONE, extra=None, group="kind", alternates=None,
               names=None):
    """Full cubes, one texture (key) per kind: kinds {state: key or {face: key}}."""
    tex = {}
    for k, t in kinds.items():
        full = f"{code}-{k}" if k else code
        if isinstance(t, dict):
            tex[full] = {f: {"base": tpath(v).replace("backrooms:", "")} for f, v in t.items()}
        else:
            entry = {"base": tpath(t).replace("backrooms:", "")}
            if alternates and k in alternates:
                entry["alternates"] = [{"base": tpath(a).replace("backrooms:", "")} for a in alternates[k]]
            tex[full] = {"all": entry}
    data = {"creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": material, "drawtype": "cube",
            "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds, "attributes": dict(FIXED)}
    if list(kinds) != [None]:
        data["variantgroups"] = [{"code": group, "states": list(kinds)}]
        data["texturesByType"] = tex
    else:
        data["textures"] = next(iter(tex.values()))
    if extra:
        data.update(extra)
    block(code, data, comment)
    COUNT["variants"] += len(kinds)
    if names:
        for pat, eng in names.items():
            LANG["block-" + pat] = eng
    LANG.setdefault(f"block-{code}-*" if list(kinds) != [None] else f"block-{code}", english)


# ======================================================================== Lang

STALE_LANG = {"item-creature-l3999-attendant-*", "entity-l3999-attendant-*", "creature-l3999-attendant-*",
              # (never read: the game names an entity by item-creature-, its kills by prefixandcreature-)
              "entity-l3999-attendant",
              # (the Level 10 door's arrival already says l3999-arrive-lobby; nothing finds a prize counter to point to)
              "l3999-revolving-in", "l3999-place-prizes"}


def merge_lang():
    """Updates the level's keys in lang/en.json in place; new keys go after the last of the level's keys already there
    (the first time, after "levelname-19"), so nothing else in the shared file moves."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    # Keys this generator wrote once and no longer writes (exact keys, never anyone else's)
    kept = []
    for line in lines:
        m = re.match(r'^\t"((?:[^"\\]|\\.)*)":', line)
        if m and json.loads('"' + m.group(1) + '"') in STALE_LANG:
            if not line.rstrip().endswith(",") and kept:
                kept[-1] = kept[-1].rstrip().rstrip(",")
            continue
        kept.append(line)
    lines = kept
    index = {}
    for i, line in enumerate(lines):
        m = re.match(r'^\t"((?:[^"\\]|\\.)*)":', line)
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
        anchor = max(mine) if mine else index["levelname-19"]
        trailing = lines[anchor].rstrip().endswith(",")
        if not trailing:
            lines[anchor] = lines[anchor].rstrip() + ","
        block_lines = [l + "," for l in new[:-1]] + [new[-1] + ("," if trailing else "")]
        lines[anchor + 1:anchor + 1] = block_lines
    out = "\n".join(lines)
    json.loads(re.sub(r"^\s*//.*$", "", out, flags=re.M))  # still valid
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print(f"lang: {len(LANG)} keys ({len(new)} new)")


# ======================================================================== Checks

def asset_exists(kind, path, ext):
    domain, rel = path.split(":", 1) if ":" in path else ("backrooms", path)
    if domain == "backrooms":
        return os.path.exists(os.path.join(ASSETS, kind, rel + ext))
    return any(os.path.exists(os.path.join(GAME, d, kind, rel + ext)) for d in ("survival", "game", "creative"))


_game_codes = {}


def game_codes(typ):
    """The first code segment of every vanilla block or item type."""
    if typ not in _game_codes:
        names = set()
        for d in ("survival", "game"):
            for root, _, files in os.walk(os.path.join(GAME, d, "blocktypes" if typ == "block" else "itemtypes")):
                for fn in files:
                    try:
                        raw = open(os.path.join(root, fn), encoding="utf-8").read()
                    except OSError:
                        continue
                    m = re.search(r'^\s*"?code"?\s*:\s*"([^"]+)"', raw, re.M)
                    if m:
                        names.add(m.group(1))
        _game_codes[typ] = names
    return _game_codes[typ]


def our_codes():
    ours = set()
    for kind in ("blocktypes", "itemtypes"):
        for root, _, files in os.walk(os.path.join(ASSETS, kind)):
            for fn in files:
                raw = open(os.path.join(root, fn), encoding="utf-8").read()
                m = re.search(r'^\s*"?code"?\s*:\s*"([^"]+)"', raw, re.M)
                if m:
                    ours.add(m.group(1))
    return ours


def code_known(typ, c, ours):
    dom, path = c.split(":", 1) if ":" in c else ("backrooms", c)
    if dom == "game":
        return any(path == g or path.startswith(g + "-") for g in game_codes(typ))
    return any(path == o or path.startswith(o + "-") for o in ours)


def check(extra_paths=()):
    """Every texture a shape names resolves; every shape, texture and sound a block, item or entity type names exists;
    every drop, dispensed item, prize and recipe ingredient is a known block or item of ours or of the game's."""
    problems = []
    for sp in SHAPES:
        p = os.path.join(ASSETS, "shapes", *sp.split("/")) + ".json"
        data = json.load(open(p, encoding="utf-8"))
        used = {f["texture"][1:] for e in _flat(data["elements"]) for f in e["faces"].values()}
        for k in used:
            if k not in data["textures"]:
                problems.append(f"shape {sp}: #{k} undefined")
        for k, t in data["textures"].items():
            if not asset_exists("textures", t, ".png"):
                problems.append(f"shape {sp}: texture {k} -> {t}")
    ours = our_codes()
    files = [("blocktypes", c) for c in CODES] + [("itemtypes", c) for c in ITEMS]
    for kind, code in files:
        raw = open(os.path.join(ASSETS, kind, "3999", code + ".json"), encoding="utf-8").read()
        data = json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
        problems += check_refs(f"{kind} {code}", data, ours)
    for p in extra_paths:
        raw = open(p, encoding="utf-8").read()
        data = json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
        problems += check_refs(os.path.relpath(p, ASSETS), data, ours)
    for name in RECIPES:
        raw = open(os.path.join(ASSETS, "recipes", "grid", name + ".json"), encoding="utf-8").read()
        data = json.loads(re.sub(r"^//.*$", "", raw, flags=re.M))
        for st in list(data["ingredients"].values()) + [data["output"]]:
            c = st["code"].replace("{colour}", "magenta")
            if "*" in c:
                c = c.split("*")[0].rstrip("-")
            if not code_known(st["type"], c, ours):
                problems.append(f"recipe {name}: {st['type']} {st['code']} unknown")
    for p in problems:
        print("CHECK:", p)
    print(f"check: {len(CODES)} block types, {len(SHAPES)} shapes, {len(ITEMS)} item types, {len(SOUNDS)} sounds, "
          f"{len(RECIPES)} recipes, {len(problems)} problems")
    return not problems


def sound_exists(rel):
    wild = rel.endswith("*")
    rel = rel.rstrip("*")
    folder = os.path.join(ASSETS, "sounds", *os.path.dirname(rel).split("/"))
    if os.path.exists(os.path.join(ASSETS, "sounds", *rel.split("/")) + ".ogg"):
        return True
    return wild and os.path.isdir(folder) and any(f.startswith(os.path.basename(rel)) for f in os.listdir(folder))


def check_refs(where, data, ours):
    problems = []
    text = json.dumps(data)
    for m in re.finditer(r'"base": "([^"]+)"', text):
        p = m.group(1)
        if not (asset_exists("shapes", p, ".json") or asset_exists("textures", p, ".png")):
            problems.append(f"{where}: {p} (no shape or texture)")
    for m in re.finditer(r'"(?:ambient|walk|place|break|hit|inside|idle|hurt|death)": "([^"]+)"', text):
        p = m.group(1)
        dom, rel = p.split(":", 1) if ":" in p else ("backrooms", p)
        if dom == "backrooms":
            if not sound_exists(rel):
                problems.append(f"{where}: sound {p}")
    for m in re.finditer(r'\{"type": "(item|block)", "code": "([^"]+)"', text):
        typ, c = m.groups()
        if not code_known(typ, c, ours):
            problems.append(f"{where}: {typ} {c} unknown")
    attrs = [data.get("attributes") or {}] + list((data.get("attributesByType") or {}).values())
    for a in attrs:
        for c in a.get("dispenses", []) + ([a["takes"]] if "takes" in a else []):
            if not code_known("item", c, ours):
                problems.append(f"{where}: dispenses or takes {c} unknown")
    return problems
