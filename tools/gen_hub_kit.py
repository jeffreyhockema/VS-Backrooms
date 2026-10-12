"""Shared kit and textures for tools/gen_hub.py (The Hub's assets): file writers, boxes with aligned UVs, the relief
carver, every block texture, and the tunnel blocks. See gen_hub.py for the conventions.
"""
import json
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

import gen_textures as T  # noqa: E402
import texlib  # noqa: E402
import gen_hub_sigils as SIG  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
S = 32
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}
DIRS = ("north", "east", "south", "west", "up", "down")
FRONT = ("north", "east", "west", "up", "down")  # everything but the back

STONE = {"walk": "game:walk/stone", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
GLASS = {"walk": "game:walk/stone", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}

LANG = {}
COUNTS = {"textures": 0, "shapes": 0, "blocktypes": 0, "variants": 0}


def seed_of(name):
    import zlib
    return zlib.crc32(name.encode()) & 0xFFFF


# ======================= Files =======================

def write_json(path, data, comment=None, compact=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, separators=(",", ":")) if compact else json.dumps(data, indent="\t")
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def save_tex(img, name, folder="block"):
    path = os.path.join(ASSETS, "textures", folder, "hub", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    COUNTS["textures"] += 1


def tpath(key):
    """A texture key in a shape: a bare name is ours (block/hub/<name>); anything with a slash is a full path."""
    if ":" in key:
        return key
    if "/" in key:
        return "backrooms:" + key
    return "backrooms:block/hub/" + key


def shape(name, elements, folder="block", width=16, height=16):
    keys = {}
    for e in elements:
        for face in e["faces"].values():
            k = face["texture"][1:]
            keys[k] = tpath(k.replace("~", "/"))
    data = {"textureWidth": width, "textureHeight": height, "textures": dict(sorted(keys.items())), "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", folder, "hub", name + ".json"), data, compact=len(elements) > 40)
    COUNTS["shapes"] += 1
    return f"{folder}/hub/{name}"


def block(code, data, comment=None):
    data = dict({"code": code}, **data)
    write_json(os.path.join(ASSETS, "blocktypes", "hub", code + ".json"), data, comment)
    COUNTS["blocktypes"] += 1
    n = 1
    for g in data.get("variantgroups", []):
        n *= len(g["states"])
    COUNTS["variants"] += n


def name(pattern, english):
    LANG["block-" + pattern] = english


def cuboid(box, side=None):
    x1, y1, z1, x2, y2, z2 = box
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if side and ROTATE[side]:
        c["rotateY"] = ROTATE[side]
    return c


def boxes_by_side(box):
    return {f"*-{s}": cuboid(box, s) for s in SIDES}


# ======================= Boxes =======================

def _wrap(a, b):
    """Shifts a UV span into 0..16 (spans longer than a block are clamped)."""
    lo, hi = min(a, b), max(a, b)
    k = math.floor(lo / 16) if hi - lo <= 16 else 0
    lo, hi = lo - 16 * k, hi - 16 * k
    if hi > 16.0001:
        lo, hi = max(0, lo), min(16, hi)
        if hi - lo < 0.01:
            lo, hi = 0, max(0.5, b - a)
    return (lo, hi) if a <= b else (hi, lo)


def bx(nm, frm, to, tex, faces=DIRS, glow=0, uv=None, full=False, aligned=True, rot=None, origin=None, uvs=None):
    """A box. By default every face takes the part of the texture that lies under it in the block (`aligned`), so
    textures run on across boxes and blocks; `full` stretches the whole texture over each face (pictures, signs);
    `uv` gives one explicitly; `uvs` maps face -> uv. `rot` is (x, y, z) degrees about `origin` (default centre)."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    w, h, d = abs(x2 - x1), abs(y2 - y1), abs(z2 - z1)
    out = {}
    for f in faces:
        if uvs and f in uvs:
            fuv = list(uvs[f])
        elif uv is not None:
            fuv = list(uv)
        elif full:
            fuv = [0, 0, 16, 16]
        elif aligned:
            span = {"north": ((16 - x2, 16 - x1), (16 - y2, 16 - y1)), "south": ((x1, x2), (16 - y2, 16 - y1)),
                    "east": ((16 - z2, 16 - z1), (16 - y2, 16 - y1)), "west": ((z1, z2), (16 - y2, 16 - y1)),
                    "up": ((x1, x2), (z1, z2)), "down": ((x1, x2), (16 - z2, 16 - z1))}[f]
            (u1, u2), (v1, v2) = _wrap(*span[0]), _wrap(*span[1])
            fuv = [round(u1, 3), round(v1, 3), round(u2, 3), round(v2, 3)]
        else:
            a, b = {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[f]
            fuv = [0, 0, min(16, max(a, 0.5)), min(16, max(b, 0.5))]
        face = {"texture": "#" + tex, "uv": fuv}
        if glow:
            face["glow"] = glow
        out[f] = face
    el = {"name": nm, "from": [round(v, 4) for v in (x1, y1, z1)], "to": [round(v, 4) for v in (x2, y2, z2)], "faces": out}
    if rot:
        el["rotationOrigin"] = list(origin) if origin else [(x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2]
        for i, k in enumerate(("rotationX", "rotationY", "rotationZ")):
            if rot[i]:
                el[k] = rot[i]
    return el


def cube(tex, faces=DIRS):
    return bx("Block", (0, 0, 0), (16, 16, 16), tex, faces=faces)


def mirror_x(els):
    """Mirrors boxes left to right (x -> 16 - x)."""
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [16 - x2, y1, z1], [16 - x1, y2, z2]
        f = e["faces"]
        east, west = f.pop("east", None), f.pop("west", None)
        if west:
            f["east"] = west
        if east:
            f["west"] = east
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [16 - o[0], o[1], o[2]]
            if "rotationY" in e:
                e["rotationY"] = -e["rotationY"]
            if "rotationZ" in e:
                e["rotationZ"] = -e["rotationZ"]
        out.append(e)
    return out


def shift(els, dx=0, dy=0, dz=0):
    out = []
    for e in els:
        e = json.loads(json.dumps(e))
        e["from"] = [e["from"][0] + dx, e["from"][1] + dy, e["from"][2] + dz]
        e["to"] = [e["to"][0] + dx, e["to"][1] + dy, e["to"][2] + dz]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [o[0] + dx, o[1] + dy, o[2] + dz]
        out.append(e)
    return out


def turn(el, times):
    """Rotates an unrotated box 90 degrees clockwise (seen from above) around the block centre."""
    el = json.loads(json.dumps(el))
    for _ in range(times % 4):
        (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]
        el["from"], el["to"] = [16 - z2, y1, x1], [16 - z1, y2, x2]
        f = el["faces"]
        el["faces"] = {k: v for k, v in {"east": f.get("north"), "south": f.get("east"), "west": f.get("south"),
                                          "north": f.get("west"), "up": f.get("up"), "down": f.get("down")}.items() if v is not None}
    return el


def relief(depths, tex_of, cell=0.5, back=True, back_tex=None, name_="R"):
    """A carved face from a height map. `depths[row][col]` is how far each cell of the north face lies behind the
    wall plane (row 0 at the top, `cell` units square, the grid covering the whole 16 x 16 face). The deepest level
    is one back slab reaching to the back of the block; every shallower cell becomes part of a box standing proud of
    it, merged into rectangles. `tex_of(depth)` names the texture for a level."""
    rows, cols = len(depths), len(depths[0])
    deepest = max(max(r) for r in depths)
    els = []
    if back:
        els.append(bx(name_ + "Back", (0, 0, deepest), (16, 16, 16), back_tex or tex_of(deepest), faces=DIRS))
        els[-1]["faces"]["north"]["texture"] = "#" + tex_of(deepest)
    used = [[False] * cols for _ in range(rows)]
    k = 0
    for r in range(rows):
        for c in range(cols):
            d = depths[r][c]
            if used[r][c] or d >= deepest:
                continue
            c2 = c
            while c2 + 1 < cols and not used[r][c2 + 1] and depths[r][c2 + 1] == d:
                c2 += 1
            r2 = r
            while r2 + 1 < rows and all(not used[r2 + 1][x] and depths[r2 + 1][x] == d for x in range(c, c2 + 1)):
                r2 += 1
            for y in range(r, r2 + 1):
                for x in range(c, c2 + 1):
                    used[y][x] = True
            # Column c runs from x = 16 (the viewer's left) toward x = 0, as the north face is seen from the north
            x1, x2 = 16 - (c2 + 1) * cell, 16 - c * cell
            y1, y2 = 16 - (r2 + 1) * cell, 16 - r * cell
            els.append(bx(f"{name_}{k}", (x1, y1, d), (x2, y2, deepest), tex_of(d), faces=FRONT))
            k += 1
    return els


# ======================= Textures =======================

def rgb(h, a=255):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255, a)


def noise(color, n, key, size=S):
    c = color if isinstance(color, tuple) else rgb(color)[:3]
    return T.noise_fill(c[:3], n, seed_of(key), size)


def speckle(img, key, count, colors, size=1):
    rng = random.Random(seed_of(key))
    px = img.load()
    w, h = img.size
    for _ in range(count):
        x, y = rng.randrange(w), rng.randrange(h)
        c = rng.choice(colors)
        for dy in range(size):
            for dx in range(size):
                px[(x + dx) % w, (y + dy) % h] = c if len(c) == 4 else c + (255,)
    return img


def tint(img, f, add=0):
    px = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            r, g, b, a = px[x, y]
            px[x, y] = (T.clamp(r * f + add), T.clamp(g * f + add), T.clamp(b * f + add), a)
    return img


def concrete(base, key, grain=True, holes=True, n=5):
    """Cast concrete: fine noise, the faint grain of formwork boards (horizontal), a few bug holes."""
    img = noise(base, n, key)
    px = img.load()
    rng = random.Random(seed_of(key + "g"))
    if grain:
        for y in range(S):
            f = 1 + 0.025 * math.sin(y * 1.7 + rng.random()) + (0.02 if y % 8 == 0 else 0)
            for x in range(S):
                r, g, b, a = px[x, y]
                px[x, y] = (T.clamp(r * f), T.clamp(g * f), T.clamp(b * f), a)
    texlib_m = texlib._periodic_noise(seed_of(key + "m"), 2)
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            m = 1 + 0.05 * texlib_m[y][x]
            px[x, y] = (T.clamp(r * m), T.clamp(g * m), T.clamp(b * m), a)
    if holes:
        for _ in range(5):
            x, y = rng.randrange(S), rng.randrange(S)
            px[x, y] = tuple(T.clamp(v * 0.62) for v in px[x, y][:3]) + (255,)
    return img


SEAM, SEAMHI = (0x5E, 0x5C, 0x57, 255), (0xA4, 0xA1, 0x9A, 255)


def wall_textures():
    base = 0x8E8B84
    for seam in ("plain", "left", "bottom", "corner"):
        img = concrete(base, "hubwall-" + seam)
        d = ImageDraw.Draw(img)
        if seam in ("left", "corner"):
            d.line([0, 0, 0, S - 1], fill=SEAM)
            d.line([1, 0, 1, S - 1], fill=SEAMHI)
        if seam in ("bottom", "corner"):
            d.line([0, S - 1, S - 1, S - 1], fill=SEAM)
            d.line([0, S - 2, S - 1, S - 2], fill=tuple(T.clamp(v * 0.85) for v in SEAM[:3]) + (255,))
        save_tex(img, "wall-" + seam)
    # The wall that isn't there: like a plain panel, but its seams sit 3 px off, so they meet nothing
    img = concrete(base, "hubwall-false")
    d = ImageDraw.Draw(img)
    d.line([3, 0, 3, S - 1], fill=SEAM)
    d.line([4, 0, 4, S - 1], fill=SEAMHI)
    d.line([0, S - 4, S - 1, S - 4], fill=SEAM)
    d.line([0, S - 5, S - 1, S - 5], fill=SEAMHI)
    save_tex(img, "wall-false")
    # Ceiling: darker, the board lines of the formwork it was cast against
    img = concrete(0x77746E, "hubceiling", grain=False)
    d = ImageDraw.Draw(img)
    for y in (0, 16):
        d.line([0, y, S - 1, y], fill=rgb(0x6E6B65))
    save_tex(img, "ceiling")
    # Tiles creeping in where a tunnel turns toward Level 37
    for stage, share in ((1, 0.22), (2, 0.8)):
        img = concrete(base, f"tilecrumb{stage}")
        px = img.load()
        rng = random.Random(seed_of(f"tc{stage}"))
        for ty in range(8):
            for tx in range(8):
                if rng.random() < share:
                    f = rng.uniform(0.985, 1.01)
                    for y in range(ty * 4 + 1, ty * 4 + 4):
                        for x in range(tx * 4 + 1, tx * 4 + 4):
                            c = 244 * f + rng.uniform(-2, 2)
                            px[x, y] = (T.clamp(c), T.clamp(c), T.clamp(c * 0.975), 255)
                    for x in range(tx * 4, tx * 4 + 4):
                        px[x, ty * 4] = (198, 194, 184, 255)
                    for y in range(ty * 4, ty * 4 + 4):
                        px[tx * 4, y] = (198, 194, 184, 255)
        save_tex(img, f"tilecrumb-{stage}")


def road_textures():
    def asphalt(key, base=(0x2E, 0x2D, 0x2C)):
        img = noise(base, 4, key)
        speckle(img, key + "s", 70, [(0x5A, 0x58, 0x55), (0x6E, 0x6B, 0x66), (0x44, 0x42, 0x40), (0x23, 0x22, 0x21)])
        return img
    save_tex(asphalt("asphalt"), "asphalt-plain")
    img = asphalt("asphaltworn")
    px = img.load()
    for y in range(S):
        f = 1.18 + 0.06 * math.sin(y * 0.4)
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (T.clamp(r * f + 4), T.clamp(g * f + 4), T.clamp(b * f + 4), a)
    save_tex(img, "asphalt-worn")
    img = asphalt("asphaltpatch")
    d = ImageDraw.Draw(img)
    d.rectangle([5, 7, 25, 23], fill=(0x1E, 0x1D, 0x1D, 255))
    speckle(img, "patchspeck", 10, [(0x33, 0x32, 0x31)])
    d.rectangle([5, 7, 25, 23], outline=(0x17, 0x16, 0x16, 255))
    save_tex(img, "asphalt-patch")
    # The hole's broken rim: asphalt crumbling into black
    img = asphalt("holeedge")
    px = img.load()
    rng = random.Random(seed_of("holeedge"))
    for x in range(S):
        depth = 4 + int(3 * math.sin(x * 0.7) + rng.uniform(0, 3))
        for y in range(S - depth, S):
            px[x, y] = (8, 8, 9, 255)
    save_tex(img, "holeedge")
    save_tex(noise((5, 5, 6), 1, "void"), "void")
    # Road stud: yellow glazed ceramic, and its little reflector
    img = noise(0xE8B92A, 6, "stud")
    d = ImageDraw.Draw(img)
    d.line([0, 2, S, 2], fill=rgb(0xF6D468))
    save_tex(img, "stud")
    img = Image.new("RGBA", (S, S), rgb(0xD8C070))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x + 2, S], fill=rgb(0xFFF2B0))
    save_tex(img, "studreflector")
    # Sidewalk: pale concrete, a joint at each block edge; the kerb's face below
    img = concrete(0xB5B0A6, "sidewalk", grain=False)
    d = ImageDraw.Draw(img)
    d.line([0, 0, S - 1, 0], fill=rgb(0x8C877E))
    d.line([0, 0, 0, S - 1], fill=rgb(0x8C877E))
    save_tex(img, "sidewalk")
    img = concrete(0xA8A398, "kerb", grain=False)
    d = ImageDraw.Draw(img)
    d.line([0, 0, S - 1, 0], fill=rgb(0xC4BFB4))
    T.blotch(img, (16, S - 2), 9, (70, 66, 60), 0.35, seed_of("kerbgrime"))
    save_tex(img, "kerb")


def fixture_textures():
    # Caged sodium lamp: amber glass, brightest at its heart; dead, it is a dull brown bottle
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = ((x - 15.5) ** 2 + (y - 15.5) ** 2) ** 0.5 / 22
            px[x, y] = (255, T.clamp(214 - 70 * d), T.clamp(120 - 90 * d), 255)
    save_tex(img, "lampglass")
    save_tex(noise(0x5A4630, 4, "lampdead"), "lampglass-dead")
    save_tex(noise(0x3D4A3F, 4, "lamphousing"), "lamphousing")
    # The inside of a lit lamp's hood, washed amber by the glass under it
    img = noise(0xC8782C, 4, "lamphoodlit")
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0x5A3A1C), width=2)
    save_tex(img, "lamphood-lit")
    save_tex(noise(0x7A7F7C, 3, "cage"), "cage")
    # Galvanised steel: the spangle of zinc crystals
    img = noise(0xA7ACAE, 3, "galv")
    rng = random.Random(seed_of("spangle"))
    d = ImageDraw.Draw(img)
    for _ in range(14):
        x, y, r = rng.randrange(S), rng.randrange(S), rng.randint(2, 5)
        c = rng.choice([0x9FA4A6, 0xB2B7B9, 0xA2A7A9])
        d.polygon([(x - r, y), (x, y - r), (x + r, y), (x, y + r)], fill=rgb(c))
    save_tex(img, "galvanised")
    save_tex(tint(noise(0xA7ACAE, 3, "galvdark"), 0.8), "galvanised-dark")
    # The fan's intake: a black mesh over darkness
    img = Image.new("RGBA", (S, S), (14, 14, 15, 255))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 3):
        d.line([k, 0, k, S], fill=(58, 60, 62, 255))
        d.line([0, k, S, k], fill=(58, 60, 62, 255))
    save_tex(img, "fanmesh")
    save_tex(noise(0x1A1B1D, 2, "signalhousing"), "signalhousing")
    for sign in ("go", "stop"):
        img = Image.new("RGBA", (S, S), (10, 10, 11, 255))
        d = ImageDraw.Draw(img)
        # A matrix of lamps: the unlit ones faint, the lit ones in 3 px lines
        for y in range(2, S - 1, 3):
            for x in range(2, S - 1, 3):
                img.putpixel((x, y), (28, 28, 30, 255))
        col = (90, 255, 120, 255) if sign == "go" else (255, 50, 40, 255)
        if sign == "go":
            d.line([16, 5, 16, 24], fill=col, width=3)
            d.line([7, 16, 16, 26], fill=col, width=3)
            d.line([25, 16, 16, 26], fill=col, width=3)
        else:
            d.line([7, 7, 25, 25], fill=col, width=3)
            d.line([25, 7, 7, 25], fill=col, width=3)
        save_tex(img, f"signal-{sign}")


SEGMENTS = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
            "8": "abcdefg", "9": "abcdfg"}


def stencil_glyph(d, ch, x0, y0, w, h, t):
    """A digit drawn as stencil segments: each stroke stops short of the next, as a cut stencil leaves it."""
    g = 1  # the bridge between strokes
    segs = {
        "a": [x0 + g + t // 2, y0, x0 + w - g - t // 2 - 1, y0 + t - 1],
        "d": [x0 + g + t // 2, y0 + h - t, x0 + w - g - t // 2 - 1, y0 + h - 1],
        "g": [x0 + g + t // 2, y0 + h // 2 - t // 2, x0 + w - g - t // 2 - 1, y0 + h // 2 - t // 2 + t - 1],
        "f": [x0, y0 + g + t // 2, x0 + t - 1, y0 + h // 2 - g - 1],
        "b": [x0 + w - t, y0 + g + t // 2, x0 + w - 1, y0 + h // 2 - g - 1],
        "e": [x0, y0 + h // 2 + g, x0 + t - 1, y0 + h - g - t // 2 - 1],
        "c": [x0 + w - t, y0 + h // 2 + g, x0 + w - 1, y0 + h - g - t // 2 - 1],
    }
    for s in SEGMENTS[ch]:
        d.rectangle(segs[s], fill=255)


def spray(mask, key, color=(238, 238, 232)):
    """White spray paint through a stencil: crisp strokes, a soft overspray, a few flecks."""
    soft = mask.filter(ImageFilter.GaussianBlur(1.2))
    img = Image.new("RGBA", mask.size, (0, 0, 0, 0))
    px, m, sp = img.load(), mask.load(), soft.load()
    rng = random.Random(seed_of(key))
    for y in range(mask.size[1]):
        for x in range(mask.size[0]):
            if m[x, y] > 128:
                a = 235 - rng.randint(0, 30)
            elif sp[x, y] > 30:
                a = int(sp[x, y] * 0.35) if rng.random() < 0.7 else 0
            else:
                a = 0
            if a and rng.random() < 0.004 * 10:
                a = int(a * 0.6)
            if a:
                px[x, y] = color + (a,)
    for _ in range(10 * mask.size[0] // S):
        x, y = rng.randrange(mask.size[0]), rng.randrange(mask.size[1])
        if sp[x, y] > 5:
            px[x, y] = color + (150,)
    return img


def stencil_textures():
    Z = 64  # stencils are drawn at 64 px so the lettering reads
    for n in range(1, 11):
        mask = Image.new("L", (Z, Z), 0)
        d = ImageDraw.Draw(mask)
        digits = str(n)
        w, h, t = (22, 48, 6) if len(digits) == 1 else (18, 44, 6)
        total = len(digits) * w + (len(digits) - 1) * 6
        x = (Z - total) // 2
        for ch in digits:
            stencil_glyph(d, ch, x, (Z - h) // 2, w, h, t)
            x += w + 6
        save_tex(spray(mask, f"stencil{n}"), f"stencil-{n}")
    from PIL import ImageFont
    for direction in ("", "l", "r"):
        big = Image.new("L", (Z * 4, Z * 4), 0)
        d = ImageDraw.Draw(big)
        # An arrow along the wall, then TOWER under it, in stencil capitals
        pts = [(20, 84), (84, 34), (84, 64), (236, 64), (236, 104), (84, 104), (84, 134)]
        if direction == "r":
            pts = [(Z * 4 - x, y) for x, y in pts]
        if direction == "":  # straight on
            pts = [(128, 12), (186, 70), (150, 70), (150, 138), (106, 138), (106, 70), (70, 70)]
        d.polygon(pts, fill=255)
        font = ImageFont.load_default(size=64)
        tw = d.textbbox((0, 0), "TOWER", font=font)[2]
        d.text(((Z * 4 - tw) / 2, 150), "TOWER", font=font, fill=255)
        # stencil bridges: thin cuts through the letters
        for x in range(0, Z * 4, 22):
            d.line([x, 168, x, 172], fill=0, width=3)
        mask = big.resize((Z, Z), Image.LANCZOS)
        save_tex(spray(mask, f"stencilt{direction}"), f"stencil-tower{direction}")
    # The M.E.G. plaques beside the open doors: drawn wide (12 x 6) and squeezed into a square texture
    for lvl, label in (("1", "LVL 1"), ("11", "LVL 11"), ("178", "178")):
        img = noise(0x8B9094, 4, "plaque" + lvl, size=64).resize((64, 32))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 63, 31], outline=rgb(0x5E6366), width=2)
        for cx, cy in ((5, 5), (58, 5), (5, 26), (58, 26)):
            d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=rgb(0x6A6F72))
        T.text_img(img, label, (9, 5, 55, 27), (240, 240, 236, 255), 15)
        save_tex(img.resize((S, S), Image.LANCZOS), f"plaque-{lvl}")
    save_tex(noise(0x8B9094, 4, "plaqueside"), "plaqueside")
    save_tex(noise(0xA2A7AA, 3, "rivet"), "rivet")


def door_textures():
    # The carved doors: smooth cast concrete a little warmer than the walls; a damp stain creeping up from the sill
    save_tex(concrete(0xA59E90, "doorleaf", n=3, holes=False), "doorleaf")
    img = concrete(0xA59E90, "doorleaflow", n=3, holes=False)
    px = img.load()
    rng = random.Random(seed_of("damp"))
    for x in range(S):
        top = 14 + int(4 * math.sin(x * 0.45) + rng.uniform(0, 3))
        for y in range(top, S):
            t = min(1, (y - top) / 10) * 0.32
            r, g, b, a = px[x, y]
            px[x, y] = (T.clamp(r * (1 - t) + 70 * t), T.clamp(g * (1 - t) + 72 * t), T.clamp(b * (1 - t) + 64 * t), a)
    save_tex(img, "doorleaf-low")
    save_tex(concrete(0x85817A, "doorframe", n=4), "doorframe")
    save_tex(concrete(0x7D7A73, "doorsill", grain=False), "doorsill")
    img = noise(0xB08D57, 6, "brass")
    d = ImageDraw.Draw(img)
    d.line([0, 3, S, 3], fill=rgb(0xD0AE74))
    T.blotch(img, (24, 24), 8, (70, 86, 60), 0.3, seed_of("verdigris"))
    save_tex(img, "brass")
    save_tex(noise(0x0D0C0B, 1, "keyhole"), "keyhole")
    # Carving: the face, the floor of the recess (in its own shadow) and the relief (catching the light)
    save_tex(concrete(0x98938A, "carved", n=4), "carved")
    save_tex(tint(concrete(0x98938A, "carveddeep", n=4), 0.7), "carved-deep")
    save_tex(tint(concrete(0x98938A, "carvedrecess", n=4), 0.45), "carved-recess")  # a sigil's disc, deep in shadow
    save_tex(tint(concrete(0x98938A, "carvedrelief", n=3), 1.1, 6), "carved-relief")
    # Service door: grey-painted steel, chipped at the edges; its frame; a push bar; wired glass
    img = noise(0x7F8589, 3, "servicesteel")
    rng = random.Random(seed_of("chips"))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        x, y = rng.randrange(S), rng.choice([rng.randrange(3), S - 1 - rng.randrange(3), rng.randrange(S)])
        d.rectangle([x, y, x + rng.randint(0, 2), y + rng.randint(0, 1)], fill=rgb(rng.choice([0x5B4A3C, 0x9EA3A6])))
    save_tex(img, "servicesteel")
    save_tex(noise(0x5F6468, 3, "serviceframe"), "serviceframe")
    save_tex(noise(0xBFC3C6, 3, "pushbar"), "pushbar")
    img = Image.new("RGBA", (S, S), (34, 40, 44, 255))
    d = ImageDraw.Draw(img)
    for k in range(-S, S, 6):
        d.line([k, 0, k + S, S], fill=(88, 94, 96, 255))
        d.line([k + S, 0, k, S], fill=(88, 94, 96, 255))
    d.line([4, 2, 12, 10], fill=(70, 80, 86, 255), width=2)
    save_tex(img, "wireglass")
    # Ornate Tower doors: dark oiled oak, its grain running up; bronze bands and studs
    img = noise(0x4A3426, 4, "oak")
    px = img.load()
    rng = random.Random(seed_of("oakgrain"))
    for x in range(S):
        f = 1 + 0.12 * math.sin(x * 1.3 + rng.random() * 2) * (1 if x % 5 else 1.4)
        for y in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (T.clamp(r * f), T.clamp(g * f), T.clamp(b * f), a)
    save_tex(img, "oak")
    save_tex(tint(Image.open(os.path.join(ASSETS, "textures", "block", "hub", "oak.png")).convert("RGBA"), 1.18), "oak-light")
    img = noise(0x8C6A3A, 6, "bronze")
    T.blotch(img, (8, 20), 9, (62, 92, 70), 0.35, seed_of("bronzev"))
    save_tex(img, "bronze")
    # The pink door: glossy pink paint, white frame, a satin ribbon and a gold knob
    save_tex(noise(0xE896B6, 2, "pinkpaint"), "pinkpaint")
    save_tex(noise(0xF3B9D0, 2, "pinkpanel"), "pinkpanel")
    save_tex(noise(0xF4EEE8, 2, "whitepaint"), "whitepaint")
    img = noise(0xD8305E, 3, "ribbon")
    d = ImageDraw.Draw(img)
    for y in (3, 4, 17):
        d.line([0, y, S, y], fill=rgb(0xF06A90))
    d.line([0, 27, S, 27], fill=rgb(0xA81E44))
    save_tex(img, "ribbon")
    img = noise(0xD4AF37, 6, "gold")
    ImageDraw.Draw(img).line([0, 2, S, 2], fill=rgb(0xF2D77A))
    save_tex(img, "gold")


def tower_textures():
    # Ashlar: pale limestone-marble in two courses a block, staggered, with fine joints
    for state in ("plain", "worn"):
        img = noise(0xD9D2C3, 4, "ashlar" + state)
        mott = texlib._periodic_noise(seed_of("ashm" + state), 2)
        px = img.load()
        for y in range(S):
            for x in range(S):
                r, g, b, a = px[x, y]
                m = 1 + 0.04 * mott[y][x]
                px[x, y] = (T.clamp(r * m), T.clamp(g * m), T.clamp(b * m), a)
        d = ImageDraw.Draw(img)
        joint = rgb(0xA79F90)
        d.line([0, 0, S - 1, 0], fill=joint)
        d.line([0, 16, S - 1, 16], fill=joint)
        d.line([0, 1, 0, 15], fill=joint)
        d.line([16, 17, 16, S - 1], fill=joint)
        if state == "worn":
            rng = random.Random(seed_of("ashlarworn"))
            for _ in range(6):
                x, y = rng.randrange(S), rng.randrange(S)
                d.ellipse([x, y, x + rng.randint(1, 3), y + rng.randint(1, 2)], fill=rgb(0xB8B0A0))
            T.blotch(img, (10, 26), 10, (120, 112, 96), 0.3, seed_of("ashgrime"))
        save_tex(img, "ashlar-" + state)
    # Fluting for the pilasters: soft vertical channels
    img = noise(0xD9D2C3, 3, "flute")
    px = img.load()
    for y in range(S):
        for x in range(S):
            f = 0.86 + 0.14 * abs(math.cos(math.pi * x / 6.4))
            r, g, b, a = px[x, y]
            px[x, y] = (T.clamp(r * f), T.clamp(g * f), T.clamp(b * f), a)
    save_tex(img, "flute")
    # Polished marble floor, its inlaid band and the medallion at the rotunda's centre
    save_tex(texlib.marble((230, 225, 216), (182, 178, 172), seed_of("hubmarble"), veins=1, sharpness=9, turbulence=2.0), "marble-plain")
    img = texlib.marble((230, 225, 216), (182, 178, 172), seed_of("hubmarble2"), veins=1, sharpness=9, turbulence=2.0)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, S - 1, 21], fill=rgb(0x4E5A54))
    d.line([0, 9, S - 1, 9], fill=rgb(0xB8A27A))
    d.line([0, 22, S - 1, 22], fill=rgb(0xB8A27A))
    save_tex(img, "marble-inlay")
    img = texlib.marble((230, 225, 216), (182, 178, 172), seed_of("hubmarble3"), veins=1, sharpness=9, turbulence=2.0)
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], outline=rgb(0x4E5A54), width=3)
    d.ellipse([9, 9, 22, 22], fill=rgb(0x4E5A54))
    for k in range(10):
        a = 2 * math.pi * k / 10
        d.line([15.5 + 6 * math.cos(a), 15.5 + 6 * math.sin(a), 15.5 + 12 * math.cos(a), 15.5 + 12 * math.sin(a)], fill=rgb(0xB8A27A))
    d.ellipse([13, 13, 18, 18], fill=rgb(0xB8A27A))
    save_tex(img, "marble-centre")
    img = texlib.marble((216, 212, 204), (176, 172, 166), seed_of("statue"), veins=1, sharpness=8, mottle=0.06, turbulence=2.0)
    T.blotch(img, (12, 4), 12, (110, 108, 100), 0.25, seed_of("statuerain"))
    save_tex(img, "statue")
    # Artifacts under glass
    img = Image.new("RGBA", (S, S), (190, 215, 225, 46))
    d = ImageDraw.Draw(img)
    d.line([6, 0, 3, S], fill=(240, 250, 255, 120), width=2)
    d.line([24, 0, 22, S], fill=(240, 250, 255, 70))
    save_tex(img, "bellglass")
    img = Image.new("RGBA", (S, S), (150, 196, 170, 110))
    save_tex(img, "jarliquid")
    save_tex(noise(0x2E3A30, 4, "scarab"), "scarab")
    img = noise(0x3D5A44, 4, "scarabshell")
    ImageDraw.Draw(img).line([16, 0, 16, S], fill=rgb(0x1C2A20))
    save_tex(img, "scarabshell")
    save_tex(noise(0xD88AA0, 4, "squid"), "squid")
    save_tex(noise(0xE85A8A, 3, "noodle"), "noodle")
    save_tex(noise(0xC85A3A, 7, "clay"), "clay")
    save_tex(noise(0x3A6AC8, 7, "clayblue"), "clayblue")
    save_tex(noise(0x6A4A2E, 4, "radiowood"), "radiowood")
    img = Image.new("RGBA", (S, S), rgb(0x2A2420))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 3):
        d.line([0, y, S, y], fill=rgb(0x8A7A60))
    save_tex(img, "radiogrille")
    save_tex(noise(0xE0B040, 8, "crowngold"), "crowngold")
    save_tex(noise(0x7A1E2A, 3, "velvetred"), "velvetred")
    save_tex(noise(0x24314F, 3, "megnavy"), "megnavy")
    save_tex(noise(0xC8CCD0, 4, "silver"), "silver")


def outpost_textures():
    # Doorstep Carpet: a worn coir mat, WELCOME faded nearly away; drawn 14 x 10, squeezed square
    img = noise(0x8A6A3F, 12, "coir", size=64).resize((70, 50))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 69, 49], outline=rgb(0x5E4628), width=3)
    T.text_img(img, "WELCOME", (6, 12, 64, 38), (52, 36, 20, 150), 13)
    T.blotch(img, (35, 25), 20, (150, 126, 90), 0.4, seed_of("matworn"))
    save_tex(img.resize((S, S), Image.LANCZOS), "doormat")
    save_tex(noise(0x7A5C36, 8, "coirside"), "coir")
    # The M.E.G. banner: navy, a white eagle of our own, M.E.G. under it (drawn 14 x 24, then squeezed square)
    img = noise(0x22314F, 3, "banner", size=56).resize((56, 96))
    d = ImageDraw.Draw(img)
    white = (236, 236, 230, 255)
    cx = 28
    # wings spread, head turned, tail fanned
    d.polygon([(cx, 26), (cx - 22, 14), (cx - 17, 24), (cx - 23, 26), (cx - 14, 32), (cx - 18, 36), (cx - 6, 38),
               (cx - 4, 50), (cx - 9, 58), (cx, 54), (cx + 9, 58), (cx + 4, 50), (cx + 6, 38), (cx + 18, 36),
               (cx + 14, 32), (cx + 23, 26), (cx + 17, 24), (cx + 22, 14)], fill=white)
    d.ellipse([cx - 4, 18, cx + 4, 27], fill=white)
    d.polygon([(cx + 3, 21), (cx + 8, 23), (cx + 3, 25)], fill=(232, 190, 70, 255))
    T.text_img(img, "M.E.G.", (4, 66, 52, 86), white, 14)
    d.rectangle([0, 0, 55, 95], outline=(200, 170, 80, 255), width=2)
    save_tex(img.resize((S, S), Image.LANCZOS), "megbanner")
    save_tex(noise(0x3E3A34, 3, "rod"), "rod")
    # Key cabinet: steel, a mesh door; little brass and iron keys
    save_tex(noise(0x6E7478, 3, "cabinet"), "cabinet")
    save_tex(noise(0x2C2E30, 3, "cabinetback"), "cabinetback")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 4):
        d.line([k, 0, k, S], fill=(150, 156, 160, 255))
        d.line([0, k, S, k], fill=(150, 156, 160, 255))
    save_tex(img, "mesh")
    save_tex(noise(0x5C5E60, 4, "ironkey"), "ironkey")
    # The door register: a whiteboard with the Hub sketched on it in marker (64 x 48, then squeezed square)
    img = noise(0xF2F2EE, 2, "board", size=64).resize((64, 48))
    d = ImageDraw.Draw(img)
    blue, red, black = (40, 70, 170, 255), (190, 40, 40, 255), (30, 30, 34, 255)
    cx, cy = 20, 24
    for r in (5, 12, 19):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=blue)
    for k in range(10):
        a = 2 * math.pi * k / 10 - math.pi / 2
        d.line([cx + 3 * math.cos(a), cy + 3 * math.sin(a), cx + 21 * math.cos(a), cy + 21 * math.sin(a)], fill=black)
    for k, mark in ((6, red), (9, red), (4, red)):
        a = 2 * math.pi * k / 10 - math.pi / 2
        x, y = cx + 15 * math.cos(a), cy + 15 * math.sin(a)
        d.line([x - 2, y - 2, x + 2, y + 2], fill=mark, width=2)
        d.line([x - 2, y + 2, x + 2, y - 2], fill=mark, width=2)
    for i, line in enumerate(("L1 - T7", "L11 - T10", "178 - T5", "KEYS? ASK")):
        T.text_img(img, line, (42, 4 + i * 10, 63, 13 + i * 10), black if i < 3 else red, 7)
    d.rectangle([0, 0, 63, 47], outline=(170, 174, 178, 255), width=2)
    save_tex(img.resize((S, S), Image.LANCZOS), "whiteboard")
    save_tex(noise(0xAEB2B6, 3, "aluminium"), "aluminium")
    # Field radio: olive drab, knobs, a dial
    save_tex(noise(0x4B5320, 4, "olive"), "olive")
    img = noise(0x4B5320, 4, "radioface")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 4, 18, 13], fill=rgb(0xC8C09A), outline=rgb(0x2A2A20))
    for x in range(5, 18, 2):
        d.line([x, 6, x, 8], fill=rgb(0x2A2A20))
    d.line([11, 5, 13, 12], fill=rgb(0xB02020))
    for cx in (7, 15, 23):
        d.ellipse([cx - 3, 18, cx + 3, 24], fill=rgb(0x1E1E18))
    d.rectangle([22, 4, 28, 13], fill=rgb(0x262620))
    save_tex(img, "radioface")
    save_tex(noise(0x1E1E18, 2, "blackknob"), "blackknob")
    # Camp Amber: a painted plywood board, an amber chalk arrow
    img = noise(0x33402F, 4, "plywood", size=64).resize((64, 64))
    d = ImageDraw.Draw(img)
    for y in range(0, 64, 9):
        d.line([0, y + 3, 64, y + 5], fill=rgb(0x2C3828))
    amber = (232, 163, 60, 255)
    T.text_img(img, "CAMP", (4, 4, 60, 20), amber, 15)
    T.text_img(img, "AMBER", (4, 19, 60, 35), amber, 15)
    T.text_img(img, "NEW?", (4, 37, 60, 49), (226, 214, 180, 255), 11)
    T.text_img(img, "ASK US", (4, 49, 60, 61), (226, 214, 180, 255), 11)
    save_tex(img.resize((S, S), Image.LANCZOS), "ambersign")
    save_tex(noise(0xB8966A, 6, "plywoodside"), "plywood")
    for direction in ("l", "r"):
        mask = Image.new("L", (S * 4, S * 4), 0)
        d = ImageDraw.Draw(mask)
        pts = [(14, 64), (50, 34), (50, 54), (114, 54), (114, 74), (50, 74), (50, 94)]
        if direction == "r":
            pts = [(S * 4 - x, y) for x, y in pts]
        d.polygon(pts, fill=255)
        mask = mask.resize((S, S), Image.LANCZOS)
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        px, m = img.load(), mask.load()
        rng = random.Random(seed_of("chalk" + direction))
        for y in range(S):
            for x in range(S):
                if m[x, y] > 100 and rng.random() < 0.82:
                    px[x, y] = (232, 163, 60, rng.randint(170, 240))
        save_tex(img, f"amberarrow-{direction}")
    # Camp cot: olive canvas on a steel frame
    save_tex(noise(0x5C6448, 4, "canvas"), "canvas")


# ======================= Blocks: the tunnels =======================

def cube_family(code, english, kinds, tex_of, comment, material="Stone", sounds=STONE, turned=(), **extra):
    """A plain cube block, one texture per kind; kinds in `turned` are rotated at random from block to block."""
    data = {"variantgroups": [{"code": "kind", "states": list(kinds)}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "texturesByType": {},
            "lightAbsorption": 99, "resistance": 4, "sounds": sounds}
    for k in kinds:
        tex = {"base": "block/hub/" + tex_of(k)}
        if k in turned:
            tex["alternates"] = [{"base": "block/hub/" + tex_of(k), "rotation": r} for r in (90, 180, 270)]
        data["texturesByType"][f"*-{k}"] = {"all": tex}
    data.update(extra)
    block(code, data, comment)
    for k in kinds:
        name(f"{code}-{k}", english if isinstance(english, str) else english[k])


def oriented(code, english, shapes, comment, groups=(), material="Stone", sounds=STONE, box=(0, 0, 0, 1, 1, 1),
             collide=True, solid=False, light=None, extra=None, creative="decorative"):
    """A block with a `side` group, shapes keyed by the leading states ("kind-part" ... without the side), each
    rotated to the four sides."""
    data = {"variantgroups": [{"code": g, "states": s} for g, s in groups] + [{"code": "side", "states": SIDES}]}
    by_type = {}
    for key, path in shapes.items():
        prefix = f"*-{key}" if key else "*"
        for s in SIDES:
            by_type[f"{prefix}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    data["shapeByType"] = by_type
    first = "*-" + "-".join(g[1][0] for g in groups) + "-north" if groups else "*-north"
    data["creativeinventory"] = {"general": [first], creative: [first]}
    data.update({"blockmaterial": material, "drawtype": "json"})
    if solid:
        data.update({"sidesolid": {"all": True}, "sideopaque": {"all": False}, "lightAbsorption": 99, "resistance": 6})
    else:
        data.update({"sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1.5})
    data["sounds"] = sounds
    if box != (0, 0, 0, 1, 1, 1):
        data["selectionboxByType"] = boxes_by_side(box)
        if collide:
            data["collisionboxByType"] = boxes_by_side(box)
    if not collide:
        data["collisionbox"] = None
    if light:
        data["lightHsv"] = light
    if extra:
        data.update(extra)
    block(code, data, comment)
    name(code + "-*", english)


def tunnel_blocks():
    cube_family("hub-wall", "Concrete Wall Panel", ["plain", "left", "bottom", "corner"], lambda k: "wall-" + k,
                "The Hub's tunnel walls: great cast concrete panels, 2 blocks wide and 3 high. 'left' carries the seam on its"
                " left edge (every 2nd block along a wall), 'bottom' on its bottom edge (every 3rd block up), 'corner' both",
                resistance=6)
    block("hub-ceiling", {"creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Stone",
                          "drawtype": "cube", "textures": {"all": {"base": "block/hub/ceiling"}},
                          "lightAbsorption": 99, "resistance": 6, "sounds": STONE},
          "The tunnel roof: darker concrete cast against boards")
    name("hub-ceiling", "Concrete Tunnel Roof")
    cube_family("hub-asphalt", {"plain": "Asphalt", "worn": "Worn Asphalt", "patch": "Patched Asphalt"}, ["plain", "worn", "patch"],
                lambda k: "asphalt-" + k, "The road through the Hub: dry asphalt; worn smooth in the lanes; patched with tar",
                turned=("plain", "worn", "patch"))
    cube_family("hub-tilecrumb", "Tiled Concrete", ["1", "2"], lambda k: "tilecrumb-" + k,
                "Where a far tunnel turns toward Level 37, white pool tile creeps over the concrete: stage 1 scattered, 2 mostly tile")
    block("hub-void", {"creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
                       "textures": {"all": {"base": "block/hub/void"}}, "lightAbsorption": 99, "resistance": 999,
                       "drops": [], "sounds": STONE},
          "Pure black: the storm void outside the Tower's balcony, and the shaft below the hole to Level 94")
    name("hub-void", "Darkness")
    block("hub-falsewall", {
        "creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "textures": {"all": {"base": "block/hub/wall-false"}}, "collisionbox": None, "lightAbsorption": 99,
        "resistance": 6, "drops": [], "sounds": STONE,
        "particleProperties": [{
            "hsvaColor": [{"avg": 25, "var": 5}, {"avg": 20, "var": 10}, {"avg": 150, "var": 20}, {"avg": 60, "var": 20}],
            "gravityEffect": {"avg": 0, "var": 0.01},
            "posOffset": [{"avg": 0, "var": 0.5}, {"avg": 0, "var": 0.5}, {"avg": 0, "var": 0.5}],
            "velocity": [{"avg": 0, "var": 0.01}, {"avg": 0.005, "var": 0.005}, {"avg": 0, "var": 0.01}],
            "quantity": {"avg": 0.015}, "size": {"avg": 0.08, "var": 0.04}, "particleModel": "Quad",
            "lifeLength": {"avg": 2, "var": 1}, "selfPropelled": True}],
    }, "A stretch of tunnel wall whose seams meet nothing. Walk into it: it isn't there (the way to Level 4)")
    name("hub-falsewall", "Concrete Wall Panel")

    # Road stud: a yellow ceramic dome standing on the asphalt (the dotted lines are made of these)
    stud = [cube("asphalt-plain"),
            bx("StudBase", (6, 16, 6), (10, 16.6, 10), "stud", faces=FRONT + ("south",)),
            bx("StudDome", (6.6, 16.6, 6.6), (9.4, 17.2, 9.4), "stud", faces=FRONT + ("south",)),
            bx("ReflectorN", (6.8, 16.15, 5.85), (9.2, 16.75, 6), "studreflector", faces=("north",), glow=40),
            bx("ReflectorS", (6.8, 16.15, 10), (9.2, 16.75, 10.15), "studreflector", faces=("south",), glow=40)]
    path = shape("asphalt-stud", stud)
    block("hub-asphalt-stud", {"creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Stone",
                               "drawtype": "json", "shape": {"base": path}, "sidesolid": {"all": True},
                               "sideopaque": {"all": True, "up": False}, "lightAbsorption": 99, "resistance": 4, "sounds": STONE,
                               "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
          "Asphalt with a yellow road stud on top (the stud stands in the air above): the Hub's dotted lines")
    name("hub-asphalt-stud", "Asphalt with Road Stud")

    # Sidewalk: a half slab; the kerb version has a rounded lip on the road side (modelled to the north)
    slab = bx("Slab", (0, 0, 0), (16, 8, 16), "sidewalk", faces=("up", "down"))
    sides = bx("SlabSides", (0, 0, 0), (16, 8, 16), "kerb", faces=("north", "east", "south", "west"))
    path = shape("sidewalk", [slab, sides])
    block("hub-sidewalk", {"creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Stone",
                           "drawtype": "json", "shape": {"base": path}, "sidesolid": {"all": False, "down": True},
                           "sideopaque": {"all": False, "down": True}, "lightAbsorption": 0, "resistance": 4, "sounds": STONE,
                           "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1},
                           "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}},
          "The tunnel's raised sidewalk: a half slab of pale concrete. Arrivals are put down here")
    name("hub-sidewalk", "Sidewalk")
    curb = [bx("Slab", (0, 0, 2), (16, 8, 16), "sidewalk", faces=("up", "down", "east", "west", "south")),
            bx("Kerb", (0, 0, 0.5), (16, 7, 2), "kerb", faces=("north", "east", "west", "down")),
            bx("KerbTop", (0, 7, 1), (16, 7.6, 2), "kerb", faces=("north", "up", "east", "west")),
            bx("KerbRound", (0, 0, 0), (16, 6.2, 0.5), "kerb", faces=("north", "up", "east", "west")),
            bx("KerbEdge", (0, 7.6, 1.6), (16, 8, 2), "kerb", faces=("north", "up", "east", "west"))]
    oriented("hub-curb", "Kerb", {None: shape("curb", curb)},
             "The sidewalk's edge: a half slab with a rounded kerb lip on its north (road) side",
             box=(0, 0, 0, 1, 0.5, 1), material="Stone", sounds=STONE, creative="construction",
             extra={"sidesolid": {"all": False, "down": True}, "sideopaque": {"all": False, "down": True}, "resistance": 4})

    # The hole's rim: asphalt broken away toward the hole (to the north), black where it drops
    lip = [bx("Body", (0, 0, 2.5), (16, 16, 16), "asphalt-plain", faces=("up", "south", "east", "west", "down")),
           bx("Edge", (0, 0, 2.5), (16, 16, 16), "holeedge", faces=("north",)),
           bx("LipLow", (0, 0, 0), (16, 13.5, 2.5), "asphalt-plain", faces=("up", "east", "west", "down")),
           bx("LipLowEdge", (0, 0, 0), (16, 13.5, 2.5), "holeedge", faces=("north",)),
           bx("Crumb1", (2, 13.5, 1), (5, 14.5, 2.5), "asphalt-plain", faces=FRONT),
           bx("Crumb2", (9, 13.5, 0.5), (13, 15, 2.5), "asphalt-plain", faces=FRONT),
           bx("Crack", (5, 16, 3), (9, 16.05, 4), "void", faces=("up",))]
    oriented("hub-holelip", "Broken Asphalt", {None: shape("holelip", lip)},
             "The rim of the rectangular hole in a far tunnel's road (the hole is to its north): asphalt broken away into black",
             solid=True, creative="construction", extra={"resistance": 4})

    # Caged sodium lamp on a wall plate: on, dead, flickering (modelled on the wall to the south)
    # (Lit, the glass fills the cage to its floor and front, so it shows from the road below, and the hood's
    # underside is washed amber; a lamp seen from below was a dark box)
    def lamp(glass):
        lit = glass == "lampglass"
        g = 255 if lit else 0
        under = ("lamphood-lit", 200) if lit else ("lamphousing", 0)
        els = [bx("Plate", (4.5, 3.5, 15), (11.5, 12.5, 16), "lamphousing"),
               bx("Arm", (7, 10, 12), (9, 11.5, 15), "lamphousing"),  # (its underside not in the hood's)
               bx("Hood", (3.5, 10, 7.5), (12.5, 12, 15), "lamphousing", faces=("north", "east", "south", "west", "up")),
               bx("HoodLip", (3, 9.5, 7), (13, 10, 15), "lamphousing", faces=("north", "east", "south", "west", "up")),
               bx("HoodUnder", (3, 9.5, 7), (13, 10, 15), under[0], glow=under[1], faces=("down",), full=True)]
        if lit:
            els.append(bx("Glass", (4.4, 4.1, 8.4), (11.6, 9.5, 14.8), glass, glow=g, full=True))
        else:
            els += [bx("Glass", (4.5, 4.5, 8.5), (11.5, 9.5, 14), glass),
                    bx("Base", (5, 3.8, 9), (11, 4.5, 13.5), "lamphousing")]
        for i, x in enumerate((4.2, 6.8, 8.7, 11.3)):
            els.append(bx(f"BarF{i}", (x - 0.25, 4.0, 7.9), (x + 0.25, 9.5, 8.4), "cage"))
        # The cage's floor and sides are bars, not plates, so the glass shows between them from below and the side
        els += [bx("BarRing", (3.8, 6.8, 7.9), (12.2, 7.2, 8.4), "cage"),
                bx("BarRingL", (3.8, 6.8, 8.4), (4.3, 7.2, 14.5), "cage"),
                bx("BarRingR", (11.7, 6.8, 8.4), (12.2, 7.2, 14.5), "cage")]
        for i, z in enumerate((7.9, 11.2, 14)):
            els.append(bx(f"BarBottom{i}", (3.8, 3.6, z), (12.2, 4.1, z + 0.5), "cage"))
            if i:
                els += [bx(f"BarSideL{i}", (3.8, 4.1, z), (4.3, 9.5, z + 0.5), "cage"),
                        bx(f"BarSideR{i}", (11.7, 4.1, z), (12.2, 9.5, z + 0.5), "cage")]
        for i, x in enumerate((3.8, 7.75, 11.7)):
            els.append(bx(f"BarUnder{i}", (x, 3.6, 8.4), (x + 0.5, 4.1, 14), "cage"))
        return els
    on, dead = shape("lamp-on", lamp("lampglass")), shape("lamp-dead", lamp("lampglass-dead"))
    oriented("hub-lamp", "Tunnel Lamp", {"on": on, "dead": dead, "flicker": on},
             "A caged sodium lamp on the tunnel wall (the wall to its south): amber when on; dead; or failing now and then",
             groups=[("state", ["on", "dead", "flicker"])], material="Glass", sounds=GLASS, box=(0.2, 0.2, 0.42, 0.8, 0.8, 1),
             collide=False,
             extra={"lightHsvByType": {"*-on-*": [5, 6, 14], "*-flicker-*": [5, 6, 14]},
                    "entityClassByType": {"*-flicker-*": "BackroomsFlicker"},
                    "attributesByType": {f"*-flicker-{s}": {"offBlock": f"backrooms:hub-lamp-dead-{s}"} for s in SIDES},
                    "dropsByType": {"*-flicker-*": [{"type": "block", "code": "hub-lamp-dead-north"}],
                                    "*": [{"type": "item", "code": "glassshard", "quantity": {"avg": 1.5, "var": 0.5}},
                                          {"type": "item", "code": "metalbracket", "quantity": {"avg": 0.5, "var": 0}},
                                          {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.4, "var": 0}}]}})

    # Jet fan: a long galvanised cylinder hung from the roof, overhanging its block along its axis (modelled along X)
    def octo(nm, x1, x2, cy, cz, r, tex, faces=DIRS):
        """A regular octagonal prism along X (inradius r): four slabs, each as long as the octagon is wide and as wide
        as one of its sides, turned 0, 45, 90 and 135 degrees about the axis."""
        a = r * math.tan(math.pi / 8)
        out = []
        for i, ang in enumerate((0, 45, 90, 135)):
            if ang == 90:
                frm, to = (x1, cy - r, cz - a), (x2, cy + r, cz + a)
            else:
                frm, to = (x1, cy - a, cz - r), (x2, cy + a, cz + r)
            rot = (ang, 0, 0) if ang in (45, 135) else None
            out.append(bx(f"{nm}{i}", frm, to, tex, faces=faces, aligned=False, rot=rot, origin=(x1, cy, cz)))
        return out
    def octo_ring(nm, x1, x2, cy, cz, r, t, tex):
        """A hollow octagonal collar along X: eight plates, one per side."""
        a = r * math.tan(math.pi / 8) + 0.05
        out = []
        for k in range(8):
            out.append(bx(f"{nm}{k}", (x1, cy + r - t, cz - a), (x2, cy + r, cz + a), tex, aligned=False,
                          rot=(k * 45, 0, 0) if k else None, origin=(x1, cy, cz)))
        return out

    def mesh(nm, x, cy, cz, r, face):
        """The intake mesh filling an octagon at x, seen from one end (its slabs a hair apart, so they never fight)."""
        out = []
        for i, e in enumerate(octo(nm, 0, 0.1, cy, cz, r, "fanmesh", faces=(face,))):
            off = x + (i * 0.03 if face == "east" else -i * 0.03)
            e = shift([e], dx=off)[0]
            e["faces"][face]["uv"] = [0, 0, 16, 16]
            out.append(e)
        return out
    cy, cz = 5.5, 8
    fan = []
    fan += octo("Body", -12.5, 28.5, cy, cz, 7, "galvanised", faces=("north", "south", "up", "down"))
    fan += octo_ring("RingW", -14, -11.5, cy, cz, 7.8, 1.6, "galvanised-dark")
    fan += octo_ring("RingE", 27.5, 30, cy, cz, 7.8, 1.6, "galvanised-dark")
    fan += octo_ring("Band", 7, 9, cy, cz, 7.4, 0.6, "galvanised-dark")
    fan += mesh("MeshW", -13.2, cy, cz, 6.4, "west") + mesh("MeshE", 29.1, cy, cz, 6.4, "east")
    fan += [bx("MotorBox", (5, 12, 5), (11, 14.5, 11), "galvanised-dark"),
            bx("HangerW", (-1, 12, 3), (0.5, 16, 13), "galvanised-dark"),
            bx("HangerE", (15.5, 12, 3), (17, 16, 13), "galvanised-dark"),
            bx("PlateW", (-2, 15.4, 2), (1.5, 16, 14), "galvanised-dark"),
            bx("PlateE", (14.5, 15.4, 2), (18, 16, 14), "galvanised-dark"),
            bx("Conduit", (10, 14.5, 7.5), (11, 16, 8.5), "galvanised-dark")]
    path = shape("jetfan", fan)
    block("hub-jetfan", {
        "variantgroups": [{"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "decorative": ["*-we"]}, "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {"*-we": {"base": path, "rotateY": 0}, "*-ns": {"base": path, "rotateY": 90}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 3, "sounds": METAL,
        "collisionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.06, "x2": 1, "y2": 1, "z2": 0.94},
                               "*-ns": {"x1": 0.06, "y1": 0, "z1": 0, "x2": 0.94, "y2": 1, "z2": 1}},
        "selectionboxByType": {"*-we": {"x1": 0, "y1": 0, "z1": 0.06, "x2": 1, "y2": 1, "z2": 0.94},
                               "*-ns": {"x1": 0.06, "y1": 0, "z1": 0, "x2": 0.94, "y2": 1, "z2": 1}},
        "drops": [{"type": "item", "code": "metalbracket", "quantity": {"avg": 2, "var": 1}},
                  {"type": "item", "code": "scrapwire", "quantity": {"avg": 1.5, "var": 0.5}},
                  {"type": "item", "code": "game:metalbit-copper", "quantity": {"avg": 0.2, "var": 0}}],
    }, "A jet fan hung from the tunnel roof, still and silent: 2.75 blocks long along its axis (we = along X), 0.9"
       " across, hanging from the top of its block 0.35 into the one below. Hang them in pairs side by side")
    name("hub-jetfan-*", "Jet Fan")

    # Lane signal: a black box on a rod from the roof, a green arrow (go) or red cross (stop) toward the north
    def signal(sign):
        lit = f"signal-{sign}"
        return [bx("Rod", (7.3, 12, 7.3), (8.7, 16, 8.7), "signalhousing"),
                bx("Mount", (5, 15.3, 5), (11, 16, 11), "signalhousing"),
                bx("Box", (2, 0.5, 5), (14, 12.5, 11), "signalhousing", faces=("east", "west", "up", "down", "south")),
                bx("Face", (2, 0.5, 5), (14, 12.5, 11), lit, faces=("north",), full=True, glow=180),
                bx("Visor", (1.5, 12, 2.5), (14.5, 12.8, 5.2), "signalhousing"),
                bx("VisorL", (13.8, 7, 2.5), (14.5, 12, 5), "signalhousing"),
                bx("VisorR", (1.5, 7, 2.5), (2.2, 12, 5), "signalhousing")]
    oriented("hub-lanesignal", "Lane Signal", {"go": shape("lanesignal-go", signal("go")), "stop": shape("lanesignal-stop", signal("stop"))},
             "A lane signal hung from the tunnel roof over a lane, its face to the north: a green arrow down, or a red cross over a dead-end lane",
             groups=[("sign", ["go", "stop"])], material="Metal", sounds=METAL, box=(0.12, 0, 0.3, 0.88, 1, 0.7),
             collide=False, extra={"lightHsvByType": {"*-go-*": [22, 7, 4], "*-stop-*": [0, 7, 4]},
                                   "drops": [{"type": "item", "code": "glassshard", "quantity": {"avg": 1, "var": 0.5}},
                                             {"type": "item", "code": "scrapwire", "quantity": {"avg": 1, "var": 0.5}}]})

    # Stencils, plaques and arrows: thin plates on the wall to the south
    decal = {"sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.2,
             "drops": [], "replaceable": 5000}
    states = [str(n) for n in range(1, 11)] + ["tower", "towerl", "towerr"]
    shapes = {s: shape(f"stencil-{s}", [bx("Paint", (0, 0, 15.9), (16, 16, 16), f"stencil-{s}", faces=("north",), full=True)]) for s in states}
    oriented("hub-stencil", "Stencilled Number", shapes,
             "The M.E.G.'s spray-stencilled tunnel numbers (1-10) and the arrow to the Tower (tower points straight on,"
             " towerl to the viewer's left, towerr right), painted on the wall to the south", groups=[("n", states)], box=(0.05, 0.05, 0.94, 0.95, 0.95, 1),
             collide=False, extra=decal)
    for s in states:
        name(f"hub-stencil-{s}-*", "Stencilled Tower Arrow" if s.startswith("tower") else f"Stencilled {s}")
    plaque = lambda lvl: [bx("Plate", (2, 5, 15.2), (14, 11, 16), f"plaque-{lvl}", faces=("north",), full=True),
                          bx("PlateSides", (2, 5, 15.2), (14, 11, 16), "plaqueside", faces=("east", "west", "up", "down"))] + \
        [bx(f"Rivet{i}", (x - 0.4, y - 0.4, 14.9), (x + 0.4, y + 0.4, 15.2), "rivet", faces=FRONT) for i, (x, y) in
         enumerate(((3, 6), (13, 6), (3, 10), (13, 10)))]
    oriented("hub-plaque", "M.E.G. Plaque", {lvl: shape(f"plaque-{lvl}", plaque(lvl)) for lvl in ("1", "11", "178")},
             "The plates the M.E.G. riveted beside the three doors that are always open", groups=[("lvl", ["1", "11", "178"])],
             material="Metal", sounds=METAL, box=(0.12, 0.3, 0.94, 0.88, 0.7, 1), collide=False, extra=dict(decal, resistance=2))
    oriented("hub-amberarrow", "Amber Chalk Arrow",
             {d: shape(f"amberarrow-{d}", [bx("Chalk", (0, 0, 15.9), (16, 16, 16), f"amberarrow-{d}", faces=("north",), full=True)]) for d in ("l", "r")},
             "Camp Amber's chalk arrows on the wall to the south, pointing to the viewer's left (l) or right (r): to the camp, or in"
             " Level 1 to the door into the Hub", groups=[("dir", ["l", "r"])], box=(0.05, 0.2, 0.94, 0.95, 0.8, 1), collide=False, extra=decal)
