"""Bones for the seabed and den props (bonepile, jawskeleton, and the ribcage's texture): the graphics pass's bone kit.

Models are built from rods (a shaft with a knob at each end, yawed on the floor or tilted in one plane), a skull
(cranium, jaw, maxilla, socket and tooth geometry) and the small vertebrae and ribs of a lying skeleton. Every
element is inside the block's 0..16 and rests on the floor (y 0) or on another bone; none floats. Each element
has a single rotation axis, which is all the game and tools/preview_shapes.py agree on.

Textures (all 32x32, painted with matlib, in block/detail/): `bone` (dry, matte, off-white with grey-brown
mottle, fibre streaks and pores; also the ribcage's), `bp-joint` (the knobs: darker, shadowed), `bp-dark` (sockets,
nose, the gap under the jaw) and `bp-tooth` (yellower).
"""
import random

import matlib as M
from detail_kit import bx
from detail_textures import save

S = M.S


def _streaks(img, seed, n, light, dark):
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        y, x0, ln = rng.randrange(S), rng.randrange(S), rng.randint(4, 11)
        d = dark if rng.random() < 0.5 else light
        for i in range(ln):
            x = (x0 + i) % S
            px[x, y] = M.rgba(M.lift(px[x, y][:3], d))


def _pores(img, seed, n, d):
    rng = random.Random(seed)
    px = img.load()
    for _ in range(n):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba(M.lift(px[x, y][:3], d))


def _bone(base, seed, mottle=7):
    img = M.noise_hv(base, 3, seed, mottle=mottle, hue=2.5)
    _streaks(img, seed + 1, 26, 7, -8)
    _pores(img, seed + 2, 14, -22)
    M.stain(img, seed + 3, radius=7, color=(150, 134, 106), strength=0.30, at=(9, 20))
    return img


def textures():
    save(_bone((204, 196, 180), 811), "bone")
    save(_bone((158, 146, 128), 821, mottle=5), "bp-joint")
    save(M.noise_hv((58, 51, 46), 3, 831, mottle=3, hue=1.5), "bp-dark")
    save(M.noise_hv((214, 204, 166), 3, 841, mottle=4, hue=1.5), "bp-tooth")


# ---------------- Elements ----------------

def _uv(el, v0):
    """Start a box's texture window `v0` units down the texture, so neighbouring bones do not repeat one another."""
    for f in el["faces"].values():
        u = f["uv"]
        f["uv"] = [u[0], u[1] + v0, u[2], u[3] + v0]
    return el


def rod(name, cx, cy, cz, length, t, yaw=0.0, tilt=0.0, axis="x", knob=1.35, v0=0):
    """A long bone: a shaft `length` long and `t` thick centred on (cx, cy, cz) along `axis` ("x" or "z"), with a knob
    of `knob` times the thickness (shadowed texture) at each end. `yaw` turns it about the vertical on the floor; `tilt`
    (instead) leans it in the plane of its axis. The lowest point of an unturned rod is cy - t/2."""
    k = t * knob
    half = length / 2
    rot = (0, yaw, 0) if yaw else ((0, 0, tilt) if axis == "x" and tilt else ((tilt, 0, 0) if tilt else None))
    org = (cx, cy, cz)

    def box(n, a, b, tex, ln):
        if axis == "x":
            frm, to = (cx + a, cy - b / 2, cz - b / 2), (cx + a + ln, cy + b / 2, cz + b / 2)
        else:
            frm, to = (cx - b / 2, cy - b / 2, cz + a), (cx + b / 2, cy + b / 2, cz + a + ln)
        return _uv(bx(n, frm, to, tex, rot=rot, origin=org), v0)

    kl = k * 0.7
    return [box(name, -half + kl * 0.6, t, "bone", length - kl * 1.2),
            box(name + "A", -half, k, "bp-joint", kl),
            box(name + "B", half - kl, k, "bp-joint", kl)]


def skull(name, cx, cz, yaw, s=1.0):
    """A skull resting on its jaw, facing north before `yaw`: cranium, jaw, maxilla with a tooth strip, a dark nose
    and two dark eye sockets set into the front."""
    org = (cx, 0, cz)

    def b(n, box, tex, faces=None):
        x1, y1, z1, x2, y2, z2 = box
        kw = {"faces": faces} if faces else {}
        return bx(name + n, (cx + x1 * s, y1 * s, cz + z1 * s), (cx + x2 * s, y2 * s, cz + z2 * s), tex,
                  rot=(0, yaw, 0), origin=org, **kw)
    N = ("north",)
    return [b("Jaw", (-1.7, 0, -1.8, 1.7, 1.2, 1.2), "bone"),
            b("Cranium", (-2.1, 1.2, -1.2, 2.1, 4.3, 2.9), "bone"),
            b("Brow", (-2.2, 3.0, -1.3, 2.2, 3.5, -1.2), "bp-joint", N),
            b("Maxilla", (-1.5, 1.2, -2.5, 1.5, 2.7, -1.2), "bone"),
            b("TeethU", (-1.3, 1.0, -2.65, 1.3, 1.5, -2.5), "bp-tooth", N),
            b("TeethL", (-1.4, 0.7, -1.95, 1.4, 1.1, -1.8), "bp-tooth", N),
            b("Nose", (-0.35, 1.7, -2.58, 0.35, 2.4, -2.45), "bp-dark", N),
            b("EyeL", (-1.55, 2.75, -1.27, -0.45, 3.65, -1.15), "bp-dark", N),
            b("EyeR", (0.45, 2.75, -1.27, 1.55, 3.65, -1.15), "bp-dark", N),
            b("Hollow", (-1.1, 0.05, -1.82, 1.1, 0.7, -1.81), "bp-dark", N)]


def vertebra(name, x, y, z, yaw=0.0, w=1.5):
    rot = (0, yaw, 0) if yaw else None
    return [bx(name, (x - w / 2, y, z - 0.6), (x + w / 2, y + 0.9, z + 0.6), "bone", rot=rot, origin=(x, y, z)),
            bx(name + "p", (x - 0.25, y + 0.9, z - 0.3), (x + 0.25, y + 1.4, z + 0.3), "bp-joint", rot=rot, origin=(x, y, z))]


def rib_pair(name, z, x=8.0, span=4.6, tilt=18.0, v0=0):
    """A pair of ribs lying out from the spine at x: each an arch of two bones, the inner rising away from the spine
    and the outer settling back to the floor."""
    els = []
    for side in (-1, 1):
        tag = "L" if side < 0 else "R"
        a_len, b_len = span * 0.6, span * 0.45
        ax = x + side * (0.5 + a_len / 2 * 0.95)
        bxc = x + side * (0.5 + a_len * 0.95 + b_len / 2 * 0.95)
        # rotation about z lifts the +x end for a positive angle
        els += rod(f"{name}{tag}1", ax, 0.65, z, a_len, 0.7, tilt=-side * tilt, knob=1.0, v0=v0)
        els += rod(f"{name}{tag}2", bxc, 0.5, z, b_len, 0.6, tilt=side * tilt * 0.8, knob=1.0, v0=v0 + 1)
    return els


# ---------------- The props ----------------

def bonepile():
    els = []
    # the lower layer, on the floor: two long bones at an angle and a short thick one
    els += rod("Femur1", 6.6, 0.65, 5.4, 10.5, 1.3, yaw=24, v0=0)
    els += rod("Femur2", 8.4, 0.6, 11.6, 9.0, 1.2, yaw=-16, v0=3)
    els += rod("Humerus", 12.4, 0.55, 9.5, 6.6, 1.1, yaw=78, v0=6)
    # the upper layer, leaning across the lower: it rests on their tops
    els += rod("Tibia", 7.2, 1.85, 8.4, 9.4, 1.1, yaw=58, v0=9)
    els += rod("Rib1", 4.2, 0.4, 11.4, 5.0, 0.7, yaw=-50, knob=1.0, v0=2)
    els += rod("Rib2", 11.0, 1.35, 6.2, 4.6, 0.7, yaw=-8, knob=1.0, v0=5)
    els += rod("Rib3", 3.2, 0.4, 6.6, 4.2, 0.7, yaw=64, knob=1.0, v0=8)
    els += vertebra("Vert1", 10.4, 0, 12.8, 20)
    els += vertebra("Vert2", 13.0, 0, 12.4, -35, 1.3)
    els += vertebra("Vert3", 3.8, 0, 3.4, 10)
    els += skull("Skull", 11.8, 4.0, -28, 0.85)
    return els


def jawskeleton():
    """A skeleton lying on the floor, head at the north (z 0), curled to fit one block: skull, spine, four rib pairs,
    pelvis, arms and bent legs. Everything is inside the block, unlike the old model, whose legs ran to z 24."""
    els = skull("Skull", 8.4, 3.4, 10, 0.88)
    for i in range(6):
        els += vertebra(f"Vert{i}", 8 + 0.1 * i, 0, 6.8 + i * 1.25, 0)
    for i, z in enumerate((7.4, 8.7, 10.0, 11.3)):
        els += rib_pair(f"Rib{i}", z, 8, span=4.7 - 0.4 * i, v0=i)
    els += [bx("Sacrum", (7, 0, 13.4), (9, 1.0, 14.6), "bone"),
            bx("IliacL", (4.6, 0, 12.6), (7.0, 1.1, 14.4), "bone", rot=(0, 18, 0), origin=(5.8, 0, 13.5)),
            bx("IliacR", (9.0, 0, 12.6), (11.4, 1.1, 14.4), "bone", rot=(0, -18, 0), origin=(10.2, 0, 13.5))]
    # arms: the left one folded back along the ribs, the right one thrown out
    els += rod("HumerusL", 3.6, 0.5, 9.0, 4.6, 1.0, axis="z", v0=1)
    els += rod("ForearmL", 4.3, 0.45, 12.0, 4.2, 0.8, yaw=-14, axis="z", knob=1.4, v0=4)
    els += rod("HumerusR", 12.8, 0.5, 8.4, 5.0, 1.0, yaw=-24, axis="z", v0=2)
    els += rod("ForearmR", 13.6, 0.4, 4.6, 4.0, 0.8, yaw=18, axis="z", knob=1.4, v0=5)
    # legs: femurs out from the pelvis, shins folded back
    els += rod("FemurL", 5.0, 0.55, 14.6, 5.0, 1.1, yaw=34, v0=7)
    els += rod("ShinL", 2.6, 0.5, 14.2, 3.6, 0.9, yaw=-40, v0=10)
    els += rod("FemurR", 11.2, 0.55, 14.6, 5.0, 1.1, yaw=-30, v0=8)
    els += rod("ShinR", 13.6, 0.5, 14.2, 3.6, 0.9, yaw=48, v0=11)
    return els


def ribcage():
    """The giant ribcage, one block wide and 28 units tall as the old tent of slabs was: a heavy spine of slightly
    irregular vertebrae along the top (z 1 to 15, y 28 to 31) and six ribs a side, each of three bones that start
    inside the spine: a short near-horizontal piece, a sloping shoulder, and a long near-vertical shank tucking back in
    at the floor. The cage is a rounded barrel, widest about a third of the way down. They are uneven in reach, tuck
    and spacing, one is broken short and one lies on the floor inside the cage."""
    import math
    rng = random.Random(91)
    els = []
    for i in range(9):
        z = 1.8 + i * 1.6
        ox, oy, yaw = rng.uniform(-0.4, 0.4), rng.uniform(-0.3, 0.3), rng.uniform(-7, 7)
        org = (8 + ox, 29.0 + oy, z)
        els += [bx(f"Vert{i}", (5.7 + ox, 28.0 + oy, z - 0.85), (10.3 + ox, 30.6 + oy, z + 0.85), "bone", rot=(0, yaw, 0), origin=org),
                bx(f"Disc{i}", (6.0 + ox, 28.3 + oy, z + 0.8), (10.0 + ox, 30.3 + oy, z + 1.0), "bp-joint", rot=(0, yaw, 0), origin=org),
                bx(f"Spine{i}", (7.4 + ox, 30.6 + oy, z - 0.45), (8.6 + ox, 31.7 + oy, z + 0.45), "bp-joint", rot=(0, yaw, 0), origin=org)]
    zs = [2.4, 4.9, 7.3, 9.7, 12.1, 14.4]
    for i, z0 in enumerate(zs):
        prof = math.sin(math.pi * (i + 0.9) / (len(zs) + 0.8))   # the middle ribs reach furthest
        for side in (-1, 1):
            tag = "L" if side < 0 else "R"
            z = z0 + rng.uniform(-0.3, 0.3)
            w = 7.0 + 2.2 * prof + rng.uniform(-0.4, 0.4)
            tuck = rng.uniform(2.4, 3.8)
            low = 0.4 + rng.uniform(0, 0.5)
            pts = [(8 + side * 1.4, 29.3), (8 + side * w * 0.55, 28.6), (8 + side * w, 20.0), (8 + side * (w - tuck), low)]
            broken = (i, side) == (2, -1)
            if broken:
                pts = pts[:3] + [(pts[2][0] - side * 0.3, 11.5)]
            t = 0.95 + 0.35 * prof
            for k in range(3):
                a_, b_ = pts[k], pts[k + 1]
                dx, dy = b_[0] - a_[0], b_[1] - a_[1]
                ang = math.degrees(math.atan2(dy, dx))
                if ang > 90:
                    ang -= 180
                elif ang <= -90:
                    ang += 180
                length = math.hypot(dx, dy) + 0.8                # overlaps the next piece
                els += rod(f"Rib{tag}{i}_{k}", (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2, z + 0.1 * k, length, t * (1 - 0.12 * k),
                           tilt=ang, knob=1.25, v0=(i * 3 + k) % 12)
    els += rod("Fallen", 9.6, 0.55, 8.4, 10.0, 1.1, yaw=12, axis="z", v0=4)
    els += rod("FallenB", 10.8, 0.5, 2.4, 3.6, 0.9, yaw=-30, axis="z", knob=1.2, v0=7)
    return els
