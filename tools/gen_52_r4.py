"""Level 52, "The Greenfield Campus": round 4's blocks (2026-11-02, the asset-quality pass), called from gen_52.py's main
after round 3 (it saves and writes through gen_52's own helpers, so its stale-file sweep and its check cover these too).

Multi-block set pieces (each a run of blocks that reads as one object; pieces meet at block edges):
    l52-hoop-{piece}-{side}        a basketball hoop. Outdoors (yard): a steel post on a base plate (pole-base, pole-mid,
                                   pole-neck, pole-top), two parallel arms out to the board (board-yard). In a gym: a braced
                                   truss off the end wall (truss-wall with the wall plate, truss-mid, brace under it) out to
                                   the board (board-gym). The rim and net (rim-yard, rim-gym) hang into the air block in front
                                   of the board, the rim at 3 blocks. side: the way the board faces (into the court).
    l52-mark-{surf}-{cell}-{side}  a court's painted markings as a flat decal over the floor (surf: gym or yard): the key,
                                   the free-throw circle, the three-point arc (cells k<i>_<j> about the hoop), the centre
                                   circle (cells c<i>_<j>)
    l52-score-{part}-{row}-{side}  the gym's scoreboard, three blocks wide and two high (HOME / GUEST, the clock stopped
                                   at 3:52 like the tower's), lit
    l52-wallmat-{row}-{side}       a padded gym wall mat on the wall behind (lower, upper)

Textures are drawn at 32 px a block from matlib's materials (painted and galvanised steel with chips and rust, vinyl
padding with stitching, nylon net cut out to alpha 0), faces with pictures at 64 px a block."""
import math
import random

from PIL import Image, ImageDraw

import gen_52_r3 as R3
import gen_52_tex as T
import matlib as M
from modelkit import box

G = None  # gen_52, set by build()
SIDES = ["north", "east", "south", "west"]
FULL = (0, 0, 16, 16)
P = 64


def save(img, name):
    G.save(img, name)


# ======================================================================== textures

def steel_paint(seed, base, rust=0.0, chips=4):
    img = M.painted_metal(seed, base=base, panel=False, chips=chips, under=(92, 88, 84))
    if rust:
        M.rust(img, amount=rust, seed=seed + 1)
    M.grime(img, amount=0.12, seed=seed + 2, cover=0.4)
    return img


def vinyl(seed, base, seams=True):
    """Padding vinyl: a soft sheen, faint creases, stitched seams at the edges."""
    img = M.noise_hv(base, 3, seed, (32, 32), 4, (16, 8))
    px = img.load()
    rng = random.Random(seed)
    for _ in range(5):
        y = rng.randrange(32)
        x0 = rng.randrange(32)
        for x in range(x0, x0 + rng.randint(4, 9)):
            M.touch(img, x % 32, y, -0.06)
    if seams:
        for k in range(1, 31, 3):
            M.touch(img, k, 2, 0.16)
            M.touch(img, k, 29, 0.16)
            M.touch(img, 2, k, 0.16)
            M.touch(img, 29, k, 0.16)
        M.bevel(img, None, 1, 0.22)
    M.grime(img, amount=0.08, seed=seed + 3, cover=0.35)
    return img


def net_tex(seed, colour, torn=0.0):
    """Nylon net: a diamond mesh of 1 px cords on a 4 px pitch, the holes cut out (alpha 0)."""
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    for y in range(32):
        for x in range(32):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                if torn and rng.random() < torn:
                    continue
                f = rng.uniform(-10, 8) - (y / 32) * 18
                px[x, y] = tuple(max(0, min(255, int(c + f))) for c in colour) + (255,)
    return img


def board_face(kind, seed):
    """A backboard's face at its own aspect (28 x 17 units, drawn 112 x 68): the border, the shooter's square over the rim."""
    w, h = 112, 72
    if kind == "gym":
        img = M.noise_hv((236, 238, 236), 2, seed, (w, h), 2, (16, 8))
        line = (200, 70, 40)
    else:
        img = M.noise_hv((214, 214, 206), 4, seed, (w, h), 5, (16, 8))
        line = (176, 74, 52)
    d = ImageDraw.Draw(img)
    d.rectangle((3, 3, w - 4, h - 4), outline=line + (255,), width=3)
    # The shooter's square: 0.59 m by 0.45 m, its bottom on the rim's top
    sx0, sx1 = w // 2 - 15, w // 2 + 15
    d.rectangle((sx0, h - 34, sx1, h - 9), outline=line + (255,), width=3)
    if kind == "yard":
        M.rust(img, amount=0.12, seed=seed + 1, edges=True)
        M.drips(img, n=7, seed=seed + 2, color=(128, 78, 44), length=(10, 30), strength=0.35, start=6)
        for bx, by in ((10, 10), (w - 11, 10), (10, h - 11), (w - 11, h - 11)):
            d.ellipse((bx - 2, by - 2, bx + 2, by + 2), fill=(120, 116, 110, 255))
        M.grime(img, amount=0.12, seed=seed + 3, cover=0.5)
    else:
        M.grime(img, amount=0.04, seed=seed + 3, cover=0.3)
    return img.resize((P, P), Image.LANCZOS)


def score_face(seed):
    """The scoreboard's face, 3 x 2 blocks drawn 192 x 128: HOME and GUEST over their scores, the clock stopped at 3:52."""
    w, h = 192, 128
    img = M.noise_hv((26, 28, 30), 2, seed, (w, h), 2, (16, 8))
    d = ImageDraw.Draw(img)
    amber, red, white = (255, 176, 40), (240, 52, 36), (230, 232, 230)
    d.rectangle((2, 2, w - 3, h - 3), outline=(70, 72, 76, 255), width=3)
    R3.text(img, "HOME", (10, 10, 58, 26), white, 14)
    R3.text(img, "GUEST", (134, 10, 184, 26), white, 14)
    R3.text(img, "PERIOD", (74, 82, 120, 94), white, 9)

    def panel(x0, y0, x1, y1):
        d.rectangle((x0, y0, x1, y1), fill=(12, 12, 14, 255), outline=(54, 56, 60, 255))

    panel(10, 30, 58, 72)
    panel(134, 30, 182, 72)
    panel(66, 14, 126, 62)
    panel(86, 98, 106, 120)
    R3.text(img, "00", (12, 32, 56, 70), red, 34)
    R3.text(img, "00", (136, 32, 180, 70), red, 34)
    R3.text(img, "3:52", (68, 18, 124, 58), amber, 30)
    R3.text(img, "2", (88, 100, 104, 118), amber, 16)
    # The fouls and the bonus lamps, dark
    for x in (18, 30, 42, 142, 154, 166):
        d.ellipse((x - 3, 82, x + 3, 88), fill=(60, 30, 26, 255))
    # The maker's strip along the bottom, blank, and grime along the top edge
    d.rectangle((40, 108, 72, 116), fill=(44, 46, 50, 255))
    d.rectangle((120, 108, 152, 116), fill=(44, 46, 50, 255))
    M.grime(img, amount=0.06, seed=seed + 1, cover=0.3, bias="top")
    return img


def mat_face(row, seed):
    """A blue gym wall mat (one block of a two-block panel): vinyl, the stitched edge, a seam where panels meet."""
    img = M.noise_hv((44, 74, 138), 3, seed, (32, 32), 4, (16, 8))
    px = img.load()
    for y in range(32):
        M.touch(img, 0, y, -0.25)
        M.touch(img, 31, y, -0.25)
        if y % 3 == 0:
            M.touch(img, 2, y, 0.18)
            M.touch(img, 29, y, 0.18)
    if row == "lower":
        for x in range(32):
            M.touch(img, x, 31, -0.3)
            if x % 3 == 0:
                M.touch(img, x, 29, 0.18)
        M.grime(img, amount=0.2, seed=seed + 2, bias="bottom", cover=0.6)
        # Scuffs where balls and shoes hit it
        rng = random.Random(seed)
        for _ in range(6):
            M.touch(img, rng.randrange(4, 28), rng.randrange(14, 28), -0.12)
    else:
        for x in range(32):
            M.touch(img, x, 0, 0.12)
            if x % 3 == 0:
                M.touch(img, x, 2, 0.18)
    return img


def textures():
    s = save
    s(steel_paint(7001, (52, 58, 66), rust=0.0), "r4-steel-dark")         # gym truss, pole
    s(steel_paint(7002, (40, 66, 58), rust=0.22, chips=7), "r4-steel-green")  # an outdoor post, weathered
    s(steel_paint(7003, (214, 92, 40), chips=6), "r4-rim")                # the rim's orange
    s(steel_paint(7004, (182, 92, 50), rust=0.28, chips=9), "r4-rim-rust")
    s(M.galvanised(7005, base=(160, 164, 166), white_rust=0.15), "r4-galv")
    s(vinyl(7006, (40, 70, 132)), "r4-pad-blue")
    s(vinyl(7007, (36, 38, 42)), "r4-pad-black")
    s(net_tex(7008, (240, 240, 236)), "r4-net")
    s(net_tex(7009, (196, 194, 184), torn=0.18), "r4-net-torn")
    s(board_face("gym", 7010), "r4-board-gym")
    s(board_face("yard", 7011), "r4-board-yard")
    back = M.painted_metal(7012, base=(118, 122, 126), panel=True, chips=3, screws=True)
    s(back, "r4-board-back")
    plate = M.painted_metal(7013, base=(96, 100, 104), panel=True, chips=2, screws=True)
    s(plate, "r4-wallplate")
    conc = M.concrete(7014, base=(150, 148, 142), cracks=1)
    s(conc, "r4-footing")
    bolt = M.noise_hv((120, 118, 112), 3, 7015, (32, 32), 3, (16, 8))
    M.rust(bolt, amount=0.25, seed=7016)
    s(bolt, "r4-bolt")
    # (the cabinet's face is 48 x 28 units: drawn 192 x 128, squeezed to 192 x 112, cut in rows of 56 and each part stretched
    # back to 64 x 64, since every face maps its whole texture)
    sf = score_face(7020).resize((192, 112), Image.LANCZOS)
    for row, y0 in (("hi", 0), ("lo", 56)):
        for part, x0 in (("l", 0), ("m", 64), ("r", 128)):
            s(sf.crop((x0, y0, x0 + 64, y0 + 56)).resize((64, 64), Image.LANCZOS), f"r4-score-{part}-{row}")
    s(steel_paint(7021, (34, 36, 40), chips=2), "r4-cabinet")
    inside = M.painted_metal(7022, base=(70, 72, 74), panel=False, chips=2)
    M.grime(inside, amount=0.25, seed=7023, cover=0.6)
    s(inside, "r4-locker-in")
    for row in ("lower", "upper"):
        s(mat_face(row, 7030 + (row == "upper")), f"r4-mat-{row}")
    # Court markings: drawn per cell below (mark_textures)


# ======================================================================== the hoop

def ring(prefix, cx, y0, y1, cz, r, tex, n=8, thick=0.6, faces=None, side_len=None):
    """An octagon of bars (or of thin planes, thick ~0) round a vertical axis: the rim, the net's courses."""
    L = side_len or 2 * (r + thick / 2) * math.tan(math.pi / n) + 0.25
    els = []
    for k in range(n):
        el = box(f"{prefix}{k}", (cx - L / 2, y0, cz - r - thick), (cx + L / 2, y1, cz - r), tex,
                 faces=faces or ("north", "south", "up", "down"), rot=(0, k * 360 / n, 0) if k else None,
                 origin=(cx, (y0 + y1) / 2, cz))
        els.append(el)
    return els


def net_planes(cx, cz, tex):
    els = []
    for i, (y0, y1, r) in enumerate(((12.4, 15.3, 3.45), (10.0, 12.6, 2.95), (8.0, 10.2, 2.45))):
        L = 2 * r * math.tan(math.pi / 8) + 0.1
        for k in range(8):
            els.append(box(f"Net{i}{k}", (cx - L / 2, y0, cz - r - 0.05), (cx + L / 2, y1, cz - r), tex, faces=("north", "south"),
                           rot=(0, k * 45, 0) if k else None, origin=(cx, (y0 + y1) / 2, cz),
                           uv=(0, 0, round(L, 3), round(y1 - y0, 3))))
    return els


def rim_shape(kind):
    """The rim and its net in the air block in front of the board (rel 3; the rim's top at the block's top, 3 blocks up)."""
    rim = "r4-rim" if kind == "gym" else "r4-rim-rust"
    net = "r4-net" if kind == "gym" else "r4-net-torn"
    cz = 9.9
    els = ring("Rim", 8, 15.1, 15.8, cz, 3.55, rim, thick=0.7, faces=("north", "south", "up", "down", "east", "west"))
    # The mounting plate on the board, the two straps out to the ring and the brace under them
    els += [box("Plate", (5.5, 12.2, 15.3), (10.5, 15.9, 16), rim),
            box("StrapL", (6.4, 15.0, 13.0), (7.2, 15.8, 15.3), rim),
            box("StrapR", (8.8, 15.0, 13.0), (9.6, 15.8, 15.3), rim),
            box("Brace", (7.5, 12.6, 12.8), (8.5, 13.4, 15.6), rim, rot=(-38, 0, 0), origin=(8, 13.0, 15.4)),
            box("Spring", (7.0, 14.0, 14.4), (9.0, 15.0, 15.3), "r4-steel-dark")]
    # The net's hooks under the rim, then the net in three narrowing courses
    for k in range(12):
        a = k * math.pi * 2 / 12
        x, z = 8 + 3.5 * math.sin(a), cz - 3.5 * math.cos(a)
        els.append(box(f"Hook{k}", (x - 0.25, 14.6, z - 0.25), (x + 0.25, 15.1, z + 0.25), "r4-galv"))
    els += net_planes(8, cz, net)
    return els


def board_shape(kind):
    """The backboard in its block (rel 4): the panel 28 units wide and 17 high centred on the block, its front at z = 0
    (the block's north edge), its frame, its bottom pad (gym) or steel lip (yard), the frame behind and the arms or
    truss chords running back to the block's south edge."""
    face = "r4-board-gym" if kind == "gym" else "r4-board-yard"
    edge = "r4-rim" if kind == "gym" else "r4-steel-green"
    els = [box("Panel", (-6, -1.6, 0), (22, 15.2, 1.2), {"front": face, "back": "r4-board-back", "side": edge}, uv=None)]
    els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    els[0]["faces"]["south"]["uv"] = [0, 0, 16, 16]
    # The frame round its face, a little proud
    els += [box("FrameT", (-6.3, 14.6, -0.3), (22.3, 15.5, 1.4), edge), box("FrameB", (-6.3, -1.9, -0.3), (22.3, -1.0, 1.4), edge),
            box("FrameL", (-6.3, -1.0, -0.3), (-5.4, 14.6, 1.4), edge), box("FrameR", (21.4, -1.0, -0.3), (22.3, 14.6, 1.4), edge)]
    if kind == "gym":
        els.append(box("Pad", (-6.4, -3.2, -0.9), (22.4, -1.0, 2.0), "r4-pad-black"))
    # The rim's mount bolted through the board
    els.append(box("Mount", (5.6, -1.0, -0.4), (10.4, 2.2, 0), "r4-rim" if kind == "gym" else "r4-rim-rust"))
    # The frame behind: two uprights, two rails
    st = "r4-steel-dark" if kind == "gym" else "r4-steel-green"
    els += [box("BackL", (2.4, 0.5, 1.2), (3.9, 14.0, 2.6), st), box("BackR", (12.1, 0.5, 1.2), (13.6, 14.0, 2.6), st),
            box("RailT", (1.5, 10.6, 1.2), (14.5, 12.0, 2.6), st), box("RailB", (1.5, 2.6, 1.2), (14.5, 4.0, 2.6), st)]
    if kind == "yard":
        # Two parallel arms back to the post (which stands a block behind, its arms meeting these at the block edge)
        els += [box("ArmT", (7.1, 10.4, 2.6), (8.9, 12.2, 16), st), box("ArmB", (7.1, 2.4, 2.6), (8.9, 4.2, 16), st),
                box("Tie", (7.3, 4.2, 9.0), (8.7, 10.4, 10.2), st)]
    else:
        els += truss_chords(2.6, 16, st)
        els += [box("Cross", (3.0, 12.2, 3.0), (13.0, 13.4, 4.2), st)]
    return els


def truss_chords(z0, z1, st):
    return [box("TopL", (3.0, 12.0, z0), (4.4, 13.4, z1), st), box("TopR", (11.6, 12.0, z0), (13.0, 13.4, z1), st),
            box("BotL", (3.0, 1.6, z0), (4.4, 3.0, z1), st), box("BotR", (11.6, 1.6, z0), (13.0, 3.0, z1), st)]


def truss_shape(part):
    """A block of the gym hoop's truss (rel 4): the four chords, the lacing on each side, a cross-tie; the wall part
    carries the plate bolted to the end wall at its south edge."""
    st = "r4-steel-dark"
    els = truss_chords(0, 15 if part == "wall" else 16, st)
    ang = math.degrees(math.atan2(10.4, 15.0))
    for x0, n in ((3.1, "L"), (11.7, "R")):
        els.append(box(f"Lace{n}", (x0, 7.4 - 0.6, 8 - 9.1), (x0 + 1.2, 7.4 + 0.6, 8 + 9.1), st, rot=(ang if part == "mid" else -ang, 0, 0),
                       origin=(x0 + 0.6, 7.4, 8)))
    els += [box("TieT", (4.4, 12.2, 7.2), (11.6, 13.2, 8.4), st), box("TieB", (4.4, 1.8, 7.2), (11.6, 2.8, 8.4), st)]
    if part == "wall":
        els.append(box("Plate", (1.0, 0.0, 15.0), (15.0, 15.0, 16.0), "r4-wallplate"))
        for bx in (2.2, 13.0):
            for by in (1.2, 12.8):
                els.append(box(f"Bolt{bx}{by}", (bx, by, 14.4), (bx + 0.8, by + 0.8, 15.0), "r4-bolt"))
    return els


def brace_shape():
    """Under the truss at the wall (rel 3): two struts from low on the wall up to the bottom chords, their foot plate."""
    st = "r4-steel-dark"
    ang = math.degrees(math.atan2(11.0, 14.0))
    els = [box("Foot", (2.0, 1.0, 15.0), (14.0, 5.0, 16.0), "r4-wallplate")]
    for x0, n in ((3.1, "L"), (11.7, "R")):
        L = math.hypot(11.0, 14.0)
        els.append(box(f"Strut{n}", (x0, 10.0 - L / 2, 9.5 - 0.6), (x0 + 1.2, 10.0 + L / 2, 9.5 + 0.6), st, rot=(-ang, 0, 0),
                       origin=(x0 + 0.6, 10.0, 9.5)))
    return els


def pole_shape(part):
    """The outdoor hoop's post, a block behind the board: a square steel post on a base plate (base), its pad (base,
    mid), the post (neck), its cap and the two arms out to the board (top)."""
    st = "r4-steel-green"
    els = []
    if part == "base":
        els += [box("Plate", (3.5, 0, 3.5), (12.5, 0.8, 12.5), "r4-steel-green"),
                box("Footing", (2.5, -0.01, 2.5), (13.5, 0.3, 13.5), "r4-footing", faces=("north", "east", "south", "west", "up"))]
        for bx in (4.2, 10.8):
            for bz in (4.2, 10.8):
                els += [box(f"Nut{bx}{bz}", (bx - 0.6, 0.8, bz - 0.6), (bx + 0.6, 1.5, bz + 0.6), "r4-bolt")]
        els += [box("Gusset1", (7.6, 0.8, 4.0), (8.4, 3.5, 6.5), st), box("Gusset2", (7.6, 0.8, 9.5), (8.4, 3.5, 12.0), st),
                box("Gusset3", (4.0, 0.8, 7.6), (6.5, 3.5, 8.4), st), box("Gusset4", (9.5, 0.8, 7.6), (12.0, 3.5, 8.4), st)]
    els.append(box("Post", (6.4, 0 if part != "base" else 0.8, 6.4), (9.6, 16 if part != "top" else 13.0, 9.6), st))
    if part in ("base", "mid"):
        y0, y1 = (4.0, 16.0) if part == "base" else (0.0, 10.0)
        els.append(box("Pad", (5.6, y0, 5.6), (10.4, y1, 10.4), "r4-pad-blue"))
        els += [box("Strap", (5.4, y1 - 2.4, 5.4), (10.6, y1 - 1.6, 10.6), "r4-pad-black")]
        if part == "base":
            els.append(box("Strap0", (5.4, y0 + 1.0, 5.4), (10.6, y0 + 1.8, 10.6), "r4-pad-black"))
    if part == "top":
        els += [box("Cap", (6.0, 13.0, 6.0), (10.0, 13.8, 10.0), st),
                box("ArmT", (7.1, 10.4, 0), (8.9, 12.2, 6.4), st), box("ArmB", (7.1, 2.4, 0), (8.9, 4.2, 6.4), st),
                box("CollarT", (6.0, 10.0, 6.0), (10.0, 12.6, 10.0), st), box("CollarB", (6.0, 2.0, 6.0), (10.0, 4.6, 10.0), st)]
        ang = math.degrees(math.atan2(8.0, 6.0))
        els.append(box("Strut", (7.4, 7.0 - 5.0, 3.0 - 0.5), (8.6, 7.0 + 5.0, 3.0 + 0.5), st, rot=(ang, 0, 0), origin=(8, 7.0, 3.0)))
    if part == "neck":
        # A rusty run-off from the collar, a stencilled height mark
        els.append(box("Band", (6.2, 6.0, 6.2), (9.8, 6.6, 9.8), "r4-galv"))
    return els


# ======================================================================== court markings

LANE_HALF = 2.45      # the key: 4.9 wide
FT_LINE = 5.8         # the free-throw line, from the baseline
FT_R = 1.8
ARC_R = 6.75
CORNER = 6.6
RIM_IN = 0.88         # the rim's centre, in from the baseline (the board half a block in, the rim in front of it)
CENTRE_R = 1.8
LINE_W = 0.07         # in blocks


def court_paint(surf):
    """(line colour, key fill colour) for a surface."""
    if surf == "gym":
        return (44, 76, 156), (176, 120, 64)
    return (232, 228, 218), (64, 104, 82)


def key_cells():
    """The cells (i across, j along) the hoop's markings touch, and for each a function that says what a point is."""
    def at(X, Y):
        # X across (0.5 the hoop's axis), Y along from the baseline tile's near edge (baseline at 0.5)
        x = X - 0.5
        y = Y - 0.5
        if y < 0.06:
            return None
        line = None
        # The key's sides and the free-throw line
        if abs(abs(x) - LANE_HALF) < LINE_W / 2 and y <= FT_LINE:
            line = "line"
        if abs(y - FT_LINE) < LINE_W / 2 and abs(x) <= LANE_HALF:
            line = "line"
        # The free-throw circle (the outer half)
        r = math.hypot(x, y - FT_LINE)
        if abs(r - FT_R) < LINE_W / 2 and y >= FT_LINE:
            line = "line"
        # The three-point line: the corner straights, then the arc round the rim
        ry = y - RIM_IN
        yc = math.sqrt(ARC_R ** 2 - CORNER ** 2)
        if abs(abs(x) - CORNER) < LINE_W / 2 and ry <= yc:
            line = "line"
        if ry > yc and abs(math.hypot(x, ry) - ARC_R) < LINE_W / 2:
            line = "line"
        if line:
            return line
        if abs(x) < LANE_HALF and y < FT_LINE:
            return "fill"
        return None
    return at


def centre_at(X, Y):
    r = math.hypot(X - 0.5, Y - 0.5)
    if abs(r - CENTRE_R) < LINE_W / 2:
        return "line"
    return None


def cell_texture(fn, i, j, surf, seed):
    """The decal for cell (i, j): pixel (px, py) is the point X = i + px/32, Y = j + 1 - py/32 (the up face: +x east,
    +z south, so north, the court's way in, is up the picture)."""
    line, fill = court_paint(surf)
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    any_ = False
    for py in range(32):
        for pxx in range(32):
            hits = 0
            kind = None
            for sx in (0.25, 0.75):
                for sy in (0.25, 0.75):
                    k = fn(i + (pxx + sx) / 32, j + 1 - (py + sy) / 32)
                    if k == "line":
                        hits += 1
                        kind = "line"
                    elif k == "fill" and kind is None:
                        kind = "fill"
            if hits >= 2 or (kind == "line" and hits >= 1 and rng.random() < 0.5):
                c = line
            elif kind == "fill":
                c = fill
            else:
                continue
            f = rng.uniform(-7, 7)
            # Worn paint: a few flecks show the floor through
            if surf == "yard" and rng.random() < 0.05:
                continue
            px[pxx, py] = tuple(max(0, min(255, int(v + f))) for v in c) + (255,)
            any_ = True
    return img if any_ else None


MARK_CELLS = {}  # surf -> {cell name: (i, j)}


def mark_textures():
    """Draws every non-empty cell for both surfaces; keeps the list for the blocktype and the layout's table."""
    at = key_cells()
    for surf in ("gym", "yard"):
        cells = {}
        for j in range(0, 9):
            for i in range(-7, 8):
                img = cell_texture(at, i, j, surf, 7100 + (i + 7) * 13 + j * 211 + (surf == "yard") * 5000)
                if img is not None:
                    name = f"k{i + 7}_{j}"
                    save(img, f"r4-mark-{surf}-{name}")
                    cells[name] = (i, j)
        for j in range(-2, 3):
            for i in range(-2, 3):
                img = cell_texture(centre_at, i, j, surf, 7900 + (i + 2) * 7 + (j + 2) + (surf == "yard") * 5000)
                if img is not None:
                    name = f"c{i + 2}_{j + 2}"
                    save(img, f"r4-mark-{surf}-{name}")
                    cells[name] = (i, j)
        MARK_CELLS[surf] = cells


# ======================================================================== blocktypes

def blocktypes():
    shapes = {}
    for kind in ("gym", "yard"):
        shapes[f"l52-hoop-rim-{kind}"] = G.shape(f"l52-hoop-rim-{kind}", rim_shape(kind))
        shapes[f"l52-hoop-board-{kind}"] = G.shape(f"l52-hoop-board-{kind}", board_shape(kind))
    for part in ("wall", "mid"):
        shapes[f"l52-hoop-truss-{part}"] = G.shape(f"l52-hoop-truss-{part}", truss_shape(part))
    shapes["l52-hoop-brace"] = G.shape("l52-hoop-brace", brace_shape())
    for part in ("base", "mid", "neck", "top"):
        shapes[f"l52-hoop-pole-{part}"] = G.shape(f"l52-hoop-pole-{part}", pole_shape(part))

    def coll(p):
        if "pole" in p:
            return (0.33, 0, 0.33, 0.67, 1, 0.67)
        if "rim" in p:
            return (0.25, 0.9, 0.35, 0.75, 1, 0.98)
        return sel(p)

    def sel(p):
        if "pole" in p:
            return (0.33, 0, 0.33, 0.67, 1, 0.67)
        if "board" in p:
            return (0, 0, 0, 1, 1, 0.2)
        if "rim" in p:
            return (0.25, 0.5, 0.35, 0.75, 1, 1)
        return (0.15, 0, 0, 0.85, 1, 1)

    pieces = ["rim-gym", "rim-yard", "board-gym", "board-yard", "truss-wall", "truss-mid", "brace", "pole-base", "pole-mid", "pole-neck", "pole-top"]
    R3.oriented("l52-hoop", [G.group("piece", pieces), G.group("side", SIDES)], {f"l52-hoop-{p}": shapes[f"l52-hoop-{p}"] for p in pieces},
                "Level 52: a basketball hoop built of several blocks, the board facing the way of its side: outdoors a padded steel post "
                "(pole-base to pole-top) a block behind the board with two arms out to it; in a gym a braced truss off the end wall "
                "(truss-wall, truss-mid, brace); the board (board-*) a block up from the rim, the rim and net (rim-*) hanging in the "
                "air in front of the board, the rim at 3 blocks", "Metal", G.METAL, coll, sel=sel)

    # Court markings: one flat shape, its texture per cell
    mk = G.shape("l52-mark", [box("Paint", (0, 0, 0), (16, 0.12, 16), "mark", faces=("up",), uv=FULL)], {"mark": "r4-mark-gym-k7_1"})
    shape_by, tex_by = {}, {}
    names = []
    for surf in ("gym", "yard"):
        for cell in MARK_CELLS[surf]:
            names.append((surf, cell))
    states_cells = sorted({c for _, c in names})
    for surf in ("gym", "yard"):
        for cell in states_cells:
            for s in SIDES:
                code = f"l52-mark-{surf}-{cell}-{s}"
                shape_by[code] = {"base": mk, "rotateY": R3.ROTATE[s]}
                t = f"r4-mark-{surf}-{cell}" if cell in MARK_CELLS[surf] else "r4-mark-gym-k7_1"
                tex_by[code] = {"mark": {"base": "block/52/" + t}}
    G.json_block("l52-mark", [G.group("surf", ["gym", "yard"]), G.group("cell", states_cells), G.group("side", SIDES)], shape_by,
                 "Level 52: a court's painted markings, a flat decal over the floor (the key, the free-throw circle, the three-point arc "
                 "about a hoop: cells k<i>_<j>; the centre circle: c<i>_<j>); side: the way into the court from the hoop",
                 "Stone", G.STONE, None, {"*": G.cuboid((0, 0, 0, 1, 0.02, 1))}, creative=("l52-mark-gym-k7_1-north",), resistance=1,
                 extra={"collisionbox": None, "texturesByType": tex_by, "replaceable": 5000})

    # The scoreboard: a cabinet on the wall, three by two, its face lit
    sb = {}
    for row in ("lo", "hi"):
        for part in ("l", "m", "r"):
            x0 = 0.6 if part == "l" else 0
            x1 = 15.4 if part == "r" else 16
            y0, y1 = (2.0, 16) if row == "lo" else (0, 14.0)
            els = [box("Case", (x0, y0, 12.8), (x1, y1, 16), "r4-cabinet", faces=("east", "west", "up", "down", "south")),
                   box("Face", (x0, y0, 12.6), (x1, y1, 12.8), f"r4-score-{part}-{row}", faces=("north",), uv=FULL, glow=140)]
            if row == "lo":
                els.append(box("Lip", (x0, 1.4, 12.2), (x1, 2.0, 16), "r4-cabinet"))
            if row == "hi":
                els.append(box("Hood", (x0, 14.0, 11.6), (x1, 14.8, 16), "r4-cabinet"))
                if part == "m":
                    els.append(box("Horn", (6.5, 14.8, 13.0), (9.5, 16.0, 15.5), "r4-cabinet"))
            sb[f"l52-score-{part}-{row}"] = G.shape(f"l52-score-{part}-{row}", els)
    R3.oriented("l52-score", [G.group("part", ["l", "m", "r"]), G.group("row", ["lo", "hi"]), G.group("side", SIDES)], sb,
                "Level 52: a gym's scoreboard, three blocks wide and two high, on the wall behind (part l, m, r as seen from in front; "
                "row lo, hi): HOME and GUEST at 00, the clock stopped at 3:52, lit", "Metal", G.METAL, None,
                sel=lambda p: (0, 0.1 if p.endswith("lo") else 0, 0.78, 1, 1 if p.endswith("lo") else 0.9, 1),
                extra={"lightHsvByType": {"*-m-*": [6, 3, 5]}})

    # Wall mats
    wm = {}
    for row in ("lower", "upper"):
        els = [box("Pad", (0.2, 0 if row == "upper" else 0.8, 13.4), (15.8, 15.4 if row == "upper" else 16, 16),
                   {"front": f"r4-mat-{row}", "side": "r4-pad-blue", "top": "r4-pad-blue", "bottom": "r4-pad-blue", "back": "r4-pad-blue"})]
        els[0]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        if row == "lower":
            els.append(box("Kick", (0.4, 0, 13.8), (15.6, 0.8, 16), "r4-pad-black"))
        else:
            els.append(box("Roll", (0.2, 15.4, 13.8), (15.8, 16, 16), "r4-pad-blue"))
        wm[f"l52-wallmat-{row}"] = G.shape(f"l52-wallmat-{row}", els)
    R3.oriented("l52-wallmat", [G.group("row", ["lower", "upper"]), G.group("side", SIDES)], wm,
                "Level 52: a padded gym wall mat on the wall behind (blue vinyl, stitched edges), two blocks high", "Cloth",
                G.STONE, lambda p: (0, 0, 0.84, 1, 1, 1))


# ======================================================================== lockers in relief

LOCKER_DOORS = ((0.5, 5.5), (6.0, 11.0), (11.5, 16.0))  # the three doors' x spans, from round 1's texture (px 1-10, 12-21, 23-31)


def nuv(x0, y0, x1, y1):
    """A north face's UV for the part of a full-block picture behind x0..x1, y0..y1 (the north face is seen from the north,
    so +x is the viewer's left: u runs from x = 16 down)."""
    return [round(16 - x1, 3), round(16 - y1, 3), round(16 - x0, 3), round(16 - y0, 3)]


def locker_shape(part, ajar):
    """A bank of three steel lockers in the wall block, their fronts in relief: the carcass a little back (its seams and kick
    base show), the doors proud with the round-1 picture on them, lift latches, louvre slats and hinges (lower), the vent
    slats, number plates and top trim (upper). ajar: the middle door stands open on its hinge, the locker behind it empty."""
    lower = part == "lower"
    y0d, y1d = (2.0, 16.0) if lower else (0.0, 15.0)
    els = []
    car = {"north": "front", "east": "wall", "west": "wall", "south": "wall", "up": "top", "down": "top"}
    if ajar:
        a0, a1 = LOCKER_DOORS[1]
        for nm, x0, x1 in (("CarL", 0, a0), ("CarR", a1, 16)):
            el = box(nm, (x0, 0, 0.6), (x1, 16, 16), car)
            el["faces"]["north"]["uv"] = nuv(x0, 0, x1, 16)
            if nm == "CarL":
                el["faces"]["east"]["texture"] = "#inside"
            else:
                el["faces"]["west"]["texture"] = "#inside"
            els.append(el)
        els.append(box("CarBack", (a0, 0, 6.0), (a1, 16, 16), {"north": "inside", "south": "wall", "up": "top", "down": "top", "side": "inside"},
                       faces=("north", "south", "up", "down")))
        if lower:
            els += [box("Floor", (a0, 0, 0.6), (a1, 2.0, 6.0), {"up": "inside", "north": "front", "side": "inside"}, faces=("up", "north"))]
        else:
            els += [box("Shelf", (a0, 8.0, 0.8), (a1, 8.6, 6.0), "inside"), box("Roof", (a0, 15.0, 0.6), (a1, 16, 6.0), {"down": "inside", "north": "front", "side": "inside"}, faces=("down", "north")),
                    box("Hook", (8.2, 11.0, 4.6), (8.8, 13.0, 6.0), "r4k-chrome")]
    else:
        el = box("Carcass", (0, 0, 0.6), (16, 16, 16), car)
        el["faces"]["north"]["uv"] = [0, 0, 16, 16]
        els.append(el)
    for k, (x0, x1) in enumerate(LOCKER_DOORS):
        door = box(f"Door{k}", (x0, y0d, 0.05), (x1, y1d, 0.6), {"north": "front", "south": "inside", "side": "front", "up": "front", "down": "front"})
        door["faces"]["north"]["uv"] = nuv(x0, y0d, x1, y1d)
        bits = []
        # hinges on the door's left as seen from in front (the +x side), the latch on its right
        for hy in ((3.0, 13.0) if lower else (2.0, 12.0)):
            bits.append(box(f"Hinge{k}{hy}", (x1 - 0.1, hy, -0.15), (x1 + 0.35, hy + 1.6, 0.6), "r4k-chrome"))
        if lower:
            bits.append(box(f"Latch{k}", (x0 + 0.6, 11.6, -0.55), (x0 + 1.5, 15.0, 0.05), "r4k-chrome"))
            bits.append(box(f"LatchCup{k}", (x0 + 0.4, 11.2, -0.1), (x0 + 1.7, 15.4, 0.05), "front"))
            for j, sy in enumerate((6.5, 5.5, 4.5)):
                bits.append(box(f"Louvre{k}{j}", (x0 + 0.9, sy - 0.3, -0.3), (x1 - 0.9, sy + 0.25, 0.05), "front"))
        else:
            for j, sy in enumerate((14.0, 13.0, 12.0, 11.0)):
                bits.append(box(f"Vent{k}{j}", (x0 + 0.9, sy - 0.3, -0.3), (x1 - 0.9, sy + 0.25, 0.05), "front"))
            pl = box(f"Plate{k}", (x0 + 1.5, 6.0, -0.15), (x1 - 1.0, 8.0, 0.05), "front", faces=("north", "up", "down", "east", "west"))
            pl["faces"]["north"]["uv"] = nuv(x0 + 1.5, 6.0, x1 - 1.0, 8.0)
            bits.append(pl)
        if ajar and k == 1:
            # The door swung open on its hinges about 55 degrees, toward the viewer's left
            group_ = [door] + bits
            for e in group_:
                e["rotationOrigin"] = [x1 + 0.1, 8, 0.3]
                e["rotationY"] = -55
            els += group_
        else:
            els += [door] + bits
    if not lower:
        trim = box("Trim", (0, 15.0, -0.2), (16, 16, 0.6), "front", faces=("north", "up", "down"))
        trim["faces"]["north"]["uv"] = nuv(0, 15.0, 16, 16)
        els.append(trim)
    return els


def locker_blocktypes():
    sh = {}
    for part in ("lower", "upper"):
        sh[part] = G.shape(f"l52-locker-{part}", locker_shape(part, False), {"front": "locker-beige-lower", "wall": "wall-beige-base", "top": "wall-beige-upper", "inside": "r4-locker-in"})
        sh[part + "-ajar"] = G.shape(f"l52-locker-{part}-ajar", locker_shape(part, True), {"front": "locker-beige-lower", "wall": "wall-beige-base", "top": "wall-beige-upper", "inside": "r4-locker-in"})
    for code, ajar in (("l52-locker", False), ("l52-lockerajar", True)):
        shape_by, tex_by = {}, {}
        for p in G.PALETTES:
            for part in ("lower", "upper"):
                back = f"wall-{p}-base" if part == "lower" else f"wall-{p}-dado"
                for side in SIDES:
                    c = f"{code}-{p}-{part}-{side}"
                    shape_by[c] = {"base": sh[part + ("-ajar" if ajar else "")], "rotateY": R3.ROTATE[side]}
                    tex_by[c] = {"front": {"base": f"block/52/locker-{p}-{part}"}, "wall": {"base": f"block/52/{back}"},
                                 "top": {"base": f"block/52/wall-{p}-upper"}, "inside": {"base": "block/52/r4-locker-in"}}
        G.json_block(code, [G.group("palette", G.PALETTES), G.group("part", ["lower", "upper"]), G.group("side", SIDES)], shape_by,
                     ("Level 52: a bank of three steel lockers in a wall block, facing its side: the doors in relief over the carcass, latches, "
                      "louvres and hinges (lower), vents, number plates and the top trim (upper); its other faces are the palette's wall paint"
                      + ("; the middle door standing open, the locker behind it empty" if ajar else "")),
                     "Metal", G.METAL, {"*": G.cuboid((0, 0, 0, 1, 1, 1))}, {"*": G.cuboid((0, 0, 0, 1, 1, 1))},
                     creative=(f"{code}-beige-lower-north",), resistance=4,
                     extra={"texturesByType": tex_by, "lightAbsorption": 99, "sideopaque": {"all": False}})


def expected():
    codes = set()
    pieces = ["rim-gym", "rim-yard", "board-gym", "board-yard", "truss-wall", "truss-mid", "brace", "pole-base", "pole-mid", "pole-neck", "pole-top"]
    for s in SIDES:
        for p in pieces:
            codes.add(f"l52-hoop-{p}-{s}")
        for part in "lmr":
            for row in ("lo", "hi"):
                codes.add(f"l52-score-{part}-{row}-{s}")
        for row in ("lower", "upper"):
            codes.add(f"l52-wallmat-{row}-{s}")
        for p in G.PALETTES:
            for part in ("lower", "upper"):
                codes.add(f"l52-lockerajar-{p}-{part}-{s}")
        codes.add(f"l52-lseat-{s}")
        for k in "abc":
            codes.add(f"l52-counter-{k}-{s}")
        codes.add(f"l52-tvcart-{s}")
        codes |= {f"l52-lunch-table-{s}", f"l52-lunch-seat-{s}", f"l52-basinrim-edge-{s}", f"l52-basinrim-corner-{s}"}
        for h in ("lower", "upper"):
            codes.add(f"l52-trophy-{h}-{s}")
            codes.add(f"l52-ladder-{h}-{s}")
            codes.add(f"l52-stack-a-{h}-{s}")
            codes.add(f"l52-stack-b-{h}-{s}")
            for e in "lmr":
                codes.add(f"l52-dugout-{e}-{h}-{s}")
        codes.add(f"l52-projector-{s}")
    codes |= {f"l52-labbench-{k}-{s}" for k in ("plain", "sink", "gas") for s in SIDES}
    codes |= {f"l52-stairrail-{h}-{s}" for h in "lr" for s in SIDES}
    codes |= {f"l52-chainpost-{p}-{a}" for p in ("lower", "upper") for a in ("ns", "we")}
    codes.add("l52-roofgravel")
    codes |= {"l52-column-base", "l52-column-shaft", "l52-column-cap", "l52-planter"}
    cells = sorted({c for surf in MARK_CELLS for c in MARK_CELLS[surf]})
    for surf in ("gym", "yard"):
        for c in cells:
            for s in SIDES:
                codes.add(f"l52-mark-{surf}-{c}-{s}")
    return codes


def write_cells_table(path):
    """The cells the layout lays (only those with paint on the surface), as C#: (name, i, j)."""
    lines = []
    for surf in ("gym", "yard"):
        for name, (i, j) in sorted(MARK_CELLS[surf].items()):
            lines.append(f"{surf} {name} {i} {j}")
    return lines


def move_z(els, dz):
    out = []
    for e in els:
        e = dict(e)
        e["from"] = [e["from"][0], e["from"][1], round(e["from"][2] + dz, 4)]
        e["to"] = [e["to"][0], e["to"][1], round(e["to"][2] + dz, 4)]
        if "rotationOrigin" in e:
            o = e["rotationOrigin"]
            e["rotationOrigin"] = [o[0], o[1], round(o[2] + dz, 4)]
        out.append(e)
    return out


def kit_shapes():
    """The rebuilt props of tools/gen_52_r4_kit.py (stalls, fume hoods, bleachers, goals, flagpoles, boards on posts, the wall
    fittings; then the desks, boards, fountains, windows, seats, projectors, vents): they override round 1-3's shapes of
    the same names (the blocktypes stay)."""
    import gen_52_r4_kit as K
    K.textures(save)
    if hasattr(K, "textures2"):
        K.textures2(save)
    out = dict(K.shapes())
    if hasattr(K, "shapes2"):
        out.update(K.shapes2())
    # (the ladder's hooks reach the block's edge; the library stack's face stands 2 units in from its own: lean it 2 further)
    for k in ("l52-ladder-lower", "l52-ladder-upper"):
        if k in out:
            out[k] = move_z(out[k], 2.0)
    for name, els in sorted(out.items()):
        G.shape(name, els)
    return set(out)


def seat_blocktypes():
    """The lecture theatres' flip seats and the classrooms' ceiling projectors (their shapes are the kit's)."""
    R3.oriented("l52-lseat", [G.group("side", SIDES)], {"l52-lseat": "backrooms:block/52/l52-lseat"},
                "Level 52: a lecture theatre's flip seat (upholstered, a writing tablet stowed by its right arm), facing the way of its side",
                "Cloth", G.WOOD, lambda p: (0.05, 0, 0.1, 0.95, 0.56, 0.95), sel=lambda p: (0, 0, 0.05, 1, 0.9, 1))
    R3.oriented("l52-projector", [G.group("side", SIDES)], {"l52-projector": "backrooms:block/52/l52-projector"},
                "Level 52: a classroom's 2000s projector hung from the ceiling on a drop pole, its lens toward the board; off, like everything "
                "electrical in a classroom", "Metal", G.METAL, None, sel=lambda p: (0.25, 0.3, 0.15, 0.75, 1, 0.85))


def set_blocktypes():
    """Round 4's other set pieces (shapes from the kit): the trophy case, the pitch's dugout, the canopy columns, the
    library ladder, the entrance planters."""
    sh = lambda n: "backrooms:block/52/" + n
    R3.oriented("l52-trophy", [G.group("part", ["lower", "upper"]), G.group("side", SIDES)],
                {"l52-trophy-lower": sh("l52-trophy-lower"), "l52-trophy-upper": sh("l52-trophy-upper")},
                "Level 52: the school's trophy case, two blocks high, its back to the wall: a laminate base with doors, the glass case over it "
                "(cups, figures, a shield, a ball, medals on ribbons), a lit header", "Glass", G.GLASS, lambda p: (0, 0, 0.38, 1, 1, 1),
                extra={"renderpass": "Transparent", "lightHsvByType": {"*-upper-*": [7, 2, 5]}})
    dug = {f"l52-dugout-{e}-{h}": sh(f"l52-dugout-{e}-{h}") for e in "lmr" for h in ("lower", "upper")}

    def dcoll(p):
        return (0, 0, 0.62, 1, 0.5, 1) if p.endswith("lower") else (0, 0, 0.94, 1, 0.71, 1)
    R3.oriented("l52-dugout", [G.group("part", ["l", "m", "r"]), G.group("half", ["lower", "upper"]), G.group("side", SIDES)], dug,
                "Level 52: a pitch's dugout, three blocks wide and two high, open toward its side: ribbed steel back and ends, a bench, coat "
                "hooks, a corrugated roof", "Metal", G.METAL, dcoll, sel=lambda p: (0, 0, 0, 1, 1, 1))
    cols = {"base": (0.16, 0, 0.16, 0.84, 1, 0.84), "shaft": (0.27, 0, 0.27, 0.73, 1, 0.73), "cap": (0.07, 0, 0.07, 0.93, 1, 0.93)}
    G.json_block("l52-column", [G.group("part", list(cols))], {f"l52-column-{k}": {"base": sh(f"l52-column-{k}")} for k in cols},
                 "Level 52: an entrance canopy's round column, three blocks high (base with its plinth and bolts, shaft, cap flaring to the soffit)",
                 "Metal", G.METAL, {f"l52-column-{k}": G.cuboid((0.27, 0, 0.27, 0.73, 1, 0.73)) for k in cols},
                 {f"l52-column-{k}": G.cuboid(v) for k, v in cols.items()}, creative=("l52-column-base",), resistance=6)
    R3.oriented("l52-ladder", [G.group("part", ["lower", "upper"]), G.group("side", SIDES)],
                {"l52-ladder-lower": sh("l52-ladder-lower"), "l52-ladder-upper": sh("l52-ladder-upper")},
                "Level 52: a library's rolling ladder leaning on the stack behind it (oak rails and treads, brass rollers on the stack's rail)",
                "Wood", G.WOOD, lambda p: (0.1, 0, 0.3, 0.9, 1, 1), extra={"climbable": True})
    stk = {}
    for kind in ("a", "b"):
        for h in ("lower", "upper"):
            stk[f"l52-stack-{kind}-{h}"] = sh(f"l52-stack-{h}" + ("-b" if kind == "b" else ""))
    R3.oriented("l52-stack", [G.group("kind", ["a", "b"]), G.group("part", ["lower", "upper"]), G.group("side", SIDES)], stk,
                "Level 52: a library's double-sided steel bookstack, two blocks high, its shelves nearly bare (the dust shows where the "
                "books stood; a few left behind); a and b differ in what was left", "Metal", G.METAL, lambda p: (0, 0, 0.125, 1, 1, 0.875))
    # (three counters: a with the binder, pens and bell; b bare; c the pen cup only, so a row does not repeat its bell)
    import json as _json
    import os as _os
    with open(_os.path.join(G.SHAPES, "l52-counter.json"), encoding="utf-8") as f_:
        full = _json.load(f_)["elements"]
    G.shape("l52-counter-b", [e for e in full if not e["name"].startswith(("Binder", "Pen", "Bell"))])
    G.shape("l52-counter-c", [e for e in full if not e["name"].startswith(("Binder", "Bell"))])
    R3.oriented("l52-counter", [G.group("kind", ["a", "b", "c"]), G.group("side", SIDES)],
                {"l52-counter-a": sh("l52-counter"), "l52-counter-b": sh("l52-counter-b"), "l52-counter-c": sh("l52-counter-c")},
                "Level 52: a front office's or library's counter, the visitors' side toward its side: laminate front, a transaction "
                "ledge, the staff worktop behind (a binder, a pen cup, a desk bell left on it)", "Wood", G.WOOD,
                lambda p: (0, 0, 0, 1, 1, 0.36), sel=lambda p: (0, 0, 0, 1, 1, 1))
    R3.oriented("l52-lunch", [G.group("part", ["table", "seat"]), G.group("side", SIDES)],
                {"l52-lunch-table": sh("l52-lunch-table"), "l52-lunch-seat": sh("l52-lunch-seat")},
                "Level 52: a canteen's folding lunch table (table: the top on its folding frame, the rows of them making one long table; "
                "seat: the bench on the frame's arm, facing the table)", "Wood", G.WOOD,
                lambda p: (0, 0, 0.05, 1, 0.75, 0.95) if p.endswith("table") else (0, 0, 0.1, 1, 0.45, 0.5))
    R3.oriented("l52-basinrim", [G.group("part", ["edge", "corner"]), G.group("side", SIDES)],
                {"l52-basinrim-edge": sh("l52-basinrim-edge"), "l52-basinrim-corner": sh("l52-basinrim-corner")},
                "Level 52: the courtyard fountain's coped precast rim (edge: the paving toward its side; corner: toward its side and to the "
                "left of it), wet below the water line inside", "Stone", G.STONE,
                lambda p: (0, 0, 0.19, 1, 1, 0.81) if p.endswith("edge") else (0.19, 0, 0.19, 1, 1, 1), resistance=6)
    R3.oriented("l52-tvcart", [G.group("side", SIDES)], {"l52-tvcart": sh("l52-tvcart")},
                "Level 52: a classroom's CRT television strapped on a tall AV cart with a VCR under it (off, like everything electrical in "
                "a classroom), its screen toward its side", "Metal", G.METAL, lambda p: (0.09, 0, 0.12, 0.91, 1, 0.88),
                sel=lambda p: (0.09, 0, 0.12, 0.91, 1, 0.88))
    G.json_block("l52-planter", [], {"*": {"base": sh("l52-planter")}},
                 "Level 52: a square concrete planter by an entrance, a clipped shrub in it (and the odd cigarette end), a corner chipped",
                 "Stone", G.STONE, {"*": G.cuboid((0.04, 0, 0.04, 0.96, 0.66, 0.96))}, {"*": G.cuboid((0.04, 0, 0.04, 0.96, 0.98, 0.96))},
                 creative=("*",), resistance=4)


def plant_blocktypes():
    """The labs' benches (kit shapes) and the roofs' air handlers, now JSON in relief (they still fill their block, so they stack)."""
    sh = lambda n: "backrooms:block/52/" + n
    R3.oriented("l52-labbench", [G.group("kind", ["plain", "sink", "gas"]), G.group("side", SIDES)],
                {f"l52-labbench-{k}": sh(f"l52-labbench-{k}") for k in ("plain", "sink", "gas")},
                "Level 52: a lab bench against the wall, black epoxy on grey cupboards: plain, a sink with a gooseneck and an eyewash, gas "
                "taps and sockets (nothing on it: the labs are empty)", "Stone", G.STONE, lambda p: (0, 0, 0.1, 1, 0.95, 1),
                sel=lambda p: (0, 0, 0.1, 1, 1, 1))
    G.json_block("l52-hvac", [G.group("part", ["body", "top"])], {f"l52-hvac-{k}": {"base": sh(f"l52-hvac-{k}")} for k in ("body", "top")},
                 "Level 52: an air-handling unit on a roof (body: casing and louvres; top: the fan shroud and grille), in relief; a block each",
                 "Metal", G.METAL, {"*": G.cuboid((0, 0, 0, 1, 1, 1))}, {"*": G.cuboid((0, 0, 0, 1, 1, 1))}, creative=("*",), resistance=6,
                 extra={"lightAbsorption": 99})


def rail_shape(hand):
    """A stair handrail on the wall beside a flight, in the air block over a step (the flight climbs north, one block a
    block): a steel rail 0.9 block over the nosings' line, rising at 45 degrees, on a bracket and wall rosette (hand r: the wall
    at +x, the climber's right; l: at -x)."""
    st = "r4-steel-dark"
    x0 = 13.4 if hand == "r" else 1.4
    xw0, xw1 = (15.4, 16.0) if hand == "r" else (0.0, 0.6)
    bx0, bx1 = (14.4, 15.4) if hand == "r" else (0.6, 1.6)
    els = [box("Rail", (x0, 5.8, 8 - 11.4), (x0 + 1.2, 7.0, 8 + 11.4), st, rot=(45, 0, 0), origin=(x0 + 0.6, 6.4, 8)),
           box("Bracket", (bx0, 4.6, 7.6), (bx1, 5.4, 8.4), "r4k-satin"),
           box("Stem", (x0 + 0.3, 4.6, 7.6), (x0 + 0.9, 5.9, 8.4), "r4k-satin"),
           box("Rosette", (xw0, 3.8, 7.0), (xw1, 6.2, 9.0), "r4k-satin")]
    return els


def rail_blocktypes():
    shp = {f"l52-stairrail-{h}": G.shape(f"l52-stairrail-{h}", rail_shape(h)) for h in ("l", "r")}
    R3.oriented("l52-stairrail", [G.group("hand", ["l", "r"]), G.group("side", SIDES)], shp,
                "Level 52: a stairwell's handrail on the wall beside a flight (side: the way the flight climbs; hand: the wall on the "
                "climber's left or right), in the air over a step", "Metal", G.METAL, None, sel=lambda p: (0, 0, 0, 1, 0.5, 1))


def jet_shape():
    """The courtyard fountain's middle (overrides round 3's): a fluted column on a plinth, a lipped bowl, a small upper bowl on a
    stem, the jet and the water falling back in four sheets."""
    st, w = "fountain-stone", "fountain-water"
    els = [box("Plinth", (4.5, 0, 4.5), (11.5, 1.5, 11.5), st), box("Torus", (5.2, 1.5, 5.2), (10.8, 2.3, 10.8), st)]
    for k in range(8):
        els.append(box(f"Flute{k}", (7.2, 2.3, 5.4), (8.8, 8.0, 6.2), st, rot=(0, k * 45, 0) if k else None, origin=(8, 5, 8)))
    els += [box("Core", (6.0, 2.3, 6.0), (10.0, 8.0, 10.0), st),
            box("BowlFoot", (5.0, 8.0, 5.0), (11.0, 9.0, 11.0), st),
            box("Bowl", (2.5, 9.0, 2.5), (13.5, 10.4, 13.5), st),
            box("LipN", (2.0, 10.4, 2.0), (14.0, 11.4, 3.0), st), box("LipS", (2.0, 10.4, 13.0), (14.0, 11.4, 14.0), st),
            box("LipW", (2.0, 10.4, 3.0), (3.0, 11.4, 13.0), st), box("LipE", (13.0, 10.4, 3.0), (14.0, 11.4, 13.0), st),
            box("Water", (3.0, 11.0, 3.0), (13.0, 11.1, 13.0), w, faces=("up",)),
            box("Stem", (7.2, 11.0, 7.2), (8.8, 13.0, 8.8), st),
            box("Cup", (5.8, 13.0, 5.8), (10.2, 14.0, 10.2), st),
            box("CupWater", (6.2, 14.0, 6.2), (9.8, 14.05, 9.8), w, faces=("up",)),
            box("Jet", (7.5, 14.0, 7.5), (8.5, 16.0, 8.5), w)]
    for nm, a, b in (("FallN", (6.0, 11.1, 5.6), (10.0, 13.6, 5.7)), ("FallS", (6.0, 11.1, 10.3), (10.0, 13.6, 10.4)),
                     ("FallW", (5.6, 11.1, 6.0), (5.7, 13.6, 10.0)), ("FallE", (10.3, 11.1, 6.0), (10.4, 13.6, 10.0))):
        els.append(box(nm, a, b, w, faces=("north", "south") if nm in ("FallN", "FallS") else ("east", "west")))
    return els


def chainpost_blocktypes():
    """A chain-link panel with its post (every third block of a fence): the round's galvanised post through the mesh's middle,
    a cap on top (upper); the panel as round 1's."""
    shp = {}
    for part in ("lower", "upper"):
        els = [box("Mesh", (7.8, 0, 0), (8.2, 16 if part == "lower" else 14.4, 16), "chainlink-mesh", faces=("east", "west"), uv=FULL)]
        if part == "upper":
            els.append(box("Rail", (7.2, 14.4, 0), (8.8, 16, 16), "chainlink-rail", uv=FULL))
        els.append(box("Post", (7.1, 0, 7.1), (8.9, 16 if part == "lower" else 15.2, 8.9), "r4-galv"))
        if part == "lower":
            els.append(box("Footing", (6.4, -0.01, 6.4), (9.6, 0.6, 9.6), "r4-footing", faces=("north", "east", "south", "west", "up")))
        else:
            els += [box("Clamp", (6.9, 13.6, 6.9), (9.1, 14.4, 9.1), "r4-galv"), box("Cap", (6.8, 16.0, 6.8), (9.2, 16.8, 9.2), "r4-galv")]
        shp[part] = G.shape(f"l52-chainpost-{part}", els)
    shape_by = {}
    for part in ("lower", "upper"):
        for axis, ang in (("ns", 0), ("we", 90)):
            d = {"base": shp[part]}
            if ang:
                d["rotateY"] = ang
            shape_by[f"l52-chainpost-{part}-{axis}"] = d
    thin = {"*-ns": G.cuboid((0.4375, 0, 0, 0.5625, 1, 1)), "*-we": G.cuboid((0, 0, 0.4375, 1, 1, 0.5625))}
    G.json_block("l52-chainpost", [G.group("part", ["lower", "upper"]), G.group("axis", ["ns", "we"])], shape_by,
                 "Level 52: a chain-link panel with its galvanised post (every third block of a fence; axis as l52-chainlink)", "Metal",
                 G.METAL, thin, thin, resistance=3, extra={"renderpass": "OpaqueNoCull"})


def roof_gravel():
    """Ballast gravel on a flat roof (patches of it over the membrane): pale pebbles, a few dark ones."""
    img = M.asphalt(7400, base=(150, 148, 142), aggregate=0.65, binder=0.1, chip=(10, 40), pits=0.03, shadow=0.18)
    M.grime(img, amount=0.08, seed=7401, cover=0.4)
    save(img, "r4-roofgravel")
    G.cube_block("l52-roofgravel", [], {"*": G.faces(all_="r4-roofgravel")},
                 "Level 52: a flat roof's ballast gravel (patches over the membrane)", "Gravel", G.STONE, resistance=2)


def build(gen):
    global G
    G = gen
    textures()
    mark_textures()
    blocktypes()
    kit_shapes()
    locker_blocktypes()
    seat_blocktypes()
    set_blocktypes()
    plant_blocktypes()
    rail_blocktypes()
    chainpost_blocktypes()
    roof_gravel()
    G.shape("l52-jet", jet_shape())
