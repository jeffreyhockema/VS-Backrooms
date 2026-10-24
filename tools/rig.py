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
        self.faces = FACES if faces is None else tuple(faces)   # () makes a bone with nothing drawn
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
        # The graphics pass's light bake (B17): None paints as before; a dict (empty for the defaults, see LIGHT) bakes
        # light from above, contact occlusion and dark feet into the painted atlas (`bake`). Set it before saving.
        self.light = None

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
                ctx.baked = self.light is not None
                if p.paint:
                    p.paint(ctx)
                else:
                    draw.rectangle([x, y, x + w - 1, y + h - 1], fill=(255, 0, 255, 255))
        if self.light is not None:
            bake(self, img, **self.light)
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


def _lattice(rng, w, h, cell):
    gw, gh = w // cell + 2, h // cell + 2
    return [[rng.uniform(-1, 1) for _ in range(gw)] for _ in range(gh)]


def _sample(lat, xx, yy, cell):
    fx, fy = xx / cell, yy / cell
    i, j = int(fx), int(fy)
    tx, ty = fx - i, fy - j
    a = lat[j][i] + (lat[j][i + 1] - lat[j][i]) * tx
    b = lat[j + 1][i] + (lat[j + 1][i + 1] - lat[j + 1][i]) * tx
    return a + (b - a) * ty


def shade_fill(ctx, base, var=0.04, face_shade=True, light=0.12, dark=0.16, ao=0.2, ao_px=2, mottle=0.06,
               drift=0.18, cap=6.0, hue=0.025, cell=4):
    """The graphics pass's shaded fill (opt in: `fill` is unchanged). Like fill, but each face is lit as a lump in
    light from above: a side face runs from lighter at the top to darker at the bottom, with a 1 px lit top edge and
    a darker bottom edge, and darkens toward its foot over `ao_px` texture px (and toward its flanks too when the face
    is narrow, so a limb reads round; B2 darkened every edge of every face, which drew a rim round large faces); a
    soft mottle (`mottle`) replaces most of the per-pixel speckle (`var`); the hue wanders a little apart from the
    value (`hue`), and lit pixels drift warm, shaded ones cool (`drift` per level, at most `cap` levels), as matlib's
    surfaces do. On a model with a light bake (`Model.light`, B17) the gradient, edges and occlusion are left to the
    bake, which knows where the part is and what touches it; the fill then paints only the mottled, hued base."""
    k = {"up": 1.08, "down": 0.72, "north": 0.94, "south": 0.94, "east": 0.88, "west": 1.0}[ctx.face] if face_shade else 1.0
    side = ctx.face not in ("up", "down")
    baked = getattr(ctx, "baked", False)
    w, h = ctx.w, ctx.h
    lat = _lattice(ctx.rng, w, h, cell)
    fine = _lattice(ctx.rng, w, h, max(1, cell // 2))
    hlat = _lattice(ctx.rng, w, h, cell * 2)
    lum = 0.299 * base[0] + 0.587 * base[1] + 0.114 * base[2]
    narrow = w <= 4 * ao_px + 1
    px = ctx.img.load()
    for yy in range(h):
        for xx in range(w):
            mot = 0.7 * _sample(lat, xx, yy, cell) + 0.4 * _sample(fine, xx, yy, max(1, cell // 2))
            m = k * (1 + mottle * mot + var * (ctx.rng.random() - 0.5) * 2)
            if side and h > 1 and not baked:
                t = yy / (h - 1)
                m *= 1 + light * (1 - t) * 0.6 - dark * t * 0.6
                if yy == 0:
                    m *= 1 + light
                elif yy == h - 1:
                    m *= 1 - dark
            if side and not baked and h > 2 * ao_px:
                occ = max(0.0, 1 - (h - 1 - yy) / ao_px)
                if narrow:
                    occ = max(occ, 0.45 * max(0.0, 1 - xx / ao_px), 0.45 * max(0.0, 1 - (w - 1 - xx) / ao_px))
                m *= 1 - ao * occ
            hv = hue * _sample(hlat, xx, yy, cell * 2)
            c = [base[0] * m * (1 + hv), base[1] * m, base[2] * m * (1 - hv)]
            dlt = max(-cap, min(cap, (m / k - 1) * lum * drift))     # about the face's own level, not its face shade
            c = (c[0] + dlt, c[1] + dlt * 0.3, c[2] - dlt)
            px[ctx.x + xx, ctx.y + yy] = clamp(c) + (255,)


def lit_fill(ctx, base, var=0.08, face_shade=True):
    """`fill`'s arguments, painted by `shade_fill` on a model with a light bake (the per-pixel speckle mostly turned
    into a soft mottle and a little hue), and by `fill` itself on any other model, which then paints as it did."""
    if not getattr(ctx, "baked", False):
        return fill(ctx, base, var, face_shade)
    shade_fill(ctx, base, var=var * 0.45, face_shade=face_shade, mottle=0.03 + var * 0.6, hue=0.02 + var * 0.1)



# ---------------- Surface detail (B17) ----------------
# Painted over a base (fill, shade_fill), at the model's texel density; each works in place on the face's pixels.

def _scale_px(px, x, y, k, lift=(0, 0, 0)):
    c = px[x, y]
    if len(c) == 4 and c[3] == 0:
        return
    px[x, y] = clamp((c[0] * k + lift[0], c[1] * k + lift[1], c[2] * k + lift[2])) + ((c[3],) if len(c) == 4 else ())


def strands(ctx, base, hi=None, sheen=0.5, spread=0.3, parting=0.22, grey=None, grey_chance=0.0, along="v",
            sheen_at=0.25, dirt=None, dirt_chance=0.0):
    """Hair as strands: each column (along v; rows with along="u") is a strand of its own tone, between `base` and
    the highlight `hi` (by `spread`), that wanders a texel now and then; dark partings between some; a lit band where
    the hair turns toward the light (toward `hi` by `sheen`, at `sheen_at` down the face); a few `grey` strands.
    Paints the whole face (call before cutting ragged ends). Works on near-black hair, as the lift is toward `hi`."""
    px = ctx.img.load()
    hi = hi if hi is not None else clamp(tuple(v * 1.6 + 12 for v in base))
    n_across, n_along = (ctx.w, ctx.h) if along == "v" else (ctx.h, ctx.w)
    tones = []
    prev = ctx.rng.random()
    for i in range(n_across + 2):
        r = ctx.rng.random()
        if r < parting and (not tones or tones[-1][0] != "dark"):
            tones.append(("dark", -0.3 - 0.15 * ctx.rng.random()))
        elif grey is not None and r < parting + grey_chance:
            tones.append(("grey", 0.0))
        else:
            cur = 0.5 * (prev + ctx.rng.random())          # neighbouring strands of a like tone: locks, not a checker
            tones.append(("hair", spread * cur))
            prev = cur
    phase = ctx.rng.random() * 6.28
    for a in range(n_along):
        t = (a + 0.5) / n_along
        lit = sheen * max(0.0, 1 - abs(t - sheen_at) / 0.18)
        wob = int(round(0.7 * math.sin(a * 0.22 + phase)))
        for c in range(n_across):
            kind, tone = tones[max(0, min(n_across + 1, c + 1 + wob))]
            if kind == "grey":
                colour = mix(grey, hi, lit * 0.5)
            elif kind == "dark":
                colour = shade(mix(base, hi, lit * 0.25), 1 + tone)
            else:
                colour = mix(base, hi, min(1.0, tone + lit + 0.06 * ctx.rng.random()))
            colour = shade(colour, 1 - 0.1 * t)
            if dirt is not None and ctx.rng.random() < dirt_chance:
                colour = mix(colour, dirt, 0.5)
            xx, yy = (c, a) if along == "v" else (a, c)
            px[ctx.x + xx, ctx.y + yy] = colour + (255,)


def fur(ctx, direction=(1.0, 0.0), length=3, density=0.4, tip=1.2, root=0.82):
    """Fur laid in one direction (in face texels: (1, 0) runs toward +u, (0, 1) down the face): short strokes over
    the painted base, dark at the root and light at the tip, so the coat reads combed rather than speckled."""
    px = ctx.img.load()
    dx, dy = direction
    ln = math.hypot(dx, dy) or 1.0
    dx, dy = dx / ln, dy / ln
    count = int(ctx.w * ctx.h * density / max(1, length))
    for _ in range(count):
        x0, y0 = ctx.rng.uniform(-1, ctx.w), ctx.rng.uniform(-1, ctx.h)
        L = length + ctx.rng.choice((-1, 0, 0, 1))
        for i in range(max(1, L)):
            xx, yy = int(x0 + dx * i), int(y0 + dy * i)
            if 0 <= xx < ctx.w and 0 <= yy < ctx.h:
                k = root + (tip - root) * (i / max(1, L - 1))
                _scale_px(px, ctx.x + xx, ctx.y + yy, k)


def folds(ctx, rows, depth=0.72, light=1.12, wobble=0.5, axis="h"):
    """Creases across a face (skin bunched at a wrist, a neck, a waist): at each fraction in `rows` a dark crease
    texel row, and the skin just below it lit (it bulges toward the light). The line wanders by `wobble` texels."""
    px = ctx.img.load()
    n_across, n_along = (ctx.w, ctx.h) if axis == "h" else (ctx.h, ctx.w)
    for v in rows:
        base = v * n_along
        phase = ctx.rng.random() * 6.28
        for c in range(n_across):
            a = int(round(base + wobble * math.sin(c * 0.7 + phase)))
            for off, k in ((0, depth), (1, light), (-1, 1 + (depth - 1) * 0.35)):
                aa = a + off
                if 0 <= aa < n_along:
                    xx, yy = (c, aa) if axis == "h" else (aa, c)
                    _scale_px(px, ctx.x + xx, ctx.y + yy, k)


def weave(ctx, amount=5.0, kind="plain", slubs=0.04):
    """Cloth weave at one texel: plain (a checker of threads), twill (a diagonal), or knit (columns of vees); a few
    slubs (short thicker threads) along the weft. `amount` in levels at a mid tone, less on dark cloth (a weave on
    black reads as a grey checker); meant to read up close, not as a pattern."""
    px = ctx.img.load()
    mid = px[ctx.x + ctx.w // 2, ctx.y + ctx.h // 2]
    amount *= max(0.5, min(1.0, (0.299 * mid[0] + 0.587 * mid[1] + 0.114 * mid[2]) / 110.0))
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            if kind == "twill":
                on = ((xx + yy) % 4) < 2
            elif kind == "knit":
                on = ((xx % 2) == 0) ^ ((yy // 1 + (xx // 2)) % 2 == 0)
            else:
                on = (xx + yy) % 2 == 0
            d = amount if on else -amount
            c = px[ctx.x + xx, ctx.y + yy]
            if c[3] == 0:
                continue
            px[ctx.x + xx, ctx.y + yy] = clamp((c[0] + d, c[1] + d, c[2] + d)) + (c[3],)
    for _ in range(int(ctx.w * ctx.h * slubs / 3)):
        x0, y0 = ctx.rng.randrange(max(1, ctx.w)), ctx.rng.randrange(max(1, ctx.h))
        d = amount * 1.6 * (1 if ctx.rng.random() < 0.5 else -1)
        for i in range(ctx.rng.randint(2, 4)):
            if x0 + i < ctx.w:
                c = px[ctx.x + x0 + i, ctx.y + y0]
                if c[3]:
                    px[ctx.x + x0 + i, ctx.y + y0] = clamp((c[0] + d, c[1] + d, c[2] + d)) + (c[3],)


def plates(ctx, n, axis="u", seam=0.6, lit=1.16, swell=0.1, reverse=False):
    """Overlapping plates (chitin segments, scutes): the face cut into `n` bands along `axis`; each band lit along its
    leading edge, rounding off to a dark seam where the next one overlaps it."""
    px = ctx.img.load()
    length = ctx.w if axis == "u" else ctx.h
    for i in range(length):
        f = (i + 0.5) / length * n
        t = f - int(f)
        if reverse:
            t = 1 - t
        k = 1 + swell * (0.5 - abs(t - 0.4)) * 2
        if t < 1.0 / max(2, length / n):
            k *= lit
        elif t > 1 - 1.0 / max(2, length / n):
            k *= seam
        for j in range(ctx.h if axis == "u" else ctx.w):
            xx, yy = (i, j) if axis == "u" else (j, i)
            _scale_px(px, ctx.x + xx, ctx.y + yy, k)


# ---------------- The light bake (B17) ----------------

# grad: brightness across a part's height (+-grad/2, lit at the top); edge / foot: the 1 px row along a side face's
# top edge lifted, along its bottom edge darkened; round: side faces darken toward their upright edges (a quadratic
# across the face), so a box limb reads round, in full on parts up to `round_px` model px across and less on wider
# ones; ao: darkening where another part is within `reach` model px of the surface (sampled along the normal and four
# tilted rays), so joints, armpits and the skin under hair and clothes go dark while free edges stay clean (B2's
# shade_fill darkened every edge of every face instead, which drew a rim round large faces); ground / ground_h:
# darker toward the floor (feet, the low belly); drift / cap: lit pixels warm, shaded ones cool, as matlib's surfaces;
# floor: levels of light added as if the colour were that much brighter (a near-black creature takes no shape from a
# multiplied light alone); skip: painters whose faces are left as painted (teeth, eyes). Glowing parts are always left
# as painted.
# A part's tag "bake" (0..1) scales all of it for that part; tag "occlude": False keeps a part from shading others.
LIGHT = dict(grad=0.26, edge=0.11, foot=0.06, ao=0.45, reach=(0.6, 1.4, 2.6), ground=0.18, ground_h=5.0, drift=0.18,
             cap=6.0, round=0.16, round_px=5.0, floor=0.0, skip=())

_NORMALS = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
# corners per face in the order of the uv corners (0,1), (1,1), (1,0), (0,0), as the game (and entrender) lays them
_CORNERS = {
    "north": [(1, 0, 0), (0, 0, 0), (0, 1, 0), (1, 1, 0)],
    "south": [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
    "west": [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)],
    "east": [(1, 0, 1), (1, 0, 0), (1, 1, 0), (1, 1, 1)],
    "up": [(0, 1, 1), (1, 1, 1), (1, 1, 0), (0, 1, 0)],
    "down": [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],
}


def _rot3(rx, ry, rz):
    import numpy as np

    def m(axis, a):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        if axis == 0:
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        if axis == 1:
            return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

    return m(0, rx) @ m(1, ry) @ m(2, rz)


def _element_matrix(base, parent_from, frm, pivot, rest):
    """The game's element transform: translate to the pivot, rotate X Y Z, translate back; `frm` and `pivot` relative
    to the parent's corner (`parent_from`), all in model px. Returns the 4x4 from the box's own coordinates."""
    import numpy as np

    def tr(v):
        t = np.eye(4)
        t[:3, 3] = v
        return t

    r = np.eye(4)
    r[:3, :3] = _rot3(*rest)
    return base @ tr(np.array(pivot) - np.array(parent_from)) @ r @ tr(np.array(frm) - np.array(pivot))


def part_matrices(model):
    """Each rig part's rest transform: a 4x4 taking the part's own box coordinates (0..size) to model space (model
    px, feet at y = 0)."""
    import numpy as np
    out = {}
    for p in model.parts:   # parents are always made before their children
        base = out[id(p.parent)] if p.parent is not None else np.eye(4)
        pf = p.parent.frm if p.parent is not None else (0.0, 0.0, 0.0)
        out[id(p)] = _element_matrix(base, pf, p.frm, p.pivot, p.rest)
    return out


def posed_matrices(model, keyframe):
    """Each part's transform in a keyframe pose ({part name: pose dict}, as given to Model.animation): the rest
    transform with the pose's rotation added to the rest rotation, its stretch, and its offset applied inside the
    rotation, as the game composes an animated element (ShapeElement.GetLocalTransformMatrix)."""
    import numpy as np
    out = {}
    for p in model.parts:
        ps = keyframe.get(p.name, {})
        r, o, s = ps.get("rot", (0, 0, 0)), ps.get("off", (0, 0, 0)), ps.get("str", (1, 1, 1))
        base = out[id(p.parent)] if p.parent is not None else np.eye(4)
        pf = p.parent.frm if p.parent is not None else (0.0, 0.0, 0.0)
        rot = np.eye(4)
        rot[:3, :3] = _rot3(*(p.rest[i] + r[i] for i in range(3)))
        out[id(p)] = base @ _shift(np.array(p.pivot) - np.array(pf)) @ rot @ np.diag([s[0], s[1], s[2], 1.0]) \
            @ _shift(np.array(p.frm) + np.array(o) - np.array(p.pivot))
    return out


def posed_extent(model, keyframe, ignore=()):
    """(lowest, highest) y of every drawn box in a keyframe pose, in model px (the floor is y = 0), leaving out the
    parts named in `ignore` (soft things such as hair, which bend where they meet the floor)."""
    import numpy as np
    mats = posed_matrices(model, keyframe)
    ys = []
    for p in model.parts:
        if not p.faces or p.name in ignore:
            continue
        c = np.array([[x * p.size[0], y * p.size[1], z * p.size[2], 1] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
        ys.extend((mats[id(p)] @ c.T)[1])
    return min(ys), max(ys)


def settle(model, keyframe, floor=0.0, ignore=()):
    """A death pose's last step: moves the root part(s) straight down (or up) in the world so the lowest drawn box
    rests at `floor` px (0 is the floor; a little below, -0.3 or so, presses the body into it instead of hovering).
    The root's offset is in its own rotated frame, so the world move is turned back through the root's rotation.
    Parts named in `ignore` do not hold the body up. Returns the keyframe (changed in place)."""
    import numpy as np
    low, _ = posed_extent(model, keyframe, ignore)
    drop = low - floor
    for p in model.parts:
        if p.parent is not None:
            continue
        ps = dict(keyframe.get(p.name, {}))
        r = ps.get("rot", (0, 0, 0))
        local = _rot3(*(p.rest[i] + r[i] for i in range(3))).T @ np.array([0.0, -drop, 0.0])
        o = ps.get("off", (0, 0, 0))
        ps["rot"] = tuple(r)
        ps["off"] = tuple(round(float(o[i] + local[i]), 3) for i in range(3))
        keyframe[p.name] = ps
    return keyframe


class _Box:
    """One box to bake: its transform, size, faces as atlas rectangles, and how it takes part."""

    def __init__(self, key, M, size, faces, strength=1.0, occlude=True, paint=True):
        self.key, self.M, self.size, self.faces = key, M, size, faces
        self.strength, self.occlude, self.paint = strength, occlude, paint


def bake(model, img, **opts):
    """Bakes light into a rig model's painted atlas from its rest pose (see LIGHT for the knobs). Every face's texels
    are placed in model space; each is lifted or darkened by where it is on its part, how near the floor it is, and
    how much of the space just off the surface is inside another part. Faces of glowing parts are left alone."""
    mats = part_matrices(model)
    skip = set(opts.get("skip", ()))
    boxes = []
    for p in model.parts:
        faces = [(f,) + tuple(p.uv[f]) + (False, False, 0) for f in p.faces]
        strength = 0.0 if (p.glow or p.paint in skip) else float(p.tag.get("bake", 1.0))
        boxes.append(_Box(p.name, mats[id(p)], [float(v) for v in p.size], faces, strength,
                          occlude=bool(p.tag.get("occlude", True)) and not p.glow))
    _bake_boxes(boxes, img, opts)


def bake_shape(shape, img, scale, skip=(), strengths=None, **opts):
    """The same bake for a JSON shape (the Facelings' seraph): elements with from/to/rotationOrigin relative to their
    parent's corner; faces whose texture rectangle is uv * `scale` (honouring flipped uvs and 90-degree face rotations).
    Elements named in `skip` are not baked; `strengths` maps names to a bake strength. An element with no opaque texel
    on any face (an attachment the look does not wear) neither takes light nor shades anything."""
    import numpy as np
    arr = np.asarray(img)
    boxes = []

    def walk(els, base, parent_from):
        for e in els:
            frm, to = e["from"], e["to"]
            M = _element_matrix(base, parent_from, frm, e.get("rotationOrigin", frm),
                                (e.get("rotationX", 0), e.get("rotationY", 0), e.get("rotationZ", 0)))
            faces, opaque = [], False
            for f, fc in (e.get("faces") or {}).items():
                if not fc or fc.get("enabled") is False or "uv" not in fc or fc.get("texture") in ("#null", None):
                    continue
                u1, v1, u2, v2 = fc["uv"]
                x0, x1 = sorted((int(round(u1 * scale)), int(round(u2 * scale))))
                y0, y1 = sorted((int(round(v1 * scale)), int(round(v2 * scale))))
                if x1 <= x0 or y1 <= y0:
                    continue
                faces.append((f, x0, y0, x1 - x0, y1 - y0, u2 < u1, v2 < v1, int(fc.get("rotation", 0)) % 360))
                opaque = opaque or bool((arr[y0:y1, x0:x1, 3] > 0).any())
            size = [abs(to[i] - frm[i]) for i in range(3)]
            name = e.get("name", "")
            st = 0.0 if name in skip else float((strengths or {}).get(name, 1.0))
            if faces and opaque:
                boxes.append(_Box(name, M, size, faces, st, occlude=min(size) > 0.05))
            # children are placed relative to this element's corner, in its rotated frame
            walk(e.get("children") or [], M @ _shift(frm), frm)

    walk(shape["elements"], _shift((-8.0, 0.0, -8.0)), (0.0, 0.0, 0.0))
    _bake_boxes(boxes, img, opts)


def _shift(v):
    import numpy as np
    t = np.eye(4)
    t[:3, 3] = v
    return t


def _bake_boxes(boxes, img, opts):
    import numpy as np
    o = dict(LIGHT)
    o.update(opts)
    inv = [np.linalg.inv(b.M) for b in boxes]
    lo_hi = []
    for b in boxes:
        c = np.array([[x * b.size[0], y * b.size[1], z * b.size[2], 1] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
        wc = (b.M @ c.T).T[:, :3]
        lo_hi.append((wc.min(0), wc.max(0)))
    occ_idx = [i for i, b in enumerate(boxes) if b.occlude and min(b.size) > 0.05]
    oc_lo = np.array([lo_hi[i][0] for i in occ_idx]) if occ_idx else np.zeros((0, 3))
    oc_hi = np.array([lo_hi[i][1] for i in occ_idx]) if occ_idx else np.zeros((0, 3))
    arr = np.asarray(img).astype(np.float64)
    reach = np.array(o["reach"], dtype=np.float64)
    rw = 1.0 / (1.0 + np.arange(len(reach)))

    def unit(vec):
        ln = np.linalg.norm(vec)
        return vec / ln if ln > 1e-9 else vec

    for bi, b in enumerate(boxes):
        if b.strength <= 0:
            continue
        R3, T3 = b.M[:3, :3], b.M[:3, 3]
        ymin, ymax = lo_hi[bi][0][1], lo_hi[bi][1][1]
        size = np.array(b.size)
        done = []        # (sub, m, ground) per face; the part's mean light is evened to 1 before it is applied
        for f, x, y, w, h, flu, flv, rot in b.faces:
            sub = arr[y:y + h, x:x + w]
            if not (sub[..., 3] > 0).any():
                continue
            s = np.broadcast_to(((np.arange(w) + 0.5) / w)[None, :], (h, w))
            t = np.broadcast_to(((np.arange(h) + 0.5) / h)[:, None], (h, w))
            if flu:
                s = 1 - s
            if flv:
                t = 1 - t
            # the face's own (u, v) for each texel, after the face's rotation; nu, nv: texels along u and v
            u, v, nu, nv = {0: (s, t, w, h), 90: (t, 1 - s, h, w), 180: (1 - s, 1 - t, w, h), 270: (1 - t, s, h, w)}[rot]
            C = np.array(_CORNERS[f], dtype=np.float64) * size
            loc = C[3] + (C[2] - C[3]) * u[..., None] + (C[0] - C[3]) * v[..., None]
            world = loc @ R3.T + T3
            n = R3 @ np.array(_NORMALS[f], dtype=np.float64)
            du, dv = unit(R3 @ (C[2] - C[3])), unit(R3 @ (C[0] - C[3]))
            m = np.ones((h, w))
            if ymax - ymin > 0.5:
                m *= 1 + o["grad"] * ((world[..., 1] - ymin) / (ymax - ymin) - 0.5)
            if abs(n[1]) < 0.6:
                for e, band, along in ((-dv, v < 1.0 / nv, nv), (dv, v > 1 - 1.0 / nv, nv),
                                       (-du, u < 1.0 / nu, nu), (du, u > 1 - 1.0 / nu, nu)):
                    if along < 3:
                        continue
                    if e[1] > 0.6:
                        m = np.where(band, m * (1 + o["edge"]), m)
                    elif e[1] < -0.6:
                        m = np.where(band, m * (1 - o["foot"]), m)
                if o["round"]:
                    across, coord = (du, u) if abs(du[1]) < abs(dv[1]) else (dv, v)
                    width = float(np.linalg.norm(C[2] - C[3] if across is du else C[0] - C[3]))
                    k = o["round"] * min(1.0, o["round_px"] / max(width, 1e-3))
                    m *= 1 - k * ((coord - 0.5) * 2) ** 2
            g = np.ones((h, w))
            if o["ground"] and o["ground_h"] > 0:
                g = 1 - o["ground"] * np.clip(1 - world[..., 1] / o["ground_h"], 0, 1) ** 2
            occl = np.zeros((h, w))
            if o["ao"] and occ_idx:
                flat = world.reshape(-1, 3)
                lo, hi = flat.min(0) - reach[-1], flat.max(0) + reach[-1]
                near = np.where(np.all(oc_hi >= lo, axis=1) & np.all(oc_lo <= hi, axis=1))[0]
                near = [occ_idx[i] for i in near if occ_idx[i] != bi]
                if near:
                    dirs = [unit(n + k * d) for k, d in ((0, du), (0.7, du), (-0.7, du), (0.7, dv), (-0.7, dv))]
                    offs = np.array([d * r for r in reach for d in dirs])                  # (S, 3)
                    wts = np.repeat(rw, len(dirs))
                    pts = world[:, :, None, :] + offs[None, None, :, :]                   # (h, w, S, 3)
                    hit = np.zeros(pts.shape[:3], dtype=bool)
                    for qi in near:
                        iq = inv[qi]
                        lq = pts @ iq[:3, :3].T + iq[:3, 3]
                        hit |= np.all((lq >= -1e-3) & (lq <= np.array(boxes[qi].size) + 1e-3), axis=-1)
                    occl = (hit * wts).sum(-1) / wts.sum()
                    m *= 1 - o["ao"] * occl
            done.append((sub, m, g, occl))
        # Keep each part's own tone: light moves about the part (the mean of what shows is evened back to 1), and
        # only the floor's darkening is a net change
        # (texels mostly buried in another part, which no one sees, are left out of that mean)
        seen = [(sub[..., 3] > 0) & (oc < 0.5) for sub, _, _, oc in done]
        n_seen = sum(float(k.sum()) for k in seen)
        mean = sum(float(m[k].sum()) for (_, m, _, _), k in zip(done, seen)) / n_seen if n_seen else 1.0
        n_vis = sum(float((sub[..., 3] > 0).sum()) for sub, _, _, _ in done)
        lit = []
        for sub, m, g, _ in done:
            m = m / (mean if o.get("even", True) else 1.0)
            m = 1 + (m * g - 1) * b.strength
            rgb = sub[..., :3]
            lum = rgb @ np.array([0.299, 0.587, 0.114])
            lit.append((sub, m, np.clip((m / g - 1) * lum * o["drift"], -o["cap"], o["cap"])))
        # the warm/cool drift moves hue about the part without shifting its mean hue
        dmean = sum(float(d[sub[..., 3] > 0].sum()) for sub, _, d in lit) / n_vis if n_vis else 0.0
        for sub, m, dlt in lit:
            dlt = dlt - dmean
            rgb = sub[..., :3]
            out = rgb * m[..., None] + ((m - 1) * o["floor"])[..., None]
            out[..., 0] += dlt
            out[..., 1] += dlt * 0.3
            out[..., 2] -= dlt
            keep = sub[..., 3] > 0
            sub[..., :3] = np.where(keep[..., None], np.clip(out, 0, 255), rgb)
    img.paste(Image.fromarray(np.rint(arr).astype(np.uint8), "RGBA"))
