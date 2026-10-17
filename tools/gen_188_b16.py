"""Level 188, the Courtyard of Windows, graphics pass B16: the painters and model parts that replace B0's flat ones.
Called from gen_188_tex.generate (textures, after the old painters, under the same keys plus new version keys) and from
gen_188 / gen_188_props (the block types' versions, and the bollard's, downpipe's and door's parts). Each family has its
own function, so dropping its call reverts it; the palette (pale paver, warm grey render, dark aluminium, white blind,
the green EXIT) and every mean are kept:

- `pavers`: the courtyard's concrete pavers as slabs in running bond, each lit on its top edge with a recessed joint, a
  fine aggregate; three plain versions, two mossy (moss cushions in the joints, a different place in each), two cracked.
- `render`: the façade render as trowelled plaster on one ground, three versions picked by height too; the floor-line
  band a clean recessed groove; the rain streak on the same ground.
- `blinds`: the roller blinds as a woven screen fabric (B0 painted slat lines on a roller blind), the lit blind too.
- `metal`: the aluminium of the window frames and doors brushed, the kick plates and push bars brushed steel with
  screws, the downpipe painted and round, the bollards' dark paint, the EXIT sign's box.
- `moss`: the moss tufts fuller, lit at their tips.
- `bollard`, `downpipe`, `downpipe_top`: a bollard on a bolted plinth with a stepped cap (the lit band unchanged); the
  downpipe with clips bolted to the wall and socket collars; the hopper a flared head with a rim and dark water.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw

import matlib as M
from gen_188_tex import save, seed_of, TEX, PAVER, MOSS, BLADE, RENDER, BLIND, ALU

S = 32
COUNTS = {"paver-plain": 3, "paver-moss": 2, "paver-cracked": 3, "cladding-plain": 3, "cladding-band": 2}


def versions(key):
    return [key] + [f"{key}-{i}" for i in range(2, COUNTS.get(key, 1) + 1)]


def _old(key):
    import os
    return Image.open(os.path.join(TEX, "block", "188", key + ".png")).convert("RGBA")


def mean_rgb(img):
    return np.asarray(img.convert("RGBA"), dtype=np.float64)[:, :, :3].reshape(-1, 3).mean(axis=0)


def matched(img, target_mean, amount=1.0):
    a = np.asarray(img.convert("RGBA"), dtype=np.float64)
    a[:, :, :3] += (np.asarray(target_mean) - a[:, :, :3].reshape(-1, 3).mean(axis=0)) * amount
    return Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8), "RGBA")


# ---------------------------------------------------------------- pavers

def _slabs(seed, ground):
    """Two slabs a face in running bond (joints at y 0 and 16, the upright joint at x 8 above and x 24 below): cast
    concrete with a fine aggregate, its broad field the shared ground's, each slab lit on its top edge and shaded at its
    foot, the joints recessed. The two rows keep one tone in every version (a slab runs across the block edge)."""
    img = M.concrete(seed=seed, base=PAVER, grain=3, mottle=3, aggregate=0.018, pores=0.008, hue=1.2, patch_hue=0)
    M.turn_safe(img, ground, band=8, radius=3, keep=0.4)
    px = img.load()
    for y in range(S):
        row = 0 if y < 16 else 1
        for x in range(S):
            d = (1.5 if row == 0 else -1.5)
            yy = y % 16
            jx = 8 if row == 0 else 24
            if yy == 0:
                d -= 28                                  # the joint
            elif yy == 1:
                d += 6                                   # the slab's lit top edge
            elif yy == 15:
                d -= 5                                   # its foot, into the joint below
            if x == jx:
                d = -26 if yy else d
            elif x == jx + 1 and yy:
                d += 4                                   # the lit end of the slab to the right of the joint
            elif x == jx - 1 and yy:
                d -= 4
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    return img


def _joints():
    return ([(x, 0) for x in range(S)] + [(x, 16) for x in range(S)] + [(8, y) for y in range(1, 16)] +
            [(24, y) for y in range(17, 32)])


def _moss(img, seed):
    """Moss cushions in the joints: dense dark-green pixels in the joint, spilling a pixel or two onto the slabs, their
    tips lit; a few short runs, at a different place in each version."""
    rng = random.Random(seed)
    px = img.load()
    joints = _joints()
    inner = [(x, y) for x, y in joints if 2 <= x <= 22 and 2 <= y <= 22 or (y in (0, 16) and 2 <= x <= 20)]
    starts = rng.sample(inner, 6)   # runs that stay inside the block, so no run is cut at its edge
    for sx, sy in starts:
        horiz = sy in (0, 16)
        run = rng.randint(5, 12)
        for i in range(run):
            x, y = (sx + i, sy) if horiz else (sx, sy + i)
            if not (1 <= x <= 30 and y <= 30):
                break
            if (x, y) not in joints and not horiz:
                break
            c = M.mix(MOSS, BLADE, rng.random() * 0.5)
            px[x, y] = M.rgba(M.lift(c, rng.uniform(-6, 2)))
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if rng.random() < 0.35:
                    xx, yy = (x + dx) % S, (y + dy) % S
                    px[xx, yy] = M.rgba(M.lift(M.mix(MOSS, BLADE, rng.random() * 0.6), rng.uniform(-2, 8)))
            if rng.random() < 0.3:   # a lit frond tip
                px[x, (y - 1) % S] = M.rgba(M.lift(BLADE, 14))
    return img


def pavers():
    ground = M.noise_hv(PAVER, 0, seed_of("b16paverground"), S, mottle=3, cells=(16, 8), hue=0.8)
    om = mean_rgb(_old("paver-plain"))
    for i, k in enumerate(versions("paver-plain")):
        save(matched(_slabs(seed_of(f"b16paver{i}"), ground), om), k)
    om = mean_rgb(_old("paver-moss"))
    for i, k in enumerate(versions("paver-moss")):
        img = _moss(_slabs(seed_of(f"b16pavermoss{i}"), ground), seed_of(f"b16moss{i}"))
        save(matched(img, om, 0.5), k)
    om = mean_rgb(_old("paver-cracked"))
    for i, k in enumerate(versions("paver-cracked")):
        img = _slabs(seed_of(f"b16pavercr{i}"), ground)
        rng = random.Random(seed_of(f"b16crack{i}"))
        x, y = rng.randrange(2, 12), rng.choice((rng.randrange(3, 13), rng.randrange(19, 29)))
        px = img.load()
        for _ in range(16):   # a hairline crack, unbroken: dark, its lower lip lit
            nx, ny = x + 1, y + rng.choice((-1, 0, 0, 1))
            if ny % 16 and 0 < nx < S - 1:
                px[nx, ny % S] = M.rgba(M.lift(px[nx, ny % S], -26))
                px[nx, (ny + 1) % S] = M.rgba(M.lift(px[nx, (ny + 1) % S], 5))
            x, y = nx, ny
        if i != 1:   # a faint stain in two of the three, at its own place, kept inside the block
            at = (rng.uniform(9, 23), rng.uniform(9, 23))
            M.stain(img, seed_of(f"b16pstain{i}"), radius=5.0, color=(96, 92, 84), strength=0.18, at=at, ring=0.2)
        save(matched(img, om), k)


# ---------------------------------------------------------------- render

def render():
    om = mean_rgb(_old("cladding-plain"))
    ground = M.noise_hv(RENDER, 0, seed_of("b16renderground"), S, mottle=3, cells=(32, 16), hue=1.0)

    def coat(i):
        img = M.plaster(seed=seed_of(f"b16render{i}"), base=RENDER, grain=3, mottle=3, roller=0.0, bumps=0.01)
        rng = random.Random(seed_of(f"b16trowel{i}"))
        px = img.load()
        for _ in range(18):  # faint trowel arcs
            x, y = rng.randrange(S), rng.randrange(S)
            ln, k = rng.randint(5, 11), rng.choice((-2.2, 2.2))
            for j in range(ln):
                xx, yy = (x + j) % S, (y + int(round(math.sin(j / ln * math.pi) * 1.5))) % S
                px[xx, yy] = M.rgba(M.lift(px[xx, yy], k))
        M.turn_safe(img, ground, band=8, radius=3, keep=0.4)
        return img
    for i, k in enumerate(versions("cladding-plain")):
        save(matched(coat(i), om), k)
    om = mean_rgb(_old("cladding-band"))
    for i, k in enumerate(versions("cladding-band")):
        img = coat(10 + i)
        px = img.load()
        for x in range(S):        # the floor line: a clean recessed groove (dark under its lip, lit below)
            px[x, 14] = M.rgba(M.lift(px[x, 14], -4))
            px[x, 15] = M.rgba(M.lift(px[x, 15], -22))
            px[x, 16] = M.rgba(M.lift(px[x, 16], 7))
        save(matched(img, om), k)
    om = mean_rgb(_old("cladding-streak"))
    img = coat(20)
    px = img.load()
    rng = random.Random(seed_of("b16streak"))
    for x in range(9, 23):   # a grey rain streak from the sill above, fading down, ragged at its edges
        edge = 1 - abs(x - 16) / 7.5
        for y in range(S):
            k = -14 * edge * (1 - y / 32) ** 1.3 * rng.uniform(0.85, 1.1)   # fades out before the block's foot
            px[x, y] = M.rgba(M.lift(px[x, y], k, 0.05))
    save(matched(img, om), "cladding-streak")


# ---------------------------------------------------------------- blinds

def blinds():
    """A roller blind is a woven screen fabric, not slats: a fine weave, a faint hem; the lit blind keeps its glow
    picture (the lamp low behind it) with the weave instead of B0's slat lines."""
    from gen_188_tex import save_quads
    om = mean_rgb(_old("blind"))
    img = M.fabric(seed=seed_of("b16blind"), base=BLIND, weave="plain", contrast=5, grain=2, mottle=3)
    save(matched(img, om), "blind")
    quads = [_old(f"blind-glow-{q}") for q in ("ul", "ur", "ll", "lr")]
    pic = Image.new("RGBA", (64, 64))
    for q, (x, y) in zip(quads, ((0, 0), (32, 0), (0, 32), (32, 32))):
        pic.paste(q, (x, y))
    a = np.asarray(pic, dtype=np.float64)
    # undo B0's slat lines (every 4th row darkened by a quarter toward (210,178,124)): take each such row from the rows
    # beside it, then lay a faint weave over the whole
    for y in range(0, 64, 4):
        a[y, :, :3] = (a[(y - 1) % 64, :, :3] + a[(y + 1) % 64, :, :3]) / 2
    yy, xx = np.mgrid[0:64, 0:64]
    a[:, :, :3] += (((xx + yy) % 2) * 2 - 1)[:, :, None] * 1.5
    pic = Image.fromarray(np.clip(np.rint(a), 0, 255).astype(np.uint8), "RGBA")
    save_quads(pic, "blind-glow")


# ---------------------------------------------------------------- metal

def round_paint(base, seed, w=6):
    """Paint on a round pipe whose face is w px wide in the texture (the face's UV starts at its left): lit a third of
    the way across, dark toward the far edge; the rest of the texture the plain paint."""
    img = M.painted_metal(seed=seed, base=base, grain=2, mottle=3, panel=False, chips=2, under=(90, 84, 78))
    px = img.load()
    for x in range(S):
        u = (x % w) / (w - 1)
        d = 10 * math.exp(-((u - 0.3) / 0.22) ** 2) - 9 * max(0.0, u - 0.6) / 0.4
        for y in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    return img


def metal():
    om = mean_rgb(_old("alu"))
    save(matched(M.brushed_metal(seed=seed_of("b16alu"), base=ALU, direction="v", streak=5, sheen=6, drift=0.1), om), "alu")
    om = mean_rgb(_old("kickplate"))
    img = M.brushed_metal(seed=seed_of("b16kick"), base=(140, 136, 128), direction="h", streak=7, sheen=8)
    for x, y in ((2, 2), (29, 2), (2, 29), (29, 29)):
        M.screw(img, x, y)
    save(matched(img, om), "kickplate")
    om = mean_rgb(_old("steel"))
    save(matched(M.brushed_metal(seed=seed_of("b16steel"), base=(150, 152, 156), direction="h", streak=6, sheen=12), om), "steel")
    om = mean_rgb(_old("downpipe"))
    save(matched(round_paint((112, 116, 118), seed_of("b16downpipe")), om), "downpipe")
    save(matched(M.painted_metal(seed=seed_of("b16hopper"), base=(112, 116, 118), grain=2, mottle=3, panel=False, chips=3,
                                 under=(90, 84, 78)), om), "hopper")
    om = mean_rgb(_old("bracket"))
    save(matched(M.painted_metal(seed=seed_of("b16bracket"), base=(80, 82, 84), grain=2, mottle=3, panel=False, chips=2), om), "bracket")
    om = mean_rgb(_old("bollard"))
    save(matched(round_paint((52, 54, 58), seed_of("b16bollard"), w=8), om), "bollard")
    om = mean_rgb(_old("signbox"))
    img = M.painted_metal(seed=seed_of("b16signbox"), base=(236, 238, 236), grain=2, mottle=2, panel=False, chips=0)
    save(matched(img, om), "signbox")


def moss():
    """The moss tufts: B0's light fronds (the 2026-10 review's), a few more of them, each darker at its root and lit
    at its tip, on alpha."""
    from gen_188_tex import big, reduce
    img, d, s = big(S, scale=4)
    rng = random.Random(seed_of("b16tuft"))
    for i in range(18):
        x = rng.uniform(4, 28) * s
        h = rng.uniform(9, 28) * s
        lean = rng.uniform(-5, 5) * s
        c = M.mix(BLADE, (0x7A, 0x9A, 0x58), rng.random())
        w = int(rng.uniform(1.2, 2.0) * s)
        mid = (x + lean * 0.5, S * s - h * 0.5)
        d.line([(x, S * s), mid], fill=M.rgba(M.lift(c, -14)), width=w)
        d.line([mid, (x + lean, S * s - h)], fill=M.rgba(c), width=w)
        d.ellipse([x + lean - 1.5 * s, S * s - h - 1.5 * s, x + lean + 1.5 * s, S * s - h + 1.5 * s], fill=M.rgba(M.lift(c, 16)))
    img = reduce(img, S)
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, min(255, int((a - 40) * 1.5)) if a > 40 else 0)
    save(img, "mosstuft")


def textures():
    pavers()
    render()
    blinds()
    metal()
    moss()
    print("188 B16: pavers, render, blinds, metal, moss")


# ---------------------------------------------------------------- models

def octagon(name, cx, cz, r, y1, y2, tex, glow=0, step=0.02, faces=None):
    """A regular octagon of inradius r (two crossed boxes and the same turned 45 degrees); each box's top and bottom a
    hair apart so no two faces share a plane."""
    from gen_188_kit import bx
    a = r * math.tan(math.pi / 8)
    els = []
    kw = {"faces": faces} if faces else {}
    for k, (hx, hz, ry) in enumerate(((r, a, 0), (a, r, 0), (r, a, 45), (a, r, 45))):
        dd = k * step
        el = bx(f"{name}{k}", (cx - hx, y1 + dd, cz - hz), (cx + hx, y2 - dd, cz + hz), tex, glow, **kw)
        if ry:
            el["rotationOrigin"] = [cx, y1, cz]
            el["rotationY"] = ry
        els.append(el)
    return els


def bollard(band):
    """The bollard: a bolted plinth, the dark body, B0's lit band (`band`, unchanged), a stepped cap."""
    from gen_188_kit import bx
    els = octagon("Plinth", 8, 8, 2.7, 0, 0.8, "bracket")
    for i, (x, z) in enumerate(((8, 5.6), (8, 10.4), (5.6, 8), (10.4, 8))):
        els.append(bx(f"Bolt{i}", (x - 0.3, 0.8, z - 0.3), (x + 0.3, 1.1, z + 0.3), "steel", faces=("north", "east", "south", "west", "up")))
    els += octagon("Body", 8, 8, 2.0, 0.8, 6, "bollard", faces=("north", "east", "south", "west"))
    els += band
    els += octagon("Cap", 8, 8, 2.25, 9, 9.7, "bollard")
    els += octagon("Crown", 8, 8, 1.6, 9.7, 10.2, "bollard", faces=("north", "east", "south", "west", "up"))
    els += octagon("Top", 8, 8, 0.8, 10.2, 10.5, "bollard", faces=("north", "east", "south", "west", "up"))
    return els


def pipe_clip(y, name="Clip"):
    """A clip round the pipe (modelled on the wall's north face, z < 0), its two ears bolted to the wall."""
    from gen_188_kit import bx
    return [bx(name, (6.1, y, -4.4), (9.9, y + 1.2, -0.6), "bracket", faces=("north", "east", "west", "up", "down")),
            bx(name + "EarL", (4.8, y + 0.1, -1.0), (6.1, y + 1.1, 0), "bracket", faces=("north", "west", "up", "down")),
            bx(name + "EarR", (9.9, y + 0.1, -1.0), (11.2, y + 1.1, 0), "bracket", faces=("north", "east", "up", "down")),
            bx(name + "BoltL", (5.2, y + 0.35, -1.3), (5.7, y + 0.85, -1.0), "steel", faces=("north", "east", "west", "up", "down")),
            bx(name + "BoltR", (10.3, y + 0.35, -1.3), (10.8, y + 0.85, -1.0), "steel", faces=("north", "east", "west", "up", "down"))]


def downpipe():
    from gen_188_kit import bx
    return ([bx("Pipe", (6.5, 0, -4), (9.5, 16, -1), "downpipe", faces=("north", "east", "west")),
             bx("Socket", (6.2, 13.4, -4.3), (9.8, 15.2, -0.7), "downpipe", faces=("north", "east", "west", "up", "down")),
             bx("SocketLip", (6.05, 13.3, -4.45), (9.95, 13.7, -0.55), "downpipe", faces=("north", "east", "west", "down"))]
            + pipe_clip(8))


def downpipe_top():
    """The hopper head: the pipe rising into a flared box with a rolled front rim, dark water inside, strapped to the
    wall; a clip lower down."""
    from gen_188_kit import bx
    return ([bx("Pipe", (6.5, 0, -4), (9.5, 10.5, -1), "downpipe", faces=("north", "east", "west")),
             bx("Neck", (5.8, 10.2, -4.8), (10.2, 11.2, -1), "hopper", faces=("north", "east", "west", "down")),
             bx("Hopper", (5, 11.2, -5.5), (11, 13.4, -1), "hopper", faces=("north", "east", "west", "down")),
             bx("Lip", (4.6, 12.8, -5.9), (11.4, 13.4, -5.5), "hopper", faces=("north", "east", "west", "up", "down")),
             bx("LipW", (4.6, 12.8, -5.5), (5.0, 13.4, -1), "hopper", faces=("east", "west", "up", "down")),
             bx("LipE", (11.0, 12.8, -5.5), (11.4, 13.4, -1), "hopper", faces=("east", "west", "up", "down")),
             bx("Water", (5.0, 13.0, -5.5), (11.0, 13.1, -1), "drain", faces=("up",)),
             bx("Strap", (4.4, 11.6, -1.0), (11.6, 12.4, 0), "bracket", faces=("north", "east", "west", "up", "down"))]
            + pipe_clip(5))
