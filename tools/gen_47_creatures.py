"""Level 47 (The Adderwood, Wikidot Level 47): the level's creature models. Writes shapes, textures and entity types:

    l47-snake        an ordinary forest snake, four species as texture alternates (grass snake, adder, black rat snake,
                     ringed milk snake); a chain of nine body segments behind a head with eyes and a forked tongue
    l47-greatadder   the Great Old Adder, a bright crimson titanoboa about 9.5 blocks long laid in a loose S behind its
                     head; a hinged jaw, fangs, glowing amber eyes with slit pupils, heavy brow scales
    l47-shuck        the Black Shuck: the vanilla wolf's shape with coal-black textures painted from a vanilla wolf's
    l47-ophion       a member of the Ophion Occult Order: hooded crimson robe, ivory mask with a carved serpent, a gold
                     clasp shaped as a snake eating its tail, a cord belt (plain, and an elder's with gold hems)

The C# AI, spawning and lang are written elsewhere (each entity's taskai has one task, backrooms-<code>).

Serpent rig: the body is a chain of boxes along X (the head at -X, as rig.py's models face). One segment about a third of
the way back (`root`) is the root part; the segments in front of it are chained toward the head (each a child of the one
behind it, pivoting at its rear end) and those behind it toward the tail (each a child of the one in front, pivoting at
its front end), so the front can rear up while the rest lies on the ground. Every segment is a little smaller than its
parent and reaches into it by about half its width, so a bend never opens a gap and nothing z-fights. Poses are given as
each part's orientation in the model (heading about Y, pitch about Z, roll about X) and turned into the local Euler
angles the game wants (`Serpent.pose`), so a travelling wave or a rear is written as a curve, not as joint angles.

Run from the repo root:  bash tools/locked.sh run python tools/gen_47_creatures.py [snake|adder|ophion|shuck|json]
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import rig  # noqa: E402
from rig import Model, pose  # noqa: E402

TAU = math.tau
FACEK = {"up": 1.1, "down": 0.72, "north": 0.93, "south": 0.93, "east": 0.86, "west": 1.0}


def put(ctx, px, xx, yy, c):
    if 0 <= xx < ctx.w and 0 <= yy < ctx.h:
        px[ctx.x + xx, ctx.y + yy] = rig.clamp(c) + (255,)


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def tri(t):
    """A triangle wave in [-1, 1] with period 1."""
    t = t - math.floor(t)
    return 4 * t - 1 if t < 0.5 else 3 - 4 * t


def noise1(seed, x, cell=1.0):
    """Smooth 1D value noise in [-1, 1]."""
    i = math.floor(x / cell)
    f = x / cell - i
    a = random.Random(seed * 7919 + i).uniform(-1, 1)
    b = random.Random(seed * 7919 + i + 1).uniform(-1, 1)
    return a + (b - a) * smooth(f)


# ================================================================ the serpent rig

def _R(ax, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    if ax == 0:
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if ax == 1:
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def orient(psi=0.0, theta=0.0, phi=0.0):
    """A part's orientation in the model: heading psi about Y, then pitch theta about its Z, then roll phi about its X."""
    return _R(1, psi) @ _R(2, theta) @ _R(0, phi)


def euler_xyz(R):
    """The game's Euler angles (R = Rx(a) Ry(b) Rz(c)) of a rotation matrix, in degrees."""
    b = math.asin(max(-1.0, min(1.0, R[0, 2])))
    c = math.atan2(-R[0, 1], R[0, 0])
    a = math.atan2(-R[1, 2], R[2, 2])
    return tuple(math.degrees(v) for v in (a, b, c))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


class Serpent:
    """A chain of segments behind a head. segs: [(length, width, height)] from the neck (Seg0) to the tail tip."""

    def __init__(self, m, hx0, head_len, segs, root, ov=0.45):
        self.m, self.segs, self.root = m, segs, root
        self.hx0, self.head_len = hx0, head_len
        self.names = [f"Seg{i}" for i in range(len(segs))]
        self.a = []
        a = hx0 + head_len
        for L, _, _ in segs:
            self.a.append(a)
            a += L
        self.tail = a
        self.total = a - hx0
        self.ov = ov
        self.chain = ["Head"] + self.names        # head to tail

    def y0(self, i):
        return 0.025 * abs(i - self.root)

    def build(self, paint):
        m, r = self.m, self.root
        L, w, h = self.segs[r]
        m.part(self.names[r], (self.a[r], self.y0(r), -w / 2), (L, h, w), pivot=(self.a[r] + L / 2, h / 2, 0), paint=paint)
        for i in range(r - 1, -1, -1):           # toward the head: each reaches back into the one behind it
            L, w, h = self.segs[i]
            ov = self.ov * w
            front = self.a[i] - (ov if i == 0 else 0.0)  # the neck also reaches forward into the head
            m.part(self.names[i], (front, self.y0(i), -w / 2), (self.a[i] + L + ov - front, h, w),
                   pivot=(self.a[i] + L, self.y0(i) + h / 2, 0), parent=self.names[i + 1], paint=paint)
        for j in range(r + 1, len(self.segs)):   # toward the tail: each reaches forward into the one in front
            L, w, h = self.segs[j]
            ov = self.ov * w
            m.part(self.names[j], (self.a[j] - ov, self.y0(j), -w / 2), (L + ov, h, w),
                   pivot=(self.a[j], self.y0(j) + h / 2, 0), parent=self.names[j - 1], paint=paint)

    def centres(self):
        """Arc position (0 at the snout, 1 at the tail tip) of the middle of each chain part, head first."""
        out = [self.head_len / 2 / self.total]
        for i, (L, _, _) in enumerate(self.segs):
            out.append((self.a[i] + L / 2 - self.hx0) / self.total)
        return out

    # ---- poses
    def local(self, world):
        """Local Euler angles of every part named in `world` ({name: 3x3 orientation in the model})."""
        out = {}
        for name, W in world.items():
            p = self.m.by_name[name]
            Wp = np.eye(3)
            q = p.parent
            if q is not None:
                Wp = world.get(q.name)
                if Wp is None:
                    Wp = np.eye(3)
            out[name] = euler_xyz(Wp.T @ W)
        return out

    def set_rest(self, world):
        for name, e in self.local(world).items():
            self.m.by_name[name].rest = tuple(round(v, 3) for v in e)

    def pose(self, world, extra=None):
        """A keyframe from orientations: each part's local angles less its rest angles; `extra` poses merged on top."""
        out = {}
        for name, e in self.local(world).items():
            rest = self.m.by_name[name].rest
            out[name] = pose(tuple(round(wrap(e[k] - rest[k]), 3) for k in range(3)))
        for name, ps in (extra or {}).items():
            if name in out:
                a = out[name]
                out[name] = pose(tuple(a["rot"][k] + ps.get("rot", (0, 0, 0))[k] for k in range(3)),
                                 tuple(a["off"][k] + ps.get("off", (0, 0, 0))[k] for k in range(3)))
            else:
                out[name] = pose(ps.get("rot", (0, 0, 0)), ps.get("off", (0, 0, 0)))
        return out

    def world(self, psi, elev=None, roll=None):
        """Orientations from per-part lists (head first, as self.chain): heading, elevation of the head-ward end (up
        positive), roll."""
        n = len(self.chain)
        elev = elev or [0.0] * n
        roll = roll or [0.0] * n
        return {name: orient(psi[k], -elev[k], roll[k]) for k, name in enumerate(self.chain)}


def wave(us, amp, waves, phase, head_k=0.4, taper=None):
    """Headings along the body for a serpenoid curve: amp * sin(2 pi (u * waves - phase)), the mean taken off so the
    body lies along the facing, the head turned only head_k as far as its neck."""
    psi = [amp * (taper(u) if taper else 1.0) * math.sin(TAU * (u * waves - phase)) for u in us]
    mean = sum(psi[1:]) / (len(psi) - 1)
    psi = [p - mean for p in psi]
    psi[0] = psi[1] * head_k
    return psi


def keyframes(fn, frames, step, extra_frames=(), loop=True):
    fr = set(range(0, frames, step)) | set(f for f in extra_frames if 0 <= f < frames)
    if not loop:
        fr.add(frames - 1)
    return {f: fn(f) for f in sorted(fr)}


# ================================================================ serpent skin

def scale_k(s, d, sz, rim=0.22):
    """Diamond scales on the (along-body s, around-body d) sheet: lit centres, darker edges."""
    row = math.floor(d / sz)
    fs = s / sz + 0.5 * row
    col = math.floor(fs)
    a = abs(fs - col - 0.5) * 2
    b = abs(d / sz - row - 0.5) * 2
    r = (a + b) / 2
    return 1.06 - rim * r * r - (0.08 if r > 0.86 else 0.0)


def skin_painter(look):
    """Paints body segments from a look: look(s, d, hf, region, rng) -> rgb, where s is the arc position (model x, the
    snout at the front), d the signed distance round the body from the dorsal midline (left +), hf how high up a side
    face (1 top, 0 bottom), region 'top', 'side', 'belly' or 'end'."""
    def paint(ctx):
        p = ctx.part
        sx, sy, sz = p.size
        x0 = p.frm[0]
        px = ctx.img.load()
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                u, v = (xx + 0.5) / ctx.w, (yy + 0.5) / ctx.h
                f = ctx.face
                if f == "up":
                    s, d, hf, region = x0 + u * sx, (v - 0.5) * sz, 1.0, "top"
                elif f == "south":
                    s, d, hf, region = x0 + u * sx, sz / 2 + v * sy, 1 - v, "side"
                elif f == "north":
                    s, d, hf, region = x0 + (1 - u) * sx, -(sz / 2 + v * sy), 1 - v, "side"
                elif f == "down":
                    s, d, hf, region = x0 + u * sx, ((1 - v) - 0.5) * sz, 0.0, "belly"
                else:   # the end faces: a cross-section, top dorsal, bottom belly
                    s = x0 if f == "west" else x0 + sx
                    d, hf, region = (u - 0.5) * sz, 1 - v, "end"
                c = look(s, d, hf, region, ctx.rng, p)
                if region == "side":
                    k = 0.8 + 0.28 * hf
                elif region == "top":
                    k = 1.1
                elif region == "belly":
                    k = 0.82
                else:
                    k = 0.78 + 0.25 * hf
                put(ctx, px, xx, yy, rig.shade(c, k))
    return paint


def plain(c, k=1.0):
    def paint(ctx):
        px = ctx.img.load()
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                put(ctx, px, xx, yy, rig.shade(c, k * FACEK[ctx.face] * (0.95 + 0.1 * ctx.rng.random())))
    return paint


# ================================================================ the forest snake

SNAKE = "47/l47-snake"
SNAKE_TEXEL = 4
# (length, width, height) from the neck to the tail tip; the root is Seg3
SNAKE_SEGS = [(2.2, 1.9, 1.6), (2.4, 2.2, 1.85), (2.5, 2.4, 2.0), (2.6, 2.5, 2.1), (2.6, 2.38, 2.0), (2.5, 2.1, 1.8),
              (2.4, 1.7, 1.45), (2.2, 1.25, 1.1), (2.0, 0.75, 0.66)]
SNAKE_ROOT = 3
SNAKE_HX0 = -10.0
SNAKE_HEAD = 3.7


class SnakeLook:
    """One species: body(s, d, hf, region) and the head's colours."""

    def __init__(self, key):
        self.key = key
        self.neck = SNAKE_HX0 + SNAKE_HEAD     # where the head ends

    def body(self, s, d, hf, region, rng, part):
        k = self.key
        sn = s - self.neck
        ad = abs(d)
        sk = scale_k(s, d, 0.55, 0.18)
        jit = 1 + 0.06 * (rng.random() - 0.5)
        belly = region == "belly" or (region in ("side", "end") and hf < 0.17)
        # glossy sheen along the upper left of the back (the light comes from above)
        sheen = math.exp(-((d + 0.25) / 0.55) ** 2) if region == "top" else (0.35 * hf * hf if region == "side" else 0)
        if k == "grass":
            if belly:
                c = (214, 210, 176)
                if (math.floor(sn / 0.8) + (d > 0)) % 2 == 0 and noise1(5, s, 0.8) > 0.2:
                    c = (64, 66, 60)
                return rig.shade(c, sk * jit)
            c = rig.mix((92, 104, 48), (112, 120, 60), 0.5 + 0.5 * noise1(1, s, 2.0))
            if 0.15 < sn < 0.95 and ad > 0.45:                    # the yellow-white collar, a patch each side
                c = rig.mix((236, 222, 132), (240, 236, 200), hf)
            elif 0.95 <= sn < 1.55 and ad > 0.3:                  # and the black crescent behind it
                c = (24, 24, 20)
            elif region == "side" and 0.22 < hf < 0.85 and sn > 1.6:   # dark bars down the sides
                ph = (sn / 1.7 + (0.5 if d < 0 else 0)) % 1
                if ph < 0.22 and noise1(3, s, 0.7) > -0.6:
                    c = (30, 34, 22)
            elif region == "top" and sn > 1.6:                     # two rows of small dark spots down the back
                ph = (sn / 1.5 + (0.5 if d < 0 else 0)) % 1
                if ph < 0.2 and 0.25 < ad < 0.75:
                    c = rig.mix(c, (38, 44, 24), 0.75)
            c = rig.mix(c, (186, 196, 120), 0.18 * sheen)
            return rig.shade(c, sk * jit)
        if k == "adder":
            if belly:
                c = rig.mix((150, 146, 140), (192, 188, 176), 0.5 + 0.5 * noise1(7, s, 1.0))
                return rig.shade(c, sk * jit)
            c = rig.mix((132, 116, 94), (156, 140, 112), 0.5 + 0.5 * noise1(2, s, 1.6))
            if region == "side":
                c = rig.mix(c, (118, 100, 80), 0.4 * (1 - hf))
            zz = 0.5 * tri(sn / 1.9 + 0.25)                       # the zigzag down the back
            dd = d if region == "top" else (math.copysign(part.size[2] / 2 + (1 - hf) * part.size[1], d))
            if sn > 0.0 and abs(dd - zz) < 0.36 + 0.08 * math.cos(TAU * sn / 1.9):
                c = (30, 26, 24)
            if region == "side" and sn > 0.5:                      # a row of dark spots on each flank
                ph = (sn / 1.9 + (0.25 if d > 0 else 0.75)) % 1
                if abs(ph - 0.5) < 0.13 and 0.35 < hf < 0.75:
                    c = (52, 44, 38)
            c = rig.mix(c, (210, 200, 180), 0.12 * sheen)
            return rig.shade(c, sk * jit)
        if k == "rat":
            t = max(0.0, min(1.0, sn / 9.0))
            if belly:
                c = rig.mix((228, 224, 206), (120, 118, 112), t)
                if t > 0.25 and (math.floor(sn / 0.8) + (d > 0)) % 2 == 0:
                    c = rig.mix(c, (36, 36, 38), 0.6 * t)
                return rig.shade(c, sk * jit)
            c = (22, 22, 26)
            ghost = noise1(4, s, 1.3)                             # faint blotches showing through the black
            if ghost > 0.45 and region in ("top", "side"):
                c = rig.mix(c, (48, 42, 38), 0.6)
            if region == "side" and hf < 0.35 and sn < 2.5:       # the pale chin running onto the throat
                c = rig.mix(c, (210, 206, 190), 1 - sn / 2.5)
            c = rig.mix(c, (110, 116, 132), 0.55 * sheen)
            sk = 1 + (sk - 1) * 2.2
            return rig.shade(c, sk * jit)
        # ringed: a milk snake's red, black, yellow, black bands
        ph = (sn - 0.1) % 3.2
        if ph < 1.75:
            c = (186, 40, 30)
        elif ph < 2.1:
            c = (22, 20, 20)
        elif ph < 2.75:
            c = (232, 206, 118)
        else:
            c = (22, 20, 20)
        if belly:
            c = rig.mix((222, 214, 190), c, 0.35 if ph < 1.75 else 0.75)
        c = rig.mix(c, (255, 240, 220), 0.14 * sheen)
        return rig.shade(c, sk * jit)

    def head_top(self, u, v, rng, region):
        """The skull and snout, u along the head (0 the snout tip, 1 the back), v across (0 right, 1 left) on top or
        down a side (region 'top', 'side' with v 0 top .. 1 bottom, 'front', 'chin')."""
        k = self.key
        lip = region == "side" and v > 0.62
        if k == "grass":
            if region == "chin":
                return (226, 222, 196)
            c = rig.mix((88, 100, 44), (108, 116, 56), rng.random() * 0.5)
            if lip:
                c = (222, 216, 176)
                if int(u * 7) % 2 == 1 and v > 0.7:
                    c = (40, 42, 30)
            return c
        if k == "adder":
            if region == "chin":
                return (190, 176, 150)
            c = rig.mix((136, 120, 96), (156, 140, 112), rng.random() * 0.5)
            if region == "top":
                # a dark V on the crown, opening back toward the neck
                if abs(abs(v - 0.5) - 0.4 * u) < 0.1 and u > 0.25:
                    c = (32, 28, 26)
            if region == "side" and 0.35 < v < 0.6 and u > 0.35:   # the dark stripe back from the eye
                c = (40, 32, 28)
            if lip:
                c = (196, 180, 150)
            return c
        if k == "rat":
            if region == "chin" or lip:
                return (224, 220, 204)
            return rig.mix((22, 22, 26), (64, 66, 76), 0.4 * rng.random() + (0.4 if region == "top" else 0.0))
        # ringed: a pale snout, a black crown band
        if region == "chin":
            return (222, 214, 190)
        if u < 0.32:
            return (214, 206, 186) if region != "top" else (190, 60, 40)
        if u < 0.7:
            return (24, 22, 22)
        return (226, 200, 116) if region != "top" else (24, 22, 22)

    def iris(self):
        return {"grass": (36, 30, 20), "adder": (170, 64, 30), "rat": (40, 34, 30), "ringed": (30, 26, 24)}[self.key]


def head_painter(look, kind):
    """The skull ('skull') or the snout ('snout'): u runs from the snout tip back, as head_top expects."""
    def paint(ctx):
        p = ctx.part
        px = ctx.img.load()
        # the head runs from SNAKE_HX0 (u 0) to SNAKE_HX0 + SNAKE_HEAD (u 1)
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                fu, fv = (xx + 0.5) / ctx.w, (yy + 0.5) / ctx.h
                f = ctx.face
                x = p.frm[0] + (fu if f in ("up", "south", "down") else 1 - fu) * p.size[0]
                u = (x - SNAKE_HX0) / SNAKE_HEAD
                if f == "up":
                    c = look.head_top(u, fv, ctx.rng, "top")
                elif f in ("south", "north"):
                    c = look.head_top(u, fv, ctx.rng, "side")
                elif f == "down":
                    c = look.head_top(u, fv, ctx.rng, "chin")
                elif f == "west":
                    c = look.head_top(0.0, fv, ctx.rng, "side" if fv > 0.25 else "top")
                    if kind == "snout" and 0.3 < fv < 0.5 and (abs(fu - 0.25) < 0.1 or abs(fu - 0.75) < 0.1):
                        c = (20, 16, 14)      # nostrils
                    if fv > 0.75:
                        c = rig.shade(c, 0.8)  # the mouth line
                else:
                    c = look.head_top(1.0, fv, ctx.rng, "side")
                put(ctx, px, xx, yy, rig.shade(c, FACEK[f] * (0.96 + 0.08 * ctx.rng.random())))
    return paint


def snake_eye(look):
    def paint(ctx):
        px = ctx.img.load()
        out = ctx.face == ("south" if ctx.part.name.endswith("L") else "north")
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                c = look.iris() if out else rig.shade(look.iris(), 0.6)
                put(ctx, px, xx, yy, c)
        if out:
            cx, cy = ctx.w // 2, ctx.h // 2
            for yy in range(ctx.h):
                put(ctx, px, cx, yy, (6, 6, 6) if look.key == "adder" else (8, 8, 8))
            if look.key != "adder":
                put(ctx, px, cx - 1, cy, (8, 8, 8))
            put(ctx, px, ctx.w - 1, 0, (236, 236, 226))   # a wet highlight
    return paint


def tongue_paint(ctx):
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, px, xx, yy, rig.shade((70, 18, 30), 0.8 + 0.3 * ctx.rng.random()))


def build_snake(look):
    m = Model(SNAKE, atlas_width=24, seed=471)
    sp = Serpent(m, SNAKE_HX0, SNAKE_HEAD, SNAKE_SEGS, SNAKE_ROOT, ov=0.42)
    sp.build(skin_painter(look.body))
    hx = SNAKE_HX0
    head = m.part("Head", (hx + 1.1, 0.05, -1.35), (2.6, 1.75, 2.7), pivot=(hx + SNAKE_HEAD, 0.85, 0), parent="Seg0",
                  paint=head_painter(look, "skull"))
    m.part("Snout", (hx, 0.1, -1.0), (1.15, 1.35, 2.0), pivot=(hx + 1.1, 0.7, 0), parent=head, paint=head_painter(look, "snout"))
    m.part("EyeL", (hx + 1.25, 0.95, 1.2), (0.75, 0.6, 0.3), pivot=(hx + 1.6, 1.25, 1.35), parent=head, paint=snake_eye(look))
    m.mirror("EyeL", "EyeR")
    t = m.part("Tongue", (hx + 0.35, 0.38, -0.12), (1.3, 0.14, 0.24), pivot=(hx + 1.65, 0.45, 0), parent=head, paint=tongue_paint)
    m.part("ForkL", (hx - 0.25, 0.39, 0.0), (0.65, 0.12, 0.12), pivot=(hx + 0.38, 0.45, 0.05), parent=t, rest=(0, -14, 0), paint=tongue_paint)
    m.part("ForkR", (hx - 0.25, 0.39, -0.12), (0.65, 0.12, 0.12), pivot=(hx + 0.38, 0.45, -0.05), parent=t, rest=(0, 14, 0), paint=tongue_paint)
    return m, sp


def snake_rest(sp):
    us = sp.centres()
    psi = wave(us, 34, 1.15, 0.05, head_k=0.5)
    return us, psi


def snake_animations(m, sp):
    us, rest_psi = snake_rest(sp)
    sp.set_rest(sp.world(rest_psi))
    n = len(sp.chain)
    ia = {name: k for k, name in enumerate(sp.chain)}
    r = sp.root + 1                     # the root's index in chain (the head is 0)

    def tongue(out, spread=1.0, tilt=0.0):
        return {"Tongue": {"off": (-1.45 * out, 0, 0), "rot": (0, 0, tilt)},
                "ForkL": {"rot": (0, -14 * spread * out, 0)}, "ForkR": {"rot": (0, 14 * spread * out, 0)}}

    def flick(f, starts, length=10):
        """Tongue out-in twice over `length` frames from each start."""
        for st in starts:
            q = f - st
            if 0 <= q <= length:
                return [0, 0.8, 1.0, 0.3, 0.9, 1.0, 0.6, 0.2, 0, 0, 0][q]
        return 0.0

    # ---- idle: 4 s; the S breathing a little, the head turning, the tongue flicked twice
    def idle(f):
        p = f / 120
        psi = [rest_psi[k] + 3.0 * us[k] * math.sin(TAU * (p - us[k] * 0.6)) for k in range(n)]
        psi[0] += 9 * math.sin(TAU * p)
        elev = [0.0] * n
        elev[0] = 4 + 3 * math.sin(TAU * 2 * p)
        o = flick(f, (22, 78))
        return sp.pose(sp.world(psi, elev), tongue(o, tilt=6 * math.sin(f)))

    m.animation("idle", 120, keyframes(idle, 120, 6, extra_frames=[s + q for s in (22, 78) for q in range(0, 11)]))

    # ---- slither: 1 s; a travelling wave along the chain, the head held steady and a touch raised
    def slither(f):
        p = f / 30
        psi = wave(us, 30, 1.1, p, head_k=0.25)
        elev = [0.0] * n
        elev[0] = 4
        return sp.pose(sp.world(psi, elev))

    m.animation("slither", 30, keyframes(slither, 30, 2))

    # ---- rear: the front third lifted in an S, the head drawn back level, ready to strike; held
    def rear_pose(t, flicker=0.0):
        psi = list(rest_psi)
        elev = [0.0] * n
        tgt = {r - 1: 42, r - 2: 96, r - 3: 58, 0: -12}
        yaw = {r - 1: 18, r - 2: -16, r - 3: -6, 0: 4}
        for k, e in tgt.items():
            elev[k] = e * t
            psi[k] = rest_psi[k] * (1 - t) + yaw[k] * t
        for k in range(r, n):
            psi[k] = rest_psi[k] * (1 + 0.35 * t)
        return sp.pose(sp.world(psi, elev), tongue(flicker))

    m.animation("rear", 20, {0: rear_pose(0), 6: rear_pose(0.55), 11: rear_pose(1.08), 14: rear_pose(0.97, 1.0),
                             16: rear_pose(1.0, 0.3), 19: rear_pose(1.0)}, end="Hold")

    # ---- hurt: a jolt, the head snapping back
    def hurt_pose(t):
        psi = [rest_psi[k] + t * 22 * math.sin(TAU * us[k] * 1.6) for k in range(n)]
        elev = [0.0] * n
        elev[0] = 28 * t
        elev[1] = 14 * t
        return sp.pose(sp.world(psi, elev))

    m.animation("hurt", 12, {0: hurt_pose(0), 2: hurt_pose(1), 5: hurt_pose(-0.5), 8: hurt_pose(0.25), 11: hurt_pose(0)}, end="Stop")

    # ---- die: a writhe, then limp, the middle rolled belly-up and the tail left on its side; held
    def die_pose(writhe, t):
        psi = [rest_psi[k] * (1 - 0.45 * t) + writhe * math.sin(TAU * (us[k] * 1.4 + 0.2)) for k in range(n)]
        elev = [0.0] * n
        elev[0] = 18 * abs(writhe) / 30 * (1 - t) - 4 * t
        roll = [0.0] * n
        prof = {0: 95, 1: 120, 2: 140, 3: 150, 4: 155, 5: 150, 6: 120, 7: 70, 8: 40, 9: 25}
        for k in range(n):
            roll[k] = prof.get(k, 0) * t
        return sp.pose(sp.world(psi, elev, roll))

    m.animation("die", 30, {0: die_pose(0, 0), 4: die_pose(30, 0), 9: die_pose(-28, 0.1), 15: die_pose(14, 0.45),
                            22: die_pose(-4, 0.85), 29: die_pose(0, 1.0)}, end="Hold")


def save_variants(m, build_fn, looks, base_name, texel):
    """Saves the first look as the model's own texture and the others as base_name-<key>.png with the same atlas."""
    old = rig.TEXEL
    rig.TEXEL = texel
    try:
        m.save()
        shape, (w, h) = m.shape()
        for key in looks:
            b = build_fn(key)
            b.shape()
            assert all(p.uv == q.uv for p, q in zip(m.parts, b.parts)), "atlas layouts differ"
            img = b._paint(w, h)
            path = os.path.join(rig.ASSETS, "textures", "entity", base_name + "-" + key + ".png")
            img.save(path)
            print("wrote", os.path.relpath(path, rig.ROOT))
    finally:
        rig.TEXEL = old


def gen_snake():
    looks = ["grass", "adder", "rat", "ringed"]
    m, sp = build_snake(SnakeLook(looks[0]))
    snake_animations(m, sp)

    def other(key):
        b, _ = build_snake(SnakeLook(key))
        return b

    save_variants(m, other, looks[1:], SNAKE, SNAKE_TEXEL)
    lo, hi = rig.posed_extent(m, {})
    print(f"  snake length {sp.total:.1f} px = {sp.total / 16:.2f} blocks, rest height {hi:.2f} px")
    return [SNAKE + "-" + k for k in looks[1:]]


# ================================================================ the Great Old Adder

ADDER = "47/l47-greatadder"
ADDER_TEXEL = 2
ADDER_HX0 = -13.0
ADDER_HEAD = 14.0
# the neck (Seg0) to the tail tip; the root is Seg5
_W = [8.6, 9.8, 10.7, 11.3, 11.8, 12.2, 12.0, 11.7, 11.3, 10.7, 9.8, 8.4, 6.6, 4.6, 2.6]
_L = [9.0, 9.6, 9.6, 9.6, 9.6, 9.6, 9.6, 9.6, 9.6, 9.6, 9.6, 9.4, 9.0, 8.4, 7.6]
ADDER_SEGS = [(L, w, w * (0.8 if i == 0 else 0.88)) for i, (L, w) in enumerate(zip(_L, _W))]
ADDER_ROOT = 5

CRIMSON = (198, 22, 30)
CRIMSON_HI = (234, 58, 50)
CRIMSON_DK = (122, 10, 20)
SADDLE = (58, 6, 12)
CREAM = (238, 190, 158)
PINK = (196, 92, 104)


def adder_body(s, d, hf, region, rng, part):
    sn = s - (ADDER_HX0 + ADDER_HEAD)
    sk = scale_k(s + 0.3 * d, d, 1.55, 0.3)
    jit = 1 + 0.05 * (rng.random() - 0.5)
    belly = region == "belly" or (region in ("side", "end") and hf < 0.16)
    if belly:
        # broad ventral scutes, cream to salmon, with darker seams
        ph = (s / 2.3) % 1
        c = rig.mix(CREAM, (226, 160, 136), 0.5 + 0.5 * noise1(11, s, 6))
        if ph > 0.84:
            c = rig.shade(c, 0.78)
        elif ph < 0.2:
            c = rig.shade(c, 1.06)
        if region != "belly" and hf > 0.1:
            c = rig.mix(c, CRIMSON, 0.35)
        return rig.shade(c, jit)
    c = rig.mix(CRIMSON, (214, 34, 34), 0.5 + 0.5 * noise1(12, s, 4.0))
    # the saddles: one dark oval blotch across the back to each segment, wavy edged, ringed with a brighter crimson;
    # between them, lower on each flank, a smaller dark blotch, so the back reads crimson with dark saddles, not bands
    P = 9.6
    w2 = part.size[2] / 2
    # the distance round the body from the dorsal midline, in px (the sides continue down from the top's edge)
    dist = abs(d)
    ph = (sn - 3.0) / P
    i = math.floor(ph + 0.5)
    ds = (ph - i) * P
    if sn > 1.0 and region != "end":
        half = 2.1 + 0.5 * noise1(13, i, 1) + 0.35 * math.sin(dist * 1.1 + i)
        across = w2 + 2.2 + 1.2 * noise1(14, i, 1)        # how far round from the midline
        dsk = ds + 1.1 * noise1(16, i, 1) * d / across  # each saddle skewed a little, so they read as blotches
        e = (dsk / half) ** 2 + (dist / across) ** 2
        if e < 0.72:
            c = rig.mix(SADDLE, (84, 10, 18), 0.4 * rng.random())
        elif e < 1.0:
            c = rig.mix(CRIMSON_HI, (250, 96, 76), 0.3)
        if region == "side":
            dl = (ph - math.floor(ph) - 0.5) * P               # half a period on from the saddles
            e2 = (dl / (1.5 + 0.3 * noise1(15, i * 2 + (d > 0), 1))) ** 2 + ((hf - 0.4) / 0.17) ** 2
            if e2 < 0.7:
                c = rig.mix((80, 8, 16), SADDLE, 0.5 * rng.random())
            elif e2 < 1.0:
                c = rig.mix(c, CRIMSON_HI, 0.5)
    if region == "top":                                 # a sheen along the upper back
        c = rig.mix(c, (255, 150, 130), 0.16 * math.exp(-((d + part.size[2] * 0.12) / (part.size[2] * 0.25)) ** 2))
    if region == "side":
        c = rig.mix(c, CRIMSON_DK, 0.3 * (1 - hf))
    return rig.shade(c, sk * jit)


def adder_head(kind):
    """Skull, snout, jaw: big head plates outlined dark, a dark band back from the eye, salmon lips, pink mouth."""
    def paint(ctx):
        p = ctx.part
        px = ctx.img.load()
        f = ctx.face
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                fu, fv = (xx + 0.5) / ctx.w, (yy + 0.5) / ctx.h
                x = p.frm[0] + (fu if f in ("up", "south", "down") else 1 - fu) * p.size[0]
                u = (x - ADDER_HX0) / ADDER_HEAD            # 0 the snout tip, 1 the back of the head
                c = rig.mix(CRIMSON, (214, 34, 34), ctx.rng.random() * 0.35)
                if kind == "jaw":
                    if f == "up":           # the floor of the mouth, a pale row of teeth along each edge
                        c = rig.mix(PINK, (150, 50, 66), 0.5 * abs(fv - 0.5) * 2 < 0.6 and 0.6 or 0.2)
                        if fv < 0.1 or fv > 0.9:
                            c = (236, 226, 204) if int(fu * 22) % 2 == 0 else (200, 180, 160)
                        if 0.35 < fv < 0.65 and u > 0.45:
                            c = (110, 30, 44)
                    elif f in ("south", "north"):
                        if fv < 0.3:                          # the lower lip, salmon scales
                            c = rig.mix(CREAM, (226, 150, 128), 0.5)
                            if int(u * 12) % 2 == 0:
                                c = rig.shade(c, 0.86)
                        elif fv > 0.72:                       # the chin's edge, cream
                            c = rig.mix(CREAM, CRIMSON, 0.25)
                        else:
                            c = rig.mix(c, CRIMSON_DK, 0.25)
                    elif f == "down":
                        c = rig.mix(CREAM, (224, 170, 146), ctx.rng.random() * 0.4)
                        if (fu * 9) % 1 > 0.85:
                            c = rig.shade(c, 0.85)
                    elif f == "west":
                        c = rig.mix(CREAM, (220, 150, 130), fv)
                    else:
                        c = (120, 30, 44)
                elif f == "down":           # the roof of the mouth
                    c = rig.mix(PINK, (160, 60, 76), ctx.rng.random() * 0.4)
                    if kind == "skull" and 0.3 < fv < 0.7 and u > 0.75:
                        c = (90, 20, 36)                # the throat
                    if fv < 0.08 or fv > 0.92:
                        c = (236, 226, 204) if int(fu * 22) % 2 == 0 else (200, 180, 160)
                elif f == "up":
                    # big head plates: a grid of shields outlined dark
                    gx = (u * (6 if kind == "skull" else 3)) % 1
                    gy = (fv * (4 if kind == "skull" else 3)) % 1
                    if gx < 0.1 or gy < 0.1:
                        c = rig.shade(c, 0.72)
                    elif gx > 0.75 and gy > 0.6:
                        c = rig.mix(c, CRIMSON_HI, 0.5)
                    if kind == "skull" and abs(fv - 0.5) < 0.08 and u > 0.55:
                        c = rig.shade(c, 0.6)           # a dark line down the crown
                elif f in ("south", "north"):
                    if fv > 0.8:                         # upper lip scales, salmon
                        c = rig.mix(CREAM, (226, 150, 128), (fv - 0.8) * 4)
                        if int(u * 12) % 2 == 0:
                            c = rig.shade(c, 0.86)
                    elif kind == "skull" and 0.3 < fv < 0.64 and u > 0.42:
                        c = rig.mix(SADDLE, CRIMSON_DK, ctx.rng.random() * 0.5)   # the dark band back from the eye
                    elif kind == "skull" and fv < 0.28 and u > 0.75:
                        c = rig.mix(c, SADDLE, 0.4)
                elif f == "west":
                    c = rig.mix(CRIMSON, CREAM, smooth((fv - 0.55) * 3)) if kind == "snout" else c
                    if kind == "snout" and 0.22 < fv < 0.42 and (abs(fu - 0.24) < 0.07 or abs(fu - 0.76) < 0.07):
                        c = (30, 6, 10)                  # nostrils
                    if kind == "snout" and fv > 0.9:
                        c = (236, 226, 204) if int(fu * 10) % 2 == 0 else (170, 70, 80)
                put(ctx, px, xx, yy, rig.shade(c, FACEK[f] * (0.96 + 0.08 * ctx.rng.random())))
    return paint


def adder_brow(ctx):
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            c = rig.mix(CRIMSON_DK, CRIMSON, 0.5 + 0.5 * ctx.rng.random())
            if (xx * 3 // max(1, ctx.w)) != ((xx + 1) * 3 // max(1, ctx.w)):
                c = rig.shade(c, 0.6)               # the brow is three heavy scales
            if ctx.face == "up" and yy < ctx.h // 2:
                c = rig.mix(c, CRIMSON_HI, 0.4)
            put(ctx, px, xx, yy, rig.shade(c, FACEK[ctx.face]))


def adder_eye(ctx):
    """Amber-gold, darker at the rim, a vertical slit pupil on the outward face."""
    px = ctx.img.load()
    out = ctx.face == ("south" if ctx.part.name.endswith("L") else "north") or ctx.face == "west"
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            r = math.hypot((xx + 0.5) / ctx.w - 0.5, (yy + 0.5) / ctx.h - 0.5) * 2
            c = rig.mix((252, 206, 70), (196, 112, 16), min(1.0, r))
            if not out:
                c = rig.shade(c, 0.75)
            put(ctx, px, xx, yy, c)
    if ctx.face in ("south", "north"):
        cx = ctx.w // 2
        for yy in range(ctx.h):
            put(ctx, px, cx, yy, (10, 4, 2))
        put(ctx, px, ctx.w - 1 if ctx.face == "south" else 0, 0, (255, 248, 220))


def fang(ctx):
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, px, xx, yy, rig.mix((240, 232, 210), (200, 186, 160), yy / max(1, ctx.h - 1) * 0.6))


def black_tongue(ctx):
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, px, xx, yy, rig.shade((22, 18, 22), 0.8 + 0.5 * ctx.rng.random()))


def build_adder():
    m = Model(ADDER, atlas_width=128, seed=472)
    sp = Serpent(m, ADDER_HX0, ADDER_HEAD, ADDER_SEGS, ADDER_ROOT, ov=0.45)
    sp.build(skin_painter(adder_body))
    hx = ADDER_HX0
    a0 = hx + ADDER_HEAD
    head = m.part("Head", (hx + 4, 2.6, -5), (10, 5.4, 10), pivot=(a0, 4.0, 0), parent="Seg0", paint=adder_head("skull"))
    m.part("Snout", (hx, 2.7, -3.8), (4.2, 4.0, 7.6), pivot=(hx + 4, 4.2, 0), parent=head, paint=adder_head("snout"))
    m.part("BrowL", (hx + 3.3, 7.1, 2.5), (5.4, 1.5, 2.8), pivot=(hx + 6, 7.6, 3.9), parent=head, rest=(-8, 0, 0), paint=adder_brow)
    m.mirror("BrowL", "BrowR")
    m.part("EyeL", (hx + 4.4, 5.0, 4.6), (2.4, 1.9, 0.8), pivot=(hx + 5.6, 6.0, 5.0), parent=head, paint=adder_eye, glow=90)
    m.mirror("EyeL", "EyeR")
    jaw = m.part("Jaw", (hx + 0.4, 0.0, -4.4), (13.0, 2.65, 8.8), pivot=(hx + 13.2, 2.6, 0), parent=head, paint=adder_head("jaw"))
    m.part("FangL", (hx + 1.0, 1.0, 1.9), (0.8, 1.8, 0.8), pivot=(hx + 1.4, 2.8, 2.3), parent="Snout", rest=(0, 0, -8), paint=fang)
    m.mirror("FangL", "FangR")
    t = m.part("Tongue", (hx + 2.4, 2.7, -0.4), (6.0, 0.4, 0.8), pivot=(hx + 8.4, 2.9, 0), parent=head, paint=black_tongue)
    m.part("ForkL", (hx + 0.4, 2.72, 0.0), (2.2, 0.36, 0.4), pivot=(hx + 2.5, 2.9, 0.2), parent=t, rest=(0, -16, 0), paint=black_tongue)
    m.part("ForkR", (hx + 0.4, 2.72, -0.4), (2.2, 0.36, 0.4), pivot=(hx + 2.5, 2.9, -0.2), parent=t, rest=(0, 16, 0), paint=black_tongue)
    return m, sp, jaw


def adder_animations(m, sp):
    us = sp.centres()
    rest_psi = wave(us, 30, 1.0, 0.08, head_k=0.3, taper=lambda u: smooth((u - 0.12) / 0.3))
    sp.set_rest(sp.world(rest_psi))
    n = len(sp.chain)
    r = sp.root + 1

    def tongue(out, tilt=0.0):
        return {"Tongue": {"off": (-6.0 * out, 0, 0), "rot": (0, 0, tilt)},
                "ForkL": {"rot": (0, -12 * out, 0)}, "ForkR": {"rot": (0, 12 * out, 0)}}

    def jaw(a):
        return {"Jaw": {"rot": (0, 0, a)}}

    def gaped(elev, g):
        """A gape of g degrees: the skull tilts up 45% of it, the jaw drops the rest (the jaw is the skull's child)."""
        elev = list(elev)
        elev[0] += 0.45 * g
        return elev

    def floor_fit(make, lo=-1.0):
        """make(lift) -> keyframe, lift raising the forepart from its base (degrees); the least lift that keeps every
        drawn box above `lo` px."""
        if rig.posed_extent(m, make(0.0))[0] >= lo:
            return make(0.0)
        a, b = 0.0, 45.0
        for _ in range(14):
            c = (a + b) / 2
            if rig.posed_extent(m, make(c))[0] >= lo:
                b = c
            else:
                a = c
        return make(b)

    def flick(f, starts):
        for st in starts:
            q = f - st
            if 0 <= q <= 14:
                return [0, 0.5, 1.0, 0.8, 0.4, 0.9, 1.0, 0.6, 0.2, 0.7, 1.0, 0.5, 0.1, 0, 0][q]
        return 0.0

    def merge(*ds):
        out = {}
        for d in ds:
            out.update(d)
        return out

    def raised(t=1.0):
        """The idle's neck: raised a little, the head held level."""
        elev = [0.0] * n
        elev[r - 1] = 6 * t
        elev[r - 2] = 9 * t
        elev[r - 3] = 13 * t
        elev[r - 4] = 16 * t
        elev[r - 5] = 10 * t
        elev[0] = -4 * t
        return elev

    # ---- idle: 4 s; head raised a little, a slow sway of the forepart, the tongue tasting the air
    def idle(f):
        p = f / 120
        psi = [rest_psi[k] + (7 * math.sin(TAU * (p - 0.15 * k)) if k <= r else 2.5 * math.sin(TAU * (p - us[k]))) for k in range(n)]
        elev = raised()
        elev[0] += 3 * math.sin(TAU * 2 * p)
        return sp.pose(sp.world(psi, elev), tongue(flick(f, (30, 84)), tilt=4 * math.sin(f * 1.7)))

    m.animation("idle", 120, keyframes(idle, 120, 6, extra_frames=[s + q for s in (30, 84) for q in range(15)]))

    # ---- slither: 1.6 s; a travelling wave, the head held level and steady
    def slither(f):
        p = f / 48
        psi = wave(us, 30, 1.0, p, head_k=0.2, taper=lambda u: 0.55 + 0.45 * smooth((u - 0.1) / 0.3))
        return sp.pose(sp.world(psi, raised(0.6)))

    m.animation("slither", 48, keyframes(slither, 48, 3))

    # ---- rear: the front quarter lifted 2-3 blocks in an S, the head looking down; held
    def rear_pose(t, tf=0.0):
        psi = list(rest_psi)
        elev = [0.0] * n
        tgt = {r - 1: 30, r - 2: 66, r - 3: 88, r - 4: 62, r - 5: 22, 0: -38}
        yaw = {r - 1: 10, r - 2: 4, r - 3: -6, r - 4: -10, r - 5: -4, 0: 0}
        for k, e in tgt.items():
            elev[k] = e * t
            psi[k] = rest_psi[k] * (1 - min(1, t)) + yaw[k] * t
        return sp.pose(sp.world(psi, elev), merge(tongue(tf), jaw(6 * t)))

    m.animation("rear", 30, {0: rear_pose(0), 8: rear_pose(0.45), 16: rear_pose(0.9), 21: rear_pose(1.04), 25: rear_pose(0.99, 1.0),
                             27: rear_pose(1.0, 0.3), 29: rear_pose(1.0)}, end="Hold")

    # ---- strike: 0.8 s; drawn back, a lunge forward and down with the jaw gaping, the bite, a recoil
    def strike_pose(back, lunge, gape, slide):
        return floor_fit(lambda lift: _strike(back, lunge, gape, slide, lift))

    def _strike(back, lunge, gape, slide, lift):
        psi = list(rest_psi)
        for k in range(1, r):
            psi[k] = rest_psi[k] * (1 - max(back, lunge))
        psi[0] = 0
        elev = raised(1 - max(back, lunge))
        coil = {r - 1: 24, r - 2: 52, r - 3: 70, r - 4: 30, r - 5: -10, 0: -6}
        hit = {r - 1: 16, r - 2: 10, r - 3: 4, r - 4: -2, r - 5: -8, 0: -14}
        for k in range(n):
            elev[k] += coil.get(k, 0) * back + hit.get(k, 0) * lunge
        elev[r - 1] += lift
        elev[r - 2] += lift * 0.3
        root = sp.names[sp.root]
        return sp.pose(sp.world(psi, gaped(elev, gape)), merge(jaw(gape), {root: {"off": (-slide, 0, 0)}}))

    m.animation("strike", 24, {0: strike_pose(0, 0, 0, 0), 5: strike_pose(1, 0, 18, 0), 9: strike_pose(0.2, 0.9, 58, 7),
                               11: strike_pose(0, 1.0, 62, 11), 13: strike_pose(0, 1.0, 8, 11), 16: strike_pose(0, 0.85, 4, 9),
                               23: strike_pose(0, 0, 0, 0)}, end="Stop")

    # ---- devour: 1.5 s; the jaw wide, the head pressing down and forward, the jaws walking over the prey in gulps
    def devour_pose(t, gape, walk, gulp, slide):
        return floor_fit(lambda lift: _devour(t, gape, walk, gulp, slide, lift))

    def _devour(t, gape, walk, gulp, slide, lift):
        psi = list(rest_psi)
        for k in range(1, r):
            psi[k] = rest_psi[k] * (1 - t)
        psi[0] = walk * 9
        psi[1] = -walk * 4
        elev = [0.0] * n
        elev[r - 3] = 6 * t
        elev[r - 4] = 4 * t + 5 * gulp
        elev[r - 5] = -8 * t - 5 * gulp
        # the jaw laid flat over the prey on the ground, the skull tilted up over it by the gape
        elev[0] = (gape - 4) * t + 6 * gulp
        elev[r - 1] += lift
        elev[r - 2] += lift * 0.3
        root = sp.names[sp.root]
        return sp.pose(sp.world(psi, elev), merge(jaw(gape), {root: {"off": (-slide, 0, 0)}}))

    m.animation("devour", 45, {0: devour_pose(0, 0, 0, 0, 0), 5: devour_pose(0.6, 50, 0, 0, 2), 9: devour_pose(1, 72, 0, 0, 5),
                               14: devour_pose(1, 46, 1, 1, 6), 19: devour_pose(1, 70, 0, 0, 6.5), 24: devour_pose(1, 44, -1, 1, 7.5),
                               29: devour_pose(1, 68, 0, 0, 8), 34: devour_pose(1, 40, 1, 1, 8.5), 39: devour_pose(0.6, 20, 0, 0.5, 6),
                               44: devour_pose(0, 0, 0, 0, 0)}, end="Stop")

    # ---- hurt: a recoil, the jaw opening in a hiss
    def hurt_pose(t):
        psi = [rest_psi[k] + t * 14 * math.sin(TAU * us[k] * 1.5) for k in range(n)]
        elev = raised(1)
        elev[0] += 20 * t
        elev[1] += 10 * t
        return sp.pose(sp.world(psi, gaped(elev, max(0.0, 26 * t))), jaw(max(0.0, 26 * t)))

    m.animation("hurt", 12, {0: hurt_pose(0), 3: hurt_pose(1), 6: hurt_pose(-0.4), 9: hurt_pose(0.2), 11: hurt_pose(0)}, end="Stop")

    # ---- die: a slow writhe, then limp: the forepart rolled onto its side, the middle belly-up, the jaw slack; held
    def die_pose(writhe, t, gape):
        psi = [rest_psi[k] * (1 - 0.4 * t) + writhe * math.sin(TAU * (us[k] * 1.2 + 0.1)) for k in range(n)]
        elev = raised(1 - t)
        roll = [0.0] * n
        prof = [70, 80, 100, 120, 140, 150, 155, 150, 130, 100, 70, 45, 25, 10, 0, 0]
        for k in range(n):
            roll[k] = prof[k] * t
        return floor_fit(lambda lift: sp.pose(sp.world(psi, [e + (lift if k == r - 1 else 0) for k, e in enumerate(elev)], roll),
                                             jaw(gape)), lo=-1.0)

    m.animation("die", 40, {0: die_pose(0, 0, 0), 6: die_pose(16, 0, 30), 13: die_pose(-14, 0.1, 40), 21: die_pose(8, 0.5, 30),
                            30: die_pose(-2, 0.9, 22), 39: die_pose(0, 1.0, 20)}, end="Hold")


def gen_adder():
    m, sp, _ = build_adder()
    adder_animations(m, sp)
    old = rig.TEXEL
    rig.TEXEL = ADDER_TEXEL
    try:
        m.save()
    finally:
        rig.TEXEL = old
    lo, hi = rig.posed_extent(m, {})
    print(f"  great adder length {sp.total:.1f} px = {sp.total / 16:.2f} blocks along the body, rest height {hi:.1f} px")
    mats = rig.posed_matrices(m, {})
    xs, zs = [], []
    for p in m.parts:
        if not p.faces:
            continue
        c = np.array([[x * p.size[0], y * p.size[1], z * p.size[2], 1] for x in (0, 1) for y in (0, 1) for z in (0, 1)])
        w = (mats[id(p)] @ c.T)
        xs.extend(w[0])
        zs.extend(w[2])
    print(f"  laid out: x {min(xs):.0f}..{max(xs):.0f} px, z {min(zs):.0f}..{max(zs):.0f} px")
    for code, frames, keys, end, _ in m.animations:
        ext = [rig.posed_extent(m, k) for k in keys.values()]
        print(f"  {code}: lowest {min(e[0] for e in ext):.1f} px, highest {max(e[1] for e in ext):.1f} px")


# ================================================================ the Ophion Occult Order

OPHION = "47/l47-ophion"
OPHION_TEXEL = 4
IVORY = (242, 236, 220)
IVORY_DK = (178, 160, 128)
GOLD = (196, 154, 58)
GOLD_HI = (244, 212, 120)
GOLD_LO = (112, 80, 26)
SHADOW = (16, 7, 10)


class OphionLook:
    def __init__(self, key):
        self.key = key
        self.elder = key == "elder"
        self.robe = (100, 9, 22) if self.elder else (148, 20, 30)
        self.robe_hi = (138, 22, 36) if self.elder else (184, 38, 44)
        self.robe_lo = (56, 4, 12) if self.elder else (92, 10, 18)


# faces that look into the hood or a sleeve (painted as deep shadow)
INNER = {("HoodL", "north"), ("HoodR", "south"), ("HoodTop", "down"), ("HoodPeak", "down"), ("HoodBack", "west"), ("HoodPeak", "east"),
         ("CuffL", "down"), ("CuffR", "down"), ("HoodTip", "west")}


def gold_band(ctx, px, yy0, yy1, rng):
    """A band of gold embroidery between two texel rows: lit above, a stitched crimson serpent running along it."""
    for yy in range(max(0, yy0), min(ctx.h, yy1)):
        for xx in range(ctx.w):
            t = (yy - yy0) / max(1, yy1 - yy0 - 1)
            c = rig.mix(GOLD_HI, GOLD, t)
            if yy == yy1 - 1:
                c = GOLD_LO
            mid = yy0 + (yy1 - yy0 - 1) / 2
            if yy1 - yy0 >= 4 and abs((yy - mid) - 1.2 * tri(xx / 6.0)) < 0.6:
                c = (70, 8, 18)
            put(ctx, px, xx, yy, rig.shade(c, 0.92 + 0.12 * rng.random()))


def robe_painter(look, trim=None):
    """Crimson cloth: a fine twill, folds down the skirt, shading down each side; trims by `trim`: 'hem' (the skirt's
    foot), 'cuff', 'hood' (its front edge), 'mantle' (its lower edge), 'front' (the elder's embroidered front panel)."""
    def paint(ctx):
        p = ctx.part
        f = ctx.face
        px = ctx.img.load()
        if (p.name, f) in INNER:
            for yy in range(ctx.h):
                for xx in range(ctx.w):
                    put(ctx, px, xx, yy, rig.shade(SHADOW, 0.8 + 0.4 * ctx.rng.random()))
            return
        rig.lit_fill(ctx, look.robe, 0.05)
        rig.weave(ctx, 4.0, "twill")
        side = f in ("north", "south", "east", "west")
        if side and p.name.startswith("Skirt"):
            n = max(2, ctx.w // 7)
            for i in range(n):
                x0 = int((i + 0.5 + 0.3 * (ctx.rng.random() - 0.5)) * ctx.w / n)
                for yy in range(ctx.h):
                    xx = x0 + int(round(0.8 * math.sin(yy * 0.15 + i)))
                    put(ctx, px, xx, yy, rig.mix(look.robe_lo, look.robe, 0.3))
                    put(ctx, px, xx + 1, yy, rig.mix(look.robe_hi, look.robe, 0.4))
        if side:
            for yy in range(ctx.h):
                k = 1.06 - 0.16 * yy / max(1, ctx.h - 1)
                for xx in range(ctx.w):
                    put(ctx, px, xx, yy, rig.shade(px[ctx.x + xx, ctx.y + yy][:3], k))
        if trim in ("hem", "cuff", "mantle") and side:
            if look.elder:
                n = {"hem": 6, "cuff": 5, "mantle": 4}[trim]
                gold_band(ctx, px, ctx.h - n, ctx.h, ctx.rng)
            else:
                for xx in range(ctx.w):
                    put(ctx, px, xx, ctx.h - 1, rig.shade(look.robe_lo, 0.8))
        if trim == "hood" and f == "west":
            for yy in range(ctx.h):
                for xx in range(ctx.w):
                    c = rig.mix(GOLD, GOLD_HI, 0.5 * ctx.rng.random()) if look.elder else rig.mix(look.robe_hi, look.robe, 0.5)
                    put(ctx, px, xx, yy, c)
        if trim == "front" and f == "west" and look.elder:
            c0, c1 = int(ctx.w * 0.38), int(math.ceil(ctx.w * 0.62))
            for yy in range(ctx.h):
                for xx in range(c0, c1):
                    edge = xx in (c0, c1 - 1)
                    c = GOLD_LO if edge else rig.mix(GOLD, GOLD_HI, 0.4 * ctx.rng.random())
                    if not edge and (yy + xx) % 4 == 0:
                        c = (88, 8, 20)
                    put(ctx, px, xx, yy, c)
    return paint


def mask_paint(ctx):
    """The ivory mask: smooth bone-white, eye slits, a faint carved serpent coiling round the brow."""
    px = ctx.img.load()
    f = ctx.face
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            u, v = (xx + 0.5) / ctx.w, (yy + 0.5) / ctx.h
            k = FACEK[f] * (0.97 + 0.05 * ctx.rng.random())
            if f == "west":
                k *= 1.0 - 0.10 * ((u - 0.5) * 2) ** 2 - 0.12 * max(0.0, v - 0.7) * 3
                if 0.36 < v < 0.72 and abs(u - 0.5) < 0.06:
                    k *= 1.05                    # the ridge of the nose
                if 0.6 < v < 0.72 and 0.12 < abs(u - 0.5) < 0.3:
                    k *= 0.93                    # cheek hollows
            put(ctx, px, xx, yy, rig.shade(IVORY, k))
    if f == "west":
        w, h = ctx.w, ctx.h

        def brow(u):
            return int(round(h * (0.2 + 0.055 * math.sin(TAU * (u * 1.5 + 0.1)))))
        # the serpent: a carved line round the brow, lit above and shadowed below, its head over the left eye
        for xx in range(w):
            y = brow((xx + 0.5) / w)
            put(ctx, px, xx, y, IVORY_DK)
            put(ctx, px, xx, y + 1, rig.shade(IVORY_DK, 0.88))
            put(ctx, px, xx, y - 1, rig.shade(IVORY, 1.06))
        hx, hy = int(w * 0.8), brow(0.8)
        for dx, dy in ((0, -1), (1, -1), (1, 0), (2, 0), (1, 1), (0, 1)):
            put(ctx, px, hx + dx, hy + dy, IVORY_DK)
        put(ctx, px, hx + 1, hy, (120, 30, 30))
        # eye slits
        for side in (-1, 1):
            for i in range(int(w * 0.2)):
                xx = int(w * (0.5 + side * 0.13)) + side * i
                yy = int(h * 0.44)
                put(ctx, px, xx, yy, (12, 6, 8))
                put(ctx, px, xx, yy + 1, (28, 14, 16))
                put(ctx, px, xx, yy - 1, rig.shade(IVORY_DK, 0.95))
        for xx in range(int(w * 0.42), int(w * 0.58) + 1):
            put(ctx, px, xx, int(h * 0.82), rig.shade(IVORY_DK, 0.9))   # a thin closed mouth
    elif f in ("south", "north"):
        for xx in range(ctx.w):
            put(ctx, px, xx, int(ctx.h * 0.21), IVORY_DK)                 # the coil carries on round the sides


def hand_paint(ctx):
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            c = rig.mix((224, 210, 198), (200, 182, 172), ctx.rng.random() * 0.4)
            put(ctx, px, xx, yy, rig.shade(c, FACEK[ctx.face]))
    if ctx.face in ("west", "east", "south", "north"):
        for i in (1, 2):
            xx = int(ctx.w * i / 3)
            for yy in range(int(ctx.h * 0.55), ctx.h):
                put(ctx, px, xx, yy, (190, 170, 160))   # fingers
        for xx in range(ctx.w):
            put(ctx, px, xx, 0, (150, 128, 120))        # the sleeve's shadow


def clasp_paint(ctx):
    """The Order's sign: a gold snake eating its tail."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, px, xx, yy, rig.shade(rig.mix(GOLD, GOLD_LO, 0.3 * ctx.rng.random()), FACEK[ctx.face]))
    if ctx.face != "west":
        return
    w, h = ctx.w, ctx.h
    cx, cy = (w - 1) / 2, (h - 1) / 2
    for yy in range(h):
        for xx in range(w):
            r = math.hypot(xx - cx, yy - cy) / (w / 2)
            if r < 0.42:
                c = (60, 6, 14)
            elif r < 0.85:
                c = rig.mix(GOLD_HI, GOLD, (r - 0.42) / 0.43)
                if (math.atan2(yy - cy, xx - cx) * 6) % 2 < 0.4:
                    c = rig.shade(c, 0.8)
            else:
                c = GOLD_LO
            put(ctx, px, xx, yy, c)
    put(ctx, px, int(cx) + 1, 0, GOLD_HI)               # the head biting the tail
    put(ctx, px, int(cx) + 2, 1, GOLD_HI)
    put(ctx, px, int(cx) + 1, 1, (20, 10, 4))


def cord_paint(look):
    def paint(ctx):
        px = ctx.img.load()
        a, b = (GOLD, GOLD_LO) if look.elder else ((150, 116, 70), (82, 60, 36))
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                c = a if (xx + yy) % 4 < 2 else b
                put(ctx, px, xx, yy, rig.shade(c, FACEK[ctx.face] * (0.92 + 0.12 * ctx.rng.random())))
    return paint


def build_ophion(look):
    m = Model(OPHION, atlas_width=48, seed=473)
    robe = robe_painter(look)
    front = robe_painter(look, "front")
    pelvis = m.part("Pelvis", (-2.2, 13, -3.6), (4.4, 3, 7.2), pivot=(0, 14.5, 0), paint=robe)
    up = m.part("SkirtUpper", (-2.9, 8.4, -4.3), (5.8, 5.4, 8.6), pivot=(0, 13.6, 0), parent=pelvis, paint=front)
    mid = m.part("SkirtMid", (-3.6, 3.8, -4.9), (7.2, 4.8, 9.8), pivot=(0, 8.6, 0), parent=up, paint=front)
    m.part("SkirtHem", (-4.3, 0.15, -5.5), (8.6, 3.8, 11.0), pivot=(0, 3.9, 0), parent=mid, paint=robe_painter(look, "hem"))
    thigh = m.part("ThighL", (-1.1, 7.2, 0.5), (2.2, 6.6, 2.2), pivot=(0, 13.6, 1.6), parent=pelvis, paint=robe)
    shin = m.part("ShinL", (-1.0, 1.1, 0.6), (2.0, 6.3, 2.0), pivot=(0, 7.4, 1.6), parent=thigh, paint=robe)
    m.part("FootL", (-4.9, 0, 0.45), (4.6, 1.25, 2.3), pivot=(0, 1.2, 1.6), parent=shin, paint=plain((40, 30, 26)))
    m.mirror("ThighL", "ThighR")
    waist = m.part("Waist", (-2.4, 15.8, -3.5), (4.8, 4.4, 7.0), pivot=(0, 16, 0), parent=pelvis, paint=front)
    belt = m.part("Belt", (-2.7, 15.4, -3.8), (5.4, 1.1, 7.6), pivot=(0, 16, 0), parent=waist, paint=cord_paint(look))
    m.part("Knot", (-3.3, 14.8, -0.7), (0.7, 1.3, 1.4), pivot=(-3, 15.4, 0), parent=belt, paint=cord_paint(look))
    m.part("CordL", (-3.35, 10.6, 0.1), (0.5, 4.4, 0.5), pivot=(-3.1, 15, 0.35), parent=belt, paint=cord_paint(look))
    m.part("CordR", (-3.35, 11.6, -0.75), (0.5, 3.4, 0.5), pivot=(-3.1, 15, -0.5), parent=belt, paint=cord_paint(look))
    chest = m.part("Chest", (-2.6, 19.8, -3.8), (5.2, 4.8, 7.6), pivot=(0, 20, 0), parent=waist, paint=front)
    mantle = m.part("Mantle", (-3.1, 22.4, -4.4), (6.2, 2.8, 8.8), pivot=(0, 23, 0), parent=chest, paint=robe_painter(look, "mantle"))
    m.part("Clasp", (-3.55, 22.8, -1.0), (0.5, 2.0, 2.0), pivot=(-3.3, 23.8, 0), parent=mantle, paint=clasp_paint)
    head = m.part("Head", (-1.6, 25.0, -2.3), (3.8, 4.4, 4.6), pivot=(0, 25.2, 0), parent=chest, paint=plain(SHADOW))
    m.part("Mask", (-2.2, 25.2, -1.85), (0.7, 4.1, 3.7), pivot=(-1.9, 27, 0), parent=head, paint=mask_paint)
    m.part("HoodTop", (-2.9, 29.4, -3.1), (6.0, 1.1, 6.2), pivot=(0, 29.9, 0), parent=head, paint=robe)
    m.part("HoodCrown", (-2.0, 30.3, -2.4), (4.6, 1.0, 4.8), pivot=(0, 30.8, 0), parent=head, paint=robe)
    m.part("HoodL", (-2.9, 24.4, 2.3), (6.0, 5.1, 0.85), pivot=(0, 27, 2.7), parent=head, paint=robe_painter(look, "hood"))
    m.mirror("HoodL", "HoodR")
    m.part("HoodBack", (2.2, 24.2, -3.1), (1.0, 5.3, 6.2), pivot=(2.7, 27, 0), parent=head, paint=robe)
    m.part("HoodPeak", (-3.7, 28.9, -2.4), (1.4, 1.1, 4.8), pivot=(-3.0, 29.4, 0), parent=head, rest=(0, 0, 8), paint=robe_painter(look, "hood"))
    m.part("HoodTip", (2.9, 25.4, -1.4), (1.5, 3.6, 2.8), pivot=(3.2, 28.8, 0), parent=head, rest=(0, 0, 14), paint=robe)
    arm = m.part("ArmL", (-1.3, 18.2, 3.8), (2.6, 5.6, 2.5), pivot=(0, 23.2, 5.0), parent=chest, paint=robe)
    fore = m.part("ForearmL", (-1.5, 13.0, 3.6), (3.0, 5.4, 2.9), pivot=(0, 18.4, 5.0), parent=arm, paint=robe)
    m.part("CuffL", (-2.1, 11.6, 3.1), (4.2, 2.8, 3.9), pivot=(0, 13.2, 5.0), parent=fore, paint=robe_painter(look, "cuff"))
    m.part("HandL", (-1.0, 9.8, 4.25), (2.0, 2.8, 1.5), pivot=(0, 12.6, 5.0), parent=fore, paint=hand_paint)
    m.mirror("ArmL", "ArmR")
    return m


def full_keys(keys):
    """Every key given every part any key names (unnamed ones at rest), so the animation never leaves a part behind."""
    names = sorted({n for k in keys.values() for n in k})
    return {f: {n: dict(k.get(n, pose())) for n in names} for f, k in keys.items()}


def ophion_animations(m):
    def s(p, amp, shift=0.0):
        return amp * math.sin(TAU * (p + shift))

    def merge(*ds):
        out = {}
        for d in ds:
            out.update(d)
        return out

    def clasped(k=1.0):
        """Hands folded together before the belly, in the sleeves."""
        return {"ArmL": pose((8 * k, 0, -16 * k)), "ArmR": pose((-8 * k, 0, -16 * k)),
                "ForearmL": pose((0, -34 * k, -62 * k)), "ForearmR": pose((0, 34 * k, -62 * k))}

    # ---- idle: 4 s, hands folded, breathing, the hood turning a little
    def idle(p):
        br = 0.5 - 0.5 * math.cos(TAU * 2 * p)
        return merge(clasped(), {
            "Chest": pose((0, 0, 1.0 * br), s=(1, 1 + 0.01 * br, 1 + 0.015 * br)),
            "Head": pose((s(p, 2, 0.2), s(p, 10), 2 + s(p, 2, 0.4))),
            "SkirtHem": pose((s(p, 0.8), 0, 0)),
        })

    m.animation("idle", 120, {f: idle(f / 120) for f in range(0, 120, 10)})

    # ---- walk: 1.33 s, a measured gliding step; the robe swings after the legs
    def walk(p):
        a = s(p, 20)
        bend = 26 * max(0.0, -math.cos(TAU * p))
        bend2 = 26 * max(0.0, math.cos(TAU * p))
        return {
            "Pelvis": pose((0, s(p, 3), 0), (0, -0.4 * abs(math.cos(TAU * p)), 0)),
            "ThighL": pose((0, 0, -a)), "ThighR": pose((0, 0, a)), "ShinL": pose((0, 0, bend)), "ShinR": pose((0, 0, bend2)),
            "FootL": pose((0, 0, a * 0.5 - bend * 0.5)), "FootR": pose((0, 0, -a * 0.5 - bend2 * 0.5)),
            "SkirtUpper": pose((s(p, 1.5, 0.25), 0, s(p, 2.5, 0.1))), "SkirtMid": pose((0, 0, s(p, 3.5, 0.2))),
            "SkirtHem": pose((s(p, 2, 0.3), s(p, 3, 0.3), s(p, 4.5, 0.3))),
            "Waist": pose((0, -s(p, 2), 0)), "Chest": pose((0, -s(p, 3), 2)), "Head": pose((0, s(p, 3), 1)),
            "ArmL": pose((0, 0, s(p, 14))), "ArmR": pose((0, 0, -s(p, 14))),
            "ForearmL": pose((0, 0, -8 - 6 * max(0, math.sin(TAU * p)))), "ForearmR": pose((0, 0, -8 - 6 * max(0, -math.sin(TAU * p)))),
            "CordL": pose((0, 0, s(p, 8, 0.3))), "CordR": pose((0, 0, s(p, 8, 0.35))),
        }

    m.animation("walk", 40, {int(40 * i / 10): walk(i / 10) for i in range(10)})

    # ---- run: 0.8 s, bent forward, the robe flaring back, sleeves pumping
    def run(p):
        a = s(p, 38)
        b1 = 50 * max(0.0, -math.cos(TAU * p))
        b2 = 50 * max(0.0, math.cos(TAU * p))
        return {
            "Pelvis": pose((0, s(p, 4), 8), (0, -1.0 + 0.8 * abs(math.sin(TAU * p)), 0)),
            "ThighL": pose((0, 0, -a - 8)), "ThighR": pose((0, 0, a - 8)), "ShinL": pose((0, 0, b1)), "ShinR": pose((0, 0, b2)),
            "FootL": pose((0, 0, 10)), "FootR": pose((0, 0, 10)),
            "SkirtUpper": pose((0, 0, -6 + s(p, 3))), "SkirtMid": pose((0, 0, 8 + s(p, 5, 0.15))),
            "SkirtHem": pose((s(p, 3, 0.3), s(p, 4, 0.3), 12 + s(p, 6, 0.3))),
            "Waist": pose((0, -s(p, 4), 4)), "Chest": pose((0, -s(p, 6), 8)), "Head": pose((0, s(p, 3), -10)),
            "ArmL": pose((0, 0, s(p, 34))), "ArmR": pose((0, 0, -s(p, 34))),
            "ForearmL": pose((0, 0, -55)), "ForearmR": pose((0, 0, -55)),
            "HoodTip": pose((0, 0, 20)), "CordL": pose((0, 0, 25)), "CordR": pose((0, 0, 25)),
        }

    m.animation("run", 24, {int(24 * i / 8): run(i / 8) for i in range(8)})

    # ---- attack: 0.8 s, a two-handed shove: drawn back, both hands thrust out, a step in
    draw = {"Chest": pose((0, 0, -8)), "Waist": pose((0, 0, -3)), "Head": pose((0, 0, -4)),
            "ArmL": pose((-6, 0, 30)), "ArmR": pose((6, 0, 30)), "ForearmL": pose((0, -10, -105)), "ForearmR": pose((0, 10, -105)),
            "HandL": pose((0, 0, 20)), "HandR": pose((0, 0, 20)), "ThighL": pose((0, 0, 8)), "ThighR": pose((0, 0, -6))}
    thrust = {"Pelvis": pose((0, 0, 4), (-1.6, -0.4, 0)), "Chest": pose((0, 0, 16)), "Waist": pose((0, 0, 6)), "Head": pose((0, 0, -10)),
              "ArmL": pose((10, 0, -84)), "ArmR": pose((-10, 0, -84)), "ForearmL": pose((0, 0, -6)), "ForearmR": pose((0, 0, -6)),
              "HandL": pose((0, 0, -60)), "HandR": pose((0, 0, -60)),
              "ThighL": pose((0, 0, -26)), "ThighR": pose((0, 0, 18)), "ShinL": pose((0, 0, 10)), "ShinR": pose((0, 0, 12)),
              "SkirtHem": pose((0, 0, 8)), "SkirtMid": pose((0, 0, 4)), "HoodTip": pose((0, 0, 14))}
    m.animation("attack", 24, full_keys({0: {}, 7: draw, 11: thrust, 15: thrust, 23: {}}), end="Stop")

    # ---- preach: arms raised outward, the masked face lifted; a loop that holds as long as the sermon lasts
    def preach(p):
        return {
            "ArmL": pose((-118 + s(p, 6), 0, -14 + s(p, 4, 0.2))), "ArmR": pose((118 - s(p, 6, 0.1), 0, -14 + s(p, 4, 0.3))),
            "ForearmL": pose((-14, 0, -6 + s(p, 6, 0.25))), "ForearmR": pose((14, 0, -6 + s(p, 6, 0.35))),
            "HandL": pose((-10, 0, 0)), "HandR": pose((10, 0, 0)),
            "Chest": pose((s(p, 2), s(p, 4, 0.1), -5)), "Waist": pose((0, 0, -2)), "Head": pose((s(p, 3, 0.3), s(p, 8, 0.15), -14)),
            "SkirtHem": pose((s(p, 1.2), 0, 0)),
        }

    m.animation("preach", 60, {f: preach(f / 60) for f in range(0, 60, 6)})

    # ---- beckon: 1.2 s, the right hand reaching out and curling in twice
    reach = {"ArmR": pose((-6, 8, -72)), "ForearmR": pose((0, 0, -16)), "HandR": pose((0, 0, 0)), "Chest": pose((0, 12, 4)), "Head": pose((0, -10, 4))}
    curl = dict(reach, HandR=pose((0, 0, -75)), ForearmR=pose((0, 0, -34)))
    m.animation("beckon", 36, full_keys({0: {}, 8: reach, 13: curl, 17: reach, 22: curl, 26: reach, 35: {}}), end="Stop")

    # ---- bow: 1.5 s, hands folded, a slow deep bow
    bowd = merge(clasped(), {"Waist": pose((0, 0, 16)), "Chest": pose((0, 0, 22)), "Head": pose((0, 0, 24)), "Pelvis": pose((0, 0, 4)),
                             "SkirtUpper": pose((0, 0, -4)), "SkirtHem": pose((0, 0, -2)), "HoodTip": pose((0, 0, -10))})
    lead = merge(clasped(), {"Head": pose((0, 0, 10))})
    m.animation("bow", 45, full_keys({0: {}, 8: lead, 18: bowd, 30: bowd, 44: {}}), end="Stop")

    # ---- hurt: a short flinch back
    hurt = {"Chest": pose((0, -6, -12)), "Head": pose((0, 6, -12)), "Waist": pose((0, 0, -4)), "Pelvis": pose((0, 0, 0), (0.8, 0, 0)),
            "ArmL": pose((-20, 0, -10)), "ArmR": pose((20, 0, -10)), "ForearmL": pose((0, 0, -30)), "ForearmR": pose((0, 0, -30))}
    m.animation("hurt", 9, full_keys({0: {}, 3: hurt, 8: {}}), end="Stop")

    # ---- die: 1.3 s, a flinch, to the knees, and over onto the face, the robe spread on the ground; held
    kneel = {"Pelvis": pose((0, 0, 6), (0, -5.5, 0)), "ThighL": pose((0, 0, -70)), "ThighR": pose((0, 0, -62)),
             "ShinL": pose((0, 0, 100)), "ShinR": pose((0, 0, 92)), "FootL": pose((0, 0, -20)), "FootR": pose((0, 0, -20)),
             "SkirtUpper": pose((0, 0, -30)), "SkirtMid": pose((0, 0, -20)), "SkirtHem": pose((0, 0, -10)),
             "Waist": pose((0, 0, 8)), "Chest": pose((0, 0, 10)), "Head": pose((0, 0, 16)),
             "ArmL": pose((-6, 0, 4)), "ArmR": pose((6, 0, 4)), "ForearmL": pose((0, 0, -10)), "ForearmR": pose((0, 0, -10))}
    topple = dict(kneel, Pelvis=pose((0, 0, 48), (-2, -4, 0)), Chest=pose((0, 0, 14)), Head=pose((0, 0, 0)),
                  ArmL=pose((-10, 0, -50)), ArmR=pose((10, 0, -40)), SkirtUpper=pose((0, 0, -10)), SkirtMid=pose((0, 0, -8)))
    prone = {"Pelvis": pose((0, 0, 90)), "ThighL": pose((-4, 0, -8)), "ThighR": pose((4, 0, -4)), "ShinL": pose((0, 0, 10)), "ShinR": pose((0, 0, 6)),
             "FootL": pose((0, 0, 40)), "FootR": pose((0, 0, 36)), "SkirtUpper": pose((0, 0, -4)), "SkirtMid": pose((0, 0, -3)), "SkirtHem": pose((0, 0, -2)),
             "Waist": pose((0, 0, 2)), "Chest": pose((0, 0, 2)), "Head": pose((14, 30, -10)),
             "ArmL": pose((-16, 0, -150)), "ArmR": pose((24, 0, -20)), "ForearmL": pose((0, 0, -10)), "ForearmR": pose((0, 0, -16))}
    keys = full_keys({0: {}, 5: hurt, 14: kneel, 26: topple, 39: prone})
    for k in (14, 26, 39):
        rig.settle(m, keys[k], floor=-0.2)
    m.animation("die", 40, keys, end="Hold")


def gen_ophion():
    m = build_ophion(OphionLook("plain"))
    ophion_animations(m)

    def other(key):
        return build_ophion(OphionLook(key))

    save_variants(m, other, ["elder"], OPHION, OPHION_TEXEL)
    lo, hi = rig.posed_extent(m, {})
    print(f"  ophion height {hi:.1f} px = {hi / 16:.2f} blocks")
    for code, frames, keys, end, _ in m.animations:
        ext = [rig.posed_extent(m, k) for k in keys.values()]
        print(f"  {code}: lowest {min(e[0] for e in ext):.1f} px")


# ================================================================ the Black Shuck (vanilla wolf shape, new textures)

SHUCK = "47/l47-shuck"
VS_ASSETS = "G:/Games/Vintagestory/assets/survival"
WOLF_SHAPE = VS_ASSETS + "/shapes/entity/animal/mammal/wolf/eurasian-adult.json"
WOLF_TEX = VS_ASSETS + "/textures/entity/animal/mammal/wolf/eurasian-adult{}.png"


def wolf_regions():
    """Texel rectangles (in the 144 px texture) of the wolf's faces by kind: eye, pupil, teeth, mouth, sleep line."""
    d = json.loads(open(WOLF_SHAPE, encoding="utf-8-sig").read())
    sc = 2
    out = {"eye": [], "pupil": [], "teeth": [], "mouth": [], "sleep": []}

    def walk(els):
        for e in els:
            n = e["name"]
            kind = ("pupil" if "Pupil" in n else "eye" if "Eye" in n else "teeth" if ("Teeth" in n or "Fang" in n)
                    else "mouth" if "Mouth" in n else "sleep" if "sleep" in n else None)
            if kind:
                for fc in (e.get("faces") or {}).values():
                    if "uv" in fc:
                        u1, v1, u2, v2 = fc["uv"]
                        out[kind].append((int(min(u1, u2) * sc), int(min(v1, v2) * sc),
                                          int(math.ceil(max(u1, u2) * sc)), int(math.ceil(max(v1, v2) * sc))))
            walk(e.get("children") or [])

    walk(d["elements"])
    return out


def shuck_texture(src_n, dark, light, seed):
    """A vanilla wolf texture repainted: its light and shade kept as the fur's structure but squeezed into coal black
    with a faint charcoal, shaggy strokes over it, the eyes pale sickly yellow-white, teeth and mouth as vanilla's."""
    src = np.asarray(Image.open(WOLF_TEX.format(src_n)).convert("RGBA")).astype(np.float64)
    rgb, alpha = src[..., :3], src[..., 3]
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    lo, hi = np.percentile(lum[alpha > 0], 4), np.percentile(lum[alpha > 0], 96)
    t = np.clip((lum - lo) / max(1.0, hi - lo), 0, 1) ** 1.3
    t = 0.12 + 0.55 * t
    rng = np.random.default_rng(seed)
    t = t + rng.normal(0, 0.05, t.shape)
    h, w = t.shape
    for _ in range(int(h * w * 0.08)):            # shaggy: short strokes, dark at the root, lighter at the tip
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        ln = int(rng.integers(2, 5))
        dk = -0.16 if rng.random() < 0.5 else 0.12
        for i in range(ln):
            if y + i < h:
                t[y + i, x] += dk * (1 - i / ln) if dk < 0 else dk * (i / ln)
    t = np.clip(t, 0, 1)
    dark, light = np.array(dark, dtype=np.float64), np.array(light, dtype=np.float64)
    out = dark[None, None, :] + (light - dark)[None, None, :] * t[..., None]
    reg = wolf_regions()
    keep = np.zeros((h, w), dtype=bool)
    for x0, y0, x1, y1 in reg["teeth"] + reg["mouth"]:
        keep[y0:y1, x0:x1] = True
    out = np.where(keep[..., None], rgb, out)
    red = (rgb[..., 0] > rgb[..., 1] * 1.6) & (rgb[..., 0] > 90)      # gums and tongue: vanilla's reds, darker
    out = np.where(red[..., None], rgb * 0.75, out)
    for x0, y0, x1, y1 in reg["eye"]:
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                out[yy, xx] = (226, 224, 178) if (xx + yy) % 3 else (238, 236, 200)
    for x0, y0, x1, y1 in reg["pupil"]:
        out[y0:y1, x0:x1] = (14, 12, 10)
    for x0, y0, x1, y1 in reg["sleep"]:
        out[y0:y1, x0:x1] = dark
    img = np.dstack([np.clip(out, 0, 255), alpha])
    return Image.fromarray(np.rint(img).astype(np.uint8), "RGBA")


def gen_shuck():
    base = os.path.join(rig.ASSETS, "textures", "entity", SHUCK)
    os.makedirs(os.path.dirname(base), exist_ok=True)
    shuck_texture(5, (12, 11, 13), (60, 58, 63), 47).save(base + ".png")
    shuck_texture(8, (17, 13, 10), (68, 56, 46), 48).save(base + "-brown.png")
    print("wrote", SHUCK + ".png and -brown.png")


# ================================================================ entity types

IDLE = {"triggeredBy": {"defaultAnim": True}, "easeOutSpeed": 4}
DIE = {"weight": 10, "triggeredBy": {"onControls": ["dead"]}}


def write_entity(code, comment, tags, weight, hitbox, dead_hitbox, eye, shape, textures, size, anims, health, decay,
                 harvest=None, extra_top=None):
    animations = []
    for acode, anim, blend, extra in anims:
        a = {"code": acode, "animation": anim, "animationSpeed": 1.0, "blendMode": blend}
        a.update(extra)
        animations.append(a)
    client_bh = [{"code": "repulseagents", "movable": True}, {"code": "controlledphysics", "stepHeight": 1.1251},
                 {"code": "floatupwhenstuck", "onlyWhenDead": True}, {"code": "interpolateposition"}]
    server_bh = [{"code": "repulseagents", "movable": True}, {"code": "controlledphysics", "stepHeight": 1.1251},
                 {"code": "health", "currenthealth": health, "maxhealth": health}, decay,
                 {"code": "floatupwhenstuck", "onlyWhenDead": True}]
    if harvest:
        client_bh.append({"code": "harvestable", "duration": 2})
        server_bh.append({"code": "harvestable", "duration": 2, "drops": harvest})
    server_bh.append({"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": [
        {"code": "backrooms-" + code, "priority": 1.5, "priorityForCancel": 1.5, "mincooldown": 0, "maxcooldown": 0}]})
    server_bh.append({"code": "entitystatetags"})
    texture = {"base": textures[0]}
    if len(textures) > 1:
        texture["alternates"] = [{"base": t} for t in textures[1:]]
    data = {"code": code, "class": "EntityAgent", "tags": tags, "weight": weight}
    data.update(extra_top or {})
    data.update({
        "hitboxSize": {"x": hitbox[0], "y": hitbox[1]},
        "deadHitboxSize": {"x": dead_hitbox[0], "y": dead_hitbox[1]},
        "eyeHeight": eye,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-" + code},
        "client": {"renderer": "Shape", "shape": {"base": shape}, "texture": texture, "size": size,
                   "behaviors": client_bh, "animations": animations},
        "server": {"behaviors": server_bh},
    })
    path = os.path.join(rig.ASSETS, "entities", code + ".json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("// " + comment + "\n")
        f.write(json.dumps(data, indent="\t") + "\n")
    print("wrote", os.path.relpath(path, rig.ROOT))


def gen_json():
    B = "backrooms:entity/"
    write_entity(
        "l47-snake", "Level 47's snakes: ordinary forest snakes, sacred to the Great Old Adder. Textures 0 grass snake, "
        "1 adder, 2 black rat snake, 3 ringed (milk) snake. Made by tools/gen_47_creatures.py",
        ["backrooms-entity", "animal", "habitat-land"], 2, (0.7, 0.3), (0.7, 0.25), 0.2,
        B + SNAKE, [B + SNAKE, B + SNAKE + "-adder", B + SNAKE + "-rat", B + SNAKE + "-ringed"], 1.0,
        [("idle", "idle", "AddAverage", IDLE), ("slither", "slither", "Average", {}), ("rear", "rear", "Average", {"weight": 5}),
         ("hurt", "hurt", "AddAverage", {"weight": 10}), ("die", "die", "Average", DIE)],
        3, {"code": "deaddecay", "hoursToDecay": 0.5})
    write_entity(
        "l47-greatadder", "Level 47's Great Old Adder: a bright crimson titanoboa about 9.5 blocks long laid in an S behind its "
        "head (the hitbox covers the head end). Made by tools/gen_47_creatures.py",
        ["backrooms-entity", "animal", "habitat-land"], 2500, (1.6, 1.5), (2.2, 1.0), 1.2,
        B + ADDER, [B + ADDER], 1.0,
        [("idle", "idle", "AddAverage", IDLE), ("slither", "slither", "Average", {}), ("rear", "rear", "Average", {"weight": 5}),
         ("strike", "strike", "Average", {"weight": 10}), ("devour", "devour", "Average", {"weight": 10}),
         ("hurt", "hurt", "AddAverage", {"weight": 10}), ("die", "die", "Average", DIE)],
        600, {"code": "deaddecay", "hoursToDecay": 0.25}, extra_top={"canClimb": False})
    write_entity(
        "l47-shuck", "Level 47's Black Shuck: a large black wolf of the Adderwood's nights (the vanilla wolf's shape at size "
        "1.3). Textures 0 coal black, 1 browner black. Made by tools/gen_47_creatures.py",
        ["backrooms-entity", "animal", "predator", "habitat-land"], 110, (1.1, 1.2), (1.3, 0.9), 1.15,
        "game:entity/animal/mammal/wolf/eurasian-adult", [B + SHUCK, B + SHUCK + "-brown"], 1.3,
        [("idle", "idle", "AddAverage", IDLE), ("walk", "walk", "Average", {}), ("run", "run", "Average", {}),
         ("attack", "attack", "Average", {"weight": 10}), ("howl", "howl", "Average", {"weight": 5}),
         ("sit", "sit", "Average", {"weight": 5, "easeInSpeed": 4, "easeOutSpeed": 4}), ("growl", "snarl_state", "Average", {}),
         ("sniff", "sniff", "Average", {}), ("hurt", "hurt", "AddAverage", {"weight": 10, "animationSpeed": 2.2}),
         ("die", "death", "Average", dict(DIE, animationSpeed=1.25))],
        30, {"code": "deaddecay", "hoursToDecay": 24, "decayedBlock": "game:carcass-medium"},
        harvest=[{"type": "item", "code": "game:bushmeat-raw", "quantity": {"avg": 7, "var": 1}},
                 {"type": "item", "code": "game:hide-raw-medium", "quantity": {"avg": 1.5, "var": 0}},
                 {"type": "item", "code": "game:fat", "quantity": {"avg": 1.25, "var": 0}}])
    write_entity(
        "l47-ophion", "Level 47's Ophion Occult Order: a hooded, crimson-robed, ivory-masked worshipper of the Great Old Adder. "
        "Textures 0 plain, 1 an elder's (deeper crimson, gold hems). Made by tools/gen_47_creatures.py",
        ["backrooms-entity", "humanoid", "habitat-land"], 60, (0.6, 1.9), (0.6, 0.5), 1.7,
        B + OPHION, [B + OPHION, B + OPHION + "-elder"], 1.0,
        [("idle", "idle", "AddAverage", IDLE), ("walk", "walk", "Average", {}), ("run", "run", "Average", {}),
         ("attack", "attack", "Average", {"weight": 10}),
         ("preach", "preach", "Average", {"weight": 5, "easeInSpeed": 3, "easeOutSpeed": 3}),
         ("beckon", "beckon", "Average", {"weight": 5}), ("bow", "bow", "Average", {"weight": 5}),
         ("hurt", "hurt", "AddAverage", {"weight": 10}), ("die", "die", "Average", DIE)],
        24, {"code": "deaddecay", "hoursToDecay": 0.25}, extra_top={"canClimb": True})


# ================================================================ main

def main():
    what = sys.argv[1:] or ["snake", "adder", "ophion", "shuck", "json"]
    if "snake" in what:
        gen_snake()
    if "adder" in what:
        gen_adder()
    if "ophion" in what and "gen_ophion" in globals():
        gen_ophion()
    if "shuck" in what and "gen_shuck" in globals():
        gen_shuck()
    if "json" in what and "gen_json" in globals():
        gen_json()


if __name__ == "__main__":
    main()
