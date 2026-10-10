"""Level 3999's Arcade Attendant (3999-plan.md 3.9, 6.7), a new model built with tools/rig.py.

Canon (Backrooms Fandom wiki, "Level 399: Neon Paradise", formerly Level 3999): "humanoid robots akin to Entity 29"
(the Mannequins), "usually 5 feet tall (152.4 cm)", dressed "in a formal style, comparable to flight attendant
outfits", "they do not have faces and are made of a special type of plastic", they "talk through a speaker embedded in
their head" and calm whoever looks at them. The one interviewed ("R.T.") speaks of herself as a dead wanderer's soul.

So the model is a shop-window mannequin made into a cabin attendant: 152 cm (24.3 model px to the crown; the pillbox
hat to 25.5), human proportions, glossy ivory plastic with a soft specular streak and darker joint seams (neck, knees,
ankles). The head is a mannequin's: a smooth oval face with a moulded nose, the faintest hollows where eyes would be,
no eyes and no mouth; moulded swept-back hair in the same plastic, gathered in a chignon at the nape. The speakers sit
where the ears would be: two small round grilles. The uniform: a fitted, nipped-waist jacket with padded shoulders,
neon piping on the lapels, cuffs, collar and flared hem, a white blouse in the V, gold wings and a name badge on the
left breast, two gold buttons, flap pockets; a neckerchief knotted at the side of the neck, its two tails splayed; a
pillbox hat, tilted, with a piped band and a gold badge; a knee-length pencil skirt with a back slit; white gloves
(the thumb is a part, so the palm-up gestures read); black court shoes with low heels. Two colourways: plum with pink
piping, navy with cyan piping.

Animations: idle (hands clasped at the waist, perfectly still, and once a loop a slow head tilt a little too far),
bow, point (the right arm out to the side, palm up, the head turned to it), serve (both hands forward, palms up, as if
handing over a tray), walk (small, smooth steps, a glide: no bob), wave.

Conventions (rig.py): the model faces -X, its left is +Z, up is +Y. For a hanging limb a negative Z rotation swings it
forward; for an upright part a positive Z rotation leans it forward; a positive X rotation swings a hanging limb
toward -Z (inward for the left arm, outward for the right); a Y rotation turns a part about its long axis.
"""
import json
import os
import re

import rig
from rig import Model, fill, mix, pose, shade
from gen_models import cycle, full, s, texel, line, ramp

from gen_3999_kit import ASSETS, LANG, write_json

PLASTIC = (236, 229, 233)      # warm ivory
PLASTIC_HI = (252, 250, 251)
PLASTIC_LO = (196, 186, 194)
SEAM = (150, 140, 150)
BLOUSE = (244, 242, 246)
GLOVE = (248, 248, 246)
SHOE = (24, 22, 28)
SHOE_HI = (86, 82, 96)
GOLD = (222, 184, 92)
GOLD_LO = (150, 112, 50)
GRILLE = (112, 108, 120)
UNIFORM = (75, 30, 92)      # plum (#4B1E5C)
PIPING = (255, 42, 90)      # hot pink
VARIANTS = {"plum": dict(UNIFORM=(75, 30, 92), PIPING=(255, 42, 90)),
            "navy": dict(UNIFORM=(27, 35, 80), PIPING=(100, 232, 247))}

SIDES = ("north", "south", "east", "west")


def vgrad(ctx, top_k, bottom_k, alpha=1.0):
    """Darkens or lightens a face from top to bottom (multiplies what is there)."""
    px = ctx.img.load()
    for yy in range(ctx.h):
        k = top_k + (bottom_k - top_k) * (yy / max(1, ctx.h - 1))
        k = 1 + (k - 1) * alpha
        for xx in range(ctx.w):
            c = px[ctx.x + xx, ctx.y + yy]
            px[ctx.x + xx, ctx.y + yy] = rig.clamp((c[0] * k, c[1] * k, c[2] * k)) + (255,)


def blob(ctx, cu, cv, ru, rv, colour, alpha):
    """A soft ellipse in face fractions (shading: sockets, cheeks, highlights)."""
    for yy in range(ctx.h):
        for xx in range(ctx.w):
            du = ((xx + 0.5) / ctx.w - cu) / ru
            dv = ((yy + 0.5) / ctx.h - cv) / rv
            d = du * du + dv * dv
            if d < 1:
                texel(ctx, xx, yy, colour, alpha * (1 - d) ** 0.7)


# ---------------------------------------------------------------- plastic

def plastic(ctx, base=None):
    """Glossy moulded plastic: a smooth fill, lighter towards the top, a soft specular streak on the side faces."""
    base = base or PLASTIC
    fill(ctx, base, 0.012)
    if ctx.face in SIDES:
        vgrad(ctx, 1.03, 0.9)
        x0 = max(0, int(ctx.w * 0.28))
        for yy in range(ctx.h):
            for xx in range(x0, min(ctx.w, x0 + max(1, ctx.w // 5))):
                texel(ctx, xx, yy, PLASTIC_HI, 0.5 * (1 - 0.6 * yy / max(1, ctx.h)))
        if ctx.part.tag.get("seam_top"):
            for xx in range(ctx.w):
                texel(ctx, xx, 0, SEAM, 0.7)
        if ctx.part.tag.get("seam_bottom"):
            for xx in range(ctx.w):
                texel(ctx, xx, ctx.h - 1, SEAM, 0.6)
    if ctx.face == "up":
        fill(ctx, PLASTIC_HI, 0.01)
    if ctx.face == "down":
        fill(ctx, PLASTIC_LO, 0.01)


def leg(ctx):
    plastic(ctx)
    if ctx.face in SIDES and ctx.part.tag.get("knee"):
        # the knee joint: a seam ring a little below the top, the kneecap's highlight on the front
        y = 1
        for xx in range(ctx.w):
            texel(ctx, xx, y, SEAM, 0.65)
        if ctx.face == "west":
            blob(ctx, 0.5, 0.06, 0.4, 0.05, PLASTIC_HI, 0.6)


def calf(ctx):
    plastic(ctx)
    if ctx.face in SIDES:
        vgrad(ctx, 1.0, 0.92)


def head(ctx):
    """The mannequin's face: smooth, the faintest hollows where eyes would be, no eyes, no mouth."""
    plastic(ctx)
    if ctx.face == "west" and ctx.part.tag.get("face"):
        # a soft overall light from the front, the brow and cheekbones catching it
        blob(ctx, 0.5, 0.45, 0.55, 0.6, PLASTIC_HI, 0.35)
        for cu in (0.27, 0.73):
            blob(ctx, cu, 0.47, 0.17, 0.09, shade(PLASTIC_LO, 0.92), 0.8)        # the empty sockets
            blob(ctx, cu, 0.33, 0.2, 0.05, PLASTIC_HI, 0.5)           # the brow above
            blob(ctx, cu + (0.04 if cu < 0.5 else -0.04), 0.62, 0.14, 0.08, PLASTIC_HI, 0.45)  # cheekbones
        for xx in range(int(ctx.w * 0.4), int(ctx.w * 0.6 + 0.5)):
            texel(ctx, xx, int(ctx.h * 0.73), PLASTIC_LO, 0.75)          # the nose's shadow
        blob(ctx, 0.5, 0.85, 0.18, 0.045, PLASTIC_LO, 0.3)             # where a mouth would be: only a dip
        blob(ctx, 0.5, 0.96, 0.4, 0.06, PLASTIC_LO, 0.35)              # under the chin
    if ctx.face in ("north", "south") and ctx.part.tag.get("face"):
        # the sides of the head: the jaw's line from the chin up to under the ear, the cheek turning away
        front_left = ctx.face == "south"
        u0, u1 = (0.0, 0.5) if front_left else (1.0, 0.5)
        line(ctx, u0, 0.98, u1, 0.72, PLASTIC_LO, 0.5)
        blob(ctx, 0.12 if front_left else 0.88, 0.55, 0.14, 0.3, PLASTIC_LO, 0.25)


def nose(ctx):
    plastic(ctx)
    if ctx.face == "west":
        for yy in range(ctx.h):
            texel(ctx, ctx.w // 2, yy, PLASTIC_HI, 0.7)
    if ctx.face == "down":
        fill(ctx, PLASTIC_LO, 0.0)


def chin(ctx):
    plastic(ctx)
    if ctx.face in SIDES:
        vgrad(ctx, 1.0, 0.86)


def hair(ctx):
    """Hair moulded in the same plastic, a shade greyer: swept back from a side parting into the chignon."""
    base = shade(PLASTIC, 0.84)
    fill(ctx, base, 0.01)
    groove = shade(PLASTIC, 0.7)
    if ctx.face in ("north", "south"):
        vgrad(ctx, 1.04, 0.9)
        front_left = ctx.face == "south"       # on the south face the front (-X) is at u = 0, on the north at u = 1
        for v0 in (0.2, 0.55):
            u0, u1 = (0.05, 0.95) if front_left else (0.95, 0.05)
            line(ctx, u0, v0, u1, v0 + 0.25, groove, 0.4)
    elif ctx.face == "east":
        vgrad(ctx, 1.02, 0.88)
    elif ctx.face == "west":
        # the hairline on the forehead: its lower edge in shadow, the side parting
        for xx in range(ctx.w):
            texel(ctx, xx, ctx.h - 1, shade(PLASTIC, 0.66), 0.8)
        line(ctx, 0.66, 0.0, 0.7, 0.8, groove, 0.6)
    elif ctx.face == "up":
        line(ctx, 0.0, 0.66, 1.0, 0.7, groove, 0.35)


def bun(ctx):
    fill(ctx, shade(PLASTIC, 0.82), 0.01)
    if ctx.face in SIDES:
        vgrad(ctx, 1.06, 0.86)
        line(ctx, 0.0, 0.5, 1.0, 0.42, shade(PLASTIC, 0.64), 0.6)          # the twist


def speaker(ctx):
    """The voice: a small round grille of pale metal where an ear would be."""
    fill(ctx, PLASTIC, 0.01)
    if ctx.face in ("north", "south"):
        w, h = ctx.w, ctx.h
        fill(ctx, (186, 182, 194), 0.02, face_shade=False)
        for corner in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            texel(ctx, corner[0], corner[1], PLASTIC, 1.0)                   # rounded off
        for yy in range(1, h - 1):
            for xx in range(1, w - 1):
                if (xx + yy) % 2 == 0:
                    texel(ctx, xx, yy, (120, 116, 130))                   # the holes


# ---------------------------------------------------------------- uniform

def cloth(ctx, base=None, var=0.035):
    base = base or UNIFORM
    fill(ctx, base, var)
    # a faint weave: every other column a touch darker
    if ctx.face in SIDES:
        for xx in range(0, ctx.w, 2):
            for yy in range(ctx.h):
                texel(ctx, xx, yy, shade(base, 0.9), 0.25)
    if ctx.face == "up":
        fill(ctx, shade(base, 1.12), 0.02)
    if ctx.face == "down":
        fill(ctx, shade(base, 0.6), 0.02)


def pipe_bottom(ctx):
    for xx in range(ctx.w):
        texel(ctx, xx, ctx.h - 1, PIPING)


def torso(ctx):
    """The jacket's chest: the lapels' V, piped, the blouse inside it, gold wings and a name badge on the left breast."""
    cloth(ctx)
    w, h = ctx.w, ctx.h
    if ctx.face in SIDES:
        vgrad(ctx, 1.06, 0.92)
    if ctx.face == "west":
        # only the top rows (above the chest panel) and the bottom rows (under it) show: the V's top, the closed front
        for yy in range(h):
            if yy < h * 0.2:
                half = int(round(w * 0.2 + 0.3))
                for xx in range(w // 2 - half, w // 2 + half):
                    texel(ctx, xx, yy, BLOUSE, 0.95)
                texel(ctx, w // 2 - half - 1, yy, PIPING)
                texel(ctx, w // 2 + half, yy, PIPING)
            else:
                texel(ctx, w // 2, yy, shade(UNIFORM, 0.62))
                texel(ctx, w // 2 - 1, yy, PIPING, 0.85)
    elif ctx.face == "east":
        for yy in range(h):
            texel(ctx, w // 2, yy, shade(UNIFORM, 0.72), 0.8)            # centre back seam
    elif ctx.face in ("north", "south"):
        for yy in range(h):
            texel(ctx, w // 2, yy, shade(UNIFORM, 0.8), 0.6)             # side seams


def chest(ctx):
    """The front panel over the chest (the bust): the piped lapels close in a V over the blouse two thirds of the way
    down, then the jacket's piped front edge; gold wings over a small name badge on the model's left breast (high u)."""
    cloth(ctx)
    w, h = ctx.w, ctx.h
    if ctx.face == "west":
        vgrad(ctx, 1.06, 0.95)
        close = h * 0.62
        for yy in range(h):
            half = int(round((w * 0.2) * (1 - yy / close) + 0.3)) if yy < close else 0
            if half > 0:
                for xx in range(w // 2 - half, w // 2 + half):
                    texel(ctx, xx, yy, BLOUSE, 0.95)
                texel(ctx, w // 2 - half - 1, yy, PIPING)
                texel(ctx, w // 2 + half, yy, PIPING)
                texel(ctx, max(0, w // 2 - half - 2), yy, shade(UNIFORM, 0.78), 0.55)
                texel(ctx, min(w - 1, w // 2 + half + 1), yy, shade(UNIFORM, 0.78), 0.55)
            else:
                texel(ctx, w // 2, yy, shade(UNIFORM, 0.62))
                texel(ctx, w // 2 - 1, yy, PIPING, 0.85)
        texel(ctx, w // 2 + 1, int(h * 0.82), GOLD)                         # the top button
        bx = int(w * 0.76)
        wy = int(h * 0.2)
        for dx in range(-2, 3):
            texel(ctx, bx + dx, wy, GOLD)
        texel(ctx, bx - 2, wy - 1, GOLD, 0.8)
        texel(ctx, bx + 2, wy - 1, GOLD, 0.8)
        by = wy + 2
        for xx in range(bx - 2, bx + 2):
            texel(ctx, xx, by, (238, 236, 228))
            texel(ctx, xx, by + 1, GOLD_LO, 0.8)
        texel(ctx, bx - 1, by, (70, 66, 76), 0.7)
        texel(ctx, bx, by, (70, 66, 76), 0.7)
    elif ctx.face in ("north", "south"):
        vgrad(ctx, 1.0, 0.9)


def waist(ctx):
    """The nipped waist: the jacket closed over it, the front edge down the middle, two gold buttons."""
    cloth(ctx)
    w, h = ctx.w, ctx.h
    if ctx.face in SIDES:
        vgrad(ctx, 0.95, 0.88)
    if ctx.face == "west":
        for yy in range(h):
            texel(ctx, w // 2, yy, shade(UNIFORM, 0.62))
            texel(ctx, w // 2 - 1, yy, PIPING, 0.85)                      # the piped front edge (it closes left over right)
        for yy in (int(h * 0.25), int(h * 0.75)):
            texel(ctx, w // 2 + 1, yy, GOLD)
            texel(ctx, w // 2 + 2, yy, GOLD_LO, 0.6)
        # darts from the bust down to the waist
        for xx in (int(w * 0.22), int(w * 0.78)):
            line(ctx, xx / w, 0, xx / w, 1, shade(UNIFORM, 0.78), 0.5)
    elif ctx.face == "east":
        for yy in range(h):
            texel(ctx, w // 2, yy, shade(UNIFORM, 0.72), 0.8)


def peplum(ctx):
    """The jacket's flared hem over the hips: piped along the bottom, flap pockets, the fronts cut away."""
    cloth(ctx)
    w, h = ctx.w, ctx.h
    if ctx.face in SIDES:
        vgrad(ctx, 0.9, 0.82)
        pipe_bottom(ctx)
    if ctx.face == "west":
        for yy in range(h - 1):
            texel(ctx, w // 2, yy, shade(UNIFORM, 0.62))
            texel(ctx, w // 2 - 1, yy, PIPING, 0.85)
        # the fronts curve away: a small notch at the bottom middle
        for k in range(2):
            texel(ctx, w // 2 - 1 - k, h - 1 - k, shade(UNIFORM, 0.5))
            texel(ctx, w // 2 + k, h - 1 - k, shade(UNIFORM, 0.5))
        # the pocket flaps
        for x0, x1 in ((int(w * 0.1), int(w * 0.36)), (int(w * 0.64), int(w * 0.9))):
            for xx in range(x0, x1):
                texel(ctx, xx, int(h * 0.25), shade(UNIFORM, 1.15), 0.7)
                texel(ctx, xx, int(h * 0.25) + 1, shade(UNIFORM, 0.6), 0.8)
    elif ctx.face == "east":
        for yy in range(h):
            texel(ctx, w // 2, yy, shade(UNIFORM, 0.45))                # the back vent


def shoulders(ctx):
    cloth(ctx)
    if ctx.face == "up":
        # the shoulder seams, piped like epaulettes
        for xx in range(ctx.w):
            texel(ctx, xx, 1, PIPING, 0.75)
            texel(ctx, xx, ctx.h - 2, PIPING, 0.75)
    if ctx.face in SIDES:
        vgrad(ctx, 1.08, 0.96)


def collar(ctx):
    cloth(ctx)
    if ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, 0, PIPING)
    if ctx.face == "west":
        fill(ctx, BLOUSE, 0.01)


def sleeve(ctx):
    cloth(ctx)
    if ctx.face in SIDES:
        vgrad(ctx, 1.05, 0.9)
        if ctx.part.tag.get("cuff"):
            for yy in (ctx.h - 3, ctx.h - 2):
                for xx in range(ctx.w):
                    texel(ctx, xx, yy, shade(UNIFORM, 0.8))
            pipe_bottom(ctx)
            for xx in range(ctx.w):
                texel(ctx, xx, ctx.h - 4, PIPING, 0.85)
        else:
            # the elbow's creases, low on the upper arm
            line(ctx, 0.1, 0.88, 0.9, 0.84, shade(UNIFORM, 0.75), 0.5)


def skirt(ctx):
    base = shade(UNIFORM, 0.88)
    cloth(ctx, base)
    w, h = ctx.w, ctx.h
    if ctx.face in SIDES:
        vgrad(ctx, 0.96, 0.84)
        # soft vertical folds
        for u in (0.2, 0.5, 0.8):
            line(ctx, u, 0.15, u + 0.02, 1.0, shade(base, 0.8), 0.35)
        if ctx.part.tag.get("hem"):
            for xx in range(w):
                texel(ctx, xx, h - 1, shade(base, 0.62))
                texel(ctx, xx, h - 2, shade(base, 0.8), 0.6)
    if ctx.face == "east" and ctx.part.tag.get("hem"):
        for yy in range(int(h * 0.35), h):
            texel(ctx, w // 2, yy, shade(base, 0.35))                     # the back slit


def kerchief(ctx):
    base = PIPING
    fill(ctx, base, 0.03)
    if ctx.face in SIDES:
        vgrad(ctx, 1.05, 0.8)
        # a thin white diagonal stripe, like a cabin crew scarf
        for yy in range(ctx.h):
            texel(ctx, (yy * 2) % max(1, ctx.w + 3), yy, (250, 248, 250), 0.7)
    if ctx.face == "down":
        fill(ctx, shade(base, 0.55), 0.02)


def glove(ctx):
    fill(ctx, GLOVE, 0.015)
    if ctx.face in SIDES:
        vgrad(ctx, 1.0, 0.9)
    if ctx.face in ("north", "south") and not ctx.part.tag.get("thumb"):
        # the fingers: grooves down the lower half, the knuckles across
        for xx in range(1, ctx.w - 1, max(2, ctx.w // 4)):
            line(ctx, xx / ctx.w, 0.45, xx / ctx.w, 1.0, (200, 200, 204), 0.7)
        for xx in range(ctx.w):
            texel(ctx, xx, int(ctx.h * 0.42), (214, 214, 218), 0.6)
    if ctx.face in ("west", "east") and not ctx.part.tag.get("thumb"):
        for xx in range(ctx.w):
            texel(ctx, xx, 0, (210, 210, 214), 0.6)


def shoe(ctx):
    fill(ctx, SHOE, 0.04)
    if ctx.face == "up":
        fill(ctx, SHOE_HI, 0.03)
        for xx in range(ctx.w):
            texel(ctx, xx, ctx.h // 2, (140, 136, 150), 0.4)
    elif ctx.face in SIDES:
        for xx in range(ctx.w):
            texel(ctx, xx, 0, SHOE_HI, 0.8)                                 # the glossy top edge
        if ctx.part.tag.get("sole"):
            for xx in range(ctx.w):
                texel(ctx, xx, ctx.h - 1, (8, 8, 10))


def hat(ctx):
    """The pillbox: the uniform's cloth, a piped band, a gold badge on the front."""
    cloth(ctx)
    w, h = ctx.w, ctx.h
    if ctx.face in SIDES:
        vgrad(ctx, 1.1, 0.9)
        pipe_bottom(ctx)
        for xx in range(w):
            texel(ctx, xx, h - 2, shade(UNIFORM, 0.7))
            texel(ctx, xx, 0, shade(UNIFORM, 1.25), 0.6)                    # the crown's edge catches the light
        if ctx.face == "west" and ctx.part.tag.get("badge"):
            cx, cy = w // 2, h // 2 - 1
            for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1), (-2, -1), (2, -1)):
                texel(ctx, cx + dx, cy + dy, GOLD)
    if ctx.face == "up":
        fill(ctx, shade(UNIFORM, 1.18), 0.02)


PY = 80
CL = [6, -6, 46, -24, 10, 12]


def attendant():
    rig.TEXEL = 4   # finer texels: the piping, the badge and the speaker grilles stay small
    m = Model("3999/attendant", atlas_width=64, seed=3999)

    # ---- Hips and skirt (the root). Hip joints at 12, knees at 7, a knee-length pencil skirt from the waist to 7.4
    hips = m.part("Hips", (-1.5, 10.0, -2.2), (3.0, 4.6, 4.4), pivot=(0, 12.4, 0), paint=skirt)
    m.part("SkirtLow", (-1.4, 7.4, -2.05), (2.8, 2.6, 4.1), pivot=(0, 12.4, 0), parent=hips, paint=skirt, tag={"hem": True})
    thigh = m.part("ThighL", (-0.65, 7.0, 0.22), (1.3, 5.4, 1.36), pivot=(0, 12.0, 0.9), parent=hips, paint=plastic)
    shin = m.part("ShinL", (-0.56, 0.8, 0.3), (1.12, 6.3, 1.2), pivot=(0, 7.0, 0.9), parent=thigh, paint=leg, tag={"knee": True})
    m.part("CalfL", (-0.42, 3.4, 0.25), (1.2, 2.9, 1.3), pivot=(0, 7.0, 0.9), parent=shin, paint=calf)
    m.part("ShoeL", (-1.62, 0.0, 0.24), (1.87, 0.82, 1.32), pivot=(0, 1.0, 0.9), parent=shin, paint=shoe, tag={"sole": True})
    m.part("ShoeBackL", (-0.2, 0.3, 0.22), (0.95, 0.85, 1.36), pivot=(0, 1.0, 0.9), parent=shin, paint=shoe)
    m.part("HeelL", (0.3, 0.0, 0.52), (0.4, 0.35, 0.76), pivot=(0, 1.0, 0.9), parent=shin, paint=shoe)
    m.mirror("ThighL", "ThighR")

    # ---- The jacket. Its pivot is the hip line, so a bow folds at the hips
    torso = m.part("Torso", (-1.5, 15.2, -2.15), (3.0, 3.6, 4.3), pivot=(0, 12.4, 0), parent=hips, paint=torso_paint)
    m.part("Peplum", (-1.72, 12.1, -2.4), (3.44, 1.45, 4.8), pivot=(0, 12.4, 0), parent=torso, paint=peplum)
    m.part("Waist", (-1.38, 13.55, -1.95), (2.76, 1.7, 3.9), pivot=(0, 12.4, 0), parent=torso, paint=waist)
    m.part("Chest", (-1.82, 15.8, -1.9), (0.34, 2.6, 3.8), pivot=(0, 12.4, 0), parent=torso, paint=chest, faces=("west", "up", "down", "north", "south"))
    m.part("Shoulders", (-1.45, 18.8, -2.55), (2.9, 0.8, 5.1), pivot=(0, 12.4, 0), parent=torso, paint=shoulders)
    m.part("Collar", (-0.95, 19.6, -1.1), (1.95, 0.35, 2.2), pivot=(0, 12.4, 0), parent=torso, paint=collar)
    # The neckerchief, knotted at the side of the neck (the model's left), its two tails splayed
    m.part("Kerchief", (-0.8, 19.75, -0.78), (1.6, 0.55, 1.56), pivot=(0, 12.4, 0), parent=torso, paint=kerchief)
    m.part("KerchiefKnot", (-1.05, 19.45, 0.3), (0.62, 0.62, 0.72), pivot=(0, 12.4, 0), parent=torso, paint=kerchief)
    m.part("KerchiefTailA", (-1.12, 18.35, 0.42), (0.3, 1.15, 0.62), pivot=(-0.97, 19.5, 0.73), parent=torso, rest=(-24, 0, 6), paint=kerchief)
    m.part("KerchiefTailB", (-1.08, 18.45, 0.5), (0.3, 1.05, 0.58), pivot=(-0.95, 19.5, 0.79), parent=torso, rest=(18, 0, 10), paint=kerchief)

    # ---- Neck and the mannequin's head: chin at 20.9, crown at 24.3
    neck = m.part("Neck", (-0.58, 19.5, -0.58), (1.16, 1.8, 1.16), pivot=(0, 19.8, 0), parent=torso, paint=plastic)
    # The skull, a narrower chin under it, a moulded nose; moulded hair as a cap over the crown and the back of the
    # head (a hairline 0.1 proud of the forehead), a small chignon low at the back; the speakers where the ears would be
    hd = m.part("Head", (-1.45, 21.25, -1.35), (2.85, 2.9, 2.7), pivot=(0, 21.0, 0), parent=neck, paint=head, tag={"face": True})
    m.part("Chin", (-1.38, 20.85, -0.92), (2.0, 0.42, 1.84), pivot=(0, 21.0, 0), parent=hd, paint=chin)
    m.part("Nose", (-1.72, 22.05, -0.22), (0.28, 0.8, 0.44), pivot=(0, 21.0, 0), parent=hd, paint=nose)
    m.part("HairTop", (-1.56, 23.45, -1.48), (3.1, 0.9, 2.96), pivot=(0, 21.0, 0), parent=hd, paint=hair)
    m.part("HairBack", (0.15, 21.6, -1.48), (1.39, 1.85, 2.96), pivot=(0, 21.0, 0), parent=hd, paint=hair, tag={"back": True})
    m.part("Bun", (1.54, 22.0, -0.66), (0.52, 1.1, 1.32), pivot=(0, 21.0, 0), parent=hd, paint=bun)
    m.part("SpeakerL", (-0.8, 21.95, 1.35), (0.92, 0.92, 0.16), pivot=(0, 21.0, 0), parent=hd, paint=speaker)
    m.part("SpeakerR", (-0.8, 21.95, -1.51), (0.92, 0.92, 0.16), pivot=(0, 21.0, 0), parent=hd, paint=speaker)
    # The pillbox hat, tilted to one side and a little back, on the crown
    hatp = m.part("Hat", (-1.0, 24.15, -1.0), (2.0, 1.1, 2.0), pivot=(0, 24.2, 0), parent=hd, rest=(9, 0, -6), paint=hat, tag={"badge": True})
    m.part("HatX", (-1.2, 24.15, -0.62), (2.4, 1.1, 1.24), pivot=(0, 24.2, 0), parent=hatp, paint=hat, tag={"badge": True})
    m.part("HatZ", (-0.62, 24.15, -1.2), (1.24, 1.1, 2.4), pivot=(0, 24.2, 0), parent=hatp, paint=hat)

    # ---- Arms: shoulder joints at 19, elbows at 15.5 (the waist), wrists at 12, fingertips at 10
    upper = m.part("UpperArmL", (-0.6, 15.45, 2.08), (1.2, 4.2, 1.2), pivot=(0, 19.0, 2.68), parent=torso, rest=(-3, 0, 0), paint=sleeve)
    fore = m.part("ForearmL", (-0.55, 11.95, 2.13), (1.1, 3.6, 1.1), pivot=(0, 15.5, 2.68), parent=upper, paint=sleeve, tag={"cuff": True})
    hand = m.part("HandL", (-0.56, 10.05, 2.33), (1.12, 1.95, 0.7), pivot=(0, 12.0, 2.68), parent=fore, paint=glove)
    m.part("ThumbL", (-0.78, 10.75, 2.22), (0.42, 0.95, 0.42), pivot=(-0.55, 11.7, 2.4), parent=hand, rest=(0, 0, -8), paint=glove, tag={"thumb": True})
    m.mirror("UpperArmL", "UpperArmR")

    arms = ["UpperArmL", "UpperArmR", "ForearmL", "ForearmR", "HandL", "HandR"]
    legs = ["ThighL", "ThighR", "ShinL", "ShinR"]
    core = ["Hips", "Torso", "Neck", "Head"]

    def clasp(k=1.0):
        """Hands clasped in front at the waist, the left over the right, as cabin crew stand."""
        return {"UpperArmL": pose((CL[0] * k, 0, CL[1] * k)), "UpperArmR": pose((-CL[0] * k, 0, CL[1] * k)),
                "ForearmL": pose((CL[2] * k, 0, CL[3] * k)), "ForearmR": pose((-CL[2] * k, 0, CL[3] * k)),
                "HandL": pose((CL[4] * k, 0, CL[5] * k)), "HandR": pose((-CL[4] * k, 0, CL[5] * k))}

    # Idle: hands clasped, perfectly still; once a loop the head tilts slowly, a little too far, and holds
    def idle(p):
        tilt = ramp(p, 0.45, 0.62, 0.8, 0.95)
        tilt = tilt * tilt * (3 - 2 * tilt)
        d = clasp()
        d.update({"Head": pose((17 * tilt, -5 * tilt, 3 * tilt)), "Neck": pose((3 * tilt, 0, 0)),
                  "Torso": pose((0, 0, s(p, 0.5, 0.2)))})
        return d
    m.animation("idle", 120, cycle(120, 24, idle))

    # Bow: hands clasped, a deep, slow bow from the hips, held, and up
    bow_names = core + arms
    bowed = dict(clasp(), Torso=pose((0, 0, 32)), Head=pose((0, 0, 8)))
    m.animation("bow", 50, {0: full(bow_names, clasp()), 14: full(bow_names, bowed), 30: full(bow_names, bowed),
                            49: full(bow_names, clasp())}, end="Stop")

    # Point: the right arm out to the side and forward, palm up ("the way out is this way"), the head turned to it
    point_pose = dict(clasp(), UpperArmR=pose((0, -45, -60)), ForearmR=pose((0, 0, -10)), HandR=pose((0, PY, -4)),
                      UpperArmL=pose((6, 0, -6)), ForearmL=pose((30, 0, -40)), HandL=pose((0, 0, 0)),
                      Head=pose((4, -32, 0)), Torso=pose((0, -10, 0)))
    m.animation("point", 40, {0: full(bow_names, clasp()), 12: full(bow_names, point_pose), 39: full(bow_names, point_pose)}, end="Hold")

    # Serve: both hands forward at waist height, palms up, as if handing over a tray; held
    serve_pose = {"UpperArmL": pose((4, 0, -22)), "UpperArmR": pose((-4, 0, -22)), "ForearmL": pose((0, 0, -62)), "ForearmR": pose((0, 0, -62)),
                  "HandL": pose((0, -85, 0)), "HandR": pose((0, 85, 0)), "Torso": pose((0, 0, 6)), "Head": pose((0, 0, 8))}
    m.animation("serve", 30, {0: full(bow_names, clasp()), 12: full(bow_names, serve_pose), 29: full(bow_names, serve_pose)}, end="Hold")

    # Walk: small, smooth steps under the pencil skirt, hands clasped, the head level: a glide
    walk_names = core + arms + legs
    def walk(p):
        leg = 11 * s(p, 1)
        d = clasp(0.95)
        d.update({"ThighL": pose((0, 0, leg)), "ThighR": pose((0, 0, -leg)),
                  "ShinL": pose((0, 0, max(0.0, -leg) * 0.7)), "ShinR": pose((0, 0, max(0.0, leg) * 0.7)),
                  "Hips": pose((0, s(p, 2), 0)), "Torso": pose((0, s(p, -2.5), 2)), "Head": pose((0, s(p, 1), -2))})
        return {k: d.get(k, pose()) for k in walk_names}
    m.animation("walk", 40, cycle(40, 10, walk))

    # Wave: the right hand raised beside the head, palm out, the forearm rocking
    def wave_pose(r):
        return dict(clasp(), UpperArmR=pose((50, 0, -18)), ForearmR=pose((130 + r, 0, 0)), HandR=pose((0, -80, 0)),
                    UpperArmL=pose((6, 0, -6)), ForearmL=pose((30, 0, -40)), HandL=pose((0, 0, 0)), Head=pose((-6, 0, 0)))
    m.animation("wave", 48, {0: full(bow_names, clasp()), 8: full(bow_names, wave_pose(0)), 16: full(bow_names, wave_pose(-18)),
                             24: full(bow_names, wave_pose(18)), 32: full(bow_names, wave_pose(-18)), 40: full(bow_names, wave_pose(0)),
                             47: full(bow_names, clasp())}, end="Stop")
    rig.TEXEL = 2
    return m


torso_paint = torso


def save_variants():
    g = globals()
    saved = {k: g[k] for v in VARIANTS.values() for k in v}
    for vname, palette in VARIANTS.items():
        g.update(palette)
        m = attendant()
        rig.TEXEL = 4
        width, height = m._pack()
        path = os.path.join(ASSETS, "textures", "entity", "3999", f"attendant-{vname}.png")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        m._paint(width, height).save(path)
        rig.TEXEL = 2
        g.update(saved)


def entity_json():
    anim = lambda code, weight=None, blend="Average", **kw: dict({"code": code, "animation": code, "animationSpeed": 1.0, "blendMode": blend},
                                                                  **({"weight": weight} if weight else {}), **kw)
    data = {
        "code": "l3999-attendant",
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "humanoid"],
        "weight": 60,
        "hitboxSize": {"x": 0.5, "y": 1.55},
        "eyeHeight": 1.38,
        "attributes": {"invulnerable": True, "l3999attendant": True},
        "client": {
            "renderer": "Shape",
            "shape": {"base": "backrooms:entity/3999/attendant"},
            "texture": {"base": "backrooms:entity/3999/attendant-plum", "alternates": [{"base": "backrooms:entity/3999/attendant-navy"}]},
            "size": 1.0,
            "behaviors": [{"code": "repulseagents"}, {"code": "controlledphysics", "stepHeight": 1.01}, {"code": "interpolateposition"}],
            "animations": [
                anim("idle", triggeredBy={"defaultAnim": True}, easeOutSpeed=4),
                anim("walk", 3), anim("bow", 6), anim("point", 6), anim("serve", 6), anim("wave", 6),
            ],
        },
        "server": {
            "attributes": {"pathfinder": {"minTurnAnglePerSec": 360, "maxTurnAnglePerSec": 720}},
            "behaviors": [
                {"code": "repulseagents"},
                {"code": "controlledphysics", "stepHeight": 1.01},
                {"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": [
                    {"code": "lookatentity", "priority": 1.5, "maxTurnAngleDeg": 120, "entityCodes": ["player"], "minduration": 2000,
                     "maxduration": 6000, "mincooldown": 1000, "maxcooldown": 3000},
                    {"code": "idle", "priority": 1.2, "minduration": 3000, "maxduration": 6000, "mincooldown": 8000, "maxcooldown": 20000,
                     "animation": "bow", "sound": "backrooms:effect/3999/chime", "soundRange": 8},
                    {"code": "wander", "priority": 1.0, "movespeed": 0.008, "animation": "walk", "executionChance": 0.004,
                     "maxDistanceToSpawn": 6, "wanderRangeMin": 2, "wanderRangeMax": 5},
                    {"code": "lookaround", "priority": 0.5},
                ]},
                {"code": "entitystatetags"},
            ],
        },
        "sounds": {"idle": "backrooms:effect/3999/voice*", "hurt": "backrooms:effect/3999/chime"},
        "idleSoundChance": 0.03,
        "idleSoundRange": 8,
    }
    path = os.path.join(ASSETS, "entities", "3999", "attendant.json")
    write_json(path, data, "Level 3999's Arcade Attendant (3999-plan.md 3.9): a faceless plastic mannequin, polite, in a plum or navy "
                           "flight-attendant uniform, speaking through a speaker in its head. No health behaviour, so it cannot be hurt; the code (L3999System) puts it behind counters and on concourses, "
                           "makes it bow, point the way and serve, and speaks for it")
    LANG.update({"item-creature-l3999-attendant": "Arcade Attendant", "entity-l3999-attendant": "Arcade Attendant",
                 "creature-l3999-attendant": "Arcade Attendant"})
    return path


def generate():
    m = attendant()
    rig.TEXEL = 4
    m.save()
    rig.TEXEL = 2
    save_variants()
    path = entity_json()
    return path
