"""Level 73, "The Redlands": round 3's furnishings and landscape pieces (2026-11-01), called from gen_73.py (run that, under
the asset lock).

Multi-block objects and the castle's text, after the lead's notes on round 2's shots ("interiors big and bare", "the island
a flat red plate"):
  l73-fire-{logs,cauldron,spit}-*   a firebox: soot-black back, firedogs, burning logs (a cauldron on a chain, a spit)
  l73-mantel-*                      the stone lintel over a fireplace with its mantel shelf and two candlesticks
  l73-canopy-{h0,h1,f0,f1}-{red,black}-*  a four-poster's frame over two hotel beds side by side (posts, tester, valance,
                                    drapes): the lore's "two large beds"
  l73-rug-{red,blue}-{part}         a bordered rug let into the floor (the part names the border it carries)
  l73-floorboards                   a floor slab: aged boards on top, a plaster ceiling below
  l73-beam-{ns,ew}                  a dark oak ceiling beam
  l73-cornice-*                     the damask's top course under a carved cornice (lined like l73-damask)
  l73-stairrail-{east,west}, l73-rail-*   the grand stair's balustrade and the rail round its stairwell
  l73-tapestry-{hunt,castle}-{bl,br,tl,tr}-*  a tapestry two blocks by two: Coran and the Great Hound; the castle under the moon
  l73-sampler-{l,r}-*               a needlework sampler, the page's own words: "We are safe here. We are loved here."
  l73-plate-{text}-*                brass plates by the doorways (guest rooms I to VI, the bath, the kitchen ...)
  l73-notice-{text}-*               notes pinned up in a careful hand ("Do not look outside" ...)
  l73-megplacard-*                  the M.E.G.'s plate by the doors (in the mod's placard style)
  l73-chest-*, l73-washstand-*, l73-worktable-{pots,meat}-*, l73-potrack, l73-lectern-*, l73-linen-*
  l73-bonejoint-c{0..63}            a bone of the Great Hound's skeleton, thin, joined to its neighbours (the mask)
  l73-deadwood-{root,trunk,top}, l73-deadbranch-{a,b}-*   the island's dead trees
  l73-boulder-{a,b}-*               black boulders on the fields
  l73-trodden, l73-flags, l73-pathflags   trodden tracks; the kitchen's flagstones; the path's darker, stained flags
Every one is attribute l73Fixed and drops nothing (the castle is "impenetrable and invincible"; nothing on the island is
worth taking).
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFont

import matlib as M
import texlib
from gen_73_castle import CLOTH, ROT, SIDES, WOOD, box, face, fixed, oriented, shape

S = 32
T = "backrooms:block/73/"
STONE = {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
METAL = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}


# ================= Textures =================

def text(img, s, box_, colour, size, font_scale=4):
    """Centred text in a box, drawn large and scaled down."""
    x0, y0, x1, y1 = box_
    big = Image.new("RGBA", ((x1 - x0) * font_scale, (y1 - y0) * font_scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    font = ImageFont.load_default(size=size * font_scale)
    l, t, r, b = d.textbbox((0, 0), s, font=font)
    d.text(((big.width - (r - l)) / 2 - l, (big.height - (b - t)) / 2 - t), s, font=font, fill=colour)
    small = big.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.alpha_composite(small, (x0, y0))


def plaster_ceiling(seed):
    img = M.plaster(seed=seed, base=(196, 184, 160), grain=3, mottle=8)
    M.grime(img, 0.1, seed=seed + 1, color=(120, 100, 78), cover=0.35)
    return img


def oak_beam(seed):
    img = M.wood_planks(seed=seed, base=(64, 40, 26), planks=1, direction="h", grain=5, contrast=1.2)
    M.scratches(img, 4, seed + 1)
    return img


def soot(seed):
    img = M.noise_hv((26, 22, 22), amp=4, seed=seed, mottle=6, hue=1)
    M.grime(img, 0.3, seed=seed + 1, color=(8, 6, 6), cover=0.6)
    return img


def firebrick(seed):
    img = M.brick(seed=seed, base=(70, 40, 32), mortar=(30, 24, 22), course=8, length=16, offset=0.5, mortar_w=1, jitter=8, hue=3,
                  pits=0.03, chamfer=False, grain=3, mottle=6)
    M.grime(img, 0.4, seed=seed + 1, color=(16, 12, 12), cover=0.7)
    return img


def bark(seed, base=(60, 46, 38)):
    img = M.wood_planks(seed=seed, base=base, planks=4, direction="v", grain=6, contrast=1.4)
    M.grime(img, 0.25, seed=seed + 1, color=(20, 14, 12), cover=0.5)
    return img


def log_end(seed):
    img = M.noise_hv((122, 92, 60), amp=6, seed=seed, mottle=5)
    d = ImageDraw.Draw(img)
    for r in (13, 10, 7, 4):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=(92, 66, 40, 255))
    d.ellipse([0, 0, 31, 31], outline=(46, 32, 24, 255), width=2)
    return img


def flame(seed):
    """Flames on a transparent ground: tongues of yellow at the heart going orange and red at the tips."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    tongues = [(rng.uniform(4, 28), rng.uniform(14, 28), rng.uniform(3, 6)) for _ in range(6)]
    for y in range(S):
        for x in range(S):
            best = 0
            for cx, h, w in tongues:
                fy = (S - 1 - y) / h
                if fy > 1:
                    continue
                half = w * (1 - fy) ** 0.8
                if abs(x - cx) <= half:
                    best = max(best, 1 - fy * 0.85 - abs(x - cx) / max(half, 0.5) * 0.3)
            if best > 0:
                c = M.mix((200, 40, 10), (255, 236, 120), min(1, best * 1.2))
                px[x, y] = M.rgba(c)
    return img


def embers(seed):
    img = M.noise_hv((60, 20, 10), amp=10, seed=seed, mottle=6)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(90):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.mix((230, 90, 20), (255, 200, 80), rng.random()))
    return img


def marble(seed, base=(214, 206, 192), vein=(150, 140, 128)):
    try:
        return texlib.marble(base, vein, seed, veins=2)
    except Exception:
        return M.noise_hv(base, amp=5, seed=seed, mottle=8)


def carved_stone(seed):
    img = marble(seed, (186, 180, 170), (132, 126, 118))
    M.bevel(img, (0, 0, 31, 31), width=1, strength=0.2)
    M.inset(img, (4, 4, 27, 27), width=1, strength=0.18)
    return img


def wax(seed):
    return M.noise_hv((230, 220, 190), amp=3, seed=seed, mottle=4)


def velvet(seed, base):
    img = Image.new("RGBA", (S, S))
    px = img.load()
    noise = M.fbm(S, seed, (8, 4))
    for x in range(S):
        ph = math.sin(2 * math.pi * x / 8.0 + 0.4 * math.sin(x * 0.7))
        for y in range(S):
            k = 0.72 + 0.3 * ph + 0.06 * noise[y][x]
            px[x, y] = M.rgba((base[0] * k * 1.08, base[1] * k, base[2] * k))
    return img


RUGS = {
    # field, border, inner border line, motif
    "red": ((122, 22, 26), (40, 30, 64), (186, 146, 70), (210, 180, 110)),
    "blue": ((34, 40, 82), (118, 24, 28), (190, 156, 84), (196, 172, 120)),
}
RUG_PARTS = ["c", "n", "e", "s", "w", "nw", "ne", "se", "sw"]


def rug_whole(seed, pattern):
    """A rug three blocks by three as one 96x96 picture: a border with a running motif, a gold line, a field with a
    lattice of small medallions; worn a little along its nap."""
    field, border, line, motif = RUGS[pattern]
    n = 96
    img = Image.new("RGBA", (n, n), M.rgba(field))
    px = img.load()
    noise = M.fbm(n, seed, (12, 6, 3))
    for y in range(n):
        for x in range(n):
            e = min(x, y, n - 1 - x, n - 1 - y)
            if e < 12:
                c = border
                if e in (2, 9):
                    c = line
                elif 3 < e < 9 and ((x + y) % 8 in (0, 1) or (x - y) % 8 in (0, 1)):
                    c = motif
            elif e in (12, 13):
                c = line
            else:
                # medallions on a 16-block lattice, a diamond with a dot
                cx, cy = (x - 14) % 17 - 8, (y - 14) % 17 - 8
                dd = abs(cx) + abs(cy)
                c = motif if dd in (5, 6) else line if dd <= 1 else field
            k = 0.9 + 0.14 * noise[y][x]
            px[x, y] = M.rgba(tuple(v * k for v in c))
    return img


def rug_part(whole, part):
    """The 32x32 piece of the 96x96 rug a part takes (c the middle; n, e, s, w the edges; the corners)."""
    col = {"w": 0, "nw": 0, "sw": 0, "e": 2, "ne": 2, "se": 2}.get(part, 1)
    row = {"n": 0, "nw": 0, "ne": 0, "s": 2, "sw": 2, "se": 2}.get(part, 1)
    # (the game shows a cube's up face turned half round against the picture: turn each piece to meet it)
    return whole.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)).rotate(180)


def cornice(seed, damask_img):
    """The damask's top course: the paper below, a carved cream cornice above it (a cove, a bead, a dentil row)."""
    img = damask_img.copy()
    px = img.load()
    rows = [(0, (206, 196, 172)), (1, (226, 216, 192)), (2, (190, 178, 152)), (3, (214, 202, 176)), (4, (214, 202, 176)),
            (5, (170, 156, 128)), (6, (220, 208, 182)), (7, (200, 188, 160)), (8, (150, 136, 108)), (9, (198, 184, 150))]
    for y, c in rows:
        for x in range(S):
            k = 1.0
            if y in (6, 7) and x % 4 == 3:
                k = 0.72  # the dentils
            px[x, y] = M.rgba(tuple(v * k for v in c))
    for x in range(S):  # a thin gilt line under the cornice
        px[x, 10] = M.rgba((168, 128, 58))
    return img


def tapestry(kind, seed):
    """A woven hanging 64x64 (two blocks by two): a dark ground, a border of red and gold, and the picture: 'hunt', the
    blind horned giant with chains for arms over the Great Hound; 'castle', the Silver Castle on its hill under the moon.
    Coarse weave lines over all."""
    n = 64
    img = Image.new("RGBA", (n, n), (40, 34, 30, 255))
    d = ImageDraw.Draw(img)
    if kind == "hunt":
        d.rectangle([0, 0, n, n], fill=(52, 44, 36))
        d.rectangle([4, 40, 59, 59], fill=(96, 26, 22))  # the red ground
        d.ellipse([46, 8, 54, 16], fill=(222, 214, 180))  # the moon
        # the Hound, lying slain: a long grey body, legs, a jaw
        d.polygon([(8, 50), (14, 42), (34, 40), (44, 44), (46, 52), (10, 54)], fill=(112, 106, 96))
        d.polygon([(6, 46), (12, 42), (14, 48)], fill=(140, 132, 118))
        for x in (16, 22, 34, 40):
            d.line([(x, 52), (x - 2, 58)], fill=(90, 84, 76), width=2)
        # the giant: black body, horns, the red heart, chains to black gauntlets
        d.rectangle([30, 14, 38, 34], fill=(20, 18, 20))
        d.rectangle([31, 34, 33, 42], fill=(20, 18, 20)); d.rectangle([35, 34, 37, 42], fill=(20, 18, 20))
        d.ellipse([30, 7, 38, 15], fill=(176, 150, 126))
        d.line([(31, 9), (28, 4)], fill=(210, 200, 170), width=2); d.line([(37, 9), (40, 4)], fill=(210, 200, 170), width=2)
        d.rectangle([33, 19, 35, 21], fill=(200, 30, 30))
        for i in range(5):
            d.ellipse([24 - i, 16 + i * 3, 27 - i, 19 + i * 3], outline=(212, 170, 60))
            d.ellipse([41 + i, 16 + i * 3, 44 + i, 19 + i * 3], outline=(212, 170, 60))
        d.rectangle([16, 30, 22, 36], fill=(16, 14, 16)); d.rectangle([46, 30, 52, 36], fill=(16, 14, 16))
    else:
        d.rectangle([0, 0, n, n], fill=(22, 20, 30))
        d.ellipse([10, 8, 22, 20], fill=(226, 220, 190))  # the moon
        d.polygon([(0, 52), (16, 40), (32, 36), (48, 40), (64, 50), (64, 64), (0, 64)], fill=(98, 24, 22))  # the hill
        d.rectangle([20, 26, 44, 40], fill=(176, 180, 188))  # the walls
        for x in range(20, 45, 4):
            d.rectangle([x, 23, x + 1, 26], fill=(176, 180, 188))
        d.rectangle([28, 18, 36, 30], fill=(190, 194, 200))  # the keep
        d.polygon([(19, 26), (22, 16), (25, 26)], fill=(60, 64, 76)); d.polygon([(39, 26), (42, 16), (45, 26)], fill=(60, 64, 76))
        d.rectangle([31, 33, 33, 40], fill=(50, 30, 20))  # the door
        d.line([(32, 40), (30, 63)], fill=(150, 150, 150), width=2)  # the path
    # the border
    d.rectangle([0, 0, n - 1, n - 1], outline=(150, 28, 30), width=3)
    d.rectangle([3, 3, n - 4, n - 4], outline=(196, 156, 70), width=1)
    px = img.load()
    rng = random.Random(seed)
    for y in range(n):
        for x in range(n):
            r, g, b, a = px[x, y]
            k = 0.86 + (0.1 if (x + y) % 2 == 0 else 0) + rng.uniform(-0.04, 0.04)
            if y % 3 == 0:
                k -= 0.05
            k *= 1 + 0.07 * math.sin(2 * math.pi * x / 16 + 0.5 * math.sin(y * 0.11))  # soft vertical folds
            px[x, y] = M.rgba((r * k, g * k, b * k))
    return img


def sampler():
    """The needlework sampler (64x32, two blocks wide): cross-stitch letters on linen, a border of red hearts."""
    img = Image.new("RGBA", (128, 48), M.rgba((214, 204, 176)))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 125, 45], outline=(120, 24, 28), width=2)
    for x in range(8, 124, 10):
        d.polygon([(x, 6), (x + 2, 4), (x + 4, 6), (x + 2, 9)], fill=(150, 28, 30))
        d.polygon([(x, 40), (x + 2, 38), (x + 4, 40), (x + 2, 43)], fill=(150, 28, 30))
    text(img, "WE ARE SAFE HERE.", (6, 11, 122, 24), (40, 30, 34, 255), 10)
    text(img, "WE ARE LOVED HERE.", (6, 24, 122, 37), (120, 22, 28, 255), 10)
    px = img.load()
    for y in range(48):
        for x in range(128):
            if (x + y) % 2 == 0:
                M.touch(img, x, y, -0.04)
    return img


PLATES = {
    "i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V", "vi": "VI", "bath": "BATH", "kitchen": "KITCHEN",
    "library": "LIBRARY", "pantry": "PANTRY", "solar": "SOLAR", "dining": "DINING", "laundry": "LAUNDRY",
}


def plate_tex(word):
    img = Image.new("RGBA", (64, 32), M.rgba((168, 132, 62)))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 63, 31], outline=(110, 82, 34), width=2)
    d.rectangle([3, 3, 60, 28], outline=(208, 176, 104), width=1)
    text(img, word, (5, 5, 59, 27), (40, 28, 14, 255), 13 if len(word) <= 4 else 9)
    M.grime(img, 0.12, seed=sum(map(ord, word)), color=(70, 52, 24), cover=0.4)
    return img


NOTICES = {
    "outside": ["DO NOT", "LOOK OUTSIDE.", "- C."],
    "attic": ["THE ATTIC", "IS HIS.", "DO NOT GO UP."],
    "bang": ["IF THEY BANG,", "LET THEM IN."],
    "count": ["WE ARE", "THIRTY-SEVEN."],
}


def notice_tex(key, seed):
    """A sheet of paper pinned up, the words in a careful dark hand."""
    img = M.paper(seed=seed, base=(222, 214, 190))
    big = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    big.alpha_composite(img.resize((64, 64)))
    lines = NOTICES[key]
    h = 48 // len(lines)
    for i, ln in enumerate(lines):
        size = 9 if len(ln) <= 7 else 7 if len(ln) <= 10 else 6
        text(big, ln, (3, 8 + i * h, 61, 8 + (i + 1) * h), (34, 26, 30, 255), size)
    d = ImageDraw.Draw(big)
    d.ellipse([30, 2, 34, 6], fill=(140, 30, 30))  # the pin
    return big


def megplacard():
    img = Image.new("RGBA", (128, 96), M.rgba((42, 48, 48)))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 127, 95], outline=(140, 148, 144))
    d.rectangle([3, 3, 124, 92], outline=(88, 95, 92))
    d.rectangle([6, 6, 121, 30], fill=(180, 42, 34))
    text(img, "M.E.G. - LEVEL 73 - CLASS 5", (8, 8, 120, 28), (20, 16, 12, 255), 9)
    text(img, "RUN TO THE CASTLE.", (6, 38, 122, 58), (232, 228, 212, 255), 8)
    text(img, "NO LIGHT. BANG ON THE DOOR", (6, 60, 122, 80), (232, 228, 212, 255), 8)
    for sx, sy in ((10, 86), (117, 86)):
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(122, 128, 124))
    M.grime(img, 0.14, seed=7373, cover=0.45)
    return img


def linen(seed):
    img = M.fabric(seed=seed, base=(214, 208, 192), weave="plain", contrast=6)
    return img


def copper(seed):
    img = M.noise_hv((168, 92, 52), amp=8, seed=seed, mottle=6)
    M.grime(img, 0.15, seed=seed + 1, color=(60, 90, 70), cover=0.3)
    return img


def meat(seed):
    img = M.noise_hv((128, 30, 30), amp=10, seed=seed, mottle=5)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(40):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba((210, 190, 170))
    return img


def leather(seed):
    return M.noise_hv((74, 36, 24), amp=5, seed=seed, mottle=6)


def pages(seed):
    img = M.paper(seed=seed, base=(226, 218, 196))
    d = ImageDraw.Draw(img)
    for y in range(4, 30, 3):
        d.line([(2, y), (14, y)], fill=(90, 80, 84, 255))
        d.line([(18, y), (30, y)], fill=(90, 80, 84, 255))
    d.line([(16, 0), (16, 31)], fill=(150, 140, 120, 255))
    return img


def mirror(seed):
    img = M.noise_hv((150, 162, 170), amp=4, seed=seed, mottle=8)
    d = ImageDraw.Draw(img)
    d.line([(4, 28), (26, 4)], fill=(196, 206, 212, 255), width=2)
    M.grime(img, 0.18, seed=seed + 1, color=(60, 60, 50), cover=0.4)
    return img


def porcelain(seed):
    return M.noise_hv((226, 226, 218), amp=3, seed=seed, mottle=5)


def old_bone(seed):
    """The Great Hound's bones: old, yellowed ivory going grey, dark in its pores and cracks (darker than round 2's, which
    read as a pale block in the moonlight)."""
    img = M.noise_hv((150, 138, 112), amp=6, seed=seed, mottle=8, hue=2)
    fib = M.fbm(S, seed + 1, (16, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            f = fib[(y * 3) % S][(x // 4) % S] * 20
            px[x, y] = M.rgba((r + f, g + f, b + f * 0.8))
    M.grime(img, 0.3, seed=seed + 4, color=(70, 52, 40), cover=0.55)
    return img


def trodden(seed):
    """Earth trodden to a dark red-brown mud, scuffed, with footprints (boots, bare feet) running along it."""
    img = M.noise_hv((84, 34, 26), amp=6, seed=seed, mottle=8, hue=2)
    M.grime(img, 0.25, seed=seed + 1, color=(40, 16, 14), cover=0.5)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(5):
        x, y = rng.randrange(2, 28), rng.randrange(2, 26)
        d.ellipse([x, y, x + 3, y + 5], fill=(54, 20, 16, 255))
        d.ellipse([x + 1, y + 6, x + 3, y + 8], fill=(54, 20, 16, 255))
    return img


def flags(seed, base=(120, 116, 110), stain=False):
    img = M.brick(seed=seed, base=base, mortar=(56, 52, 50), course=16, length=16, offset=0.5, mortar_w=1, jitter=12, hue=3,
                  pits=0.03, chamfer=True, grain=4, mottle=8)
    M.grime(img, 0.22, seed=seed + 1, color=(52, 44, 40), cover=0.5)
    if stain:
        M.stain(img, seed=seed + 2, radius=8, color=(96, 26, 22), strength=0.45)
        M.crack(img, seed + 3)
    return img


def black_velvet(seed):
    return velvet(seed, (40, 30, 36))


# ================= Shapes =================

def mantel_shape():
    """The stone over a fireplace (the wall to its back, south): a carved lintel, a moulded mantel shelf standing out over
    the room, two candlesticks on it."""
    tex = {"stone": T + "mantelstone", "carved": T + "carvedstone", "iron": T + "sconce-iron", "wax": T + "wax", "glow": T + "sconce-glow"}
    return shape(tex, [
        box("Breast", [0, 0, 4], [16, 16, 16], {"*": "#stone", "north": "#carved"}),
        box("Lintel", [0, 0, 2.5], [16, 4, 4], "#carved"),
        box("Shelf", [-1, 8, 0], [17, 10, 4], "#stone"),
        box("Bracket", [-1, 4, 1], [17, 8, 4], "#stone"),
    ])


def beam_shape(axis):
    tex = {"oak": T + "beam"}
    if axis == "ns":
        return shape(tex, [box("Beam", [5, 10, 0], [11, 16, 16], "#oak")])
    return shape(tex, [box("Beam", [0, 10, 5], [16, 16, 11], "#oak")])


def stairrail_shape(rise):
    """The grand stair's balustrade along the south edge of a step's block (the block over the step), rising east or west:
    turned balusters on the tread and a sloped mahogany handrail."""
    tex = {"wood": T + "mahogany-end", "rail": T + "mahogany"}
    els = []
    for i, x in enumerate((2, 6, 10, 14)):
        lo = -8 if x < 8 else 0
        if rise == "west":
            lo = 0 if x < 8 else -8
        top = (6 + x) if rise == "east" else (22 - x)
        els.append(box(f"Baluster{i}", [x - 0.6, lo, 14.6], [x + 0.6, top, 15.8], "#wood"))
    # the handrail, a run of short level pieces stepping up (a sloped box would need rotation)
    for k in range(8):
        x0 = 2 * k
        y = (6 + x0 + 1) if rise == "east" else (22 - x0 - 1)
        els.append(box(f"Rail{k}", [x0, y, 14.3], [x0 + 2, y + 1.5, 16], "#rail"))
    return shape(tex, els)


def rail_shape():
    """A level balustrade along the back edge (south) of the block: balusters, a handrail and a bottom rail."""
    tex = {"wood": T + "mahogany-end", "rail": T + "mahogany"}
    els = [box("Handrail", [0, 13.5, 14.3], [16, 15, 16], "#rail"), box("Bottom", [0, 0, 14.6], [16, 1.2, 15.8], "#rail")]
    for i, x in enumerate((2, 6, 10, 14)):
        els.append(box(f"Baluster{i}", [x - 0.6, 1.2, 14.6], [x + 0.6, 13.5, 15.8], "#wood"))
    return shape(tex, els)


def framed_shape(texname, l, r):
    """A flat framed picture on the wall (south), one cell of it: l/r whether it carries the frame's left/right side."""
    tex = {"canvas": T + texname, "frame": T + "mahogany-end"}
    els = [{"name": "Canvas", "from": [0, 4, 15.2], "to": [16, 12, 15.8], "faces": {"north": face("#canvas", [0, 0, 16, 16])}},
           box("Top", [0, 12, 14.6], [16, 13, 16], "#frame"), box("Bottom", [0, 3, 14.6], [16, 4, 16], "#frame")]
    if l:
        els.append(box("Left", [0, 3, 14.6], [1, 13, 16], "#frame"))
    if r:
        els.append(box("Right", [15, 3, 14.6], [16, 13, 16], "#frame"))
    return shape(tex, els)


def plate_shape(texname):
    tex = {"plate": T + texname, "brass": T + "gold"}
    return shape(tex, [box("Plate", [4, 6, 15.3], [12, 10, 16], {"*": "#brass", "north": "#plate"},
                           faces={"north": [0, 0, 16, 16], "east": None, "west": None, "up": None, "down": None})])


def notice_shape(texname):
    tex = {"paper": T + texname}
    return shape(tex, [{"name": "Paper", "from": [4, 3, 15.6], "to": [12, 13, 15.9], "faces": {"north": face("#paper", [0, 0, 16, 16])}}])


def placard_shape():
    tex = {"plate": T + "megplacard", "metal": T + "sconce-iron"}
    return shape(tex, [box("Plate", [0, 4, 15], [16, 16, 16], {"*": "#metal", "north": "#plate"},
                           faces={"north": [0, 0, 16, 16], "east": None, "west": None, "up": None, "down": None, "south": None})])


def chest_shape():
    tex = {"oak": T + "oak", "iron": T + "sconce-iron"}
    return shape(tex, [
        box("Body", [1, 0, 3], [15, 8, 13], "#oak"), box("Lid", [0.6, 8, 2.6], [15.4, 10.5, 13.4], "#oak"),
        box("BandL", [3, 0, 2.6], [4, 10.6, 13.4], "#iron"), box("BandR", [12, 0, 2.6], [13, 10.6, 13.4], "#iron"),
        box("Lock", [7, 6, 2.2], [9, 9, 2.6], "#iron"),
    ])


def washstand_shape():
    tex = {"wood": T + "mahogany", "end": T + "mahogany-end", "marble": T + "marble", "china": T + "porcelain", "mirror": T + "mirror",
           "frame": T + "gold"}
    return shape(tex, [
        box("Cabinet", [2, 0, 6], [14, 11, 15], {"*": "#wood", "up": "#end"}),
        box("Top", [1.5, 11, 5.5], [14.5, 12, 15.5], "#marble"),
        box("Basin", [4, 12, 7], [11, 14, 13], "#china"),
        box("Jug", [11.5, 12, 11], [13.5, 16, 13], "#china"),
        box("Splash", [1.5, 12, 15], [14.5, 15, 15.6], "#marble"),
        box("MirrorFrame", [4, 17, 15.2], [12, 29, 15.8], "#frame"),
        {"name": "Mirror", "from": [4.6, 17.6, 15.1], "to": [11.4, 28.4, 15.1], "faces": {"north": face("#mirror", [0, 0, 16, 16])}},
    ])


def worktable_shape(kind):
    tex = {"oak": T + "oak", "end": T + "mahogany-end", "iron": T + "sconce-iron", "copper": T + "copper", "meat": T + "meat",
           "bread": T + "bread"}
    els = [
        box("Top", [0, 13, 1], [16, 15, 15], "#oak"),
        box("LegA", [1, 0, 2], [3, 13, 4], "#end"), box("LegB", [13, 0, 2], [15, 13, 4], "#end"),
        box("LegC", [1, 0, 12], [3, 13, 14], "#end"), box("LegD", [13, 0, 12], [15, 13, 14], "#end"),
        box("Shelf", [1, 3, 3], [15, 4, 13], "#oak"),
    ]
    if kind == "pots":
        els += [box("Pot", [2.5, 15, 3.5], [6, 17.5, 7], "#copper"), box("PotRim", [2, 17.5, 3], [6.5, 18, 7.5], "#copper"),
                box("Pan", [9, 15, 4], [13, 15.8, 8], "#iron"), box("Handle", [13, 15.2, 5.6], [15.5, 15.6, 6.4], "#iron"),
                box("Bowl", [9.5, 15, 10], [12, 16.3, 12.5], "#copper"), box("Loaf", [3, 15, 10], [6.5, 16.6, 12.5], "#bread"),
                box("Kettle", [3, 4, 5], [7, 8, 9], "#iron")]
    else:
        els += [box("Haunch", [3, 15, 4], [10, 18.5, 10], "#meat"), box("Cleaver", [11, 15, 5], [14, 15.5, 9], "#iron"),
                box("Board", [2, 15, 3], [11, 15.4, 11], "#end"), box("Cut", [11, 15, 10], [14, 16, 13], "#meat")]
    return shape(tex, els)


def lectern_shape():
    tex = {"wood": T + "mahogany", "end": T + "mahogany-end", "pages": T + "pages", "leather": T + "leather"}
    return shape(tex, [
        box("Foot", [3, 0, 4], [13, 1.5, 12], "#end"), box("Post", [6.5, 1.5, 7], [9.5, 12, 10], "#wood"),
        box("Desk", [2, 12, 3], [14, 13.5, 13], "#wood"),
        box("Cover", [2.5, 13.5, 4], [13.5, 14, 12], "#leather"),
        box("Pages", [3, 14, 4.5], [13, 14.6, 11.5], {"*": "#pages", "up": "#pages"}),
    ])


def linen_shape():
    tex = {"oak": T + "oak", "linen": T + "linen"}
    return shape(tex, [
        box("PostL", [0.5, 0, 7], [1.5, 22, 9], "#oak"), box("PostR", [14.5, 0, 7], [15.5, 22, 9], "#oak"),
        box("FootL", [0, 0, 4], [2, 1, 12], "#oak"), box("FootR", [14, 0, 4], [16, 1, 12], "#oak"),
        box("Bar", [0.5, 21, 7.5], [15.5, 22, 8.5], "#oak"),
        box("SheetA", [1.5, 9, 7], [14.5, 21, 7.5], "#linen"), box("SheetB", [1.5, 12, 8.5], [14.5, 21, 9], "#linen"),
    ])


BONE_DIRS = [("n", (0, 0, -1)), ("e", (1, 0, 0)), ("s", (0, 0, 1)), ("w", (-1, 0, 0)), ("u", (0, 1, 0)), ("d", (0, -1, 0))]


def bonejoint_shape(mask):
    """A bone of the skeleton: a knuckle in the middle of the block and a shaft out to every face whose bit is set
    (n e s w u d = 1 2 4 8 16 32), so neighbouring bones join into ribs, spine and legs."""
    tex = {"bone": T + "bone-old"}
    els = [box("Knuckle", [5, 5, 5], [11, 11, 11], "#bone")]
    r = 2.2
    for bit, (name, (dx, dy, dz)) in enumerate(BONE_DIRS):
        if not mask & (1 << bit):
            continue
        lo = [8 - r, 8 - r, 8 - r]
        hi = [8 + r, 8 + r, 8 + r]
        for i, dv in enumerate((dx, dy, dz)):
            if dv < 0:
                lo[i], hi[i] = 0, 5
            elif dv > 0:
                lo[i], hi[i] = 11, 16
        els.append(box("Shaft" + name, lo, hi, "#bone"))
    return shape(tex, els)


def deadwood_shape(part):
    tex = {"bark": T + "deadbark", "end": T + "logend"}
    if part == "root":
        els = [box("Trunk", [3, 0, 3], [13, 16, 13], {"*": "#bark", "up": "#end", "down": "#end"})]
        for i, (a, b) in enumerate((([0, 0, 6], [3, 4, 10]), ([13, 0, 5], [16, 3, 9]), ([6, 0, 0], [10, 5, 3]), ([5, 0, 13], [9, 3, 16]))):
            els.append(box(f"Root{i}", a, b, "#bark"))
        return shape(tex, els)
    if part == "trunk":
        return shape(tex, [box("Lower", [3.5, 0, 3.5], [12.5, 9, 12.5], "#bark"), box("Upper", [4, 9, 3.5], [12, 16, 12], "#bark")])
    # the top: the trunk narrows and forks
    return shape(tex, [
        box("Neck", [5, 0, 4.5], [11, 7, 10.5], "#bark"),
        box("ForkA", [3, 7, 5], [6.5, 13, 8.5], "#bark"), box("ForkA2", [1.5, 13, 5.5], [4, 17, 8], "#bark"),
        box("ForkB", [9, 7, 6], [12, 12, 9.5], "#bark"), box("ForkB2", [10.5, 12, 7], [13, 18, 9], "#bark"),
        box("Twig", [6, 7, 8], [8, 15, 10], "#bark"),
    ])


def deadbranch_shape(kind):
    """A bare branch growing out of the trunk behind it (south) toward the front, crooked and rising (a) or reaching out
    level and forking (b)."""
    tex = {"bark": T + "deadbark"}
    if kind == "a":
        return shape(tex, [
            box("A1", [6.5, 2, 11], [9.5, 5, 21], "#bark"), box("A2", [6, 4, 6], [9, 8.5, 11], "#bark"),
            box("A3", [5.5, 8, 1.5], [8, 13, 6], "#bark"), box("A4", [5.8, 13, 0], [7.5, 18, 2], "#bark"),
            box("Twig", [8, 8, 3], [10.5, 9.5, 5], "#bark"), box("Twig2", [10, 9, 2], [11.5, 12, 3.5], "#bark"),
        ])
    return shape(tex, [
        box("B1", [7, 6, 9], [10, 9, 21], "#bark"), box("B2", [7.5, 7, 3], [9.5, 9.5, 9], "#bark"),
        box("B3", [8, 8, 0], [9.5, 10, 3], "#bark"),
        box("ForkL", [3, 9, 4], [7.5, 10.5, 5.5], "#bark"), box("ForkL2", [2, 10, 3], [3.5, 14, 4.5], "#bark"),
        box("ForkR", [9.5, 9, 6], [13, 11, 7.5], "#bark"), box("ForkR2", [12, 11, 6], [13.5, 15, 7.5], "#bark"),
    ])


def well_shape():
    """The courtyard's well: a ring of stone, boarded over (dry: inv.), two posts, a windlass with its rope and bucket, a
    little slate roof."""
    tex = {"stone": T + "flags", "oak": T + "oak", "iron": T + "sconce-iron", "slate": T + "slate", "rope": T + "linen", "staves": T + "staves"}
    return shape(tex, [
        box("RingN", [0, 0, 0], [16, 9, 2], "#stone"), box("RingS", [0, 0, 14], [16, 9, 16], "#stone"),
        box("RingW", [0, 0, 2], [2, 9, 14], "#stone"), box("RingE", [14, 0, 2], [16, 9, 14], "#stone"),
        box("Boards", [2, 7.5, 2], [14, 8.5, 14], "#oak"),
        box("PostW", [0.5, 9, 7], [2, 26, 9], "#oak"), box("PostE", [14, 9, 7], [15.5, 26, 9], "#oak"),
        box("Windlass", [2, 20, 7.3], [14, 21.5, 8.7], "#oak"), box("Crank", [15.5, 19, 7.6], [16.5, 22, 8.4], "#iron"),
        box("Rope", [7.6, 13, 7.6], [8.4, 20, 8.4], "#rope"), box("Bucket", [6, 9.5, 6], [10, 13, 10], "#staves"),
        box("RoofN", [-1, 26, 1], [17, 27, 8], "#slate"), box("RoofS", [-1, 26, 8], [17, 27, 15], "#slate"),
        box("Ridge", [-1, 27, 7], [17, 28, 9], "#slate"),
    ])


def cart_shape():
    """A hand cart for hauling the dead in, its shafts to the front (north), a wheel either side."""
    tex = {"oak": T + "oak", "iron": T + "sconce-iron", "end": T + "logend", "hide": T + "hide"}
    return shape(tex, [
        box("Bed", [2, 6, 3], [14, 7, 16], "#oak"), box("SideW", [2, 7, 3], [3, 11, 16], "#oak"), box("SideE", [13, 7, 3], [14, 11, 16], "#oak"),
        box("Back", [2, 7, 15], [14, 10, 16], "#oak"),
        box("WheelW", [0, 0, 7], [2, 10, 13], {"*": "#iron", "west": "#end", "east": "#end"}),
        box("WheelE", [14, 0, 7], [16, 10, 13], {"*": "#iron", "west": "#end", "east": "#end"}),
        box("ShaftW", [3, 5, -8], [4, 6, 3], "#oak"), box("ShaftE", [12, 5, -8], [13, 6, 3], "#oak"),
        box("Load", [4, 7, 5], [12, 10, 14], "#hide"),
    ])


def larder_shape():
    """Oak shelves against the wall (south), stocked: crocks, jars, a cheese, a loaf, sacks on the bottom board (fixed: the
    castle's food is the table's; these give nothing)."""
    tex = {"oak": T + "oak", "end": T + "mahogany-end", "china": T + "porcelain", "copper": T + "copper", "linen": T + "linen",
           "bread": T + "bread", "wax": T + "wax", "glass": T + "glass-full"}
    els = [box("SideL", [0, 0, 9], [1, 16, 16], "#end"), box("SideR", [15, 0, 9], [16, 16, 16], "#end"),
           box("Back", [1, 0, 15.4], [15, 16, 16], "#oak")]
    for i, y in enumerate((0, 5, 10, 15)):
        els.append(box(f"Board{i}", [1, y, 9], [15, y + 1, 15.4], "#oak"))
    els += [box("Sack", [2, 1, 10], [8, 5, 15], "#linen"), box("Sack2", [8.5, 1, 10.5], [14, 4.5, 15], "#linen"),
            box("Crock", [2, 6, 10.5], [5, 10, 13.5], "#china"), box("Jar", [6, 6, 11], [8, 9, 13], "#glass"),
            box("Jar2", [9, 6, 11], [11, 9.5, 13], "#glass"), box("Pot", [11.5, 6, 10.5], [14.5, 9, 13.5], "#copper"),
            box("Cheese", [2, 11, 10.5], [6, 13, 14], "#wax"), box("Loaf", [7, 11, 11], [11, 13, 14], "#bread"),
            box("Crock2", [11.5, 11, 10.5], [14, 14.5, 13.5], "#china")]
    return shape(tex, els)


def sacks_shape():
    tex = {"linen": T + "linen", "rope": T + "oak"}
    return shape(tex, [box("SackA", [1, 0, 2], [8, 9, 9], "#linen"), box("TieA", [3.5, 9, 4.5], [5.5, 10.5, 6.5], "#rope"),
                       box("SackB", [8, 0, 3], [15, 8, 10], "#linen"), box("SackC", [3, 0, 9], [11, 6, 15], "#linen"),
                       box("SackD", [4, 6, 9.5], [10, 10, 14.5], "#linen")])


def sheeted_shape(kind):
    """Furniture under a dust sheet in the shut attic: an armchair (a), something tall, a mirror or a wardrobe (b)."""
    tex = {"sheet": T + "dustsheet"}
    if kind == "a":
        return shape(tex, [box("Seat", [1, 0, 2], [15, 8, 14], "#sheet"), box("Back", [1, 8, 10], [15, 17, 14], "#sheet"),
                           box("ArmL", [0.5, 8, 2], [3, 11, 10], "#sheet"), box("ArmR", [13, 8, 2], [15.5, 11, 10], "#sheet"),
                           box("Hem", [0.5, 0, 1.5], [15.5, 2, 14.5], "#sheet")])
    return shape(tex, [box("Body", [2, 0, 4], [14, 28, 12], "#sheet"), box("Top", [2.5, 28, 4.5], [13.5, 30, 11.5], "#sheet"),
                       box("Hem", [1.5, 0, 3.5], [14.5, 3, 12.5], "#sheet")])


def dustsheet(seed):
    img = M.fabric(seed=seed, base=(176, 170, 156), weave="plain", contrast=5)
    M.grime(img, 0.25, seed=seed + 1, color=(110, 100, 86), cover=0.5)
    return img


def limewash(seed):
    img = M.plaster(seed=seed, base=(206, 200, 184), grain=3, mottle=9)
    M.grime(img, 0.22, seed=seed + 1, color=(120, 104, 84), cover=0.5)
    M.drips(img, 3, seed=seed + 2, color=(130, 112, 90), strength=0.25)
    return img


def hide(seed):
    img = M.noise_hv((46, 42, 44), amp=6, seed=seed, mottle=7)
    M.grime(img, 0.3, seed=seed + 1, color=(80, 20, 18), cover=0.35)
    return img


def boulder_shape(kind):
    tex = {"rock": T + "blackrock"}
    if kind == "a":
        return shape(tex, [box("Core", [2, 0, 3], [14, 9, 13], "#rock"), box("Top", [4, 9, 4], [12, 12, 11], "#rock"),
                           box("Side", [0.5, 0, 5], [2, 6, 11], "#rock"), box("Lip", [5, 0, 13], [12, 5, 15], "#rock")])
    return shape(tex, [box("Core", [1, 0, 2], [15, 13, 14], "#rock"), box("Top", [3, 13, 4], [13, 16, 12], "#rock"),
                       box("Spall", [10, 0, 14], [15, 4, 16], "#rock"), box("Shoulder", [0, 0, 4], [1, 8, 12], "#rock")])


# ================= Round 4 (2026-11-02): the asset-quality pass on the hearth, hangings, beds, barrels, meat, pots =================
# Textures under block/73/r4i-*; geometry built from the helpers below (octagonal prisms, round-ish rods, planes), every face
# mapped by position so a texel is the same size everywhere, and long elements stretched only along their grain.

R4 = T + "r4i-"


def _wobble(rng, n=32, amp=1.0):
    ph = [rng.uniform(0, 6.3) for _ in range(3)]
    return [amp * (0.6 * math.sin(2 * math.pi * x / n + ph[0]) + 0.4 * math.sin(4 * math.pi * x / n + ph[1])) for x in range(n)]


def r4_bark(seed):
    """Rough bark along the length (horizontal): plates split by wavy dark fissures, their upper lips catching the light,
    a little ash and char in the cracks."""
    img = M.noise_hv((74, 58, 46), amp=5, seed=seed, mottle=9, hue=2)
    rng = random.Random(seed)
    for k in range(9):
        y0, amp, per, ph = rng.uniform(0, 32), rng.uniform(0.4, 1.3), rng.choice((1, 2)), rng.uniform(0, 6.3)
        x0, L = rng.uniform(0, 32), rng.uniform(12, 32)
        for i in range(int(L)):
            x = int(x0 + i) % S
            y = int(y0 + amp * math.sin(2 * math.pi * per * x / S + ph)) % S
            M.touch(img, x, y, -0.42)
            M.touch(img, x, y + 1, -0.16)
            M.touch(img, x, y - 1, 0.14)
    M.grime(img, 0.18, seed=seed + 1, color=(22, 18, 16), cover=0.4)
    M.scratches(img, 5, seed + 2, length=(3, 7), light=0.12, angle=0)
    return img


def r4_logend(seed):
    """A sawn end: pale heartwood rings round a dark pith, radial checks, the bark rim, charred toward the edge; outside
    the disc, bark (a box's corners show it)."""
    img = M.noise_hv((150, 112, 72), amp=4, seed=seed, mottle=5, hue=2)
    px = img.load()
    rng = random.Random(seed)
    wob = M.fbm(S, seed + 1, (8, 4))
    checks = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - 16, y + 0.5 - 16
            r = math.hypot(dx, dy) + 0.6 * wob[y][x]
            a = math.atan2(dy, dx)
            c = px[x, y]
            if r > 15.0:
                c = M.lift((52, 40, 32), rng.uniform(-6, 6))
            elif r > 13.6:
                c = M.lift((40, 30, 24), rng.uniform(-5, 5))
            else:
                ring = math.sin(r * 2.1) * 0.5 + 0.5
                c = M.lift(c, -14 * ring + (r / 14) * -18)
                if r < 1.4:
                    c = M.lift(c, -40)
                for ca in checks:
                    da = abs((a - ca + math.pi) % (2 * math.pi) - math.pi)
                    if da * max(r, 1) < 0.55 and 3 < r < 13:
                        c = M.lift(c, -46)
                if r > 11.5:
                    c = M.mix(c, (30, 24, 20), (r - 11.5) / 2.1 * 0.7)
            px[x, y] = M.rgba(c)
    return img


def r4_char(seed, glow=True):
    """Charcoal: black, crazed into scales by cracks that glow orange where the fire is in them."""
    img = M.noise_hv((30, 26, 24), amp=4, seed=seed, mottle=5, hue=1)
    px = img.load()
    f1, f2, _ = M.worley(S, M.points(S, 14, seed + 1))
    for y in range(S):
        for x in range(S):
            edge = f2[y][x] - f1[y][x]
            if edge < 1.0:
                if glow:
                    t = 1 - edge
                    px[x, y] = M.rgba(M.mix((150, 40, 12), (255, 170, 60), t * t))
                else:
                    px[x, y] = M.rgba((14, 12, 12))
            elif edge < 1.8:
                px[x, y] = M.rgba(M.lift(px[x, y], 10))
    return img


def r4_embers(seed):
    """The bed of the fire: coals heaped close, each lit at its heart (yellow to deep red), dark ash between."""
    img = M.noise_hv((34, 28, 26), amp=5, seed=seed, mottle=6, hue=1)
    px = img.load()
    rng = random.Random(seed)
    f1, f2, idx = M.worley(S, M.points(S, 40, seed + 1))
    heat = [rng.random() for _ in range(64)]
    for y in range(S):
        for x in range(S):
            h = heat[idx[y][x] % 64]
            edge = f2[y][x] - f1[y][x]
            if edge < 0.8:
                px[x, y] = M.rgba((18, 14, 14))
            elif h > 0.3:
                t = min(1.0, (h - 0.3) / 0.7 * (1.2 - f1[y][x] / 4.0))
                if t > 0:
                    px[x, y] = M.rgba(M.mix((120, 26, 10), (255, 196, 90), t))
    return img


def r4_ash(seed):
    img = M.noise_hv((92, 88, 84), amp=6, seed=seed, mottle=8, hue=1)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((-40, -30, 26))))
    M.grime(img, 0.25, seed=seed + 1, color=(36, 32, 30), cover=0.45)
    return img


def r4_flame(seed, core=False):
    """Flames (cutout: alpha 0 or 255): tongues rising from a broad base and swaying, white-yellow at the root, orange,
    red at the tips; `core` is the narrower, hotter heart."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    n = 4 if core else 7
    tongues = []
    for i in range(n):
        cx = (8 + 16 * (i + 0.5) / n) if core else (3 + 26 * (i + 0.5) / n) + rng.uniform(-1.5, 1.5)
        h = rng.uniform(16, 26) if core else rng.uniform(14, 31)
        if not core and i in (n // 2, n // 2 - 1):
            h = rng.uniform(27, 31)
        tongues.append((cx, h, rng.uniform(2.2, 3.4) if core else rng.uniform(2.6, 4.6), rng.uniform(0, 6.3), rng.uniform(0.8, 2.2)))
    for y in range(S):
        up = S - 1 - y
        for x in range(S):
            best = 0.0
            for cx, h, w, ph, sway in tongues:
                fy = up / h
                if fy > 1:
                    continue
                c = cx + sway * math.sin(fy * 4.0 + ph) * fy
                half = w * (1 - fy) ** 0.7 + (1.2 if up < 3 else 0)
                d = abs(x + 0.5 - c)
                if d <= half:
                    best = max(best, (1 - fy) * (1 - 0.6 * d / max(half, 0.5)))
            if best > 0.04:
                if core:
                    col = M.mix((255, 180, 60), (255, 250, 214), min(1, best * 1.4))
                else:
                    col = M.mix((196, 44, 12), (255, 214, 96), min(1, best * 1.6)) if best < 0.55 else M.mix((255, 214, 96), (255, 246, 200), (best - 0.55) / 0.45)
                px[x, y] = M.rgba(col)
    return img


def r4_castiron(seed):
    """Cast iron, sooted: near black, a sandy casting grain, rubbed lighter in specks, a bloom of rust here and there."""
    img = M.noise_hv((40, 38, 38), amp=5, seed=seed, mottle=6, hue=1)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(60):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(px[x, y], rng.choice((18, 26, -14))))
    M.rust(img, 0.08, seed=seed + 1)
    M.grime(img, 0.2, seed=seed + 2, color=(14, 12, 12), cover=0.5)
    return img


def r4_iron(seed):
    """Wrought iron, black and hammered: dents as soft dark spots with a lit rim, worn bright along its length."""
    img = M.noise_hv((50, 47, 46), amp=4, seed=seed, mottle=6, hue=1)
    rng = random.Random(seed)
    for _ in range(14):
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, -0.25)
        M.touch(img, x + 1, y, -0.12)
        M.touch(img, x, y - 1, 0.18)
    M.scratches(img, 6, seed + 1, length=(4, 10), light=0.26, angle=0)
    M.rust(img, 0.07, seed=seed + 2)
    return img


def r4_fireback(seed):
    """A cast-iron fireback: a raised border and the Silver Castle's heart and horns in relief, sooted, glowing a little
    red at its foot."""
    import gen_73_castle as castle
    img = r4_castiron(seed)
    d = ImageDraw.Draw(img)
    castle.heart_horns(d, 16, 6, 6.4, (84, 78, 76, 255), outline=(22, 20, 20, 255))
    M.bevel(img, (1, 1, 31, 31), width=2, strength=0.3)
    M.inset(img, (4, 4, 28, 28), width=1, strength=0.25)
    M.grime(img, 0.25, seed=seed + 3, color=(10, 8, 8), cover=0.5, bias="bottom")
    return img


def r4_roast(seed):
    """A haunch on the spit: browned crust, darker caramel cracks, glints of fat."""
    img = M.noise_hv((128, 66, 30), amp=7, seed=seed, mottle=10, hue=3)
    px = img.load()
    rng = random.Random(seed)
    f1, f2, _ = M.worley(S, M.points(S, 18, seed + 1))
    for y in range(S):
        for x in range(S):
            if f2[y][x] - f1[y][x] < 0.9:
                px[x, y] = M.rgba(M.lift(px[x, y], -40))
    for _ in range(26):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba((236, 196, 130))
    M.grime(img, 0.2, seed=seed + 2, color=(46, 22, 12), cover=0.4)
    return img


def r4_potmouth(seed):
    """The cauldron seen from above (mapped by position, its centre at the block's): the rolled iron lip round a stew
    with bubbles and scraps, darker in the shadow under the lip."""
    img = r4_castiron(seed)
    px = img.load()
    rng = random.Random(seed)
    stew = M.noise_hv((104, 50, 28), amp=6, seed=seed + 1, mottle=10, hue=3).load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if r < 8.6:
                c = stew[x, y]
                if r > 7.2:
                    c = M.lift(c, -30 * (r - 7.2) / 1.4)
                px[x, y] = M.rgba(c)
            elif r < 10.6:
                px[x, y] = M.rgba(M.lift(px[x, y], 22 if r < 9.4 else 6))
    for _ in range(14):
        x, y = rng.randrange(10, 22), rng.randrange(10, 22)
        if math.hypot(x - 16, y - 16) < 6.5:
            px[x, y] = M.rgba(rng.choice([(176, 120, 60), (90, 120, 50), (210, 170, 110)]))
    return img


def r4_fringe(seed):
    """A gold bullion fringe (cutout): a braided heading 5 px deep, then twisted threads hanging, every eighth px a
    tassel's knot; ragged at the ends."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    for y in range(5):
        for x in range(S):
            k = 0.9 + 0.25 * (((x + y) % 4) < 2) - 0.15 * (y in (0, 4))
            px[x, y] = M.rgba((188 * k, 146 * k, 58 * k))
    for x in range(S):
        if x % 2:
            continue
        L = rng.randint(22, 30)
        shade = rng.uniform(0.8, 1.15)
        for y in range(5, 5 + L):
            if y >= S:
                break
            tw = 1.0 + 0.18 * (((y + x // 2) % 3) == 0)
            px[x, y] = M.rgba((176 * shade * tw, 132 * shade * tw, 50 * shade * tw))
        if x % 8 == 0:
            for y in range(7, 10):
                for dx in (-1, 1):
                    px[(x + dx) % S, y] = M.rgba((206, 164, 70))
    return img


def r4_braid(seed):
    """Gold cord, twisted (diagonal ridges), opaque."""
    img = M.noise_hv((176, 136, 56), amp=5, seed=seed, mottle=5, hue=2)
    for y in range(S):
        for x in range(S):
            k = (x + y) % 4
            M.touch(img, x, y, 0.22 if k == 0 else -0.25 if k == 2 else 0)
    return img


def r4_hem(seed):
    """A tapestry's hem: dark red wool, a gold line woven along it."""
    img = M.fabric(seed=seed, base=(122, 24, 26), weave="twill", contrast=8)
    px = img.load()
    for x in range(S):
        for y in (13, 14, 17, 18):
            px[x, y] = M.rgba((190, 150, 64) if y in (14, 17) else (150, 110, 46))
    return img


def r4_mahogany(seed, direction):
    """Polished mahogany for turned and carved work: close grain along the piece, a sheen."""
    img = M.wood_planks(seed=seed, base=(98, 40, 26), planks=2, direction=direction, grain=3, contrast=0.9, per_plank=4,
                        gap=(80, 32, 22), flecks=0.6)
    for i in range(S):
        for j in range(S):
            x, y = (i, j) if direction == "h" else (j, i)
            t = math.sin(2 * math.pi * (j / S)) * 0.06
            M.touch(img, x, y, t)
    return img


def r4_carved(seed):
    """A carved mahogany moulding (horizontal): a gilt bead, an ogee, a row of dentils, a fillet, every 16 px."""
    img = r4_mahogany(seed, "h")
    px = img.load()
    for y in range(S):
        r = y % 16
        for x in range(S):
            c = px[x, y]
            if r == 0:
                c = M.lift(c, 26)
            elif r in (1, 2):
                c = (190, 150, 64) if r == 1 else (150, 112, 44)
            elif 3 <= r <= 7:
                c = M.lift(c, 18 - (r - 3) * 9)
            elif r == 8:
                c = M.lift(c, -34)
            elif 9 <= r <= 12:
                c = M.lift(c, 10 if x % 4 < 2 else -30) if r < 12 else M.lift(c, -36)
            elif r == 13:
                c = M.lift(c, 14)
            px[x, y] = M.rgba(c)
    return img


def r4_hoop(seed):
    """Hoop iron: a flat band, black, rubbed bright at its edges, rivets every 16 px, rust weeping from them."""
    img = M.noise_hv((46, 43, 42), amp=4, seed=seed, mottle=5, hue=1)
    px = img.load()
    for x in range(S):
        for y in range(S):
            r = y % 8
            if r == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], 24))
            elif r == 7:
                px[x, y] = M.rgba(M.lift(px[x, y], -18))
    for x in range(4, S, 16):
        for y in range(3, S, 8):
            px[x, y] = M.rgba((96, 90, 84))
            px[x + 1, y + 1] = M.rgba((20, 18, 18))
    M.rust(img, 0.12, seed=seed + 1)
    M.scratches(img, 4, seed + 2, length=(3, 6), light=0.3, angle=0)
    return img


def r4_staves(seed):
    """Oak staves (vertical), each its own shade, dark joints, grimy toward the foot."""
    img = M.wood_planks(seed=seed, base=(104, 72, 44), planks=4, direction="v", grain=4, contrast=1.05, per_plank=10,
                        gap=(36, 24, 16))
    M.grime(img, 0.2, seed=seed + 1, color=(46, 36, 26), cover=0.5, bias="bottom")
    return img


def r4_barrelhead(seed):
    """The head of a barrel (mapped by position, its centre at the block's): boards across, the croze groove round them,
    the bung; the stave ends outside it."""
    img = M.wood_planks(seed=seed, base=(112, 80, 50), planks=4, direction="h", grain=4, contrast=1.0, per_plank=8, gap=(40, 28, 18))
    px = img.load()
    ends = M.noise_hv((92, 66, 42), amp=5, seed=seed + 1, mottle=5).load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if r > 9.6:
                a = math.atan2(y + 0.5 - 16, x + 0.5 - 16)
                c = ends[x, y]
                if int((a + math.pi) / (2 * math.pi) * 22) % 2 == 0:
                    c = M.lift(c, -10)
                px[x, y] = M.rgba(c)
            elif r > 8.6:
                px[x, y] = M.rgba((40, 28, 20))
    for y in range(18, 22):
        for x in range(10, 14):
            if math.hypot(x + 0.5 - 12, y + 0.5 - 20) < 2:
                px[x, y] = M.rgba((60, 42, 28))
    M.grime(img, 0.14, seed=seed + 2, color=(50, 40, 30), cover=0.4)
    return img


def r4_copper(seed):
    """Polished copper, hand-hammered: warm, bright streaks along the piece, darker tarnish, a little green in the seams."""
    img = M.brushed_metal(seed=seed, base=(164, 82, 44), direction="h", streak=16, sheen=30)
    rng = random.Random(seed)
    for _ in range(26):  # the hammer's dimples: lit on the upper left, shadowed on the lower right
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, -0.16)
        M.touch(img, x - 1, y - 1, 0.32)
        M.touch(img, x + 1, y + 1, -0.22)
    for x in range(S):  # a bright specular streak and its falloff
        for dy, f in ((0, 0.34), (1, 0.18), (-1, 0.12)):
            M.touch(img, x, int(9 + 1.5 * math.sin(x * 0.3)) + dy, f)
    M.grime(img, 0.28, seed=seed + 1, color=(74, 34, 20), cover=0.45)
    M.grime(img, 0.14, seed=seed + 2, color=(70, 124, 100), cover=0.12)
    return img


def r4_tinned(seed):
    """The inside of a copper pan (mapped centred): bright copper rim, the tinned silver-grey well, a burnt patch."""
    img = r4_copper(seed)
    px = img.load()
    tin = M.brushed_metal(seed=seed + 3, base=(150, 148, 142), direction="h", streak=6, sheen=10).load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if r < 12.5:
                c = tin[x, y]
                if r < 6:
                    c = M.mix(c, (70, 60, 52), 0.35 * (1 - r / 6))
                if r > 11.2:
                    c = M.lift(c, -26)
                px[x, y] = M.rgba(c)
            elif r < 14:
                px[x, y] = M.rgba(M.lift(px[x, y], 26))
    return img


def r4_lid(seed):
    """A copper lid seen from above (centred): concentric spinning rings, a bright rolled edge."""
    img = r4_copper(seed)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            M.touch(img, x, y, 0.12 * math.sin(r * 1.7) + (0.2 if 13 < r < 14.6 else 0))
    return img


def r4_hide(seed):
    """The hordes' hide: coarse grey-black hair in short strokes running down, matted with old blood in patches."""
    img = M.noise_hv((50, 46, 46), amp=5, seed=seed, mottle=8, hue=1)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(220):
        x, y = rng.randrange(S), rng.randrange(S)
        L = rng.randint(2, 5)
        d = rng.choice((-22, -14, 12, 20))
        for i in range(L):
            M.touch(img, x, y + i, d / 100.0 * 2 * (1 - i / L))
    M.stain(img, seed=seed + 1, radius=8, color=(84, 18, 16), strength=0.5)
    M.grime(img, 0.2, seed=seed + 2, color=(70, 20, 18), cover=0.3)
    return img


def r4_flesh(seed):
    """Raw meat: dark red muscle in fibres, white fat marbling, a wet sheen, clotted spots."""
    img = M.noise_hv((132, 30, 30), amp=8, seed=seed, mottle=8, hue=2)
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            if (y + int(2 * math.sin(x * 0.5))) % 5 == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], -22))
    for _ in range(6):
        x0, y0 = rng.uniform(0, S), rng.uniform(0, S)
        for i in range(rng.randint(6, 14)):
            x, y = int(x0 + i) % S, int(y0 + 1.5 * math.sin(i * 0.6)) % S
            px[x, y] = M.rgba((222, 206, 186))
    for _ in range(8):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba((236, 160, 150))
        px[(x + 1) % S, y] = M.rgba((60, 10, 12))
    return img


def r4_rag(seed):
    """A rag of someone's clothes: grey-brown linen, frayed, stained with blood and mud."""
    img = M.fabric(seed=seed, base=(128, 118, 100), weave="plain", contrast=8)
    M.stain(img, seed=seed + 1, radius=10, color=(96, 22, 20), strength=0.55)
    M.grime(img, 0.3, seed=seed + 2, color=(56, 44, 34), cover=0.55)
    M.scratches(img, 6, seed + 3, length=(3, 8), light=-0.3, angle=90, dark_side=False)
    return img


def r4_blood(seed):
    img = M.noise_hv((64, 12, 12), amp=5, seed=seed, mottle=8, hue=1)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(30):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba((120, 30, 26))
    return img


# ---------------- geometry helpers ----------------

FACES6 = ("north", "east", "south", "west", "up", "down")


def _span(a1, a2):
    """A uv range for a span of the model, kept inside the texture: shifted by whole blocks, nudged in, or (longer than a
    block) stretched over the whole texture."""
    if a2 - a1 >= 16:
        return 0.0, 16.0
    off = math.floor(a1 / 16.0) * 16
    a1, a2 = a1 - off, a2 - off
    if a2 > 16:
        a1, a2 = a1 - (a2 - 16), 16.0
    return a1, a2


def _auto_uv(face_, f, t):
    x1, y1, z1 = f
    x2, y2, z2 = t
    if face_ == "north":
        u, v = _span(16 - x2, 16 - x1), _span(16 - y2, 16 - y1)
    elif face_ == "south":
        u, v = _span(x1, x2), _span(16 - y2, 16 - y1)
    elif face_ == "east":
        u, v = _span(16 - z2, 16 - z1), _span(16 - y2, 16 - y1)
    elif face_ == "west":
        u, v = _span(z1, z2), _span(16 - y2, 16 - y1)
    elif face_ == "up":
        u, v = _span(x1, x2), _span(z1, z2)
    else:
        u, v = _span(x1, x2), _span(16 - z2, 16 - z1)
    return [u[0], v[0], u[1], v[1]]


def bb(name, frm, to, tex, faces=FACES6, glow=0, uv=None, rot=None):
    """A box: tex a "#key" or {face: "#key", "*": default}; faces the ones it has; uv {face: [u1, v1, u2, v2]} overrides
    the position mapping; rot (axis, degrees, origin) one turn about one axis."""
    f = [round(v, 3) for v in frm]
    t = [round(v, 3) for v in to]
    fs = {}
    for k in faces:
        tx = tex if isinstance(tex, str) else tex.get(k, tex.get("*"))
        u = (uv or {}).get(k) or _auto_uv(k, f, t)
        fc = {"texture": tx, "uv": [round(max(0.0, min(16.0, v)), 3) for v in u]}
        g = glow.get(k, 0) if isinstance(glow, dict) else glow
        if g:
            fc["glow"] = g
        fs[k] = fc
    e = {"name": name, "from": f, "to": t, "faces": fs}
    if rot:
        ax, deg, org = rot
        e["rotationOrigin"] = [round(v, 3) for v in org]
        e["rotation" + ax.upper()] = round(deg, 3)
    return e


_ENDS = {"x": ("west", "east"), "y": ("down", "up"), "z": ("north", "south")}
_SIDES = {"x": ("north", "south", "up", "down"), "y": ("north", "east", "south", "west"), "z": ("east", "west", "up", "down")}


def octo(name, axis, c, a0, a1, a, tex, n=4, w=None, cap0=True, cap1=True, lift=0.03, radial=None, glow=0, rot=None, endtex=None):
    """A prism of apothem `a` along `axis` from a0 to a1, centred at c (the two other coordinates in x, y, z order): n=4,
    a regular octagon (two crossed boxes and the same two turned 45 degrees); n=2, a rounded plus (w the arms' half
    width, 0.62 a by default). The ends (cap0, cap1) step in by `lift` per box so no two lie in one plane; radial maps
    the ends centred (a texture drawn round its middle, its edge at radius `radial`); rot turns the whole (n=2 only)."""
    w = a * math.tan(math.radians(22.5)) if w is None else w
    c1, c2 = c
    out = []
    shapes_ = ((a, w, 0), (w, a, 0), (a, w, 45), (w, a, 45))[:n]
    e0n, e1n = _ENDS[axis]
    for i, (h1, h2, r) in enumerate(shapes_):
        s0 = a0 + (lift * i if cap0 else 0)
        s1 = a1 - (lift * i if cap1 else 0)
        if axis == "x":
            f, t = (s0, c1 - h1, c2 - h2), (s1, c1 + h1, c2 + h2)
            org = (a0, c1, c2)
            hu, hv = h2, h1
        elif axis == "y":
            f, t = (c1 - h1, s0, c2 - h2), (c1 + h1, s1, c2 + h2)
            org = (c1, a0, c2)
            hu, hv = h1, h2
        else:
            f, t = (c1 - h1, c2 - h2, s0), (c1 + h1, c2 + h2, s1)
            org = (c1, c2, a0)
            hu, hv = h1, h2
        fl = list(_SIDES[axis]) + ([e0n] if cap0 else []) + ([e1n] if cap1 else [])
        uv = {}
        if radial:
            k = 8.0 / radial
            for en in (e0n, e1n):
                uv[en] = [8 - hu * k, 8 - hv * k, 8 + hu * k, 8 + hv * k]
        tx = tex
        if endtex:
            et = endtex if isinstance(endtex, tuple) else (endtex, endtex)
            tx = {"*": tex, e0n: et[0], e1n: et[1]}
        rr = (axis, 45, org) if r else rot
        out.append(bb(f"{name}{i}", f, t, tx, faces=fl, uv=uv, glow=glow, rot=rr))
    return out


def rod(name, axis, c, a0, a1, r, tex, k=0.62, **kw):
    return octo(name, axis, c, a0, a1, r, tex, n=2, w=k * r, **kw)


def plane(name, axis, at, lo, hi, tex, glow=255, flip=False, rot=None):
    """A flat picture with no thickness (a flame), facing along `axis` ('z': its face north, 'x': east); lo/hi its two
    other corners. Drawn on one side; the block's OpaqueNoCull pass shows it from both."""
    if axis == "z":
        f, t = (lo[0], lo[1], at), (hi[0], hi[1], at)
        fn = "north"
    else:
        f, t = (at, lo[1], lo[0]), (at, hi[1], hi[0])
        fn = "east"
    u = [16, 0, 0, 16] if flip else [0, 0, 16, 16]
    return bb(name, f, t, tex, faces=(fn,), uv={fn: u}, glow=glow, rot=rot)


def chain(name, x, z, y0, y1, tex, link=1.1, r=0.45):
    """Links hanging from y1 down to y0, turned alternately."""
    out, y, i = [], y1, 0
    while y - link > y0 - 0.01:
        if i % 2 == 0:
            out.append(bb(f"{name}{i}", (x - r, y - link, z - 0.12), (x + r, y, z + 0.12), tex))
        else:
            out.append(bb(f"{name}{i}", (x - 0.12, y - link, z - r), (x + 0.12, y, z + r), tex))
        y -= link * 0.82
        i += 1
    return out


# ---------------- the hearth ----------------

def _firedog(n, x, top):
    """An andiron: a bar running back on which the logs lie, a front upright on scrolled feet, a collar, a brass knob."""
    e = [bb(f"{n}Bar", (x - 0.45, 2.2, 3.4), (x + 0.45, 3.0, 13.2), "#iron"),
         bb(f"{n}BackLeg", (x - 0.45, 1, 12.4), (x + 0.45, 2.2, 13.2), "#iron", faces=("north", "east", "south", "west")),
         bb(f"{n}Foot", (x - 1.8, 1, 2.5), (x + 1.8, 1.5, 3.5), "#iron"),
         bb(f"{n}ToeL", (x - 2.2, 1, 2.4), (x - 1.5, 2.0, 3.6), "#iron"),
         bb(f"{n}ToeR", (x + 1.5, 1, 2.4), (x + 2.2, 2.0, 3.6), "#iron")]
    e += rod(f"{n}Post", "y", (x, 3.0), 1.5, top, 0.55, "#iron")
    e += rod(f"{n}Collar", "y", (x, 3.0), top * 0.6, top * 0.6 + 0.6, 0.8, "#iron")
    e += rod(f"{n}Knob", "y", (x, 3.0), top, top + 1.4, 0.95, "#brass")
    e.append(bb(f"{n}Cap", (x - 0.35, top + 1.4, 2.65), (x + 0.35, top + 1.9, 3.35), "#brass"))
    return e


def _log(name, cx, cy, cz, length, r, yaw, ends=True):
    """A log along x (turned `yaw` about y): a rounded section from two crossed boxes, bark along it, sawn ends with
    rings, its underside charred and glowing."""
    out = []
    for i, (h1, h2) in enumerate(((r, 0.62 * r), (0.62 * r, r))):
        d = 0.03 * i
        f = (cx - length / 2 + d, cy - h1, cz - h2)
        t = (cx + length / 2 - d, cy + h1, cz + h2)
        k = 8.0 / r
        uv = {"east": [8 - h2 * k, 8 - h1 * k, 8 + h2 * k, 8 + h1 * k], "west": [8 - h2 * k, 8 - h1 * k, 8 + h2 * k, 8 + h1 * k]}
        tex = {"*": "#bark", "east": "#end", "west": "#end", "down": "#char"}
        faces = ("north", "south", "up", "down") + (("east", "west") if ends else ())
        out.append(bb(f"{name}{i}", f, t, tex, faces=faces, uv=uv, glow={"down": 150}, rot=("y", yaw, (cx, cy, cz)) if yaw else None))
    return out


def fire_shape(kind):
    """A fire in its hearth, the wall to its back (south): firebrick lining and a cast-iron fireback with the castle's
    emblem, a stone hearth under ash, a bed of embers with coals on it, two andirons with brass knobs carrying the logs
    (round, barked, sawn ends, charred and glowing underneath), and flames in layers (broad tongues crossed, a hot core).
    'cauldron': a cast-iron pot with a rolled lip, lugs and a bail, on a chain from a wrought crane pivoting on the side;
    'spit': the andirons taller with hooks, a spit through a roasting haunch, a crank at its end."""
    tall = kind != "logs"
    tex = {"soot": T + "soot", "brick": T + "firebrick", "stone": T + "mantelstone", "back": R4 + "fireback", "iron": R4 + "iron",
           "cast": R4 + "castiron", "bark": R4 + "bark", "end": R4 + "logend", "char": R4 + "char", "coal": R4 + "coal",
           "ember": R4 + "embers", "ash": R4 + "ash", "f1": R4 + "flame", "f2": R4 + "flamecore", "brass": T + "gold",
           "roast": R4 + "roast", "bone": T + "bone-old", "mouth": R4 + "potmouth"}
    els = [
        bb("Back", (0, 0, 14), (16, 32 if tall else 16, 16), "#brick", faces=("north", "up", "east", "west")),
        bb("Hearth", (0, 0, 0), (16, 1, 14), {"*": "#stone", "up": "#soot"}, faces=("north", "east", "west", "up")),
        bb("Fireback", (2.5, 1, 13.4), (13.5, 14 if tall else 12, 14), {"*": "#cast", "north": "#back"},
           faces=("north", "up", "east", "west"), uv={"north": [0, 0, 16, 16]}),
        bb("Ash", (0.8, 1, 1.2), (15.2, 1.3, 13.4), "#ash", faces=("north", "east", "west", "up")),
        bb("Embers", (2.6, 1.3, 3.6), (13.4, 1.8, 12.6), "#ember", faces=("north", "east", "west", "up"), glow=220),
    ]
    rng = random.Random({"logs": 1, "cauldron": 2, "spit": 3}[kind])
    for i in range(7):
        x, z, s = rng.uniform(3.5, 12.5), rng.uniform(4.2, 12), rng.uniform(0.7, 1.4)
        els.append(bb(f"Coal{i}", (x - s, 1.8, z - s * 0.8), (x + s, 1.8 + s * 0.9, z + s * 0.8), "#coal",
                      faces=("north", "east", "south", "west", "up"), glow=170))
    post_top = 12.6 if kind == "spit" else 7.5
    els += _firedog("DogL", 2.5, post_top)
    els += _firedog("DogR", 13.5, post_top)
    # the logs on the andirons' bars (top 3.0)
    if kind == "logs":
        els += _log("LogFront", 8, 4.25, 6.0, 14.6, 1.25, 5)
        els += _log("LogBack", 8, 4.4, 10.4, 14.0, 1.4, -4)
        els += _log("LogCross", 8, 6.6, 8.2, 11.0, 1.1, 24)
        els += _log("Brand", 4.6, 2.4, 7.6, 4.6, 0.6, -38)
        flame_top, fz = 15.4, 8.2
    elif kind == "cauldron":
        els += _log("LogFront", 8, 4.0, 6.4, 13.6, 1.0, 6)
        els += _log("LogBack", 8, 4.1, 9.8, 13.2, 1.1, -5)
        flame_top, fz = 7.6, 8.0
    else:
        els += _log("LogFront", 8, 4.2, 7.0, 13.6, 1.2, -4)
        els += _log("LogBack", 8, 4.4, 10.6, 13.6, 1.35, 3)
        els += _log("LogCross", 8, 6.4, 8.8, 10, 1.0, -20)
        flame_top, fz = 11.0, 8.8
    h = flame_top - 3.2
    els += [
        plane("FlameBroad", "z", fz, (1.6, 3.2), (14.4, flame_top), "#f1"),
        plane("FlameCrossA", "x", 8, (2.5, 3.4), (13.5, 3.4 + h * 0.86), "#f1", flip=True, rot=("y", 48, (8, 3.4, 8))),
        plane("FlameCrossB", "x", 8, (2.5, 3.4), (13.5, 3.4 + h * 0.8), "#f1", rot=("y", -48, (8, 3.4, 8))),
        plane("FlameCoreA", "z", fz - 1.0, (4.0, 3.6), (12.0, 3.6 + h * 0.62), "#f2"),
        plane("FlameCoreB", "z", fz + 1.4, (4.6, 3.8), (11.6, 3.8 + h * 0.7), "#f2", flip=True),
    ]
    if kind == "cauldron":
        # the crane: a post on pintles against the side, an arm out over the fire, a brace
        els += rod("CranePost", "y", (1.2, 8.0), 1.0, 29.0, 0.6, "#iron")
        els += [bb("PintleLo", (-0.6, 5.5, 7.4), (1.2, 6.5, 8.6), "#iron"), bb("PintleHi", (-0.6, 27.0, 7.4), (1.2, 28.0, 8.6), "#iron")]
        els += rod("CraneArm", "x", (26.0, 8.0), 1.2, 9.4, 0.5, "#iron")
        els.append(bb("ArmTip", (9.0, 24.8, 7.6), (9.8, 26.4, 8.4), "#iron"))
        L = math.hypot(5.0, 7.6)
        els.append(bb("Brace", (3.7 - 0.3, 22.1 - L / 2, 7.7), (3.7 + 0.3, 22.1 + L / 2, 8.3), "#iron",
                      rot=("z", -math.degrees(math.atan2(5.0, 7.6)), (3.7, 22.1, 8.0))))
        els += chain("Chain", 8.0, 8.0, 19.4, 25.6, "#iron")
        els.append(bb("Hook", (7.6, 19.0, 7.4), (8.4, 19.8, 8.6), "#iron"))
        # the pot: a cast-iron belly, three stub legs, the rolled lip round the stew (mapped centred), lugs and a bail
        prof = [(6.6, 7.4, 3.2), (7.4, 8.8, 4.6), (8.8, 12.0, 5.4), (12.0, 13.2, 4.9), (13.2, 13.7, 4.5)]
        for i, (y0, y1, a) in enumerate(prof):
            els += octo(f"Pot{i}", "y", (8, 8), y0, y1, a, "#cast", cap0=(i <= 2), cap1=(i == 2))
        els += octo("Lip", "y", (8, 8), 13.7, 14.5, 5.2, "#cast", endtex=("#cast", "#mouth"))
        for i, (lx, lz) in enumerate(((4.8, 10.0), (11.2, 10.0), (8.0, 4.6))):
            els.append(bb(f"Leg{i}", (lx - 0.5, 5.6, lz - 0.5), (lx + 0.5, 7.6, lz + 0.5), "#cast", faces=("north", "east", "south", "west", "down")))
        els += [bb("LugE", (13.0, 13.0, 7.4), (13.9, 14.2, 8.6), "#cast"), bb("LugW", (2.1, 13.0, 7.4), (3.0, 14.2, 8.6), "#cast")]
        L = math.hypot(3.5, 5.2)
        ang = math.degrees(math.atan2(3.5, 5.2))
        els.append(bb("BailE", (11.75 - 0.25, 16.4 - L / 2, 7.75), (11.75 + 0.25, 16.4 + L / 2, 8.25), "#iron", rot=("z", ang, (11.75, 16.4, 8))))
        els.append(bb("BailW", (4.25 - 0.25, 16.4 - L / 2, 7.75), (4.25 + 0.25, 16.4 + L / 2, 8.25), "#iron", rot=("z", -ang, (4.25, 16.4, 8))))
        els.append(bb("BailTop", (5.6, 18.6, 7.75), (10.4, 19.2, 8.25), "#iron"))
    elif kind == "spit":
        # hooks at the top of the tall andirons; the spit rod through a haunch; the crank at the west end
        zs = 1.6  # the spit, in hooks on the andirons' fronts
        for nm, x in (("L", 2.5), ("R", 13.5)):
            els.append(bb(f"Hook{nm}Arm", (x - 0.3, 10.9, 0.9), (x + 0.3, 11.25, 2.5), "#iron"))
            els.append(bb(f"Hook{nm}Prong", (x - 0.3, 10.9, 0.9), (x + 0.3, 12.5, 1.2), "#iron"))
        els += rod("Spit", "x", (11.6, zs), 0.4, 15.8, 0.35, "#iron")
        els += octo("Haunch", "x", (11.6, zs), 4.6, 11.0, 2.5, "#roast", cap0=False, cap1=False)
        els += rod("HaunchHip", "x", (11.8, zs), 3.6, 4.6, 1.9, "#roast")
        els += rod("HaunchShank", "x", (11.6, zs), 11.0, 12.4, 1.5, "#roast")
        els += rod("Bone", "x", (11.6, zs), 12.4, 13.0, 0.6, "#bone", cap0=False, cap1=False)
        els += rod("Knuckle", "x", (11.6, zs), 13.0, 13.6, 0.95, "#bone")
        els += [bb("CrankArm", (0.4, 8.4, zs - 0.3), (1.1, 12.0, zs + 0.3), "#iron"),
                bb("CrankGrip", (1.1, 8.4, zs - 0.25), (1.9, 9.2, zs + 0.25), "#iron")]
        for i, x in enumerate((6.0, 8.4, 10.2)):
            els.append(bb(f"Drip{i}", (x, 8.2 + 0.4 * i, zs - 0.12), (x + 0.25, 9.2, zs + 0.13), "#roast", faces=("north", "east", "west", "south")))
    return shape(tex, els)


# ---------------- the tapestries ----------------

def _belly(Y):
    """The cloth's front (z) at height Y over the hanging's two blocks (0 its foot, 32 the rod): out from the wall in a
    slight belly at mid height, back toward it at the foot."""
    t = Y / 32.0
    return 14.15 - 1.25 * math.sin(math.pi * min(1.0, t * 1.04)) ** 0.9 + (0.35 * (1 - t) ** 3)


def hanging_shape(texname, with_rod=False, part=None):
    """One cell of a tapestry two blocks by two on the wall to its south: the cloth hangs in a slight belly (bands
    tilted to follow it), a hem and a gold fringe at the foot; the top cells carry the iron rod through cloth tabs, the
    outer end a bracket on the wall and a finial. part bl/br/tl/tr (l is the viewer's left, +x of the north model)."""
    part = part or ("tl" if with_rod else "bl")
    top = part[0] == "t"
    left = part[1] == "l"
    tex = {"cloth": T + texname, "iron": R4 + "iron", "hem": R4 + "hem", "fringe": R4 + "fringe", "brass": T + "gold"}
    base = 16 if top else 0
    els = []
    lo, hi = (1.0, 16.0) if not top else (0.0, 14.6)
    cuts = [lo + (hi - lo) * i / 4 for i in range(5)]
    for i in range(4):
        ya, yb = cuts[i], cuts[i + 1]
        za, zb = _belly(base + ya), _belly(base + yb)
        ym, zm = (ya + yb) / 2, (za + zb) / 2
        L = math.hypot(yb - ya, zb - za) + 0.3
        ang = math.degrees(math.atan2(zb - za, yb - ya))
        fl = ["north", "east", "west"] + (["up"] if top and i == 3 else [])
        els.append(bb(f"Cloth{i}", (0, ym - L / 2, zm), (16, ym + L / 2, zm + 0.45), "#cloth", faces=fl,
                      uv={"north": [0, 16 - yb, 16, 16 - ya]}, rot=("x", ang, (8, ym, zm + 0.2))))
    if not top:
        z0 = _belly(1.0)
        els.append(bb("Hem", (0, 0.4, z0 - 0.2), (16, 1.6, z0 + 0.65), "#hem"))
        els.append(plane("Fringe", "z", z0 + 0.05, (0, -2.4), (16, 0.6), "#fringe", glow=0))
    else:
        zr = _belly(32) - 0.1
        for i in range(4):
            x = 1.0 + 4 * i
            els.append(bb(f"Tab{i}", (x, 13.8, zr - 0.75), (x + 2.0, 16.0, zr + 0.75), "#hem"))
        ox = 16 if left else 0  # the outer end
        sg = 1 if left else -1

        def X(a, b):
            return (min(ox + sg * a, ox + sg * b), max(ox + sg * a, ox + sg * b))

        x0, x1 = X(-16, 1.7)
        els += rod("Rod", "x", (15.0, zr), x0, x1, 0.5, "#iron")
        bx0, bx1 = X(0.4, 1.2)
        els.append(bb("BracketPlate", (bx0 - 0.2, 13.4, 15.5), (bx1 + 0.2, 16.0, 16.0), "#iron"))
        els.append(bb("BracketArm", (bx0, 14.6, zr), (bx1, 15.4, 15.5), "#iron"))
        els += rod("BracketCup", "x", (15.0, zr), bx0 - 0.05, bx1 + 0.05, 0.8, "#iron")
        for nm, a, b, r, tx in (("Collar", 1.7, 2.0, 0.75, "#brass"), ("Ball", 2.0, 3.2, 1.0, "#brass"), ("Neck", 3.2, 3.5, 0.45, "#brass"),
                                ("Tip", 3.5, 4.3, 0.55, "#brass")):
            a_, b_ = X(a, b)
            els += rod(f"Finial{nm}", "x", (15.0, zr), a_, b_, r, tx)
    return shape(tex, els)


# ---------------- the four-posters ----------------

POST_PROFILE = [  # (y from, y to, half width, square?) from the floor (y -32) to the tester (13.5)
    (-32.0, -31.2, 1.45, True), (-31.2, -27.6, 1.2, True), (-27.6, -27.0, 1.05, False), (-27.0, -25.6, 0.95, False),
    (-25.6, -22.8, 1.2, False), (-22.8, -21.2, 0.95, False), (-21.2, -20.6, 1.1, False), (-20.6, -14.2, 0.9, False),
    (-14.2, -13.6, 1.05, False), (-13.6, -3.0, 0.72, False), (-3.0, -2.4, 0.95, False), (-2.4, 9.4, 0.68, False),
    (9.4, 10.0, 0.95, False), (10.0, 13.6, 0.85, True),
]
FINIAL_PROFILE = [(15.2, 15.6, 0.85), (15.6, 16.9, 1.05), (16.9, 17.3, 0.55), (17.3, 18.5, 0.8), (18.5, 19.2, 0.35)]


def canopy_shape(part, cloth):
    """One quarter of a four-poster's frame over two beds side by side (2 x 2 blocks), in the block two over the bed (its
    floor at y -32). Front (the foot) north, head south; part h0/h1/f0/f1: head or foot, x-low (0) or x-high (1). The
    turned post stands round the hotel bed's own corner post (a base block, collars, a vase, ringed shafts, a capital, a
    finial over the cornice); the carved tester frame runs round the outer edges under a stepped cornice; the valance
    hangs from it in pleats with a gold fringe; the curtains at each post are gathered in folds and tied back with a
    gold cord and tassel; at the head, a pleated backcloth."""
    tex = {"post": R4 + "mahog-v", "rail": R4 + "mahog-h", "carved": R4 + "carved", "cloth": T + ("velvet" if cloth == "red" else "velvet-black"),
           "gold": T + "gold", "braid": R4 + "braid", "fringe": R4 + "fringe"}
    head = part[0] == "h"
    hi = part[1] == "1"
    px = 14.75 if hi else 1.25
    pz = 15.75 if head else 0.75
    sx = 1 if hi else -1  # outward along x
    sz = 1 if head else -1  # outward along z
    els = []
    for i, (y0, y1, r, sq) in enumerate(POST_PROFILE):
        if sq:
            els.append(bb(f"Post{i}", (px - r, y0, pz - r), (px + r, y1, pz + r), "#post"))
        else:
            els += rod(f"Post{i}", "y", (px, pz), y0, y1, r, "#post", k=0.8)
    for i, (y0, y1, r) in enumerate(FINIAL_PROFILE):
        els += rod(f"Finial{i}", "y", (px, pz), y0, y1, r, "#post" if i != 3 else "#gold", k=0.75)
    # the frame on the outer edges, the cornice stepping out over it, a gilt bead under it
    xo = 15.85 if hi else 0.15  # the outer face along x
    zo = 16.85 if head else -0.85
    def xr(a, b):  # an x range measured inward (a) to outward (b) from the outer face
        return (min(xo - sx * a, xo + sx * b), max(xo - sx * a, xo + sx * b))
    def zr(a, b):
        return (min(zo - sz * a, zo + sz * b), max(zo - sz * a, zo + sz * b))
    x0, x1 = xr(1.6, 0)
    z0, z1 = zr(1.6, 0)
    els.append(bb("RailX", (x0, 11.0, 0), (x1, 13.6, 16), {"*": "#carved", "up": "#rail", "down": "#rail"}))
    els.append(bb("RailZ", (0, 11.0, z0), (16, 13.6, z1), {"*": "#carved", "up": "#rail", "down": "#rail"}))
    for nm, y0, y1, out in (("CorniceA", 13.6, 14.3, 0.45), ("CorniceB", 14.3, 15.2, 0.9)):
        a, b = xr(1.6, out)
        els.append(bb(f"{nm}X", (a, y0, 0), (b, y1, 16), {"*": "#carved", "up": "#rail", "down": "#rail"}))
        a, b = zr(1.6, out)
        els.append(bb(f"{nm}Z", (0, y0, a), (16, y1, b), {"*": "#carved", "up": "#rail", "down": "#rail"}))
    a, b = xr(0.2, 0.2)
    els.append(bb("BeadX", (a, 10.7, 0), (b, 11.0, 16), "#gold"))
    a, b = zr(0.2, 0.2)
    els.append(bb("BeadZ", (0, 10.7, a), (16, 11.0, b), "#gold"))
    els.append(bb("Tester", (0, 12.6, 0), (16, 13.0, 16), "#cloth", faces=("down",)))
    # the valance in pleats under the frame on both outer edges, a braid along its top, the fringe below
    for i in range(4):
        d = 0.35 if i % 2 else 0.0
        a, b = xr(1.0 - d, -0.4 + d + 0.3)
        els.append(bb(f"ValX{i}", (a, 7.0, 4 * i), (b, 11.0, 4 * i + 4), "#cloth", faces=("north", "south", "east", "west", "down")))
        a, b = zr(1.0 - d, -0.4 + d + 0.3)
        els.append(bb(f"ValZ{i}", (4 * i, 7.0, a), (4 * i + 4, 11.0, b), "#cloth", faces=("north", "south", "east", "west", "down")))
    a, b = xr(1.1, 0.35)
    els.append(bb("BraidX", (a, 10.2, 0), (b, 10.7, 16), "#braid"))
    a, b = zr(1.1, 0.35)
    els.append(bb("BraidZ", (0, 10.2, a), (16, 10.7, b), "#braid"))
    fx = xo + sx * 0.12
    fz = zo + sz * 0.12
    els.append(bb("FringeX", (fx, 4.6, 0), (fx, 7.2, 16), "#fringe", faces=("east",), uv={"east": [0, 0, 16, 16]}))
    els.append(bb("FringeZ", (0, 4.6, fz), (16, 7.2, fz), "#fringe", faces=("north",), uv={"north": [0, 0, 16, 16]}))
    if head:
        # the backcloth behind the headboard, in pleats
        for i in range(4):
            d = 0.35 if i % 2 else 0
            els.append(bb(f"Back{i}", (4 * i, -18, 15.9 + d), (4 * i + 4, 10.4, 16.4 + d), "#cloth", faces=("north", "east", "west")))
    # the curtains at the post: along the side (toward the other end) and, at the foot, along the foot too
    els += _drape("SideCurtain", "z", px + sx * 0.75, pz - sz * 1.4, -sz, sx, sx)
    if not head:
        els += _drape("FootCurtain", "x", pz + sz * 1.2, px - sx * 1.4, -sx, -sz, sz)
    return shape(tex, els)


def _drape(name, run, plane_c, start, along, fold, vis):
    """A velvet curtain gathered at a post: hanging from the tester to the floor in folds (pairs of boxes at different
    depths), widest at the top, narrowing to the tie-back, flaring to the floor; the gold cord round it and its tassel.
    run 'z': it lies in the plane x = plane_c and runs along z from `start` (+1/-1 `along`); 'x': the plane z = plane_c,
    along x. fold: the side (+1/-1) its second fold stands to; vis: the room's side, where the tassel hangs."""
    els = []
    bands = [(-31.8, -24.0, 4.0), (-24.0, -16.6, 2.8), (-14.6, -6.0, 2.6), (-6.0, 3.0, 4.0), (3.0, 10.6, 5.6)]

    def put(nm, d0, d1, a, b, y0, y1, tx):
        lo_, hi_ = min(a, b), max(a, b)
        if run == "z":
            els.append(bb(nm, (d0, y0, lo_), (d1, y1, hi_), tx))
        else:
            els.append(bb(nm, (lo_, y0, d0), (hi_, y1, d1), tx))

    for i, (y0, y1, wdt) in enumerate(bands):
        for j in range(2):
            a = start + along * (j * wdt / 2 - 0.2 * j)
            b = start + along * ((j + 1) * wdt / 2)
            d0 = plane_c - 0.2 + (0.3 * fold if j else 0)
            put(f"{name}{i}{j}", d0, d0 + 0.4, a, b, y0, y1, "#cloth")
    put(f"{name}Tie", plane_c - 0.55, plane_c + 0.55, start - along * 0.3, start + along * 3.1, -16.6, -14.6, "#braid")
    tc = start + along * 1.4
    d = plane_c + vis * 0.75
    put(f"{name}Tassel", d - 0.35, d + 0.35, tc - 0.4, tc + 0.4, -19.6, -16.4, "#gold")
    return els


# ---------------- barrels ----------------

def barrel_shape():
    """A barrel: staves bulging to the middle (an octagon in seven courses), three iron hoops and one at the chime, the
    staves standing proud of the head at the top (the chime), the head's boards and bung."""
    tex = {"staves": R4 + "staves", "hoop": R4 + "hoop", "head": R4 + "barrelhead", "end": R4 + "barrelhead"}
    prof = [(0, 1.4, 5.3), (1.4, 3.8, 5.8), (3.8, 6.2, 6.2), (6.2, 8.2, 6.4), (8.2, 10.6, 6.2), (10.6, 12.8, 5.8)]
    els = []
    for i, (y0, y1, a) in enumerate(prof):
        els += octo(f"Course{i}", "y", (8, 8), y0, y1, a, "#staves", cap0=(i == 0), cap1=False, endtex="#head")
    # the chime: an octagonal ring of stave ends round the sunk head
    a, t = 5.4, 0.85
    hw = a * math.tan(math.radians(22.5)) + 0.25
    ring = [((8 - hw, 8 - a), (8 + hw, 8 - a + t)), ((8 - hw, 8 + a - t), (8 + hw, 8 + a)),
            ((8 - a, 8 - hw), (8 - a + t, 8 + hw)), ((8 + a - t, 8 - hw), (8 + a, 8 + hw))]
    for k, rot45 in enumerate((False, True)):
        for j, ((x0, z0), (x1, z1)) in enumerate(ring):
            d = 0.03 * k
            els.append(bb(f"Chime{k}{j}", (x0, 12.8, z0), (x1, 14.0 - d, z1), {"*": "#staves", "up": "#end"},
                          rot=("y", 45, (8, 12.8, 8)) if rot45 else None))
    for j, (h1, h2) in enumerate(((3.75, 3.75), (4.7, 2.6), (2.6, 4.7))):
        els.append(bb(f"Head{j}", (8 - h1, 12.8, 8 - h2), (8 + h1, 13.3, 8 + h2), "#head", faces=("up",)))
    for i, (y0, y1, a) in enumerate(((1.6, 2.5, 5.95), (6.6, 7.5, 6.55), (11.0, 11.9, 5.95))):
        els += octo(f"Hoop{i}", "y", (8, 8), y0, y1, a, "#hoop", endtex="#hoop")
    import gen_73_r4_props as P
    els += P.ring8("Hoop3", 8, 8, 13.1, 13.9, 5.45, 0.3, "#hoop")  # round the chime: a ring, so the sunk head shows
    els.append(bb("Bung", (7.3, 7.6, 1.45), (8.7, 8.9, 1.75), "#head", faces=("north", "east", "west", "up", "down")))
    return shape(tex, els)


# ---------------- meat and the dead ----------------

def hookmeat_shape():
    """A Hound's carcass hung by its heels under the cellar's ceiling: an iron rail on straps from the ceiling, an S-hook,
    a gambrel spreading the hind legs (paws still on), the rump, the body skinned at the front to the ribs over the
    open cavity, the hide left on its back and flanks, a foreleg hanging, the neck cut."""
    tex = {"hide": R4 + "hide", "meat": R4 + "flesh", "bone": T + "bone-old", "iron": R4 + "iron", "wood": R4 + "mahog-h"}
    els = [bb("CeilPlateW", (0.6, 15.6, 6.8), (2.8, 16.0, 9.2), "#iron"), bb("CeilPlateE", (13.2, 15.6, 6.8), (15.4, 16.0, 9.2), "#iron"),
           bb("StrapW", (1.4, 13.6, 7.7), (2.0, 15.6, 8.3), "#iron"), bb("StrapE", (14.0, 13.6, 7.7), (14.6, 15.6, 8.3), "#iron")]
    els += rod("Rail", "x", (13.6, 8.0), 0.0, 16.0, 0.45, "#iron")
    # the S-hook: over the rail from behind, the shank, the lower hook curling up in front
    els += [bb("SHookTop", (7.7, 14.05, 7.2), (8.3, 14.45, 8.8), "#iron"), bb("SHookBack", (7.7, 13.0, 8.6), (8.3, 14.45, 9.0), "#iron"),
            bb("SHookShank", (7.7, 10.6, 7.8), (8.3, 13.2, 8.3), "#iron"), bb("SHookFoot", (7.7, 10.3, 7.3), (8.3, 10.7, 8.6), "#iron"),
            bb("SHookTip", (7.7, 10.7, 7.0), (8.3, 11.6, 7.4), "#iron")]
    els += rod("Gambrel", "x", (10.5, 8.0), 3.6, 12.4, 0.4, "#wood")
    # the hind legs, from paws over the gambrel down and inward to the rump
    for nm, x, s in (("L", 4.6, 1), ("R", 11.4, -1)):
        els.append(bb(f"Paw{nm}", (x - 0.9, 10.2, 7.0), (x + 0.9, 12.4, 9.6), "#hide"))
        els += rod(f"Hock{nm}", "y", (x, 8.0), 6.2, 10.4, 0.6, "#meat", rot=("z", s * 8, (x, 10.0, 8.0)))
        els += octo(f"Thigh{nm}", "y", (x + s * 1.1, 8.0), -1.6, 6.4, 1.9, "#meat", n=2, w=1.4, rot=("z", s * 10, (x + s * 1.1, 6.4, 8.0)))
        els.append(bb(f"ThighHide{nm}", (x + s * 1.1 - 1.7, -1.4, 8.9), (x + s * 1.1 + 1.7, 6.0, 10.1), "#hide", rot=("z", s * 10, (x + s * 1.1, 6.4, 8.0))))
    els += octo("Rump", "y", (8.0, 8.4), -6.0, -0.8, 3.6, "#meat", n=2, w=2.4)
    els.append(bb("RumpHide", (4.6, -6.0, 8.6), (11.4, -0.4, 11.0), "#hide"))
    # the body: hide on the back and flanks, the cavity open at the front with the ribs across it
    els += [bb("Back", (4.6, -14.6, 8.6), (11.4, -6.0, 11.2), "#hide"),
            bb("FlankW", (4.2, -14.6, 5.4), (5.4, -6.0, 10.6), {"*": "#hide", "north": "#meat"}),
            bb("FlankE", (10.6, -14.6, 5.4), (11.8, -6.0, 10.6), {"*": "#hide", "north": "#meat"}),
            bb("Cavity", (5.4, -14.2, 7.6), (10.6, -6.4, 8.8), "#meat", faces=("north",))]
    for k in range(5):
        y = -13.6 + k * 1.5
        els.append(bb(f"Rib{k}", (5.0, y, 5.4), (11.0, y + 0.55, 6.0), "#bone"))
    els += [bb("Sternum", (7.5, -14.2, 5.0), (8.5, -7.0, 5.5), "#bone"),
            bb("Shoulders", (4.4, -17.2, 5.8), (11.6, -14.6, 10.8), {"*": "#hide", "north": "#meat", "down": "#meat"}),
            bb("Neck", (6.2, -19.4, 6.6), (9.8, -17.2, 10.0), {"*": "#hide", "down": "#meat"}),
            bb("NeckBone", (7.5, -19.8, 7.8), (8.5, -19.4, 8.8), "#bone")]
    els += rod("Foreleg", "y", (10.2, 7.6), -22.4, -16.8, 0.75, "#hide", rot=("z", 10, (10.2, -16.8, 7.6)))
    els.append(bb("ForePaw", (9.1, -23.6, 6.5), (11.3, -22.4, 8.7), "#hide", rot=("z", 10, (10.2, -16.8, 7.6))))
    return shape(tex, els)


def _bone(name, x, y, z, length, yaw, r=0.45, tex="#bone"):
    """A long bone lying along x (turned `yaw`): a shaft and its two knobbed ends."""
    org = (x, y, z)
    return [bb(f"{name}Shaft", (x - length / 2, y, z - r), (x + length / 2, y + 2 * r, z + r), tex, rot=("y", yaw, org)),
            bb(f"{name}EndA", (x - length / 2 - 0.5, y, z - r * 1.9), (x - length / 2 + 0.5, y + 2.4 * r, z + r * 1.9), tex, rot=("y", yaw, org)),
            bb(f"{name}EndB", (x + length / 2 - 0.5, y, z - r * 1.7), (x + length / 2 + 0.5, y + 2.2 * r, z + r * 1.7), tex, rot=("y", yaw, org))]


def _skull(name, x, z, yaw):
    """A Hound's skull, long in the snout, lying on its side; the jaw beside it."""
    org = (x, 0, z)
    rt = ("y", yaw, org)
    return [bb(f"{name}Cranium", (x - 1.6, 0, z - 1.5), (x + 1.4, 2.8, z + 1.5), "#bone", rot=rt),
            bb(f"{name}Brow", (x + 1.0, 1.2, z - 1.2), (x + 1.6, 2.6, z + 1.2), "#bone", rot=rt),
            bb(f"{name}Socket", (x + 1.55, 1.5, z - 1.0), (x + 1.65, 2.3, z + 1.0), "#meat", faces=("east",), rot=rt),
            bb(f"{name}Snout", (x + 1.4, 0.4, z - 0.8), (x + 4.6, 1.9, z + 0.8), "#bone", rot=rt),
            bb(f"{name}Fangs", (x + 3.9, 0.0, z - 0.7), (x + 4.4, 0.6, z + 0.7), "#bone", faces=("north", "south", "east", "west", "down"), rot=rt),
            bb(f"{name}Jaw", (x + 0.2, 0, z - 2.6), (x + 4.2, 0.7, z - 1.8), "#bone", rot=rt)]


def _rag(name, f, t, yaw=0, tilt=None):
    rot = ("y", yaw, ((f[0] + t[0]) / 2, f[1], (f[2] + t[2]) / 2)) if yaw else tilt
    return bb(name, f, t, "#rag", rot=rot)


def carcass_shape(kind):
    """A heap of the hordes' dead dragged in for the fire ("Hound is the fuel"): a Hound's body under its hide, the
    ribcage broken open, a leg thrown out; bones scattered, a skull, the rags of the ones it had eaten, a pool of blood.
    b: mostly bones and rags, a smaller carcass, a ribcage on its own."""
    tex = {"hide": R4 + "hide", "meat": R4 + "flesh", "bone": T + "bone-old", "rag": R4 + "rag", "blood": R4 + "blood"}
    els = [bb("Blood", (0.6, 0.02, 1.0), (15.0, 0.1, 14.6), "#blood", faces=("up",))]
    if kind == "a":
        els += octo("Body", "x", (3.4, 8.0), 2.0, 13.4, 3.3, "#hide", n=2, w=2.2, endtex="#meat")
        els += octo("Haunch", "x", (2.9, 9.4), 10.6, 14.6, 2.7, "#hide", n=2, w=2.0)
        # the ribcage broken open along the top
        els.append(bb("Wound", (4.0, 6.6, 5.6), (11.0, 6.9, 9.6), "#meat", faces=("up", "north", "east", "west")))
        els.append(bb("Spine", (3.4, 6.6, 9.4), (11.4, 7.4, 10.2), "#bone"))
        for k in range(6):
            x = 4.0 + 1.3 * k
            els.append(bb(f"RibTop{k}", (x, 7.4, 6.4), (x + 0.5, 7.9, 10.0), "#bone"))
            els.append(bb(f"RibFront{k}", (x, 5.4 + (k % 2) * 0.6, 6.0), (x + 0.5, 7.9, 6.5), "#bone"))
        # a hind leg thrown out over the floor, a foreleg folded under
        els += rod("Thigh", "x", (2.0, 13.2), 11.0, 14.8, 1.1, "#hide", rot=("y", -30, (11.0, 2.0, 13.2)))
        els.append(bb("Paw", (13.2, 0.1, 14.2), (15.4, 1.3, 16.0), "#hide"))
        els += rod("Foreleg", "z", (1.6, 1.0), 0.4, 4.6, 0.75, "#hide", rot=("y", 25, (1.6, 1.0, 4.6)))
        els += _skull("Skull", 3.0, 14.0, -10)
        els += _bone("BoneA", 6.0, 0.1, 1.8, 6.0, 12)
        els += _bone("BoneB", 12.0, 0.1, 3.0, 4.6, -50)
        els += [_rag("RagA", (0.6, 0.1, 9.6), (4.6, 0.35, 12.8), yaw=20),
                _rag("RagDrape", (5.0, 1.2, 4.3), (9.6, 5.4, 4.75), tilt=("x", -8, (7.3, 5.4, 4.5))),
                _rag("RagB", (11.0, 0.1, 6.0), (14.8, 0.3, 9.6), yaw=-15)]
    else:
        els += octo("Body", "x", (2.7, 9.8), 3.0, 11.0, 2.5, "#hide", n=2, w=1.8, endtex="#meat")
        # a ribcage standing on its own, the spine along its top
        els.append(bb("Spine", (3.0, 5.0, 4.4), (11.4, 5.6, 5.2), "#bone"))
        for k in range(6):
            x = 3.6 + 1.35 * k
            hgt = 5.6 - abs(k - 2.5) * 0.25
            els.append(bb(f"RibL{k}", (x, 0.3, 2.4), (x + 0.45, hgt, 2.9), "#bone"))
            els.append(bb(f"RibR{k}", (x, 0.3, 6.7), (x + 0.45, hgt, 7.2), "#bone"))
            els.append(bb(f"RibTop{k}", (x, hgt - 0.5, 2.4), (x + 0.45, hgt, 7.2), "#bone"))
        els += _skull("Skull", 10.8, 12.8, -15)
        els += _skull("SkullB", 13.6, 2.0, -100)
        els += _bone("BoneA", 7.0, 0.1, 13.6, 7.0, 6)
        els += _bone("BoneB", 9.0, 0.95, 13.2, 5.6, -24)
        els += _bone("BoneC", 3.0, 0.1, 13.0, 4.0, 70)
        els += rod("Leg", "x", (1.2, 10.8), 9.0, 15.6, 1.0, "#hide", rot=("y", 30, (9.0, 1.2, 10.8)))
        els += [_rag("RagA", (1.0, 0.1, 1.0), (6.0, 0.35, 4.8), yaw=-12),
                _rag("RagB", (8.4, 0.1, 8.6), (13.0, 0.4, 11.6), yaw=30),
                _rag("RagC", (4.0, 2.4, 8.2), (9.0, 5.2, 8.6), tilt=("x", -15, (6.5, 2.4, 8.4))),
                _rag("RagD", (10.0, 0.1, 0.4), (14.6, 0.3, 2.6))]
    return shape(tex, els)


# ---------------- the pot rack ----------------

def _pan(name, cx, cy, cz, a, handle):
    """A copper frying pan hung by its handle: the disc upright (an octagon about z, its tinned face north), a rolled
    rim, the iron handle up to the hook."""
    els = octo(f"{name}Disc", "z", (cx, cy), cz - 0.3, cz + 0.3, a, "#copper", radial=a, endtex=("#tinned", "#copper"))
    els += [bb(f"{name}Handle", (cx - 0.35, cy + a - 0.2, cz - 0.2), (cx + 0.35, cy + a + handle, cz + 0.25), "#iron"),
            bb(f"{name}Eye", (cx - 0.6, cy + a + handle - 0.2, cz - 0.25), (cx + 0.6, cy + a + handle + 0.8, cz + 0.3), "#iron")]
    return els


def _stockpot(name, cx, cz, y0):
    """A copper stockpot hanging upright on its bail: the body, a rolled lip, two lugs, the lid with its knob, the bail
    up to the hook."""
    els = octo(f"{name}Body", "y", (cx, cz), y0, y0 + 3.6, 2.4, "#copper", endtex="#tinned", radial=2.4)
    els += octo(f"{name}Lip", "y", (cx, cz), y0 + 3.6, y0 + 4.0, 2.6, "#copper", endtex="#lid", radial=2.6)
    els += rod(f"{name}Knob", "y", (cx, cz), y0 + 4.0, y0 + 4.6, 0.5, "#iron")
    els += [bb(f"{name}LugW", (cx - 3.0, y0 + 3.0, cz - 0.4), (cx - 2.4, y0 + 3.6, cz + 0.4), "#iron"),
            bb(f"{name}LugE", (cx + 2.4, y0 + 3.0, cz - 0.4), (cx + 3.0, y0 + 3.6, cz + 0.4), "#iron")]
    L = math.hypot(2.2, 3.6)
    ang = math.degrees(math.atan2(2.2, 3.6))
    ym = y0 + 3.3 + 1.8
    els += [bb(f"{name}BailW", (cx - 1.75 - 0.18, ym - L / 2, cz - 0.18), (cx - 1.75 + 0.18, ym + L / 2, cz + 0.18), "#iron", rot=("z", -ang, (cx - 1.75, ym, cz))),
            bb(f"{name}BailE", (cx + 1.75 - 0.18, ym - L / 2, cz - 0.18), (cx + 1.75 + 0.18, ym + L / 2, cz + 0.18), "#iron", rot=("z", ang, (cx + 1.75, ym, cz))),
            bb(f"{name}BailTop", (cx - 0.8, y0 + 7.1, cz - 0.18), (cx + 0.8, y0 + 7.5, cz + 0.18), "#iron")]
    return els


def potrack_shape():
    """An iron rack hung under the kitchen's ceiling on four chains: two rails and their cross bars, S-hooks, and on them
    copper pans (upright, tinned faces out), stockpots with their lids on their bails, a saucepan by its handle, a lid,
    a ladle."""
    tex = {"iron": R4 + "iron", "copper": R4 + "copper", "tinned": R4 + "tinned", "lid": R4 + "lid", "brass": T + "gold"}
    els = []
    for nm, z in (("Front", 4.0), ("Back", 12.0)):
        els += rod(f"Rail{nm}", "x", (12.6, z), 0.6, 15.4, 0.4, "#iron")
    for nm, x in (("W", 1.4), ("E", 14.6)):
        els.append(bb(f"Cross{nm}", (x - 0.4, 12.2, 3.4), (x + 0.4, 12.9, 12.6), "#iron"))
        for z in (4.0, 12.0):
            els += chain(f"Chain{nm}{int(z)}", x, z, 13.0, 15.8, "#iron", link=1.0, r=0.4)
            els.append(bb(f"Ceil{nm}{int(z)}", (x - 0.8, 15.7, z - 0.8), (x + 0.8, 16.0, z + 0.8), "#iron", faces=("north", "east", "south", "west", "down")))
    # S-hooks along both rails
    hooks = [(3.6, 4.0), (8.0, 4.0), (12.2, 4.0), (3.4, 12.0), (7.6, 12.0), (11.6, 12.0)]
    for i, (x, z) in enumerate(hooks):
        els += [bb(f"Hook{i}Top", (x - 0.2, 12.95, z - 0.55), (x + 0.2, 13.3, z + 0.55), "#iron"),
                bb(f"Hook{i}Shank", (x - 0.2, 10.9, z + 0.2), (x + 0.2, 12.95, z + 0.55), "#iron"),
                bb(f"Hook{i}Foot", (x - 0.2, 10.6, z - 0.6), (x + 0.2, 10.95, z + 0.55), "#iron")]
    els += _pan("PanBig", 3.6, 4.6, 4.0, 3.0, 2.4)
    els += _stockpot("Stock", 8.0, 4.0, 3.2)
    els += _pan("PanSmall", 12.2, 6.2, 4.0, 2.2, 2.0)
    # the back rail: a saucepan by its long handle (the pot's mouth turned north), a lid, a ladle
    els += octo("SaucepanBody", "z", (3.4, 4.8), 11.0, 13.6, 2.0, "#copper", radial=2.0, endtex=("#tinned", "#copper"))
    els += [bb("SaucepanHandle", (3.1, 6.6, 11.9), (3.7, 10.9, 12.4), "#iron")]
    els += octo("Lid", "z", (7.6, 7.4), 11.8, 12.2, 2.4, "#copper", radial=2.4, endtex="#lid")
    els += [bb("LidLoop", (7.3, 9.6, 11.8), (7.9, 10.9, 12.2), "#iron"), bb("LidKnob", (7.2, 6.9, 11.4), (8.0, 7.7, 11.8), "#iron")]
    els += [bb("LadleHandle", (11.4, 5.2, 11.8), (11.8, 10.9, 12.2), "#iron"),
            bb("LadleNeck", (11.4, 4.4, 11.4), (11.8, 5.4, 12.0), "#iron")]
    els += octo("LadleBowl", "y", (11.6, 11.4), 2.8, 4.4, 1.3, "#copper", endtex="#tinned", radial=1.3)
    return shape(tex, els)


def r4_textures(sv):
    sv(r4_bark(7601), "r4i-bark")
    sv(r4_logend(7602), "r4i-logend")
    sv(r4_char(7603), "r4i-char")
    sv(r4_char(7604), "r4i-coal")
    sv(r4_embers(7605), "r4i-embers")
    sv(r4_ash(7606), "r4i-ash")
    sv(r4_flame(7607), "r4i-flame")
    sv(r4_flame(7608, core=True), "r4i-flamecore")
    sv(r4_castiron(7609), "r4i-castiron")
    sv(r4_iron(7610), "r4i-iron")
    sv(r4_fireback(7611), "r4i-fireback")
    sv(r4_roast(7612), "r4i-roast")
    sv(r4_potmouth(7613), "r4i-potmouth")
    sv(r4_fringe(7614), "r4i-fringe")
    sv(r4_braid(7615), "r4i-braid")
    sv(r4_hem(7616), "r4i-hem")
    sv(r4_mahogany(7617, "v"), "r4i-mahog-v")
    sv(r4_mahogany(7618, "h"), "r4i-mahog-h")
    sv(r4_carved(7619), "r4i-carved")
    sv(r4_hoop(7620), "r4i-hoop")
    sv(r4_staves(7621), "r4i-staves")
    sv(r4_barrelhead(7622), "r4i-barrelhead")
    sv(r4_copper(7623), "r4i-copper")
    sv(r4_tinned(7624), "r4i-tinned")
    sv(r4_lid(7625), "r4i-lid")
    sv(r4_hide(7626), "r4i-hide")
    sv(r4_flesh(7627), "r4i-flesh")
    sv(r4_rag(7628), "r4i-rag")
    sv(r4_blood(7629), "r4i-blood")


# ================= Blocktypes =================

def plain(code, comment, shape_base, material, sel=None, coll=None, sounds=None, light=None, extra=None):
    b = {
        "code": code, "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": material, "drawtype": "json",
        "shape": {"base": shape_base}, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "selectionbox": sel or {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1},
        "drops": [], "sounds": sounds or WOOD,
    }
    b["collisionbox"] = coll
    if light:
        b["lightHsv"] = light
    if extra:
        b.update(extra)
    return comment, fixed(b)


def multi(code, comment, groups, shapes_by, material, sel, coll=None, sounds=None, light=None, inv=None, extra=None):
    """A json block with variant groups (the side last, rotated), its shape per variant from shapes_by(states...)."""
    import itertools
    names = [g[0] for g in groups]
    states = [g[1] for g in groups]
    shape_by, sel_by, coll_by = {}, {}, {}
    for combo in itertools.product(*states):
        key = "*-" + "-".join(combo)
        side = combo[-1] if names[-1] == "side" else None
        base = shapes_by(*combo)
        shape_by[key] = {"base": base, "rotateY": ROT[side]} if side else {"base": base}
        if side:
            sel_by[key] = dict(sel, rotateY=ROT[side])
            if coll:
                coll_by[key] = dict(coll, rotateY=ROT[side])
    b = {
        "code": code, "variantgroups": [{"code": n, "states": s} for n, s in zip(names, states)],
        "creativeinventory": {"general": [inv or "*"], "backrooms": [inv or "*"]}, "blockmaterial": material, "drawtype": "json",
        "shapeByType": shape_by, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "drops": [], "sounds": sounds or WOOD,
    }
    if sel_by:
        b["selectionboxByType"] = sel_by
    else:
        b["selectionbox"] = sel
    if coll is None:
        b["collisionbox"] = None
    elif coll_by:
        b["collisionboxByType"] = coll_by
    else:
        b["collisionbox"] = coll
    if light:
        b["lightHsv"] = light
    if extra:
        b.update(extra)
    return comment, fixed(b)


def cube(code, comment, textures, material, sounds, extra=None):
    b = {"code": code, "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": material, "drawtype": "cube",
         "textures": textures, "drops": [], "sounds": sounds}
    if extra:
        b.update(extra)
    return comment, fixed(b)


FULL = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}
WALLTHIN = {"x1": 0.0, "y1": 0.0, "z1": 0.88, "x2": 1, "y2": 1, "z2": 1}
TAPESTRIES = ["hunt", "castle"]
TPARTS = ["bl", "br", "tl", "tr"]
PLANKS = "game:block/wood/planks/aged1"


def blocktypes():
    out = []
    out.append(multi("l73-fire", "// Level 73: a fire in a fireplace (the wall to its back, south for -north): firedogs, burning logs; a cauldron or a spit",
                     [("kind", ["logs", "cauldron", "spit"]), ("side", SIDES)], lambda k, s: f"block/73/fire-{k}", "Stone",
                     FULL, coll=FULL, sounds=STONE, light=[4, 7, 14], inv="*-logs-north", extra={"renderpass": "OpaqueNoCull"}))
    out.append(multi("l73-mantel", "// Level 73: the carved stone over a fireplace, its mantel shelf with two candles",
                     [("side", SIDES)], lambda s: "block/73/mantel", "Stone", FULL, coll=FULL, sounds=STONE, inv="*-north"))
    out.append(multi("l73-canopy", "// Level 73: a four-poster's frame (posts, tester, valance, drapes) over two beds side by side, two blocks over them",
                     [("part", ["h0", "h1", "f0", "f1"]), ("cloth", ["red", "black"]), ("side", SIDES)],
                     lambda p, c, s: f"block/73/canopy-{p}-{c}", "Cloth", {"x1": 0, "y1": 0.66, "z1": 0, "x2": 1, "y2": 0.95, "z2": 1},
                     sounds=CLOTH, inv="*-h0-red-north", extra={"renderpass": "OpaqueNoCull"}))
    rug_tex = {}
    for pat in RUGS:
        for part in RUG_PARTS:
            rug_tex[f"*-{pat}-{part}"] = {"all": {"base": PLANKS}, "up": {"base": f"block/73/rug-{pat}-{part}"}, "down": {"base": "block/73/ceilplaster"}}
    out.append(("// Level 73: a bordered rug let into the floor (the part names the border it carries), plaster below", fixed({
        "code": "l73-rug", "variantgroups": [{"code": "pattern", "states": list(RUGS)}, {"code": "part", "states": RUG_PARTS}],
        "creativeinventory": {"general": ["*-red-c"], "backrooms": ["*-red-c"]}, "blockmaterial": "Wood", "drawtype": "cube",
        "texturesByType": rug_tex, "drops": [], "sounds": CLOTH})))
    out.append(cube("l73-floorboards", "// Level 73: a floor of the keep: aged boards on top, the plaster ceiling of the room below underneath",
                    {"all": {"base": PLANKS}, "down": {"base": "block/73/ceilplaster"}}, "Wood", WOOD))
    out.append(cube("l73-tileceil", "// Level 73: a bathroom's tiled floor, the plaster ceiling of the room below underneath",
                    {"all": {"base": "block/188/tile-bath"}, "down": {"base": "block/73/ceilplaster"}}, "Stone", STONE))
    out.append(cube("l73-flags", "// Level 73: the kitchen's and the pantry's flagstones, plaster below",
                    {"all": {"base": "block/73/flags"}, "down": {"base": "block/73/ceilplaster"}}, "Stone", STONE))
    out.append(cube("l73-pathflags", "// Level 73: the stone path to the castle: dark worn flags, stained",
                    {"all": {"base": "block/73/pathflags", "alternates": [{"base": "block/73/pathflags-2"}]}}, "Stone", STONE))
    out.append(cube("l73-trodden", "// Level 73: earth trodden to mud along the tracks the runners wore toward the castle",
                    {"all": {"base": "block/73/trodden", "alternates": [{"base": "block/73/trodden-2"}]}}, "Soil",
                    {"walk": "game:walk/sludge*", "place": "game:block/dirt*", "break": "game:block/dirt*", "hit": "game:block/dirt*"}))
    out.append(multi("l73-beam", "// Level 73: a dark oak beam under a ceiling", [("axis", ["ns", "ew"])], lambda a: f"block/73/beam-{a}", "Wood",
                     {"x1": 0, "y1": 0.62, "z1": 0, "x2": 1, "y2": 1, "z2": 1}, inv="*-ns"))
    out.append(multi("l73-stairrail", "// Level 73: the grand stair's balustrade on the south edge of a step, rising east or west",
                     [("rise", ["east", "west"])], lambda r: f"block/73/stairrail-{r}", "Wood",
                     {"x1": 0, "y1": 0, "z1": 0.88, "x2": 1, "y2": 1, "z2": 1}, coll={"x1": 0, "y1": 0, "z1": 0.9, "x2": 1, "y2": 1, "z2": 1}, inv="*-east"))
    out.append(multi("l73-rail", "// Level 73: a balustrade along the back edge of the block (round a stairwell)", [("side", SIDES)],
                     lambda s: "block/73/rail", "Wood", WALLTHIN, coll={"x1": 0, "y1": 0, "z1": 0.9, "x2": 1, "y2": 1.5, "z2": 1}, inv="*-north"))
    out.append(multi("l73-tapestry", "// Level 73: a tapestry two blocks by two (Coran and the Great Hound; the castle under the moon)",
                     [("design", TAPESTRIES), ("part", TPARTS), ("side", SIDES)], lambda d, p, s: f"block/73/tapestry-{d}-{p}", "Cloth",
                     {"x1": 0, "y1": 0, "z1": 0.78, "x2": 1, "y2": 1, "z2": 1}, sounds=CLOTH, inv="*-hunt-bl-north",
                     extra={"renderpass": "OpaqueNoCull"}))
    out.append(multi("l73-sampler", "// Level 73: a needlework sampler: \"We are safe here. We are loved here.\"",
                     [("part", ["l", "r"]), ("side", SIDES)], lambda p, s: f"block/73/sampler-{p}", "Cloth", WALLTHIN, sounds=CLOTH, inv="*-l-north"))
    out.append(multi("l73-plate", "// Level 73: a brass plate by a doorway, the room's name or number",
                     [("text", list(PLATES)), ("side", SIDES)], lambda t, s: f"block/73/plate-{t}", "Metal",
                     {"x1": 0.25, "y1": 0.375, "z1": 0.94, "x2": 0.75, "y2": 0.625, "z2": 1}, sounds=METAL, inv="*-i-north"))
    out.append(multi("l73-notice", "// Level 73: a note pinned up in a careful hand", [("text", list(NOTICES)), ("side", SIDES)],
                     lambda t, s: f"block/73/notice-{t}", "Cloth", {"x1": 0.25, "y1": 0.19, "z1": 0.95, "x2": 0.75, "y2": 0.81, "z2": 1},
                     sounds=CLOTH, inv="*-outside-north"))
    out.append(multi("l73-megplacard", "// Level 73: the M.E.G.'s plate by the castle's doors (in the mod's placard style)", [("side", SIDES)],
                     lambda s: "block/73/megplacard", "Metal", {"x1": 0, "y1": 0.25, "z1": 0.94, "x2": 1, "y2": 1, "z2": 1}, sounds=METAL, inv="*-north"))
    out.append(multi("l73-chest", "// Level 73: an iron-bound oak chest", [("side", SIDES)], lambda s: "block/73/chest", "Wood",
                     {"x1": 0.04, "y1": 0, "z1": 0.16, "x2": 0.96, "y2": 0.66, "z2": 0.84}, coll={"x1": 0.04, "y1": 0, "z1": 0.16, "x2": 0.96, "y2": 0.66, "z2": 0.84}, inv="*-north"))
    out.append(multi("l73-washstand", "// Level 73: a washstand, its basin and jug, the mirror over it", [("side", SIDES)], lambda s: "block/73/washstand",
                     "Wood", {"x1": 0.1, "y1": 0, "z1": 0.34, "x2": 0.9, "y2": 1, "z2": 1}, coll={"x1": 0.1, "y1": 0, "z1": 0.34, "x2": 0.9, "y2": 0.9, "z2": 1}, inv="*-north"))
    out.append(multi("l73-worktable", "// Level 73: the kitchen's worktable (pots and a loaf; a haunch and a cleaver)",
                     [("kind", ["pots", "meat"]), ("side", SIDES)], lambda k, s: f"block/73/worktable-{k}", "Wood", FULL,
                     coll={"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.94, "z2": 1}, inv="*-pots-north"))
    out.append(plain("l73-potrack", "// Level 73: an iron rack of copper pots hung under the kitchen's ceiling", "block/73/potrack", "Metal",
                     sel={"x1": 0.05, "y1": 0.1, "z1": 0.08, "x2": 0.95, "y2": 1, "z2": 0.88}, sounds=METAL))
    out.append(multi("l73-lectern", "// Level 73: a lectern with the castle's book open on it", [("side", SIDES)], lambda s: "block/73/lectern", "Wood",
                     {"x1": 0.12, "y1": 0, "z1": 0.18, "x2": 0.88, "y2": 0.92, "z2": 0.82}, coll={"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 0.9, "z2": 0.7}, inv="*-north"))
    out.append(multi("l73-linen", "// Level 73: a drying rack hung with linen", [("side", SIDES)], lambda s: "block/73/linen", "Cloth",
                     {"x1": 0, "y1": 0, "z1": 0.4, "x2": 1, "y2": 1, "z2": 0.6}, coll={"x1": 0, "y1": 0, "z1": 0.4, "x2": 1, "y2": 1, "z2": 0.6}, sounds=CLOTH, inv="*-north"))
    out.append(multi("l73-bonejoint", "// Level 73: a bone of the Great Hound's skeleton, joined to its neighbours (the mask: n e s w u d)",
                     [("c", [f"c{m}" for m in range(64)])], lambda c: f"block/73/bone/{c}", "Stone",
                     {"x1": 0.25, "y1": 0.25, "z1": 0.25, "x2": 0.75, "y2": 0.75, "z2": 0.75}, coll={"x1": 0.25, "y1": 0.25, "z1": 0.25, "x2": 0.75, "y2": 0.75, "z2": 0.75},
                     sounds=STONE, inv="*-c63"))
    out.append(multi("l73-deadwood", "// Level 73: a dead tree's trunk, charred black (its root, a length of trunk, its forked top)",
                     [("part", ["root", "trunk", "top"])], lambda p: f"block/73/deadwood-{p}", "Wood",
                     {"x1": 0.25, "y1": 0, "z1": 0.25, "x2": 0.75, "y2": 1, "z2": 0.75}, coll={"x1": 0.25, "y1": 0, "z1": 0.25, "x2": 0.75, "y2": 1, "z2": 0.75}, inv="*-trunk"))
    out.append(multi("l73-deadbranch", "// Level 73: a dead tree's bare branch, the trunk to its back (south for -north)",
                     [("kind", ["a", "b"]), ("side", SIDES)], lambda k, s: f"block/73/deadbranch-{k}", "Wood",
                     {"x1": 0.3, "y1": 0.1, "z1": 0, "x2": 0.7, "y2": 0.9, "z2": 1}, inv="*-a-north"))
    out.append(plain("l73-well", "// Level 73: the courtyard's well, boarded over, under its little roof", "block/73/well", "Stone",
                     sel=FULL, coll={"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.6, "z2": 1}, sounds=STONE))
    out.append(multi("l73-carcass", "// Level 73: a heap of the hordes' dead dragged in for the fire (\"Hound is the fuel\")",
                     [("kind", ["a", "b"]), ("side", SIDES)], lambda k, s: f"block/73/carcass-{k}", "Cloth",
                     {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.56, "z2": 1}, coll={"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.4, "z2": 1},
                     sounds=CLOTH, inv="*-a-north"))
    out.append(multi("l73-larder", "// Level 73: larder shelves, stocked (the wall to their back, south for -north); fixed, they give nothing",
                     [("side", SIDES)], lambda s: "block/73/larder", "Wood", {"x1": 0, "y1": 0, "z1": 0.56, "x2": 1, "y2": 1, "z2": 1},
                     coll={"x1": 0, "y1": 0, "z1": 0.56, "x2": 1, "y2": 1, "z2": 1}, inv="*-north"))
    out.append(multi("l73-sacks", "// Level 73: sacks of flour and meal (fixed, they give nothing)", [("side", SIDES)], lambda s: "block/73/sacks", "Cloth",
                     {"x1": 0.05, "y1": 0, "z1": 0.1, "x2": 0.95, "y2": 0.65, "z2": 0.95}, coll={"x1": 0.05, "y1": 0, "z1": 0.1, "x2": 0.95, "y2": 0.6, "z2": 0.95},
                     sounds=CLOTH, inv="*-north"))
    out.append(multi("l73-sheeted", "// Level 73: furniture under a dust sheet in the attic (an armchair; something tall)",
                     [("kind", ["a", "b"]), ("side", SIDES)], lambda k, s: f"block/73/sheeted-{k}", "Cloth", FULL, coll=FULL, sounds=CLOTH, inv="*-a-north"))
    out.append(plain("l73-hookmeat", "// Level 73: a carcass hung on a hook under the cellar's ceiling (the fuel)", "block/73/hookmeat", "Cloth",
                     sel={"x1": 0.22, "y1": 0, "z1": 0.3, "x2": 0.78, "y2": 1, "z2": 0.7}, sounds=CLOTH))
    out.append(("// Level 73: limewashed walls of the keep's service rooms (the kitchen, the pantry), on the room's side", fixed({
        "code": "l73-lime", "variantgroups": [{"code": "lined", "states": ["north", "east", "south", "west", "all"]}],
        "creativeinventory": {"general": ["*-all"], "backrooms": ["*-all"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "texturesByType": dict({f"*-{f}": {"all": {"base": "block/73/silverwall"}, f: {"base": "block/73/limewash"}} for f in SIDES},
                               **{"*-all": {"all": {"base": "block/73/limewash"}}}),
        "drops": [], "sounds": STONE})))
    out.append(plain("l73-barrel", "// Level 73: a barrel in the courtyard", "block/73/barrel", "Wood",
                     sel={"x1": 0.12, "y1": 0, "z1": 0.12, "x2": 0.88, "y2": 0.88, "z2": 0.88}, coll={"x1": 0.12, "y1": 0, "z1": 0.12, "x2": 0.88, "y2": 0.88, "z2": 0.88}))
    out.append(multi("l73-cart", "// Level 73: a hand cart, its shafts to the front", [("side", SIDES)], lambda s: "block/73/cart", "Wood",
                     FULL, coll={"x1": 0, "y1": 0, "z1": 0.1, "x2": 1, "y2": 0.7, "z2": 1}, inv="*-north"))
    out.append(multi("l73-boulder", "// Level 73: a black boulder on the fields", [("kind", ["a", "b"]), ("side", SIDES)],
                     lambda k, s: f"block/73/boulder-{k}", "Stone", FULL, coll=FULL, sounds=STONE, inv="*-a-north"))
    out.append(("// Level 73: the keep's walls at the ceiling, the damask under a carved cornice, on the room's side", fixed({
        "code": "l73-cornice", "variantgroups": [{"code": "lined", "states": ["north", "east", "south", "west", "all"]}],
        "creativeinventory": {"general": ["*-all"], "backrooms": ["*-all"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "texturesByType": dict({f"*-{f}": {"all": {"base": "block/73/silverwall"}, f: {"base": "block/73/cornice"}} for f in SIDES},
                               **{"*-all": {"all": {"base": "block/73/cornice"}}}),
        "drops": [], "sounds": STONE})))
    return out


# ================= Writing =================

def textures(save):
    n = 0
    def sv(img, name):
        nonlocal n
        save(img, "block/73/" + name)
        n += 1
    sv(plaster_ceiling(7501), "ceilplaster")
    sv(oak_beam(7502), "beam")
    sv(soot(7503), "soot")
    sv(firebrick(7504), "firebrick")
    sv(bark(7505), "deadbark")
    sv(log_end(7506), "logend")
    sv(flame(7507), "flame")
    sv(embers(7508), "embers")
    sv(marble(7509), "mantelstone")
    sv(carved_stone(7510), "carvedstone")
    sv(marble(7511, (226, 222, 214), (170, 166, 160)), "marble")
    sv(wax(7512), "wax")
    sv(black_velvet(7513), "velvet-black")
    for i, pat in enumerate(RUGS):
        whole = rug_whole(7520 + i, pat)
        for part in RUG_PARTS:
            sv(rug_part(whole, part), f"rug-{pat}-{part}")
    import gen_73
    sv(cornice(7530, gen_73.damask(7421)), "cornice")
    for i, kind in enumerate(TAPESTRIES):
        t = tapestry(kind, 7540 + i)
        for p in TPARTS:
            col = 0 if p[1] == "l" else 1
            row = 0 if p[0] == "t" else 1
            sv(t.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32)), f"tapestry-{kind}-{p}")
    smp = sampler()
    sv(smp.crop((0, 0, 64, 48)).resize((64, 48)), "sampler-l")
    sv(smp.crop((64, 0, 128, 48)), "sampler-r")
    for key, word in PLATES.items():
        sv(plate_tex(word), f"plate-{key}")
    for i, key in enumerate(NOTICES):
        sv(notice_tex(key, 7560 + i), f"notice-{key}")
    sv(megplacard(), "megplacard")
    sv(linen(7570), "linen")
    sv(copper(7571), "copper")
    sv(meat(7572), "meat")
    sv(leather(7573), "leather")
    sv(pages(7574), "pages")
    sv(mirror(7575), "mirror")
    sv(porcelain(7576), "porcelain")
    sv(old_bone(7577), "bone-old")
    sv(trodden(7578), "trodden")
    sv(trodden(7579), "trodden-2")
    sv(flags(7580), "flags")
    sv(hide(7583), "hide")
    sv(limewash(7585), "limewash")
    sv(dustsheet(7584), "dustsheet")
    sv(flags(7581, (92, 88, 86), stain=True), "pathflags")
    sv(flags(7582, (88, 84, 84), stain=True), "pathflags-2")
    r4_textures(sv)
    return n


def shapes(write_json, shape_dir):
    n = 0
    def w(name, obj):
        nonlocal n
        write_json(os.path.join(shape_dir, *name.split("/")) + ".json", None, obj)
        n += 1
    for k in ("logs", "cauldron", "spit"):
        w(f"fire-{k}", fire_shape(k))
    w("mantel", mantel_shape())
    for p in ("h0", "h1", "f0", "f1"):
        for c in ("red", "black"):
            w(f"canopy-{p}-{c}", canopy_shape(p, c))
    for a in ("ns", "ew"):
        w(f"beam-{a}", beam_shape(a))
    for r in ("east", "west"):
        w(f"stairrail-{r}", stairrail_shape(r))
    w("rail", rail_shape())
    for d in TAPESTRIES:
        for p in TPARTS:
            w(f"tapestry-{d}-{p}", hanging_shape(f"tapestry-{d}-{p}", part=p))
    w("sampler-l", framed_shape("sampler-l", True, False))
    w("sampler-r", framed_shape("sampler-r", False, True))
    for key in PLATES:
        w(f"plate-{key}", plate_shape(f"plate-{key}"))
    for key in NOTICES:
        w(f"notice-{key}", notice_shape(f"notice-{key}"))
    w("megplacard", placard_shape())
    w("chest", chest_shape())
    w("washstand", washstand_shape())
    for k in ("pots", "meat"):
        w(f"worktable-{k}", worktable_shape(k))
    w("potrack", potrack_shape())
    w("lectern", lectern_shape())
    w("linen", linen_shape())
    for m in range(64):
        w(f"bone/c{m}", bonejoint_shape(m))
    for p in ("root", "trunk", "top"):
        w(f"deadwood-{p}", deadwood_shape(p))
    for k in ("a", "b"):
        w(f"deadbranch-{k}", deadbranch_shape(k))
        w(f"boulder-{k}", boulder_shape(k))
        w(f"carcass-{k}", carcass_shape(k))
    w("well", well_shape())
    w("hookmeat", hookmeat_shape())
    w("larder", larder_shape())
    w("sheeted-a", sheeted_shape("a"))
    w("sheeted-b", sheeted_shape("b"))
    w("sacks", sacks_shape())
    w("barrel", barrel_shape())
    w("cart", cart_shape())
    return n


LANG = [
    ("block-l73-fire-*", "Fireplace"),
    ("block-l73-mantel-*", "Mantelpiece"),
    ("block-l73-canopy-*", "Four-Poster Canopy"),
    ("block-l73-rug-*", "Rug"),
    ("block-l73-floorboards", "Floorboards"),
    ("block-l73-tileceil", "Bathroom Tiles"),
    ("block-l73-flags", "Flagstones"),
    ("block-l73-pathflags", "Path Flagstones"),
    ("block-l73-trodden", "Trodden Earth"),
    ("block-l73-beam-*", "Oak Beam"),
    ("block-l73-stairrail-*", "Balustrade"),
    ("block-l73-rail-*", "Balustrade"),
    ("block-l73-tapestry-hunt-*", "Tapestry of the Great Hound"),
    ("block-l73-tapestry-castle-*", "Tapestry of the Silver Castle"),
    ("block-l73-sampler-*", "Needlework Sampler"),
    ("block-l73-plate-*", "Brass Plate"),
    ("block-l73-notice-*", "Pinned Note"),
    ("block-l73-megplacard-*", "M.E.G. Placard"),
    ("block-l73-chest-*", "Iron-Bound Chest"),
    ("block-l73-washstand-*", "Washstand"),
    ("block-l73-worktable-*", "Kitchen Worktable"),
    ("block-l73-potrack", "Pot Rack"),
    ("block-l73-lectern-*", "Lectern"),
    ("block-l73-linen-*", "Drying Rack"),
    ("block-l73-bonejoint-*", "Great Hound's Bone"),
    ("block-l73-deadwood-*", "Dead Tree"),
    ("block-l73-deadbranch-*", "Dead Branch"),
    ("block-l73-boulder-*", "Black Boulder"),
    ("block-l73-cornice-*", "Cornice"),
    ("block-l73-well", "Well"),
    ("block-l73-hookmeat", "Hung Carcass"),
    ("block-l73-lime-*", "Limewashed Wall"),
    ("block-l73-larder-*", "Larder Shelves"),
    ("block-l73-sheeted-*", "Dust Sheet"),
    ("block-l73-sacks-*", "Sacks of Meal"),
    ("block-l73-carcass-*", "Heap of the Dead"),
    ("block-l73-barrel", "Barrel"),
    ("block-l73-cart-*", "Hand Cart"),
]
