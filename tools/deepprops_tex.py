"""Textures for the deep-level props of the graphics pass's "deep props" round: Level 6.1's food-court signs and its
exit and kitchen doors, Level 9's tool shelf, Level 10's tool rack, barrel of nails, feed trough and hand pump.

Every key starts with `dp-` (graphics pass B9's lesson: all props share textures/block/detail/, so a plain name can
overwrite another level's texture). Lettering is drawn in a pixel face (`FONT`), never scaled type. Nothing here
changes an old key. `generate()` is called from gen_deep.generate().
"""
import random

from PIL import Image, ImageDraw

import matlib as M
from detail_kit import seed_of
from detail_textures import S, save

# 3x5 capitals for the signs and plates (the letters the props use)
FONT = {
    "A": ("010", "101", "111", "101", "101"), "B": ("110", "101", "110", "101", "110"), "C": ("011", "100", "100", "100", "011"),
    "D": ("110", "101", "101", "101", "110"), "E": ("111", "100", "111", "100", "111"), "G": ("011", "100", "101", "101", "011"),
    "I": ("111", "010", "010", "010", "111"), "N": ("110", "101", "101", "101", "101"), "O": ("010", "101", "101", "101", "010"),
    "P": ("110", "101", "110", "100", "100"), "R": ("110", "101", "110", "101", "101"), "S": ("011", "100", "010", "001", "110"),
    "T": ("111", "010", "010", "010", "010"), "U": ("101", "101", "101", "101", "111"), "X": ("101", "101", "010", "101", "101"),
    "Z": ("111", "001", "010", "100", "111"),
}
TALL = (0, 1, 1, 2, 3, 3, 4)  # a 3x5 face stretched to 7 rows: the stems grow, the strokes stay one pixel


def word_width(word, gap=1):
    return sum(len(FONT[c][0]) for c in word) + gap * (len(word) - 1)


def draw_word(img, word, x, y, ink, gap=1, tall=False, shadow=None):
    """A word in the pixel face with its top-left at (x, y); `tall` stretches it to seven rows."""
    p = img.load()
    rows = TALL if tall else range(5)
    for ch in word:
        g = FONT[ch]
        for r, src in enumerate(rows):
            for c, bit in enumerate(g[src]):
                if bit == "1":
                    if shadow:
                        p[x + c + 1, y + r + 1] = M.rgba(shadow)
                    p[x + c, y + r] = ink if isinstance(ink, int) else M.rgba(ink)
        x += len(g[0]) + gap
    return x


def rgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


# ---------------- Level 6.1: the food-court signs ----------------

SIGNS = (("signburger", "BURGERS", 0xFF4060), ("signpizza", "PIZZA", 0x40FF90),
         ("signtaco", "TACOS", 0xFFC040), ("signdonut", "DONUTS", 0x60C0FF))


def sign_face(word, neon, seed):
    """A neon sign's lit face, 28 x 20 px of the 32 (the plate shows its top-left 14 x 10 units): a dark glass panel, a
    neon tube across the top and the bottom, and the word in tall pixel capitals with a halo of its own colour."""
    img = M.noise_hv((22, 20, 30), 2, seed, mottle=2)
    p = img.load()
    for y in range(S):  # outside the 28 x 20 window nothing shows; keep it the panel colour
        for x in range(S):
            if x >= 28 or y >= 20:
                p[x, y] = M.rgba((22, 20, 30))
    core = M.lift(neon, 28)
    halo = M.mix((22, 20, 30), neon, 0.38)
    far = M.mix((22, 20, 30), neon, 0.16)
    for x in range(1, 27):  # the tubes: a lit core with a halo above and below
        for y, c in ((2, core), (17, core)):
            p[x, y] = M.rgba(c)
            p[x, y - 1] = M.rgba(halo)
            p[x, y + 1] = M.rgba(halo)
    w = word_width(word)
    x0 = (28 - w) // 2
    y0 = 6
    mask = Image.new("L", (S, S), 0)
    draw_word(mask, word, x0, y0, 255, tall=True)
    m = mask.load()
    for y in range(S):  # halo round the letters, in two rings
        for x in range(S):
            if m[x, y]:
                continue
            near = any(0 <= x + dx < 28 and 0 <= y + dy < 20 and m[x + dx, y + dy] for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
            if near and 3 < y < 16:
                p[x, y] = M.rgba(halo)
    for y in range(S):
        for x in range(S):
            if m[x, y]:
                p[x, y] = M.rgba(M.lift(core, 4 if y % 2 else 0, 0.05))
    return img


def sign_case(seed):
    return M.painted_metal(seed, base=(40, 38, 46), grain=2, mottle=3, panel=False, chips=3, under=(88, 84, 90))


def signs():
    for key, word, neon in SIGNS:
        save(sign_face(word, rgb(neon), seed_of(key)), key)
    save(sign_case(seed_of("dp-signcase")), "dp-signcase")


# ---------------- Shared metals ----------------

def steel(seed, base=(168, 172, 176), direction="h"):
    return M.brushed_metal(seed, base=base, grain=3, direction=direction, streak=7, sheen=8)


def dark_iron(seed, base=(46, 48, 52)):
    img = M.noise_hv(base, 4, seed, mottle=4)
    M.scratches(img, 3, seed + 1, length=(2, 5), light=0.2)
    return img


def metals():
    save(steel(seed_of("dp-steel")), "dp-steel")
    save(dark_iron(seed_of("dp-iron")), "dp-iron")


# ---------------- Doors ----------------

def exit_leaf(upper):
    """The exit door's leaf, 13 x 16 units: rust-brown painted steel, a lit weld seam, rust at the foot and round the
    middle (the old door's tone, 99 69 53)."""
    seed = seed_of("dp-exitleaf" + ("u" if upper else "l"))
    img = M.painted_metal(seed, base=(112, 78, 58), grain=3, mottle=6, panel=False, chips=0)
    p = img.load()
    # welded stiffener ribs: a dark groove with a lit lip under it across the leaf, so it is not one flat sheet
    for y in ((9, 22) if not upper else (5, 20)):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y], -26))
            p[x, y + 1] = M.rgba(M.lift(p[x, y + 1], 10))
    M.rust(img, 0.32 if not upper else 0.22, seed + 5, color=(150, 82, 40), dark=(86, 48, 30), cells=(4, 2, 1))
    M.drips(img, 3, seed + 6, color=(86, 54, 36), length=(5, 14), strength=0.4)
    M.grime(img, 0.18, seed + 7, color=(60, 44, 34), bias="bottom" if not upper else None)
    M.scratches(img, 5, seed + 8, length=(3, 8), light=0.16)
    return img


def exit_plate():
    """The EXIT plate, 12 x 5 units (24 x 10 px): white capitals on red enamel with a white rule."""
    img = M.noise_hv((178, 36, 30), 2, seed_of("dp-exitplate"), mottle=2)
    p = img.load()
    for y in range(S):
        for x in range(S):
            if x >= 24 or y >= 10:
                p[x, y] = M.rgba((178, 36, 30))
    for x in range(24):
        p[x, 0] = M.rgba((232, 228, 220))
        p[x, 9] = M.rgba((232, 228, 220))
    for y in range(10):
        p[0, y] = M.rgba((232, 228, 220))
        p[23, y] = M.rgba((232, 228, 220))
    w = word_width("EXIT", 2)
    draw_word(img, "EXIT", (24 - w) // 2, 2, (246, 240, 230), gap=2)
    M.rust(img, 0.12, 31, color=(120, 60, 40), dark=(80, 40, 30), cells=(4, 2, 1))
    return img


def wired_glass(seed):
    """A pane behind a door's window: dark blue-green glass with a wire diamond mesh and two short glints, painted
    opaque (the block draws it in its opaque pass)."""
    img = M.noise_hv((44, 62, 68), 2, seed, mottle=3)
    p = img.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                p[x, y] = M.rgba(M.lift(p[x, y], 14))
    for k in range(3):
        p[3 + k, 9 - k] = M.rgba((176, 200, 206))
    for k in range(2):
        p[8 + k, 5 - k] = M.rgba((150, 176, 182))
    return img


def porthole_glass(seed):
    """A kitchen door's porthole, 4 x 5.5 units (8 x 11 px) of dark glass: a lit streak, a reflected strip light, the
    corners nicked off in the steel's tone. Opaque, so it reads as dark, deep glass."""
    img = M.noise_hv((34, 48, 54), 2, seed, mottle=2)
    p = img.load()
    for y in range(11):
        for x in range(8):
            if y > 4:
                p[x, y] = M.rgba(M.lift(p[x, y], -4))
    for k in range(4):
        p[1 + k, 6 - k] = M.rgba((156, 184, 192))
    p[2, 7] = M.rgba((120, 148, 156))
    for x in range(2, 7):
        p[x, 9] = M.rgba(M.lift(p[x, 9], 16))
    steelc = (150, 152, 152)
    for (x, y) in ((0, 0), (1, 0), (0, 1), (7, 0), (6, 0), (7, 1), (0, 10), (1, 10), (0, 9), (7, 10), (6, 10), (7, 9)):
        p[x, y] = M.rgba(steelc)
    return img


def kitchen_leaf(upper):
    """A swing door's leaf, 6.25 x 16 units: painted pale steel with a fine grain, a lit top edge and a dark foot edge
    (the old door's tone, 180 182 181 below and 169 171 171 above)."""
    seed = seed_of("dp-kitleaf" + ("u" if upper else "l"))
    img = M.brushed_metal(seed, base=(196, 198, 196) if not upper else (186, 188, 188), grain=2, direction="v", streak=5, sheen=6)
    M.scratches(img, 4 if not upper else 3, seed + 3, length=(3, 8), light=0.14)
    M.grime(img, 0.1, seed + 4, color=(104, 100, 90), bias="bottom" if not upper else None)
    return img


def doors():
    save(exit_leaf(False), "dp-exitleaf-lower")
    save(exit_leaf(True), "dp-exitleaf-upper")
    save(exit_plate(), "dp-exitplate")
    img = M.painted_metal(seed_of("dp-exitframe"), base=(74, 56, 46), grain=2, mottle=3, panel=False, chips=3, under=(110, 96, 84))
    M.rust(img, 0.25, 41, color=(140, 76, 40), dark=(80, 44, 30), cells=(4, 2, 1))
    save(img, "dp-exitframe")
    save(wired_glass(seed_of("dp-exitglass")), "dp-exitglass")
    img = M.galvanised(seed_of("dp-exitkick"), base=(140, 142, 140), spangle=10)
    M.scratches(img, 6, 51, length=(3, 8), light=0.2)
    M.grime(img, 0.2, 52, color=(70, 62, 52), bias="bottom")
    save(img, "dp-exitkick")
    save(kitchen_leaf(False), "dp-kitleaf-lower")
    save(kitchen_leaf(True), "dp-kitleaf-upper")
    save(steel(seed_of("dp-kitframe"), base=(150, 154, 154), direction="v"), "dp-kitframe")
    save(porthole_glass(seed_of("dp-kitglass")), "dp-kitglass")
    img = steel(seed_of("dp-kitkick"), base=(208, 210, 210))
    M.scratches(img, 8, 61, length=(3, 9), light=0.22)
    M.grime(img, 0.18, 62, color=(104, 98, 86), bias="bottom")
    save(img, "dp-kitkick")
    save(M.noise_hv((60, 62, 66), 2, seed_of("dp-kitgap"), mottle=2), "dp-kitgap")


# ---------------- Level 9: the tool shelf ----------------

def shelf_steel():
    """The shelving's uprights and boards: grey-green painted steel, chipped at the edges."""
    seed = seed_of("dp-shelfsteel")
    img = M.painted_metal(seed, base=(92, 104, 98), grain=2, mottle=3, panel=False, chips=6, under=(150, 146, 134))
    M.rust(img, 0.1, seed + 2, color=(130, 76, 42), dark=(84, 50, 32), cells=(4, 2, 1))
    return img


def pegboard():
    """Perforated hardboard, 32 px: a hole every 4 px (2 units, a hole each 3 cm), each a dark pit with a lit lip below;
    the board a warm khaki, a little greasy near the middle."""
    seed = seed_of("dp-pegboard")
    img = M.noise_hv((148, 124, 88), 3, seed, mottle=5)
    p = img.load()
    for hy in range(1, S, 4):
        for hx in range(1, S, 4):
            p[hx, hy] = M.rgba((46, 36, 26))
            p[hx, hy + 1] = M.rgba(M.lift(p[hx, hy + 1], 10)) if hy + 1 < S else p[hx, hy]
    M.grime(img, 0.12, seed + 3, color=(88, 70, 48), cells=(4, 2))
    return img


def tool_wood():
    seed = seed_of("dp-toolwood")
    return M.wood_planks(seed, base=(150, 108, 66), planks=4, direction="v", grain=3, contrast=0.8, flecks=0.4, per_plank=7, gap=(98, 70, 42))


def tool_steel():
    seed = seed_of("dp-toolsteel")
    img = M.brushed_metal(seed, base=(150, 154, 160), grain=3, direction="v", streak=8, sheen=12)
    M.scratches(img, 5, seed + 1, length=(2, 6), light=0.22)
    return img


def painted(name, base, chips=3):
    seed = seed_of(name)
    return M.painted_metal(seed, base=base, grain=2, mottle=3, panel=False, chips=chips, under=(120, 116, 108))


def toolbox_red():
    img = painted("dp-toolred", (160, 40, 34), 5)
    M.scratches(img, 4, 77, length=(3, 7), light=0.18)
    return img


def cardboard():
    seed = seed_of("dp-cardboard")
    img = M.noise_hv((160, 130, 88), 3, seed, mottle=5)
    p = img.load()
    for x in range(0, S, 1):  # flute lines
        if x % 3 == 0:
            for y in range(S):
                p[x, y] = M.rgba(M.lift(p[x, y], -5))
    for x in range(S):
        for y in (14, 15):
            p[x, y] = M.rgba(M.lift(p[x, y], -16 if y == 15 else 8))
    return img


def label_cardboard():
    """The box of nails/screws on the shelf: cardboard with a printed band."""
    img = cardboard()
    p = img.load()
    for y in range(6, 16):
        for x in range(2, 30):
            p[x, y] = M.rgba((228, 214, 160))
    for x in range(4, 28):
        p[x, 9] = M.rgba((150, 40, 30))
        p[x, 12] = M.rgba((60, 54, 44))
    return img


def tin_can(base, band):
    seed = seed_of("dp-tin" + str(base))
    img = M.brushed_metal(seed, base=base, grain=2, direction="v", streak=4, sheen=10)
    p = img.load()
    for y in range(8, 22):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(band, ((x * 7 + y * 3) % 5) - 2))
    for x in range(S):
        p[x, 7] = M.rgba(M.lift(base, -20))
        p[x, 22] = M.rgba(M.lift(base, -20))
    return img


def rope():
    img = Image.new("RGBA", (S, S), M.rgba((172, 146, 96)))
    p = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) % 4
            p[x, y] = M.rgba(M.lift((178, 150, 98), (-12, 4, 10, -2)[t]))
    return img


def shelf_textures():
    save(shelf_steel(), "dp-shelfsteel")
    save(pegboard(), "dp-pegboard")
    save(tool_wood(), "dp-toolwood")
    save(tool_steel(), "dp-toolsteel")
    save(toolbox_red(), "dp-toolred")
    save(painted("dp-toolyellow", (206, 168, 40)), "dp-toolyellow")
    save(painted("dp-toolblack", (36, 36, 40), 2), "dp-toolblack")
    save(label_cardboard(), "dp-cardlabel")
    save(tin_can((176, 178, 176), (186, 56, 40)), "dp-tinred")
    save(tin_can((176, 178, 176), (48, 98, 150)), "dp-tinblue")
    save(rope(), "dp-rope")


# ---------------- Level 10: tool rack, barrel, trough, pump ----------------

def rack_wood():
    seed = seed_of("dp-rackwood")
    img = M.wood_planks(seed, base=(122, 92, 60), planks=4, direction="h", grain=3, contrast=1.0, knots=0, flecks=0.8, per_plank=8, gap=(66, 46, 30))
    M.grime(img, 0.1, seed + 3, color=(70, 56, 40), cells=(4, 2))
    return img


def handle_wood():
    seed = seed_of("dp-handle")
    return M.wood_planks(seed, base=(176, 138, 92), planks=4, direction="v", grain=3, contrast=0.55, flecks=0.5, per_plank=5, gap=(120, 92, 58))


def barrel_staves():
    """Vertical staves of 6 px (a plate shows 16 px of it), each its own brown, a dark joint between, a lit left edge."""
    seed = seed_of("dp-barrel")
    img = M.wood_planks(seed, base=(104, 74, 46), planks=[6, 5, 5, 6, 5, 5], direction="v", grain=3, contrast=0.7, flecks=0.5, per_plank=8, gap=(48, 32, 22))
    M.grime(img, 0.12, seed + 3, color=(60, 44, 30), cells=(4, 2))
    return img


def hoop():
    seed = seed_of("dp-hoop")
    img = M.painted_metal(seed, base=(60, 60, 64), grain=3, mottle=4, panel=False, chips=0)
    M.rust(img, 0.35, seed + 1, color=(130, 72, 40), dark=(80, 46, 30), cells=(8, 4, 2))
    p = img.load()
    for x in range(4, S, 8):  # rivets
        for y in (14, 15):
            p[x, y] = M.rgba(M.lift(p[x, y], 24))
            p[x + 1, y] = M.rgba(M.lift(p[x + 1, y], -10))
    return img


def barrel_head():
    """The barrel's top edge and inside (seen from above): end grain in rings."""
    img = M.noise_hv((92, 64, 40), 3, seed_of("dp-barrelhead"), mottle=5)
    return img


def nail_heap():
    """A loose heap of nails seen from above and the side: dark iron, a lot of short bright lines at every angle
    (nails), a few rusted ones."""
    seed = seed_of("dp-nails")
    img = M.noise_hv((84, 84, 88), 6, seed, mottle=7)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(46):
        x, y = rng.randrange(S), rng.randrange(S)
        L = rng.randint(3, 7)
        dx, dy = rng.choice(((1, 0), (0, 1), (1, 1), (1, -1), (2, 1), (1, 2)))
        c = rng.choice(((170, 172, 176), (140, 144, 148), (110, 112, 116), (150, 100, 66), (84, 86, 90)))
        pts = [(x, y), (x + dx * L // 2, y + dy * L // 2)]
        d.line(pts, fill=M.rgba(c))
        d.point((x, y), fill=M.rgba(M.lift(c, 30)))  # the head
    return img


def trough_planks():
    seed = seed_of("dp-troughplank")
    img = M.wood_planks(seed, base=(130, 100, 66), planks=4, direction="h", grain=3, contrast=1.1, knots=0, flecks=0.9, per_plank=9, gap=(58, 40, 26))
    M.grime(img, 0.14, seed + 2, color=(76, 60, 42), cells=(4, 2))
    return img


def trough_plank_end():
    seed = seed_of("dp-troughend")
    img = M.wood_planks(seed, base=(130, 100, 66), planks=3, direction="v", grain=3, contrast=1.0, knots=0, flecks=0.9, per_plank=9, gap=(58, 40, 26))
    return img


def trough_timber():
    seed = seed_of("dp-troughpost")
    return M.wood_planks(seed, base=(86, 62, 40), planks=2, direction="v", grain=3, contrast=1.0, flecks=0.8, per_plank=6, gap=(44, 30, 20))


def feed_grain():
    """Rolled oats and cracked grain heaped in the trough: warm, short grains in all directions, a few darker seeds."""
    seed = seed_of("dp-feed")
    img = M.noise_hv((196, 164, 90), 8, seed, mottle=8)
    p = img.load()
    rng = random.Random(seed)
    for _ in range(90):
        x, y = rng.randrange(S), rng.randrange(S)
        c = rng.choice(((228, 200, 130), (170, 134, 70), (150, 112, 56), (214, 182, 104)))
        p[x, y] = M.rgba(c)
        if rng.random() < 0.6:
            p[(x + 1) % S, y] = M.rgba(M.lift(c, -14))
    return img


def hay_strand():
    seed = seed_of("dp-hay")
    img = M.noise_hv((206, 176, 92), 7, seed, mottle=6)
    p = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            if (x * 3 + (y // 4) * 2) % 5 == 0:
                p[x, y] = M.rgba(M.lift(p[x, y], -16))
    return img


def trough_water():
    """Rainwater in the trough: dark, slightly green, with a pale sheen band, a floating leaf and a ring (the old
    troughwater tone, 64 92 91)."""
    seed = seed_of("dp-troughwater")
    img = M.noise_hv((56, 84, 84), 2, seed, mottle=5)
    p = img.load()
    for x in range(S):
        for dy, d in ((0, 22), (1, 8)):
            y = (9 + int(1.4 * ((x // 4) % 2)) + dy) % S
            p[x, y] = M.rgba(M.lift(p[x, y], d))
    for (x, y) in ((22, 22), (23, 22), (22, 23), (23, 23), (24, 23)):
        p[x, y] = M.rgba((96, 108, 62))
    for k in range(5):
        p[5 + k, 19] = M.rgba(M.lift(p[5 + k, 19], 16))
    return img


def pump_iron():
    """Cast iron, rough from the sand: very dark green-black, a lit grain, rust bloom at the edges (the old pump was
    1c1e21 flat)."""
    seed = seed_of("dp-pumpiron")
    img = M.noise_hv((58, 62, 62), 7, seed, mottle=6)
    M.rust(img, 0.12, seed + 1, color=(110, 66, 40), dark=(72, 46, 34), cells=(8, 4, 2))
    return img


def pump_paint():
    """The pump's handle and spout: black enamel worn to iron."""
    seed = seed_of("dp-pumphandle")
    return M.painted_metal(seed, base=(40, 42, 46), grain=2, mottle=3, panel=False, chips=7, under=(104, 98, 90))


def pump_plinth():
    seed = seed_of("dp-pumpplinth")
    img = M.concrete(seed, base=(152, 148, 140), grain=3, mottle=6, aggregate=0.04, pores=0.01)
    M.grime(img, 0.18, seed + 1, color=(70, 62, 50), cells=(4, 2))
    return img


def pump_wet():
    img = M.concrete(seed_of("dp-pumpwet"), base=(96, 94, 90), grain=3, mottle=5, aggregate=0.03)
    return img


def barrel_textures():
    save(rack_wood(), "dp-rackwood")
    save(handle_wood(), "dp-handle")
    save(barrel_staves(), "dp-barrel")
    save(hoop(), "dp-hoop")
    save(barrel_head(), "dp-barrelhead")
    save(nail_heap(), "dp-nails")
    save(trough_planks(), "dp-troughplank")
    save(trough_plank_end(), "dp-troughend")
    save(trough_timber(), "dp-troughpost")
    save(feed_grain(), "dp-feed")
    save(hay_strand(), "dp-hay")
    save(trough_water(), "dp-troughwater")
    save(pump_iron(), "dp-pumpiron")
    save(pump_paint(), "dp-pumphandle")
    save(pump_plinth(), "dp-pumpplinth")
    save(pump_wet(), "dp-pumpwet")


def generate():
    signs()
    metals()
    doors()
    shelf_textures()
    barrel_textures()
