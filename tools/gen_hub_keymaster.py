"""The Keymaster (for tools/gen_hub.py): the Hub's overseer, a new model built with tools/rig.py.

Canon (Wikidot, The Hub's Discovery Log; his own page is trimmed): he "slowly descends to the ground, quietly touching
down with a faint jingling of his key ring", "looms tall", "spins on his heel and sharply turns around, his cloak
swooping with him as he quickly strides down the corridor", points out doors and "hastily shoves" wanderers through.
Level Keys (object-2) are of every period and material, mostly metal, some plastic or stone.

hub-plan.md 4.7: too tall and inhuman (43 px, 2.7 blocks), a long narrow deep-hooded cloak, charcoal with a faint
violet sheen; in the hood's shadow a gaunt pale-grey lower face and two faint pale eyes; long thin grey hands with long
fingers; at the hip a big iron ring of fifteen keys, each one modelled, on a bone of its own so it swings.

The build: a solid robe (waist, skirt, hem) under swinging outer panels (front, sides) and a long cape from the
shoulders (the swoop); a shoulder mantle with a keyhole clasp; a real cowl (shell, crown, brim, pointed peak, drape)
with the face set back in it; long arms in bell sleeves, hands with two-jointed fingers; pointed boots under the hem
(canon has him touch down, stride and spin on his heel); the key ring at the front-left hip, turned 45 degrees so it
reads from the front and clears the arm, its fifteen keys a mixed lot (iron and brass skeleton keys, modern keys, one
of stone, one of red plastic).

Animations: idle (standing: a slow breath, the cloak and keys stirring, the fingers flexing), descend (feet dangling,
the cloak billowing up, keys jingling; the code moves him down), point (one long arm out, one finger), shove (both arms
forward hard, palms out), turn (a spin on the heel, the cape swooping), jingle (he lifts the ring and shakes it),
dismiss (a curt backhand flick: "Yes yes, indeed, goodbye!"), stride (a quick walk under the robe, for an escort).

Conventions (rig.py): the model faces -X, its left is +Z, up is +Y; a hanging part swings backward with +Z.
"""
import math
import os

from rig import Model, clamp, fill, mix, pose, rect, shade, vlines
from gen_hub_kit import ASSETS, write_json
from gen_models import cycle, full, line, ragged, s, texel

CLOAK = (33, 32, 38)
ROBE = (24, 23, 28)
INNER = (40, 31, 50)   # the robe under the open cloak: a deep violet
SHEEN = (54, 42, 74)
FOLD = (13, 12, 16)
HOOD_IN = (7, 6, 9)
TRIM = (92, 88, 100)
FACE = (152, 152, 147)
FACE_DARK = (88, 88, 90)
HAND = (146, 146, 142)
NAIL = (52, 50, 54)
IRON = (84, 84, 88)
BRASS = (168, 134, 82)
RUST = (112, 70, 44)
STONE = (146, 142, 132)
PLASTIC = (178, 46, 50)
STEEL = (150, 152, 156)
LEATHER = (52, 38, 28)
BOOT = (30, 25, 25)
EYE = (214, 230, 236)

SIDES = ("north", "south", "east", "west")
LIGHT = {"up": 1.08, "down": 0.7, "north": 0.94, "south": 0.94, "east": 0.86, "west": 1.0}


# ---------------- Painters ----------------

def cloth(ctx, base=CLOAK, period=5, top=1.06, bottom=0.8, sheen=0.4, hem=False):
    period = period + ctx.rng.choice((0, 0, 1, 2)) if ctx.w > 6 else period
    """Heavy cloth: broad wavering folds (dark valleys, a faint violet sheen on the ridges), darker toward the hem."""
    if ctx.face not in SIDES:
        fill(ctx, base, 0.04)
        return
    px = ctx.img.load()
    k = LIGHT[ctx.face]
    off = ctx.rng.uniform(0, period)
    wob = ctx.rng.uniform(0, math.tau)
    for yy in range(ctx.h):
        g = top + (bottom - top) * yy / max(1, ctx.h - 1)
        for xx in range(ctx.w):
            ph = ((xx + off + 0.6 * math.sin(yy * 0.23 + wob)) % period) / period
            v = 0.5 - 0.5 * math.cos(ph * math.tau)  # 0 in a valley, 1 on a ridge
            c = mix(FOLD, base, 0.5 + 0.5 * v)
            if v > 0.85 and (xx + int(off)) % (2 * period) < period:
                c = mix(c, SHEEN, sheen * (v - 0.85) / 0.15)
            m = 1 + 0.05 * (ctx.rng.random() - 0.5) * 2
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(ch * k * g * m for ch in c)) + (255,)
    if hem:
        # Dust and wear along the bottom edge, then a frayed edge
        for xx in range(ctx.w):
            texel(ctx, xx, -1, (70, 66, 64), 0.35)
            texel(ctx, xx, -2, (60, 56, 56), 0.15)
        ragged(ctx, 2)


def robe(ctx):
    cloth(ctx, ROBE, period=4, sheen=0.3)


def robe_hem(ctx):
    cloth(ctx, ROBE, period=4, sheen=0.3, top=0.9, bottom=0.72)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, -1, (66, 62, 60), 0.4)


def panel(ctx):
    cloth(ctx, CLOAK, hem=True)


def front_panel(ctx):
    cloth(ctx, INNER, period=4, sheen=0.5, hem=True)


def inner(ctx):
    cloth(ctx, INNER if ctx.face == "west" else ROBE, period=4, sheen=0.5)


def side_panel(ctx):
    cloth(ctx, CLOAK, hem=True)
    if ctx.face == "west":
        # The cloak's front edge, hemmed in dull pewter
        for yy in range(ctx.h - 2):
            for xx in range(ctx.w):
                texel(ctx, xx, yy, TRIM, 0.45)


def cape(ctx):
    cloth(ctx, CLOAK, period=6, top=1.0, bottom=0.84)


def cape_low(ctx):
    cloth(ctx, CLOAK, period=6, top=0.84, bottom=0.7, hem=True)


def mantle(ctx):
    cloth(ctx, CLOAK, period=4, top=1.12, bottom=0.9, sheen=0.55)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, -1, TRIM, 0.35)  # a dull pewter edge
        ragged(ctx, 1)


def keyhole(ctx, u, v, scale=1):
    """A tiny pewter plate with a keyhole, centred at (u, v)."""
    cx, cy = int(u * ctx.w), int(v * ctx.h)
    for dx in (-1, 0, 1):
        for dy in range(0, 3):
            texel(ctx, cx + dx, cy + dy, TRIM)
    texel(ctx, cx, cy, HOOD_IN)
    texel(ctx, cx, cy + 1, HOOD_IN)


def clasp(ctx):
    fill(ctx, TRIM, 0.08)
    if ctx.face == "west":
        rect(ctx, 0, 0, 1, 1, shade(TRIM, 0.8))
        rect(ctx, 0.17, 0.17, 0.83, 0.83, shade(TRIM, 1.15))
        rect(ctx, 0.4, 0.25, 0.6, 0.5, HOOD_IN)
        rect(ctx, 0.45, 0.45, 0.55, 0.75, HOOD_IN)


def hood(ctx):
    cloth(ctx, CLOAK, period=4, top=1.1, bottom=0.92, sheen=0.5)
    if ctx.face == "west":
        fill(ctx, HOOD_IN, 0.03, face_shade=False)  # the opening: deep shadow


def brim(ctx):
    cloth(ctx, CLOAK, period=3, top=1.1, bottom=1.0, sheen=0.6)
    if ctx.face == "west":
        # The hood's edge: a thin dull trim
        for xx in range(ctx.w):
            texel(ctx, xx, 0, TRIM, 0.3)
    if ctx.face == "down":
        fill(ctx, shade(HOOD_IN, 2), 0.03, face_shade=False)


def hood_in(ctx):
    fill(ctx, HOOD_IN, 0.02, face_shade=False)


def face(ctx):
    fill(ctx, HOOD_IN, 0.02, face_shade=False)
    if ctx.face == "west":
        # Only the jaw shows, fading up into the hood's shadow: narrowing to a pointed chin, cheekbones catching a
        # little light, a thin hard mouth
        for yy in range(ctx.h):
            v = (yy + 0.5) / ctx.h
            if v < 0.5:
                continue
            t = min(1.0, (v - 0.5) / 0.4)
            half = 0.36 - 0.2 * max(0.0, (v - 0.7) / 0.3)
            for xx in range(ctx.w):
                u = (xx + 0.5) / ctx.w
                if abs(u - 0.5) <= half:
                    edge = abs(u - 0.5) > half - 0.12
                    c = mix(HOOD_IN, mix(FACE_DARK, FACE, 0.25), t * (0.55 if edge else 0.9))
                    texel(ctx, xx, yy, c)
        texel(ctx, 1, int(ctx.h * 0.55), mix(FACE_DARK, FACE, 0.3))       # cheekbones
        texel(ctx, ctx.w - 2, int(ctx.h * 0.55), mix(FACE_DARK, FACE, 0.3))
        for xx in range(int(ctx.w * 0.35), int(ctx.w * 0.65) + 1):
            texel(ctx, xx, int(ctx.h * 0.84), (26, 22, 24))                 # the mouth
        texel(ctx, ctx.w // 2 - 1, -1, mix(FACE_DARK, FACE, 0.5))           # the chin
        texel(ctx, ctx.w // 2, -1, mix(FACE_DARK, FACE, 0.5))


def face_part(ctx):
    fill(ctx, shade(FACE_DARK, 0.5) if ctx.face != "west" else shade(FACE_DARK, 0.75), 0.04, face_shade=False)
    if ctx.face == "down":
        fill(ctx, mix(FACE_DARK, FACE, 0.6), 0.04, face_shade=False)


def eye(ctx):
    fill(ctx, EYE, 0.03, face_shade=False)


def sleeve(ctx):
    cloth(ctx, CLOAK, period=3, top=1.05, bottom=0.9)


def cuff(ctx):
    cloth(ctx, CLOAK, period=3, top=1.1, bottom=0.85, sheen=0.6)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, 0, TRIM, 0.4)
            texel(ctx, xx, 1, TRIM, 0.2)
        ragged(ctx, 2)
    if ctx.face == "down":
        fill(ctx, HOOD_IN, 0.02, face_shade=False)  # the dark inside of the bell


def hand(ctx):
    fill(ctx, HAND, 0.06)
    if ctx.face in SIDES and ctx.h > 3:
        for t in (0.3, 0.6):
            line(ctx, t, 0.15, t, 0.85, shade(HAND, 0.8), 0.5)  # tendons
        for xx in range(ctx.w):
            texel(ctx, xx, -1, shade(HAND, 0.78), 0.6)  # the knuckles
    if ctx.face == "up":
        fill(ctx, shade(HAND, 0.6), 0.04)


def finger(ctx):
    fill(ctx, HAND, 0.05)
    if ctx.face in SIDES:
        texel(ctx, 0, -1, shade(HAND, 0.75))
        texel(ctx, -1, -1, shade(HAND, 0.75))


def fingertip(ctx):
    fill(ctx, shade(HAND, 0.96), 0.05)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, -1, NAIL)
            texel(ctx, xx, -2, NAIL, 0.5)
    if ctx.face == "down":
        fill(ctx, NAIL, 0.05)


def boot(ctx):
    fill(ctx, BOOT, 0.08)
    if ctx.face == "up":
        fill(ctx, shade(BOOT, 1.4), 0.08)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, -1, (18, 15, 15))  # the sole


def belt(ctx):
    fill(ctx, LEATHER, 0.08)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, 0, shade(LEATHER, 1.3), 0.6)
            texel(ctx, xx, -1, shade(LEATHER, 0.6), 0.6)


def buckle(ctx):
    fill(ctx, IRON, 0.1)
    if ctx.face == "west":
        rect(ctx, 0.25, 0.25, 0.75, 0.75, LEATHER)
        rect(ctx, 0.45, 0.2, 0.55, 0.8, shade(IRON, 1.3))


def metal(colour, hole=False):
    def paint(ctx):
        fill(ctx, colour, 0.1)
        if ctx.face in SIDES and ctx.w > 1:
            texel(ctx, 0, 0, shade(colour, 1.4))            # a glint
            for yy in range(ctx.h):
                texel(ctx, -1, yy, shade(colour, 0.7), 0.6)  # the shadowed edge
        if hole and ctx.face in ("north", "south") and ctx.w >= 3 and ctx.h >= 3:
            rect(ctx, 0.34, 0.3, 0.66, 0.62, (14, 12, 12))  # the bow's hole
    return paint


def rust(ctx):
    fill(ctx, RUST, 0.15)
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            if ctx.rng.random() < 0.3:
                texel(ctx, xx, yy, (78, 46, 30))


# ---------------- The model ----------------

# Level keys: (paint, bow paint, shaft length, shaft width, bow w, bow h, bit w, bit h)
KEY_KINDS = [
    ("iron", 4.8, 0.4, 1.8, 1.8, 0.9, 1.0),     # a skeleton key
    ("brass", 5.4, 0.45, 2.2, 2.0, 1.0, 1.2),   # an ornate one
    ("steel", 3.0, 0.7, 1.6, 1.3, 0.5, 2.0),    # a modern key: a short wide blade, teeth along it
    ("rust", 4.2, 0.4, 1.6, 1.6, 0.8, 0.8),
    ("iron", 5.6, 0.45, 2.0, 1.6, 1.2, 1.4),
    ("brass", 3.6, 0.4, 1.5, 1.5, 0.8, 0.9),
    ("stone", 3.4, 0.7, 2.0, 1.7, 0.9, 1.0),    # canon: some keys are stone
    ("iron", 4.4, 0.4, 1.7, 1.9, 0.9, 1.1),
    ("plastic", 3.0, 0.6, 2.0, 1.8, 0.6, 1.6),  # and some plastic
    ("brass", 4.8, 0.4, 1.9, 1.7, 1.0, 1.0),
    ("steel", 3.2, 0.7, 1.7, 1.3, 0.5, 2.2),
    ("iron", 5.0, 0.45, 2.1, 1.9, 1.1, 1.2),
    ("rust", 3.8, 0.4, 1.5, 1.4, 0.9, 0.8),
    ("brass", 4.2, 0.4, 2.0, 2.0, 0.8, 1.0),
    ("iron", 3.6, 0.4, 1.6, 1.6, 0.8, 0.9),
]
KEY_PAINT = {"iron": IRON, "brass": BRASS, "steel": STEEL, "stone": STONE, "plastic": PLASTIC}

RING_PIVOT = (-3.0, 19.0, 3.4)
RING_C, RING_R = (-3.0, 14.4), 3.0


def build():
    m = Model("hub-keymaster", atlas_width=64, seed=1717)
    # B17: light baked from the rest pose (rig.bake): occlusion under the capelet, at the cuffs and the keys, round limbs;
    # added as if 24 levels brighter, since the robe is near black and takes no shape from multiplied light alone
    m.light = dict(floor=24.0, grad=0.12, edge=0.06, foot=0.04)
    # The waist is the root; under it a solid robe, so no swing of the panels shows a gap
    waist = m.part("Waist", (-2.5, 18, -3.5), (5, 4, 7), pivot=(0, 20, 0), paint=inner)
    m.part("Belt", (-2.8, 18.4, -3.8), (5.6, 1.4, 7.6), pivot=(0, 19, 0), parent=waist, paint=belt)
    m.part("Buckle", (-3.05, 18.2, -0.9), (0.4, 1.8, 1.8), pivot=(-2.9, 19, 0), parent=waist, paint=buckle)
    skirt = m.part("Skirt", (-3.0, 11.5, -4.0), (6.0, 7, 8.0), pivot=(0, 18, 0), parent=waist, paint=robe)
    m.part("SkirtLow", (-3.5, 5.5, -4.5), (7.0, 6.2, 9.0), pivot=(0, 11.5, 0), parent=skirt, paint=robe)
    m.part("Hem", (-4.0, 0.9, -5.0), (8.0, 4.8, 10.0), pivot=(0, 5, 0), parent=skirt, paint=robe_hem)
    # The outer panels, a little proud of the robe and flaring to the hem a pixel off the floor
    m.part("CloakFront", (-4.0, 1.0, -3.2), (0.9, 17.5, 6.4), pivot=(-3.55, 18.5, 0), parent=waist, rest=(0, 0, -6), paint=front_panel)
    m.part("CloakSideL", (-2.8, 1.0, 4.1), (6.0, 17.5, 0.9), pivot=(0, 18.5, 4.55), parent=waist, rest=(-6, 0, 0), paint=side_panel)
    m.mirror("CloakSideL", "CloakSideR", parent=waist)
    # Pointed boots: canon has him touch down, stride, spin on his heel
    boot_l = m.part("BootL", (-3.6, 0, 0.6), (3.0, 1.3, 1.9), pivot=(-1.0, 1.3, 1.55), parent=waist, paint=boot)
    m.part("ToeL", (-6.3, 0, 0.9), (2.7, 0.9, 1.3), pivot=(-3.6, 0.45, 1.55), parent=boot_l, rest=(0, 0, -8), paint=boot)
    m.mirror("BootL", "BootR", parent=waist)

    # Chest, stooped a little; a shoulder mantle clasped with a keyhole; a cape from the shoulders to the hem
    chest = m.part("Chest", (-2.6, 21.5, -3.6), (5.2, 8.5, 7.2), pivot=(0, 22, 0), parent=waist, rest=(0, 0, 5), paint=inner)
    cape_top = m.part("CloakBack", (2.5, 15.0, -5.6), (1.2, 14.5, 11.2), pivot=(3.1, 29.5, 0), parent=chest, rest=(0, 0, 1), paint=cape)
    m.part("CapeLow", (2.5, 1.4, -5.6), (1.2, 13.8, 11.2), pivot=(3.1, 15.0, 0), parent=cape_top, paint=cape_low)
    m.part("Mantle", (-3.6, 26.6, -6.6), (7.2, 3.6, 13.2), pivot=(0, 28, 0), parent=chest, paint=mantle)
    m.part("MantleSideL", (-3.2, 22.6, 6.0), (6.4, 4.4, 0.7), pivot=(0, 27, 6.35), parent=chest, rest=(-8, 0, 0), paint=mantle)
    m.mirror("MantleSideL", "MantleSideR", parent=chest)
    m.part("MantleFront", (-4.1, 23.8, -4.6), (0.6, 5.2, 9.2), pivot=(-3.8, 29, 0), parent=chest, rest=(0, 0, -3), paint=mantle)
    m.part("Clasp", (-4.6, 27.0, -0.8), (0.5, 1.6, 1.6), pivot=(-4.3, 28, 0), parent=chest, paint=clasp)
    m.part("Cowl", (-3.2, 29.6, -4.2), (6.4, 2.4, 8.4), pivot=(0, 30, 0), parent=chest, paint=hood)

    # The hood: a shell, its crown, a brim standing forward of the face, a pointed peak and a drape onto the cape.
    # The face is set 1.5 px back from the brim, so it sits in shadow
    neck = m.part("Neck", (-1.2, 30.5, -1.4), (2.4, 2.5, 2.8), pivot=(0, 31, 0), parent=chest, rest=(0, 0, 9), paint=hood_in)
    head = m.part("Hood", (-3.0, 32.0, -3.3), (6.4, 7.6, 6.6), pivot=(0, 32.5, 0), parent=neck, paint=hood)
    m.part("BrimTop", (-4.8, 38.4, -3.6), (2.6, 1.8, 7.2), pivot=(-3.0, 39.5, 0), parent=head, rest=(0, 0, 6), paint=brim)
    m.part("BrimL", (-4.6, 31.6, 2.0), (1.8, 7.0, 1.6), pivot=(-3.2, 35, 2.8), parent=head, rest=(0, 0, 3), paint=brim)
    m.mirror("BrimL", "BrimR", parent=head)
    m.part("HoodTip", (1.0, 37.4, -2.4), (4.4, 2.4, 4.8), pivot=(1.0, 38.6, 0), parent=head, rest=(0, 0, -22), paint=hood)
    m.part("HoodDrape", (1.4, 28.4, -3.6), (2.4, 4.6, 7.2), pivot=(2.6, 32, 0), parent=head, rest=(0, 0, 4), paint=hood)
    m.part("Face", (-3.25, 32.2, -2.0), (0.3, 6.0, 4.0), pivot=(-3.1, 35, 0), parent=head, paint=face)
    m.part("Nose", (-3.5, 34.6, -0.25), (0.3, 1.0, 0.5), pivot=(-3.35, 35.0, 0), parent=head, paint=face_part)
    m.part("Chin", (-3.45, 32.2, -0.75), (0.25, 0.8, 1.5), pivot=(-3.3, 32.6, 0), parent=head, paint=face_part)
    m.part("EyeL", (-3.4, 36.2, 0.55), (0.2, 0.45, 0.85), pivot=(-3.3, 36.4, 1), parent=head, paint=eye, glow=150)
    m.mirror("EyeL", "EyeR", parent=head)

    # Long thin arms in bell sleeves; grey hands with long two-jointed fingers hanging well below the hips
    arm = m.part("ArmL", (-1.5, 20.5, 4.0), (3.0, 9.0, 2.8), pivot=(0, 29, 5.4), parent=chest, rest=(-4, 0, -2), paint=sleeve)
    fore = m.part("ForearmL", (-1.4, 12.5, 4.1), (2.8, 8.5, 2.6), pivot=(0, 20.8, 5.4), parent=arm, rest=(0, 0, -8), paint=sleeve)
    m.part("CuffL", (-2.1, 10.6, 3.4), (4.2, 3.4, 4.0), pivot=(0, 12.5, 5.4), parent=fore, paint=cuff)
    palm = m.part("HandL", (-0.9, 8.6, 4.75), (1.8, 3.2, 1.3), pivot=(0, 11.6, 5.4), parent=fore, rest=(0, 0, 3), paint=hand)
    for i, length in enumerate((2.4, 2.8, 2.6, 2.0)):
        x = -0.88 + i * 0.45
        fing = m.part(f"Finger{i}L", (x, 8.6 - length, 5.15), (0.4, length, 0.5), pivot=(x + 0.2, 8.6, 5.4), parent=palm,
                      rest=(6, 0, -3 + 2 * i), paint=finger)
        y0 = 8.6 - length
        m.part(f"Tip{i}L", (x + 0.03, y0 - length * 0.9, 5.17), (0.34, length * 0.9, 0.46), pivot=(x + 0.2, y0, 5.4), parent=fing,
               rest=(10, 0, 0), paint=fingertip)
    m.part("ThumbL", (-1.15, 7.0, 4.9), (0.45, 2.2, 0.5), pivot=(-0.9, 9.2, 5.15), parent=palm, rest=(-10, 0, -14), paint=fingertip)
    m.mirror("ArmL", "ArmR", parent=chest)

    # The key ring at the front-left hip, turned to face front-left; fifteen keys hung round its lower half
    px, py, pz = RING_PIVOT
    cx, cy = RING_C
    ring = m.part("KeyRing", (px - 0.3, py - 0.6, pz - 0.3), (0.6, 1.0, 0.6), pivot=RING_PIVOT, parent=waist, rest=(-6, -45, 0),
                  paint=metal(IRON))
    m.part("RingHanger", (px - 0.2, cy + RING_R - 0.2, pz - 0.2), (0.4, py - (cy + RING_R) - 0.2, 0.4), pivot=RING_PIVOT,
           parent=ring, paint=metal(IRON))
    n = 10
    seg = 2 * RING_R * math.tan(math.pi / n) + 0.15
    for k in range(n):
        a = k * math.tau / n
        hx, hy = cx + RING_R * math.cos(a), cy + RING_R * math.sin(a)
        m.part(f"Hoop{k}", (hx - 0.25, hy - seg / 2, pz - 0.25), (0.5, seg, 0.5), pivot=(hx, hy, pz), parent=ring,
               rest=(0, 0, -math.degrees(a)), paint=metal(IRON))
    for k, (kind, length, sw, bw, bh, bitw, bith) in enumerate(KEY_KINDS):
        a = math.radians(205 + k * (130 / 14))
        hx, hy = cx + RING_R * math.cos(a), cy + RING_R * math.sin(a)
        zz = pz + (0.32 if k % 2 else -0.32)
        colour = KEY_PAINT.get(kind, RUST)
        paint = rust if kind == "rust" else metal(colour)
        bow_paint = rust if kind == "rust" else metal(colour, hole=True)
        top = hy - bh + 0.5  # the hoop runs through the bow
        key = m.part(f"Key{k}", (hx - sw / 2, top - length, zz - 0.17), (sw, length, 0.34), pivot=(hx, hy, zz), parent=ring,
                     rest=(0, 0, (k - 7) * 4), paint=paint)
        m.part(f"KeyBow{k}", (hx - bw / 2, top - 0.1, zz - 0.2), (bw, bh, 0.4), pivot=(hx, hy, zz), parent=key, paint=bow_paint)
        side = 1 if k % 3 else -1
        bx = hx + sw / 2 if side > 0 else hx - sw / 2 - bitw
        m.part(f"KeyBit{k}", (bx, top - length + 0.1, zz - 0.14), (bitw, bith, 0.28), pivot=(hx, hy, zz), parent=key, paint=paint)
    return m


# ---------------- Animations ----------------

KEYS = [f"Key{k}" for k in range(15)]
CLOAK_PARTS = ["CloakFront", "CloakBack", "CapeLow", "CloakSideL", "CloakSideR"]


def fingers(side):
    return [f"{b}{i}{side}" for i in range(4) for b in ("Finger", "Tip")]


def animate(m):
    def idle(p):
        out = {"Waist": pose((0, 0, 0), (0, s(p, 0.2), 0)),
               "Chest": pose((0, 0, s(p, 1.2, 0.1))),
               "CloakFront": pose((0, 0, s(p, 1.5, 0.15))), "CloakBack": pose((0, 0, s(p, 1.0, 0.3))), "CapeLow": pose((0, 0, s(p, 1.5, 0.4))),
               "CloakSideL": pose((s(p, 1.2, 0.2), 0, 0)), "CloakSideR": pose((-s(p, 1.2, 0.25), 0, 0)),
               "MantleFront": pose((0, 0, s(p, 1.5, 0.2))),
               "KeyRing": pose((s(p, 3, 0.25), 0, s(p, 4, 0.1))),
               "ArmL": pose((0, 0, s(p, 1.5, 0.1))), "ArmR": pose((0, 0, -s(p, 1.5, 0.1))),
               "Hood": pose((s(p, 2, 0.4), s(p, 5, 0.1), s(p, 2, 0.3)))}
        for i, k in enumerate(KEYS):
            out[k] = pose((0, 0, s(p, 4, 0.05 * i)))
        # The long fingers flex, one after another, as if counting
        for side, sign in (("L", 1), ("R", -1)):
            for i in range(4):
                f = max(0.0, s(p * 2, 1.0, -0.08 * i))
                out[f"Finger{i}{side}"] = pose((sign * 14 * f, 0, 0))
                out[f"Tip{i}{side}"] = pose((sign * 18 * f, 0, 0))
        return out
    m.animation("idle", 120, cycle(120, 24, idle))

    def descend(p):
        flutter = 10 + s(p * 2, 4)
        out = {"CloakFront": pose((0, 0, -flutter)), "CloakBack": pose((0, 0, 3 + flutter * 0.3)), "CapeLow": pose((0, 0, 4 + flutter * 0.8)),
               "CloakSideL": pose((-flutter * 0.9, 0, 0)), "CloakSideR": pose((flutter * 0.9, 0, 0)),
               "MantleFront": pose((0, 0, -6 - s(p * 2, 3, 0.2))),
               "Mantle": pose((0, 0, 0), (0, 0.4 + s(p * 2, 0.3), 0)),
               "Hood": pose((0, 0, 10)),
               "BootL": pose((0, 0, 40)), "BootR": pose((0, 0, 36)),
               "KeyRing": pose((-8 + s(p * 2, 8), 0, s(p * 2, 12, 0.25))),
               "ArmL": pose((-10, 0, 0)), "ArmR": pose((10, 0, 0)),
               "HandL": pose((-14, 0, 0)), "HandR": pose((14, 0, 0))}
        for i, k in enumerate(KEYS):
            out[k] = pose((s(p * 2, 14, 0.07 * i), 0, s(p * 2, 20, 0.11 * i)))
        return out
    m.animation("descend", 40, cycle(40, 20, descend))

    # One long arm out toward the door, one finger; the sleeve's bell droops from it
    point_parts = ["ArmR", "ForearmR", "CuffR", "HandR", "ThumbR", "Hood", "Chest", "CloakBack", "CapeLow"] + fingers("R")
    out = {"ArmR": pose((-10, 0, -80)), "ForearmR": pose((0, 0, 4)), "CuffR": pose((0, 0, 30)), "HandR": pose((0, 0, -4)),
           "Finger0R": pose((-6, 0, 3)), "Tip0R": pose((10, 0, 0)), "ThumbR": pose((-30, 0, 10)),
           "Hood": pose((0, -14, 4)), "Chest": pose((0, -6, 2)), "CloakBack": pose((0, 0, -1)), "CapeLow": pose((0, 0, 2))}
    for i in (1, 2, 3):
        out[f"Finger{i}R"] = pose((-70, 0, 0))
        out[f"Tip{i}R"] = pose((-80, 0, 0))
    m.animation("point", 50, {0: full(point_parts, {}), 12: full(point_parts, out), 40: full(point_parts, out),
                              49: full(point_parts, {})}, end="Stop")

    # Both arms back, then forward hard, palms out; he leans into it and the cloak flies back
    shove_parts = ["ArmL", "ArmR", "ForearmL", "ForearmR", "HandL", "HandR", "CuffL", "CuffR", "Chest", "Waist", "Hood",
                   "CloakFront", "CloakBack", "CapeLow", "KeyRing"]
    wind = {"ArmL": pose((0, 0, 30)), "ArmR": pose((0, 0, 30)), "ForearmL": pose((0, 0, -60)), "ForearmR": pose((0, 0, -60)),
            "Chest": pose((0, 0, -8)), "Hood": pose((0, 0, 6)), "CloakBack": pose((0, 0, 2)), "CapeLow": pose((0, 0, 3)), "KeyRing": pose((0, 0, -10))}
    hit = {"ArmL": pose((8, 0, -86)), "ArmR": pose((-8, 0, -86)), "ForearmL": pose((0, 0, 4)), "ForearmR": pose((0, 0, 4)),
           "HandL": pose((0, 0, -75)), "HandR": pose((0, 0, -75)), "CuffL": pose((0, 0, 25)), "CuffR": pose((0, 0, 25)),
           "Chest": pose((0, 0, 14)), "Waist": pose((0, 0, 0), (-1.5, 0, 0)), "Hood": pose((0, 0, -6)),
           "CloakFront": pose((0, 0, 8)), "CloakBack": pose((0, 0, -4)), "CapeLow": pose((0, 0, 12)), "KeyRing": pose((0, 0, 20))}
    m.animation("shove", 30, {0: full(shove_parts, {}), 9: full(shove_parts, wind), 14: full(shove_parts, hit),
                              22: full(shove_parts, hit), 29: full(shove_parts, {})}, end="Stop")

    # A spin on the heel, the cape and the keys flung out by it
    turn_parts = ["Waist", "Mantle", "MantleFront", "KeyRing"] + CLOAK_PARTS

    def turn_frame(deg, swoop):
        return full(turn_parts, {"Waist": pose((0, deg, 0)), "CloakFront": pose((0, 0, -swoop * 0.5)),
                                 "CloakBack": pose((-swoop * 0.5, 0, swoop * 0.3)), "CapeLow": pose((-swoop * 0.6, 0, swoop * 0.6)),
                                 "CloakSideL": pose((-swoop * 0.5, 0, 0)), "CloakSideR": pose((swoop * 0.5, 0, 0)),
                                 "Mantle": pose((0, -swoop * 0.4, 0)), "MantleFront": pose((0, 0, -swoop * 0.5)),
                                 "KeyRing": pose((-swoop * 1.2, 0, 0))})
    m.animation("turn", 20, {0: turn_frame(0, 0), 5: turn_frame(100, 18), 10: turn_frame(200, 26), 15: turn_frame(300, 16),
                             19: turn_frame(360, 0)}, end="Stop")

    # He takes the ring in his left hand, lifts it and shakes it
    jingle_parts = ["ArmL", "ForearmL", "HandL", "CuffL", "ThumbL", "KeyRing", "Hood"] + fingers("L") + KEYS
    grip = {f"Finger{i}L": pose((40, 0, 0)) for i in range(4)}
    grip.update({f"Tip{i}L": pose((50, 0, 0)) for i in range(4)})
    grip["ThumbL"] = pose((30, 0, 0))
    reach = {"ArmL": pose((10, 0, -22)), "ForearmL": pose((6, 0, -38)), "HandL": pose((0, 0, -10)), "CuffL": pose((0, 0, 14)),
             "Hood": pose((0, 8, 8))}
    j0 = full(jingle_parts, {})
    j1 = full(jingle_parts, dict(reach, **grip, KeyRing=pose((0, 0, -14))))
    j1.update({k: pose((0, 0, 16 * (1 if i % 2 else -1))) for i, k in enumerate(KEYS)})
    j2 = full(jingle_parts, dict(reach, **grip, KeyRing=pose((10, 0, 8)), ForearmL=pose((6, 0, -44))))
    j2.update({k: pose((8, 0, -16 * (1 if i % 2 else -1))) for i, k in enumerate(KEYS)})
    m.animation("jingle", 36, {0: j0, 8: j1, 14: j2, 20: j1, 26: j2, 35: j0}, end="Stop")

    # A curt backhand flick of the right hand, the head turning away: "Yes yes, indeed, goodbye!"
    dismiss_parts = ["ArmR", "ForearmR", "HandR", "CuffR", "Hood", "Chest"] + fingers("R")
    up = {"ArmR": pose((0, 0, -30)), "ForearmR": pose((0, 0, -60)), "HandR": pose((0, 0, -20)), "CuffR": pose((0, 0, 20)),
          "Hood": pose((0, 10, 0))}
    flick = {"ArmR": pose((24, 0, -36)), "ForearmR": pose((-10, 0, -50)), "HandR": pose((-40, 0, 10)), "CuffR": pose((0, 0, 20)),
             "Hood": pose((0, 22, -4)), "Chest": pose((0, 6, 0))}
    flick.update({f"Finger{i}R": pose((10, 0, 0)) for i in range(4)})
    m.animation("dismiss", 24, {0: full(dismiss_parts, {}), 7: full(dismiss_parts, up), 11: full(dismiss_parts, flick),
                                17: full(dismiss_parts, flick), 23: full(dismiss_parts, {})}, end="Stop")

    # A quick, long stride: the boots step under the robe, the cloak swings, the arms barely move
    def stride(p):
        a, b = s(p, 1), s(p, 1, 0.5)
        lift_l, lift_r = max(0.0, s(p, 0.8, 0.25)), max(0.0, s(p, 0.8, 0.75))
        out = {"Waist": pose((0, s(p, 3), 0), (0, abs(s(p, 0.4)), 0)),
               "Chest": pose((0, -s(p, 4), 3)),
               "BootL": pose((0, 0, -lift_l * 25), (a * 2.4, lift_l, 0)), "BootR": pose((0, 0, -lift_r * 25), (b * 2.4, lift_r, 0)),
               "CloakFront": pose((0, 0, -3 - 3 * abs(a))), "CloakBack": pose((0, 0, 1 + s(p * 2, 1))), "CapeLow": pose((0, 0, 3 + s(p * 2, 2, 0.15))),
               "CloakSideL": pose((0, 0, -a * 5)), "CloakSideR": pose((0, 0, -b * 5)),
               "ArmL": pose((0, 0, a * 6)), "ArmR": pose((0, 0, b * 6)),
               "KeyRing": pose((s(p * 2, 6), 0, s(p, 10, 0.2)))}
        for i, k in enumerate(KEYS):
            out[k] = pose((0, 0, s(p * 2, 10, 0.06 * i)))
        return out
    m.animation("stride", 30, cycle(30, 12, stride))


def entity():
    data = {
        "code": "hub-keymaster",
        "class": "EntityAgent",
        "tags": ["backrooms-entity"],
        "weight": 90,
        "hitboxSize": {"x": 0.8, "y": 2.7},
        "eyeHeight": 2.35,
        "attributes": {"keymaster": True, "invulnerable": True},
        "client": {
            "renderer": "Shape",
            "shape": {"base": "backrooms:entity/hub-keymaster"},
            "texture": {"base": "backrooms:entity/hub-keymaster"},
            "size": 1,
            "behaviors": [{"code": "interpolateposition"}],
            "animations": [
                {"code": "idle", "animation": "idle", "animationSpeed": 1.0, "blendMode": "Average", "triggeredBy": {"defaultAnim": True}},
                {"code": "descend", "animation": "descend", "animationSpeed": 1.0, "blendMode": "Average", "weight": 4},
                {"code": "point", "animation": "point", "animationSpeed": 1.0, "blendMode": "Average", "weight": 6},
                {"code": "shove", "animation": "shove", "animationSpeed": 1.0, "blendMode": "Average", "weight": 8},
                {"code": "turn", "animation": "turn", "animationSpeed": 1.0, "blendMode": "Average", "weight": 8},
                {"code": "jingle", "animation": "jingle", "animationSpeed": 1.0, "blendMode": "Average", "weight": 5},
                {"code": "dismiss", "animation": "dismiss", "animationSpeed": 1.0, "blendMode": "Average", "weight": 6},
                {"code": "stride", "animation": "stride", "animationSpeed": 1.0, "blendMode": "Average", "weight": 4},
            ],
        },
        "server": {
            "behaviors": [
                {"code": "taskai", "aiCreatureType": "Default", "aitasks": [
                    {"code": "lookatentity", "priority": 1.5, "maxTurnAngleDeg": 60, "entityCodes": ["player"]},
                    {"code": "idle", "priority": 1.0, "minduration": 4000, "maxduration": 8000, "mincooldown": 2000,
                     "maxcooldown": 6000, "animation": "jingle", "animationSpeed": 1.0, "sound": "backrooms:effect/hub/keyjingle",
                     "soundRange": 16},
                ]},
            ],
        },
        "sounds": {"idle": "backrooms:effect/hub/keyjingle"},
        "idleSoundChance": 0.02,
    }
    write_json(os.path.join(ASSETS, "entities", "hub-keymaster.json"), data,
               "The Keymaster: the Hub's overseer (hub-plan.md 2.6, 4.7). No health behaviour (he cannot be hurt), no physics (he"
               " floats; HubSystem moves him: descend, escort). Class EntityAgent until the code's own class exists")


def generate():
    m = build()
    animate(m)
    m.save()
    entity()
