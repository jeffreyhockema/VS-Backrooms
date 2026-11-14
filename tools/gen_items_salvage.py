"""The item pass (0.700): real models for the Lobby's salvage and tools, the most-handled items in the game. Each was
drawn flat (the game's extruded 32 x 32 sprite); each now has a shape built of boxes and its own hand-painted texture
at vanilla's density (32 px over 16 units, as vanilla's item textures), sized and held like the vanilla item it is
nearest to.

    python tools/gen_items_salvage.py            (all of them)
    python tools/gen_items_salvage.py rubble ... (only these)

Writes shapes/item/salvage/<code>.json and textures/item/salvage/model/<code>.png (the five seed packets: one texture
per crop), and gives each item type its shape, textures and transforms:
- the hand-written item types (itemtypes/salvage/*.json but carpetsquare and rubble): their `shape`, `guiTransform`,
  `tpHandTransform`, `groundTransform` lines and `attributes.groundStorageTransform` are rewritten in place, comments
  and everything else kept;
- the generated ones go through `look(code, data)`, which tools/gen_breakdown.py (carpetsquare, rubble),
  tools/gen_loop.py (prybar, seedpacket) and tools/gen_materials.py (clumpsinew, mothjelly, mothquill, spidersilk) call
  when they write the type; this script also patches their current files the same way, so it need not re-run them.
The flat sprites (textures/item/salvage/*.png and the rest) stay: the glass spear's model uses the shard's, and the
retired pleather is still drawn flat.

Transforms (1.22): the inventory icon is drawn from guiTransform (InventoryItemRenderer: slot centre + translation +
25.6 px x scale x Rx Ry Rz (p - origin), y down); the held item, in first and third person alike, from tpHandTransform
on the hand's attachment point (EntityShapeRenderer.RenderItem; fpHandTransform is no longer read, so none is written);
the dropped item from groundTransform (EntityItemRenderer: translation + 0.2 x scale x Ry Rz Rx (p - origin), on the
entity's feet); a stack set down from attributes.groundStorageTransform (applied to the mesh, then the layout's offset).
Here the icon is fitted to the slot (`gui`), the item laid on the floor at a life size given in blocks (`ground`), a
set-down stack fitted to its layout's cell resting on the floor (`storage`), and the held item placed and sized where
the nearest vanilla item is held (`held`: the same rotation, its centre where the vanilla item's centre is).
"""
import hashlib
import json
import math
import os
import random
import re
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEXDIR = "item/salvage/model"
SHAPEDIR = "item/salvage"
GAME = os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory"))
NL = "\n"
W = 32          # texture pixels
PXU = 0.5       # one texture pixel in shape units (32 px over 16 units, as vanilla)


# ======================= Colour and texture kit =======================

def clamp(v):
    return max(0, min(255, int(round(v))))


def shade(c, k):
    return tuple(clamp(v * k) for v in c[:3]) + ((c[3],) if len(c) > 3 else (255,))


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def rgba(c):
    return tuple(c[:3]) + (255,)


class Tex:
    """A 32 x 32 texture painted zone by zone. A zone is a rectangle in pixels; faces sample it in shape units
    (two pixels a unit), so `uv(zone)` gives its rectangle in UV units."""

    def __init__(self, seed):
        self.img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
        self.px = self.img.load()
        self.rnd = random.Random(seed)
        self.zones = {}

    def zone(self, name, x, y, w, h):
        assert 0 <= x and 0 <= y and x + w <= W and y + h <= W, (name, x, y, w, h)
        self.zones[name] = (x, y, w, h)
        return name

    def paint(self, name, fn):
        """fn(i, j, w, h, rnd) -> colour, for every pixel of the zone (i across, j down)."""
        x, y, w, h = self.zones[name]
        for j in range(h):
            for i in range(w):
                self.px[x + i, y + j] = rgba(fn(i, j, w, h, self.rnd))

    def put(self, name, i, j, c):
        x, y, w, h = self.zones[name]
        if 0 <= i < w and 0 <= j < h:
            self.px[x + i, y + j] = rgba(c)

    def get(self, name, i, j):
        x, y, w, h = self.zones[name]
        return self.px[x + min(w - 1, max(0, i)), y + min(h - 1, max(0, j))]

    def grain(self, name, amount=0.06, seed=0):
        """A fine value grain over the zone, so no face is one flat colour."""
        x, y, w, h = self.zones[name]
        r = random.Random(seed)
        for j in range(h):
            for i in range(w):
                c = self.px[x + i, y + j]
                self.px[x + i, y + j] = shade(c, 1 + r.uniform(-amount, amount))


def noise2(seed, w, h, cell=4):
    """Smooth value noise on a w x h grid (bilinear between random lattice values), -1..1."""
    r = random.Random(seed)
    gw, gh = w // cell + 2, h // cell + 2
    g = [[r.uniform(-1, 1) for _ in range(gw)] for _ in range(gh)]

    def at(i, j):
        fx, fy = i / cell, j / cell
        x0, y0 = int(fx), int(fy)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = g[y0][x0] * (1 - tx) + g[y0][x0 + 1] * tx
        b = g[y0 + 1][x0] * (1 - tx) + g[y0 + 1][x0 + 1] * tx
        return a * (1 - ty) + b * ty
    return at


def block_texture(rel):
    """One of the mod's block textures, to cut the Lobby's own carpet and paper from."""
    return Image.open(os.path.join(ASSETS, "textures", rel + ".png")).convert("RGBA")


# ======================= Model kit =======================

DIRS = ("north", "east", "south", "west", "up", "down")
ROLES = {"north": ("front", "long", "side"), "south": ("back", "long", "side"), "east": ("right", "ends", "side"),
         "west": ("left", "ends", "side"), "up": ("top",), "down": ("bottom",)}


def face_size(face, d):
    w, h, l = d
    return {"north": (w, h), "south": (w, h), "east": (l, h), "west": (l, h), "up": (w, l), "down": (w, l)}[face]


class Model:
    """Elements for one shape, with one texture key. `zones` on a box: a zone name for every face, or a dict by face
    (north, east, south, west, up, down), by role (front, back, left, right, top, bottom; long = north and south,
    ends = east and west, side = all four) or "all"; a value is a zone name, (zone, du, dv) to start that many units
    into the zone, an explicit [u0, v0, u1, v1], or None to leave the face out. A face samples its own size (in
    units) out of its zone, from a start that varies with the element's name unless given, so a material keeps its
    density on parts of any size and neighbouring parts do not repeat each other."""

    def __init__(self, code, tex, key="tex"):
        self.code = code
        self.tex = tex
        self.key = key
        self.els = []

    def _uv(self, spec, fw, fh, salt):
        if isinstance(spec, list):
            return spec
        du = dv = None
        if isinstance(spec, tuple):
            spec, du, dv = spec
        x, y, w, h = self.tex.zones[spec]
        zw, zh = w * PXU, h * PXU
        fw, fh = min(fw, zw), min(fh, zh)
        hsh = int(hashlib.md5(salt.encode()).hexdigest()[:8], 16)
        if du is None:
            du = ((hsh & 0xFFFF) % max(1, int((zw - fw) / PXU) + 1)) * PXU
        if dv is None:
            dv = (((hsh >> 16) & 0xFFFF) % max(1, int((zh - fh) / PXU) + 1)) * PXU
        du, dv = min(du, zw - fw), min(dv, zh - fh)
        u0, v0 = x * PXU + du, y * PXU + dv
        return [round(u0, 4), round(v0, 4), round(u0 + fw, 4), round(v0 + fh, 4)]

    def box(self, name, frm, to, zones, rot=None, origin=None, parent=None):
        (x1, y1, z1), (x2, y2, z2) = frm, to
        assert x2 > x1 and y2 > y1 and z2 > z1, (self.code, name, frm, to)
        d = (x2 - x1, y2 - y1, z2 - z1)
        if not isinstance(zones, dict):
            zones = {"all": zones}
        faces = {}
        for f in DIRS:
            spec = zones.get(f, "_")
            if spec == "_":
                for role in ROLES[f]:
                    if role in zones:
                        spec = zones[role]
                        break
            if spec == "_":
                spec = zones.get("all")
            if spec is None:
                continue
            fw, fh = face_size(f, d)
            faces[f] = {"texture": "#" + self.key, "uv": self._uv(spec, fw, fh, self.code + name + f)}
        el = {"name": name, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to], "faces": faces}
        if rot:
            el["rotationOrigin"] = [round(v, 4) for v in (origin or ((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2))]
            for axis, v in zip("XYZ", rot):
                if v:
                    el["rotation" + axis] = v
        if parent is None:
            self.els.append(el)
        else:
            parent.setdefault("children", []).append(el)
        return el

    def chain(self, name, start, segs, width, thick, zones, axis_z=True, along=None):
        """A strip bent along its length: segs = [(length, degrees), ...], each segment turned about Z (curling up
        for positive degrees) from the end of the one before, pivoting on its bottom edge. `start` = (x, y, z) of the
        first segment's lower near corner; width runs along z. `along(k, u)` may give each segment's zones from the
        distance u (units) already laid, so a pattern runs on across the bends. Returns the elements."""
        out = []
        parent = None
        u = 0.0
        for k, (length, deg) in enumerate(segs):
            z = along(k, u) if along else zones
            if parent is None:
                x, y, zz = start
                el = self.box(f"{name}{k}", (x, y, zz), (x + length, y + thick, zz + width), z,
                              rot=(0, 0, deg) if deg else None, origin=(x, y, zz))
            else:
                pl = parent["to"][0] - parent["from"][0]
                el = self.box(f"{name}{k}", (pl, 0, 0), (pl + length, thick, width), z,
                              rot=(0, 0, deg) if deg else None, origin=(pl, 0, 0), parent=parent)
            out.append(el)
            parent = el
            u += length
        return out

    def shape(self, textures):
        return {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": self.els}


# ----- geometry of a shape, in block units, for fitting the transforms -----

def rot_zyx(p, rx, ry, rz):
    """A point turned as the game turns an element (and as Rx.Ry.Rz turns it): about Z, then Y, then X."""
    x, y, z = p
    if rz:
        a = math.radians(rz)
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
    if ry:
        a = math.radians(ry)
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
    if rx:
        a = math.radians(rx)
        y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
    return (x, y, z)


def points(els):
    """Every corner of every element (children placed on their parents), in block units."""
    out = []

    def rec(els, xf):
        for e in els:
            f, t = e["from"], e["to"]
            o = e.get("rotationOrigin", [0, 0, 0])
            r = (e.get("rotationX", 0), e.get("rotationY", 0), e.get("rotationZ", 0))

            def mine(p, o=o, r=r, xf=xf):
                q = rot_zyx((p[0] - o[0], p[1] - o[1], p[2] - o[2]), *r)
                return xf((q[0] + o[0], q[1] + o[1], q[2] + o[2]))
            for cx in (f[0], t[0]):
                for cy in (f[1], t[1]):
                    for cz in (f[2], t[2]):
                        out.append(mine((cx, cy, cz)))
            if e.get("children"):
                rec(e["children"], lambda p, e=e, mine=mine: mine((p[0] + e["from"][0], p[1] + e["from"][1], p[2] + e["from"][2])))
    rec(els, lambda p: p)
    return [(p[0] / 16, p[1] / 16, p[2] / 16) for p in out]


def bbox(pts):
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi


def vec(x, y, z):
    return {"x": round(x, 3), "y": round(y, 3), "z": round(z, 3)}


def gui(els, rot, fill=40.0):
    """An inventory icon: the shape turned by rot, centred in the 48 px slot and `fill` px across at most."""
    pts = points(els)
    lo, hi = bbox(pts)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    q = [rot_zyx((p[0] - c[0], p[1] - c[1], p[2] - c[2]), *rot) for p in pts]
    w = max(p[0] for p in q) - min(p[0] for p in q)
    h = max(p[1] for p in q) - min(p[1] for p in q)
    scale = fill / (25.6 * max(w, h))
    mx = (max(p[0] for p in q) + min(p[0] for p in q)) / 2 * 25.6 * scale
    my = (max(p[1] for p in q) + min(p[1] for p in q)) / 2 * 25.6 * scale
    # the renderer puts an item 3 px left and 1 px up of the slot centre; make up for it with the centring
    return {"translation": vec(3 - mx, 1 - my, 0), "rotation": vec(*rot), "origin": vec(*c), "scale": round(scale, 3)}


def ground(els, size, rot=(0, 0, 0)):
    """A dropped item: turned by rot (as EntityItemRenderer turns it: X, then Z, then Y), `size` blocks across at
    most, its lowest point on the floor."""
    pts = points(els)
    lo, hi = bbox(pts)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]

    def tf(p):
        x, y, z = p[0] - c[0], p[1] - c[1], p[2] - c[2]
        a = math.radians(rot[0])
        y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
        a = math.radians(rot[2])
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        a = math.radians(rot[1])
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
        return (x, y, z)
    q = [tf(p) for p in pts]
    ext = max(max(p[0] for p in q) - min(p[0] for p in q), max(p[2] for p in q) - min(p[2] for p in q))
    scale = size / (0.2 * ext)
    lift = -min(p[1] for p in q) * 0.2 * scale
    return {"translation": vec(0, lift, 0), "rotation": vec(*rot), "origin": vec(*c), "scale": round(scale, 3)}


def storage(els, layout, rot=(0, 0, 0), most=1.0):
    """A stack set down (groundStorageTransform, as a ModelTransform on the mesh: turned Z, Y, X about the origin,
    then the layout's offset): resting on the floor, centred in its cell, no bigger than the cell (a half is 0.5 x 1
    blocks, a quadrant 0.5 x 0.5; Messy12 scatters twelve over the block, each its own size) nor `most` times its
    own size."""
    pts = points(els)
    lo, hi = bbox(pts)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    q = [rot_zyx((p[0] - c[0], p[1] - c[1], p[2] - c[2]), *rot) for p in pts]
    qlo, qhi = bbox(q)
    room = {"Halves": (0.44, 0.92), "Quadrants": (0.44, 0.44), "Messy12": (0.62, 0.62)}[layout]
    scale = min(most, room[0] / (qhi[0] - qlo[0]), room[1] / (qhi[2] - qlo[2]))
    # ModelTransform: p' = T + O + S R (p - O), with O the shape's centre: the centre goes to T + O
    cx, cz = (qlo[0] + qhi[0]) / 2 * scale, (qlo[2] + qhi[2]) / 2 * scale
    ty = -c[1] - qlo[1] * scale + 0.002
    return {"translation": vec(0.5 - c[0] - cx, ty, 0.5 - c[2] - cz), "rotation": vec(*rot), "origin": vec(*c),
            "scale": round(scale, 3)}


# The vanilla items the salvage is held like: their tpHandTransform and the centre of their shape (block units),
# measured from the game's assets (survival/itemtypes and shapes/item); a held item takes the rotation and origin of
# its model and puts its own centre where the model's centre is held.
HELD = {
    "flaxfibers": ({"translation": (-0.66, 0, -0.63), "rotation": (70, 5, -5), "origin": (0.5, 0, 0.5), "scale": 0.8}, (0.499, 0.044, 0.527), 0.645),
    "flint": ({"translation": (-1, -0.9, -1.35), "rotation": (-80, 0, 0), "origin": (0.5, 0.5, 0.5), "scale": 0.56}, (0.594, 0.047, 0.484), 0.562),
    "leather": ({"translation": (-1, -1.2, -1.45), "rotation": (92, -180, 180), "origin": (0.5, 0.5, 0.5), "scale": 0.49}, (0.517, 0.031, 0.517), 0.87),
    "feather": ({"translation": (-0.6, 0, -0.5), "rotation": (0, -2, 18), "origin": (0.5, 0.5, 0.5), "scale": 0.9}, (0.49, 0.011, 0.5), 0.604),
    "stone": ({"translation": (-0.7, -0.12, -0.7), "rotation": (-44, 7, -9), "origin": (0.5, 0.1, 0.5), "scale": 0.7}, (0.5, 0.062, 0.5), 0.312),
    "stick": ({"translation": (-1.22, 0.06, -0.89), "rotation": (-6, 30, 18), "origin": (0.5, 0, 0.5), "scale": 0.59}, (0.505, 0.044, 0.487), 0.751),
    "rope": ({"translation": (-0.7, -0.28, -0.8), "rotation": (-78, 7, 8), "origin": (0.5, 0.125, 0.5), "scale": 0.7}, (0.5, 0.078, 0.578), 0.719),
    "fat": ({"translation": (-1.1, -1.2, -1.5), "rotation": (90, -92, -180), "origin": (0.5, 0.5, 0.5), "scale": 0.43}, (0.484, 0.062, 0.469), 0.344),
    "nails": ({"translation": (-0.7, -0.2, -0.6), "rotation": (94, 0, 0), "origin": (0.5, 0.1, 0.5), "scale": 0.75}, (0.573, 0.051, 0.563), 0.469),
}


def held(els, like, size=None):
    """The held item: rotation and origin of the vanilla item `like`, its centre where that item's centre is held
    (EntityShapeRenderer: q = O + S (T + R (p - O)) on the hand's attachment point), `size` times as big in the hand
    as the vanilla item (default: the same size in the hand as the vanilla item, measured on the longest side)."""
    tf, vc, vext = HELD[like]
    pts = points(els)
    lo, hi = bbox(pts)
    c = [(lo[i] + hi[i]) / 2 for i in range(3)]
    ext = max(hi[i] - lo[i] for i in range(3))
    O, T, R, S = tf["origin"], tf["translation"], tf["rotation"], tf["scale"]
    R1 = (R[0], R[1] - 180, R[2])  # the right hand's attachment point is turned 180 about Y
    rv = rot_zyx(tuple(vc[i] - O[i] for i in range(3)), *R1)
    q = [O[i] + S * (T[i] + rv[i]) for i in range(3)]
    s = S * (size or 1.0) * vext / ext
    rm = rot_zyx(tuple(c[i] - O[i] for i in range(3)), *R1)
    t = [(q[i] - O[i]) / s - rm[i] for i in range(3)]
    return {"translation": vec(*t), "rotation": vec(*R), "origin": vec(*O), "scale": round(s, 3)}


# ======================= The items =======================

LOOKS = {}      # code -> {"shape": base, "textures": {...} or None, transforms..., "storage": {...}}
BUILDERS = {}


def item(code):
    def reg(fn):
        BUILDERS[code] = fn
        return fn
    return reg


def finish(code, m, transforms, textures=None, shape_name=None):
    """Writes the shape and remembers how the item type shows it."""
    name = shape_name or code
    tex_paths = {m.key: f"backrooms:{TEXDIR}/{code}"} if textures is None else textures
    write_shape(name, m.shape(tex_paths))
    LOOKS[code] = dict(transforms, shape=f"{SHAPEDIR}/{name}")


def write_shape(name, data):
    path = os.path.join(ASSETS, "shapes", SHAPEDIR, name + ".json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(json.dumps(data, indent="\t") + NL)


def save_tex(t, name):
    path = os.path.join(ASSETS, "textures", TEXDIR, name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    t.img.save(path)


# ---------------- Carpet fibres ----------------

CARPET = (163, 146, 107)
CARPET_DAMP = (122, 106, 80)


@item("carpetfibre")
def carpetfibre():
    """A tuft of the Lobby's carpet pile, cut away with a blade: a twisted bundle in the middle, fraying out at both
    ends into loose threads, two stray crimped threads lying across it. The damp beige of the carpet, tips paler,
    roots darker with the backing's dirt."""
    t = Tex(1101)
    # strand rows: 2 px each, a thread's length running across the texture, paler at one end
    tones = [(176, 158, 116), (160, 143, 104), (184, 168, 128), (146, 130, 94), (170, 152, 110), (154, 136, 98)]
    for k, tone in enumerate(tones):
        t.zone(f"s{k}", 0, k * 2, 32, 2)
        t.paint(f"s{k}", lambda i, j, w, h, r, tone=tone: shade(tone, (0.86 + 0.22 * i / w) * (0.92 if (i + 2 * j + k) % 5 == 0 else 1.0)
                                                                 * (1.06 if j == 0 else 0.94) * r.uniform(0.96, 1.04)))
    # the twisted bundle: diagonal plies, darker in the grooves between them
    t.zone("bundle", 0, 12, 16, 8)
    t.paint("bundle", lambda i, j, w, h, r: shade(CARPET, (0.78 if (i + j) % 4 == 0 else 1.0 + 0.08 * ((i + j) % 4 == 2))
                                                  * r.uniform(0.95, 1.05)))
    t.zone("bundleend", 16, 12, 4, 4)
    t.paint("bundleend", lambda i, j, w, h, r: shade(CARPET, 0.72 + 0.12 * ((i * 3 + j * 5) % 4 == 0) + r.uniform(-0.04, 0.04)))
    save_tex(t, "carpetfibre")

    m = Model("carpetfibre", t)
    m.box("Bundle", (6, 0.25, 7.25), (10, 1.25, 8.75), {"all": "bundle", "ends": "bundleend"})
    m.box("BundleWrap", (7.5, 0.125, 7.125), (8.5, 1.375, 8.875), {"all": ("bundle", 2, 1), "ends": "bundleend"})
    # the frayed ends: threads splayed from each end of the bundle
    fray = [(-1, 6.25, 0.0, 3.5, 24, 0), (-1, 6.25, 0.5, 4.0, 9, 1), (-1, 6.25, 0.25, 3.0, -8, 2), (-1, 6.25, 0.75, 2.5, -26, 3),
            (1, 9.75, 0.0, 4.0, -20, 4), (1, 9.75, 0.5, 3.5, -6, 5), (1, 9.75, 0.25, 4.5, 7, 0), (1, 9.75, 0.75, 3.0, 22, 1),
            (1, 9.75, 0.0, 2.5, 36, 2)]
    for n, (side, x0, y0, length, deg, tone) in enumerate(fray):
        z0 = 7.6 + (n % 3) * 0.25
        x1, x2 = (x0, x0 + length) if side > 0 else (x0 - length, x0)
        m.box(f"Fray{n}", (x1, y0, z0), (x2, y0 + 0.5, z0 + 0.75), f"s{tone}", rot=(0, deg, 0), origin=(x0, y0, z0 + 0.375))
    # two stray threads, each crimped once
    for n, (x0, z0, l1, l2, d1, d2, tone) in enumerate([(4.5, 6.0, 3.5, 3.0, -12, 18, 3), (7.0, 10.0, 3.0, 3.5, 10, -16, 4)]):
        m.box(f"Stray{n}a", (x0, 0, z0), (x0 + l1, 0.5, z0 + 0.5), f"s{tone}", rot=(0, d1, 0), origin=(x0 + l1, 0, z0 + 0.25))
        m.box(f"Stray{n}b", (x0 + l1, 0, z0), (x0 + l1 + l2, 0.5, z0 + 0.5), f"s{tone}", rot=(0, d2, 0), origin=(x0 + l1, 0, z0 + 0.25))
    finish("carpetfibre", m, {
        "guiTransform": gui(m.els, (150, -35, 0)),
        "tpHandTransform": held(m.els, "flaxfibers", 0.9),
        "groundTransform": ground(m.els, 0.42),
        "storage": storage(m.els, "Messy12", most=0.85),
    })


# ---------------- Carpet square ----------------

@item("carpetsquare")
def carpetsquare():
    """A square of the Lobby's carpet lifted whole: a thick cut tile, the pile cut from the floor's own carpet (one
    corner gone dark with damp), its grey-brown backing under it, one corner curling up off the floor and a few tufts
    of pile frayed out along the cut edges."""
    t = Tex(1102)
    carpet = block_texture("block/carpet-normal")
    soaked = block_texture("block/carpet-soaked")
    damp = noise2(1102, 24, 24, 6)
    t.zone("pile", 0, 0, 24, 24)
    t.paint("pile", lambda i, j, w, h, r: mix(carpet.getpixel((i + 3, j + 5)), soaked.getpixel((i + 3, j + 5)),
                                              max(0.0, min(1.0, (i + j) / 30 - 0.55 + 0.35 * damp(i, j)))))
    for i in range(24):  # the cut edge of the pile, a pixel in, a little darker
        for j in (0, 23):
            t.put("pile", i, j, shade(t.get("pile", i, j), 0.86))
            t.put("pile", j, i, shade(t.get("pile", j, i), 0.86))
    t.zone("cut", 0, 24, 24, 2)  # the cut edge: pile tips over the tuft roots
    t.paint("cut", lambda i, j, w, h, r: shade(CARPET, (1.02 if j == 0 else 0.74) * (0.84 if i % 3 == 0 else 1.0) * r.uniform(0.94, 1.05)))
    t.zone("bedge", 0, 26, 24, 1)  # the backing's edge
    t.paint("bedge", lambda i, j, w, h, r: shade((104, 92, 74), r.uniform(0.9, 1.08)))
    t.zone("back", 24, 0, 8, 16)  # the backing: a woven jute grid in grey-brown latex
    t.paint("back", lambda i, j, w, h, r: shade((120, 106, 84), (0.82 if i % 2 == 0 or j % 3 == 0 else 1.0) * r.uniform(0.94, 1.05)))
    t.zone("tuft", 24, 16, 8, 4)
    t.paint("tuft", lambda i, j, w, h, r: shade(CARPET, (1.1 - 0.1 * j) * (0.86 if (i + j) % 3 == 0 else 1.0) * r.uniform(0.95, 1.05)))
    save_tex(t, "carpetsquare")

    m = Model("carpetsquare", t)

    def top(x, z):
        return ("pile", x - 2, z - 2)
    m.box("PileA", (2, 0.5, 2), (14, 1.5, 10), {"top": top(2, 2), "side": "cut", "bottom": None})
    m.box("PileB", (2, 0.5, 10), (10, 1.5, 14), {"top": top(2, 10), "side": "cut", "bottom": None})
    m.box("BackA", (2, 0, 2), (14, 0.5, 10), {"side": "bedge", "bottom": "back", "top": None})
    m.box("BackB", (2, 0, 10), (10, 0.5, 14), {"side": "bedge", "bottom": "back", "top": None})
    # the corner curling up off the floor, hinged on its edge
    m.box("FlapPile", (10, 0.5, 10), (14, 1.5, 14), {"top": top(10, 10), "side": "cut", "bottom": None}, rot=(-20, 0, 0), origin=(12, 0, 10))
    m.box("FlapBack", (10, 0, 10), (14, 0.5, 14), {"side": "bedge", "bottom": "back", "top": None}, rot=(-20, 0, 0), origin=(12, 0, 10))
    for n, (a, b) in enumerate([((1.5, 0.5, 4.5), (2, 1.25, 5.5)), ((6.5, 0.5, 1.5), (7.5, 1.25, 2)), ((14, 0.5, 6), (14.5, 1.25, 7)),
                                ((3, 0.5, 14), (4, 1.25, 14.5)), ((1.5, 0.5, 11), (2, 1.0, 12))]):
        m.box(f"Tuft{n}", a, b, "tuft")
    finish("carpetsquare", m, {
        "guiTransform": gui(m.els, (145, -40, 0)),
        "tpHandTransform": held(m.els, "leather", 0.85),
        "groundTransform": ground(m.els, 0.62),
        "storage": storage(m.els, "Messy12", most=0.85),
    })


# ---------------- Wallpaper strip ----------------

@item("wallpaperstrip")
def wallpaperstrip():
    """A curling torn length of the Lobby's yellow chevron wallpaper: the face cut from the wall's own paper, the
    backing off-white and streaked with old paste, the far end rolled up on itself (yellow inside the roll, backing
    out), the near end torn ragged, one corner folded over."""
    t = Tex(1103)
    paper = block_texture("block/wallpaper/chevron-plain")
    t.zone("front", 0, 0, 32, 7)
    t.paint("front", lambda i, j, w, h, r: shade(paper.getpixel((i, j + 3)), r.uniform(0.97, 1.03) * (0.9 if j in (0, 6) else 1.0)))
    paste = noise2(1103, 32, 7, 4)
    t.zone("back", 0, 8, 32, 7)
    t.paint("back", lambda i, j, w, h, r: shade(mix((232, 226, 204), (196, 176, 128), max(0.0, paste(i, j) * 0.9)), r.uniform(0.95, 1.04)))
    t.zone("edge", 0, 16, 32, 1)  # a torn edge: white fibres, a fleck of the yellow
    t.paint("edge", lambda i, j, w, h, r: (238, 234, 216) if (i * 7) % 5 else (214, 206, 150))
    save_tex(t, "wallpaperstrip")

    m = Model("wallpaperstrip", t)
    segs = [(3.0, 0), (3.0, 0), (2.5, 8), (2.0, 22), (1.5, 40), (1.25, 48), (1.25, 52), (1.0, 50)]
    m.chain("Strip", (1.5, 0, 6.25), segs, 3.5, 0.5, None,
            along=lambda k, u: {"top": ("front", min(u, 16 - segs[k][0]), 0), "bottom": ("back", min(u, 16 - segs[k][0]), 0),
                                "side": "edge"})
    # the torn near end: a narrower tongue of paper, ragged
    m.box("Tongue", (0.5, 0, 6.25), (1.5, 0.5, 8.25), {"top": ("front", 0, 0), "bottom": ("back", 0, 0), "side": "edge"})
    m.box("Tongue2", (0.0, 0, 6.75), (0.5, 0.5, 7.5), {"top": ("front", 0, 0.5), "bottom": ("back", 0, 0.5), "side": "edge"})
    # a corner folded over, backing up
    m.box("Fold", (2.5, 0.5, 8.75), (4.0, 0.75, 9.75), {"top": ("back", 1, 2), "bottom": ("front", 1, 2), "side": "edge"},
          rot=(0, 25, 0), origin=(3.25, 0.5, 9.25))
    finish("wallpaperstrip", m, {
        "guiTransform": gui(m.els, (150, -30, 0)),
        "tpHandTransform": held(m.els, "feather", 0.9),
        "groundTransform": ground(m.els, 0.5),
        "storage": storage(m.els, "Quadrants"),
    })


# ---------------- Glass ----------------

GLASS = (198, 224, 222)
GLASS_EDGE = (112, 158, 150)


def paint_glass(t, zone, seed):
    """Frosted fixture glass: a faint prism grid, a sheen streak across it."""
    sheen = noise2(seed, 32, 32, 8)

    def fn(i, j, w, h, r):
        k = 1.0
        if i % 4 == 0 and j % 4 == 0:
            k = 1.08
        elif i % 4 == 2 and j % 4 == 2:
            k = 0.93
        if abs((i - j) - 3) <= 1:
            k *= 1.12  # the sheen
        k *= 1 + 0.05 * sheen(i, j)
        return shade(GLASS, k * r.uniform(0.98, 1.02))
    t.paint(zone, fn)


@item("glassshard")
def glassshard():
    """A broken piece of a light fixture's frosted glass: an irregular flat pane fragment, a sharp tip on one side and
    a chip off the other, its broken edges the green of thick glass."""
    t = Tex(1104)
    t.zone("glass", 0, 0, 24, 24)
    paint_glass(t, "glass", 1104)
    t.zone("edge", 24, 0, 8, 2)
    t.paint("edge", lambda i, j, w, h, r: shade(GLASS_EDGE, (1.15 if j == 0 else 0.9) * r.uniform(0.94, 1.06)))
    t.zone("under", 24, 4, 8, 8)
    t.paint("under", lambda i, j, w, h, r: shade(GLASS, 0.9 * r.uniform(0.96, 1.04)))
    save_tex(t, "glassshard")

    m = Model("glassshard", t)
    plates = [("Body", (5, 6.5), (11, 9.5), 0, (8, 8)), ("Long", (8, 7), (13, 9), 22, (8, 8)), ("Heel", (4, 7.5), (7.5, 10.5), -18, (6, 9)),
              ("Tip", (11.5, 7.75), (14.5, 8.75), 30, (11.5, 8.25)), ("Chip", (6, 5.5), (8.5, 7), 35, (7, 6.5)),
              ("Lobe", (8.5, 9), (10, 10.25), -40, (9.25, 9.6))]
    for n, (name, (x1, z1), (x2, z2), deg, (ox, oz)) in enumerate(plates):
        top = 0.5 + 0.02 * n  # each a hair higher than the last, so overlapping tops never fight
        m.box(name, (x1, 0, z1), (x2, top, z2), {"top": ("glass", x1 - 3.5, z1 - 4.5), "bottom": "under", "side": "edge"},
              rot=(0, deg, 0) if deg else None, origin=(ox, 0, oz))
    finish("glassshard", m, {
        "guiTransform": gui(m.els, (150, -40, 0)),
        "tpHandTransform": held(m.els, "flint", 0.9),
        "groundTransform": ground(m.els, 0.42),
        "storage": storage(m.els, "Messy12", most=0.85),
    })


KNIFE_GUI = (-158, 0, 48)
KNIFE_TP = {"translation": vec(-0.84, -0.11, -0.48), "rotation": vec(0, 0, -15), "origin": vec(0.5, 0.5, 0.5), "scale": 1}
FLAT_HALVES = (-90, 0, 90)  # a knife or bar laid flat in its half of the block, along it


@item("glassshiv")
def glassshiv():
    """A shard bound into a handle: the frosted glass as the blade (vanilla's stone knife's frame: handle low x, blade
    up x), the tang wrapped round with strips of the yellow wallpaper and lashed with twisted carpet fibre at the butt,
    the middle and the blade, a tail of the twine left hanging."""
    t = Tex(1105)
    t.zone("glass", 0, 0, 16, 16)
    paint_glass(t, "glass", 1105)
    t.zone("edge", 16, 0, 16, 2)
    t.paint("edge", lambda i, j, w, h, r: shade(GLASS_EDGE, (1.15 if j == 0 else 0.9) * r.uniform(0.94, 1.06)))
    paper = block_texture("block/wallpaper/chevron-plain")
    t.zone("wrap", 16, 4, 16, 8)  # paper strips wound on the bias: yellow bands with their pale torn edges between
    t.paint("wrap", lambda i, j, w, h, r: (shade((236, 230, 208), 0.92) if (i + j * 2) % 6 == 0
                                           else shade(paper.getpixel((i, j)), 0.96 if (i + j * 2) % 6 == 1 else 1.0)))
    t.zone("twine", 16, 12, 16, 4)  # twisted carpet fibre
    t.paint("twine", lambda i, j, w, h, r: shade(CARPET, (0.76 if (i + j) % 3 == 0 else 1.04) * r.uniform(0.95, 1.05)))
    save_tex(t, "glassshiv")

    m = Model("glassshiv", t)
    blade = {"long": "glass", "top": "edge", "bottom": "edge", "ends": "edge"}
    m.box("Blade", (8.5, -0.25, 7.75), (12, 2.0, 8.25), blade)
    m.box("BladeMid", (11, 0, 7.76), (14, 1.6, 8.24), blade, rot=(0, 0, -6), origin=(11, 0.8, 8))
    m.box("BladeTip", (13.5, 0.35, 7.77), (15.5, 1.15, 8.23), blade, rot=(0, 0, -12), origin=(13.5, 0.75, 8))
    m.box("Notch", (9.5, 1.8, 7.78), (11, 2.3, 8.22), blade, rot=(0, 0, 15), origin=(10.25, 2.05, 8))
    m.box("Grip", (3, -0.25, 7.25), (9, 1.25, 8.75), "wrap")
    m.box("Butt", (2.25, 0, 7.5), (3, 1, 8.5), {"all": "wrap", "ends": ("wrap", 0, 4)})
    for n, x in enumerate((3.5, 6.0)):
        m.box(f"Lash{n}", (x, -0.5, 7.0), (x + 0.75, 1.5, 9.0), "twine")
    m.box("Bolster", (8.25, -0.5, 7.0), (9.25, 1.5, 9.0), "twine")
    m.box("Tail", (8.75, -1.75, 8.0), (9.25, -0.5, 8.5), "twine", rot=(0, 0, 20), origin=(9, -0.5, 8.25))
    finish("glassshiv", m, {
        "guiTransform": gui(m.els, KNIFE_GUI),
        "tpHandTransform": KNIFE_TP,
        "groundTransform": ground(m.els, 0.52, (-90, 0, 0)),
        "storage": storage(m.els, "Halves", FLAT_HALVES),
    })


# ---------------- Steel ----------------

STEEL = (150, 156, 162)
RUST = (150, 82, 42)


def paint_steel(t, zone, seed, base=STEEL, rust=0.12):
    """Galvanised steel: a soft zinc mottle, a few scratches catching the light, rust coming through here and there."""
    mot = noise2(seed, 32, 32, 3)
    rus = noise2(seed + 7, 32, 32, 5)

    def fn(i, j, w, h, r):
        c = shade(base, 1 + 0.07 * mot(i, j))
        if rus(i, j) > 1 - rust * 4:
            c = mix(c, RUST, min(1.0, (rus(i, j) - (1 - rust * 4)) * 4))
        if (i * 3 + j * 7) % 23 == 0:
            c = shade(c, 1.18)
        return shade(c, r.uniform(0.97, 1.03))
    t.paint(zone, fn)


@item("scraper")
def scraper():
    """A steel bracket from the ceiling grid ground to an edge: a flat blade with the bracket's two bolt holes still
    in it and a bright ground bevel along its edge, its point ground at a slant; the grip wrapped in a strip of carpet
    and bound with copper wire, a bolt through the blade at the grip (vanilla's knife frame)."""
    t = Tex(1106)
    t.zone("blade", 0, 0, 14, 5)
    paint_steel(t, "blade", 1106)
    for (hx, hy) in ((4, 2), (9, 2)):  # the bolt holes
        t.put("blade", hx, hy, (40, 40, 42))
        t.put("blade", hx + 1, hy, (58, 58, 62))
        t.put("blade", hx, hy + 1, (66, 66, 70))
        t.put("blade", hx + 1, hy + 1, shade(STEEL, 1.22))
    for i in range(14):
        t.put("blade", i, 4, shade(STEEL, 1.3))  # the ground edge
    t.zone("steel", 0, 6, 16, 6)
    paint_steel(t, "steel", 1107, rust=0.2)
    t.zone("bevel", 0, 12, 16, 1)
    t.paint("bevel", lambda i, j, w, h, r: shade((214, 220, 226), r.uniform(0.94, 1.06)))
    carpet = block_texture("block/carpet-soaked")
    t.zone("cloth", 16, 0, 16, 8)
    t.paint("cloth", lambda i, j, w, h, r: shade(carpet.getpixel((i, j)), 0.84 if (i + j * 3) % 7 == 0 else 1.0))
    t.zone("copper", 16, 8, 16, 4)
    t.paint("copper", lambda i, j, w, h, r: shade((184, 104, 56), (1.25 if j == 1 else 0.85 if j == 3 else 1.0) * (0.82 if i % 2 else 1.0)))
    save_tex(t, "scraper")

    m = Model("scraper", t)
    m.box("Blade", (8.5, -0.25, 7.75), (15, 2.0, 8.25), {"long": ("blade", 0, 0), "top": "steel", "ends": "steel", "bottom": "bevel"})
    m.box("Point", (14.25, -0.25, 7.76), (16, 1.0, 8.24), {"long": ("steel", 2, 1), "top": "steel", "ends": "bevel", "bottom": "bevel"},
          rot=(0, 0, 28), origin=(14.25, -0.25, 8))
    m.box("Edge", (8.5, -0.5, 7.875), (14.75, -0.25, 8.125), "bevel")
    m.box("Bolt", (9.25, 0.4, 7.4), (10.25, 1.4, 8.6), {"all": ("steel", 4, 3), "long": ("steel", 0, 0)})
    m.box("Grip", (3, -0.25, 7.25), (9, 1.5, 8.75), "cloth")
    m.box("Flap", (2.25, 0, 7.4), (3, 1.25, 8.6), ("cloth", 3, 2))
    for n, x in enumerate((4.0, 7.75)):
        m.box(f"Wire{n}", (x, -0.4, 7.1), (x + 0.5, 1.65, 8.9), "copper")
    finish("scraper", m, {
        "guiTransform": gui(m.els, KNIFE_GUI),
        "tpHandTransform": KNIFE_TP,
        "groundTransform": ground(m.els, 0.55, (-90, 0, 0)),
        "storage": storage(m.els, "Halves", FLAT_HALVES),
    })


# ---------------- Pry bar ----------------

RED = (164, 40, 32)


@item("prybar")
def prybar():
    """A proper wrecking bar (vanilla's crowbar frame: the shaft along x, the claw at the far end): a bevelled bar in
    chipped red paint, worn to bare steel at both working ends; the near end a flattened chisel bent a little, the far
    end a gooseneck curling right round into a split claw."""
    t = Tex(1107)
    chips = noise2(1107, 32, 16, 3)
    t.zone("red", 0, 0, 32, 4)
    t.paint("red", lambda i, j, w, h, r: (shade((76, 78, 82), r.uniform(0.9, 1.1)) if chips(i, j) > 0.62
                                          else shade(RED, (1.15 if j == 0 else 0.9 if j == 3 else 1.0) * r.uniform(0.94, 1.05))))
    t.zone("worn", 0, 4, 32, 4)  # the paint going at the ends: more steel than red
    t.paint("worn", lambda i, j, w, h, r: (shade(RED, 0.92 * r.uniform(0.92, 1.05)) if chips(i, j + 6) > 0.35
                                           else shade((96, 98, 104), (1.2 if (i + j) % 5 == 0 else 1.0) * r.uniform(0.92, 1.08))))
    t.zone("steel", 0, 8, 32, 4)
    t.paint("steel", lambda i, j, w, h, r: shade((104, 106, 112), (1.25 if (i * 2 + j) % 7 == 0 else 1.0) * r.uniform(0.9, 1.1)))
    t.zone("end", 0, 12, 4, 4)
    t.paint("end", lambda i, j, w, h, r: shade((150, 152, 158), r.uniform(0.92, 1.08)))
    save_tex(t, "prybar")

    m = Model("prybar", t)
    m.box("Shaft", (3, 0.125, 7.5), (13, 0.875, 8.5), {"all": "red", "ends": "end"})
    m.box("ShaftB", (3, 0, 7.625), (13, 1, 8.375), {"all": "red", "ends": "end"})
    m.box("Chisel", (1.25, 0.15, 7.4), (3.25, 0.85, 8.6), {"all": "worn", "ends": "end"}, rot=(0, 0, -10), origin=(3.25, 0.5, 8))
    m.box("ChiselTip", (0.25, 0.3, 7.3), (1.5, 0.65, 8.7), {"all": "steel", "ends": "end"}, rot=(0, 0, -10), origin=(3.25, 0.5, 8))
    neck = m.chain("Neck", (12.9, 0, 7.5), [(1.25, 10), (1.0, 25), (1.0, 30), (1.0, 30), (1.0, 30), (0.9, 30), (0.8, 25)], 1.0, 1.0,
                   None, along=lambda k, u: {"all": ("worn" if k < 4 else "steel", u * 2 % 12, 0), "ends": "end"})
    last = neck[-1]
    for n, (z1, z2) in enumerate(((0.0, 0.42), (0.58, 1.0))):
        m.box(f"Prong{n}", (0.8, 0.1, z1), (1.7, 0.7, z2), {"all": "steel", "ends": "end"}, rot=(0, 0, -8), origin=(0.8, 0.4, 0.5), parent=last)
    finish("prybar", m, {
        "guiTransform": gui(m.els, (-157, 0, -48)),
        "tpHandTransform": {"translation": vec(-0.63, 0.08, -0.52), "rotation": vec(180, 0, 0), "origin": vec(0.5, 0, 0.5), "scale": 0.95},
        "groundTransform": ground(m.els, 0.8, (-90, 0, 0)),
        "storage": storage(m.els, "Halves", FLAT_HALVES),
    })


# ---------------- Metal bracket ----------------

@item("metalbracket")
def metalbracket():
    """A steel angle bracket from a ceiling grid or a light fixture: one leg lying flat, the other bent up past square,
    a gusset pressed into the corner, two screw holes in each leg and a wood screw still stuck in one; galvanised,
    rust in the bend."""
    t = Tex(1108)
    t.zone("leg", 0, 0, 16, 6)
    paint_steel(t, "leg", 1108, rust=0.1)
    for hx in (4, 10):  # screw holes, a pixel and a half across: dark with a lit lower rim
        t.put("leg", hx, 2, (58, 58, 62))
        t.put("leg", hx + 1, 2, (92, 94, 98))
        t.put("leg", hx, 3, (96, 98, 102))
        t.put("leg", hx + 1, 3, shade(STEEL, 1.22))
    t.zone("edge", 0, 6, 16, 1)
    t.paint("edge", lambda i, j, w, h, r: shade(STEEL, 1.2 * r.uniform(0.94, 1.06)))
    t.zone("rusty", 0, 8, 16, 4)
    paint_steel(t, "rusty", 1109, rust=0.4)
    t.zone("screw", 16, 0, 8, 4)
    t.paint("screw", lambda i, j, w, h, r: shade((176, 168, 140), (1.2 if (i + j) % 3 == 0 else 0.9) * r.uniform(0.94, 1.06)))
    save_tex(t, "metalbracket")

    m = Model("metalbracket", t)
    leg = {"top": ("leg", 0, 0), "bottom": ("leg", 0, 0), "side": "edge"}
    m.box("Flat", (5.5, 0, 6.5), (12.5, 0.5, 9.5), leg)
    m.box("Up", (5.0, 0, 6.5), (5.5, 6.0, 9.5), {"ends": ("leg", 0, 0), "long": "edge", "top": "edge", "bottom": "edge"},
          rot=(0, 0, 8), origin=(5.5, 0, 8))
    m.box("Bend", (5.0, 0, 6.6), (6.0, 0.75, 9.4), "rusty")
    m.box("Gusset", (5.5, 0.5, 7.75), (7.0, 1.5, 8.25), "rusty")
    m.box("ScrewHead", (9.75, 0.5, 7.25), (10.75, 0.75, 8.25), "screw")
    m.box("ScrewShank", (10.0, 0.75, 7.5), (10.5, 2.25, 8.0), "screw", rot=(0, 0, -20), origin=(10.25, 0.75, 7.75))
    finish("metalbracket", m, {
        "guiTransform": gui(m.els, (155, -45, 0)),
        "tpHandTransform": held(m.els, "nails", 0.9),
        "groundTransform": ground(m.els, 0.36),
        "storage": storage(m.els, "Messy12", most=0.85),
    })


# ---------------- Scrap wire ----------------

def ring(m, name, cx, cz, r, y, th, zone, turn=0.0, drop=0.0):
    """An octagonal loop of wire lying flat: eight bars round (cx, cz), radius r, thickness th, its far side `drop`
    units lower or higher than its near side (a loose coil is never level)."""
    side = 2 * r * math.tan(math.pi / 8) + th
    out = []
    for k in range(8):
        a = turn + k * 45
        rad = math.radians(a)
        # each bar's centre on the ring, the bar along its tangent
        bx, bz = cx + r * math.cos(rad), cz + r * math.sin(rad)
        dy = drop * math.sin(rad) / 2
        el = m.box(f"{name}{k}", (bx - side / 2, y + dy, bz - th / 2), (bx + side / 2, y + dy + th, bz + th / 2), zone,
                   rot=(0, -(a + 90), 0), origin=(bx, y + dy, bz))
        out.append(el)
    return out


@item("scrapwire")
def scrapwire():
    """A tangle of copper wire pulled from the ceiling: three loose loops coiled on each other, never quite level,
    the copper bright where it was bent and brown where it was not; one end still in a stub of red insulation, the
    other sticking out kinked."""
    t = Tex(1110)
    tar = noise2(1110, 32, 8, 3)
    t.zone("copper", 0, 0, 32, 2)
    t.paint("copper", lambda i, j, w, h, r: shade(mix((196, 112, 58), (122, 74, 44), max(0.0, tar(i, j) * 0.8)),
                                                  (1.25 if j == 0 and i % 5 == 0 else 1.0 if j == 0 else 0.82) * r.uniform(0.95, 1.05)))
    t.zone("insul", 0, 4, 16, 3)
    t.paint("insul", lambda i, j, w, h, r: shade((170, 44, 36), (1.18 if j == 0 else 0.86 if j == 2 else 1.0) * r.uniform(0.95, 1.05)))
    t.zone("cut", 16, 4, 2, 2)
    t.paint("cut", lambda i, j, w, h, r: (226, 150, 92))
    save_tex(t, "scrapwire")

    m = Model("scrapwire", t)
    ring(m, "LoopA", 8.0, 8.0, 3.2, 0.0, 0.5, "copper", turn=10, drop=0.2)
    ring(m, "LoopB", 8.6, 7.6, 2.9, 0.45, 0.5, "copper", turn=30, drop=-0.3)
    ring(m, "LoopC", 7.5, 8.5, 2.6, 0.9, 0.5, "copper", turn=0, drop=0.4)
    m.box("Insulated", (10.5, 0.0, 10.5), (14.0, 0.75, 11.25), {"all": "insul", "ends": "cut"}, rot=(0, -30, 0), origin=(10.5, 0, 10.9))
    m.box("Bare", (13.5, 0.15, 10.65), (14.75, 0.6, 11.1), "copper", rot=(0, -30, 0), origin=(10.5, 0, 10.9))
    m.box("Kink1", (3.0, 0.0, 5.0), (5.5, 0.5, 5.5), "copper", rot=(0, 20, 0), origin=(5.5, 0, 5.25))
    m.box("Kink2", (1.5, 0.0, 5.0), (3.25, 0.5, 5.5), "copper", rot=(0, -35, 0), origin=(3.25, 0, 5.25))
    finish("scrapwire", m, {
        "guiTransform": gui(m.els, (150, -30, 0)),
        "tpHandTransform": held(m.els, "rope", 0.75),
        "groundTransform": ground(m.els, 0.36),
        "storage": storage(m.els, "Messy12", most=0.85),
    })


# ---------------- Rubble ----------------

def paint_concrete(t, zone, seed, base=(134, 132, 126)):
    """Concrete broken open: grey cement with the stone of the aggregate showing in it."""
    agg = noise2(seed, 32, 32, 2)

    def fn(i, j, w, h, r):
        c = shade(base, 1 + 0.06 * agg(i, j))
        v = r.random()
        if v < 0.10:
            c = shade((110, 104, 96), r.uniform(0.9, 1.1))
        elif v < 0.16:
            c = shade((168, 162, 150), r.uniform(0.95, 1.05))
        return shade(c, r.uniform(0.96, 1.04))
    t.paint(zone, fn)


@item("rubble")
def rubble():
    """Lumps of broken concrete, brick and plaster: what a wall comes down to. A big angular lump of concrete with its
    aggregate showing, half a red brick, a slab of plaster with a scrap of the Lobby's yellow paper still on its face,
    and grit."""
    t = Tex(1111)
    t.zone("concrete", 0, 0, 16, 16)
    paint_concrete(t, "concrete", 1111)
    t.zone("brick", 16, 0, 16, 8)
    t.paint("brick", lambda i, j, w, h, r: shade((150, 72, 52), (0.82 if r.random() < 0.18 else 1.0) * (1.1 if j == 0 else 1.0) * r.uniform(0.93, 1.06)))
    t.zone("mortar", 16, 8, 16, 2)
    t.paint("mortar", lambda i, j, w, h, r: shade((182, 176, 160), r.uniform(0.9, 1.06)))
    t.zone("plaster", 16, 10, 16, 6)
    t.paint("plaster", lambda i, j, w, h, r: shade((222, 214, 192), r.uniform(0.93, 1.05)))
    paper = block_texture("block/wallpaper/chevron-plain")
    t.zone("paper", 16, 16, 8, 8)
    t.paint("paper", lambda i, j, w, h, r: paper.getpixel((i + 4, j + 2)) if (i + j) < 11 else shade((222, 214, 192), r.uniform(0.93, 1.05)))
    t.zone("grit", 0, 16, 16, 4)
    paint_concrete(t, "grit", 1112, base=(118, 116, 110))
    save_tex(t, "rubble")

    m = Model("rubble", t)
    # the concrete lump: an angular core with two broken faces cut across it
    m.box("Concrete", (4.5, 0, 6.0), (9.5, 3.0, 10.0), "concrete", rot=(0, 15, 0), origin=(7, 0, 8))
    m.box("ConcreteB", (5.0, 0, 5.0), (8.5, 2.25, 9.0), "concrete", rot=(0, -20, 0), origin=(7, 0, 7))
    m.box("ConcreteTop", (5.5, 2.5, 6.75), (8.5, 3.5, 9.25), "concrete", rot=(8, 15, 0), origin=(7, 3, 8))
    # half a brick lying on its side, mortar still on its end
    m.box("Brick", (9.5, 0, 8.5), (13.5, 2.0, 10.5), {"all": "brick", "left": "mortar"}, rot=(0, -25, 0), origin=(11.5, 0, 9.5))
    m.box("BrickMortar", (9.0, 0.25, 8.75), (9.5, 1.75, 10.25), "mortar", rot=(0, -25, 0), origin=(11.5, 0, 9.5))
    # a slab of plaster, paper side up
    m.box("Plaster", (8.5, 0, 3.5), (12.5, 1.0, 6.5), {"all": "plaster", "top": ("paper", 0, 0)}, rot=(0, 30, 0), origin=(10.5, 0, 5))
    m.box("PlasterB", (11.0, 0, 5.0), (12.75, 0.75, 7.0), "plaster", rot=(0, 10, 0), origin=(12, 0, 6))
    for n, (x, z, s, a) in enumerate([(3.0, 10.5, 1.0, 20), (6.5, 11.5, 0.75, -10), (13.0, 6.5, 1.0, 40), (3.5, 5.0, 0.75, 0)]):
        m.box(f"Grit{n}", (x, 0, z), (x + s, s * 0.8, z + s), "grit", rot=(0, a, 0) if a else None, origin=(x, 0, z))
    finish("rubble", m, {
        "guiTransform": gui(m.els, (150, -35, 0)),
        "tpHandTransform": held(m.els, "stone", 1.1),
        "groundTransform": ground(m.els, 0.42),
        "storage": storage(m.els, "Messy12", most=0.85),
    })


# ---------------- Pottery ----------------

TERRACOTTA = (178, 96, 58)


@item("ceramicgrit")
def ceramicgrit():
    """Pottery shards pounded with a stone: a little heap of terracotta grit, coarse orange-brown grains with the odd
    chip of the pot's glaze in them, and loose grains run out round its foot."""
    t = Tex(1113)
    t.zone("grit", 0, 0, 16, 16)
    t.paint("grit", lambda i, j, w, h, r: (shade((214, 206, 176), r.uniform(0.95, 1.05)) if r.random() < 0.012 else
                                           shade(TERRACOTTA, (0.72 if r.random() < 0.25 else 1.12 if r.random() < 0.2 else 1.0) * r.uniform(0.94, 1.06))))
    t.zone("dark", 16, 0, 8, 8)
    t.paint("dark", lambda i, j, w, h, r: shade(TERRACOTTA, (0.62 if r.random() < 0.3 else 0.8) * r.uniform(0.94, 1.06)))
    save_tex(t, "ceramicgrit")

    m = Model("ceramicgrit", t)
    m.box("Heap", (4.5, 0, 5.0), (11.5, 1.0, 11.0), {"all": "grit", "bottom": "dark"})
    m.box("Heap2", (5.5, 1.0, 6.0), (10.5, 2.0, 10.0), {"all": "grit", "bottom": None})
    m.box("Heap3", (6.5, 2.0, 7.0), (9.75, 2.75, 9.25), {"all": "grit", "bottom": None})
    m.box("Peak", (7.5, 2.75, 7.5), (9.0, 3.25, 8.75), {"all": "grit", "bottom": None})
    m.box("SpillA", (3.5, 0, 6.5), (4.5, 0.5, 9.5), "grit")
    m.box("SpillB", (11.5, 0, 6.0), (12.5, 0.5, 8.5), "grit")
    m.box("SpillC", (6.0, 0, 11.0), (9.5, 0.5, 12.0), "grit")
    m.box("SpillD", (6.5, 0, 4.0), (10.0, 0.5, 5.0), "grit")
    for n, (x, z, a) in enumerate([(2.5, 9.5, 20), (13.0, 9.5, -15), (10.5, 3.0, 35), (4.0, 3.5, 10), (12.75, 4.5, 0)]):
        m.box(f"Grain{n}", (x, 0, z), (x + 0.75, 0.5, z + 0.75), "grit", rot=(0, a, 0) if a else None, origin=(x, 0, z))
    finish("ceramicgrit", m, {
        "guiTransform": gui(m.els, (145, -35, 0)),
        "tpHandTransform": held(m.els, "stone", 1.1),
        "groundTransform": ground(m.els, 0.34),
        "storage": storage(m.els, "Quadrants"),
    })


@item("potshard")
def potshard():
    """A piece of the fired pot a dead office plant stood in: a curved shard of the wall lying hollow side up, a bit of
    the thick rim along one end, broken edges ragged, the outside glazed a faded office green, the inside bare
    terracotta still dirty with the plant's dried soil."""
    t = Tex(1114)
    soil = noise2(1114, 32, 32, 4)
    t.zone("inside", 0, 0, 16, 12)
    t.paint("inside", lambda i, j, w, h, r: (shade((70, 52, 40), r.uniform(0.85, 1.1)) if soil(i, j) > 0.25 else
                                             shade(TERRACOTTA, (0.92 if j % 3 == 0 else 1.0) * r.uniform(0.94, 1.05))))
    t.zone("outside", 16, 0, 16, 12)
    t.paint("outside", lambda i, j, w, h, r: shade((112, 138, 104), (0.9 if (i + j) % 7 == 0 else 1.0) * r.uniform(0.95, 1.05)))
    t.zone("break", 0, 12, 16, 2)  # the broken edge: raw terracotta, a glaze line on the outer side
    t.paint("break", lambda i, j, w, h, r: shade(TERRACOTTA if j == 0 else (104, 128, 96), r.uniform(0.92, 1.08)))
    t.zone("rim", 0, 16, 16, 4)
    t.paint("rim", lambda i, j, w, h, r: shade((112, 138, 104), (1.15 if j == 0 else 0.92) * r.uniform(0.95, 1.05)))
    save_tex(t, "potshard")

    m = Model("potshard", t)
    wall = {"top": "inside", "bottom": "outside", "side": "break"}
    # three bands of the curved wall: the middle flat on the floor, the sides tipped up round it
    m.box("Mid", (4.0, 0, 6.75), (12.0, 0.75, 9.25), wall)
    m.box("Near", (4.5, 0, 4.25), (11.0, 0.75, 6.85), wall, rot=(28, 0, 0), origin=(8, 0, 6.85))
    m.box("Far", (4.0, 0, 9.15), (10.0, 0.75, 11.5), wall, rot=(-28, 0, 0), origin=(8, 0, 9.15))
    # the rim, thicker, along the near end
    rim = {"all": "rim", "top": ("rim", 0, 0)}
    m.box("RimMid", (3.0, 0, 6.75), (4.25, 1.25, 9.25), rim)
    m.box("RimNear", (3.5, 0, 4.25), (4.75, 1.25, 6.85), rim, rot=(28, 0, 0), origin=(8, 0, 6.85))
    m.box("RimFar", (3.0, 0, 9.15), (4.25, 1.25, 11.5), rim, rot=(-28, 0, 0), origin=(8, 0, 9.15))
    m.box("Chip", (12.0, 0, 7.25), (13.25, 0.75, 8.75), wall, rot=(0, 25, 0), origin=(12, 0, 8))
    finish("potshard", m, {
        "guiTransform": gui(m.els, (145, -35, 0)),
        "tpHandTransform": held(m.els, "flint", 0.9),
        "groundTransform": ground(m.els, 0.38),
        "storage": storage(m.els, "Quadrants"),
    })


# ---------------- Rotten wood ----------------

@item("rottenwood")
def rottenwood():
    """A soft, damp batten from above the ceiling: a length of pale pine gone grey, snapped off at one end in long
    splinters, the other end dark and crumbling with rot (a bite gone out of it, white threads of mould on it), a
    rusty nail still through it."""
    t = Tex(1115)
    grain = noise2(1115, 32, 32, 3)
    t.zone("wood", 0, 0, 32, 8)  # along the grain, across the texture
    t.paint("wood", lambda i, j, w, h, r: shade(mix((156, 128, 92), (92, 74, 56), max(0.0, min(1.0, (i - 18) / 14))),
                                                (0.86 if (j * 5 + int(3 * grain(i, j))) % 4 == 0 else 1.0) * r.uniform(0.95, 1.05)))
    rot = noise2(1116, 16, 16, 3)
    t.zone("rot", 0, 8, 16, 8)
    t.paint("rot", lambda i, j, w, h, r: ((214, 210, 196) if rot(i, j) > 0.55 else
                                          shade((70, 56, 44), (0.7 if rot(i, j) < -0.3 else 1.0) * r.uniform(0.9, 1.1))))
    t.zone("endgrain", 16, 8, 8, 4)
    t.paint("endgrain", lambda i, j, w, h, r: shade((176, 146, 104), 0.86 if (i + j) % 3 == 0 else 1.0))
    t.zone("splinter", 16, 12, 16, 2)
    t.paint("splinter", lambda i, j, w, h, r: shade((178, 150, 108), (1.08 if j == 0 else 0.9) * r.uniform(0.94, 1.06)))
    t.zone("nail", 24, 8, 4, 4)
    t.paint("nail", lambda i, j, w, h, r: shade((120, 70, 40), r.uniform(0.8, 1.2)))
    save_tex(t, "rottenwood")

    m = Model("rottenwood", t)
    # x 2..12 sound wood, 12..14.5 rotting; 2.5 wide (z), 1.5 tall
    m.box("Batten", (3.0, 0, 6.75), (11.0, 1.5, 9.25), {"all": ("wood", 0, 0), "ends": "endgrain"})
    m.box("Rotten", (11.0, 0, 6.75), (13.5, 1.25, 8.75), {"all": "rot", "ends": "rot"})
    m.box("RottenB", (11.0, 0, 8.25), (12.25, 1.0, 9.25), "rot")
    m.box("Crumb", (13.5, 0, 7.25), (14.25, 0.75, 8.25), "rot")
    m.box("Crumb2", (14.5, 0, 9.0), (15.25, 0.5, 9.75), "rot")
    # the snapped end: splinters of different lengths
    m.box("SplinterA", (1.0, 0.75, 6.75), (3.0, 1.5, 7.5), {"all": "splinter", "ends": "endgrain"})
    m.box("SplinterB", (1.75, 0, 7.75), (3.0, 1.0, 8.75), {"all": "splinter", "ends": "endgrain"})
    m.box("SplinterC", (0.25, 0.25, 8.5), (3.0, 0.75, 9.0), {"all": "splinter", "ends": "endgrain"}, rot=(0, 6, 0), origin=(3, 0.5, 8.75))
    m.box("NailHead", (7.0, 1.5, 7.5), (8.0, 1.75, 8.5), "nail")
    m.box("NailShank", (7.25, 1.75, 7.75), (7.75, 2.75, 8.25), "nail", rot=(0, 0, 25), origin=(7.5, 1.75, 8))
    finish("rottenwood", m, {
        "guiTransform": gui(m.els, (150, -35, 0)),
        "tpHandTransform": held(m.els, "stick", 0.85),
        "groundTransform": ground(m.els, 0.6),
        "storage": storage(m.els, "Quadrants"),
    })


# ---------------- Seed packets ----------------

SEED_LOOK = {  # the crop's colour, and what is drawn on the front
    "turnip": ((196, 120, 200), "turnip"), "carrot": ((232, 128, 40), "carrot"), "onion": ((210, 180, 110), "onion"),
    "flax": ((90, 130, 210), "flax"), "spelt": ((210, 176, 70), "spelt"),
}


SEED_ART = {  # 8 x 7, top row first
    "carrot": ["  g g   ", "  gGg   ", "  ooo   ", "  ooO   ", "   oO   ", "   o    ", "   o    "],
    "turnip": ["  gGg   ", "   g    ", "  ppp   ", " ppppp  ", " wwwww  ", "  www   ", "   w    "],
    "onion": ["   gg   ", "   g    ", "  bBb   ", " bBbbb  ", " bbBbb  ", "  bbb   ", "   w    "],
    "flax": ["  u u   ", "   y    ", "  u u   ", "   g    ", " u g    ", "   g    ", "   g    "],
    "spelt": ["   s    ", "  sSs   ", "  sSs   ", "  sSs   ", "   S    ", "   S    ", "   S    "],
}


def seed_texture(crop):
    """The packet: front (16 x 16 px) a printed card with the crop pictured in a window on its colour, a band of
    faded print (never words) and a stripe; back the instructions' lines; crimped top; one texture a crop."""
    col, pic = SEED_LOOK[crop]
    t = Tex(1117 + len(crop))
    paper = (232, 224, 200)
    t.zone("front", 0, 0, 12, 16)

    # the up face runs +z with the texture's rows, and the fold is at +z: the packet's top is the zone's bottom, so
    # the print is at the top of the zone, the window in the middle and the coloured band at the bottom
    def front(i, j, w, h, r):
        c = paper
        if j >= 14:
            c = shade(col, 0.85)                       # the coloured band under the fold
        elif 4 <= j <= 12 and 1 <= i <= 10:
            c = shade(col, 1.0 if 5 <= j <= 11 and 2 <= i <= 9 else 0.8)  # the picture's window, framed
        elif j in (1, 3) and 2 <= i <= 9 - (j == 1) * 3:
            c = (96, 88, 74)                           # faded print
        if i in (0, 11):
            c = shade(c, 0.9)
        return shade(c, r.uniform(0.96, 1.03))
    t.paint("front", front)
    # the picture, 8 x 7 px in the window, drawn the right way up (its first row at the packet's top)
    art = SEED_ART[pic]
    pal = {"g": (64, 140, 52), "G": (44, 104, 40), "o": (240, 120, 30), "O": (196, 88, 22), "w": (244, 240, 226),
           "p": (150, 60, 160), "b": (176, 118, 60), "B": (206, 160, 96), "u": (160, 190, 250), "y": (250, 230, 120),
           "s": (236, 204, 104), "S": (170, 132, 50)}
    for row, line in enumerate(art):
        for col_i, ch in enumerate(line):
            if ch in pal:
                t.put("front", 2 + col_i, 11 - row, pal[ch])
    t.zone("back", 12, 0, 12, 16)

    def back(i, j, w, h, r):
        c = paper
        if j % 3 == 1 and 1 <= i <= 10 - (j * 3) % 4:
            c = (150, 142, 124)                        # rows of instructions, too faded to read
        return shade(c, r.uniform(0.95, 1.03) * (0.92 if (i * 3 + j) % 11 == 0 else 1.0))
    t.paint("back", back)
    t.zone("edge", 24, 0, 8, 2)
    t.paint("edge", lambda i, j, w, h, r: shade(paper, 0.86 if j else 0.95))
    t.zone("crimp", 24, 2, 8, 2)
    t.paint("crimp", lambda i, j, w, h, r: shade(col, (0.75 if i % 2 else 0.95)))
    t.zone("bulge", 24, 4, 8, 8)
    t.paint("bulge", lambda i, j, w, h, r: shade(paper, 0.97 * r.uniform(0.96, 1.03)))
    save_tex(t, f"seedpacket-{crop}")
    return t


@item("seedpacket")
def seedpacket():
    """An old paper packet of seeds, still sealed: a flat envelope lying face up, the seeds plumping its middle, the
    top folded over and crimped, a corner dog-eared; the front printed with the crop in a window on the crop's colour
    and bands of faded print (no words); one model, a texture for each of the five crops."""
    t = None
    for crop in SEED_LOOK:
        t = seed_texture(crop)
    m = Model("seedpacket", t, key="packet")
    m.box("Body", (5.0, 0, 4.0), (11.0, 0.5, 12.0), {"top": ("front", 0, 0), "bottom": ("back", 0, 0), "side": "edge"})
    m.box("Seeds", (5.75, 0.5, 5.0), (10.25, 0.85, 10.5), {"top": ("front", 0.75, 1.0), "side": "bulge", "bottom": None})
    m.box("Fold", (5.0, 0.5, 11.0), (11.0, 0.75, 12.25), {"top": "crimp", "side": "edge", "bottom": "crimp"})
    m.box("DogEar", (9.5, 0.5, 4.0), (11.0, 0.65, 5.5), {"top": ("back", 0, 0), "side": "edge", "bottom": None},
          rot=(0, 45, 0), origin=(10.25, 0.5, 4.75))
    finish("seedpacket", m, {
        "guiTransform": gui(m.els, (150, -25, 0)),
        "tpHandTransform": held(m.els, "flint", 0.75),
        "groundTransform": ground(m.els, 0.3),
        "storage": storage(m.els, "Quadrants"),
    }, textures={"packet": f"backrooms:{TEXDIR}/seedpacket-turnip"})


# ---------------- Harvest materials ----------------

@item("clumpsinew")
def clumpsinew():
    """A Clump's dried sinew: a coil of pale cord, two loops lying loose on each other, bound across with a twist of
    itself, a tail left out; cream fading to a dried pink, darker where it is thin."""
    t = Tex(1120)
    t.zone("cord", 0, 0, 32, 2)
    t.paint("cord", lambda i, j, w, h, r: shade(mix((214, 194, 166), (196, 150, 140), 0.5 + 0.5 * math.sin(i * 0.7)),
                                                (1.1 if j == 0 else 0.86) * (0.9 if i % 4 == 0 else 1.0) * r.uniform(0.95, 1.05)))
    t.zone("tie", 0, 4, 8, 4)
    t.paint("tie", lambda i, j, w, h, r: shade((168, 132, 112), (0.8 if (i + j) % 3 == 0 else 1.0) * r.uniform(0.95, 1.05)))
    save_tex(t, "clumpsinew")

    m = Model("clumpsinew", t)
    ring(m, "LoopA", 8.0, 8.0, 3.0, 0.0, 0.75, "cord", turn=0, drop=0.2)
    ring(m, "LoopB", 8.5, 8.25, 2.6, 0.6, 0.75, "cord", turn=22.5, drop=-0.3)
    m.box("Tie", (4.25, 0, 7.0), (5.75, 1.75, 9.0), "tie")
    m.box("Tail", (11.0, 0, 10.5), (14.5, 0.75, 11.25), "cord", rot=(0, -25, 0), origin=(11, 0, 10.9))
    finish("clumpsinew", m, {
        "guiTransform": gui(m.els, (150, -30, 0)),
        "tpHandTransform": held(m.els, "rope", 0.7),
        "groundTransform": ground(m.els, 0.34),
        "storage": storage(m.els, "Quadrants"),
    })


@item("mothjelly")
def mothjelly():
    """A lump of amber jelly from a Deathmoth hive: a glossy rounded blob sagging under its own weight, a drip run
    down one side, a shard of the hive's grey chewed-paper comb stuck in its top; amber with a wet highlight and a
    deep, darker heart."""
    t = Tex(1121)
    depth = noise2(1121, 32, 32, 5)
    t.zone("jelly", 0, 0, 16, 16)
    t.paint("jelly", lambda i, j, w, h, r: (shade((252, 214, 120), 1.0) if (i - 4) ** 2 + (j - 4) ** 2 < 3 else
                                            shade(mix((228, 156, 44), (150, 78, 20), max(0.0, min(1.0, 0.35 + 0.5 * depth(i, j)))),
                                                  r.uniform(0.97, 1.03))))
    t.zone("side", 16, 0, 16, 8)
    t.paint("side", lambda i, j, w, h, r: shade(mix((214, 140, 36), (140, 70, 18), j / 8), (1.15 if (i * 5) % 13 == 0 and j < 3 else 1.0)))
    t.zone("comb", 16, 8, 8, 8)
    t.paint("comb", lambda i, j, w, h, r: shade((150, 146, 136), (0.7 if (i % 3 == 0 or (j + (i // 3) % 2 * 1) % 3 == 0) else 1.0) * r.uniform(0.94, 1.06)))
    save_tex(t, "mothjelly")

    m = Model("mothjelly", t)
    m.box("Base", (4.5, 0, 5.0), (11.5, 1.5, 11.0), {"top": ("jelly", 0, 0), "side": "side", "bottom": "side"})
    m.box("BaseX", (4.0, 0, 6.0), (12.0, 1.25, 10.0), {"top": ("jelly", 0, 1), "side": "side", "bottom": "side"})
    m.box("BaseZ", (5.5, 0, 4.5), (10.5, 1.25, 11.5), {"top": ("jelly", 1, 0), "side": "side", "bottom": "side"})
    m.box("Middle", (5.5, 1.5, 6.0), (10.5, 2.75, 10.0), {"top": ("jelly", 1, 1), "side": ("side", 0, 0), "bottom": None})
    m.box("MiddleX", (5.0, 1.5, 6.75), (11.0, 2.25, 9.25), {"top": ("jelly", 0.5, 2), "side": ("side", 0, 0), "bottom": None})
    m.box("MiddleZ", (6.25, 1.5, 5.25), (9.75, 2.25, 10.75), {"top": ("jelly", 2, 0.5), "side": ("side", 0, 0), "bottom": None})
    m.box("Top", (6.5, 2.75, 6.75), (9.5, 3.5, 9.25), {"top": ("jelly", 2, 2), "side": ("side", 0, 0), "bottom": None})
    m.box("Drip", (11.5, 0, 7.5), (12.75, 0.75, 8.75), {"all": "side", "top": ("jelly", 6, 6)})
    m.box("DripRun", (10.5, 0.5, 7.75), (11.75, 1.5, 8.5), {"all": "side", "top": ("jelly", 6, 6)})
    m.box("Comb", (7.0, 2.5, 7.5), (9.5, 4.25, 8.0), "comb", rot=(0, 30, 12), origin=(8.25, 3, 7.75))
    finish("mothjelly", m, {
        "guiTransform": gui(m.els, (150, -30, 0)),
        "tpHandTransform": held(m.els, "fat", 0.9),
        "groundTransform": ground(m.els, 0.32),
        "storage": storage(m.els, "Quadrants"),
    })


@item("mothquill")
def mothquill():
    """A Deathmoth larva's quill, a hand's length: a hollow, pale shaft tapering from its open end (dark inside) to
    a black tip, a ridge of little barbs along it, a faint curve."""
    t = Tex(1122)
    t.zone("shaft", 0, 0, 32, 3)
    t.paint("shaft", lambda i, j, w, h, r: shade(mix((236, 228, 204), (200, 186, 156), i / 32),
                                                 (1.1 if j == 0 else 0.88 if j == 2 else 1.0) * (0.94 if i % 6 == 0 else 1.0) * r.uniform(0.97, 1.03)))
    t.zone("tip", 0, 4, 16, 2)
    t.paint("tip", lambda i, j, w, h, r: shade((44, 36, 40), (1.3 if j == 0 and i % 3 == 0 else 1.0)))
    t.zone("hollow", 16, 4, 4, 4)
    t.paint("hollow", lambda i, j, w, h, r: (70, 60, 56) if 1 <= i <= 2 and 1 <= j <= 2 else (218, 208, 182))
    t.zone("barb", 20, 4, 4, 2)
    t.paint("barb", lambda i, j, w, h, r: shade((184, 170, 140), r.uniform(0.92, 1.05)))
    save_tex(t, "mothquill")

    m = Model("mothquill", t)
    segs = [(3.5, 1.25, 0), (3.0, 1.0, 3), (2.5, 0.75, 4), (1.5, 0.5, 5)]
    x, deg = 2.5, 0
    m.box("Open", (2.0, 0, 7.25), (2.5, 1.5, 8.75), {"all": "shaft", "ends": "hollow"})
    for n, (l, w, d) in enumerate(segs):
        deg += d
        m.box(f"Shaft{n}", (x, (1.5 - w) / 2 * 0.5, 8 - w / 2), (x + l, (1.5 - w) / 2 * 0.5 + w, 8 + w / 2),
              {"all": ("shaft", x - 2, 0), "ends": "hollow"}, rot=(0, -deg, 0) if deg else None, origin=(2.5, 0, 8))
        x += l
    m.box("Tip", (x, 0.25, 7.8), (x + 1.75, 0.6, 8.2), "tip", rot=(0, -deg - 3, 0), origin=(2.5, 0, 8))
    for n, (bx, top, d) in enumerate(((4.0, 1.31, 0), (5.5, 1.31, 0), (7.0, 1.12, 3), (8.5, 1.12, 3), (10.0, 0.94, 7))):
        m.box(f"Barb{n}", (bx, top - 0.25, 7.75), (bx + 0.75, top + 0.25, 8.25), "barb", rot=(0, -d, 0) if d else None, origin=(2.5, 0, 8))
    finish("mothquill", m, {
        "guiTransform": gui(m.els, (150, -40, 0)),
        "tpHandTransform": held(m.els, "feather", 0.85),
        "groundTransform": ground(m.els, 0.42),
        "storage": storage(m.els, "Quadrants"),
    })


@item("spidersilk")
def spidersilk():
    """A skein of a Giant Spider's silk: grey-white strands wound into a long loose hank, doubled over, bound round
    the middle with a twist of darker silk, a loose end trailing; the strands catch the light in streaks."""
    t = Tex(1123)
    t.zone("silk", 0, 0, 32, 4)
    t.paint("silk", lambda i, j, w, h, r: shade((214, 216, 218), (1.14 if (i + 3 * j) % 7 == 0 else 0.9 if (i + j) % 5 == 0 else 1.0) * r.uniform(0.97, 1.03)))
    t.zone("tie", 0, 4, 8, 4)
    t.paint("tie", lambda i, j, w, h, r: shade((150, 152, 158), (0.8 if (i + j) % 2 == 0 else 1.0)))
    t.zone("end", 8, 4, 4, 4)
    t.paint("end", lambda i, j, w, h, r: shade((200, 202, 206), r.uniform(0.9, 1.05)))
    save_tex(t, "spidersilk")

    m = Model("spidersilk", t)
    hank = {"all": "silk", "ends": "end"}
    # the hank: two long bundles side by side, the loops round at each end, a second, thinner layer on top
    m.box("SideA", (4.0, 0, 6.25), (12.0, 1.0, 7.5), hank)
    m.box("SideB", (4.0, 0, 8.5), (12.0, 1.0, 9.75), hank)
    for n, x in enumerate((2.75, 12.25)):
        m.box(f"End{n}", (x, 0, 7.25), (x + 1.0, 0.9, 8.75), {"all": "silk", "ends": ("silk", 0, 0)})
    for n, (x, a) in enumerate(((3.25, 40), (3.25, -40), (11.75, -40), (11.75, 40))):
        z = 6.9 if a * (1 if x < 8 else -1) > 0 else 9.1
        m.box(f"Loop{n}", (x - 0.5, 0, z - 0.55), (x + 1.0, 0.9, z + 0.55), hank, rot=(0, a, 0), origin=(x + 0.25, 0, z))
    m.box("TopA", (5.0, 1.0, 6.75), (11.0, 1.6, 7.75), hank, rot=(0, 3, 0), origin=(8, 1, 7.25))
    m.box("TopB", (5.5, 1.0, 8.25), (10.5, 1.6, 9.25), hank, rot=(0, -4, 0), origin=(8, 1, 8.75))
    m.box("Tie", (7.25, -0.1, 6.0), (8.75, 1.9, 10.0), "tie")
    m.box("Loose", (8.75, 0, 10.0), (12.5, 0.5, 10.5), "silk", rot=(0, -20, 0), origin=(8.75, 0, 10.25))
    finish("spidersilk", m, {
        "guiTransform": gui(m.els, (150, -30, 0)),
        "tpHandTransform": held(m.els, "flaxfibers", 0.85),
        "groundTransform": ground(m.els, 0.4),
        "storage": storage(m.els, "Quadrants"),
    })


# ======================= Writing the item types =======================

def transforms_of(code):
    lk = LOOKS[code]
    return {k: lk[k] for k in ("guiTransform", "tpHandTransform", "groundTransform")}


def look(code, data, textures=None):
    """Gives an item type dict (a generator's, before it is written) its model: `texture` becomes `shape` (and
    `textures`, for variants), the three transforms are replaced where they stand, and
    attributes.groundStorageTransform is set. Keys keep their order, so the generators' files stay stable."""
    lk = LOOKS[code] if code in LOOKS else build(code)
    out = {}
    for k, v in data.items():
        if k in ("texture", "shape"):  # the flat item's texture, or the model a run before gave it
            out["shape"] = {"base": lk["shape"]}
            if textures:
                out["textures"] = textures
            continue
        if k in ("textures", "fpHandTransform"):
            continue
        if k in ("guiTransform", "tpHandTransform", "groundTransform"):
            out[k] = lk[k]
            continue
        out[k] = v
    for k in ("guiTransform", "tpHandTransform", "groundTransform"):
        out.setdefault(k, lk[k])
    if "shape" not in out:
        out["shape"] = {"base": lk["shape"]}
    attrs = dict(out.get("attributes") or {})
    attrs["groundStorageTransform"] = lk["storage"]
    out["attributes"] = attrs
    return out


def build(code):
    BUILDERS[code]()
    return LOOKS[code]


def j5(v):
    """A value as the hand-written JSON5 item types write it: { x: 1, y: 2 }."""
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k}: {j5(x)}" for k, x in v.items()) + " }"
    if isinstance(v, str):
        return json.dumps(v)
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return json.dumps(v)


def _span(text, start):
    """The end of the { ... } that opens at text[start]."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError("unbalanced braces")


def patch_json5(rel, code, textures=None):
    """A hand-written item type: replaces its one-line texture/shape/transform lines, keeps the rest."""
    path = os.path.join(ASSETS, "itemtypes", rel)
    text = open(path, encoding="utf-8").read()
    lk = LOOKS[code]
    lines = text.split("\n")
    keep, at = [], None
    for ln in lines:
        s = ln.strip()
        if re.match(r"(texture|shape|textures|guiTransform|fpHandTransform|tpHandTransform|groundTransform)\s*:", s):
            if at is None:
                at = len(keep)
            continue
        keep.append(ln)
    assert at is not None, rel
    ind = "\t"
    new = [f"{ind}shape: {j5({'base': lk['shape']})},"]
    if textures:
        new.append(f"{ind}textures: {j5(textures)},")
    tail = [f"{ind}guiTransform: {j5(lk['guiTransform'])},", f"{ind}tpHandTransform: {j5(lk['tpHandTransform'])},",
            f"{ind}groundTransform: {j5(lk['groundTransform'])}"]
    keep[at:at] = new
    # the transforms go last, before the closing brace
    close = max(i for i, ln in enumerate(keep) if ln.strip() == "}")
    if not keep[close - 1].rstrip().endswith(","):
        keep[close - 1] = keep[close - 1].rstrip() + ","
    keep[close:close] = tail
    text = "\n".join(keep)
    gst = "groundStorageTransform: " + j5(lk["storage"])
    m = re.search(r"groundStorageTransform\s*:\s*{", text)
    if m:
        end = _span(text, m.end() - 1)
        text = text[:m.start()] + gst + text[end:]
    else:
        m = re.search(r"\n(\s*)attributes\s*:\s*{", text)
        if m:
            text = text[:m.end()] + " " + gst + "," + text[m.end():]
        else:
            m = re.search(r"\n(\s*)creativeinventory\s*:[^\n]*\n", text)
            text = text[:m.end()] + f"{ind}attributes: {{ {gst} }},\n" + text[m.end():]
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(text)


def patch_generated(rel, code, textures=None):
    """A generated item type (a // comment line, then json.dumps with tabs): given its look as its generator now
    gives it, so the file is what a re-run of that generator writes."""
    path = os.path.join(ASSETS, "itemtypes", rel)
    text = open(path, encoding="utf-8").read()
    first, body = text.split("\n", 1)
    assert first.startswith("//"), rel
    data = look(code, json.loads(body), textures)
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(first + NL + json.dumps(data, indent="\t", ensure_ascii=False) + NL)


# Where each item type lives and who writes it
TYPES = {
    "carpetfibre": ("salvage/carpetfibre.json", "json5"),
    "carpetsquare": ("salvage/carpetsquare.json", "gen_breakdown"),
    "wallpaperstrip": ("salvage/wallpaperstrip.json", "json5"),
    "glassshard": ("salvage/glassshard.json", "json5"),
    "glassshiv": ("salvage/glassshiv.json", "json5"),
    "scraper": ("salvage/scraper.json", "json5"),
    "metalbracket": ("salvage/metalbracket.json", "json5"),
    "scrapwire": ("salvage/scrapwire.json", "json5"),
    "rubble": ("salvage/rubble.json", "gen_breakdown"),
    "ceramicgrit": ("salvage/ceramicgrit.json", "json5"),
    "potshard": ("salvage/potshard.json", "json5"),
    "rottenwood": ("salvage/rottenwood.json", "json5"),
    "prybar": ("prybar.json", "gen_loop"),
    "seedpacket": ("seedpacket.json", "gen_loop"),
    "clumpsinew": ("clumpsinew.json", "gen_materials"),
    "mothjelly": ("mothjelly.json", "gen_materials"),
    "mothquill": ("mothquill.json", "gen_materials"),
    "spidersilk": ("spidersilk.json", "gen_materials"),
}
VARIANT_TEXTURES = {"seedpacket": {"packet": {"base": f"{TEXDIR}/seedpacket-{{crop}}"}}}


def main(codes):
    for code in codes:
        build(code)
        rel, kind = TYPES[code]
        if kind == "json5":
            patch_json5(rel, code, VARIANT_TEXTURES.get(code))
        else:
            patch_generated(rel, code, VARIANT_TEXTURES.get(code))
        print(code, LOOKS[code]["shape"], sum(1 for _ in _walk(json.load(open(os.path.join(ASSETS, "shapes", LOOKS[code]["shape"] + ".json")))["elements"])), "elements")


def _walk(els):
    for e in els:
        yield e
        yield from _walk(e.get("children") or [])


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args or [c for c in TYPES if c in BUILDERS])
