"""The Backrooms' entities, modelled after the lore (Wikidot entity pages) and animated: written as Vintage Story
shapes with their textures (see rig.py for the conventions: models face -X, left is +Z, feet at y=0).

Run from the repo root:  python tools/gen_models.py [name ...]
"""
import math
import os
import random
import sys

import rig
from rig import ASSETS, Model, fill, speckle, hlines, vlines, rect, mix, shade, clamp, gradient_down, pose

TAU = math.tau


def cycle(frames, steps, fn):
    """Keyframes for a looping cycle: fn(phase 0..1) -> {part: pose}, sampled at `steps` points."""
    return {int(round(frames * i / steps)): fn(i / steps) for i in range(steps)}


def merge(*dicts):
    out = {}
    for d in dicts:
        for frame, parts in d.items():
            out.setdefault(frame, {}).update(parts)
    return out


def s(phase, amp, shift=0.0):
    return amp * math.sin(TAU * (phase + shift))


# ======================================================================== Skin-Stealer
# "Tall, pale yellow humanoids with sunken white eyes" that wear stolen human skins. The model goes for the uncanny
# rather than the monstrous: a person-shaped thing wearing a person badly. Human at a distance, wrong on approach:
# a bit too tall and thin, forearms too long, hands hanging nearly to the knees, a thin long neck, a narrow skull
# with a slight forward pitch and a tilt, uneven shoulders. The skin is waxy and stretched, patchily discoloured,
# with folds where it bunches (under the jaw, at the wrists) and the sunken white eyes sit at different heights.
# The animation does most of the horror work: it walks like something that learned walking by watching.

SK_BASE = (230, 216, 170)      # pale yellow-beige
SK_CREAM = (242, 234, 204)     # sickly cream (highlights, stretched over bone)
SK_TAN = (190, 166, 118)       # muted tan (shading, patches)
SK_PINK = (196, 164, 152)      # greyish pink (lips, folds, bunched skin)
SK_BROWN = (122, 98, 68)       # dirty brown (deep creases)
SK_BRUISE = (154, 128, 146)    # a purple bruise under the surface
SK_GREEN = (170, 176, 126)     # ... and the green edge of an old one
EYE_WHITE = (240, 240, 232)
SOCKET = (76, 60, 46)
MOUTH = (46, 28, 28)


def blotch(ctx, colour, count, rmin, rmax, alpha):
    """Soft patches of discolouration: the stolen skin does not fit evenly."""
    px = ctx.img.load()
    for _ in range(count):
        cx, cy = ctx.rng.uniform(0, ctx.w), ctx.rng.uniform(0, ctx.h)
        rx = max(0.6, ctx.rng.uniform(rmin, rmax))
        ry = max(0.6, rx * ctx.rng.uniform(0.6, 1.4))
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                d = math.hypot((xx + 0.5 - cx) / rx, (yy + 0.5 - cy) / ry)
                a = alpha * max(0.0, 1 - d * d)
                if a > 0.01:
                    old = px[ctx.x + xx, ctx.y + yy]
                    px[ctx.x + xx, ctx.y + yy] = mix(old[:3], colour, a) + (255,)


def line(ctx, u0, v0, u1, v1, colour, alpha=1.0):
    """A thin line in face fractions: creases, tendons, collarbones, veins."""
    px = ctx.img.load()
    x0, y0, x1, y1 = u0 * ctx.w, v0 * ctx.h, u1 * ctx.w, v1 * ctx.h
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    done = set()
    for i in range(n + 1):
        t = i / n
        xx, yy = int(min(ctx.w - 1e-6, x0 + (x1 - x0) * t)), int(min(ctx.h - 1e-6, y0 + (y1 - y0) * t))
        if 0 <= xx < ctx.w and 0 <= yy < ctx.h and (xx, yy) not in done:
            done.add((xx, yy))
            old = px[ctx.x + xx, ctx.y + yy]
            px[ctx.x + xx, ctx.y + yy] = mix(old[:3], colour, alpha) + (255,)


def texel(ctx, tx, ty, colour, alpha=1.0):
    """One texture pixel of the face, counted from its top-left; negative counts from the right/bottom."""
    if tx < 0:
        tx += ctx.w
    if ty < 0:
        ty += ctx.h
    if 0 <= tx < ctx.w and 0 <= ty < ctx.h:
        px = ctx.img.load()
        old = px[ctx.x + tx, ctx.y + ty]
        px[ctx.x + tx, ctx.y + ty] = mix(old[:3], colour, alpha) + (255,)


def texrow(ctx, ty, x0, x1, colour, alpha=1.0):
    for tx in range(x0, x1 + 1):
        texel(ctx, tx, ty, colour, alpha)


def sk_base(ctx, base=SK_BASE):
    """Waxy, stretched, old skin: a flat base with slow mottling, a bruise now and then, a faint sheen on top faces."""
    fill(ctx, base, 0.035)
    blotch(ctx, SK_TAN, 2, 1.5, 4.5, 0.35)
    blotch(ctx, SK_CREAM, 1, 1.5, 4.0, 0.3)
    blotch(ctx, SK_PINK, 1, 1.0, 3.0, 0.32)
    r = ctx.rng.random()
    if r < 0.3:
        blotch(ctx, SK_BRUISE, 1, 1.0, 2.5, 0.3)
        blotch(ctx, SK_GREEN, 1, 1.5, 3.0, 0.18)
    elif r < 0.5:
        blotch(ctx, SK_GREEN, 1, 1.0, 2.5, 0.2)
    if ctx.face == "up":
        speckle(ctx, mix(base, SK_CREAM, 0.7), 0.1)
    speckle(ctx, shade(base, 0.9), 0.04)  # the faint sucker-bumps of the lore, under the stolen skin


def sk_skin(ctx):
    sk_base(ctx)


def sk_head(ctx):
    """A narrow skull: dark hollow sockets with small white eyes at different heights, a flattened nose, hollow cheeks
    and an upper lip that does not quite line up. The bottom rows are the inside of the mouth, behind the jaw."""
    sk_base(ctx, mix(SK_BASE, SK_CREAM, 0.25))
    if ctx.face == "west":
        w, h = ctx.w, ctx.h  # 9 x 12 for the 4.5 x 6 face
        texrow(ctx, 0, 0, w - 1, SK_CREAM, 0.35)                      # the stretched brow
        for x0 in (1, 5):                                              # brow shadow, sockets
            texrow(ctx, 2, x0, x0 + 2, SK_TAN, 0.5)
            for ty in (3, 4, 5):
                texrow(ctx, ty, x0, x0 + 2, SOCKET)
            texel(ctx, x0, 3, mix(SOCKET, SK_TAN, 0.35))
            texel(ctx, x0 + 2, 3, mix(SOCKET, SK_TAN, 0.35))
        texrow(ctx, 4, 1, 2, EYE_WHITE)                                # the eyes, one lower than the other, both
        texrow(ctx, 5, 5, 6, EYE_WHITE)                                # ... turned the same way in their sockets
        texel(ctx, 7, 5, mix(SOCKET, EYE_WHITE, 0.15))
        texel(ctx, 4, 3, SK_CREAM, 0.7)                                # the bridge of the nose
        texel(ctx, 4, 4, SK_CREAM, 0.9)
        texel(ctx, 4, 5, SK_CREAM, 0.8)
        texel(ctx, 4, 6, SK_TAN, 0.5)
        texel(ctx, 3, 7, SK_BROWN, 0.8)                                # nostrils, flattened
        texel(ctx, 5, 7, SK_BROWN, 0.8)
        texel(ctx, 4, 7, SK_TAN, 0.6)
        for ty in (5, 6, 7, 8):                                        # hollow cheeks
            texel(ctx, 0, ty, SK_TAN, 0.6)
            texel(ctx, w - 1, ty, SK_TAN, 0.5)
            texel(ctx, 1, ty, SK_TAN, 0.3)
        texrow(ctx, 8, 1, 6, MOUTH, 0.85)                              # the upper lip line, off centre
        texel(ctx, 7, 8, SK_PINK, 0.7)
        texel(ctx, 7, 9, MOUTH, 0.6)                                   # ... one corner pulled down
        for ty in (9, 10, 11):                                         # the inside of the mouth (behind the jaw)
            texrow(ctx, ty, 0, w - 1, MOUTH)
    elif ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.62, 0.45, 0.70, SK_TAN, 0.5)                   # the jaw hinge shadow
        blotch(ctx, SK_TAN, 1, 1.5, 2.5, 0.3)
    elif ctx.face == "east":
        line(ctx, 0.5, 0.6, 0.5, 1.0, SK_TAN, 0.4)                      # the nape
    elif ctx.face == "up":
        line(ctx, 0.3, 0.1, 0.5, 0.9, SK_CREAM, 0.35)                   # the skull's seam under thin skin


def sk_jaw(ctx):
    """The lower face: a slack grey-pink lower lip, a chin, a crease where the stolen skin bunches."""
    sk_base(ctx, mix(SK_BASE, SK_CREAM, 0.15))
    if ctx.face == "west":
        texrow(ctx, 0, 1, 6, SK_PINK, 0.85)                            # the lower lip
        texel(ctx, 1, 0, MOUTH, 0.5)
        texel(ctx, 7, 0, SK_PINK, 0.4)
        texel(ctx, 7, 1, MOUTH, 0.5)                                   # the pulled-down corner continues
        texrow(ctx, -1, 0, -1, SK_TAN, 0.55)                           # the crease under the chin
    elif ctx.face == "up":
        fill(ctx, MOUTH, 0.0, face_shade=False)                        # seen only when the jaw drops
    elif ctx.face == "down":
        texrow(ctx, 0, 0, -1, SK_TAN, 0.4)
    else:
        line(ctx, 0.0, 0.9, 1.0, 0.75, SK_TAN, 0.5)


def sk_fold(ctx):
    """The loose fold of skin under the jaw."""
    sk_base(ctx, mix(SK_BASE, SK_PINK, 0.45))
    if ctx.face in ("west", "north", "south"):
        texrow(ctx, -1, 0, -1, SK_BROWN, 0.6)
        texrow(ctx, 0, 0, -1, SK_TAN, 0.4)


def sk_neck(ctx):
    sk_base(ctx)
    if ctx.face == "west":
        line(ctx, 0.25, 0.0, 0.2, 1.0, SK_TAN, 0.5)                     # tendons
        line(ctx, 0.75, 0.0, 0.8, 1.0, SK_TAN, 0.5)
    elif ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.35, 1.0, 0.45, SK_TAN, 0.4)                    # a stretch wrinkle
    elif ctx.face == "east":
        line(ctx, 0.5, 0.0, 0.5, 1.0, SK_TAN, 0.45)


def sk_chest(ctx):
    """The upper torso: collarbones, a sternum line, faint ribs (not the same on both sides), shoulder blades."""
    sk_base(ctx)
    if ctx.face == "west":
        line(ctx, 0.08, 0.14, 0.46, 0.08, SK_TAN, 0.6)                  # collarbones
        line(ctx, 0.54, 0.09, 0.92, 0.16, SK_TAN, 0.6)
        line(ctx, 0.08, 0.20, 0.46, 0.14, SK_CREAM, 0.35)
        line(ctx, 0.50, 0.12, 0.50, 0.70, SK_TAN, 0.5)                  # the sternum, a hollow
        line(ctx, 0.50, 0.3, 0.50, 0.75, SK_BROWN, 0.25)
        for i, v in enumerate((0.38, 0.52, 0.66)):                     # ribs, the left side more prominent
            line(ctx, 0.08, v - 0.06, 0.46, v, SK_TAN, 0.4)
            if i < 2:
                line(ctx, 0.54, v + 0.03, 0.9, v - 0.03, SK_TAN, 0.3)
        blotch(ctx, SK_BRUISE, 1, 1.5, 3.0, 0.25)
    elif ctx.face == "east":
        for v in (0.15, 0.3, 0.45, 0.6, 0.75, 0.9):                     # the knuckles of the spine
            rect(ctx, 0.44, v, 0.56, v + 0.06, SK_TAN)
        line(ctx, 0.12, 0.2, 0.3, 0.55, SK_TAN, 0.5)                    # shoulder blades
        line(ctx, 0.88, 0.22, 0.72, 0.5, SK_TAN, 0.5)
    elif ctx.face in ("north", "south"):
        rect(ctx, 0.2, 0.0, 0.8, 0.22, SK_TAN)                           # the shadow under the arm
        for v in (0.4, 0.55, 0.7):
            line(ctx, 0.0, v, 1.0, v - 0.04, SK_TAN, 0.35)
    elif ctx.face == "up":
        line(ctx, 0.0, 0.5, 1.0, 0.5, SK_TAN, 0.3)


def sk_belly(ctx):
    sk_base(ctx)
    if ctx.face == "west":
        texel(ctx, ctx.w // 2 + 1, ctx.h * 2 // 3, SK_BROWN, 0.7)        # a navel, off centre
        line(ctx, 0.5, 0.0, 0.5, 0.5, SK_TAN, 0.3)
        blotch(ctx, SK_GREEN, 1, 1.5, 3.0, 0.2)
    elif ctx.face == "east":
        for v in (0.1, 0.3, 0.5, 0.7, 0.9):
            rect(ctx, 0.44, v, 0.56, v + 0.08, SK_TAN)
    elif ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.5, 1.0, 0.56, SK_TAN, 0.35)                    # the skin bunched at the waist
        line(ctx, 0.0, 0.95, 1.0, 0.95, SK_PINK, 0.4)


def sk_pelvis(ctx):
    sk_base(ctx)
    if ctx.face in ("west", "east"):
        line(ctx, 0.5, 0.3, 0.5, 1.0, SK_TAN, 0.4)
    if ctx.face == "west":
        line(ctx, 0.1, 0.1, 0.4, 0.9, SK_TAN, 0.35)                     # hip bones
        line(ctx, 0.9, 0.1, 0.6, 0.9, SK_TAN, 0.35)


def sk_upperarm(ctx):
    sk_base(ctx)
    if ctx.face in ("west", "east", "north", "south"):
        line(ctx, 0.0, 0.06, 1.0, 0.12, SK_TAN, 0.4)                    # the shoulder's edge
    if ctx.face in ("west", "north", "south"):
        line(ctx, 0.4, 0.3, 0.6, 0.9, SK_BRUISE, 0.2)                   # a vein


def sk_forearm(ctx):
    """Long forearms: the elbow crease on top, the skin bunched at the wrist, a vein or two."""
    sk_base(ctx)
    if ctx.face in ("west", "east", "north", "south"):
        line(ctx, 0.0, 0.08, 1.0, 0.08, SK_TAN, 0.55)                   # the elbow crease
        line(ctx, 0.0, 0.86, 1.0, 0.88, SK_PINK, 0.6)                   # wrist bunching
        line(ctx, 0.0, 0.94, 1.0, 0.94, SK_TAN, 0.55)
    if ctx.face in ("west", "north"):
        line(ctx, 0.3, 0.2, 0.6, 0.8, SK_BRUISE, 0.25)                  # a vein
    if ctx.face == "east":
        line(ctx, 0.5, 0.0, 0.5, 0.14, SK_BROWN, 0.35)                  # the point of the elbow


def sk_palm(ctx):
    sk_base(ctx)
    if ctx.face in ("west", "east"):
        texrow(ctx, -1, 0, -1, SK_BROWN, 0.45)                          # the knuckles
        blotch(ctx, SK_BRUISE, 1, 1.0, 2.0, 0.25)
    if ctx.face == "east":
        line(ctx, 0.5, 0.0, 0.5, 1.0, SK_TAN, 0.3)


def sk_finger(ctx):
    sk_base(ctx, mix(SK_BASE, SK_PINK, 0.15))
    if ctx.face in ("west", "east", "north", "south"):
        texrow(ctx, ctx.h // 2, 0, -1, SK_TAN, 0.5)                     # the knuckle
        texrow(ctx, -1, 0, -1, SK_BROWN, 0.6)                           # the nail's dark edge


def sk_thigh(ctx):
    sk_base(ctx)
    if ctx.face in ("west", "north", "south"):
        line(ctx, 0.0, 0.92, 1.0, 0.92, SK_TAN, 0.5)                    # stretched over the knee
    if ctx.face == "west":
        line(ctx, 0.5, 0.0, 0.5, 0.4, SK_CREAM, 0.3)


def sk_shin(ctx):
    sk_base(ctx)
    if ctx.face in ("west", "north", "south", "east"):
        line(ctx, 0.0, 0.08, 1.0, 0.08, SK_TAN, 0.55)                   # the knee
        line(ctx, 0.0, 0.14, 1.0, 0.14, SK_TAN, 0.3)
    if ctx.face == "west":
        line(ctx, 0.5, 0.2, 0.5, 0.95, SK_CREAM, 0.45)                  # the shin bone under thin skin
    if ctx.face == "east":
        line(ctx, 0.5, 0.3, 0.5, 0.7, SK_TAN, 0.3)


def sk_foot(ctx):
    sk_base(ctx)
    if ctx.face == "up":
        line(ctx, 0.1, 0.5, 0.5, 0.5, SK_TAN, 0.4)
    if ctx.face == "west":                                              # the toes
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, -1, SK_BROWN, 0.6)
    if ctx.face == "down":
        fill(ctx, SK_TAN, 0.05)


def plateau(phase, amp, k=1.4):
    """A sine with its peaks clipped: the limb pauses where it ends its swing (the foot planted a moment too long)."""
    return amp * max(-1.0, min(1.0, k * math.sin(TAU * phase)))


def ragged(ctx, depth=3):
    """Cuts the bottom edge of a face to transparency unevenly: hair ends, fur, worn wing edges."""
    px = ctx.img.load()
    for xx in range(ctx.w):
        cut = ctx.rng.choice([0] * 3 + list(range(1, depth + 1)))
        for yy in range(ctx.h - cut, ctx.h):
            px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)


def full(names, d):
    """A keyframe naming every part in `names`, at rest unless `d` poses it (the game needs every part in every frame)."""
    out = {n: pose() for n in names}
    out.update(d)
    return out


def ramp(p, a, b, c, d):
    """0 before a, rising to 1 at b, holding to c, falling to 0 at d."""
    if p <= a or p >= d:
        return 0.0
    if p < b:
        return (p - a) / (b - a)
    if p <= c:
        return 1.0
    return (d - p) / (d - c)


def skinstealer():
    m = Model("skinstealer", atlas_width=64, seed=10)
    # Torso chain. The rest rotations give the forward hunch: belly 3, chest 6 and neck 10 lean forward (19 in all);
    # the head takes 10 back so it pitches forward by 9 and sits forward of the shoulders on its too-long neck.
    pelvis = m.part("Pelvis", (-1.5, 16.5, -2.75), (3, 3, 5.5), pivot=(0, 18, 0), paint=sk_pelvis)
    belly = m.part("TorsoLower", (-1.75, 19.5, -2.75), (3.5, 4.5, 5.5), pivot=(0, 19.5, 0), parent=pelvis, rest=(0, 0, 3), paint=sk_belly)
    chest = m.part("TorsoUpper", (-2.25, 24, -3.5), (4, 5.5, 7), pivot=(0, 24, 0), parent=belly, rest=(0, 0, 6), paint=sk_chest)
    neck = m.part("Neck", (-1.125, 29.5, -1.125), (2.25, 3.5, 2.25), pivot=(0, 29.5, 0), parent=chest, rest=(0, 0, 10), paint=sk_neck)
    head = m.part("Head", (-3, 32.5, -2.25), (5, 6, 4.5), pivot=(0, 33, 0), parent=neck, rest=(5, -4, -10), paint=sk_head)
    m.part("Jaw", (-3.25, 32, -2.25), (2.75, 2, 4.5), pivot=(-0.5, 34, 0), parent=head, paint=sk_jaw)
    m.part("NeckFold", (-1.8, 30.9, -1.5), (0.75, 1.3, 3), pivot=(-1.05, 32.2, 0), parent=head, rest=(0, 0, -8), paint=sk_fold)

    # Arms: ordinary upper arms, forearms too long, flat hands with three stiff fingers reaching the knee.
    arm = m.part("ArmL", (-1.25, 22, 3.75), (2.5, 7, 2.5), pivot=(0, 28.75, 5), parent=chest, rest=(-3, 0, -15), paint=sk_upperarm)
    fore = m.part("ForearmL", (-1, 14, 4), (2, 8, 2), pivot=(0, 22, 5), parent=arm, rest=(4, 0, -12), paint=sk_forearm)
    palm = m.part("HandL", (-0.75, 11.5, 3.875), (1.5, 2.5, 2.25), pivot=(0, 14, 5), parent=fore, rest=(0, 0, 4), paint=sk_palm)
    for i in range(3):
        z = 4.0 + i * 0.8
        m.part(f"Finger{i}L", (-0.55, 9, z), (0.7, 2.5, 0.6), pivot=(-0.2, 11.5, z + 0.3), parent=palm, rest=(0, 0, -4 + 3 * i), paint=sk_finger)
    # Legs: thin, knees very slightly bent, feet flat and a little long, toes turned out a touch.
    thigh = m.part("ThighL", (-1.5, 9, 0.4), (3, 7.5, 3), pivot=(0, 16.5, 1.9), parent=pelvis, rest=(0, 0, -4), paint=sk_thigh)
    shin = m.part("ShinL", (-1.25, 1.5, 0.65), (2.5, 7.5, 2.5), pivot=(0, 9, 1.9), parent=thigh, rest=(0, 0, 8), paint=sk_shin)
    m.part("FootL", (-3.6, 0, 0.65), (4.75, 1.5, 2.5), pivot=(0, 1.5, 1.9), parent=shin, rest=(0, 7, -4), paint=sk_foot)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    # Asymmetry: the right shoulder rides higher and the right arm hangs a little further forward
    for name in ("ArmR", "ForearmR", "HandR", "Finger0R", "Finger1R", "Finger2R"):
        p = m.by_name[name]
        p.frm[1] += 0.5
        p.pivot[1] += 0.5
    m.by_name["ArmR"].rest = (3, 0, -19)
    m.by_name["ForearmR"].rest = (-2, 0, -10)

    # ---- Animations ----
    # Conventions: a hanging limb swings backward with +Z, an upright part leans forward with +Z; the left side is
    # +Z, so +X tilts the head to the left and swings the left arm inward (and the right arm outward).

    def gait(p, amp, lean, arm, bob, knee, head_wobble, fore_base):
        a = plateau(p, amp)                                 # the left thigh: forward while a > 0
        shin_l = knee * max(0.0, math.cos(TAU * p))         # the knee bends mid-swing, straight through the stance
        shin_r = knee * max(0.0, -math.cos(TAU * p))
        thigh_l, thigh_r = -a, a
        return {
            "ThighL": pose((2, 0, thigh_l)), "ThighR": pose((-2, 0, thigh_r)),                  # knees a touch inward
            "ShinL": pose((0, 0, shin_l)), "ShinR": pose((0, 0, shin_r)),
            "FootL": pose((0, 0, -(thigh_l + shin_l))), "FootR": pose((0, 0, -(thigh_r + shin_r))),  # placed flat
            "ArmL": pose((0, 0, s(p, amp * arm)), (0, 0.4, 0)), "ArmR": pose((0, 0, -s(p, amp * arm) * 0.8), (0, 0.5, 0)),
            "ForearmL": pose((0, 0, fore_base - 4 * max(0.0, -s(p, 1, -0.08)))),              # the forearms lag
            "ForearmR": pose((0, 0, fore_base - 4 * max(0.0, s(p, 1, -0.08)))),
            "Pelvis": pose((s(p, 2), 0, 0), (0, -bob * abs(math.sin(TAU * p)), 0)),
            "TorsoLower": pose((0, s(p, 3), lean)),
            "TorsoUpper": pose((0, -s(p, 2), lean * 0.5)),
            "Neck": pose((0, 0, s(p * 2, 1.5))),
            "Head": pose((s(p, head_wobble, 0.1), s(p, 5, -0.12), s(p * 2, head_wobble * 0.6, 0.3))),  # not quite in step
            "Jaw": pose((0, 0, max(0.0, s(p * 2, 2)))),
        }

    m.animation("walk", 40, cycle(40, 10, lambda p: gait(p, 26, 2, 0.3, 0.6, 32, 2, 0)))
    m.animation("run", 24, cycle(24, 8, lambda p: gait(p, 36, 9, 0.55, 1.0, 44, 5, -30)))

    def idle(p):
        sway = s(p, 1.5)
        breath = math.sin(TAU * p * 2)
        tilt = ramp(p, 0.55, 0.62, 0.80, 0.90)             # the delayed head tilt, once a loop
        twitch = ramp(p, 0.30, 0.33, 0.34, 0.40)           # a shoulder twitch
        return {
            "TorsoLower": pose((sway, 0, 0)),
            "TorsoUpper": pose((0, 0, breath), s=(1, 1 + 0.015 * breath, 1)),
            "Neck": pose((0, 0, -breath)),
            "Head": pose((9 * tilt - 0.4 * sway, -7 * tilt + s(p, 2, 0.4), 2 * tilt)),
            "ArmR": pose((0, 0, 4 * twitch), (0, 0.7 * twitch, 0)),
            "ArmL": pose((0, 0, s(p, 1.2))),
            "Finger0L": pose((0, 0, s(p * 3, 5))), "Finger2L": pose((0, 0, s(p * 3, 4, 0.3))),
            "Finger1R": pose((0, 0, s(p * 2, 5, 0.6))),
            "Jaw": pose((0, 0, max(0.0, s(p * 2, 2.5)))),
        }

    m.animation("idle", 80, cycle(80, 16, idle))

    # The signature: it drags a hand across its jaw and pulls at the loose skin under it, as if adjusting a collar.
    rest_adj = {k: pose() for k in ("ArmR", "ForearmR", "HandR", "Finger0R", "Finger1R", "Finger2R", "Head", "Neck", "Jaw", "NeckFold", "TorsoUpper")}
    m.animation("skinadjust", 72, {
        0: rest_adj,
        12: merge({0: rest_adj}, {0: {"ArmR": pose((-18, 0, -45)), "ForearmR": pose((-8, 0, -70)), "Head": pose((-4, 6, 0)),
                                     "Finger0R": pose((0, 0, -12)), "Finger1R": pose((0, 0, -15)), "Finger2R": pose((0, 0, -12))}})[0],
        22: merge({0: rest_adj}, {0: {"ArmR": pose((-38, 0, -62)), "ForearmR": pose((-14, 0, -124)), "HandR": pose((0, 0, -10)),
                                     "Head": pose((-10, 4, 6)), "Neck": pose((0, 0, 3)),
                                     "Finger0R": pose((0, 0, -22)), "Finger1R": pose((0, 0, -26)), "Finger2R": pose((0, 0, -20))}})[0],
        34: merge({0: rest_adj}, {0: {"ArmR": pose((-30, 0, -56)), "ForearmR": pose((-18, 0, -130)), "HandR": pose((0, 0, -16)),
                                     "Head": pose((-15, -8, 8)), "Neck": pose((0, 0, 5)), "Jaw": pose((0, 0, 7)),
                                     "NeckFold": pose((0, 0, -10), (-0.3, -0.3, 0)),
                                     "Finger0R": pose((0, 0, -26)), "Finger1R": pose((0, 0, -30)), "Finger2R": pose((0, 0, -24))}})[0],
        46: merge({0: rest_adj}, {0: {"ArmR": pose((-26, 0, -52)), "ForearmR": pose((-16, 0, -126)), "HandR": pose((0, 0, -12)),
                                     "Head": pose((-6, -4, 14)), "Neck": pose((0, 0, 8)), "Jaw": pose((0, 0, 4)),
                                     "NeckFold": pose((0, 0, -18), (-0.6, -0.6, 0), s=(1.4, 1.3, 1.0)),
                                     "TorsoUpper": pose((0, 4, 2)),
                                     "Finger0R": pose((0, 0, -30)), "Finger1R": pose((0, 0, -34)), "Finger2R": pose((0, 0, -28))}})[0],
        56: merge({0: rest_adj}, {0: {"ArmR": pose((-10, 0, -32)), "ForearmR": pose((-4, 0, -60)), "Head": pose((7, 3, -2)),
                                     "Finger0R": pose((0, 0, -10)), "Finger1R": pose((0, 0, -12)), "Finger2R": pose((0, 0, -8))}})[0],
        64: merge({0: rest_adj}, {0: {"Head": pose((4, 2, 0))}})[0],
        71: rest_adj,
    }, end="Stop")

    # Attack: a wind-up, then everything snaps forward: both arms rake, the head thrusts, the torso collapses into it.
    # (32 frames at 30 fps: the entity's damageAtMs 650 lands on the strike, frames 17-21.)
    rest_atk = {k: pose() for k in ("ArmL", "ArmR", "ForearmL", "ForearmR", "TorsoLower", "TorsoUpper", "Neck", "Head", "Jaw",
                                    "Finger0L", "Finger1L", "Finger2L", "Finger0R", "Finger1R", "Finger2R")}

    def fingers(curl):
        return {f"Finger{i}{side}": pose((0, 0, curl)) for i in range(3) for side in "LR"}

    m.animation("attack", 32, {
        0: rest_atk,
        10: merge({0: rest_atk}, {0: {"TorsoLower": pose((0, 0, -6)), "TorsoUpper": pose((0, 0, -10)), "Neck": pose((0, 0, -10)), "Head": pose((-4, 0, -4)),
                                     "ArmL": pose((-16, 0, 28)), "ArmR": pose((16, 0, 22)), "ForearmL": pose((0, 0, -22)), "ForearmR": pose((0, 0, -18)),
                                     "Jaw": pose((0, 0, 10))}}, {0: fingers(8)})[0],
        14: merge({0: rest_atk}, {0: {"TorsoLower": pose((0, 0, 4)), "TorsoUpper": pose((0, 0, 6)), "Neck": pose((0, 0, 2)), "Head": pose((-2, 0, 4)),
                                     "ArmL": pose((-6, 0, -150)), "ArmR": pose((4, 0, -138)), "ForearmL": pose((0, 0, -50)), "ForearmR": pose((0, 0, -44)),
                                     "Jaw": pose((0, 0, 24))}}, {0: fingers(-4)})[0],
        17: merge({0: rest_atk}, {0: {"TorsoLower": pose((0, 0, 14)), "TorsoUpper": pose((0, 0, 20)), "Neck": pose((0, 0, 10)), "Head": pose((0, 0, 12)),
                                     "ArmL": pose((12, 0, -98)), "ArmR": pose((-10, 0, -86)), "ForearmL": pose((0, 0, -30)), "ForearmR": pose((0, 0, -26)),
                                     "Jaw": pose((0, 0, 28))}}, {0: fingers(-28)})[0],
        21: merge({0: rest_atk}, {0: {"TorsoLower": pose((0, 0, 12)), "TorsoUpper": pose((0, 0, 16)), "Neck": pose((0, 0, 8)), "Head": pose((3, 0, 10)),
                                     "ArmL": pose((8, 0, -62)), "ArmR": pose((-6, 0, -54)), "ForearmL": pose((0, 0, -20)), "ForearmR": pose((0, 0, -18)),
                                     "Jaw": pose((0, 0, 22))}}, {0: fingers(-34)})[0],
        26: merge({0: rest_atk}, {0: {"TorsoLower": pose((0, 0, -2)), "TorsoUpper": pose((0, 0, -4)), "Neck": pose((0, 0, -4)), "Head": pose((5, 0, -2)),
                                     "ArmL": pose((0, 0, -40)), "ArmR": pose((0, 0, -34)), "ForearmL": pose((0, 0, -16)), "ForearmR": pose((0, 0, -14)),
                                     "Jaw": pose((0, 0, 8))}}, {0: fingers(-10)})[0],
        31: rest_atk,
    }, end="Stop")

    # Hurt: the shoulders recoil, the head jerks sideways and back, the torso twists.
    rest_hurt = {k: pose() for k in ("TorsoUpper", "Neck", "Head", "ArmL", "ArmR")}
    m.animation("hurt", 12, {
        0: rest_hurt,
        3: {"TorsoUpper": pose((0, 10, -14)), "Neck": pose((0, 0, -8)), "Head": pose((16, 6, -10)), "ArmL": pose((-15, 0, -20)), "ArmR": pose((8, 0, -10))},
        7: {"TorsoUpper": pose((0, 6, -8)), "Neck": pose((0, 0, -4)), "Head": pose((10, 0, -4)), "ArmL": pose((-8, 0, -10)), "ArmR": pose((4, 0, -5))},
        11: rest_hurt,
    }, end="Stop")

    # Death: whatever holds the skin up fails. The knees buckle, the torso folds, the head drops, one arm goes under
    # the body, and it all twists a little on the way down.
    rest_die = {k: pose() for k in ("Pelvis", "TorsoLower", "TorsoUpper", "Neck", "Head", "ThighL", "ThighR", "ShinL", "ShinR",
                                    "FootL", "FootR", "ArmL", "ArmR", "ForearmL", "ForearmR", "Jaw")}
    m.animation("die", 30, {
        0: rest_die,
        8: merge({0: rest_die}, {0: {"Pelvis": pose((0, 8, 0), (0, -4, 0)), "ThighL": pose((0, 0, -35)), "ThighR": pose((0, 0, -22)),
                                    "ShinL": pose((0, 0, 70)), "ShinR": pose((0, 0, 50)), "FootL": pose((0, 0, -25)), "FootR": pose((0, 0, -20)),
                                    "TorsoLower": pose((0, 0, 10)), "Neck": pose((0, 0, 6)), "Head": pose((-6, 0, 4)),
                                    "ArmL": pose((-12, 0, -10)), "ArmR": pose((-20, 0, 6)), "Jaw": pose((0, 0, 10))}})[0],
        16: merge({0: rest_die}, {0: {"Pelvis": pose((4, 22, 10), (0, -11, 0)), "ThighL": pose((0, 0, -80)), "ThighR": pose((0, 0, -60)),
                                     "ShinL": pose((0, 0, 105)), "ShinR": pose((0, 0, 95)), "FootL": pose((0, 0, -30)), "FootR": pose((0, 0, -40)),
                                     "TorsoLower": pose((0, 0, 35)), "TorsoUpper": pose((0, 6, 30)), "Neck": pose((0, 0, 20)), "Head": pose((-14, 0, 15)),
                                     "ArmL": pose((28, 0, -50)), "ForearmL": pose((0, 0, -60)), "ArmR": pose((-48, 0, -14)), "ForearmR": pose((0, 0, -20)),
                                     "Jaw": pose((0, 0, 16))}})[0],
        29: merge({0: rest_die}, {0: {"Pelvis": pose((8, 30, 25), (0, -13.5, 0)), "ThighL": pose((0, 0, -85)), "ThighR": pose((0, 0, -70)),
                                     "ShinL": pose((0, 0, 110)), "ShinR": pose((0, 0, 100)), "FootL": pose((0, 0, -30)), "FootR": pose((0, 0, -40)),
                                     "TorsoLower": pose((0, 0, 45)), "TorsoUpper": pose((0, 10, 35)), "Neck": pose((0, 0, 28)), "Head": pose((-22, 0, 20)),
                                     "ArmL": pose((36, 0, -70)), "ForearmL": pose((0, 0, -80)), "ArmR": pose((-58, 0, -8)), "ForearmR": pose((0, 0, -30)),
                                     "Jaw": pose((0, 0, 20))}})[0],
    }, end="Hold", stopped="Stop")
    return m


# Hound variants, painted on the common Hound's atlas so they work as texture alternates: the starved ones, paler and
# patchier with the ribs standing out; the old ones, greying, scarred, darker in the hands.
HOUND_VARIANTS = {
    "starved": dict(HD_SKIN=(244, 232, 220), HD_SHADOW=(200, 156, 142), HD_BRUISE=(172, 118, 132), HD_RED=(168, 84, 80)),
    "elder": dict(HD_SKIN=(206, 196, 184), HD_SHADOW=(150, 132, 124), HD_BRUISE=(128, 108, 116), HD_RED=(132, 68, 64),
                  HAIR=(84, 82, 80), HAIR_HI=(150, 146, 140), CLAW=(40, 34, 30)),
}


def hound_variant_textures():
    g = globals()
    saved = {k: g[k] for v in HOUND_VARIANTS.values() for k in v}
    for name, palette in HOUND_VARIANTS.items():
        g.update(palette)
        m = hound()
        width, height = m._pack()
        m._paint(width, height).save(os.path.join(ASSETS, "textures", "entity", f"hound-{name}.png"))
        print(f"wrote hound-{name} texture {width}x{height}")
        g.update(saved)


# ======================================================================== Hound
# "A human with long black hair growing on the head", "sickly skinny", walking on all fours on "arms and legs built for
# travel on all fours", with "sharp claws, and an extremely large mouth with sharp teeth" hidden behind the hair.
# The model is a human body adapted to a predator's stance, not a dog: human shoulders, elbows, hands, hips and knees,
# the knees sharply bent, the long arms holding up the front, the neck angled down, the back arched up to tall bony
# shoulders (the highest point). The head is a black shape of hair over a pale body; the hair hides a jaw hinged at
# the back of the skull so that, open, the mouth is far larger than a face should hold. About 22 px at the shoulder
# and 33 px long. Design brief: human at a distance (a survivor crawling?), wrong on approach.

HD_SKIN = (236, 222, 200)      # pale skin
HD_SHADOW = (184, 152, 132)    # shadow flesh
HD_BRUISE = (158, 122, 128)    # bruising
HD_RED = (152, 88, 82)         # red-brown flesh at the joints
HAIR = (22, 19, 18)
HAIR_HI = (58, 52, 50)
TEETH = (236, 230, 210)
MOUTH = (96, 30, 32)
CLAW = (66, 54, 46)
DIRT = (118, 98, 72)


def clear(ctx, tx, ty):
    if 0 <= tx < ctx.w and 0 <= ty < ctx.h:
        ctx.img.load()[ctx.x + tx, ctx.y + ty] = (0, 0, 0, 0)


def hd_skin(ctx):
    """Pale, patchy, unhealthy skin: shadow flesh in blotches, red at the joints, dirt on what touches the floor."""
    fill(ctx, HD_SKIN, 0.035)
    blotch(ctx, HD_SHADOW, 2, 1.5, 4.0, 0.35)
    blotch(ctx, HD_BRUISE, 1, 1.0, 2.5, 0.25)
    if ctx.rng.random() < 0.35:
        blotch(ctx, HD_RED, 1, 1.0, 2.0, 0.2)
    speckle(ctx, shade(HD_SKIN, 0.9), 0.04)


def hd_joint(ctx, top=True, bottom=True):
    """Darker, reddened skin folds where a limb bends: at the top and bottom of the part."""
    hd_skin(ctx)
    if ctx.face in ("north", "south", "east", "west"):
        if top:
            line(ctx, 0.0, 0.06, 1.0, 0.08, HD_RED, 0.45)
            line(ctx, 0.0, 0.14, 1.0, 0.12, HD_SHADOW, 0.35)
        if bottom:
            line(ctx, 0.0, 0.9, 1.0, 0.92, HD_RED, 0.4)
            line(ctx, 0.0, 0.84, 1.0, 0.86, HD_SHADOW, 0.3)


def hd_arm(ctx):
    hd_joint(ctx)
    if ctx.face == "west":
        line(ctx, 0.5, 0.2, 0.55, 0.8, HD_BRUISE, 0.25)  # a vein


def hd_forearm(ctx):
    hd_joint(ctx)
    if ctx.face == "east":
        line(ctx, 0.5, 0.0, 0.5, 0.12, HD_RED, 0.5)      # the point of the elbow


def hd_hand(ctx):
    hd_skin(ctx)
    if ctx.face == "up":
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, 0, HD_RED, 0.5)              # knuckles, reddened
    if ctx.face == "down":
        fill(ctx, mix(HD_SKIN, DIRT, 0.5), 0.05)


def hd_finger(ctx):
    """A long finger lying on the floor; its last third is a claw."""
    hd_skin(ctx)
    if ctx.face in ("up", "north", "south", "down"):
        n = max(1, ctx.w // 3)
        for tx in range(n):
            for ty in range(ctx.h):
                texel(ctx, tx, ty, CLAW)             # the claw at the tip (the finger's -X end is at u = 0)
        for ty in range(ctx.h):
            texel(ctx, n, ty, HD_RED, 0.5)
        texel(ctx, ctx.w // 2 + 1, 0, HD_SHADOW, 0.5)    # a knuckle
    if ctx.face == "west":
        fill(ctx, CLAW, 0.05)


def hd_thigh(ctx):
    hd_joint(ctx, top=False)
    if ctx.face in ("north", "south"):
        line(ctx, 0.3, 0.1, 0.5, 0.8, HD_SHADOW, 0.3)    # the hollow of a wasted thigh


def hd_shin(ctx):
    hd_joint(ctx, bottom=False)
    if ctx.face == "west":
        line(ctx, 0.5, 0.15, 0.5, 0.95, mix(HD_SKIN, (255, 255, 250), 0.5), 0.5)  # the shin bone


def hd_foot(ctx):
    hd_skin(ctx)
    if ctx.face == "up":
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, 0, CLAW, 0.7)
        line(ctx, 0.0, 0.5, 0.6, 0.5, HD_SHADOW, 0.35)    # a tendon
    if ctx.face == "down":
        fill(ctx, mix(HD_SKIN, DIRT, 0.55), 0.05)
    if ctx.face == "west":
        fill(ctx, CLAW, 0.05)


def hd_chest(ctx):
    """The ribcage: ribs round the sides, the spine's knuckles along the top, a sunken belly below."""
    hd_skin(ctx)
    if ctx.face in ("north", "south"):
        for u in (0.12, 0.3, 0.48, 0.66, 0.84):
            line(ctx, u, 0.05, u + 0.04, 0.72, HD_SHADOW, 0.55)
            line(ctx, u + 0.09, 0.05, u + 0.13, 0.72, mix(HD_SKIN, (255, 255, 255), 0.3), 0.4)
        rect(ctx, 0.0, 0.8, 1.0, 1.0, shade(HD_SKIN, 0.8))
    if ctx.face == "up":
        for u in (0.1, 0.3, 0.5, 0.7, 0.9):
            rect(ctx, u - 0.05, 0.4, u + 0.05, 0.6, HD_SHADOW)
    if ctx.face == "down":
        fill(ctx, shade(HD_SKIN, 0.8), 0.05)
        line(ctx, 0.5, 0.0, 0.5, 1.0, HD_SHADOW, 0.4)
    if ctx.face == "west":
        line(ctx, 0.1, 0.15, 0.45, 0.1, HD_SHADOW, 0.5)    # collarbones
        line(ctx, 0.55, 0.1, 0.9, 0.15, HD_SHADOW, 0.5)
        line(ctx, 0.5, 0.15, 0.5, 0.8, HD_SHADOW, 0.45)    # the sternum


def hd_rib(ctx):
    """A ridge of ribs standing out from the side of the chest."""
    hd_skin(ctx)
    if ctx.face in ("north", "south"):
        for u in (0.1, 0.3, 0.5, 0.7, 0.9):
            line(ctx, u, 0.0, u, 1.0, HD_SHADOW, 0.6)
            line(ctx, u + 0.08, 0.0, u + 0.08, 1.0, mix(HD_SKIN, (255, 255, 255), 0.35), 0.5)


def hd_spine(ctx):
    hd_skin(ctx)
    if ctx.face == "up":
        for u in (0.12, 0.37, 0.62, 0.87):
            rect(ctx, u - 0.07, 0.38, u + 0.07, 0.62, HD_SHADOW)
    if ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.3, 1.0, 0.35, HD_SHADOW, 0.35)
        rect(ctx, 0.0, 0.8, 1.0, 1.0, shade(HD_SKIN, 0.82))


def hd_pelvis(ctx):
    hd_skin(ctx)
    if ctx.face in ("north", "south"):
        line(ctx, 0.2, 0.1, 0.5, 0.6, HD_SHADOW, 0.5)      # the hip bone
    if ctx.face == "up":
        rect(ctx, 0.4, 0.3, 0.6, 0.7, HD_SHADOW)
    if ctx.face == "east":
        line(ctx, 0.5, 0.3, 0.5, 1.0, HD_SHADOW, 0.5)


def hd_blade(ctx):
    hd_skin(ctx)
    speckle(ctx, mix(HD_SKIN, (255, 255, 255), 0.4), 0.1)
    if ctx.face in ("north", "south", "west", "east"):
        line(ctx, 0.0, 0.5, 1.0, 0.5, HD_SHADOW, 0.35)


def hd_head(ctx):
    """The skull. Hair over the top and back; in front, under the brow, eyes that are hardly there."""
    fill(ctx, HD_SKIN, 0.035)
    blotch(ctx, HD_SHADOW, 2, 1.5, 3.0, 0.35)
    if ctx.face in ("up", "east"):
        fill(ctx, HAIR, 0.2, face_shade=False)
        vlines(ctx, HAIR_HI, 2, alpha=0.45, jitter=1)
    elif ctx.face == "west":
        w, h = ctx.w, ctx.h
        for ty in range(0, max(1, h // 3)):                               # hair down to the brow
            texrow(ctx, ty, 0, w - 1, HAIR)
        for ty in range(h // 3, h // 3 + 2):
            texrow(ctx, ty, 0, w - 1, HD_SHADOW, 0.5)                     # the brow's shadow
        ey = h // 3 + 2
        texrow(ctx, ey, 2, 3, mix(HD_SHADOW, (240, 240, 236), 0.75))      # pale eyes, hardly there
        texrow(ctx, ey + 1, w - 4, w - 3, mix(HD_SHADOW, (240, 240, 236), 0.6))
        for ty in range(ey, ey + 2):
            texel(ctx, 1, ty, HD_SHADOW, 0.6)
            texel(ctx, w - 2, ty, HD_SHADOW, 0.6)
        texel(ctx, w // 2, ey + 2, HD_SHADOW, 0.6)                       # the nose, flattened
        texel(ctx, w // 2, ey + 3, HD_RED, 0.5)
    elif ctx.face in ("north", "south"):
        rect(ctx, 0.0, 0.0, 1.0, 0.3, HAIR)
        line(ctx, 0.0, 0.7, 0.6, 0.75, HD_SHADOW, 0.5)                    # the jaw hinge
    elif ctx.face == "down":
        fill(ctx, MOUTH, 0.05, face_shade=False)


def hd_upperjaw(ctx):
    """The upper jaw: a lip line with the tips of teeth below it, and the roof of the mouth underneath."""
    fill(ctx, HD_SKIN, 0.035)
    blotch(ctx, HD_SHADOW, 1, 1.5, 3.0, 0.3)
    if ctx.face == "west":
        texrow(ctx, -2, 0, -1, MOUTH, 0.7)
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, -1, TEETH)
            texel(ctx, tx + 1, -1, MOUTH)
    elif ctx.face in ("north", "south"):
        texrow(ctx, -2, 0, ctx.w * 2 // 3, MOUTH, 0.7)                    # the mouth runs far back along the head
        for tx in range(0, ctx.w * 2 // 3, 2):
            texel(ctx, tx, -1, TEETH)
            texel(ctx, tx + 1, -1, MOUTH)
        texrow(ctx, -1, ctx.w * 2 // 3 + 1, -1, HD_RED, 0.5)
    elif ctx.face == "down":
        fill(ctx, MOUTH, 0.08, face_shade=False)
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, 0, TEETH)                                      # teeth along the front edge
            texel(ctx, tx, -1, TEETH)
        for ty in range(0, ctx.h, 2):
            texel(ctx, 0, ty, TEETH)
            texel(ctx, ctx.w - 1, ty, TEETH)
        line(ctx, 0.3, 0.5, 0.7, 0.5, shade(MOUTH, 0.6), 0.6)


def hd_jaw(ctx):
    """The lower jaw: skin and a lip in front, the floor of the mouth with a ring of teeth on top."""
    fill(ctx, HD_SKIN, 0.035)
    blotch(ctx, HD_SHADOW, 1, 1.5, 3.0, 0.3)
    if ctx.face == "up":
        fill(ctx, MOUTH, 0.08, face_shade=False)
        for tx in range(1, ctx.w, 2):
            texel(ctx, tx, 0, TEETH)
            texel(ctx, tx, -1, TEETH)
        for ty in range(1, ctx.h, 2):
            texel(ctx, 0, ty, TEETH)
            texel(ctx, ctx.w - 1, ty, TEETH)
        rect(ctx, 0.25, 0.3, 0.75, 0.8, mix(MOUTH, (200, 90, 100), 0.5))  # the tongue
    elif ctx.face == "west":
        texrow(ctx, 0, 0, -1, MOUTH, 0.6)
        for tx in range(1, ctx.w, 2):
            texel(ctx, tx, 0, TEETH)
    elif ctx.face in ("north", "south"):
        texrow(ctx, 0, 0, ctx.w * 2 // 3, MOUTH, 0.6)
        for tx in range(1, ctx.w * 2 // 3, 2):
            texel(ctx, tx, 0, TEETH)
    elif ctx.face == "down":
        fill(ctx, mix(HD_SKIN, DIRT, 0.3), 0.05)


def hd_tooth(ctx):
    fill(ctx, TEETH, 0.04, face_shade=False)
    if ctx.face != "up":
        texrow(ctx, -1, 0, -1, shade(TEETH, 0.75), 0.6)


def hd_hair(ctx):
    """Stringy neglected hair: black with grey streaks, the ends ragged (cut away to transparency)."""
    fill(ctx, HAIR, 0.25, face_shade=False)
    vlines(ctx, HAIR_HI, 2, alpha=0.45, jitter=1)
    speckle(ctx, DIRT, 0.015)
    if ctx.face in ("north", "south", "east", "west") and ctx.h >= 6:
        for tx in range(ctx.w):
            cut = ctx.rng.choice((0, 0, 1, 1, 2, 3))
            for ty in range(ctx.h - cut, ctx.h):
                clear(ctx, tx, ty)
            if cut == 0 and ctx.rng.random() < 0.3:
                clear(ctx, tx, ctx.h - 2)
    if ctx.face == "down":
        for tx in range(ctx.w):
            if ctx.rng.random() < 0.5:
                clear(ctx, tx, 0)


def hd_hair_plate(ctx):
    """Hair lying over the top of the head and down the neck onto the shoulders."""
    fill(ctx, HAIR, 0.25, face_shade=False)
    if ctx.face == "up":
        hlines(ctx, HAIR_HI, 2, alpha=0.35)
    elif ctx.face in ("north", "south"):
        vlines(ctx, HAIR_HI, 2, alpha=0.4, jitter=1)
    if ctx.face == "east":
        for tx in range(ctx.w):
            if ctx.rng.random() < 0.5:
                clear(ctx, tx, ctx.h - 1)


FRONT_HAIR = ((-2.75, 11.0), (-2.0, 9.0), (-1.25, 12.0), (-0.5, 8.5), (0.25, 10.5), (1.0, 12.5), (1.75, 9.5), (2.5, 11.5))


def hound():
    m = Model("hound", atlas_width=64, seed=8)
    # The body: a narrow chest with the shoulders the highest point, a spine arching back and down to a narrow
    # raised pelvis. The chest is the root.
    chest = m.part("Body", (-6, 15, -3), (7, 7, 6), pivot=(-2, 18.5, 0), paint=hd_chest)
    spine = m.part("Spine", (1, 15.5, -2.5), (6, 6.5, 5), pivot=(1, 18.5, 0), parent=chest, rest=(0, 0, -6), paint=hd_spine)
    pelvis = m.part("Pelvis", (7, 14, -2.25), (5, 5.5, 4.5), pivot=(7, 17, 0), parent=spine, rest=(0, 0, -8), paint=hd_pelvis)
    for side, z in (("L", 3), ("R", -3.5)):
        m.part("Rib" + side, (-4.5, 15.3, z), (5, 4.2, 0.5), pivot=(-2, 17.5, z), parent=chest, paint=hd_rib)
        m.part("Blade" + side, (-5.5, 21.8, z - (0 if side == "L" else 0.4) - (0.8 if side == "L" else 0)), (3.5, 1.4, 2.2), pivot=(-4, 21.8, z), parent=chest, paint=hd_blade)
    # A long neck angled down to a head that hangs below the shoulders
    neck = m.part("Neck", (-10.5, 17, -1.5), (5, 3.5, 3), pivot=(-5.5, 19, 0), parent=chest, rest=(0, 0, 22), paint=hd_joint)
    head = m.part("Head", (-16, 15, -3), (6, 6.5, 6), pivot=(-10, 19, 0), parent=neck, rest=(0, 0, -14), paint=hd_head)
    m.part("UpperJaw", (-17, 15, -2.75), (7, 2.5, 5.5), pivot=(-10, 16, 0), parent=head, paint=hd_upperjaw)
    jaw = m.part("Jaw", (-17, 13.4, -2.6), (7, 1.6, 5.2), pivot=(-10, 15, 0), parent=head, paint=hd_jaw)
    # Teeth as their own small cuboids: fangs hanging from the upper jaw, rising from the lower
    for i, (x, z) in enumerate(((-16.6, -2.2), (-16.6, -0.9), (-16.6, 0.4), (-16.6, 1.7), (-14.6, -2.75), (-14.6, 2.25))):
        m.part(f"FangU{i}", (x, 13.8, z), (0.5, 1.3, 0.5), pivot=(x, 15, z), parent=head, paint=hd_tooth)
    for i, (x, z) in enumerate(((-16.4, -1.7), (-16.4, 0.1), (-16.4, 1.5), (-14.2, -2.5), (-14.2, 2.0))):
        m.part(f"FangL{i}", (x, 15, z), (0.5, 1.2, 0.5), pivot=(x, 15, z), parent=jaw, paint=hd_tooth)
    # Hair: a crown, a curtain of uneven strands over the face past the jaw, plates down the sides, and hair lying
    # back over the neck onto the shoulders with strands hanging either side of the neck
    m.part("HairCrown", (-17.8, 21.5, -3.4), (8.2, 0.8, 6.8), pivot=(-13, 21.5, 0), parent=head, paint=hd_hair_plate)
    for i, (z, length) in enumerate(FRONT_HAIR):
        m.part(f"Hair{i}", (-18.0, 21.8 - length, z - 0.4), (0.6, length, 0.8), pivot=(-17.7, 21.8, z), parent=head,
               rest=(0, 0, (i % 3 - 1) * 3), paint=hd_hair)
    for side, z in (("L", 3.0), ("R", -3.6)):
        m.part(f"HairSide{side}0", (-17.6, 11, z), (4.8, 10.8, 0.6), pivot=(-15, 21.8, z + 0.3), parent=head, rest=(0, 0, 2 if side == "L" else -3), paint=hd_hair)
        m.part(f"HairSide{side}1", (-12.8, 12.5, z + (0.1 if side == "L" else -0.1)), (3.4, 9.3, 0.6), pivot=(-11, 21.8, z + 0.3), parent=head, paint=hd_hair)
    m.part("HairBack", (-10, 20.6, -2.8), (7.5, 0.9, 5.6), pivot=(-10, 20.6, 0), parent=neck, rest=(0, 0, -2), paint=hd_hair_plate)
    for side, z in (("L", 1.6), ("R", -2.2)):
        m.part(f"HairMane{side}0", (-9.5, 12.5, z), (2.8, 8.4, 0.6), pivot=(-8, 20.9, z + 0.3), parent=neck, rest=(0, 0, 4), paint=hd_hair)
        m.part(f"HairMane{side}1", (-6.5, 14, z + (0.3 if side == "L" else -0.3)), (2.4, 7, 0.6), pivot=(-5.3, 21, z + 0.3), parent=neck, paint=hd_hair)

    # Front limbs: human arms, long, with elbows, holding the front of the body up on long clawed fingers
    arm = m.part("ArmL", (-5.25, 11.5, 3), (2.5, 10, 2.5), pivot=(-4, 21.5, 4.25), parent=chest, rest=(-4, 0, -12), paint=hd_arm)
    fore = m.part("ForearmL", (-5, 1.5, 3.25), (2, 10, 2), pivot=(-4, 11.5, 4.25), parent=arm, rest=(2, 0, 12), paint=hd_forearm)
    hand = m.part("HandL", (-6.2, 0, 3), (2.4, 1.1, 2.5), pivot=(-4, 1.5, 4.25), parent=fore, paint=hd_hand)
    for i in range(3):
        z = 3.1 + i * 0.85
        m.part(f"Finger{i}L", (-9.3, 0.05, z), (3.2, 0.7, 0.6), pivot=(-6.2, 0.4, z + 0.3), parent=hand, rest=(0, (1 - i) * 9, 0), paint=hd_finger)
    # Hind limbs: human legs folded into a crouch, the knees far forward, long flat feet
    # (the spine and pelvis already tilt the hips 14 forward: the thigh ends up at -35, the shin at +30, the foot flat)
    thigh = m.part("ThighL", (8, 7.5, 2), (3, 9, 3), pivot=(9.5, 16.5, 3.5), parent=pelvis, rest=(0, 0, -21), paint=hd_thigh)
    shin = m.part("ShinL", (8.25, -1.5, 2.25), (2.5, 9, 2.5), pivot=(9.5, 7.5, 3.5), parent=thigh, rest=(0, 0, 65), paint=hd_shin)
    m.part("FootL", (5, -2.5, 2.2), (5.5, 1.0, 2.6), pivot=(9.5, -1.5, 3.5), parent=shin, rest=(0, 6, -30), paint=hd_foot)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    # Asymmetry: the right arm stands a little further forward and its hand turns out
    m.by_name["ArmR"].rest = (4, 0, -16)
    m.by_name["ForearmR"].rest = (-2, 0, 14)
    m.by_name["HandR"].rest = (0, -8, 0)

    hair_names = [f"Hair{i}" for i in range(len(FRONT_HAIR))] + ["HairSideL0", "HairSideL1", "HairSideR0", "HairSideR1",
                                                                 "HairManeL0", "HairManeL1", "HairManeR0", "HairManeR1"]

    def hair(p, sway=4.0, back=0.0, part_=0.0, shift=0.0):
        """Hair poses: a sway, blown back (+rotZ), and parted (front strands swung to their side) by `part_` degrees."""
        d = {}
        for i, (z, length) in enumerate(FRONT_HAIR):
            side = -1 if z < 0 else 1
            d[f"Hair{i}"] = pose((s(p, sway, i * 0.11 + shift) + side * part_, 0, back + s(p * 2, sway * 0.6, i * 0.07)))
        for n in ("HairSideL0", "HairSideL1"):
            d[n] = pose((part_ * 0.5 + s(p, sway * 0.5, 0.2), 0, back * 0.6))
        for n in ("HairSideR0", "HairSideR1"):
            d[n] = pose((-part_ * 0.5 - s(p, sway * 0.5, 0.3), 0, back * 0.6))
        for n in ("HairManeL0", "HairManeL1"):
            d[n] = pose((s(p, sway * 0.4, 0.4), 0, back * 0.3))
        for n in ("HairManeR0", "HairManeR1"):
            d[n] = pose((-s(p, sway * 0.4, 0.1), 0, back * 0.3))
        return d

    # ---- Animations ----
    # A hanging limb swings backward with +Z. Parts in front of their pivot (neck, head, jaw) drop with +Z, so the
    # jaw opens with +Z and the neck lifts with -Z. The body's pivot is in the chest: +Z lowers the front.

    def gait(p, amp, bob, lag, hand_lift, gallop):
        if gallop:
            fl, fr, hl, hr = s(p, amp), s(p, amp, -0.08), s(p, amp, 0.5 + lag), s(p, amp, 0.42 + lag)
            gather = math.sin(TAU * p)
        else:
            # Diagonal pairs (left arm with right leg), the hind legs lagging a little, the right arm's swing shorter
            fl, fr = plateau(p, amp, 1.6), plateau(p + 0.5, amp * 0.85, 1.6)
            hl, hr = plateau(p + 0.5 + lag, amp, 1.5), plateau(p + lag, amp, 1.5)
            gather = 0.0

        def swing(v):  # how far into its forward swing a limb is (0 while it bears weight)
            return max(0.0, -v) / amp

        d = {
            "ArmL": pose((0, 0, fl)), "ArmR": pose((0, 0, fr)),
            "ForearmL": pose((0, 0, 28 * swing(fl))), "ForearmR": pose((0, 0, 28 * swing(fr))),
            "HandL": pose((0, 0, -hand_lift * swing(fl))), "HandR": pose((0, 0, -hand_lift * swing(fr))),
            "ThighL": pose((0, 0, hl)), "ThighR": pose((0, 0, hr)),
            "ShinL": pose((0, 0, 30 * swing(hl))), "ShinR": pose((0, 0, 30 * swing(hr))),
            "FootL": pose((0, 0, -0.7 * (hl + 30 * swing(hl)))), "FootR": pose((0, 0, -0.7 * (hr + 30 * swing(hr)))),
            "Body": pose((s(p, 2.5), s(p, 2), 8 * gather), (-1.5 * gather if gallop else 0, bob * abs(math.sin(TAU * p)) + (1.2 * gather if gallop else 0), 0)),
            "Spine": pose((0, s(p, 1.5), -6 * gather)), "Pelvis": pose((0, 0, -6 * gather)),
            "Neck": pose((0, s(p, 4, 0.1), -4 * gather + s(p * 2, 2))),
            "Head": pose((s(p, 3, 0.2), s(p, 5, 0.15), s(p * 2, 2.5, 0.25))),
            "Jaw": pose((0, 0, (10 + 4 * gather) if gallop else max(0.0, s(p * 2, 2)))),
        }
        d.update(hair(p, sway=4 if not gallop else 7, back=22 + 6 * gather if gallop else 0))
        return d

    m.animation("walk", 36, cycle(36, 12, lambda p: gait(p, 28, 0.5, 0.08, 18, False)))
    m.animation("run", 18, cycle(18, 9, lambda p: gait(p, 40, 1.4, 0.05, 25, True)))

    def idle(p):
        breath = math.sin(TAU * p * 3)
        lower = ramp(p, 0.45, 0.55, 0.72, 0.85)            # the head drops and the shoulders lift
        step = ramp(p, 0.15, 0.18, 0.2, 0.26)              # a hand repositioned quickly
        twitch = ramp(p, 0.78, 0.79, 0.8, 0.83)
        d = {
            "Body": pose((0, 0, -2 * lower), (0, 0.4 * lower, 0), s=(1, 1 + 0.02 * breath, 1 + 0.02 * breath)),
            "Spine": pose((0, 0, 1.5 * breath + 2 * lower)), "Pelvis": pose((0, 0, 1.5 * lower)),
            "Neck": pose((0, s(p, 3, 0.3), 10 * lower - 1.5 * breath)),
            "Head": pose((s(p, 3), s(p, 6, 0.2) + 10 * twitch, -3 * lower)),
            "ArmL": pose((0, 0, 2 * lower - 14 * step), (0, 0, 0)), "ForearmL": pose((0, 0, 20 * step)), "HandL": pose((0, 0, -15 * step)),
            "ArmR": pose((0, 0, 2 * lower)),
            "ThighL": pose((0, 0, -2 * lower)), "ThighR": pose((0, 0, -2 * lower)),
            "Jaw": pose((0, 0, max(0.0, s(p * 2, 3)) + 3 * lower)),
        }
        d.update(hair(p, sway=3.5))
        return d

    m.animation("idle", 150, cycle(150, 20, idle))

    def full(names, d):
        out = {n: pose() for n in names}
        out.update(d)
        return out

    # Alert: the head snaps up and round toward a noise, sniffs, then turns the other way
    alert_names = ["Neck", "Head", "Jaw", "Body"] + hair_names
    m.animation("sniff", 40, {
        0: full(alert_names, hair(0)),
        4: full(alert_names, dict({"Neck": pose((0, 10, -28)), "Head": pose((0, 35, -6)), "Body": pose((0, 3, -2))}, **hair(0.1, back=10))),
        10: full(alert_names, dict({"Neck": pose((0, 12, -24)), "Head": pose((0, 38, -2)), "Jaw": pose((0, 0, 6)), "Body": pose((0, 3, -2))}, **hair(0.25, sway=3))),
        16: full(alert_names, dict({"Neck": pose((0, 10, -28)), "Head": pose((0, 36, -8)), "Jaw": pose((0, 0, 2)), "Body": pose((0, 3, -2))}, **hair(0.4, sway=3))),
        24: full(alert_names, dict({"Neck": pose((0, -8, -22)), "Head": pose((0, -30, -4)), "Jaw": pose((0, 0, 5)), "Body": pose((0, -2, -1))}, **hair(0.6, sway=5))),
        30: full(alert_names, dict({"Neck": pose((0, -10, -26)), "Head": pose((0, -34, -10)), "Jaw": pose((0, 0, 1)), "Body": pose((0, -2, -1))}, **hair(0.75, sway=3))),
        39: full(alert_names, hair(0.97)),
    })

    # Howl (kept for the hunt call): head thrown up, the mouth wide
    m.animation("howl", 50, {
        0: full(alert_names, hair(0)),
        12: full(alert_names, dict({"Neck": pose((0, 0, -50)), "Head": pose((0, 0, -30)), "Jaw": pose((0, 0, 55)), "Body": pose((0, 0, -10))}, **hair(0.2, back=35, part_=20))),
        38: full(alert_names, dict({"Neck": pose((0, 0, -54)), "Head": pose((0, 0, -32)), "Jaw": pose((0, 0, 60)), "Body": pose((0, 0, -10))}, **hair(0.6, back=38, part_=22))),
        49: full(alert_names, hair(0.95)),
    }, end="Stop")

    # Intimidated: the head drops, the jaw parts, the torso shakes with a growl, and it steps back a little
    growl_names = ["Neck", "Head", "Jaw", "Body", "ArmL", "ArmR", "ForearmL", "ForearmR"] + hair_names
    growl = {0: full(growl_names, hair(0))}
    for f in range(8, 38, 3):
        k = 1 if (f // 3) % 2 == 0 else -1
        back = min(1.0, (f - 8) / 12)
        growl[f] = full(growl_names, dict({
            "Neck": pose((0, 0, 14)), "Head": pose((k * 2, 0, -4)), "Jaw": pose((0, 0, 24 + k * 3)),
            "Body": pose((k * 1.5, 0, 1), (2.2 * back, 0, 0)),
            "ArmL": pose((0, 0, -9 * back)), "ArmR": pose((0, 0, -9 * back)), "ForearmL": pose((0, 0, 4 * back)), "ForearmR": pose((0, 0, 4 * back)),
        }, **hair(f / 45, sway=2, part_=6)))
    growl[44] = full(growl_names, hair(0.98))
    m.animation("growl", 45, growl, end="Stop")

    # Attack: the head recoils and the jaw parts, then the whole front lunges and the jaw snaps shut at the bite
    # (30 frames: the entity's damageAtMs 600 lands on frame 18, as the mouth closes).
    atk_names = ["Body", "Spine", "Neck", "Head", "Jaw", "ArmL", "ArmR", "ForearmL", "ForearmR", "HandL", "HandR"] + hair_names
    m.animation("attack", 30, {
        0: full(atk_names, hair(0)),
        8: full(atk_names, dict({"Body": pose((0, 0, -8), (1.5, 0, 0)), "Spine": pose((0, 0, 4)), "Neck": pose((0, 0, -26)), "Head": pose((0, 0, -16)), "Jaw": pose((0, 0, 48)),
                                 "ArmL": pose((0, 0, 14)), "ArmR": pose((0, 0, 12)), "ForearmL": pose((0, 0, -10)), "ForearmR": pose((0, 0, -8))}, **hair(0.2, back=12, part_=25))),
        14: full(atk_names, dict({"Body": pose((0, 0, 6), (-5, 0.5, 0)), "Spine": pose((0, 0, -4)), "Neck": pose((0, 0, -14), (-1.5, 0, 0)), "Head": pose((0, 0, -4)), "Jaw": pose((0, 0, 75)),
                                  "ArmL": pose((0, 0, -40)), "ArmR": pose((0, 0, -34)), "ForearmL": pose((0, 0, 10)), "ForearmR": pose((0, 0, 8)), "HandL": pose((0, 0, -20)), "HandR": pose((0, 0, -20))},
                                 **hair(0.4, back=40, part_=45))),
        18: full(atk_names, dict({"Body": pose((0, 0, 10), (-6, 0, 0)), "Spine": pose((0, 0, -6)), "Neck": pose((0, 0, 2), (-1.5, 0, 0)), "Head": pose((0, 0, 14)), "Jaw": pose((0, 0, 4)),
                                  "ArmL": pose((0, 0, -30)), "ArmR": pose((0, 0, -26)), "ForearmL": pose((0, 0, 6)), "ForearmR": pose((0, 0, 4))}, **hair(0.5, back=30, part_=35))),
        23: full(atk_names, dict({"Body": pose((0, 0, 4), (-3, 0, 0)), "Neck": pose((0, 0, -6)), "Head": pose((0, 0, 4)), "Jaw": pose((0, 0, 18)),
                                  "ArmL": pose((0, 0, -12)), "ArmR": pose((0, 0, -10))}, **hair(0.7, back=10, part_=15))),
        29: full(atk_names, hair(0.95)),
    }, end="Stop")

    # Hurt: a sharp recoil to one side
    hurt_names = ["Body", "Neck", "Head", "Jaw", "ArmL", "ForearmL"] + hair_names
    m.animation("hurt", 12, {
        0: full(hurt_names, hair(0)),
        3: full(hurt_names, dict({"Body": pose((10, 14, -6), (1.5, 0, 0)), "Neck": pose((0, 0, -12)), "Head": pose((8, 28, 0)), "Jaw": pose((0, 0, 20)),
                                  "ArmL": pose((-20, 0, -30)), "ForearmL": pose((0, 0, 25))}, **hair(0.3, sway=8, part_=10))),
        7: full(hurt_names, dict({"Body": pose((6, 8, -3), (0.5, 0, 0)), "Neck": pose((0, 0, -6)), "Head": pose((4, 14, 0)), "Jaw": pose((0, 0, 8)),
                                  "ArmL": pose((-8, 0, -12)), "ForearmL": pose((0, 0, 10))}, **hair(0.6, sway=5))),
        11: full(hurt_names, hair(0.95)),
    }, end="Stop")

    # Death: the front limbs buckle first, then the hind, and the body rolls onto its side with the jaw slack
    die_names = ["Body", "Spine", "Pelvis", "Neck", "Head", "Jaw", "ArmL", "ArmR", "ForearmL", "ForearmR", "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR"] + hair_names
    m.animation("die", 45, {
        0: full(die_names, hair(0)),
        12: full(die_names, dict({"Body": pose((0, 0, 16), (0, -6, 0)), "Spine": pose((0, 0, -10)), "Pelvis": pose((0, 0, -6)),
                                  "Neck": pose((0, 0, 10)), "Head": pose((0, 0, 8)), "Jaw": pose((0, 0, 20)),
                                  "ArmL": pose((-40, 0, 20)), "ArmR": pose((40, 0, 30)), "ForearmL": pose((0, 0, -50)), "ForearmR": pose((0, 0, -60)),
                                  "ThighL": pose((0, 0, -10)), "ThighR": pose((0, 0, -5))}, **hair(0.2, sway=6))),
        28: full(die_names, dict({"Body": pose((42, 0, 8), (0, -11, 0)), "Spine": pose((0, 0, -4)), "Pelvis": pose((0, 0, 4)),
                                  "Neck": pose((10, 0, 20)), "Head": pose((0, 0, 10)), "Jaw": pose((0, 0, 35)),
                                  "ArmL": pose((-20, 0, 30)), "ArmR": pose((25, 0, 40)), "ForearmL": pose((0, 0, -70)), "ForearmR": pose((0, 0, -80)),
                                  "ThighL": pose((-10, 0, 10)), "ThighR": pose((15, 0, -20)), "ShinL": pose((0, 0, 20)), "ShinR": pose((0, 0, 10)),
                                  "FootL": pose((0, 0, -10)), "FootR": pose((0, 0, -20))}, **hair(0.5, sway=5))),
        44: full(die_names, dict({"Body": pose((72, 0, 4), (0, -12.5, 0)), "Spine": pose((0, 0, -4)), "Pelvis": pose((0, 0, 6)),
                                  "Neck": pose((20, 0, 30)), "Head": pose((0, 0, 12)), "Jaw": pose((0, 0, 40)),
                                  "ArmL": pose((-25, 0, 40)), "ArmR": pose((30, 0, 50)), "ForearmL": pose((0, 0, -80)), "ForearmR": pose((0, 0, -90)),
                                  "ThighL": pose((-12, 0, 20)), "ThighR": pose((20, 0, -30)), "ShinL": pose((0, 0, 30)), "ShinR": pose((0, 0, 20)),
                                  "FootL": pose((0, 0, -10)), "FootR": pose((0, 0, -20))}, **hair(0.7, sway=3))),
    }, end="Hold", stopped="Stop")

    # The signature: a hind leg comes up and scratches at the shoulder and face, the head turning to it, like a dog's
    # scratch performed by a human leg.
    scr_names = ["Body", "Spine", "Pelvis", "Neck", "Head", "Jaw", "ThighR", "ShinR", "FootR", "ThighL", "ArmR", "ArmL"] + hair_names
    base = {"Body": pose((4, 0, -2), (0, 0, 0.6)), "Spine": pose((0, -6, 0)), "Pelvis": pose((0, -8, 2)), "ThighL": pose((6, 0, -6)),
            "Neck": pose((0, -14, 4)), "Head": pose((-12, -34, 0)), "ArmR": pose((0, 0, 4)), "ArmL": pose((0, 0, -3))}
    scratch = {0: full(scr_names, hair(0))}
    scratch[12] = full(scr_names, dict(base, **{"ThighR": pose((34, 0, -70)), "ShinR": pose((0, 0, -20)), "FootR": pose((0, 0, 30)), "Jaw": pose((0, 0, 8))}, **hair(0.15, sway=3)))
    for i, f in enumerate(range(18, 54, 3)):
        k = 1 if i % 2 == 0 else -1
        scratch[f] = full(scr_names, dict(base, **{
            "ThighR": pose((36, 0, -78 + k * 7)), "ShinR": pose((0, 0, -26 + k * 14)), "FootR": pose((0, 0, 34)), "Jaw": pose((0, 0, 10 + k * 2)),
            "Head": pose((-13 + k, -36, k * 2)), "Body": pose((4 + k * 0.5, 0, -2), (0, k * 0.15, 0.6)),
        }, **hair(f / 60, sway=5, shift=i * 0.2)))
    scratch[60] = full(scr_names, dict(base, **{"ThighR": pose((30, 0, -60)), "ShinR": pose((0, 0, -10)), "FootR": pose((0, 0, 25)), "Head": pose((-8, -20, 0))}, **hair(0.85, sway=3)))
    scratch[74] = full(scr_names, hair(0.98))
    m.animation("scratch", 75, scratch, end="Stop")
    return m


# ======================================================================== Duller
# "Tall, grey humanoid, frail skeletal structure", no face, no ears; arms of great length that reach through walls;
# "very wobbly", an "unnatural" walk, yet they run at extreme speeds. Design brief: the architecture turned predator.
# Less human than a Faceling, more abstract than a Skin-Stealer: a narrow unfinished head (no brow, no nose, no ears,
# no mouth, the skull long at the back and the jaw narrow, like a hood), a long thin neck, sloping shoulders, a torso
# too narrow to hold anything, arms hanging to mid-shin with hands too large and perfectly ordinary, thin legs that
# look about to give. Matte charcoal and ash, no warmth, no gore; darker bands at the joints. Each forearm hides two
# extension segments inside it that slide out when it reaches through a wall: a 24 px arm becomes 42. Standing
# 39.5 px raw, drawn at 0.92 for 36 px (2.3 blocks), a head over the player.

DU_SKIN = (78, 80, 88)        # charcoal
DU_ASH = (120, 122, 128)      # ash, on the crowns of the head and shoulders
DU_SLATE = (84, 90, 106)      # a blue-grey cast in the shadows
DU_SHADOW = (54, 56, 64)
DU_JOINT = (132, 134, 140)    # pale, chalky joints
DU_DARK = (42, 42, 48)        # the hands and feet, near black
DU_GRIME = (70, 62, 54)


def du_skin(ctx, base=DU_SKIN):
    """Dry, flat, chalky grey: barely any variation, a cool shadow, a little dust."""
    fill(ctx, base, 0.03)
    blotch(ctx, DU_SLATE, 1, 2, 5, 0.3)
    blotch(ctx, DU_ASH, 1, 1.5, 4, 0.2)
    speckle(ctx, shade(base, 1.15), 0.025)
    if ctx.face == "down":
        fill(ctx, DU_SHADOW, 0.03)


def du_banded(ctx, top=True, bottom=True, base=DU_SKIN):
    """A limb segment with a darker band and a pale knuckle of bone at the joints."""
    du_skin(ctx, base)
    if ctx.face in ("north", "south", "east", "west"):
        if top:
            texrow(ctx, 0, 0, -1, DU_SHADOW, 0.6)
            texrow(ctx, 1, 0, -1, DU_JOINT, 0.35)
        if bottom:
            texrow(ctx, -1, 0, -1, DU_SHADOW, 0.6)
            texrow(ctx, -2, 0, -1, DU_JOINT, 0.3)


def du_head(ctx):
    """Smooth, blank, slightly lighter than the body; a sheen where a face would be, nothing else."""
    fill(ctx, mix(DU_SKIN, DU_ASH, 0.4), 0.02)
    blotch(ctx, DU_ASH, 1, 2, 4, 0.3)
    if ctx.face == "west":
        blotch(ctx, mix(DU_ASH, (170, 172, 178), 0.4), 1, 2.5, 3.5, 0.3)
        line(ctx, 0.5, 0.3, 0.5, 0.95, DU_SHADOW, 0.12)                              # the faintest midline
    if ctx.face == "up":
        blotch(ctx, mix(DU_ASH, (170, 172, 178), 0.5), 1, 2, 3, 0.4)
    if ctx.face in ("north", "south"):
        blotch(ctx, DU_SLATE, 1, 1.5, 3, 0.3)                                        # where an ear is not


def du_torso(ctx):
    du_skin(ctx)
    if ctx.face in ("north", "south", "west"):
        hlines(ctx, DU_SHADOW, 3, start=3, alpha=0.3)                                  # ribs, barely
        if ctx.face == "west":
            line(ctx, 0.5, 0.1, 0.5, 0.8, DU_SHADOW, 0.35)
    if ctx.face == "east":
        for v in (0.1, 0.25, 0.4, 0.55, 0.7, 0.85):
            rect(ctx, 0.42, v, 0.58, v + 0.06, DU_JOINT)                               # the spine's knuckles
            rect(ctx, 0.42, v + 0.06, 0.58, v + 0.1, DU_SHADOW)


def du_hand(ctx):
    du_skin(ctx, mix(DU_SKIN, DU_DARK, 0.6))
    if ctx.face in ("west", "east"):
        texrow(ctx, -1, 0, -1, DU_JOINT, 0.4)                                          # knuckles


def du_finger(ctx):
    du_skin(ctx, mix(DU_SKIN, DU_DARK, 0.7))
    if ctx.face in ("west", "east", "north", "south"):
        texrow(ctx, ctx.h // 2, 0, -1, DU_JOINT, 0.35)


def du_foot(ctx):
    du_skin(ctx, mix(DU_SKIN, DU_DARK, 0.6))
    if ctx.face == "down":
        fill(ctx, mix(DU_DARK, DU_GRIME, 0.5), 0.04)


def du_arm(ctx):
    du_banded(ctx)


def du_forearm(ctx):
    du_banded(ctx)
    if ctx.face == "east":
        line(ctx, 0.5, 0.0, 0.5, 0.12, DU_JOINT, 0.5)                                  # the elbow's point


def du_extension(ctx):
    du_skin(ctx, mix(DU_SKIN, DU_SLATE, 0.3))
    if ctx.face in ("north", "south", "east", "west"):
        texrow(ctx, -1, 0, -1, DU_SHADOW, 0.5)


def duller():
    m = Model("duller", atlas_width=32, seed=6)
    # Legs: thin, knees slightly bent, feet not parallel, the pelvis drifting to one side
    pelvis = m.part("Pelvis", (-1.4, 18, -2.5), (2.8, 2.5, 5), pivot=(0, 19, 0), rest=(3, 0, 0), paint=du_skin)
    thigh = m.part("ThighL", (-1.4, 9.5, 0.4), (2.8, 8.8, 2.8), pivot=(0, 18.3, 1.8), parent=pelvis, rest=(4, 0, -5), paint=lambda c: du_banded(c, top=False))
    shin = m.part("ShinL", (-1.2, 1.0, 0.6), (2.4, 8.8, 2.4), pivot=(0, 9.6, 1.8), parent=thigh, rest=(0, 0, 9), paint=lambda c: du_banded(c, bottom=False))
    m.part("FootL", (-3.4, 0, 0.5), (4.6, 1.0, 2.6), pivot=(0, 1.0, 1.8), parent=shin, rest=(0, 11, -4), paint=du_foot)
    # Torso: too narrow, long; sloping shoulders; a long thin neck
    torso = m.part("Torso", (-1.6, 20.5, -2.75), (3.2, 10, 5.5), pivot=(0, 20.5, 0), parent=pelvis, rest=(-2, 0, 3), paint=du_torso)
    for side, z, dy in (("L", 2.0, 0.0), ("R", -4.6, -0.7)):
        sgn = 1 if side == "L" else -1
        m.part("Shoulder" + side, (-1.5, 29.6 + dy, z), (3.0, 1.4, 2.6), pivot=(0, 30.3 + dy, 1.0 if side == "L" else -1.0), parent=torso, rest=(-sgn * 16, 0, 0),
               paint=lambda c: du_skin(c, mix(DU_SKIN, DU_ASH, 0.3)))
    neck = m.part("Neck", (-0.7, 30.3, -0.7), (1.4, 3.6, 1.4), pivot=(0, 30.3, 0), parent=torso, rest=(0, 0, 4), paint=lambda c: du_banded(c, top=False))
    # The head: narrow, long at the back, no brow or nose or ears; a narrower jaw block below it
    head = m.part("Head", (-2.0, 33.5, -2.25), (5.0, 5.2, 4.5), pivot=(0, 33.6, 0), parent=neck, rest=(-4, 0, -3), paint=du_head)
    m.part("Skull", (0.5, 34.2, -1.9), (3.2, 4.2, 3.8), pivot=(2, 36, 0), parent=head, paint=du_head)              # the back of the skull, drawn out
    m.part("Jaw", (-1.7, 32.3, -1.7), (3.6, 1.4, 3.4), pivot=(0, 33.5, 0), parent=head, paint=du_head)
    # Arms: hanging to mid-shin, the hands too large; the right one hangs lower and further forward
    arm = m.part("ArmL", (-1.25, 21.0, 3.5), (2.5, 9, 2.5), pivot=(0, 29.8, 4.75), parent=torso, rest=(-5, 0, -4), paint=du_arm)
    fore = m.part("ForearmL", (-1.1, 11.0, 3.65), (2.2, 10, 2.2), pivot=(0, 21.0, 4.75), parent=arm, rest=(2, 0, -5), paint=du_forearm)
    # Two extension segments hidden inside the forearm; they slide out along it when the arm reaches through a wall
    ext1 = m.part("Ext0L", (-0.95, 11.3, 3.8), (1.9, 9.5, 1.9), pivot=(0, 20.8, 4.75), parent=fore, paint=du_extension)
    ext2 = m.part("Ext1L", (-0.8, 11.6, 3.95), (1.6, 9.0, 1.6), pivot=(0, 20.6, 4.75), parent=ext1, paint=du_extension)
    hand = m.part("HandL", (-0.75, 6.5, 3.4), (1.5, 4.5, 2.7), pivot=(0, 11.0, 4.75), parent=ext2, rest=(0, 0, 3), paint=du_hand)
    for i in range(4):
        z = 3.45 + i * 0.68
        m.part(f"Finger{i}L", (-0.55, 3.0, z), (0.6, 3.6, 0.55), pivot=(-0.25, 6.6, z + 0.27), parent=hand, rest=(0, 0, -6 + 4 * i), paint=du_finger)
    m.part("ThumbL", (-0.55, 5.0, 2.95), (0.6, 2.6, 0.5), pivot=(-0.25, 7.5, 3.2), parent=hand, rest=(22, 0, -10), paint=du_finger)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    for n in ("ArmR", "ForearmR", "Ext0R", "Ext1R", "HandR", "ThumbR") + tuple(f"Finger{i}R" for i in range(4)):
        p = m.by_name[n]
        p.frm[1] -= 0.7
        p.pivot[1] -= 0.7
    m.by_name["ArmR"].rest = (6, 0, -10)                 # hangs forward: the hand nearly drags
    m.by_name["ForearmR"].rest = (-2, 0, -8)
    m.by_name["FootR"].rest = (0, 4, -4)                 # the feet not parallel

    fingers_l = [f"Finger{i}L" for i in range(4)] + ["ThumbL"]
    fingers_r = [f"Finger{i}R" for i in range(4)] + ["ThumbR"]

    # ---- Animations ----
    # A hanging limb swings backward with +Z; +X tilts toward the left (+Z). The torso's +Z leans forward.
    def idle(p):
        sway = s(p, 3)
        lag = s(p, 3, -0.08)
        dip = ramp(p, 0.55, 0.62, 0.7, 0.8)
        knee = ramp(p, 0.3, 0.31, 0.32, 0.36) - ramp(p, 0.81, 0.82, 0.83, 0.87)
        d = {
            "Pelvis": pose((sway * 0.6, 0, 0), (0, 0, 0.15 * sway)),
            "Torso": pose((sway, s(p, 2, 0.2), s(p, 1.5))),
            "Neck": pose((-lag * 1.6, s(p, 4, 0.3), -s(p, 1.5))),                        # the head lags, and stays level-ish
            "ArmL": pose((s(p, 1.5), 0, s(p, 1.5, 0.1))), "ArmR": pose((s(p, 2.5, 0.05), 0, s(p, 4, 0.2))),   # one swings more
            "ForearmR": pose((0, 0, -s(p, 3, 0.3))),
            "ShoulderR": pose((0, 0, 0), (0, -0.5 * dip, 0)),
            "ShinL": pose((0, 0, 5 * knee)), "ShinR": pose((0, 0, -4 * knee)),            # tiny corrections at the knees
        }
        for i, f in enumerate(fingers_l + fingers_r):
            d[f] = pose((0, 0, 7 * math.sin(TAU * (p * 2 + i * 0.09))))                  # the fingers open and close
        return d

    m.animation("idle", 120, cycle(120, 20, idle))

    def walk(p, amp, lean, wobble, inward, bob, arm_lag):
        a = s(p, amp)
        bend_l, bend_r = max(0.0, math.cos(TAU * p)), max(0.0, -math.cos(TAU * (p + 0.07)))   # the knees not in step
        return {
            "ThighL": pose((inward, 0, -a)), "ThighR": pose((-inward, 0, a)),
            "ShinL": pose((0, 0, 34 * bend_l)), "ShinR": pose((0, 0, 30 * bend_r)),
            "FootL": pose((0, 0, -(-a + 34 * bend_l) * 0.6)), "FootR": pose((0, 0, -(a + 30 * bend_r) * 0.6)),
            "ArmL": pose((s(p, 2), 0, s(p - arm_lag, amp * 0.35))), "ArmR": pose((s(p, 2, 0.5), 0, -s(p - arm_lag, amp * 0.3))),
            "ForearmL": pose((0, 0, -4 - 4 * max(0.0, -s(p - arm_lag - 0.05, 1)))), "ForearmR": pose((0, 0, -4 - 4 * max(0.0, s(p - arm_lag - 0.05, 1)))),
            "Pelvis": pose((s(p, wobble), s(p, 4), lean * 0.4), (0, -bob * abs(math.sin(TAU * p)), 0)),
            "Torso": pose((s(p, wobble * 0.6, 0.12), -s(p, 3), lean * 0.6)),
            "Neck": pose((-s(p, wobble * 1.3, 0.06), s(p, 3, 0.2), -lean * 0.7)),       # the head stays level while the body wobbles
        }

    m.animation("walk", 48, cycle(48, 12, lambda p: walk(p, 26, 3, 9, 6, 0.6, 0.12)))
    m.animation("run", 18, cycle(18, 9, lambda p: dict(walk(p, 50, 26, 3, 2, 0.3, 0.02),
                                                      ArmL=pose((0, 0, 38 + s(p, 8))), ArmR=pose((0, 0, 36 + s(p, 8, 0.5))),
                                                      ForearmL=pose((0, 0, -20)), ForearmR=pose((0, 0, -20)))))

    # Listening: it stands by a wall, raises a palm flat against it, tilts its head and waits, then lowers the hand
    # (the entity's idle task plays this; the code is kept from the old model)
    listen_names = ["ArmL", "ForearmL", "HandL", "Neck", "Head", "Torso"] + fingers_l
    up = {"ArmL": pose((-6, 0, -84)), "ForearmL": pose((0, 0, -4)), "HandL": pose((0, 0, -78)), "Torso": pose((0, -6, 2))}
    spread = {f: pose((0, 0, (i - 2) * 5)) for i, f in enumerate(fingers_l)}
    m.animation("despair", 90, {
        0: full(listen_names, {}),
        14: full(listen_names, dict(up, **{"Neck": pose((8, -6, 0))}, **spread)),
        26: full(listen_names, dict(up, **{"Neck": pose((22, -10, 2)), "Head": pose((6, 0, 0))}, **spread)),
        50: full(listen_names, dict(up, **{"Neck": pose((24, 8, 2)), "Head": pose((6, 0, 0))}, **spread)),
        68: full(listen_names, dict(up, **{"Neck": pose((20, -4, 2)), "Head": pose((4, 0, 0))}, **spread)),
        80: full(listen_names, dict({"ArmL": pose((-3, 0, -30)), "ForearmL": pose((0, 0, -10)), "HandL": pose((0, 0, -20)), "Neck": pose((6, 0, 0))})),
        89: full(listen_names, {}),
    }, end="Stop")

    # The grab (27 frames, 0.9 s; the entity's damageAtMs 400 is frame 12): the body stays almost still. The arm rises
    # level, the hidden segments slide out along it, the hand snaps shut, and it all draws back.
    grab_names = ["ArmL", "ForearmL", "Ext0L", "Ext1L", "HandL", "Torso", "Neck"] + fingers_l

    def ext(k):
        """The extension segments slid out by k (0..1): each by its length, down the arm's own axis."""
        return {"Ext0L": pose((0, 0, 0), (0, -9.3 * k, 0)), "Ext1L": pose((0, 0, 0), (0, -8.8 * k, 0))}

    m.animation("attack", 27, {
        0: full(grab_names, {}),
        4: full(grab_names, dict({"ArmL": pose((-4, 0, -88)), "ForearmL": pose((0, 0, -4)), "HandL": pose((0, 0, -10)), "Torso": pose((0, 0, 2))}, **ext(0),
                                 **{f: pose((0, 0, -14)) for f in fingers_l})),
        8: full(grab_names, dict({"ArmL": pose((-4, 0, -90)), "ForearmL": pose((0, 0, -2)), "HandL": pose((0, 0, -16)), "Torso": pose((0, 0, 4))}, **ext(0.7),
                                 **{f: pose((0, 0, -30)) for f in fingers_l})),
        11: full(grab_names, dict({"ArmL": pose((-4, 0, -90)), "ForearmL": pose((0, 0, 0)), "HandL": pose((0, 0, -20)), "Torso": pose((0, 0, 5))}, **ext(1.0),
                                  **{f: pose((0, 0, -40)) for f in fingers_l})),
        13: full(grab_names, dict({"ArmL": pose((-4, 0, -90)), "ForearmL": pose((0, 0, 0)), "HandL": pose((0, 0, 10)), "Torso": pose((0, 0, 5))}, **ext(1.0),
                                  **{f: pose((0, 0, 55)) for f in fingers_l})),
        18: full(grab_names, dict({"ArmL": pose((-4, 0, -86)), "ForearmL": pose((0, 0, -6)), "HandL": pose((0, 0, 12)), "Torso": pose((0, 0, -2)), "Neck": pose((0, 0, -3))}, **ext(0.5),
                                  **{f: pose((0, 0, 55)) for f in fingers_l})),
        22: full(grab_names, dict({"ArmL": pose((-3, 0, -50)), "ForearmL": pose((0, 0, -16)), "HandL": pose((0, 0, 6))}, **ext(0.0),
                                  **{f: pose((0, 0, 30)) for f in fingers_l})),
        26: full(grab_names, {}),
    }, end="Stop")

    hurt_names = ["Torso", "Neck", "Head", "ArmL", "ArmR", "Pelvis"]
    m.animation("hurt", 12, {
        0: full(hurt_names, {}),
        3: full(hurt_names, {"Torso": pose((0, 12, -16)), "Neck": pose((24, 0, -10)), "Head": pose((8, 0, 0)), "ArmL": pose((-12, 0, -20)), "ArmR": pose((8, 0, -8)), "Pelvis": pose((0, 0, 0), (0.6, 0, 0))}),
        7: full(hurt_names, {"Torso": pose((0, 6, -8)), "Neck": pose((14, 0, -4)), "Head": pose((4, 0, 0)), "ArmL": pose((-6, 0, -10)), "ArmR": pose((4, 0, -4))}),
        11: full(hurt_names, {}),
    }, end="Stop")

    # Death: the balance it never quite had goes. Knees buckle, it folds, and the long arms sprawl out in front.
    die_names = ["Pelvis", "Torso", "Neck", "Head", "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR", "ArmL", "ArmR", "ForearmL", "ForearmR"]
    m.animation("die", 36, {
        0: full(die_names, {}),
        10: full(die_names, {"Pelvis": pose((6, 0, 6), (0, -5, 0)), "Torso": pose((0, 0, 20)), "Neck": pose((0, 0, 14)), "Head": pose((0, 0, 8)),
                             "ThighL": pose((0, 0, -50)), "ThighR": pose((0, 0, -36)), "ShinL": pose((0, 0, 95)), "ShinR": pose((0, 0, 85)),
                             "ArmL": pose((-12, 0, -20)), "ArmR": pose((16, 0, -6))}),
        20: full(die_names, {"Pelvis": pose((14, 10, 14), (0, -11, 0)), "Torso": pose((0, 4, 48)), "Neck": pose((6, 0, 26)), "Head": pose((0, 0, 14)),
                             "ThighL": pose((0, 0, -78)), "ThighR": pose((0, 0, -62)), "ShinL": pose((0, 0, 108)), "ShinR": pose((0, 0, 98)), "FootL": pose((0, 0, -30)), "FootR": pose((0, 0, -36)),
                             "ArmL": pose((-28, 0, -70)), "ArmR": pose((30, 0, -56)), "ForearmL": pose((0, 0, -20)), "ForearmR": pose((0, 0, -16))}),
        35: full(die_names, {"Pelvis": pose((18, 14, 20), (0, -13.5, 0)), "Torso": pose((0, 6, 60)), "Neck": pose((10, 0, 34)), "Head": pose((0, 0, 20)),
                             "ThighL": pose((0, 0, -84)), "ThighR": pose((0, 0, -70)), "ShinL": pose((0, 0, 112)), "ShinR": pose((0, 0, 104)), "FootL": pose((0, 0, -30)), "FootR": pose((0, 0, -36)),
                             "ArmL": pose((-34, 0, -96)), "ArmR": pose((36, 0, -84)), "ForearmL": pose((0, 0, -10)), "ForearmR": pose((0, 0, -6))}),
    }, end="Hold", stopped="Stop")
    return m


# ======================================================================== Death Rat
# "A normal house rat, with a long body, and black fur", with "strange brown horns coming out of their head, that has
# a red glow on the tips". The common form: 80% believable rat, 20% Backrooms. A low body on high haunches, a long
# tapered head held forward, big dirty incisors, round ears, whiskers, a long hairless tail in six segments that does
# much of the acting, and two short keratin horns swept back from the crown, brown at the root and glowing crimson at
# the tip. Dark eyes, not red: the red belongs to the horns. About 8 px at the shoulder (0.5 blocks) and 32 nose to
# tail. Design brief: a curious, skittish scavenger, dirty-cute rather than monstrous, so the variants have room.

RAT_VARIANTS = {
    # fur, fur streak, belly, skin (ears, paws, tail), hairless
    "common": dict(fur=(36, 33, 34), streak=(58, 48, 42), belly=(70, 62, 56), skin=(172, 126, 118), hairless=False),
    # Level 2's heat: hairless, grey-pink, the skin wrinkled
    "hairless": dict(fur=(148, 126, 122), streak=(118, 96, 94), belly=(170, 150, 146), skin=(176, 134, 128), hairless=True),
}
RV = RAT_VARIANTS["common"]
R_HORN = (94, 66, 40)
R_HORN_RUST = (132, 54, 38)
R_HORN_GLOW = (242, 72, 48)
R_TEETH = (222, 196, 128)
R_EYE = (10, 8, 8)
R_NOSE = (190, 118, 118)
R_CLAW = (70, 58, 48)


def r_fur(ctx):
    """Charcoal fur, not pure black: brown-black streaks running nose to tail, a few clumps, a lighter belly."""
    v = RV
    if v["hairless"]:
        fill(ctx, v["fur"], 0.04)
        hlines(ctx, v["streak"], 3, start=1, alpha=0.4)                 # wrinkles
        blotch(ctx, v["belly"], 1, 2, 4, 0.3)
        return
    fill(ctx, v["fur"], 0.14)
    if ctx.face in ("north", "south", "up"):
        hlines(ctx, v["streak"], 2, start=ctx.rng.randint(0, 1), alpha=0.35)
        speckle(ctx, shade(v["fur"], 1.5), 0.05)
        speckle(ctx, shade(v["fur"], 0.6), 0.05)
    if ctx.face == "down":
        fill(ctx, v["belly"], 0.1)
    if ctx.face in ("west", "east"):
        vlines(ctx, v["streak"], 2, alpha=0.3, jitter=1)


def r_rump(ctx):
    r_fur(ctx)
    if ctx.face in ("north", "south") and not RV["hairless"]:
        blotch(ctx, shade(RV["streak"], 1.2), 1, 2, 3, 0.3)             # a messy clump over the haunch


def r_head(ctx):
    r_fur(ctx)
    if ctx.face in ("north", "south"):
        # A tiny glossy dark eye, catching the light, set back from the snout (the snout is at u = 0, the -x end)
        texel(ctx, 1, ctx.h // 2 - 1, R_EYE)
        texel(ctx, 2, ctx.h // 2 - 1, R_EYE)
        texel(ctx, 1, ctx.h // 2, R_EYE)
        texel(ctx, 2, ctx.h // 2, R_EYE)
        texel(ctx, 1, ctx.h // 2 - 1, (200, 200, 200), 0.3)                # a glossy glint, just
        texel(ctx, 3, ctx.h // 2 + 1, shade(RV["fur"], 0.6), 0.6)       # the cheek's shadow
    if ctx.face == "up" and not RV["hairless"]:
        line(ctx, 0.5, 0.0, 0.5, 1.0, shade(RV["fur"], 0.7), 0.4)        # a parting between the horns


def r_snout(ctx):
    r_fur(ctx)
    if ctx.face == "west":
        texel(ctx, ctx.w // 2, 0, R_NOSE)                                  # the nose, at the very tip
        texel(ctx, ctx.w // 2 - 1, 0, R_NOSE, 0.8)
        texel(ctx, ctx.w // 2, 1, shade(R_NOSE, 0.7))
    if ctx.face in ("north", "south"):
        for ty in range(1, ctx.h, 2):
            texel(ctx, 0, ty, shade(RV["fur"], 1.5), 0.5)                  # whisker roots
    if ctx.face == "down":
        fill(ctx, mix(RV["belly"], RV["skin"], 0.4), 0.05)
        texrow(ctx, 0, 0, -1, (60, 36, 36), 0.8)                            # the mouth's line under the tip


def r_jaw(ctx):
    fill(ctx, mix(RV["belly"], RV["skin"], 0.3), 0.06)
    if ctx.face == "up":
        fill(ctx, (90, 36, 40), 0.05, face_shade=False)                    # the inside of the mouth


def r_ear(ctx):
    """A round ear: thin fur on the back, dark pink inside."""
    if ctx.face == "west":
        fill(ctx, shade(RV["skin"], 0.85), 0.06)
        blotch(ctx, shade(RV["skin"], 0.7), 1, 1, 2, 0.4)
    else:
        fill(ctx, mix(RV["fur"], RV["skin"], 0.35), 0.08)


def r_skin(ctx):
    fill(ctx, RV["skin"], 0.06)


def r_paw(ctx):
    fill(ctx, mix(RV["skin"], (150, 132, 108), 0.5), 0.06)                # dirty beige
    if ctx.face in ("west", "up"):
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, 0, R_CLAW)                                      # tiny claws at the toes
    if ctx.face == "up":
        line(ctx, 0.3, 0.5, 0.7, 0.5, shade(RV["skin"], 0.8), 0.4)


def r_tail(ctx):
    """Pink-brown, hairless, ringed."""
    fill(ctx, RV["skin"], 0.05)
    if ctx.face in ("north", "south", "up", "down"):
        vlines(ctx, shade(RV["skin"], 0.78), 2, start=1, alpha=0.6)      # the segment rings
    if ctx.face == "up":
        hlines(ctx, shade(RV["skin"], 1.12), 2, alpha=0.3)


def r_horn(ctx):
    """Brown at the root, rust toward the top: the tip is its own glowing part."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        t = yy / max(1, ctx.h - 1)                                         # 0 at the top of the part
        c = mix(R_HORN_RUST, R_HORN, t)
        for xx in range(ctx.w):
            m = 1 + 0.08 * (ctx.rng.random() - 0.5)
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(v * m for v in c)) + (255,)
    hlines(ctx, shade(R_HORN, 0.7), 2, start=1, alpha=0.4)                 # keratin ridges


def r_horntip(ctx):
    px = ctx.img.load()
    for yy in range(ctx.h):
        t = yy / max(1, ctx.h - 1)
        c = mix(R_HORN_GLOW, R_HORN_RUST, t * 0.7)
        for xx in range(ctx.w):
            px[ctx.x + xx, ctx.y + yy] = c + (255,)


def r_teeth(ctx):
    fill(ctx, R_TEETH, 0.05, face_shade=False)
    if ctx.face != "up":
        texrow(ctx, -1, 0, -1, shade(R_TEETH, 0.75), 0.6)


def r_whisker(ctx):
    fill(ctx, (196, 192, 186), 0.06, face_shade=False)


TAIL = ((3.0, 1.1), (3.0, 0.95), (2.5, 0.8), (2.5, 0.65), (2.0, 0.5), (2.0, 0.4))


def deathrat(variant="common"):
    global RV
    RV = RAT_VARIANTS[variant]
    m = Model("deathrat" if variant == "common" else f"deathrat-{variant}", atlas_width=32, seed=24)
    body = m.part("Body", (-4, 2.5, -2.75), (6, 5, 5.5), pivot=(0, 5, 0), paint=r_fur)
    rump = m.part("Rump", (2, 2, -3), (5, 6.2, 6), pivot=(2, 5, 0), parent=body, paint=r_rump)
    neck = m.part("Neck", (-6, 3.5, -2), (2.5, 3.5, 4), pivot=(-4, 5.5, 0), parent=body, rest=(0, 0, 8), paint=r_fur)
    head = m.part("Head", (-9.5, 3.6, -2), (4, 3.8, 4), pivot=(-5.5, 5.5, 0), parent=neck, rest=(0, 0, -4), paint=r_head)
    snout = m.part("Snout", (-12, 4, -1.3), (2.7, 2.4, 2.6), pivot=(-9.3, 5.2, 0), parent=head, rest=(0, 0, 4), paint=r_snout)
    jaw = m.part("Jaw", (-11.8, 3.6, -1.1), (2.5, 0.5, 2.2), pivot=(-9.3, 4.1, 0), parent=head, paint=r_jaw)
    for i, z in enumerate((-0.55, 0.15)):
        m.part(f"Incisor{i}", (-11.95, 3.2, z), (0.4, 1.0, 0.4), pivot=(-11.75, 4.2, z + 0.2), parent=snout, paint=r_teeth)
        m.part(f"LowerIncisor{i}", (-11.6, 3.75, z + 0.05), (0.3, 0.7, 0.3), pivot=(-11.45, 3.75, z + 0.2), parent=jaw, paint=r_teeth)
    # Whiskers: three hairline boxes a side, splayed, drooping a little
    for side, z0 in (("L", 1.3), ("R", -1.3)):
        sgn = 1 if side == "L" else -1
        for i, (y, yaw, droop) in enumerate(((4.6, -14, 10), (5.0, 0, 4), (5.4, 14, -2))):
            frm = (-11.1, y, z0) if side == "L" else (-11.1, y, z0 - 2.8)
            m.part(f"Whisker{side}{i}", frm, (0.12, 0.12, 2.8), pivot=(-11.05, y + 0.06, z0), parent=snout, rest=(sgn * droop, sgn * yaw, 0), paint=r_whisker)
    for side, z in (("L", 0.9), ("R", -2.5)):
        sgn = 1 if side == "L" else -1
        m.part(f"Ear{side}", (-7.6, 7.2, z), (0.4, 1.8, 1.6), pivot=(-7.4, 7.2, z + 0.8), parent=head, rest=(sgn * 22, 0, -10), paint=r_ear)
        hz = 0.35 if side == "L" else -1.05
        horn = m.part(f"Horn{side}", (-8.6, 7.3, hz), (0.7, 1.6, 0.7), pivot=(-8.25, 7.3, hz + 0.35), parent=head, rest=(sgn * 14, 0, -32), paint=r_horn)
        m.part(f"HornTip{side}", (-8.5, 8.9, hz + 0.1), (0.5, 1.2, 0.5), pivot=(-8.25, 8.9, hz + 0.35), parent=horn, rest=(sgn * 4, 0, -22), paint=r_horntip, glow=150)
    # Legs: small front paws with long fingers; big haunches, long planted hind feet
    for side, z in (("L", 1.4), ("R", -2.8)):
        leg = m.part(f"LegFront{side}", (-3.4, 0.8, z), (1.4, 2.6, 1.4), pivot=(-2.7, 3.2, z + 0.7), parent=body, paint=r_fur)
        m.part(f"PawFront{side}", (-4.3, 0, z - 0.05), (2.0, 0.8, 1.5), pivot=(-2.7, 0.8, z + 0.7), parent=leg, paint=r_paw)
    for side, z in (("L", 2.2), ("R", -4.0)):
        thigh = m.part(f"LegHind{side}", (3.5, 1.1, z), (2.3, 3.6, 1.8), pivot=(4.7, 4.5, z + 0.9), parent=rump, paint=r_fur)
        m.part(f"FootHind{side}", (2.4, 0, z + 0.1), (3.4, 1.1, 1.6), pivot=(5.3, 1.1, z + 0.9), parent=thigh, paint=r_paw)
    prev, x = rump, 7.0
    for i, (length, thick) in enumerate(TAIL):
        prev = m.part(f"Tail{i}", (x, 4.0 - thick / 2, -thick / 2), (length, thick, thick), pivot=(x, 4.0, 0), parent=prev,
                      rest=(0, 0, (-12, -8, -5, -2, 2, 5)[i]), paint=r_tail)
        x += length

    def tail(p, sweep=10.0, lift=0.0, shift=0.0, whip=0.0):
        """The tail sweeping side to side in a wave, lifted (or dropped) as a whole."""
        return {f"Tail{i}": pose((0, s(p, sweep + i * 3, i * 0.12 + shift) + whip * (i / 5), lift * (1 - i / 8))) for i in range(len(TAIL))}

    # ---- Animations ----
    # Legs hang from the body: +Z swings them backward. The neck and head are in front of their pivots: +Z drops them,
    # -Z lifts them; the jaw opens with +Z. The body's pivot is at mid-chest: -Z raises the front.
    def gait(p, amp, bob, head_low, bound):
        if bound:
            fl, fr = s(p, amp), s(p, amp, -0.06)
            hl, hr = s(p, amp, 0.5), s(p, amp, 0.44)
            g = math.sin(TAU * p)
        else:
            fl, fr, hl, hr = s(p, amp), s(p, amp, 0.5), s(p, amp, 0.5), s(p, amp, 0.0)
            g = 0.0
        d = {
            "LegFrontL": pose((0, 0, fl)), "LegFrontR": pose((0, 0, fr)), "LegHindL": pose((0, 0, hl)), "LegHindR": pose((0, 0, hr)),
            "PawFrontL": pose((0, 0, -fl * 0.4)), "PawFrontR": pose((0, 0, -fr * 0.4)),
            "FootHindL": pose((0, 0, -hl * 0.6)), "FootHindR": pose((0, 0, -hr * 0.6)),
            "Body": pose((s(p, 2), s(p, 2), 7 * g), (-1.0 * g if bound else 0, bob * abs(math.sin(TAU * p)) + (0.8 * g if bound else 0), 0)),
            "Rump": pose((0, 0, -5 * g)),
            "Neck": pose((0, s(p, 3, 0.1), head_low - 4 * g)), "Head": pose((s(p, 2), s(p, 4, 0.2), 0)),
            "Snout": pose((0, 0, s(p * 3, 2))),
        }
        d.update(tail(p, sweep=8 if bound else 12, lift=(8 if bound else 0)))
        return d

    m.animation("walk", 24, cycle(24, 8, lambda p: gait(p, 26, 0.3, 6, False)))
    m.animation("scamper", 14, cycle(14, 7, lambda p: gait(p, 32, 0.25, 0, False)))
    m.animation("run", 10, cycle(10, 5, lambda p: gait(p, 42, 0.8, -4, True)))

    def idle(p):
        breath = math.sin(TAU * p * 3)
        flick = ramp(p, 0.3, 0.31, 0.33, 0.37)
        shift = ramp(p, 0.6, 0.66, 0.72, 0.8)
        d = {
            "Body": pose((0, 0, 0), (0, 0, 0), s=(1, 1 + 0.02 * breath, 1 + 0.02 * breath)),
            "Neck": pose((0, s(p, 5, 0.3), 3 * shift)), "Head": pose((s(p, 3), s(p, 7, 0.2) - 10 * shift, 0)),
            "Snout": pose((0, s(p * 7, 1.5), s(p * 5, 1.5))),
            "EarL": pose((25 * flick, 0, 0)), "EarR": pose((0, 0, 0)),
            "LegFrontL": pose((0, 0, -6 * shift)), "PawFrontL": pose((0, 0, 6 * shift)),
        }
        d.update(tail(p, sweep=7))
        return d

    m.animation("idle", 90, cycle(90, 18, idle))

    def sniff(p):
        up = ramp(p, 0.0, 0.1, 0.85, 1.0)
        return dict({
            "Neck": pose((0, s(p, 12, 0.25), -10 * up + s(p * 2, 3))), "Head": pose((0, s(p, 18, 0.2), -6 * up)),
            "Snout": pose((0, s(p * 8, 2.5), s(p * 6, 3))),
            "EarL": pose((0, 0, 12 * up)), "EarR": pose((0, 0, 12 * up)),
            "Body": pose((0, 0, 0), (-0.6 * ramp(p, 0.4, 0.5, 0.6, 0.7), 0, 0)),
            "LegFrontL": pose((0, 0, -12 * ramp(p, 0.38, 0.46, 0.5, 0.62))),
        }, **tail(p, sweep=5, lift=3 * up))

    m.animation("sniff", 36, cycle(36, 12, sniff))

    # Groom: sits back on the haunches, the front paws come up and rub the snout and behind an ear, then it drops.
    groom_names = ["Body", "Rump", "LegHindL", "LegHindR", "FootHindL", "FootHindR", "LegFrontL", "LegFrontR", "PawFrontL", "PawFrontR",
                   "Neck", "Head", "Snout", "EarL"] + [f"Tail{i}" for i in range(len(TAIL))]
    sit = {"Body": pose((0, 0, -32), (0.5, 2.4, 0)), "Rump": pose((0, 0, 6)), "LegHindL": pose((0, 0, 26)), "LegHindR": pose((0, 0, 26)),
           "FootHindL": pose((0, 0, 6)), "FootHindR": pose((0, 0, 6))}

    def groom_frame(p, rub, ear):
        d = dict(sit)
        d.update({
            "LegFrontL": pose((0, 0, -78 + 8 * rub)), "LegFrontR": pose((0, 0, -74 - 8 * rub)),
            "PawFrontL": pose((0, 0, -50 - 10 * rub)), "PawFrontR": pose((0, 0, -46 + 10 * rub)),
            "Neck": pose((0, 0, 18)), "Head": pose((-10 * ear, 8 * rub, 22 - 10 * ear)), "Snout": pose((0, 0, 4 * rub)),
            "EarL": pose((20 * ear, 0, 0)),
        })
        d.update(tail(p, sweep=4, lift=-6))
        return d

    groom = {0: full(groom_names, tail(0)), 12: full(groom_names, groom_frame(0.13, 0, 0))}
    for i, f in enumerate(range(18, 60, 4)):
        groom[f] = full(groom_names, groom_frame(f / 90, 1 if i % 2 == 0 else -1, 0))
    for i, f in enumerate(range(62, 78, 4)):
        groom[f] = full(groom_names, groom_frame(f / 90, 0.5 if i % 2 == 0 else -0.5, 1))
    groom[82] = full(groom_names, groom_frame(0.9, 0, 0))
    groom[89] = full(groom_names, tail(0.99))
    m.animation("groom", 90, groom, end="Stop")

    # Rear up: rises onto the hind legs, paws tucked, nose high, sniffing the air; the signature pose.
    rear_names = groom_names + ["EarR"]
    rear = {"Body": pose((0, 0, -58), (1.0, 3.4, 0)), "Rump": pose((0, 0, 10)), "LegHindL": pose((0, 0, 46)), "LegHindR": pose((0, 0, 46)),
            "FootHindL": pose((0, 0, 4)), "FootHindR": pose((0, 0, 4)),
            "LegFrontL": pose((0, 0, -46)), "LegFrontR": pose((0, 0, -38)), "PawFrontL": pose((0, 0, -40)), "PawFrontR": pose((0, 0, -44)),
            "Neck": pose((0, 0, 26)), "Head": pose((0, 0, 12)), "EarL": pose((0, 0, 10)), "EarR": pose((0, 0, 10))}
    rearup = {0: full(rear_names, tail(0))}
    for f, yaw, sn in ((10, 0, 0), (18, 18, 3), (26, -6, -2), (34, 22, 3), (42, -14, -3), (48, 4, 0)):
        d = dict(rear)
        d["Head"] = pose((0, yaw, 12 + sn))
        d["Snout"] = pose((0, 0, sn * 1.5))
        d.update(tail(f / 60, sweep=4, lift=-14))
        rearup[f] = full(rear_names, d)
    rearup[54] = full(rear_names, dict({"Body": pose((0, 0, -20), (0.3, 1.0, 0)), "LegHindL": pose((0, 0, 16)), "LegHindR": pose((0, 0, 16)),
                                        "LegFrontL": pose((0, 0, -16)), "LegFrontR": pose((0, 0, -12)), "Neck": pose((0, 0, 8))}, **tail(0.9, sweep=4, lift=-4)))
    rearup[59] = full(rear_names, tail(0.98))
    m.animation("rearup", 60, rearup, end="Stop")

    # Eat: nose to the floor, nibbling, a paw holding the food down
    def eat(p):
        return dict({
            "Neck": pose((0, s(p, 2), 34)), "Head": pose((0, s(p, 3, 0.3), 14)), "Snout": pose((0, 0, s(p * 6, 2))),
            "Jaw": pose((0, 0, max(0.0, s(p * 6, 10)))),
            "Body": pose((0, 0, 4), (0, -0.3, 0)), "LegFrontL": pose((0, 0, -22)), "PawFrontL": pose((0, 0, 14)),
            "LegFrontR": pose((0, 0, 4)),
        }, **tail(p, sweep=5))

    m.animation("eat", 60, cycle(60, 12, eat))

    # Attack: a dart forward, a bite, and straight back (18 frames; the entity's damageAtMs 300 is frame 9)
    atk_names = ["Body", "Neck", "Head", "Jaw", "LegFrontL", "LegFrontR", "LegHindL", "LegHindR"] + [f"Tail{i}" for i in range(len(TAIL))]
    m.animation("attack", 18, {
        0: full(atk_names, tail(0)),
        4: full(atk_names, dict({"Body": pose((0, 0, -8), (0.8, 0.3, 0)), "Neck": pose((0, 0, -10)), "Head": pose((0, 0, -8)), "Jaw": pose((0, 0, 22)),
                                 "LegHindL": pose((0, 0, 20)), "LegHindR": pose((0, 0, 20))}, **tail(0.1, sweep=4, lift=6))),
        8: full(atk_names, dict({"Body": pose((0, 0, 6), (-3.2, 0, 0)), "Neck": pose((0, 0, 8)), "Head": pose((0, 0, 10)), "Jaw": pose((0, 0, 34)),
                                 "LegFrontL": pose((0, 0, -30)), "LegFrontR": pose((0, 0, -26)), "LegHindL": pose((0, 0, -25)), "LegHindR": pose((0, 0, -25))},
                                **tail(0.3, sweep=4, lift=14))),
        10: full(atk_names, dict({"Body": pose((0, 0, 6), (-3.4, 0, 0)), "Neck": pose((0, 0, 10)), "Head": pose((0, 0, 12)), "Jaw": pose((0, 0, 2)),
                                  "LegFrontL": pose((0, 0, -26)), "LegFrontR": pose((0, 0, -22)), "LegHindL": pose((0, 0, -22)), "LegHindR": pose((0, 0, -22))},
                                 **tail(0.4, sweep=4, lift=12))),
        14: full(atk_names, dict({"Body": pose((0, 4, -2), (1.5, 0.2, 0)), "Neck": pose((0, 6, -4)), "Head": pose((0, 8, -2)), "Jaw": pose((0, 0, 8)),
                                  "LegFrontL": pose((0, 0, 10)), "LegFrontR": pose((0, 0, 14))}, **tail(0.7, sweep=8, lift=4))),
        17: full(atk_names, tail(0.95)),
    }, end="Stop")

    hurt_names = ["Body", "Neck", "Head", "Jaw", "EarL", "EarR"] + [f"Tail{i}" for i in range(len(TAIL))]
    m.animation("hurt", 10, {
        0: full(hurt_names, tail(0)),
        3: full(hurt_names, dict({"Body": pose((14, 10, -4), (1.4, 0.4, 0)), "Neck": pose((0, 0, -8)), "Head": pose((0, 24, -6)), "Jaw": pose((0, 0, 24)),
                                  "EarL": pose((0, 0, 20)), "EarR": pose((0, 0, 20))}, **tail(0.2, sweep=14, lift=16))),
        6: full(hurt_names, dict({"Body": pose((6, 4, -2), (0.6, 0.1, 0)), "Head": pose((0, 10, -2)), "Jaw": pose((0, 0, 10)),
                                  "EarL": pose((0, 0, 10)), "EarR": pose((0, 0, 10))}, **tail(0.5, sweep=10, lift=8))),
        9: full(hurt_names, tail(0.9)),
    }, end="Stop")

    # Death: it stops, rolls onto its side, the legs curl in, the tail gives one last twitch
    die_names = ["Body", "Neck", "Head", "Jaw", "LegFrontL", "LegFrontR", "LegHindL", "LegHindR", "PawFrontL", "PawFrontR"] + [f"Tail{i}" for i in range(len(TAIL))]
    m.animation("die", 24, {
        0: full(die_names, tail(0)),
        8: full(die_names, dict({"Body": pose((40, 0, 4), (0, -0.6, 0)), "Neck": pose((0, 0, 10)), "Head": pose((8, 0, 6)), "Jaw": pose((0, 0, 14)),
                                 "LegFrontL": pose((0, 0, -30)), "LegFrontR": pose((0, 0, -20)), "LegHindL": pose((0, 0, 20)), "LegHindR": pose((0, 0, 30))},
                                **tail(0.2, sweep=6))),
        16: full(die_names, dict({"Body": pose((82, 0, 6), (0, -1.6, 0)), "Neck": pose((0, 0, 14)), "Head": pose((12, 0, 8)), "Jaw": pose((0, 0, 18)),
                                  "LegFrontL": pose((0, 0, -55)), "LegFrontR": pose((0, 0, -45)), "LegHindL": pose((0, 0, 45)), "LegHindR": pose((0, 0, 55)),
                                  "PawFrontL": pose((0, 0, -30)), "PawFrontR": pose((0, 0, -30))}, **tail(0.4, sweep=4, whip=40))),
        19: full(die_names, dict({"Body": pose((84, 0, 6), (0, -1.7, 0)), "Neck": pose((0, 0, 14)), "Head": pose((12, 0, 8)), "Jaw": pose((0, 0, 18)),
                                  "LegFrontL": pose((0, 0, -58)), "LegFrontR": pose((0, 0, -48)), "LegHindL": pose((0, 0, 48)), "LegHindR": pose((0, 0, 58)),
                                  "PawFrontL": pose((0, 0, -30)), "PawFrontR": pose((0, 0, -30))}, **tail(0.5, sweep=4, whip=-30))),
        23: full(die_names, dict({"Body": pose((85, 0, 6), (0, -1.7, 0)), "Neck": pose((0, 0, 14)), "Head": pose((12, 0, 8)), "Jaw": pose((0, 0, 18)),
                                  "LegFrontL": pose((0, 0, -60)), "LegFrontR": pose((0, 0, -50)), "LegHindL": pose((0, 0, 50)), "LegHindR": pose((0, 0, 60)),
                                  "PawFrontL": pose((0, 0, -30)), "PawFrontR": pose((0, 0, -30))}, **tail(0.5, sweep=0, lift=-4))),
    }, end="Hold", stopped="Stop")
    return m


def deathrat_variant_textures():
    """The variants' textures, painted onto the common rat's atlas layout so they work as texture alternates."""
    for variant in RAT_VARIANTS:
        if variant == "common":
            continue
        m = deathrat(variant)
        width, height = m._pack()
        img = m._paint(width, height)
        path = os.path.join(ASSETS, "textures", "entity", f"deathrat-{variant}.png")
        img.save(path)
        print(f"wrote deathrat-{variant} texture {width}x{height}")
    global RV
    RV = RAT_VARIANTS["common"]


# ======================================================================== Deathmoth
# Two pairs of membranous wings "covered in scales and microscopic fibers", compound eyes, ocelli, "a pair of
# feathered antennae", six clawed legs; males have "a long, needle-like proboscis", females "extended mandibles", a
# thicker body and a caustic organ in the abdomen. 70% moth, 20% predatory insect, 10% Backrooms: a small head, a
# fuzzy thorax, a banded tapering abdomen, forewings longer and pointed over rounder hindwings, and wing markings
# like water-stained wallpaper, so a resting moth all but disappears against the walls. A pair of false eye spots on
# the forewings opens with them. Male: 21 px wingspan, 9 px body, great plumed antennae, a proboscis coiled under the
# head that uncoils to feed. Female: 27 px wingspan, 12 px body, narrower antennae, dark mandibles, darker markings.

M_FUZZ = (150, 132, 108)
M_BODY = (88, 74, 62)
M_BAND = (176, 156, 118)
M_CHITIN = (54, 42, 36)
M_EYE = (62, 22, 26)
M_WING = (150, 134, 110)
M_WING_DARK = (72, 60, 52)
M_WING_GREY = (124, 118, 110)
M_WING_RED = (118, 76, 56)
M_CREAM = (214, 200, 168)

MF = {"female": False}


def m_fuzz(ctx):
    """The thorax's fur: pale tan fibres, dense, with a few dark hairs."""
    fill(ctx, M_FUZZ, 0.16)
    speckle(ctx, shade(M_FUZZ, 1.25), 0.14)
    speckle(ctx, M_BODY, 0.1)
    vlines(ctx, shade(M_FUZZ, 0.8), 2, alpha=0.3, jitter=1)


def m_fuzz_ragged(ctx):
    m_fuzz(ctx)
    if ctx.face in ("north", "south", "west", "east"):
        ragged(ctx, 2)


def m_body(ctx):
    fill(ctx, M_BODY, 0.1)
    speckle(ctx, shade(M_BODY, 1.3), 0.08)


def m_abdomen(ctx):
    """Segment bands round the abdomen: pale on the male, with a dark seam; the female's redder."""
    m_body(ctx)
    band = M_BAND if not MF["female"] else mix(M_BAND, (150, 80, 60), 0.5)
    if ctx.face in ("north", "south", "up", "down"):
        vlines(ctx, band, 3, start=1, alpha=0.75)
        vlines(ctx, shade(M_BODY, 0.6), 3, start=2, alpha=0.5)
    if ctx.face == "up":
        line(ctx, 0.0, 0.5, 1.0, 0.5, shade(M_BODY, 0.7), 0.4)              # the dorsal line
    if ctx.face == "down":
        fill(ctx, shade(M_BODY, 0.85), 0.08)
        vlines(ctx, band, 3, start=1, alpha=0.6)


def m_abdomen_tip(ctx):
    m_body(ctx)
    if MF["female"]:
        fill(ctx, mix(M_BODY, (130, 50, 44), 0.6), 0.1)                     # the caustic organ's dark red tip
        if ctx.face == "east":
            texel(ctx, ctx.w // 2, ctx.h // 2, (40, 14, 16))                 # the opening


def m_head(ctx):
    m_body(ctx)
    speckle(ctx, M_FUZZ, 0.15)
    if ctx.face == "up":
        for u in (0.3, 0.5, 0.7):                                             # the three ocelli
            texel(ctx, int(u * ctx.w), 0, (120, 60, 50))


def m_eye(ctx):
    """A compound eye: dark burgundy, faceted."""
    fill(ctx, M_EYE, 0.08, face_shade=False)
    speckle(ctx, shade(M_EYE, 1.5), 0.3)
    speckle(ctx, shade(M_EYE, 0.6), 0.2)
    if ctx.face in ("north", "south"):
        texel(ctx, 0, 0, mix(M_EYE, (255, 240, 240), 0.5), 0.8)              # a gloss glint


def m_chitin(ctx):
    fill(ctx, M_CHITIN, 0.1)
    if ctx.face in ("north", "south", "west", "east") and ctx.h >= 3:
        texrow(ctx, 0, 0, -1, shade(M_CHITIN, 1.4), 0.5)                      # a joint's rim


def m_claw(ctx):
    fill(ctx, shade(M_CHITIN, 0.7), 0.05)


def m_antenna(ctx):
    fill(ctx, (128, 104, 72), 0.12, face_shade=False)
    hlines(ctx, (90, 70, 48), 2, alpha=0.5)


def m_plume(ctx):
    """The antenna's feathering: a plane with a comb of fine barbs, cut to transparency between them."""
    fill(ctx, (150, 126, 86), 0.12, face_shade=False)
    if ctx.face in ("up", "down"):
        px = ctx.img.load()
        for xx in range(ctx.w):
            for yy in range(ctx.h):
                # Barbs every other column, thinning toward the tip (the tip is at u = 0, the -x end)
                keep = (xx % 2 == 0) and (yy / ctx.h) < (0.35 + 0.65 * xx / max(1, ctx.w - 1))
                if not keep and yy != ctx.h // 2:
                    px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)
    else:
        px = ctx.img.load()
        for xx in range(ctx.w):
            for yy in range(ctx.h):
                px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)


def m_proboscis(ctx):
    fill(ctx, (112, 86, 70), 0.1)
    hlines(ctx, (80, 60, 50), 2, alpha=0.4)


def m_wing(ctx):
    """Wing scales like water-stained wallpaper: dirty tan, charcoal and grey blotches, a dark band, veins fanning from
    the root (the root is at v = 0 for the left wing, the texture runs root to tip down the face), and a ragged edge.
    The forewing carries a false eye spot near its tip. The underside is paler and plainer."""
    female = MF["female"]
    under = ctx.face == "down"
    base = mix(M_WING, M_CREAM, 0.35) if under else (mix(M_WING, M_WING_DARK, 0.25) if female else M_WING)
    fill(ctx, base, 0.1, face_shade=False)
    blotch(ctx, M_WING_DARK, 3 if female else 2, 1.5, 4.0, 0.5 if not under else 0.25)
    blotch(ctx, M_WING_GREY, 2, 1.5, 3.5, 0.4)
    blotch(ctx, M_WING_RED, 1 if not female else 2, 1.5, 3.0, 0.35)
    blotch(ctx, M_CREAM, 1, 1.0, 2.5, 0.3)
    speckle(ctx, shade(base, 0.75), 0.06)
    # Veins fan from the root across the span; a dark band two thirds out
    for u in (0.15, 0.32, 0.5, 0.68, 0.85):
        line(ctx, u * 0.6 + 0.2, 0.0, u, 1.0, shade(base, 0.6), 0.45 if not under else 0.25)
    rect(ctx, 0.0, 0.62, 1.0, 0.7, mix(base, M_WING_DARK, 0.6 if not under else 0.3))
    if ctx.part.tag.get("fore") and not under:
        cu, cv = 0.5, 0.52
        for r, c in ((0.26, M_WING_DARK), (0.19, mix(M_WING_DARK, M_CREAM, 0.6)), (0.12, M_WING_DARK), (0.05, (20, 14, 14))):
            rect(ctx, cu - r * 0.9, cv - r, cu + r * 0.9, cv + r, c)
        texel(ctx, int(cu * ctx.w) - 1, int(cv * ctx.h) - 1, M_CREAM, 0.8)  # a highlight: it looks back at you
    if ctx.part.tag.get("tip"):
        ragged(ctx, 2)
    # The trailing edge is worn: cut a few texels from the long edge (the +x side is u = 1)
    px = ctx.img.load()
    for yy in range(ctx.h):
        if ctx.rng.random() < 0.35:
            px[ctx.x + ctx.w - 1, ctx.y + yy] = (0, 0, 0, 0)


def deathmoth(female):
    MF["female"] = female
    name = "deathmoth-female" if female else "deathmoth-male"
    m = Model(name, atlas_width=32, seed=4 + female)
    tag = {"female": True} if female else {}
    # Body: the thorax is the root; the abdomen tapers behind in two segments and a tip
    tx, th = (3.5, 3.2) if female else (3.0, 2.8)
    thorax = m.part("Thorax", (-tx / 2, 1.8, -th / 2), (tx, th, th), pivot=(0, 1.8 + th / 2, 0), paint=m_body, tag=tag)
    m.part("FuzzTop", (-tx / 2 - 0.2, 1.8 + th - 0.2, -th / 2 - 0.3), (tx + 0.4, 0.7, th + 0.6), pivot=(0, 1.8 + th, 0), parent=thorax, paint=m_fuzz_ragged)
    m.part("FuzzCollar", (-tx / 2 - 0.4, 1.8 + th * 0.35, -th / 2 - 0.25), (0.6, th * 0.75, th + 0.5), pivot=(-tx / 2, 1.8 + th / 2, 0), parent=thorax, paint=m_fuzz_ragged)
    m.part("FuzzBelly", (-tx / 2, 1.6, -th / 2 + 0.3), (tx, 0.4, th - 0.6), pivot=(0, 1.8, 0), parent=thorax, paint=m_fuzz)
    a1 = (3.2, 3.0) if female else (2.6, 2.4)
    a2 = (3.4, 2.4) if female else (2.2, 1.8)
    ab1 = m.part("Abdomen1", (tx / 2, 1.8 + th / 2 - a1[1] / 2, -a1[1] / 2), (a1[0], a1[1], a1[1]), pivot=(tx / 2, 1.8 + th / 2, 0), parent=thorax, rest=(0, 0, 6), paint=m_abdomen, tag=tag)
    x2 = tx / 2 + a1[0]
    ab2 = m.part("Abdomen2", (x2, 1.8 + th / 2 - a2[1] / 2, -a2[1] / 2), (a2[0], a2[1], a2[1]), pivot=(x2, 1.8 + th / 2, 0), parent=ab1, rest=(0, 0, 5), paint=m_abdomen, tag=tag)
    x3 = x2 + a2[0]
    t = 1.6 if female else 1.1
    m.part("AbdomenTip", (x3, 1.8 + th / 2 - t / 2, -t / 2), (1.4 if female else 1.0, t, t), pivot=(x3, 1.8 + th / 2, 0), parent=ab2, rest=(0, 0, 4), paint=m_abdomen_tip, tag=tag)
    # Head: small, with the compound eyes as their own boxes
    hx, hh, hw = (1.6, 1.8, 2.0) if female else (1.4, 1.6, 1.8)
    hy = 1.8 + th / 2 - hh / 2 + 0.1
    head = m.part("Head", (-tx / 2 - hx, hy, -hw / 2), (hx, hh, hw), pivot=(-tx / 2, 1.8 + th / 2, 0), parent=thorax, rest=(0, 0, -6), paint=m_head, tag=tag)
    for side, z in (("L", hw / 2 - 0.15), ("R", -hw / 2 - 0.4)):
        m.part("Eye" + side, (-tx / 2 - hx - 0.1, hy + hh * 0.35, z), (0.9, hh * 0.55, 0.55), pivot=(-tx / 2 - hx + 0.3, hy + hh * 0.6, z + 0.27), parent=head, paint=m_eye)
    # Antennae: a stalk and a plume of barbs; the male's are long and broad
    alen, aw = (2.6, 1.1) if not female else (2.0, 0.55)
    for side, z in (("L", 0.35), ("R", -0.5)):
        sgn = 1 if side == "L" else -1
        stalk = m.part("Antenna" + side, (-tx / 2 - hx - alen + 0.2, hy + hh - 0.1, z), (alen, 0.15, 0.15), pivot=(-tx / 2 - hx + 0.2, hy + hh - 0.05, z + 0.07),
                       parent=head, rest=(sgn * 18, sgn * 30, -22), paint=m_antenna)
        pz = z + 0.15 if side == "L" else z - aw
        m.part("Plume" + side, (-tx / 2 - hx - alen + 0.3, hy + hh - 0.1, pz), (alen - 0.4, 0.05, aw), pivot=(-tx / 2 - hx + 0.2, hy + hh - 0.05, z + 0.07),
               parent=stalk, paint=m_plume, faces=("up", "down"))
    # Mouthparts
    if female:
        for side, z in (("L", 0.05), ("R", -0.45)):
            sgn = 1 if side == "L" else -1
            jaw = m.part("Mandible" + side, (-tx / 2 - hx - 0.9, hy + 0.15, z), (0.9, 0.35, 0.4), pivot=(-tx / 2 - hx, hy + 0.3, z + 0.2), parent=head,
                         rest=(0, sgn * 22, 8), paint=m_chitin)
            m.part("MandibleTip" + side, (-tx / 2 - hx - 1.4, hy + 0.15, z + (0.1 if side == "L" else 0.0)), (0.5, 0.3, 0.3), pivot=(-tx / 2 - hx - 0.9, hy + 0.3, z + 0.2),
                   parent=jaw, rest=(0, -sgn * 30, 0), paint=m_claw)
    else:
        # The proboscis: three segments coiled under the head, uncoiling to feed
        px0 = -tx / 2 - hx + 0.3
        base = m.part("Proboscis0", (px0 - 1.0, hy - 0.05, -0.12), (1.0, 0.24, 0.24), pivot=(px0, hy + 0.07, 0), parent=head, rest=(0, 0, 70), paint=m_proboscis)
        mid = m.part("Proboscis1", (px0 - 2.0, hy - 0.05, -0.12), (1.0, 0.24, 0.24), pivot=(px0 - 1.0, hy + 0.07, 0), parent=base, rest=(0, 0, 85), paint=m_proboscis)
        m.part("Proboscis2", (px0 - 2.9, hy - 0.05, -0.1), (0.9, 0.2, 0.2), pivot=(px0 - 2.0, hy + 0.07, 0), parent=mid, rest=(0, 0, 85), paint=m_proboscis)
    # Wings: two pairs of planes; the forewing longer and pointed (a stepped tip), the hindwing shorter and rounder.
    span = 12.5 if female else 9.5
    flen, hlen = (5.0, 3.4) if female else (4.0, 2.8)
    wy = 1.8 + th - 0.1
    for side, sgn in (("L", 1), ("R", -1)):
        z0 = th / 2 - 0.2
        def zr(a, b):  # a z range a..b on this side, as (from, size)
            return (z0 + a, b - a) if sgn > 0 else (-z0 - b, b - a)
        zf, zs = zr(0, span * 0.7)
        fore = m.part("Forewing" + side, (-flen * 0.55, wy, zf), (flen, 0.12, zs), pivot=(-flen * 0.1, wy, z0 * sgn), parent=thorax,
                      paint=m_wing, faces=("up", "down"), tag={"fore": True})
        zf, zs = zr(span * 0.7, span)
        m.part("ForewingTip" + side, (-flen * 0.4, wy, zf), (flen * 0.62, 0.12, zs), pivot=(-flen * 0.1, wy, z0 * sgn), parent=fore,
               paint=m_wing, faces=("up", "down"), tag={"fore": True, "tip": True})
        zf, zs = zr(0, span * 0.55)
        hind = m.part("Hindwing" + side, (flen * 0.3, wy - 0.1, zf), (hlen, 0.12, zs), pivot=(flen * 0.3, wy - 0.1, z0 * sgn), parent=thorax,
                      paint=m_wing, faces=("up", "down"))
        zf, zs = zr(span * 0.55, span * 0.78)
        m.part("HindwingTip" + side, (flen * 0.3, wy - 0.1, zf), (hlen * 0.7, 0.12, zs), pivot=(flen * 0.3, wy - 0.1, z0 * sgn), parent=hind,
               paint=m_wing, faces=("up", "down"), tag={"tip": True})
        # Six legs: upper segment out and down, lower segment down and in, a clawed tarsus flat on the ground
        for i, (x, sweep) in enumerate(((-tx / 2 + 0.3, -35), (0.0, 0), (tx / 2 - 0.3, 35))):
            zl = (th / 2 - 0.1) * sgn
            up = m.part(f"Leg{i}{side}", (x - 0.15, 1.9 - 1.6, zl - 0.15), (0.3, 1.6, 0.3), pivot=(x, 1.9, zl), parent=thorax,
                        rest=(sgn * 55, 0, sweep), paint=m_chitin)
            low = m.part(f"Shin{i}{side}", (x - 0.12, 0.3 - 1.6, zl - 0.12), (0.24, 1.6, 0.24), pivot=(x, 0.3, zl), parent=up,
                         rest=(-sgn * 72, 0, 0), paint=m_chitin)
            m.part(f"Tarsus{i}{side}", (x - 0.4, -1.3 - 0.2, zl - 0.1), (0.8, 0.2, 0.2), pivot=(x, -1.3, zl), parent=low, rest=(sgn * 17, 0, 0), paint=m_claw)
    m.shift(dy=0.4)   # the rotated leg chain reaches 0.4 below the floor; stand on it

    wing_names = ["ForewingL", "ForewingR", "HindwingL", "HindwingR"]
    leg_names = [f"{p}{i}{s}" for p in ("Leg", "Shin") for i in range(3) for s in "LR"]

    def wings(up_fore, up_hind, back=0.0):
        """Wing poses: up_* lifts the wings about the body's axis (left and right mirrored); back sweeps them over the body."""
        return {"ForewingL": pose((up_fore, -back, 0)), "ForewingR": pose((-up_fore, back, 0)),   # (+up_fore drops the left tip)
                "HindwingL": pose((up_hind, -back * 0.85, 0)), "HindwingR": pose((-up_hind, back * 0.85, 0))}

    def legs_tucked(k):
        d = {}
        for i in range(3):
            for s, sgn in (("L", 1), ("R", -1)):
                d[f"Leg{i}{s}"] = pose((-sgn * 20 * k, 0, 30 * k))
                d[f"Shin{i}{s}"] = pose((sgn * 30 * k, 0, 0))
        return d

    def antennae(p, amp=6):
        return {"AntennaL": pose((s(p, amp), s(p, amp * 0.6, 0.3), 0)), "AntennaR": pose((-s(p, amp, 0.1), -s(p, amp * 0.6, 0.4), 0))}

    # Flight: a fast beat (the butterfly class plays it at 2.5x: 16 frames give about 4.7 beats a second), the hindwings a little behind; the body bobs only slightly
    m.animation("fly", 16, cycle(16, 8, lambda p: dict(wings(-62 * math.cos(TAU * p) - 8, -56 * math.cos(TAU * (p - 0.1)) - 6),
                                                     Thorax=pose((0, 0, 0), (0, 0.3 * math.sin(TAU * p), 0)),
                                                     Abdomen1=pose((0, 0, s(p, 5))), Abdomen2=pose((0, 0, s(p, 4, 0.1))),
                                                     **legs_tucked(1.0), **antennae(p * 0.5, 3))))
    m.animation("glide", 30, cycle(30, 6, lambda p: dict(wings(-14 + s(p, 5), -12 + s(p, 5, 0.1)), Abdomen1=pose((0, 0, s(p, 3))),
                                                        **legs_tucked(1.0), **antennae(p, 5))))
    # Resting: wings folded back over the abdomen in a shallow roof, standing on all six, antennae feeling the air,
    # a shiver through the wings now and then
    def rest(p):
        shiver = ramp(p, 0.55, 0.57, 0.6, 0.66) * math.sin(TAU * p * 20)
        d = wings(22 + 6 * shiver, 16 + 5 * shiver, back=72)   # +X tilt drops the outer edges: a shallow roof
        d.update(antennae(p, 8))
        d["Abdomen1"] = pose((0, 0, 0), s=(1, 1 + 0.03 * math.sin(TAU * p * 2), 1 + 0.03 * math.sin(TAU * p * 2)))
        d["Head"] = pose((0, s(p, 4, 0.2), 0))
        return d

    m.animation("rest", 60, cycle(60, 12, rest))

    if female:
        # Feeding: head down into the meat, the mandibles working
        m.animation("feed", 30, cycle(30, 6, lambda p: dict(wings(22, 16, back=72), Head=pose((0, 0, 16 + s(p, 4))),
                                                            MandibleL=pose((0, -14 * abs(math.sin(TAU * p)), 0)), MandibleR=pose((0, 14 * abs(math.sin(TAU * p)), 0)),
                                                            **antennae(p, 3))))
        # Bite: a lunge of the head, the mandibles opening wide and snapping shut, the wings flicking (12 frames, 0.4 s)
        bite_names = ["Thorax", "Head", "MandibleL", "MandibleR"] + wing_names
        m.animation("bite", 12, {
            0: full(bite_names, {}),
            3: full(bite_names, dict({"Thorax": pose((0, 0, -6), (0.6, 0, 0)), "Head": pose((0, 0, -10)), "MandibleL": pose((0, -40, 0)), "MandibleR": pose((0, 40, 0))}, **wings(-30, -26))),
            6: full(bite_names, dict({"Thorax": pose((0, 0, 8), (-1.4, 0, 0)), "Head": pose((0, 0, 18)), "MandibleL": pose((0, 24, 0)), "MandibleR": pose((0, -24, 0))}, **wings(10, 8))),
            8: full(bite_names, dict({"Thorax": pose((0, 0, 6), (-1.2, 0, 0)), "Head": pose((0, 0, 14)), "MandibleL": pose((0, 26, 0)), "MandibleR": pose((0, -26, 0))}, **wings(-10, -8))),
            11: full(bite_names, {}),
        }, end="Stop")
        # Threat: the wings snap open to show the eye spots, the front legs rise, the abdomen curls under to spray
        threat_names = ["Thorax", "Head", "Abdomen1", "Abdomen2", "AbdomenTip", "Leg0L", "Leg0R", "MandibleL", "MandibleR"] + wing_names
        m.animation("threat", 40, {
            0: full(threat_names, wings(22, 16, back=72)),
            5: full(threat_names, dict({"Thorax": pose((0, 0, -12)), "Leg0L": pose((0, 0, -50)), "Leg0R": pose((0, 0, -50)), "MandibleL": pose((0, -30, 0)), "MandibleR": pose((0, 30, 0))},
                                       **wings(-8, -6))),
            12: full(threat_names, dict({"Thorax": pose((0, 0, -16)), "Head": pose((0, 0, -8)), "Leg0L": pose((0, 0, -60)), "Leg0R": pose((0, 0, -60)),
                                        "Abdomen1": pose((0, 0, -30)), "Abdomen2": pose((0, 0, -40)), "AbdomenTip": pose((0, 0, -30)),
                                        "MandibleL": pose((0, -35, 0)), "MandibleR": pose((0, 35, 0))}, **wings(6, 4))),
            26: full(threat_names, dict({"Thorax": pose((0, 0, -16)), "Head": pose((0, 0, -8)), "Leg0L": pose((0, 0, -56)), "Leg0R": pose((0, 0, -64)),
                                        "Abdomen1": pose((0, 0, -34)), "Abdomen2": pose((0, 0, -44)), "AbdomenTip": pose((0, 0, -34)),
                                        "MandibleL": pose((0, -35, 0)), "MandibleR": pose((0, 35, 0))}, **wings(-4, -2))),
            39: full(threat_names, wings(22, 16, back=72)),
        }, end="Stop")
    else:
        # Feeding: the proboscis uncoils and goes down into the spill, the head bowing to it
        def feed(p):
            d = wings(22, 16, back=72)
            ext = ramp(p, 0.0, 0.25, 0.85, 1.0)
            d.update({"Head": pose((0, s(p, 2), 10 * ext)), "Proboscis0": pose((0, 0, 20 * ext)), "Proboscis1": pose((0, 0, -85 * ext)),
                      "Proboscis2": pose((0, 0, -85 * ext + 6 * math.sin(TAU * p * 3) * ext))})
            d.update(antennae(p, 3))
            return d

        m.animation("feed", 60, cycle(60, 12, feed))
    return m


# ======================================================================== Smiler
# "A long smile with multiple sharp teeth, and white glowing eyes"; its body, if it has one, "cannot be seen", though
# some say "non-human, alien-like bodies, with arms and legs bent in unnatural ways".

def sm_eye(ctx):
    fill(ctx, (250, 250, 246), 0.02, face_shade=False)
    if ctx.face == "west":
        rect(ctx, 0.0, 0.0, 1.0, 0.2, (222, 222, 216))


def sm_teeth(ctx):
    """Rows of narrow pointed teeth on black."""
    fill(ctx, (10, 6, 8), 0.0, face_shade=False)
    if ctx.face not in ("west", "east"):
        return
    px = ctx.img.load()
    teeth = max(6, ctx.w // 2)
    for i in range(teeth):
        x0 = ctx.x + int(i * ctx.w / teeth)
        width = max(1, int(ctx.w / teeth) - 0)
        for yy in range(ctx.h):
            # Upper teeth point down, lower teeth point up, meeting in a jagged line
            depth = yy / max(1, ctx.h - 1)
            for xx in range(width):
                centre = abs((xx + 0.5) / width - 0.5) * 2
                upper = depth < 0.55 and centre < 1 - depth / 0.55
                lower = depth > 0.45 and centre < (depth - 0.45) / 0.55
                if upper or lower:
                    px[min(x0 + xx, ctx.x + ctx.w - 1), ctx.y + yy] = (246, 242, 226, 255)


def sm_body(ctx):
    fill(ctx, (9, 8, 10), 0.3, face_shade=False)


def smiler():
    m = Model("smiler", atlas_width=48, seed=3)
    # A body you are not meant to see: almost black, thin, its joints bent wrong
    torso = m.part("Torso", (-1.25, 16, -2.5), (2.5, 12, 5), pivot=(0, 16, 0), rest=(0, 0, 10), paint=sm_body)
    head = m.part("Head", (-2.5, 28, -3.5), (5, 5, 7), pivot=(0, 28, 0), parent=torso, rest=(0, 0, -8), paint=sm_body)
    for z, side in ((0.6, "L"), (-1.6, "R")):
        m.part("Eye" + side, (-2.7, 31.2, z), (0.4, 1.2, 1.0), pivot=(-2.5, 31.8, z + 0.5), parent=head, rest=(0, 0, 0), paint=sm_eye, glow=255)
    # The grin: far wider than the face, curling up at the ends
    m.part("Grin", (-2.75, 28.6, -3.0), (0.4, 1.8, 6), pivot=(-2.55, 29.5, 0), parent=head, paint=sm_teeth, glow=235)
    m.part("GrinL", (-2.7, 29.6, 3.0), (0.4, 1.4, 1.6), pivot=(-2.5, 30, 3.0), parent=head, rest=(18, 0, 0), paint=sm_teeth, glow=235)
    m.part("GrinR", (-2.7, 29.6, -4.6), (0.4, 1.4, 1.6), pivot=(-2.5, 30, -3.0), parent=head, rest=(-18, 0, 0), paint=sm_teeth, glow=235)
    for z, side, sign in ((2.5, "L", 1), (-3.5, "R", -1)):
        arm = m.part("Arm" + side, (-0.5, 15, z), (1, 12, 1), pivot=(0, 27, z + 0.5), parent=torso, rest=(sign * -35, 0, -30), paint=sm_body)
        fore = m.part("Forearm" + side, (-0.5, 3, z), (1, 12, 1), pivot=(0, 15, z + 0.5), parent=arm, rest=(0, 0, 120), paint=sm_body)
        m.part("Claw" + side, (-0.5, -2, z), (1, 5, 1), pivot=(0, 3, z + 0.5), parent=fore, rest=(0, 0, -60), paint=sm_body)
        leg = m.part("Leg" + side, (-0.5, 4, z * 0.5), (1, 12, 1), pivot=(0, 16, z * 0.5 + 0.5), parent=torso, rest=(0, 0, -50), paint=sm_body)
        m.part("Shin" + side, (-0.5, -8, z * 0.5), (1, 12, 1), pivot=(0, 4, z * 0.5 + 0.5), parent=leg, rest=(0, 0, 95), paint=sm_body)

    m.animation("idle", 120, cycle(120, 8, lambda p: {
        "Head": pose((s(p, 10), s(p, 6, 0.3), 0)),
        "Grin": pose(s=(1, 1, 1 + 0.06 * max(0.0, math.sin(TAU * p)))),
        "Torso": pose((0, 0, s(p, 3)), (0, s(p, 0.6), 0)),
    }))
    m.animation("walk", 40, cycle(40, 8, lambda p: {
        "Torso": pose((s(p, 6), 0, 14), (0, s(p * 2, 0.4), 0)),
        "LegL": pose((0, 0, s(p, 25))), "LegR": pose((0, 0, -s(p, 25))),
        "ArmL": pose((0, 0, -s(p, 20))), "ArmR": pose((0, 0, s(p, 20))),
        "Head": pose((s(p, 8), 0, 0)),
    }))
    m.animation("attack", 18, {
        0: {"Head": pose(), "Torso": pose(), "ArmL": pose(), "ArmR": pose(), "Grin": pose(s=(1, 1, 1))},
        6: {"Head": pose((0, 0, -10)), "Torso": pose((0, 0, -12)), "ArmL": pose((0, 0, -60)), "ArmR": pose((0, 0, -60)), "Grin": pose(s=(1, 1.8, 1.1))},
        10: {"Head": pose((0, 0, 20)), "Torso": pose((0, 0, 25), (-3, 0, 0)), "ArmL": pose((0, 0, -10)), "ArmR": pose((0, 0, -10)), "Grin": pose(s=(1, 2.2, 1.1))},
        17: {"Head": pose(), "Torso": pose(), "ArmL": pose(), "ArmR": pose(), "Grin": pose(s=(1, 1, 1))},
    }, end="Stop")
    return m


# ======================================================================== Clump
# "Bundles of human limbs of varying lengths", with "eyes and ears emerging from the mass"; dormant, it buries itself,
# "leaving only their longest limb out into the open"; within eight feet "it will stretch out its longest limb ...
# bringing them towards its center to reveal a mouth filled with razor-sharp teeth". Design brief: human anatomy
# recombined with no front, back, top or bottom. A knot of overlapping flesh cores (no ribs, no pelvis) with ten limbs
# leaving it at conflicting angles: arms, legs, a forearm that ends in a foot, a thigh that ends in a hand, a child's
# arm; each a different desaturated skin, dry and cracked out along the limb, dark and wet where it enters the mass.
# A mouth in the top of the knot under four flaps of flesh, lined with human teeth repeated wrongly. One capture arm,
# 30 px, folded into the mass until it snaps out. Two wet eyes and an ear in the mass on the common look; a second
# texture has none. The mass is 14 px wide and 12 high (0.75 blocks); the limbs spread over two.

C_TONES = [(206, 176, 158), (190, 150, 128), (172, 150, 142), (150, 112, 92), (214, 190, 176), (130, 96, 82), (184, 160, 150)]
C_WET = (96, 44, 48)
C_BRUISE = (140, 108, 130)
C_GRIME = (104, 86, 70)
C_TEETH = (224, 212, 176)
C_MOUTH = (66, 18, 22)
C_NAIL = (190, 170, 150)
CV = {"blind": False}


def c_skin(ctx, tone, dry=True):
    """Old, deprived skin: cracked and grey toward the end of a limb, bruised, grimy where it meets the floor."""
    fill(ctx, tone, 0.04)
    blotch(ctx, shade(tone, 0.85), 2, 1.5, 4, 0.35)
    blotch(ctx, C_BRUISE, 1, 1.0, 3.0, 0.3)
    if ctx.rng.random() < 0.4:
        blotch(ctx, C_GRIME, 1, 1.5, 3.0, 0.3)
    if dry:
        for _ in range(2):
            u, v = ctx.rng.random(), ctx.rng.random()
            line(ctx, u, v, min(1, u + ctx.rng.uniform(0.1, 0.4)), min(1, v + ctx.rng.uniform(-0.1, 0.1)), shade(tone, 0.7), 0.35)   # cracks
    speckle(ctx, shade(tone, 0.9), 0.04)


def c_limb(ctx):
    """A limb segment: dry skin out along it, darkening to raw wet flesh at the root (the root is the +x end, u = 1)."""
    tone = C_TONES[ctx.part.tag.get("tone", 0)]
    c_skin(ctx, tone)
    if ctx.part.tag.get("root") and ctx.face in ("north", "south", "up", "down"):
        px = ctx.img.load()
        for xx in range(ctx.w):
            t = xx / max(1, ctx.w - 1)
            a = max(0.0, (t - 0.6) / 0.4) * 0.85
            if a > 0:
                for yy in range(ctx.h):
                    old = px[ctx.x + xx, ctx.y + yy]
                    px[ctx.x + xx, ctx.y + yy] = mix(old[:3], C_WET, a) + (255,)
    if ctx.part.tag.get("joint") and ctx.face in ("north", "south", "up", "down"):
        line(ctx, 0.0, 0.5, 0.12, 0.5, shade(tone, 0.6), 0.5)                 # the crease of a joint at the far end
        line(ctx, 0.04, 0.2, 0.04, 0.8, shade(tone, 0.7), 0.4)


def c_hand(ctx):
    tone = C_TONES[ctx.part.tag.get("tone", 0)]
    c_skin(ctx, tone, dry=False)
    if ctx.face == "up":
        for ty in range(0, ctx.h, 2):
            texel(ctx, 1, ty, shade(tone, 0.6), 0.6)                            # knuckles along the far edge
        if not ctx.part.tag.get("fingers"):
            for ty in range(1, ctx.h, 2):
                for tx in range(0, ctx.w // 2):
                    texel(ctx, tx, ty, shade(tone, 0.55), 0.7)                   # painted fingers
    if ctx.face == "down":
        fill(ctx, mix(tone, C_GRIME, 0.45), 0.05)                                 # a palm that has dragged over floors
        blotch(ctx, mix(tone, (230, 210, 200), 0.4), 1, 1.5, 3, 0.4)


def c_finger(ctx):
    tone = C_TONES[ctx.part.tag.get("tone", 0)]
    c_skin(ctx, tone, dry=False)
    if ctx.face in ("up", "north", "south"):
        texrow(ctx, ctx.h // 2, 0, -1, shade(tone, 0.65), 0.5)                   # a knuckle
    if ctx.face == "up":
        for tx in range(0, max(1, ctx.w // 4)):
            for ty in range(ctx.h):
                texel(ctx, tx, ty, C_NAIL)                                          # the nail at the tip (u = 0)
    if ctx.face == "west":
        fill(ctx, C_NAIL, 0.05)


def c_foot(ctx):
    tone = C_TONES[ctx.part.tag.get("tone", 0)]
    c_skin(ctx, tone, dry=False)
    if ctx.face in ("up", "west"):
        for ty in range(0, ctx.h, 2):
            texel(ctx, 0, ty, shade(tone, 0.6), 0.6)                               # toes
            texel(ctx, 0, ty, C_NAIL, 0.4)
    if ctx.face == "down":
        fill(ctx, mix(tone, C_GRIME, 0.5), 0.05)
    if ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.15, 0.6, 0.0, shade(tone, 0.8), 0.4)                       # the arch


def c_core(ctx):
    """The mass: compressed shoulders and hips, indistinct; raw and wet in the folds, dry on the crowns."""
    tone = C_TONES[ctx.part.tag.get("tone", 2)]
    fill(ctx, tone, 0.05)
    blotch(ctx, C_WET, 2, 2, 5, 0.5)
    blotch(ctx, shade(tone, 0.8), 2, 2, 5, 0.4)
    blotch(ctx, C_BRUISE, 1, 1.5, 4, 0.35)
    blotch(ctx, mix(tone, (240, 230, 225), 0.5), 1, 1.5, 3, 0.3)                    # a crown catching the light
    for _ in range(3):
        u, v = ctx.rng.random(), ctx.rng.random()
        line(ctx, u, v, min(1, u + ctx.rng.uniform(0.1, 0.35)), min(1, v + ctx.rng.uniform(-0.2, 0.2)), C_WET, 0.45)   # folds
    speckle(ctx, mix(tone, (255, 245, 240), 0.5), 0.012)                             # dew


def c_jaw(ctx):
    tone = C_TONES[2]
    c_skin(ctx, tone, dry=False)
    blotch(ctx, C_WET, 1, 1.5, 3, 0.5)
    if ctx.face == "down":
        fill(ctx, C_MOUTH, 0.1, face_shade=False)                                      # the inside of the flap


def c_cavity(ctx):
    fill(ctx, C_MOUTH, 0.12, face_shade=False)
    blotch(ctx, shade(C_MOUTH, 0.5), 2, 1.5, 3, 0.6)
    if ctx.face == "up":
        speckle(ctx, mix(C_MOUTH, (200, 120, 130), 0.5), 0.05)                          # wet


def c_tooth(ctx):
    fill(ctx, mix(C_TEETH, (200, 170, 100), ctx.rng.random() * 0.5), 0.05, face_shade=False)
    if ctx.face != "up":
        texrow(ctx, -1, 0, -1, (120, 90, 60), 0.6)                                      # brown at the gum


def c_eye(ctx):
    """A wet human eye in the mass: sclera with a dark iris, the lids raw. Painted over as flesh on the blind look."""
    if CV["blind"]:
        c_skin(ctx, C_TONES[2], dry=False)
        blotch(ctx, C_WET, 1, 1, 2, 0.4)
        return
    fill(ctx, (236, 230, 222), 0.03, face_shade=False)
    if ctx.face in ("west", "up", "north", "south", "east"):
        cx, cy = ctx.w // 2, ctx.h // 2
        for dx in (-1, 0):
            for dy in (-1, 0):
                texel(ctx, cx + dx, cy + dy, (46, 56, 62))
        texel(ctx, cx, cy, (14, 14, 16))
        texel(ctx, cx - 1, cy - 1, (255, 255, 255), 0.7)
        texrow(ctx, 0, 0, -1, (150, 60, 66), 0.6)                                        # raw lids
        texrow(ctx, -1, 0, -1, (150, 60, 66), 0.6)


def c_ear(ctx):
    if CV["blind"]:
        c_skin(ctx, C_TONES[0], dry=False)
        return
    tone = C_TONES[0]
    c_skin(ctx, tone, dry=False)
    if ctx.face in ("north", "south"):
        w, h = ctx.w, ctx.h
        for ty in range(h):                                                              # the whorl
            texel(ctx, 0, ty, shade(tone, 0.7), 0.6)
            texel(ctx, w - 1, ty, shade(tone, 0.8), 0.5)
        for tx in range(w):
            texel(ctx, tx, 0, shade(tone, 0.75), 0.5)
        texel(ctx, w // 2, h // 2, shade(tone, 0.45), 0.9)                               # the canal
        texel(ctx, w // 2, h // 2 + 1, shade(tone, 0.6), 0.7)


# Limbs: (yaw from the front, root (x, y, z) in the mass, kind, thickness, upper length, lower length, pitch of the
# upper segment, skin tone). Kinds: arm (ends in a hand), leg (a foot), armfoot (a forearm ending in a foot),
# thighhand (a thigh ending in a hand), child (a small arm).
LIMBS = [
    (28, (-4.5, 7.5, -2.0), "arm", 1.4, 6.0, 6.0, 15, 1),
    (75, (-3.0, 8.5, -5.0), "leg", 1.7, 6.5, 10.5, -15, 3),       # the knee raised above the hip
    (118, (0.5, 5.5, -5.5), "child", 0.9, 3.5, 4.2, 20, 4),
    (152, (4.0, 8.0, -4.0), "arm", 1.3, 6.5, 7.0, 10, 0),
    (186, (5.0, 9.0, 0.5), "leg", 1.8, 6.0, 10.5, -10, 5),
    (222, (4.0, 5.0, 4.5), "armfoot", 1.2, 5.5, 3.0, 25, 6),       # a forearm ending in a foot, low and short
    (262, (0.0, 9.5, 5.5), "thighhand", 1.7, 7.0, 10.5, -5, 3),    # a thigh ending in a hand
    (300, (-3.5, 8.0, 5.0), "arm", 1.5, 7.5, 7.0, 12, 2),
    (335, (-5.0, 5.0, 2.5), "leg", 1.5, 5.0, 5.0, 5, 1),
    (100, (2.0, 12.0, -2.5), "arm", 1.1, 5.0, 8.5, 50, 4),         # one that reaches over the top and back down
]


def clump(variant="common"):
    CV["blind"] = variant == "blind"
    m = Model("clump" if variant == "common" else f"clump-{variant}", atlas_width=64, seed=5)
    # The knot: overlapping cores, none of them a torso
    core = m.part("CoreA", (-4.5, 3.5, -5), (9, 7, 10), pivot=(0, 7, 0), paint=c_core, tag={"tone": 2})
    m.part("CoreB", (0.5, 8, -5), (6, 6, 6.5), pivot=(3, 11, -1.5), parent=core, rest=(10, 14, -8), paint=c_core, tag={"tone": 1})
    m.part("CoreC", (-7, 4, 1), (5.5, 5.5, 5.5), pivot=(-4, 6.5, 3.5), parent=core, rest=(-12, 22, 16), paint=c_core, tag={"tone": 6})
    m.part("CoreD", (1.5, 2.5, -7), (5.5, 4.5, 4.5), pivot=(4, 4.5, -4.5), parent=core, rest=(16, -10, 6), paint=c_core, tag={"tone": 0})
    m.part("CoreE", (-6, 9, -3.5), (5, 4, 4.5), pivot=(-3.5, 11, -1), parent=core, rest=(6, 0, 20), paint=c_core, tag={"tone": 3})
    m.part("CoreF", (-2, 9.5, 2), (5, 3.5, 4.5), pivot=(0.5, 11, 4), parent=core, rest=(-18, 0, -6), paint=c_core, tag={"tone": 5})
    # The mouth: a cavity in the top of the mass, in the hollow between the lumps, under four flaps of flesh hinged
    # at their outer edges
    m.part("Cavity", (-3.2, 10.0, -3.2), (6.4, 1.2, 6.4), pivot=(0, 10.5, 0), parent=core, paint=c_cavity)
    flaps = {"JawN": ((-3.4, 11.1, -3.4), (3.4, 0.9, 6.8), (-3.4, 11.2, 0)), "JawS": ((0.0, 11.1, -3.4), (3.4, 0.9, 6.8), (3.4, 11.2, 0)),
             "JawE": ((-3.4, 10.9, 0.4), (6.8, 0.8, 3.0), (0, 11.0, 3.4)), "JawW": ((-3.4, 10.9, -3.4), (6.8, 0.8, 3.0), (0, 11.0, -3.4))}
    for name, (frm, size, piv) in flaps.items():
        m.part(name, frm, size, pivot=piv, parent=core, paint=c_jaw)
    # Teeth: human teeth, too many, round the rim of the cavity, at odd angles
    rng = random.Random(55)
    for i in range(14):
        ang = i / 14 * TAU + rng.uniform(-0.1, 0.1)
        r = rng.uniform(2.1, 2.7)
        x, z = math.cos(ang) * r, math.sin(ang) * r
        w, h = rng.uniform(0.4, 0.7), rng.uniform(0.7, 1.3)
        m.part(f"Tooth{i}", (x - w / 2, 10.2, z - w / 2), (w, h, w), pivot=(x, 10.2, z), parent=core,
               rest=(math.sin(ang) * rng.uniform(10, 30), 0, -math.cos(ang) * rng.uniform(10, 30)), paint=c_tooth)
    # Eyes and an ear, wherever the mass happened to put them
    m.part("Eye0", (-4.8, 8.6, -2.6), (0.7, 1.1, 1.3), pivot=(-4.5, 9.1, -1.9), parent=core, rest=(0, -15, 10), paint=c_eye)
    m.part("Eye1", (2.6, 13.8, -2.2), (1.2, 0.7, 1.1), pivot=(3.2, 13.9, -1.7), parent=core, rest=(20, 0, -8), paint=c_eye)
    m.part("Ear0", (0.5, 5.4, 4.8), (1.3, 1.6, 0.5), pivot=(1.1, 6.2, 4.9), parent=core, rest=(0, 0, 25), paint=c_ear)

    def hand(name, x, y, z, parent, tone, size=(2.6, 0.9, 2.4), fingers=False, rest=(0, 0, 0)):
        h = m.part(name, (x - size[0], y - size[1] / 2, z - size[2] / 2), size, pivot=(x, y, z), parent=parent, rest=rest, paint=c_hand,
                   tag={"tone": tone, "fingers": fingers})
        if fingers:
            n = 4
            for i in range(n):
                fz = z - size[2] / 2 + 0.15 + i * (size[2] - 0.3) / n
                fw = (size[2] - 0.3) / n - 0.1
                m.part(f"{name}F{i}", (x - size[0] - 2.4, y - 0.3, fz), (2.4, 0.6, fw), pivot=(x - size[0], y, fz + fw / 2), parent=h,
                       rest=(0, (i - 1.5) * 6, 10), paint=c_finger, tag={"tone": tone})
        return h

    def foot(name, x, y, z, parent, tone, big=1.0, rest=(0, 0, 0)):
        return m.part(name, (x - 3.0 * big, y - 0.5, z - 0.9 * big), (3.2 * big, 1.1 * big, 1.8 * big), pivot=(x, y, z), parent=parent, rest=rest, paint=c_foot, tag={"tone": tone})

    # The limbs: built pointing -x from their root, pitched down, then turned to their yaw; the lower segment bends
    # further so the end lands on the floor; the hand or foot lies flat there.
    for i, (yaw, (rx, ry, rz), kind, thick, la, lb, pitch, tone) in enumerate(LIMBS):
        a = math.radians(pitch)
        ey = ry - la * math.sin(a)
        sb = max(-1.0, min(1.0, (ey - 0.55) / lb))
        b = math.degrees(math.asin(sb)) - pitch                         # the extra pitch of the lower segment
        tl = thick * (1.15 if kind in ("leg", "thighhand") else 1.0)
        up = m.part(f"Limb{i}A", (rx - la, ry - tl / 2, rz - tl / 2), (la + 1.0, tl, tl), pivot=(rx, ry, rz), parent=core,
                    rest=(0, yaw, pitch), paint=c_limb, tag={"tone": tone, "root": True})
        tb = thick * (0.85 if kind != "child" else 0.9)
        low = m.part(f"Limb{i}B", (rx - la - lb, ry - tb / 2, rz - tb / 2), (lb + 0.4, tb, tb), pivot=(rx - la, ry, rz), parent=up,
                     rest=(0, 0, b), paint=c_limb, tag={"tone": tone, "joint": True})
        ex = rx - la - lb
        flat = (0, 0, -(pitch + b))
        if kind in ("arm", "thighhand"):
            hand(f"Hand{i}", ex, ry, rz, low, tone, fingers=(i in (0, 7)), rest=flat)
        elif kind == "child":
            hand(f"Hand{i}", ex, ry, rz, low, tone, size=(1.8, 0.7, 1.7), rest=flat)
        else:
            foot(f"Foot{i}", ex, ry, rz, low, tone, big=1.1 if kind == "leg" else 0.9, rest=flat)

    # The capture arm: 9 + 9 + 2 + 4 + 3 of fingers = 27 px from the shoulder, folded into the front of the mass
    cu = m.part("CaptureUpper", (-14.5, 2.15, -0.85), (10.5, 1.7, 1.7), pivot=(-4, 3.0, 0), parent=core, rest=(0, -8, 8), paint=c_limb, tag={"tone": 2, "root": True})
    cf = m.part("CaptureFore", (-24, 2.25, -0.75), (9.5, 1.5, 1.5), pivot=(-14.5, 3.0, 0), parent=cu, rest=(0, 162, -4), paint=c_limb, tag={"tone": 2, "joint": True})
    cw = m.part("CaptureWrist", (-26, 2.35, -0.65), (2.2, 1.3, 1.3), pivot=(-24, 3.0, 0), parent=cf, rest=(0, 0, 0), paint=c_limb, tag={"tone": 2})
    hand("CaptureHand", -26, 2.9, 0, cw, 2, size=(3.2, 1.0, 2.8), fingers=True, rest=(0, 0, 0))

    limb_a = [f"Limb{i}A" for i in range(len(LIMBS))]
    limb_b = [f"Limb{i}B" for i in range(len(LIMBS))]
    jaws = ["JawN", "JawS", "JawE", "JawW"]
    cap_fingers = [f"CaptureHandF{i}" for i in range(4)]
    hand_fingers = [f"Hand0F{i}" for i in range(4)] + [f"Hand7F{i}" for i in range(4)]

    def jaw_open(k):
        """The four flaps hinged at their outer edges lift outward by k degrees."""
        return {"JawN": pose((0, 0, k)), "JawS": pose((0, 0, -k)), "JawE": pose((-k, 0, 0)), "JawW": pose((k, 0, 0))}

    # ---- Animations ----
    # A limb's +Z (in its own frame) presses its far end down; -Z lifts it. Its Y turns it about the root.
    def idle(p):
        d = {"CoreA": pose((s(p, 1.5), 0, s(p, 1.2, 0.3)), (0.2 * s(p, 1), 0, 0.2 * s(p, 1, 0.25)), s=(1, 1 + 0.015 * math.sin(TAU * p * 3), 1))}
        twitch = ramp(p, 0.22, 0.23, 0.25, 0.3)
        reach = ramp(p, 0.5, 0.62, 0.7, 0.85)
        grip = ramp(p, 0.78, 0.8, 0.9, 0.97)
        d["Limb4A"] = pose((0, 0, -8 * twitch))                                 # a leg twitches
        d["Limb1B"] = pose((0, 0, 6 * twitch))
        d["Limb7A"] = pose((0, 10 * reach, -12 * reach))                        # an arm slowly reaches out, and settles
        d["Limb7B"] = pose((0, 0, 14 * reach))
        d["Hand7"] = pose((0, 0, -10 * reach + 8 * grip))
        d["Limb0A"] = pose((0, -4 * grip, 0))
        d["Hand0"] = pose((0, 0, 10 * grip))                                    # another hand grips the floor
        for i, f in enumerate(hand_fingers):
            d[f] = pose((0, 0, 8 * math.sin(TAU * (p * 2 + i * 0.13)) + (18 * grip if f.startswith("Hand0") else 0)))
        for i, f in enumerate(cap_fingers):
            d[f] = pose((0, 0, 6 * math.sin(TAU * (p * 3 + i * 0.2))))
        d["Eye0"] = pose((0, 25 * ramp(p, 0.1, 0.12, 0.4, 0.44) - 10, 0))      # the eyes look about, not together
        d["Eye1"] = pose((0, -20 * ramp(p, 0.3, 0.33, 0.55, 0.6), 15 * ramp(p, 0.7, 0.72, 0.8, 0.85)))
        d.update(jaw_open(1.5 + 1.5 * math.sin(TAU * p * 3)))                   # it breathes through the mouth, just
        return d

    m.animation("idle", 120, cycle(120, 24, idle))

    # Stir: someone is near. Limbs lift and re-plant in turn, the mass rises, the flaps part.
    stir_names = ["CoreA"] + limb_a + limb_b + jaws + ["CaptureUpper", "Eye0", "Eye1"]
    stir = {0: full(stir_names, {})}
    for f, group in ((4, (1, 5, 8)), (9, (0, 3, 6)), (14, (2, 4, 7, 9))):
        d = {"CoreA": pose((0, 0, 0), (0, 0.8, 0)), "CaptureUpper": pose((0, 0, -4))}
        for i in group:
            d[f"Limb{i}A"] = pose((0, 8, -22))
            d[f"Limb{i}B"] = pose((0, 0, 12))
        d.update(jaw_open(8))
        d["Eye0"] = pose((0, -30, 0)); d["Eye1"] = pose((0, 25, 0))
        stir[f] = full(stir_names, d)
    stir[19] = full(stir_names, dict({"CoreA": pose((0, 0, 0), (0, 0.4, 0))}, **jaw_open(4)))
    stir[23] = full(stir_names, {})
    m.animation("stir", 24, stir, end="Stop")

    # Grab (24 frames, 0.8 s): a freeze, the limbs spread, the arm snaps out straight, the hand opens and clenches,
    # then the arm sweeps up and back to the mouth, which opens to meet it
    grab_names = ["CoreA", "CaptureUpper", "CaptureFore", "CaptureWrist", "CaptureHand"] + cap_fingers + limb_a + jaws
    spread = {n: pose((0, 0, -10)) for n in limb_a}
    m.animation("grab", 24, {
        0: full(grab_names, {}),
        2: full(grab_names, dict(spread, **{"CoreA": pose((0, 0, 0), (0.6, 0, 0))}, **{f: pose((0, 0, -20)) for f in cap_fingers})),
        5: full(grab_names, dict(spread, **{"CoreA": pose((0, 0, 0), (-0.8, 0.4, 0)), "CaptureUpper": pose((0, 8, -2)), "CaptureFore": pose((0, -162, 0)),
                                           "CaptureHand": pose((0, 0, -12))}, **{f: pose((0, 0, -35)) for f in cap_fingers})),
        7: full(grab_names, dict(spread, **{"CoreA": pose((0, 0, 0), (-0.8, 0.4, 0)), "CaptureUpper": pose((0, 8, -2)), "CaptureFore": pose((0, -162, 0)),
                                           "CaptureHand": pose((0, 0, 10))}, **{f: pose((0, 0, 45)) for f in cap_fingers})),
        12: full(grab_names, dict(spread, **{"CoreA": pose((0, 0, 0), (0, 1.0, 0)), "CaptureUpper": pose((0, 20, -50)), "CaptureFore": pose((0, -60, 0)),
                                            "CaptureWrist": pose((0, 0, 20)), "CaptureHand": pose((0, 0, 25))}, **{f: pose((0, 0, 50)) for f in cap_fingers}, **jaw_open(45))),
        17: full(grab_names, dict(spread, **{"CoreA": pose((0, 0, 0), (0, 1.0, 0)), "CaptureUpper": pose((0, 25, -70)), "CaptureFore": pose((0, -10, 0)),
                                            "CaptureWrist": pose((0, 0, 30)), "CaptureHand": pose((0, 0, 30))}, **{f: pose((0, 0, 50)) for f in cap_fingers}, **jaw_open(70))),
        21: full(grab_names, dict({"CoreA": pose((0, 0, 0), (0, 0.4, 0)), "CaptureUpper": pose((0, 10, -30)), "CaptureFore": pose((0, 0, 0))}, **jaw_open(25))),
        23: full(grab_names, {}),
    }, end="Stop")

    # Feeding: the limbs fold inward over the top and the flaps work under them; you mostly see hands and legs moving
    def feed(p):
        d = {n: pose((0, 0, 12 + s(p, 3, i * 0.1))) for i, n in enumerate(limb_a)}
        d.update({f"Limb{i}B": pose((0, 0, -10)) for i in range(len(LIMBS))})
        d.update({"CaptureUpper": pose((0, 20, -65 + s(p, 3))), "CaptureFore": pose((0, -20, 0)), "CaptureWrist": pose((0, 0, 30))})
        d.update(jaw_open(30 + 20 * abs(math.sin(TAU * p * 2))))
        d["CoreA"] = pose((0, 0, 0), (0, 0.5 + 0.3 * math.sin(TAU * p * 2), 0))
        return d

    m.animation("feed", 40, cycle(40, 8, feed))

    # Buried: the mass sunk into the floor (the floor hides it), a single arm sticking up out of it like something
    # dropped there, the hand hanging; a finger twitches now and then. Emerging, the floor gives the whole knot up.
    bury_names = ["CoreA", "CaptureUpper", "CaptureFore", "CaptureWrist", "CaptureHand", "Limb9A"] + cap_fingers
    buried = {"CoreA": pose((4, 0, 6), (0, -17, 0)), "Limb9A": pose((0, 0, 40)),
              "CaptureUpper": pose((0, 8, -83)), "CaptureFore": pose((0, -162, -8)), "CaptureWrist": pose((0, 0, 10)), "CaptureHand": pose((0, 0, 28)),
              "CaptureHandF0": pose((0, 0, 20)), "CaptureHandF1": pose((0, 0, 26)), "CaptureHandF2": pose((0, 0, 22)), "CaptureHandF3": pose((0, 0, 30))}
    twitch = dict(buried, CaptureHandF2=pose((0, 0, -6)))
    m.animation("dormant", 120, {0: full(bury_names, buried), 70: full(bury_names, buried), 72: full(bury_names, twitch),
                                 75: full(bury_names, buried), 110: full(bury_names, buried)})
    m.animation("emerge", 20, {0: full(bury_names, buried), 8: full(bury_names, dict(buried, CoreA=pose((-6, 0, -4), (0, -6, 0)))),
                               19: full(bury_names, {})}, end="Stop")

    # Crawl: improvised, not a gait. Three groups of limbs pull, push and catch out of step; the mass jerks forward.
    groups = ((0, 4, 7), (1, 3, 8, 9), (2, 5, 6))

    def crawl(p):
        d = {}
        for g, members in enumerate(groups):
            ph = p + g * 0.33
            for i in members:
                yaw_dir = -1 if (LIMBS[i][0] % 360) < 180 else 1
                d[f"Limb{i}A"] = pose((0, yaw_dir * 18 * math.sin(TAU * ph), -14 * max(0.0, math.sin(TAU * (ph + 0.25)))))
                d[f"Limb{i}B"] = pose((0, 0, 10 * max(0.0, math.sin(TAU * (ph + 0.25)))))
        jerk = max(0.0, math.sin(TAU * p * 3))
        d["CoreA"] = pose((s(p, 3), s(p * 3, 4), s(p * 2, 3)), (-0.6 * jerk, 0.6 * jerk, 0))
        d["CaptureUpper"] = pose((0, s(p, 6), -6 * jerk))
        return d

    m.animation("crawl", 24, cycle(24, 12, crawl))

    # Death: coordination goes. A supporting limb fails and the mass tips; arms reach out; one tries to push upright
    # and weakens; the mass sinks; a last finger moves; stillness.
    die_names = ["CoreA", "CaptureUpper", "CaptureFore"] + limb_a + limb_b + jaws + hand_fingers + cap_fingers
    m.animation("die", 40, {
        0: full(die_names, {}),
        6: full(die_names, dict({"CoreA": pose((10, 0, 4), (0, -0.8, 0)), "Limb1A": pose((0, 0, 30)), "Limb1B": pose((0, 0, -20)),
                                 "Limb4A": pose((0, 0, 24))}, **jaw_open(12))),
        14: full(die_names, dict({"CoreA": pose((16, 6, 8), (0, -1.6, 0)), "Limb1A": pose((0, 0, 32)), "Limb1B": pose((0, 0, -24)), "Limb4A": pose((0, 0, 26)),
                                  "Limb0A": pose((0, 0, -26)), "Limb7A": pose((0, -10, -30)), "Limb3A": pose((0, 0, -20)),
                                  "Limb6A": pose((0, 0, -28)), "Limb6B": pose((0, 0, 30)), "CaptureUpper": pose((0, 10, -8))}, **jaw_open(30))),
        24: full(die_names, dict({"CoreA": pose((20, 8, 10), (0, -2.4, 0), s=(1.06, 0.8, 1.06)), "Limb1A": pose((0, 0, 32)), "Limb1B": pose((0, 0, -24)), "Limb4A": pose((0, 0, 28)),
                                  "Limb0A": pose((0, 0, -10)), "Limb7A": pose((0, -10, -12)), "Limb3A": pose((0, 0, -6)),
                                  "Limb6A": pose((0, 0, -4)), "Limb6B": pose((0, 0, 8)), "CaptureUpper": pose((0, 10, 2)), "CaptureFore": pose((0, -30, 0))},
                                 **jaw_open(20), **{f: pose((0, 0, 20)) for f in hand_fingers + cap_fingers})),
        33: full(die_names, dict({"CoreA": pose((22, 8, 12), (0, -2.8, 0), s=(1.08, 0.72, 1.08)), "Limb1A": pose((0, 0, 32)), "Limb1B": pose((0, 0, -24)), "Limb4A": pose((0, 0, 28)),
                                  "Limb0A": pose((0, 0, -6)), "Limb7A": pose((0, -10, -6)), "Limb3A": pose((0, 0, -2)), "Limb6A": pose((0, 0, 2)), "Limb6B": pose((0, 0, 2)),
                                  "CaptureUpper": pose((0, 10, 4)), "CaptureFore": pose((0, -30, 0))},
                                 **jaw_open(14), **{f: pose((0, 0, 24 if f != "CaptureHandF2" else -10)) for f in hand_fingers + cap_fingers})),
        39: full(die_names, dict({"CoreA": pose((22, 8, 12), (0, -2.8, 0), s=(1.08, 0.72, 1.08)), "Limb1A": pose((0, 0, 32)), "Limb1B": pose((0, 0, -24)), "Limb4A": pose((0, 0, 28)),
                                  "Limb0A": pose((0, 0, -6)), "Limb7A": pose((0, -10, -6)), "Limb3A": pose((0, 0, -2)), "Limb6A": pose((0, 0, 2)), "Limb6B": pose((0, 0, 2)),
                                  "CaptureUpper": pose((0, 10, 4)), "CaptureFore": pose((0, -30, 0))},
                                 **jaw_open(14), **{f: pose((0, 0, 24)) for f in hand_fingers + cap_fingers})),
    }, end="Hold", stopped="Stop")
    return m


def clump_variant_textures():
    """The blind look (no eyes, no ear) painted on the common atlas layout, a texture alternate picked per spawn."""
    m = clump("blind")
    width, height = m._pack()
    img = m._paint(width, height)
    img.save(os.path.join(ASSETS, "textures", "entity", "clump-blind.png"))
    print(f"wrote clump-blind texture {width}x{height}")
    CV["blind"] = False


# ======================================================================== The Mangled
# "A spider-like creature", "a massive black pillar, reaching up far out of sight", made of "faces, merging together
# into a singular mass"; it lifts people up on tendrils; the noises it makes are human speech. Design brief: not a
# giant spider but an impossible piece of the landscape that moves. Six irregular pillar limbs, bark-like and
# tapering, hold a core of merged human faces well above the rooftops, a pillar rising further from it; capture
# tendrils of nine segments hang beneath, tapering to a few grasping strands. Most faces sleep, eyes closed and
# slack; a few are open, one screams. Near-black leathery fibre with burnt brown-red undertones; the faces pale, so
# they come out of the dark. 8 blocks to the top of the pillar, the core at 5 to 6.5; the legs stand within a
# 4-block footprint so it can walk a street. Unique: there is The Mangled, not a Mangled.

MG_SKIN = (30, 27, 28)
MG_FIBRE_DARK = (16, 14, 16)
MG_FIBRE_LIGHT = (62, 50, 46)
MG_BURN = (74, 40, 34)
MG_MAROON = (84, 36, 44)
MG_FACE = (164, 148, 140)
MG_FACE_DARK = (118, 102, 98)
MG_IRIS = (58, 62, 70)
MG_TEETH = (214, 204, 184)
MG_MOUTH = (44, 14, 18)


def mg_bark(ctx):
    """Charcoal, leathery, fibrous: dark and light fibres run along the limb; cracks across it; burnt undertones."""
    fill(ctx, MG_SKIN, 0.12)
    if ctx.face in ("north", "south", "east", "west"):
        vlines(ctx, MG_FIBRE_DARK, 3, start=0, alpha=0.6, jitter=1)
        vlines(ctx, MG_FIBRE_LIGHT, 4, start=2, alpha=0.35, jitter=1)
        hlines(ctx, MG_FIBRE_DARK, 7, start=ctx.rng.randint(0, 6), alpha=0.35)       # ridges and cracks
    blotch(ctx, MG_BURN, 2, 2, 6, 0.3)
    blotch(ctx, MG_MAROON, 1, 2, 4, 0.2)
    speckle(ctx, MG_FIBRE_LIGHT, 0.02)


def mg_core(ctx):
    """The mass between the faces: bark, with more faces half-sunk into it, painted, eyes shut."""
    mg_bark(ctx)
    if ctx.face in ("up", "down"):
        return
    for _ in range(max(1, ctx.w * ctx.h // 220)):
        u, v = ctx.rng.uniform(0.0, 0.8), ctx.rng.uniform(0.0, 0.8)
        w, h = ctx.rng.uniform(0.14, 0.22), ctx.rng.uniform(0.14, 0.22)
        sunk = ctx.rng.uniform(0.35, 0.7)
        c = mix(MG_FACE_DARK, MG_SKIN, sunk)
        rect(ctx, u, v, u + w, v + h, c)
        rect(ctx, u + w * 0.15, v + h * 0.3, u + w * 0.4, v + h * 0.38, mix(MG_FIBRE_DARK, c, 0.3))     # shut eyes
        rect(ctx, u + w * 0.6, v + h * 0.3, u + w * 0.85, v + h * 0.38, mix(MG_FIBRE_DARK, c, 0.3))
        rect(ctx, u + w * 0.35, v + h * 0.7, u + w * 0.65, v + h * 0.76, mix(MG_MOUTH, c, 0.4))        # a slack mouth


def mg_face(ctx):
    """One face of the mass, a human one: pale skin sinking into the black at its edges, eyes shut or open, a mouth
    closed, slack, or open in a scream. Which, from the part's tags."""
    t = ctx.part.tag
    pale = t.get("pale", 0.8)
    base = mix(MG_FACE_DARK, MG_FACE, pale)
    if ctx.face != "west":
        fill(ctx, mix(base, MG_SKIN, 0.55), 0.06)
        blotch(ctx, MG_SKIN, 1, 2, 4, 0.5)
        return
    fill(ctx, base, 0.04)
    px = ctx.img.load()
    w, h = ctx.w, ctx.h
    for yy in range(h):                                                        # sinking into the mass at the edges
        for xx in range(w):
            e = min(xx, w - 1 - xx, yy, h - 1 - yy)
            if e < 3:
                old = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = mix(old[:3], MG_SKIN, (3 - e) / 3 * 0.85) + (255,)
    blotch(ctx, shade(base, 0.85), 1, 2, 4, 0.3)
    ey = int(h * 0.42)
    for cx in (int(w * 0.32), int(w * 0.68)):
        if t.get("eyes") == "open":
            for dx in (-1, 0, 1):
                texel(ctx, cx + dx, ey, (236, 232, 228))
                texel(ctx, cx + dx, ey - 1, (236, 232, 228), 0.7)
            texel(ctx, cx + t.get("look", 0), ey, MG_IRIS)
            texel(ctx, cx + t.get("look", 0), ey, (8, 8, 10), 0.8)
            texrow(ctx, ey - 2, cx - 1, cx + 1, shade(base, 0.6), 0.6)              # the lid's crease
        else:
            texrow(ctx, ey, cx - 1, cx + 1, shade(base, 0.55), 0.8)                   # shut: a dark line
            texrow(ctx, ey - 1, cx - 1, cx + 1, shade(base, 0.85), 0.5)
    texel(ctx, w // 2, int(h * 0.56), shade(base, 0.75), 0.6)                         # the nose's shadow
    texel(ctx, w // 2 - 1, int(h * 0.56), shade(base, 0.85), 0.4)
    my = int(h * 0.74)
    mouth = t.get("mouth", "closed")
    if mouth == "scream":
        for yy in range(my - 2, my + 3):
            texrow(ctx, yy, w // 2 - 3, w // 2 + 2, MG_MOUTH)
        for tx in range(w // 2 - 3, w // 2 + 3, 2):
            texel(ctx, tx, my - 2, MG_TEETH)
            texel(ctx, tx + 1, my + 2, MG_TEETH, 0.8)
    elif mouth == "open":
        texrow(ctx, my, w // 2 - 2, w // 2 + 1, MG_MOUTH)
        texrow(ctx, my + 1, w // 2 - 2, w // 2 + 1, MG_MOUTH, 0.8)
        texel(ctx, w // 2 - 1, my, MG_TEETH, 0.6)
    else:
        texrow(ctx, my, w // 2 - 2, w // 2 + 1, shade(base, 0.5), 0.8)


def mg_tendril(ctx):
    fill(ctx, (26, 22, 24), 0.1)
    if ctx.face in ("north", "south", "east", "west"):
        vlines(ctx, MG_FIBRE_DARK, 2, alpha=0.5, jitter=1)                           # sinew along it
        vlines(ctx, (54, 40, 40), 3, start=1, alpha=0.3, jitter=1)
    blotch(ctx, MG_MAROON, 1, 1.5, 3, 0.25)


def mg_pad(ctx):
    mg_bark(ctx)
    if ctx.face == "down":
        fill(ctx, (40, 34, 28), 0.08)


# Faces of the mass: (position on the core's surface as (x, y, z) of the face's centre, yaw to face outward, pitch,
# roll, size (w, h), eyes, mouth, pale)
FACES = [
    ((-9.2, 92, -2), 0, 0, 6, (7, 8), "closed", "closed", 0.85),
    ((-8.8, 82, 4), 20, -10, -8, (6, 7), "open", "closed", 0.9),
    ((-6, 98, 7.5), 55, 15, 0, (6, 7), "closed", "slack", 0.7),
    ((2, 100, 9.4), 90, 20, 12, (7, 8), "closed", "open", 0.75),
    ((7, 88, 7.5), 130, -5, -15, (6, 6.5), "open", "scream", 0.95),
    ((9.4, 80, -1), 180, -20, 6, (7, 8), "closed", "closed", 0.6),
    ((6.5, 96, -7), 230, 10, 0, (6, 7), "closed", "closed", 0.8),
    ((0, 86, -9.2), 270, 0, -20, (7, 8), "open", "open", 0.85),
    ((-6, 90, -7.5), 315, 25, 8, (5.5, 6.5), "closed", "closed", 0.65),
    ((-3, 104.5, -3), 20, 70, 0, (6, 6), "closed", "slack", 0.7),      # one looking up out of the top
    ((2, 74.2, 2), 200, -70, 0, (6, 6), "open", "scream", 0.9),       # one looking down out of the underside
]

# Support limbs: (yaw, upper length, upper pitch (negative is upward), thickness, splay of the shin from vertical)
LEGS = [(12, 22, -14, 5.0, 7), (70, 26, -8, 4.2, 5), (118, 20, -18, 5.5, 9), (192, 24, -10, 4.6, 6), (250, 28, -6, 4.0, 4), (305, 21, -16, 5.2, 8)]
TENDRILS = [((-5, 74, -4), 9, 2.4, True), ((5.5, 74, -3.5), 9, 2.2, True), ((0, 74, 5.5), 9, 2.3, True),
            ((-6.5, 76, 5), 5, 1.6, False), ((7, 76, 4.5), 5, 1.4, False), ((-1, 74, -7), 6, 1.5, False)]


def mangled():
    m = Model("mangled", atlas_width=128, seed=63)
    # The core: a knot of dark masses from 74 to 106, the pillar above it to 130
    core = m.part("Core", (-9, 76, -9), (18, 24, 18), pivot=(0, 88, 0), paint=mg_core)
    m.part("CoreLobeA", (-11, 80, -4), (8, 16, 12), pivot=(-7, 88, 2), parent=core, rest=(6, 10, -8), paint=mg_core)
    m.part("CoreLobeB", (2, 84, -12), (10, 14, 9), pivot=(7, 90, -7), parent=core, rest=(-8, -12, 10), paint=mg_core)
    m.part("CoreLobeC", (-5, 72, -6), (12, 7, 12), pivot=(1, 75, 0), parent=core, rest=(4, 20, 6), paint=mg_core)
    m.part("CoreLobeD", (-4, 98, -5), (11, 9, 10), pivot=(1.5, 102, 0), parent=core, rest=(-10, 30, 8), paint=mg_core)
    pillar = m.part("Pillar", (-5, 104, -5), (10, 16, 10), pivot=(0, 104, 0), parent=core, rest=(5, 0, 7), paint=mg_core)
    m.part("PillarTop", (-3.5, 119, -3.5), (7, 12, 7), pivot=(0, 119, 0), parent=pillar, rest=(-7, 20, -5), paint=mg_bark)
    # The faces, set into the surface, each turned its own way
    for i, ((x, y, z), yaw, pitch, roll, (fw, fh), eyes, mouth, pale) in enumerate(FACES):
        m.part(f"Face{i}", (x - 1.6, y - fh / 2, z - fw / 2), (2.2, fh, fw), pivot=(x, y, z), parent=core, rest=(roll, yaw, pitch), paint=mg_face,
               tag={"eyes": eyes, "mouth": mouth, "pale": pale, "look": (-1, 0, 1)[i % 3]})
    # Six pillar limbs: up and out from under the core, then down in two tapering segments to a pad on the ground
    for i, (yaw, la, pitch, thick, splay) in enumerate(LEGS):
        root = (-7, 78, 0)
        up = m.part(f"Leg{i}", (root[0] - la, root[1] - thick / 2, root[2] - thick / 2), (la + 4, thick, thick), pivot=root, parent=core,
                    rest=(0, yaw, pitch), paint=mg_bark)
        knee_y = root[1] - la * math.sin(math.radians(pitch))
        kx = root[0] - la
        t1 = thick * 0.95
        l1 = 40.0
        a1 = 90 - splay - pitch                       # the shin's own pitch: nearly vertical, splayed a little out
        shin1 = m.part(f"Shin{i}", (kx - l1, root[1] - t1 / 2, root[2] - t1 / 2), (l1 + 1.5, t1, t1), pivot=(kx, root[1], root[2]), parent=up,
                       rest=(0, 0, a1), paint=mg_bark)
        y1 = knee_y - l1 * math.sin(math.radians(90 - splay))
        b = 2 * splay + 2                             # the lower shin bends back in past vertical
        l2 = max(4.0, (y1 - 1.0) / math.sin(math.radians(90 + splay + 2)))
        t2 = thick * 0.7
        shin2 = m.part(f"Shank{i}", (kx - l1 - l2, root[1] - t2 / 2, root[2] - t2 / 2), (l2 + 1.0, t2, t2), pivot=(kx - l1, root[1], root[2]), parent=shin1,
                       rest=(0, 0, b), paint=mg_bark)
        m.part(f"Pad{i}", (kx - l1 - l2 - 3.5, root[1] - 1.0, root[2] - 3.2), (6.0, 2.6, 6.4), pivot=(kx - l1 - l2, root[1], root[2]), parent=shin2,
               rest=(0, 0, -(92 + splay)), paint=mg_pad)      # level on the ground
    # Tendrils from the underside: three long capture tendrils ending in grasping strands, three shorter ones that trail
    for i, ((x, y, z), n, thick, capture) in enumerate(TENDRILS):
        prev, top = core, y
        for j in range(n):
            t = thick * (1 - 0.7 * j / max(1, n - 1))
            seg = 8.0 if capture else 7.0
            prev = m.part(f"Tendril{i}_{j}", (x - t / 2, top - seg, z - t / 2), (t, seg, t), pivot=(x, top, z), parent=prev,
                          rest=(((-1) ** j) * (4 + 2 * (j % 3)) * (1 if i % 2 else -1), 0, ((-1) ** (j // 2)) * (3 + j)), paint=mg_tendril)
            top -= seg
        if capture:
            for k in range(3):
                ang = k * TAU / 3
                m.part(f"Strand{i}_{k}", (x - 0.3, top - 4, z - 0.3), (0.6, 4, 0.6), pivot=(x, top, z), parent=prev,
                       rest=(math.cos(ang) * 22, 0, math.sin(ang) * 22), paint=mg_tendril)

    face_names = [f"Face{i}" for i in range(len(FACES))]
    leg_names = [f"Leg{i}" for i in range(6)]
    shin_names = [f"Shin{i}" for i in range(6)]
    tendril_names = [f"Tendril{i}_{j}" for i, (_, n, _, _) in enumerate(TENDRILS) for j in range(n)]
    strand_names = [f"Strand{i}_{k}" for i in range(3) for k in range(3)]

    def tendrils(p, amp, lift=0.0, which=None):
        d = {}
        for i, (_, n, _, capture) in enumerate(TENDRILS):
            if which is not None and i not in which:
                continue
            for j in range(n):
                d[f"Tendril{i}_{j}"] = pose((s(p, amp * 0.6, i * 0.17 + j * 0.08), 0, s(p, amp, i * 0.23 + j * 0.07) + (lift if j == 0 else lift * 0.2)))
        return d

    def faces_emerge(active, k):
        """Faces come forward out of the mass (k px along their own outward axis) and tilt a little."""
        return {f"Face{i}": pose((0, 0, 0), (-k, 0, 0)) if i in active else pose() for i in range(len(FACES))}

    # ---- Animations ----
    # Legs are built pointing -x and turned to their yaw: their -Z lifts, +Z presses down; Y swings them about the root.
    def step(p, amp, lift_deg, bob, sink=0.0):
        """One limb at a time: it lifts, hangs, swings forward and comes down; the others slide back through the stance."""
        d = {}
        for i in range(6):
            order = (0, 3, 1, 4, 2, 5).index(i)          # never two neighbours at once
            q = (p - order / 6) % 1.0
            lift = ramp(q, 0.0, 0.05, 0.11, 0.16)
            yaw = -amp + 2 * amp * (q / 0.16) if q < 0.16 else amp - 2 * amp * (q - 0.16) / 0.84
            side = 1 if (LEGS[i][0] % 360) < 180 else -1
            d[f"Leg{i}"] = pose((0, side * yaw, -lift_deg * lift))
            d[f"Shin{i}"] = pose((0, 0, lift_deg * 0.7 * lift))
            d[f"Shank{i}"] = pose((0, 0, lift_deg * 0.4 * lift))
        d["Core"] = pose((s(p * 3, 1.2), s(p, 2), s(p * 3, 1.0, 0.3)), (0, -sink + 0.8 * math.sin(TAU * p * 6), 0))
        d["Pillar"] = pose((s(p * 3, 2, 0.1), 0, s(p * 3, 1.5, 0.4)))
        d["PillarTop"] = pose((s(p * 3, 3, 0.2), s(p, 6), s(p * 3, 2, 0.5)))
        d.update(tendrils(p, 10))
        return d

    m.animation("walk", 90, cycle(90, 18, lambda p: step(p, 16, 20, 0.8)))
    m.animation("run", 48, cycle(48, 12, lambda p: step(p, 26, 24, 1.2, sink=6)))

    def idle(p):
        d = {"Core": pose((s(p, 1.5), s(p, 3), s(p, 1.2, 0.3)), s=(1 + 0.012 * math.sin(TAU * p * 4), 1 + 0.012 * math.sin(TAU * p * 4), 1 + 0.012 * math.sin(TAU * p * 4))),
             "Pillar": pose((s(p, 3, 0.1), s(p, 5, 0.2), s(p, 2))), "PillarTop": pose((s(p, 5, 0.25), s(p, 10, 0.1), s(p, 4, 0.4)))}
        d.update(tendrils(p, 12))
        active = set()
        for i, (a, b_, c, e) in enumerate(((0.1, 0.16, 0.3, 0.38), (0.45, 0.5, 0.62, 0.7), (0.72, 0.76, 0.85, 0.92))):
            k = ramp(p, a, b_, c, e)
            face = (4, 1, 7)[i]
            d[f"Face{face}"] = pose((0, 0, 4 * k), (-1.8 * k, 0, 0))
        for i in range(len(FACES)):
            d.setdefault(f"Face{i}", pose())
        return d

    m.animation("idle", 150, cycle(150, 25, idle))

    # Searching: the capture tendrils rise and probe forward, the core tilts, faces come out of the mass in turn
    search_names = ["Core", "Pillar", "PillarTop"] + face_names + tendril_names + strand_names
    def search(p):
        d = {"Core": pose((0, s(p, 8), 6 * ramp(p, 0.05, 0.2, 0.8, 0.95))), "Pillar": pose((s(p, 6), s(p, 14, 0.2), -4)), "PillarTop": pose((0, s(p, 25, 0.3), 0))}
        r = ramp(p, 0.05, 0.25, 0.75, 0.95)
        for i, (_, n, _, capture) in enumerate(TENDRILS):
            for j in range(n):
                if capture:
                    d[f"Tendril{i}_{j}"] = pose((s(p, 10, i * 0.2 + j * 0.1) * (1 - r * 0.5), 0, (-70 * r if j == 0 else -8 * r) + s(p * 2, 6, j * 0.1)))
                else:
                    d[f"Tendril{i}_{j}"] = pose((s(p, 8, i * 0.2 + j * 0.1), 0, s(p, 8, j * 0.1)))
        for i in range(3):
            for k in range(3):
                d[f"Strand{i}_{k}"] = pose((0, 0, 0), s=(1, 1 + 0.3 * r * abs(math.sin(TAU * (p * 3 + k * 0.3))), 1))
        for i in range(len(FACES)):
            k = ramp(p, 0.1 + i * 0.05, 0.16 + i * 0.05, 0.7, 0.9)
            d[f"Face{i}"] = pose((0, 0, 0), (-1.5 * k, 0, 0))
        return d

    m.animation("despair", 80, {f: full(search_names, search(f / 80)) for f in range(0, 80, 5)} | {79: full(search_names, search(0.99))}, end="Stop")

    # The take (27 frames, 0.9 s; the entity's damageAtMs 450 is frame 13): the front tendril draws up coiled, drops
    # on what is below, the strands close, and it lifts away upward. The body hardly moves.
    atk_names = ["Core"] + [f"Tendril0_{j}" for j in range(9)] + [f"Strand0_{k}" for k in range(3)] + face_names

    def coil(k_up, k_down, close, lift):
        d = {}
        for j in range(9):
            # The root swings forward (-Z) to coil up and to strike; the segments curl back under for the drop
            d[f"Tendril0_{j}"] = pose((0, 0, (-16 * k_up + 14 * k_down - 10 * lift) if j else (-40 * k_up - 70 * k_down - 30 * lift)))
        for k in range(3):
            ang = k * TAU / 3
            d[f"Strand0_{k}"] = pose((-math.cos(ang) * 40 * close, 0, -math.sin(ang) * 40 * close))
        return d

    m.animation("attack", 27, {
        0: full(atk_names, {}),
        5: full(atk_names, dict(coil(1.0, 0.0, 0.0, 0.0), **{"Core": pose((0, 0, -3), (0, 1, 0))}, **faces_emerge({4, 7, 10}, 1.5))),
        9: full(atk_names, dict(coil(0.7, 0.0, -0.5, 0.0), **{"Core": pose((0, 0, -3), (0, 1, 0))}, **faces_emerge({4, 7, 10}, 1.5))),
        13: full(atk_names, dict(coil(0.0, 1.0, 0.0, 0.0), **{"Core": pose((0, 0, 6), (0, -2, 0))}, **faces_emerge({4, 7, 10, 1}, 2.0))),
        15: full(atk_names, dict(coil(0.0, 1.0, 1.0, 0.0), **{"Core": pose((0, 0, 6), (0, -2, 0))}, **faces_emerge({4, 7, 10, 1}, 2.0))),
        21: full(atk_names, dict(coil(0.6, 0.0, 1.0, 1.0), **{"Core": pose((0, 0, -4), (0, 4, 0))}, **faces_emerge(set(range(11)), 1.5))),
        26: full(atk_names, {}),
    }, end="Stop")

    hurt_names = ["Core", "Pillar", "PillarTop"] + face_names
    m.animation("hurt", 14, {
        0: full(hurt_names, {}),
        4: full(hurt_names, dict({"Core": pose((5, 0, -4)), "Pillar": pose((8, 0, -8)), "PillarTop": pose((10, 0, -6))}, **faces_emerge(set(range(11)), 2.5))),
        9: full(hurt_names, dict({"Core": pose((-2, 0, 2)), "Pillar": pose((-4, 0, 3)), "PillarTop": pose((-5, 0, 2))}, **faces_emerge(set(range(11)), 1.2))),
        13: full(hurt_names, {}),
    }, end="Stop")

    # Death: the limbs buckle one after another and the whole height comes down; the pillar topples; the tendrils go slack
    die_names = ["Core", "Pillar", "PillarTop"] + leg_names + shin_names + [f"Shank{i}" for i in range(6)] + tendril_names + face_names
    def collapse(k, topple):
        d = {"Core": pose((8 * k, 0, 12 * k), (0, -62 * k, 0)), "Pillar": pose((10 * topple, 0, 50 * topple)), "PillarTop": pose((0, 0, 30 * topple))}
        for i in range(6):
            kk = min(1.0, max(0.0, k * 1.6 - i * 0.12))
            d[f"Leg{i}"] = pose((0, 0, 30 * kk)); d[f"Shin{i}"] = pose((0, 0, 40 * kk)); d[f"Shank{i}"] = pose((0, 0, -50 * kk))
        d.update({n: pose((0, 0, 0)) for n in tendril_names})
        d.update(faces_emerge(set(range(11)), 2.0 * (1 - k)))
        return d

    m.animation("die", 60, {0: full(die_names, {}), 15: full(die_names, collapse(0.3, 0.0)), 32: full(die_names, collapse(0.7, 0.4)),
                            48: full(die_names, collapse(1.0, 0.9)), 59: full(die_names, collapse(1.0, 1.0))}, end="Hold", stopped="Stop")
    return m


# ======================================================================== The Thing
# Nothing in the lore says what it looks like: only that it rules the Midnight Zone and the Abyss, that it killed off
# everything else in the sea, and that its eyes, made for perpetual dark, cannot bear bright light. Here: a vast black
# eel-like fish with a maw full of needles and small, milky, light-sick eyes.

T_SKIN = (16, 18, 22)


def t_skin(ctx):
    fill(ctx, T_SKIN, 0.25)
    speckle(ctx, (36, 40, 46), 0.08, 2)
    if ctx.face == "down":
        fill(ctx, (40, 42, 46), 0.15)


def t_head(ctx):
    t_skin(ctx)
    if ctx.face in ("north", "south"):
        rect(ctx, 0.12, 0.25, 0.26, 0.42, (190, 196, 190))   # small milky eyes
        rect(ctx, 0.16, 0.29, 0.22, 0.38, (220, 226, 214))


def t_maw(ctx):
    fill(ctx, (40, 12, 16), 0.1)
    if ctx.face in ("up", "west", "north", "south"):
        vlines(ctx, (210, 206, 190), 2, alpha=0.95)


def t_fin(ctx):
    fill(ctx, (28, 30, 36), 0.25, face_shade=False)
    vlines(ctx, (10, 12, 14), 2, alpha=0.6)


def thething():
    m = Model("thething", atlas_width=128, seed=7)
    head = m.part("Head", (-10, 2, -4.5), (12, 8, 9), pivot=(2, 6, 0), paint=t_head)
    m.part("Jaw", (-11, 0, -4), (11, 3, 8), pivot=(0, 2.5, 0), parent=head, paint=t_maw)
    prev, x = head, 2
    for i, (length, h, w) in enumerate(((14, 9, 9.5), (14, 8.5, 9), (14, 7.5, 8), (13, 6.5, 7), (12, 5, 5.5), (11, 3.5, 4))):
        prev = m.part(f"Seg{i}", (x, 6 - h / 2, -w / 2), (length, h, w), pivot=(x, 6, 0), parent=prev, paint=t_skin)
        m.part(f"Fin{i}", (x + 1, 6 + h / 2, -0.25), (length - 2, 3.5 - i * 0.3, 0.5), pivot=(x + 1, 6 + h / 2, 0), parent=prev, paint=t_fin, faces=("north", "south"))
        x += length
    m.part("Tail", (x, 0, -0.3), (9, 12, 0.6), pivot=(x, 6, 0), parent=prev, paint=t_fin, faces=("north", "south"))

    def swim(p, amp, jaw):
        d = {f"Seg{i}": pose((0, s(p, amp * (0.4 + i * 0.25), -i * 0.11), 0)) for i in range(6)}
        d["Head"] = pose((0, s(p, amp * 0.25, 0.1), s(p * 2, 1.5)))
        d["Jaw"] = pose((0, 0, -jaw))
        return d

    # Centred on the entity's position (its middle, not its snout)
    m.shift(dx=-38)
    m.animation("swim", 60, cycle(60, 8, lambda p: swim(p, 10, 4)))
    m.animation("attack", 20, {
        0: dict(swim(0, 0, 0)),
        8: dict(swim(0, 0, 0), Jaw=pose((0, 0, -45)), Head=pose((0, 0, 10))),
        14: dict(swim(0, 0, 0), Jaw=pose((0, 0, -5)), Head=pose((0, 0, -6))),
        19: dict(swim(0, 0, 0)),
    }, end="Stop")
    return m


# ======================================================================== The Animations (Level 94, Motion)
# Entity 32: the stop-motion characters of the 1930s-50s (puppets, claymation, plastic and wooden figures) that hunt
# anything that does not look animated, chanting "All glory to the King!". Four of them: a lump of plasticine, an
# artist's wooden mannequin, a paper cut-out, and the castle's tin Robo-Men. They are made to look made: a little too
# saturated, grainy, thumbprinted, painted or crayoned by hand.
#
# Every one of their animations is stop-motion: a pose is held (two identical keyframes two frames apart) and then
# jumps to the next in a single frame, ten poses a second, never easing. A little "boil" (each pose a degree or two off,
# as a puppet moved by hand never lands exactly where it was) keeps the held poses from looking frozen.


def stopmo(poses, hold=2):
    """Stop-motion keyframes: each pose held for `hold` frames, then a one-frame jump to the next. -> (keys, frames)"""
    keys, step = {}, hold + 1
    for i, p in enumerate(poses):
        keys[i * step] = p
        keys[i * step + hold] = p
    return keys, len(poses) * step


def held(m, code, poses, hold=2, end="Repeat", stopped="EaseOut"):
    keys, frames = stopmo(poses, hold)
    m.animation(code, frames, keys, end=end, stopped=stopped)
    return frames


def boil(poses, names, amount, seed):
    """Each pose's parts nudged a little at random: the shimmer of a figure re-posed by hand every frame."""
    rng = random.Random(seed)
    out = []
    for p in poses:
        q = dict(p)
        for n in names:
            b = q.get(n, pose())
            r = b["rot"]
            q[n] = dict(b, rot=(r[0] + rng.uniform(-amount, amount), r[1] + rng.uniform(-amount, amount), r[2] + rng.uniform(-amount, amount)))
        out.append(q)
    return out


def toppled(theta, height, depth=0.0):
    """The offset (in the root part's own rotated frame) that keeps a figure toppling about Z by theta (positive:
    forwards) with its feet where they were, its hips pivoting at `height`, lifted by `depth` as it comes to lie."""
    t = math.radians(theta)
    dx = -height * math.sin(t)
    dy = -height * (1 - math.cos(t)) + depth * abs(math.sin(t))
    c, sn = math.cos(-t), math.sin(-t)
    return (dx * c - dy * sn, dx * sn + dy * c, 0.0)


def grain(ctx, amount=7):
    """Per-texel noise over a face: the grain of a hand-made thing filmed on old stock."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            r, g, b, a = px[ctx.x + xx, ctx.y + yy]
            if a:
                n = ctx.rng.uniform(-amount, amount)
                px[ctx.x + xx, ctx.y + yy] = clamp((r + n, g + n, b + n)) + (a,)


# ---------------------------------------------------------------- Clay Animation
# A lumpy, faceless figure of grey-brown plasticine, slightly hunched, worked over so often that threads of other
# colours are kneaded into it. Thumbprints all over, two deep ones where the eyes should be. Stubby fingers.

CL_BASE = (166, 136, 110)
CL_GREY = (148, 136, 128)
CL_WARM = (174, 124, 82)
CL_LIGHT = (204, 176, 146)
CL_DARK = (88, 66, 52)
CL_STREAKS = ((60, 98, 182), (204, 60, 46), (76, 160, 70), (232, 190, 60))


def thumbprint(ctx, cx, cy, r, depth=0.16):
    """A thumbprint pressed into the clay: a shallow dent, shadowed on its upper side and lit on its lower lip, with the
    whorl of the ridges in it (cx, cy, r in texels of the face)."""
    px = ctx.img.load()
    turn = ctx.rng.uniform(0, TAU)
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            dx, dy = xx + 0.5 - cx, (yy + 0.5 - cy) * 1.25
            d = math.hypot(dx, dy)
            if d >= r:
                continue
            k = 1 - d / r
            f = 1 - depth * (0.4 + k) * (1.0 if dy < 0 else 0.45)
            if d > r * 0.68 and dy > 0.3:
                f = 1 + depth * 0.7
            if (d * 1.1 + (math.atan2(dy, dx) + turn) / math.pi) % 2.0 < 0.8:
                f *= 1 - depth * 0.6 * (0.4 + k)
            old = px[ctx.x + xx, ctx.y + yy]
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(c * f for c in old[:3])) + (old[3],)


def cl_streak(ctx, colour, alpha):
    """A thread of another colour of plasticine, kneaded in and never quite mixed."""
    u, v, a = ctx.rng.random(), ctx.rng.random(), ctx.rng.uniform(0, TAU)
    for _ in range(4):
        a += ctx.rng.uniform(-0.9, 0.9)
        u2, v2 = u + 0.28 * math.cos(a), v + 0.28 * math.sin(a)
        line(ctx, u, v, u2, v2, colour, alpha)
        u, v = u2, v2


def cl_clay(ctx, base=CL_BASE, prints=True):
    fill(ctx, base, 0.05)
    blotch(ctx, CL_GREY, 2, 1.5, 4.5, 0.4)
    blotch(ctx, CL_WARM, 2, 1.5, 4.0, 0.35)
    if ctx.w >= 6 and ctx.h >= 6 and ctx.rng.random() < 0.35:
        cl_streak(ctx, ctx.rng.choice(CL_STREAKS), 0.32)
    for _ in range(max(1, ctx.w * ctx.h // 50)):                       # smoothing strokes of a finger
        u, v = ctx.rng.random(), ctx.rng.random()
        line(ctx, u, v, u + ctx.rng.uniform(-0.35, 0.35), v + ctx.rng.uniform(-0.12, 0.12), CL_LIGHT, 0.18)
    if prints and ctx.w >= 6 and ctx.h >= 6:
        for _ in range(1 + ctx.w * ctx.h // 160):
            thumbprint(ctx, ctx.rng.uniform(1.5, ctx.w - 1.5), ctx.rng.uniform(1.5, ctx.h - 1.5), ctx.rng.uniform(2.4, 3.8), 0.11)
    speckle(ctx, CL_DARK, 0.008)                                        # grit and lint picked up off the set
    grain(ctx, 7)


def cl_head(ctx):
    """Where a face would be: smoothed over, a brow pinched up, a ridge where a nose might go, and two thumbs pressed in
    deep for eyes."""
    cl_clay(ctx, mix(CL_BASE, CL_LIGHT, 0.12), prints=ctx.face != "west")
    if ctx.face == "west":
        w, h = ctx.w, ctx.h
        line(ctx, 0.05, 0.28, 0.95, 0.26, CL_LIGHT, 0.5)
        line(ctx, 0.05, 0.34, 0.95, 0.33, CL_DARK, 0.3)
        thumbprint(ctx, w * 0.28, h * 0.47, 2.7, 0.34)
        thumbprint(ctx, w * 0.73, h * 0.5, 2.5, 0.34)
        line(ctx, 0.5, 0.40, 0.52, 0.66, CL_LIGHT, 0.45)
        line(ctx, 0.25, 0.84, 0.75, 0.80, CL_DARK, 0.35)                # a smear, not a mouth


def cl_finger(ctx):
    cl_clay(ctx, mix(CL_BASE, CL_WARM, 0.2), prints=False)
    if ctx.face not in ("up", "down"):
        texrow(ctx, -1, 0, -1, CL_DARK, 0.4)


def animation_clay():
    m = Model("animation-clay", atlas_width=64, seed=94)
    pelvis = m.part("Pelvis", (-2.5, 10.5, -3.25), (5, 3.5, 6.5), pivot=(0, 12, 0), paint=cl_clay)
    body = m.part("Body", (-3.25, 13.5, -4), (6.5, 7.5, 8), pivot=(0, 13.5, 0), parent=pelvis, rest=(0, 0, 14), paint=cl_clay)
    m.part("Hump", (2, 15.5, -3), (2.5, 4.5, 5.5), pivot=(3, 17, 0), parent=body, rest=(4, 0, -8), paint=cl_clay)
    m.part("Belly", (-4, 13.75, -2.75), (1.5, 3, 5), pivot=(-3.5, 15, 0), parent=body, rest=(0, 0, -6), paint=cl_clay)
    m.part("ShoulderL", (-2, 19.25, 2.25), (4, 2, 2.5), pivot=(0, 20, 3.5), parent=body, rest=(10, 0, 0), paint=cl_clay)
    head = m.part("Head", (-3, 20.5, -2.75), (5, 5, 5.5), pivot=(0, 20.5, 0), parent=body, rest=(4, 0, -10), paint=cl_head)
    m.part("HeadLump", (-2.25, 25.25, -2.25), (3.75, 1.25, 4.25), pivot=(0, 25.5, 0), parent=head, rest=(0, 0, 6), paint=cl_clay)
    m.part("Jowl", (-3.3, 19.9, -2.1), (2, 1.5, 4.2), pivot=(-2.5, 20.5, 0), parent=head, paint=cl_clay)
    # Arms hang forward of the hunched shoulders, the stubby hands at the knee
    arm = m.part("ArmL", (-1.5, 13, 4), (3, 7.5, 3), pivot=(0, 19.5, 5.5), parent=body, rest=(-6, 0, -24), paint=cl_clay)
    fore = m.part("ForearmL", (-1.25, 6.5, 4.25), (2.5, 7, 2.5), pivot=(0, 13, 5.5), parent=arm, rest=(0, 0, -12), paint=cl_clay)
    hand = m.part("HandL", (-1.6, 4, 3.9), (3.2, 2.75, 3.2), pivot=(0, 6.5, 5.5), parent=fore, paint=cl_clay)
    for i in range(3):
        m.part(f"Finger{i}L", (-1.45 + i * 1.0, 2.5, 5.0), (0.95, 1.7, 1.05), pivot=(-1.0 + i * 1.0, 4.1, 5.5), parent=hand,
               rest=(0, 0, -6 + 6 * i), paint=cl_finger)
    m.part("ThumbL", (-2.1, 3.4, 4.7), (0.95, 1.5, 0.95), pivot=(-1.6, 4.8, 5.1), parent=hand, rest=(0, 0, -28), paint=cl_finger)
    thigh = m.part("ThighL", (-1.75, 5.5, 0.4), (3.5, 6.5, 3.5), pivot=(0, 11.5, 2.15), parent=pelvis, rest=(0, 0, -6), paint=cl_clay)
    shin = m.part("ShinL", (-1.5, 1.2, 0.65), (3, 5, 3), pivot=(0, 6.2, 2.15), parent=thigh, rest=(0, 0, 10), paint=cl_clay)
    m.part("FootL", (-3.6, 0, 0.4), (5, 1.6, 3.6), pivot=(0, 1.6, 2.15), parent=shin, rest=(0, 6, -4), paint=cl_clay)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    m.mirror("ShoulderL", "ShoulderR")
    # Lumpy, not symmetrical: the right arm hangs lower and further forward, the right shoulder is a smaller lump
    m.by_name["ArmR"].rest = (8, 0, -30)
    m.by_name["ShoulderR"].rest = (-16, 0, 8)
    m.by_name["FootR"].rest = (0, -10, -4)

    # ---- Animations (all stop-motion) ----
    def gait(p, amp, lean, arm, reach, sway):
        a = amp * math.sin(TAU * p)
        kl, kr = 26 * max(0.0, math.cos(TAU * p)), 26 * max(0.0, -math.cos(TAU * p))
        return {
            "ThighL": pose((0, 0, -a)), "ThighR": pose((0, 0, a)),
            "ShinL": pose((0, 0, kl)), "ShinR": pose((0, 0, kr)),
            "FootL": pose((0, 0, (a - kl) * 0.8)), "FootR": pose((0, 0, -(a + kr) * 0.8)),
            "Pelvis": pose((s(p, sway), s(p, 6), 0), (0, -0.7 * abs(math.sin(TAU * p)), 0)),
            "Body": pose((-s(p, sway * 0.7), -s(p, 5), lean)),
            "Hump": pose((0, 0, s(p * 2, 3))),
            "Head": pose((s(p, 4, 0.25), s(p, 8, 0.1), -lean * 0.6)),
            "ArmL": pose((0, 0, s(p, arm) - reach)), "ArmR": pose((0, 0, -s(p, arm) - reach)),
            "ForearmL": pose((0, 0, -reach * 0.4)), "ForearmR": pose((0, 0, -reach * 0.4)),
        }

    jitter = ("Body", "Head", "ArmL", "ArmR", "Hump")
    held(m, "walk", boil([gait(i / 8, 16, 2, 14, 0, 4) for i in range(8)], jitter, 1.5, 9401))
    held(m, "run", boil([gait(i / 6, 26, 12, 10, 40, 6) for i in range(6)], jitter, 2.0, 9402))

    def idle(i):
        b = math.sin(TAU * i / 12)
        look = (0, 0, 0, 0, 16, 16, 16, 16, 0, -8, -8, 0)[i]          # the blank face turns, holds, turns back
        return {
            "Body": pose((0, 0, b * 1.5), s=(1 + 0.02 * b, 1 - 0.03 * b, 1 + 0.02 * b)),  # it breathes, squashing
            "Head": pose((look * 0.3, look, -b * 2)),
            "ArmL": pose((0, 0, b * 2)), "ArmR": pose((0, 0, -b * 1.5)),
            "Finger0L": pose((0, 0, 8 * b)), "Finger2R": pose((0, 0, -8 * b)),
        }

    held(m, "idle", boil([idle(i) for i in range(12)], jitter, 1.2, 9403))

    # Smother (24 frames, 0.8 s; damageAtMs 450 lands on pose 4, frames 12-14): it rears up, stretching tall, arms
    # wide, then falls forward over the victim, wrapping round and squashing down onto it.
    held(m, "smother", [
        {},
        {"ArmL": pose((0, 0, -60)), "ArmR": pose((0, 0, -55)), "ForearmL": pose((0, 0, -20)), "ForearmR": pose((0, 0, -20)), "Body": pose((0, 0, -6))},
        {"ArmL": pose((-30, 0, -115)), "ArmR": pose((30, 0, -110)), "ForearmL": pose((0, 0, -25)), "ForearmR": pose((0, 0, -25)),
         "Body": pose((0, 0, -12), s=(0.92, 1.14, 0.92)), "Head": pose((0, 0, -14))},
        {"ArmL": pose((-10, 0, -88)), "ArmR": pose((10, 0, -84)), "ForearmL": pose((0, 0, -34)), "ForearmR": pose((0, 0, -34)),
         "Body": pose((0, 0, 28), s=(1.0, 0.94, 1.06)), "Head": pose((0, 0, 10)), "Pelvis": pose(o=(-1.5, 0, 0))},
        {"ArmL": pose((14, 0, -72)), "ArmR": pose((-14, 0, -70)), "ForearmL": pose((0, 0, -58)), "ForearmR": pose((0, 0, -58)),
         "Body": pose((0, 0, 38), s=(1.1, 0.86, 1.16)), "Head": pose((0, 0, 20)), "Pelvis": pose(o=(-2, -0.5, 0)),
         "ThighL": pose((0, 0, -16)), "ThighR": pose((0, 0, -10)), "ShinL": pose((0, 0, 20)), "ShinR": pose((0, 0, 14))},
        {"ArmL": pose((18, 0, -66)), "ArmR": pose((-18, 0, -64)), "ForearmL": pose((0, 0, -64)), "ForearmR": pose((0, 0, -64)),
         "Body": pose((0, 0, 36), s=(1.16, 0.82, 1.2)), "Head": pose((0, 0, 22)), "Pelvis": pose(o=(-2, -0.7, 0)),
         "ThighL": pose((0, 0, -18)), "ThighR": pose((0, 0, -12)), "ShinL": pose((0, 0, 24)), "ShinR": pose((0, 0, 18))},
        {"ArmL": pose((0, 0, -45)), "ArmR": pose((0, 0, -40)), "ForearmL": pose((0, 0, -15)), "ForearmR": pose((0, 0, -15)),
         "Body": pose((0, 0, 12), s=(1.04, 0.96, 1.04)), "Pelvis": pose(o=(-0.8, 0, 0))},
        {},
    ], end="Stop")

    held(m, "hurt", [
        {},
        {"Body": pose((6, 0, -14), s=(1.12, 0.88, 1.12)), "Head": pose((10, 0, -12)), "ArmL": pose((-15, 0, 10)), "ArmR": pose((12, 0, 8))},
        {"Body": pose((3, 0, -6), s=(0.96, 1.05, 0.96)), "Head": pose((4, 0, -4))},
        {},
    ], end="Stop")

    # Death: the knees go, it sits down into itself and slumps into a heap of clay
    # (Only the head and the lumps squash: a stretch on the body would stretch the arms hanging from it too)
    def heap(drop, thigh, shin, foot, lean, squash, head, arms):
        lump = (1 + squash * 0.6, 1 - squash, 1 + squash * 0.6)
        return {
            "Pelvis": pose((drop * 0.5, 0, 0), (0, -drop, 0)),
            "ThighL": pose((0, 0, -thigh)), "ThighR": pose((0, 0, -thigh * 0.92)),
            "ShinL": pose((0, 0, shin)), "ShinR": pose((0, 0, shin * 0.92)),
            "FootL": pose((0, 0, -foot)), "FootR": pose((0, 0, -foot)),
            "Body": pose((0, 0, lean)),
            "Hump": pose((0, 0, 0), s=lump), "Belly": pose((0, 0, 0), s=lump),
            "Head": pose((head * 0.4, 0, head), s=lump),
            # the arms flop forward and lie out in front of it, reaching
            "ArmL": pose((-6, 0, 10 - lean - arms)), "ArmR": pose((8, 0, 4 - lean - arms)),
            "ForearmL": pose((0, 0, -arms * 0.1)), "ForearmR": pose((0, 0, arms * 0.1)),
        }

    held(m, "die", [
        {},
        heap(1.5, 30, 55, 25, 16, 0.0, 8, 0),
        heap(4.5, 62, 108, 45, 30, 0.1, 14, 16),
        heap(7.0, 84, 140, 55, 48, 0.28, 22, 55),
        heap(8.0, 88, 148, 58, 60, 0.42, 30, 72),
        heap(8.3, 88, 150, 58, 66, 0.5, 34, 78),
    ], end="Hold", stopped="Stop")
    return m


# ---------------------------------------------------------------- Wooden Animation
# A 1930s jointed artist's mannequin: an egg of a head on a peg neck, a chest wider at the shoulders, ball joints at
# every hinge, honey-coloured beech with the grain showing through the varnish. Someone has painted a face on it with a
# finger: two black dots and a fixed red grin, and rosy cheeks. The rod that held it up on its stand has snapped off
# and still sticks out of its back.

WD_BASE = (218, 164, 96)
WD_LIGHT = (240, 200, 138)
WD_GRAIN = (168, 110, 56)
WD_DARK = (112, 70, 36)
WD_JOINT = (184, 124, 66)
PAINT_BLACK = (20, 16, 18)
PAINT_RED = (206, 30, 28)
PAINT_PINK = (236, 116, 104)
PAINT_WHITE = (246, 238, 220)


def wd_wood(ctx, base=WD_BASE):
    fill(ctx, base, 0.04)
    px = ctx.img.load()
    if ctx.face in ("up", "down"):                                      # end grain: rings
        cx, cy = ctx.w * ctx.rng.uniform(0.3, 0.7), ctx.h * ctx.rng.uniform(0.3, 0.7)
        for yy in range(ctx.h):
            for xx in range(ctx.w):
                if math.hypot(xx + 0.5 - cx, yy + 0.5 - cy) % 2.2 < 0.7:
                    old = px[ctx.x + xx, ctx.y + yy]
                    px[ctx.x + xx, ctx.y + yy] = mix(old[:3], WD_GRAIN, 0.5) + (255,)
    else:                                                               # long grain, wavering
        for _ in range(max(2, ctx.w // 2)):
            x0, ph, amp = ctx.rng.uniform(0, ctx.w), ctx.rng.uniform(0, TAU), ctx.rng.uniform(0.3, 1.0)
            for yy in range(ctx.h):
                xx = int(x0 + amp * math.sin(yy / 3.0 + ph))
                if 0 <= xx < ctx.w:
                    old = px[ctx.x + xx, ctx.y + yy]
                    px[ctx.x + xx, ctx.y + yy] = mix(old[:3], WD_GRAIN, 0.4) + (255,)
        if ctx.face == "west":
            line(ctx, 0.3, 0.05, 0.35, 0.95, WD_LIGHT, 0.3)            # the varnish catching the light
        if ctx.w * ctx.h > 40 and ctx.rng.random() < 0.35:               # a knot
            kx, ky = ctx.rng.uniform(1, ctx.w - 1), ctx.rng.uniform(1, ctx.h - 1)
            texel(ctx, int(kx), int(ky), WD_DARK, 0.8)
            texel(ctx, int(kx) + 1, int(ky), WD_GRAIN, 0.6)
    speckle(ctx, WD_DARK, 0.015)
    grain(ctx, 6)


def wd_joint(ctx):
    """A ball joint: darker, oiled, a ring round its middle."""
    fill(ctx, WD_JOINT, 0.05)
    if ctx.face not in ("up", "down"):
        texrow(ctx, ctx.h // 2, 0, -1, WD_DARK, 0.55)
        texel(ctx, 0, 0, WD_LIGHT, 0.6)
        texel(ctx, 1, 0, WD_LIGHT, 0.4)
    grain(ctx, 6)


def wd_head(ctx):
    wd_wood(ctx, mix(WD_BASE, WD_LIGHT, 0.2))
    if ctx.face == "west":                                               # 8 x 9 texels
        for tx, ty in ((1, 3), (2, 3), (1, 4), (2, 4)):                  # the eyes: two dabs of black, not level
            texel(ctx, tx, ty, PAINT_BLACK)
        for tx, ty in ((5, 3), (6, 3), (5, 2)):
            texel(ctx, tx, ty, PAINT_BLACK)
        texel(ctx, 0, 5, PAINT_PINK, 0.8)                                # rosy cheeks
        texel(ctx, 7, 5, PAINT_PINK, 0.8)
        texel(ctx, 0, 6, PAINT_BLACK)                                    # the grin, ear to ear, fixed
        texel(ctx, 7, 5, PAINT_BLACK)
        texrow(ctx, 6, 1, 6, PAINT_RED)
        texel(ctx, 7, 6, PAINT_BLACK)
        texrow(ctx, 7, 1, 6, PAINT_BLACK)
        texel(ctx, 2, 6, PAINT_WHITE)                                    # a tooth or two dabbed in white
        texel(ctx, 4, 6, PAINT_WHITE)
        texel(ctx, 6, 7, PAINT_RED, 0.6)                                 # where the brush slipped


def wd_rod(ctx):
    fill(ctx, (70, 72, 78), 0.1)
    speckle(ctx, (150, 84, 50), 0.3)
    grain(ctx, 6)


def animation_wooden():
    m = Model("animation-wooden", atlas_width=48, seed=95)
    pelvis = m.part("Pelvis", (-1.5, 13.5, -2.5), (3, 2.75, 5), pivot=(0, 15, 0), paint=wd_wood)
    m.part("Rod", (1.4, 14.35, -0.35), (2.6, 0.7, 0.7), pivot=(1.5, 14.7, 0), parent=pelvis, rest=(0, 8, -12), paint=wd_rod)
    m.part("WaistBall", (-1.1, 15.9, -1.1), (2.2, 1.6, 2.2), parent=pelvis, paint=wd_joint)
    chest = m.part("Chest", (-1.75, 19.5, -3.25), (3.5, 3.75, 6.5), pivot=(0, 17, 0), parent=pelvis, paint=wd_wood)
    m.part("Ribs", (-1.5, 17.1, -2.25), (3, 2.6, 4.5), pivot=(0, 17, 0), parent=chest, paint=wd_wood)
    neck = m.part("Neck", (-0.6, 23, -0.6), (1.2, 1.6, 1.2), pivot=(0, 23, 0), parent=chest, paint=wd_wood)
    head = m.part("Head", (-1.9, 24.3, -2), (3.8, 4.5, 4), pivot=(0, 24.5, 0), parent=neck, paint=wd_head)
    m.part("HeadTop", (-1.5, 28.7, -1.6), (3, 0.6, 3.2), parent=head, paint=wd_wood)
    m.part("Chin", (-1.6, 23.9, -1.5), (3, 0.5, 3), parent=head, paint=wd_wood)
    m.part("ShoulderL", (-1.1, 21.2, 3.0), (2.2, 2.2, 2.2), parent=chest, paint=wd_joint)
    arm = m.part("ArmL", (-0.8, 17.2, 3.3), (1.6, 5, 1.6), pivot=(0, 22.2, 4.1), parent=chest, rest=(-5, 0, 0), paint=wd_wood)
    m.part("ElbowL", (-0.95, 16.3, 3.15), (1.9, 1.5, 1.9), parent=arm, paint=wd_joint)
    fore = m.part("ForearmL", (-0.7, 12.4, 3.4), (1.4, 4.4, 1.4), pivot=(0, 17, 4.1), parent=arm, rest=(0, 0, -8), paint=wd_wood)
    m.part("HandL", (-0.9, 10.2, 3.5), (1.8, 2.4, 1.2), pivot=(0, 12.6, 4.1), parent=fore, paint=wd_wood)
    thigh = m.part("ThighL", (-0.95, 8.6, 0.55), (1.9, 5.8, 1.9), pivot=(0, 14.2, 1.5), parent=pelvis, paint=wd_wood)
    m.part("KneeL", (-1.05, 7.7, 0.45), (2.1, 1.6, 2.1), parent=thigh, paint=wd_joint)
    shin = m.part("ShinL", (-0.8, 1.6, 0.7), (1.6, 6.6, 1.6), pivot=(0, 8.4, 1.5), parent=thigh, paint=wd_wood)
    m.part("AnkleL", (-0.75, 1.1, 0.75), (1.5, 1.0, 1.5), parent=shin, paint=wd_joint)
    m.part("FootL", (-2.8, 0, 0.6), (3.8, 1.3, 1.8), pivot=(0, 1.3, 1.5), parent=shin, paint=wd_wood)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    m.mirror("ShoulderL", "ShoulderR")
    m.by_name["Head"].rest = (6, 0, 0)                                   # the head cocked, just a little

    # ---- Animations (all stop-motion) ----
    def gait(p, amp, lean, arm, knee):
        a = amp * math.sin(TAU * p)
        kl, kr = knee * max(0.0, math.cos(TAU * p)), knee * max(0.0, -math.cos(TAU * p))
        return {
            "ThighL": pose((0, 0, -a)), "ThighR": pose((0, 0, a)),
            "ShinL": pose((0, 0, kl)), "ShinR": pose((0, 0, kr)),
            "FootL": pose((0, 0, (a - kl) * 0.9)), "FootR": pose((0, 0, -(a + kr) * 0.9)),
            "Pelvis": pose((0, s(p, 8), lean * 0.3), (0, -0.5 * abs(math.sin(TAU * p)), 0)),
            "Chest": pose((0, -s(p, 12), lean * 0.7)),
            "Head": pose((0, s(p, 6), -lean)),                           # the grin stays fixed on its target
            "ArmL": pose((0, 0, s(p, arm))), "ArmR": pose((0, 0, -s(p, arm))),   # elbows locked: stiff, marching
            "ForearmL": pose((0, 0, -4)), "ForearmR": pose((0, 0, -4)),
        }

    jitter = ("Chest", "Head", "ArmL", "ArmR")
    held(m, "walk", boil([gait(i / 8, 18, 2, 24, 22) for i in range(8)], jitter, 1.2, 9501))
    held(m, "run", boil([gait(i / 6, 32, 16, 48, 50) for i in range(6)], jitter, 2.0, 9502))

    def idle(i):
        # Stock still, then the head snaps to one side, holds, snaps to the other, cocks; a finger-tap of a hand
        head = ((0, 0, 0), (0, 0, 0), (0, 0, 0), (14, 20, 0), (14, 20, 0), (14, 20, 0), (0, 0, 0), (-10, -24, 4),
                (-10, -24, 4), (-10, -24, 4), (20, 0, 0), (20, 0, 0))[i]
        tap = (0, 0, 0, 0, 0, 0, 0, 0, -10, 0, -10, 0)[i]
        return {"Head": pose(head), "ForearmR": pose((0, 0, tap)), "Chest": pose((0, head[1] * 0.15, 0))}

    held(m, "idle", boil([idle(i) for i in range(12)], ("Chest", "ArmL", "ArmR"), 0.8, 9503))

    # Club (24 frames, 0.8 s; damageAtMs 420 lands on pose 4, frames 12-14): both arms swung up overhead, fists
    # together, and brought down like a mallet, the whole body folding into the blow.
    held(m, "club", [
        {},
        {"Chest": pose((0, 0, -6)), "ArmL": pose((-8, 0, -90)), "ArmR": pose((8, 0, -90)), "ForearmL": pose((0, 0, -30)), "ForearmR": pose((0, 0, -30))},
        {"Chest": pose((0, 0, -14)), "Head": pose((0, 0, 8)), "ArmL": pose((-14, 0, -168)), "ArmR": pose((14, 0, -168)),
         "ForearmL": pose((0, 0, -22)), "ForearmR": pose((0, 0, -22)), "Pelvis": pose((0, 0, -4))},
        {"Chest": pose((0, 0, 10)), "Head": pose((0, 0, -6)), "ArmL": pose((-12, 0, -110)), "ArmR": pose((12, 0, -110)),
         "ForearmL": pose((0, 0, 0)), "ForearmR": pose((0, 0, 0))},
        {"Chest": pose((0, 0, 30)), "Head": pose((0, 0, -18)), "ArmL": pose((-10, 0, -54)), "ArmR": pose((10, 0, -54)),
         "Pelvis": pose((0, 0, 4), (-0.8, -0.8, 0)), "ThighL": pose((0, 0, -18)), "ThighR": pose((0, 0, -8)),
         "ShinL": pose((0, 0, 24)), "ShinR": pose((0, 0, 12)), "FootL": pose((0, 0, -10)), "FootR": pose((0, 0, -6))},
        {"Chest": pose((0, 0, 26)), "Head": pose((0, 0, -14)), "ArmL": pose((-10, 0, -46)), "ArmR": pose((10, 0, -46)),
         "Pelvis": pose((0, 0, 4), (-0.8, -0.8, 0)), "ThighL": pose((0, 0, -18)), "ThighR": pose((0, 0, -8)),
         "ShinL": pose((0, 0, 24)), "ShinR": pose((0, 0, 12)), "FootL": pose((0, 0, -10)), "FootR": pose((0, 0, -6))},
        {"Chest": pose((0, 0, 10)), "ArmL": pose((-4, 0, -20)), "ArmR": pose((4, 0, -20))},
        {},
    ], end="Stop")

    held(m, "hurt", [
        {},
        {"Chest": pose((10, 14, -16)), "Head": pose((18, 10, -12)), "ArmL": pose((-20, 0, -10)), "ArmR": pose((14, 0, 6))},
        {"Chest": pose((4, 6, -6)), "Head": pose((8, 4, -4))},
        {},
    ], end="Stop")

    # Death: the strings are cut. It drops straight down onto its knees, folds over, the head lolling on its peg
    def drop(k, fold, head, arms, sit):
        return {
            "Pelvis": pose((0, 0, 0), (0, -sit, 0)),
            "ThighL": pose((0, 0, -k)), "ThighR": pose((0, 0, -k * 0.9)),
            "ShinL": pose((0, 0, k * 1.6)), "ShinR": pose((0, 0, k * 1.5)),
            "FootL": pose((0, 0, -k * 0.6)), "FootR": pose((0, 0, -k * 0.6)),
            "Chest": pose((fold * 0.2, 0, fold)), "Head": pose((head, 10, head * 0.6)),
            "ArmL": pose((-arms * 0.3, 0, arms * 0.2)), "ArmR": pose((arms * 0.4, 0, -arms * 0.1)),
            "ForearmL": pose((0, 0, -arms * 0.5)), "ForearmR": pose((0, 0, -arms * 0.3)),
        }

    held(m, "die", [
        {},
        drop(40, 10, 10, 10, 2.0),
        drop(80, 22, 24, 20, 6.0),
        drop(92, 50, 36, 34, 8.1),
        drop(95, 72, 48, 50, 8.5),
        drop(95, 78, 52, 54, 8.6),
    ], end="Hold", stopped="Stop")
    return m


# ---------------------------------------------------------------- Paper Animation
# A flat cut-out paper doll a child might have made: a round crayon face, scribbled hair, two dots for eyes and a red
# grin, a red crayon dress, mittened hands; cut out with a margin of white paper all round, and the arms pinned on with
# brass paper fasteners so they swing in the plane of the paper. Seen edge-on there is almost nothing there.

PA_PAPER = (242, 234, 212)
CR_RED = (222, 44, 38)
CR_BLUE = (40, 84, 210)
CR_YELLOW = (248, 202, 36)
CR_BLACK = (34, 28, 40)
CR_PEACH = (248, 186, 146)
CR_BROWN = (132, 72, 30)
CR_PINK = (244, 118, 150)
BRASS = (214, 170, 64)


class FineModel(Model):
    """A model painted at 4 texels to the pixel rather than 2: the paper doll's crayon needs the room."""

    def save(self):
        old, rig.TEXEL = rig.TEXEL, 4
        try:
            return super().save()
        finally:
            rig.TEXEL = old


def paper_part(ctx, design):
    """design(x, y, w, h) -> the crayon colour of the front's texel at (x, y), or None off the drawing. The front is
    crayon, outlined in black, on a white paper margin; the back is plain paper with the crayon faintly through it."""
    w, h = ctx.w, ctx.h
    front = ctx.face == "west"
    grid = [[design(x if front else w - 1 - x, y, w, h) for x in range(w)] for y in range(h)]
    margin = max(1, rig.TEXEL // 2)

    def inside(x, y):
        return 0 <= x < w and 0 <= y < h and grid[y][x] is not None

    px = ctx.img.load()
    for y in range(h):
        for x in range(w):
            c = grid[y][x]
            if c is None:
                near = any(inside(x + dx, y + dy) for dx in range(-margin, margin + 1) for dy in range(-margin, margin + 1))
                px[ctx.x + x, ctx.y + y] = clamp(shade(PA_PAPER, ctx.rng.uniform(0.96, 1.02))) + (255,) if near else (0, 0, 0, 0)
                continue
            if not front:
                col = mix(PA_PAPER, c, 0.12)
            elif not all(inside(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)) and ctx.rng.random() < 0.9:
                col = CR_BLACK
            else:
                col = shade(c, ctx.rng.uniform(0.88, 1.06))
                if (x + 2 * y) % 5 == 0:
                    col = shade(col, 0.88)                               # the direction of the crayon strokes
                if ctx.rng.random() < 0.14:
                    col = mix(col, PA_PAPER, 0.55)                       # the paper's tooth showing through the wax
            px[ctx.x + x, ctx.y + y] = clamp(col) + (255,)
    grain(ctx, 5)


def pa_head(x, y, w, h):
    k = w / 12                                                           # (laid out on a 12-wide grid)
    cx, cy, r = w / 2, h * 0.42, w * 0.42
    dx, dy = (x + 0.5 - cx) / k, (y + 0.5 - cy) / k
    r /= k
    if y >= h * 0.78 and abs(dx) < 1.6:
        return CR_PEACH                                                  # the neck tab
    d = math.hypot(dx, dy)
    if d > r:
        if dy < -r * 0.2 and d < r + 1.3 and (int(dx * 1.5) % 3 == 0):
            return CR_BROWN                                              # hair sticking out in tufts
        return None
    if dy < -r * 0.3 + 0.9 * abs(math.sin(dx * 1.6)):
        return CR_BROWN                                                  # scribbled hair, a zigzag fringe
    if math.hypot(dy + 0.3, abs(dx) - 2.0) < 0.85:
        return CR_BLACK                                                  # dot eyes
    if abs(dx) < 3.1 and abs(dy - (2.9 - 0.16 * dx * dx)) < 0.5:
        return CR_RED                                                    # a red grin, too wide
    if math.hypot(abs(dx) - 3.3, dy - 1.0) < 0.7:
        return CR_PINK
    return CR_PEACH


def pa_dress(x, y, w, h):
    u, v = (x + 0.5) / w, (y + 0.5) / h
    if abs(u - 0.5) > 0.2 + 0.27 * v:
        return None
    if v < 0.16 and abs(u - 0.5) < 0.16 - v * 0.6:
        return PA_PAPER                                                  # a white collar
    if 0.42 < v < 0.52:
        return CR_YELLOW                                                 # a belt
    if v > 0.86:
        return CR_BLUE                                                   # the hem
    if abs(x + 0.5 - w / 2) < w * 0.04 and (0.22 < v < 0.26 or 0.32 < v < 0.36):
        return CR_BLACK                                                  # buttons
    return CR_RED


def pa_arm(x, y, w, h):
    u, v = (x + 0.5) / w, (y + 0.5) / h
    if v < 0.32:
        return CR_RED if abs(u - 0.5) < 0.45 else None                   # a puffed sleeve
    if v < 0.78:
        return CR_PEACH if abs(u - 0.5) < 0.3 else None
    return CR_PEACH if math.hypot((u - 0.5) * w, (v - 0.88) * h) < w * 0.45 else None   # a mitten hand


def pa_leg(x, y, w, h):
    u, v = (x + 0.5) / w, (y + 0.5) / h
    if v < 0.62:
        return CR_PEACH if abs(u - 0.5) < 0.3 else None
    if v < 0.8:
        return (PA_PAPER if (y * 8 // h) % 2 else CR_BLUE) if abs(u - 0.5) < 0.32 else None   # striped socks
    return CR_BLACK if abs(u - 0.5) < 0.45 else None                     # Mary Janes


def brad(ctx, tx, ty):
    """A brass paper fastener pinning the limb on, on the front."""
    if ctx.face == "west":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                texel(ctx, tx + dx, ty + dy, shade(BRASS, 1.0 - 0.12 * (dx + dy)))
        texel(ctx, tx - 1, ty - 1, (255, 240, 190))
        texel(ctx, tx, ty, shade(BRASS, 0.6))                            # the split of the pin


def animation_paper():
    m = FineModel("animation-paper", atlas_width=48, seed=96)
    flat = ("west", "east")
    # Layers a fraction of a pixel apart: the legs behind the dress, the head and the arms in front of it
    torso = m.part("Torso", (-0.125, 9.5, -3.5), (0.25, 7.5, 7), pivot=(0, 9.5, 0), paint=lambda c: paper_part(c, pa_dress), faces=flat)
    m.part("Head", (-0.32, 16.5, -3), (0.25, 7, 6), pivot=(-0.2, 17, 0), parent=torso, paint=lambda c: paper_part(c, pa_head), faces=flat)

    def arm_paint(c):
        paper_part(c, pa_arm)
        brad(c, c.w // 2, 3)

    m.part("ArmL", (-0.55, 9.5, 2.0), (0.25, 7, 2.4), pivot=(-0.42, 15.8, 3.2), parent=torso, rest=(-10, 0, 0), paint=arm_paint, faces=flat)
    m.part("LegL", (0.2, 0, 0.3), (0.25, 10.5, 2.4), pivot=(0.32, 10, 1.5), parent=torso, rest=(-3, 0, 0), paint=lambda c: paper_part(c, pa_leg), faces=flat)
    m.mirror("ArmL", "ArmR")
    m.mirror("LegL", "LegR")
    # (The mirror puts the right arm a hair to the side of the left; nudge it so both sit in front of the dress)

    # ---- Animations (all stop-motion) ----
    # Everything moves in the plane of the paper, as a cut-out does: rotationX swings a limb sideways (+X takes a
    # hanging limb toward -Z). The walk is a hop and a scissor of the legs, the whole sheet yawing a little.
    def walk(p, amp, lean, hop, yaw):
        a = amp * math.sin(TAU * p)
        return {
            "Torso": pose((s(p, 5), s(p, yaw, 0.25), lean), (0, hop * abs(math.sin(TAU * p)), 0)),
            "LegL": pose((-amp * max(0.0, math.sin(TAU * p)), 0, 0)), "LegR": pose((amp * max(0.0, -math.sin(TAU * p)), 0, 0)),
            "ArmL": pose((-a * 1.1, 0, 0)), "ArmR": pose((-a * 1.1, 0, 0)),
            "Head": pose((s(p, 8, 0.25), 0, -lean * 0.5)),
        }

    held(m, "walk", boil([walk(i / 6, 18, 4, 1.0, 10) for i in range(6)], ("Torso", "Head"), 1.5, 9601))
    held(m, "run", boil([walk(i / 4, 26, 14, 2.0, 14) for i in range(4)], ("Torso", "Head"), 2.0, 9602))

    def idle(i):
        flutter = (0, 3, 0, -3, 0, 0, 4, 0, -2, 0)[i]                     # caught by a draught
        tilt = (0, 0, 0, 12, 12, 12, 0, 0, -10, 0)[i]
        return {"Torso": pose((0, flutter * 3, flutter * 0.5)), "Head": pose((tilt, 0, 0)),
                "ArmL": pose((-flutter * 2, 0, 0)), "ArmR": pose((flutter * 2, 0, 0))}

    held(m, "idle", boil([idle(i) for i in range(10)], ("Torso", "Head", "ArmL", "ArmR"), 1.5, 9603))

    # Slap (18 frames, 0.6 s; damageAtMs 330 lands on pose 3, frames 9-11): the right arm swings up beside the head,
    # the sheet turns and folds forward at the waist, and the arm comes round flat across the face.
    held(m, "slap", [
        {},
        {"Torso": pose((0, -25, -8)), "ArmR": pose((120, 0, 0)), "Head": pose((-10, 0, 0))},
        {"Torso": pose((0, -10, 14)), "ArmR": pose((80, 0, -60)), "Head": pose((-4, 0, 0))},
        {"Torso": pose((0, 25, 30)), "ArmR": pose((10, 0, -95)), "Head": pose((8, 0, 10))},
        {"Torso": pose((0, 32, 26)), "ArmR": pose((-20, 0, -80)), "Head": pose((10, 0, 8))},
        {"Torso": pose((0, 8, 6)), "ArmR": pose((10, 0, -20))},
    ], end="Stop")

    held(m, "hurt", [
        {},
        {"Torso": pose((12, 30, -12)), "Head": pose((-16, 0, 0)), "ArmL": pose((-30, 0, 0)), "ArmR": pose((30, 0, 0))},
        {"Torso": pose((5, 12, -4)), "Head": pose((-6, 0, 0))},
        {},
    ], end="Stop")

    # Death: it tips over backwards like a cardboard stand and lies flat on the floor, rocking once
    def fall(theta, yaw, arms):
        return {"Torso": pose((0, yaw, theta), toppled(theta, 9.5, 0.6)), "ArmL": pose((-arms, 0, 0)), "ArmR": pose((arms, 0, 0)),
                "Head": pose((0, 0, theta * 0.05))}

    held(m, "die", [
        {}, fall(-10, 4, 10), fall(-28, 10, 30), fall(-55, 14, 45), fall(-82, 8, 40), fall(-90, 4, 36), fall(-87, 4, 36), fall(-90, 4, 36),
    ], end="Hold", stopped="Stop")
    return m


# ---------------------------------------------------------------- Robo-Man
# The castle's guards: 1930s tin wind-up toy robots. A boxy body of lithographed tin, crimson with yellow trim and a
# blue panel of dials, rivets everywhere, a riveted silver head with a slotted grill for a mouth and two round yellow
# lenses for eyes, an antenna with a red bulb, accordion arms ending in pincers, block feet, and a big brass key in its
# back that turns as it walks.

RB_RED = (200, 34, 30)
RB_RED_DARK = (138, 22, 24)
RB_BLUE = (32, 70, 170)
RB_YELLOW = (244, 196, 36)
RB_TIN = (184, 190, 198)
RB_TIN_DARK = (106, 112, 124)
RB_TIN_LIGHT = (232, 236, 240)
RB_BRASS = (212, 164, 58)
RB_BLACK = (24, 22, 28)
RB_EYE = (255, 216, 70)


def rivets(ctx, every=4):
    """Rivet heads along the edges: a light point, its shadow below."""
    if ctx.w < 5 or ctx.h < 5:
        return
    pts = set()
    for tx in range(1, ctx.w - 1, every):
        pts.add((tx, 1))
        pts.add((tx, ctx.h - 3))
    for ty in range(1, ctx.h - 2, every):
        pts.add((1, ty))
        pts.add((ctx.w - 2, ty))
    for tx, ty in pts:
        texel(ctx, tx, ty, RB_TIN_LIGHT)
        texel(ctx, tx, ty + 1, RB_TIN_DARK, 0.7)


def rb_tin(ctx, base, trim=None, rv=True, scratches=2):
    fill(ctx, base, 0.03)
    if trim and ctx.face not in ("up", "down"):
        texrow(ctx, 0, 0, -1, trim)
        texrow(ctx, -1, 0, -1, trim)
    for _ in range(scratches):                                          # bare tin where the litho has worn
        u, v = ctx.rng.random(), ctx.rng.random()
        line(ctx, u, v, u + ctx.rng.uniform(-0.2, 0.2), v + ctx.rng.uniform(-0.1, 0.1), RB_TIN_LIGHT if base != RB_TIN else RB_TIN_DARK, 0.45)
    if rv:
        rivets(ctx)
    grain(ctx, 6)


def rb_torso(ctx):
    rb_tin(ctx, RB_RED, RB_YELLOW)
    if ctx.face in ("north", "south"):
        rect(ctx, 0.4, 0.1, 0.6, 0.9, RB_BLUE)                           # a blue stripe down each side
        rect(ctx, 0.44, 0.1, 0.48, 0.9, RB_YELLOW)
    elif ctx.face == "east":
        rect(ctx, 0.42, 0.42, 0.58, 0.58, RB_BLACK)                      # where the key goes in
    elif ctx.face == "west":
        for v in (0.12, 0.88):
            rect(ctx, 0.1, v - 0.03, 0.9, v + 0.03, RB_YELLOW)


def rb_panel(ctx):
    rb_tin(ctx, RB_BLUE, RB_YELLOW, rv=False, scratches=1)
    if ctx.face == "west":                                               # 11 x 9: three dials and two lamps
        for cx in (2, 5, 8):
            for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (2, 0), (1, -1), (-1, 1), (0, 2), (2, 1), (1, 2)):
                texel(ctx, cx + dx, 3 + dy, PAINT_WHITE)
            texel(ctx, cx, 3, RB_BLACK)
            texel(ctx, cx + (1 if cx != 5 else 0), 2 + (cx == 5), RB_BLACK)
        texel(ctx, 3, 7, (240, 40, 30))
        texel(ctx, 7, 7, (60, 220, 80))


def rb_head(ctx):
    rb_tin(ctx, RB_TIN, RB_BLUE)
    if ctx.face == "west":                                               # 12 x 10: a slotted grill for a mouth
        for tx in range(3, 9):
            for ty in (6, 7):
                texel(ctx, tx, ty, RB_BLACK if tx % 2 else RB_TIN_DARK)
        texrow(ctx, 5, 2, 9, RB_RED)
        texrow(ctx, 8, 2, 9, RB_RED)
        texel(ctx, 6, 3, RB_TIN_LIGHT)                                   # a rivet for a nose
        texel(ctx, 6, 4, RB_TIN_DARK)


def rb_eye(ctx):
    fill(ctx, RB_TIN_DARK, 0.05)
    if ctx.face == "west":
        rect(ctx, 0.0, 0.0, 1.0, 1.0, RB_EYE)
        texel(ctx, 0, 0, RB_TIN_DARK)
        texel(ctx, -1, 0, RB_TIN_DARK)
        texel(ctx, 0, -1, RB_TIN_DARK)
        texel(ctx, -1, -1, RB_TIN_DARK)
        texel(ctx, ctx.w // 2, ctx.h // 2, RB_BLACK)
        texel(ctx, ctx.w // 2 - 1, ctx.h // 2 - 1, (255, 250, 220))


def rb_tube(ctx):
    """Accordion tin tubing: ridges every other texel."""
    fill(ctx, RB_TIN, 0.03)
    if ctx.face not in ("up", "down"):
        hlines(ctx, RB_TIN_DARK, 2, start=1, alpha=0.7)
        hlines(ctx, RB_TIN_LIGHT, 2, start=0, alpha=0.3)
    grain(ctx, 5)


def rb_brass(ctx):
    fill(ctx, RB_BRASS, 0.06)
    if ctx.face in ("west", "east"):
        line(ctx, 0.2, 0.2, 0.8, 0.2, (250, 220, 140), 0.6)
    grain(ctx, 6)


def rb_bulb(ctx):
    fill(ctx, (236, 40, 32), 0.05, face_shade=False)
    texel(ctx, 0, 0, (255, 190, 170))


def roboman():
    m = Model("roboman", atlas_width=64, seed=97)
    hips = m.part("Hips", (-2.5, 7.5, -3.75), (5, 2.25, 7.5), pivot=(0, 8.5, 0), paint=lambda c: rb_tin(c, RB_BLUE, RB_YELLOW))
    torso = m.part("Torso", (-3, 9.5, -4.5), (6, 9, 9), pivot=(0, 9.5, 0), parent=hips, paint=rb_torso)
    m.part("Panel", (-3.45, 12, -2.75), (0.5, 4.5, 5.5), parent=torso, paint=rb_panel)
    m.part("Collar", (-1.75, 18.5, -1.75), (3.5, 1, 3.5), parent=torso, paint=lambda c: rb_tin(c, RB_TIN_DARK, rv=False))
    head = m.part("Head", (-2.75, 19.5, -3), (5.5, 5, 6), pivot=(0, 19.5, 0), parent=torso, paint=rb_head)
    m.part("EyeL", (-3.3, 21.6, 0.35), (0.6, 1.9, 1.9), parent=head, paint=rb_eye, glow=60)
    m.part("EarL", (-1, 21, 2.9), (2, 2, 0.7), parent=head, paint=rb_brass)
    antenna = m.part("Antenna", (-0.25, 24.5, -0.25), (0.5, 2.75, 0.5), pivot=(0, 24.5, 0), parent=head, paint=lambda c: fill(c, RB_TIN_DARK, 0.05))
    m.part("Bulb", (-0.6, 27.1, -0.6), (1.2, 1.2, 1.2), parent=antenna, paint=rb_bulb, glow=120)
    # The wind-up key: a shaft out of the back and a two-lobed bow, turning about the shaft (X)
    key = m.part("Key", (3, 13.6, -0.4), (1.8, 0.8, 0.8), pivot=(3, 14, 0), parent=torso, paint=rb_brass)
    m.part("KeyBar", (4.8, 13.4, -2.6), (0.5, 1.2, 5.2), pivot=(3, 14, 0), parent=key, paint=rb_brass)
    m.part("KeyLobeL", (4.8, 12.5, 1.1), (0.5, 3, 1.7), pivot=(3, 14, 0), parent=key, paint=rb_brass)
    m.part("KeyLobeR", (4.8, 12.5, -2.8), (0.5, 3, 1.7), pivot=(3, 14, 0), parent=key, paint=rb_brass)
    arm = m.part("ArmL", (-1, 13.5, 4.5), (2, 4.5, 2), pivot=(0, 17, 5.5), parent=torso, rest=(-4, 0, 0), paint=rb_tube)
    m.part("ShoulderL", (-1.25, 16.25, 4.4), (2.5, 2.25, 2.2), parent=arm, paint=lambda c: rb_tin(c, RB_RED, rv=False))
    fore = m.part("ForearmL", (-0.85, 10, 4.65), (1.7, 4, 1.7), pivot=(0, 13.75, 5.5), parent=arm, paint=rb_tube)
    hand = m.part("HandL", (-1.25, 8, 4.25), (2.5, 2.25, 2.5), pivot=(0, 10, 5.5), parent=fore, paint=lambda c: rb_tin(c, RB_TIN_DARK, rv=False))
    m.part("PincerAL", (-1.3, 6.2, 4.6), (0.8, 1.9, 1.8), pivot=(-0.9, 8, 5.5), parent=hand, paint=lambda c: rb_tin(c, RB_TIN_DARK, rv=False))
    m.part("PincerBL", (0.5, 6.2, 4.6), (0.8, 1.9, 1.8), pivot=(0.9, 8, 5.5), parent=hand, paint=lambda c: rb_tin(c, RB_TIN_DARK, rv=False))
    leg = m.part("LegL", (-1.5, 2, 0.6), (3, 6, 3), pivot=(0, 8, 2.1), parent=hips, paint=rb_tube)
    m.part("FootL", (-3.6, 0, 0.25), (5.6, 2, 3.7), pivot=(0, 2, 2.1), parent=leg, paint=lambda c: rb_tin(c, RB_RED, RB_YELLOW, rv=False))
    m.mirror("ArmL", "ArmR")
    m.mirror("LegL", "LegR")
    m.mirror("EyeL", "EyeR")
    m.mirror("EarL", "EarR")

    # ---- Animations (all stop-motion) ----
    # The key is symmetric under half a turn, so it is wound 180 degrees per cycle, in steps
    def walk(p, i, n, amp, lean, arm):
        a = amp * math.sin(TAU * p)
        return {
            "LegL": pose((0, 0, -a)), "LegR": pose((0, 0, a)),               # no knees: stiff tin legs
            "FootL": pose((0, 0, a * 0.5)), "FootR": pose((0, 0, -a * 0.5)),
            "Hips": pose((s(p, 7), 0, 0), (0, 0.6 * abs(math.sin(TAU * p)), 0)),   # a waddle, rocking foot to foot
            "Torso": pose((-s(p, 3), s(p, 6), lean)),
            "Head": pose((0, -s(p, 6), -lean)),
            "ArmL": pose((0, 0, s(p, arm))), "ArmR": pose((0, 0, -s(p, arm))),
            "Key": pose((-180 * i / n, 0, 0)),
            "Antenna": pose((s(p, 10, 0.2), 0, s(p * 2, 6))),
        }

    jitter = ("Torso", "Head", "Antenna")
    held(m, "walk", boil([walk(i / 8, i, 8, 16, 2, 26) for i in range(8)], jitter, 0.8, 9701))
    held(m, "run", boil([walk(i / 6, i, 6, 24, 10, 40) for i in range(6)], jitter, 1.2, 9702))

    def idle(i):
        look = (0, 0, 0, 30, 30, 30, 0, 0, -30, -30, -30, 0)[i]          # the head clicks round, scanning the hall
        return {"Head": pose((0, look, 0)), "Key": pose((-15 * i, 0, 0)), "Antenna": pose((0, 0, (-4, 4)[i % 2])),
                "Torso": pose((0, look * 0.1, 0))}

    held(m, "idle", boil([idle(i) for i in range(12)], ("Torso",), 0.6, 9703))

    # Punch (21 frames, 0.7 s; damageAtMs 330 lands on pose 3, frames 9-11): the right arm swings up level, the
    # body winds back, then turns and the forearm pistons out of the upper arm, pincers snapping shut.
    held(m, "punch", [
        {},
        {"ArmR": pose((0, 0, -88)), "Torso": pose((0, -12, 0)), "PincerAR": pose((0, 0, 0), (0, 0, -0.3)), "PincerBR": pose((0, 0, 0), (0, 0, -0.3))},
        {"ArmR": pose((0, 0, -90)), "ForearmR": pose((0, 0, 0), (0, 2.5, 0)), "Torso": pose((0, -26, -4)), "Head": pose((0, 18, 0)),
         "PincerAR": pose((0, 0, -30)), "PincerBR": pose((0, 0, 30))},
        {"ArmR": pose((0, 0, -92)), "ForearmR": pose((0, 0, 0), (0, -3.5, 0)), "Torso": pose((0, 22, 8)), "Head": pose((0, -14, -6)),
         "Hips": pose((0, 0, 0), (-0.8, 0, 0)), "LegL": pose((0, 0, -10)), "LegR": pose((0, 0, 8))},
        {"ArmR": pose((0, 0, -90)), "ForearmR": pose((0, 0, 0), (0, -3.0, 0)), "Torso": pose((0, 26, 6)), "Head": pose((0, -16, -6)),
         "Hips": pose((0, 0, 0), (-0.8, 0, 0)), "LegL": pose((0, 0, -10)), "LegR": pose((0, 0, 8))},
        {"ArmR": pose((0, 0, -80)), "Torso": pose((0, 8, 2))},
        {"ArmR": pose((0, 0, -36))},
    ], end="Stop")

    held(m, "hurt", [
        {},
        {"Torso": pose((8, 0, -12)), "Head": pose((14, 0, -10)), "Antenna": pose((20, 0, -20)), "ArmL": pose((-24, 0, 0)), "ArmR": pose((24, 0, 0))},
        {"Torso": pose((3, 0, -4)), "Head": pose((4, 0, -4)), "Antenna": pose((-10, 0, 10))},
        {},
    ], end="Stop")

    # Death: it runs down. The key turns slower and slower, the head droops, it leans further and further forward
    # and falls flat on its face, one arm still twitching.
    def wind_down(theta, key, head, arms):
        return {"Hips": pose((0, 0, theta), toppled(theta, 8.5, 3.4)), "Key": pose((-key, 0, 0)), "Head": pose((0, 0, head)),
                "ArmL": pose((0, 0, -arms)), "ArmR": pose((0, 0, -arms * 0.96)), "Antenna": pose((0, 0, theta * 0.2))}

    held(m, "die", [
        {}, wind_down(4, 20, 6, 0), wind_down(8, 34, 14, 6), wind_down(14, 42, 22, 12), wind_down(30, 46, 26, 30),
        wind_down(62, 48, 20, 110), wind_down(90, 48, 10, 186), wind_down(86, 48, 10, 178), wind_down(90, 48, 10, 186),
    ], end="Hold", stopped="Stop")
    return m


MODELS = {
    "skinstealer": skinstealer, "hound": hound, "duller": duller, "deathrat": deathrat,
    "deathmoth-male": lambda: deathmoth(False), "deathmoth-female": lambda: deathmoth(True),
    "smiler": smiler, "clump": clump, "mangled": mangled, "thething": thething,
    "animation-clay": animation_clay, "animation-wooden": animation_wooden, "animation-paper": animation_paper, "roboman": roboman,
}


def build(names=None):
    for name in names or list(MODELS):
        MODELS[name]().save()
        if name == "deathrat":
            deathrat_variant_textures()
        if name == "clump":
            clump_variant_textures()
        if name == "hound":
            hound_variant_textures()


def main():
    build(sys.argv[1:])


if __name__ == "__main__":
    main()
