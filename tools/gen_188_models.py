"""Level 188: the Window's arm (Entity 2: "a physical representation of an arm to grasp and pull the victim").
Called from gen_188.py; uses rig.py.

It has no body and no feet. The root sits at the window's centre, hidden in the glass; the arm reaches along the
model's forward axis (rig convention: the model faces -X, its left is +Z), and L188System turns the whole entity
(yaw) toward its victim. It is the arm of the silhouette in the window (Wikidot's "dark, indistinct human silhouette";
Miraheze's panes of black and "an even darker black" figure): a human arm in shape, stretched too long (about two
blocks), matt near-black with a faint smoky mottle. It is least solid where it leaves the glass (a smoky stump that
reaches back into the window, the texels thinning out) and densest at the hand, which is long, palm down, with long
thin fingers of one joint too many. It moves smoothly and wrongly: it is extruded out of the glass rather than
pushed through it, the elbow bends the wrong way (up, like a spider's knee) as it unfolds and as it drags, and the
fingers never quite stop.

Lengths (px, 16 to a block): upper arm 13, forearm 12.5, palm 3, fingers 4.3-5.2. Thickness 2.2 -> 1.8 -> 1 -> 0.5.
Poses are worked out so the hand meets a victim standing 1-1.3 blocks from the root (L188System grabs within 2 blocks
of the window centre, the root is 0.55 in front of it), at the root's height (chest height), and draws back to
0.6 blocks while it drags.
"""
import json
import math
import os
import random

import rig
from rig import Model, pose

from gen_188_kit import LANG, WRITTEN, reg

NAME = "188/l188-arm"
SKIN = (22, 21, 26)
SMOKE = (44, 41, 52)
DEEP = (12, 11, 15)
TAU = math.tau


def smoky(ctx):
    """Near-black, a faint smoky mottle in soft streaks along the limb, the edge texels semi-transparent (it is not
    quite solid). A part tagged fade=(near, far) thins out along its length: `near` is the density at its +X end (the
    glass), `far` at its -X end; texels below the density are left out, so it frays into smoke rather than ending."""
    px = ctx.img.load()
    near, far = ctx.part.tag.get("fade", (1.0, 1.0))
    long_face = ctx.face in ("north", "south", "up", "down")
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            m = ctx.rng.random()
            streak = 0.5 + 0.5 * math.sin((yy if long_face else xx) * 1.7 + ctx.rng.random() * 0.8)
            c = rig.mix(SKIN, SMOKE, 0.30 * m * m + 0.12 * streak)
            if ctx.face == "up":
                c = rig.mix(c, SMOKE, 0.12)
            elif ctx.face == "down":
                c = rig.mix(c, DEEP, 0.5)
            # Where along the limb this texel is: t = 0 at the +X end (the glass), 1 at the -X end
            u = (xx + 0.5) / ctx.w
            if ctx.face == "north":
                t = u
            elif ctx.face in ("south", "up", "down"):
                t = 1 - u
            else:
                t = 0.0 if ctx.face == "east" else 1.0
            density = near + (far - near) * t
            edge = xx == 0 or yy == 0 or xx == ctx.w - 1 or yy == ctx.h - 1
            a = 150 if edge and ctx.w > 2 and ctx.h > 2 else 255
            if density < 1.0:
                a = int(a * (0.55 + 0.45 * density))
                if ctx.rng.random() > density + 0.25:
                    a = 0
            px[ctx.x + xx, ctx.y + yy] = c + (a,)


# Fingers: (name, z centre, splay in degrees, length scale), from the -Z side to the +Z side
FINGERS = [("1", -0.98, -9, 0.84), ("2", -0.33, -3, 1.0), ("3", 0.33, 3, 0.96), ("4", 0.98, 9, 0.8)]
SEGS = (1.55, 1.4, 1.25, 1.05)   # four joints: one too many
HAND_X = -29.5                   # the knuckles


def build():
    m = Model(NAME, atlas_width=32, seed=188)
    root = m.part("Root", (-1, 0, -1), (2, 2, 2), pivot=(0, 1, 0), paint=smoky, tag={"fade": (0.55, 0.85)})
    # The stump reaching back into the glass, fraying out to nothing
    m.part("Shoulder", (0.6, -0.2, -1.3), (5.0, 2.4, 2.6), pivot=(1, 1, 0), parent=root, paint=smoky, tag={"fade": (0.05, 0.6)})
    upper = m.part("UpperArm", (-14, -0.1, -1.1), (13, 2.2, 2.2), pivot=(-1, 1, 0), parent=root, paint=smoky, tag={"fade": (0.7, 1.0)})
    fore = m.part("Forearm", (-26.5, 0.1, -0.9), (12.5, 1.8, 1.8), pivot=(-14, 1, 0), parent=upper, paint=smoky)
    # A bony elbow, standing up a little (it is the wrong-way knee of the drag)
    m.part("Elbow", (-15.0, 0.0, -1.05), (2.0, 2.6, 2.1), pivot=(-14, 1, 0), parent=fore, paint=smoky)
    hand = m.part("Hand", (HAND_X, 0.5, -1.4), (3, 1, 2.8), pivot=(-26.5, 1, 0), parent=fore, paint=smoky)
    m.part("Wrist", (-27.3, 0.25, -1.0), (1.6, 1.5, 2.0), pivot=(-26.5, 1, 0), parent=hand, paint=smoky)
    m.part("Knuckles", (HAND_X - 0.1, 1.5, -1.35), (0.9, 0.3, 2.7), pivot=(HAND_X, 1.5, 0), parent=hand, paint=smoky)
    for n, z, splay, k in FINGERS:
        parent, x = hand, HAND_X
        for i, seg in enumerate(SEGS):
            ln = seg * k
            t = 0.55 - 0.04 * i
            p = m.part(f"Finger{n}{'abcd'[i]}", (x - ln, 1.0 - t / 2, z - t / 2), (ln, t, t), pivot=(x, 1.0, z), parent=parent,
                       rest=(0, splay if i == 0 else 0, 0), paint=smoky)
            parent, x = p, x - ln
    # The thumb, from the +Z side near the wrist, splayed out and forward
    t1 = m.part("ThumbA", (-28.9, 0.7, 1.1), (1.7, 0.55, 0.55), pivot=(-27.2, 0.97, 1.37), parent=hand, rest=(0, 32, 6), paint=smoky)
    m.part("ThumbB", (-30.3, 0.72, 1.12), (1.4, 0.5, 0.5), pivot=(-28.9, 0.97, 1.37), parent=t1, rest=(0, -18, 8), paint=smoky)
    return m


def finger_names():
    return [f"Finger{n}{s}" for n, _, _, _ in FINGERS for s in "abcd"] + ["ThumbA", "ThumbB"]


def curl(amount, jitter=None, spread=0.0):
    """Fingers curled down (palm down: +Z rotation bends a -X part downward) by `amount` (0-1; below 0 they bend back,
    splayed); `spread` adds to the splay of the first joints; `jitter(i)` adds degrees per finger."""
    out = {}
    for i, (n, _, splay, _) in enumerate(FINGERS):
        j = jitter(i) if jitter else 0
        for k, s in enumerate("abcd"):
            out[f"Finger{n}{s}"] = pose((0, spread * splay / 9 * 6 if k == 0 else 0, (34 + 6 * k) * amount + j * (1 + 0.3 * k)))
    out["ThumbA"] = pose((0, -18 * max(0.0, amount), 30 * amount))
    out["ThumbB"] = pose((0, 0, 40 * amount))
    return out


def arm(ua, fa, ha, ua_yaw=0.0, fa_yaw=0.0, roll=0.0, stretch=None):
    """The arm's pose from three pitches (degrees, + is downward for these -X pointing parts): the upper arm's, the
    forearm's relative to it, the hand's relative to the forearm; a little yaw and a roll of the hand."""
    out = {"UpperArm": pose((0, ua_yaw, ua), s=stretch or (1, 1, 1)), "Forearm": pose((0, fa_yaw, fa)), "Hand": pose((roll, 0, ha))}
    return out


def animations(m):
    F = finger_names()
    parts = ["UpperArm", "Forearm", "Hand"]

    def merge(*ds):
        out = {}
        for d in ds:
            out.update(d)
        return out

    # The key poses (worked out in model space: see the docstring)
    # HOLD: the elbow up 40, the forearm down 50, the hand hooked down: the wrist ~19 px out at the root's height
    HOLD = dict(ua=-40, fa=90, ha=22)
    # DRAWN: the elbow high (52 up), the forearm plumb, the hand hanging: the wrist ~10 px out
    DRAWN = dict(ua=-52, fa=136, ha=12)
    # FOLDED: drawn into the glass: straight, so the upper arm's stretch (about its pivot at the root, and inherited by
    # everything below it) squeezes the whole limb into the root
    FOLDED = dict(ua=0, fa=0, ha=0)
    # How far the fingers close on a victim: a hook, open toward the glass (1.0 would close them into a ring)
    CLUTCH = 0.8

    def mix(a, b, t):
        return {k: a[k] + (b[k] - a[k]) * t for k in a}

    # ---- reach, 0.5 s, held: extruded out of the glass, the elbow first and bent the wrong way (the forearm folded up
    # over it); then the forearm whips out straight in a lunge with the fingers splayed wide, and it hooks back into
    # the hold with the fingers closing on the victim.
    m.animation("reach", 15, {
        0: merge(arm(**FOLDED, stretch=(0.05, 0.5, 0.5)), curl(1.0)),
        4: merge(arm(30, -140, 20, ua_yaw=6, stretch=(0.45, 0.85, 0.85)), curl(0.8)),
        8: merge(arm(-22, 40, -18, ua_yaw=-3, stretch=(1, 1, 1)), curl(-0.45, spread=1.5)),
        11: merge(arm(**mix(HOLD, dict(ua=-30, fa=70, ha=0), 0.4)), curl(0.35, spread=0.6)),
        14: merge(arm(**HOLD), curl(CLUTCH)),
    }, end="Hold")

    # ---- grab, 0.2 s, held: from the hold with the fingers open, they close (L188System's reach already ends closed;
    # this is for a re-grip)
    m.animation("grab", 6, {0: merge(arm(**HOLD), curl(-0.35, spread=1.0)), 3: merge(arm(**HOLD), curl(0.6)),
                            5: merge(arm(**HOLD), curl(CLUTCH))}, end="Hold")

    # ---- pull, a 1 s loop: a slow, heavy drag. The elbow rises like a spider's knee and the hand draws in toward the
    # glass, a tug to one side at the end of the stroke; then it eases back out, re-gripping, the fingers never still.
    def grip(p, amt=1.0):
        return curl(CLUTCH * amt, lambda i: 5 * math.sin(TAU * (p * 2 + i * 0.27)))

    m.animation("pull", 30, {
        0: merge(arm(**HOLD), grip(0.0)),
        8: merge(arm(**mix(HOLD, DRAWN, 0.6), ua_yaw=2), grip(0.27, 1.05)),
        14: merge(arm(**DRAWN, ua_yaw=5, roll=-6), grip(0.47, 1.1)),
        19: merge(arm(**DRAWN, ua_yaw=-3, roll=4), grip(0.63, 1.05)),
        25: merge(arm(**mix(DRAWN, HOLD, 0.7), ua_yaw=-1), grip(0.83, 0.85)),
    })

    # ---- recoil, 0.3 s, held: struck or shaken off, it flinches (the elbow jerks up, the fingers spasm open) and
    # is sucked back into the glass, folding the wrong way as it goes
    rng = random.Random(188)
    spasm = lambda span: (lambda i: rng.uniform(-span, span))
    m.animation("recoil", 9, {
        0: merge(arm(**HOLD), curl(CLUTCH)),
        2: merge(arm(-62, 112, -25, ua_yaw=8), curl(-0.6, spasm(28), spread=1.6)),
        5: merge(arm(-10, -100, 20, ua_yaw=-6, stretch=(0.55, 0.85, 0.85)), curl(0.2, spasm(30))),
        8: merge(arm(**FOLDED, stretch=(0.04, 0.4, 0.4)), curl(1.0, spasm(15))),
    }, end="Hold")

    # ---- idle, a 2 s loop (added over the rest): the fingers flex one after another, never together; the hand turns
    # a little and the forearm trembles
    def idle(p):
        out = {}
        for i, (n, _, _, _) in enumerate(FINGERS):
            a = 0.5 + 0.5 * math.sin(TAU * (p + i * 0.21))
            for k, s in enumerate("abcd"):
                out[f"Finger{n}{s}"] = pose((0, 0, (4 + 5 * k) * a - 4))
        out["ThumbA"] = pose((0, 0, 12 * (0.5 + 0.5 * math.sin(TAU * (p + 0.6)))))
        out["ThumbB"] = pose((0, 0, 8 * (0.5 + 0.5 * math.sin(TAU * (p + 0.75)))))
        out["Hand"] = pose((3 * math.sin(TAU * (p + 0.5)), 4 * math.sin(TAU * p), 3 * math.sin(TAU * (p + 0.3))))
        out["Forearm"] = pose((0, 1.2 * math.sin(TAU * p * 3), 1.0 * math.sin(TAU * (p * 3 + 0.4))))
        return out

    m.animation("idle", 60, {int(60 * i / 12): idle(i / 12) for i in range(12)})
    return F + parts


def entity():
    # L188System starts reach, then pull, then recoil without stopping the one before (reach and grab hold their last
    # frame), and Average blends by weight: so each later animation outweighs the earlier ones by far, or the drag
    # would play at 60 % and the recoil only half-way into the glass.
    anims = [("idle", "AddAverage", {"triggeredBy": {"defaultAnim": True}}), ("reach", "Average", {"weight": 2}),
             ("grab", "Average", {"weight": 3}), ("pull", "Average", {"weight": 12}), ("recoil", "Average", {"weight": 60})]
    animations = []
    for code, blend, extra in anims:
        a = {"code": code, "animation": code, "animationSpeed": 1.0, "blendMode": blend}
        a.update(extra)
        animations.append(a)
    data = {
        "code": "l188-arm",
        "class": "BackroomsL188Arm" if reg("BackroomsL188Arm") else "EntityAgent",
        "tags": ["backrooms-entity"],
        "weight": 20,
        "hitboxSize": {"x": 0.6, "y": 0.6},
        "selectionBoxSize": {"x": 0.7, "y": 0.6},
        "eyeHeight": 0.3,
        "knockbackResistance": 1,
        "canClimb": False,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-l188-arm"},
        "client": {
            "renderer": "Shape",
            "shape": {"base": f"backrooms:entity/{NAME}"},
            "texture": {"base": f"backrooms:entity/{NAME}"},
            "size": 1.0,
            "behaviors": [{"code": "interpolateposition"}],
            "animations": animations,
        },
        # Placed and driven by L188System (it reaches, grabs, pulls, recoils): no AI tasks, no gravity, no physics
        "server": {"behaviors": [{"code": "health", "currenthealth": 6, "maxhealth": 6}]},
        "sounds": {"hurt": "backrooms:effect/188/recoil", "death": "backrooms:effect/188/recoil"},
        "drops": [],
    }
    path = os.path.join(rig.ASSETS, "entities", "l188-arm.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("// Level 188: a Window's arm (Entity 2). Anchored at a predatory window's centre, reaching along its forward axis (-X); driven by L188System\n")
        f.write(json.dumps(data, indent="\t") + "\n")
    WRITTEN["entities"].append("l188-arm")
    LANG["item-creature-l188-arm"] = "A Window's arm"
    LANG["creature-l188-arm"] = "A Window's arm"


def generate():
    m = build()
    animations(m)
    m.save()
    entity()
    return m


if __name__ == "__main__":
    generate()
