"""The item model pass (0.700), package "treats": the levels' own food and drink get real 3D models instead of the flat
32 x 32 sprite the game extrudes from a texture.

    python tools/gen_items_treats.py          # writes shapes/item/treats/*.json and textures/item/treats/*.png

Level 188's breakfast (a paper cereal cup, a juice box), Kitty's House 974 (wrapped pastel candies, a striped bag of
marshmallows, a strawberry-milk carton, the three remembered meals on her pink-rimmed plate), Level 3999's arcade (a can
of Paradise Pop in three flavours, a striped popcorn bucket, cotton candy on a paper cone, six tray meals on a red
food-court tray), Level Fun (two cake slices on party plates, a chocolate-chip cookie, a vial of LUCA Tears), Level 31's
snack bar (two pizza slices, wings in a checked paper boat, a foot-long hot dog) and The End's Memory Juice.

How a model is made: each part is a box (`Box`) whose faces name a painter, a function that paints that face's pixels
(`w` x `h`, 2 pixels to a shape unit, as vanilla's 32-px item textures over 16 units). `Model.write` packs every face
into one texture atlas per model, paints it, and writes the shape with the matching UVs, so a model's texture is drawn
for its faces, not tiled. A family that shares a geometry (the three cans, the two pizzas) packs the same way and gets
one shape and a texture per variant, set by the item type's `texturesByType`.

The item types themselves are written by the levels' own generators (gen_188_props, gen_974, gen_3999_items, gen_fun,
gen_31_content, gen_end): each calls `dress(code, data)` from here, which swaps the flat texture for the model and sets
the four transforms and the ground-storage size. Nothing else about the items (codes, nutrition, classes, stacks)
changes. The old sprite textures stay: blocks still use some of them (the cereal dispenser, the cookie plates).
"""
import json
import math
import os
import random
import zlib

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
P = 2  # texture pixels per shape unit (vanilla: a 32-px texture over a 16-unit block)


# ======================================================================== Colour and pixel kit

def hx(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)


def shade(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3]) + (c[3] if len(c) > 3 else 255,)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


def warm(c, t):
    """Lit pixels drift a little warm, shaded ones cool (as the vanilla items are painted)."""
    r, g, b = c[:3]
    return (max(0, min(255, int(r + 6 * t))), g, max(0, min(255, int(b - 6 * t))), c[3] if len(c) > 3 else 255)


def seed(*parts):
    return zlib.crc32("/".join(str(p) for p in parts).encode()) & 0xFFFFFFFF


def new(w, h, c=(0, 0, 0, 0)):
    return Image.new("RGBA", (max(1, w), max(1, h)), c)


def fill(w, h, c, rng, grad=0.14, noise=0.05, edge=0.86, light="top", lo=None):
    """A painted surface: `c` lit from the top (light 'top', for sides) or evenly ('flat', for tops), darker towards
    the bottom by `grad`, a fine grain of `noise`, the border pixels shaded by `edge` (1 = none). `lo` mixes towards a
    second colour at the bottom instead of only darkening."""
    img = new(w, h)
    px = img.load()
    for y in range(h):
        t = (y + 0.5) / h if light == "top" else 0.5
        for x in range(w):
            k = 1 + grad * (0.5 - t) * 2 if light == "top" else 1.0
            col = mix(c, lo, t) if lo else c
            k *= 1 + rng.uniform(-noise, noise)
            if edge != 1 and w > 2 and h > 2 and (x in (0, w - 1) or y in (0, h - 1)):
                k *= edge
            col = warm(shade(col, k), k - 1)
            px[x, y] = col
    return img


def put(img, x, y, c):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), c)


def get(img, x, y):
    return img.getpixel((min(img.width - 1, max(0, int(x))), min(img.height - 1, max(0, int(y)))))


def tint(img, x, y, k):
    if 0 <= x < img.width and 0 <= y < img.height:
        img.putpixel((int(x), int(y)), shade(img.getpixel((int(x), int(y))), k))


def rect(img, x0, y0, x1, y1, c, rng=None, noise=0.04):
    for y in range(max(0, y0), min(img.height, y1)):
        for x in range(max(0, x0), min(img.width, x1)):
            img.putpixel((x, y), shade(c, 1 + (rng.uniform(-noise, noise) if rng else 0)))


def band(img, y0, y1, c, rng=None, noise=0.04, grad=0.0):
    for y in range(max(0, y0), min(img.height, y1)):
        t = (y - y0 + 0.5) / max(1, y1 - y0)
        for x in range(img.width):
            img.putpixel((x, y), shade(c, (1 + grad * (0.5 - t)) * (1 + (rng.uniform(-noise, noise) if rng else 0))))


def disc(img, cx, cy, r, c, rng=None, rim=None):
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if d <= r:
                col = c
                if rim and d > r - 1:
                    col = rim
                elif d < r * 0.5 and x + 0.5 < cx and y + 0.5 < cy:
                    col = shade(c, 1.12)
                put(img, x, y, shade(col, 1 + (rng.uniform(-0.04, 0.04) if rng else 0)))


def speckle(img, rng, colours, n, area=None, size=1):
    x0, y0, x1, y1 = area or (0, 0, img.width, img.height)
    if x1 <= x0 or y1 <= y0:
        return
    for _ in range(n):
        x, y = rng.randrange(x0, x1), rng.randrange(y0, y1)
        c = rng.choice(colours)
        for dy in range(size):
            for dx in range(size):
                put(img, x + dx, y + dy, c)


def grime(img, rng, n, k=0.88):
    """A few slightly darker pixels: handling, a little dirt (never noise all over)."""
    for _ in range(n):
        tint(img, rng.randrange(img.width), rng.randrange(img.height), k)


def stripes_v(w, h, c1, c2, period, rng, phase=0, **kw):
    img = fill(w, h, c1, rng, **kw)
    for x in range(w):
        if ((x + phase) // period) % 2:
            for y in range(h):
                k = img.getpixel((x, y))[0] / max(1, c1[0]) if c1[0] else 1
                img.putpixel((x, y), shade(c2, k))
    return img


def checks(w, h, c1, c2, size, rng, edge=0.9):
    img = new(w, h)
    for y in range(h):
        for x in range(w):
            c = c1 if ((x // size) + (y // size)) % 2 else c2
            k = 1 + rng.uniform(-0.04, 0.04)
            if edge != 1 and (x in (0, w - 1) or y in (0, h - 1)) and w > 2 and h > 2:
                k *= edge
            img.putpixel((x, y), shade(c, k))
    return img


def print_lines(img, x0, x1, ys, c, rng, gap=0.25):
    """Fine print: rows of short dashes, never letters."""
    for y in ys:
        x = x0
        while x < x1:
            n = rng.randint(1, 3)
            for i in range(n):
                if x + i < x1:
                    put(img, x + i, y, c)
            x += n + (1 if rng.random() > gap else 2)


def heart(img, cx, cy, c, big=False):
    pat = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"] if big else ["1010", "1111", "0110"]
    hw = len(pat[0]) // 2
    for j, row in enumerate(pat):
        for i, ch in enumerate(row):
            if ch == "1":
                put(img, cx - hw + i, cy + j, c)


# ======================================================================== Models

FACES = ("north", "east", "south", "west", "up", "down")
SIDES = ("north", "east", "south", "west")
WRAP_ORDER = ("north", "west", "south", "east")  # left to right round a box, each side seen from outside


class Box:
    """A part. `paint` maps faces to painters (fn(w, h, rng) -> Image): keys are face names, 'side' (the four sides),
    'all', or 'wrap' (fn(total_w, h, rng) painted once round the four sides). A face given None is left out.
    `rot` is (axis, degrees) about `origin` (the box's centre by default)."""

    def __init__(self, name, frm, to, paint, rot=None, origin=None, glow=0):
        self.name, self.frm, self.to, self.rot, self.origin, self.glow = name, list(frm), list(to), rot, origin, glow
        faces = {}
        for k in ("all", "side"):
            if k in paint:
                for f in (FACES if k == "all" else SIDES):
                    faces[f] = paint[k]
        for f in FACES:
            if f in paint:
                faces[f] = paint[f]
        self.wrap = paint.get("wrap")
        if self.wrap:
            for f in SIDES:
                faces.setdefault(f, "wrap")
        self.faces = {f: p for f, p in faces.items() if p is not None}

    def size(self, face):
        w, h, d = (abs(self.to[i] - self.frm[i]) for i in range(3))
        return {"north": (w, h), "south": (w, h), "east": (d, h), "west": (d, h), "up": (w, d), "down": (w, d)}[face]


def B(name, x0, y0, z0, x1, y1, z1, paint, **kw):
    return Box(name, (x0, y0, z0), (x1, y1, z1), paint, **kw)


def px_size(units):
    return max(1, int(round(units * P)))


def pack(rects, width):
    """Shelf packing: rects (key, w, h) into `width`; returns ({key: (x, y)}, height) or None if one is too wide."""
    pos, x, y, shelf = {}, 0, 0, 0
    for key, w, h in sorted(rects, key=lambda r: (-r[2], -r[1], r[0])):
        if w > width:
            return None
        if x + w > width:
            x, y, shelf = 0, y + shelf, 0
        pos[key] = (x, y)
        x += w
        shelf = max(shelf, h)
    return pos, y + shelf


class Model:
    def __init__(self, name, boxes):
        self.name, self.boxes = name, boxes

    def layout(self):
        rects = []
        for i, b in enumerate(self.boxes):
            for f in b.faces:
                w, h = b.size(f)
                rects.append(((i, f), px_size(w), px_size(h)))
        for width in (16, 32, 64, 128):
            res = pack(rects, width)
            if res is None:
                continue
            pos, height = res
            side = 16
            while side < height:
                side *= 2
            if side <= width * 2:
                return pos, width, max(side, 16), rects
        raise ValueError(self.name + ": faces do not fit a 128-px atlas")

    def paint(self, variant=""):
        pos, W, H, rects = self.layout()
        img = new(W, H)
        sizes = {k: (w, h) for k, w, h in rects}
        for i, b in enumerate(self.boxes):
            if b.wrap:
                ws = [sizes[(i, f)][0] for f in WRAP_ORDER]
                h = sizes[(i, "north")][1]
                strip = b.wrap(sum(ws), h, random.Random(seed(self.name, variant, b.name, "wrap")))
                x = 0
                for f, w in zip(WRAP_ORDER, ws):
                    if b.faces.get(f) == "wrap":
                        img.paste(strip.crop((x, 0, x + w, h)), pos[(i, f)])
                    x += w
            for f, fn in b.faces.items():
                if fn == "wrap":
                    continue
                w, h = sizes[(i, f)]
                part = fn(w, h, random.Random(seed(self.name, variant, b.name, f)))
                if part.size != (w, h):
                    part = part.resize((w, h), Image.NEAREST)
                img.paste(part, pos[(i, f)])
        return img, pos, W, H

    def shape(self, texture):
        pos, W, H, rects = self.layout()
        sizes = {k: (w, h) for k, w, h in rects}
        els = []
        for i, b in enumerate(self.boxes):
            faces = {}
            for f in FACES:
                if f not in b.faces:
                    continue
                x, y = pos[(i, f)]
                w, h = sizes[(i, f)]
                face = {"texture": "#tex", "uv": [x / P, y / P, (x + w) / P, (y + h) / P]}
                if b.glow:
                    face["glow"] = b.glow
                faces[f] = face
            el = {"name": b.name, "from": [round(v, 4) for v in b.frm], "to": [round(v, 4) for v in b.to], "faces": faces}
            if b.rot:
                axis, deg = b.rot
                el["rotationOrigin"] = list(b.origin) if b.origin else [round((b.frm[k] + b.to[k]) / 2, 4) for k in range(3)]
                el["rotation" + axis.upper()] = deg
            els.append(el)
        return {"textureWidth": W // P, "textureHeight": H // P, "textures": {"tex": "backrooms:" + texture}, "elements": els}

    def extent(self):
        lo, hi = [99.0] * 3, [-99.0] * 3
        for b in self.boxes:
            for k in range(3):
                lo[k] = min(lo[k], b.frm[k], b.to[k])
                hi[k] = max(hi[k], b.frm[k], b.to[k])
        return lo, hi


def tex_path(name):
    return f"item/treats/{name}"


def write_model(model, variants=None):
    """Writes the model's shape (shapes/item/treats/<name>.json) and its texture, or one texture per variant
    (<name>-<variant>.png) when `variants` maps variant names to the painter set the model is built with."""
    shapes_dir = os.path.join(ASSETS, "shapes", "item", "treats")
    tex_dir = os.path.join(ASSETS, "textures", "item", "treats")
    os.makedirs(shapes_dir, exist_ok=True)
    os.makedirs(tex_dir, exist_ok=True)
    first = None
    for v, m in (variants or {"": model}).items():
        name = model.name + (f"-{v}" if v else "")
        img, *_ = m.paint(v)
        img.save(os.path.join(tex_dir, name + ".png"))
        first = first or name
    with open(os.path.join(shapes_dir, model.name + ".json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(model.shape(tex_path(first)), indent="\t") + "\n")


# ======================================================================== Shared parts

def cross(name, cx, cz, dx, dz, y0, y1, paint_a, paint_b=None, k=0.62, inset=0.03):
    """A round thing as two crossed boxes (dx wide by dz deep, each narrowed to `k` the other way). The second is held
    `inset` inside the first at top and bottom so their caps never fight."""
    a = B(name + "A", cx - dx / 2, y0, cz - dz * k / 2, cx + dx / 2, y1, cz + dz * k / 2, paint_a)
    b = B(name + "B", cx - dx * k / 2, y0 + inset, cz - dz / 2, cx + dx * k / 2, y1 - inset, cz + dz / 2, paint_b or paint_a)
    return [a, b]


def surf(c, **kw):
    return lambda w, h, rng: fill(w, h, c, rng, **kw)


def top(c, **kw):
    kw.setdefault("light", "flat")
    return lambda w, h, rng: fill(w, h, c, rng, **kw)


ALU = hx("c9ccd2")  # can aluminium
PAPER = hx("f1ece0")
WHITE = hx("f6f3ec")


def metal(c=ALU, **kw):
    """Brushed metal: a bright streak a third of the way across, darker edges."""
    def fn(w, h, rng):
        img = fill(w, h, c, rng, grad=0.25, noise=0.03, edge=0.8, **kw)
        x = max(0, w // 3)
        for y in range(h):
            tint(img, x, y, 1.18)
        return img
    return fn


# ======================================================================== Level 3999: Paradise Pop (cherry, lime, grape)

FLAVOURS = {
    "cherry": {"base": hx("c8143c"), "band": hx("ff4fa8"), "dark": hx("6e0a24")},
    "lime": {"base": hx("1d9e45"), "band": hx("d2ff3c"), "dark": hx("0b4f22")},
    "grape": {"base": hx("6420b4"), "band": hx("3ce6ff"), "dark": hx("2c0c5e")},
}


def can_label(fl, emblem):
    f = FLAVOURS[fl]

    def fn(w, h, rng):
        img = fill(w, h, f["base"], rng, grad=0.22, noise=0.04, edge=1)
        band(img, 0, 1, shade(ALU, 1.05), rng)                     # the rolled rim
        band(img, 1, 3, f["band"], rng, grad=0.2)                   # the neon band
        band(img, h - 2, h - 1, f["dark"], rng)
        band(img, h - 1, h, shade(ALU, 0.85), rng)                  # the bottom seam
        band(img, 3, 4, shade(WHITE, 0.97), rng)                    # a white pinstripe under the band
        if emblem and w >= 4:
            cx, cy = w / 2, 3 + (h - 5) / 2 + 0.5
            if fl == "cherry":
                disc(img, cx - 1, cy + 0.5, 1.2, hx("e8203c"), rim=hx("7a0818"))
                disc(img, cx + 1, cy + 1, 1.2, hx("e8203c"), rim=hx("7a0818"))
                put(img, int(cx - 1) - 1, int(cy) - 1, shade(WHITE, 1))
                put(img, int(cx), int(cy) - 2, hx("4ec23a"))
                put(img, int(cx) + 1, int(cy) - 2, hx("2e8a24"))
            elif fl == "lime":
                disc(img, cx, cy, 2.0, hx("c8f07a"), rim=hx("2c8a2a"))
                put(img, int(cx), int(cy), shade(WHITE, 1))
                put(img, int(cx) - 1, int(cy) - 1, hx("f4ffe0"))
                put(img, int(cx) + 1, int(cy) + 1, hx("f4ffe0"))
            else:
                for dx, dy in ((-1, -1), (0, -1), (1, -1), (-0.5, 0), (0.5, 0), (0, 1)):
                    put(img, int(cx + dx), int(cy + dy), hx("b56cff") if (dx + dy) % 2 else hx("8a3cf0"))
                put(img, int(cx), int(cy) - 2, hx("4ec23a"))
        if not emblem:
            speckle(img, rng, [shade(f["band"], 0.9)], 1, area=(0, 5, w, h - 3))  # a fizz bubble
        return img
    return fn


def soda(fl="cherry"):
    lab_main, lab_hidden = can_label(fl, True), can_label(fl, False)
    lid = top(shade(ALU, 0.92), edge=0.85)
    return Model("l3999-soda", [
        *cross("Foot", 8, 8, 3.4, 3.4, 0, 0.45, {"side": metal(shade(ALU, 0.9)), "down": top(shade(ALU, 0.8))}),
        B("BodyA", 6, 0.45, 8 - 1.24, 10, 5.9, 8 + 1.24, {"north": lab_hidden, "south": lab_hidden, "east": lab_main, "west": lab_main}),
        B("BodyB", 8 - 1.24, 0.48, 6, 8 + 1.24, 5.87, 10, {"north": lab_main, "south": lab_main, "east": lab_hidden, "west": lab_hidden}),
        *cross("Shoulder", 8, 8, 3.5, 3.5, 5.9, 6.35, {"side": metal(), "up": lid}),
        B("Tab", 7.5, 6.35, 7.0, 8.5, 6.5, 8.3, {"all": metal(shade(ALU, 0.95))}),
    ])


class RimTop:
    """The top of a round part with a rim (a plate, a cup's lip): `inner` painted all over, `rim` (a painter of the
    whole face) laid along the outline of the two crossed boxes only, so the rims of the two never cross each other."""

    def __init__(self, inner, rim, width=1):
        self.inner, self.rim, self.width = inner, rim, width

    def for_box(self, along_x, d, k):
        def fn(w, h, rng):
            img, rim = self.inner(w, h, rng), self.rim(w, h, rng)
            wd = self.width
            for y in range(h):
                for x in range(w):
                    long, short, L, S = (x, y, w, h) if along_x else (y, x, h, w)
                    span = (L - L * k) / 2              # how far in from each end the long sides are the outline
                    end = long < wd or long >= L - wd
                    side = (short < wd or short >= S - wd) and (long < span + wd or long >= L - span - wd)
                    if end or side:
                        img.putpixel((x, y), rim.getpixel((x, y)))
            return img
        return fn


def round_part(name, cx, cz, d, y0, y1, main, hidden=None, up=None, down=None, k=0.62, inset=0.03, rot=None, origin=None):
    """`cross` with the faces sorted: the narrow faces of each box stand furthest out and carry `main` (a label, a
    badge); the wide faces are mostly hidden behind the other box and carry `hidden` (the plain colour). `up` may be a
    RimTop."""
    hidden = hidden or main
    up_a, up_b = (up.for_box(True, d, k), up.for_box(False, d, k)) if isinstance(up, RimTop) else (up, up)
    a = B(name + "A", cx - d / 2, y0, cz - d * k / 2, cx + d / 2, y1, cz + d * k / 2,
          {"north": hidden, "south": hidden, "east": main, "west": main, "up": up_a, "down": down}, rot=rot, origin=origin)
    b = B(name + "B", cx - d * k / 2, y0 + inset, cz - d / 2, cx + d * k / 2, y1 - inset, cz + d / 2,
          {"north": main, "south": main, "east": hidden, "west": hidden, "up": up_b, "down": down}, rot=rot, origin=origin)
    return [a, b]


def wedge(name, cx, z_back, z_tip, w_back, w_tip, y0, y1, steps, paint, back=None, rot=None, origin=None):
    """A slice (pizza, cake) as boxes stepping from `w_back` wide at z_back to `w_tip` at z_tip; `back` paints the
    outer (crust) face of the widest step."""
    els = []
    dz = (z_tip - z_back) / steps
    for i in range(steps):
        w = w_back + (w_tip - w_back) * (i + 0.5) / steps
        p = dict(paint)
        if i == 0 and back:
            p["north"] = back
        if i:
            p["north"] = None
        els.append(B(f"{name}{i}", cx - w / 2, y0 + 0.01 * i, z_back + dz * i, cx + w / 2, y1 - 0.01 * i, z_back + dz * (i + 1), p,
                     rot=rot, origin=origin))
    return els


# ======================================================================== Level 3999: popcorn and cotton candy

RED = hx("d42a30")


def bucket_side(main):
    def fn(w, h, rng):
        img = stripes_v(w, h, hx("f4f0e8"), RED, 2, rng, phase=1, grad=0.2, edge=1, noise=0.03)
        band(img, 0, 1, shade(hx("f4f0e8"), 1.0), rng)
        if main and w >= 5 and h >= 4:                       # a yellow badge with a red star
            cx, cy = w / 2, h / 2
            disc(img, cx, cy, min(w, h) / 2 - 0.3, hx("ffd23c"), rim=hx("c88a10"))
            for dx, dy in ((0, 0), (-1, 0), (0, -1)):
                put(img, int(cx) + dx, int(cy) + dy, RED)
        grime(img, rng, max(1, w * h // 25), 0.9)
        return img
    return fn


def kernel_tex(w, h, rng):
    img = fill(w, h, hx("f6edd2"), rng, grad=0.2, noise=0.06, edge=0.9)
    speckle(img, rng, [hx("f2c84b"), hx("e8b030")], max(1, w * h // 4))     # butter
    speckle(img, rng, [hx("8a5a2a")], max(1, w * h // 14))                  # hulls
    return img


def popcorn():
    rim = RimTop(top(hx("f0e2b8")), top(hx("f4f0e8"), edge=1))
    els = []
    for i, (d, y0, y1) in enumerate(((3.8, 0, 2.3), (4.4, 2.3, 4.6), (5.0, 4.6, 6.5))):
        els += round_part(f"Tier{i}", 8, 8, d, y0, y1, bucket_side(i == 1), bucket_side(False),
                          up=rim if i == 2 else None, down=top(hx("e0d8c8")) if i == 0 else None)
    els += cross("Heap", 8, 8, 4.4, 4.4, 6.5, 7.2, {"all": kernel_tex}, k=0.7)
    for i, (x, z, y, r) in enumerate(((6.6, 7.0, 7.1, 20), (8.6, 6.6, 7.2, -35), (9.4, 8.6, 7.0, 10), (7.4, 9.2, 7.1, 45),
                                      (8.1, 8.0, 7.7, 30), (6.2, 8.6, 6.8, -15), (9.8, 7.1, 6.9, 60))):
        s = 1.1 if i != 4 else 1.3
        els.append(B(f"Kernel{i}", x - s / 2, y, z - s / 2, x + s / 2, y + s * 0.85, z + s / 2, {"all": kernel_tex}, rot=("y", r)))
    return Model("l3999-popcorn", els)


def fluff(c1, c2):
    def fn(w, h, rng):
        img = fill(w, h, c1, rng, grad=0.25, noise=0.05, edge=0.9)
        for _ in range(max(2, w * h // 6)):                   # wisps of the second colour
            x, y = rng.randrange(w), rng.randrange(h)
            for i in range(rng.randint(1, 3)):
                put(img, x + i, y + (i % 2), shade(c2, 1 + rng.uniform(-0.05, 0.05)))
        speckle(img, rng, [shade(c1, 1.15), hx("ffffff")], max(1, w * h // 12))   # sugar glints
        return img
    return fn


def cone_paper(w, h, rng):
    img = fill(w, h, hx("f4efe4"), rng, grad=0.2, edge=0.9)
    for y in range(h):                                         # a pink spiral stripe
        for x in range(w):
            if (x + y) % 4 == 0:
                img.putpixel((x, y), shade(hx("f07ab0"), 1 + rng.uniform(-0.05, 0.05)))
    return img


def cottoncandy():
    pink, blue = hx("ff9fd2"), hx("9fd6ff")
    els = []
    for i, (d, y0, y1) in enumerate(((0.8, 0, 1.8), (1.2, 1.8, 3.4), (1.7, 3.4, 4.8))):
        els += cross(f"Cone{i}", 8, 8, d, d, y0, y1, {"side": cone_paper, "down": top(hx("e8e0d0"))}, k=0.7)
    els += [
        B("FluffCore", 5.8, 4.4, 5.9, 10.2, 7.6, 10.1, {"all": fluff(pink, blue)}),
        B("FluffBlue", 6.6, 5.2, 6.4, 10.0, 8.4, 9.6, {"all": fluff(blue, pink)}, rot=("y", 30)),
        B("FluffTop", 6.8, 7.6, 6.9, 9.4, 9.2, 9.3, {"all": fluff(pink, blue)}, rot=("y", -20)),
        B("FluffSide", 4.9, 5.0, 7.0, 6.6, 7.0, 9.0, {"all": fluff(pink, hx("ffd0ea"))}),
        B("FluffPuff", 9.6, 5.6, 6.0, 11.0, 7.2, 7.8, {"all": fluff(blue, hx("d8f0ff"))}),
    ]
    return Model("l3999-cottoncandy", els)


# ======================================================================== Food painters shared by the levels

BUN = hx("c87a34")
CRUST = hx("d29a52")
CHEESE = hx("f2c048")
SAUCE = hx("b8321e")


def bread(c=BUN, top_light=True, seeds=False):
    def fn(w, h, rng):
        img = fill(w, h, c, rng, grad=0.3 if top_light else 0, noise=0.05, edge=0.85, light="top" if top_light else "flat")
        speckle(img, rng, [shade(c, 1.12)], max(1, w * h // 8))
        if seeds:
            speckle(img, rng, [hx("f6ecd0"), hx("fff6e0")], max(1, w * h // 14))
        return img
    return fn


def pizza_top(pepperoni=False):
    def fn(w, h, rng):
        img = fill(w, h, CHEESE, rng, light="flat", noise=0.06, edge=0.92)
        speckle(img, rng, [hx("f7d670"), hx("ffe08a")], max(1, w * h // 5))      # melted highlights
        speckle(img, rng, [hx("d98a28"), hx("c8761c")], max(1, w * h // 10))     # browned spots
        speckle(img, rng, [SAUCE], max(0, w * h // 18))                           # sauce showing through
        speckle(img, rng, [hx("4e8a2c")], max(0, w * h // 30))                    # a fleck of herb
        return img
    return fn


def pizza_edge(w, h, rng):
    img = fill(w, h, hx("e8c070"), rng, grad=0.2, edge=1)
    band(img, 0, 1, CHEESE, rng)
    if h > 2:
        band(img, h - 1, h, shade(CRUST, 0.85), rng)
    return img


def pepperoni_tex(w, h, rng):
    img = fill(w, h, hx("b2281e"), rng, light="flat", noise=0.06, edge=0.75)
    speckle(img, rng, [hx("e8a090"), hx("7a1810")], max(1, w * h // 4))
    return img


def checker_paper(c=hx("d42a30")):
    return lambda w, h, rng: checks(w, h, hx("f6f2ea"), c, 1, rng, edge=0.88)


def paper_plate(rim1, rim2):
    """A white paper plate with a squiggle of two colours round its rim (a RimTop for a round part)."""
    def inner(w, h, rng):
        img = fill(w, h, hx("f4f2ee"), rng, light="flat", noise=0.03, edge=1)
        speckle(img, rng, [hx("e8dcc0")], max(1, w * h // 40), area=(3, 3, max(4, w - 3), max(4, h - 3)))   # a grease spot
        return img

    def rim(w, h, rng):
        img = fill(w, h, hx("ece8e2"), rng, light="flat", noise=0.03, edge=1)
        for y in range(h):
            for x in range(w):
                if (x + y) % 4 == 0:
                    img.putpixel((x, y), rim1)
                elif (x - y) % 4 == 2:
                    img.putpixel((x, y), rim2)
        return img
    return RimTop(inner, rim, 2)


# ======================================================================== Level 3999: tray meals

def tray_liner(w, h, rng):
    img = fill(w, h, hx("f2eee6"), rng, light="flat", noise=0.03, edge=1)
    for y in range(0, h, 4):                                   # neon zigzags
        for x in range(w):
            put(img, x, y + (x % 3 == 1), hx("ff3ca8") if (y // 4) % 2 else hx("28c8f0"))
    speckle(img, rng, [hx("e4d4b4")], max(1, w * h // 60))      # grease
    return img


def tray(name, food):
    red = hx("c42430")
    side = surf(red, grad=0.2, edge=0.82)
    rim_top = top(shade(red, 1.12), edge=0.9)
    els = [
        B("Tray", 3, 0, 4.5, 13, 0.4, 11.5, {"side": side, "down": top(shade(red, 0.7))}),
        B("RimN", 3, 0.4, 4.5, 13, 0.9, 5.0, {"side": side, "up": rim_top}),
        B("RimS", 3, 0.4, 11.0, 13, 0.9, 11.5, {"side": side, "up": rim_top}),
        B("RimW", 3, 0.4, 5.0, 3.5, 0.9, 11.0, {"east": side, "west": side, "up": rim_top}),
        B("RimE", 12.5, 0.4, 5.0, 13, 0.9, 11.0, {"east": side, "west": side, "up": rim_top}),
        B("Liner", 3.5, 0.4, 5.0, 12.5, 0.45, 11.0, {"up": tray_liner}),
    ]
    return Model("l3999-traymeal-" + name, els + food)


def traymeal(meal="burger"):
    y = 0.45
    if meal == "burger":
        lettuce = lambda w, h, rng: checks(w, h, hx("7ccc44"), hx("5aa832"), 1, rng, edge=1)
        food = [
            *round_part("BunBottom", 7, 8, 4.0, y, y + 0.7, bread(), up=None, down=None),
            *round_part("Patty", 7, 8, 4.3, y + 0.7, y + 1.35, surf(hx("5a3220"), noise=0.1, edge=0.8), up=top(hx("5a3220"), noise=0.1)),
            B("Cheese", 5.2, y + 1.35, 6.2, 8.8, y + 1.57, 9.8, {"side": surf(CHEESE), "up": top(CHEESE)}, rot=("y", 45)),
            *round_part("Lettuce", 7, 8, 4.4, y + 1.57, y + 1.85, lettuce, up=lettuce),
            *round_part("BunTop", 7, 8, 4.1, y + 1.85, y + 2.75, bread(seeds=True), up=bread(top_light=False, seeds=True)),
            *round_part("Dome", 7, 8, 3.0, y + 2.75, y + 3.25, bread(seeds=True), up=bread(top_light=False, seeds=True)),
            B("FrySleeve", 10.0, y, 7.3, 11.8, y + 1.9, 8.7, {"side": lambda w, h, rng: stripes_v(w, h, RED, hx("ffd23c"), 3, rng, edge=0.85)}),
        ]
        fries = surf(hx("f7cf4f"), grad=0.1, edge=0.85)
        for i, (fx, fz, fh, r) in enumerate(((10.4, 7.6, 1.5, 0), (10.9, 8.1, 1.9, 10), (11.3, 7.7, 1.3, -8), (10.6, 8.3, 1.1, 5))):
            food.append(B(f"Fry{i}", fx - 0.18, y + 1.5, fz - 0.18, fx + 0.18, y + 1.9 + fh, fz + 0.18, {"side": fries, "up": top(hx("e0a838"))},
                          rot=("z", r)))
    elif meal == "pizza":
        food = pizza_slice(7.6, 5.6, 0.45, pepperoni=True, rot=-25)
    elif meal == "noodles":
        bowl = lambda w, h, rng: (lambda img: (band(img, 0, 2, hx("28c8f0"), rng), img)[1])(fill(w, h, hx("e83a2c"), rng, grad=0.25, edge=0.85))

        def noodles(w, h, rng):
            img = fill(w, h, hx("c8783a"), rng, light="flat", noise=0.05, edge=1)   # broth
            for yy in range(1, h - 1):
                for xx in range(1, w - 1):
                    if (xx + 2 * yy + rng.randrange(2)) % 3 == 0:
                        img.putpixel((xx, yy), shade(hx("f4d880"), 1 + rng.uniform(-0.06, 0.06)))
            speckle(img, rng, [hx("4cb040")], max(1, w * h // 14), area=(1, 1, w - 1, h - 1))   # spring onion
            for xx in range(w):
                put(img, xx, 0, hx("f4f0ea"))
                put(img, xx, h - 1, hx("f4f0ea"))
            for yy in range(h):
                put(img, 0, yy, hx("f4f0ea"))
                put(img, w - 1, yy, hx("f4f0ea"))
            return img
        wood = surf(hx("d8b078"), grad=0.1, edge=0.85)
        food = [
            *round_part("Foot", 7.4, 8, 3.0, y, y + 0.55, bowl),
            *round_part("Bowl", 7.4, 8, 4.8, y + 0.55, y + 2.4, bowl, up=noodles),
            B("Egg", 6.0, y + 2.4, 6.9, 7.4, y + 2.75, 8.0, {"side": surf(hx("f6f2e8")), "up": lambda w, h, rng: (lambda img: (disc(img, w / 2, h / 2, 1.1, hx("f2b82c")), img)[1])(fill(w, h, hx("f8f4ec"), rng, light="flat"))}),
            B("StickA", 9.0, y + 2.4, 5.6, 9.4, y + 2.75, 11.0, {"all": wood}, rot=("y", 18)),
            B("StickB", 9.7, y + 2.4, 5.4, 10.1, y + 2.75, 10.8, {"all": wood}, rot=("y", 26)),
        ]
    elif meal == "taco":
        food = []
        for n, cx in (("L", 6.2), ("R", 9.8)):
            shell = bread(hx("eec060"))
            food += [
                B(f"Shell{n}", cx - 0.9, y, 5.9, cx + 0.9, y + 0.5, 10.1, {"side": shell, "down": shell, "up": None}),
                B(f"Wall{n}W", cx - 1.25, y, 5.9, cx - 0.9, y + 2.3, 10.1, {"all": shell}, rot=("z", 14), origin=(cx - 0.9, y, 8)),
                B(f"Wall{n}E", cx + 0.9, y, 5.9, cx + 1.25, y + 2.3, 10.1, {"all": shell}, rot=("z", -14), origin=(cx + 0.9, y, 8)),
                B(f"Filling{n}", cx - 0.95, y + 0.5, 6.1, cx + 0.95, y + 1.9, 9.9, {"north": taco_fill, "south": taco_fill, "up": taco_fill}),
            ]
    elif meal == "icecream":
        cup = lambda w, h, rng: stripes_v(w, h, hx("f8f0f4"), hx("ff6ab4"), 2, rng, grad=0.2, edge=0.9)
        scoop = lambda c: lambda w, h, rng: (lambda img: (speckle(img, rng, [shade(c, 1.12)], max(1, w * h // 5)), img)[1])(fill(w, h, c, rng, grad=0.3, edge=0.88))
        sprinkles = lambda w, h, rng: (lambda img: (speckle(img, rng, [hx("ff3ca8"), hx("28c8f0"), hx("ffe23c"), hx("7cf04a")], max(1, w * h // 4)), img)[1])(fill(w, h, hx("f8e8c8"), rng, light="flat"))
        food = [
            *round_part("Cup", 7.6, 8, 3.2, y, y + 1.8, cup, down=None),
            *round_part("Scoop1", 7.6, 8, 3.5, y + 1.8, y + 3.0, scoop(hx("ff9cc8")), up=scoop(hx("ff9cc8"))),
            *round_part("Scoop2", 7.6, 8, 2.8, y + 3.0, y + 4.1, scoop(hx("f8eccc")), up=sprinkles),
            B("Cherry", 7.25, y + 4.1, 7.65, 7.95, y + 4.8, 8.35, {"all": surf(hx("d01828"), edge=0.8)}),
            B("Wafer", 8.6, y + 2.8, 7.6, 9.0, y + 5.2, 8.6, {"all": checks_fn(hx("e8b868"), hx("c89040"))}, rot=("z", -25)),
            B("Spoon", 9.6, y, 6.0, 10.0, y + 0.25, 10.2, {"all": surf(hx("ff3ca8"), edge=0.8)}, rot=("y", -20)),
        ]
    else:  # pretzel
        dough = bread(hx("8a4a1c"), seeds=True)
        dough_top = bread(hx("9a5422"), top_light=False, seeds=True)
        p = {"side": dough, "up": dough_top}
        food = [
            B("Belly", 5.0, y, 9.2, 10.4, y + 1.1, 10.4, p),
            B("SideW", 4.2, y, 6.4, 5.4, y + 1.1, 9.8, p),
            B("SideE", 10.0, y, 6.4, 11.2, y + 1.1, 9.8, p),
            B("LobeW", 4.8, y + 0.02, 5.6, 7.6, y + 1.08, 6.8, p),
            B("LobeE", 7.8, y + 0.02, 5.6, 10.6, y + 1.08, 6.8, p),
            B("TwistA", 6.7, y + 0.05, 6.2, 7.9, y + 1.25, 10.0, p, rot=("y", 30)),
            B("TwistB", 7.5, y + 0.08, 6.2, 8.7, y + 1.22, 10.0, p, rot=("y", -30)),
            *round_part("Mustard", 11.0, 6.4, 1.6, y, y + 0.9, surf(hx("f4f0e8")), up=top(hx("f0c020"))),
        ]
    return tray(meal, food)


def checks_fn(c1, c2):
    return lambda w, h, rng: checks(w, h, c1, c2, 1, rng, edge=0.9)


def taco_fill(w, h, rng):
    img = fill(w, h, hx("6a3c22"), rng, light="flat", noise=0.08, edge=1)      # meat
    speckle(img, rng, [hx("7ccc44"), hx("5aa832")], max(1, w * h // 3))           # lettuce
    speckle(img, rng, [hx("f4c43a")], max(1, w * h // 6))                         # cheese
    speckle(img, rng, [hx("e0402c")], max(1, w * h // 10))                        # tomato
    return img


# ======================================================================== Level 31: the snack bar

def pizza_slice(cx, z_back, y, pepperoni=False, rot=0, crust=True):
    """A slice lying flat, crust to the north, tip to the south (6 long, 5 wide), turned `rot` about its middle."""
    origin = (cx, y, z_back + 3)
    r = ("y", rot) if rot else None
    els = []
    if crust:
        els.append(B("Crust", cx - 2.65, y, z_back - 0.8, cx + 2.65, y + 0.85, z_back + 0.2,
                     {"side": bread(CRUST), "up": bread(shade(CRUST, 1.05), top_light=False)}, rot=r, origin=origin))
    els += wedge("Slice", cx, z_back + 0.2, z_back + 6.2, 5.0, 0.7, y, y + 0.55, 4, {"side": pizza_edge, "up": pizza_top(), "down": top(shade(CRUST, 0.9))},
                 rot=r, origin=origin)
    els.append(B("Drip", cx + 1.0, y - 0.4, z_back + 2.6, cx + 1.4, y + 0.5, z_back + 3.0, {"all": surf(CHEESE, edge=0.9)}, rot=r, origin=origin))
    if pepperoni:
        for i, (dx, dz) in enumerate(((-1.2, 1.2), (1.0, 1.5), (-0.1, 3.0), (0.2, 4.6))):
            s = 1.2 if i < 3 else 0.9
            els.append(B(f"Pepperoni{i}", cx + dx - s / 2, y + 0.55, z_back + dz - s / 2, cx + dx + s / 2, y + 0.75, z_back + dz + s / 2,
                         {"side": surf(hx("8a1c14")), "up": pepperoni_tex}, rot=r, origin=origin))
    return els


def l31_pizza(kind="pizza"):
    plate = paper_plate(hx("1fb8b0"), hx("8a3cc8"))
    return Model("l31-" + kind, [
        *round_part("Plate", 8, 8, 8.0, 0, 0.3, surf(hx("e8e4dc"), edge=0.9), up=plate, down=top(hx("dcd6cc")), k=0.7),
        *pizza_slice(8, 5.2, 0.3, pepperoni=(kind == "pepperoni")),
    ])


def boat(x0, z0, x1, z1, h, c=hx("d42a30")):
    """A checked paper food boat with low walls."""
    paper = checker_paper(c)
    t = 0.3
    return [
        B("BoatBase", x0, 0, z0, x1, 0.3, z1, {"up": paper, "down": top(hx("e4dcd0")), "side": paper}),
        B("BoatN", x0, 0.3, z0, x1, h, z0 + t, {"all": paper}),
        B("BoatS", x0, 0.3, z1 - t, x1, h, z1, {"all": paper}),
        B("BoatW", x0, 0.3, z0 + t, x0 + t, h, z1 - t, {"all": paper}),
        B("BoatE", x1 - t, 0.3, z0 + t, x1, h, z1 - t, {"all": paper}),
    ]


def wing_tex(w, h, rng):
    img = fill(w, h, hx("c8501e"), rng, grad=0.3, noise=0.08, edge=0.8)
    speckle(img, rng, [hx("e8783a"), hx("f09a50")], max(1, w * h // 4))   # glaze
    speckle(img, rng, [hx("5a2410")], max(1, w * h // 9))                  # char
    return img


def l31_wings():
    els = boat(4.8, 5.4, 11.2, 10.6, 1.6)
    for i, (x, z, yy, r) in enumerate(((6.6, 7.2, 0.3, 25), (9.2, 7.0, 0.3, -40), (7.4, 9.2, 0.3, 70), (9.0, 9.0, 1.0, 10))):
        els.append(B(f"Wing{i}", x - 1.3, yy, z - 0.7, x + 1.3, yy + 1.2, z + 0.7, {"all": wing_tex}, rot=("y", r)))
        els.append(B(f"Tip{i}", x + 1.1, yy + 0.1, z - 0.45, x + 2.2, yy + 0.9, z + 0.45, {"all": wing_tex}, rot=("y", r), origin=(x, yy, z)))
    els.append(B("Celery", 5.4, 1.0, 8.2, 10.4, 1.6, 8.8, {"all": lambda w, h, rng: stripes_v(w, h, hx("a8d870"), hx("88c050"), 1, rng, edge=0.85)},
                 rot=("y", -30)))
    return Model("l31-wings", els)


def l31_hotdog():
    els = boat(2.6, 6.2, 13.4, 9.8, 1.4, c=hx("2a6ad4"))
    bun, bun_top = bread(hx("e0a458")), bread(hx("e8b468"), top_light=False)
    els += [
        B("BunW", 2.9, 0.3, 6.5, 13.1, 1.7, 7.9, {"side": bun, "up": bun_top}),
        B("BunE", 2.9, 0.3, 8.1, 13.1, 1.7, 9.5, {"side": bun, "up": bun_top}),
        B("Sausage", 2.2, 1.0, 7.4, 13.8, 2.1, 8.6, {"side": sausage_side, "up": sausage_top}),
    ]
    return Model("l31-hotdog", els)


def sausage_side(w, h, rng):
    img = fill(w, h, hx("b2482a"), rng, grad=0.3, noise=0.05, edge=0.85)
    for x in range(1, w, 4):                                       # grill marks
        put(img, x, 0, hx("5a2010"))
        put(img, x + 1, 1, hx("5a2010"))
    return img


def sausage_top(w, h, rng):
    img = fill(w, h, hx("c0522e"), rng, light="flat", noise=0.05, edge=0.88)
    for x in range(w):                                             # a mustard zigzag
        put(img, x, (x // 2) % max(1, h - 1) if h > 1 else 0, hx("f6d21c"))
    speckle(img, rng, [hx("4a9a2a")], max(1, w * h // 8))         # relish
    return img


# ======================================================================== Level 188: breakfast

def cereal_cup(main):
    def fn(w, h, rng):
        img = fill(w, h, hx("f4f2ec"), rng, grad=0.18, noise=0.03, edge=1)
        if h >= 3:
            band(img, h // 2 - 1, h // 2 + 1, hx("2a5ab8"), rng)        # the blue band
        if main and w >= 5 and h >= 5:                                    # a yellow sun on the band
            disc(img, w / 2, h / 2, 1.6, hx("f6c42a"), rim=hx("d8941a"))
        grime(img, rng, max(1, w * h // 30), 0.9)
        return img
    return fn


def cereal_bits(w, h, rng):
    """A toasted oat ring: golden, its hole dark in the middle of the top."""
    img = fill(w, h, hx("d8a040"), rng, light="flat" if w == h else "top", noise=0.08, edge=0.85)
    if w == h and w >= 2:
        put(img, w // 2 - (w % 2 == 0), h // 2 - (h % 2 == 0), hx("6a4018"))
        put(img, 0, 0, hx("f0c868"))
    return img


def l188_cereal():
    els = []
    for i, (d, y0, y1) in enumerate(((4.0, 0, 1.6), (4.6, 1.6, 3.2), (5.2, 3.2, 4.0))):
        els += round_part(f"Cup{i}", 8, 8, d, y0, y1, cereal_cup(i == 1), cereal_cup(False),
                          up=RimTop(top(hx("c89038")), top(hx("f4f2ec"), edge=1)) if i == 2 else None, down=top(hx("e8e4dc")) if i == 0 else None)
    for i, (x, z, yy, s) in enumerate(((7.0, 7.2, 3.95, 1.2), (8.9, 7.6, 4.0, 1.1), (7.8, 9.0, 3.95, 1.2), (9.2, 9.1, 3.9, 1.0),
                                       (8.0, 8.0, 4.4, 1.2), (6.6, 8.6, 3.9, 1.0))):
        els.append(B(f"Loop{i}", x - s / 2, yy, z - s / 2, x + s / 2, yy + 0.7, z + s / 2, {"all": cereal_bits}, rot=("y", (i * 37) % 90)))
    foil = lambda w, h, rng: (lambda img: (print_lines(img, 1, w - 1, range(1, h - 1, 2), hx("2a5ab8"), rng), img)[1])(
        fill(w, h, hx("d8dce4"), rng, light="flat", noise=0.05, edge=0.8))
    els.append(B("Lid", 6.2, 4.0, 4.6, 9.8, 4.15, 6.0, {"up": foil, "down": top(hx("b8bcc4")), "side": surf(hx("c8ccd4"))},
                 rot=("x", 35), origin=(8, 4.0, 6.0)))
    return Model("l188-cereal", els)


def juice_front(w, h, rng):
    img = fill(w, h, hx("f39a1e"), rng, grad=0.2, noise=0.04, edge=0.85)
    band(img, h - 3, h - 1, hx("f8f0e0"), rng)                       # the white wave
    for x in range(w):
        put(img, x, h - 3 - (x % 3 == 0), hx("f8f0e0"))
    cx, cy = w / 2, h / 2 - 1
    disc(img, cx, cy, 2.2, hx("ffb83a"), rim=hx("e06a10"))           # an orange
    put(img, int(cx), int(cy - 2.5), hx("3ea830"))                  # its leaf
    put(img, int(cx) + 1, int(cy - 2.5), hx("2e8a24"))
    put(img, int(cx) - 1, int(cy) - 1, hx("fff0c8"))
    print_lines(img, 1, w - 1, [1], hx("8a3a08"), rng)
    return img


def juice_side(w, h, rng):
    img = fill(w, h, hx("f39a1e"), rng, grad=0.2, noise=0.04, edge=0.85)
    rect(img, 1, 2, w - 1, h - 3, hx("f8f0e0"), rng)                  # the nutrition panel
    print_lines(img, 1, w - 1, range(3, h - 3, 2), hx("9a9488"), rng)
    return img


def l188_juicebox():
    def straw(w, h, rng):
        img = fill(w, h, hx("f8f4ec"), rng, edge=1)
        for y in range(0, h, 3):                                    # a red stripe winding round it
            band(img, y, y + 1, hx("e83a3a"))
        return img
    return Model("l188-juicebox", [
        B("Box", 6.6, 0, 7.1, 9.4, 4.6, 8.9, {"north": juice_front, "south": juice_front, "east": juice_side, "west": juice_side,
                                               "up": top(hx("f0a030"), edge=0.8), "down": top(hx("c87818"))}),
        B("Seal", 6.55, 4.6, 7.8, 9.45, 4.85, 8.2, {"all": surf(hx("f4a632"), edge=0.8)}),
        B("FlapW", 6.45, 3.7, 7.3, 6.6, 4.6, 8.7, {"all": surf(hx("e08a18"), edge=0.85)}),
        B("FlapE", 9.4, 3.7, 7.3, 9.55, 4.6, 8.7, {"all": surf(hx("e08a18"), edge=0.85)}),
        B("Straw", 8.6, 4.6, 7.35, 8.95, 7.0, 7.7, {"all": straw}),
        B("StrawBend", 8.6, 7.0, 7.35, 8.95, 8.2, 7.7, {"all": straw}, rot=("z", 40), origin=(8.775, 7.0, 7.525)),
    ])


# ======================================================================== Level 974: Kitty's House (pastel, cosy)

MINT, LILAC, BUTTER, PINK = hx("a8f0cf"), hx("cdb4f0"), hx("fbe48f"), hx("f7a8c4")


def cellophane(c):
    def fn(w, h, rng):
        img = fill(w, h, c, rng, grad=0.25, noise=0.04, edge=0.85)
        for x in range(w):                                       # white twist stripes
            if x % 3 == 1:
                for y in range(h):
                    tint(img, x, y, 1.12)
        put(img, 1 if w > 2 else 0, 0, hx("ffffff"))             # a glint
        return img
    return fn


def candy(cx, cz, y, c, r, n):
    o = (cx, y, cz)
    p = {"all": cellophane(c)}
    return [
        B(f"Candy{n}", cx - 0.9, y, cz - 0.65, cx + 0.9, y + 1.3, cz + 0.65, p, rot=("y", r), origin=o),
        B(f"Knot{n}W", cx - 1.2, y + 0.35, cz - 0.3, cx - 0.9, y + 0.95, cz + 0.3, p, rot=("y", r), origin=o),
        B(f"Twist{n}W", cx - 1.8, y + 0.1, cz - 0.6, cx - 1.2, y + 1.2, cz + 0.6, p, rot=("y", r), origin=o),
        B(f"Knot{n}E", cx + 0.9, y + 0.35, cz - 0.3, cx + 1.2, y + 0.95, cz + 0.3, p, rot=("y", r), origin=o),
        B(f"Twist{n}E", cx + 1.2, y + 0.1, cz - 0.6, cx + 1.8, y + 1.2, cz + 0.6, p, rot=("y", r), origin=o),
    ]


def l974_candy():
    return Model("l974-candy", candy(6.6, 7.0, 0, MINT, 15, 0) + candy(9.4, 8.6, 0, LILAC, -35, 1) + candy(7.6, 9.6, 0, BUTTER, 60, 2)
                 + candy(8.0, 7.9, 1.25, hx("ffc8dc"), -10, 3))


def bag_side(main):
    def fn(w, h, rng):
        img = stripes_v(w, h, hx("fbf2f4"), hx("f7a8c4"), 2, rng, grad=0.15, edge=0.9, noise=0.03)
        if main and w >= 6:
            heart(img, w // 2, h // 2 - 1, hx("e8487c"), big=w >= 8)
        band(img, 0, 1, shade(hx("fbf2f4"), 0.92), rng)
        grime(img, rng, max(1, w * h // 30), 0.92)
        return img
    return fn


def marshmallow_tex(w, h, rng):
    img = fill(w, h, hx("fbf4f0"), rng, grad=0.2, noise=0.03, edge=0.9)
    speckle(img, rng, [hx("ffffff"), hx("f4d8d8")], max(1, w * h // 5))   # the greasy sheen
    return img


def l974_marshmallow():
    inside = top(hx("7a5a64"), edge=0.7)
    els = [
        B("Bag", 6.0, 0, 6.8, 10.0, 4.4, 9.2, {"north": bag_side(True), "south": bag_side(True), "east": bag_side(False), "west": bag_side(False),
                                               "up": inside, "down": top(hx("e8d8dc"))}),
        B("Fold", 5.9, 4.0, 6.7, 10.1, 4.4, 9.3, {"side": surf(hx("f2d0dc"), edge=0.85)}),
    ]
    for i, (x, z, yy) in enumerate(((7.0, 7.6, 3.9), (8.6, 7.4, 4.1), (7.8, 8.6, 4.3), (9.0, 8.6, 3.8))):
        els.append(B(f"Mallow{i}", x - 0.7, yy, z - 0.65, x + 0.7, yy + 1.2, z + 0.65, {"all": marshmallow_tex}, rot=("y", i * 25)))
    els.append(B("Loose", 10.6, 0, 9.4, 12.0, 1.3, 10.7, {"all": marshmallow_tex}, rot=("y", 20)))
    return Model("l974-marshmallow", els)


def carton_front(w, h, rng):
    img = fill(w, h, PINK, rng, grad=0.15, noise=0.03, edge=0.88)
    rect(img, 0, h - 4, w, h - 1, hx("fff4f6"), rng)                  # the white label
    cx, cy = w / 2, h / 2 - 1.5
    disc(img, cx, cy + 0.3, 1.6, hx("e8304c"), rim=hx("a01830"))      # a strawberry
    put(img, int(cx) - 1, int(cy) - 1, hx("4ec23a"))
    put(img, int(cx), int(cy) - 2, hx("4ec23a"))
    put(img, int(cx) + 1, int(cy) - 1, hx("4ec23a"))
    put(img, int(cx), int(cy) + 1, hx("ffe08a"))
    print_lines(img, 1, w - 1, [h - 3], hx("e86a90"), rng)
    return img


def carton_side(w, h, rng):
    img = fill(w, h, PINK, rng, grad=0.15, noise=0.03, edge=0.88)
    heart(img, w // 2, 1, hx("ffffff"))
    print_lines(img, 1, w - 1, range(4, h - 1, 2), hx("e86a90"), rng)
    return img


def l974_strawberrymilk():
    roof = surf(hx("fbc0d4"), grad=0, edge=0.88)
    return Model("l974-strawberrymilk", [
        B("Carton", 6.5, 0, 6.5, 9.5, 4.4, 9.5, {"north": carton_front, "south": carton_front, "east": carton_side, "west": carton_side,
                                                 "up": None, "down": top(hx("e090ac"))}),
        B("GableLow", 6.55, 4.4, 6.95, 9.45, 5.0, 9.05, {"east": surf(PINK), "west": surf(PINK)}),
        B("GableHigh", 6.55, 5.0, 7.45, 9.45, 5.5, 8.55, {"east": surf(PINK), "west": surf(PINK)}),
        B("RoofN", 6.45, 4.98, 6.3, 9.55, 5.18, 8.35, {"all": roof}, rot=("x", -40), origin=(8, 5.08, 7.325)),
        B("RoofS", 6.45, 4.98, 7.65, 9.55, 5.18, 9.7, {"all": roof}, rot=("x", 40), origin=(8, 5.08, 8.675)),
        B("Fin", 6.4, 5.6, 7.85, 9.6, 6.2, 8.15, {"all": lambda w, h, rng: (lambda img: (print_lines(img, 0, w, [h // 2], hx("e86a90"), rng), img)[1])(
            fill(w, h, hx("fff0f4"), rng, edge=0.85))}),
    ])


def plate_rim(w, h, rng):
    img = fill(w, h, PINK, rng, light="flat", noise=0.04, edge=1)
    for y in range(h):
        for x in range(w):
            if (x + 2 * y) % 6 == 0:                               # little red dots round the rim
                img.putpixel((x, y), hx("e8487c"))
    return img


def plate():
    up = RimTop(top(hx("fbf8f4"), noise=0.02, edge=1), plate_rim, 2)
    return round_part("Plate", 8, 8, 8.0, 0, 0.45, surf(hx("f2e4ea"), edge=0.85), up=up, down=top(hx("e8dce0")), k=0.7)


def l974_meal(meal="pancakes"):
    y = 0.45
    els = plate()
    if meal == "pancakes":
        def edge(w, h, rng):
            img = fill(w, h, hx("f0d098"), rng, grad=0.1, edge=1)
            band(img, 0, 1, hx("b8702a"), rng)                      # the browned face
            for x in range(0, w, 3):
                put(img, x, h - 1, hx("c88a40"))
            return img

        def syrup_top(w, h, rng):
            img = fill(w, h, hx("d89a48"), rng, light="flat", noise=0.05, edge=0.9)
            for yy in range(1, h - 1):
                for xx in range(1, w - 1):
                    if math.hypot(xx - w / 2 + 0.5, yy - h / 2 + 0.5) < min(w, h) / 2 - 0.5:
                        img.putpixel((xx, yy), shade(hx("a0581c"), 1 + rng.uniform(-0.05, 0.08)))
            put(img, w // 2 - 1, h // 2 - 1, hx("e8a860"))
            return img
        for i, (d, dx) in enumerate(((5.2, 0.0), (5.0, 0.25), (5.1, -0.2), (4.9, 0.1))):
            els += round_part(f"Cake{i}", 8 + dx, 8, d, y + i * 0.6, y + i * 0.6 + 0.6, edge, up=syrup_top if i == 3 else None, k=0.68)
        els.append(B("Butter", 7.4, y + 2.4, 7.4, 8.6, y + 2.85, 8.6, {"all": surf(hx("fbe89a"), edge=0.85)}, rot=("y", 20)))
        els.append(B("Drip", 10.5, y + 1.0, 7.6, 10.75, y + 2.4, 8.2, {"all": surf(hx("a0581c"))}))
    elif meal == "soup":
        bowl_side = lambda w, h, rng: (lambda img: (band(img, 1, 2, PINK, rng), img)[1])(fill(w, h, hx("fbf8f4"), rng, grad=0.2, edge=0.88))

        def broth(w, h, rng):
            img = fill(w, h, hx("f0c060"), rng, light="flat", noise=0.05, edge=1)
            speckle(img, rng, [hx("f8e0a0")], max(1, w * h // 4), area=(1, 1, w - 1, h - 1))       # noodles
            speckle(img, rng, [hx("f08030")], max(1, w * h // 14), area=(1, 1, w - 1, h - 1))      # carrot
            speckle(img, rng, [hx("8cc860")], max(1, w * h // 16), area=(1, 1, w - 1, h - 1))      # celery
            speckle(img, rng, [hx("f4ead8")], max(1, w * h // 12), area=(1, 1, w - 1, h - 1))      # chicken
            for xx in range(w):
                put(img, xx, 0, hx("fbf8f4"))
                put(img, xx, h - 1, hx("fbf8f4"))
            for yy in range(h):
                put(img, 0, yy, hx("fbf8f4"))
                put(img, w - 1, yy, hx("fbf8f4"))
            return img
        els += round_part("BowlFoot", 8, 8, 3.2, y, y + 0.5, bowl_side)
        els += round_part("Bowl", 8, 8, 5.4, y + 0.5, y + 2.4, bowl_side, up=broth, k=0.68)
        steel = metal(hx("c8ccd4"))
        els.append(B("Spoon", 9.6, y + 2.3, 7.7, 13.2, y + 2.5, 8.1, {"all": steel}, rot=("y", -25), origin=(9.6, y + 2.4, 7.9)))
        els.append(B("SpoonBowl", 8.6, y + 2.25, 7.4, 9.8, y + 2.45, 8.4, {"all": steel}, rot=("y", -25), origin=(9.6, y + 2.4, 7.9)))
    else:  # macaroni
        def mac(w, h, rng):
            img = fill(w, h, hx("f2a81d"), rng, grad=0.15, noise=0.06, edge=0.9)
            for yy in range(h):
                for xx in range(w):
                    if (xx * 2 + yy + rng.randrange(2)) % 4 == 0:
                        img.putpixel((xx, yy), shade(hx("c87810"), 1 + rng.uniform(-0.08, 0.08)))   # the elbows' shadows
            speckle(img, rng, [hx("ffd060")], max(1, w * h // 5))
            return img
        els += round_part("Heap", 8, 8, 5.6, y, y + 0.9, mac, up=mac, k=0.7)
        els += round_part("Mound", 7.8, 8.2, 4.0, y + 0.9, y + 1.6, mac, up=mac, k=0.7)
        for i, (x, z, yy, r) in enumerate(((7.0, 7.4, 1.5, 20), (8.8, 7.8, 1.5, -30), (8.0, 9.0, 1.6, 55), (7.6, 8.2, 2.0, 10),
                                           (11.0, 9.6, 0.45, 40), (5.2, 6.6, 0.45, -20))):
            els.append(B(f"Elbow{i}", x - 0.5, y + yy - 0.45 if yy > 0.5 else yy, z - 0.35, x + 0.5, (y + yy - 0.45 if yy > 0.5 else yy) + 0.6, z + 0.35,
                         {"all": mac}, rot=("y", r)))
    return Model("l974-meal-" + meal, els)


# ======================================================================== Level Fun: party food

SPONGE = hx("f2d080")


def cake_side(kind):
    def fn(w, h, rng):
        if kind == "velvet":
            sponge, layer, frost = hx("8e1426"), hx("f8f0e4"), hx("f8f0e4")
        else:
            sponge, layer, frost = SPONGE, hx("f06a9a"), hx("fbf6f0")
        img = fill(w, h, sponge, rng, grad=0.15, noise=0.06, edge=1)
        speckle(img, rng, [shade(sponge, 0.85)], max(1, w * h // 6))           # crumb
        band(img, 0, 1, frost, rng)                                              # frosting
        if h >= 6:
            band(img, h // 3, h // 3 + 1, layer, rng)
            band(img, 2 * h // 3, 2 * h // 3 + 1, layer if kind == "velvet" else hx("fbf6f0"), rng)
        return img
    return fn


def cake_top(kind):
    def fn(w, h, rng):
        img = fill(w, h, hx("fbf6f0") if kind != "velvet" else hx("f8f0e4"), rng, light="flat", noise=0.03, edge=0.92)
        if kind == "velvet":
            speckle(img, rng, [hx("8e1426"), hx("a8202e")], max(1, w * h // 8))   # red crumbs on the cream
        else:
            speckle(img, rng, [hx("ff4a8a"), hx("3ab0ff"), hx("ffd23c"), hx("6ad84a"), hx("b06aff")], max(1, w * h // 4))
        return img
    return fn


def cake_back(kind):
    def fn(w, h, rng):
        c = hx("fbf6f0") if kind != "velvet" else hx("f8f0e4")
        img = fill(w, h, c, rng, grad=0.15, noise=0.03, edge=0.9)
        for x in range(0, w, 3):                                                  # piped shells along the bottom
            put(img, x, h - 1, shade(c, 0.85))
            put(img, x + 1, h - 2, shade(c, 0.9))
        if kind != "velvet":
            speckle(img, rng, [hx("ff4a8a"), hx("3ab0ff"), hx("ffd23c")], max(1, w * h // 10))
        return img
    return fn


def fun_cakeslice(kind="birthday"):
    plate_c = (hx("3ab0ff"), hx("ff4a8a")) if kind == "birthday" else (hx("ffd23c"), hx("b06aff"))
    els = round_part("Plate", 8, 8, 7.6, 0, 0.3, surf(hx("f0eef0"), edge=0.9), up=paper_plate(*plate_c), down=top(hx("e0dce0")), k=0.7)
    els += wedge("Slice", 8, 4.8, 11.0, 4.6, 0.8, 0.3, 3.3, 4, {"side": cake_side(kind), "up": cake_top(kind), "down": None},
                 back=cake_back(kind))
    rosette = hx("ff8ab8") if kind == "birthday" else hx("f8f0e4")
    els += [
        B("RosetteW", 6.4, 3.3, 5.0, 7.4, 3.9, 6.0, {"all": surf(rosette, edge=0.82)}, rot=("y", 20)),
        B("RosetteE", 8.6, 3.3, 5.0, 9.6, 3.9, 6.0, {"all": surf(rosette, edge=0.82)}, rot=("y", -15)),
    ]
    if kind == "birthday":
        els += [
            B("Candle", 7.8, 3.3, 6.6, 8.2, 5.5, 7.0, {"side": lambda w, h, rng: (lambda img: ([band(img, y, y + 1, hx("3ab0ff")) for y in range(0, h, 2)], img)[1])(
                fill(w, h, hx("f8f4f0"), rng, edge=1)), "up": top(hx("f8f4f0"))}),
            B("Wick", 7.95, 5.5, 6.75, 8.05, 5.7, 6.85, {"all": surf(hx("3a3028"))}),
            B("Flame", 7.75, 5.7, 6.55, 8.25, 6.5, 7.05, {"all": lambda w, h, rng: (lambda img: (band(img, 0, 1, hx("fff4b0")), img)[1])(
                fill(w, h, hx("ffb82c"), rng, edge=1, grad=0.4))}, glow=200),
        ]
    else:
        els.append(B("Crumb", 10.4, 0.3, 9.4, 10.9, 0.7, 9.9, {"all": surf(hx("8e1426"))}))
    return Model("fun-cakeslice-" + kind, els)


def cookie_tex(top_face):
    def fn(w, h, rng):
        img = fill(w, h, hx("d39b52"), rng, light="flat" if top_face else "top", grad=0.25, noise=0.07, edge=0.8)
        speckle(img, rng, [hx("e8b870"), hx("f0c880")], max(1, w * h // 5))     # cracks catching the light
        speckle(img, rng, [hx("b07830")], max(1, w * h // 8))
        if top_face:
            speckle(img, rng, [hx("4a2a14"), hx("3a2010")], max(1, w * h // 12))  # flat chips
        return img
    return fn


def fun_cookie():
    els = round_part("Disc", 8, 8, 5.2, 0, 0.8, cookie_tex(False), up=cookie_tex(True), down=top(hx("b07830")), k=0.72)
    els += round_part("Dome", 8, 8, 3.6, 0.8, 1.05, cookie_tex(False), up=cookie_tex(True), k=0.72)
    chip = {"all": surf(hx("3e2412"), edge=0.8, noise=0.08)}
    for i, (x, z, yy) in enumerate(((6.8, 7.0, 0.7), (9.0, 7.4, 0.7), (7.6, 9.1, 0.7), (8.4, 8.0, 0.95), (9.6, 8.9, 0.55))):
        els.append(B(f"Chip{i}", x - 0.35, yy, z - 0.35, x + 0.35, yy + 0.4, z + 0.35, chip, rot=("y", i * 20)))
    return Model("fun-cookie", els)


def glass(liquid, level, empty=hx("dce8e4"), hl=True):
    """Bottle glass seen with what is in it: `liquid` up to `level` (0-1 of the face's height), the glass above it, a
    vertical highlight, a darker tide line."""
    def fn(w, h, rng):
        img = new(w, h)
        line = int(round(h * (1 - level)))
        for y in range(h):
            for x in range(w):
                if y < line:
                    c = shade(empty, 0.95 + 0.1 * rng.random())
                else:
                    t = (y - line) / max(1, h - line)
                    c = shade(liquid, (1.08 - 0.25 * t) * (1 + rng.uniform(-0.05, 0.05)))
                if x in (0, w - 1) and w > 2:
                    c = shade(c, 0.82)
                img.putpixel((x, y), c)
        if 0 < line < h:
            band(img, line, line + 1, shade(liquid, 1.25))
        if hl and w >= 3:
            for y in range(1, h - 1):
                put(img, 1, y, shade(get(img, 1, y), 1.25))
        return img
    return fn


GLASS = hx("e8eedc")


def fun_lucatears():
    gold = hx("f2b81c")
    cork = surf(hx("b08a5a"), noise=0.1, edge=0.85)
    return Model("fun-lucatears", [
        *round_part("Body", 8, 8, 3.6, 0, 3.0, glass(gold, 0.75, empty=GLASS), up=None, down=top(shade(gold, 0.8)), k=0.66),
        *round_part("Shoulder", 8, 8, 2.6, 3.0, 3.6, glass(gold, 0.0, empty=GLASS), up=top(GLASS), k=0.66),
        B("Neck", 7.4, 3.6, 7.4, 8.6, 4.8, 8.6, {"side": glass(gold, 0.0, empty=GLASS)}),
        B("Lip", 7.25, 4.8, 7.25, 8.75, 5.15, 8.75, {"all": surf(hx("e8f0ec"), edge=0.85)}),
        B("Cork", 7.5, 5.0, 7.5, 8.5, 6.0, 8.5, {"all": cork}),
        B("Ribbon", 7.35, 4.0, 7.35, 8.65, 4.35, 8.65, {"side": surf(hx("f0c030"), edge=0.8)}),
    ])


# ======================================================================== The End: Memory Juice

def l_end_memoryjuice():
    amber = hx("c07a28")

    def body(main):
        def fn(w, h, rng):
            img = glass(amber, 0.82, empty=hx("a8b4a0"))(w, h, rng)
            for _ in range(max(1, w * h // 10)):                     # the cloud in it
                x, y = rng.randrange(w), rng.randrange(int(h * 0.2), h)
                put(img, x, y, shade(hx("e0b070"), 1 + rng.uniform(-0.05, 0.05)))
            if main and w >= 6:                                       # where a label was scraped off
                rect(img, 2, h // 2 - 1, w - 1, h // 2 + 3, hx("d8c8a0"), rng, noise=0.08)
                speckle(img, rng, [hx("b8a478")], 3, area=(2, h // 2 - 1, w - 1, h // 2 + 3))
            band(img, h - 1, h, shade(amber, 0.6))
            return img
        return fn
    cork = lambda w, h, rng: (lambda img: (speckle(img, rng, [hx("8a6a40"), hx("c8a878")], max(1, w * h // 3)), img)[1])(
        fill(w, h, hx("a88a60"), rng, noise=0.06, edge=0.85))
    neck = glass(amber, 0.0, empty=hx("b4c0aa"))
    return Model("end-memoryjuice", [
        B("Body", 6, 0, 6.5, 10, 6, 9.5, {"north": body(True), "south": body(True), "east": body(False), "west": body(False),
                                          "up": None, "down": top(shade(amber, 0.7))}),
        B("Shoulder", 6.4, 6, 6.8, 9.6, 6.8, 9.2, {"side": neck, "up": top(hx("b4c0aa"), edge=0.85)}),
        B("Neck", 7.3, 6.8, 7.3, 8.7, 8.4, 8.7, {"side": neck}),
        B("Lip", 7.1, 8.4, 7.1, 8.9, 8.9, 8.9, {"side": neck, "up": top(hx("b4c0aa"), edge=0.8), "down": top(hx("8a9480"))}),
        B("Cork", 7.4, 8.5, 7.4, 8.6, 10.0, 8.6, {"all": cork}),
        B("Twine", 7.15, 7.4, 7.15, 8.85, 7.8, 8.85, {"side": lambda w, h, rng: stripes_v(w, h, hx("c8b080"), hx("a08858"), 1, rng, edge=1)}),
        B("TwineEnd", 8.85, 6.6, 8.0, 9.0, 7.6, 8.3, {"all": surf(hx("b89c6c"))}),
    ])


# ======================================================================== The items: which model, how big, how held

# code: (models, kind, real size in cm). models: a builder, or {variant state: builder} for shapeByType, or
# ("shared", builder, [states]) for one shape with a texture per state. kind: "upright" (stands: bottles, cans, cartons,
# buckets), "flat" (lies: plates, slices, trays). cm: the thing's largest real dimension, which sizes it in the world
# (small things a little over: candy, a cookie), or {state: cm} for a family of different sizes.
LOOKS = {
    "l188-cereal": (l188_cereal, "upright", 11),
    "l188-juicebox": (l188_juicebox, "upright", 15),
    "l974-candy": (l974_candy, "flat", 10),
    "l974-marshmallow": (l974_marshmallow, "upright", 15),
    "l974-strawberrymilk": (l974_strawberrymilk, "upright", 13),
    "l974-meal": ({m: (lambda m=m: l974_meal(m)) for m in ("pancakes", "soup", "macaroni")}, "flat", 24),
    "l3999-cottoncandy": (cottoncandy, "upright", 30),
    "l3999-popcorn": (popcorn, "upright", 20),
    "l3999-soda": (("shared", soda, ["cherry", "lime", "grape"]), "upright", 12),
    "l3999-traymeal": ({m: (lambda m=m: traymeal(m)) for m in ("burger", "pizza", "noodles", "taco", "icecream", "pretzel")}, "flat", 32),
    "fun-cakeslice-birthday": (lambda: fun_cakeslice("birthday"), "flat", 18),
    "fun-cakeslice-velvet": (lambda: fun_cakeslice("velvet"), "flat", 18),
    "fun-cookie": (fun_cookie, "flat", 11),
    "fun-lucatears": (fun_lucatears, "upright", 12),
    "l31-food": ({"pizza": lambda: l31_pizza("pizza"), "pepperoni": lambda: l31_pizza("pepperoni"), "wings": l31_wings,
                  "hotdog": l31_hotdog}, "flat", {"pizza": 22, "pepperoni": 22, "wings": 17, "hotdog": 30}),
    "end-memoryjuice": (l_end_memoryjuice, "upright", 18),
}


def _models(code):
    """[(state or None, Model)] for an item: one model, or one per variant state."""
    spec = LOOKS[code][0]
    if isinstance(spec, dict):
        return [(s, fn()) for s, fn in spec.items()]
    if isinstance(spec, tuple):
        return [(None, spec[1](spec[2][0]))]
    return [(None, spec())]


def _r(v):
    return round(v, 3)


def transforms(models, kind, cm):
    """The four transforms, the size set down on the floor and the height there (blocks), from the models' size (the
    largest of a variant family). fpHandTransform is obsolete in 1.22 (the first-person view draws the tp one); it is
    written the same so older readers agree."""
    sx = sy = sz = cy = 0.0
    for m in models:
        lo, hi = m.extent()
        sx, sy, sz = max(sx, hi[0] - lo[0]), max(sy, hi[1] - lo[1]), max(sz, hi[2] - lo[2])
        cy = max(cy, (lo[1] + hi[1]) / 2)
    e = max(sx, sy, sz)
    foot = max(sx, sz)
    if kind == "upright":
        # Seen from above at 22.6 degrees, turned 45 (the mod's bottles): the height and the diagonal of the foot
        proj = max(sy * 0.92 + foot * 0.55, foot * 1.35)
        gui = {"rotation": {"x": 157.4, "y": -45.3, "z": 0}, "origin": {"x": 0.5, "y": _r(cy / 16), "z": 0.5}, "scale": _r(24 / proj)}
        ground = {"rotation": {"x": 0, "y": -45, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": _r(1.05 * cm / e)}
    else:
        # Seen from above at 35 degrees, turned 45: a plate or a slice shows its top
        diag = (sx + sz) * 0.707
        proj = max(diag, diag * 0.57 + sy * 0.82)
        gui = {"rotation": {"x": 145, "y": -45.3, "z": 0}, "origin": {"x": 0.5, "y": _r(cy / 16), "z": 0.5}, "scale": _r(25 / proj)}
        ground = {"rotation": {"x": 0, "y": 0, "z": 0}, "origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": _r(1.05 * cm / e)}
    # In the hand: held as the pantry holds its bottles and bars, upright or flat in the palm, a little turned (the
    # breadfruit-style hold, stood on the hand's x, was drawn inside the fist or the arm when seen in the client)
    # (a plate or a tray at full size hung down to the shin: smaller and higher in the palm)
    # (and a sweet or a cookie, a hand's width or less, that high was drawn inside the fist: held as the candy bar)
    ts = 0.42 * cm / e
    tp = ({"translation": {"x": -0.85, "y": -0.5, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": _r(min(0.85, ts))}
          if kind == "upright" else
          {"translation": {"x": -0.8, "y": -0.45, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": _r(min(0.75, ts))}
          if cm <= 12 else
          {"translation": {"x": -0.8, "y": -0.3, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": _r(min(0.7, ts))})
    # Set down on the floor (four to a block): one and a half times life size, never wider than its quadrant
    store = min(0.24 * cm / e, 7.5 / foot)
    tf = {"guiTransform": gui, "fpHandTransform": json.loads(json.dumps(tp)), "tpHandTransform": tp, "groundTransform": ground}
    return tf, store, sy * store / 16


def dress(code, data):
    """Gives an item type written by a level's generator its model: the shape (or shapes by variant) and textures from
    here in place of the flat texture, the four transforms, and its size set down on the floor. Returns `data`; an
    item not in LOOKS is returned as it is."""
    if code not in LOOKS:
        return data
    spec, kind, cm = LOOKS[code]
    models = _models(code)
    for k in ("texture", "textureByType", "texturebytype", "textures", "texturesByType", "shape", "shapeByType", "shapebytype"):
        data.pop(k, None)
    if isinstance(spec, dict):
        data["shapeByType"] = {f"{code}-{s}": {"base": tex_path(m.name)} for s, m in models}
    else:
        data["shape"] = {"base": tex_path(models[0][1].name)}
        if isinstance(spec, tuple):
            data["texturesByType"] = {f"{code}-{s}": {"tex": {"base": tex_path(f"{models[0][1].name}-{s}")}} for s in spec[2]}
    sizes = cm if isinstance(cm, dict) else {s: cm for s, _ in models}
    tf, store, height = transforms([m for _, m in models], kind, max(sizes.values()))
    data.update(tf)
    if isinstance(spec, dict):
        # each variant its own transforms (a hot dog is twice a wing's length)
        for k in tf:
            data.pop(k, None)
            data[k + "ByType"] = {f"{code}-{s}": transforms([m], kind, sizes[s])[0][k] for s, m in models}
    gs = [b for b in data.get("behaviors", []) if b.get("name") == "GroundStorable"]
    if gs:
        data.setdefault("attributes", {})["groundStorageTransform"] = {"origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": _r(store)}
        props = gs[0].setdefault("properties", {})
        props["selectionBox"] = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": _r(max(0.125, min(1.0, height + 0.05))), "z2": 1}
    return data


def main():
    written = []
    for code, (spec, _, _) in LOOKS.items():
        if isinstance(spec, tuple):
            _, fn, states = spec
            model = fn(states[0])
            write_model(model, {s: fn(s) for s in states})
            written.append(model.name)
        else:
            for _, m in _models(code):
                write_model(m)
                written.append(m.name)
    print(f"treats: {len(written)} models:", ", ".join(written))


if __name__ == "__main__":
    main()
