"""Level 73, "The Redlands": round 4's (2026-11-02) asset-quality pass, the props part; called from gen_73.py (run that, under
the asset lock). Same interface as gen_73_interior.py: textures(save) -> count, blocktypes() -> [(comment, block)],
shapes(write_json, shape_dir) -> count.

New blocks (all l73Fixed, drop nothing):
  l73-chandelier               a wrought-iron ring chandelier of eight candles; hangs in the top air cell of a room (the
                               ceiling is the block above), light [7, 4, 14]
  l73-candelabrum              a floor-standing iron candelabrum of five candles, ~1.7 blocks tall (it reaches into the
                               cell above), light [7, 4, 12]
  l73-highchair-{side}         a carved high-backed mahogany chair: the sitter faces the variant's side, its back to the
                               south for -north (as the hotel chairs); the back rises to ~1.85 blocks
  l73-bookcase-{a,b}-{side}    a mahogany bookcase against the wall at its back (south for -north), two fillings
The candle parts (wax, flame: r4p-wax, r4p-flame) are shared with gen_73.py's sconce; the pewter, silver and plate with
gen_73_castle.py's table.
"""
import math
import os
import random

from PIL import Image, ImageDraw

import matlib as M
from gen_73_castle import ROT, SIDES, WOOD, oriented, shape
from gen_73_interior import METAL, bb, chain, octo, plain, plane, rod

T = "backrooms:block/73/"
P = T + "r4p-"
S = 32
TAN = math.tan(math.radians(22.5))

# Block names for the HUD: [("block-l73-...", "Name")]
LANG = [
    ("block-l73-chandelier", "Chandelier"),
    ("block-l73-candelabrum", "Candelabrum"),
    ("block-l73-highchair-*", "High-Backed Chair"),
    ("block-l73-bookcase-*", "Bookcase"),
]


# ================= Textures =================

def wax(seed):
    """Ivory candle wax: a soft mottle, runs of drips from the top (lighter, rounded at their ends), the top warmer where
    the flame lights it through, a little dust at the foot."""
    img = M.noise_hv((228, 214, 178), amp=3, seed=seed, mottle=5, hue=2)
    rng = random.Random(seed)
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = 1 - y / (S - 1)
            r, g, b, a = px[x, y]
            px[x, y] = M.rgba((r + 10 * t, g + 6 * t, b - 4 * t))
    for _ in range(9):
        x = rng.randrange(S)
        L = rng.randint(6, 26)
        w = rng.choice((1, 2))
        for y in range(L):
            for dx in range(w):
                M.touch(img, x + dx, y, 0.07)
        for dx in range(-1, w + 1):  # the drip's rounded end
            M.touch(img, x + dx, L, 0.09 if 0 <= dx < w else 0.04)
        M.touch(img, x, L + 1, -0.06)
    for y in range(S - 4, S):
        for x in range(S):
            M.touch(img, x, y, -0.03 * (y - S + 5))
    return img


def candle_flame(seed):
    """A candle flame (cutout: alpha 0 or 255): a teardrop, the wick dark at its root, a blue heart at the base, white
    and yellow inside, orange at the rim, the tip going red."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    cx = 16.0
    for y in range(S):
        u = 1 - (y + 0.5) / S  # 0 at the root, 1 at the tip
        hw = 13.0 * math.sqrt(u / 0.32) if u < 0.32 else 13.0 * ((1 - u) / 0.68) ** 1.35
        sway = 1.2 * math.sin(u * 3.2) * u
        for x in range(S):
            d = abs(x + 0.5 - cx - sway)
            if hw < 0.6 or d > hw:
                continue
            k = d / hw
            if u < 0.16 and k < 0.45:
                c = M.mix((70, 90, 190), (150, 150, 220), u / 0.16)
            elif k < 0.42 and u < 0.62:
                c = M.mix((255, 252, 230), (255, 236, 160), u / 0.62)
            elif k < 0.75:
                c = M.mix((255, 226, 120), (255, 190, 70), u)
            else:
                c = M.mix((250, 160, 50), (220, 90, 30), u)
            j = rng.uniform(-4, 4)
            px[x, y] = M.rgba((c[0] + j, c[1] + j, c[2] + j))
    for y in range(S - 6, S):  # the wick
        px[15, y] = (34, 24, 18, 255)
        px[16, y] = (46, 32, 22, 255)
    return img


def pewter(seed):
    img = M.brushed_metal(seed=seed, base=(150, 150, 146), direction="h", streak=6, sheen=12)
    M.grime(img, 0.14, seed=seed + 1, color=(70, 70, 64), cover=0.4)
    M.scratches(img, 7, seed + 2, length=(3, 8), light=0.22)
    return img


def silver(seed):
    img = M.brushed_metal(seed=seed, base=(172, 172, 178), direction="h", streak=6, sheen=16)
    M.grime(img, 0.12, seed=seed + 1, color=(120, 104, 76), cover=0.35)  # tarnish in the hollows
    M.scratches(img, 6, seed + 2, length=(2, 6), light=0.18)
    return img


def plate_face(seed):
    """A pewter plate seen from above (mapped centred on the dish): the broad rim with a lit bead at its edge and a dark
    step down into the well, the well knife-scratched."""
    img = pewter(seed)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x + 0.5 - 16, y + 0.5 - 16)
            if r > 15.2:
                f = -0.1
            elif r > 14.0:
                f = 0.2
            elif r > 10.6:
                f = 0.06
            elif r > 9.6:
                f = -0.22
            elif r > 8.8:
                f = 0.1
            else:
                f = -0.03
            M.touch(img, x, y, f)
    M.scratches(img, 8, seed + 5, length=(2, 5), light=0.18)
    return img


SPINE_COLOURS = [(112, 28, 24), (36, 70, 44), (32, 40, 74), (150, 104, 60), (36, 32, 32), (150, 112, 44), (80, 36, 60), (94, 58, 36)]


def spines(seed):
    """Leather book spines, eight 4 px columns: oxblood, green, navy, tan, black, ochre, plum, brown. Raised bands at top
    and bottom, gilt rules, a title label, scuffed edges, a darker foot."""
    img = Image.new("RGBA", (S, S))
    rng = random.Random(seed)
    for i, c in enumerate(SPINE_COLOURS):
        tile = M.noise_hv(c, amp=5, seed=seed + i, mottle=7, hue=2)
        img.paste(tile.crop((i * 4, 0, i * 4 + 4, S)), (i * 4, 0))
    gilt, gilt_d = (206, 168, 80), (140, 104, 44)
    px = img.load()
    for i in range(8):
        x0 = i * 4
        label = rng.choice(((24, 20, 20), (120, 28, 24), None))
        for y in range(S):
            for x in range(x0, x0 + 4):
                c = px[x, y][:3]
                if y in (3, 27):
                    c = M.lift(c, 22)
                elif y in (4, 28):
                    c = M.lift(c, -26)
                elif y in (6, 25):
                    c = gilt if (x + y) % 3 else gilt_d
                elif 11 <= y <= 16 and label:
                    c = M.lift(label, rng.uniform(-4, 4))
                    if y in (13, 14) and x in (x0 + 1, x0 + 2) and rng.random() < 0.7:
                        c = gilt
                elif y in (19, 21) and x == x0 + 1 + (y // 20):
                    c = gilt_d
                if x in (x0, x0 + 3):
                    c = M.lift(c, -14 if x == x0 + 3 else 10)
                if y >= 29:
                    c = M.lift(c, -18)
                px[x, y] = M.rgba(c)
    return img


def pages(seed):
    """Page edges seen from above: cream, fine lines running from spine to fore-edge, foxed here and there."""
    img = M.noise_hv((222, 210, 176), amp=3, seed=seed, mottle=5, hue=2)
    for x in range(0, S, 2):
        for y in range(S):
            M.touch(img, x, y, -0.07)
    M.grime(img, 0.14, seed=seed + 1, color=(170, 140, 90), cover=0.4)
    return img


def cushion(seed):
    """Deep red velvet, button-tufted: a diamond lattice of buttons sunk in dimples, pleats between them, the puffs lit."""
    img = M.noise_hv((122, 16, 26), amp=4, seed=seed, mottle=6, hue=2)
    buttons = [(i * 8 + (4 if j % 2 else 0), j * 8 + 4) for j in range(-1, 6) for i in range(-1, 6)]
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = min(math.hypot(x + 0.5 - bx, y + 0.5 - by) for bx, by in buttons)
            if d < 1.1:
                px[x, y] = M.rgba((60, 8, 14))
                continue
            M.touch(img, x, y, -0.32 * max(0, 1 - d / 3.2) + 0.12 * min(1, max(0, (d - 2.0) / 2.5)))
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                M.touch(img, x, y, -0.08)
    return img


def gothic_panel(seed):
    """A carved mahogany back panel (vertical grain): a pointed arch sunk in it, a quatrefoil in its head round a gilt
    boss, a raised border."""
    img = M.wood_planks(seed=seed, base=(96, 38, 24), planks=2, direction="v", grain=3, contrast=0.9, per_plank=4, gap=(70, 28, 20),
                        flecks=0.6)
    M.bevel(img, (0, 0, 32, 32), width=2, strength=0.22)
    pts = []
    for y in range(12, 31):
        pts += [(5, y), (26, y)]
    for k in range(40):
        a = math.radians(180 - 60 * k / 39)
        pts.append((26 + 21 * math.cos(a), 12 - 21 * math.sin(a) * 0.45))
        a2 = math.radians(60 * k / 39)
        pts.append((5 + 21 * math.cos(a2), 12 - 21 * math.sin(a2) * 0.45))
    for x, y in pts:
        xi, yi = int(round(x)), int(round(y))
        M.touch(img, xi, yi, -0.32)
        M.touch(img, xi + (1 if x < 16 else -1), yi + 1, 0.2)
    d = ImageDraw.Draw(img)
    for cx, cy in ((15.5, 9), (12.5, 12), (18.5, 12), (15.5, 15)):
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], outline=(52, 20, 14, 255))
    d.ellipse([14, 11, 17, 14], fill=(176, 138, 58, 255))
    M.inset(img, (6, 13, 26, 31), width=1, strength=0.18)
    return img


def bathwater(seed):
    """Warm water seen from above: deep teal, rings of ripple, glints and wisps of steam."""
    img = M.noise_hv((70, 106, 112), amp=4, seed=seed, mottle=9, hue=3)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(3):
        cx, cy, R = rng.uniform(6, 26), rng.uniform(6, 26), rng.uniform(4, 9)
        for y in range(S):
            for x in range(S):
                r = math.hypot(x - cx, y - cy)
                if abs(r - R) < 0.7:
                    M.touch(img, x, y, 0.12)
                elif abs(r - R - 1.2) < 0.6:
                    M.touch(img, x, y, -0.08)
    for _ in range(26):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.mix(px[x, y][:3], (226, 232, 228), 0.55))
    return img


def textures(save):
    n = 0

    def sv(img, name):
        nonlocal n
        save(img, "block/73/r4p-" + name)
        n += 1
    sv(wax(7701), "wax")
    sv(candle_flame(7702), "flame")
    sv(pewter(7703), "pewter")
    sv(silver(7704), "silver")
    sv(plate_face(7705), "plate")
    sv(spines(7706), "spines")
    sv(pages(7707), "pages")
    sv(cushion(7708), "cushion")
    sv(gothic_panel(7709), "panel")
    sv(bathwater(7710), "bathwater")
    return n


# ================= Shape helpers (shared with the sconce, the table and the bath) =================

def ring8(name, cx, cz, y0, y1, R, t, tex, faces=None):
    """An octagonal ring (a hoop, a rim) of apothem R and thickness t: four bars and the same four turned 45 degrees."""
    hs = (R + t / 2) * TAN + 0.02
    out = []
    for k in range(2):
        d = 0.02 * k
        bars = [((cx - hs, cz - R - t / 2), (cx + hs, cz - R + t / 2)), ((cx - hs, cz + R - t / 2), (cx + hs, cz + R + t / 2)),
                ((cx - R - t / 2, cz - hs), (cx - R + t / 2, cz + hs)), ((cx + R - t / 2, cz - hs), (cx + R + t / 2, cz + hs))]
        for j, ((x0, z0), (x1, z1)) in enumerate(bars):
            kw = {"faces": faces} if faces else {}
            out.append(bb(f"{name}{k}{j}", (x0, y0 + d, z0), (x1, y1 - d, z1), tex, rot=("y", 45, (cx, y0, cz)) if k else None, **kw))
    return out


def flame(name, x, y, z, w=1.1, h=1.9):
    """Two crossed flame planes standing on (x, y, z), glowing (the block draws them from both sides: OpaqueNoCull)."""
    return [plane(f"{name}A", "z", z, (x - w / 2, y), (x + w / 2, y + h), "#flame"),
            plane(f"{name}B", "x", x, (z - w / 2, y), (z + w / 2, y + h), "#flame")]


def candle(name, x, y, z, h, r=0.42, pan=1.15, cup=0.55, metal="#iron", drip=1, blob=False, fw=1.1, fh=1.9):
    """A candle in a socket on a drip pan standing at height y: the pan (a rounded plus), the socket, the candle with a
    run of wax down one side (drip picks the side, 0..3), its top lit by the flame, a pool of wax on the pan (blob), the
    flame."""
    els = octo(f"{name}Pan", "y", (x, z), y, y + 0.3, pan, metal, n=2, w=pan * 0.7)
    els.append(bb(f"{name}Cup", (x - cup, y + 0.3, z - cup), (x + cup, y + 0.95, z + cup), metal))
    top = y + 0.95 + h
    els.append(bb(f"{name}Wax", (x - r, y + 0.95, z - r), (x + r, top, z + r), "#wax", glow={"up": 90}))
    dx, dz = [(1, 0), (0, 1), (-1, 0), (0, -1)][drip % 4]
    if dx:
        x0 = x + r if dx > 0 else x - r - 0.16
        els.append(bb(f"{name}Drip", (x0, top - h * 0.75, z - 0.17), (x0 + 0.16, top - 0.05, z + 0.17), "#wax"))
    else:
        z0 = z + r if dz > 0 else z - r - 0.16
        els.append(bb(f"{name}Drip", (x - 0.17, top - h * 0.75, z0), (x + 0.17, top - 0.05, z0 + 0.16), "#wax"))
    if blob:
        bx, bz = x + dx * (r + 0.35), z + dz * (r + 0.35)
        els.append(bb(f"{name}Pool", (bx - 0.35, y + 0.3, bz - 0.35), (bx + 0.35, y + 0.42, bz + 0.35), "#wax"))
    els += flame(f"{name}Flame", x, top - 0.05, z, fw, fh)
    return els


def arm_box(name, d, r0, r1, y0, y1, s, tex, tilt=None, c=(8, 8)):
    """A box along an arm pointing in direction d (0 +x, 1 +z, 2 -x, 3 -z) from the centre c: r0..r1 out, y0..y1 up, s
    its half width across. tilt (degrees) turns it about its middle so that its outer end drops."""
    cx, cz = c
    if d in (0, 2):
        sg = 1 if d == 0 else -1
        xa, xb = sorted((cx + sg * r0, cx + sg * r1))
        f, t = (xa, y0, cz - s), (xb, y1, cz + s)
        rot = ("z", -sg * tilt, ((xa + xb) / 2, (y0 + y1) / 2, cz)) if tilt else None
    else:
        sg = 1 if d == 1 else -1
        za, zb = sorted((cz + sg * r0, cz + sg * r1))
        f, t = (cx - s, y0, za), (cx + s, y1, zb)
        rot = ("x", sg * tilt, (cx, (y0 + y1) / 2, (za + zb) / 2)) if tilt else None
    return bb(name, f, t, tex, rot=rot)


# ================= 1. The chandelier =================

def chandelier_shape():
    """A wrought-iron ring chandelier hung from the ceiling (the block above): a ceiling rose, a chain, a turned stem with
    knops, four S-scrolls down to the spokes of a ring of eight candles on drip pans, a drop finial under the hub."""
    tex = {"iron": T + "r4i-iron", "gold": T + "gold", "wax": P + "wax", "flame": P + "flame"}
    els = []
    els += octo("Rose", "y", (8, 8), 15.45, 16.0, 2.3, "#iron")
    els += octo("Boss", "y", (8, 8), 14.85, 15.45, 1.0, "#gold", n=2)
    els += chain("Chain", 8, 8, 10.3, 14.85, "#iron", link=1.1, r=0.42)
    els.append(bb("Loop", (7.55, 9.6, 7.85), (8.45, 10.5, 8.15), "#iron"))
    els += octo("KnopTop", "y", (8, 8), 8.7, 9.6, 0.85, "#gold", n=2)
    els += rod("Shaft", "y", (8, 8), 4.6, 8.7, 0.42, "#iron")
    els += octo("KnopMid", "y", (8, 8), 6.5, 7.4, 1.05, "#iron", n=2)
    els += octo("Hub", "y", (8, 8), 3.3, 4.6, 1.35, "#iron")
    els += octo("Drop", "y", (8, 8), 2.1, 3.3, 0.8, "#gold", n=2)
    els.append(bb("DropTip", (7.7, 1.2, 7.7), (8.3, 2.1, 8.3), "#iron"))
    R = 6.1
    els += ring8("Ring", 8, 8, 3.7, 4.25, R, 0.55, "#iron")
    els.append(bb("SpokeX", (8 - R, 3.75, 7.75), (8 + R, 4.2, 8.25), "#iron"))
    els.append(bb("SpokeZ", (7.75, 3.76, 8 - R), (8.25, 4.21, 8 + R), "#iron"))
    for d in range(4):
        els.append(arm_box(f"ScrollTop{d}", d, 1.0, 2.7, 7.3, 7.7, 0.22, "#iron"))
        els.append(arm_box(f"ScrollCurl{d}", d, 2.3, 2.7, 6.2, 7.7, 0.22, "#iron"))
        els.append(arm_box(f"ScrollRun{d}", d, 2.2, 4.9, 5.0, 5.4, 0.22, "#iron", tilt=38))
        els.append(arm_box(f"ScrollFoot{d}", d, 4.6, 5.0, 4.2, 5.2, 0.22, "#iron"))
    rng = random.Random(73)
    for k in range(8):
        a = math.radians(45 * k)
        x, z = 8 + R * math.cos(a), 8 + R * math.sin(a)
        els += candle(f"C{k}", x, 4.25, z, rng.uniform(1.8, 2.9), pan=1.05, drip=rng.randrange(4))
    return shape(tex, els)


# ================= 2. The candelabrum =================

def candelabrum_shape():
    """A floor-standing iron candelabrum, about 1.7 blocks to the candle tips: three scrolled feet, a drum, a turned stem
    with knops, a collar, four arms curling up to their candles and one candle on top."""
    tex = {"iron": T + "r4i-iron", "gold": T + "gold", "wax": P + "wax", "flame": P + "flame"}
    els = []
    for i, deg in enumerate((90, 210, 330)):
        rot = ("y", deg, (8, 0, 8))
        els.append(bb(f"FootHip{i}", (8.6, 2.2, 7.55), (10.6, 3.4, 8.45), "#iron", rot=rot))
        els.append(bb(f"FootLeg{i}", (10.2, 0.9, 7.6), (12.4, 2.6, 8.4), "#iron", rot=rot))
        els.append(bb(f"FootCurl{i}", (12.0, 1.4, 7.65), (12.9, 3.0, 8.35), "#iron", rot=rot))
        els.append(bb(f"FootPad{i}", (11.6, 0.0, 7.3), (13.5, 0.9, 8.7), "#iron", rot=rot))
    els += octo("Drum", "y", (8, 8), 2.0, 3.8, 1.6, "#iron")
    els += octo("DrumCap", "y", (8, 8), 3.8, 4.3, 1.25, "#gold", n=2)
    els += octo("Vase", "y", (8, 8), 4.3, 6.4, 0.95, "#iron", n=2)
    els += octo("KnopLow", "y", (8, 8), 6.4, 7.3, 1.25, "#iron", n=2)
    els += rod("StemLow", "y", (8, 8), 7.3, 12.0, 0.5, "#iron")
    els += octo("KnopMid", "y", (8, 8), 12.0, 13.2, 1.0, "#gold", n=2)
    els += rod("StemHigh", "y", (8, 8), 13.2, 18.4, 0.5, "#iron")
    els += octo("Collar", "y", (8, 8), 18.4, 19.6, 1.3, "#iron")
    els += rod("StemTop", "y", (8, 8), 19.6, 22.0, 0.45, "#iron")
    rng = random.Random(7302)
    for d in range(4):
        els.append(arm_box(f"Arm{d}", d, 1.2, 5.4, 18.7, 19.3, 0.28, "#iron"))
        els.append(arm_box(f"Riser{d}", d, 4.8, 5.4, 19.3, 21.0, 0.28, "#iron"))
        els.append(arm_box(f"Curl{d}", d, 2.4, 2.9, 17.4, 18.7, 0.24, "#iron"))
        els.append(arm_box(f"CurlFoot{d}", d, 2.4, 3.6, 17.2, 17.6, 0.24, "#iron"))
        x = 8 + 5.1 * (1 if d == 0 else -1 if d == 2 else 0)
        z = 8 + 5.1 * (1 if d == 1 else -1 if d == 3 else 0)
        els += candle(f"C{d}", x, 21.0, z, rng.uniform(3.0, 3.8), pan=1.2, drip=rng.randrange(4), blob=d % 2 == 0)
    els += candle("CTop", 8, 22.0, 8, 4.0, pan=1.35, drip=1, blob=True)
    return shape(tex, els)


# ================= 7b. The high-backed chair =================

def _turned_leg(name, x, z, y0, y1, a=0.85, tex="#wood"):
    """A turned leg from y0 to y1: a foot, a vase, a gilt ring, a shaft, a square block at the top."""
    h = y1 - y0
    els = octo(f"{name}Foot", "y", (x, z), y0, y0 + 0.9, a * 1.15, tex, n=2)
    els += octo(f"{name}Vase", "y", (x, z), y0 + 0.9, y0 + h * 0.45, a * 0.95, tex, n=2)
    els += octo(f"{name}Ring", "y", (x, z), y0 + h * 0.45, y0 + h * 0.55, a * 1.1, "#gold", n=2)
    els += rod(f"{name}Shaft", "y", (x, z), y0 + h * 0.55, y1 - 1.6, a * 0.7, tex)
    els.append(bb(f"{name}Block", (x - a, y1 - 1.6, z - a), (x + a, y1, z + a), tex))
    return els


def highchair_shape():
    """A carved high-backed mahogany chair (the sitter faces north, the back to the south): turned front legs, square back
    posts running up into finials, a seat with a red velvet cushion at half a block, padded arms on turned supports,
    stretchers, a carved back panel with a pointed arch and a velvet pad, a gothic crest gabled to a finial at ~1.85."""
    tex = {"wood": T + "r4i-mahog-v", "rail": T + "r4i-mahog-h", "carved": T + "r4i-carved", "gold": T + "gold",
           "velvet": P + "cushion", "panel": P + "panel"}
    els = []
    for nm, x in (("L", 2.6), ("R", 13.4)):
        els += _turned_leg(f"Leg{nm}", x, 2.6, 0.0, 7.0)
    for nm, x in (("L", 2.6), ("R", 13.4)):
        els.append(bb(f"Post{nm}", (x - 0.95, 0.0, 12.6), (x + 0.95, 26.5, 14.5), {"*": "#wood", "up": "#rail"}))
        els += octo(f"PostCap{nm}", "y", (x, 13.55), 26.5, 27.1, 1.2, "#carved", n=2)
        els += octo(f"PostKnob{nm}", "y", (x, 13.55), 27.1, 28.4, 0.8, "#wood", n=2)
        els.append(bb(f"PostSpike{nm}", (x - 0.3, 28.4, 13.25), (x + 0.3, 29.8, 13.85), "#gold", rot=("y", 45, (x, 28.4, 13.55))))
    els += [bb("StretchF", (2.6, 2.0, 2.2), (13.4, 2.8, 3.0), "#rail"), bb("StretchB", (2.6, 2.0, 13.1), (13.4, 2.8, 13.9), "#rail"),
            bb("StretchL", (2.2, 2.6, 2.6), (3.0, 3.4, 13.4), "#rail"), bb("StretchR", (13.0, 2.6, 2.6), (13.8, 3.4, 13.4), "#rail")]
    els += [bb("SeatFrame", (1.8, 5.6, 1.8), (14.2, 7.0, 13.9), {"*": "#rail", "north": "#carved"}),
            bb("Skirt", (4.0, 4.6, 1.85), (12.0, 5.6, 2.3), "#carved"),
            bb("SkirtDrop", (7.0, 3.9, 1.9), (9.0, 4.6, 2.3), "#gold"),
            bb("Cushion", (2.4, 7.0, 2.0), (13.6, 8.4, 13.0), "#velvet"),
            bb("CushionRoll", (2.6, 7.0, 1.6), (13.4, 8.0, 2.4), "#velvet")]
    for nm, x in (("L", 1.9), ("R", 14.1)):
        els += rod(f"ArmPost{nm}", "y", (x, 3.0), 7.0, 12.8, 0.55, "#wood")
        els.append(bb(f"ArmRest{nm}", (x - 0.9, 12.8, 2.0), (x + 0.9, 13.8, 13.0), "#rail"))
        els.append(bb(f"ArmPad{nm}", (x - 0.65, 13.8, 4.0), (x + 0.65, 14.4, 12.0), "#velvet"))
        els.append(bb(f"ArmScroll{nm}", (x - 1.0, 12.2, 1.4), (x + 1.0, 14.1, 2.6), "#carved"))
    els += [bb("BackRailLow", (3.5, 8.4, 13.0), (12.5, 9.6, 14.2), "#carved"),
            bb("BackRailTop", (3.5, 23.0, 13.0), (12.5, 24.4, 14.2), {"*": "#carved", "up": "#rail"}),
            bb("BackPanel", (3.5, 9.6, 13.5), (12.5, 23.0, 14.2), "#panel", uv={"north": [0, 0, 16, 16], "south": [0, 0, 16, 16]}),
            bb("BackPad", (4.8, 10.2, 12.9), (11.2, 18.6, 13.5), "#velvet"),
            bb("BackPadTop", (5.6, 18.6, 12.95), (10.4, 19.6, 13.5), "#velvet"),
            bb("BackPadPoint", (7.3, 18.9, 13.0), (8.7, 20.3, 13.5), "#velvet", rot=("z", 45, (8, 19.6, 13.25))),
            bb("BeadL", (4.4, 9.8, 12.85), (4.8, 19.0, 13.5), "#gold"), bb("BeadR", (11.2, 9.8, 12.85), (11.6, 19.0, 13.5), "#gold")]
    # the crest: a gable over the top rail (two pieces turned about z), crockets along it, a finial at the peak
    for nm, sg in (("L", 1), ("R", -1)):
        ang = sg * 27.0
        cx = 8 - sg * 3.0
        els.append(bb(f"Gable{nm}", (cx - 3.6, 24.6, 13.1), (cx + 3.6, 25.8, 14.1), "#carved", rot=("z", ang, (cx, 25.2, 13.6))))
        for k, t in enumerate((-1.8, 1.4)):
            px_ = cx + t * math.cos(math.radians(ang))
            py = 25.2 + t * math.sin(math.radians(ang)) + 0.9
            els.append(bb(f"Crocket{nm}{k}", (px_ - 0.4, py - 0.3, 13.25), (px_ + 0.4, py + 0.5, 13.95), "#gold", rot=("z", 45, (px_, py, 13.6))))
    els.append(bb("Tympanum", (5.6, 24.4, 13.4), (10.4, 25.6, 13.8), "#panel"))
    els.append(bb("Tympanum2", (6.8, 25.6, 13.4), (9.2, 26.4, 13.8), "#panel"))
    els += octo("CrestKnob", "y", (8, 13.6), 26.6, 27.8, 0.85, "#gold", n=2)
    els.append(bb("CrestSpike", (7.6, 27.8, 13.2), (8.4, 29.6, 14.0), "#carved", rot=("y", 45, (8, 27.8, 13.6))))
    els.append(bb("CrestLeafL", (6.6, 27.3, 13.35), (7.6, 28.0, 13.85), "#gold", rot=("z", 30, (7.1, 27.6, 13.6))))
    els.append(bb("CrestLeafR", (8.4, 27.3, 13.35), (9.4, 28.0, 13.85), "#gold", rot=("z", -30, (8.9, 27.6, 13.6))))
    els.append(bb("Heart", (7.4, 23.3, 12.85), (8.6, 24.1, 13.0), "#gold", rot=("z", 45, (8, 23.7, 12.9))))
    return shape(tex, els)


# ================= 9. The bookcases =================

def _book(name, at, w, h, depth, col, flat=False, lean=None):
    """One book, its spine on the north face from atlas column `col`, the covers in the same leather, page edges on top
    (on the south face, lying flat). Upright: w thick (x), h tall (y); flat: w long (x), h thick (y). lean (degrees)
    turns it about z at its foot (top toward -x)."""
    x, y, z = at
    u0 = col * 2.0
    cover = [u0 + 0.25, 8.6, u0 + 1.75, 12.0]
    f, t = (x, y, z), (x + w, y + h, z + depth)
    if flat:
        e = bb(name, f, t, {"*": "#spines", "south": "#pages", "east": "#pages", "west": "#pages"},
               uv={"north": [u0, 0, u0 + 2, 16], "east": [0, 0, 8, 2], "west": [0, 0, 8, 2], "south": [0, 0, 8, 2], "up": cover, "down": cover})
        e["faces"]["north"]["rotation"] = 90  # the spine lies along x: its bands at the ends
        return e
    uv = {"north": [u0, 0, u0 + 2, 16], "east": cover, "west": cover, "south": cover, "down": cover, "up": [0, 0, min(16, w * 2), min(16, depth * 2)]}
    rot = ("z", lean, (x, y, z)) if lean else None
    return bb(name, f, t, {"*": "#spines", "up": "#pages"}, uv=uv, rot=rot)


def _books(rng, x0, x1, y, hmax, zf, filling, row):
    """Books on a shelf from x0 to x1 standing on y, spines to the room (north, from about zf): upright books of varied
    height and thickness, now and then one leaning, a gap, or a short stack lying flat."""
    els = []
    x = x0 + rng.uniform(0, 0.3)
    i = 0
    flat_done = False
    while x < x1 - 0.7:
        col = rng.randrange(8)
        w = rng.choice((0.7, 0.9, 1.0, 1.1, 1.3, 1.6))
        w = min(w, x1 - x)
        h = min(hmax - 0.2, rng.uniform(hmax * 0.62, hmax * 0.95))
        depth = rng.uniform(4.6, 6.4)
        nm = f"B{row}{i}"
        i += 1
        if not flat_done and rng.random() < (0.16 if filling == "a" else 0.26) and x1 - x > 4.4:
            yy = y
            for k in range(rng.randint(2, 3)):
                bt = rng.uniform(0.6, 0.9)
                els.append(_book(f"{nm}F{k}", (x + rng.uniform(0, 0.4), yy, zf + rng.uniform(0, 0.4)), rng.uniform(3.0, 3.8), bt,
                                 rng.uniform(4.6, 5.6), rng.randrange(8), flat=True))
                yy += bt
            x += 4.3
            flat_done = True
            continue
        if rng.random() < 0.08:
            x += rng.uniform(0.6, 1.4)  # a gap where a book was taken
            continue
        if rng.random() < 0.15 and x1 - x > 2.8 and i > 1:
            ang = rng.uniform(12, 22)
            pivot = x + h * math.sin(math.radians(ang)) + 0.05
            els.append(_book(nm, (pivot, y, zf + rng.uniform(0, 0.4)), w, h, depth, col, lean=ang))
            x = pivot + w + 0.15
            continue
        els.append(_book(nm, (x, y, zf + rng.uniform(0, 0.5)), w, h, depth, col))
        x += w + rng.choice((0, 0, 0.05, 0.1))
    return els


def bookcase_shape(filling):
    """A mahogany bookcase one block, against the wall at its back (south): sides with fluted pilasters, a carved plinth, a
    stepped cornice, three shelves of books; filling b has a burnt-out pewter candlestick, a has a little brass-bound casket."""
    tex = {"wood": T + "r4i-mahog-v", "rail": T + "r4i-mahog-h", "carved": T + "r4i-carved", "gold": T + "gold",
           "spines": P + "spines", "pages": P + "pages", "iron": T + "r4i-iron", "pewter": P + "pewter", "wax": P + "wax"}
    els = [
        bb("SideL", (0.0, 1.2, 4.0), (1.2, 14.6, 16.0), "#wood"),
        bb("SideR", (14.8, 1.2, 4.0), (16.0, 14.6, 16.0), "#wood"),
        bb("PilasterL", (0.0, 1.2, 3.4), (1.4, 14.6, 4.0), "#wood"),
        bb("PilasterR", (14.6, 1.2, 3.4), (16.0, 14.6, 4.0), "#wood"),
        bb("FluteL", (0.5, 2.4, 3.2), (0.9, 13.2, 3.4), "#gold"),
        bb("FluteR", (15.1, 2.4, 3.2), (15.5, 13.2, 3.4), "#gold"),
        bb("Back", (1.2, 1.2, 15.3), (14.8, 14.6, 16.0), "#rail"),
        bb("Plinth", (0.0, 0.0, 3.0), (16.0, 1.2, 16.0), {"*": "#carved", "up": "#rail"}),
        bb("Cornice", (0.0, 14.6, 3.5), (16.0, 15.2, 16.0), "#carved"),
        bb("CorniceMid", (0.0, 15.2, 3.0), (16.0, 15.6, 16.0), "#gold"),
        bb("CorniceTop", (0.0, 15.6, 2.6), (16.0, 16.0, 16.0), {"*": "#rail", "north": "#carved"}),
    ]
    tiers = [(1.2, 5.0), (5.6, 9.4), (10.0, 14.6)]
    for k, (y0, _) in enumerate(tiers[1:]):
        els.append(bb(f"Shelf{k}", (1.2, y0 - 0.6, 4.2), (14.8, y0, 15.3), "#rail"))
        els.append(bb(f"ShelfLip{k}", (1.2, y0 - 0.75, 3.9), (14.8, y0 + 0.05, 4.3), "#carved"))
    rng = random.Random(7350 if filling == "a" else 7351)
    for k, (y0, y1) in enumerate(tiers):
        x0, x1 = 1.3, 14.7
        if filling == "b" and k == 1:
            els += octo("StickFoot", "y", (12.8, 8.0), y0, y0 + 0.4, 1.0, "#pewter", n=2)
            els += rod("StickStem", "y", (12.8, 8.0), y0 + 0.4, y0 + 2.2, 0.3, "#pewter")
            els += octo("StickCup", "y", (12.8, 8.0), y0 + 2.2, y0 + 2.6, 0.6, "#pewter", n=2)
            els.append(bb("StickStub", (12.45, y0 + 2.6, 7.65), (13.15, y0 + 3.3, 8.35), "#wax"))
            x1 = 11.4
        if filling == "a" and k == 2:
            els.append(bb("Casket", (11.6, y0, 6.0), (14.6, y0 + 1.9, 10.0), {"*": "#rail", "up": "#carved"}))
            els.append(bb("CasketBand", (11.5, y0 + 0.6, 5.9), (14.7, y0 + 0.9, 10.1), "#gold"))
            els.append(bb("CasketLock", (12.8, y0 + 0.8, 5.75), (13.4, y0 + 1.5, 6.0), "#iron"))
            x1 = 11.3
        els += _books(rng, x0, x1, y0, y1 - y0, 4.6, filling, k)
    return shape(tex, els)


# ================= Writing =================

def blocktypes():
    out = []
    out.append(plain("l73-chandelier", "// Level 73: a wrought-iron ring chandelier of eight candles, hung in the top air cell of a room from the ceiling above",
                     "block/73/chandelier", "Metal", sel={"x1": 0.08, "y1": 0.06, "z1": 0.08, "x2": 0.92, "y2": 1, "z2": 0.92},
                     coll=None, sounds=METAL, light=[7, 4, 14], extra={"renderpass": "OpaqueNoCull"}))
    out.append(plain("l73-candelabrum", "// Level 73: a floor-standing iron candelabrum of five candles, about 1.7 blocks tall (it reaches into the cell above)",
                     "block/73/candelabrum", "Metal", sel={"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 1.75, "z2": 0.85},
                     coll={"x1": 0.4, "y1": 0, "z1": 0.4, "x2": 0.6, "y2": 1.5, "z2": 0.6}, sounds=METAL, light=[7, 4, 12],
                     extra={"renderpass": "OpaqueNoCull"}))
    out.append(oriented("l73-highchair", "// Level 73: a carved high-backed mahogany chair in red velvet; the sitter faces the variant's side (its back to the south for -north); the back rises into the cell above",
                        "block/73/highchair", "Wood", {"x1": 0.06, "y1": 0, "z1": 0.06, "x2": 0.94, "y2": 1.85, "z2": 0.94},
                        coll={"x1": 0.06, "y1": 0, "z1": 0.06, "x2": 0.94, "y2": 0.53, "z2": 0.94}, sounds=WOOD))
    out.append(oriented("l73-bookcase", "// Level 73: a mahogany bookcase of three shelves against the wall at its back (south for -north); two fillings",
                        None, "Wood", {"x1": 0, "y1": 0, "z1": 0.16, "x2": 1, "y2": 1, "z2": 1},
                        coll={"x1": 0, "y1": 0, "z1": 0.2, "x2": 1, "y2": 1, "z2": 1}, sounds=WOOD,
                        extra_variants=[{"code": "fill", "states": ["a", "b"]}],
                        shape_by={f"*-{f}-{s}": {"base": f"block/73/bookcase-{f}", "rotateY": ROT[s]} for f in ("a", "b") for s in SIDES},
                        inv="*-a-north"))
    return out


def shapes(write_json, shape_dir):
    n = 0

    def w(name, obj):
        nonlocal n
        write_json(os.path.join(shape_dir, name + ".json"), None, obj)
        n += 1
    w("chandelier", chandelier_shape())
    w("candelabrum", candelabrum_shape())
    w("highchair", highchair_shape())
    for f in ("a", "b"):
        w(f"bookcase-{f}", bookcase_shape(f))
    return n
