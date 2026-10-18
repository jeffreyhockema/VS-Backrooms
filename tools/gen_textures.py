"""Generates the placeholder textures and mod icon procedurally.

Colours and patterns follow the original 2002 Backrooms photos: dingy pale yellow wallpaper with alternating
columns of beaded lines and stacked chevrons (or a dot grid on some walls), brownish-beige Berber carpet,
fissured drop-ceiling tiles and prismatic troffer lights.

Run from the repo root:  python tools/gen_textures.py
Re-running overwrites the PNGs, so once a texture has been hand-painted, remove it from this script.
"""
import math
import os
import random

import matlib as M
import texlib

import iconkit  # B17: finishing for 2D item icons

from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), "..")
TEX = os.path.join(ROOT, "assets", "backrooms", "textures")
S = 32  # block texture size


# Block textures share one atlas, packed edge to edge with no padding, and mipmapped three levels down (8 pixels to a
# texel at the coarsest). A texture whose width or height is not a multiple of 8 leaves the space after it in the
# atlas off that grid, so whatever is packed there next (Level 0's carpet, say) has its coarse texels straddle two
# textures, and far off its block edges show as a bright grid. Every vanilla block texture is a multiple of 8.
ATLAS_GRID = 8


def check_atlas_grid(img, rel):
    """Refuses a block texture that would knock the atlas off its mipmap grid (see ATLAS_GRID)."""
    if rel.replace("\\", "/").startswith("block/") and (img.width % ATLAS_GRID or img.height % ATLAS_GRID):
        raise ValueError(f"{rel} is {img.width}x{img.height}: block textures must be multiples of {ATLAS_GRID} on both sides "
                         "(scale it up with fit_atlas_grid, or pad it with pad_to_atlas_grid and map the face to the original part)")


def fit_atlas_grid(img):
    """The smallest whole-number nearest-neighbour enlargement (up to 4x) that puts both sides on the atlas grid,
    so a picture mapped over its whole face looks exactly the same; None if there is none."""
    for k in range(1, 5):
        if (img.width * k) % ATLAS_GRID == 0 and (img.height * k) % ATLAS_GRID == 0:
            return img if k == 1 else img.resize((img.width * k, img.height * k), Image.NEAREST)
    return None


def pad_to_atlas_grid(img):
    """The picture padded on the right and bottom to the atlas grid, with its edge pixels repeated outwards (so its
    own mipmaps blend into its own colours), and the face UV, in 16ths, that shows just the original picture."""
    w, h = img.width, img.height
    W, H = -(-w // ATLAS_GRID) * ATLAS_GRID, -(-h // ATLAS_GRID) * ATLAS_GRID
    out = Image.new(img.mode, (W, H))
    out.paste(img, (0, 0))
    src, px = img.load(), out.load()
    for y in range(H):
        for x in range(W):
            if x >= w or y >= h:
                px[x, y] = src[min(x, w - 1), min(y, h - 1)]
    return out, (0, 0, 16 * w / W, 16 * h / H)


def save(img, rel):
    check_atlas_grid(img, rel)
    if iconkit.is_icon(rel):
        img = iconkit.finish(img, seed=rel)        # B17: a 2D item icon is lit and outlined as vanilla's are
    path = os.path.join(TEX, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def hexrgb(h):
    return ((h >> 16) & 255, (h >> 8) & 255, h & 255)


def clamp(v):
    return max(0, min(255, int(v)))


def shade(c, f):
    return tuple(clamp(v * f) for v in c[:3]) + (255,)


def noise_fill(base, amount, seed, size=S):
    rng = random.Random(seed)
    img = Image.new("RGBA", (size, size))
    px = img.load()
    for y in range(size):
        for x in range(size):
            d = rng.randint(-amount, amount)
            px[x, y] = tuple(clamp(v + d) for v in base) + (255,)
    return img


def blotch(img, center, radius, color, strength, seed):
    """Tints a soft irregular blob, e.g. a water stain."""
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    cx, cy = center
    for y in range(h):
        for x in range(w):
            # Wrap so stains stay seamless across tiles
            dx = min(abs(x - cx), w - abs(x - cx))
            dy = min(abs(y - cy), h - abs(y - cy))
            d = (dx * dx + dy * dy) ** 0.5 / radius + rng.uniform(-0.2, 0.2)
            if d < 1:
                t = strength * (1 - d)
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r + (color[0] - r) * t), clamp(g + (color[1] - g) * t), clamp(b + (color[2] - b) * t), a)


# ---------------- Wallpaper ----------------
#
# Level 0's papers (graphics pass B3). Each is printed paper built with matlib: a fibre ground with a butt seam every
# 16 px (two strips to a block, each from a slightly different roll), the motif dyed into it so it keeps the fibre and
# the seam's shading, and the ink a little uneven. The trims (baseboard, chair rail, outlet) are drawn as relief, lit
# from above. Every part comes in three versions the blocktype mixes at random: two plain ones (`-2` is a second seed)
# and `-damp`, an older stretch with a contained water stain, so the stain lands on about one block in three.

GROUND = hexrgb(0xD7D48A)
CHEVRON = hexrgb(0xB3AE7A)
BEAD = hexrgb(0xE8E4BE)
# The chevron as printed (B3): the same hue as CHEVRON, about 48 levels below the ground rather than 34, so the motif
# still reads from a few blocks away once the paper's fibre and seams are under it (the lore paper's chevron is plain
# to see). The beads print at about half strength, so the chevrons lead.
CHEVRON_PRINT = (165, 160, 108)
BEAD_ALPHA = 0.5


def _ink(rng, wear, k=1.0):
    """The alpha of one printed pixel: mostly full, a little uneven, now and then nearly missed by the roller."""
    return int(255 * k * (rng.uniform(0.4, 0.65) if rng.random() < wear else rng.uniform(0.9, 1.0)))


def motif_chevron(seed, chevron=CHEVRON_PRINT, bead=BEAD, wear=0.03, bead_alpha=BEAD_ALPHA):
    """The 2002 photo's print: columns of beaded lines alternating with columns of stacked upward chevrons, offset by
    half a step, on an 8 px column. Transparent where there is no ink."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    for col in range(S // 8):
        x0 = col * 8
        offset = (col % 2) * 4
        for y in range(S):
            if (y // 2) % 2 == 0:
                px[x0, y] = bead + (_ink(rng, wear, bead_alpha),)  # beaded / dashed line
            row = (y + offset) % 8
            # "^" three rows tall, five pixels wide, centred in the column
            for dx, r in ((4, 0), (3, 1), (5, 1), (2, 2), (6, 2)):
                if row == r:
                    px[x0 + dx, y] = chevron + (_ink(rng, wear),)
    return img


def motif_dots(seed, colour, pitch, stagger, wear=0.08):
    """A dot grid every `pitch` px, alternate rows shifted by `stagger` (pitch divides 32, so it tiles)."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed)
    for y in range(0, S, pitch):
        for x in range(0, S, pitch):
            px[(x + (stagger if (y // pitch) % 2 else 0) + pitch // 2 - 1) % S, (y + pitch // 2 - 1) % S] = colour + (_ink(rng, wear),)
    return img


def paper_wall(seed, ground, motif=None, strip=1.0, mottle=3, fibre=0.6, grain=3, seam=0.3):
    """A printed paper wall: matlib.paper (fibre, strips with butt seams every 16 px, kept faint: on a whole wall a
    stronger seam reads as a stripe) with the motif dyed in."""
    img = M.paper(seed, base=ground, grain=grain, mottle=mottle, fibre=fibre, seams=16, strip=strip, seam=seam)
    if motif is not None:
        M.dye(img, motif, ground)
    M.hue_jitter(img, 1.0, seed + 5, cell=16)
    return img


def pattern_chevron(seed, alt=0, ground=GROUND, chevron=CHEVRON_PRINT, bead=BEAD, grain=3):
    return paper_wall(seed, ground, motif_chevron(seed + 1, chevron, bead), grain=grain)


# (D1) The yellow wall's paper. The user preferred the old paper's seamless look but liked the new one's mustier tone.
# B3's paper gave every block (each part, each version) its own mottle, strip shades and a hue drift, and a butt seam
# every 16 px: on a long wall those repeated block by block, so the wall read as panels. Now every block of the yellow
# wall shares one paper ground (the same soft mottle and hue, CHEVRON_PAPER), so blocks meet without a step; what
# differs block to block is fine (the fibres, the ink). The butt seam is gone from the plain versions; the second
# version (`-2`, one block in three) has one, faint, on its edge, so a strip join turns up now and then rather than
# twice in every block. The chevron rows are on the 8 px grid and line up across every edge, as the old paper's did,
# and the bead lines are printed nearer the old paper's strength. The damp version is listed less often for this paper
# (blocktypes/wallpaper.json), since its stain is the one mark that sits in the same place each time.
CHEVRON_PAPER = 100
CHEVRON_BEADS = 0.8  # the bead lines nearer the old paper's (B3 printed them at half strength)


def chevron_wall(seed, alt=0):
    img = M.noise_hv(GROUND, 3, CHEVRON_PAPER, (S, S), mottle=2.5, cells=(8, 4), hue=1.5)
    rng = random.Random(M.sub(seed, "fibre"))
    for _ in range(int(0.6 * S * S / 6)):  # matlib.paper's fibre: short pale and dark strokes in all directions
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, math.pi)
        L = rng.uniform(1.5, 4)
        f = rng.choice((0.035, -0.04))
        for (px_, py_) in M._line(x, y, x + math.cos(a) * L, y + math.sin(a) * L):
            M.touch(img, px_, py_, f)
    if alt:  # a butt seam on the block's edge, faint
        for y in range(S):
            M.touch(img, 0, y, -0.035)
            M.touch(img, 1, y, 0.018 if rng.random() < 0.85 else 0.03)
    M.dye(img, motif_chevron(seed + 1, bead_alpha=CHEVRON_BEADS), GROUND)
    return img


def pattern_dotted(seed, alt=0):
    return paper_wall(seed, hexrgb(0xDCD89C), motif_dots(seed + 1, hexrgb(0xB5AE78), 4, 2))


def pattern_cream(seed, alt=0):
    """The pale walls of the arched areas: the same paper, bleached until the pattern is only just there."""
    return paper_wall(seed, hexrgb(0xE9E1BA), motif_chevron(seed + 1, hexrgb(0xCFC497), hexrgb(0xF1EBCF), wear=0.12),
                      strip=1.2, mottle=6)


def pattern_manila(seed, alt=0):
    """The Manila Room: plain manila paper with a fine staggered dot (every 4 px, so it tiles); the seams kept fainter
    than on the printed papers, since with no motif over them they read as panel joints."""
    return paper_wall(seed, hexrgb(0xD5BE8A), motif_dots(seed + 1, hexrgb(0xB49A64), 4, 2, wear=0.1), strip=0.8,
                      mottle=5, fibre=0.8, seam=0.15)


def pattern_stripped(seed, alt=0):
    """Bare drywall where the paper was cut away: the drywall's own paper face and the dried paste in bands along the
    old strip seams; the second version (alt) also has a few small scraps of the yellow paper that would not come
    away, each with a torn pale edge and its own thickness (lit on top, a shadow under it). Scraps in every block
    would repeat as a grid, so they are in one version of three."""
    rng = random.Random(seed + 7)
    img = M.plaster(seed, base=hexrgb(0xC9C3B2), grain=3, mottle=4, roller=0.3, bumps=0.004)
    px = img.load()
    paste = (186, 172, 132)
    for s0 in (0, 16):  # paste left along the old seams: a soft yellowish band with streaks of the brush in it
        w = rng.uniform(3.0, 5.0)
        for y in range(S):
            for dx in range(-6, 7):
                t = max(0.0, 1 - abs(dx + rng.uniform(-0.6, 0.6)) / w) * 0.22
                if t > 0:
                    x = (s0 + dx) % S
                    px[x, y] = M.rgba(M.mix(px[x, y], paste, t))
        for _ in range(3):
            x = (s0 + rng.randint(-3, 3)) % S
            y0 = rng.randrange(S)
            for y in range(y0, y0 + rng.randint(6, 16)):
                M.touch(img, x, y, -0.05)
    scrap = pattern_chevron(seed + 20)
    sp = scrap.load()
    for _ in range(rng.randint(2, 3) if alt else 0):  # scraps, irregular, 2-5 px
        cx, cy = rng.randrange(S), rng.randrange(S)
        cells = {(cx, cy)}
        for _ in range(rng.randint(3, 9)):
            ax, ay = rng.choice(sorted(cells))
            cells.add((ax + rng.choice((-1, 0, 1)), ay + rng.choice((-1, 0, 0, 1))))
        cells = {(x % S, y % S) for x, y in cells}
        for (x, y) in cells:
            px[x, y] = M.rgba(M.lift(sp[x, y], -6))
        for (x, y) in cells:
            if ((x, (y - 1) % S)) not in cells:
                M.touch(img, x, y, 0.08)  # the scrap's top edge catches the light
            if ((x, (y + 1) % S)) not in cells:
                M.touch(img, x, y + 1, -0.14)  # and throws a hairline shadow under it
            for nx, ny in ((x + 1, y), (x - 1, y)):
                if ((nx % S, ny % S)) not in cells and rng.random() < 0.4:
                    M.touch(img, nx, ny, 0.06)  # torn white fibre at the edge
    return img


def pattern_red(seed, alt=0):
    """The Red Rooms: the same beaded lines and chevrons as the yellow paper, in dried-blood red, with darker runs
    down it (faint and frequent, so they read as the paper's state rather than one mark per block)."""
    ground = hexrgb(0x8A2A22)
    img = paper_wall(seed, ground, motif_chevron(seed + 1, hexrgb(0x5A1412), hexrgb(0xB45C4A), wear=0.12),
                     strip=2.0, mottle=8, grain=4)
    M.drips(img, n=4, seed=seed + 3, color=(70, 14, 12), length=(10, 30), strength=0.22)
    M.grime(img, 0.12, seed + 4, color=(60, 12, 10), cells=(8, 4, 2), cover=0.45)
    return img


PATTERNS = {"stripped": pattern_stripped, "chevron": chevron_wall, "dotted": pattern_dotted, "cream": pattern_cream, "manila": pattern_manila,
            "red": pattern_red}

VINYL = (80, 68, 52)     # the baseboard: dark brown vinyl cove base
RAIL_WOOD = (126, 92, 56)


def scuff_band(img, seed, top, bottom, n=3, dirt=(118, 104, 70)):
    """The foot of a wall: a little dirt gathering toward the floor, and a few short shoe and mop scuffs above the
    trim (small and several, so they read as wear, not as a mark)."""
    rng = random.Random(seed)
    px = img.load()
    for y in range(top, bottom):
        t = ((y - top) / max(1, bottom - top)) ** 1.6 * 0.12
        for x in range(S):
            px[x, y] = M.rgba(M.mix(px[x, y], dirt, t * rng.uniform(0.6, 1.2)))
    for _ in range(n):
        x, y = rng.randrange(S), rng.randint(bottom - 5, bottom - 1)
        for k in range(rng.randint(2, 5)):
            M.touch(img, x + k, y + (1 if k > 2 and rng.random() < 0.3 else 0), -rng.uniform(0.05, 0.1))
    return img


def add_baseboard(img, seed=0):
    """A 4 px vinyl cove base: the rounded cap lit from above, the face, and the toe darkest where it meets the carpet,
    with a hairline of shade on the wall where the cap meets it."""
    rng = random.Random(seed + 77)
    scuff_band(img, seed + 78, 18, 27)
    px = img.load()
    for x in range(S):
        px[x, 27] = M.rgba(M.lift(px[x, 27], -7))
        px[x, 28] = M.rgba(M.lift(VINYL, 26 + rng.uniform(-2, 2)))
        px[x, 29] = M.rgba(M.lift(VINYL, 9 + rng.uniform(-2, 2)))
        px[x, 30] = M.rgba(M.lift(VINYL, rng.uniform(-2, 2)))
        px[x, 31] = M.rgba(M.lift(VINYL, -16 + rng.uniform(-2, 2)))
    for _ in range(2):  # pale scuffs on the vinyl, where a shoe caught it
        x, y = rng.randrange(S), rng.choice((29, 30))
        for k in range(rng.randint(2, 4)):
            M.touch(img, x + k, y, 0.18)
    return img


def add_rail(img, seed=0):
    """A wooden chair rail about 0.4 m up the wall: a lit rounded top, the moulding face with a little grain, a darker
    bead below, and its shadow on the paper under it."""
    rng = random.Random(seed + 91)
    px = img.load()
    streak = [rng.uniform(-5, 5) for _ in range(S)]
    for x in range(S):
        g = streak[x] * 0.5 + streak[(x + 1) % S] * 0.5
        px[x, 17] = M.rgba(M.lift(px[x, 17], -6))
        px[x, 18] = M.rgba(M.lift(RAIL_WOOD, 26 + g * 0.4))
        px[x, 19] = M.rgba(M.lift(RAIL_WOOD, 6 + g))
        px[x, 20] = M.rgba(M.lift(RAIL_WOOD, -4 + g))
        px[x, 21] = M.rgba(M.lift(RAIL_WOOD, -22 + g * 0.5))
        px[x, 22] = M.rgba(M.shade_px(px[x, 22], -0.16))
        px[x, 23] = M.rgba(M.shade_px(px[x, 23], -0.06))
    scuff_band(img, seed + 92, 24, 32, n=2)
    return img


def add_outlet(img, name, seed=0):
    """A duplex outlet: an ivory plate standing proud of the wall, its top and left edges lit and its bottom and right
    in shade, a soft shadow on the paper to its lower right, two receptacles (slots dark, each with a lit lip under it)
    and the screw between them. Same trim as the wall it sits on: under the rail on dotted paper, above the baseboard
    elsewhere."""
    if name == "dotted":
        add_rail(img, seed)
        top = 24
    else:
        add_baseboard(img, seed)
        top = 19
    x0, x1, y0, y1 = 14, 19, top, top + 7  # 5 x 7 px (about 15 x 21 cm), end exclusive
    plate = (232, 228, 212)
    rng = random.Random(seed + 5)
    px = img.load()
    for y in range(y0 + 1, y1 + 1):  # the shadow first, offset by one to the lower right
        for x in range(x0 + 1, x1 + 1):
            px[x, y] = M.rgba(M.shade_px(px[x, y], -0.2 if (x == x1 or y == y1) else 0))
    for y in range(y0, y1):
        for x in range(x0, x1):
            px[x, y] = M.rgba(M.lift(plate, rng.uniform(-1.5, 1.5)))
    M.bevel(img, (x0, y0, x1, y1), 1, 0.07)
    for ry in (y0 + 1, y0 + 4):  # the two receptacles: two dark slots each, a lit lip under them
        for sx in (x0 + 1, x1 - 2):
            for sy in (ry, ry + 1):
                px[sx, sy] = M.rgba((86, 82, 74))
            M.touch(img, sx, ry + 2, 0.03)
    px[(x0 + x1) // 2, y0 + 3] = M.rgba((200, 196, 184))  # the screw between them
    return img


def _window(x, edge=6):
    """0 at the texture's left and right edges, rising to 1 by `edge` px in: keeps a feature inside its own block, so
    a damp block beside a plain one shows no cut-off mark."""
    d = min(x + 0.5, S - x - 0.5)
    return max(0.0, min(1.0, (d - 1) / edge)) ** 1.5


def damp(img, seed, part="upper", stain_c=(176, 150, 86), seam_x=16):
    """The same wall, older: a water run down from above and a soft tide-ringed stain (upper blocks), or a rising-damp
    tide mark from the floor (bottom blocks), with one seam lifting. Kept inside the block (they fade before its edges)
    so a damp block beside a plain one reads as the same paper aged, not as a patch; more yellowing than darkening."""
    img = img.copy()
    rng = random.Random(seed)
    px = img.load()
    if part == "upper":
        xc, w, L = rng.uniform(10, 22), rng.uniform(2.5, 3.5), rng.uniform(20, 28)
        wob = [rng.uniform(-0.6, 0.6) for _ in range(S)]
        for y in range(S):
            for x in range(S):
                u = (x + 0.5 - xc - wob[y]) / (w * (1 + 0.5 * y / S))
                t = 0.13 * math.exp(-u * u) * min(1.0, (y + 1) / 6) * max(0.0, 1 - y / L) * _window(x, 4)
                if t > 0.005:
                    px[x, y] = M.rgba(M.mix(px[x, y], stain_c, t))
        st = img.copy()
        M.stain(st, seed + 1, radius=rng.uniform(6.5, 8.5), color=stain_c, strength=0.2, ring=0.9,
                at=(rng.uniform(13, 19), rng.uniform(12, 19)))
        img = st
        px = img.load()
    else:
        tide = img.copy()
        M.tideline(tide, rng.uniform(19, 22), seed + 2, color=stain_c, amount=0.24, wave=1.6, below=0.45)
        tp = tide.load()
        for y in range(27 if part in ("baseboard", "outlet") else S):
            for x in range(S):
                t = _window(x, 7)
                if t:
                    px[x, y] = M.rgba(M.mix(px[x, y], tp[x, y], t))
    # one seam lifting: a dark gap opening from the top of a run, the lifted edge catching the light
    y0, L = rng.randint(3, 10), rng.randint(6, 12)
    for k in range(L):
        y = y0 + k
        if part != "upper" and y > 24:
            break
        M.touch(img, seam_x, y, -0.16 * (1 - k / L))
        M.touch(img, seam_x + 1, y, 0.08 * (1 - k / L))
    return img


def wallpapers(only=None):
    """Every paper in every part, each in its three versions (see the section comment)."""
    for i, (name, fn) in enumerate(PATTERNS.items()):
        if only and name not in only:
            continue
        for v, seed0 in (("", 100), ("-2", 500)):
            s = seed0 + i
            a = 1 if v else 0
            parts = {"upper": fn(s, a), "plain": scuff_band(fn(s + 10, a), s + 11, 22, 32),
                     "baseboard": add_baseboard(fn(s + 20, a), s + 21), "rail": add_rail(fn(s + 30, a), s + 31),
                     "outlet": add_outlet(fn(s + 40, a), name, s + 41)}
            for part, img in parts.items():
                save(img, f"block/wallpaper/{name}-{part}{v}.png")
                if not v:
                    stain_c = {"red": (66, 18, 14), "stripped": (170, 154, 116), "cream": (204, 186, 126),
                               "manila": (166, 136, 84)}.get(name, (176, 150, 86))
                    save(damp(img, 300 + i * 10 + len(part), part, stain_c, 0 if name == "chevron" else 16),
                         f"block/wallpaper/{name}-{part}-damp.png")
    # The arch soffits and risers: painted plaster in the pale paper's colour, without the print
    save(M.plaster(61, base=(232, 224, 190), grain=3, mottle=6, roller=0.35), "block/wallpaper/cream-soffit.png")


# ---------------- Floor, ceiling, lights ----------------

CARPET = hexrgb(0xA8956A)  # the beige of Level 0's carpet (lore: keep)


def dingy(img, seed, dull=0.1, dim=3.0, grime=0.07, flecks=9):
    """(D1) A carpet nobody has vacuumed in a while: the colour a little duller (`dull` of the way to its own grey) and
    `dim` levels darker, a faint tracked-in grime at the scale of a few tufts (fine, so turned blocks still meet), and
    a few flecks: grit and crumbs (dark) and lint (pale). Subtle by design: it should read as unloved, not stained."""
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            g = M.lum(c)
            px[x, y] = M.rgba(M.lift(M.mix(c, (g, g, g), dull), -dim, 0), c[3])
    M.grime(img, grime, M.sub(seed, "tracked"), color=(84, 72, 54), cells=(4, 2), cover=0.45)
    rng = random.Random(M.sub(seed, "flecks"))
    for _ in range(flecks):
        x, y = rng.randrange(w), rng.randrange(h)
        if rng.random() < 0.7:
            M.touch(img, x, y, -rng.uniform(0.12, 0.2))  # grit, a crumb
        else:
            M.touch(img, x, y, rng.uniform(0.1, 0.16))  # a bit of lint
    return img


def carpet(variant, alt=0):
    img = _carpet(variant, alt)
    if alt:  # the two seeds at the same mean brightness, or blocks of one read lighter than the other at a distance
        ref = _carpet(variant, 0)
        d = _mean_lum(ref) - _mean_lum(img)
        px = img.load()
        for y in range(S):
            for x in range(S):
                px[x, y] = M.rgba(M.lift(px[x, y], d, 0))
    return img


def _mean_lum(img):
    px = img.load()
    return sum(M.lum(px[x, y]) for y in range(img.height) for x in range(img.width)) / (img.width * img.height)


def _carpet(variant, alt=0):
    """Level 0's carpet (graphics pass B3), from matlib.carpet: a beige Berber (loop pile, so its structure is at the
    texel, as vanilla's cloth is), two yarn tones, trodden patches. The blocktype turns each block at random and
    mixes the two seeds (`alt`), so neither the pile's mottle nor a stain lines up into a grid.
    - normal: the beige pile.
    - stained: the same carpet with the original soft brown blotches (wrapping across the block's edges) and small
      dark spots; the second seed places them elsewhere.
    - soaked: dark, wet and flattened, a few wet highlights."""
    seed = (1, 2, 3)[("normal", "stained", "soaked").index(variant)] * 10 + alt
    if variant in ("normal", "stained"):
        img = M.carpet(10 + alt, base=CARPET, tone2=M.hue_shift(M.lift(CARPET, -13), 3), mix2=0.35, loop=True,
                       pile=6, grain=4, mottle=5)
        dingy(img, 10 + alt)  # (D1) the user found it a little too pristine
        if variant == "normal":
            return img
        rng = random.Random(seed + 1)
        # The original soft blotches, wrapping across the edges, placed differently in the second seed (B3 round 2:
        # a tint showed hard squares round each patch, and stains faded at the block edges a grid of spots)
        for (cx, cy, r, c, k, sd) in (((12, 18, 12, (96, 80, 50), 0.6, 3), (27, 5, 6, (110, 92, 58), 0.4, 4)) if not alt
                                       else ((20, 9, 11, (96, 80, 50), 0.55, 5), (4, 25, 7, (110, 92, 58), 0.4, 6))):
            blotch(img, (cx, cy), r, c, k, sd)
        for _ in range(14):  # small dark spots of old spills
            x, y = rng.randrange(S), rng.randrange(S)
            M.touch(img, x, y, -rng.uniform(0.06, 0.12))
        return img
    base = hexrgb(0x857356)
    img = M.carpet(seed, base=base, tone2=M.hue_shift(M.lift(base, -12), 3), mix2=0.45, loop=True, pile=4, grain=3,
                   mottle=5)
    rng = random.Random(seed + 4)
    M.grime(img, 0.16, seed + 5, color=(70, 62, 48), cells=(4, 2), cover=0.5)
    for _ in range(14):  # a wet fibre catching the light here and there
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, 0.16)
        M.touch(img, x, y + 1, -0.08)
    return dingy(img, seed, dull=0.06, dim=1.5, grime=0.04, flecks=6)


def carpet_threadbare(alt=0):
    """The pile cut away for its fibres: the woven jute backing (a 2 px plain weave), rows of cut tuft stubs where the
    yarn went through it (on a 4 px gauge), the odd tuft left standing, and dark patches of latex glue."""
    seed = 40 + alt
    img = M.fabric(seed, base=hexrgb(0x7C6F58), weave="plain", tone2=hexrgb(0x6E624C), contrast=3, grain=3, mottle=6)
    rng = random.Random(seed + 1)
    px = img.load()
    stub = M.lift(CARPET, -18)
    for y in range(1, S, 4):  # the tufting rows: short cut stubs, some missing
        for x in range(0, S):
            if rng.random() < 0.6:
                px[x, y] = M.rgba(M.lift(stub, rng.uniform(-10, 8)))
                M.touch(img, x, y + 1, -0.07)
    for _ in range(rng.randint(3, 5)):  # tufts the blade missed: a small clump of pile, lit on top, a shadow under
        x, y = rng.randrange(S), rng.randrange(S)
        cells = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (-1, 1)][:rng.randint(2, 6)]
        for dx, dy in cells:
            px[(x + dx) % S, (y + dy) % S] = M.rgba(M.lift(CARPET, (8 if dy == 0 else -4) + rng.uniform(-4, 4)))
        for dx, dy in cells:
            if (dx, dy + 1) not in cells:
                M.touch(img, x + dx, y + dy + 1, -0.12)
    M.grime(img, 0.25, seed + 2, color=(62, 54, 40), cells=(8, 4, 2), cover=0.35)
    return dingy(img, seed, dull=0.06, dim=1.5, grime=0.04, flecks=6)


def sprite():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def salvage_items():
    """Flat item sprites; the game extrudes them into 3D."""
    glass, glass_hi, glass_lo = (196, 226, 232, 235), (240, 250, 252, 255), (120, 160, 170, 255)
    wrap, steel, steel_lo = (200, 190, 110, 255), (150, 156, 162, 255), (96, 102, 108, 255)

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(6, 27), (12, 6), (20, 3), (25, 14), (16, 28)], fill=glass, outline=glass_lo)
    d.line([(13, 8), (10, 24)], fill=glass_hi)
    save(img, "item/salvage/glassshard.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(14, 16), (22, 3), (27, 6), (19, 20)], fill=glass, outline=glass_lo)  # blade
    d.line([(21, 6), (16, 16)], fill=glass_hi)
    d.polygon([(5, 27), (13, 16), (18, 20), (9, 30)], fill=wrap, outline=(140, 130, 70, 255))  # bound handle
    for k in range(3):
        d.line([(8 + k * 3, 24 - k * 3), (11 + k * 3, 27 - k * 3)], fill=(140, 124, 84, 255))
    save(img, "item/salvage/glassshiv.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(12, 18), (22, 4), (28, 4), (28, 9), (18, 22)], fill=steel, outline=steel_lo)  # ground edge
    d.line([(23, 5), (14, 18)], fill=(214, 220, 224, 255))
    d.polygon([(4, 27), (12, 17), (18, 22), (9, 31)], fill=wrap, outline=(140, 130, 70, 255))
    for k in range(3):
        d.line([(7 + k * 3, 25 - k * 3), (10 + k * 3, 28 - k * 3)], fill=(140, 124, 84, 255))
    save(img, "item/salvage/scraper.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    rng = random.Random(50)
    for _ in range(26):  # a tangle of beige threads
        x, y = rng.randint(6, 24), rng.randint(8, 24)
        d.line([(x, y), (x + rng.randint(-6, 6), y + rng.randint(-5, 5))], fill=rng.choice([(168, 149, 106, 255), (142, 124, 84, 255), (190, 172, 128, 255)]))
    save(img, "item/salvage/carpetfibre.png")

    img = sprite()
    strip = pattern_chevron(51).crop((0, 0, 9, 26))
    img.paste(strip, (9, 3))
    d = ImageDraw.Draw(img)
    d.polygon([(9, 26), (18, 26), (22, 30), (13, 30)], fill=(190, 186, 120, 255))  # curled end
    d.rectangle([9, 3, 17, 28], outline=(150, 146, 92, 255))
    save(img, "item/salvage/wallpaperstrip.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(6, 5), (11, 5), (11, 21), (26, 21), (26, 26), (6, 26)], fill=steel, outline=steel_lo)  # L bracket
    for hole in ((8, 9), (8, 16), (16, 23), (22, 23)):
        d.point(hole, fill=(40, 42, 46, 255))
    save(img, "item/salvage/metalbracket.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    for k in range(4):  # coils of copper wire
        d.ellipse([7 + k, 8 + k * 2, 24 - k, 22 - k], outline=(184, 115, 51, 255))
    d.line([(22, 20), (28, 27)], fill=(184, 115, 51, 255), width=1)
    d.line([(9, 12), (4, 5)], fill=(150, 90, 40, 255), width=1)
    save(img, "item/salvage/scrapwire.png")

    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(4, 20), (25, 8), (28, 13), (27, 15), (7, 26)], fill=(84, 60, 40, 255), outline=(52, 36, 24, 255))
    d.line([(8, 21), (24, 12)], fill=(110, 82, 56, 255))
    for x, y in ((12, 21), (18, 17), (22, 14)):  # rot
        d.point((x, y), fill=(40, 52, 30, 255))
    save(img, "item/salvage/rottenwood.png")


def pottery_items():
    """The broken pot of a dead office plant, and the grit it pounds down to. Run on its own:
    python -c "import gen_textures; gen_textures.pottery_items()" (from tools/), so the other sprites are left alone."""
    terra, terra_hi, terra_lo = (176, 96, 60, 255), (206, 128, 86, 255), (118, 60, 36, 255)

    # A curved piece of the pot's wall: the rolled rim along the top, the break jagged below, soil stuck inside
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(4, 10), (14, 6), (27, 8), (28, 13), (24, 18), (26, 23), (19, 27), (14, 24), (9, 27), (6, 21)], fill=terra, outline=terra_lo)
    d.line([(5, 10), (14, 7), (26, 9)], fill=terra_hi, width=2)  # the rim
    d.line([(6, 13), (14, 10), (26, 12)], fill=terra_lo)
    for x, y in ((10, 18), (16, 20), (20, 15), (12, 23)):  # dried soil in the curve
        d.point((x, y), fill=(74, 56, 40, 255))
        d.point((x + 1, y), fill=(92, 70, 48, 255))
    d.line([(17, 14), (21, 22)], fill=terra_lo)  # a crack
    save(img, "item/salvage/potshard.png")

    # A heap of pounded grit, coarse grains and dust
    img = sprite()
    d = ImageDraw.Draw(img)
    d.ellipse([5, 15, 27, 28], fill=(160, 92, 62, 255))
    d.ellipse([9, 11, 23, 24], fill=(170, 100, 68, 255))
    rng = random.Random(52)
    for _ in range(70):
        x, y = rng.randint(6, 26), rng.randint(12, 27)
        if ((x - 16) / 11) ** 2 + ((y - 21) / 7) ** 2 <= 1 or ((x - 16) / 7) ** 2 + ((y - 17) / 6.5) ** 2 <= 1:
            d.point((x, y), fill=rng.choice([terra_hi, terra_lo, (190, 150, 120, 255), (140, 78, 50, 255)]))
    save(img, "item/salvage/ceramicgrit.png")


def portrait(seed):
    """A dark, unsettling oil portrait: a figure in black against murky brown, the face lit from one side, the eyes
    lost in shadow, the varnish gone yellow."""
    img = texlib.vertical_gradient((52, 40, 28), (28, 22, 16))
    px = img.load()
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-6, 6)
            # shoulders and a dark coat
            if y > 20 and abs(x - 16) < 6 + (y - 20) * 0.9:
                r, g, b = 22, 18, 20
                if abs(x - 16) < 2 and y < 26:
                    r, g, b = 150, 140, 120  # a white collar
            # the face: an oval, lit from the left, shadowed on the right
            dx, dy = (x - 16) / 5.0, (y - 13) / 6.5
            if dx * dx + dy * dy < 1:
                light = 0.55 + 0.45 * max(0.0, -dx)
                r, g, b = int(176 * light), int(142 * light), int(110 * light)
                if 10 <= y <= 12 and (13 <= x <= 14 or 18 <= x <= 19):
                    r, g, b = 40, 30, 24  # eyes in shadow
            # hair, dark and close
            if 0.75 < dx * dx + dy * dy < 1.25 and y < 12:
                r, g, b = 34, 26, 20
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), 255)
    # the varnish, yellowed toward the middle
    blotch(img, (16, 14), 14, (120, 96, 40), 0.18, seed + 1)
    return img


# ---------------- The ceiling module (graphics pass B3) ----------------
#
# Level 0's drop ceiling sets the convention the other painted T-bar ceilings (Levels 4, 6.1, !, Fun, The End, 3999)
# reuse: the T-bar is painted, not modelled (the ceiling is a plain cube everywhere, and a shape on every ceiling
# block would cost far more than it shows): a 2 px rail split across neighbouring blocks (matlib.tbar: the lit half on
# a block's left and top edges, the other half on its right and bottom, so tiled blocks meet in one rail), the tile
# stepping up into the grid with a soft tegular recess, and the troffer as a bevelled housing frame round a prismatic
# lens, all painted; the troffer stays a cube (a recessed-lens shape lost the cube's glow, see gen_l0_walls.troffer).

CEILING = hexrgb(0xD6CFA6)  # the cream mineral-fibre tile (keep)
TBAR_RAIL = (176, 170, 146)  # darker than the tile, so the grid reads at a distance as the old one did


def ceiling_tile(seed=6, stain=False):
    return M.ceiling_tile(seed, base=CEILING, rail=TBAR_RAIL, fissures=0.65, recess=2,
                          stain_color=(192, 168, 116) if stain else None)


def ceiling_side(seed=21):
    """The cut edge of the ceiling where the drop ceiling's layer ends (seen at level edges and gates): the board's
    material without the grid (the `all` texture's rail and recess on a vertical face read as tiles stood on end),
    and the T-bar's flange along its foot."""
    img = M.noise_hv(CEILING, 3, seed, mottle=4)
    rng = random.Random(seed)
    for _ in range(40):
        M.touch(img, rng.randrange(S), rng.randrange(S - 3), -0.08)
    px = img.load()
    for x in range(S):
        px[x, S - 4] = M.rgba(M.lift(px[x, S - 4], -8))
        px[x, S - 3] = M.rgba(M.lift(TBAR_RAIL, 14))
        px[x, S - 2] = M.rgba(TBAR_RAIL)
        px[x, S - 1] = M.rgba(M.lift(TBAR_RAIL, -12))
    return img


TROFFER = {  # lens colour, glow colour, how lit
    "on": ((252, 252, 244), (255, 254, 246), 1.0),
    "off": ((214, 214, 204), (214, 214, 204), 0.0),
    "dim": ((236, 196, 140), (250, 210, 150), 0.85),  # the Manila Room's old orange-tinted lamp
    "red": ((240, 72, 52), (255, 112, 86), 1.0),
}


def troffer(state, rail=TBAR_RAIL, frame=(214, 210, 198), table=None, tubes=2):
    """matlib.troffer_lens, then (B3) the lens of a lit panel pulled 35% toward its glow colour so it reads as emissive,
    and the step down from the housing frame to the lens (the troffer stays a cube: see gen_l0_walls.troffer for the
    shape that was tried). (D1) B3 painted that step as a near-black 1 px gap all round, which the user read as a black
    ring; it is now the frame's inner edge in soft shade, deeper on the top and left (in the frame's shadow) than on
    the bottom and right. (B7) `rail`, `frame`, `table` (TROFFER's form) and `tubes` let Level 4 draw its own."""
    lens, glow, lit = (table or TROFFER)[state]
    img = M.troffer_lens(seed={"on": 1, "off": 2, "dim": 3, "red": 4}[state], lit=lit, lens=lens, glow=glow,
                         frame=frame, frame_px=2, rail=rail, tubes=tubes)
    px = img.load()
    if lit:
        for y in range(3, S - 3):
            for x in range(3, S - 3):
                px[x, y] = M.rgba(M.mix(px[x, y], glow, 0.35))
    for i in range(2, S - 2):
        for (x, y, f) in ((i, 2, -0.16), (2, i, -0.16), (i, S - 3, -0.06), (S - 3, i, -0.06)):
            M.touch(img, x, y, f)
    return img


def troffer_side(seed=23, base=(190, 186, 174), rail=TBAR_RAIL):
    """(D4) The side of a troffer, where it shows (a gate, a level's edge, a step in the ceiling): B3 drew every face with
    the framed lens, so a light's side read as a window. Now the sides are the housing's edge: plain off-white painted
    steel (a little darker than the lens frame, since the whole block glows), a faint seam under its top where the
    housing's flange folds, and along its foot the T-bar flange as `ceiling_side` has it, so the rail runs on from the
    ceiling's cut edge beside it. Only the down face (fluorescentlight-<state>) shows the lens. Lights stay cubes."""
    img = M.painted_metal(seed, base=base, grain=2, mottle=3, panel=False, chips=0)
    M.emboss_lines(img, ys=(5,), strength=0.12)
    px = img.load()
    for x in range(S):
        px[x, S - 4] = M.rgba(M.lift(px[x, S - 4], -8))
        px[x, S - 3] = M.rgba(M.lift(rail, 14))
        px[x, S - 2] = M.rgba(rail)
        px[x, S - 1] = M.rgba(M.lift(rail, -12))
    return img


def concrete(alt=0):
    """Plain cast concrete (the Level 0 gate's surround, Level !'s void): matlib.concrete, with a broad pour mottle
    and some hue in it; the third version carries a hairline crack (one block in three)."""
    return M.concrete(70 + alt, base=(128, 127, 121), grain=4, mottle=9, aggregate=0.07, pores=0.012,
                      cracks=1 if alt == 2 else 0)


# ---------------- Supply boxes (graphics pass B3) ----------------
#
# Kraft cardboard: a fibre ground, faint vertical pressure lines from the flutes inside, and the tape with a sheen.
# supplybox-side and supplybox-top are also the mod's shared cardboard (detail_kit "cardboard", the shelves, the
# End's stock, 3999), so their tape stays where it always was (top centre, 6 px) and their wear is scattered rather
# than along the edges; the supply box's own crushed edges are geometry (gen_loop.supply_box_shape).

KRAFT = hexrgb(0xAA8052)
TAPE = (214, 188, 136)


def cardboard(seed, base=KRAFT, flutes=True):
    img = M.paper(seed, base=base, grain=3, mottle=6, fibre=0.9, seams=None)
    if flutes:
        px = img.load()
        for x in range(0, S, 4):  # the flutes press through as faint vertical lines
            for y in range(S):
                px[x, y] = M.rgba(M.lift(px[x, y], -2.5))
                px[(x + 1) % S, y] = M.rgba(M.lift(px[(x + 1) % S, y], 1.5))
    M.grime(img, 0.08, seed + 1, color=(110, 80, 50), cells=(8, 4), cover=0.4)
    return img


def tape(img, x0, x1, y0, y1, seed):
    """Brown packing tape over the board: semi-opaque (the fibre shows through), a sheen streak along it, its edges
    a hair lighter where they lift, a wrinkle or two."""
    rng = random.Random(seed)
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = M.mix(px[x, y], TAPE, 0.72)
            if x == x0 + 1:
                c = M.lift(c, 10)  # the sheen
            px[x, y] = M.rgba(c)
        M.touch(img, x0 - 1, y, -0.05)
        M.touch(img, x1, y, -0.07)
    for x in range(x0, x1):
        M.touch(img, x, y0, 0.05)
    for _ in range(2):
        y = rng.randint(y0 + 1, max(y0 + 1, y1 - 2))
        for x in range(x0, x1):
            M.touch(img, x, y, 0.07)
            M.touch(img, x, y + 1, -0.06)
    return img


def box(top, seed=None):
    """The shared cardboard: top (two flaps meeting under a strip of tape) or side (the tape coming down over the top
    edge, a printed pair of this-way-up arrows)."""
    img = cardboard(12 if top else 13)
    px = img.load()
    if top:
        tape(img, 13, 19, 0, S, 14)
        for y in range(S):  # the flaps' seam under the tape
            M.touch(img, 16, y, -0.1)
            M.touch(img, 17, y, 0.04)
    else:
        tape(img, 13, 19, 0, 8, 15)
        ink = (74, 56, 40)
        for ax in (21, 27):  # two this-way-up arrows over a bar, faded (y 9-15: what the supply box's sides show)
            for dx, dy in ((0, 0), (-1, 1), (1, 1), (-2, 2), (2, 2), (0, 1), (0, 2), (0, 3), (0, 4)):
                x, y = ax + dx, 9 + dy
                px[x, y] = M.rgba(M.mix(px[x, y], ink, 0.5))
        for x in range(18, 31):
            px[x, 15] = M.rgba(M.mix(px[x, 15], ink, 0.42))
    return img


def supply_box_faces():
    """The sealed supply box's own faces (B3), cut for its UVs (sides show x 4-28, y 0-20 of the texture; the top
    x 4-28, y 4-28): the shared cardboard with the carton's edges worn: a lit rim along the top edge, the corners and
    the foot scuffed darker where it has been dragged and stacked."""
    def edges(img, box, seed, top_lit=True):
        x0, y0, x1, y1 = box
        M.ao_border(img, 2, 0.14, box, "lrb")
        if top_lit:
            for x in range(x0, x1):
                M.touch(img, x, y0, 0.07)
        rng = random.Random(seed)
        for _ in range(7):  # scuffs and crushed spots along the edges
            side = rng.choice("lrb")
            if side == "b":
                x, y = rng.randrange(x0, x1), y1 - 1 - rng.randrange(2)
            else:
                x, y = (x0 + rng.randrange(2)) if side == "l" else (x1 - 1 - rng.randrange(2)), rng.randrange(y0, y1)
            M.touch(img, x, y, -rng.uniform(0.06, 0.12))
        return img
    side = edges(box(False), (4, 0, 28, 20), 31)
    end = edges(cardboard(17), (4, 0, 28, 20), 32)
    top = box(True)
    M.ao_border(top, 2, 0.12, (4, 4, 28, 28))
    return side, end, top


# ---------------- Level 1: concrete car park ----------------

# 5x7 bitmap glyphs for painted bay letters and signs
GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
}


def draw_glyph(img, ch, x0, y0, scale, color):
    px = img.load()
    for gy, row in enumerate(GLYPHS[ch]):
        for gx, bit in enumerate(row):
            if bit == "1":
                for sy in range(scale):
                    for sx in range(scale):
                        px[x0 + gx * scale + sx, y0 + gy * scale + sy] = color


# ---- Level 1's concrete (graphics pass B4) ----
#
# Everything is matlib.concrete with broad pour patches and some hue (warm buff and blue-grey batches), a low grain
# and fine aggregate, so at playing distance it reads as poured concrete rather than as static. Features a player
# would spot twice (a crack, a tyre scuff, a rust run, a stain) are in one version of three; the floor and ceiling
# versions are also turned at random, so each feature lands in about one block in three, at a different place. Every
# version of a surface is brought to the same mean brightness as the old texture (match_mean), so blocks of
# different versions do not show as a checker and the level is no lighter or darker than it was.

L1_FLOOR = {"plain": (92, 93, 89), "wet": (69, 70, 66), "dark": (67, 72, 76)}
L1_FLOOR_MEAN = {"plain": 90, "wet": 70, "dark": 71}
L1_WALL = (142, 145, 145)
L1_PILLAR = (154, 157, 157)
L1_CEILING = (120, 122, 119)


def match_mean(img, target):
    """img shifted (with the warm/cool drift) so its mean luminance is `target`."""
    px = img.load()
    w, h = img.size
    m = sum(M.lum(px[x, y]) for y in range(h) for x in range(w)) / (w * h)
    d = target - m
    for y in range(h):
        for x in range(w):
            px[x, y] = M.rgba(M.lift(px[x, y], d), px[x, y][3])
    return img


def l1_concrete(seed, base, pores=0.012, swirl=0.0, patches=4.5, patch_hue=1.5, aggregate=0.03):
    return M.concrete(seed, base=base, grain=3, mottle=5, aggregate=aggregate, pores=pores, swirl=swirl,
                      patches=patches, patch_hue=patch_hue, hue=1.5)


def pour_line(img, y, seed):
    """The line where one lift of the pour met the next: a faint dark seam with a little cement bleed under it."""
    rng = random.Random(seed)
    for x in range(S):
        M.touch(img, x, y, -0.07)
        M.touch(img, x, y + 1, 0.035 if rng.random() < 0.7 else 0.06)


def tyre_scuff(img, seed, strength=0.06):
    """A faint rubber mark: a soft band 3 px wide on a wide arc, darkest in the middle, wrapping."""
    rng = random.Random(seed)
    w, h = img.size
    r = rng.uniform(40, 70)
    cx, cy = rng.uniform(0, w), rng.uniform(0, h) + r
    a0 = rng.uniform(-2.2, -0.9)
    for i in range(int(r * 0.55)):
        a = a0 + i / r
        t = math.sin(math.pi * (i + 0.5) / (r * 0.55)) ** 0.6
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        for k, f in ((-1, 0.5), (0, 1.0), (1, 0.5)):
            M.touch(img, round(x), round(y) + k, -strength * f * t)


def inside_block(plain, featured, band=5):
    """`featured` where it differs from `plain`, faded out over the last `band` px toward each edge: a feature (a crack,
    a scuff, a stain) on a surface whose versions are turned and mixed at random must not run into the edge, where the
    neighbour would cut it off. Returns `plain`, changed."""
    p, f = plain.load(), featured.load()
    w, h = plain.size

    def ramp(d):
        t = max(0.0, min(1.0, (d - 0.5) / band))
        return t * t * (3 - 2 * t)
    for y in range(h):
        for x in range(w):
            k = ramp(min(x + 0.5, w - x - 0.5)) * ramp(min(y + 0.5, h - y - 0.5))
            p[x, y] = M.rgba(M.mix(p[x, y], f[x, y], k), p[x, y][3])
    return plain


def concrete_floor(kind, alt=0):
    """Level 1's car park floor: power-trowelled concrete (faint swirl arcs) with broad pour patches. Version 2 of 3
    carries a hairline crack and a faint tyre scuff; the dark floor's mould and the wet floor's film change place.
    (D1) Every version is turned and mixed at random, and the user saw the block edges: a turned block's pour patches
    did not continue into its neighbour's. Each version keeps its own patches inside the block, but toward the edges
    they blend into one shared field that is the same at every turn (`matlib.turn_safe`), and the features fade out
    before the edge, so no version at any turn shows a step against any other."""
    seed = {"plain": 3000, "wet": 3010, "dark": 3020}[kind] + alt
    img = l1_concrete(seed, L1_FLOOR[kind], pores=0.008, swirl=0.7, aggregate=0.03 if kind == "plain" else 0.05)
    ground = l1_concrete(seed - alt, L1_FLOOR[kind], pores=0.0, swirl=0.0, aggregate=0.0)
    M.turn_safe(img, ground, band=8)
    plain = img.copy()
    if kind == "plain" and alt == 2:
        M.crack(img, M.sub(seed, "crack"), at=(15, 12), length=(14, 20), strength=0.2)
        tyre_scuff(img, M.sub(seed, "scuff"))
    if kind == "dark" and alt:
        M.stain(img, M.sub(seed, "mould"), radius=8, color=(70, 84, 72), strength=0.32, at=(13 + 6 * alt, 19 - 5 * alt), ring=0.3)
    img = inside_block(plain, img)
    if kind == "wet":
        # standing water: glints of the lights on it, as the old wet floor had, each a lit pixel with a softer one
        # beside it, scattered all over so the patch has no edge of its own inside the block
        rng = random.Random(M.sub(seed, "glint"))
        for _ in range(30):
            x, y = rng.randrange(S), rng.randrange(S)
            M.touch(img, x, y, 0.42)
            M.touch(img, x + 1, y, 0.16)
    return match_mean(img, L1_FLOOR_MEAN[kind])


def tie_hole(img, x, y):
    """A form-tie hole: a 2 px recess, dark at its top left (it is in shadow), its lower lip lit."""
    for (dx, dy, f) in ((0, 0, -0.34), (1, 0, -0.26), (0, 1, -0.22), (1, 1, -0.12), (-1, 0, -0.06), (0, -1, -0.06),
                        (0, 2, 0.06), (1, 2, 0.05), (2, 1, 0.04)):
        M.touch(img, x + dx, y + dy, f)


# Where concretewall-damaged's three rebar ends come out of the wall (gen_shapes.level1, as the north face shows them,
# u = 16 - x): the broken-out patch is round them
REBAR_PX = ((23, 19, 4.6), (11, 13, 4.2), (7, 25, 3.6))


def spall(img, seed):
    """Concrete broken out round the rebar: a recess with coarse exposed aggregate, its upper rim in shadow and its
    lower rim lit, and a rust run below each bar."""
    rng = random.Random(seed)
    w, h = img.size
    rough = M.value_noise((w, h), 4, M.sub(seed, "rough"))
    inside = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            for (cx, cy, r) in REBAR_PX:
                if math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 1.15) < r + rough[y][x] * 1.4:
                    inside[y][x] = True
    px = img.load()
    for y in range(h):
        for x in range(w):
            if inside[y][x]:
                c = M.lift(px[x, y], -22 + rough[y][x] * 6)
                px[x, y] = M.rgba(M.hue_shift(c, 3))
    for _ in range(110):  # exposed stones, lit on top
        x, y = rng.randrange(w), rng.randrange(h)
        if inside[y][x] and inside[min(h - 1, y + 1)][x]:
            c = M.hue_shift(M.lift(L1_WALL, rng.uniform(-18, 6)), rng.uniform(-8, 8))
            px[x, y] = M.rgba(M.lift(c, 6))
            px[x, (y + 1) % h] = M.rgba(c)
            M.touch(img, x, y + 2, -0.1)
    for y in range(h):
        for x in range(w):
            if not inside[y][x]:
                continue
            if y == 0 or not inside[y - 1][x]:
                M.touch(img, x, y, -0.22)
                M.touch(img, x, y + 1, -0.1)
            if y == h - 1 or not inside[y + 1][x]:
                M.touch(img, x, y, 0.16)
            if x == 0 or not inside[y][x - 1]:
                M.touch(img, x, y, -0.12)
    for k, (cx, cy, r) in enumerate(REBAR_PX):
        M.drips(img, 1, M.sub(seed, f"rust{k}"), color=(128, 74, 44), length=(5, 10), strength=0.4, start=int(cy) + 1)
    return img


def concrete_wall(damaged, alt=0):
    """Level 1's cast walls: plywood-formed concrete with bug holes, a pour line along the top of each block, and a
    row of two form-tie holes. Version 3 has a hairline crack and a rust run from a tie (one block in eight). The damaged wall is
    broken out round its (modelled) rebar; the old painted rebar is gone."""
    seed = 3100 + alt + (50 if damaged else 0)
    img = l1_concrete(seed, L1_WALL, pores=0.022, patches=3.0, patch_hue=2.0)
    pour_line(img, 0, M.sub(seed, "lift"))
    for x in (8, 24):
        tie_hole(img, x, 8)
    if alt == 2 and not damaged:
        # (D1) the user saw this crack over and over: it is now a shorter, fainter hairline, and the blocktype lists
        # this version once in eight (blocktypes/level1/concretewall.json)
        M.crack(img, M.sub(seed, "crack"), at=(rng_at(seed)), length=(9, 14), strength=0.14)
        M.drips(img, 1, M.sub(seed, "tie"), color=(124, 86, 58), length=(8, 14), strength=0.3, start=10)
    if damaged:
        spall(img, M.sub(seed, "spall"))
        M.crack(img, M.sub(seed, "crack1"), at=(16, 4), length=(10, 16), strength=0.24)
        M.crack(img, M.sub(seed, "crack2"), at=(28, 14), length=(8, 14), strength=0.22)
    return match_mean(img, 138 if damaged else 142)


def rng_at(seed):
    r = random.Random(seed)
    return (r.uniform(4, 28), r.uniform(14, 28))


def pillar_concrete(seed=3200):
    """The columns' concrete: lighter, smoother (steel-formed), with fewer bug holes; a lit arris at the left edge of
    each face and a shaded one at the right."""
    img = M.concrete(seed, base=L1_PILLAR, grain=3, mottle=5, aggregate=0.045, pores=0.01, patches=5, patch_hue=3, hue=2.5)
    for y in range(S):
        M.touch(img, 0, y, 0.07)
        M.touch(img, S - 1, y, -0.06)
    return img


def pillar(letter):
    img = match_mean(pillar_concrete(), 154)
    if letter:
        # The bay letter: a painted panel over the concrete (the paint thin where the form's pores show through)
        # and the letter stencilled on it; a little paint lost at the panel's edges
        paint = M.noise_hv((226, 224, 214), 2, 3210, (S, S), 3)
        px, pp = img.load(), paint.load()
        rng = random.Random(3211)
        for y in range(5, 28):
            for x in range(7, 25):
                px[x, y] = pp[x, y]
        draw_glyph(img, letter.upper(), 9, 6, 3, (40, 58, 96, 255))
    return img


def pillar_light():
    img = pillar(None)
    d = ImageDraw.Draw(img)
    d.rectangle([12, 0, 19, S - 1], fill=(70, 72, 72, 255))  # housing
    d.rectangle([14, 0, 17, S - 1], fill=(240, 248, 252, 255))  # tube
    return img


def concrete_ceiling(alt=0):
    """The car park's slab soffit: formed concrete with the two white conduits that run along every bay, as before
    (graphics pass B4: now shaded as round runs, a lit line along each and a shadow on the slab beside it, clipped
    every 16 px). Version 3 of 3 has a faint water stain with a tide ring. Not turned: the conduits keep their run."""
    seed = 3300 + alt
    img = l1_concrete(seed, (116, 118, 115), pores=0.016)
    if alt == 2:
        M.stain(img, M.sub(seed, "stain"), radius=8, color=(150, 140, 112), strength=0.22, at=(6, 24), ring=0.6)
    px = img.load()
    for y0 in (8, 12):
        for x in range(S):
            px[x, y0] = M.rgba(M.lift((214, 216, 214), 8))
            px[x, y0 + 1] = M.rgba((190, 192, 190))
            px[x, y0 + 2] = M.rgba((160, 162, 160))
            M.touch(img, x, y0 + 3, -0.16)
        for x in (3, 19):  # clips
            for y in range(y0, y0 + 3):
                px[x, y] = M.rgba((128, 130, 132))
    return match_mean(img, 126)


def concrete_base(base, seed, holes=True):
    """The old Level 1 concrete (noise with pores and tie holes). Level 2's cage lights still use it."""
    img = noise_fill(hexrgb(base), 10, seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(40):  # pores and aggregate
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = shade(px[x, y], 0.82)
    if holes:  # form-tie holes from the casting
        for (x, y) in ((6, 8), (25, 8), (6, 24), (25, 24)):
            px[x, y] = shade(px[x, y], 0.55)
            px[x + 1, y] = shade(px[x + 1, y], 0.7)
    return img


def painted_line(img, box, colour, seed, wear=0.0):
    """Road paint over the concrete: the paint takes the concrete's light and dark (the texture shows through), its
    edges a little soft, worn through here and there."""
    x0, y0, x1, y1 = box
    px = img.load()
    rng = random.Random(seed)
    worn = M.fbm((S, S), M.sub(seed, "wear"), (8, 4, 2), 0.6)  # wear in patches (tyres, feet), not pepper
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if wear and worn[y % S][x % S] > 1 - wear * 4:
                continue
            under = px[x, y]
            d = (M.lum(under) - 90) * 0.3
            px[x, y] = M.rgba(M.lift(colour, d + rng.uniform(-3, 3)))
    return img


def strip_light(state):
    img = concrete_base(0x747673, 331, holes=False)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 10, S - 1, 21], fill=(150, 152, 150, 255))  # housing
    tube = {"on": (240, 248, 252), "off": (150, 154, 156)}[state]
    d.rectangle([0, 13, S - 1, 18], fill=tube + (255,))
    return img


def exit_sign():
    img = Image.new("RGBA", (S, S), (24, 60, 32, 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(14, 30, 18, 255), width=2)
    x = 3
    for ch in "EXIT":
        draw_glyph(img, ch, x, 12, 1, (120, 255, 140, 255))
        x += 7
    return img


CRATE_WOOD = (156, 116, 68)


def crate(top):
    """Level 1's supply crate (a cube, as vanilla's crate is): three boards in a raised frame, the frame's members lit
    on top and casting a shadow onto the boards under them, the sides braced corner to corner, a nail at each joint."""
    boards = M.wood_planks(3400 + top, base=CRATE_WOOD, planks=3, grain=3, contrast=0.8, per_plank=9, flecks=0.8)
    rails = M.wood_planks(3410 + top, base=M.lift(CRATE_WOOD, -10), planks=[4, 4, 4, 4, 4, 4, 4, 4], grain=3,
                          contrast=0.7, per_plank=6)
    stiles = M.wood_planks(3420 + top, base=M.lift(CRATE_WOOD, -10), planks=[4, 4, 4, 4, 4, 4, 4, 4], grain=3,
                           contrast=0.7, per_plank=6, direction="v")
    brace = M.wood_planks(3430 + top, base=M.lift(CRATE_WOOD, -4), planks=[10, 6, 16], grain=3, contrast=0.7, per_plank=4)
    img = boards.copy()
    px, rp, sp, bp = img.load(), rails.load(), stiles.load(), brace.load()
    F = 3  # frame width
    # the boards: shadowed under the top rail and beside the left stile, lit along the foot rail
    for x in range(S):
        for k, f in ((F, -0.16), (F + 1, -0.08), (F + 2, -0.03)):
            M.touch(img, x, k, f)
        M.touch(img, x, S - F - 1, 0.05)
    for y in range(S):
        for k, f in ((F, -0.1), (F + 1, -0.04)):
            M.touch(img, k, y, f)
    if not top:  # the brace, bottom left to top right, raised like the frame
        for y in range(F, S - F):
            for x in range(F, S - F):
                d = (x + y - (S - 1))  # 0 on the diagonal
                if -2 <= d <= 2:
                    c = bp[x % S, 12 + d]
                    if d == -2:
                        c = M.lift(c, 12)
                    elif d == 2:
                        c = M.lift(c, -14)
                    px[x, y] = M.rgba(c)
                elif d == 3:
                    M.touch(img, x, y, -0.14)
                elif d == 4:
                    M.touch(img, x, y, -0.05)
    for y in range(S):
        for x in range(S):
            if y < F or y >= S - F:
                px[x, y] = rp[x, y % 4 + (4 if y < F else 12)]
            elif x < F or x >= S - F:
                px[x, y] = sp[x % 4 + (4 if x < F else 12), y]
    for x in range(S):  # rails: lit top edge, dark lower edge
        for y0 in (0, S - F):
            M.touch(img, x, y0, 0.12)
            M.touch(img, x, y0 + F - 1, -0.14)
    for y in range(F, S - F):  # stiles: lit left edge, dark right
        for x0 in (0, S - F):
            M.touch(img, x0, y, 0.08)
            M.touch(img, x0 + F - 1, y, -0.12)
    for (nx, ny) in ((1, 1), (S - 2, 1), (1, S - 2), (S - 2, S - 2), (1, 15), (S - 2, 15), (15, 1), (15, S - 2)):
        px[nx, ny] = M.rgba((58, 54, 50))
        M.touch(img, nx, ny + 1, 0.1)
    return match_mean(img, 101 if top else 99)


# ---------------- Level 2: utility tunnels ----------------

def tunnel_concrete(seed):
    """Level 2's dark grey cast concrete: a quiet grain with a few broad stains and water streaks run down from the
    ceiling, so it does not read as static up close. Streaks fade in and out along y but wrap, so walls stack.
    (D1) The user kept this original wall over B5's `matlib.concrete` version (`tunnel_cast`, removed with its two
    alternates); B5's brick panels stay."""
    img = noise_fill(hexrgb(0x43484D), 4, seed)
    rng = random.Random(seed + 1)
    px = img.load()
    for _ in range(18):  # pores and aggregate
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = shade(px[x, y], 0.86)
    for (x, y) in ((6, 8), (25, 8), (6, 24), (25, 24)):  # form-tie holes from the casting
        px[x, y] = shade(px[x, y], 0.6)
        px[x + 1, y] = shade(px[x + 1, y], 0.75)
    blotch(img, (24, 26), 11, (78, 86, 74), 0.4, seed + 2)  # grime
    blotch(img, (rng.randrange(S), rng.randrange(S)), 9, (34, 32, 28), 0.5, seed + 3)  # damp stain
    blotch(img, (rng.randrange(S), rng.randrange(S)), 6, (96, 98, 92), 0.3, seed + 4)  # efflorescence
    for sx in (rng.randrange(2, 12), rng.randrange(18, 29)):  # water streaks, each showing over half the tile
        phase = rng.random() * 6.283
        for y in range(S):
            k = max(0.0, math.sin(y * 6.283 / S + phase)) ** 2 * 0.2
            for x, w in ((sx, 1.0), (sx + 1, 0.5)):
                px[x, y] = shade(px[x, y], 1 - k * w)
    return img


def tunnel_plain(alt=0):
    """(Graphics pass, Level 2) The tunnel wall's plain concrete: the original's tone and quiet grain, without the
    shaded circle that sat in every block (and the tie holes and streaks that repeated with it). Three versions share
    one faint low-frequency ground and are turned and mixed at random by the blocktype (`matlib.turn_safe`), so no
    block edge shows; only version 3 (one block in eight) has a mark, a faint damp run, kept inside the block."""
    base = hexrgb(0x43484D)
    ground = M.noise_hv(base, 0, 3500, S, 5, (16, 8), hue=0)
    img = noise_fill(base, 4, 3510 + alt)
    px, gp = img.load(), ground.load()
    for y in range(S):  # the original's grain over the shared ground
        for x in range(S):
            px[x, y] = M.rgba(tuple(px[x, y][i] + gp[x, y][i] - base[i] for i in range(3)))
    M.turn_safe(img, ground, band=8, keep=0.6)
    rng = random.Random(3520 + alt)
    for _ in range(18):  # pores and aggregate, as before
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = shade(px[x, y], 0.86)
    plain = img.copy()
    if alt == 2:
        sx, phase = rng.randrange(11, 19), rng.random() * 6.283
        for y in range(S):
            k = 0.07 + 0.05 * math.sin(y * 6.283 / S + phase)
            dx = round(1.5 * math.sin(y * 0.35 + phase))
            for x, w in ((sx + dx, 1.0), (sx + dx + 1, 0.6), (sx + dx - 1, 0.3)):
                px[x, y] = shade(px[x, y], 1 - k * w)
    img = inside_block(plain, img)
    return match_rgb(img, (66, 70, 74), "tunnelwall")


def tunnel_brick(seed=360):
    """(B5) The brick panels in Level 2's walls: dark, sooty engineering brick in running bond (`matlib.brick`), each
    brick its own shade and a little hue, lit on top, the 2 px joints recessed and darker than the brick, as the old
    one's were. Mean kept (50)."""
    img = M.brick(seed, base=(66, 52, 44), mortar=(40, 36, 34), course=8, length=16, offset=0.5, mortar_w=2,
                  jitter=9, hue=4, recess=1.0, pits=0.03, grain=4, mottle=6)
    M.grime(img, 0.12, M.sub(seed, "soot"), color=(30, 28, 28), cover=0.45)
    return match_mean(img, 50)


def tunnel_wall(variant):
    img = tunnel_concrete(350 + len(variant))
    d = ImageDraw.Draw(img)
    if variant == "pipes":
        for y, h, col in ((3, 5, (107, 62, 42)), (11, 7, (226, 225, 215)), (22, 4, (90, 70, 56))):
            d.rectangle([0, y, S - 1, y + h], fill=col + (255,))
            d.line([0, y, S - 1, y], fill=shade(col, 1.15))
            d.line([0, y + h, S - 1, y + h], fill=shade(col, 0.6))
        for x in (8, 24):  # brackets
            d.rectangle([x, 2, x + 1, 27], fill=(60, 62, 64, 255))
    elif variant == "machinery":
        d.rectangle([2, 3, 29, 28], fill=(84, 92, 86, 255), outline=(40, 44, 42, 255))
        for cx in (9, 21):  # gauges
            d.ellipse([cx - 4, 7, cx + 4, 15], fill=(220, 214, 196, 255), outline=(30, 30, 30, 255))
            d.line([cx, 11, cx + 2, 8], fill=(160, 30, 20, 255))
        d.rectangle([6, 19, 25, 24], fill=(52, 56, 54, 255))  # vent slots
        for x in range(8, 25, 3):
            d.line([x, 20, x, 23], fill=(28, 30, 30, 255))
    elif variant == "brick":
        img = Image.new("RGBA", (S, S), (42, 36, 34, 255))
        d = ImageDraw.Draw(img)
        rng = random.Random(360)
        for row in range(4):
            off = 4 if row % 2 else 0
            for col in range(-1, 3):
                x0 = col * 16 + off
                c = rng.choice([(74, 58, 46), (62, 48, 40), (52, 44, 40)])
                d.rectangle([x0 + 1, row * 8 + 1, x0 + 14, row * 8 + 6], fill=c + (255,))
    return img


def tunnel_ceiling(alt=0):
    """(B5) The tunnel soffit: the same cast concrete, darker (it is seldom lit from below), soot-stained, two tie
    holes. The old painted rust pipe band is gone: the real pipe runs hang beside it, and the blind review read the
    painted one (shaded, in round 1) as a ladder of painted pipes across every corridor. Three versions
    (alternates in blocktypes/level2/tunnelceiling.json); the third has a water stain."""
    seed = 370 + alt
    img = M.concrete(370, base=(62, 67, 72), grain=2, mottle=6, aggregate=0.012, pores=0.005, patches=4.0,
                     patch_hue=1.2, hue=1.2)  # one ground for all three versions, so they meet without a seam
    M.grime(img, 0.2, M.sub(370, "soot"), color=(36, 36, 34), cells=(16, 8), cover=0.6)
    for x in (8, 24):
        tie_hole(img, x, 6)
    if alt == 1:
        M.crack(img, M.sub(seed, "crack"), at=(12, 20), length=(10, 16), strength=0.2)
    if alt == 2:
        M.stain(img, M.sub(seed, "leak"), radius=8, color=(44, 42, 36), strength=0.3)
    return match_mean(img, 67)


# ---------------- Level 2: the machine cabinets (B5) ----------------
# The cabinets' gauges, lamps, vents, handles and labels are geometry (gen_shapes.level2, tools/modelkit.py); these are
# their materials, one texture key each. The old painted front (props/cabinet-front) is still written for anything
# else that uses it.

CAB_PAINT = (70, 79, 74)


def dial_face(size=16):
    """A printed gauge dial: a cream face with a dark rim, ticks round the scale and the last two in red. Outside the
    disc it is the bezel's dark, so the square face reads round behind the octagonal bezel."""
    paper = (222, 216, 196)
    img = M.noise_hv(paper, 2, 5110, size, 2)
    p = img.load()
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c)
            if d > c + 0.3:
                p[x, y] = M.rgba((48, 50, 50))
            elif d > c - 0.9:
                p[x, y] = M.rgba(M.lift(paper, -60))
            elif y < c and d > c * 0.5:
                p[x, y] = M.rgba(M.lift(p[x, y][:3], 4))  # the old glass's sheen on the upper half
    for k in range(9):
        a = math.radians(-120 + 30 * k)
        for r in (c * 0.6, c * 0.76):
            x, y = round(c + r * math.sin(a)), round(c - r * math.cos(a))
            p[x, y] = M.rgba((176, 40, 30) if k >= 7 else (48, 44, 40))
    return img


def lamp_lens(colour, seed, size=16):
    """An indicator lamp's domed lens: lighter in the middle, a hot spot up and to the left, darker at the rim."""
    img = M.noise_hv(colour, 3, seed, size, 2)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c) / c
            hot = math.hypot(x - c + 3, y - c + 3)
            M.touch(img, x, y, 0.18 - 0.42 * d * d + (0.3 if hot < 2 else 0))
    return img


def cabinet_label(seed=5120):
    """A riveted equipment plate, 16x8: cream enamel, a dark border, two lines of dark print and a red rule."""
    img = M.noise_hv((206, 198, 172), 2, seed, (16, 8), 3)
    p = img.load()
    rng = random.Random(seed)
    for x in range(16):
        for y in (0, 7):
            p[x, y] = M.rgba((70, 66, 58))
    for y in range(8):
        for x in (0, 15):
            p[x, y] = M.rgba((70, 66, 58))
    for y, x0, x1 in ((2, 3, 13), (4, 3, 10)):
        x = x0
        while x < x1:
            n = rng.randint(1, 3)
            for k in range(n):
                if x + k < x1:
                    p[x + k, y] = M.rgba((52, 48, 44))
            x += n + 1
    for x in range(3, 13):
        p[x, 6] = M.rgba((150, 52, 40))
    for (x, y) in ((1, 1), (14, 1), (1, 6), (14, 6)):
        p[x, y] = M.rgba((150, 146, 132))
    return img


def cabinet_warning(seed=5121):
    """A small warning decal, 8x8: yellow with a black border and an exclamation mark."""
    img = M.noise_hv((210, 176, 52), 2, seed, (8, 8), 2)
    p = img.load()
    for i in range(8):
        for (x, y) in ((i, 0), (i, 7), (0, i), (7, i)):
            p[x, y] = M.rgba((34, 32, 30))
    for y in (2, 3, 5):
        for x in (3, 4):
            p[x, y] = M.rgba((34, 32, 30))
    return img


def cabinet_textures():
    paint = M.painted_metal(5101, base=CAB_PAINT, grain=4, mottle=7, panel=False, chips=6, under=(96, 92, 84))
    M.grime(paint, 0.22, 5102, cover=0.55)
    M.rust(paint, 0.06, 5109, color=(112, 66, 40), dark=(70, 46, 32))
    M.scratches(paint, 3, 5113)
    save(paint, "block/level2/cabinet-paint.png")
    panel = M.painted_metal(5103, base=M.lift(CAB_PAINT, -10), grain=4, mottle=7, panel=False, chips=4, under=(96, 92, 84))
    M.grime(panel, 0.24, 5104, cover=0.55)
    M.drips(panel, 3, 5114, color=(44, 42, 36), length=(8, 18), strength=0.3)
    save(panel, "block/level2/cabinet-panel.png")
    top = M.painted_metal(5115, base=M.lift(CAB_PAINT, -6), grain=4, mottle=7, panel=False, chips=4, under=(96, 92, 84))
    M.grime(top, 0.4, 5116, color=(58, 54, 46), cover=0.75)  # dust settled on the lid
    save(top, "block/level2/cabinet-top.png")
    save(M.painted_metal(5105, base=(48, 52, 52), panel=False, chips=0), "block/level2/cabinet-dark.png")
    save(M.noise_hv((24, 26, 26), 3, 5106, mottle=4), "block/level2/cabinet-vent.png")
    bezel = M.brushed_metal(5107, base=(112, 112, 108), direction="h", streak=8, sheen=10)
    M.grime(bezel, 0.15, 5117, cover=0.5)
    save(bezel, "block/level2/cabinet-bezel.png")
    save(M.noise_hv((176, 44, 34), 3, 5108, mottle=2), "block/level2/cabinet-needle.png")
    save(dial_face(), "block/level2/cabinet-dial.png")
    save(lamp_lens((190, 48, 34), 5111), "block/level2/cabinet-lampred.png")
    save(lamp_lens((206, 146, 44), 5112), "block/level2/cabinet-lampamber.png")
    save(cabinet_label(), "block/level2/cabinet-label.png")
    save(cabinet_warning(), "block/level2/cabinet-warning.png")


def cage_light(state):
    img = concrete_base(0x3E4348, 371, holes=False)
    d = ImageDraw.Draw(img)
    bulb = {"white": (255, 248, 230), "warm": (255, 176, 96), "off": (90, 86, 78)}[state]
    d.ellipse([9, 9, 22, 22], fill=bulb + (255,))
    for i in range(8, 25, 4):  # wire cage
        d.line([i, 7, i, 24], fill=(30, 30, 30, 255))
        d.line([7, i, 24, i], fill=(30, 30, 30, 255))
    return img


def pipe_tex(kind):
    """A pipe's skin, shaded like a cylinder lit from above in two 16-pixel bands: a highlight a third of the way
    down each band, falling to shadow at its bottom. Pipe models stretch one band over the pipe's height, so a
    square pipe reads as round."""
    import math
    base = {"rust": 0xA5582E, "red": 0xA8302A, "lagging": 0xE2E1D7, "tar": 0x2A2622}[kind]
    noise = {"lagging": 5, "tar": 4}.get(kind, 10)
    img = noise_fill(hexrgb(base), noise, {"rust": 380, "red": 382, "lagging": 381, "tar": 383}[kind])
    px = img.load()
    rng = random.Random({"rust": 21, "red": 22, "lagging": 23, "tar": 24}[kind])
    for y in range(S):
        p = (y % 16 + 0.5) / 16
        light = 0.66 + 0.52 * math.exp(-((p - 0.3) / 0.2) ** 2) - 0.22 * max(0.0, (p - 0.6) / 0.4) ** 1.5
        for x in range(S):
            px[x, y] = shade(px[x, y], light)
    d = ImageDraw.Draw(img)
    if kind == "lagging":
        # Insulation wrapped in cloth: a strap every quarter, a seam along the top, a brown water stain
        for x in range(3, S, 8):
            for y in range(S):
                px[x, y] = shade(px[x, y], 0.72)
                px[x + 1, y] = shade(px[x + 1, y], 1.06)
        blotch(img, (22, 13), 5, (150, 120, 70), 0.35, 24)
        blotch(img, (9, 29), 4, (150, 120, 70), 0.3, 25)
    else:
        # A flanged joint with its bolts, and for the bare pipe, pits and streaks of rust
        for x in (14, 17):
            for y in range(S):
                px[x, y] = shade(px[x, y], 0.6)
        for x in (15, 16):
            for y in range(S):
                px[x, y] = shade(px[x, y], 1.15)
        for y in (2, 7, 12, 18, 23, 28):
            d.point((15, y), fill=(40, 34, 30, 255))
        if kind == "rust":
            for _ in range(26):
                x, y = rng.randrange(S), rng.randrange(S)
                px[x, y] = shade(px[x, y], rng.choice((0.55, 0.65, 1.3)))
            for _ in range(5):
                x, y = rng.randrange(S), rng.randrange(0, S, 16) + rng.randint(4, 9)
                for k in range(rng.randint(3, 6)):
                    if y + k < S:
                        px[x, y + k] = shade(px[x, y + k], 0.72)
        if kind == "tar":
            # Level 3's pipes of black sludge: a wet sheen along the highlight, and the joint weeping tar
            for y in range(S):
                if y % 16 in (4, 5):
                    for x in range(S):
                        if rng.random() < 0.55:
                            px[x, y] = (96, 92, 86, 255) if y % 16 == 4 else (70, 66, 62, 255)
            for band in (0, 16):
                for x in (12, 13, 18, 19, 20):
                    for y in range(band + 6, band + 6 + rng.randint(3, 9)):
                        px[x, y] = (14, 12, 10, 255) if y < band + 15 else px[x, y]
    return img


def smooth_noise(w, h, cell, seed):
    """Value noise in 0..1, bilinear between random values on a grid of `cell` pixels, wrapping on both axes."""
    rng = random.Random(seed)
    gw, gh = max(1, w // cell), max(1, h // cell)
    grid = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        fy = y / cell
        y0, ty = int(fy) % gh, fy - int(fy)
        y1 = (y0 + 1) % gh
        ty = ty * ty * (3 - 2 * ty)
        for x in range(w):
            fx = x / cell
            x0, tx = int(fx) % gw, fx - int(fx)
            x1 = (x0 + 1) % gw
            tx = tx * tx * (3 - 2 * tx)
            a = grid[y0][x0] + (grid[y0][x1] - grid[y0][x0]) * tx
            b = grid[y1][x0] + (grid[y1][x1] - grid[y1][x0]) * tx
            out[y][x] = a + (b - a) * ty
    return out


def pipe_light(v):
    """How bright a round pipe on a wall is at `v` (0 its top, 1 its underside, round its front), lit from above and
    in front: a soft diffuse falloff, a narrow specular highlight a little above the middle, deep shadow underneath."""
    theta = math.pi / 2 - v * math.pi  # +90 degrees at the top, -90 at the bottom
    nx, ny = math.cos(theta), math.sin(theta)  # facing out of the wall, and up
    lx, ly = 0.55, 0.83
    diffuse = max(0.0, nx * lx + ny * ly)
    hx, hy = 0.92, 0.39  # half way between the light and the eye
    spec = max(0.0, nx * hx + ny * hy) ** 24
    return 0.42 + 0.62 * diffuse, spec


def wall_pipe_tex(kind):
    """The skin of the round pipes bolted along Level 2's and Level 3's walls, 64 pixels square: along U the length of
    the pipe (a block), down V once round it from its top to its underside, so the stepped boxes of the model each
    take their own part of the shading and the pipe reads as round. Smooth mottling rather than per-pixel noise, so
    it holds up at arm's length."""
    W = 64
    if kind == "rust":
        paint, rust, dark = (150, 74, 38), (176, 96, 44), (86, 44, 26)
    else:  # lagging: canvas-wrapped insulation, cream gone grubby
        paint, rust, dark = (214, 208, 190), (196, 186, 160), (160, 138, 100)
    mott = smooth_noise(W, W, 16, {"rust": 711, "lagging": 712}[kind])
    fine = smooth_noise(W, W, 4, {"rust": 713, "lagging": 714}[kind])
    blooms = smooth_noise(W, W, 8, {"rust": 715, "lagging": 716}[kind])
    rng = random.Random({"rust": 717, "lagging": 718}[kind])
    img = Image.new("RGBA", (W, W))
    px = img.load()
    for y in range(W):
        light, spec = pipe_light((y + 0.5) / W)
        for x in range(W):
            m = mott[y][x] * 0.7 + fine[y][x] * 0.3
            c = [paint[i] + (rust[i] - paint[i]) * max(0.0, min(1.0, (m - 0.45) * 2.2)) for i in range(3)]
            if blooms[y][x] > 0.7:  # a darker crust of rust, or a grimy patch on the canvas
                t = min(1.0, (blooms[y][x] - 0.7) * 4) * (0.45 + 0.55 * fine[y][x])
                c = [c[i] + (dark[i] - c[i]) * t * 0.7 for i in range(3)]
            gloss = 0.22 if kind == "rust" else 0.1
            c = [clamp(c[i] * light + 255 * spec * gloss) for i in range(3)]
            px[x, y] = tuple(c) + (255,)
    if kind == "rust":
        # Streaks of rust running down the underside from the seam, and a few pits
        for _ in range(9):
            x, y = rng.randrange(W), rng.randrange(W // 2, W - 6)
            for k in range(rng.randint(4, 10)):
                if y + k < W:
                    px[x, y + k] = shade(px[x, y + k], 0.8)
        for _ in range(14):
            x, y = rng.randrange(W), rng.randrange(W)
            px[x, y] = shade(px[x, y], 0.62)
    else:
        # The canvas is strapped every half block, and seamed along the top
        for x0 in (12, 44):
            for y in range(W):
                for dx, f in ((0, 0.74), (1, 0.8), (2, 1.08)):
                    px[x0 + dx, y] = shade(px[x0 + dx, y], f)
        for x in range(W):
            px[x, 9] = shade(px[x, 9], 0.86)
    return img


def wall_pipe_flange():
    """A flanged joint and the clamps of the wall pipes: dark, rust-bloomed steel. (B5) Painted steel gone to rust in
    scattered patches with pits, a lit top edge and a dark foot on every 8 px band (the flange rings and straps take
    their own slice of it, so each reads as a shaded ring), bolt heads picked out. Mean kept (61)."""
    img = M.painted_metal(719, base=(74, 62, 54), grain=3, mottle=5, panel=False, chips=3, under=(96, 90, 84))
    M.rust(img, 0.35, 720, color=(126, 70, 38), dark=(70, 44, 30))
    for y0 in range(0, S, 8):
        for x in range(S):
            M.touch(img, x, y0, 0.16)
            M.touch(img, x, y0 + 7, -0.18)
    for (x, y) in ((3, 3), (13, 3), (23, 3), (8, 19), (18, 19), (28, 19)):
        M.screw(img, x, y, slot=False)
    return match_mean(img, 61)


def drum(top):
    """The oil drum's wall (top=0) and lid (top=1): painted and rusted steel, drawn in tools/l1props_tex.py."""
    import l1props_tex
    return l1props_tex.drum(top)


def props_textures():
    """Small textures for 3D props: metal, tubes, valve, cabinet front, hazard sign, floor lines."""
    save(noise_fill(hexrgb(0x8C9196), 8, 400), "block/props/metal.png")
    save(noise_fill(hexrgb(0x3A3E42), 6, 401), "block/props/metal-dark.png")
    save(noise_fill(hexrgb(0xA8261E), 10, 402), "block/props/valve.png")
    save(noise_fill(hexrgb(0xF4F8FA), 2, 403), "block/props/tube-white.png")
    save(noise_fill(hexrgb(0xFFB868), 3, 404), "block/props/tube-warm.png")
    save(noise_fill(hexrgb(0x8E9294), 4, 405), "block/props/tube-off.png")
    save(noise_fill(hexrgb(0xD8DADA), 3, 406), "block/props/conduit.png")

    front = noise_fill(hexrgb(0x55605A), 6, 407)
    d = ImageDraw.Draw(front)
    d.rectangle([2, 2, S - 3, S - 3], outline=(30, 34, 32, 255))
    for x in range(6, 27, 3):  # vent slots
        d.line([x, 20, x, 27], fill=(28, 30, 30, 255))
    d.rectangle([6, 6, 12, 10], fill=(180, 40, 30, 255))  # warning label
    d.rectangle([18, 6, 26, 10], fill=(220, 214, 196, 255))
    save(front, "block/props/cabinet-front.png")

    sign = tunnel_concrete(408)
    d = ImageDraw.Draw(sign)
    d.rectangle([6, 8, 25, 23], fill=(232, 192, 40, 255))
    for k in range(-16, 32, 6):  # hazard stripes
        d.line([6 + k, 23, 6 + k + 15, 8], fill=(30, 30, 30, 255), width=2)
    d.rectangle([6, 8, 25, 23], outline=(30, 30, 30, 255))
    sign = sign.crop((0, 0, S, S))
    save(sign, "block/level2/tunnelwall-warning.png")

    for axis in ("ns", "we"):
        img = concrete_floor("plain")
        box = (15, 0, 16, S - 1) if axis == "ns" else (0, 15, S - 1, 16)
        painted_line(img, box, (214, 214, 202), 3500 + len(axis) + (axis == "ns"))
        save(img, f"block/level1/concretefloor-line{axis}.png")


def parking_textures():
    for axis in ("we", "ns"):
        img = concrete_floor("plain", 1)
        box = (0, 14, S - 1, 17) if axis == "we" else (14, 0, 17, S - 1)
        painted_line(img, box, (212, 178, 48), 3510 + (axis == "ns"))
        save(img, f"block/level1/concretefloor-dash{axis}.png")

    # The wheel stop: precast concrete painted in yellow and grey bands, the paint chipped at the arrises
    stop = pillar_concrete(3520)
    for x in range(0, S, 8):  # yellow-and-grey striped wheel stop
        painted_line(stop, (x, 0, x + 3, S - 1), (210, 178, 56), 3521 + x, wear=0.06)
    for x in range(S):
        M.touch(stop, x, 0, 0.1)
        M.touch(stop, x, S - 1, -0.12)
    save(stop, "block/level1/wheelstop.png")

    for name, colour in (("red", 0x8E2222), ("blue", 0x2A4A7E), ("white", 0xD8D8D2), ("black", 0x26282A)):
        img = noise_fill(hexrgb(colour), 6, 430 + len(name))
        blotch(img, (8, 24), 7, (90, 80, 70), 0.35, 22)  # dust and grime
        save(img, f"block/level1/car-{name}.png")
    glass = noise_fill(hexrgb(0x1C2428), 4, 440)
    glass.putalpha(104)  # tinted, so the interior shows through (the car blocktype is a Transparent pass)
    d = ImageDraw.Draw(glass)
    d.line([4, 2, 14, 12], fill=(70, 84, 92, 170), width=2)  # reflection
    save(glass, "block/level1/car-glass.png")
    car_wreck_textures()


def car_wreck_textures():
    """Level 1's wrecks: the paint faded and grimed and rusting through at the edges and in blooms, the black one
    burnt out to grey ash and rust; the windscreen crazed round a hole; the seats' cracked vinyl."""
    for name, colour in (("redwreck", 0x7A2A24), ("bluewreck", 0x3A4E6C), ("whitewreck", 0xBDB8A8), ("burnt", 0x2E2A26)):
        img = noise_fill(hexrgb(colour), 7, 450 + len(name))
        rust = (122, 64, 34) if name != "burnt" else (110, 58, 30)
        rng = random.Random(451 + len(name))
        for k in range(7 if name != "burnt" else 11):
            blotch(img, (rng.randrange(S), rng.randrange(S)), rng.randint(3, 7), rust, rng.uniform(0.45, 0.8), 452 + k)
        blotch(img, (rng.randrange(S), S - 3), 9, (96, 88, 74), 0.45, 470)  # road dirt up the sills
        if name == "burnt":
            for k in range(4):  # grey ash where the paint blistered off
                blotch(img, (rng.randrange(S), rng.randrange(S)), rng.randint(4, 8), (92, 88, 82), 0.5, 480 + k)
        save(img, f"block/level1/car-{name}.png")
    glass = noise_fill(hexrgb(0x1C2428), 4, 441)
    glass.putalpha(120)
    d = ImageDraw.Draw(glass)
    cx, cy = 20, 12
    rng = random.Random(442)
    for k in range(9):  # cracks running out from the impact
        a = k * math.tau / 9 + rng.uniform(-0.2, 0.2)
        r = rng.randint(9, 22)
        d.line([cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)], fill=(150, 160, 164, 220), width=1)
    for r in (3, 6):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(130, 140, 146, 200))
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(6, 6, 8, 0))  # the hole (nothing there)
    save(glass, "block/level1/car-glass-broken.png")
    seat = noise_fill(hexrgb(0x4A3426), 6, 443)
    d = ImageDraw.Draw(seat)
    for y in range(4, S, 8):  # piping
        d.line([0, y, S - 1, y], fill=(58, 42, 30, 255))
    d.line([9, 10, 17, 19], fill=(176, 160, 120, 255), width=2)  # the foam showing through a split
    save(seat, "block/level1/car-seat.png")
    car_interior_textures()


def car_interior_textures():
    """What you see through a car's glass (tools/gen_shapes.py `parking`): twill seat cloth, dashboard and door-card
    plastic, floor carpet, the headliner, a door card with its stitched panel, the dials and the radio (painted in the
    top-left corner of their texture: their faces map just that part), and for the wrecks the same worn, stained and
    split, with the foam showing."""
    def _lift(c, d):
        return tuple(int(v) for v in M.lift(c, d))

    def worn(img, seed, dirt, amount=0.35):
        M.grime(img, amount, seed=seed, color=dirt, cover=0.7)
        M.scratches(img, 5, seed=seed + 1, length=(3, 9), light=0.18)
        return img

    save(M.fabric(5300, base=(124, 112, 96), weave="twill", tone2=(116, 104, 90), contrast=7, grain=3, mottle=5),
         "block/level1/car-cloth.png")

    trim = M.rubber(5301, base=(66, 62, 58), grain=3, mottle=4)
    M.scratches(trim, 3, seed=5302, length=(3, 7), light=0.1)
    save(trim, "block/level1/car-trim.png")
    save(worn(M.rubber(5301, base=(60, 57, 52), grain=3, mottle=5), 5303, (96, 88, 72)), "block/level1/car-trimworn.png")

    save(M.carpet(5304, base=(86, 82, 78), mix2=0.2, tone2=(74, 72, 70), pile=6, grain=3, mottle=5), "block/level1/car-carpet.png")
    worncarpet = M.carpet(5304, base=(80, 74, 66), mix2=0.3, tone2=(66, 62, 56), pile=6, grain=3, mottle=6)
    M.stain(worncarpet, 5305, radius=8, color=(58, 50, 38), strength=0.5, at=(10, 12))
    M.stain(worncarpet, 5306, radius=6, color=(104, 92, 66), strength=0.4, at=(23, 22))
    save(worn(worncarpet, 5307, (92, 82, 62), 0.4), "block/level1/car-carpetworn.png")

    save(M.fabric(5308, base=(170, 164, 148), weave="plain", contrast=4, grain=3, mottle=4), "block/level1/car-liner.png")
    liner = M.fabric(5308, base=(150, 142, 120), weave="plain", contrast=4, grain=3, mottle=5)
    M.stain(liner, 5309, radius=10, color=(112, 92, 56), strength=0.55, at=(14, 12))
    save(liner, "block/level1/car-linerworn.png")

    def doorcard(seed, base, wear):
        img = M.rubber(seed, base=base, grain=3, mottle=4)
        d = ImageDraw.Draw(img)
        d.rectangle([2, 3, 29, 28], outline=_lift(base, -14) + (255,))   # the moulded panel
        d.line([3, 17, 28, 17], fill=_lift(base, 12) + (255,))           # the seam where the vinyl insert starts
        for x in range(4, 29, 3):
            d.point((x, 18), fill=_lift(base, -16) + (255,))               # its stitching
        M.bevel(img, box=(2, 3, 30, 29), width=1, strength=0.16)
        return worn(img, seed + 1, (90, 82, 66), 0.3) if wear else img
    save(doorcard(5310, (70, 66, 60), False), "block/level1/car-doorcard.png")
    save(doorcard(5312, (64, 60, 52), True), "block/level1/car-doorcardworn.png")

    # The instrument cluster: two round dials and a row of warning lamps, in the top-left 16 x 6 px (the cluster's face
    # is 8 x 3 units, which the shape maps to just that part of the texture)
    dials = M.rubber(5314, base=(36, 36, 36), grain=2, mottle=3)
    d = ImageDraw.Draw(dials)
    for cx in (4, 11):
        d.ellipse([cx - 3, 0, cx + 3, 6], fill=(14, 16, 16, 255), outline=(120, 118, 108, 255))
        d.line([cx, 3, cx + 1, 1], fill=(206, 196, 150, 255))
        for a in range(-60, 61, 30):
            d.point((cx + round(2.3 * math.sin(math.radians(a))), 3 - round(2.3 * math.cos(math.radians(a)))), fill=(190, 184, 160, 255))
    for x, c in ((14, (190, 60, 40)), (15, (210, 170, 60))):
        d.point((x, 5), fill=c + (255,))
    save(dials, "block/level1/car-dials.png")

    # The radio: a dark face with a station window, two knobs and a row of buttons, in the top-left 12 x 6 px
    radio = M.rubber(5315, base=(40, 40, 42), grain=2, mottle=3)
    d = ImageDraw.Draw(radio)
    d.rectangle([2, 0, 9, 2], fill=(52, 70, 60, 255), outline=(96, 98, 92, 255))
    for x in (0, 11):
        d.rectangle([x, 0, x + 1, 2], fill=(120, 118, 110, 255))
    for x in range(1, 11, 2):
        d.point((x, 4), fill=(130, 126, 116, 255))
    save(radio, "block/level1/car-radio.png")

    # Foam showing through a split cushion
    foam = M.noise_hv((170, 142, 78), 8, 5316, (S, S), 10, (16, 8), M.DRIFT)
    save(foam, "block/level1/car-foam.png")


def text_img(img, text, box, color, size):
    """Draws centred text into the given box, rendered large and scaled down for crisp pixels."""
    from PIL import ImageFont
    x0, y0, x1, y1 = box
    scale = 4
    big = Image.new("RGBA", ((x1 - x0) * scale, (y1 - y0) * scale), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    font = ImageFont.load_default(size=size * scale)
    w, h = d.textbbox((0, 0), text, font=font)[2:]
    d.text(((big.width - w) / 2, (big.height - h) / 2 - scale), text, font=font, fill=color)
    small = big.resize((x1 - x0, y1 - y0), Image.LANCZOS)
    img.alpha_composite(small, (x0, y0))


def bars_steel():
    """Level 3's bars: cold blue-grey steel, darker at the edges of a bar and with a bright specular stripe down it, so
    they read as round metal and not as pale wooden pickets in the amber haze. The left half runs across a vertical bar
    (the bars map it over their width), the right half the same turned for the horizontal rails; flecks of rust."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    base = (84, 90, 98)
    grain = smooth_noise(S, S, 4, 511)
    rng = random.Random(512)
    for y in range(S):
        for x in range(S):
            t = (x % 16 + 0.5) / 16 if x < 16 else (y + 0.5) / S  # across the bar, or across the rail
            a = (t - 0.5) * math.pi
            f = 0.55 + 0.5 * math.cos(a) ** 1.5 + 0.75 * math.exp(-((t - 0.36) / 0.07) ** 2)
            g = 0.92 + 0.16 * grain[y][x]
            px[x, y] = tuple(clamp(base[i] * f * g) for i in range(3)) + (255,)
    for _ in range(10):  # rust flecks
        x, y = rng.randrange(S), rng.randrange(S)
        for k in range(rng.randint(1, 3)):
            if y + k < S:
                px[x, y + k] = (92, 58, 36, 255)
    return img


# ---------------- Level 3 (B6) ----------------
# The user kept Level 2's original concrete over B5's restyle, so Level 3 keeps its old tones (each texture's mean
# colour is matched to the old one's) and its old units (brick 8 x 4 px, glazed tile 16 x 8, cinder block 16 x 16);
# what changes is structure (each unit shaded as a unit, joints recessed) and tiling (no feature in every block).
L3_MEAN = {"brick": (96, 42, 20), "glazed": (118, 93, 65), "cinder": (51, 46, 24), "dusty": (138, 125, 108),
           "plaster": (92, 87, 77)}
_L3_SHIFT = {}


def mean_rgb(img):
    px = img.load()
    w, h = img.size
    tot, n = [0.0, 0.0, 0.0], 0
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c[3]:
                n += 1
                for i in range(3):
                    tot[i] += c[i]
    return [t / max(1, n) for t in tot]


def shift_rgb(img, d):
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            px[x, y] = M.rgba((c[0] + d[0], c[1] + d[1], c[2] + d[2]), c[3])
    return img


def match_rgb(img, target, key=None):
    """img shifted channel by channel so its mean colour is `target`. With `key`, the shift is worked out once (on the
    first version drawn under that key) and reused, so the versions of one surface keep the same ground where they
    meet; the features of a version (a stain) then move its mean by the little they should."""
    if key is None or key not in _L3_SHIFT:
        m = mean_rgb(img)
        d = [target[i] - m[i] for i in range(3)]
        if key is not None:
            _L3_SHIFT[key] = d
    else:
        d = _L3_SHIFT[key]
    return shift_rgb(img, d)


def calm_hue(img, base, k):
    """Pulls each pixel's hue a fraction k back toward `base` at the pixel's own brightness: for a dark, dull surface
    whose hue wander (and the cool drift of its shadows) reads as lavender patches."""
    px = img.load()
    w, h = img.size
    lb = M.lum(base)
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            px[x, y] = M.rgba(M.mix(c, M.lift(base, M.lum(c) - lb, 0), k), c[3])
    return img


def _unit_boxes(course, length, offset, mortar_w=1, size=S):
    """The faces (x0, y0, x1, y1, end exclusive, x0 may be negative: wrap) of the units matlib.brick lays."""
    out = []
    for r in range(size // course):
        shift = int(round(r * offset * length)) % length
        for k in range(size // length + 1):
            x0 = shift + k * length - length
            if x0 + length - mortar_w <= 0 or x0 >= size:
                continue
            out.append((x0, r * course, x0 + length - mortar_w, r * course + course - mortar_w))
    return out


def l3_brick(alt=0):
    """Level 3's red brick: the old units (8 x 4 px, eight courses to a block) and colours, now each brick its own
    shade and hue (some more orange, as the old four tones were), lit along its top, dark along its foot, with the
    bed joint under it in shadow. The three versions share every face and mortar texture and differ only in which
    bricks are darker or warmer (matlib.brick's `tones`), so they mix without a patchwork."""
    img = M.brick(5010, base=(112, 46, 18), mortar=(60, 32, 20), course=4, length=8, offset=0.5, mortar_w=1,
                  jitter=11, hue=8, recess=1.0, pits=0.02, grain=4, mottle=7, tones=5010 + 7 * alt)
    return match_rgb(img, L3_MEAN["brick"], "brick")


def l3_glazed(alt=0):
    """Level 3's glazed structural tile: the old 16 x 8 px units in running bond, the upper two courses of each block
    a darker ochre as before. Each tile is now a glazed face: an even glaze with a soft sheen toward its upper left, a
    bright lit top edge and a dark foot, the 1 px joint recessed. Faint crazing in a few tiles. Three versions differ
    only in the tiles' shades and which ones are crazed."""
    img = M.brick(5020, base=(140, 112, 84), mortar=(52, 38, 20), course=8, length=16, offset=0.5, mortar_w=1, jitter=5,
                  hue=3, recess=1.0, pits=0.0, grain=2, mottle=4, tones=5020 + 7 * alt)
    px = img.load()
    for y in range(16):  # the two-tone band, as the old texture's
        if y % 8 == 7:
            continue
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (clamp(r * 0.88), clamp(g * 0.85), clamp(b * 0.76), a)
    rng = random.Random(M.sub(5020 + 7 * alt, "craze"))
    boxes = _unit_boxes(8, 16, 0.5)
    crazed = set(rng.sample(range(len(boxes)), 2))
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        for y in range(y0, y1):
            for x in range(x0, x1):
                t = ((x - x0) / (x1 - x0) * 0.6 + (y - y0) / (y1 - y0)) / 1.6
                M.touch(img, x % S, y, 0.07 * (1 - t) - 0.03)
        for x in range(x0 + 1, x1 - 1):  # the glaze catches the light along the top edge
            M.touch(img, x % S, y0, 0.04)
        M.touch(img, (x0 + 1) % S, y0 + 1, 0.06)
        if i in crazed:
            x, y = rng.uniform(x0 + 2, x1 - 2), rng.uniform(y0 + 1, y1 - 1)
            a = rng.uniform(0, 6.3)
            for _ in range(rng.randint(5, 9)):
                if x0 < x < x1 - 1 and y0 < y < y1 - 1:
                    M.touch(img, round(x) % S, round(y), -0.06)
                a += rng.uniform(-1.0, 1.0)
                x, y = x + math.cos(a), y + math.sin(a) * 0.6
    return match_rgb(img, L3_MEAN["glazed"], "glazed")


def l3_cinder(alt=0):
    """Level 3's cinder block, in the machine rooms: the old 16 x 16 px units and dark olive. Each block now has the
    open, pitted face of cinder concrete (coarse aggregate, each pore dark with a lit lip under it), its own shade, a
    lit top and a shadowed foot, and recessed joints. Three versions differ in shades and pores only."""
    t = 5030 + 7 * alt
    img = M.brick(5030, base=(62, 56, 32), mortar=(34, 31, 18), course=16, length=16, offset=0.5, mortar_w=1, jitter=3,
                  hue=1.5, recess=1.0, pits=0.0, grain=5, mottle=5, tones=t)
    rng = random.Random(M.sub(t, "pores"))
    for (x0, y0, x1, y1) in _unit_boxes(16, 16, 0.5):
        for _ in range(18):
            x, y = rng.randrange(x0, x1) % S, rng.randrange(y0 + 1, y1 - 1)
            M.touch(img, x, y, -rng.uniform(0.07, 0.14))
            M.touch(img, x, y + 1, 0.04)
            if rng.random() < 0.3:
                M.touch(img, (x + 1) % S, y, -0.06)
        for _ in range(14):
            x, y = rng.randrange(x0, x1) % S, rng.randrange(y0 + 1, y1 - 1)
            M.touch(img, x, y, rng.uniform(0.06, 0.12))
    calm_hue(img, (62, 56, 32), 0.6)  # (round 2) no olive and grey-green blocks side by side
    return match_rgb(img, L3_MEAN["cinder"], "cinder")


def dusty_floor(alt=0):
    """Level 3's dusty concrete floor (also under Level 5's boilers). The old one put the same dark blotch in every
    block, a polka-dot grid. Now concrete in the old tone with a film of settled dust, three versions turned at random
    that meet without a step (`matlib.turn_safe`, as D1's floors); grit in one version and a faint scuff in another,
    both kept inside the block."""
    base = (140, 127, 110)
    seed = 5040 + alt
    img = M.concrete(seed, base=base, grain=4, mottle=5, aggregate=0.02, pores=0.01, patches=3.5, patch_hue=1.2, hue=1.4)
    ground = M.noise_hv(base, 0, 5040, S, 5, (16,), hue=0)
    M.turn_safe(img, ground, band=8)
    dust = M.fbm((S, S), M.sub(seed, "dust"), (4, 2), 0.6)  # settled dust: fine, pale and soft
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.mix(M.lift(px[x, y], dust[y][x] * 3), (150, 142, 128), 0.08))
    plain = img.copy()
    rng = random.Random(M.sub(seed, "grit"))
    if alt == 1:
        for _ in range(22):
            x, y = rng.uniform(8, 24), rng.uniform(8, 24)
            M.touch(img, round(x), round(y), -rng.uniform(0.12, 0.22))
            M.touch(img, round(x), round(y) + 1, 0.04)
    if alt == 2:
        tyre_scuff(img, M.sub(seed, "scuff"), strength=0.035)
    img = inside_block(plain, img)
    return match_rgb(img, L3_MEAN["dusty"], "dusty")


def plaster_ceiling(alt=0):
    """Level 3's dark plaster ceiling (also over Level 5's boilers). The old one had the same stain in every block. Now
    a painted plaster in the old tone, its broad clouding shared at the block edges so the versions turn and mix
    freely: three plain versions, a fourth with a water stain and a tide line and a fifth with a fainter damp mark,
    each mark kept inside its block and listed about one block in fourteen."""
    base = (94, 89, 78)
    seed = 5050 + alt
    img = calm_hue(M.plaster(seed, base=base, grain=3, mottle=4, roller=0.35, bumps=0.015), base, 0.6)
    # (the shared ground is only the broadest clouding: anything finer, made four-fold symmetric, would come back at
    # the same place along every block's edge as a grid of spots)
    ground = M.noise_hv(base, 0, 5050, S, 6, (16,), hue=0)
    M.turn_safe(img, ground, band=8, keep=0.6)
    plain = img.copy()
    if alt == 3:
        M.stain(img, M.sub(seed, "stain"), radius=10, color=(66, 56, 40), strength=0.22, at=(16, 15), ring=0.5)
    if alt == 4:
        M.stain(img, M.sub(seed, "damp"), radius=6, color=(72, 64, 50), strength=0.2, at=(15, 17), ring=0.3)
    img = inside_block(plain, img)
    return match_rgb(img, L3_MEAN["plaster"], "plaster")


def l3_fixture_textures():
    """(B6) Materials for Level 3's modelled fixtures (gen_shapes.level3): the breaker panel's grey enamel and dead
    front, bakelite breakers and their toggles; the wall fan's housing, the dark well behind its blades, galvanised
    blades and a dark wire guard; the cable trays' galvanised steel; the cables' rubber jackets; the transformer's
    green-grey paint, its darker cooling fins and glazed porcelain bushings. Paint is matlib's, with grime and wear
    scattered over the face (these are model parts, so nothing sits along the texture's edges)."""
    def paint(seed, base, grime=0.2, rust=0.0, chips=5, top=False):
        img = M.painted_metal(seed, base=base, grain=4, mottle=6, panel=False, chips=chips, under=(98, 94, 86))
        M.grime(img, grime, seed + 1, cover=0.55)
        if rust:
            M.rust(img, rust, seed + 2, color=(112, 66, 40), dark=(70, 46, 32))
        M.scratches(img, 2, seed + 3)
        if top:
            M.grime(img, 0.35, seed + 4, color=(70, 64, 54), cover=0.7)
        return img
    save(paint(5201, (116, 118, 112)), "block/level3/panel-paint.png")
    save(paint(5205, (92, 94, 90), grime=0.15, chips=2), "block/level3/panel-face.png")
    img = M.noise_hv((40, 37, 34), 2, 5210, S, 3, hue=0.5)
    for y in range(0, S, 4):  # a sheen along the top of each moulded case
        for x in range(S):
            M.touch(img, x, y, 0.1)
    save(img, "block/level3/breaker.png")
    save(M.noise_hv((156, 150, 136), 2, 5211, S, 3), "block/level3/toggle.png")
    save(paint(5220, (82, 88, 80), grime=0.3, rust=0.08), "block/level3/fan-housing.png")
    save(M.noise_hv((22, 21, 20), 2, 5225, S, 3, hue=0.5), "block/level3/fan-well.png")
    blade = M.galvanised(5226, base=(168, 170, 166), spangle=8)
    M.grime(blade, 0.15, 5227, color=(60, 56, 48), cover=0.5)  # the dust a fan's blades gather
    save(blade, "block/level3/fan-blade.png")
    guard = M.brushed_metal(5228, base=(70, 72, 70), streak=6, sheen=6)
    M.grime(guard, 0.2, 5229, cover=0.5)
    save(guard, "block/level3/fan-guard.png")
    tray = M.galvanised(5230, base=(128, 130, 128), spangle=9)
    M.grime(tray, 0.28, 5231, color=(64, 60, 52), cover=0.6)
    save(tray, "block/level3/tray.png")
    cable = M.rubber(5235, base=(34, 33, 34), grain=2, mottle=3)
    for y in range(S):  # a soft sheen along the jacket
        for x in range(S):
            if y % 8 in (1, 2):
                M.touch(cable, x, y, 0.08)
    save(cable, "block/level3/cable.png")
    save(paint(5240, (88, 98, 84), grime=0.25, rust=0.05), "block/level3/transformer.png")
    save(paint(5245, (70, 78, 66), grime=0.3, rust=0.1, chips=2), "block/level3/transformer-fin.png")
    save(paint(5248, (84, 92, 80), grime=0.45, chips=2, top=True), "block/level3/transformer-top.png")
    # Glazed porcelain: a deep brown glaze, a highlight down one side of each shed
    img = M.noise_hv((122, 70, 40), 2, 5250, S, 3, hue=1.0)
    for y in range(S):
        for x in range(S):
            M.touch(img, x, y, 0.16 if x % 8 in (2, 3) else (-0.12 if x % 8 == 7 else 0.0))
    save(img, "block/level3/insulator.png")
    save(cabinet_warning(5255), "block/level3/warning.png")
    # The risers' skins: the wall pipes' own, turned so U goes round the pipe and V along it (gen_shapes.round_riser)
    for kind, name in (("rust", "riser-rust"), ("lagging", "riser-lagging")):
        save(wall_pipe_tex(kind).transpose(Image.Transpose.TRANSPOSE), f"block/level3/{name}.png")


def manhole_ladder_textures():
    """Layout version 9's manholes (gen_shapes.manhole_ladder): the ladder in worn safety-yellow paint over dark steel,
    so it reads down a dark shaft; the hazard stripes on the lip round the opening and on the step out of the water
    (black and yellow at 45 degrees, 8 px to a pair so they tile); the open lid's chequer plate."""
    ladder = M.painted_metal(seed=5301, base=(196, 158, 44), grain=3, mottle=6, panel=False, chips=10,
                             under=(70, 64, 58))
    M.rust(ladder, 0.12, seed=5302, cells=(4, 2))
    M.grime(ladder, 0.12, seed=5303)
    save(ladder, "block/level3/manholeladder.png")

    lip = M.noise_hv((40, 38, 34), 3, 5304, S, 4)
    yellow = M.noise_hv((206, 166, 46), 3, 5305, S, 5)
    p, q = lip.load(), yellow.load()
    for y in range(S):
        for x in range(S):
            if (x + y) % 8 < 4:
                p[x, y] = q[x, y]
    M.grime(lip, 0.2, seed=5306)  # trodden dust
    M.scratches(lip, 8, seed=5307)
    save(lip, "block/level3/hazardlip.png")

    lid = M.noise_hv((92, 90, 86), 3, 5308, S, 6)
    for y in range(0, S, 8):  # diamond tread: raised lenses, alternately turned, lit on top, a shadow under
        for x in range(0, S, 8):
            turn = (x // 8 + y // 8) % 2
            for i in range(-2, 3):
                cx, cy = (x + 4 + i, y + 4 - i) if turn else (x + 4 + i, y + 4 + i)
                M.touch(lid, cx % S, cy % S, 0.2)
                M.touch(lid, cx % S, (cy + 1) % S, -0.16)
    M.rust(lid, 0.18, seed=5309, edges=True)
    M.grime(lid, 0.14, seed=5310)
    save(lid, "block/level3/hatchlid.png")


def level3_textures():
    l3_fixture_textures()
    manhole_ladder_textures()
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        save(l3_glazed(alt), f"block/level3/l3wall-glazed{v}.png")
        save(l3_brick(alt), f"block/level3/l3wall-brick{v}.png")
        save(l3_cinder(alt), f"block/level3/l3wall-cinder{v}.png")
        save(dusty_floor(alt), f"block/level3/dustyfloor{v}.png")
        save(plaster_ceiling(alt), f"block/level3/plasterceiling{v}.png")
    save(plaster_ceiling(3), "block/level3/plasterceiling-4.png")
    save(plaster_ceiling(4), "block/level3/plasterceiling-5.png")
    # (B6: the painted breaker panel, fan grille, transformer fins and cable are gone; l3_fixture_textures above)
    save(bars_steel(), "block/level3/bars.png")
    img = noise_fill(hexrgb(0x2E2C2A), 6, 514)
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], outline=(70, 66, 60, 255), width=2)
    for i in range(6, 27, 5):
        d.line([i, 6, i, 25], fill=(60, 56, 52, 255))
    save(img, "block/level3/manhole.png")
    img = Image.new("RGBA", (S, S), (255, 248, 222, 255))  # daylight through a window
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(120, 110, 90, 255), width=2)
    d.line([16, 0, 16, S - 1], fill=(120, 110, 90, 255), width=2)
    d.line([0, 16, S - 1, 16], fill=(120, 110, 90, 255), width=2)
    save(img, "block/level3/windowglow.png")
    for i, number in enumerate(("447", "112", "318", "905", "563", "274", "781", "036")):
        img = Image.new("RGBA", (S, S), (236, 234, 226, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=(90, 90, 90, 255))
        text_img(img, number, (2, 4, 30, 18), (20, 20, 20, 255), 11)
        for y in (21, 25):  # illegible text beneath
            d.line([6, y, 26, y], fill=(120, 120, 120, 255))
        save(img, f"block/level3/roomsign-{i}.png")


# ---------------- Level 4: the abandoned office (graphics pass B7) ----------------
#
# Every surface keeps its old tone: each texture's mean colour is matched to the noise fill it replaces (L4_MEAN), and
# the versions of one surface share their ground and their shift (`match_rgb` with a key), so they mix without a
# patchwork. The drop ceiling is Level 0's module (matlib.ceiling_tile, troffer_lens, the D1 troffer) in the office's
# 2 x 4 layout and greys.

L4_MEAN = {"wall": (216.1, 213.1, 212.1), "carpet": (133.3, 131.3, 125.3), "ghost": (110.3, 108.3, 103.3),
           "ceiling": (206.1, 202.4, 197.5), "partition": (135.5, 137.5, 131.8), "laminate": (180.2, 156.2, 120.2),
           "crt": (201.0, 194.0, 174.0), "chair": (51.0, 54.0, 60.0), "filing": (136.8, 140.6, 144.6),
           "cooler": (229.9, 229.9, 225.9)}
OFFICE_WALL = hexrgb(0xD8D5D4)
OFFICE_CARPET = hexrgb(0x85837D)
OFFICE_TILE = (216, 212, 207)
OFFICE_RAIL = (140, 138, 133)  # the old grid's grey: darker than the tile, so the 2 x 4 grid reads as it did


def office_wall(alt=0):
    """Painted drywall in the old off-white: matlib.plaster with a fine roller stipple and the faintest clouding, its
    hue held close to the base (no lavender or green patches on a near-white wall). Every version is the same paint
    (one seed): the second has a touched-up patch a shade off the wall, and is listed one block in six. (Round 2
    dropped its two nail holes: pin specks that showed at the same place.)"""
    img = calm_hue(M.plaster(5200, base=OFFICE_WALL, grain=2, mottle=3, roller=0.55, bumps=0.0), OFFICE_WALL, 0.7)
    if alt == 1:
        rng = random.Random(5201)
        px = img.load()
        for y in range(18, 25):  # a patch of touch-up paint, a little warmer and flatter than the wall round it
            for x in range(4, 13):
                if rng.random() < 0.9 - 0.1 * abs(y - 21):
                    px[x, y] = M.rgba(M.hue_shift(M.mix(px[x, y], OFFICE_WALL, 0.6), 1.5))
    return match_rgb(img, L4_MEAN["wall"], "l4wall")


def office_baseboard(img, seed=5210):
    """The office's skirting: 5 px of dark grey vinyl cove base at the foot of the drywall (where the old flat band
    was), its rounded cap lit from above, the face, the toe darkest where it meets the carpet, a hairline of shade on
    the wall over the cap and a faint dirt band above it. No scuffs: the wall's foot repeats every block along every
    corridor, and a scuff in each block reads as a dashed line."""
    vinyl = (64, 64, 66)
    rng = random.Random(seed)
    scuff_band(img, seed + 1, 17, 26, n=0, dirt=(120, 116, 104))
    px = img.load()
    for x in range(S):
        px[x, 26] = M.rgba(M.lift(px[x, 26], -9))
        px[x, 27] = M.rgba(M.lift(vinyl, 30 + rng.uniform(-2, 2)))
        px[x, 28] = M.rgba(M.lift(vinyl, 12 + rng.uniform(-2, 2)))
        px[x, 29] = M.rgba(M.lift(vinyl, 2 + rng.uniform(-2, 2)))
        px[x, 30] = M.rgba(M.lift(vinyl, -3 + rng.uniform(-2, 2)))
        px[x, 31] = M.rgba(M.lift(vinyl, -14 + rng.uniform(-2, 2)))
    return img


def _office_pile(seed, base):
    return M.carpet(seed, base=base, tone2=M.hue_shift(M.lift(base, -16), 2), mix2=0.4, loop=True, pile=5, grain=4,
                    mottle=1.5)


def office_carpet(alt=0, kind="plain"):
    """Low commercial loop-pile carpet in the old grey-beige: two yarns twisted (a fine heather of a lighter and a
    darker thread), trodden a little, and (D1's dingy) not vacuumed in a long time. Three versions, turned at random
    by the blocktype, meet without a step (`matlib.turn_safe` on one shared ground). 'ghost', the darker mark where
    furniture once stood, is the same pile less trodden and darker; its blocks lie in the layout's patches."""
    seed = (5220 if kind == "plain" else 5230) + alt
    img = _office_pile(seed, OFFICE_CARPET)
    ground = M.noise_hv(OFFICE_CARPET, 0, 5220, S, 4, (16,), hue=0)
    M.turn_safe(img, ground, band=8, keep=0.5)
    dingy(img, seed, dull=0.08, dim=0.0, grime=0.06 if kind == "plain" else 0.05, flecks=8 if kind == "plain" else 4)
    return match_rgb(img, L4_MEAN["carpet" if kind == "plain" else "ghost"], "l4carpet-" + kind)


def office_ceiling(alt=0, stain=None):
    """The office's 2 x 4 drop ceiling: Level 0's lay-in tile (matlib.ceiling_tile: fissured board, a recess where it
    steps up into the grid, the T-bar split between neighbours) as two 32 x 16 tiles per block, as the old one was laid
    out, in the office's grey-white with its darker grid. Three plain versions (other fissures; one ground), and with
    `stain` (0 or 1) a water stain in one of the two tiles, kept inside it."""
    img = Image.new("RGBA", (S, S))
    for half in (0, 1):
        seed = 5240 + alt * 2 + half
        tile = M.ceiling_tile(seed, size=(S, S // 2), base=OFFICE_TILE, rail=OFFICE_RAIL, fissures=0.6, recess=2)
        img.paste(tile, (0, half * S // 2))
    # (the recess's warm light and cool shade show as cream and lilac on a near-white board: held to the board's hue)
    calm_hue(img, OFFICE_TILE, 0.6)
    if stain is not None:  # (round 2) a brown water stain with a tide ring, spread over both tiles of the block (the
        # T-bar between them unstained), fading out before the block's edge; `stain` (0 or 1) moves it up or down
        st = img.copy()
        M.stain(st, 5250 + alt, radius=9, color=(150, 116, 66), strength=0.55, at=(15 + 3 * stain, 13 + 6 * stain), ring=0.8)
        p, q = img.load(), st.load()
        for y in range(1, S - 1):
            if y in (S // 2 - 1, S // 2):
                continue
            for x in range(1, S - 1):
                e = min(x - 1, S - 2 - x, y - 1, S - 2 - y)
                t = max(0.0, min(1.0, (e - 1) / 3.5))
                if t:
                    p[x, y] = M.rgba(M.mix(p[x, y], q[x, y], t))
    return match_rgb(img, L4_MEAN["ceiling"], "l4ceiling")


OFFICE_TROFFER = {"on": ((252, 252, 248), (255, 254, 248), 1.0), "off": ((176, 176, 170), (176, 176, 170), 0.0)}


def office_troffer(state):
    """The office's 2 x 4 troffer: Level 0's (the D1 version, no dark ring round the lens) in the office's grid grey,
    with three tubes behind the lens. The light stays a cube and keeps its light values."""
    return troffer(state, rail=OFFICE_RAIL, frame=(208, 206, 200), table=OFFICE_TROFFER, tubes=3)


def partition_fabric():
    """The cubicle panels' fabric: a fine plain weave in the old grey-green, two threads a touch apart in hue (a
    tweed fleck), soft and matte; seamless both ways, as the panels run on block after block."""
    base = (136, 138, 132)
    img = M.fabric(5260, base=base, weave="plain", tone2=M.hue_shift(M.lift(base, -4), -2), contrast=2, grain=3,
                   mottle=3, thread=4)  # (round 2) contrast 6 read as a 1 px checkerboard at 1-2 blocks
    rng = random.Random(5261)
    for _ in range(40):  # flecks of a darker and a lighter yarn in the weave
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, rng.choice((-0.07, -0.05, 0.05)))
    return match_rgb(calm_hue(img, base, 0.4), L4_MEAN["partition"])


def partition_rail(top=False):
    """Anodised aluminium for the partitions' top cap and posts: brushed along the run. For the cap's sides (`top`
    False) the first row is the rolled edge catching the light and the third its shade, so a 1.5-unit face shows a
    lit top edge; the cap's top face is plain brushed metal."""
    img = M.brushed_metal(5270, base=(152, 154, 152), grain=3, streak=6, sheen=5)  # (round 2) duller, nearer the old grey
    if not top:
        px = img.load()
        for x in range(S):
            for y in range(0, S, 4):  # the edge every 4 rows: the cap's faces are 1.5 units (3 px) tall
                px[x, y] = M.rgba(M.lift(px[x, y], 26))
                px[x, (y + 2) % S] = M.rgba(M.lift(px[x, (y + 2) % S], -14))
    return img


def laminate_grain(seed, base, direction="h"):
    """Printed wood-grain laminate (desk and table tops, the desks' end panels): one sheet with no boards or seams,
    long streaks along the grain from matlib.brushed_metal's stretched noise, warm, plus a few wavy darker grain lines
    and a faint satin sheen, so tops that meet (a conference table) run on without an edge."""
    img = M.brushed_metal(seed, base=base, grain=3, direction="h", streak=12, sheen=4, drift=M.DRIFT)
    wave = M.value_noise((S, S), (S // 2, S // 2), M.sub(seed, "wave"))
    lines = M.value_noise((S, S), (8, 2), M.sub(seed, "lines"))
    px = img.load()
    for y in range(S):
        for x in range(S):
            yy = (y + wave[y][x] * 2.5) % S
            k = lines[int(yy)][x]
            if k > 0.5:  # short grain streaks (a lattice 8 px along the grain, so no line runs the whole width)
                px[x, y] = M.rgba(M.lift(px[x, y], -(k - 0.5) * 26))
    if direction == "v":
        img = img.transpose(Image.TRANSPOSE)
    return img


def laminate_edge():
    """The dark vinyl edge-banding of a laminate top or panel: plain, a lit first row (the rounded arris) and a darker
    third, as the faces it covers are 1-1.5 units deep."""
    base = (118, 96, 70)
    img = M.noise_hv(base, 2, 5280, S, 3, (16, 8))
    px = img.load()
    for x in range(S):
        for y in range(0, S, 4):
            px[x, y] = M.rgba(M.lift(px[x, y], 22))
            px[x, (y + 2) % S] = M.rgba(M.lift(px[x, (y + 2) % S], -10))
    return img


def beige_plastic(seed, base=(201, 194, 174), yellow=0.0):
    """Moulded office plastic (the CRT, the keyboard, the copier): a fine matte grain, broad faint yellowing, and a few
    scuffs."""
    img = M.noise_hv(base, 4, seed, S, 2, (16, 8), hue=1.0)  # (round 2) a fine moulded grain, not an airbrush
    if yellow:
        M.grime(img, yellow, M.sub(seed, "yellow"), color=(196, 176, 120), cells=(16, 8), cover=0.6)
    M.scratches(img, 2, M.sub(seed, "scuff"), length=(2, 3), light=0.05)
    return img


def crt_screen():
    """A dead terminal's screen: dark green glass, the curve of the tube darker toward its corners, faint scanlines,
    the prompt still burnt on, and the reflection of the room in a soft pale band across the top left."""
    img = noise_fill(hexrgb(0x16241A), 3, 528)
    px = img.load()
    for y in range(S):
        for x in range(S):
            dx, dy = (x - 15.5) / 16, (y - 15.5) / 16
            v = -22 * (dx * dx + dy * dy) ** 1.5 - (3 if y % 2 else 0)
            px[x, y] = M.rgba(M.lift(px[x, y], v, 0.05))
    ImageDraw.Draw(img).text((3, 4), "C:\\>_", fill=(80, 200, 100, 255))
    for y in range(S):
        for x in range(S):
            t = x + y * 1.4
            if 6 < t < 15:
                px[x, y] = M.rgba(M.mix(px[x, y], (150, 170, 160), 0.14 * (1 - abs(t - 10.5) / 4.5)))
    return img


def keyboard_keys():
    """Keycaps seen from above: beige keys on a 2 px pitch (each lit on its top-left pixel), dark gaps, the space bar
    along the front row. The keyboard's top is a 9 x 2.5 unit face: rows 0-4 of this texture."""
    base = (196, 190, 172)
    img = Image.new("RGBA", (S, S), (70, 68, 62, 255))
    px = img.load()
    rng = random.Random(5290)
    for y in range(0, S, 2):
        space = y % 10 == 8
        for x in range(0, S, 2):
            c = M.lift(base, rng.uniform(-4, 4))
            if space and 8 <= x < 24:
                px[x, y] = M.rgba(M.lift(c, 8))
                px[x + 1, y] = M.rgba(c)
                continue
            px[x, y] = M.rgba(M.lift(c, 10))
            px[x + 1, y] = M.rgba(c)
            px[x, y + 1] = M.rgba(M.lift(c, -14))
    return img


def chair_fabric(seed=5300, base=(54, 57, 63)):
    """The office chairs' upholstery: a charcoal tweed (a plain weave with a lighter and a darker yarn), worn shiny in
    places."""
    img = M.fabric(seed, base=base, weave="plain", tone2=M.hue_shift(M.lift(base, 10), -2), contrast=7, grain=3,
                   mottle=4, thread=3)
    return match_rgb(img, L4_MEAN["chair"], "l4chair")


def filing_paint(top=False):
    """The filing cabinets' baked enamel in the old blue-grey: matlib.painted_metal without panel edges (the drawers
    are geometry now), a few worn spots; the top a little dustier."""
    img = M.painted_metal(5310 + (1 if top else 0), base=(138, 142, 146), grain=4, mottle=2, panel=False, chips=0,
                          under=(160, 160, 158))
    if top:
        M.grime(img, 0.1, 5312, color=(150, 146, 134), cells=(8, 4), cover=0.5)
    return match_rgb(img, L4_MEAN["filing"], "l4filing")


def office_window(alt=0):
    """(Level 4 art) The clear window, a light block (a cube, its light unchanged): the pane is dark, cold glass with nothing
    to see through it (the wiki: any window not blacked out is a trap), a faint soft reflection of the room's strip lights
    and a few smudges of old condensation, no rain: the picture of rain runs read as a static image and is gone. In a
    satin aluminium frame with a lit inner edge and a mullion. Even, no gradient (the windows stack and run on)."""
    img = M.noise_hv((58, 64, 72), 2, 521 + alt, S, 5, (16, 8), hue=1.5)
    rng = random.Random(522 + 31 * alt)
    px = img.load()
    for _ in range(3 + alt):  # soft smudges of condensation: a pale blot a few px wide
        cx, cy, r = rng.randrange(4, 28), rng.randrange(4, 28), rng.randint(2, 4)
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                d = math.hypot(x - cx, y - cy)
                if d <= r and 3 <= x < S - 3 and 3 <= y < S - 3:
                    px[x, y] = M.rgba(M.lift(px[x, y], 7 * (1 - d / r)))
    for y in range(3, S - 3):  # the reflection of a strip light: a faint pale bar, offset by version
        for x in range(6 + 8 * alt, 8 + 8 * alt):
            px[x, y] = M.rgba(M.lift(px[x, y], 5))
    frame = (154, 156, 154)
    for i in range(S):
        for (x, y) in ((i, 0), (i, 1), (0, i), (1, i), (i, S - 1), (i, S - 2), (S - 1, i), (S - 2, i), (16, i)):
            px[x, y] = M.rgba(M.lift(frame, rng.uniform(-2, 2) + (8 if y <= 1 or x <= 1 else -10 if y >= S - 2 or x >= S - 2 else 0)))
    for i in range(2, S - 2):  # the frame's inner edge: shade on the glass under the head and beside the left jamb
        px[i, 2] = M.rgba(M.lift(px[i, 2][:3], -16))
        px[2, i] = M.rgba(M.lift(px[2, i][:3], -10))
        px[15, i] = M.rgba(M.lift(px[15, i][:3], -8))
        px[17, i] = M.rgba(M.lift(px[17, i][:3], 6))
    return img


def vending_textures():
    """The vending machine's materials: the cabinet's red baked enamel (the old red), the lit back wall of its window,
    an Almond Water bottle's label and cap, and the dark selection panel."""
    red = M.painted_metal(5320, base=(168, 40, 32), grain=4, mottle=2, panel=False, chips=0, under=(150, 146, 140))
    M.grime(red, 0.1, 5321, color=(80, 40, 30), cells=(8, 4), cover=0.4)
    glow = M.noise_hv((214, 226, 230), 2, 5322, S, 3, (16, 8))
    bottle = Image.new("RGBA", (S, S), (236, 228, 205, 255))  # cream plastic, a brown label band, a blue cap on top
    px = bottle.load()
    for y in range(S):
        for x in range(S):
            if y % 8 < 2:
                px[x, y] = M.rgba(M.lift((60, 110, 170), 10 if y % 8 == 0 else -6))
            elif 3 <= y % 8 <= 5:
                px[x, y] = M.rgba(M.lift((196, 160, 104), 6 if y % 8 == 3 else -4))
            else:
                px[x, y] = M.rgba(M.lift((236, 228, 205), -8 * (x % 2)))
    panel = M.painted_metal(5323, base=(44, 46, 50), grain=2, mottle=3, panel=False, chips=0, under=(120, 120, 118))
    return red, glow, bottle, panel


def cooler_textures():
    """The water cooler: white enamel body (the old white), and the bottle's tinted blue plastic with the water inside
    a little darker below a meniscus line every 8 px (the bottle face is cut to show one)."""
    body = M.painted_metal(5330, base=(230, 230, 226), grain=4, mottle=2, panel=False, chips=0, under=(170, 170, 166))
    bottle = M.noise_hv((156, 200, 230), 3, 5331, S, 4, (16, 8), hue=1.0)
    px = bottle.load()
    for y in range(S):
        for x in range(S):
            if x % 16 in (2, 3):  # the light catching the curve of the bottle
                px[x, y] = M.rgba(M.lift(px[x, y], 18))
            elif x % 16 in (13, 14):
                px[x, y] = M.rgba(M.lift(px[x, y], -12))
    return body, bottle


def level4_textures():
    save(office_wall(0), "block/level4/officewall.png")
    save(office_wall(1), "block/level4/officewall-2.png")
    save(office_window(), "block/level4/officewindow.png")
    save(office_window(1), "block/level4/officewindow-2.png")
    img = Image.new("RGBA", (S, S), (180, 210, 220, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(110, 114, 118, 255), width=2)
    save(img, "block/level4/officeglass.png")
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        save(office_carpet(alt), f"block/level4/officecarpet-plain{v}.png")
    for alt, v in ((0, ""), (1, "-2")):
        save(office_carpet(alt, "ghost"), f"block/level4/officecarpet-ghost{v}.png")
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        save(office_ceiling(alt), f"block/level4/officeceiling{v}.png")
    for state in ("on", "off"):
        save(office_troffer(state), f"block/level4/officelight-{state}.png")
    save(partition_fabric(), "block/level4/partition.png")
    save(partition_rail(), "block/level4/partitionrail.png")
    save(partition_rail(True), "block/level4/partitionrail-top.png")
    save(M.noise_hv((62, 62, 64), 2, 5275, S, 3, (16, 8)), "block/level4/partitionbase.png")
    # Laminate: the tops (grain along x), the end panels (grain upright), the edge banding; `laminate` keeps its name
    # for the props that share it (bookshelf, reception desk, round table) and is now the grain too
    save(match_rgb(laminate_grain(5285, (182, 158, 122)), L4_MEAN["laminate"], "l4lam"), "block/level4/laminate.png")
    save(match_rgb(laminate_grain(5286, (182, 158, 122), "v"), L4_MEAN["laminate"], "l4lam"), "block/level4/laminate-v.png")
    save(laminate_edge(), "block/level4/laminate-edge.png")
    # the break room's round table: a plain flecked laminate (its octagonal top is boxes turned 45 degrees, which
    # would show a grain turning from box to box)
    img = M.noise_hv((180, 158, 124), 3, 5287, S, 2, (16, 8), hue=1.0)
    rng = random.Random(5288)
    for _ in range(70):
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((-0.08, -0.05, 0.06)))
    save(match_rgb(img, L4_MEAN["laminate"]), "block/level4/laminate-fleck.png")
    save(match_rgb(beige_plastic(527, yellow=0.12), L4_MEAN["crt"], "l4crt"), "block/level4/crt.png")
    save(crt_screen(), "block/level4/crt-screen.png")
    save(keyboard_keys(), "block/level4/keys.png")
    save(chair_fabric(), "block/level4/chairfabric.png")
    save(M.noise_hv((36, 37, 40), 2, 5305, S, 3, (16, 8), hue=0.5), "block/level4/chairplastic.png")
    save(filing_paint(), "block/level4/filing.png")
    save(filing_paint(True), "block/level4/filing-top.png")
    red, glow, bottle, panel = vending_textures()
    save(red, "block/level4/vending.png")
    save(glow, "block/level4/vending-glow.png")
    save(bottle, "block/level4/vending-bottle.png")
    save(panel, "block/level4/vending-panel.png")
    body, bottle = cooler_textures()
    save(match_rgb(body, L4_MEAN["cooler"]), "block/level4/cooler.png")
    save(bottle, "block/level4/coolerbottle.png")


# ---------------- Level 5: the Terror Hotel (graphics pass B8) ----------------
#
# Old tones kept: each surface's mean colour is matched to the texture it replaces (L5_MEAN, measured on main before
# B8), and the damask's two reds, the cream and the gilt are the old ones. Structure first: mahogany has grain and
# pores, brass is brushed and tarnished, gilt is burnished on its high points; the wall's mouldings are shaded as
# relief lit from above; the carpets are a short pile with the old patterns dyed into it.

L5_MEAN = {
    "mahogany": (89.8, 45.8, 25.8), "brass": (176.0, 138.0, 60.0), "gilt": (200.7, 159.7, 63.7),
    "wainscot": (79.5, 45.6, 29.4), "frieze": (218.0, 196.2, 160.9),
    "damask": (110.5, 50.4, 17.9), "maroon": (46.1, 12.1, 10.1), "lobby": (177.5, 124.7, 72.1),
    "hotelwood": (70.0, 39.4, 24.9), "cream": (225.9, 209.9, 179.9), "door": (76.0, 42.5, 27.5),
    "crystal": (240.2, 244.2, 253.5),
}
DAMASK_GROUND, DAMASK_MOTIF = (98, 12, 8), (116, 22, 14)
PANEL_CREAM = hexrgb(0xD9C3A0)
GILT = (196, 160, 72)
DOOR_WOOD = (74, 40, 25)
# The red field inside the panel's gilt frame (64 px, inclusive), and the frame's width round it
PANEL_FIELD, FRAME_W = (11, 7, 52, 56), 4


def wood_grain(seed, base, direction="h", figure=1.0, pores=0.4, size=S):
    """(B8) Mahogany or walnut as a material for models and mouldings: one board with no edges or seams (the boxes it
    goes on make the edges), long streaks along the grain, wavy darker grain lines in short runs, open pores (short
    dark dashes along the grain, as mahogany has) and a faint satin sheen. Tileable."""
    img = M.brushed_metal(seed, size=size, base=base, grain=3, direction="h", streak=9 * figure, sheen=3, drift=M.DRIFT)
    w, h = img.size
    wave = M.value_noise((w, h), (w // 2, h // 4), M.sub(seed, "wave"))
    lines = M.value_noise((w, h), (w // 2, 1), M.sub(seed, "lines"))
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = lines[int(y + wave[y][x] * 2.0) % h][x]
            if k > 0.5:  # long, gently wavy grain lines (short ones read as a pattern of arcs)
                px[x, y] = M.rgba(M.lift(px[x, y], -(k - 0.5) * 34 * figure))
    rng = random.Random(M.sub(seed, "pores"))
    for _ in range(int(pores * w * h / 8)):
        x, y = rng.randrange(w), rng.randrange(h)
        for i in range(rng.randint(1, 3)):
            M.touch(img, x + i, y, -0.1)
    return img.transpose(Image.TRANSPOSE) if direction == "v" else img


def brass_metal(seed=5500, base=(176, 138, 60), mean=None):
    """Old brass: brushed, a soft sheen band, tarnish gathering in broad patches."""
    img = M.brushed_metal(seed, base=base, grain=3, direction="h", streak=8, sheen=9, drift=M.DRIFT)
    M.grime(img, 0.1, M.sub(seed, "tarnish"), color=(98, 78, 40), cells=(4, 2), cover=0.45)
    return match_rgb(img, mean or L5_MEAN["brass"])


def gilt_leaf(seed=5510):
    """Gilded wood: the leaf's soft clouding, burnished high points catching the light, tarnish in the hollows. (No
    specks rubbed through to the bole: on a frame tiled down a corridor they read as a row of nail heads.)"""
    img = M.noise_hv(GILT, 4, seed, S, 8, (8, 4), hue=3.0)
    burn = M.fbm((S, S), M.sub(seed, "burnish"), (8, 4))
    px = img.load()
    for y in range(S):
        for x in range(S):
            if burn[y][x] > 0.25:
                px[x, y] = M.rgba(M.lift(px[x, y], (burn[y][x] - 0.25) * 26))
    M.grime(img, 0.2, M.sub(seed, "tarnish"), color=(110, 82, 36), cells=(4, 2), cover=0.4)
    return match_rgb(img, L5_MEAN["gilt"])


def layered_pattern(layers, size=S, k=4, crisp=False):
    """A dyeable pattern (RGBA, transparent where there is none) from layers of (colour, paint): paint(draw, k) fills
    a mask drawn k times larger, which is scaled down, so curves and rings come out smooth (or, `crisp`, cut at half
    cover: whole pixels, as a woven carpet's pattern is). Later layers lie on top."""
    w, h = (size, size) if isinstance(size, int) else size
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for colour, paint in layers:
        m = Image.new("L", (w * k, h * k), 0)
        paint(ImageDraw.Draw(m), k)
        layer = Image.new("RGBA", (w, h), tuple(colour) + (255,))
        m = m.resize((w, h), Image.BOX)
        if crisp:
            m = m.point(lambda a: 255 if a >= 110 else 0)
        layer.putalpha(m)
        out.alpha_composite(layer)
    return out


def damask_print(phase=(0.0, 0.0), N=64):
    """The hotel's red damask over the whole 64 px square (the frame shows the middle of it): a diamond lattice with
    a fleur in every cell in two reds about 10% apart, drawn 4x large and scaled down. `phase` shifts the print, as a
    paperhanger cuts each panel from the roll wherever it falls. Woven: the motif a satin with a faint sheen, the
    ground a matte rib."""
    k = 4
    big = Image.new("RGBA", (N * k, N * k), DAMASK_GROUND + (255,))
    d = ImageDraw.Draw(big)
    cw, ch = 20, 26  # one diamond of the lattice

    def fleur(cx, cy, w, h):
        cx, cy, w, h = cx * k, cy * k, w * k, h * k
        d.polygon([(cx, cy - h * 0.5), (cx + w * 0.17, cy - h * 0.18), (cx + w * 0.1, cy + h * 0.08),
                   (cx, cy + h * 0.14), (cx - w * 0.1, cy + h * 0.08), (cx - w * 0.17, cy - h * 0.18)], fill=DAMASK_MOTIF)
        for sx in (1, -1):  # the two curling side leaves
            d.polygon([(cx + sx * w * 0.08, cy + h * 0.06), (cx + sx * w * 0.3, cy - h * 0.12), (cx + sx * w * 0.5, cy - h * 0.34),
                       (cx + sx * w * 0.52, cy - h * 0.12), (cx + sx * w * 0.4, cy + h * 0.06), (cx + sx * w * 0.2, cy + h * 0.14)], fill=DAMASK_MOTIF)
            d.ellipse([cx + sx * w * 0.42 - w * 0.07, cy - h * 0.4, cx + sx * w * 0.42 + w * 0.07, cy - h * 0.3], fill=DAMASK_MOTIF)
        d.rectangle([cx - w * 0.24, cy + h * 0.14, cx + w * 0.24, cy + h * 0.22], fill=DAMASK_MOTIF)  # the band
        d.polygon([(cx - w * 0.14, cy + h * 0.22), (cx + w * 0.14, cy + h * 0.22), (cx, cy + h * 0.46)], fill=DAMASK_MOTIF)

    ox, oy = 31.5 + phase[0], 31.5 + phase[1]
    for i in range(-4, 5):
        for j in range(-6, 7):
            fleur(ox + i * cw + (cw / 2 if j % 2 else 0), oy + j * ch / 2, cw * 0.56, ch * 0.6)
    for i in range(-7, 8):  # the lattice: lines through the diamonds' side corners
        px0, py0 = ox + cw / 2 + i * cw, oy
        for sgn in (1, -1):
            d.line([((px0 - 5 * cw) * k, (py0 - sgn * 5 * ch) * k), ((px0 + 5 * cw) * k, (py0 + sgn * 5 * ch) * k)],
                   fill=DAMASK_MOTIF, width=k)
    img = big.resize((N, N), Image.LANCZOS)
    px = img.load()
    rng = random.Random(541)
    sheen = M.value_noise((N, N), (32, 16), 5410)
    mid = (M.lum(DAMASK_GROUND) + M.lum(DAMASK_MOTIF)) / 2
    for y in range(N):
        for x in range(N):
            c = px[x, y]
            if M.lum(c) > mid:  # satin: a soft sheen across the motif, its floats running upright
                c = M.lift(c, 2.5 + sheen[y][x] * 3 + (1.0 if x % 2 else -0.5))
            else:  # matte ground: a fine horizontal rib
                c = M.lift(c, 0.8 if y % 2 else -0.8)
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-1.6, 1.6)))
    return img


MOULD = {  # a gilt ogee moulding's profile, outer px first, per member: lit where it faces up (and a little left)
    "t": (0.20, 0.10, -0.04, -0.16), "b": (-0.24, -0.10, 0.04, 0.12),
    "l": (0.12, 0.05, -0.02, -0.10), "r": (-0.16, -0.07, 0.02, 0.08)}


def gilt_frame(img, box, gilt, width=FRAME_W):
    """Paints a raised gilt moulding of `width` px round box (x0, y0, x1, y1 inclusive, the inside of the frame):
    each member shaded across its profile by which way it faces (MOULD), mitred at the corners; the shadow it casts
    on the field under its top member and on the wall under and right of it."""
    x0, y0, x1, y1 = box
    ox0, oy0, ox1, oy1 = x0 - width, y0 - width, x1 + width, y1 + width
    p, g = img.load(), gilt.load()
    for y in range(oy0, oy1 + 1):
        for x in range(ox0, ox1 + 1):
            if x0 <= x <= x1 and y0 <= y <= y1:
                continue
            dist = {"t": y - oy0, "b": oy1 - y, "l": x - ox0, "r": ox1 - x}
            m = min(dist, key=lambda k: (dist[k], "tlbr".index(k)))
            f = MOULD[m][min(width - 1, dist[m]) * 4 // width]
            p[x, y] = M.rgba(M.shade_px(g[x % gilt.width, y % gilt.height], f))
    for x in range(x0, x1 + 1):  # the shadow under the top member, on the field
        M.touch(img, x, y0, -0.18)
        M.touch(img, x, y0 + 1, -0.07)
    for y in range(y0 + 2, y1 + 1):
        M.touch(img, x0, y, -0.08)
    for x in range(ox0 + 1, ox1 + 2):  # and on the wall under the frame and to its right
        M.touch(img, x, oy1 + 1, -0.14)
        M.touch(img, x, oy1 + 2, -0.05)
    for y in range(oy0 + 1, oy1 + 2):
        M.touch(img, ox1 + 1, y, -0.1)
        M.touch(img, ox1 + 2, y, -0.04)
    return img


def hotel_panel(alt=0):
    """The hotel's damask panel, at 64 px: cream plaster round a gilt-framed panel of red damask (the old layout,
    tones and print). The frame is a moulding shaded as relief and casts its shadow; the plaster is plain and
    seamless, so a corridor's walls run on from block to block. Versions (the blocktype lists them): the print cut
    at three different places of the roll, and (`alt` 3, one block in eight) an old water mark down the damask."""
    N = 64
    img = M.plaster(5620, size=N, base=PANEL_CREAM, grain=2, mottle=3, roller=0.4, bumps=0.0)
    phase = ((0.0, 0.0), (10.0, 0.0), (5.0, 6.5), (0.0, 0.0))[alt]
    field = damask_print(phase, N)
    if alt == 3:
        M.stain(field, 5631, radius=10, color=(70, 18, 10), strength=0.3, at=(36, 44), ring=0.6)
    x0, y0, x1, y1 = PANEL_FIELD
    img.paste(field.crop((x0, y0, x1 + 1, y1 + 1)), (x0, y0))
    gilt = gilt_leaf()
    return gilt_frame(img, PANEL_FIELD, gilt)


def wainscot(alt=0):
    """The mahogany wainscot (32 px): a moulded cap (the chair rail), a top rail, a raised and fielded panel in a
    recess, a bottom rail and a skirting with a dark toe; the stiles are split across the block's edges (2 px each
    side), so neighbouring blocks make one 4 px stile and the run reads as panelling, not as boxes. The rails have
    grain along them, the stiles and panels up them. Old tone. One version: a second grain read as a
    patchwork of lighter and darker blocks."""
    seed = 5600 + alt * 10
    vt = wood_grain(seed, (82, 47, 30), "v", figure=0.6, pores=0.15)
    ht = wood_grain(seed + 3, (82, 47, 30), "h", figure=0.7, pores=0.15)
    img = Image.new("RGBA", (S, S))
    p, v, h = img.load(), vt.load(), ht.load()
    shade = [[0.0] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            stile = (x < 2 or x >= 30) and 3 <= y <= 27
            panel = 2 <= x <= 29 and 7 <= y <= 24
            upright = stile or panel
            p[x, y] = (v if upright else h)[x, y]
    for x in range(S):  # the cap: a rounded top lit, its underside dark, its shadow on the rail
        for y, f in ((0, 0.18), (1, 0.05), (2, -0.2), (3, -0.12), (27, -0.07), (28, 0.15), (29, 0.02), (30, -0.05), (31, -0.22)):
            shade[y][x] += f
    for y in range(7, 25):  # the panel's recess: its top and left walls in shadow, bottom and right lit
        for x in range(2, 30):
            if y == 7 or x == 2:
                shade[y][x] += -0.18
            elif y == 24 or x == 29:
                shade[y][x] += 0.09
            elif 4 <= x <= 27 and 9 <= y <= 22:  # the raised field's bevel, mitred
                dist = {"t": y - 9, "b": 22 - y, "l": x - 4, "r": 27 - x}
                m = min(dist, key=lambda k: (dist[k], "tlbr".index(k)))
                if dist[m] < 2:
                    shade[y][x] += {"t": (0.14, 0.06), "b": (-0.16, -0.07), "l": (0.08, 0.03), "r": (-0.12, -0.05)}[m][dist[m]]
            else:
                shade[y][x] += -0.03
    for y in range(S):
        for x in range(S):
            if shade[y][x]:
                p[x, y] = M.rgba(M.shade_px(p[x, y], shade[y][x]))
    M.grime(img, 0.08, M.sub(seed, "dust"), color=(54, 40, 30), cells=(4, 2), bias="bottom", cover=0.4)
    return match_rgb(img, L5_MEAN["wainscot"], "l5wainscot")


def frieze():
    """The cream frieze over the damask (32 px): plain plaster, and at its top a picture-rail moulding shaded as
    relief: a shadow line where it meets what is above, a lit cove, a fillet, its dark underside and the soft shadow
    it casts on the wall. In the grand rooms (two frieze blocks high) it reads as a picture rail."""
    img = M.plaster(5620, base=PANEL_CREAM, grain=2, mottle=3, roller=0.4, bumps=0.0)
    p = img.load()
    for y, f, k in ((0, -0.22, 0.3), (1, 0.13, 0.6), (2, 0.08, 0.6), (3, 0.02, 0.6), (4, 0.10, 0.5), (5, -0.17, 0.4),
                    (6, -0.08, 0), (7, -0.03, 0)):
        for x in range(S):
            c = M.mix(p[x, y], (236, 220, 188), k)
            p[x, y] = M.rgba(M.shade_px(c, f))
    return match_rgb(img, L5_MEAN["frieze"], "l5frieze")


def hotel_ceiling():
    """The corridors' cream ceiling: plaster with the faintest clouding."""
    img = M.plaster(5640, base=(226, 210, 180), grain=2, mottle=2, roller=0.3, bumps=0.0)
    return match_rgb(img, L5_MEAN["cream"], "l5cream")


def hotel_pile(seed, base, pile=4):
    """The hotel's carpets: a short, even cut pile (B6's runner lesson: a long nap reads as red static at range), two
    tones of yarn."""
    return M.carpet(seed, base=base, tone2=M.hue_shift(M.lift(base, -8), 2), mix2=0.35, pile=pile, grain=2, mottle=2)


def _medallion():
    """The corridor carpet's medallions as the old ones (a 1 px ring and a small heart, drawn at 1:1 so they come out as
    clean pixel octagons), but an even number of pixels across and centred on the half pixel (7.5, 23.5), so a block
    turned by the blocktype keeps every ring where it was (the old odd-sized rings would jump a pixel). (Round 2) A
    small gold rosette in each gap between four medallions, so it reads as a woven pattern rather than a grid of dots."""
    def ring(d, k):
        for cx, cy in ((2, 2), (18, 2), (2, 18), (18, 18)):
            d.ellipse([cx, cy, cx + 11, cy + 11], outline=255)

    def dot(d, k):
        for cx, cy in ((6, 6), (22, 6), (6, 22), (22, 22)):
            d.ellipse([cx - 0.5, cy - 0.5, cx + 3.5, cy + 3.5], fill=255)
    def rosette(d, k):  # (round 2) a small gold rosette in the middle of each gap between four medallions
        for cx in (-2, 14, 30):
            for cy in (-2, 14, 30):
                d.rectangle([cx + 1, cy, cx + 2, cy + 3], fill=255)
                d.rectangle([cx, cy + 1, cx + 3, cy + 2], fill=255)
    return [((196, 150, 60), ring), ((160, 40, 20), dot), ((186, 140, 56), rosette)]


def hotel_carpet(kind, alt=0):
    """The hotel's carpets on a short pile, the old patterns dyed in (so they keep the pile), a little dingy. Three
    versions of each share one ground and are turned at random by the blocktype (matlib.turn_safe), so they meet
    without a seam; the patterns are four-fold symmetric, so a turned block keeps the pattern's rhythm.
    - damask: the corridors' red-brown carpet with its gold rings and red centres, on every half block as before;
    - maroon: the ballroom's plain near-black maroon;
    - lobby: tan with its red border line."""
    base = {"damask": (100, 42, 14), "maroon": (48, 13, 10), "lobby": (181, 133, 76)}[kind]
    seed = {"damask": 5660, "maroon": 5670, "lobby": 5680}[kind] + alt
    img = hotel_pile(seed, base, pile=2 if kind == "maroon" else 4)  # (round 2) the dark maroon's pile calmer: it read coarse
    M.turn_safe(img, M.noise_hv(base, 0, seed - alt, S, 2, (16,), hue=0), band=8, keep=0.5)
    if kind == "damask":
        M.dye(img, layered_pattern(_medallion(), k=1), base)
    elif kind == "lobby":
        def border(d, k):
            d.rectangle([2 * k, 2 * k, 30 * k - 1, 30 * k - 1], fill=255)
            d.rectangle([3.2 * k, 3.2 * k, 28.8 * k - 1, 28.8 * k - 1], fill=0)
        M.dye(img, layered_pattern([((150, 40, 24), border)], crisp=True), base)
    dingy(img, seed, dull=0.05, dim=1.0, grime=0.05 if kind != "maroon" else 0.03, flecks=6 if kind != "maroon" else 2)
    return match_rgb(img, L5_MEAN[kind], "l5carpet-" + kind)


def hotel_floorboards(alt=0):
    """The dining rooms' dark walnut floor: four boards of 8 px to the block (the old 6 px lines did not tile), each
    its own shade with grain and a dark gap; the versions share every board's shade and grain and differ only in the
    one butt joint each has (none in the first), in a different board and place, so the floor mixes without a seam and
    no joint stands at the same place block after block. Not turned (the boards keep their direction)."""
    img = M.wood_planks(5690, base=(78, 44, 28), planks=4, direction="h", grain=3, contrast=0.8, per_plank=6,
                        joints=0.0, gap=(30, 18, 12))
    p = img.load()
    if alt:
        board, jx = ((0, 0), (2, 21), (1, 9), (3, 27), (0, 15))[alt]
        for y in range(board * 8, board * 8 + 7):
            p[jx, y] = M.rgba(M.lift((30, 18, 12), 0))
            M.touch(img, jx + 1, y, 0.06)
    return match_rgb(img, L5_MEAN["hotelwood"], "l5wood")


def door_plate(number, tarnish=0.12, size=(32, 16)):
    """A room door's brass number plate (the plate is a box on the door; this is its face): brushed brass, its edge
    bevelled, the number engraved: dark in the cut, lit on the cut's lower right wall."""
    img = M.brushed_metal(5710, size=size, base=(206, 170, 84), grain=3, direction="h", streak=7, sheen=10, drift=M.DRIFT)
    M.grime(img, tarnish, 5711, color=(110, 84, 36), cells=(8, 4), cover=0.5)
    w, h = size
    M.bevel(img, (0, 0, w, h), 1, 0.22)
    if number:  # tall, narrow numerals (a 5 x 7 face drawn twice as tall), centred
        ink = Image.new("RGBA", size, (0, 0, 0, 0))
        x0, tall = (w - (len(number) * 6 - 1)) // 2, (h - 2) // 7
        top = (h - 7 * tall) // 2
        for i, ch in enumerate(number):
            for j, row in enumerate(PLACARD_FONT[ch]):
                for k, bit in enumerate(row):
                    if bit == "1":
                        for t in range(tall):
                            ink.putpixel((x0 + i * 6 + k, top + j * tall + t), (255, 255, 255, 255))
        a, p = ink.load(), img.load()
        cut = {(x, y) for y in range(h) for x in range(w) if a[x, y][3] > 110}
        for (x, y) in cut:
            p[x, y] = M.rgba(M.mix(p[x, y], (44, 26, 10), 0.8))
        for (x, y) in cut:
            if (x + 1, y + 1) not in cut and x + 1 < w and y + 1 < h:
                M.touch(img, x + 1, y + 1, 0.18)
    return img


def oil_portrait(kind):
    """(B8) The corridor portraits: dark, unsettling oils in yellowed varnish, the eyes lost in shadow. Print 0 is the
    old one (a man in black); the others are listed beside it as texture alternates, so a corridor of portraits is
    not one face over and over: a woman in a dark gown with a high collar, an old man with a grey beard, a pale
    child."""
    if kind == 0:
        return portrait(557)
    rng = random.Random(5720 + kind)
    bg = {1: ((40, 46, 32), (20, 22, 16)), 2: ((58, 40, 26), (26, 20, 14)), 3: ((44, 36, 40), (20, 16, 20))}[kind]
    img = texlib.vertical_gradient(*bg)
    px = img.load()
    fy, fr = {1: (13, (4.6, 6.2)), 2: (12, (5.2, 6.6)), 3: (15, (4.2, 5.0))}[kind]
    coat = {1: (24, 16, 22), 2: (30, 24, 20), 3: (40, 34, 30)}[kind]
    skin = {1: (190, 160, 136), 2: (168, 136, 110), 3: (200, 184, 168)}[kind]
    for y in range(S):
        for x in range(S):
            r, g, b, _ = px[x, y]
            n = rng.uniform(-5, 5)
            body = y > fy + 7 and abs(x - 16) < 5 + (y - fy - 7) * (1.1 if kind == 1 else 0.9)
            if body:
                r, g, b = coat
                if kind == 1 and y < fy + 11 and abs(x - 16) < 3:
                    r, g, b = 150, 138, 116  # the high lace collar
                if kind == 3 and abs(x - 16) < 2 and y < fy + 10:
                    r, g, b = 168, 160, 146  # a pinafore's bib
            dx, dy = (x - 16) / fr[0], (y - fy) / fr[1]
            if dx * dx + dy * dy < 1:
                light = 0.5 + 0.5 * max(0.0, -dx)
                r, g, b = (int(c * light) for c in skin)
                if fy - 2 <= y <= fy - 1 and (13 <= x <= 14 or 18 <= x <= 19):
                    r, g, b = 34, 26, 22  # the eyes, in shadow
                if kind == 2 and y > fy + 2 and abs(dx) < 0.9:  # the grey beard over the chin
                    r, g, b = (int(c * (0.7 + 0.3 * light)) for c in (150, 146, 136))
            hair = 0.75 < dx * dx + dy * dy < 1.35 and y < fy - 1
            if kind == 1 and 0.8 < dx * dx + dy * dy < 1.6 and y < fy + 4:
                hair = True  # hair drawn down over the ears
            if hair:
                r, g, b = {1: (30, 22, 18), 2: (118, 114, 106), 3: (70, 50, 30)}[kind]
            px[x, y] = (clamp(r + n), clamp(g + n), clamp(b + n), 255)
    blotch(img, (16, 14), 14, (120, 96, 40), 0.18, 5730 + kind)  # the varnish, yellowed toward the middle
    return img


PLACARD_FONT = {
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "V": ("10001", "10001", "10001", "10001", "01010", "01010", "00100"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "0": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
}


def beverly_placard():
    """The Beverly Room's placard (the face of a plate on its wall, 64 x 32): nickel silver, brushed, its edge
    bevelled, the name engraved in three lines."""
    w, h = 64, 32
    img = M.brushed_metal(5740, size=(w, h), base=(184, 188, 192), grain=3, direction="h", streak=6, sheen=10, drift=0.1)
    M.grime(img, 0.12, 5741, color=(120, 116, 104), cells=(8, 4), cover=0.5)
    M.bevel(img, (0, 0, w, h), 1, 0.2)
    rows = []  # the engraved letters, a 5 x 7 pixel face (the font scaled down lost ROOM's O's), BEVERLY drawn twice as tall
    for word, top, tall in (("THE", 1, 1), ("BEVERLY", 9, 2), ("ROOM", 24, 1)):
        x0 = (w - (len(word) * 6 - 1)) // 2
        for i, ch in enumerate(word):
            for j, row in enumerate(PLACARD_FONT[ch]):
                for k, bit in enumerate(row):
                    if bit == "1":
                        rows += [(x0 + i * 6 + k, top + j * tall + t) for t in range(tall)]
    ink = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for (x, y) in rows:
        ink.putpixel((x, y), (255, 255, 255, 255))
    a, p = ink.load(), img.load()
    cut = {(x, y) for y in range(h) for x in range(w) if a[x, y][3] > 110}
    for (x, y) in cut:
        p[x, y] = M.rgba(M.mix(p[x, y], (40, 30, 20), 0.85))
    for (x, y) in cut:
        if (x + 1, y + 1) not in cut and x + 1 < w and y + 1 < h:
            M.touch(img, x + 1, y + 1, 0.16)
    return img


def crystal_glass():
    """The chandelier's cut crystal: pale, with bright and shaded facets in small diamonds."""
    img = M.noise_hv((232, 238, 250), 3, 5750, S, 2, (8, 4), hue=1.0)
    for y in range(S):
        for x in range(S):
            u, v = (x + y) % 16, (x - y) % 16
            f = 0.08 if (u < 8) != (v < 8) else -0.05
            if u == 0 or v == 0:
                f = 0.12
            M.touch(img, x, y, f, 0.05)
    return match_rgb(img, L5_MEAN["crystal"], "l5crystal")


def palm_textures_b14():
    """(B14) The potted palm's materials (it stands in Level 5's halls and Level Fun's lobbies). palmleaf: the fronds'
    blades, leaflets as long strips along the length with a lit edge and a dark gap between them, a paler midrib down
    the middle; pot: glazed terracotta with a thrown rim band and a few throwing rings; palmtrunk: the fibrous stub
    rings of a palm's trunk; potsoil: dark potting soil with bits of bark."""
    rng = random.Random(5660)
    img = M.noise_hv((62, 106, 44), 3, 5661, mottle=5, cells=(16, 8))
    p = img.load()
    for y in range(32):
        for x in range(32):
            d = abs(y - 15.5)
            if d < 1.2:
                p[x, y] = M.rgba(M.lift((122, 150, 74), rng.uniform(-3, 3)))  # the midrib
            elif (x + int(d * 1.6)) % 4 == 0:
                p[x, y] = M.rgba(M.lift(p[x, y], -22))  # the gaps between leaflets, slanting out from the rib
            elif (x + int(d * 1.6)) % 4 == 1:
                p[x, y] = M.rgba(M.lift(p[x, y], 10))
    save(img, "block/level5/palmleaf.png")
    img = M.noise_hv((150, 84, 52), 3, 5671, mottle=5, cells=(16, 8))
    for y in (6, 7, 13, 21):
        for x in range(32):
            M.touch(img, x, y, -0.08 if y != 7 else 0.06)
    M.hue_jitter(img, 2, 5672)
    save(img, "block/level5/pot.png")
    img = M.noise_hv((112, 84, 56), 3, 5681, mottle=4, cells=(16, 8))
    for y in range(32):
        k = y % 4
        for x in range(32):
            if k == 0:
                M.touch(img, x, y, -0.22)
            elif k == 1:
                M.touch(img, x, y, 0.12)
            if (x * 7 + y * 3) % 11 == 0:
                M.touch(img, x, y, -0.1)
    save(img, "block/level5/palmtrunk.png")
    img = M.noise_hv((58, 42, 30), 5, 5691, mottle=5, cells=(8, 4))
    for _ in range(30):
        x, y = rng.randrange(32), rng.randrange(32)
        img.putpixel((x, y), M.rgba(M.lift((120, 86, 52), rng.uniform(-10, 10))))
    save(img, "block/level5/potsoil.png")


def boiler_textures():
    """(B6) The boiler's shell: riveted plates in the old brown, gone to rust at the seams, sooty and grimy; its iron
    bands and plinth; the cast iron firebox door, sooted round its edges. The rivets sit along the plates' seams (the
    texture's edges: each lift and face of the model is a plate) rather than in a grid over everything."""
    shell = M.riveted_plate(5301, base=(108, 76, 46), grain=4, mottle=7, pitch=4, layout="edges", rust_amount=0.22)
    M.grime(shell, 0.22, 5302, color=(52, 44, 36), cover=0.55)
    M.drips(shell, 3, 5303, color=(70, 44, 28), length=(6, 16), strength=0.3)
    save(shell, "block/level5/boiler.png")
    band = M.painted_metal(5305, base=(58, 52, 48), grain=4, mottle=5, panel=False, chips=3, under=(96, 90, 84))
    M.rust(band, 0.25, 5306, color=(120, 68, 38), dark=(70, 44, 30))
    save(band, "block/level5/boiler-band.png")
    door = M.noise_hv((50, 47, 44), 4, 5308, S, 6)
    M.grime(door, 0.3, 5309, color=(26, 24, 22), cover=0.6)
    M.ao_border(door, 3, 0.2)
    save(door, "block/level5/boiler-door.png")


BOILER_IRON = (82, 75, 69)   # (D4) the shell's iron: darker and cooler than B6's clay brown (102, 70, 43)
BOILER_RUST = (124, 66, 36)


def boiler_textures_d4():
    """(D4) The boiler re-done after B8 graded it C in the hotel's boiler bays (a clay-orange shell at a low density).
    `boiler.png` is now riveted iron plate for gen_shapes.boiler's facet plates: two plates side by side, 16 px each,
    each plate's left edge a lap seam (a dark groove, the overlapping edge lit) with a row of rivet heads beside it,
    so every corner of the octagon reads as a riveted seam; the shape shows each facet as one 16 px plate at about one
    and a half times the block's density, at a seed-chosen height. The iron is a dark, cool grey with a little warmth
    (vanilla's plate iron is 105, 93, 86); rust only in runs down from some rivets and from the seams, soot on the
    upper half. `boiler-strap.png` is the hoop over each course joint: strap iron with one row of rivets, the pattern
    repeating every 4 px down so any 2-unit window shows one strap (lit top edge, rivets, shadowed foot).
    `boiler-flue.png` the flue's sooty iron, rust runs from its joints. Revert: drop the call in level5_textures."""
    rng = random.Random(5320)
    shell = M.noise_hv(BOILER_IRON, 4, 5321, mottle=6, cells=(16, 8), hue=1.5)
    px = shell.load()
    for col in range(2):
        x0 = col * 16
        tone = (-3, 3)[col]
        for y in range(32):
            for x in range(x0, x0 + 16):
                px[x, y] = M.rgba(M.lift(px[x, y], tone))
        # the lap: the plate on the left overlaps this one; its edge is lit, the groove under it dark
        for y in range(32):
            M.touch(shell, x0, y, -0.32)
            M.touch(shell, x0 + 1, y, 0.16)
            M.touch(shell, x0 + 2, y, 0.05)
        for y in range(1, 32, 4):
            M.screw(shell, x0 + 3, y, slot=False)
    # soot over the top half (the fire and the flue), wrapped faintly into the bottom
    M.grime(shell, 0.2, 5322, color=(40, 36, 34), cover=0.5)
    # rust runs from a few rivets and from the seams: thin, fading, not patches
    for col in range(2):
        x0 = col * 16
        for k in range(3):
            y0 = 1 + 4 * rng.randrange(8)
            L = rng.randint(5, 13)
            x = x0 + 3 + rng.choice((0, 1))
            for i in range(L):
                t = (1 - i / L) ** 0.8 * 0.55
                y = (y0 + 2 + i) % 32
                c = shell.getpixel((x % 32, y))
                shell.putpixel((x % 32, y), M.rgba(M.mix(c[:3], BOILER_RUST, t)))
                if i < L // 2:
                    c = shell.getpixel(((x + 1) % 32, y))
                    shell.putpixel(((x + 1) % 32, y), M.rgba(M.mix(c[:3], BOILER_RUST, t * 0.4)))
                if rng.random() < 0.12:
                    x += rng.choice((-1, 1))
        # a longer run down the seam groove of one plate
        if col == 1:
            for i in range(14):
                y = (6 + i) % 32
                c = shell.getpixel((x0 + 1, y))
                shell.putpixel((x0 + 1, y), M.rgba(M.mix(c[:3], BOILER_RUST, 0.45 * (1 - i / 14))))
    save(match_rgb(shell, (70, 62, 56)), "block/level5/boiler.png")  # (round 2) darker than B6's (102, 70, 43)

    strap = M.noise_hv((60, 55, 51), 3, 5325, mottle=4, cells=(16, 8), hue=1.0)
    for y in range(32):
        r = y % 4
        for x in range(32):
            if r == 0:
                M.touch(strap, x, y, 0.18)
            elif r == 3:
                M.touch(strap, x, y, -0.22)
    for y in range(0, 32, 4):
        for x in range(1, 32, 5):
            M.touch(strap, x, y + 1, 0.34)
            M.touch(strap, x + 1, y + 1, 0.12)
            M.touch(strap, x, y + 2, -0.04)
            M.touch(strap, x + 1, y + 2, -0.2)
    M.rust(strap, 0.12, 5326, color=(116, 64, 36), dark=(70, 44, 30))
    save(strap, "block/level5/boiler-strap.png")

    flue = M.noise_hv((66, 60, 56), 4, 5328, mottle=6, cells=(16, 8), hue=1.2)
    M.grime(flue, 0.35, 5329, color=(30, 28, 27), cover=0.6, bias="top")
    M.emboss_lines(flue, xs=(), ys=(15,), strength=0.2)
    M.drips(flue, 3, 5330, color=BOILER_RUST, length=(5, 12), strength=0.35, start=16)
    save(flue, "block/level5/boiler-flue.png")


def level5_textures():
    # (B8) Hotel walls: the damask panel cut from the roll at three places, and a fourth with an old water mark (one
    # block in eight, gen_blocktypes); the wainscot; the frieze with its picture rail
    for alt, v in ((0, ""), (1, "-2"), (2, "-3"), (3, "-4")):
        save(hotel_panel(alt), f"block/level5/hotelwall-panel{v}.png")
    save(wainscot(0), "block/level5/hotelwall-wainscot.png")
    save(frieze(), "block/level5/hotelwall-frieze.png")

    # (B8) Carpets on a short pile, three versions each (turned at random); the walnut floor in five versions
    for kind in ("damask", "maroon", "lobby"):
        for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
            save(hotel_carpet(kind, alt), f"block/level5/hotelcarpet-{kind}{v}.png")
    for alt in range(5):
        save(hotel_floorboards(alt), "block/level5/hotelwood" + (f"-{alt + 1}" if alt else "") + ".png")
    save(hotel_ceiling(), "block/level5/hotelceiling-cream.png")
    # The old painted beam ceiling (rooms generated before the beams were modelled)
    img = noise_fill(hexrgb(0x9E5720), 6, 548)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 6], fill=(221, 163, 65, 255))
    d.rectangle([0, 25, S - 1, S - 1], fill=(78, 23, 6, 255))
    for x in range(4, S, 8):
        d.rectangle([x, 10, x + 3, 20], fill=(180, 60, 30, 255))
    save(img, "block/level5/hotelceiling-beams.png")
    # Red faux marble (the lobby columns): deep oxblood with pale, wandering veins
    save(texlib.marble((150, 52, 34), (214, 150, 118), 549, mottle=0.12), "block/level5/marble.png")
    img = noise_fill(hexrgb(0x8C6E48), 9, 551)
    blotch(img, (16, 28), 12, (60, 44, 26), 0.5, 552)
    save(img, "block/level5/plaster.png")

    # (B8) The guest-room doors are geometry now (gen_shapes.hotel_door): the leaf's wood (grain up it, and along the
    # rails), the casing, a near-black for the keyhole, and each door's brass number plate as the face of a plate.
    # Consecutive numbers: odd doors down one side of a corridor, even down the other; then (layout 5) a blank plate
    # for the Beverly Room's doors, and the odd 666 (its brass a little more tarnished)
    save(match_rgb(wood_grain(5700, DOOR_WOOD, "v"), L5_MEAN["door"], "l5door"), "block/level5/hoteldoor-wood.png")
    save(match_rgb(wood_grain(5701, DOOR_WOOD, "h"), L5_MEAN["door"]), "block/level5/hoteldoor-rail.png")
    save(wood_grain(5702, (98, 60, 40), "v"), "block/level5/hoteldoor-casing.png")
    save(M.noise_hv((26, 16, 10), 2, 5703, S, 2), "block/level5/hoteldoor-dark.png")
    for i, number in enumerate(("201", "202", "203", "204", "205", "206", "207", "208", "", "666")):
        save(door_plate(number, 0.3 if number == "666" else 0.12), f"block/level5/hoteldoor-plate{i}.png")
    for part in ("lower", "upper"):
        img = Image.new("RGBA", (S, S), (40, 24, 14, 255))
        d = ImageDraw.Draw(img)
        for k in range(-S, S, 6):  # copper lattice
            d.line([k, 0, k + S, S], fill=(184, 115, 51, 255))
            d.line([k + S, 0, k, S], fill=(184, 115, 51, 255))
        d.rectangle([0, 0, S - 1, S - 1], outline=(150, 90, 40, 255), width=2)
        save(img, f"block/level5/cagedoor-{part}.png")
    img = noise_fill(hexrgb(0xD9C3A0), 4, 555)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 9, 28, 22], fill=(30, 30, 30, 255))
    text_img(img, "STAFF", (3, 9, 29, 16), (230, 200, 120, 255), 6)
    text_img(img, "ONLY", (3, 15, 29, 22), (230, 200, 120, 255), 6)
    save(img, "block/level5/staffsign.png")
    save(beverly_placard(), "block/level5/beverly.png")
    # (B8) Four portraits, listed as alternates on the portrait fixture
    for k, v in ((0, ""), (1, "-2"), (2, "-3"), (3, "-4")):
        save(oil_portrait(k), f"block/level5/portrait{v}.png")
    # (B8) The shared materials: gilt, brass, mahogany and crystal have structure now (old means kept)
    save(gilt_leaf(), "block/level5/gilt.png")
    save(brass_metal(), "block/level5/brass.png")
    save(noise_fill(hexrgb(0xFFF0C8), 3, 560), "block/level5/domeglass.png")
    save(crystal_glass(), "block/level5/crystal.png")
    save(match_rgb(wood_grain(5650, (90, 46, 26), "h"), L5_MEAN["mahogany"]), "block/level5/mahogany.png")
    save(noise_fill(hexrgb(0xEDE8DC), 3, 563), "block/level5/linen.png")
    save(noise_fill(hexrgb(0x7A1A14), 5, 564), "block/level5/blanket.png")
    save(noise_fill(hexrgb(0x6E1420), 6, 565), "block/level5/velvet.png")
    palm_textures_b14()  # (B14) the potted palm: leaf, pot, trunk and soil
    save(noise_fill(hexrgb(0x1E5A30), 5, 568), "block/level5/felt.png")
    save(noise_fill(hexrgb(0xEEE6D0), 3, 569), "block/level5/mahjong.png")
    boiler_textures()
    boiler_textures_d4()  # (D4) riveted iron plate, the strap and the flue
    img = noise_fill(hexrgb(0xFF8A2A), 18, 571)
    save(img, "block/level5/fire.png")
    save(noise_fill(hexrgb(0xE8C890), 4, 572), "block/level5/lampshade.png")


def level_textures():
    props_textures()
    level3_textures()
    level4_textures()
    level5_textures()
    for k in ("plain", "wet", "dark"):
        for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
            save(concrete_floor(k, alt), f"block/level1/concretefloor-{k}{v}.png")
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        save(concrete_wall(False, alt), f"block/level1/concretewall-plain{v}.png")
        save(concrete_ceiling(alt), f"block/level1/concreteceiling{v}.png")
    save(concrete_wall(True), "block/level1/concretewall-damaged.png")
    save(pillar(None), "block/level1/concretepillar-plain.png")
    for letter in "abcdef":
        save(pillar(letter), f"block/level1/concretepillar-{letter}.png")
    save(pillar_light(), "block/level1/pillarlight.png")
    save(exit_sign(), "block/level1/exitsign.png")
    save(crate(1), "block/level1/crate-top.png")
    save(crate(0), "block/level1/crate-side.png")
    # The plain wall as it was before B5 (D1: the user's choice), the brick from matlib (B5)
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):  # three versions, one shared ground, turned at random
        save(tunnel_plain(alt), f"block/level2/tunnelwall-plain{v}.png")
    save(tunnel_brick(), "block/level2/tunnelwall-brick.png")
    save(tunnel_wall("machinery"), "block/level2/tunnelwall-machinery.png")
    cabinet_textures()
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        save(tunnel_ceiling(alt), f"block/level2/tunnelceiling{v}.png")
    save(pipe_tex("rust"), "block/level2/pipe-rust.png")
    save(pipe_tex("lagging"), "block/level2/pipe-lagging.png")
    save(pipe_tex("red"), "block/level2/pipe-red.png")
    save(pipe_tex("tar"), "block/level3/pipe-tar.png")
    save(wall_pipe_tex("rust"), "block/level2/wallpipe-rust.png")
    save(wall_pipe_tex("lagging"), "block/level2/wallpipe-lagging.png")
    save(wall_pipe_flange(), "block/level2/wallpipe-flange.png")
    parking_textures()
    save(drum(1), "block/level2/oildrum-top.png")
    save(drum(0), "block/level2/oildrum-side.png")


# ---------------- Items (16x16 atlases, layout matches the shapes) ----------------

def almond_water():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 7, 15], fill=(236, 228, 205, 255))
    d.rectangle([0, 5, 7, 10], fill=(196, 160, 104, 255))
    d.line([0, 7, 7, 7], fill=(120, 84, 44, 255))
    d.line([1, 0, 1, 15], fill=(250, 248, 240, 255))
    d.rectangle([8, 0, 11, 3], fill=(225, 232, 236, 255))
    d.rectangle([12, 0, 15, 3], fill=(60, 110, 170, 255))
    d.rectangle([8, 8, 15, 15], fill=(236, 228, 205, 255))
    return img


def crackers():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 11], fill=(196, 52, 40, 255))
    d.rectangle([3, 3, 12, 8], fill=(232, 196, 120, 255))
    for x in (5, 8, 11):
        d.point((x, 5), fill=(170, 130, 70, 255))
    d.rectangle([0, 12, 15, 15], fill=(170, 40, 32, 255))
    return img


def canned_beans():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 15, 11], fill=(176, 180, 186, 255))
    d.rectangle([0, 3, 15, 8], fill=(214, 120, 40, 255))
    d.rectangle([5, 4, 10, 7], fill=(150, 70, 30, 255))
    d.rectangle([0, 12, 15, 15], fill=(150, 154, 160, 255))
    return img


# ---------------- Mod icon ----------------

def mod_icon():
    s = 128
    img = Image.new("RGBA", (s, s), (40, 36, 20, 255))
    d = ImageDraw.Draw(img)
    vp = (64, 60)
    d.polygon([(0, 0), (s, 0), vp], fill=hexrgb(0xD6CFA6))
    d.polygon([(0, s), (s, s), vp], fill=hexrgb(0xA8956A))
    d.polygon([(0, 0), (0, s), vp], fill=hexrgb(0xD7D48A))
    d.polygon([(s, 0), (s, s), vp], fill=hexrgb(0xC4C07C))
    for t in (0.0, 0.45, 0.7):
        y = int(t * vp[1])
        half = int((1 - t) * 18)
        d.rectangle([64 - half, y + 2, 64 + half, y + 4 + int((1 - t) * 4)], fill=(255, 253, 235, 255))
    d.rectangle([56, 48, 72, 72], fill=(30, 26, 14, 255))
    return img


if __name__ == "__main__":
    wallpapers()
    for alt, v in ((0, ""), (1, "-2")):
        for kind in ("normal", "stained", "soaked"):
            save(carpet(kind, alt), f"block/carpet-{kind}{v}.png")
        save(carpet_threadbare(alt), f"block/carpet-threadbare{v}.png")
    salvage_items()
    pottery_items()
    save(ceiling_tile(), "block/ceilingtile.png")
    save(ceiling_tile(8), "block/ceilingtile2.png")
    save(ceiling_tile(9), "block/ceilingtile3.png")
    save(ceiling_tile(11, stain=True), "block/ceilingtile-stain.png")
    save(ceiling_tile(12, stain=True), "block/ceilingtile-stain2.png")
    save(ceiling_side(), "block/ceilingtile-side.png")
    for st in ("on", "off", "dim", "red"):
        save(troffer(st), f"block/fluorescentlight-{st}.png")
    save(troffer_side(), "block/fluorescentlight-side.png")  # (D4) the housing's edge on the troffer's sides
    save(concrete(), "block/concrete.png")
    save(concrete(1), "block/concrete2.png")
    save(concrete(2), "block/concrete3.png")
    save(box(True), "block/supplybox-top.png")
    save(box(False), "block/supplybox-side.png")
    for name, img in zip(("side", "end", "top"), supply_box_faces()):
        save(img, f"block/supplybox-box-{name}.png")
    level_textures()
    save(almond_water(), "item/almondwater.png")
    save(crackers(), "item/crackers.png")
    save(canned_beans(), "item/cannedbeans.png")
    mod_icon().save(os.path.join(ROOT, "modicon.png"))
    print("textures written")
