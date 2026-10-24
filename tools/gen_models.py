"""The Backrooms' entities, modelled after the lore (Wikidot entity pages) and animated: written as Vintage Story
shapes with their textures (see rig.py for the conventions: models face -X, left is +Z, feet at y=0).

Run from the repo root:  python tools/gen_models.py [name ...]
"""
import math
import os
import random
import sys

import rig
from rig import ASSETS, Model, speckle, hlines, vlines, rect, mix, shade, clamp, gradient_down, pose
from rig import lit_fill as fill   # rig.fill on an unbaked model; shade_fill on a model with a light bake (B17)

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


def lit(**opts):
    """B17: gives the model a builder makes a light bake (rig.bake; `opts` over rig.LIGHT). As a decorator, so the
    variant painters, which call the builders again, get it too."""
    def wrap(builder):
        def build_lit(*a, **k):
            m = builder(*a, **k)
            m.light = dict(opts)
            return m
        build_lit.__name__ = builder.__name__
        build_lit.__doc__ = builder.__doc__
        return build_lit
    return wrap


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


# The fed look (AI overhaul, README 6.1): a fed Skin-Stealer is docile and wears a person's clothes over a fresher, less
# waxy skin (the lore: it keeps the skin warm with pumped blood). Painted on the common atlas, so it is a texture
# alternate; the tells stay (the sunken eyes, the long forearms, the cuffs ending short of the knuckles).
SK_FED = False
SK_FRESH = dict(SK_BASE=(236, 212, 188), SK_CREAM=(248, 230, 214), SK_TAN=(214, 172, 146), SK_PINK=(218, 152, 144),
                SK_BROWN=(150, 106, 84), SK_BRUISE=(172, 132, 142), SK_GREEN=(196, 182, 156))
SK_SHIRT = (84, 98, 120)       # a faded blue work shirt
SK_TROUSERS = (64, 58, 52)     # dark, worn trousers
SK_SHOE = (38, 30, 26)


def clothe(ctx, colour, until=1.0, seam=True):
    """Cloth over the skin on the top `until` of a face: a weave, a seam, a fold or two."""
    if not SK_FED:
        return
    px = ctx.img.load()
    rows = max(1, int(round(ctx.h * until)))
    for yy in range(rows):
        for xx in range(ctx.w):
            k = {"up": 1.08, "down": 0.72, "north": 0.94, "south": 0.94, "east": 0.88, "west": 1.0}[ctx.face]
            m = 1 + 0.07 * (ctx.rng.random() - 0.5) * 2
            if (xx + yy) % 2 == 0:
                m *= 0.95                                           # the weave
            px[ctx.x + xx, ctx.y + yy] = shade(colour, k * m) + (255,)
    if seam and ctx.face in ("west", "east", "north", "south"):
        line(ctx, 0.5, 0.0, 0.5, until, shade(colour, 0.7), 0.45)
        line(ctx, 0.0, until * 0.55, 1.0, until * 0.5, shade(colour, 0.8), 0.4)      # a crease where it bunches
    if until < 1.0 and ctx.face in ("west", "east", "north", "south"):
        texrow(ctx, rows - 1, 0, -1, shade(colour, 0.65), 0.8)    # the hem or cuff


def worn(paint, colour, until=1.0, buttons=False):
    """A painter that puts clothes on whatever `paint` draws, when painting the fed look (and is `paint` itself otherwise)."""
    def wrapped(ctx):
        paint(ctx)
        if SK_FED:
            clothe(ctx, colour, until)
            if buttons and ctx.face == "west":
                for yy in range(1, ctx.h - 1, 3):
                    texel(ctx, ctx.w // 2, yy, shade(colour, 1.5), 0.9)
    wrapped.__name__ = paint.__name__
    return wrapped


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


def sk_base(ctx, base=None):
    """Waxy, stretched, old skin: a flat base with slow mottling, a bruise now and then, a faint sheen on top faces."""
    if base is None:
        base = SK_BASE
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
    if ctx.baked and ctx.face in ("west", "north", "south"):
        rig.folds(ctx, (0.45,), depth=0.82, light=1.06)
    if ctx.face in ("west", "north", "south"):
        texrow(ctx, -1, 0, -1, SK_BROWN, 0.6)
        texrow(ctx, 0, 0, -1, SK_TAN, 0.4)


def sk_neck(ctx):
    sk_base(ctx)
    if ctx.baked and ctx.face in ("west", "north", "south"):
        rig.folds(ctx, (0.25, 0.7), depth=0.88, light=1.05, wobble=0.8)    # B17: the stretched neck's rings
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
        if ctx.baked:
            rig.folds(ctx, (0.8, 0.9), depth=0.84, light=1.05)          # B17: the loose skin rucked up at the wrist
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


def death(m, frames, names, keys, floor=-0.25, airborne=(), standing=(), soft=(), code="die"):
    """A death animation to the standard in docs/design/entity-ai-overhaul/death-poses.md: `keys` maps frame to
    {part: pose}; every keyframe names every part in `names` (at rest unless posed) and is settled so its lowest box
    rests on the floor (`floor` px, a little below 0 to press the body into it), so a collapse keeps its weight on
    the ground. Frame 0 (the rest pose the death blends from) and frames in `airborne` (a flier falling) are left
    where they are; frames in `standing` (still on its feet) are settled to the rest pose's own lowest point, so the
    feet do not pop up or down. Parts in `soft` (hair, cloth) do not hold the body up. The last keyframe should be
    frames - 1: it is held."""
    rest_low = rig.posed_extent(m, {}, soft)[0]
    out = {}
    for f, d in keys.items():
        k = full(names, d)
        if f != 0 and f not in airborne:
            rig.settle(m, k, rest_low if f in standing else floor, soft)
        out[f] = k
    m.animation(code, frames, out, end="Hold", stopped="Stop")


def ramp(p, a, b, c, d):
    """0 before a, rising to 1 at b, holding to c, falling to 0 at d."""
    if p <= a or p >= d:
        return 0.0
    if p < b:
        return (p - a) / (b - a)
    if p <= c:
        return 1.0
    return (d - p) / (d - c)


@lit()
def skinstealer():
    m = Model("skinstealer", atlas_width=64, seed=10)
    # Torso chain. The rest rotations give the forward hunch: belly 3, chest 6 and neck 10 lean forward (19 in all);
    # the head takes 10 back so it pitches forward by 9 and sits forward of the shoulders on its too-long neck.
    pelvis = m.part("Pelvis", (-1.5, 16.5, -2.75), (3, 3, 5.5), pivot=(0, 18, 0), paint=worn(sk_pelvis, SK_TROUSERS))
    belly = m.part("TorsoLower", (-1.75, 19.5, -2.75), (3.5, 4.5, 5.5), pivot=(0, 19.5, 0), parent=pelvis, rest=(0, 0, 3), paint=worn(sk_belly, SK_SHIRT, buttons=True))
    chest = m.part("TorsoUpper", (-2.25, 24, -3.5), (4, 5.5, 7), pivot=(0, 24, 0), parent=belly, rest=(0, 0, 6), paint=worn(sk_chest, SK_SHIRT, buttons=True))
    neck = m.part("Neck", (-1.125, 29.5, -1.125), (2.25, 3.5, 2.25), pivot=(0, 29.5, 0), parent=chest, rest=(0, 0, 10), paint=sk_neck)
    head = m.part("Head", (-3, 32.5, -2.25), (5, 6, 4.5), pivot=(0, 33, 0), parent=neck, rest=(5, -4, -10), paint=sk_head)
    m.part("Jaw", (-3.25, 32, -2.25), (2.75, 2, 4.5), pivot=(-0.5, 34, 0), parent=head, paint=sk_jaw)
    m.part("NeckFold", (-1.8, 30.9, -1.5), (0.75, 1.3, 3), pivot=(-1.05, 32.2, 0), parent=head, rest=(0, 0, -8), paint=sk_fold)

    # Arms: ordinary upper arms, forearms too long, flat hands with three stiff fingers reaching the knee.
    arm = m.part("ArmL", (-1.25, 22, 3.75), (2.5, 7, 2.5), pivot=(0, 28.75, 5), parent=chest, rest=(-3, 0, -15), paint=worn(sk_upperarm, SK_SHIRT))
    fore = m.part("ForearmL", (-1, 14, 4), (2, 8, 2), pivot=(0, 22, 5), parent=arm, rest=(4, 0, -12), paint=worn(sk_forearm, SK_SHIRT, 0.8))
    palm = m.part("HandL", (-0.75, 11.5, 3.875), (1.5, 2.5, 2.25), pivot=(0, 14, 5), parent=fore, rest=(0, 0, 4), paint=sk_palm)
    for i in range(3):
        z = 4.0 + i * 0.8
        m.part(f"Finger{i}L", (-0.55, 9, z), (0.7, 2.5, 0.6), pivot=(-0.2, 11.5, z + 0.3), parent=palm, rest=(0, 0, -4 + 3 * i), paint=sk_finger)
    # Legs: thin, knees very slightly bent, feet flat and a little long, toes turned out a touch.
    thigh = m.part("ThighL", (-1.5, 9, 0.4), (3, 7.5, 3), pivot=(0, 16.5, 1.9), parent=pelvis, rest=(0, 0, -4), paint=worn(sk_thigh, SK_TROUSERS))
    shin = m.part("ShinL", (-1.25, 1.5, 0.65), (2.5, 7.5, 2.5), pivot=(0, 9, 1.9), parent=thigh, rest=(0, 0, 8), paint=worn(sk_shin, SK_TROUSERS, 0.85))
    m.part("FootL", (-3.6, 0, 0.65), (4.75, 1.5, 2.5), pivot=(0, 1.5, 1.9), parent=shin, rest=(0, 7, -4), paint=worn(sk_foot, SK_SHOE))
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

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): whatever holds the skin up fails. A jolt, the knees
    # go with the feet still planted, it kneels for a moment as the torso folds at the hips, then pitches forward onto
    # its chest, turned a little onto its left side, the arms flung out by the landing, rocks and goes slack: the left
    # arm out along the floor, the right bent up with the hand by the face, the right knee drawn up out to the side,
    # the head laid on its left cheek last with the jaw hanging open. With the body face down, the floor is -X in the
    # pelvis's frame; +X on the pelvis rolls it onto its left side. (The held limbs were placed with a small solver
    # against floor contact and hand/knee targets, so they rest on the floor without propping the torso up.)
    die_names = [p.name for p in m.parts]

    def legs(tl, tr, pz=0.0):
        """The knees folding straight down over planted feet: thigh angles (world, forward is -) under a pelvis
        pitched by pz; the shins fold twice as far, the feet stay flat."""
        return {"ThighL": pose((2, 0, tl - pz)), "ShinL": pose((0, 0, -2 * tl)), "FootL": pose((0, 0, tl)),
                "ThighR": pose((-2, 0, tr - pz)), "ShinR": pose((0, 0, -2 * tr)), "FootR": pose((0, 0, tr))}

    def curl(cl, cr):
        return {f"Finger{i}{sd}": pose((0, 0, c - 7 * ((i + j) % 3))) for j, (sd, c) in enumerate((("L", cl), ("R", cr))) for i in range(3)}

    def prone(roll, slack, jaw, head_k, **limbs):
        """Face down, rolled `roll` degrees onto its left side, from the way it landed (slack 0) to the way it rests
        (slack 1): the left arm flung out to the side, the right bent up with the hand by the face, the left leg
        trailing, the right knee drawn up out to the side; the head turned onto its left cheek by head_k (0..1)."""
        def at(a, b):
            return tuple(a[i] + (b[i] - a[i]) * slack for i in range(3))
        return dict({
            "Pelvis": pose((roll, 3, 93)), "TorsoLower": pose(at((0, 2, -6), (-1, 6, -3))), "TorsoUpper": pose(at((0, 2, -10), (-4, 8, -8))),
            "Neck": pose(at((0, 0, -14), (1, -7, -12))), "Head": pose((15 * head_k, -61 * head_k, -8 + 6 * head_k)), "Jaw": pose((0, 0, jaw)),
            "NeckFold": pose((0, 0, -6 * head_k)),
            "ArmL": pose(at((-102, -10, 62), (-57, -17, 41))), "ForearmL": pose(at((7, 0, -30), (2, 0, -25))), "HandL": pose(at((-5, 0, 17), (6, 0, 22))),
            "ArmR": pose(at((52, -38, -18), (67, -40, -6))), "ForearmR": pose(at((-30, 0, -105), (-33, 0, -125))), "HandR": pose(at((4, 0, 4), (2, 0, -5))),
            "ThighL": pose(at((-6, -20, -6), (-10, -40, -1))), "ShinL": pose(at((-2, 0, 16), (-6, 0, 8))), "FootL": pose(at((0, -10, 20), (2, -23, 1))),
            "ThighR": pose(at((6, -20, -30), (14, -40, -55))), "ShinR": pose(at((-8, 0, 40), (-15, 0, 56))), "FootR": pose(at((0, -6, 14), (-5, -12, -2))),
        }, **curl(-12 - 10 * slack, -18 - 14 * slack), **{k: pose(v) for k, v in limbs.items()})

    death(m, 40, die_names, {
        0: {},
        # the hit: it stiffens, the head jerks back and the jaw drops, the arms twitch out
        3: dict({"TorsoUpper": pose((0, 4, -6)), "Neck": pose((0, 0, -6)), "Head": pose((6, 8, -10)), "Jaw": pose((0, 0, 20)),
                 "ArmL": pose((-10, 0, -6)), "ArmR": pose((8, 0, -8))}, **curl(10, 8)),
        # the knees go, the feet still planted; the torso sags forward, the head lolls
        8: dict({"Pelvis": pose((3, 4, 0)), "TorsoLower": pose((0, 0, 8)), "TorsoUpper": pose((0, 2, 6)), "Neck": pose((0, 0, 8)), "Head": pose((-6, 4, 6)),
                 "Jaw": pose((0, 0, 16)), "ArmL": pose((-6, 0, -4)), "ArmR": pose((4, 0, -2)), "ForearmL": pose((0, 0, 6)), "ForearmR": pose((0, 0, 4))},
                **legs(-34, -26), **curl(-4, -6)),
        # the knees reach the floor
        11: dict({"Pelvis": pose((5, 6, 10)), "TorsoLower": pose((0, 0, 12)), "TorsoUpper": pose((0, 3, 9)), "Neck": pose((0, 0, 10)), "Head": pose((-8, 5, 8)),
                  "Jaw": pose((0, 0, 17)), "ArmL": pose((-10, 0, -16)), "ArmR": pose((5, 0, -12)), "ForearmL": pose((0, 0, -2)), "ForearmR": pose((0, 0, -4))},
                 **legs(-52, -46, pz=10), **curl(-5, -7)),
        # down on its knees, folding at the hips, the arms swinging forward and loose
        13: dict({"Pelvis": pose((6, 8, 22)), "TorsoLower": pose((0, 0, 14)), "TorsoUpper": pose((0, 4, 12)), "Neck": pose((0, 0, 10)), "Head": pose((-8, 6, 10)),
                  "Jaw": pose((0, 0, 18)), "ArmL": pose((-12, 0, -30)), "ArmR": pose((6, 0, -24)), "ForearmL": pose((0, 0, -8)), "ForearmR": pose((0, 0, -10)),
                  "ThighL": pose((2, 0, -62)), "ShinL": pose((0, 0, 118)), "FootL": pose((0, 0, -30)),
                  "ThighR": pose((-2, 0, -56)), "ShinR": pose((0, 0, 112)), "FootR": pose((0, 0, -24))}, **curl(-6, -8)),
        # pitching forward, rolling to the left, the hips lifting off the heels; the arms trail, limp
        18: dict({"Pelvis": pose((12, 4, 56)), "TorsoLower": pose((0, 0, 6)), "TorsoUpper": pose((0, 2, 2)), "Neck": pose((0, 0, -2)), "Head": pose((-4, -6, 2)),
                  "Jaw": pose((0, 0, 22)), "ArmL": pose((-24, 0, -4)), "ArmR": pose((20, 0, -14)), "ForearmL": pose((4, 0, -40)), "ForearmR": pose((-4, 0, -30)),
                  "HandL": pose((0, 0, 10)), "HandR": pose((0, 0, 12)),
                  "ThighL": pose((2, 0, -40)), "ShinL": pose((0, 0, 90)), "FootL": pose((0, 0, 30)),
                  "ThighR": pose((4, 0, -46)), "ShinR": pose((0, 0, 92)), "FootR": pose((0, 0, 24))}, **curl(-8, -10)),
        # the chest hits first, the legs sliding out behind, the arms flung out by the landing
        20: dict({"Pelvis": pose((24, 2, 78)), "TorsoLower": pose((0, 0, 0)), "TorsoUpper": pose((-2, 2, -4)), "Neck": pose((0, 0, -4)), "Head": pose((4, -16, -4)),
                  "Jaw": pose((0, 0, 26)), "ArmL": pose((-70, -8, 40)), "ArmR": pose((40, -26, -40)), "ForearmR": pose((-14, 0, -70)), "ForearmL": pose((0, 0, -16)),
                  "HandL": pose((0, 0, 10)), "HandR": pose((0, 0, 16)),
                  "ThighL": pose((0, 0, -18)), "ShinL": pose((0, 0, 50)), "FootL": pose((0, 0, 40)),
                  "ThighR": pose((14, 0, -30)), "ShinR": pose((-10, 0, 60)), "FootR": pose((0, -10, 36))}, **curl(-10, -14)),
        # impact: flat on its chest, rolled a little past
        22: prone(31, 0.0, jaw=26, head_k=0.4),
        # it rocks back
        26: prone(22, 0.5, jaw=30, head_k=0.7, ArmL=(-78, -10, 48), ForearmL=(7, 0, -31), HandL=(5, 0, 23),
                  ArmR=(56, -40, -14), ForearmR=(-39, 0, -119), HandR=(7, 0, 1), ThighR=(17, -40, -52), ShinR=(-15, 0, 53), FootR=(-8, -14, 3)),
        # and settles, the limbs slack; the head turns onto its cheek last
        31: prone(25, 0.85, jaw=28, head_k=0.9, ArmL=(-68, -7, 38), ForearmL=(8, 0, -14), HandL=(6, 0, 17),
                  ArmR=(56, -40, -14), ForearmR=(-39, 0, -119), HandR=(7, 0, 1)),
        39: prone(24, 1.0, jaw=30, head_k=1.0),
    }, standing=(3,))
    return m


def skinstealer_variant_textures():
    """The fed look, painted on the common atlas layout so it works as a texture alternate (index 1)."""
    global SK_FED
    g = globals()
    saved = {k: g[k] for k in SK_FRESH}
    g.update(SK_FRESH)
    SK_FED = True
    m = skinstealer()
    width, height = m._pack()
    m._paint(width, height).save(os.path.join(ASSETS, "textures", "entity", "skinstealer-fed.png"))
    print(f"wrote skinstealer-fed texture {width}x{height}")
    SK_FED = False
    g.update(saved)


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
    if ctx.baked and ctx.face in ("north", "south", "east", "west") and ctx.h >= 8:
        rig.fur(ctx, (0, 1), length=4, density=0.18, tip=0.94, root=1.05)       # B17: sinew down the limb, faint
        rig.folds(ctx, [r for r, on in ((0.18, top), (0.8, bottom)) if on], depth=0.86, light=1.06)
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
        if ctx.baked:
            rig.strands(ctx, HAIR, mix(HAIR, HAIR_HI, 0.6 if HAIR[0] > 60 else 1.0), sheen=0.5, spread=0.35, parting=0.25,
                        along="u" if ctx.face == "up" else "v")
        else:
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
    if ctx.baked:   # B17: strands of their own tone, lit where they fall over the crown, partings, a few greys
        rig.strands(ctx, HAIR, mix(HAIR, HAIR_HI, 0.6 if HAIR[0] > 60 else 1.0), sheen=0.55, spread=0.35, parting=0.25, grey=mix(HAIR_HI, (150, 146, 140), 0.4),
                    grey_chance=0.06, along="v" if ctx.face not in ("up", "down") else "u", sheen_at=0.15,
                    dirt=DIRT, dirt_chance=0.012)
    else:
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
    if ctx.baked:
        rig.strands(ctx, HAIR, mix(HAIR, HAIR_HI, 0.6 if HAIR[0] > 60 else 1.0), sheen=0.5, spread=0.35, parting=0.25,
                    along="u" if ctx.face == "up" else "v", sheen_at=0.3, grey=mix(HAIR_HI, (150, 146, 140), 0.4), grey_chance=0.05)
    else:
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


@lit()
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

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): a flinch, the arms buckle at the elbows and the
    # chest drops onto them, the hind legs give and the hips sit, then it tips over onto its left side, rocks once and
    # settles: every joint loose and a little different (the right limbs, on top, fall across the left ones, which lie
    # under it on the floor), the back curled, the head laid on the floor last with the jaw hanging open and the hair
    # spilled over the face. With the body on its left side, the floor is +Z in the body's frame: a limb falls onto
    # the floor with -X rotation, and a curl of the back (Z rotation) lies flat along the floor.
    die_names = ["Body", "Spine", "Pelvis", "Neck", "Head", "Jaw", "ArmL", "ArmR", "ForearmL", "ForearmR", "HandL", "HandR",
                 "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR"] + [f"Finger{i}{sd}" for sd in "LR" for i in range(3)] + hair_names

    def fallen_hair(k, lift=0.0, back=0.0):
        """Hair falling toward the floor (+Z in the body's frame once it lies on its left side) by k (0..1)."""
        d = {}
        for i, (z, length) in enumerate(FRONT_HAIR):
            d[f"Hair{i}"] = pose((-k * (6 + 4 * ((i * 5) % 3)) + lift, 0, k * (10 + 6 * (i % 2)) + back))
        for j, n in enumerate(("HairSideL0", "HairSideL1", "HairSideR0", "HairSideR1")):
            d[n] = pose((-k * (4 + 3 * j) + lift, 0, k * 6))
        for j, n in enumerate(("HairManeL0", "HairManeL1", "HairManeR0", "HairManeR1")):
            d[n] = pose((-k * (5 + 3 * j) + lift, 0, -k * 8))
        return d

    def fingers(curl_l, curl_r):
        return {f"Finger{i}{sd}": pose((0, 0, c + 9 * ((i + j) % 3))) for j, (sd, c) in enumerate((("L", curl_l), ("R", curl_r))) for i in range(3)}

    def lying(roll, slack, jaw, hair_k):
        """On its side (`roll` degrees about the spine), from the fold it fell in (slack 0) to the pose it rests in
        (slack 1): the back curled, the arms drawn up toward the face with the elbows bent, the knees drawn up toward
        the belly, the top (right) limbs fallen across the bottom ones."""
        def at(a, b):
            return tuple(a[i] + (b[i] - a[i]) * slack for i in range(3))
        return dict({
            "Body": pose((roll, 0, at((8, 0, 0), (6, 0, 0))[0])), "Spine": pose(at((6, 0, -2), (4, 0, -8))), "Pelvis": pose(at((10, 0, -2), (9, 0, -8))),
            "Neck": pose(at((6, 0, 12), (6, 6, 18))), "Head": pose(at((4, 3, 6), (4, 6, 8))), "Jaw": pose((3 * slack, 0, jaw)),
            "ArmL": pose(at((8, 0, 4), (10, 0, -38))), "ForearmL": pose(at((0, 0, -100), (0, 0, -78))), "HandL": pose(at((0, 0, 36), (6, 0, 34))),
            "ArmR": pose(at((-14, 0, 6), (-34, 0, -10))), "ForearmR": pose(at((0, 0, -92), (-10, 0, -62))), "HandR": pose(at((0, 0, 32), (-20, 0, 36))),
            "ThighL": pose(at((6, 0, -56), (8, 0, -52))), "ShinL": pose(at((0, 0, 70), (0, 0, 22))), "FootL": pose(at((0, 0, -10), (12, 0, 18))),
            "ThighR": pose(at((-10, 0, -58), (-30, 0, -36))), "ShinR": pose(at((0, 0, 66), (0, 0, 4))), "FootR": pose(at((0, 0, -12), (0, 0, 30))),
        }, **fingers(20 + 8 * slack, 22 + 16 * slack), **fallen_hair(hair_k))

    death(m, 42, die_names, {
        0: hair(0),
        # the hit: a flinch, the head jerks up, the jaw drops
        4: dict({"Body": pose((3, 2, -5)), "Neck": pose((0, 4, -12)), "Head": pose((4, 6, -6)), "Jaw": pose((0, 0, 30)),
                 "ArmL": pose((0, 0, -4)), "ArmR": pose((0, 0, -6)), "ThighL": pose((0, 0, -3)), "ThighR": pose((0, 0, -4))},
                **hair(0.1, back=12, sway=6)),
        # the arms buckle: the elbows fold back and the chest drops onto the forearms, the head to the floor, the hair
        # swinging back off the face; the hips still up
        8: dict({"Body": pose((4, 2, 22)), "Spine": pose((0, 0, -4)), "Pelvis": pose((0, 0, -16)),
                 "Neck": pose((0, -2, -10)), "Head": pose((2, 4, -8)), "Jaw": pose((0, 0, 26)),
                 "ArmL": pose((-12, 0, 16)), "ArmR": pose((14, 0, 12)), "ForearmL": pose((0, 0, -70)), "ForearmR": pose((0, 0, -62)),
                 "HandL": pose((0, 0, 24)), "HandR": pose((0, 0, 20)), "ThighL": pose((0, 0, 3)), "ThighR": pose((0, 0, 4))},
                **fingers(6, 4), **hair(0.2, sway=7, back=20)),
        12: dict({"Body": pose((6, 2, 42)), "Spine": pose((0, 0, -6)), "Pelvis": pose((0, 0, -30)),
                  "Neck": pose((0, -3, -6)), "Head": pose((2, 4, -10)), "Jaw": pose((0, 0, 22)),
                  "ArmL": pose((-14, 0, 12)), "ArmR": pose((16, 0, 8)), "ForearmL": pose((0, 0, -120)), "ForearmR": pose((0, 0, -110)),
                  "HandL": pose((0, 0, 40)), "HandR": pose((0, 0, 35)),
                  "ThighL": pose((0, 0, 4)), "ThighR": pose((0, 0, 6)), "ShinL": pose((0, 0, 4)), "ShinR": pose((0, 0, 2))},
                 **fingers(10, 6), **hair(0.3, sway=5, back=45, part_=10)),
        # the hind legs give: the hips drop onto the folded legs, and the body starts to tip onto its left side
        18: dict({"Body": pose((20, 2, 14)), "Spine": pose((2, 0, -2)), "Pelvis": pose((4, 0, -6)),
                  "Neck": pose((0, 4, -2)), "Head": pose((2, 4, -6)), "Jaw": pose((0, 0, 26)),
                  "ArmL": pose((-10, 0, 10)), "ArmR": pose((14, 0, 4)), "ForearmL": pose((0, 0, -110)), "ForearmR": pose((0, 0, -100)),
                  "HandL": pose((0, 0, 40)), "HandR": pose((0, 0, 35)),
                  "ThighL": pose((4, 0, -60)), "ThighR": pose((-2, 0, -64)), "ShinL": pose((0, 0, 80)), "ShinR": pose((0, 0, 76)),
                  "FootL": pose((0, 0, -10)), "FootR": pose((0, 0, -12))},
                 **fingers(16, 14), **fallen_hair(0.3, back=30)),
        # over onto its left side, a little past; the limbs still folded from the fall
        23: lying(94, 0.0, jaw=20, hair_k=0.8),
        # rocks back once, the top limbs swinging down
        28: lying(81, 0.6, jaw=30, hair_k=0.95),
        # settling: the limbs go slack, the head sinks to the floor
        34: lying(86, 0.9, jaw=27, hair_k=1.0),
        41: lying(85, 1.0, jaw=28, hair_k=1.0),
    }, standing=(4, 8, 12), soft=hair_names + ["HairCrown", "HairBack"])

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
    if ctx.baked and ctx.face in ("north", "south", "east", "west") and ctx.h >= 10:
        rig.fur(ctx, (0, 1), length=5, density=0.12, tip=0.92, root=1.08)  # B17: dry, drawn sinew down the limb
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


@lit()
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

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): the balance it never quite had goes. A jolt, the left
    # knee gives and it lurches left, the right gives and it overcorrects, and it comes apart on the way down like
    # something badly put together: the knees folding a little sideways, the torso twisting off the hips, the head
    # lolling the wrong way. It pitches forward onto its chest, turned onto its right side, wobbles twice and lies
    # still: the long right arm flung out along the floor, the left bent up with the big hand by the head, the left
    # knee drawn up out to the side, the head laid on its right cheek last, a little too far over. The extension
    # segments stay inside the forearms. With the body face down, -X on the pelvis rolls it onto its right side.
    # (The held limbs were placed with a small solver against floor contact and hand/knee targets.)
    die_names = [p.name for p in m.parts]

    def hands(cl, cr):
        d = {f: pose((0, 0, cl - 9 * ((i * 3) % 4))) for i, f in enumerate(fingers_l[:4])}
        d.update({f: pose((0, 0, cr - 8 * ((i * 5) % 3))) for i, f in enumerate(fingers_r[:4])})
        d["ThumbL"], d["ThumbR"] = pose((-10, 0, cl * 0.5)), pose((8, 0, cr * 0.5))
        return d

    def prone(roll, slack, wob=0.0, head_k=1.0, **limbs):
        """Face down, rolled `roll` degrees onto its right side, from the way it landed (slack 0) to the way it rests
        (slack 1); `wob` bends the loose torso and neck for the wobble, head_k turns the head onto its cheek."""
        def at(a, b):
            return tuple(a[i] + (b[i] - a[i]) * slack for i in range(3))
        return dict({
            "Pelvis": pose((roll, -1, 90)), "Torso": pose((-1 + 4 * wob, -10 + 6 * wob, -6 - 4 * wob)),
            "Neck": pose((-1 - 6 * wob, 11 * head_k, -7 + 3 * wob)), "Head": pose((-15 * head_k, 55 * head_k, 0)), "Jaw": pose((0, 0, 6 * slack)),
            "ArmL": pose(at((20, 50, -95), (25, 56, -104))), "ForearmL": pose(at((-30, 0, -95), (-40, 0, -111))), "HandL": pose(at((0, 0, 5), (-5, 0, -3))),
            "ArmR": pose(at((120, 10, 24), (128, 12, 28))), "ForearmR": pose(at((15, 0, -10), (23, 0, -5))), "HandR": pose(at((0, 0, 10), (2, 0, 15))),
            "ThighL": pose(at((-26, 34, -30), (6, 53, -71))), "ShinL": pose(at((16, 0, 24), (3, 0, 90))), "FootL": pose(at((-3, 10, 4), (6, 14, 3))),
            "ThighR": pose(at((1, -20, -4), (1, -27, 2))), "ShinR": pose(at((-2, 0, 10), (-4, 0, 10))), "FootR": pose(at((-1, -4, 0), (-1, -4, -10))),
        }, **hands(-30 - 6 * slack, -20 - 8 * slack), **{k: pose(v) for k, v in limbs.items()})

    def between(a, b, t=0.5):
        """A pose partway from a to b, joint by joint; as a keyframe of its own it is settled onto the floor, so a
        planted foot or knee does not dip through it on the way."""
        return {n: pose(tuple(x + (y - x) * t for x, y in zip(a.get(n, pose())["rot"], b.get(n, pose())["rot"]))) for n in set(a) | set(b)}

    # the left knee gives, it lurches left; the torso wobbles back the other way
    lurch = dict({"Pelvis": pose((10, 4, 4)), "Torso": pose((-14, -6, 6)), "Neck": pose((-10, 4, 4)), "Head": pose((-6, 0, 2)),
                  "ThighL": pose((-4, 0, -32)), "ShinL": pose((-8, 0, 64)), "FootL": pose((0, 0, -28)),
                  "ThighR": pose((-10, 0, 2)), "ShinR": pose((0, 0, 4)), "FootR": pose((10, 0, -4)),
                  "ArmL": pose((-6, 0, 4)), "ArmR": pose((-14, 0, -6))}, **hands(4, 2))
    # the right knee goes too and it overcorrects to the right, folding forward, the left knee caving inward
    buckle = dict({"Pelvis": pose((-10, -6, 14)), "Torso": pose((-12, 10, 20)), "ShoulderR": pose((-6, 0, 0)), "Neck": pose((-14, -8, 16)), "Head": pose((-8, 0, 8)),
                   "ThighL": pose((10, 0, -62)), "ShinL": pose((-14, 0, 96)), "FootL": pose((0, 0, -30)),
                   "ThighR": pose((-6, 0, -44)), "ShinR": pose((4, 0, 80)), "FootR": pose((0, 0, -30)),
                   "ArmL": pose((-22, 0, -34)), "ArmR": pose((86, 0, -24)), "ForearmL": pose((0, 0, -22)), "ForearmR": pose((0, 0, -16))}, **hands(-4, -8))
    # down on its knees, pitching forward off the hips: the left hand hits the floor and the elbow buckles, the right
    # arm flung out to the side as it tips that way
    pitch = dict({"Pelvis": pose((-14, -4, 50)), "Torso": pose((-10, 8, 20)), "Neck": pose((-8, 0, 10)), "Head": pose((-6, 10, 6)),
                  "ThighL": pose((10, 0, -50)), "ShinL": pose((-12, 0, 92)), "FootL": pose((0, 0, -10)),
                  "ThighR": pose((-6, 0, -42)), "ShinR": pose((4, 0, 84)), "FootR": pose((0, 0, -6)),
                  "ArmL": pose((4, 4, -59)), "ForearmL": pose((2, 0, -53)), "HandL": pose((0, 0, -17)),
                  "ArmR": pose((127, 11, 23)), "ForearmR": pose((4, 0, -1)), "HandR": pose((0, 0, 5))}, **hands(-10, -6))
    # impact: down on its chest, rolled a little past onto its right side
    impact = prone(-38, 0.0, wob=0.6, head_k=0.4,
                   ArmR=(116, 19, 33), ForearmR=(23, 0, 5), HandR=(1, 0, 10),
                   ArmL=(3, 34, -82), ForearmL=(-40, 0, -99), HandL=(-25, 0, 30),
                   ThighL=(-18, 33, -43), ShinL=(21, 0, 42), FootL=(-3, 18, 4),
                   ThighR=(-3, -33, -1), ShinR=(-3, 0, 0), FootR=(-2, -6, 25))

    death(m, 40, die_names, {
        0: {},
        # the hit: it jerks upright, the head snaps back and sideways, the arms twitch out, the hands splay
        3: dict({"Torso": pose((0, 8, -6)), "Neck": pose((14, 0, -10)), "Head": pose((6, 0, -4)),
                 "ArmL": pose((-14, 0, -6)), "ArmR": pose((12, 0, 4))}, **hands(12, 10)),
        7: lurch,
        9: between(lurch, buckle),
        11: buckle,
        13: between(buckle, pitch, 0.4),
        16: pitch,
        17: between(pitch, impact, 0.3),
        20: impact,
        # the first wobble back, the loose torso bending under it
        24: prone(-24, 0.4, wob=-1.0, head_k=0.6,
                  ArmR=(133, 16, 14), ForearmR=(19, 0, 10), HandR=(0, 0, 13),
                  ArmL=(27, 74, -103), ForearmL=(-19, 0, -107), HandL=(-10, 0, -1),
                  ThighL=(11, 55, -74), ShinL=(2, 0, 84), FootL=(7, 15, 3),
                  ThighR=(-1, -24, -4), ShinR=(-4, 0, 8), FootR=(0, -1, -6)),
        # and over again, less
        28: prone(-33, 0.7, wob=0.5, head_k=0.85,
                  ArmR=(123, 18, 27), ForearmR=(25, 0, 4), HandR=(1, 0, 13),
                  ArmL=(14, 45, -94), ForearmL=(-47, 0, -110), HandL=(-9, 0, 2),
                  ThighL=(9, 52, -74), ShinL=(4, 0, 92), FootL=(5, 13, 3),
                  ThighR=(1, -29, 3), ShinR=(-3, 0, 2), FootR=(-1, -4, -7)),
        # settling: the limbs go slack, the head lies over last
        39: prone(-30, 1.0),
    }, standing=(3,))
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
        if ctx.baked and ctx.face in ("north", "south", "up"):
            rig.folds(ctx, (0.3, 0.62), depth=0.84, light=1.08, axis="v")     # B17: wrinkles as folds across the body
        else:
            hlines(ctx, v["streak"], 3, start=1, alpha=0.4)                 # wrinkles
        blotch(ctx, v["belly"], 1, 2, 4, 0.3)
        return
    fill(ctx, v["fur"], 0.14)
    if ctx.baked:   # B17: the coat combed nose to tail (+x) in short strokes, dark roots and lit tips, the belly paler
        if ctx.face == "down":
            fill(ctx, v["belly"], 0.1)
        blotch(ctx, v["streak"], 2, 1.5, 3.5, 0.3)
        way = {"north": (-1, 0.3), "south": (1, 0.3), "up": (1, 0), "down": (1, 0), "west": (0, 1), "east": (0, 1)}[ctx.face]
        rig.fur(ctx, way, length=5, density=1.1, tip=1.32, root=0.8)
        return
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


@lit(reach=(0.4, 0.9, 1.6), ground_h=3.0, round_px=3.0)
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

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): a squeal and a jerk, the front legs buckle and the
    # chest drops onto them, the haunches give, it rolls onto its left side, rocks once and settles curled: the legs
    # folded with the paws drawn in toward the belly (the right legs, on top, fallen across the left), the back
    # curved, the tail limp in a curve along the floor, the head laid down last with the mouth hanging open. On its
    # left side the floor is +Z in the body's frame: a limb falls onto it with -X rotation, the tail and neck reach it
    # with Y rotation (-Y for the tail, +Y for the neck), and a curl (Z rotation) lies flat along the floor.
    die_names = ["Body", "Rump", "Neck", "Head", "Snout", "Jaw", "EarL", "EarR", "LegFrontL", "LegFrontR", "LegHindL", "LegHindR",
                 "PawFrontL", "PawFrontR", "FootHindL", "FootHindR"] + [f"Tail{i}" for i in range(len(TAIL))]

    def limp_tail(k, curl=1.0, flick=0.0):
        """The tail fallen to the floor (k 0..1) in a lazy curve along it; its rest droop (Z) lies flat once on the side."""
        return {f"Tail{i}": pose((0, k * (-22, -12, 10, 10, 0, -4)[i] + flick * (i / 5), curl * (8, -6, -8, -6, -4, 0)[i])) for i in range(len(TAIL))}

    def curled(roll, slack, jaw):
        """On its left side (`roll` degrees about the spine), from the fold it fell in (slack 0) to the pose it rests in
        (slack 1): the back curved, the front legs folded up under the chin, the hind legs drawn up to the belly."""
        def at(a, b):
            return tuple(a[i] + (b[i] - a[i]) * slack for i in range(3))
        return {
            "Body": pose((roll, 0, at((4, 0, 0), (6, 0, 0))[0])), "Rump": pose(at((0, 0, -14), (2, -4, -26))),
            "Neck": pose(at((0, 6, 14), (0, 8, 24))), "Head": pose(at((4, 4, 8), (10, 6, 16))), "Snout": pose(at((0, 0, 2), (0, 0, 4))),
            "Jaw": pose((0, 0, jaw)), "EarL": pose((0, 0, 14)), "EarR": pose((-10, 0, 18)),
            "LegFrontL": pose(at((6, 0, -40), (8, 0, -52))), "PawFrontL": pose(at((0, 0, 60), (0, 0, 74))),
            "LegFrontR": pose(at((-20, 0, -44), (-46, 0, -36))), "PawFrontR": pose(at((0, 0, 54), (-8, 0, 82))),
            "LegHindL": pose(at((4, 0, -40), (6, 0, -34))), "FootHindL": pose(at((0, 0, 40), (0, 0, 50))),
            "LegHindR": pose(at((-20, 0, -44), (-44, 0, -24))), "FootHindR": pose(at((0, 0, 36), (-6, 0, 58))),
        }

    death(m, 36, die_names, {
        0: tail(0),
        # the hit: a jerk, the head snaps up, the mouth opens, the tail whips
        3: dict({"Body": pose((4, 6, -6)), "Neck": pose((0, 6, -10)), "Head": pose((0, 10, -6)), "Jaw": pose((0, 0, 30)),
                 "EarL": pose((0, 0, 20)), "EarR": pose((0, 0, 20)), "LegFrontL": pose((0, 0, -6)), "LegFrontR": pose((0, 0, -4))},
                **tail(0.1, sweep=10, lift=14)),
        # the front legs buckle: the chest drops onto the folding forelegs, the hips still up
        7: dict({"Body": pose((8, 4, 14)), "Rump": pose((0, 0, -8)), "Neck": pose((0, 4, 4)), "Head": pose((2, 6, 0)), "Jaw": pose((0, 0, 24)),
                 "LegFrontL": pose((-6, 0, -50)), "LegFrontR": pose((8, 0, -44)), "PawFrontL": pose((0, 0, 70)), "PawFrontR": pose((0, 0, 64)),
                 "LegHindL": pose((0, 0, -6)), "LegHindR": pose((0, 0, -4))}, **tail(0.2, sweep=6, lift=6)),
        10: dict({"Body": pose((22, 3, 12)), "Rump": pose((0, 0, -8)), "Neck": pose((0, 5, 6)), "Head": pose((2, 6, 2)), "Jaw": pose((0, 0, 23)),
                  "LegFrontL": pose((-3, 0, -48)), "LegFrontR": pose((0, 0, -42)), "PawFrontL": pose((0, 0, 68)), "PawFrontR": pose((0, 0, 62)),
                  "LegHindL": pose((2, 0, -18)), "LegHindR": pose((-3, 0, -18)), "FootHindL": pose((0, 0, 14)), "FootHindR": pose((0, 0, 14))},
                 **tail(0.25, sweep=4, lift=2)),
        # the haunches give and it tips over onto its left side, falling fast
        12: dict({"Body": pose((40, 2, 8)), "Rump": pose((0, 0, -8)), "Neck": pose((0, 6, 8)), "Head": pose((2, 6, 4)), "Jaw": pose((0, 0, 22)),
                  "LegFrontL": pose((0, 0, -44)), "LegFrontR": pose((-6, 0, -40)), "PawFrontL": pose((0, 0, 64)), "PawFrontR": pose((0, 0, 60)),
                  "LegHindL": pose((4, 0, -30)), "LegHindR": pose((-6, 0, -34)), "FootHindL": pose((0, 0, 30)), "FootHindR": pose((0, 0, 30))},
                 **limp_tail(0.3, curl=0.3)),
        15: dict(curled(78, 0.0, jaw=21), **limp_tail(0.6, curl=0.5, flick=16)),
        # down, a little past; the legs still folded from the fall
        17: dict(curled(104, 0.0, jaw=20), **limp_tail(0.9, curl=0.6, flick=10)),
        # rocks back once, the top legs dropping across the lower ones
        22: dict(curled(90, 0.6, jaw=30), **limp_tail(0.8, curl=0.9, flick=14)),
        # settling: the legs go slack, the head sinks to the floor, a last twitch of the tail
        28: dict(curled(97, 0.9, jaw=26), **limp_tail(1.0, curl=1.0, flick=4)),
        35: dict(curled(96, 1.0, jaw=28), **limp_tail(1.0, curl=1.0)),
    }, soft=[f"Whisker{sd}{i}" for sd in "LR" for i in range(3)])
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
    if ctx.baked:
        rig.fur(ctx, (0, 1) if ctx.face not in ("up", "down") else (1, 0), length=2, density=0.5, tip=1.2, root=0.8)


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
        if ctx.baked:
            rig.plates(ctx, max(1, ctx.w // 3), axis="u", seam=0.8, lit=1.12, reverse=ctx.face == "north")  # B17
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


@lit(reach=(0.3, 0.6, 1.0), ground=0.08, ground_h=2.0, round_px=2.0)
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

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): a last spasm of the wings, which close together over
    # the back and stop; the legs give and it comes down (the entity itself falls under physics, so the model stays
    # at its feet's level), topples onto its left side, the closed wings slapping down onto the floor, bounces once and
    # settles: the wings laid together along the floor like a shut book, the legs curled in toward the belly, as a dead
    # moth's do, the head bowed, the antennae limp. Closed over the back, the left wing's rotX is -90 and the right's
    # +90; on its left side the floor is +Z in the body's frame, so adding to both lays them down toward it.
    mouth = ["MandibleL", "MandibleR"] if female else ["Proboscis0", "Proboscis1", "Proboscis2"]
    die_names = (["Thorax", "Head", "Abdomen1", "Abdomen2", "AbdomenTip", "AntennaL", "AntennaR"] + wing_names + mouth
                 + [f"{p}{i}{sd}" for p in ("Leg", "Shin", "Tarsus") for i in range(3) for sd in "LR"])

    def curl(k, twitch=0.0):
        """The legs drawn in by k (0..1; +X folds a left leg in under the belly, -X a right one): the femurs bunched
        toward the middle, the shins and claws hooked in; each a little different, and `twitch` stirs the middle right
        one."""
        d = {}
        for i in range(3):
            for sd, sgn in (("L", 1), ("R", -1)):
                j = i + (0 if sd == "L" else 1)
                d[f"Leg{i}{sd}"] = pose((sgn * k * (8 + 6 * (j % 3)), 0, k * (16, -4, -18)[i] + (twitch if (i, sd) == (1, "R") else 0)))
                d[f"Shin{i}{sd}"] = pose((sgn * k * (30 + 8 * ((j + 1) % 3)), 0, k * (-10, 6, 12)[i]))
                d[f"Tarsus{i}{sd}"] = pose((sgn * k * (40 + 10 * (j % 2)), 0, 0))
        return d

    def mouthparts(k):
        if female:
            return {"MandibleL": pose((0, -18 * k, 0)), "MandibleR": pose((0, 12 * k, 0))}
        return {"Proboscis0": pose((0, 0, -20 * k)), "Proboscis1": pose((0, 0, -30 * k)), "Proboscis2": pose((0, 0, -20 * k))}

    def shut(lay, back=0.0, lay_r=None):
        """The wings closed together over the back, laid over toward the floor (+Z in the body's frame) by `lay` (the
        right wing, on top once it lies on its side, by `lay_r`, so it rests on the left one)."""
        lay_r = lay if lay_r is None else lay_r
        return {"ForewingL": pose((-90 + lay, -back, 0)), "ForewingR": pose((90 + lay_r, back, 0)),
                "HindwingL": pose((-88 + lay, -back * 0.85, 0)), "HindwingR": pose((88 + lay_r, back * 0.85, 0))}

    def dead(roll, k, lay, lay_r, twitch=0.0):
        """On its left side (`roll` degrees about the body's axis): the wings laid along the floor, the abdomen a
        little curled, the head bowed, the legs curled by k."""
        return dict({
            "Thorax": pose((roll, 0, 3)), "Head": pose((0, 6 * k, 14 * k)),
            "Abdomen1": pose((0, 4 * k, -4 * k)), "Abdomen2": pose((0, 6 * k, 6 * k)), "AbdomenTip": pose((0, 4 * k, 8 * k)),
            "AntennaL": pose((-60 * k, -20 * k, 10 * k)), "AntennaR": pose((14 * k, -4 * k, 26 * k)),
        }, **shut(lay, back=8 * k, lay_r=lay_r), **curl(k, twitch), **mouthparts(k))

    bounce = rig.settle(m, full(die_names, dead(87, 0.75, -6, 4)), 0.6)   # off the floor: kept as it is
    death(m, 34, die_names, {
        0: {},
        # the hit: the wings snap up, the abdomen jerks under, the legs splay
        3: dict({"Thorax": pose((0, 0, -6)), "Abdomen1": pose((0, 0, -14)), "Abdomen2": pose((0, 0, -10)), "AbdomenTip": pose((0, 0, -8)),
                 "Head": pose((0, 0, -8))}, **wings(-66, -60), **curl(-0.3), **mouthparts(1.0)),
        # the wings close over the back and stop; the legs give, the body comes down and starts to tip to its left
        6: dict({"Thorax": pose((12, 0, 2)), "Abdomen1": pose((0, 0, -8)), "Abdomen2": pose((0, 0, -6)), "Head": pose((0, 0, 4))},
                **shut(0), **curl(0.3), **mouthparts(1.0)),
        10: dict({"Thorax": pose((58, 0, 3)), "Abdomen1": pose((0, 2, -6)), "Abdomen2": pose((0, 2, -2)), "Head": pose((0, 3, 8))},
                 **shut(-4), **curl(0.5), **mouthparts(1.0)),
        12: dict({"Thorax": pose((78, 0, 3)), "Abdomen1": pose((0, 2, -4)), "Abdomen2": pose((0, 3, 0)), "Head": pose((0, 4, 10))},
                 **shut(0), **curl(0.55), **mouthparts(1.0)),
        # down on its side, the wings slapping onto the floor
        13: dead(90, 0.6, 0, 9),
        # a small bounce off the floor, the wings lifting with it
        16: bounce,
        # down again, the wings slapping down a little past and settling along the floor
        19: dead(92, 0.85, 3, 16),
        25: dead(88, 0.95, 1, 11, twitch=18),
        33: dead(90, 1.0, 2, 13),
    }, standing=(3,), airborne=(16,))
    return m


# ======================================================================== Smiler
# Entity 3. "A long smile with multiple sharp teeth, and white glowing eyes"; "reflective eyes and teeth gleaming in the
# dark"; whatever else it is "cannot be seen with the human eye", though some report "non-human, alien-like bodies,
# with arms and legs bent in unnatural ways" (Wikidot). The Fandom canon calls it amorphous: a face organ (the
# Ardenti risu, the "burning smile") over a body of Nigrum ignem, "black fire", an unidentified spectral substance.
# Design brief: in the dark it is only a grin and two eyes floating where a head should be; the grin is the identity.
# So the face is all that glows, and it is built to read from any angle: 33 separate teeth on a crescent that runs
# ear to ear, twice as wide as the skull, its ends curling up level with the eyes, the rows interlocking; behind them
# a second row that shows only when the jaw drops. The eyes are narrow white almonds, slanted down to the nose, no
# pupils. Everything else is near-black with a cold violet sheen, so in torchlight (which it never enters) or close up
# you see what holds the face up: a skull like a hood with black flame licking off the back, a long neck craned
# forward, a waist too thin to hold anything, high bony shoulders, arms that hang to the ankles with the elbows bent
# backwards, hands of three long fingers, legs whose knees bend the wrong way and end on points, and from the hips
# down the body comes apart into tatters of black smoke. It glides: the legs trail, the face stays level as if on
# rails. About 31 px tall (1.95 blocks), the grin 9.6 px wide at 27-29 px.

SM_BLACK = (13, 11, 16)        # the body: near-black with a cold violet cast
SM_SHEEN = (34, 30, 44)        # ... the oily sheen where light catches it
SM_DEEP = (4, 3, 6)            # eye sockets, the throat, the deepest folds
SM_SMOKE = (17, 15, 21)        # the tatters, a hair lighter so they part from the body in light
SM_MAW = (30, 6, 12)           # the inside of the mouth, wet and dark red (only in light)
SM_TOOTH = (238, 234, 218)     # the teeth: ivory at the root ...
SM_TIP = (255, 255, 250)       # ... white at the tip
SM_EYE = (255, 255, 252)
SM_EYE_RIM = (214, 226, 236)   # a cold edge to the eyes

GRIN_W = 4.8                   # the grin's half-width (px from the middle)


def sm_gum(z):
    """The upper gum line: a crescent rising from 27.55 in the middle to 29.2 at the ends (level with the eyes)."""
    return 27.55 + 0.072 * z * z


def sm_face_x(z):
    """How far back the grin sits: it wraps round the front of the head and on past its sides."""
    return -2.3 + 0.062 * z * z


def sm_upper_len(z):
    return 1.05 - 0.55 * (abs(z) / GRIN_W) ** 1.5


def sm_lower_len(z):
    return 0.95 - 0.5 * (abs(z) / GRIN_W) ** 1.5


def sm_lower_base(z):
    """The lower teeth's roots: as far below the gum as both rows are long, less the overlap where they interlock."""
    return sm_gum(z) - (sm_upper_len(z) + sm_lower_len(z) - 0.32)


def sm_dark(ctx, base=SM_BLACK, var=0.1):
    """Not skin: a matte black that drinks the light, with slow swirls of a cold sheen like oil on the surface."""
    fill(ctx, base, var)
    blotch(ctx, SM_SHEEN, 2, 1.0, 3.0, 0.35 if ctx.face == "up" else 0.22)
    blotch(ctx, SM_DEEP, 1, 1.0, 3.0, 0.5)
    speckle(ctx, mix(base, SM_SHEEN, 0.6), 0.03)


def sm_body(ctx):
    sm_dark(ctx)


def sm_chest(ctx):
    """A ribcage too narrow for lungs: ribs and a spine show as faint ridges under the black."""
    sm_dark(ctx)
    if ctx.face in ("north", "south", "west"):
        for v in (0.18, 0.34, 0.5, 0.66):
            line(ctx, 0.05, v, 0.95, v + 0.06, SM_SHEEN, 0.3)
            line(ctx, 0.05, v + 0.06, 0.95, v + 0.12, SM_DEEP, 0.45)
    if ctx.face == "west":
        line(ctx, 0.5, 0.0, 0.5, 0.8, SM_DEEP, 0.6)                          # the sternum's hollow
    elif ctx.face == "east":
        for v in (0.1, 0.3, 0.5, 0.7, 0.9):
            rect(ctx, 0.35, v, 0.65, v + 0.08, SM_SHEEN)                      # the knuckles of the spine


def sm_limb(ctx):
    """Long thin limbs: a sheen down the leading edge, a dark band at each end where they bend."""
    sm_dark(ctx)
    if ctx.face in ("north", "south", "west", "east"):
        texrow(ctx, 0, 0, -1, SM_DEEP, 0.7)
        texrow(ctx, -1, 0, -1, SM_DEEP, 0.7)
        if ctx.face == "west":
            line(ctx, 0.5, 0.1, 0.5, 0.9, SM_SHEEN, 0.4)


def sm_finger(ctx):
    """A finger as long as a hand, its last joint a dull grey claw."""
    sm_dark(ctx, SM_BLACK, 0.06)
    if ctx.face in ("north", "south", "west", "east"):
        texrow(ctx, ctx.h // 3, 0, -1, SM_DEEP, 0.7)                        # the knuckle
        for ty in range(ctx.h - 2, ctx.h):
            texrow(ctx, ty, 0, -1, (52, 48, 58))                             # the claw
        texrow(ctx, -1, 0, -1, (72, 68, 80))


def sm_skull(ctx):
    """The skull: a hood of black with deep sockets under a heavy brow where the eyes sit; nothing else on the face."""
    sm_dark(ctx, SM_BLACK, 0.06)
    if ctx.face == "west":
        w, h = ctx.w, ctx.h
        for ty in range(h // 3, h * 3 // 4):                                 # the sockets, wide and deep
            texrow(ctx, ty, 0, w // 2 - 2, SM_DEEP, 0.85)
            texrow(ctx, ty, w // 2 + 1, w - 1, SM_DEEP, 0.85)
        texrow(ctx, h // 3 - 1, 0, w - 1, SM_SHEEN, 0.5)                     # the brow ridge catching light
        for ty in range(h * 3 // 4, h):
            texrow(ctx, ty, 0, w - 1, SM_DEEP, 0.6)                          # the shadow over the grin
    elif ctx.face == "up":
        line(ctx, 0.2, 0.5, 1.0, 0.5, SM_SHEEN, 0.35)                         # a seam over the crown


def sm_throat(ctx):
    """The mouth's inside: wet, dark red going to black (in the dark, nothing at all)."""
    if ctx.face not in ("west", "up", "down"):
        fill(ctx, SM_DEEP, 0.1, face_shade=False)
        return
    fill(ctx, SM_MAW, 0.15, face_shade=False)
    blotch(ctx, SM_DEEP, 2, 1.0, 3.0, 0.7)
    if ctx.face == "west":
        speckle(ctx, mix(SM_MAW, (120, 50, 60), 0.5), 0.05)                  # wet


def sm_jaw(ctx):
    sm_dark(ctx, SM_BLACK, 0.06)
    if ctx.face == "up":
        fill(ctx, SM_MAW, 0.15, face_shade=False)                             # the floor of the mouth
        blotch(ctx, SM_DEEP, 1, 1.0, 2.5, 0.6)
    elif ctx.face == "west":
        texrow(ctx, 0, 0, -1, SM_DEEP)


def sm_cheek(ctx):
    """The face torn wide to hold the grin: a black web stretched out behind its ends, raw-dark along the seam."""
    sm_dark(ctx, SM_BLACK, 0.06)
    if ctx.face in ("west", "up", "down"):
        blotch(ctx, SM_MAW, 1, 1.0, 2.0, 0.3)
    if ctx.face in ("north", "south", "west", "east"):
        line(ctx, 0.0, 0.5, 1.0, 0.5, SM_DEEP, 0.6)                          # the stretch line


def sm_tooth(ctx):
    """A narrow tooth: ivory at the root, white at the tip (the tip is at the bottom of an upper tooth, the top of a
    lower one). It all glows, so in the dark the rows read as one jagged white crescent."""
    up = ctx.part.tag.get("upper", True)
    side = ctx.face in ("north", "south")
    fill(ctx, mix(SM_TOOTH, (150, 140, 120), 0.4) if side else SM_TOOTH, 0.03, face_shade=False)  # flanks a shade darker,
    if ctx.face in ("west", "east"):                                                              # so seen edge-on the teeth stay apart
        texrow(ctx, ctx.h - 1 if up else 0, 0, -1, SM_TIP)
        texrow(ctx, 0 if up else ctx.h - 1, 0, -1, mix(SM_TOOTH, (190, 180, 160), 0.6))
    elif ctx.face == ("down" if up else "up"):
        fill(ctx, SM_TIP, 0.0, face_shade=False)


def sm_eye(ctx):
    """A narrow slit of white light with no pupil; the rim a little colder."""
    fill(ctx, SM_EYE, 0.0, face_shade=False)
    if ctx.face in ("west", "up", "down", "north", "south", "east"):
        texrow(ctx, -1, 0, -1, SM_EYE_RIM, 0.6)
    if ctx.face == "west":
        # A plain slit of light: no pupil, no iris (corners cut to shape it read as pupils at a distance). The inner
        # end is a touch colder, so the slant reads toward the nose.
        inner = 0 if ctx.part.tag.get("side", "L") == "L" else ctx.w - 1
        texel(ctx, inner, 0, SM_EYE_RIM, 0.5)


def sm_smoke(ctx, top=False):
    """Black fire: a flat tatter of the body's substance, darker toward its end, the end cut ragged to nothing."""
    fill(ctx, SM_SMOKE, 0.12, face_shade=False)
    if ctx.face in ("north", "south", "west", "east"):
        px = ctx.img.load()
        for yy in range(ctx.h):
            t = yy / max(1, ctx.h - 1)
            t = 1 - t if top else t
            for xx in range(ctx.w):
                old = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = mix(old[:3], SM_DEEP, 0.6 * t) + (255,)
        vlines(ctx, SM_SHEEN, 3, start=ctx.rng.randint(0, 2), alpha=0.18, jitter=1)
        # The end burns away into tongues: cut deepest at the edges, unevenly, with holes burnt through above
        half = max(1.0, (ctx.w - 1) / 2)
        for xx in range(ctx.w):
            edge = abs(xx - half) / half if ctx.w > 2 else ctx.rng.random()
            cut = int(ctx.h * (0.08 + 0.4 * edge ** 1.5) + ctx.rng.uniform(0, ctx.h * 0.22))
            for k in range(min(ctx.h - 2, cut)):
                clear(ctx, xx, k if top else ctx.h - 1 - k)
            for k in range(cut, int(ctx.h * 0.7)):
                if ctx.rng.random() < 0.12 * (1 - k / ctx.h):
                    clear(ctx, xx, k if top else ctx.h - 1 - k)


def sm_flame(ctx):
    sm_smoke(ctx, top=True)


@lit(floor=26.0)
def smiler():
    m = Model("smiler", atlas_width=64, seed=3)

    # ---- The body: a thin black thing holding the face up ----
    # The torso chain leans forward 4 + 8 and the neck cranes 24 further; the head takes 32 back, so the face hangs in
    # front of the shoulders, tipped down a touch (looking up through its brow).
    hips = m.part("Hips", (-1.1, 12.4, -1.6), (2.2, 2.2, 3.2), pivot=(0, 13.5, 0), paint=sm_body)
    waist = m.part("Waist", (-0.6, 14.5, -0.8), (1.2, 3.3, 1.6), pivot=(0, 14.6, 0), parent=hips, rest=(0, 0, 6), paint=sm_limb)
    chest = m.part("Chest", (-1.15, 17.6, -1.8), (2.3, 5.4, 3.6), pivot=(0, 17.8, 0), parent=waist, rest=(0, 0, 12), paint=sm_chest)
    m.part("Collar", (-0.75, 22.4, -3.1), (1.5, 1.0, 6.2), pivot=(0, 22.9, 0), parent=chest, paint=sm_limb)
    neck = m.part("Neck", (-0.5, 22.6, -0.5), (1.0, 3.8, 1.0), pivot=(0, 22.8, 0), parent=chest, rest=(0, 0, 30), paint=sm_limb)
    head = m.part("Head", (-2.0, 27.3, -2.4), (4.0, 3.7, 4.8), pivot=(0, 26.4, 0), parent=neck, rest=(0, 0, -44), paint=sm_skull)
    m.part("Cranium", (0.8, 27.9, -1.9), (3.0, 3.0, 3.8), pivot=(1.2, 29.0, 0), parent=head, rest=(0, 0, -14), paint=sm_skull)
    m.part("Throat", (-1.15, 25.2, -2.2), (2.6, 2.2, 4.4), pivot=(0, 26.3, 0), parent=head, paint=sm_throat)
    jaw = m.part("Jaw", (-2.05, 24.5, -1.9), (3.4, 1.35, 3.8), pivot=(1.2, 25.6, 0), parent=head, paint=sm_jaw)
    m.part("Chin", (-1.9, 23.7, -1.0), (2.2, 0.9, 2.0), pivot=(-0.8, 24.5, 0), parent=jaw, rest=(0, 0, 6), paint=sm_jaw)

    # The eyes: narrow white almonds slanted down toward the nose (the left one at +z: its outer end up is -X rotation)
    m.part("EyeL", (-2.5, 29.2, 0.2), (0.35, 0.95, 2.4), pivot=(-2.3, 29.65, 1.4), parent=head, rest=(-19, 8, 0), paint=sm_eye,
           glow=255, tag={"side": "L"})

    # The cheeks: black webs stretched behind the grin's ends where it runs on past the sides of the skull
    zc = (2.25 + GRIN_W + 0.3) / 2
    m.part("CheekL", (sm_face_x(zc) + 0.25, sm_gum(zc) - 0.95, 2.1), (0.45, 1.25, 3.2), pivot=(sm_face_x(zc) + 0.45, sm_gum(zc) - 0.3, zc),
           parent=head, rest=(-math.degrees(math.atan(0.144 * zc)), math.degrees(math.atan(0.124 * zc)), 0), paint=sm_cheek)
    m.part("JawCheekL", (sm_face_x(zc) + 0.3, sm_lower_base(zc) - 0.55, 2.0), (0.45, 1.15, 3.2),
           pivot=(sm_face_x(zc) + 0.5, sm_lower_base(zc), zc), parent=jaw,
           rest=(-math.degrees(math.atan(0.16 * zc)), math.degrees(math.atan(0.124 * zc)), 0), paint=sm_cheek)
    m.mirror("EyeL", "EyeR")
    m.by_name["EyeR"].tag["side"] = "R"
    m.mirror("CheekL", "CheekR")
    m.mirror("JawCheekL", "JawCheekR")

    # ---- The grin ----
    # Every tooth its own cuboid, placed on the crescent, turned to stand square to its curve and to face out from the
    # arc round the head. The upper teeth hang from the gum line; the lower ones, set between them, rise from the jaw
    # (and open with it) so the rows interlock. The teeth shorten toward the ends; every fourth upper one is a fang.
    rng = random.Random(33)
    upper, lower, inner = [], [], []

    def tooth(name, z, root, length, width, parent, up, back=0.0, depth=0.42):
        x = sm_face_x(z) + back
        roll = -math.degrees(math.atan(0.144 * z))
        yaw = math.degrees(math.atan(0.124 * z))
        frm = (x, root - length, z - width / 2) if up else (x, root - 0.15, z - width / 2)
        m.part(name, frm, (depth, length + 0.15, width), pivot=(x + depth / 2, root, z), parent=parent, rest=(roll, yaw, 0),
               paint=sm_tooth, glow=255 if not back else 210, tag={"upper": up})

    for i in range(17):
        z = -GRIN_W + i * 0.6
        fang = i % 4 == 2 and abs(z) < 3.6
        length = sm_upper_len(z) + rng.uniform(-0.1, 0.1) + (0.32 if fang else 0)
        tooth(f"ToothU{i}", z, sm_gum(z), length, 0.5 if fang else 0.44, head, True)
        upper.append(f"ToothU{i}")
    for i in range(16):
        z = -GRIN_W + 0.3 + i * 0.6
        tooth(f"ToothD{i}", z, sm_lower_base(z), sm_lower_len(z) + rng.uniform(-0.1, 0.08), 0.44, jaw, False)
        lower.append(f"ToothD{i}")
    # The second rows, set back in the mouth and longer than the first: shut, each hides behind the opposite outer
    # row; open, they are a deeper set of needles hanging and rising in the dark of the throat
    for i in range(7):
        z = -1.8 + i * 0.6
        root = sm_gum(z) - 0.1
        tip = sm_lower_base(z) + 0.05
        tooth(f"InnerU{i}", z, root, (root - tip) * rng.uniform(0.85, 1.0), 0.36, head, True, back=0.55, depth=0.3)
        inner.append(f"InnerU{i}")
    for i in range(6):
        z = -1.5 + i * 0.6
        root = sm_lower_base(z) + 0.1
        tip = sm_gum(z) - 0.15
        tooth(f"InnerD{i}", z, root, (tip - root) * rng.uniform(0.75, 0.95), 0.36, jaw, False, back=0.55, depth=0.3)
        inner.append(f"InnerD{i}")

    # Black fire licking up off the back of the skull
    flames = []
    for i, (z, hgt, lean, spread) in enumerate(((-1.6, 3.2, -38, 14), (-0.55, 4.4, -48, 4), (0.55, 3.8, -44, -5), (1.6, 2.8, -34, -15))):
        m.part(f"Flame{i}", (1.4, 29.6, z - 0.15), (2.2, hgt, 0.3), pivot=(2.2, 29.8, z), parent="Cranium", rest=(spread, 0, lean), paint=sm_flame)
        flames.append(f"Flame{i}")

    # ---- Arms: hanging to the ankles, the upper arm forward and the elbow bent backwards ----
    arm = m.part("ArmL", (-0.45, 13.9, 2.6), (0.9, 9.4, 0.9), pivot=(0, 23.0, 3.05), parent=chest, rest=(-10, 0, -20), paint=sm_limb)
    fore = m.part("ForearmL", (-0.4, 4.2, 2.65), (0.8, 9.9, 0.8), pivot=(0, 14.0, 3.05), parent=arm, rest=(4, 0, 36), paint=sm_limb)
    hand = m.part("HandL", (-0.5, 2.6, 2.6), (1.0, 1.7, 0.9), pivot=(0, 4.3, 3.05), parent=fore, rest=(0, 0, -12), paint=sm_limb)
    for i in range(3):
        z = 2.62 + i * 0.3
        length = 3.7 if i == 1 else 3.2                                          # the middle finger longest
        m.part(f"Finger{i}L", (-0.42, 2.7 - length, z), (0.3, length, 0.26),
               pivot=(-0.27, 2.65, z + 0.13), parent=hand, rest=((i - 1) * -7, 0, -6 + i * 4), paint=sm_finger)
    # ---- Legs: knees bent backwards, the shins ending on points ----
    thigh = m.part("ThighL", (-0.5, 6.6, 0.5), (1.0, 7.4, 1.0), pivot=(0, 13.8, 1.0), parent=hips, rest=(-8, 0, 32), paint=sm_limb)
    shin = m.part("ShinL", (-0.4, 0.2, 0.6), (0.8, 6.8, 0.8), pivot=(0, 6.9, 1.0), parent=thigh, rest=(6, 0, -62), paint=sm_limb)
    m.part("FootL", (-0.3, -1.8, 0.68), (0.6, 2.4, 0.64), pivot=(0, 0.4, 1.0), parent=shin, rest=(0, 0, 34), paint=sm_finger)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    # Asymmetry: the right arm hangs a little further forward and its elbow bends further
    m.by_name["ArmR"].rest = (10, 0, -26)
    m.by_name["ForearmR"].rest = (-4, 0, 42)

    # ---- The body coming apart into smoke below the hips ----
    tatters = []
    for i, (frm, size, rest) in enumerate((
            ((0.8, 1.4, -1.4), (0.3, 12.2, 2.8), (0, 0, -12)),      # behind, nearly to the floor
            ((0.5, 3.0, -2.3), (0.3, 10.6, 1.8), (-16, 0, -10)),
            ((0.5, 2.4, 0.5), (0.3, 11.2, 1.8), (16, 0, -11)),
            ((-0.9, 5.0, 1.4), (2.2, 8.6, 0.3), (20, 0, -4)),       # at the sides, flaring out
            ((-0.9, 5.8, -1.7), (2.2, 7.8, 0.3), (-20, 0, -4)),
            ((-1.2, 7.4, -1.0), (0.3, 6.2, 2.0), (0, 0, 8)),        # a short one in front
            ((0.2, 6.6, 1.5), (1.4, 7.0, 0.3), (28, 0, -16)),       # wisps curling off the back corners
            ((0.2, 7.2, -1.8), (1.4, 6.4, 0.3), (-28, 0, -16)),
    )):
        pivot = (frm[0] + size[0] / 2, 13.6, frm[2] + size[2] / 2)
        m.part(f"Tatter{i}", frm, size, pivot=pivot, parent=hips, rest=rest, paint=sm_smoke)
        tatters.append(f"Tatter{i}")

    # ---- Animations ----
    # A hanging limb swings backward with +Z; an upright part leans forward with +Z; +X tilts toward the left (+z).
    # The jaw is hinged at the back: +Z drops it. The face is what is seen, so every animation keeps it steady: what
    # the body does, the head undoes.
    fingers = [f"Finger{i}{s_}" for i in range(3) for s_ in "LR"]

    def smoke(p, trail=0.0, amp=4.0):
        """The tatters and the flames flicker like slow black fire, and stream back as it moves."""
        d = {}
        for i, n in enumerate(tatters):
            d[n] = pose((s(p * 2, amp * 0.8, i * 0.17), 0, trail + s(p * 3, amp, i * 0.23)))
        for i, n in enumerate(flames):
            d[n] = pose((s(p * 3, amp, i * 0.29), 0, -trail * 0.6 + s(p * 2, amp * 1.2, i * 0.21)), s=(1, 1 + 0.12 * math.sin(TAU * (p * 3 + i * 0.3)), 1))
        return d

    # Idle, which is also what it does while it is stared at: nothing. It holds still and keeps smiling. The head
    # drifts into a slow tilt and jerks back once, a finger curls; the jaw parts a hair and closes. Only the black
    # fire never stops.
    def idle(p):
        tilt = ramp(p, 0.05, 0.5, 0.62, 0.63)                   # a slow lean over ... then a twitch back upright
        breath = math.sin(TAU * p)
        d = {
            "Hips": pose((0, 0, 0), (0, 0.15 * breath, 0)),
            "Chest": pose((0, 0, 0.8 * breath)),
            "Neck": pose((0, 0, -0.8 * breath)),
            "Head": pose((14 * tilt, 3 * tilt, 0), (0, -0.15 * breath, 0)),
            "Jaw": pose((0, 0, 3.5 * ramp(p, 0.68, 0.74, 0.8, 0.88))),
            "ArmL": pose((0, 0, s(p, 1.2))), "ArmR": pose((0, 0, -s(p, 1.0, 0.2))),
            "Finger0L": pose((0, 0, 0)), "Finger1L": pose((0, 0, -26 * ramp(p, 0.2, 0.3, 0.4, 0.5))),
            "Finger2L": pose((0, 0, -20 * ramp(p, 0.26, 0.36, 0.42, 0.52))),
            "Finger0R": pose((0, 0, -22 * ramp(p, 0.75, 0.82, 0.86, 0.95))), "Finger1R": pose((0, 0, 0)), "Finger2R": pose((0, 0, 0)),
        }
        d.update(smoke(p, 0, 4))
        return d

    m.animation("idle", 120, cycle(120, 24, idle))

    # Walk (also its run, at twice the speed): it glides. The body leans in and sways, the legs trail and drift
    # without stepping, toes dragging; the arms hang back and swing loose, late; the smoke streams behind. The head
    # cancels all of it: the grin comes toward you level and smooth.
    def glide(p):
        sway = s(p, 3.5)
        bob = 0.35 * math.sin(TAU * p * 2)
        d = {
            "Hips": pose((sway, s(p, 4, 0.1), 0), (0, bob, 0)),
            "Waist": pose((0, 0, 7)), "Chest": pose((-sway * 0.4, 0, 5)),
            "Neck": pose((0, 0, -2)),
            "Head": pose((-sway * 0.6, -s(p, 4, 0.1), -10), (0, -bob, 0)),
            "ThighL": pose((0, 0, 12 + s(p, 7))), "ThighR": pose((0, 0, 12 - s(p, 7))),
            "ShinL": pose((0, 0, 10 + s(p, 6, -0.12))), "ShinR": pose((0, 0, 10 - s(p, 6, -0.12))),
            "FootL": pose((0, 0, 14)), "FootR": pose((0, 0, 14)),
            "ArmL": pose((-sway * 0.5, 0, 12 + s(p, 6, -0.15))), "ArmR": pose((-sway * 0.5, 0, 12 - s(p, 6, -0.15))),
            "ForearmL": pose((0, 0, -22 + s(p, 5, -0.3))), "ForearmR": pose((0, 0, -26 - s(p, 5, -0.3))),     # hanging, the wrong bend let out
            "HandL": pose((0, 0, 8 + s(p, 6, -0.4))), "HandR": pose((0, 0, 8 - s(p, 6, -0.4))),
        }
        d.update(smoke(p, 22, 6))
        return d

    m.animation("walk", 40, cycle(40, 10, glide))

    # Attack (21 frames, 0.7 s; damageAtMs 300 lands on frame 9): the head draws back and the grin splits open,
    # far wider than a mouth, the second row behind; the arms come up and out; then the whole thing lunges, the arms
    # rake in, and the jaw slams shut on frame 9. It settles back as if nothing happened, still smiling.
    atk = ["Hips", "Waist", "Chest", "Neck", "Head", "Jaw", "ArmL", "ArmR", "ForearmL", "ForearmR", "HandL", "HandR"] + fingers + tatters + flames
    spread = {f: pose((0, 0, 24)) for f in fingers}
    clutch = {f: pose((0, 0, -40)) for f in fingers}
    m.animation("attack", 21, {
        0: full(atk, smoke(0, 0, 4)),
        4: full(atk, dict({"Waist": pose((0, 0, -6)), "Chest": pose((0, 0, -8)), "Neck": pose((0, 0, -12)), "Head": pose((0, 0, 4)),
                           "Jaw": pose((0, 0, 28)), "ArmL": pose((-30, 0, -20)), "ArmR": pose((30, 0, -24)),
                           "ForearmL": pose((0, 0, -20)), "ForearmR": pose((0, 0, -24)), "HandL": pose((0, 0, -10)), "HandR": pose((0, 0, -10))},
                          **spread, **smoke(0.1, -8, 6))),
        7: full(atk, dict({"Hips": pose((0, 0, 0), (-1.5, 0, 0)), "Waist": pose((0, 0, 10)), "Chest": pose((0, 0, 12)), "Neck": pose((0, 0, 10)),
                           "Head": pose((0, 0, -14)), "Jaw": pose((0, 0, 50)),
                           "ArmL": pose((-24, 0, -96)), "ArmR": pose((24, 0, -100)), "ForearmL": pose((0, 0, -30)), "ForearmR": pose((0, 0, -34)),
                           "HandL": pose((0, 0, -16)), "HandR": pose((0, 0, -16))}, **spread, **smoke(0.2, 26, 6))),
        9: full(atk, dict({"Hips": pose((0, 0, 0), (-2.5, 0, 0)), "Waist": pose((0, 0, 14)), "Chest": pose((0, 0, 16)), "Neck": pose((0, 0, 14)),
                           "Head": pose((0, 0, -22)), "Jaw": pose((0, 0, 2)),
                           "ArmL": pose((6, 0, -70)), "ArmR": pose((-6, 0, -74)), "ForearmL": pose((0, 0, -46)), "ForearmR": pose((0, 0, -50)),
                           "HandL": pose((0, 0, -20)), "HandR": pose((0, 0, -20))}, **clutch, **smoke(0.3, 30, 5))),
        13: full(atk, dict({"Hips": pose((0, 0, 0), (-2.0, 0, 0)), "Waist": pose((0, 0, 10)), "Chest": pose((0, 0, 12)), "Neck": pose((0, 0, 10)),
                            "Head": pose((0, 0, -16)), "Jaw": pose((0, 0, 6)),
                            "ArmL": pose((10, 0, -52)), "ArmR": pose((-10, 0, -56)), "ForearmL": pose((0, 0, -40)), "ForearmR": pose((0, 0, -42)),
                            "HandL": pose((0, 0, -14)), "HandR": pose((0, 0, -14))}, **clutch, **smoke(0.45, 18, 5))),
        20: full(atk, smoke(0.95, 0, 4)),
    }, end="Stop")

    # Hurt (not registered by default: it cannot be killed, struck it withdraws): the face jerks back and aside, the
    # grin snaps shut, and the black fire flares.
    hurt = ["Waist", "Chest", "Neck", "Head", "Jaw", "ArmL", "ArmR"] + tatters + flames
    m.animation("hurt", 14, {
        0: full(hurt, smoke(0, 0, 4)),
        3: full(hurt, dict({"Waist": pose((0, 0, -8)), "Chest": pose((6, 10, -10)), "Neck": pose((0, 0, -16)), "Head": pose((18, 14, 6)),
                            "Jaw": pose((0, 0, 0)), "ArmL": pose((-24, 0, 12)), "ArmR": pose((20, 0, 16))}, **smoke(0.2, -20, 12))),
        8: full(hurt, dict({"Waist": pose((0, 0, -3)), "Chest": pose((2, 4, -4)), "Neck": pose((0, 0, -6)), "Head": pose((6, 4, 2)),
                            "ArmL": pose((-8, 0, 4)), "ArmR": pose((8, 0, 6))}, **smoke(0.5, -6, 8))),
        13: full(hurt, smoke(0.9, 0, 4)),
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
        if ctx.baked and ctx.w >= 8:
            rig.folds(ctx, (0.1, 0.2), depth=0.8, light=1.08, axis="v")       # B17: skin bunched at the bend


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


@lit()
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
    limb_rest = {}
    for i, (yaw, (rx, ry, rz), kind, thick, la, lb, pitch, tone) in enumerate(LIMBS):
        a = math.radians(pitch)
        ey = ry - la * math.sin(a)
        sb = max(-1.0, min(1.0, (ey - 0.55) / lb))
        b = math.degrees(math.asin(sb)) - pitch                         # the extra pitch of the lower segment
        limb_rest[i] = (pitch, b)
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

    # Death: coordination goes. A supporting limb fails and the mass lurches; the limbs scrabble, then give, one after
    # another, and the mass sags onto the floor, stretched wide and low, the limbs spreading out flat from it, bent at
    # the joints, no two alike; the flaps hang open, the hands curl and one finger moves last.
    ends = [f"{'Hand' if LIMBS[i][2] in ('arm', 'thighhand', 'child') else 'Foot'}{i}" for i in range(len(LIMBS))]
    die_names = ["CoreA", "CaptureUpper", "CaptureFore", "CaptureWrist"] + limb_a + limb_b + ends + jaws + hand_fingers + cap_fingers

    # Where each limb lies when it has gone slack: (upper slope, lower slope) in degrees below horizontal; no two alike
    slack = {0: (22, 6), 1: (30, 2), 2: (12, 4), 3: (26, 16), 4: (36, 18), 5: (8, 2), 6: (28, 12), 7: (20, 3), 8: (10, 5), 9: (32, 14)}

    def sag(c, roll=(0, 0, 0), wide=(1.0, 1.0, 1.0), finger=24, jaw=20, hold=()):
        """c 0..1: how far the limbs have given (each lets go in its own time, flattening from its rest pitch)."""
        d = {"CoreA": pose(roll, s=wide), "CaptureUpper": pose((0, 6 * c, -8 * c)), "CaptureFore": pose((0, -6 * c, 0))}
        for i in range(len(LIMBS)):
            pitch, b = limb_rest[i]
            ci = min(1.0, max(0.0, c * 1.3 - (i * 0.06 + (0.1 if i in (1, 4, 6) else 0.0))))
            side = -1 if (LIMBS[i][0] % 360) < 180 else 1
            sprawl = [0.9, 1.0, 0.5, 1.1, 0.8, 0.6, 1.2, 0.9, 0.7, 0.4][i]
            if i in hold:
                d[f"Limb{i}A"] = pose((0, 0, -22))                                         # one still scrabbling at the floor
                d[f"Limb{i}B"] = pose((0, 0, 24))
                continue
            ta, tb = slack[i]                                                          # the slopes it settles to
            d[f"Limb{i}A"] = pose((0, side * 10 * ci * sprawl, (ta - pitch) * ci))
            d[f"Limb{i}B"] = pose((0, side * [-34, 62, -10, 40, -64, 12, 58, -22, 38, -16][i] * ci, (tb - ta - b) * ci))
            d[ends[i]] = pose((0, 0, ((pitch + b - tb) + [4, 8, 2, 10, 5, 3, 7, 1, 6, 9][i]) * ci))   # lies flat, a little curled
        for f in hand_fingers + cap_fingers:
            d[f] = pose((0, 0, finger - (30 if f == "CaptureHandF2" and c > 0.95 else 0)))
        d.update(jaw_open(jaw))
        return d

    death(m, 40, die_names, {
        0: {},
        3: sag(0.0, roll=(3, 0, -2), jaw=14, finger=10),                                      # the hit: it jerks, the mouth gapes
        8: sag(0.2, roll=(4, 1, 2), wide=(1.0, 0.95, 1.0), jaw=26, finger=12, hold=(1, 4)),   # a leg gives
        13: sag(0.45, roll=(7, 2, 4), wide=(1.04, 0.85, 1.04), jaw=34, finger=16, hold=(4,)),
        18: sag(0.7, roll=(9, 3, 5), wide=(1.1, 0.7, 1.1), jaw=30, finger=18),                # the mass drops
        22: sag(0.95, roll=(12, 3, 6), wide=(1.2, 0.58, 1.2), jaw=24, finger=22),             # impact, a little low
        27: sag(0.9, roll=(10, 3, -2), wide=(1.16, 0.62, 1.16), jaw=22, finger=24),            # rocks back
        33: sag(1.0, roll=(10, 3, -2), wide=(1.18, 0.6, 1.18), jaw=18, finger=26),
        39: sag(1.0, roll=(10, 3, -2), wide=(1.18, 0.6, 1.18), jaw=16, finger=28),
    }, standing=(3,))
    # The stretch the mass settles under is not counted by the settle, so it hovers a little at the end: press it down
    for f, k in m.animations[-1][2].items():
        if f >= 18:
            o = k["CoreA"]["off"]
            k["CoreA"]["off"] = (o[0], round(o[1] - min(1.4, 0.1 * (f - 15)), 3), o[2])
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
# Entity 63 (Wikidot, Spectre48 and Nikuchan; art by Poliacci). Rumoured to be "a spider-like creature roughly the size
# of a house, with a thick smokescreen masking its presence", a "sudden temperature decrease" before it is seen. What
# the witnesses actually see is a leg: "a massive tree ... the size of a giant redwood. Wait a minute. That isn't a
# tree - the bark is too black, and it has no branches or leaves"; on camera "a massive black pillar, reaching up far
# out of sight", which then lifts and is gone, "all that's left is a crater in the middle of the street"; its steps
# are thunder. Glimpsed once without the fog, its body is "Faces. Merging together into a singular mass - a brain for
# this unholy thing", and one face apart from the rest, screaming, calling out. It takes people with "a tendril" and
# lifts them "up into the sky"; its roar is human speech. Fandom's Entity 163 retelling keeps it: "several black limbs
# are walking ... the craters are just footprints", "a spider the size of a house? A giant tree?".
#
# Design brief, after the article's own drawing (Tournesol's sketch: thin jointed black trunks standing in a street,
# the body lost in cloud, a knot hanging beneath it trailing curled tendrils): a harvestman, not a tarantula. Eight
# legs rise steeply from a dark body to knees high above it, then drop almost straight to the street as long, knotted,
# near-black trunks that taper to points (the craters). In fog you see a stand of black trees that do not belong, a
# crown of knees, and something hanging. The body is a lumpy spider's back of black fibre with a sagging abdomen.
# Beneath its front hangs the brain: a knot of dark flesh studded with fourteen human faces (two more in the abdomen), modelled, not painted (brows,
# noses, cheekbones, lips, jaws that open and talk), turned every way, most asleep or moaning, some staring, one
# looking down at the street; and one apart from the rest on its own lobe, paler, screaming. Seven tendrils hang from
# the knot and curl outward at their ends; three are long capture tendrils ending in three hooked fingers.
# Charcoal-black, bark-fibred legs, dull mud at the points; the flesh black with a wet maroon cast and frost-grey
# where it faces up (the cold); the faces ashen, cold-toned, each a different person.
#
# Proportions (model px, drawn at size 1.5): knees at 118-122 (the top, 11.5 blocks drawn), the body 84-108, the face
# knot 51-76 (4.8-7.1 blocks drawn), the capture tendrils' tips 1-10 px off the street. The feet stand in an ellipse
# 59 px long by 54 wide (5 blocks wide drawn: a street is 8). Unique: there is The Mangled, not a Mangled.

MG_BLACK = (14, 12, 14)           # the legs: bark too black
MG_BARK = (24, 21, 22)
MG_RIDGE = (50, 43, 42)           # the lighter ridges of the fibre
MG_CRACK = (5, 4, 6)
MG_MUD = (58, 50, 42)             # the points, from the street
MG_FLESH = (30, 23, 25)           # the body and the knot
MG_FLESH_HI = (66, 48, 50)
MG_WET = (86, 30, 40)             # wet maroon where it is torn or folds
MG_FROST = (122, 126, 134)        # rime on whatever faces up (it brings the cold)
MG_SKIN = {"ash": (178, 166, 160), "cold": (156, 160, 170), "warm": (190, 160, 142), "sallow": (176, 166, 132),
           "grey": (146, 140, 138), "pale": (206, 198, 194)}
MG_LIP = (122, 86, 90)
MG_MOUTH = (34, 8, 12)
MG_THROAT = (12, 2, 4)
MG_TEETH = (206, 196, 172)
MG_EYE = (214, 208, 196)
MG_IRIS = {"brown": (70, 46, 32), "blue": (78, 98, 120), "grey": (96, 100, 104), "green": (74, 88, 60), "milk": (176, 180, 182)}


class MgModel(Model):
    """Packs each part's faces at its own texel density (tag "texel"; 1.0 = the usual 2 texels a pixel): the black
    flesh, bark and sinew are painted at 1 texel a pixel, like vanilla's creatures, so the faces can keep 2 and the
    atlas stays 256 x 512."""

    def _pack(self):
        rects = []
        for p in self.parts:
            k = p.tag.get("texel", 0.5 if p.paint in (mg_flesh, mg_bark, mg_knob, mg_tendril) else 1.0)
            for f in p.faces:
                w, h = p.face_size(f)
                pw, ph = max(1, math.ceil(w * rig.TEXEL * k - 1e-6)), max(1, math.ceil(h * rig.TEXEL * k - 1e-6))
                rects.append((ph, pw, p, f))
        rects.sort(key=lambda r: (-r[0], -r[1]))
        width = self.atlas_width * rig.TEXEL
        x = y = shelf = 0
        for ph, pw, p, f in rects:
            if x + pw + 1 > width:
                x, y, shelf = 0, y + shelf + 1, 0
            p.uv[f] = (x, y, pw, ph)
            x += pw + 1
            shelf = max(shelf, ph)
        height = y + shelf + 1
        h2 = 1
        while h2 < height:
            h2 *= 2
        return width, h2


def mg_side(ctx):
    return ctx.face in ("north", "south", "east", "west")


def mg_outer(ctx, xx):
    """For a limb built along -X: how far along it (0 at its root, the +X end; 1 at its -X end) a texel column lies."""
    u = (xx + 0.5) / ctx.w
    return u if ctx.face == "north" else 1 - u


def mg_bark(ctx):
    """The legs (boxes built along -X): near-black, the fibre running along the limb in ridges and deep cracks,
    knotted, a burnt red-brown under the black; muddier toward the point (tag "mud": (at the root, at the far end))."""
    t = ctx.part.tag
    fill(ctx, MG_BARK, 0.14)
    long = ctx.face in ("north", "south", "up", "down")
    if long:
        hlines(ctx, MG_BLACK, 2, start=ctx.rng.randint(0, 1), alpha=0.45)
        px = ctx.img.load()
        for yy in range(ctx.rng.randint(0, 2), ctx.h, 3):                                  # ridges, broken
            for xx in range(ctx.w):
                if ctx.rng.random() < 0.7:
                    texel(ctx, xx, yy, MG_RIDGE, 0.22)
        for _ in range(max(1, ctx.w * ctx.h // 60)):                                      # deep cracks along it
            x0, y0 = ctx.rng.randint(0, ctx.w - 1), ctx.rng.randint(0, ctx.h - 1)
            for xx in range(x0, min(ctx.w, x0 + ctx.rng.randint(3, 10))):
                texel(ctx, xx, y0, MG_CRACK, 0.9)
                y0 = max(0, min(ctx.h - 1, y0 + ctx.rng.choice((0, 0, 0, -1, 1))))
        for _ in range(max(0, ctx.w // 16)):                                              # knots: a ring of ridge round a pit
            cx, cy = ctx.rng.randint(1, max(1, ctx.w - 2)), ctx.rng.randint(1, max(1, ctx.h - 2))
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                texel(ctx, cx + dx, cy + dy, MG_RIDGE, 0.6)
            texel(ctx, cx, cy, MG_CRACK)
        mud = t.get("mud")
        if mud is not None:
            for xx in range(ctx.w):
                a = mud[0] + (mud[1] - mud[0]) * mg_outer(ctx, xx)
                if a > 0:
                    for yy in range(ctx.h):
                        texel(ctx, xx, yy, MG_MUD, min(0.8, a) * (0.6 + 0.4 * ctx.rng.random()))
    else:
        blotch(ctx, MG_CRACK, 1, 1, 2, 0.6)
    blotch(ctx, (60, 30, 26), max(1, ctx.w * ctx.h // 160), 1.5, 4, 0.2)


def mg_knob(ctx):
    """The swollen joints: the same black, ringed and puckered where the segments meet."""
    fill(ctx, MG_BARK, 0.16)
    blotch(ctx, MG_RIDGE, 1, 1, 2.5, 0.3)
    if mg_side(ctx):
        for yy in (0, ctx.h - 1):
            texrow(ctx, yy, 0, ctx.w - 1, MG_CRACK, 0.6)
        texrow(ctx, ctx.h // 2, 0, ctx.w - 1, MG_RIDGE, 0.35)
        blotch(ctx, MG_WET, 1, 1, 2.5, 0.35)


def mg_flesh(ctx):
    """The body and the knot: black fibre twisted every way, wet maroon in the folds, rime on the tops; on the big
    surfaces, the ghosts of more faces sunk in it (tag "ghosts")."""
    fill(ctx, MG_FLESH, 0.16)
    w, h = ctx.w, ctx.h
    for _ in range(max(2, w * h // 40)):                                                     # twisted fibre
        u, v = ctx.rng.random(), ctx.rng.random()
        ang = ctx.rng.uniform(-1.2, 1.2) + (math.pi / 2 if ctx.rng.random() < 0.5 else 0)
        ln = ctx.rng.uniform(2, 6)
        line(ctx, u, v, u + math.cos(ang) * ln / w, v + math.sin(ang) * ln / h, MG_FLESH_HI if ctx.rng.random() < 0.5 else MG_CRACK, 0.45)
    blotch(ctx, MG_WET, max(1, w * h // 120), 1.5, 4, 0.35)
    if ctx.face == "up":
        speckle(ctx, shade(MG_FROST, 0.75), 0.08)
        blotch(ctx, MG_FROST, max(1, w * h // 200), 2, 5, 0.18)
    elif ctx.face == "down":
        blotch(ctx, MG_WET, 2, 2, 5, 0.3)
    if ctx.part.tag.get("ghosts") and mg_side(ctx) and w >= 14 and h >= 12:
        for _ in range(max(1, w * h // 260)):                                                 # sunk faces, eyes shut
            fw, fh = ctx.rng.randint(7, 10), ctx.rng.randint(9, 12)
            x0, y0 = ctx.rng.randint(0, w - fw), ctx.rng.randint(0, h - fh)
            sunk = ctx.rng.uniform(0.55, 0.8)
            c = mix(MG_SKIN["grey"], MG_FLESH, sunk)
            for yy in range(fh):
                for xx in range(fw):
                    e = math.hypot((xx + 0.5 - fw / 2) / (fw / 2), (yy + 0.5 - fh / 2) / (fh / 2))
                    if e < 1:
                        texel(ctx, x0 + xx, y0 + yy, c, 0.9 * (1 - e * e) + 0.1)
            ey = y0 + int(fh * 0.42)
            for ex in (x0 + int(fw * 0.28), x0 + int(fw * 0.62)):
                texrow(ctx, ey, ex, ex + 1, MG_CRACK, 0.7)
            texrow(ctx, y0 + int(fh * 0.76), x0 + int(fw * 0.38), x0 + int(fw * 0.6), mix(MG_MOUTH, c, 0.3), 0.8)
            texel(ctx, x0 + fw // 2, y0 + int(fh * 0.6), shade(c, 0.7), 0.6)


def mg_tone(ctx):
    t = ctx.part.tag
    return mix(MG_SKIN[t.get("tone", "ash")], MG_SKIN["pale"], t.get("pale", 0.0))


def mg_skin(ctx, base=None, var=0.05):
    """Face skin, waxy, mottled; dark flesh creeping in at the edges, more on the faces that look inward."""
    base = base or mg_tone(ctx)
    fill(ctx, base, var)
    blotch(ctx, shade(base, 0.82), 1, 1.5, 3, 0.35)
    blotch(ctx, mix(base, (150, 120, 140), 0.5), 1, 1, 2.5, 0.2)                              # bruising
    if ctx.face == "up":
        speckle(ctx, MG_FROST, 0.1)


def mg_mask(ctx):
    """The face: skin over the front, the sockets, the shadow under the nose, cheek hollows, the mouth (shut: a dark
    line; open: dark red going black, its size from the part's "gap"), crow's feet and creases on the old ones; the
    edges sinking into the black flesh. The other sides are the flesh it is sunk in."""
    t = ctx.part.tag
    if ctx.face != "west":
        mg_flesh(ctx)
        return
    base = mg_tone(ctx)
    mg_skin(ctx, base)
    w, h = ctx.w, ctx.h
    px = ctx.img.load()
    H = t["h"]                                                     # the face's height in px without the dropped jaw
    k = h / (H + t["gap"])                                         # texels per px down the mask
    # Face-local "frac": +0.5 at the top of the face, -0.5 at its chin (before the jaw drops), in face heights
    def row(frac):
        return int(round((0.5 - frac) * H * k))
    # Eye sockets: a soft shadow round each eye
    for side in (-1, 1):
        cx = w / 2 + side * 0.22 * w
        cy = row(0.0) + 0.5
        for yy in range(h):
            for xx in range(w):
                d = math.hypot((xx + 0.5 - cx) / (0.2 * w), (yy + 0.5 - cy) / (0.16 * H * k))
                if d < 1:
                    old = px[ctx.x + xx, ctx.y + yy]
                    px[ctx.x + xx, ctx.y + yy] = mix(old[:3], shade(base, 0.45), 0.75 * (1 - d * d)) + (255,)
    # Cheek hollows and the nasolabial folds
    for side in (-1, 1):
        line(ctx, 0.5 + side * 0.16, 0.5 - (-0.16) * H * k / h, 0.5 + side * 0.26, 0.5 + 0.34 * H * k / h, shade(base, 0.62), 0.55)
        blotch_x, blotch_y = w / 2 + side * 0.36 * w, row(-0.18)
        for yy in range(max(0, blotch_y - 2), min(h, blotch_y + 3)):
            for xx in range(max(0, int(blotch_x) - 1), min(w, int(blotch_x) + 2)):
                texel(ctx, xx, yy, shade(base, 0.78), 0.4)
    # The mouth: the shadow under the upper lip and, when open, the cavity down to the dropped jaw
    gap = t["gap"]
    my0 = row(-0.36) - 1
    my1 = row(-0.36) + int(round((0.8 + gap) * k))
    mw = int(round(0.24 * w))
    for yy in range(max(0, my0), min(h, my1 + 1)):
        depth = (yy - my0) / max(1, my1 - my0)
        for xx in range(int(w / 2 - mw - (1 if gap > 1 else 0)), int(w / 2 + mw + (1 if gap > 1 else 0))):
            c = MG_THROAT if gap > 0.4 and 0.25 < depth < 0.85 and abs(xx + 0.5 - w / 2) < mw * 0.8 else MG_MOUTH
            texel(ctx, xx, yy, c if gap > 0.4 else shade(base, 0.4), 0.95)
    # Creases: the forehead, crow's feet on the old
    if t.get("age", 0) > 0.3:
        for frac in (0.4, 0.33):
            texrow(ctx, row(frac), int(w * 0.25), int(w * 0.75), shade(base, 0.78), 0.5)
        for side in (-1, 1):
            texel(ctx, int(w / 2 + side * 0.42 * w), row(0.03), shade(base, 0.7), 0.6)
            texel(ctx, int(w / 2 + side * 0.44 * w), row(-0.02), shade(base, 0.7), 0.5)
    # Tear tracks and wet streaks on the ones awake
    if t.get("eyes") != "shut":
        for side in (-1, 1):
            xx = int(w / 2 + side * 0.24 * w)
            for yy in range(row(-0.05), row(-0.3)):
                texel(ctx, xx, yy, shade(base, 0.72), 0.35)
    # Sinking into the flesh at the edges, raggedly; dark fibres reaching in across the skin
    for yy in range(h):
        for xx in range(w):
            e = min(xx, w - 1 - xx, yy, h - 1 - yy) + ctx.rng.uniform(-0.8, 0.8)
            sink = t.get("sink", 2.5)
            if e < sink:
                old = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = mix(old[:3], MG_FLESH, min(1.0, (sink - e) / sink) * 0.95) + (255,)
    for _ in range(t.get("veins", 2)):
        side = ctx.rng.choice(((0, ctx.rng.random()), (1, ctx.rng.random()), (ctx.rng.random(), 0), (ctx.rng.random(), 1)))
        u1, v1 = side[0] + (0.5 - side[0]) * ctx.rng.uniform(0.25, 0.45), side[1] + (0.5 - side[1]) * ctx.rng.uniform(0.25, 0.45)
        line(ctx, side[0], side[1], u1, v1, MG_CRACK, 0.6)


def mg_brow(ctx):
    base = mg_tone(ctx)
    mg_skin(ctx, base)
    if ctx.face == "west":                                       # the eyebrow
        hair = mix((40, 32, 30), base, ctx.part.tag.get("grey", 0.0))
        texrow(ctx, ctx.h - 1, 0, ctx.w - 1, hair, 0.8)
        texrow(ctx, ctx.h - 2, 1, ctx.w - 2, hair, 0.4)
    elif ctx.face == "down":
        fill(ctx, shade(base, 0.45), 0.05, face_shade=False)


def mg_nose(ctx):
    base = mg_tone(ctx)
    mg_skin(ctx, base, 0.04)
    if ctx.face == "down":                                       # nostrils
        fill(ctx, shade(base, 0.6), 0.05, face_shade=False)
        texel(ctx, ctx.w // 2, ctx.h // 2 - 1, MG_THROAT)
        texel(ctx, ctx.w // 2, -(ctx.h // 2), MG_THROAT)
    elif ctx.face in ("north", "south"):
        for yy in range(ctx.h):
            texel(ctx, ctx.w - 1, yy, shade(base, 0.7), 0.5)
    elif ctx.face == "west":
        texrow(ctx, ctx.h - 1, 0, ctx.w - 1, shade(base, 0.8), 0.6)
        texel(ctx, ctx.w // 2, 1, shade(base, 1.08), 0.5)


def mg_cheek(ctx):
    base = mg_tone(ctx)
    mg_skin(ctx, base, 0.04)
    if ctx.face == "down":
        fill(ctx, shade(base, 0.55), 0.05, face_shade=False)


def mg_lid(ctx):
    """A shut eye: the lid, bulging a little, the lashes a dark line along its foot."""
    base = mg_tone(ctx)
    mg_skin(ctx, shade(base, 0.92), 0.04)
    if ctx.face == "west":
        texrow(ctx, ctx.h - 1, 0, ctx.w - 1, (30, 22, 22), 0.9)
        texrow(ctx, 0, 0, ctx.w - 1, shade(base, 0.7), 0.5)


def mg_eye(ctx):
    """An open eye: a dull white, the iris and a pinprick pupil looking wherever the tag says, a wet glint; red at
    the corners; the lid's shadow along the top."""
    t = ctx.part.tag
    if ctx.face != "west":
        fill(ctx, shade(MG_EYE, 0.7), 0.05)
        return
    fill(ctx, MG_EYE, 0.04, face_shade=False)
    w, h = ctx.w, ctx.h
    texel(ctx, 0, h - 1, (170, 96, 96), 0.7)
    texel(ctx, w - 1, h - 1, (170, 96, 96), 0.7)
    iris = MG_IRIS[t.get("iris", "brown")]
    cx = w // 2 + t.get("look", 0)
    for xx in range(cx - 1, cx + 1):
        for yy in range(h):
            texel(ctx, xx, yy, iris)
    if t.get("iris") != "milk":
        texel(ctx, cx - 1 + (1 if t.get("look", 0) > 0 else 0), h // 2, (6, 4, 6))
    texel(ctx, cx - 1, 0, (250, 250, 246), 0.8)
    texrow(ctx, 0, 0, w - 1, (60, 44, 44), 0.45)


def mg_lip(ctx):
    base = mix(MG_LIP, mg_tone(ctx), 0.35)
    fill(ctx, base, 0.05)
    if ctx.face == "west" and ctx.part.tag.get("teeth"):
        texrow(ctx, ctx.h - 1, 1, ctx.w - 2, MG_TEETH)
        for xx in range(1, ctx.w - 1, 3):
            texel(ctx, xx, ctx.h - 1, shade(MG_TEETH, 0.7))
    if ctx.face == "down":
        fill(ctx, MG_TEETH if ctx.part.tag.get("teeth") else MG_MOUTH, 0.05, face_shade=False)


def mg_jaw(ctx):
    """The chin and lower lip; teeth along its top when the mouth is open; the throat on its top face."""
    t = ctx.part.tag
    base = mg_tone(ctx)
    if ctx.face == "up":
        fill(ctx, MG_MOUTH, 0.06, face_shade=False)
        if t.get("teeth"):
            texrow(ctx, 0, 0, ctx.w - 1, MG_TEETH, 0.9)
        return
    mg_skin(ctx, base)
    if ctx.face == "west":
        texrow(ctx, 0, 1, ctx.w - 2, mix(MG_LIP, base, 0.3), 0.85)
        texrow(ctx, 1, 2, ctx.w - 3, mix(MG_LIP, base, 0.55), 0.5)
        if t.get("teeth"):
            for xx in range(2, ctx.w - 2, 2):
                texel(ctx, xx, 0, MG_TEETH, 0.9)
        texrow(ctx, ctx.h - 1, 0, ctx.w - 1, shade(base, 0.7), 0.5)
        for xx in (0, ctx.w - 1):
            for yy in range(ctx.h):
                texel(ctx, xx, yy, MG_FLESH, 0.6)


def mg_tendril(ctx):
    """Black sinew, ridged across like a trachea, wet maroon underneath; a frostless grey at the hooked tips."""
    fill(ctx, (24, 19, 21), 0.12)
    if mg_side(ctx):
        hlines(ctx, MG_CRACK, 3, start=ctx.rng.randint(0, 2), alpha=0.5)
        vlines(ctx, (52, 36, 40), 3, start=1, alpha=0.25, jitter=1)
    blotch(ctx, MG_WET, 1, 1, 3, 0.3)
    if ctx.part.tag.get("tip"):
        for yy in range(ctx.h):
            a = (yy + 0.5) / ctx.h
            texrow(ctx, yy, 0, ctx.w - 1, (96, 86, 84), 0.55 * a)


# The legs, left side front to back, then the right (mirrored, a little different each): (yaw, root radius, femur
# length, femur angle (negative: up), tibia length, tibia angle, metatarsus angle (over 90: in under), thickness).
# Their order of stepping (one limb at a time, never two neighbours in a row) is MG_ORDER.
MG_LEGS = [
    (42, 10, 36, -50, 38, 68, 96, 4.4), (78, 9, 32, -56, 37, 79, 97, 4.1), (104, 9, 33, -54, 36, 80, 97, 4.2), (140, 10, 37, -48, 39, 70, 95, 4.6),
    (319, 10, 37, -49, 39, 68, 95, 4.2), (283, 9, 31, -58, 35, 79, 98, 4.4), (254, 9, 34, -53, 37, 81, 96, 3.9), (218, 11, 35, -50, 38, 71, 97, 5.0),
]
MG_ORDER = (0, 6, 1, 7, 2, 4, 3, 5)
TIB, META = 0.4, 0.3
MG_ROOT_Y = 93

# The faces of the knot: (yaw: 0 looks forward, 90 to its left; pitch: up; roll; width, height; eyes; mouth; tone;
# pale; age; iris; look; anguish (degrees the inner brows lift); how far it stands out of the knot)
MG_FACES = [
    (-34, -4, 6, 8, 10, "open", "scream", "pale", 0.5, 0.1, "blue", -1, 18, 3.5),     # apart from the others: screaming, calling out
    (6, 16, -6, 8, 10, "shut", "slack", "ash", 0.0, 0.6, "brown", 0, 6, 0.8),         # the big one in front, asleep and moaning
    (44, -4, 4, 7, 9, "open", "closed", "warm", 0.0, 0.2, "brown", 1, 0, 0.5),
    (92, 8, -6, 7, 8.5, "shut", "open", "cold", 0.0, 0.0, "grey", 0, 10, 0.4),
    (-84, 10, 8, 7, 9, "open", "open", "sallow", 0.0, 0.8, "green", -1, 12, 0.4),
    (8, -48, 0, 7, 8.5, "open", "slack", "grey", 0.1, 0.4, "milk", 0, 4, 0.6),        # looking down at the street
    (148, 12, 10, 6.5, 8, "shut", "closed", "ash", 0.0, 0.3, "grey", 0, 0, 0.3),
    (-142, -2, -10, 6.5, 8, "shut", "slack", "cold", 0.0, 0.9, "grey", 0, 8, 0.3),
    (-46, 44, 4, 6, 7.5, "shut", "closed", "warm", 0.0, 0.1, "brown", 0, 0, 0.2),    # sunk where the knot meets the stalk
    (-176, -36, 0, 6.5, 8, "open", "open", "sallow", 0.0, 0.5, "blue", 1, 14, 0.4),
    (58, 40, -12, 6, 7.5, "open", "closed", "grey", 0.2, 0.7, "grey", -1, 6, 0.3),
    (40, -38, 14, 6, 7.5, "shut", "slack", "warm", 0.1, 0.0, "brown", 0, 4, 0.3),     # a young one
    (118, -30, -8, 6, 7.5, "open", "scream", "cold", 0.0, 0.3, "blue", 0, 16, 0.3),
    (-112, -34, 6, 6, 7.5, "shut", "closed", "ash", 0.0, 0.5, "grey", 0, 0, 0.3),
]
# Two more, sunk in the back of the abdomen (the same fields), looking back and down at what follows it
MG_BODY_FACES = [
    (180, -18, 4, 7, 8.5, "open", "open", "ash", 0.1, 0.4, "brown", 0, 12, 0.3),
    (128, -46, -8, 6.5, 8, "shut", "slack", "cold", 0.0, 0.7, "grey", 0, 6, 0.3),
]
MG_ABD = ((16.0, 91.0, 0.0), (10.0, 8.5, 11.5))
MG_GAP = {"closed": 0.0, "slack": 0.7, "open": 1.4, "scream": 2.6}
MG_KNOT = (-5.0, 63.0, 0.0)
MG_KNOT_R = (12.0, 12.5, 12.0)

# Tendrils from the underside of the knot: (root x, z, segments, thickness, capture?)
MG_TENDRILS = [(-12, 0.5, 9, 3.0, True), (-3, 7.5, 9, 2.8, True), (-1, -8, 9, 2.8, True),
               (-9, -6, 6, 2.0, False), (-8, 6.5, 6, 1.9, False), (4, 3, 7, 2.2, False), (5, -3, 5, 1.8, False)]
MG_SEG = 5.3


@lit(reach=(1.0, 2.5, 5.0), ground_h=12.0, round_px=8.0, floor=30.0)
def mangled():
    m = MgModel("mangled", atlas_width=128, seed=63)
    rng = random.Random(6363)

    # ---- The body: a lumpy spider's back, a sagging abdomen behind ----
    body = m.part("Body", (-16, 86, -13), (30, 15, 26), pivot=(0, 93, 0), paint=mg_flesh, tag={"ghosts": True})
    m.part("Carapace", (-12, 98, -10), (22, 8, 20), pivot=(-1, 102, 0), parent=body, rest=(3, 6, -4), paint=mg_flesh, tag={"ghosts": True})
    m.part("Crest", (-6, 104, -5), (12, 4, 9), pivot=(0, 106, 0), parent=body, rest=(-6, -14, 5), paint=mg_flesh)
    abd = m.part("Abdomen", (6, 82, -12), (20, 18, 24), pivot=(8, 94, 0), parent=body, rest=(0, 0, 12), paint=mg_flesh, tag={"ghosts": True})
    m.part("AbdomenTip", (22, 80, -7), (9, 12, 14), pivot=(24, 88, 0), parent=abd, rest=(5, 8, 20), paint=mg_flesh)
    m.part("Brisket", (-20, 84, -9), (9, 12, 18), pivot=(-14, 92, 0), parent=body, rest=(-4, 0, 10), paint=mg_flesh)
    m.part("Belly", (-12, 82, -10), (20, 6, 20), pivot=(0, 86, 0), parent=body, rest=(0, 10, 0), paint=mg_flesh)

    # Lumps of black flesh heaped over the back and sides
    bc, be = (-1.0, 94.0, 0.0), (15.0, 9.0, 13.0)
    for q in range(22):
        yy = 1 - 2 * (q + 0.5) / 22
        if yy < -0.35:
            continue
        rad = math.sqrt(1 - yy * yy)
        th = q * math.pi * (3 - math.sqrt(5))
        c = (bc[0] + rad * math.cos(th) * (be[0] - 3), bc[1] + yy * (be[1] - 2), bc[2] + rad * math.sin(th) * (be[2] - 3))
        sz = rng.uniform(7, 11)
        m.part(f"Lump{q}", (c[0] - sz / 2, c[1] - sz * 0.35, c[2] - sz / 2), (sz, sz * rng.uniform(0.55, 0.85), sz * rng.uniform(0.8, 1.1)), pivot=c,
               parent=body, rest=(rng.uniform(-18, 18), rng.uniform(-45, 45), rng.uniform(-18, 18)), paint=mg_flesh, tag={"ghosts": q % 3 == 0})

    # ---- The legs ----
    legs = []
    for i, (yaw, r0, lf, af, lt, at, am, th) in enumerate(MG_LEGS):
        y0 = MG_ROOT_Y + (i % 3) - 1
        m.part(f"Hip{i}", (-r0 - 4, y0 - 3.5, -3.5), (7, 7, 7), pivot=(0, y0, 0), parent=body, rest=(0, yaw, 0), paint=mg_knob)
        # In the leg's own plane: u outward from the root, y up. Joint positions:
        ku, ky = r0 + lf * math.cos(math.radians(af)), y0 - lf * math.sin(math.radians(af))
        au, ay = ku + lt * math.cos(math.radians(at)), ky - lt * math.sin(math.radians(at))
        tip_len, spur_len = 7.0, 12.0
        # the metatarsus is as long as it must be for the point to reach the street
        lm = (ay - 0.5 - (spur_len + tip_len) * math.sin(math.radians(am + 4))) / math.sin(math.radians(am))
        femur = m.part(f"Femur{i}", (-r0 - lf, y0 - th * 0.45, -th * 0.45), (lf + 2, th * 0.9, th * 0.9), pivot=(-r0, y0, 0),
                       parent=f"Hip{i}", rest=(0, 0, af), paint=mg_bark, tag={"texel": 0.5})
        m.part(f"Knee{i}", (-r0 - lf - th * 0.7, y0 - th * 0.75, -th * 0.75), (th * 1.4, th * 1.5, th * 1.5), pivot=(-r0 - lf, y0, 0),
               parent=femur, rest=(0, 0, 20), paint=mg_knob)
        tib = m.part(f"Tibia{i}", (-r0 - lf - lt, y0 - th / 2, -th / 2), (lt + 1.5, th, th), pivot=(-r0 - lf, y0, 0), parent=femur,
                     rest=(0, 0, at - af), paint=mg_bark, tag={"texel": 0.5})
        x_a = -r0 - lf - lt
        m.part(f"Ankle{i}", (x_a - th * 0.6, y0 - th * 0.65, -th * 0.65), (th * 1.2, th * 1.3, th * 1.3), pivot=(x_a, y0, 0), parent=tib,
               rest=(0, 0, 35), paint=mg_knob)
        t2 = th * 0.85
        meta = m.part(f"Meta{i}", (x_a - lm, y0 - t2 / 2, -t2 / 2), (lm + 1.0, t2, t2), pivot=(x_a, y0, 0), parent=tib,
                      rest=(0, 0, am - at), paint=mg_bark, tag={"texel": 0.5, "mud": (-0.6, 0.1)})
        x_m = x_a - lm
        t3 = th * 0.6
        spur = m.part(f"Spur{i}", (x_m - spur_len, y0 - t3 / 2, -t3 / 2), (spur_len + 0.8, t3, t3), pivot=(x_m, y0, 0), parent=meta,
                      rest=(0, 0, 4), paint=mg_bark, tag={"texel": 0.5, "mud": (0.1, 0.6)})
        t4 = th * 0.32
        m.part(f"Tip{i}", (x_m - spur_len - tip_len, y0 - t4 / 2, -t4 / 2), (tip_len + 0.6, t4, t4), pivot=(x_m - spur_len, y0, 0), parent=spur,
               rest=(0, 0, 0), paint=mg_bark, tag={"texel": 0.5, "mud": (0.6, 1.0)})
        legs.append(i)

    # ---- The knot of faces, hanging under the front of the body ----
    stalk = m.part("Stalk", (-11.5, 71, -4.5), (9, 16, 9), pivot=(-7, 86, 0), parent=body, rest=(4, 0, -6), paint=mg_flesh)
    m.part("StalkSinew", (-9, 70, -6), (5, 15, 4), pivot=(-6.5, 85, -4), parent=stalk, rest=(-8, 20, 4), paint=mg_flesh)
    kx, ky, kz = MG_KNOT
    rx, ry, rz = MG_KNOT_R
    knot = m.part("Knot", (kx - rx + 3, ky - ry + 3, kz - rz + 3), (2 * rx - 6, 2 * ry - 6, 2 * rz - 6), pivot=(-7, 75, 0), parent=stalk,
                  paint=mg_flesh, tag={"ghosts": True})
    # Lobes of flesh bulging between the faces (wherever no face is), so the knot is no box
    face_dirs = []
    for (yaw, pitch, *_r) in MG_FACES:
        face_dirs.append((-math.cos(math.radians(pitch)) * math.cos(math.radians(yaw)), math.sin(math.radians(pitch)),
                          math.cos(math.radians(pitch)) * math.sin(math.radians(yaw))))
    lobes = 0
    for q in range(26):
        yy = 1 - 2 * (q + 0.5) / 26
        rad = math.sqrt(1 - yy * yy)
        th = q * math.pi * (3 - math.sqrt(5))
        d = (rad * math.cos(th), yy, rad * math.sin(th))
        if max(sum(d[k] * f[k] for k in range(3)) for f in face_dirs) > math.cos(math.radians(30)) or yy > 0.85:
            continue
        sz = rng.uniform(6, 9)
        c = (kx + d[0] * (rx - 3.5), ky + d[1] * (ry - 3.5), kz + d[2] * (rz - 3.5))
        m.part(f"KnotLobe{lobes}", (c[0] - sz / 2, c[1] - sz / 2, c[2] - sz / 2), (sz, sz * rng.uniform(0.8, 1.2), sz), pivot=c, parent=knot,
               rest=(rng.uniform(-25, 25), rng.uniform(-40, 40), rng.uniform(-25, 25)), paint=mg_flesh)
        lobes += 1

    face_names, jaw_names = [], []
    hosts = [(spec, knot, MG_KNOT, MG_KNOT_R) for spec in MG_FACES] + [(spec, abd, *MG_ABD) for spec in MG_BODY_FACES]
    for i, ((yaw, pitch, roll, fw, fh, eyes, mouth, tone, pale, age, iris, look, anguish, stand), host, (kx, ky, kz), (rx, ry, rz)) in enumerate(hosts):
        # Where its direction meets the ellipsoid of its host
        dx = -math.cos(math.radians(pitch)) * math.cos(math.radians(yaw))
        dz = math.cos(math.radians(pitch)) * math.sin(math.radians(yaw))
        dy = math.sin(math.radians(pitch))
        rr = 1 / math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2)
        c = (kx + dx * (rr - 1.5 + stand), ky + dy * (rr - 1.5 + stand), kz + dz * (rr - 1.5 + stand))
        gap = MG_GAP[mouth]
        tag = {"tone": tone, "pale": pale, "age": age, "eyes": eyes, "h": fh, "gap": gap, "sink": 2.5 if stand < 1 else 1.6, "veins": 2 if stand < 1 else 1}
        parent = host
        if stand > 1:                                   # the one apart: on a lobe of its own, pushed out of the mass
            parent = m.part(f"Lobe{i}", (c[0] + 0.5, c[1] - fh * 0.45, c[2] - fw * 0.45), (stand + 3, fh * 0.9, fw * 0.9), pivot=(c[0] + 1.5, c[1], c[2]),
                            parent=host, rest=(roll, yaw, -pitch), paint=mg_flesh)
        fx, cy, cz = c[0] - 1.5, c[1], c[2]
        mask = m.part(f"Face{i}", (fx, cy - fh / 2 - gap, cz - fw / 2), (3, fh + gap, fw), pivot=(c[0], cy, cz), parent=parent,
                      rest=(0, 0, 0) if stand > 1 else (roll, yaw, -pitch), paint=mg_mask, glow=18, tag=tag,
                      faces=("north", "south", "west", "up", "down"))
        face_names.append(mask.name)
        sk = dict(tone=tone, pale=pale)
        # Brows, in two halves, the inner ends lifting in anguish
        for side, nm in ((-1, "a"), (1, "b")):
            zc = cz + side * fw * 0.22
            m.part(f"Brow{i}{nm}", (fx - 0.9, cy + fh * 0.1, zc - fw * 0.22), (1.1, 1.1, fw * 0.44), pivot=(fx - 0.3, cy + fh * 0.1 + 0.5, zc),
                   parent=mask, rest=(side * anguish, 0, 0), paint=mg_brow, glow=18, tag=dict(sk, grey=age))
        # Eyes
        for side, nm in ((-1, "a"), (1, "b")):
            ze = cz + side * fw * 0.22
            ye = cy - fh * 0.02
            if eyes == "open":
                m.part(f"Eye{i}{nm}", (fx - 0.3, ye - 0.55, ze - 0.95), (0.5, 1.1, 1.9), pivot=(fx, ye, ze), parent=mask, paint=mg_eye, glow=60,
                       tag={"iris": iris, "look": look})
            else:
                m.part(f"Lid{i}{nm}", (fx - 0.45, ye - 0.6, ze - 1.0), (0.6, 1.1, 2.0), pivot=(fx, ye, ze), parent=mask, rest=(0, 0, 8),
                       paint=mg_lid, glow=18, tag=sk)
        # The nose, the cheekbones
        nh = fh * 0.32
        m.part(f"Nose{i}", (fx - 1.4, cy - fh * 0.27, cz - 0.75), (1.6, nh, 1.5), pivot=(fx, cy - fh * 0.27 + nh, cz), parent=mask,
               rest=(0, 0, -6), paint=mg_nose, glow=18, tag=sk)
        if fw >= 6.5:
            for side, nm in ((-1, "a"), (1, "b")):
                zc = cz + side * fw * 0.34
                m.part(f"Cheek{i}{nm}", (fx - 0.55, cy - fh * 0.2, zc - 0.9), (0.8, 1.3, 1.8), pivot=(fx, cy - fh * 0.14, zc), parent=mask,
                       rest=(side * -10, 0, 0), paint=mg_cheek, glow=18, tag=sk)
        # The mouth: the upper lip, and the jaw (chin and lower lip) hinged far back so it drops as it opens
        teeth = gap > 1.0
        ly = cy - fh * 0.36
        m.part(f"Lip{i}", (fx - 0.6, ly - 0.3, cz - fw * 0.24), (0.8, 0.8, fw * 0.48), pivot=(fx, ly, cz), parent=mask, paint=mg_lip, glow=18,
               tag=dict(sk, teeth=teeth))
        jh = fh * 0.2
        jaw = m.part(f"Jaw{i}", (fx - 0.5, ly - 0.3 - gap - jh, cz - fw * 0.3), (1.6, jh, fw * 0.6), pivot=(fx + 2.6, ly - 0.3, cz), parent=mask,
                     paint=mg_jaw, glow=18, tag=dict(sk, teeth=teeth))
        jaw_names.append(jaw.name)

    # ---- The tendrils ----
    tendril_names, claw_names, rest_z = [], [], {}
    for i, (x, z, n, thick, capture) in enumerate(MG_TENDRILS):
        out = math.atan2(z - MG_KNOT[2], x - MG_KNOT[0])                          # bend outward from under the knot, the ends hooking back in
        ox, oz = math.cos(out), math.sin(out)
        prev, top = knot, 54.0 if capture else 55.0
        names = []
        for j in range(n):
            t = thick * (1 - 0.62 * j / max(1, n - 1))
            seg = MG_SEG if capture else 5.0
            a = (9 if j == 0 else 3.5) if j < n - 4 else -9 - rng.uniform(0, 4)
            a *= 1.0 if capture else 1.3
            twist = rng.uniform(-4, 4)
            prev = m.part(f"Tendril{i}_{j}", (x - t / 2, top - seg - 0.5, z - t / 2), (t, seg + 0.5, t), pivot=(x, top, z), parent=prev,
                          rest=(-a * oz + twist * ox, 0, a * ox + twist * oz), paint=mg_tendril, tag={"tip": j == n - 1})
            names.append(prev.name)
            rest_z[prev.name] = a * ox + twist * oz
            top -= seg
        tendril_names.append(names)
        claws = []
        if capture:
            for k in range(3):
                ang = k * TAU / 3 + 0.4
                cx_, cz_ = math.cos(ang), math.sin(ang)
                cl = m.part(f"Claw{i}_{k}", (x - 0.35, top - 5, z - 0.35), (0.7, 5.2, 0.7), pivot=(x, top, z), parent=prev,
                            rest=(-cz_ * 28, 0, cx_ * 28), paint=mg_tendril, tag={"tip": True})
                m.part(f"Hook{i}_{k}", (x - 0.25, top - 8.2, z - 0.25), (0.5, 3.5, 0.5), pivot=(x, top - 5, z), parent=cl,
                       rest=(cz_ * 50, 0, -cx_ * 50), paint=mg_tendril, tag={"tip": True})
                claws.append(cl.name)
        claw_names.append(claws)

    all_tendrils = [nm for names in tendril_names for nm in names]
    all_claws = [nm for cl in claw_names for nm in cl]
    femurs = [f"Femur{i}" for i in range(8)]
    tibias = [f"Tibia{i}" for i in range(8)]
    metas = [f"Meta{i}" for i in range(8)]
    leg_names = femurs + tibias + metas
    side = [1 if yaw < 180 else -1 for (yaw, *_r) in MG_LEGS]

    def sway(p, amp, lag=0.0, which=None, speed=1.0):
        """The tendrils swinging, a wave running down each (and their claws flexing a little)."""
        d = {}
        for i, names in enumerate(tendril_names):
            if which is not None and i not in which:
                continue
            for j, nm in enumerate(names):
                d[nm] = pose((s(p * speed, amp * 0.7, i * 0.21 + j * 0.09 + lag), 0, s(p * speed, amp, i * 0.13 + j * 0.08 + lag + 0.25)))
        for i, cl in enumerate(claw_names):
            if which is not None and i not in which:
                continue
            for k, nm in enumerate(cl):
                d[nm] = pose((0, 0, 0)) if amp == 0 else pose((s(p * speed * 2, 6, k * 0.33), 0, s(p * speed * 2, 6, k * 0.33 + 0.25)))
        return d

    def talk(p, amount, speed=4, faces=None):
        """The faces' jaws working, each at its own pace: talking, all at once."""
        d = {}
        for i, nm in enumerate(jaw_names):
            if faces is not None and i not in faces:
                d[nm] = pose()
                continue
            k = max(0.0, math.sin(TAU * (p * (speed + i % 3) + i * 0.37))) * max(0.0, math.sin(TAU * (p * 2 + i * 0.19)))
            d[nm] = pose((0, 0, -amount * k), (0, -0.6 * amount / 20 * k, 0))
        return d

    def emerge(k_by_face):
        return {f"Face{i}": pose((0, 0, 0), (-k_by_face.get(i, 0.0), 0, 0)) for i in range(len(MG_FACES))}

    # ---- Walk: one leg at a time, in the order above; each lifts high, hangs, swings forward and comes down hard;
    # the others push back through the stance; the body rolls off the lifted leg and settles on each footfall; the
    # knot swings behind like a weight on a rope. 120 frames, 4 s: a footfall every half second.
    def gait(p, fwd, lift_deg, roll, swing_n=1.0, pitch=0.0):
        d = {}
        sw = 0.125 * swing_n                                    # the share of the cycle a leg spends in the air
        body_roll = body_dip = 0.0
        for i in range(8):
            q = (p - MG_ORDER.index(i) / 8) % 1.0
            if q < sw:
                t = q / sw
                lift = min(1.0, math.sin(math.pi * min(1.0, t * 1.1)) ** 0.6)
                a = -1 + 2 * (t * t * (3 - 2 * t))                  # back to front, easing
            else:
                t = (q - sw) / (1 - sw)
                lift = 0.0
                a = 1 - 2 * t
                if t < 0.06:                                   # the slam: the body settles onto it
                    body_dip += (1 - t / 0.06)
            body_roll += side[i] * lift
            d[f"Femur{i}"] = pose((0, -side[i] * fwd * a, -lift_deg * lift))
            d[f"Tibia{i}"] = pose((0, 0, lift_deg * TIB * lift))
            d[f"Meta{i}"] = pose((0, 0, lift_deg * META * lift))
        d["Body"] = pose((-roll * body_roll, s(p, 1.2), pitch - 0.5 * body_dip), (0, -0.6 * body_dip, 0))
        d["Abdomen"] = pose((s(p * 2, 2.5, 0.2), 0, s(p * 4, 2, 0.1) + 1.5 * body_dip))
        d["Stalk"] = pose((roll * 3 * s(p * 4, 1, 0.3) + s(p, 3), 0, 6 + s(p * 8, 1.5, 0.15)))
        d["Knot"] = pose((s(p * 4, 3, 0.45), s(p, 6), 3 + s(p * 8, 2, 0.3)))
        d.update({k: v for k, v in sway(p, 6, lag=0.0, speed=2).items() if k.startswith("Tendril")})
        for nm in all_tendrils:                                 # trailing behind as it goes
            r, o = d[nm]["rot"], d[nm]["off"]
            d[nm] = pose((r[0], r[1], r[2] + (5 if nm.endswith("_0") else 1.5)), o)
        d.update(talk(p, 10, speed=3))
        return d

    walk_names = ["Body", "Abdomen", "Stalk", "Knot"] + leg_names + all_tendrils + jaw_names
    m.animation("walk", 120, {f: full(walk_names, d) for f, d in cycle(120, 30, lambda p: gait(p, 18, 22, 1.0)).items()})
    # Run: the same order, faster, the legs reaching further and two in the air at once, the body leaning in
    m.animation("run", 64, {f: full(walk_names, d) for f, d in cycle(64, 24, lambda p: gait(p, 22, 26, 1.3, swing_n=1.9, pitch=0.5)).items()})

    # ---- Idle: breathing, settling its weight, the knot turning slowly, the faces murmuring, one opening its eyes ----
    idle_names = ["Body", "Abdomen", "Stalk", "Knot"] + all_tendrils + all_claws + jaw_names + face_names

    def idle(p):
        b = 0.012 * math.sin(TAU * p * 3)
        d = {"Body": pose((s(p, 0.8), s(p, 1.0, 0.3), s(p * 3, 0.6))), "Abdomen": pose((s(p, 2, 0.2), 0, s(p * 3, 2.5)), s=(1 + b, 1 + b * 1.5, 1 + b)),
             "Stalk": pose((s(p * 2, 2.5), 0, s(p * 3, 2, 0.2))), "Knot": pose((s(p * 2, 3, 0.3), s(p, 12), s(p * 3, 2.5, 0.5)))}
        d.update(sway(p, 7, speed=2))
        d.update(talk(p, 12, speed=4))
        d.update(emerge({0: 0.6 * ramp(p, 0.1, 0.2, 0.4, 0.55), 4: 0.8 * ramp(p, 0.45, 0.55, 0.7, 0.85), 2: 0.6 * ramp(p, 0.7, 0.8, 0.9, 1.0)}))
        return d

    m.animation("idle", 150, {f: full(idle_names, d) for f, d in cycle(150, 25, idle).items()})

    # ---- Search (the idle task's "despair"): it stoops, the knot dips toward the street and turns, the faces push out
    # of the mass one after another, all talking; the capture tendrils lift and feel forward ----
    search_names = ["Body", "Stalk", "Knot"] + all_tendrils + all_claws + jaw_names + face_names

    def search(p):
        r = ramp(p, 0.05, 0.22, 0.78, 0.95)
        d = {"Body": pose((0, s(p, 3), 0), (0, -1.2 * r, 0)), "Stalk": pose((s(p, 5), 0, -16 * r + s(p * 2, 3))),
             "Knot": pose((s(p * 2, 4), s(p, 40) * r, 10 * r))}                    # the knot swings out in front and turns
        d.update(sway(p, 9, speed=2))
        for i, names in enumerate(tendril_names):
            if MG_TENDRILS[i][4]:
                for j, nm in enumerate(names):
                    rr, o = d[nm]["rot"], d[nm]["off"]
                    d[nm] = pose((rr[0], rr[1], rr[2] * (1 - 0.4 * r) + (-48 * r if j == 0 else 6 * r * (1 if j > 5 else -0.3)) + s(p * 3, 5, i * 0.3 + j * 0.06)), o)
        d.update(talk(p, 18, speed=5))
        d.update(emerge({i: 1.6 * ramp(p, 0.08 + 0.05 * i, 0.16 + 0.05 * i, 0.7, 0.9) for i in range(len(MG_FACES))}))
        return d

    m.animation("despair", 100, {f: full(search_names, search(f / 100)) for f in range(0, 100, 5)} | {99: full(search_names, search(0.999))}, end="Stop")

    # ---- Attack (27 frames, 0.9 s; the entity's damage lands at 450 ms, frame 13): the front capture tendril draws
    # back and coils, lashes forward and down onto whoever is in front (frame 12-13), its fingers close round them, and
    # it hauls them up and away overhead. The knot leans in, its faces screaming; the body hardly moves. ----
    cap = tendril_names[0]
    atk_names = ["Body", "Stalk", "Knot"] + cap + claw_names[0] + jaw_names + face_names
    n0 = len(cap)

    def lash(root, curl, close, tip_curl=0.0):
        """The capture tendril posed absolutely (in the knot's frame): its root's angle from hanging straight down
        (negative: forward), each further segment's bend on the one before, the last three bending more."""
        d = {}
        for j, nm in enumerate(cap):
            a = root if j == 0 else curl + (tip_curl if j >= n0 - 3 else 0)
            d[nm] = pose((0, 0, a - rest_z[nm]))
        for k, nm in enumerate(claw_names[0]):
            ang = k * TAU / 3 + 0.4
            d[nm] = pose((math.sin(ang) * 30 * close, 0, -math.cos(ang) * 30 * close))
        return d

    def lean(knot_pitch, stalk_pitch, body_pitch, faces_out, scream):
        d = {"Body": pose((0, 0, body_pitch)), "Stalk": pose((0, 0, stalk_pitch)), "Knot": pose((0, 0, knot_pitch))}
        d.update(emerge({i: faces_out for i in range(len(MG_FACES))}))
        d.update({nm: pose((0, 0, -scream), (0, -scream / 25, 0)) for nm in jaw_names})
        return d

    m.animation("attack", 27, {
        0: full(atk_names, {}),
        4: full(atk_names, {**lash(30, 9, -0.6, 4), **lean(4, 4, -0.5, 0.6, 8)}),            # drawn back under it, coiling
        8: full(atk_names, {**lash(52, 14, -0.8, 8), **lean(6, 6, -1, 1.0, 14)}),
        11: full(atk_names, {**lash(-24, 1, -0.8, 0), **lean(-6, -6, 1, 1.6, 26)}),         # the lash
        13: full(atk_names, {**lash(-31, 0, 0.2, 18), **lean(-8, -9, 1.5, 2.0, 30)}),       # the hit: frame 13, 450 ms
        15: full(atk_names, {**lash(-31, 2, 1.0, 30), **lean(-8, -9, 1.5, 2.0, 30)}),       # the fingers close round them
        19: full(atk_names, {**lash(-95, -2, 1.0, 30), **lean(-2, -4, 0, 1.6, 24)}),        # hauled up
        23: full(atk_names, {**lash(-150, -4, 1.0, 30), **lean(4, 2, -1, 1.0, 14)}),        # overhead, seven blocks up
    }, end="Stop")

    # ---- Hurt: it flinches all over, every mouth opens at once ----
    hurt_names = ["Body", "Stalk", "Knot"] + jaw_names + face_names + all_tendrils
    def flinch(k):
        d = {"Body": pose((1.5 * k, 0, -1 * k)), "Stalk": pose((10 * k, 0, -12 * k)), "Knot": pose((8 * k, 14 * k, -8 * k))}
        d.update(emerge({i: 2.2 * k for i in range(len(MG_FACES))}))
        d.update({nm: pose((0, 0, -26 * k), (0, -1.0 * k, 0)) for nm in jaw_names})
        d.update({nm: pose((0, 0, (-14 if nm.endswith("_0") else -3) * k)) for nm in all_tendrils})
        return d
    m.animation("hurt", 16, {0: full(hurt_names, {}), 4: full(hurt_names, flinch(1.0)), 9: full(hurt_names, flinch(0.4)), 15: full(hurt_names, {})}, end="Stop")

    # ---- Death (it never dies; the animation is there all the same): the legs buckle one after another and the body
    # comes down into the street; the legs fold at their joints, zigzagging out across the road, the knot of faces
    # slumps over to lie on its side with the tendrils trailing along the ground after it; the abdomen sags ----
    die_names = ["Body", "Abdomen", "Stalk", "Knot"] + leg_names + all_tendrils + jaw_names + face_names
    TB = -1.5                                           # which way (and how hard) the tendrils droop
    DIE_BODY = (7, 0, 5)                                # the body's lean when it lies there
    # How each leg ends up: its femur's, tibia's and metatarsus's angle below horizontal (negative: up), then the
    # tibia's swing back across and the metatarsus's swing out again (the legs lie in zigzags, no two alike)
    leg_end = [(9, -2, 3, 128, -96), (6, 2, 5, 150, -118), (10, -5, 1, 118, -104), (8, 0, 4, 140, -84),
               (7, -3, 2, 136, 110), (9, 3, 5, 122, 92), (11, -1, 2, 148, 120), (6, -4, 3, 112, 100)]

    def lay(i, kb, st, sm):
        """The pose z of leg i's femur, tibia and metatarsus that put each at its angle below horizontal in the world,
        with the body leaned and the swings turned (the swings tilt the joints' axes, so this is solved, not added)."""
        import numpy as np
        yaw, _r0, _lf, af, _lt, at, am, _th = MG_LEGS[i]
        fd, td, md, ty, my = leg_end[i]
        R = rig._rot3(*(c * kb for c in DIE_BODY)) @ rig._rot3(0, yaw, 0)
        out = []
        for rest_z, drop, ry in ((af, fd, 0), (at - af, td, ty * side[i] * st), (am - at, md, my * sm)):
            best = min(np.arange(-70.0, 70.0, 0.25),
                       key=lambda z: abs((R @ rig._rot3(0, ry, z) @ np.array([-1.0, 0, 0]))[1] + math.sin(math.radians(drop))))
            R = R @ rig._rot3(0, ry, best)
            out.append(best - rest_z)
        return out

    def collapse(kl, ky, kb, hit=0.0, stagger=0.06):
        """kl: how far the legs have given (staggered by MG_ORDER), ky: how far they have folded, kb: the knot slumped."""
        d = {"Body": pose(tuple(c * kb for c in DIE_BODY)), "Abdomen": pose((0, 0, -12 * kb)),
             "Stalk": pose((88 * kb, 0, -8 * kb)), "Knot": pose((80 * kb, 12 * kb, 10 * kb))}
        for i in range(8):
            q = MG_ORDER.index(i) * stagger
            a = min(1.0, max(0.0, kl * (1 + 7 * stagger) - q))
            b = min(1.0, max(0.0, ky * (1 + 7 * stagger) - q))
            a, b = a * a * (3 - 2 * a), b * b * (3 - 2 * b)
            fz, tz, mz = lay(i, kb, b * a, b * a)
            ty, my = leg_end[i][3] * side[i], leg_end[i][4]
            d[f"Femur{i}"] = pose((0, 0, fz * a - 3 * hit))
            d[f"Tibia{i}"] = pose((0, ty * b * a, tz * a))
            d[f"Meta{i}"] = pose((0, my * b * a, mz * a))
        kt = min(1.0, kb * 1.6)
        for i, names in enumerate(tendril_names):                 # slack: draped down off the knot and curling along the street
            for j, nm in enumerate(names):
                bend = (34 if j == 0 else 15 + 4 * ((i + j) % 3)) * TB
                d[nm] = pose((6 * kt * (1 if (i + j) % 2 else -1) * TB, 0, bend * kt if MG_TENDRILS[i][4] or j else bend * kt * 1.3))
        d.update({nm: pose((0, 0, -34 * hit - 10 * kb - 6), (0, -1, 0)) for nm in jaw_names})
        d.update(emerge({i: 2.2 * hit + 1.5 * (1 - kb) * (1 - kl) for i in range(len(MG_FACES))}))
        return d

    die_keys = {0: collapse(0, 0, 0),
                4: collapse(0.0, 0.0, 0.0, hit=1.0),                    # the hit: every mouth gapes, the legs shudder
                14: collapse(0.25, 0.0, 0.1, hit=0.3),                    # the first legs buckle
                22: collapse(0.45, 0.0, 0.3),                             # the body comes down
                26: collapse(0.72, 0.05, 0.5),
                29: collapse(1.0, 0.15, 0.8),                             # impact: the legs thrown wide, the knot slams
                34: collapse(1.0, 0.3, 1.0),                              # a small rock back
                41: collapse(1.0, 0.65, 0.95),                            # the legs begin to fold
                47: collapse(1.0, 0.92, 1.0),
                53: collapse(1.0, 1.0, 1.0)}
    death(m, 54, die_names, die_keys, standing=(4,), soft=[p.name for p in m.parts if p.name.startswith(("Tendril", "Claw", "Hook"))])
    return m


# ======================================================================== The Thing
# Entity 20, "The Thing on Level 7". The Wikidot level page gives it almost no body: it rules the Midnight Zone and
# the upper Abyss, it "appears to have killed off any other life in the ocean", and "its life in perpetual darkness
# makes its eyes much more sensitive to light" (light drives it off). The other wikis fill the shape in: "a huge fish
# or sea monster" whose open mouth dwarfs a person (Miraheze), a body that "more closely resembles an eel" (Fandom),
# jaws that shoot forward to snap up prey, "many spikes ... especially on its tail" (Pantheon), and, in the fan
# retellings, "a colossal, shadowy shape" with "large, murky eyes" that surface beneath swimmers.
#
# The design is thalassophobia first: what you see is a vast dark length passing under you at the edge of the murk,
# far longer than you are, and only when it comes close does it resolve into a face. An eel-like leviathan 11 blocks
# long: a massive blunt head over a prognathous lower jaw hinged far back (open, it could take a person whole), a
# thick fore-body tapering through ten segments to a ragged leaf of a tail, a spined dorsal ribbon that ripples like
# an oarfish's, long trailing pectoral fins, and two chin barbels. Blue-black above, a dirty ivory belly below (the
# underside is what you see when it rises at you), pale needle teeth that show even with the mouth shut. The things
# that read in fog are the few pale or faintly glowing accents: milky, cataract-clouded, light-sick eyes, too many of
# them and not in matching places on its two sides; a line of dim photophores along each flank; the barbel tips.
# Old claw rakes and sucker-ring scars from whatever else once lived down there.
#
# Rig: the root is the middle segment (Seg4) at the entity's position, with the fore-body chained forward to the head
# and the hind-body chained back to the tail, so a swimming wave can travel through it while the middle holds course.

TH_DEEP = (7, 8, 12)            # the back: near black
TH_SKIN = (16, 19, 26)          # blue-black flank
TH_SLATE = (36, 42, 54)         # mottling, wrinkles
TH_BELLY_DARK = (56, 58, 62)    # the countershade's middle
TH_BELLY = (112, 110, 102)      # dirty ivory belly
TH_SCAR = (96, 100, 104)        # healed rakes and sucker rings
TH_PORE = (124, 136, 132)       # sensory pits on the head
TH_FLESH = (104, 54, 62)        # inside the mouth
TH_GUM = (156, 106, 106)
TH_THROAT = (10, 2, 5)
TH_TOOTH = (224, 218, 198)
TH_TOOTH_ROOT = (120, 108, 94)
TH_EYE = (208, 218, 212)        # milky
TH_EYE_CLOUD = (140, 160, 166)  # the cataract
TH_GLOW = (150, 212, 200)       # photophores: pale sea-green
TH_FIN = (20, 24, 32)
TH_RAY = (54, 62, 76)

TH_CY = 10                      # the spine's height: the middle of the 1.2-block hitbox
TH_X0, TH_STEP = 33, 12         # where the first body segment starts behind the snout, and the spacing of the rest
# Body segments, head to tail: (length, height, width, rise of the middle above the spine line)
TH_SEGS = [(15, 28, 25, 0.5), (14, 27, 23.5, 1.0), (14, 25.5, 22, 1.0), (14, 24, 20, 0.5), (14, 22, 18, 0),
           (14, 19.5, 15, 0), (14, 16.5, 12, 0), (14, 13, 9, 0), (14, 9.5, 6.5, 0), (14, 6.5, 4.5, 0)]
TH_ROOT = 4
TH_DORSAL = [0, 3, 5.5, 7, 7.5, 7.5, 7, 6.5, 6, 5.5]          # height of the dorsal ribbon over each segment
TH_VENTRAL = {5: 3.5, 6: 5, 7: 5.5, 8: 5, 9: 4.5}


def th_along(ctx, xx):
    """How far along the body (0 at the front, 1 at the back) a texel column of a side, top or bottom face lies."""
    u = (xx + 0.5) / ctx.w
    return 1 - u if ctx.face == "north" else u


def th_column(ctx, a):
    """The texel column at a fraction `a` along the body (inverse of th_along)."""
    return int((1 - a if ctx.face == "north" else a) * ctx.w)


def ring(ctx, cx, cy, r, colour, alpha):
    done = set()
    for i in range(int(r * 8) + 6):
        ang = TAU * i / (int(r * 8) + 6)
        p = (int(round(cx + r * math.cos(ang))), int(round(cy + r * math.sin(ang))))
        if p not in done:
            done.add(p)
            texel(ctx, p[0], p[1], colour, alpha)


def th_scars(ctx, chance=0.5):
    """What it fought: claw rakes in threes, and the round scars of suckers."""
    rng = ctx.rng
    if rng.random() < chance:
        u0, v0 = rng.uniform(0.05, 0.6), rng.uniform(0.1, 0.55)
        ang = rng.uniform(-0.7, 0.7)
        ln = rng.uniform(0.25, 0.5)
        for k in range(3):
            dv = k * 2.2 / ctx.h
            line(ctx, u0, v0 + dv, u0 + ln * math.cos(ang), v0 + dv + ln * math.sin(ang) * ctx.w / ctx.h * 0.4, TH_SCAR, 0.4)
            line(ctx, u0, v0 + dv + 1 / ctx.h, u0 + ln * math.cos(ang), v0 + dv + 1 / ctx.h + ln * math.sin(ang) * ctx.w / ctx.h * 0.4, TH_DEEP, 0.3)
    if rng.random() < chance * 0.6:
        for _ in range(rng.randint(1, 3)):
            ring(ctx, rng.uniform(3, max(3.5, ctx.w - 3)), rng.uniform(3, max(3.5, ctx.h - 3)), rng.uniform(1.4, 2.8), TH_SCAR, 0.45)


def th_flank(ctx, belly=0.58):
    """Countershaded: near black along the back, blue-black down the side, greying into a dirty ivory belly."""
    px = ctx.img.load()
    k = {"north": 0.94, "south": 0.94, "east": 0.88, "west": 1.0, "up": 1.0, "down": 1.0}[ctx.face]
    for yy in range(ctx.h):
        t = (yy + 0.5) / ctx.h
        if t < 0.22:
            c = mix(TH_DEEP, TH_SKIN, t / 0.22)
        elif t < belly:
            c = TH_SKIN
        else:
            q = (t - belly) / (1 - belly)
            c = mix(TH_SKIN, TH_BELLY_DARK, q / 0.55) if q < 0.55 else mix(TH_BELLY_DARK, TH_BELLY, (q - 0.55) / 0.45)
        for xx in range(ctx.w):
            mm = 1 + 0.1 * (ctx.rng.random() - 0.5) * 2
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(v * k * mm for v in c)) + (255,)
    blotch(ctx, TH_SLATE, max(1, ctx.w * ctx.h // 400), 2, 6, 0.22)
    if ctx.face in ("north", "south"):
        vlines(ctx, TH_DEEP, 3, start=ctx.rng.randint(0, 2), alpha=0.16, jitter=1)       # the slack folds of eel skin


def th_body(ctx):
    t = ctx.part.tag
    if ctx.face == "down":
        fill(ctx, TH_BELLY, 0.07, face_shade=False)
        blotch(ctx, TH_BELLY_DARK, 2, 2, 5, 0.35)
        hlines(ctx, shade(TH_BELLY, 0.8), 4, start=1, alpha=0.3)
        th_scars(ctx, 0.35)
        return
    if ctx.face == "up":
        fill(ctx, TH_DEEP, 0.18, face_shade=False)
        blotch(ctx, TH_SLATE, 2, 2, 5, 0.25)
        texrow(ctx, ctx.h // 2, 0, ctx.w - 1, (2, 2, 4), 0.6)                            # the groove of the spine
        speckle(ctx, TH_SLATE, 0.04)
        return
    th_flank(ctx)
    if ctx.face not in ("north", "south"):
        return
    ly = int(ctx.h * 0.47)
    for xx in range(ctx.rng.randint(0, 1), ctx.w, 2):                                   # the lateral line
        texel(ctx, xx, ly, TH_SLATE, 0.7)
    if t.get("gills"):
        for a in (0.14, 0.3, 0.46, 0.62):
            x0 = th_column(ctx, a)
            back = 1 if ctx.face == "south" else -1
            for yy in range(int(ctx.h * 0.2), int(ctx.h * 0.7)):
                bow = int(round(-back * 1.6 * math.sin(math.pi * (yy - ctx.h * 0.2) / (ctx.h * 0.5))))
                texel(ctx, x0 + bow, yy, TH_THROAT, 0.95)
                texel(ctx, x0 + bow + back, yy, TH_FLESH, 0.55)
                texel(ctx, x0 + bow - back, yy, TH_SLATE, 0.4)
    th_scars(ctx, t.get("scars", 0.45))


def th_pores(ctx, v, every=3, alpha=0.55):
    for xx in range(1 + ctx.rng.randint(0, every - 1), ctx.w - 1, every):
        yy = int(v * ctx.h) + ctx.rng.choice((0, 0, 1))
        texel(ctx, xx, yy, TH_PORE, alpha)
        texel(ctx, xx, yy + 1, TH_DEEP, 0.5)


def th_palate(ctx):
    """The roof of the mouth: dark red, ridged across, paler at the gum line."""
    fill(ctx, TH_FLESH, 0.1, face_shade=False)
    vlines(ctx, TH_GUM, 3, start=1, alpha=0.3)
    for yy in (0, 1, ctx.h - 2, ctx.h - 1):
        texrow(ctx, yy, 0, ctx.w - 1, TH_GUM, 0.7)
    blotch(ctx, TH_THROAT, 1, 2, 4, 0.3)


def th_head(ctx):
    if ctx.face == "down":
        th_palate(ctx)
        return
    if ctx.face == "up":
        fill(ctx, TH_DEEP, 0.18, face_shade=False)
        blotch(ctx, TH_SLATE, 2, 2, 6, 0.25)
        for v in (0.22, 0.78):
            th_pores(ctx, v)
        th_scars(ctx, 0.6)
        return
    th_flank(ctx, belly=0.8)
    if ctx.face in ("north", "south"):
        th_pores(ctx, 0.66)
        th_pores(ctx, 0.84, every=4, alpha=0.4)
        th_scars(ctx, 0.7)
        texrow(ctx, ctx.h - 1, 0, ctx.w - 1, TH_GUM, 0.45)                              # the lip


def th_snout(ctx):
    th_head(ctx)
    if ctx.face == "west":                                                               # the blunt face: pits, nostrils
        for v in (0.25, 0.45, 0.62):
            th_pores(ctx, v, every=4)
        for u in (0.3, 0.7):
            texel(ctx, int(u * ctx.w), int(ctx.h * 0.3), TH_THROAT)
            texel(ctx, int(u * ctx.w), int(ctx.h * 0.3) + 1, TH_THROAT, 0.7)


def th_brow(ctx):
    fill(ctx, TH_DEEP, 0.2)
    blotch(ctx, TH_SLATE, 2, 2, 5, 0.3)
    if ctx.face in ("north", "south", "west"):
        hlines(ctx, (2, 2, 4), 3, start=1, alpha=0.35)
    th_scars(ctx, 0.4)


def th_jaw(ctx):
    w, h = ctx.w, ctx.h
    if ctx.face == "up":                                                                 # the floor of the mouth
        fill(ctx, TH_FLESH, 0.1, face_shade=False)
        for yy in (0, 1, h - 2, h - 1):
            texrow(ctx, yy, 0, w - 1, TH_GUM, 0.75)
        texrow(ctx, h // 2, 4, w - 1, TH_THROAT, 0.5)                                    # the tongue's groove
        blotch(ctx, TH_THROAT, 2, 2, 5, 0.35)
        lip, beside = int(w * 5.5 / 40), int(w * 14 / 40)                                # ahead of and beside the snout: chin, dark
        for xx in range(beside):
            for yy in range(h):
                if xx < lip or yy < 3 or yy >= h - 3:
                    texel(ctx, xx, yy, mix(TH_SKIN, TH_SLATE, ctx.rng.random() * 0.4))
        return
    if ctx.face == "down":                                                               # the pale throat, pleated
        fill(ctx, TH_BELLY, 0.07, face_shade=False)
        hlines(ctx, TH_BELLY_DARK, 3, start=1, alpha=0.45)
        blotch(ctx, TH_BELLY_DARK, 1, 2, 5, 0.3)
        th_scars(ctx, 0.6)
        return
    if ctx.face == "east":
        fill(ctx, shade(TH_FLESH, 0.6), 0.1)
        return
    th_flank(ctx, belly=0.3)
    if ctx.face in ("north", "south"):
        texrow(ctx, 0, 0, w - 1, TH_GUM, 0.6)
        th_pores(ctx, 0.3, every=4, alpha=0.45)
        th_scars(ctx, 0.6)


def th_gullet(ctx):
    """The way in: a black hole ringed with ridged throat."""
    if ctx.face != "west":
        fill(ctx, shade(TH_FLESH, 0.7), 0.12)
        return
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            d = math.hypot((xx + 0.5 - ctx.w / 2) / (ctx.w / 2), (yy + 0.5 - ctx.h * 0.55) / (ctx.h / 2))
            if d < 0.5:
                c = TH_THROAT
            elif d < 0.62:
                c = mix(TH_THROAT, TH_FLESH, (d - 0.5) / 0.12)
            else:
                c = shade(TH_FLESH, 1.0 - 0.2 * ((int(d * 10)) % 2))
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(v * (0.92 + 0.16 * ctx.rng.random()) for v in c)) + (255,)


def th_eye(ctx):
    """Milky and clouded, the pupil shrunk to a pinprick: made for a dark that never ends, hurt by any light."""
    t = ctx.part.tag
    out = "south" if t.get("side", 1) > 0 else "north"
    if ctx.face != out:
        fill(ctx, TH_SKIN, 0.15)
        return
    px = ctx.img.load()
    w, h = ctx.w, ctx.h
    r = min(w, h) / 2
    for yy in range(h):
        for xx in range(w):
            d = math.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2) / r
            if d > 0.98:
                c = TH_DEEP
            elif d > 0.8:
                c = mix(TH_EYE_CLOUD, TH_DEEP, (d - 0.8) / 0.2 * 0.7)
            else:
                c = mix(TH_EYE, TH_EYE_CLOUD, d * d * 0.9)
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(v * (0.95 + 0.08 * ctx.rng.random()) for v in c)) + (255,)
    blotch(ctx, TH_EYE_CLOUD, 1, 1.5, r * 0.8, 0.35)
    if w >= 8:
        cx, cy = int(w / 2 + t.get("look", 0)), int(h / 2)
        texel(ctx, cx, cy, (40, 46, 50), 0.85)
        texel(ctx, cx - 1, cy, (70, 80, 84), 0.5)
        texel(ctx, cx - 2, cy - 2, (250, 252, 248), 0.8)                                  # a wet glint
    lid = t.get("lid", 0)
    for yy in range(int(lid * h)):                                                         # a heavy lid, half down
        texrow(ctx, yy, 0, w - 1, TH_SKIN)
    if lid:
        texrow(ctx, int(lid * h), 0, w - 1, TH_DEEP, 0.8)


def th_light(ctx):
    fill(ctx, TH_GLOW, 0.06, face_shade=False)
    if ctx.w >= 3 and ctx.h >= 3:
        texel(ctx, ctx.w // 2, ctx.h // 2, (228, 252, 242))
    for xx in range(ctx.w):
        texel(ctx, xx, 0, shade(TH_GLOW, 0.7), 0.6)
        texel(ctx, xx, ctx.h - 1, shade(TH_GLOW, 0.7), 0.6)


def th_tooth(ctx):
    """Long translucent needles, yellowed at the root."""
    if ctx.part.tag.get("tip"):
        fill(ctx, TH_TOOTH, 0.05, face_shade=False)
        return
    root_at_top = not ctx.part.tag.get("up")
    for yy in range(ctx.h):
        t = (yy + 0.5) / ctx.h
        r = (1 - t) if root_at_top else t                     # 1 at the root
        c = mix(TH_TOOTH, TH_TOOTH_ROOT, max(0.0, r - 0.55) / 0.45)
        texrow(ctx, yy, 0, ctx.w - 1, c)


def th_spine(ctx):
    for yy in range(ctx.h):
        texrow(ctx, yy, 0, ctx.w - 1, mix((96, 98, 92), TH_SKIN, (yy + 0.5) / ctx.h))


def th_barbel(ctx):
    t = ctx.part.tag
    fill(ctx, mix(TH_SLATE, TH_SKIN, 0.4), 0.12)
    if t.get("tip"):
        for xx in range(ctx.w):
            a = th_along(ctx, xx) if ctx.face in ("north", "south", "up", "down") else 1.0
            for yy in range(ctx.h):
                texel(ctx, xx, yy, TH_GLOW, 0.25 + 0.65 * a)


def th_fin(ctx):
    """Dark membrane between pale spined rays; the free edge torn into scallops between them."""
    t = ctx.part.tag
    kind = t.get("kind", "dorsal")
    w, h = ctx.w, ctx.h
    px = ctx.img.load()
    fill(ctx, TH_FIN, 0.14, face_shade=False)
    blotch(ctx, TH_SLATE, 1, 2, 5, 0.25)
    if kind in ("dorsal", "ventral"):
        free_top = kind == "dorsal"
        back = 1 if ctx.face == "south" else -1
        every, lean = 9, 0.8
        for yy in range(h):
            dist = (h - 1 - yy) if free_top else yy
            for k in range(-2 * h, w + 2 * h, every):
                texel(ctx, int(round(k + dist * lean * back)), yy, mix(TH_RAY, (118, 120, 112), (dist / max(1, h - 1)) ** 2 * 0.8), 0.9)
        for xx in range(w):
            r = (xx - back * lean * (h - 1)) % every
            dd = min(r, every - r) / (every / 2)
            cut = int(round(dd ** 1.4 * min(h * 0.4, 5)))
            for i in range(min(cut, h - 1)):
                yy = i if free_top else h - 1 - i
                px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)
        return
    if kind == "tail":
        # A spear-head: the dorsal and ventral ribbons meeting in a point, rays leaning back from the axis to the edge
        lim = lambda a: (0.68 + 0.6 * a) * (1 - a)
        back = 1 if ctx.face == "south" else -1
        mid = (h - 1) / 2
        for yy in range(h):
            dist = abs(yy - mid)
            for k in range(-2 * h, w + 2 * h, 9):
                texel(ctx, int(round(k + dist * 0.8 * back)), yy, mix(TH_RAY, (118, 120, 112), (dist / mid) ** 2 * 0.8), 0.9)
        texrow(ctx, int(mid), 0, w - 1, TH_RAY, 0.5)
        for xx in range(w):
            a = th_along(ctx, xx)
            r = (xx - back * 0.8 * mid) % 9
            dd = min(r, 9 - r) / 4.5
            for yy in range(h):
                v = abs(yy - mid) / mid
                if v > lim(a) - dd ** 1.4 * 0.12:
                    px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)
        return
    # Pectoral fins: flat plates (up/down faces); 0 at the body, 1 at the outer edge
    if ctx.face not in ("up", "down"):
        return
    inner_v0 = (ctx.face == "up") == (t.get("side", 1) > 0)
    trail = t.get("trail", False)
    for i in range(7):
        e = 0.15 + 0.85 * i / 6
        v0, v1 = (0.0, e) if inner_v0 else (1.0, 1 - e)
        line(ctx, 0.0, v0, 1.0 if trail else 0.35 + 0.65 * i / 6, v1, TH_RAY, 0.8)
    for xx in range(w):
        a = (xx + 0.5) / w
        lim = 0.9 * (1 - a) ** 0.6 if trail else 1 - 0.35 * a ** 2
        jag = ctx.rng.random() * 0.15
        for yy in range(h):
            o = (yy + 0.5) / h
            o = o if inner_v0 else 1 - o
            if o > lim - jag:
                px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)


@lit(reach=(1.0, 2.5, 4.5), ground=0.0, round_px=10.0, floor=26.0)
def thething():
    m = Model("thething", atlas_width=128, seed=7)
    cy = TH_CY
    xs = [TH_X0 + TH_STEP * i for i in range(len(TH_SEGS))]
    seg = {}

    def body(i, parent, pivot_x):
        length, h, w, rise = TH_SEGS[i]
        tag = {"gills": i == 0, "scars": 0.6 if i < 5 else 0.3}
        faces = tuple(f for f in ("north", "east", "south", "west", "up", "down") if not (f == "west" or f == "east" and i < len(TH_SEGS) - 1))
        seg[i] = m.part(f"Seg{i}", (xs[i], cy + rise - h / 2, -w / 2), (length, h, w), pivot=(pivot_x, cy, 0), parent=parent, paint=th_body, tag=tag,
                        faces=faces)

    # The middle first (the root, at the entity's position), then the fore-body forward and the hind-body back
    body(TH_ROOT, None, xs[TH_ROOT] + 3)
    for i in range(TH_ROOT - 1, -1, -1):
        body(i, seg[i + 1], xs[i + 1] + 1)
    for i in range(TH_ROOT + 1, len(TH_SEGS)):
        body(i, seg[i - 1], xs[i] + 1)

    # The head: a heavy skull over a lower jaw that juts past the snout, hinged far back
    head = m.part("Head", (6, cy - 4, -13), (31, 20, 26), pivot=(35, cy + 2, 0), parent=seg[0], paint=th_head,
                  faces=("north", "east", "south", "west", "up", "down"))
    m.part("Snout", (-3, cy - 4, -10), (10, 13, 20), pivot=(6, cy + 2, 0), parent=head, paint=th_snout)
    m.part("Forehead", (-4, cy + 10, -9.5), (16, 6, 19), pivot=(12, cy + 16, 0), parent=head, rest=(0, 0, 30), paint=th_brow)
    m.part("Brow", (6, cy + 14, -11), (24, 4.5, 22), pivot=(30, cy + 16, 0), parent=head, rest=(0, 0, 7), paint=th_brow)
    m.part("Gullet", (23, cy - 13, -10), (11, 11, 20), pivot=(30, cy - 6, 0), parent=head, paint=th_gullet, faces=("north", "south", "west"))
    jaw = m.part("Jaw", (-7, cy - 15, -11.5), (40, 10.8, 23), pivot=(31, cy - 7, 0), parent=head, paint=th_jaw)

    # Teeth. Upper: needles hanging from the snout (inside the jaw, seen when it opens) and along the cheeks, where the
    # skull overhangs the jaw (seen always). Lower: fangs up the outside of the snout, the front pair longest.
    rng = random.Random(2077)

    def tooth(name, parent, x, y, z, ln, wd, way, rest):
        """A needle from (x, y, z) pointing down (way -1) or up (+1); a long one tapers in a thinner, inward-curving tip."""
        base = ln * 0.55 if ln >= 4.5 else ln
        y0 = y - base - 0.3 if way < 0 else y - 0.6
        t = m.part(name, (x - wd / 2, y0, z - wd / 2), (wd, base + 0.9, wd), pivot=(x, y, z), parent=parent, rest=rest, paint=th_tooth,
                   tag={"up": way > 0})
        if ln >= 4.5:
            tw, tl, side = wd * 0.55, ln * 0.5, (1 if z > 0 else -1)
            yb = y + way * base
            m.part(name + "Tip", (x - tw / 2, yb - tl if way < 0 else yb, z - tw / 2), (tw, tl, tw), pivot=(x, yb, z), parent=t,
                   rest=(-way * side * 12, 0, rng.uniform(-6, 6)), paint=th_tooth, tag={"tip": True})
    for side in (1, -1):
        for j, (x, ln, z, wd) in enumerate([(-1.5, 6, 9.2, 1.0), (1.0, 4.5, 9.4, 0.9), (3.5, 5, 9.3, 0.9), (5.5, 3.5, 9.4, 0.8),
                                            (8.5, 4.5, 12.4, 1.0), (11.5, 3, 12.5, 0.8), (14, 5.5, 12.4, 1.0), (17, 3.5, 12.5, 0.8),
                                            (20, 4.5, 12.4, 0.9), (23, 3, 12.5, 0.8), (26, 3.5, 12.4, 0.8)]):
            tooth(f"ToothU{'L' if side > 0 else 'R'}{j}", head, x, cy - 4, side * z, ln, wd, -1, (side * rng.uniform(-8, 8), 0, rng.uniform(-14, 6)))
        for j, (x, ln, wd) in enumerate([(-6, 9, 1.3), (-3.5, 7, 1.1), (-1, 5, 1.0), (1.5, 6, 1.0), (4, 4, 0.9), (7, 5, 0.9), (10, 3.5, 0.8), (13, 4, 0.8)]):
            tooth(f"ToothD{'L' if side > 0 else 'R'}{j}", jaw, x, cy - 4.2, side * 10.9, ln, wd, 1, (side * rng.uniform(-10, 4), 0, rng.uniform(-6, 12)))

    # Eyes: one large milky eye a side, and a scatter of smaller ones behind it, not where the other side has them.
    # (x, y, size, lid, look, glow)
    eyes = {1: [(11, cy + 5, 6, 0.0, -1, 70), (19.5, cy + 9.5, 3, 0.0, 0, 55), (23, cy + 4.5, 2.5, 0.4, 0, 45)],
            -1: [(11.5, cy + 4.5, 6, 0.15, 1, 70), (18, cy + 2.5, 3.5, 0.5, 0, 50), (23.5, cy + 9, 2, 0.0, 0, 50), (8, cy + 11, 2, 0.0, 0, 45)]}
    eye_names = []
    for side, row in eyes.items():
        for k, (x, y, sz, lid, look, glow) in enumerate(row):
            name = f"Eye{'L' if side > 0 else 'R'}{k}"
            z0 = 12.3 if side > 0 else -12.3 - 1.4 * (1 if k == 0 else 0.9)
            m.part(name, (x, y, z0), (sz, sz, 1.4 if k == 0 else 1.26), pivot=(x + sz / 2, y + sz / 2, side * 13), parent=head, paint=th_eye,
                   glow=glow, tag={"side": side, "lid": lid, "look": look})
            eye_names.append(name)
        # The brow's overhang above the big eye
        m.part(f"Lid{'L' if side > 0 else 'R'}", (9.5, cy + 11, 11.8 if side > 0 else -13.8), (9, 2.2, 2), parent=head, paint=th_brow)

    # Barbels from the chin: they trail, and their tips glow faintly
    m.part("BarbelL", (-3, cy - 15.6, 3.4), (9, 1.2, 1.2), pivot=(-3, cy - 15, 4), parent=jaw, rest=(0, 10, -38), paint=th_barbel)
    m.part("BarbelMidL", (5.5, cy - 15.5, 3.5), (9, 1.0, 1.0), pivot=(5.5, cy - 15, 4), parent="BarbelL", rest=(0, 0, 22), paint=th_barbel)
    m.part("BarbelTipL", (14, cy - 15.4, 3.6), (8, 0.8, 0.8), pivot=(14, cy - 15, 4), parent="BarbelMidL", rest=(0, 0, 18), paint=th_barbel,
           glow=60, tag={"tip": True})
    m.mirror("BarbelL", "BarbelR")

    # Long trailing pectoral fins, low behind the head
    m.part("PecFinL", (38, cy - 7, 12), (14, 0.6, 12), pivot=(38, cy - 6.7, 12), parent=seg[0], rest=(30, 25, 0), paint=th_fin,
           faces=("up", "down"), tag={"kind": "pec", "side": 1})
    m.part("PecTrailL", (51, cy - 7, 12), (24, 0.6, 10), pivot=(51, cy - 6.7, 12), parent="PecFinL", rest=(-8, 6, 0), paint=th_fin,
           faces=("up", "down"), tag={"kind": "pec", "side": 1, "trail": True})
    m.mirror("PecFinL", "PecFinR")
    for n in ("PecFinR", "PecTrailR"):
        m.by_name[n].tag["side"] = -1

    # Spines over the shoulders, then the dorsal ribbon to the tail; a ventral ribbon under the hind third
    spines = []
    for k, (i, dx, ln) in enumerate([(0, 3, 8), (0, 9, 11), (1, 5, 10), (1, 11, 7)]):
        length, h, w, rise = TH_SEGS[i]
        top = cy + rise + h / 2
        m.part(f"Spine{k}", (xs[i] + dx - 0.5, top - 1, -0.5), (1, ln + 1, 1), pivot=(xs[i] + dx, top - 1, 0), parent=seg[i], rest=(0, 0, -38), paint=th_spine)
        spines.append(f"Spine{k}")
    dorsal, ventral = [], []
    for i in range(2, len(TH_SEGS)):
        length, h, w, rise = TH_SEGS[i]
        top = cy + rise + h / 2
        m.part(f"Dorsal{i}", (xs[i] + 0.5, top - 0.5, -0.3), (TH_STEP + 1.5, TH_DORSAL[i] + 0.5, 0.6), pivot=(xs[i] + 0.5, top - 0.5, 0), parent=seg[i],
               paint=th_fin, faces=("north", "south"), tag={"kind": "dorsal"})
        dorsal.append(f"Dorsal{i}")
    for i, fh in TH_VENTRAL.items():
        length, h, w, rise = TH_SEGS[i]
        bottom = cy + rise - h / 2
        m.part(f"Ventral{i}", (xs[i] + 0.5, bottom - fh, -0.3), (TH_STEP + 1.5, fh + 0.5, 0.6), pivot=(xs[i] + 0.5, bottom + 0.5, 0), parent=seg[i],
               paint=th_fin, faces=("north", "south"), tag={"kind": "ventral"})
        ventral.append(f"Ventral{i}")
    last = len(TH_SEGS) - 1
    m.part("TailFin", (xs[last] + 9, cy - 13, -0.3), (28, 26, 0.6), pivot=(xs[last] + 9, cy, 0), parent=seg[last], paint=th_fin,
           faces=("north", "south"), tag={"kind": "tail"})

    # Photophores: a dim line down each flank, two under each big eye
    lights = []
    for i in range(len(TH_SEGS) - 1):
        length, h, w, rise = TH_SEGS[i]
        for side in (1, -1):
            y = cy + rise - h * 0.12 + rng.uniform(-0.6, 0.6)
            name = f"Light{'L' if side > 0 else 'R'}{i}"
            m.part(name, (xs[i] + 6 + rng.uniform(-1, 1), y, w / 2 - 0.1 if side > 0 else -w / 2 - 0.2), (1.6, 1.6, 0.3), parent=seg[i], paint=th_light, glow=95)
            lights.append(name)
    for side in (1, -1):
        for k, x in enumerate((10, 15)):
            m.part(f"LightHead{'L' if side > 0 else 'R'}{k}", (x, cy + 1.5 - k, 12.9 if side > 0 else -13.2), (1.4, 1.4, 0.3), parent=head, paint=th_light, glow=95)

    # Centred on the entity's position: the middle of its length
    m.shift(dx=-84)

    # ---- Animations ----
    n = len(TH_SEGS)
    seg_names = [f"Seg{i}" for i in range(n)]
    barbels = ["BarbelL", "BarbelMidL", "BarbelTipL", "BarbelR", "BarbelMidR", "BarbelTipR"]
    pecs = ["PecFinL", "PecTrailL", "PecFinR", "PecTrailR"]
    names = ["Head", "Jaw", "TailFin"] + seg_names + barbels + pecs + dorsal + ventral

    def wave(p, amp, lag=0.085, vamp=0.0, straight=1.0):
        """A swimming wave from the head to the tail. Joint k (0: head to Seg0 ... n: last segment to the tail fin)
        bends by b_k; a forward-chained part (the head and the fore-body) takes -b_k, a hind one +b_k."""
        d = {}
        for k in range(n + 1):
            f = k / n
            a = amp * (0.3 + 0.7 * f ** 1.2) * straight
            b = a * math.sin(TAU * (p - k * lag))
            c = vamp * (0.4 + 0.6 * f) * math.sin(TAU * (p - k * lag) + 1.3)
            front = k <= TH_ROOT                                 # the joint lies ahead of the root: its child is the part before it
            part = ("Head" if k == 0 else f"Seg{k - 1}") if front else ("TailFin" if k == n else f"Seg{k}")
            sign = -1 if front else 1
            d[part] = pose((0, sign * b, sign * c))
        d[f"Seg{TH_ROOT}"] = pose((0, s(p, amp * 0.25, 0.25), 0))
        return d

    def fins(p, amp=9, fold=0.0, barbel_back=0.0):
        d = {}
        for j, nm in enumerate(dorsal):                          # the dorsal ribbon ripples front to back, twice a cycle
            d[nm] = pose((s(p * 2, amp * (1 - fold), -j * 0.12), 0, 0))
        for j, nm in enumerate(ventral):
            d[nm] = pose((s(p * 2, amp * (1 - fold), -j * 0.12 - 0.3), 0, 0))
        for side, sfx in ((1, "L"), (-1, "R")):                  # slow sculling; folded back flat in a rush
            d[f"PecFin{sfx}"] = pose((side * (s(p, 12, 0.0 if side > 0 else 0.5) * (1 - fold) - 18 * fold), side * 22 * fold, 0))
            d[f"PecTrail{sfx}"] = pose((side * s(p, 16, 0.2 if side > 0 else 0.7) * (1 - fold), side * 8 * fold, 0))
            d[f"Barbel{sfx}"] = pose((0, side * s(p, 8, 0.1 if side > 0 else 0.4), s(p, 6) + 30 * barbel_back))
            d[f"BarbelMid{sfx}"] = pose((0, side * s(p, 14, 0.25 if side > 0 else 0.55), s(p, 10, 0.2) - 12 * barbel_back))
            d[f"BarbelTip{sfx}"] = pose((0, side * s(p, 20, 0.4 if side > 0 else 0.7), s(p, 14, 0.35) - 10 * barbel_back))
        return d

    # Swim: slow and smooth, three seconds a stroke; the jaw hangs a little open and works
    def swim(p):
        d = wave(p, 6.5, lag=0.1, vamp=0.9)
        d.update(fins(p))
        d["Jaw"] = pose((0, 0, 4 + 3 * math.sin(TAU * (p + 0.2))))
        d[f"Seg{TH_ROOT}"] = pose((0, s(p, 1.4, 0.25), s(p, 0.8, 0.5)), (0, 1.2 * math.sin(TAU * p), 0))
        return d

    m.animation("swim", 90, {f: full(names, swim(f / 90)) for f in range(0, 90, 5)})

    # Rush: the long run in at a diver, the wave quick and deep, the maw already open, the fins laid back
    def rush(p):
        d = wave(p, 8.5, lag=0.1, vamp=0.6)
        d.update(fins(p, amp=4, fold=1.0, barbel_back=1.0))
        d["Jaw"] = pose((0, 0, 32 + 4 * math.sin(TAU * p * 2)))
        d["Head"] = pose((0, d["Head"]["rot"][1] * 0.5, -4))
        return d

    m.animation("rush", 30, {f: full(names, rush(f / 30)) for f in range(0, 30, 3)})

    # Attack (one-shot, 36 frames): it draws back into an S, the jaw dropping; lunges a block and a half forward with the
    # maw gaped wide; snaps shut (frame 15); shakes its head, and settles back into its line.
    def bend(front, back):
        """An S-curve: the fore-body one way, the hind-body the other (positive front pulls the head up and back)."""
        d = {}
        for i in range(n):
            if i < TH_ROOT:
                d[f"Seg{i}"] = pose((0, front * 6 * (1 - i / TH_ROOT), -front * 5))
            elif i > TH_ROOT:
                d[f"Seg{i}"] = pose((0, back * 7, back * 2))
        d["Head"] = pose((0, front * 4, -front * 10))
        d["TailFin"] = pose((0, back * 12, 0))
        return d

    def atk(front, back, jaw, lunge, head=(0, 0), fold=0.0, p=0.0):
        d = bend(front, back)
        d.update(fins(p, amp=5, fold=fold, barbel_back=fold))
        d["Jaw"] = pose((0, 0, jaw))
        d[f"Seg{TH_ROOT}"] = pose((0, 0, -front * 3), (-lunge, front * 1.5, 0))
        hy, hz = head
        d["Head"] = pose((0, d["Head"]["rot"][1] + hy, d["Head"]["rot"][2] + hz))
        return d

    atk_names = names + [f"Seg{TH_ROOT}"]
    m.animation("attack", 36, {
        0: full(atk_names, atk(0, 0, 5, 0)),
        7: full(atk_names, atk(1.0, -1.0, 24, -6, fold=0.5, p=0.2)),
        12: full(atk_names, atk(-0.3, 0.6, 58, 22, fold=1.0, p=0.4)),
        15: full(atk_names, atk(-0.2, 0.4, -1, 25, head=(0, 6), fold=1.0, p=0.5)),
        19: full(atk_names, atk(0, 0.2, 2, 23, head=(12, 3), fold=0.6, p=0.6)),
        23: full(atk_names, atk(0, -0.2, 3, 20, head=(-10, 0), fold=0.4, p=0.7)),
        27: full(atk_names, atk(0, 0.1, 4, 14, head=(5, 0), fold=0.2, p=0.8)),
        35: full(atk_names, atk(0, 0, 5, 0, p=1.0)),
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


@lit()
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


@lit()
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


@lit(grad=0.12, round=0.0, ao=0.3)
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


@lit()
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


# ======================================================================== Bacteria
# The Howler of Kane Parsons' found footage ("the Lifeform"; Entity 1 on the Fandom wiki), here the "dark figures
# stalking them between the corridors" of the Wikidot Level 0. "Very tall, thin and vaguely humanoid ... standing on two
# legs"; "a slim vine-like anatomy akin to a tangle of black wires shaped into a humanoid form"; "the arms reach the
# floor and it has long, thin fingers, while its legs are relatively short and lack feet"; "a cable-like string wraps
# around the body and legs"; its limbs "very thin and stiff, but it can still move fast and quietly"; it "comes to life"
# out of a black substance like mould. About eleven feet of it, which Level 0's three-block rooms cannot hold: it
# stoops, the torso bent forward and the faceless head craned out on a long neck, so it stands ~45 px with its crown
# under the ceiling tiles. As in the footage (stills on the Kane Pixels wiki: "Bacteria Standing", "Bacteria Canvas"),
# it is drawn in wire: a trunk of one kinked black cable with a thinner one twisted round it, a bar of wire across the
# shoulders whose ends curl down into hooks, floor-length arms and short legs that zigzag at every kink, coils wound on
# the limbs and loops of wire standing off the chest and a thigh; the legs end not in feet but in frayed wires splayed
# on the carpet like roots, and the fingers of the floor-length arms rest on the carpet too. The head is a squat
# faceless lump ringed with a coil like a hat's brim, with a seam that splits open when it howls. A cut or frayed end
# shows a little dull copper; nothing glows. It moves wrong: holds still, snaps to a new pose in a frame or two, holds
# again; it runs bent double, clawing at the carpet with its arms in turn.

BA_BLACK = (16, 15, 13)        # the cable: a black that is not quite black
BA_FIBRE = (31, 29, 25)        # ... lighter fibres in the knots
BA_GLINT = (64, 60, 50)        # ... and the dull glint where it creases
BA_DEEP = (5, 5, 5)            # gaps in the tangle
BA_MOULD = (26, 28, 18)        # an olive fuzz of mould
BA_TIP = (54, 50, 44)          # finger tips, worn grey


def ba_knot(ctx):
    """A knot of the tangle (hips, joints, jaw): strands crossing every which way over black gaps."""
    fill(ctx, BA_BLACK, 0.12)
    for _ in range(max(2, (ctx.w * ctx.h) // 10)):
        u0, v0 = ctx.rng.random(), ctx.rng.random()
        ang = ctx.rng.uniform(0, math.pi)
        ln = ctx.rng.uniform(0.3, 0.9)
        u1, v1 = u0 + math.cos(ang) * ln, v0 + math.sin(ang) * ln
        line(ctx, u0, v0, u1, v1, BA_FIBRE if ctx.rng.random() < 0.7 else BA_GLINT, 0.55)
    for _ in range(max(1, (ctx.w * ctx.h) // 18)):
        u0, v0 = ctx.rng.random(), ctx.rng.random()
        line(ctx, u0, v0, u0 + ctx.rng.uniform(-0.3, 0.3), v0 + ctx.rng.uniform(0.1, 0.4), BA_DEEP, 0.8)
    blotch(ctx, BA_MOULD, 1, 1.0, 2.5, 0.4)


def ba_head(ctx):
    """The head: a lump of the tangle, wound tighter and smoother than the body (it catches more light), no face."""
    fill(ctx, BA_BLACK, 0.1)
    if ctx.face in ("up", "west", "north", "south"):
        for _ in range(3):
            v = ctx.rng.uniform(0.1, 0.9)
            line(ctx, 0.0, v, 1.0, v + ctx.rng.uniform(-0.25, 0.25), BA_FIBRE, 0.6)
        line(ctx, 0.0, ctx.rng.uniform(0.2, 0.8), 1.0, ctx.rng.uniform(0.2, 0.8), BA_GLINT, 0.4)
    blotch(ctx, BA_MOULD, 1, 1.0, 2.0, 0.35)
    if ctx.face == "down":
        fill(ctx, BA_DEEP, 0.1, face_shade=False)


def ba_finger(ctx):
    """A long finger: a length of the cable with a darker knuckle band; the tip worn through to grey and copper."""
    ba_wire_paint(ctx)
    tip_c = mix(BA_TIP, BA_COPPER, 0.55)
    if ctx.face in ("north", "south", "east", "west"):
        texrow(ctx, 0, 0, ctx.w - 1, BA_DEEP, 0.7)
        if ctx.part.tag.get("tip"):
            texrow(ctx, ctx.h - 1, 0, ctx.w - 1, tip_c)
            texrow(ctx, ctx.h - 2, 0, ctx.w - 1, tip_c, 0.5)
    elif ctx.face == "down" and ctx.part.tag.get("tip"):
        fill(ctx, tip_c, 0.05, face_shade=False)


def ba_stain(ctx):
    """The black mould it comes out of: a blotch on the carpet, black at the heart, fuzzed olive-black at the rim, the
    edge blobby and spreading in fingers, spores round it."""
    px = ctx.img.load()
    w, h = ctx.w, ctx.h
    cx, cy = w / 2, h / 2
    lobes = [(ctx.rng.uniform(0, TAU), ctx.rng.uniform(0.06, 0.16), ctx.rng.randint(2, 5)) for _ in range(4)]
    fingers = [(ctx.rng.uniform(0, TAU), ctx.rng.uniform(0.15, 0.35)) for _ in range(7)]
    for ty in range(h):
        for tx in range(w):
            dx, dy = (tx + 0.5 - cx) / (w / 2), (ty + 0.5 - cy) / (h / 2)
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            edge = 0.66 + sum(amp * math.sin(k * a + ph) for ph, amp, k in lobes)
            for fa, fl in fingers:                           # creeping fingers of it reaching out
                da = abs((a - fa + math.pi) % TAU - math.pi)
                if da < 0.09:
                    edge = max(edge, 0.66 + fl * (1 - da / 0.09))
            edge += ctx.rng.uniform(-0.03, 0.03)
            if r < edge:
                t = r / edge
                c = mix(BA_DEEP, BA_BLACK, t * 0.8)
                if t > 0.7:
                    c = mix(c, BA_MOULD, (t - 0.7) / 0.3 * 0.8)
                if ctx.rng.random() < 0.08:
                    c = mix(c, BA_FIBRE, 0.6)
                px[ctx.x + tx, ctx.y + ty] = c + (255,)
            elif r < edge + 0.12 and ctx.rng.random() < 0.18 * (1 - (r - edge) / 0.12):
                px[ctx.x + tx, ctx.y + ty] = mix(BA_MOULD, BA_BLACK, 0.4) + (255,)      # spores
            else:
                px[ctx.x + tx, ctx.y + ty] = (0, 0, 0, 0)


BA_SHEEN = (46, 44, 40)        # the dull sheen down one edge of the cable's sheath
BA_COPPER = (110, 64, 34)      # bared copper where a wire is cut or frayed, dulled
BA_COPPER_HI = (150, 94, 52)   # ... and its brighter strands


def ba_wire_paint(ctx):
    """A length of the black cable it is made of (each segment is built along its own +y, so v runs along it on the
    side faces, the far end at the top): a matte sheath, a dull sheen down one edge that comes and goes, creases where
    it has been bent and straightened, now and then a fleck of mould; at a cut or frayed end (tag copper) the copper
    shows in the last texels and on the end."""
    p = ctx.part
    ph = p.tag.get("phase", 0)
    copper = p.tag.get("copper", False)
    fill(ctx, BA_BLACK, 0.04)
    if ctx.face in ("up", "down"):
        if ctx.face == "up" and copper:
            for ty in range(ctx.h):
                for tx in range(ctx.w):
                    texel(ctx, tx, ty, BA_COPPER_HI if (tx + ty + ph) % 2 else BA_COPPER)
        else:
            fill(ctx, BA_DEEP, 0.04, face_shade=False)
        return
    w, h = ctx.w, ctx.h
    edge = 0 if ctx.face in ("north", "west") else w - 1
    for ty in range(h):
        texel(ctx, edge, ty, BA_SHEEN, 0.3 + 0.22 * math.sin((ty + ph * 3) * 0.7))
    for ty in range((ph * 2 + 1) % 4, h, 4):
        texrow(ctx, ty, 0, w - 1, BA_DEEP, 0.5)
        if ty + 1 < h:
            texel(ctx, (ty // 4 + ph) % w, ty + 1, BA_GLINT, 0.3)
    if ctx.rng.random() < 0.25:
        blotch(ctx, BA_MOULD, 1, 0.8, 2.0, 0.35)
    if copper:
        n = min(h, 2)
        for ty in range(n):
            for tx in range(w):
                if ty == n - 1 and (tx + ph) % 2:
                    continue                                   # the ragged edge of the stripped sheath
                texel(ctx, tx, ty, BA_COPPER_HI if (tx + ty + ph) % 3 == 0 else BA_COPPER, 1.0 if ty < n - 1 else 0.7)


def _b_add(a, b, k=1.0):
    return tuple(a[i] + b[i] * k for i in range(3))


def _b_sub(a, b):
    return tuple(a[i] - b[i] for i in range(3))


def _b_unit(v):
    ln = math.sqrt(sum(c * c for c in v))
    return tuple(c / ln for c in v)


def _b_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _b_lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _b_perp(d):
    """Two unit vectors square to d (and to each other)."""
    d = _b_unit(d)
    ref = (1.0, 0.0, 0.0) if abs(d[0]) < 0.9 else (0.0, 0.0, 1.0)
    u = _b_unit(_b_cross(d, ref))
    return u, _b_cross(d, u)


def ba_bone(m, name, parent, at, length, rest=(0, 0, 0), up=False):
    """A bone that draws nothing: the animations turn it, the wires hung on it show it. Its pivot is `at` and it
    runs `length` up (or down) from there, as the strands it replaces did."""
    x, y, z = at
    return m.part(name, (x - 0.3, y if up else y - length, z - 0.3), (0.6, length, 0.6), pivot=at, parent=parent, rest=rest,
                  faces=(), tag={"occlude": False})


def ba_seg(m, name, parent, a, b, t, phase=0, copper=False):
    """One straight length of cable from a to b (model space, the parents unrotated), t thick: a box along +y from a,
    turned so +y points at b, lengthened by t/2 at both ends so the lengths of a kinked wire overlap at the bends."""
    d = _b_sub(b, a)
    ln = math.sqrt(sum(c * c for c in d))
    dx, dy, dz = (c / ln for c in d)
    rest = (round(math.degrees(math.atan2(dz, dy)), 3), 0, round(math.degrees(math.asin(max(-1.0, min(1.0, -dx)))), 3))
    # no start cap: every segment starts inside the one before it or the part it hangs from
    return m.part(name, (a[0] - t / 2, a[1] - t / 2, a[2] - t / 2), (t, ln + t, t), pivot=a, parent=parent, rest=rest,
                  paint=ba_wire_paint, faces=("north", "east", "south", "west", "up"), tag={"phase": phase, "copper": copper})


def ba_wire(m, name, parent, pts, t, copper=False, sd=""):
    """A wire through the points, one segment per leg, all hung on `parent`; copper bared at the last end."""
    for i in range(len(pts) - 1):
        ba_seg(m, f"{name}{i}{sd}", parent, pts[i], pts[i + 1], t, phase=i + len(name), copper=copper and i == len(pts) - 2)


def ba_kinks(a, b, n, amp, rng, lean=(0.0, 0.0)):
    """Points from a to b in n legs, the inner ones knocked aside in turn (zig, zag) by up to `amp`: a kinked wire.
    lean drifts the whole wire to one side (u, w) at its middle."""
    u, w = _b_perp(_b_sub(b, a))
    pts = [a]
    for k in range(1, n):
        f = (k + rng.uniform(-0.25, 0.25)) / n
        side = (1 if k % 2 else -1) * rng.uniform(0.55, 1.0) * amp
        across = rng.uniform(-0.45, 0.45) * amp
        bow = math.sin(math.pi * f)
        pts.append(_b_add(_b_add(_b_lerp(a, b, f), u, side + lean[0] * bow), w, across + lean[1] * bow))
    pts.append(b)
    return pts


def ba_twin(pts, off, rng):
    """A thinner wire twisted round another: it leaves from beside the first, crosses it at every bend (swapping
    sides) and ends beside it again."""
    out = []
    for k, p in enumerate(pts):
        if k + 1 < len(pts):
            u, w = _b_perp(_b_sub(pts[k + 1], p))
        sg = 1 if k % 2 else -1
        o = off * (0.4 if k in (0, len(pts) - 1) else 1.0)
        out.append(_b_add(_b_add(p, u, sg * o), w, rng.uniform(-0.5, 0.5) * off))
    return out


def ba_coil(a, b, f0, f1, r, turns, per_turn=6, phase=0.0):
    """A helix of wire wound round the line a..b from fraction f0 to f1, r out from it."""
    u, w = _b_perp(_b_sub(b, a))
    n = max(2, int(round(turns * per_turn)))
    pts = []
    for k in range(n + 1):
        t = k / n
        ang = phase + TAU * turns * t
        c = _b_lerp(a, b, f0 + (f1 - f0) * t)
        pts.append(_b_add(_b_add(c, u, r * math.cos(ang)), w, r * math.sin(ang)))
    return pts


def ba_loop(centre, u, w, r, n=6, open_at=0.0, phase=0.0):
    """A loop of wire round `centre` in the plane of u and w; open_at leaves that fraction of it out (a hook)."""
    u, w = _b_unit(u), _b_unit(w)
    span = TAU * (1.0 - open_at)
    return [_b_add(_b_add(centre, u, r * math.cos(phase + span * k / n)), w, r * math.sin(phase + span * k / n)) for k in range(n + 1)]


def _ba_lerp(a, b, t):
    out = {"rot": tuple(a["rot"][i] + (b["rot"][i] - a["rot"][i]) * t for i in range(3)),
           "off": tuple(a["off"][i] + (b["off"][i] - a["off"][i]) * t for i in range(3))}
    if "str" in a or "str" in b:
        sa, sb = a.get("str", (1, 1, 1)), b.get("str", (1, 1, 1))
        out["str"] = tuple(sa[i] + (sb[i] - sa[i]) * t for i in range(3))
    return out


def _ba_at(track, f, frames, loop):
    ks = sorted(k for k in track if not loop or k < frames)
    if f in ks:
        return track[f]
    prev = [k for k in ks if k <= f]
    nxt = [k for k in ks if k > f]
    if loop:
        pk, pv = (prev[-1], track[prev[-1]]) if prev else (ks[-1] - frames, track[ks[-1]])
        nk, nv = (nxt[0], track[nxt[0]]) if nxt else (ks[0] + frames, track[ks[0]])
    else:
        if not prev:
            return track[ks[0]]
        if not nxt:
            return track[ks[-1]]
        pk, pv, nk, nv = prev[-1], track[prev[-1]], nxt[0], track[nxt[0]]
    return _ba_lerp(pv, nv, (f - pk) / (nk - pk))


def ba_keys(frames, spec, overlay=None, step=0, loop=True, names=()):
    """Keyframes from sparse per-part keys, the way the motion is thought of: spec {frame: {part: pose}} keys a part
    only where it changes; between its keys it eases linearly (so two keys a frame apart are a snap, two equal keys a
    hold). Every emitted keyframe names every animated part at its interpolated pose (the game wants that), plus an
    optional overlay(frame) -> {part: pose} added on top (the loose wires swaying), sampled every `step` frames."""
    tracks = {}
    for f, parts in spec.items():
        for n, p in parts.items():
            tracks.setdefault(n, {})[f] = p
    frames_set = {0} | {f for f in spec if f < frames or not loop}
    if step:
        frames_set |= set(range(0, frames, step))
    if not loop:
        frames_set.add(frames - 1)
    every = set(tracks) | set(names) | (set(overlay(0)) if overlay else set())
    out = {}
    for f in sorted(frames_set):
        d = {}
        ov = overlay(f) if overlay else {}
        for n in every:
            p = _ba_at(tracks[n], f, frames, loop) if n in tracks else pose()
            if n in ov:
                o = ov[n]
                q = {"rot": tuple(p["rot"][i] + o["rot"][i] for i in range(3)), "off": tuple(p["off"][i] + o["off"][i] for i in range(3))}
                if "str" in p or "str" in o:
                    q["str"] = tuple(p.get("str", (1, 1, 1))[i] * o.get("str", (1, 1, 1))[i] for i in range(3))
                p = q
            d[n] = p
        out[f] = d
    return out


def R(x=0.0, y=0.0, z=0.0, o=(0, 0, 0), st=None):
    return pose((x, y, z), o, st)


@lit(floor=26.0)
def bacteria():
    m = Model("bacteria", atlas_width=64, seed=1)

    # The bones keep the places, pivots and rest turns of the first model (so every animation plays as before), but
    # draw nothing: what shows is wire hung on them, built in model space as if no parent were turned. Each limb is a
    # kinked main wire with a thinner one twisted round it and a coil wound on it; the shoulder bar's ends curl down
    # into hooks, loose loops stand off the chest and a thigh, and every cut or frayed end shows a little copper.
    rng = random.Random(386)
    HY, WL, CL, NL = 15.6, 8.8, 12.6, 5.6               # hip height; waist, chest and neck lengths
    CY = HY + 0.6 + WL - 0.2                            # where the chest starts
    SY = CY + CL - 0.8                                  # the shoulder bar
    NY = CY + CL - 0.2                                  # the neck's root
    HD = NY + NL                                        # the head's pivot

    # ---- Hips and torso: a small knot, a twisted trunk of wire rising out of it, bent forward under the ceiling ----
    hips = m.part("Hips", (-0.9, HY - 0.9, -1.4), (1.8, 1.8, 2.8), pivot=(0, HY, 0), paint=ba_knot)
    ba_wire(m, "HipTangleA", hips, [(0.7, HY + 1.0, -1.5), (-0.2, HY - 0.2, 0.3), (-0.6, HY - 1.3, 1.8)], 0.45)
    ba_wire(m, "HipBand", hips, ba_loop((0.1, HY + 0.2, 0), (1, 0.25, 0), (0, -0.15, 1), 1.55, n=5), 0.32)

    ba_bone(m, "Waist", hips, (0, HY + 0.6, 0), WL, rest=(0, 0, 6), up=True)
    a, b = (0, HY + 0.6, 0), (0, CY + 0.2, 0)
    trunk = ba_kinks(a, b, 3, 0.95, rng)
    ba_wire(m, "WaistWire", "Waist", trunk, 0.8)
    ba_wire(m, "WaistTwist", "Waist", ba_twin(trunk, 0.5, rng), 0.45)
    ba_wire(m, "WaistCoil", "Waist", ba_coil(a, b, 0.3, 0.62, 0.95, 1.2, 5, 0.4), 0.36)

    ba_bone(m, "Chest", "Waist", (0, CY, 0), CL, rest=(0, 0, 9), up=True)
    a, b = (0, CY, 0), (0, NY + 0.2, 0)
    trunk = ba_kinks(a, b, 4, 1.0, rng, lean=(0.3, 0.0))
    ba_wire(m, "ChestWire", "Chest", trunk, 0.85)
    ba_wire(m, "ChestTwist", "Chest", ba_twin(trunk, 0.55, rng), 0.5)
    ba_wire(m, "ChestCoil", "Chest", ba_coil(a, b, 0.22, 0.5, 1.05, 1.25, 5, 1.3), 0.38)
    # a loose loop standing off the back of the chest, as if pulled out of the coil
    ba_wire(m, "ChestLoop", "Chest", ba_loop((1.5, CY + 8.0, -0.9), (0.7, 0.7, 0.2), (0.1, -0.3, 1), 1.25, n=5, phase=2.6), 0.32)

    # ---- Shoulders: one bar of wire across, hunched high, its ends curled down into hooks ----
    m.part("ShoulderL", (-0.55, SY - 0.55, 0.0), (1.1, 1.1, 5.0), pivot=(0, SY, 0.2), parent="Chest", rest=(10, 0, 0),
           faces=(), tag={"occlude": False})

    # ---- Arms: floor-length kinked wires, the fingers splayed on the carpet ----
    UL, FL = 14.5, 14.4
    EY = SY - 0.2 - UL                                  # the elbow
    WY = EY - FL                                        # the wrist
    KY = WY - 2.2                                       # the knuckles
    ba_bone(m, "UpperArmL", "ShoulderL", (0, SY - 0.2, 4.75), UL, rest=(-13, 0, -15))
    ba_bone(m, "ForearmL", "UpperArmL", (0, EY, 4.75), FL, rest=(0, 0, -7))
    hand = m.part("HandL", (-0.3, WY - 2.3, 4.45), (0.6, 2.4, 0.6), pivot=(0, WY, 4.75), parent="ForearmL", rest=(0, 0, -4),
                  faces=(), tag={"occlude": False})
    for i, (dz, ln, tip, spread) in enumerate(((-0.6, 3.2, 2.6, 12), (-0.2, 3.8, 3.2, 4), (0.2, 3.6, 3.0, -4), (0.6, 3.0, 2.4, -12))):
        z = 4.75 + dz
        m.part(f"Finger{i}L", (-0.18, KY - ln, z - 0.18), (0.36, ln, 0.36), pivot=(0, KY, z), parent=hand,
               rest=(spread, 0, -14), paint=ba_finger)
        m.part(f"Tip{i}L", (-0.15, KY - ln - tip, z - 0.15), (0.3, tip + 0.1, 0.3), pivot=(0, KY - ln + 0.05, z), parent=f"Finger{i}L",
               rest=(0, 0, -38), paint=ba_finger, tag={"tip": True})
    ba_bone(m, "ShoulderWireL", "ShoulderL", (0.5, SY - 0.6, 4.3), 8.5, rest=(-6, 0, 8))
    ba_bone(m, "ElbowWireL", "ForearmL", (0.4, EY - 0.4, 5.2), 6.5, rest=(-4, 0, 6))

    # ---- Legs: short, footless, kinked, frayed into roots on the carpet ----
    TL, SL = 8.0, 6.9
    KN = HY - 0.4 - TL                                  # the knee
    ba_bone(m, "ThighL", hips, (0, HY - 0.4, 1.3), TL, rest=(-4, 0, -18))
    ba_bone(m, "ShinL", "ThighL", (0, KN + 0.1, 1.3), SL, rest=(3, 0, 30))

    m.mirror("ShoulderL", "ShoulderR")
    m.mirror("ThighL", "ThighR")
    # Asymmetry: the right shoulder sits a touch lower and further forward, the right arm a little more bent
    m.by_name["ShoulderR"].rest = (-13, 0, 0)
    m.by_name["UpperArmR"].rest = (14, 0, -15)
    m.by_name["ForearmR"].rest = (0, 0, -9)

    # The wire on each side, kinked differently left and right (z is mirrored for the right)
    for sd, g in (("L", 1), ("R", -1)):
        def P(x, y, z):
            return (x, y, g * z)
        # the shoulder bar, and its hook curling down over the top of the arm
        bar = ba_kinks(P(0, SY, 0.0), P(0, SY + 0.1, 5.0), 2, 0.4, rng)
        ba_wire(m, "ShoulderBar", f"Shoulder{sd}", bar, 0.75, sd=sd)
        ba_wire(m, "ShoulderTwist", f"Shoulder{sd}", ba_twin(bar, 0.42, rng), 0.42, sd=sd)
        ba_wire(m, "ShoulderHook", f"Shoulder{sd}", [P(0, SY + 0.1, 5.0), P(0.2, SY + 0.6, 6.0), P(0.3, SY - 0.6, 6.6),
                                                     P(0.1, SY - 1.7, 6.1), P(-0.1, SY - 1.9, 5.4)], 0.5, copper=True, sd=sd)
        # the upper arm: a kinked wire, a thinner one twisted round it, a coil wound on it below the shoulder
        a, b = P(0, SY - 0.2, 4.75), P(0, EY, 4.75)
        w1 = ba_kinks(a, b, 4, 0.75, rng)
        ba_wire(m, "UpperArmWire", f"UpperArm{sd}", w1, 0.65, sd=sd)
        ba_wire(m, "UpperArmTwist", f"UpperArm{sd}", ba_twin(w1[::2] + ([w1[-1]] if len(w1) % 2 == 0 else []), 0.42, rng), 0.4, sd=sd)
        ba_wire(m, "UpperArmCoil", f"UpperArm{sd}", ba_coil(a, b, 0.18, 0.4, 0.95, 1.5, 6, 0.7 * g), 0.36, sd=sd)
        # the forearm, and a tighter coil near the wrist
        a, b = P(0, EY, 4.75), P(0, WY, 4.75)
        w2 = ba_kinks(a, b, 3, 0.65, rng)
        ba_wire(m, "ForearmWire", f"Forearm{sd}", w2, 0.6, sd=sd)
        ba_wire(m, "ForearmTwist", f"Forearm{sd}", ba_twin(w2, 0.38, rng), 0.38, sd=sd)
        ba_wire(m, "ForearmCoil", f"Forearm{sd}", ba_coil(a, b, 0.7, 0.84, 0.7, 0.85, 6, 2.0), 0.34, sd=sd)
        # the hand: the wire splaying from the wrist to the four fingers
        for i, dz in enumerate((-0.55, 0.05, 0.6)):
            ba_seg(m, f"HandWire{i}{sd}", f"Hand{sd}", P(0, WY + 0.2, 4.75), P(0.15 * (i - 1), KY + 0.1, 4.75 + dz), 0.42, phase=i)
        # loose wires: off the shoulder and the elbow, kinked, the ends bared
        at = P(0.5, SY - 0.6, 4.3)
        ba_wire(m, "ShoulderLoose", f"ShoulderWire{sd}", ba_kinks(at, _b_add(at, (0.3, -8.5, 0)), 2, 0.6, rng), 0.3, copper=True, sd=sd)
        at = P(0.4, EY - 0.4, 5.2)
        ba_wire(m, "ElbowLoose", f"ElbowWire{sd}", ba_kinks(at, _b_add(at, (0.4, -6.5, 0.4 * g)), 2, 0.6, rng), 0.3, copper=True, sd=sd)
        # the thigh: a kinked wire, a twist, a coil
        a, b = P(0, HY - 0.4, 1.3), P(0, KN, 1.3)
        w3 = ba_kinks(a, b, 3, 1.15, rng)
        ba_wire(m, "ThighWire", f"Thigh{sd}", w3, 0.75, sd=sd)
        ba_wire(m, "ThighTwist", f"Thigh{sd}", ba_twin(w3, 0.45, rng), 0.42, sd=sd)
        ba_wire(m, "ThighCoil", f"Thigh{sd}", ba_coil(a, b, 0.25, 0.6, 1.0, 1.5, 6, 1.1 * g), 0.36, sd=sd)
        # the shin: kinked, ending in frayed roots splayed on the carpet
        a, b = P(0, KN + 0.1, 1.3), P(0, KN + 0.1 - SL + 0.2, 1.3)
        w4 = ba_kinks(a, b, 3, 1.0, rng)
        ba_wire(m, "ShinWire", f"Shin{sd}", w4, 0.7, sd=sd)
        ba_wire(m, "ShinTwist", f"Shin{sd}", ba_twin(w4[:1] + w4[2:], 0.4, rng), 0.4, sd=sd)
        for i, (dx, dz, ln) in enumerate(((-2.4, 1.0, 2.8), (2.0, 1.2, 2.4), (0.4, -2.2, 2.6))):
            end = _b_add(b, (dx, -0.4, g * dz))
            mid = _b_add(_b_lerp(b, end, 0.5), (rng.uniform(-0.5, 0.5), 0.5, g * rng.uniform(-0.5, 0.5)))
            ba_wire(m, f"Root{i}", f"Shin{sd}", [b, mid, end], 0.32, copper=True, sd=sd)
    # a loose loop standing off the left thigh
    ba_wire(m, "ThighLoopL", "ThighL", ba_loop((0.4, HY - 3.0, 2.6), (0.3, 1, 0), (0.2, 0, 1), 1.1, n=5, open_at=0.15, phase=0.4), 0.3)

    # Wires hanging off the hips: the cable wound round the body coming loose
    hip_wires = []
    for i, (at, ln, rest) in enumerate((((-0.9, HY - 0.8, 1.4), 9.0, (-10, 0, -6)), ((1.0, HY - 0.4, 0.4), 11.5, (4, 0, 10)),
                                        ((0.2, HY - 0.8, -1.6), 7.5, (12, 0, 4)), ((-0.6, HY - 0.6, -0.8), 5.5, (6, 0, -12)))):
        ba_bone(m, f"HipWire{i}", hips, at, ln, rest=rest)
        ba_wire(m, f"HipLoose{i}", f"HipWire{i}", ba_kinks(at, _b_add(at, (0, -ln, 0)), 2, 0.7, rng), 0.3, copper=True)
        hip_wires.append(f"HipWire{i}")

    # ---- Neck and head: a twisted wire craned forward; a squat faceless lump ringed with a coil like a hat brim ----
    ba_bone(m, "Neck", "Chest", (0, NY, 0), NL, rest=(0, 0, 24), up=True)
    neck = ba_kinks((0, NY, 0), (0, HD + 0.2, 0), 2, 0.45, rng)
    ba_wire(m, "NeckWire", "Neck", neck, 0.65)
    ba_wire(m, "NeckTwist", "Neck", ba_twin(neck, 0.4, rng), 0.4)
    head = m.part("Head", (-1.9, HD - 0.5, -1.5), (3.0, 1.6, 3.0), pivot=(0, HD, 0), parent="Neck", rest=(10, 0, -32), paint=ba_head)
    m.part("Crown", (-1.5, HD + 1.0, -1.1), (2.2, 1.0, 2.2), pivot=(-0.4, HD + 1.0, 0), parent=head, paint=ba_head)
    # the brim: a coil of wire round the head, wider than it and a little tilted, one loop of it sagging at the side
    ba_wire(m, "Brim", head, ba_loop((-0.4, HD + 0.25, 0), (1, 0.08, 0), (0, -0.1, 1), 2.75, n=7, phase=0.3), 0.5)
    ba_wire(m, "BrimSag", head, [(-1.0, HD + 0.2, 2.6), (-0.6, HD - 0.8, 3.1), (0.5, HD - 1.0, 2.9), (1.0, HD + 0.1, 2.4)], 0.35)
    jaw = m.part("Jaw", (-2.2, HD - 1.5, -1.1), (2.8, 1.0, 2.2), pivot=(0.4, HD - 0.9, 0), parent=head, paint=ba_knot)
    # short frayed wires under the jaw and off the back of the head, bared at the ends
    jaw_wires = []
    for i, (at, ln, rest) in enumerate((((-1.6, HD - 1.4, 0.6), 5.0, (-6, 0, 28)), ((-0.6, HD - 1.4, -0.6), 6.5, (8, 0, 34)),
                                        ((1.6, HD + 1.6, 0.2), 5.5, (4, 0, 40)))):
        ba_bone(m, f"JawWire{i}", jaw if i < 2 else "Crown", at, ln, rest=rest)
        ba_seg(m, f"JawLoose{i}", f"JawWire{i}", at, _b_add(at, (0.3, -ln * 0.45, 0.2)), 0.3, phase=i, copper=True)
        jaw_wires.append(f"JawWire{i}")

    # ---- The mould it comes out of: a stain on the floor, buried under the carpet except while it rises or falls ----
    m.part("Stain", (-12, -0.4, -12), (24, 0.1, 24), pivot=(0, -0.35, 0), faces=("up",), paint=ba_stain)

    # ================================================================ Animations
    # +Z swings a hanging limb back and leans an upright part forward; +X tilts an upright part toward the left (+z)
    # and swings a hanging part toward the right. Motion is held still and snapped between poses (two keys a frame or
    # two apart), never eased into a natural rhythm; only the loose wires drift.
    fingers = [f"{k}{i}{sd}" for k in ("Finger", "Tip") for i in range(4) for sd in "LR"]
    wires = ["ShoulderWireL", "ShoulderWireR", "ElbowWireL", "ElbowWireR"] + hip_wires + jaw_wires

    def drift(amp=4.0, speed=1.0, trail=0.0, frames=120):
        def f(fr):
            p = fr / frames
            d = {}
            for i, n in enumerate(wires):
                d[n] = pose((s(p * speed, amp * 0.7, i * 0.21), 0, trail + s(p * speed * 1.3, amp, i * 0.37)))
            return d
        return f

    def fingers_curl(side, amount, tips=1.4):
        return {**{f"Finger{i}{side}": R(z=-amount) for i in range(4)}, **{f"Tip{i}{side}": R(z=-amount * tips) for i in range(4)}}

    def fingers_spread(side, amount):
        sg = 1 if side == "L" else -1
        return {**{f"Finger{i}{side}": R(x=sg * (1.5 - i) * amount * 0.5, z=amount * 0.4) for i in range(4)},
                **{f"Tip{i}{side}": R(z=amount * 0.6) for i in range(4)}}

    # Idle (5 s): nothing, held. Then the head snaps over into a tilt and stays there, a shoulder jerks, two fingers
    # on the carpet curl and let go, the head snaps back; once, the whole thing shudders for a frame.
    m.animation("idle", 150, ba_keys(150, {
        0: {"Head": R(), "Neck": R(), "Chest": R(), "ShoulderR": R(), "Finger1L": R(), "Tip1L": R(), "Finger2L": R(), "Tip2L": R()},
        36: {"Head": R()},
        38: {"Head": R(x=-22, y=-6, z=4)},
        40: {"Head": R(x=-18, y=-4, z=2)},
        70: {"Head": R(x=-18, y=-4, z=2), "ShoulderR": R()},
        71: {"ShoulderR": R(x=-6, z=-6)},
        74: {"ShoulderR": R()},
        88: {"Finger1L": R(), "Tip1L": R(), "Finger2L": R(), "Tip2L": R()},
        92: {"Finger1L": R(z=26), "Tip1L": R(z=-40), "Finger2L": R(z=18), "Tip2L": R(z=-34)},
        104: {"Finger1L": R(z=26), "Tip1L": R(z=-40), "Finger2L": R(z=18), "Tip2L": R(z=-34)},
        106: {"Finger1L": R(), "Tip1L": R(), "Finger2L": R(), "Tip2L": R()},
        110: {"Head": R(x=-18, y=-4, z=2)},
        111: {"Head": R(x=4, y=2, z=-3)},
        113: {"Head": R()},
        128: {"Chest": R(), "Neck": R()},
        129: {"Chest": R(x=3, z=-2), "Neck": R(x=-4, z=3)},
        131: {"Chest": R(), "Neck": R()},
        # twitches in the wire: a hand jerks, a forearm kinks and lets go, a knee buckles for a frame, the head shivers
        18: {"HandR": R()}, 19: {"HandR": R(x=6, z=-14)}, 21: {"HandR": R(x=2, z=-4)}, 23: {"HandR": R()},
        52: {"ForearmL": R()}, 53: {"ForearmL": R(x=-5, z=-9)}, 54: {"ForearmL": R(x=3, z=-3)}, 57: {"ForearmL": R()},
        80: {"ShinR": R(), "ThighR": R()}, 81: {"ShinR": R(z=9), "ThighR": R(z=-5)}, 83: {"ShinR": R(), "ThighR": R()},
        140: {"Head": R(), "ShoulderL": R()}, 141: {"Head": R(x=5, z=-2), "ShoulderL": R(x=4)}, 142: {"Head": R(x=-3)},
        143: {"Head": R(x=2, z=1), "ShoulderL": R()}, 145: {"Head": R()},
    }, overlay=drift(3, 1, 0, 150), step=10))

    # Lurk (6 s): standing at the end of the corridor, watching. The head tilts over, slowly, far further than a neck
    # should allow; holds; snaps upright and forward (it has seen you); the fingers flex on the carpet one after
    # another; the head turns a little and tilts back the other way.
    lk = {
        0: {"Head": R(), "Neck": R(), "Chest": R(), "Waist": R(), "ShoulderL": R(), "ShoulderR": R(), "Jaw": R(),
            **fingers_curl("L", 0), **fingers_curl("R", 0)},
        20: {"Head": R(x=-4)},
        60: {"Head": R(x=-34, y=-6, z=-4), "Neck": R(x=-6)},
        96: {"Head": R(x=-36, y=-6, z=-4), "Neck": R(x=-6), "Chest": R(), "ShoulderL": R(), "ShoulderR": R()},
        98: {"Head": R(x=6, y=8, z=-12), "Neck": R(x=2, z=6), "Chest": R(z=3), "ShoulderL": R(x=-5), "ShoulderR": R(x=5)},
        100: {"Head": R(x=4, y=6, z=-10), "Neck": R(z=5), "Chest": R(z=2), "ShoulderL": R(), "ShoulderR": R()},
        104: {"Jaw": R()}, 106: {"Jaw": R(z=12)}, 112: {"Jaw": R(z=12)}, 113: {"Jaw": R()},
        150: {"Head": R(x=4, y=6, z=-10), "Neck": R(z=5), "Chest": R(z=2)},
        172: {"Head": R(x=14, y=2, z=-4), "Neck": R(z=2), "Chest": R()},
    }
    # the finger ripple (right hand, then left), each finger curling in two frames and letting go slowly
    for k, (side, base) in enumerate((("R", 108), ("L", 126))):
        for i in range(4):
            f0 = base + i * 3
            for fr, amt in ((f0, 0), (f0 + 2, 34), (f0 + 10, 30), (f0 + 16, 0)):
                lk.setdefault(fr, {}).update({f"Finger{i}{side}": R(z=-amt * 0.2 if amt else 0, x=0), f"Tip{i}{side}": R(z=-amt)})
                if amt:
                    lk[fr][f"Finger{i}{side}"] = R(z=amt * 0.7)
    m.animation("lurk", 180, ba_keys(180, lk, overlay=drift(3, 1, 0, 180), step=12))

    # Walk (1.33 s a cycle): a stiff, stepped stride, each leg swinging and then stopping dead (plateau), the knee
    # barely bending; the body rocks side to side over the planted leg; the arms hardly swing but drag, the fingers
    # trailing over the carpet behind the hands. The head is held level and still, then twitches once.
    def walk(p):
        sw = plateau(p, 1.0, 1.7)
        lift_l = max(0.0, math.sin(TAU * (p + 0.25)))
        lift_r = max(0.0, math.sin(TAU * (p + 0.75)))
        rock = plateau(p + 0.25, 1.0, 1.8)
        d = {
            "Hips": R(x=rock * 4, y=sw * 5, o=(0, -0.4 + 0.4 * abs(math.sin(TAU * p)), 0)),
            "Waist": R(x=-rock * 2, z=3), "Chest": R(x=-rock * 2, y=-sw * 5, z=2),
            "Neck": R(), "Head": R(x=-rock * 1, y=0, z=-4),
            "ThighL": R(z=-18 * sw), "ThighR": R(z=18 * sw),
            "ShinL": R(z=22 * lift_l), "ShinR": R(z=22 * lift_r),
            "UpperArmL": R(z=-1 + 7 * sw), "UpperArmR": R(z=-1 - 7 * sw),
            "ForearmL": R(z=-20 + 4 * sw), "ForearmR": R(z=-20 - 4 * sw),
            "HandL": R(z=6), "HandR": R(z=6),
        }
        for sd in "LR":
            for i in range(4):
                d[f"Finger{i}{sd}"] = R(z=40)
                d[f"Tip{i}{sd}"] = R(z=40)
        return d

    wk = cycle(40, 20, walk)
    # the head's twitch, once a cycle: snap aside and back
    for fr, hp in ((26, R(z=-4)), (27, R(x=-14, y=10, z=-6)), (30, R(x=-12, y=8, z=-6)), (31, R(z=-4))):
        wk.setdefault(fr, walk(fr / 40))
        wk[fr]["Head"] = hp
    for fr in list(wk):
        wk[fr].update(drift(5, 2, 10, 40)(fr))
    m.animation("walk", 40, wk)

    # Run (0.67 s a cycle): bent double and lurching, the long arms reaching out ahead and clawing the carpet back in
    # turn like front legs, the short legs scrabbling under it; the head thrust out level, jerking. The wires stream.
    def run(p):
        # each arm: reaching out ahead at phase 0, planted and dragged back to phase 0.5, then whipped forward folded
        d = {}
        bob = math.sin(TAU * p * 2)
        for sd, ph in (("L", 0.0), ("R", 0.5)):
            q = (p + ph) % 1.0
            swing = -math.cos(TAU * q)                        # -1 reaching ahead .. +1 swept back
            lift = max(0.0, -math.sin(TAU * q))               # the arm's swing forward, off the carpet
            d[f"UpperArm{sd}"] = R(z=-26 + (30 if swing < 0 else 22) * swing - 8 * lift)
            d[f"Forearm{sd}"] = R(z=-38 * (1 - abs(swing) * 0.5) * (1 - lift) + 50 * lift)
            d[f"Hand{sd}"] = R(z=20 + 30 * lift)
            for i in range(4):
                d[f"Finger{i}{sd}"] = R(z=-6 + 30 * lift + 14 * max(0.0, swing))
                d[f"Tip{i}{sd}"] = R(z=-20 + 40 * lift)
        for sd, ph in (("L", 0.25), ("R", 0.75)):
            q = (p + ph) % 1.0
            swing = -math.cos(TAU * q)
            lift = max(0.0, -math.sin(TAU * q))
            d[f"Thigh{sd}"] = R(z=-14 + 28 * swing - 12 * lift)
            d[f"Shin{sd}"] = R(z=8 + 50 * lift)
        a = math.sin(TAU * p)
        d.update({
            "Hips": R(z=14 + 3 * bob, x=3 * a, o=(0, -0.8 + 0.8 * bob, 0)),
            "Waist": R(z=6 - 2 * bob), "Chest": R(z=2 + 3 * bob, x=-4 * a),
            "Neck": R(z=-22), "Head": R(z=-6 - 5 * bob, x=6 * a),
            "Jaw": R(z=8 + 8 * max(0.0, bob)),
            "ShoulderL": R(z=-5 * a), "ShoulderR": R(z=5 * a),
        })
        d.update(drift(8, 3, 34, 20)(p * 20))
        return d

    m.animation("run", 20, cycle(20, 10, run))

    # Attack (30 frames, 1 s; the grab lands on frame 13, damageAtMs ~450): it rears up, the jaw splitting into a howl
    # and the arms flung up and wide; snaps forward, the arms sweeping in from both sides to close round you at frame
    # 13, fingers clenching; holds you, pulling in; lets go and stands as if nothing happened.
    atk = {
        0: {"Hips": R(), "Waist": R(), "Chest": R(), "Neck": R(), "Head": R(), "Jaw": R(),
            "ShoulderL": R(), "ShoulderR": R(), "UpperArmL": R(), "UpperArmR": R(), "ForearmL": R(), "ForearmR": R(),
            "HandL": R(), "HandR": R(), **fingers_curl("L", 0), **fingers_curl("R", 0),
            "ThighL": R(), "ShinL": R(), "ThighR": R(), "ShinR": R()},
        3: {"Waist": R(z=-4), "Chest": R(z=-6), "Neck": R(z=-10), "Head": R(z=10), "Jaw": R(z=18)},
        7: {"Hips": R(o=(0.8, 0, 0)), "Waist": R(z=-8), "Chest": R(z=-12), "Neck": R(z=-14), "Head": R(z=16, x=-8), "Jaw": R(z=38),
            "ShoulderL": R(), "ShoulderR": R(),
            "UpperArmL": R(-103.5, 0, -34.4), "UpperArmR": R(103.5, 0, -34.4), "ForearmL": R(x=50.6, z=0.9), "ForearmR": R(x=-50.6, z=0.9),
            "HandL": R(), "HandR": R(), **fingers_spread("L", 40), **fingers_spread("R", 40)},
        9: {"ThighL": R(), "ShinL": R(), "ThighR": R(), "ShinR": R(), "Hips": R(o=(0.6, 0, 0)), "Waist": R(z=-8), "Chest": R(z=-12), "Neck": R(z=-14), "Head": R(z=16, x=-8), "Jaw": R(z=38),
            "UpperArmL": R(-97.8, -5.2, -32.2), "UpperArmR": R(97.8, 5.2, -32.2), "ForearmL": R(x=34.7, z=1.7), "ForearmR": R(x=-34.7, z=1.7)},
        # the lunge: a long step in, the arms swinging round from wide to close
        11: {"Hips": R(o=(-1.6, -1.2, 0)), "Waist": R(z=10), "Chest": R(z=8), "Neck": R(z=2), "Head": R(z=-14), "Jaw": R(z=36),
             "ShoulderL": R(x=-6), "ShoulderR": R(x=6),
             "UpperArmL": R(-84.2, 21.4, -4.8), "UpperArmR": R(84.2, -21.4, -4.8), "ForearmL": R(x=25.3, z=-39.1), "ForearmR": R(x=-25.3, z=-39.1),
             "ThighL": R(z=-26), "ShinL": R(z=22), "ThighR": R(z=16), "ShinR": R(z=8)},
        # frame 13: the grab closes round you (damage)
        13: {"Hips": R(o=(-2, -1.6, 0)), "Waist": R(z=12), "Chest": R(z=10), "Neck": R(z=2), "Head": R(z=-16), "Jaw": R(z=30),
             "ShoulderL": R(x=4), "ShoulderR": R(x=-4),
             "UpperArmL": R(-92.4, -1.0, -20.1), "UpperArmR": R(92.4, 1.0, -20.1), "ForearmL": R(x=18.2, z=-92.3), "ForearmR": R(x=-18.2, z=-92.3),
             "HandL": R(x=20), "HandR": R(x=-20), **fingers_curl("L", 40), **fingers_curl("R", 40),
             "ThighL": R(z=-30), "ShinL": R(z=25), "ThighR": R(z=18), "ShinR": R(z=10)},
        16: {"Hips": R(o=(-1.8, -1.5, 0)), "Waist": R(z=11), "Chest": R(z=9), "Neck": R(z=2), "Head": R(z=-14), "Jaw": R(z=12),
             "UpperArmL": R(-87.4, -10.9, -20.0), "UpperArmR": R(87.4, 10.9, -20.0), "ForearmL": R(x=14.2, z=-106.6), "ForearmR": R(x=-14.2, z=-106.6),
             "HandL": R(x=20), "HandR": R(x=-20)},
        # pulling what it caught in to itself
        21: {"Hips": R(o=(-1.0, -0.8, 0)), "Waist": R(z=6), "Chest": R(z=4), "Neck": R(z=0), "Head": R(z=-8), "Jaw": R(z=4),
             "ShoulderL": R(), "ShoulderR": R(),
             "UpperArmL": R(-79.9, -26.8, -24.6), "UpperArmR": R(79.9, 26.8, -24.6), "ForearmL": R(x=10.4, z=-106.6), "ForearmR": R(x=-10.4, z=-106.6),
             **fingers_curl("L", 40), **fingers_curl("R", 40),
             "ThighL": R(z=-14), "ShinL": R(z=12), "ThighR": R(z=8), "ShinR": R(z=4)},
        29: {"Hips": R(), "Waist": R(), "Chest": R(), "Neck": R(), "Head": R(), "Jaw": R(),
             "UpperArmL": R(), "UpperArmR": R(), "ForearmL": R(), "ForearmR": R(), "HandL": R(), "HandR": R(),
             **fingers_curl("L", 0), **fingers_curl("R", 0), "ThighL": R(), "ShinL": R(), "ThighR": R(), "ShinR": R()},
    }
    m.animation("attack", 30, ba_keys(30, atk, overlay=drift(10, 2, 0, 30), step=0, loop=False), end="Stop")

    # Hurt (15 frames): snaps back and aside, the head wrenched over, the jaw split, the arms flung; jerks back.
    hu = {
        0: {"Hips": R(), "Waist": R(), "Chest": R(), "Neck": R(), "Head": R(), "Jaw": R(), "UpperArmL": R(), "UpperArmR": R(),
            "ForearmL": R(), "ForearmR": R()},
        2: {"Hips": R(o=(1.5, 0, 0)), "Waist": R(z=-10, x=6), "Chest": R(z=-10, y=14), "Neck": R(z=-8), "Head": R(x=34, y=-10, z=14),
            "Jaw": R(z=30), "UpperArmL": R(x=-30, z=20), "UpperArmR": R(x=24, z=26), "ForearmL": R(z=-20), "ForearmR": R(z=-16)},
        5: {"Hips": R(o=(1.2, 0, 0)), "Waist": R(z=-8, x=5), "Chest": R(z=-8, y=12), "Neck": R(z=-6), "Head": R(x=30, y=-8, z=12),
            "Jaw": R(z=26), "UpperArmL": R(x=-24, z=16), "UpperArmR": R(x=20, z=20), "ForearmL": R(z=-16), "ForearmR": R(z=-12)},
        6: {"Head": R(x=-6, y=4, z=-4), "Jaw": R(z=6)},
        8: {"Hips": R(o=(0.3, 0, 0)), "Waist": R(z=-2), "Chest": R(z=-2, y=3), "Neck": R(), "Head": R(x=-6, y=4, z=-4),
            "UpperArmL": R(x=-6, z=4), "UpperArmR": R(x=6, z=4), "ForearmL": R(z=-4), "ForearmR": R(z=-4)},
        14: {"Hips": R(), "Waist": R(), "Chest": R(), "Neck": R(), "Head": R(), "Jaw": R(), "UpperArmL": R(), "UpperArmR": R(),
             "ForearmL": R(), "ForearmR": R()},
    }
    m.animation("hurt", 15, ba_keys(15, hu, overlay=drift(14, 2, -10, 15), loop=False), end="Stop")

    # Die (2 s, held): convulses, the head snapping back; the knees go and it folds at the waist; it topples forward like
    # a puppet with its strings cut, the arms flung out and the wire of it whipping; lands, rocks, and goes slack, lying
    # along the carpet on its chest, one arm under it, one out, the legs folded, the head turned; the stain it came out
    # of spreads under it, as if it were going back into the mould.
    die_names = ["Hips", "Waist", "Chest", "Neck", "Head", "Jaw", "ShoulderL", "ShoulderR", "UpperArmL", "UpperArmR", "ForearmL", "ForearmR",
                 "HandL", "HandR", "ThighL", "ThighR", "ShinL", "ShinR"] + wires + fingers

    def bd(hips=R(), waist=R(), chest=R(), neck=R(), head=R(), jaw=R(), shl=R(), shr=R(), ual=R(), uar=R(), fal=R(), far=R(),
           hl=R(), hr=R(), tl=R(), tr=R(), sl=R(), sr=R(), curl=(0, 0), loose=0.0):
        d = {"Hips": hips, "Waist": waist, "Chest": chest, "Neck": neck, "Head": head, "Jaw": jaw, "ShoulderL": shl, "ShoulderR": shr,
             "UpperArmL": ual, "UpperArmR": uar, "ForearmL": fal, "ForearmR": far, "HandL": hl, "HandR": hr,
             "ThighL": tl, "ThighR": tr, "ShinL": sl, "ShinR": sr}
        d.update(fingers_curl("L", curl[0]))
        d.update(fingers_curl("R", curl[1]))
        for i, n in enumerate(wires):
            d[n] = pose((0, 0, loose + 6 * math.sin(i * 1.9)))
        return d

    # (prone: the hips tipped 90 degrees forward and every joint after them given back what the rest pose leans, so
    # the trunk, the legs and the arms lie along the floor, splayed and bent, not propped on anything)
    held = bd(hips=R(z=90, x=12), waist=R(z=-5, x=3), chest=R(z=-10, x=-3), neck=R(z=-34, x=-8), head=R(z=0, x=24, y=10), jaw=R(z=24),
              shl=R(x=-6), shr=R(x=10), ual=R(x=-39, z=26), uar=R(x=44, z=4), fal=R(x=30, z=3), far=R(x=-23, z=13), hl=R(z=10), hr=R(z=-9),
              tl=R(x=-9, z=28), tr=R(x=14, z=20), sl=R(x=-10, z=-12), sr=R(x=8, z=-10), curl=(30, 20), loose=20)
    keys = {
        0: {},
        3: bd(chest=R(z=-10, x=8), neck=R(z=-16), head=R(z=30, x=-20), jaw=R(z=40), ual=R(x=-40, z=10), uar=R(x=36, z=14)),   # the hit
        7: bd(chest=R(z=-6, x=-10), neck=R(z=-10), head=R(z=22, x=24), jaw=R(z=36), ual=R(x=-30, z=-10), uar=R(x=40, z=4)),
        12: bd(hips=R(z=4), waist=R(z=14), chest=R(z=8), neck=R(z=2), head=R(z=10, x=10), jaw=R(z=28), ual=R(x=-30, z=-20), uar=R(x=30, z=-26),
               tl=R(z=-40, x=-8), tr=R(z=-34, x=8), sl=R(z=50), sr=R(z=46)),                                                   # the knees go
        17: bd(hips=R(z=34, x=4), waist=R(z=16), chest=R(z=12), neck=R(z=6), head=R(z=16, x=14), jaw=R(z=30), shl=R(x=-6), shr=R(x=8),
               ual=R(x=-50, z=-6), uar=R(x=44, z=-30), fal=R(z=-14), far=R(z=-24), tl=R(z=-46, x=-10), tr=R(z=-22, x=8), sl=R(z=56), sr=R(z=34),
               curl=(14, 8), loose=10),                                                                                       # topples
        22: dict(held, **{"Hips": R(z=100, x=24), "Head": R(z=10, x=24, y=8)}),                                                # lands, a little past
        27: dict(held, **{"Hips": R(z=93, x=16), "Waist": R(z=-2, x=4)}),                                                       # rocks back
        59: dict(held, **{"Head": R(z=14, x=34, y=10), "Jaw": R(z=22)}),
    }
    def _mid(a, b, u):
        out = {}
        for n in set(a) | set(b):
            pa, pb = a.get(n) or pose(), b.get(n) or pose()
            out[n] = pose(tuple(pa["rot"][i] + (pb["rot"][i] - pa["rot"][i]) * u for i in range(3)),
                          tuple(pa["off"][i] + (pb["off"][i] - pa["off"][i]) * u for i in range(3)))
        return out

    keys[18] = _mid(keys[17], keys[22], 0.2)
    keys[19] = _mid(keys[17], keys[22], 0.4)
    keys[20] = _mid(keys[17], keys[22], 0.6)             # the fall, so the frames between stay on the floor
    soft = ["Stain"] + wires
    death(m, 60, die_names, {f: (k if f else {}) for f, k in keys.items()}, standing=(3, 7), soft=soft)
    # death() settles every root: the stain is a root too, so it gets its own keyframes back
    for f, k in m.animations[-1][2].items():
        g = min(1.0, max(0.0, (f - 14) / 44))
        k["Stain"] = R(st=(0.2 + 0.8 * g, 1, 0.2 + 0.8 * g)) if f == 0 else R(o=(0, 0.45 * min(1.0, f / 14), 0), st=(0.2 + 0.8 * g, 1, 0.2 + 0.8 * g))

    # Emerge (2.5 s): out of a black stain on the carpet. The fingers come up first, then the arms, which reach out and
    # grip the floor; the head pushes up between them, then the shoulders; it hauls the rest of itself out bent double,
    # stands, and snaps upright into its stance with a jerk of the head. The stain shrinks back under it.
    def arms(u, f, hand=0.0):
        """Both arms from the left one's (UpperArm x, y, z) and (Forearm x, z), mirrored."""
        return {"UpperArmL": R(*u), "UpperArmR": R(-u[0], -u[1], u[2]), "ForearmL": R(x=f[0], z=f[1]), "ForearmR": R(x=-f[0], z=f[1]),
                "HandL": R(z=hand), "HandR": R(z=hand)}

    up = arms((-172, 0, 32), (0, 0))
    legs0 = {"ThighL": R(), "ThighR": R(), "ShinL": R(), "ShinR": R()}
    # The arm poses that keep the hands planted on the carpet as the body hauls itself up were solved numerically
    em = {
        0: {"Hips": R(o=(0, -72, 0)), "Waist": R(), "Chest": R(), "Neck": R(z=-10), "Head": R(z=30), "Jaw": R(),
            "ShoulderL": R(), "ShoulderR": R(), **legs0, **up, **fingers_curl("L", -10), **fingers_curl("R", -10),
            "Stain": R(o=(0, 0.45, 0), st=(0.15, 1, 0.15))},
        8: {"Hips": R(o=(0, -66, 0)), "Stain": R(o=(0, 0.45, 0), st=(0.8, 1, 0.8)), **fingers_spread("L", 30), **fingers_spread("R", 30)},
        16: {"Hips": R(o=(0, -59, 0)), **up, "Neck": R(z=-10), "Head": R(z=30)},
        18: {**fingers_spread("L", 44), **fingers_spread("R", 44)},
        # the arms snap over and down: the hands slap onto the carpet either side, the elbows up like a spider's knees
        24: {**fingers_curl("L", -24), **fingers_curl("R", -24)},
        26: {"Hips": R(o=(0, -41, 0)), **arms((-136.6, 0, 46.0), (15.4, -108.8), 30), "Waist": R(), "Chest": R(), "Neck": R(z=-10), "Head": R(z=30)},
        # the head comes up between them, then the shoulders, bent over, pulling
        34: {"Hips": R(o=(0, -34, 0)), "Waist": R(z=10), "Chest": R(z=8), "Neck": R(z=-14), "Head": R(z=10, x=-16),
             **arms((-139.5, 0, 50.9), (-21.7, -162.7), 30), **legs0},
        44: {"Hips": R(o=(0, -24, 0)), "Waist": R(z=26), "Chest": R(z=18), "Neck": R(z=-24), "Head": R(z=-6, x=10),
             **arms((-103.6, 0, 66.3), (-29.0, -161.5), 30), **fingers_curl("L", -24), **fingers_curl("R", -24)},
        54: {"Hips": R(o=(0, -11, 0)), "Waist": R(z=34), "Chest": R(z=22), "Neck": R(z=-26), "Head": R(z=-14, x=6),
             **arms((-65.9, 0, 19.1), (-34.2, -125.1), 30),
             "ThighL": R(z=-70), "ThighR": R(z=-70), "ShinL": R(z=90), "ShinR": R(z=90)},
        56: {"Stain": R(o=(0, 0.45, 0), st=(0.9, 1, 0.9))},
        58: {"Hips": R(o=(0, -5, 0)), "Waist": R(z=26), "Chest": R(z=16), "Neck": R(z=-20), "Head": R(z=-10),
             **arms((-47.5, 0, -7.0), (-98.7, -121.5), 20), **fingers_curl("L", -24), **fingers_curl("R", -24),
             "ThighL": R(z=-45), "ThighR": R(z=-45), "ShinL": R(z=60), "ShinR": R(z=60)},
        # it lets go and stands, bent ...
        61: {"Hips": R(o=(0, -2.5, 0)), "Waist": R(z=18), "Chest": R(z=11), "Neck": R(z=-12), "Head": R(z=-8),
             **arms((0, 0, -14), (0, -8)), **fingers_curl("L", 0), **fingers_curl("R", 0),
             "ThighL": R(z=-30), "ThighR": R(z=-30), "ShinL": R(z=36), "ShinR": R(z=36)},
        64: {"Hips": R(o=(0, -0.5, 0)), "Waist": R(z=10), "Chest": R(z=8), "Neck": R(z=-4), "Head": R(z=-4, x=-30, y=-8),
             **arms((0, 0, -6), (0, -4)), "ThighL": R(z=-8), "ThighR": R(z=-8), "ShinL": R(z=10), "ShinR": R(z=10)},
        66: {"Hips": R(o=(0, -0.5, 0)), "Waist": R(z=10), "Chest": R(z=8), "Neck": R(z=-4), "Head": R(z=-4, x=-30, y=-8)},
        # ... and snaps upright in two frames, the head jerking over the other way and back
        68: {"Hips": R(), "Waist": R(), "Chest": R(), "Neck": R(), "Head": R(x=8, y=4), **arms((0, 0, 0), (0, 0)), **legs0,
             "Stain": R(o=(0, 0.45, 0), st=(0.7, 1, 0.7))},
        72: {"Head": R(x=8, y=4)},
        73: {"Head": R()},
        74: {"Stain": R(st=(0.2, 1, 0.2)), "Hips": R(), "Head": R(), "Jaw": R()},
    }
    m.animation("emerge", 75, ba_keys(75, em, overlay=drift(6, 2, 0, 75), loop=False), end="Stop")

    # Howl (1.5 s, an extra for the hunt's start): it straightens as far as the ceiling lets it, throws the head back,
    # the jaw splitting wide, the arms jerking out from its sides; the noise is in the sounds, the shudder here.
    hw = {
        0: {"Waist": R(), "Chest": R(), "Neck": R(), "Head": R(), "Jaw": R(), "UpperArmL": R(), "UpperArmR": R(),
            **fingers_curl("L", 0), **fingers_curl("R", 0)},
        6: {"Waist": R(z=-6), "Chest": R(z=-8), "Neck": R(z=-14), "Head": R(z=24), "Jaw": R(z=40),
            "UpperArmL": R(x=-24), "UpperArmR": R(x=24), **fingers_spread("L", 40), **fingers_spread("R", 40)},
    }
    for k, fr in enumerate(range(8, 36, 2)):                          # the shudder through the howl
        j = 1 if k % 2 else -1
        hw[fr] = {"Head": R(x=4 * j, z=24 + 2 * j), "Chest": R(z=-8, x=1.5 * j), "Jaw": R(z=40 - 2 * j)}
    hw[38] = {"Waist": R(z=-6), "Chest": R(z=-8), "Neck": R(z=-14), "Head": R(z=24), "Jaw": R(z=40), "UpperArmL": R(x=-24), "UpperArmR": R(x=24),
              **fingers_spread("L", 40), **fingers_spread("R", 40)}
    hw[44] = hw[0]
    m.animation("howl", 45, ba_keys(45, hw, overlay=drift(8, 3, 0, 45), loop=False), end="Stop")
    return m


# ======================================================================== Wretch
# Entity 15, "Wretches": wanderers undone by the Wretched Cycle, the slow work of hunger, thirst and sleeplessness.
# Wikidot: humanoids with "reddish-brown skin that is dry and flaky, covered in holes and pustules secreting a thick
# red-brown substance", skeletal yet strong enough to break through walls. In the last stage "eyelids, lips, and
# cartilage dissolve, forcing the eyes to remain open constantly and roll wildly in their sockets"; "hair loss sets
# in"; "nails and teeth fall out of their natural positions, often regrowing elsewhere in unnatural quantities and
# sizes"; they "ooze a brown sludge-like substance from mouths and other orifices"; and "clothing, supplies, and
# personal belongings will remain on the body, though often mutilated beyond recognition". Speeds run "from a slow
# shamble to sprints surpassing human capabilities"; they gurgle and snarl.
# Design brief: once a person, and you can still tell. A starved body bent nearly double (the spine and shoulder
# blades standing out of the curved back, a waist like a wrist, knees wider than the thighs), the head pushed forward
# on a thin neck. The remains of a wanderer: a t-shirt in rags, jeans torn at the knees and cinched with a belt, one
# sneaker and one bare foot, a backpack strap still over the shoulder with a torn pouch hanging from it. The face is
# where the Cycle shows: no lips (the teeth bare to the gums over a slack, hanging jaw), no nose (two holes), ears
# shrivelled to stubs, lidless bloodshot eyes rolling in deep sockets under a heavy brow, a few strings of hair,
# teeth growing out of a cheek, nails out of a forearm. Pustules stand off the skin as real bumps; the holes are
# pits with sludge running from them. Warm red-brown against the Skin-Stealer's pale yellow, the Duller's grey, the
# Smiler's black; upright on two legs, unlike the Hound. About 27 px tall hunched (1.7 blocks; 30 standing straight).
# Two more looks on the same atlas: "early" (stage 2: still dressed, sallow skin in a scratched-raw rash, eyelids,
# hair, no sludge yet) and "fargone" (deep in stage 3: the shirt gone but for its collar, skin hanging in flaps where
# it was, black rags, darker skin riddled with holes, yellowed eyes).

WRETCH_VARIANTS = {
    "common": dict(skin=(136, 70, 50), dark=(86, 40, 30), raw=(168, 58, 46), flake=(200, 156, 124),
                   holes=0.013, pus=0.009, flakes=0.035, cracks=0.02, scratches=0.4, ooze=1.0, rash=0.0,
                   shirt=(160, 152, 134), trousers=(66, 84, 112), shoe=(176, 168, 150), sole=(74, 68, 62), gear=(56, 66, 72),
                   chest=0.42, belly=0.0, sleeveL=0.34, sleeveR=0.0, thighL=0.94, thighR=0.82, shinL=0.42, shinR=0.0,
                   shoeL=True, shoeR=False, rags="cloth", trouser_rag=True, hair="wisps", eyes="lidless", drool=True,
                   stain=1.0, tears=2, sclera=(212, 166, 148), iris=(84, 60, 36)),
    "early": dict(skin=(180, 126, 102), dark=(136, 90, 72), raw=(192, 84, 70), flake=(220, 188, 164),
                  holes=0.004, pus=0.006, flakes=0.08, cracks=0.02, scratches=1.0, ooze=0.0, rash=0.45,
                  shirt=(78, 96, 128), trousers=(122, 110, 84), shoe=(98, 72, 50), sole=(52, 42, 36), gear=(64, 76, 56),
                  chest=1.0, belly=1.0, sleeveL=0.62, sleeveR=0.62, thighL=1.0, thighR=1.0, shinL=1.0, shinR=1.0,
                  shoeL=True, shoeR=True, rags="cloth", trouser_rag=False, hair="thin", eyes="lidded", drool=False,
                  stain=0.4, tears=1, sclera=(226, 200, 186), iris=(70, 84, 64)),
    "fargone": dict(skin=(110, 50, 36), dark=(64, 26, 20), raw=(152, 40, 34), flake=(172, 118, 92),
                    holes=0.028, pus=0.012, flakes=0.025, cracks=0.035, scratches=0.25, ooze=2.0, rash=0.0,
                    shirt=(50, 44, 40), trousers=(54, 48, 44), shoe=(122, 108, 90), sole=(50, 44, 40), gear=(40, 36, 34),
                    chest=0.0, belly=0.0, sleeveL=0.0, sleeveR=0.0, thighL=0.5, thighR=0.36, shinL=0.0, shinR=0.0,
                    shoeL=True, shoeR=False, rags="skin", trouser_rag=False, hair="none", eyes="yellow", drool=True,
                    stain=1.7, tears=3, sclera=(200, 172, 98), iris=(120, 36, 26)),
}
WV = dict(WRETCH_VARIANTS["common"])

W_HOLE = (26, 9, 7)            # the inside of a hole
W_RIM = (100, 28, 22)          # ... its raw rim
W_CRACK = (48, 22, 16)
W_PUS = (214, 174, 88)         # a pustule's head
W_PUS_HI = (244, 226, 160)
W_SLUDGE = (84, 52, 22)        # the brown sludge
W_SLUDGE_HI = (140, 98, 48)    # ... wet where it catches the light
W_GUM = (112, 34, 34)
W_MAWC = (38, 9, 9)
W_TOOTH = (206, 186, 138)
W_TOOTH_DK = (128, 102, 66)
W_NAIL = (178, 158, 114)
W_NAIL_DK = (104, 88, 60)
W_VEIN = (182, 30, 30)
W_PUPIL = (10, 6, 5)
W_METAL = (152, 148, 138)
W_HAIR = (40, 32, 26)
W_TONGUE = (98, 40, 46)


def w_side(ctx):
    return "R" if ctx.part.name.endswith("R") else "L"


def w_hole(ctx, tx, ty, drip=True):
    """A pit in the skin: a dark hole with a raw rim, sludge running from it down the face."""
    texel(ctx, tx, ty, W_HOLE)
    texel(ctx, tx - 1, ty, W_RIM, 0.55)
    texel(ctx, tx + 1, ty, W_RIM, 0.45)
    texel(ctx, tx, ty - 1, W_RIM, 0.5)
    if drip and WV["ooze"] > 0:
        run = ctx.rng.randint(0, int(1 + 2 * WV["ooze"]))
        for k in range(run):
            texel(ctx, tx, ty + 1 + k, W_SLUDGE, 0.85 - 0.16 * k)
        if run:
            texel(ctx, tx, ty + 1, W_SLUDGE_HI, 0.35)


def w_pimple(ctx, tx, ty):
    head = mix(W_PUS, WV["raw"], 0.55) if WV["rash"] else W_PUS
    texel(ctx, tx, ty, head)
    texel(ctx, tx, ty - 1, W_PUS_HI if not WV["rash"] else head, 0.35)
    for dx, dy, a in ((-1, 0, 0.5), (1, 0, 0.5), (0, 1, 0.55)):
        texel(ctx, tx + dx, ty + dy, WV["raw"], a)


def w_scratches(ctx, count):
    """Claw marks in threes: the itch of the Cycle, scratched until the skin came off."""
    if ctx.w < 4 or ctx.h < 4:
        return
    for _ in range(int(count + ctx.rng.random())):
        u0, v0 = ctx.rng.uniform(0.0, 0.6), ctx.rng.uniform(0.0, 0.6)
        du, dv = ctx.rng.uniform(0.15, 0.4), ctx.rng.uniform(0.25, 0.5)
        col = WV["raw"] if WV["rash"] else mix(WV["raw"], WV["dark"], 0.4)
        for k in range(3):
            off = k * 1.0 / ctx.w
            line(ctx, u0 + off, v0, u0 + off + du, v0 + dv, col, 0.7)


def w_skin(ctx, k=1.0, base=None):
    """Dry, flaking, cracked red-brown skin, pocked with holes that weep sludge and studded with pustules."""
    v = WV
    base = base or v["skin"]
    fill(ctx, base, 0.05)
    if ctx.face not in ("up", "down") and ctx.h > 2:                       # a little darker toward the bottom
        px = ctx.img.load()
        for yy in range(ctx.h):
            k_ = 1.06 - 0.16 * yy / (ctx.h - 1)
            for xx in range(ctx.w):
                c = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = clamp((c[0] * k_, c[1] * k_, c[2] * k_)) + (255,)
    blotch(ctx, v["dark"], 2, 1.5, 4.0, 0.35)
    blotch(ctx, mix(base, v["flake"], 0.5), 1, 1.5, 3.5, 0.28)
    if v["rash"]:
        blotch(ctx, v["raw"], 2, 1.0, 3.0, v["rash"])
    elif ctx.rng.random() < 0.45:
        blotch(ctx, v["raw"], 1, 1.0, 2.5, 0.4)
    area = ctx.w * ctx.h
    side = ctx.face not in ("up", "down")
    for _ in range(int(area * v["flakes"] * k + ctx.rng.random())):        # flakes: the lifted edge's shadow below
        tx, ty = ctx.rng.randrange(ctx.w), ctx.rng.randrange(ctx.h)
        texel(ctx, tx, ty, v["flake"], 0.75)
        texel(ctx, tx + 1, ty, v["flake"], 0.3)
        texel(ctx, tx, ty + 1, v["dark"], 0.5)
    for _ in range(int(area * v["cracks"] * k + ctx.rng.random())):         # cracks: short jagged lines
        tx, ty = ctx.rng.randrange(ctx.w), ctx.rng.randrange(ctx.h)
        for _ in range(ctx.rng.randint(2, 4)):
            texel(ctx, tx, ty, W_CRACK, 0.7)
            texel(ctx, tx, ty - 1, v["flake"], 0.25)
            if ctx.rng.random() < 0.5:
                tx += ctx.rng.choice((-1, 1))
            else:
                ty += 1
    for _ in range(int(area * v["holes"] * k + ctx.rng.random() * 0.7)):
        w_hole(ctx, ctx.rng.randrange(ctx.w), ctx.rng.randrange(ctx.h), side)
    for _ in range(int(area * v["pus"] * k + ctx.rng.random() * 0.5)):
        w_pimple(ctx, ctx.rng.randrange(ctx.w), ctx.rng.randrange(ctx.h))


def w_cloth(ctx, colour, stain=None):
    """Worn cloth: a weave, grime darker toward the bottom, sludge and old blood soaked in."""
    stain = WV["stain"] if stain is None else stain
    fill(ctx, colour, 0.05)
    vlines(ctx, shade(colour, 0.86), 2, start=ctx.rng.randint(0, 1), alpha=0.25)
    if ctx.face not in ("up", "down"):
        px = ctx.img.load()
        for yy in range(ctx.h):
            t = yy / max(1, ctx.h - 1)
            for xx in range(ctx.w):
                old = px[ctx.x + xx, ctx.y + yy]
                px[ctx.x + xx, ctx.y + yy] = mix(old[:3], shade(colour, 0.6), 0.3 * t) + (255,)
    blotch(ctx, mix(colour, (120, 104, 80), 0.6), 1, 1.5, 3.5, 0.35)                 # dust
    blotch(ctx, W_SLUDGE, int(1 + stain), 1.0, 3.0, min(0.85, 0.4 * stain))         # sludge soaked in
    if ctx.rng.random() < 0.5 * stain:
        blotch(ctx, (70, 24, 20), 1, 1.0, 2.5, 0.4)                                  # old blood
    speckle(ctx, shade(colour, 1.18), 0.04)


def cloth_over(ctx, colour, limit, tears=0, stain=None, fray=True):
    """Cloth over the skin already painted, from the top of the face down to `limit` (a fraction of its height) with a
    torn, uneven edge; `tears` holes show the skin through. Up faces are covered if any is, down faces only if all."""
    if limit <= 0:
        return
    if ctx.face == "down" and limit < 1:
        return
    tmp = rig.Ctx()
    tmp.img = rig.Image.new("RGBA", (ctx.w, ctx.h), (0, 0, 0, 0))
    tmp.draw = rig.ImageDraw.Draw(tmp.img)
    tmp.x = tmp.y = 0
    tmp.w, tmp.h, tmp.face, tmp.part, tmp.rng = ctx.w, ctx.h, ctx.face, ctx.part, ctx.rng
    w_cloth(tmp, colour, stain)
    src, dst = tmp.img.load(), ctx.img.load()
    full_cover = limit >= 1 or ctx.face == "up"
    edge, e = [], limit * ctx.h + ctx.rng.uniform(-1, 1)
    for xx in range(ctx.w):
        e += ctx.rng.choice((-1, 0, 0, 1)) * (1 if ctx.h > 4 else 0.5)
        e = max(limit * ctx.h - 2.5, min(limit * ctx.h + 2.5, e))
        edge.append(ctx.h if full_cover else int(round(e)))
    holes = []
    for _ in range(int(tears + ctx.rng.random() * 0.5)):
        if ctx.w >= 4 and ctx.h >= 4:
            holes.append((ctx.rng.uniform(1, ctx.w - 1), ctx.rng.uniform(1, ctx.h - 1), ctx.rng.uniform(0.8, 1.8)))
    for xx in range(ctx.w):
        for yy in range(min(ctx.h, edge[xx])):
            d = min([math.hypot(xx + 0.5 - hx, (yy + 0.5 - hy) * 1.3) / hr for hx, hy, hr in holes] or [9])
            if d < 1:
                continue                                                              # a tear: the skin shows
            c = src[xx, yy][:3]
            if d < 1.5 or (fray and yy >= edge[xx] - 1 and not full_cover):
                c = mix(c, shade(colour, 1.35) if ctx.rng.random() < 0.5 else shade(colour, 0.6), 0.6)   # frayed
            dst[ctx.x + xx, ctx.y + yy] = c + (255,)
        if not full_cover and 0 <= edge[xx] < ctx.h:                                 # the cloth's shadow on the skin
            old = dst[ctx.x + xx, ctx.y + edge[xx]]
            dst[ctx.x + xx, ctx.y + edge[xx]] = mix(old[:3], WV["dark"], 0.45) + (255,)


def w_rows(ctx, rows, colour, alpha=1.0):
    for ty in rows:
        texrow(ctx, ty, 0, -1, colour, alpha)


# ---- the body ----

def w_hips(ctx):
    """Trousers hanging off the pelvis, a belt cinched three holes past its last, the spare end hanging."""
    v = WV
    w_skin(ctx)
    w_cloth(ctx, v["trousers"])
    if ctx.face in ("west", "north", "south", "east"):
        w_rows(ctx, (0, 1), (58, 40, 28))                                               # the belt
        texrow(ctx, 1, 0, -1, (40, 26, 18), 0.5)
        if ctx.face == "west":
            cx = ctx.w // 2 + 1
            for tx in (cx - 1, cx):
                texel(ctx, tx, 0, W_METAL)
                texel(ctx, tx, 1, W_METAL, 0.8)
            for ty in range(2, 5):
                texel(ctx, cx + 2, ty, (58, 40, 28))                                    # the spare end, hanging
            texel(ctx, cx + 2, 3, (30, 20, 14))                                         # ... the hole punched by hand
            line(ctx, 0.5, 0.35, 0.5, 1.0, shade(v["trousers"], 0.7), 0.5)              # the fly
        if ctx.face == "east":
            texel(ctx, ctx.w // 2, 0, (30, 20, 14))
    if ctx.face == "up":
        fill(ctx, v["dark"], 0.05)


def w_belly(ctx):
    """A waist like a wrist: the skin sunk between the ribs and the hips, a navel stretched sideways."""
    v = WV
    w_skin(ctx)
    if ctx.face == "west":
        texel(ctx, ctx.w // 2, ctx.h * 2 // 3, v["dark"])
        texel(ctx, ctx.w // 2 - 1, ctx.h * 2 // 3, v["dark"], 0.5)
        line(ctx, 0.0, 0.0, 0.2, 1.0, v["dark"], 0.4)                                   # the sunken flanks
        line(ctx, 1.0, 0.0, 0.8, 1.0, v["dark"], 0.4)
    elif ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.15, 1.0, 0.1, v["flake"], 0.35)                                # the lowest rib
        line(ctx, 0.0, 0.25, 1.0, 0.2, v["dark"], 0.5)
    cloth_over(ctx, v["shirt"], v["belly"], tears=v["tears"] - 1)


def w_chest(ctx):
    """The ribcage under dry skin: every rib, collarbones, a hollow sternum, scratched raw; the shirt in rags on top."""
    v = WV
    w_skin(ctx)
    if ctx.face in ("west", "north", "south"):
        for i in range(2, ctx.h - 1, 2):                                                 # ribs and the hollows between
            if ctx.face == "west":
                line(ctx, 0.0, i / ctx.h + 0.06, 0.42, i / ctx.h, v["dark"], 0.55)
                line(ctx, 0.58, i / ctx.h, 1.0, i / ctx.h + 0.06, v["dark"], 0.55)
                line(ctx, 0.0, (i + 1) / ctx.h + 0.06, 0.42, (i + 1) / ctx.h, v["flake"], 0.3)
                line(ctx, 0.58, (i + 1) / ctx.h, 1.0, (i + 1) / ctx.h + 0.06, v["flake"], 0.3)
            else:
                texrow(ctx, i, 0, -1, v["dark"], 0.5)
                texrow(ctx, i + 1, 0, -1, v["flake"], 0.25)
        if ctx.face == "west":
            line(ctx, 0.5, 0.15, 0.5, 0.9, v["dark"], 0.6)                               # the sternum's hollow
            line(ctx, 0.05, 0.08, 0.45, 0.02, v["flake"], 0.6)                           # collarbones
            line(ctx, 0.55, 0.02, 0.95, 0.08, v["flake"], 0.6)
        w_scratches(ctx, v["scratches"])
    elif ctx.face == "east":
        line(ctx, 0.1, 0.25, 0.32, 0.6, v["dark"], 0.5)                                  # under the shoulder blades
        line(ctx, 0.9, 0.25, 0.68, 0.6, v["dark"], 0.5)
        w_scratches(ctx, v["scratches"])
    cloth_over(ctx, v["shirt"], v["chest"], tears=v["tears"])
    if v["chest"] >= 1 and ctx.face == "west":                                           # a faded print on the shirt
        for tx, ty in ((3, 3), (4, 3), (5, 3), (4, 4), (3, 5), (5, 5)):
            texel(ctx, tx, ty, shade(v["shirt"], 1.4), 0.5)


def w_spine(ctx):
    """The spine through the skin of the bent back, a knuckle at every other texel."""
    v = WV
    w_skin(ctx, 0.6, base=mix(v["skin"], v["flake"], 0.25))
    if ctx.face not in ("up", "down"):
        for ty in range(0, ctx.h, 2):
            texrow(ctx, ty, 0, -1, mix(v["flake"], v["skin"], 0.3), 0.7)
            texrow(ctx, ty + 1, 0, -1, v["dark"], 0.55)
    limit = v["chest"] if ctx.part.name == "SpineHigh" else v["belly"]
    cloth_over(ctx, v["shirt"], limit, fray=False)


def w_blade(ctx):
    v = WV
    w_skin(ctx, 0.6, base=mix(v["skin"], v["flake"], 0.2))
    if ctx.face in ("east", "down"):
        texrow(ctx, -1, 0, -1, v["dark"], 0.6)
    cloth_over(ctx, v["shirt"], v["chest"] * 1.6, fray=False)


def w_collar(ctx):
    """What is left of the shirt: its ribbed collar, filthy, still round the neck."""
    v = WV
    w_cloth(ctx, v["shirt"], WV["stain"] * 1.3)
    if ctx.face not in ("up", "down"):
        texrow(ctx, 0, 0, -1, shade(v["shirt"], 0.75), 0.5)
        ragged(ctx, 1)
    if ctx.face == "up":
        fill(ctx, v["dark"], 0.05)


def w_rag(ctx):
    """A strip of shirt hanging from the ribs; on the far-gone look, a flap of the skin itself, raw underneath."""
    v = WV
    if v["rags"] == "skin":
        if ctx.face in ("north", "east") or (ctx.face == "west" and ctx.part.name == "RagBack"):
            fill(ctx, v["raw"], 0.12)                                                     # the inside of the flap
            blotch(ctx, W_RIM, 2, 1.0, 2.5, 0.5)
            blotch(ctx, W_SLUDGE, 1, 1.0, 2.5, 0.5)
        else:
            w_skin(ctx, 1.4)
        texrow(ctx, 0, 0, -1, W_RIM, 0.5)
        ragged(ctx, 4)
        return
    w_cloth(ctx, v["shirt"], v["stain"] * 1.2)
    if ctx.face not in ("up", "down"):
        if ctx.w >= 3 and ctx.h >= 4 and ctx.rng.random() < 0.6:
            tx, ty = ctx.rng.randrange(1, ctx.w - 1), ctx.rng.randrange(1, ctx.h - 2)
            clear(ctx, tx, ty)                                                           # a hole worn through
        ragged(ctx, 2 if v["chest"] >= 1 else 4)


def w_strap(ctx):
    """Backpack webbing over the shoulder: nylon, stitched along both edges, the slider still on it."""
    v = WV
    w_cloth(ctx, v["gear"], v["stain"] * 0.8)
    if ctx.face in ("west", "east"):
        line(ctx, 0.2, 0.0, 0.2, 1.0, shade(v["gear"], 1.35), 0.4)
        line(ctx, 0.8, 0.0, 0.8, 1.0, shade(v["gear"], 1.35), 0.4)
    if ctx.face == "up":
        fill(ctx, mix(v["gear"], (140, 130, 116), 0.2), 0.08)                             # worn pale over the shoulder


def w_metal(ctx):
    fill(ctx, W_METAL, 0.08)
    blotch(ctx, (110, 70, 40), 1, 0.8, 1.5, 0.5)                                         # rust


def w_pouch(ctx):
    """All that is left of the backpack: a pouch torn open, its zip burst, a keyring tag still on its pull."""
    v = WV
    w_cloth(ctx, v["gear"], v["stain"])
    if ctx.face == "up":
        rect(ctx, 0.15, 0.2, 0.85, 0.8, (18, 14, 12))                                     # torn open
        texel(ctx, 0, ctx.h // 2, W_METAL, 0.8)
    elif ctx.face == "east":
        line(ctx, 0.0, 0.2, 1.0, 0.2, W_METAL, 0.7)                                       # the zip
        texel(ctx, ctx.w // 3, 1, (196, 40, 36))                                           # the keyring tag: red ...
        texel(ctx, ctx.w // 3, 2, (226, 224, 214))                                         # ... and white
        texel(ctx, ctx.w // 3 + 1, 2, (196, 40, 36))
        if ctx.w >= 4:
            rect(ctx, 0.55, 0.5, 0.85, 0.85, (22, 18, 14))                                 # a rip in the side
    elif ctx.face in ("north", "south"):
        line(ctx, 0.0, 0.2, 1.0, 0.25, shade(v["gear"], 0.6), 0.5)
    if ctx.face in ("north", "south", "east", "west"):
        ragged(ctx, 1)


def w_pustule(ctx):
    """A pustule standing off the skin: a yellow head (on the early look, an angry red bump), a raw base."""
    v = WV
    head = mix(W_PUS, v["raw"], 0.6) if v["rash"] else W_PUS
    fill(ctx, head, 0.08, face_shade=False)
    if ctx.face == "up":
        texel(ctx, 0, 0, W_PUS_HI if not v["rash"] else shade(head, 1.2), 0.8)
    elif ctx.face != "down":
        texrow(ctx, -1, 0, -1, v["raw"], 0.8)
        texel(ctx, 0, 0, W_PUS_HI if not v["rash"] else shade(head, 1.2), 0.5)
        if v["ooze"] > 0.5 and ctx.rng.random() < 0.5:
            texel(ctx, ctx.w - 1, ctx.h - 1, W_SLUDGE, 0.8)


# ---- head and face ----

def w_hair_on(ctx, rows=None):
    """Hair on a scalp face, as the look has it: thinning (early), a few roots (common), none."""
    v = WV
    if v["hair"] == "none":
        return
    chance = 0.75 if v["hair"] == "thin" else 0.12
    rows = range(ctx.h) if rows is None else rows
    for ty in rows:
        for tx in range(ctx.w):
            if ctx.rng.random() < chance:
                texel(ctx, tx, ty, W_HAIR if ctx.rng.random() < 0.8 else mix(W_HAIR, (110, 100, 90), 0.5), 0.9)
    if v["hair"] == "thin":
        blotch(ctx, v["skin"], 1, 1.0, 2.0, 0.8)                                          # a bald patch


def w_head(ctx):
    """The skull. In front, the deep sockets the eyes sit in; temples sunk; the scalp as the look has it."""
    v = WV
    w_skin(ctx)
    if ctx.face == "west":
        fill(ctx, (34, 14, 12), 0.15, face_shade=False)                                    # the sockets, deep
        blotch(ctx, W_RIM, 2, 1.0, 2.0, 0.4)
    elif ctx.face == "down":
        fill(ctx, W_MAWC, 0.1, face_shade=False)                                           # the roof of the mouth
        texrow(ctx, 0, 0, -1, W_GUM, 0.7)
    elif ctx.face in ("north", "south"):
        blotch(ctx, v["dark"], 1, 1.5, 2.5, 0.55)                                          # sunken temples
        w_hair_on(ctx, range(0, ctx.h // 3))
        if v["hair"] != "thin":
            texrow(ctx, ctx.h // 3, 0, -1, v["dark"], 0.2)
    elif ctx.face == "east":
        w_hair_on(ctx, range(0, ctx.h * 2 // 3))
    elif ctx.face == "up":
        w_hair_on(ctx)
        if v["hair"] == "none":
            w_hole(ctx, ctx.w // 2, ctx.h // 2, False)


def w_crown(ctx):
    """The top of the skull, narrower than the head: the scalp as the look has it."""
    v = WV
    w_skin(ctx, 0.8)
    if ctx.face == "up":
        w_hair_on(ctx)
    elif ctx.face != "down":
        w_hair_on(ctx, range(ctx.h))


def w_brow(ctx):
    """The forehead and a heavy brow over the sockets, bone pushing through the skin at its edge."""
    v = WV
    w_skin(ctx, 0.8)
    if ctx.face == "west":
        texrow(ctx, -1, 0, -1, mix(v["flake"], v["skin"], 0.2), 0.7)                       # the brow ridge
        texrow(ctx, -2, 0, -1, v["dark"], 0.35)
        line(ctx, 0.1, 0.35, 0.9, 0.3, v["dark"], 0.35)                                    # a furrow
        if v["eyes"] == "lidded":
            w_scratches(ctx, 0.5)
    elif ctx.face == "down":
        fill(ctx, (30, 12, 10), 0.1, face_shade=False)                                     # the socket's ceiling
    elif ctx.face == "up":
        w_hair_on(ctx)


def w_face(ctx):
    """Below the eyes: hollows; where the nose was, two holes; the upper lip gone, the gums and teeth bare."""
    v = WV
    w_skin(ctx, 0.5)
    if ctx.face == "west":
        w, h = ctx.w, ctx.h
        texrow(ctx, 0, 0, w // 2 - 2, v["dark"], 0.6)                                       # under-eye hollows
        texrow(ctx, 0, w // 2 + 2, w - 1, v["dark"], 0.6)
        cx = w // 2
        for tx in (cx - 1, cx):                                                             # the nasal holes
            texel(ctx, tx, 0, W_HOLE)
            texel(ctx, tx, 1, W_HOLE, 0.85)
        texel(ctx, cx - 1, 2, W_RIM, 0.6)
        texel(ctx, cx, 2, W_RIM, 0.6)
        if v["ooze"] > 0:
            texel(ctx, cx, 2, W_SLUDGE, 0.8)
        for tx in (1, w - 2):                                                               # cheekbones under the skin
            texel(ctx, tx, 0, mix(v["flake"], v["skin"], 0.25), 0.8)
        texrow(ctx, 1, 0, 0, v["dark"], 0.6)                                                # hollow cheeks
        texrow(ctx, 1, w - 1, w - 1, v["dark"], 0.6)
        texrow(ctx, h - 2, 0, -1, W_GUM, 0.7)                                               # the gum, no lip
        texrow(ctx, h - 1, 0, -1, W_GUM)
        for tx in range(1, w - 1, 3):
            texel(ctx, tx, h - 1, W_MAWC, 0.8)                                              # the gaps the teeth left
        if v["eyes"] == "lidded":                                                           # stage 2: a lip, cracked
            texrow(ctx, h - 2, 1, w - 2, mix(v["raw"], v["skin"], 0.4))
            texel(ctx, w // 3, h - 2, W_CRACK)
    elif ctx.face in ("north", "south"):
        blotch(ctx, v["dark"], 1, 1.0, 2.0, 0.5)
        texrow(ctx, -1, 0, -1, W_GUM, 0.7)
    elif ctx.face == "down":
        fill(ctx, W_GUM, 0.1, face_shade=False)


def w_bridge(ctx):
    v = WV
    w_skin(ctx, 0.4, base=mix(v["skin"], v["flake"], 0.2))
    if ctx.face == "west":
        texrow(ctx, -1, 0, -1, W_RIM, 0.7)                                                  # the cartilage gone below


def w_eye(ctx):
    """A lidless eye, bloodshot: two texels of white, a vein, and a pupil looking somewhere the other eye is not.
    Early, a heavy lid still over the top; far gone, yellowed."""
    v = WV
    fill(ctx, v["sclera"], 0.04, face_shade=False)
    if ctx.face == "west":
        right = w_side(ctx) == "R"
        px_, py_ = (1, 0) if right else (0, 1)                                                # the pupils diverge
        texel(ctx, px_, py_, W_PUPIL)
        texel(ctx, 1 - px_, 1 - py_, W_VEIN, 0.45 if v["eyes"] != "yellow" else 0.7)
        if v["eyes"] == "lidded":
            texrow(ctx, 0, 0, -1, mix(v["skin"], v["dark"], 0.25), 0.85)                       # the lid, heavy
            texel(ctx, px_, 1, v["iris"])
    else:
        texel(ctx, 0, ctx.h - 1, W_VEIN, 0.6)
        if v["eyes"] == "lidded" and ctx.face != "down":
            texrow(ctx, 0, 0, -1, mix(v["skin"], v["dark"], 0.25))


def w_ear(ctx):
    """An ear shrivelled to a stub, its cartilage gone."""
    v = WV
    w_skin(ctx, 0.5, base=v["dark"])
    if ctx.face == "south" or ctx.face == "north":
        texel(ctx, ctx.w // 2, ctx.h // 2, W_HOLE)
        texrow(ctx, 0, 0, -1, W_RIM, 0.6)
        ragged(ctx, 1)


def w_jaw(ctx):
    """The jaw: bare gum and teeth on top (no lip), a chin streaked with sludge, a dry tongue in the floor."""
    v = WV
    w_skin(ctx, 0.7)
    if ctx.face == "west":
        texrow(ctx, 0, 0, -1, W_GUM)
        texrow(ctx, 1, 0, -1, W_GUM, 0.6)
        if v["eyes"] == "lidded":
            texrow(ctx, 1, 0, -1, mix(v["raw"], v["skin"], 0.4))
        if v["ooze"] > 0:
            for tx in (1, ctx.w - 2, ctx.w // 2):                                           # sludge from the mouth
                for ty in range(1, 1 + ctx.rng.randint(1, ctx.h - 1)):
                    texel(ctx, tx, ty, W_SLUDGE, 0.85)
                texel(ctx, tx, 1, W_SLUDGE_HI, 0.4)
    elif ctx.face == "up":
        fill(ctx, W_MAWC, 0.1, face_shade=False)
        rect(ctx, 0.15, 0.25, 0.75, 0.75, W_TONGUE)                                          # the tongue, dry
        texel(ctx, ctx.w // 3, ctx.h // 2, W_CRACK)
        texrow(ctx, 0, 0, -1, W_GUM)
        texrow(ctx, -1, 0, -1, W_GUM)
        if v["ooze"] > 0:
            blotch(ctx, W_SLUDGE, 1, 1.0, 2.0, 0.7)
    elif ctx.face == "down":
        blotch(ctx, v["dark"], 1, 1.5, 3, 0.5)
    elif ctx.face in ("north", "south"):
        texrow(ctx, 0, 0, -1, W_GUM, 0.6)


def w_maw(ctx):
    fill(ctx, W_MAWC, 0.15, face_shade=False)
    blotch(ctx, (4, 2, 2), 1, 1.0, 2.5, 0.8)
    if ctx.face == "west":
        texrow(ctx, 0, 0, -1, W_GUM, 0.6)


def w_tooth(ctx):
    """A tooth, stained; brown toward the gum (on the far-gone look, brown all through)."""
    base = mix(W_TOOTH, W_TOOTH_DK, 0.65 if WV["eyes"] == "yellow" else 0.15 + ctx.rng.random() * 0.4)
    fill(ctx, base, 0.05, face_shade=False)
    if ctx.face not in ("up", "down"):
        up = ctx.part.tag.get("upper", True)
        texrow(ctx, 0 if up else -1, 0, -1, W_TOOTH_DK, 0.8)
        texrow(ctx, -1 if up else 0, 0, -1, shade(base, 1.08), 0.6)


def w_hair(ctx):
    """A few strings of hair left: dark strands with gaps between, the ends ragged. None at all far gone."""
    v = WV
    if v["hair"] == "none":
        ctx.draw.rectangle([ctx.x, ctx.y, ctx.x + ctx.w - 1, ctx.y + ctx.h - 1], fill=(0, 0, 0, 0))
        return
    fill(ctx, W_HAIR, 0.15, face_shade=False)
    keep = 0.8 if v["hair"] == "thin" else 0.5
    for xx in range(ctx.w):
        if ctx.rng.random() > keep:
            for yy in range(ctx.h):
                clear(ctx, xx, yy)
        elif ctx.rng.random() < 0.3:
            for yy in range(ctx.h):
                texel(ctx, xx, yy, (82, 72, 62), 0.6)
    ragged(ctx, max(2, ctx.h // 2))


def w_drool(ctx):
    """A rope of brown sludge from the mouth, wet, with a drop at its end. Stage 2 has none."""
    if not WV["drool"]:
        ctx.draw.rectangle([ctx.x, ctx.y, ctx.x + ctx.w - 1, ctx.y + ctx.h - 1], fill=(0, 0, 0, 0))
        return
    fill(ctx, W_SLUDGE, 0.1, face_shade=False)
    if ctx.face not in ("up", "down"):
        line(ctx, 0.3, 0.0, 0.3, 0.8, W_SLUDGE_HI, 0.7)
        if ctx.w > 1:
            for yy in range(ctx.h * 2 // 3, ctx.h - 1):
                clear(ctx, ctx.w - 1, yy)


def w_trouser_rag(ctx):
    v = WV
    if not v["trouser_rag"]:
        ctx.draw.rectangle([ctx.x, ctx.y, ctx.x + ctx.w - 1, ctx.y + ctx.h - 1], fill=(0, 0, 0, 0))
        return
    w_cloth(ctx, v["trousers"])
    vlines(ctx, shade(v["trousers"], 1.3), 3, alpha=0.3)
    ragged(ctx, 4)


# ---- limbs ----

def w_arm(ctx):
    """The upper arm: bone and skin, the shoulder's knob, a sleeve (or what is left of it)."""
    v = WV
    w_skin(ctx)
    if ctx.face in ("west", "north", "south", "east"):
        texrow(ctx, 0, 0, -1, mix(v["flake"], v["skin"], 0.3), 0.6)                        # the knob of the shoulder
        texrow(ctx, -1, 0, -1, v["dark"], 0.5)
        w_scratches(ctx, v["scratches"] * 0.7)
    cloth_over(ctx, v["shirt"], v["sleeve" + w_side(ctx)], tears=v["tears"] - 1)


def w_forearm(ctx):
    """A forearm of two bones and tendons; the elbow a knot; on the far-gone looks, a nail growing out of it."""
    v = WV
    w_skin(ctx)
    if ctx.face in ("west", "north", "south", "east"):
        texrow(ctx, 0, 0, -1, v["dark"], 0.5)
        texrow(ctx, 1, 0, -1, v["flake"], 0.3)
        line(ctx, 0.35, 0.15, 0.3, 0.9, v["dark"], 0.35)                                     # between the bones
        texrow(ctx, -2, 0, -1, mix(v["flake"], v["skin"], 0.3), 0.5)                          # the wrist's knobs
        w_scratches(ctx, v["scratches"])
    if ctx.face == "east":
        texrow(ctx, 0, 0, -1, mix(v["flake"], v["skin"], 0.2), 0.8)                           # the elbow
        if v["eyes"] != "lidded" and w_side(ctx) == "L":
            for ty in (ctx.h // 2, ctx.h // 2 + 1):
                texrow(ctx, ty, 1, 2, W_NAIL)                                                  # a nail, grown wrong
            texrow(ctx, ctx.h // 2 + 2, 1, 2, W_RIM, 0.7)


def w_hand(ctx):
    v = WV
    w_skin(ctx, 0.7)
    if ctx.face == "west":
        for tx in range(0, ctx.w, 2):
            line(ctx, (tx + 0.5) / ctx.w, 0.1, (tx + 0.5) / ctx.w, 0.9, v["flake"], 0.35)  # tendons
    if ctx.face in ("west", "east", "north", "south"):
        texrow(ctx, -1, 0, -1, mix(v["flake"], v["skin"], 0.2), 0.6)                         # knuckles
    if ctx.face == "down":
        fill(ctx, mix(v["dark"], (60, 50, 40), 0.4), 0.08)


def w_finger(ctx):
    """A long bony finger ending in a long cracked nail (a claw now)."""
    v = WV
    w_skin(ctx, 0.4)
    if ctx.face in ("west", "east", "north", "south"):
        texrow(ctx, ctx.h // 3, 0, -1, v["dark"], 0.5)                                       # knuckles
        texrow(ctx, ctx.h * 2 // 3 - 1, 0, -1, v["dark"], 0.4)
        nail = W_NAIL if v["eyes"] != "yellow" else mix(W_NAIL, W_NAIL_DK, 0.5)
        for ty in range(ctx.h - 2, ctx.h):
            texrow(ctx, ty, 0, -1, nail)
        texrow(ctx, -1, 0, -1, W_NAIL_DK)
        if ctx.face == "west":
            texel(ctx, 0, ctx.h - 2, W_CRACK, 0.6)
    elif ctx.face == "down":
        fill(ctx, W_NAIL_DK, 0.05)


def w_thigh(ctx):
    v = WV
    w_skin(ctx)
    side = w_side(ctx)
    cloth_over(ctx, v["trousers"], v["thigh" + side], tears=v["tears"])
    if v["thigh" + side] > 0 and ctx.face in ("west", "north", "south", "east"):
        vlines(ctx, shade(v["trousers"], 1.25), 4, start=1, alpha=0.12)
    if ctx.face == "west" and v["thigh" + side] > 0.8 and v["shin" + side] < 1:               # torn open at the knee
        rect(ctx, 0.2, 0.86, 0.8, 1.0, v["skin"])
        texrow(ctx, -1, 0, -1, mix(v["flake"], v["skin"], 0.3), 0.6)


def w_shin(ctx):
    v = WV
    w_skin(ctx)
    if ctx.face == "west":
        line(ctx, 0.5, 0.1, 0.5, 0.95, mix(v["flake"], v["skin"], 0.2), 0.55)                 # the shin bone
    if ctx.face in ("west", "north", "south", "east"):
        texrow(ctx, -2, 0, -1, mix(v["flake"], v["skin"], 0.3), 0.5)                          # ankle knobs
        w_scratches(ctx, v["scratches"] * 0.5)
    cloth_over(ctx, v["trousers"], v["shin" + w_side(ctx)], tears=1)


def w_knee(ctx):
    """A knee wider than the thigh above it, scraped from crawling."""
    v = WV
    w_skin(ctx, 1.0, base=mix(v["skin"], v["flake"], 0.15))
    blotch(ctx, v["raw"], 1, 1.0, 2.0, 0.6)
    if v["shin" + w_side(ctx)] > 0:
        w_cloth(ctx, v["trousers"])
        if v["shin" + w_side(ctx)] < 1:
            blotch(ctx, v["skin"], 1, 1.0, 1.8, 0.9)                                          # worn through


def w_foot(ctx):
    """A sneaker (boots, early), stained and split; or a bare foot with long cracked toenails."""
    v = WV
    side = w_side(ctx)
    if v["shoe" + side]:
        fill(ctx, v["shoe"], 0.06)
        blotch(ctx, W_SLUDGE, 2, 1.0, 3.0, 0.45 * v["stain"])
        blotch(ctx, (90, 30, 24), 1, 1.0, 2.0, 0.3)
        if ctx.face in ("north", "south", "west", "east"):
            texrow(ctx, -1, 0, -1, v["sole"])
            if ctx.h > 2:
                texrow(ctx, -2, 0, -1, mix(v["sole"], v["shoe"], 0.5))
        if ctx.face == "up":
            for tx in range(ctx.w // 3, ctx.w * 2 // 3, 2):                                   # laces
                texel(ctx, tx, ctx.h // 2, (220, 214, 200) if v["shoe"][0] > 150 else (40, 30, 24))
                texel(ctx, tx + 1, ctx.h // 2 - 1, shade(v["shoe"], 0.6))
                texel(ctx, tx + 1, ctx.h // 2 + 1, shade(v["shoe"], 0.6))
            rect(ctx, 0.0, 0.0, 0.25, 1.0, shade(v["shoe"], 0.92))                            # the toe cap
            rect(ctx, 0.85, 0.15, 1.0, 0.85, (24, 18, 14))                                    # the opening, the ankle
        if ctx.face == "west" and v["eyes"] == "yellow":
            texrow(ctx, -2, 1, -2, (20, 12, 10))                                              # the sole split open
            texel(ctx, 2, -2, v["skin"])
            texel(ctx, 3, -2, v["skin"])
        if ctx.face == "down":
            fill(ctx, v["sole"], 0.08)
        return
    w_skin(ctx, 0.8)
    if ctx.face == "up":
        for ty in range(0, ctx.h, 2):                                                          # the toes, long nails
            texel(ctx, 0, ty, W_NAIL)
            texel(ctx, 1, ty, W_NAIL, 0.6)
            texel(ctx, 2, ty, v["dark"], 0.5)
        line(ctx, 0.3, 0.5, 0.9, 0.5, mix(v["flake"], v["skin"], 0.3), 0.45)                   # the tendons, the bones
    elif ctx.face == "west":
        for tx in range(0, ctx.w, 2):
            texel(ctx, tx, 0, W_NAIL)
            texel(ctx, tx + 1, 0, v["dark"], 0.6)
        texrow(ctx, -1, 0, -1, (54, 44, 36), 0.7)
    elif ctx.face == "down":
        fill(ctx, (62, 48, 38), 0.1)                                                           # grime
    else:
        texrow(ctx, -1, 0, -1, (60, 48, 40), 0.6)


# ---- the model ----

W_THIGH_REST, W_SHIN_REST, W_FOOT_REST = -16.0, 28.0, -12.0
W_SHIFT = -0.4                 # the bent knees lift the feet: the whole model is moved down onto the floor
W_HIP_P, W_THIGH_P, W_KNEE_P, W_ANKLE_P = (0.0, 14.4), (0.0, 14.3), (0.0, 7.6), (0.0, 1.0)


def _w_rot(pt, piv, deg):
    a = math.radians(deg)
    x, y = pt[0] - piv[0], pt[1] - piv[1]
    return (piv[0] + x * math.cos(a) - y * math.sin(a), piv[1] + x * math.sin(a) + y * math.cos(a))


def _w_ankle(hip, thigh, shin):
    """Where the ankle ends up (model space) for the hips', thigh's and shin's own Z rotations (rest + animation)."""
    q = _w_rot(W_ANKLE_P, W_KNEE_P, shin)
    q = _w_rot(q, W_THIGH_P, thigh)
    return _w_rot(q, W_HIP_P, hip)


def w_legs(thigh_w, shin_w, hip=0.0, hip_x=0.0, sides="LR", foot_w=0.0):
    """Legs posed by their world angles (thigh and shin from straight down, + is backward), the feet set at foot_w
    (0: flat), the hips moved (in their own turned frame) so the feet stay where they stood at rest. -> poses"""
    a0 = _w_ankle(0, W_THIGH_REST, W_SHIN_REST)
    a = _w_ankle(hip, thigh_w - hip, shin_w - thigh_w)
    d = (a0[0] - a[0], a0[1] - a[1])
    off = _w_rot(d, (0, 0), -hip)
    out = {"Hips": pose((hip_x, 0, hip), (off[0], off[1], 0))}
    for sd in sides:
        out["Thigh" + sd] = pose((0, 0, thigh_w - hip - W_THIGH_REST))
        out["Shin" + sd] = pose((0, 0, shin_w - thigh_w - W_SHIN_REST))
        out["Foot" + sd] = pose((0, 0, foot_w - shin_w - W_FOOT_REST))
    return out


@lit()
def wretch(variant="common"):
    global WV
    WV = dict(WRETCH_VARIANTS[variant])
    m = Model("wretch", atlas_width=64, seed=15)

    # ---- The body, bent nearly double ----
    # The waist leans forward 10, the chest 16 more; the thin neck juts forward a further 22 and the head tips back 46
    # (so the face looks ahead, a touch down, from in front of the shoulders, as a vulture's does).
    hips = m.part("Hips", (-1.7, 12.8, -2.7), (3.4, 3.2, 5.4), pivot=(0, 14.4, 0), paint=w_hips)
    belly = m.part("Belly", (-1.3, 15.8, -2.0), (2.6, 4.0, 4.0), pivot=(0, 15.9, 0), parent=hips, rest=(0, 0, 14), paint=w_belly)
    chest = m.part("Chest", (-1.9, 19.5, -2.7), (3.8, 5.3, 5.4), pivot=(0, 19.7, 0), parent=belly, rest=(0, 0, 22), paint=w_chest)
    m.part("SpineLow", (1.2, 16.1, -0.35), (0.4, 3.7, 0.7), parent=belly, paint=w_spine)
    m.part("SpineHigh", (1.8, 19.6, -0.4), (0.45, 4.6, 0.8), parent=chest, paint=w_spine)
    m.part("BladeL", (1.75, 21.0, 0.6), (0.4, 2.8, 1.9), pivot=(1.95, 23.8, 1.55), parent=chest, rest=(0, 0, 10), paint=w_blade)
    m.mirror("BladeL", "BladeR")
    m.part("Collar", (-1.35, 24.3, -1.35), (2.7, 0.75, 2.7), parent=chest, paint=w_collar)
    neck = m.part("Neck", (-0.75, 24.3, -0.75), (1.5, 3.4, 1.5), pivot=(0, 24.5, 0), parent=chest, rest=(0, 0, 40), paint=w_neck)

    # ---- The head: the skull set back, a brow and the cheeks in front, the sockets between ----
    head = m.part("Head", (-2.0, 27.2, -2.0), (4.0, 4.4, 4.0), pivot=(0.3, 27.6, 0), parent=neck, rest=(0, 0, -70), paint=w_head)
    m.part("Crown", (-1.7, 31.6, -1.65), (3.5, 0.65, 3.3), parent=head, paint=w_crown)
    m.part("Brow", (-2.75, 30.3, -2.05), (0.8, 1.45, 4.1), parent=head, paint=w_brow)
    m.part("Face", (-2.6, 27.2, -1.95), (0.65, 1.7, 3.9), parent=head, paint=w_face)
    m.part("Bridge", (-2.42, 28.9, -0.3), (0.45, 1.4, 0.6), parent=head, paint=w_bridge)
    m.part("EyeL", (-2.3, 29.05, 0.5), (1.0, 1.0, 1.0), pivot=(-1.8, 29.55, 1.0), parent=head, paint=w_eye)
    m.mirror("EyeL", "EyeR")
    for n, dy in (("EyeR", -0.12),):                                                    # one eye a little lower
        p = m.by_name[n]
        p.frm[1] += dy
        p.pivot[1] += dy
    m.part("EarL", (-0.2, 28.7, 1.95), (1.0, 1.3, 0.35), pivot=(0.3, 29.3, 2.0), parent=head, rest=(-8, 0, 0), paint=w_ear)
    m.mirror("EarL", "EarR")
    m.part("Maw", (-1.95, 26.0, -1.5), (2.2, 1.25, 3.0), parent=head, paint=w_maw)
    jaw = m.part("Jaw", (-2.5, 25.9, -1.75), (2.9, 1.3, 3.5), pivot=(0.3, 26.9, 0), parent=head, rest=(0, 0, 22), paint=w_jaw)
    # Teeth: the upper ones left in the gum, uneven, one far too long; the lower ones; and three grown out of a cheek
    for i, (z, wd, ln) in enumerate(((-1.4, 0.35, 0.5), (-0.55, 0.3, 0.75), (0.25, 0.4, 1.15), (1.2, 0.3, 0.45))):
        m.part(f"ToothU{i}", (-2.55, 27.2 - ln, z - wd / 2), (0.4, ln + 0.1, wd), parent=head, paint=w_tooth, tag={"upper": True})
    for i, (z, wd, ln) in enumerate(((-1.05, 0.35, 0.55), (-0.15, 0.3, 0.4), (0.8, 0.45, 0.85))):
        m.part(f"ToothD{i}", (-2.45, 27.1, z - wd / 2), (0.4, ln, wd), parent=jaw, paint=w_tooth, tag={"upper": False})
    for i, (x, y, sz) in enumerate(((-1.45, 27.75, 0.45), (-0.95, 27.5, 0.35), (-1.0, 28.15, 0.3))):
        m.part(f"CheekTooth{i}", (x, y, 1.9), (sz, sz, 0.45 + sz * 0.6), parent=head, paint=w_tooth, tag={"upper": True})
    # A few strings of hair
    m.part("HairA", (-0.4, 27.0, 2.0), (1.9, 4.6, 0.12), pivot=(0.55, 31.6, 2.06), parent=head, rest=(-5, 0, 0), paint=w_hair)
    m.part("HairB", (2.0, 26.4, -1.3), (0.12, 5.2, 1.7), pivot=(2.06, 31.6, -0.45), parent=head, rest=(0, 0, 6), paint=w_hair)
    m.part("HairC", (0.4, 29.4, -2.12), (1.3, 2.2, 0.12), pivot=(1.05, 31.6, -2.06), parent=head, rest=(4, 0, 0), paint=w_hair)
    # Sludge hanging from the mouth (turned to hang straight down: the jaw sits 18 forward of upright)
    m.part("Drool", (-2.38, 23.3, -0.65), (0.3, 2.7, 0.45), pivot=(-2.23, 26.0, -0.42), parent=jaw, rest=(0, 0, -28), paint=w_drool)
    m.part("DroolB", (-1.75, 24.5, 1.25), (0.25, 1.5, 0.35), pivot=(-1.62, 26.0, 1.42), parent=jaw, rest=(0, 0, -28), paint=w_drool)

    # ---- Arms: long, all bone, hanging to the knees, the hands turned back, nails grown into claws ----
    arm = m.part("ArmL", (-0.7, 17.4, 2.7), (1.4, 7.0, 1.4), pivot=(0, 24.0, 3.4), parent=chest, rest=(-5, 0, -38), paint=w_arm)
    fore = m.part("ForearmL", (-0.6, 10.0, 2.8), (1.2, 7.6, 1.2), pivot=(0, 17.6, 3.4), parent=arm, rest=(2, 0, -6), paint=w_forearm)
    hand = m.part("HandL", (-0.45, 8.0, 2.6), (0.9, 2.1, 1.6), pivot=(0, 10.0, 3.4), parent=fore, rest=(0, 0, 6), paint=w_hand)
    for i in range(3):
        z = 2.62 + i * 0.55
        m.part(f"Finger{i}L", (-0.35, 5.2 + (0.3 if i != 1 else 0), z), (0.45, 2.9 - (0.3 if i != 1 else 0), 0.45),
               pivot=(-0.12, 8.05, z + 0.22), parent=hand, rest=((i - 1) * -4, 0, -8), paint=w_finger)
    m.part("ThumbL", (-0.6, 6.7, 2.55), (0.45, 1.7, 0.45), pivot=(-0.4, 8.4, 2.75), parent=hand, rest=(10, 0, -20), paint=w_finger)
    # ---- Legs: thin, knees bent and knobbed, one shoe ----
    thigh = m.part("ThighL", (-1.05, 7.4, 0.25), (2.1, 7.2, 2.1), pivot=(0, 14.3, 1.3), parent=hips, rest=(0, 0, W_THIGH_REST), paint=w_thigh)
    shin = m.part("ShinL", (-0.8, 0.9, 0.45), (1.6, 6.8, 1.7), pivot=(0, 7.6, 1.3), parent=thigh, rest=(0, 0, W_SHIN_REST), paint=w_shin)
    m.part("KneeL", (-1.15, 6.6, 0.55), (0.5, 1.4, 1.5), parent=shin, paint=w_knee)
    m.part("FootL", (-3.0, 0.0, 0.25), (4.0, 1.2, 2.1), pivot=(0, 1.0, 1.3), parent=shin, rest=(0, 0, W_FOOT_REST), paint=w_foot)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    # The bare right foot is narrower than the shoe; the right arm hangs a little further forward and turns in
    fr = m.by_name["FootR"]
    fr.frm, fr.size = [-2.85, 0.0, -2.2], [3.85, 1.0, 1.8]
    m.by_name["ArmR"].rest = (3, 0, -44)
    m.by_name["ForearmR"].rest = (-4, 0, -10)
    m.by_name["HandR"].rest = (0, 10, 4)
    m.part("TrouserRagR", (-0.9, 4.6, -2.32), (1.9, 2.9, 0.12), pivot=(0, 7.5, -2.26), parent="ShinR", rest=(6, 0, 0), paint=w_trouser_rag)

    # ---- The rags of the shirt, the backpack's strap and its torn pouch ----
    m.part("RagFront", (-2.0, 16.9, -2.4), (0.15, 3.0, 2.3), pivot=(-1.92, 19.9, -1.25), parent=chest, rest=(0, 0, -32), paint=w_rag)
    m.part("RagFront2", (-2.0, 17.7, 0.3), (0.15, 2.2, 1.6), pivot=(-1.92, 19.9, 1.1), parent=chest, rest=(4, 0, -28), paint=w_rag)
    m.part("RagSide", (-1.2, 16.5, 2.7), (2.1, 3.4, 0.15), pivot=(-0.15, 19.9, 2.75), parent=chest, rest=(8, 0, -24), paint=w_rag)
    m.part("RagBack", (1.85, 16.3, -2.3), (0.15, 3.6, 2.6), pivot=(1.92, 19.9, -1.0), parent=chest, rest=(0, 0, -30), paint=w_rag)
    m.part("Strap", (-2.05, 19.3, 1.0), (4.1, 5.75, 0.7), parent=chest, paint=w_strap)
    m.part("Buckle", (-2.2, 21.0, 0.95), (0.2, 0.6, 0.8), parent=chest, paint=w_metal)
    m.part("Pouch", (1.95, 16.6, 0.5), (1.6, 2.6, 2.2), pivot=(2.4, 19.2, 1.35), parent=chest, rest=(0, 0, -34), paint=w_pouch)
    # Pustules standing off the skin
    for name, parent, frm, size in (("PusA", "Chest", (1.85, 22.4, 1.9), (0.5, 0.8, 0.8)),
                                    ("PusB", "ArmR", (-0.4, 22.2, -4.45), (0.8, 0.9, 0.4)),
                                    ("PusC", "Head", (-1.3, 29.7, -2.3), (0.7, 0.7, 0.35)),
                                    ("PusD", "ForearmL", (-0.3, 13.0, 3.95), (0.7, 0.8, 0.35)),
                                    ("PusE", "Belly", (-0.6, 17.4, -2.3), (0.8, 0.8, 0.35)),
                                    ("PusF", "Neck", (-0.95, 25.4, 0.1), (0.3, 0.6, 0.6))):
        m.part(name, frm, size, parent=parent, paint=w_pustule)

    # ---- Animations ----
    # A hanging limb swings backward with +Z, an upright part leans forward with +Z; the jaw drops with +Z. +X tilts
    # an upright part to the left (+z) and swings a hanging left limb inward (a right one outward).
    fingers = [f"Finger{i}{sd}" for i in range(3) for sd in "LR"] + ["ThumbL", "ThumbR"]
    loose = ["Drool", "DroolB", "RagFront", "RagFront2", "RagSide", "RagBack", "Pouch", "HairA", "HairB", "HairC", "TrouserRagR"]
    NAMES = (["Hips", "Belly", "Chest", "Neck", "Head", "Jaw", "EyeL", "EyeR",
              "ArmL", "ArmR", "ForearmL", "ForearmR", "HandL", "HandR", "ThighL", "ThighR", "ShinL", "ShinR", "FootL", "FootR"]
             + fingers + loose)

    def eyes(p, amt=1.0):
        """Lidless eyes rolling on their own, each to its own rhythm, never quite still."""
        return {"EyeL": pose((0, amt * (24 * math.sin(TAU * (3 * p + 0.1)) + 9 * math.sin(TAU * 7 * p)), amt * 16 * math.sin(TAU * (2 * p + 0.35)))),
                "EyeR": pose((0, amt * (22 * math.sin(TAU * (4 * p + 0.62)) + 8 * math.sin(TAU * (5 * p + 0.2))), amt * 18 * math.sin(TAU * (3 * p + 0.8))))}

    def dangle(p, lean=0.0, head=0.0, trail=0.0, amp=1.0, f=1):
        """The loose things (rags, strap pouch, hair, sludge) hang straight down whatever the body does (`lean`: how far
        the chest leans past its rest; `head`: the jaw's tilt past its rest), trail behind as it moves, and sway."""
        d = {}
        for i, n in enumerate(("RagFront", "RagFront2", "RagSide", "RagBack")):
            d[n] = pose((s(p * f, 3 * amp, i * 0.21), 0, -lean + trail + s(p * f * 2, 5 * amp, i * 0.17)))
        d["Pouch"] = pose((s(p * f, 3 * amp, 0.4), 0, -lean + trail * 0.7 + s(p * f * 2, 4 * amp, 0.3)))
        d["TrouserRagR"] = pose((s(p * f, 4 * amp, 0.6), 0, trail * 0.8 + s(p * f * 2, 6 * amp, 0.5)))
        d["Drool"] = pose((s(p * f, 6 * amp, 0.1), 0, -head + trail + s(p * f * 2, 8 * amp, 0.25)))
        d["DroolB"] = pose((s(p * f, 6 * amp, 0.4), 0, -head + trail + s(p * f * 2, 8 * amp, 0.55)))
        for i, n in enumerate(("HairA", "HairB", "HairC")):
            d[n] = pose((s(p * f, 4 * amp, i * 0.3), 0, trail * 0.5 + s(p * f * 2, 4 * amp, i * 0.2)))
        return d

    def claws(curl, spread=0.0):
        d = {}
        for i in range(3):
            for sd, k in (("L", 1), ("R", -1)):
                d[f"Finger{i}{sd}"] = pose(((i - 1) * spread * k, 0, curl))
        d["ThumbL"] = pose((-curl * 0.5, 0, curl * 0.4))
        d["ThumbR"] = pose((curl * 0.5, 0, curl * 0.4))
        return d

    def loop(code, frames, steps, fn):
        m.animation(code, frames, cycle(frames, steps, lambda p: full(NAMES, fn(p))))

    # Idle: it stands bent, breathing hard through the open mouth, swaying; the head drifts and jerks; the jaw works
    # at nothing; the fingers twitch; the eyes never stop.
    def idle(p):
        breath = math.sin(TAU * p * 3)
        twitch = ramp(p, 0.30, 0.32, 0.36, 0.42) - ramp(p, 0.70, 0.72, 0.75, 0.82)
        sway = s(p, 2.0)
        d = {
            "Hips": pose((sway, 0, 0), (0, 0.12 * breath, 0)),
            "Belly": pose((0, s(p, 3, 0.2), 0.8 * breath)),
            "Chest": pose((-sway * 0.5, 0, 1.2 * breath), s=(1, 1 + 0.025 * breath, 1 + 0.02 * breath)),
            "Neck": pose((0, 0, -1.2 * breath)),
            "Head": pose((10 * twitch - sway * 0.5, 16 * twitch + s(p, 6, 0.3), s(p * 2, 3, 0.1))),
            "Jaw": pose((0, 0, 4 + s(p * 3, 4, 0.2) + 6 * ramp(p, 0.5, 0.55, 0.6, 0.66))),
            "ArmL": pose((0, 0, s(p, 2, 0.2))), "ArmR": pose((0, 0, -s(p, 2))),
            "ForearmL": pose((0, 0, s(p, 2, 0.4))), "ForearmR": pose((0, 0, -s(p, 2, 0.1))),
        }
        d.update(claws(6 + 10 * ramp(p, 0.15, 0.2, 0.24, 0.3) - 8 * ramp(p, 0.8, 0.84, 0.88, 0.94)))
        d.update(eyes(p))
        d.update(dangle(p, amp=0.6))
        return d

    loop("idle", 90, 30, idle)

    # Walk: a stumbling lurch. The bare right foot drags and takes the weight badly: the body drops and swings over
    # it every other step, the head flops a beat late, the arms dangle and swing loose, the jaw bounces.
    def walk(p):
        c, sn = math.cos(TAU * p), math.sin(TAU * p)
        r_st, l_st = max(0.0, c), max(0.0, -c)            # weight on the right (p ~ 0) and on the left (p ~ 0.5)
        thigh_l, thigh_r = -24 * sn, 18 * sn               # the left swings forward from p 0 to 0.5
        knee_l = 34 * max(0.0, c)                          # the left knee bends mid-swing; the right barely does
        knee_r = 12 * max(0.0, -c)
        d = {
            "Hips": pose((-5 * r_st + 2 * l_st, s(p, 6, 0.05), 0), (0, -0.25 * r_st * r_st - 0.1 * l_st, 0)),
            "Belly": pose((-2 * r_st, -s(p, 4, 0.1), 3 * r_st)),
            "Chest": pose((-6 * r_st + 3 * l_st, -s(p, 5, 0.12), 2 + 4 * r_st)),
            "Neck": pose((0, 0, -3 * r_st)),
            "Head": pose((8 * max(0.0, math.cos(TAU * (p - 0.14))) - 4 * max(0.0, -math.cos(TAU * (p - 0.14))), s(p, 6, 0.2),
                          -2 * r_st + 5 * max(0.0, math.cos(TAU * (p - 0.18))))),
            "Jaw": pose((0, 0, 3 + 8 * abs(math.sin(TAU * (p - 0.15))))),
            "ThighL": pose((2, 0, thigh_l)), "ThighR": pose((-3, 0, thigh_r)),
            "ShinL": pose((0, 0, knee_l)), "ShinR": pose((0, 0, knee_r)),
            "FootL": pose((0, 0, -(thigh_l + knee_l) * 0.85)),
            "FootR": pose((0, 0, -(thigh_r + knee_r) * 0.6 + 18 * max(0.0, -sn))),        # the toes dragging through
            "ArmL": pose((-3 + 3 * r_st, 0, 4 + 10 * math.sin(TAU * (p - 0.12)))),
            "ArmR": pose((2, 0, -8 - 9 * math.sin(TAU * (p - 0.12)))),
            "ForearmL": pose((0, 0, -4 + 10 * math.sin(TAU * (p - 0.3)))),
            "ForearmR": pose((0, 0, -8 - 7 * math.sin(TAU * (p - 0.3)))),
            "HandL": pose((0, 0, 8 * math.sin(TAU * (p - 0.4)))), "HandR": pose((0, 0, -6 * math.sin(TAU * (p - 0.4)))),
        }
        d.update(claws(8))
        d.update(eyes(p, 0.8))
        d.update(dangle(p, lean=2 + 4 * r_st, head=5 * max(0.0, math.cos(TAU * (p - 0.18))), trail=6, amp=1.3, f=2))
        return d

    loop("walk", 48, 16, walk)

    # Run: a desperate sprint, faster than a person should run, bent forward, the head thrust out and the jaw wide;
    # the arms flail forward grabbing at the air in turn, out of step with the legs.
    def run(p):
        c, sn = math.cos(TAU * p), math.sin(TAU * p)
        thigh_l, thigh_r = -44 * sn, 44 * sn
        knee_l, knee_r = 70 * max(0.0, c), 70 * max(0.0, -c)
        d = {
            "Hips": pose((s(p, 4), s(p, 8, 0.05), 8), (0, -0.8 + 0.9 * abs(math.sin(TAU * (p * 2 - 0.1))), 0)),
            "Belly": pose((0, -s(p, 6), 8)),
            "Chest": pose((s(p * 2, 3), -s(p, 8, 0.1), 10)),
            "Neck": pose((0, 0, -6)),
            "Head": pose((s(p * 2, 6, 0.2), s(p * 3, 8), -18 + s(p * 2, 5, 0.3))),
            "Jaw": pose((0, 0, 18 + s(p * 4, 8))),
            "ThighL": pose((0, 0, thigh_l - 8)), "ThighR": pose((0, 0, thigh_r - 8)),
            "ShinL": pose((0, 0, knee_l + 10)), "ShinR": pose((0, 0, knee_r + 10)),
            "FootL": pose((0, 0, -(thigh_l + knee_l) * 0.7)), "FootR": pose((0, 0, -(thigh_r + knee_r) * 0.7)),
            "ArmL": pose((-16 + s(p * 2, 8), 0, -90 + 32 * math.sin(TAU * (p + 0.1)))),
            "ArmR": pose((16 + s(p * 2, 8, 0.3), 0, -90 + 32 * math.sin(TAU * (p + 0.6)))),
            "ForearmL": pose((0, 0, -30 + 28 * math.sin(TAU * (p + 0.35)))),
            "ForearmR": pose((0, 0, -30 + 28 * math.sin(TAU * (p + 0.85)))),
            "HandL": pose((0, 0, -10 + s(p, 12, 0.5))), "HandR": pose((0, 0, -10 + s(p, 12))),
        }
        d.update(claws(20 + 25 * math.sin(TAU * (p + 0.2)), 10))
        d.update(eyes(p, 1.2))
        d.update(dangle(p, lean=26, head=-14, trail=22, amp=1.6, f=2))
        return d

    loop("run", 24, 12, run)

    # Attack (30 frames, 1 s): it rears up with the arms high and the mouth wide, lunges, rakes down with both hands and
    # bites, the jaw slamming shut on frame 13 (damage there: ~430 ms), then tears, shaking its head, and lets go.
    def atk(d, p, lean=0.0, head=0.0):
        out = dict(d)
        out.update(eyes(p, 0.6))
        out.update(dangle(p, lean=lean, head=head, trail=0, amp=1.0))
        return full(NAMES, out)

    rear = {"Hips": pose((0, 0, -6), (0.8, -0.6, 0)), "Belly": pose((0, 0, -10)), "Chest": pose((0, 0, -16)), "Neck": pose((0, 0, -4)),
            "Head": pose((0, 0, 2)), "Jaw": pose((0, 0, 26)),
            "ArmL": pose((-30, 0, -74)), "ArmR": pose((30, 0, -68)), "ForearmL": pose((0, 0, -44)), "ForearmR": pose((0, 0, -40)),
            "HandL": pose((0, 0, -20)), "HandR": pose((0, 0, -20)),
            **w_legs(-26, 18, -6), **claws(-15, 12)}
    launch = {"Hips": pose((0, 0, 6), (-1.0, -0.4, 0)), "Belly": pose((0, 0, 6)), "Chest": pose((0, 0, 8)), "Neck": pose((0, 0, 2)),
              "Head": pose((0, 0, -6)), "Jaw": pose((0, 0, 30)),
              "ArmL": pose((-24, 0, -96)), "ArmR": pose((24, 0, -90)), "ForearmL": pose((0, 0, -30)), "ForearmR": pose((0, 0, -28)),
              "HandL": pose((0, 0, -15)), "HandR": pose((0, 0, -15)),
              "ThighL": pose((0, 0, -34)), "ShinL": pose((0, 0, 30)), "FootL": pose((0, 0, 4)),
              "ThighR": pose((0, 0, 12)), "ShinR": pose((0, 0, 8)), "FootR": pose((0, 0, -20)), **claws(-5, 12)}
    strike = {"Hips": pose((0, 0, 8), (-2.8, -0.3, 0)), "Belly": pose((0, 0, 6)), "Chest": pose((0, 0, 8)), "Neck": pose((0, 0, 4)),
              "Head": pose((0, 0, -16)), "Jaw": pose((0, 0, -20)),
              "ArmL": pose((-6, 0, -58)), "ArmR": pose((6, 0, -48)), "ForearmL": pose((0, 0, -38)), "ForearmR": pose((0, 0, -34)),
              "HandL": pose((0, 0, 10)), "HandR": pose((0, 0, 10)),
              "ThighL": pose((0, 0, -36)), "ShinL": pose((0, 0, 28)), "FootL": pose((0, 0, 8)),
              "ThighR": pose((0, 0, 16)), "ShinR": pose((0, 0, 12)), "FootR": pose((0, 0, -26)), **claws(45)}
    tear_a = dict(strike, **{"Head": pose((0, 18, -18)), "Jaw": pose((0, 0, -12)), "ArmL": pose((-4, 0, -36)), "ArmR": pose((4, 0, -30)),
                             "ForearmL": pose((0, 0, -62)), "ForearmR": pose((0, 0, -58)), "Chest": pose((0, -6, 6))})
    tear_b = dict(strike, **{"Head": pose((0, -16, -16)), "Jaw": pose((0, 0, -6)), "ArmL": pose((-4, 0, -30)), "ArmR": pose((4, 0, -34)),
                             "ForearmL": pose((0, 0, -55)), "ForearmR": pose((0, 0, -62)), "Chest": pose((0, 6, 4)),
                             "Hips": pose((0, 0, 6), (-2.2, -0.3, 0)), "Belly": pose((0, 0, 4))})
    settle = {"Hips": pose((0, 0, 3), (-0.6, -0.2, 0)), "Belly": pose((0, 0, 4)), "Chest": pose((0, 0, 4)), "Head": pose((0, 0, -4)),
              "Jaw": pose((0, 0, 6)), "ArmL": pose((0, 0, -16)), "ArmR": pose((0, 0, -12)), "ForearmL": pose((0, 0, -20)),
              "ForearmR": pose((0, 0, -16)), **claws(20)}
    m.animation("attack", 30, {
        0: atk({}, 0), 5: atk(rear, 5 / 30, lean=-28, head=-24), 9: atk(launch, 9 / 30, lean=20, head=10),
        13: atk(strike, 13 / 30, lean=44, head=-15), 16: atk(tear_a, 16 / 30, lean=40, head=-10),
        20: atk(tear_b, 20 / 30, lean=30, head=-6), 25: atk(settle, 25 / 30, lean=11, head=4), 29: atk({}, 29 / 30),
    }, end="Stop")

    # Hurt: it reels back from the blow, the head snapping aside, the mouth gaping, the arms flinching up.
    hurt_names = ["Belly", "Chest", "Neck", "Head", "Jaw", "ArmL", "ArmR", "ForearmL", "ForearmR", "EyeL", "EyeR"]
    m.animation("hurt", 12, {
        0: full(hurt_names, {}),
        3: full(hurt_names, {"Belly": pose((0, 0, -8)), "Chest": pose((6, 12, -14)), "Neck": pose((0, 0, -10)), "Head": pose((16, 18, 2)),
                             "Jaw": pose((0, 0, 20)), "ArmL": pose((-22, 0, -40)), "ArmR": pose((18, 0, -30)),
                             "ForearmL": pose((0, 0, -40)), "ForearmR": pose((0, 0, -30)),
                             "EyeL": pose((0, 30, -20)), "EyeR": pose((0, -25, 15))}),
        7: full(hurt_names, {"Belly": pose((0, 0, -3)), "Chest": pose((2, 5, -5)), "Neck": pose((0, 0, -4)), "Head": pose((6, 6, 0)),
                             "Jaw": pose((0, 0, 10)), "ArmL": pose((-8, 0, -14)), "ArmR": pose((6, 0, -10)),
                             "EyeL": pose((0, -10, 10)), "EyeR": pose((0, 15, -10))}),
        11: full(hurt_names, {}),
    }, end="Stop")

    # Death (see docs/design/entity-ai-overhaul/death-poses.md): it reels from the blow, the knees go and it drops
    # onto them, sways there a moment, then pitches forward, the left elbow buckling out to the side, and goes down on
    # its face, rolling a little onto its left side; it rocks back once and settles: the right arm flung out past the
    # head with the elbow bent and the claws curled, the left elbow out and its hand by the face, the right knee drawn
    # up and out along the floor, the left leg trailing, the back slack, the head laid on its cheek last with the jaw
    # hanging; the eyes go still. Face down, a limb's Z swing is toward or away from the floor; X swings it out along it.
    soft = ["Drool", "DroolB", "RagFront", "RagFront2", "RagSide", "RagBack", "HairA", "HairB", "HairC", "TrouserRagR"]

    def flat(k):
        """The rags and hair falling flat along the body, the sludge onto the floor, as it lies (k 0..1)."""
        d = {n: pose((0, 0, 0)) for n in soft}
        for i, n in enumerate(("RagFront", "RagFront2", "RagSide", "RagBack")):
            d[n] = pose(((-8, 6, 14, -4)[i] * k, 0, (34, 30, 20, 26)[i] * k))
        d["Pouch"] = pose((-12 * k, 0, 30 * k))
        d["TrouserRagR"] = pose((10 * k, 0, 24 * k))
        d["Drool"] = pose((10 * k, 0, 60 * k))
        d["DroolB"] = pose((-10 * k, 0, 54 * k))
        for i, n in enumerate(("HairA", "HairB", "HairC")):
            d[n] = pose(((-30, 10, 20)[i] * k, 0, (-40, -30, -36)[i] * k))
        return d

    def fallen(theta, roll, dx):
        """The hips turned forward by theta and rolled `roll` onto the left side, moved dx along the floor."""
        o = _w_rot((dx, 0), (0, 0), -theta)
        return pose((roll, 0, theta), (o[0], o[1], 0))

    def prone(roll, slack, jaw, curl):
        """Face down and rolled `roll` onto its left side, from the sprawl it landed in (slack 0) to the pose it rests
        in (slack 1)."""
        def at(a, b):
            return tuple(a[i] + (b[i] - a[i]) * slack for i in range(3))
        return dict({
            "Hips": fallen(86, roll, -3), "Belly": pose(at((0, 0, -12), (3, 2, -10))), "Chest": pose(at((0, 0, -18), (4, 4, -16))),
            "Neck": pose(at((0, 0, -38), (0, 0, -45))), "Head": pose(at((0, 60, 30), (0, 85, 40))), "Jaw": pose((0, 0, jaw)),
            "ArmR": pose(at((-40, 0, -120), (-60, 0, -128))), "ForearmR": pose(at((-40, 0, 0), (-65, 0, 0))), "HandR": pose(at((0, 20, 10), (0, 40, 30))),
            "ArmL": pose(at((-100, 0, 55), (-110, 0, 45))), "ForearmL": pose(at((-90, 0, -5), (-90, 0, 5))), "HandL": pose(at((0, 0, 10), (0, 10, 24))),
            "ThighR": pose(at((15, -25, -25), (30, -45, -40))), "ShinR": pose(at((0, 0, 30), (0, 0, 55))), "FootR": pose(at((0, 0, 20), (0, 0, 30))),
            "ThighL": pose(at((-4, 0, 16), (-8, 14, 12))), "ShinL": pose(at((0, 0, -20), (0, 0, -14))), "FootL": pose(at((0, 0, 50), (0, 0, 60))),
        }, **claws(curl, 10), **flat(0.7 + 0.3 * slack))

    def tween(a, b, t):
        """The pose t of the way from keyframe a to keyframe b: a frame the body passes through, put on the floor."""
        out = {}
        for n in set(a) | set(b):
            pa, pb = a.get(n, pose()), b.get(n, pose())
            out[n] = pose(*(tuple(pa[k][i] + (pb[k][i] - pa[k][i]) * t for i in range(3)) for k in ("rot", "off")))
        return out

    kneel = w_legs(0, 90, 0, foot_w=-188)
    keys = {
        0: {},
        # the hit: it reels back, the head snapping aside, the mouth wide, the arms flung up
        4: {"Hips": pose((5, 0, -6), (1.4, -0.3, 0)), "Belly": pose((0, 0, -6)), "Chest": pose((0, 8, -12)), "Neck": pose((0, 0, -8)),
            "Head": pose((14, 10, -14)), "Jaw": pose((0, 0, 26)), "ArmL": pose((-30, 0, -60)), "ArmR": pose((30, 0, -40)),
            "ForearmL": pose((0, 0, -40)), "ForearmR": pose((0, 0, -30)), **w_legs(-4, 10, -6), **claws(-10, 10)},
        # the knees go: down onto them, the arms dropping, the head lolling forward
        11: dict(kneel, **{"Belly": pose((0, 0, 8)), "Chest": pose((4, 0, 10)), "Neck": pose((0, 0, 8)), "Head": pose((8, -6, 8)),
                           "Jaw": pose((0, 0, 22)), "ArmL": pose((-14, 0, -6)), "ArmR": pose((14, 0, 4)),
                           "ForearmL": pose((0, 0, -64)), "ForearmR": pose((0, 0, -58)), **claws(10)}),
        # it sways there a moment
        16: dict(kneel, **{"Hips": pose((-4, 0, 6), kneel["Hips"]["off"]), "Belly": pose((0, 0, 12)), "Chest": pose((-6, 0, 14)), "Neck": pose((0, 0, 10)),
                           "Head": pose((-10, 8, 10)), "Jaw": pose((0, 0, 26)), "ArmL": pose((-14, 0, -30)), "ArmR": pose((14, 0, -6)),
                           "ForearmL": pose((0, 0, -70)), "ForearmR": pose((0, 0, -76)),
                           "ThighL": pose((0, 0, 6)), "ThighR": pose((0, 0, 6)), **claws(10)}),
        # pitching forward over the knees, the right arm thrown out ahead, the left elbow buckling out
        22: dict(w_legs(-40, 92, 48, hip_x=6, foot_w=-190), **{
            "Belly": pose((0, 0, -4)), "Chest": pose((0, 0, -8)), "Neck": pose((0, 0, -16)), "Head": pose((0, 20, 8)), "Jaw": pose((0, 0, 24)),
            "ArmR": pose((10, 0, -110)), "ArmL": pose((-90, 0, 5)), "ForearmR": pose((0, 0, -10)), "ForearmL": pose((-55, 0, -40)),
            **claws(-5, 10), **flat(0.3)}),
        # the chest going down onto the folded left arm
        25: dict(w_legs(-45, 85, 74, hip_x=22, foot_w=-170), **{
            "Belly": pose((0, 0, -8)), "Chest": pose((2, 0, -14)), "Neck": pose((0, 0, -30)), "Head": pose((0, 40, 20)), "Jaw": pose((0, 0, 28)),
            "ArmR": pose((-20, 0, -120)), "ArmL": pose((-105, 0, 30)), "ForearmR": pose((-20, 0, -10)), "ForearmL": pose((-75, 0, -22)),
            **claws(-5, 10), **flat(0.5)}),
        # down on its face, a little over onto its left side
        27: prone(24, 0.0, 30, 0),
        # rocks back
        31: prone(12, 0.5, 18, 20),
        # settling, the head sinks onto its cheek
        39: prone(15, 1.0, 22, 44),
    }
    keys[8] = dict(tween(keys[4], keys[11], 0.5), **w_legs(-2, 50, -3, foot_w=-40))  # dropping onto the knees
    keys[19] = dict(tween(keys[16], keys[22], 0.5), ArmL=pose((-90, 0, -20)), ForearmL=pose((-30, 0, -40)))  # toppling
    keys[26] = tween(keys[25], keys[27], 0.5)                                      # the knees slide back as the chest hits
    keys = dict(sorted(keys.items()))
    # (floor: the whole model is moved down W_SHIFT after this)
    death(m, 40, NAMES, {f: dict(d, **eyes(f / 40, 0.0 if f > 31 else 0.8 * (1 - f / 40))) for f, d in keys.items()},
          floor=-0.25 - W_SHIFT, standing=(4,), soft=soft)

    # Huddle (6 s): squatting on its heels with its arms round its shins, rocking; then the itch: the right hand goes
    # to the left arm and scratches, fast, the head turned to it, until it stops, and rocks again.
    def huddle(p):
        rock = math.sin(TAU * p * 4)
        itch = ramp(p, 0.40, 0.46, 0.74, 0.80)
        scr = math.sin(TAU * p * 20)
        twitch = ramp(p, 0.12, 0.14, 0.17, 0.22) + ramp(p, 0.88, 0.9, 0.92, 0.97)
        d = w_legs(-108 + 5 * rock * (1 - itch), 40 + 4 * rock * (1 - itch), 4 + 4 * rock * (1 - itch))
        d.update({
            "Belly": pose((0, 0, 2 * rock * (1 - itch))), "Chest": pose((0, -6 * itch, 4 + 2 * rock * (1 - itch) + 6 * itch)),
            "Neck": pose((0, 0, -10 + 6 * itch)),
            "Head": pose((10 * twitch + 4 * scr * itch, -14 * itch, -10 - 4 * rock * (1 - itch) + 12 * twitch + 16 * itch)),
            "Jaw": pose((0, 0, -6 + 8 * abs(scr) * itch + 3 * math.sin(TAU * p * 6))),
            "ArmL": pose((-6, 0, -36 - 12 * itch)), "ForearmL": pose((0, -80 + 30 * itch, -50 - 14 * itch)), "HandL": pose((0, 0, -16)),
            "ArmR": pose((6, 0, -36 - 10 * itch)),
            "ForearmR": pose((0, 80 - 26 * itch + 14 * scr * itch, -50 - 14 * itch + 10 * scr * itch)), "HandR": pose((0, 0, -16 + 20 * itch + 22 * scr * itch)),
        })
        d.update(claws(40 * (1 - itch) + (30 + 30 * scr) * itch))
        d.update(eyes(p, 1.0))
        d.update(dangle(p, lean=10, head=-14, amp=0.6, f=2))
        return d

    loop("huddle", 180, 90, huddle)

    # Gnaw (2 s): crouched over something on the floor, one hand pinning it, the other tearing; the head jerks down,
    # bites and rips up, chewing fast; once it looks up, still chewing.
    def gnaw(p):
        rip = math.sin(TAU * p * 2)
        look = ramp(p, 0.62, 0.68, 0.82, 0.88)
        chew = abs(math.sin(TAU * p * 5))
        d = w_legs(-104, 44, 10)
        d.update({
            "Belly": pose((0, s(p * 2, 3), 2)), "Chest": pose((0, s(p * 2, 4, 0.2), 6 - 12 * look)),
            "Neck": pose((0, 0, 4 - 8 * look)), "Head": pose((s(p * 2, 4), s(p * 4, 10) * (1 - look), 14 + 8 * rip * (1 - look) - 30 * look)),
            "Jaw": pose((0, 0, -10 + 24 * chew)),
            "ArmL": pose((-4, 0, -38 + 6 * rip)), "ForearmL": pose((0, -30 - 8 * rip, -112 - 10 * rip)), "HandL": pose((0, 0, -20)),
            "ArmR": pose((4, 0, -38 - 6 * rip)), "ForearmR": pose((0, 30 - 8 * rip, -112 + 10 * rip)), "HandR": pose((0, 0, -20)),
        })
        d.update(claws(55))
        d.update(eyes(p, 1.0))
        d.update(dangle(p, lean=34 - 12 * look, head=0, amp=0.6, f=2))
        return d

    loop("gnaw", 60, 30, gnaw)

    # Snarl (an alert, 1.2 s): it straightens, throws its arms out and gapes, gurgling, the whole body shuddering.
    def snarl_pose(k, shake):
        return {"Hips": pose((0, 0, -4 * k)), "Belly": pose((0, 0, -6 * k)), "Chest": pose((shake * 3, shake * 4, -10 * k)),
                "Neck": pose((0, 0, -6 * k)), "Head": pose((shake * 6, shake * 8, 14 * k)), "Jaw": pose((0, 0, 32 * k)),
                "ArmL": pose((-40 * k, 0, -40 * k)), "ArmR": pose((40 * k, 0, -40 * k)),
                "ForearmL": pose((0, 0, -50 * k)), "ForearmR": pose((0, 0, -50 * k)), **claws(-15 * k, 14 * k)}

    m.animation("snarl", 36, {f: full(NAMES, dict(snarl_pose(k, sh), **eyes(f / 36, 1.3), **dangle(f / 36, lean=-16 * k, head=-20 * k)))
                              for f, k, sh in ((0, 0, 0), (6, 0.9, 0), (10, 1.0, 1), (13, 1.0, -1), (16, 1.0, 1), (19, 1.0, -1),
                                               (22, 1.0, 1), (25, 0.9, -0.5), (35, 0, 0))}, end="Stop")
    m.shift(dy=W_SHIFT)
    return m


def w_neck(ctx):
    v = WV
    w_skin(ctx, 0.8)
    if ctx.face == "west":
        line(ctx, 0.2, 0.0, 0.35, 1.0, v["flake"], 0.4)                                        # the tendons
        line(ctx, 0.8, 0.0, 0.65, 1.0, v["flake"], 0.4)
        texel(ctx, ctx.w // 2, ctx.h // 2, mix(v["flake"], v["skin"], 0.3), 0.7)                # the Adam's apple
        w_scratches(ctx, v["scratches"])


def wretch_variant_textures():
    """The early and far-gone looks, painted on the common atlas layout: texture alternates picked per spawn."""
    global WV
    for variant in WRETCH_VARIANTS:
        if variant == "common":
            continue
        m = wretch(variant)
        width, height = m._pack()
        m._paint(width, height).save(os.path.join(ASSETS, "textures", "entity", f"wretch-{variant}.png"))
        print(f"wrote wretch-{variant} texture {width}x{height}")
    WV = dict(WRETCH_VARIANTS["common"])


MODELS = {
    "skinstealer": skinstealer, "hound": hound, "duller": duller, "deathrat": deathrat,
    "deathmoth-male": lambda: deathmoth(False), "deathmoth-female": lambda: deathmoth(True),
    "smiler": smiler, "clump": clump, "mangled": mangled, "thething": thething,
    "animation-clay": animation_clay, "animation-wooden": animation_wooden, "animation-paper": animation_paper, "roboman": roboman,
    "bacteria": bacteria, "wretch": wretch,
    # (Level 8's Giant Spider lives in its own file)
    "giantspider": lambda: __import__("gen_spider").giantspider(),
}


def build(names=None):
    for name in names or list(MODELS):
        MODELS[name]().save()
        if name == "skinstealer":
            skinstealer_variant_textures()
        if name == "deathrat":
            deathrat_variant_textures()
        if name == "clump":
            clump_variant_textures()
        if name == "hound":
            hound_variant_textures()
        if name == "wretch":
            wretch_variant_textures()


def main():
    build(sys.argv[1:])


if __name__ == "__main__":
    main()
