"""Level 8's Giant Spider: its model, texture and animations (built through gen_models.MODELS), and its entity type
and names (written by gen_entities.py).

The lore (Level 8, "Cave Systems"): Wikidot's page says the caves hold "innumerably many species of spiders", most in
"large, single-species clusters", "aggressively territorial", "HIGHLY venomous", some with "extreme gigantism" bred
into them by the Church of the Veiled; "Spiders can't swim!", so whoever stumbles into a nest should make for water.
The old Fandom page (the version most retold) gave the level its name for "spider-like creatures": nests of small
spiders and "massive king and queen spiders", the queens deadly, and loud sounds "attracting large numbers of spiders
to the source". The current Fandom page's Troglosidae are "far larger" than spiders, with long legs for building webs
and many tiny eyes. The guides add the web of a Giant Spider.

So the model is a spider as big as a person is long, low and wide: a cave hunting spider, not a cartoon. A rounded
cephalothorax with a raised eye mound, eight eyes as geometry (two big forward ones, two smaller beside them, two on
top, two at the sides) that catch any light as eyeshine; heavy chelicerae with black fangs folded under them and short
pedipalps either side; a slim pedicel; a large egg-shaped abdomen carried a little raised, with a pale folium of
chevrons down its back and spinnerets at the end. Eight legs, each a coxa and three segments (femur, tibia,
metatarsus), the first and fourth pairs the longest, knees high above the body, banded pale at the joints and bristled.
Dark umber, almost black, with grey-tan hair: in Level 8's dark, all you see first is the eyes.

Rig (rig.py conventions: faces -X, left is +Z, feet at y=0, model pixels): the root is the cephalothorax; each leg's
coxa is turned to the leg's direction (yaw 0 forward, 90 to its left) and the leg is built along -X in that frame, as
the Mangled's are, so a femur's z rotation raises or lowers it and its y rotation swings it fore and aft. Feet stay on
the floor when the body lowers or rears (leg_ik).

Animations: idle, lurk (low on its legs, forelegs feeling ahead, palps twitching), walk and run (alternating
tetrapods: L1 R2 L3 R4 against R1 L2 R3 L4), rear (the threat display: forelegs and palps up, fangs spread), attack
(rears and lunges, the fangs strike at 450 ms), hurt, die (the legs curl in under it).

Run from the repo root:  python tools/gen_models.py giantspider   (or gen_entities.py for everything)
"""
import math
import random

import rig
from rig import Model, speckle, vlines, hlines, mix, shade, clamp, pose
from rig import lit_fill as fill
from gen_models import lit, cycle, full, ramp, s, blotch, line, texel, texrow, TAU

# ---------------------------------------------------------------- Colours

SP_BASE = (50, 39, 31)         # dark umber chitin
SP_DEEP = (26, 20, 17)         # the deepest shade, seams, the fovea
SP_HAIR = (122, 108, 88)       # grey-tan setae
SP_HAIR_DK = (74, 62, 50)
SP_BAND = (128, 110, 84)       # the pale rings at the leg joints
SP_FOLIUM = (138, 118, 90)     # the chevrons down the abdomen
SP_BELLY = (70, 60, 52)
SP_FANG = (18, 12, 12)
SP_FANG_HI = (86, 40, 34)      # dark red at the fang's base
SP_SHEEN = (58, 64, 74)        # a cold blue-grey sheen on the chelicerae
SP_EYE = (8, 7, 8)
SP_SHINE = (214, 232, 196)     # eyeshine: the tapetum catching a torch
SP_SILK = (214, 208, 196)


def _along(ctx, xx):
    """For a limb built along -X: how far along it (0 at the root, the +X end; 1 at the tip) a texel column lies."""
    u = (xx + 0.5) / ctx.w
    return u if ctx.face == "north" else 1 - u


def _side(ctx):
    return ctx.face in ("north", "south", "up", "down")


def _setae(ctx, density=0.5, length=2, direction=None):
    """Bristles: short strokes of pale hair over the chitin, and a few dark ones."""
    speckle(ctx, mix(SP_BASE, SP_HAIR, 0.5), 0.03 * density)
    speckle(ctx, SP_HAIR_DK, 0.05 * density)
    if ctx.baked:
        d = direction or ((1, 0) if _side(ctx) else (0, 1))
        rig.fur(ctx, d, length=length, density=density, tip=1.25, root=0.88)


def sp_chitin(ctx):
    fill(ctx, SP_BASE, 0.06)
    blotch(ctx, shade(SP_BASE, 0.75), 2, 1.5, 3.5, 0.35)
    _setae(ctx, 0.5)


def sp_carapace(ctx):
    """The cephalothorax: on top, dark striae radiating from the fovea, a paler rim, a grey-haired band down the
    middle; the sides darker, densely haired."""
    fill(ctx, SP_BASE, 0.05)
    if ctx.face == "up":
        cu, cv = 0.62, 0.5
        for k in range(10):
            a = TAU * k / 10
            line(ctx, cu, cv, cu + 0.55 * math.cos(a), cv + 0.62 * math.sin(a), SP_DEEP, 0.45)
        rig.rect(ctx, 0.0, 0.42, 1.0, 0.58, mix(SP_BASE, SP_HAIR, 0.35))       # the pale median band
        rig.rect(ctx, cu - 0.04, cv - 0.06, cu + 0.04, cv + 0.06, SP_DEEP)     # the fovea
        texrow(ctx, 0, 0, ctx.w - 1, mix(SP_BASE, SP_BAND, 0.35), 0.6)
        texrow(ctx, ctx.h - 1, 0, ctx.w - 1, mix(SP_BASE, SP_BAND, 0.35), 0.6)
    elif ctx.face == "down":
        fill(ctx, SP_BELLY, 0.05)
    _setae(ctx, 0.6)


def sp_head(ctx):
    """The face under the eyes: dark, thick with bristles."""
    fill(ctx, shade(SP_BASE, 0.9), 0.05)
    _setae(ctx, 0.7, length=2, direction=(0, 1))


def sp_eye(ctx):
    """A spider's eye: a glossy black dome, a bright point of eyeshine and a pale rim where the light catches it."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            px[ctx.x + xx, ctx.y + yy] = SP_EYE + (255,)
    big = ctx.part.tag.get("big", False)
    if ctx.face in ("west", "up") or ctx.part.tag.get("look") == ctx.face:
        # A ring of the tapetum's green-white, the brightest toward the top
        for xx in range(ctx.w):
            for yy in range(ctx.h):
                du, dv = (xx + 0.5) / ctx.w - 0.5, (yy + 0.5) / ctx.h - 0.5
                r = math.hypot(du, dv)
                if 0.28 < r < 0.5:
                    texel(ctx, xx, yy, mix(SP_EYE, SP_SHINE, 0.1 if dv > 0 else 0.22))
        texel(ctx, max(0, ctx.w // 2 - 1), max(0, ctx.h // 2 - 1), SP_SHINE, 1.0)
        if big and ctx.w >= 3:
            texel(ctx, ctx.w // 2, ctx.h // 2 - 1, SP_SHINE, 0.6)
            texel(ctx, ctx.w // 2 - 1, ctx.h // 2, mix(SP_EYE, SP_SHINE, 0.5), 0.8)


def sp_mound(ctx):
    """The eye mound, darker than the carapace and bare."""
    fill(ctx, shade(SP_BASE, 0.7), 0.04)


def sp_chelicera(ctx):
    """The jaws: heavy, dark, a cold sheen down their front, bristled."""
    fill(ctx, shade(SP_BASE, 0.85), 0.05)
    if ctx.face in ("west", "north", "south"):
        vlines(ctx, mix(SP_BASE, SP_SHEEN, 0.55), 3, start=1, alpha=0.35)
    _setae(ctx, 0.6, length=2, direction=(0, 1))


def sp_fang(ctx):
    """A fang: black, glossy, dark red at its base, a dull highlight down one edge."""
    fill(ctx, SP_FANG, 0.03, face_shade=False)
    texrow(ctx, 0, 0, ctx.w - 1, SP_FANG_HI, 0.8)
    if ctx.face in ("west", "north"):
        for yy in range(ctx.h):
            texel(ctx, 0, yy, (70, 64, 66), 0.5)


def sp_leg(ctx):
    """A leg segment (built along -X): dark, a pale ring at the joint it ends in and a fainter one at its root, hair laid
    along it toward the tip, and a few long dark spines standing out across it."""
    t = ctx.part.tag
    fill(ctx, SP_BASE, 0.05)
    px = ctx.img.load()
    if _side(ctx):
        band, root_band = t.get("band", 0.16), t.get("root_band", 0.06)
        for xx in range(ctx.w):
            a = _along(ctx, xx)
            k = 0.0
            if a > 1 - band:
                k = 0.55 * (a - (1 - band)) / band
            elif a < root_band:
                k = 0.3 * (1 - a / root_band)
            if k > 0:
                for yy in range(ctx.h):
                    c = px[ctx.x + xx, ctx.y + yy]
                    px[ctx.x + xx, ctx.y + yy] = mix(c[:3], SP_BAND, k) + (255,)
        # Hair laid toward the tip (the tip is at u = 0 except on north faces)
        if ctx.baked:
            rig.fur(ctx, (1, 0) if ctx.face == "north" else (-1, 0), length=3, density=0.5, tip=1.28, root=0.88)
        speckle(ctx, mix(SP_BASE, SP_HAIR, 0.5), 0.025)
        # Spines: dark strokes standing across the segment, more on the tibiae
        spines = t.get("spines", 2)
        for _ in range(spines):
            xx = ctx.rng.randrange(1, max(2, ctx.w - 1))
            for yy in range(0, max(1, ctx.h // 2)):
                texel(ctx, xx, yy, SP_DEEP, 0.75)
    else:
        # The ends: the joint's pale membrane
        fill(ctx, mix(SP_BASE, SP_BAND, 0.3), 0.05)
    if t.get("claw") and ctx.face in ("west",):
        fill(ctx, SP_DEEP, 0.02)


def sp_coxa(ctx):
    fill(ctx, mix(SP_BASE, SP_BELLY, 0.4), 0.05)
    _setae(ctx, 0.4)


def sp_pedicel(ctx):
    fill(ctx, shade(SP_BELLY, 0.8), 0.04)


def sp_abdomen(ctx):
    """The abdomen: dark umber thick with grey-tan hair; down its back a pale folium of chevrons pointing forward, a
    dark heart mark at the front; the sides mottled with pale flecks; the underside paler, with the book lungs."""
    fill(ctx, SP_BASE, 0.06)
    blotch(ctx, shade(SP_BASE, 0.8), 3, 2, 5, 0.35)
    tag = ctx.part.tag
    if ctx.face == "up" and tag.get("folium"):
        # u runs along -X to +X? On an up face u = 0 is the -X end (the front); v across
        n = 5
        for i in range(n):
            u0 = 0.18 + 0.72 * i / n
            w = 0.34 - 0.045 * i
            for xx in range(ctx.w):
                u = (xx + 0.5) / ctx.w
                for yy in range(ctx.h):
                    v = (yy + 0.5) / ctx.h - 0.5
                    # a chevron: the band's front edge runs back from the middle line toward the sides
                    edge = u0 + 1.1 * abs(v)
                    if edge <= u < edge + 0.06 and abs(v) < w:
                        texel(ctx, xx, yy, SP_FOLIUM, 0.75 - 0.08 * i)
                    elif edge + 0.06 <= u < edge + 0.09 and abs(v) < w:
                        texel(ctx, xx, yy, SP_DEEP, 0.5)
        rig.rect(ctx, 0.02, 0.44, 0.2, 0.56, SP_DEEP)                       # the heart mark
    elif ctx.face in ("north", "south"):
        speckle(ctx, mix(SP_BASE, SP_FOLIUM, 0.6), 0.05)
        blotch(ctx, mix(SP_BASE, SP_FOLIUM, 0.4), 2, 1.0, 2.5, 0.4)
    elif ctx.face == "down":
        fill(ctx, SP_BELLY, 0.05)
        if tag.get("folium"):
            rig.rect(ctx, 0.1, 0.25, 0.22, 0.4, shade(SP_BELLY, 1.3))       # the book lungs
            rig.rect(ctx, 0.1, 0.6, 0.22, 0.75, shade(SP_BELLY, 1.3))
    _setae(ctx, 0.65, length=3, direction=(1, 0) if ctx.face in ("up", "down") else (0, 1))


def sp_spinneret(ctx):
    fill(ctx, mix(SP_BELLY, SP_SILK, 0.25), 0.05)


def sp_palp(ctx):
    sp_leg(ctx)
    if ctx.part.tag.get("bulb"):
        fill(ctx, shade(SP_BASE, 0.7), 0.04)


# ---------------------------------------------------------------- The legs

# Each leg: (name, root x, root z, yaw, femur length, femur angle (negative: up), tibia length, tibia angle,
# metatarsus angle (over 90: in under), thickness). Left side (+Z) front to back; the right mirrors it, a little apart.
# Lengths: the first and fourth pairs the longest, as a hunting spider's.
SP_ROOT_Y = 11.5
SP_LEGS_L = [
    ("L1", -7.2, 3.6, 30, 18.0, -40, 17.5, 50, 72, 2.1),
    ("L2", -5.0, 4.3, 70, 15.5, -44, 15.5, 56, 78, 2.0),
    ("L3", -2.6, 4.3, 114, 14.0, -46, 13.5, 58, 80, 1.95),
    ("L4", -0.4, 3.5, 154, 17.5, -38, 17.0, 52, 74, 2.1),
]
GROUP_A = ("L1", "R2", "L3", "R4")
SIDE = {"L": 1, "R": -1}


def _leg_specs():
    out = []
    for (n, x, z, yaw, lf, af, lt, at, am, th) in SP_LEGS_L:
        out.append((n, x, z, yaw, lf, af, lt, at, am, th))
        out.append(("R" + n[1], x, -z, 360 - yaw, lf * 0.98, af - 1, lt * 1.01, at + 1, am, th))
    return out


SP_LEGS = _leg_specs()


def _leg_points(lf, af, lt, at, am, y0):
    """In the leg's plane (u outward from the root, y up): the knee, the ankle, and the metatarsus length that puts the
    foot on the floor."""
    ku, ky = lf * math.cos(math.radians(af)), y0 - lf * math.sin(math.radians(af))
    au, ay = ku + lt * math.cos(math.radians(at)), ky - lt * math.sin(math.radians(at))
    lm = (ay - 0.4) / math.sin(math.radians(am))
    return (ku, ky), (au, ay), lm


def leg_ik(spec, dy=0.0, du=0.0):
    """The femur, tibia and metatarsus z rotations (on top of their rest) that keep a leg's foot where it stands when the
    root moves `dy` up and `du` outward (in the leg's plane): the ankle is put back where it was with the metatarsus
    kept at its angle, by the two-link solution with the knee up."""
    (n, x, z, yaw, lf, af, lt, at, am, th) = spec
    (ku, ky), (au, ay), lm = _leg_points(lf, af, lt, at, am, SP_ROOT_Y)
    # The ankle as seen from the moved root
    tu, ty = au - du, (ay - SP_ROOT_Y) - dy
    d = math.hypot(tu, ty)
    d = min(d, lf + lt - 0.01)
    # angle at the root between the femur and the line to the ankle
    cos_a = (lf * lf + d * d - lt * lt) / (2 * lf * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    base = math.atan2(ty, tu)                     # up is +y here
    femur = base + a                              # knee up
    k2u, k2y = lf * math.cos(femur), lf * math.sin(femur)
    tib = math.atan2(ty - k2y, tu - k2u)
    # Back to the rig's angles (positive: down): af' = -femur, at' = -tib
    af2, at2 = -math.degrees(femur), -math.degrees(tib)
    d_f = af2 - af
    d_t = (at2 - af2) - (at - af)
    d_m = (am - at2) - (am - at)
    return d_f, d_t, d_m


def leg_pose(spec, dy=0.0, du=0.0, lift=0.0, swing=0.0, curl=0.0):
    """Poses for a leg's three segments: the foot kept on the floor for a root moved by dy, du (leg_ik), then lifted
    (degrees of femur raise), swung fore (+) or aft (-) in degrees, and curled in (degrees at each joint)."""
    n = spec[0]
    side = SIDE[n[0]]
    d_f, d_t, d_m = leg_ik(spec, dy, du) if (dy or du) else (0.0, 0.0, 0.0)
    return {
        f"Femur{n}": pose((0, -side * swing, d_f - lift - curl * 0.4)),
        f"Tibia{n}": pose((0, 0, d_t + lift * 0.45 + curl)),
        f"Meta{n}": pose((0, 0, d_m + lift * 0.3 + curl * 0.8)),
    }


def _du_for(spec, ox):
    """How far a body offset along x moves a leg's root outward in its plane (its yaw from -X toward +Z)."""
    yaw = math.radians(spec[3])
    return ox * -math.cos(yaw)


# ---------------------------------------------------------------- The model

@lit(reach=(0.5, 1.2, 2.4), ground=0.12, ground_h=4.0, round_px=3.0, floor=12.0, skip=(sp_eye, sp_fang))
def giantspider():
    m = Model("giantspider", atlas_width=128, seed=88)

    # ---- The cephalothorax: the root ----
    body = m.part("Body", (-10.5, 8.5, -5.5), (12.5, 5.5, 11), pivot=(-2.0, 11.5, 0), paint=sp_carapace)
    m.part("CarapaceTop", (-9.5, 13.8, -4.6), (10.5, 1.4, 9.2), pivot=(-4, 14, 0), parent=body, paint=sp_carapace)
    m.part("CarapaceRear", (1.5, 9.0, -4.2), (1.6, 4.4, 8.4), parent=body, paint=sp_carapace)
    m.part("Sternum", (-9.0, 7.9, -4.0), (9.5, 0.8, 8.0), parent=body, paint=sp_coxa)
    head = m.part("Head", (-12.6, 9.2, -4.3), (2.4, 5.2, 8.6), pivot=(-10.5, 11.5, 0), parent=body, paint=sp_head)
    mound = m.part("EyeMound", (-12.0, 14.0, -2.8), (4.0, 2.0, 5.6), pivot=(-10, 15, 0), parent=body, rest=(0, 0, -6), paint=sp_mound)

    # ---- Eight eyes ----
    # Anterior median: the big pair, staring forward
    m.part("EyeAML", (-13.15, 12.2, 0.35), (0.7, 1.9, 1.9), pivot=(-12.8, 13.1, 1.3), parent=head, paint=sp_eye, glow=90, tag={"big": True})
    m.part("EyeAMR", (-13.15, 12.2, -2.25), (0.7, 1.9, 1.9), pivot=(-12.8, 13.1, -1.3), parent=head, paint=sp_eye, glow=90, tag={"big": True})
    # Anterior lateral: smaller, beside and below
    m.part("EyeALL", (-12.95, 11.7, 2.6), (0.6, 1.1, 1.1), pivot=(-12.6, 12.2, 3.1), parent=head, rest=(0, -25, 0), paint=sp_eye, glow=70)
    m.part("EyeALR", (-12.95, 11.7, -3.7), (0.6, 1.1, 1.1), pivot=(-12.6, 12.2, -3.1), parent=head, rest=(0, 25, 0), paint=sp_eye, glow=70)
    # Posterior median: on top of the mound, looking up and ahead
    m.part("EyePML", (-11.4, 15.8, 0.4), (1.3, 0.6, 1.3), pivot=(-10.7, 16, 1.0), parent=mound, paint=sp_eye, glow=70)
    m.part("EyePMR", (-11.4, 15.8, -1.7), (1.3, 0.6, 1.3), pivot=(-10.7, 16, -1.0), parent=mound, paint=sp_eye, glow=70)
    # Posterior lateral: on the mound's sides, looking out
    m.part("EyePLL", (-10.9, 14.6, 2.75), (1.2, 1.0, 0.55), pivot=(-10.3, 15.1, 3.0), parent=mound, paint=sp_eye, glow=70, tag={"look": "south"})
    m.part("EyePLR", (-10.9, 14.6, -3.3), (1.2, 1.0, 0.55), pivot=(-10.3, 15.1, -3.0), parent=mound, paint=sp_eye, glow=70, tag={"look": "north"})

    # ---- Chelicerae, the fangs folded under them, and the pedipalps ----
    for side, z in (("L", 1.6), ("R", -1.6)):
        che = m.part(f"Chelicera{side}", (-14.0, 5.8, z - 1.45), (2.9, 5.6, 2.9), pivot=(-12.4, 11.2, z), parent=head,
                     rest=(0, 0, -12), paint=sp_chelicera)
        m.part(f"Fang{side}", (-14.3, 5.2, z - 0.45 - (0.4 if side == "L" else -0.4)), (0.9, 2.6, 0.9), pivot=(-13.6, 6.4, z),
               parent=che, rest=((30 if side == "L" else -30), 0, -20), paint=sp_fang)
        sz = SIDE[side]
        palp = m.part(f"Palp{side}", (-18.5, 9.4, z + sz * 2.6 - 0.75), (6.0, 1.5, 1.5), pivot=(-12.5, 10.2, z + sz * 2.6), parent=head,
                      rest=(0, -sz * 18, 22), paint=sp_palp, tag={"band": 0.2, "spines": 1})
        m.part(f"PalpTip{side}", (-22.5, 9.5, z + sz * 2.6 - 0.8), (4.2, 1.3, 1.6), pivot=(-18.4, 10.2, z + sz * 2.6), parent=palp,
               rest=(0, 0, 38), paint=sp_palp, tag={"bulb": True, "band": 0.1, "spines": 1})

    # ---- The pedicel and the abdomen, carried a little raised ----
    m.part("Pedicel", (1.8, 9.6, -1.8), (3.4, 2.8, 3.6), parent=body, paint=sp_pedicel)
    abd = m.part("Abdomen", (4.0, 7.4, -6.0), (15.5, 10.0, 12.0), pivot=(4.5, 11.5, 0), parent=body, rest=(0, 0, 7),
                 paint=sp_abdomen, tag={"folium": True})
    # Rounded off: a crown over the back, flanks, a tapering rear and a belly, each a step in from the last
    m.part("AbdomenCrown", (5.5, 17.4, -4.8), (12.5, 1.6, 9.6), pivot=(11, 18, 0), parent=abd, paint=sp_abdomen, tag={"folium": True})
    m.part("AbdomenRidge", (8.0, 19.0, -3.0), (7.5, 0.9, 6.0), parent=abd, paint=sp_abdomen)
    m.part("AbdomenFlankL", (5.5, 8.6, 6.0), (12.5, 7.6, 1.3), parent=abd, paint=sp_abdomen)
    m.part("AbdomenFlankR", (5.5, 8.6, -7.3), (12.5, 7.6, 1.3), parent=abd, paint=sp_abdomen)
    m.part("AbdomenRear", (19.5, 8.3, -4.8), (1.8, 8.2, 9.6), parent=abd, paint=sp_abdomen)
    m.part("AbdomenTip", (21.3, 9.6, -3.0), (1.3, 5.4, 6.0), parent=abd, paint=sp_abdomen)
    m.part("AbdomenFront", (3.0, 8.6, -4.8), (1.2, 7.6, 9.6), parent=abd, paint=sp_abdomen)
    m.part("AbdomenBelly", (5.5, 6.3, -4.8), (12.5, 1.2, 9.6), parent=abd, paint=sp_abdomen, tag={"folium": True})
    for side, z in (("L", 0.4), ("R", -1.6)):
        m.part(f"Spinneret{side}", (21.0, 7.6, z), (1.8, 1.4, 1.2), pivot=(21, 8.3, z + 0.6), parent=abd, rest=(0, 0, -20), paint=sp_spinneret)

    # ---- The legs ----
    for spec in SP_LEGS:
        (n, x, z, yaw, lf, af, lt, at, am, th) = spec
        y0 = SP_ROOT_Y
        hip = m.part(f"Coxa{n}", (x - 1.8, y0 - 1.8, z - 1.8), (3.6, 3.4, 3.6), pivot=(x, y0, z), parent=body, rest=(0, yaw, 0), paint=sp_coxa)
        _, _, lm = _leg_points(lf, af, lt, at, am, y0)
        r0 = 1.2
        femur = m.part(f"Femur{n}", (x - r0 - lf, y0 - th / 2, z - th / 2), (lf + 1.2, th, th), pivot=(x - r0, y0, z), parent=hip,
                       rest=(0, 0, af), paint=sp_leg, tag={"band": 0.14, "root_band": 0.08, "spines": 2})
        t2 = th * 0.86
        tib = m.part(f"Tibia{n}", (x - r0 - lf - lt, y0 - t2 / 2, z - t2 / 2), (lt + 1.0, t2, t2), pivot=(x - r0 - lf, y0, z), parent=femur,
                     rest=(0, 0, at - af), paint=sp_leg, tag={"band": 0.16, "root_band": 0.12, "spines": 4})
        # The patella: the knuckle of the knee
        m.part(f"Knee{n}", (x - r0 - lf - th * 0.6, y0 - th * 0.62, z - th * 0.62), (th * 1.2, th * 1.24, th * 1.24), pivot=(x - r0 - lf, y0, z),
               parent=femur, rest=(0, 0, (at - af) / 2), paint=sp_leg, tag={"band": 0.0, "root_band": 0.0, "spines": 0})
        t3 = th * 0.62
        m.part(f"Meta{n}", (x - r0 - lf - lt - lm, y0 - t3 / 2, z - t3 / 2), (lm + 0.8, t3, t3), pivot=(x - r0 - lf - lt, y0, z), parent=tib,
               rest=(0, 0, am - at), paint=sp_leg, tag={"band": 0.08, "root_band": 0.14, "spines": 3, "claw": True})

    # Centre the body and abdomen over the entity's position
    m.shift(dx=-3.5)

    leg_names = [f"{seg}{spec[0]}" for spec in SP_LEGS for seg in ("Femur", "Tibia", "Meta")]
    jaw_names = ["CheliceraL", "CheliceraR", "FangL", "FangR"]
    palp_names = ["PalpL", "PalpR", "PalpTipL", "PalpTipR"]
    core = ["Body", "Abdomen", "EyeMound"]
    every = core + leg_names + jaw_names + palp_names
    spec_by = {spec[0]: spec for spec in SP_LEGS}

    def palps(p, amp, up=0.0):
        return {"PalpL": pose((s(p * 3, amp * 0.6), s(p * 2, amp), up + s(p * 3, amp, 0.3))),
                "PalpR": pose((s(p * 3, amp * 0.6, 0.5), s(p * 2, amp, 0.5), up + s(p * 3, amp, 0.8))),
                "PalpTipL": pose((0, 0, s(p * 4, amp * 0.8, 0.2))), "PalpTipR": pose((0, 0, s(p * 4, amp * 0.8, 0.7)))}

    def jaws(spread, fang):
        # (Spread: the jaws' feet swing apart; fang: the fangs unfold outward and forward)
        return {"CheliceraL": pose((-spread, 0, 0)), "CheliceraR": pose((spread, 0, 0)),
                "FangL": pose((-fang, 0, -fang * 0.4)), "FangR": pose((fang, 0, -fang * 0.4))}

    def body_at(dy=0.0, ox=0.0, pitch=0.0, roll=0.0, abd=0.0, lifts=None, swings=None, curls=None):
        """The body moved, pitched nose up (degrees) and rolled onto its right side, every leg's foot kept on the floor
        but for those lifted, swung or curled."""
        d = {"Body": pose((roll, 0, -pitch), (ox, dy, 0)), "Abdomen": pose((0, 0, abd))}
        for spec in SP_LEGS:
            n = spec[0]
            # A pitch about the body's pivot raises the roots in front of it (rx < 0) and lowers those behind; a roll
            # lowers the left (+z) side
            rx = spec[1] - 3.5 - (-5.5)
            pdy = dy - rx * math.sin(math.radians(pitch)) - spec[2] * math.sin(math.radians(roll))
            du = _du_for(spec, ox)
            d.update(leg_pose(spec, pdy, du, lift=(lifts or {}).get(n, 0.0), swing=(swings or {}).get(n, 0.0), curl=(curls or {}).get(n, 0.0)))
        return d

    # ---- Idle: breathing, the palps feeling, now and then a leg settling ----
    def idle(p):
        b = 0.015 * math.sin(TAU * p * 2)
        d = body_at(dy=0.25 * math.sin(TAU * p * 2), abd=1.2 * math.sin(TAU * p * 2 + 0.6),
                    lifts={"L2": 10 * ramp(p, 0.3, 0.36, 0.42, 0.5), "R3": 8 * ramp(p, 0.7, 0.76, 0.8, 0.88)})
        d["Abdomen"] = pose((0, 0, 1.2 * math.sin(TAU * p * 2 + 0.6)), s=(1 + b, 1 + b * 1.4, 1 + b))
        d.update(palps(p, 6))
        d.update(jaws(2 * max(0, math.sin(TAU * p * 3)), 0))
        return d

    m.animation("idle", 120, {f: full(every, d) for f, d in cycle(120, 24, idle).items()})

    # ---- Lurk: low on its legs, the first pair held out in front and feeling, palps twitching, quite still ----
    def lurk(p):
        lift = {"L1": 22 + 4 * s(p * 2, 1), "R1": 20 + 4 * s(p * 2, 1, 0.4)}
        swing = {"L1": 10 + 5 * s(p, 1), "R1": 8 + 5 * s(p, 1, 0.5)}
        d = body_at(dy=-3.4, pitch=-3, abd=-3 + 0.8 * math.sin(TAU * p), lifts=lift, swings=swing)
        d.update(palps(p, 9, up=-8))
        d.update(jaws(0, 0))
        return d

    m.animation("lurk", 80, {f: full(every, d) for f, d in cycle(80, 16, lurk).items()})

    # ---- Walk and run: alternating tetrapods. A leg lifts, swings forward and comes down; the rest push back ----
    def gait(p, fwd, lift_deg, bob, dy=0.0, pitch=0.0, duty=0.5):
        lifts, swings = {}, {}
        for spec in SP_LEGS:
            n = spec[0]
            q = (p + (0.0 if n in GROUP_A else 0.5)) % 1.0
            if q < 1 - duty:
                t = q / (1 - duty)
                lifts[n] = lift_deg * math.sin(math.pi * t)
                swings[n] = fwd * (-1 + 2 * (t * t * (3 - 2 * t)))
            else:
                t = (q - (1 - duty)) / duty
                swings[n] = fwd * (1 - 2 * t)
        d = body_at(dy=dy + bob * abs(math.sin(TAU * p)), pitch=pitch, roll=1.5 * math.sin(TAU * p), abd=2 * math.sin(TAU * p * 2),
                    lifts=lifts, swings=swings)
        d.update(palps(p, 8))
        return d

    m.animation("walk", 40, {f: full(every, d) for f, d in cycle(40, 20, lambda p: gait(p, 13, 24, 0.4)).items()})
    m.animation("run", 20, {f: full(every, d) for f, d in cycle(20, 20, lambda p: gait(p, 18, 30, 0.7, dy=-1.2, pitch=-3, duty=0.45)).items()})

    # ---- Rear: the threat display. Up on its hind legs, the first two pairs and the palps raised, fangs out ----
    def rear(k, tremble=0.0):
        lifts = {"L1": 62 * k, "R1": 62 * k, "L2": 40 * k, "R2": 40 * k}
        swings = {"L1": 20 * k, "R1": 20 * k, "L2": 12 * k, "R2": 12 * k}
        d = body_at(dy=1.5 * k, pitch=18 * k + tremble, abd=10 * k, lifts=lifts, swings=swings)
        d.update(palps(0.25, 4, up=-30 * k))
        d.update(jaws(14 * k, 35 * k))
        return d

    m.animation("rear", 30, {0: full(every, rear(0)), 6: full(every, rear(0.8)), 9: full(every, rear(1.0)),
                             14: full(every, rear(1.0, 1.5)), 19: full(every, rear(1.0, -1.0)), 24: full(every, rear(1.0, 1.0)),
                             29: full(every, rear(1.0))}, end="Hold")

    # ---- Attack (27 frames, 0.9 s; the bite lands at 450 ms, frame 13): rears back, lunges, the fangs stab down ----
    def strike(up, lunge, fang, spread):
        lifts = {"L1": 50 * up + 10 * lunge, "R1": 50 * up + 10 * lunge, "L2": 25 * up, "R2": 25 * up}
        swings = {"L1": 24 * up + 14 * lunge, "R1": 24 * up + 14 * lunge, "L2": 10 * up, "R2": 10 * up}
        d = body_at(dy=1.2 * up - 1.4 * lunge, ox=-3.2 * lunge, pitch=14 * up - 12 * lunge, abd=8 * up - 4 * lunge, lifts=lifts, swings=swings)
        d.update(palps(0.25, 3, up=-24 * up + 10 * lunge))
        d.update(jaws(spread, fang))
        return d

    m.animation("attack", 27, {
        0: full(every, strike(0, 0, 0, 0)),
        5: full(every, strike(0.8, 0, 30, 14)),           # back and up, fangs opening
        9: full(every, strike(1.0, 0, 42, 18)),
        12: full(every, strike(0.1, 1.0, 10, 6)),         # the lunge
        14: full(every, strike(0.0, 1.1, -10, 0)),        # the fangs driven in: frame 13-14
        19: full(every, strike(0.0, 0.6, -6, 0)),
        26: full(every, strike(0, 0, 0, 0)),
    }, end="Stop")

    # ---- Hurt: it flinches, the legs drawing in, the body dropping ----
    def flinch(k):
        d = body_at(dy=-1.5 * k, pitch=4 * k, roll=3 * k, abd=6 * k, curls={spec[0]: 10 * k for spec in SP_LEGS})
        d.update(jaws(8 * k, 20 * k))
        return d

    m.animation("hurt", 16, {0: full(every, flinch(0)), 4: full(every, flinch(1.0)), 9: full(every, flinch(0.4)), 15: full(every, flinch(0))}, end="Stop")

    # ---- Death: the body sinks to the floor and the legs curl in under it, one pair after another ----
    def collapse(k):
        curls = {}
        order = ["L4", "R4", "L3", "R3", "L2", "R2", "L1", "R1"]
        for i, n in enumerate(order):
            curls[n] = 70 * min(1.0, max(0.0, k * 1.6 - i * 0.07))
        d = {"Body": pose((6 * k, 0, -4 * k), (0, -7.5 * k, 0)), "Abdomen": pose((0, 0, -9 * k))}
        for spec in SP_LEGS:
            # Each leg folds shut like a fist: the femur stands up, the tibia folds back in over the body and the
            # metatarsus hooks down
            n, c = spec[0], curls[spec[0]] / 70
            d[f"Femur{n}"] = pose((0, 0, -45 * c))
            d[f"Tibia{n}"] = pose((0, 0, 150 * c))
            d[f"Meta{n}"] = pose((0, 0, 55 * c))
        d.update(palps(0.25, 0, up=40 * k))
        d.update(jaws(0, 20 * k))
        return d

    m.animation("die", 60, {0: full(every, collapse(0)), 12: full(every, collapse(0.3)), 26: full(every, collapse(0.6)),
                            40: full(every, collapse(0.9)), 50: full(every, collapse(1.0)), 59: full(every, collapse(1.0))},
                end="Hold", stopped="Stop")
    return m


# ---------------------------------------------------------------- The entity type (gen_entities.py)

def entity(anim, common_client, server, drops=None):
    """The entity type: gen_entities' helpers passed in (anim, common_client, server)."""
    task = {"code": "backrooms-spider", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0,
            # (Speeds compare with a player's 0.025 walking and 0.05 sprinting; Level 8's danger adds a fifth: a sprint
            # and a bit, so the head start its rearing gives is what saves you)
            "walkSpeed": 0.016, "runSpeed": 0.05, "leash": 24,
            # What it notices by (the shared model, AiTaskSpider): someone within 5 blocks it will not stand (creeping
            # shrinks it to 55 %), a racket or a runner within 20. A loud noise (0.5) within 24 blocks of its nest's
            # heart wakes the whole nest (MenaceSystem.NestHeard)
            "senses": {"touch": 5.0, "hearing": 20, "sneakFactor": 0.55},
            "attackRange": 0.55, "damage": 3.5, "damageTier": 2, "knockback": 0.4,
            "attackDurationMs": 900, "damageAtMs": 450, "attackCooldownMs": 1500, "rearMs": 900,
            "venom": 0.5, "venomTicks": 5, "venomEveryMs": 1200, "retreatBelow": 0.25, "mendPerSecond": 0.25,
            "chitterSound": "backrooms:entity/chitter", "hissSound": "backrooms:entity/spiderhiss", "biteSound": "backrooms:entity/spiderbite"}
    animations = [
        anim("hurt", "hurt", 1.0, weight=10, blendMode="AddAverage"),
        anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
        anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage", easeOutSpeed=4),
        anim("walk", "walk", 1.0),
        anim("run", "run", 1.0),
        anim("attack", "attack", 1.0, weight=10),
        # (Weighted over the idle, which would otherwise lift it half off the floor)
        anim("lurk", "lurk", 1.0, weight=5),
        anim("rear", "rear", 1.0, weight=8),
    ]
    sv = server(20, [task], drops, menace={"stalkSeconds": 240, "huntSeconds": 150})
    return {
        "code": "giantspider",
        "class": "EntityGiantSpider",
        "tags": ["backrooms-entity", "habitat-land"],
        "weight": 120,
        # It climbs the cave walls, as the game's locusts do, and takes no harm from a fall
        "canClimb": True,
        "canClimbAnywhere": True,
        "climbTouchDistance": 0.1,
        "rotateModelOnClimb": True,
        "fallDamageMultiplier": 0.0,
        # The body is 2 blocks long and 1.1 tall; the legs spread over three and a half
        "hitboxSize": {"x": 1.3, "y": 1.1},
        "deadHitboxSize": {"x": 1.3, "y": 0.5},
        # (The game culls a body by its selection box, and the legs reach a block past the hitbox all round; it is
        # also what a blow must hit)
        "selectionBoxSize": {"x": 2.2, "y": 1.2},
        "eyeHeight": 0.8,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-giantspider"},
        "client": common_client("backrooms:entity/giantspider", {"base": "backrooms:entity/giantspider"}, animations),
        "server": sv,
        "sounds": {"hurt": "backrooms:entity/spiderhurt", "death": "backrooms:entity/spiderdeath"},
    }


LANG = {
    "item-creature-giantspider": "Giant Spider",
    "prefixandcreature-giantspider": "a Giant Spider",
    "deadcreature-giantspider": "Killed by a Giant Spider",
}
