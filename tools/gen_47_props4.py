"""Level 47 round 4 (2026-11-02): the asset-quality pass's models, their textures and blocktypes.

Called from tools/gen_47.py's main (run it through the asset lock: bash tools/locked.sh run python tools/gen_47.py).

The forest: bark fillets that round the trunks', roots' and boulders' stepped outlines (`l47-fillet-*`), moss drapes on
the trunks' (mostly north) faces (`l47-mossdrape-*`), bracket fungi (`l47-bracket-*`), mushroom clumps (`l47-mushclump-*`),
the Order's carved way-stones (`l47-waystone2-*`), the fallen giants' root plates (`l47-rootearth`).
The manor: leaded windows in stone surrounds (`l47-leaded-*`), the oak door with its strap hinges, open (`l47-door-*`)
and its frame (`l47-doorjamb-*`), slate roof slopes, eaves and ridge (`l47-roof-*`), bookcases of books, scrolls and
bottles (`l47-bookcase-*`), the great hall's fire (`l47-fire`), mantel (`l47-mantel-*`), trestle table (`l47-table-*`),
benches (`l47-bench-*`), the World Snake tapestry (`l47-tapestry-*`), iron sconces (`l47-sconce-*`).

Conventions (tools/modelkit.py): block space 0-16, rotationX/Y/Z right-handed (rotationY counter-clockwise seen from
above), a "side" prop is modelled facing north and turned for the others (gen_47.ROT).
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

import matlib as M
import modelkit as K
import gen_47_tex4 as T

S = 32
SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
B = K.box


def tex(rel):
    return f"backrooms:block/47/{rel}"


def shape(els, textures):
    return {"textureWidth": 16, "textureHeight": 16, "textures": {k: tex(v) for k, v in textures.items()}, "elements": els}


def mirror_x(els):
    """Mirrors elements east-west (x -> 16 - x), swapping their east and west faces and their Y/Z rotations' sense."""
    import json
    els = json.loads(json.dumps(els))
    for e in els:
        (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
        e["from"], e["to"] = [round(16 - x2, 4), y1, z1], [round(16 - x1, 4), y2, z2]
        f = e["faces"]
        if "east" in f or "west" in f:
            ea, we = f.pop("east", None), f.pop("west", None)
            if we is not None:
                f["east"] = we
            if ea is not None:
                f["west"] = ea
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [round(16 - o[0], 4), o[1], o[2]]
            for ax in ("rotationY", "rotationZ"):
                if ax in e:
                    e[ax] = -e[ax]
    return els


# =============================== Textures ===============================

def fungus_top(seed):
    """A bracket's top: concentric zones of brown, ochre and cream, a pale growing rim (at the texture's bottom = the
    shelf's outer edge, as the shelf's up face is mapped)."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    zones = [(92, 64, 40), (124, 90, 52), (150, 116, 70), (110, 80, 50), (176, 150, 104), (200, 186, 150)]
    n = T.fbm(seed, (4, 8))
    for y in range(S):
        for x in range(S):
            r = y / S * len(zones) + 0.6 * n[y, x]
            c = zones[min(len(zones) - 1, max(0, int(r)))]
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-6, 6) + 6 * math.sin(r * 6)))
    return img


def fungus_under(seed):
    img = M.noise_hv((214, 200, 166), 4, seed, mottle=6)
    rng = random.Random(seed)
    px = img.load()
    for y in range(0, S, 2):
        for x in range((y // 2) % 2, S, 2):
            px[x, y] = M.rgba(M.lift(px[x, y], -14 + rng.uniform(-4, 4)))
    return img


def sulphur(seed):
    """Chicken-of-the-woods: lumpy sulphur-yellow shelves, orange toward the middle (the texture's top)."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    n = T.fbm(seed, (4, 8, 16))
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            t = y / S
            c = M.mix((222, 110, 40), (236, 200, 70), min(1, t * 1.4 + 0.3 * n[y, x]))
            px[x, y] = M.rgba(M.lift(c, 14 * n[y, x] + rng.uniform(-5, 5)))
    return img


def agaric_cap(seed):
    """Fly agaric: scarlet cap, orange toward its rim, white warts scattered (the model's warts stand out from it too)."""
    img = M.noise_hv((196, 30, 24), 5, seed, mottle=10, hue=4)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(18):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift((236, 226, 206), rng.uniform(-10, 4)))
        px[(x + 1) % S, y] = M.rgba(M.lift((220, 210, 190), rng.uniform(-10, 4)))
    return img


def stem(seed, base=(222, 214, 192)):
    img = M.noise_hv(base, 3, seed, mottle=5)
    rng = random.Random(seed)
    for _ in range(12):
        x = rng.randrange(S)
        for y in range(S):
            if rng.random() < 0.5:
                M.touch(img, x, y, -0.05)
    return img


def honey_cap(seed):
    img = M.noise_hv((176, 128, 58), 5, seed, mottle=10, hue=3)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(40):  # dark scales
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift((96, 64, 34), rng.uniform(-6, 6)))
    return img


def inkcap(seed):
    """Shaggy ink cap: white, shaggy upturned scales, the rim melting to black ink (the texture's bottom)."""
    img = M.noise_hv((226, 222, 210), 4, seed, mottle=6)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(60):
        x, y = rng.randrange(S), rng.randrange(S - 6)
        px[x, y] = M.rgba(M.lift((168, 150, 120), rng.uniform(-10, 10)))
    for y in range(S - 7, S):
        for x in range(S):
            k = (y - (S - 7)) / 7
            if rng.random() < 0.3 + 0.7 * k:
                px[x, y] = M.rgba(M.mix(px[x, y], (30, 28, 30), 0.4 + 0.6 * k))
    return img


def dressed_granite(seed, base=(104, 104, 100)):
    """A way-stone's dressed granite: darker than the boulders, tooled in fine diagonal strokes, the arrises chipped."""
    h = 0.6 + 0.2 * T.fbm(seed, (2, 4, 8))
    img = T.light(h, base, 0, relief=30, ao=10, grain=4, seed=seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(50):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(rng.choice([(150, 146, 140), (60, 58, 56)]), rng.uniform(-6, 6)))
    T.lichen(img, seed + 2, (160, 168, 128), n=2, rad=(1.2, 2.2))
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(3):
            M.touch(img, (x + k) % S, (y + k) % S, -0.07)
    return img


def snake_relief(seed):
    """The carved snake's body: granite cut in overlapping scale rows, the lit edges catching, kept clean of lichen."""
    img = M.noise_hv((132, 128, 118), 4, seed, mottle=6)
    px = img.load()
    for y in range(S):
        for x in range(S):
            u = (x + (y // 4 % 2) * 2) % 4
            v = y % 4
            if v == 3:
                px[x, y] = M.rgba(M.lift(px[x, y], -26))
            elif u == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], -14))
            elif v == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], 16))
    return img


def books(seed):
    """Book spines in a strip (the models pick one spine per book by its UV): leather in oxblood, green, brown, black
    and blue, gilt bands at the top and foot, a title panel; pages (cream) in the last quarter."""
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    cols = [(110, 30, 26), (54, 70, 44), (92, 62, 38), (34, 30, 30), (46, 52, 80), (124, 84, 44), (80, 26, 40), (60, 50, 34)]
    x = 0
    k = 0
    while x < 24:
        w = 3 if k % 3 else 2
        c = cols[k % len(cols)]
        for xx in range(x, x + w):
            for y in range(S):
                px = M.lift(c, rng.uniform(-6, 6) + (8 if xx == x else -10 if xx == x + w - 1 else 0))
                img.putpixel((xx, y), M.rgba(px))
        gold = M.rgba((196, 160, 70))
        for yb in (2, 3, S - 4, S - 3, 10):
            d.line([x, yb, x + w - 1, yb], fill=gold)
        d.rectangle([x, 12, x + w - 1, 17], fill=M.rgba(M.lift(c, -18)))
        x += w
        k += 1
    for xx in range(24, S):
        for y in range(S):
            img.putpixel((xx, y), M.rgba(M.lift((212, 200, 168), -6 * (y % 2) + rng.uniform(-4, 4))))
    return img


def parchment(seed):
    img = M.noise_hv((206, 190, 150), 4, seed, mottle=8)
    for y in range(0, S, 4):
        for x in range(S):
            M.touch(img, x, y, -0.06)
    return img


def bottle(seed):
    """Old bottle glass, dark green and brown, opaque here (a jar's highlight painted on)."""
    img = M.noise_hv((44, 74, 50), 4, seed, mottle=8, hue=4)
    px = img.load()
    for y in range(4, 26):
        px[3, y] = M.rgba((140, 176, 140))
        px[4, y] = M.rgba((96, 130, 100))
    return img


def bone(seed):
    img = M.noise_hv((214, 204, 176), 4, seed, mottle=6)
    M.grime(img, 0.12, seed=seed + 1, color=(150, 130, 90), cover=0.4)
    return img


def pewter(seed):
    return M.brushed_metal(seed=seed, base=(132, 134, 136), direction="h", streak=6, sheen=8)


def oak_top(seed):
    img = M.wood_planks(seed=seed, base=(92, 66, 42), planks=2, direction="h", grain=4, knots=1, joints=0)
    M.scratches(img, 8, seed + 1)
    M.stain(img, seed + 2, radius=6, color=(60, 40, 26), strength=0.3)
    return img


def oak_beam(seed):
    return M.wood_planks(seed=seed, base=(70, 50, 34), planks=1, direction="h", grain=5, contrast=1.3, knots=1)


def oak_door(seed):
    """The door's boards: vertical oak, weathered grey at the foot, the grain open."""
    img = M.wood_planks(seed=seed, base=(84, 62, 42), planks=4, direction="v", grain=5, contrast=1.2, knots=1)
    M.grime(img, 0.18, seed=seed + 1, color=(60, 56, 50), bias="bottom")
    return img


def wrought(seed):
    """Wrought iron: near black, a dull sheen on the edges, rust bleeding at the bolts."""
    img = M.noise_hv((40, 38, 38), 4, seed, mottle=6)
    M.rust(img, 0.18, seed=seed + 1)
    return img


def soot(seed):
    img = M.noise_hv((26, 24, 22), 3, seed, mottle=6)
    T.lichen(img, seed + 1, (60, 52, 46), n=3)
    return img


def ember(seed):
    img = M.noise_hv((230, 96, 24), 8, seed, mottle=16, hue=6)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(80):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(rng.choice([(255, 210, 110), (90, 30, 16), (40, 20, 14)]))
    return img


def flame_tex(seed):
    """A flame sheet: tongues of fire from the bottom, white-yellow at the root, orange and red at the tips; cut out
    (alpha 0 or 255 only)."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    n = T.fbm(seed, (4, 8))
    tongues = [rng.uniform(0.45, 0.95) for _ in range(5)]
    for y in range(S):
        for x in range(S):
            u = x / S * 5
            k = int(u)
            f = u - k
            hgt = tongues[k] * (1 - (2 * f - 1) ** 2) * S + 4 * n[y, x]
            up = S - 1 - y
            if up < hgt:
                t = up / max(1, hgt)
                c = M.mix((255, 236, 160), (240, 120, 30), min(1, t * 1.3))
                if t > 0.75:
                    c = M.mix(c, (190, 50, 20), (t - 0.75) * 4)
                px[x, y] = M.rgba(c)
    return img


def tapestry(seed, w=64, h=64):
    """The Order's tapestry: the World Snake, crimson-scaled, coiled round the world (a dark disc of forest under a
    pale moon), biting its tail, on a deep green field with a border of gold-and-crimson knots; woven texture over all."""
    img = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    field = (34, 52, 40)
    for y in range(h):
        for x in range(w):
            img.putpixel((x, y), M.rgba(M.lift(field, rng.uniform(-6, 6) + (4 if (x + y) % 2 else -4))))
    # Border
    gold, crim, dark = (196, 154, 64), (140, 24, 30), (24, 20, 18)
    d.rectangle([0, 0, w - 1, 3], fill=M.rgba(crim))
    d.rectangle([0, h - 4, w - 1, h - 1], fill=M.rgba(crim))
    d.rectangle([0, 0, 3, h - 1], fill=M.rgba(crim))
    d.rectangle([w - 4, 0, w - 1, h - 1], fill=M.rgba(crim))
    for k in range(4, w - 4, 4):
        d.point([k, 1], fill=M.rgba(gold))
        d.point([k + 1, 2], fill=M.rgba(gold))
        d.point([k, h - 2], fill=M.rgba(gold))
        d.point([k + 1, h - 3], fill=M.rgba(gold))
    for k in range(4, h - 4, 4):
        d.point([1, k], fill=M.rgba(gold))
        d.point([2, k + 1], fill=M.rgba(gold))
        d.point([w - 2, k], fill=M.rgba(gold))
        d.point([w - 3, k + 1], fill=M.rgba(gold))
    cx, cy = w / 2, h / 2 + 2
    # The world: a dark disc, trees on its rim, a moon over it
    d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], fill=M.rgba((22, 34, 26)))
    for k in range(18):
        a = k / 18 * 2 * math.pi
        tx, ty = cx + math.cos(a) * 12, cy + math.sin(a) * 12
        d.polygon([(tx + math.cos(a) * 4, ty + math.sin(a) * 4), (tx + math.cos(a + 1.4) * 1.5, ty + math.sin(a + 1.4) * 1.5),
                   (tx + math.cos(a - 1.4) * 1.5, ty + math.sin(a - 1.4) * 1.5)], fill=M.rgba((48, 74, 44)))
    d.ellipse([cx - 4, cy - 6, cx + 4, cy + 2], fill=M.rgba((212, 208, 186)))
    d.ellipse([cx - 2, cy - 4, cx, cy - 2], fill=M.rgba((176, 172, 154)))
    # The snake: a thick ring round it, scales, head biting the tail at the top
    R = 21
    for t in range(0, 360, 2):
        a = math.radians(t - 90)
        th = 4.2 if t < 330 else 4.2 * (1 - (t - 330) / 36)
        x, y = cx + math.cos(a) * R, cy + math.sin(a) * R
        d.ellipse([x - th, y - th, x + th, y + th], fill=M.rgba((156, 22, 26)))
    for t in range(0, 330, 6):
        a = math.radians(t - 90)
        for rr, c in ((R - 2, (110, 14, 20)), (R + 2, (110, 14, 20)), (R, (196, 60, 44))):
            x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
            d.point([x, y], fill=M.rgba(c))
    # (belly scales gold along the inner edge)
    for t in range(0, 330, 4):
        a = math.radians(t - 90)
        x, y = cx + math.cos(a) * (R - 3.5), cy + math.sin(a) * (R - 3.5)
        d.point([x, y], fill=M.rgba(gold))
    hx, hy = cx, cy - R
    d.ellipse([hx - 7, hy - 5, hx + 5, hy + 5], fill=M.rgba((156, 22, 26)))
    d.polygon([(hx + 4, hy - 3), (hx + 9, hy), (hx + 4, hy + 3)], fill=M.rgba((156, 22, 26)))
    d.point([hx + 1, hy - 2], fill=M.rgba((240, 210, 90)))
    d.point([hx + 2, hy - 2], fill=M.rgba(dark))
    # Stars on the field
    for _ in range(26):
        x, y = rng.randrange(6, w - 6), rng.randrange(6, h - 6)
        if math.hypot(x - cx, y - cy) > R + 6:
            d.point([x, y], fill=M.rgba((200, 196, 170)))
    # Weave and wear: a faint thread grid, a fade toward the foot, moth holes
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            dv = (-5 if y % 2 else 3) + (-3 if x % 2 else 2) - 10 * (y / h) ** 2
            px[x, y] = M.rgba(M.lift(c[:3], dv))
    for _ in range(3):
        x, y = rng.randrange(6, w - 6), rng.randrange(h // 2, h - 6)
        px[x, y] = M.rgba(dark)
    return img


def rootearth(seed):
    """A root plate's face: dark earth with roots cut through it, stones held in it."""
    img = M.noise_hv((60, 46, 34), 5, seed, mottle=10)
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    for _ in range(7):
        x, y, a = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(0, 2 * math.pi)
        w = rng.choice([1, 1, 2])
        for k in range(rng.randint(8, 18)):
            a += rng.uniform(-0.4, 0.4)
            x2, y2 = x + math.cos(a) * 1.5, y + math.sin(a) * 1.5
            for ox in (-S, 0, S):
                for oy in (-S, 0, S):
                    d.line([x + ox, y + oy, x2 + ox, y2 + oy], fill=M.rgba((120, 92, 62)), width=w)
            x, y = x2, y2
    for _ in range(10):
        x, y = rng.randrange(S), rng.randrange(S)
        d.ellipse([x, y, x + rng.randint(1, 3), y + rng.randint(1, 2)], fill=M.rgba((120, 116, 108)))
    return img


def roofslate(seed, moss=False):
    """Slate for the roof plates: courses of overlapping slates, each a little different, their lower edges lit and the
    shadow line under them (the course runs along the texture's x, the slope down its y)."""
    img = M.brick(seed=seed, base=(70, 74, 82), mortar=(30, 32, 36), course=6 if False else 8, length=8, offset=0.5, mortar_w=1,
                  jitter=12, hue=3, pits=0.03, grain=4, mottle=7)
    if moss:
        T.overgrow(img, seed + 3, cover=0.28, top_bias=-0.4)
    T.lichen(img, seed + 4, (176, 176, 140), n=2, rad=(1.5, 2.5))
    return img


# =============================== Models ===============================

# ---- The forest ----

def fillet(corner):
    """The bark chamfer for a notch whose trunk lies to the north and east (corner ne), turned for the others: a bark
    plate along the cell's diagonal (rotated 45 degrees) over a stepped fill, so the trunk's outline runs diagonally."""
    tx = {"all": "bark", "top": "top", "bottom": "top"}
    els = [B("Face", (8 - 11.3137, 0, 7.2), (8 + 11.3137, 16, 8.4), tx, rot=(0, -45, 0), origin=(8, 8, 8))]
    for k in range(3):
        els.append(B(f"Step{k}", (4 * k + 4, 0, 4 * k), (16, 16, 4 * k + 4), tx))
    turns = {"ne": 0, "se": 1, "sw": 2, "nw": 3}[corner]
    return K.turn(els, turns)


def mossdrape(design, seed):
    """Moss on a trunk's face (the face to the south of the block: the drape faces north): a mat with ragged edges in
    three depths, cushions standing off it, and strands hanging from its lower edge."""
    rng = random.Random(seed)
    els = []
    if design == "a":  # the thick collar at a trunk's foot
        y0, y1 = 0, rng.uniform(9, 13)
    else:  # a patch higher up
        y0, y1 = rng.uniform(2, 5), rng.uniform(11, 15)
    for k in range(4):
        x0 = rng.uniform(0, 4)
        x1 = rng.uniform(12, 16)
        a = y0 + rng.uniform(0, 2.5) * k
        b = y1 - rng.uniform(0, 2.5) * k
        if b - a < 2:
            continue
        depth = [1.0, 1.6, 2.2, 2.8][k]
        els.append(B(f"Mat{k}", (x0 + k * 0.8, a, 16 - depth), (x1 - k * 0.8, b, 16), "moss", faces=("north", "east", "west", "up", "down")))
    for k in range(5):
        cx, cy = rng.uniform(2, 13), rng.uniform(y0 + 1, y1 - 2)
        w, h = rng.uniform(2, 3.5), rng.uniform(1.5, 2.5)
        els.append(B(f"Cushion{k}", (cx, cy, 16 - 3.4 - rng.uniform(0, 0.6)), (cx + w, cy + h, 16 - 2), "moss", faces=("north", "east", "west", "up", "down")))
    for k in range(6 if design == "b" else 3):
        x = rng.uniform(1, 14.5)
        L = rng.uniform(1.5, 4.5)
        top = y0 + 0.5
        if top - L < 0:
            L = top
        if L < 0.6:
            continue
        els.append(B(f"Strand{k}", (x, top - L, 15.2 - rng.uniform(0, 1)), (x + 0.6, top, 15.8), "beard", faces=("north", "east", "west", "south", "down")))
    return els


def bracket(kind, seed):
    """Bracket fungus on a trunk face (the face to the south; it faces north): two or three half-round shelves, each three
    stacked plates narrowing outward (top zoned, under pale pores)."""
    rng = random.Random(seed)
    els = []
    shelves = [(rng.uniform(3, 5), 9.5, 6.0), (rng.uniform(8, 10), 7.0, 4.6), (rng.uniform(12, 13.5), 4.5, 3.2)]
    xoff = [rng.uniform(-2, 2) for _ in shelves]
    for k, (y, w, depth) in enumerate(shelves):
        cx = 8 + xoff[k]
        th = 1.6 if kind == "zoned" else 2.2
        for j, (fw, fd) in enumerate(((1.0, 0.45), (0.8, 0.8), (0.5, 1.0))):
            hw = w * fw / 2
            d = depth * fd
            els.append(B(f"Shelf{k}{j}", (cx - hw, y - j * 0.2, 16 - d), (cx + hw, y + th - j * 0.35, 16),
                         {"top": "ftop", "bottom": "funder", "side": "ftop", "front": "ftop", "back": "ftop"},
                         faces=("north", "east", "west", "up", "down")))
    return els


def mushclump(kind, seed):
    """A clump of mushrooms on the forest floor (decor; the vanilla ones are the food)."""
    rng = random.Random(seed)
    els = []
    if kind == "agaric":
        spots = [(5.0, 5.5, 8.0, 4.8), (11, 9.5, 6.0, 3.8), (5.5, 12, 3.6, 2.6)]
        for k, (x, z, h, r) in enumerate(spots):
            s = 0.8 if r > 3 else 0.6
            els.append(B(f"Stem{k}", (x - s, 0, z - s), (x + s, h, z + s), "stem"))
            els.append(B(f"Volva{k}", (x - s - 0.4, 0, z - s - 0.4), (x + s + 0.4, 0.8, z + s + 0.4), "stem"))
            els.append(B(f"Ring{k}", (x - s - 0.5, h * 0.7, z - s - 0.5), (x + s + 0.5, h * 0.7 + 0.5, z + s + 0.5), "stem"))
            els.append(B(f"Cap{k}", (x - r, h, z - r), (x + r, h + 1.2, z + r), {"all": "cap", "bottom": "gill"}))
            els.append(B(f"Dome{k}", (x - r * 0.7, h + 1.2, z - r * 0.7), (x + r * 0.7, h + 2.0, z + r * 0.7), "cap"))
            for w in range(4):
                wx, wz = x + rng.uniform(-r * 0.6, r * 0.5), z + rng.uniform(-r * 0.6, r * 0.5)
                top = h + (2.0 if abs(wx - x) < r * 0.7 - 0.5 and abs(wz - z) < r * 0.7 - 0.5 else 1.2)
                els.append(B(f"Wart{k}{w}", (wx, top, wz), (wx + 0.5, top + 0.4, wz + 0.5), "wart", faces=("north", "east", "south", "west", "up")))
    elif kind == "honey":
        # A tuft of honey fungus from one base: many small tawny caps on slender stems, leaning out
        els.append(B("Base", (5, 0, 5), (10, 1.2, 10), "stem"))
        for k in range(8):
            a = k / 8 * 2 * math.pi + rng.uniform(-0.3, 0.3)
            out = rng.uniform(1.5, 4.5)
            x, z = 7.5 + math.cos(a) * out, 7.5 + math.sin(a) * out
            h = rng.uniform(3.5, 7.5)
            r = rng.uniform(1.4, 2.4)
            lean = math.degrees(math.atan2(out, h)) * 0.6
            els.append(B(f"Stem{k}", (7.5 - 0.35, 0.5, 7.5 - 0.35), (7.5 + 0.35, 0.5 + math.hypot(h, out), 7.5 + 0.35), "stem",
                         rot=(lean * math.sin(a), 0, -lean * math.cos(a)), origin=(7.5, 0.5, 7.5)))
            els.append(B(f"Cap{k}", (x - r, h, z - r), (x + r, h + 0.8, z + r), {"all": "cap", "bottom": "gill"}))
            els.append(B(f"Boss{k}", (x - r * 0.45, h + 0.8, z - r * 0.45), (x + r * 0.45, h + 1.2, z + r * 0.45), "cap"))
    else:  # inkcap: tall shaggy bells
        for k, (x, z, h) in enumerate([(5, 6, 10.5), (10, 9.5, 8.0), (11.5, 4.5, 6.0), (5.5, 11.5, 4.5)]):
            els.append(B(f"Stem{k}", (x - 0.5, 0, z - 0.5), (x + 0.5, h * 0.55, z + 0.5), "stem"))
            r = 1.4 + h * 0.08
            els.append(B(f"Bell{k}", (x - r, h * 0.35, z - r), (x + r, h, z + r), "cap"))
            els.append(B(f"Tip{k}", (x - r * 0.65, h, z - r * 0.65), (x + r * 0.65, h + 0.8, z + r * 0.65), "cap"))
    return els


def waystone(part):
    """The Order's way-stone, two blocks: a dressed granite post on a rough footing, a snake carved in relief winding up
    it (runs of stepped scales across each face), its head lifted over the chamfered top. Faces north (the side to the
    trail)."""
    st, sn, ms = "stone", "snake", "moss"
    els = []
    lo, hi = 4.0, 12.0  # the shaft's sides
    if part == "lower":
        els.append(B("Footing", (1.5, 0, 2), (14.5, 2.5, 14), {"all": "rough", "top": ms}))
        els.append(B("Footing2", (2.5, 0, 0.8), (12, 1.6, 15.2), {"all": "rough", "top": ms}))
        els.append(B("Plinth", (3, 2.5, 3), (13, 4, 13), st))
        els.append(B("Shaft", (lo, 4, lo), (hi, 16, hi), st))
        y0, y1 = 4.5, 16.0
    else:
        els.append(B("Shaft", (lo, 0, lo), (hi, 9, hi), st))
        els.append(B("Neck", (lo + 0.5, 9, lo + 0.5), (hi - 0.5, 10, hi - 0.5), st))
        els.append(B("Cap", (lo + 1.5, 10, lo + 1.5), (hi - 1.5, 11, hi - 1.5), st))
        els.append(B("Cap2", (lo + 3, 11, lo + 3), (hi - 3, 11.8, hi - 3), st))
        y0, y1 = 0.0, 8.5
    # The snake's body: a band rising across north, east, south, west faces in turn (one turn per 1.5 blocks)
    per = 14.0  # units of rise per full turn
    start = 0.0 if part == "lower" else 16.0
    step = 0.4
    y = y0
    n = 0
    while y < y1 - 2.2:
        h = start + y
        t = (h / per) % 1.0  # where round the post
        face = int(t * 4)
        f = t * 4 - face
        a = lo - 0.2 + f * (hi - lo + 0.4)  # position along the face
        w = 3.0
        if face == 0:  # north face, running east
            frm, to = (min(a, hi - w), y, lo - 1.6), (min(a, hi - w) + w, y + 2.2, lo)
        elif face == 1:  # east face, running south
            frm, to = (hi, y, min(a, hi - w)), (hi + 1.6, y + 2.2, min(a, hi - w) + w)
        elif face == 2:  # south face, running west
            frm, to = (max(16 - a - w, lo), y, hi), (max(16 - a - w, lo) + w, y + 2.2, hi + 1.6)
        else:  # west face, running north
            frm, to = (lo - 1.6, y, max(16 - a - w, lo)), (lo, y + 2.2, max(16 - a - w, lo) + w)
        els.append(B(f"Coil{n}", frm, to, sn))
        y += step
        n += 1
    if part == "upper":
        # The head lifted over the top, facing the trail (north): neck, head, the eyes as notches
        els.append(B("RaisedNeck", (6.6, 8.0, 2.6), (9.4, 13.0, 5.4), sn))
        els.append(B("Hood", (6.0, 11.5, 2.2), (10.0, 13.2, 5.8), sn))
        els.append(B("Head", (5.8, 13.0, 0.8), (10.2, 15.4, 5.8), sn))
        els.append(B("Brow", (5.6, 15.0, 1.6), (10.4, 15.8, 4.6), sn))
        els.append(B("Snout", (6.6, 13.2, -0.6), (9.4, 14.8, 0.8), sn))
        els.append(B("Jaw", (6.4, 12.4, 0.0), (9.6, 13.2, 4.8), sn))
        els.append(B("EyeL", (5.5, 14.2, 1.8), (5.8, 14.9, 2.8), "eye", faces=("west", "north")))
        els.append(B("EyeR", (10.2, 14.2, 1.8), (10.5, 14.9, 2.8), "eye", faces=("east", "north")))
    return els


# ---- The manor ----

def leaded(part):
    """A leaded window in the wall's thickness (glass in the middle plane), axis ns (the wall runs east-west): stone jambs,
    a mullion, iron saddle bars both sides; the lower light has the sill (both faces), the upper the head and its hood
    mould; a single light has both."""
    st, gl, ir = "stone", "glass", "iron"
    els = [B("JambW", (0, 0, 0), (2, 16, 16), st), B("JambE", (14, 0, 0), (16, 16, 16), st),
           B("Mullion", (7, 0, 5), (9, 16, 11), st),
           B("GlassW", (2, 0, 7.6), (7, 16, 8.4), gl, faces=("north", "south")),
           B("GlassE", (9, 0, 7.6), (14, 16, 8.4), gl, faces=("north", "south"))]
    for y in (5, 11):
        els.append(B(f"BarN{y}", (2, y, 7.1), (14, y + 0.5, 7.6), ir, faces=("north", "up", "down")))
        els.append(B(f"BarS{y}", (2, y, 8.4), (14, y + 0.5, 8.9), ir, faces=("south", "up", "down")))
    for x in (4.25, 11.25):
        els.append(B(f"Stanchion{x}", (x, 0, 7.45), (x + 0.5, 16, 8.55), ir, faces=("north", "south", "east", "west")))
    if part in ("lower", "single"):
        els.append(B("Sill", (-0.5, 0, -1.5), (16.5, 2, 17.5), st))
        els.append(B("SillDrip", (0, -0.6, -1.5), (16, 0, -0.5), st, faces=("north", "east", "west", "down")))
    if part in ("upper", "single"):
        els.append(B("Head", (0, 13.5, 0), (16, 16, 16), st))
        els.append(B("HoodN", (-1, 14.5, -1.4), (17, 16, 0), st))
        els.append(B("HoodS", (-1, 14.5, 16), (17, 16, 17.4), st))
        els.append(B("HoodNEnd", (-1, 12.5, -1.4), (0.2, 14.5, 0), st))
        els.append(B("HoodNEnd2", (15.8, 12.5, -1.4), (17, 14.5, 0), st))
    if part == "upper":
        els.append(B("Transom", (2, 0, 5.5), (14, 1.2, 10.5), st))
    # (The jambs' and mullion's inner arrises chamfered: a thin lit strip)
    return els


def door_leaf(piece):
    """One leaf of the manor's oak door, open into the hall (lying north from its hinge along the doorway's west side):
    `piece` is near/far (the block at the hinge, the one beyond) and lower/mid/upper. The leaf: vertical boards 2 thick
    at x 0.3-2.3, three iron straps with their hinge eyes at the near end, studs, the ring handle on the far end."""
    pos, lvl = piece.split("-")
    od, ir = "door", "iron"
    els = []
    z0, z1 = (0, 16) if pos == "near" else (8, 16)  # the leaf is 24 units: the near block whole, the far block's south half
    els.append(B("Boards", (0.3, 0, z0), (2.3, 16, z1), od))
    # ledges inside (west face) and the straps outside (east face, toward the passage)
    straps = {"lower": [3.0], "mid": [8.0], "upper": [12.5]}[lvl]
    for y in straps:
        els.append(B(f"StrapE{y}", (2.3, y, z0 + (0 if pos == "far" else 0)), (2.8, y + 1.6, z1 - (0 if pos == "near" else 0.5)), ir,
                     faces=("east", "up", "down", "north", "south")))
        if pos == "near":
            els.append(B(f"Eye{y}", (1.0, y - 0.3, 14.8), (3.2, y + 1.9, 16.6), ir))
            els.append(B(f"Pintle{y}", (0.8, y - 1.2, 16.0), (1.6, y + 3.0, 16.8), ir))
        else:
            els.append(B(f"StrapEnd{y}", (2.3, y - 0.4, 8), (2.9, y + 2.0, 9.2), ir, faces=("east", "up", "down", "north", "south")))
        els.append(B(f"Ledge{y}", (-0.4, y - 1, z0 + 0.5), (0.3, y + 2.6, z1 - 0.5), od, faces=("west", "up", "down", "north", "south")))
    for k, y in enumerate((1.5, 6.0, 10.5, 15.0)):
        for z in ((3, 8, 13) if pos == "near" else (11, 14)):
            els.append(B(f"Stud{k}{z}", (2.3, y - 0.4, z - 0.4), (2.7, y + 0.4, z + 0.4), ir, faces=("east", "up", "down", "north", "south")))
    if pos == "far" and lvl == "mid":
        els.append(B("RingBoss", (2.3, 6.5, 9.4), (3.0, 8.5, 11.4), ir))
        els.append(B("Ring", (2.8, 3.6, 10.1), (3.4, 7.0, 10.7), ir, rot=(0, 0, 0)))
        els.append(B("RingFoot", (2.8, 3.4, 9.7), (3.4, 4.0, 11.1), ir))
    return els


def doorjamb(level):
    """The doorway's oak frame on its west side (the cell in the wall at the doorway's west end; mirrored for the east):
    a chamfered post, a stop, and at the top the arch's spandrel bracket (a Tudor door head)."""
    els = [B("Post", (0, 0, 2), (2.5, 16, 14), "post"), B("Stop", (2.5, 0, 5), (3.2, 16, 7), "post"),
           B("Plinth", (-0.2, 0, 1.6), (2.9, 1.4, 14.4), "stone")]
    if level == "upper":
        # The spandrel under the lintel, curving down from the head to the post: three stepped pieces and a rotated brace
        els += [B("Head", (0, 13.5, 2), (16, 16, 14), "beam"),
                B("Sp1", (2.5, 11.5, 2.5), (8, 13.5, 13.5), "beam"),
                B("Sp2", (2.5, 9.5, 2.5), (5, 11.5, 13.5), "beam"),
                B("Brace", (1.5, 9.0, 3.0), (10.5, 10.5, 13.0), "beam", rot=(0, 0, 32), origin=(2.5, 9.5, 8))]
    return els


def roof(kind):
    """The roof over a row of the manor, as the plates the slates lie on: `south` (the slope falling to the south: its high
    edge at the cell's north top, its low edge at its south foot), `south-eave` (the same over the wall's line, a fascia
    board at its foot), `ridge` (both slopes meeting in the cell, a ridge of rounded tiles). Turned for north."""
    els = []
    s = 11.3137  # half the diagonal
    if kind in ("south", "south-eave", "south-gable"):
        # Slates: a plate 2 thick whose underside lies on the diagonal, sarking boards a plate under it (the loft's ceiling)
        els.append(B("Slates", (0, 8, 8 - s), (16, 10, 8 + s), {"all": "slate", "bottom": "boards"}, rot=(45, 0, 0), origin=(8, 8, 8)))
        els.append(B("Sarking", (0.01, 6.6, 8 - s), (15.99, 7.6, 8 + s), {"all": "boards"}, rot=(45, 0, 0), origin=(8, 8, 8)))
        # (A course of slates proud of the plate every half block, so the roof has its shadow lines)
        for k, c in enumerate((-4.0, 4.0)):
            els.append(B(f"Course{k}", (0, 10, 8 + c - 1.0), (16, 10.6, 8 + c + 1.0), "slate", rot=(45, 0, 0), origin=(8, 8, 8)))
        if kind == "south-gable":  # (over the gable wall: the wall's stone filled up under the slope)
            for k in range(3):
                els.append(B(f"Infill{k}", (0, 0, 4 * k), (16, 12 - 4 * k, 4 * k + 4), "wall"))
        if kind == "south-eave":
            els.append(B("Fascia", (0, -1.5, 15.2), (16, 1.5, 16.6), "beam"))
            els.append(B("Gutter", (0, -1.0, 16.6), (16, 0.6, 18.2), "iron", faces=("south", "east", "west", "down", "up")))
    else:  # ridge
        for side, rx in (("S", 45), ("N", -45)):
            if side == "S":
                frm, to = (0, 8, 8), (16, 10, 8 + s)
            else:
                frm, to = (0, 8, 8 - s), (16, 10, 8)
            els.append(B(f"Slates{side}", frm, to, {"all": "slate", "bottom": "boards"}, rot=(rx, 0, 0), origin=(8, 8, 8)))
        els.append(B("Ridge", (0, 8.5, 6), (16, 11, 10), "ridge"))
        els.append(B("RidgeTop", (0, 11, 6.8), (16, 12, 9.2), "ridge"))
        for x in (0, 8):
            els.append(B(f"Joint{x}", (x, 8.5, 5.8), (x + 0.6, 12.1, 10.2), "ridge"))
    return els


def bookcase(part, seed):
    """A bookcase against the wall behind it (faces north): oak carcass, shelves, books of every height leaning and
    lying, scrolls in a pigeon-hole run, bottles and jars, on one shelf the snake's skull. lower: plinth and two shelves;
    upper: two shelves and the cornice."""
    rng = random.Random(seed)
    wd, bk = "oak", "books"
    els = [B("SideW", (0, 0, 3), (1.5, 16, 16), wd), B("SideE", (14.5, 0, 3), (16, 16, 16), wd),
           B("Back", (1.5, 0, 15), (14.5, 16, 16), "beam", faces=("north",))]
    shelves = [0.0, 7.5] if part == "lower" else [0.0, 8.0]
    if part == "lower":
        els.append(B("Plinth", (-0.3, 0, 2.5), (16.3, 1.6, 16), wd))
        shelves = [1.6, 8.6]
    else:
        els.append(B("Cornice", (-0.6, 14.5, 2.2), (16.6, 16, 16), wd))
        els.append(B("Frieze", (0, 13.5, 2.8), (16, 14.5, 16), wd))
    for i, y in enumerate(shelves):
        els.append(B(f"Shelf{i}", (1.5, y, 3.2), (14.5, y + 1.0, 15), wd))
        els.append(B(f"Lip{i}", (1.5, y + 1.0, 3.0), (14.5, y + 1.4, 3.4), wd, faces=("north", "up")))
        top_room = (shelves[i + 1] if i + 1 < len(shelves) else (13.5 if part == "upper" else 16)) - (y + 1.0)
        x = 1.6
        kind_row = rng.random()
        while x < 14.2:
            r = rng.random()
            if kind_row < 0.25 and r < 0.6:  # scrolls lying in a stack
                d = 1.8
                if x + d > 14.4:
                    break
                for k in range(rng.randint(2, 3)):
                    els.append(B(f"Scroll{i}{x:.1f}{k}", (x, y + 1 + k * d, 4.0), (x + d, y + 1 + (k + 1) * d, 14.5),
                                 {"all": "parch", "front": "parchend", "back": "parchend"}))
                x += d + 0.2
            elif r < 0.12:  # a bottle or a jar
                w = rng.choice([2.0, 2.6])
                h = min(top_room - 1.0, rng.uniform(4.5, 6.5))
                if x + w > 14.4:
                    break
                els.append(B(f"Bottle{i}{x:.1f}", (x, y + 1, 6.5), (x + w, y + 1 + h, 6.5 + w), "bottle"))
                if w < 2.5:
                    els.append(B(f"Neck{i}{x:.1f}", (x + 0.6, y + 1 + h, 7.1), (x + w - 0.6, y + 2.6 + h, 7.1 + w - 1.2), "bottle"))
                    els.append(B(f"Cork{i}{x:.1f}", (x + 0.5, y + 2.6 + h, 7.0), (x + w - 0.5, y + 3.2 + h, 7.0 + w - 1.0), "cork"))
                else:
                    els.append(B(f"Lid{i}{x:.1f}", (x - 0.2, y + 1 + h, 6.3), (x + w + 0.2, y + 1.6 + h, 6.7 + w), "cork"))
                x += w + 0.4
            elif r < 0.16 and part == "lower" and i == 1:  # the snake's skull
                if x + 4 > 14.4:
                    break
                els.append(B(f"Skull{i}", (x, y + 1, 6), (x + 3.4, y + 3.0, 11), "bone"))
                els.append(B(f"Snout{i}", (x + 0.7, y + 1, 4.0), (x + 2.7, y + 2.2, 6), "bone"))
                els.append(B(f"Orbit{i}", (x + 0.3, y + 2.2, 6.6), (x + 3.1, y + 3.2, 8.2), "bone"))
                x += 4.0
            else:  # a book standing, now and then one leaning or lying
                w = rng.choice([1.0, 1.0, 1.5, 1.5, 2.0])
                h = min(top_room - 0.6, rng.uniform(4.5, 6.8))
                dep = rng.uniform(8.5, 10.5)
                if x + w > 14.4:
                    break
                u0 = rng.choice([0, 2, 4, 6, 8, 10])  # which spine (books.png: spines at 0-12 units, pages at 12-16)
                spine = {"north": {"texture": "#books", "uv": [u0, 16 - h, u0 + w, 16]}}
                el = B(f"Book{i}{x:.1f}", (x, y + 1, 15 - dep), (x + w, y + 1 + h, 15), {"all": bk})
                el["faces"]["north"]["uv"] = spine["north"]["uv"]
                # (the covers the spine's leather, the top the pages' edge)
                for f in ("east", "west"):
                    el["faces"][f]["uv"] = [u0, 16 - h, u0 + w, 16]
                el["faces"]["up"]["uv"] = [12, 0, 12 + w, min(16, dep)]
                if rng.random() < 0.12 and x + h < 14.4:  # lying flat instead
                    el["from"], el["to"] = [round(x, 4), round(y + 1, 4), round(15 - dep, 4)], [round(x + h, 4), round(y + 1 + w, 4), 15]
                    x += h + 0.3
                elif rng.random() < 0.1:  # leaning
                    el["rotationOrigin"] = [round(x + w, 4), round(y + 1, 4), 10]
                    el["rotationZ"] = -14
                    x += w + 1.2
                else:
                    x += w + 0.05
                els.append(el)
    return els


def fire():
    """The great hall's fire on its hearth: two andirons (feet, upright, ball finial), three logs across them, a bed of
    embers, crossed sheets of flame; glows."""
    ir, bk, en, em, fl = "iron", "bark", "end", "ember", "flame"
    els = []
    for k, x in enumerate((3.0, 12.0)):
        els += [B(f"Foot{k}a", (x - 0.5, 0, 3), (x + 0.5, 1.0, 13), ir),
                B(f"Bar{k}", (x - 0.4, 1.0, 4), (x + 0.4, 2.0, 13), ir),
                B(f"Upright{k}", (x - 0.6, 0, 2.8), (x + 0.6, 6.0, 4.0), ir),
                B(f"Ball{k}", (x - 0.9, 6.0, 2.5), (x + 0.9, 7.6, 4.3), ir)]
    els.append(B("Embers", (1.5, 0, 4), (14.5, 1.2, 14), {"all": em}, glow=200))
    els.append(B("Log1", (1.0, 2.0, 7.0), (15.0, 4.6, 9.6), {"all": bk, "east": en, "west": en}))
    els.append(B("Log2", (2.0, 2.0, 10.5), (14.0, 4.2, 12.7), {"all": bk, "east": en, "west": en}))
    els.append(B("Log3", (4.0, 4.4, 8.2), (12.0, 6.4, 10.4), {"all": bk, "east": en, "west": en}, rot=(0, 12, 0)))
    els.append(B("Brand", (5.0, 1.2, 4.6), (11.5, 2.6, 6.0), {"all": em}, glow=180, rot=(0, -20, 0)))
    for k, (a, h) in enumerate(((35, 11), (-35, 10), (90, 9))):
        els.append(B(f"Flame{k}", (2.5, 2.0, 9.0), (13.5, 2.0 + h, 9.01), {"all": fl}, glow=255, faces=("north", "south"), rot=(0, a, 0), origin=(8, 6, 9)))
    return els


def mantel(part):
    """The hearth's mantel beam (an oak beam across the chimney breast, on stone corbels at its ends), faces north:
    part l / m / r along it; candles stand on it at the middle pieces."""
    els = [B("Beam", (0, 2, 9.5), (16, 6.5, 16), "beam"),
           B("Shelf", (0, 6.5, 8.6), (16, 7.6, 16), "beam")]
    if part == "l":
        els.append(B("Corbel", (0.5, 0, 10), (4.5, 2, 16), "stone"))
        els.append(B("Corbel2", (1.0, -2.5, 11.5), (4.0, 0, 16), "stone"))
    if part == "r":
        els.append(B("Corbel", (11.5, 0, 10), (15.5, 2, 16), "stone"))
        els.append(B("Corbel2", (12.0, -2.5, 11.5), (15.0, 0, 16), "stone"))
    if part == "m":
        for k, (x, h) in enumerate(((4.0, 5.0), (8.5, 6.5), (12.0, 4.0))):
            els.append(B(f"Stick{k}", (x - 0.9, 7.6, 11.3), (x + 0.9, 8.4, 13.1), "pewter"))
            els.append(B(f"Wax{k}", (x - 0.5, 8.4, 11.7), (x + 0.5, 8.4 + h, 12.7), "wax"))
            els.append(B(f"Drip{k}", (x - 0.65, 8.4 + h - 2.0, 11.6), (x - 0.35, 8.4 + h - 0.4, 11.9), "wax"))
            els.append(B(f"Flame{k}", (x - 0.3, 8.4 + h, 11.9), (x + 0.3, 9.6 + h, 12.5), "glow", glow=255))
    return els


def table(part):
    """A trestle table along x (its top 0.8 high: an oak board 1.6 thick on cleats): `end` (a trestle: two splayed legs on
    a foot, the long stretcher's tenon through it, a pewter candlestick lit), `mid` (top and stretcher, set with pewter
    plates, cups and a bread board), `centre` (a trestle and a candelabrum)."""
    ok, bm, pw = "oak", "beam", "pewter"
    els = [B("Top", (0, 12.6, 1.5), (16, 14.2, 14.5), {"all": ok, "bottom": bm}),
           B("Cleat", (0, 11.8, 2.5), (16, 12.6, 3.5), bm), B("Cleat2", (0, 11.8, 12.5), (16, 12.6, 13.5), bm),
           B("Stretcher", (0, 4.0, 7.2), (16, 6.0, 8.8), bm)]
    if part in ("end", "centre"):
        x = 8
        els += [B("Foot", (x - 1.2, 0, 2.5), (x + 1.2, 1.6, 13.5), bm),
                B("LegN", (x - 1.0, 1.0, 4.6), (x + 1.0, 12.0, 6.6), bm, rot=(-9, 0, 0), origin=(x, 6, 5.6)),
                B("LegS", (x - 1.0, 1.0, 9.4), (x + 1.0, 12.0, 11.4), bm, rot=(9, 0, 0), origin=(x, 6, 10.4)),
                B("Head", (x - 1.2, 10.6, 3.0), (x + 1.2, 11.8, 13.0), bm),
                B("Wedge", (x - 0.4, 3.6, 6.8), (x + 0.4, 6.4, 9.2), "beam")]
    if part == "end":
        els += [B("StickFoot", (6.5, 14.2, 6.5), (9.5, 14.8, 9.5), pw), B("StickStem", (7.5, 14.8, 7.5), (8.5, 19.0, 8.5), pw),
                B("StickPan", (6.8, 19.0, 6.8), (9.2, 19.5, 9.2), pw), B("Wax", (7.4, 19.5, 7.4), (8.6, 23.0, 8.6), "wax"),
                B("Flame", (7.7, 23.0, 7.7), (8.3, 24.3, 8.3), "glow", glow=255)]
    elif part == "centre":
        els += [B("CFoot", (5.5, 14.2, 6.0), (10.5, 14.8, 10.0), pw), B("CStem", (7.4, 14.8, 7.4), (8.6, 20.0, 8.6), pw),
                B("CArm", (3.0, 19.0, 7.5), (13.0, 19.8, 8.5), pw)]
        for k, x in enumerate((3.4, 7.4, 11.8)):
            hh = 3.4 if k != 1 else 4.4
            yb = 19.8 if k != 1 else 20.0
            els += [B(f"CPan{k}", (x - 0.4, yb, 7.0), (x + 1.6, yb + 0.5, 9.0), pw), B(f"CWax{k}", (x, yb + 0.5, 7.4), (x + 1.2, yb + 0.5 + hh, 8.6), "wax"),
                    B(f"CFlame{k}", (x + 0.3, yb + 0.5 + hh, 7.7), (x + 0.9, yb + 1.8 + hh, 8.3), "glow", glow=255)]
    else:
        for k, (x, z) in enumerate(((3.5, 3.0), (11.0, 10.5))):
            els += [B(f"Plate{k}", (x - 2.2, 14.2, z), (x + 2.2, 14.6, z + 3.6), pw), B(f"Rim{k}", (x - 1.4, 14.6, z + 0.6), (x + 1.4, 14.7, z + 3.0), pw, faces=("up",))]
            els += [B(f"Cup{k}", (x + 3.0, 14.2, z + 0.5), (x + 4.4, 16.4, z + 1.9), pw)]
        els += [B("Board", (5.5, 14.2, 9.5), (10.0, 14.8, 13.0), ok), B("Loaf", (6.3, 14.8, 10.2), (9.0, 16.4, 12.2), "bread")]
    return els


def bench(part):
    """A bench along x: an oak seat at 0.5 on splayed legs (`end`: legs and a stretcher; `mid`: the seat only, a stretcher)."""
    ok, bm = "oak", "beam"
    els = [B("Seat", (0, 7.0, 5.0), (16, 8.6, 11.0), {"all": ok, "bottom": bm}), B("Stretcher", (0, 2.5, 7.4), (16, 3.7, 8.6), bm)]
    if part == "end":
        els += [B("LegN", (7.2, 0, 5.6), (8.8, 7.2, 7.0), bm, rot=(-10, 0, 0), origin=(8, 7, 6.3)),
                B("LegS", (7.2, 0, 9.0), (8.8, 7.2, 10.4), bm, rot=(10, 0, 0), origin=(8, 7, 9.7)),
                B("Rail", (7.0, 5.6, 5.4), (9.0, 7.0, 10.6), bm)]
    return els


def tapestry_shape(cell):
    """One quarter of the World Snake tapestry (2x2 blocks), hanging on the wall to the south of the block (faces north):
    cell tl/tr/bl/br. The cloth in three vertical folds (each strip at its own depth), the rod with its finials over the
    top cells, a fringe under the bottom ones."""
    col = 0 if cell[1] == "l" else 1
    row = 0 if cell[0] == "t" else 1
    key = f"tap{cell}"
    els = []
    xs = [(0, 5.6, 14.6), (5.2, 11.0, 14.2), (10.6, 16, 14.6)]
    for k, (a, b, z) in enumerate(xs):
        els.append(B(f"Fold{k}", (a, 0 if row == 1 else 0, z), (b, 15.0 if row == 0 else 16, z + 0.4), key, faces=("north", "south", "east", "west"),
                     uv=None))
        el = els[-1]
        y0, y1 = el["from"][1], el["to"][1]
        # (A face's UV is as seen from outside it: on the north face the viewer's left is east, x = 16)
        el["faces"]["north"]["uv"] = [16 - b, 16 - y1, 16 - a, 16 - y0]
        el["faces"]["south"]["uv"] = [a, 16 - y1, b, 16 - y0]
        el["faces"]["east"]["uv"] = [0, 16 - y1, 0.4, 16 - y0]
        el["faces"]["west"]["uv"] = [15.6, 16 - y1, 16, 16 - y0]
    if row == 0:
        els.append(B("Rod", (0 if col == 1 else 1.0, 15.0, 13.8), (16 if col == 0 else 15.0, 16.0, 14.8), "iron"))
        if col == 0:
            els.append(B("Finial", (-0.6, 14.6, 13.4), (1.0, 16.4, 15.2), "iron"))
            els.append(B("Hook", (2.0, 15.6, 14.8), (3.0, 16.0, 16.0), "iron"))
        else:
            els.append(B("Finial", (15.0, 14.6, 13.4), (16.6, 16.4, 15.2), "iron"))
            els.append(B("Hook", (13.0, 15.6, 14.8), (14.0, 16.0, 16.0), "iron"))
    else:
        for k in range(16):
            x = k + 0.25
            z = 14.6 if (x < 5.4 or x > 10.8) else 14.2
            els.append(B(f"Fringe{k}", (x, 0, z), (x + 0.5, 1.2 + (k % 3) * 0.2, z + 0.4), "gold", faces=("north", "south", "east", "west")))
    return els


def chimneypot():
    """A clay chimney pot on the stack's cap (round 4): the flaunching, the pot (octagonal: two crossed boxes), its rolled rim,
    soot at its mouth."""
    return [B("Cap", (0, 0, 0), (16, 1.5, 16), "stone"), B("Flaunch", (3, 1.5, 3), (13, 3.0, 13), "stone"),
            B("PotA", (5, 3.0, 4), (11, 13, 12), "clay"), B("PotB", (4, 3.0, 5), (12, 13, 11), "clay"),
            B("RimA", (4.6, 13, 3.6), (11.4, 14.2, 12.4), "clay"), B("RimB", (3.6, 13, 4.6), (12.4, 14.2, 11.4), "clay"),
            B("Soot", (5.6, 13.6, 5.6), (10.4, 14.25, 10.4), "soot", faces=("up",))]


def streamstone(kind):
    """A stone in a stream (round 4), its top just out of the water: `step` a flat, worn stepping stone where the trail fords
    (a slab rounded at its corners, moss in its cracks), `rock` a rounded river boulder, moss on its crown."""
    g, m = {"all": "stone", "top": "stone"}, {"all": "stone", "top": "moss"}
    if kind == "step":
        return [B("Base", (1.5, 0, 2.5), (14.5, 13, 13.5), g), B("BaseX", (2.5, 0, 1.5), (13.5, 13, 14.5), g),
                B("Slab", (2.0, 13, 3.0), (14.0, 15.2, 13.0), {"all": "stone", "top": "worn"}),
                B("SlabX", (3.0, 13, 2.0), (13.0, 15.2, 14.0), {"all": "stone", "top": "worn"}),
                B("Moss1", (2.0, 15.2, 9.0), (5.0, 15.6, 12.5), "moss", faces=("up", "north", "east", "south", "west")),
                B("Moss2", (11.0, 15.2, 3.0), (13.5, 15.5, 5.5), "moss", faces=("up", "north", "east", "south", "west"))]
    return [B("Body", (2.0, 0, 2.5), (14.0, 11, 13.5), g), B("BodyX", (3.0, 0, 1.5), (13.0, 11, 14.5), g),
            B("Shoulder", (3.0, 11, 3.5), (13.0, 14.5, 12.5), g), B("Crown", (4.5, 14.5, 5.0), (11.5, 16.6, 11.0), m),
            B("CrownMoss", (4.0, 16.6, 5.5), (10.5, 17.0, 10.0), "moss", faces=("up", "north", "east", "south", "west"))]


def leafspray(form):
    """Sprays of leaves (or needles) hanging under a crown's lumps (`hang`) or standing over them (`tuft`), so a crown's
    outline breaks up into twigs instead of ending in a cube (round 4): two crossed sheets of the crown's own cut-out leaves."""
    y0, y1 = (2.5, 16) if form == "hang" else (0, 11)
    els = []
    for k, ry in enumerate((45, -45)):
        el = B(f"Sheet{k}", (8 - 11.3, y0, 8), (8 + 11.3, y1, 8.01), "leaf", faces=("north", "south"), rot=(0, ry, 0), origin=(8, 8, 8))
        for f in ("north", "south"):
            el["faces"][f]["uv"] = [0, 16 - y1, 16, 16 - y0]
        els.append(el)
    return els


def sarsentop():
    """The top of a standing stone with no lintel on it (round 4): weathered round, the rain's runnels down it."""
    m = {"all": "stone", "top": "lichen"}
    return [B("Body", (0, 0, 0), (16, 9, 16), "stone"), B("Round1", (0.8, 9, 0.6), (15.2, 12.5, 15.4), m),
            B("Round2", (2.4, 12.5, 2.0), (13.6, 14.8, 14.0), m), B("Crown", (4.5, 14.8, 4.2), (11.0, 16.0, 11.8), m),
            B("Spall", (11.0, 13.8, 10.0), (15.0, 14.6, 14.6), "stone")]


def lamppost(part):
    """A lamp post beside the walk (round 4), two blocks, facing the walk (north): a dressed footing, a chamfered oak post
    (corner strips), on the upper block a cap, a bracket arm out over the walk with its brace, and a lantern hanging from it
    on a hook: iron frame, lit glass, a cap with a ring."""
    bm, st, ir, gl = "beam", "stone", "iron", "glass"
    if part == "lower":
        return [B("Footing", (3.5, 0, 3.5), (12.5, 2.5, 12.5), {"all": st, "top": "moss"}), B("Footing2", (4.5, 2.5, 4.5), (11.5, 3.2, 11.5), st),
                B("Post", (5.5, 3.2, 5.5), (10.5, 16, 10.5), "post"),
                B("ChamferNW", (5.2, 3.6, 5.2), (6.0, 16, 6.0), "post"), B("ChamferSE", (10.0, 3.6, 10.0), (10.8, 16, 10.8), "post")]
    return [B("Post", (5.5, 0, 5.5), (10.5, 11, 10.5), "post"), B("Cap", (5.0, 11, 5.0), (11.0, 12.2, 11.0), bm), B("Cap2", (6.0, 12.2, 6.0), (10.0, 13.0, 10.0), bm),
            B("Arm", (7.0, 9.0, -2.0), (9.0, 10.6, 5.5), bm), B("ArmEnd", (6.6, 8.6, -2.6), (9.4, 11.0, -1.6), bm),
            B("Brace", (7.4, 3.0, 2.0), (8.6, 4.4, 9.0), bm, rot=(-40, 0, 0), origin=(8, 4.5, 5.5)),
            B("Hook", (7.7, 6.6, -1.4), (8.3, 9.0, -0.8), ir),
            B("LanternCap", (6.2, 5.8, -2.9), (9.8, 6.6, 0.7), ir), B("LanternTop", (7.0, 6.6, -2.1), (9.0, 7.0, -0.1), ir),
            B("Glass", (6.6, 1.6, -2.5), (9.4, 5.8, 0.3), gl, glow=200),
            B("CornerA", (6.4, 1.4, -2.7), (6.9, 5.9, -2.2), ir), B("CornerB", (9.1, 1.4, -2.7), (9.6, 5.9, -2.2), ir),
            B("CornerC", (6.4, 1.4, 0.0), (6.9, 5.9, 0.5), ir), B("CornerD", (9.1, 1.4, 0.0), (9.6, 5.9, 0.5), ir),
            B("Base", (6.2, 0.9, -2.9), (9.8, 1.6, 0.7), ir)]


def offering(kind):
    """An offering on the Altar Stone (round 4): a bronze bowl of dark water with a shed skin draped over its rim, a snake's
    skull on a cloth, or the Order's book lying open."""
    if kind == "bowl":
        return [B("Foot", (6, 0, 6), (10, 0.8, 10), "bronze"), B("Bowl", (4, 0.8, 4), (12, 3.2, 12), "bronze"),
                B("Lip", (3.4, 3.2, 3.4), (12.6, 3.8, 12.6), "bronze", faces=("north", "east", "south", "west", "down")),
                B("Water", (4.4, 3.0, 4.4), (11.6, 3.3, 11.6), "dark", faces=("up",)),
                B("Skin", (10.5, 1.5, 6.5), (13.0, 3.9, 8.0), "skin"), B("Skin2", (12.0, 0, 7.0), (13.4, 1.6, 9.5), "skin")]
    if kind == "skull":
        return [B("Cloth", (2.5, 0, 3), (13.5, 0.3, 13), "cloth"), B("Cranium", (5, 0.3, 6), (11, 3.6, 12), "bone"),
                B("Snout", (6.2, 0.3, 2.4), (9.8, 2.2, 6.0), "bone"), B("Orbit", (4.6, 2.0, 6.4), (11.4, 3.2, 8.2), "bone"),
                B("JawL", (5.0, 0.3, 3.0), (5.8, 1.0, 11.0), "bone"), B("JawR", (10.2, 0.3, 3.0), (11.0, 1.0, 11.0), "bone"),
                B("FangL", (6.6, -0.6, 2.8), (7.2, 0.6, 3.4), "bone"), B("FangR", (8.8, -0.6, 2.8), (9.4, 0.6, 3.4), "bone")]
    return [B("CoverL", (2.0, 0, 3.0), (8.0, 0.6, 13.0), "leather"), B("CoverR", (8.0, 0, 3.0), (14.0, 0.6, 13.0), "leather"),
            B("PagesL", (2.6, 0.6, 3.6), (7.9, 1.6, 12.4), {"all": "pages", "top": "script"}, rot=(0, 0, 5), origin=(8, 0.6, 8)),
            B("PagesR", (8.1, 0.6, 3.6), (13.4, 1.6, 12.4), {"all": "pages", "top": "script"}, rot=(0, 0, -5), origin=(8, 0.6, 8)),
            B("Ribbon", (7.8, 0.6, 12.4), (8.4, 0.9, 15.0), "cloth")]


def porchpost(part):
    """An oak post of the porch (round 4): a stone pad at its foot, chamfered arrises, at its head a capital and curved
    braces out to the beam both ways along it (east-west) and back to the wall (north)."""
    p = "post"
    els = [B("Post", (5.5, 0, 5.5), (10.5, 16, 10.5), p), B("ArrisA", (5.2, 0.5, 5.2), (6.0, 15.5, 6.0), p), B("ArrisB", (10.0, 0.5, 10.0), (10.8, 15.5, 10.8), p)]
    if part == "base":
        els += [B("Pad", (3.5, 0, 3.5), (12.5, 2.0, 12.5), {"all": "stone", "top": "moss"}), B("Plinth", (5.0, 2.0, 5.0), (11.0, 3.2, 11.0), p)]
    if part == "head":
        els += [B("Capital", (4.5, 13.0, 4.5), (11.5, 16, 11.5), "beam"),
                B("BraceE", (8.0, 10.5, 7.0), (16.5, 12.0, 9.0), "beam", rot=(0, 0, 35), origin=(10.5, 8.0, 8)),
                B("BraceW", (-0.5, 10.5, 7.0), (8.0, 12.0, 9.0), "beam", rot=(0, 0, -35), origin=(5.5, 8.0, 8)),
                B("BraceN", (7.0, 10.5, -0.5), (9.0, 12.0, 8.0), "beam", rot=(35, 0, 0), origin=(8, 8.0, 5.5))]
    return els


def sconce():
    """An iron candle sconce on the wall to the south (faces north): a back plate, a scrolled arm, a drip pan, a candle
    and its flame."""
    ir = "iron"
    return [B("Plate", (6.5, 5.0, 15.2), (9.5, 11.0, 16), ir), B("PlateTop", (7.2, 11.0, 15.4), (8.8, 12.0, 16), ir),
            B("Arm", (7.4, 6.4, 10.6), (8.6, 7.4, 15.2), ir), B("Curl", (7.4, 7.4, 10.6), (8.6, 8.4, 11.6), ir),
            B("Brace", (7.6, 4.0, 12.5), (8.4, 8.0, 13.3), ir, rot=(-40, 0, 0), origin=(8, 6, 14.5)),
            B("Pan", (6.0, 8.4, 9.0), (10.0, 9.0, 13.0), ir), B("Wax", (7.2, 9.0, 10.2), (8.8, 13.0, 11.8), "wax"),
            B("Drip", (7.0, 10.5, 10.6), (7.3, 12.6, 11.0), "wax"), B("Flame", (7.7, 13.0, 10.7), (8.3, 14.4, 11.3), "glow", glow=255)]


# =============================== Blocktypes ===============================

FILLET_BARKS = ["oak", "beech", "fir", "spruce", "dead", "green", "mossoak", "mossbeech", "mossfir", "mossspruce", "mossdead", "mossgreen",
                "granite", "granitemoss"]


def _snd(walk, dig):
    return {"walk": walk, "place": dig, "break": dig, "hit": dig}


WOOD = _snd("game:walk/wood*", "game:block/planks")
STONE = _snd("game:walk/stone*", "game:block/rock-hit-pickaxe")
PLANT = _snd("game:walk/grass*", "game:block/plant")
METAL = _snd("game:walk/stone*", "game:block/anvil")
CLOTH = _snd("game:walk/cloth*", "game:block/cloth")


def inv(states=None):
    return {"general": [states or "*"], "backrooms": [states or "*"]}


def box_by_side(bx):
    return {f"*-{s}": dict(bx, rotateY=ROT[s]) for s in SIDES}


def bt_side(code, comment, shape_by, textures, material, sounds, resistance, sel, coll=None, extra=None, groups=None, drops=()):
    """A prop with a side variant (and optional further groups before it); `shape_by` maps a wildcard of the other groups
    to a shape path, or is a single path."""
    groups = (groups or []) + [{"code": "side", "states": SIDES}]
    b = {"code": code, "variantgroups": groups, "creativeinventory": inv("*-north"), "blockmaterial": material, "drawtype": "json",
         "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": resistance,
         "drops": list(drops), "sounds": sounds, "textures": {k: {"base": tex(v)} for k, v in textures.items()}}
    if isinstance(shape_by, str):
        b["shapeByType"] = {f"*-{s}": {"base": f"block/47/{shape_by}", "rotateY": ROT[s]} for s in SIDES}
    else:
        b["shapeByType"] = {f"{pat}-{s}": {"base": f"block/47/{path}", "rotateY": ROT[s]} for pat, path in shape_by.items() for s in SIDES}
    b["selectionboxByType"] = box_by_side(sel)
    if coll is None:
        b["collisionbox"] = None
    else:
        b["collisionboxByType"] = box_by_side(coll)
    if extra:
        b.update(extra)
    return comment, b


def blocktypes():
    out = []
    # ---- Fillets ----
    tb = {}
    for k in FILLET_BARKS:
        if k.startswith("granite"):
            side = "block/47/granite-moss" if k == "granitemoss" else "block/47/granite"
            top = "block/47/moss" if k == "granitemoss" else "block/47/granite"
        elif k.startswith("moss"):
            w = k[4:]
            side, top = f"block/47/mossbark-{w}", "block/47/moss"
        else:
            side, top = f"block/47/bark-{k}", f"block/47/rings-{k}"
        tb[f"*-{k}-*"] = {"bark": {"base": side}, "top": {"base": top}}
    corners = {"ne": (0.5, 0, 1, 0.5), "se": (0.5, 0.5, 1, 1), "sw": (0, 0.5, 0.5, 1), "nw": (0, 0, 0.5, 0.5)}
    out.append(("// Level 47 (round 4): the bark (or granite) chamfer in a notch of a trunk's, root's or boulder's stepped outline, so it reads round", {
        "code": "l47-fillet", "variantgroups": [{"code": "bark", "states": FILLET_BARKS}, {"code": "corner", "states": list(corners)}],
        "creativeinventory": inv("*-oak-ne"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{c}": {"base": f"block/47/fillet-{c}"} for c in corners}, "texturesByType": tb,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 6, "faceCullMode": "NeverCull",
        "collisionboxByType": {f"*-{c}": {"x1": a, "y1": 0, "z1": b, "x2": c2, "y2": 1, "z2": d} for c, (a, b, c2, d) in corners.items()},
        "selectionboxByType": {f"*-{c}": {"x1": a, "y1": 0, "z1": b, "x2": c2, "y2": 1, "z2": d} for c, (a, b, c2, d) in corners.items()},
        "drops": [{"type": "item", "code": "game:firewood", "quantity": {"avg": 0.3, "var": 0.3}}], "sounds": WOOD}))
    # ---- Moss drapes, brackets, mushrooms ----
    out.append(bt_side("l47-mossdrape", "// Level 47 (round 4): moss grown over a trunk's face, ragged, strands hanging (a: the collar at the foot; b: a patch higher up)",
                       {"*-a": "mossdrape-a", "*-b": "mossdrape-b"}, {"moss": "moss", "beard": "beard"}, "Plant", PLANT, 0.4,
                       {"x1": 0, "y1": 0, "z1": 0.8, "x2": 1, "y2": 1, "z2": 1}, groups=[{"code": "design", "states": ["a", "b"]}],
                       drops=[{"type": "item", "code": "game:drygrass", "quantity": {"avg": 0.3, "var": 0.3}}]))
    out.append(bt_side("l47-bracket", "// Level 47 (round 4): bracket fungus on a trunk (zoned: turkey-tail browns; sulphur: chicken-of-the-woods)",
                       {"*-zoned": "bracket-zoned", "*-sulphur": "bracket-sulphur"}, {}, "Plant", PLANT, 0.4,
                       {"x1": 0.15, "y1": 0.15, "z1": 0.6, "x2": 0.85, "y2": 0.95, "z2": 1}, groups=[{"code": "kind", "states": ["zoned", "sulphur"]}],
                       extra={"texturesByType": {"*-zoned-*": {"ftop": {"base": tex("fungus-top")}, "funder": {"base": tex("fungus-under")}},
                                                 "*-sulphur-*": {"ftop": {"base": tex("sulphur")}, "funder": {"base": tex("sulphur")}}}}))
    out[-1][1].pop("textures")
    out.append(("// Level 47 (round 4): a clump of mushrooms on the forest floor (decor: the vanilla mushrooms are the ones to eat)", {
        "code": "l47-mushclump", "variantgroups": [{"code": "kind", "states": ["agaric", "honey", "inkcap"]}], "creativeinventory": inv(),
        "blockmaterial": "Plant", "drawtype": "json", "shapeByType": {f"*-{k}": {"base": f"block/47/mush-{k}"} for k in ("agaric", "honey", "inkcap")},
        "texturesByType": {"*-agaric": {"cap": {"base": tex("agaric-cap")}, "gill": {"base": tex("stem")}, "stem": {"base": tex("stem")}, "wart": {"base": tex("wax")}},
                           "*-honey": {"cap": {"base": tex("honey-cap")}, "gill": {"base": tex("fungus-under")}, "stem": {"base": tex("honey-stem")}},
                           "*-inkcap": {"cap": {"base": tex("inkcap")}, "stem": {"base": tex("stem")}}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.2, "collisionbox": None,
        "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.5, "z2": 0.9}, "replaceable": 3000, "drops": [], "sounds": PLANT}))
    # ---- Way-stone ----
    out.append(bt_side("l47-waystone2", "// Level 47 (round 4): the Order's way-stone, a dressed granite post with the snake carved coiling up it, its head over the top (our invention)",
                       {"*-lower": "waystone-lower", "*-upper": "waystone-upper"},
                       {"stone": "waystone-dressed", "snake": "waystone-snake", "rough": "granite", "moss": "moss", "eye": "iron"}, "Stone", STONE, 12,
                       {"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 1, "z2": 0.85}, coll={"x1": 0.2, "y1": 0, "z1": 0.2, "x2": 0.8, "y2": 1, "z2": 0.8},
                       groups=[{"code": "part", "states": ["lower", "upper"]}], drops=[{"type": "item", "code": "game:stone-granite", "quantity": {"avg": 2, "var": 1}}]))
    # ---- Manor ----
    win = {"lower": "leaded-lower", "upper": "leaded-upper", "single": "leaded-single"}
    out.append(("// Level 47 (round 4): the manor's leaded windows in their stone surrounds (part lower/upper/single, axis of the wall)", {
        "code": "l47-leaded", "variantgroups": [{"code": "part", "states": list(win)}, {"code": "axis", "states": ["ns", "ew"]}],
        "creativeinventory": inv("*-ns"), "blockmaterial": "Glass", "drawtype": "json", "renderpass": "OpaqueNoCull", "faceCullMode": "NeverCull",
        "shapeByType": {f"*-{p}-{a}": {"base": f"block/47/{v}", "rotateY": 0 if a == "ns" else 90} for p, v in win.items() for a in ("ns", "ew")},
        "textures": {"stone": {"base": tex("manorstone-dressed")}, "glass": {"base": tex("leaded-glass")}, "iron": {"base": tex("iron")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 8, "drops": [],
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}}))
    leaves = [f"{p}-{l}" for p in ("near", "far") for l in ("lower", "mid", "upper")]
    out.append(("// Level 47 (round 4): the manor's oak door, iron-strapped, open into the hall (leaf west/east, piece near/far at lower/mid/upper)", {
        "code": "l47-door", "variantgroups": [{"code": "leaf", "states": ["west", "east"]}, {"code": "piece", "states": leaves}],
        "creativeinventory": inv("*-west-near-mid"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{lf}-{p}": {"base": f"block/47/door-{lf}-{p}"} for lf in ("west", "east") for p in leaves},
        "textures": {"door": {"base": tex("door")}, "iron": {"base": tex("wrought")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 5,
        "collisionboxByType": {"*-west-*": {"x1": 0, "y1": 0, "z1": 0, "x2": 0.18, "y2": 1, "z2": 1}, "*-east-*": {"x1": 0.82, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
        "selectionboxByType": {"*-west-*": {"x1": 0, "y1": 0, "z1": 0, "x2": 0.18, "y2": 1, "z2": 1}, "*-east-*": {"x1": 0.82, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
        "drops": [{"type": "item", "code": "game:firewood", "quantity": {"avg": 1, "var": 0.5}}], "sounds": WOOD}))
    out.append(("// Level 47 (round 4): the door's oak frame, a Tudor head (side west/east of the doorway, level lower/upper)", {
        "code": "l47-doorjamb", "variantgroups": [{"code": "leaf", "states": ["west", "east"]}, {"code": "level", "states": ["lower", "upper"]}],
        "creativeinventory": inv("*-west-upper"), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{lf}-{l}": {"base": f"block/47/doorjamb-{lf}-{l}"} for lf in ("west", "east") for l in ("lower", "upper")},
        "textures": {"beam": {"base": tex("oak-beam")}, "post": {"base": tex("oak-post")}, "stone": {"base": tex("manorstone-dressed")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 6,
        "collisionboxByType": {"*-west-*": {"x1": 0, "y1": 0, "z1": 0, "x2": 0.2, "y2": 1, "z2": 1}, "*-east-*": {"x1": 0.8, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
        "selectionboxByType": {"*-west-*": {"x1": 0, "y1": 0, "z1": 0, "x2": 0.2, "y2": 1, "z2": 1}, "*-east-*": {"x1": 0.8, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}},
        "drops": [], "sounds": WOOD}))
    kinds = ["slope", "eave", "ridge", "gable"]
    out.append(("// Level 47 (round 4): the manor's slate roof: slopes (falling to the side), the eaves with fascia and gutter, the ridge; the north slope mossed", {
        "code": "l47-roof", "variantgroups": [{"code": "kind", "states": kinds}, {"code": "side", "states": ["north", "south"]}],
        "creativeinventory": inv("*-south"), "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {f"*-{k}-{s}": {"base": f"block/47/roof-{'south' if k == 'slope' else 'south-eave' if k == 'eave' else 'south-gable' if k == 'gable' else 'ridge'}", "rotateY": 0 if s == "south" else 180}
                        for k in kinds for s in ("north", "south")},
        "texturesByType": {"*-north": {"slate": {"base": tex("roofslate-moss")}, "boards": {"base": tex("boards")}, "beam": {"base": tex("oak-beam")},
                                       "iron": {"base": tex("wrought")}, "ridge": {"base": tex("ridge")}, "wall": {"base": tex("manorstone")}},
                           "*-south": {"slate": {"base": tex("roofslate")}, "boards": {"base": tex("boards")}, "beam": {"base": tex("oak-beam")},
                                       "iron": {"base": tex("wrought")}, "ridge": {"base": tex("ridge")}, "wall": {"base": tex("manorstone")}}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 6, "faceCullMode": "NeverCull",
        "drops": [], "sounds": STONE}))
    out.append(bt_side("l47-bookcase", "// Level 47 (round 4): the Order's bookcases: books in no language you know, scrolls, bottles, a snake's skull",
                       {"*-lower-a": "bookcase-lower-a", "*-lower-b": "bookcase-lower-b", "*-upper-a": "bookcase-upper-a", "*-upper-b": "bookcase-upper-b"},
                       {"oak": "oak-top", "beam": "oak-beam", "books": "books", "parch": "parchment", "parchend": "parchment-end", "bottle": "bottle",
                        "cork": "cork", "bone": "bone"}, "Wood", WOOD, 3,
                       {"x1": 0, "y1": 0, "z1": 0.15, "x2": 1, "y2": 1, "z2": 1}, coll={"x1": 0, "y1": 0, "z1": 0.15, "x2": 1, "y2": 1, "z2": 1},
                       groups=[{"code": "part", "states": ["lower", "upper"]}, {"code": "design", "states": ["a", "b"]}],
                       drops=[{"type": "item", "code": "game:paper-parchment", "quantity": {"avg": 0.5, "var": 0.5}},
                              {"type": "item", "code": "game:firewood", "quantity": {"avg": 0.5, "var": 0.3}}]))
    out.append(bt_side("l47-fire", "// Level 47 (round 4): the great hall's fire: andirons, logs, embers, flames (kept by the Order); faces the room", "fire",
                       {"iron": "wrought", "bark": "bark-oak", "end": "rings-oak", "ember": "ember", "flame": "flame-sheet"}, "Metal", METAL, 3,
                       {"x1": 0.05, "y1": 0, "z1": 0.15, "x2": 0.95, "y2": 0.6, "z2": 0.9}, coll={"x1": 0.05, "y1": 0, "z1": 0.15, "x2": 0.95, "y2": 0.45, "z2": 0.9},
                       extra={"lightHsv": [5, 6, 15]}))
    out.append(bt_side("l47-mantel", "// Level 47 (round 4): the hearth's mantel beam on its corbels, candles on it (part l/m/r)",
                       {"*-l": "mantel-l", "*-m": "mantel-m", "*-r": "mantel-r"},
                       {"beam": "oak-beam", "stone": "manorstone-dressed", "pewter": "pewter", "wax": "wax", "glow": "flame"}, "Wood", WOOD, 6,
                       {"x1": 0, "y1": 0, "z1": 0.5, "x2": 1, "y2": 1, "z2": 1}, coll={"x1": 0, "y1": 0.1, "z1": 0.55, "x2": 1, "y2": 0.5, "z2": 1},
                       groups=[{"code": "part", "states": ["l", "m", "r"]}],
                       extra={"lightHsvByType": {"*-m-*": [8, 5, 8]}}))
    tparts = ["end", "mid", "centre"]
    out.append(("// Level 47 (round 4): the great hall's trestle table, set (along x: end with a candlestick, mid with plates, centre with a candelabrum)", {
        "code": "l47-table", "variantgroups": [{"code": "part", "states": tparts}], "creativeinventory": inv(), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{p}": {"base": f"block/47/table-{p}"} for p in tparts},
        "textures": {"oak": {"base": tex("oak-top")}, "beam": {"base": tex("oak-beam")}, "pewter": {"base": tex("pewter")}, "wax": {"base": tex("wax")},
                     "glow": {"base": tex("flame")}, "bread": {"base": tex("bread")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 4,
        "lightHsvByType": {"*-end": [8, 5, 9], "*-centre": [8, 5, 11]},
        "collisionbox": {"x1": 0, "y1": 0, "z1": 0.1, "x2": 1, "y2": 0.9, "z2": 0.9}, "selectionbox": {"x1": 0, "y1": 0, "z1": 0.1, "x2": 1, "y2": 0.9, "z2": 0.9},
        "drops": [{"type": "item", "code": "game:firewood", "quantity": {"avg": 1, "var": 0.5}}], "sounds": WOOD}))
    out.append(("// Level 47 (round 4): a bench along x (end: legs; mid: the seat)", {
        "code": "l47-bench", "variantgroups": [{"code": "part", "states": ["end", "mid"]}], "creativeinventory": inv(), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{p}": {"base": f"block/47/bench-{p}"} for p in ("end", "mid")},
        "textures": {"oak": {"base": tex("oak-top")}, "beam": {"base": tex("oak-beam")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 3,
        "collisionbox": {"x1": 0, "y1": 0, "z1": 0.3, "x2": 1, "y2": 0.55, "z2": 0.7}, "selectionbox": {"x1": 0, "y1": 0, "z1": 0.3, "x2": 1, "y2": 0.55, "z2": 0.7},
        "drops": [{"type": "item", "code": "game:firewood", "quantity": {"avg": 0.5, "var": 0.3}}], "sounds": WOOD}))
    cells = ["tl", "tr", "bl", "br"]
    out.append(bt_side("l47-tapestry", "// Level 47 (round 4): the Order's tapestry, the World Snake coiled round the world (2x2: cell tl/tr/bl/br)",
                       {f"*-{c}": f"tapestry-{c}" for c in cells},
                       {"taptl": "tapestry-tl", "taptr": "tapestry-tr", "tapbl": "tapestry-bl", "tapbr": "tapestry-br", "iron": "wrought", "gold": "gold"},
                       "Cloth", CLOTH, 0.6, {"x1": 0, "y1": 0, "z1": 0.85, "x2": 1, "y2": 1, "z2": 1}, groups=[{"code": "cell", "states": cells}],
                       drops=[{"type": "item", "code": "game:cloth-plain", "quantity": {"avg": 0.4, "var": 0.4}}]))
    out.append(bt_side("l47-sconce", "// Level 47 (round 4): an iron candle sconce on the wall", "sconce", {"iron": "wrought", "wax": "wax", "glow": "flame"},
                       "Metal", METAL, 2, {"x1": 0.35, "y1": 0.25, "z1": 0.55, "x2": 0.65, "y2": 0.9, "z2": 1}, extra={"lightHsv": [8, 5, 10]}))
    out.append(("// Level 47 (round 4): stones in the streams (step: the trail's worn stepping stones; rock: a mossy river boulder)", {
        "code": "l47-streamstone", "variantgroups": [{"code": "kind", "states": ["step", "rock"]}], "creativeinventory": inv(), "blockmaterial": "Stone",
        "drawtype": "json", "shapeByType": {"*-step": {"base": "block/47/streamstone-step"}, "*-rock": {"base": "block/47/streamstone-rock"}},
        "textures": {"stone": {"base": tex("granite")}, "moss": {"base": tex("moss")}, "worn": {"base": tex("granite-2")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 6,
        "collisionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.95, "z2": 0.9}, "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.95, "z2": 0.9},
        "drops": [{"type": "item", "code": "game:stone-granite", "quantity": {"avg": 2, "var": 1}}], "sounds": STONE}))
    leafkinds = {"oak": "leaves-oak", "beech": "leaves-beech", "needle": "leaves-needle"}
    out.append(("// Level 47 (round 4): sprays of leaves under (hang) and over (tuft) the crowns' lumps", {
        "code": "l47-leafspray", "variantgroups": [{"code": "leaf", "states": list(leafkinds)}, {"code": "form", "states": ["hang", "tuft"]}],
        "creativeinventory": inv("*-hang"), "blockmaterial": "Leaves", "drawtype": "json", "renderpass": "OpaqueNoCull",
        "vertexFlags": {"windMode": "Leaves"}, "shapeByType": {"*-hang": {"base": "block/47/leafspray-hang"}, "*-tuft": {"base": "block/47/leafspray-tuft"}},
        "texturesByType": {f"*-{k}-*": {"leaf": {"base": tex(v)}} for k, v in leafkinds.items()},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.3, "collisionbox": None,
        "selectionbox": {"x1": 0.1, "y1": 0.1, "z1": 0.1, "x2": 0.9, "y2": 0.9, "z2": 0.9}, "replaceable": 4000,
        "drops": [], "sounds": PLANT}))
    out.append(("// Level 47 (round 4): a standing stone's weathered, rounded top", {
        "code": "l47-sarsentop", "creativeinventory": inv(), "blockmaterial": "Stone", "drawtype": "json", "shape": {"base": "block/47/sarsentop"},
        "textures": {"stone": {"base": tex("megalith")}, "lichen": {"base": tex("megalith-moss")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 20, "drops": [], "sounds": STONE}))
    out.append(bt_side("l47-lamppost", "// Level 47 (round 4): a lamp post by the walk up to the manor, its lantern hung out over the walk (part lower/upper)",
                       {"*-lower": "lamppost-lower", "*-upper": "lamppost-upper"},
                       {"beam": "oak-beam", "post": "oak-post", "stone": "manorstone-dressed", "iron": "wrought", "glass": "lantern-glass", "moss": "moss"}, "Wood", WOOD, 4,
                       {"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7}, coll={"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7},
                       groups=[{"code": "part", "states": ["lower", "upper"]}], extra={"lightHsvByType": {"*-upper-*": [7, 4, 13]}}))
    out.append(("// Level 47 (round 4): an oak post of the porch over the manor's door (base/shaft/head)", {
        "code": "l47-porchpost", "variantgroups": [{"code": "part", "states": ["base", "shaft", "head"]}], "creativeinventory": inv(), "blockmaterial": "Wood",
        "drawtype": "json", "shapeByType": {f"*-{k}": {"base": f"block/47/porchpost-{k}"} for k in ("base", "shaft", "head")},
        "textures": {"post": {"base": tex("oak-post")}, "beam": {"base": tex("oak-beam")}, "stone": {"base": tex("manorstone-dressed")}, "moss": {"base": tex("moss")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 5,
        "collisionbox": {"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7}, "selectionbox": {"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7},
        "drops": [{"type": "item", "code": "game:firewood", "quantity": {"avg": 1, "var": 0.5}}], "sounds": WOOD}))
    offk = ["bowl", "skull", "book"]
    out.append(("// Level 47 (round 4): the offerings on the Altar Stone (a bowl with a shed skin, a snake's skull, the Order's book)", {
        "code": "l47-offering", "variantgroups": [{"code": "kind", "states": offk}], "creativeinventory": inv(), "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{k}": {"base": f"block/47/offering-{k}"} for k in offk},
        "textures": {"bronze": {"base": tex("bronze")}, "dark": {"base": tex("hearth")}, "skin": {"base": tex("parchment")}, "cloth": {"base": tex("gold")},
                     "bone": {"base": tex("bone")}, "leather": {"base": tex("leather")}, "pages": {"base": tex("parchment")}, "script": {"base": tex("script")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1, "collisionbox": None,
        "selectionbox": {"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 0.3, "z2": 0.85}, "drops": [], "sounds": WOOD}))
    out.append(("// Level 47 (round 4): a clay chimney pot on the manor's stacks", {
        "code": "l47-chimneypot", "creativeinventory": inv(), "blockmaterial": "Ceramic", "drawtype": "json", "shape": {"base": "block/47/chimneypot"},
        "textures": {"stone": {"base": tex("manorstone-dressed")}, "clay": {"base": tex("clay")}, "soot": {"base": tex("soot")}},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 3, "drops": [], "sounds": STONE}))
    out.append(("// Level 47 (round 4): the face of a fallen giant's root plate: earth held in roots", {
        "code": "l47-rootearth", "creativeinventory": inv(), "blockmaterial": "Soil", "drawtype": "cube",
        "textures": {"all": {"base": tex("rootearth"), "alternates": [{"base": tex("rootearth-2")}]}, "up": {"base": tex("moss")}},
        "resistance": 2, "drops": [{"type": "block", "code": "game:soil-low-none", "quantity": {"avg": 1, "var": 0}}],
        "sounds": _snd("game:walk/gravel*", "game:block/dirt*")}))
    return out


def shapes():
    """{file name (under shapes/block/47): shape}."""
    out = {}
    for c in ("ne", "se", "sw", "nw"):
        out[f"fillet-{c}"] = shape(fillet(c), {"bark": "bark-oak", "top": "rings-oak"})
    out["mossdrape-a"] = shape(mossdrape("a", 4801), {"moss": "moss", "beard": "beard"})
    out["mossdrape-b"] = shape(mossdrape("b", 4802), {"moss": "moss", "beard": "beard"})
    out["bracket-zoned"] = shape(bracket("zoned", 4803), {"ftop": "fungus-top", "funder": "fungus-under"})
    out["bracket-sulphur"] = shape(bracket("sulphur", 4804), {"ftop": "sulphur", "funder": "sulphur"})
    out["mush-agaric"] = shape(mushclump("agaric", 4805), {"cap": "agaric-cap", "gill": "stem", "stem": "stem", "wart": "wax"})
    out["mush-honey"] = shape(mushclump("honey", 4806), {"cap": "honey-cap", "gill": "fungus-under", "stem": "honey-stem"})
    out["mush-inkcap"] = shape(mushclump("inkcap", 4807), {"cap": "inkcap", "stem": "stem"})
    ws = {"stone": "waystone-dressed", "snake": "waystone-snake", "rough": "granite", "moss": "moss", "eye": "iron"}
    out["waystone-lower"] = shape(waystone("lower"), ws)
    out["waystone-upper"] = shape(waystone("upper"), ws)
    for p in ("lower", "upper", "single"):
        out[f"leaded-{p}"] = shape(leaded(p), {"stone": "manorstone-dressed", "glass": "leaded-glass", "iron": "iron"})
    for lf in ("west", "east"):
        for pos in ("near", "far"):
            for lvl in ("lower", "mid", "upper"):
                els = door_leaf(f"{pos}-{lvl}")
                out[f"door-{lf}-{pos}-{lvl}"] = shape(els if lf == "west" else mirror_x(els), {"door": "door", "iron": "wrought"})
        for lvl in ("lower", "upper"):
            els = doorjamb(lvl)
            out[f"doorjamb-{lf}-{lvl}"] = shape(els if lf == "west" else mirror_x(els), {"beam": "oak-beam", "post": "oak-post", "stone": "manorstone-dressed"})
    rt = {"slate": "roofslate", "boards": "boards", "beam": "oak-beam", "iron": "wrought", "ridge": "ridge", "wall": "manorstone"}
    out["roof-south"] = shape(roof("south"), rt)
    out["roof-south-eave"] = shape(roof("south-eave"), rt)
    out["roof-south-gable"] = shape(roof("south-gable"), rt)
    out["roof-ridge"] = shape(roof("ridge"), rt)
    bc = {"oak": "oak-top", "beam": "oak-beam", "books": "books", "parch": "parchment", "parchend": "parchment-end", "bottle": "bottle", "cork": "cork", "bone": "bone"}
    for p in ("lower", "upper"):
        for k, d in enumerate(("a", "b")):
            out[f"bookcase-{p}-{d}"] = shape(bookcase(p, 4810 + k * 7 + (p == "upper")), bc)
    out["fire"] = shape(fire(), {"iron": "wrought", "bark": "bark-oak", "end": "rings-oak", "ember": "ember", "flame": "flame-sheet"})
    mt = {"beam": "oak-beam", "stone": "manorstone-dressed", "pewter": "pewter", "wax": "wax", "glow": "flame"}
    for p in ("l", "m", "r"):
        out[f"mantel-{p}"] = shape(mantel(p), mt)
    tt = {"oak": "oak-top", "beam": "oak-beam", "pewter": "pewter", "wax": "wax", "glow": "flame", "bread": "bread"}
    for p in ("end", "mid", "centre"):
        out[f"table-{p}"] = shape(table(p), tt)
    for p in ("end", "mid"):
        out[f"bench-{p}"] = shape(bench(p), {"oak": "oak-top", "beam": "oak-beam"})
    for c in ("tl", "tr", "bl", "br"):
        out[f"tapestry-{c}"] = shape(tapestry_shape(c), {f"tap{c}": f"tapestry-{c}", "iron": "wrought", "gold": "gold"})
    out["sconce"] = shape(sconce(), {"iron": "wrought", "wax": "wax", "glow": "flame"})
    for p in ("lower", "upper"):
        out[f"lamppost-{p}"] = shape(lamppost(p), {"beam": "oak-beam", "post": "oak-post", "stone": "manorstone-dressed", "iron": "wrought", "glass": "lantern-glass", "moss": "moss"})
    for k in ("base", "shaft", "head"):
        out[f"porchpost-{k}"] = shape(porchpost(k), {"post": "oak-post", "beam": "oak-beam", "stone": "manorstone-dressed", "moss": "moss"})
    for k in ("bowl", "skull", "book"):
        out[f"offering-{k}"] = shape(offering(k), {"bronze": "bronze", "dark": "hearth", "skin": "parchment", "cloth": "gold", "bone": "bone",
                                                   "leather": "leather", "pages": "parchment", "script": "script"})
    out["sarsentop"] = shape(sarsentop(), {"stone": "megalith", "lichen": "megalith-moss"})
    for form in ("hang", "tuft"):
        out[f"leafspray-{form}"] = shape(leafspray(form), {"leaf": "leaves-oak"})
    for k in ("step", "rock"):
        out[f"streamstone-{k}"] = shape(streamstone(k), {"stone": "granite", "moss": "moss", "worn": "granite-2"})
    out["chimneypot"] = shape(chimneypot(), {"stone": "manorstone-dressed", "clay": "clay", "soot": "soot"})
    return out


def textures(save):
    """Paints and saves the round's textures (save(img, "block/47/<name>"))."""
    for name, img in [("fungus-top", fungus_top(4830)), ("fungus-under", fungus_under(4831)), ("sulphur", sulphur(4832)),
                      ("agaric-cap", agaric_cap(4833)), ("stem", stem(4834)), ("honey-cap", honey_cap(4835)),
                      ("honey-stem", stem(4836, (168, 140, 96))), ("inkcap", inkcap(4837)),
                      ("waystone-dressed", dressed_granite(4838)), ("waystone-snake", snake_relief(4839)),
                      ("books", books(4840)), ("parchment", parchment(4841)), ("bottle", bottle(4842)), ("bone", bone(4843)),
                      ("pewter", pewter(4844)), ("oak-top", oak_top(4845)), ("oak-beam", oak_beam(4846)), ("oak-post", oak_beam(4846).transpose(Image.Transpose.ROTATE_90)), ("door", oak_door(4847)),
                      ("wrought", wrought(4848)), ("soot", soot(4849)), ("ember", ember(4850)), ("flame-sheet", flame_tex(4851)),
                      ("rootearth", rootearth(4852)), ("rootearth-2", rootearth(4853)),
                      ("roofslate", roofslate(4854)), ("roofslate-moss", roofslate(4855, moss=True))]:
        save(img, f"block/47/{name}")
    # Small ones
    end = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(end)
    d.rectangle([0, 0, S - 1, S - 1], fill=M.rgba((196, 178, 136)))
    for r, c in ((12, (170, 150, 110)), (8, (186, 168, 128)), (4, (150, 128, 92))):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=M.rgba(c))
    save(end, "block/47/parchment-end")
    save(M.noise_hv((150, 118, 80), 4, 4856, mottle=6), "block/47/cork")
    save(M.noise_hv((176, 132, 74), 5, 4857, mottle=8), "block/47/bread")
    save(M.noise_hv((200, 160, 70), 4, 4858, mottle=6), "block/47/gold")
    save(M.brushed_metal(seed=4867, base=(150, 108, 60), direction="h", streak=6, sheen=10), "block/47/bronze")
    save(M.noise_hv((92, 30, 26), 4, 4868, mottle=8), "block/47/leather")
    script = parchment(4869)
    d = ImageDraw.Draw(script)
    rng = random.Random(4870)
    for y in range(3, S - 3, 3):
        x = 2
        while x < S - 4:
            w = rng.randint(1, 4)
            d.line([x, y, x + w, y], fill=M.rgba((70, 40, 30)))
            x += w + rng.randint(1, 2)
    d.ellipse([12, 12, 20, 20], outline=M.rgba((150, 24, 24)))
    save(script, "block/47/script")
    # The leaded lights' glass, opaque (a window in the opaque pass: the translucent pass drew the stone round it as a
    # ghost): old green-grey glass in diamond panes, each pane lit at its upper left and darker at its lower right, a
    # bullseye here and there, the lead cames dark
    lg = Image.new("RGBA", (S, S))
    px = lg.load()
    rng = random.Random(4871)
    for y in range(S):
        for x in range(S):
            u, v = (x + y) % 8, (x - y) % 8
            if u == 0 or v == 0:
                px[x, y] = (34, 34, 38, 255)
            else:
                g = 22 * (1 - (u + (8 - v)) / 14) + rng.uniform(-5, 5)
                px[x, y] = M.rgba(M.lift((70, 92, 86), g))
    for _ in range(3):
        cx, cy = rng.randrange(4, 28), rng.randrange(4, 28)
        px[cx, cy] = M.rgba((150, 170, 150))
        px[cx + 1, cy] = M.rgba((110, 130, 116))
    save(lg, "block/47/leaded-glass")
    clay = M.noise_hv((150, 88, 62), 4, 4865, mottle=8)
    M.grime(clay, 0.3, seed=4866, color=(50, 44, 40), bias="top")
    save(clay, "block/47/clay")
    beard = M.noise_hv((104, 122, 86), 6, 4859, mottle=8)
    save(beard, "block/47/beard")
    # The ridge tiles: rounded clay-grey, a lit crown line
    ridge = M.noise_hv((84, 84, 88), 4, 4860, mottle=6)
    for x in range(S):
        ridge.putpixel((x, 12), M.rgba((120, 120, 124)))
        ridge.putpixel((x, 20), M.rgba((50, 50, 54)))
    save(ridge, "block/47/ridge")
    # The window surrounds' dressed stone: the manor's ashlar, finer, a tooled margin
    img = M.noise_hv((136, 132, 122), 4, 4861, mottle=8)
    M.grime(img, 0.16, seed=4862, color=(70, 72, 60), cover=0.5)
    T.lichen(img, 4863, (176, 180, 136), n=2, rad=(1.5, 3))
    save(img, "block/47/manorstone-dressed")
    # The tapestry, in four quarters
    tap = tapestry(4864)
    for c, (x, y) in {"tl": (0, 0), "tr": (32, 0), "bl": (0, 32), "br": (32, 32)}.items():
        save(tap.crop((x, y, x + 32, y + 32)), f"block/47/tapestry-{c}")
