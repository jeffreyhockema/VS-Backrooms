"""Level 974: Kitty, the house's one resident (docs/new-levels/974-plan.md section 4.5). Called from gen_974.py.

3.2 m tall (51 model px), faceless, matt black like mosou fabric, its long limbs ending in points: no hands, no feet.
A silhouette before anything else (checked against Wikidot's photo, newkitty.jpg): a small egg-shaped head carried
forward on a thin neck, shoulders sloping away from it, a rounded hunch between the shoulder blades, arms hanging to the
knees, legs as long as the torso and head together. It never walks where anyone can see; it idles, tilts its head,
stoops under lintels, peeks round door jambs, glides out of the way, holds out an arm for its gift, takes it, bends
over a sleeper, kneels by the cat bed, and stretches a little as it comes and goes.

Rig conventions (rig.py): the model faces -X, its left is +Z, feet at y = 0, parts given in model space as if every
parent were unrotated. +Z rotation on the torso leans it forward; a hanging limb swings forward with -Z and out to its
own side with -X (left) / +X (right).
"""
import json
import math
import os

import rig
from rig import Model, pose

TAU = math.tau
NAME = "974/l974-kitty"
BLACK = (10, 10, 12)
WEAVE = (18, 18, 22)


def s(phase, amp, shift=0.0):
    return amp * math.sin(TAU * (phase + shift))


def cycle(frames, steps, fn):
    return {int(round(frames * i / steps)): fn(i / steps) for i in range(steps)}


def ramp(p, a, b, c, d):
    if p <= a or p >= d:
        return 0.0
    if p < b:
        return (p - a) / (b - a)
    if p <= c:
        return 1.0
    return (d - p) / (d - c)


def cloth(ctx):
    """Matt black, a faint one-texel cross-hatch weave at 20 %. No highlights, no face shading: the top is as dark as the sides."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            c = BLACK
            if (xx + yy) % 2 == 0 or (xx - yy) % 4 == 0:
                c = rig.mix(BLACK, WEAVE, 0.2 + 0.05 * ctx.rng.random())
            px[ctx.x + xx, ctx.y + yy] = c + (255,)


def build():
    m = Model(NAME, atlas_width=32, seed=974)
    # ---- Legs: hips 5 px wide; thighs and shins long and thin, ending in points (no feet: it stands on them)
    pelvis = m.part("Pelvis", (-1.75, 26, -2.5), (3.5, 3, 5), pivot=(0, 27.5, 0), paint=cloth)
    thigh = m.part("ThighL", (-1.5, 13, 0.1), (3, 13.5, 3), pivot=(0, 26.5, 1.6), parent=pelvis, rest=(-3, 0, 0), paint=cloth)
    shin = m.part("ShinL", (-1.1, 2, 0.5), (2.2, 11.2, 2.2), pivot=(0, 13.2, 1.6), parent=thigh, rest=(2, 0, 2), paint=cloth)
    tip = m.part("LegTipL", (-0.8, 0.8, 0.8), (1.6, 1.4, 1.6), pivot=(0, 2, 1.6), parent=shin, paint=cloth)
    m.part("LegPointL", (-0.4, 0, 1.2), (0.8, 0.8, 0.8), pivot=(0, 0.8, 1.6), parent=tip, paint=cloth)
    # ---- Torso: a narrow waist widening to a chest of 8, a rounded hunch between the shoulder blades, and shoulders
    # that slope away from the neck (the photo's silhouette: no squared-off shoulders)
    waist = m.part("Waist", (-1.75, 29, -2.5), (3.5, 6.2, 5), pivot=(0, 29, 0), parent=pelvis, rest=(0, 0, 3), paint=cloth)
    chest = m.part("Chest", (-1.75, 35, -4), (3.5, 6, 8), pivot=(0, 35, 0), parent=waist, rest=(0, 0, 3), paint=cloth)
    m.part("Ribs", (-1.5, 33.6, -3.2), (3.0, 1.6, 6.4), pivot=(0, 35, 0), parent=chest, paint=cloth)
    m.part("Hunch", (1.6, 36.4, -3.0), (1.0, 4.4, 6.0), pivot=(1.6, 38.6, 0), parent=chest, paint=cloth)
    m.part("ShoulderL", (-1.5, 40.0, 0.9), (3.0, 1.8, 3.9), pivot=(0, 41, 0.9), parent=chest, rest=(17, 0, 0), paint=cloth)
    m.part("ShoulderR", (-1.5, 40.0, -4.8), (3.0, 1.8, 3.9), pivot=(0, 41, -0.9), parent=chest, rest=(-17, 0, 0), paint=cloth)
    # ---- Neck and head: a thin neck angled forward carrying the head ahead of the shoulders; the head a small egg,
    # taller than wide and narrower at the chin, built of a core and six inset slabs. No features at all.
    neck = m.part("Neck", (-1, 40.5, -1), (2, 3.8, 2), pivot=(0, 40.8, 0), parent=chest, rest=(0, 0, 10), paint=cloth)
    head = m.part("Head", (-2.2, 45.0, -2.0), (4.4, 5.4, 4.0), pivot=(0, 44.4, 0), parent=neck, rest=(0, 0, -6), paint=cloth)
    m.part("Cap", (-1.6, 50.4, -1.4), (3.2, 0.7, 2.8), pivot=(0, 50.4, 0), parent=head, paint=cloth)
    m.part("Chin", (-1.4, 44.3, -1.2), (2.8, 0.7, 2.4), pivot=(0, 44.4, 0), parent=head, paint=cloth)
    m.part("Brow", (-2.7, 45.9, -1.4), (0.5, 3.8, 2.8), pivot=(0, 47, 0), parent=head, paint=cloth)
    m.part("Crown", (2.2, 45.6, -1.5), (0.6, 4.2, 3.0), pivot=(0, 47, 0), parent=head, paint=cloth)
    m.part("CheekL", (-1.6, 45.9, 2.0), (3.3, 3.8, 0.45), pivot=(0, 47, 0), parent=head, paint=cloth)
    m.part("CheekR", (-1.6, 45.9, -2.45), (3.3, 3.8, 0.45), pivot=(0, 47, 0), parent=head, paint=cloth)
    # ---- Arms: from the shoulder (40) to the elbow (28), forearm to 15, then a point to about knee height. Each
    # segment thinner than the last: 2.5, 2, 1.2, 0.6.
    arm = m.part("ArmL", (-1.25, 28, 2.75), (2.5, 12.4, 2.5), pivot=(0, 39.6, 4.0), parent=chest, rest=(-4, 0, 0), paint=cloth)
    fore = m.part("ForearmL", (-1, 15, 3.0), (2, 13.4, 2), pivot=(0, 28.2, 4.0), parent=arm, rest=(1, 0, -3), paint=cloth)
    atip = m.part("ArmTipL", (-0.6, 13.4, 3.4), (1.2, 1.8, 1.2), pivot=(0, 15.1, 4.0), parent=fore, paint=cloth)
    m.part("ArmPointL", (-0.3, 12, 3.7), (0.6, 1.5, 0.6), pivot=(0, 13.5, 4.0), parent=atip, paint=cloth)
    m.mirror("ArmL", "ArmR")
    m.mirror("ThighL", "ThighR")
    return m


def animations(m):
    names = [p.name for p in m.parts]

    def full(d, keep=()):
        """Every part this animation touches, at rest unless d poses it."""
        out = {n: pose() for n in keep}
        out.update(d)
        return out

    def lerp(a, b, t):
        """Two poses dicts blended (rotations and offsets); parts missing on one side are at rest there."""
        out = {}
        for k in set(a) | set(b):
            pa, pb = a.get(k, pose()), b.get(k, pose())
            out[k] = pose(tuple(pa["rot"][i] + (pb["rot"][i] - pa["rot"][i]) * t for i in range(3)),
                          tuple(pa["off"][i] + (pb["off"][i] - pa["off"][i]) * t for i in range(3)))
        return out

    def ease(t):
        return t * t * (3 - 2 * t)

    # ---- idle: 8 s. Breathing in the chest and the hunch, a slow sway of the weight from one point to the other, the
    # head drifting and once a loop turning a little toward something; the right arm's point curls and uncurls, and
    # later, more slowly, the left's.
    def idle(p):
        breath = 0.5 - 0.5 * math.cos(TAU * p * 2)
        curl_r = ramp(p, 0.52, 0.60, 0.70, 0.80)
        curl_l = ramp(p, 0.08, 0.20, 0.26, 0.38)
        look = ramp(p, 0.30, 0.40, 0.50, 0.62)
        sway = s(p, 1.0)
        return {
            "Pelvis": pose((sway, 0, 0), (0, 0, 0.25 * s(p, 1))),
            "ThighL": pose((-sway, 0, 0)), "ThighR": pose((-sway, 0, 0)),
            "Waist": pose((-0.4 * sway, 0, 0)),
            "Chest": pose((0, 0, 0.8 * breath), s=(1, 1 + 0.01 * breath, 1 + 0.01 * breath)),
            "Hunch": pose((0, 0, 0), (0.12 * breath, 0, 0)),
            "Neck": pose((s(p, 1.5, 0.1) - 0.6 * sway, s(p, 3) + 9 * look, s(p, 1.5, 0.3) - 0.6 * breath)),
            "Head": pose((s(p, 2, 0.4) + 4 * look, 4 * look, 0)),
            "ArmL": pose((s(p, 0.8) - 0.5 * sway, 0, s(p, 1.2, 0.2))), "ArmR": pose((-s(p, 0.8, 0.5) - 0.5 * sway, 0, s(p, 1.2, 0.7))),
            "ForearmL": pose((0, 0, -6 * curl_l)), "ForearmR": pose((0, 0, -4 * curl_r)),
            "ArmTipL": pose((0, 0, -22 * curl_l)), "ArmPointL": pose((0, 0, -18 * curl_l)),
            "ArmTipR": pose((0, 0, -35 * curl_r)), "ArmPointR": pose((0, 0, -25 * curl_r)),
        }

    m.animation("idle", 240, cycle(240, 24, idle))

    # ---- headtilt: 1.2 s. Quick and cat-like: the head rolls 22 degrees with a little overshoot, holds, turns a few
    # degrees as if listening, and settles back slowly.
    hk = ["Neck", "Head", "Chest"]
    m.animation("headtilt", 36, {
        0: full({}, hk),
        7: full({"Head": pose((25, 3, 2)), "Neck": pose((5, 2, 0)), "Chest": pose((1.5, 0, 0))}, hk),
        11: full({"Head": pose((21, 0, 1)), "Neck": pose((4, 0, 0)), "Chest": pose((1, 0, 0))}, hk),
        22: full({"Head": pose((22, -7, 3)), "Neck": pose((4, -2, 1)), "Chest": pose((1, 0, 0))}, hk),
        35: full({}, hk)}, end="Stop")

    # ---- glide: a 1 s loop. Leaning 8 degrees forward from the hips, the legs barely shifting (+-4), the arms trailing
    # back and the points trailing further, the head held level; no bob, no step.
    def glide(p):
        return {"Pelvis": pose((0, 0, 8)), "ThighL": pose((0, 0, -8 + s(p, 4))), "ThighR": pose((0, 0, -8 - s(p, 4))),
                "ShinL": pose((0, 0, 3 + s(p, 2, 0.2))), "ShinR": pose((0, 0, 3 - s(p, 2, 0.2))),
                "ArmL": pose((0, 0, 11 + s(p, 1.5))), "ArmR": pose((0, 0, 11 - s(p, 1.5))),
                "ForearmL": pose((0, 0, 5)), "ForearmR": pose((0, 0, 5)),
                "ArmTipL": pose((0, 0, 9 + s(p, 4, 0.3))), "ArmTipR": pose((0, 0, 9 - s(p, 4, 0.3))),
                "Neck": pose((0, 0, -4)), "Head": pose((0, 0, -4))}

    m.animation("glide", 30, cycle(30, 6, glide))

    # ---- stoop: under a lintel, in over 0.6 s and held; 30 degrees from waist and chest, the neck +15, the head tipped
    # back a little to keep facing ahead, the arms hanging plumb
    sk = ["Waist", "Chest", "Neck", "Head", "ArmL", "ArmR", "ForearmL", "ForearmR"]
    stoop = {"Waist": pose((0, 0, 12)), "Chest": pose((0, 0, 18)), "Neck": pose((0, 0, 15)), "Head": pose((0, 0, -12)),
             "ArmL": pose((0, 0, -26)), "ArmR": pose((0, 0, -26)), "ForearmL": pose((0, 0, -4)), "ForearmR": pose((0, 0, -4))}
    m.animation("stoop", 18, {0: full({}, sk), 10: full(lerp({}, stoop, 0.8), sk), 17: full(stoop, sk)}, end="Hold")

    # ---- peek: leaning 35 degrees out to its right from behind a jamb (on its left), as in Fandom's photo; the head
    # rolled the other way, the left arm's point resting on the jamb at shoulder height, the right arm hanging plumb
    pk = ["Pelvis", "ThighL", "ThighR", "Waist", "Chest", "Neck", "Head", "ArmL", "ForearmL", "ArmTipL", "ArmPointL", "ArmR", "ForearmR"]
    peek = {"Pelvis": pose((-22, 0, 3), (0, 0, 1.0)), "ThighL": pose((22, 0, -3)), "ThighR": pose((22, 0, -3)),
            "Waist": pose((-8, 0, 2)), "Chest": pose((-5, 0, 2)),
            "Neck": pose((12, 0, 4)), "Head": pose((-15, 0, 0)),
            "ArmL": pose((-50, 0, -42)), "ForearmL": pose((0, 0, -60)), "ArmTipL": pose((0, 0, -25)), "ArmPointL": pose((0, 0, -20)),
            "ArmR": pose((35, 0, 0)), "ForearmR": pose((0, 0, -4))}
    m.animation("peek", 24, {0: full({}, pk), 12: full(lerp({}, peek, 0.75), pk), 23: full(peek, pk)}, end="Hold")

    # ---- ask: 1.5 s, then held. The right arm rises slowly to horizontal, the forearm lagging behind the upper arm, its
    # point curling up 30 degrees as if to say "give it here"; the head tilts 15 degrees, the chest leans back a touch.
    ak = ["ArmR", "ForearmR", "ArmTipR", "ArmPointR", "Neck", "Head", "Chest"]
    ask = {"ArmR": pose((6, 0, -84)), "ForearmR": pose((0, 0, -4)), "ArmTipR": pose((0, 0, -30)), "ArmPointR": pose((0, 0, -20)),
           "Neck": pose((0, 0, 4)), "Head": pose((15, 0, 0)), "Chest": pose((0, 0, -3))}
    lag = {"ArmR": pose((4, 0, -40)), "ForearmR": pose((0, 0, 14)), "ArmTipR": pose((0, 0, 10)), "ArmPointR": pose((0, 0, 6)),
           "Neck": pose((0, 0, 2)), "Head": pose((8, 0, 0)), "Chest": pose((0, 0, -1))}
    m.animation("ask", 45, {0: full({}, ak), 18: full(lag, ak), 34: full(lerp(lag, ask, 0.85), ak), 44: full(ask, ak)}, end="Hold")

    # ---- take: 1.2 s. The offered arm draws the gift back to the chest, the other comes up to meet it, both points
    # crossing over the breastbone; the head bows 20 degrees over it.
    tk = ak + ["ArmL", "ForearmL", "ArmTipL", "ArmPointL"]
    took = {"ArmR": pose((-14, 0, -30)), "ForearmR": pose((22, 0, -102)), "ArmTipR": pose((0, 0, -25)), "ArmPointR": pose((0, 0, -15)),
            "ArmL": pose((14, 0, -28)), "ForearmL": pose((-24, 0, -98)), "ArmTipL": pose((0, 0, -25)), "ArmPointL": pose((0, 0, -15)),
            "Neck": pose((0, 0, 14)), "Head": pose((0, 0, 8)), "Chest": pose((0, 0, 4))}
    m.animation("take", 36, {0: full(ask, tk), 10: full(lerp(ask, took, 0.6), tk), 18: full(took, tk), 35: full(took, tk)}, end="Stop")

    # ---- sleepwatch: bent over a sleeper in over 1 s, held. Hips pitched 35, chest 25 more, head 20 down, the arms
    # hanging straight down beside the bed.
    wk = ["Pelvis", "ThighL", "ThighR", "Waist", "Chest", "Neck", "Head", "ArmL", "ArmR"]
    watch = {"Pelvis": pose((0, 0, 35), (0, -1.0, 0)), "ThighL": pose((0, 0, -35)), "ThighR": pose((0, 0, -35)),
             "Waist": pose((0, 0, 12)), "Chest": pose((0, 0, 13)), "Neck": pose((0, 0, 12)), "Head": pose((0, 0, 8)),
             "ArmL": pose((-3, 0, -60)), "ArmR": pose((3, 0, -60))}
    m.animation("sleepwatch", 30, {0: full({}, wk), 16: full(lerp({}, watch, 0.8), wk), 29: full(watch, wk)}, end="Hold")

    # ---- kneel: folded down by the cat bed, about 30 px tall. Sitting back on its shins (thighs forward along the
    # floor, shins folded under them, the points trailing behind), the body upright and leaning a little over the bed;
    # the long arms folded like a mantis's: the upper arms reaching forward, the forearms hanging so the points rest
    # on the knees.
    kk = ["Pelvis", "ThighL", "ThighR", "ShinL", "ShinR", "LegTipL", "LegTipR", "Waist", "Chest", "Neck", "Head",
          "ArmL", "ArmR", "ForearmL", "ForearmR", "ArmTipL", "ArmTipR"]
    kneel = {"Pelvis": pose((0, 0, 0), (0, -23.0, 0)), "ThighL": pose((3, 0, -84)), "ThighR": pose((-3, 0, -84)),
             "ShinL": pose((0, 0, 172)), "ShinR": pose((0, 0, 172)), "LegTipL": pose((0, 0, 12)), "LegTipR": pose((0, 0, 12)),
             "Waist": pose((0, 0, 6)), "Chest": pose((0, 0, 8)), "Neck": pose((0, 0, 10)), "Head": pose((0, 0, -2)),
             "ArmL": pose((4, 0, -38)), "ArmR": pose((-4, 0, -38)), "ForearmL": pose((0, 0, -66)), "ForearmR": pose((0, 0, -66)),
             "ArmTipL": pose((0, 0, 80)), "ArmTipR": pose((0, 0, 80))}
    # On the way down the legs fold first, then the arms
    mid = lerp({}, kneel, 0.55)
    mid.update({"ArmL": pose((2, 0, -30)), "ArmR": pose((-2, 0, -30)), "ForearmL": pose((0, 0, -20)), "ForearmR": pose((0, 0, -20))})
    m.animation("kneel", 40, {0: full({}, kk), 20: full(mid, kk), 39: full(kneel, kk)}, end="Hold")

    # ---- vanish / appear: 0.25 s, a stretch of the whole figure, 1 -> 1.05 tall and a little thinner, the head lifting
    # and the arms drawn in to the sides, as if it were pulled up and out of the room
    vk = ["Pelvis", "Neck", "ArmL", "ArmR"]
    thin = {"Pelvis": pose(s=(0.9, 1.05, 0.9)), "Neck": pose((0, 0, -6)), "ArmL": pose((3, 0, 0)), "ArmR": pose((-3, 0, 0))}
    rest = {"Pelvis": pose(s=(1, 1, 1)), "Neck": pose(), "ArmL": pose(), "ArmR": pose()}
    m.animation("vanish", 8, {0: full(rest, vk), 7: full(thin, vk)}, end="Hold")
    m.animation("appear", 8, {0: full(thin, vk), 7: full(rest, vk)}, end="Stop")
    return names


def entity(LANG):
    anims = [
        ("idle", "AddAverage", {"triggeredBy": {"defaultAnim": True}}),
        ("headtilt", "AddAverage", {"weight": 2}),
        ("glide", "Average", {}),
        ("walk", "Average", {"animation": "glide"}),
        ("stoop", "Average", {}),
        ("peek", "Average", {}),
        ("ask", "Average", {"weight": 2}),
        ("take", "Average", {"weight": 3}),
        ("sleepwatch", "Average", {}),
        ("kneel", "Average", {}),
        ("vanish", "Average", {"weight": 5}),
        ("appear", "Average", {"weight": 5}),
    ]
    animations = []
    for code, blend, extra in anims:
        a = {"code": code, "animation": extra.pop("animation", code), "animationSpeed": 1.0, "blendMode": blend}
        a.update(extra)
        animations.append(a)
    data = {
        "code": "l974-kitty",
        "class": "EntityKitty",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": 60,
        "hitboxSize": {"x": 0.7, "y": 2.9},
        "selectionBoxSize": {"x": 0.8, "y": 3.2},
        "eyeHeight": 2.9,
        "canClimb": False,
        "attributes": {"invulnerable": True},
        "client": {
            "renderer": "Shape",
            "shape": {"base": f"backrooms:entity/{NAME}"},
            "texture": {"base": f"backrooms:entity/{NAME}"},
            "size": 1.0,
            "behaviors": [{"code": "interpolateposition"}],
            "animations": animations,
        },
        # Kitty is driven by L974System (it appears, vanishes and glides; it never paths): no taskai, no health
        "server": {"behaviors": [{"code": "controlledphysics", "stepHeight": 0.6}]},
        "sounds": {},
    }
    path = os.path.join(rig.ASSETS, "entities", "l974-kitty.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("// Kitty (Level 974): faceless, 3.2 m, matt black, never harms. Class EntityKitty; driven by L974System\n")
        f.write(json.dumps(data, indent="\t") + "\n")
    LANG["item-creature-l974-kitty"] = "Kitty"
    LANG["creature-l974-kitty"] = "Kitty"


def generate(LANG=None):
    m = build()
    animations(m)
    m.save()
    if LANG is not None:
        entity(LANG)
    return m


if __name__ == "__main__":
    generate()
