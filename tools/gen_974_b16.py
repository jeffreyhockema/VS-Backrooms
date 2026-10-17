"""Level 974, Kitty's House, graphics pass B16: the painters and model parts that replace B0's flat ones. Called from
gen_974_tex.generate (textures, after the old painters, under the same keys plus new version keys) and gen_974 (the block
types' versions, and the computer's and photo frames' parts). Each family has its own function, so dropping its call
reverts it; the palette (Baker-Miller pink, trim white, blush carpet, the pastel tiles) and every mean are kept:

- `walls`: the pink paint as paint over plaster, four versions on one calm ground, picked by height too.
- `ceiling`: white plaster in three versions on one ground.
- `carpet`: the blush carpet as a cut pile, a little lived-in (not pristine), three versions turned at random.
- `tiles`: the kitchen checker and the mint bath tile as glazed tiles, each shaded, a recessed grout; two versions.
- `trim`: the white trim and furniture paint over wood, a faint grain and brush marks (still almost flat: mouldings
  overlap at corners); the gilt of the gold frames burnished; the computer's beige plastic and its key caps.
- `computer_parts`, `frame_parts`: the old computer's screen set back in a bezel and its keyboard's keys as keys; the
  photo frames as a moulding with a lit outer bead and an inner step down to the mat.
"""
import math
import random

import numpy as np
from PIL import Image

import matlib as M
from gen_974_tex import (save, seed_of, PINK, CEILING, CARPET, CHECK_PINK, CHECK_WHITE, MINT, TRIM, TEX)

S = 32
COUNTS = {"paint-1": 4, "ceiling": 3, "carpet": 3, "checker": 2, "bathtile": 2}
EXTRA = {"paint-1": ["paint-2", "paint-3", "paint-4"]}   # paint-2 was B0's alternate; paint-3 and -4 are new


def versions(key):
    """The texture keys of a surface's versions (the first is the key itself)."""
    if key in EXTRA:
        return [key] + EXTRA[key]
    return [key] + [f"{key}-{i}" for i in range(2, COUNTS.get(key, 1) + 1)]


def _old(key):
    import os
    return Image.open(os.path.join(TEX, "block", "974", key + ".png")).convert("RGBA")


def mean_rgb(img):
    return np.asarray(img.convert("RGBA"), dtype=np.float64)[:, :, :3].reshape(-1, 3).mean(axis=0)


def matched(img, target_mean):
    a = np.asarray(img.convert("RGBA"), dtype=np.float64)
    a[:, :, :3] += np.asarray(target_mean) - a[:, :, :3].reshape(-1, 3).mean(axis=0)
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8), "RGBA")


def walls():
    """Baker-Miller pink over plaster: one calm ground for every version, each its own fine roller stipple and the odd
    filled bump; the old mean kept (the lit wall lands near canon's #F09AB0 in game)."""
    om = mean_rgb(_old("paint-1"))
    ground = M.noise_hv(tuple(om), 0, seed_of("b16paintground"), S, mottle=3, cells=(32, 16), hue=1.0)
    for i, k in enumerate(versions("paint-1")):
        img = M.plaster(seed=seed_of(f"b16paint{i}"), base=tuple(om), grain=2, mottle=3, roller=0.55, bumps=0.003)
        M.turn_safe(img, ground, band=8, radius=3, keep=0.5)
        save(matched(img, om), k)


def ceiling():
    om = mean_rgb(_old("ceiling"))
    ground = M.noise_hv(tuple(om), 0, seed_of("b16ceilground"), S, mottle=2, cells=(32, 16), hue=0.6)
    for i, k in enumerate(versions("ceiling")):
        img = M.plaster(seed=seed_of(f"b16ceil{i}"), base=tuple(om), grain=2, mottle=2, roller=0.3, bumps=0.006)
        M.turn_safe(img, ground, band=8, radius=3, keep=0.5)
        save(matched(img, om), k)


def carpet():
    """A soft blush cut pile, heathered a shade darker, a little lived-in (D1's dingy, lightly: the user found a
    pristine carpet wrong), three versions on one ground, turned at random by the block type."""
    import gen_textures as T
    om = mean_rgb(_old("carpet"))
    base = tuple(CARPET)
    ground = M.noise_hv(base, 0, seed_of("b16carpetground"), mottle=3, cells=(16, 8), hue=1.0)
    for i, k in enumerate(versions("carpet")):
        img = M.carpet(seed_of(f"b16carpet{i}"), base=base, tone2=M.hue_shift(M.lift(base, -9), 2), mix2=0.35,
                       pile=5, grain=3, mottle=2)
        T.dingy(img, seed_of(f"b16carpetdingy{i}"), dull=0.03, dim=0.5, grime=0.04, flecks=5)
        M.turn_safe(img, ground, band=8, keep=0.6)
        save(matched(img, om), k)


def _glazed(px, x0, y0, n, c, rng, gloss=True):
    """One glazed tile of n x n px at (x0, y0) inside the grout: its own shade and a slight tilt, a lit top and left
    edge, a shaded foot and right edge, a small highlight up and to the left."""
    v, ax, ay = rng.uniform(-2.5, 2.5), rng.uniform(-2, 2), rng.uniform(-2, 2)
    hu = rng.uniform(-1.2, 1.2)
    for yy in range(n):
        for xx in range(n):
            d = v + ax * (xx / (n - 1) - 0.5) + ay * (yy / (n - 1) - 0.5) + rng.uniform(-0.8, 0.8)
            if yy == 0 or xx == 0:
                d += 4
            if yy == n - 1 or xx == n - 1:
                d -= 5
            px[x0 + xx, y0 + yy] = M.rgba(M.hue_shift(M.lift(c, d), hu))
    if gloss:
        px[x0 + 1, y0 + 1] = M.rgba(M.lift(px[x0 + 1, y0 + 1], 9))
        px[x0 + 2, y0 + 1] = M.rgba(M.lift(px[x0 + 2, y0 + 1], 5))


def tiles():
    """The kitchen checker (4 x 4 to a block, pink and white) and the mint bath tile, glazed: each tile shaded, the grout
    a recessed line, darker under the tile above. Two versions each (the tiles' own shades differ); never turned: a
    turned checker would swap its colours."""
    om = mean_rgb(_old("checker"))
    grout = (226, 214, 214)
    for i, k in enumerate(versions("checker")):
        rng = random.Random(seed_of(f"b16checker{i}"))
        img = M.noise_hv(grout, 1.5, seed_of(f"b16chgrout{i}"), S, mottle=1)
        px = img.load()
        for ty in range(4):
            for tx in range(4):
                _glazed(px, tx * 8 + 1, ty * 8 + 1, 7, CHECK_PINK if (tx + ty) % 2 == 0 else CHECK_WHITE, rng)
        for ty in range(4):  # grout in the shadow of the tile above
            for x in range(S):
                px[x, ty * 8] = M.rgba(M.lift(px[x, ty * 8], -6))
        save(matched(img, om), k)
    om = mean_rgb(_old("bathtile"))
    for i, k in enumerate(versions("bathtile")):
        rng = random.Random(seed_of(f"b16bathtile{i}"))
        img = M.noise_hv((240, 236, 230), 1.5, seed_of(f"b16btgrout{i}"), S, mottle=1)
        px = img.load()
        for ty in range(4):
            for tx in range(4):
                _glazed(px, tx * 8 + 1, ty * 8 + 1, 7, MINT, rng)
        for ty in range(4):
            for x in range(S):
                px[x, ty * 8] = M.rgba(M.lift(px[x, ty * 8], -8))
        save(matched(img, om), k)


def trim():
    """White trim paint over wood (almost flat: mouldings overlap at corners): a faint long grain under the paint and the
    odd brush mark; the gold frames' gilt burnished (a soft sheen and darker recesses); the old computer's beige plastic
    (a faint texture) and its key caps."""
    om = mean_rgb(_old("trim"))
    img = M.noise_hv(TRIM, 0.8, seed_of("b16trim"), S, mottle=1, cells=(16, 8), hue=0.4)
    st = M.value_noise((S, S), (32, 1), seed_of("b16trimgrain"))
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y], st[y][x] * 1.6))
    save(matched(img, om), "trim")
    om = mean_rgb(_old("gilt"))
    img = M.brushed_metal(seed=seed_of("b16gilt"), base=(214, 176, 92), direction="h", streak=6, sheen=14, drift=0.2)
    M.grime(img, 0.1, seed_of("b16giltgrime"), color=(120, 84, 40), cells=(4, 2), cover=0.35)
    save(matched(img, om), "gilt")
    om = mean_rgb(_old("beige"))
    save(matched(M.noise_hv((232, 224, 204), 1.5, seed_of("b16beige"), S, mottle=2, hue=0.6), om), "beige")
    img = M.noise_hv((244, 240, 228), 1.2, seed_of("b16keycap"), S, mottle=1)
    px = img.load()
    for x in range(S):
        px[x, 0] = M.rgba(M.lift(px[x, 0], 6))
    save(img, "keycap")


def computer_parts():
    """The old computer's screen set back 0.5 inside a beige bezel of four strips, and a keyboard of a beige tray and
    four rows of key caps (B0 painted the keys). Returns (bezel parts, keyboard parts); the screen itself (its glow and
    picture) stays as it was, moved back."""
    import detail_kit as DK
    bezel = [DK.bx("BezelT", (3.9, 20.5, 5.4), (12.1, 21.6, 6.0), "beige", faces=("north", "down", "east", "west", "up")),
             DK.bx("BezelB", (3.9, 14.6, 5.4), (12.1, 15.0, 6.0), "beige", faces=("north", "up", "east", "west", "down")),
             DK.bx("BezelL", (3.9, 15.0, 5.4), (4.5, 20.5, 6.0), "beige", faces=("north", "east")),
             DK.bx("BezelR", (11.5, 15.0, 5.4), (12.1, 20.5, 6.0), "beige", faces=("north", "west"))]
    keys = [DK.bx("KeyTray", (3, 13.5, 1.4), (12, 13.95, 4.8), "beige")]
    for r, (z, off, n) in enumerate(((1.75, 0.0, 9), (2.5, 0.35, 9), (3.25, 0.6, 8), (4.0, 0.0, 9))):
        x = 3.35 + off
        for c in range(n):
            w = 0.62
            if r == 3 and c == 4:   # the space bar
                keys.append(DK.bx("KeySpace", (x, 13.95, z), (x + 3.0, 14.25, z + 0.55), "keycap"))
                x += 3.0 + 0.32
                continue
            if r == 3 and c > 4:
                break
            keys.append(DK.bx(f"Key{r}{c}", (x, 13.95, z), (x + w, 14.25, z + 0.55), "keycap"))
            x += w + 0.32
    return bezel, keys


def frame_parts(t):
    """A photo frame (modelled on the wall's north face, z < 0) as a moulding: the outer bead 1.4 deep, a step down
    toward the opening, and a thin lip round the mat (B0: four flat bars). t is the frame's material key."""
    import detail_kit as DK
    return [DK.bx("Top", (3, 12.6, -1.2), (13, 14, 0), t), DK.bx("Bottom", (3, 2, -1.2), (13, 3.4, 0), t),
            DK.bx("Left", (3, 3.4, -1.2), (4.4, 12.6, 0), t), DK.bx("Right", (11.6, 3.4, -1.2), (13, 12.6, 0), t),
            DK.bx("BeadT", (3.3, 13.2, -1.45), (12.7, 13.7, -1.2), t, faces=("north", "up", "down", "east", "west")),
            DK.bx("BeadB", (3.3, 2.3, -1.45), (12.7, 2.8, -1.2), t, faces=("north", "up", "down", "east", "west")),
            DK.bx("BeadL", (3.3, 2.8, -1.45), (3.8, 13.2, -1.2), t, faces=("north", "east", "west")),
            DK.bx("BeadR", (12.2, 2.8, -1.45), (12.7, 13.2, -1.2), t, faces=("north", "east", "west")),
            DK.bx("LipT", (4.4, 12.1, -0.85), (11.6, 12.6, -0.6), t, faces=("north", "down")),
            DK.bx("LipB", (4.4, 3.4, -0.85), (11.6, 3.9, -0.6), t, faces=("north", "up")),
            DK.bx("LipL", (4.4, 3.9, -0.85), (4.9, 12.1, -0.6), t, faces=("north", "east")),
            DK.bx("LipR", (11.1, 3.9, -0.85), (11.6, 12.1, -0.6), t, faces=("north", "west")),
            DK.bx("Mat", (4.4, 3.4, -0.6), (11.6, 12.6, 0), "mat", faces=("north",)),
            DK.bx("Back", (6, 5.4, -0.66), (10, 10.6, -0.6), "matback", faces=("north",))]


def textures():
    walls()
    ceiling()
    carpet()
    tiles()
    trim()
    print("974 B16: paint, ceiling, carpet, tiles, trim")
