"""Stripped (looted) prop variants: the food props of Levels 1-5 as they look once wanderers have been through them.

Run on its own: python tools/gen_stripped.py     (re-runnable and deterministic; reads the original shapes and
blocktypes, writes only new files, and prints the lang lines, which are also in LANG here)

    metalshelf       -> metalshelfbare      (Level 1: the boxes gone, one flattened carton)
    oildrum          -> oildrumopen         (Level 2: lid, bung and vent gone, an open dark mouth)
    cardboardboxes   -> cardboardflat       (the stack flattened, one box left open)
    fridge           -> fridgeajar          (the door swung open, the inside bare)
    kitchencabinet   -> kitchencabinetbare  (doors open, bare inside)
    pantryshelf      -> pantryshelfbare     (picked clean, one tipped tin)

Each new blocktype is the original with its code, shapes and drops changed (and boxes, for the flat cardboard); the drops
are the original's non-food rows only.
"""
import copy
import json
import math
import os
import random
import re

from PIL import Image, ImageDraw, ImageEnhance

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
NL = "\n"

LANG = {
    "block-metalshelfbare-*": "Emptied Metal Shelving",
    "blockdesc-metalshelfbare-*": "Nothing left on it but a flattened carton. Whoever came through took what they could carry.",
    "block-oildrumopen": "Open Drum",
    "blockdesc-oildrumopen": "The lid is gone and the inside has dried to a dark ring. Nothing to drink here now.",
    "block-cardboardflat": "Flattened Cardboard",
    "blockdesc-cardboardflat": "Trodden flat and gone through. One box still stands, open and empty.",
    "block-fridgeajar-*": "Emptied Refrigerator",
    "blockdesc-fridgeajar-*": "The door hangs open on a bare, dry inside. Whatever it kept cold was eaten long ago.",
    "block-kitchencabinetbare-*": "Bare Kitchen Cupboard",
    "blockdesc-kitchencabinetbare-*": "Both doors hang open and nothing to eat is left on the shelf. What they could not eat, they left.",
    "block-pantryshelfbare-*": "Bare Pantry Shelf",
    "blockdesc-pantryshelfbare-*": "Picked clean of anything to eat. One empty tin rolled into the corner.",
}


# ---------------------------------------------------------------- reading and writing


def load_json(*rel):
    """The original's JSON: // comments (whole-line or trailing) stripped, then a tolerant loader (unquoted keys,
    trailing commas, single quotes)."""
    with open(os.path.join(ASSETS, *rel), encoding="utf-8") as f:
        text = f.read()
    try:
        import json5
        return json5.loads(text)
    except ImportError:
        pass
    out, i, n, in_str, q = [], 0, len(text), False, ""
    while i < n:  # strip comments outside strings
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\":
                out.append(text[i + 1])
                i += 1
            elif c == q:
                in_str = False
        elif c in "\"'":
            in_str, q = True, c
            out.append(c)
        elif text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif text.startswith("/*", i):
            i = text.index("*/", i) + 2
            continue
        else:
            out.append(c)
        i += 1
    text = "".join(out)
    text = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', text)  # unquoted keys
    text = re.sub(r",(\s*[}\]])", r"\1", text)  # trailing commas
    return json.loads(text)


def fit_uvs(elements, size=16):
    """A face UV past the texture's 16 units samples whatever lies beside it in the game's atlas (the client showed other
    blocks' textures on the fridge's tall faces): scale any such UV back into 0..16, keeping its aspect."""
    for e in elements:
        for face in e.get("faces", {}).values():
            uv = face.get("uv")
            if uv and (max(uv) > size + 0.001 or min(uv) < -0.001):
                lo = min(uv)
                k = size / max(1e-9, max(uv) - min(0, lo))
                face["uv"] = [round((v - min(0, lo)) * k, 4) for v in uv]
        fit_uvs(e.get("children", []), size)


def write_json(data, rel, comment):
    if isinstance(data, dict) and "elements" in data:
        fit_uvs(data["elements"], data.get("textureWidth", 16))
    path = os.path.join(ASSETS, *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False) + NL
    if comment:  # blocktypes only: shape files stay plain JSON (the preview tool reads them with json)
        text = "// " + comment + NL + text
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)
    print("wrote", "/".join(rel))


def save_png(img, rel):
    path = os.path.join(ASSETS, "textures", *rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote textures/" + "/".join(rel))


def r(v):
    return round(v + 0.0, 4)


# ---------------------------------------------------------------- shape helpers


def box(name, frm, to, tex, up=None, down=None, sides=None, rot=None, origin=None, faces=None):
    """A cuboid. tex: texture key used on every face; up, down, sides override the key on those faces (sides: one key or a
    {north, east, south, west} dict). faces: restrict to this list. rot: (rx, ry, rz) about origin (default the centre)."""
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    size = {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}
    out = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        if faces is not None and f not in faces:
            continue
        key = tex
        if f == "up" and up:
            key = up
        elif f == "down" and down:
            key = down
        elif f in ("north", "east", "south", "west") and sides:
            key = sides.get(f, tex) if isinstance(sides, dict) else sides
        if key is None:
            continue
        w, h = size[f]
        out[f] = {"texture": "#" + key, "uv": [0, 0, r(w), r(h)]}
    el = {"name": name, "from": [r(v) for v in frm], "to": [r(v) for v in to], "faces": out}
    if rot:
        rx, ry, rz = rot
        el["rotationOrigin"] = [r(v) for v in (origin or [(frm[i] + to[i]) / 2 for i in range(3)])]
        for k, v in (("rotationX", rx), ("rotationY", ry), ("rotationZ", rz)):
            if v:
                el[k] = v
    return el


def shape_file(textures, elements, base):
    d = {"textureWidth": 16, "textureHeight": 16, "textures": dict(textures), "elements": elements}
    for k in ("textureWidth", "textureHeight"):
        if k in base:
            d[k] = base[k]
    return d


def keep_only_used(shape):
    used = set()
    for e in shape["elements"]:
        for f in e["faces"].values():
            used.add(f["texture"][1:])
    shape["textures"] = {k: v for k, v in shape["textures"].items() if k in used}
    return shape


def keep_drops(drops, keep):
    out = [d for d in drops if d["code"] in keep]
    assert [d["code"] for d in out] == [k for k in keep], (out, keep)
    return out


def make_blocktype(orig, code, shape_rel, drops, comment, rel, boxes=None):
    """The original with its code, shape(s) and drops changed; `shape_rel` is the new base shape path (no extension)."""
    t = copy.deepcopy(orig)
    t["code"] = code
    old = None

    def swap(s):
        if isinstance(s, dict) and "base" in s:
            s["base"] = shape_rel
        return s
    if "shape" in t:
        swap(t["shape"])
    for k in ("shapeByType", "shapebytype"):
        for v in t.get(k, {}).values():
            swap(v)
    t["drops"] = drops
    for k, v in (boxes or {}).items():
        t[k] = v
    # the original's comments about what the thing holds do not travel (load strips them)
    write_json(t, rel, comment)


BY_SIDE = {"*-north": 0, "*-east": 270, "*-south": 180, "*-west": 90}


def boxes_by_side(b):
    """collision/selection box (x1..z2) as the original's four ByType entries."""
    out = {}
    for k, ry in BY_SIDE.items():
        e = dict(b)
        if ry:
            e["rotateY"] = ry
        out[k] = e
    return out


# ---------------------------------------------------------------- textures


def tex_path(rel):
    return os.path.join(ASSETS, "textures", *rel.split("/")) + ".png"


def opentop_texture():
    """oildrum-opentop: the drum's mouth seen from above, in oildrum-top's palette: the rolled rim ring (lighter, with
    its rust), the inside dark, with a dried tide-mark ring and residue. 32 x 32 like oildrum-top (16 shape units)."""
    S = 32
    rng = random.Random(7120)
    src = Image.open(tex_path("block/level2/oildrum-top")).convert("RGBA")
    base = src.resize((1, 1), Image.BOX).getpixel((0, 0))[:3]
    img = src.copy()
    px = img.load()
    c = (S - 1) / 2
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - c, y - c)
            if d > 12.4:
                continue  # the corners outside the lid keep oildrum-top's own
            if d > 10.6:  # the rolled rim: lit on one side
                lit = 1.0 + 0.22 * ((x - y) / S) + rng.uniform(-0.04, 0.04)
                px[x, y] = tuple(min(255, int(v * 1.12 * lit)) for v in base) + (255,)
            elif d > 9.6:  # the lip's shadow line
                px[x, y] = (14, 22, 34, 255)
            else:  # the inside: nearly black, a blue cast
                k = rng.uniform(0.85, 1.15)
                v = (16 * k, 20 * k, 26 * k)
                if 6.6 < d < 8.0:  # the dried tide-mark: a brown-grey ring where the water stood
                    t = 1 - abs(d - 7.3) / 0.9
                    v = tuple(a + (b - a) * (0.35 + 0.35 * t) for a, b in zip(v, (74, 62, 46)))
                px[x, y] = tuple(int(q) for q in v) + (255,)
    for _ in range(26):  # residue: crusted flecks and a few rust runs
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 8.8)
        x, y = int(c + d * math.cos(a)), int(c + d * math.sin(a))
        px[x, y] = rng.choice([(58, 48, 38, 255), (84, 52, 32, 255), (38, 36, 34, 255), (96, 70, 44, 255)])
    for _ in range(5):  # rust at the rim
        a = rng.uniform(0, 2 * math.pi)
        x, y = int(c + 11.2 * math.cos(a)), int(c + 11.2 * math.sin(a))
        px[x, y] = (128, 64, 32, 255)
    return img


def cabinet_inside_texture():
    """The cupboard's inside: dresserwood a little darker, with a grain of dust."""
    img = Image.open(tex_path("block/detail/dresserwood")).convert("RGB")
    img = ImageEnhance.Brightness(img).enhance(0.78)
    rng = random.Random(7121)
    px = img.load()
    for _ in range(40):
        x, y = rng.randrange(img.width), rng.randrange(img.height)
        px[x, y] = tuple(min(255, v + 10) for v in px[x, y])
    return img.convert("RGBA")


# ---------------------------------------------------------------- the six shapes


def metalshelf(base):
    els = [e for e in base["elements"] if not e["name"].startswith("Box")]
    tex = dict(base["textures"])
    tex.update({"tornin": "backrooms:block/supplybox-torn-inside", "tornside": "backrooms:block/supplybox-torn-side",
                "tape": "backrooms:block/supplybox-top"})
    low = 1.6
    els += [  # one carton, split along its seams and trodden flat, on the lower shelf
        box("FlatCarton", (3, low, 4), (11.5, low + 0.3, 12), "tornside", up="tornin", rot=(0, 14, 0)),
        box("FlatFlap", (8, low + 0.3, 7), (14, low + 0.55, 12.5), "tornside", up="tornin", rot=(0, -23, 0)),
        box("TapeScrap", (4, low + 0.3, 9), (7, low + 0.4, 9.8), "tape", rot=(0, 31, 0)),
    ]
    els.append(box("TornBit", (4, 8.6, 9), (8.5, 8.85, 13), "tornside", up="tornin", rot=(0, -17, 0)))
    return keep_only_used(shape_file(tex, els, base))


def oildrum(base):
    keep = ("Wall", "Hoop", "ChimeLo", "ChimeHi", "Label", "Lid")
    els = [e for e in base["elements"] if e["name"].startswith(keep)]
    tex = dict(base["textures"])
    tex["opentop"] = "backrooms:block/level2/oildrum-opentop"
    sink = 2.2  # the lid sits this far down: the open mouth under the chime
    for e in els:
        if e["name"].startswith("Lid"):
            e["from"][1] = r(e["from"][1] - sink)
            e["to"][1] = r(e["to"][1] - sink)
            e["faces"] = {"up": {"texture": "#opentop", "uv": e["faces"]["up"]["uv"]}}
    # the inside of the wall, lit dark: inward faces from the floor to the mouth
    inner = []
    for e in els:
        if e["name"].startswith("Wall"):
            i = copy.deepcopy(e)
            i["name"] = "In" + e["name"]
            (x1, _, z1), (x2, _, z2) = e["from"], e["to"]
            y1 = r(13.5 - sink - 0.5)
            # each wall panel is thin along x or z: a sliver just inside it, its face turned inward
            if z2 - z1 < 0.1:
                face, (z1, z2) = ("south", (z2, z2 + 0.01)) if z1 < 8 else ("north", (z1 - 0.01, z1))
            else:
                face, (x1, x2) = ("east", (x2, x2 + 0.01)) if x1 < 8 else ("west", (x1 - 0.01, x1))
            i["from"] = [r(x1), y1, r(z1)]
            i["to"] = [r(x2), 13.5, r(z2)]
            i["faces"] = {face: {"texture": "#opentop", "uv": [6, 6, 10, 9]}}
            inner.append(i)
    els = els + inner
    return keep_only_used(shape_file(tex, els, base))


def cardboard(base):
    tex = dict(base["textures"])
    tex.update({"tornin": "backrooms:block/supplybox-torn-inside", "tornside": "backrooms:block/supplybox-torn-side"})
    els = [
        box("SheetA", (0.8, 0, 1.2), (9.2, 0.35, 8.6), "cardboard", up="cardboardtop", rot=(0, 11, 0)),
        box("SheetB", (3.5, 0.35, 5), (11.5, 0.65, 11.5), "cardboard", up="cardboardtop", rot=(0, -24, 0)),
        box("SheetC", (1, 0, 10.2), (8.5, 0.3, 15), "cardboard", up="cardboardtop", rot=(0, 33, 0)),
    ]
    # the box left standing: four thin walls, the inside of each torn-inside, flaps out
    x1, x2, z1, z2, h, t = 9.4, 14.8, 7.0, 13.2, 5.2, 0.4
    els += [
        box("BoxBottom", (x1, 0.01, z1), (x2, 0.4, z2), "tornin", sides="tornside", down="tornside"),
        box("WallN", (x1, 0.4, z1), (x2, h, z1 + t), "tornside", sides={"north": "tornside", "south": "tornin", "east": "tornside", "west": "tornside"}),
        box("WallS", (x1, 0.4, z2 - t), (x2, h, z2), "tornside", sides={"north": "tornin", "south": "tornside", "east": "tornside", "west": "tornside"}),
        box("WallW", (x1, 0.4, z1 + t), (x1 + t, h, z2 - t), "tornside", sides={"east": "tornin", "west": "tornside", "north": "tornside", "south": "tornside"}),
        box("WallE", (x2 - t, 0.4, z1 + t), (x2, h, z2 - t), "tornside", sides={"west": "tornin", "east": "tornside", "north": "tornside", "south": "tornside"}),
    ]
    # flaps hinged on the rim, folded out and down (the sign of the turn is checked in the preview)
    fl = 0.25
    els += [
        box("FlapN", (x1, h, z1 - 3.4), (x2, h + fl, z1), "tornin", sides="tornside", rot=(-38, 0, 0), origin=[0, h, z1]),
        box("FlapS", (x1, h, z2), (x2, h + fl, z2 + 3.4), "tornin", sides="tornside", rot=(38, 0, 0), origin=[0, h, z2]),
        box("FlapW", (x1 - 3.2, h, z1 + 1), (x1, h + fl, z2 - 1), "tornin", sides="tornside", rot=(0, 0, 52), origin=[x1, h, 0]),
    ]
    return keep_only_used(shape_file(tex, els, base))


def fridge(base):
    tex = dict(base["textures"])
    tex["inside"] = "backrooms:block/detail/fridgeinside"
    W, I, ST, SD = "fridgewhite", "inside", "steel", "steeldark"
    els = [
        box("Bottom", (1, 0, 3), (15, 1.2, 15), W, up=I),
        box("Top", (1, 28.8, 3), (15, 30, 15), W, down=I),
        box("Back", (1, 1.2, 14), (15, 28.8, 15), W, sides={"south": W, "north": I}),
        box("SideW", (1, 1.2, 3), (2.2, 28.8, 14), W, sides={"east": I, "west": W, "north": W, "south": W}),
        box("SideE", (12.8, 1.2, 3), (15, 28.8, 14), W, sides={"west": I, "east": W, "north": W, "south": W}),
        box("ShelfLow", (2.2, 9.5, 3.6), (12.8, 10, 13.8), ST, sides=SD),
        box("ShelfHigh", (2.2, 19, 3.6), (12.8, 19.5, 13.8), ST, sides=SD),
        box("ShelfTop", (2.2, 25, 3.6), (12.8, 25.4, 13.8), ST, sides=SD),
        box("Stain", (4, 1.2, 6), (9.5, 1.25, 11.5), SD, faces=["up"]),
    ]
    els[-1]["faces"]["up"]["uv"] = [0, 0, 2, 2]
    # the door, hinged on its left edge (west, x 1) as the shape faces north: the handles are at x 12-13, the free side
    ang = 68
    org = [1, 0, 3]
    door = [
        box("Door", (1, 0, 2.2), (15, 30, 3.2), W, sides={"south": W, "north": W}, rot=(0, ang, 0), origin=org),
        box("DoorLiner", (2.2, 1.2, 3.2), (13.8, 28.8, 3.5), I, faces=["south", "up", "down", "east", "west"], rot=(0, ang, 0), origin=org),
        box("DoorSeam", (1, 18, 1.9), (15, 18.5, 2.2), SD, rot=(0, ang, 0), origin=org),
        box("DoorHandle1", (12, 20, 1.5), (13, 27, 2.2), ST, rot=(0, ang, 0), origin=org),
        box("DoorHandle2", (12, 9, 1.5), (13, 16, 2.2), ST, rot=(0, ang, 0), origin=org),
        box("DoorBinLow", (3, 8, 3.5), (13, 8.5, 4.6), ST, sides=SD, rot=(0, ang, 0), origin=org),
        box("DoorBinHigh", (3, 17, 3.5), (13, 17.5, 4.6), ST, sides=SD, rot=(0, ang, 0), origin=org),
    ]
    return keep_only_used(shape_file(tex, els + door, base))


def kitchencabinet(base):
    tex = dict(base["textures"])
    tex["inside"] = "backrooms:block/detail/cabinetbare-inside"
    D, IN = "dresserwood", "inside"
    els = [
        box("Floor", (0, 0, 3), (16, 1, 16), D, up=IN),
        box("Back", (1, 1, 15), (15, 14, 16), D, sides={"north": IN, "south": D, "east": IN, "west": IN}),
        box("SideW", (0, 1, 3), (1, 14, 16), D, sides={"east": IN, "west": D, "north": D, "south": D}),
        box("SideE", (15, 1, 3), (16, 14, 16), D, sides={"west": IN, "east": D, "north": D, "south": D}),
        box("Shelf", (1, 7, 3.6), (15, 7.6, 15), IN),
        box("Top", (0, 14, 2), (16, 15, 16), "formica"),
    ]
    # two doors: cabinetfront's door half each, hanging open (the right one further, its lower hinge gone)
    cf = "cabinetfront"
    t = 0.8
    left = box("DoorL", (0, 0, 3 - t), (8, 14, 3), cf, sides=D, faces=["north", "south", "up", "east", "west"], rot=(0, 82, 0), origin=[0, 0, 3])
    left["faces"]["north"]["uv"] = [0, 0, 8, 14]
    left["faces"]["south"] = {"texture": "#" + IN, "uv": [0, 0, 8, 14]}
    right = box("DoorR", (8, 0, 3 - t), (16, 14, 3), cf, sides=D, faces=["north", "south", "up", "east", "west"], rot=(0, -104, 0), origin=[16, 0, 3])
    right["faces"]["north"]["uv"] = [8, 0, 16, 14]
    right["faces"]["south"] = {"texture": "#" + IN, "uv": [8, 0, 16, 14]}
    right["rotationZ"] = 0
    return keep_only_used(shape_file(tex, els + [left, right], base))


def pantryshelf(base):
    gone = ("Sack", "BigTin", "Jar", "Oil", "Can", "Carton", "Tin", "Tea")
    els = [e for e in base["elements"] if not e["name"].startswith(gone)]
    tex = dict(base["textures"])
    top = 3.2  # the lowest board's top
    els += [
        box("TippedTin", (3.2, top, 9.6), (7.4, top + 2.4, 12), "l11a-tintomato", faces=["north", "south", "up", "down"], rot=(0, 23, 0)),
        box("TippedTinEnd", (7.4, top + 0.2, 9.9), (7.5, top + 2.2, 11.7), "l11a-tinlid", faces=["east"], rot=(0, 23, 0), origin=[5.3, top, 10.8]),
        box("TinLid", (9.8, top, 10.6), (11.6, top + 0.1, 12.4), "l11a-tinlid", faces=["up"]),
    ]
    els[-3]["faces"] = {"north": {"texture": "#l11a-tintomato", "uv": [0, 0, 4.2, 2.4]},
                        "south": {"texture": "#l11a-tintomato", "uv": [0, 0, 4.2, 2.4]},
                        "up": {"texture": "#l11a-tintomato", "uv": [0, 0, 4.2, 2.4]},
                        "down": {"texture": "#l11a-tintomato", "uv": [0, 0, 4.2, 2.4]}}
    els[-2]["from"], els[-2]["to"] = [r(7.4), r(top + 0.0), 9.6], [r(7.45), r(top + 2.4), 12]
    return keep_only_used(shape_file(tex, els, base))


# ---------------------------------------------------------------- run


def main():
    save_png(opentop_texture(), ("block", "level2", "oildrum-opentop.png"))
    save_png(cabinet_inside_texture(), ("block", "detail", "cabinetbare-inside.png"))

    # (original blocktype path, original shape path, new code, build, keep drops, blocktype rel dir, shape rel, what)
    jobs = [
        (("blocktypes", "level1", "metalshelf.json"), "shapes/block/metalshelf.json", "metalshelfbare", metalshelf,
         ["game:flaxtwine", "game:candle", "metalbracket"], ("blocktypes", "level1"), ("shapes", "block"),
         "block/metalshelfbare", "Metal shelving after the boxes have been taken: one flattened carton left."),
        (("blocktypes", "level2", "oildrum.json"), "shapes/block/oildrum.json", "oildrumopen", oildrum,
         [], ("blocktypes", "level2"), ("shapes", "block"), "block/oildrumopen", "An oil drum with its lid off and nothing inside."),
        (("blocktypes", "detail", "cardboardboxes.json"), "shapes/block/detail/cardboardboxes.json", "cardboardflat", cardboard,
         ["game:paper-parchment", "game:candle", "game:drygrass"], ("blocktypes", "detail"), ("shapes", "block", "detail"),
         "block/detail/cardboardflat", "The cardboard boxes trodden flat and gone through, one box left open and empty."),
        (("blocktypes", "detail", "fridge.json"), "shapes/block/detail/fridge.json", "fridgeajar", fridge,
         ["metalbracket", "scrapwire"], ("blocktypes", "detail"), ("shapes", "block", "detail"),
         "block/detail/fridgeajar", "The refrigerator with its door open and the inside bare."),
        (("blocktypes", "detail", "kitchencabinet.json"), "shapes/block/detail/kitchencabinet.json", "kitchencabinetbare", kitchencabinet,
         ["game:salt", "game:knife-generic-copper", "game:fat", "game:candle", "seedpacket-onion"], ("blocktypes", "detail"),
         ("shapes", "block", "detail"), "block/detail/kitchencabinetbare", "The kitchen cupboard with its doors open and nothing on the shelf."),
        (("blocktypes", "detail", "pantryshelf.json"), "shapes/block/detail/pantryshelf.json", "pantryshelfbare", pantryshelf,
         ["game:salt"], ("blocktypes", "detail"), ("shapes", "block", "detail"), "block/detail/pantryshelfbare",
         "The pantry shelf picked clean, one empty tin left."),
    ]
    for bt_path, shape_path, code, build, keep, bt_dir, shape_dir, shape_rel, what in jobs:
        orig = load_json(*bt_path)
        base = load_json(*shape_path.split("/"))
        shape = build(base)
        write_json(shape, shape_dir + (shape_rel.split("/")[-1] + ".json",), None)
        drops = keep_drops(orig["drops"], keep) if keep else []
        boxes = None
        if code == "cardboardflat":
            b = {"x1": 0.06, "y1": 0, "z1": 0.06, "x2": 0.94, "y2": 0.4, "z2": 0.94}
            boxes = {"collisionbox": b, "selectionbox": dict(b)}
        make_blocktype(orig, code, shape_rel, drops, "Generated by tools/gen_stripped.py. " + what,
                       bt_dir + (code + ".json",), boxes)
    print()
    for k, v in LANG.items():
        print('\t"%s": %s,' % (k, json.dumps(v)))


if __name__ == "__main__":
    main()
