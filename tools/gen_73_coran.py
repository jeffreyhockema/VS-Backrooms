"""Level 73 (The Redlands): Coran, the unique guardian of the Silver Castle (Wikidot lore).

A middle-aged man 7'9" tall (2.36 m, 38 model px), heavily muscular, with slicked-back black hair and two horns. He has
no arms: gigantic golden chain links run from each shoulder to an enormous black spiked gauntlet. A black exoskeleton
covers most of his body (modelled as chitinous plates over the torso, shoulders, thighs and shins, dark trousers at the
joints). He has three hearts: two inside the gauntlets (a dark-red glowing seam at each wrist cuff) and one exposed on
his chest, red and glowing, in an opening of the chest plate. A scar gouged across his face took both eyes (he is blind:
no lantern, no hood); he wears the eyes on a necklace as an act of defiance. He is never hostile to humans and slaughters
the other entities outside the castle wall. The castle's banner is a silver heart with ram's horns, so the horns curl like
a ram's.

Build: a Pelvis root (belt, buckle, hip plates), legs (thigh with plate, shin with plate and ridge, knee plate and cap,
sabaton with toe cap and instep), abdomen (three stacked plates), chest (a framed opening with the exposed heart,
layered pectoral lames, spine ridge), a gorget, neck, head (scarred face, brow, chin, jaw, slicked hair with a back sweep,
two ram horns curled from stepped, rotated boxes), the necklace of eyes, a tattered mantle (a yoke and hanging strips
with ragged tails, parented to the chest so the animations carry it), and for each side a layered pauldron and a chain
of five alternating flat / edge-on gold links hanging from the shoulder (Link1 .. Link5, each parented to the one above;
every link is a real oval ring of four boxes, gold with darker inner faces), ending in a Gauntlet (parent Link5) with a
wrist cuff and rim, a glowing heart seam, a back plate, four two-segment fingers, a thumb, four knuckle spikes and back
spikes.

Rig conventions (rig.py): the model faces -X, its left is +Z, feet at y = 0, parts given in model space as if every
parent were unrotated. Rotations: Z swings a hanging limb forward when negative and a torso forward when positive; X
swings a limb out sideways (negative for the left arm, positive for the right); Y turns about the vertical.
Pivots: Neck (0, 31, 0), Head (0, 32.5, 0), Link1 (0, 29.3, +-9) and each next link at its own top (2.4 px lower each),
Gauntlet (0, 15, +-9), hips (0, 16.8, +-3.4), knees (0, 9.2, +-3.4).
Both sides are built by the same code with a sign (SIDES), not by Model.mirror, so the paint can know which face of a
ring is its inner one.

Animations (30 per second): idle (loop 8 s), walk (loop 1.33 s), run (loop 0.93 s), attack (0.8 s, Stop), sweep (1 s, Stop),
listen (0.8 s, Hold), bow (1.5 s, Stop), hurt (0.3 s, Stop). They key Pelvis, Abdomen, Chest, Heart, Neck, Head, Thigh,
Shin, Foot, Link1..5 and Gauntlet of each side.

Run from the repo root:  bash tools/locked.sh run python tools/gen_73_coran.py
"""
import json
import math
import os

import numpy as np

import rig
from rig import Model, pose
from oggutil import write_ogg

TAU = math.tau
NAME = "73/l73-coran"

BLK = (24, 22, 28)
BLKHI = (70, 66, 78)
IRON = (28, 28, 34)
IRONHI = (88, 90, 104)
STEEL = (196, 202, 214)
GOLD = (176, 138, 52)
GOLDHI = (236, 204, 110)
GOLDLO = (96, 70, 24)
SKIN = (186, 160, 130)
SKINLO = (146, 120, 96)
HAIR = (20, 18, 22)
IVORY = (226, 212, 182)
TROUSER = (40, 36, 40)
FACEK = {"up": 1.15, "down": 0.6, "north": 0.95, "south": 0.95, "east": 0.85, "west": 1.0}


# ---------------------------------------------------------------- painters

def put(ctx, xx, yy, c):
    if 0 <= xx < ctx.w and 0 <= yy < ctx.h:
        ctx.img.load()[ctx.x + xx, ctx.y + yy] = tuple(c[:3]) + (255,)


def get(ctx, xx, yy):
    return ctx.img.load()[ctx.x + xx, ctx.y + yy][:3]


def chitin(base=BLK, hi=BLKHI, rows=7):
    """Near-black plate with a cool sheen: lit top and edges, a few scratches, panel lines every few rows."""
    def paint(ctx):
        k = FACEK[ctx.face]
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                g = 0.10 + 0.12 * ctx.rng.random()
                if ctx.face == "up":
                    g += 0.40
                if yy == 0 and ctx.face not in ("up", "down"):
                    g += 0.35
                if xx == 0:
                    g += 0.12
                if (xx * 2 + yy) % 11 == 0:
                    g += 0.18
                c = rig.shade(rig.mix(base, hi, min(1.0, g)), k)
                if rows and ctx.h >= 8 and yy % rows == rows - 1 and ctx.face not in ("up", "down"):
                    c = rig.shade(c, 0.55)
                put(ctx, xx, yy, c)
    return paint


def cloth(ctx):
    k = FACEK[ctx.face]
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            m = 1 + 0.1 * (ctx.rng.random() - 0.5)
            if (xx + yy) % 2 == 0:
                m *= 1.12
            put(ctx, xx, yy, rig.shade(TROUSER, k * m))


def skin(ctx):
    k = FACEK[ctx.face]
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            c = rig.mix(SKIN, SKINLO, 0.5 * ctx.rng.random())
            if ctx.rng.random() < 0.05:
                c = rig.shade(c, 0.85)
            put(ctx, xx, yy, rig.shade(c, k))


def abdomen(ctx):
    """Segmented plates with dark skin showing in the gaps."""
    chitin(rows=0)(ctx)
    if ctx.face in ("up", "down"):
        return
    for yy in range(ctx.h):
        if yy % 3 == 2:
            for xx in range(ctx.w):
                put(ctx, xx, yy, rig.mix(SKINLO, (40, 26, 28), 0.5 + 0.3 * ctx.rng.random()))
    if ctx.face == "west":
        for yy in range(ctx.h):
            put(ctx, ctx.w // 2, yy, rig.shade(BLK, 0.6))


def chest(ctx):
    chitin(rows=0)(ctx)
    if ctx.face != "west":
        return
    w, h = ctx.w, ctx.h
    u0, u1, v0, v1 = int(w * 0.32), int(w * 0.68), 1, h - 1
    for yy in range(v0, v1):
        for xx in range(u0, u1):
            rim = xx in (u0, u1 - 1) or yy == v1 - 1
            put(ctx, xx, yy, (120, 54, 52) if rim else rig.mix((50, 18, 22), (74, 26, 30), ctx.rng.random()))
    for xx in range(u0, u1, 2):                       # plate teeth hanging into the opening
        put(ctx, xx, v0, rig.shade(BLKHI, 0.8))
        put(ctx, xx, v0 + 1, rig.shade(BLK, 0.9))
    for yy in range(h):                               # pectoral split down the middle, below the opening nothing
        if yy >= v1:
            put(ctx, w // 2, yy, rig.shade(BLK, 0.5))
    for xx in range(w):
        if xx < u0 or xx >= u1:
            if (xx + 3) % 7 == 0:
                for yy in range(1, h):
                    put(ctx, xx, yy, rig.shade(get(ctx, xx, yy), 0.7))


HEART = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000", "0000000"]


def heart(ctx):
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, xx, yy, rig.mix((120, 16, 20), (150, 20, 24), ctx.rng.random()))
    if ctx.face != "west":
        return
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            if HEART[min(6, yy * 7 // ctx.h)][min(6, xx * 7 // ctx.w)] == "1":
                c = rig.mix((176, 28, 32), (230, 60, 50), 1 - (xx + yy) / (ctx.w + ctx.h))
                put(ctx, xx, yy, c)


def eyeball(ctx):
    """A pale clouded eye with a few red veins, a dark pupil on the front face and a wet glint."""
    k = FACEK[ctx.face]
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            c = (232, 226, 214)
            if ctx.rng.random() < 0.16:
                c = (196, 104, 104)
            put(ctx, xx, yy, rig.shade(c, k * (0.95 + 0.08 * ctx.rng.random())))
    if ctx.face == "west":
        cx, cy = (ctx.w - 1) / 2, (ctx.h - 1) / 2
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                d = math.hypot(xx - cx, yy - cy)
                if d <= 1.25:
                    put(ctx, xx, yy, (132, 164, 190) if d > 0.6 else (24, 18, 24))
        put(ctx, 0, 0, (250, 246, 240))


def cord(ctx):
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, xx, yy, rig.shade((70, 52, 40), 0.8 + 0.4 * ctx.rng.random()))


def face(ctx):
    """Scarred and blind: closed hollow sockets with a ragged pale scar gouged across both, a heavy brow, a set mouth."""
    skin(ctx)
    if ctx.face != "west":
        return
    w, h = ctx.w, ctx.h

    def at(u, v):
        return min(w - 1, int(u * w)), min(h - 1, int(v * h))
    bx = at(0, 0.30)[1]
    for xx in range(w):                               # the shadow under the brow ridge
        put(ctx, xx, bx, rig.shade(SKIN, 0.74))
    for u0, u1 in ((0.10, 0.40), (0.60, 0.90)):       # the brows
        y = at(0, 0.23)[1]
        for xx in range(int(u0 * w), int(u1 * w)):
            put(ctx, xx, y, (44, 34, 32))
    eyes = []
    for u0, u1 in ((0.17, 0.38), (0.62, 0.83)):       # hollow, closed sockets with swollen lids
        x0, x1, y0 = int(u0 * w), max(int(u0 * w) + 1, int(u1 * w)), at(0, 0.40)[1]
        for xx in range(x0, x1 + 1):
            put(ctx, xx, y0 - 1, (122, 84, 74))
            put(ctx, xx, y0, (46, 24, 28))
            put(ctx, xx, y0 + 1, (60, 34, 34))
            put(ctx, xx, y0 + 2, (118, 82, 72))
        eyes.append((x0, x1, y0))
    x, y = at(0.5, 0.42)                              # nose bridge shadow
    for dy in range(0, 4):
        put(ctx, x, y + dy, rig.shade(SKIN, 0.8))
    for xx in (at(0.12, 0)[0], at(0.88, 0)[0]):       # cheek hollows
        put(ctx, xx, at(0, 0.66)[1], rig.shade(SKIN, 0.82))
    for i in range(w):                                # the scar: top left to lower right, ragged, stitched
        yc = int(h * 0.18 + h * 0.52 * i / max(1, w - 1) + (1 if i % 4 == 1 else 0))
        put(ctx, i, yc - 1, (112, 46, 46))
        put(ctx, i, yc, (226, 208, 196))
        put(ctx, i, yc + 1, (208, 186, 174) if i % 2 else (226, 208, 196))
        put(ctx, i, yc + 2, (122, 54, 50))
        if i % 3 == 0:
            put(ctx, i, yc - 2, (150, 120, 112))
            put(ctx, i, yc + 3, (150, 120, 112))
        for x0, x1, y0 in eyes:                       # across a socket it is a raw gouge
            if x0 <= i <= x1 and y0 - 1 <= yc + 1 and yc <= y0 + 2:
                put(ctx, i, yc, (92, 22, 26))
                put(ctx, i, yc + 1, (70, 16, 22))
    x0, y0 = at(0.32, 0.82)
    for x in range(x0, int(w * 0.68)):                # mouth, with a fuller lower lip
        put(ctx, x, y0, (88, 52, 50))
        put(ctx, x, y0 + 1, (150, 104, 94))
    for yy in range(int(h * 0.86), h):                # stubble
        for xx in range(w):
            if ctx.rng.random() < 0.3:
                put(ctx, xx, yy, rig.shade(get(ctx, xx, yy), 0.75))


def hair(ctx):
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            streak = 0.15 + 0.1 * (ctx.rng.random()) + (0.35 if (yy * 2 + xx) % 5 == 0 and ctx.face in ("up", "east") else 0)
            put(ctx, xx, yy, rig.shade(rig.mix(HAIR, (74, 70, 84), streak), FACEK[ctx.face]))


def horn(c0, c1):
    def paint(ctx):
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                t = (xx + yy) / max(1, ctx.w + ctx.h - 2)
                c = rig.mix(c0, c1, t)
                if (xx + yy) % 3 == 2:
                    c = rig.shade(c, 0.82)                # growth ridges
                put(ctx, xx, yy, rig.shade(c, FACEK[ctx.face] * (0.94 + 0.1 * ctx.rng.random())))
    return paint


def gold_part(inner=()):
    """One side of a chain ring: gold, lit on the top and front edges; the faces looking into the ring's hole are dark."""
    def paint(ctx):
        k = FACEK[ctx.face]
        dark = ctx.face in inner
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                g = 0.30 + 0.22 * ctx.rng.random()
                if xx == 0 or yy == 0:
                    g += 0.35
                if xx == ctx.w - 1 or yy == ctx.h - 1:
                    g -= 0.15
                g = max(0.0, min(1.0, g))
                if dark:
                    c = rig.mix(GOLDLO, (34, 24, 8), 0.25 + 0.5 * (1 - g))
                else:
                    c = rig.mix(GOLD, GOLDHI, g) if g > 0.25 else rig.mix(GOLD, GOLDLO, 0.25 - g)
                put(ctx, xx, yy, rig.shade(c, k))
    return paint


def edged(base=BLK, hi=BLKHI):
    """A chitin plate with a lit upper and left rim and a dark lower and right edge, so stacked lames read as layers."""
    def paint(ctx):
        chitin(base, hi, rows=0)(ctx)
        w, h, k = ctx.w, ctx.h, FACEK[ctx.face]
        if w < 3 or h < 3:
            return
        for xx in range(w):
            put(ctx, xx, 0, rig.shade(rig.mix(base, hi, 0.95), k))
            put(ctx, xx, h - 1, rig.shade(base, 0.45 * k))
        for yy in range(h):
            put(ctx, 0, yy, rig.shade(rig.mix(base, hi, 0.7), k))
            put(ctx, w - 1, yy, rig.shade(base, 0.5 * k))
    return paint


def mantle(ctx):
    """Tattered black cloth: vertical folds, a few paler threads and a frayed, darker hem."""
    k = FACEK[ctx.face]
    base = (42, 34, 46)
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            m = 0.85 + 0.3 * ctx.rng.random()
            if xx % 3 == 0:
                m *= 0.8
            if (xx + yy // 2) % 7 == 0:
                m *= 1.18
            c = rig.shade(base, k * m)
            if yy >= ctx.h - 2 and ctx.face not in ("up", "down"):
                c = rig.shade(base, 0.5) if ctx.rng.random() < 0.5 else rig.shade((74, 62, 70), k)
            put(ctx, xx, yy, c)


def spike(ctx):
    """Black iron at the root, pale steel at the tip. The tip is named by the part's tag {"tip": face} (default west)."""
    tip = ctx.part.tag.get("tip", "west")
    opp = {"west": "east", "east": "west", "up": "down", "down": "up", "north": "south", "south": "north"}[tip]
    ax = {"west": "x", "east": "x", "up": "y", "down": "y", "north": "z", "south": "z"}[tip]
    pos = tip in ("east", "up", "south")
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            u, v = (xx + 0.5) / ctx.w, (yy + 0.5) / ctx.h
            if ctx.face == tip:
                c = STEEL
            elif ctx.face == opp:
                c = IRON
            else:
                x = {"north": 1 - u, "south": u, "up": u, "down": u}.get(ctx.face)
                z = {"west": u, "east": 1 - u, "up": v, "down": 1 - v}.get(ctx.face)
                y = 1 - v
                p = {"x": x, "y": y, "z": z}[ax]
                f = p if pos else 1 - p
                c = rig.mix(IRON, STEEL, max(0.0, min(1.0, f * 1.25 - 0.15)))
            put(ctx, xx, yy, rig.shade(c, FACEK[ctx.face]))


def gauntlet(ctx):
    chitin(IRON, IRONHI, rows=0)(ctx)
    if ctx.face in ("up", "down"):
        return
    for yy in range(2, ctx.h, 4):                       # knuckle / finger ridges
        for xx in range(ctx.w):
            put(ctx, xx, yy, rig.shade(get(ctx, xx, yy), 0.55))
    for xx in range(1, ctx.w, 4):
        put(ctx, xx, 1, STEEL)                          # rivets
        put(ctx, xx, ctx.h - 2, rig.shade(STEEL, 0.7))


def cuff(ctx):
    chitin(IRON, IRONHI, rows=0)(ctx)
    for xx in range(0, ctx.w, 3):
        put(ctx, xx, ctx.h // 2, rig.shade(IRONHI, 0.9))


def seam(ctx):
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            put(ctx, xx, yy, rig.mix((110, 14, 20), (200, 40, 36), 0.5 + 0.5 * math.sin(xx * 1.1)))


# ---------------------------------------------------------------- the model

SIDES = ((1, "L"), (-1, "R"))


def build():
    m = Model(NAME, atlas_width=64, seed=73)
    C = chitin()
    P = edged(BLK, BLKHI)
    PI = edged(IRON, IRONHI)
    GOLDP = gold_part()

    def box(name, p0, p1, parent, paint, sg=1, rest=(0, 0, 0), pivot=None, glow=0, tag=None):
        """A box given by two corners in left-side (+z) model space; sg = -1 mirrors it to the right side (z -> -z)."""
        x0, x1 = sorted((p0[0], p1[0]))
        y0, y1 = sorted((p0[1], p1[1]))
        za, zb = sorted((sg * p0[2], sg * p1[2]))
        if pivot is not None:
            pivot = (pivot[0], pivot[1], sg * pivot[2])
        elif any(rest):
            pivot = ((x0 + x1) / 2, (y0 + y1) / 2, (za + zb) / 2)
        return m.part(name, (x0, y0, za), (x1 - x0, y1 - y0, zb - za), pivot=pivot, parent=parent,
                      rest=(rest[0] * sg, rest[1] * sg, rest[2]), paint=paint, glow=glow, tag=tag)

    # ---- Pelvis (root): dark trousers, a belt with a gold buckle, hip plates
    pelvis = m.part("Pelvis", (-3.5, 16, -6), (7, 4, 12), pivot=(0, 18, 0), paint=cloth)
    box("Belt", (-4.0, 18.2, -6.3), (-3.5, 19.7, 6.3), pelvis, PI)
    box("Buckle", (-4.5, 18.4, -1.1), (-4.0, 19.5, 1.1), pelvis, GOLDP)
    # ---- Legs: thigh and plate, shin with plate and ridge, knee plate and cap with a spike, sabaton with toe cap and instep
    for sg, S in SIDES:
        thigh = box("Thigh" + S, (-3, 9, 0.8), (3, 17.2, 6.0), pelvis, C, sg, pivot=(0, 16.8, 3.4))
        box("ThighPlate" + S, (-3.5, 10.6, 1.2), (-3.0, 16.4, 5.6), thigh, P, sg)
        shin = box("Shin" + S, (-2.8, 2.0, 1.1), (2.8, 9.4, 5.7), thigh, C, sg, pivot=(0, 9.2, 3.4))
        box("Knee" + S, (-3.6, 8.0, 1.4), (-2.4, 10.8, 5.4), shin, P, sg, pivot=(0, 9.2, 3.4))
        box("KneeCap" + S, (-4.3, 8.4, 2.0), (-3.6, 10.4, 4.8), shin, P, sg)
        box("ShinPlate" + S, (-3.4, 2.8, 1.5), (-2.8, 8.0, 5.3), shin, P, sg)
        box("ShinRidge" + S, (-3.9, 3.0, 3.0), (-3.4, 7.8, 3.8), shin, PI, sg)
        foot = box("Foot" + S, (-5.6, 0, 0.9), (2.8, 2.2, 5.9), shin, chitin(rows=0), sg, pivot=(0, 2.2, 3.4))
        box("ToeCap" + S, (-6.4, 0, 1.2), (-5.6, 1.9, 5.6), foot, P, sg)
    # ---- Torso: abdomen plates, chest with the framed heart, layered pectoral lames
    ab = m.part("Abdomen", (-3.2, 19.5, -5), (6.4, 5, 10), pivot=(0, 20, 0), parent=pelvis, paint=abdomen)
    for i, (y0, y1, hz) in enumerate(((19.9, 21.3, 3.4), (21.5, 22.9, 3.8), (23.1, 24.5, 4.2))):
        box(f"AbPlate{i + 1}", (-3.7, y0, -hz), (-3.2, y1, hz), ab, P)
    ch = m.part("Chest", (-4, 24, -7), (8, 5, 14), pivot=(0, 24.5, 0), parent=ab, paint=chest)
    up = m.part("UpperChest", (-3.2, 28.5, -5.8), (6.4, 3.3, 11.6), pivot=(0, 29, 0), parent=ch, paint=skin)
    box("Spine", (3.8, 22, -1.4), (5.2, 31.5, 1.4), ch, C, pivot=(0, 28, 0))
    box("Heart", (-4.4, 25.1, -1.6), (-3.2, 28.3, 1.6), ch, heart, pivot=(-4, 26.6, 0), glow=200)
    box("LipTop", (-4.5, 28.4, -3.1), (-4.0, 29.2, 3.1), ch, PI)          # the frame of the opening
    box("LipBot", (-4.5, 24.0, -3.1), (-4.0, 24.8, 3.1), ch, PI)
    for sg, S in SIDES:
        box("LipSide" + S, (-4.5, 24.8, 2.5), (-4.0, 28.4, 3.1), ch, PI, sg)
        for i, (y0, y1) in enumerate(((27.5, 29.0), (25.8, 27.6))):     # lames, the upper ones in front
            box(f"Lame{i + 1}{S}", (-4.7 + 0.25 * i, y0, 3.2), (-4.0, y1, 6.9), ch, P, sg)
    # ---- the necklace of eyes
    box("Cord", (-3.7, 31.2, -3.0), (3.1, 31.7, 3.0), up, cord)
    for sg, S in SIDES:
        box("Strand" + S, (-3.85, 30.0, 1.3), (-3.5, 31.4, 1.7), up, cord, sg, pivot=(-3.6, 31.4, 1.5))
        box("Eye" + S, (-4.7, 28.4, 0.6), (-3.0, 30.2, 2.4), up, eyeball, sg, pivot=(-3.7, 30.2, 1.5))
    # ---- Neck, gorget and head
    neck = box("Neck", (-2.3, 31.0, -2.4), (2.3, 32.6, 2.4), ch, skin, pivot=(0, 31.0, 0))
    box("GorgetB", (2.3, 30.8, -3.4), (3.6, 33.0, 3.4), ch, P)
    head = box("Head", (-3, 32.3, -3), (3, 37.8, 3), neck, face, pivot=(0, 32.5, 0))
    box("Nose", (-3.6, 34.0, -0.7), (-2.8, 35.8, 0.7), head, skin)
    box("Brow", (-3.6, 35.5, -3.1), (-2.9, 36.5, 3.1), head, skin)
    box("HairTop", (-3.1, 36.9, -3.15), (3.3, 38.3, 3.15), head, hair)
    box("HairFront", (-3.5, 36.5, -2.9), (-2.8, 37.4, 2.9), head, hair)
    box("HairBack", (2.5, 33.0, -3.15), (3.5, 37.9, 3.15), head, hair)
    box("HairSweep", (3.4, 33.6, -2.6), (4.5, 37.6, 2.6), head, hair)
    # the ram's horns: stepped boxes, each turned along the curl, rising from the temple, back, down behind the ear and
    # forward again to the tip (a circle in the x-y plane that tightens and drifts outwards in z)
    cx, cy = 1.4, 35.0
    for sg, S in SIDES:
        for i in range(5):
            phi = -30 + 62 * i
            r = 3.1 - 0.0075 * (phi + 30)
            t = (1.7, 1.55, 1.35, 1.1, 0.8)[i]
            x = cx + r * math.sin(math.radians(phi))
            y = cy + r * math.cos(math.radians(phi))
            z = 3.0 + 0.7 * i
            seg = 3.4
            u = i / 4
            box(f"Horn{i + 1}{S}", (x - seg / 2, y - t / 2, z - t / 2), (x + seg / 2, y + t / 2, z + t / 2), head,
                horn(rig.mix((58, 44, 38), (210, 196, 162), u), rig.mix((100, 78, 58), (224, 210, 176), u)), sg,
                rest=(0, 0, -phi))
    # ---- Shoulders: layered pauldrons with a rim and spikes; gold chains; gauntlets
    for sg, S in SIDES:
        box("Shoulder" + S, (-3.0, 28.2, 6.2), (3.0, 31.8, 11.2), ch, C, sg, pivot=(0, 29, 8.7))
        box("Pauldron1" + S, (-3.4, 31.4, 6.0), (3.4, 32.4, 11.4), ch, P, sg)
        box("Pauldron2" + S, (-3.8, 30.4, 6.4), (3.8, 31.5, 12.0), ch, P, sg)
        box("Pauldron3" + S, (-4.2, 29.4, 6.8), (4.2, 30.5, 12.6), ch, P, sg)
        box("ShSpike" + S, (-0.6, 32.2, 8.1), (0.6, 34.4, 9.3), ch, spike, sg, pivot=(0, 31.8, 8.7), tag={"tip": "up"})
        parent = ch
        for k in range(5):
            top = 29.3 - 2.4 * k
            if k % 2 == 0:      # hole along x: the ring lies in the z-y plane (its bars at the low / high z end)
                xa, xb, za, zb, bz = -0.55, 0.55, 7.8, 10.2, 0.7
                lo_face, hi_face = ("south", "north") if sg > 0 else ("north", "south")
                bars = ((xa, za, xb, za + bz, gold_part((lo_face,))), (xa, zb - bz, xb, zb, gold_part((hi_face,))))
            else:               # hole along z: the ring lies in the x-y plane (its bars at the low / high x end)
                xa, xb, za, zb, bz = -1.2, 1.2, 8.5, 9.5, 0.7
                bars = ((xa, za, xa + bz, zb, gold_part(("east",))), (xb - bz, za, xb, zb, gold_part(("west",))))
            n = f"Link{k + 1}"
            link = box(n + S, (xa, top - 0.7, za), (xb, top, zb), parent, gold_part(("down",)), sg, pivot=(0, top, 9.0))
            box(n + "Lo" + S, (xa, top - 2.8, za), (xb, top - 2.1, zb), link, gold_part(("up",)), sg)
            for j, (ax0, az0, ax1, az1, pp) in enumerate(bars):
                box(n + "AB"[j] + S, (ax0, top - 2.1, az0), (ax1, top - 0.7, az1), link, pp, sg)
            parent = link
        g = box("Gauntlet" + S, (-3.6, 6.5, 6.0), (3.6, 14.9, 12.0), parent, gauntlet, sg, pivot=(0, 15, 9.0))
        box("Cuff" + S, (-2.4, 14.9, 6.6), (2.4, 17.9, 11.4), g, cuff, sg)
        box("Seam" + S, (-2.7, 15.5, 6.3), (2.7, 16.4, 11.7), g, seam, sg, glow=140)
        box("Rim" + S, (-3.0, 17.4, 6.2), (3.0, 18.2, 11.8), g, PI, sg)
        box("BackPlate" + S, (3.6, 7.4, 6.4), (4.2, 14.2, 11.6), g, PI, sg)
        for j, c in enumerate((6.75, 8.25, 9.75, 11.25)):                  # four fingers, two segments each, curled in
            long_ = j in (1, 2)
            box(f"Finger{j + 1}a{S}", (-5.0, 9.0, c - 0.65), (-3.6, 12.6, c + 0.65), g, PI, sg)
            box(f"Finger{j + 1}b{S}", (-5.4 if long_ else -5.0, 7.6, c - 0.6), (-2.8, 9.2, c + 0.6), g, PI, sg)
        box("ThumbA" + S, (-3.8, 9.8, 4.9), (-1.6, 12.4, 6.0), g, PI, sg)
        box("ThumbB" + S, (-4.8, 9.0, 5.1), (-3.6, 11.0, 5.9), g, PI, sg)
        for i, z in enumerate((6.9, 8.3, 9.7, 11.1)):
            box(f"Knuckle{S}{i + 1}", (-5.6, 10.0, z - 0.6), (-3.4, 11.2, z + 0.6), g, spike, sg, tag={"tip": "west"})
        for i, y in enumerate((10.1,)):
            box(f"BackSpike{S}{i + 1}", (4.2, y - 0.6, 8.4), (6.4, y + 0.6, 9.6), g, spike, sg, tag={"tip": "east"})
    # ---- the mantle: a yoke over the shoulders and hanging strips, the lower tails turned and ragged
    box("Mantle", (3.3, 28.4, -6.6), (5.5, 31.1, 6.6), ch, mantle)
    for sg, S in SIDES:
        for i, (z0, z1, yend, rz) in enumerate(((1.7, 3.4, 8.0, 4), (3.5, 5.2, 10.5, 5), (5.3, 7.0, 14.0, 6))):
            ymid = yend + 5.0
            zc = (z0 + z1) / 2
            upper = box(f"Mantle{i + 1}{S}", (5.0, ymid, z0), (5.7, 28.4, z1), ch, mantle, sg,
                        rest=(0, 0, rz), pivot=(5.3, 28.4, zc))
            tilt = (5, -6, 4)[i] * (1 if i % 2 == 0 else -1)
            box(f"MantleTail{i + 1}{S}", (5.0, yend, z0 + 0.3), (5.7, ymid + 0.3, z1 - 0.3), upper, mantle, sg,
                rest=(tilt, 0, 4), pivot=(5.2, ymid, zc))
    return m


# ---------------------------------------------------------------- animations

def s(p, amp, shift=0.0):
    return amp * math.sin(TAU * (p + shift))


def cycle(frames, steps, fn):
    return {int(round(frames * i / steps)): fn(i / steps) for i in range(steps)}


LINKS = ["Link1", "Link2", "Link3", "Link4", "Link5"]


def arm(S, zs, out=0.0, g=(0, 0), gy=0.0, outs=None):
    """Pose of one chain and its gauntlet. zs: five Z rotations (forward = negative); out: sideways swing of the whole
    chain at the shoulder (outwards positive, applied with the right sign for each side); g: (z, x) of the gauntlet."""
    sg = -1 if S == "L" else 1
    d = {}
    for k, name in enumerate(LINKS):
        z = zs[k] if isinstance(zs, (list, tuple)) else zs
        x = (out if k == 0 else 0) if outs is None else outs[k]
        d[name + S] = pose((sg * x, 0, z))
    d["Gauntlet" + S] = pose((sg * g[1], gy, g[0]))
    return d


def hanging(S, a, lag=0.0, out=0.0, amp=1.0):
    """A chain swinging like a pendulum: the first link by a, the rest following more gently, the gauntlet most."""
    return arm(S, [a, a * 0.35 + lag, a * 0.3 + lag, a * 0.25 + lag, a * 0.2 + lag], out=out, g=(a * 0.3 + lag, 0))


def merge(*ds):
    out = {}
    for d in ds:
        out.update(d)
    return out


def animations(m):
    # ---- idle: 8 s. Slow heavy breathing, a heartbeat each second, the chains swaying, the head turning a little
    def idle(p):
        br = 0.5 - 0.5 * math.cos(TAU * p * 2)
        beat = max(0.0, math.sin(TAU * p * 8)) ** 6
        d = {
            "Pelvis": pose((s(p, 0.5), 0, 0), (0, 0, 0)),
            "Abdomen": pose((0, 0, 0.3 * br)),
            "Chest": pose((s(p, 0.4, 0.25), 0, 0.8 * br), s=(1, 1 + 0.012 * br, 1 + 0.012 * br)),
            "Heart": pose((0, 0, 0), s=(1 + 0.12 * beat, 1 + 0.12 * beat, 1 + 0.12 * beat)),
            "Neck": pose((s(p, 1.5, 0.1), s(p, 9), s(p, 0.8, 0.3))),
            "Head": pose((s(p, 1.5, 0.4), s(p, 4, 0.1), -1.5 + s(p, 1.5, 0.2))),
        }
        for S, ph in (("L", 0.0), ("R", 0.5)):
            d.update(hanging(S, s(p, 3.0, ph), lag=s(p, 2.5, ph + 0.15), out=2 + s(p, 1.5, ph + 0.3)))
        return d

    m.animation("idle", 240, cycle(240, 24, idle))

    # ---- walk: 40 frames, heavy stride
    def walk(p):
        a = s(p, 24)
        bend = 34 * max(0.0, -math.cos(TAU * p))
        bend2 = 34 * max(0.0, math.cos(TAU * p))
        d = {
            "Pelvis": pose((s(p, 1.2, 0.25), s(p, 4), 2), (0, -0.7 * abs(math.cos(TAU * p)) + 0.2, 0)),
            "ThighL": pose((0, 0, a)), "ThighR": pose((0, 0, -a)),
            "ShinL": pose((0, 0, bend)), "ShinR": pose((0, 0, bend2)),
            "FootL": pose((0, 0, -a * 0.5 - bend * 0.4)), "FootR": pose((0, 0, a * 0.5 - bend2 * 0.4)),
            "Abdomen": pose((0, -s(p, 3), 0)), "Chest": pose((s(p, 1.2, 0.25), -s(p, 3), 3 + 0.6 * math.cos(TAU * p * 2))),
            "Neck": pose((0, s(p, 2), -2)), "Head": pose((0, 0, -1)),
        }
        d.update(hanging("L", s(p, 14, 0.5), lag=s(p, 8, 0.35), out=4 + s(p, 2, 0.25)))
        d.update(hanging("R", s(p, 14, 0.0), lag=s(p, 8, 0.85), out=4 + s(p, 2, 0.75)))
        return d

    m.animation("walk", 40, cycle(40, 10, walk))

    # ---- run: 28 frames, a loping charge: leaning, gauntlets trailing on the chains
    def run(p):
        a = s(p, 40)
        b1 = 55 * max(0.0, -math.cos(TAU * p))
        b2 = 55 * max(0.0, math.cos(TAU * p))
        d = {
            "Pelvis": pose((s(p, 2, 0.25), s(p, 5), 6), (0, -1.2 + 1.8 * abs(math.sin(TAU * p)) - 0.9, 0)),
            "ThighL": pose((0, 0, a)), "ThighR": pose((0, 0, -a)),
            "ShinL": pose((0, 0, b1)), "ShinR": pose((0, 0, b2)),
            "FootL": pose((0, 0, -a * 0.4 - b1 * 0.3)), "FootR": pose((0, 0, a * 0.4 - b2 * 0.3)),
            "Abdomen": pose((0, -s(p, 4), 4)), "Chest": pose((0, -s(p, 5), 10)),
            "Neck": pose((0, s(p, 3), -9)), "Head": pose((0, 0, -4)),
        }
        for S, ph in (("L", 0.5), ("R", 0.0)):
            sw = s(p, 18, ph)
            d.update(arm(S, [38 + sw, 22 + 0.5 * sw, 18 + 0.4 * sw, 14, 12], out=14 + s(p, 4, ph), g=(18 + 0.3 * sw, 0)))
        return d

    m.animation("run", 28, cycle(28, 8, run))

    # ---- attack: 24 frames. The right gauntlet is wound back, thrown up and over on its chain, slammed down in front
    R0 = {}
    atk = {
        0: R0,
        5: merge({"Chest": pose((0, 22, -7)), "Pelvis": pose((0, 8, 0)), "Neck": pose((0, -10, 0)),
                  "ThighL": pose((0, 0, 6)), "ThighR": pose((0, 0, -8))},
                 arm("R", [28, 20, 16, 14, 12], out=10, g=(18, 0)), arm("L", [-6, -2, -2, -2, -2], out=5)),
        10: merge({"Chest": pose((0, 6, -14)), "Pelvis": pose((0, 2, -2)), "Neck": pose((0, 0, 8)), "Head": pose((0, 0, 4)),
                   "ThighL": pose((0, 0, 10)), "ThighR": pose((0, 0, -12))},
                  arm("R", [-168, -30, -26, -20, -16], out=8, g=(-20, 0)), arm("L", [-10, -4, -4, -4, -4], out=8)),
        14: merge({"Chest": pose((0, -14, 18)), "Pelvis": pose((0, -6, 4), (0, -0.8, 0)), "Neck": pose((0, 8, -4)),
                   "Abdomen": pose((0, -4, 6)), "ThighL": pose((0, 0, -22)), "ThighR": pose((0, 0, 14)),
                   "ShinL": pose((0, 0, 8)), "ShinR": pose((0, 0, 14))},
                  arm("R", [-46, -8, -6, -6, -4], out=-2, g=(-12, 0)), arm("L", [8, 4, 4, 2, 2], out=4)),
        17: merge({"Chest": pose((0, -12, 14)), "Pelvis": pose((0, -5, 3), (0, -0.5, 0)), "Neck": pose((0, 6, -4)),
                   "ThighL": pose((0, 0, -20)), "ThighR": pose((0, 0, 12))},
                  arm("R", [-54, -10, -8, -6, -4], out=-1, g=(-14, 0)), arm("L", [8, 4, 4, 2, 2], out=4)),
        23: R0,
    }
    m.animation("attack", 24, {f: merge({k: pose() for k in ("Chest", "Pelvis")}, d) for f, d in atk.items()}, end="Stop")

    # ---- sweep: 30 frames. Both gauntlets thrown round in a wide horizontal arc by a turn of the whole body
    def spin(yaw, chestyaw, outv, tr):
        d = {"Pelvis": pose((0, yaw, 0)), "Chest": pose((0, chestyaw, 2)), "Abdomen": pose((0, chestyaw * 0.3, 0)),
             "Neck": pose((0, -(yaw + chestyaw) * 0.6, 0)),
             "ThighL": pose((0, 0, -10)), "ThighR": pose((0, 0, 10))}
        d.update(arm("L", [0, tr, tr, tr, tr], out=outv, g=(tr * 0.5, 0)))
        d.update(arm("R", [0, -tr, -tr, -tr, -tr], out=outv, g=(-tr * 0.5, 0)))
        return d

    m.animation("sweep", 30, {
        0: spin(0, 0, 0, 0),
        7: spin(18, 30, 62, -14),
        13: spin(6, 8, 88, 8),
        19: spin(-22, -34, 90, 26),
        25: spin(-14, -20, 60, 10),
        29: spin(0, 0, 0, 0),
    }, end="Stop")

    # ---- listen: 24 frames, held. The head tilts and turns toward a sound, the chest following a little
    lst = {"Neck": pose((14, 24, 3)), "Head": pose((10, 8, -6)), "Chest": pose((0, 8, -1)), "Pelvis": pose((0, 3, 0))}
    lst.update(hanging("L", -2, out=3))
    lst.update(hanging("R", -2, out=3))
    m.animation("listen", 24, {0: {k: pose() for k in lst}, 9: {k: v for k, v in lst.items()}, 16: lst, 23: lst}, end="Hold")

    # ---- bow: 45 frames. One gauntlet drawn up to the chest on its chain, a slow nod and a bow of the whole body
    bow_up = {"Chest": pose((0, 0, 11)), "Abdomen": pose((0, 0, 5)), "Neck": pose((0, 0, 16)), "Head": pose((0, 0, 8)),
              "Pelvis": pose((0, 0, 3)), "ThighL": pose((0, 0, -3)), "ThighR": pose((0, 0, -3))}
    bow_up.update(arm("R", [-50, -30, -24, -18, -8], out=-24, g=(-6, 0)))
    bow_up.update(hanging("L", 8, out=4))
    lead = {k: (v if k.startswith(("Link", "Gaunt")) else pose()) for k, v in bow_up.items()}
    for k in ("Chest", "Neck"):
        lead[k] = pose((0, 0, 3))
    m.animation("bow", 45, {0: {k: pose() for k in bow_up}, 14: lead, 24: bow_up, 31: bow_up, 44: {k: pose() for k in bow_up}}, end="Stop")

    # ---- hurt: 9 frames, a short flinch
    hurt = merge({"Chest": pose((0, -6, -9)), "Neck": pose((0, 4, 7)), "Head": pose((0, 0, 6)), "Pelvis": pose((0, 0, -2), (1.0, 0, 0))},
                 arm("L", [14, 6, 4, 4, 4], out=18, g=(8, 0)), arm("R", [14, 6, 4, 4, 4], out=18, g=(8, 0)))
    m.animation("hurt", 9, {0: {k: pose() for k in hurt}, 3: hurt, 8: {k: pose() for k in hurt}}, end="Stop")
    return [a[0] for a in m.animations]


# ---------------------------------------------------------------- entity type

def entity():
    anims = [
        ("idle", "AddAverage", {"triggeredBy": {"defaultAnim": True}}),
        ("walk", "Average", {}),
        ("run", "Average", {}),
        ("attack", "Average", {"weight": 10}),
        ("sweep", "Average", {"weight": 10}),
        ("listen", "Average", {}),
        ("bow", "Average", {"weight": 10}),
        ("hurt", "AddAverage", {"weight": 10}),
    ]
    animations = []
    for code, blend, extra in anims:
        a = {"code": code, "animation": code, "animationSpeed": 1.0, "blendMode": blend}
        a.update(extra)
        animations.append(a)
    data = {
        "code": "l73-coran",
        "class": "BackroomsCoran",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": 250,
        "hitboxSize": {"x": 0.9, "y": 2.3},
        "selectionBoxSize": {"x": 1.0, "y": 2.4},
        "eyeHeight": 2.1,
        "canClimb": False,
        "attributes": {"invulnerable": True},
        "client": {
            "renderer": "Shape",
            "shape": {"base": f"backrooms:entity/{NAME}"},
            "texture": {"base": f"backrooms:entity/{NAME}"},
            "size": 1.0,
            "behaviors": [{"code": "repulseagents", "movable": False}, {"code": "controlledphysics", "stepHeight": 1.1251},
                          {"code": "interpolateposition"}],
            "animations": animations,
        },
        "server": {
            "behaviors": [
                {"code": "repulseagents", "movable": False},
                {"code": "controlledphysics", "stepHeight": 1.1251},
                {"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": [
                    {"code": "backrooms-l73coran", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
                     "walkSpeed": 0.022, "runSpeed": 0.05},
                    {"code": "lookaround", "priority": 0.5}]},
            ]
        },
        "sounds": {"hurt": "backrooms:entity/73/coran/hurt"},
    }
    path = os.path.join(rig.ASSETS, "entities", "l73-coran.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("// Coran (Level 73): the Silver Castle's guardian, 2.36 m, gold chains and spiked gauntlets, never harms a human. Class BackroomsCoran\n")
        f.write(json.dumps(data, indent="\t") + "\n")


# ---------------------------------------------------------------- sounds

RATE = 44100
OUT = os.path.join(rig.ASSETS, "sounds", "entity", "73", "coran")


def write(name, signal, peak=0.85):
    os.makedirs(OUT, exist_ok=True)
    signal = np.asarray(signal, dtype=np.float64)
    fade = min(len(signal) // 4, int(0.01 * RATE))
    signal[:fade] *= np.linspace(0, 1, fade)
    signal[-fade:] *= np.linspace(1, 0, fade)
    signal = peak * signal / max(1e-9, np.max(np.abs(signal)))
    write_ogg(os.path.join(OUT, name + ".ogg"), signal, RATE)


def secs(x):
    return np.arange(int(x * RATE)) / RATE


def band(sig, lo, hi):
    sp = np.fft.rfft(sig)
    f = np.fft.rfftfreq(len(sig), 1 / RATE)
    sp *= (f >= lo) & (f <= hi)
    return np.fft.irfft(sp, n=len(sig))


def place(out, snd, at):
    i = int(at * RATE)
    n = min(len(snd), len(out) - i)
    if n > 0:
        out[i:i + n] += snd[:n]


def clink(rng, length=0.35, lo=1400, hi=5600):
    """One link of chain: a few inharmonic partials with fast decays and a touch of noise."""
    t = secs(length)
    out = np.zeros(len(t))
    for _ in range(rng.integers(3, 6)):
        f = rng.uniform(lo, hi)
        out += rng.uniform(0.3, 1.0) * np.sin(TAU * f * t) * np.exp(-t * rng.uniform(18, 60))
    out += 0.3 * band(rng.normal(size=len(t)), 2000, 8000) * np.exp(-t * 120)
    return out


def step_sound(rng, length=0.6):
    t = secs(length)
    out = np.zeros(len(t))
    out += np.sin(TAU * (60 - 22 * t / 0.3).clip(36) * t) * np.exp(-t * 11)
    out += 0.7 * band(rng.normal(size=len(t)), 50, 420) * np.exp(-t * 16)
    for k in range(rng.integers(4, 8)):
        place(out, clink(rng, 0.3) * rng.uniform(0.06, 0.2) * (0.97 ** k), rng.uniform(0.04, 0.42))
    return out


def chain_sound(rng, length):
    t = secs(length)
    out = np.zeros(len(t))
    drag = band(rng.normal(size=len(t)), 700, 3800)
    env = np.abs(band(rng.normal(size=len(t)), 0, 14))
    out += 0.25 * drag * env / (env.max() + 1e-9) * np.sin(np.pi * t / length) ** 0.5
    at = 0.02
    while at < length - 0.2:
        place(out, clink(rng, 0.3) * rng.uniform(0.2, 0.8), at)
        at += rng.uniform(0.04, 0.16)
    return out


def strike_sound(rng, length=0.6):
    t = secs(length)
    out = np.sin(TAU * (48 - 14 * t).clip(30) * t) * np.exp(-t * 8) * 1.2
    out += 0.7 * band(rng.normal(size=len(t)), 70, 900) * np.exp(-t * 22)
    out += 0.5 * band(rng.normal(size=len(t)), 900, 6500) * np.exp(-t * 45)
    for k in range(4):
        place(out, clink(rng, 0.3, 900, 4200) * rng.uniform(0.15, 0.4), 0.01 + k * rng.uniform(0.02, 0.07))
    return out


def voice(length, f0_fn, formants, rng, amp_fn=None, drive=1.0, breath=0.03, rough=0.0):
    """Source-filter by harmonics: a bank of harmonics of a moving f0, weighted by formant peaks."""
    t = secs(length)
    f0 = f0_fn(t)
    phase = np.cumsum(f0) / RATE
    amp = amp_fn(t) if amp_fn else np.sin(np.pi * t / length) ** 0.7
    out = np.zeros(len(t))
    for k in range(1, 48):
        fk = f0 * k
        if fk.max() > 3500:
            break
        w = np.zeros(len(t))
        for fc, bw, gain in formants(t):
            w += gain * np.exp(-0.5 * ((fk - fc) / bw) ** 2)
        w += 0.12 / k
        out += (w / k ** 0.6) * np.sin(TAU * k * phase + k * 0.3)
    if rough:
        out *= 1 + rough * np.sin(TAU * 38 * t + 3 * np.sin(TAU * 3 * t))
    out += breath * band(rng.normal(size=len(t)), 150, 1200)
    out = np.tanh(drive * out / (np.abs(out).max() + 1e-9) * 1.4)
    return out * amp


def sounds():
    rng = np.random.default_rng(73)
    for i in range(3):
        write(f"step{i + 1}", step_sound(rng, 0.5 + 0.1 * i))
    for i, ln in enumerate((0.9, 1.2, 1.45)):
        write(f"chain{i + 1}", chain_sound(rng, ln))
    for i in range(2):
        write(f"strike{i + 1}", strike_sound(rng))

    def mk_formants(f1a, f1b, f2a, f2b):
        def f(t):
            u = t / t[-1]
            return [(f1a + (f1b - f1a) * u, 90, 1.0), (f2a + (f2b - f2a) * u, 140, 0.45), (2400, 300, 0.12)]
        return f
    # three hums: rising, falling, wobbling "mm - oh"
    specs = [(2.1, lambda t: 74 + 8 * np.sin(np.pi * t / t[-1]) + 1.2 * np.sin(TAU * 4.5 * t), mk_formants(300, 480, 800, 900)),
             (2.4, lambda t: 88 - 14 * (t / t[-1]) + 1.0 * np.sin(TAU * 4 * t), mk_formants(500, 330, 900, 700)),
             (1.8, lambda t: 80 + 6 * np.sin(TAU * 0.9 * t) + 1.0 * np.sin(TAU * 5 * t), mk_formants(330, 520, 760, 1000))]
    for i, (ln, f0, fm) in enumerate(specs):
        write(f"voice{i + 1}", voice(ln, f0, fm, rng, drive=0.8, breath=0.02))
    # roar: a bellow, f0 rising then falling, saturated, rough
    write("roar", voice(1.5, lambda t: 70 + 55 * np.sin(np.pi * np.minimum(1, t / 1.0) * 0.9) * np.exp(-((t - 0.6) / 0.7) ** 2) + 6 * np.sin(TAU * 7 * t),
                        mk_formants(650, 760, 1100, 1250), rng, amp_fn=lambda t: np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.9) * 3.0),
                        drive=3.0, breath=0.12, rough=0.25), 0.9)
    # hurt: a short low grunt
    write("hurt", voice(0.4, lambda t: 96 - 40 * t / 0.4, mk_formants(520, 420, 1000, 850), rng,
                        amp_fn=lambda t: np.minimum(1, t / 0.03) * np.exp(-t * 6), drive=2.0, breath=0.06, rough=0.15))


def generate(LANG=None):
    m = build()
    animations(m)
    m.save()
    entity()
    sounds()
    if LANG is not None:
        LANG["item-creature-l73-coran"] = "Coran"
        LANG["prefixandcreature-l73-coran"] = "Coran"
    return m


if __name__ == "__main__":
    generate()

