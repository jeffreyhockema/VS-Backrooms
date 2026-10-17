"""Level Fun =)'s entity models (docs/design/new-levels/fun-plan.md, 4.4), built with rig.py and the helpers of gen_models.py.

- The Partygoer (Entity 67), after the Wikidot page and its two canon drawings (Daniel Kebab's first sketch and Myra
  Oberlyn's berserker diagram): a Gumby slab of bright yellow leathery skin, head and body one piece with the top
  rolled over to one side, a carved and bloody "=)" for a face, long thick noodle arms bowed out at the elbow and
  ending in flared lamprey mouths ringed with hooked teeth, long blocky slab legs. A subtle carapace over the chest
  opens like a pair of doors (their insides lined with hooks) on a wet cavity: the black Phobic Centipede curled in
  it, its inverted grinning face with softly glowing eyes, and its two long black arms folded up, which unfold in
  berserker mode into whip-long reaches ending in three sickle talons. Interns carry a red balloon on a string.
- The lure balloon: a red latex balloon floating on its own at head height, its string hanging free ("almost always
  bait").
- The Party Host (Level 26): "a huge monster filling the ceiling ... like a golden fried egg with an eye-and-mouth
  combination in the middle", into whose maw the Partygoers feed Facelings. A pale fleshy white with crisp golden
  lace at its edge, a glossy golden yolk dome, and at its crown one organ that is both: a huge eye between a lashed
  lid and a toothed jaw. Its LUCA tears hang from the corners of the eye.

Conventions as rig.py: models face -X, the left is +Z, feet at y = 0, 16 px to a block.
Written to shapes/entity/fun-*.json and textures/entity/fun-*.png. Run through gen_fun.py, or alone:
    bash tools/locked.sh run python tools/gen_fun_models.py [name ...]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import rig  # noqa: E402
from rig import ASSETS, Model, fill, speckle, mix, shade, clamp, pose  # noqa: E402
from gen_models import blotch, line, texel, cycle, full, s, ramp  # noqa: E402

TAU = math.tau

# ======================================================================== Partygoer palette (variants swap these)
SKIN = (236, 204, 44)        # bright yellow
MOTTLE = (208, 168, 32)      # leathery mottling
SHEEN = (250, 230, 124)      # sheen
CARVE = (58, 6, 6)           # the carved smile's dark inside
BLOOD = (122, 16, 16)
BLOOD_HI = (160, 24, 24)
CHITIN = (26, 24, 30)        # the Phobic Centipede: "a non-reflective black"
CHITIN_HI = (66, 70, 88)     # the diagram's grey-blue sheen
CAVITY = (110, 20, 32)
FLESH = (156, 52, 62)
TEETH = (232, 224, 200)
BALLOON = (226, 34, 40)
BALLOON_DARK = (150, 14, 24)
BALLOON_HI = (255, 196, 196)

VARIANTS = {
    "red": dict(SKIN=(200, 51, 43), MOTTLE=(170, 38, 34), SHEEN=(230, 104, 92)),
    "blue": dict(SKIN=(47, 111, 208), MOTTLE=(36, 88, 172), SHEEN=(112, 162, 238)),
    "green": dict(SKIN=(63, 163, 77), MOTTLE=(48, 132, 60), SHEEN=(122, 208, 132)),
    "white": dict(SKIN=(232, 232, 224), MOTTLE=(204, 202, 190), SHEEN=(250, 250, 246)),
}

SIDES = ("north", "south", "east", "west")


def grade(ctx, top=1.04, bottom=0.93):
    """A soft vertical light down a side face: a little brighter at its top, a little darker at its foot."""
    if ctx.face not in SIDES or ctx.h < 3:
        return
    px = ctx.img.load()
    for yy in range(ctx.h):
        k = top + (bottom - top) * yy / (ctx.h - 1)
        for xx in range(ctx.w):
            c = px[ctx.x + xx, ctx.y + yy]
            px[ctx.x + xx, ctx.y + yy] = clamp((c[0] * k, c[1] * k, c[2] * k)) + (255,)


def pg_skin(ctx, blood=0.0):
    """Smooth leathery skin: a clean bright base, slow mottling, a few faint creases, softly rounded edges, a sheen on
    top faces; blood if asked."""
    fill(ctx, SKIN, 0.03)
    grade(ctx)
    blotch(ctx, MOTTLE, 1 + ctx.w * ctx.h // 160, 1.5, 4.0, 0.22)
    blotch(ctx, SHEEN, 1, 1.0, 3.0, 0.22)
    for _ in range(ctx.w * ctx.h // 90):  # leather creases: short faint lines, mostly across
        u, v = ctx.rng.random(), ctx.rng.random()
        line(ctx, u, v, min(1, u + ctx.rng.uniform(0.08, 0.3)), min(1, v + ctx.rng.uniform(-0.04, 0.04)), MOTTLE, 0.22)
    if ctx.face in SIDES and ctx.w >= 6 and ctx.h >= 4:  # the slab's edges roll away from the light
        for yy in range(ctx.h):
            texel(ctx, 0, yy, MOTTLE, 0.3)
            texel(ctx, -1, yy, MOTTLE, 0.3)
    if ctx.face == "up":
        speckle(ctx, SHEEN, 0.06)
    if blood > 0 and ctx.face in ("west", "north", "south", "up", "down"):
        bleed(ctx, blood)


def bleed(ctx, amount):
    """Blood: runs down a face from its top, and a smear or two."""
    for _ in range(int(1 + amount * 3)):
        x = ctx.rng.randrange(ctx.w)
        length = int(ctx.h * ctx.rng.uniform(0.3, 0.9) * amount)
        for y in range(length):
            texel(ctx, x, y, BLOOD if y < length - 1 else BLOOD_HI, 0.85)
            if ctx.rng.random() < 0.3 and x + 1 < ctx.w:
                texel(ctx, x + 1, y, BLOOD, 0.6)
    blotch(ctx, BLOOD, 1, 1.0, 2.5, 0.5 * amount)


def pg_body(ctx):
    pg_skin(ctx, ctx.part.tag.get("blood", 0.0))


def pg_flesh(ctx):
    """Raw wet flesh: the walls of the chest cavity."""
    fill(ctx, CAVITY, 0.1)
    blotch(ctx, FLESH, 1 + ctx.w * ctx.h // 40, 1.0, 2.5, 0.5)
    for _ in range(max(1, ctx.w * ctx.h // 30)):  # veins
        u, v = ctx.rng.random(), ctx.rng.random()
        line(ctx, u, v, u + ctx.rng.uniform(-0.3, 0.3), v + ctx.rng.uniform(0.1, 0.4), (60, 8, 16), 0.6)
    speckle(ctx, (200, 110, 110), 0.04)


def pg_torso(ctx):
    """The torso's own front is the back wall of the cavity behind the carapace; the rest is skin."""
    if ctx.face == "west":
        pg_flesh(ctx)
    else:
        pg_body(ctx)


def pg_frame(ctx):
    """The rim of skin round the chest opening: skin outside, flesh on the faces into the opening."""
    if ctx.face in ctx.part.tag.get("inner", ()):
        pg_flesh(ctx)
    else:
        pg_body(ctx)


def pg_faceplate(ctx):
    """The skin over the face: skin on the front, with blood run down under the grin; raw cut flesh on the walls of the carving."""
    if ctx.face in ctx.part.tag.get("outer", ()):
        pg_skin(ctx)
        return
    if ctx.face != "west":
        fill(ctx, (104, 14, 16), 0.12, face_shade=False)
        return
    pg_skin(ctx)
    for u in ctx.part.tag.get("runs", []):
        x = int(u * ctx.w)
        length = max(1, int(ctx.h * ctx.rng.uniform(0.4, 1.0)))
        for y in range(length):
            texel(ctx, x, y, BLOOD if y < length - 1 else BLOOD_HI, 0.8 if ctx.rng.random() < 0.7 else 0.5)


def pg_carved(ctx):
    """The inside of the carving: dark maroon, wetter in the middle."""
    fill(ctx, CARVE, 0.12)
    blotch(ctx, (90, 12, 14), 1, 1.0, 2.5, 0.4)


def pg_carapace(ctx):
    """The chest plates: skin hardened toward amber chitin in overlapping bands, blood run down them; inside, flesh
    lined with rows of little hooks (the diagram's door)."""
    hard = mix(SKIN, (176, 120, 36), 0.3)
    if ctx.face == "east":
        fill(ctx, CAVITY, 0.1, face_shade=False)
        blotch(ctx, FLESH, 2, 1.0, 2.0, 0.4)
        for yy in range(1, ctx.h - 2, 4):
            for xx in range(1 + (yy // 4) % 2 * 2, ctx.w - 1, 4):
                if ctx.rng.random() < 0.8:
                    texel(ctx, xx, yy, (222, 208, 182))
                    texel(ctx, xx, yy + 1, (190, 160, 150))
                    texel(ctx, xx + 1, yy + 1, (222, 208, 182), 0.7)
        return
    fill(ctx, hard, 0.04)
    grade(ctx, 1.06, 0.9)
    if ctx.face == "west":
        for yy in range(2, ctx.h, 3):  # the bands: a dark seam under a lit lip
            for xx in range(ctx.w):
                texel(ctx, xx, yy, shade(hard, 0.72), 0.9)
                texel(ctx, xx, yy - 1, mix(hard, SHEEN, 0.5), 0.5)
        bleed(ctx, 0.55)
    else:
        rig.hlines(ctx, shade(hard, 0.75), 3, 2, 0.8)


def pg_chitin(ctx):
    """The centipede's arms: matte black segments with a grey-blue sheen along their tops, joints ringed."""
    fill(ctx, CHITIN, 0.12)
    if ctx.face in ("up", "west", "north", "south") and ctx.w >= 2:
        for xx in range(0, ctx.w):
            if ctx.rng.random() < 0.5:
                texel(ctx, xx, 0, CHITIN_HI, 0.7)
    if ctx.face in SIDES or ctx.face in ("up", "down"):
        n = ctx.part.tag.get("rings", 0)
        for i in range(1, n + 1):
            tx = int(ctx.w * i / (n + 1))
            for yy in range(ctx.h):
                texel(ctx, tx, yy, (8, 6, 10), 0.9)
                if tx + 1 < ctx.w:
                    texel(ctx, tx + 1, yy, CHITIN_HI, 0.35)


def pg_talon(ctx):
    """A sickle talon: black at the root, darkening to a bloody tip."""
    tip = ctx.part.tag.get("tip", False)
    fill(ctx, (40, 30, 36) if not tip else (96, 20, 40), 0.08)
    if ctx.face in SIDES:
        for yy in range(ctx.h):
            texel(ctx, 0, yy, CHITIN_HI if not tip else (170, 40, 70), 0.6)
    if tip and ctx.face in ("west", "down"):
        texel(ctx, 0, ctx.h - 1, (210, 200, 180))


def pg_centipede(ctx):
    """The Phobic Centipede curled in the cavity: black segments, pale little legs at their sides."""
    fill(ctx, CHITIN, 0.12)
    if ctx.face == "west":
        texel(ctx, 0, 0, CHITIN_HI, 0.6)
        for yy in range(ctx.h):
            texel(ctx, 0, yy, (190, 170, 150), 0.5 if yy % 2 else 0.0)
            texel(ctx, -1, yy, (190, 170, 150), 0.5 if yy % 2 == 0 else 0.0)


def pg_innerface(ctx):
    """The Phobic Centipede's face, upside down: pale, grey-green, grinning (its eyes are their own glowing parts)."""
    fill(ctx, (176, 190, 160), 0.06)
    if ctx.face == "west":
        w, h = ctx.w, ctx.h
        # Upside down: the grin is at the top, curving the "wrong" way
        for xx in range(1, w - 1):
            texel(ctx, xx, 1, (60, 10, 14))
        texel(ctx, 0, 2, (60, 10, 14))
        texel(ctx, w - 1, 2, (60, 10, 14))
        for xx in range(1, w - 1, 2):
            texel(ctx, xx, 1, TEETH, 0.8)
        texel(ctx, w // 2, h // 2 + 1, (130, 140, 116))  # a nose
        # hair hangs up from what is now its chin side, into the cavity's top (the canon: "including human hair")
    if ctx.face == "up":
        speckle(ctx, (40, 30, 26), 0.5)


def pg_innereye(ctx):
    fill(ctx, (240, 244, 236), 0.02, face_shade=False)


def pg_sucker(ctx):
    """The arm's last swell before the mouth: skin bloodied toward its end."""
    pg_skin(ctx, 0.9)
    if ctx.face in SIDES:
        rig.hlines(ctx, (150, 40, 40), ctx.h, ctx.h - 1, 0.6)


def pg_lip(ctx):
    """The lamprey mouth's flared rim: red raw lips, and on its end a red-black throat ringed with hooked teeth."""
    if ctx.face == "down":
        fill(ctx, (110, 16, 26), 0.08, face_shade=False)
        cx, cy = (ctx.w - 1) / 2, (ctx.h - 1) / 2
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                d = math.hypot((xx - cx) / max(1, cx), (yy - cy) / max(1, cy))
                a = math.atan2(yy - cy, xx - cx)
                if d < 0.32:
                    texel(ctx, xx, yy, (22, 2, 6))
                elif d < 0.95 and math.cos(a * 8) > 0.55 and d > 0.4:
                    texel(ctx, xx, yy, TEETH)  # the teeth, in a star round the throat
                elif d < 0.5:
                    texel(ctx, xx, yy, (60, 6, 12))
        return
    fill(ctx, (150, 34, 40), 0.1)
    if ctx.face == "up":
        speckle(ctx, SKIN, 0.3)


def pg_tooth(ctx):
    fill(ctx, TEETH, 0.05)
    if ctx.face in SIDES:
        texel(ctx, 0, -1, (150, 60, 60), 0.6)


def pg_balloon(ctx):
    """Glossy red latex, shaded as one round body across all its boxes: darker below, a hot highlight up at the
    front-left, a rim of reflected light low on the back."""
    y0, y1 = ctx.part.tag.get("y0", 0.0), ctx.part.tag.get("y1", 1.0)
    p = ctx.part
    px = ctx.img.load()
    for yy in range(ctx.h):
        if ctx.face in SIDES:
            wy = p.frm[1] + p.size[1] * (1 - (yy + 0.5) / ctx.h)
        else:
            wy = p.to[1] if ctx.face == "up" else p.frm[1]
        t = max(0.0, min(1.0, (wy - y0) / max(0.01, y1 - y0)))
        base = mix(BALLOON_DARK, BALLOON, min(1.0, 0.35 + t * 1.1))
        if ctx.face == "up":
            base = mix(base, (236, 80, 80), 0.25)
        if ctx.face == "down":
            base = shade(base, 0.8)
        for xx in range(ctx.w):
            v = 1 + 0.03 * (ctx.rng.random() - 0.5)
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(c * v for c in base)) + (255,)
    if ctx.part.tag.get("hi") and ctx.face in ("west", "south", "up"):
        hu, hv = (0.3, 0.3) if ctx.face != "up" else (0.35, 0.35)
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                d = math.hypot((xx + 0.5) / ctx.w - hu, ((yy + 0.5) / ctx.h - hv) * 0.8)
                if d < 0.17:
                    texel(ctx, xx, yy, BALLOON_HI, 0.9 * (1 - d / 0.17) + 0.1)
    if ctx.part.tag.get("knot"):
        fill(ctx, shade(BALLOON, 0.75), 0.05)


def pg_string(ctx):
    fill(ctx, (236, 232, 224), 0.03, face_shade=False)


def balloon(m, root, centre, pivot, parent=None):
    """A latex balloon as voxels: an egg 6.6 across and 7.6 tall, widest a little above its middle, built in round
    layers (a square with a cross through it), and a knot below. The widest layer is the root part `root` with its
    bars `root`+X and Z; the others are `root`+0..5 (+X, Z) and `root`+Knot. Returns the root."""
    cx, cy, cz = centre
    T = dict(y0=cy - 3.8, y1=cy + 3.8)
    P = dict(pivot=pivot, paint=pg_balloon)
    layers = [(-3.8, -3.2, 1.3), (-3.2, -2.2, 2.2), (-2.2, -0.8, 2.9), (-0.8, 2.2, 3.3), (2.2, 3.2, 2.8), (3.2, 3.8, 1.8)]
    core = None
    for i in (3, 0, 1, 2, 4, 5):  # the widest layer first: it is the root the rest hang from
        a, b, r = layers[i]
        nm = root if i == 3 else f"{root}{i}"
        tg = dict(T)
        sq = r * (0.72 if r > 2 else 0.85)
        part = m.part(nm, (cx - sq, cy + a, cz - sq), (2 * sq, b - a, 2 * sq), parent=core if core is not None else parent, tag=tg, **P)
        if i == 3:
            tg = dict(T, hi=True)  # the highlight: once on each outermost face of the widest layer
        core = core or part
        if r > 2:
            w = r * 0.6
            m.part(nm + "X", (cx - r, cy + a, cz - w), (2 * r, b - a, 2 * w), parent=part, tag=tg, **P)
            m.part(nm + "Z", (cx - w, cy + a, cz - r), (2 * w, b - a, 2 * r), parent=part, tag=tg, **P)
    m.part(root + "Knot", (cx - 0.5, cy - 4.6, cz - 0.5), (1.0, 0.8, 1.0), parent=core, tag=dict(T, knot=True), **P)
    return core


# ======================================================================== Partygoer model

def rotm(x, y, z):
    """A rotation as the game composes an element's: X, then Y, then Z (degrees), as 3x3 rows."""
    a, b, c = math.radians(x), math.radians(y), math.radians(z)
    rx = [[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]]
    ry = [[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]]
    rz = [[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]]
    return matmul(matmul(rx, ry), rz)


def matmul(p, q):
    return [[sum(p[i][k] * q[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def transpose(p):
    return [[p[j][i] for j in range(3)] for i in range(3)]


def euler(r):
    """Back from a matrix to X, Y, Z degrees (r = Rx Ry Rz)."""
    b = math.asin(max(-1.0, min(1.0, r[0][2])))
    a = math.atan2(-r[1][2], r[2][2])
    c = math.atan2(-r[0][1], r[0][0])
    return (math.degrees(a), math.degrees(b), math.degrees(c))


# The noodle arms: four links, each thinner; rest bends bow the elbow out and bring the mouth back in by the thigh
ARM = [("Arm1", 2.0, 5.0), ("Arm2", 1.85, 4.6), ("Arm3", 1.7, 4.4), ("Arm4", 1.6, 3.8)]
ARM_REST = {"Arm1": (-20, 0, -4), "Arm2": (8, 0, -3), "Arm3": (12, 0, -6), "Arm4": (8, 0, 3)}
ARM_TOP, ARM_Z = 23.8, 4.45
THUMB_REST, THUMB_OPEN = 10, -40  # the opposed talon lies flat along the folded hand and opens when it unfolds
HAND_CURL = 90  # the centipede's hands rest turned in across the cavity, crossed; berserk straightens them


# The intern's balloon floats: whatever the body and the right arm do, the string's own rotation undoes it (the chain's
# rotations composed as the game composes them and inverted), so it stands up from the hand leaning a little out
PG_CHAIN = [("Pelvis", (0, 0, 0)), ("Torso", (0, 0, 5))] + [(f"{nm}R", (-ARM_REST[nm][0], -ARM_REST[nm][1], ARM_REST[nm][2])) for nm, _, _ in ARM]     + [("SuckerR", (0, 0, 0))]


def string_rot(d, bob=(0.0, 0.0)):
    mat = rotm(0, 0, 0)
    for n, rest in PG_CHAIN:
        a = d.get(n, {}).get("rot", (0, 0, 0))
        mat = matmul(mat, rotm(rest[0] + a[0], rest[1] + a[1], rest[2] + a[2]))
    return euler(matmul(transpose(mat), rotm(-13 + bob[0], 0, 3 + bob[1])))


STRING_REST = tuple(round(v, 3) for v in string_rot({}))


# B17: light baked from the rest pose (rig.bake): occlusion where the parts meet, round limbs, dark feet. The skin is
# already graded down each face (`grade`), so the bake's own gradient is light.
LIGHT = dict(grad=0.12, edge=0.06, foot=0.04)


def partygoer(intern=False):
    name = "fun-partygoer-intern" if intern else "fun-partygoer"
    m = Model(name, atlas_width=64, seed=67)
    m.light = dict(LIGHT)
    # Proportions after the canon drawings: legs nearly half the height, the head and body one slab, no neck, no
    # shoulders to speak of, the arms leaving the slab just under the face
    pelvis = m.part("Pelvis", (-2, 15, -3.75), (4, 3, 7.5), pivot=(0, 16.5, 0), paint=pg_body)
    m.part("Seat", (2, 15.2, -3.25), (0.8, 3.2, 6.5), pivot=(0, 16.5, 0), parent=pelvis, paint=pg_body)
    # The torso leans a little forward from the hips (a lanky hunch); the head tips back up to keep its face on you.
    # Its front 1.4 px is a frame of skin round the chest opening, the torso's own front the back wall of the cavity.
    torso = m.part("Torso", (-0.6, 18, -3.5), (2.6, 7, 7), pivot=(0, 18, 0), parent=pelvis, rest=(0, 0, 5), paint=pg_torso)
    tp = dict(pivot=(0, 18, 0), parent=torso)
    m.part("ChestTop", (-2, 24, -3.5), (1.4, 1.0, 7), paint=pg_frame, tag={"inner": ("down",), "blood": 0.6}, **tp)
    m.part("ChestBase", (-2, 18, -3.5), (1.4, 0.8, 7), paint=pg_frame, tag={"inner": ("up",)}, **tp)
    m.part("ChestSideL", (-2, 18.8, 2.9), (1.4, 5.2, 0.6), paint=pg_frame, tag={"inner": ("north",)}, **tp)
    m.part("ChestSideR", (-2, 18.8, -3.5), (1.4, 5.2, 0.6), paint=pg_frame, tag={"inner": ("south",)}, **tp)
    # The back is rounded and humped over the shoulder blades
    m.part("Back", (2, 18.4, -3.1), (1.1, 6.2, 6.2), paint=pg_body, **tp)
    m.part("Hump", (3.1, 20, -2.4), (0.7, 4.4, 4.8), paint=pg_body, **tp)
    m.part("Belly", (-2.4, 17.6, -3.0), (0.4, 1.2, 6.0), paint=pg_body, **tp)
    m.part("Neck", (-1.95, 24.4, -2.9), (4.1, 1.4, 5.8), paint=pg_body, **tp)
    m.part("ShoulderL", (-1.5, 22.6, 2.6), (3.3, 2.4, 2.4), paint=pg_body, **tp)
    m.part("ShoulderTopL", (-1.0, 25.0, 2.4), (2.4, 0.5, 1.9), pivot=(0, 18, 0), parent="ShoulderL", paint=pg_body)
    m.mirror("ShoulderL", "ShoulderR")

    # The head: as wide as the torso, deep and rounded behind, its front set back so the "=)" is carved into skin over it
    head = m.part("Head", (-1.7, 25, -3.25), (4.0, 8.2, 6.5), pivot=(0, 25, 0), parent=torso, rest=(0, 0, -5), paint=pg_body)
    m.part("HeadBack", (2.3, 25.6, -2.7), (0.7, 7.0, 5.4), pivot=(0, 25, 0), parent=head, paint=pg_body)
    m.part("CheekL", (-1.4, 25.4, 3.25), (3.4, 6.8, 0.45), pivot=(0, 25, 0), parent=head, paint=pg_body)
    m.mirror("CheekL", "CheekR")
    m.part("Carving", (-1.75, 25.2, -3.0), (0.05, 7.6, 6.0), pivot=(0, 25, 0), parent=head, paint=pg_carved, faces=("west",))
    # The face, carved on a half-voxel grid (one texel a cell): two horizontal slashes for eyes (the "=") over a wide,
    # deep crescent of a grin (the ")" turned up into a smile). '#' is cut through the skin plate to the dark under it.
    face = [
        ".............",   # y 32.5..33
        ".............",
        ".####...####.",   # the eyes: two slashes, side by side
        ".####...####.",
        ".............",
        ".#.........#.",   # the grin's corners, curling up
        ".##.......##.",
        "..##.....##..",
        "..#########..",
        "...#######...",
        ".....###.....",   # y 27.5..28
        ".............",
        ".............",
        ".............",
        ".............",
        ".............",   # y 25..25.5
    ]
    CELL, FZ0, FY1 = 0.5, -3.25, 33.0
    rows, cols = len(face), len(face[0])
    cut = lambda r, c: 0 <= r < rows and 0 <= c < cols and face[r][c] == "#"
    used = [[cut(r, c) for c in range(cols)] for r in range(rows)]
    k = 0
    for r in range(rows):
        for c in range(cols):
            if used[r][c]:
                continue
            c1 = c
            while c1 + 1 < cols and not used[r][c1 + 1]:
                c1 += 1
            r1 = r
            while r1 + 1 < rows and all(not used[r1 + 1][x] for x in range(c, c1 + 1)):
                r1 += 1
            for rr in range(r, r1 + 1):
                for cc in range(c, c1 + 1):
                    used[rr][cc] = True
            # A side face only where it borders a cut (the walls of the carving); north is -z (a lower column)
            sides = ["west"]
            if any(cut(r - 1, x) for x in range(c, c1 + 1)):
                sides.append("up")
            if any(cut(r1 + 1, x) for x in range(c, c1 + 1)):
                sides.append("down")
            if any(cut(y, c - 1) for y in range(r, r1 + 1)):
                sides.append("north")
            if any(cut(y, c1 + 1) for y in range(r, r1 + 1)):
                sides.append("south")
            # ...and skin on the plate's outer edges, so the face is closed seen from the side or above
            outer = [f for f, edge in (("up", r == 0), ("down", r1 == rows - 1), ("north", c == 0), ("south", c1 == cols - 1)) if edge and f not in sides]
            sides += outer
            # Blood run down from the grin onto the chin, only under the mouth
            runs = [(x - c) / (c1 - c + 1) for x in range(c, c1 + 1) if r > 10 and r <= 12 and x % 2 == 1 and any(cut(y, x) for y in range(8, 11))]
            m.part(f"Face{k}", (-2.1, FY1 - (r1 + 1) * CELL, FZ0 + c * CELL), (0.4, (r1 - r + 1) * CELL, (c1 - c + 1) * CELL),
                   pivot=(0, 25, 0), parent=head, paint=pg_faceplate, faces=tuple(sides), tag={"runs": runs, "outer": outer})
            k += 1
    # Blood running from the grin and from an eye's end, as real drips
    for i, (z, y, ln) in enumerate(((-0.6, 27.5, 1.5), (1.1, 28.0, 0.9), (-2.4, 31.0, 0.7), (2.3, 29.5, 1.1))):
        m.part(f"Drip{i}", (-2.2, y - ln, z - 0.15), (0.15, ln, 0.3), pivot=(0, 25, 0), parent=head, paint=lambda c: fill(c, BLOOD, 0.1))
    # The Gumby slant of the canon sketch: the top of the head rounded over and rolled down to its right
    top = m.part("HeadTop", (-1.9, 32.4, -3.3), (4.3, 2.4, 6.6), pivot=(0.2, 33.6, 0), parent=head, rest=(-10, 0, 0), paint=pg_body)
    m.part("HeadCrown", (-1.3, 34.8, -2.6), (3.2, 0.7, 5.0), pivot=(0.2, 33.6, 0), parent=top, paint=pg_body)
    m.part("HeadBrow", (-2.1, 33.0, -2.9), (0.4, 1.0, 5.8), pivot=(0.2, 33.6, 0), parent=top, paint=pg_body)

    # ---- The chest: the carapace's two doors hinged at their outer edges, and behind them the cavity
    m.part("CarapaceL", (-2.6, 18.6, 0), (0.6, 5.8, 3.55), pivot=(-2.3, 21.5, 3.55), parent=torso, paint=pg_carapace)
    m.part("CarapaceRimL", (-2.85, 18.9, 2.7), (0.3, 5.2, 0.6), pivot=(-2.3, 21.5, 3.55), parent="CarapaceL", paint=pg_carapace)
    m.mirror("CarapaceL", "CarapaceR")
    m.part("Cavity", (-0.7, 18.8, -2.9), (0.1, 5.2, 5.8), pivot=(0, 18, 0), parent=torso, paint=pg_flesh, faces=("west",))
    # Inside: the black Phobic Centipede curled on the back wall, its grinning face upside down at the top
    for i, (y, z) in enumerate(((22.4, -1.9), (21.3, -1.1), (20.2, -0.3), (19.4, 0.6), (19.0, 1.6))):
        m.part(f"Centipede{i}", (-1.1, y - 0.5, z - 0.55), (0.5, 1.0, 1.1), pivot=(0, 18, 0), parent=torso, paint=pg_centipede)
    m.part("InnerFace", (-1.15, 22.3, -0.1), (0.55, 1.6, 2.2), pivot=(0, 18, 0), parent=torso, paint=pg_innerface)
    m.part("InnerEyeL", (-1.22, 22.55, 0.25), (0.1, 0.3, 0.45), pivot=(0, 18, 0), parent=torso, paint=pg_innereye, glow=200)
    m.part("InnerEyeR", (-1.22, 22.55, 1.35), (0.1, 0.3, 0.45), pivot=(0, 18, 0), parent=torso, paint=pg_innereye, glow=200)
    # Something small, curled under the carapace: when the body dies it walks away on little centipede legs
    m.part("Skitter", (-1.25, 18.85, -1.6), (0.6, 0.5, 3.2), pivot=(-1.0, 19.1, 0), parent=torso, paint=pg_centipede)

    # The centipede's arms, given extended (pointing forward from the shoulder of the cavity) and folded by their rest
    # rotations: the upper arm straight up inside the body, the forearm doubled back down into the cavity, the talons
    # curled in. Berserk unfolds them into a reach of nearly a block.
    # Folded, the upper arm stands up the cavity from its floor and the forearm hangs back down beside it (a little
    # outboard), hand and talons tucked into the belly; unfolding swings them forward out of the open chest.
    SY, SX, FZ = 19.4, -1.4, 0.85
    claw = m.part("ClawArmL", (SX - 5.0, SY - 0.45, 1.15), (5.0, 0.9, 0.9), pivot=(SX, SY, 1.6), parent=torso, rest=(0, 0, -90),
                  paint=pg_chitin, tag={"rings": 1})
    ex = SX - 5.0
    fore = m.part("ClawForeL", (ex - 5.2, SY - 0.4, 1.2 + FZ), (5.2, 0.8, 0.8), pivot=(ex, SY, 1.6 + FZ), parent=claw, rest=(0, 0, 180),
                  paint=pg_chitin, tag={"rings": 2})
    hx = ex - 5.2
    hand = m.part("ClawL", (hx - 1.5, SY - 0.7, 0.9 + FZ), (1.5, 1.4, 1.4), pivot=(hx, SY, 1.6 + FZ), parent=fore, rest=(0, -HAND_CURL, 0), paint=pg_chitin)
    # Three sickle talons: two hooking down and forward, one opposed above, like the diagram's hand
    for nm, z, rz, ry in (("TalonL", 1.95 + FZ, 30, 6), ("Talon2L", 1.25 + FZ, 30, -6), ("Talon3L", 1.6 + FZ, THUMB_REST, 0)):
        up = nm == "Talon3L"
        y = SY + 0.15 if up else SY - 0.55
        t = m.part(nm, (hx - 4.3, y - 0.3, z - 0.3), (2.8, 0.6, 0.6), pivot=(hx - 1.5, y, z), parent=hand, rest=(0, ry, rz),
                   paint=pg_talon)
        m.part(nm[:-1] + "TipL", (hx - 6.1, y - 0.22, z - 0.22), (1.8, 0.45, 0.45), pivot=(hx - 4.3, y, z), parent=t,
               rest=(0, 0, -50 if up else 50), paint=pg_talon, tag={"tip": True})
    m.mirror("ClawArmL", "ClawArmR")

    # ---- Legs: long thick slabs with barely a knee, standing on flat square soles
    thigh = m.part("ThighL", (-1.75, 8, 0.25), (3.5, 8, 3.5), pivot=(0, 16, 2.0), parent=pelvis, paint=pg_body)
    shin = m.part("ShinL", (-1.65, 0.8, 0.35), (3.3, 7.4, 3.3), pivot=(0, 8, 2.0), parent=thigh, paint=pg_body)
    m.part("FootL", (-2.3, 0, 0.1), (4.2, 1.2, 3.8), pivot=(0, 0.6, 2.0), parent=shin, paint=pg_body)
    m.mirror("ThighL", "ThighR")

    # ---- Noodle arms in four links, thick as the canon's, bowed out at the elbow and ending in a flared lamprey mouth
    parent, top = torso, ARM_TOP
    for nm, w, ln in ARM:
        p = m.part(nm + "L", (-w / 2, top - ln, ARM_Z - w / 2), (w, ln, w), pivot=(0, top, ARM_Z), parent=parent, paint=pg_body,
                   rest=ARM_REST[nm], tag={"blood": 0.5 if nm == "Arm4" else 0.0})
        parent, top = p, top - ln
    sucker = m.part("SuckerL", (-1.2, top - 1.0, ARM_Z - 1.2), (2.4, 1.0, 2.4), pivot=(0, top, ARM_Z), parent=parent, paint=pg_sucker)
    m.part("LipL", (-1.5, top - 1.6, ARM_Z - 1.5), (3.0, 0.6, 3.0), pivot=(0, top, ARM_Z), parent=sucker, paint=pg_lip)
    for i in range(6):  # hooked teeth round the rim, leaning in over the throat
        a = TAU * i / 6
        dx, dz = 1.0 * math.cos(a), 1.0 * math.sin(a)
        m.part(f"Tooth{i}L", (dx - 0.18, top - 2.15, ARM_Z + dz - 0.18), (0.36, 0.6, 0.36), pivot=(dx, top - 1.6, ARM_Z + dz),
               parent=sucker, rest=(dz * 35, 0, -dx * 35), paint=pg_tooth)
    m.mirror("Arm1L", "Arm1R")
    hand_y = top - 1.6

    if intern:
        # A red balloon on a string from the right hand, floating up beside the head. The string's rest undoes the
        # arm's own bends so it stands straight up from the mouth, leaning a little out.
        string = m.part("BalloonString", (-0.12, hand_y, -ARM_Z - 0.12), (0.25, 24, 0.25), pivot=(0, hand_y, -ARM_Z),
                        parent="SuckerR", rest=STRING_REST, paint=pg_string)
        balloon(m, "Balloon", (0, hand_y + 24 + 4.6, -ARM_Z), (0, hand_y + 24, -ARM_Z), parent=string)

    arm_names = [f"{nm}{sd}" for sd in "LR" for nm, _, _ in ARM]
    arms = arm_names + ["SuckerL", "SuckerR"]
    legs = ["ThighL", "ThighR", "ShinL", "ShinR"]
    shell = ["CarapaceL", "CarapaceR"] + [f"{p}{sd}" for sd in "LR" for p in ("ClawArm", "ClawFore", "Claw", "Talon", "Talon2", "Talon3")]
    core = ["Pelvis", "Torso", "Head"]
    extra = ["BalloonString", "Balloon"] if intern else []
    every = core + arms + legs + shell + extra


    def floated(d, bob=(0.0, 0.0)):
        if not intern:
            return d
        r = string_rot(d, bob)
        d = dict(d)
        d["BalloonString"] = pose(tuple(r[i] - STRING_REST[i] for i in range(3)))
        d.setdefault("Balloon", pose())
        return d

    def noodle(p, amp=6.0, side_amp=4.0, lag=0.12, base_z=0.0, base_x=0.0, speed=1.0):
        """The arms float in slow waves, each link lagging the one above it."""
        d = {}
        for sd, sign in (("L", 1), ("R", -1)):
            for i, (nm, _, _) in enumerate(ARM):
                ph = p * speed - i * lag + (0.31 if sd == "R" else 0)
                d[f"{nm}{sd}"] = pose((sign * (base_x * (1 if i == 0 else 0.3) + s(ph, side_amp * (0.6 + 0.2 * i))), 0,
                                       (base_z if i == 0 else base_z * 0.25) + s(ph, amp * (0.6 + 0.25 * i), 0.25)))
        return d

    def balloon_bob(p, amp=4):
        return (s(p, amp), s(p, amp * 0.7, 0.3))

    # Idle, "party": swaying side to side, nodding to a beat no one else hears with a little dip at the knees, arms
    # drifting, the balloon bobbing
    def idle(p):
        nod = max(0.0, math.sin(TAU * p * 2)) ** 3
        d = {"Pelvis": pose((s(p, 4), 0, 0), (0, -0.25 * nod, 0)), "Torso": pose((s(p, 1.5, 0.1), 0, 0)),
             "Head": pose((s(p, -3, 0.15), 0, 9 * nod)),
             "ThighL": pose((0, 0, -4 * nod)), "ThighR": pose((0, 0, -4 * nod)), "ShinL": pose((0, 0, 7 * nod)), "ShinR": pose((0, 0, 7 * nod))}
        d.update(noodle(p, 7, 5, 0.12, 0, 6))
        d["SuckerL"] = pose((0, 0, s(p, 8, 0.4)))
        d["SuckerR"] = pose((0, 0, s(p, 8, 0.7)))
        return floated(d, balloon_bob(p))
    m.animation("idle", 60, cycle(60, 12, idle))

    # Walk: the deliberate wading gait: long stiff strides pushed through something thick, the body rolling over each
    # planted foot, leaning back, arms trailing and curling
    def walk(p):
        leg = 20 * math.sin(TAU * p)
        d = {"Pelvis": pose((s(p, 4), s(p, 5), -4), (0, 0.5 * abs(math.sin(TAU * p)), 0)),
             "Torso": pose((s(p, -2), s(p, -2), -2)), "Head": pose((s(p, 2.5, 0.1), s(p, -4), 4)),
             "ThighL": pose((0, 0, -leg)), "ThighR": pose((0, 0, leg)),
             "ShinL": pose((0, 0, max(0.0, leg) * 0.5)), "ShinR": pose((0, 0, max(0.0, -leg) * 0.5))}
        d.update(noodle(p, 10, 4, 0.14, 24, 6))
        d["SuckerL"] = pose((0, 0, 10 + s(p, 6)))
        d["SuckerR"] = pose((0, 0, 10 + s(p, 6, 0.5)))
        return floated(d, balloon_bob(p, 6))
    m.animation("walk", 48, cycle(48, 12, walk))

    # Run: hunched forward, arms reaching ahead and rippling, the mouths pulsing
    def run(p):
        leg = 32 * math.sin(TAU * p)
        pulse = 1 + 0.15 * max(0.0, math.sin(TAU * p * 2))
        d = {"Pelvis": pose((s(p, 3), s(p, 6), 15), (0, 1.0 * abs(math.sin(TAU * p)), 0)),
             "Torso": pose((0, s(p, -4), 4)), "Head": pose((0, s(p, 3), -12)),
             "ThighL": pose((0, 0, -leg - 12)), "ThighR": pose((0, 0, leg - 12)),
             "ShinL": pose((0, 0, max(0.0, leg) * 0.7)), "ShinR": pose((0, 0, max(0.0, -leg) * 0.7)),
             "SuckerL": pose((0, 0, -20), s=(pulse, pulse, pulse)), "SuckerR": pose((0, 0, -20), s=(pulse, pulse, pulse))}
        d.update(noodle(p * 2, 10, 4, 0.1, -70, 14))
        return floated(d, balloon_bob(p, 8))
    m.animation("run", 28, cycle(28, 14, run))

    # Gaze: every sway stops; the head tilts twenty degrees and holds on you, the arms lift a little from the sides
    gaze_names = core + arms + extra
    rest_arms = noodle(0, 0, 0, 0, 0, 6)
    lifted = noodle(0, 0, 0, 0, -12, 10)
    m.animation("gaze", 20, {
        0: full(gaze_names, floated(dict(rest_arms))),
        8: full(gaze_names, floated(dict(lifted, Head=pose((20, 0, -4)), Torso=pose((2, 0, -2))))),
        19: full(gaze_names, floated(dict(lifted, Head=pose((21, 0, -5)), Torso=pose((2, 0, -2))))),
    }, end="Hold", stopped="EaseOut")

    # Latch: both arms whip forward and in together, the mouths flare and clamp on, hold, and pull back
    latch_names = core + arms + extra

    def reach(z1, z2, sq, t=1.0):
        d = {}
        for sd, sign in (("L", 1), ("R", -1)):
            d[f"Arm1{sd}"] = pose((sign * 26 * t, 0, z1))
            d[f"Arm2{sd}"] = pose((sign * -8 * t, 0, z2))
            d[f"Arm3{sd}"] = pose((sign * -12 * t, 0, z2 * 0.6))
            d[f"Arm4{sd}"] = pose((sign * -8 * t, 0, z2 * 0.3))
            d[f"Sucker{sd}"] = pose(s=(sq, sq, sq))
        return d
    m.animation("latch", 24, {
        0: full(latch_names, floated({})),
        3: full(latch_names, floated(dict(reach(30, 14, 1.0, 0.3), Torso=pose((0, 0, -8))))),
        6: full(latch_names, floated(dict(reach(-95, 4, 1.3), Torso=pose((0, 0, 12)), Head=pose((0, 0, -8))))),
        10: full(latch_names, floated(dict(reach(-92, 2, 0.8), Torso=pose((0, 0, 14)), Head=pose((0, 0, -8))))),
        13: full(latch_names, floated(dict(reach(-90, 2, 0.9), Torso=pose((0, 0, 12)), Head=pose((0, 0, -6))))),
        16: full(latch_names, floated(dict(reach(-86, -4, 0.85), Torso=pose((0, 0, 10)), Head=pose((0, 0, -4))))),
        23: full(latch_names, floated({})),
    }, end="Stop")

    # Berserk: the carapace cracks, its doors swing wide, and the centipede's arms unfold out of the cavity; held
    def opened(t, twitch=0.0, grip=0.0, sway=0.0):
        a = min(1.0, t * 1.6)            # the doors lead...
        b = max(0.0, (t - 0.3) / 0.7)    # ...the arms follow
        d = {"CarapaceL": pose((0, 105 * a, 0)), "CarapaceR": pose((0, -105 * a, 0))}
        for sd, sign, tw in (("L", 1, twitch), ("R", -1, -twitch)):
            d[f"ClawArm{sd}"] = pose((0, sign * 20 * b, 80 * b + tw + sway * sign))
            d[f"ClawFore{sd}"] = pose((0, -sign * 6 * b, -166 * b - tw * 0.5))
            d[f"Claw{sd}"] = pose((0, sign * HAND_CURL * b, 8 * b))
            d[f"Talon{sd}"] = pose((0, 0, -10 * b - grip))
            d[f"Talon2{sd}"] = pose((0, 0, -10 * b - grip))
            d[f"Talon3{sd}"] = pose((0, 0, (THUMB_OPEN - THUMB_REST) * b + grip))
        return d
    bz_names = core + shell + arms
    m.animation("berserk", 16, {
        0: full(bz_names, opened(0)),
        3: full(bz_names, dict(opened(0.15), Torso=pose((4, 0, -8)), Head=pose((0, 0, -10)))),
        7: full(bz_names, dict(opened(0.5), Torso=pose((-3, 0, -2)), Head=pose((-4, 0, -2)))),
        11: full(bz_names, dict(opened(1.0, 0, 12), Torso=pose((0, 0, 8)), Head=pose((-6, 0, 6)))),
        15: full(bz_names, dict(opened(1.0), Torso=pose((0, 0, 5)), Head=pose((-4, 0, 2)))),
    }, end="Hold")
    # Berserk idle: the arms held out like a mantis's, swaying, talons flexing; now and then a twitch
    bi = {}
    for f in range(0, 40, 4):
        tw = 14 if f in (8, 28) else -10 if f in (20,) else 0
        bi[f] = full(bz_names, dict(opened(1.0, tw, 10 * math.sin(TAU * f / 40 * 2), s(f / 40, 6)),
                                    Torso=pose((s(f / 40, 2), 0, 5)), Head=pose((-4, 0, 2 + s(f / 40, 2, 0.3)))))
    m.animation("berserkidle", 40, bi)

    # Claw: two fast slashes, the right arm then the left: drawn back, then whipped down and across
    def slash(side, raise_t, strike_t):
        other = "L" if side == "R" else "R"
        sign = 1 if side == "L" else -1
        d = opened(1.0)
        d[f"ClawArm{side}"] = pose((0, sign * (20 - 30 * strike_t), 80 - 45 * raise_t + 65 * strike_t))
        d[f"ClawFore{side}"] = pose((0, 0, -166 + 75 * raise_t - 75 * raise_t * strike_t))
        d[f"Talon{side}"] = pose((0, 0, -10 - 30 * strike_t))
        d[f"Talon2{side}"] = pose((0, 0, -10 - 30 * strike_t))
        d[f"Talon3{side}"] = pose((0, 0, THUMB_OPEN - THUMB_REST + 30 * strike_t))
        d[f"ClawArm{other}"] = pose((0, -sign * 20, 80))
        return d
    m.animation("claw", 16, {
        0: full(bz_names, opened(1.0)),
        2: full(bz_names, dict(slash("R", 1, 0), Torso=pose((0, -10, 2)))),
        5: full(bz_names, dict(slash("R", 1, 1), Torso=pose((0, 12, 10)))),
        7: full(bz_names, dict(slash("L", 1, 0), Torso=pose((0, 10, 4)))),
        10: full(bz_names, dict(slash("L", 1, 1), Torso=pose((0, -12, 10)))),
        15: full(bz_names, opened(1.0)),
    }, end="Stop")

    # Hurt: almost nothing. It never flinched
    m.animation("hurt", 8, {0: full(["Head"], {}), 2: full(["Head"], {"Head": pose((3, 0, -3))}), 7: full(["Head"], {})}, end="Stop")

    # Die: it topples forward onto its face; the carapace heaves twice; a leg twitches; and from under the body
    # something small walks away on little centipede legs; held
    die_names = every + ["Skitter"]

    def down(t, heave=0.0, twitch=0.0, crawl=0.0):
        d = {"Pelvis": pose((0, 0, 86 * t), (-14.2 * t, -0.5 * t, 0)), "Torso": pose((0, 0, 3 * t)), "Head": pose((8 * t, 0, 4 * t)),
             "ThighL": pose((0, 0, -4 * t + twitch)), "ThighR": pose((0, 0, -2 * t)), "ShinL": pose((0, 0, 4 * t + twitch * 0.5)),
             "CarapaceL": pose((0, 14 * heave, 0)), "CarapaceR": pose((0, -14 * heave, 0)),
             "Skitter": pose((0, 25 * math.sin(crawl * 14), 0), (-1.0 * min(1, crawl * 4), 0, 11 * crawl))}
        d.update(noodle(0.3, 0, 0, 0, 6 * t, 12 * t))
        return floated(d)
    m.animation("die", 60, {
        0: full(die_names, down(0)), 10: full(die_names, down(0.55)), 18: full(die_names, down(1.0)),
        22: full(die_names, down(1.0, 1.0)), 25: full(die_names, down(1.0, 0.0)), 28: full(die_names, down(1.0, 1.0)),
        31: full(die_names, down(1.0, 0.0, 12)), 33: full(die_names, down(1.0, 0.0, -4)), 36: full(die_names, down(1.0)),
        40: full(die_names, down(1.0, 0.3, 0, 0.12)), 44: full(die_names, down(1.0, 0, 0, 0.3)), 48: full(die_names, down(1.0, 0, 0, 0.5)),
        52: full(die_names, down(1.0, 0, 0, 0.72)), 56: full(die_names, down(1.0, 0, 0, 0.9)), 59: full(die_names, down(1.0, 0, 0, 1.0)),
    }, end="Hold", stopped="Stop")
    return m


def partygoer_variants(intern):
    g = globals()
    saved = {k: g[k] for v in VARIANTS.values() for k in v}
    base = "fun-partygoer-intern" if intern else "fun-partygoer"
    for vname, palette in VARIANTS.items():
        g.update(palette)
        m = partygoer(intern)
        width, height = m._pack()
        m._paint(width, height).save(os.path.join(ASSETS, "textures", "entity", f"{base}-{vname}.png"))
        print(f"wrote {base}-{vname} texture {width}x{height}")
        g.update(saved)


# ======================================================================== The lure balloon
# "Avoid balloons if you see them floating on their own ... these are almost always bait." A red balloon at head
# height, its string hanging free above the floor. The balloon is the root (it does the floating); the string hangs
# from the knot in three links that sway after it.

def lureballoon():
    m = Model("fun-lureballoon", atlas_width=32, seed=110)
    cy = 24.5
    bal = balloon(m, "Balloon", (0, cy, 0), (0, cy, 0))
    top, parent = cy - 4.6, bal
    for i, ln in enumerate((5.0, 5.0, 4.5)):
        parent = m.part(f"String{i}", (-0.12, top - ln, -0.12), (0.25, ln, 0.25), pivot=(0, top, 0), parent=parent,
                        rest=((4, 0, -3), (-6, 0, 5), (5, 0, -4))[i], paint=pg_string)
        top -= ln
    strings = ["String0", "String1", "String2"]

    def sway(p, lean=0.0, amp=5.0):
        d = {"Balloon": pose((s(p, 3, 0.2), s(p, 14), lean * 0.4), (0, s(p, 0.6, 0.1), 0))}
        for i, n in enumerate(strings):
            d[n] = pose((s(p, amp, 0.15 * (i + 1)), 0, (lean if i == 0 else lean * 0.3) + s(p, amp * 0.8, 0.25 + 0.15 * i)))
        return d
    m.animation("idle", 60, cycle(60, 12, lambda p: sway(p)))
    # Drift: moving off, the balloon tips into its way and the string trails behind it
    m.animation("drift", 30, cycle(30, 10, lambda p: sway(p, -24, 4)))
    return m


# ======================================================================== The Party Host
# Level 26: "a huge monster filling the ceiling. It looked like a golden fried egg with an eye-and-mouth combination
# in the middle." A Faceling a Partygoer bit by mistake ("Once Party Hosts turn golden, they are perfect").
# Built to hang: its top (the flat of the egg) at y = 16, the yolk dome below it facing down into the room, and at the
# dome's crown one organ that is both eye and mouth: a huge eye between a lashed lid and a toothed jaw, wide enough to
# take a Faceling feet first. LUCA tears hang from the corners of the eye. Spawn it with its feet one block below the
# ceiling.

HOST_WHITE = (244, 240, 224)
HOST_LACE = (198, 132, 46)
HOST_GOLD = (238, 172, 30)
HOST_GOLD_HI = (255, 220, 96)
HOST_GOLD_LO = (196, 112, 16)
HOST_LIP = (176, 54, 52)
HOST_TEAR = (250, 200, 64)


def host_white(ctx):
    """The white: pale, faintly fleshy (it was a Faceling), blistered, with fine pink veins and a sheen of grease."""
    fill(ctx, HOST_WHITE, 0.03)
    blotch(ctx, (226, 206, 178), 2 + ctx.w * ctx.h // 900, 2.0, 7.0, 0.35)
    blotch(ctx, (250, 222, 140), 1 + ctx.w * ctx.h // 1500, 2.0, 6.0, 0.3)
    for _ in range(ctx.w * ctx.h // 300):
        u, v = ctx.rng.random(), ctx.rng.random()
        line(ctx, u, v, u + ctx.rng.uniform(-0.12, 0.12), v + ctx.rng.uniform(-0.12, 0.12), (214, 150, 150), 0.35)
    speckle(ctx, (252, 250, 240), 0.03)
    if ctx.face in SIDES:
        grade(ctx, 1.0, 0.85)


def host_lace(ctx):
    """The crisp fried edge: golden brown lace, darker where it curls, holes in it."""
    fill(ctx, HOST_LACE, 0.1)
    blotch(ctx, (150, 84, 28), 2, 1.0, 3.0, 0.5)
    blotch(ctx, (232, 186, 96), 1, 1.0, 3.0, 0.4)
    speckle(ctx, (110, 60, 22), 0.08)


def host_gold(ctx):
    """The yolk: glossy gold, deeper orange low on the dome, wet highlights."""
    fill(ctx, shade(HOST_GOLD, ctx.part.tag.get("tier", 1.0)), 0.04)
    if ctx.face == "down":  # a wet sheen on the dome's underside, brighter toward its crown
        blotch(ctx, HOST_GOLD_HI, 2, ctx.w * 0.1, ctx.w * 0.25, 0.35)
    if ctx.face in SIDES:
        grade(ctx, 1.06, 0.86)
    blotch(ctx, HOST_GOLD_HI, 2 + ctx.w * ctx.h // 400, 1.5, 5.0, 0.45)
    blotch(ctx, HOST_GOLD_LO, 1 + ctx.w * ctx.h // 600, 1.5, 4.0, 0.35)
    speckle(ctx, (255, 240, 170), 0.025)


def host_rim(ctx):
    """The rim of the eye-mouth: gold outside, raw red lip on its inner faces and along its bottom edge."""
    if ctx.face in ctx.part.tag.get("inner", ()):
        fill(ctx, HOST_LIP, 0.08, face_shade=False)
        blotch(ctx, (120, 24, 30), 1, 1.0, 2.0, 0.5)
        return
    host_gold(ctx)
    lip = ctx.part.tag.get("lipu")
    if ctx.face == "down" and lip is not None:  # a raw red lip along the edge that meets the eye
        for yy in range(ctx.h):
            for k in range(3):
                texel(ctx, (ctx.w - 1 - k) if lip else k, yy, HOST_LIP if k < 2 else mix(HOST_LIP, HOST_GOLD, 0.5))
    elif ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, -1, HOST_LIP, 0.8)


def host_throat(ctx):
    fill(ctx, (40, 6, 10), 0.1, face_shade=False)
    blotch(ctx, (100, 14, 22), 2, 1.0, 3.0, 0.5)


def host_eye(ctx):
    """The eye: a yellowed, bloodshot ball; on its underside a huge deep red iris round a black pupil."""
    fill(ctx, (238, 230, 206), 0.03, face_shade=False)
    if ctx.face == "down" and ctx.part.tag.get("iris"):
        cx, cy = (ctx.w - 1) / 2, (ctx.h - 1) / 2
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                d = math.hypot((xx - cx) / max(1, ctx.w * 0.36), (yy - cy) / max(1, ctx.h * 0.36))
                if d < 0.38:
                    texel(ctx, xx, yy, (10, 2, 4))
                elif d < 0.5:
                    texel(ctx, xx, yy, (80, 6, 12))
                elif d < 1.0:
                    texel(ctx, xx, yy, mix((176, 30, 30), (226, 140, 40), (d - 0.5) * 1.6))
                elif d < 1.12:
                    texel(ctx, xx, yy, (90, 20, 20))
        texel(ctx, int(cx - ctx.w * 0.14), int(cy - ctx.h * 0.14), (255, 250, 240))  # a wet glint
    for _ in range(3 + ctx.w // 3):  # veins from the edges in
        e = ctx.rng.randrange(4)
        u, v = [(0, ctx.rng.random()), (1, ctx.rng.random()), (ctx.rng.random(), 0), (ctx.rng.random(), 1)][e]
        line(ctx, u, v, u + (0.5 - u) * ctx.rng.uniform(0.15, 0.35), v + (0.5 - v) * ctx.rng.uniform(0.15, 0.35), (200, 50, 50), 0.6)


def host_tooth(ctx):
    fill(ctx, (236, 226, 192), 0.06, face_shade=ctx.face != "down")
    if ctx.face in SIDES:
        texel(ctx, 0, 0, (150, 60, 50), 0.6)


def host_lash(ctx):
    fill(ctx, (40, 22, 14), 0.1)


def host_tear(ctx):
    fill(ctx, HOST_TEAR, 0.05, face_shade=False)
    if ctx.face in SIDES:
        for yy in range(ctx.h):
            texel(ctx, 0, yy, (255, 240, 170), 0.6)


def disc(m, name, r, y0, y1, parent, pivot, paint, glow=0, faces=None, tag=None):
    """A rough circle of radius r as voxels: a square with its corners cut, and two crossing bars."""
    a, b = r * 0.88, r * 0.62
    first = m.part(name, (-a, y0, -a), (2 * a, y1 - y0, 2 * a), pivot=pivot, parent=parent, paint=paint, glow=glow, faces=faces, tag=tag)
    m.part(name + "X", (-r, y0, -b), (2 * r, y1 - y0, 2 * b), pivot=pivot, parent=first, paint=paint, glow=glow, faces=faces, tag=tag)
    m.part(name + "Z", (-b, y0, -r), (2 * b, y1 - y0, 2 * r), pivot=pivot, parent=first, paint=paint, glow=glow, faces=faces, tag=tag)
    return first


def partyhost():
    m = Model("fun-partyhost", atlas_width=128, seed=26)
    m.light = dict(LIGHT, ground=0.0)
    NO_UP = ("north", "south", "east", "west", "down")
    # The white: a rough disc 48 across, 3 thick, its top against the ceiling at y 16, spread unevenly
    white = disc(m, "Disc", 22, 13, 16, None, (0, 14.5, 0), host_white, glow=20, faces=NO_UP)
    for i, (x, z, w, d) in enumerate(((-24, -8, 9, 12), (14, 12, 12, 9), (-10, 17, 11, 8), (8, -24, 10, 7), (17, -12, 8, 10), (-20, 10, 8, 9))):
        m.part(f"Lump{i}", (x, 13.3, z), (w, 2.7, d), pivot=(0, 14.5, 0), parent=white, paint=host_white, faces=NO_UP)
    # The crisp golden lace round the edge
    for i in range(16):
        a = TAU * (i + 0.3 * math.sin(i * 7)) / 16
        r = 22.5 + 1.8 * math.sin(i * 2.3)
        x, z = r * math.cos(a), r * math.sin(a)
        w, d = 3.5 + 2 * abs(math.sin(i * 1.7)), 3.5 + 2 * abs(math.cos(i * 1.3))
        m.part(f"Lace{i}", (x - w / 2, 13.2 + 0.4 * (i % 3), z - d / 2), (w, 1.0, d), pivot=(0, 14.5, 0), parent=white, paint=host_lace,
               glow=15, faces=NO_UP)
    # Blisters on the white's underside
    for i, (x, z, w) in enumerate(((-16, -4, 3), (12, 8, 2.5), (-5, 15, 2), (6, -15, 3), (16, -3, 2))):
        m.part(f"Blister{i}", (x, 12.4, z), (w, 0.6, w), pivot=(0, 14.5, 0), parent=white, paint=host_white)

    # The yolk dome in three tiers, glowing faintly gold; the lowest, the "head", turns to follow you
    yolk = disc(m, "Yolk", 12.5, 9, 13, white, (0, 13, 0), host_gold, glow=40, faces=NO_UP, tag={"tier": 0.86})
    mid = disc(m, "YolkMid", 10.5, 6.5, 9, yolk, (0, 9, 0), host_gold, glow=40, faces=NO_UP, tag={"tier": 0.95})
    head = disc(m, "Head", 8.5, 4.5, 6.5, mid, (0, 6.5, 0), host_gold, glow=40, faces=("north", "south", "east", "west"), tag={"tier": 1.06})
    hp = dict(pivot=(0, 6.5, 0), parent=head)
    # The socket's floor: a dark wet throat behind the eye
    m.part("Mouth", (-4, 4.4, -6), (8, 0.1, 12), paint=host_throat, faces=("down",), **hp)
    # The rim round the opening: gold, raw red inside
    m.part("RimN", (-6.5, 3.6, -7.5), (13, 0.9, 1.5), paint=host_rim, tag={"inner": ("south",)}, **hp)
    m.part("RimS", (-6.5, 3.6, 6), (13, 0.9, 1.5), paint=host_rim, tag={"inner": ("north",)}, **hp)
    # The eye, bulging out of the opening
    # (an almond: a core, narrower ends, and the iris on a bulge underneath; the throat shows dark at its corners)
    eye = m.part("Eye", (-3.0, 1.4, -3.8), (6.0, 3.0, 7.6), pivot=(0, 3.4, 0), paint=host_eye, glow=60, parent=head)
    m.part("EyeEndN", (-1.9, 1.8, -5.3), (3.8, 2.4, 1.5), pivot=(0, 3.4, 0), parent=eye, paint=host_eye, glow=60)
    m.part("EyeEndS", (-1.9, 1.8, 3.8), (3.8, 2.4, 1.5), pivot=(0, 3.4, 0), parent=eye, paint=host_eye, glow=60)
    m.part("EyeBulge", (-2.2, 0.9, -3.0), (4.4, 0.5, 6.0), pivot=(0, 3.4, 0), parent=eye, paint=host_eye, glow=60, tag={"iris": True})
    # The lid (on the -X side) with its lashes, and the jaw (on the +X side) with its teeth: the eye-and-mouth
    lid = m.part("Lid", (-6.5, 2.4, -6.2), (3.4, 2.1, 12.4), pivot=(-6.5, 4.5, 0), parent=head, paint=host_rim, tag={"inner": ("east",), "lipu": 1})
    for i, z in enumerate((-4.5, -2.2, 0, 2.2, 4.5)):
        m.part(f"Lash{i}", (-3.6, 0.8 + 0.3 * abs(z) / 4.5, z - 0.2), (0.4, 1.8 - 0.3 * abs(z) / 4.5, 0.4), pivot=(-3.4, 2.6, z),
               parent=lid, rest=(0, 0, 18), paint=host_lash)
    jaw = m.part("Jaw", (3.1, 2.4, -6.2), (3.4, 2.1, 12.4), pivot=(6.5, 4.5, 0), parent=head, paint=host_rim, tag={"inner": ("west",), "lipu": 0})
    for i, z in enumerate((-4.6, -2.3, 0, 2.3, 4.6)):
        ln = 1.5 if i % 2 == 0 else 1.1
        m.part(f"Tooth{i}", (3.1, 2.4 - ln, z - 0.35), (0.7, ln, 0.7), pivot=(3.45, 2.4, z), parent=jaw, rest=(0, 0, 14), paint=host_tooth)

    # LUCA tears: long ones from the corners of the eye, more from the yolk's tiers and the white's edge
    drips = []
    spots = ((0, -7.2, 4.0, 7), (0, 7.2, 4.0, 6), (-9.5, 3, 6.5, 4), (8, -6, 6.5, 5), (-4, 11, 9, 4), (11, 5, 9, 3),
             (-20, 2, 13, 5), (-6, -19, 13, 6), (14, -14, 13, 4), (18, 8, 13, 5))
    for i, (x, z, y, ln) in enumerate(spots):
        d = m.part(f"Drip{i}", (x - 0.4, y - ln, z - 0.4), (0.8, ln, 0.8), pivot=(x, y, z), parent=white if y >= 13 else (mid if y > 6 else head),
                   paint=host_tear, glow=90)
        m.part(f"Drop{i}", (x - 0.6, y - ln - 1.1, z - 0.6), (1.2, 1.2, 1.2), pivot=(x, y, z), parent=d, paint=host_tear, glow=110)
        drips.append(d)
    dn = [d.name for d in drips]

    # Idle: the yolk breathes, the head drifts, the eye darts and now and then blinks, the jaw works, tears swell
    def idle(p):
        blink = ramp(p, 0.62, 0.66, 0.68, 0.73)
        dart = [(0, 0), (6, -4), (6, -4), (-3, 5), (-3, 5), (0, 0), (0, 0), (-7, -2), (-7, -2), (2, 6), (2, 6), (0, 0)][int(p * 12) % 12]
        d = {"Yolk": pose(s=(1 + 0.03 * math.sin(TAU * p), 1 + 0.05 * math.sin(TAU * p), 1 + 0.03 * math.sin(TAU * p))),
             "Head": pose((s(p, 4), 0, s(p, 4, 0.25))), "Eye": pose((dart[0], 0, dart[1])),
             "Lid": pose((0, 0, 62 * blink)), "Jaw": pose((0, 0, s(p * 3, 4)))}
        d.update({n: pose(s=(1, 1 + 0.15 * max(0, math.sin(TAU * (p + i * 0.17))), 1)) for i, n in enumerate(dn)})
        return d
    m.animation("idle", 90, cycle(90, 12, idle))
    # Weep: the eye squeezes half shut and the tears lengthen and swell
    w_names = dn + ["Lid", "Eye", "Yolk"]
    m.animation("weep", 60, {
        0: full(w_names, {}),
        20: full(w_names, dict({n: pose(s=(1.1, 1.4 + 0.1 * i, 1.1)) for i, n in enumerate(dn)}, Lid=pose((0, 0, 35)), Eye=pose((-10, 0, 0)),
                               Yolk=pose(s=(1.03, 0.96, 1.03)))),
        40: full(w_names, dict({n: pose(s=(1.15, 1.9 + 0.12 * i, 1.15)) for i, n in enumerate(dn)}, Lid=pose((0, 0, 40)), Eye=pose((-12, 0, 4)),
                               Yolk=pose(s=(1.05, 0.95, 1.05)))),
        59: full(w_names, dict({n: pose(s=(1, 1.1, 1)) for n in dn}, Lid=pose((0, 0, 8)))),
    })
    # Upset: the lid and jaw gape, the eye rolls back into the head, the teeth show, the whole egg shudders
    up_names = ["Disc", "Yolk", "Head", "Lid", "Jaw", "Eye"]
    up = {0: full(up_names, {})}
    for f in range(3, 60, 3):
        k_ = 1 if (f // 3) % 2 else -1
        g = min(1.0, f / 9) * (1.0 if f < 54 else (60 - f) / 6)
        up[f] = full(up_names, {"Disc": pose((k_ * 1.2 * g, 0, -k_ * 1.0 * g)), "Yolk": pose(s=(1 + 0.06 * g, 1 + 0.1 * g, 1 + 0.06 * g)),
                                "Head": pose((k_ * 3 * g, 0, 4 * g)), "Lid": pose((0, 0, -55 * g)), "Jaw": pose((0, 0, (50 + 6 * k_) * g)),
                                "Eye": pose((0, 0, -70 * g), (0, 1.6 * g, 0))})
    up[63] = full(up_names, {})
    m.animation("upset", 64, up, end="Stop")
    return m


MODELS = {"partygoer": lambda: partygoer(False), "partygoer-intern": lambda: partygoer(True),
          "lureballoon": lureballoon, "partyhost": partyhost}


def main(names=None):
    names = names or list(MODELS)
    for n in names:
        MODELS[n]().save()
        if n == "partygoer":
            partygoer_variants(False)
        if n == "partygoer-intern":
            partygoer_variants(True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
