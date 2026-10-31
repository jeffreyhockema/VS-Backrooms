"""The Neighborhood Watch (Entity 96, Level 9): its model, texture, entity type, sounds and names.

Lore (Wikidot, Entity 96 "The Neighborhood Watch", habitat Level 9; the Level 9 page names it the level's most
notable entity, and the other wikis that mention it call it "a giant walking eyeball patrolling the town in search
for prey"). Wikidot gives three forms: Watchers (car-sized eyeballs drifting over the streets, a beam that turns the
living to dust), Striders ("six appendages of about 8 feet, centralized under their main eyeball", the most vigilant,
on rooftops and looking into buildings; they grab and pummel, fast) and Swimmers (dog-sized, in drains and puddles).
They have no hearing and no smell: keen sight and touch are their senses. Advice: stay hidden, do not power
electronics, keep a level head ("it will attempt to trick you"), and if spotted, leave.

This is the Strider, the walking eyeball every source agrees on: a bloodshot eye a block and a quarter across, an
amber iris and a wide black pupil, optic veins standing out over its surface and the optic nerve trailing behind it
like a tail, carried three blocks up on six long jointed legs of pale sinew that meet in a knot of red flesh under the
eye. Too tall for any door: it keeps to the streets and yards and looks in through the windows. The iris and, faintly,
the white of the eye glow, so in the Suburbs' night you see it before it sees you.

Animations: idle (a slow breath, the eye drifting), scan (the eye sweeping the street, the body still), walk (a
tripod gait), run (long fast strides, lower and leaning), stare (the eye lurches at what it has seen, the pupil
narrowing then flaring), peer (crouched at a window, the eye leaning in), attack (the two front legs rise and slam
down), hurt (a flinch, the pupil pinched), die (the legs splay and the eye comes down). The legs are posed by solving
for where the feet are (two-bone IK in each leg's plane), so the feet stay planted while the body moves.

Conventions (rig.py): the model faces -X, its left is +Z, up is +Y, feet at y = 0; a part's rest rotation turns it and
its children; in a leg's own plane (built along -X), +Z rotation turns the outer end down.

Run from the repo root:  python tools/gen_watch.py   (writes the shape, texture, entity type, three sounds, and the
names into lang/en.json)
"""
import json
import math
import os
import re
import sys

import numpy as np

import rig
from rig import Model, pose, mix, shade, clamp, speckle, hlines, vlines
from rig import lit_fill as fill
from gen_models import blotch, line, texel, cycle, full, death

TAU = math.tau
CODE = "neighborhoodwatch"

# ---------------------------------------------------------------- Colours

SCLERA = (224, 218, 200)       # an old, yellowed white
SCLERA_PINK = (214, 178, 168)  # where it reddens toward the back
VEIN = (146, 36, 42)
VEIN_DARK = (92, 22, 30)
VEIN_HI = (178, 70, 70)
IRIS = (178, 128, 50)          # amber
IRIS_DARK = (104, 68, 28)
IRIS_FLECK = (220, 184, 104)
LIMBUS = (52, 36, 22)
PUPIL = (8, 6, 8)
GLINT = (250, 248, 238)
SINEW = (168, 132, 126)        # the legs: pale greyish flesh, fibrous
SINEW_DARK = (112, 74, 74)
JOINT = (182, 150, 142)
TIP = (58, 42, 40)
TIP_HI = (112, 92, 86)
FLESH = (150, 76, 72)          # the knot under the eye: raw, wet
FLESH_DARK = (96, 40, 42)
FLESH_HI = (196, 124, 112)
NERVE = (198, 160, 148)
NERVE_DARK = (138, 98, 94)

# ---------------------------------------------------------------- Geometry

EYE_Y = 38.0                    # the eye's centre
R = 10.0                        # its radius (to its square faces)
A = R / (1 + math.sqrt(2))      # half the side of a face of the rhombicuboctahedron it is built as
Y0 = 26.5                       # the hips
R0 = 3.0                        # how far out from the axis the hips are
LF = 12.0                       # femur
AF = -34.0                      # femur at rest: up and out
AT = 78.0                       # tibia at rest: steeply down and out (absolute, in the leg's plane)
AP = 86.0                       # the point
TL = 5.0                        # the point's length
LEG_YAWS = (30, 90, 150, 210, 270, 330)   # front left, middle left, rear left, rear right, middle right, front right
TRIPOD_A = (0, 2, 4)            # front left, rear left, middle right lift together; then the other three


def _leg_lengths():
    """The tibia's length (so the point reaches the street at rest), and the rest foot's distance out from the axis."""
    ku = R0 + LF * math.cos(math.radians(-AF))
    ky = Y0 + LF * math.sin(math.radians(-AF))
    ay = 0.0 + TL * math.sin(math.radians(AP)) - 0.3      # the ankle's height, for the point's end at y = -0.3
    lt = (ky - ay) / math.sin(math.radians(AT))
    au = ku + lt * math.cos(math.radians(AT))
    fu = au + TL * math.cos(math.radians(AP))
    return lt, (ku, ky), (au, ay), fu


LT, KNEE, ANKLE, FOOT_U = _leg_lengths()
FOOT_Y = -0.3


# ---------------------------------------------------------------- Painters

def _veins(ctx, count, colour=VEIN, alpha=0.75, branch=0.35, length=(0.4, 0.9)):
    """Thin bloodshot veins wandering across a face, branching now and then."""
    rng = ctx.rng
    for _ in range(count):
        # start at an edge, head inward
        edge = rng.randrange(4)
        u, v = [(rng.random(), 0.0), (1.0, rng.random()), (rng.random(), 1.0), (0.0, rng.random())][edge]
        ang = math.atan2(0.5 - v, 0.5 - u) + rng.uniform(-0.8, 0.8)
        total = rng.uniform(*length)
        step = 1.6 / max(ctx.w, ctx.h)
        stack = [(u, v, ang, total, alpha)]
        while stack:
            u, v, ang, left, a = stack.pop()
            while left > 0:
                nu, nv = u + math.cos(ang) * step, v + math.sin(ang) * step
                line(ctx, u, v, nu, nv, colour, a)
                u, v, left = nu, nv, left - step
                ang += rng.uniform(-0.45, 0.45)
                if not (0 <= u <= 1 and 0 <= v <= 1):
                    break
                if rng.random() < branch * step * 3 and a > 0.3:
                    stack.append((u, v, ang + rng.choice((-1, 1)) * rng.uniform(0.5, 1.1), left * 0.5, a * 0.7))


def p_sclera(ctx):
    """The white of the eye: yellowed, faintly mottled, reddening toward the back, crazed with fine veins."""
    back = ctx.part.tag.get("back", 0.0)
    base = mix(SCLERA, SCLERA_PINK, 0.15 + 0.5 * back if ctx.face == "east" else 0.12 + 0.2 * back)
    fill(ctx, base, 0.03)
    blotch(ctx, SCLERA_PINK, 2, 1.5, max(2.0, ctx.w * 0.3), 0.3)
    blotch(ctx, (236, 232, 218), 1, 1.5, max(2.0, ctx.w * 0.25), 0.35)
    # (Bloodshot, not crazed: a few fine veins on each face, more toward the back where the nerve goes in)
    n = int((ctx.w * ctx.h) / 260 * (0.6 + 2.0 * back) + ctx.rng.random())
    _veins(ctx, n, VEIN, 0.4, 0.25, (0.25, 0.6))
    if back > 0.5 and ctx.face == "east":
        _veins(ctx, 2, VEIN_DARK, 0.45, 0.2, (0.3, 0.6))
    speckle(ctx, mix(base, VEIN, 0.25), 0.02)


def p_iris(ctx):
    """The iris on the front face: an amber ring of fibres, a pale collarette near the pupil, a dark limbus, flecks;
    the corners of the square are the white of the eye. Its thin sides are white too."""
    if ctx.face != "west":
        fill(ctx, SCLERA, 0.03)
        return
    px = ctx.img.load()
    cx, cy, rad = ctx.w / 2, ctx.h / 2, ctx.w / 2
    phase = ctx.rng.uniform(0, TAU)
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
            r = math.hypot(dx, dy) / rad
            ang = math.atan2(dy, dx)
            if r > 0.97:
                c = mix(SCLERA, VEIN, 0.18 * ctx.rng.random())
            elif r > 0.84:
                c = mix(LIMBUS, IRIS_DARK, (0.97 - r) / 0.13 * 0.6)
            else:
                fib = 0.5 + 0.5 * math.sin(ang * 17 + phase + 2.2 * math.sin(ang * 5 + r * 6))
                c = mix(IRIS_DARK, IRIS, 0.35 + 0.55 * fib)
                if 0.40 < r < 0.56:
                    c = mix(c, IRIS_FLECK, 0.45)           # the collarette
                if r < 0.42:
                    c = mix(c, IRIS_DARK, 0.5)
                if ctx.rng.random() < 0.05:
                    c = mix(c, IRIS_FLECK, 0.6)
            px[ctx.x + xx, ctx.y + yy] = clamp(c) + (255,)


def p_pupil(ctx):
    """The pupil: round and black (the corners of its square are the iris), with a hard little glint up and to one side."""
    fill(ctx, PUPIL, 0.02, face_shade=False)
    if ctx.face == "west" and ctx.w >= 6:
        px = ctx.img.load()
        rad = ctx.w / 2
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                r = math.hypot(xx + 0.5 - rad, yy + 0.5 - rad) / rad
                if r > 1.0:
                    px[ctx.x + xx, ctx.y + yy] = clamp(mix(IRIS_DARK, IRIS, 0.3 * ctx.rng.random())) + (255,)
                elif r > 0.86:
                    px[ctx.x + xx, ctx.y + yy] = clamp(mix(PUPIL, IRIS_DARK, 0.5)) + (255,)
        texel(ctx, 2, 2, GLINT)
        texel(ctx, 3, 2, GLINT, 0.8)
        texel(ctx, 2, 3, GLINT, 0.8)
        texel(ctx, 3, 3, GLINT, 0.4)
        texel(ctx, -3, -2, (90, 86, 84), 0.6)


def p_vein(ctx):
    """An optic vein standing out of the surface: dark red, lit along its top."""
    fill(ctx, VEIN, 0.06)
    if ctx.face == "up":
        speckle(ctx, VEIN_HI, 0.35)
    elif ctx.face == "down":
        speckle(ctx, VEIN_DARK, 0.4)


def p_nerve(ctx):
    """The optic nerve: a pale rope of fibres trailing from the back of the eye."""
    fill(ctx, NERVE, 0.05)
    if ctx.face in ("north", "south", "east", "west"):
        vlines(ctx, NERVE_DARK, 2, ctx.rng.randrange(2), 0.35, jitter=1)
        line(ctx, 0.3, 0.0, 0.6, 1.0, VEIN, 0.5)
    blotch(ctx, SCLERA_PINK, 1, 1.0, 2.5, 0.3)


def p_flesh(ctx):
    """The knot under the eye where the legs meet: raw red flesh, wet highlights, dark folds."""
    fill(ctx, FLESH, 0.07)
    blotch(ctx, FLESH_DARK, 3, 1.0, 3.0, 0.45)
    blotch(ctx, FLESH_HI, 2, 0.8, 2.0, 0.35)
    if ctx.face not in ("up", "down"):
        hlines(ctx, FLESH_DARK, 3, ctx.rng.randrange(3), 0.35)
    speckle(ctx, FLESH_HI, 0.04)


def p_sinew(ctx):
    """A leg: pale greyish sinew in long fibres down its length, a dark vein running along it."""
    fill(ctx, SINEW, 0.05)
    if ctx.face in ("east", "west"):
        blotch(ctx, SINEW_DARK, 1, 1.0, 2.0, 0.4)
        return
    # the long axis of a leg segment runs across the face (u)
    hlines(ctx, SINEW_DARK, 2, ctx.rng.randrange(2), 0.22)
    if ctx.h >= 4:
        v = ctx.rng.uniform(0.3, 0.7)
        line(ctx, 0.0, v, 1.0, v + ctx.rng.uniform(-0.25, 0.25), VEIN, 0.55)
    blotch(ctx, JOINT, 1, 1.0, 3.0, 0.25)
    speckle(ctx, shade(SINEW, 1.12), 0.03)


def p_joint(ctx):
    """A knuckle of the leg: paler, knobbly."""
    fill(ctx, JOINT, 0.06)
    blotch(ctx, SINEW, 2, 0.8, 1.8, 0.4)
    speckle(ctx, shade(JOINT, 0.85), 0.08)


def p_tip(ctx):
    """The point a leg ends in: dark and hard, paler toward its root."""
    fill(ctx, TIP, 0.06)
    if ctx.face not in ("east", "west"):
        px = ctx.img.load()
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                t = 1 - xx / max(1, ctx.w - 1)       # the root is toward +x (east) on these faces' u
                c = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = mix(c[:3], TIP_HI, 0.35 * (1 - t)) + (255,)


# ---------------------------------------------------------------- The model

def seg(m, name, parent, a, b, t, paint, glow=0, tag=None):
    """A straight box from a to b (model space, the parents unrotated), t thick: a box along +y from a, turned so +y
    points at b (as gen_models.ba_seg), a little longer than the gap so the lengths of a bent strand overlap."""
    d = [b[i] - a[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in d))
    dx, dy, dz = (c / ln for c in d)
    rest = (round(math.degrees(math.atan2(dz, dy)), 3), 0, round(math.degrees(math.asin(max(-1.0, min(1.0, -dx)))), 3))
    return m.part(name, (a[0] - t / 2, a[1] - t / 2, a[2] - t / 2), (t, ln + t * 0.6, t), pivot=a, parent=parent, rest=rest,
                  paint=paint, glow=glow, faces=("north", "east", "south", "west", "up"), tag=tag)


def surface(yaw, pitch, out=0.0):
    """A point on the eye in a direction (yaw from the front toward its left, +Z; pitch up), at its radius plus `out`."""
    y, p = math.radians(yaw), math.radians(pitch)
    d = (-math.cos(p) * math.cos(y), math.sin(p), math.cos(p) * math.sin(y))
    # the eye is no sphere: its faces lie at R, its edges and corners a little further out
    k = R + out + 0.45 * (1 - max(abs(c) for c in d))
    return (d[0] * k, EYE_Y + d[1] * k, d[2] * k)


VEINS = [
    [(170, 40), (125, 55), (75, 46), (36, 25)],
    [(190, -20), (135, -35), (82, -30), (36, -18)],
    [(150, 5), (106, 12), (62, 12), (32, 6)],
    [(-150, 15), (-104, 8), (-60, -5), (-33, -6)],
    [(-172, 52), (-122, 40), (-76, 30), (-38, 21)],
    [(176, -56), (130, -60), (76, -50), (40, -34)],
    [(-160, -40), (-112, -42), (-64, -30), (-36, -22)],
]

NERVE_PTS = [(9.0, EYE_Y - 1.0, 0.0), (13.5, EYE_Y - 2.5, 0.4), (17.0, EYE_Y - 6.0, 1.0), (18.6, EYE_Y - 11.0, 1.4), (18.4, EYE_Y - 15.0, 0.8)]


def build():
    m = Model(CODE, atlas_width=128, seed=96)

    # ---- The knot of flesh under the eye, where the legs meet (the root: it carries the Center point) ----
    body = m.part("Body", (-4.5, 23.5, -4.5), (9, 6.5, 9), pivot=(0, Y0, 0), paint=p_flesh)
    m.part("Stem", (-3.2, 28.5, -3.2), (6.4, 4, 6.4), pivot=(0, 30, 0), parent=body, paint=p_flesh)
    m.part("Under", (-3, 22, -3), (6, 2, 6), pivot=(0, 23, 0), parent=body, paint=p_flesh)

    # ---- The eye: a rhombicuboctahedron of ten boxes (three slabs along the axes, six turned 45 degrees between
    # them, and a core whose corners fill the triangular faces) ----
    c = (0.0, EYE_Y, 0.0)
    s = (R + 2 * A) / 3
    eye = m.part("Eye", (-s, EYE_Y - s, -s), (2 * s, 2 * s, 2 * s), pivot=c, parent=body, paint=p_sclera, glow=24, tag={"back": 0.3})
    slab_x = ((-R, EYE_Y - A, -A), (2 * R, 2 * A, 2 * A))
    slab_y = ((-A, EYE_Y - R, -A), (2 * A, 2 * R, 2 * A))
    slab_z = ((-A, EYE_Y - A, -R), (2 * A, 2 * A, 2 * R))
    m.part("EyeX", *slab_x, pivot=c, parent=eye, paint=p_sclera, glow=24, tag={"back": 0.8})
    m.part("EyeY", *slab_y, pivot=c, parent=eye, paint=p_sclera, glow=24, tag={"back": 0.3})
    m.part("EyeZ", *slab_z, pivot=c, parent=eye, paint=p_sclera, glow=24, tag={"back": 0.3})
    for name, box, rest, back in (("EyeXZa", slab_x, (0, 45, 0), 0.5), ("EyeXZb", slab_x, (0, -45, 0), 0.5),
                                  ("EyeXYa", slab_x, (0, 0, 45), 0.5), ("EyeXYb", slab_x, (0, 0, -45), 0.5),
                                  ("EyeYZa", slab_y, (45, 0, 0), 0.3), ("EyeYZb", slab_y, (-45, 0, 0), 0.3)):
        m.part(name, *box, pivot=c, parent=eye, rest=rest, paint=p_sclera, glow=24, tag={"back": back})

    # The iris, a little proud of the front face, and the pupil on it (stretched by the animations)
    m.part("Iris", (-R - 0.55, EYE_Y - 4.6, -4.6), (0.6, 9.2, 9.2), pivot=(-R, EYE_Y, 0), parent=eye, paint=p_iris, glow=90)
    m.part("Pupil", (-R - 0.85, EYE_Y - 2.3, -2.3), (0.4, 4.6, 4.6), pivot=(-R - 0.65, EYE_Y, 0), parent=eye, paint=p_pupil)

    # Optic veins standing out of the surface, from the back toward the iris
    for i, path in enumerate(VEINS):
        pts = [surface(yw, pt, 0.15) for yw, pt in path]
        for j in range(len(pts) - 1):
            seg(m, f"Vein{i}_{j}", eye, pts[j], pts[j + 1], 1.0 - 0.15 * j, p_vein)

    # The optic nerve, trailing from the back of the eye like a tail
    for j in range(len(NERVE_PTS) - 1):
        seg(m, f"Nerve{j}", eye, NERVE_PTS[j], NERVE_PTS[j + 1], 3.6 - 0.45 * j, p_nerve)

    # ---- The six legs, each built pointing forward (-X) and turned about the axis to its place ----
    for i, yaw in enumerate(LEG_YAWS):
        hip = m.part(f"Hip{i}", (-R0 - 2.2, Y0 - 2.2, -2.2), (4.4, 4.4, 4.4), pivot=(0, Y0, 0), parent=body, rest=(0, yaw, 0), paint=p_joint)
        femur = m.part(f"Femur{i}", (-R0 - LF, Y0 - 1.5, -1.5), (LF + 1, 3, 3), pivot=(-R0, Y0, 0), parent=hip, rest=(0, 0, AF), paint=p_sinew)
        m.part(f"Knee{i}", (-R0 - LF - 1.9, Y0 - 1.9, -1.9), (3.8, 3.8, 3.8), pivot=(-R0 - LF, Y0, 0), parent=femur, rest=(0, 0, 20), paint=p_joint)
        tib = m.part(f"Tibia{i}", (-R0 - LF - LT, Y0 - 1.15, -1.15), (LT + 1, 2.3, 2.3), pivot=(-R0 - LF, Y0, 0), parent=femur,
                     rest=(0, 0, AT - AF), paint=p_sinew)
        xa = -R0 - LF - LT
        m.part(f"Ankle{i}", (xa - 1.3, Y0 - 1.3, -1.3), (2.6, 2.6, 2.6), pivot=(xa, Y0, 0), parent=tib, rest=(0, 0, 30), paint=p_joint)
        m.part(f"Tip{i}", (xa - TL, Y0 - 0.6, -0.6), (TL + 0.6, 1.2, 1.2), pivot=(xa, Y0, 0), parent=tib, rest=(0, 0, AP - AT), paint=p_tip)

    # The light bake (B17): the eye's glowing parts keep their own colours
    m.light = dict(skip=("Iris", "Pupil"))
    return m


# ---------------------------------------------------------------- Legs by where the feet are

def _chain():
    """The rigid knee-to-point chain: its length, and the angle it makes below the tibia's own line."""
    v = (LT * 1.0 + TL * math.cos(math.radians(AP - AT)), -TL * math.sin(math.radians(AP - AT)))
    return math.hypot(*v), -math.atan2(v[1], v[0])


L2, GAMMA = _chain()


def rest_foot(i):
    """Where a foot rests: (x, y, z) in model space."""
    yaw = math.radians(LEG_YAWS[i])
    return (-math.cos(yaw) * FOOT_U, FOOT_Y, math.sin(yaw) * FOOT_U)


def leg_pose(i, foot, body=(0.0, 0.0, 0.0)):
    """The poses of a leg's hip (its turn about the axis), femur and tibia (their bends) that put its point at `foot`
    (model space) with the body moved by `body`: two-bone IK in the leg's plane, knee up."""
    fx, fy, fz = foot[0] - body[0], foot[1] - body[1], foot[2] - body[2]
    yaw = math.degrees(math.atan2(fz, -fx))
    delta = (yaw - LEG_YAWS[i] + 180) % 360 - 180
    u = math.hypot(fx, fz) - R0
    dy = fy - Y0
    d = max(1e-3, min(LF + L2 - 0.01, math.hypot(u, dy)))
    beta = math.atan2(-dy, u)
    c = math.acos(max(-1.0, min(1.0, (LF * LF + d * d - L2 * L2) / (2 * LF * d))))
    af = beta - c
    ku, ky = LF * math.cos(af), -LF * math.sin(af)
    tu, ty = d * math.cos(beta), -d * math.sin(beta)
    av = math.atan2(-(ty - ky), tu - ku)
    at = av - GAMMA
    return {
        f"Hip{i}": pose((0, delta, 0)),
        f"Femur{i}": pose((0, 0, math.degrees(af) - AF)),
        f"Tibia{i}": pose((0, 0, math.degrees(at - af) - (AT - AF))),
    }


def check_rest():
    for i in range(6):
        p = leg_pose(i, rest_foot(i))
        for k, v in p.items():
            assert max(abs(a) for a in v["rot"]) < 0.05, (k, v)


LEG_PARTS = [f"{n}{i}" for i in range(6) for n in ("Hip", "Femur", "Tibia")]
ANIMATED = ["Body", "Eye", "Pupil"] + LEG_PARTS


def frame(body=(0.0, 0.0, 0.0), feet=None, eye=(0, 0, 0), eye_off=(0, 0, 0), pupil=1.0, extra=None):
    """One keyframe: the body moved, the feet where given (else at rest), the eye turned, the pupil sized."""
    d = {"Body": pose((0, 0, 0), body), "Eye": pose(eye, eye_off), "Pupil": pose(s=(1, pupil, pupil))}
    for i in range(6):
        d.update(leg_pose(i, (feet or {}).get(i, rest_foot(i)), body))
    if extra:
        d.update(extra)
    return full(ANIMATED, d)


def gait(p, stride, lift, offset):
    """The feet walking: each foot slides back on the ground for half its cycle and swings forward lifted for the
    other half; the two tripods half a cycle apart."""
    feet = {}
    for i in range(6):
        q = (p + (0.0 if i in TRIPOD_A else 0.5) + offset * (i % 3) * 0.04) % 1.0
        rx, ry, rz = rest_foot(i)
        x = rx - stride * math.cos(TAU * q)            # forward is -x: at q = 0 the foot is furthest forward
        y = ry + lift * max(0.0, -math.sin(TAU * q))
        feet[i] = (x, y, rz)
    return feet


def animations(m):
    s_ = lambda p, a, sh=0.0: a * math.sin(TAU * (p + sh))

    # Idle: a slow breath; the eye drifting, the pupil easing open and shut
    m.animation("idle", 120, cycle(120, 12, lambda p: frame(body=(0, s_(p, 0.4), 0), eye=(s_(p, 2, 0.3), s_(p, 7, 0.1), s_(p, 3, 0.6)),
                                                            pupil=1 + s_(p, 0.06, 0.2))))
    # Scan: the eye sweeps the street one way and the other, holding at each end
    def scan(p):
        yaw = 55 * max(-1.0, min(1.0, 1.35 * math.sin(TAU * p)))
        return frame(body=(0, s_(p, 0.3, 0.25), 0), eye=(0, yaw, 4 + s_(p, 3, 0.4)), pupil=1 + s_(p, 0.08, 0.1))
    m.animation("scan", 120, cycle(120, 16, scan))

    # Walk: a tripod gait, the body bobbing twice a stride, the eye held steady
    m.animation("walk", 40, cycle(40, 10, lambda p: frame(body=(0, 0.7 * math.cos(2 * TAU * p) - 0.3, s_(p, 0.4)), feet=gait(p, 5.0, 4.0, 1),
                                                         eye=(s_(p, 1.5), s_(p, 2), -1.2 * math.cos(2 * TAU * p)))))
    # Run: long fast strides, lower and leaning forward, the eye fixed ahead
    m.animation("run", 24, cycle(24, 8, lambda p: frame(body=(-1.2, -1.8 + 1.0 * math.cos(2 * TAU * p), 0), feet=gait(p, 8.5, 6.5, 0),
                                                       eye=(0, 0, 6 - 1.5 * math.cos(2 * TAU * p)))))

    # Stare: it lurches at what it has seen: the eye thrusts forward, the pupil pinches to a point, then flares wide
    m.animation("stare", 33, {
        0: frame(),
        5: frame(body=(-0.6, 1.2, 0), eye_off=(-1.5, 0.5, 0), pupil=0.45),
        12: frame(body=(-0.8, 1.6, 0), eye=(0, 0, 3), eye_off=(-2.0, 0.6, 0), pupil=0.4),
        20: frame(body=(-0.4, 1.0, 0), eye=(0, 0, 2), eye_off=(-1.2, 0.3, 0), pupil=1.35),
        32: frame(body=(-0.2, 0.4, 0), eye=(0, 0, 1), eye_off=(-0.4, 0, 0), pupil=1.25),
    }, end="Stop")

    # Peer: crouched low at a window, the eye leaning in and tilting, the pupil wide
    def peer(p):
        return frame(body=(-1.0, -6.0 + s_(p, 0.3), 0), eye=(s_(p, 6), s_(p, 5, 0.25), 9 + s_(p, 2, 0.5)), eye_off=(-1.6, 0, 0), pupil=1.3 + s_(p, 0.08))
    m.animation("peer", 80, cycle(80, 8, peer))

    # Attack: the front pair of legs rise high before the eye, then slam down together, the body lunging after them
    def front(raise_, out, body):
        feet = {}
        for i in (0, 5):
            rx, ry, rz = rest_foot(i)
            feet[i] = (rx - out, ry + raise_, rz * 0.55)
        return frame(body=body, feet=feet, eye=(0, 0, 4 if raise_ < 5 else -4), pupil=0.7 if raise_ > 5 else 1.1)
    m.animation("attack", 27, {
        0: frame(),
        8: front(26.0, 6.0, (1.0, 1.5, 0)),
        12: front(30.0, 8.0, (1.4, 2.0, 0)),
        15: front(0.0, 12.0, (-2.5, -2.0, 0)),
        20: front(0.0, 11.0, (-2.0, -1.6, 0)),
        26: frame(),
    }, end="Stop")

    # Hurt: it flinches: the body jerks back and sinks, the eye rolls up, the pupil pinches
    m.animation("hurt", 15, {
        0: frame(),
        3: frame(body=(1.6, -1.4, 0), eye=(4, -6, -14), eye_off=(0.8, 0, 0), pupil=0.5),
        9: frame(body=(0.8, -0.8, 0), eye=(2, -3, -7), pupil=0.75),
        14: frame(),
    }, end="Stop")

    # Die: a hit (the eye jerks, the pupil pinches), the legs buckle one after another with the feet planted, the hub
    # sinks between them and the eye comes down onto the floor; it rolls over to stare at the ceiling, and the legs go
    # slack: the points slide out and curl in, each leg folded differently, knees arched, the eye lying on the floor.
    # Where each foot ends: (yaw turned from its place, distance out from the axis, height of the point)
    ends = {0: (-16, 24, 0.0), 1: (12, 34, 0.0), 2: (24, 18, 0.0), 3: (-24, 30, 0.0), 4: (10, 25, 0.0), 5: (-34, 39, 0.0)}
    order = (0, 5, 1, 4, 2, 3)
    HUB = 6.0                                           # where the hub ends up: the eye (1.5 above it) on the floor

    def slump(k, eye, pupil, eye_dy=0.0, eye_dx=0.0, out=1.0):
        """k 0..1: how far the legs have gone (staggered by `order`), the hub following them down onto the floor."""
        kb = k * k * (3 - 2 * k) if k < 1 else 1.0
        body = (0.0, -(Y0 - HUB) * kb, 0.0)
        feet = {}
        for i in range(6):
            kk = min(1.0, max(0.0, k * 1.5 - order.index(i) * 0.1))
            kk = kk * kk * (3 - 2 * kk)
            rx, ry, rz = rest_foot(i)
            dyaw, r, y = ends[i]
            yaw = math.radians(LEG_YAWS[i] + dyaw * kk * out)
            r = FOOT_U + (r - FOOT_U) * kk * out
            feet[i] = (-math.cos(yaw) * r, FOOT_Y + (y - FOOT_Y) * kk, math.sin(yaw) * r)
        # the eye's offset is inside its own turn: turn the wanted world move (down onto the floor) back through it
        local = rig._rot3(*eye).T @ np.array([eye_dx, -(HUB + 1.5) * kb + eye_dy, 0.0])
        return frame(body=body, feet=feet, eye=eye, eye_off=tuple(round(float(v), 3) for v in local), pupil=pupil)

    die_keys = {
        0: frame(),
        3: slump(0.0, (0, 0, -8), 0.45, 0.5, -1.0),
        8: slump(0.3, (0, 0, -16), 0.6, 0.3, -0.5),
        14: slump(0.7, (6, 0, -30), 1.3),
        20: slump(1.0, (100, 8, -30), 1.7, 0.0, 0.0, out=1.12),
        26: slump(1.0, (94, 5, -24), 1.5, 0.0, 0.0, out=1.04),
        32: slump(1.0, (98, 8, -28), 1.7, 0.0, 0.0, out=1.0),
        39: slump(1.0, (100, 9, -30), 1.75, 0.0, 0.0, out=1.0),
    }
    death(m, 40, ANIMATED, die_keys, standing=(3,), soft=[f"Nerve{j}" for j in range(len(NERVE_PTS) - 1)])


# ---------------------------------------------------------------- The entity type

def entity():
    import gen_entities as ge
    animations_ = ge.model_anims(
        ge.anim("scan", "scan", blendMode="Average"),
        ge.anim("stare", "stare", weight=10),
        ge.anim("peer", "peer"),
    )
    task = {
        "code": "backrooms-watch", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
        # (Speeds compare with a player's 0.025 walking and 0.05 sprinting; Level 9's danger adds a quarter)
        "walkSpeed": 0.016, "runSpeed": 0.044,
        # What it sees by (the shared perception, Perception.cs): someone in the dark within 12 blocks, someone in light
        # (a torch, a lit room, a working street lamp, a fire) within 40; a crouch shrinks both to 0.6; anything within
        # 2.5 it feels. Its gaze is a cone of 70 degrees either way (scanHalfAngle, 100, while it sweeps the street);
        # glass does not stop it; no hearing and no smell. The Watch reckons light by lamps and fires only, not the sky.
        "senses": {"sightLit": 40, "sightDim": 12, "sightDark": 12, "sightCone": 70, "touch": 2.5, "sneakFactor": 0.6,
                   "hearing": 0, "hearsRunning": False, "special": "glass"},
        "scanHalfAngle": 100,
        # What fears it (Hounds, Smilers, Skin-Stealers and Deathmoths, Wikidot) within this many blocks goes to Leave
        "fearRange": 24,
        "noticeSeconds": 1.6, "loseSeconds": 3.0, "searchSeconds": 14, "feintSeconds": 16, "peerSeconds": 40,
        "damage": 6.5, "damageTier": 2, "damageType": "BluntAttack", "knockback": 0.9, "attackRange": 1.7,
        "attackDurationMs": 900, "damageAtMs": 500, "attackCooldownMs": 1900, "retreatBelow": 0.3,
        "walkAnimation": "walk", "runAnimation": "run", "attackAnimation": "attack", "scanAnimation": "scan",
        "stareAnimation": "stare", "stareMs": 1100, "peerAnimation": "peer",
        "noticeSound": "backrooms:entity/watch-notice", "attackSound": "backrooms:entity/watch-slam",
        "tapSound": "backrooms:entity/watch-tap", "soundRange": 32,
    }
    tasks = [task, ge.idle("scan", 1.2, 5000, 9000, 6000, 20000), dict(ge.WANDER, movespeed=0.006), ge.LOOKAROUND]
    client = ge.common_client(f"backrooms:entity/{CODE}", {"base": f"backrooms:entity/{CODE}"}, animations_, step=1.1251)
    # The eye turns to whatever it is watching (client side, from what the server says it watches)
    client["behaviors"].append({"code": "backrooms-watcheye"})
    data = {
        "code": CODE,
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "habitat-land"],
        "weight": 260,
        # The eye's top is at 48 px (3 blocks), its legs spread 2.4 blocks: too tall for any door
        "hitboxSize": {"x": 1.4, "y": 2.9},
        "deadHitboxSize": {"x": 1.6, "y": 0.9},
        "selectionBoxSize": {"x": 1.6, "y": 3.0},
        "eyeHeight": 2.4,
        "attributes": {"killedByInfoText": f"backrooms:deadcreature-{CODE}"},
        "client": client,
        "server": ge.server(30, tasks, None, menace={"glimpseSeconds": 30, "stalkSeconds": 180, "huntSeconds": 240, "rangedDamageMul": 2}),
        "sounds": {"hurt": "game:effect/squish*", "death": "backrooms:effect/squelch"},
    }
    ge.sync_harvestable(data)
    path = os.path.join(rig.ASSETS, "entities", f"{CODE}.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent="\t", ensure_ascii=False) + "\n")
    print("wrote", os.path.relpath(path, os.path.join(rig.ROOT)))


# ---------------------------------------------------------------- Sounds

def sounds():
    import gen_entity_sounds as gs
    rng = np.random.default_rng(9601)
    rate = gs.RATE

    # Noticed: a wet click as the eye turns in its socket, and a thin tone rising under it, like a lens focusing
    t = gs.seconds(1.3)
    out = np.zeros(len(t))
    click = gs.band(rng.normal(size=int(0.05 * rate)), 600, 5000) * np.exp(-np.arange(int(0.05 * rate)) / (0.006 * rate))
    gs.place(out, click * 0.9, 0.02)
    gs.place(out, click * 0.6, 0.11)
    squelch = gs.band(rng.normal(size=int(0.35 * rate)), 120, 900) * np.exp(-np.arange(int(0.35 * rate)) / (0.09 * rate))
    gs.place(out, squelch * 0.5, 0.05)
    f = 1800 + 1700 * (t / t[-1]) ** 1.6
    tone = np.sin(TAU * np.cumsum(f) / rate) * np.minimum(1, t / 0.4) * np.exp(-np.maximum(0, t - 0.9) * 8) * 0.22
    tone += 0.08 * np.sin(TAU * np.cumsum(f * 1.5) / rate) * np.minimum(1, t / 0.6)
    gs.write("watch-notice", out + tone, 0.7)

    # The slam: two long legs come down together, a heavy blow on asphalt
    out = np.zeros(int(1.0 * rate))
    gs.place(out, gs.thud(0.5, 52, rng, 0.9), 0.0)
    gs.place(out, gs.thud(0.45, 61, rng, 0.7) * 0.8, 0.035)
    grit = gs.band(rng.normal(size=int(0.4 * rate)), 800, 6000) * np.exp(-np.arange(int(0.4 * rate)) / (0.05 * rate)) * 0.3
    gs.place(out, grit, 0.01)
    gs.write("watch-slam", gs.reverb(out, 0.25), 0.85)

    # At the window: the point of a leg tapping on the glass, three times, unhurried
    out = np.zeros(int(2.4 * rate))
    for i, at in enumerate((0.05, 0.62, 1.38)):
        n = int(0.12 * rate)
        tap = gs.band(rng.normal(size=n), 1800, 9000) * np.exp(-np.arange(n) / (0.004 * rate))
        ring = np.sin(TAU * (3100 + 140 * i) * np.arange(n) / rate) * np.exp(-np.arange(n) / (0.03 * rate)) * 0.35
        gs.place(out, (tap + ring) * (0.85 + 0.15 * (i % 2)), at)
    gs.write("watch-tap", out, 0.6)

    # Heard from a street or two over: the points of six legs on asphalt, quick and uneven, then nothing
    out = np.zeros(int(3.0 * rate))
    at = 0.05
    for i in range(14):
        n = int(0.06 * rate)
        tick = gs.band(rng.normal(size=n), 1200, 7000) * np.exp(-np.arange(n) / (0.005 * rate))
        gs.place(out, tick * rng.uniform(0.5, 1.0), at)
        at += rng.uniform(0.07, 0.24) if i % 3 else rng.uniform(0.25, 0.4)
    gs.write("watch-steps", gs.reverb(out, 0.5), 0.55)


# ---------------------------------------------------------------- Names

LANG = {
    "item-creature-neighborhoodwatch": "Strider of the Neighborhood Watch",
    "prefixandcreature-neighborhoodwatch": "a Strider of the Neighborhood Watch",
    "deadcreature-neighborhoodwatch": "Seen by a Strider of the Neighborhood Watch",
}


def merge_lang():
    """Adds the names to lang/en.json without disturbing it: existing keys updated in place, new ones appended (as
    gen_entities.merge_lang)."""
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
        # (Beside the other creatures' names, after the Wretch's, rather than at the end where everything else goes)
        anchor = re.search('^\t"deadcreature-wretch":.*,$', text, re.M)
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
    check_rest()
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
