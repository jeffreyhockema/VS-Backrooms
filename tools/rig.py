"""A small rigging kit for entity models: parts are boxes in model space, the texture atlas is unwrapped and painted
automatically, and animations are lists of keyframes per part, written out as a Vintage Story shape.

Conventions (as vanilla's animals): a model faces -X (west), its left side is +Z (south), up is +Y. Coordinates are in
model pixels (16 to a block) with the entity's feet at (0, 0, 0); they are moved to the middle of the block on
export. A part's position and pivot are given in model space as if every parent were unrotated (which is how the
game stores them: relative to the parent's corner), and its rest rotation turns it and everything below it.

    model = Model("hound")
    body = model.part("Body", (-7, 10, -3.5), (14, 5, 7), pivot=(0, 12, 0), paint=skin)
    model.part("Head", (-12, 9, -2.5), (5, 5, 5), pivot=(-7, 11, 0), parent=body, paint=head)
    model.animation("walk", 30, keys={0: {"LegL": rot(z=20)}, 15: {"LegL": rot(z=-20)}, 30: {"LegL": rot(z=20)}})
    model.save()   # writes shapes/entity/hound.json and textures/entity/hound.png

A painter is called once per face as paint(ctx), with ctx.img/ctx.draw (the atlas), ctx.x, ctx.y, ctx.w, ctx.h (the
face's rectangle in texture pixels), ctx.face ("north", "east", "south", "west", "up", "down"), ctx.part and ctx.rng.
For side faces, v runs down the face; the front of a model is its "west" face.
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
FACES = ("north", "east", "south", "west", "up", "down")

# Texture pixels per model pixel
TEXEL = 2


def rot(x=0.0, y=0.0, z=0.0):
    return {"rot": (x, y, z)}


def off(x=0.0, y=0.0, z=0.0):
    return {"off": (x, y, z)}


def pose(r=(0, 0, 0), o=(0, 0, 0), s=None):
    p = {"rot": tuple(r), "off": tuple(o)}
    if s is not None:
        p["str"] = tuple(s)
    return p


class Part:
    def __init__(self, model, name, frm, size, pivot, parent, rest, paint, faces, glow, tag):
        self.model, self.name = model, name
        self.frm = [float(v) for v in frm]
        self.size = [float(v) for v in size]
        self.pivot = [float(v) for v in (pivot if pivot is not None else [frm[i] + size[i] / 2 for i in range(3)])]
        self.parent = parent
        self.rest = tuple(rest)
        self.paint = paint
        self.faces = faces or FACES
        self.glow = glow
        self.tag = tag or {}
        self.children = []
        self.uv = {}

    @property
    def to(self):
        return [self.frm[i] + self.size[i] for i in range(3)]

    def face_size(self, face):
        sx, sy, sz = self.size
        return {"north": (sx, sy), "south": (sx, sy), "east": (sz, sy), "west": (sz, sy), "up": (sx, sz), "down": (sx, sz)}[face]


class Ctx:
    pass


class Model:
    def __init__(self, name, atlas_width=64, seed=1):
        self.name = name
        self.parts = []
        self.by_name = {}
        self.animations = []
        self.atlas_width = atlas_width
        self.seed = seed

    def part(self, name, frm, size, pivot=None, parent=None, rest=(0, 0, 0), paint=None, faces=None, glow=0, tag=None):
        assert name not in self.by_name, name
        p = Part(self, name, frm, size, pivot, self.by_name[parent] if isinstance(parent, str) else parent, rest, paint, faces, glow, tag)
        self.parts.append(p)
        self.by_name[name] = p
        if p.parent is not None:
            p.parent.children.append(p)
        return p

    def mirror(self, name, new_name, parent=None):
        """A copy of a part (and its children) mirrored left to right (z to -z)."""
        src = self.by_name[name]

        def copy(p, parent_part, rename):
            frm = (p.frm[0], p.frm[1], -p.to[2])
            pivot = (p.pivot[0], p.pivot[1], -p.pivot[2])
            rest = (-p.rest[0], -p.rest[1], p.rest[2])
            q = self.part(rename(p.name), frm, p.size, pivot, parent_part, rest, p.paint, p.faces, p.glow, dict(p.tag))
            for c in p.children:
                copy(c, q, rename)
            return q

        def rename(n):
            for a, b in (("L", "R"), ("Left", "Right")):
                if n.endswith(a):
                    return n[: -len(a)] + b
            return n + "M"

        return copy(src, self.by_name[parent] if isinstance(parent, str) else (parent or src.parent), lambda n: new_name if n == src.name else rename(n))

    def shift(self, dx=0.0, dy=0.0, dz=0.0):
        """Moves the whole model (every part and pivot), e.g. to centre a long body on the entity's position."""
        for p in self.parts:
            p.frm = [p.frm[0] + dx, p.frm[1] + dy, p.frm[2] + dz]
            p.pivot = [p.pivot[0] + dx, p.pivot[1] + dy, p.pivot[2] + dz]

    def animation(self, code, frames, keys, end="Repeat", stopped="EaseOut"):
        """keys: {frame: {part name: pose dict}}; frame == frames is folded onto frame 0 for looping animations."""
        self.animations.append((code, frames, keys, end, stopped))

    # ---------------- Export ----------------

    def _pack(self):
        rects = []
        for p in self.parts:
            for f in p.faces:
                w, h = p.face_size(f)
                pw, ph = max(1, math.ceil(w * TEXEL - 1e-6)), max(1, math.ceil(h * TEXEL - 1e-6))
                rects.append((ph, pw, p, f))
        rects.sort(key=lambda r: (-r[0], -r[1]))
        width = self.atlas_width * TEXEL
        x = y = shelf = 0
        for ph, pw, p, f in rects:
            if x + pw + 1 > width:
                x, y, shelf = 0, y + shelf + 1, 0
            p.uv[f] = (x, y, pw, ph)
            x += pw + 1
            shelf = max(shelf, ph)
        height = y + shelf + 1
        # Texture sizes in powers of two keep mipmaps happy
        h2 = 1
        while h2 < height:
            h2 *= 2
        return width, h2

    def _paint(self, width, height):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for i, p in enumerate(self.parts):
            for f in p.faces:
                x, y, w, h = p.uv[f]
                ctx = Ctx()
                ctx.img, ctx.draw, ctx.x, ctx.y, ctx.w, ctx.h, ctx.face, ctx.part = img, draw, x, y, w, h, f, p
                ctx.rng = random.Random(self.seed * 1000003 + i * 101 + FACES.index(f))
                if p.paint:
                    p.paint(ctx)
                else:
                    draw.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 0, 255, 255))
        return img

    def _element(self, p, width, height):
        parent_from = p.parent.frm if p.parent else [-8.0, 0.0, -8.0]
        el = {
            "name": p.name,
            "from": [round(p.frm[i] - parent_from[i], 4) for i in range(3)],
            "to": [round(p.to[i] - parent_from[i], 4) for i in range(3)],
            "rotationOrigin": [round(p.pivot[i] - parent_from[i], 4) for i in range(3)],
        }
        for axis, v in zip("XYZ", p.rest):
            if v:
                el["rotation" + axis] = v
        faces = {}
        for f in FACES:
            if f not in p.faces:
                continue
            x, y, w, h = p.uv[f]
            face = {"texture": "#skin", "uv": [x / TEXEL, y / TEXEL, (x + w) / TEXEL, (y + h) / TEXEL]}
            if p.glow:
                face["glow"] = p.glow
            faces[f] = face
        el["faces"] = faces
        if p.parent is None and p is self.parts[0]:
            # FloatUpWhenStuck (and the game's warning) want a Center point: the middle of the root part
            el["attachmentpoints"] = [{"code": "Center", "posX": round(p.size[0] / 2, 4), "posY": round(p.size[1] / 2, 4), "posZ": round(p.size[2] / 2, 4),
                                       "rotationX": 0, "rotationY": 0, "rotationZ": 0}]
        if p.children:
            el["children"] = [self._element(c, width, height) for c in p.children]
        return el

    def _animations(self):
        out = []
        for code, frames, keys, end, stopped in self.animations:
            keys = dict(keys)
            if end == "Repeat" and frames in keys:
                keys.pop(frames)  # the loop closes on frame 0
            animated = sorted({name for k in keys.values() for name in k})
            stretched = {name for k in keys.values() for name, ps in k.items() if "str" in ps}
            kfs = []
            for frame in sorted(keys):
                elements = {}
                for name in animated:
                    assert name in self.by_name, (code, name)
                    ps = keys[frame].get(name, {})
                    r, o = ps.get("rot", (0, 0, 0)), ps.get("off", (0, 0, 0))
                    e = {"offsetX": o[0], "offsetY": o[1], "offsetZ": o[2], "rotationX": r[0], "rotationY": r[1], "rotationZ": r[2]}
                    if name in stretched:
                        s = ps.get("str", (1, 1, 1))
                        e.update({"stretchX": s[0], "stretchY": s[1], "stretchZ": s[2]})
                    elements[name] = {k: round(v, 3) for k, v in e.items()}
                kfs.append({"frame": frame, "elements": elements})
            out.append({"name": code, "code": code, "quantityframes": frames, "onActivityStopped": stopped, "onAnimationEnd": end, "keyframes": kfs})
        return out

    def shape(self):
        width, height = self._pack()
        roots = [p for p in self.parts if p.parent is None]
        return {
            "editor": {"allAngles": True, "entityTextureMode": True},
            "textureWidth": width // TEXEL,
            "textureHeight": height // TEXEL,
            "textures": {"skin": f"backrooms:entity/{self.name}"},
            "elements": [self._element(p, width, height) for p in roots],
            "animations": self._animations(),
        }, (width, height)

    def save(self):
        shape, (width, height) = self.shape()
        img = self._paint(width, height)
        tex = os.path.join(ASSETS, "textures", "entity", self.name + ".png")
        os.makedirs(os.path.dirname(tex), exist_ok=True)
        img.save(tex)
        path = os.path.join(ASSETS, "shapes", "entity", self.name + ".json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(shape, indent="\t") + "\n")
        print(f"wrote {self.name}: {len(self.parts)} parts, {len(self.animations)} animations, texture {width}x{height}")
        return shape


# ---------------- Painting helpers ----------------

def clamp(c):
    return tuple(max(0, min(255, int(v))) for v in c)


def shade(c, k):
    return clamp((c[0] * k, c[1] * k, c[2] * k))


def mix(a, b, t):
    return clamp(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def fill(ctx, base, var=0.08, face_shade=True):
    """The face filled with a colour, mottled a little, and darker underneath (as if lit from above)."""
    k = {"up": 1.08, "down": 0.72, "north": 0.94, "south": 0.94, "east": 0.88, "west": 1.0}[ctx.face] if face_shade else 1.0
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            m = 1 + var * (ctx.rng.random() - 0.5) * 2
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(v * k * m for v in base)) + (255,)


def speckle(ctx, colour, chance, size=1):
    px = ctx.img.load()
    for yy in range(0, ctx.h, size):
        for xx in range(0, ctx.w, size):
            if ctx.rng.random() < chance:
                for dy in range(size):
                    for dx in range(size):
                        if xx + dx < ctx.w and yy + dy < ctx.h:
                            px[ctx.x + xx + dx, ctx.y + yy + dy] = clamp(colour) + (255,)


def hlines(ctx, colour, every, start=0, alpha=1.0):
    """Horizontal lines down a side face (ribs, creases)."""
    px = ctx.img.load()
    for yy in range(start, ctx.h, every):
        for xx in range(ctx.w):
            old = px[ctx.x + xx, ctx.y + yy]
            px[ctx.x + xx, ctx.y + yy] = mix(old[:3], colour, alpha) + (255,)


def vlines(ctx, colour, every, start=0, alpha=1.0, jitter=0):
    px = ctx.img.load()
    for xx in range(start, ctx.w, every):
        for yy in range(ctx.h):
            x2 = min(ctx.w - 1, max(0, xx + (ctx.rng.randint(-jitter, jitter) if jitter else 0)))
            old = px[ctx.x + x2, ctx.y + yy]
            px[ctx.x + x2, ctx.y + yy] = mix(old[:3], colour, alpha) + (255,)


def rect(ctx, u0, v0, u1, v1, colour):
    """A rectangle in face-relative fractions (0..1 across, 0..1 down)."""
    x0, y0 = ctx.x + int(round(u0 * ctx.w)), ctx.y + int(round(v0 * ctx.h))
    x1, y1 = ctx.x + max(int(round(u1 * ctx.w)) - 1, int(round(u0 * ctx.w))), ctx.y + max(int(round(v1 * ctx.h)) - 1, int(round(v0 * ctx.h)))
    ctx.draw.rectangle([x0, y0, x1, y1], fill=clamp(colour) + (255,))


def gradient_down(ctx, top, bottom):
    """A side face shading from one colour at the top to another at the bottom."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        c = mix(top, bottom, yy / max(1, ctx.h - 1))
        for xx in range(ctx.w):
            px[ctx.x + xx, ctx.y + yy] = c + (255,)
