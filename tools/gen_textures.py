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


def motif_chevron(seed, chevron=CHEVRON_PRINT, bead=BEAD, wear=0.03):
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
                px[x0, y] = bead + (_ink(rng, wear, BEAD_ALPHA),)  # beaded / dashed line
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


PATTERNS = {"stripped": pattern_stripped, "chevron": pattern_chevron, "dotted": pattern_dotted, "cream": pattern_cream, "manila": pattern_manila,
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


def damp(img, seed, part="upper", stain_c=(176, 150, 86)):
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
        M.touch(img, 16, y, -0.16 * (1 - k / L))
        M.touch(img, 17, y, 0.08 * (1 - k / L))
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
                    save(damp(img, 300 + i * 10 + len(part), part, stain_c), f"block/wallpaper/{name}-{part}-damp.png")
    # The arch soffits and risers: painted plaster in the pale paper's colour, without the print
    save(M.plaster(61, base=(232, 224, 190), grain=3, mottle=6, roller=0.35), "block/wallpaper/cream-soffit.png")


# ---------------- Floor, ceiling, lights ----------------

CARPET = hexrgb(0xA8956A)  # the beige of Level 0's carpet (lore: keep)


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
    return img


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
    return img


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


def troffer(state):
    """matlib.troffer_lens, then (B3) the lens of a lit panel pulled 35% toward its glow colour so it reads as emissive,
    and a dark 1 px gap between the housing frame and the lens, painting the recess (the troffer stays a cube: see
    gen_l0_walls.troffer for the shape that was tried)."""
    lens, glow, lit = TROFFER[state]
    img = M.troffer_lens(seed={"on": 1, "off": 2, "dim": 3, "red": 4}[state], lit=lit, lens=lens, glow=glow,
                         frame=(214, 210, 198), frame_px=2, rail=TBAR_RAIL)
    px = img.load()
    if lit:
        for y in range(3, S - 3):
            for x in range(3, S - 3):
                px[x, y] = M.rgba(M.mix(px[x, y], glow, 0.35))
    gap = (96, 94, 88) if state != "red" else (88, 40, 34)
    for i in range(2, S - 2):
        for (x, y) in ((i, 2), (i, S - 3), (2, i), (S - 3, i)):
            px[x, y] = M.rgba(M.lift(gap, (x + y) % 3 - 1))
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


def concrete_floor(kind, alt=0):
    """Level 1's car park floor: power-trowelled concrete (faint swirl arcs) with broad pour patches. Version 2 of 3
    carries a hairline crack and a faint tyre scuff; the dark floor's mould and the wet floor's film change place."""
    seed = {"plain": 3000, "wet": 3010, "dark": 3020}[kind] + alt
    img = l1_concrete(seed, L1_FLOOR[kind], pores=0.008, swirl=0.7, aggregate=0.03 if kind == "plain" else 0.05)
    if kind == "plain" and alt == 2:
        M.crack(img, M.sub(seed, "crack"), length=(16, 26), strength=0.2)
        tyre_scuff(img, M.sub(seed, "scuff"))
    if kind == "dark" and alt:
        M.stain(img, M.sub(seed, "mould"), radius=9, color=(70, 84, 72), strength=0.32, at=M.spread(seed, 3)[alt], ring=0.3)
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
    row of two form-tie holes. Version 3 of 3 has a hairline crack and a rust run from a tie. The damaged wall is
    broken out round its (modelled) rebar; the old painted rebar is gone."""
    seed = 3100 + alt + (50 if damaged else 0)
    img = l1_concrete(seed, L1_WALL, pores=0.022, patches=3.0, patch_hue=2.0)
    pour_line(img, 0, M.sub(seed, "lift"))
    for x in (8, 24):
        tie_hole(img, x, 8)
    if alt == 2 and not damaged:
        M.crack(img, M.sub(seed, "crack"), at=(rng_at(seed)), length=(14, 24), strength=0.22)
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
    """Level 2's dark grey cast concrete (B5: `tunnel_cast`, the plain wall's first version), for the textures painted
    over it (the warning sign, the old cube faces of the pipe and machinery walls)."""
    return tunnel_cast(seed)


TUNNEL_GREY = (67, 72, 77)


def tunnel_cast(seed, alt=0):
    """(B5) Level 2's walls: dark grey cast concrete (`matlib.concrete`, quiet aggregate, grey patches as B4 found
    best), plywood-formed with a faint lift line and four form-tie holes, and water run down from the ceiling. The
    old texture's broad stain, damp patch and efflorescence sat in the same place in every block; here the damp
    patch and a rust run from a tie are in one version of three (`tunnelwall-plain-3`), efflorescence at the lift
    line in the second. Mean brightness is kept (69)."""
    # (round 2) every version shares one concrete ground, so neighbouring blocks in different versions meet without a
    # seam (the round-2 shots showed block squares where the ground differed); only the features differ
    ground = 352
    img = M.concrete(ground, base=TUNNEL_GREY, grain=2, mottle=6, aggregate=0.012, pores=0.005, patches=4.0,
                     patch_hue=1.2, hue=1.2)
    M.grime(img, 0.16, M.sub(ground, "soot"), color=(40, 40, 38), cells=(16, 8), cover=0.55)  # soot and damp
    for (x, y) in ((6, 8), (24, 8), (6, 24), (24, 24)):
        tie_hole(img, x, y)
    rng = random.Random(seed + 1)
    px = img.load()
    for sx in (rng.randrange(2, 12), rng.randrange(18, 29)):  # water streaks, each showing over half the tile
        phase = rng.random() * 6.283
        for y in range(S):
            k = max(0.0, math.sin(y * 6.283 / S + phase)) ** 2 * 0.2
            for x, w in ((sx, 1.0), (sx + 1, 0.5)):
                px[x, y] = shade(px[x, y], 1 - k * w)
    if alt == 1:
        pour_line(img, 0, M.sub(seed, "lift"))  # a lift line with lime bloom weeping out of it, in one version only
        for x in range(S):
            if rng.random() < 0.55:
                M.touch(img, x, 1, 0.08)
                if rng.random() < 0.4:
                    M.touch(img, x, 2, 0.05)
    if alt == 2:
        M.stain(img, M.sub(seed, "damp"), radius=8, color=(40, 40, 38), strength=0.35)
        M.drips(img, 1, M.sub(seed, "tie"), color=(104, 70, 48), length=(7, 12), strength=0.28, start=10)
    return match_mean(img, 69)


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
    img = noise_fill(hexrgb(0x2E4A6E), 8, 390 + top)
    d = ImageDraw.Draw(img)
    if top:
        d.ellipse([3, 3, 28, 28], outline=(20, 34, 52, 255))
        d.ellipse([20, 8, 24, 12], fill=(30, 30, 30, 255))
    else:
        for y in (8, 22):
            d.line([0, y, S - 1, y], fill=(20, 34, 52, 255), width=2)
        blotch(img, (10, 28), 7, (110, 70, 40), 0.6, 13)  # rust
    return img


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
    d = ImageDraw.Draw(glass)
    d.line([4, 2, 14, 12], fill=(70, 84, 92, 255), width=2)  # reflection
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
    d = ImageDraw.Draw(glass)
    cx, cy = 20, 12
    rng = random.Random(442)
    for k in range(9):  # cracks running out from the impact
        a = k * math.tau / 9 + rng.uniform(-0.2, 0.2)
        r = rng.randint(9, 22)
        d.line([cx, cy, cx + r * math.cos(a), cy + r * math.sin(a)], fill=(150, 160, 164, 255), width=1)
    for r in (3, 6):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(130, 140, 146, 255))
    d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(6, 6, 8, 255))  # the hole
    save(glass, "block/level1/car-glass-broken.png")
    seat = noise_fill(hexrgb(0x4A3426), 6, 443)
    d = ImageDraw.Draw(seat)
    for y in range(4, S, 8):  # piping
        d.line([0, y, S - 1, y], fill=(58, 42, 30, 255))
    d.line([9, 10, 17, 19], fill=(176, 160, 120, 255), width=2)  # the foam showing through a split
    save(seat, "block/level1/car-seat.png")


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


def level3_textures():
    # Two-tone glazed structural tile: darker ochre glaze below, lighter above, dark grout lines
    img = noise_fill(hexrgb(0x8B7056), 6, 500)
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=(63, 46, 21, 255))
    for row in range(4):
        off = 8 if row % 2 else 0
        for x in range(off, S + 16, 16):
            d.line([x % S, row * 8, x % S, row * 8 + 7], fill=(63, 46, 21, 255))
    for y in range(0, 16):
        for x in range(S):
            r, g, b, a = img.getpixel((x, y))
            if (y % 8) != 0:
                img.putpixel((x, y), (clamp(r * 0.88), clamp(g * 0.85), clamp(b * 0.75), a))
    save(img, "block/level3/l3wall-glazed.png")

    img = Image.new("RGBA", (S, S), (60, 30, 18, 255))
    d = ImageDraw.Draw(img)
    rng = random.Random(501)
    for row in range(8):
        off = 4 if row % 2 else 0
        for col in range(-1, 5):
            c = rng.choice([(118, 39, 5), (112, 56, 26), (96, 40, 20), (130, 60, 30)])
            d.rectangle([col * 8 + off + 1, row * 4 + 1, col * 8 + off + 7, row * 4 + 3], fill=c + (255,))
    save(img, "block/level3/l3wall-brick.png")

    img = noise_fill(hexrgb(0x36311A), 7, 502)
    d = ImageDraw.Draw(img)
    for row in range(2):
        off = 8 if row % 2 else 0
        d.line([0, row * 16, S - 1, row * 16], fill=(28, 25, 12, 255))
        for x in range(off, S + 16, 16):
            d.line([x % S, row * 16, x % S, row * 16 + 15], fill=(28, 25, 12, 255))
    save(img, "block/level3/l3wall-cinder.png")

    img = noise_fill(hexrgb(0x8C7F6E), 9, 503)
    blotch(img, (20, 10), 8, (76, 72, 56), 0.4, 504)
    save(img, "block/level3/dustyfloor.png")
    img = noise_fill(hexrgb(0x5E594F), 8, 505)
    blotch(img, (12, 18), 10, (61, 53, 41), 0.5, 506)
    save(img, "block/level3/plasterceiling.png")
    save(noise_fill(hexrgb(0x1E1E20), 5, 507), "block/level3/cable.png")
    img = noise_fill(hexrgb(0x5A6458), 6, 508)
    d = ImageDraw.Draw(img)
    for x in range(2, S, 4):
        d.line([x, 0, x, S - 1], fill=(70, 78, 70, 255))
    d.rectangle([10, 10, 21, 16], fill=(220, 200, 40, 255))  # warning label
    save(img, "block/level3/transformer.png")
    save(noise_fill(hexrgb(0x8A5A3A), 8, 509), "block/level3/insulator.png")
    img = noise_fill(hexrgb(0x7C8084), 5, 510)
    d = ImageDraw.Draw(img)
    for i in range(4):  # breakers
        d.rectangle([4 + i * 6, 8, 7 + i * 6, 14], fill=(30, 30, 30, 255))
        d.rectangle([5 + i * 6, 9, 6 + i * 6, 11], fill=(200, 200, 200, 255))
    d.rectangle([6, 20, 25, 24], fill=(180, 30, 25, 255))
    save(img, "block/level3/panel.png")
    img = Image.new("RGBA", (S, S), (40, 42, 44, 255))
    d = ImageDraw.Draw(img)
    for i in range(0, S, 4):
        d.line([i, 0, i, S - 1], fill=(120, 124, 128, 255))
        d.line([0, i, S - 1, i], fill=(120, 124, 128, 255))
    save(img, "block/level3/fan.png")
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


def level4_textures():
    save(noise_fill(hexrgb(0xD8D5D4), 4, 520), "block/level4/officewall.png")
    img = noise_fill(hexrgb(0x5A6068), 8, 521)  # a rainy, foggy nowhere
    rng = random.Random(522)
    px = img.load()
    for _ in range(60):
        x, y = rng.randrange(S), rng.randrange(S - 6)
        for k in range(rng.randint(3, 6)):
            px[x, y + k] = (150, 160, 172, 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(40, 42, 46, 255), width=2)
    d.line([16, 0, 16, S - 1], fill=(40, 42, 46, 255), width=1)
    save(img, "block/level4/officewindow.png")
    img = Image.new("RGBA", (S, S), (180, 210, 220, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(110, 114, 118, 255), width=2)
    save(img, "block/level4/officeglass.png")
    save(noise_fill(hexrgb(0x85837D), 7, 523), "block/level4/officecarpet-plain.png")
    save(noise_fill(hexrgb(0x6E6C67), 7, 523), "block/level4/officecarpet-ghost.png")
    img = noise_fill(hexrgb(0xD8D4CF), 3, 524)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=(150, 148, 144, 255))
    d.line([0, 15, S - 1, 15], fill=(150, 148, 144, 255))  # 2x4 tiles
    save(img, "block/level4/officeceiling.png")
    for state, lens in (("on", (252, 252, 248)), ("off", (150, 150, 146))):
        img = Image.new("RGBA", (S, S), (200, 198, 194, 255))
        d = ImageDraw.Draw(img)
        d.rectangle([2, 2, S - 3, S - 3], fill=lens + (255,))
        for x in range(4, S - 3, 3):
            d.line([x, 3, x, S - 4], fill=shade(lens, 0.93))
        save(img, f"block/level4/officelight-{state}.png")
    img = noise_fill(hexrgb(0x8A8C86), 3, 525)  # warm grey cubicle fabric with a faint basket weave
    px = img.load()
    for y in range(S):
        for x in range(S):
            f = 1.035 if ((x // 2) + (y // 2)) % 2 else 0.97
            px[x, y] = shade(px[x, y], f * (0.97 if y % 2 else 1.0))
    save(img, "block/level4/partition.png")
    save(noise_fill(hexrgb(0xB49C78), 5, 526), "block/level4/laminate.png")
    save(noise_fill(hexrgb(0xC9C2AE), 4, 527), "block/level4/crt.png")
    img = noise_fill(hexrgb(0x16241A), 4, 528)
    ImageDraw.Draw(img).text((3, 4), "C:\\>_", fill=(80, 200, 100, 255))
    save(img, "block/level4/crt-screen.png")
    save(noise_fill(hexrgb(0x33363C), 5, 529), "block/level4/chairfabric.png")
    img = noise_fill(hexrgb(0x8E9296), 4, 530)
    d = ImageDraw.Draw(img)
    for y in (10, 21):
        d.line([0, y, S - 1, y], fill=(60, 62, 66, 255))
    save(img, "block/level4/filing.png")
    img = noise_fill(hexrgb(0xA82820), 6, 531)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 21, 26], fill=(30, 34, 40, 255))
    for row in range(4):
        for col in range(3):
            d.rectangle([5 + col * 6, 5 + row * 6, 8 + col * 6, 9 + row * 6], fill=(236, 228, 205, 255))  # bottles
    d.rectangle([24, 8, 28, 16], fill=(40, 40, 40, 255))
    save(img, "block/level4/vending.png")
    save(noise_fill(hexrgb(0xE6E6E2), 3, 532), "block/level4/cooler.png")
    save(noise_fill(hexrgb(0x9CC8E6), 5, 533), "block/level4/coolerbottle.png")
    for part in ("lower", "upper"):
        img = noise_fill(hexrgb(0x9EA4A8), 4, 534)
        d = ImageDraw.Draw(img)
        d.line([15, 0, 15, S - 1], fill=(50, 52, 56, 255), width=2)
        if part == "upper":
            d.rectangle([12, 2, 19, 7], fill=(40, 40, 40, 255))
            d.text((13, 1), "^", fill=(240, 200, 80, 255))
        save(img, f"block/level4/elevatordoor-{part}.png")


def damask_panel():
    """The hotel's red damask panel in a gilt frame on cream, at 64 px: a diamond lattice with a fleur in every cell,
    woven in two reds about 10% apart (drawn 4x large and scaled down, so the curves come out smooth)."""
    N, k = 64, 4
    ground, motif = (98, 12, 8), (116, 22, 14)
    big = Image.new("RGBA", (N * k, N * k), ground + (255,))
    d = ImageDraw.Draw(big)
    x0, y0, x1, y1 = 11, 7, 52, 56  # the red field inside the frame
    cw, ch = 20, 26  # one diamond of the lattice

    def fleur(cx, cy, w, h):
        cx, cy, w, h = cx * k, cy * k, w * k, h * k
        d.polygon([(cx, cy - h * 0.5), (cx + w * 0.17, cy - h * 0.18), (cx + w * 0.1, cy + h * 0.08),
                   (cx, cy + h * 0.14), (cx - w * 0.1, cy + h * 0.08), (cx - w * 0.17, cy - h * 0.18)], fill=motif)
        for sx in (1, -1):  # the two curling side leaves
            d.polygon([(cx + sx * w * 0.08, cy + h * 0.06), (cx + sx * w * 0.3, cy - h * 0.12), (cx + sx * w * 0.5, cy - h * 0.34),
                       (cx + sx * w * 0.52, cy - h * 0.12), (cx + sx * w * 0.4, cy + h * 0.06), (cx + sx * w * 0.2, cy + h * 0.14)], fill=motif)
            d.ellipse([cx + sx * w * 0.42 - w * 0.07, cy - h * 0.4, cx + sx * w * 0.42 + w * 0.07, cy - h * 0.3], fill=motif)
        d.rectangle([cx - w * 0.24, cy + h * 0.14, cx + w * 0.24, cy + h * 0.22], fill=motif)  # the band
        d.polygon([(cx - w * 0.14, cy + h * 0.22), (cx + w * 0.14, cy + h * 0.22), (cx, cy + h * 0.46)], fill=motif)  # the foot

    ox, oy = (x0 + x1) / 2, (y0 + y1) / 2
    for i in range(-3, 4):
        for j in range(-4, 5):
            fleur(ox + i * cw + (cw / 2 if j % 2 else 0), oy + j * ch / 2, cw * 0.56, ch * 0.6)
    for i in range(-6, 7):  # the lattice: lines through the diamonds' side corners
        px0, py0 = ox + cw / 2 + i * cw, oy
        for sgn in (1, -1):
            d.line([((px0 - 4 * cw) * k, (py0 - sgn * 4 * ch) * k), ((px0 + 4 * cw) * k, (py0 + sgn * 4 * ch) * k)], fill=motif, width=k)
    field = big.resize((N, N), Image.LANCZOS)

    img = noise_fill(hexrgb(0xD9C3A0), 3, 541, size=N)
    img.paste(field.crop((x0, y0, x1 + 1, y1 + 1)), (x0, y0))
    rng = random.Random(541)
    px = img.load()
    for y in range(y0, y1 + 1):  # a little weave noise
        for x in range(x0, x1 + 1):
            px[x, y] = shade(px[x, y], 1 + rng.uniform(-0.04, 0.04))
    d = ImageDraw.Draw(img)
    gilt, light, dark = (196, 160, 72, 255), (232, 204, 120, 255), (124, 92, 36, 255)
    d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], outline=gilt, width=4)
    d.line([x0 - 4, y0 - 4, x1 + 4, y0 - 4], fill=light)  # bevel: lit from above
    d.line([x0 - 4, y0 - 4, x0 - 4, y1 + 4], fill=light)
    d.line([x0 - 4, y1 + 4, x1 + 4, y1 + 4], fill=dark)
    d.line([x1 + 4, y0 - 4, x1 + 4, y1 + 4], fill=dark)
    d.rectangle([x0 - 1, y0 - 1, x1 + 1, y1 + 1], outline=dark)  # the inner sight edge
    return img


def level5_textures():
    # Hotel walls: mahogany wainscot, red damask panel in a gilt frame on cream, cream frieze with a cornice
    img = noise_fill(hexrgb(0x452518), 6, 540)
    d = ImageDraw.Draw(img)
    d.rectangle([3, 4, 28, 27], outline=(115, 74, 48, 255), width=2)
    d.line([0, 1, S - 1, 1], fill=(140, 100, 60, 255))
    save(img, "block/level5/hotelwall-wainscot.png")
    save(damask_panel(), "block/level5/hotelwall-panel.png")
    img = noise_fill(hexrgb(0xD9C3A0), 4, 542)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 5], fill=(232, 214, 180, 255))
    d.line([0, 6, S - 1, 6], fill=(160, 120, 70, 255))
    save(img, "block/level5/hotelwall-frieze.png")

    img = noise_fill(hexrgb(0x5E260C), 6, 543)
    d = ImageDraw.Draw(img)
    for cx, cy in ((8, 8), (24, 24), (24, 8), (8, 24)):  # gold medallions
        d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=(196, 150, 60, 255))
        d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(160, 40, 20, 255))
    save(img, "block/level5/hotelcarpet-damask.png")
    save(noise_fill(hexrgb(0x2E0C0A), 5, 544), "block/level5/hotelcarpet-maroon.png")
    img = noise_fill(hexrgb(0xB5874E), 6, 545)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, S - 3, S - 3], outline=(150, 40, 24, 255))
    save(img, "block/level5/hotelcarpet-lobby.png")
    img = noise_fill(hexrgb(0x4E2C1C), 6, 546)
    d = ImageDraw.Draw(img)
    for y in range(0, S, 6):
        d.line([0, y, S - 1, y], fill=(36, 20, 12, 255))
    save(img, "block/level5/hotelwood.png")
    save(noise_fill(hexrgb(0xE2D2B4), 3, 547), "block/level5/hotelceiling-cream.png")
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

    # The doors are drawn at 64 px (the wood and mouldings at 32 px, doubled) so the room number on its brass plate
    # can be read from across the corridor
    img = noise_fill(hexrgb(0x452518), 5, 553)
    d = ImageDraw.Draw(img)
    d.rectangle([4, 3, 27, 28], outline=(115, 74, 48, 255), width=2)
    d.rectangle([24, 10, 27, 13], fill=(196, 160, 72, 255))  # knob
    save(img.resize((2 * S, 2 * S), Image.NEAREST), "block/level5/hoteldoor-lower.png")
    # Consecutive numbers: odd doors down one side of a corridor, even down the other, counting up and then,
    # every few doors, starting again
    # Then (layout 5) a blank plate for the Beverly Room's doors, which are no guest rooms', and the odd 666
    for i, number in enumerate(("201", "202", "203", "204", "205", "206", "207", "208", "", "666")):
        img = noise_fill(hexrgb(0x452518), 5, 554)
        d = ImageDraw.Draw(img)
        d.rectangle([4, 3, 27, 31], outline=(115, 74, 48, 255), width=2)
        img = img.resize((2 * S, 2 * S), Image.NEAREST)
        d = ImageDraw.Draw(img)
        d.rectangle([17, 13, 46, 30], fill=(206, 170, 84, 255), outline=(120, 86, 32, 255))  # brass plate
        d.line([18, 14, 45, 14], fill=(236, 210, 140, 255))
        d.point([(19, 16), (44, 16), (19, 27), (44, 27)], fill=(120, 86, 32, 255))  # screws
        if number:
            text_img(img, number, (17, 14, 47, 31), (40, 22, 6, 255), 13)
        save(img, f"block/level5/hoteldoor-upper{i}.png")
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
    img = noise_fill(hexrgb(0xB8BCC0), 4, 556)
    text_img(img, "THE", (0, 0, S, 11), (40, 30, 20, 255), 7)
    text_img(img, "BEVERLY", (0, 10, S, 21), (40, 30, 20, 255), 7)
    text_img(img, "ROOM", (0, 20, S, 31), (40, 30, 20, 255), 7)
    save(img, "block/level5/beverly.png")
    save(portrait(557), "block/level5/portrait.png")
    save(noise_fill(hexrgb(0xC9A040), 8, 558), "block/level5/gilt.png")
    save(noise_fill(hexrgb(0xB08A3C), 6, 559), "block/level5/brass.png")
    save(noise_fill(hexrgb(0xFFF0C8), 3, 560), "block/level5/domeglass.png")
    save(noise_fill(hexrgb(0xF0F4FF), 6, 561), "block/level5/crystal.png")
    save(noise_fill(hexrgb(0x5A2E1A), 5, 562), "block/level5/mahogany.png")
    save(noise_fill(hexrgb(0xEDE8DC), 3, 563), "block/level5/linen.png")
    save(noise_fill(hexrgb(0x7A1A14), 5, 564), "block/level5/blanket.png")
    save(noise_fill(hexrgb(0x6E1420), 6, 565), "block/level5/velvet.png")
    save(noise_fill(hexrgb(0x3E6A2A), 10, 566), "block/level5/palmleaf.png")
    save(noise_fill(hexrgb(0x8A5A3A), 6, 567), "block/level5/pot.png")
    save(noise_fill(hexrgb(0x1E5A30), 5, 568), "block/level5/felt.png")
    save(noise_fill(hexrgb(0xEEE6D0), 3, 569), "block/level5/mahjong.png")
    img = noise_fill(hexrgb(0x654729), 10, 570)
    d = ImageDraw.Draw(img)
    for y in range(4, S, 9):
        for x in range(3, S, 7):
            d.point((x, y), fill=(175, 146, 93, 255))  # rivets
    save(img, "block/level5/boiler.png")
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
    # (B5) the plain wall in three versions (alternates in blocktypes/level2/tunnelwall.json), the brick from matlib
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        save(tunnel_cast(352 + alt, alt), f"block/level2/tunnelwall-plain{v}.png")
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
