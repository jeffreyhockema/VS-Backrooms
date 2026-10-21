"""The Watcher (Entity 96's floating form, Level 9): its model, texture, entity type, sounds and names.

Lore (Wikidot, Entity 96 "The Neighborhood Watch"): Watchers are "gigantic eyeball-like structures with multiple optic
veins" that "levitate effortlessly at walking speeds and silently glide over the suburban areas"; the beam "instantly
turns any living matter fully absorbed in the light into fine, gray dust"; no weapon has destroyed one, Firesalt does
nothing, they have no hearing and no smell; victims leave piles of gray dust beside their belongings.

The model: a bloodshot eye two and a quarter blocks across (the Strider's is a block and a quarter), a milky, yellowed
sclera crazed with red veins that run from the back toward the iris, a large dark iris of crimson-brown fibres and a
black pupil with a dull ember at its heart (the pupil faintly glows), and at its back a wet red bulb from which eight
optic veins trail, tapering strands of segments that hang back and down and sway. A hot disc sits behind the pupil,
shrunk to nothing until the charge brightens the iris.

Animations: float (a slow bob, the veins trailing and swaying: the default), idle (stiller), scan (the eye sweeping
left and right), charge (2 s: the pupil contracts, the iris brightens, the eye leans in, the veins stiffen and
tremble), beam (held open for half a second: the iris white-hot, the pupil a point, the veins rigid).

Conventions (rig.py): the model faces -X, its left is +Z, up is +Y, feet at y = 0; a part's rest rotation turns it and
its children. The veins are chains of segments built standing up (+y) in the model and bent into place by their rest
rotations, so a segment's pose bends everything beyond it.

Run from the repo root:  python tools/gen_watcher.py   (writes the shape, texture, entity type, three sounds, and the
names into lang/en.json;  `model` as an argument writes the shape and texture only)
"""
import json
import math
import os
import re
import sys

import numpy as np

import rig
from rig import Model, pose, mix, shade, clamp, speckle, part_matrices, _rot3, _CORNERS
from rig import fill
from gen_models import blotch, line, cycle, full

TAU = math.tau
CODE = "watcher"

# ---------------------------------------------------------------- Colours

SCLERA = (226, 218, 198)       # an old, yellowed white
SCLERA_PINK = (212, 170, 160)  # where it reddens toward the back
SCLERA_SHADE = (150, 134, 130)
VEIN = (150, 30, 38)
VEIN_DARK = (96, 18, 28)
IRIS = (112, 36, 30)           # a dark crimson-brown
IRIS_DARK = (58, 16, 16)
IRIS_HI = (176, 70, 40)
IRIS_FLECK = (214, 120, 56)
LIMBUS = (26, 10, 10)
PUPIL = (8, 4, 6)
EMBER = (150, 20, 16)
HOT_IN = (255, 236, 190)
HOT_MID = (255, 150, 70)
HOT_OUT = (214, 50, 34)
GLINT = (240, 232, 220)
BULB = (150, 50, 62)           # the root of the veins: raw, wet
BULB_DARK = (92, 24, 38)
BULB_HI = (206, 116, 124)
STRAND = (164, 58, 74)         # the veins themselves: wet red-pink
STRAND_END = (210, 130, 140)
STRAND_DARK = (100, 26, 44)

# ---------------------------------------------------------------- Geometry

R = 17.6                        # the eye's radius to its square faces: 2.2 blocks across
A = R / (1 + math.sqrt(2))      # half the side of a face of the rhombicuboctahedron it is built as
EYE_Y = 20.0                    # the eye's centre (its lowest point is at 2.4 px, the veins hang below the entity)
FRONT_X = -R

N_STRANDS = 8
N_SEG = 6
BULB_X0, BULB_X1 = 16.2, 23.8   # the bulb at the back of the eye
STRAND_X = 23.4

rng = np.random.default_rng(9602)


def _strand_specs():
    """For each vein: its base thickness, where it leaves the bulb (y and z offsets from the eye's axis), and the
    direction of each segment (model space: +x is back): fanned out behind, drooping more toward the tip."""
    specs = []
    yaws = [-46, -30, -16, -4, 8, 20, 34, 48]
    for i in range(N_STRANDS):
        yaw0 = yaws[i] + float(rng.uniform(-4, 4))
        pitch0 = [14, -6, 8, -14, 4, -10, 12, -4][i] + float(rng.uniform(-3, 3))
        droop = float(rng.uniform(8, 12))
        curl = float(rng.uniform(-5, 5))
        t0 = float(rng.uniform(3.4, 4.2))
        length = float(rng.uniform(8.5, 10.5))
        oy = [3.0, -2.5, 0.5, -3.5, 2.5, -0.5, 3.5, -2.0][i]
        oz = [-2.8, -2.2, -3.4, -0.8, 0.8, 3.0, 2.2, 3.4][i]
        dirs = []
        for k in range(N_SEG):
            p = max(-84.0, pitch0 - droop * k * (1 + 0.1 * k))
            y = yaw0 + curl * k
            dirs.append((math.cos(math.radians(p)) * math.cos(math.radians(y)), math.sin(math.radians(p)),
                         math.cos(math.radians(p)) * math.sin(math.radians(y))))
        specs.append(dict(t0=t0, length=length, oy=oy, oz=oz, dirs=dirs))
    return specs


SPECS = _strand_specs()


def _rot_between(a, b):
    """The smallest rotation taking unit vector a onto unit vector b (3x3)."""
    a, b = np.array(a, float), np.array(b, float)
    v = np.cross(a, b)
    c = float(np.dot(a, b))
    if c < -0.999999:
        return _rot3(0, 0, 180)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def _euler(M):
    """rx, ry, rz in degrees such that rig._rot3(rx, ry, rz) = M (it multiplies Rx @ Ry @ Rz)."""
    b = math.asin(max(-1.0, min(1.0, M[0, 2])))
    c = math.atan2(-M[0, 1], M[0, 0])
    a = math.atan2(-M[1, 2], M[2, 2])
    return tuple(round(math.degrees(v), 3) for v in (a, b, c))


def _strand_rests():
    """The rest rotations of every segment of every vein (the first from straight up to its direction, the others
    relative to the segment before), by parallel transport so the strands do not twist."""
    out = []
    for sp in SPECS:
        up = np.array([0.0, 1.0, 0.0])
        Rw = _rot_between(up, sp["dirs"][0])
        rests = [_euler(Rw)]
        prev = np.array(sp["dirs"][0])
        for k in range(1, N_SEG):
            d = np.array(sp["dirs"][k])
            Rn = _rot_between(prev, d) @ Rw
            rests.append(_euler(Rw.T @ Rn))
            Rw, prev = Rn, d
        out.append(rests)
    return out


REST = _strand_rests()


# ---------------------------------------------------------------- The veins on the eye (painted in 3D)

def _walk(p, h, steps, step, wander, depth, width, out, front_pull=0.12):
    """One vein across the sphere: from p heading h (a tangent), pulled toward the front pole, wandering, now and then
    branching. Appends (points, widths) to out."""
    front = np.array([-1.0, 0.0, 0.0])
    pts, wid = [], []
    for s in range(steps):
        pts.append(p.copy())
        wid.append(width * (1 - 0.35 * s / steps))
        g = front - np.dot(front, p) * p
        gn = np.linalg.norm(g)
        if gn < 1e-6:
            break
        g /= gn
        if math.acos(max(-1, min(1, float(np.dot(front, p))))) < 0.62:       # the iris edge
            break
        side = np.cross(p, h)
        h = h * (1 - front_pull) + g * front_pull + side * float(rng.normal(0, wander))
        h = h - np.dot(h, p) * p
        h /= np.linalg.norm(h)
        p = p + h * step
        p /= np.linalg.norm(p)
        if depth < 2 and s > 3 and rng.random() < 0.05:
            side = np.cross(p, h)
            ang = float(rng.choice([-1, 1]) * rng.uniform(0.5, 1.0))
            h2 = h * math.cos(ang) + side * math.sin(ang)
            _walk(p.copy(), h2, int((steps - s) * 0.7), step, wander * 1.2, depth + 1, width * 0.62, out, front_pull)
    out.append((np.array(pts), np.array(wid)))


def _make_veins():
    out = []
    for i in range(15):
        # start round the back
        ang = float(rng.uniform(0.35, 1.25))
        az = (i / 15 + float(rng.uniform(-0.02, 0.02))) * TAU
        p = np.array([math.cos(ang), math.sin(ang) * math.sin(az), math.sin(ang) * math.cos(az)])
        p /= np.linalg.norm(p)
        h = np.array([-1.0, 0.0, 0.0]) - np.dot([-1.0, 0.0, 0.0], p) * p
        h /= np.linalg.norm(h)
        side = np.cross(p, h)
        h = h + side * float(rng.normal(0, 0.35))
        h /= np.linalg.norm(h)
        _walk(p, h, int(rng.integers(40, 62)), 0.032, 0.20, 0, float(rng.uniform(0.050, 0.062)), out)
    out = [o for o in out if len(o[0]) > 1]
    pts = np.concatenate([o[0] for o in out])
    wid = np.concatenate([o[1] for o in out])
    return pts, wid


VPTS, VWID = _make_veins()


def texel_dirs(ctx):
    """The unit direction from the eye's centre of every texel of the face being painted (h, w, 3), and the radius."""
    model = ctx.part.model
    mats = getattr(model, "_mats", None)
    if mats is None:
        mats = model._mats = part_matrices(model)
    M = mats[id(ctx.part)]
    size = np.array(ctx.part.size, float)
    s = np.broadcast_to(((np.arange(ctx.w) + 0.5) / ctx.w)[None, :], (ctx.h, ctx.w))
    t = np.broadcast_to(((np.arange(ctx.h) + 0.5) / ctx.h)[:, None], (ctx.h, ctx.w))
    C = np.array(_CORNERS[ctx.face], float) * size
    loc = C[3] + (C[2] - C[3]) * s[..., None] + (C[0] - C[3]) * t[..., None]
    world = loc @ M[:3, :3].T + M[:3, 3] - np.array([0.0, EYE_Y, 0.0])
    r = np.linalg.norm(world, axis=-1)
    return world / np.maximum(r, 1e-6)[..., None], r


def _noise(d, seed):
    """A smooth mottle (-1..1) over directions."""
    x, y, z = d[..., 0], d[..., 1], d[..., 2]
    s = seed * 1.7
    return (np.sin(x * 5.1 + s) * np.sin(y * 4.3 + 2 * s) + np.sin(z * 6.2 + 3 * s) * np.sin(x * 3.7 - s)
            + 0.5 * np.sin((x + y + z) * 9.0 + s)) / 2.5


def p_sclera(ctx):
    """The white of the eye: yellowed, mottled, reddening toward the back, lit from above, crossed with bloodshot veins
    that run on from face to face because they are drawn on the sphere, not the box."""
    d, _ = texel_dirs(ctx)
    h, w = ctx.h, ctx.w
    back = np.clip(d[..., 0], 0, 1)                    # 1 at the back
    front = np.clip(-d[..., 0], 0, 1)
    base = np.array(SCLERA, float)[None, None, :] * np.ones((h, w, 1))
    pink = np.array(SCLERA_PINK, float)
    base = base + (pink - base) * (0.10 + 0.55 * back ** 1.5)[..., None]
    base = base + (np.array((236, 232, 214), float) - base) * np.clip(0.45 * _noise(d, 1.0) + 0.1, 0, 1)[..., None] * 0.5
    base = base + (pink - base) * np.clip(0.4 * _noise(d, 5.0), 0, 1)[..., None] * 0.6
    # shade: lit from above, darker underneath and toward the rim of the back
    light = 0.72 + 0.28 * (d[..., 1] * 0.5 + 0.5) + 0.08 * front
    base = base * light[..., None]
    # veins
    flat = d.reshape(-1, 3)
    near = np.full(len(flat), 99.0)
    for i0 in range(0, len(flat), 1024):
        q = flat[i0:i0 + 1024]
        dist = np.sqrt(np.maximum(0, 2 - 2 * (q @ VPTS.T)))
        near[i0:i0 + 1024] = (dist / VWID[None, :]).min(axis=1)
    near = near.reshape(h, w)
    halo = np.clip(1 - near / 3.2, 0, 1) ** 2 * 0.28
    core = np.clip(1.15 - near, 0, 1)
    vein = np.array(VEIN, float)
    dark = np.array(VEIN_DARK, float)
    col = base + (vein * (0.8 + 0.2 * light)[..., None] - base) * halo[..., None]
    col = col + (vein * light[..., None] - col) * np.clip(core * 1.15, 0, 0.92)[..., None]
    col = col + (dark * light[..., None] - col) * (np.clip(core - 0.6, 0, 1) * 0.6)[..., None]
    # a little texel noise
    jit = 1 + (np.array([[ctx.rng.random() for _ in range(w)] for _ in range(h)]) - 0.5) * 0.05
    col = col * jit[..., None]
    px = ctx.img.load()
    for yy in range(h):
        for xx in range(w):
            px[ctx.x + xx, ctx.y + yy] = clamp(col[yy, xx]) + (255,)


def _disc(ctx, fn):
    """Paints a face texel by texel from fn(r, angle) -> colour, r the distance from the middle in half-widths."""
    px = ctx.img.load()
    cx, cy, rad = ctx.w / 2, ctx.h / 2, ctx.w / 2
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
            px[ctx.x + xx, ctx.y + yy] = clamp(fn(math.hypot(dx, dy) / rad, math.atan2(dy, dx))) + (255,)


def p_iris(ctx):
    """The iris on the front face: a dark crimson-brown ring of fibres, a glowing collarette near the pupil, a near-black
    limbus, flecks; the corners of the square are the white of the eye."""
    if ctx.face != "west":
        fill(ctx, SCLERA, 0.03)
        return
    phase = ctx.rng.uniform(0, TAU)
    rng_ = ctx.rng

    def f(r, ang):
        if r > 1.0:
            return mix(SCLERA, VEIN, 0.12 + 0.2 * rng_.random())
        if r > 0.86:
            return mix(LIMBUS, IRIS_DARK, (1.0 - r) / 0.14 * 0.7)
        fib = 0.5 + 0.5 * math.sin(ang * 21 + phase + 2.4 * math.sin(ang * 6 + r * 7))
        c = mix(IRIS_DARK, IRIS, 0.25 + 0.7 * fib)
        c = mix(c, IRIS_HI, max(0.0, 0.55 - r) * 1.1 * fib)
        if 0.36 < r < 0.5:
            c = mix(c, IRIS_FLECK, 0.5)                  # the collarette
        if r < 0.36:
            c = mix(c, IRIS_DARK, 0.4)
        if rng_.random() < 0.05:
            c = mix(c, IRIS_FLECK, 0.5)
        return c
    _disc(ctx, f)


def p_hot(ctx):
    """The hot disc behind the pupil: white-hot in the middle, orange, then red at its rim; outside the circle it is
    transparent (alpha 0), so a square never shows over the iris."""
    px = ctx.img.load()
    if ctx.face != "west":
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)
        return
    cx, cy, rad = ctx.w / 2, ctx.h / 2, ctx.w / 2
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            r = math.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / rad
            if r > 1.0:
                px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)
            else:
                c = mix(HOT_IN, HOT_MID, r / 0.45) if r < 0.45 else mix(HOT_MID, HOT_OUT, (r - 0.45) / 0.55)
                px[ctx.x + xx, ctx.y + yy] = clamp(c) + (255,)


def p_pupil(ctx):
    """The pupil: round and black with a dull ember at its heart (it glows, faintly); the corners are the iris."""
    if ctx.face != "west":
        fill(ctx, PUPIL, 0.02, face_shade=False)
        return
    rng_ = ctx.rng

    def f(r, ang):
        if r > 1.0:
            return mix(IRIS_DARK, IRIS, 0.3 * rng_.random())
        if r > 0.88:
            return mix(PUPIL, IRIS_DARK, 0.5)
        c = mix(EMBER, PUPIL, min(1.0, r / 0.75))
        return c
    _disc(ctx, f)
    if ctx.w >= 6:
        px = ctx.img.load()
        for dx, dy, a in ((2, 2, 0.9), (3, 2, 0.6), (2, 3, 0.6)):
            old = px[ctx.x + dx, ctx.y + dy]
            px[ctx.x + dx, ctx.y + dy] = mix(old[:3], GLINT, a) + (255,)


def p_bulb(ctx):
    """The bulb at the back of the eye where the veins gather: raw wet flesh, dark folds, bright wet highlights."""
    fill(ctx, BULB, 0.07)
    blotch(ctx, BULB_DARK, 4, 1.0, 3.0, 0.5)
    blotch(ctx, BULB_HI, 3, 0.8, 2.0, 0.4)
    if ctx.face == "up":
        speckle(ctx, BULB_HI, 0.12)
    speckle(ctx, shade(BULB, 0.8), 0.06)


def p_strand(ctx):
    """An optic vein: wet red-pink, darker toward the root and paler toward the tip, a dark channel down it and a bright
    wet line along its top."""
    f = ctx.part.tag["f"]
    fill(ctx, mix(STRAND, STRAND_END, f * 0.8), 0.06)
    if ctx.face in ("north", "south", "east", "west") and ctx.w >= 2:
        px = ctx.img.load()
        mid = ctx.w // 2
        for yy in range(ctx.h):
            old = px[ctx.x + mid, ctx.y + yy]
            px[ctx.x + mid, ctx.y + yy] = mix(old[:3], STRAND_DARK, 0.45) + (255,)
        if ctx.w >= 3:
            for yy in range(0, ctx.h, 2):
                old = px[ctx.x, ctx.y + yy]
                px[ctx.x, ctx.y + yy] = mix(old[:3], BULB_HI, 0.35) + (255,)
    if ctx.face == "up":
        speckle(ctx, BULB_HI, 0.3)
    blotch(ctx, STRAND_DARK, 1, 0.8, 1.6, 0.3)


# ---------------------------------------------------------------- The model

def build():
    m = Model(CODE, atlas_width=128, seed=97)

    # A bone to carry everything (nothing drawn); the Center point goes on it
    body = m.part("Body", (-1, EYE_Y - 1, -1), (2, 2, 2), pivot=(0, EYE_Y, 0), faces=())

    # ---- The eye: a rhombicuboctahedron of ten boxes, as the Strider's ----
    c = (0.0, EYE_Y, 0.0)
    s = (R + 2 * A) / 3
    eye = m.part("Eye", (-s, EYE_Y - s, -s), (2 * s, 2 * s, 2 * s), pivot=c, parent=body, paint=p_sclera, glow=10)
    slab_x = ((-R, EYE_Y - A, -A), (2 * R, 2 * A, 2 * A))
    slab_y = ((-A, EYE_Y - R, -A), (2 * A, 2 * R, 2 * A))
    slab_z = ((-A, EYE_Y - A, -R), (2 * A, 2 * A, 2 * R))
    m.part("EyeX", *slab_x, pivot=c, parent=eye, paint=p_sclera, glow=10)
    m.part("EyeY", *slab_y, pivot=c, parent=eye, paint=p_sclera, glow=10)
    m.part("EyeZ", *slab_z, pivot=c, parent=eye, paint=p_sclera, glow=10)
    for name, box, rest in (("EyeXZa", slab_x, (0, 45, 0)), ("EyeXZb", slab_x, (0, -45, 0)),
                            ("EyeXYa", slab_x, (0, 0, 45)), ("EyeXYb", slab_x, (0, 0, -45)),
                            ("EyeYZa", slab_y, (45, 0, 0)), ("EyeYZb", slab_y, (-45, 0, 0))):
        m.part(name, *box, pivot=c, parent=eye, rest=rest, paint=p_sclera, glow=10)

    # The iris, a little proud of the front face, the hot disc on it (shrunk to nothing until the charge), and the pupil
    ir = A * 1.1                                       # half the iris
    m.part("Iris", (FRONT_X - 0.55, EYE_Y - ir, -ir), (0.6, 2 * ir, 2 * ir), pivot=(FRONT_X, EYE_Y, 0), parent=eye, paint=p_iris, glow=45)
    hh = ir * 0.72
    m.part("IrisHot", (FRONT_X - 0.74, EYE_Y - hh, -hh), (0.16, 2 * hh, 2 * hh), pivot=(FRONT_X - 0.66, EYE_Y, 0), parent=eye, paint=p_hot, glow=255)
    ph = ir * 0.46
    m.part("Pupil", (FRONT_X - 0.95, EYE_Y - ph, -ph), (0.4, 2 * ph, 2 * ph), pivot=(FRONT_X - 0.75, EYE_Y, 0), parent=eye, paint=p_pupil, glow=70)

    # ---- The bulb at the back and the optic veins trailing from it ----
    bulb = m.part("Bulb", (BULB_X0, EYE_Y - 5, -5), (BULB_X1 - BULB_X0, 10, 10), pivot=(BULB_X0 + 3, EYE_Y, 0), parent=body, paint=p_bulb)
    for i, sp in enumerate(SPECS):
        y = EYE_Y + sp["oy"]
        z = sp["oz"]
        parent = bulb
        for k in range(N_SEG):
            t = sp["t0"] * (1 - 0.72 * k / (N_SEG - 1))
            length = sp["length"] * (1 - 0.1 * k / (N_SEG - 1))
            part = m.part(f"V{i}_{k}", (STRAND_X - t / 2, y, z - t / 2), (t, length + t * 0.45, t), pivot=(STRAND_X, y, z), parent=parent,
                          rest=REST[i][k], paint=p_strand, faces=("north", "east", "south", "west", "up"), tag={"f": k / (N_SEG - 1)})
            parent = part
            y += length
    return m


# ---------------------------------------------------------------- Animations

SEGS = [f"V{i}_{k}" for i in range(N_STRANDS) for k in range(N_SEG)]
ANIMATED = ["Body", "Eye", "Pupil", "IrisHot"] + SEGS
HOT_OFF = 0.01          # the hot disc's size when it is not lit


def veins(p, sway=1.0, speed=1, stiff=0.0, tremble=0.0, lag=0.10):
    """Poses for the veins: swaying in waves down each strand (p a cycle phase), pulled straight by `stiff` (0 to 1: the
    bend at each joint taken out), shaking by `tremble` degrees."""
    out = {}
    for i in range(N_STRANDS):
        for k in range(N_SEG):
            name = f"V{i}_{k}"
            ph = p * speed + 0.137 * i - lag * k
            amp = sway * (1.4 + 0.9 * k)
            rx = amp * math.sin(TAU * ph)
            rz = amp * 0.8 * math.sin(TAU * (ph + 0.23))
            ry = 0.0
            if k > 0:
                a, b, c = REST[i][k]
                rx -= stiff * a
                ry -= stiff * b
                rz -= stiff * c
            if tremble:
                rx += tremble * math.sin(TAU * (p * 11 + i * 0.31 + k * 0.17))
                rz += tremble * math.sin(TAU * (p * 13 + i * 0.23 - k * 0.11))
            out[name] = pose((rx, ry, rz))
    return out


def frame(body=(0.0, 0.0, 0.0), body_rot=(0, 0, 0), eye=(0, 0, 0), eye_off=(0, 0, 0), pupil=1.0, hot=HOT_OFF, **vk):
    d = {"Body": pose(body_rot, body), "Eye": pose(eye, eye_off), "Pupil": pose(s=(1, pupil, pupil)), "IrisHot": pose(s=(1, hot, hot))}
    d.update(veins(**vk))
    return full(ANIMATED, d)


def animations(m):
    s_ = lambda p, a, sh=0.0: a * math.sin(TAU * (p + sh))

    # Float: a slow bob, a slight roll, the eye drifting a little, the veins trailing and swaying
    m.animation("float", 90, cycle(90, 12, lambda p: frame(
        body=(0, s_(p, 1.3), 0), body_rot=(s_(p, 1.8, 0.25), 0, s_(p, 1.4)), eye=(0, s_(p, 4, 0.2), s_(p, 3, 0.55)),
        pupil=1 + s_(p, 0.06, 0.2), p=p, sway=1.0)))
    # Idle: stiller than the float
    m.animation("idle", 120, cycle(120, 10, lambda p: frame(
        body=(0, s_(p, 0.6), 0), eye=(0, s_(p, 2, 0.3), s_(p, 1.5, 0.6)), pupil=1 + s_(p, 0.04), p=p, sway=0.6)))

    # Scan: the eye sweeps one way and the other, holding at each end; the veins swing after it
    def scan(p):
        yaw = 62 * max(-1.0, min(1.0, 1.35 * math.sin(TAU * p)))
        return frame(body=(0, s_(p, 0.8), 0), body_rot=(0, 0, s_(p, 1.2)), eye=(0, yaw, 3 + s_(p, 3, 0.4)), pupil=1 + s_(p, 0.08, 0.1), p=p, sway=1.2)
    m.animation("scan", 120, cycle(120, 16, scan))

    # Charge (2 s): the pupil contracts, the iris brightens, the eye leans in and rises, the veins stiffen and tremble
    def charge(f):
        s = f / 60.0
        e = s * s * (3 - 2 * s)
        shake = 1.4 * s * math.sin(TAU * f * 0.45)
        return frame(body=(0, 2.2 * e, 0), eye=(shake * 0.5, shake, 2 * e), eye_off=(-1.8 * e, 0, 0), pupil=1 - 0.7 * e,
                     hot=HOT_OFF + (1.05 - HOT_OFF) * s ** 1.6, p=s * 1.5, sway=0.9 * (1 - e) + 0.15, stiff=0.85 * e, tremble=2.4 * s * s)
    m.animation("charge", 60, {f: charge(f) for f in range(0, 60, 3)} | {59: charge(59)}, end="Hold")

    # Beam (held open): the iris white-hot, the pupil a point, the eye thrown back, the veins rigid
    def beam(f):
        s = min(1.0, f / 4.0)
        return frame(body=(0.8 * s, 2.2, 0), eye=(0, 0, 2), eye_off=(-0.4 + 1.6 * s, 0, 0), pupil=0.3 - 0.12 * s, hot=1.1,
                     p=f / 15.0, stiff=0.95, tremble=1.2)
    m.animation("beam", 15, {f: beam(f) for f in range(0, 15, 2)} | {14: beam(14)}, end="Hold")


# ---------------------------------------------------------------- The entity type

def entity():
    import gen_entities as ge
    animations_ = [
        ge.anim("float", "float", triggeredBy={"defaultAnim": True}, blendMode="Average", easeOutSpeed=4),
        ge.anim("idle", "idle"),
        ge.anim("scan", "scan", blendMode="Average", weight=5),
        ge.anim("charge", "charge", weight=10),
        ge.anim("beam", "beam", weight=12),
    ]
    task = {
        "code": "backrooms-watcher", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
        # (Speeds compare with a player's 0.025 walking; it glides at walking speed, in the air above the streets)
        "speed": 0.025, "hoverMin": 4, "hoverMax": 6, "fireRange": 12, "chargeSeconds": 2.0, "beamSeconds": 0.5,
        "searchSeconds": 10, "cooldownSeconds": 4, "loseGraceSeconds": 0.4,
        # Sight only: it sees by the light on someone (a torch, a lit room, a street lamp) as the Strider does, and through
        # glass (but its beam does not go through glass); it has no hearing and no smell
        "senses": {"sightLit": 40, "sightDim": 20, "sightDark": 14, "sightCone": 90, "special": "glass", "hearing": 0,
                   "hearsRunning": False, "sneakFactor": 0.6},
        "scanAnimation": "scan", "chargeAnimation": "charge", "beamAnimation": "beam",
        "humSound": "backrooms:entity/watcher-hum", "chargeSound": "backrooms:entity/watcher-charge",
        "beamSound": "backrooms:entity/watcher-beam", "soundRange": 40,
    }
    client = ge.common_client(f"backrooms:entity/{CODE}", {"base": f"backrooms:entity/{CODE}"}, animations_, step=1.0001, movable=False)
    # No repulsion, no harvest on the client; the eye turns to whatever it is watching (client side)
    client["behaviors"] = [b for b in client["behaviors"] if b["code"] in ("controlledphysics", "interpolateposition")]
    client["behaviors"].append({"code": "backrooms-watchereye"})
    data = {
        "code": CODE,
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "habitat-air"],
        "habitat": "Air",
        "weight": 300,
        # The eye is 2.2 blocks across
        "hitboxSize": {"x": 2.2, "y": 2.4},
        "deadHitboxSize": {"x": 2.2, "y": 2.4},
        "selectionBoxSize": {"x": 2.2, "y": 2.4},
        "eyeHeight": 1.25,
        "attributes": {"killedByInfoText": f"backrooms:deadcreature-{CODE}"},
        "client": client,
        "server": {
            "attributes": {"pathfinder": {"minTurnAnglePerSec": 120, "maxTurnAnglePerSec": 240}},
            "behaviors": [
                {"code": "controlledphysics", "stepHeight": 1.0001},
                # Nothing hurts it and nothing moves it: a blow is only noted
                {"code": "backrooms-menace", "immortal": True, "unmoved": True, "glimpseSeconds": 30, "stalkSeconds": 180, "huntSeconds": 240},
                {"code": "taskai", "aiCreatureType": "Default", "aitasks": [task]},
                {"code": "entitystatetags"},
            ],
        },
        "sounds": {},
    }
    path = os.path.join(rig.ASSETS, "entities", f"{CODE}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent="\t", ensure_ascii=False) + "\n")
    print("wrote", os.path.relpath(path, os.path.join(rig.ROOT)))


# ---------------------------------------------------------------- Sounds

def sounds():
    import gen_entity_sounds as gs
    nrng = np.random.default_rng(9602)
    rate = gs.RATE

    # The hum: a low, beating drone with a faint wet rustle, a few seconds, swelling and fading (played every few seconds
    # near it: it is silent otherwise, and this is all there is of it)
    t = gs.seconds(4.2)
    swell = np.sin(np.pi * t / t[-1]) ** 1.5
    drone = np.sin(TAU * 58 * t) * 0.5 + np.sin(TAU * 58.9 * t) * 0.5 + 0.22 * np.sin(TAU * 116.4 * t + 1.0) + 0.1 * np.sin(TAU * 174 * t)
    wob = 1 + 0.15 * np.sin(TAU * 0.6 * t)
    rustle = gs.band(nrng.normal(size=len(t)), 300, 1400) * (0.5 + 0.5 * np.sin(TAU * 1.7 * t)) * 0.07
    gs.write("watcher-hum", (drone * wob + rustle) * swell, 0.55)

    # The charge: a rising tone over two seconds (the warning and the dodge window), a second voice a fifth above creeping
    # in, a tremolo that quickens, and a swell at the end
    t = gs.seconds(2.0)
    u = t / t[-1]
    f = 220 + 1500 * u ** 2.0
    tone = np.sin(TAU * np.cumsum(f) / rate)
    tone2 = np.sin(TAU * np.cumsum(f * 1.5) / rate) * u
    trem = 0.75 + 0.25 * np.sin(TAU * np.cumsum(5 + 18 * u) / rate)
    sub = np.sin(TAU * 55 * t) * (1 - u) * 0.6
    gs.write("watcher-charge", (tone * 0.6 + tone2 * 0.35) * trem * (0.15 + 0.85 * u ** 1.3) + sub, 0.75)

    # The beam: a hard bright crack, then a searing hiss over a falling tone, and a fine dry crackle of dust
    t = gs.seconds(1.1)
    crack = gs.band(nrng.normal(size=len(t)), 1500, 9000) * np.exp(-t * 28) * 1.0
    hiss = gs.band(nrng.normal(size=len(t)), 2500, 11000) * np.exp(-t * 4.0) * 0.35
    fall = np.sin(TAU * np.cumsum(3400 * np.exp(-t * 1.6) + 300) / rate) * np.exp(-t * 3.0) * 0.5
    boom = np.sin(TAU * 70 * t * (1 - 0.2 * t)) * np.exp(-t * 6) * 0.8
    grit = np.zeros(len(t))
    for _ in range(26):
        at = float(nrng.uniform(0.15, 1.0))
        n = int(0.004 * rate)
        gs.place(grit, nrng.normal(size=n) * np.exp(-np.arange(n) / (0.001 * rate)) * 0.4 * (1 - at / 1.2), at)
    gs.write("watcher-beam", gs.reverb(crack + hiss + fall + boom + grit, 0.25), 0.9)


# ---------------------------------------------------------------- Names

LANG = {
    "item-creature-watcher": "Watcher",
    "prefixandcreature-watcher": "a Watcher",
    "deadcreature-watcher": "Turned to dust by a Watcher",
    "deathmsg-watcher-1": "Player {0} was turned to dust by a Watcher.",
    "deathmsg-watcher-2": "Player {0} looked a Watcher in the eye.",
    "deathmsg-watcher-3": "Player {0} stayed in the light too long.",
}


def merge_lang():
    """Adds the names to lang/en.json without disturbing it: existing keys updated in place, new ones appended after the
    Neighborhood Watch's (as gen_watch.merge_lang does)."""
    path = os.path.join(rig.ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_lines = []
    for key, value in LANG.items():
        entry = "\t" + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^\t" + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda mt: entry + mt.group(1), text, count=1)
        else:
            new_lines.append(entry)
    if new_lines:
        anchor = re.search('^\t"deadcreature-neighborhoodwatch":.*,$', text, re.M)
        if anchor:
            text = text[:anchor.end()] + "\n" + ",\n".join(new_lines) + "," + text[anchor.end():]
        else:
            body = text.rstrip().rpartition("}")[0].rstrip()
            if not body.endswith(",") and not body.endswith("{"):
                body += ","
            text = body + "\n\n" + (",\n").join(new_lines) + "\n}\n"
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    json.loads(text)


def main(args):
    m = build()
    animations(m)
    m.save()
    if "model" in args:
        return
    entity()
    sounds()
    merge_lang()


if __name__ == "__main__":
    main(sys.argv[1:])
