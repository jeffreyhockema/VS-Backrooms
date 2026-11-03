"""Level 23, round 4 (2026-11-02), second batch, called from tools/gen_23.py: glowcaps as clusters, the sentries' faces
sculpted, the Parthenon's columns, a statue of an Architect, lily pads on the Heart of Water. Shares tools/gen_23_r4.py's
model helpers (E, every, sided, CORE); models face NORTH, "side" last.
"""
import math
import random

from PIL import Image

import matlib as M
import gen_23 as G
from gen_23_r4 import E, every, sided, shape, load, opaque, CORE, WOOD_SOUNDS, STONE_SOUNDS

S = G.S


# ---------------- Glowcaps ----------------

def glowcap_cluster(colour):
    """Glowcaps as a little cluster: four mushrooms of different sizes, each a stem (a little bent), a domed cap of two
    layers, gills under it that glow brightest, and specks of glowing spores on the ground round them."""
    rng = random.Random(len(colour) * 31)
    els = []
    gills = {"down": "#gills", "north": "#gills", "south": "#gills", "east": "#gills", "west": "#gills"}
    for k, (x, z, h, r) in enumerate([(5, 6, 6.5, 2.6), (10.5, 9.5, 4.5, 2.0), (7.5, 11.5, 3.0, 1.4), (11.5, 4.5, 2.4, 1.1)]):
        lean = rng.uniform(-9, 9)
        sw = max(0.6, r * 0.32)
        els.append(E(f"Stem{k}", (x - sw, 0, z - sw), (x + sw, h, z + sw), every("#stem", ("down",)),
                     {"rotationOrigin": [x, 0, z], "rotationZ": lean}))
        cx = x - math.sin(math.radians(lean)) * h
        els += [E(f"Gills{k}", (cx - r, h - 0.4, z - r), (cx + r, h, z + r), gills, glow=230),
                E(f"Cap{k}", (cx - r - 0.2, h, z - r - 0.2), (cx + r + 0.2, h + r * 0.45, z + r + 0.2), every("#cap", ("down",)), glow=150),
                E(f"Dome{k}", (cx - r * 0.62, h + r * 0.45, z - r * 0.62), (cx + r * 0.62, h + r * 0.8, z + r * 0.62),
                  every("#cap", ("down",)), glow=150)]
    for k in range(6):
        x, z = rng.uniform(2, 14), rng.uniform(2, 14)
        els.append(E(f"Spore{k}", (x, 0, z), (x + 0.5, 0.25, z + 0.5), {"up": "#gills", "north": "#gills", "east": "#gills"}, glow=255))
    return els


def gills_glow(colour, seed):
    """A glowcap's gills: thin bright lines of its colour, radiating; its brightest part."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            a = math.atan2(y + 0.5 - S / 2, x + 0.5 - S / 2)
            line = math.cos(a * 14) > 0.3
            c = M.mix(colour, (255, 255, 236), 0.45 if line else 0.05)
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-6, 6) - (0 if line else 30)))
    return img


# ---------------- A buried sentry's face ----------------

def sentryface_shape():
    """A buried sentry's face pushed out of the bark (facing north; the trunk behind): the bark's core with its fissures
    either side, folds of bark curling round the face, then the face itself in relief: brow, sunken shut eyes, cheekbones,
    a nose, the mouth open in its scream, a chin; a little larger than life so it reads from a few steps off."""
    sk, bk, dp, mo = "#skin", "#bark", "#deep", "#mouth"
    side = {"north": bk, "east": dp, "west": dp, "up": dp, "down": dp}
    face = {"north": sk, "east": sk, "west": sk, "up": sk, "down": sk}
    els = [E("Core", (0, 0, CORE), (16, 16, 16), {"north": dp, "east": bk, "west": bk, "south": bk, "up": bk, "down": bk})]
    for k, (x1, x2, d) in enumerate([(0, 2.2, 3.2), (13.8, 16, 3.0)]):
        els.append(E(f"Ridge{k}", (x1, 0, CORE - d), (x2, 16, CORE), side))
    els += [E("FoldL", (2.2, 1, CORE - 2.6), (4.2, 15, CORE), side), E("FoldR", (11.8, 1.5, CORE - 2.6), (13.8, 15.5, CORE), side),
            E("FoldTop", (3.6, 13.6, CORE - 2.2), (12.4, 16, CORE), side), E("FoldBot", (3.2, 0, CORE - 2.0), (12.8, 1.6, CORE), side),
            E("FoldLip", (4, 14.4, CORE - 3.2), (12, 15.2, CORE - 2.0), side)]
    z = CORE - 1.2
    els += [E("Mask", (4.4, 1.2, z), (11.6, 13.4, CORE), face),
            E("Brow", (4.6, 9.4, z - 1.8), (11.4, 10.8, z), face),
            E("BrowRidge", (5.0, 10.8, z - 1.2), (11.0, 11.8, z), face),
            E("Forehead", (5.2, 11.8, z - 0.7), (10.8, 13.2, z), face),
            E("SocketL", (5.1, 7.6, z - 0.05), (7.3, 9.4, z), {"north": dp}),
            E("SocketR", (8.7, 7.6, z - 0.05), (10.9, 9.4, z), {"north": dp}),
            E("LidL", (5.4, 8.2, z - 0.7), (7.0, 8.9, z), face), E("LidR", (9.0, 8.2, z - 0.7), (10.6, 8.9, z), face),
            E("CheekL", (4.5, 5.4, z - 1.3), (6.7, 7.6, z), face), E("CheekR", (9.3, 5.4, z - 1.3), (11.5, 7.6, z), face),
            E("Nose", (7.2, 6.0, z - 2.6), (8.8, 9.4, z), face), E("NoseTip", (6.9, 5.6, z - 3.0), (9.1, 6.8, z - 0.8), face),
            E("LipTop", (5.9, 4.8, z - 1.5), (10.1, 5.6, z), face),
            E("Mouth", (6.2, 1.6, z - 0.05), (9.8, 4.8, z), {"north": mo}),
            E("LipBottom", (6.0, 1.0, z - 1.3), (10.0, 1.8, z), face),
            E("JawL", (4.6, 1.0, z - 1.0), (6.2, 5.4, z), face), E("JawR", (9.8, 1.0, z - 1.0), (11.4, 5.4, z), face),
            E("Chin", (6.6, 0.2, z - 1.5), (9.4, 1.2, z), face)]
    return els


def skin(seed):
    """The sentry's face: the grey bark's stone, finer and paler, worn smooth on its high points, crazed with fine cracks."""
    img = M.noise_hv((170, 160, 140), 3, seed, mottle=5, hue=1)
    px = img.load()
    rng = random.Random(seed + 1)
    for y in range(S):
        for x in range(S):
            if rng.random() < 0.05:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], -20))
    for k in range(4):
        x = rng.randrange(S)
        for y in range(rng.randrange(S // 2), S):
            x = (x + rng.choice((-1, 0, 0, 1))) % S
            px[x, y] = M.rgba(M.lift(px[x, y][:3], -24))
    G.flecks(img, seed + 2, 8, (200, 204, 196), 0.4)
    return img


def mouth(seed):
    """The open mouth: dark going black toward the back of the throat (top of the texture lit a little: the upper lip's shadow)."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r = math.hypot((x + 0.5 - S / 2) / (S / 2), (y + 0.5 - S / 2) / (S / 2))
            v = int(14 + 26 * min(1, r))
            px[x, y] = (v, v - 3, v - 5, 255)
    return img


# ---------------- The ruins: columns and a statue ----------------

def octagon(name, y0, y1, w, tex):
    """An octagonal section w across, centred on (8, 8) in plan, from y0 to y1: two crossed boxes and one turned 45."""
    q = w * 0.4142 / 2
    h = w / 2
    f = every(tex)
    return [E(f"{name}A", (8 - h, y0, 8 - q), (8 + h, y1, 8 + q), f), E(f"{name}B", (8 - q, y0, 8 - h), (8 + q, y1, 8 + h), f),
            E(f"{name}C", (8 - q * 1.7, y0, 8 - q * 1.7), (8 + q * 1.7, y1, 8 + q * 1.7), f, {"rotationOrigin": [8, y0, 8], "rotationY": 45})]


def column_shape(part):
    s = "#stone"
    if part == "base":
        return ([E("Plinth", (0.5, 0, 0.5), (15.5, 2.6, 15.5), every(s)), E("PlinthTop", (1.2, 2.6, 1.2), (14.8, 3.2, 14.8), every(s))]
                + octagon("Torus", 3.2, 5.2, 13.4, s) + octagon("Scotia", 5.2, 6.0, 11.6, s) + octagon("Shaft", 6.0, 16, 10.6, "#flute"))
    if part == "shaft":
        return octagon("Shaft", 0, 16, 10.6, "#flute")
    if part == "capital":
        return (octagon("Neck", 0, 6.0, 10.4, "#flute") + octagon("Ring", 6.0, 7.0, 11.2, s)
                + octagon("Echinus", 7.0, 9.0, 13.0, s) + octagon("EchinusTop", 9.0, 10.6, 14.8, s)
                + [E("Abacus", (0.4, 10.6, 0.4), (15.6, 16, 15.6), every(s))])
    return (octagon("Shaft", 0, 9, 10.6, "#flute") + [E("Jag1", (4, 9, 5), (9, 12.5, 11), every(s)), E("Jag2", (8, 9, 4), (12, 10.8, 10), every(s)),
                                                       E("Chip", (6, 9, 9), (11, 11.4, 12.5), every(s))])


def flute(mossy=False):
    """Limestone with vertical flutes: shallow concave channels, each lit on one side and shadowed on the other."""
    img = load("ruinmoss" if mossy else "ruinstone")
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x % 6) / 6
            d = -16 * math.sin(math.pi * t) + (10 if x % 6 == 0 else 0)
            px[x, y] = M.rgba(M.lift(px[x, y][:3], d))
    return img


def statue_shape(part):
    """A robed Architect on a plinth, three blocks (plinth, lower, upper), facing north: the robe falling in folds to bare
    feet; a hooded head worn faceless but for two green stones for eyes (the plaque's "our purple eyes have turned green");
    a sapling held to the chest; one arm broken off at the elbow."""
    s, r = "#stone", "#robe"
    if part == "plinth":
        die = every(s)
        die["north"] = "#inscr"
        return [E("Base", (0, 0, 0), (16, 3, 16), every(s)), E("Die", (1.5, 3, 1.5), (14.5, 12.5, 14.5), die),
                E("Cornice", (0.6, 12.5, 0.6), (15.4, 14.2, 15.4), every(s)), E("Top", (1.2, 14.2, 1.2), (14.8, 16, 14.8), every(s))]
    if part == "lower":
        els = [E("Robe", (3.6, 1.2, 4.6), (12.4, 16, 12.0), every(r)), E("Hem", (3.0, 0, 4.0), (13.0, 1.6, 12.6), every(r)),
               E("FootL", (4.6, 0, 2.6), (7.2, 1.2, 4.6), every(s)), E("FootR", (8.8, 0, 2.8), (11.4, 1.1, 4.6), every(s))]
        for k, x in enumerate((4.2, 6.6, 9.0, 11.2)):
            els.append(E(f"Fold{k}", (x, 1.2, 4.0), (x + 1.0, 16, 4.6), every(r)))
        return els
    return [E("Torso", (3.8, 0, 5.0), (12.2, 9.6, 11.6), every(r)), E("Shoulders", (2.6, 7.0, 5.4), (13.4, 10.4, 11.2), every(r)),
            E("Neck", (6.6, 10.4, 7.0), (9.4, 11.4, 9.6), every(s)),
            E("Head", (5.6, 11.4, 6.0), (10.4, 16.0, 10.6), every(s)), E("Hood", (5.0, 11.8, 6.4), (11.0, 16.8, 11.4), every(r)),
            E("HoodPeak", (5.8, 16.0, 6.4), (10.2, 17.4, 10.4), every(r)),
            E("EyeL", (6.6, 14.0, 5.8), (7.6, 14.7, 6.0), {"north": "#eye"}, glow=60),
            E("EyeR", (8.4, 14.0, 5.8), (9.4, 14.7, 6.0), {"north": "#eye"}, glow=60),
            E("ArmL", (9.6, 3.6, 3.6), (12.4, 8.4, 6.4), every(r)), E("HandL", (7.4, 4.0, 3.2), (10.2, 6.4, 5.0), every(s)),
            E("Sapling", (7.9, 4.0, 3.6), (8.5, 12.6, 4.2), every("#twig")),
            E("Leaf1", (8.4, 9.6, 3.4), (10.6, 10.0, 4.6), every("#leaf"), {"rotationOrigin": [8.4, 9.6, 4], "rotationZ": 20}),
            E("Leaf2", (5.8, 11.0, 3.4), (8.0, 11.4, 4.6), every("#leaf"), {"rotationOrigin": [8.0, 11.0, 4], "rotationZ": -24}),
            E("Leaf3", (7.6, 12.4, 3.4), (9.2, 12.8, 4.4), every("#leaf")),
            E("ArmR", (3.2, 3.8, 5.2), (5.6, 9.6, 8.2), every(r)), E("Stump", (3.4, 3.0, 4.4), (5.4, 4.2, 7.4), every(s))]


def robe():
    img = load("ruinstone")
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], 6 * math.sin(x * 0.9) - 4))
    G.lichened(img, 2490, (96, 118, 70), n=1)
    return img


def inscription():
    img = load("ruinstone")
    G.carve(img, ["HORTV", "LANO", "MAGNO"], 6)
    return img


# ---------------- Lily pads ----------------

def lilypad_shape():
    """Lily pads on the Heart of Water's shallows (the block over the water): four pads, each a disc of two crossed boxes
    turned a little, one white flower."""
    els = []
    for k, (x, z, r, a) in enumerate([(5, 5, 3.4, 20), (11, 6.5, 2.6, -35), (6.5, 11.5, 2.9, 70), (12, 12, 1.8, 0)]):
        q = r * 0.62
        rot = {"rotationOrigin": [x, 0, z], "rotationY": a}
        els += [E(f"PadA{k}", (x - r, 0.05, z - q), (x + r, 0.3, z + q), every("#pad"), rot),
                E(f"PadB{k}", (x - q, 0.05, z - r), (x + q, 0.3, z + r - 1.2), every("#pad"), rot)]
    els += [E("Petals", (4, 0.3, 4), (6.2, 1.2, 6.2), every("#flower"), {"rotationOrigin": [5, 0.3, 5], "rotationY": 45}),
            E("Petals2", (4.3, 0.3, 4.3), (5.9, 1.6, 5.9), every("#flower")), E("Heart", (4.8, 1.2, 4.8), (5.4, 1.8, 5.4), every("#heart"))]
    return els


def lilypad_tex(seed):
    img = M.noise_hv((62, 104, 46), 4, seed, mottle=6)
    px = img.load()
    for y in range(S):
        for x in range(S):
            a = math.atan2(y + 0.5 - S / 2, x + 0.5 - S / 2)
            if math.cos(a * 9) > 0.92:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], 18))
    return img


# ---------------- Bracket fungi ----------------

def bracket_shape():
    """Shelves of stone bracket fungus stepping up a trunk (the trunk on the south side, facing north): each shelf a
    half-disc in plan built of three slabs narrowing outward, its upper side banded, a pale growing rim, gills under."""
    els = []
    top = {"north": "#rim", "east": "#rim", "west": "#rim", "up": "#cap"}
    for k, (cx, y, r, t) in enumerate([(6.5, 2.5, 6.0, 1.8), (10.5, 8.0, 4.4, 1.5), (5.5, 12.0, 3.4, 1.2)]):
        for n, f in enumerate((1.0, 0.82, 0.55)):
            half = r * math.sqrt(1 - (n / 3) ** 2) if n else r
            depth = r * f
            yy = y + n * t * 0.35
            els.append(E(f"Shelf{k}_{n}", (cx - half, yy, 16 - depth), (cx + half, yy + t - n * 0.3, 16), top))
        els.append(E(f"Gills{k}", (cx - r + 0.4, y - 0.1, 16 - r * 0.95), (cx + r - 0.4, y, 16), {"down": "#gills"}))
    return els


# ---------------- Root knuckles ----------------

def rootknuckle_shape():
    """The top of a root crawling out over the ground: its upper edges rounded off in two steps, so a run of them reads
    as a knobbly root and not as a row of cubes."""
    r, t = "#root", "#top"
    return [E("Body", (0, 0, 0), (16, 11.5, 16), {"north": r, "east": r, "south": r, "west": r, "up": t, "down": r}),
            E("Round1", (1.0, 11.5, 1.0), (15.0, 14.2, 15.0), {"north": r, "east": r, "south": r, "west": r, "up": t}),
            E("Round2", (3.2, 14.2, 2.6), (12.8, 15.6, 13.4), {"north": r, "east": r, "south": r, "west": r, "up": t})]


# ---------------- The M.E.G.'s boards ----------------

def signboard_shape():
    """A painted board on a post's top (the post its own block below), front north: the board, battens along the top and
    bottom of the painted face (a hair proud), nail heads at the corners, the post's top showing behind it with a cap."""
    w = "#wood"
    fr = {"north": w, "east": w, "west": w, "up": w, "down": w}
    els = [E("Board", (0, 2, 7), (16, 15, 9), {"east": w, "south": w, "west": w, "up": w, "down": w}),
           {"name": "Face", "from": [0, 2, 6.98], "to": [16, 15, 7], "faces": {"north": {"texture": "#face", "uv": [0, 1, 16, 15]}}},
           E("FrameTop", (0, 14.3, 6.4), (16, 15.3, 7), fr), E("FrameBottom", (0, 1.7, 6.4), (16, 2.6, 7), fr),
           # (no battens up the sides: a sign of two or three boards reads across their joins)
           E("Back", (6.5, 0, 9), (9.5, 15.6, 10.4), {"east": w, "south": w, "west": w, "up": w}),
           E("Cap", (6.1, 15.6, 8.6), (9.9, 16.4, 10.8), every(w))]
    for k, (x, y) in enumerate(((1.2, 13.2), (14.2, 13.2), (1.2, 2.8), (14.2, 2.8))):
        els.append(E(f"Nail{k}", (x, y, 6.2), (x + 0.6, y + 0.6, 6.4), {"north": "#nail", "east": "#nail", "west": "#nail", "up": "#nail"}))
    return els


def signpost_shape():
    w = "#wood"
    return [E("Post", (6.5, 0, 6.5), (9.5, 16, 9.5), every(w)), E("Foot", (6.0, 0, 6.0), (10.0, 1.4, 10.0), every("#moss"))]


# ---------------- Stone fern ----------------

def stone_fern_shape():
    """A fern gone to stone: six fronds arching out from a crown, each a rachis with pinnae across it shortening toward
    its tip (each piece turned with its frond: lifted about z, then swung about y)."""
    els = [E("Crown", (6.8, 0, 6.8), (9.2, 1.4, 9.2), every("#bark"))]
    for k in range(6):
        rot = {"rotationOrigin": [8, 0.6, 8], "rotationZ": 30 + (k % 2) * 14, "rotationY": k * 60 + (k % 3) * 9}
        els.append(E(f"Rachis{k}", (8, 0.4, 7.7), (15.5, 0.9, 8.3), every("#bark"), rot))
        for n, d in enumerate((1.6, 3.2, 4.8, 6.2)):
            half = 2.2 - n * 0.45
            els.append(E(f"Pinna{k}_{n}", (8 + d, 0.5, 8 - half), (8 + d + 0.9, 0.8, 8 + half), every("#bark"), rot))
    return els


# ---------------- A carved lintel ----------------

def frieze_shape():
    """A carved lintel over a door (front north): the stone set back two px, a cornice over it, a row of dentils under
    it, a garland of carved leaves swagged across, a rosette in its middle; fits side by side into a lintel."""
    s = "#stone"
    els = [E("Core", (0, 0, 2), (16, 16, 16), every(s)),
           E("Cornice", (0, 13.4, 0), (16, 15.0, 2), every(s)), E("CorniceTop", (0, 15.0, 0.8), (16, 16, 2), every(s)),
           E("Fascia", (0, 1.6, 1.2), (16, 3.0, 2), every(s))]
    for k in range(8):
        els.append(E(f"Dentil{k}", (k * 2 + 0.3, 3.0, 1.0), (k * 2 + 1.3, 4.2, 2), every(s)))
    # The swag: leaves stepping down to the middle and up again
    for k in range(8):
        x = 1 + k * 1.8
        y = 9.6 - 2.6 * math.sin(math.pi * (k + 0.5) / 8)
        els.append(E(f"Leaf{k}", (x, y, 0.8), (x + 2.0, y + 1.6, 2), every("#moss" if k % 3 == 0 else s),
                     {"rotationOrigin": [x + 1, y + 0.8, 1.4], "rotationZ": 25 if k < 4 else -25}))
    els += [E("Rosette", (6.6, 8.4, 0.4), (9.4, 11.2, 2), every(s)), E("RosetteEye", (7.4, 9.2, 0.0), (8.6, 10.4, 0.4), every(s))]
    return els


# ---------------- A bird's nest ----------------

def nest_shape():
    """A nest of twigs on a limb (the block over the limb, the trunk south): a ring of twigs crossing at angles round a
    bowl, three pale eggs. The lore's Curabitur Birds live in the Garden; nobody has seen one up close."""
    els = [E("Bowl", (5.2, 0, 6.2), (10.8, 1.2, 11.8), every("#twig"))]
    for k in range(10):
        a = k * 36
        els.append(E(f"Twig{k}", (3.2, 0.6 + (k % 3) * 0.5, 8.6), (12.8, 1.3 + (k % 3) * 0.5, 9.4), every("#twig"),
                     {"rotationOrigin": [8, 1, 9], "rotationY": a, "rotationZ": 6 if k % 2 else -6}))
    for k, (x, z) in enumerate(((6.8, 8.2), (8.6, 9.6), (7.0, 10.0))):
        els.append(E(f"Egg{k}", (x, 1.0, z), (x + 1.3, 2.4, z + 1.0), every("#egg")))
    return els


# ---------------- Stone sapling and shrub ----------------

def stone_sapling_shape():
    """A young tree gone to stone: a trunk narrowing in three lengths with a little lean, a flare at its foot, five
    branches spiralling up it (lifted about z, swung about y), each with a side twig, the leader snapped off at the top."""
    rng = random.Random(12)
    b = "#bark"
    els = [E("Foot", (6.6, 0, 6.6), (9.4, 1.2, 9.4), every(b)),
           E("Trunk1", (7.2, 0, 7.2), (8.8, 6, 8.8), every(b), {"rotationOrigin": [8, 0, 8], "rotationZ": 3}),
           E("Trunk2", (7.4, 5.6, 7.4), (8.6, 11, 8.6), every(b), {"rotationOrigin": [8, 0, 8], "rotationZ": 4}),
           E("Trunk3", (7.6, 10.6, 7.6), (8.4, 15.4, 8.4), every(b), {"rotationOrigin": [8, 0, 8], "rotationZ": 5}),
           E("Snap", (7.5, 15.2, 7.7), (8.1, 16.4, 8.3), every(b), {"rotationOrigin": [8, 0, 8], "rotationZ": 9})]
    for k in range(5):
        y = 5 + k * 2.1
        yaw = k * 137 + rng.uniform(-15, 15)
        length = 6.5 - k * 0.8
        rot = {"rotationOrigin": [8, y, 8], "rotationZ": rng.uniform(18, 34), "rotationY": yaw}
        els.append(E(f"Branch{k}", (8, y, 7.65), (8 + length, y + 0.7, 8.35), every(b), rot))
        rot2 = {"rotationOrigin": [8, y, 8], "rotationZ": rng.uniform(40, 55), "rotationY": yaw + 35}
        els.append(E(f"Twig{k}", (8 + length * 0.5, y, 7.75), (8 + length * 0.5 + 2.6, y + 0.5, 8.25), every(b), rot2))
    return els


def stone_shrub_shape():
    """A shrub gone to stone: seven stems fanning from a knot at the ground, each with two side twigs."""
    rng = random.Random(11)
    b = "#bark"
    els = [E("Knot", (5.6, 0, 5.6), (10.4, 1.6, 10.4), every(b))]
    for k in range(7):
        yaw = k * 51 + rng.uniform(-10, 10)
        lift = rng.uniform(52, 72)
        length = rng.uniform(7, 11)
        rot = {"rotationOrigin": [8, 0.8, 8], "rotationZ": lift, "rotationY": yaw}
        els.append(E(f"Stem{k}", (8, 0.8, 7.6), (8 + length, 1.6, 8.4), every(b), rot))
        for n, d in enumerate((0.45, 0.75)):
            r2 = {"rotationOrigin": [8, 0.8, 8], "rotationZ": lift - 22 + n * 40, "rotationY": yaw + (25 if n else -25)}
            els.append(E(f"Side{k}_{n}", (8 + length * d, 0.8, 7.7), (8 + length * d + 3, 1.4, 8.3), every(b), r2))
    return els


# ---------------- Pottery ----------------

def amphora_shape():
    """The Architects' amphora: a foot, a body swelling and narrowing in octagonal bands, a shoulder, a neck and a lip,
    two handles from the neck down to the shoulder; chipped at the lip."""
    c = "#clay"
    els = (octagon("Foot", 0, 1.0, 3.6, c) + octagon("Lower", 1.0, 3.0, 5.4, c) + octagon("Belly", 3.0, 7.0, 7.4, c)
           + octagon("Upper", 7.0, 8.6, 6.4, c) + octagon("Shoulder", 8.6, 9.6, 4.6, c) + octagon("Neck", 9.6, 12.4, 2.8, c)
           + octagon("Lip", 12.4, 13.2, 3.8, c))
    for k, sx in enumerate((-1, 1)):
        x0 = 8 + sx * 1.4
        x1 = 8 + sx * 3.4
        els += [E(f"HandleTop{k}", (min(x0, x1), 11.2, 7.6), (max(x0, x1), 11.9, 8.4), every(c)),
                E(f"HandleSide{k}", (min(x1, x1 + sx * 0.7), 8.8, 7.6), (max(x1, x1 + sx * 0.7), 11.9, 8.4), every(c))]
    return els


# ---------------- Light shafts ----------------

def sunbeam_shape():
    """A slice of a shaft of light falling through a hole in the lid: three thin upright planes crossed (one each way
    and one turned), soft at their edges, glowing; the shaft is a stack of them."""
    f = {"north": "#beam", "south": "#beam"}
    return [E("PlaneA", (0, 0, 7.9), (16, 16, 8.1), f, glow=90),
            E("PlaneB", (7.9, 0, 0), (8.1, 16, 16), {"east": "#beam", "west": "#beam"}, glow=90),
            E("PlaneC", (0, 0, 7.9), (16, 16, 8.1), f, {"rotationOrigin": [8, 0, 8], "rotationY": 45}, glow=90)]


def sunbeam_tex():
    """Pale gold light, see-through: brightest down the middle of a plane, fading to nothing at its sides (the
    translucent pass, on purpose), a few motes of dust."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(2470)
    for y in range(S):
        for x in range(S):
            t = 1 - abs(x + 0.5 - S / 2) / (S / 2)
            a = int(46 * t ** 1.6)
            px[x, y] = (255, 240, 196, a)
    for _ in range(10):
        x, y = rng.randrange(6, S - 6), rng.randrange(S)
        px[x, y] = (255, 250, 230, 120)
    return img


# ---------------- Blocktypes ----------------

FACE_TEX = {"bark": "backrooms:block/23/bark-grey", "deep": "backrooms:block/23/barkdeep-grey", "skin": "backrooms:block/23/sentry-skin",
            "mouth": "backrooms:block/23/sentry-mouth"}
STATUE_TEX = {"stone": "backrooms:block/23/ruinstone", "robe": "backrooms:block/23/statue-robe", "inscr": "backrooms:block/23/statue-inscription",
              "eye": "backrooms:block/23/statue-eye", "twig": "backrooms:block/23/bark-pale", "leaf": "backrooms:block/23/leaves-0"}


def blocks():
    out = []
    out.append(sided("l23-sentryface", "// Level 23 (round 4): a buried sentry's face sculpted out of the bark (the face on the -side); says nothing until someone says it",
                     [("kind", ["grey"])], lambda s: "sentryface", lambda s: FACE_TEX, "Wood", WOOD_SOUNDS,
                     extra={"lightAbsorption": 99, "resistance": 9}))
    out.append(sided("l23-column", "// Level 23 (round 4): the Parthenon's columns (base, fluted shaft, Doric capital, a broken stump), clean or mossy",
                     [("part", ["base", "shaft", "capital", "broken"]), ("moss", ["clean", "mossy"])],
                     lambda s: f"column-{s['part']}",
                     lambda s: {"stone": f"backrooms:block/23/{'ruinmoss' if s['moss'] == 'mossy' else 'ruinstone'}",
                                "flute": f"backrooms:block/23/flute-{s['moss']}"},
                     "Stone", STONE_SOUNDS, collision={"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 1, "z2": 0.85},
                     selection={"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 1, "z2": 0.85}, extra={"resistance": 8}))
    out.append(sided("l23-statue", "// Level 23 (round 4): a robed Architect on a plinth (three blocks: plinth, lower, upper), facing out; green stones for eyes",
                     [("part", ["plinth", "lower", "upper"])], lambda s: f"statue-{s['part']}", lambda s: STATUE_TEX,
                     "Stone", STONE_SOUNDS, collision={"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 1, "z2": 0.85},
                     selection={"x1": 0.15, "y1": 0, "z1": 0.15, "x2": 0.85, "y2": 1, "z2": 0.85}, extra={"resistance": 8}))
    out.append(("// Level 23 (round 4): lily pads on the Heart of Water's shallows (the block over the water)", {
        "code": "l23-lilypad", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Plant", "drawtype": "json",
        "shape": {"base": "block/23/lilypad"}, "renderpass": "OpaqueNoCull", "faceCullMode": "NeverCull",
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0.3, "replaceable": 3000,
        "collisionbox": None, "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.1, "z2": 0.9}, "drops": [],
        "sounds": {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}}))
    out.append(sided("l23-frieze", "// Level 23 (round 4): a carved lintel over a ruin's door (cornice, dentils, a garland and a rosette), front on the -side",
                     [("moss", ["clean"])], lambda s: "frieze", lambda s: {"stone": "backrooms:block/23/ruinstone", "moss": "backrooms:block/23/ruinmoss"},
                     "Stone", STONE_SOUNDS, extra={"resistance": 8, "lightAbsorption": 99}))
    out.append(("// Level 23 (round 4): a bird's nest on a limb (the lore's Curabitur Birds; an invention: the nest alone)", {
        "code": "l23-nest", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Plant", "drawtype": "json",
        "shape": {"base": "block/23/nest"}, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "resistance": 0.5, "collisionbox": None, "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.3, "x2": 0.8, "y2": 0.2, "z2": 0.8},
        "drops": [G.drop("game:stick", 1, 1)],
        "sounds": {"walk": "game:walk/grass*", "place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"}}))
    out.append(sided("l23-rootknuckle", "// Level 23 (round 4): the rounded top of a root crawling out over the ground (bare or mossed)",
                     [("kind", ["bare", "moss"])], lambda s: "rootknuckle",
                     lambda s: {"root": "backrooms:block/23/root" if s["kind"] == "bare" else "backrooms:block/23/mossbark",
                                "top": "backrooms:block/23/root" if s["kind"] == "bare" else "backrooms:block/23/moss-cushion"},
                     "Wood", WOOD_SOUNDS, drops=[G.drop("game:stick", 1, 1)], extra={"resistance": 6}))
    out.append(("// Level 23 (round 4): a slice of a shaft of light under a hole in the lid (translucent, glows, gives no light, nothing to hit)", {
        "code": "l23-sunbeam", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Air", "drawtype": "json",
        "shape": {"base": "block/23/sunbeam"}, "renderpass": "Transparent", "faceCullMode": "NeverCull", "emitSideAo": {"all": False},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 0, "replaceable": 9000,
        "collisionbox": None, "selectionbox": None, "rainPermeable": True, "drops": [], "sounds": {}}))
    return out


def shapes():
    out = {"sentryface": shape(FACE_TEX, sentryface_shape()),
           "lilypad": shape({"pad": "backrooms:block/23/lilypad", "flower": "backrooms:block/23/lilyflower", "heart": "backrooms:block/23/lilyheart"},
                            lilypad_shape())}
    out["bracket"] = shape({"cap": "backrooms:block/23/mushcap-top", "rim": "backrooms:block/23/mushstem", "gills": "backrooms:block/23/mushcap-gills"},
                           bracket_shape())
    out["signboard"] = shape({"face": "backrooms:block/23/sign-trail", "wood": "backrooms:block/23/planks", "nail": "backrooms:block/23/iron"},
                             signboard_shape())
    out["signpost"] = shape({"wood": "backrooms:block/23/planks", "moss": "backrooms:block/23/moss-cushion"}, signpost_shape())
    out["stone-sapling"] = shape({"bark": "backrooms:block/23/bark-pale"}, stone_sapling_shape())
    out["stone-shrub"] = shape({"bark": "backrooms:block/23/bark-grey"}, stone_shrub_shape())
    out["amphora"] = shape({"clay": "backrooms:block/23/terracotta"}, amphora_shape())
    out["stone-fern"] = shape({"bark": "backrooms:block/23/bark-grey-2"}, stone_fern_shape())
    out["frieze"] = shape({"stone": "backrooms:block/23/ruinstone", "moss": "backrooms:block/23/ruinmoss"}, frieze_shape())
    out["nest"] = shape({"twig": "backrooms:block/23/bark-pale", "egg": "backrooms:block/23/lilyflower"}, nest_shape())
    out["rootknuckle"] = shape({"root": "backrooms:block/23/root", "top": "backrooms:block/23/root"}, rootknuckle_shape())
    out["sunbeam"] = shape({"beam": "backrooms:block/23/sunbeam"}, sunbeam_shape())
    for part in ("base", "shaft", "capital", "broken"):
        out[f"column-{part}"] = shape({"stone": "backrooms:block/23/ruinstone", "flute": "backrooms:block/23/flute-clean"}, column_shape(part))
    for part in ("plinth", "lower", "upper"):
        out[f"statue-{part}"] = shape(STATUE_TEX, statue_shape(part))
    for c in ("teal", "violet", "amber"):
        out[f"glowcap-{c}"] = shape({"cap": f"backrooms:block/23/glowcap-{c}", "stem": "backrooms:block/23/glowstem",
                                     "gills": f"backrooms:block/23/glowgills-{c}"}, glowcap_cluster(c))
    return out


def textures(save):
    save(skin(2452), "block/23/sentry-skin")
    save(mouth(2453), "block/23/sentry-mouth")
    save(opaque(flute(False)), "block/23/flute-clean")
    save(opaque(flute(True)), "block/23/flute-mossy")
    save(opaque(robe()), "block/23/statue-robe")
    save(opaque(inscription()), "block/23/statue-inscription")
    save(Image.new("RGBA", (S, S), (70, 200, 110, 255)), "block/23/statue-eye")
    save(lilypad_tex(2459), "block/23/lilypad")
    save(sunbeam_tex(), "block/23/sunbeam")
    save(M.noise_hv((236, 232, 222), 3, 2460, mottle=4), "block/23/lilyflower")
    save(M.noise_hv((230, 196, 70), 3, 2461, mottle=3), "block/23/lilyheart")
    for c in ("teal", "violet", "amber"):
        save(gills_glow(G.GLOW[c], 2462 + len(c)), f"block/23/glowgills-{c}")


LANG = [
    ("block-l23-sentryface-*", "Buried Sentry"),
    ("blockdesc-l23-sentryface-*", "A face in the bark, eyes shut, mouth open. Someone was trapped here, or something was put here to keep watch. It is quiet. Keep it that way: never say, near one, that it's only a matter of time."),
    ("block-l23-column-*", "Architects' Column"),
    ("block-l23-statue-*", "Statue of an Architect"),
    ("blockdesc-l23-statue-*", "A robed figure holding a sapling to its chest, the face worn away but for two green stones set for eyes. On the plinth: HORTVLANO MAGNO, \"to the Great Gardener\"."),
    ("block-l23-lilypad", "Lily Pads"),
    ("block-l23-sunbeam", "Shaft of Light"),
    ("block-l23-rootknuckle-*", "Petrified Root"),
    ("block-l23-frieze-*", "Carved Lintel"),
    ("block-l23-nest", "Bird's Nest"),
    ("blockdesc-l23-nest", "Twigs of stone, woven tight. The eggs are cold. Whatever laid them is somewhere up in the dark."),
]
