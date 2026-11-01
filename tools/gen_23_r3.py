"""Level 23, "The Petrified Garden": round 3's blocks (2026-11-01), called from tools/gen_23.py (which writes the lang).

The forest floor between the trees: aspen bark (white with black eyes: the lore lists aspen), fallen logs (bark along their
length, the rings at their ends), boulders, giant stone mushrooms (stem and cap), petrified undergrowth (a shrub, a
sapling, fern fronds, a stump), bracket fungi on the trunks, a buried sentry's body under its face, glowing bushes for
the glow rooms; in the ruins, a damaged fresco and rags of cloth; Base Seedling's things (its sign, the M.E.G.'s notice
board, a way-sign, the warning at the Heart of Water, a painted plank by a sentry, water barrels, crates, bedrolls, a fire
ring, flagstones, a ledger).

Oriented models face NORTH (their front at low z) and have the variant group "side" (north, east, south, west) last:
-east is rotateY 270, -south 180, -west 90, as the released levels' props (tools/gen_31_props.py).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

import matlib as M
import gen_23 as G

S = G.S
SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
FONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
WOOD, SOIL = G.WOOD, G.SOIL
STONE = ("game:walk/stone*", "game:block/rock-hit-pickaxe")


def font(name, size):
    for path in (os.path.join(FONTS, name), name):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


# ---------------- Textures ----------------

def aspen(seed):
    """Petrified aspen: smooth white-cream bark, faint horizontal lenticels, black diamond-shaped eyes where branches fell."""
    img = M.noise_hv((206, 204, 192), 3, seed, mottle=6, hue=2)
    px = img.load()
    rng = random.Random(seed + 1)
    for _ in range(14):  # lenticels: short dark dashes across
        x, y, n = rng.randrange(S), rng.randrange(S), rng.randint(2, 5)
        for k in range(n):
            px[(x + k) % S, y] = M.rgba(M.lift(px[(x + k) % S, y], -38))
    for _ in range(2):  # the eyes
        cx, cy = rng.randrange(4, S - 4), rng.randrange(4, S - 4)
        w, h = rng.randint(3, 5), rng.randint(2, 3)
        for y in range(-h - 1, h + 2):
            for x in range(-w - 1, w + 2):
                e = abs(x) / (w + 0.5) + abs(y) / (h + 0.5)
                if e < 1:
                    px[(cx + x) % S, (cy + y) % S] = M.rgba(M.lift((34, 32, 30), rng.uniform(-6, 6)))
                elif e < 1.35:
                    px[(cx + x) % S, (cy + y) % S] = M.rgba(M.lift(px[(cx + x) % S, (cy + y) % S], -30))
    G.flecks(img, seed + 2, 10, (150, 156, 132), 0.4)
    return img


def boulder(seed, mossy=0.5):
    img = M.noise_hv((112, 112, 102), 4, seed, mottle=9, hue=2)
    pts = M.points(S, 6, seed + 1)
    f1, f2, idx = M.worley(S, pts)
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = -18 if f2[y][x] - f1[y][x] < 0.7 else 4 * math.sin(idx[y][x] * 1.7)
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    G.flecks(img, seed + 2, 16, (200, 200, 190), 0.4)
    if mossy:
        G.lichened(img, seed + 3, (78, 100, 46), n=3)
    return img


def mushcap_top(seed):
    """A stone mushroom's cap, seen from above: warm grey-ochre stone, darker spots, fine cracks."""
    img = M.noise_hv((150, 132, 104), 4, seed, mottle=8, hue=3)
    px = img.load()
    rng = random.Random(seed + 1)
    for _ in range(6):
        cx, cy, r = rng.randrange(S), rng.randrange(S), rng.uniform(1.5, 3)
        for y in range(S):
            for x in range(S):
                dx, dy = min(abs(x - cx), S - abs(x - cx)), min(abs(y - cy), S - abs(y - cy))
                if dx * dx + dy * dy < r * r:
                    px[x, y] = M.rgba(M.lift(px[x, y], -26))
    G.flecks(img, seed + 2, 14, (206, 196, 170), 0.4)
    return img


def mushcap_gills(seed):
    """The underside: gills, thin dark and pale lines close together."""
    img = M.noise_hv((176, 164, 140), 2, seed, mottle=4)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (x + (y // 8)) % 3 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], -34))
    return img


def mushcap_side(seed):
    img = mushcap_top(seed)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if y > 22:
                px[x, y] = M.rgba(M.lift(px[x, y], -14 - (y - 22) * 3))
    return img


def mushstem(seed):
    img = M.noise_hv((184, 176, 156), 3, seed, mottle=5)
    px = img.load()
    rng = random.Random(seed)
    for k in range(9):
        x = rng.randrange(S)
        for y in range(S):
            px[(x + y // 11) % S, y] = M.rgba(M.lift(px[(x + y // 11) % S, y], -16))
    return img


def flagstone(seed):
    """Flat stones set in moss: the M.E.G.'s path at Base Seedling."""
    img = G.moss(seed)
    px = img.load()
    rng = random.Random(seed + 1)
    stones = [(2, 2, 14, 13), (17, 1, 30, 11), (3, 16, 13, 30), (16, 14, 30, 30)]
    for (x0, y0, x1, y1) in stones:
        shade = rng.uniform(-10, 10)
        for y in range(y0, y1):
            for x in range(x0, x1):
                edge = x in (x0, x1 - 1) or y in (y0, y1 - 1)
                c = M.lift((136, 132, 120), shade + rng.uniform(-6, 6) - (14 if edge else 0))
                px[x, y] = M.rgba(c)
    return img


def planks(seed, base=(118, 92, 62)):
    img = M.noise_hv(base, 4, seed, mottle=6, hue=2)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if y % 8 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], -36))
            elif (x * 7 + (y // 8) * 13) % 31 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], -14))
    return img


def stencil(img, text, size, colour=(230, 228, 214), y=None, fnt="bahnschrift.ttf", alpha=230):
    """Spray-paints text across the middle of an image (M.E.G. stencil)."""
    d = ImageDraw.Draw(img)
    f = font(fnt, size)
    box = d.textbbox((0, 0), text, font=f)
    w, h = box[2] - box[0], box[3] - box[1]
    x = (img.width - w) // 2 - box[0]
    yy = (img.height - h) // 2 - box[1] if y is None else y - box[1]
    d.text((x, yy), text, font=f, fill=colour + (alpha,))
    return img


def crate(seed):
    img = planks(seed, (132, 104, 66))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(70, 52, 34, 255))
    return stencil(img, "M.E.G.", 9, colour=(32, 30, 28), y=12)


def barrel_side(seed):
    img = planks(seed, (122, 90, 56)).transpose(Image.Transpose.ROTATE_90)
    px = img.load()
    for y in (4, 5, 26, 27):
        for x in range(S):
            px[x, y] = M.rgba((62, 60, 58))
    return stencil(img, "WATER", 8, colour=(40, 70, 120), y=12)


def barrel_top(seed):
    img = planks(seed, (110, 82, 52))
    d = ImageDraw.Draw(img)
    d.ellipse([1, 1, S - 2, S - 2], outline=(62, 60, 58, 255), width=2)
    return img


def canvas(seed):
    """A bedroll's canvas: drab green, stitched."""
    img = M.noise_hv((92, 98, 70), 3, seed, mottle=5)
    px = img.load()
    for x in range(S):
        if x % 4 == 0:
            px[x, 3] = px[x, 28] = M.rgba((60, 62, 46))
    return img


def blanket(seed):
    img = M.noise_hv((128, 64, 50), 3, seed, mottle=5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            if (y // 4) % 4 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], 22))
    return img


def embers(seed):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            t = rng.random()
            c = (255, 196, 90) if t > 0.85 else (226, 110, 40) if t > 0.4 else (90, 34, 20)
            px[x, y] = M.rgba(c)
    return img


def charred(seed):
    img = M.noise_hv((40, 34, 30), 3, seed, mottle=6)
    G.flecks(img, seed + 1, 8, (200, 90, 40), 0.6)
    return img


def board(w_blocks, h_px, seed, base=(116, 88, 58)):
    """A weathered painted board w blocks wide (64 px a block)."""
    W = 64 * w_blocks
    img = Image.new("RGBA", (W, h_px))
    px = img.load()
    rng = random.Random(seed)
    for y in range(h_px):
        for x in range(W):
            c = M.lift(base, rng.uniform(-6, 6) + (-28 if y % 16 == 0 else 0))
            px[x, y] = M.rgba(c)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, h_px - 1], outline=(60, 44, 30, 255), width=2)
    return img


def wear(img, seed, amount=0.08):
    """Paint worn off in flecks, a little damp at the bottom."""
    px = img.load()
    rng = random.Random(seed)
    for _ in range(int(img.width * img.height * amount)):
        x, y = rng.randrange(img.width), rng.randrange(img.height)
        px[x, y] = M.rgba(M.lift(px[x, y][:3], rng.uniform(-24, 10)))
    return img


def text_lines(img, lines, colour, x=None):
    """Draws (text, size, font, y) lines; centred unless x is given."""
    d = ImageDraw.Draw(img)
    for (s, size, fnt, y) in lines:
        f = font(fnt, size)
        box = d.textbbox((0, 0), s, font=f)
        w = box[2] - box[0]
        xx = (img.width - w) // 2 - box[0] if x is None else x
        d.text((xx, y - box[1]), s, font=f, fill=colour + (255,))
    return img


def split(img, n):
    return [img.crop((64 * k, 0, 64 * (k + 1), img.height)) for k in range(n)]


def sign_camp():
    """BASE SEEDLING over the M.E.G.'s name, three blocks wide."""
    img = board(3, 64, 2401, base=(54, 72, 58))
    text_lines(img, [("BASE SEEDLING", 25, "bahnschrift.ttf", 9)], (232, 226, 196))
    text_lines(img, [("M.E.G.  OUTPOST 23-1  ·  ALL WELCOME", 10, "bahnschrift.ttf", 44)], (206, 196, 150))
    return split(wear(img, 2402), 3)


def sign_rules():
    """The notice board: the camp's rules on a sheet, a map scrap and a missing-person note pinned beside it."""
    img = board(2, 64, 2403, base=(98, 76, 52))
    d = ImageDraw.Draw(img)
    d.rectangle([6, 4, 74, 60], fill=(226, 220, 198, 255))
    lines = [("CAMP RULES", 9, "arialbd.ttf", 7), ("1. NEVER SAY IT.", 6, "arialbd.ttf", 19), ("2. WATER FREE.", 6, "arial.ttf", 28),
             ("   FOOD BY RATION.", 6, "arial.ttf", 36), ("3. THE TREE IS THE", 6, "arial.ttf", 44), ("   WAY OUT. ASK FIRST.", 6, "arial.ttf", 52)]
    for (s, size, fnt, y) in lines:
        d.text((10, y), s, font=font(fnt, size), fill=(40, 36, 30, 255))
    d.rectangle([82, 6, 122, 32], fill=(208, 196, 160, 255))
    d.text((85, 9), "MISSING:", font=font("arialbd.ttf", 7), fill=(120, 30, 24, 255))
    d.text((85, 19), "T. ALLARD", font=font("arial.ttf", 7), fill=(40, 36, 30, 255))
    d.rectangle([84, 38, 120, 60], fill=(196, 202, 176, 255))
    for k in range(5):
        d.line([86, 42 + k * 4, 86 + 10 + k * 5, 44 + k * 3], fill=(80, 100, 70, 255))
    d.text((100, 50), "N", font=font("arialbd.ttf", 7), fill=(40, 36, 30, 255))
    for (x, y) in [(8, 6), (72, 6), (84, 8), (120, 8), (86, 40), (118, 40)]:
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(190, 40, 30, 255))
    return split(img, 2)


def sign_trail():
    img = board(1, 64, 2404, base=(54, 72, 58))
    text_lines(img, [("BASE", 14, "bahnschrift.ttf", 5), ("SEEDLING", 12, "bahnschrift.ttf", 21)], (232, 226, 196))
    d = ImageDraw.Draw(img)
    d.polygon([(24, 40), (40, 40), (40, 46), (46, 46), (32, 60), (18, 46), (24, 46)], fill=(232, 226, 196, 255))
    return split(wear(img, 2405), 1)


def sign_giants():
    img = board(2, 64, 2406, base=(150, 40, 32))
    text_lines(img, [("GREEN GIANTS", 16, "bahnschrift.ttf", 7), ("DO NOT CUT · CLIMB · CARVE", 8, "bahnschrift.ttf", 31),
                     ("- M.E.G.", 9, "bahnschrift.ttf", 46)], (240, 234, 220))
    return split(wear(img, 2407, 0.1), 2)


def sign_dontsay():
    """A plank nailed up by a sentry, hand-painted."""
    img = board(1, 64, 2408, base=(132, 104, 70))
    text_lines(img, [("DON'T", 15, "Inkfree.ttf", 6), ("SAY IT", 15, "Inkfree.ttf", 24)], (150, 26, 20))
    d = ImageDraw.Draw(img)
    d.line([8, 52, 56, 46], fill=(150, 26, 20, 255), width=2)
    return split(wear(img, 2409), 1)


def fresco(seed):
    """A damaged painting on the ruins' plaster: a garden and figures with green eyes, mostly flaked away."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    stone = G.ruinstone(seed)
    sp = stone.load()
    for y in range(S):
        for x in range(S):
            c = (196, 176, 140) if y > 8 else (120, 150, 160)
            if 14 < y < 26 and (x // 5) % 2 == 0:
                c = (82, 112, 60)  # trees
            if 6 < x < 12 and 12 < y < 28:
                c = (150, 92, 64)  # a figure
            if x in (8, 10) and y == 15:
                c = (60, 200, 90)  # its green eyes
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-10, 6)))
    flake = M.fbm(S, seed + 1, (8, 4, 2))
    for y in range(S):
        for x in range(S):
            if flake[y][x] > 0.1:
                px[x, y] = sp[x, y]
    return img


def cloth(seed):
    img = M.noise_hv((150, 120, 92), 3, seed, mottle=6)
    G.flecks(img, seed + 1, 30, (70, 60, 44), 0.5)
    return img


def sentry_body(seed):
    """Under a buried sentry's face: shoulders and arms pushed out of the bark, the hands up at the chest as if pushing."""
    img = G.bark(G.BARKS["grey"], seed, wave=1.3)
    px = img.load()
    for y in range(S):
        for x in range(S):
            dx = (x + 0.5 - 16) / 13.0
            sh = 1 - dx * dx * 1.2 - max(0, y - 20) * 0.02
            if y < 26 and sh > 0 and y > 1 + 6 * dx * dx:
                c = M.lift(px[x, y], 12 * sh - (10 if y > 22 else 0))
                px[x, y] = M.rgba(c)
    for hx in (9, 19):  # the hands, fingers splayed
        for k in range(4):
            for j in range(5):
                M.touch(img, hx + k, 6 + j + (k % 2), 0.18)
            M.touch(img, hx + k, 11, -0.2)
    for x in range(14, 18):  # the neck's shadow at the top
        M.touch(img, x, 0, -0.22)
    return img


# ---------------- Models ----------------

def B(name, frm, to, tex, glow=0, faces="nsewud", rot=None):
    b = G.box(name, list(frm), list(to), tex, glow, faces)
    if rot:
        b.update(rot)
    return b


def shape(textures, elements, w=16, h=16):
    return {"textureWidth": w, "textureHeight": h, "textures": textures, "elements": elements}


def stone_shrub():
    els, rng = [], random.Random(11)
    for k in range(7):
        x, z = rng.uniform(4, 11), rng.uniform(4, 11)
        hgt = rng.uniform(5, 11)
        els.append(B(f"Twig{k}", (x, 0, z), (x + 1, hgt, z + 1), "#bark",
                     rot={"rotationOrigin": [x + 0.5, 0, z + 0.5], "rotationX": rng.uniform(-30, 30), "rotationZ": rng.uniform(-30, 30)}))
    return shape({"bark": "backrooms:block/23/bark-grey"}, els)


def stone_sapling():
    els = [B("Trunk", (7.3, 0, 7.3), (8.7, 15, 8.7), "#bark")]
    rng = random.Random(12)
    for k in range(5):
        y = 6 + k * 2
        els.append(B(f"Twig{k}", (8, y, 7.6), (8 + rng.uniform(3, 5), y + 0.8, 8.4), "#bark",
                     rot={"rotationOrigin": [8, y, 8], "rotationY": k * 72 + rng.uniform(-20, 20), "rotationZ": rng.uniform(15, 35)}))
    return shape({"bark": "backrooms:block/23/bark-pale"}, els)


def stone_fern():
    els = []
    for k in range(6):
        a = k * 60
        els.append(B(f"Frond{k}", (7, 0, 7.5), (15, 0.6, 8.5), "#bark",
                     rot={"rotationOrigin": [8, 0, 8], "rotationY": a, "rotationZ": 32 + (k % 2) * 12}))
    return shape({"bark": "backrooms:block/23/bark-dark"}, els)


def stone_stump():
    els = [B("Stump", (3, 0, 3), (13, 6, 13), "#bark", faces="nsewd"),
           B("Top", (3, 6, 3), (13, 6.01, 13), "#ring", faces="u"),
           B("Jag1", (3, 6, 3), (7, 9, 6), "#bark"), B("Jag2", (10, 6, 9), (13, 8, 13), "#bark"),
           B("Root1", (0, 0, 6), (3, 2, 9), "#bark"), B("Root2", (13, 0, 7), (16, 1.6, 10), "#bark")]
    return shape({"bark": "backrooms:block/23/bark-red", "ring": "backrooms:block/23/heartwood-red"}, els)


def bracket():
    """Shelves of stone fungus stepping up the side of a trunk (the trunk is on the block's south side; they face north)."""
    els = [B("Shelf1", (2, 3, 9), (11, 4.5, 16), "#cap"), B("Under1", (2.5, 2.9, 9.5), (10.5, 3, 16), "#gills", faces="d"),
           B("Shelf2", (7, 8, 11), (14, 9.2, 16), "#cap"), B("Shelf3", (3, 12, 12), (9, 13, 16), "#cap")]
    return shape({"cap": "backrooms:block/23/mushcap-top", "gills": "backrooms:block/23/mushcap-gills"}, els)


def glowbush(colour):
    els, rng = [], random.Random(len(colour) * 13)
    for k in range(6):
        x, z = rng.uniform(4, 11), rng.uniform(4, 11)
        hgt = rng.uniform(6, 12)
        els.append(B(f"Twig{k}", (x, 0, z), (x + 0.8, hgt, z + 0.8), "#stem",
                     rot={"rotationOrigin": [x + 0.4, 0, z + 0.4], "rotationX": rng.uniform(-25, 25), "rotationZ": rng.uniform(-25, 25)}))
    for k in range(12):
        x, y, z = rng.uniform(2, 13), rng.uniform(4, 12), rng.uniform(2, 13)
        els.append(B(f"Berry{k}", (x, y, z), (x + 1.2, y + 1.2, z + 1.2), "#bead", 255))
    return shape({"stem": "backrooms:block/23/bark-dark", "bead": f"backrooms:block/23/sorry-{colour}"}, els)


def signboard():
    """A board on a post's top (the post its own block below): the front (north face) carries the text."""
    return shape({"face": "backrooms:block/23/sign-trail", "wood": "backrooms:block/23/planks"},
                 [B("Board", (0, 2, 7), (16, 15, 9), "#wood", faces="sewud"),
                  {"name": "Face", "from": [0, 2, 6.98], "to": [16, 15, 7], "faces": {"north": {"texture": "#face", "uv": [0, 1, 16, 15]}}}])


def signpost():
    return shape({"wood": "backrooms:block/23/planks"}, [B("Post", (6.5, 0, 6.5), (9.5, 16, 9.5), "#wood")])


def barrel():
    t = "#side"
    return shape({"side": "backrooms:block/23/barrel-side", "top": "backrooms:block/23/barrel-top"},
                 [B("Body", (2, 0, 2), (14, 14, 14), t, faces="nsewd"), B("Lid", (2, 14, 2), (14, 14.01, 14), "#top", faces="u"),
                  B("BulgeX", (1.4, 2, 3), (14.6, 12, 13), t, faces="ew"), B("BulgeZ", (3, 2, 1.4), (13, 12, 14.6), t, faces="ns")])


def bedroll():
    """Facing north: the roll at the head (north), the blanket over the canvas toward the foot."""
    return shape({"canvas": "backrooms:block/23/canvas", "blanket": "backrooms:block/23/blanket"},
                 [B("Mat", (2, 0, 0), (14, 1, 16), "#canvas"), B("Blanket", (2.2, 1, 5), (13.8, 1.6, 16), "#blanket"),
                  B("Roll", (2.5, 1, 0.5), (13.5, 3.6, 4), "#canvas")])


def firering():
    els = []
    for k in range(10):
        a = k * math.pi * 2 / 10
        x, z = 8 + math.cos(a) * 6, 8 + math.sin(a) * 6
        els.append(B(f"Stone{k}", (x - 1.5, 0, z - 1.5), (x + 1.5, 2.2 + (k % 3) * 0.5, z + 1.5), "#stone"))
    els += [B("Ash", (3, 0, 3), (13, 0.5, 13), "#char", faces="u"), B("Embers", (5, 0.5, 5), (11, 1, 11), "#ember", 255),
            B("Log1", (4, 0.8, 7), (12, 2.4, 8.6), "#char", rot={"rotationOrigin": [8, 1.6, 8], "rotationY": 30}),
            B("Log2", (4, 0.8, 7.4), (12, 2.4, 9), "#char", rot={"rotationOrigin": [8, 1.6, 8], "rotationY": -40})]
    return shape({"stone": "backrooms:block/23/boulder", "char": "backrooms:block/23/charred", "ember": "backrooms:block/23/embers"}, els)


def lantern():
    """The M.E.G.'s lanterns (and the lamp on the Lighthouse): a frame of dark iron round a glowing glass, a ring on top."""
    return shape({"iron": "backrooms:block/23/charred", "glass": "backrooms:block/23/lantern-glass"},
                 [B("Base", (5, 0, 5), (11, 1, 11), "#iron"), B("Glass", (5.5, 1, 5.5), (10.5, 7, 10.5), "#glass", 255),
                  B("PostNW", (5, 1, 5), (6, 7, 6), "#iron"), B("PostNE", (10, 1, 5), (11, 7, 6), "#iron"),
                  B("PostSW", (5, 1, 10), (6, 7, 11), "#iron"), B("PostSE", (10, 1, 10), (11, 7, 11), "#iron"),
                  B("Top", (5, 7, 5), (11, 8, 11), "#iron"), B("Cap", (6.5, 8, 6.5), (9.5, 9, 9.5), "#iron"),
                  B("Ring", (7.5, 9, 7.8), (8.5, 10.5, 8.2), "#iron")])


def lantern_glass(seed):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            r = abs(x + 0.5 - S / 2) / (S / 2)
            px[x, y] = M.rgba(M.lift((255, 206, 120), rng.uniform(-8, 8) - 40 * r * r))
    return img


def squirtrack():
    """The M.E.G.'s Almond Water squirt guns (the lore's arms of Base Seedling), three on a little rack, facing north."""
    els = [B("Back", (1, 0, 13), (15, 12, 14.5), "#wood"), B("Shelf", (1, 0, 9), (15, 1, 14.5), "#wood")]
    for k, x in enumerate((2.5, 7, 11.5)):
        els += [B(f"Body{k}", (x, 1, 10), (x + 2.5, 4, 13), "#orange"), B(f"Tank{k}", (x + 0.2, 4, 10.5), (x + 2.3, 7.5, 12.8), "#green"),
                B(f"Barrel{k}", (x + 0.8, 2.5, 6.5), (x + 1.7, 3.4, 10), "#orange"), B(f"Grip{k}", (x + 0.6, 1, 12.6), (x + 1.9, 3, 13), "#green")]
    return shape({"wood": "backrooms:block/23/planks", "orange": "backrooms:block/23/plastic-orange", "green": "backrooms:block/23/plastic-green"}, els)


def plastic(rgb, seed):
    img = M.noise_hv(rgb, 2, seed, mottle=3)
    G.flecks(img, seed + 1, 6, (255, 255, 255), 0.3)
    return img


def mossbark(seed):
    """Moss grown up over the foot of a trunk: dark bark under a thick green mat, ragged at its top edge."""
    img = G.bark((70, 66, 58), seed, wave=1.3)
    px = img.load()
    edge = M.fbm(S, seed + 1, (8, 4))
    for y in range(S):
        for x in range(S):
            t = (y / S) + 0.35 * edge[y][x]
            if t > 0.28:
                px[x, y] = M.rgba(M.mix(px[x, y], M.lift((58, 82, 36), 18 * edge[y][x]), min(1, (t - 0.28) * 3)))
    G.flecks(img, seed + 2, 20, (126, 150, 70), 0.5)
    return img


def ledger():
    return shape({"paper": "backrooms:block/23/ledger", "cover": "backrooms:block/23/blanket"},
                 [B("Cover", (3, 0, 4), (13, 0.6, 12), "#cover"), B("Pages", (3.4, 0.6, 4.4), (12.6, 1.2, 11.6), "#paper", faces="u")])


def cloth_shape():
    return shape({"cloth": "backrooms:block/23/cloth"},
                 [B("Rag1", (2, 0, 3), (12, 0.4, 11), "#cloth"), B("Fold", (4, 0.4, 5), (10, 1.2, 8), "#cloth"),
                  B("Rag2", (10, 0, 9), (15, 0.3, 14), "#cloth")])


def ledger_tex(seed):
    img = Image.new("RGBA", (S, S), (226, 220, 198, 255))
    d = ImageDraw.Draw(img)
    for y in range(4, S - 2, 3):
        d.line([3, y, 14, y], fill=(90, 84, 74, 255))
        d.line([18, y, 29, y], fill=(90, 84, 74, 255))
    d.line([16, 0, 16, S], fill=(150, 140, 120, 255))
    return img


# ---------------- Blocktypes ----------------

LOG_BARKS = ["grey", "red", "pale", "dark", "aspen"]


def log_block():
    tex = {}
    for b in LOG_BARKS:
        side = {"base": f"block/23/bark-{b}", "alternates": [{"base": f"block/23/bark-{b}-2"}]}
        turned = dict(side, rotation=90)
        end = {"base": f"block/23/heartwood-{b}"}
        tex[f"*-{b}-x"] = {"all": turned, "north": turned, "south": turned, "east": end, "west": end}
        tex[f"*-{b}-z"] = {"all": side, "north": end, "south": end, "east": turned, "west": turned, "up": side, "down": side}
    return ("// Level 23 (round 3): a fallen petrified log, lying along x or z, its rings at its ends", {
        "code": "l23-log",
        "variantgroups": [{"code": "bark", "states": LOG_BARKS}, {"code": "axis", "states": ["x", "z"]}],
        "creativeinventory": {"general": ["*-x"], "backrooms": ["*-x"]},
        "blockmaterial": "Wood", "drawtype": "cube", "texturesByType": tex, "resistance": 7,
        "drops": [G.drop("game:firewood", 0.6, 0.4)],
        "sounds": {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]},
    })


def model_block(code, comment, shp, material, sounds, drops=(), sides=False, collision=None, selection=None, light=None, variants=None,
                extra=None):
    """A json-model block; with sides, the variant group "side" (rotated as the released props); with variants, a first group
    of its own (name, states, shape per state)."""
    groups, shape_by = [], {}
    if variants:
        gname, states, shp_of = variants
        groups.append({"code": gname, "states": states})
    if sides:
        groups.append({"code": "side", "states": SIDES})
    if variants and sides:
        for s in variants[1]:
            for side in SIDES:
                shape_by[f"*-{s}-{side}"] = {"base": f"block/23/{variants[2](s)}", "rotateY": ROT[side]}
    elif variants:
        for s in variants[1]:
            shape_by[f"*-{s}"] = {"base": f"block/23/{variants[2](s)}"}
    elif sides:
        for side in SIDES:
            shape_by[f"*-{side}"] = {"base": f"block/23/{shp}", "rotateY": ROT[side]}
    b = {"code": code}
    if groups:
        b["variantgroups"] = groups
    first = "*-north" if sides else "*"
    b.update({
        "creativeinventory": {"general": [first], "backrooms": [first]},
        "blockmaterial": material, "drawtype": "json",
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "resistance": 1.5, "drops": list(drops), "sounds": sounds,
    })
    if shape_by:
        b["shapeByType"] = shape_by
    else:
        b["shape"] = {"base": f"block/23/{shp}"}
    b["collisionbox"] = collision
    if selection:
        b["selectionbox"] = selection
    if light:
        b["lightHsv"] = light
    if extra:
        b.update(extra)
    return comment, b


def signs_block():
    texts = ["camp-a", "camp-b", "camp-c", "rules-a", "rules-b", "trail", "giants-a", "giants-b", "dontsay"]
    shape_by, tex_by = {}, {}
    for t in texts:
        for side in SIDES:
            shape_by[f"*-{t}-{side}"] = {"base": "block/23/signboard", "rotateY": ROT[side]}
        tex_by[f"*-{t}-*"] = {"face": {"base": f"block/23/sign-{t}"}}
    return ("// Level 23 (round 3): the M.E.G.'s painted boards (the camp's sign, its notice board, the way-signs, the warning at the Heart of Water, a plank by a sentry); each is a block of a board, on a post below", {
        "code": "l23-sign",
        "variantgroups": [{"code": "text", "states": texts}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by, "texturesByType": tex_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2,
        "collisionboxByType": {f"*-{s}": {"x1": 0, "y1": 0.12, "z1": 0.4, "x2": 1, "y2": 0.95, "z2": 0.6, "rotateY": ROT[s]} for s in SIDES},
        "selectionboxByType": {f"*-{s}": {"x1": 0, "y1": 0.12, "z1": 0.4, "x2": 1, "y2": 0.95, "z2": 0.6, "rotateY": ROT[s]} for s in SIDES},
        "drops": [G.drop("game:plank-oak", 1, 0)],
        "sounds": {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]},
    })


def blocks():
    out = []
    out.append(G.cube_block("l23-bark-aspen", "// Level 23 (round 3): petrified aspen bark, white with black eyes; its cut ends grey rings",
                            ["block/23/bark-aspen", "block/23/bark-aspen-2"], "Wood", *WOOD, 7, drops=[G.drop("game:firewood", 0.6, 0.4)],
                            faces={"up": "block/23/heartwood-aspen", "down": "block/23/heartwood-aspen"}))
    out.append(log_block())
    out.append(G.cube_block("l23-boulder", "// Level 23 (round 3): a mossy boulder half sunk in the humus", ["block/23/boulder", "block/23/boulder-2"],
                            "Stone", *STONE, 6, drops=[G.drop("game:stone-granite", 2, 1)]))
    out.append(G.cube_block("l23-mushstem", "// Level 23 (round 3): a giant stone mushroom's stem", ["block/23/mushstem"], "Stone", *STONE, 4))
    out.append(G.cube_block("l23-mushcap", "// Level 23 (round 3): a giant stone mushroom's cap, gills under it", ["block/23/mushcap-side"],
                            "Stone", *STONE, 4, faces={"up": "block/23/mushcap-top", "down": "block/23/mushcap-gills"}))
    out.append(G.cube_block("l23-flagstone", "// Level 23 (round 3): flat stones set in moss (the path at Base Seedling)", ["block/23/flagstone"],
                            "Stone", *STONE, 5))
    out.append(G.cube_block("l23-crate", "// Level 23 (round 3): the M.E.G.'s crates at Base Seedling (stencilled)", ["block/23/crate"],
                            "Wood", *WOOD, 3, drops=[G.drop("game:plank-oak", 2, 1)]))
    plant_sounds = {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe",
                    "hit": "game:block/rock-hit-pickaxe"}
    out.append(model_block("l23-stoneplant", "// Level 23 (round 3): petrified undergrowth (a shrub, a sapling, fern fronds, a stump)", None,
                           "Stone", plant_sounds, drops=[G.drop("game:stick", 0.3, 0.3)],
                           selection={"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 0.7, "z2": 0.85},
                           variants=("kind", ["shrub", "sapling", "fern", "stump"], lambda k: f"stone-{k}"),
                           extra={"collisionboxByType": {"*-stump": {"x1": 0.19, "y1": 0, "z1": 0.19, "x2": 0.81, "y2": 0.4, "z2": 0.81}, "*": None},
                                  "collisionbox": None, "replaceable": 3500}))
    out[-1][1].pop("collisionbox", None)
    out.append(model_block("l23-bracket", "// Level 23 (round 3): bracket fungi of stone stepping up a trunk (the trunk on the block's back)",
                           "bracket", "Stone", plant_sounds, sides=True,
                           selection={"x1": 0.1, "y1": 0.15, "z1": 0.55, "x2": 0.9, "y2": 0.85, "z2": 1}))
    out[-1][1]["selectionboxByType"] = {f"*-{s}": {"x1": 0.1, "y1": 0.15, "z1": 0.55, "x2": 0.9, "y2": 0.85, "z2": 1, "rotateY": ROT[s]} for s in SIDES}
    out[-1][1].pop("selectionbox", None)
    colours = ["teal", "violet", "amber"]
    gb = model_block("l23-glowbush", "// Level 23 (round 3): the glow rooms' glowing bushes (the lore's \"glowing fungi and bushes\")", None,
                     "Plant", {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
                     selection={"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.8, "z2": 0.9},
                     variants=("colour", colours, lambda c: f"glowbush-{c}"),
                     extra={"lightHsvByType": {f"*-{c}": [G.GLOW_HSV[c], 6, 9] for c in colours}, "renderpass": "OpaqueNoCull",
                            "faceCullMode": "NeverCull", "replaceable": 3000})
    out.append(gb)
    out.append(signs_block())
    out.append(model_block("l23-signpost", "// Level 23 (round 3): the post a sign stands on", "signpost", "Wood",
                           {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]}, drops=[G.drop("game:stick", 2, 0)],
                           collision={"x1": 0.4, "y1": 0, "z1": 0.4, "x2": 0.6, "y2": 1, "z2": 0.6},
                           selection={"x1": 0.4, "y1": 0, "z1": 0.4, "x2": 0.6, "y2": 1, "z2": 0.6}))
    out.append(model_block("l23-barrel", "// Level 23 (round 3): Base Seedling's water barrels (only looks: drink at the spring)", "barrel", "Wood",
                           {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]}, drops=[G.drop("game:plank-oak", 2, 1)],
                           collision={"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.88, "z2": 0.9},
                           selection={"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.88, "z2": 0.9}))
    out.append(model_block("l23-bedroll", "// Level 23 (round 3): a bedroll by the tents at Base Seedling (only looks)", "bedroll", "Cloth",
                           {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
                           sides=True, selection={"x1": 0.1, "y1": 0, "z1": 0, "x2": 0.9, "y2": 0.25, "z2": 1}))
    out.append(model_block("l23-firering", "// Level 23 (round 3): Base Seedling's fire ring, its embers glowing", "firering", "Stone",
                           {"walk": "game:walk/stone*", "place": STONE[1], "break": STONE[1], "hit": STONE[1]},
                           selection={"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.2, "z2": 1}, light=[7, 7, 10]))
    out.append(model_block("l23-lantern", "// Level 23 (round 3): the M.E.G.'s lanterns at Base Seedling and down its tunnels, and the lamp on the Lighthouse (breaks to nothing: the balance review)",
                           "lantern", "Metal", {"walk": "game:walk/stone*", "place": "game:block/anvil", "break": "game:block/glass", "hit": "game:block/anvil"},
                           selection={"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 0.65, "z2": 0.7},
                           collision={"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 0.6, "z2": 0.7}, light=[7, 4, 14]))
    out.append(G.cube_block("l23-mossbark", "// Level 23 (round 3): moss grown up over the foot of a trunk and over its roots", ["block/23/mossbark", "block/23/mossbark-2"],
                            "Wood", *WOOD, 7, drops=[G.drop("game:firewood", 0.4, 0.4)], faces={"up": "block/23/moss", "down": "block/23/heartwood-grey"}))
    out.append(model_block("l23-squirtrack", "// Level 23 (round 3): the M.E.G.'s Almond Water squirt guns on their rack (only looks)", "squirtrack", "Wood",
                           {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]}, sides=True,
                           selection={"x1": 0.05, "y1": 0, "z1": 0.4, "x2": 0.95, "y2": 0.75, "z2": 0.92}))
    out.append(model_block("l23-ledger", "// Level 23 (round 3): the quartermaster's ledger, open", "ledger", "Cloth",
                           {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
                           selection={"x1": 0.2, "y1": 0, "z1": 0.25, "x2": 0.8, "y2": 0.1, "z2": 0.75}))
    out.append(model_block("l23-cloth", "// Level 23 (round 3): rags of the Architects' cloth in the ruins", "cloth", "Cloth",
                           {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
                           drops=[G.drop("game:cloth-plain", 0.5, 0.5)],
                           selection={"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.1, "z2": 0.9}))
    sides_tex = {}
    for s in SIDES:
        sides_tex[f"*-{s}"] = {"all": {"base": "block/23/ruinstone"}, s: {"base": "block/23/fresco"}}
    out.append(("// Level 23 (round 3): a damaged painting on the inside of a ruin's wall (the painted face on the -side)", {
        "code": "l23-fresco", "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "texturesByType": sides_tex, "resistance": 8, "drops": [],
        "sounds": {"walk": STONE[0], "place": STONE[1], "break": STONE[1], "hit": STONE[1]}}))
    body_tex = {}
    for s in SIDES:
        body_tex[f"*-{s}"] = {"all": {"base": "block/23/bark-grey"}, "up": {"base": "block/23/heartwood-grey"},
                              "down": {"base": "block/23/heartwood-grey"}, s: {"base": "block/23/sentry-body"}}
    out.append(("// Level 23 (round 3): a buried sentry's body under its face, shoulders and hands pushed out of the bark", {
        "code": "l23-sentrybody", "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}, "blockmaterial": "Wood", "drawtype": "cube",
        "texturesByType": body_tex, "resistance": 9, "drops": [],
        "sounds": {"walk": WOOD[0], "place": WOOD[1], "break": WOOD[1], "hit": WOOD[1]}}))
    return out


def shapes():
    out = {"stone-shrub": stone_shrub(), "stone-sapling": stone_sapling(), "stone-fern": stone_fern(), "stone-stump": stone_stump(),
           "bracket": bracket(), "signboard": signboard(), "signpost": signpost(), "barrel": barrel(), "bedroll": bedroll(),
           "firering": firering(), "ledger": ledger(), "lantern": lantern(), "squirtrack": squirtrack(), "cloth": cloth_shape()}
    for c in ["teal", "violet", "amber"]:
        out[f"glowbush-{c}"] = glowbush(c)
    return out


def textures(save):
    save(aspen(2410), "block/23/bark-aspen")
    save(G.lichened(aspen(2411), 2412, (150, 160, 128)), "block/23/bark-aspen-2")
    save(G.heartwood((206, 204, 192), 2413), "block/23/heartwood-aspen")
    save(boulder(2414), "block/23/boulder")
    save(boulder(2415, mossy=1), "block/23/boulder-2")
    save(mushcap_top(2416), "block/23/mushcap-top")
    save(mushcap_gills(2417), "block/23/mushcap-gills")
    save(mushcap_side(2418), "block/23/mushcap-side")
    save(mushstem(2419), "block/23/mushstem")
    save(flagstone(2420), "block/23/flagstone")
    save(planks(2421), "block/23/planks")
    save(crate(2422), "block/23/crate")
    save(barrel_side(2423), "block/23/barrel-side")
    save(barrel_top(2424), "block/23/barrel-top")
    save(canvas(2425), "block/23/canvas")
    save(blanket(2426), "block/23/blanket")
    save(embers(2427), "block/23/embers")
    save(charred(2428), "block/23/charred")
    save(fresco(2429), "block/23/fresco")
    save(cloth(2430), "block/23/cloth")
    save(sentry_body(2431), "block/23/sentry-body")
    save(ledger_tex(2432), "block/23/ledger")
    save(lantern_glass(2433), "block/23/lantern-glass")
    save(plastic((236, 122, 40), 2434), "block/23/plastic-orange")
    save(plastic((70, 168, 90), 2435), "block/23/plastic-green")
    save(mossbark(2436), "block/23/mossbark")
    save(mossbark(2437), "block/23/mossbark-2")
    for name, parts in [("camp", sign_camp()), ("rules", sign_rules()), ("giants", sign_giants())]:
        for k, img in enumerate(parts):
            save(img, f"block/23/sign-{name}-{'abc'[k]}")
    save(sign_trail()[0], "block/23/sign-trail")
    save(sign_dontsay()[0], "block/23/sign-dontsay")


LANG = [
    ("block-l23-bark-aspen", "Petrified Aspen Bark"),
    ("block-l23-log-*", "Fallen Petrified Log"),
    ("blockdesc-l23-log-*", "A tree of the Garden that came down, a long time ago, and turned to stone where it lay."),
    ("block-l23-boulder", "Mossy Boulder"),
    ("block-l23-mushstem", "Stone Mushroom Stem"),
    ("block-l23-mushcap", "Stone Mushroom Cap"),
    ("blockdesc-l23-mushcap", "A mushroom as big as a shed, gone to stone like everything else up here."),
    ("block-l23-flagstone", "Flagstones"),
    ("block-l23-crate", "M.E.G. Crate"),
    ("block-l23-stoneplant-shrub", "Petrified Shrub"),
    ("block-l23-stoneplant-sapling", "Petrified Sapling"),
    ("block-l23-stoneplant-fern", "Petrified Fern"),
    ("block-l23-stoneplant-stump", "Petrified Stump"),
    ("block-l23-bracket-*", "Stone Bracket Fungus"),
    ("block-l23-glowbush-*", "Glowing Bush"),
    ("blockdesc-l23-glowbush-*", "A bush of thin dark twigs hung with berries that glow. Nobody at Seedling eats them, and nobody will say why."),
    ("block-l23-sign-*", "M.E.G. Sign"),
    ("blockdesc-l23-sign-camp-*", "BASE SEEDLING. M.E.G. outpost 23-1. All welcome."),
    ("blockdesc-l23-sign-rules-*", "Camp rules: 1. Never say it. 2. Water free, food by ration. 3. The tree is the way out: ask first. Pinned beside it, a missing-person notice for a T. Allard and a scrap of a map."),
    ("blockdesc-l23-sign-trail", "Base Seedling, down this way."),
    ("blockdesc-l23-sign-giants-*", "GREEN GIANTS. Do not cut, climb or carve. - M.E.G."),
    ("blockdesc-l23-sign-dontsay", "Painted in a hurry on a plank nailed by the face in the bark: DON'T SAY IT."),
    ("block-l23-signpost", "Sign Post"),
    ("block-l23-barrel", "Water Barrel"),
    ("blockdesc-l23-barrel", "Stencilled WATER. The spring fills them; the M.E.G. say drink from the spring itself."),
    ("block-l23-bedroll-*", "Bedroll"),
    ("block-l23-firering", "Fire Ring"),
    ("block-l23-ledger", "Quartermaster's Ledger"),
    ("block-l23-lantern", "M.E.G. Lantern"),
    ("block-l23-mossbark", "Mossy Petrified Bark"),
    ("block-l23-squirtrack-*", "Squirt Gun Rack"),
    ("blockdesc-l23-squirtrack-*", "Three plastic squirt guns, filled with Almond Water. The M.E.G. at Seedling swear by them. Nobody has said against what."),
    ("blockdesc-l23-lantern", "Bolted down and wired shut. The M.E.G. keep the ways to Seedling lit, and they count their lanterns."),
    ("blockdesc-l23-ledger", "Columns of names and rations. Under the last line: \"5 rescued. 0 back up the tree yet.\""),
    ("block-l23-cloth", "Rags of Cloth"),
    ("block-l23-fresco-*", "Damaged Painting"),
    ("blockdesc-l23-fresco-*", "A garden painted on the plaster, and people in it, with green eyes. Most of it has flaked away."),
    ("block-l23-sentrybody-*", "Buried Sentry"),
    ("blockdesc-l23-sentrybody-*", "Shoulders, and two hands pressed flat against the inside of the bark, as if pushing. Keep quiet."),
]
