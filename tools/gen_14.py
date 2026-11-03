"""Level 14, "The Hospital" (experimental): its surfaces and architecture, their textures and shapes.
(docs/design/experimental-levels/14-plan.md, section 4: "Surfaces and architecture".) The furniture is
tools/gen_14_props.py's, the link doors and the placard tools/gen_14_links.py's.

    l14-wall        cubes: the halls' mint paint (paint, paintscuff), the teal-green wainscot at the foot with its steel
                    kick strip (paintbase), the inpatient units' blinding white (white, whitebase), white wall tile (tile,
                    tilebase), the behaviour cells' quilted padding, painted cinderblock, patched plywood, corroded steel
                    plate (rust, rustblood), filthy tiles with blood running down them (tileblood), mould, white with moss
                    creeping up (whitemoss), bare concrete, and a doorway's steel frame head (lintel)
    l14-rail        a hall wall's foot (paintbase or whitebase) with a handrail on brackets and a bumper strip proud of
                    its face (paint, white; four sides); JSON
    l14-walldeco    a mint wall block with one face dressed: room plates, the department signs, children's posters,
                    health posters, a stopped clock, a ward whiteboard, a lit X-ray light box, blood (a smear, running
                    down from above), mould, scratches, the green running man, a sanitizer, an extinguisher, the
                    T.14.R.G. stencil; cubes
    l14-window      a window in a wall (lower, upper; broken: a few shards left, shattered: almost none) with nothing
                    but black behind it; JSON
    l14-floor       cubes: sheet vinyl (vinyl, vinylworn, vinylborder), white, pink, the theatres' epoxy, terrazzo,
                    concrete, marble (marbleshattered), blood, mould, contam (faintly glowing), cracked (the warning),
                    the red way line and its arrows; sagging (a patch giving way, sunk, black in its gaps) is JSON
    l14-ceiling     cubes: acoustic tiles (tile, stained), the troffers (on: light 16; bright: 20; lit: looks it; flicker;
                    off), a missing tile (hole), blood, mould, plaster, concrete
    l14-door        a hospital room door (closed, open, locked; hinge l or r; lower, upper; four sides),
                    BackroomsSuburbDoor; JSON
    l14-contamdoor  a contaminated room's steel door, a green glow through its wire glass, the trefoil; never opens
    l14-revolving   the reception's stained-glass revolving door, 3 wide, 2 deep, 3 high, nothing beyond it; JSON
    l14-firedoor    a hall's fire door leaf propped open against a wall (hinge l or r; lower, upper; four sides); JSON
    l14-hangsign    a department sign hung from the hall ceiling, its name on both faces (0-7; we, ns); JSON

Textures are 32 px a block (64 where they carry lettering), shapes 16 units; every JSON shape names its texture keys one
by one and its blocktype names no textures. Run from the repo root:  python tools/gen_14.py   (under tools/locked.sh run)
"""
import json
import math
import os
import random

from PIL import Image, ImageDraw

import sys

import matlib as M
import texlib
from modelkit import box, turn, move, textures as shape_keys, lever, kick_plate, hinge, inset_window, PX, DIRS, without
from gen_15 import SMALL, STONE, METAL, GLASS, CLOTH, WOOD, text as pixel_text
from gen_15_r3 import draw_text, font
import gen_14_r4 as R4

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "14")
SHAPES = os.path.join(ASSETS, "shapes", "block", "14")
BLOCKS = os.path.join(ASSETS, "blocktypes", "14")
S = 32
B = 64  # px a block for faces with lettering
SIDES = ["north", "east", "south", "west"]
ROTATE = {"north": 0, "east": 270, "south": 180, "west": 90}

# The palette (14-plan.md section 4)
MINT = (176, 206, 188)
TEAL = (98, 140, 128)
WHITE = (238, 240, 238)
CEIL = (214, 212, 202)
VINYL = (190, 198, 188)
RUST = (138, 72, 38)
BLOOD = (92, 10, 12)
MOULD = (66, 82, 40)
MOULD_DK = (34, 38, 30)
FRAME = (78, 104, 100)      # the doors' pressed-steel frames: a darker teal-grey
STAINLESS = (176, 182, 184)
INK = (26, 30, 32)
WAY_RED = (184, 40, 36)
SIGN_TEAL = (30, 74, 84)


# ======================================================================== Files

def write_json(path, data, comment=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    if comment:
        text = "// " + comment + "\n" + text
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")


def save(img, name):
    assert img.size[0] % 8 == 0 and img.size[1] % 8 == 0, name
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def load(name):
    return Image.open(os.path.join(TEX, name + ".png")).convert("RGBA")


def T(name):
    return "backrooms:block/14/" + name


def tex(name):
    return {"base": "block/14/" + name}


def shape(name, els):
    els = [{k: v for k, v in e.items() if not k.startswith("_")} for e in els]
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: T(k) for k in shape_keys(els)}, "elements": els}
    write_json(os.path.join(SHAPES, name + ".json"), data)
    return T(name)


# ======================================================================== Painting helpers

def rect(img, x0, y0, x1, y1, c, a=255):
    """Fills x0..x1, y0..y1 inclusive."""
    px = img.load()
    for y in range(max(0, y0), min(img.size[1], y1 + 1)):
        for x in range(max(0, x0), min(img.size[0], x1 + 1)):
            if a >= 255:
                px[x, y] = tuple(int(v) for v in c[:3]) + (255,)
            else:
                r, g, b, al = px[x, y]
                t = a / 255
                px[x, y] = (M.clamp(r + (c[0] - r) * t), M.clamp(g + (c[1] - g) * t), M.clamp(b + (c[2] - b) * t), al)


def blend(img, x, y, c, t):
    px = img.load()
    w, h = img.size
    x, y = x % w, y % h
    r, g, b, a = px[x, y]
    px[x, y] = (M.clamp(r + (c[0] - r) * t), M.clamp(g + (c[1] - g) * t), M.clamp(b + (c[2] - b) * t), a)


def art(img, box_, fn, k=4):
    """Draws with fn(draw, k, W, H) on a layer k times the size of box_ and shrinks it onto img: clean edges."""
    x0, y0, x1, y1 = box_
    layer = Image.new("RGBA", ((x1 - x0) * k, (y1 - y0) * k), (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer), k, layer.width, layer.height)
    layer = layer.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.alpha_composite(layer, (x0, y0))


def up2(img):
    return img.resize((img.width * 2, img.height * 2), Image.NEAREST)


def speckle(img, seed, density, colours, sizes=(1, 1, 1, 2)):
    """Chips of colour scattered over a surface (sheet vinyl, terrazzo), wrapping."""
    rng = random.Random(seed)
    w, h = img.size
    px = img.load()
    for _ in range(int(density * w * h)):
        x, y = rng.randrange(w), rng.randrange(h)
        c = rng.choice(colours)
        n = rng.choice(sizes)
        for dx in range(n):
            for dy in range(n if rng.random() < 0.5 else 1):
                r, g, b, a = px[(x + dx) % w, (y + dy) % h]
                k = rng.uniform(0.6, 0.95)
                px[(x + dx) % w, (y + dy) % h] = (M.clamp(r + (c[0] - r) * k), M.clamp(g + (c[1] - g) * k), M.clamp(b + (c[2] - b) * k), a)
    return img


def scuffs(img, seed, n, colour=(70, 72, 70), ys=None, length=(4, 12), strength=0.35):
    """Horizontal scrapes (trolleys, shoes, chair backs) at the heights given or anywhere."""
    rng = random.Random(seed)
    w, h = img.size
    for _ in range(n):
        y = rng.choice(ys) + rng.randint(-1, 1) if ys else rng.randrange(h)
        x = rng.randrange(w)
        L = rng.randint(*length)
        for k in range(L):
            t = strength * (1 - abs(k - L / 2) / (L / 2 + 1)) * rng.uniform(0.6, 1.0)
            blend(img, x + k, y + (k * rng.choice((0, 0, 0, 1)) // max(1, L)), colour, t)
    return img


def blotch(img, seed, at, radius, colour, strength=0.8, rough=0.5, fuzz=True, wrap=True):
    """An irregular blob (mould, blood, moss) round `at`, with a ragged edge; wrapping (unless wrap=False: for pictures)."""
    rng = random.Random(seed)
    w, h = img.size
    field = M.fbm((w, h), seed, (8, 4, 2))
    cx, cy = at
    for y in range(h):
        for x in range(w):
            dx, dy = abs(x - cx), abs(y - cy)
            if wrap:
                dx, dy = min(dx, w - dx), min(dy, h - dy)
            d = math.hypot(dx, dy) / radius
            v = d + (field[y][x] - 0.5) * rough * 2
            if v < 1:
                t = strength * min(1.0, (1 - v) * 3)
                if fuzz and v > 0.75 and rng.random() < 0.5:
                    continue
                blend(img, x, y, colour, t)
    return img


def mould_wall(seed):
    """Round 4: the mint paint with black mould growing on it in colonies: round spots of all sizes, each with a dark
    core, a sooty halo and a fringe of olive, crowding into patches and merging, the paint between them yellowed and
    damp-stained; seamless."""
    rng = random.Random(seed)
    img = paint(seed)
    M.tideline(img, 22, seed=seed + 1, color=(130, 132, 100), amount=0.25)
    M.grime(img, 0.18, seed=seed + 2, color=(150, 150, 110), cells=(16, 8), cover=0.6)
    px = img.load()
    # colonies cluster round a few centres
    centres = [(rng.randrange(S), rng.randrange(S)) for _ in range(3)]
    for _ in range(46):
        cx, cy = rng.choice(centres)
        x, y = cx + rng.gauss(0, 6), cy + rng.gauss(0, 6)
        r = rng.choice((0.6, 0.8, 1.0, 1.2, 1.6, 2.2, 3.0))
        for yy in range(int(y - r - 2), int(y + r + 3)):
            for xx in range(int(x - r - 2), int(x + r + 3)):
                d = math.hypot(xx - x, yy - y) / r
                X, Y = xx % S, yy % S
                if d < 0.55:
                    blend(img, X, Y, (22, 24, 20), 0.92)
                elif d < 1.0:
                    blend(img, X, Y, MOULD_DK, 0.75)
                elif d < 1.45 and rng.random() < 0.7:
                    blend(img, X, Y, MOULD, 0.4)
    speckle(img, seed + 3, 0.02, [MOULD_DK, (24, 26, 22)])
    return img


def seamless_runs(img, seed, n=3):
    """Round 4: old blood run down a wall from above, in runs that go the whole height and come back to where they
    started (so the block above and below carry them on), dried dark at the edges and darker where thick; a short run
    or two that stops in a bead, and a fine spatter."""
    rng = random.Random(seed)
    w, h = img.size
    xs = rng.sample(range(2, w - 3), n + 2)
    for i, x0 in enumerate(xs):
        full = i < n
        wd = rng.choice((1, 2, 2, 3)) if full else 1
        L = h if full else rng.randint(6, 14)
        y0 = 0 if full else rng.randint(0, 12)
        wander = [0.0]
        for k in range(1, L):
            wander.append(wander[-1] + rng.choice((0, 0, 0, 0.5, -0.5)))
        if full:  # come back to x0 at the bottom so it meets itself in the next block
            drift = wander[-1]
            wander = [v - drift * k / (L - 1) for k, v in enumerate(wander)]
        col = M.lift((84, 8, 10), rng.uniform(-10, 6))
        for k in range(L):
            fx = x0 + wander[k]
            for dx in range(wd):
                edge = dx in (0, wd - 1) and wd > 1
                blend(img, int(fx) + dx, (y0 + k) % h, M.lift(col, -14) if edge else col, 0.9 if not edge else 0.75)
        if not full:
            yb = (y0 + L) % h
            for dx in (-1, 0, 1):
                blend(img, int(x0 + wander[-1]) + dx, yb, M.lift(col, -18), 0.85)
    for _ in range(10):
        blend(img, rng.randrange(w), rng.randrange(h), (70, 8, 10), rng.uniform(0.5, 0.9))
    return img


def runs(img, seed, n, colour, start=(0, 6), length=(10, 30), width=(1, 2), strength=0.85, xs=None):
    """Thick liquid running down from the top: each run a wavering line, wider and darker at its head, a bead where it stops."""
    rng = random.Random(seed)
    w, h = img.size
    for i in range(n):
        x = xs[i % len(xs)] if xs else rng.randrange(w)
        y0 = rng.randint(*start)
        L = rng.randint(*length)
        wd = rng.randint(*width)
        fx = float(x)
        for k in range(L):
            y = y0 + k
            if y >= h:
                break
            fx += rng.choice((0, 0, 0, 0, 0.5, -0.5))
            t = strength * (1 - 0.35 * k / L)
            for dx in range(wd):
                blend(img, int(fx) + dx, y, colour, t)
        yb = min(h - 1, y0 + L)
        for dx in range(-1, wd + 1):
            blend(img, int(fx) + dx, yb, M.lift(colour, -10), strength)
        for dx in range(wd):
            blend(img, int(fx) + dx, yb + 1, M.lift(colour, -14), strength * 0.8)
    return img


def wire_mesh(img, box_, colour=(150, 156, 156), pitch=4, t=0.55):
    x0, y0, x1, y1 = box_
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x - x0) % pitch == 0 or (y - y0) % pitch == 0:
                blend(img, x, y, colour, t)


# ======================================================================== Wall textures

def paint(seed=14001):
    """The halls' mint paint: an eggshell over plaster, broad soft clouds, a faint roller stipple, the dirt of years low
    in its colour and a few small marks."""
    img = M.plaster(seed=seed, base=MINT, grain=2, mottle=5, roller=0.35)
    M.grime(img, 0.07, seed=seed + 1, color=(132, 140, 118), cells=(16, 8), cover=0.55)
    M.drips(img, n=2, seed=seed + 2, color=(150, 160, 134), length=(6, 18), strength=0.12)
    scuffs(img, seed + 3, 2, colour=(120, 128, 118), length=(2, 4), strength=0.2)
    return img


def wall_textures():
    save(paint(), "wall-paint")
    # Scuffed: a trolley's scrape and shoe marks low, chipped paint showing the plaster, a grey handprint smudge, a water stain
    sc = paint(14002)
    scuffs(sc, 14003, 7, colour=(64, 70, 66), ys=(22, 25, 28), length=(5, 14), strength=0.45)
    scuffs(sc, 14004, 3, colour=(96, 100, 92), length=(3, 7), strength=0.3)
    rng = random.Random(14005)
    for _ in range(3):
        x, y = rng.randrange(S), rng.randrange(S)
        for dx, dy in ((0, 0), (1, 0), (0, 1), (2, 0))[:rng.randint(2, 4)]:
            blend(sc, x + dx, y + dy, (214, 220, 204), 0.6)
            blend(sc, x + dx, y + dy + 1, (120, 130, 116), 0.3)
    M.stain(sc, seed=14006, radius=7, color=(150, 146, 112), strength=0.25, at=(9, 9), ring=0.6)
    save(sc, "wall-paintscuff")
    # The wainscot: teal-green semi-gloss, a dado trim along its top (where the mint starts), a stainless kick strip at
    # the foot, scuffed by trolleys and shoes, dirt gathered low
    wb = M.plaster(seed=14010, base=TEAL, grain=2, mottle=4, roller=0.2)
    rect(wb, 0, 0, S - 1, 1, M.lift(TEAL, -16))
    rect(wb, 0, 2, S - 1, 2, M.lift(TEAL, 14))
    rect(wb, 0, 3, S - 1, 3, M.lift(TEAL, -8))
    steel = M.brushed_metal(seed=14011, base=STAINLESS, direction="h", streak=5, sheen=6)
    sp, px = steel.load(), wb.load()
    for y in range(26, S):
        for x in range(S):
            px[x, y] = sp[x, y]
    M.emboss_lines(wb, ys=(26,), raised=True, strength=0.25)
    for x in (4, 20):
        M.screw(wb, x, 28, slot=False)
    scuffs(wb, 14012, 8, colour=(46, 60, 56), ys=(8, 14, 20, 24), length=(4, 12), strength=0.45)
    M.scratches(wb, n=5, seed=14013, light=0.18, angle=0)
    M.grime(wb, 0.16, seed=14014, bias="bottom", color=(60, 62, 52))
    save(wb, "wall-paintbase")
    # The inpatient units' white: hardly a mark on it
    wh = M.plaster(seed=14020, base=WHITE, grain=1, mottle=2, roller=0.15)
    save(wh, "wall-white")
    whb = wh.copy()
    cove = M.plaster(seed=14021, base=(208, 212, 210), grain=1, mottle=2, roller=0.0)
    cp, px = cove.load(), whb.load()
    for y in range(27, S):
        for x in range(S):
            px[x, y] = cp[x, y]
    M.emboss_lines(whb, ys=(27,), raised=True, strength=0.2)
    M.grime(whb, 0.05, seed=14022, bias="bottom", color=(170, 172, 164))
    save(whb, "wall-whitebase")
    # White ceramic wall tile; its foot a band of pale green tiles, grimy
    def walltile(seed):
        # round 4: flat glazed tiles (a soft highlight, hardly a tilt), pale grout, fine crazing and a little dirt in the joints
        rng = random.Random(seed)
        img = M.noise_hv((228, 232, 230), 1.5, seed, S, 2, (16, 8))
        px = img.load()
        for ty in range(4):
            for tx in range(4):
                v = rng.uniform(-2.5, 2.5)
                for y in range(ty * 8, ty * 8 + 7):
                    for x in range(tx * 8, tx * 8 + 7):
                        M.touch(img, x, y, v / 100)
                M.touch(img, tx * 8 + 1, ty * 8 + 1, 0.06)
                M.touch(img, tx * 8 + 2, ty * 8 + 1, 0.04)
                for x in range(tx * 8, tx * 8 + 7):
                    M.touch(img, x, ty * 8 + 6, -0.03)
        for i in range(S):
            for j in range(S):
                if i % 8 == 7 or j % 8 == 7:
                    px[i, j] = M.rgba(M.lift((196, 200, 196), rng.uniform(-4, 3)))
        for k in range(3):
            M.crack(img, seed + 20 + k, length=(3, 6), strength=0.08)
        M.grime(img, 0.05, seed=seed + 7, color=(150, 150, 136), cells=(8, 4), cover=0.4)
        return img
    save(walltile(14030), "wall-tile")
    tb = walltile(14031)
    band = M.tile(seed=14032, base=(150, 190, 174), grout=(132, 158, 148), pitch=8, grout_w=1, jitter=3, uneven=1)
    bp, px = band.load(), tb.load()
    for y in range(24, S):
        for x in range(S):
            px[x, y] = bp[x, y]
    M.grime(tb, 0.14, seed=14033, bias="bottom", color=(96, 98, 84))
    save(tb, "wall-tilebase")
    # The behaviour cells (round 4): button-tufted vinyl padding in a diamond lattice: a button sunk at each point, the
    # padding puffed up between them, creases running button to button, grubby where hands and heads have been
    pad = M.fabric(seed=14040, base=(224, 222, 210), weave="plain", contrast=3, mottle=3)
    buttons = [(x, y) for y in range(0, S + 1, 8) for x in range(0 if (y // 8) % 2 == 0 else 8, S + 1, 16)]
    for y in range(S):
        for x in range(S):
            d = min(math.hypot(x - bx, y - by) for bx, by in buttons)
            f = 0.09 * min(1.0, d / 6.0) - 0.05
            f += 0.03 * (0.5 - (y % 8) / 8.0)
            M.touch(pad, x, y, f)
    for bx, by in buttons:
        for dx, dy in ((0, 0), (-1, 0), (0, -1), (-1, -1)):
            blend(pad, bx + dx, by + dy, (128, 124, 112), 0.75)
        for k in range(1, 5):
            for sx, sy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                blend(pad, bx + sx * k, by + sy * k, (176, 172, 160), 0.3 * (1 - k / 5))
    M.grime(pad, 0.12, seed=14041, color=(160, 150, 120), cells=(16, 8), cover=0.45)
    M.stain(pad, seed=14042, radius=5, color=(170, 150, 110), strength=0.25, at=(22, 20))
    save(pad, "wall-padded")
    # Painted cinderblock: blocks 16 x 8, the paint a pale grey-green thick over their pores
    cin = M.brick(seed=14050, base=(170, 184, 172), mortar=(158, 170, 160), course=8, length=16, offset=0.5, jitter=3, hue=0,
                  recess=0.7, pits=0.025, grain=3, mottle=4)
    M.grime(cin, 0.08, seed=14051, color=(110, 116, 100))
    save(cin, "wall-cinder")
    # Patched plywood: two sheets, a third nailed over a hole at an angle to the grain, screws, damp at the foot
    ply = M.wood_planks(seed=14060, base=(176, 142, 100), planks=2, direction="v", grain=3, contrast=0.6, flecks=0.6, per_plank=12)
    patch = M.wood_planks(seed=14061, base=(150, 118, 80), planks=1, direction="h", grain=3, contrast=0.6, flecks=0.6)
    pp, px = patch.load(), ply.load()
    for y in range(9, 22):
        for x in range(5, 23):
            px[x, y] = pp[x, y]
    M.bevel(ply, (5, 9, 23, 22), strength=0.25)
    for sx, sy in ((6, 10), (21, 10), (6, 20), (21, 20), (13, 10), (13, 20)):
        blend(ply, sx, sy, (60, 56, 50), 0.9)
    for sy in (2, 14, 27):
        for sx in (1, 17):
            blend(ply, sx, sy, (70, 64, 56), 0.8)
    M.tideline(ply, 25, seed=14062, color=(96, 76, 52), amount=0.35)
    save(ply, "wall-plywood")
    # Corroded steel plate
    rs = M.riveted_plate(seed=14070, base=(96, 80, 68), pitch=4, layout="edges", rust_amount=0.4)
    M.rust(rs, 0.82, seed=14071, color=RUST)
    M.drips(rs, n=4, seed=14072, color=(96, 50, 28), length=(8, 24), strength=0.4)
    save(rs, "wall-rust")
    rb = rs.copy()
    seamless_runs(rb, 14073, n=1)
    save(rb, "wall-rustblood")
    # Filthy tiles, cracked, blood run down them from the top
    tbl = walltile(14080)
    M.grime(tbl, 0.32, seed=14081, color=(150, 140, 96), cells=(8, 4, 2), cover=0.7)
    for k in range(3):
        M.crack(tbl, 14082 + k, length=(6, 14), strength=0.3)
    seamless_runs(tbl, 14085, n=1)
    save(tbl, "wall-tileblood")
    # Mould: the mint gone black and green in blooms, a damp tide below
    save(mould_wall(14090), "wall-mould")
    # White with moss creeping up from the foot, and a rust run from a fixing
    wm = M.plaster(seed=14100, base=WHITE, grain=1, mottle=2, roller=0.15)
    M.grime(wm, 0.55, seed=14101, bias="bottom", color=MOULD, cells=(8, 4, 2), cover=0.5)
    rng = random.Random(14102)
    for _ in range(70):
        x = rng.randrange(S)
        y = S - 1 - int(abs(rng.gauss(0, 7)))
        if 0 <= y < S:
            blend(wm, x, y, rng.choice((MOULD, (84, 102, 48), MOULD_DK)), rng.uniform(0.5, 0.9))
    M.drips(wm, n=1, seed=14103, color=RUST, length=(8, 14), strength=0.45, start=4)
    save(wm, "wall-whitemoss")
    # Bare concrete
    save(M.concrete(seed=14110, base=(146, 146, 140), grain=4, mottle=6, aggregate=0.05, joints=(16,), patches=3), "wall-concrete")
    # A doorway's frame head: the pressed-steel head of the frame along the foot, the mint over it
    li = paint(14120)
    fr = M.painted_metal(seed=14121, base=FRAME, panel=False, chips=3)
    fp, px = fr.load(), li.load()
    for y in range(22, S):
        for x in range(S):
            px[x, y] = fp[x, y]
    M.emboss_lines(li, ys=(22,), raised=True, strength=0.3)
    M.emboss_lines(li, ys=(26,), strength=0.2)
    save(li, "wall-lintel")


# ======================================================================== Wall decorations (64 px, one face)

def deco_base():
    return up2(load("wall-paint"))


def plate(img, box_, bg, fg, name, tab=None, size=9):
    x0, y0, x1, y1 = box_
    rect(img, x0 - 1, y0 - 1, x1 + 1, y1 + 1, (70, 76, 74))
    rect(img, x0, y0, x1, y1, bg)
    M.bevel(img, (x0, y0, x1 + 1, y1 + 1), strength=0.18)
    tx0 = x0 + 2
    if tab:
        rect(img, x0, y0, x0 + 4, y1, tab)
        tx0 = x0 + 6
    draw_text(img, (tx0, y0 + 2, x1 - 1, y1 - 1), name, fg, size, condensed=True)
    for sx, sy in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1)):
        blend(img, sx, sy, (120, 124, 120), 0.6)


def trefoil(d, cx, cy, r, colour, k=1, kind="radiation"):
    """The radiation trefoil (three blades round a dot) or the biohazard's three hooked rings, drawn on a layer."""
    if kind == "radiation":
        for a in (90, 210, 330):
            d.pieslice([cx - r, cy - r, cx + r, cy + r], a - 30, a + 30, fill=colour)
        d.ellipse([cx - r * 0.42, cy - r * 0.42, cx + r * 0.42, cy + r * 0.42], fill=(0, 0, 0, 0))
        d.ellipse([cx - r * 0.25, cy - r * 0.25, cx + r * 0.25, cy + r * 0.25], fill=colour)
    else:
        # the biohazard symbol (round 4): three crescents open outward round a ring, cut through at the middle
        clear = (0, 0, 0, 0)

        def disc(a, dist, rad, fill):
            ox, oy = cx + dist * math.cos(math.radians(a)), cy + dist * math.sin(math.radians(a))
            d.ellipse([ox - rad, oy - rad, ox + rad, oy + rad], fill=fill)
        for a in (-90, 30, 150):
            disc(a, r * 0.46, r * 0.54, colour)
        for a in (-90, 30, 150):
            disc(a, r * 0.62, r * 0.38, clear)
        d.ellipse([cx - r * 0.36, cy - r * 0.36, cx + r * 0.36, cy + r * 0.36], outline=colour, width=max(1, int(r * 0.1)))
        d.ellipse([cx - r * 0.15, cy - r * 0.15, cx + r * 0.15, cy + r * 0.15], fill=clear)
        for a in (90, 210, 330):
            ex, ey = cx + r * 0.42 * math.cos(math.radians(a)), cy + r * 0.42 * math.sin(math.radians(a))
            d.line([cx, cy, ex, ey], fill=clear, width=max(1, int(r * 0.07)))


PLATES = [("ward", "WARD", (60, 120, 170)), ("icu", "INTENSIVE\nCARE", (180, 60, 50)), ("surgery", "SURGERY", (60, 140, 110)),
          ("maternity", "MATERNITY", (210, 120, 150)), ("psych", "PSYCHIATRY", (130, 100, 170)), ("storage", "STORAGE", (150, 140, 110)),
          ("reception", "RECEPTION", (70, 150, 160)), ("office", "OFFICE", (120, 124, 128)), ("research", "RESEARCH", (90, 110, 70)),
          ("danger", None, None), ("biohazard", None, None)]
SIGNS = ["WARD 1", "INTENSIVE CARE", "SURGERY", "MATERNITY", "PSYCHIATRY", "STORES", "RECEPTION", "OUTPATIENTS"]


def sign_face(w, h, name, seed, arrow=True):
    """A department sign (w x h px): deep teal enamel, an off-white rim, the name in white, an arrow to the right; old."""
    img = M.painted_metal(seed=seed, size=(-(-w // 8) * 8, -(-h // 8) * 8), base=SIGN_TEAL, panel=False, chips=0).crop((0, 0, w, h))
    rect(img, 0, 0, w - 1, 0, (210, 214, 206))
    rect(img, 0, h - 1, w - 1, h - 1, (210, 214, 206))
    rect(img, 0, 0, 0, h - 1, (210, 214, 206))
    rect(img, w - 1, 0, w - 1, h - 1, (210, 214, 206))
    aw = int(h * 0.75) if arrow else 0
    lines = name.replace(" CARE", "\nCARE") if len(name) > 10 else name
    draw_text(img, (3, 2, w - aw - 3, h - 2), lines, (236, 238, 230), int(h * 0.42), condensed=True)
    if arrow:
        def a(d, k, W, H):
            m = H * 0.5
            d.polygon([(W * 0.1, m - H * 0.12), (W * 0.5, m - H * 0.12), (W * 0.5, m - H * 0.3), (W * 0.92, m), (W * 0.5, m + H * 0.3),
                       (W * 0.5, m + H * 0.12), (W * 0.1, m + H * 0.12)], fill=(236, 238, 230, 255))
        art(img, (w - aw - 2, 2, w - 2, h - 2), a)
    M.grime(img, 0.12, seed=seed + 1, color=(40, 44, 36), cells=(8, 4))
    M.scratches(img, n=3, seed=seed + 2, light=0.15)
    return img


def deco_textures():
    # Room plates by the doors, at eye height
    for code, name, tab in PLATES:
        img = deco_base()
        if code == "danger":
            rect(img, 13, 18, 50, 45, (30, 30, 30))
            rect(img, 14, 19, 49, 44, (236, 214, 60))
            rect(img, 14, 19, 49, 29, (196, 30, 28))
            draw_text(img, (15, 20, 49, 29), "DANGER", (250, 246, 236), 8)
            draw_text(img, (15, 31, 49, 43), "KEEP\nOUT", (24, 24, 24), 6, condensed=True)
        elif code == "biohazard":
            rect(img, 16, 14, 47, 49, (30, 30, 30))
            rect(img, 17, 15, 46, 48, (238, 200, 40))
            art(img, (19, 16, 45, 40), lambda d, k, W, H: trefoil(d, W / 2, H / 2 + k, H * 0.4, (20, 20, 20, 255), k, "bio"))
            draw_text(img, (18, 40, 46, 47), "BIOHAZARD", (20, 20, 20), 6, condensed=True)
        else:
            plate(img, (10, 22, 53, 40), (232, 230, 220), INK, name, tab=tab, size=9 if "\n" not in name else 7)
        M.grime(img, 0.05, seed=14200 + len(code), color=(110, 110, 96), cells=(8, 4))
        save(img, "deco-plate-" + code)
    # The halls' department signs, with an arrow
    for n, name in enumerate(SIGNS):
        img = deco_base()
        sg = sign_face(56, 24, name, 14210 + n)
        rect(img, 3, 19, 60, 44, (60, 64, 62))
        img.alpha_composite(sg, (4, 20))
        save(img, f"deco-sign-{n}")
    # Children's posters: crayon animals, a smiling sun, a cartoon doctor; on paper taped up, curling, faded
    def paper(img, x0, y0, x1, y1, seed):
        rect(img, x0 + 1, y0 + 1, x1 + 1, y1 + 1, (110, 120, 110), 120)
        rect(img, x0, y0, x1, y1, (238, 234, 222))
        for (tx, ty) in ((x0 - 1, y0 - 1), (x1 - 3, y0 - 1)):
            rect(img, tx, ty, tx + 4, ty + 2, (226, 220, 180), 200)
    for n in range(3):
        img = deco_base()
        paper(img, 10, 8, 54, 56, 14220 + n)
        if n == 0:
            def kid(d, k, W, H):
                lw = 2 * k
                d.line([(0, H * 0.82), (W, H * 0.8)], fill=(60, 170, 60, 255), width=3 * k)
                # A dog: body, head, ears, legs, tail
                d.ellipse([W * 0.12, H * 0.5, W * 0.55, H * 0.7], outline=(150, 90, 40, 255), width=lw, fill=(200, 140, 70, 255))
                d.ellipse([W * 0.48, H * 0.36, W * 0.7, H * 0.56], outline=(150, 90, 40, 255), width=lw, fill=(200, 140, 70, 255))
                for lx in (0.18, 0.28, 0.4, 0.5):
                    d.line([(W * lx, H * 0.66), (W * lx, H * 0.8)], fill=(150, 90, 40, 255), width=lw)
                d.line([(W * 0.13, H * 0.56), (W * 0.04, H * 0.46)], fill=(150, 90, 40, 255), width=lw)
                d.ellipse([W * 0.6, H * 0.42, W * 0.64, H * 0.46], fill=(20, 20, 20, 255))
                # A blue bird and a cat's head
                d.arc([W * 0.55, H * 0.1, W * 0.7, H * 0.2], 200, 340, fill=(40, 80, 200, 255), width=lw)
                d.arc([W * 0.68, H * 0.1, W * 0.83, H * 0.2], 200, 340, fill=(40, 80, 200, 255), width=lw)
                d.ellipse([W * 0.12, H * 0.12, W * 0.38, H * 0.36], outline=(230, 120, 30, 255), width=lw)
                d.polygon([(W * 0.14, H * 0.16), (W * 0.17, H * 0.06), (W * 0.22, H * 0.13)], fill=(230, 120, 30, 255))
                d.polygon([(W * 0.36, H * 0.16), (W * 0.33, H * 0.06), (W * 0.28, H * 0.13)], fill=(230, 120, 30, 255))
                d.ellipse([W * 0.75, H * 0.62, W * 0.95, H * 0.8], outline=(200, 40, 140, 255), width=lw)
            art(img, (12, 12, 52, 54), kid)
            draw_text(img, (12, 47, 52, 55), "MY PETS", (60, 60, 200), 5)
        elif n == 1:
            def sun(d, k, W, H):
                cx, cy, r = W / 2, H * 0.42, W * 0.22
                for i in range(12):
                    a = i * math.pi / 6
                    d.line([(cx + r * 1.2 * math.cos(a), cy + r * 1.2 * math.sin(a)), (cx + r * 1.75 * math.cos(a), cy + r * 1.75 * math.sin(a))],
                           fill=(250, 170, 20, 255), width=2 * k)
                d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(252, 220, 40, 255), outline=(240, 150, 20, 255), width=2 * k)
                d.ellipse([cx - r * 0.45, cy - r * 0.3, cx - r * 0.2, cy - r * 0.05], fill=(30, 30, 30, 255))
                d.ellipse([cx + r * 0.2, cy - r * 0.3, cx + r * 0.45, cy - r * 0.05], fill=(30, 30, 30, 255))
                d.arc([cx - r * 0.55, cy - r * 0.4, cx + r * 0.55, cy + r * 0.6], 30, 150, fill=(200, 40, 30, 255), width=2 * k)
            art(img, (12, 10, 52, 46), sun)
            draw_text(img, (12, 44, 52, 54), "GET WELL\nSOON", (220, 50, 40), 4)
        else:
            def doc(d, k, W, H):
                cx = W / 2
                d.ellipse([cx - W * 0.13, H * 0.06, cx + W * 0.13, H * 0.3], fill=(244, 200, 160, 255), outline=(120, 70, 40, 255), width=k)
                d.ellipse([cx - W * 0.07, H * 0.14, cx - W * 0.03, H * 0.18], fill=(20, 20, 20, 255))
                d.ellipse([cx + W * 0.03, H * 0.14, cx + W * 0.07, H * 0.18], fill=(20, 20, 20, 255))
                d.arc([cx - W * 0.07, H * 0.15, cx + W * 0.07, H * 0.26], 20, 160, fill=(180, 40, 30, 255), width=k)
                d.polygon([(cx - W * 0.25, H * 0.32), (cx + W * 0.25, H * 0.32), (cx + W * 0.3, H * 0.8), (cx - W * 0.3, H * 0.8)],
                          fill=(250, 250, 250, 255), outline=(90, 90, 120, 255))
                d.line([(cx - W * 0.1, H * 0.33), (cx - W * 0.12, H * 0.55), (cx + W * 0.02, H * 0.6)], fill=(40, 40, 40, 255), width=k)
                d.ellipse([cx, H * 0.57, cx + W * 0.06, H * 0.63], fill=(150, 150, 160, 255))
                d.rectangle([cx + W * 0.08, H * 0.4, cx + W * 0.2, H * 0.44], fill=(220, 30, 30, 255))
                d.rectangle([cx + W * 0.12, H * 0.36, cx + W * 0.16, H * 0.48], fill=(220, 30, 30, 255))
                for lx in (-0.12, 0.08):
                    d.line([(cx + W * lx, H * 0.8), (cx + W * lx, H * 0.95)], fill=(40, 60, 140, 255), width=2 * k)
                for s in (-1, 1):
                    d.line([(cx + s * W * 0.25, H * 0.36), (cx + s * W * 0.4, H * 0.55)], fill=(250, 250, 250, 255), width=3 * k)
            art(img, (12, 12, 52, 52), doc)
            draw_text(img, (12, 50, 52, 56), "DR. FRIEND", (40, 120, 60), 4)
        M.grime(img, 0.08, seed=14230 + n, color=(170, 160, 120), cells=(8, 4))
        save(img, f"deco-poster-kid{n}")
    # Health posters: WASH YOUR HANDS; a faded anatomy chart
    img = deco_base()
    rect(img, 12, 6, 52, 58, (40, 50, 60))
    rect(img, 13, 7, 51, 57, (240, 242, 238))
    rect(img, 13, 7, 51, 18, (36, 110, 180))
    draw_text(img, (14, 8, 51, 18), "WASH YOUR\nHANDS", (250, 250, 250), 5, condensed=True)
    def hands(d, k, W, H):
        for s in (-1, 1):
            cx = W / 2 + s * W * 0.17
            d.rounded_rectangle([cx - W * 0.13, H * 0.35, cx + W * 0.13, H * 0.85], radius=W * 0.06, fill=(240, 196, 160, 255), outline=(150, 100, 70, 255), width=k)
            for f in range(4):
                fx = cx - W * 0.11 + f * W * 0.06
                d.rounded_rectangle([fx, H * 0.12 + abs(f - 1.5) * H * 0.04, fx + W * 0.045, H * 0.4], radius=W * 0.02, fill=(240, 196, 160, 255),
                                    outline=(150, 100, 70, 255), width=k)
        for i in range(5):
            x, y = W * (0.2 + 0.15 * i), H * (0.05 + 0.04 * (i % 2))
            d.ellipse([x, y, x + W * 0.06, y + H * 0.09], fill=(80, 160, 230, 255))
    art(img, (16, 20, 48, 48), hands)
    draw_text(img, (14, 49, 51, 56), "20 SECONDS - EVERY TIME", (36, 110, 180), 3, condensed=True)
    M.grime(img, 0.1, seed=14240, color=(170, 160, 120), cells=(8, 4))
    save(img, "deco-poster-health0")
    img = deco_base()
    rect(img, 10, 4, 54, 60, (60, 56, 48))
    rect(img, 11, 5, 53, 59, (222, 210, 182))
    def body(d, k, W, H):
        cx = W / 2
        ol = (120, 96, 80, 255)
        d.ellipse([cx - W * 0.1, H * 0.02, cx + W * 0.1, H * 0.15], outline=ol, width=k)
        d.polygon([(cx - W * 0.2, H * 0.18), (cx + W * 0.2, H * 0.18), (cx + W * 0.15, H * 0.55), (cx - W * 0.15, H * 0.55)], outline=ol)
        for s in (-1, 1):
            d.line([(cx + s * W * 0.2, H * 0.19), (cx + s * W * 0.32, H * 0.52)], fill=ol, width=k)
            d.line([(cx + s * W * 0.1, H * 0.55), (cx + s * W * 0.12, H * 0.97)], fill=ol, width=k)
            d.ellipse([cx + s * W * 0.02 - W * 0.07, H * 0.22, cx + s * W * 0.02 + W * 0.07, H * 0.36], fill=(196, 140, 140, 255))
        d.ellipse([cx - W * 0.04, H * 0.24, cx + W * 0.06, H * 0.33], fill=(170, 60, 60, 255))
        d.ellipse([cx - W * 0.12, H * 0.36, cx + W * 0.1, H * 0.44], fill=(170, 110, 80, 255))
        d.rectangle([cx - W * 0.1, H * 0.44, cx + W * 0.1, H * 0.53], fill=(200, 160, 130, 255))
        d.line([(cx, H * 0.2), (cx, H * 0.95)], fill=(90, 110, 170, 200), width=k)
        for i in range(6):
            y = H * (0.1 + 0.14 * i)
            d.line([(cx + W * 0.2, y), (W * 0.92, y)], fill=(90, 80, 70, 255), width=1)
            d.line([(W * 0.08, y + H * 0.05), (cx - W * 0.2, y + H * 0.05)], fill=(90, 80, 70, 255), width=1)
    art(img, (12, 6, 52, 58), body)
    # Faded and water-stained
    px = img.load()
    for y in range(5, 60):
        for x in range(11, 54):
            r, g, b, a = px[x, y]
            l = (r + g + b) / 3
            px[x, y] = (M.clamp(r * 0.55 + l * 0.45 + 8), M.clamp(g * 0.55 + l * 0.45 + 4), M.clamp(b * 0.55 + l * 0.45 - 6), a)
    M.stain(img, seed=14241, radius=12, color=(170, 140, 90), strength=0.35, at=(40, 48), ring=0.7)
    save(img, "deco-poster-health1")
    # A wall clock, stopped at 3:47, its glass cracked
    img = deco_base()
    def clock(d, k, W, H):
        cx, cy, r = W / 2, H / 2, W * 0.46
        d.ellipse([cx - r - k, cy - r + k, cx + r + k, cy + r + 2 * k], fill=(60, 70, 66, 160))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(30, 32, 34, 255))
        d.ellipse([cx - r * 0.88, cy - r * 0.88, cx + r * 0.88, cy + r * 0.88], fill=(236, 234, 222, 255))
        for i in range(60):
            a = i * math.pi / 30
            L = 0.14 if i % 5 == 0 else 0.06
            d.line([(cx + r * 0.84 * math.sin(a), cy - r * 0.84 * math.cos(a)), (cx + r * (0.84 - L) * math.sin(a), cy - r * (0.84 - L) * math.cos(a))],
                   fill=(30, 30, 30, 255), width=max(1, k if i % 5 == 0 else k // 2))
        for a_deg, L, wd in ((3 * 30 + 47 * 0.5, 0.45, 3 * k), (47 * 6, 0.7, 2 * k)):
            a = math.radians(a_deg)
            d.line([(cx, cy), (cx + r * L * math.sin(a), cy - r * L * math.cos(a))], fill=(20, 20, 20, 255), width=wd)
        a = math.radians(122)
        d.line([(cx - r * 0.15 * math.sin(a), cy + r * 0.15 * math.cos(a)), (cx + r * 0.75 * math.sin(a), cy - r * 0.75 * math.cos(a))], fill=(190, 30, 30, 255), width=k)
        d.ellipse([cx - 2 * k, cy - 2 * k, cx + 2 * k, cy + 2 * k], fill=(20, 20, 20, 255))
        d.line([(cx - r * 0.6, cy - r * 0.5), (cx - r * 0.1, cy - r * 0.05), (cx + r * 0.2, cy + r * 0.5)], fill=(255, 255, 255, 150), width=k)
        d.line([(cx - r * 0.1, cy - r * 0.05), (cx - r * 0.55, cy + r * 0.3)], fill=(255, 255, 255, 120), width=k)
    art(img, (14, 10, 50, 46), clock)
    save(img, "deco-clock")
    # The ward whiteboard: an aluminium frame, ruled into BED / PATIENT / NURSE, names in marker, one crossed out in red
    img = deco_base()
    rect(img, 4, 10, 59, 52, (160, 166, 168))
    M.bevel(img, (4, 10, 60, 53), strength=0.25)
    rect(img, 6, 12, 57, 50, (240, 242, 240))
    rect(img, 6, 12, 57, 17, (36, 90, 150))
    draw_text(img, (7, 12, 15, 17), "BED", (240, 240, 240), 4, condensed=True)
    names = [("1", "WILLIAMS", (30, 60, 140)), ("2", "AFTON", (30, 30, 30)), ("3", "", None), ("4", "MOSS", (30, 60, 140)), ("5", "", None)]
    for i, (bed, nm, col) in enumerate(names):
        y = 20 + i * 6
        rect(img, 6, y + 5, 57, y + 5, (190, 196, 200))
        draw_text(img, (7, y, 14, y + 5), bed, (40, 40, 40), 5)
        if nm:
            draw_text(img, (17, y, 46, y + 5), nm, col, 5, condensed=True)
    for x in range(16, 48):
        blend(img, x, 28 + (x % 3 == 0), (200, 30, 30), 0.85)
    draw_text(img, (47, 25, 57, 31), "?", (200, 30, 30), 5)
    rect(img, 15, 18, 15, 49, (190, 196, 200))
    M.stain(img, seed=14250, radius=8, color=(170, 176, 186), strength=0.3, at=(44, 42), ring=0.2)
    rect(img, 22, 13, 40, 16, (36, 90, 150))
    draw_text(img, (20, 12, 46, 17), "PATIENT", (240, 240, 240), 4, condensed=True)
    rect(img, 8, 51, 56, 52, (130, 134, 136))
    rect(img, 40, 50, 46, 50, (40, 40, 160))
    save(img, "deco-whiteboard")
    # The X-ray light box, lit: a cold white panel, the film of a chest on it (the ribs, the spine, a dark shape in the lung)
    img = deco_base()
    rect(img, 6, 6, 57, 57, (200, 204, 206))
    M.bevel(img, (6, 6, 58, 58), strength=0.25)
    rect(img, 9, 9, 54, 54, (232, 244, 252))
    rect(img, 15, 11, 48, 52, (22, 26, 34))
    def xray(d, k, W, H):
        cx = W / 2
        bone = (210, 220, 228, 255)
        d.rectangle([cx - W * 0.03, H * 0.02, cx + W * 0.03, H * 0.98], fill=(150, 160, 170, 255))
        for i in range(8):
            y = H * (0.12 + i * 0.1)
            for s in (-1, 1):
                d.arc([cx - W * 0.42 if s < 0 else cx - W * 0.02, y, cx + W * 0.02 if s < 0 else cx + W * 0.42, y + H * 0.18],
                      200 if s < 0 else 270, 270 if s < 0 else 340, fill=bone, width=2 * k)
        d.line([(cx - W * 0.4, H * 0.08), (cx - W * 0.05, H * 0.12)], fill=bone, width=3 * k)
        d.line([(cx + W * 0.4, H * 0.08), (cx + W * 0.05, H * 0.12)], fill=bone, width=3 * k)
        d.ellipse([cx + W * 0.1, H * 0.45, cx + W * 0.3, H * 0.68], fill=(8, 8, 10, 255))
    art(img, (15, 11, 49, 53), xray)
    save(img, "deco-xray")
    # Blood: a smear at hand height, dragged sideways from a hand; blood running down from above
    img = deco_base()
    rng = random.Random(14260)
    for i in range(5):
        y0 = 24 + i * 3 + rng.randint(-1, 1)
        L = rng.randint(22, 36)
        for k in range(L):
            for w_ in range(3):
                blend(img, 12 + k, y0 + w_ + (k // 9), BLOOD, 0.85 * (1 - k / L) ** 0.6)
    art(img, (6, 18, 22, 40), lambda d, k, W, H: (d.ellipse([W * 0.2, H * 0.3, W * 0.85, H * 0.85], fill=(96, 12, 14, 230)),
                                                  [d.rounded_rectangle([W * (0.15 + 0.15 * f), H * 0.02 + abs(f - 1.5) * H * 0.05,
                                                                        W * (0.25 + 0.15 * f), H * 0.42], radius=W * 0.05, fill=(96, 12, 14, 230))
                                                   for f in range(4)]))
    runs(img, 14261, 4, BLOOD, start=(36, 40), length=(6, 18), width=(1, 2), strength=0.8)
    save(img, "deco-blood")
    img = deco_base()
    runs(img, 14262, 9, BLOOD, start=(0, 2), length=(20, 62), width=(1, 3), strength=0.9)
    blotch(img, 14263, (30, 0), 14, (74, 6, 8), 0.85, wrap=False)
    save(img, "deco-blooddrip")
    # A mould bloom: a black-green heart, a fuzzy ring, yellowed paint round it
    img = deco_base()
    blotch(img, 14270, (30, 34), 26, (150, 146, 96), 0.35, rough=0.4, wrap=False)
    blotch(img, 14271, (30, 34), 19, MOULD, 0.85, rough=0.5, wrap=False)
    blotch(img, 14272, (28, 36), 12, MOULD_DK, 0.95, rough=0.6, wrap=False)
    speckle(img, 14273, 0.04, [MOULD_DK, MOULD, (90, 110, 50)], sizes=(1, 1, 2))
    save(img, "deco-mould")
    # Scratches: fingernails dragged down the paint in fours, the plaster white in the gouges
    img = deco_base()
    rng = random.Random(14280)
    for g in range(3):
        x0, y0 = rng.randint(6, 40), rng.randint(4, 20)
        L, slope = rng.randint(22, 36), rng.uniform(-0.25, 0.25)
        for f in range(4):
            for k in range(int(L - abs(f - 1.5) * 3)):
                x = int(x0 + f * 3 + k * slope)
                y = int(y0 + k + abs(f - 1.5) * 2)
                blend(img, x, y, (232, 232, 222), 0.9)
                blend(img, x + 1, y, (70, 80, 72), 0.6)
        if g == 0:
            runs(img, 14281, 2, BLOOD, start=(y0 + L - 6, y0 + L - 2), length=(4, 9), width=(1, 1), strength=0.7, xs=(x0 + 3, x0 + 9))
    save(img, "deco-scratches")
    # The green running man over a doorway, lit
    img = deco_base()
    rect(img, 4, 18, 59, 45, (226, 230, 226))
    M.bevel(img, (4, 18, 60, 46), strength=0.25)
    rect(img, 6, 20, 57, 43, (30, 168, 84))
    def man(d, k, W, H):
        g = (240, 255, 244, 255)
        d.rectangle([W * 0.04, H * 0.1, W * 0.3, H * 0.9], outline=g, width=2 * k)
        d.ellipse([W * 0.44, H * 0.06, W * 0.54, H * 0.26], fill=g)
        d.line([(W * 0.47, H * 0.3), (W * 0.41, H * 0.62)], fill=g, width=4 * k)
        d.line([(W * 0.46, H * 0.36), (W * 0.58, H * 0.5)], fill=g, width=3 * k)
        d.line([(W * 0.46, H * 0.36), (W * 0.36, H * 0.42)], fill=g, width=3 * k)
        d.line([(W * 0.41, H * 0.62), (W * 0.52, H * 0.9)], fill=g, width=3 * k)
        d.line([(W * 0.41, H * 0.62), (W * 0.32, H * 0.74), (W * 0.25, H * 0.7)], fill=g, width=3 * k)
        d.polygon([(W * 0.66, H * 0.42), (W * 0.82, H * 0.42), (W * 0.82, H * 0.3), (W * 0.96, H * 0.5), (W * 0.82, H * 0.7), (W * 0.82, H * 0.58),
                   (W * 0.66, H * 0.58)], fill=g)
    art(img, (7, 21, 57, 43), man)
    save(img, "deco-exitsign")
    # A hand sanitizer dispenser: a white box, a grey lever, a window on its gel (empty), a crust below
    img = deco_base()
    rect(img, 22, 14, 41, 44, (226, 228, 226))
    M.bevel(img, (22, 14, 42, 45), strength=0.3)
    rect(img, 23, 15, 40, 18, (36, 110, 180))
    rect(img, 27, 22, 36, 30, (200, 210, 214))
    rect(img, 28, 23, 35, 29, (120, 130, 136))
    rect(img, 24, 34, 39, 40, (150, 154, 156))
    M.bevel(img, (24, 34, 40, 41), strength=0.25)
    rect(img, 30, 44, 33, 45, (180, 180, 170))
    M.drips(img, n=2, seed=14290, color=(196, 200, 180), length=(4, 10), strength=0.4, start=46)
    save(img, "deco-sanitizer")
    # A fire extinguisher on its bracket under its sign
    img = deco_base()
    rect(img, 18, 4, 45, 13, (196, 30, 28))
    draw_text(img, (19, 5, 45, 13), "FIRE\nEXTINGUISHER", (250, 246, 240), 3, condensed=True)
    def ext(d, k, W, H):
        red, dk, hi = (190, 28, 24, 255), (110, 14, 12, 255), (240, 120, 110, 255)
        d.rounded_rectangle([W * 0.3, H * 0.18, W * 0.7, H * 0.98], radius=W * 0.18, fill=red)
        d.rectangle([W * 0.36, H * 0.25, W * 0.42, H * 0.9], fill=hi)
        d.rectangle([W * 0.62, H * 0.25, W * 0.68, H * 0.9], fill=dk)
        d.rectangle([W * 0.36, H * 0.45, W * 0.64, H * 0.7], fill=(236, 232, 220, 255))
        d.rectangle([W * 0.42, H * 0.04, W * 0.58, H * 0.18], fill=(40, 40, 40, 255))
        d.line([(W * 0.42, H * 0.06), (W * 0.2, H * 0.1), (W * 0.18, H * 0.6)], fill=(30, 30, 30, 255), width=3 * k)
        d.line([(W * 0.52, H * 0.04), (W * 0.78, H * 0.0)], fill=(60, 60, 60, 255), width=3 * k)
        d.rectangle([W * 0.26, H * 0.3, W * 0.74, H * 0.34], fill=(70, 70, 70, 255))
    art(img, (20, 14, 44, 62), ext)
    save(img, "deco-extinguisher")
    # The T.14.R.G. stencil, sprayed black over the paint, the overspray and a run or two
    img = deco_base()
    lay = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw_text(lay, (4, 18, 60, 36), "T.14.R.G.", (28, 28, 28), 14)
    px, lp = img.load(), lay.load()
    for y in range(64):
        for x in range(64):
            r, g, b, a = lp[x, y]
            if a > 30:
                blend(img, x, y, (28, 30, 28), 0.9 * a / 255)
                if (x + y * 3) % 7 == 0:
                    blend(img, x + 1, y + 1, (60, 64, 60), 0.25)
    for x, y0 in ((10, 34), (29, 35), (47, 34)):
        for k in range(random.Random(x).randint(4, 12)):
            blend(img, x, y0 + k, (28, 30, 28), 0.7 * (1 - k / 14))
    draw_text(img, (14, 40, 50, 48), "LEVEL 14 RESEARCH GROUP", (40, 42, 40), 3, condensed=True)
    save(img, "deco-trg")
    directory_textures()


def directory_textures():
    """Round 4: the hospital directory board by a hall crossing, two blocks wide (deco-directory-l and -r, the board's
    left and right halves as seen from the hall): a teal enamel board in an aluminium frame, HOSPITAL DIRECTORY over the
    departments with their arrows, a YOU ARE HERE dot with no map round it, a sticker gone over one line."""
    W, H = 128, 64
    board = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0, y0, x1, y1 = 6, 10, 121, 55
    rect(board, x0 - 2, y0 - 2, x1 + 2, y1 + 2, (176, 182, 184))
    rect(board, x0 - 1, y0 - 1, x1 + 1, y1 + 1, (120, 126, 128))
    face = M.painted_metal(seed=14290, size=(120, 48), base=SIGN_TEAL, panel=False, chips=0)
    board.alpha_composite(face.crop((0, 0, x1 - x0 + 1, y1 - y0 + 1)), (x0, y0))
    rect(board, x0, y0, x1, y0 + 8, (236, 238, 230))
    draw_text(board, (x0 + 2, y0 + 1, x1 - 2, y0 + 8), "HOSPITAL DIRECTORY", SIGN_TEAL, 6)
    rows = [("WARD 1", ">"), ("INTENSIVE CARE", "<"), ("SURGERY", "^"), ("MATERNITY", ">"), ("PSYCHIATRY", "<"), ("STORES", "^")]
    for i, (name, arrow) in enumerate(rows):
        col, row = i // 3, i % 3
        bx = x0 + 3 + col * 58
        by = y0 + 11 + row * 11
        draw_text(board, (bx, by, bx + 40, by + 8), name, (236, 238, 230), 5, condensed=True)
        ax, ay = bx + 46, by + 4

        def arr(d, k, Wd, Hd, a=arrow):
            m, c = Hd / 2, (236, 238, 230, 255)
            pts = {">": [(0.1, m - 1.2 * k), (0.55 * Wd, m - 1.2 * k), (0.55 * Wd, 0), (Wd, m), (0.55 * Wd, Hd), (0.55 * Wd, m + 1.2 * k), (0.1, m + 1.2 * k)],
                   "<": [(Wd - 0.1, m - 1.2 * k), (0.45 * Wd, m - 1.2 * k), (0.45 * Wd, 0), (0, m), (0.45 * Wd, Hd), (0.45 * Wd, m + 1.2 * k), (Wd - 0.1, m + 1.2 * k)],
                   "^": [(Wd / 2 - 1.2 * k, Hd), (Wd / 2 - 1.2 * k, 0.45 * Hd), (0, 0.45 * Hd), (Wd / 2, 0), (Wd, 0.45 * Hd), (Wd / 2 + 1.2 * k, 0.45 * Hd), (Wd / 2 + 1.2 * k, Hd)]}[a]
            d.polygon(pts, fill=c)
        art(board, (ax - 4, ay - 4, ax + 4, ay + 4), arr)
    # YOU ARE HERE: a red dot and nothing round it
    rect(board, 100, 44, 103, 47, (210, 40, 36))
    draw_text(board, (78, 48, 120, 54), "YOU ARE HERE", (236, 238, 230), 4, condensed=True)
    # a strip of tape over the last line, half peeled
    rect(board, x0 + 58, y0 + 33, x0 + 100, y0 + 39, (214, 206, 170))
    M.grime(board, 0.14, seed=14291, color=(40, 44, 36), cells=(8, 4))
    M.scratches(board, n=6, seed=14292, light=0.12)
    for half, xs in (("l", 0), ("r", 64)):
        img = deco_base()
        img.alpha_composite(board.crop((xs, 0, xs + 64, 64)), (0, 0))
        save(img, "deco-directory-" + half)


# ======================================================================== Floors

def vinyl(seed, base=VINYL, chips=None, density=0.16):
    """Sheet vinyl: a pale ground with chips of darker, paler and tinted colour all through it, a dull sheen."""
    img = M.noise_hv(base, 2, seed, S, 4, (16, 8))
    chips = chips or [M.lift(base, -50), M.lift(base, -30), M.lift(base, 30), (132, 160, 150), (110, 116, 108)]
    speckle(img, seed + 1, density, chips)
    return img


def terrazzo(seed):
    """Round 4: polished terrazzo: a warm cream cement matrix packed with marble chips of mixed size (mostly white, pale
    grey, rose and sage, a few dark), each chip with a lit edge, a soft polish sheen, wear dulling it in patches, and a
    brass divider strip along two edges (a grid of panels a block across)."""
    rng = random.Random(seed)
    img = M.noise_hv((214, 204, 186), 2, seed, S, 3, (16, 8))
    px = img.load()
    chips = [((240, 236, 226), 30), ((226, 222, 212), 18), ((196, 192, 186), 14), ((214, 184, 170), 10), ((176, 188, 168), 8),
             ((168, 160, 148), 8), ((124, 116, 106), 5), ((92, 86, 80), 3), ((184, 150, 120), 4)]
    pool = [c for c, n in chips for _ in range(n)]
    shapes = [((0, 0),), ((0, 0), (1, 0)), ((0, 0), (0, 1)), ((0, 0), (1, 0), (0, 1)), ((0, 0), (1, 0), (1, 1)),
              ((0, 0), (1, 0), (0, 1), (1, 1)), ((0, 0), (1, 0), (2, 0), (1, 1))]
    weights = [34, 18, 18, 10, 10, 6, 4]
    taken = set()
    for _ in range(int(S * S * 0.30)):
        x, y = rng.randrange(1, S), rng.randrange(1, S)
        shp = rng.choices(shapes, weights)[0]
        cells = [((x + dx) % S, (y + dy) % S) for dx, dy in shp]
        if any(c in taken for c in cells):
            continue
        col = M.lift(rng.choice(pool), rng.uniform(-6, 6))
        for k, (cx, cy) in enumerate(cells):
            taken.add((cx, cy))
            edge = 8 if (k == 0 and len(cells) > 1) else 0
            px[cx, cy] = M.rgba(M.lift(col, edge))
    # polish: a broad soft sheen, then traffic wear dulling it
    for y in range(S):
        for x in range(S):
            t = 0.5 + 0.5 * math.sin(2 * math.pi * (x + y) / S)
            M.touch(img, x, y, 0.035 * t)
    M.grime(img, 0.08, seed=seed + 1, color=(170, 160, 140), cells=(16, 8), cover=0.5)
    M.scratches(img, n=4, seed=seed + 2, light=0.06)
    # the brass divider strip along the north and west edges (a grid of block-sized panels)
    for i in range(S):
        px[i, 0] = M.rgba(M.lift((186, 150, 84), rng.uniform(-8, 8)))
        px[0, i] = M.rgba(M.lift((186, 150, 84), rng.uniform(-8, 8)))
        M.touch(img, i, 1, -0.06)
        M.touch(img, 1, i, -0.04)
    return img


def floor_textures():
    save(vinyl(14300), "floor-vinyl")
    worn = vinyl(14301)
    M.grime(worn, 0.22, seed=14302, color=(130, 126, 108), cells=(16, 8, 4), cover=0.65)
    M.scratches(worn, n=8, seed=14303, light=0.1)
    scuffs(worn, 14304, 5, colour=(60, 60, 56), length=(2, 6), strength=0.35)
    M.crack(worn, 14305, length=(6, 12), strength=0.2)
    save(worn, "floor-vinylworn")
    save(vinyl(14306, base=(110, 128, 120), density=0.14), "floor-vinylborder")
    save(vinyl(14307, base=(232, 234, 230), chips=[(200, 204, 200), (214, 218, 214), (246, 248, 246)], density=0.1), "floor-white")
    save(vinyl(14308, base=(222, 192, 192), chips=[(190, 150, 154), (236, 214, 214), (176, 140, 148)], density=0.12), "floor-pink")
    th = M.noise_hv((150, 168, 158), 2, 14309, S, 5, (16, 8))
    M.grime(th, 0.08, seed=14310, color=(110, 120, 110), cells=(16, 8), cover=0.5)
    M.scratches(th, n=3, seed=14311, light=0.08)
    save(th, "floor-theatre")
    save(terrazzo(14312), "floor-terrazzo")
    cf = M.concrete(seed=14314, base=(140, 138, 132), grain=4, mottle=6, aggregate=0.04, pores=0.01, cracks=1)
    M.stain(cf, seed=14315, radius=8, color=(110, 104, 90), strength=0.3, at=(20, 12))
    save(cf, "floor-concrete")
    # Marble: white, veined, in tiles of half a block; shattered: cracked through in shards, some sunk and darker, chips gone
    def marble(seed):
        img = texlib.marble((232, 230, 224), (146, 148, 152), seed, veins=1, sharpness=10.0, mottle=0.05, turbulence=1.5)
        M.emboss_lines(img, xs=(0, 16), ys=(0, 16), strength=0.12)
        return img
    save(marble(14316), "floor-marble")
    ms = marble(14317)
    # round 4: hairline fractures (dark, a pixel wide) with a chipped pale lip on one side, the shards tipped a little
    # (a slight shade each), no cartoon outlines
    pts = M.points(S, 5, 14318)
    f1, f2, idx = M.worley(S, pts)
    rng = random.Random(14319)
    shade = [rng.uniform(-0.09, 0.04) for _ in pts]
    px = ms.load()
    for y in range(S):
        for x in range(S):
            M.touch(ms, x, y, shade[idx[y][x]])
            e = f2[y][x] - f1[y][x]
            if e < 0.32:
                px[x, y] = (70, 66, 62, 255)
            elif e < 0.75:
                M.touch(ms, x, y, 0.07 if idx[y][x] % 2 else -0.1)
    for _ in range(4):
        x, y = rng.randrange(S), rng.randrange(S)
        for dx in range(2):
            for dy in range(2):
                blend(ms, x + dx, y + dy, (24, 22, 20), 0.95)
    M.grime(ms, 0.12, seed=14320, color=(110, 96, 80), cells=(8, 4))
    save(ms, "floor-marbleshattered")
    bl = load("floor-vinylworn")
    # a dried pool, and a broad smear dragged away from it, streaky with the fingers that made it
    blotch(bl, 14321, (10, 12), 7, BLOOD, 0.85, rough=0.9, fuzz=False)
    blotch(bl, 14322, (9, 12), 4, (60, 4, 6), 0.5, rough=0.6, fuzz=False)
    rng = random.Random(14323)
    for k in range(6):
        y0 = 12 + k * 1.6 + rng.uniform(-0.5, 0.5)
        for x in range(12, S + 4):
            t = 0.75 * max(0.0, 1 - (x - 12) / 24) ** 0.7 * rng.uniform(0.7, 1.0)
            blend(bl, x, int(y0 + (x - 12) * 0.45), (100, 16, 14), t)
    speckle(bl, 14324, 0.01, [BLOOD], sizes=(1,))
    save(bl, "floor-blood")
    mf = vinyl(14324)
    M.tideline(mf, 4, seed=14325, color=(110, 110, 80), amount=0.25)
    M.grime(mf, 0.55, seed=14326, color=MOULD_DK, cells=(8, 4, 2), cover=0.55)
    M.grime(mf, 0.3, seed=14327, color=MOULD, cells=(4, 2), cover=0.4)
    speckle(mf, 14328, 0.05, [MOULD_DK, MOULD])
    save(mf, "floor-mould")
    ct = M.concrete(seed=14329, base=(118, 120, 104), grain=4, mottle=5, aggregate=0.04)
    blotch(ct, 14330, (12, 12), 9, (150, 176, 56), 0.6, rough=0.7)
    blotch(ct, 14331, (25, 24), 5, (170, 196, 64), 0.55, rough=0.7)
    blotch(ct, 14332, (11, 13), 4, (206, 228, 104), 0.55, rough=0.6)
    speckle(ct, 14333, 0.015, [(190, 220, 80)])
    save(ct, "floor-contam")
    # Cracked: the warning. Hairline cracks running out from a point, the sheet split along one of them, slightly sunk
    cr = vinyl(14334)
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 15.5, y - 15.5)
            if d < 13:
                M.touch(cr, x, y, -0.07 * (1 - d / 13))
    rng = random.Random(14335)
    for i in range(7):
        a = i * 2 * math.pi / 7 + rng.uniform(-0.3, 0.3)
        x, y = 15.5, 15.5
        L = rng.randint(9, 17)
        for k in range(L):
            a += rng.uniform(-0.35, 0.35)
            x, y = x + math.cos(a), y + math.sin(a)
            blend(cr, int(x), int(y), (40, 40, 38), 0.85 if k < L * 0.6 else 0.5)
            if i % 3 == 0:
                blend(cr, int(x) + 1, int(y), (40, 40, 38), 0.6)
            blend(cr, int(x), int(y) + 1, (226, 230, 222), 0.3)
    save(cr, "floor-cracked")
    # The red way line along a hall, and its arrow
    line = vinyl(14336)
    for y in range(S):
        for x in range(12, 20):
            blend(line, x, y, WAY_RED, 0.85 if 13 <= x <= 18 else 0.4)
    M.scratches(line, n=5, seed=14337, light=0.12, angle=90)
    scuffs(line, 14338, 3, colour=(150, 150, 140), length=(2, 4), strength=0.3)
    save(line, "floor-line-ns")
    save(line.rotate(90), "floor-line-we")
    arrow = vinyl(14339)
    for y in range(14, S):
        for x in range(12, 20):
            blend(arrow, x, y, WAY_RED, 0.85 if 13 <= x <= 18 else 0.4)
    art(arrow, (0, 0, S, S), lambda d, k, W, H: d.polygon([(W * 0.5, H * 0.06), (W * 0.9, H * 0.5), (W * 0.64, H * 0.5), (W * 0.64, H * 0.56),
                                                            (W * 0.36, H * 0.56), (W * 0.36, H * 0.5), (W * 0.1, H * 0.5)],
                                                           fill=WAY_RED + (230,)))
    M.scratches(arrow, n=4, seed=14340, light=0.12, angle=90)
    for dname, ang in (("n", 0), ("w", 90), ("s", 180), ("e", 270)):
        save(arrow.rotate(ang), f"floor-arrow-{dname}")
    # The sagging patch's parts: the void under it; the broken sheet's torn edge
    save(M.noise_hv((14, 12, 12), 2, 14341, S, 3, (8, 4)), "floor-void")
    edge = M.concrete(seed=14342, base=(96, 94, 88), grain=4, mottle=5, aggregate=0.08)
    rect(edge, 0, 0, S - 1, 1, M.lift(VINYL, -20))
    save(edge, "floor-edge")
    sag = vinyl(14343)
    M.grime(sag, 0.2, seed=14344, color=(110, 106, 92), cells=(8, 4), cover=0.6)
    for k in range(3):
        M.crack(sag, 14345 + k, length=(6, 14), strength=0.35)
    save(sag, "floor-sagvinyl")


# ======================================================================== Ceilings

def ceiling_textures():
    save(M.ceiling_tile(seed=14400, base=CEIL), "ceil-tile")
    save(M.ceiling_tile(seed=14401, base=CEIL, stain_color=(150, 116, 64)), "ceil-stained")
    lens = dict(lens=(232, 240, 244), frame=(206, 208, 204), tubes=2, glow=(240, 248, 255))
    save(M.troffer_lens(seed=14402, lit=1.0, **lens), "ceil-troffer")
    save(M.troffer_lens(seed=14403, lit=1.0, lens=(244, 248, 250), frame=(226, 228, 226), tubes=3, glow=(252, 254, 255)), "ceil-bright")
    off = M.troffer_lens(seed=14404, lit=0.0, **lens)
    rng = random.Random(14405)
    for _ in range(9):  # dead flies in the lens
        x, y = rng.randrange(5, 27), rng.randrange(5, 27)
        blend(off, x, y, (30, 28, 24), 0.85)
    M.stain(off, seed=14406, radius=6, color=(150, 130, 90), strength=0.3, at=(10, 22))
    save(off, "ceil-off")
    # A missing tile: the rail round a black hole, the edge of a duct and a cable barely there in it
    hole = M.ceiling_tile(seed=14407, base=CEIL)
    px = hole.load()
    for y in range(1, S - 1):
        for x in range(1, S - 1):
            px[x, y] = (8 + (x * 7 + y * 3) % 3, 8, 9, 255)
    for x in range(1, S - 1):
        blend(hole, x, 9, (30, 30, 30), 0.8)
        blend(hole, x, 10, (22, 22, 22), 0.8)
    for y in range(1, S - 1):
        blend(hole, 20 + int(3 * math.sin(y / 5)), y, (34, 30, 26), 0.8)
    save(hole, "ceil-hole")
    bl = M.ceiling_tile(seed=14408, base=CEIL, stain_color=(120, 40, 30))
    blotch(bl, 14409, (15, 14), 6, BLOOD, 0.8, rough=0.9, wrap=False)
    blotch(bl, 14410, (15, 14), 3, (60, 4, 6), 0.6, rough=0.6, wrap=False)
    speckle(bl, 14411, 0.012, [(70, 8, 10)], sizes=(1, 2))
    save(bl, "ceil-blood")
    mo = M.ceiling_tile(seed=14411, base=CEIL, stain_color=(130, 120, 80))
    M.grime(mo, 0.5, seed=14412, color=MOULD_DK, cells=(8, 4, 2), cover=0.55)
    speckle(mo, 14413, 0.05, [MOULD_DK, MOULD])
    save(mo, "ceil-mould")
    save(M.plaster(seed=14414, base=(226, 228, 224), grain=1, mottle=3, roller=0.1), "ceil-plaster")
    save(M.concrete(seed=14415, base=(128, 128, 122), grain=4, mottle=6, aggregate=0.05, border=1), "ceil-concrete")


# ======================================================================== Model textures (doors, rails, windows, the revolving door)

def model_textures():
    # The rails: a warm wood handrail, the bumper's teal vinyl, the brackets' steel; for the white units, white vinyl
    rw = M.wood_planks(seed=14500, base=(150, 108, 66), planks=[8, 8, 8, 8], direction="h", grain=3, contrast=0.7, flecks=0.8)
    M.scratches(rw, n=4, seed=14501, light=0.15, angle=0)
    save(rw, "rail-wood")
    save(M.rubber(seed=14502, base=(64, 104, 96), grain=2, mottle=3, pattern="ribs", pitch=4), "rail-bumper")
    save(M.rubber(seed=14503, base=(206, 210, 208), grain=2, mottle=2), "rail-white")
    save(M.rubber(seed=14504, base=(176, 184, 186), grain=2, mottle=2, pattern="ribs", pitch=4), "rail-whitebumper")
    save(M.brushed_metal(seed=14505, base=STAINLESS, direction="h", streak=5, sheen=8), "rail-steel")
    # Window frame (painted steel, white, chipped), the glass shards, the black of nothing
    wf = M.painted_metal(seed=14510, base=(214, 216, 210), panel=False, chips=4, under=(110, 104, 96))
    M.grime(wf, 0.12, seed=14511, color=(130, 126, 110))
    save(wf, "win-frame")
    sh = M.noise_hv((150, 176, 172), 2, 14512, S, 3, (8, 4))
    for k in range(S):
        blend(sh, k, (k * 2) % S, (226, 240, 238), 0.6)
        blend(sh, k, (k * 2 + 1) % S, (200, 220, 218), 0.4)
    save(sh, "win-shard")
    save(M.new((S, S), (0, 0, 0)), "win-black")
    # The doors: pale laminate, its edge, the frame's teal-grey steel, stainless kick plates and levers, wire glass dark behind
    lam = M.noise_hv((206, 198, 176), 2, 14520, S, 3, (16, 8))
    for y in range(S):
        for x in range(S):
            M.touch(lam, x, y, 0.025 * math.sin(x * 0.9 + math.sin(y * 0.2) * 2))
    scuffs(lam, 14521, 4, colour=(140, 132, 116), length=(3, 8), strength=0.3)
    M.grime(lam, 0.08, seed=14522, color=(150, 140, 116))
    save(lam, "door-leaf")
    save(M.noise_hv((150, 140, 120), 2, 14523, S, 3, (8, 4)), "door-leafedge")
    fr = M.painted_metal(seed=14524, base=FRAME, panel=False, chips=4, under=(150, 154, 150))
    M.scratches(fr, n=4, seed=14525, light=0.18)
    save(fr, "door-frame")
    save(M.brushed_metal(seed=14526, base=STAINLESS, direction="h", streak=5, sheen=8), "door-steel")
    wg = M.noise_hv((14, 18, 20), 2, 14527, S, 2, (8, 4))
    wire_mesh(wg, (0, 0, S - 1, S - 1), colour=(70, 80, 84), pitch=4, t=0.6)
    for k in range(10):
        blend(wg, 4 + k, 3 + k, (90, 104, 110), 0.5)
    save(wg, "door-wireglass")
    # The contaminated room's door: steel painted a grey-green, the trefoil placard on its lower half; the green glass
    for part in ("lower", "upper"):
        cs = M.painted_metal(seed=14530 + (part == "upper"), base=(120, 134, 124), panel=False, chips=4, under=(90, 84, 76))
        M.rust(cs, 0.08, seed=14532)
        if part == "lower":
            cs = up2(cs)
            rect(cs, 18, 4, 45, 34, (30, 30, 30))
            rect(cs, 19, 5, 44, 33, (238, 200, 40))
            art(cs, (20, 6, 44, 28), lambda d, k, W, H: trefoil(d, W / 2, H / 2, H * 0.42, (20, 20, 20, 255), k, "radiation"))
            draw_text(cs, (19, 27, 45, 33), "DO NOT ENTER", (20, 20, 20), 4, condensed=True)
            M.grime(cs, 0.15, seed=14533, bias="bottom", color=(70, 66, 56))
        save(cs, "door-contam" + part)
    cg = M.noise_hv((110, 200, 70), 3, 14534, S, 8, (16, 8))
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 15.5, y - 15.5) / 22
            M.touch(cg, x, y, 0.25 * (1 - d))
    wire_mesh(cg, (0, 0, S - 1, S - 1), colour=(40, 70, 30), pitch=4, t=0.5)
    save(cg, "door-contamglass")
    # The fire door: oxide-red painted steel, a round FIRE DOOR KEEP SHUT sign, a push plate
    for part in ("lower", "upper"):
        fd = M.painted_metal(seed=14540 + (part == "upper"), base=(132, 58, 46), panel=False, chips=5, under=(90, 84, 80))
        scuffs(fd, 14542, 5, colour=(80, 40, 34), length=(3, 9), strength=0.4)
        if part == "lower":
            M.grime(fd, 0.15, seed=14543, bias="bottom", color=(60, 40, 30))
            fd = up2(fd)
            art(fd, (24, 4, 44, 24), lambda d, k, W, H: (d.ellipse([0, 0, W - 1, H - 1], fill=(30, 90, 170, 255)),
                                                         d.ellipse([W * 0.08, H * 0.08, W * 0.92, H * 0.92], outline=(240, 240, 240, 255), width=k)))
            draw_text(fd, (26, 8, 42, 20), "FIRE DOOR\nKEEP SHUT", (240, 240, 240), 3, condensed=True)
        save(fd, "door-fire" + part)
    # The hanging sign's rods and rim
    save(M.brushed_metal(seed=14550, base=(70, 76, 78), direction="v", streak=4, sheen=5), "sign-rod")
    for n, name in enumerate(SIGNS):
        save(sign_face(120, 64, name, 14560 + n), f"sign-hang{n}")
    revolving_textures()


# ---------------- the revolving door

JEWELS = [(150, 18, 36), (28, 48, 140), (18, 110, 62), (206, 132, 26), (100, 36, 120), (196, 70, 30), (40, 120, 140)]


def stained_glass(seed, W=80, H=80, panes=5):
    """A side of the drum (five tall lancets side by side, 16 px each), leaded glass in jewel colours: a border of small
    squares, a pointed arch of pale amber at the top, a field of large quarries in the lancet's colour, and in the middle
    of each a gold halo round nothing: black. Each piece of glass has its own shade, as old glass does."""
    rng = random.Random(seed)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    px = img.load()
    lead = (30, 27, 24)
    bronze = (126, 92, 46)
    fields = [JEWELS[1], JEWELS[0], JEWELS[2], JEWELS[4], JEWELS[1]]
    if seed % 2:
        fields = fields[::-1]
    shade = {}

    def piece(key, c):
        if key not in shade:
            shade[key] = (rng.uniform(-22, 18), rng.uniform(-6, 6))
        v, hcol = shade[key]
        return (c[0] + v + hcol, c[1] + v, c[2] + v - hcol)

    pw = W // panes
    for p in range(panes):
        x0 = p * pw
        field = fields[p]
        cx, cy, r = x0 + pw / 2 - 0.5, 44.0, 4.6
        for y in range(H):
            for x in range(x0, x0 + pw):
                lx = x - x0
                d = math.hypot(x - cx, (y - cy) * 0.9)
                arch = abs(lx - 7.5) - (y - 3) * 0.55  # > 0 outside the arch's point
                if lx in (0, pw - 1):
                    c = bronze
                elif lx in (1, pw - 2) or y in (0, 1, H - 2, H - 1):
                    c = lead
                elif lx in (2, pw - 3):
                    c = lead if y % 5 == 0 else piece(("b", p, lx, y // 5), JEWELS[(y // 5 + p) % 2 * 3])
                elif lx in (3, pw - 4):
                    c = lead
                elif y < 20 and arch <= 0.5:
                    c = lead if abs(arch) < 0.9 or y == 19 else piece(("a", p, y // 7), (214, 178, 96))
                elif d < r + 2.4 and 22 < y < 66:
                    if d < r - 1.0:
                        c = (3, 3, 4)
                    elif d < r:
                        c = lead
                    elif d < r + 1.4:
                        c = piece(("h", p, int(math.atan2(y - cy, x - cx) * 2)), (228, 184, 66))
                    else:
                        c = lead
                elif y > 66:
                    m = abs(lx - 7.5) + abs(y - 72.5)
                    c = lead if abs(m - 4.5) < 0.7 or y == 67 else piece(("d", p, m < 4.5), JEWELS[3] if m < 4.5 else JEWELS[2])
                else:
                    qx, qy = (lx - 4) // 4, (y - 20) // 9
                    edge = (lx - 4) % 4 == 3 or (y - 20) % 9 == 8
                    c = lead if edge else piece(("q", p, qx, qy), field)
                n = rng.uniform(-3, 3)
                px[x, y] = (M.clamp(c[0] + n), M.clamp(c[1] + n), M.clamp(c[2] + n), 255)
    # grime in the leads and the lower corners, a sheen down the glass
    M.grime(img, 0.14, seed=seed + 1, color=(26, 22, 18), cells=(8, 4, 2), cover=0.45)
    for y in range(H):
        for x in range(W):
            t = max(0.0, 1 - abs((x % pw) - 4 - y * 0.08) / 2.5) * 0.12
            if t:
                blend(img, x, y, (255, 246, 220), t)
    return img


def revolving_textures():
    save(stained_glass(1), "rev-glasse")
    save(stained_glass(4), "rev-glassw")
    br = M.brushed_metal(seed=14600, base=(166, 126, 66), direction="v", streak=6, sheen=16)
    M.grime(br, 0.16, seed=14601, color=(58, 86, 70), cells=(8, 4, 2), cover=0.4)  # verdigris in the corners of years
    M.scratches(br, 4, seed=14605, light=0.18)
    save(br, "rev-bronze")
    # round 4: the canopy's frieze: a raised bronze meander between two beads, verdigris in the recesses
    fr = M.brushed_metal(seed=14606, base=(120, 90, 48), direction="h", streak=5, sheen=8)
    px = fr.load()
    hi, lo = (196, 156, 90), (70, 54, 30)
    for x in range(S):
        for y in (2, 3, 28, 29):
            px[x, y] = M.rgba(hi if y in (2, 28) else lo)
    # the meander: a square key every 16 px, 2 px strokes
    def stroke(x0, y0, x1, y1):
        for x in range(min(x0, x1), max(x0, x1) + 2):
            for y in range(min(y0, y1), max(y0, y1) + 2):
                px[x % S, y] = M.rgba(hi)
                if y + 2 < S:
                    M.touch(fr, x % S, y + 2, -0.12)
    for k in (0, 16):
        stroke(k, 22, k + 14, 22)
        stroke(k + 14, 8, k + 14, 22)
        stroke(k + 4, 8, k + 14, 8)
        stroke(k + 4, 8, k + 4, 17)
        stroke(k + 4, 17, k + 9, 17)
        stroke(k + 9, 12, k + 9, 17)
    M.grime(fr, 0.2, seed=14607, color=(58, 96, 76), cells=(4, 2), cover=0.35)
    save(fr, "rev-frieze")
    dk = M.noise_hv((10, 12, 14), 1, 14602, S, 2, (8, 4))
    for k in range(S):
        for w_ in range(3):
            blend(dk, k + w_, S - 1 - k, (46, 50, 56), 0.35 - 0.1 * w_)
    save(dk, "rev-dark")
    save(M.new((S, S), (0, 0, 0)), "rev-black")
    mb = texlib.marble((38, 52, 46), (110, 134, 120), 14603, veins=1, sharpness=10.0, mottle=0.08, turbulence=1.5)
    M.emboss_lines(mb, xs=(0,), ys=(0,), strength=0.15)
    save(mb, "rev-marble")
    save(M.rubber(seed=14604, base=(30, 30, 32), pattern="ribs", pitch=4), "rev-floor")


# ======================================================================== Shape tools

def project(el):
    """Sets every face's UV from where it lies on the block (as a cube's faces), so a texture runs on across the
    elements of a model and across its blocks. For axis-aligned elements in block-local coordinates."""
    (x1, y1, z1), (x2, y2, z2) = el["from"], el["to"]

    def fit(a, b):
        k = math.floor(min(a, b) / 16 + 1e-6)
        a, b = a - 16 * k, b - 16 * k
        return round(max(0.0, a), 4), round(min(16.0, b), 4)

    for f, face in el["faces"].items():
        if f == "north":
            u, v = fit(16 - x2, 16 - x1), fit(16 - y2, 16 - y1)
        elif f == "south":
            u, v = fit(x1, x2), fit(16 - y2, 16 - y1)
        elif f == "east":
            u, v = fit(16 - z2, 16 - z1), fit(16 - y2, 16 - y1)
        elif f == "west":
            u, v = fit(z1, z2), fit(16 - y2, 16 - y1)
        elif f == "up":
            u, v = fit(x1, x2), fit(z1, z2)
        else:
            u, v = fit(x1, x2), fit(16 - z2, 16 - z1)
        if u[1] - u[0] < 0.01:
            u = (u[0], u[0] + 0.5) if u[0] < 15.5 else (15.5, 16)
        if v[1] - v[0] < 0.01:
            v = (v[0], v[0] + 0.5) if v[0] < 15.5 else (15.5, 16)
        face["uv"] = [u[0], v[0], u[1], v[1]]
    return el


def finish(els):
    """Projects the UVs of a shape's axis-aligned elements that keep no UVs of their own (see project)."""
    for e in els:
        if not rotated(e) and "_uv" not in e:
            project(e)
    return els


def rotated(e):
    return any(e.get("rotation" + a) for a in "XYZ")


def centre_of(e):
    """The element's centre after its rotation (about Y only, which is all the cut models use)."""
    c = [(e["from"][i] + e["to"][i]) / 2 for i in range(3)]
    if not rotated(e):
        return c
    o = e["rotationOrigin"]
    a = math.radians(e.get("rotationY", 0))
    dx, dz = c[0] - o[0], c[2] - o[2]
    return [o[0] + math.cos(a) * dx + math.sin(a) * dz, c[1], o[2] - math.sin(a) * dx + math.cos(a) * dz]


def cut(els, nx, ny, nz):
    """A model of nx x ny x nz blocks cut into its blocks: {(ix, iy, iz): elements in that block's coordinates}.
    Axis-aligned elements are clipped to each block they cross and their UVs projected (unless they carry "_uv", which
    keeps theirs: only for elements inside one block); a turned element is cut only across y (its side faces' UVs cut in proportion) and each piece goes
    whole to the block that holds its centre. Parts proud of the model's outline go to its edge blocks."""
    parts = {(i, j, k): [] for i in range(nx) for j in range(ny) for k in range(nz)}
    n = (nx, ny, nz)

    def spans(lo, hi, axis):
        out = []
        for c in range(n[axis]):
            a = -1e9 if c == 0 else 16 * c
            b = 1e9 if c == n[axis] - 1 else 16 * (c + 1)
            s, t = max(lo, a), min(hi, b)
            if t - s > 1e-6:
                out.append((c, s, t))
        return out

    for e in els:
        f, t = e["from"], e["to"]
        if not rotated(e):
            for (ix, x1, x2) in spans(f[0], t[0], 0):
                for (iy, y1, y2) in spans(f[1], t[1], 1):
                    for (iz, z1, z2) in spans(f[2], t[2], 2):
                        p = json.loads(json.dumps(e))
                        p["from"] = [round(x1 - 16 * ix, 4), round(y1 - 16 * iy, 4), round(z1 - 16 * iz, 4)]
                        p["to"] = [round(x2 - 16 * ix, 4), round(y2 - 16 * iy, 4), round(z2 - 16 * iz, 4)]
                        # faces on a cut plane are inside the model
                        for face, (axis, edge, orig) in (("west", (0, x1, f[0])), ("east", (0, x2, t[0])), ("down", (1, y1, f[1])),
                                                         ("up", (1, y2, t[1])), ("north", (2, z1, f[2])), ("south", (2, z2, t[2]))):
                            if abs(edge - orig) > 1e-6:
                                p["faces"].pop(face, None)
                        if not p["faces"]:
                            continue
                        if "_uv" not in e:
                            project(p)
                        parts[(ix, iy, iz)].append(p)
        else:
            assert not e.get("rotationX") and not e.get("rotationZ"), e["name"]
            cx, _, cz = centre_of(e)
            ix = min(nx - 1, max(0, int(cx // 16)))
            iz = min(nz - 1, max(0, int(cz // 16)))
            for (iy, y1, y2) in spans(f[1], t[1], 1):
                p = json.loads(json.dumps(e))
                p["from"] = [round(f[0] - 16 * ix, 4), round(y1 - 16 * iy, 4), round(f[2] - 16 * iz, 4)]
                p["to"] = [round(t[0] - 16 * ix, 4), round(y2 - 16 * iy, 4), round(t[2] - 16 * iz, 4)]
                o = e["rotationOrigin"]
                p["rotationOrigin"] = [round(o[0] - 16 * ix, 4), round(o[1] - 16 * iy, 4), round(o[2] - 16 * iz, 4)]
                if y1 > f[1] + 1e-6:
                    p["faces"].pop("down", None)
                if y2 < t[1] - 1e-6:
                    p["faces"].pop("up", None)
                h = t[1] - f[1]
                for face, fc in p["faces"].items():
                    if face in ("north", "south", "east", "west"):
                        u1, v1, u2, v2 = fc["uv"]
                        fc["uv"] = [u1, round(v1 + (t[1] - y2) / h * (v2 - v1), 4), u2, round(v1 + (t[1] - y1) / h * (v2 - v1), 4)]
                if p["faces"]:
                    parts[(ix, iy, iz)].append(p)
    return parts


def mirror_z(els, about=8.0):
    """The elements mirrored front to back about z = about: north and south faces swap."""
    out = []
    for e in json.loads(json.dumps(els)):
        z1, z2 = e["from"][2], e["to"][2]
        e["from"][2], e["to"][2] = round(2 * about - z2, 4), round(2 * about - z1, 4)
        if "rotationOrigin" in e:
            e["rotationOrigin"][2] = round(2 * about - e["rotationOrigin"][2], 4)
            if "rotationY" in e:
                e["rotationY"] = -e["rotationY"]
            if "rotationX" in e:
                e["rotationX"] = -e["rotationX"]
        e["faces"] = {({"north": "south", "south": "north"}.get(k, k)): v for k, v in e["faces"].items()}
        out.append(e)
    return out


def mirror_x(els):
    out = []
    for e in json.loads(json.dumps(els)):
        x1, x2 = e["from"][0], e["to"][0]
        e["from"][0], e["to"][0] = round(16 - x2, 4), round(16 - x1, 4)
        if "rotationOrigin" in e:
            e["rotationOrigin"][0] = round(16 - e["rotationOrigin"][0], 4)
            if "rotationY" in e:
                e["rotationY"] = -e["rotationY"]
            if "rotationZ" in e:
                e["rotationZ"] = -e["rotationZ"]
        e["faces"] = {({"east": "west", "west": "east"}.get(k, k)): v for k, v in e["faces"].items()}
        out.append(e)
    return out


def ring(name, phi, r1, r2, hw, y1, y2, tex_out, tex_in, tex_edge, cx=24.0, cz=16.0, lateral=0.0, uv=None, glow=0):
    """A box standing on a circle about (cx, cz), facing out at compass angle phi (0 north, 90 east, clockwise): from
    radius r1 to r2, hw either side of its radial line (shifted `lateral`), y1 to y2. Its outer face takes tex_out (with
    `uv` if given), its inner tex_in, the rest tex_edge. Built facing north or south and turned by a multiple of 22.5."""
    phi = phi % 360
    if phi in (90, 270):
        s = 1 if phi == 90 else -1
        xa, xb = sorted((cx + s * r1, cx + s * r2))
        el = box(name, (xa, y1, cz - hw + lateral * s), (xb, y2, cz + hw + lateral * s),
                 {"east": tex_out if s > 0 else tex_in, "west": tex_in if s > 0 else tex_out, "all": tex_edge}, glow=glow)
        outf = "east" if s > 0 else "west"
    elif phi < 90 or phi > 270:
        el = box(name, (cx - hw + lateral, y1, cz - r2), (cx + hw + lateral, y2, cz - r1), {"north": tex_out, "south": tex_in, "all": tex_edge},
                 rot=(0, -(phi if phi < 180 else phi - 360), 0), origin=(cx, y1, cz), glow=glow)
        outf = "north"
    else:
        el = box(name, (cx - hw - lateral, y1, cz + r1), (cx + hw - lateral, y2, cz + r2), {"south": tex_out, "north": tex_in, "all": tex_edge},
                 rot=(0, 180 - phi, 0), origin=(cx, y1, cz), glow=glow)
        outf = "south"
    if el.get("rotationY") == 0:
        el.pop("rotationY")
        el.pop("rotationOrigin")
    if uv:
        el["faces"][outf]["uv"] = list(uv)
    for f in el["faces"].values():
        if glow and f["texture"] not in ("#" + tex_out,):
            f.pop("glow", None)
    return el


# ======================================================================== Shapes

def rail_shape(kind):
    """A hall wall's foot: the full wall block (its wainscot), and proud of its north face a bumper strip and above it a
    handrail on two brackets, at the top of the block (13 to 15.5 up)."""
    wall = "wall-paintbase" if kind == "paint" else "wall-whitebase"
    rail = "rail-wood" if kind == "paint" else "rail-white"
    bump = "rail-bumper" if kind == "paint" else "rail-whitebumper"
    els = [box("Wall", (0, 0, 0), (16, 16, 16), wall)]
    # the bumper: a flat strip on the wall below the rail
    els.append(box("Bumper", (0, 10.5, -0.75), (16, 12.5, 0), bump, faces=("north", "up", "down")))
    els.append(box("BumperLip", (0, 10.75, -1.0), (16, 12.25, -0.75), bump, faces=("north", "up", "down")))
    # brackets: a round rose on the wall, an arm out and up under the rail
    for i, x in enumerate((4.0, 12.0)):
        els.append(box(f"Rose{i}", (x - 1, 12.75, -0.5), (x + 1, 14.25, 0), "rail-steel", faces=("north", "east", "west", "up", "down")))
        els.append(box(f"Arm{i}", (x - 0.4, 13.25, -2.25), (x + 0.4, 13.85, -0.5), "rail-steel", faces=("north", "east", "west", "up", "down")))
        els.append(box(f"Saddle{i}", (x - 0.75, 13.85, -2.6), (x + 0.75, 14.25, -1.4), "rail-steel", faces=("north", "east", "west", "down")))
    # the handrail: a rounded bar (a core and two thinner boxes for the round)
    els.append(box("Rail", (0, 14.25, -3.0), (16, 15.75, -1.0), rail, faces=("north", "up", "down", "south")))
    els.append(box("RailTop", (0, 15.75, -2.6), (16, 16.0, -1.4), rail, faces=("north", "up", "south")))
    els.append(box("RailUnder", (0, 14.0, -2.6), (16, 14.25, -1.4), rail, faces=("north", "down", "south")))
    return shape("l14-rail-" + kind, finish(els))


def window_shape(part, state):
    """A wall block with a window in its north face: the paint round it, a recess 4 deep lined with the frame, a sill
    (lower), the glass gone but for shards in the frame (broken: a few; shattered: almost none), and behind it at the
    back of the recess a black plane: nothing on the other side. The window runs from 4 up in the lower block to 12 up in
    the upper one, 2 to 14 across."""
    lower = part == "lower"
    rng = random.Random(f"win-{part}-{state}")
    oy1, oy2 = (4, 16) if lower else (0, 12)
    els = [
        box("PostL", (0, 0, 0), (2, 16, 16), {"all": "wall-paint", "east": "win-frame"}),
        box("PostR", (14, 0, 0), (16, 16, 16), {"all": "wall-paint", "west": "win-frame"}),
        box("Back", (2, oy1, 6), (14, oy2, 16), {"all": "wall-paint", "north": "win-black"}, faces=("north", "south")),
    ]
    if lower:
        els.append(box("Under", (2, 0, 0), (14, 4, 16), {"all": "wall-paint", "up": "win-frame"}))
        els.append(box("Sill", (1, 3.25, -1.5), (15, 4.25, 6), "win-frame", faces=("north", "up", "east", "west", "down")))
        els.append(box("SillLip", (1, 2.75, -1.5), (15, 3.25, -0.75), "win-frame", faces=("north", "east", "west", "down")))
    else:
        els.append(box("Over", (2, 12, 0), (14, 16, 16), {"all": "wall-paint", "down": "win-frame"}))
    # the frame: a bead round the opening on the wall's face, and the glazing stop near the back of the recess
    if lower:
        els.append(box("BeadL", (1.25, 4.25, -0.5), (2.5, 16, 0), "win-frame", faces=("north", "east", "west")))
        els.append(box("BeadR", (13.5, 4.25, -0.5), (14.75, 16, 0), "win-frame", faces=("north", "east", "west")))
    else:
        els.append(box("BeadL", (1.25, 0, -0.5), (2.5, 12.75, 0), "win-frame", faces=("north", "east", "west")))
        els.append(box("BeadR", (13.5, 0, -0.5), (14.75, 12.75, 0), "win-frame", faces=("north", "east", "west")))
        els.append(box("BeadT", (1.25, 11.5, -0.5), (14.75, 12.75, 0), "win-frame", faces=("north", "up", "down", "east", "west")))
    stop_y1, stop_y2 = (4, 16) if lower else (0, 12)
    els.append(box("StopL", (2, stop_y1, 4.5), (3, stop_y2, 6), "win-frame", faces=("north", "east")))
    els.append(box("StopR", (13, stop_y1, 4.5), (14, stop_y2, 6), "win-frame", faces=("north", "west")))
    if lower:
        els.append(box("StopB", (3, 4, 4.5), (13, 5, 6), "win-frame", faces=("north", "up")))
        els.append(box("Rail", (2, 15, 4.5), (14, 16, 6), "win-frame", faces=("north", "down", "up")))  # the meeting rail
    else:
        els.append(box("StopT", (3, 11, 4.5), (13, 12, 6), "win-frame", faces=("north", "down")))
        els.append(box("Rail", (2, 0, 4.5), (14, 1, 6), "win-frame", faces=("north", "up", "down")))
    # Shards left in the frame: jagged triangles (boxes turned on z) along the stops
    n = 7 if state == "broken" else 2
    for i in range(n):
        edge = rng.choice(("l", "r", "e", "e") if state == "broken" else ("l", "e"))
        size = rng.uniform(1.5, 3.5) if state == "broken" else rng.uniform(1.0, 1.8)
        if edge == "l":
            x0, y0 = 2.6, rng.uniform(oy1 + 1.5, oy2 - 3)
        elif edge == "r":
            x0, y0 = 13.4 - size, rng.uniform(oy1 + 1.5, oy2 - 3)
        else:
            x0 = rng.uniform(3.5, 12.5 - size)
            y0 = (5.2 if lower else 11.2 - size)
        z = 5.0 + (i % 3) * 0.12
        els.append(box(f"Shard{i}", (x0, y0, z), (x0 + size, y0 + size * rng.uniform(0.8, 1.6), z + 0.25), "win-shard",
                       faces=("north", "south"), rot=(0, 0, rng.choice((-45, -22.5, 22.5, 45))), uv=(0, 0, 4, 6)))
    return shape(f"l14-window-{part}-{state}", finish(els))


def door_model(kind):
    """A hospital door two blocks high in its frame, the leaf (shut) near the north face, hinged at the west (x 0) edge;
    kind "room": pale laminate, a narrow wire-glass vision panel at eye height, a lever each side, kick plates; "contam":
    painted steel, a square window of green-lit wire glass, the trefoil placard. Returns (frame, leaf)."""
    frame = [
        box("JambW", (0, 0, 0), (1.25, 32, 16), {"all": "door-frame"}, faces=("east", "north", "south")),
        box("JambE", (14.75, 0, 0), (16, 32, 16), {"all": "door-frame"}, faces=("west", "north", "south")),
        box("Head", (1.25, 29.5, 0), (14.75, 32, 16), "door-frame", faces=("down", "north", "south")),
        box("CasingWN", (-0.75, 0, -0.5), (1.25, 32, 0), "door-frame", faces=("north", "east", "west")),
        box("CasingEN", (14.75, 0, -0.5), (16.75, 32, 0), "door-frame", faces=("north", "east", "west")),
        box("CasingHN", (1.25, 29.5, -0.5), (14.75, 32, 0), "door-frame", faces=("north", "down")),
        box("StopW", (1.25, 0, 0.2), (1.85, 29.5, 0.95), "door-frame", faces=("north", "east", "south")),
        box("StopE", (14.15, 0, 0.2), (14.75, 29.5, 0.95), "door-frame", faces=("north", "west", "south")),
        box("StopH", (1.85, 28.9, 0.2), (14.15, 29.5, 0.95), "door-frame", faces=("north", "down", "south")),
    ]
    frame += mirror_z([e for e in frame if e["name"].startswith("Casing")], 8.0)
    x1, x2, y1, y2, z1, z2 = 1.35, 14.65, 0.4, 29.4, 1.0, 2.75
    if kind == "room":
        wx1, wx2, wy1, wy2 = 9.0, 12.0, 18.5, 27.0
        lt = {"north": "door-leaf", "south": "door-leaf", "all": "door-leafedge"}
    else:
        wx1, wx2, wy1, wy2 = 4.5, 11.5, 18.0, 25.0
        lt = None
    leaf = []

    def piece(name, a, b, c, d):
        if kind == "room":
            t = lt
        else:
            # the contaminated door's paint: its own picture per block (the placard is on the lower one)
            t = {"north": "door-contamlower" if d <= 16 else "door-contamupper", "south": "door-contamlower" if d <= 16 else "door-contamupper",
                 "all": "door-frame"}
        if kind != "room" and b < 16 < d:
            leaf.append(box(name + "A", (a, b, z1), (c, 16, z2), {**t, "north": "door-contamlower", "south": "door-contamlower"}))
            leaf.append(box(name + "B", (a, 16, z1), (c, d, z2), {**t, "north": "door-contamupper", "south": "door-contamupper"}))
        else:
            leaf.append(box(name, (a, b, z1), (c, d, z2), t))

    piece("LeafLow", x1, y1, x2, wy1)
    piece("LeafHigh", x1, wy2, x2, y2)
    piece("LeafW", x1, wy1, wx1, wy2)
    piece("LeafE", wx2, wy1, x2, wy2)
    glass = "door-wireglass" if kind == "room" else "door-contamglass"
    win = inset_window("Vision", wx1, wy1, wx2, wy2, z1, z2, "door-steel", glass=glass)
    if kind != "room":
        for e in win:
            if e["name"].endswith("Pane"):
                for f in e["faces"].values():
                    f["glow"] = 160
    leaf += win
    hw = "door-steel"
    leaf += lever("LeverN", x2 - 2.0, 15.0, z1, 3.0, hw, side=-1)
    leaf += mirror_z(lever("LeverS", x2 - 2.0, 15.0, z1, 3.0, hw, side=-1), (z1 + z2) / 2)
    leaf += kick_plate("KickN", x1 + 0.5, x2 - 0.5, 0.75, 5.0, z1, hw)
    leaf += mirror_z(kick_plate("KickS", x1 + 0.5, x2 - 0.5, 0.75, 5.0, z1, hw), (z1 + z2) / 2)
    if kind == "room":
        leaf.append(box("PushPlate", (x2 - 3.25, 19.0, z2), (x2 - 1.25, 25.0, z2 + 0.25), hw, faces=without(DIRS, "north")))
    else:
        leaf.append(box("Bolt", (x2 - 3.0, 21.0, z1 - 0.75), (x2 - 1.0, 23.0, z1), hw, faces=without(DIRS, "south")))
    for i, (a, b) in enumerate(((3.0, 6.0), (13.0, 16.0), (24.0, 27.0))):
        leaf.append(box(f"Knuckle{i}", (x1 - 0.6, a, z2 - 0.5), (x1 + 0.2, b, z2 + 0.3), hw))
    return frame, leaf


def door_open(leaf):
    """The leaf swung in a quarter turn on its west hinges, standing along the west jamb, its front facing east."""
    turned = turn(leaf, 1)
    return move(turned, dx=1.35 - 13.25, dz=2.65 - 1.35)


def door_shapes():
    """The room door and the contaminated room's door, cut into their two blocks; shapes by state and hinge.
    Returns {(state, hinge, part): path} for the room door and {part: path} for the contaminated one."""
    out = {}
    frame, leaf = door_model("room")
    for state in ("closed", "open"):
        model = frame + (leaf if state == "closed" else door_open(leaf))
        for hng in ("l", "r"):
            # r: hinged at the model's west (x 0), on the right as seen from the north face; l: mirrored to the east
            m = model if hng == "r" else mirror_x(model)
            parts = cut(m, 1, 2, 1)
            for j, part in enumerate(("lower", "upper")):
                out[(state, hng, part)] = shape(f"l14-door-{state}-{hng}-{part}", parts[(0, j, 0)])
    cframe, cleaf = door_model("contam")
    parts = cut(cframe + cleaf, 1, 2, 1)
    cont = {part: shape(f"l14-contamdoor-{part}", parts[(0, j, 0)]) for j, part in enumerate(("lower", "upper"))}
    return out, cont


def firedoor_shapes():
    """A fire door's leaf propped open flat against a wall: the wall to the south, the leaf's face to the north, hinge
    knuckles at the west edge (r) or the east (l), a wire-glass panel, a push plate, a rubber wedge under its foot, the
    hold-open magnet on the wall at its top."""
    x1, x2, z1, z2 = 0.6, 15.4, 13.6, 15.4
    els = []
    lt = lambda part: {"north": "door-fire" + part, "south": "door-fire" + part, "all": "door-leafedge"}
    wx1, wx2, wy1, wy2 = 4.0, 12.0, 19.0, 27.0
    els.append(box("LeafLow", (x1, 0.4, z1), (x2, 16, z2), lt("lower")))
    els.append(box("LeafMid", (x1, 16, z1), (x2, wy1, z2), lt("upper")))
    els.append(box("LeafTop", (x1, wy2, z1), (x2, 29.4, z2), lt("upper")))
    els.append(box("LeafW", (x1, wy1, z1), (wx1, wy2, z2), lt("upper")))
    els.append(box("LeafE", (wx2, wy1, z1), (x2, wy2, z2), lt("upper")))
    els += inset_window("Vision", wx1, wy1, wx2, wy2, z1, z2, "door-steel", glass="door-wireglass")
    els.append(box("PushPlate", (11.75, 10.5, z1 - 0.25), (14.25, 17.5, z1), "door-steel", faces=without(DIRS, "south")))
    els += kick_plate("Kick", x1 + 0.5, x2 - 0.5, 0.75, 6.0, z1, "door-steel")
    for i, (a, b) in enumerate(((3.0, 6.5), (13.0, 16.5), (24.0, 27.5))):
        els.append(box(f"Knuckle{i}", (0.0, a, z2 - 0.4), (0.9, b, 16.0), "door-steel"))
    # a closer arm folded along the top, the magnet on the wall that holds it
    els.append(box("Closer", (2.0, 27.8, z1 - 1.2), (8.0, 29.2, z1), "door-steel", faces=without(DIRS, "south")))
    els.append(box("Magnet", (13.0, 27.0, z1 - 1.0), (15.0, 29.0, z1), "door-steel", faces=without(DIRS, "south")))
    els.append(box("Wedge", (12.0, 0, z1 - 2.5), (14.5, 1.0, z1), "rev-floor", faces=without(DIRS, "south", "down")))
    out = {}
    for hng in ("r", "l"):
        m = els if hng == "r" else mirror_x(els)
        parts = cut(m, 1, 2, 1)
        for j, part in enumerate(("lower", "upper")):
            out[(hng, part)] = shape(f"l14-firedoor-{hng}-{part}", parts[(0, j, 0)])
    return out


def hangsign_shape(n):
    """A department sign hung under the hall ceiling on two rods, along x: a panel low in the block, its name on both faces."""
    face = f"sign-hang{n}"
    els = [
        box("Panel", (0.25, 4.0, 7.5), (15.75, 12.0, 8.5), {"north": face, "south": face, "all": "sign-rod"}, uv=(0, 0, 16, 16)),
        box("Rail", (0.0, 12.0, 7.25), (16.0, 12.75, 8.75), "sign-rod"),
    ]
    for f in ("east", "west", "up", "down"):
        els[0]["faces"][f]["uv"] = [0, 0, 1, 8]
    for i, x in enumerate((3.0, 13.0)):
        els.append(box(f"Rod{i}", (x - 0.3, 12.75, 7.7), (x + 0.3, 16.0, 8.3), "sign-rod", faces=("north", "south", "east", "west")))
        els.append(box(f"Plate{i}", (x - 1.0, 15.6, 7.0), (x + 1.0, 16.0, 9.0), "sign-rod", faces=("north", "south", "east", "west", "down")))
        # round 4: a clamp where each rod takes the rail, and a turnbuckle half way up
        els.append(box(f"Clamp{i}", (x - 0.7, 12.0, 7.0), (x + 0.7, 13.3, 9.0), "rail-steel", faces=("north", "south", "east", "west", "up")))
        els.append(box(f"Buckle{i}", (x - 0.5, 14.0, 7.5), (x + 0.5, 14.9, 8.5), "rail-steel", faces=("north", "south", "east", "west")))
    # round 4: an aluminium edge round the panel, proud of both faces
    for nm, frm, to in (("EdgeB", (0.0, 3.6, 7.3), (16.0, 4.1, 8.7)), ("EdgeW", (0.0, 4.1, 7.3), (0.4, 12.0, 8.7)),
                        ("EdgeE", (15.6, 4.1, 7.3), (16.0, 12.0, 8.7))):
        els.append(box(nm, frm, to, "rail-steel"))
    els[0]["_uv"] = True
    return shape(f"l14-hangsign-{n}", finish(els))


def sagging_shape():
    """A patch of floor giving way: the sheet's edge slabs tilted down toward a hole, broken pieces sunk in it, black
    showing in the gaps."""
    els = [box("Void", (0, 0, 0), (16, 9, 16), {"all": "floor-edge", "up": "floor-void"})]
    v = "floor-sagvinyl"
    sl = {"up": v, "all": "floor-edge"}
    # edge slabs: hinged on the block's edge, falling toward the middle
    els.append(box("SlabN", (0, 12, 0), (16, 16, 4.5), sl, rot=(15, 0, 0), origin=(8, 16, 0)))
    els.append(box("SlabS", (0, 12, 11.5), (16, 16, 16), sl, rot=(-15, 0, 0), origin=(8, 16, 16)))
    els.append(box("SlabW", (0, 12, 4.6), (4.5, 16, 11.4), sl, rot=(0, 0, -17), origin=(0, 16, 8)))
    els.append(box("SlabE", (11.5, 12, 4.6), (16, 16, 11.4), sl, rot=(0, 0, 17), origin=(16, 16, 8)))
    # pieces sunk in the middle, tilted every way
    for i, (a, b, c, d, y, r) in enumerate(((4.8, 4.8, 8.2, 8.0, 12.2, (12, 0, 0)), (8.6, 5.0, 11.2, 8.6, 11.6, (0, 0, -16)),
                                            (4.9, 8.6, 7.6, 11.2, 11.2, (0, 0, 14)), (8.2, 9.2, 11.0, 11.2, 12.4, (-10, 0, 0)))):
        els.append(box(f"Piece{i}", (a, y - 3, b), (c, y, d), sl, rot=r, origin=((a + c) / 2, y, (b + d) / 2)))
    for e in els:
        for f, fc in e["faces"].items():
            if f == "up":
                fc["uv"] = [round(e["from"][0], 3), round(e["from"][2], 3), round(e["to"][0], 3), round(e["to"][2], 3)]
    return shape("l14-floor-sagging", finish(els))


def revolving_model():
    """The reception's revolving door, 3 x 3 x 2 blocks (x 0-48, y 0-48, z 0-32), the room to the north: a drum of
    radius 16 on the wall line (z 16), its curved sides leaded stained glass between bronze rails, four wings of dark
    glass on a bronze post turned to 45 degrees, a bronze canopy over it, green marble round it in the wall line, and
    black inside and behind."""
    els = []
    C = (24.0, 16.0)
    R = 16.0
    hw = R * math.tan(math.radians(11.25))  # half a facet of the sixteen-sided drum
    # the curved sides: five facets a side, east (45..135) and west (225..315)
    for side, phis, glass in (("E", (45, 67.5, 90, 112.5, 135), "rev-glasse"), ("W", (225, 247.5, 270, 292.5, 315), "rev-glassw")):
        for i, phi in enumerate(phis):
            k = 4 - i  # the lancets left to right as seen from outside
            uv = (k * 3.2, 0, (k + 1) * 3.2, 16)
            els.append(ring(f"Glass{side}{i}", phi, R - 0.5, R, hw + 0.02, 3, 34, glass, "rev-black", "rev-bronze", uv=uv, glow=70))
            els.append(ring(f"Kick{side}{i}", phi, R - 0.9, R + 0.4, hw + 0.15, 0, 3, "rev-bronze", "rev-black", "rev-bronze"))
            els.append(ring(f"Top{side}{i}", phi, R - 0.9, R + 0.4, hw + 0.15, 34, 36, "rev-bronze", "rev-black", "rev-bronze"))
    # the wings: four arms at 45 degrees, dark glass in bronze, a push bar across each face
    for j, phi in enumerate((45, 135, 225, 315)):
        els.append(ring(f"Wing{j}", phi, 1.3, 14.8, 0.25, 3, 33, "rev-bronze", "rev-bronze", "rev-bronze"))
        # the glass faces of a radial wing are its sides: east/west of the box built along z
        w = els[-1]
        for f in ("east", "west"):
            if f in w["faces"]:
                w["faces"][f]["texture"] = "#rev-dark"
        els.append(ring(f"WingKick{j}", phi, 1.3, 14.8, 0.45, 0, 3, "rev-bronze", "rev-bronze", "rev-bronze"))
        els.append(ring(f"WingTop{j}", phi, 1.3, 14.8, 0.45, 33, 35, "rev-bronze", "rev-bronze", "rev-bronze"))
        els.append(ring(f"WingEdge{j}", phi, 14.0, 15.3, 0.5, 0, 35, "rev-bronze", "rev-bronze", "rev-bronze"))
        for s in (-1, 1):
            els.append(ring(f"Push{j}{'ab'[s > 0]}", phi, 4.0, 13.0, 0.3, 16.5, 17.5, "rev-bronze", "rev-bronze", "rev-bronze", lateral=s * 1.1))
    # round 4: a bronze threshold ring across the open front, and the canopy's frieze all round
    for i, phi in enumerate((337.5, 0, 22.5)):
        els.append(ring(f"Threshold{i}", phi, R - 0.9, R + 0.3, hw + 0.05, 0, 0.45, "rev-bronze", "rev-bronze", "rev-bronze"))
    for i in range(16):
        phi = i * 22.5
        if 112.5 < phi < 247.5:
            continue  # the back half is in the wall
        els.append(ring(f"Frieze{i}", phi, R + 1.4, R + 1.85, (R + 1.5) * math.tan(math.radians(11.25)) + 0.05, 37.2, 41.2,
                        "rev-frieze", "rev-black", "rev-bronze"))
    # the post
    els.append(box("Post", (C[0] - 1.3, 0, C[1] - 1.3), (C[0] + 1.3, 36, C[1] + 1.3), "rev-bronze"))
    els.append(box("PostB", (C[0] - 1.3, 0.01, C[1] - 1.3), (C[0] + 1.3, 35.99, C[1] + 1.3), "rev-bronze", rot=(0, 45, 0), origin=(C[0], 0, C[1])))
    # the floor inside and the ceiling over it: dark
    els.append(box("Mat", (C[0] - 11.3, 0, C[1] - 11.3), (C[0] + 11.3, 0.3, C[1] + 11.3), "rev-floor", faces=("up",)))
    els.append(box("Sill", (C[0] - 9.5, 0, 0.6), (C[0] + 9.5, 0.4, 3.2), "rev-bronze", faces=("up", "north")))
    els.append(box("Beyond", (C[0] - 9.5, 0, 29.6), (C[0] + 9.5, 36, 30.0), "rev-black", faces=("north",)))
    # the canopy: a sixteen-sided bronze drum over it, its underside black
    Rc = R + 1.5
    w = Rc * math.tan(math.radians(11.25))
    ANG = (0, 22.5, 45, 67.5, 90, -67.5, -45, -22.5)
    for i, a in enumerate(ANG):
        dy = 0.02 * i
        for k in range(5):
            l1, l2 = -Rc + k * 2 * Rc / 5, -Rc + (k + 1) * 2 * Rc / 5
            faces = ("up", "down") + (("north",) if k == 0 else ()) + (("south",) if k == 4 else ())
            e = box(f"Canopy{i}_{k}", (C[0] - w, 36 - dy, C[1] + l1), (C[0] + w, 43 + dy, C[1] + l2),
                    {"up": "rev-bronze", "down": "rev-black", "all": "rev-bronze"}, faces=faces,
                    rot=(0, a, 0) if a else None, origin=(C[0], 36, C[1]))
            els.append(e)
    for i, a in enumerate(ANG):
        e = box(f"Cornice{i}", (C[0] - w - 0.3, 41.5, C[1] - Rc - 0.6), (C[0] + w + 0.3, 43.5, C[1] - Rc + 0.4), "rev-bronze",
                faces=("north", "up", "down"), rot=(0, a, 0) if a else None, origin=(C[0], 41.5, C[1]))
        els.append(e)
        e = box(f"CorniceB{i}", (C[0] - w - 0.3, 41.5, C[1] + Rc - 0.4), (C[0] + w + 0.3, 43.5, C[1] + Rc + 0.6), "rev-bronze",
                faces=("south", "up", "down"), rot=(0, a, 0) if a else None, origin=(C[0], 41.5, C[1]))
        els.append(e)
    # the wall line round it: green marble, a bronze band at the drum's edge, the marble over the canopy
    mb = {"all": "rev-marble"}
    els.append(box("WallW", (0, 0, 16), (8.6, 48, 32), mb, faces=("north", "up", "east")))
    els.append(box("WallE", (39.4, 0, 16), (48, 48, 32), mb, faces=("north", "up", "west")))
    els.append(box("WallTop", (8.6, 36, 16), (39.4, 48, 32), mb, faces=("north", "up")))
    for s, x in (("W", 8.6), ("E", 39.4)):
        els.append(box(f"Jamb{s}", (x - 0.8, 0, 15.2), (x + 0.8, 44, 17.2), "rev-bronze", faces=("north", "east", "west", "up")))
    # black behind the glass where the drum leaves the wall's corners open
    els.append(box("BackW", (8.6, 0, 31.5), (16, 36, 32), "rev-black", faces=("north",)))
    els.append(box("BackE", (32, 0, 31.5), (39.4, 36, 32), "rev-black", faces=("north",)))
    return els


REV_COLS = {0: 2, 1: 1, 2: 0}  # column (left to right as seen from the room, facing south) -> the model's x block
REV_ROWS = {"front": 0, "back": 1}
REV_TIERS = ("lower", "middle", "upper")


def revolving_shapes():
    parts = cut(revolving_model(), 3, 3, 2)
    out = {}
    for col, ix in REV_COLS.items():
        for row, iz in REV_ROWS.items():
            for iy, tier in enumerate(REV_TIERS):
                els = parts[(ix, iy, iz)]
                if not els:
                    els = [box("Nothing", (7.9, 7.9, 7.9), (8.1, 8.1, 8.1), "rev-black", faces=("up",))]
                out[(col, row, tier)] = shape(f"l14-revolving-{col}-{row}-{tier}", els)
    return out


# ======================================================================== Block types

def cuboid(b, angle=0):
    c = {"x1": b[0], "y1": b[1], "z1": b[2], "x2": b[3], "y2": b[4], "z2": b[5]}
    if angle:
        c["rotateY"] = angle
    return c


def turned_box(b, side):
    """A box (x1, y1, z1, x2, y2, z2 in 0..1) of a model facing north, as it lies when the model is turned to face side."""
    x1, y1, z1, x2, y2, z2 = b
    for _ in range({"north": 0, "east": 1, "south": 2, "west": 3}[side]):
        x1, z1, x2, z2 = 1 - z2, x1, 1 - z1, x2
    return {"x1": round(x1, 4), "y1": y1, "z1": round(z1, 4), "x2": round(x2, 4), "y2": y2, "z2": round(z2, 4)}


FULL = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}


def lift_shapes():
    """Round 4: a hospital lift in a hall wall (our invention: a "well-equipped hospital"), two blocks wide and three
    high: l / r halves (left and right seen from the hall), lower / upper / header; its doors shut, a dead indicator."""
    out = {}
    for half in ("l", "r"):
        for part in ("lower", "upper", "header"):
            els = R4.lift_model(half, part)
            keys = shape_keys(els)
            write_json(os.path.join(SHAPES, f"l14-lift-{half}-{part}.json"),
                       {"textureWidth": 16, "textureHeight": 16, "textures": {k: T(k) for k in keys}, "elements": els})
            out[(half, part)] = T(f"l14-lift-{half}-{part}")
    return out


def walldeco_shapes(bboxes):
    """Round 4: the wall decorations' models (gen_14_r4.deco_model), one a kind; returns {kind: shape path}."""
    out = {}
    ext = R4.ext_textures()
    for name, bbox in list(bboxes.items()) + [("deco-monarm", None)]:  # round 4: the ICU's monitor on its arm (no picture)
        kind = name[len("deco-"):]
        els = R4.deco_model(kind, bbox)
        keys = shape_keys(els)
        textures = {k: (ext[k] if k in ext else T("wall-paint") if k == "wall" else T(k)) for k in keys}
        write_json(os.path.join(SHAPES, f"l14-walldeco-{kind}.json"),
                   {"textureWidth": 16, "textureHeight": 16, "textures": textures, "elements": els})
        out[kind] = T(f"l14-walldeco-{kind}")
    return out


def blocktypes(rail, windows, doors, contam, revolving, fire, hang, sag, deco_shapes):
    # ---- walls
    walls = ["paint", "paintscuff", "paintbase", "white", "whitebase", "tile", "tilebase", "padded", "cinder", "plywood", "rust",
             "rustblood", "tileblood", "mould", "whitemoss", "concrete", "lintel"]
    write_json(os.path.join(BLOCKS, "l14-wall.json"), {
        "code": "l14-wall", "variantgroups": [{"code": "kind", "states": walls}],
        "texturesByType": {f"*-{k}": {"all": tex("wall-" + k)} for k in walls},
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterialByType": {"*-plywood": "Wood", "*-rust": "Metal", "*-rustblood": "Metal", "*-lintel": "Metal", "*-padded": "Cloth",
                                "*": "Stone"},
        "drawtype": "cube", "lightAbsorption": 99, "resistance": 6, "drops": [],
        "soundsByType": {"*-plywood": WOOD, "*-rust": METAL, "*-rustblood": METAL, "*-lintel": METAL, "*-padded": CLOTH, "*": STONE}},
        "Level 14: the halls' mint paint (paint, scuffed, the teal-green wainscot with its kick strip at the foot), the inpatient units' "
        "white (and its foot), white wall tile (and its green foot), the behaviour cells' padding, painted cinderblock, patched plywood, "
        "corroded steel (and with blood run down it), filthy tiles with blood run down them, mould, white with moss creeping up, bare "
        "concrete, a doorway's steel frame head (lintel)")

    # ---- the rails
    shapes, coll = {}, {}
    for kind in ("paint", "white"):
        for s in SIDES:
            shapes[f"*-{kind}-{s}"] = {"base": rail[kind], "rotateY": ROTATE[s]}
    write_json(os.path.join(BLOCKS, "l14-rail.json"), {
        "code": "l14-rail", "variantgroups": [{"code": "kind", "states": ["paint", "white"]}, {"code": "side", "states": SIDES}],
        "shapeByType": shapes, "creativeinventory": {"general": ["*-paint-north", "*-white-north"], "backrooms": ["*-paint-north", "*-white-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99,
        "collisionbox": FULL, "selectionbox": FULL, "resistance": 6, "drops": [], "sounds": STONE},
        "Level 14: the foot of a hall wall (the wainscot, or the white units' foot) with a handrail on brackets and a bumper strip "
        "proud of its face, toward its side")

    # ---- wall decorations (round 4: models proud of the wall, on the wall's own material)
    deco = list(deco_shapes)
    shapes, tbt = {}, {}
    for k in deco:
        for sd in SIDES:
            shapes[f"l14-walldeco-{k}-*-{sd}"] = {"base": deco_shapes[k], "rotateY": ROTATE[sd]}
    for w in R4.DECO_WALLS:
        for sd in SIDES:
            tbt[f"*-{w}-{sd}"] = {"wall": tex("wall-" + w)}
    allowed = [f"l14-walldeco-*-{w}-*" for w in ("paint", "white", "tile")] + [f"l14-walldeco-{k}-*" for k in R4.DECALS]
    write_json(os.path.join(BLOCKS, "l14-walldeco.json"), {
        "code": "l14-walldeco", "variantgroups": [{"code": "kind", "states": deco}, {"code": "wall", "states": R4.DECO_WALLS},
                                                  {"code": "side", "states": SIDES}],
        "allowedVariants": allowed, "shapeByType": shapes, "texturesByType": tbt,
        "creativeinventory": {"general": ["*-paint-north"], "backrooms": ["*-paint-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99,
        "collisionbox": FULL, "selectionbox": FULL, "resistance": 6, "drops": [], "sounds": STONE,
        "lightHsvByType": {"*-xray-*": [34, 1, 5], "*-exitsign-*": [22, 6, 4]}},
        "Level 14: a wall block (of the wall's own material: <wall>) with a decoration on the face toward its side: the rooms' name "
        "plates, the halls' department signs, children's and health posters, a stopped clock, a ward whiteboard with its tray, an "
        "X-ray light box (lit), blood smeared and running down, a mould bloom, scratches, an EXIT box sign (lit), a hand gel "
        "dispenser, the mod's extinguisher, the T.14.R.G. stencil")

    # ---- windows
    shapes = {}
    for part in ("lower", "upper"):
        for st in ("broken", "shattered"):
            for s in SIDES:
                shapes[f"*-{part}-{st}-*-{s}"] = {"base": windows[(part, st)], "rotateY": ROTATE[s]}
    # round 4: the wall round the window in the wall's own material (paint, the inpatient white, tile)
    win_walls = ["paint", "white", "tile"]
    tbt = {f"*-{w}-{s}": {"wall-paint": tex("wall-" + w)} for w in win_walls for s in SIDES}
    write_json(os.path.join(BLOCKS, "l14-window.json"), {
        "code": "l14-window", "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "state", "states": ["broken", "shattered"]},
                                                {"code": "wall", "states": win_walls}, {"code": "side", "states": SIDES}],
        "shapeByType": shapes, "texturesByType": tbt,
        "creativeinventory": {"general": ["*-lower-broken-white-north", "*-upper-broken-white-north"],
                              "backrooms": ["*-lower-broken-white-north", "*-upper-broken-white-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99,
        "collisionbox": FULL, "selectionbox": FULL, "resistance": 6, "drops": [], "sounds": STONE},
        "Level 14: a wall block with a window in the face toward its side (lower, upper; broken: shards left in the frame, shattered: "
        "almost none), and on the other side of it nothing but black")

    # ---- floors
    floors = ["vinyl", "vinylworn", "vinylborder", "white", "pink", "theatre", "terrazzo", "concrete", "marble", "marbleshattered", "blood",
              "mould", "contam", "cracked", "sagging", "line-ns", "line-we", "arrow-n", "arrow-e", "arrow-s", "arrow-w"]
    tbt = {f"*-{k}": {"all": tex("floor-" + k)} for k in floors if k != "sagging"}
    write_json(os.path.join(BLOCKS, "l14-floor.json"), {
        "code": "l14-floor", "variantgroups": [{"code": "kind", "states": floors}],
        "drawtypeByType": {"*-sagging": "json", "*": "cube"}, "shapeByType": {"*-sagging": {"base": sag}},
        "texturesByType": tbt, "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Stone",
        "sidesolidByType": {"*-sagging": {"all": False, "down": True}, "*": {"all": True}},
        "sideopaqueByType": {"*-sagging": {"all": False, "down": True}, "*": {"all": True}},
        "collisionboxByType": {"*-sagging": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.8125, "z2": 1}, "*": FULL},
        "selectionboxByType": {"*-sagging": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}, "*": FULL},
        "lightAbsorptionByType": {"*-contam": 0, "*": 99}, "lightHsvByType": {"*-contam": [16, 6, 3]},
        "vertexFlagsByType": {"*-contam": {"glowLevel": 50}},
        "resistance": 6, "drops": [], "sounds": STONE},
        "Level 14: the halls' sheet vinyl (worn; the darker band by the walls), the inpatient units' white, the maternity units' pink, the "
        "theatres' epoxy, the reception's terrazzo, concrete, white marble (shattered), blood, mould, a contaminated stain (glowing "
        "faintly), cracked (the warning), sagging (giving way: sunk, black in its gaps), the red way line and its arrows")

    # ---- ceilings
    ceil = ["tile", "stained", "on", "bright", "lit", "flicker", "off", "hole", "blood", "mould", "plaster", "concrete"]
    look = {"tile": "ceil-tile", "stained": "ceil-stained", "on": "ceil-troffer", "bright": "ceil-bright", "lit": "ceil-troffer",
            "flicker": "ceil-troffer", "off": "ceil-off", "hole": "ceil-hole", "blood": "ceil-blood", "mould": "ceil-mould",
            "plaster": "ceil-plaster", "concrete": "ceil-concrete"}
    tbt = {}
    for k, t in look.items():
        tbt[f"*-{k}"] = {"all": tex("ceil-tile"), "down": tex(t)} if k in ("on", "bright", "lit", "flicker", "off", "hole") else {"all": tex(t)}
    hum = dict(GLASS, ambient="backrooms:ambient/hum", ambientBlockCount=140)
    write_json(os.path.join(BLOCKS, "l14-ceiling.json"), {
        "code": "l14-ceiling", "variantgroups": [{"code": "kind", "states": ceil}], "texturesByType": tbt,
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Stone", "drawtype": "cube", "resistance": 2,
        "lightHsvByType": {"*-on": [34, 1, 16], "*-bright": [34, 1, 20]},
        "lightAbsorptionByType": {"*-on": 0, "*-bright": 0, "*-lit": 0, "*-flicker": 0, "*": 99},
        "vertexFlagsByType": {"*-on": {"glowLevel": 200}, "*-bright": {"glowLevel": 230}, "*-lit": {"glowLevel": 200}, "*-flicker": {"glowLevel": 200}},
        "entityClassByType": {"*-flicker": "BackroomsFlicker"},
        "attributesByType": {"*-flicker": {"offBlock": "backrooms:l14-ceiling-off"}},
        "drops": [],
        "soundsByType": {"*-on": hum, "*-bright": hum, "*-lit": hum, "*": STONE}},
        "Level 14: acoustic ceiling tiles (water-stained), the troffers (on: cool white light; bright: the inpatient units' blinding "
        "white; lit: only looks it; flicker; off), a missing tile (black), blood soaked through, mould, plaster, concrete")

    # ---- the room door
    shapes, coll = {}, {}
    for st in ("closed", "open", "locked"):
        for hng in ("l", "r"):
            for part in ("lower", "upper"):
                base = doors[("open" if st == "open" else "closed", hng, part)]
                for s in SIDES:
                    shapes[f"*-{st}-{hng}-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
            bx_ = (0, 0, 1 / 16, 1, 1, 2.75 / 16) if st != "open" else (1.35 / 16, 0, 2.65 / 16, 3.1 / 16, 1, 1)
            if hng == "l":
                bx_ = (1 - bx_[3], bx_[1], bx_[2], 1 - bx_[0], bx_[4], bx_[5])
            for s in SIDES:
                coll[f"*-{st}-{hng}-*-{s}"] = [turned_box(bx_, s)]
    write_json(os.path.join(BLOCKS, "l14-door.json"), {
        "code": "l14-door",
        "variantgroups": [{"code": "state", "states": ["closed", "open", "locked"]}, {"code": "hinge", "states": ["l", "r"]},
                          {"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-closed-l-lower-north"], "backrooms": ["*-closed-l-lower-north"]},
        "behaviors": [{"name": "BackroomsSuburbDoor"}],
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shapes, "collisionSelectionBoxesByType": coll,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 1, "resistance": 3, "drops": [], "sounds": WOOD},
        "Level 14: a hospital room door (closed, open, locked; hinged on the left or right as seen from the side its leaf is toward; "
        "lower, upper): pale laminate, a kick plate, a narrow wire-glass vision panel with dark behind it, a lever handle. Right-click "
        "opens or shuts it; a locked one stays shut")

    shapes = {f"*-{part}-{s}": {"base": contam[part], "rotateY": ROTATE[s]} for part in ("lower", "upper") for s in SIDES}
    write_json(os.path.join(BLOCKS, "l14-contamdoor.json"), {
        "code": "l14-contamdoor", "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-lower-north"], "backrooms": ["*-lower-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shapes,
        "collisionSelectionBoxesByType": {f"*-{s}": [turned_box((0, 0, 1 / 16, 1, 1, 2.75 / 16), s)] for s in SIDES},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "lightHsvByType": {"*-upper-*": [20, 6, 3]}, "resistance": 99999, "drops": [], "sounds": METAL},
        "Level 14: a contaminated room's steel door (lower, upper; its leaf toward its side): a green glow through its square of wire "
        "glass, the trefoil, DO NOT ENTER. It does not open")

    # ---- the revolving door
    shapes = {}
    for (col, row, tier), base in revolving.items():
        for s in SIDES:
            shapes[f"*-{col}-{row}-{tier}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    write_json(os.path.join(BLOCKS, "l14-revolving.json"), {
        "code": "l14-revolving",
        "variantgroups": [{"code": "col", "states": ["0", "1", "2"]}, {"code": "row", "states": ["back", "front"]},
                          {"code": "tier", "states": list(REV_TIERS)}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-1-front-lower-north"], "backrooms": ["*-1-front-lower-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shapes, "collisionbox": FULL, "selectionbox": FULL,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 99999, "drops": [],
        "sounds": GLASS},
        "Level 14: the reception's large stained-glass revolving door, depicting nothing beyond (3 wide: col 0-2 left to right as seen "
        "from the room; 2 deep: back in the wall line, front on the room's floor; 3 high: lower, middle, upper; it faces its side). It "
        "does not turn")

    # ---- the fire door
    shapes, coll = {}, {}
    for (hng, part), base in fire.items():
        for s in SIDES:
            shapes[f"*-{hng}-{part}-{s}"] = {"base": base, "rotateY": ROTATE[s]}
    for s in SIDES:
        coll[f"*-{s}"] = [turned_box((0, 0, 13.4 / 16, 1, 1, 1), s)]
    write_json(os.path.join(BLOCKS, "l14-firedoor.json"), {
        "code": "l14-firedoor", "variantgroups": [{"code": "hinge", "states": ["l", "r"]}, {"code": "part", "states": ["lower", "upper"]},
                                                  {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-l-lower-north"], "backrooms": ["*-l-lower-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shapes, "collisionSelectionBoxesByType": coll,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 4, "drops": [], "sounds": METAL},
        "Level 14: a hall's fire door, propped open flat against the wall behind it, its face toward its side (hinged at the left or "
        "right as seen from its face; lower, upper): red-brown steel, wire glass, FIRE DOOR KEEP SHUT")

    # ---- the hanging signs
    shapes = {}
    for n, base in hang.items():
        shapes[f"*-{n}-we"] = {"base": base}
        shapes[f"*-{n}-ns"] = {"base": base, "rotateY": 90}
    write_json(os.path.join(BLOCKS, "l14-hangsign.json"), {
        "code": "l14-hangsign", "variantgroups": [{"code": "sign", "states": [str(n) for n in range(len(SIGNS))]}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-we"], "backrooms": ["*-we"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shapes, "collisionbox": None,
        "selectionboxByType": {"*-we": cuboid((0, 0.25, 0.44, 1, 1, 0.56)), "*-ns": cuboid((0.44, 0.25, 0, 0.56, 1, 1))},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2, "drops": [], "sounds": METAL},
        "Level 14: a department sign hung from the hall ceiling on two rods, its name on both faces and an arrow (0 WARD 1, 1 INTENSIVE "
        "CARE, 2 SURGERY, 3 MATERNITY, 4 PSYCHIATRY, 5 STORES, 6 RECEPTION, 7 OUTPATIENTS; along x: we, along z: ns)")


def main():
    wall_textures()
    deco_textures()
    deco = walldeco_shapes(R4.deco_cutouts(sys.modules[__name__]))
    R4.lift_textures(sys.modules[__name__])
    lift = lift_shapes()
    floor_textures()
    ceiling_textures()
    model_textures()
    rail = {k: rail_shape(k) for k in ("paint", "white")}
    windows = {(p, s): window_shape(p, s) for p in ("lower", "upper") for s in ("broken", "shattered")}
    doors, contam = door_shapes()
    revolving = revolving_shapes()
    fire = firedoor_shapes()
    hang = {n: hangsign_shape(n) for n in range(len(SIGNS))}
    sag = sagging_shape()
    blocktypes(rail, windows, doors, contam, revolving, fire, hang, sag, deco)
    shapes = {f"*-{h}-{p}-{sd}": {"base": lift[(h, p)], "rotateY": ROTATE[sd]} for h in ("l", "r") for p in ("lower", "upper", "header") for sd in SIDES}
    write_json(os.path.join(BLOCKS, "l14-lift.json"), {
        "code": "l14-lift", "variantgroups": [{"code": "half", "states": ["l", "r"]}, {"code": "part", "states": ["lower", "upper", "header"]},
                                              {"code": "side", "states": SIDES}],
        "shapeByType": shapes, "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]},
        "blockmaterial": "Metal", "drawtype": "json", "sidesolid": {"all": True}, "sideopaque": {"all": True}, "lightAbsorption": 99,
        "collisionbox": FULL, "selectionbox": FULL, "resistance": 8, "drops": [], "sounds": METAL},
        "Level 14: a lift in a hall wall, two wide (l, r seen from the hall) and three high (lower, upper, header), its brushed steel "
        "doors shut and taped, the floor indicator over them dead, a call panel by it. It does not come")
    print("Level 14: textures in", os.path.relpath(TEX, ROOT), "; shapes in", os.path.relpath(SHAPES, ROOT), "; blocktypes in",
          os.path.relpath(BLOCKS, ROOT))


if __name__ == "__main__":
    main()
