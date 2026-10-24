"""Level Fun =) (tag `fun`, id 15): every asset in the plan's manifest (docs/design/new-levels/fun-plan.md, section 4).

Surfaces, props as real 3D shapes, items, the entity types and the level's lang. The entity models are made by
gen_fun_models.py and the sounds by gen_fun_sounds.py; this runs both first unless told not to.

Everything is written to Fun's own folders: textures/block/fun/, shapes/block/fun/, blocktypes/fun/, itemtypes/fun/,
textures/item/fun/, shapes/item/fun/, entities/fun-*.json; the names are merged into lang/en.json in place.

Props are modelled facing north (toward -Z), as everywhere in the mod; `-{side}` variants turn them. Run only through
the asset lock:   bash tools/locked.sh run python tools/gen_fun.py [--no-models] [--no-sounds]
"""
import json
import math
import os
import random
import re
import sys

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import detail_kit  # noqa: E402
from detail_kit import ASSETS, CLOTH, GLASS, METAL, ROTATE, SIDES, STONE, WOOD, bx, seed_of, shift, turn  # noqa: E402
import gen_textures as T  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
SRC = os.path.join(ROOT, "src")
S = 32
TAB, NL = "\t", "\n"
LANG = {}
FUN_TEX = set()
WRITTEN = {"blocktypes": [], "shapes": [], "textures": [], "itemtypes": [], "entities": []}

PLASTIC = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
RUBBER = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
POP = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "backrooms:ambient/fun/balloonpop", "hit": "game:block/cloth"}
PAPER = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}

# The six party colours of the manifest
PARTY = {"red": 0xD64541, "yellow": 0xF2C641, "blue": 0x3C7DD9, "green": 0x4CAF6A, "orange": 0xF08A3C, "purple": 0x8E5BC4}


# ============================================================ Kit (Fun's own folders)

def registered(name):
    """True once the code agent has registered a class or task of this name in src/ (so the JSON may use it)."""
    pat = re.compile(r'Register[\w<>, ]*\(\s*"' + re.escape(name) + r'"')
    for dirpath, _, files in os.walk(SRC):
        for f in files:
            if f.endswith(".cs"):
                with open(os.path.join(dirpath, f), encoding="utf-8", errors="ignore") as fh:
                    if pat.search(fh.read()):
                        return True
    return False


def rgb(h, a=255):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255, a)


def clamp(v):
    return max(0, min(255, int(v)))


def tint(c, k):
    return tuple(clamp(v * k) for v in c[:3]) + ((c[3],) if len(c) > 3 else (255,))


def mixc(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def save(img, key):
    T.save(img, f"block/fun/{key}.png")
    FUN_TEX.add(key)
    WRITTEN["textures"].append(key)


def save_item(img, key):
    T.save(img, f"item/fun/{key}.png")
    WRITTEN["textures"].append("item/" + key)


def tpath(key):
    if key in FUN_TEX:
        return f"backrooms:block/fun/{key}"
    return detail_kit.tpath(key)


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def shape(name, elements, size=16):
    keys = set()
    for e in elements:
        stack = [e]
        while stack:
            el = stack.pop()
            for face in el["faces"].values():
                keys.add(face["texture"][1:])
            stack.extend(el.get("children", []))
    data = {"textureWidth": size, "textureHeight": size, "textures": {k: tpath(k) for k in sorted(keys)}, "elements": elements}
    write_json(os.path.join(ASSETS, "shapes", "block", "fun", name + ".json"), data)
    WRITTEN["shapes"].append(name)
    return "block/fun/" + name


def block(fname, data, comment=None):
    write_json(os.path.join(ASSETS, "blocktypes", "fun", fname + ".json"), data, comment)
    WRITTEN["blocktypes"].append(fname)


def name(pattern, english):
    LANG["block-" + pattern] = english


def cuboid(box, side=None):
    x1, y1, z1, x2, y2, z2 = box
    c = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
    if side and ROTATE[side]:
        c["rotateY"] = ROTATE[side]
    return c


def bxf(nm, frm, to, tex, **kw):
    """A box with the whole texture stretched over each face (pictures, balloons, round things on alpha)."""
    return bx(nm, frm, to, tex, full=True, **kw)


def prop(code, english, parts, box=None, oriented=True, material="Wood", sounds=WOOD, light=None, comment=None,
         collide=True, extra=None, fname=None, inventory=True, sel=None):
    """A free-standing prop in Fun's folders. `parts` is a list of boxes, or {kind: boxes} for several kinds."""
    data = {"code": code}
    kinds = parts if isinstance(parts, dict) else None
    groups = []
    if kinds:
        groups.append({"code": "kind", "states": list(kinds)})
    if oriented:
        groups.append({"code": "side", "states": SIDES})
    if groups:
        data["variantgroups"] = groups
    shapes = {k: shape(f"{code}-{k}", v) for k, v in kinds.items()} if kinds else {None: shape(code, parts)}
    by_type = {}
    for k, path in shapes.items():
        prefix = f"*-{k}" if k else "*"
        if oriented:
            for s_ in SIDES:
                by_type[f"{prefix}-{s_}"] = {"base": path, "rotateY": ROTATE[s_]}
        else:
            by_type[prefix if k else "*"] = {"base": path}
    if len(by_type) == 1:
        data["shape"] = next(iter(by_type.values()))
    else:
        data["shapeByType"] = by_type
    if inventory:
        first = f"*-{next(iter(kinds))}" if kinds else "*"
        first += "-north" if oriented else ""
        data["creativeinventory"] = {"general": [first], "decorative": [first]}
    data.update({"blockmaterial": material, "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
                 "lightAbsorption": 0, "resistance": 1.5, "sounds": sounds})
    if box is not None:
        if oriented:
            data["collisionboxByType"] = {f"*-{s_}": cuboid(box, s_) for s_ in SIDES}
            data["selectionboxByType"] = {f"*-{s_}": cuboid(sel or box, s_) for s_ in SIDES}
        else:
            data["collisionbox"] = cuboid(box)
            data["selectionbox"] = cuboid(sel or box)
    if not collide:
        data["collisionbox"] = None
        data.pop("collisionboxByType", None)
    if light:
        data["lightHsv"] = light
    if extra:
        data.update(extra)
    block(fname or code, data, comment or english)
    name(code + "-*" if groups else code, english)


def drops(*items):
    out = []
    for code, avg, var in items:
        kind = "item"
        if code.startswith("block:"):
            kind, code = "block", code[6:]
        out.append({"type": kind, "code": code, "quantity": {"avg": avg, "var": var}})
    return out


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


TRANSFORMS = {
    "guiTransform": {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1},
    "tpHandTransform": {"translation": {"x": -0.75, "y": -0.4, "z": -0.55}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.6},
    "groundTransform": {"rotation": {"x": 90, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2},
}


# ============================================================ Texture helpers

def noise(color, n=5, key="x", size=S):
    c = rgb(color)[:3] if isinstance(color, int) else tuple(color[:3])
    return T.noise_fill(c, n, seed_of(key), size)


def flat(c, size=S):
    c = rgb(c) if isinstance(c, int) else tuple(c[:3]) + (255,)
    return Image.new("RGBA", (size, size), c)


def clear(size=S, h=None):
    return Image.new("RGBA", (size, h or size), (0, 0, 0, 0))


def grain(img, amount, key):
    rng = random.Random(seed_of(key))
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            n = rng.uniform(-amount, amount)
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), a)
    return img


def text(img, s_, box, color, size):
    T.text_img(img, s_, box, rgb(color) if isinstance(color, int) else color, size)


def supersample(w, h, k, draw_fn, bg=(0, 0, 0, 0)):
    """Draws at k times the size with draw_fn(draw, k) and scales down: smooth curves for pictures and round things."""
    big = Image.new("RGBA", (w * k, h * k), bg)
    draw_fn(ImageDraw.Draw(big), k, big)
    return big.resize((w, h), Image.LANCZOS)


def harden(img, cut=110):
    """Alpha to 0 or 255, so cut-out shapes stay crisp at their edges."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 255 if a >= cut else 0)
    return img


def sheen(img, strength=18, key="sheen", angle=1):
    """A soft diagonal highlight streak, as on glossy vinyl or plastic."""
    px = img.load()
    rng = random.Random(seed_of(key))
    off = rng.randrange(img.width)
    for y in range(img.height):
        for x in range(img.width):
            d = abs(((x + angle * y + off) % (img.width * 2)) - img.width * 0.6)
            k = max(0.0, 1 - d / 4.0)
            if k > 0:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r + strength * k), clamp(g + strength * k), clamp(b + strength * k), a)
    return img


PIXFONT = {
    "A": ["01110", "11011", "11011", "11111", "11011", "11011", "11011"],
    "B": ["11110", "11011", "11011", "11110", "11011", "11011", "11110"],
    "D": ["11110", "11011", "11011", "11011", "11011", "11011", "11110"],
    "H": ["11011", "11011", "11011", "11111", "11011", "11011", "11011"],
    "I": ["11111", "01110", "01110", "01110", "01110", "01110", "11111"],
    "P": ["11110", "11011", "11011", "11110", "11000", "11000", "11000"],
    "R": ["11110", "11011", "11011", "11110", "11011", "11011", "11011"],
    "T": ["11111", "01110", "01110", "01110", "01110", "01110", "01110"],
    "Y": ["11011", "11011", "11011", "01110", "01110", "01110", "01110"],
}


def glyph(img, ch, x0, y0, scale, color):
    px = img.load()
    for gy, row in enumerate(PIXFONT[ch]):
        for gx, bit in enumerate(row):
            if bit == "1":
                for sy in range(scale):
                    for sx in range(scale):
                        if 0 <= x0 + gx * scale + sx < img.width and 0 <= y0 + gy * scale + sy < img.height:
                            px[x0 + gx * scale + sx, y0 + gy * scale + sy] = color


def wrap_ellipse(d, cx, cy, rx, ry, fill, size=S):
    """An ellipse drawn on a tiling texture: copies at the edges so it wraps."""
    for ox in (-size, 0, size):
        for oy in (-size, 0, size):
            d.ellipse([cx - rx + ox, cy - ry + oy, cx + rx + ox, cy + ry + oy], fill=fill)


# ============================================================ Textures: surfaces

def vinyl_textures():
    """Vinyl floor tiles, 2 x 2 to a block face, in the six party colours: 1 px darker grout, scuffs, a sheen."""
    cols = list(PARTY.values())
    for k, kind in enumerate("abcd"):
        rng = random.Random(seed_of("vinyl" + kind))
        img = Image.new("RGBA", (S, S))
        px = img.load()
        picks = []
        for ty in range(2):
            for tx in range(2):
                options = [c for c in cols if c not in picks[-1:] and (ty == 0 or c != picks[tx])]
                picks.append(rng.choice(options))
        for ty in range(2):
            for tx in range(2):
                base = rgb(picks[ty * 2 + tx])
                for y in range(16):
                    for x in range(16):
                        n = rng.uniform(-5, 5)
                        c = tuple(clamp(base[i] + n) for i in range(3)) + (255,)
                        if x == 15 or y == 15:
                            c = tint(base, 0.62)
                        elif x == 0 or y == 0:
                            c = tint(base, 1.08)
                        px[tx * 16 + x, ty * 16 + y] = c
        sheen(img, 16, "vinylsheen" + kind)
        d = ImageDraw.Draw(img)
        for _ in range(3):  # scuffs: short grey-black marks from shoes
            x, y = rng.randrange(1, S - 4), rng.randrange(1, S - 2)
            d.line([x, y, x + rng.randint(1, 3), y + rng.randint(-1, 1)], fill=(60, 56, 54, 120))
        save(img, f"vinyl-{kind}")


def racecarpet_texture():
    """Red loop-pile play carpet: race-track lanes crossing both ways, dashed yellow centre lines, two toy cars."""
    rng = random.Random(seed_of("racecarpet"))
    img = noise(0xB3201E, 7, "racecarpet")
    px = img.load()
    lane = rgb(0x8A1512)
    for y in range(S):
        for x in range(S):
            if 7 <= y <= 14 or 19 <= x <= 26:
                n = rng.uniform(-6, 6)
                px[x, y] = tuple(clamp(lane[i] + n) for i in range(3)) + (255,)
    for y in range(S):  # pile dots
        for x in range(S):
            if (x * 7 + y * 3) % 5 == 0:
                px[x, y] = tint(px[x, y], 0.9)
    d = ImageDraw.Draw(img)
    for x in range(0, S, 6):
        if not 18 <= x <= 26:
            d.line([x, 10, x + 2, 10], fill=rgb(0xE8C43A))
            d.line([x, 11, x + 2, 11], fill=rgb(0xE8C43A))
    for y in range(0, S, 6):
        if not 6 <= y <= 14:
            d.line([22, y, 22, y + 2], fill=rgb(0xE8C43A))
            d.line([23, y, 23, y + 2], fill=rgb(0xE8C43A))
    # Lane edges: a white line each side
    for y in (7, 14):
        for x in range(S):
            if not 19 <= x <= 26:
                px[x, y] = (226, 214, 204, 255)
    for x in (19, 26):
        for y in range(S):
            if not 7 <= y <= 14:
                px[x, y] = (226, 214, 204, 255)
    # Two toy cars: a blue one along the lane, a yellow one up the other
    d.rectangle([3, 8, 8, 12], fill=rgb(0x2E5FC8))
    d.rectangle([4, 9, 6, 11], fill=rgb(0x9CC4F0))
    for wx in (3, 7):
        d.point([(wx, 8), (wx, 12)], fill=(20, 20, 20, 255))
    d.rectangle([20, 21, 24, 26], fill=rgb(0xF2C232))
    d.rectangle([21, 22, 23, 23], fill=rgb(0xFFF0A8))
    for wy in (21, 26):
        d.point([(20, wy), (24, wy)], fill=(20, 20, 20, 255))
    save(img, "racecarpet")


def retrocarpet_texture():
    """Faded 1990s carpet: teal ground with pink squiggles and yellow triangles, worn pale in patches."""
    rng = random.Random(seed_of("retro"))
    img = noise(0x2A8A8C, 6, "retrocarpet")
    d = ImageDraw.Draw(img)
    for _ in range(4):
        x, y = rng.randrange(S), rng.randrange(S)
        pts = [(x + i * 2, y + (2 if i % 2 else -1)) for i in range(5)]
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.line([(p[0] + ox, p[1] + oy) for p in pts], fill=rgb(0xE868A8), width=1)
    for _ in range(4):
        x, y = rng.randrange(S), rng.randrange(S)
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.polygon([(x + ox, y + oy), (x + 4 + ox, y + 1 + oy), (x + 1 + ox, y + 4 + oy)], fill=rgb(0xF2D040))
    for _ in range(5):
        x, y = rng.randrange(S), rng.randrange(S)
        d.point((x, y), fill=rgb(0x7A3AB0))
    T.blotch(img, (rng.randrange(S), rng.randrange(S)), 9, (170, 200, 196), 0.35, seed_of("retroworn"))
    save(grain(img, 4, "retrograin"), "retrocarpet")


def checkermat_textures():
    """Foam play mats: 16 px squares in two colours with jigsaw tabs along their edges."""
    for kind, (a, b) in (("a", (0xD8443C, 0x3A6CD0)), ("b", (0xF2C83A, 0x48A85A))):
        img = Image.new("RGBA", (S, S))
        d = ImageDraw.Draw(img)
        for ty in range(2):
            for tx in range(2):
                c = a if (tx + ty) % 2 == 0 else b
                d.rectangle([tx * 16, ty * 16, tx * 16 + 15, ty * 16 + 15], fill=rgb(c))
        # Tabs: each square pokes a little knob into its right and lower neighbour
        for ty in range(2):
            for tx in range(2):
                c = a if (tx + ty) % 2 == 0 else b
                x0, y0 = tx * 16, ty * 16
                rx = (x0 + 16) % S
                d.rectangle([rx, y0 + 6, rx + 1, y0 + 9], fill=rgb(c))
                d.rectangle([rx + 1, y0 + 5, rx + 2, y0 + 10], fill=rgb(c))
                ry = (y0 + 16) % S
                d.rectangle([x0 + 6, ry, x0 + 9, ry + 1], fill=rgb(c))
                d.rectangle([x0 + 5, ry + 1, x0 + 10, ry + 2], fill=rgb(c))
        px = img.load()
        for y in range(S):  # the foam's fine texture, and a groove at the seams
            for x in range(S):
                c = px[x, y]
                if x % 16 == 0 or y % 16 == 0:
                    c = tint(c, 0.8)
                px[x, y] = tint(c, 1 + random.Random(x * 131 + y + seed_of(kind)).uniform(-0.04, 0.04))
        save(img, f"checkermat-{kind}")


PAINTS = {"orange": 0xF2A060, "sky": 0x8EC8EE, "lime": 0xB6DC78, "pink": 0xF2A8C6, "yellow": 0xF4E07C, "lilac": 0xC6B0E6}


def paint(base, key, scuffs=False):
    """Eggshell paint: a fine roller stipple, faint vertical roller laps, and scuffs at chair height on the low wall."""
    rng = random.Random(seed_of(key))
    img = noise(base, 3, key)
    px = img.load()
    for x in range(S):
        k = 1 + 0.012 * math.sin(x * 0.7 + rng.uniform(0, 6))
        for y in range(S):
            px[x, y] = tint(px[x, y], k)
    if scuffs:
        d = ImageDraw.Draw(img)
        for _ in range(4):
            x, y = rng.randrange(0, S - 5), rng.randrange(4, 12)
            d.line([x, y, x + rng.randint(2, 5), y + rng.randint(-1, 1)], fill=tint(rgb(base), 0.8)[:3] + (90,))
    return img


def brushed_brass(key, seam=False, vertical=False):
    """Brushed brass: a gradient from #B8923E to #E8C878 across the face (down it, if vertical), a 2 px specular
    band, fine horizontal brushing; seam darkens the right edge, where two leaves meet."""
    lo, hi, spec = (0xB8, 0x92, 0x3E), (0xE8, 0xC8, 0x78), (0xFA, 0xEC, 0xBC)
    rng = random.Random(seed_of(key))
    rows = [rng.uniform(-7, 7) for _ in range(S)]
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (S - 1 - y if vertical else x) / (S - 1)
            c = [lo[k] + (hi[k] - lo[k]) * t for k in range(3)]
            band = (y if vertical else x) - (8 if vertical else 22)
            if 0 <= band < 2:
                c = [c[k] + (spec[k] - c[k]) * 0.75 for k in range(3)]
            n = rows[y] * 0.6 + rng.uniform(-2.5, 2.5)
            px[x, y] = (clamp(c[0] + n), clamp(c[1] + n), clamp(c[2] + n), 255)
    if seam:
        d = ImageDraw.Draw(img)
        d.line([S - 2, 0, S - 2, S - 1], fill=rgb(0x7A5C22))
        d.line([S - 1, 0, S - 1, S - 1], fill=rgb(0x4A3612))
    return img


def skirting_texture():
    """White ceramic tile skirting: 8 px tiles with grey grout."""
    img = noise(0xF4F4F0, 2, "skirting")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.line([x, 0, x, S], fill=rgb(0xB8B8B4))
    for y in range(0, S, 8):
        d.line([0, y, S, y], fill=rgb(0xB8B8B4))
    save(img, "skirting")


def promwall_textures():
    save(paint(0xF2EAD0, "promwall"), "promwall")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    order = [PARTY["red"], PARTY["yellow"], PARTY["blue"], PARTY["green"]]
    for row in range(4):
        for col in range(4):
            c = order[(row + col) % 4]
            d.rectangle([col * 8, row * 8, col * 8 + 7, row * 8 + 7], fill=rgb(c))
    d.rectangle([0, 0, S - 1, 1], fill=rgb(0xF6F2E4))
    save(grain(img, 4, "promband"), "promband")


# ----- The murals: original cartoon figures, flat-shaded with black outlines, on sunshine yellow

MURAL_BG = (243, 226, 122)
INK = (24, 20, 20, 255)


def mural(subject):
    k = 4
    W = 64 * k

    def draw(d, k_, img):
        d.rectangle([0, 0, W, W], fill=MURAL_BG + (255,))
        o = 2 * k  # outline width
        def E(box, fill):
            d.ellipse([v * k for v in box], fill=fill, outline=INK, width=o)
        def P(pts, fill):
            d.polygon([(x * k, y * k) for x, y in pts], fill=fill, outline=INK, width=o)
        def R(box, fill, r=0):
            d.rounded_rectangle([v * k for v in box], radius=r * k, fill=fill, outline=INK, width=o)
        def L(pts, width=2, fill=INK):
            d.line([(x * k, y * k) for x, y in pts], fill=fill, width=width * k, joint="curve")
        if subject == "mouse":
            # A grey mouse in a green jumper and orange trousers, holding up a red cup
            grey, pink = (150, 152, 160, 255), (240, 168, 176, 255)
            R((22, 44, 30, 58), (236, 120, 40, 255), 2); R((34, 44, 42, 58), (236, 120, 40, 255), 2)   # trouser legs
            E((18, 56, 31, 62), INK); E((33, 56, 46, 62), INK)                                           # shoes
            R((20, 28, 44, 48), (60, 160, 80, 255), 6)                                                   # jumper
            L([(43, 40), (52, 36), (54, 28)], 3, (60, 160, 80, 255))                                     # arm up
            R((49, 18, 59, 28), (210, 40, 40, 255), 1)                                                   # the cup
            d.rectangle([50 * k, 19 * k, 58 * k, 21 * k], fill=(255, 255, 255, 140))
            L([(21, 34), (15, 42)], 3, (60, 160, 80, 255))
            E((12, 41, 18, 47), grey)                                                                    # hand
            E((14, 4, 26, 16), grey); E((38, 4, 50, 16), grey)                                           # ears
            E((17, 7, 23, 13), pink); E((41, 7, 47, 13), pink)
            E((20, 8, 44, 32), grey)                                                                     # head
            E((26, 15, 30, 21), (255, 255, 255, 255)); E((34, 15, 38, 21), (255, 255, 255, 255))
            E((27, 17, 29, 20), INK); E((35, 17, 37, 20), INK)
            E((30, 22, 34, 26), INK)                                                                     # nose
            d.arc([26 * k, 21 * k, 38 * k, 29 * k], 20, 160, fill=INK, width=o)
            L([(44, 50), (52, 46), (56, 50)], 2)                                                         # tail
        elif subject == "hotdog":
            # A grinning yellow man in a white vest and blue jeans, a hot dog in his hand
            yellow = (250, 214, 60, 255)
            R((22, 42, 31, 58), (50, 90, 170, 255), 1); R((33, 42, 42, 58), (50, 90, 170, 255), 1)
            E((19, 56, 32, 62), (90, 60, 40, 255)); E((32, 56, 45, 62), (90, 60, 40, 255))
            R((21, 26, 43, 44), (250, 250, 250, 255), 3)
            L([(22, 30), (13, 38), (12, 46)], 4, yellow)
            L([(42, 30), (50, 36), (52, 30)], 4, yellow)
            # The hot dog: bun, sausage, a squiggle of mustard
            R((44, 23, 62, 30), (220, 160, 80, 255), 3)
            R((42, 24, 63, 28), (190, 70, 50, 255), 2)
            L([(45, 25), (48, 27), (51, 25), (54, 27), (57, 25), (60, 27)], 1, (250, 220, 40, 255))
            E((20, 4, 44, 28), yellow)
            E((25, 11, 30, 17), (255, 255, 255, 255)); E((34, 11, 39, 17), (255, 255, 255, 255))
            E((27, 13, 29, 16), INK); E((36, 13, 38, 16), INK)
            d.chord([24 * k, 12 * k, 40 * k, 26 * k], 10, 170, fill=(150, 30, 40, 255), outline=INK, width=o)
            d.rectangle([27 * k, 19 * k, 37 * k, 20.5 * k], fill=(255, 255, 255, 255))
            L([(26, 6), (30, 3), (33, 6), (37, 2), (40, 6)], 2)                                         # a tuft of hair
        elif subject == "cheese":
            # An orange cheese block with arms and legs, kicking a football
            orange = (246, 168, 40, 255)
            L([(26, 44), (24, 56)], 3); L([(36, 44), (46, 50)], 3)
            E((19, 54, 29, 60), (200, 40, 40, 255)); E((44, 46, 54, 52), (200, 40, 40, 255))
            P([(14, 20), (46, 12), (50, 44), (16, 46)], orange)
            P([(14, 20), (46, 12), (40, 8), (12, 14)], (252, 196, 80, 255))
            for hx, hy, r in ((21, 39, 3), (42, 19, 2), (43, 37, 2), (33, 41, 1.5)):
                E((hx - r, hy - r, hx + r, hy + r), (210, 130, 30, 255))
            E((22, 23, 27, 28), (255, 255, 255, 255)); E((32, 21, 37, 26), (255, 255, 255, 255))
            E((24, 24, 26, 27), INK); E((34, 22, 36, 25), INK)
            d.arc([22 * k, 26 * k, 36 * k, 36 * k], 20, 160, fill=INK, width=o)
            L([(15, 30), (6, 24)], 2); L([(48, 26), (56, 20)], 2)
            E((50, 48, 62, 60), (250, 250, 250, 255))                                                   # the football
            for bx_, by_ in ((55, 53), (52, 50), (58, 50), (53, 57), (58, 57)):
                d.regular_polygon(((bx_ + 0.5) * k, (by_ + 0.5) * k, 1.6 * k), 5, fill=INK)
            L([(58, 46), (61, 44)], 1); L([(60, 48), (63, 47)], 1)
        elif subject == "stork":
            # A pink stork in a dark jacket and a top hat, on long legs
            pink = (244, 150, 180, 255)
            L([(28, 44), (26, 61)], 2, (230, 120, 60, 255)); L([(34, 44), (37, 61)], 2, (230, 120, 60, 255))
            L([(22, 61), (30, 61)], 2, (230, 120, 60, 255)); L([(34, 61), (42, 61)], 2, (230, 120, 60, 255))
            E((17, 25, 45, 48), pink)
            P([(18, 32), (28, 27), (30, 47), (20, 45)], (40, 44, 70, 255))                               # jacket
            P([(34, 27), (44, 32), (42, 45), (32, 47)], (40, 44, 70, 255))
            P([(29, 28), (33, 28), (31, 38)], (250, 250, 250, 255))
            d.regular_polygon((31 * k, 30 * k, 2 * k), 3, fill=(200, 30, 40, 255))                      # bow tie
            L([(30, 27), (32, 20), (31, 14)], 4, pink)                                                  # neck
            E((24, 6, 38, 18), pink)
            P([(37, 11), (58, 14), (37, 15)], (240, 150, 50, 255))                                       # beak
            E((30, 9, 34, 13), (255, 255, 255, 255)); E((31, 10, 33, 12), INK)
            R((24, 0, 36, 7), (30, 30, 34, 255), 1); R((21, 6, 39, 8), (30, 30, 34, 255), 1)              # top hat
            d.rectangle([24 * k + o, 4 * k, 36 * k - o, 5 * k], fill=(200, 30, 40, 255))
            L([(20, 34), (10, 30)], 3, pink); L([(43, 34), (52, 40)], 3, pink)                           # wings as arms
        # A few stray brush marks so it reads as paint on a wall
        rng = random.Random(seed_of("mural" + subject))
        for _ in range(6):
            x, y = rng.randrange(W), rng.randrange(W)
            d.line([x, y, x + rng.randint(4, 14), y + rng.randint(-2, 2)], fill=(232, 212, 110, 255), width=k)

    img = supersample(64, 64, k, draw, MURAL_BG + (255,))
    grain(img, 3, "muralgrain" + subject)
    for name_, (x0, y0) in (("tl", (0, 0)), ("tr", (32, 0)), ("bl", (0, 32)), ("br", (32, 32))):
        save(img.crop((x0, y0, x0 + 32, y0 + 32)), f"mural-{subject}-{name_}")
    save(paint(0xF3E27A, "muralwall"), "muralwall")


def hull_textures():
    """White ship paint over steel plate: a seam, rows of rivets every 8 px, rust weeping from two of them."""
    rng = random.Random(seed_of("hull"))
    img = noise(0xEEEEE8, 3, "hull")
    px = img.load()
    d = ImageDraw.Draw(img)
    d.line([0, 15, S, 15], fill=rgb(0xC8C8C2))
    d.line([0, 16, S, 16], fill=rgb(0xFAFAF6))
    rivets = []
    for y in (3, 19, 28):
        for x in range(4, S, 8):
            d.point((x, y), fill=rgb(0xB0B0AA))
            d.point((x - 1, y - 1), fill=rgb(0xFFFFFF))
            rivets.append((x, y))
    for x, y in rng.sample(rivets, 2):  # rust weeping down from a rivet
        for yy in range(y + 1, min(S, y + rng.randint(6, 12))):
            a = 1 - (yy - y) / 12
            for xx in (x, x + (1 if rng.random() < 0.3 else 0)):
                c = px[xx % S, yy]
                px[xx % S, yy] = mixc(c, (150, 80, 40), 0.55 * a)
        px[x, y] = (120, 60, 30, 255)
    save(img, "hull")
    save(noise(0xB89040, 7, "brass"), "brass")
    img = flat(0x0B1018)
    d = ImageDraw.Draw(img)
    d.line([6, 24, 22, 8], fill=(40, 52, 66, 255), width=3)
    d.line([12, 26, 26, 12], fill=(26, 34, 44, 255), width=1)
    save(img, "portholeglass")


def steel_textures():
    img = noise(0x7B8288, 5, "funsteel")
    d = ImageDraw.Draw(img)
    for y in (2, 29):
        for x in range(3, S, 6):
            d.point((x, y), fill=rgb(0x5A6066))
            d.point((x, y - 1), fill=rgb(0xA0A6AC))
    rng = random.Random(seed_of("steelscuff"))
    for _ in range(5):
        x, y = rng.randrange(S), rng.randrange(S)
        d.line([x, y, x + rng.randint(2, 6), y + rng.randint(-1, 1)], fill=rgb(0x9AA0A6))
    save(img, "steel")
    sign = flat(0xE8C030, 64)
    d = ImageDraw.Draw(sign)
    for x in range(-64, 64, 10):  # hazard edge
        d.polygon([(x, 0), (x + 5, 0), (x + 13, 8), (x + 8, 8)], fill=(30, 30, 30, 255))
        d.polygon([(x, 56), (x + 5, 56), (x + 13, 64), (x + 8, 64)], fill=(30, 30, 30, 255))
    text(sign, "CREW", (4, 12, 60, 32), 0x1A1A1A, 15)
    text(sign, "ONLY", (4, 32, 60, 52), 0x1A1A1A, 15)
    save(grain(sign, 6, "crewsign"), "crewonly")


def deck_textures():
    rng = random.Random(seed_of("deck"))
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for p in range(4):
        base = rgb(0x9A6A3E)
        f = rng.uniform(0.9, 1.08)
        for y in range(p * 8, p * 8 + 8):
            for x in range(S):
                grain_ = math.sin(x * 0.9 + p * 3 + 2 * math.sin(y * 0.6)) * 6
                n = rng.uniform(-5, 5)
                c = tuple(clamp(base[i] * f + grain_ + n) for i in range(3)) + (255,)
                if y == p * 8 + 7:
                    c = (24, 20, 16, 255)  # black caulk
                if rng.random() < 0.05:
                    c = mixc(c, (214, 204, 186), 0.5)  # salt bleaching
                px[x, y] = c
        jx = (p * 13 + 5) % S  # a butt joint in each plank
        for y in range(p * 8, p * 8 + 7):
            px[jx, y] = (40, 30, 22, 255)
    save(img, "deckplank")
    img = flat(0x05070B)
    px = img.load()
    for x, y, v in ((5, 9, 70), (21, 3, 55), (26, 24, 80)):
        px[x, y] = (v, v, v + 10, 255)
    save(img, "nightvoid")


def parquet_texture():
    """Chevron parquet in honey-coloured wood: columns of short planks laid on the slant, each column the other way."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed_of("parquet"))
    tones = [rng.uniform(0.86, 1.1) for _ in range(64)]
    for y in range(S):
        for x in range(S):
            col, u = x // 8, x % 8
            t = (y + u) if col % 2 == 0 else (y + 7 - u)
            plank = (t // 4) % 16 + col * 16
            base = (204, 152, 86)
            k = tones[plank % 64]
            n = math.sin((u + y) * 1.7 + plank) * 5 + rng.uniform(-3, 3)
            c = tuple(clamp(b * k + n) for b in base) + (255,)
            if t % 4 == 0 or u == 0:
                c = tint(c, 0.66)
            px[x, y] = c
    save(img, "parquet")


def lobbycarpet_texture():
    img = noise(0x6E1018, 5, "lobbycarpet")
    d = ImageDraw.Draw(img)
    gold = rgb(0xC8A040)
    for cx, cy in ((8, 8), (24, 24)):
        d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], outline=gold)
        d.point((cx, cy), fill=gold)
    for cx, cy in ((24, 8), (8, 24)):
        d.polygon([(cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)], fill=tint(gold, 0.85))
    save(grain(img, 3, "lobbygrain"), "lobbycarpet")


def surface_textures():
    vinyl_textures()
    racecarpet_texture()
    retrocarpet_texture()
    checkermat_textures()
    for c, base in PAINTS.items():
        save(paint(base, "paint" + c), f"paint-{c}")
        save(paint(base, "paintlow" + c, scuffs=True), f"paint-{c}-low")
    skirting_texture()
    promwall_textures()
    for subject in ("mouse", "hotdog", "cheese", "stork"):
        mural(subject)
    hull_textures()
    steel_textures()
    deck_textures()
    parquet_texture()
    lobbycarpet_texture()


# ============================================================ Textures: props

BALLOONS = {"red": 0xD8202C, "yellow": 0xF4CC30, "blue": 0x2E6CD8, "green": 0x3AAE54, "pink": 0xF07AB4, "orange": 0xF2842C,
            "purple": 0x8A4CC8, "white": 0xF2F0EC,
            "pastelpink": 0xF8C4D8, "mint": 0xB4E8CC, "babyblue": 0xB4D4F4, "lemon": 0xF8EC9C, "lilac": 0xD8C4F0}
GOLD = 0xD8A838


def latex(colour, key):
    """Balloon latex: round shading toward the edges and a soft white highlight high on the left, stretched over a face."""
    base = rgb(colour)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dx, dy = (x - 15.5) / 16, (y - 15.5) / 16
            r = math.sqrt(dx * dx + dy * dy)
            k = 1.08 - 0.32 * r * r
            c = tint(base, k)
            hx, hy = (x - 10) / 5.5, (y - 9) / 4.5
            h = max(0.0, 1 - (hx * hx + hy * hy))
            px[x, y] = mixc(c, (255, 255, 255), 0.75 * h * h)
    return img


def crepe(c1, key):
    """Crepe paper: fine crinkles running along the band."""
    rng = random.Random(seed_of(key))
    img = noise(c1, 4, key)
    px = img.load()
    for x in range(S):
        k = 1 + 0.07 * math.sin(x * 2.1 + rng.uniform(0, 1))
        for y in range(S):
            px[x, y] = tint(px[x, y], k)
    return img


def pennant(colour, letter=None):
    """A pennant hanging point-down: a cut-out triangle, white letter on the middle one."""
    img = clear()
    d = ImageDraw.Draw(img)
    d.polygon([(0, 0), (31, 0), (16, 31)], fill=rgb(colour))
    d.line([(0, 0), (31, 0)], fill=tint(rgb(colour), 0.8), width=2)
    if letter:
        glyph(img, letter, 9, 4, 3, (255, 255, 255, 255))
    return grain(img, 4, f"pennant{colour}{letter}")


def round_tex(fill, rim=None, rim_w=3, key="round", inner=None, size=S):
    """Something round seen from above, cut out of the square on alpha: a plate, a cookie, a board."""
    def draw(d, k, img):
        d.ellipse([0, 0, size * k - 1, size * k - 1], fill=rgb(rim if rim is not None else fill))
        if rim is not None:
            w = rim_w * k
            d.ellipse([w, w, size * k - 1 - w, size * k - 1 - w], fill=rgb(fill))
        if inner:
            inner(d, k)
    return harden(supersample(size, size, 4, draw))


def gift_paper(colour, pattern, key):
    img = noise(colour, 3, key)
    d = ImageDraw.Draw(img)
    light = tint(rgb(colour), 1.35)
    if pattern == "stripes":
        for x in range(-S, S, 8):
            d.polygon([(x, 0), (x + 3, 0), (x + 3 + S, S), (x + S, S)], fill=light)
    elif pattern == "dots":
        for y in range(2, S, 8):
            for x in range(2 + (4 if (y // 8) % 2 else 0), S, 8):
                d.ellipse([x, y, x + 3, y + 3], fill=(250, 250, 246, 255))
    elif pattern == "stars":
        for cx, cy in ((7, 7), (23, 9), (14, 21), (28, 26), (4, 27)):
            pts = [(cx + 3.5 * math.cos(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45),
                    cy - 3.5 * math.sin(math.pi / 2 + i * math.pi / 5) * (1 if i % 2 == 0 else 0.45)) for i in range(10)]
            d.polygon(pts, fill=rgb(0xF4D040))
    return sheen(img, 10, key + "sh")


def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("arialbd.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def hand(img, x0, y0, colour):
    """A red handprint pressed onto paper, smeared a little downward."""
    d = ImageDraw.Draw(img)
    c = colour + (225,)
    d.ellipse([x0, y0 + 4, x0 + 9, y0 + 13], fill=c)
    for dx, l in ((0, 6), (2.5, 8), (5, 8), (7.5, 6)):
        d.line([x0 + 1 + dx, y0 + 5, x0 + 1 + dx, y0 + 5 - l], fill=c, width=2)
    d.line([x0 + 9, y0 + 9, x0 + 12, y0 + 5], fill=c, width=2)
    for i in range(3):
        d.line([x0 + 2 + i * 3, y0 + 13, x0 + 2 + i * 3, y0 + 16 + i], fill=colour + (160,), width=1)


def poster_time4fun():
    """The canon poster, redrawn: an orange clock, "4 Fun =)" in four colours, a rainbow banner, and a red handprint."""
    k = 4

    def draw(d, k_, img):
        d.rectangle([0, 0, 64 * k, 64 * k], fill=(252, 246, 228, 255))
        for i, c in enumerate([(230, 50, 50), (246, 150, 40), (246, 214, 50), (70, 180, 80), (60, 120, 220), (140, 80, 200)]):
            d.arc([-8 * k, 34 * k + i * 3 * k, 72 * k, 100 * k + i * 3 * k], 180, 360, fill=c + (255,), width=3 * k)
        d.ellipse([18 * k, 6 * k, 46 * k, 34 * k], fill=(246, 140, 30, 255), outline=(40, 30, 30, 255), width=2 * k)
        d.ellipse([22 * k, 10 * k, 42 * k, 30 * k], fill=(255, 250, 236, 255))
        for a in range(12):
            ang = a * math.pi / 6
            d.line([32 * k + 8 * k * math.cos(ang), 20 * k + 8 * k * math.sin(ang), 32 * k + 9.5 * k * math.cos(ang), 20 * k + 9.5 * k * math.sin(ang)],
                   fill=(40, 30, 30, 255), width=k)
        d.line([32 * k, 20 * k, 32 * k, 13 * k], fill=(40, 30, 30, 255), width=2 * k)
        d.line([32 * k, 20 * k, 37 * k, 22 * k], fill=(40, 30, 30, 255), width=2 * k)
        d.text((4 * k, 2 * k), "TIME", fill=(40, 30, 30, 255), font=_font(8 * k))
        x = 6 * k
        f = _font(14 * k)
        for ch, c in zip("4 Fun =)", [(230, 50, 50), None, (60, 120, 220), (70, 180, 80), (246, 160, 30), None, (230, 50, 50), (230, 50, 50)]):
            if c:
                d.text((x, 41 * k), ch, fill=c + (255,), font=f, stroke_width=k // 2, stroke_fill=(40, 30, 30, 255))
            x += f.getlength(ch)
    img = supersample(64, 64, k, draw)
    hand(img, 47, 10, (176, 14, 20))
    return grain(img, 3, "t4f")


def directory_board():
    """The ship's directory in a lobby: white letters pressed into a navy felt letter board, DECK 4 in gold, the ways
    to everything, and a red YOU ARE HERE =)."""
    k = 4
    rows = [("PARTY ROOMS", ">"), ("BALL PIT", "<"), ("BOUNCE HALL", "^"), ("ARCADE", "v"), ("KITCHEN", ">"),
            ("LIDO DECK", "^"), ("GUEST SVCS", "X")]

    def draw(d, k_, img):
        d.rectangle([0, 0, 56 * k, 72 * k], fill=(28, 34, 50, 255))
        for y in range(19, 66, 3):  # the felt's grooves
            d.line([2 * k, y * k, 54 * k, y * k], fill=(36, 44, 62, 255), width=k // 2)
        d.text((28 * k, 7 * k), "DECK 4", fill=(232, 196, 96, 255), font=_font(10 * k), anchor="mm")
        d.text((28 * k, 14.5 * k), "DIRECTORY", fill=(236, 232, 220, 255), font=_font(5 * k), anchor="mm")
        d.line([4 * k, 18 * k, 52 * k, 18 * k], fill=(200, 160, 70, 255), width=k)
        f = _font(5 * k)
        for i, (label, arrow) in enumerate(rows):
            y = (22.5 + i * 5.6) * k
            d.text((4 * k, y), label, fill=(236, 232, 220, 255), font=f, anchor="lm")
            d.text((52 * k, y), arrow, fill=(236, 232, 220, 255), font=f, anchor="rm")
        d.ellipse([4 * k, 63.5 * k, 8 * k, 67.5 * k], fill=(214, 40, 40, 255))
        d.text((10 * k, 65.5 * k), "YOU ARE HERE =)", fill=(230, 60, 60, 255), font=_font(int(4.4 * k)), anchor="lm")
    return grain(supersample(56, 72, k, draw), 3, "fundirectory")


def poster_happybday():
    k = 4

    def draw(d, k_, img):
        d.rectangle([0, 0, 64 * k, 64 * k], fill=(120, 196, 236, 255))
        for cx, cy, c in ((12, 16, (230, 50, 60)), (24, 11, (246, 210, 50)), (40, 13, (80, 190, 90)), (52, 17, (150, 90, 210))):
            d.line([cx * k, (cy + 7) * k, (cx + 2) * k, 34 * k], fill=(250, 250, 250, 255), width=k // 2)
            d.ellipse([(cx - 5) * k, (cy - 7) * k, (cx + 5) * k, (cy + 7) * k], fill=c + (255,), outline=(40, 30, 30, 255), width=k)
            d.ellipse([(cx - 3) * k, (cy - 5) * k, (cx - 1) * k, (cy - 2) * k], fill=(255, 255, 255, 200))
        d.text((32 * k, 42 * k), "HAPPY", fill=(250, 60, 120, 255), font=_font(13 * k), anchor="mm", stroke_width=k, stroke_fill=(255, 255, 255, 255))
        d.text((32 * k, 55 * k), "BIRTHDAY", fill=(250, 140, 30, 255), font=_font(11 * k), anchor="mm", stroke_width=k, stroke_fill=(255, 255, 255, 255))
    return grain(supersample(64, 64, k, draw), 3, "hbd")


def poster_comejoin():
    k = 4

    def draw(d, k_, img):
        d.rectangle([0, 0, 64 * k, 64 * k], fill=(250, 226, 90, 255))
        # Three smiling yellow guests in party hats, one with a red balloon
        for i, cx in enumerate((14, 32, 50)):
            d.ellipse([(cx - 5) * k, 16 * k, (cx + 5) * k, 26 * k], fill=(246, 214, 70, 255), outline=(40, 30, 30, 255), width=k)
            d.arc([(cx - 3) * k, 18 * k, (cx + 3) * k, 24 * k], 20, 160, fill=(180, 20, 30, 255), width=k)
            d.rectangle([(cx - 4) * k, 26 * k, (cx + 4) * k, 40 * k], fill=(246, 214, 70, 255), outline=(40, 30, 30, 255), width=k)
            d.polygon([((cx - 4) * k, 16 * k), (cx * k, 7 * k), ((cx + 4) * k, 16 * k)], fill=[(230, 60, 140), (60, 150, 230), (90, 190, 90)][i] + (255,))
        d.line([56 * k, 30 * k, 60 * k, 8 * k], fill=(60, 60, 60, 255), width=k // 2)
        d.ellipse([56 * k, 0, 64 * k, 9 * k], fill=(210, 30, 40, 255))
        d.text((32 * k, 50 * k), "COME JOIN US", fill=(210, 40, 60, 255), font=_font(9 * k), anchor="mm")
        d.text((32 * k, 59 * k), "=)", fill=(210, 40, 60, 255), font=_font(9 * k), anchor="mm")
    return grain(supersample(64, 64, k, draw), 3, "cju")


def smiley(kind):
    """Red paint daubed on a wall by hand: a "=)" with drips, or COME JOIN US =)."""
    k = 4
    rng = random.Random(seed_of("smiley" + kind))

    def draw(d, k_, img):
        red = (168, 14, 18, 235)
        if kind == "4":
            d.text((32 * k, 22 * k), "COME JOIN", fill=red, font=_font(12 * k), anchor="mm")
            d.text((32 * k, 38 * k), "US =)", fill=red, font=_font(12 * k), anchor="mm")
            for _ in range(6):
                x = rng.randrange(8, 56)
                d.line([x * k, 28 * k, x * k, (28 + rng.randint(4, 14)) * k], fill=red, width=k)
            return
        size = {"1": 34, "2": 46, "3": 26}[kind]
        cx, cy = 32 + rng.randint(-3, 3), 30
        d.text((cx * k, cy * k), "=)", fill=red, font=_font(size * k), anchor="mm")
        for _ in range(6):  # paint running down from the strokes
            x = cx + rng.uniform(-size * 0.4, size * 0.3)
            y0_ = cy + rng.uniform(0, size * 0.25)
            d.line([x * k, y0_ * k, x * k, (y0_ + rng.uniform(4, 14)) * k], fill=red, width=max(1, int(k * 0.9)))
            d.ellipse([(x - 0.8) * k, (y0_ + 13) * k, (x + 0.8) * k, (y0_ + 14.6) * k], fill=red) if rng.random() < 0.3 else None
    return supersample(64, 64, k, draw)


def bulb(c):
    img = flat(c)
    d = ImageDraw.Draw(img)
    d.ellipse([8, 6, 18, 16], fill=mixc(rgb(c), (255, 255, 255), 0.6))
    return img


def inflatable(colour, key):
    img = noise(colour, 3, key)
    d = ImageDraw.Draw(img)
    d.line([0, 0, S, 0], fill=tint(rgb(colour), 0.72))
    d.line([0, 16, S, 16], fill=tint(rgb(colour), 0.78))
    for x in range(0, S, 8):  # stitching
        d.point((x, 1), fill=tint(rgb(colour), 0.6))
    return sheen(img, 22, key + "sh", angle=0)


def gym_doors():
    """Green-painted gym doors with a small square window, and the mascots painted on them: a tiger, a parrot, a giraffe."""
    k = 4

    def leaf(part, side):
        def draw(d, k_, img):
            d.rectangle([0, 0, 32 * k, 32 * k], fill=(46, 122, 68, 255))
            d.rectangle([0, 0, 32 * k - 1, 32 * k - 1], outline=(30, 80, 46, 255), width=k)
            ink = (30, 24, 20, 255)
            if part == "upper":
                d.rectangle([10 * k, 3 * k, 22 * k, 13 * k], fill=(170, 200, 210, 255), outline=(200, 200, 200, 255), width=k)
                d.line([10 * k, 8 * k, 22 * k, 8 * k], fill=(120, 120, 120, 255), width=k // 2)
                if side == "l":  # the parrot, perched under the window
                    d.ellipse([10 * k, 17 * k, 20 * k, 30 * k], fill=(220, 40, 40, 255), outline=ink, width=k)
                    d.ellipse([16 * k, 15 * k, 23 * k, 22 * k], fill=(220, 40, 40, 255), outline=ink, width=k)
                    d.polygon([(22 * k, 17 * k), (26 * k, 19 * k), (22 * k, 21 * k)], fill=(240, 200, 60, 255), outline=ink)
                    d.ellipse([18 * k, 17 * k, 20 * k, 19 * k], fill=(255, 255, 255, 255))
                    d.polygon([(10 * k, 22 * k), (6 * k, 31 * k), (13 * k, 29 * k)], fill=(40, 120, 220, 255), outline=ink)
                    d.polygon([(12 * k, 21 * k), (17 * k, 28 * k), (11 * k, 29 * k)], fill=(250, 210, 50, 255))
                else:  # the giraffe's neck and head
                    d.rectangle([14 * k, 19 * k, 19 * k, 32 * k], fill=(240, 196, 80, 255), outline=ink, width=k)
                    d.ellipse([11 * k, 15 * k, 23 * k, 22 * k], fill=(240, 196, 80, 255), outline=ink, width=k)
                    d.line([14 * k, 16 * k, 13 * k, 13 * k], fill=ink, width=k)
                    d.line([19 * k, 16 * k, 20 * k, 13 * k], fill=ink, width=k)
                    d.ellipse([15 * k, 17 * k, 17 * k, 19 * k], fill=ink)
                    for sy in (23, 27):
                        d.ellipse([15 * k, sy * k, 18 * k, (sy + 2) * k], fill=(170, 100, 40, 255))
            else:
                if side == "l":  # the tiger's face
                    d.ellipse([7 * k, 10 * k, 25 * k, 28 * k], fill=(246, 140, 30, 255), outline=ink, width=k)
                    d.ellipse([7 * k, 8 * k, 12 * k, 13 * k], fill=(246, 140, 30, 255), outline=ink, width=k)
                    d.ellipse([20 * k, 8 * k, 25 * k, 13 * k], fill=(246, 140, 30, 255), outline=ink, width=k)
                    for x0 in (9, 13, 19, 23):
                        d.line([x0 * k, 11 * k, (x0 + (1 if x0 < 16 else -1)) * k, 15 * k], fill=ink, width=k)
                    d.ellipse([11 * k, 16 * k, 14 * k, 19 * k], fill=(255, 255, 255, 255))
                    d.ellipse([18 * k, 16 * k, 21 * k, 19 * k], fill=(255, 255, 255, 255))
                    d.ellipse([14 * k, 21 * k, 18 * k, 24 * k], fill=(250, 240, 230, 255))
                    d.polygon([(15 * k, 21 * k), (17 * k, 21 * k), (16 * k, 23 * k)], fill=ink)
                    d.arc([12 * k, 21 * k, 20 * k, 26 * k], 20, 160, fill=ink, width=k)
                else:  # the giraffe's body and legs
                    d.ellipse([6 * k, 2 * k, 26 * k, 16 * k], fill=(240, 196, 80, 255), outline=ink, width=k)
                    for lx in (8, 12, 19, 23):
                        d.rectangle([lx * k, 13 * k, (lx + 2) * k, 29 * k], fill=(240, 196, 80, 255), outline=ink, width=k)
                    for sx, sy in ((10, 6), (16, 4), (20, 9), (13, 10)):
                        d.ellipse([sx * k, sy * k, (sx + 4) * k, (sy + 3) * k], fill=(170, 100, 40, 255))
        return grain(supersample(32, 32, k, draw), 3, f"gym{part}{side}")
    for part in ("lower", "upper"):
        for side in ("l", "r"):
            save(leaf(part, side), f"gymdoor-{side}-{part}")


def prop_textures():
    for c, h in BALLOONS.items():
        save(latex(h, "latex" + c), f"latex-{c}")
    save(noise(0xF0EEE8, 3, "balloonstring"), "balloonstring")
    save(noise(0xE8BA38, 6, "curlyribbon"), "curlyribbon")
    for c in ("red", "yellow", "blue", "green", "purple"):
        save(crepe(PARTY[c], "crepe" + c), f"crepe-{c}")
    save(crepe(0xF07AB4, "crepepink"), "crepe-pink")
    for c in ("red", "yellow", "green", "purple"):
        save(pennant(PARTY[c]), f"pennant-{c}")
    for ch in "HAPYBIRTD":
        save(pennant(PARTY["blue"], ch), f"pennant-letter-{ch.lower()}")
    save(noise(0x30302C, 3, "buntingstring"), "buntingstring")

    # Tablecloths: plastic, with a crease grid from being folded in the packet
    for kind in ("blue", "greenstripe", "pink", "yellow", "redcheck"):
        if kind == "greenstripe":
            img = flat(0xF6F6F0)
            d = ImageDraw.Draw(img)
            for x in range(0, S, 8):
                d.rectangle([x, 0, x + 3, S], fill=rgb(0x4CAF6A))
        elif kind == "redcheck":
            img = flat(0xF8F4F0)
            px = img.load()
            for y in range(S):
                for x in range(S):
                    a, b = (x // 4) % 2, (y // 4) % 2
                    px[x, y] = (rgb(0xC8282C) if a and b else rgb(0xE48A88) if a or b else (248, 244, 240, 255))
        else:
            img = noise({"blue": 0x3C7DD9, "pink": 0xF29AC0, "yellow": 0xF2D050}[kind], 3, "cloth" + kind)
        d = ImageDraw.Draw(img)
        for v in (10, 21):
            d.line([v, 0, v, S], fill=tint(img.getpixel((v, 3)), 0.9))
            d.line([0, v, S, v], fill=tint(img.getpixel((3, v)), 0.92))
        save(sheen(img, 14, "clothsheen" + kind), f"cloth-{kind}")
    save(noise(0xF4F4EE, 2, "whiteplastic"), "whiteplastic")
    save(noise(0xB8BEC4, 4, "steeltube"), "steeltube")
    save(noise(0xD8DDE2, 3, "chrome"), "chrome")
    for c, h in (("yellow", 0xF2C641), ("blue", 0x3C7DD9)):
        save(round_tex(0xFAFAF6, h, 3, "plate" + c), f"plate-{c}")
    save(round_tex(0xFAFAF6, 0xE0E0DA, 2, "plateplain"), "plate-plain")
    save(noise(0xF6F6F2, 2, "paperwhite"), "paperwhite")
    save(noise(0xF08A3C, 3, "cuporange"), "cup-orange")
    img = noise(0xF4B8CC, 2, "napkin")
    ImageDraw.Draw(img).line([0, 16, S, 16], fill=rgb(0xE098B0))
    save(img, "napkin")
    stain = clear()
    d = ImageDraw.Draw(stain)
    rng = random.Random(seed_of("stain"))
    for _ in range(9):
        x, y, r = rng.randrange(6, 26), rng.randrange(6, 26), rng.randint(2, 6)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(120, 10, 16, 210))
    save(stain, "stain")
    conf = clear()
    px = conf.load()
    rng = random.Random(seed_of("confetti"))
    cols = list(PARTY.values()) + [0xFFFFFF, 0xF07AB4]
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        c = rgb(rng.choice(cols))
        px[x, y] = c
        if rng.random() < 0.5:
            px[(x + 1) % S, y] = c
    save(conf, "confetti")

    # Cake: frosting, sponge, the velvet's red crumb with its cream layer, a silver board, striped candles, flames
    save(noise(0xFAF6EE, 2, "frosting"), "frosting")
    save(noise(0xF8DCE0, 2, "frostingpink"), "frosting-pink")
    side = noise(0xFAF6EE, 2, "frostingside")
    d = ImageDraw.Draw(side)
    for x in range(0, S, 5):  # a ridged comb pattern round the side
        d.line([x, 0, x, S], fill=rgb(0xECE6DA))
    d.rectangle([0, 26, S, S], fill=rgb(0xF4B8CC))  # a piped pink band at the foot
    save(side, "frosting-side")
    side = noise(0xF8DCE0, 2, "frostingpinkside")
    d = ImageDraw.Draw(side)
    for x in range(0, S, 5):
        d.line([x, 0, x, S], fill=rgb(0xEECAD0))
    save(side, "frosting-pink-side")
    img = noise(0xEAC878, 7, "sponge")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("spongeholes"))
    for _ in range(18):
        x, y = rng.randrange(S), rng.randrange(S)
        d.point((x, y), fill=rgb(0xC8A050))
    d.rectangle([0, 14, S, 17], fill=rgb(0xE84A6A))  # a jam layer
    save(img, "sponge")
    img = noise(0x7A1420, 7, "velvetsponge")
    d = ImageDraw.Draw(img)
    for _ in range(14):
        x, y = rng.randrange(S), rng.randrange(S)
        d.point((x, y), fill=rgb(0x4A0810))
    d.rectangle([0, 14, S, 17], fill=rgb(0xF4ECE4))  # cream cheese layer
    save(img, "velvet")
    save(round_tex(0xD8DCE0, 0xB8BEC4, 2, "cakeboard"), "cakeboard")
    for c, h in (("pink", 0xF07AB4), ("blue", 0x3C7DD9), ("green", 0x4CAF6A), ("yellow", 0xF2C641)):
        img = flat(0xFAFAF4)
        d = ImageDraw.Draw(img)
        for y in range(-S, S, 8):
            d.polygon([(0, y), (S, y + S // 2), (S, y + S // 2 + 3), (0, y + 3)], fill=rgb(h))
        save(img, f"candle-{c}")
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = y / S
            px[x, y] = (255, clamp(250 - 120 * t), clamp(170 - 160 * t), 255)
    save(img, "flame")
    save(noise(0xC8141E, 2, "piping"), "piping")
    save(noise(0xF8F0F2, 2, "beads"), "beads")
    save(noise(0xF07AB4, 2, "beadspink"), "beads-pink")
    save(noise(0xC0C6CC, 4, "knifeblade"), "knifeblade")
    save(noise(0x7A1420, 8, "crumbs"), "crumbs")

    def cookie_face(d, k):
        rng_ = random.Random(seed_of("chips"))
        for _ in range(7):
            x, y = rng_.uniform(6, 26) * k, rng_.uniform(6, 26) * k
            d.ellipse([x - 1.5 * k, y - 1.5 * k, x + 1.5 * k, y + 1.5 * k], fill=(70, 40, 24, 255))
    save(round_tex(0xD8A060, 0xC08848, 3, "cookie", inner=cookie_face), "cookie")
    save(noise(0xC08848, 6, "cookieside"), "cookie-side")

    # Plastic chairs and their chrome legs
    for c, h in (("white", 0xF2F2EE), ("orange", 0xF08A3C), ("lime", 0x9ACD3C), ("red", 0xD23A34), ("black", 0x2A2A2C)):
        save(sheen(noise(h, 3, "chair" + c), 12, "chairsh" + c), f"plastic-{c}")

    # Gift wrap, ribbons and bows
    for c, h, pat in (("red", 0xD8343A, "stripes"), ("blue", 0x2E62C8, "dots"), ("green", 0x2E9A4A, "stars"),
                      ("yellow", 0xF2C030, "stripes"), ("purple", 0x7A44B8, "dots")):
        save(gift_paper(h, pat, "gift" + c), f"giftwrap-{c}")
    save(sheen(noise(GOLD, 4, "ribbongold"), 30, "ribbonsh", angle=0), "ribbon-gold")
    save(sheen(noise(0xF4F4F4, 3, "ribbonwhite"), 20, "ribbonsh2", angle=0), "ribbon-white")
    save(sheen(noise(0xD8202C, 3, "ribbonred"), 24, "ribbonsh3", angle=0), "ribbon-red")

    # The wall speaker's grille, string-light bulbs and wire
    img = flat(0x1C1C1E)
    px = img.load()
    for y in range(1, S, 3):
        for x in range(1, S, 3):
            px[x, y] = (8, 8, 8, 255)
    save(img, "grille")
    save(noise(0x2A2A2C, 3, "speakerbody"), "speakerbody")
    for c, h in (("red", 0xF04040), ("green", 0x40D060), ("blue", 0x4080F0), ("yellow", 0xF8D040)):
        save(bulb(h), f"bulb-{c}")
    save(noise(0x1E3A1E, 2, "wire"), "wire")

    # Posters, the reversed one and its tape; red smileys on the walls
    save(poster_time4fun(), "poster-time4fun")
    save(poster_happybday(), "poster-happybday")
    save(poster_comejoin(), "poster-comejoin")
    rev = poster_happybday().transpose(Image.FLIP_LEFT_RIGHT).filter(ImageFilter.BoxBlur(2))
    save(rev, "poster-reversed")
    save(noise(0xEDE6C8, 2, "tape"), "tape")
    save(noise(0xF6F0DC, 3, "posterback"), "posterback")
    for kind in "1234":
        save(smiley(kind), f"smiley-{kind}")

    # Inflatables, the blower, extension cords, foam, the climbing net
    for c, h in (("yellow", 0xF6C830), ("blue", 0x2E78D8), ("red", 0xE0362E), ("green", 0x3AAE54)):
        save(inflatable(h, "infl" + c), f"inflatable-{c}")
    quilt = inflatable(0xF6C830, "quilt")
    d = ImageDraw.Draw(quilt)
    for v in (0, 8, 16, 24):
        d.line([v, 0, v, S], fill=tint(rgb(0xF6C830), 0.75))
    save(quilt, "inflatable-floor")
    save(sheen(noise(0x2E62B0, 3, "blower"), 14, "blowersh"), "blower")
    save(noise(0xC8302C, 4, "blowertube"), "blowertube")
    save(noise(0xF07820, 3, "cord"), "cord")
    save(noise(0x6A6A6E, 3, "plug"), "plug")
    for c, h in (("red", 0xD8443C), ("blue", 0x3A6CD0), ("yellow", 0xF2C83A), ("green", 0x48A85A)):
        save(sheen(noise(h, 2, "foam" + c), 14, "foamsh" + c), f"foam-{c}")
    save(noise(0xC8A870, 6, "rope"), "rope")

    # Air hockey, popcorn, the movie screen
    img = flat(0xF4F6F8)
    d = ImageDraw.Draw(img)
    for y in range(2, S, 4):
        for x in range(2, S, 4):
            d.point((x, y), fill=rgb(0xB8C0C8))
    d.line([0, 16, S, 16], fill=rgb(0xD83030))
    d.ellipse([10, 10, 22, 22], outline=rgb(0x3060D0))
    save(img, "airhockey")
    save(noise(0x2E62C8, 3, "airhockeyrail"), "airhockeyrail")
    save(noise(0x1A1A1A, 2, "puck"), "puck")
    save(sheen(noise(0xC82A2A, 3, "popcorncart"), 14, "pcsh"), "popcorncart")
    img = noise(0xF8EEC4, 6, "popcorn")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("kernels"))
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        d.ellipse([x, y, x + 2, y + 2], fill=rng.choice([(255, 250, 230, 255), (246, 220, 140, 255), (230, 196, 100, 255)]))
    save(img, "popcorn")
    glass = Image.new("RGBA", (S, S), (210, 230, 240, 70))
    ImageDraw.Draw(glass).line([4, 28, 28, 4], fill=(255, 255, 255, 120), width=2)
    save(glass, "glass")
    save(noise(0xF6F6F4, 1, "screen"), "screen")
    save(noise(0x1A1A1C, 2, "roller"), "roller")
    save(noise(0x3A3A3A, 3, "rubber"), "rubber")

    # The kitchen: stainless steel, an oven, cake tins
    img = noise(0xC4CACE, 3, "stainless")
    for x in range(S):
        for y in range(S):
            if (x * 3 + y) % 7 == 0:
                img.putpixel((x, y), tint(img.getpixel((x, y)), 1.06))
    save(img, "stainless")
    img = flat(0x1E1E20)
    d = ImageDraw.Draw(img)
    d.rectangle([4, 9, 27, 24], fill=(40, 30, 24, 255), outline=(120, 124, 128, 255))
    d.rectangle([6, 11, 25, 22], fill=(140, 60, 20, 255))
    d.rectangle([4, 4, 27, 6], fill=(150, 154, 158, 255))
    for x in (7, 13, 19, 25):
        d.ellipse([x - 1, 0, x + 1, 2], fill=(200, 200, 200, 255))
    save(img, "ovenfront")
    save(noise(0xA8AEB4, 3, "tin"), "caketin")

    # The waiting room: teal cushions, laminate, magazines
    save(noise(0x2A8A8A, 4, "teal"), "teal")
    save(noise(0xC8A87A, 4, "laminate"), "laminatefun")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for i, c in enumerate((0xD83A5A, 0x3A7AD8, 0xF2C641, 0x4CAF6A)):
        d.rectangle([i * 8, 0, i * 8 + 7, S], fill=rgb(c))
        d.rectangle([i * 8 + 1, 3, i * 8 + 6, 6], fill=(250, 250, 250, 255))
    save(img, "magazines")

    # Doors: the waiting room's white exit, the FUN doors' plywood, the gym doors' green, the brass of the lifts
    for part in ("lower", "upper"):
        img = noise(0xF2F2EE, 2, "exitdoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xC8C8C2), width=1)
        if part == "upper":
            d.rectangle([9, 6, 22, 18], fill=rgb(0xC8D8E0), outline=rgb(0xA0A0A0))
        save(img, f"exitdoor-{part}")
        img = noise(0xC89A62, 6, "fundoor" + part)
        d = ImageDraw.Draw(img)
        for y in range(0, S, 3):
            d.line([0, y + random.Random(y).randint(0, 1), S, y], fill=rgb(0xB8884E))
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A5E30), width=1)
        save(img, f"fundoor-{part}")
    save(noise(0x2E7A44, 3, "gymgreen"), "gymgreen")
    gym_doors()
    # The elevator doors: brushed brass, darker toward the post and brighter toward the seam where the leaves meet,
    # a narrow specular band, fine horizontal brushing, the meeting edge drawn dark as if recessed. Drawn as the left
    # leaf seen from the front (seam on the right); the right leaf mirrors it
    for part in ("lower", "upper"):
        img = brushed_brass("elevator" + part, seam=True)
        save(img, f"elevator-{part}")
        save(img.transpose(Image.FLIP_LEFT_RIGHT), f"elevator-{part}-r")
    save(brushed_brass("elevatorlintel", vertical=True), "elevatorlintel")
    img = brushed_brass("elevatorpost")
    d = ImageDraw.Draw(img)
    d.line([0, 0, 0, S - 1], fill=rgb(0x5A4418))
    d.line([S - 1, 0, S - 1, S - 1], fill=rgb(0x5A4418))
    save(img, "elevatorpost")
    img = flat(0xF6F2E4, 64)
    d = ImageDraw.Draw(img)
    d.text((32, 18), "OUT OF", fill=(30, 30, 30, 255), font=_font(13), anchor="mm")
    d.text((32, 34), "ORDER", fill=(30, 30, 30, 255), font=_font(13), anchor="mm")
    d.text((32, 50), "=)", fill=(200, 20, 30, 255), font=_font(14), anchor="mm")
    save(grain(img, 4, "ooo"), "outoforder")
    img = Image.new("RGBA", (64, 32), rgb(0xB89040))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 63, 31], outline=(110, 80, 30, 255), width=2)
    d.text((32, 10), "DECK 4", fill=(40, 26, 10, 255), font=_font(11), anchor="mm")
    d.text((32, 22), "PARTY ROOMS 1-38 >", fill=(40, 26, 10, 255), font=_font(7), anchor="mm")
    save(grain(img, 5, "decksign"), "decksign")
    save(directory_board(), "fundirectory")
    img = flat(0x2A9A48, 64)
    text(img, "EXIT", (4, 16, 60, 48), 0xFFFFFF, 18)
    save(img, "exitsign")

    # The deck: white rail, life ring, lounger slats, a caged lamp
    save(noise(0xF4F4F0, 2, "railwhite"), "railwhite")
    save(noise(0xD82A2A, 3, "ringred"), "ring-red")
    save(noise(0xF4F2EE, 2, "ringwhite"), "ring-white")
    save(noise(0xA87848, 6, "loungewood"), "loungewood")
    save(noise(0x2A2A2A, 3, "cage"), "cage")
    save(flat(0xFFE8B0), "lampglow")

    # Service: canvas, cardboard boxes of party goods
    save(noise(0xD8D0B8, 5, "canvas"), "canvas")
    for kind, cols_ in (("balloons", (0xD8202C, 0xF4CC30, 0x2E6CD8)), ("hats", (0xF07AB4, 0x4CAF6A, 0xF2C641))):
        img = noise(0xC8A070, 5, "supplybox" + kind)
        d = ImageDraw.Draw(img)
        d.rectangle([3, 8, 28, 22], fill=(250, 250, 246, 255))
        for i, c in enumerate(cols_):
            if kind == "balloons":
                d.ellipse([6 + i * 7, 11, 11 + i * 7, 18], fill=rgb(c))
            else:
                d.polygon([(6 + i * 8, 20), (9 + i * 8, 10), (12 + i * 8, 20)], fill=rgb(c))
        save(img, f"supplybox-{kind}")

    # The Host's golden pool and inflatable throne
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            v = math.sin(x * 0.5 + math.sin(y * 0.4) * 2) * 0.5 + 0.5
            px[x, y] = mixc((214, 160, 30), (255, 226, 110), v)
    save(img, "lucagold")
    save(sheen(noise(0x6A2C9A, 3, "thronepurple"), 20, "thsh", angle=0), "inflatable-plum")
    save(sheen(noise(0xE0B030, 3, "thronegold"), 24, "thsh2", angle=0), "inflatable-gold")


# ============================================================ Blocks: surfaces

def cube_block(fname, code, kinds, textures, material="Stone", sounds=STONE, comment=None, english=None, **extra):
    """A cube block, one texture per kind (kinds None: a block with no variants). `textures` maps kind to key or to
    a {face: key} dict."""
    data = {"code": code}
    if kinds:
        data["variantgroups"] = [{"code": "kind", "states": list(kinds)}]
    data.update({"creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": material, "drawtype": "cube",
                 "lightAbsorption": 99, "resistance": 3, "sounds": sounds})

    def faces(t):
        if isinstance(t, dict):
            return {f: {"base": tpath(v).replace("backrooms:", "")} for f, v in t.items()}
        return {"all": {"base": tpath(t).replace("backrooms:", "")}}
    if kinds:
        data["texturesByType"] = {f"*-{k}": faces(textures[k]) for k in kinds}
    else:
        data["textures"] = faces(textures)
    data.update(extra)
    block(fname, data, comment)
    if kinds:
        for k in kinds:
            name(f"{code}-{k}", english[k] if isinstance(english, dict) else english)
    else:
        name(code, english)


def wall_shape(name_, wall, front=None, extra_els=(), front_full=True):
    """A full wall block, its north face given its own texture (a mural, a band), with anything standing proud of it."""
    faces = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        tex_ = front if (f == "north" and front) else wall
        faces[f] = {"texture": "#" + tex_, "uv": [0, 0, 16, 16]}
    el = {"name": "Wall", "from": [0, 0, 0], "to": [16, 16, 16], "faces": faces}
    return shape(name_, [el] + list(extra_els))


def sided_wall(fname, code, groups, shapes_by_state, english, material="Stone", sounds=STONE, comment=None, extra=None):
    """A wall block with a north-facing decoration, turned to each side. shapes_by_state: {"a-b": shape path}."""
    by_type = {}
    for state, path in shapes_by_state.items():
        for s_ in SIDES:
            by_type[f"{code}-{state}-{s_}"] = {"base": path, "rotateY": ROTATE[s_]}
    data = {"code": code, "variantgroups": groups + [{"code": "side", "states": SIDES}],
            "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
            "blockmaterial": material, "drawtype": "json", "shapeByType": by_type,
            "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 3, "sounds": sounds}
    if extra:
        data.update(extra)
    block(fname, data, comment)
    name(f"{code}-*", english)


# A trimmed wall's "side" states: every set of faces its trim can run along, in mask order (north 1, east 2, south 4,
# west 8; see WorldGenerator.FunOpenFaces). The four single faces keep their old names; the rest are their letters.
# Each set is one of five shapes, turned.
TRIM_BASES = ("n", "ne", "ns", "nes", "nesw")


def trim_sets():
    """[(state, base shape, rotateY)] for each non-empty set of faces, in mask order."""
    out = []
    for mask in range(1, 16):
        faces = "".join(f for i, f in enumerate("nesw") if mask >> i & 1)
        state = SIDES["nesw".index(faces)] if len(faces) == 1 else faces
        out.append(next((state, base, rot) for base in TRIM_BASES for k, rot in enumerate((0, 270, 180, 90))
                        if sorted("nesw"[("nesw".index(f) + k) % 4] for f in base) == sorted(faces)))
    return out


def trim_shape(name_, wall, front, faces):
    """A wall block with `front` on each of `faces` and white tile skirting standing proud along their foot, each run
    carried round the outside corner to the next face clockwise when that face is trimmed too."""
    tex = {f: wall for f in ("north", "east", "south", "west", "up", "down")}
    for f in faces:
        tex[SIDES["nesw".index(f)]] = front
    els = [{"name": "Wall", "from": [0, 0, 0], "to": [16, 16, 16],
            "faces": {f: {"texture": "#" + t, "uv": [0, 0, 16, 16]} for f, t in tex.items()}}]
    for f in faces:
        turn_on = "nesw"[("nesw".index(f) + 1) % 4] in faces
        for nm, y0, y1, out in (("Skirting", 0, 3, 1), ("SkirtingCap", 3, 3.5, 0.6)):
            e = out if turn_on else 0
            frm, to = {"n": ((0, y0, -out), (16 + e, y1, 0)), "e": ((16, y0, 0), (16 + out, y1, 16 + e)),
                       "s": ((-e, y0, 16), (16, y1, 16 + out)), "w": ((-out, y0, -e), (0, y1, 16))}[f]
            els.append(bx(nm if faces == "n" else nm + f.upper(), frm, to, "skirting"))
    return shape(name_ if faces == "n" else f"{name_}-{faces}", els)


def trim_wall(fname, code, groups, prefix_shapes, english, comment):
    """A wall's lowest block, trimmed on any set of its faces. prefix_shapes: {"a-b": (shape name, wall, front)}."""
    by_type = {}
    for prefix, (name_, wall, front) in prefix_shapes.items():
        paths = {base: trim_shape(name_, wall, front, base) for base in TRIM_BASES}
        for state, base, rot in trim_sets():
            by_type[f"{code}-{prefix}-{state}"] = {"base": paths[base], "rotateY": rot}
    data = {"code": code, "variantgroups": groups + [{"code": "side", "states": [s for s, _, _ in trim_sets()]}],
            "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
            "blockmaterial": "Stone", "drawtype": "json", "shapeByType": by_type,
            "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 3, "sounds": STONE}
    block(fname, data, comment)
    name(f"{code}-*", english)


def surfaces():
    cube_block("fun-vinyl", "fun-vinyl", "abcd", {k: f"vinyl-{k}" for k in "abcd"}, sounds=PLASTIC, english="Vinyl Tiles",
               comment="Level Fun: vinyl floor tiles in every party colour (promenades, halls, party rooms)")
    cube_block("fun-racecarpet", "fun-racecarpet", None, "racecarpet", material="Cloth", sounds=CLOTH, english="Race-Track Carpet",
               comment="Level Fun: the mural room's red play carpet with race-track lanes and toy cars")
    cube_block("fun-retrocarpet", "fun-retrocarpet", None, "retrocarpet", material="Cloth", sounds=CLOTH, english="Retro Carpet",
               comment="Level Fun: faded 1990s carpet in the bounce halls and arcades")
    cube_block("fun-checkermat", "fun-checkermat", "ab", {"a": "checkermat-a", "b": "checkermat-b"}, material="Cloth", sounds=CLOTH,
               english="Foam Play Mat", comment="Level Fun: jigsaw foam mats in the play rooms")
    cube_block("fun-paint", "fun-paint", list(PAINTS), {c: f"paint-{c}" for c in PAINTS}, english="Painted Wall",
               comment="Level Fun: a party room's painted wall")
    # The lowest block of a painted wall: scuffed paint and a real white tile skirting along each face onto the floor
    trim_wall("fun-paint-skirted", "fun-paint", [{"code": "colour", "states": list(PAINTS)}, {"code": "trim", "states": ["skirted"]}],
              {f"{c}-skirted": (f"fun-paint-{c}-skirted", f"paint-{c}-low", f"paint-{c}-low") for c in PAINTS}, "Painted Wall",
              comment="Level Fun: the lowest block of a painted wall, with white tile skirting on each face its side names (north alone in the inventory)")
    cube_block("fun-promwall", "fun-promwall", None, "promwall", english="Promenade Wall", comment="Level Fun: the promenades' cream walls")
    trim_wall("fun-promwall-band", "fun-promwall", [{"code": "trim", "states": ["band"]}],
              {"band": ("fun-promwall-band", "promwall", "promband")}, "Promenade Wall",
              comment="Level Fun: a promenade wall's lowest block: a band of four-colour checks and white tile skirting on each face its side names")
    # The edge of a low hall's drop ceiling where it opens into a taller room: ceiling tile underneath, but its side,
    # in plain view from the taller room, is the cream wall's
    wall_tex = {"base": tpath("promwall").replace("backrooms:", "")}
    block("fun-soffit", {"code": "fun-soffit", "creativeinventory": {"general": ["*"], "construction": ["*"]},
                         "blockmaterial": "Ceramic", "drawtype": "cube",
                         "textures": {"up": {"base": "block/ceilingtile"}, "down": {"base": "block/ceilingtile"}, "north": wall_tex,
                                      "east": wall_tex, "south": wall_tex, "west": wall_tex},
                         "lightAbsorption": 99, "resistance": 1, "sounds": STONE},
          "Level Fun: a hall's last ceiling tile where it opens into a taller lobby; cream sides toward the lobby")
    name("fun-soffit", "Soffit")
    # The murals: 2 x 2 blocks each; tl/tr/bl/br as seen by someone facing the painted (north) face
    shapes_ = {}
    for subject in ("mouse", "hotdog", "cheese", "stork"):
        for q in ("tl", "tr", "bl", "br"):
            shapes_[f"{subject}-{q}"] = wall_shape(f"fun-mural-{subject}-{q}", "muralwall", f"mural-{subject}-{q}")
    sided_wall("fun-mural", "fun-mural", [{"code": "subject", "states": ["mouse", "hotdog", "cheese", "stork"]},
                                          {"code": "part", "states": ["tl", "tr", "bl", "br"]}], shapes_, "Mural",
               comment="Level Fun: the mural room's cartoon murals on sunshine yellow, 2 x 2 blocks each, painted on the north face")
    # The ship's hull, and a porthole: a brass ring of eight pieces standing proud round dark glass
    cube_block("fun-hull", "fun-hull", None, "hull", material="Metal", sounds=METAL, english="Ship's Hull",
               comment="Level Fun: the rim of the region, the white riveted hull of a ship that cannot be this big")
    ring = porthole_ring()
    sided_wall("fun-hull-porthole", "fun-hull", [{"code": "kind", "states": ["porthole"]}],
               {"porthole": wall_shape("fun-hull-porthole", "hull", extra_els=[bx("Glass", (3, 3, -0.2), (13, 13, 0), "portholeglass", faces=("north",), full=True)] + ring)},
               "Porthole", material="Metal", sounds=METAL, comment="Level Fun: a porthole in the hull, onto black")
    cube_block("fun-steel", "fun-steel", None, "steel", material="Metal", sounds=METAL, english="Riveted Steel",
               comment="Level Fun: the crew's grey riveted steel in the service corridors")
    sided_wall("fun-steel-sign", "fun-steel", [{"code": "kind", "states": ["sign"]}, {"code": "sign", "states": ["crewonly"]}],
               {"sign-crewonly": wall_shape("fun-steel-sign-crewonly", "steel", extra_els=[
                   bx("Plate", (3, 4, -0.5), (13, 12, 0), "crewonly", faces=("north",), full=True),
                   bx("PlateEdge", (3, 4, -0.5), (13, 12, 0), "steel", faces=("east", "west", "up", "down"))])},
               "CREW ONLY", material="Metal", sounds=METAL, comment="Level Fun: a stencilled CREW ONLY plate on the service corridors' steel")
    cube_block("fun-deckplank", "fun-deckplank", None, "deckplank", material="Wood", sounds=WOOD, english="Teak Deck",
               comment="Level Fun: the open deck's salt-bleached teak")
    cube_block("fun-nightvoid", "fun-nightvoid", None, "nightvoid", english="Night", comment="Level Fun: the black over the open deck, a star or two")
    cube_block("fun-parquet", "fun-parquet", None, "parquet", material="Wood", sounds=WOOD, english="Parquet", comment="Level Fun: the Host's hall's parquet")
    cube_block("fun-lobbycarpet", "fun-lobbycarpet", None, "lobbycarpet", material="Cloth", sounds=CLOTH, english="Lobby Carpet",
               comment="Level Fun: the elevator lobbies' deep red carpet with its gold diamonds")
    b14_wall_versions()


def porthole_ring(cx=8, cy=8, inner=5.0, outer=6.6, z0=-1.5, z1=0.0, tex="brass", pre="Ring"):
    """An octagonal ring of eight boxes round (cx, cy) in the plane of a north face."""
    els = []
    w = outer - inner
    half = inner * math.tan(math.pi / 8) + 0.6
    for i in range(8):
        a = i * 45
        # A bar centred on the ring's middle radius, then turned about the centre
        r = (inner + outer) / 2
        x, y = cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))
        el = bx(f"{pre}{i}", (x - w / 2, y - half, z0), (x + w / 2, y + half, z1), tex, rot=(0, 0, a), origin=(x, y, (z0 + z1) / 2))
        els.append(el)
    return els


# ============================================================ Props

def balloon(nm, cx, cy, cz, colour, k=1.0, neck=True):
    """A balloon of latex: two crossed boxes for the round body, a cap on top, and a neck below. (cx, cy, cz) is the
    body's centre; k scales it (1 = 6 wide, 7 tall)."""
    t = f"latex-{colour}"
    w, h, n = 3.0 * k, 3.5 * k, 2.1 * k
    hb = 2.5 * k  # the crossed boxes are shorter; a taller narrow core rounds the top and the bottom
    els = [bxf(nm + "A", (cx - w, cy - hb + 0.3 * k, cz - n), (cx + w, cy + hb + 0.3 * k, cz + n), t),
           # (B stands a hair shorter than A: equal tops would be coplanar where the two boxes cross, and z-fight)
           bxf(nm + "B", (cx - n, cy - hb + 0.45 * k, cz - w), (cx + n, cy + hb + 0.15 * k, cz + w), t),
           bxf(nm + "Core", (cx - 2.2 * k, cy - h, cz - 2.2 * k), (cx + 2.2 * k, cy + h, cz + 2.2 * k), t)]
    if neck:
        els.append(bxf(nm + "Neck", (cx - 1.3 * k, cy - h - 1.2 * k, cz - 1.3 * k), (cx + 1.3 * k, cy - h, cz + 1.3 * k), t))
    return els


def string(nm, x, y_top, z, length, tilt=(0, 0), tex="balloonstring"):
    """A string hanging from (x, y_top, z), `length` long, tilted a few degrees (about x, about z)."""
    return bx(nm, (x - 0.12, y_top - length, z - 0.12), (x + 0.12, y_top, z + 0.12), tex,
              rot=(tilt[0], 0, tilt[1]) if any(tilt) else None, origin=(x, y_top, z))


BALLOON_SETS = {"mixed": ("red", "yellow", "blue"), "pastel": ("pastelpink", "mint", "babyblue"), "red": ("red", "red", "red")}


def balloons():
    # Three balloons against the ceiling, strings hanging to head height
    kinds = {}
    for set_, cols in BALLOON_SETS.items():
        els = []
        for i, ((cx, cy, cz), col) in enumerate(zip(((6, 11.6, 6), (11, 11.0, 10), (6.5, 12.0, 12)), cols)):
            els += balloon(f"B{i}", cx, cy, cz, col)
            els.append(string(f"S{i}", cx, cy - 4.6, cz, [10, 12, 9][i], ((-1) ** i * 5, 4 - 3 * i)))
        kinds[set_] = els
    prop("fun-balloons-ceiling", "Balloons", kinds, oriented=False, collide=False, material="Cloth", sounds=POP,
         box=(0.2, 0.4, 0.2, 0.8, 1, 0.8), comment="Level Fun: three balloons against the ceiling, their strings hanging",
         extra={"drops": [], "resistance": 0.2})
    # Two on the floor, one half gone down, strings lying in loops
    kinds = {}
    for set_, cols in (("mixed", ("blue", "orange")), ("pastel", ("lemon", "lilac"))):
        els = balloon("Up", 5, 3.6, 6, cols[0], neck=True)
        t = f"latex-{cols[1]}"
        els += [bxf("FlatA", (7, 0, 8), (14, 4, 13.5), t), bxf("FlatB", (8, 0, 7.5), (13, 3.4, 14), t),
                bxf("FlatNeck", (6, 0.2, 10), (7, 1.4, 11.2), t)]
        els += [bx("Str1", (4.9, 0, 6), (5.1, 0.2, 11), "balloonstring"), bx("Str2", (2, 0, 10.8), (5.1, 0.2, 11), "balloonstring"),
                bx("Str3", (3, 0, 11), (7, 0.2, 11.2), "balloonstring", rot=(0, 25, 0), origin=(5, 0, 11))]
        kinds[set_] = els
    prop("fun-balloons-floor", "Balloons", kinds, oriented=False, collide=False, material="Cloth", sounds=POP,
         box=(0.1, 0, 0.3, 0.9, 0.45, 0.9), comment="Level Fun: two balloons on the floor, one gone soft: the party is over",
         extra={"drops": [], "resistance": 0.2})
    # One balloon on a string, rising from the bottom of its block (tied to a chair back below, or a stair rail)
    kinds = {}
    for col in ("red", "yellow", "blue", "green", "pink"):
        els = balloon("B", 8, 26, 8, col, 1.0)
        els += [string("S1", 8, 21.3, 8, 11, (4, 0)), string("S2", 8.0, 10.6, 8.75, 10.6, (-3, 2)),
                bx("Knot", (7.4, 0, 8.1), (8.6, 0.8, 9.3), "balloonstring")]
        kinds[col] = els
    prop("fun-balloon-tied", "Balloon", kinds, oriented=False, collide=False, material="Cloth", sounds=POP,
         box=(0.3, 0, 0.3, 0.7, 1.9, 0.7), comment="Level Fun: a balloon on a string, tied to something below",
         extra={"drops": [], "resistance": 0.2})
    # The arch over a door that has guests behind it: a quarter-arc each side, six balloons, climbing from the floor
    # beside the doorway to its top. Hung in the cell in front of the wall beside a 2-wide doorway (the wall south):
    # -l stands at the viewer's left of the doorway, its arc reaching 16 voxels past its west edge to the middle.
    for part in ("l", "r"):
        els = []
        cols = ("red", "yellow", "blue", "green", "pink", "orange", "purple", "white")
        for i in range(8):
            t = math.radians(90 * i / 7)
            x = -16 + 19 * math.cos(t)
            y = 3.5 + 40 * math.sin(t)  # the top balloon's top edge is 47 of the corridor's 48 voxels (three blocks)
            if part == "r":
                x = 16 - x
            col = cols[i if part == "l" else 7 - i]
            r = 3.5
            zc = 12.2 + (0.8 if i % 2 else -0.4)
            # (A and B differ in depth too, or their fronts and backs would be coplanar and flicker)
            els += [bxf(f"B{i}A", (x - r, y - r * 0.8, zc - r * 0.7), (x + r, y + r * 0.8, zc + r * 0.7), f"latex-{col}"),
                    bxf(f"B{i}B", (x - r * 0.7, y - r, zc - r * 0.6), (x + r * 0.7, y + r, zc + r * 0.6), f"latex-{col}")]
        prop(f"fun-balloonarch-{part}", "Balloon Arch", els, collide=False, material="Cloth", sounds=POP,
             box=(0, 0, 0.6, 0.5, 1, 1) if part == "l" else (0.5, 0, 0.6, 1, 1, 1),
             comment="Level Fun: half of a balloon arch over a doorway; an arch means guests inside",
             extra={"drops": [], "resistance": 0.2})
        name(f"fun-balloonarch-{part}-*", "Balloon Arch")


def streamers():
    """A twisted crepe streamer crossing the block at the ceiling, sagging 3 voxels in the middle; two colours."""
    pairs = {"redyellow": ("red", "yellow"), "bluegreen": ("blue", "green"), "pinkpurple": ("pink", "purple")}
    kinds = {}
    for pair, (a, b) in pairs.items():
        for axis in ("ns", "ew"):
            els = []
            for i in range(4):
                z0, z1 = i * 4, i * 4 + 4
                y0, y1 = (13 + 3 * ((z - 8) / 8) ** 2 for z in (z0, z1))
                ang = math.degrees(math.atan2(y1 - y0, z1 - z0))
                ym = (y0 + y1) / 2 - 0.4
                tw = 25 if i % 2 == 0 else -25
                for j, col in enumerate((a, b)):
                    off = (j - 0.5) * 0.9
                    el = bx(f"Seg{i}{j}", (7.6 + off - 0.45, ym - 0.12, z0 - 0.05), (7.6 + off + 0.45, ym + 0.12, z1 + 0.05), f"crepe-{col}",
                            rot=(-ang, 0, tw * (1 if j else -1)), origin=(8, ym, (z0 + z1) / 2))
                    els.append(el)
            if axis == "ew":
                els = [turn(e, 1) for e in els]
                for e in els:  # turn() leaves rotations about x; swap them onto z for the turned piece
                    rx, rz = e.pop("rotationX", 0), e.pop("rotationZ", 0)
                    o = e["rotationOrigin"]
                    e["rotationOrigin"] = [16 - o[2], o[1], o[0]]
                    if rx:
                        e["rotationZ"] = rx
                    if rz:
                        e["rotationX"] = -rz
            kinds[f"{pair}-{axis}"] = els
    prop("fun-streamer", "Streamer", kinds, oriented=False, collide=False, material="Cloth", sounds=PAPER,
         box=(0, 0.75, 0, 1, 1, 1), comment="Level Fun: twisted crepe streamers across the ceiling",
         extra={"drops": [], "resistance": 0.2})


def bunting():
    """Pennants on a string along the top of a wall (hung in the cell in front of it; the wall to the south)."""
    kinds = {}
    letters = list("hapybirtd") + ["blank"]
    cols = ["red", "yellow", "green", "orange", "purple", "blue"]
    for n, letter in enumerate(letters):
        els = [bx("String", (0, 15, 15.3), (16, 15.25, 15.55), "buntingstring", rot=(0, 0, 0))]
        for i, x in enumerate((0.5, 5.75, 11)):
            if i == 1 and letter != "blank":
                t = f"pennant-letter-{letter}"
            else:
                t = f"pennant-{cols[(n * 2 + i) % len(cols)]}"
            els.append(bx(f"P{i}", (x, 9.2, 15.35), (x + 4.5, 15.1, 15.5), t, faces=("north", "south"), full=True))
        kinds[letter] = els
    prop("fun-bunting", "Bunting", kinds, collide=False, material="Cloth", sounds=PAPER, box=(0, 0.55, 0.9, 1, 1, 1),
         comment="Level Fun: pennant bunting along a head wall; the letter variants spell HAPPY BIRTHDAY",
         extra={"drops": [], "resistance": 0.2})


CLOTHS = ["blue", "greenstripe", "pink", "yellow", "redcheck"]


def tables():
    """One block of a 2-block folding party table (a at the west end, b at the east): white plastic top, a plastic
    tablecloth with skirts hanging down the long sides and the end, steel legs and a folding brace at that end."""
    kinds = {}
    for cloth in CLOTHS:
        t = f"cloth-{cloth}"
        for part in ("a", "b"):
            els = [bx("Top", (0.05, 12, 0.5), (16, 13, 15.5), "whiteplastic"),  # (its end inside the skirt, not in its face)
                   bx("Cloth", (0, 13, 0.25), (16, 13.25, 15.75), t),
                   bx("SkirtN", (0, 7, 0), (16, 13.25, 0.25), t), bx("SkirtS", (0, 7, 15.75), (16, 13.25, 16), t),
                   bx("SkirtEnd", (0, 7, 0), (0.25, 13.25, 16), t),
                   bx("LegN", (1.5, 0, 1.5), (2.5, 12, 2.5), "steeltube"), bx("LegS", (1.5, 0, 13.5), (2.5, 12, 14.5), "steeltube"),
                   bx("Brace", (2, 4, 2), (2.6, 4.6, 14), "steeltube"),
                   bx("Fold", (2.2, 4.4, 7.6), (9, 5, 8.4), "steeltube", rot=(0, 0, 38), origin=(2.2, 4.6, 8))]
            if part == "b":
                els = [turn(e, 2) for e in els]
                for e in els:
                    if "rotationZ" in e:
                        o = e["rotationOrigin"]
                        e["rotationOrigin"] = [16 - o[0], o[1], 16 - o[2]]
                        e["rotationZ"] = -e["rotationZ"]
            kinds[f"{cloth}-{part}"] = els
    prop("fun-table", "Party Table", kinds, material="Wood", sounds=PLASTIC, box=(0, 0, 0, 1, 0.83, 1),
         comment="Level Fun: a folding party table in a plastic tablecloth, two blocks long",
         extra={"drops": drops(("block:game:linen-normal-down", 1, 0), ("metalbracket", 0.5, 0.3))})


TABLE_Y = -2.75  # the top of a table's cloth, in the block above it


def tableware():
    y = TABLE_Y
    kinds = {
        "plates": [
            bx("Plate1", (1.5, y, 2), (6.5, y + 0.25, 7), "plate-yellow", faces=("up", "down"), full=True),
            bx("Plate2", (9, y, 1.5), (14, y + 0.25, 6.5), "plate-blue", faces=("up", "down"), full=True),
            bx("Plate3", (5, y, 9.5), (10, y + 0.25, 14.5), "plate-yellow", faces=("up", "down"), full=True),
            bx("Napkin1", (6.8, y, 3), (8.8, y + 0.3, 6), "napkin", rot=(0, 15, 0)),
            bx("Napkin2", (10.5, y, 10), (13, y + 0.3, 12.5), "napkin"),
            bx("Fork", (0.8, y + 0.25, 3), (1.2, y + 0.4, 6.5), "chrome")],
        "cups": [
            bx("Cup1", (3, y, 3), (5, y + 3, 5), "cup-orange"), bx("Rim1", (2.85, y + 2.8, 2.85), (5.15, y + 3.05, 5.15), "cup-orange", faces=("north", "east", "south", "west")),
            bx("Cup2", (10, y, 4), (12, y + 3, 6), "cup-orange"), bx("Rim2", (9.85, y + 2.8, 3.85), (12.15, y + 3.05, 6.15), "cup-orange", faces=("north", "east", "south", "west")),
            bx("Cup3", (6, y, 10), (8, y + 3, 12), "cup-orange"), bx("Rim3", (5.85, y + 2.8, 9.85), (8.15, y + 3.05, 12.15), "cup-orange", faces=("north", "east", "south", "west")),
            bx("Punch1", (3.1, y + 2.4, 3.1), (4.9, y + 2.5, 4.9), "piping", faces=("up",)),
            bx("Napkin", (10, y, 9), (13, y + 0.3, 12), "napkin")],
        "mess": [
            bx("Cup1", (3, y, 4), (6, y + 2, 6), "cup-orange", rot=(0, 30, 0)),
            bx("Cup2", (10, y + 0.0, 9), (12, y + 2, 12), "cup-orange", rot=(0, -60, 0)),
            bx("Plate", (6, y, 2), (11, y + 0.25, 7), "plate-blue", faces=("up", "down"), full=True, rot=(0, 20, 0)),
            bx("Stain", (2, y + 0.02, 7), (10, y + 0.05, 15), "stain", faces=("up",), full=True),
            bx("Confetti", (1, y + 0.03, 1), (15, y + 0.06, 15), "confetti", faces=("up",), full=True)],
    }
    prop("fun-tableware", "Tableware", kinds, oriented=False, collide=False, material="Cloth", sounds=PAPER,
         box=(0.05, -0.18, 0.05, 0.95, 0.02, 0.95), comment="Level Fun: what is laid on a party table (placed in the block above it)",
         extra={"drops": [], "resistance": 0.2})


def cake_quadrant(q, kind, y):
    """A quarter of a round cake on its board: the body's two crossed boxes (frosted outside, the crumb at the cut),
    two beads of piping on the rim, a drip, and on a birthday cake a striped candle and its flame."""
    sx = -1 if q in (0, 3) else 1
    sz = -1 if q in (0, 1) else 1
    top, side, crumb = ("frosting", "frosting-side", "sponge") if kind == "birthday" else ("frosting-pink", "frosting-pink-side", "velvet")
    y0, y1 = y + 0.5, y + 6.5

    def body(nm, x_ext, z_ext):
        xa, xb = sorted((8, 8 + sx * x_ext))
        za, zb = sorted((8, 8 + sz * z_ext))
        faces = {}
        for f in ("north", "east", "south", "west", "up", "down"):
            cut = (f == "west" and sx == 1) or (f == "east" and sx == -1) or (f == "north" and sz == 1) or (f == "south" and sz == -1)
            tex_ = top if f in ("up", "down") else crumb if cut else side
            w = (xb - xa) if f in ("north", "south", "up", "down") else (zb - za)
            h = (zb - za) if f in ("up", "down") else (y1 - y0)
            faces[f] = {"texture": "#" + tex_, "uv": [0, 0, min(16, w * 1.4), min(16, h * 1.4)]}
        return {"name": nm, "from": [xa, y0, za], "to": [xb, y1, zb], "faces": faces}

    els = [body(f"Q{q}A", 5.5, 3.2), body(f"Q{q}B", 3.2, 5.5)]
    bead = "beads-pink" if kind == "birthday" else "beads"
    for i, a in enumerate((20, 70)):
        ang = math.radians(a)
        bxx, bzz = 8 + sx * 4.3 * math.cos(ang), 8 + sz * 4.3 * math.sin(ang)
        els.append(bx(f"Q{q}Bead{i}", (bxx - 0.5, y1, bzz - 0.5), (bxx + 0.5, y1 + 0.7, bzz + 0.5), bead))
    # A drip down the outer side
    dz = 8 + sz * 5.5
    dx = 8 + sx * 1.6
    els.append(bx(f"Q{q}Drip", (dx - 0.5, y1 - 2.2, dz - (0.3 if sz < 0 else 0) + (0 if sz < 0 else 0)), (dx + 0.5, y1, dz + (0 if sz < 0 else 0.3)),
                  "frosting" if kind == "birthday" else "piping"))
    if kind == "birthday":
        cx, cz = 8 + sx * 2.4, 8 + sz * 2.4
        col = ("pink", "blue", "green", "yellow")[q]
        els.append(bx(f"Q{q}Candle", (cx - 0.3, y1, cz - 0.3), (cx + 0.3, y1 + 2.5, cz + 0.3), f"candle-{col}", full=True))
        els.append(bx(f"Q{q}Flame", (cx - 0.3, y1 + 2.6, cz - 0.3), (cx + 0.3, y1 + 3.4, cz + 0.3), "flame", glow=255, full=True))
    return els


def cakes():
    """Round party cakes on a board, on a table (the block above it). 4 slices to cut; each slice is a quadrant."""
    y = TABLE_Y
    order = [0, 1, 2, 3]
    kinds = {}
    for kind in ("birthday", "velvet"):
        for left in (4, 3, 2, 1, 0):
            els = [bx("Board", (1.75, y, 1.75), (14.25, y + 0.5, 14.25), "cakeboard", faces=("up", "down"), full=True),
                   bx("BoardEdge", (2.6, y, 2.6), (13.4, y + 0.45, 13.4), "steeltube", faces=("north", "east", "south", "west"))]
            for q in order[4 - left:]:
                els += cake_quadrant(q, kind, y)
            if kind == "velvet" and left >= 2:
                # "=)" piped in red across the top, and a cake knife beside it
                yt = y + 6.5
                if left >= 3:
                    els += [bx("PipeEq1", (5.5, yt, 6), (8.5, yt + 0.5, 6.7), "piping"), bx("PipeEq2", (5.5, yt, 8), (8.5, yt + 0.5, 8.7), "piping")]
                els += [bx("PipeP1", (9.5, yt, 5), (10.2, yt + 0.5, 6.5), "piping", rot=(0, 30, 0)),
                        bx("PipeP2", (10.2, yt, 6.5), (10.9, yt + 0.5, 9.5), "piping"),
                        bx("PipeP3", (9.5, yt, 9.5), (10.2, yt + 0.5, 11), "piping", rot=(0, -30, 0))]
            if kind == "velvet":
                els += [bx("KnifeBlade", (14.6, y + 0.0, 3), (15.4, y + 0.3, 10), "knifeblade"),
                        bx("KnifeHandle", (14.5, y + 0.0, 10), (15.5, y + 0.6, 14), "plastic-black")]
            if left == 0:
                els += [bx("Crumb1", (5, y + 0.5, 6), (6, y + 1, 7), "crumbs" if kind == "velvet" else "sponge"),
                        bx("Crumb2", (9, y + 0.5, 8), (9.8, y + 0.9, 8.8), "crumbs" if kind == "velvet" else "sponge"),
                        bx("Smear", (6, y + 0.51, 9), (10, y + 0.55, 11), "frosting" if kind == "birthday" else "frosting-pink", faces=("up",))]
            kinds[f"{kind}-{left}"] = els
    light = {f"*-birthday-{n}": [7, 4, 4] for n in (1, 2, 3, 4)}
    data = {"lightHsvByType": light, "drops": [], "resistance": 0.5,
            "selectionbox": cuboid((0.1, -0.18, 0.1, 0.9, 0.3, 0.9)),
            "attributes": {"slices": 4}}
    data["class"] = "BackroomsFunCake"
    prop("fun-cake", "Cake", kinds, oriented=False, collide=False, material="Cloth", sounds=CLOTH,
         comment="Level Fun: a round party cake on a table (placed in the block above it); right-click cuts a slice",
         extra=data)
    for left in range(5):
        name(f"fun-cake-birthday-{left}", "Birthday Cake")
        name(f"fun-cake-velvet-{left}", "Red Velvet Cake =)")


def cookieplates():
    y = TABLE_Y
    kinds = {}
    spots = [(5, 5.5), (9.5, 6.5), (7, 9.8)]
    for n in (3, 2, 1, 0):
        els = [bx("Plate", (3, y, 3), (13, y + 0.3, 13), "plate-plain", faces=("up", "down"), full=True)]
        for i in range(n):
            cx, cz = spots[i]
            els += [bx(f"C{i}", (cx - 1.6, y + 0.3 + 0.3 * i, cz - 1.6), (cx + 1.6, y + 0.9 + 0.3 * i, cz + 1.6), "cookie", faces=("up", "down"), full=True),
                    bx(f"C{i}Edge", (cx - 1.2, y + 0.3 + 0.3 * i, cz - 1.2), (cx + 1.2, y + 0.85 + 0.3 * i, cz + 1.2), "cookie-side", faces=("north", "east", "south", "west"))]
        kinds[str(n)] = els
    data = {"drops": [], "resistance": 0.3, "selectionbox": cuboid((0.15, -0.18, 0.15, 0.85, 0.0, 0.85))}
    data["class"] = "BackroomsFunCookies"
    prop("fun-cookieplate", "Plate of Cookies", kinds, oriented=False, collide=False, material="Cloth", sounds=PAPER,
         comment="Level Fun: a paper plate of cookies on a party table (placed in the block above it); right-click takes one",
         extra=data)


CHAIRS = {"white": "plastic-white", "orange": "plastic-orange", "lime": "plastic-lime", "red": "plastic-red", "black": "plastic-black"}


def chair_els(t):
    """A plastic stacking chair facing north: a shell seat, a curved back of three slats tipped back, chrome legs."""
    return chair_b14(t)


def chairs():
    prop("fun-chair", "Plastic Chair", {c: chair_els(t) for c, t in CHAIRS.items()}, material="Wood", sounds=PLASTIC,
         box=(0.15, 0, 0.15, 0.85, 0.56, 0.85), sel=(0.15, 0, 0.15, 0.85, 1.15, 0.92),
         comment="Level Fun: a plastic stacking chair at a party table", extra={"drops": []})
    tipped = {}
    for c, t in CHAIRS.items():
        els = []
        for e in chair_els(t):
            e = json.loads(json.dumps(e))
            e.pop("rotationOrigin", None)
            e.pop("rotationX", None)
            e["rotationOrigin"] = [8, 0, 14]
            e["rotationX"] = 82
            els.append(shift([e], 0, 0.6, 0)[0])
        tipped[c] = els
    prop("fun-chairtipped", "Plastic Chair", tipped, material="Wood", sounds=PLASTIC, collide=False,
         box=(0.1, 0, 0.3, 0.9, 0.6, 1), comment="Level Fun: a plastic chair knocked over onto its back", extra={"drops": []})


# A wanderer's belongings, gift-wrapped (each entry rolled on its own, as the supply boxes are)
GIFT_LOOT = drops(("cannedbeans", 0.35, 0.3), ("crackers", 0.4, 0.4), ("almondwater", 0.3, 0.3), ("game:bandage-clean", 0.3, 0.3),
                  ("game:poultice-linen-horsetail", 0.15, 0), ("game:knife-generic-copper", 0.06, 0), ("game:flaxtwine", 0.6, 0.6),
                  ("game:gear-rusty", 0.3, 0.3), ("game:candle", 0.3, 0.3), ("fun-wanderernote-altered", 0.12, 0), ("wanderernote-way", 0.05, 0))
GIFTS = {"red": "gold", "blue": "white", "green": "red", "yellow": "red", "purple": "gold"}


def gifts():
    """Wrapped gifts: a box with a lid, a ribbon both ways round, a bow of two loops and a knot. Broken open, they give
    a wanderer's belongings (BackroomsFunGift; one in five is a popper instead)."""
    for col, rib in GIFTS.items():
        for size, (w, h) in (("small", (10, 8)), ("tall", (8, 12))):
            a, b = 8 - w / 2, 8 + w / 2
            r = f"ribbon-{rib}"
            p = f"giftwrap-{col}"
            els = [bx("Box", (a, 0, a), (b, h - 1.6, b), p), bx("Lid", (a - 0.3, h - 2, a - 0.3), (b + 0.3, h, b + 0.3), p),
                   bx("RibbonX", (7.25, -0.01, a - 0.5), (8.75, h + 0.2, b + 0.5), r, faces=("north", "south", "up")),
                   bx("RibbonZ", (a - 0.5, -0.01, 7.25), (b + 0.5, h + 0.2, 8.75), r, faces=("east", "west", "up")),
                   bx("LoopA", (5.2, h + 0.2, 7.5), (8.2, h + 2.2, 8.5), r, rot=(0, 30, 0), origin=(8, h, 8)),
                   bx("LoopB", (7.8, h + 0.2, 7.5), (10.8, h + 2.2, 8.5), r, rot=(0, 30, 0), origin=(8, h, 8)),
                   bx("Knot", (7.4, h + 0.2, 7.4), (8.6, h + 1.4, 8.6), r)]
            path = shape(f"fun-gift-{col}-{size}", els)
            code = f"fun-gift-{col}-{size}"
            data = {
                "code": "fun-gift", "variantgroups": [{"code": "colour", "states": [col]}, {"code": "size", "states": [size]}],
                "class": "BackroomsFunGift",
                "creativeinventory": {"general": ["*"], "decorative": ["*"]},
                "shape": {"base": path}, "blockmaterial": "Wood", "drawtype": "json",
                "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.8, "sounds": PAPER,
                "collisionbox": cuboid((a / 16 - 0.02, 0, a / 16 - 0.02, b / 16 + 0.02, (h + 1) / 16, b / 16 + 0.02)),
                "selectionbox": cuboid((a / 16 - 0.02, 0, a / 16 - 0.02, b / 16 + 0.02, (h + 2.2) / 16, b / 16 + 0.02)),
                "drops": GIFT_LOOT,
            }
            block(code, data, "Level Fun: a wrapped gift, the belongings of a guest who never left. Break it to open it: its drops are what is inside; one in five is a popper (BackroomsFunGift)")
    name("fun-gift-*", "Wrapped Gift")


def wall_props():
    # The wall speaker over a party room's door (hung on the wall to its south). -on plays the tune
    sp = speaker_b14() + [bx("Bracket", (7, 10.5, 14.5), (9, 11.5, 16), "metaldark"),
                          bx("Cable", (10.5, 11, 15.4), (11, 16, 15.9), "plastic-black")]
    on = sp + [bx("Led", (9.6, 4.1, 10.25), (10.2, 4.5, 10.4), "bulb-green", glow=200, rot=(-10, 0, 0), origin=(8, 12, 14.5))]
    prop("fun-speaker", "Wall Speaker", {"on": on, "off": sp}, collide=False, material="Metal", sounds=PLASTIC,
         box=(0.3, 0.25, 0.6, 0.7, 0.75, 1), comment="Level Fun: a wall speaker over a party room's door; -on plays Happy Birthday",
         extra={"soundsByType": {"*-on-*": PLASTIC, "*": PLASTIC},
                "drops": drops(("scrapwire", 1, 0.5), ("metalbracket", 0.3, 0.3))})
    # String lights along the top of a wall: a sagging wire, four coloured bulbs that glow
    els = [bx("Wire1", (0, 14.0, 15.2), (8.2, 14.25, 15.45), "wire", rot=(0, 0, -12), origin=(0, 15, 15.3)),
           bx("Wire2", (7.8, 14.0, 15.2), (16, 14.25, 15.45), "wire", rot=(0, 0, 12), origin=(16, 15, 15.3))]
    for i, (x, col) in enumerate(zip((2, 6, 10, 14), ("red", "green", "blue", "yellow"))):
        yy = 15 - 1.7 * (1 - abs(x - 8) / 8) - 1.0
        els.append(bx(f"Bulb{i}", (x - 0.5, yy - 1.5, 14.9), (x + 0.5, yy, 15.9), f"bulb-{col}", glow=255))
    prop("fun-stringlights", "String Lights", els, collide=False, material="Glass", sounds=GLASS, light=[5, 4, 6],
         box=(0, 0.7, 0.85, 1, 1, 1), comment="Level Fun: coloured string lights along the top of a wall",
         extra={"drops": drops(("scrapwire", 0.5, 0.3), ("glassshard", 0.4, 0.3))})
    # Posters: paper on the wall, taped at the corners, one corner curling away
    def poster(tex_):
        return [bx("Paper", (3, 2, 15.75), (13, 14, 15.95), tex_, faces=("north",), full=True),
                bx("PaperBack", (3, 2, 15.75), (13, 14, 15.95), "posterback", faces=("south", "east", "west", "up", "down")),
                bx("Curl", (10.6, 11.6, 15.5), (13, 14, 15.7), "posterback", rot=(-25, 20, 0), origin=(11.8, 11.6, 15.8)),
                bx("TapeTL", (2.4, 13, 15.6), (4.4, 14, 15.75), "tape", rot=(0, 0, 30)),
                bx("TapeBL", (2.4, 2, 15.6), (4.4, 3, 15.75), "tape", rot=(0, 0, -30)),
                bx("TapeBR", (11.6, 2, 15.6), (13.6, 3, 15.75), "tape", rot=(0, 0, 30))]
    prop("fun-poster", "Poster", {"time4fun": poster("poster-time4fun"), "happybday": poster("poster-happybday"), "comejoin": poster("poster-comejoin")},
         collide=False, material="Cloth", sounds=PAPER, box=(0.15, 0.1, 0.95, 0.85, 0.9, 1),
         comment="Level Fun: a party poster taped to the wall", extra={"drops": drops(("game:paper-parchment", 1, 0))})
    name("fun-poster-time4fun-*", "TIME 4 FUN =) Poster")
    prop("fun-poster-trap", "TIME 4 FUN =) Poster", poster("poster-time4fun"), collide=False, material="Cloth", sounds=PAPER,
         box=(0.15, 0.1, 0.95, 0.85, 0.9, 1),
         comment="Level 0's trap: a TIME 4 FUN =) poster in a party-dressed room. Touch it and you are in Level Fun (one-way); a torch burns it",
         extra={"class": "BackroomsFunPoster", "behaviors": threshold("funposter"), "drops": []})
    prop("fun-poster-reversed", "Reversed Poster", poster("poster-reversed"), collide=False, material="Cloth", sounds=PAPER,
         box=(0.15, 0.1, 0.95, 0.85, 0.9, 1),
         comment="Level Fun: a party poster mirror-written and out of focus. Touch it and you are in Level 4 (one-way)",
         extra={"behaviors": threshold("funposter-reversed"), "drops": []})
    # Red smileys daubed on a wall
    kinds = {k: [bx("Paint", (0, 0, 15.88), (16, 16, 15.98), f"smiley-{k}", faces=("north",), full=True)] for k in "1234"}
    prop("fun-smiley", "=)", kinds, collide=False, material="Cloth", sounds=PAPER, box=(0.1, 0.1, 0.97, 0.9, 0.9, 1),
         comment="Level Fun: a red =) daubed on the wall. Anything marked =) is a lie", extra={"drops": [], "resistance": 0.2})
    name("fun-smiley-4-*", "COME JOIN US =)")
    # The deck sign in the lobbies
    prop("fun-decksign", "Deck Sign", [bx("Plate", (2, 5, 15.4), (14, 11, 15.9), "decksign", faces=("north",), full=True),
                                       bx("PlateEdge", (2, 5, 15.4), (14, 11, 16), "brass", faces=("east", "west", "up", "down", "south"))],
         collide=False, material="Metal", sounds=METAL, box=(0.1, 0.3, 0.95, 0.9, 0.7, 1),
         comment="Level Fun: DECK 4 · PARTY ROOMS 1-38 →", extra={"drops": []})
    # The ship's directory board in the lobbies: a felt letter board in a brass frame, a little taller than a block
    prop("fun-directory", "Ship's Directory", [
        bx("Board", (1.4, -0.6, 15.2), (14.6, 16.6, 16), "fundirectory", faces=("north",), full=True),
        bx("FrameT", (0.4, 16.6, 14.7), (15.6, 17.6, 16), "brass"), bx("FrameB", (0.4, -1.6, 14.7), (15.6, -0.6, 16), "brass"),
        bx("FrameL", (0.4, -0.6, 14.7), (1.4, 16.6, 16), "brass"), bx("FrameR", (14.6, -0.6, 14.7), (15.6, 16.6, 16), "brass")],
        collide=False, material="Metal", sounds=METAL, box=(0.03, 0, 0.9, 0.97, 1, 1),
        comment="Level Fun: the ship's directory board in a lobby (DECK 4, the ways to everything, YOU ARE HERE =))", extra={"drops": []})


def inflatables():
    """The bounce hall: puffy vinyl walls, rounded corner towers with a cone top, an arched entrance, a quilted floor."""
    cols = ["yellow", "blue", "red"]
    kinds = {}
    for c in cols:
        t = f"inflatable-{c}"
        els = []
        for i in range(4):
            y0 = i * 3.9
            out = 0.5 if i % 2 else 0
            els.append(bx(f"Tube{i}", (0, y0, 5.5 - out), (16, y0 + 4.4, 10.5 + out), t, uv=None))
        kinds[c] = els
    data = {"code": "fun-inflatable", "variantgroups": [{"code": "kind", "states": ["wall"]}, {"code": "colour", "states": cols}, {"code": "side", "states": SIDES}]}
    by_type = {}
    for c in cols:
        path = shape(f"fun-inflatable-wall-{c}", kinds[c])
        for s_ in SIDES:
            by_type[f"*-{c}-{s_}"] = {"base": path, "rotateY": ROTATE[s_]}
    data.update({"creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]}, "blockmaterial": "Cloth", "drawtype": "json",
                 "shapeByType": by_type, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
                 "resistance": 1, "sounds": RUBBER, "drops": [],
                 "collisionboxByType": {f"*-{s_}": cuboid((0, 0, 0.3, 1, 1, 0.7), s_) for s_ in SIDES},
                 "selectionboxByType": {f"*-{s_}": cuboid((0, 0, 0.3, 1, 1, 0.7), s_) for s_ in SIDES}})
    block("fun-inflatable-wall", data, "Level Fun: the puffy wall of a bounce house")
    name("fun-inflatable-wall-*", "Inflatable Wall")
    # Towers: a column of rounded drums (one block); the top block is a cone with a pennant
    tcols = ["yellow", "blue", "red", "green"]
    tower, top = {}, {}
    for c in tcols:
        t = f"inflatable-{c}"
        els = []
        for i in range(3):
            y0 = i * 16 / 3
            els += [bx(f"D{i}", (1, y0 + 0.3, 1), (15, y0 + 5.0, 15), t), bx(f"D{i}X", (2, y0 + 0.3, 0), (14, y0 + 5.0, 16), t),
                    bx(f"D{i}Z", (0, y0 + 0.3, 2), (16, y0 + 5.0, 14), t)]
        tower[c] = els
        top[c] = [bx("Rim", (1, 0, 1), (15, 3, 15), t), bx("C1", (3, 3, 3), (13, 7, 13), t), bx("C2", (5, 7, 5), (11, 11, 11), t),
                  bx("C3", (6.8, 11, 6.8), (9.2, 15, 9.2), t), bx("Pole", (7.8, 15, 7.8), (8.2, 21, 8.2), "steeltube"),
                  bx("Flag", (8.2, 17.5, 7.9), (12.5, 21, 8.1), "pennant-red", faces=("north", "south"), full=True, rot=(0, 0, 90), origin=(8.2, 21, 8))]
    for kind, parts, english, box_ in (("tower", tower, "Inflatable Tower", (0, 0, 0, 1, 1, 1)), ("towertop", top, "Inflatable Tower Top", (0.06, 0, 0.06, 0.94, 0.95, 0.94))):
        by_type = {f"*-{c}": {"base": shape(f"fun-inflatable-{kind}-{c}", els)} for c, els in parts.items()}
        block(f"fun-inflatable-{kind}", {"code": "fun-inflatable", "variantgroups": [{"code": "kind", "states": [kind]}, {"code": "colour", "states": tcols}],
                                         "creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Cloth", "drawtype": "json",
                                         "shapeByType": by_type, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
                                         "resistance": 1, "sounds": RUBBER, "drops": [], "collisionbox": cuboid(box_), "selectionbox": cuboid(box_)},
              f"Level Fun: a bounce house's corner {kind}")
        name(f"fun-inflatable-{kind}-*", english)
    # The arched entrance: two tower stubs and a curved top of five tube segments (walk through)
    t = "inflatable-red"
    els = [bx("StubL", (12.5, 0, 5), (16.5, 22, 11), t), bx("StubR", (-0.5, 0, 5), (3.5, 22, 11), t)]
    for i in range(5):
        a0, a1 = math.pi * i / 5, math.pi * (i + 1) / 5
        x0, y0 = 8 + 6.5 * math.cos(a0), 21 + 7 * math.sin(a0)
        x1, y1 = 8 + 6.5 * math.cos(a1), 21 + 7 * math.sin(a1)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        ln = math.hypot(x1 - x0, y1 - y0) + 1.6
        ang = math.degrees(math.atan2(y1 - y0, x1 - x0))
        # (the yellow lengths a hair fatter, so where two lengths overlap their faces are not in one plane)
        fat = 0.05 if i % 2 else 0
        els.append(bx(f"Arc{i}", (mx - ln / 2, my - 2.2 - fat, 5.5 - fat), (mx + ln / 2, my + 2.2 + fat, 10.5 + fat), "inflatable-yellow" if i % 2 else t,
                      rot=(0, 0, ang), origin=(mx, my, 8)))
    prop("fun-inflatable", "Inflatable Arch", {"arch": els}, collide=False, material="Cloth", sounds=RUBBER,
         box=(0, 0, 0.3, 1, 1, 0.7), fname="fun-inflatable-arch", comment="Level Fun: the arched entrance of a bounce house (walk through)",
         extra={"drops": []})
    name("fun-inflatable-arch-*", "Inflatable Arch")
    block("fun-inflatable-floor", {
        "code": "fun-inflatable", "variantgroups": [{"code": "kind", "states": ["floor"]}],
        "creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Cloth", "drawtype": "cube",
        "textures": {"up": {"base": "block/fun/inflatable-floor"}, "horizontals": {"base": "block/fun/inflatable-yellow"}, "down": {"base": "block/fun/inflatable-yellow"}},
        "lightAbsorption": 99, "resistance": 1, "sounds": RUBBER, "drops": [], "walkspeedmultiplier": 0.7,
        "collisionbox": cuboid((0, 0, 0, 1, 0.75, 1))}, "Level Fun: the quilted floor of a bounce house: soft, slow to walk on, and it bounces you")
    name("fun-inflatable-floor", "Inflatable Floor")


def playroom():
    # The blower: an octagonal housing on a stand, its fabric tube running south into the inflatable
    prop("fun-blower", "Blower", [
        bx("HousingA", (4, 3, 2), (12, 11, 12), "blower"), bx("HousingB", (3, 4, 2), (13, 10, 12), "blower"),
        bx("Intake", (4.5, 3.5, 1.8), (11.5, 10.5, 2), "grille", faces=("north",), full=True),
        bx("LegL", (4, 0, 5), (5, 3, 9), "metaldark"), bx("LegR", (11, 0, 5), (12, 3, 9), "metaldark"),
        bx("Tube", (6, 5, 12), (10, 9, 24), "blowertube"), bx("Switch", (12.9, 7, 6), (13.4, 8.5, 7.5), "plastic-red")],
         material="Metal", sounds=METAL, box=(0.18, 0, 0.12, 0.82, 0.72, 1),
         comment="Level Fun: a bounce house's blower, droning",
         extra={"sounds": dict(METAL, ambient="backrooms:ambient/fun/blower", ambientBlockCount=2),
                "drops": drops(("scrapwire", 1.5, 0.5), ("metalbracket", 1, 0.5))})
    # Orange extension cords lying on the floor
    y = 0.8
    kinds = {
        "straight": [bx("Cord", (7.6, 0, 0), (8.4, y, 16), "cord")],
        "corner": [bx("C1", (7.6, 0, 0), (8.4, y, 5.5), "cord"),
                   bx("C2", (7.6, 0, 5), (8.4, y, 10.5), "cord", rot=(0, -45, 0), origin=(8, 0, 8)),
                   bx("C3", (10.5, 0, 7.6), (16, y, 8.4), "cord")],
        "plug": [bx("Cord", (7.6, 0, 0), (8.4, y, 9), "cord"), bx("Plug", (7, 0, 9), (9, 1.5, 10.5), "plug"),
                 bx("Pin1", (7.4, 0.4, 10.5), (7.7, 0.8, 11.6), "chrome"), bx("Pin2", (8.3, 0.4, 10.5), (8.6, 0.8, 11.6), "chrome")],
    }
    prop("fun-extensioncord", "Extension Cord", kinds, collide=False, material="Cloth", sounds=RUBBER, box=(0.3, 0, 0, 0.7, 0.06, 1),
         comment="Level Fun: an orange extension cord snaking over the carpet", extra={"drops": drops(("scrapwire", 0.6, 0.3)), "resistance": 0.3})
    # Soft-play foam blocks: three crossed boxes round off every edge
    kinds = {c: [bx("X", (0, 1, 1), (16, 15, 15), f"foam-{c}"), bx("Y", (1, 0, 1), (15, 16, 15), f"foam-{c}"), bx("Z", (1, 1, 0), (15, 15, 16), f"foam-{c}")]
             for c in ("red", "blue", "yellow", "green")}
    prop("fun-foam", "Soft-Play Block", kinds, oriented=False, material="Cloth", sounds=CLOTH, box=(0, 0, 0, 1, 1, 1),
         comment="Level Fun: a soft-play foam block", extra={"drops": [], "sidesolid": {"all": True}})
    # A climbing net: rope strands every 4 voxels, knotted where they cross
    els = []
    for i, v in enumerate((2, 6, 10, 14)):
        els.append(bx(f"V{i}", (v - 0.25, 0, 7.75), (v + 0.25, 16, 8.25), "rope"))
        els.append(bx(f"H{i}", (0, v - 0.25, 7.75), (16, v + 0.25, 8.25), "rope"))
    for i, (u, v) in enumerate(((2, 6), (10, 2), (6, 10), (14, 14), (10, 10), (6, 2))):
        els.append(bx(f"K{i}", (u - 0.5, v - 0.5, 7.5), (u + 0.5, v + 0.5, 8.5), "rope"))
    prop("fun-net", "Climbing Net", els, collide=True, material="Cloth", sounds=CLOTH, box=(0, 0, 0.44, 1, 1, 0.56),
         comment="Level Fun: a play room's climbing net", extra={"climbable": True, "drops": drops(("game:rope", 0.4, 0.3))})


def rooms():
    # Air hockey: a 2-block table (a at the west end), a puck and two strikers
    def hockey(part):
        els = [bx("Top", (0, 10, 1), (16, 12, 15), "airhockey", faces=("up",), full=True),
               bx("TopSides", (0, 10, 1), (16, 12, 15), "airhockeyrail", faces=("north", "south", "east", "west", "down")),
               bx("RailN", (0, 12, 0.5), (16, 13, 1.5), "airhockeyrail"), bx("RailS", (0, 12, 14.5), (16, 13, 15.5), "airhockeyrail"),
               bx("RailEnd", (14.5, 12, 1.5), (15.5, 13, 5.5), "airhockeyrail"), bx("RailEnd2", (14.5, 12, 10.5), (15.5, 13, 14.5), "airhockeyrail"),
               bx("Apron", (1, 4, 2), (15, 10, 14), "blackmetal"), bx("Leg1", (12, 0, 3), (14, 4, 5), "blackmetal"), bx("Leg2", (12, 0, 11), (14, 4, 13), "blackmetal"),
               bx("Striker", (11, 12, 7), (13, 13.4, 9), "plastic-red"), bx("StrikerKnob", (11.6, 13.4, 7.6), (12.4, 14.4, 8.4), "plastic-red")]
        if part == "a":
            els.append(bx("Puck", (4, 12, 7.2), (5.6, 12.4, 8.8), "puck"))
            # (a is the west half: turn it round so its goal is at the west)
            out = []
            for e in els:
                e2 = turn(e, 2)
                out.append(e2)
            return out
        return els
    prop("fun-airhockey", "Air Hockey Table", {"a": hockey("a"), "b": hockey("b")}, material="Metal", sounds=METAL, box=(0, 0, 0, 1, 0.8, 1),
         comment="Level Fun: an arcade's air hockey table, two blocks long", extra={"drops": drops(("metalbracket", 1.5, 0.5), ("scrapwire", 0.5, 0.5))})
    prop("fun-popcorncart", "Popcorn Cart", [
        bx("Cart", (2, 4, 3), (14, 14, 13), "popcorncart"), bx("Popcorn", (3, 14, 4), (13, 18.5, 12), "popcorn"),
        bx("Glass", (2.5, 14, 3.5), (13.5, 22, 12.5), "glass", faces=("north", "south", "east", "west"), full=True),
        bx("Roof", (1.5, 22, 2.5), (14.5, 23.5, 13.5), "popcorncart"), bx("Sign", (3, 23.5, 7.5), (13, 26.5, 8.5), "piping"),
        bx("WheelL", (14, 0, 5), (15, 6, 11), "rubber"), bx("WheelR", (1, 0, 5), (2, 6, 11), "rubber"),
        bx("Leg", (7, 0, 11), (9, 4, 12), "metaldark"), bx("Handle", (3, 12, 13), (13, 13, 16), "chrome")],
         material="Metal", sounds=METAL, box=(0.06, 0, 0.12, 0.94, 1.45, 0.94),
         comment="Level Fun: a movie night's popcorn cart", extra={"renderpass": "Transparent", "drops": drops(("metalbracket", 1, 0.5), ("glassshard", 1, 0.5))})
    # The pull-down screen: three blocks wide, hanging below its roller bar from the block under the ceiling
    kinds = {}
    for part in ("l", "m", "r"):
        els = [bx("Screen", (0, -14, 14.5), (16, 13, 14.75), "screen", faces=("north",), full=True),
               bx("ScreenBack", (0, -14, 14.5), (16, 13, 14.75), "paperwhite", faces=("south", "east", "west", "down")),
               bx("Roller", (0, 13, 14), (16, 15, 16), "roller"), bx("Hem", (0, -14.5, 14.3), (16, -13.8, 14.95), "roller")]
        if part == "l":
            els.append(bx("CapL", (15, 12.5, 13.5), (16.5, 15.5, 16), "roller"))
        if part == "r":
            els.append(bx("CapR", (-0.5, 12.5, 13.5), (1, 15.5, 16), "roller"))
        kinds[part] = els
    prop("fun-screen", "Movie Screen", kinds, collide=False, material="Cloth", sounds=CLOTH, box=(0, -0.9, 0.88, 1, 1, 1),
         comment="Level Fun: a blank pull-down screen, three blocks wide (l, m, r as seen facing it), hung from under the ceiling",
         extra={"drops": drops(("game:cloth-plain", 0.6, 0.3))})
    # The kitchen ("bakery")
    prop("fun-counter", "Stainless Counter", [
        bx("Body", (0, 1, 4), (16, 14, 16), "stainless"), bx("Top", (0, 14, 3), (16, 15, 16), "stainless"),
        bx("Kick", (0, 0, 5), (16, 1, 16), "blackmetal"), bx("Seam", (7.8, 2, 3.8), (8.2, 13, 4), "metaldark"),
        bx("Handle1", (5, 11, 3.4), (7, 11.6, 4), "chrome"), bx("Handle2", (9, 11, 3.4), (11, 11.6, 4), "chrome")],
         material="Metal", sounds=METAL, box=(0, 0, 0.18, 1, 0.94, 1), comment="Level Fun: a stainless steel counter in the kitchen",
         extra={"drops": drops(("metalbracket", 2, 1), ("scrapwire", 0.5, 0.5))})
    prop("fun-oven", "Oven", [
        bx("Body", (1, 0, 3), (15, 15, 16), "stainless", faces=("east", "west", "up", "down", "south")),
        bx("Front", (1, 0, 3), (15, 15, 16), "ovenfront", faces=("north",), full=True),
        bx("Handle", (3, 11.2, 2.2), (13, 11.8, 2.8), "chrome"), bx("HandleL", (3, 11, 2.2), (3.6, 12, 3), "chrome"),
        bx("HandleR", (12.4, 11, 2.2), (13, 12, 3), "chrome")],
         material="Metal", sounds=METAL, box=(0.06, 0, 0.18, 0.94, 0.94, 1), comment="Level Fun: a black oven with its window",
         extra={"drops": drops(("metalbracket", 2, 1), ("scrapwire", 1, 0.5), ("glassshard", 0.5, 0.5))})
    els = [bx("Rack", (1, 4, 3), (15, 5, 13), "steeltube"),
           bx("Leg1", (1.5, 0, 3.5), (2.3, 4, 4.3), "steeltube"), bx("Leg2", (13.7, 0, 3.5), (14.5, 4, 4.3), "steeltube"),
           bx("Leg3", (1.5, 0, 11.7), (2.3, 4, 12.5), "steeltube"), bx("Leg4", (13.7, 0, 11.7), (14.5, 4, 12.5), "steeltube")]
    for i, x in enumerate((1.4, 5.8, 10.2)):
        els += [bx(f"Tin{i}", (x, 5, 5.6), (x + 4.4, 7, 10.4), "caketin", faces=("north", "east", "south", "west", "down")),
                bx(f"Sponge{i}", (x + 0.3, 6.6, 5.9), (x + 4.1, 6.9, 10.1), "velvet", faces=("up",))]
    prop("fun-caketins", "Cooling Rack", els, material="Metal", sounds=METAL, box=(0.06, 0, 0.18, 0.94, 0.45, 0.82), collide=False,
         comment="Level Fun: a cooling rack of cake tins, full of something red (placed on a counter: the block above it)",
         extra={"drops": drops(("fun-cakeslice-velvet", 2, 1), ("metalbracket", 0.5, 0.5))})
    # The waiting room: two cushioned teal seats on a chrome frame, a reception desk behind glass, a magazine table
    prop("fun-waitingchair", "Waiting Room Chairs", [
        bx("Rail", (0, 6, 7), (16, 7, 9), "chrome"), bx("LegL", (1, 0, 6), (2, 6, 10), "chrome"), bx("LegR", (14, 0, 6), (15, 6, 10), "chrome"),
        bx("SeatL", (0.6, 7, 2.5), (7.6, 9, 13), "teal"), bx("SeatR", (8.4, 7, 2.5), (15.4, 9, 13), "teal"),
        bx("BackL", (0.6, 9, 12), (7.6, 17, 14), "teal", rot=(-6, 0, 0), origin=(4, 9, 13)),
        bx("BackR", (8.4, 9, 12), (15.4, 17, 14), "teal", rot=(-6, 0, 0), origin=(12, 9, 13)),
        bx("ArmM", (7.6, 9, 4), (8.4, 12, 12), "chrome"), bx("ArmL", (0, 9, 4), (0.6, 12, 12), "chrome"), bx("ArmR", (15.4, 9, 4), (16, 12, 12), "chrome")],
         material="Cloth", sounds=CLOTH, box=(0, 0, 0.12, 1, 0.56, 0.9), comment="Level Fun: a waiting room's cushioned teal seats",
         extra={"drops": drops(("metalbracket", 1, 0.5), ("game:cloth-plain", 0.5, 0.3))})
    prop("fun-reception", "Reception Desk", [
        bx("Desk", (0, 0, 6), (16, 12, 16), "laminatefun"), bx("Top", (0, 12, 5), (16, 13, 16), "laminatefun"),
        bx("Glass", (0, 15, 9), (16, 27, 9.5), "glass", faces=("north", "south"), full=True),
        bx("GlassFrame", (0, 13, 8.8), (16, 15, 9.7), "chrome"), bx("GlassTop", (0, 27, 8.8), (16, 28, 9.7), "chrome"),
        bx("Bell", (10, 13, 6), (12, 14.2, 8), "brass"), bx("Book", (3, 13, 6), (7, 13.6, 8.5), "piping")],
         material="Wood", sounds=WOOD, box=(0, 0, 0.3, 1, 0.82, 1), sel=(0, 0, 0.3, 1, 1.75, 1),
         comment="Level Fun: the waiting room's reception desk, behind glass; nobody is there",
         extra={"renderpass": "Transparent", "drops": drops(("game:plank-aged", 2, 1), ("glassshard", 1, 0.5))})
    prop("fun-magazinetable", "Magazine Table", [
        bx("Top", (2, 5, 2), (14, 6, 14), "laminatefun"),
        bx("Leg1", (2.5, 0, 2.5), (3.5, 5, 3.5), "chrome"), bx("Leg2", (12.5, 0, 2.5), (13.5, 5, 3.5), "chrome"),
        bx("Leg3", (2.5, 0, 12.5), (3.5, 5, 13.5), "chrome"), bx("Leg4", (12.5, 0, 12.5), (13.5, 5, 13.5), "chrome"),
        bx("Mag1", (4, 6, 4), (8, 6.3, 9.5), "magazines", full=True, faces=("up",), rot=(0, 15, 0)),
        bx("Mag2", (6, 6.3, 5), (10, 6.6, 10.5), "magazines", full=True, faces=("up",), rot=(0, -10, 0)),
        bx("Mag3", (8.5, 6.6, 6), (12.5, 6.9, 11.5), "magazines", full=True, faces=("up",), rot=(0, 25, 0))],
         oriented=False, material="Wood", sounds=WOOD, box=(0.12, 0, 0.12, 0.88, 0.4, 0.88),
         comment="Level Fun: a low table of fanned magazines, all years out of date", extra={"drops": drops(("game:paper-parchment", 2, 1))})


def door_shape(name_, front, back, extra_els, all_round=True):
    """A door half: a full block, the door's face on every side (all_round) or north only, and whatever stands proud."""
    if all_round:
        extra_els = all_faces(extra_els)
    faces = {f: {"texture": "#" + (front if (f == "north" or (all_round and f in ("east", "south", "west"))) else back), "uv": [0, 0, 16, 16]}
             for f in ("north", "east", "south", "west", "up", "down")}
    return shape(name_, [{"name": "Door", "from": [0, 0, 0], "to": [16, 16, 16], "faces": faces}] + list(extra_els))


def letter_boxes(letter, u0, colour, y0=1.5, k=1.0):
    """Raised plywood letters, 2 voxels proud of a door's north face; u runs left to right as seen facing it; k
    narrows them (the single door carries all three)."""
    t = 1.8 * max(0.75, k)

    def B(nm, u1, y1, u2, y2):
        return bx(nm, (16 - u2, y1, -2), (16 - u1, y2, 0), colour)
    if letter == "F":
        return [B("FStem", u0, y0, u0 + t, y0 + 12), B("FTop", u0, y0 + 12 - t, u0 + 6 * k, y0 + 12), B("FMid", u0, y0 + 5.4, u0 + 4.8 * k, y0 + 5.4 + t)]
    if letter == "U":
        w = 6.4 * k
        return [B("UL", u0, y0 + t, u0 + t, y0 + 12), B("UR", u0 + w - t, y0 + t, u0 + w, y0 + 12), B("UB", u0, y0, u0 + w, y0 + t)]
    if letter == "N":
        w = 7.2 * k
        mid_u, mid_y = u0 + w / 2, y0 + 6
        ang = math.degrees(math.atan2(w - 2 * t, 12))
        return [B("NL", u0, y0, u0 + t, y0 + 12), B("NR", u0 + w - t, y0, u0 + w, y0 + 12),
                bx("ND", (16 - mid_u - t / 2, mid_y - 6.4, -2), (16 - mid_u + t / 2, mid_y + 6.4, 0), colour, rot=(0, 0, -ang), origin=(16 - mid_u, mid_y, -1))]
    return []


def doors():
    # The waiting room's plain white exit door, a push bar on its north face and a small EXIT sign
    shapes_ = {
        "lower": door_shape("fun-door-exit-lower", "exitdoor-lower", "exitdoor-lower", [
            bx("Bar", (2, 14, -1.4), (14, 15, -0.6), "chrome"), bx("BarL", (2, 13.6, -0.8), (3, 15.4, 0), "metaldark"),
            bx("BarR", (13, 13.6, -0.8), (14, 15.4, 0), "metaldark")]),
        "upper": door_shape("fun-door-exit-upper", "exitdoor-upper", "exitdoor-upper", [
            bx("Sign", (5, 9.5, -0.4), (11, 13, 0), "exitsign", faces=("north",), full=True)])}
    door_type("fun-door-exit", "fun-door-exit", [{"code": "part", "states": ["lower", "upper"]}], shapes_, "Exit Door", "funlobbydoor",
              "Level Fun: the waiting room's plain white exit door. Two-way, to a parking garage in Level 11")
    # The FUN doors: wooden double doors with big raised letters F, U (left leaf) and N (right leaf), brass handles
    shapes_ = {}
    for leaf in ("l", "r"):
        handle_u = 13.6 if leaf == "l" else 1.4
        for part in ("lower", "upper"):
            els = []
            if part == "upper":
                if leaf == "l":
                    els += letter_boxes("F", 1.2, "foam-red") + letter_boxes("U", 8.6, "foam-yellow")
                else:
                    els += letter_boxes("N", 4.4, "foam-blue")
            else:
                hx = 16 - handle_u
                els += [bx("Handle", (hx - 0.5, 7, -1.6), (hx + 0.5, 14, -0.8), "brass"),
                        bx("HandleT", (hx - 0.4, 13, -1.0), (hx + 0.4, 13.8, 0), "brass"),
                        bx("HandleB", (hx - 0.4, 7.2, -1.0), (hx + 0.4, 8, 0), "brass")]
            shapes_[f"{leaf}-{part}"] = door_shape(f"fun-door-fun-{leaf}-{part}", f"fundoor-{part}", f"fundoor-{part}", els)
    # The single leaf for Level 5's one-block hotel doors: all three letters, narrower, and a handle on the right
    shapes_["single-upper"] = door_shape("fun-door-fun-single-upper", "fundoor-upper", "fundoor-upper",
                                         letter_boxes("F", 0.9, "foam-red", k=0.62) + letter_boxes("U", 5.6, "foam-yellow", k=0.62)
                                         + letter_boxes("N", 10.4, "foam-blue", k=0.62))
    shapes_["single-lower"] = door_shape("fun-door-fun-single-lower", "fundoor-lower", "fundoor-lower", [
        bx("Handle", (2, 7, -1.6), (3, 14, -0.8), "brass"), bx("HandleT", (2.1, 13, -1.0), (2.9, 13.8, 0), "brass"),
        bx("HandleB", (2.1, 7.2, -1.0), (2.9, 8, 0), "brass")])
    door_type("fun-door-fun", "fun-door-fun", [{"code": "leaf", "states": ["l", "r", "single"]}, {"code": "part", "states": ["lower", "upper"]}],
              shapes_, "FUN Doors", "fundoor",
              "Wooden doors with big raised multicoloured letters spelling FUN: between Level 5 and Level Fun (two-way). A double door (l, r as seen "
              "from any face) or a single leaf with all three letters (Level 5's hotel corridors)",
              material="Wood", sounds=WOOD)
    # The gym doors of Level 11's parking garages: green, push bars, small windows, mascots painted on
    shapes_ = {}
    for leaf in ("l", "r"):
        for part in ("lower", "upper"):
            els = []
            if part == "lower":
                els = [bx("Bar", (1.5, 14, -1.4), (14.5, 15, -0.6), "chrome"), bx("BarL", (1.5, 13.6, -0.8), (2.5, 15.4, 0), "metaldark"),
                       bx("BarR", (13.5, 13.6, -0.8), (14.5, 15.4, 0), "metaldark")]
            shapes_[f"{leaf}-{part}"] = door_shape(f"fun-door-mascot-{leaf}-{part}", f"gymdoor-{leaf}-{part}", "gymgreen", els)
    door_type("fun-door-mascot", "fun-door-mascot", [{"code": "leaf", "states": ["l", "r"]}, {"code": "part", "states": ["lower", "upper"]}],
              shapes_, "Gym Doors", "mascotdoor",
              "Gymnasium double doors painted with a tiger, a parrot and a giraffe, at the back of a parking garage in Level 11: to a Level Fun waiting room (two-way)")
    # The brass elevator doors of the lobbies; they never open. The upper half carries the lintel and dial above it.
    # Their sides are the lobby's own cream wall (and its checked band and skirting, low down), since where a lobby
    # wall steps back beside the doors a side is in plain view
    shapes_ = {}
    for leaf in ("l", "r"):
        seam_x = 0 if leaf == "l" else 16
        for part in ("lower", "upper", "uppersign"):
            ptex = ("elevator-lower" if part == "lower" else "elevator-upper") + ("-r" if leaf == "r" else "")
            els = [bx("Seam", (seam_x - 0.2, 0, -0.15), (seam_x + 0.2, 16, 0), "blackmetal", faces=("north",))]
            post_x = 15 if leaf == "l" else 0
            els.append(bx("Post", (post_x, 0, -1), (post_x + 1, 16, 0), "elevatorpost", full=True))
            els += elevator_frame_b14(leaf, part, ptex)
            if part != "lower":
                els += [bx("Lintel", (-0.01, 16, -1), (16.01, 19, 0), "elevatorlintel", faces=("north", "up", "down"), full=True),
                        bx("LintelEnds", (-0.01, 16, -1), (16.01, 19, 0), "elevatorpost", faces=("east", "west"), full=True)]
                if leaf == "l":
                    els += lift_dial_b14()
                else:
                    els += call_buttons_b14()
                if part == "uppersign":
                    els += [bx("Sign", (3, 4, -0.3), (11, 10, -0.1), "outoforder", faces=("north",), full=True, rot=(0, 0, 4)),
                            bx("Tape1", (6, 9.6, -0.35), (8, 10.4, -0.25), "tape"), bx("Tape2", (6, 3.6, -0.35), (8, 4.4, -0.25), "tape")]
            side = "promband" if part == "lower" else "promwall"
            faces = {f: {"texture": "#" + (ptex if f == "north" else side if f in ("east", "west") else "promwall"), "uv": [0, 0, 16, 16]}
                     for f in ("north", "east", "south", "west", "up", "down")}
            if part == "lower":
                for nm, y0, y1, out in (("Skirting", 0, 3, 1), ("SkirtingCap", 3, 3.5, 0.6)):
                    els += [bx(nm + "E", (16, y0, 0), (16 + out, y1, 16), "skirting"), bx(nm + "W", (-out, y0, 0), (0, y1, 16), "skirting")]
            shapes_[f"{leaf}-{part}"] = shape(f"fun-elevator-{leaf}-{part}", [{"name": "Door", "from": [0, 0, 0], "to": [16, 16, 16], "faces": faces}] + els)
    door_type("fun-elevator", "fun-elevator", [{"code": "leaf", "states": ["l", "r"]}, {"code": "part", "states": ["lower", "upper", "uppersign"]}],
              shapes_, "Elevator Doors", None,
              "Level Fun: brass elevator doors in a lobby, with a dial above; they never open. uppersign: OUT OF ORDER =)", material="Metal", sounds=METAL, sided=True)


def turn_el(e, times):
    """turn() for a box that may be rotated: moves its rotation origin and swaps its rotation axes too."""
    e2 = turn(e, times)
    if "rotationOrigin" in e:
        o = list(e["rotationOrigin"])
        rx, rz = e.get("rotationX", 0), e.get("rotationZ", 0)
        for _ in range(times % 4):
            o = [16 - o[2], o[1], o[0]]
            rx, rz = -rz, rx
        e2["rotationOrigin"] = o
        e2.pop("rotationX", None)
        e2.pop("rotationZ", None)
        if rx:
            e2["rotationX"] = rx
        if rz:
            e2["rotationZ"] = rz
    return e2


def all_faces(els):
    """A door's face decorations (modelled on its north face) repeated on all four faces, so a door block needs no
    side: whichever way it is set in a wall, both faces show (what pokes into the wall beside it is hidden)."""
    out = []
    for t in range(4):
        for e in els:
            e2 = turn_el(e, t)
            e2["name"] = e2["name"] + "NESW"[t]
            out.append(e2)
    return out


def door_type(fname, code, groups, shapes_, english, kind, comment, material="Metal", sounds=METAL, sided=False):
    """Doors are cubes like door_block (no side variants; their decorations repeat on every face). sided=True: the
    elevators, which are wall dressing with a front."""
    by_type = {}
    for state, path in shapes_.items():
        if sided:
            for s_ in SIDES:
                by_type[f"*-{state}-{s_}"] = {"base": path, "rotateY": ROTATE[s_]}
        else:
            by_type[f"*-{state}"] = {"base": path}
    data = {"code": code, "variantgroups": groups + ([{"code": "side", "states": SIDES}] if sided else []),
            "creativeinventory": {"general": ["*-north" if sided else "*"], "construction": ["*-north" if sided else "*"]},
            "blockmaterial": material, "drawtype": "json", "shapeByType": by_type,
            "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": sounds}
    if kind:
        data["behaviors"] = threshold(kind)
    block(fname, data, comment)
    name(f"{code}-*", english)


def deck():
    prop("fun-shiprail", "Ship's Rail", [
        bx("Rail1", (0, 5.5, 7.5), (16, 6.5, 8.5), "railwhite"), bx("Rail2", (0, 10.5, 7.5), (16, 11.5, 8.5), "railwhite"),
        bx("Rail3", (0, 15, 7.2), (16, 16, 8.8), "railwhite"),
        bx("Post1", (3.5, 0, 7.5), (4.5, 15, 8.5), "railwhite"), bx("Post2", (11.5, 0, 7.5), (12.5, 15, 8.5), "railwhite")],
         material="Metal", sounds=METAL, box=(0, 0, 0.44, 1, 1, 0.56), comment="Level Fun: the white rail of an open deck; beyond it, black water",
         extra={"drops": []})
    # A life ring on the bulkhead: eight boxes in red and white quarters, its rope looped round
    ring = porthole_ring(8, 8, 3.6, 6.0, 14.0, 16.0, "ring-red", "Ring")
    for i, e in enumerate(ring):
        if (i // 2) % 2:
            for f in e["faces"].values():
                f["texture"] = "#ring-white"
            # (a hair thicker than the red quarters, so where they overlap their faces are not in one plane)
            e["from"][2] -= 0.05
            e["to"][2] += 0.05
    ring += [bx("Rope1", (1.6, 7.6, 13.6), (2.4, 8.4, 16), "rope"), bx("Rope2", (13.6, 7.6, 13.6), (14.4, 8.4, 16), "rope"),
             bx("Hook", (7.5, 14, 15), (8.5, 15.5, 16), "metaldark")]
    prop("fun-lifering", "Life Ring", ring, collide=False, material="Cloth", sounds=CLOTH, box=(0.1, 0.1, 0.85, 0.9, 0.9, 1),
         comment="Level Fun: a life ring on the deck's bulkhead", extra={"drops": drops(("game:rope", 0.5, 0.3))})
    # A wooden slatted lounger, two blocks long: a is the head end, its back raised
    def lounger(part):
        els = [bx("RailW", (2, 4, 0), (3, 5.5, 16), "loungewood"), bx("RailE", (13, 4, 0), (14, 5.5, 16), "loungewood"),
               bx("LegW", (2, 0, 1), (3, 4, 2.5), "loungewood"), bx("LegE", (13, 0, 1), (14, 4, 2.5), "loungewood")]
        if part == "b":
            els += [bx(f"Slat{i}", (2.5, 5.5, 0.5 + i * 4), (13.5, 6.3, 3.3 + i * 4), "loungewood") for i in range(4)]
        else:
            els += [bx(f"Slat{i}", (2.5, 5.5, 8.5 + i * 4), (13.5, 6.3, 11.3 + i * 4), "loungewood") for i in range(2)]
            els += [bx(f"Back{i}", (2.5, 5.8, 0.5 + i * 3.6), (13.5, 6.6, 3.3 + i * 3.6), "loungewood", rot=(-40, 0, 0), origin=(8, 6, 8)) for i in range(2)]
            els += [bx("BackBrace", (3, 1, 2), (13, 2, 3), "loungewood", rot=(-40, 0, 0), origin=(8, 6, 8))]
        return els
    prop("fun-deckchair", "Deck Chair", {"a": lounger("a"), "b": lounger("b")}, material="Wood", sounds=WOOD, box=(0.12, 0, 0, 0.88, 0.4, 1),
         comment="Level Fun: a wooden lounger on the deck, two blocks long (a: the head end, raised)",
         extra={"drops": drops(("game:plank-aged", 2, 1), ("game:stick", 1, 1))})
    prop("fun-decklamp", "Deck Lamp", [
        bx("Base", (6, 5, 15), (10, 11, 16), "blackmetal"), bx("Glass", (6.5, 5.5, 13), (9.5, 10.5, 15), "lampglow", glow=255),
        bx("CageV1", (6.2, 5.2, 12.6), (6.6, 10.8, 13), "cage"), bx("CageV2", (9.4, 5.2, 12.6), (9.8, 10.8, 13), "cage"),
        bx("CageH", (6.2, 7.8, 12.5), (9.8, 8.2, 13), "cage")],
         collide=False, material="Metal", sounds=METAL, light=[6, 3, 9], box=(0.35, 0.3, 0.78, 0.65, 0.7, 1),
         comment="Level Fun: a caged bulkhead lamp on the deck", extra={"drops": drops(("glassshard", 0.6, 0.3), ("metalbracket", 0.4, 0.3))})


def service():
    prop("fun-linencart", "Linen Cart", [
        bx("Bag", (2, 4, 1), (14, 15, 15), "canvas"), bx("Rim", (1.5, 14.5, 0.5), (14.5, 15.5, 15.5), "steeltube"),
        bx("Frame", (2, 3, 1), (14, 4, 15), "steeltube"), bx("Linen", (3, 15, 3), (12, 16.5, 12), "paperwhite"),
        bx("Castor1", (2.5, 0, 1.5), (4, 3, 3), "rubber"), bx("Castor2", (12, 0, 1.5), (13.5, 3, 3), "rubber"),
        bx("Castor3", (2.5, 0, 13), (4, 3, 14.5), "rubber"), bx("Castor4", (12, 0, 13), (13.5, 3, 14.5), "rubber")],
         oriented=False, material="Cloth", sounds=CLOTH, box=(0.1, 0, 0.05, 0.9, 1, 0.95), comment="Level Fun: a crew's linen cart on castors",
         extra={"drops": drops(("block:game:linen-normal-down", 1, 0.5), ("game:cloth-plain", 1, 0.5))})
    els = [bx(f"Post{i}", (x, 0, z), (x + 1, 16, z + 1), "steel") for i, (x, z) in enumerate(((0.5, 8), (14.5, 8), (0.5, 15), (14.5, 15)))]
    els += [bx(f"Shelf{i}", (0.5, y, 8), (15.5, y + 0.6, 16), "steel") for i, y in enumerate((1, 8, 15))]
    els += [bx("BoxA", (1.5, 1.6, 9), (7, 6.5, 15), "supplybox-balloons", full=True), bx("BoxB", (8, 1.6, 9.5), (14.5, 5.5, 15), "supplybox-hats", full=True),
            bx("BoxC", (2, 8.6, 9), (8, 12.5, 15), "supplybox-hats", full=True), bx("BoxD", (9, 8.6, 9), (14, 14, 15), "supplybox-balloons", full=True)]
    path = shape("fun-supplyshelf", els)
    by_type = {f"*-{s_}": {"base": path, "rotateY": ROTATE[s_]} for s_ in SIDES}
    block("fun-supplyshelf", {
        "code": "fun-supplyshelf", "variantgroups": [{"code": "side", "states": SIDES}],
        # (Our subclass of the game's typed container: the game's own picks itself by its first code part, which is "fun";
        # and that container reads textures as "<type>-<code>", so each is given under both names)
        "class": "BackroomsFunSupplyShelf", "entityClass": "GenericTypedContainer", "behaviors": [{"name": "Container"}],
        "attributes": {"inventoryClassName": "fun-supplyshelf", "defaultType": "shelf", "types": ["shelf"], "drop": {"shelf": False},
                       "quantitySlots": {"shelf": 8}, "dialogTitleLangCode": {"shelf": "backrooms:fun-suppliescontents"},
                       "storageType": {"shelf": 189}, "retrieveOnly": {"shelf": False}, "shape": {"shelf": "backrooms:" + path},
                       "variantByGroup": "side"},
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]}, "blockmaterial": "Metal", "drawtype": "json",
        "textures": {k: {"base": "block/fun/" + t} for t in ("steel", "supplybox-balloons", "supplybox-hats") for k in (t, "shelf-" + t)},
        "shapeByType": by_type, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2, "sounds": METAL,
        "collisionboxByType": {f"*-{s_}": cuboid((0, 0, 0.5, 1, 1, 1), s_) for s_ in SIDES},
        "selectionboxByType": {f"*-{s_}": cuboid((0, 0, 0.5, 1, 1, 1), s_) for s_ in SIDES},
        "drops": drops(("metalbracket", 2, 1))}, "Level Fun: a steel shelf of party supplies in the service corridors (an 8-slot container)")
    name("fun-supplyshelf-*", "Party Supplies")
    LANG["fun-suppliescontents"] = "Party Supplies"


def carnivorous():
    """Entity 110: a balloon floating at chest height, tied to nothing, its ribbon a curly ribbon (a helix of six
    little boxes turned 60 degrees apart) hanging below. Non-solid; touch it and it stings."""
    kinds = {}
    for col in ("red", "yellow", "blue", "green", "pink"):
        els = balloon("B", 8, 24, 8, col, 1.05)
        for i in range(6):
            a = math.radians(i * 60)
            x, z = 8 + 0.9 * math.cos(a), 8 + 0.9 * math.sin(a)
            y1 = 19.2 - i * 2.6
            els.append(bx(f"Curl{i}", (x - 0.5, y1 - 2.4, z - 0.15), (x + 0.5, y1, z + 0.15), "curlyribbon", rot=(0, i * 60 + 90, 18), origin=(x, y1, z)))
        kinds[col] = els
    data = {"drops": drops(("game:vegetable-onion", 1.5, 0.5)), "resistance": 0.4, "selectionbox": cuboid((0.28, 1.15, 0.28, 0.72, 1.75, 0.72)),
            "attributes": {"carnivorous": True}}
    data["class"] = "BackroomsCarnivorousBalloon"
    prop("fun-cballoon", "Balloon", kinds, oriented=False, collide=False, material="Cloth", sounds=POP,
         comment="Level Fun: a Carnivorous Balloon (Entity 110) in a dark corner: don't touch it, don't pop it", extra=data)


def misc_blocks():
    block("fun-confetti", {
        "code": "fun-confetti", "creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Cloth", "drawtype": "json",
        "shape": {"base": shape("fun-confetti", [bx("Layer", (0, 0, 0), (16, 0.2, 16), "confetti", faces=("up",), full=True)])},
        "textures": {"confetti": confetti_alts_b14()},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.1, "sounds": PAPER,
        "replaceable": 5000, "collisionbox": None, "selectionbox": cuboid((0, 0, 0, 1, 0.05, 1)), "maxstacksize": 64,
        "drops": [{"type": "block", "code": "fun-confetti", "quantity": {"avg": 1}}],
    }, "Level Fun: a thin layer of confetti; a handful of it places a layer (a path marker, the party's own chalk)")
    name("fun-confetti", "Confetti")
    LANG["blockdesc-fun-confetti"] = "A handful of confetti. Scatter it to mark a path: the party's own chalk."
    prop("fun-lucapool", "Golden Pool", [
        bx("Floor", (0, 0, 0), (16, 0.5, 16), "brass"), bx("RimN", (0, 0, 0), (16, 2, 1), "brass"), bx("RimS", (0, 0, 15), (16, 2, 16), "brass"),
        bx("RimW", (0, 0, 1), (1, 2, 15), "brass"), bx("RimE", (15, 0, 1), (16, 2, 15), "brass"),
        bx("Tears", (1, 0.5, 1), (15, 1.6, 15), "lucagold", glow=160, faces=("up",))],
         oriented=False, collide=True, material="Metal", sounds=METAL, light=[7, 6, 8], box=(0, 0, 0, 1, 0.125, 1),
         comment="Level Fun: the shallow golden basin under the Host, where its LUCA tears collect (a bottle a day)",
         extra=dict({"drops": []}, **({"class": "BackroomsFunLucaPool"} if registered("BackroomsFunLucaPool") else {})))
    prop("fun-hostthrone", "Inflatable Throne", [
        bx("Base", (1, 0, 2), (15, 8, 14), "inflatable-plum"), bx("Seat", (2, 8, 2.5), (14, 11, 12.5), "inflatable-gold"),
        bx("ArmL", (0, 8, 2), (3, 15, 13), "inflatable-plum"), bx("ArmR", (13, 8, 2), (16, 15, 13), "inflatable-plum"),
        bx("ArmTopL", (-0.3, 14, 1.7), (3.3, 16, 13.3), "inflatable-gold"), bx("ArmTopR", (12.7, 14, 1.7), (16.3, 16, 13.3), "inflatable-gold"),
        bx("Back", (1, 8, 12), (15, 28, 15.5), "inflatable-plum"), bx("Crown", (0, 27, 11), (16, 31, 16), "inflatable-gold"),
        bx("Knob1", (0, 31, 12.5), (3, 34, 14.5), "inflatable-gold"), bx("Knob2", (13, 31, 12.5), (16, 34, 14.5), "inflatable-gold"),
        bx("Knob3", (6.5, 31, 12.5), (9.5, 35, 14.5), "inflatable-gold")],
         material="Cloth", sounds=RUBBER, box=(0, 0, 0.12, 1, 0.7, 1), sel=(0, 0, 0.12, 1, 2, 1),
         comment="Level Fun: the purple and gold inflatable throne on the stage of the Host's hall", extra={"drops": []})


def tidy_names():
    """Drop the catch-all names prop() gave families that share a code with other files, and name each kind."""
    for k in ("block-fun-poster-*", "block-fun-smiley-*", "block-fun-cake-*", "block-fun-inflatable-*"):
        LANG.pop(k, None)
    for k in ("time4fun", "happybday", "comejoin"):
        name(f"fun-poster-{k}-*", "TIME 4 FUN =) Poster" if k == "time4fun" else "Poster")
    for k in "123":
        name(f"fun-smiley-{k}-*", "=)")
    name("fun-smiley-4-*", "COME JOIN US =)")
    name("fun-poster-trap-*", "TIME 4 FUN =) Poster")
    name("fun-poster-reversed-*", "Reversed Poster")


def props():
    balloons()
    streamers()
    bunting()
    tables()
    tableware()
    cakes()
    cookieplates()
    chairs()
    gifts()
    wall_props()
    inflatables()
    playroom()
    rooms()
    doors()
    deck()
    service()
    carnivorous()
    misc_blocks()
    tidy_names()


# ============================================================ Items

def item_textures():
    k = 4

    def slice_(sponge, frost, piping=False, candle=False):
        def draw(d, k_, img):
            # A wedge of layer cake seen from the side, on its point: frosting on top and down the back
            pts = [(4 * k, 26 * k), (28 * k, 26 * k), (28 * k, 12 * k), (4 * k, 22 * k)]
            d.polygon(pts, fill=sponge)
            d.line([(4 * k, 24 * k), (28 * k, 19 * k)], fill=(232, 74, 106, 255) if not piping else (244, 236, 228, 255), width=2 * k)
            d.polygon([(4 * k, 22 * k), (28 * k, 12 * k), (28 * k, 9 * k), (4 * k, 19.5 * k)], fill=frost)
            d.rectangle([26 * k, 9 * k, 29 * k, 26 * k], fill=frost)
            for x in range(6, 27, 4):
                d.ellipse([x * k, (21.5 - (x - 4) * 10 / 24 - 2) * k, (x + 2) * k, (21.5 - (x - 4) * 10 / 24) * k], fill=tint(frost, 0.9))
            if piping:
                d.text((16 * k, 15 * k), "=)", fill=(200, 20, 30, 255), font=_font(7 * k), anchor="mm")
            if candle:
                d.rectangle([20 * k, 3 * k, 21.5 * k, 12 * k], fill=(240, 122, 180, 255))
                d.ellipse([19.5 * k, 0, 22 * k, 3.5 * k], fill=(255, 220, 90, 255))
            d.line([(3 * k, 27 * k), (29 * k, 27 * k)], fill=(200, 204, 210, 255), width=k)
        return supersample(32, 32, k, draw)
    save_item(slice_((236, 200, 120, 255), (250, 246, 238, 255), candle=True), "cakeslice-birthday")
    save_item(slice_((122, 20, 32, 255), (248, 220, 224, 255), piping=True), "cakeslice-velvet")

    def cookie(d, k_, img):
        d.ellipse([4 * k, 4 * k, 28 * k, 28 * k], fill=(200, 140, 74, 255), outline=(150, 100, 50, 255), width=k)
        rng = random.Random(seed_of("cookieitem"))
        for _ in range(8):
            x, y = rng.uniform(8, 24) * k, rng.uniform(8, 24) * k
            d.ellipse([x - 1.6 * k, y - 1.6 * k, x + 1.6 * k, y + 1.6 * k], fill=(70, 40, 24, 255))
    save_item(supersample(32, 32, k, cookie), "cookie")

    def tears(d, k_, img):
        d.rectangle([13 * k, 2 * k, 19 * k, 6 * k], fill=(120, 90, 60, 255))
        d.rectangle([14 * k, 6 * k, 18 * k, 10 * k], fill=(220, 230, 230, 200))
        d.rounded_rectangle([8 * k, 10 * k, 24 * k, 30 * k], 4 * k, fill=(230, 240, 240, 140), outline=(200, 214, 220, 255), width=k)
        d.rounded_rectangle([9 * k, 15 * k, 23 * k, 29 * k], 3 * k, fill=(246, 196, 40, 255))
        d.ellipse([11 * k, 17 * k, 15 * k, 22 * k], fill=(255, 240, 160, 255))
    save_item(supersample(32, 32, k, tears), "lucatears")

    for kind in ("stripes", "dots"):
        img = flat(0xF07AB4 if kind == "stripes" else 0x3C7DD9)
        d = ImageDraw.Draw(img)
        if kind == "stripes":
            for x in range(-S, S, 8):
                d.polygon([(x, 0), (x + 4, 0), (x + 4 + S, S), (x + S, S)], fill=rgb(0xF2C641))
        else:
            for y in range(2, S, 7):
                for x in range(2 + (3 if (y // 7) % 2 else 0), S, 7):
                    d.ellipse([x, y, x + 3, y + 3], fill=rgb(0xF4F4F0))
        save_item(img, f"partyhat-{kind}")
    save_item(noise(0xF6F6F0, 3, "pompom"), "pompom")
    save_item(noise(0x222222, 2, "elastic"), "elastic")


def item_shapes():
    # The red balloon held on its string: the string rises from the hand, the balloon well above it
    els = balloon("B", 8, 30, 8, "red", 1.0) + [string("S", 8, 25.4, 8, 25, (0, 0)), bx("Loop", (7.2, 0, 7.6), (8.8, 1.2, 8.4), "balloonstring")]
    keys = {"latex-red": "backrooms:block/fun/latex-red", "balloonstring": "backrooms:block/fun/balloonstring"}
    write_json(os.path.join(ASSETS, "shapes", "item", "fun", "balloon-red.json"), {"textureWidth": 16, "textureHeight": 16, "textures": keys, "elements": els})
    # The party hat, worn on the head (stepParentName Head: the seraph's head is 5.5 x 5 x 5, its top at y 5)
    cx, cz = 2.75, 2.5
    els = []
    for i, (w, h) in enumerate(((4.4, 1.6), (3.6, 1.6), (2.8, 1.6), (2.0, 1.5), (1.2, 1.4))):
        y0 = 4.85 + sum(hh for _, hh in ((4.4, 1.6), (3.6, 1.6), (2.8, 1.6), (2.0, 1.5))[:i])
        els.append({"name": f"Cone{i}", "from": [cx - w / 2, y0, cz - w / 2], "to": [cx + w / 2, y0 + h, cz + w / 2],
                    "faces": {f: {"texture": "#hat", "uv": [0, 0, 16, 16]} for f in ("north", "east", "south", "west", "up", "down")}})
    els.append({"name": "Pompom", "from": [cx - 0.8, 12.6, cz - 0.8], "to": [cx + 0.8, 14.2, cz + 0.8],
                "faces": {f: {"texture": "#pompom", "uv": [0, 0, 16, 16]} for f in ("north", "east", "south", "west", "up", "down")}})
    for side, z in (("L", cz - 2.35), ("R", cz + 2.25)):
        els.append({"name": "Elastic" + side, "from": [cx - 0.1, 0.4, z], "to": [cx + 0.1, 4.9, z + 0.1],
                    "faces": {f: {"texture": "#elastic", "uv": [0, 0, 1, 16]} for f in ("north", "east", "south", "west")}})
    # Tip the whole hat a little to one side, about the middle of the head's top, and hang it from the head
    hat = {"name": "PartyHat", "stepParentName": "Head", "from": [cx - 2.2, 4.85, cz - 2.2], "to": [cx + 2.2, 4.86, cz + 2.2],
           "rotationOrigin": [cx, 4.85, cz], "rotationX": 10, "rotationZ": -8, "faces": {},
           "children": [dict(e, **{"from": [e["from"][i] - [cx - 2.2, 4.85, cz - 2.2][i] for i in range(3)],
                                    "to": [e["to"][i] - [cx - 2.2, 4.85, cz - 2.2][i] for i in range(3)]}) for e in els]}
    write_json(os.path.join(ASSETS, "shapes", "item", "fun", "partyhat.json"), {
        "textureWidth": 16, "textureHeight": 16,
        "textures": {"hat": "backrooms:item/fun/partyhat-stripes", "pompom": "backrooms:item/fun/pompom", "elastic": "backrooms:item/fun/elastic"},
        "elements": [hat]})


def write_item(code, data, comment, **ground):
    """Writes an item type, set down on the floor as `ground` says (detail_kit.ground_storable's arguments)."""
    write_json(os.path.join(ASSETS, "itemtypes", "fun", code + ".json"), detail_kit.ground_storable(data, **ground), comment)
    WRITTEN["itemtypes"].append(code)


def items():
    item_textures()
    item_shapes()

    def food(code, english, satiety, category, desc, cls=None, extra=None):
        data = {"code": code, "maxstacksize": 16, "texture": {"base": f"item/fun/{code[4:]}"},
                "creativeinventory": {"general": ["*"], "items": ["*"]},
                "nutritionProps": {"satiety": satiety, "foodcategory": category}, "materialDensity": 600}
        if cls and cls.startswith("!"):
            data["class"] = cls[1:]  # (contracted with the code agent: always)
        elif cls and registered(cls):
            data["class"] = cls
        data.update(TRANSFORMS)
        if extra:
            data.update(extra)
        write_item(code, data, english)
        LANG[f"item-{code}"] = english
        LANG[f"itemdesc-{code}"] = desc
    food("fun-cakeslice-birthday", "Slice of Birthday Cake", 260, "Grain",
         "Cut from a party cake in Level Fun. Sweet and fresh, as if it was baked this morning. It tastes faintly of rust.")
    food("fun-cakeslice-velvet", "Slice of Red Velvet Cake =)", 420, "Protein",
         "Sweeter than it should be. M.E.G. archives: DO NOT EAT.", cls="!BackroomsVelvetCake",
         extra={"attributes": {"stabilityChange": -0.2, "funFever": 0.2}})
    food("fun-cookie", "Cookie", 60, "Grain", "A chocolate chip cookie from a party table. Still soft.")
    data = {"code": "fun-lucatears", "maxstacksize": 4, "texture": {"base": "item/fun/lucatears"},
            "creativeinventory": {"general": ["*"], "items": ["*"]},
            "nutritionProps": {"satiety": 20, "foodcategory": "NoNutrition"}, "materialDensity": 1000,
            "attributes": {"maxhealthExtraPoints": 4, "meleeWeaponsDamage": 0.25, "durationHours": 24, "stabilityRestored": 0.3}}
    if registered("BackroomsLucaTears"):
        data["class"] = "BackroomsLucaTears"
    data.update(TRANSFORMS)
    write_item("fun-lucatears", data, "LUCA tears from the Host's golden pool")
    LANG["item-fun-lucatears"] = "LUCA Tears"
    LANG["itemdesc-fun-lucatears"] = "Golden, faintly warm. \"Think of it as spinach for Popeye.\""

    # The red balloon, held: half of the disguise
    write_item("fun-balloon-red", {
        "code": "fun-balloon-red", "maxstacksize": 1, "shape": {"base": "backrooms:item/fun/balloon-red"},
        "creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 50, "attributes": {"funDisguise": "balloon"},
        "guiTransform": {"translation": {"x": 0, "y": -6, "z": 0}, "rotation": {"x": -15, "y": 30, "z": 0}, "origin": {"x": 0.5, "y": 1.2, "z": 0.5}, "scale": 1.1},
        "tpHandTransform": {"translation": {"x": -0.75, "y": -0.1, "z": -0.6}, "rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 0.9},
        "fpHandTransform": {"translation": {"x": 0.1, "y": -0.6, "z": 0}, "rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 1.6},
        "groundTransform": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": 2.4},
    }, "A red balloon on a string: what the Partygoers' new interns carry",
        # Tied to the floor, a block high (it is two as modelled)
        layout="SingleCenter", scale=0.5, box=(0, 0, 0, 0, 0, 0), select=(0.3, 0, 0.3, 0.7, 1, 0.7))
    LANG["item-fun-balloon-red"] = "Red Balloon"
    LANG["itemdesc-fun-balloon-red"] = "A red balloon on a string. With a party hat on, from a few steps away, you could pass for one of them. Don't run."

    # The party hat: head-slot clothing, the other half of the disguise
    write_item("fun-partyhat", {
        "code": "fun-partyhat", "variantgroups": [{"code": "pattern", "states": ["stripes", "dots"]}],
        "maxstacksize": 1, "storageFlags": 128, "behaviors": [{"name": "Wearable"}],
        "shape": {"base": "backrooms:item/fun/partyhat"},
        "texturesByType": {f"*-{k}": {"hat": {"base": f"backrooms:item/fun/partyhat-{k}"}, "pompom": {"base": "backrooms:item/fun/pompom"},
                                      "elastic": {"base": "backrooms:item/fun/elastic"}} for k in ("stripes", "dots")},
        "attributes": {"clothescategory": "head", "wearableAttachment": True, "funDisguise": "hat",
                       "disableElements": ["ponytailhigh", "sidehigh", "hoodshoulder", "hoodupperover"], "keepElements": ["hair-covered", "hoodtight"]},
        "creativeinventory": {"general": ["*"], "clothing": ["*"], "items": ["*"]},
        "tpHandTransform": {"translation": {"x": -0.97, "y": -3, "z": -1}, "rotation": {"x": -13, "y": -80, "z": 12}, "origin": {"x": 0.5, "y": 1.5, "z": 0.5}, "scale": 0.55},
        "guiTransform": {"translation": {"x": 0, "y": 0, "z": 19}, "rotation": {"x": 174, "y": -45, "z": 23}, "origin": {"x": 0.52, "y": 1.6, "z": 0.5}, "scale": 1.99},
        "groundTransform": {"translation": {"x": 0.05, "y": -1.1, "z": 0}, "rotation": {"x": -2, "y": 0, "z": -4}, "origin": {"x": 0.5, "y": 0.5, "z": 0.53}, "scale": 4},
    }, "A paper party hat with an elastic and a pompom: head-slot clothing",
        # Modelled on the head: brought to the middle of the block with its brim on the floor (the elastic hangs under it)
        height=0.6, transform={"translation": {"x": 0.328, "y": -0.303, "z": 0.344}})
    LANG["item-fun-partyhat-*"] = "Party Hat"
    LANG["itemdesc-fun-partyhat-*"] = "A paper cone hat on an elastic, with a pompom. Wear it with a red balloon in hand and, beyond a few steps, they may take you for one of their own."

    # The lying note: a wanderer's note in an altered hand, marking a party room with guests as a refuge
    write_item("fun-wanderernote", {
        "code": "fun-wanderernote", "class": "BackroomsWandererNote", "variantgroups": [{"code": "kind", "states": ["altered"]}],
        "maxstacksize": 16, "texture": {"base": "item/wanderernote"}, "creativeinventory": {"general": ["*"], "items": ["*"]},
        "guiTransform": TRANSFORMS["guiTransform"], "tpHandTransform": TRANSFORMS["tpHandTransform"], "groundTransform": TRANSFORMS["groundTransform"],
    }, "A wanderer's note found in Level Fun's gifts: altered. Its kind is 'altered' (Variant[\"kind\"])")
    LANG["item-fun-wanderernote-altered"] = "Wanderer's Note"
    LANG["itemdesc-fun-wanderernote-altered"] = "A note about somewhere safe, underlined twice, and a little smiley face in the corner. Right-click to read it."


# ============================================================ Entities

def entities():
    import gen_entities as E
    anim = E.anim

    def tex(code, variants=()):
        t = {"base": f"backrooms:entity/{code}"}
        if variants:
            t["alternates"] = [{"base": f"backrooms:entity/{code}-{v}"} for v in variants]
        return t

    pg_anims = [
        anim("hurt", "hurt", 1.0, weight=10, blendMode="AddAverage"),
        anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
        anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage", easeOutSpeed=4),
        anim("walk", "walk", 1.0), anim("run", "run", 1.0),
        anim("gaze", "gaze", 1.0, weight=6), anim("latch", "latch", 1.0, weight=10),
        anim("berserk", "berserk", 1.0, weight=8), anim("berserkidle", "berserkidle", 1.0, weight=3),
        anim("claw", "claw", 1.0, weight=10), anim("attack", "latch", 1.0, weight=10),
    ]
    snd = "backrooms:entity/partygoer/"
    # The task the code registers (src/Entities/AiTaskPartygoer.cs); keys and defaults as the plan's "Manifest changes" C4
    task = {"code": "backrooms-partygoer", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
            "walkSpeed": 0.016, "runSpeed": 0.031,
            # (What the task reads is the nested senses object; flat sight keys on the task itself are ignored)
            "senses": {"sightLit": 12, "sightDim": 7, "sightDark": 4, "sightCone": 70, "sneakFactor": 0.6, "hearing": 6, "touch": 2},
            "latchDamage": 2.5, "clawDamage": 4.0, "attackRange": 1.6,
            "gazeSound": snd + "gaze", "latchSound": snd + "latch", "clawSound": snd + "claw"}
    tasks = [task, E.idle("idle", 1.1, 4000, 12000, 4000, 12000)]

    def partygoer(code, shape_, extra_drops):
        return {
            "code": code, "class": "EntityAgent", "tags": ["backrooms-entity", "humanoid", "habitat-land", "partygoer"],
            "weight": 90,
            # The model stands 36 px (2.25 blocks); the hitbox is kept just under the doorways' height
            "hitboxSize": {"x": 0.8, "y": 2.2}, "deadHitboxSize": {"x": 0.8, "y": 0.6}, "eyeHeight": 2.0,
            "attributes": {"killedByInfoText": "backrooms:deadcreature-partygoer", "fireDamageClosed": 0.25, "fireDamageOpen": 3.0,
                           "headDamageOpen": 2.0},
            "drops": [E.drop("fun-partyhat-stripes", 0.2), E.drop("fun-partyhat-dots", 0.2), E.drop("game:gear-rusty", 0.5, 0.5)] + extra_drops,
            "client": E.common_client(f"backrooms:entity/{shape_}", tex(shape_, ("red", "blue", "green", "white")), pg_anims, size=0.86),
            "server": E.server(30, tasks, menace={"huntSeconds": 90}, decay=None),
            "sounds": {"hurt": "game:creature/drifter-hurt", "death": snd + "die",
                       "idle": snd + "step*"},
            "idleSoundChance": 0.05, "idleSoundRange": 6,
        }
    def with_behaviour(e):
        # The code's damage rules (fire x0.25 closed, x3 open; berserk below half health) must see damage before health does
        bs = e["server"]["behaviors"]
        i = next(k for k, b in enumerate(bs) if b["code"] == "health")
        bs.insert(i, {"code": "backrooms-partygoer"})
        return E.sync_harvestable(e)
    write_entity("fun-partygoer", with_behaviour(partygoer("partygoer", "fun-partygoer", [])))
    write_entity("fun-partygoer-intern", with_behaviour(partygoer("partygoer-intern", "fun-partygoer-intern", [E.drop("fun-balloon-red", 1)])))

    # The lure balloon: a red balloon floating at head height on its own (the code moves it: no tasks)
    write_entity("fun-lureballoon", {
        "code": "lureballoon", "class": "EntityAgent", "tags": ["backrooms-entity", "habitat-air"], "habitat": "Air", "weight": 0.1,
        # The hitbox covers the balloon on top as well as its string
        "hitboxSize": {"x": 0.5, "y": 1.8}, "eyeHeight": 0.6,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-lureballoon"},
        "client": {"renderer": "Shape", "shape": {"base": "backrooms:entity/fun-lureballoon"}, "texture": {"base": "backrooms:entity/fun-lureballoon"},
                   "size": 1.0, "behaviors": [{"code": "interpolateposition"}],
                   "animations": [anim("idle", "idle", triggeredBy={"defaultAnim": True}), anim("drift", "drift", 1.0)]},
        "server": {"behaviors": [{"code": "health", "currenthealth": 1, "maxhealth": 1}, {"code": "entitystatetags"}]},
        "sounds": {"hurt": "backrooms:ambient/fun/balloonpop", "death": "backrooms:ambient/fun/balloonpop"},
    })
    # The Party Host: a golden fried egg in the ceiling, an eye and a mouth together. It never moves and cannot be hurt
    # (class BackroomsPartyHost, src/Regions/FunSystem.cs, refuses all damage; no health behaviour)
    write_entity("fun-partyhost", {
        "code": "partyhost", "class": "BackroomsPartyHost", "tags": ["backrooms-entity"], "weight": 2000,
        "hitboxSize": {"x": 3.0, "y": 0.8}, "eyeHeight": 0.3,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-partyhost", "invulnerable": True},
        "client": {"renderer": "Shape", "shape": {"base": "backrooms:entity/fun-partyhost"}, "texture": {"base": "backrooms:entity/fun-partyhost"},
                   "size": 1.0, "behaviors": [{"code": "interpolateposition"}],
                   "animations": [anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage"),
                                  anim("weep", "weep", 1.0, weight=5), anim("upset", "upset", 1.0, weight=10)]},
        "server": {"behaviors": [{"code": "entitystatetags"}]},
        # Its wet breathing, heard across its hall (about one breath in ten seconds)
        "sounds": {"idle": "backrooms:ambient/fun/hostbreath"}, "idleSoundChance": 0.2,
    })


def write_entity(fname, data):
    write_json(os.path.join(ASSETS, "entities", fname + ".json"), data)
    WRITTEN["entities"].append(fname)


# ============================================================ Lang

def lang():
    LANG.update({
        "level-15": "Level Fun =)",
        "levelhint-15": "They are slow and nearsighted. Distance is your best chance.",
        "levelname-15": "Level Fun",
        "funposter": "You touch the poster. Suddenly the room is full of balloons.",
        "funposter-reversed": "The letters swim into focus under your hand.",
        "funposter-burnt": "The poster curls, blackens and is gone.",
        "funstairs": "The steps climb into the ceiling, and on, through confetti.",
        "fundoor": "Music, and the smell of cake.",
        "mascotdoor": "The doors swing shut behind you on a quiet room full of chairs.",
        "overboard": "Black water closes over you.",
        "funballpit": "You push down through the balls, and down, and down.",
        "fun-latched": "It has latched on to you. Seconds count!",
        "fun-fever-pending": "The bite burns. A poultice, now!",
        "fun-fever-cleared": "You bind the bite in time.",
        "fun-fever": "You are so hungry. Everything smells of cake.",
        "fun-joined": "{0} joined the party =)",
        "fun-voice-1": "Come join us! =)",
        "fun-voice-2": "We have so much fun here!",
        "fun-voice-3": "There's cake! =)",
        "fun-voice-4": "It's your birthday! =)",
        "fun-voice-5": "Don't upset the host.",
        "fun-voice-6": "Why would you want to leave? =)",
        "fun-voice-7": "They're dead! You're next! =)",
        "fun-voice-from": "{0}'s voice: {1}",
        "fun-voice-familiar-1": "Mum",
        "fun-voice-familiar-2": "Dad",
        "fun-voice-familiar-3": "your sister",
        "fun-voice-familiar-4": "an old friend",
        "fun-disguised": "In a party hat, with a red balloon, you could pass for one of them. Don't run.",
        "prefixandcreature-partygoer": "a Partygoer",
        "item-creature-partygoer": "Partygoer",
        "deadcreature-partygoer": "Dead Partygoer",
        "prefixandcreature-partygoer-intern": "a Partygoer",
        "item-creature-partygoer-intern": "Partygoer",
        "prefixandcreature-lureballoon": "a balloon",
        "item-creature-lureballoon": "Balloon",
        "deadcreature-lureballoon": "Popped Balloon",
        "prefixandcreature-partyhost": "the Host",
        "item-creature-partyhost": "The Host",
        "deadcreature-partyhost": "The Host",
    })


def merge_lang():
    """Adds the names to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text_ = f.read()
    new_lines = []
    for key, value in LANG.items():
        line = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text_):
            text_ = pattern.sub(lambda m: line + m.group(1), text_, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text_.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text_ = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    json.loads(re.sub(r"^\s*//.*$", "", text_, flags=re.M))  # still valid
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text_)
    print(f"lang: {len(LANG)} keys merged ({len(new_lines)} new)")


# ============================================================ Checks

def resolve_texture(path):
    domain, rel = path.split(":", 1) if ":" in path else ("backrooms", path)
    if domain == "backrooms":
        return os.path.exists(os.path.join(ASSETS, "textures", rel + ".png"))
    game = os.path.join(os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory")), "assets")
    return any(os.path.exists(os.path.join(game, d, "textures", rel + ".png")) for d in ("survival", "game"))


def check():
    """Every texture a shape, block, item or entity of ours names resolves, every shape a block names exists, every
    sound of ours exists."""
    problems = []
    for nm in WRITTEN["shapes"]:
        data = json.load(open(os.path.join(ASSETS, "shapes", "block", "fun", nm + ".json"), encoding="utf-8"))
        for k, p in data["textures"].items():
            if not resolve_texture(p):
                problems.append(f"shape {nm}: texture {k} -> {p}")
    for kind in ("blocktypes", "itemtypes", "entities"):
        folder = os.path.join(ASSETS, kind, "fun") if kind != "entities" else os.path.join(ASSETS, "entities")
        for nm in WRITTEN[kind]:
            raw = open(os.path.join(folder, nm + ".json"), encoding="utf-8").read()
            raw = re.sub(r"^//.*$", "", raw, flags=re.M)
            for m in re.finditer(r'"base":\s*"([^"]+)"', raw):
                p = m.group(1)
                rel = p.split(":", 1)[-1]
                if rel.startswith(("block/fun/fun-", "entity/fun-", "item/fun/balloon", "item/fun/partyhat")) and not rel.startswith("item/fun/partyhat-"):
                    sub = "shapes"
                    ok = os.path.exists(os.path.join(ASSETS, sub, rel + ".json")) or resolve_texture(p)
                else:
                    ok = resolve_texture(p)
                if not ok:
                    problems.append(f"{kind} {nm}: {p}")
            for m in re.finditer(r'"(backrooms:(?:ambient|entity)/[^"*]+)\*?"', raw):
                p = m.group(1).split(":", 1)[1]
                if not os.path.exists(os.path.join(ASSETS, "sounds", p + ".ogg")) and not os.path.exists(os.path.join(ASSETS, "sounds", p + "1.ogg")):
                    if not p.startswith("entity/fun-"):
                        problems.append(f"{kind} {nm}: sound {p}")
    for p in problems:
        print("CHECK:", p)
    print(f"check: {len(WRITTEN['blocktypes'])} blocktypes, {len(WRITTEN['shapes'])} shapes, {len(WRITTEN['textures'])} textures, "
          f"{len(WRITTEN['itemtypes'])} itemtypes, {len(WRITTEN['entities'])} entities, {len(problems)} problems")
    return not problems


# ============================================================ B14 (graphics pass)
#
# Every B14 painter runs after surface_textures() and prop_textures() under the same keys (plus a few new ones), so a
# family reverts by dropping its call from b14_textures(); the models are the *_b14 functions. Means are matched to
# main's PNGs where the surface is large (FUN_OLD). The palette is the level's own: the party colours are kept.

import matlib as M  # noqa: E402
from gen_city import CITY_F3, CITY_F5  # noqa: E402  (the B12 pixel faces)

FUN_OLD = {
    "promwall": (241, 233, 207), "skirting": (230, 230, 226), "lobbycarpet": (115, 25, 26), "racecarpet": (170, 57, 49),
    "retrocarpet": (63, 141, 139), "elevator": (201, 167, 89),
}
FUN_F3 = dict(CITY_F3, **{" ": "0 0 0 0 0", ">": "100 010 001 010 100", "<": "001 010 100 010 001",
                          "^": "010 111 010 010 010", "v": "010 010 010 111 010", "=": "000 111 000 111 000",
                          ")": "10 01 01 01 10", "'": "1 1 0 0 0"})
FUN_F5 = dict(CITY_F5, **{"=": "00000 00000 11111 00000 11111 00000 00000", ")": "100 010 001 001 001 010 100",
                          ">": "1000 0100 0010 0001 0010 0100 1000"})
BIG = {  # a chunky 4 x 6 face for the poster's "4 Fun =)", drawn at twice the size
    "4": "1010 1010 1111 0010 0010 0010", "F": "1111 1000 1110 1000 1000 1000", "u": "0000 0000 1001 1001 1001 0111",
    "n": "0000 0000 1110 1001 1001 1001", "=": "000 111 000 111 000 000", ")": "010 001 001 001 001 010",
    " ": "0 0 0 0 0 0",
}


def fwidth(s, font=FUN_F3, gap=1, scale=1):
    return sum((len(font[ch].split()[0]) + gap) * scale for ch in s) - gap * scale


def ftext(img, s, x, y, col, font=FUN_F3, gap=1, scale=1, outline=None):
    """`s` in a pixel face at (x, y) (characters looked up as given, then upper-cased); with `outline`, a 1 px ring of
    that colour round every stroke first."""
    p = img.load()
    w, h = img.size

    def glyph(ch):
        return (font.get(ch) or font[ch.upper()]).split()
    for pass_ in ((outline, 1), (col, 0)) if outline else ((col, 0),):
        c, ring = pass_
        xx = x
        for ch in s:
            rows = glyph(ch)
            for r, row in enumerate(rows):
                for cc, bit in enumerate(row):
                    if bit != "1":
                        continue
                    for dy in range(-ring, scale + ring):
                        for dx in range(-ring, scale + ring):
                            X, Y = xx + cc * scale + dx, y + r * scale + dy
                            if 0 <= X < w and 0 <= Y < h:
                                p[X, Y] = M.rgba(c)
            xx += (len(rows[0]) + gap) * scale
    return x + fwidth(s, font, gap, scale)


def ftext_c(img, s, y, col, font=FUN_F3, gap=1, scale=1, x0=0, x1=None, outline=None):
    x1 = img.width if x1 is None else x1
    return ftext(img, s, x0 + (x1 - x0 - fwidth(s, font, gap, scale) + 1) // 2, y, col, font, gap, scale, outline)


def fmatch(img, key, target=None):
    return T.match_rgb(img, target or FUN_OLD[key], key="b14fun" + key)


def fine(img, seed, amp=1.6, roller=2.2):
    """A version's own fine grain and roller stipple over a shared ground."""
    rng = random.Random(seed)
    st = M.fbm(img.size, M.sub(seed, "roll"), (2, 1), 0.7)
    p = img.load()
    for y in range(img.height):
        for x in range(img.width):
            p[x, y] = M.rgba(M.lift(p[x, y], rng.uniform(-amp, amp) + st[y][x] * roller), p[x, y][3])
    return img


def paint_b14(base, key, n=3, low=False):
    """Eggshell paint over plaster: one calm ground for every version (no block edges), each version its own roller
    stipple. The low block (above the skirting) gathers a little dirt toward the floor, and one version in four carries
    a pair of soft chair-back rubs at a random place."""
    base = rgb(base)[:3] if isinstance(base, int) else base
    ground = M.noise_hv(base, 0, seed_of("b14" + key + "ground"), mottle=1.8, cells=(16, 8), hue=1.0)
    out = []
    for k in range(n):
        img = fine(ground.copy(), seed_of(f"b14{key}fine{k}"))
        if low:
            p = img.load()
            for y in range(S):
                t = max(0.0, (y - 14) / (S - 14)) ** 1.6
                for x in range(S):
                    p[x, y] = M.rgba(M.mix(p[x, y], M.lift(base, -26), t * 0.10))
            if k == n - 1:
                rng = random.Random(seed_of(f"b14{key}rub"))
                for _ in range(2):
                    cx, cy, L = rng.uniform(6, 26), rng.uniform(13, 17), rng.randint(5, 8)
                    for i in range(L):
                        tt = math.sin(math.pi * (i + 0.5) / L)
                        M.touch(img, int(cx) + i - L // 2, int(cy), -0.05 * tt)
                        M.touch(img, int(cx) + i - L // 2, int(cy) + 1, -0.03 * tt)
        out.append(T.match_rgb(img, base if not low else M.lift(base, -1), key="b14p" + key))
    return out


def b14_paint():
    for i, (c, base) in enumerate(PAINTS.items()):
        for k, img in enumerate(paint_b14(base, "paint" + c)):
            save(img, f"paint-{c}" + ("" if k == 0 else f"-{k + 1}"))
        for k, img in enumerate(paint_b14(base, "paintlow" + c, n=4, low=True)):
            save(img, f"paint-{c}-low" + ("" if k == 0 else f"-{k + 1}"))
    for k, img in enumerate(paint_b14((241, 233, 207), "promwall")):
        save(fmatch(img, "promwall"), "promwall" + ("" if k == 0 else f"-{k + 1}"))
    for k, img in enumerate(paint_b14(0xF3E27A, "muralwall", n=1)):
        save(img, "muralwall")


def glazed(img, box, colour, seed, hl=True):
    """One glazed ceramic tile in `box` (end exclusive): its own shade and a hue nudge, a slight tilt across it, a lit
    top and left edge, a dark bottom and right one, and a small highlight up and to the left."""
    x0, y0, x1, y1 = box
    rng = random.Random(seed)
    c0 = M.hue_shift(M.lift(colour, rng.uniform(-5, 5)), rng.uniform(-3, 3))
    tx, ty = rng.uniform(-3, 3), rng.uniform(-3, 3)
    p = img.load()
    w, h = x1 - x0, y1 - y0
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, v = (x - x0) / max(1, w - 1) - 0.5, (y - y0) / max(1, h - 1) - 0.5
            p[x, y] = M.rgba(M.lift(c0, tx * u + ty * v - 4 * v + rng.uniform(-1.5, 1.5)))
    M.bevel(img, box, 1, 0.16)
    if hl and w > 4:
        for (dx, dy, f) in ((1, 1, 0.22), (2, 1, 0.12), (1, 2, 0.1)):
            M.touch(img, x0 + dx, y0 + dy, f)


def b14_tiles():
    # The promenade's checked band: glazed 8 px tiles in the four colours under a cream cap, in a recessed grout
    img = Image.new("RGBA", (S, S))
    order = [PARTY["red"], PARTY["yellow"], PARTY["blue"], PARTY["green"]]
    grout = (196, 190, 176)
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), M.rgba(grout))
    for row in range(4):
        for col in range(4):
            y0 = row * 8 + (2 if row == 0 else 0)
            glazed(img, (col * 8, y0, col * 8 + 7, row * 8 + 7), rgb(order[(row + col) % 4])[:3], seed_of(f"b14band{row}{col}"))
    for x in range(S):  # the cap: a cream bullnose along the top
        img.putpixel((x, 0), M.rgba(M.lift((246, 242, 228), 8)))
        img.putpixel((x, 1), M.rgba(M.lift((246, 242, 228), -6)))
    save(img, "promband")
    # White skirting tiles: glazed, in pale grey grout
    img = Image.new("RGBA", (S, S))
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), M.rgba((186, 186, 180)))
    for row in range(4):
        for col in range(4):
            glazed(img, (col * 8, row * 8, col * 8 + 7, row * 8 + 7), (240, 240, 234), seed_of(f"b14skirt{row}{col}"))
    save(fmatch(img, "skirting"), "skirting")


def b14_vinyl():
    """The party vinyl tiles: B0's colour picks (the same draw), each tile now its own shade and hue, a soft satin
    sheen falling across it (no streak repeating block after block), a fine grain, a recessed joint, a scuff or two."""
    cols = list(PARTY.values())
    for kind in "abcd":
        rng = random.Random(seed_of("vinyl" + kind))
        picks = []
        for ty in range(2):
            for tx in range(2):
                options = [c for c in cols if c not in picks[-1:] and (ty == 0 or c != picks[tx])]
                picks.append(rng.choice(options))
        img = Image.new("RGBA", (S, S))
        r2 = random.Random(seed_of("b14vinyl" + kind))
        for ty in range(2):
            for tx in range(2):
                base = rgb(picks[ty * 2 + tx])[:3]
                c0 = M.hue_shift(M.lift(base, r2.uniform(-4, 4)), r2.uniform(-3, 3))
                for y in range(16):
                    for x in range(16):
                        sheen = 5 * (1 - ((x - 3) ** 2 + (y - 3) ** 2) ** 0.5 / 18)
                        img.putpixel((tx * 16 + x, ty * 16 + y), M.rgba(M.lift(c0, sheen + r2.uniform(-2, 2))))
                box = (tx * 16, ty * 16, tx * 16 + 16, ty * 16 + 16)
                M.bevel(img, box, 1, 0.10)
                for k in range(16):  # the joint: dark on the right and bottom of each tile (the next tile's lit edge meets it)
                    M.touch(img, tx * 16 + 15, ty * 16 + k, -0.22)
                    M.touch(img, tx * 16 + k, ty * 16 + 15, -0.24)
        for _ in range(1 if kind in "ac" else 0):  # a faint shoe scuff, in two of the four kinds
            x, y = r2.randrange(1, S - 5), r2.randrange(1, S - 3)
            for i in range(r2.randint(3, 5)):
                M.touch(img, x + i, y + (1 if i in (0, 4) else 0), -0.08)
        save(img, f"vinyl-{kind}")


def flat_rgba(c, size=S):
    return Image.new("RGBA", (size, size) if isinstance(size, int) else size, rgb(c) if isinstance(c, int) else tuple(c) + (255,))


def crisp(img, pat, t=0.45):
    """Pulls the dyed motif part of the way back to its flat colour, so woven lines stay whole across the tufts."""
    p, q = img.load(), pat.load()
    for y in range(img.height):
        for x in range(img.width):
            if q[x, y][3]:
                p[x, y] = M.rgba(M.mix(p[x, y], q[x, y][:3], t))
    return img


def b14_carpets():
    """The three patterned carpets keep their patterns, now dyed into a cut pile (matlib.carpet) instead of over noise."""
    # Lobby: deep red, gold diamonds
    pat = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(pat)
    gold = rgb(0xD0A844)
    for cx, cy in ((8, 8), (24, 24)):
        d.polygon([(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)], outline=gold)
        d.point((cx, cy), fill=gold)
    for cx, cy in ((24, 8), (8, 24)):
        d.polygon([(cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)], fill=tint(gold, 0.88))
    img = M.carpet(seed_of("b14lobbycarpet"), base=(122, 22, 30), pile=8, grain=3, mottle=0, pattern=pat)
    save(fmatch(crisp(img, pat), "lobbycarpet"), "lobbycarpet")
    # The race-track play carpet: B0's lanes, lines and two toy cars, flat, then dyed into the pile
    pat = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = pat.load()
    lane = rgb(0x8A1512)
    for y in range(S):
        for x in range(S):
            if 7 <= y <= 14 or 19 <= x <= 26:
                px[x, y] = lane
    d = ImageDraw.Draw(pat)
    for x in range(0, S, 6):
        if not 18 <= x <= 26:
            d.line([x, 10, x + 2, 10], fill=rgb(0xE8C43A))
            d.line([x, 11, x + 2, 11], fill=rgb(0xE8C43A))
    for y in range(0, S, 6):
        if not 6 <= y <= 14:
            d.line([22, y, 22, y + 2], fill=rgb(0xE8C43A))
            d.line([23, y, 23, y + 2], fill=rgb(0xE8C43A))
    for y in (7, 14):
        for x in range(S):
            if not 19 <= x <= 26:
                px[x, y] = (226, 214, 204, 255)
    for x in (19, 26):
        for y in range(S):
            if not 7 <= y <= 14:
                px[x, y] = (226, 214, 204, 255)
    d.rectangle([3, 8, 8, 12], fill=rgb(0x2E5FC8))
    d.rectangle([4, 9, 6, 11], fill=rgb(0x9CC4F0))
    for wx in (3, 7):
        d.point([(wx, 8), (wx, 12)], fill=(20, 20, 20, 255))
    d.rectangle([20, 21, 24, 26], fill=rgb(0xF2C232))
    d.rectangle([21, 22, 23, 23], fill=rgb(0xFFF0A8))
    for wy in (21, 26):
        d.point([(20, wy), (24, wy)], fill=(20, 20, 20, 255))
    img = M.carpet(seed_of("b14racecarpet"), base=(180, 34, 32), pile=6, grain=3, mottle=0, loop=True, pattern=pat)
    save(fmatch(crisp(img, pat), "racecarpet"), "racecarpet")
    # Retro: teal with pink squiggles and yellow triangles, the worn patch kept
    rng = random.Random(seed_of("retro"))
    pat = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(pat)
    for _ in range(4):
        x, y = rng.randrange(S), rng.randrange(S)
        pts = [(x + i * 2, y + (2 if i % 2 else -1)) for i in range(5)]
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.line([(p[0] + ox, p[1] + oy) for p in pts], fill=rgb(0xE868A8), width=1)
    for _ in range(4):
        x, y = rng.randrange(S), rng.randrange(S)
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d.polygon([(x + ox, y + oy), (x + 4 + ox, y + 1 + oy), (x + 1 + ox, y + 4 + oy)], fill=rgb(0xF2D040))
    for _ in range(5):
        d.point((rng.randrange(S), rng.randrange(S)), fill=rgb(0x7A3AB0))
    img = M.carpet(seed_of("b14retrocarpet"), base=(42, 138, 140), pile=8, grain=3, mottle=1, pattern=pat, wear=0.3)
    save(fmatch(crisp(img, pat), "retrocarpet"), "retrocarpet")


def b14_elevator():
    """The lifts: brushed brass with no painted seam (the seam is a box), the dial a face of its own under a needle and
    a bezel, call buttons, the lintel and posts as before."""
    for part in ("lower", "upper"):
        # (round 2) brushed brass: fine horizontal brushing, darker toward the post and brighter toward the meeting
        # edge, a soft broad sheen instead of B0's crisp pale stripe (which read as a painted plank edge)
        img = M.brushed_metal(seed_of("b14elev" + part), base=(198, 164, 86), grain=3, direction="h", streak=10, sheen=6)
        for y in range(S):
            for x in range(S):
                M.touch(img, x, y, ((x / 31 - 0.5) * 0.16 + 0.07 * math.exp(-((x - 21) / 4.0) ** 2)))
        img = fmatch(img, "elevator")
        save(img, f"elevator-{part}")
        save(img.transpose(Image.FLIP_LEFT_RIGHT), f"elevator-{part}-r")
    img = flat_rgba(0x2A2420, (32, 16))  # 32 x 16 to the dial's 8 x 4: the arc's centre is where the needle pivots
    d = ImageDraw.Draw(img)
    d.pieslice([4, 1, 28, 25], 180, 360, fill=rgb(0xF4ECD8))
    for i in range(5):  # the floor marks round the arc
        a = math.pi + i * math.pi / 4
        d.line([16 + 11 * math.cos(a), 13 + 11 * math.sin(a), 16 + 9 * math.cos(a), 13 + 9 * math.sin(a)], fill=(40, 30, 30, 255))
    save(img, "liftdialface")
    save(M.noise_hv((200, 30, 30), 2, seed_of("b14needle"), mottle=2), "liftneedle")
    img = M.noise_hv((236, 228, 206), 2, seed_of("b14button"), mottle=2)
    M.bevel(img, (0, 0, S, S), 2, 0.2)
    save(img, "liftbutton")
    plate = M.brushed_metal(seed_of("b14callplate"), base=(206, 170, 92), grain=3, direction="v", sheen=12)
    save(plate, "liftplate")


def b14_signs():
    # OUT OF ORDER =): a card taped to the doors, in a pixel face; 64 x 48 to the sign's 8 x 6
    img = M.paper(seed_of("b14ooo"), (64, 48), base=(246, 242, 228), grain=2, mottle=3, fibre=0.4, seams=None, strip=0)
    ink = (34, 32, 34)
    ftext_c(img, "OUT OF", 6, ink, FUN_F5)
    ftext_c(img, "ORDER", 16, ink, FUN_F5)
    ftext_c(img, "=)", 28, (200, 22, 32), FUN_F5, scale=2)
    save(img, "outoforder")
    # DECK 4 / PARTY ROOMS 1-38 >: engraved in a brass plate; 80 x 40 to the plate's 12 x 6
    img = M.brushed_metal(seed_of("b14decksign"), (80, 40), base=(160, 124, 54), grain=3, direction="h", sheen=10)
    M.bevel(img, (0, 0, 80, 40), 2, 0.22)
    eng = (58, 40, 14)
    x = ftext_c(img, "DECK 4", 6, eng, FUN_F5, scale=2)
    ftext_c(img, "PARTY ROOMS 1-38 >", 27, eng, FUN_F3)
    save(img, "decksign")
    # The ship's directory: white letters pressed into navy felt; 56 x 72
    rows = [("PARTY ROOMS", ">"), ("BALL PIT", "<"), ("BOUNCE HALL", "^"), ("ARCADE", "v"), ("KITCHEN", ">"),
            ("LIDO DECK", "^"), ("GUEST SVCS", "X")]
    img = M.fabric(seed_of("b14felt"), (56, 72), base=(30, 36, 52), weave="plain", contrast=3, grain=2, mottle=3)
    for y in range(20, 70, 3):  # the felt's grooves
        for x in range(2, 54):
            M.touch(img, x, y, -0.18)
    white, goldc = (236, 232, 220), (232, 196, 96)
    ftext_c(img, "DECK 4", 2, goldc, FUN_F5)
    ftext_c(img, "DIRECTORY", 11, white, FUN_F3)
    for x in range(4, 52):
        img.putpixel((x, 18), M.rgba((200, 160, 70)))
    for i, (label, arrow) in enumerate(rows):
        y = 21 + i * 6
        ftext(img, label, 4, y, white, FUN_F3)
        ftext(img, arrow, 49, y, white, FUN_F3)
    ftext_c(img, "YOU ARE HERE =)", 63, (232, 70, 70), FUN_F3)
    save(img, "fundirectory")
    # TIME 4 FUN =): B0's picture (clock, rainbow, handprint), its lettering now pixels
    k = 4

    def draw(d, k_, im):
        d.rectangle([0, 0, 64 * k, 64 * k], fill=(252, 246, 228, 255))
        for i, c in enumerate([(230, 50, 50), (246, 150, 40), (246, 214, 50), (70, 180, 80), (60, 120, 220), (140, 80, 200)]):
            d.arc([-8 * k, 34 * k + i * 3 * k, 72 * k, 100 * k + i * 3 * k], 180, 360, fill=c + (255,), width=3 * k)
        d.ellipse([18 * k, 6 * k, 46 * k, 34 * k], fill=(246, 140, 30, 255), outline=(40, 30, 30, 255), width=2 * k)
        d.ellipse([22 * k, 10 * k, 42 * k, 30 * k], fill=(255, 250, 236, 255))
        for a in range(12):
            ang = a * math.pi / 6
            d.line([32 * k + 8 * k * math.cos(ang), 20 * k + 8 * k * math.sin(ang), 32 * k + 9.5 * k * math.cos(ang),
                    20 * k + 9.5 * k * math.sin(ang)], fill=(40, 30, 30, 255), width=k)
        d.line([32 * k, 20 * k, 32 * k, 13 * k], fill=(40, 30, 30, 255), width=2 * k)
        d.line([32 * k, 20 * k, 37 * k, 22 * k], fill=(40, 30, 30, 255), width=2 * k)
    img = supersample(64, 64, k, draw)
    hand(img, 47, 10, (176, 14, 20))
    ftext(img, "TIME", 2, 11, (40, 30, 30), FUN_F3)  # (below the corner tape)
    dark = (40, 30, 30)
    x = (64 - fwidth("4 Fun=)", BIG, 1, 2)) // 2
    for ch, c in zip("4 Fun=)", [(230, 50, 50), None, (60, 120, 220), (70, 180, 80), (246, 160, 30), (230, 50, 50), (230, 50, 50)]):
        if c:
            ftext(img, ch, x, 41, c, BIG, 1, 2, outline=dark)
        x += (len(BIG[ch].split()[0]) + 1) * 2
    save(grain(img, 2, "t4f"), "poster-time4fun")


def b14_party():
    """Confetti: crisp paper bits (slivers, squares and the odd round dot) in the party colours, three versions; the
    plastic of the chairs as moulded plastic (the stretched streak is gone); the speaker's cloth and cone."""
    cols = list(PARTY.values()) + [0xFFFFFF, 0xF07AB4, 0xF2C641]
    for k in range(3):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        p = img.load()
        rng = random.Random(seed_of(f"b14confetti{k}"))
        for _ in range(46):
            x, y = rng.randrange(S), rng.randrange(S)
            c = rgb(rng.choice(cols))[:3]
            shape_ = rng.choice(([(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 0), (0, 1), (1, 1)], [(0, 0)],
                                 [(0, 0), (1, 1)], [(0, 0), (1, 0), (2, 0)]))
            lit = rng.uniform(-14, 10)
            for (dx, dy) in shape_:
                p[(x + dx) % S, (y + dy) % S] = M.rgba(M.lift(c, lit + (6 if (dx, dy) == (0, 0) else 0)))
        save(img, "confetti" + ("" if k == 0 else f"-{k + 1}"))
    for c, h in (("white", 0xF2F2EE), ("orange", 0xF08A3C), ("lime", 0x9ACD3C), ("red", 0xD23A34), ("black", 0x3A3A3E)):
        # moulded plastic: a soft fall of light down each face (lit top, a little shade at the foot), a faint sheen
        img = M.noise_hv(rgb(h)[:3], 1.5, seed_of("b14plastic" + c), mottle=2.5, cells=(16, 8), hue=1.0)
        for y in range(S):
            for x in range(S):
                M.touch(img, x, y, 0.07 * (1 - y / 15.5) if y < 16 else -0.05 * (y - 16) / 15)
        for x in range(S):
            M.touch(img, x, 0, 0.08)
        save(img, f"plastic-{c}")
    save(M.fabric(seed_of("b14speakercloth"), base=(30, 30, 32), weave="plain", contrast=5, grain=2, mottle=2), "speakercloth")
    img = M.noise_hv((48, 48, 50), 2, seed_of("b14cone"), mottle=2)
    save(img, "speakercone")
    save(M.painted_metal(seed_of("b14speakerbody"), base=(62, 62, 64), panel=False, chips=1, under=(110, 110, 112)), "speakerbody")


def b14_textures():
    b14_paint()
    b14_tiles()
    b14_vinyl()
    b14_carpets()
    b14_elevator()
    b14_signs()
    b14_party()


# ---- B14 models and versions

def b14_tex(key):
    return tpath(key).replace("backrooms:", "")


def b14_entry(keys):
    return {"base": b14_tex(keys[0]), "alternates": [{"base": b14_tex(k)} for k in keys[1:]]}


def b14_patch(fname, fn):
    path = os.path.join(ASSETS, "blocktypes", "fun", fname + ".json")
    with open(path, encoding="utf-8") as f:
        text_ = f.read()
    comment = None
    if text_.startswith("//"):
        head, _, text_ = text_.partition("\n")
        comment = head[3:]
    data = json.loads(text_)
    fn(data)
    write_json(path, data, comment)


def b14_wall_versions():
    """The painted walls' and the promenade's versions (alternates), picked by height too (randomizeAxes xyz); the low
    block above the skirting has four, the rubbed one listed once in seven."""
    def paint(data):
        for c in PAINTS:
            data["texturesByType"][f"*-{c}"] = {"all": b14_entry([f"paint-{c}", f"paint-{c}-2", f"paint-{c}-3"])}
        data["randomizeAxes"] = "xyz"
    b14_patch("fun-paint", paint)

    def prom(data):
        data["textures"] = {"all": b14_entry(["promwall", "promwall-2", "promwall-3"])}
        data["randomizeAxes"] = "xyz"
    b14_patch("fun-promwall", prom)

    def low(data):
        data["textures"] = {f"paint-{c}-low": b14_entry([f"paint-{c}-low"] + [f"paint-{c}-low-{k}" for k in (2, 3, 2, 3, 4)] +
                                                        [f"paint-{c}-low"]) for c in PAINTS}
    b14_patch("fun-paint-skirted", low)

    def band(data):
        data["textures"] = {"promwall": b14_entry(["promwall", "promwall-2", "promwall-3"])}
    b14_patch("fun-promwall-band", band)


def confetti_alts_b14():
    keys = [(k, r) for k in ("confetti", "confetti-2", "confetti-3") for r in (0, 90, 180, 270)]
    return {"base": b14_tex(keys[0][0]), "alternates": [dict({"base": b14_tex(k)}, **({"rotation": r} if r else {}))
                                                         for k, r in keys[1:]]}


def wbx(nm, frm, to, tex, faces):
    """A box whose faces take world-aligned UVs, so a strip standing on a door shows the door's own texture there."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    uv = {"north": (16 - x1, 16 - y1, 16 - x0, 16 - y0), "south": (x0, 16 - y1, x1, 16 - y0),
          "west": (z0, 16 - y1, z1, 16 - y0), "east": (16 - z1, 16 - y1, 16 - z0, 16 - y0),
          "up": (x0, z0, x1, z1), "down": (x0, 16 - z1, x1, 16 - z0)}
    el = bx(nm, frm, to, tex, faces=faces)
    for f in el["faces"]:
        el["faces"][f]["uv"] = [round(min(16, max(0, v)), 4) for v in uv[f]]
    return el


def elevator_frame_b14(leaf, part, ptex):
    """(B14) A lift leaf's raised frame: a stile by the meeting edge and one by the post, a rail across the foot (lower)
    or the head (upper), 0.3 proud, in the leaf's own brass, so its face reads as a panel set into a frame."""
    m = (lambda x: x) if leaf == "l" else (lambda x: 16 - x)
    xa, xb = sorted((m(0.4), m(1.5)))
    xc, xd = sorted((m(13.4), m(14.6)))
    xl, xr = min(xa, xc), max(xb, xd)
    y0, y1 = (1.8, 16) if part == "lower" else (0, 14.2)
    faces = ("north", "east", "west")
    els = [wbx("StileIn", (xa, y0, -0.3), (xb, y1, 0), ptex, faces), wbx("StileOut", (xc, y0, -0.3), (xd, y1, 0), ptex, faces)]
    if part == "lower":
        els.append(wbx("RailFoot", (xl, 0.6, -0.3), (xr, 1.8, 0), ptex, ("north", "east", "west", "up", "down")))
    else:
        els.append(wbx("RailHead", (xl, 14.2, -0.3), (xr, 15.4, 0), ptex, ("north", "east", "west", "up", "down")))
    return els


def lift_dial_b14():
    """(B14) The floor dial over the left leaf: a face, a brass bezel round it, a red needle on a pivot."""
    els = [bx("Dial", (-4, 19.5, -0.8), (4, 23.5, 0), "liftdialface", faces=("north",), full=True, glow=60),
           bx("DialBack", (-4, 19.5, -0.8), (4, 23.5, 0), "brass", faces=("east", "west", "up", "down"))]
    for nm, frm, to in (("BezelT", (-4.4, 23.5, -1.1), (4.4, 23.9, 0)), ("BezelB", (-4.4, 19.1, -1.1), (4.4, 19.5, 0)),
                        ("BezelL", (-4.4, 19.5, -1.1), (-4, 23.5, 0)), ("BezelR", (4, 19.5, -1.1), (4.4, 23.5, 0))):
        els.append(bx(nm, frm, to, "brass", faces=("north", "east", "west", "up", "down")))
    els += [bx("Needle", (-0.15, 20.25, -1.0), (0.15, 22.6, -0.85), "liftneedle", rot=(0, 0, 38), origin=(0, 20.25, -0.9)),
            bx("Pivot", (-0.35, 19.9, -1.15), (0.35, 20.6, -0.8), "brass")]
    return els


def call_buttons_b14():
    """(B14) The call station in the right leaf's jamb (on its post, so it never stands out past a wall's end): a narrow
    brass plate with an up and a down button, lit a little."""
    F5 = ("north", "east", "west", "up", "down")
    return [bx("CallPlate", (0.1, 0.8, -1.25), (0.9, 5.2, -1.0), "liftplate", faces=F5),
            bx("CallUp", (0.25, 3.1, -1.45), (0.75, 3.7, -1.25), "liftbutton", glow=40, faces=F5),
            bx("CallDown", (0.25, 1.9, -1.45), (0.75, 2.5, -1.25), "liftbutton", glow=40, faces=F5)]


def speaker_b14():
    """(B14) The wall speaker, tipped down 10 degrees: its cabinet, a bezel round a recessed black cloth, a woofer and a
    tweeter set back behind four wire bars."""
    R = dict(rot=(-10, 0, 0), origin=(8, 12, 14.5))
    F5 = ("north", "east", "west", "up", "down")
    return [bx("Body", (5, 4, 11), (11, 12, 14.5), "speakerbody", **R),
            bx("BezelT", (5, 11.4, 10.4), (11, 12, 11), "speakerbody", faces=F5, **R),
            bx("BezelB", (5, 4, 10.4), (11, 4.6, 11), "speakerbody", faces=F5, **R),
            bx("BezelL", (5, 4.6, 10.4), (5.6, 11.4, 11), "speakerbody", faces=("north", "east", "west"), **R),
            bx("BezelR", (10.4, 4.6, 10.4), (11, 11.4, 11), "speakerbody", faces=("north", "east", "west"), **R),
            bx("Cloth", (5.6, 4.6, 10.9), (10.4, 11.4, 11), "speakercloth", faces=("north",), **R),
            bx("WooferH", (6.0, 5.8, 10.75), (10.0, 8.2, 10.9), "speakercone", faces=F5, **R),
            bx("WooferV", (6.8, 5.0, 10.75), (9.2, 9.0, 10.9), "speakercone", faces=F5, **R),
            bx("DustCap", (7.5, 6.5, 10.65), (8.5, 7.5, 10.75), "speakerbody", faces=F5, **R),
            bx("Tweeter", (7.3, 9.5, 10.7), (8.7, 10.9, 10.9), "speakercone", faces=F5, **R)] + [
        bx(f"Bar{k}", (5.6, y, 10.5), (10.4, y + 0.3, 10.65), "metaldark", faces=F5, **R) for k, y in enumerate((5.6, 7.2, 8.8, 10.4))]


def chair_b14(t):
    """(B14) A plastic stacking chair facing north: a moulded seat with a rolled front edge, the back tipped back; chrome
    tube legs joined by side stretchers, rubber glides. (D2) The back is the pre-B14 chair's again, as the user asked:
    three stepped slats, each set a little further back and the top one narrower, in the B14 shaded plastic (each
    slat shows the texture's lit top band, so every step has its own lit edge). The first slat starts at the B14 seat's
    top (8.8; the old seat was 0.2 higher); B14's one shell, rolled top and foot are gone."""
    R = dict(rot=(-8, 0, 0), origin=(8, 9, 13.5))
    return [bx("Seat", (2.5, 7.8, 2.6), (13.5, 8.8, 13.5), t),
            bx("SeatRoll", (2.5, 7.2, 2.0), (13.5, 8.6, 2.6), t),
            bx("SeatSkirtL", (2.5, 7.0, 3.0), (3.0, 7.8, 12.8), t, faces=("east", "west", "down")),
            bx("SeatSkirtR", (13.0, 7.0, 3.0), (13.5, 7.8, 12.8), t, faces=("east", "west", "down")),
            bx("Back1", (2.5, 8.8, 13), (13.5, 12, 14), t, **R),
            bx("Back2", (2.5, 12, 13.4), (13.5, 15, 14.4), t, **R),
            bx("Back3", (3, 15, 13.8), (13, 18.5, 14.8), t, **R),
            bx("Leg1", (3, 0.4, 3), (3.8, 7.2, 3.8), "chrome"), bx("Leg2", (12.2, 0.4, 3), (13, 7.2, 3.8), "chrome"),
            bx("Leg3", (3, 0.4, 12.2), (3.8, 7.8, 13), "chrome"), bx("Leg4", (12.2, 0.4, 12.2), (13, 7.8, 13), "chrome"),
            bx("StretchL", (3.05, 2.4, 3.8), (3.75, 3.0, 12.2), "chrome"), bx("StretchR", (12.25, 2.4, 3.8), (12.95, 3.0, 12.2), "chrome"),
            bx("Glide1", (2.9, 0, 2.9), (3.9, 0.4, 3.9), "rubber"), bx("Glide2", (12.1, 0, 2.9), (13.1, 0.4, 3.9), "rubber"),
            bx("Glide3", (2.9, 0, 12.1), (3.9, 0.4, 13.1), "rubber"), bx("Glide4", (12.1, 0, 12.1), (13.1, 0.4, 13.1), "rubber")]


def main():
    args = sys.argv[1:]
    if "--no-models" not in args:
        import gen_fun_models
        gen_fun_models.main()
    if "--no-sounds" not in args:
        import gen_fun_sounds
        gen_fun_sounds.main()
    surface_textures()
    prop_textures()
    b14_textures()
    surfaces()
    props()
    items()
    entities()
    lang()
    merge_lang()
    check()


if __name__ == "__main__":
    main()
