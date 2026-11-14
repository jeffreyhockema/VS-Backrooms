"""The item pass (0.700), package "paper": real models for the notes, cards, chalk and the levels' small things that were
drawn as flat sprites (scratchpad brief: COMMON.md, BATCHES.md "paper").

    wanderernote-* (door, way, cache, refuge)   a page torn from a spiral notebook, folded once, pencilled; each kind its own hand
    fun-wanderernote-altered                    the same page, a smiley face in crayon in the corner
    wanderernote-folded                         a sheet folded small and tied with twine, ink showing through
    end-cataloguecard                           a library catalogue card: ruled card stock, typed lines, the rod hole
    chalk, chalk-blue/green/red/yellow          a stick of surveyor's chalk in a paper wrapper, worn to an edge at one end
    l188-keycard                                a white housekeeping master card on a badge clip
    l31-greencard                               Level 31's green arcade card on a split ring
    l3999-circuitboard                          a green board from an arcade machine: chips, capacitors, a heat sink, torn wires
    l3999-coinmech                              a coin mechanism: plate, reject button, coin slot, price window, return cup
    l3999-glowband-magenta/cyan/lilac           a glow bracelet: a ring of glowing tube and its connector
    l3999-neontubing                            a bent length of dead neon tube with its electrode and leads, broken at one end
    l3999-plastic                               a snapped shard of an arcade cabinet's moulded panel, its decal and a screw boss
    l3999-ticket                                a strip of three red tickets, folded
    crownshard                                  a broken piece of the King's gilt crown: two points, a red stone, a cartoon outline

Writes shapes/item/paper/*.json and textures/item/paper/*.png. The item types stay with the generators that write them
(gen_loop, gen_notes, gen_fun, gen_end, gen_deep, gen_188_props, gen_31_content, gen_3999_items, gen_motion): they call
`dress(data, code)` from here, which swaps the flat sprite for the model and its transforms. The four coloured chalk
item types (hand-written in a2b5a948) have no generator: this script patches their look in place.

Textures are 2 px per shape unit (32 px per block face, as vanilla's own item textures), each model's faces packed into
one small atlas and painted by hand-written painters (no photo noise). First-person views use tpHandTransform (1.22:
fpHandTransform is obsolete), so only the GUI, third-person and ground transforms are set.

    python tools/gen_items_paper.py
"""
import json
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
FOLDER = "item/paper"
PPU = 2  # texture pixels per shape unit
FACES = ("north", "east", "south", "west", "up", "down")


# ------------------------------------------------------------------ colour

def clamp(v):
    return max(0, min(255, int(round(v))))


def tone(c, k):
    return tuple(clamp(v * k) for v in c[:3]) + (255,)


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# ------------------------------------------------------------------ painting

class Canvas:
    """One face's rectangle of the atlas, painted as the face is seen from outside, upright (an up face: north at the
    top; a down face: south at the top; a side face: as seen standing in front of it)."""

    def __init__(self, img, x, y, w, h, face, el, v, seed):
        self.img, self.x, self.y, self.w, self.h = img, x, y, w, h
        self.face, self.el, self.v = face, el, v
        self.rng = random.Random(seed)
        self.px = img.load()

    def set(self, i, j, c):
        if 0 <= i < self.w and 0 <= j < self.h:
            self.px[self.x + i, self.y + j] = c

    def get(self, i, j):
        return self.px[self.x + min(max(i, 0), self.w - 1), self.y + min(max(j, 0), self.h - 1)]

    def fill(self, c, jitter=0.035):
        for j in range(self.h):
            for i in range(self.w):
                self.set(i, j, tone(c, 1 + (self.rng.random() * 2 - 1) * jitter))

    def rect(self, i0, j0, i1, j1, c, jitter=0.03):
        for j in range(max(0, j0), min(self.h, j1)):
            for i in range(max(0, i0), min(self.w, i1)):
                self.set(i, j, tone(c, 1 + (self.rng.random() * 2 - 1) * jitter))

    def shade(self, i, j, k):
        if 0 <= i < self.w and 0 <= j < self.h:
            self.set(i, j, tone(self.get(i, j), k))

    def tint(self, i, j, c, t):
        if 0 <= i < self.w and 0 <= j < self.h:
            self.set(i, j, mix(self.get(i, j), c, t))

    def bevel(self, light=1.12, dark=0.82, width=1):
        """Lit from the top left: the top and left rims lighter, the bottom and right darker."""
        for w in range(width):
            for i in range(self.w):
                self.shade(i, w, light)
                self.shade(i, self.h - 1 - w, dark)
            for j in range(self.h):
                self.shade(w, j, light)
                self.shade(self.w - 1 - w, j, dark)

    def grime(self, amount=0.12, edge=2):
        """Dirt worked into the outer rim, a little on the face."""
        for j in range(self.h):
            for i in range(self.w):
                d = min(i, j, self.w - 1 - i, self.h - 1 - j)
                if d < edge and self.rng.random() < 0.55:
                    self.shade(i, j, 1 - amount * (edge - d) / edge)
                elif self.rng.random() < 0.04:
                    self.shade(i, j, 1 - amount * 0.6)

    def specks(self, c, density, t=0.6):
        for j in range(self.h):
            for i in range(self.w):
                if self.rng.random() < density:
                    self.tint(i, j, c, t)

    def gradient(self, k_top, k_bottom):
        for j in range(self.h):
            k = k_top + (k_bottom - k_top) * (j / max(1, self.h - 1))
            for i in range(self.w):
                self.shade(i, j, k)


def flat(c, jitter=0.035, bevel=True, grime=0.0):
    def paint(cv):
        cv.fill(c, jitter)
        if bevel and cv.w > 2 and cv.h > 2:
            cv.bevel()
        if grime:
            cv.grime(grime)
    return paint


# ------------------------------------------------------------------ models

class Model:
    """Elements in the game's shape format (units of 1/16 block), each face painted into one packed atlas."""

    def __init__(self, name):
        self.name, self.elements, self.regions = name, [], []
        self.size = None

    def box(self, name, frm, to, paint, rot=None, origin=None, skip=(), glow=0):
        el = {"name": name, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to]}
        if rot:
            el["rotationOrigin"] = [round(v, 4) for v in (origin or [(frm[i] + to[i]) / 2 for i in range(3)])]
            for axis, a in zip("XYZ", rot):
                if a:
                    el["rotation" + axis] = a
        el["faces"] = {}
        dx, dy, dz = (to[i] - frm[i] for i in range(3))
        ext = {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}
        for face in FACES:
            if face in skip:
                continue
            p = paint
            if isinstance(paint, dict):
                p = paint.get(face) or paint.get("sides" if face in ("north", "east", "south", "west") else "caps") or paint.get("all")
            uw, uh = ext[face]
            pw, ph = max(1, math.ceil(uw * PPU - 1e-6)), max(1, math.ceil(uh * PPU - 1e-6))
            el["faces"][face] = {"texture": "#tex"}
            if glow:
                el["faces"][face]["glow"] = glow
            self.regions.append({"el": el, "face": face, "uw": uw, "uh": uh, "pw": pw, "ph": ph, "paint": p})
        self.elements.append(el)
        return el

    def layout(self):
        """Shelf-packs the faces into the smallest square-ish atlas (power-of-two sides) and sets their UVs."""
        order = sorted(self.regions, key=lambda r: (-r["ph"], -r["pw"]))
        for W in (16, 32, 64, 128):
            x = y = row = 0
            ok = True
            for r in order:
                if r["pw"] > W:
                    ok = False
                    break
                if x + r["pw"] > W:
                    x, y, row = 0, y + row, 0
                r["x"], r["y"] = x, y
                x += r["pw"]
                row = max(row, r["ph"])
            H = y + row
            if ok and H <= W:
                break
        Hp = 16
        while Hp < H:
            Hp *= 2
        self.size = (W, Hp)
        for r in self.regions:
            u0, v0 = r["x"] / PPU, r["y"] / PPU
            r["el"]["faces"][r["face"]]["uv"] = [round(u0, 4), round(v0, 4), round(u0 + r["uw"], 4), round(v0 + r["uh"], 4)]
        return self

    def paint(self, v=None):
        v = v or {}
        img = Image.new("RGBA", self.size, (0, 0, 0, 0))
        for n, r in enumerate(self.regions):
            cv = Canvas(img, r["x"], r["y"], r["pw"], r["ph"], r["face"], r["el"]["name"], v,
                        f"{self.name}/{r['el']['name']}/{r['face']}/{v.get('seed', '')}")
            r["paint"](cv)
        return img

    def shape_json(self, texture):
        W, H = self.size
        return {"textureWidth": W // PPU, "textureHeight": H // PPU, "textures": {"tex": f"backrooms:{FOLDER}/{texture}"},
                "elements": self.elements}

    def corners(self):
        """Every element's corners in shape units, rotated as the game does (Z, then Y, then X about the origin)."""
        out = []
        for el in self.elements:
            f, t = el["from"], el["to"]
            o = el.get("rotationOrigin", [0, 0, 0])
            for c in range(8):
                p = [t[i] if c >> i & 1 else f[i] for i in range(3)]
                x, y, z = p[0] - o[0], p[1] - o[1], p[2] - o[2]
                a = math.radians(el.get("rotationZ", 0))
                x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
                a = math.radians(el.get("rotationY", 0))
                x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
                a = math.radians(el.get("rotationX", 0))
                y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
                out.append((x + o[0], y + o[1], z + o[2]))
        return out


def gui(model, rx, ry, rz, fill=1.1, shift=(0, 0)):
    """The inventory transform: the model's middle in the middle of the slot, turned (rx, ry, rz), scaled so its
    widest extent on screen is `fill` (vanilla's icons are about 1.0: some 26 px of a 48 px slot)."""
    pts = model.corners()
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    c = [(lo[i] + hi[i]) / 2 / 16 for i in range(3)]
    sx, sy = [], []
    for p in pts:
        x, y, z = p[0] / 16 - c[0], p[1] / 16 - c[1], p[2] / 16 - c[2]
        # the game's GUI matrix: RotateX, RotateY, RotateZ (Z applied first)
        a = math.radians(rz)
        x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
        a = math.radians(ry)
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
        a = math.radians(rx)
        y, z = y * math.cos(a) - z * math.sin(a), y * math.sin(a) + z * math.cos(a)
        sx.append(x)
        sy.append(y)
    span = max(max(sx) - min(sx), max(sy) - min(sy))
    # the rotated box's own middle, off the slot's middle, is taken up by a translation (in GUI pixels at item size 25.6)
    mx, my = (max(sx) + min(sx)) / 2, (max(sy) + min(sy)) / 2
    scale = round(fill / span, 2)
    return {"translation": {"x": round(-mx * scale * 25.6 + shift[0], 2), "y": round(-my * scale * 25.6 + shift[1], 2), "z": 0},
            "rotation": {"x": rx, "y": ry, "z": rz},
            "origin": {"x": round(c[0], 3), "y": round(c[1], 3), "z": round(c[2], 3)}, "scale": scale}


def tf(t=(0, 0, 0), r=(0, 0, 0), o=(0.5, 0, 0.5), s=1.0):
    return {"translation": dict(zip("xyz", t)), "rotation": dict(zip("xyz", r)), "origin": dict(zip("xyz", o)), "scale": s}


# Held flat in the fingers, as vanilla holds a letter (itemtypes/lore/letter.json, its shape lying flat round 8, 8)
TP_FLAT = tf((-0.75, -0.16, -0.73), (-81, -92, -2), (0.5, 0, 0.51), 0.5)
# Held like a block in the fist (a chunky thing): the fuse's
TP_CHUNK = tf((-0.8, -0.2, -0.6), (0, 0, -60), (0.5, 0.05, 0.5), 0.6)
# Lying on the ground at its own size: dropped items are drawn at 0.2 x scale, ground-stored ones at 1
GROUND = tf((0, 0, 0), (0, 0, 0), (0.5, 0, 0.5), 4.6)


# ================================================================== the models

PAPER = rgb("e6dcc0")
PAPER_EDGE = rgb("b8ab88")
RULE = rgb("8ea7c4")
MARGIN = rgb("cf7a78")
PENCIL = rgb("4a4a4e")
INK = rgb("27406e")


def paper_sheet(cv, base=PAPER, grime=0.10):
    cv.fill(base, 0.025)
    for j in range(cv.h):  # fibres: a few faint streaks
        if cv.rng.random() < 0.3:
            i0 = cv.rng.randrange(cv.w)
            for i in range(i0, min(cv.w, i0 + cv.rng.randint(2, 4))):
                cv.shade(i, j, 0.965)
    cv.grime(grime, 2)


def scrawl(cv, j, i0, i1, c, gap=0.3, lift=0.0, faint=1.0):
    """A line of handwriting on row j: strokes of 1-3 px with a gap after each (a wider one between words), now and
    then a tall letter, never readable."""
    i = i0
    while i < i1:
        n = cv.rng.randint(1, 3)
        for k in range(n):
            if i + k < i1 and cv.rng.random() > lift:
                cv.tint(i + k, j, c, 0.62 * faint)
                if cv.rng.random() < 0.08:
                    cv.tint(i + k, j - 1, c, 0.35 * faint)
        i += n + (2 if cv.rng.random() < gap else 1)


def note_model():
    """A page torn from a spiral notebook (7 x 9 units), folded once across the middle and opened again: the two halves
    rise a little from the crease, the far corner curls, and the torn spiral edge leaves a ragged fringe."""
    m = Model("wanderernote")
    x0, x1, zc, t = 4.75, 11.25, 8.0, 0.25

    def top(cv):
        v = cv.v
        paper_sheet(cv)
        far = cv.el.endswith("N")      # the half nearer the top of the page
        start = 1 if far else 0
        for j in range(start, cv.h, 2):  # ruled lines, two pixels apart
            for i in range(cv.w):
                cv.tint(i, j, RULE, 0.3)
        for j in range(cv.h):            # the margin
            cv.tint(3, j, MARGIN, 0.5)
        kind = v.get("kind", "way")
        c = PENCIL
        rows = list(range(start + (1 if far else 0), cv.h - 1, 2))
        if kind == "door":   # pencil, half rubbed out, and a box with an arrow through it
            for j in rows:
                scrawl(cv, j, 5, cv.w - 2, c, lift=0.45, faint=0.55)
            if not far:
                for i in range(6, 11):
                    cv.tint(i, 2, c, 0.8)
                    cv.tint(i, 6, c, 0.8)
                for j in range(2, 7):
                    cv.tint(6, j, c, 0.8)
                    cv.tint(10, j, c, 0.8)
                for i in range(4, 13):
                    cv.tint(i, 4, c, 0.9)
                cv.tint(12, 3, c, 0.9)
                cv.tint(12, 5, c, 0.9)
                for _ in range(10):  # the eraser's smudge
                    cv.tint(cv.rng.randrange(4, cv.w - 1), cv.rng.randrange(cv.h), rgb("9c968a"), 0.35)
        elif kind == "way":  # scrawled in a hurry, slanting, and an arrow at the foot
            for n, j in enumerate(rows):
                scrawl(cv, j, 5 + n % 2, cv.w - 1 - n % 3, c, gap=0.35)
            if not far:
                for i in range(6, 12):
                    cv.tint(i, cv.h - 3, c, 0.9)
                cv.tint(11, cv.h - 4, c, 0.9)
                cv.tint(11, cv.h - 2, c, 0.9)
                cv.tint(10, cv.h - 5, c, 0.7)
                cv.tint(10, cv.h - 1, c, 0.7)
        elif kind == "cache":  # a list, each line struck through
            for j in rows:
                cv.tint(5, j, c, 0.9)
                scrawl(cv, j, 7, cv.w - 3 - cv.rng.randint(0, 4), c, gap=0.1)
                if cv.rng.random() < 0.7:
                    for i in range(6, cv.w - 3):
                        cv.tint(i, j, rgb("5a5450"), 0.5)
        elif kind == "refuge":  # a few words, underlined twice
            for j in rows[:-2] if not far else rows:
                scrawl(cv, j, 5, cv.w - 2, c)
            if not far:
                for i in range(5, cv.w - 2):
                    cv.tint(i, cv.h - 3, c, 0.9)
                    cv.tint(i, cv.h - 1, c, 0.8)
        elif kind == "altered":  # the refuge note, and a smiley face in pink crayon in the corner
            for j in rows[:-2] if not far else rows:
                scrawl(cv, j, 5, cv.w - 2, c)
            if not far:
                for i in range(5, cv.w - 6):
                    cv.tint(i, cv.h - 3, c, 0.9)
                    cv.tint(i, cv.h - 1, c, 0.8)
                pink = rgb("e0508c")
                cx, cy = cv.w - 3, cv.h - 3
                for a in range(0, 360, 30):
                    cv.tint(round(cx + 2 * math.cos(math.radians(a))), round(cy + 2 * math.sin(math.radians(a))), pink, 0.9)
                cv.tint(cx - 1, cy - 1, pink, 0.9)
                cv.tint(cx + 1, cy - 1, pink, 0.9)
                cv.tint(cx, cy + 1, pink, 0.9)
        if far:
            cv.tint(cv.w - 2, 0, rgb("a08c64"), 0.4)  # a thumb's worth of dirt

    def back(cv):
        paper_sheet(cv, tone(PAPER, 0.96), 0.14)
        for j in range(0, cv.h, 2):
            for i in range(cv.w):
                cv.tint(i, j, RULE, 0.25)

    def edge(cv):
        cv.fill(PAPER_EDGE, 0.05)

    paint = {"up": top, "down": back, "all": edge}
    # the halves turn up from the crease along x at z = 8 (a negative X turn lifts the south side)
    m.box("HalfN", (x0, 0, 4.0), (x1, t, zc), paint, rot=(6, 0, 0), origin=(8, 0, zc))
    m.box("HalfS", (x0, 0, zc), (x1, t, 12.0), paint, rot=(-5, 0, 0), origin=(8, 0, zc))
    # the far corner curls up (it lies on the north half's far edge)
    m.box("CurlN", (8.5, 0.42, 3.1), (x1, 0.42 + t, 4.1), paint, rot=(28, 0, 0), origin=(8, 0.42, 4.1))
    # the torn spiral edge: tags of paper left by the wire along the west side
    for n, z in enumerate((4.6, 6.4, 8.9, 10.7)):
        rx = 6 if z < zc else -5
        m.box(f"Tear{n}", (x0 - 0.5, 0, z), (x0, t, z + 0.9), {"all": edge, "up": back, "down": back}, rot=(rx, 0, 0),
              origin=(8, 0, zc))
    return m.layout()


def folded_model():
    """A sheet folded small (5 x 6 units) and kept dry: the folded layers, the top fold, ink showing through, and a
    length of twine tied round it both ways with a knot."""
    m = Model("wanderernote-folded")
    cream = rgb("ece4cc")
    twine = rgb("a07a4c")

    def top(cv):
        paper_sheet(cv, cream, 0.08)
        for j in range(2, cv.h - 1, 2):  # ink through the paper, written on the other side
            i = 2
            while i < cv.w - 2:
                n = cv.rng.randint(1, 3)
                for k in range(n):
                    cv.tint(i + k, j, INK, 0.3)
                i += n + 1
        for i in range(cv.w):            # the fold's crease
            cv.shade(i, 0, 0.88)

    def layers(cv):                       # the folded edges: layers of paper
        cv.fill(cream, 0.03)
        for j in range(cv.h):
            if j % 2:
                for i in range(cv.w):
                    cv.shade(i, j, 0.82)

    def under(cv):
        paper_sheet(cv, tone(cream, 0.95), 0.16)

    def cord(cv):
        cv.fill(twine, 0.08)
        for j in range(cv.h):  # the twist
            for i in range(cv.w):
                if (i + j) % 3 == 0:
                    cv.shade(i, j, 0.78)

    m.box("Packet", (5.5, 0, 5), (10.5, 0.5, 11), {"up": top, "down": under, "all": layers})
    m.box("Flap", (5.75, 0.5, 5.25), (10.25, 0.75, 8.75), {"up": top, "down": under, "all": layers}, rot=(-4, 0, 0),
          origin=(8, 0.5, 5.25))
    m.box("TwineX", (5.35, -0.02, 7.6), (10.65, 0.95, 8.1), cord)
    m.box("TwineZ", (7.75, -0.03, 4.85), (8.25, 0.97, 11.15), cord)
    m.box("Knot", (7.55, 0.9, 7.4), (8.45, 1.35, 8.3), cord)
    m.box("Tail", (8.3, 0.95, 7.9), (9.9, 1.15, 8.3), cord, rot=(0, -25, 0), origin=(8.3, 1, 8.1))
    return m.layout()


def catalogue_model():
    """A library catalogue card (5 x 8 units): cream card stock, a red rule under the heading, typed lines, the hole
    the catalogue's rod ran through near the foot, and the top edge bent up from handling."""
    m = Model("cataloguecard")
    stock = rgb("efe6cf")
    red, typed, stamp = rgb("b83a34"), rgb("3a3a40"), rgb("6b4c9a")

    def face(cv):
        cv.fill(stock, 0.025)
        cv.grime(0.08, 2)
        if cv.el == "Card":
            for i in range(1, cv.w - 1):        # the heading's red rule
                cv.tint(i, 3, red, 0.85)
            for i in range(1, 5):               # the call number
                cv.tint(i, 1, typed, 0.8)
            scrawl(cv, 1, 6, cv.w - 2, typed, gap=0.15)
            for j in range(5, cv.h - 1, 2):     # typed lines, even and regular
                i = 2
                end = cv.w - 2 - cv.rng.randint(0, 5)
                while i < end:
                    n = cv.rng.randint(1, 4)
                    for k in range(n):
                        if i + k < end:
                            cv.tint(i + k, j, typed, 0.7)
                    i += n + 1
            for i in range(cv.w - 6, cv.w - 2):  # a date stamp, smudged
                for j in range(cv.h - 4, cv.h - 2):
                    if cv.rng.random() < 0.7:
                        cv.tint(i, j, stamp, 0.55)

    def back(cv):
        cv.fill(tone(stock, 0.96), 0.03)
        cv.grime(0.12, 2)

    def edge(cv):
        cv.fill(tone(stock, 0.78), 0.04)

    p = {"up": face, "down": back, "all": edge}
    t = 0.25
    m.box("Card", (5.5, 0, 4), (10.5, t, 10.5), p)
    m.box("FootW", (5.5, 0, 10.5), (7.5, t, 12), p)
    m.box("FootE", (8.5, 0, 10.5), (10.5, t, 12), p)
    m.box("FootSill", (7.5, 0, 11.5), (8.5, t, 12), p)
    m.box("Bent", (5.5, 0, 3), (10.5, t, 4), p, rot=(14, 0, 0), origin=(8, 0, 4))
    return m.layout()


CHALK = {"white": rgb("ece8dc"), "blue": rgb("4f7fd0"), "green": rgb("57a85e"), "red": rgb("cf4a40"), "yellow": rgb("e9c84a")}


def chalk_model():
    """A stick of surveyor's chalk (1.5 units square, 7.5 long), modelled upright: a kraft paper wrapper with a band
    of the chalk's colour round its lower half, torn at the top, and the bare end worn down to a slanted edge."""
    m = Model("chalk")
    kraft = rgb("b28d5e")

    def chalk(cv):
        c = cv.v.get("colour", CHALK["white"])
        cv.fill(c, 0.05)
        for j in range(cv.h):           # powdery streaks along the stick
            for i in range(cv.w):
                if cv.rng.random() < 0.12:
                    cv.tint(i, j, (255, 255, 255), 0.25)
        if cv.face not in ("up", "down"):
            cv.bevel(1.06, 0.9)

    def worn(cv):                       # the worn end: smoother and lighter, dusty
        c = cv.v.get("colour", CHALK["white"])
        cv.fill(mix(c, (255, 255, 255), 0.18), 0.02)

    def wrapper(cv):
        c = cv.v.get("colour", CHALK["white"])
        cv.fill(kraft, 0.05)
        if cv.face in ("up", "down"):
            return
        for j in range(cv.h):
            for i in range(cv.w):
                if cv.el == "Wrapper" and 1 <= j <= 3:
                    cv.set(i, j, tone(c, 0.95 + cv.rng.random() * 0.08))  # the colour band
                elif cv.el == "Wrapper" and j == 4 and i % 2 == 0:
                    cv.tint(i, j, rgb("3a3028"), 0.55)                    # printed lines
        for i in range(cv.w):            # the torn top edge
            if cv.rng.random() < 0.5:
                cv.shade(i, 0, 0.75)
        cv.grime(0.12, 1)
        cv.bevel(1.05, 0.85)

    s0, s1 = 7.25, 8.75
    m.box("Stick", (s0, 0.1, s0), (s1, 6.4, s1), chalk)
    m.box("Wrapper", (7.12, 0.8, 7.12), (8.88, 3.6, 8.88), wrapper)
    m.box("Flap", (7.6, 3.0, 8.88), (8.6, 4.0, 9.08), wrapper, rot=(16, 0, 0), origin=(8, 3.0, 8.88))
    m.box("Wear1", (7.4, 6.4, 7.4), (8.6, 7.0, 8.6), {"up": worn, "all": chalk})
    m.box("Wear2", (7.55, 7.0, 7.7), (8.45, 7.4, 8.6), {"up": worn, "all": chalk})
    m.box("Edge", (7.25, 6.2, 7.6), (8.75, 7.35, 8.2), {"all": worn, "north": chalk, "south": chalk}, rot=(38, 0, 0),
          origin=(8, 6.5, 7.9))
    return m.layout()


def card_shape(m, x0, x1, z0, z1, t, paint, r=0.25):
    """A plastic card with its corners rounded: the body and two narrower end strips."""
    m.box("Card", (x0, 0, z0 + r), (x1, t, z1 - r), paint)
    m.box("CardN", (x0 + r, 0, z0), (x1 - r, t, z0 + r), paint)
    m.box("CardS", (x0 + r, 0, z1 - r), (x1 - r, t, z1), paint)


def keycard_model():
    """Level 188's housekeeping master card (5 x 8 units), white plastic, on a clear strap and a steel badge clip."""
    m = Model("keycard")
    white, band, stripe = rgb("eeeeea"), rgb("3c6fa8"), rgb("5a5a5e")

    def front(cv):
        cv.fill(white, 0.02)
        if cv.el == "Card":
            for j in range(0, 3):          # the printed band at the top
                for i in range(cv.w):
                    cv.set(i, j, tone(band, 0.95 + cv.rng.random() * 0.08))
            cv.rect(1, 5, 4, 8, band)        # the hotel's square mark
            cv.tint(2, 6, white, 0.7)
            for i in range(5, cv.w - 1):     # "HOUSEKEEPING", too small to read
                if i % 2 or cv.rng.random() < 0.3:
                    cv.tint(i, 6, rgb("6a6a70"), 0.7)
            for i in range(1, cv.w - 1, 2):  # the row of dots
                cv.tint(i, cv.h - 3, rgb("8a8a90"), 0.6)
            cv.tint(cv.w // 2, cv.h - 1, rgb("9a9aa0"), 0.6)  # the insert arrow
        elif cv.el == "CardN":
            for i in range(cv.w):
                cv.set(i, 0, tone(band, 0.95))
        for _ in range(cv.w * cv.h // 12):   # scratches
            cv.tint(cv.rng.randrange(cv.w), cv.rng.randrange(cv.h), rgb("c8c8c4"), 0.5)

    def back(cv):
        cv.fill(tone(white, 0.97), 0.02)
        if cv.el == "Card":
            for j in range(2, 5):            # the magnetic stripe
                for i in range(cv.w):
                    cv.set(i, j, tone(stripe, 0.9 + cv.rng.random() * 0.15))
            for i in range(1, cv.w - 1):
                cv.tint(i, 8, rgb("b0b0b0"), 0.6)  # the signature strip

    def edge(cv):
        cv.fill(tone(white, 0.8), 0.03)

    def strap(cv):
        cv.fill(rgb("c8d4d8"), 0.04)
        cv.bevel(1.12, 0.85)

    def steel(cv):
        cv.fill(rgb("a8acb0"), 0.05)
        cv.bevel(1.2, 0.75)

    card_shape(m, 5.5, 10.5, 4.5, 12.5, 0.3, {"up": front, "down": back, "all": edge})
    m.box("Strap", (7.4, 0.05, 2.0), (8.6, 0.4, 5.6), strap)
    m.box("Snap", (7.55, 0.4, 4.6), (8.45, 0.6, 5.4), steel)
    m.box("Clip", (6.9, 0, 0.6), (9.1, 0.7, 2.3), steel)
    m.box("Jaw", (7.2, 0.7, 0.9), (8.8, 0.95, 2.0), steel, rot=(-10, 0, 0), origin=(8, 0.7, 2.0))
    return m.layout()


def greencard_model():
    """Level 31's arcade card (5 x 8 units): green, a white stripe, a big white 31, on a steel split ring."""
    m = Model("greencard")
    green, dark, white = rgb("2f9a4e"), rgb("1d6b35"), rgb("f2f2ea")

    def front(cv):
        cv.fill(green, 0.03)
        if cv.el == "Card":
            for i in range(cv.w):            # the light stripe
                for j in (2, 3):
                    cv.set(i, j, tone(rgb("bfe8c4"), 0.95 + cv.rng.random() * 0.06))
            # a blocky 31, lower right (Level 31's own number)
            three = ["111", "..1", ".11", "..1", "111"]
            one = [".1", "11", ".1", ".1", "11"]
            ox, oy = cv.w - 7, cv.h - 7
            for j, row in enumerate(three):
                for i, ch in enumerate(row):
                    if ch == "1":
                        cv.set(ox + i, oy + j, white)
            for j, row in enumerate(one):
                for i, ch in enumerate(row):
                    if ch == "1":
                        cv.set(ox + 4 + i, oy + j, white)
            for j in range(cv.h - 3, cv.h):   # a darker foot
                for i in range(cv.w):
                    cv.shade(i, j, 0.92)
        for _ in range(cv.w * cv.h // 14):
            cv.tint(cv.rng.randrange(cv.w), cv.rng.randrange(cv.h), rgb("7fc08f"), 0.35)

    def back(cv):
        cv.fill(tone(green, 0.92), 0.03)
        if cv.el == "Card":
            for j in range(3, 6):
                for i in range(cv.w):
                    cv.set(i, j, tone(rgb("26262a"), 0.9 + cv.rng.random() * 0.15))

    def edge(cv):
        cv.fill(dark, 0.04)

    def steel(cv):
        cv.fill(rgb("b4b8bc"), 0.06)
        cv.bevel(1.2, 0.75)

    card_shape(m, 5.5, 10.5, 4.0, 12.0, 0.3, {"up": front, "down": back, "all": edge})
    # the split ring through the card's corner: an octagon of wire, lying flat
    R, w = 1.3, 0.35
    L = 2 * R * math.tan(math.radians(22.5)) + 0.05
    cx, cz = 6.3, 4.6
    for k in range(8):
        m.box(f"Ring{k}", (cx - L / 2, 0.12, cz + R - w / 2), (cx + L / 2, 0.12 + w, cz + R + w / 2), steel,
              rot=(0, 45 * k, 0), origin=(cx, 0.12, cz))
    return m.layout()


def circuit_model():
    """A board from an arcade machine (9 x 7 units): green solder mask with copper traces and white print, a big chip
    and a small one, two capacitors, a finned heat sink, a resistor, the gold edge fingers, a broken corner and two
    torn wires."""
    m = Model("circuitboard")
    mask, trace, silk, gold = rgb("2a7a3a"), rgb("8fb86a"), rgb("e8ecd8"), rgb("d8b048")

    def board(cv):
        cv.fill(mask, 0.04)
        rng = cv.rng
        for _ in range(9):                 # traces: runs with right-angle turns
            i, j = rng.randrange(cv.w), rng.randrange(cv.h)
            for _ in range(rng.randint(5, 12)):
                cv.tint(i, j, trace, 0.6)
                if rng.random() < 0.5:
                    i += rng.choice((-1, 1))
                else:
                    j += rng.choice((-1, 1))
        for _ in range(10):                # solder pads
            cv.set(rng.randrange(cv.w), rng.randrange(cv.h), tone(rgb("c9ccd0"), 0.9 + rng.random() * 0.2))
        for _ in range(4 if cv.w > 4 and cv.h > 3 else 0):  # printed outlines of parts long gone
            i, j = rng.randrange(cv.w - 3), rng.randrange(cv.h - 2)
            for k in range(3):
                cv.tint(i + k, j, silk, 0.6)
                cv.tint(i + k, j + 2, silk, 0.6)
        if cv.el == "Board":
            for i in range(1, cv.w - 1, 2):   # the gold edge fingers, along the south edge
                for j in range(cv.h - 2, cv.h):
                    cv.set(i, j, tone(gold, 0.9 + rng.random() * 0.2))
        cv.grime(0.12, 1)
        cv.specks(rgb("8a8070"), 0.04, 0.5)  # dust

    def board_edge(cv):
        cv.fill(rgb("c8c0a0"), 0.05)        # the fibreglass core
        for i in range(cv.w):
            cv.tint(i, 0, mask, 0.7)

    def chip(cv):
        cv.fill(rgb("26262a"), 0.04)
        if cv.face == "up":
            cv.tint(1, 1, rgb("707078"), 0.8)   # the pin-1 dot
            for i in range(2, cv.w - 2):
                cv.tint(i, cv.h // 2, rgb("55555c"), 0.6)
            cv.bevel(1.25, 0.85)
        elif cv.face in ("north", "south", "east", "west"):
            for i in range(0, cv.w, 2):         # its legs
                cv.set(i, cv.h - 1, tone(rgb("c8ccd0"), 0.9 + cv.rng.random() * 0.2))

    def cap(cv):
        c = cv.v.get("cap", rgb("2c4f9c"))
        cv.fill(c, 0.04)
        if cv.face == "up":
            cv.fill(rgb("b8bcc0"), 0.05)
            for i in range(cv.w):
                cv.tint(i, cv.h // 2, rgb("6a6e74"), 0.7)
            for j in range(cv.h):
                cv.tint(cv.w // 2, j, rgb("6a6e74"), 0.7)
        else:
            for j in range(cv.h):
                cv.tint(0, j, rgb("dadada"), 0.55)   # the stripe
            cv.bevel(1.15, 0.8)

    def fins(cv):
        cv.fill(rgb("b6bcc2"), 0.05)
        cv.bevel(1.18, 0.78)

    def resistor(cv):
        cv.fill(rgb("d8c08c"), 0.04)
        if cv.face != "down":
            for i, c in ((1, rgb("8a4a20")), (2, rgb("202020")), (3, rgb("d03030"))):
                for j in range(cv.h):
                    cv.set(i, j, c)

    def wire(cv):
        cv.fill(cv.v.get("wire", rgb("c03028")) if cv.el == "WireR" else rgb("2a2a2c"), 0.05)
        if cv.face in ("east",):
            cv.fill(rgb("c87a40"), 0.05)   # the copper core where it tore

    bp = {"up": board, "down": board_edge, "all": board_edge}
    m.box("Board", (3.5, 0, 5.5), (12.5, 0.5, 11.5), bp)
    m.box("BoardN", (3.5, 0, 4.5), (10.5, 0.5, 5.5), bp)
    m.box("Chip", (5.0, 0.5, 6.2), (8.0, 1.1, 8.6), chip)
    m.box("Chip2", (9.0, 0.5, 5.2), (10.4, 0.95, 6.6), chip)
    m.box("Cap", (9.3, 0.5, 8.4), (10.5, 2.3, 9.6), cap)
    m.box("Cap2", (10.9, 0.5, 8.9), (11.8, 1.8, 9.8), cap)
    m.box("Sink", (4.8, 0.5, 9.0), (7.8, 0.9, 11.0), fins)
    for n, z in enumerate((9.0, 9.85, 10.7)):
        m.box(f"Fin{n}", (4.8, 0.9, z), (7.8, 2.1, z + 0.3), fins)
    m.box("Resistor", (8.4, 0.5, 9.6), (9.0, 0.9, 10.8), {"all": resistor, "north": flat(rgb("b8b8b8")), "south": flat(rgb("b8b8b8"))})
    m.box("WireR", (12.3, 0.5, 6.4), (14.2, 0.85, 6.75), wire, rot=(0, -14, 0), origin=(12.3, 0.6, 6.6))
    m.box("WireK", (12.3, 0.5, 7.2), (13.6, 0.85, 7.55), wire, rot=(0, 9, 0), origin=(12.3, 0.6, 7.4))
    return m.layout()


def coinmech_model():
    """An arcade coin mechanism lying face up: the housing behind, the plate with its screws, the reject button, the
    coin slot in its bezel, the red price window and the coin-return cup, and the wire lever out of the side."""
    m = Model("coinmech")
    chrome, housing, red = rgb("c4c2b8"), rgb("4a4c50"), rgb("c0302c")

    def plate(cv):
        cv.fill(chrome, 0.03)
        for j in range(cv.h):              # brushed
            k = 1 + (cv.rng.random() - 0.5) * 0.06
            for i in range(cv.w):
                cv.shade(i, j, k)
        if cv.face == "up":
            for i, j in ((1, 1), (cv.w - 2, 1), (1, cv.h - 2), (cv.w - 2, cv.h - 2)):
                cv.set(i, j, tone(rgb("6e6c66"), 1))   # the screws
            cv.grime(0.14, 2)
            cv.bevel(1.12, 0.8)
        else:
            cv.bevel(1.1, 0.75)

    def box_metal(cv):
        cv.fill(housing, 0.05)
        cv.grime(0.1, 1)
        if cv.face != "up":
            cv.bevel(1.15, 0.8)

    def bezel(cv):
        cv.fill(tone(chrome, 1.05), 0.03)
        if cv.face == "up":
            for j in range(1, cv.h - 1):       # the coin slot
                cv.set(cv.w // 2, j, rgb("101012"))
                cv.set(cv.w // 2 - 1, j, rgb("2a2a2c"))
        cv.bevel(1.2, 0.75)

    def button(cv):
        cv.fill(tone(chrome, 1.1), 0.03)
        if cv.face == "up":
            for i in range(1, cv.w - 1):
                cv.tint(i, cv.h // 2, rgb("70706a"), 0.5)
        cv.bevel(1.25, 0.75)

    def price(cv):
        cv.fill(red, 0.04)
        if cv.face == "up":
            for i in range(2, cv.w - 2):        # the price, a white blur
                if i % 3:
                    cv.tint(i, 1, (250, 250, 240, 255), 0.85)
        cv.bevel(1.1, 0.8)

    def cup(cv):
        cv.fill(tone(chrome, 0.98), 0.04)
        if cv.face == "north":
            cv.rect(1, 0, cv.w - 1, cv.h - 1, rgb("141416"), 0.02)   # the opening
        cv.bevel(1.15, 0.78)

    def lever(cv):
        cv.fill(rgb("d0d0cc"), 0.05)

    m.box("Housing", (5.2, 0, 4.2), (10.8, 2.0, 11.8), box_metal)
    m.box("Plate", (4.6, 2.0, 3.2), (11.4, 2.6, 12.8), plate)
    m.box("Button", (7.1, 2.6, 3.9), (8.9, 3.3, 5.2), button)
    m.box("Bezel", (6.6, 2.6, 5.7), (9.4, 3.1, 8.6), bezel)
    m.box("Price", (6.1, 2.6, 9.0), (9.9, 2.85, 10.2), price)
    m.box("Cup", (6.6, 2.6, 10.6), (9.4, 3.6, 12.3), cup)
    m.box("Lever", (10.8, 0.8, 6.0), (12.6, 1.2, 6.4), lever, rot=(0, 0, -10), origin=(10.8, 1, 6.2))
    m.box("LeverTip", (12.2, 0.6, 6.0), (12.6, 1.6, 6.4), lever, rot=(0, 0, -10), origin=(10.8, 1, 6.2))
    return m.layout()


GLOW = {"magenta": rgb("f04ad8"), "cyan": rgb("46e6f0"), "lilac": rgb("b48cf8")}


def glowband_model():
    """A glow bracelet lying flat: an octagon of glowing tube (radius 3 units) and the white connector that closes it."""
    m = Model("glowband")

    def tube(cv):
        c = cv.v.get("colour", GLOW["magenta"])
        cv.fill(c, 0.03)
        for i in range(cv.w):          # the shine along the tube and its brighter core
            cv.tint(i, 0, (255, 255, 255), 0.45)
            if cv.h > 2:
                cv.tint(i, cv.h - 1, tone(c, 0.7), 0.6)

    def connector(cv):
        cv.fill(rgb("f0f0ea"), 0.03)
        cv.bevel(1.08, 0.8)

    R, w = 3.0, 0.75
    L = 2 * R * math.tan(math.radians(22.5)) + 0.06
    for k in range(8):
        m.box(f"Tube{k}", (8 - L / 2, 0, 8 + R - w / 2), (8 + L / 2, w, 8 + R + w / 2), tube, rot=(0, 45 * k, 0),
              origin=(8, 0, 8), glow=110)
    m.box("Connector", (7.35, -0.05, 10.55), (8.65, 0.85, 11.45), connector)
    return m.layout()


def neon_model():
    """A length of dead neon tube bent back on itself (pale phosphor glass), its electrode cap and two leads at one end,
    snapped off at the other."""
    m = Model("neontubing")
    glass = rgb("f0d6ec")

    def tube(cv):
        cv.fill(glass, 0.03)
        for i in range(cv.w):
            cv.tint(i, 0, (255, 255, 255), 0.6)      # the highlight
            if cv.h > 1:
                cv.tint(i, cv.h - 1, rgb("b89ab8"), 0.5)
        for _ in range(max(1, cv.w // 6)):           # dust inside the glass
            cv.tint(cv.rng.randrange(cv.w), cv.rng.randrange(cv.h), rgb("9a8c90"), 0.35)

    def snapped(cv):                                 # the broken end: sharp, clear, dark inside
        cv.fill(rgb("dcdce6"), 0.05)
        if cv.face == "west":
            cv.set(cv.w // 2, cv.h // 2, rgb("40404a"))

    def cap(cv):
        cv.fill(rgb("3c3c40"), 0.05)
        cv.bevel(1.2, 0.8)

    def band(cv):
        cv.fill(rgb("b8b4a8"), 0.05)
        cv.bevel(1.2, 0.8)

    def lead(cv):
        cv.fill(rgb("c8302c") if cv.el == "LeadR" else rgb("e0e0dc"), 0.05)

    d = 0.8
    h = d
    tp = {"all": tube}
    m.box("RunA", (3.6, 0, 5.6), (11.6, h, 5.6 + d), tp)
    m.box("BendA", (11.2, 0, 5.6), (12.9, h, 5.6 + d), tp, rot=(0, -45, 0), origin=(11.6, 0, 6.0))
    m.box("Back", (12.6, 0, 6.7), (12.6 + d, h, 9.3), tp)
    m.box("BendB", (11.2, 0, 9.4), (12.9, h, 9.4 + d), tp, rot=(0, 45, 0), origin=(11.6, 0, 9.8))
    m.box("RunB", (5.6, 0, 9.4), (11.6, h, 9.4 + d), tp)
    m.box("Snap", (5.0, 0.1, 9.5), (5.6, h - 0.1, 9.4 + d - 0.1), {"all": snapped}, rot=(0, 18, 0), origin=(5.6, 0, 9.8))
    m.box("Cap", (2.2, -0.05, 5.45), (3.6, h + 0.05, 5.75 + d), cap)
    m.box("CapBand", (3.2, -0.1, 5.4), (3.6, h + 0.1, 5.8 + d), band)
    m.box("LeadR", (0.6, 0.25, 5.7), (2.2, 0.5, 5.95), lead, rot=(0, -12, 0), origin=(2.2, 0.3, 5.8))
    m.box("LeadW", (0.9, 0.25, 6.15), (2.2, 0.5, 6.4), lead, rot=(0, 15, 0), origin=(2.2, 0.3, 6.3))
    return m.layout()


def plastic_model():
    """A snapped shard of an arcade cabinet's moulded side panel: glossy cyan, a scrap of the pink decal, a broken edge,
    a strengthening rib and a screw boss on the back (it lies face up, the rib holding one side off the floor)."""
    m = Model("plastic")
    cyan, pink = rgb("3cc4d8"), rgb("f070b0")

    def face(cv):
        cv.fill(cyan, 0.03)
        if cv.el == "PanelA":
            cv.rect(cv.w // 2 - 3, 2, cv.w // 2 + 3, 7, pink)        # the decal
            for i in range(cv.w // 2 - 3, cv.w // 2 + 3):
                cv.tint(i, 4, (255, 255, 255), 0.5)
        for i in range(min(cv.w, cv.h)):                              # the gloss
            cv.tint(i, i // 2, (255, 255, 255), 0.25)
        for _ in range(cv.w * cv.h // 10):                            # scuffs
            cv.tint(cv.rng.randrange(cv.w), cv.rng.randrange(cv.h), rgb("a8dce4"), 0.5)
        cv.grime(0.1, 1)

    def back(cv):
        cv.fill(tone(cyan, 0.8), 0.04)
        for _ in range(4):
            cv.tint(cv.rng.randrange(cv.w), cv.rng.randrange(cv.h), rgb("207080"), 0.6)

    def edge(cv):  # the broken edge: stress-whitened
        cv.fill(mix(cyan, (255, 255, 255), 0.45), 0.06)

    def boss(cv):
        cv.fill(tone(cyan, 0.75), 0.04)
        if cv.face == "up":
            cv.set(cv.w // 2, cv.h // 2, rgb("1a3a40"))
        cv.bevel(1.1, 0.8)

    p = {"up": face, "down": back, "all": edge}
    m.box("PanelA", (4.0, 0.6, 4.5), (11.0, 1.2, 9.5), p, rot=(0, 0, -6), origin=(8, 0.6, 7))
    m.box("PanelB", (5.5, 0.6, 9.0), (10.0, 1.2, 12.0), p, rot=(0, 16, -6), origin=(8, 0.6, 9.5))
    m.box("PanelC", (9.5, 0.6, 3.6), (12.2, 1.2, 6.5), p, rot=(0, -22, -6), origin=(10, 0.6, 5))
    m.box("Rib", (4.6, 0, 5.0), (5.2, 0.7, 10.5), {"all": back, "up": back})
    m.box("Boss", (8.6, 0, 6.8), (9.8, 0.7, 8.0), boss)
    return m.layout()


def ticket_model():
    """A strip of three red arcade tickets folded zig-zag (each 7 x 3 units): a cream border, a blocky print the eye
    reads as ADMIT ONE without spelling it, perforated ends and a serial number."""
    m = Model("ticket")
    red, cream = rgb("d23a36"), rgb("f4e6c8")

    def front(cv):
        cv.fill(red, 0.03)
        for i in range(cv.w):
            cv.tint(i, 0, cream, 0.75)
            cv.tint(i, cv.h - 1, cream, 0.75)
        for j in range(cv.h):
            cv.tint(0, j, cream, 0.75)
            cv.tint(cv.w - 1, j, cream, 0.75)
        for i in range(2, cv.w - 2):          # the print: two blocky words
            if i not in (cv.w // 2 - 1, cv.w // 2) and cv.rng.random() < 0.85:
                for j in (2, 3):
                    if cv.rng.random() < 0.8:
                        cv.tint(i, j, cream, 0.85)
        cv.grime(0.12, 1)

    def back(cv):
        cv.fill(tone(red, 0.9), 0.03)
        for i in range(2, cv.w - 2, 3):       # the serial number
            cv.tint(i, cv.h // 2, rgb("401818"), 0.5)

    def edge(cv):
        cv.fill(tone(red, 0.7), 0.04)
        if cv.face in ("east", "west"):        # perforations
            for j in range(0, cv.h, 2):
                cv.shade(0, j, 0.6)

    p = {"up": front, "down": back, "all": edge}
    t = 0.2
    m.box("Ticket1", (4.5, 0, 3.0), (11.5, t, 6.0), p)
    m.box("Ticket2", (4.5, 0, 6.0), (11.5, t, 9.0), p, rot=(-18, 0, 0), origin=(8, 0, 6.0))
    lift = 3 * math.sin(math.radians(18))
    z2 = 6 + 3 * math.cos(math.radians(18))
    m.box("Ticket3", (4.5, lift, z2), (11.5, lift + t, z2 + 3), p, rot=(16, 0, 0), origin=(8, lift, z2))
    return m.layout()


def crown_model():
    """A broken piece of the King's crown (Level 94: a cartoon king, so a cartoon outline): a curved gilt band with a
    beaded rim, two points with balls on their tips, a red stone, and the jagged ends where it broke."""
    m = Model("crownshard")
    gold, deep, red = rgb("e8b83c"), rgb("a8761c"), rgb("c8202c")
    ink = rgb("3a2410")

    def gilt(cv):
        cv.fill(gold, 0.03)
        cv.gradient(1.12, 0.86)
        for _ in range(cv.w * cv.h // 9):     # the shine
            cv.tint(cv.rng.randrange(cv.w), cv.rng.randrange(cv.h), rgb("fff2b0"), 0.5)
        for i in range(cv.w):                  # the cartoon outline
            cv.tint(i, cv.h - 1, ink, 0.55)
        for j in range(cv.h):
            cv.tint(cv.w - 1, j, ink, 0.45)

    def rim(cv):
        cv.fill(deep, 0.04)
        for i in range(0, cv.w, 2):            # the beads
            cv.tint(i, max(0, cv.h // 2 - 1), rgb("f8d878"), 0.7)
        for i in range(cv.w):
            cv.tint(i, cv.h - 1, ink, 0.5)

    def broken(cv):
        cv.fill(tone(deep, 0.85), 0.08)

    def stone(cv):
        cv.fill(red, 0.04)
        if cv.face == "up":
            cv.set(0, 0, rgb("ffb0b8"))
            cv.bevel(1.25, 0.7)
        else:
            cv.bevel(1.1, 0.7)

    def ball(cv):
        cv.fill(rgb("f6d466"), 0.04)
        cv.bevel(1.2, 0.75)

    g = {"all": gilt}
    # the band lies flat, its points to the north; two halves bent to a curve
    m.box("BandW", (3.2, 0, 8.4), (8.2, 1.0, 10.6), g, rot=(0, -10, 0), origin=(8, 0, 9.5))
    m.box("BandE", (7.8, 0, 8.4), (12.6, 1.0, 10.6), g, rot=(0, 10, 0), origin=(8, 0, 9.5))
    m.box("RimW", (3.2, 0, 10.4), (8.2, 1.3, 11.2), {"all": rim}, rot=(0, -10, 0), origin=(8, 0, 9.5))
    m.box("RimE", (7.8, 0, 10.4), (12.6, 1.3, 11.2), {"all": rim}, rot=(0, 10, 0), origin=(8, 0, 9.5))
    # the points: squares turned 45 degrees, their lower halves sunk in the band
    m.box("PointW", (4.3, 0.1, 6.1), (6.9, 0.9, 8.7), g, rot=(0, 45, 0), origin=(5.6, 0.5, 7.4))
    m.box("PointE", (9.4, 0.1, 6.4), (11.6, 0.9, 8.6), g, rot=(0, 45, 0), origin=(10.5, 0.5, 7.5))
    m.box("TipW", (5.1, 0.05, 4.3), (6.1, 1.05, 5.3), {"all": ball})
    m.box("TipE", (10.0, 0.05, 4.9), (11.0, 1.05, 5.9), {"all": ball})
    m.box("Stone", (7.2, 1.0, 8.8), (8.8, 1.5, 10.2), {"all": stone})
    m.box("StoneTop", (7.5, 1.5, 9.1), (8.5, 1.8, 9.9), {"all": stone})
    m.box("BreakW", (2.6, 0, 8.9), (3.3, 0.8, 10.0), {"all": broken}, rot=(0, -10, 0), origin=(8, 0, 9.5))
    m.box("BreakE", (12.5, 0, 8.6), (13.1, 0.7, 9.8), {"all": broken}, rot=(0, 10, 0), origin=(8, 0, 9.5))
    return m.layout()


# ================================================================== the items

MODELS = {}


def model(name):
    if name not in MODELS:
        MODELS[name] = {"wanderernote": note_model, "wanderernote-folded": folded_model, "cataloguecard": catalogue_model,
                        "chalk": chalk_model, "keycard": keycard_model, "greencard": greencard_model,
                        "circuitboard": circuit_model, "coinmech": coinmech_model, "glowband": glowband_model,
                        "neontubing": neon_model, "plastic": plastic_model, "ticket": ticket_model,
                        "crownshard": crown_model}[name]()
    return MODELS[name]


NOTE_KINDS = ("door", "way", "cache", "refuge")

# code -> (model, textures by variant: {suffix: painter variables}, gui rotation, gui fill, tp, ground, extra)
ITEMS = {
    "wanderernote": ("wanderernote", {k: {"kind": k} for k in NOTE_KINDS}, (125, 150, 0), 1.15, TP_FLAT, GROUND),
    "fun-wanderernote": ("wanderernote", {"altered": {"kind": "altered"}}, (125, 150, 0), 1.15, TP_FLAT, GROUND),
    "wanderernote-folded": ("wanderernote-folded", None, (125, 150, 0), 1.05, TP_FLAT, GROUND),
    "end-cataloguecard": ("cataloguecard", None, (125, 150, 0), 1.15, TP_FLAT, GROUND),
    "chalk": ("chalk", {"": {"colour": CHALK["white"]}}, (-160, -45, -40), 1.15, None, None),
    "chalk-blue": ("chalk", {"": {"colour": CHALK["blue"]}}, (-160, -45, -40), 1.15, None, None),
    "chalk-green": ("chalk", {"": {"colour": CHALK["green"]}}, (-160, -45, -40), 1.15, None, None),
    "chalk-red": ("chalk", {"": {"colour": CHALK["red"]}}, (-160, -45, -40), 1.15, None, None),
    "chalk-yellow": ("chalk", {"": {"colour": CHALK["yellow"]}}, (-160, -45, -40), 1.15, None, None),
    "l188-keycard": ("keycard", None, (125, 150, 0), 1.15, TP_FLAT, GROUND),
    "l31-greencard": ("greencard", None, (125, 150, 0), 1.15, TP_FLAT, GROUND),
    "l3999-circuitboard": ("circuitboard", None, (130, 145, 0), 1.2, TP_FLAT, GROUND),
    "l3999-coinmech": ("coinmech", None, (130, 145, 0), 1.15, TP_CHUNK, GROUND),
    "l3999-glowband": ("glowband", {c: {"colour": GLOW[c]} for c in GLOW}, (125, 150, 0), 1.1, TP_FLAT, GROUND),
    "l3999-neontubing": ("neontubing", None, (125, 150, 0), 1.2, TP_FLAT, GROUND),
    "l3999-plastic": ("plastic", None, (125, 150, 0), 1.15, TP_FLAT, GROUND),
    "l3999-ticket": ("ticket", None, (125, 150, 0), 1.1, TP_FLAT, GROUND),
    "crownshard": ("crownshard", None, (125, 150, 0), 1.2, TP_FLAT, GROUND),
}

# The chalk is modelled upright (as vanilla's tools and the bone are) and laid down on the ground: a 90 degree turn
# about X through the stick's middle, dropped so it rests on its side
CHALK_MID = 3.7 / 16
CHALK_TP = tf((-0.75, -0.35, -0.55), (0, -45, -10), (0.5, 0.2, 0.5), 0.55)
CHALK_GROUND = tf((0, round(0.2 * 4.6 * 0.9 / 16, 3), 0), (90, 0, 0), (0.5, CHALK_MID, 0.5), 4.6)
CHALK_STORED = {"translation": {"x": 0, "y": round(-CHALK_MID + 0.9 / 16, 3), "z": 0}, "rotation": {"x": 90, "y": 0, "z": 0},
                "origin": {"x": 0.5, "y": CHALK_MID, "z": 0.5}}


def texture_name(code, suffix):
    base = ITEMS[code][0]
    if code.startswith("chalk"):
        return code
    if code == "fun-wanderernote":
        return "wanderernote-altered"
    return base + ("-" + suffix if suffix else "")


def look(code):
    """The keys an item type needs for its model: shape, textures (by type where its variants differ), transforms."""
    name, variants, rot, fill, tp, ground = ITEMS[code]
    m = model(name)
    out = {"shape": {"base": f"{FOLDER}/{name}"}}
    if variants and len(variants) > 1:
        out["texturesByType"] = {f"{code}-{s}": {"tex": {"base": f"{FOLDER}/{texture_name(code, s)}"}} for s in variants}
    else:
        s = next(iter(variants)) if variants else ""
        out["textures"] = {"tex": {"base": f"{FOLDER}/{texture_name(code, s)}"}}
    out["guiTransform"] = gui(m, *rot, fill=fill)
    if code.startswith("chalk"):
        out["tpHandTransform"] = CHALK_TP
        out["groundTransform"] = CHALK_GROUND
    else:
        out["tpHandTransform"] = tp
        out["groundTransform"] = ground
    return out


def dress(data, code):
    """Swaps an item type's flat sprite for its model, in place (call it before detail_kit.ground_storable, so a
    shaped item gets no flat item's groundStorageTransform), and returns it."""
    for k in ("texture", "textureByType", "texturebytype", "textures", "texturesByType"):
        data.pop(k, None)
    lk = look(code)
    for k in ("guiTransform", "fpHandTransform", "tpHandTransform", "groundTransform"):
        data.pop(k, None)
    data.update(lk)
    attrs = data.get("attributes")
    if attrs is not None:
        attrs.pop("groundStorageTransform", None)
        if not attrs:
            del data["attributes"]
    if code.startswith("chalk"):
        data.setdefault("attributes", {})["groundStorageTransform"] = CHALK_STORED
    return data


# ================================================================== writing

def write_json(path, data, comment=None, nl="\r\n"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline=nl) as f:
        f.write(text + "\n")


def write_assets():
    written = []
    for code, (name, variants, *_rest) in ITEMS.items():
        m = model(name)
        shape_path = os.path.join(ASSETS, "shapes", FOLDER, name + ".json")
        first = next(iter(variants)) if variants else ""
        if name not in written:
            write_json(shape_path, m.shape_json(texture_name(code, first) if not code.startswith("chalk") else "chalk"))
            written.append(name)
        for s, v in (variants or {"": {}}).items():
            img = m.paint(v)
            path = os.path.join(ASSETS, "textures", FOLDER, texture_name(code, s) + ".png")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            img.save(path)
    return written


HAND_WRITTEN = {"chalk-blue": "deep/chalk-blue.json", "chalk-green": "deep/chalk-green.json",
                "chalk-red": "deep/chalk-red.json", "chalk-yellow": "deep/chalk-yellow.json"}


def patch_hand_written():
    """The coloured chalk's item types have no generator: their look is patched in place, all else kept, key order
    kept (the model's keys where the texture was)."""
    for code, rel in HAND_WRITTEN.items():
        path = os.path.join(ASSETS, "itemtypes", rel)
        text = open(path, encoding="utf-8").read()
        comment = re.match(r"\s*//\s*(.*)\n", text).group(1).rstrip("\r")
        data = json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))
        out = {}
        lk = None
        for k, v in data.items():
            if k in ("texture", "textures", "shape"):
                if lk is None:
                    lk = dress({}, code)
                    for kk in ("shape", "textures", "texturesByType"):
                        if kk in lk:
                            out[kk] = lk[kk]
                continue
            out[k] = v
        lk = lk or dress({}, code)
        for kk in ("guiTransform", "tpHandTransform", "groundTransform"):
            out[kk] = lk[kk]
        out.pop("fpHandTransform", None)
        out.setdefault("attributes", {})["groundStorageTransform"] = CHALK_STORED
        write_json(path, out, comment)


def main():
    write_assets()
    patch_hand_written()
    for name in sorted({v[0] for v in ITEMS.values()}):
        m = model(name)
        print(f"{name}: {len(m.elements)} elements, texture {m.size[0]} x {m.size[1]}")


if __name__ == "__main__":
    main()
