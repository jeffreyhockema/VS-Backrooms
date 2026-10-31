"""The Beast of Level 5 (Entity 18): its model (tools/rig.py), its two looks, its entity types, its sounds and its
names. Run from the repo root:  python tools/gen_beast.py   (only this entity's files are written)

Canon (the Fandom wiki's Entity 18, "The Beast of Level 5", the best-known and fullest account; the Wikidot page of
the same number is a short story in his voice, "the Gentleman", and agrees with it): an eldritch, sapient thing deep in
the Terror Hotel, "a chimaeric conglomeration of human, octopus and deathmoth dressed in a furred black suit". About
6'2" (30 px); "a head resembling a dark blue octopus, his eyes an otherworldly violet"; two pairs of arms, "the upper set
resembling mottled blue tentacles", the lower "akin to those of a human, albeit having clawed hands with sharpened
ungues of what appears to be steel"; "a fashionable and furry black suit and pointed, buckled black leather shoes
resembling footwear common in the eighteenth century"; the furred outer jacket "appears to actually be a massive pair
of moth-wings", which he unfurls. Unveiled to attack he grows to "over 4 metres", "his claws sharpen and elongate into
shining blades; the tentacles on the bottom of his head undulate furiously; and his purple eyes split into compound
orbs like those of a moth, thousands of tiny twinkling violet lights shining from dark eyeballs".

The build: a gentleman's frame in an 18th-century frock suit of black moth-fur (the coat tails are the folded wings,
hinged at the shoulder blades, moth-patterned on their inner face), a violet waistcoat, a white jabot, buckled shoes
with pointed toes; an octopus head (a lower face, a mantle swept back) with violet slit-pupilled eyes and a beard of
eight tentacles; two tentacle arms from behind the shoulders; human arms in sleeves with lace cuffs and steel claws.
The unveiled form is the same shape drawn half as big again (the hotel's halls are three blocks high, so 2.8 blocks,
not four metres), with its own animations (claws stretched into blades, wings half spread, tentacles thrashing) and
its own texture (the compound eyes).

Animations: idle, walk, run, attack, hurt, die; offer (the handshake: one clawed hand held out, a little bow), shocked
(the start a wanderer who looks him in the eye gives him: he recoils and stands frozen, trembling), unveil (the wings
open, the arms spread, the blades come out); for the unveiled form fury (its idle), stalk (walk), charge (run) and rend
(attack).

Conventions (rig.py): the model faces -X, its left is +Z, up is +Y; a hanging part swings backward with +Z.
"""
import json
import math
import os
import re

import numpy as np

import rig
from rig import ASSETS, Model, clamp, fill, fur, mix, pose, rect, shade, speckle
from gen_models import blotch, cycle, death, full, lit, line, plateau, ragged, s, texel

TAU = math.tau

SUIT = (30, 27, 31)          # the black moth-fur of the suit
SUIT_HI = (62, 56, 60)
SUIT_DARK = (12, 11, 13)
WAIST = (66, 34, 82)         # the waistcoat: a deep violet brocade
WAIST_HI = (104, 62, 124)
GOLD = (176, 142, 74)
LACE = (226, 220, 204)
LACE_SHADE = (168, 160, 146)
SKIN = (36, 56, 96)          # a dark blue octopus skin, mottled
SKIN_HI = (70, 104, 150)
SKIN_DARK = (18, 28, 56)
SKIN_PALE = (92, 120, 164)
SUCKER = (170, 168, 196)
VIOLET = (178, 92, 236)
VIOLET_HI = (226, 178, 255)
PUPIL = (12, 6, 18)
STEEL = (164, 170, 180)
STEEL_HI = (226, 230, 236)
LEATHER = (20, 18, 18)
LEATHER_HI = (74, 70, 70)
SILVER = (196, 196, 204)
WING = (122, 106, 94)         # the wings' inner face: dusky moth scales
WING_DARK = (40, 34, 36)
WING_PALE = (176, 160, 140)

# Which look is being painted: "gentleman" (violet slit-pupilled eyes) or "unveiled" (compound eyes)
LOOK = {"eyes": "gentleman"}

SIDES = ("north", "south", "east", "west")


# ---------------- Painters ----------------

def suit(ctx):
    """Black moth-fur: combed downward on the sides, a faint violet-brown lift on the ridges of the nap."""
    fill(ctx, SUIT, 0.06)
    if ctx.face in SIDES:
        fur(ctx, (0.15, 1.0), length=3, density=0.55, tip=1.35, root=0.8)
    else:
        fur(ctx, (1.0, 0.3), length=2, density=0.35, tip=1.25, root=0.85)


def trouser(ctx):
    fill(ctx, shade(SUIT, 0.92), 0.05)
    if ctx.face in SIDES:
        fur(ctx, (0.0, 1.0), length=2, density=0.3, tip=1.25, root=0.85)
        # a crease down the front of the leg
        if ctx.face == "west":
            line(ctx, 0.5, 0.0, 0.5, 1.0, SUIT_HI, 0.35)


def shoe(ctx):
    """Polished black leather: a lit edge along the top, a gleam on the toe."""
    fill(ctx, LEATHER, 0.04)
    if ctx.face == "up":
        line(ctx, 0.1, 0.5, 0.9, 0.5, LEATHER_HI, 0.5)
    elif ctx.face in SIDES:
        line(ctx, 0.0, 0.05, 1.0, 0.05, LEATHER_HI, 0.6)
        if ctx.part.name.startswith("Toe"):
            texel(ctx, 1, 1, LEATHER_HI, 0.7)


def buckle(ctx):
    fill(ctx, SILVER, 0.05)
    if ctx.face == "up":
        rect(ctx, 0.25, 0.25, 0.75, 0.75, LEATHER)
        texel(ctx, 0, 0, (240, 240, 246), 0.8)


def waist(ctx):
    """The waistcoat in front, buttoned, between the open fronts of the coat; fur at the sides and back."""
    if ctx.face != "west":
        suit(ctx)
        return
    brocade(ctx)
    rect(ctx, 0.0, 0.0, 0.2, 1.0, SUIT)
    rect(ctx, 0.8, 0.0, 1.0, 1.0, SUIT)
    for v in (0.15, 0.45, 0.75):
        texel(ctx, ctx.w // 2, int(v * ctx.h), GOLD)


def brocade(ctx):
    fill(ctx, WAIST, 0.05)
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            if (xx + 2 * yy) % 5 == 0 and (xx - yy) % 3 == 0:
                old = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = mix(old[:3], WAIST_HI, 0.6) + (255,)


def chest(ctx):
    """The coat's chest: wide fur lapels either side of the waistcoat, a white shirt at the throat; fur elsewhere."""
    if ctx.face != "west":
        suit(ctx)
        return
    brocade(ctx)
    for xx in range(ctx.w):
        for yy in range(ctx.h):
            u, v = (xx + 0.5) / ctx.w, (yy + 0.5) / ctx.h
            # the lapels narrow toward the waist
            edge = 0.18 + 0.16 * (1 - v)
            if u < edge or u > 1 - edge:
                texel(ctx, xx, yy, SUIT, 1.0)
            elif u < edge + 0.05 or u > 1 - edge - 0.05:
                texel(ctx, xx, yy, SUIT_HI, 0.8)   # the lit roll of the lapel
    for v in (0.62, 0.86):
        texel(ctx, ctx.w // 2, int(v * ctx.h), GOLD)
    fur(ctx, (0.0, 1.0), length=2, density=0.2, tip=1.3, root=0.85)


def cravat(ctx):
    """A lace jabot: tiers of white ruffles, shaded under each."""
    fill(ctx, LACE, 0.04, face_shade=False)
    px = ctx.img.load()
    for yy in range(ctx.h):
        k = 0.82 if yy % 3 == 2 else 1.0
        for xx in range(ctx.w):
            old = px[ctx.x + xx, ctx.y + yy]
            c = shade(old[:3], k)
            if (xx + yy) % 4 == 0:
                c = mix(c, LACE_SHADE, 0.4)
            px[ctx.x + xx, ctx.y + yy] = c + (255,)


def cuff(ctx):
    cravat(ctx)
    ragged(ctx, 1)


def skin(ctx, base=SKIN, k=1.0):
    """Octopus skin: dark blue, mottled light and dark in soft patches, pale papillae here and there."""
    fill(ctx, shade(base, k), 0.05)
    area = ctx.w * ctx.h
    blotch(ctx, SKIN_HI, max(1, area // 40), 0.8, 2.4, 0.45)
    blotch(ctx, SKIN_DARK, max(1, area // 36), 0.8, 2.2, 0.55)
    speckle(ctx, SKIN_PALE, 0.025)


def head(ctx):
    skin(ctx)
    if ctx.face == "west":
        # creases under the eyes, the dark of the beak hidden in the tentacles below
        line(ctx, 0.1, 0.6, 0.4, 0.68, SKIN_DARK, 0.6)
        line(ctx, 0.6, 0.68, 0.9, 0.6, SKIN_DARK, 0.6)
        rect(ctx, 0.35, 0.86, 0.65, 1.0, SKIN_DARK)


def mantle(ctx):
    skin(ctx, k=1.04)
    if ctx.face in SIDES:
        # faint ridges round the mantle, as an octopus's skin bunches
        for v in (0.3, 0.62):
            line(ctx, 0.0, v, 1.0, v + 0.04, SKIN_DARK, 0.3)


def brow(ctx):
    skin(ctx, k=0.85)


def eye(ctx):
    """The gentleman's eyes: violet with a black bar of a pupil; unveiled, dark orbs full of tiny violet lights."""
    if ctx.face != "west":
        skin(ctx)
        return
    if LOOK["eyes"] == "unveiled":
        fill(ctx, (22, 10, 34), 0.1, face_shade=False)
        px = ctx.img.load()
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                if ctx.rng.random() < 0.42:
                    c = VIOLET_HI if ctx.rng.random() < 0.4 else VIOLET
                    px[ctx.x + xx, ctx.y + yy] = c + (255,)
        return
    fill(ctx, VIOLET, 0.06, face_shade=False)
    rect(ctx, 0.0, 0.0, 1.0, 0.14, shade(VIOLET, 0.6))
    rect(ctx, 0.08, 0.42, 0.92, 0.6, PUPIL)          # the horizontal slit of an octopus
    texel(ctx, 1, 1, VIOLET_HI, 0.9)


def tentacle(ctx):
    """A tentacle: the mottled skin, and pale suckers in a row along the inner face."""
    skin(ctx)
    name = ctx.part.name
    inner = ctx.part.tag.get("inner")
    if ctx.face == inner:
        px = ctx.img.load()
        cx = ctx.w // 2
        for yy in range(1, ctx.h, 2):
            old = px[ctx.x + cx, ctx.y + yy]
            px[ctx.x + cx, ctx.y + yy] = mix(old[:3], SUCKER, 0.85) + (255,)
            if ctx.w >= 3 and (yy // 2) % 2 == 0:
                for dx in (-1, 1):
                    if 0 <= cx + dx < ctx.w:
                        old = px[ctx.x + cx + dx, ctx.y + yy]
                        px[ctx.x + cx + dx, ctx.y + yy] = mix(old[:3], SUCKER, 0.4) + (255,)
    if name.endswith(("3", "4")) and ctx.face == "down":
        fill(ctx, SKIN_PALE, 0.05)


def hand(ctx):
    skin(ctx, k=0.95)
    if ctx.face == "up":
        fill(ctx, SKIN_DARK, 0.05)


def finger(ctx):
    skin(ctx, k=0.9)


def claw(ctx):
    """Steel ungues: grey steel, a bright edge down the front."""
    fill(ctx, STEEL, 0.05)
    if ctx.face in ("west", "north"):
        line(ctx, 0.5, 0.0, 0.5, 1.0, STEEL_HI, 0.8)
    if ctx.face == "down":
        fill(ctx, STEEL_HI, 0.03)


def wing(ctx):
    """The coat tails, which are wings: fur outside (the back of the coat); the moth's scales inside (seen only when
    they open): dusky brown with dark bands, a violet eye spot, veins fanning from the root."""
    if ctx.face != "west":
        suit(ctx)
        if ctx.part.tag.get("tip") and ctx.face in SIDES:
            ragged(ctx, 2)
        return
    fill(ctx, WING, 0.1, face_shade=False)
    blotch(ctx, WING_DARK, 3, 1.5, 4.0, 0.5)
    blotch(ctx, WING_PALE, 2, 1.0, 2.5, 0.3)
    speckle(ctx, shade(WING, 0.7), 0.06)
    for u in (0.15, 0.4, 0.65, 0.9):
        line(ctx, 0.5, 0.0, u, 1.0, shade(WING, 0.55), 0.5)
    if ctx.part.tag.get("tip"):
        rect(ctx, 0.0, 0.0, 1.0, 0.25, WING_DARK)
        ragged(ctx, 2)
        return
    rect(ctx, 0.0, 0.7, 1.0, 0.76, WING_DARK)
    # the eye spot, a third of the way down: dark ring, violet, a cream pupil that looks back at you
    cu, cv = 0.5, (0.62 if ctx.part.tag.get("hind") else 0.36)
    if ctx.part.tag.get("hind"):
        rect(ctx, 0.0, 0.0, 1.0, 0.08, WING_DARK)
    for r, c in ((0.3, WING_DARK), (0.22, (120, 70, 150)), (0.13, VIOLET), (0.06, (234, 222, 196))):
        rect(ctx, cu - r, cv - r * 0.22, cu + r, cv + r * 0.22, c)


# ---------------- The model ----------------

def chain(m, prefix, parent, top, thick, lengths, rest, paint, inner, taper=0.8):
    """A hanging chain of tapering segments (a tentacle) from `top` (x, y, z), each segment's rest rotation from
    `rest` (one tuple per segment). Returns the segment names, root first."""
    names = []
    x, y, z = top
    t = thick
    p = parent
    for i, length in enumerate(lengths):
        name = f"{prefix}{i}"
        p = m.part(name, (x - t / 2, y - length, z - t / 2), (t, length, t), pivot=(x, y, z), parent=p, rest=rest[i],
                   paint=paint, tag={"inner": inner})
        names.append(name)
        y -= length
        t = max(0.35, t * taper)
    return names


# Element groups used by the animations
FACE_TENTACLES = []
ARM_TENTACLES = {"L": [], "R": []}
CLAWS = []

# The beard: (z, x, segment lengths, sway phase)
BEARD = [(-1.55, -1.9, (1.6, 1.5, 1.3, 1.0), 0.0), (-0.95, -2.25, (1.9, 1.7, 1.5, 1.1), 0.21), (-0.32, -2.4, (2.1, 1.9, 1.6, 1.2), 0.47),
         (0.32, -2.4, (2.0, 1.9, 1.7, 1.2), 0.71), (0.95, -2.25, (1.8, 1.7, 1.5, 1.1), 0.33), (1.55, -1.9, (1.6, 1.4, 1.3, 0.9), 0.58),
         (-1.95, -0.9, (1.8, 1.6, 1.5, 1.3), 0.12), (1.95, -0.9, (1.8, 1.6, 1.4, 1.3), 0.84)]


@lit(floor=22.0)
def beast(look="gentleman"):
    LOOK["eyes"] = look
    FACE_TENTACLES.clear()
    ARM_TENTACLES["L"].clear()
    ARM_TENTACLES["R"].clear()
    CLAWS.clear()
    m = Model("beast", atlas_width=64, seed=18)

    # ---- Legs and hips ----
    pelvis = m.part("Pelvis", (-1.8, 12.8, -2.7), (3.6, 2.4, 5.4), pivot=(0, 14, 0), paint=suit)
    thigh = m.part("ThighL", (-1.35, 7.4, 0.25), (2.7, 6.2, 2.3), pivot=(0, 13.6, 1.4), parent=pelvis, paint=trouser)
    shin = m.part("ShinL", (-1.15, 1.3, 0.35), (2.3, 6.3, 2.1), pivot=(0, 7.6, 1.4), parent=thigh, paint=trouser)
    shoe_p = m.part("ShoeL", (-2.9, 0, 0.3), (4.3, 1.4, 2.2), pivot=(0, 1.3, 1.4), parent=shin, paint=shoe)
    m.part("ToeL", (-4.4, 0, 0.85), (1.5, 0.9, 1.1), pivot=(-2.9, 0.45, 1.4), parent=shoe_p, rest=(0, 0, 0), paint=shoe)
    m.part("BuckleL", (-2.55, 1.4, 0.75), (1.2, 0.3, 1.3), pivot=(-2.0, 1.4, 1.4), parent=shoe_p, paint=buckle)
    m.mirror("ThighL", "ThighR")

    # ---- Body: the waistcoat under an open frock coat of fur ----
    waist_p = m.part("Waist", (-1.7, 15.0, -2.5), (3.4, 3.6, 5.0), pivot=(0, 15.0, 0), parent=pelvis, rest=(0, 0, 2), paint=waist)
    chest_p = m.part("Chest", (-2.1, 18.4, -3.1), (4.1, 5.2, 6.2), pivot=(0, 18.4, 0), parent=waist_p, rest=(0, 0, 2), paint=chest)
    m.part("Collar", (-0.4, 22.9, -2.7), (2.8, 1.9, 5.4), pivot=(1.0, 23.0, 0), parent=chest_p, rest=(0, 0, -6), paint=suit)
    m.part("Cravat", (-2.5, 20.4, -1.0), (0.5, 2.8, 2.0), pivot=(-2.25, 23.2, 0), parent=chest_p, paint=cravat)
    m.part("CravatKnot", (-2.6, 22.6, -0.8), (0.7, 0.8, 1.6), pivot=(-2.25, 23.0, 0), parent=chest_p, paint=cravat)

    # ---- The head: an octopus's, the mantle swept back, a beard of tentacles ----
    head_p = m.part("Head", (-2.3, 23.4, -2.1), (4.0, 3.2, 4.2), pivot=(0, 23.6, 0), parent=chest_p, paint=head)
    # The mantle: a bulb swept back from the brow, rounded by a narrower cap and a tip behind
    mantle_p = m.part("Mantle", (-2.0, 26.2, -2.8), (5.6, 4.6, 5.6), pivot=(-0.6, 26.4, 0), parent=head_p, rest=(0, 0, -24), paint=mantle)
    m.part("MantleTop", (-1.4, 30.8, -2.2), (4.4, 1.2, 4.4), pivot=(0.8, 31.0, 0), parent=mantle_p, paint=mantle)
    m.part("MantleTip", (3.6, 27.0, -2.0), (1.2, 3.4, 4.0), pivot=(3.6, 28.7, 0), parent=mantle_p, paint=mantle)
    m.part("EyeL", (-2.55, 24.9, 0.5), (0.4, 1.3, 1.5), pivot=(-2.3, 25.5, 1.2), parent=head_p, paint=eye, glow=60)
    m.part("BrowL", (-2.65, 26.1, 0.35), (0.7, 0.5, 1.8), pivot=(-2.3, 26.3, 1.2), parent=head_p, rest=(-8, 0, 0), paint=brow)
    m.mirror("EyeL", "EyeR")
    m.mirror("BrowL", "BrowR")
    for i, (z, x, lengths, _) in enumerate(BEARD):
        inner = "east"
        side = 6 if z > 0 else -6
        rest = [(-side * 0.6 if abs(z) > 1.8 else -side * 0.3, 0, 4), (0, 0, -6), (side * 0.3, 0, -10), (side * 0.6, 0, -14)]
        FACE_TENTACLES.append(chain(m, f"Beard{i}_", head_p, (x, 23.9, z), 0.95, lengths, rest, tentacle, inner, taper=0.78))

    # ---- The lower arms: a man's, in sleeves, with lace at the wrist and steel claws ----
    arm = m.part("ArmL", (-1.1, 16.4, 3.1), (2.2, 6.6, 2.1), pivot=(0, 22.6, 4.1), parent=chest_p, rest=(-4, 0, -4), paint=suit)
    fore = m.part("ForearmL", (-1.0, 11.0, 3.15), (2.0, 5.6, 2.0), pivot=(0, 16.6, 4.15), parent=arm, rest=(0, 0, -12), paint=suit)
    m.part("CuffL", (-1.25, 10.6, 2.9), (2.5, 1.0, 2.5), pivot=(0, 11.6, 4.15), parent=fore, paint=cuff)
    palm = m.part("HandL", (-0.9, 8.6, 3.25), (1.8, 2.4, 1.8), pivot=(0, 11.0, 4.15), parent=fore, rest=(0, 0, 4), paint=hand)
    for i in range(3):
        x = -0.85 + i * 0.6
        f = m.part(f"Finger{i}L", (x, 7.3, 3.55), (0.48, 1.4, 0.5), pivot=(x + 0.24, 8.7, 3.8), parent=palm, rest=(0, 0, -6 + 4 * i), paint=finger)
        m.part(f"Claw{i}L", (x + 0.02, 5.9, 3.6), (0.44, 1.45, 0.4), pivot=(x + 0.24, 7.35, 3.8), parent=f, rest=(0, 0, -10), paint=claw)
    thumb = m.part("ThumbL", (-1.05, 8.0, 3.0), (0.5, 1.3, 0.5), pivot=(-0.8, 9.2, 3.25), parent=palm, rest=(12, 0, -14), paint=finger)
    m.part("ThumbClawL", (-1.03, 6.7, 3.05), (0.44, 1.3, 0.4), pivot=(-0.8, 8.05, 3.25), parent=thumb, rest=(0, 0, -10), paint=claw)
    m.mirror("ArmL", "ArmR")
    for side in "LR":
        CLAWS.extend([f"Claw{i}{side}" for i in range(3)] + [f"ThumbClaw{side}"])

    # ---- The upper arms: tentacles, from behind the shoulders ----
    for side, z, sign in (("L", 3.0, 1), ("R", -3.0, -1)):
        rest = [(-sign * 22, 0, 8), (sign * 6, 0, -8), (sign * 4, 0, -14), (sign * 6, 0, -18), (sign * 8, 0, -22)]
        ARM_TENTACLES[side].extend(chain(m, f"Tent{side}", chest_p, (1.2, 23.0, z), 1.5, (2.6, 2.4, 2.2, 2.0, 1.7), rest, tentacle,
                                         "north" if side == "L" else "south", taper=0.84))

    # ---- The coat tails, which are wings, hinged at the shoulder blades ----
    wing_p = m.part("WingL", (1.9, 8.6, 0.05), (0.8, 14.6, 3.2), pivot=(2.3, 23.0, 0.4), parent=chest_p, rest=(-3, 0, 2), paint=wing)
    m.part("WingTipL", (1.95, 6.4, 0.25), (0.7, 2.3, 2.8), pivot=(2.3, 8.7, 1.6), parent=wing_p, paint=wing, tag={"tip": True})
    # The hindwing, folded away inside the coat tail until the wings open, when it fans out below the forewing
    m.part("WingHindL", (2.0, 9.4, 0.15), (0.6, 13.2, 3.0), pivot=(2.3, 23.0, 0.4), parent=wing_p, paint=wing, tag={"hind": True})
    m.mirror("WingL", "WingR")

    animate(m)
    return m


# ---------------- Animations ----------------

def tentacles(p, amp, speed=1.0, fury=False):
    """The beard and the tentacle arms writhing: every segment a little out of step with the one above it."""
    out = {}
    k = 3.2 if fury else 1.0
    for t, names in enumerate(FACE_TENTACLES):
        ph = BEARD[t][3]
        for i, n in enumerate(names):
            out[n] = pose((s(p * speed, amp * k * (0.6 + 0.3 * i), ph + 0.13 * i), 0, s(p * speed, amp * k * (0.5 + 0.35 * i), ph + 0.25 + 0.11 * i)))
    for side, sign in (("L", 1), ("R", -1)):
        for i, n in enumerate(ARM_TENTACLES[side]):
            out[n] = pose((sign * s(p * speed, amp * k * 0.8, 0.1 * i + (0.5 if sign < 0 else 0)), 0,
                           s(p * speed, amp * k * (1.0 + 0.25 * i), 0.15 * i + (0.3 if sign < 0 else 0))))
    return out


def blades(d, length=3.4):
    """Unveiled: every claw drawn out into a blade."""
    for n in CLAWS:
        old = d.get(n, pose())
        d[n] = pose(old["rot"], old["off"], s=(1, length, 1))
    return d


def spread_wings(d, a=60, flap=0.0):
    d["WingL"] = pose((-a - flap, 0, 14))
    d["WingR"] = pose((a + flap, 0, 14))
    d["WingHindL"] = pose((0.36 * a, 0, 6))
    d["WingHindR"] = pose((-0.36 * a, 0, 6))
    d["WingTipL"] = pose((-10, 0, 0))
    d["WingTipR"] = pose((10, 0, 0))
    return d


def gait(p, amp, lean, arm, bob, knee, run=False):
    a = plateau(p, amp)
    shin_l = knee * max(0.0, math.cos(TAU * p))
    shin_r = knee * max(0.0, -math.cos(TAU * p))
    return {
        "ThighL": pose((0, 0, -a)), "ThighR": pose((0, 0, a)),
        "ShinL": pose((0, 0, shin_l)), "ShinR": pose((0, 0, shin_r)),
        "ShoeL": pose((0, 0, a - shin_l)), "ShoeR": pose((0, 0, -a - shin_r)),
        "ArmL": pose((0, 0, s(p, amp * arm))), "ArmR": pose((0, 0, -s(p, amp * arm))),
        "ForearmL": pose((0, 0, -6 - 6 * max(0.0, s(p, 1)))), "ForearmR": pose((0, 0, -6 - 6 * max(0.0, -s(p, 1)))),
        "Pelvis": pose((0, s(p, 4), 0), (0, -bob * abs(math.sin(TAU * p)), 0)),
        "Waist": pose((0, -s(p, 3), lean)),
        "Chest": pose((0, -s(p, 2), lean * 0.5)),
        "Head": pose((0, s(p, 3), -lean * 0.6)),
        # the coat tails swing behind, and fly back at a run
        "WingL": pose((0, 0, (14 if run else 3) + s(p * 2, 3 if run else 1.5))),
        "WingR": pose((0, 0, (14 if run else 3) + s(p * 2, 3 if run else 1.5, 0.2))),
    }


def animate(m):
    def walk(p):
        return {**tentacles(p, 6, 1), **gait(p, 24, 2, 0.35, 0.4, 30)}

    def run(p):
        return {**tentacles(p, 9, 2), **gait(p, 38, 10, 0.6, 0.8, 52, run=True)}

    m.animation("walk", 40, cycle(40, 10, walk))
    m.animation("run", 24, cycle(24, 8, run))

    def idle(p):
        breath = math.sin(TAU * p * 2)
        d = tentacles(p, 5, 1)
        d.update({
            "Chest": pose((0, 0, 0.8 * breath), s=(1, 1 + 0.012 * breath, 1)),
            "Head": pose((s(p, 3, 0.2), s(p, 6, 0.1), -0.6 * breath)),
            "ArmL": pose((0, 0, s(p, 1.5))), "ArmR": pose((0, 0, s(p, 1.5, 0.5))),
            "Finger0L": pose((0, 0, s(p * 3, 6))), "Finger2R": pose((0, 0, s(p * 3, 6, 0.4))),
            "WingL": pose((s(p, 1.5), 0, 0)), "WingR": pose((-s(p, 1.5), 0, 0)),
        })
        return d

    m.animation("idle", 90, cycle(90, 18, idle))

    # The offer: the right hand held out to shake, the left behind his back, a little bow, the head on one side
    def offer(p):
        d = tentacles(p, 4, 1)
        d.update({
            "Waist": pose((0, 0, 6)), "Chest": pose((0, 0, 6)), "Head": pose((8, 6, -8 + s(p, 2))),
            "ArmR": pose((4, 0, -62 + s(p, 2))), "ForearmR": pose((0, 0, -10)), "HandR": pose((-70, 0, 0)),
            "ArmL": pose((-6, 0, 28)), "ForearmL": pose((0, 0, -60)), "HandL": pose((0, 0, -20)),
            "TentL0": pose((-30, 0, -8 + s(p, 4))), "TentR0": pose((30, 0, -8 + s(p, 4, 0.5))),
        })
        return d

    m.animation("offer", 60, cycle(60, 12, offer))

    # Shocked: someone looked him in the eye. He starts back and stands frozen, the tentacles stiff and trembling
    def shocked(p):
        tremble = s(p * 6, 1.2)
        d = {n: pose((tremble * (1 if i % 2 else -1), 0, -18 - 4 * i)) for names in FACE_TENTACLES for i, n in enumerate(names)}
        for side, sign in (("L", 1), ("R", -1)):
            for i, n in enumerate(ARM_TENTACLES[side]):
                d[n] = pose((-sign * 30 + tremble, 0, -20 - 6 * i))
        d.update({
            "Waist": pose((0, 0, -8)), "Chest": pose((0, 0, -8)), "Head": pose((0, 0, -16 + tremble)),
            "ArmL": pose((-18, 0, -40)), "ForearmL": pose((0, 0, -70)), "ArmR": pose((18, 0, -40)), "ForearmR": pose((0, 0, -70)),
            "ThighL": pose((0, 0, 8)), "ShinL": pose((0, 0, 6)), "ShoeL": pose((0, 0, -14)),
            "Pelvis": pose((0, 0, 0), (0.6, -0.3, 0)),
        })
        return d

    m.animation("shocked", 30, cycle(30, 10, shocked))

    # Unveil: the wings open, the arms spread, the blades come out (as the unveiled form appears)
    rest_names = ["WingL", "WingR", "WingTipL", "WingTipR", "WingHindL", "WingHindR", "ArmL", "ArmR", "ForearmL", "ForearmR", "Chest", "Head"] + CLAWS
    def unveil_key(t):
        a = 110 * min(1.0, t * 1.6)
        d = {n: pose() for n in rest_names}
        d.update(tentacles(t * 2, 4 + 20 * t, 1))
        spread_wings(d, a, 0)
        d.update({"ArmL": pose((-60 * t, 0, -30 * t)), "ArmR": pose((60 * t, 0, -30 * t)),
                  "ForearmL": pose((0, 0, -40 * t)), "ForearmR": pose((0, 0, -40 * t)),
                  "Chest": pose((0, 0, -10 * t)), "Head": pose((0, 0, -20 * t))})
        return blades(d, 1 + 2.4 * min(1.0, t * 1.4))

    m.animation("unveil", 60, {f: unveil_key(f / 59) for f in (0, 10, 20, 30, 42, 59)}, end="Hold", stopped="Stop")

    # Attack (the gentleman's, if it ever comes to it): one backhand rake of the right claws
    rest_atk = {n: pose() for n in ("ArmR", "ForearmR", "Chest", "Waist", "Head")}
    m.animation("attack", 30, {
        0: dict(rest_atk),
        9: {**rest_atk, "Chest": pose((0, 14, -6)), "ArmR": pose((30, 0, 40)), "ForearmR": pose((0, 0, -30))},
        14: {**rest_atk, "Chest": pose((0, -20, 10)), "Waist": pose((0, -8, 4)), "ArmR": pose((-10, 0, -110)), "ForearmR": pose((0, 0, -10))},
        20: {**rest_atk, "Chest": pose((0, -10, 6)), "ArmR": pose((-20, 0, -60)), "ForearmR": pose((0, 0, -20))},
        29: dict(rest_atk),
    }, end="Stop")

    hurt_names = ("Chest", "Head", "ArmL", "ArmR", "TentL0", "TentR0")
    m.animation("hurt", 12, {
        0: {n: pose() for n in hurt_names},
        3: {"Chest": pose((0, 8, -12)), "Head": pose((14, 0, -12)), "ArmL": pose((-14, 0, -18)), "ArmR": pose((10, 0, -10)),
            "TentL0": pose((-30, 0, -20)), "TentR0": pose((30, 0, -20))},
        7: {"Chest": pose((0, 4, -6)), "Head": pose((6, 0, -6)), "ArmL": pose((-6, 0, -8)), "ArmR": pose((4, 0, -4)),
            "TentL0": pose((-10, 0, -8)), "TentR0": pose((10, 0, -8))},
        11: {n: pose() for n in hurt_names},
    }, end="Stop")

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): a jolt (the head snaps back, the tentacles and wings
    # flare), the knees go and he drops onto them, slumps, then pitches forward onto his face, rolling a little onto
    # his right side; he rocks once and settles: the left hand by the head with the claws curled, the right arm along
    # his side, the left knee drawn up and out, the right leg trailing with the toe on the floor, the head on its right
    # cheek, the beard spilled on the floor, the tentacle arms limp along it, the wings slumped open on either side of
    # him (fur side up, the hindwings fanned behind). Face down, a hanging part's Z swing is toward or away from the
    # floor and its X swing out along it. Wings and tentacles are soft: they do not hold him up.
    die_soft = [p.name for p in m.parts if p.name.startswith(("Wing", "Tent", "Beard"))]
    die_names = (["Pelvis", "Waist", "Chest", "Head", "ThighL", "ThighR", "ShinL", "ShinR", "ShoeL", "ShoeR",
                  "ArmL", "ArmR", "ForearmL", "ForearmR", "HandL", "HandR"]
                 + [f"Finger{i}{sd}" for sd in "LR" for i in range(3)] + ["ThumbL", "ThumbR"] + die_soft)

    def plant(k, part, at):
        """Moves the body along the floor so `part`'s pivot is over `at` (x, z) (the floor contact stays put)."""
        p = m.by_name[part]
        mats = rig.posed_matrices(m, k)
        w = mats[id(p)] @ np.array([p.pivot[i] - p.frm[i] for i in range(3)] + [1.0])
        root = k["Pelvis"]
        R = rig._rot3(*root["rot"])
        local = R.T @ np.array([at[0] - w[0], 0.0, at[1] - w[2]])
        o = root.get("off", (0, 0, 0))
        k["Pelvis"] = pose(root["rot"], tuple(round(float(o[i] + local[i]), 3) for i in range(3)))
        return k

    def tween(a, b, t):
        """The pose t of the way from keyframe a to keyframe b (a frame passed through, put on the floor)."""
        a, b = full(die_names, a), full(die_names, b)
        return {n: pose(*(tuple(a[n][c][i] + (b[n][c][i] - a[n][c][i]) * t for i in range(3)) for c in ("rot", "off"))) for n in die_names}

    def where(k, part):
        p = m.by_name[part]
        w = rig.posed_matrices(m, k)[id(p)] @ np.array([p.pivot[i] - p.frm[i] for i in range(3)] + [1.0])
        return float(w[0]), float(w[2])

    def curl(c_l, c_r):
        """The fingers curled (the claws with them), each a little differently."""
        d = {f"Finger{i}{sd}": pose((0, 0, c + 8 * ((i + j) % 3))) for j, (sd, c) in enumerate((("L", c_l), ("R", c_r))) for i in range(3)}
        d["ThumbL"], d["ThumbR"] = pose((-c_l * 0.4, 0, c_l * 0.5)), pose((c_r * 0.4, 0, c_r * 0.5))
        return d

    def limp(k_tent, k_beard, flare=0.0):
        """The tentacles: flared stiff (flare) or hanging slack, curling a little more at each segment (k 0..1)."""
        d = {}
        for t, names in enumerate(FACE_TENTACLES):
            for i, n in enumerate(names):
                d[n] = pose((0, 0, -flare * (16 + 6 * i) + k_beard * (6 + 4 * i) * (1 if t % 2 else 0.6)))
        for sd, sign in (("L", 1), ("R", -1)):
            for i, n in enumerate(ARM_TENTACLES[sd]):
                d[n] = pose((-sign * flare * (24 - 4 * i), 0, -flare * (10 + 4 * i) + k_tent * (8 + 5 * i)))
        return d

    # The soft parts lying: as he lands, and as they settle on the floor
    soft_land = {
        "WingL": (-40, 0, -20), "WingTipL": (30, 0, -30), "WingHindL": (17, 0, -18), "WingR": (40, 0, -6),
        "WingTipR": (3, 0, 30), "WingHindR": (-14, 0, -6), "TentL0": (-35.7, 0, -49.6), "TentL1": (-18.9, 0, 4.4),
        "TentL2": (-18.9, 0, 2.6), "TentL3": (-25.2, 0, -8.2), "TentL4": (18.6, 0, -2.2), "TentR0": (21.6, 0, -33.4),
        "TentR1": (8.1, 0, 4.4), "TentR2": (8.1, 0, 46.4), "TentR3": (9.9, 0, 33.2), "TentR4": (16.2, 0, 23.6),
        "Beard0_0": (75.2, 0, -55), "Beard0_1": (7, 0, -16), "Beard0_2": (8.6, 0, -10), "Beard0_3": (9.3, 0, 62),
        "Beard1_0": (65.8, 0, -55), "Beard1_1": (5.2, 0, -16), "Beard1_2": (5.8, 0, -10), "Beard1_3": (14.7, 0, 62),
        "Beard2_0": (56, 0, -55), "Beard2_1": (3.4, 0, -16), "Beard2_2": (2.7, 0, -10), "Beard2_3": (46.9, 0, 62),
        "Beard3_0": (46, 0, -55), "Beard3_1": (1.4, 0, -16), "Beard3_2": (-0.3, 0, -10), "Beard3_3": (52.1, 0, 56),
        "Beard4_0": (36.2, 0, -55), "Beard4_1": (-0.4, 0, -16), "Beard4_2": (-3.4, 0, -10),
        "Beard4_3": (54.3, 0, 44), "Beard5_0": (26.8, 0, -55), "Beard5_1": (-2.2, 0, -16),
        "Beard5_2": (-6.2, 0, -10), "Beard5_3": (50.7, 0, 29), "Beard6_0": (81.4, 0, -55), "Beard6_1": (8.2, 0, -16),
        "Beard6_2": (10.6, 0, -10), "Beard6_3": (11.7, 0, 26), "Beard7_0": (20.6, 0, -55),
        "Beard7_1": (-3.4, 0, -16), "Beard7_2": (-8.2, 0, -10), "Beard7_3": (48.3, 0, 26)}
    soft_held = {
        "WingL": (-51, 0, -24), "WingTipL": (-6, 0, 12), "WingHindL": (27, 0, 0), "WingR": (51, 0, -12),
        "WingTipR": (3, 0, 12), "WingHindR": (-30, 0, -3), "TentL0": (-51, 0, -66), "TentL1": (-27, 0, 24),
        "TentL2": (-27, 0, 21), "TentL3": (-36, 0, 3), "TentL4": (-42, 0, 3), "TentR0": (72, 0, -39),
        "TentR1": (27, 0, 24), "TentR2": (27, 0, 9), "TentR3": (33, 0, 12), "TentR4": (54, 0, -9),
        "Beard0_0": (125.3, 0, -45), "Beard0_1": (20.8, 0, -9), "Beard0_2": (14.4, 0, 0), "Beard0_3": (15.5, 0, 12),
        "Beard1_0": (109.7, 0, -45), "Beard1_1": (8.8, 0, -27), "Beard1_2": (9.6, 0, 0), "Beard1_3": (9.5, 0, 12),
        "Beard2_0": (93.3, 0, -45), "Beard2_1": (5.6, 0, -18), "Beard2_2": (4.6, 0, -15), "Beard2_3": (3.2, 0, 12),
        "Beard3_0": (76.7, 0, -45), "Beard3_1": (2.4, 0, -6), "Beard3_2": (-0.6, 0, -15), "Beard3_3": (-3.2, 0, 0),
        "Beard4_0": (60.3, 0, -45), "Beard4_1": (-0.8, 0, -6), "Beard4_2": (-5.6, 0, 0), "Beard4_3": (-9.5, 0, 33),
        "Beard5_0": (44.7, 0, -45), "Beard5_1": (-3.8, 0, -6), "Beard5_2": (-10.4, 0, 0), "Beard5_3": (44.5, 0, 36),
        "Beard6_0": (135.7, 0, -45), "Beard6_1": (22.8, 0, -6), "Beard6_2": (17.6, 0, 0), "Beard6_3": (-25.5, 0, 12),
        "Beard7_0": (34.3, 0, -45), "Beard7_1": (-5.8, 0, -6), "Beard7_2": (-13.6, 0, 0), "Beard7_3": (40.5, 0, 36)}

    def lying(roll, slack):
        """Face down, rolled `roll` onto his right side, from the sprawl he lands in (slack 0) to the pose he rests in
        (slack 1)."""
        def at(a, b):
            return tuple(a[i] + (b[i] - a[i]) * slack for i in range(3))
        d = {
            "Pelvis": pose((roll, 0, at((0, 0, 90), (0, 0, 88))[2])), "Waist": pose(at((0, 0, -4), (2, -3, -3))), "Chest": pose(at((0, 0, -6), (3, -4, -4))),
            "Head": pose(at((0, 60, -6), (0, 80, 0))),
            "ArmL": pose(at((-100, 0, -30), (-111, 0, -9))), "ForearmL": pose(at((-70, 0, 0), (-93, 0, 3))), "HandL": pose(at((0, 0, -10), (-6, 0, -18))),
            "ArmR": pose(at((8, 0, 14), (9, 0, 6))), "ForearmR": pose(at((6, 0, 0), (12, 0, 9))), "HandR": pose(at((0, 0, 0), (0, 20, 10))),
            "ThighL": pose(at((-50, 0, -10), (-72, 0, -18))), "ShinL": pose(at((60, 0, 0), (93, 0, 3))), "ShoeL": pose(at((-50, 0, 60), (-78, 0, 84))),
            "ThighR": pose(at((4, 0, 0), (6, 0, 0))), "ShinR": pose(at((0, 0, 20), (3, 0, 9))), "ShoeR": pose(at((30, 0, 50), (42, 0, 60))),
        }
        d.update({n: pose(at(soft_land[n], r)) for n, r in soft_held.items()})
        d.update(curl(at((10, 0, 0), (40, 0, 0))[0], at((6, 0, 0), (34, 0, 0))[0]))
        return d

    keys = {
        0: {},
        # the jolt: the head snaps back, the arms jerk out, the tentacles and the wings flare
        3: dict({"Waist": pose((0, 0, -6)), "Chest": pose((0, 6, -8)), "Head": pose((10, 0, -16)),
                 "ArmL": pose((-16, 0, -14)), "ArmR": pose((12, 0, -8)), "ForearmL": pose((0, 0, -24)), "ForearmR": pose((0, 0, -18)),
                 "WingL": pose((-12, 0, 6)), "WingR": pose((12, 0, 6))}, **limp(0, 0, flare=1.0), **curl(-10, -6)),
        # the knees go, the feet where they stood; he slumps
        8: dict({"Pelvis": pose((2, 0, 8)), "ThighL": pose((0, 0, -58)), "ThighR": pose((0, 0, -50)),
                 "ShinL": pose((0, 0, 85)), "ShinR": pose((0, 0, 78)), "ShoeL": pose((0, 0, -35)), "ShoeR": pose((0, 0, -36)),
                 "Waist": pose((0, 0, 10)), "Chest": pose((0, 4, 8)), "Head": pose((6, 0, 16)),
                 "ArmL": pose((-4, 0, -8)), "ArmR": pose((6, 0, -6)), "ForearmL": pose((0, 0, -10)), "ForearmR": pose((0, 0, -8)),
                 "WingL": pose((-4, 0, 2)), "WingR": pose((4, 0, 2))}, **limp(0.3, 0.3), **curl(4, 2)),
        # on his knees, swaying, the head hanging
        13: dict({"Pelvis": pose((3, 0, 10)), "ThighL": pose((0, 0, -22)), "ThighR": pose((0, 0, -16)),
                  "ShinL": pose((0, 0, 125)), "ShinR": pose((0, 0, 121)), "ShoeL": pose((0, 0, 0)), "ShoeR": pose((0, 0, 4)),
                  "Waist": pose((0, -4, 16)), "Chest": pose((2, 6, 14)), "Head": pose((8, 10, 26)),
                  "ArmL": pose((-10, 0, 14)), "ArmR": pose((8, 0, 6)), "ForearmL": pose((0, 0, -34)), "ForearmR": pose((0, 0, -22)),
                  "WingL": pose((-8, 0, 0)), "WingR": pose((8, 0, 0))}, **limp(0.5, 0.5), **curl(10, 6)),
        # tipping forward over the knees, the left hand going out, the wings sliding off his back
        18: dict({"Pelvis": pose((-4, 0, 40)), "ThighL": pose((0, 0, -22)), "ThighR": pose((0, 0, -16)),
                  "ShinL": pose((0, 0, 95)), "ShinR": pose((0, 0, 91)), "ShoeL": pose((0, 0, -10)), "ShoeR": pose((0, 0, -6)),
                  "Waist": pose((0, -2, 8)), "Chest": pose((0, 4, 6)), "Head": pose((4, 24, 8)),
                  "ArmL": pose((-30, 0, -60)), "ArmR": pose((10, 0, 10)), "ForearmL": pose((-20, 0, -20)), "ForearmR": pose((0, 0, -10)),
                  "WingL": pose((-20, 0, -6)), "WingR": pose((20, 0, -6))}, **limp(0.6, 0.6), **curl(6, 10)),
        # falling, the knees sliding back
        23: dict({"Pelvis": pose((-10, 0, 68)), "ThighL": pose((0, 0, -28)), "ThighR": pose((0, 0, -22)),
                  "ShinL": pose((0, 0, 75)), "ShinR": pose((0, 0, 71)), "ShoeL": pose((0, 0, -10)), "ShoeR": pose((0, 0, -6)),
                  "Waist": pose((0, -2, 0)), "Chest": pose((0, 2, -2)), "Head": pose((2, 44, 0)),
                  "ArmL": pose((-75, 0, -70)), "ArmR": pose((10, 0, 20)), "ForearmL": pose((-55, 0, -5)), "ForearmR": pose((0, 0, -10)),
                  "WingL": pose((-34, 0, -14)), "WingR": pose((34, 0, -10))}, **limp(0.7, 0.7), **curl(8, 12)),
        # down on his face, a little past onto his right side
        26: lying(-22, 0.0),
        # rocks back
        30: lying(-8, 0.5),
        # settling: the wings and tentacles slump, the head sinks onto its cheek
        39: lying(-14, 1.0),
    }
    rest_feet = [where({}, "ShoeL"), where({}, "ShoeR")]
    for f in (8, 13):
        k = full(die_names, keys[f])
        feet = [where(k, "ShoeL"), where(k, "ShoeR")]
        plant(k, "Pelvis", (where(k, "Pelvis")[0] + sum(r[0] - q[0] for r, q in zip(rest_feet, feet)) / 2,
                            where(k, "Pelvis")[1] + sum(r[1] - q[1] for r, q in zip(rest_feet, feet)) / 2))
        keys[f] = k
    knees = where(keys[13], "ShinL")
    for f in (18, 23):
        k = full(die_names, keys[f])
        keys[f] = plant(k, "ShinL", knees)
    hips = where(keys[23], "Pelvis")
    for f in (26, 30, 39):
        keys[f] = plant(full(die_names, keys[f]), "Pelvis", (hips[0] - 1.0, hips[1]))
    keys[5] = tween(keys[3], keys[8], 0.45)
    keys[9] = tween(keys[8], keys[13], 0.33)
    keys[11] = tween(keys[8], keys[13], 0.6)
    death(m, 40, die_names, dict(sorted(keys.items())), standing=(3,), soft=die_soft)

    # ---- The unveiled form's own (claws as blades, wings half open, everything thrashing) ----
    def fury(p):
        d = tentacles(p, 7, 2, fury=True)
        spread_wings(d, 45, s(p, 8))
        d.update({"Waist": pose((0, 0, 8)), "Chest": pose((0, s(p, 4), 10)), "Head": pose((s(p * 2, 4), s(p, 8), -12)),
                  "ArmL": pose((-24, 0, -30 + s(p, 4))), "ArmR": pose((24, 0, -30 + s(p, 4, 0.5))),
                  "ForearmL": pose((0, 0, -30)), "ForearmR": pose((0, 0, -30))})
        return blades(d)

    m.animation("fury", 40, cycle(40, 10, fury))

    def stalk(p):
        d = {**tentacles(p, 6, 2, fury=True), **gait(p, 26, 14, 0.2, 0.5, 36)}
        spread_wings(d, 40, s(p * 2, 6))
        d.update({"ArmL": pose((-20, 0, -40 + s(p, 8))), "ArmR": pose((20, 0, -40 - s(p, 8))),
                  "ForearmL": pose((0, 0, -26)), "ForearmR": pose((0, 0, -26)), "Head": pose((0, s(p, 4), -16))})
        return blades(d)

    def charge(p):
        d = {**tentacles(p, 8, 3, fury=True), **gait(p, 42, 22, 0.3, 1.0, 58, run=True)}
        spread_wings(d, 75, s(p * 2, 12))
        d.update({"ArmL": pose((-30, 0, -70 + s(p, 14))), "ArmR": pose((30, 0, -70 - s(p, 14))),
                  "ForearmL": pose((0, 0, -20)), "ForearmR": pose((0, 0, -20)), "Head": pose((0, 0, -24))})
        return blades(d)

    m.animation("stalk", 32, cycle(32, 8, stalk))
    m.animation("charge", 20, cycle(20, 10, charge))

    # Rend: both blades raised and brought down across, the tentacle arms lashing in after them
    def rend_key(t):
        d = tentacles(t, 10, 2, fury=True)
        spread_wings(d, 70, 0)
        up, down = math.sin(math.pi * min(1.0, t / 0.45)) if t < 0.45 else 1.0, max(0.0, (t - 0.4) / 0.25)
        down = min(1.0, down)
        back = max(0.0, (t - 0.75) / 0.25)
        arm = -150 * up * (1 - down) + (-40) * down * (1 - back) - 30 * back
        d.update({"ArmL": pose((-30 + 20 * down, 0, arm)), "ArmR": pose((30 - 20 * down, 0, arm)),
                  "ForearmL": pose((0, 0, -30 * (1 - down))), "ForearmR": pose((0, 0, -30 * (1 - down))),
                  "Chest": pose((0, 0, -10 * up * (1 - down) + 24 * down * (1 - back))), "Waist": pose((0, 0, 10 * down * (1 - back))),
                  "Head": pose((0, 0, -20 + 10 * down)),
                  "TentL0": pose((-20, 0, -60 * down * (1 - back))), "TentR0": pose((20, 0, -60 * down * (1 - back)))})
        return blades(d)

    m.animation("rend", 26, {f: rend_key(f / 25) for f in (0, 5, 9, 11, 13, 16, 20, 25)}, end="Stop")


# ---------------- Entity types ----------------

def entity_types():
    from gen_entities import anim, common_client, menace_task, server, sync_harvestable, LOOKAROUND
    sounds = {"hurt": "backrooms:entity/beast/hurt", "death": "backrooms:entity/beast/death"}

    # The gentleman: put down by BeastSystem (src/Entities/BeastSystem.cs) for whoever he has chosen, standing a few
    # steps off. He makes his offer (AiTaskBeast): shake his hand, look him in the eye, or refuse him (strike him,
    # walk off, or let the offer lapse), and he unveils. Nothing hurts him.
    gentleman_anims = [
        anim("hurt", "hurt", 1.0, weight=10, blendMode="AddAverage"),
        anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
        anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage", easeOutSpeed=4),
        anim("walk", "walk"), anim("run", "run"), anim("attack", "attack", weight=10),
        anim("offer", "offer", weight=5), anim("shocked", "shocked", weight=10), anim("unveil", "unveil", weight=10),
    ]
    task = {"code": "backrooms-beast", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
            "walkSpeed": 0.006, "offerSeconds": 24, "stareSeconds": 5, "shockedSeconds": 8, "refuseDistance": 13,
            "lostSightSeconds": 4}
    gentleman = {
        "code": "beast",
        "class": "BackroomsBeast",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": 90,
        "canClimb": True,
        "hitboxSize": {"x": 0.7, "y": 1.95},
        "deadHitboxSize": {"x": 0.7, "y": 0.6},
        "eyeHeight": 1.6,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-beast"},
        "client": common_client("backrooms:entity/beast", {"base": "backrooms:entity/beast"}, gentleman_anims, 1.0),
        "server": server(60, [task, LOOKAROUND], None, menace={"immortal": True, "unmoved": True, "glimpseSeconds": 4,
                                                          "stalkSeconds": 90, "huntSeconds": 90}, decay=None),
        "sounds": sounds,
    }

    # Unveiled: half as big again, blades for claws, the moth's compound eyes; a hunter on the common menace task.
    # A little short of a sprint (0.05): a runner who keeps going pulls away, and a hunt that draws no blood for 20
    # seconds is given up. Its blows are the worst in the hotel. It can be brought down
    # (BeastSystem: it dissolves, and drops Level 5's key), though not for long.
    unveiled_anims = [
        anim("hurt", "hurt", 1.0, weight=10, blendMode="AddAverage"),
        anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
        anim("idle", "fury", triggeredBy={"defaultAnim": True}, blendMode="AddAverage", easeOutSpeed=4),
        anim("walk", "stalk", 1.2), anim("run", "charge", 1.2), anim("attack", "rend", weight=10),
        anim("unveil", "unveil", weight=10),
    ]
    hunt = menace_task(walkSpeed=0.024, runSpeed=0.047, stalkMin=6, stalkMax=10, glimpseFleeDistance=8,
                       damage=7, damageTier=3, damageType="SlashingAttack", knockback=0.6, attackRange=1.7,
                       attackDurationMs=870, damageAtMs=420, attackCooldownMs=1700, attackAnimation="attack",
                       emergeAnimation="unveil", emergeMs=2000, huntSound="backrooms:entity/beast/roar",
                       voices=["backrooms:entity/beast/voice", "backrooms:entity/beast/clang"], soundRange=40,
                       # What he perceives (README section 6.2, the shared model): he smells fear (the unsteady, within 24),
                       # sees 30 lit, 20 dim and 10 in the dark, hears 20; a runner who hides in a dark room is lost for
                       # a while, and he searches where he last had them
                       senses=dict(sightLit=30, sightDim=20, sightDark=10, hearing=20, fearSense=24, memorySeconds=10),
                       investigateSeconds=8, searchSeconds=14)
    unveiled = {
        "code": "beast-unveiled",
        "class": "BackroomsBeast",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": 160,
        "canClimb": True,
        "hitboxSize": {"x": 0.9, "y": 1.95},
        "deadHitboxSize": {"x": 0.9, "y": 0.6},
        "eyeHeight": 2.4,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-beast"},
        "client": common_client("backrooms:entity/beast", {"base": "backrooms:entity/beast-unveiled"}, unveiled_anims, 1.4),
        "server": server(120, [hunt, LOOKAROUND], None, menace={"stalkSeconds": 20, "huntSeconds": 120}, decay=None),
        "sounds": sounds,
    }
    for entity in (gentleman, unveiled):
        write_entity(sync_harvestable(entity))


def write_entity(data):
    path = os.path.join(ASSETS, "entities", data["code"] + ".json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent="\t") + "\n")
    print("wrote", os.path.relpath(path, os.path.join(ASSETS, "..", "..")))


# ---------------- Names and lines ----------------

LANG = {
    "item-creature-beast": "The Beast of Level 5",
    "item-creature-beast-unveiled": "The Beast of Level 5 (unveiled)",
    "prefixandcreature-beast": "the Beast of Level 5",
    "prefixandcreature-beast-unveiled": "the Beast of Level 5",
    "deadcreature-beast": "Taken by the Beast of Level 5",
    "beast-help-shake": "Shake his hand",
    "beast-greet-1": "A gentleman in a black fur suit stands where nobody stood a moment ago. \"Ah, there you are. Let us strike a deal, you and I.\"",
    "beast-greet-2": "Out of the flames steps a gentleman in a black fur suit, and bows. \"You need never be afraid again. Shake my hand.\"",
    "beast-greet-3": "A tall figure in a furred black suit holds out a clawed hand. \"Welcome to my hotel. A small favour, and all your fear is gone.\"",
    "beast-collect": "\"Time is up.\" A gentleman in a black fur suit is waiting for you. \"I have come for what is mine.\"",
    "beast-doubt": "\"Why are you doubting me?\" His suit opens like wings.",
    "beast-deal": "You shake his hand. Warmth floods through you: you are whole, fed, and not afraid. \"Splendid. I shall come for what is mine in three days.\"",
    "beast-shocked": "You hold his gaze. He stands as if struck, and for a few seconds nothing in the hotel moves. Run.",
    "beast-free": "Your soul is your own again.",
    "beast-taken": "The Beast of Level 5 has collected what you owed him.",
    "beast-reprieve": "You got away. He will come again for what is his.",
}


def merge_lang():
    """Adds the names and lines to lang/en.json without disturbing its layout (as gen_entities.merge_lang)."""
    tab, nl = "\t", "\n"
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_lines = []
    for key, value in LANG.items():
        line_ = tab + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + tab + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda mt: line_ + mt.group(1), text, count=1)
        else:
            new_lines.append(line_)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + nl + nl + ("," + nl).join(new_lines) + nl + "}" + nl
    with open(path, "w", encoding="utf-8", newline=nl) as f:
        f.write(text)
    json.loads(text)


# ---------------- Sounds (with gen_entity_sounds' synthesis kit) ----------------

def sounds():
    import gen_entity_sounds as ges
    from gen_entity_sounds import band, place, reverb, seconds, thud, vowel
    rate = ges.RATE
    old = ges.OUT
    ges.OUT = os.path.join(old, "beast")
    try:
        # A deep drum somewhere far off in the hotel: two slow strokes, felt more than heard
        rng = np.random.default_rng(1801)
        out = np.zeros(int(3.2 * rate))
        for at, f0, g in ((0.05, 46, 1.0), (1.15, 42, 0.8)):
            t = seconds(1.6)
            body = np.sin(2 * np.pi * f0 * t * (1 - 0.18 * t)) * np.exp(-t * 3.2) + 0.4 * np.sin(2 * np.pi * f0 * 2.02 * t) * np.exp(-t * 6)
            skin_ = band(rng.normal(size=len(t)), 60, 400) * np.exp(-t * 14) * 0.5
            place(out, (body + skin_) * g, at)
        ges.write("drum", reverb(band(out, 25, 900), decay=0.9), 0.85)

        # Scraping and clanging coming closer: metal dragged along pipes, struck now and then, louder at the end
        rng = np.random.default_rng(1802)
        n = int(3.6 * rate)
        t = np.arange(n) / rate
        scrape = band(rng.normal(size=n), 900, 5200) * (0.35 + 0.65 * np.abs(np.sin(2 * np.pi * 2.1 * t))) * (0.25 + 0.75 * t / t[-1])
        out = scrape * 0.6
        for at in (0.4, 1.1, 1.6, 2.2, 2.6, 3.0, 3.3):
            tt = seconds(0.9)
            ring = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, d in ((523, 5), (1187, 7), (1733, 9), (2410, 12)))
            place(out, ring * (0.3 + 0.7 * at / 3.3) * rng.uniform(0.6, 1.0), at)
        ges.write("clang", reverb(out, decay=0.6), 0.6)

        # A column of flame: a roaring rush that swells and dies
        rng = np.random.default_rng(1803)
        n = int(1.8 * rate)
        t = np.arange(n) / rate
        env = np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.25) * 2.6)
        roar = band(rng.normal(size=n), 80, 2600) * env
        crackle = (rng.random(n) < 0.002) * rng.normal(size=n) * 4 * env
        ges.write("flame", roar + band(crackle, 1500, 8000), 0.8)

        # His voice: a low, pleasant murmur, words almost made out, a chuckle at the end
        rng = np.random.default_rng(1804)
        n = int(2.6 * rate)
        out = np.zeros(n)
        at = 0.05
        vowels = [((600, 110, 1), (1000, 140, 0.7)), ((420, 90, 1), (1900, 200, 0.5)), ((500, 90, 1), (800, 110, 0.7)), ((330, 80, 1), (2200, 240, 0.4))]
        while at < 2.0:
            length = rng.uniform(0.12, 0.3)
            tt = seconds(length)
            f0 = 82 + 10 * np.sin(2 * np.pi * rng.uniform(0.5, 1.5) * tt) + rng.uniform(-6, 6)
            v = vowel(tt, f0, vowels[rng.integers(len(vowels))], 0.1, rng) * np.sin(np.pi * tt / tt[-1]) ** 0.6
            place(out, v, at)
            at += length + rng.uniform(0.02, 0.12)
        for k in range(3):
            tt = seconds(0.1)
            place(out, vowel(tt, 96 - 4 * k + 0 * tt, vowels[0], 0.3, rng) * np.sin(np.pi * tt / tt[-1]), 2.05 + 0.15 * k)
        ges.write("voice", reverb(out, decay=0.5), 0.6)

        # Unveiling: a deep, tearing roar, a voice and a storm of wings in one
        rng = np.random.default_rng(1805)
        n = int(2.4 * rate)
        t = np.arange(n) / rate
        f0 = 58 + 30 * np.minimum(1, t / 0.5) - 12 * np.maximum(0, t - 1.4)
        roar = vowel(t, f0, ((380, 160, 1), (900, 240, 0.8), (2400, 400, 0.3)), 0.6, rng)
        env = np.minimum(1, t / 0.15) * np.exp(-np.maximum(0, t - 1.5) * 3)
        wings = band(rng.normal(size=n), 60, 700) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t) ** 2)
        ges.write("roar", (np.tanh(2.2 * roar) + 0.5 * wings) * env, 0.9)

        # Struck: a hiss and a wet click; dying: a long sigh that goes down into a rattle
        rng = np.random.default_rng(1806)
        t = seconds(0.5)
        hiss = band(rng.normal(size=len(t)), 1200, 7000) * np.exp(-t * 6)
        ges.write("hurt", hiss + 0.6 * thud(0.5, 140, rng, 0.8), 0.7)
        t = seconds(2.2)
        f0 = 90 - 40 * t / t[-1]
        sigh = vowel(t, f0, ((500, 150, 1), (1100, 200, 0.5)), 0.5, rng) * np.exp(-t * 0.9)
        rattle = band(rng.normal(size=len(t)), 200, 1500) * (np.sin(2 * np.pi * 9 * t) > 0.6) * np.minimum(1, t / 1.2)
        ges.write("death", reverb(sigh + 0.4 * rattle), 0.75)
    finally:
        ges.OUT = old


def build_model():
    beast("gentleman").save()
    m = beast("unveiled")
    width, height = m._pack()
    m._paint(width, height).save(os.path.join(ASSETS, "textures", "entity", "beast-unveiled.png"))
    print(f"wrote beast-unveiled texture {width}x{height}")
    LOOK["eyes"] = "gentleman"


def main():
    import sys
    parts = set(sys.argv[1:]) or {"model", "entities", "lang", "sounds"}
    if "model" in parts:
        build_model()
    if "entities" in parts:
        entity_types()
    if "lang" in parts:
        merge_lang()
    if "sounds" in parts:
        sounds()


if __name__ == "__main__":
    main()
