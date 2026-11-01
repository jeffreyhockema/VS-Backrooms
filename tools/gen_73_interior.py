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
    return whole.crop((col * 32, row * 32, col * 32 + 32, row * 32 + 32))


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

def fire_shape(kind):
    """A fire in its hearth, the wall to its back (south): a soot-black back and cheeks of firebrick, a stone hearth slab,
    firedogs, logs and flames; a cauldron hung on a chain over it, or a spit with a haunch on it."""
    tex = {"soot": T + "soot", "brick": T + "firebrick", "stone": T + "mantelstone", "iron": T + "sconce-iron", "bark": T + "deadbark",
           "end": T + "logend", "flame": T + "flame", "ember": T + "embers", "copper": T + "copper", "meat": T + "meat"}
    els = [
        box("Back", [0, 0, 14], [16, 16, 16], "#brick"),
        box("Hearth", [0, 0, 0], [16, 1, 14], {"*": "#stone", "up": "#soot"}),
        box("Bed", [2, 1, 4], [14, 1.6, 13], "#ember", glow=200),
        box("DogL", [2, 1, 4], [3, 5, 12], "#iron"), box("DogR", [13, 1, 4], [14, 5, 12], "#iron"),
        box("Log1", [1, 2, 6], [15, 4.5, 8.5], {"*": "#bark", "east": "#end", "west": "#end"}),
        box("Log2", [2, 2, 9], [14, 4.5, 11.5], {"*": "#bark", "east": "#end", "west": "#end"}),
        box("Log3", [3, 4.2, 7.5], [13, 6.5, 10], {"*": "#bark", "east": "#end", "west": "#end"}),
        {"name": "FlameA", "from": [1, 3, 8.5], "to": [15, 14, 8.5], "faces": {"north": face("#flame", [0, 0, 16, 16], glow=255), "south": face("#flame", [0, 0, 16, 16], glow=255)}},
        {"name": "FlameB", "from": [8, 3, 3], "to": [8, 12, 14], "faces": {"east": face("#flame", [16, 0, 0, 16], glow=255), "west": face("#flame", [16, 0, 0, 16], glow=255)}},
    ]
    if kind == "cauldron":
        els += [box("Chain", [7.6, 11, 7.6], [8.4, 16, 8.4], "#iron"),
                box("Pot", [4, 6, 4], [12, 11, 12], "#iron"),
                box("Rim", [3.5, 10.5, 3.5], [12.5, 11.5, 12.5], "#iron")]
    elif kind == "spit":
        els += [box("Spit", [0, 9, 7.6], [16, 9.8, 8.4], "#iron"),
                box("Haunch", [5, 7.5, 6], [11, 11.5, 10], "#meat"),
                box("CrankL", [0.4, 9, 7.6], [1.2, 12, 8.4], "#iron")]
    return shape(tex, els)


def mantel_shape():
    """The stone over a fireplace (the wall to its back, south): a carved lintel, a moulded mantel shelf standing out over
    the room, two candlesticks on it."""
    tex = {"stone": T + "mantelstone", "carved": T + "carvedstone", "iron": T + "sconce-iron", "wax": T + "wax", "glow": T + "sconce-glow"}
    return shape(tex, [
        box("Breast", [0, 0, 4], [16, 16, 16], {"*": "#stone", "north": "#carved"}),
        box("Lintel", [0, 0, 2.5], [16, 4, 4], "#carved"),
        box("Shelf", [-1, 8, 0], [17, 10, 4], "#stone"),
        box("Bracket", [-1, 4, 1], [17, 8, 4], "#stone"),
        box("StickL", [2, 10, 1], [3, 13, 2], "#iron"), box("CandleL", [2.1, 13, 1.1], [2.9, 16, 1.9], "#wax"),
        box("FlameL", [2.2, 16, 1.2], [2.8, 17, 1.8], "#glow", glow=255),
        box("StickR", [13, 10, 1], [14, 13, 2], "#iron"), box("CandleR", [13.1, 13, 1.1], [13.9, 16, 1.9], "#wax"),
        box("FlameR", [13.2, 16, 1.2], [13.8, 17, 1.8], "#glow", glow=255),
    ])


def canopy_shape(part, cloth):
    """One quarter of a four-poster's frame, hung over two beds side by side (2 x 2 blocks), in the block two over the bed:
    the post going down to the floor at its outer corner, the tester above, the valance on its outer edges with a gold
    fringe, drapes gathered at the foot posts, the cloth behind the headboard. Front (the foot) north, head south; part
    h0/h1/f0/f1: head or foot, x-low (0) or x-high (1)."""
    tex = {"post": T + "mahogany-end", "cloth": T + ("velvet" if cloth == "red" else "velvet-black"), "gold": T + "gold"}
    head = part[0] == "h"
    hi = part[1] == "1"
    px0 = 14.5 if hi else 0
    pz0 = 14.5 if head else 0
    els = [
        box("Post", [px0, -32, pz0], [px0 + 1.5, 14, pz0 + 1.5], "#post"),
        box("Finial", [px0 - 0.3, 14, pz0 - 0.3], [px0 + 1.8, 15.5, pz0 + 1.8], "#post"),
        box("Tester", [0, 12, 0], [16, 13, 16], "#cloth"),
    ]
    # the valance on the outer edges
    if hi:
        els.append(box("ValanceX", [15.4, 6, 0], [16, 12, 16], "#cloth"))
        els.append(box("FringeX", [15.3, 5.5, 0], [16.1, 6.3, 16], "#gold"))
    else:
        els.append(box("ValanceX", [0, 6, 0], [0.6, 12, 16], "#cloth"))
        els.append(box("FringeX", [-0.1, 5.5, 0], [0.7, 6.3, 16], "#gold"))
    if head:
        els.append(box("ValanceZ", [0, 6, 15.4], [16, 12, 16], "#cloth"))
        els.append(box("Backdrop", [0, -24, 15.2], [16, 6, 15.6], "#cloth"))
    else:
        els.append(box("ValanceZ", [0, 6, 0], [16, 12, 0.6], "#cloth"))
        els.append(box("FringeZ", [0, 5.5, -0.1], [16, 6.3, 0.7], "#gold"))
        # the drapes, gathered and tied at the foot post
        dx0 = 12 if hi else 1.5
        els.append(box("Drape", [dx0, -30, 0.2], [dx0 + 2.5, 6, 2.2], "#cloth"))
        els.append(box("Tie", [dx0 - 0.2, -14, 0], [dx0 + 2.7, -13, 2.4], "#gold"))
    return shape(tex, els)


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


def hanging_shape(texname, rod=False):
    """A cloth hanging flat against the wall (south), one cell of a larger hanging; the top cells carry the rod."""
    tex = {"cloth": T + texname, "iron": T + "sconce-iron"}
    els = [{"name": "Cloth", "from": [0, 0, 15.2], "to": [16, 16, 15.7], "faces": {"north": face("#cloth", [0, 0, 16, 16])}}]
    if rod:
        els.append(box("Rod", [0, 15, 14.2], [16, 16, 15.2], "#iron"))
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
        els += [box("Pot", [2, 15, 3], [7, 19, 8], "#copper"), box("Pan", [9, 15, 4], [14, 16, 9], "#iron"),
                box("Bowl", [9, 15, 10], [12, 17, 13], "#copper"), box("Loaf", [3, 15, 10], [7, 17, 13], "#bread"),
                box("Kettle", [3, 4, 5], [7, 8, 9], "#iron")]
    else:
        els += [box("Haunch", [3, 15, 4], [10, 18.5, 10], "#meat"), box("Cleaver", [11, 15, 5], [14, 15.5, 9], "#iron"),
                box("Board", [2, 15, 3], [11, 15.4, 11], "#end"), box("Cut", [11, 15, 10], [14, 16, 13], "#meat")]
    return shape(tex, els)


def potrack_shape():
    tex = {"iron": T + "sconce-iron", "copper": T + "copper"}
    els = [box("Bar", [1, 13, 7.5], [15, 14, 8.5], "#iron"),
           box("HangL", [1, 14, 7.6], [2, 16, 8.4], "#iron"), box("HangR", [14, 14, 7.6], [15, 16, 8.4], "#iron")]
    for i, (x, w, h) in enumerate(((3, 4, 4), (8, 3, 3), (12, 3, 5))):
        els.append(box(f"Hook{i}", [x + w / 2 - 0.3, 10.5, 7.7], [x + w / 2 + 0.3, 13, 8.3], "#iron"))
        els.append(box(f"Pot{i}", [x - 0.5, 10.5 - h, 6], [x + w - 0.5, 10.5, 10], "#copper"))
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
        return shape(tex, [box("Lower", [4, 0, 4], [12, 9, 12], "#bark"), box("Upper", [4.5, 9, 3.5], [11.5, 16, 11], "#bark")])
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
            box("A1", [6.5, 2, 11], [9.5, 5, 16], "#bark"), box("A2", [6, 4, 6], [9, 8.5, 11], "#bark"),
            box("A3", [5.5, 8, 1.5], [8, 13, 6], "#bark"), box("A4", [5.8, 13, 0], [7.5, 18, 2], "#bark"),
            box("Twig", [8, 8, 3], [10.5, 9.5, 5], "#bark"), box("Twig2", [10, 9, 2], [11.5, 12, 3.5], "#bark"),
        ])
    return shape(tex, [
        box("B1", [7, 6, 9], [10, 9, 16], "#bark"), box("B2", [7.5, 7, 3], [9.5, 9.5, 9], "#bark"),
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


def carcass_shape(kind):
    """A heap of the hordes' dead dragged in for the fire ("Hound is the fuel"): grey-black hides, a leg, a jaw, red."""
    tex = {"hide": T + "hide", "meat": T + "meat", "bone": T + "bone-old"}
    if kind == "a":
        return shape(tex, [box("BodyA", [1, 0, 2], [14, 6, 10], "#hide"), box("BodyB", [3, 0, 9], [15, 4.5, 15], "#hide"),
                           box("Wound", [6, 5.9, 4], [10, 6.3, 8], "#meat"), box("Leg", [12, 2, 0], [14, 4, 4], "#hide"),
                           box("Jaw", [0, 1, 11], [4, 3.5, 14], "#bone"), box("Top", [4, 6, 4], [11, 9, 9], "#hide")])
    return shape(tex, [box("Body", [2, 0, 3], [13, 5, 13], "#hide"), box("Neck", [12, 0, 6], [16, 3.5, 10], "#hide"),
                       box("Wound", [5, 4.9, 6], [9, 5.3, 10], "#meat"), box("Rib", [3, 5, 4], [4, 8, 12], "#bone"),
                       box("Leg", [0, 1, 1], [5, 3, 3], "#hide")])


def barrel_shape():
    tex = {"staves": T + "staves", "iron": T + "sconce-iron", "end": T + "mahogany-end"}
    return shape(tex, [box("Body", [2, 0, 2], [14, 14, 14], {"*": "#staves", "up": "#end", "down": "#end"}),
                       box("Band1", [1.6, 2, 1.6], [14.4, 3, 14.4], "#iron", faces={"north": None, "south": None, "east": None, "west": None}),
                       box("Band2", [1.6, 11, 1.6], [14.4, 12, 14.4], "#iron", faces={"north": None, "south": None, "east": None, "west": None})])


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
                     [("side", SIDES)], lambda s: "block/73/mantel", "Stone", FULL, coll=FULL, sounds=STONE, light=[6, 5, 6], inv="*-north"))
    out.append(multi("l73-canopy", "// Level 73: a four-poster's frame (posts, tester, valance, drapes) over two beds side by side, two blocks over them",
                     [("part", ["h0", "h1", "f0", "f1"]), ("cloth", ["red", "black"]), ("side", SIDES)],
                     lambda p, c, s: f"block/73/canopy-{p}-{c}", "Cloth", {"x1": 0, "y1": 0.75, "z1": 0, "x2": 1, "y2": 0.82, "z2": 1},
                     sounds=CLOTH, inv="*-h0-red-north"))
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
                     WALLTHIN, sounds=CLOTH, inv="*-hunt-bl-north", extra={"renderpass": "OpaqueNoCull"}))
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
                     sel={"x1": 0, "y1": 0.4, "z1": 0.3, "x2": 1, "y2": 1, "z2": 0.7}, sounds=METAL))
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
    sv(flags(7581, (92, 88, 86), stain=True), "pathflags")
    sv(flags(7582, (88, 84, 84), stain=True), "pathflags-2")
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
            w(f"tapestry-{d}-{p}", hanging_shape(f"tapestry-{d}-{p}", rod=p[0] == "t"))
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
    w("larder", larder_shape())
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
    ("block-l73-larder-*", "Larder Shelves"),
    ("block-l73-sacks-*", "Sacks of Meal"),
    ("block-l73-carcass-*", "Heap of the Dead"),
    ("block-l73-barrel", "Barrel"),
    ("block-l73-cart-*", "Hand Cart"),
]
