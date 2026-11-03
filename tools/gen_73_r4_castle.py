"""Level 73, "The Redlands": round 4's (2026-11-02) asset-quality pass, the castle's outside; called from gen_73.py (run that,
under the asset lock). Same interface as gen_73_interior.py: LANG, textures(save) -> count, blocktypes() -> [(comment, block)],
shapes(write_json, shape_dir) -> count.

After the lead's notes on round 3 ("one flat grey-white masonry block with a saw-tooth top"; "the roof/attic shot is a bare
grey box"): a real castle's vocabulary, every piece a model rather than a cube with a picture.
  l73-silverfoot, l73-silverstreak, l73-quoin   the masonry weathered: moss and damp at the foot, rain streaks under the
                                                parapets, pale dressed quoins at the corners
  l73-corbel-{straight,corner}-*                the machicolation course: a wall block with stepped corbels carrying a
                                                projecting floor on its outer face(s) (-north: out to the north; the
                                                corner variant also to the west, i.e. the side and the one anticlockwise)
  l73-merlon-{plain,slit,corner}-*              a merlon on that projection, with a weathered cap (and an arrow slit)
  l73-slit-*                                    a wall block with a tall arrow slit in its outer face
  l73-arch-{col}{row}-{plain,gate}              the gate's pointed arch, cut cell by cell (col 0-3 across the 4-wide gate,
                                                row 3 or 4 over its floor); "gate" carries the raised portcullis hanging
                                                into the arch on the outer (south) side
  l73-drum-{cell}-{course}                      the gatehouse's drum towers: one cell of a half-round tower front (radius 2
                                                about a cell corner), by course: foot, body, string, corbel, merlon
  l73-cone-{big,drum,small}                     conical slate roofs with an iron finial and vane: the corner towers' (over
                                                a cell corner), the drums', the keep turrets' (over a cell's middle)
  l73-roof-{slate,eave,ridge,gable,gablepeak}-* the attic's 45-degree slate roof: a slope rising toward the variant's side,
                                                the eave course with its overhang and gutter, the ridge with its cap and
                                                iron cresting, the stone gable with its coping, the gable's apex cross
  l73-dormer-{window,roof,roofback}-*           a dormer: its leaded window in a stone frame, its little gabled roof
  l73-chimneycap                                a chimney stack's corbelled cap with clay pots
  l73-window-{low,high}-*                       the keep's windows: a stone reveal and sill, a pointed head with its hood
                                                mould, the boards inside with the rooms' warm light leaking between them
All are attribute l73Fixed and drop nothing.
"""
import math
import os
import random

from PIL import Image

import matlib as M
from gen_73_castle import ROT, SIDES, face, fixed, oriented, shape


def _wrap(a, b):
    """A face's texture range from its position range: kept where it lies if it fits in one 16 (shifted by whole 16s, so
    neighbouring boxes still meet), else the last 16 (or all of it when wider), never collapsed to nothing at an edge (a
    zero-size UV at the edge of the texture samples its neighbour in the atlas)."""
    w = b - a
    if w >= 16:
        return 0.0, 16.0
    k = math.floor(a / 16)
    a2, b2 = a - 16 * k, b - 16 * k
    if b2 > 16:
        a2, b2 = 16 - w, 16.0
    return round(a2, 3), round(b2, 3)


def box(name, frm, to, tex, faces=None, uv=None, glow=0, **kw):  # (shadows gen_73_castle.box: elements here go outside the block)
    x1, y1, z1 = frm
    x2, y2, z2 = to
    spans = {"north": ((16 - x2, 16 - x1), (16 - y2, 16 - y1)), "south": ((x1, x2), (16 - y2, 16 - y1)),
             "east": ((16 - z2, 16 - z1), (16 - y2, 16 - y1)), "west": ((z1, z2), (16 - y2, 16 - y1)),
             "up": ((x1, x2), (z1, z2)), "down": ((x1, x2), (16 - z2, 16 - z1))}
    fs = {}
    for k, (su, sv) in spans.items():
        if faces is not None and k not in faces:
            continue
        t = tex if not isinstance(tex, dict) else tex.get(k, tex.get("*"))
        u0, u1 = _wrap(*su)
        v0, v1 = _wrap(*sv)
        fs[k] = face(t, [u0, v0, u1, v1], **({"glow": glow} if glow else {}))
    e = {"name": name, "from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": fs}
    e.update(kw)
    return e

S = 32
T = "backrooms:block/73/"
STONE = {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe",
         "hit": "game:block/rock-hit-pickaxe"}
FULL = {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1, "z2": 1}

LANG = [
    ("block-l73-silverfoot", "Silver Ashlar"),
    ("block-l73-silverstreak", "Silver Ashlar"),
    ("block-l73-quoin", "Dressed Quoin"),
    ("block-l73-corbel-*", "Machicolation"),
    ("block-l73-merlon-*", "Merlon"),
    ("block-l73-slit-*", "Arrow Slit"),
    ("block-l73-arch-*", "Gate Arch"),
    ("block-l73-drum-*", "Drum Tower"),
    ("block-l73-cone-*", "Slate Spire"),
    ("block-l73-roof-*", "Slate Roof"),
    ("block-l73-dormer-*", "Dormer"),
    ("block-l73-chimneycap", "Chimney Pot"),
    ("block-l73-window-*", "Boarded Window"),
]


# ================= Textures =================

def ashlar(seed, base=(150, 154, 160)):
    """The Silver Castle's ashlar: two courses a block, each stone its own shade, tooled faces, chamfered arrises."""
    img = M.brick(seed=seed, base=base, mortar=(92, 92, 96), course=16, length=32, offset=0.5, mortar_w=1, jitter=11, hue=2,
                  pits=0.05, chamfer=True, grain=5, mottle=8)
    M.scratches(img, 10, seed + 2, length=(2, 5), light=0.08, angle=80)
    M.grime(img, 0.12, seed=seed + 1, color=(70, 68, 72), cover=0.45)
    return img


def silverfoot(seed):
    """The bottom courses: damp darkening toward the ground, moss in the joints and patches on the stones."""
    img = ashlar(seed)
    M.grime(img, 0.45, seed=seed + 4, color=(44, 50, 40), bias="bottom", cover=0.8)
    px = img.load()
    rng = random.Random(seed)
    f = M.fbm((S, S), seed + 5, (8, 4, 2))
    for y in range(S):
        for x in range(S):
            low = (y / (S - 1)) ** 1.5
            t = (f[y][x] + 1) / 2
            if t * low > 0.3:
                c = px[x, y]
                g = M.mix(c, (52, 74, 40), min(1, (t * low - 0.3) * 4))
                px[x, y] = M.rgba(M.lift(g, rng.uniform(-6, 6)))
    for y in (15, 31):
        for x in range(S):
            if rng.random() < 0.55 + 0.4 * (y / 31):
                px[x, y] = M.rgba(M.mix(px[x, y], (60, 82, 44), 0.7))
    return img


def silverstreak(seed):
    """Under a parapet: dark rain streaks running down from the top edge."""
    img = ashlar(seed)
    M.drips(img, 7, seed + 6, color=(60, 60, 64), length=(14, 30), strength=0.55, start=0, width=2)
    M.drips(img, 5, seed + 7, color=(76, 78, 70), length=(6, 16), strength=0.4, start=0, width=1)
    M.grime(img, 0.25, seed=seed + 8, color=(58, 58, 62), bias="top", cover=0.7)
    return img


def quoin(seed):
    """A dressed quoin: one large pale stone a course, a tooled margin round its face."""
    img = M.brick(seed=seed, base=(178, 180, 184), mortar=(98, 98, 102), course=16, length=32, offset=0.0, mortar_w=1, jitter=6,
                  hue=1, pits=0.02, chamfer=True, grain=3, mottle=5)
    for y0 in (0, 16):
        M.inset(img, (2, y0 + 2, 29, y0 + 13), width=1, strength=0.14)
        M.scratches(img, 6, seed + y0, length=(2, 4), light=0.1, angle=90)
    M.grime(img, 0.1, seed=seed + 1, color=(80, 78, 80), cover=0.4)
    return img


def slate_roof(seed):
    """Roof slates: staggered rows, each slate its own blue-black, a lit lip and a shadowed lap, lichen here and there."""
    img = M.brick(seed=seed, base=(58, 62, 72), mortar=(18, 18, 22), course=8, length=8, offset=0.5, mortar_w=1, jitter=9, hue=4,
                  recess=1.0, pits=0.02, chamfer=False, grain=3, mottle=6)
    for y in range(S):
        k = (y % 8) / 7.0
        for x in range(S):
            M.touch(img, x, y, 0.12 - 0.26 * k)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(5):
        cx, cy = rng.randrange(S), rng.randrange(S)
        for _ in range(9):
            x, y = (cx + rng.randint(-2, 2)) % S, (cy + rng.randint(-1, 1)) % S
            px[x, y] = M.rgba(M.mix(px[x, y], (112, 118, 84), 0.55))
    M.grime(img, 0.1, seed=seed + 3, color=(30, 34, 30), cover=0.35)
    return img


def coping(seed):
    img = M.noise_hv((164, 166, 170), amp=5, seed=seed, mottle=6, hue=1)
    M.bevel(img, (0, 0, 31, 31), width=1, strength=0.18)
    M.grime(img, 0.22, seed=seed + 1, color=(70, 72, 66), cover=0.5)
    return img


def rafters(seed):
    img = M.wood_planks(seed=seed, base=(70, 50, 34), planks=4, direction="h", grain=5, contrast=1.1)
    for x in (0, 1, 16, 17):
        for y in range(S):
            M.touch(img, x, y, -0.3)
    M.grime(img, 0.3, seed=seed + 1, color=(30, 24, 20), cover=0.6)
    return img


def board_gaps(seed):
    """Window boards nailed across: three planks with gaps between them (alpha 0: the light shows through), nails."""
    img = M.wood_planks(seed=seed, base=(92, 70, 48), planks=3, direction="h", grain=5, contrast=1.2)
    M.grime(img, 0.25, seed=seed + 1, color=(40, 30, 22), cover=0.5)
    px = img.load()
    rng = random.Random(seed)
    for y0 in (10, 21):
        for x in range(S):
            for k in range(2 if rng.random() < 0.7 else 1):
                px[x, y0 + k] = (0, 0, 0, 0)
    for y in (4, 15, 26):
        for x in (3, 28):
            px[x, y] = M.rgba((40, 38, 40))
            px[x + 1, y] = M.rgba((96, 90, 86))
    return img


def warmglow(seed):
    """The rooms' light seen between the boards: amber, brighter in the middle, flickering in patches."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    f = M.fbm((S, S), seed, (8, 4))
    for y in range(S):
        for x in range(S):
            d = 1 - abs(y - 16) / 18
            t = max(0, min(1, 0.55 + 0.35 * d + 0.25 * f[y][x]))
            px[x, y] = M.rgba(M.mix((150, 60, 18), (255, 196, 96), t))
    return img


def leaded(seed):
    """Leaded glass in diamond quarries, dark (the attic is unlit), a dull sheen on a few panes."""
    img = M.noise_hv((34, 40, 46), amp=4, seed=seed, mottle=5)
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            if (x + y) % 8 == 0 or (x - y) % 8 == 0:
                px[x, y] = M.rgba((22, 22, 24))
            elif rng.random() < 0.04 or (x + 2 * y) % 29 < 3:
                px[x, y] = M.rgba(M.mix(px[x, y], (110, 118, 126), 0.4))
    return img


def darkness(seed):
    return M.noise_hv((14, 12, 14), amp=2, seed=seed, mottle=3)


def terracotta(seed):
    img = M.noise_hv((112, 58, 40), amp=6, seed=seed, mottle=6, hue=2)
    M.grime(img, 0.5, seed=seed + 1, color=(24, 20, 18), bias="top", cover=0.8)
    return img


def iron_dark(seed):
    img = M.noise_hv((36, 34, 36), amp=4, seed=seed, mottle=5, hue=1)
    M.rust(img, 0.18, seed=seed + 1)
    return img


def textures(save):
    save(silverfoot(7701), "block/73/silverfoot")
    save(silverfoot(7702), "block/73/silverfoot-2")
    save(silverstreak(7703), "block/73/silverstreak")
    save(silverstreak(7704), "block/73/silverstreak-2")
    save(quoin(7705), "block/73/quoin")
    save(slate_roof(7706), "block/73/r4-slate")
    save(coping(7707), "block/73/r4-coping")
    save(rafters(7708), "block/73/r4-rafters")
    save(board_gaps(7709), "block/73/r4-boardgaps")
    save(warmglow(7710), "block/73/r4-warmglow")
    save(leaded(7711), "block/73/r4-leaded")
    save(darkness(7712), "block/73/r4-dark")
    save(terracotta(7713), "block/73/r4-terracotta")
    save(iron_dark(7714), "block/73/r4-iron")
    return 14


# ================= Shape helpers =================

STONE_TEX = {"stone": T + "silverwall", "foot": T + "silverfoot", "streak": T + "silverstreak", "coping": T + "r4-coping",
             "dark": T + "r4-dark", "iron": T + "r4-iron", "slate": T + "r4-slate", "rafters": T + "r4-rafters",
             "boards": T + "r4-boardgaps", "glow": T + "r4-warmglow", "leaded": T + "r4-leaded", "pot": T + "r4-terracotta",
             "quoin": T + "quoin", "oak": T + "beam", "oakb": T + "oak"}


def rects(grid):
    """Greedy rectangles over a 2D boolean grid [a][b] -> [(a0, b0, a1, b1)] (half-open)."""
    n0, n1 = len(grid), len(grid[0])
    used = [[False] * n1 for _ in range(n0)]
    out = []
    for a in range(n0):
        for b in range(n1):
            if not grid[a][b] or used[a][b]:
                continue
            b1 = b
            while b1 < n1 and grid[a][b1] and not used[a][b1]:
                b1 += 1
            a1 = a + 1
            while a1 < n0 and all(grid[a1][k] and not used[a1][k] for k in range(b, b1)):
                a1 += 1
            for i in range(a, a1):
                for k in range(b, b1):
                    used[i][k] = True
            out.append((a, b, a1, b1))
    return out


def layer_xz(name, pred, y0, y1, tex, res=1.0, lo=0.0, hi=16.0):
    """Boxes filling where pred(x, z) holds (cell px, sampled at pixel centres from lo to hi), from y0 to y1."""
    n = int(round((hi - lo) / res))
    grid = [[pred(lo + (i + 0.5) * res, lo + (k + 0.5) * res) for k in range(n)] for i in range(n)]
    return [box(f"{name}{j}", [lo + a0 * res, y0, lo + b0 * res], [lo + a1 * res, y1, lo + b1 * res], tex)
            for j, (a0, b0, a1, b1) in enumerate(rects(grid))]


def layer_xy(name, pred, z0, z1, tex, res=1.0):
    """Boxes filling where pred(x, y) holds over the cell's x-y face, extruded from z0 to z1."""
    n = int(16 / res)
    grid = [[pred((i + 0.5) * res, (k + 0.5) * res) for k in range(n)] for i in range(n)]
    return [box(f"{name}{j}", [a0 * res, b0 * res, z0], [a1 * res, b1 * res, z1], tex)
            for j, (a0, b0, a1, b1) in enumerate(rects(grid))]


# ---- Machicolations, merlons, slits ----

PROJ = 3.0  # how far the parapet stands out from the wall face on its corbels


def corbel_shape(corner):
    """A wall block (the course under the parapet) with three stepped corbels on its outer face (north; also west for the
    corner) carrying a projecting floor, its underside dark between the corbels (the machicolation's holes)."""
    els = [box("Wall", [0, 0, 0], [16, 16, 16], "#streak")]

    def corbels(axis):
        out = []
        for i, c in enumerate((2.5, 8, 13.5)):
            for t, (y0, y1, d) in enumerate(((5, 8.5, 1.0), (8.5, 12, 2.0), (12, 13.5, 2.8))):
                if axis == "n":
                    out.append(box(f"CorbelN{i}{t}", [c - 1.6, y0, -d], [c + 1.6, y1, 0], "#stone"))
                else:
                    out.append(box(f"CorbelW{i}{t}", [-d, y0, c - 1.6], [0, y1, c + 1.6], "#stone"))
        return out

    els += corbels("n")
    els.append(box("FloorN", [-PROJ if corner else 0, 13.5, -PROJ], [16, 16, 0], {"*": "#coping", "down": "#dark"}))
    if corner:
        els += corbels("w")
        els.append(box("FloorW", [-PROJ, 13.5, 0], [0, 16, 16], {"*": "#coping", "down": "#dark"}))
    return shape(STONE_TEX, els)


def merlon_shape(kind):
    """A merlon standing on the machicolation's projection (its outer face PROJ beyond the wall's), a sloped, weathered cap
    with a drip; 'slit' has an arrow slit through it; 'corner' projects to the north and the west."""
    corner = kind == "corner"
    x0 = -PROJ if corner else 0
    z0 = -PROJ
    els = []
    if kind == "slit":
        els += [box("Left", [0, 0, z0], [7, 12.5, 14], "#streak"), box("Right", [9, 0, z0], [16, 12.5, 14], "#streak"),
                box("Sill", [7, 0, z0], [9, 2.5, 14], "#streak"), box("Lintel", [7, 10.5, z0], [9, 12.5, 14], "#streak"),
                box("SlitBack", [7, 2.5, 3], [9, 10.5, 14], "#dark"),
                box("Oillet", [6, 3.2, z0 - 0.02], [10, 4.8, z0 + 1.5], {"*": "#stone", "north": "#dark"})]
    else:
        els.append(box("Body", [x0, 0, z0], [16, 12.5, 14], "#streak"))
    els.append(box("Cap", [x0 - 0.6, 12.5, z0 - 0.6], [16, 14, 14.6], "#coping"))
    els.append(box("CapTop", [x0 + 1, 14, z0 + 1.2], [16, 15.2, 12.8], "#coping"))
    els.append(box("CapRidge", [x0 + 3, 15.2, z0 + 3.5], [15, 16, 10.5], "#coping"))
    return shape(STONE_TEX, els)


def slit_shape():
    """A wall block with a tall arrow slit in its outer (north) face: splayed reveals, a dark slot, a round oillet at its
    foot and a short cross-arm."""
    els = [box("Left", [0, 0, 0], [6.5, 16, 16], "#stone"), box("Right", [9.5, 0, 0], [16, 16, 16], "#stone"),
           box("Below", [6.5, 0, 0], [9.5, 2, 16], "#stone"), box("Above", [6.5, 15, 0], [9.5, 16, 16], "#stone"),
           box("Behind", [6.5, 2, 5], [9.5, 15, 16], {"*": "#dark", "up": "#stone"}),
           box("ArmL", [4.5, 9, -0.02], [6.5, 10.4, 2], {"*": "#stone", "north": "#dark"}),
           box("ArmR", [9.5, 9, -0.02], [11.5, 10.4, 2], {"*": "#stone", "north": "#dark"}),
           box("Oillet", [6.2, 2, -0.02], [9.8, 3.6, 2], {"*": "#stone", "north": "#dark"})]
    return shape(STONE_TEX, els)


# ---- The gate's pointed arch and portcullis ----
# Gate-local: x' 0..4 across the gate (cells 0-3), y over the gate's floor block (c): open from c 1 up to the apex at c 5,
# a drop arch of two circles of radius 3 about (1, s) and (3, s), s = 5 - sqrt(8).

ARCH_S = 5 - math.sqrt(8)
ARCH_CELLS = [(c, r) for r in (3, 4) for c in range(4)]


def arch_open(x, y):
    if y < 1 or x < 0 or x > 4:
        return False
    if y < ARCH_S:
        return True
    return (x - 3) ** 2 + (y - ARCH_S) ** 2 <= 9 and (x - 1) ** 2 + (y - ARCH_S) ** 2 <= 9


def arch_shape(col, row, gate):
    els = layer_xy("Stone", lambda x, y: not arch_open(col + x / 16, row + y / 16), 0, 16, "#stone")
    # a chamfered edge round the arch's face (the voussoirs' line), on both faces
    els += layer_xy("Arris", lambda x, y: (not arch_open(col + x / 16, row + y / 16))
                    and (arch_open(col + (x + 1.5) / 16, row + y / 16) or arch_open(col + (x - 1.5) / 16, row + y / 16)
                         or arch_open(col + x / 16, row + (y - 1.5) / 16)), -0.6, 16.6, "#coping")
    if gate and row == 4:
        # the portcullis, raised: its grid of iron bars in a slot near the outer (south) face, its spiked foot hanging
        # into the arch a hand below this cell
        def bar(x, y):
            gx = col * 16 + x
            return arch_open(col + x / 16, row + y / 16) and ((gx % 6) < 1.5 or (y % 5) < 1.2)
        els += layer_xy("Grid", bar, 12, 13.5, "#iron")
        for i in range(16):
            gx = col * 16 + i
            if gx % 6 < 1 and 1 < gx < 63 and arch_open(col + (i + 0.5) / 16, row + 0.02):
                els.append(box(f"Spike{i}", [i, -3.5, 12.2], [i + 1.5, 0, 13.3], "#iron"))
                els.append(box(f"Tip{i}", [i + 0.3, -4.6, 12.4], [i + 1.2, -3.5, 13.1], "#iron"))
    return shape(STONE_TEX, els)


# ---- The drum towers ----
# Cells (dx, dz) from the drum's centre (a cell corner), +z outward (the gatehouse faces south); radius 2. A cell claims
# what lies past its edges where no drum cell is (the projecting floors and caps run beyond the outermost cells).

DRUM_R = 2.0
DRUM_CELLS = [(dx, dz) for dx in (-2, -1, 0, 1) for dz in (0, 1)]
DRUM_COURSES = ["foot", "body", "string", "corbel", "merlon"]


def drum_key(dx, dz):
    return f"{dx + 2}{dz}"


def drum_shape(dx, dz, course):
    def owner(x, z):
        wx, wz = dx + x / 16, dz + z / 16
        if wz < 0:
            return False
        return (max(-2, min(1, math.floor(wx))), min(1, math.floor(wz))) == (dx, dz)

    def r(x, z):
        return math.hypot(dx + x / 16, dz + z / 16)

    def ang(x, z):
        return math.degrees(math.atan2(dz + z / 16, dx + x / 16))

    def L(name, pred, y0, y1, tex, res=1.0):
        return layer_xz(name, lambda x, z: owner(x, z) and pred(x, z), y0, y1, tex, res, -5.0, 21.0)

    els = []
    if course in ("foot", "body", "string"):
        els += L("Body", lambda x, z: r(x, z) <= DRUM_R, 0, 16, "#foot" if course == "foot" else "#stone")
        if course == "string":
            els += L("Band", lambda x, z: DRUM_R < r(x, z) <= DRUM_R + 0.09, 11, 14, "#coping", 0.5)
    elif course == "corbel":
        sector = lambda x, z: (ang(x, z) % 22.5) < 7
        els += L("Body", lambda x, z: r(x, z) <= DRUM_R, 0, 13.5, "#streak")
        els += L("CorbelA", lambda x, z: DRUM_R < r(x, z) <= DRUM_R + 0.07 and sector(x, z), 5, 8.5, "#stone", 0.5)
        els += L("CorbelB", lambda x, z: DRUM_R < r(x, z) <= DRUM_R + 0.13 and sector(x, z), 8.5, 13.5, "#stone", 0.5)
        els += L("Floor", lambda x, z: r(x, z) <= DRUM_R + 0.19, 13.5, 16, "#coping")
    elif course == "merlon":
        merl = lambda x, z: (ang(x, z) % 30) < 17
        els += L("Merlon", lambda x, z: DRUM_R - 0.45 <= r(x, z) <= DRUM_R + 0.19 and merl(x, z), 0, 12.5, "#streak")
        els += L("Cap", lambda x, z: DRUM_R - 0.5 <= r(x, z) <= DRUM_R + 0.23 and merl(x, z), 12.5, 14.5, "#coping")
    return shape(STONE_TEX, els)


# ---- Cones ----

CONES = {"big": (16, 16, 2.0, 7.0), "drum": (16, 16, 1.45, 5.5), "small": (8, 8, 1.75, 3.7)}


def cone_shape(kind):
    """A conical slate roof: rings stepping in (a cross and a square each, a twelve-sided round), a flared eave, a lead
    roll at the top, an iron finial with a ball and a vane."""
    cx, cz, R, H = CONES[kind]
    R *= 16
    H *= 16
    n = int(H / 4)
    els = [box("EaveA", [cx - R - 1.2, 0, cz - R * 0.42 - 1], [cx + R + 1.2, 1.2, cz + R * 0.42 + 1], "#slate"),
           box("EaveB", [cx - R * 0.42 - 1, 0, cz - R - 1.2], [cx + R * 0.42 + 1, 1.2, cz + R + 1.2], "#slate"),
           box("EaveC", [cx - R * 0.8 - 1, 0, cz - R * 0.8 - 1], [cx + R * 0.8 + 1, 1.2, cz + R * 0.8 + 1], "#slate")]
    for i in range(n):
        r = R * (1 - i / n) ** 1.08
        y0, y1 = 1.2 + (H - 1.2) * i / n, 1.2 + (H - 1.2) * (i + 1) / n
        if r < 0.6:
            break
        a, b, c = r, r * 0.42, r * 0.8
        els += [box(f"RingA{i}", [cx - a, y0, cz - b], [cx + a, y1, cz + b], "#slate"),
                box(f"RingB{i}", [cx - b, y0, cz - a], [cx + b, y1, cz + a], "#slate"),
                box(f"RingC{i}", [cx - c, y0, cz - c], [cx + c, y1, cz + c], "#slate")]
    top = H
    els += [box("Roll", [cx - 1.2, top - 2, cz - 1.2], [cx + 1.2, top + 0.5, cz + 1.2], "#iron"),
            box("Rod", [cx - 0.4, top, cz - 0.4], [cx + 0.4, top + 10, cz + 0.4], "#iron"),
            box("Ball", [cx - 1.1, top + 2.5, cz - 1.1], [cx + 1.1, top + 4.7, cz + 1.1], "#iron"),
            box("VaneArm", [cx - 0.3, top + 7, cz - 4], [cx + 0.3, top + 7.6, cz + 4], "#iron"),
            box("Vane", [cx - 0.15, top + 7.6, cz + 0.5], [cx + 0.15, top + 10.5, cz + 4], "#iron"),
            box("Point", [cx - 0.25, top + 10, cz - 0.25], [cx + 0.25, top + 12.5, cz + 0.25], "#iron")]
    return shape(STONE_TEX, els)


# ---- The attic's roof ----
# Default orientation: the slope rises toward the south (+z): low at the north edge (z 0, y 0), high at the south (z 16,
# y 16). The blocktype turns it to rise toward the variant's side.

SQ2 = math.sqrt(2)


def slope_els(z_from=0.0):
    L = 16 * SQ2
    els = [{"name": "Deck", "from": [0, -1.6, z_from * SQ2], "to": [16, 0, L], "rotationOrigin": [0, 0, 0], "rotationX": -45,
            "faces": {"up": face("#slate", [0, 0, 16, 16]), "down": face("#rafters", [0, 0, 16, 16]),
                      "north": face("#slate", [0, 0, 16, 1.6]), "east": face("#slate", [0, 0, 16, 1.6]),
                      "west": face("#slate", [0, 0, 16, 1.6]), "south": face("#slate", [0, 0, 16, 1.6])}}]
    for k in range(4):
        s = 4 * k + 0.5
        els.append(box(f"Lip{k}", [0, s - 0.2, s - 0.9], [16, s + 0.8, s + 0.3], "#slate"))
    return els


def roof_shape(kind):
    if kind == "slate":
        els = slope_els()
    elif kind == "eave":
        els = slope_els(z_from=-3.5)
        els += [box("Fascia", [0, -4.6, -3.6], [16, -2.2, -2.6], "#oak"),
                box("Gutter", [0, -5.6, -5.2], [16, -4.2, -3.4], "#iron"),
                box("BracketL", [3, -5.8, -5.4], [3.8, -3.6, -2.6], "#iron"),
                box("BracketR", [12.2, -5.8, -5.4], [13, -3.6, -2.6], "#iron")]
    elif kind == "ridge":
        els = slope_els()
        els += [box("Ridge", [0, 14.6, 14.2], [16, 17.2, 17.8], "#slate"),
                box("RidgeTop", [0, 17.2, 15.2], [16, 17.8, 16.8], "#iron")]
        for i, x in enumerate((2, 6, 10, 14)):
            els += [box(f"Crest{i}", [x - 0.35, 17.8, 15.65], [x + 0.35, 21.5, 16.35], "#iron"),
                    box(f"CrestL{i}", [x - 1.4, 19.2, 15.75], [x + 1.4, 19.8, 16.25], "#iron"),
                    box(f"CrestB{i}", [x - 0.7, 20.6, 15.6], [x + 0.7, 21.9, 16.4], "#iron")]
    elif kind == "gable":
        els = [box(f"Wedge{i}", [0, 2 * i, 2 * i + 1], [16, 2 * i + 2, 16], "#stone") for i in range(8)]
        L = 16 * SQ2
        els.append({"name": "Coping", "from": [-1.2, 0, 0], "to": [17.2, 2.6, L + 1], "rotationOrigin": [0, 0, 0], "rotationX": -45,
                    "faces": {k: face("#coping", [0, 0, 16, 16] if k in ("up", "down") else [0, 0, 16, 2.6])
                              for k in ("up", "down", "north", "south", "east", "west")}})
    else:  # gablepeak: where the two copings meet: a kneeler of stone and a cross finial
        els = [box("Kneeler", [-1.2, 0, 0], [17.2, 16, 16], {"*": "#stone", "up": "#coping"}),
               box("Cap", [-1.6, 16, -0.5], [17.6, 18, 16.5], "#coping"),
               box("Shaft", [6.5, 18, 6.5], [9.5, 27, 9.5], "#coping"),
               box("Arms", [3.5, 23, 6.8], [12.5, 25.4, 9.2], "#coping"),
               box("Head", [6.2, 27, 6.2], [9.8, 28.4, 9.8], "#coping")]
    return shape(STONE_TEX, els)


def dormer_window_shape():
    """A dormer's front (outward north): a stone frame with a pointed head round a leaded window, slate-hung cheeks going
    back into the roof, a sill; the attic side plain rafters."""
    def light(x, y):
        if not 4 <= x <= 12 or y < 2:
            return False
        if y < 7.1:
            return True
        return (x - 12) ** 2 + (y - 7.1) ** 2 <= 64 and (x - 4) ** 2 + (y - 7.1) ** 2 <= 64
    els = layer_xy("Frame", lambda x, y: not light(x, y) and 1 <= x <= 15, 0, 3, "#coping")
    els += [box("Glass", [4, 2, 2.2], [12, 14, 2.6], "#leaded"),
            box("Mullion", [7.6, 2, 1.6], [8.4, 13, 2.4], "#coping"),
            box("Sill", [0.5, 0, -1.4], [15.5, 2, 3], "#coping"),
            box("CheekL", [0, 0, 3], [1.5, 16, 16], "#slate"), box("CheekR", [14.5, 0, 3], [16, 16, 16], "#slate"),
            box("Back", [1.5, 0, 15], [14.5, 16, 16], "#rafters")]
    return shape(STONE_TEX, els)


def dormer_roof_shape(front):
    """A dormer's gabled roof running back into the main slope (ridge along z at y 11.4): two slate planes, and on the
    front cell the stone gable under them with a finial."""
    a = 9 * SQ2
    z0 = -2.5 if front else 0
    planes = []
    for nm, frm, to, rot, side in (("PlaneL", [8 - a, 10, z0], [8, 11.4, 16], 45, "west"),
                                   ("PlaneR", [8, 10, z0], [8 + a, 11.4, 16], -45, "east")):
        planes.append({"name": nm, "from": frm, "to": to, "rotationOrigin": [8, 11.4, 0], "rotationZ": rot,
                       "faces": {"up": face("#slate", [0, 0, 16, 16]), "down": face("#rafters", [0, 0, 16, 16]),
                                 "north": face("#slate", [0, 0, 16, 1.4]), "south": face("#slate", [0, 0, 16, 1.4]),
                                 side: face("#slate", [0, 0, 16, 1.4])}})
    els = planes + [box("RidgeRoll", [7.2, 11, z0], [8.8, 12.4, 16], "#iron")]
    if not front:
        # the main roof's slope carries on through the back cell: the dormer's roof runs into it (the valleys)
        els += slope_els()
    if front:
        for i in range(5):
            w = 7.5 - 2 * i
            els.append(box(f"Gable{i}", [8 - w, 2 * i, 0], [8 + w, 2 * i + 2, 1.5], "#stone"))
        els += [box("Finial", [7.3, 11.5, -2.4], [8.7, 16.5, -1.0], "#coping"),
                box("FinialKnop", [6.9, 16.5, -2.8], [9.1, 17.6, -0.6], "#coping")]
    return shape(STONE_TEX, els)


def chimneycap_shape():
    """A chimney stack's top: rain-streaked ashlar, a band and a corbelled cornice standing out all round, a weathered top,
    clay pots with sooted rims."""
    els = [box("Stack", [0, 0, 0], [16, 9, 16], "#streak"),
           box("Band", [-0.8, 9, -0.8], [16.8, 10.5, 16.8], "#coping"),
           box("Cornice", [-1.6, 10.5, -1.6], [17.6, 12.5, 17.6], "#coping"),
           box("Top", [-0.6, 12.5, -0.6], [16.6, 13.5, 16.6], {"*": "#coping", "up": "#dark"})]
    for i, (a, b) in enumerate(((5.5, 10.5), (6, 10), (6.5, 9.5))):
        els.append(box(f"Pot{i}", [a, 13.5 + 3 * i, a], [b, 16.5 + 3 * i, b], "#pot"))
    els += [box("PotRim", [5.6, 22.5, 5.6], [10.4, 23.6, 10.4], "#pot")]
    return shape(STONE_TEX, els)


def window_shape(part):
    """The keep's window (outward north), two blocks: 'low' the sill and the lower boards, 'high' the pointed head with its
    hood mould. A stone reveal 4 deep, boards nailed across with the rooms' warm light between them, boards on the room
    side (behind the curtains)."""
    def opening(x, y):
        if not 3 <= x <= 13:
            return False
        if part == "low":
            return y >= 2.5
        if y < 6.3:
            return True
        return (x - 13) ** 2 + (y - 6.3) ** 2 <= 100 and (x - 3) ** 2 + (y - 6.3) ** 2 <= 100 and y <= 15
    y0, y1 = (2.5, 16) if part == "low" else (0, 15)
    els = layer_xy("Reveal", lambda x, y: not opening(x, y), 0, 4, "#stone")
    els += [box("Inner", [0, 0, 7.5], [16, 16, 16], {"*": "#stone", "south": "#oakb"}),
            box("Boards", [3, y0, 4.8], [13, y1, 5.8], "#boards"),
            box("Batten", [3, 6, 5.8], [13, 7.2, 6.4], "#oak"),
            {"name": "Light", "from": [3, y0, 7.4], "to": [13, y1, 7.45],
             "faces": {"north": face("#glow", [3, 16 - y1, 13, 16 - y0], glow=200)}}]
    if part == "low":
        els += [box("Sill", [1.5, 0, -1.6], [14.5, 2.5, 4], "#coping"),
                box("Drip", [1.5, 0, -1.9], [14.5, 0.8, -1.6], "#coping")]
    else:
        els += [box("Hood", [1.5, 14.8, -1.2], [14.5, 16, 0.5], "#coping"),
                box("HoodL", [1.5, 9, -1.2], [2.6, 14.8, 0.5], "#coping"),
                box("HoodR", [13.4, 9, -1.2], [14.5, 14.8, 0.5], "#coping"),
                box("Keystone", [7, 13.6, -0.8], [9, 16, 0.5], "#coping")]
    return shape(STONE_TEX, els)


# ================= Blocktypes =================

def cube(code, comment, tex, alts=None):
    t = {"base": tex}
    if alts:
        t["alternates"] = [{"base": a} for a in alts]
    return comment, fixed({
        "code": code, "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "textures": {"all": t}, "drops": [], "sounds": STONE})


def jsonblock(code, comment, groups, shape_by, inv, sel=FULL, coll=FULL, extra=None):
    b = {"code": code, "variantgroups": groups, "creativeinventory": {"general": [inv], "backrooms": [inv]},
         "blockmaterial": "Stone", "drawtype": "json", "shapeByType": shape_by, "sidesolid": {"all": False},
         "sideopaque": {"all": False}, "lightAbsorption": 0, "selectionbox": sel, "collisionbox": coll, "drops": [], "sounds": STONE}
    if extra:
        b.update(extra)
    return comment, fixed(b)


def blocktypes():
    out = [
        cube("l73-silverfoot", "// Level 73: the castle's lowest courses, moss and damp at the foot", "block/73/silverfoot",
             ["block/73/silverfoot-2"]),
        cube("l73-silverstreak", "// Level 73: the castle's masonry under a parapet, streaked by the rain", "block/73/silverstreak",
             ["block/73/silverstreak-2"]),
        cube("l73-quoin", "// Level 73: a pale dressed quoin at the castle's corners", "block/73/quoin"),
    ]
    out.append(oriented(
        "l73-corbel", "// Level 73: the machicolation course: corbels carrying a projecting floor on the outer face (-north: north; corner: and west)",
        None, "Stone", FULL, coll=FULL, sounds=STONE, extra_variants=[{"code": "kind", "states": ["straight", "corner"]}],
        shape_by={f"*-{k}-{s}": {"base": f"block/73/corbel-{k}", "rotateY": ROT[s]} for k in ("straight", "corner") for s in SIDES},
        inv="*-straight-north"))
    out.append(oriented(
        "l73-merlon", "// Level 73: a merlon on the machicolations, a sloped cap (slit: an arrow slit; corner: projecting two ways)",
        None, "Stone", FULL, coll=FULL, sounds=STONE, extra_variants=[{"code": "kind", "states": ["plain", "slit", "corner"]}],
        shape_by={f"*-{k}-{s}": {"base": f"block/73/merlon-{k}", "rotateY": ROT[s]} for k in ("plain", "slit", "corner") for s in SIDES},
        inv="*-plain-north"))
    out.append(oriented("l73-slit", "// Level 73: a wall block with an arrow slit in its outer face (north for -north)",
                        "block/73/slit", "Stone", FULL, coll=FULL, sounds=STONE))
    arch_states = [f"{c}{r}" for c, r in ARCH_CELLS]
    out.append(jsonblock(
        "l73-arch", "// Level 73: the gate's pointed arch, one cell of it (column and row over the gate's floor); gate: with the raised portcullis",
        [{"code": "piece", "states": arch_states}, {"code": "kind", "states": ["plain", "gate"]}],
        {f"*-{p}-{g}": {"base": f"block/73/arch-{p}-{g}"} for p in arch_states for g in ("plain", "gate")}, "*-04-plain", coll=None))
    keys = [drum_key(dx, dz) for dx, dz in DRUM_CELLS]
    out.append(jsonblock(
        "l73-drum", "// Level 73: the gatehouse's drum towers, one cell of a half-round front by course",
        [{"code": "cell", "states": keys}, {"code": "course", "states": DRUM_COURSES}],
        {f"*-{k}-{c}": {"base": f"block/73/drum-{k}-{c}"} for k in keys for c in DRUM_COURSES}, "*-11-body"))
    out.append(jsonblock(
        "l73-cone", "// Level 73: a conical slate roof with an iron finial (big: a corner tower's, centred on the cell's south-east corner; drum likewise; small: a turret's, over its middle)",
        [{"code": "kind", "states": list(CONES)}], {f"*-{k}": {"base": f"block/73/cone-{k}"} for k in CONES}, "*",
        sel={"x1": 0.3, "y1": 0, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7}, coll=None))
    roof_kinds = ["slate", "eave", "ridge", "gable", "gablepeak"]
    out.append(oriented(
        "l73-roof", "// Level 73: the attic's 45-degree slate roof, rising toward the variant's side (eave, ridge with cresting, stone gable with coping)",
        None, "Stone", FULL, coll=FULL, sounds=STONE, extra_variants=[{"code": "kind", "states": roof_kinds}],
        shape_by={f"*-{k}-{s}": {"base": f"block/73/roof-{k}", "rotateY": (ROT[s] + 180) % 360} for k in roof_kinds for s in SIDES},
        inv="*-slate-south", extra={"renderpass": "OpaqueNoCull"}))
    out.append(oriented(
        "l73-dormer", "// Level 73: a dormer in the attic's roof: its leaded window (front) and its gabled roof (front and back cells), outward north for -north",
        None, "Stone", FULL, coll=FULL, sounds=STONE, extra_variants=[{"code": "part", "states": ["window", "roof", "roofback"]}],
        shape_by={f"*-{p}-{s}": {"base": f"block/73/dormer-{p}", "rotateY": ROT[s]} for p in ("window", "roof", "roofback") for s in SIDES},
        inv="*-window-north", extra={"renderpass": "OpaqueNoCull"}))
    out.append(("// Level 73: a chimney stack's corbelled cap and its clay pots", fixed({
        "code": "l73-chimneycap", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone",
        "drawtype": "json", "shape": {"base": "block/73/chimneycap"}, "sidesolid": {"all": False}, "sideopaque": {"all": False},
        "lightAbsorption": 0, "selectionbox": FULL, "collisionbox": FULL, "drops": [], "sounds": STONE})))
    out.append(oriented(
        "l73-window", "// Level 73: the keep's boarded windows (outward north for -north), the rooms' light leaking between the boards",
        None, "Stone", FULL, coll=FULL, sounds=STONE, light=[5, 4, 5], extra_variants=[{"code": "part", "states": ["low", "high"]}],
        shape_by={f"*-{p}-{s}": {"base": f"block/73/window-{p}", "rotateY": ROT[s]} for p in ("low", "high") for s in SIDES},
        inv="*-low-north"))
    return out


def shapes(write_json, shape_dir):
    n = 0

    def w(name, obj):
        nonlocal n
        write_json(os.path.join(shape_dir, name + ".json"), None, obj)
        n += 1
    for k in ("straight", "corner"):
        w(f"corbel-{k}", corbel_shape(k == "corner"))
    for k in ("plain", "slit", "corner"):
        w(f"merlon-{k}", merlon_shape(k))
    w("slit", slit_shape())
    for c, r in ARCH_CELLS:
        for g in ("plain", "gate"):
            w(f"arch-{c}{r}-{g}", arch_shape(c, r, g == "gate"))
    for dx, dz in DRUM_CELLS:
        for course in DRUM_COURSES:
            w(f"drum-{drum_key(dx, dz)}-{course}", drum_shape(dx, dz, course))
    for k in CONES:
        w(f"cone-{k}", cone_shape(k))
    for k in ("slate", "eave", "ridge", "gable", "gablepeak"):
        w(f"roof-{k}", roof_shape(k))
    w("dormer-window", dormer_window_shape())
    w("dormer-roof", dormer_roof_shape(True))
    w("dormer-roofback", dormer_roof_shape(False))
    w("chimneycap", chimneycap_shape())
    for p in ("low", "high"):
        w(f"window-{p}", window_shape(p))
    return n


# ================= The island's dead trees and boulders, rebuilt (round 4) =================
# Same files as gen_73_interior.py's (deadwood-*, deadbranch-*, boulder-*), written after them: limbs as boxes turned about
# one axis (so they fork and lean instead of stepping), twigs at their ends, an octagonal trunk with a root flare; the
# boulders faceted by slabs turned about the vertical and tilted.

from gen_73_r4_hound import box as sbox  # (faces mapped by their own size, for elements far outside the block)

WOOD_TEX = {"bark": T + "deadbark", "end": T + "logend", "char": T + "burnt"}


def limb(name, p, q, w, tex="#bark"):
    """A limb from p to q (x, y, z in px) in one of the planes x-y (turned about z), y-z (about x) or x-z (about y)."""
    (x0, y0, z0), (x1, y1, z1) = p, q
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    c = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]
    if abs(dz) < 1e-6:
        L = math.hypot(dx, dy)
        el = sbox(name, [c[0] - L / 2, c[1] - w / 2, c[2] - w / 2], [c[0] + L / 2, c[1] + w / 2, c[2] + w / 2], tex)
        el["rotationOrigin"], el["rotationZ"] = [round(v, 3) for v in c], round(math.degrees(math.atan2(dy, dx)), 3)
    elif abs(dx) < 1e-6:
        L = math.hypot(dz, dy)
        el = sbox(name, [c[0] - w / 2, c[1] - w / 2, c[2] - L / 2], [c[0] + w / 2, c[1] + w / 2, c[2] + L / 2], tex)
        el["rotationOrigin"], el["rotationX"] = [round(v, 3) for v in c], round(math.degrees(math.atan2(-dy, dz)), 3)
    else:
        L = math.hypot(dx, dz)
        el = sbox(name, [c[0] - L / 2, c[1] - w / 2, c[2] - w / 2], [c[0] + L / 2, c[1] + w / 2, c[2] + w / 2], tex)
        el["rotationOrigin"], el["rotationY"] = [round(v, 3) for v in c], round(math.degrees(math.atan2(-dz, dx)), 3)
    return el


def octo(name, x0, z0, x1, z1, y0, y1, tex="#bark"):
    """An eight-sided trunk section: a cross of two boxes and a square between."""
    cx, cz, rx, rz = (x0 + x1) / 2, (z0 + z1) / 2, (x1 - x0) / 2, (z1 - z0) / 2
    return [sbox(f"{name}A", [cx - rx, y0, cz - rz * 0.45], [cx + rx, y1, cz + rz * 0.45], tex),
            sbox(f"{name}B", [cx - rx * 0.45, y0, cz - rz], [cx + rx * 0.45, y1, cz + rz], tex),
            sbox(f"{name}C", [cx - rx * 0.82, y0, cz - rz * 0.82], [cx + rx * 0.82, y1, cz + rz * 0.82], tex)]


def deadwood_r4(part):
    if part == "root":
        els = octo("Trunk", 3, 3, 13, 13, 0, 16)
        # the flare: roots running out and down into the ground on four sides, and two between
        for i, (p, q, w) in enumerate((((8, 6, 3), (8, -1, -6), 4), ((13, 6, 8), (22, -1, 8), 4), ((8, 6, 13), (8, -1, 21), 3.5),
                                        ((3, 5, 8), (-5, -1, 8), 3.5), ((12, 4, 4), (18, -1, -1), 2.5), ((4, 4, 12), (-1, -1, 18), 2.5))):
            els.append(limb(f"Root{i}", p, q, w))
        els += octo("Flare", 1.5, 1.5, 14.5, 14.5, 0, 4)
        return shape(WOOD_TEX, els)
    if part == "trunk":
        els = octo("Lower", 3.5, 3.5, 12.5, 12.5, 0, 9) + octo("Upper", 4, 3.5, 12, 12, 9, 16)
        els += [sbox("Scar", [3, 4, 6], [3.6, 11, 9], "#char"), sbox("Knot", [11.6, 10, 7], [13, 12, 9], "#bark")]
        return shape(WOOD_TEX, els)
    # the top: the trunk narrows and splits into crooked leaders and their twigs, well above the block
    els = octo("Neck", 5, 4.5, 11, 10.5, 0, 7)
    for i, (p, q, w) in enumerate((((6, 6, 7.5), (-2, 20, 7.5), 3.2), ((-2, 20, 7.5), (-6, 32, 7.5), 2.2), ((-6, 32, 7.5), (-4, 40, 7.5), 1.2),
                                    ((10, 6, 7.5), (16, 18, 7.5), 3), ((16, 18, 7.5), (24, 27, 7.5), 2), ((24, 27, 7.5), (30, 30, 7.5), 1.2),
                                    ((8, 7, 9), (8, 22, 16), 2.4), ((8, 22, 16), (8, 34, 13), 1.6), ((8, 7, 6), (8, 17, -2), 2),
                                    ((-2, 20, 7.5), (-10, 24, 7.5), 1.3), ((16, 18, 7.5), (14, 30, 7.5), 1.4), ((8, 22, 16), (8, 27, 24), 1.1),
                                    ((8, 17, -2), (8, 25, -6), 1.1), ((-6, 32, 7.5), (-12, 35, 7.5), 0.8), ((14, 30, 7.5), (18, 36, 7.5), 0.8))):
        els.append(limb(f"Limb{i}", p, q, w))
    return shape(WOOD_TEX, els)


def deadbranch_r4(kind):
    """A bare branch from the trunk behind it (south, z 16+) out toward the front: crooked and rising (a), or reaching out
    level and forking (b); twigs off it."""
    if kind == "a":
        pts = [((8, 3, 22), (8, 6, 12), 3), ((8, 6, 12), (8, 12, 4), 2.4), ((8, 12, 4), (8, 21, -1), 1.6), ((8, 21, -1), (8, 27, 1), 1.0),
               ((8, 9, 8), (14, 14, 8), 1.2), ((14, 14, 8), (17, 20, 8), 0.8), ((8, 15, 2), (2, 19, 2), 1.0), ((2, 19, 2), (-1, 24, 2), 0.7)]
    else:
        pts = [((8, 7, 22), (8, 8, 10), 3), ((8, 8, 10), (8, 10, 0), 2.2), ((8, 10, 0), (8, 13, -8), 1.4),
               ((8, 9, 6), (0, 12, 6), 1.5), ((0, 12, 6), (-5, 18, 6), 1.0), ((8, 9, 4), (16, 13, 4), 1.4), ((16, 13, 4), (19, 19, 4), 0.9),
               ((8, 12, -4), (8, 18, -7), 0.8), ((-5, 18, 6), (-6, 22, 6), 0.6)]
    return shape(WOOD_TEX, [limb(f"B{i}", p, q, w) for i, (p, q, w) in enumerate(pts)])


def boulder_r4(kind):
    """A faceted black boulder: a core, slabs turned about the vertical round it, a tilted cap, chips at the foot."""
    tex = {"rock": T + "blackrock", "moss": T + "crust"}
    h = 11 if kind == "a" else 15
    els = [sbox("Core", [2.5, 0, 2.5], [13.5, h, 13.5], "#rock")]
    for i, (yaw, w, d, hh) in enumerate(((20, 13, 9, h - 1), (-35, 12, 10, h - 3), (65, 10, 12, h - 4))):
        el = sbox(f"Facet{i}", [8 - w / 2, 0, 8 - d / 2], [8 + w / 2, hh, 8 + d / 2], "#rock")
        el["rotationOrigin"], el["rotationY"] = [8, 0, 8], yaw
        els.append(el)
    cap = sbox("Cap", [3.5, h - 2, 4], [12.5, h + 2, 12], "#rock")
    cap["rotationOrigin"], cap["rotationZ"] = [8, h, 8], 14 if kind == "a" else -11
    els.append(cap)
    cap2 = sbox("Cap2", [5, h - 1, 3.5], [11, h + 1.5, 11], "#rock")
    cap2["rotationOrigin"], cap2["rotationX"] = [8, h, 8], 18
    els.append(cap2)
    els += [sbox("Chip0", [14, 0, 5], [17, 2.5, 8], "#rock"), sbox("Chip1", [-1, 0, 10], [2, 2, 12.5], "#rock"),
            sbox("Moss", [3, 0, 13.4], [12, 3, 14.6], "#moss")]
    if kind == "b":
        sp = sbox("Spall", [10, 0, 13], [16, 5, 17], "#rock")
        sp["rotationOrigin"], sp["rotationY"] = [13, 0, 15], 25
        els.append(sp)
    return shape(tex, els)


_shapes_castle = shapes


def shapes(write_json, shape_dir):  # noqa: F811 (the castle's pieces, then the island's)
    n = _shapes_castle(write_json, shape_dir)
    for part in ("root", "trunk", "top"):
        write_json(os.path.join(shape_dir, f"deadwood-{part}.json"), None, deadwood_r4(part))
    for k in ("a", "b"):
        write_json(os.path.join(shape_dir, f"deadbranch-{k}.json"), None, deadbranch_r4(k))
        write_json(os.path.join(shape_dir, f"boulder-{k}.json"), None, boulder_r4(k))
    return n + 7


# ================= The shore's wreckage (round 4) =================

WRECK_TEX = {"wood": T + "r4-rafters", "dark": T + "deadbark", "iron": T + "r4-iron", "rope": T + "linen"}


def wreck_shape(kind):
    """What the sea left on the beach: the ribs of a boat's hull half sunk in the ash sand along a broken keel (ribs), or
    planks of it washed up with a coil of rope (planks)."""
    els = []
    if kind == "ribs":
        els.append(limb("Keel", (-10, 1.2, 8), (26, 0.4, 8), 2.6, "#dark"))
        for i, x in enumerate((-6, 0, 6, 12, 18)):
            top = 22 if i in (1, 2) else 15 if i != 4 else 9
            for side in (-1, 1):
                if i == 3 and side > 0:
                    continue
                z0 = 8
                pts = [(x, 1, z0), (x, 6, z0 + side * 9), (x, 14, z0 + side * 12), (x, top, z0 + side * 11)]
                for k in range(3):
                    if pts[k + 1][1] > top:
                        break
                    els.append(limb(f"Rib{i}{side}{k}", pts[k], pts[k + 1], 1.6, "#wood"))
        els += [limb("Strake", (-4, 6, -1), (16, 5, -1), 1.2, "#wood"), limb("Strake2", (-6, 10, 18), (8, 9, 18), 1.0, "#wood"),
                sbox("Nail", [5.6, 13.5, -4.6], [6.4, 14.3, -3.6], "#iron")]
    else:
        for i, (p, q, w) in enumerate((((-3, 0.6, 2), (15, 0.6, 7), 2.2), ((2, 1.5, 12), (19, 1.4, 9), 1.8), ((0, 0.5, 15), (11, 0.6, 18), 1.6))):
            el = limb(f"Plank{i}", p, q, w, "#wood")
            el["to"][1] = el["from"][1] + 0.9
            els.append(el)
        for k in range(3):
            r = 3.2 - k * 0.9
            els += [sbox(f"CoilA{k}", [9 - r, 0.2 + k * 0.7, 2 - r * 0.4], [9 + r, 1 + k * 0.7, 2 + r * 0.4], "#rope"),
                    sbox(f"CoilB{k}", [9 - r * 0.4, 0.2 + k * 0.7, 2 - r], [9 + r * 0.4, 1 + k * 0.7, 2 + r], "#rope")]
        els.append(sbox("Bolt", [3, 0, 6], [5, 2, 8], "#iron"))
    return shape(WRECK_TEX, els)


_shapes_island = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_island(write_json, shape_dir)
    for k in ("ribs", "planks"):
        write_json(os.path.join(shape_dir, f"wreck-{k}.json"), None, wreck_shape(k))
    return n + 2


_blocktypes_castle = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_castle()
    out.append(oriented(
        "l73-wreck", "// Level 73: wreckage on the beach: a boat's ribs sunk in the sand, or washed-up planks and rope",
        None, "Wood", {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, coll=None,
        sounds={"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
        extra_variants=[{"code": "kind", "states": ["ribs", "planks"]}],
        shape_by={f"*-{k}-{s}": {"base": f"block/73/wreck-{k}", "rotateY": ROT[s]} for k in ("ribs", "planks") for s in SIDES},
        inv="*-ribs-north", extra={"renderpass": "OpaqueNoCull"}))
    return out


LANG.append(("block-l73-wreck-*", "Wreckage"))


# ================= The keep door's hood (round 4) =================

def hood_shape(side):
    """Half of a gabled stone hood over the keep's door (two cells wide, the wall to the north): a slate plane from the
    shared ridge (x 16 of the left cell, x 0 of the right) down to the outer edge, a stone barge and a carved bracket under
    it, the front gable's half with its trefoil, a finial at the ridge."""
    left = side == "l"
    a = 16 * SQ2
    rx = 16 if left else 0
    plane = {"name": "Plane", "from": [rx - a, 12, 0] if left else [rx, 12, 0], "to": [rx, 13.6, 12] if left else [rx + a, 13.6, 12],
             "rotationOrigin": [rx, 13.6, 0], "rotationZ": 45 if left else -45,
             "faces": {"up": face("#slate", [0, 0, 16, 12]), "down": face("#coping", [0, 0, 16, 12]), "south": face("#coping", [0, 0, 16, 1.6]),
                       ("west" if left else "east"): face("#coping", [0, 0, 12, 1.6])}}
    els = [plane]
    # the front gable under the plane: stepped stone, a dark trefoil in it
    for i in range(7):
        w = 15 - 2 * i
        x0, x1 = (16 - w, 16) if left else (0, w)
        els.append(sbox(f"Gable{i}", [x0, -2 + 2 * i, 10.5], [x1, 2 * i, 12], "#stone"))
    tx = (11.5, 16) if left else (0, 4.5)
    els += [sbox("Trefoil", [tx[0], 2.5, 12.0], [tx[1], 6.5, 12.1], "#dark"),
            sbox("Bracket", [0, -4, 1] if left else [13, -4, 1], [3, 0, 11] if left else [16, 0, 11], "#stone"),
            sbox("BracketFoot", [0.5, -7, 6] if left else [13.5, -7, 6], [2.5, -4, 11] if left else [15.5, -4, 11], "#stone")]
    if left:
        els += [sbox("Finial", [15, 13, 10.6], [17, 19.5, 12.6], "#coping"), sbox("Knop", [14.6, 19.5, 10.2], [17.4, 21, 13], "#coping")]
    return shape(STONE_TEX, els)


_shapes_wreck = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_wreck(write_json, shape_dir)
    for k in ("l", "r"):
        write_json(os.path.join(shape_dir, f"hood-{k}.json"), None, hood_shape(k))
    return n + 2


_blocktypes_wreck = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_wreck()
    out.append(jsonblock("l73-hood", "// Level 73: the gabled stone hood over the keep's door, its left and right halves (the door in a south wall)",
                         [{"code": "half", "states": ["l", "r"]}], {f"*-{k}": {"base": f"block/73/hood-{k}"} for k in ("l", "r")}, "*-l",
                         coll=None, extra={"renderpass": "OpaqueNoCull"}))
    return out


LANG.append(("block-l73-hood-*", "Door Hood"))


# ================= The castle's own seats and tables (round 4) =================
# Gothic carved mahogany and red velvet in place of the Level 5 hotel's (which stay in the hotel). Front (the sitter's view,
# the drawers) north for -north, the back to the south, like the hotel pieces they replace.

FURN_TEX = {"wood": T + "mahogany", "end": T + "mahogany-end", "velvet": T + "velvet", "gold": T + "gold", "silver": T + "silverware",
            "pages": T + "pages", "leather": T + "leather", "wax": T + "wax"}


def turned(name, x, z, y0, y1, r=0.8, tex="#end"):
    """A turned leg or post (x, z its middle): a shaft with a collar or two."""
    els = [box(f"{name}", [x - r, y0, z - r], [x + r, y1, z + r], tex)]
    h = y1 - y0
    for i, f in enumerate((0.12, 0.5) if h > 6 else (0.3,)):
        y = y0 + h * f
        els.append(box(f"{name}C{i}", [x - r - 0.35, y, z - r - 0.35], [x + r + 0.35, y + 0.8, z + r + 0.35], tex))
    return els


def chair_shape():
    """A carved side chair: turned legs on an H-stretcher, a velvet seat at 0.5, a tall back with a pointed crest and
    finials, a velvet panel between its posts."""
    els = []
    for i, (x, z) in enumerate(((2.8, 2.8), (13.2, 2.8))):
        els += turned(f"LegF{i}", x, z, 0, 7.2)
    for i, x in enumerate((2.8, 13.2)):
        els += turned(f"Post{i}", x, 13.2, 0, 24.5)
        els += [box(f"Finial{i}", [x - 0.6, 24.5, 12.6], [x + 0.6, 26.5, 13.8], "#end"),
                box(f"Knob{i}", [x - 0.9, 26.5, 12.3], [x + 0.9, 27.6, 14.1], "#gold")]
    els += [box("StretchL", [2.3, 2.2, 3], [3.3, 3.0, 13], "#end"), box("StretchR", [12.7, 2.2, 3], [13.7, 3.0, 13], "#end"),
            box("StretchX", [3.3, 2.4, 7.6], [12.7, 3.1, 8.4], "#end"),
            box("SeatFrame", [1.6, 7.2, 1.6], [14.4, 8.6, 14.4], "#wood"),
            box("Cushion", [2.2, 8.6, 2.0], [13.8, 9.9, 13.0], "#velvet"),
            box("Piping", [2.0, 8.5, 1.8], [14.0, 8.9, 2.2], "#gold"),
            box("RailLow", [3.6, 11, 12.8], [12.4, 12.2, 13.8], "#wood"),
            box("Panel", [3.6, 12.2, 13.0], [12.4, 21, 13.6], "#velvet"),
            box("RailTop", [3.6, 21, 12.6], [12.4, 23, 14.0], "#wood"),
            box("Crest1", [5.2, 23, 12.8], [10.8, 24.4, 13.8], "#wood"),
            box("Crest2", [6.6, 24.4, 12.8], [9.4, 25.8, 13.8], "#wood"),
            box("Crest3", [7.5, 25.8, 12.9], [8.5, 27.4, 13.7], "#gold")]
    return shape(FURN_TEX, els)


def wingchair_shape():
    """A wing chair in red velvet on a carved frame: bun feet, a deep seat, rolled arms, a high back with wings, brass studs."""
    els = []
    for i, (x, z) in enumerate(((2.2, 2.2), (13.8, 2.2), (2.2, 13.6), (13.8, 13.6))):
        els += [box(f"Foot{i}", [x - 1.1, 0, z - 1.1], [x + 1.1, 1.8, z + 1.1], "#end"),
                box(f"Leg{i}", [x - 0.7, 1.8, z - 0.7], [x + 0.7, 3.4, z + 0.7], "#end")]
    els += [box("Base", [1, 3.4, 1], [15, 6.5, 15], "#velvet"), box("Apron", [0.8, 3.2, 0.8], [15.2, 4.0, 15.2], "#wood"),
            box("Cushion", [3.2, 6.5, 1.6], [12.8, 8.6, 13], "#velvet"),
            box("Back", [2.4, 6.5, 13], [13.6, 24, 15.2], "#velvet"), box("BackTop", [3, 24, 13.2], [13, 25.4, 15], "#velvet"),
            box("WingL", [1, 12, 9.5], [3.2, 23, 15.2], "#velvet"), box("WingR", [12.8, 12, 9.5], [15, 23, 15.2], "#velvet"),
            box("ArmL", [0.8, 6.5, 1.2], [3.4, 12.2, 13], "#velvet"), box("ArmR", [12.6, 6.5, 1.2], [15.2, 12.2, 13], "#velvet"),
            box("RollL", [0.4, 10.4, 1.0], [3.8, 12.8, 3.2], "#velvet"), box("RollR", [12.2, 10.4, 1.0], [15.6, 12.8, 3.2], "#velvet")]
    for i, y in enumerate((7.5, 9.5)):
        els += [box(f"StudL{i}", [1.4, y, 0.7], [2.2, y + 0.7, 1.05], "#gold"), box(f"StudR{i}", [13.8, y, 0.7], [14.6, y + 0.7, 1.05], "#gold")]
    return shape(FURN_TEX, els)


def settee_shape(part):
    """Half of a long carved settee (two cells): 'l' the left end as one sits on it (x low), 'r' the right; an arm at the
    outer end, the back's carved top rail with a crest at the middle, a velvet seat and back, turned legs."""
    left = part == "l"
    outer = 0.0 if left else 16.0
    s = 1 if left else -1
    els = []
    for i, z in enumerate((2.5, 13.5)):
        els += turned(f"Leg{i}", outer + s * 2.2, z, 0, 4.6, r=0.9)
    els += [box("Rail", [0, 4.6, 1.6], [16, 6.2, 15], "#wood"),
            box("Seat", [0, 6.2, 2], [16, 8.6, 13.4], "#velvet"),
            box("Back", [0, 6.2, 13.4], [16, 20, 15], "#velvet"),
            box("TopRail", [0, 20, 13.2], [16, 21.6, 15.2], "#wood"),
            box("Piping", [0, 8.4, 1.8], [16, 8.8, 2.2], "#gold")]
    ax0, ax1 = (0.4, 3.0) if left else (13.0, 15.6)
    px0, px1 = (0.2, 2.0) if left else (14.0, 15.8)
    els += [box("Arm", [ax0, 6.2, 2], [ax1, 12, 13.4], "#velvet"), box("ArmTop", [ax0 - 0.3, 12, 1.4], [ax1 + 0.3, 13.2, 13.6], "#wood"),
            box("ArmPost", [ax0, 4.6, 1.2], [ax1, 13.2, 2.4], "#wood"),
            box("EndPost", [px0, 4.6, 13.2], [px1, 22.5, 15.2], "#end"),
            box("EndFinial", [px0 + 0.2, 22.5, 13.5], [px1 - 0.2, 24, 14.9], "#gold")]
    c0, c1 = (11, 16) if left else (0, 5)
    d0, d1 = (14, 16) if left else (0, 2)
    els += [box("Crest", [c0, 21.6, 13.4], [c1, 23.2, 15], "#wood"), box("Crest2", [d0, 23.2, 13.5], [d1, 24.8, 14.9], "#wood")]
    return shape(FURN_TEX, els)


def sideboard_shape():
    """A carved mahogany sideboard against the wall (south): bracket feet, a plinth, two panelled doors and a drawer with
    brass pulls, a moulded top; on it a silver tray, a decanter and two glasses, a candlestick."""
    els = [box("Plinth", [0.6, 1.2, 3.4], [15.4, 2.2, 15.6], "#end")]
    for i, x in enumerate((0.6, 13.6)):
        for j, z in enumerate((3.4, 13.6)):
            els.append(box(f"Foot{i}{j}", [x, 0, z], [x + 1.8, 1.2, z + 2.0], "#end"))
    els += [box("Carcass", [0.8, 2.2, 4], [15.2, 12.6, 15.6], "#wood"),
            box("Top", [0.2, 12.6, 3.2], [15.8, 13.6, 16], "#end"),
            box("Drawer", [1.6, 10.2, 3.6], [14.4, 12.2, 4], "#wood"),
            box("Pull", [7.0, 10.9, 3.2], [9.0, 11.5, 3.6], "#gold"),
            box("DoorL", [1.6, 3, 3.6], [7.8, 9.8, 4], "#wood"), box("DoorR", [8.2, 3, 3.6], [14.4, 9.8, 4], "#wood"),
            box("PanelL", [2.6, 4, 3.3], [6.8, 8.8, 3.6], "#end"), box("PanelR", [9.2, 4, 3.3], [13.4, 8.8, 3.6], "#end"),
            box("KnobL", [6.8, 6.2, 3.0], [7.4, 6.8, 3.6], "#gold"), box("KnobR", [8.6, 6.2, 3.0], [9.2, 6.8, 3.6], "#gold"),
            box("Tray", [3, 13.6, 7], [10, 14.0, 13], "#silver"),
            box("Decanter", [4.2, 14.0, 8.6], [6.2, 17.2, 10.6], "#silver"), box("Neck", [4.8, 17.2, 9.2], [5.6, 19, 10.0], "#silver"),
            box("Stopper", [4.6, 19, 9.0], [5.8, 19.8, 10.2], "#silver"),
            box("Glass1", [7.2, 14.0, 8.8], [8.2, 16.0, 9.8], "#silver"), box("Glass2", [8.6, 14.0, 10.6], [9.6, 16.0, 11.6], "#silver"),
            box("StickBase", [11.6, 13.6, 9.6], [13.6, 14.2, 11.6], "#gold"), box("Stick", [12.3, 14.2, 10.3], [12.9, 17.6, 10.9], "#gold"),
            box("Candle", [12.2, 17.6, 10.2], [13.0, 20.6, 11.0], "#wax")]
    return shape(FURN_TEX, els)


def lowtable_shape():
    """A low carved table before the fire: turned legs, a stretcher, a moulded top; a book open on it and a candlestick."""
    els = []
    for i, (x, z) in enumerate(((2.2, 3.2), (13.8, 3.2), (2.2, 12.8), (13.8, 12.8))):
        els += turned(f"Leg{i}", x, z, 0, 6.6, r=0.8)
    els += [box("StretchA", [2.2, 1.6, 7.6], [13.8, 2.3, 8.4], "#end"),
            box("Apron", [1.4, 6.0, 2.4], [14.6, 7.0, 13.6], "#wood"),
            box("Top", [0.6, 7.0, 1.6], [15.4, 8.0, 14.4], "#end"),
            box("BookL", [3.5, 8.0, 5.5], [6.6, 8.6, 10.5], "#pages"), box("BookR", [6.6, 8.0, 5.5], [9.7, 8.6, 10.5], "#pages"),
            box("Cover", [3.3, 7.95, 5.3], [9.9, 8.1, 10.7], "#leather"),
            box("StickBase", [11.4, 8.0, 8.4], [13.2, 8.5, 10.2], "#gold"), box("Stick", [12.0, 8.5, 9.0], [12.6, 11.2, 9.6], "#gold"),
            box("Candle", [11.9, 11.2, 8.9], [12.7, 13.6, 9.7], "#wax")]
    return shape(FURN_TEX, els)


FURNITURE = {"chair": chair_shape, "wingchair": wingchair_shape, "sideboard": sideboard_shape, "lowtable": lowtable_shape}

_shapes_hood = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_hood(write_json, shape_dir)
    for k, fn in FURNITURE.items():
        write_json(os.path.join(shape_dir, f"{k}.json"), None, fn())
    for p in ("l", "r"):
        write_json(os.path.join(shape_dir, f"settee-{p}.json"), None, settee_shape(p))
    return n + len(FURNITURE) + 2


_blocktypes_hood = blocktypes

FURN_SOUNDS = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}


def blocktypes():  # noqa: F811
    out = _blocktypes_hood()
    seat = {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.6, "z2": 0.9}
    for code, sel, coll, comment in (
            ("chair", {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 1.6, "z2": 0.9}, seat, "a carved side chair, velvet seat, tall pointed back"),
            ("wingchair", {"x1": 0.05, "y1": 0, "z1": 0.05, "x2": 0.95, "y2": 1.6, "z2": 0.95}, seat, "a wing chair in red velvet"),
            ("sideboard", {"x1": 0, "y1": 0, "z1": 0.2, "x2": 1, "y2": 0.85, "z2": 1}, {"x1": 0, "y1": 0, "z1": 0.2, "x2": 1, "y2": 0.85, "z2": 1},
             "a carved sideboard against the wall, silver on it"),
            ("lowtable", {"x1": 0.05, "y1": 0, "z1": 0.1, "x2": 0.95, "y2": 0.5, "z2": 0.9}, {"x1": 0.05, "y1": 0, "z1": 0.1, "x2": 0.95, "y2": 0.5, "z2": 0.9},
             "a low carved table, a book and a candle on it")):
        out.append(oriented(f"l73-{code}", f"// Level 73 (round 4): {comment} (front north for -north)", f"block/73/{code}", "Wood", sel,
                            coll=coll, sounds=FURN_SOUNDS))
    out.append(oriented("l73-settee", "// Level 73 (round 4): a long carved settee, its left (l) and right (r) halves as one sits on it (facing north for -north)",
                        None, "Wood", {"x1": 0, "y1": 0, "z1": 0.1, "x2": 1, "y2": 1.4, "z2": 1}, coll=seat, sounds=FURN_SOUNDS,
                        extra_variants=[{"code": "part", "states": ["l", "r"]}],
                        shape_by={f"*-{p}-{s}": {"base": f"block/73/settee-{p}", "rotateY": ROT[s]} for p in ("l", "r") for s in SIDES},
                        inv="*-l-north"))
    return out


LANG += [("block-l73-chair-*", "Carved Chair"), ("block-l73-wingchair-*", "Wing Chair"), ("block-l73-sideboard-*", "Sideboard"),
         ("block-l73-lowtable-*", "Low Table"), ("block-l73-settee-*", "Settee")]


# ---- More of the castle's own furniture (round 4): the armoire, the bedside cabinet, the chest of drawers, the writing desk ----

FURN_TEX["mirror"] = T + "mirror"
FURN_TEX["ink"] = T + "r4-dark"


def armoire_shape():
    """A tall carved armoire against the wall (south), near two blocks high: a plinth on bracket feet, two doors with
    pointed-arch panels and brass handles, pilasters, a deep cornice with a crest."""
    els = [box("Plinth", [0.4, 1, 1.6], [15.6, 2.6, 16], "#end")]
    for i, x in enumerate((0.4, 13.8)):
        els.append(box(f"Foot{i}", [x, 0, 1.6], [x + 1.8, 1, 3.6], "#end"))
    els += [box("Carcass", [0.8, 2.6, 2.4], [15.2, 27, 16], "#wood"),
            box("PilasterL", [0.4, 2.6, 2.0], [1.8, 27, 2.8], "#end"), box("PilasterR", [14.2, 2.6, 2.0], [15.6, 27, 2.8], "#end"),
            box("Meeting", [7.6, 3.2, 2.0], [8.4, 26.2, 2.4], "#end"),
            box("Cornice", [0, 27, 1.4], [16, 28.6, 16], "#end"), box("CorniceTop", [0.4, 28.6, 1.8], [15.6, 29.4, 16], "#wood"),
            box("Crest", [5.5, 29.4, 2.2], [10.5, 30.6, 3.0], "#end"), box("Crest2", [7, 30.6, 2.2], [9, 31.6, 3.0], "#gold")]
    for side, (x0, x1) in (("L", (2.6, 6.8)), ("R", (9.2, 13.4))):
        els += [box(f"Panel{side}", [x0, 5, 2.1], [x1, 20, 2.4], "#end"),
                box(f"Arch{side}", [x0 + 0.8, 20, 2.1], [x1 - 0.8, 22, 2.4], "#end"),
                box(f"Arch2{side}", [x0 + 1.6, 22, 2.1], [x1 - 1.6, 23.2, 2.4], "#end"),
                box(f"PanelLow{side}", [x0, 3.4, 2.1], [x1, 4.4, 2.4], "#end")]
    els += [box("HandleL", [6.8, 13, 1.6], [7.4, 16, 2.4], "#gold"), box("HandleR", [8.6, 13, 1.6], [9.2, 16, 2.4], "#gold"),
            box("Escutcheon", [7.7, 11.5, 1.8], [8.3, 12.5, 2.0], "#gold")]
    return shape(FURN_TEX, els)


def bedside_shape():
    """A bedside cabinet: turned legs, a drawer and a cupboard door, a moulded top; a candlestick and a small book on it."""
    els = []
    for i, (x, z) in enumerate(((2.4, 3.4), (13.6, 3.4), (2.4, 14.2), (13.6, 14.2))):
        els += turned(f"Leg{i}", x, z, 0, 3.0, r=0.8)
    els += [box("Body", [1.6, 3, 2.6], [14.4, 11.6, 15], "#wood"),
            box("Top", [1.0, 11.6, 2.0], [15.0, 12.6, 15.6], "#end"),
            box("Drawer", [2.6, 9.0, 2.3], [13.4, 11.0, 2.6], "#end"), box("Pull", [7.2, 9.7, 1.9], [8.8, 10.3, 2.3], "#gold"),
            box("Door", [2.6, 3.8, 2.3], [13.4, 8.4, 2.6], "#end"), box("Knob", [11.6, 5.8, 1.9], [12.2, 6.4, 2.3], "#gold"),
            box("StickBase", [3.4, 12.6, 6], [5.4, 13.2, 8], "#gold"), box("Stick", [4.1, 13.2, 6.7], [4.7, 16.4, 7.3], "#gold"),
            box("Candle", [4.0, 16.4, 6.6], [4.8, 18.8, 7.4], "#wax"),
            box("Book", [8, 12.6, 6.5], [12.5, 13.6, 12], "#leather")]
    return shape(FURN_TEX, els)


def drawers_shape():
    """A chest of drawers against the wall (south): bun feet, four drawers with brass pulls, a moulded top; a swing mirror
    in a carved frame standing on it."""
    els = []
    for i, (x, z) in enumerate(((1.6, 4.0), (14.4, 4.0), (1.6, 14.4), (14.4, 14.4))):
        els.append(box(f"Foot{i}", [x - 1.0, 0, z - 1.0], [x + 1.0, 1.4, z + 1.0], "#end"))
    els += [box("Carcass", [0.6, 1.4, 3.6], [15.4, 13.4, 15.8], "#wood"),
            box("Top", [0.2, 13.4, 3.0], [15.8, 14.4, 16], "#end")]
    for k in range(4):
        y = 2.0 + 2.8 * k
        els += [box(f"Drawer{k}", [1.4, y, 3.3], [14.6, y + 2.4, 3.6], "#end"),
                box(f"PullL{k}", [4.0, y + 0.9, 2.9], [5.4, y + 1.5, 3.3], "#gold"), box(f"PullR{k}", [10.6, y + 0.9, 2.9], [12.0, y + 1.5, 3.3], "#gold")]
    els += [box("StandL", [3.6, 14.4, 11], [4.6, 22, 12], "#end"), box("StandR", [11.4, 14.4, 11], [12.4, 22, 12], "#end"),
            box("Frame", [4.6, 15.4, 11.2], [11.4, 23.4, 12.0], "#end"),
            box("Glass", [5.4, 16.2, 11.0], [10.6, 22.6, 11.2], "#mirror"),
            box("FrameCrest", [6.6, 23.4, 11.2], [9.4, 24.6, 12.0], "#gold")]
    return shape(FURN_TEX, els)


def desk_shape():
    """A writing desk against the wall (south): turned legs, a drawer, a leather-topped desk, a gallery of pigeonholes at
    the back with letters in them, an inkwell and quill, papers."""
    els = []
    for i, (x, z) in enumerate(((1.8, 2.4), (14.2, 2.4), (1.8, 14.2), (14.2, 14.2))):
        els += turned(f"Leg{i}", x, z, 0, 10.8, r=0.85)
    els += [box("Apron", [1.0, 10.8, 1.6], [15.0, 12.2, 15.2], "#wood"),
            box("Drawer", [5, 11.0, 1.3], [11, 12.0, 1.6], "#end"), box("Pull", [7.4, 11.3, 1.0], [8.6, 11.7, 1.3], "#gold"),
            box("Top", [0.4, 12.2, 1.0], [15.6, 13.0, 15.8], "#end"),
            box("Leather", [2.0, 13.0, 2.4], [14.0, 13.15, 10.4], "#leather"),
            box("Gallery", [0.8, 13.0, 11.0], [15.2, 19.0, 15.6], "#wood"),
            box("GalleryTop", [0.4, 19.0, 10.6], [15.6, 19.8, 15.8], "#end")]
    for k in range(4):
        x = 1.6 + 3.5 * k
        els += [box(f"Hole{k}", [x, 13.8, 10.9], [x + 2.8, 18.2, 11.4], "#ink"),
                box(f"Letter{k}", [x + 0.4, 13.8, 11.0], [x + 2.4, 16.4 + 0.6 * (k % 2), 11.6], "#pages")]
    els += [box("Inkwell", [11.2, 13.0, 4.8], [12.6, 14.2, 6.2], "#ink"), box("Quill", [12.0, 14.2, 5.2], [12.3, 18.4, 5.5], "#pages"),
            box("Paper", [4.0, 13.15, 4.0], [9.0, 13.3, 8.6], "#pages")]
    return shape(FURN_TEX, els)


FURNITURE2 = {"armoire": armoire_shape, "bedside": bedside_shape, "drawers": drawers_shape, "desk": desk_shape}

_shapes_furn = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_furn(write_json, shape_dir)
    for k, fn in FURNITURE2.items():
        write_json(os.path.join(shape_dir, f"{k}.json"), None, fn())
    return n + len(FURNITURE2)


_blocktypes_furn = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_furn()
    for code, h, comment in (("armoire", 1.95, "a tall carved armoire against the wall"), ("bedside", 0.8, "a bedside cabinet, a candle on it"),
                             ("drawers", 0.9, "a chest of drawers, a swing mirror on it"), ("desk", 0.85, "a writing desk with its pigeonholes")):
        box_ = {"x1": 0.02, "y1": 0, "z1": 0.08, "x2": 0.98, "y2": h, "z2": 1}
        out.append(oriented(f"l73-{code}", f"// Level 73 (round 4): {comment} (front north for -north, the wall to the south)", f"block/73/{code}",
                            "Wood", box_, coll=dict(box_, y2=min(1.0, h)), sounds=FURN_SOUNDS))
    return out


LANG += [("block-l73-armoire-*", "Armoire"), ("block-l73-bedside-*", "Bedside Cabinet"), ("block-l73-drawers-*", "Chest of Drawers"),
         ("block-l73-desk-*", "Writing Desk")]


# ---- The longcase clock in the main hall (round 4) ----

def clock_dial(seed):
    """A clock's dial: an aged cream face in a brass ring, twelve hour marks, the hands stopped near a quarter to twelve."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 15.5, y - 15.5)
            if d <= 15.5:
                px[x, y] = M.rgba((168, 132, 58)) if d > 13.5 else M.rgba(M.lift((214, 200, 168), -d * 0.8))
            else:
                px[x, y] = M.rgba((52, 22, 14))
    for k in range(12):
        a = k * math.pi / 6
        for r in (11, 12):
            x, y = int(round(15.5 + r * math.sin(a))), int(round(15.5 - r * math.cos(a)))
            px[x, y] = M.rgba((30, 26, 24))
    for r in range(1, 9):  # the minute hand (toward 11:45, the 9)
        px[int(round(15.5 - r)), 15] = M.rgba((24, 20, 20))
    for r in range(1, 6):  # the hour hand (toward 12)
        px[15, int(round(15.5 - r))] = M.rgba((24, 20, 20))
        px[16, int(round(15.5 - r))] = M.rgba((24, 20, 20))
    M.grime(img, 0.15, seed=seed, color=(120, 100, 60), cover=0.4)
    return img


_textures_furn = textures


def textures(save):  # noqa: F811
    n = _textures_furn(save)
    save(clock_dial(7720), "block/73/r4-dial")
    return n + 1


def clock_shape():
    """A longcase clock against the wall (south), two blocks and more: a plinth, the waist with its door and a glass to
    the brass pendulum, the hood with its dial under a broken pediment and finials."""
    tex = dict(FURN_TEX, dial=T + "r4-dial", glass=T + "r4-leaded")
    els = [box("Plinth", [2, 0, 6], [14, 7, 16], "#wood"), box("PlinthTop", [1.6, 7, 5.6], [14.4, 8, 16], "#end"),
           box("Base", [1.6, 0, 5.6], [14.4, 1, 16], "#end"),
           box("Waist", [3.4, 8, 7.4], [12.6, 22, 16], "#wood"),
           box("Door", [4.4, 9, 7.0], [11.6, 21, 7.4], "#end"),
           box("Window", [6, 12, 6.9], [10, 19, 7.0], "#glass"),
           box("Bob", [7.2, 13, 6.85], [8.8, 14.6, 6.9], "#gold"), box("Rod", [7.8, 14.6, 6.85], [8.2, 19, 6.9], "#gold"),
           box("Collar", [2.6, 22, 6.6], [13.4, 23.2, 16], "#end"),
           box("Hood", [2.2, 23.2, 6.2], [13.8, 34, 16], "#wood"),
           {"name": "Dial", "from": [3.6, 24.8, 6.1], "to": [12.4, 33.6, 6.2], "faces": {"north": face("#dial", [0, 0, 16, 16])}},
           box("ColL", [2.0, 23.2, 5.8], [3.2, 34, 7.0], "#end"), box("ColR", [12.8, 23.2, 5.8], [14.0, 34, 7.0], "#end"),
           box("Cornice", [1.6, 34, 5.6], [14.4, 35.4, 16], "#end"),
           box("PedL", [1.8, 35.4, 6.0], [6.4, 37.4, 7.4], "#end"), box("PedR", [9.6, 35.4, 6.0], [14.2, 37.4, 7.4], "#end"),
           box("Urn", [7.2, 35.4, 6.4], [8.8, 38.4, 8.0], "#gold"),
           box("FinL", [2.2, 35.4, 7.6], [3.4, 38, 8.8], "#gold"), box("FinR", [12.6, 35.4, 7.6], [13.8, 38, 8.8], "#gold")]
    return shape(tex, els)


_shapes_furn2 = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_furn2(write_json, shape_dir)
    write_json(os.path.join(shape_dir, "clock.json"), None, clock_shape())
    return n + 1


_blocktypes_furn2 = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_furn2()
    sel = {"x1": 0.1, "y1": 0, "z1": 0.35, "x2": 0.9, "y2": 2.2, "z2": 1}
    out.append(oriented("l73-clock", "// Level 73 (round 4): a longcase clock against the wall, stopped (front north for -north)", "block/73/clock",
                        "Wood", sel, coll=dict(sel, y2=1.0), sounds=FURN_SOUNDS))
    return out


LANG.append(("block-l73-clock-*", "Longcase Clock"))


# ---- The bathroom's close stool (round 4): a panelled mahogany box seat with a hinged lid, in place of the hotel's toilet ----

def privy_shape():
    els = [box("Plinth", [1.0, 0, 3.0], [15.0, 1.2, 15.6], "#end"),
           box("Box", [1.4, 1.2, 3.4], [14.6, 7.6, 15.2], "#wood"),
           box("PanelF", [3.0, 2.4, 3.1], [13.0, 6.4, 3.4], "#end"),
           box("Seat", [1.0, 7.6, 3.0], [15.0, 8.6, 15.6], "#end"),
           box("Lid", [2.0, 8.6, 13.0], [14.0, 17.0, 14.0], "#wood"),
           box("LidPanel", [3.4, 10.0, 12.7], [12.6, 15.6, 13.0], "#end"),
           box("HingeL", [3.6, 8.4, 13.6], [5.0, 9.2, 14.6], "#gold"), box("HingeR", [11.0, 8.4, 13.6], [12.4, 9.2, 14.6], "#gold"),
           box("Back", [1.0, 7.6, 14.2], [15.0, 19.0, 15.8], "#wood"), box("BackCrest", [5.0, 19.0, 14.4], [11.0, 20.6, 15.6], "#end"),
           box("Ewer", [12.4, 8.6, 4.6], [14.4, 11.6, 6.6], "#silver")]
    return shape(FURN_TEX, els)


_shapes_clock = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_clock(write_json, shape_dir)
    write_json(os.path.join(shape_dir, "privy.json"), None, privy_shape())
    return n + 1


_blocktypes_clock = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_clock()
    sel = {"x1": 0.06, "y1": 0, "z1": 0.18, "x2": 0.94, "y2": 1.25, "z2": 1}
    out.append(oriented("l73-privy", "// Level 73 (round 4): the bathroom's close stool, a panelled box seat (front north for -north)", "block/73/privy",
                        "Wood", sel, coll=dict(sel, y2=0.55), sounds=FURN_SOUNDS))
    return out


LANG.append(("block-l73-privy-*", "Close Stool"))


# ---- A string course (round 4): a wall block with a moulded drip standing out from its outer face (and the west for the corner) ----

def stringcourse_shape(corner):
    els = [box("Wall", [0, 0, 0], [16, 16, 16], "#stone"),
           box("MouldN", [-1.6 if corner else 0, 12, -1.6], [16, 14, 0], "#coping"),
           box("DripN", [-1.0 if corner else 0, 11, -1.0], [16, 12, 0], "#coping"),
           box("WashN", [-0.8 if corner else 0, 14, -0.8], [16, 15, 0], "#coping")]
    if corner:
        els += [box("MouldW", [-1.6, 12, 0], [0, 14, 16], "#coping"), box("DripW", [-1.0, 11, 0], [0, 12, 16], "#coping"),
                box("WashW", [-0.8, 14, 0], [0, 15, 16], "#coping")]
    return shape(STONE_TEX, els)


_shapes_privy = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_privy(write_json, shape_dir)
    for k in ("straight", "corner"):
        write_json(os.path.join(shape_dir, f"string-{k}.json"), None, stringcourse_shape(k == "corner"))
    return n + 2


_blocktypes_privy = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_privy()
    out.append(oriented(
        "l73-string", "// Level 73: a string course, a wall block with a moulded drip on its outer face (-north: north; corner: and west)",
        None, "Stone", FULL, coll=FULL, sounds=STONE, extra_variants=[{"code": "kind", "states": ["straight", "corner"]}],
        shape_by={f"*-{k}-{s}": {"base": f"block/73/string-{k}", "rotateY": ROT[s]} for k in ("straight", "corner") for s in SIDES},
        inv="*-straight-north"))
    return out


LANG.append(("block-l73-string-*", "String Course"))


# ---- Bartizans (round 4): little round corbelled turrets with conical roofs at the corner towers' outer corners ----

def bartizan_shape():
    """At the outer corner of a corner tower's parapet (-north: the north-west corner, i.e. the corner variant's): a round
    turret 1.1 blocks across standing out diagonally on a corbelled base, an arrow slit looking out along the diagonal, a
    slate cone with an iron finial."""
    cx = cz = 2.5
    els = []

    def ring(name, r, y0, y1, tex):
        a, b, c = r, r * 0.42, r * 0.8
        return [sbox(f"{name}A", [cx - a, y0, cz - b], [cx + a, y1, cz + b], tex),
                sbox(f"{name}B", [cx - b, y0, cz - a], [cx + b, y1, cz + a], tex),
                sbox(f"{name}C", [cx - c, y0, cz - c], [cx + c, y1, cz + c], tex)]
    # the corbelled base, stepping out from the tower's corner
    for i, (r, y0, y1) in enumerate(((3.5, -14, -10), (5.5, -10, -6), (7.5, -6, -2), (9, -2, 0))):
        els += ring(f"Base{i}", r, y0, y1, "#stone")
    els += ring("Body", 9, 0, 13, "#streak")
    els += ring("Band", 9.6, 13, 14.4, "#coping")
    slit = sbox("Slit", [cx - 0.9, 3, cz - 9.25], [cx + 0.9, 10, cz - 8.6], "#dark")
    slit["rotationOrigin"], slit["rotationY"] = [cx, 0, cz], 45  # (turned to look out along the north-west diagonal)
    els.append(slit)
    n = 7
    for i in range(n):
        r = 10.4 * (1 - i / n) ** 1.05
        y0, y1 = 14.4 + 3.6 * i, 14.4 + 3.6 * (i + 1)
        els += ring(f"Cone{i}", max(r, 0.8), y0, y1, "#slate")
    top = 14.4 + 3.6 * n
    els += [sbox("Rod", [cx - 0.35, top, cz - 0.35], [cx + 0.35, top + 7, cz + 0.35], "#iron"),
            sbox("Ball", [cx - 0.9, top + 2, cz - 0.9], [cx + 0.9, top + 3.8, cz + 0.9], "#iron")]
    return shape(STONE_TEX, els)


_shapes_string = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_string(write_json, shape_dir)
    write_json(os.path.join(shape_dir, "bartizan.json"), None, bartizan_shape())
    return n + 1


_blocktypes_string = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_string()
    out.append(oriented("l73-bartizan", "// Level 73: a bartizan, a corbelled round turret with a slate cone at a corner tower's outer corner (-north: the north-west)",
                        "block/73/bartizan", "Stone", FULL, coll=FULL, sounds=STONE, extra={"renderpass": "OpaqueNoCull"}))
    return out


LANG.append(("block-l73-bartizan-*", "Bartizan"))


# ---- The castle's stairs (round 4): the hotel's grand stair's geometry in dark oak with a red velvet runner and gilt rods ----

_HERE = os.path.dirname(os.path.abspath(__file__))


def stairs_shape():
    import json
    with open(os.path.join(_HERE, "..", "assets", "backrooms", "shapes", "block", "hotelstairs-runner.json"), encoding="utf-8") as f:
        s = json.load(f)
    s["textures"] = {"marble": T + "mahogany-end", "carpet": T + "velvet", "brass": T + "gold"}
    return s


_shapes_bart = shapes


def shapes(write_json, shape_dir):  # noqa: F811
    n = _shapes_bart(write_json, shape_dir)
    write_json(os.path.join(shape_dir, "stairs.json"), None, stairs_shape())
    return n + 1


_blocktypes_bart = blocktypes


def blocktypes():  # noqa: F811
    out = _blocktypes_bart()
    boxes = {"north": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0, "x2": 1, "y2": 1, "z2": 0.5}],
             "east": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0.5, "y1": 0.5, "z1": 0, "x2": 1, "y2": 1, "z2": 1}],
             "south": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0.5, "x2": 1, "y2": 1, "z2": 1}],
             "west": [{"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.5, "z2": 1}, {"x1": 0, "y1": 0.5, "z1": 0, "x2": 0.5, "y2": 1, "z2": 1}]}
    out.append(("// Level 73 (round 4): the castle's oak stairs with a red velvet runner, climbing toward the variant's side (the hotel stair's geometry)", fixed({
        "code": "l73-stairs", "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}, "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": "block/73/stairs", "rotateY": ROT[s]} for s in SIDES},
        "collisionSelectionBoxesByType": {f"*-{s}": boxes[s] for s in SIDES},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "drops": [],
        "sounds": {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}})))
    return out


LANG.append(("block-l73-stairs-*", "Oak Stairs"))
