"""The item pass (0.700), package "pantry": everyday food, drink and medicine as real 3D models.

Writes, idempotently:

  * shapes/item/pantry/*.json: the models, built from boxes in item space (0-16 per axis, standing on y = 0, centred on
    x = z = 8), each with its own texture atlas laid out here (one texel per unit, as vanilla's items);
  * textures/item/pantry/*.png: the atlases, painted texel by texel from materials (plastic, glass, liquid, printed
    labels, tinplate, card, foil), with shading, grain and wear;
  * the item types that have no generator of their own: itemtypes/almondwater.json, cannedbeans.json, crackers.json and
    foodscraps.json (their behaviours, nutrition and attributes as they were; only the look is this generator's).

The other item types of the package are written by their own generators, which take the look from here (`look(code)`:
the shape, the textures and the four transforms): gen_needs.py (the bottles of the Needs feature), gen_14_items.py
(Level 14's painkillers, antibiotics and stale soda), gen_deep.py (the Snackrooms' chips, candy bar, soda, cashew water and
bottled water), gen_motion.py (Almond Milk) and gen_pool.py (Epsom salt, red water).

The models:
  - bottle: the Almond Water bottle, a 1990s PET bottle (ribbed foot, recessed label panel, shoulder, threaded neck,
    tamper ring, ridged cap). Shared, each with its own atlas, by Blue and Green Almond Water, Cashew Water, the Snackrooms'
    bottle of water, the refilled bottles (clean, murky, salt: no label) and the empty bottle;
  - sodabottle: Level 14's stale soda, a brown glass bottle with a long neck, a crown cap and a half-peeled label;
  - milkbottle: Level 94's Almond Milk, a 1950s glass milk bottle with a printed band and a red foil cap;
  - flask: red water from the Sanguine Reservoir, a corked glass flask;
  - beancan: a tin of beans (rims, beads, a paper label, a lid with its rings); sodacan: a can of soda with its tab;
  - crackerbox: a box of crackers with its flap open and a wax-paper sleeve showing; candybar: a wrapped chocolate bar
    torn open at one end; chips: a pillow bag of chips with crimped seals;
  - pillbottle: amber, with a child-proof cap; blister: a card of eight capsules, two pushed out;
  - saltheap: a little heap of Epsom salt crystals; foodscraps: an emptied tin with its lid bent back, a torn wrapper and
    crumbs.

    python tools/gen_items_pantry.py            (or through tools/locked.sh run)
"""
import json
import math
import os
import re
import sys
import zlib

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
SHAPES = os.path.join(ASSETS, "shapes", "item", "pantry")
TEXTURES = os.path.join(ASSETS, "textures", "item", "pantry")
DIRS = ("north", "east", "south", "west", "up", "down")

# Corners of each face (top-left, top-right, bottom-left) in the unit box, as the game maps a face's UV: seen from
# outside, north faces have east on the left, up faces run +x along u and +z along v (tools/preview_shapes.py FACES)
FACE_TL_TR_BL = {
    "north": ((1, 1, 0), (0, 1, 0), (1, 0, 0)), "south": ((0, 1, 1), (1, 1, 1), (0, 0, 1)),
    "west": ((0, 1, 0), (0, 1, 1), (0, 0, 0)), "east": ((1, 1, 1), (1, 1, 0), (1, 0, 1)),
    "up": ((0, 1, 0), (1, 1, 0), (0, 1, 1)), "down": ((0, 0, 1), (1, 0, 1), (0, 0, 0)),
}


# ======================================================================= colour helpers

def hsh(*parts):
    """A deterministic number in [0, 1) from anything printable."""
    return (zlib.crc32("|".join(str(p) for p in parts).encode()) & 0xFFFFFF) / float(0x1000000)


def clamp(v):
    return max(0, min(255, int(round(v))))


def mul(c, k):
    return tuple(clamp(v * k) for v in c[:3])


def add(c, d):
    return tuple(clamp(v + d) for v in c[:3])


def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# ======================================================================= the model kit

class Px:
    """One texel of a face being painted: where it is on the face and in the model."""
    __slots__ = ("el", "face", "u", "v", "W", "H", "fu", "fv", "x", "y", "z", "salt")

    def n(self, *extra):
        """Grain: a number in [0, 1) for this texel."""
        return hsh(self.salt, self.el, self.face, self.u, self.v, *extra)

    def side(self):
        """Which side of the model the face looks to: front (north), back (south), left (west), right (east), top, bottom."""
        return {"north": "front", "south": "back", "west": "left", "east": "right", "up": "top", "down": "bottom"}[self.face]


class Model:
    """Boxes with a material role per face; `paint(materials)` lays every face out in one atlas (the same layout for
    every set of materials, so variants share the shape) and paints it."""

    def __init__(self, name):
        self.name = name
        self.els = []

    def box(self, name, frm, to, role, faces=DIRS, rot=None, origin=None, roles=None):
        """role: the material of every face, or roles: {face: role} for some of them."""
        roles = dict(roles or {})
        self.els.append({"name": name, "from": list(frm), "to": list(to),
                         "roles": {f: roles.get(f, role) for f in faces}, "rot": rot, "origin": origin})
        return self

    def octa(self, name, cx, cz, w, d, y0, y1, role, ch=0.5, top=True, bottom=False, roles=None):
        """A rounded column: two crossed boxes, the wide one w by d - 2 ch, the deep one w - 2 ch by d (a chamfered
        octagon). Only the wide one carries the top and bottom; the deep one stops a hair short so they never fight."""
        f = [x for x in ("north", "east", "south", "west")]
        a_faces = f + (["up"] if top else []) + (["down"] if bottom else [])
        e = 0.02
        self.box(name + "A", (cx - w / 2, y0, cz - d / 2 + ch), (cx + w / 2, y1, cz + d / 2 - ch), role, a_faces, roles=roles)
        self.box(name + "B", (cx - w / 2 + ch, y0 + (e if bottom else 0), cz - d / 2), (cx + w / 2 - ch, y1 - (e if top else 0), cz + d / 2),
                 role, a_faces, roles=roles)
        return self

    # ---- layout

    @staticmethod
    def face_size(el, face):
        d = [el["to"][i] - el["from"][i] for i in range(3)]
        return {"north": (d[0], d[1]), "south": (d[0], d[1]), "east": (d[2], d[1]), "west": (d[2], d[1]),
                "up": (d[0], d[2]), "down": (d[0], d[2])}[face]

    def layout(self):
        """Shelf-packs every face (sizes rounded up to whole texels) into the smallest power-of-two atlas."""
        rects = []
        for i, el in enumerate(self.els):
            for face in el["roles"]:
                w, h = self.face_size(el, face)
                rects.append((max(1, math.ceil(w - 1e-6)), max(1, math.ceil(h - 1e-6)), i, face, w, h))
        rects.sort(key=lambda r: (-r[1], -r[0]))
        area = sum(r[0] * r[1] for r in rects)
        width = 16
        while width * width < area * 1.3 or width < max(r[0] for r in rects):
            width *= 2
        for width in (width, width * 2):
            place, x, y, row = {}, 0, 0, 0
            for pw, ph, i, face, w, h in rects:
                if x + pw > width:
                    x, y, row = 0, y + row, 0
                place[(i, face)] = (x, y, pw, ph, w, h)
                x += pw
                row = max(row, ph)
            height = 16
            while height < y + row:
                height *= 2
            if height <= width:
                return width, height, place
        return width, height, place

    # ---- painting

    def paint(self, materials, salt):
        width, height, place = self.layout()
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        px = img.load()
        p = Px()
        p.salt = salt
        for i, el in enumerate(self.els):
            f0, t0 = el["from"], el["to"]
            for face, role in el["roles"].items():
                x0, y0, pw, ph, w, h = place[(i, face)]
                tl, tr, bl = FACE_TL_TR_BL[face]
                corner = lambda c: [f0[k] + (t0[k] - f0[k]) * c[k] for k in range(3)]
                TL, TR, BL = corner(tl), corner(tr), corner(bl)
                mat = materials[role]
                p.el, p.face, p.W, p.H = el["name"], face, pw, ph
                for v in range(ph):
                    for u in range(pw):
                        fu = min(1.0, (u + 0.5) / max(w, 1e-6))
                        fv = min(1.0, (v + 0.5) / max(h, 1e-6))
                        p.u, p.v, p.fu, p.fv = u, v, fu, fv
                        p.x, p.y, p.z = (TL[k] + (TR[k] - TL[k]) * fu + (BL[k] - TL[k]) * fv for k in range(3))
                        c = mat(p)
                        px[x0 + u, y0 + v] = tuple(c[:3]) + (255,)
        return img

    def shape(self, texture_path):
        width, height, place = self.layout()
        els = []
        for i, el in enumerate(self.els):
            faces = {}
            for face in el["roles"]:
                x0, y0, pw, ph, w, h = place[(i, face)]
                faces[face] = {"texture": "#tex", "uv": [round(x0, 3), round(y0, 3), round(x0 + w, 3), round(y0 + h, 3)]}
            e = {"name": el["name"], "from": [round(v, 3) for v in el["from"]], "to": [round(v, 3) for v in el["to"]]}
            if el["rot"]:
                e["rotationOrigin"] = [round(v, 3) for v in (el["origin"] or [(el["from"][k] + el["to"][k]) / 2 for k in range(3)])]
                for axis, ang in zip("XYZ", el["rot"]):
                    if ang:
                        e["rotation" + axis] = ang
            e["faces"] = faces
            els.append(e)
        return {"textureWidth": width, "textureHeight": height, "textures": {"tex": texture_path}, "elements": els}


def write_shape(name, shape):
    os.makedirs(SHAPES, exist_ok=True)
    text = json.dumps(shape, indent="\t")
    # number arrays on one line, as the hand-made shapes have them
    text = re.sub(r"\[\s+([-\d.,\s]+?)\s+\]", lambda m: "[" + ", ".join(s.strip() for s in m.group(1).split(",")) + "]", text)
    text = re.sub(r"\{\s+\"texture\": \"#tex\",\s+\"uv\": (\[[^\]]*\])\s+\}", r'{ "texture": "#tex", "uv": \1 }', text)
    with open(os.path.join(SHAPES, name + ".json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def write_texture(name, img):
    os.makedirs(TEXTURES, exist_ok=True)
    img.save(os.path.join(TEXTURES, name + ".png"))


# ======================================================================= shared materials

def grain(p, c, amount=6, *salt):
    return add(c, (p.n("g", *salt) - 0.5) * 2 * amount)


def edge_shade(p, c, k=0.86):
    """The outer texel columns of a narrow upright face turn away from the light: a rounded look on a boxy column."""
    if p.face in ("up", "down") or p.W < 3:
        return c
    if p.u == 0 or p.u == p.W - 1:
        return mul(c, k)
    return c


def scuffs(p, c, rate=0.06, k=1.12):
    r = p.n("scuff")
    if r < rate / 2:
        return mul(c, k)
    if r < rate:
        return mul(c, 2 - k)
    return c


def solid(c, amount=5, k_edge=None):
    def m(p):
        out = grain(p, c, amount)
        return edge_shade(p, out, k_edge) if k_edge else out
    return m


# ======================================================================= the bottle (Almond Water and its family)

BOTTLE_TOP = 11.5
FILL = 7.6            # where the liquid stands in a full bottle (the shoulder starts at 7.5)
PLASTIC = (214, 224, 228)   # clear PET, empty, against a dim room


def bottle_model():
    m = Model("bottle")
    m.octa("Foot", 8, 8, 4.4, 4.4, 0, 0.7, "foot", ch=0.6, bottom=True)
    m.octa("Lower", 8, 8, 5, 5, 0.7, 2.2, "body")
    m.octa("Label", 8, 8, 4.7, 4.7, 2.2, 6.2, "label", top=False)
    m.octa("Upper", 8, 8, 5, 5, 6.2, 7.6, "body")
    m.octa("Shoulder", 8, 8, 4, 4, 7.6, 8.6, "shoulder")
    m.box("Neck", (7, 8.6, 7), (9, 9.9, 9), "neck", faces=("north", "east", "south", "west"))
    m.box("Ring", (6.6, 9.9, 6.6), (9.4, 10.2, 9.4), "ring")
    m.octa("Cap", 8, 8, 2.8, 2.8, 10.2, BOTTLE_TOP, "cap", ch=0.4)
    return m


def bottle_materials(liquid, cap, label=None, fill=FILL, murk=0.0, silt=None, tint=None, salt=""):
    """liquid: the colour of what is in it (None: empty); cap: the cap's colour; label: a dict (ground, band, ink, mark,
    style) or None for a bare bottle (a refill: the label soaked off long ago, a ring of glue left); murk: how much silt
    clouds it (0-1), silt: its colour; tint: the plastic's own tint for an empty bottle."""
    plastic = tint or PLASTIC

    def body(p):
        y = p.y
        if liquid is not None and y < fill:
            c = liquid
            c = mul(c, 0.9 + 0.1 * min(1.0, y / fill))           # deeper toward the bottom
            if silt and y < 1.6 + 2 * murk:
                c = mix(c, silt, 0.55 * murk + 0.25)               # settled silt
            if murk and p.n("murk") < murk * 0.35:
                c = mix(c, silt or mul(c, 0.7), 0.5)
            if fill - 0.9 < y < fill:
                c = mix(c, (250, 250, 250), 0.35)                  # the meniscus catches the light
        else:
            c = plastic
            if 0.4 < (y % 1.0) < 0.6 and p.face != "up":
                c = mul(c, 0.95)
        # the long highlight down the bottle's front-left, the shadowed back-right
        if p.face in ("north", "west") and p.u == 1 and p.W >= 4:
            c = mix(c, (255, 255, 255), 0.35)
        if p.face in ("south", "east"):
            c = mul(c, 0.96)
        c = edge_shade(p, c, 0.88)
        c = scuffs(p, c, 0.05, 1.08)
        return grain(p, c, 4)

    def foot(p):
        c = body(p)
        if p.face == "down":
            # the petaloid base: five feet round a dimple, grimy from the floors it has stood on
            d = abs(p.fu - 0.5) + abs(p.fv - 0.5)
            c = mul(c, 0.78 if d < 0.25 else 0.9)
            return grain(p, mix(c, (96, 84, 62), 0.25), 5)
        return grain(p, mix(mul(c, 0.86), (110, 98, 70), 0.12), 4)

    def shoulder(p):
        c = body(p)
        if p.face == "up":
            c = mul(c, 1.04)
        return c

    def neck(p):
        c = plastic if liquid is None or fill < 9 else liquid
        c = mul(c, 0.93 if p.v % 2 == 0 else 1.0)                 # the thread
        return grain(p, c, 3)

    def cap_m(p):
        c = cap
        if p.face == "up":
            r = max(abs(p.fu - 0.5), abs(p.fv - 0.5))
            c = mul(c, 1.08 if r > 0.38 else 0.96)                # the moulded rim, a dished top
            return scuffs(p, grain(p, c, 4), 0.08, 1.1)
        if p.face == "down":
            return mul(c, 0.7)
        c = mul(c, 1.0 if p.u % 2 == 0 else 0.82)                 # the grip ribs
        if p.v == p.H - 1:
            c = mul(c, 0.9)
        return scuffs(p, grain(p, c, 4), 0.05, 1.15)

    def ring(p):
        c = mul(cap, 0.86)
        if p.face in ("north", "east", "south", "west") and p.u % 2:
            c = mul(c, 0.9)                                        # the tamper band's bridges
        return grain(p, c, 4)

    def label_m(p):
        if label is None:
            # no label: the bottle's own body, and a dirty ring of the old glue round it
            c = body(p)
            if p.face in ("north", "east", "south", "west") and p.v in (0, p.H - 1) and p.n("glue") < 0.6:
                c = mix(c, (176, 164, 128), 0.45)
            return c
        g, band, ink = label["ground"], label["band"], label["ink"]
        if p.face in ("up", "down"):
            return grain(p, mul(g, 0.9), 3)
        v, last = p.v, p.H - 1
        side = p.side()
        wide = p.W >= 3                       # a face of the label's own (the narrow ones are the octagon's corners)
        cu = (p.W - 1) / 2.0
        c = band if v in (0, last) else g      # the coloured trims top and bottom
        if wide and 0 < v < last:
            if side == "front":
                # the brand's mark in the middle of the front: an almond, a drop, a nut
                if abs(p.u - cu) <= (1.6 if label.get("wide_mark") and v == 1 else 0.6):
                    c = label["mark"]
            elif side == "back":
                if v == 1 and p.u % 2 == 0 and 0 < p.u < p.W - 1:
                    c = mix(g, ink, 0.6)           # a barcode
            elif v == 2:
                c = mix(g, ink, 0.18)              # a line of small print
            if label.get("style") == "wave" and side != "front" and v == 1 and (p.u + p.v) % 2 == 0:
                c = mix(g, band, 0.7)              # a printed wave
        c = edge_shade(p, c, 0.9)
        # paper on a round bottle: worn at the edges, a water stain or two
        if p.n("wear") < 0.06:
            c = mix(c, (238, 230, 206), 0.45)
        if label.get("stain") and p.n("stain") < label["stain"]:
            c = mix(c, (150, 120, 70), 0.3)
        return grain(p, c, 3)

    return {"foot": foot, "body": body, "label": label_m, "shoulder": shoulder, "neck": neck, "ring": ring, "cap": cap_m}


ALMOND_LABEL = dict(ground=(232, 214, 168), band=(150, 104, 54), ink=(96, 64, 34), mark=(132, 86, 44), stain=0.06)
BOTTLES = {
    # The icon of the mod: a milky, faintly golden water, a buff label with a brown almond, the blue cap
    "almondwater": dict(liquid=(232, 226, 204), cap=(48, 94, 168), label=ALMOND_LABEL),
    # Blue: the same bottle, a cold blue water, a blue label, a navy cap
    "almondwaterblue": dict(liquid=(192, 214, 240), cap=(26, 50, 124),
                            label=dict(ground=(198, 218, 244), band=(52, 98, 182), ink=(28, 52, 110), mark=(52, 98, 182), stain=0.05)),
    # Green: a pale green water, a leafy label, a dark green cap
    "almondwatergreen": dict(liquid=(204, 230, 196), cap=(34, 96, 48),
                             label=dict(ground=(212, 232, 196), band=(72, 140, 64), ink=(36, 80, 40), mark=(72, 140, 64), stain=0.05)),
    # The Snackrooms' Cashew Water: a nutty, creamier water, a cream label with a brown band, a brown cap
    "cashewwater": dict(liquid=(226, 206, 162), cap=(110, 72, 36),
                        label=dict(ground=(240, 228, 196), band=(128, 84, 44), ink=(90, 58, 30), mark=(176, 120, 60), wide_mark=True, stain=0.04)),
    # A store bottle of water: clear, a white cap, a pale blue label with a printed wave
    "waterbottle": dict(liquid=(188, 220, 236), cap=(232, 236, 238),
                        label=dict(ground=(220, 236, 246), band=(64, 128, 196), ink=(40, 80, 140), mark=(64, 128, 196), style="wave")),
    # Refilled bottles: the label long gone
    "bottledwater-clean": dict(liquid=(194, 224, 238), cap=(228, 232, 234), label=None),
    "bottledwater-murky": dict(liquid=(148, 122, 80), cap=(112, 112, 106), label=None, murk=0.7, silt=(96, 76, 46)),
    "bottledwater-salt": dict(liquid=(158, 178, 160), cap=(206, 210, 206), label=None, murk=0.25, silt=(222, 226, 214)),
    # Empty: a scuffed, faintly cloudy bottle, a grey cap
    "emptybottle": dict(liquid=None, cap=(150, 158, 164), label=None, tint=(206, 216, 220)),
}


# ======================================================================= Level 14's stale soda (a glass bottle)

def sodabottle_model():
    m = Model("sodabottle")
    m.octa("Base", 8, 8, 4.4, 4.4, 0, 0.6, "glass", ch=0.6, bottom=True)
    m.octa("Body", 8, 8, 4.6, 4.6, 0.6, 6.0, "body", top=False)
    m.octa("Shoulder", 8, 8, 3.6, 3.6, 6.0, 7.2, "glass")
    m.box("Neck", (7.1, 7.2, 7.1), (8.9, 10.4, 8.9), "neck", faces=("north", "east", "south", "west"))
    m.box("Lip", (6.9, 10.4, 6.9), (9.1, 10.9, 9.1), "glass", faces=("north", "east", "south", "west"))
    m.box("Crown", (6.8, 10.9, 6.8), (9.2, 11.5, 9.2), "crown")
    return m


def soda_materials():
    glass, dregs = (92, 64, 34), (52, 32, 16)
    paper, pink, ink = (220, 204, 172), (184, 110, 104), (110, 46, 44)
    tide = 2.8

    def glass_m(p):
        c = dregs if p.y < tide else glass
        if abs(p.y - tide) < 0.5:
            c = (124, 86, 44)                                      # the dried tide line
        if p.face in ("north", "west") and p.u == 1:
            c = mix(c, (236, 210, 170), 0.35)                      # the glint
        c = edge_shade(p, c, 0.82)
        if p.face == "down":
            c = mul(dregs, 0.8)
        if p.face == "up":
            c = mul(glass, 1.1)
        c = scuffs(p, c, 0.1, 1.15)                                # dull and scratched
        return grain(p, mix(c, (110, 100, 86), 0.12), 5)

    def body(p):
        c = glass_m(p)
        # a paper label, faded to pink, peeling: the front still has it, the back only a torn half of it
        if 1.6 < p.y < 4.8 and p.face not in ("up", "down"):
            keep = {"front": 1.0, "left": 0.85, "right": 0.6, "back": 0.25}[p.side()]
            torn = p.fu > keep + (p.n("tear") - 0.5) * 0.3
            if not torn:
                c = pink if 2.3 < p.y < 4.1 else paper
                if p.side() == "front" and 2.9 < p.y < 3.6 and 0.3 < p.fu < 0.7:
                    c = paper                                      # a white panel where the name was
                if p.n("fade") < 0.25:
                    c = mix(c, paper, 0.4)
                if p.n("mould") < 0.08:
                    c = mix(c, (90, 96, 62), 0.5)                  # mildew spots
                c = grain(p, edge_shade(p, c, 0.88), 5)
            elif p.n("glue") < 0.3:
                c = mix(c, paper, 0.4)                             # paper fibres stuck to the glass
        return c

    def neck(p):
        c = glass if p.n("n") > 0.1 else (124, 86, 44)
        if p.face in ("north", "west") and p.u == 0:
            c = mix(c, (236, 210, 170), 0.4)
        return grain(p, mix(edge_shade(p, c, 0.85), (110, 100, 86), 0.12), 5)

    def crown(p):
        c = (176, 170, 156)
        if p.face in ("north", "east", "south", "west"):
            c = mul(c, 1.0 if p.u % 2 == 0 else 0.76)              # the crimped skirt
        elif p.face == "up":
            r = max(abs(p.fu - 0.5), abs(p.fv - 0.5))
            c = mul(c, 0.9 if r > 0.35 else 1.04)
        if p.n("rust") < 0.35:
            c = mix(c, (134, 70, 32), 0.7)                         # rusted through
        return grain(p, c, 6)

    return {"glass": glass_m, "body": body, "neck": neck, "crown": crown}


# ======================================================================= Level 94's Almond Milk (a 1950s milk bottle)

def milkbottle_model():
    m = Model("milkbottle")
    m.octa("Heel", 8, 8, 4.6, 4.6, 0, 0.6, "glass", ch=0.7, bottom=True)
    m.octa("Body", 8, 8, 5.2, 5.2, 0.6, 6.2, "body", ch=0.7, top=False)
    m.octa("Shoulder", 8, 8, 4.4, 4.4, 6.2, 7.4, "milk", ch=0.6)
    m.octa("Upper", 8, 8, 3.4, 3.4, 7.4, 8.4, "milk", ch=0.4)
    m.box("Neck", (6.8, 8.4, 6.8), (9.2, 10.2, 9.2), "milk", faces=("north", "east", "south", "west"))
    m.box("Lip", (6.5, 10.2, 6.5), (9.5, 10.7, 9.5), "glass", faces=("north", "east", "south", "west"))
    m.box("Cap", (6.6, 10.7, 6.6), (9.4, 11.1, 9.4), "cap")
    return m


def milk_materials():
    milk, glass = (246, 244, 236), (222, 232, 232)
    blue, red = (54, 104, 178), (204, 52, 48)

    def milk_m(p):
        c = milk
        if p.face in ("north", "west") and p.u == 1:
            c = (255, 255, 255)
        c = edge_shade(p, c, 0.9)
        if p.face == "up":
            c = mul(c, 0.98)
        return scuffs(p, grain(p, c, 3), 0.04, 0.94)

    def glass_m(p):
        c = mix(milk, glass, 0.6)
        if p.face == "down":
            c = mul(glass, 0.8)
        return grain(p, edge_shade(p, c, 0.88), 4)

    def body(p):
        c = milk_m(p)
        if p.face in ("up", "down"):
            return c
        # the printed band (applied colour, fired on): blue, a white star on the front, the dairy's name in white
        if 2.0 < p.y < 4.8:
            c = blue
            if p.side() == "front":
                cu = (p.W - 1) / 2.0
                if (abs(p.u - cu) < 0.6 and 2.6 < p.y < 4.2) or (abs(p.u - cu) < 1.6 and 3.0 < p.y < 3.8):
                    c = (250, 248, 240)
            elif 3.0 < p.y < 3.8 and p.n("txt") < 0.5:
                c = (238, 236, 228)
            c = edge_shade(p, c, 0.86)
            if p.n("chip") < 0.06:
                c = milk                                           # the print chipped off
            c = grain(p, c, 4)
        elif 1.4 < p.y < 2.0 or 4.8 < p.y < 5.4:
            c = mix(c, red, 0.85)                                  # red pinstripes either side
        return c

    def cap(p):
        c = red
        if p.face == "up":
            r = max(abs(p.fu - 0.5), abs(p.fv - 0.5))
            c = mul(red, 1.12 if r < 0.2 else 0.95)
            if r > 0.4:
                c = mul(red, 0.85)
        elif p.face != "down":
            c = mul(red, 0.9 if p.u % 2 else 1.0)                  # the foil's crimp
        else:
            c = mul(red, 0.6)
        return scuffs(p, grain(p, c, 6), 0.08, 1.2)

    return {"milk": milk_m, "glass": glass_m, "body": body, "cap": cap}


# ======================================================================= red water (a corked flask)

def flask_model():
    m = Model("flask")
    m.octa("Base", 8, 8, 3.8, 3.8, 0, 0.6, "glass", ch=0.6, bottom=True)
    m.octa("Body", 8, 8, 4.4, 4.4, 0.6, 4.4, "liquid", ch=0.7)
    m.octa("Shoulder", 8, 8, 3.2, 3.2, 4.4, 5.3, "liquid", ch=0.5)
    m.box("Neck", (7.25, 5.3, 7.25), (8.75, 7.4, 8.75), "neck", faces=("north", "east", "south", "west"))
    m.box("Lip", (7.0, 7.4, 7.0), (9.0, 7.8, 9.0), "glass", faces=("north", "east", "south", "west", "up"))
    m.box("Cork", (7.35, 7.8, 7.35), (8.65, 9.0, 8.65), "cork")
    m.box("Twine", (7.15, 6.6, 7.15), (8.85, 6.95, 8.85), "twine", faces=("north", "east", "south", "west"))
    m.box("Tag", (7.0, 1.4, 5.65), (9.0, 3.4, 5.8), "tag", faces=("north", "east", "west", "up", "down"), rot=(0, 0, 6), origin=(8, 2.4, 5.7))
    return m


def flask_materials():
    red, deep = (164, 22, 30), (92, 8, 16)
    glass = (214, 196, 196)

    def liquid(p):
        c = mix(deep, red, min(1.0, p.y / 4.5))
        if p.face in ("north", "west") and p.u == 1:
            c = mix(c, (255, 120, 120), 0.5)                       # the glow that lives in it
        if p.face == "up":
            c = mix(red, (220, 60, 60), 0.3)
        if p.n("bub") < 0.04:
            c = add(c, 50)
        return grain(p, edge_shade(p, c, 0.8), 6)

    def glass_m(p):
        c = mix(glass, red, 0.25) if p.face not in ("up",) else glass
        if p.face == "down":
            c = mul(deep, 1.2)
        return grain(p, edge_shade(p, c, 0.88), 4)

    def neck(p):
        c = mix(glass, red, 0.35) if p.y < 6 else glass
        if p.face in ("north", "west") and p.u == 0:
            c = add(c, 20)
        return grain(p, c, 4)

    def cork(p):
        c = (170, 128, 82)
        if p.face == "up":
            c = (186, 146, 98)
        if p.n("pore") < 0.25:
            c = mul(c, 0.78)
        if p.y < 8.1 and p.face not in ("up", "down"):
            c = mul(c, 0.7)                                        # stained where the water touched it
        return grain(p, c, 8)

    def twine(p):
        return grain(p, mul((196, 178, 140), 0.9 if p.u % 2 else 1.04), 6)

    def tag(p):
        c = (222, 210, 182)
        if p.face == "north" and p.v == 1 and 0 < p.u:
            c = (120, 30, 30)                                      # a word in red ink, by hand
        if p.face in ("east", "west"):
            c = mul(c, 0.85)
        if p.n("fox") < 0.1:
            c = mix(c, (176, 140, 90), 0.5)
        return grain(p, c, 5)

    return {"glass": glass_m, "liquid": liquid, "neck": neck, "cork": cork, "twine": twine, "tag": tag}


# ======================================================================= a tin of beans

def beancan_model():
    m = Model("beancan")
    m.octa("Seam", 8, 8, 6.2, 6.2, 0, 0.5, "rim", ch=0.9, bottom=True)
    m.octa("Can", 8, 8, 6, 6, 0.5, 6.5, "label", ch=0.9, top=False)
    m.octa("Rim", 8, 8, 6.2, 6.2, 6.5, 7.0, "rim", ch=0.9, top=False)
    m.octa("Lid", 8, 8, 5.4, 5.4, 6.5, 6.8, "lid", ch=0.8, top=True)
    # the lid sits a little below the rim: the rim's top is the ring round it
    m.box("RimN", (5.8, 6.98, 4.9), (10.2, 7.0, 5.6), "rim", faces=("up",))
    m.box("RimS", (5.8, 6.98, 10.4), (10.2, 7.0, 11.1), "rim", faces=("up",))
    m.box("RimW", (4.9, 6.98, 5.8), (5.6, 7.0, 10.2), "rim", faces=("up",))
    m.box("RimE", (10.4, 6.98, 5.8), (11.1, 7.0, 10.2), "rim", faces=("up",))
    return m


def beancan_materials():
    tin = (178, 182, 186)
    orange, cream, brown, green = (210, 104, 34), (238, 222, 184), (122, 58, 26), (64, 112, 52)

    def rim(p):
        c = tin
        if p.face in ("north", "west"):
            c = add(c, 14)
        if p.n("rust") < 0.09:
            c = mix(c, (128, 70, 38), 0.6)
        c = mul(c, 1.0 if p.u % 3 else 0.92)
        return grain(p, c, 6)

    def lid(p):
        if p.face != "up":
            return grain(p, tin, 5)
        # the lid's rings: concentric beads that catch the light, a darker well in the middle
        r = max(abs(p.fu - 0.5), abs(p.fv - 0.5)) * 2
        c = tin
        for ring, k in ((0.85, 1.12), (0.55, 0.9), (0.3, 1.08)):
            if abs(r - ring) < 0.09:
                c = mul(tin, k)
        if r < 0.2:
            c = mul(tin, 0.94)
        if p.n("rust") < 0.05:
            c = mix(c, (128, 70, 38), 0.5)
        return scuffs(p, grain(p, c, 5), 0.08, 1.1)

    def label(p):
        if p.face == "down":
            return grain(p, mul(tin, 0.8), 5)
        y = p.y
        # the paper label from 1 to 6: an orange ground, a cream window with a bowl of beans on the front, green trims
        if y < 1.0 or y > 6.0:
            c = tin
            if 0.5 < y < 0.8 or 6.2 < y < 6.5:
                c = mul(tin, 0.85)                                 # the rolled beads above and below the label
            c = edge_shade(p, c, 0.88)
            return grain(p, c, 6)
        c = orange
        if y < 1.5 or y > 5.5:
            c = green
        front = p.side() == "front"
        if front and 2.0 < y < 5.0 and p.W >= 3:
            if 0.1 < p.fu < 0.9:
                c = cream
                # the beans: brown dots in a red-brown sauce
                if 2.3 < y < 3.6:
                    c = brown if p.n("bean") < 0.6 else (176, 70, 34)
                elif 3.6 < y < 4.2:
                    c = (176, 70, 34) if p.n("sauce") < 0.3 else cream
        elif p.side() in ("left", "right") and 3.0 < y < 4.0 and p.u % 2 == 1 and p.W >= 3:
            c = mix(orange, cream, 0.75)                           # the ingredients, in small print
        elif p.side() == "back" and 2.0 < y < 4.0 and p.u % 2 == 0 and 0.2 < p.fu < 0.8 and p.W >= 3:
            c = (40, 30, 24)                                       # the barcode
        c = edge_shade(p, c, 0.86)
        if p.n("scuff") < 0.08:
            c = mix(c, (240, 230, 210), 0.45)                      # the print scuffed white
        if y < 1.6 and p.n("damp") < 0.35:
            c = mix(c, (110, 90, 60), 0.35)                        # a damp tide mark from the floor
        return grain(p, c, 5)

    return {"rim": rim, "lid": lid, "label": label}


# ======================================================================= a can of soda

def sodacan_model():
    m = Model("sodacan")
    m.octa("Base", 8, 8, 3.4, 3.4, 0, 0.6, "metal", ch=0.6, bottom=True)
    m.octa("Can", 8, 8, 4.2, 4.2, 0.6, 6.2, "print", ch=0.7, top=False)
    m.octa("Neck", 8, 8, 3.6, 3.6, 6.2, 6.9, "metal", ch=0.6)
    m.box("Tab", (7.5, 6.9, 6.8), (8.5, 7.05, 8.3), "tab", faces=("up", "north", "east", "south", "west"))
    return m


def sodacan_materials():
    red, white, metal = (192, 30, 34), (238, 234, 226), (186, 190, 196)

    def metal_m(p):
        c = metal
        if p.face == "up":
            # the lid: a rim, the opening's score line by the tab
            r = max(abs(p.fu - 0.5), abs(p.fv - 0.5))
            if r > 0.38:
                c = add(metal, 18)
            elif p.fv < 0.42 and abs(p.fu - 0.5) < 0.2:
                c = mul(metal, 0.8)
        elif p.face != "down":
            c = edge_shade(p, add(c, 8 if p.face in ("north", "west") else -6), 0.85)
        else:
            c = mul(metal, 0.75)
        return scuffs(p, grain(p, c, 5), 0.06, 1.1)

    def print_m(p):
        y = p.y
        c = red
        # a white swoosh across the can, rising round it; a white band near the top for the name
        sweep = {"front": 0.0, "right": 1.0, "back": 2.0, "left": 3.0}[p.side()]
        t = sweep + p.fu
        wave = 3.2 + 0.9 * math.sin(t * math.pi / 2)
        if abs(y - wave) < 0.45:
            c = white
        if 4.9 < y < 5.6 and p.side() == "front" and 0.2 < p.fu < 0.8:
            c = white if p.n("name") < 0.7 else red
        if y < 0.9 or y > 5.9:
            c = metal                                              # the bare aluminium at both ends
        c = edge_shade(p, c, 0.8)
        if p.face in ("north", "west") and p.u == 1:
            c = mix(c, (255, 255, 255), 0.25)                      # the shine down the front
        if p.n("dent") < 0.04:
            c = mul(c, 0.8)
        return grain(p, c, 4)

    def tab(p):
        c = (200, 204, 208)
        if p.face == "up" and 0.3 < p.fu < 0.7 and 0.5 < p.fv < 0.8:
            c = (90, 92, 96)                                       # the finger hole
        return grain(p, c, 4)

    return {"metal": metal_m, "print": print_m, "tab": tab}


# ======================================================================= a box of crackers

def crackerbox_model():
    m = Model("crackerbox")
    # upright, the front to the north; 7 wide, 9 tall, 2.6 deep
    m.box("Box", (4.5, 0, 6.7), (11.5, 8.6, 9.3), "box", faces=("north", "east", "south", "west", "down"))
    m.box("Rim", (4.5, 8.6, 6.7), (11.5, 8.8, 9.3), "edge", faces=("north", "east", "south", "west", "up"))
    # the top flap, folded back over the box's back
    m.box("Flap", (4.5, 8.8, 9.3), (11.5, 9.0, 11.8), "flap", rot=(28, 0, 0), origin=(8, 8.8, 9.3))
    # the tuck flap at the front, standing up
    m.box("Tuck", (4.7, 8.8, 6.7), (11.3, 9.9, 6.9), "flap", rot=(-14, 0, 0), origin=(8, 8.8, 6.8))
    # the wax-paper sleeve of crackers, its torn end out of the top
    m.box("Sleeve", (5.6, 7.8, 7.1), (10.4, 9.8, 8.9), "sleeve")
    m.box("Cracker", (5.9, 9.8, 7.3), (10.1, 10.2, 8.7), "cracker", faces=("up", "north", "south", "east", "west"))
    return m


def cracker_materials():
    red, cream, tan, dark = (184, 40, 34), (240, 226, 190), (214, 168, 98), (120, 26, 24)
    card = (198, 180, 150)

    def box(p):
        c = red
        if p.face == "down":
            return grain(p, mul(card, 0.8), 6)
        side = p.side()
        if side == "front":
            # the picture window: three golden crackers with their docking holes, on a cream plate
            if 0.12 < p.fu < 0.88 and 1.4 < p.y < 6.2:
                c = cream
                if 2.0 < p.y < 5.6 and 0.2 < p.fu < 0.8:
                    c = tan
                    if (p.u + int(p.y)) % 2 == 0 and p.n("dock") < 0.7:
                        c = mul(tan, 0.8)
            elif 6.8 < p.y < 7.8 and 0.15 < p.fu < 0.85:
                c = cream if p.n("name") < 0.75 else red           # the name, a cream bar
            elif p.y < 0.8:
                c = dark
        elif side == "back":
            if 1.5 < p.y < 6.5 and 0.15 < p.fu < 0.85:
                c = cream                                          # the nutrition panel: a cream box, lines of print
                if int(p.y) % 2 == 0 and 0.25 < p.fu < 0.75:
                    c = mix(cream, red, 0.6)
        elif 6.8 < p.y < 7.8:
            c = cream                                              # the cream band round the box
        elif 2.0 < p.y < 5.0 and int(p.y) % 2 == 0 and p.u == 1:
            c = mix(red, cream, 0.5)
        c = edge_shade(p, c, 0.85)
        if p.n("crush") < 0.05:
            c = mix(c, card, 0.5)                                  # rubbed through to the card
        if p.y < 1.0 and p.n("damp") < 0.3:
            c = mix(c, (100, 80, 56), 0.4)
        return grain(p, c, 5)

    def edge(p):
        if p.face == "up":
            return grain(p, mul(card, 0.6), 4)                     # looking down into the box
        return grain(p, mul(red, 0.92), 5)

    def flap(p):
        c = red if p.face in ("up", "north", "south") and p.face != "down" else card
        if p.face == "down":
            c = card
        if p.n("fold") < 0.1:
            c = mix(c, card, 0.5)
        return grain(p, c, 5)

    def sleeve(p):
        # waxed paper: translucent white, crackers showing through in bands, creased
        c = (232, 230, 220)
        if p.face in ("north", "south", "east", "west") and p.v % 2 == 1:
            c = mix(c, tan, 0.35)
        if p.n("crease") < 0.15:
            c = mul(c, 0.9)
        if p.face == "up":
            c = mix(c, tan, 0.3)
        return grain(p, c, 4)

    def cracker(p):
        c = tan
        if p.face == "up" and (p.u + p.v) % 2 == 0 and p.n("hole") < 0.6:
            c = mul(tan, 0.78)
        if p.face != "up":
            c = mul(tan, 0.9)
        if p.n("salt") < 0.1:
            c = (246, 240, 226)
        return grain(p, c, 6)

    return {"box": box, "edge": edge, "flap": flap, "sleeve": sleeve, "cracker": cracker}


# ======================================================================= a chocolate bar

def candybar_model():
    m = Model("candybar")
    # lying flat along x, 10 long, 3.6 wide, 1.2 thick; the right end torn open
    m.box("Wrapper", (3.6, 0, 6.2), (10.4, 1.2, 9.8), "wrapper")
    m.box("SealL", (2.6, 0.3, 6.0), (3.6, 0.9, 10.0), "seal", faces=("north", "south", "east", "west", "up", "down"))
    m.box("Bar", (10.4, 0.1, 6.4), (12.6, 1.0, 9.6), "choc", faces=("north", "south", "east", "up"))
    m.box("Ridge1", (10.9, 1.0, 6.6), (11.1, 1.2, 9.4), "choc", faces=("north", "south", "east", "west", "up"))
    m.box("Ridge2", (11.9, 1.0, 6.6), (12.1, 1.2, 9.4), "choc", faces=("north", "south", "east", "west", "up"))
    m.box("Foil", (10.4, 0.05, 6.3), (11.2, 0.15, 9.7), "foil", faces=("up", "north", "south", "east"))
    m.box("Torn", (10.4, 1.2, 6.3), (11.8, 1.3, 9.0), "wrapper", rot=(0, 0, 32), origin=(10.4, 1.2, 8))
    return m


def candybar_materials():
    brown, gold, red, choc = (92, 46, 26), (226, 178, 56), (184, 40, 34), (88, 50, 30)

    def wrapper(p):
        c = brown
        if p.face in ("up", "north", "south"):
            # a gold band across the middle with the name in red, a red corner flash
            along = (p.x - 3.6) / 6.8
            if 0.32 < along < 0.7:
                c = gold
                if p.face == "up" and 0.42 < along < 0.62 and 0.35 < p.fv < 0.65:
                    c = red if p.n("name") < 0.8 else gold
            elif along < 0.14 and p.face == "up":
                c = red
        elif p.face == "down":
            c = mul(brown, 0.8)
        if p.n("crinkle") < 0.12:
            c = add(c, 22)                                         # the foil-lined wrapper catches light where creased
        return grain(p, c, 5)

    def seal(p):
        c = brown if p.face != "up" else mul(brown, 1.1)
        if p.face == "up" and p.v % 2 == 0:
            c = mul(c, 0.8)                                        # the crimp
        if p.face in ("north", "south") and p.u % 2 == 0:
            c = mul(c, 0.82)
        return grain(p, c, 5)

    def choc_m(p):
        c = choc
        if p.face == "up":
            c = add(choc, 10)
        if p.n("bloom") < 0.1:
            c = mix(c, (176, 150, 130), 0.4)                      # bloom: it has been warm and cold again
        return grain(p, c, 5)

    def foil(p):
        return grain(p, mul((214, 214, 206), 1.0 if p.u % 2 else 0.88), 6)

    return {"wrapper": wrapper, "seal": seal, "choc": choc_m, "foil": foil}


# ======================================================================= a bag of chips

def chips_model():
    m = Model("chips")
    # lying flat, the bag's face up; 7.4 wide (x), 9.4 long (z), puffed in the middle
    m.box("Puff", (5.0, 0, 5.2), (11.0, 2.4, 10.8), "bag", faces=("north", "east", "south", "west", "up", "down"))
    m.box("Body", (4.3, 0.2, 4.4), (11.7, 1.8, 11.6), "bag", faces=("north", "east", "south", "west", "up", "down"))
    m.box("SealN", (4.2, 0.7, 3.4), (11.8, 1.1, 4.4), "seal")
    m.box("SealS", (4.2, 0.7, 11.6), (11.8, 1.1, 12.6), "seal")
    return m


def chips_materials():
    yellow, red, white, silver = (232, 186, 40), (196, 36, 30), (244, 238, 222), (196, 196, 190)

    def bag(p):
        c = yellow
        if p.face in ("up", "down"):
            along = (p.z - 4.4) / 7.2
            if 0.36 < along < 0.66:
                c = red                                            # the band with the name
                if p.face == "up" and 0.42 < along < 0.6 and 0.2 < p.fu < 0.8 and p.n("name") < 0.6:
                    c = white
            elif 0.7 < along < 0.9 and p.face == "up" and 0.3 < p.fu < 0.7:
                c = (214, 160, 70) if p.n("chip") < 0.7 else yellow  # a heap of chips in the picture
            if p.face == "down":
                c = mul(c, 0.86)
        else:
            c = mul(yellow, 0.95)
        if p.n("crinkle") < 0.14:
            c = mix(c, silver, 0.45)                               # the foil inside shows at the creases
        return grain(p, c, 5)

    def seal(p):
        c = mul(yellow, 0.92)
        if p.face == "up" and p.u % 2 == 0:
            c = mul(c, 0.82)                                       # the serrated crimp
        if p.face in ("north", "south") and p.u % 2 == 0:
            c = mix(c, silver, 0.4)
        return grain(p, c, 5)

    return {"bag": bag, "seal": seal}


# ======================================================================= painkillers (an amber pill bottle)

def pillbottle_model():
    m = Model("pillbottle")
    m.octa("Body", 8, 8, 3.6, 3.6, 0, 4.4, "body", ch=0.5, bottom=True, top=False)
    m.box("Neck", (6.6, 4.4, 6.6), (9.4, 4.8, 9.4), "amber", faces=("north", "east", "south", "west"))
    m.octa("Cap", 8, 8, 4.2, 4.2, 4.8, 6.3, "cap", ch=0.6)
    return m


def pill_materials():
    amber, deep, label, cap = (186, 104, 30), (120, 60, 16), (240, 238, 228), (238, 236, 230)

    def amber_m(p):
        c = amber
        if p.face in ("north", "west") and p.u == 1:
            c = mix(c, (255, 220, 160), 0.4)
        if p.n("pill") < 0.2:
            c = mix(c, (236, 228, 200), 0.35)                      # the pills inside, through the amber
        return grain(p, edge_shade(p, c, 0.8), 5)

    def body(p):
        if p.face == "down":
            return grain(p, deep, 5)
        c = amber_m(p)
        # the pharmacy label: white, a red rule, lines of print; it wraps the front and sides, not the back
        if 0.8 < p.y < 3.8 and p.side() != "back":
            c = label
            if 3.0 < p.y < 3.4:
                c = (196, 40, 40)
            elif (1.2 < p.y < 1.6 or 2.0 < p.y < 2.4) and p.n("txt") < 0.6 and 0 < p.u < p.W - 1:
                c = (70, 70, 80)
            c = edge_shade(p, c, 0.9)
            if p.n("stain") < 0.06:
                c = mix(c, (190, 170, 120), 0.4)
        return grain(p, c, 4)

    def cap_m(p):
        c = cap
        if p.face == "up":
            # PUSH DOWN & TURN: two arrows moulded in the top
            if abs(p.fv - 0.5) < 0.15 and 0.2 < p.fu < 0.8:
                c = mul(cap, 0.86)
            return grain(p, c, 4)
        if p.face == "down":
            return mul(cap, 0.7)
        c = mul(cap, 1.0 if p.u % 2 == 0 else 0.86)               # the grip
        if p.v == p.H - 1:
            c = mul(c, 0.9)
        return scuffs(p, grain(p, c, 3), 0.06, 0.9)

    return {"amber": amber_m, "body": body, "cap": cap_m}


# ======================================================================= antibiotics (a blister card)

BLISTER_POPPED = {(1, 0), (3, 1)}


def blister_model():
    m = Model("blister")
    # lying flat: the card 8 long (x) by 5.2 (z), the bubbles up; two rows of four, two pushed out
    m.box("Card", (4, 0, 5.4), (12, 0.4, 10.6), "card")
    for col in range(4):
        for row in range(2):
            x, z = 4.8 + col * 1.8, 6.2 + row * 2.2
            if (col, row) in BLISTER_POPPED:
                m.box(f"Torn{col}{row}", (x, 0.4, z), (x + 1.2, 0.5, z + 1.4), "torn", faces=("up", "north", "east", "south", "west"))
            else:
                m.box(f"Bubble{col}{row}", (x, 0.4, z), (x + 1.2, 1.1, z + 1.4), "bubble", faces=("up", "north", "east", "south", "west"))
    return m


def blister_materials():
    foil, card, print_ = (206, 208, 210), (236, 234, 226), (54, 96, 160)

    def card_m(p):
        if p.face == "down":
            # the foil back, printed with the drug's name in a repeat
            c = foil
            if p.v % 2 == 0 and p.n("print") < 0.4:
                c = mix(foil, print_, 0.6)
            return grain(p, c, 5)
        if p.face == "up":
            c = card
            # a blue stripe at the end with the name
            if p.x > 11.0:
                c = print_ if p.n("name") < 0.85 else card
            elif p.n("fox") < 0.05:
                c = mix(card, (190, 170, 130), 0.4)
            return grain(p, c, 4)
        return grain(p, mul(foil, 0.9), 4)

    def bubble(p):
        # clear plastic over a two-tone capsule: white and yellow halves
        if p.face == "up":
            c = (240, 236, 226) if p.fu < 0.5 else (230, 196, 80)
        else:
            c = (220, 222, 226)
        if p.face in ("north", "west"):
            c = add(c, 12)
        return grain(p, c, 4)

    def torn(p):
        c = mul(foil, 0.85)
        if p.face == "up" and p.n("tear") < 0.45:
            c = (70, 70, 74)                                       # the hole where the capsule came through
        return grain(p, c, 5)

    return {"card": card_m, "bubble": bubble, "torn": torn}


# ======================================================================= Epsom salt (a little heap of crystals)

SALT_CRYSTALS = [
    # (x, y, z, size, turn about y)
    (6.2, 1.0, 7.0, 1.2, 20), (8.8, 1.2, 6.6, 1.0, -30), (7.6, 1.6, 8.2, 1.3, 45), (9.6, 0.8, 8.8, 1.1, 10),
    (5.4, 0.4, 9.2, 0.9, -15), (10.4, 0.3, 6.4, 0.8, 35), (7.0, 0.5, 5.4, 0.8, 0), (8.6, 2.2, 7.6, 0.8, -40),
    (11.2, 0.0, 9.6, 0.7, 25), (4.6, 0.0, 6.6, 0.6, 10),
]


def saltheap_model():
    m = Model("saltheap")
    m.box("Heap", (5.0, 0, 5.6), (11.0, 1.0, 10.6), "heap")
    m.box("Mound", (6.2, 1.0, 6.4), (10.0, 1.8, 9.6), "heap")
    m.box("Peak", (7.2, 1.8, 7.2), (9.0, 2.4, 8.8), "heap", faces=("north", "east", "south", "west", "up"))
    for i, (x, y, z, s, ry) in enumerate(SALT_CRYSTALS):
        m.box(f"Crystal{i}", (x, y, z), (x + s, y + s * 0.9, z + s), "crystal", faces=("north", "east", "south", "west", "up"),
              rot=(0, ry, 0) if ry else None, origin=(x + s / 2, y, z + s / 2))
    return m


def salt_materials():
    white, blue = (236, 240, 242), (196, 212, 222)

    def heap(p):
        c = mix(white, blue, p.n("tone") * 0.7)
        if p.face != "up":
            c = mul(mix(c, (170, 186, 196), 0.4), 0.92)            # the heap's sides, in its own shadow
        if p.n("glint") < 0.08:
            c = (255, 255, 255)
        if p.n("grit") < 0.04:
            c = (150, 156, 160)                                    # a grain of the pool's grit
        return grain(p, c, 6)

    def crystal(p):
        c = mix(white, blue, 0.2 + 0.5 * p.n("tone"))
        if p.face == "up":
            c = add(c, 10)
        else:
            c = mul(c, 0.9)
        if (p.u + p.v) % 3 == 0 and p.face != "up":
            c = mix(c, (255, 255, 255), 0.5)                       # the facets
        return grain(p, c, 4)

    return {"heap": heap, "crystal": crystal}


# ======================================================================= food scraps (what someone else left)

def foodscraps_model():
    m = Model("foodscraps")
    # an emptied tin of beans on its side would roll; it stands, opened, its lid bent back
    m.octa("Tin", 5.6, 6.6, 4.4, 4.4, 0, 3.2, "tin", ch=0.7, bottom=True, top=False)
    m.box("Inside", (4.1, 2.9, 5.1), (7.1, 3.0, 8.1), "inside", faces=("up",))
    m.box("Lid", (3.6, 3.2, 4.4), (7.6, 3.4, 8.4), "lid", rot=(0, 0, 0), origin=(3.6, 3.2, 6.6))
    # (the lid hinged up at the west edge)
    m.els[-1]["rot"] = (0, 0, 70)
    m.els[-1]["origin"] = (3.6, 3.2, 6.6)
    # a torn cracker wrapper, crumpled flat
    m.box("Wrapper", (8.0, 0, 7.4), (13.0, 0.5, 11.4), "wrapper", rot=(0, 18, 0), origin=(10.5, 0, 9.4))
    m.box("Crumple", (9.0, 0.5, 8.4), (11.6, 1.2, 10.2), "wrapper", rot=(0, -24, 6), origin=(10.3, 0.5, 9.3))
    # crackers, broken
    m.box("Cracker1", (7.2, 0, 3.6), (9.8, 0.5, 6.0), "cracker", rot=(0, 30, 0), origin=(8.5, 0, 4.8))
    m.box("Cracker2", (10.4, 0, 4.4), (12.0, 0.5, 6.0), "cracker", rot=(0, -12, 0), origin=(11.2, 0, 5.2))
    m.box("Crumb1", (6.6, 0, 10.4), (7.3, 0.4, 11.1), "cracker")
    m.box("Crumb2", (12.4, 0, 7.0), (13.0, 0.35, 7.6), "cracker")
    return m


def foodscraps_materials():
    beans = beancan_materials()
    tan = (214, 168, 98)

    def tin(p):
        c = beans["label"](p)
        if p.y > 2.4 and p.n("rust") < 0.2:
            c = mix(c, (128, 70, 38), 0.5)
        return c

    def inside(p):
        c = (176, 70, 34) if p.n("sauce") < 0.3 else (150, 152, 156)
        return grain(p, c, 6)

    def lid(p):
        c = (186, 190, 194)
        if p.face == "up" or p.face == "down":
            r = max(abs(p.fu - 0.5), abs(p.fv - 0.5)) * 2
            if abs(r - 0.6) < 0.12:
                c = mul(c, 0.9)
            if p.face == "down" and p.n("sauce") < 0.2:
                c = (176, 70, 34)
        elif p.n("jag") < 0.5:
            c = add(c, 20)                                         # the cut edge
        return grain(p, c, 6)

    def wrapper(p):
        c = (184, 40, 34)
        if p.face in ("up",) and p.n("print") < 0.18:
            c = (240, 226, 190)
        if p.n("crease") < 0.2:
            c = mul(c, 0.84)
        if p.face == "down":
            c = (226, 222, 210)                                    # the wax lining
        return grain(p, c, 5)

    def cracker(p):
        c = tan
        if p.face == "up" and (p.u + p.v) % 2 == 0 and p.n("dock") < 0.5:
            c = mul(tan, 0.8)
        if p.face != "up":
            c = mul(tan, 0.86)
        return grain(p, c, 7)

    return {"tin": tin, "inside": inside, "lid": lid, "wrapper": wrapper, "cracker": cracker}


# ======================================================================= the items' looks

def tf(rot=(0, 0, 0), origin=(0.5, 0.5, 0.5), scale=1.0, translation=None):
    t = {}
    if translation:
        t["translation"] = dict(zip("xyz", translation))
    t["rotation"] = dict(zip("xyz", rot))
    t["origin"] = dict(zip("xyz", origin))
    t["scale"] = scale
    return t


def hand(translation, rot, scale, origin=None):
    t = {"translation": dict(zip("xyz", translation)), "rotation": dict(zip("xyz", rot))}
    if origin:
        t["origin"] = dict(zip("xyz", origin))
    t["scale"] = scale
    return t


# Items are drawn in the inventory with the screen's y axis down and no extra half turn (blocks get 180 added), so an
# upright thing takes x = 180 - 22.6 to stand the right way up, seen a little from above (as almondwater always had).
UPRIGHT = {
    "gui": lambda oy, s: tf((157.4, -45.3, 0), (0.5, oy, 0.5), s),
    # held like a bottle: upright in the palm, a little turned
    "fp": lambda s, y=0.1: hand((0, y, 0.4), (0, -30, 0), s),
    "tp": lambda s, y=-0.5: hand((-0.85, y, -0.6), (0, -45, -10), s),
    "ground": lambda s: tf((0, -45, 0), (0.5, 0, 0.5), s),
}
# Things that lie flat (a bar, a bag, a blister card): seen from higher up (50 degrees), held flat in the palm
FLAT = {
    "gui": lambda oy, s: tf((130, -45.3, 0), (0.5, oy, 0.5), s),
    "fp": lambda s, y=0.2: hand((0, y, 0.4), (0, -30, 0), s),
    "tp": lambda s, y=-0.45: hand((-0.8, y, -0.6), (0, -45, -10), s),
    "ground": lambda s: tf((0, -45, 0), (0.5, 0, 0.5), s),
}


def upright(gui_oy, gui_s, fp_s, tp_s, ground_s, fp_y=0.1, tp_y=-0.5):
    return {"guiTransform": UPRIGHT["gui"](gui_oy, gui_s), "fpHandTransform": UPRIGHT["fp"](fp_s, fp_y),
            "tpHandTransform": UPRIGHT["tp"](tp_s, tp_y), "groundTransform": UPRIGHT["ground"](ground_s)}


def flat(gui_oy, gui_s, fp_s, tp_s, ground_s, fp_y=0.2, tp_y=-0.45):
    return {"guiTransform": FLAT["gui"](gui_oy, gui_s), "fpHandTransform": FLAT["fp"](fp_s, fp_y),
            "tpHandTransform": FLAT["tp"](tp_s, tp_y), "groundTransform": FLAT["ground"](ground_s)}


BOTTLE_LOOK = upright(0.36, 2.1, 1.8, 0.7, 2.5)
# code: (shape, texture, transforms, height in blocks when set on the ground[, its scale there: the Messy12 heaps of
# small things, twelve to a block, are drawn at that size rather than their own])
LOOKS = {code: ("bottle", code, BOTTLE_LOOK, 0.72) for code in BOTTLES}
LOOKS.update({
    "l14-stalesoda": ("sodabottle", "stalesoda", BOTTLE_LOOK, 0.72),
    "almondmilk": ("milkbottle", "almondmilk", upright(0.36, 2.1, 1.8, 0.7, 2.5), 0.7),
    "redwater": ("flask", "redwater", upright(0.3, 2.6, 2.2, 0.85, 3.0), 0.56),
    "cannedbeans": ("beancan", "cannedbeans", upright(0.24, 2.1, 1.8, 0.7, 2.5), 0.44),
    "soda": ("sodacan", "soda", upright(0.24, 2.4, 2.0, 0.8, 2.8), 0.44),
    "crackers": ("crackerbox", "crackers", upright(0.32, 1.9, 1.7, 0.65, 2.4), 0.62),
    "candybar": ("candybar", "candybar", flat(0.06, 2.6, 1.9, 0.75, 2.6), 0.1),
    "chips": ("chips", "chips", flat(0.08, 2.0, 1.7, 0.7, 2.5), 0.16),
    "l14-painkillers": ("pillbottle", "painkillers", upright(0.2, 2.8, 2.2, 0.8, 3.0, fp_y=0.2, tp_y=-0.45), 0.4),
    "l14-antibiotics": ("blister", "antibiotics", flat(0.04, 2.4, 2.0, 0.75, 2.8), 0.08, 0.55),
    "epsomsalt": ("saltheap", "epsomsalt", flat(0.08, 2.6, 2.0, 0.8, 3.0), 0.16, 0.6),
    "foodscraps": ("foodscraps", "foodscraps", flat(0.12, 2.0, 1.7, 0.65, 2.4), 0.25),
})

MODELS = {
    "bottle": bottle_model, "sodabottle": sodabottle_model, "milkbottle": milkbottle_model, "flask": flask_model,
    "beancan": beancan_model, "sodacan": sodacan_model, "crackerbox": crackerbox_model, "candybar": candybar_model,
    "chips": chips_model, "pillbottle": pillbottle_model, "blister": blister_model, "saltheap": saltheap_model,
    "foodscraps": foodscraps_model,
}
MATERIALS = {
    "stalesoda": soda_materials, "almondmilk": milk_materials, "redwater": flask_materials, "cannedbeans": beancan_materials,
    "soda": sodacan_materials, "crackers": cracker_materials, "candybar": candybar_materials, "chips": chips_materials,
    "painkillers": pill_materials, "antibiotics": blister_materials, "epsomsalt": salt_materials,
    "foodscraps": foodscraps_materials,
}
MATERIALS.update({code: (lambda c=code: bottle_materials(salt=c, **BOTTLES[c])) for code in BOTTLES})


def look(code):
    """The look of an item type: its shape, texture and transforms, for the generator that writes the type.
    Returns (keys to put in the item type, the height it stands when set on the ground, in blocks)."""
    shape, tex, transforms, height = LOOKS[code][:4]
    data = {"shape": {"base": f"item/pantry/{shape}"}, "textures": {"tex": {"base": f"item/pantry/{tex}"}}}
    data.update(json.loads(json.dumps(transforms)))
    return data, height


def apply_look(data, code):
    """Puts the look of `code` into an item type dict in place (dropping a flat item's texture), and returns the height."""
    data.pop("texture", None)
    data.pop("textures", None)
    keys, height = look(code)
    data.update(keys)
    attrs = data.get("attributes")
    if isinstance(attrs, dict):
        attrs.pop("groundStorageTransform", None)     # a flat icon's; a shape stands on its own foot
    if len(LOOKS[code]) > 4:
        data.setdefault("attributes", {})["groundStorageTransform"] = {"origin": {"x": 0.5, "y": 0, "z": 0.5}, "scale": LOOKS[code][4]}
    return height


# ======================================================================= the item types with no generator of their own

def write_item(path, comment_lines, data):
    text = "".join("// " + line + "\n" for line in comment_lines) + json.dumps(data, indent="\t") + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def ground(layout, height):
    props = {"layout": layout, "collisionBox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.125, "z2": 1}}
    if height:
        props["selectionBox"] = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": height, "z2": 1}
    return {"name": "GroundStorable", "properties": props}


def own_items():
    inv = {"general": ["*"], "items": ["*"]}
    items = ASSETS + "/itemtypes/"
    data = {"code": "almondwater", "class": "BackroomsAlmondWater", "maxstacksize": 8}
    h = apply_look(data, "almondwater")
    data.update({"behaviors": [ground("Quadrants", h)], "creativeinventory": inv,
                 "nutritionProps": {"satiety": 120, "health": 1, "foodcategory": "NoNutrition"},
                 "attributes": {"hydration": 600, "satietyWhenThirst": 0, "leavesBottle": "backrooms:emptybottle"},
                 "materialDensity": 1000})
    write_item(items + "almondwater.json", [
        "Generated by tools/gen_items_pantry.py (the look) from the hand-made type: edit the generator.",
        "Almond Water: drinking it restores some Reality Stability (class BackroomsAlmondWater). Drunk like food: holding right",
        "click raises the bottle (the drink sound and hint come from the class). Thirst on: hydrates 40% of the meter, gives no",
        "satiety, leaves its bottle (the class reads the attributes)."], data)

    data = {"code": "cannedbeans", "maxstacksize": 8}
    h = apply_look(data, "cannedbeans")
    data.update({"behaviors": [ground("Quadrants", h)], "creativeinventory": inv,
                 "nutritionProps": {"satiety": 450, "foodcategory": "Protein"}, "materialDensity": 1100})
    write_item(items + "cannedbeans.json", ["Generated by tools/gen_items_pantry.py (the look) from the hand-made type: edit the generator.",
                                            "A tin of beans: the best meal the Backrooms leaves lying about."], data)

    data = {"code": "crackers", "maxstacksize": 16}
    h = apply_look(data, "crackers")
    data.update({"behaviors": [ground("Quadrants", h)], "creativeinventory": inv,
                 "nutritionProps": {"satiety": 300, "foodcategory": "Grain"}, "materialDensity": 400})
    write_item(items + "crackers.json", ["Generated by tools/gen_items_pantry.py (the look) from the hand-made type: edit the generator.",
                                         "A box of crackers."], data)

    data = {"code": "foodscraps", "maxstacksize": 32}
    h = apply_look(data, "foodscraps")
    data.update({"behaviors": [ground("Quadrants", h)], "creativeinventory": inv,
                 "nutritionProps": {"satiety": 70, "foodcategory": "Grain"}, "materialDensity": 400})
    write_item(items + "foodscraps.json", ["Generated by tools/gen_items_pantry.py (the look) from the hand-made type: edit the generator.",
                                           "Food scraps: what someone else left of a meal."], data)


# ======================================================================= main

def generate():
    built = {}
    for code, (shape, tex, *_) in LOOKS.items():
        if shape not in built:
            built[shape] = MODELS[shape]()
            write_shape(shape, built[shape].shape(f"backrooms:item/pantry/{tex}"))
        write_texture(tex, built[shape].paint(MATERIALS[tex](), tex))
    own_items()
    return built


if __name__ == "__main__":
    models = generate()
    print(f"pantry: {len(models)} shapes, {len(LOOKS)} looks")
    sys.exit(0)
