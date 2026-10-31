"""Level 120: the Misglitch (Wikidot Level 120, "Broken Servos"). Writes shapes/entity/120/l120-misglitch.json and two
textures with the same atlas: l120-misglitch.png (red marks where the victim died) and l120-misglitch-black.png (an
internal death: all black). Entity json and lang are written elsewhere.

A gaunt, slightly stooped black humanoid about 1.9 blocks tall (30 px), the corrupted copy of a person, surrounded by
bright pixel cubes. Its right arm is the weapon: from the elbow a tapering tentacle of six segments, each a child of the
last, ending in a point, 22.3 px (1.39 blocks) from the shoulder when straight.

Rig conventions (rig.py): faces -X, left is +Z. +Z rotation leans a torso forward / swings a hanging limb back (-Z swings
it forward); +Y on the chest brings the right shoulder forward; +X on a hanging left limb swings it inward.
"""
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(__file__))
import rig  # noqa: E402
from rig import Model, pose  # noqa: E402

TAU = math.tau
NAME = "120/l120-misglitch"
BLACK_TEX = "l120-misglitch-black"
BASE = (8, 8, 10)
DEAD = [(0, 255, 255), (255, 0, 255), (40, 255, 60), (255, 255, 255), (255, 230, 0), (60, 80, 255)]
RED_DARK, RED_MID, RED_BRIGHT = (60, 3, 5), (130, 5, 8), (215, 12, 16)

# (name, parent, centre x, y, z, size, colour). The floating ones sit 2-5 px off the body; "PxS" ones sit on its surface.
PIX = [
    ("PxF1", "Chest", (-1.0, 26.0, 7.8), 1.2, (0, 255, 255)),
    ("PxF2", "Chest", (2.0, 22.0, -8.2), 1.0, (255, 0, 255)),
    ("PxF3", "Chest", (-5.2, 23.0, 3.0), 1.4, (40, 255, 60)),
    ("PxF4", "Chest", (4.6, 27.0, -2.0), 0.9, (255, 255, 255)),
    ("PxF5", "Head", (-5.0, 31.0, 2.5), 1.0, (255, 0, 255)),
    ("PxF6", "Head", (3.2, 33.0, -3.0), 0.8, (0, 255, 255)),
    ("PxF7", "Head", (-1.0, 34.0, 4.2), 1.1, (255, 230, 0)),
    ("PxF8", "Pelvis", (-4.2, 17.0, 5.5), 1.2, (40, 255, 60)),
    ("PxF9", "Pelvis", (3.6, 12.0, -6.0), 1.0, (0, 255, 255)),
    ("PxF10", "Pelvis", (-5.0, 10.0, -3.0), 1.3, (60, 90, 255)),
    ("PxF11", "Pelvis", (4.2, 19.0, 6.6), 0.9, (255, 255, 255)),
    ("PxF12", "Chest", (-5.6, 20.0, -6.2), 0.8, (255, 0, 255)),
    ("PxS1", "Chest", (-2.55, 23.0, 1.5), 1.1, (0, 255, 255)),
    ("PxS2", "Head", (-0.5, 28.6, 2.35), 1.0, (255, 0, 255)),
    ("PxS3", "ThighL", (-1.95, 10.0, 1.9), 0.9, (40, 255, 60)),
    ("PxS4", "Waist", (2.05, 18.0, -1.0), 1.0, (255, 255, 255)),
]
PIXN = [p[0] for p in PIX]
CENTRE = (0.0, 20.0, 0.0)


def _dir(c):
    v = [c[i] - CENTRE[i] for i in range(3)]
    n = math.sqrt(sum(a * a for a in v)) or 1.0
    return tuple(a / n for a in v)


DIRS = {p[0]: _dir(p[2]) for p in PIX}
SEGS = [("TentR1", 3.8, 1.9), ("TentR2", 3.4, 1.6), ("TentR3", 3.0, 1.3), ("TentR4", 2.6, 1.0), ("TentR5", 1.8, 0.7), ("TentTip", 1.2, 0.45)]
SEGN = [s[0] for s in SEGS]
TENT_REST = [-4, -6, -8, -8, -8, -6]
LEGS = ["ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR"]


# ---------------- Painters ----------------

def _put(ctx, px, x, y, c):
    if 0 <= x < ctx.w and 0 <= y < ctx.h:
        px[ctx.x + x, ctx.y + y] = tuple(int(max(0, min(255, v))) for v in c) + (255,)


def _get(ctx, px, x, y):
    return px[ctx.x + max(0, min(ctx.w - 1, x)), ctx.y + max(0, min(ctx.h - 1, y))][:3]


def _slash(ctx, px, rg, u0, v0, u1, v1, wd):
    x0, y0, x1, y1 = u0 * ctx.w, v0 * ctx.h, u1 * ctx.w, v1 * ctx.h
    n = max(2, int(max(abs(x1 - x0), abs(y1 - y0)) * 2))
    for i in range(n + 1):
        t = i / n
        x, y = int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t)
        core = rig.mix(RED_BRIGHT, RED_MID, rg.random() * 0.6 + 0.4 * abs(t - 0.5) * 2)
        _put(ctx, px, x, y, core)
        for dx, dy in ((0, 1), (1, 0)):
            if rg.random() < 0.55:
                _put(ctx, px, x + dx, y + dy, RED_DARK if rg.random() < 0.7 else RED_MID)
        if wd > 0.9 and rg.random() < 0.5:
            _put(ctx, px, x - 1, y, RED_DARK)


def _blot(ctx, px, rg, u, v, r):
    cx, cy = u * ctx.w, v * ctx.h
    rx, ry = max(1.2, r * ctx.w), max(1.2, r * ctx.h)
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            d = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 + (rg.random() - 0.5) * 0.7
            if d < 0.45:
                _put(ctx, px, xx, yy, rig.mix(RED_BRIGHT, RED_MID, rg.random() * 0.5))
            elif d < 1.0:
                _put(ctx, px, xx, yy, RED_MID if rg.random() < 0.6 else RED_DARK)
            elif d < 1.4 and rg.random() < 0.5:
                _put(ctx, px, xx, yy, rig.mix(_get(ctx, px, xx, yy), RED_DARK, 0.6))


def _drip(ctx, px, rg, u, v, ln):
    x = int(u * ctx.w)
    y0 = int(v * ctx.h)
    n = max(2, int(ln * ctx.h))
    for i in range(n):
        t = i / max(1, n - 1)
        _put(ctx, px, x, y0 + i, rig.mix(RED_MID, RED_DARK, t * 0.8))
    _put(ctx, px, x, y0 + n, RED_BRIGHT)


MARKS = {
    ("Chest", "west"): [("slash", .15, .1, .85, .75, 1.0), ("slash", .3, .05, .95, .5, .8), ("blot", .55, .5, .22), ("drip", .55, .6, .35), ("drip", .3, .4, .3)],
    ("Chest", "south"): [("blot", .35, .35, .2), ("drip", .35, .45, .4)],
    ("Neck", "south"): [("blot", .5, .5, .4), ("drip", .5, .7, .3)],
    ("Head", "south"): [("slash", .2, .2, .8, .7, 1.0), ("blot", .55, .55, .22), ("drip", .55, .65, .5)],
    ("Head", "west"): [("slash", .7, .0, .95, .5, .6)],
    ("ThighL", "west"): [("slash", .1, .15, .9, .6, 1.0), ("blot", .5, .5, .25), ("drip", .5, .6, .4)],
    ("ThighL", "south"): [("slash", .2, .1, .8, .5, .8), ("drip", .5, .5, .4)],
}


def make_body(red):
    def body(ctx):
        """Near-black with a fine noise of dark greys, sparse dead-pixel texels, scanline tears, and (red) wound marks."""
        px = ctx.img.load()
        rng = ctx.rng
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                v = 6 + rng.random() * 8
                if rng.random() < 0.07:
                    v += rng.random() * 10
                c = (v, v, v + rng.random() * 2)
                if rng.random() < 0.013:
                    c = rng.choice(DEAD)
                _put(ctx, px, xx, yy, c)
        for yy in range(ctx.h):
            if rng.random() < 0.08 and ctx.w > 2:
                x0 = rng.randrange(ctx.w)
                x1 = rng.randint(x0, ctx.w - 1)
                sh = rng.choice((-2, -1, 1, 2))
                tone = rng.choice((10, -4, 14))
                row = [_get(ctx, px, xx, yy) for xx in range(ctx.w)]
                for xx in range(x0, x1 + 1):
                    src = row[(xx - sh) % ctx.w]
                    _put(ctx, px, xx, yy, (src[0] + tone, src[1] + tone, src[2] + tone))
        if red:
            rg = random.Random(f"{ctx.part.name}-{ctx.face}")
            for op in MARKS.get((ctx.part.name, ctx.face), []):
                if op[0] == "slash":
                    _slash(ctx, px, rg, *op[1:])
                elif op[0] == "blot":
                    _blot(ctx, px, rg, *op[1:])
                else:
                    _drip(ctx, px, rg, *op[1:])
    return body


def make_pixel(col):
    def pixel(ctx):
        px = ctx.img.load()
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                k = 0.9 + 0.1 * ctx.rng.random() if ctx.face != "down" else 0.7
                _put(ctx, px, xx, yy, tuple(v * k for v in col))
    return pixel


# ---------------- The model ----------------

LIGHT = dict(floor=12.0, ground=0.0, grad=0.25, edge=0.05, foot=0.03, drift=0.0, round=0.15)


def build(red=True):
    m = Model(NAME, atlas_width=48, seed=120)
    m.light = dict(LIGHT)
    body = make_body(red)
    pelvis = m.part("Pelvis", (-2, 13, -3.5), (4, 3, 7), pivot=(0, 14.5, 0), paint=body)
    thigh = m.part("ThighL", (-1.8, 6.8, 0.4), (3.4, 7.2, 3.2), pivot=(0, 13.8, 2.0), parent=pelvis, rest=(0, 0, 0), paint=body)
    shin = m.part("ShinL", (-1.4, 1.4, 0.6), (2.8, 5.6, 2.8), pivot=(0, 7.0, 2.0), parent=thigh, paint=body)
    m.part("FootL", (-4.2, 0, 0.5), (5.6, 1.5, 3), pivot=(0, 1.6, 2.0), parent=shin, paint=body)
    m.mirror("ThighL", "ThighR")
    waist = m.part("Waist", (-2, 16, -3.2), (4, 4, 6.4), pivot=(0, 16, 0), parent=pelvis, rest=(0, 0, 3), paint=body)
    chest = m.part("Chest", (-2.4, 20, -4.2), (4.8, 5.5, 8.4), pivot=(0, 20, 0), parent=waist, rest=(0, 0, 4), paint=body)
    neck = m.part("Neck", (-1, 25.3, -1), (2, 2, 2), pivot=(0, 25.3, 0), parent=chest, rest=(0, 0, 10), paint=body)
    m.part("Head", (-2.3, 26.8, -2.1), (4.6, 4.6, 4.2), pivot=(0, 27, 0), parent=neck, rest=(7, 0, -4), paint=body)
    # Left arm: thin, human-length, hanging to the knee
    arm = m.part("ArmL", (-1.1, 17.5, 4.3), (2.2, 7, 2.2), pivot=(0, 24.3, 5.4), parent=chest, rest=(-3, 0, 0), paint=body)
    fore = m.part("ForearmL", (-1, 11.2, 4.4), (2, 6.5, 2), pivot=(0, 17.7, 5.4), parent=arm, rest=(0, 0, -4), paint=body)
    m.part("HandL", (-0.9, 8.8, 4.3), (1.8, 2.6, 2.2), pivot=(0, 11.4, 5.4), parent=fore, paint=body)
    # Right arm: the upper arm, then the tentacle
    last = m.part("ArmR", (-1.1, 17.8, -6.5), (2.2, 6.5, 2.2), pivot=(0, 24.3, -5.4), parent=chest, rest=(0, 0, 0), paint=body)
    y = 17.8
    for (name, ln, w), rz in zip(SEGS, TENT_REST):
        last = m.part(name, (-w / 2, y - ln, -5.4 - w / 2), (w, ln, w), pivot=(0, y, -5.4), parent=last, rest=(0, 0, rz), paint=body)
        y -= ln
    for name, parent, c, sz, col in PIX:
        glow = 160 if name.startswith("PxF") else 190
        m.part(name, (c[0] - sz / 2, c[1] - sz / 2, c[2] - sz / 2), (sz, sz, sz), parent=parent, paint=make_pixel(col), glow=glow, tag={"occlude": False})
    return m


# ---------------- Animation helpers ----------------

def s(phase, amp, shift=0.0):
    return amp * math.sin(TAU * (phase + shift))


def plus(d, delta):
    """A pose dict with `delta` (pose dicts) added on (rotations and offsets)."""
    out = {k: dict(v) for k, v in d.items()}
    for k, v in delta.items():
        a = out.get(k, pose())
        out[k] = pose(tuple(a["rot"][i] + v["rot"][i] for i in range(3)), tuple(a["off"][i] + v["off"][i] for i in range(3)),
                      a.get("str", v.get("str")))
    return out


def blend(a, b, t):
    out = {}
    for k in set(a) | set(b):
        pa, pb = a.get(k, pose()), b.get(k, pose())
        out[k] = pose(tuple(pa["rot"][i] + (pb["rot"][i] - pa["rot"][i]) * t for i in range(3)),
                      tuple(pa["off"][i] + (pb["off"][i] - pa["off"][i]) * t for i in range(3)))
    return out


def drift(f, frames, amp=0.8, jit=0.0, scatter=0.0):
    """Pixel cubes' offsets: slow orbit in whole cycles, now and then a one-frame jump, and a scatter outward."""
    p = f / frames
    out = {}
    for i, name in enumerate(PIXN):
        a = amp if name.startswith("PxF") else amp * 0.18
        k = 1 + i % 3
        o = [a * math.sin(TAU * (k * p + i * 0.37)), a * math.sin(TAU * (k * p + i * 0.61 + 0.2)), a * math.sin(TAU * (k * p + i * 0.13 + 0.5))]
        if jit:
            rg = random.Random(f * 977 + i * 31)
            if rg.random() < jit:
                j = 1.2 if name.startswith("PxF") else 0.4
                o = [v + rg.uniform(-j, j) for v in o]
        if scatter:
            d = DIRS[name]
            sc = scatter if name.startswith("PxF") else scatter * 0.5
            o = [o[a_] + d[a_] * sc for a_ in range(3)]
        out[name] = pose((0, 0, 0), tuple(o))
    return out


def tent(rots, arm=None, sway=None):
    """Tentacle segment poses from a list of z rotations (six), plus an optional y sway list."""
    out = {}
    for i, n in enumerate(SEGN):
        out[n] = pose((0, sway[i] if sway else 0, rots[i]))
    return out


def keys_from(fn, frames, step, glitches=None):
    """Keyframes of fn(frame) every `step` frames, and the glitch frames (consecutive keys, one frame apart) with their
    deltas added, the frames either side of a glitch sampled plain so it snaps."""
    glitches = glitches or {}
    fr = set(range(0, frames, step)) | set(glitches)
    for g in list(glitches):
        for q in (g - 1, g + 1):
            if 0 <= q < frames and q not in glitches:
                fr.add(q)
    keys = {}
    for f in sorted(fr):
        d = fn(f)
        if f in glitches:
            d = plus(d, glitches[f])
        keys[f] = d
    return keys


# ---------------- Animations ----------------

def animations(m):
    # ---- idle: 4 s
    def idle(f):
        p = f / 120
        breath = 0.5 - 0.5 * math.cos(TAU * 2 * p)
        d = {
            "Pelvis": pose((s(p, 1.2), 0, 0), (0, 0, s(p, 0.3))),
            "Waist": pose((s(p, -0.8), 0, 0.8 * breath)),
            "Chest": pose((0, s(p, 2, 0.16), 1.2 * breath), (0, 0, 0), (1, 1 + 0.012 * breath, 1 + 0.02 * breath)),
            "Neck": pose((s(p, 1, 0.0), 0, s(p, 1.5, 0.08))),
            "Head": pose((s(p, 6), s(p, 8, 0.24), 2 + s(p, 3, 0.0) * 1 + s(p * 2, 2))),
            "ArmL": pose((1.5 * math.sin(TAU * p + 1), 0, 2 * math.sin(TAU * 2 * p))),
            "ForearmL": pose((0, 0, -3 - 2 * breath)), "HandL": pose((0, 0, -3 * math.sin(TAU * p))),
            "ArmR": pose((1, 0, -3 + s(p, 2, 0.3))),
            "ThighL": pose((0, 0, -2)), "ThighR": pose((0, 0, -2)), "ShinL": pose((0, 0, 3)), "ShinR": pose((0, 0, 3)),
            "FootL": pose((0, 0, -1)), "FootR": pose((0, 0, -1)),
        }
        cur = [0.5 - 0.5 * math.cos(TAU * (p - 0.07 * i)) for i in range(6)]
        d.update(tent([-(2 + 9 * c) for c in cur], sway=[s(p, 6, -0.1 * i) for i in range(6)]))
        d.update(drift(f, 120, 0.8, 0.12))
        return d

    G = {
        31: {"Head": pose((0, 45, 10)), "Chest": pose(o=(0, 0, 1.8)), **{n: pose(o=(0, 0, 2.2 * DIRS[n][2])) for n in PIXN[:6]}},
        32: {"Head": pose((0, -30, -8)), "ArmL": pose((0, 0, -35)), "Chest": pose(o=(0, 0, -1.5))},
        84: {"ArmR": pose((0, 0, 25)), "TentR2": pose((0, 0, 30)), "Pelvis": pose(o=(1.2, 0, 0)), "Waist": pose((0, 12, 0))},
        85: {"TentR3": pose((0, 0, -40)), "Chest": pose((0, 0, 8), (0, 1, 0)), "ThighL": pose((0, 0, -18))},
    }
    m.animation("idle", 120, keys_from(idle, 120, 6, G))

    # ---- lurk: 3 s, slumped, head hanging, tentacle limp on the floor, tiny twitches
    def lurk(f):
        p = f / 90
        breath = 0.5 - 0.5 * math.cos(TAU * p)
        rg = random.Random(f * 53)
        tw = (rg.random() < 0.25)
        d = {
            "Pelvis": pose((0, 0, 4), (0, -1.2, 0)),
            "ThighL": pose((0, 0, -14)), "ThighR": pose((0, 0, -14)), "ShinL": pose((0, 0, 14)), "ShinR": pose((0, 0, 14)),
            "FootL": pose((0, 0, 0)), "FootR": pose((0, 0, 0)),
            "Waist": pose((0, 0, 8)), "Chest": pose((0, 0, 14 + 1.2 * breath)), "Neck": pose((0, 0, 20 + s(p, 1.5))),
            "Head": pose((s(p, 3), 0, 26 + (rg.uniform(-3, 3) if tw else 0))),
            "ArmL": pose((2, 0, -10 + s(p, 1.5))), "ForearmL": pose((0, 0, -10)), "HandL": pose((0, 0, -10 + (rg.uniform(-14, 14) if tw else 0))),
            "ArmR": pose((0, 0, -8 + s(p, 1.0))),
        }
        d.update(tent([-16, -14, -12, -10, -8, -6], sway=[s(p, 3, 0.1 * i) + (rg.uniform(-6, 6) if tw and i > 3 else 0) for i in range(6)]))
        d.update(drift(f, 90, 0.35, 0.05))
        return d

    m.animation("lurk", 90, keys_from(lurk, 90, 6))

    # ---- glitch: 0.4 s one-shot: sideways jerks, a stretch, pixels scattered outward
    def gl(chest_z, head_z, st, sc, rot=0):
        d = {"Chest": pose((0, rot, 0), (0, 0, chest_z), st), "Head": pose((0, -rot, 0), (0, 0, head_z)),
             "Waist": pose(o=(0, 0, chest_z * 0.4)), "Pelvis": pose(o=(0, 0, -chest_z * 0.3))}
        d.update(drift(0, 1, 0, 0, sc))
        return d

    m.animation("glitch", 12, {
        0: gl(0, 0, (1, 1, 1), 0), 1: gl(1.6, -2.0, (1, 1.12, 0.92), 3.0, 4), 2: gl(-1.4, 1.8, (0.9, 1.0, 1.2), 4.5, -5),
        4: gl(2.0, 0, (1, 1.2, 0.9), 5.0, 3), 5: gl(-0.6, 1.0, (1.1, 0.95, 1.0), 4.0, -2), 8: gl(0.8, -0.6, (1, 1.05, 1), 2.0, 1),
        11: gl(0, 0, (1, 1, 1), 0)}, end="Stop")

    # ---- walk: 32 frames, stiff and uneven; the tentacle trails
    def walk(f):
        p = f / 32
        sw = math.sin(TAU * p)
        swr = math.sin(TAU * p + math.pi)
        # a limp: the left stride is longer, the right foot drags
        tl = -(24 * sw + 3 * math.sin(TAU * 2 * p))
        tr = -(15 * swr)
        kl = 22 * max(0.0, math.cos(TAU * p))
        kr = 12 * max(0.0, math.cos(TAU * p + math.pi))
        d = {
            "Pelvis": pose((s(p, 2, 0.25), s(p, 3), 5), (0, -0.7 * (0.5 - 0.5 * math.cos(TAU * 2 * p)), 0)),
            "ThighL": pose((0, 0, tl - 5)), "ThighR": pose((0, 0, tr - 5)), "ShinL": pose((0, 0, kl)), "ShinR": pose((0, 0, kr)),
            "FootL": pose((0, 0, -0.8 * (tl - 5 + kl))), "FootR": pose((0, 0, -0.8 * (tr - 5 + kr))),
            "Waist": pose((0, s(p, -3), 3)), "Chest": pose((s(p, 1.5), s(p, -4), 4 + s(p * 2, 1.2))),
            "Neck": pose((0, s(p, 3, 0.1), 4)), "Head": pose((s(p, 6, 0.2), s(p, 6, 0.3), s(p * 2, 3, 0.3) - 2)),
            "ArmL": pose((0, 0, -8 * swr - 4)), "ForearmL": pose((0, 0, -10 - 8 * max(0, swr))), "HandL": pose((0, 0, -6)),
            "ArmR": pose((0, 0, 8 + s(p, 6, 0.0))),
        }
        d.update(tent([6 + 8 * math.sin(TAU * (p - 0.08 * i)) for i in range(6)], sway=[s(p, 8, -0.1 * i) for i in range(6)]))
        d.update(drift(f, 32, 0.6, 0.1))
        return d

    m.animation("walk", 32, keys_from(walk, 32, 4))

    # ---- run: 18 frames, leaning forward, long strides, tentacle swept back
    def run(f):
        p = f / 18
        sw = math.sin(TAU * p)
        swr = -sw
        d = {
            "Pelvis": pose((0, s(p, 4), 9), (0, 0.9 * math.cos(TAU * 2 * p) - 0.5, 0)),
            "ThighL": pose((0, 0, -9 - 42 * sw)), "ThighR": pose((0, 0, -9 - 42 * swr)),
            "ShinL": pose((0, 0, 8 + 62 * max(0.0, math.cos(TAU * p)))), "ShinR": pose((0, 0, 8 + 62 * max(0.0, -math.cos(TAU * p)))),
            "FootL": pose((0, 0, 10)), "FootR": pose((0, 0, 10)),
            "Waist": pose((0, s(p, -5), 6)), "Chest": pose((0, s(p, -7), 8)),
            "Neck": pose((0, 0, 4)), "Head": pose((s(p, 5), s(p, 4, 0.2), -16 + s(p * 2, 3))),
            "ArmL": pose((0, 0, 30 * swr - 6)), "ForearmL": pose((0, 0, -45 - 20 * max(0, swr))), "HandL": pose((0, 0, -10)),
            "ArmR": pose((-12, 0, 62 + s(p, 7))),
        }
        d.update(tent([8 + 3 * math.sin(TAU * (p - 0.1 * i)) + 3 * i for i in range(6)], sway=[s(p, 10, -0.12 * i) for i in range(6)]))
        d.update(drift(f, 18, 0.6, 0.15, 0.8))
        return d

    m.animation("run", 18, keys_from(run, 18, 2))

    # ---- attack: 30 frames. Wind-up 0-10, the slice 10-14 (the arm passes horizontal in front at frame 13: the hit),
    # follow-through 14-22, recover to 29.
    z = pose()
    rest = {}
    wind = {
        "Pelvis": pose((0, -8, -3), (0.5, -0.5, 0)), "Waist": pose((0, -8, -3)), "Chest": pose((0, -24, -8)), "Neck": pose((0, 0, -4)), "Head": pose((-4, 4, -8)),
        "ThighL": pose((0, 0, -8)), "ThighR": pose((0, 0, 12)), "ShinR": pose((0, 0, 8)), "FootL": pose((0, 0, 8)), "FootR": pose((0, 0, -16)),
        "ArmL": pose((0, 0, 20)), "ForearmL": pose((0, 0, -20)),
        "ArmR": pose((-10, 0, 150)), **tent([14, 16, 16, 14, 12, 10], sway=[0, 3, 5, 6, 6, 4]),
    }
    early = blend(rest, wind, 0.4)
    early["ArmR"] = pose((-4, 0, 60))
    slice_ = {
        "Pelvis": pose((0, 8, 7), (-2.0, -0.8, 0)), "Waist": pose((0, 8, 6)), "Chest": pose((0, 22, 14)), "Neck": pose((0, 0, 4)), "Head": pose((0, -3, 0)),
        "ThighL": pose((0, 0, -30)), "ThighR": pose((0, 0, 16)), "ShinL": pose((0, 0, 14)), "ShinR": pose((0, 0, 20)), "FootL": pose((0, 0, 14)), "FootR": pose((0, 0, -20)),
        "ArmL": pose((0, 0, 30)), "ForearmL": pose((0, 0, -30)),
        "ArmR": pose((4, 0, 300)), **tent([-10, -12, -12, -10, -8, -6]),
    }
    follow = {
        "Pelvis": pose((0, 10, 10), (-2.5, -1.2, 0)), "Waist": pose((0, 10, 8)), "Chest": pose((0, 26, 20)), "Neck": pose((0, 0, 6)), "Head": pose((0, -4, 6)),
        "ThighL": pose((0, 0, -34)), "ThighR": pose((0, 0, 20)), "ShinL": pose((0, 0, 20)), "ShinR": pose((0, 0, 24)), "FootL": pose((0, 0, 14)), "FootR": pose((0, 0, -24)),
        "ArmL": pose((0, 0, 36)), "ForearmL": pose((0, 0, -30)),
        "ArmR": pose((6, 0, 326)), **tent([-22, -20, -18, -16, -14, -10], sway=[0, -4, -7, -8, -8, -6]),
    }
    recover = blend(follow, rest, 0.6)
    recover["ArmR"] = pose((2, 0, 346))
    end = {"ArmR": pose((0, 0, 360))}

    def with_px(d, sc):
        out = dict(d)
        out.update(drift(0, 1, 0.3, 0, sc))
        return out

    m.animation("attack", 30, {0: with_px(rest, 0), 5: with_px(early, 0.4), 10: with_px(wind, 0.8), 14: with_px(slice_, 2.6),
                               17: with_px(follow, 1.8), 22: with_px(recover, 0.6), 29: with_px(end, 0)}, end="Stop")

    # ---- hurt: 12 frames, recoil back with a glitch offset
    def hurt_pose(back, ox, sc, st=(1, 1, 1)):
        d = {"Pelvis": pose((0, 0, -3 * back), (0.8 * back, 0, 0)), "Waist": pose((0, 0, -6 * back)), "Chest": pose((0, 2 * back, -12 * back), (0, 0, ox), st),
             "Neck": pose((0, 0, -4 * back)), "Head": pose((0, -6 * back, -14 * back), (0, 0, -ox)),
             "ArmL": pose((0, 0, 12 * back)), "ArmR": pose((0, 0, 28 * back)), "ThighL": pose((0, 0, 4 * back)), "ThighR": pose((0, 0, -4 * back))}
        d.update(tent([12 * back] * 6, sway=[0, 5 * back, 8 * back, 8 * back, 6 * back, 4 * back]))
        d.update(drift(0, 1, 0, 0, sc))
        return d

    m.animation("hurt", 12, {0: hurt_pose(0, 0, 0), 2: hurt_pose(1.0, 1.8, 3.0, (1, 1.1, 0.9)), 3: hurt_pose(0.9, -1.6, 4.0),
                             5: hurt_pose(0.6, 1.0, 2.0), 8: hurt_pose(0.25, 0, 0.8), 11: hurt_pose(0, 0, 0)}, end="Stop")

    # ---- die: 36 frames, collapses forward, ends lying on its front, pixels falling; settled onto the floor
    flinch = hurt_pose(0.7, 1.4, 2.0)
    buckle = {
        "Pelvis": pose((0, 0, 8), (0, -5.0, 0)), "ThighL": pose((0, 0, -45)), "ThighR": pose((0, 0, -50)), "ShinL": pose((0, 0, 75)), "ShinR": pose((0, 0, 80)),
        "FootL": pose((0, 0, -30)), "FootR": pose((0, 0, -30)), "Waist": pose((0, 0, 10)), "Chest": pose((0, 3, 15)), "Neck": pose((0, 0, 15)), "Head": pose((8, 0, 20)),
        "ArmL": pose((0, 0, -15)), "ArmR": pose((0, 0, 20)), **tent([10, 12, 10, 8, 8, 6], sway=[0, 8, 10, 8, 6, 4]),
    }
    topple = {
        "Pelvis": pose((0, 0, 55), (-4.0, 0, 0)), "ThighL": pose((0, 0, -22)), "ThighR": pose((0, 0, -30)), "ShinL": pose((0, 0, 28)), "ShinR": pose((0, 0, 40)),
        "FootL": pose((0, 0, 10)), "FootR": pose((0, 0, 10)), "Waist": pose((0, 0, 10)), "Chest": pose((0, 0, 14)), "Neck": pose((0, 0, 6)), "Head": pose((0, 0, -14)),
        "ArmL": pose((0, 0, -50)), "ArmR": pose((0, 0, -60)), **tent([-10, -10, -8, -8, -6, -6], sway=[0, 6, -6, 6, -6, 6]),
    }
    prone = {
        "Pelvis": pose((0, 0, 92)), "ThighL": pose((-8, 0, 2)), "ThighR": pose((8, 0, -4)), "ShinL": pose((0, 0, 4)), "ShinR": pose((0, 0, 6)),
        "FootL": pose((0, 0, 24)), "FootR": pose((0, 0, 20)), "Waist": pose((0, 0, 4)), "Chest": pose((0, 0, 4)), "Neck": pose((0, 0, 0)), "Head": pose((12, 14, -24)),
        "ArmL": pose((12, 0, -184)), "ForearmL": pose((0, 0, -4)), "HandL": pose((0, 0, -4)),
        "ArmR": pose((-18, 0, -172)), **tent([0, 0, 0, 0, 0, 0], sway=[0, 0, 0, 0, 0, 0]),
    }
    for i, n in enumerate(SEGN):
        prone[n] = pose((9 * (1 if i % 2 == 0 else -1), 0, -3))
    dkeys = {0: {}, 4: flinch, 10: buckle, 22: topple, 35: prone}
    dkeys = {k: dict(v) for k, v in dkeys.items()}
    dm = build()
    for k in (10, 22, 35):
        rig.settle(dm, dkeys[k], floor=-0.2, ignore=PIXN)
    # the pixel cubes fall: at the end each lies on the floor, scattered; fractions of that on the way
    mats = rig.posed_matrices(dm, dkeys[35])
    import numpy as np
    rg = random.Random(1204)
    final = {}
    for name, parent, c, sz, col in PIX:
        p = dm.by_name[name]
        M = mats[id(p)] @ np.array([sz / 2, sz / 2, sz / 2, 1.0])
        want = np.array([rg.uniform(-4, 4), sz / 2 - M[1], rg.uniform(-4, 4)])
        if name.startswith("PxS"):
            want[0] = want[2] = 0.0
            want[1] = -0.0
        R = mats[id(p.parent)][:3, :3]
        final[name] = tuple(float(v) for v in R.T @ want)
    frac = {0: 0, 4: 0.04, 10: 0.2, 22: 0.62, 35: 1.0}
    for k in dkeys:
        for name in PIXN:
            f = final[name]
            sc = 3.0 * min(1.0, k / 10) * (1 - frac[k])
            d = DIRS[name]
            dkeys[k][name] = pose((0, 0, 0), tuple(f[i] * frac[k] + d[i] * sc for i in range(3)))
    m.animation("die", 36, dkeys, end="Hold")
    return dm


def check(m):
    """Lowest and highest drawn point of each animation's keys (the floor is y = 0), to see nothing sinks badly."""
    for code, frames, keys, end, _ in m.animations:
        lo = min(rig.posed_extent(m, k, ignore=PIXN)[0] for k in keys.values())
        print(f"  {code}: {frames} frames, lowest point {lo:.2f} px")


def reach(m):
    mats = rig.posed_matrices(m, {})
    import numpy as np
    tip = m.by_name["TentTip"]
    end = mats[id(tip)] @ np.array([tip.size[0] / 2, 0, tip.size[2] / 2, 1.0])
    sh = np.array([0, 24.3, -5.4])
    return float(np.linalg.norm(end[:3] - sh))


def generate():
    m = build(red=True)
    animations(m)
    m.save()
    lo, hi = rig.posed_extent(m, {})
    print(f"  rest height {hi:.1f} px = {hi / 16:.2f} blocks")
    # straight tentacle reach (rest curls removed) from the shoulder
    straight = 24.3 - (17.8 - sum(ln for _, ln, _ in SEGS))
    print(f"  tentacle reach (straight) {straight:.1f} px = {straight / 16:.2f} blocks; rest-pose point at {reach(m):.1f} px from the shoulder")
    check(m)
    # the second texture: same parts in the same order and sizes, painted without the red
    b = build(red=False)
    shape, (w, h) = b.shape()
    shape_a, (wa, ha) = m.shape()
    assert (w, h) == (wa, ha) and all(p.uv == q.uv for p, q in zip(m.parts, b.parts)), "atlas layouts differ"
    img = b._paint(w, h)
    path = os.path.join(rig.ASSETS, "textures", "entity", "120", BLACK_TEX + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", os.path.relpath(path, rig.ROOT))
    return m


if __name__ == "__main__":
    generate()
