"""Level 14 ("The Hospital", Fandom): The Hunter ("Patient Zero", File 14-E) and its Infecting Agents. Writes
shapes/entity/14/l14-hunter.json, l14-agent.json, their textures (textures/entity/14/) and their sounds (sounds/entity/14/).
Entity jsons, AI (src/Regions/L14Hunter.cs) and lang are written elsewhere.

The Hunter: a hunched, amorphous mass round what is left of a man, about 2.3 blocks tall: a heap of wet black flesh on
the floor, a sagging torso leaning out of it, a head with a slack jaw and two dull red, bloodshot eyes (the only thing on it
that catches the light), a thin human arm still hanging from its left shoulder; twelve octopus-like tentacles in every
direction, seven trailing on the floor round it (they hug the floor in every pose: `hug`), five raised or reaching from
the shoulders, the back and the chest, each ending in a round mouth ringed with teeth, and smaller mouths along them.

The Infecting Agent: a segmented leech about half a block long, wet black-grey, a round lamprey mouth with rings of teeth.

Rig conventions (rig.py): faces -X, left is +Z, +Z rotation leans a torso forward. A tentacle is a chain of boxes hanging
along -Y from its base; its root's rest rotation is (0, azimuth, tilt): tilt 0 hangs down, 90 is level, 180 straight up;
azimuth 0 points back (+X), 180 forward (-X), -90 left (+Z), 90 right (-Z). Its later segments curl in that plane (Z) and
sway out of it (X).

Run from the repo root:  python tools/gen_14_hunter.py
"""
import math
import os
import random
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import rig  # noqa: E402
from rig import Model, pose  # noqa: E402

TAU = math.tau
# Four texels to the model pixel: the mouths need room for a ring of teeth
rig.TEXEL = 4

HUNTER = "14/l14-hunter"
AGENT = "14/l14-agent"

SKIN = (13, 14, 19)            # near-black, a little blue
SHEEN = (44, 50, 64)           # a wet streak
SPEC = (104, 114, 136)         # where it catches the light
FLESH_DARK, FLESH, GUM = (34, 4, 6), (92, 12, 15), (128, 22, 24)
TOOTH, TOOTH_DIM = (228, 218, 192), (176, 164, 140)
EYE_RED, EYE_HOT, EYE_VEIN = (120, 22, 18), (176, 58, 44), (70, 8, 8)


# ================= Painters =================

def _put(ctx, px, x, y, c):
    if 0 <= x < ctx.w and 0 <= y < ctx.h:
        px[ctx.x + x, ctx.y + y] = rig.clamp(c) + (255,)


def _get(ctx, px, x, y):
    return px[ctx.x + max(0, min(ctx.w - 1, x)), ctx.y + max(0, min(ctx.h - 1, y))][:3]


def _noise(ctx, cell):
    lat = rig._lattice(ctx.rng, ctx.w, ctx.h, cell)
    return lambda x, y: rig._sample(lat, x, y, cell)


def wet_skin(ctx, base=SKIN, streaks=1.0, spec=1.0):
    """Moist black: a slow mottle, wet streaks running down the side faces (blots on the top ones), a few bright texels
    where the wet catches the light, dark veins. Down the face is down the part, as the side faces are painted."""
    px = ctx.img.load()
    n1, n2 = _noise(ctx, 6), _noise(ctx, 2)
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            m = 0.85 + 0.22 * n1(xx, yy) + 0.1 * n2(xx, yy) + 0.06 * (ctx.rng.random() - 0.5)
            _put(ctx, px, xx, yy, tuple(v * m for v in base))
    area = ctx.w * ctx.h
    side = ctx.face not in ("up", "down")
    for _ in range(int(area * 0.012 * streaks) + (1 if ctx.rng.random() < streaks else 0)):
        x0, y0 = ctx.rng.randrange(ctx.w), ctx.rng.randrange(ctx.h)
        if side:
            ln = ctx.rng.randint(3, max(4, ctx.h // 2))
            wob = 0.0
            for i in range(ln):
                t = i / max(1, ln - 1)
                x = int(round(x0 + wob))
                wob += ctx.rng.uniform(-0.35, 0.35)
                c = rig.mix(SHEEN, base, 0.25 + 0.6 * t)
                _put(ctx, px, x, y0 + i, c)
                if i == 0 and ctx.rng.random() < 0.7 * spec:
                    _put(ctx, px, x, y0, SPEC)
            # a bead at the bottom of the run
            if ctx.rng.random() < 0.5 * spec:
                _put(ctx, px, int(round(x0 + wob)), y0 + ln, rig.mix(SPEC, SHEEN, 0.4))
        else:
            r = ctx.rng.uniform(0.8, 2.2)
            for yy in range(int(y0 - r) - 1, int(y0 + r) + 2):
                for xx in range(int(x0 - r) - 1, int(x0 + r) + 2):
                    d = math.hypot(xx - x0, yy - y0) / r
                    if d < 1:
                        _put(ctx, px, xx, yy, rig.mix(_get(ctx, px, xx, yy), SHEEN, 0.75 * (1 - d)))
            if ctx.rng.random() < 0.6 * spec:
                _put(ctx, px, x0, y0, SPEC)
    # veins: dark lines wandering across
    for _ in range(int(area * 0.002) + (1 if ctx.rng.random() < 0.3 else 0)):
        x, y = ctx.rng.uniform(0, ctx.w), ctx.rng.uniform(0, ctx.h)
        a = ctx.rng.uniform(0, TAU)
        for _i in range(ctx.rng.randint(4, 14)):
            _put(ctx, px, int(x), int(y), tuple(v * 0.45 for v in base))
            a += ctx.rng.uniform(-0.6, 0.6)
            x, y = x + math.cos(a), y + math.sin(a)


def small_mouth(ctx, px, u, v, rx, ry):
    """A small mouth in the skin: a dark red slit with off-white teeth along its lips."""
    cx, cy = u * ctx.w, v * ctx.h
    for yy in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for xx in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2
            if d < 0.35:
                _put(ctx, px, xx, yy, FLESH_DARK)
            elif d < 0.75:
                tooth = (xx + yy) % 2 == 0
                _put(ctx, px, xx, yy, TOOTH if tooth else GUM)
            elif d < 1.2:
                _put(ctx, px, xx, yy, rig.mix(_get(ctx, px, xx, yy), FLESH, 0.6))


def tentacle_paint(mouths=()):
    """A tentacle segment: wet skin, creases across it, and on the faces named in `mouths` a small toothed mouth."""
    def paint(ctx):
        wet_skin(ctx, streaks=0.7)
        if ctx.face not in ("up", "down"):
            rig.folds(ctx, [0.3, 0.7], depth=0.6, light=1.25, wobble=0.6)
            if ctx.face in mouths:
                px = ctx.img.load()
                small_mouth(ctx, px, 0.5, 0.55, max(1.4, ctx.w * 0.28), max(1.6, ctx.h * 0.16))
    return paint


def mouth_tip(ctx):
    """The tentacle's end: a bulb whose far face (down: the chain hangs along -Y) is a round mouth, a throat ringed with
    teeth inside red gums, the lips swollen round it; its sides wet black going red toward the lips."""
    px = ctx.img.load()
    if ctx.face == "down":
        cx, cy = ctx.w / 2, ctx.h / 2
        r = min(ctx.w, ctx.h) / 2
        n_teeth = 9
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
                d = math.hypot(dx, dy) / r
                a = (math.atan2(dy, dx) / TAU) % 1.0
                if d < 0.3:
                    c = FLESH_DARK
                elif d < 0.62:
                    tooth = ((a * n_teeth) % 1.0) < 0.55 and d > 0.36
                    c = rig.mix(TOOTH, TOOTH_DIM, (d - 0.36) * 2) if tooth else rig.mix(FLESH_DARK, GUM, (d - 0.3) * 3)
                elif d < 0.88:
                    c = rig.mix(GUM, FLESH, ctx.rng.random() * 0.5)
                else:
                    c = rig.mix(FLESH, SKIN, 0.5)
                _put(ctx, px, xx, yy, c)
        return
    wet_skin(ctx, streaks=0.5)
    if ctx.face != "up":
        for yy in range(ctx.h):
            t = yy / max(1, ctx.h - 1)
            if t > 0.55:
                k = (t - 0.55) / 0.45
                for xx in range(ctx.w):
                    c = _get(ctx, px, xx, yy)
                    _put(ctx, px, xx, yy, rig.mix(c, FLESH if k < 0.8 else GUM, 0.25 + 0.6 * k))


def head_paint(ctx):
    """The head: wet black; the face (west) sunken round the eyes, a slack dark mouth below them, the skin cracked."""
    wet_skin(ctx, base=(15, 15, 20), streaks=0.8)
    px = ctx.img.load()
    if ctx.face == "west":
        # sockets: darker hollows round where the eyes sit (the eye parts stand in them), u along z from -z
        for (u0, u1) in ((0.12, 0.42), (0.58, 0.88)):
            for yy in range(int(ctx.h * 0.22), int(ctx.h * 0.52)):
                for xx in range(int(ctx.w * u0), int(ctx.w * u1)):
                    c = _get(ctx, px, xx, yy)
                    _put(ctx, px, xx, yy, tuple(v * 0.5 for v in c))
        # a slack mouth hanging open over the jaw: a black hole edged with dark red, a few teeth
        x0, x1, y0, y1 = int(ctx.w * 0.25), int(ctx.w * 0.75), int(ctx.h * 0.74), ctx.h
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                edge = xx in (x0, x1 - 1) or yy == y0
                c = FLESH if edge else (6, 2, 3)
                if yy == y0 + 1 and not edge and (xx - x0) % 2 == 1:
                    c = TOOTH_DIM
                _put(ctx, px, xx, yy, c)
        # tear tracks of something dark running from the eyes
        for u in (0.27, 0.73):
            x = int(ctx.w * u)
            for yy in range(int(ctx.h * 0.5), int(ctx.h * 0.72)):
                _put(ctx, px, x, yy, (38, 6, 8) if yy % 3 else (60, 10, 12))


def jaw_paint(ctx):
    wet_skin(ctx, base=(15, 15, 20), streaks=0.5)
    if ctx.face == "up":
        px = ctx.img.load()
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                edge = xx in (0, ctx.w - 1) or yy in (0, ctx.h - 1)
                c = TOOTH_DIM if (edge and xx == 0 and yy % 2 == 0) else (FLESH if edge else FLESH_DARK)
                _put(ctx, px, xx, yy, c)


def eye_paint(ctx):
    """Bloodshot: dull red, hotter at the middle, darker veins; vacant (no pupil worth the name)."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            d = math.hypot((xx + 0.5) / ctx.w - 0.5, (yy + 0.5) / ctx.h - 0.5) * 2
            c = rig.mix(EYE_HOT, EYE_RED, min(1.0, d))
            if ctx.rng.random() < 0.18:
                c = EYE_VEIN
            _put(ctx, px, xx, yy, c)
    if ctx.face == "west" and ctx.w >= 3 and ctx.h >= 3:
        _put(ctx, px, ctx.w // 2, ctx.h // 2, (40, 6, 6))


def body_paint(ctx):
    wet_skin(ctx, streaks=1.0)


def arm_paint(ctx):
    """The human arm left on it: the same black, thinner, with the creases of a wrist and an elbow."""
    wet_skin(ctx, base=(16, 16, 21), streaks=0.8)
    if ctx.face not in ("up", "down"):
        rig.folds(ctx, [0.15, 0.85], depth=0.65, light=1.2, wobble=0.4)


def hand_paint(ctx):
    wet_skin(ctx, base=(17, 16, 21), streaks=0.4)
    if ctx.face not in ("up", "down"):
        px = ctx.img.load()
        # fingers: dark lines down the lower half
        for xx in range(1, ctx.w - 1, 2):
            for yy in range(int(ctx.h * 0.45), ctx.h):
                _put(ctx, px, xx, yy, (7, 7, 9))


# ================= The Hunter =================

class Tent:
    """One tentacle: where it grows from, which way, its curls and its segments' lengths and widths."""

    def __init__(self, name, parent, base, az, tilt, curls, lens, widths, kind, mouth=(2.2, 1.5), phase=0.0):
        self.name, self.parent, self.base, self.az, self.tilt = name, parent, base, az, tilt
        self.curls, self.lens, self.widths, self.kind, self.mouth, self.phase = curls, lens, widths, kind, mouth, phase
        self.parts = [f"{name}S{i + 1}" for i in range(len(lens))] + [f"{name}M"]


FLOOR_L = [3.8, 3.5, 3.2, 2.9, 2.5]
FLOOR_W = [2.6, 2.3, 2.0, 1.7, 1.4]
RAISE_L = [3.8, 3.5, 3.2, 2.9, 2.5]
RAISE_W = [2.4, 2.1, 1.8, 1.55, 1.3]
ARM_L = [4.3, 3.9, 3.5, 3.1, 2.7]
ARM_W = [2.5, 2.2, 1.9, 1.6, 1.35]

TENTS = [
    # seven on the floor round the mass
    Tent("TFL", "Mass", (-5.6, 3.6, 4.4), -140, 64, [0, 10, 10, 6, 2, -10], FLOOR_L, FLOOR_W, "floor", phase=0.0),
    Tent("TFR", "Mass", (-5.6, 3.6, -4.4), 138, 64, [0, 10, 10, 6, 2, -10], FLOOR_L, FLOOR_W, "floor", phase=2.1),
    Tent("TL", "Mass", (0.0, 3.8, 6.2), -88, 64, [0, 10, 10, 6, 2, -10], [l * 0.92 for l in FLOOR_L], FLOOR_W, "floor", phase=4.0),
    Tent("TR", "Mass", (0.6, 3.8, -6.2), 94, 64, [0, 10, 10, 6, 2, -10], [l * 0.95 for l in FLOOR_L], FLOOR_W, "floor", phase=1.2),
    Tent("TBL", "Mass", (5.2, 3.6, 4.6), -38, 64, [0, 10, 10, 6, 2, -10], FLOOR_L, FLOOR_W, "floor", phase=3.1),
    Tent("TBR", "Mass", (5.2, 3.6, -4.6), 34, 64, [0, 10, 10, 6, 2, -10], [l * 1.05 for l in FLOOR_L], FLOOR_W, "floor", phase=5.2),
    Tent("TB", "Mass", (6.4, 4.2, 0.2), 2, 64, [0, 10, 10, 6, 2, -10], [l * 1.2 for l in FLOOR_L], FLOOR_W, "floor", phase=0.7),
    # raised from the shoulders and the back, drooping their mouths outward
    Tent("TSL", "Chest", (1.4, 27.6, 3.0), -104, 122, [0, -8, -14, -18, -16, -12], RAISE_L, RAISE_W, "raised", phase=1.7),
    Tent("TSR", "Chest", (0.6, 27.8, -3.4), 112, 118, [0, -6, -14, -18, -16, -10], [l * 1.08 for l in RAISE_L], RAISE_W, "raised", phase=3.6),
    Tent("TK", "Chest", (3.0, 25.8, 0.0), 26, 112, [0, -6, -14, -20, -18, -12], [l * 1.1 for l in RAISE_L], RAISE_W, "raised", phase=5.0),
    # reaching forward from the chest and the belly: its arms
    Tent("TAL", "Torso", (-3.2, 18.5, 4.0), -152, 98, [0, 6, 2, -6, -10, -12], ARM_L, ARM_W, "arm", phase=2.6),
    Tent("TAR", "Chest", (-2.6, 23.4, -4.0), 156, 92, [0, 4, 0, -8, -10, -12], ARM_L, ARM_W, "arm", phase=0.4),
]
TBY = {t.name: t for t in TENTS}
FLOORS = [t for t in TENTS if t.kind == "floor"]
ARMS = [TBY["TAL"], TBY["TAR"]]
RAISED = [t for t in TENTS if t.kind == "raised"]
TPARTS = {n for t in TENTS for n in t.parts}
BODY = ["Mass", "Torso", "Chest", "Neck", "Head", "Jaw", "ArmL", "ForearmL", "HandL"]


def build_hunter():
    m = Model(HUNTER, atlas_width=64, seed=1414)
    m.light = dict(floor=12.0, ground=0.0, grad=0.25, edge=0.05, foot=0.03, drift=0.0, round=0.15)
    mass = m.part("Mass", (-6.5, 0.6, -6.5), (13, 10.4, 13), pivot=(0, 5, 0), paint=body_paint)
    m.part("LumpF", (-8.2, 1.2, -4.0), (4.2, 6.5, 8.0), pivot=(-6, 4, 0), parent=mass, rest=(0, 0, -10), paint=body_paint)
    m.part("LumpBL", (2.5, 1.4, 2.0), (6.5, 7.0, 6.0), pivot=(5, 4, 5), parent=mass, rest=(0, 22, 6), paint=body_paint)
    m.part("LumpBR", (1.5, 2.5, -8.0), (6.0, 6.0, 5.0), pivot=(4, 5, -5), parent=mass, rest=(0, -16, 0), paint=body_paint)
    m.part("LumpTop", (-4.5, 9.0, -5.6), (10.5, 5.5, 11.2), pivot=(0, 10, 0), parent=mass, rest=(4, 0, 8), paint=body_paint)
    m.part("LumpS", (-2.0, 6.0, 4.5), (7.0, 6.0, 4.0), pivot=(1, 8, 6), parent=mass, rest=(-14, 10, 0), paint=body_paint)
    torso = m.part("Torso", (-4.4, 11.5, -4.8), (8.8, 10.5, 9.6), pivot=(0, 12, 0), parent=mass, rest=(0, 0, 24), paint=body_paint)
    m.part("Belly", (-6.0, 11.0, -4.0), (3.0, 6.5, 8.0), pivot=(-4.5, 16, 0), parent=torso, rest=(0, 0, -8), paint=body_paint)
    chest = m.part("Chest", (-3.6, 21.5, -4.3), (7.2, 7.0, 8.6), pivot=(0, 21.5, 0), parent=torso, rest=(0, 0, 14), paint=body_paint)
    m.part("Hump", (0.2, 23.0, -3.8), (4.4, 5.5, 6.0), pivot=(2, 25, -1), parent=chest, rest=(10, 0, 4), paint=body_paint)
    neck = m.part("Neck", (-1.4, 28.2, -1.4), (2.8, 2.6, 2.8), pivot=(0, 28.4, 0), parent=chest, rest=(0, 0, 8), paint=body_paint)
    head = m.part("Head", (-2.6, 30.3, -2.4), (5.2, 5.6, 4.8), pivot=(0, 30.6, 0), parent=neck, rest=(6, 0, -38), paint=head_paint)
    m.part("Jaw", (-2.9, 29.3, -1.8), (3.0, 1.2, 3.6), pivot=(-0.2, 30.4, 0), parent=head, rest=(0, 0, 12), paint=jaw_paint)
    m.part("EyeL", (-2.8, 33.6, 0.5), (0.4, 0.8, 1.1), parent=head, paint=eye_paint, glow=70, tag={"occlude": False})
    m.part("EyeR", (-2.8, 33.6, -1.6), (0.4, 0.8, 1.1), parent=head, paint=eye_paint, glow=70, tag={"occlude": False})
    # the arm that is left: thin, hanging forward from the left shoulder
    arm = m.part("ArmL", (-1.0, 19.4, 4.2), (2.0, 7.0, 2.0), pivot=(0, 26.2, 5.0), parent=chest, rest=(-8, 0, -32), paint=arm_paint)
    fore = m.part("ForearmL", (-0.9, 13.0, 4.3), (1.8, 6.6, 1.8), pivot=(0, 19.6, 5.0), parent=arm, rest=(0, 0, -16), paint=arm_paint)
    m.part("HandL", (-0.9, 10.4, 4.2), (1.8, 2.6, 1.6), pivot=(0, 13.0, 5.0), parent=fore, rest=(0, 0, -6), paint=hand_paint)
    for t in TENTS:
        last = m.by_name[t.parent]
        bx, by, bz = t.base
        y = by
        for i, (ln, w) in enumerate(zip(t.lens, t.widths)):
            rest = (0, t.az, t.tilt) if i == 0 else (0, 0, t.curls[i])
            mouths = ("north", "south") if i in (1, 3) else ()
            last = m.part(t.parts[i], (bx - w / 2, y - ln, bz - w / 2), (w, ln, w), pivot=(bx, y, bz), parent=last, rest=rest,
                          paint=tentacle_paint(mouths))
            y -= ln
        mw, ml = t.mouth
        m.part(t.parts[-1], (bx - mw / 2, y - ml, bz - mw / 2), (mw, ml, mw), pivot=(bx, y, bz), parent=last, rest=(0, 0, t.curls[-1]),
               paint=mouth_tip)
    # the floor tentacles' rest: lying along the floor (as every animation keeps them)
    key = hug(m, {}, FLOORS)
    for t in FLOORS:
        for n in t.parts:
            p, r = m.by_name[n], key[n]["rot"]
            p.rest = tuple(p.rest[i] + r[i] for i in range(3))
    return m


# ================= Posing helpers =================

def s(phase, amp, shift=0.0):
    return amp * math.sin(TAU * (phase + shift))


def tpose(t, dtilt=0.0, daz=0.0, dcurls=None, sways=None):
    """A tentacle's pose deltas: the root's tilt and azimuth, each segment's curl (in its plane) and sway (out of it)."""
    out = {}
    for i, n in enumerate(t.parts):
        c = dcurls[i] if dcurls else 0.0
        w = sways[i] if sways else 0.0
        out[n] = pose((w, daz if i == 0 else 0.0, (dtilt if i == 0 else 0.0) + c))
    return out


def writhe(t, p, amp, cycles=1, lag=0.12, sway=0.8, dtilt=0.0, daz=0.0, extra=None):
    """A travelling wave down a tentacle (`cycles` whole waves in the loop, so it closes)."""
    ph = t.phase
    dc = [amp * math.sin(TAU * cycles * p - TAU * lag * i + ph) for i in range(6)]
    sw = [amp * sway * math.sin(TAU * cycles * p - TAU * lag * i + ph + 1.7) for i in range(6)]
    if extra:
        dc = [dc[i] + extra[i] for i in range(6)]
    return tpose(t, dtilt, daz, dc, sw)


def _rotm(rx, ry, rz):
    m = np.eye(4)
    m[:3, :3] = rig._rot3(rx, ry, rz)
    return m


def _chain(m, mats, t, key):
    """The tentacle's part matrices in a pose, from its parent's (mats from rig.posed_matrices)."""
    out = []
    parent = m.by_name[t.parent]
    base = mats[id(parent)]
    pf = parent.frm
    for n in t.parts:
        p = m.by_name[n]
        ps = key.get(n, {})
        r, o = ps.get("rot", (0, 0, 0)), ps.get("off", (0, 0, 0))
        M = base @ rig._shift(np.array(p.pivot) - np.array(pf)) @ _rotm(*(p.rest[i] + r[i] for i in range(3))) \
            @ rig._shift(np.array(p.frm) + np.array(o) - np.array(p.pivot))
        out.append(M)
        base, pf = M, p.frm
    return out


def _low(p, M):
    c = np.array([[x * p.size[0], y * p.size[1], z * p.size[2], 1] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
    return float((M @ c.T)[1].min())


def hug(m, key, tents, lift=None, floor=0.05):
    """Bends each tentacle's segments (curl, the root's tilt) so that it lies along the floor: segment by segment, the curl
    whose box comes lowest nearest the floor (a little over it, by `lift[name]` for the mouth: a tip raised to taste the
    air), keeping the sways and any azimuth the pose gave. Changes `key` in place."""
    mats = rig.posed_matrices(m, key)
    for t in tents:
        for i, n in enumerate(t.parts):
            p = m.by_name[n]
            ps = dict(key.get(n, pose()))
            r = list(ps["rot"])
            target = floor + (lift.get(t.name, 0.0) if lift and i == len(t.parts) - 1 else 0.0)
            pref = r[2]
            best, bestv = r[2], None
            for c in np.arange(-80, 80.1, 2.0):
                r[2] = float(c)
                ps["rot"] = tuple(r)
                key[n] = ps
                M = _chain(m, mats, t, key)[i]
                lo = _low(p, M)
                v = abs(lo - target) + 0.004 * abs(c - pref) + (3.0 * (target - lo) if lo < target else 0.0)
                if bestv is None or v < bestv:
                    best, bestv = float(c), v
            r[2] = best
            ps["rot"] = tuple(r)
            key[n] = ps
    return key


def plus(d, delta):
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
        if "str" in pa or "str" in pb:
            sa, sb = pa.get("str", (1, 1, 1)), pb.get("str", (1, 1, 1))
            out[k]["str"] = tuple(sa[i] + (sb[i] - sa[i]) * t for i in range(3))
    return out


# ================= The Hunter's animations =================

def hunter_animations(m):
    lifts = lambda p, amp: {t.name: max(0.0, amp * math.sin(TAU * p + t.phase * 1.3)) for t in FLOORS}

    # ---- idle: 4 s, slow writhing, a heavy breath
    def idle(f):
        p = f / 120
        br = 0.5 - 0.5 * math.cos(TAU * p)
        d = {
            "Mass": pose((0, 0, 0), (0, 0.15 * br, 0), (1 + 0.015 * br, 1 - 0.01 * br, 1 + 0.015 * br)),
            "Torso": pose((s(p, 1.5), s(p, 2, 0.2), 1.5 * br)),
            "Chest": pose((0, s(p, 2, 0.4), 1.2 * br), (0, 0, 0), (1, 1 + 0.02 * br, 1 + 0.03 * br)),
            "Neck": pose((0, 0, s(p, 2, 0.1))),
            "Head": pose((s(p, 4, 0.3), s(p, 6, 0.15), s(p, 3))),
            "Jaw": pose((0, 0, 3 * br)),
            "ArmL": pose((s(p, 2, 0.5), 0, s(p, 3, 0.3))), "ForearmL": pose((0, 0, s(p, 4, 0.4))), "HandL": pose((0, 0, s(p, 8, 0.6))),
        }
        for t in TENTS:
            amp = {"floor": 7, "raised": 9, "arm": 8}[t.kind]
            d.update(writhe(t, p, amp, cycles=1 if t.kind != "raised" else 2))
        hug(m, d, FLOORS, lifts(p, 1.4))
        return d

    m.animation("idle", 120, keys(idle, 120, 6))

    # ---- lurk (sensing): 4 s. It rises out of its hunch and holds still, the head turning slowly as if listening; the
    # raised tentacles lift and splay, their mouths turning about; the floor ones flatten and twitch now and then
    def lurk(f):
        p = f / 120
        rg = random.Random(f * 31 + 7)
        tw = rg.random() < 0.3
        d = {
            "Mass": pose((0, 0, 0), (0, 0.4, 0)),
            "Torso": pose((0, 0, -10)), "Chest": pose((0, s(p, 4), -6)), "Neck": pose((0, 0, -4)),
            "Head": pose((s(p * 2, 6), s(p, 26), 4 + s(p * 2, 3))),
            "Jaw": pose((0, 0, 6)),
            "ArmL": pose((0, 0, -4)), "ForearmL": pose((0, 0, -6)), "HandL": pose((0, 0, rg.uniform(-14, 14) if tw else 0)),
        }
        for t in TENTS:
            if t.kind == "raised":
                d.update(writhe(t, p, 5, cycles=2, dtilt=14, extra=[0, 6, 6, 4, 2, 0]))
            elif t.kind == "arm":
                d.update(writhe(t, p, 4, cycles=1, dtilt=22, daz=s(p, 10, t.phase / TAU)))
            else:
                d.update(writhe(t, p, 3 + (6 if tw else 0), cycles=2, daz=rg.uniform(-6, 6) if tw else 0))
        hug(m, d, FLOORS, {t.name: (1.5 if tw and i % 2 else 0.4) for i, t in enumerate(FLOORS)})
        return d

    m.animation("lurk", 120, keys(lurk, 120, 6))

    # ---- shriek: 0.9 s one-shot. It rears up, head thrown back, jaw wide, every tentacle flung out
    def shriek_pose(k, jit=0.0):
        d = {
            "Mass": pose((0, 0, 0), (0.4 * k, 0.6 * k, 0)),
            "Torso": pose((0, 0, -22 * k)), "Chest": pose((jit, 0, -12 * k)), "Neck": pose((0, 0, -10 * k)),
            "Head": pose((jit * 2, 0, 26 * k)), "Jaw": pose((0, 0, 30 * k)),
            "ArmL": pose((-10 * k, 0, 30 * k)), "ForearmL": pose((0, 0, -20 * k)),
        }
        for t in TENTS:
            if t.kind == "raised":
                d.update(tpose(t, -20 * k, 0, [0, 14 * k, 16 * k, 16 * k, 12 * k, 8 * k], [jit] * 6))
            elif t.kind == "arm":
                d.update(tpose(t, 40 * k, (-20 if t.az < 0 else 20) * k, [0, -8 * k, -10 * k, -6 * k, 6 * k, 14 * k], [jit] * 6))
            else:
                d.update(tpose(t, 18 * k, 0, [0, -4 * k, -4 * k, -2 * k, 4 * k, 10 * k], [jit * 0.5] * 6))
        return d

    m.animation("shriek", 27, {0: shriek_pose(0), 5: shriek_pose(1.0), 8: shriek_pose(1.05, 4), 10: shriek_pose(1.0, -4),
                               12: shriek_pose(1.05, 4), 14: shriek_pose(1.0, -4), 16: shriek_pose(1.05, 3), 20: shriek_pose(0.9),
                               26: shriek_pose(0)}, end="Stop")

    # ---- walk: 1.6 s. It hauls itself along: the front floor tentacles reach forward, plant and pull while the mass
    # surges after them (twice a loop, the two sides in turn); the back ones drag
    def walk(f):
        p = f / 48
        surge = math.sin(TAU * 2 * p)
        d = {
            "Mass": pose((s(p, 2, 0.25), s(p, 3), 4), (-0.7 * surge, 0.25 * max(0.0, surge), 0)),
            "Torso": pose((s(p, 3, 0.1), s(p, -3), 4 + 2 * surge)), "Chest": pose((0, s(p, -4), 2 + 1.5 * surge)),
            "Neck": pose((0, 0, 2)), "Head": pose((s(p, 4, 0.2), s(p, 5, 0.3), -6 - 2 * surge)),
            "Jaw": pose((0, 0, 4)),
            "ArmL": pose((s(p, 3), 0, -6 + s(p, 8, 0.3))), "ForearmL": pose((0, 0, -8 + s(p, 6, 0.5))), "HandL": pose((0, 0, -6)),
        }
        lift = {}
        for t in TENTS:
            if t.kind == "floor":
                front = t.name in ("TFL", "TFR", "TL", "TR")
                side = 0.0 if t.name in ("TFL", "TR") else 0.5
                ph = (2 * p + side) % 1.0
                if front:
                    # reach forward while lifted (ph 0-0.5), then plant and pull back (0.5-1)
                    reach = math.sin(TAU * ph)
                    toward = 1 if t.az > 0 else -1                   # forward is toward +-180
                    d.update(writhe(t, p, 4, cycles=2, daz=toward * 26 * reach))
                    lift[t.name] = 2.5 * max(0.0, reach)
                else:
                    d.update(writhe(t, p, 6, cycles=2, daz=s(p, 8, t.phase / TAU)))
                    lift[t.name] = 0.3
            elif t.kind == "arm":
                d.update(writhe(t, p, 7, cycles=1, dtilt=-6 + s(p, 8, 0.25 if t.az < 0 else 0.75)))
            else:
                d.update(writhe(t, p, 8, cycles=2, dtilt=-6))
        hug(m, d, FLOORS, lift)
        # the lifted fronts: raised off the floor while they reach
        for t in FLOORS:
            if lift.get(t.name, 0) > 0.5:
                d[t.parts[0]] = pose((d[t.parts[0]]["rot"][0], d[t.parts[0]]["rot"][1], d[t.parts[0]]["rot"][2] + 6 * lift[t.name]))
        return d

    m.animation("walk", 48, keys(walk, 48, 4))

    # ---- run: 0.8 s. Lunging: the arms slam forward and pull like front legs, the floor tentacles thrash, the body
    # pitched forward and heaving, the raised ones swept back
    def run(f):
        p = f / 24
        surge = math.sin(TAU * p)
        d = {
            "Mass": pose((s(p, 3, 0.25), s(p, 4), 10), (-1.3 * surge, 0.6 * max(0.0, surge), 0)),
            "Torso": pose((0, s(p, -5), 12 + 4 * surge)), "Chest": pose((0, s(p, -6), 6 + 3 * surge)),
            "Neck": pose((0, 0, 0)), "Head": pose((s(p, 4), s(p, 4, 0.2), -18 - 4 * surge)),
            "Jaw": pose((0, 0, 14)),
            "ArmL": pose((-6, 0, 26 + s(p, 14))), "ForearmL": pose((0, 0, -30 + s(p, 10, 0.4))), "HandL": pose((0, 0, -10)),
        }
        lift = {}
        for t in TENTS:
            if t.kind == "floor":
                front = t.name in ("TFL", "TFR", "TL", "TR")
                side = 0.0 if t.name in ("TFL", "TR") else 0.5
                reach = math.sin(TAU * (p + side))
                toward = 1 if t.az > 0 else -1
                if front:
                    d.update(writhe(t, p, 6, cycles=2, daz=toward * 34 * reach))
                    lift[t.name] = 3.0 * max(0.0, reach)
                else:
                    d.update(writhe(t, p, 10, cycles=2, daz=-toward * 14 * reach))
                    lift[t.name] = 0.6
            elif t.kind == "arm":
                # each arm swings forward high and slams down to pull (the two in turn)
                k = math.sin(TAU * p + (0 if t.az < 0 else math.pi))
                d.update(tpose(t, -8 + 28 * k, (-12 if t.az < 0 else 12) * k, [0, -6 * k, -8, -10, -8 - 8 * k, -6],
                               [s(p, 6, i * 0.1) for i in range(6)]))
            else:
                d.update(writhe(t, p, 10, cycles=2, dtilt=-30, extra=[0, 10, 12, 12, 8, 4]))
        hug(m, d, FLOORS, lift)
        for t in FLOORS:
            if lift.get(t.name, 0) > 0.5:
                d[t.parts[0]] = pose((d[t.parts[0]]["rot"][0], d[t.parts[0]]["rot"][1], d[t.parts[0]]["rot"][2] + 6 * lift[t.name]))
        return d

    m.animation("run", 24, keys(run, 24, 2))

    # ---- attack: 1 s one-shot. Wind-up 0-9 (it rears, the arms and the shoulder tentacles drawn up high), the lash 9-13
    # (the arms whip forward and down together: the hit at frame 13, 430 ms), the grab 13-22 (they coil and drag back
    # toward it), recover to 29
    def body(rear, lean, jaw):
        return {"Mass": pose((0, 0, lean * 0.3), (-0.08 * lean, 0, 0)), "Torso": pose((0, 0, -rear + lean)), "Chest": pose((0, 0, -rear * 0.5 + lean * 0.6)),
                "Head": pose((0, 0, rear * 0.6 - lean * 0.4)), "Jaw": pose((0, 0, jaw)),
                "ArmL": pose((0, 0, rear * 0.8)), "ForearmL": pose((0, 0, -rear * 0.5))}

    def lash(k_up, k_fwd, coil, inward):
        d = {}
        for t in ARMS:
            sg = -1 if t.az < 0 else 1
            d.update(tpose(t, 60 * k_up - 6 * k_fwd, sg * inward, [0, -10 * k_up + coil, -12 * k_up + coil, -10 * k_up + coil * 1.2,
                                                                     -6 * k_up + coil * 1.4, coil * 1.6],
                           [0, 0, 0, 0, 0, 0]))
        for t in RAISED:
            if t.name == "TK":
                d.update(tpose(t, -16 * k_up, 0, [0, 4 * k_up + coil * 0.3, 6 * k_up, 6 * k_up, 4 * k_up, 0]))
            else:
                d.update(tpose(t, 18 * k_up - 30 * k_fwd, 0, [0, 6 * k_up - 6 * k_fwd + coil * 0.5, 6 * k_up - 8 * k_fwd, -6 * k_fwd, 0, 6 * k_fwd]))
        return d

    def akey(rear, lean, jaw, k_up, k_fwd, coil, inward, floor_lift=0.0):
        d = body(rear, lean, jaw)
        d.update(lash(k_up, k_fwd, coil, inward))
        for t in FLOORS:
            d.update(tpose(t))
        hug(m, d, FLOORS, {t.name: floor_lift for t in FLOORS})
        return d

    rest = akey(0, 0, 0, 0, 0, 0, 0)
    m.animation("attack", 30, {
        0: rest,
        5: akey(8, 0, 10, 0.6, 0, 0, 0),
        9: akey(14, -2, 18, 1.0, 0, -4, 6, 0.5),
        11: akey(4, 12, 26, 0.4, 0.8, 0, 18, 0.3),
        13: akey(-4, 14, 28, 0.0, 1.0, 10, 26),
        16: akey(-2, 12, 20, 0.05, 0.8, 26, 30),
        21: akey(6, 4, 12, 0.2, 0.2, 34, 20),
        25: akey(3, 1, 6, 0.1, 0.0, 14, 8),
        29: rest,
    }, end="Stop")

    # ---- hurt: 0.4 s, a recoil: the body flinches back, every tentacle jerks inward
    def hurt_pose(k, jit=0.0):
        d = {"Mass": pose((0, 0, -3 * k), (0.6 * k, 0, 0)), "Torso": pose((jit, 0, -14 * k)), "Chest": pose((0, 0, -8 * k)),
             "Head": pose((0, -10 * k, 14 * k)), "Jaw": pose((0, 0, 16 * k)), "ArmL": pose((0, 0, 20 * k))}
        for t in TENTS:
            if t.kind == "floor":
                d.update(tpose(t, 0, 0, None, [jit * 2] * 6))
            else:
                d.update(tpose(t, -10 * k, 0, [0, 10 * k, 12 * k, 12 * k, 10 * k, 6 * k], [jit] * 6))
        hug(m, d, FLOORS, {t.name: 1.5 * k for t in FLOORS})
        return d

    m.animation("hurt", 12, {0: hurt_pose(0), 2: hurt_pose(1.0, 3), 4: hurt_pose(0.9, -3), 7: hurt_pose(0.5), 11: hurt_pose(0)}, end="Stop")

    # ---- die: 1.5 s, held. A shudder, the torso sags forward over the mass, the raised tentacles fall, then all of it
    # slumps into a heap, every tentacle limp along the floor
    def die_pose(k_sag, k_fall, k_heap, jit=0.0):
        d = {
            "Mass": pose((0, 0, 0), (0, -2.6 * k_heap, 0), (1 + 0.16 * k_heap, 1 - 0.38 * k_heap, 1 + 0.16 * k_heap)),
            "Torso": pose((jit, 0, 26 * k_sag + 40 * k_fall)), "Chest": pose((0, 0, 18 * k_sag + 18 * k_fall)),
            "Neck": pose((0, 0, 10 * k_sag + 6 * k_fall)), "Head": pose((14 * k_fall, 10 * k_fall, 22 * k_sag + 6 * k_fall)),
            "Jaw": pose((0, 0, 20 * k_sag)),
            "ArmL": pose((-16 * k_fall, 0, -20 * k_sag - 30 * k_fall)), "ForearmL": pose((0, 0, -10 * k_fall)), "HandL": pose((0, 0, 10 * k_fall)),
        }
        for t in TENTS:
            if t.kind == "raised":
                d.update(tpose(t, -70 * k_fall, 0, [0, 14 * k_sag, 10 * k_sag, 6 * k_sag, 0, 0], [jit] * 6))
            elif t.kind == "arm":
                d.update(tpose(t, -30 * k_fall, 0, [0, 6 * k_sag, 4 * k_sag, 0, 0, 0], [jit] * 6))
            else:
                d.update(tpose(t, 0, 0, None, [jit] * 6))
        return d

    flinch = die_pose(0.15, 0, 0, 5)
    sag = die_pose(1.0, 0.1, 0.1, -3)
    fall = die_pose(1.0, 0.7, 0.6)
    heap = die_pose(1.0, 1.0, 1.0)
    dm = build_hunter()
    hug(dm, flinch, FLOORS)
    hug(dm, sag, FLOORS)
    hug(dm, fall, FLOORS)
    rig.settle(dm, heap, floor=-0.4, ignore=TPARTS | {"ArmL", "ForearmL", "HandL"})
    hug(dm, heap, TENTS, floor=0.0)
    m.animation("die", 45, {0: {}, 4: flinch, 14: sag, 28: fall, 44: heap}, end="Hold")
    return dm


def keys(fn, frames, step):
    return {f: fn(f) for f in range(0, frames, step)}


def check(m, ignore=()):
    for code, frames, ks, end, _ in m.animations:
        lo = min(rig.posed_extent(m, k, ignore)[0] for k in ks.values())
        hi = max(rig.posed_extent(m, k, ignore)[1] for k in ks.values())
        print(f"  {code}: {frames} frames, {len(ks)} keys, lowest {lo:.2f} px, highest {hi:.2f} px")


# ================= The Infecting Agent =================

AG_SKIN, AG_BELLY = (36, 37, 44), (74, 68, 66)
AG_SEGS = ["Seg3", "Seg2", "AHead", "Seg4", "Seg5", "Tail"]


def agent_skin(ctx):
    base = AG_BELLY if ctx.face == "down" else AG_SKIN
    wet_skin(ctx, base=base, streaks=0.6)
    if ctx.face not in ("east", "west"):
        rig.plates(ctx, 1, axis="u", seam=0.55, lit=1.3, swell=0.2)


def agent_maw(ctx):
    """The lamprey disc: on its front (west) face a round mouth, rings of teeth going in to a dark throat."""
    if ctx.face != "west":
        agent_skin(ctx)
        return
    px = ctx.img.load()
    cx, cy = ctx.w / 2, ctx.h / 2
    r = min(ctx.w, ctx.h) / 2
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
            d = math.hypot(dx, dy) / r
            a = (math.atan2(dy, dx) / TAU) % 1.0
            # two rings of fangs pointing in to the throat, each tooth wide at its root and sharp at its tip
            if d < 0.2:
                c = (14, 2, 3)
            elif d < 0.42:
                k = (d - 0.2) / 0.22
                c = TOOTH_DIM if abs(((a * 6 + 0.5) % 1.0) - 0.5) < 0.12 + 0.3 * k else FLESH_DARK
            elif d < 0.7:
                k = (d - 0.42) / 0.28
                c = TOOTH if abs(((a * 9) % 1.0) - 0.5) < 0.1 + 0.32 * k else GUM
            elif d < 0.86:
                c = FLESH
            elif d < 1.05:
                c = rig.mix(FLESH, AG_SKIN, 0.6)
            else:
                c = AG_SKIN
            _put(ctx, px, xx, yy, c)


def build_agent():
    m = Model(AGENT, atlas_width=24, seed=1415)
    m.light = dict(floor=10.0, ground=0.0, grad=0.25, edge=0.06, foot=0.03, drift=0.0, round=0.2)
    mid = m.part("Seg3", (-0.8, 0.0, -1.25), (1.8, 2.3, 2.5), pivot=(0, 1.1, 0), paint=agent_skin)
    s2 = m.part("Seg2", (-2.5, 0.05, -1.2), (1.7, 2.25, 2.4), pivot=(-0.8, 1.1, 0), parent=mid, paint=agent_skin)
    head = m.part("AHead", (-4.0, 0.1, -1.15), (1.5, 2.2, 2.3), pivot=(-2.5, 1.1, 0), parent=s2, paint=agent_skin)
    m.part("Maw", (-4.7, -0.15, -1.5), (0.7, 2.9, 3.0), pivot=(-4.0, 1.2, 0), parent=head, paint=agent_maw)
    s4 = m.part("Seg4", (1.0, 0.05, -1.1), (1.7, 2.05, 2.2), pivot=(1.0, 1.0, 0), parent=mid, paint=agent_skin)
    s5 = m.part("Seg5", (2.7, 0.15, -0.9), (1.5, 1.7, 1.8), pivot=(2.7, 0.9, 0), parent=s4, paint=agent_skin)
    m.part("Tail", (4.2, 0.25, -0.65), (1.2, 1.2, 1.3), pivot=(4.2, 0.8, 0), parent=s5, paint=agent_skin)
    return m


def agent_animations(m):
    front = ["Seg2", "AHead", "Maw"]
    back = ["Seg4", "Seg5", "Tail"]

    def wave(p, amp, cycles=1, lift=0.0):
        d = {"Seg3": pose((0, amp * 0.5 * math.sin(TAU * cycles * p), 0), (0, 0, 0.25 * amp / 30 * math.sin(TAU * cycles * p + 1.5)))}
        for i, n in enumerate(front):
            d[n] = pose((0, -amp * math.sin(TAU * cycles * p + 1.1 * (i + 1)), -lift * (1 if i < 2 else 0)))
        for i, n in enumerate(back):
            d[n] = pose((0, amp * math.sin(TAU * cycles * p - 1.1 * (i + 1)), 0))
        return d

    m.animation("idle", 40, {f: wave(f / 40, 14, 1) for f in range(0, 40, 4)})
    m.animation("walk", 16, {f: wave(f / 16, 26, 1) for f in range(0, 16, 2)})
    m.animation("run", 10, {f: wave(f / 10, 34, 1) for f in range(0, 10, 1)})

    def rear(k, snap=0.0, gape=0.0):
        d = {"Seg3": pose((0, 0, 0), (0, 0, 0)), "Seg2": pose((0, 0, -30 * k + 12 * snap)), "AHead": pose((0, 0, -22 * k + 22 * snap)),
             "Maw": pose((0, 0, 0), (0, 0, 0), (1, 1 + 0.25 * gape, 1 + 0.25 * gape)),
             "Seg4": pose((0, 0, 8 * k)), "Seg5": pose((0, 0, 6 * k)), "Tail": pose((0, 0, 4 * k))}
        return d

    # bite: rears and strikes forward (the hit at frame 7, 230 ms)
    m.animation("attack", 15, {0: rear(0), 4: rear(1.0, 0, 0.6), 7: rear(0.2, 1.4, 1.0), 10: rear(0.3, 0.6, 0.3), 14: rear(0)}, end="Stop")
    # spit: rears high, heaves, the maw gaping
    m.animation("spit", 18, {0: rear(0), 6: rear(1.3, 0, 0.4), 9: rear(0.9, 0.9, 1.2), 12: rear(1.0, 0.4, 0.8), 17: rear(0)}, end="Stop")
    m.animation("hurt", 8, {0: wave(0, 0), 2: wave(0.25, 40), 4: wave(0.75, 30), 7: wave(0, 0)}, end="Stop")
    curl = {"Seg3": pose((180, 20, 0), (0, 0, 0)), "Seg2": pose((0, 40, 0)), "AHead": pose((0, 45, -10)), "Maw": pose((0, 20, 0)),
            "Seg4": pose((0, 40, 0)), "Seg5": pose((0, 45, 0)), "Tail": pose((0, 40, 0))}
    rig.settle(m, curl, floor=-0.1)
    m.animation("die", 20, {0: {}, 4: wave(0.25, 45), 8: wave(0.75, 45), 19: curl}, end="Hold")


# ================= Sounds =================

def sounds():
    from gen_entity_sounds import RATE, band, place, reverb, seconds, vowel
    from gen_level_sounds import write as write_ogg

    def norm(x):
        return x / max(1e-9, np.max(np.abs(x)))

    def bubbles(rng, n, rate, depth=0.8):
        """A gate of wet bubbles: random pops at about `rate` a second, each a short resonant blip."""
        out = np.zeros(n)
        t = 0.0
        while t < n / RATE:
            t += rng.exponential(1 / rate)
            L = int(rng.uniform(0.012, 0.04) * RATE)
            tt = np.arange(L) / RATE
            f = rng.uniform(180, 700)
            blip = np.sin(2 * np.pi * f * tt * (1 + 1.5 * tt / tt[-1])) * np.exp(-tt * rng.uniform(60, 140))
            place(out, blip * rng.uniform(0.4, 1.0) * depth, t)
        return out

    def breath(rng, length, f0):
        t = seconds(length)
        n = len(t)
        # in, then a long wet out: two swells of low air through liquid
        env = np.interp(t, [0, 0.35 * length, 0.45 * length, 0.55 * length, 0.95 * length, length], [0, 0.6, 0.35, 1.0, 0.4, 0])
        air = norm(band(rng.normal(size=n), 90, 900)) * env
        f = f0 + 8 * np.sin(2 * np.pi * 0.8 * t) + 6 * rng.normal(size=n).cumsum() / np.sqrt(n)
        voice = norm(vowel(t, f, ((320, 90, 1.0), (700, 140, 0.5), (2100, 260, 0.12)), breath=0.6, rng=rng))
        gurg = bubbles(rng, n, 22) * env
        rattle = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * (11 + 4 * np.sin(2 * np.pi * 0.6 * t)) * t)) ** 2
        out = 0.55 * air + 0.5 * voice * rattle * env + 0.7 * band(gurg, 100, 2400)
        return reverb(band(out, 40, 5000), decay=0.45)

    def drag(rng, length):
        t = seconds(length)
        n = len(t)
        env = np.sin(np.pi * np.clip(t / length, 0, 1)) ** 0.8
        slide = norm(band(rng.normal(size=n), 120, 1400)) * env * (0.6 + 0.4 * np.sin(2 * np.pi * 3.2 * t) ** 2)
        squelch = band(bubbles(rng, n, 30, 1.0), 120, 3000) * env
        slap = np.zeros(n)
        for at in (0.05 * length, 0.45 * length + rng.uniform(-0.05, 0.05)):
            L = int(0.09 * RATE)
            tt = np.arange(L) / RATE
            place(slap, norm(band(rng.normal(size=L), 80, 1600)) * np.exp(-tt * 38) * 1.2, at)
        return 0.5 * slide + 0.8 * squelch + slap

    def shriek(rng):
        length = 1.7
        t = seconds(length)
        n = len(t)
        f0 = 260 + 340 * np.clip(t / 0.25, 0, 1) - 120 * np.clip((t - 0.9) / 0.8, 0, 1) + 18 * np.sin(2 * np.pi * 37 * t)
        a = norm(vowel(t, f0, ((900, 220, 1.0), (1600, 260, 0.8), (3100, 400, 0.5)), breath=1.4, rng=rng))
        b = norm(vowel(t, f0 * 1.51, ((800, 200, 1.0), (2400, 300, 0.6), (3600, 500, 0.3)), breath=1.0, rng=rng))
        rasp = norm(band(rng.normal(size=n), 1200, 7000)) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 37 * t)))
        low = norm(vowel(t, f0 * 0.25, ((260, 80, 1.0), (600, 120, 0.4)), breath=0.8, rng=rng))
        wet = band(bubbles(rng, n, 40), 150, 3000)
        env = np.clip(t / 0.06, 0, 1) * np.clip((length - t) / 0.5, 0, 1)
        out = (0.8 * a + 0.45 * b + 0.45 * rasp + 0.5 * low + 0.4 * wet) * env
        return reverb(out, decay=0.6)

    def lash(rng):
        t = seconds(0.6)
        n = len(t)
        out = np.zeros(n)
        frame = int(0.015 * RATE)
        noise = rng.normal(size=n)
        for i in range(0, int(0.2 * RATE) - frame, frame):
            c = 500 + 3500 * (i / (0.2 * RATE)) ** 1.5
            out[i:i + frame] += band(noise[i:i + frame] * np.hanning(frame), c * 0.6, c * 1.5) * (i / (0.2 * RATE))
        whoosh = norm(out)
        smack = norm(band(rng.normal(size=n), 90, 2500)) * np.where(t >= 0.2, np.exp(-(t - 0.2) * 30), 0)
        crack = norm(band(rng.normal(size=n), 2500, 10000)) * np.where(t >= 0.2, np.exp(-(t - 0.2) * 90), 0)
        suck = band(bubbles(rng, n, 50), 200, 3000) * np.where(t >= 0.22, np.exp(-(t - 0.22) * 6), 0)
        return 0.5 * whoosh + 1.1 * smack + 0.6 * crack + 0.8 * suck

    def hurt(rng):
        t = seconds(0.55)
        n = len(t)
        f0 = 300 - 140 * t / 0.55 + 20 * np.sin(2 * np.pi * 29 * t)
        v = norm(vowel(t, f0, ((700, 180, 1.0), (1300, 240, 0.6), (2700, 320, 0.3)), breath=1.0, rng=rng))
        wet = band(bubbles(rng, n, 45), 150, 3000)
        return (v + 0.6 * wet) * np.clip(t / 0.02, 0, 1) * np.exp(-t * 4)

    def death(rng):
        length = 2.6
        t = seconds(length)
        n = len(t)
        f0 = 200 - 130 * (t / length) ** 0.7 + 10 * np.sin(2 * np.pi * 21 * t)
        v = norm(vowel(t, f0, ((600, 160, 1.0), (1100, 220, 0.5), (2400, 300, 0.2)), breath=1.2, rng=rng))
        v *= np.interp(t, [0, 0.05, 1.2, 2.0], [0, 1, 0.5, 0])
        gurg = band(bubbles(rng, n, 30), 100, 2500) * np.interp(t, [0, 0.5, 2.2, length], [0.3, 1, 0.6, 0])
        slump = np.zeros(n)
        for at, g in ((1.25, 1.0), (1.55, 0.7), (1.9, 0.5)):
            L = int(0.25 * RATE)
            tt = np.arange(L) / RATE
            place(slump, norm(band(rng.normal(size=L), 40, 700)) * np.exp(-tt * 14) * g, at)
        return reverb(0.7 * v + 0.8 * gurg + 1.0 * slump, decay=0.5)

    def release(rng):
        t = seconds(0.6)
        n = len(t)
        pop = norm(band(rng.normal(size=n), 150, 2200)) * np.where(t >= 0.05, np.exp(-(t - 0.05) * 25), 0)
        gl = np.sin(2 * np.pi * (180 + 500 * np.clip((t - 0.05) / 0.12, 0, 1)) * t) * np.where((t > 0.05) & (t < 0.2), 1, 0) * np.exp(-np.abs(t - 0.1) * 20)
        wet = band(bubbles(rng, n, 60), 200, 4000) * np.exp(-t * 6)
        return 0.9 * pop + 0.5 * gl + 0.7 * wet

    def chitter(rng):
        t = seconds(0.55)
        n = len(t)
        out = np.zeros(n)
        at = 0.0
        while at < 0.45:
            L = int(0.008 * RATE)
            tt = np.arange(L) / RATE
            place(out, norm(band(rng.normal(size=L), 2500, 9000)) * np.exp(-tt * 500) * rng.uniform(0.4, 1.0), at)
            at += rng.uniform(0.015, 0.05)
        hiss = norm(band(rng.normal(size=n), 3000, 9000)) * 0.15 * np.sin(np.pi * t / 0.55)
        squeal = np.sin(2 * np.pi * (2400 + 600 * np.sin(2 * np.pi * 9 * t)) * t) * 0.18 * np.exp(-np.abs(t - 0.25) * 9)
        return out + hiss + squeal

    def bite(rng):
        t = seconds(0.3)
        n = len(t)
        snap = norm(band(rng.normal(size=n), 2000, 9000)) * np.exp(-t * 80)
        crunch = np.zeros(n)
        for at in (0.02, 0.05, 0.08):
            L = int(0.01 * RATE)
            place(crunch, norm(band(rng.normal(size=L), 900, 6000)) * np.exp(-np.arange(L) / RATE * 300), at)
        wet = band(bubbles(rng, n, 80), 300, 4000) * np.exp(-t * 10)
        return snap + 0.8 * crunch + 0.6 * wet

    def spit(rng):
        t = seconds(0.7)
        n = len(t)
        hawk = norm(band(rng.normal(size=n), 600, 4000)) * np.where(t < 0.18, np.sin(np.pi * t / 0.18), 0) * 0.6
        ptoo = norm(band(rng.normal(size=n), 300, 3000)) * np.where(t >= 0.18, np.exp(-(t - 0.18) * 40), 0)
        sizz = norm(band(rng.normal(size=n), 3500, 12000)) * np.where(t >= 0.3, np.exp(-(t - 0.3) * 5), 0) * 0.35
        return hawk + ptoo + sizz * (0.6 + 0.4 * rng.random(n))

    def sizzle(rng):
        t = seconds(1.0)
        n = len(t)
        crackle = np.zeros(n)
        for at in rng.uniform(0, 0.9, 60):
            L = int(0.003 * RATE)
            place(crackle, rng.choice((-1, 1)) * np.linspace(1, 0, L) * rng.uniform(0.2, 1.0), at)
        hiss = norm(band(rng.normal(size=n), 2500, 12000)) * np.exp(-t * 3)
        return 0.7 * hiss + crackle * np.exp(-t * 2)

    def agent_death(rng):
        t = seconds(0.45)
        n = len(t)
        squish = norm(band(rng.normal(size=n), 150, 2500)) * np.exp(-t * 18)
        squeal = np.sin(2 * np.pi * (2600 - 1800 * t / 0.45) * t) * 0.3 * np.exp(-t * 7)
        return squish + squeal + 0.5 * band(bubbles(rng, n, 40), 300, 3000) * np.exp(-t * 6)

    written = []

    def write(name, sig, peak):
        write_ogg("entity/14", name, sig, peak)
        written.append(name)

    for i, (seed, length, f0) in enumerate(((1401, 2.6, 62), (1402, 3.1, 55), (1403, 2.3, 70)), 1):
        write(f"hunter-breath{i}", breath(np.random.default_rng(seed), length, f0), 0.6)
    for i, (seed, length) in enumerate(((1411, 0.8), (1412, 0.95), (1413, 0.7)), 1):
        write(f"hunter-drag{i}", drag(np.random.default_rng(seed), length), 0.45)
    write("hunter-shriek", shriek(np.random.default_rng(1421)), 0.8)
    write("hunter-lash", lash(np.random.default_rng(1422)), 0.7)
    write("hunter-hurt", hurt(np.random.default_rng(1423)), 0.6)
    write("hunter-death", death(np.random.default_rng(1424)), 0.7)
    write("hunter-release", release(np.random.default_rng(1425)), 0.55)
    write("agent-chitter1", chitter(np.random.default_rng(1431)), 0.45)
    write("agent-chitter2", chitter(np.random.default_rng(1432)), 0.45)
    write("agent-bite", bite(np.random.default_rng(1433)), 0.55)
    write("agent-spit", spit(np.random.default_rng(1434)), 0.5)
    write("agent-sizzle", sizzle(np.random.default_rng(1435)), 0.45)
    write("agent-death", agent_death(np.random.default_rng(1436)), 0.5)
    print(f"Level 14 creature sounds: {len(written)}")


def generate(do_sounds=True):
    m = build_hunter()
    hunter_animations(m)
    m.save()
    lo, hi = rig.posed_extent(m, {})
    print(f"  Hunter rest height {hi:.1f} px = {hi / 16:.2f} blocks (lowest {lo:.2f})")
    check(m)
    a = build_agent()
    agent_animations(a)
    a.save()
    lo, hi = rig.posed_extent(a, {})
    xs = []
    mats = rig.part_matrices(a)
    for p in a.parts:
        c = np.array([[x * p.size[0], y * p.size[1], z * p.size[2], 1] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
        xs.extend((mats[id(p)] @ c.T)[0])
    print(f"  Agent length {(max(xs) - min(xs)) / 16:.2f} blocks, height {hi / 16:.2f}")
    check(a)
    if do_sounds:
        sounds()


if __name__ == "__main__":
    generate("--nosounds" not in sys.argv)
