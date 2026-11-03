"""Level 31, "Roller Rink" (experimental): its five blocks, their textures and shapes, and its one sound.

    l31-rinkwood    the rink's polished maple boards: plain, with a painted lane stripe north-south or west-east, and the
                    centre circle's swirl; cubes
    l31-skatewall   the rink's walls: stripe (the lower band, blue with magenta and cyan stripes under a chrome rail),
                    plain (pale lavender gloss above it), blue (Skate Rental), chart (a skate size chart sign) and dasher
                    (the rink's low barrier: a white polymer kick panel, its top a padded black rail); cubes
    l31-mirror      a mirror panel on one face of a wall block (the others the wall's plain paint), by side; and the
                    disco ball hung under the rink's ceiling (JSON shape, lit)
    l31-tube        a ceiling light panel with two coloured tubes: magenta, cyan, amber, green, violet or white, each on
                    (gives light), lit (looks on, gives none), flicker (a failing one, BackroomsFlicker) or off; cubes
    l31-glowcarpet  dark carpet with 1990s teal and magenta squiggles that glow faintly (light 5); cube
    sounds/ambient/31/rinkmusic.ogg   a muffled four-chord synth-pop loop, as if from ceiling speakers two rooms away

Round 4 (tools/gen_31_round4.py, run after this one) rebuilds some of these blocks over this script's files; see its
docstring for which.

Textures are 32 px a block (block/31/); the ball's shape names its texture keys itself and its blocktype names no
textures for it. Run from the repo root:  python tools/gen_31.py
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image

from modelkit import box
from oggutil import write_ogg
from gen_entity_sounds import RATE
from texlib import S, vertical_gradient

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "31")
SHAPES = os.path.join(ASSETS, "shapes", "block", "31")
BLOCKS = os.path.join(ASSETS, "blocktypes", "31")
SIDES = ["north", "east", "south", "west"]

STONE = {"walk": "game:walk/stone*", "place": "game:block/loosestone*", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
WOOD = {"walk": "game:walk/wood*", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
GLASS = {"walk": "game:walk/stone", "place": "game:block/glass", "break": "game:block/glass", "hit": "game:block/glass"}
CLOTH = {"walk": "game:walk/cloth*", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}

# The room hues, in the order the layout numbers them (WorldLayout.L31Hues), with each tube's colour and its light
HUES = ["magenta", "cyan", "amber", "green", "violet", "white"]
TUBE_RGB = {"magenta": (255, 80, 214), "cyan": (90, 236, 255), "amber": (255, 184, 70), "green": (110, 255, 140),
            "violet": (170, 110, 255), "white": (246, 248, 255)}
LIGHT_HSV = {"magenta": [51, 6, 18], "cyan": [33, 6, 18], "amber": [6, 6, 18], "green": [20, 5, 17], "violet": [45, 6, 17],
             "white": [10, 1, 19]}

MAPLE = (222, 178, 118)
LAVENDER = (206, 200, 222)
NAVY = (34, 40, 88)
MAGENTA = (226, 60, 170)
CYAN = (60, 200, 230)
CHROME = (206, 212, 222)


def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


# ======================================================================== Textures

def clamp(v):
    return max(0, min(255, int(round(v))))


def shade(c, k):
    return tuple(clamp(v * k) for v in c)


def canvas(colour):
    return Image.new("RGBA", (S, S), tuple(colour) + (255,))


def rect(img, x0, y0, x1, y1, colour):
    px = img.load()
    for y in range(max(0, y0), min(S, y1 + 1)):
        for x in range(max(0, x0), min(S, x1 + 1)):
            px[x, y] = tuple(colour[:3]) + (255,)


def grain(img, seed, amount=4):
    rng = random.Random(seed)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount)
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), a)
    return img


def save(img, name):
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def rinkwood():
    """Maple strips 4 px wide along X, the joints staggered, under a varnish with a soft glossy streak."""
    def boards():
        img = Image.new("RGBA", (S, S))
        px = img.load()
        rng = random.Random(3101)
        for board in range(8):
            tone = rng.uniform(0.92, 1.07)
            joint = rng.randint(0, 31)
            for y in range(board * 4, board * 4 + 4):
                for x in range(S):
                    # A long glossy streak across the boards (wrapping, so the floor tiles)
                    gloss = 1 + 0.10 * math.exp(-((((x + y) % S) - 16) / 5.0) ** 2)
                    c = shade(MAPLE, tone * gloss * (1 + 0.03 * math.sin(x * 0.6 + board * 1.7)))
                    if y == board * 4:
                        c = shade(c, 0.72)
                    if x == joint:
                        c = shade(c, 0.66)
                    px[x, y] = c + (255,)
        return grain(img, 3102, 3)

    save(boards(), "rinkwood-plain")
    ns = boards()
    rect(ns, 13, 0, 18, 31, MAGENTA)
    rect(ns, 15, 0, 16, 31, shade(MAGENTA, 1.2))
    save(ns, "rinkwood-stripens")
    we = boards()
    rect(we, 0, 13, 31, 18, MAGENTA)
    rect(we, 0, 15, 31, 16, shade(MAGENTA, 1.2))
    save(we, "rinkwood-stripewe")
    # The centre circle: a painted swirl of magenta, cyan and violet bands (tiling)
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            v = math.sin(2 * math.pi * (x + 2 * y) / S + 1.5 * math.sin(2 * math.pi * (x - y) / S))
            c = MAGENTA if v > 0.35 else CYAN if v < -0.35 else (124, 70, 200)
            px[x, y] = shade(c, 0.95 + 0.08 * math.sin(2 * math.pi * x / S)) + (255,)
    save(grain(img, 3103, 3), "rinkwood-centre")


def walls():
    plain = canvas(LAVENDER)
    px = plain.load()
    for y in range(S):
        for x in range(S):
            k = 1 + 0.05 * math.sin(2 * math.pi * x / S)
            px[x, y] = shade(LAVENDER, k) + (255,)
    save(grain(plain, 3111, 3), "wall-plain")

    stripe = canvas(NAVY)
    rect(stripe, 0, 0, 31, 2, shade(CHROME, 0.75))  # the chrome rail
    rect(stripe, 0, 1, 31, 1, CHROME)
    rect(stripe, 0, 3, 31, 3, (20, 22, 40))
    rect(stripe, 0, 9, 31, 12, MAGENTA)
    rect(stripe, 0, 16, 31, 19, CYAN)
    rect(stripe, 0, 28, 31, 31, (22, 24, 46))  # the scuffed skirting
    save(grain(stripe, 3112, 3), "wall-stripe")

    blue = canvas((52, 104, 196))
    rect(blue, 0, 27, 31, 31, (30, 52, 104))
    save(grain(blue, 3113, 4), "wall-blue")

    chart = canvas((52, 104, 196))
    rect(chart, 3, 3, 28, 28, (240, 240, 232))
    rect(chart, 3, 3, 28, 7, (220, 50, 70))  # the red header band ("SIZES")
    for k in range(4):
        rect(chart, 8 + 4 * k, 4, 9 + 4 * k, 6, (250, 250, 250))
    rng = random.Random(3114)
    for row in range(5):
        y = 10 + row * 4
        rect(chart, 4, y + 3, 27, y + 3, (200, 200, 196))
        for col in range(3):
            x = 6 + col * 8
            for k in range(rng.randint(1, 2)):  # a number or two in each cell
                rect(chart, x + 2 * k, y, x + 2 * k, y + 2, (40, 40, 48))
    save(grain(chart, 3115, 2), "wall-chart")

    side = canvas((236, 238, 240))
    rect(side, 0, 0, 31, 4, (40, 86, 190))
    rect(side, 0, 5, 31, 5, (180, 186, 196))
    rect(side, 0, 26, 31, 31, (36, 36, 40))  # the kick strip
    for x in (0, 15, 16, 31):
        rect(side, x, 6, x, 25, (200, 204, 210))  # the panel seams
    save(grain(side, 3116, 2), "dasher-side")
    top = canvas((30, 30, 36))
    px = top.load()
    for y in range(S):
        for x in range(S):
            k = 1 + 0.25 * math.exp(-((y - 15.5) / 5) ** 2)
            px[x, y] = shade((30, 30, 36), k) + (255,)
    save(grain(top, 3117, 3), "dasher-top")


def mirror():
    """Silver with a faint blue tint, a bevelled edge and a diagonal sheen; and the ball's facets."""
    img = vertical_gradient((214, 222, 236), (168, 178, 198))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            k = 1 + 0.18 * math.exp(-(((x - y) - 4) / 3.0) ** 2) + 0.10 * math.exp(-(((x - y) + 10) / 2.0) ** 2)
            px[x, y] = (clamp(r * k), clamp(g * k), clamp(b * k), 255)
    for i in range(S):
        for (x, y, c) in ((i, 0, 0.75), (i, 31, 0.6), (0, i, 0.75), (31, i, 0.6), (i, 1, 1.1), (1, i, 1.1)):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * c), clamp(g * c), clamp(b * c), 255)
    save(grain(img, 3121, 2), "mirror")

    ball = Image.new("RGBA", (S, S))
    px = ball.load()
    rng = random.Random(3122)
    cells = [[rng.choice((0.55, 0.7, 0.85, 1.0, 1.15, 1.3)) for _ in range(8)] for _ in range(8)]
    for y in range(S):
        for x in range(S):
            k = cells[y // 4][x // 4]
            c = shade((200, 206, 220), k)
            if x % 4 == 0 or y % 4 == 0:
                c = (70, 72, 80)
            px[x, y] = c + (255,)
    save(ball, "discoball")
    save(grain(canvas((60, 62, 70)), 3123, 4), "chain")


def tubes():
    """A ceiling panel: a dark housing, a frosted diffuser, two tubes across it in the hue; the dead one grey."""
    def panel(tube):
        img = canvas((44, 44, 52))
        rect(img, 2, 2, 29, 29, (70, 70, 80))
        for y0 in (8, 20):
            rect(img, 3, y0, 28, y0 + 3, tube)
            rect(img, 3, y0 + 1, 28, y0 + 2, tuple(clamp(v * 0.5 + 128) for v in tube))
        rect(img, 0, 0, 31, 0, (30, 30, 36))
        rect(img, 0, 0, 0, 31, (30, 30, 36))
        return grain(img, 3131, 2)
    for hue in HUES:
        save(panel(TUBE_RGB[hue]), "tube-" + hue)
    save(panel((96, 96, 104)), "tube-off")


def glowcarpet():
    """Dark navy pile with teal and magenta confetti squiggles (tiling: they wrap round the edges)."""
    img = canvas((26, 24, 56))
    px = img.load()
    rng = random.Random(3141)
    for _ in range(9):
        colour = rng.choice(((60, 230, 210), (240, 70, 190), (250, 220, 90)))
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, 2 * math.pi)
        for k in range(rng.randint(6, 11)):
            a += rng.uniform(-0.9, 0.9)
            x, y = x + math.cos(a), y + math.sin(a)
            px[int(x) % S, int(y) % S] = colour + (255,)
            px[int(x + 1) % S, int(y) % S] = colour + (255,)
    save(grain(img, 3142, 4), "glowcarpet")


# ======================================================================== Shapes

def shape(name, elements):
    keys = sorted({face["texture"][1:] for e in elements for face in e["faces"].values()})
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: "backrooms:block/31/" + k for k in keys}, "elements": elements}
    write_json(os.path.join(SHAPES, name + ".json"), data)
    return "backrooms:block/31/" + name


def ball_shape():
    # A faceted ball hung from the ceiling by a short chain: an octagonal-ish stack of boxes, glowing a little
    els = [
        box("Chain", (7.5, 12, 7.5), (8.5, 16, 8.5), "chain"),
        box("Core", (3, 2, 3), (13, 12, 13), "discoball", glow=120),
        box("BandX", (2, 4, 4), (14, 10, 12), "discoball", faces=("east", "west"), glow=120),
        box("BandZ", (4, 4, 2), (12, 10, 14), "discoball", faces=("north", "south"), glow=120),
        box("Cap", (5, 12, 5), (11, 13, 11), "discoball", faces=("up", "north", "east", "south", "west"), glow=120),
        box("Foot", (5, 1, 5), (11, 2, 11), "discoball", faces=("down", "north", "east", "south", "west"), glow=120),
    ]
    return shape("l31-discoball", els)


# ======================================================================== Block types

def tex(name):
    return {"base": "block/31/" + name}


def cube_block(code, groups, textures_by_type, comment, material="Stone", sounds=STONE, extra=None):
    data = {"code": code, "variantgroups": groups, "texturesByType": textures_by_type,
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": material, "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": sounds}
    data.update(extra or {})
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)


def blocktypes():
    kinds = ["plain", "stripens", "stripewe", "centre"]
    cube_block("l31-rinkwood", [{"code": "kind", "states": kinds}], {f"*-{k}": {"all": tex("rinkwood-" + k)} for k in kinds},
               "Level 31: the rink's polished maple boards (plain, a painted lane stripe north-south or west-east, the centre circle's swirl)",
               material="Wood", sounds=WOOD)

    walls_ = {"stripe": {"all": tex("wall-stripe")}, "plain": {"all": tex("wall-plain")}, "blue": {"all": tex("wall-blue")},
              "chart": {"all": tex("wall-chart"), "up": tex("wall-blue"), "down": tex("wall-blue")},
              "dasher": {"all": tex("dasher-side"), "up": tex("dasher-top"), "down": tex("dasher-top")}}
    cube_block("l31-skatewall", [{"code": "kind", "states": list(walls_)}], {f"*-{k}": v for k, v in walls_.items()},
               "Level 31: the rink's walls (stripe: the lower band under a chrome rail; plain: lavender gloss; blue: Skate Rental's; chart: a "
               "size chart sign; dasher: the rink's low barrier, white polymer under a padded rail)")

    # Mirror panels (cubes, the mirror on one face) and the disco ball (a JSON shape)
    states = SIDES + ["ball"]
    textures = {}
    for side in SIDES:
        faces = {f: tex("wall-plain") for f in SIDES + ["up", "down"]}
        faces[side] = tex("mirror")
        textures[f"*-{side}"] = faces
    ball = ball_shape()
    data = {"code": "l31-mirror", "variantgroups": [{"code": "kind", "states": states}],
            "texturesByType": textures,
            "drawtypeByType": {"*-ball": "json", "*": "cube"},
            "shapeByType": {"*-ball": {"base": ball}},
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Glass",
            "sidesolidByType": {"*-ball": {"all": False}},
            "sideopaqueByType": {"*-ball": {"all": False}},
            "lightAbsorptionByType": {"*-ball": 0, "*": 99},
            "lightHsvByType": {"*-ball": [48, 2, 16]},
            "collisionboxByType": {"*-ball": {"x1": 0.1875, "y1": 0.0625, "z1": 0.1875, "x2": 0.8125, "y2": 1, "z2": 0.8125}},
            "selectionboxByType": {"*-ball": {"x1": 0.1875, "y1": 0.0625, "z1": 0.1875, "x2": 0.8125, "y2": 1, "z2": 0.8125}},
            "resistance": 3, "drops": [], "sounds": GLASS}
    write_json(os.path.join(BLOCKS, "l31-mirror.json"), data,
               "Level 31: a mirror panel on one face of a wall block (the others the wall's lavender paint), by side; and the disco ball hung "
               "under the rink's ceiling (lit)")

    # The coloured tubes
    states = ["on", "lit", "flicker", "off"]
    textures = {}
    light = {}
    glow = {}
    attrs = {}
    entity = {}
    sounds = {}
    for hue in HUES:
        textures[f"*-{hue}-off"] = {"all": tex("tube-off")}
        textures[f"*-{hue}-*"] = {"all": tex("tube-" + hue)}
        light[f"*-{hue}-on"] = LIGHT_HSV[hue]
        attrs[f"*-{hue}-flicker"] = {"offBlock": f"backrooms:l31-tube-{hue}-off"}
    for st in ("on", "lit", "flicker"):
        glow[f"*-{st}"] = {"glowLevel": 160}
    entity["*-flicker"] = "BackroomsFlicker"
    hum = dict(GLASS, ambient="backrooms:ambient/hum", ambientBlockCount=140)
    sounds["*-on"] = hum
    sounds["*"] = GLASS
    data = {"code": "l31-tube", "variantgroups": [{"code": "hue", "states": HUES}, {"code": "state", "states": states}],
            "texturesByType": textures, "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Glass", "drawtype": "cube", "lightHsvByType": light, "vertexFlagsByType": glow,
            "entityClassByType": entity, "attributesByType": attrs,
            # Must be 0: a light source subtracts its own absorption before spreading
            "lightAbsorption": 0, "resistance": 0.8, "drops": [], "soundsByType": sounds}
    write_json(os.path.join(BLOCKS, "l31-tube.json"), data,
               "Level 31: a ceiling light panel with two coloured tubes (on: gives light; lit: looks on, gives none; flicker: a failing one; off)")

    cube_block("l31-glowcarpet", [{"code": "kind", "states": ["plain"]}], {"*": {"all": tex("glowcarpet")}},
               "Level 31: dark carpet with 1990s teal and magenta squiggles that glow faintly",
               material="Cloth", sounds=CLOTH,
               extra={"lightHsv": [44, 4, 5], "vertexFlags": {"glowLevel": 60}})


# ======================================================================== Sound

def lowpass_circular(sig, cutoff, slope=2.0):
    """A soft low-pass done in the frequency domain on the whole loop (circular, so the loop stays seamless)."""
    spec = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / RATE)
    spec *= 1 / (1 + (f / cutoff) ** (2 * slope))
    spec *= 1 - np.exp(-(f / 90) ** 2)  # the little ceiling speakers have no real bass
    return np.fft.irfft(spec, n=len(sig))


def room_circular(sig, decay=0.45):
    """A rink-sized room: an exponential noise tail convolved round the loop."""
    rng = np.random.default_rng(3151)
    n = len(sig)
    k = np.zeros(n)
    m = int(1.2 * RATE)
    k[:m] = rng.normal(size=m) * np.exp(-np.arange(m) / (decay * RATE)) * 0.012
    k[0] = 1.0
    for d, g in ((0.043, 0.35), (0.071, 0.25), (0.113, 0.18)):
        k[int(d * RATE)] += g
    return np.fft.irfft(np.fft.rfft(sig) * np.fft.rfft(k), n=n)


def rinkmusic():
    """Sixteen bars of 1990s rink synth-pop at 120 bpm (32 s, looping): a four-chord progression on a pad, a saw bass on
    the beat, kick, snare and hats, a square lead; then muffled and smeared as if from ceiling speakers far off."""
    rng = np.random.default_rng(3150)
    bpm = 120
    beat = 60 / bpm
    bars = 16
    n = int(bars * 4 * beat * RATE)
    out = np.zeros(n)
    t_all = np.arange(n) / RATE

    def add(sound, at):
        i = int(at * RATE) % n
        j = min(n, i + len(sound))
        out[i:j] += sound[: j - i]
        if i + len(sound) > n:  # wrap round the loop
            out[: i + len(sound) - n] += sound[j - i:]

    def note(midi):
        return 440 * 2 ** ((midi - 69) / 12)

    # I - V - vi - IV in C: C, G, Am, F (two bars each, twice)
    chords = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]
    for bar in range(bars):
        root, triad = chords[(bar // 2) % 4]
        at = bar * 4 * beat
        # The pad: detuned saws, the whole bar
        t = np.arange(int(4 * beat * RATE)) / RATE
        env = np.minimum(1, t / 0.08) * np.minimum(1, (4 * beat - t) / 0.1)
        pad = sum(((2 * ((note(m) * (1 + d) * t) % 1) - 1) for m in triad for d in (-0.004, 0.004))) * 0.05 * env
        add(pad, at)
        for b8 in range(8):
            t8 = np.arange(int(beat / 2 * RATE)) / RATE
            # The saw bass on eighths, the root and its octave
            f = note(root - 12 + (12 if b8 % 2 else 0))
            saw = (2 * ((f * t8) % 1) - 1) * np.exp(-t8 * 6) * 0.22
            add(saw, at + b8 * beat / 2)
            # Hats on the off-eighths
            if b8 % 2:
                hat = rng.normal(size=int(0.04 * RATE)) * np.exp(-np.arange(int(0.04 * RATE)) / RATE * 90) * 0.05
                add(hat, at + b8 * beat / 2)
        for b in range(4):
            tk = np.arange(int(0.25 * RATE)) / RATE
            kick = np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tk * 30)) / RATE) * np.exp(-tk * 9) * 0.55
            add(kick, at + b * beat)
            if b % 2:
                ts = np.arange(int(0.2 * RATE)) / RATE
                snare = (rng.normal(size=len(ts)) * 0.3 + np.sin(2 * np.pi * 190 * ts) * 0.3) * np.exp(-ts * 16) * 0.35
                add(snare, at + b * beat)
    # The lead: a square-wave hook over the chords, a different turn in the second half
    hook = [72, 74, 76, 79, 76, 74, 72, None, 71, 72, 74, 71, 67, None, 69, 71,
            72, 69, 72, 76, 74, 72, 69, None, 69, 72, 77, 76, 74, 72, None, None]
    hook2 = [79, None, 79, 77, 76, 74, 76, None, 74, 76, 79, 74, 71, None, 67, 71,
             72, 76, 81, 79, 77, 76, 72, None, 72, 74, 77, 76, 74, 71, 72, None]
    for half, line in ((0, hook), (1, hook2)):
        for k, m in enumerate(line):
            if m is None:
                continue
            at = half * 8 * 4 * beat + k * beat
            tl = np.arange(int(beat * 0.9 * RATE)) / RATE
            f = note(m) * (1 + 0.003 * np.sin(2 * np.pi * 5 * tl))
            sq = np.sign(np.sin(2 * np.pi * np.cumsum(f) / RATE)) * np.minimum(1, tl / 0.01) * np.exp(-tl * 2.5) * 0.10
            add(sq, at)
    # Through the ceiling speakers, two rooms away
    sig = lowpass_circular(out, 1500)
    sig = room_circular(sig)
    sig += 0.004 * lowpass_circular(rng.normal(size=n), 3000)  # a little speaker hiss
    sig = 0.6 * sig / max(1e-9, np.max(np.abs(sig)))
    path = os.path.join(ASSETS, "sounds", "ambient", "31", "rinkmusic.ogg")
    if write_ogg(path, sig, RATE):
        print("wrote", os.path.relpath(path, ROOT))


def main():
    rinkwood()
    walls()
    mirror()
    tubes()
    glowcarpet()
    blocktypes()
    rinkmusic()
    print("Level 31: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in", os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
