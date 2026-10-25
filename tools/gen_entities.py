"""The Backrooms' entities: the entity types, the Facelings' clothes and hair, Firesalt, and their names.

The entities' own models and textures (Smiler, Hound, Skin-Stealer, Duller, Death Rat, Deathmoths, Clump, the
Mangled, The Thing) are made by gen_models.py, which this runs first. Facelings are the one exception: the lore makes
them human in every way but the face, so they are the game's own faceless body, given hair here and dressed in plain
clothes painted onto its body parts.

What each entity does is set in its task config (see src/Entities/AiTaskMenace.cs and AiTaskMoth.cs).

Run from the repo root:  python tools/gen_entities.py
"""
import json
import math
import os
import random
import re

from PIL import Image, ImageDraw

import rig
from rig import speckle, hlines, vlines, rect, mix, shade, clamp
from rig import lit_fill as fill   # B17: shade_fill's soft mottle and hue on the baked Faceling atlas (rig.fill elsewhere)
from gen_models import blotch, line

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
GAME = os.environ.get("VINTAGE_STORY", os.path.join(os.environ.get("APPDATA", ""), "Vintagestory"))
VANILLA = os.path.join(GAME, "assets")
TAB, NL = "\t", "\n"


def vanilla(path):
    return os.path.join(VANILLA, *path.split("/"))


def save_texture(img, name):
    path = os.path.join(ASSETS, "textures", "entity", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT))


def write_json(data, *parts):
    path = os.path.join(ASSETS, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(data, indent="\t", ensure_ascii=False) + "\n")
    print("wrote", os.path.relpath(path, ROOT))


# ---------------------------------------------------------------- Textures

# ---------------------------------------------------------------- Facelings
# "Humanlike in every way but the face": the game's own faceless body (so they stand, walk, wave, nod, sit and stretch
# exactly like a player), given hair and clothes. The clothes and hair are attachment boxes on the body parts, one
# union of them in the shape; each look paints the ones it wears and leaves the rest transparent, so the one shape
# serves every look. The face is skin: a forehead that catches the light, temples and a jaw in shadow, a little warmth
# on the cheeks, and nothing else. Textures are 4 texels to the model pixel (128 wide).

SCALE = 4                 # texels per shape unit (the seraph's units are model pixels)
BODY_TOP = 76             # the body's UVs end here; the attachments' strip starts below
TOOLS = {"Knife", "saw", "saw2", "saw3", "saw4", "Shovel1", "Shovel2"}

# Attachments: (name, parent, from relative to the parent's corner, size). The head is 5.5 x 5 x 5 and faces -x.
ATTACHMENTS = [
    # Hair
    ("HairTop", "Head", (-0.3, 4.6, -0.3), (6.1, 1.0, 5.6)),
    ("HairPuff", "Head", (-0.6, 4.4, -0.6), (6.7, 1.9, 6.2)),          # a thick curly top
    ("HairBack", "Head", (5.3, 0.6, -0.3), (0.5, 4.4, 5.6)),
    ("HairSideL", "Head", (0.9, 2.2, 5.0), (4.6, 2.8, 0.3)),
    ("HairSideR", "Head", (0.9, 2.2, -0.3), (4.6, 2.8, 0.3)),
    ("HairBobL", "Head", (0.6, -0.6, 5.05), (5.0, 5.4, 0.35)),         # hair down past the jaw either side
    ("HairBobR", "Head", (0.6, -0.6, -0.4), (5.0, 5.4, 0.35)),
    ("HairFringe", "Head", (-0.35, 3.7, -0.3), (0.5, 0.9, 5.6)),
    ("HairLong", "Head", (5.35, -4.2, 0.2), (0.6, 5.0, 4.6)),           # down the back to the shoulder blades
    ("HairPony", "Head", (5.6, -1.5, 1.6), (0.9, 5.2, 1.8)),            # a ponytail from the crown
    # Clothes
    ("Collar", "UpperTorso", (-0.45, 4.3, 0.7), (5.9, 1.3, 4.8)),
    ("Jacket", "UpperTorso", (-0.35, -0.6, -0.4), (5.7, 5.9, 7.0)),
    ("SleeveL", "UpperArmL", (-0.3, -0.3, -0.3), (3.6, 7.6, 2.6)),
    ("SleeveR", "UpperArmR", (-0.3, -0.3, -0.3), (3.6, 7.6, 2.6)),
    ("CoatSkirt", "LowerTorso", (-0.4, -4.6, -0.4), (5.8, 5.0, 6.8)),
    ("Skirt", "LowerTorso", (-0.45, -5.6, -0.45), (5.9, 6.0, 6.9)),
    # Accessories
    ("Backpack", "UpperTorso", (5.0, 0.3, 0.9), (2.3, 4.6, 4.4)),
    ("Bag", "LowerTorso", (0.6, -2.4, 6.0), (3.6, 3.4, 1.3)),
    ("Glasses", "Head", (-0.4, 1.5, -0.35), (0.4, 1.2, 5.7)),
    ("GlassesArmL", "Head", (-0.2, 2.2, 5.0), (3.4, 0.3, 0.3)),
    ("GlassesArmR", "Head", (-0.2, 2.2, -0.3), (3.4, 0.3, 0.3)),
    ("Beanie", "Head", (-0.55, 3.0, -0.55), (6.6, 2.7, 6.1)),
    ("Cap", "Head", (-0.5, 4.0, -0.5), (6.5, 1.7, 6.0)),
    ("CapBrim", "Head", (-3.0, 4.3, -0.3), (2.8, 0.4, 5.6)),
]
ATTACH_BY_NAME = {a[0]: a for a in ATTACHMENTS}

# Skin tones: (base, name). Faces are painted from these alone.
SKINS = {
    "light": (236, 206, 184), "fair": (242, 216, 196), "tan": (212, 170, 134), "olive": (198, 160, 120),
    "brown": (150, 104, 76), "dark": (98, 68, 52), "weathered": (214, 184, 160),
}
HAIR_COLOURS = {
    "black": (26, 22, 22), "darkbrown": (58, 40, 30), "brown": (104, 70, 44), "auburn": (124, 62, 40),
    "blonde": (196, 164, 104), "dirtyblonde": (150, 124, 82), "grey": (150, 148, 144), "white": (214, 212, 206),
}
HAIR_STYLES = {           # which hair boxes each style paints
    "bald": (), "buzz": ("HairTop", "HairBack"), "short": ("HairTop", "HairBack", "HairSideL", "HairSideR", "HairFringe"),
    "long": ("HairTop", "HairBack", "HairSideL", "HairSideR", "HairFringe", "HairLong"),
    "bob": ("HairTop", "HairBack", "HairBobL", "HairBobR", "HairFringe"),
    "ponytail": ("HairTop", "HairBack", "HairSideL", "HairSideR", "HairPony"),
    "curly": ("HairPuff", "HairBack", "HairSideL", "HairSideR"),
}

# A look: skin, hair (style, colour), top (kind, colour, accent), bottom (kind, colour), shoes (kind, colour), extras.
# Tops: tshirt, sweater, hoodie, blouse, jacket (over a tshirt), suit (over a shirt and tie), coat, overalls, cardigan.
# Bottoms: jeans, slacks, shorts, skirt. Shoes: sneakers, boots, dress. Extras: glasses, beanie, cap, backpack, bag.
LOOKS = {
    "casual":    dict(skin="light", hair=("long", "darkbrown"), top=("jacket", (96, 102, 70), (30, 30, 32)), bottom=("jeans", (74, 92, 124)), shoes=("boots", (96, 68, 44)), extras=()),
    "workwear":  dict(skin="tan", hair=("short", "black"), top=("tshirt", (92, 106, 122), None), bottom=("jeans", (54, 62, 80)), shoes=("boots", (72, 50, 34)), extras=("backpack",)),
    "hoodie":    dict(skin="fair", hair=("curly", "black"), top=("hoodie", (136, 136, 140), None), bottom=("jeans", (66, 80, 108)), shoes=("sneakers", (230, 230, 226)), extras=()),
    "elderly":   dict(skin="weathered", hair=("short", "grey"), top=("cardigan", (108, 84, 112), (226, 222, 212)), bottom=("slacks", (92, 84, 74)), shoes=("dress", (40, 30, 26)), extras=("glasses",)),
    "business":  dict(skin="brown", hair=("buzz", "black"), top=("suit", (44, 46, 56), (150, 40, 44)), bottom=("slacks", (44, 46, 56)), shoes=("dress", (28, 24, 22)), extras=()),
    "overalls":  dict(skin="light", hair=("ponytail", "dirtyblonde"), top=("overalls", (70, 84, 112), (150, 54, 48)), bottom=("jeans", (70, 84, 112)), shoes=("boots", (84, 58, 38)), extras=()),
    "outdoor":   dict(skin="tan", hair=("short", "brown"), top=("coat", (150, 128, 96), (84, 64, 44)), bottom=("jeans", (62, 70, 90)), shoes=("boots", (70, 50, 36)), extras=("beanie",)),
    "summer":    dict(skin="dark", hair=("long", "black"), top=("tshirt", (232, 228, 218), None), bottom=("shorts", (120, 106, 86)), shoes=("sneakers", (222, 220, 214)), extras=()),
    "winter":    dict(skin="fair", hair=("bald", "grey"), top=("coat", (48, 44, 50), (36, 32, 36)), bottom=("slacks", (40, 38, 42)), shoes=("boots", (34, 28, 26)), extras=("bag",)),
    "office":    dict(skin="light", hair=("bob", "auburn"), top=("blouse", (236, 234, 228), None), bottom=("skirt", (46, 46, 56)), shoes=("dress", (30, 26, 28)), extras=()),
    "guest":     dict(skin="brown", hair=("short", "grey"), top=("suit", (62, 56, 70), (210, 206, 196)), bottom=("slacks", (62, 56, 70)), shoes=("dress", (34, 28, 26)), extras=("glasses",)),
    "suburban":  dict(skin="light", hair=("ponytail", "blonde"), top=("sweater", (196, 130, 140), None), bottom=("jeans", (90, 108, 140)), shoes=("sneakers", (236, 234, 230)), extras=()),
    "street":    dict(skin="dark", hair=("curly", "darkbrown"), top=("jacket", (78, 96, 130), (200, 196, 186)), bottom=("slacks", (50, 48, 46)), shoes=("sneakers", (40, 40, 44)), extras=("cap",)),
    "teacher":   dict(skin="olive", hair=("long", "brown"), top=("sweater", (120, 128, 96), None), bottom=("skirt", (80, 70, 60)), shoes=("dress", (60, 44, 36)), extras=("glasses", "bag")),
    # APPEND ONLY (texture indices are saved with the entities). Level 3's Evolved Facelings: the lore's half-formed face
    # (a lumpy brow, a slit where a mouth would be, two shallow dimples for eyes), worn by every Faceling put down
    # there. MenaceSystem.ChooseLook gives it by index (EvolvedLook, the last one); never chosen elsewhere.
    "evolved":   dict(skin="weathered", hair=("bald", "grey"), top=("tshirt", (118, 116, 108), None), bottom=("slacks", (68, 64, 58)), shoes=("boots", (48, 42, 38)), extras=(), evolved=True),
}


# Children: smaller, in play clothes; the same faceless face
CHILD_LOOKS = {
    "child-stripes":  dict(skin="fair", hair=("short", "brown"), top=("tshirt", (196, 84, 70), None), bottom=("shorts", (70, 86, 120)), shoes=("sneakers", (226, 224, 220)), extras=()),
    "child-hoodie":   dict(skin="tan", hair=("curly", "black"), top=("hoodie", (88, 132, 160), None), bottom=("jeans", (66, 80, 108)), shoes=("sneakers", (60, 60, 66)), extras=("backpack",)),
    "child-dress":    dict(skin="light", hair=("ponytail", "blonde"), top=("blouse", (232, 196, 120), None), bottom=("skirt", (150, 74, 96)), shoes=("dress", (60, 36, 40)), extras=()),
    "child-overalls": dict(skin="brown", hair=("short", "black"), top=("overalls", (82, 106, 140), (236, 200, 90)), bottom=("jeans", (82, 106, 140)), shoes=("sneakers", (200, 70, 60)), extras=()),
    "child-sweater":  dict(skin="olive", hair=("bob", "darkbrown"), top=("sweater", (110, 150, 110), None), bottom=("slacks", (70, 64, 60)), shoes=("boots", (90, 62, 40)), extras=("beanie",)),
    "child-school":   dict(skin="dark", hair=("buzz", "black"), top=("cardigan", (60, 70, 110), (230, 230, 226)), bottom=("slacks", (60, 62, 70)), shoes=("dress", (30, 26, 26)), extras=("backpack",)),
}


def walk(elements):
    for e in elements:
        yield e
        yield from walk(e.get("children", []))


def attachment_uvs():
    """Each attachment's faces laid out in rows below the body's texture: {part: {face: [u1, v1, u2, v2]}}."""
    out, x, y, row = {}, 0.0, float(BODY_TOP), 0.0
    q = 1 / SCALE
    for name, _, _, (sx, sy, sz) in ATTACHMENTS:
        faces = {"north": (sx, sy), "south": (sx, sy), "east": (sz, sy), "west": (sz, sy), "up": (sx, sz), "down": (sx, sz)}
        out[name] = {}
        for face, (w, h) in faces.items():
            w, h = max(q, math.ceil(w / q) * q), max(q, math.ceil(h / q) * q)
            if x + w > 32:
                x, y, row = 0.0, y + row + q, 0.0
            out[name][face] = [x, y, x + w, y + h]
            x += w + q
            row = max(row, h)
    return out, int(math.ceil((y + row) / 8) * 8)


def _rest(names):
    return {n: {"offsetX": 0, "offsetY": 0, "offsetZ": 0, "rotationX": 0, "rotationY": 0, "rotationZ": 0} for n in names}


def _key(frame, names, poses):
    elements = _rest(names)
    for n, (rx, ry, rz) in poses.items():
        elements[n].update({"rotationX": rx, "rotationY": ry, "rotationZ": rz})
    return {"frame": frame, "elements": elements}


def point_animation():
    """A Faceling points the way: the right arm comes up level and holds there a moment too long, the head turning
    after it. (The seraph's arms swing forward with -Z.)"""
    names = ["UpperArmR", "LowerArmR", "UpperTorso", "Neck"]
    held = {"UpperArmR": (6, 0, -84), "LowerArmR": (0, 0, -4), "UpperTorso": (0, -8, 0), "Neck": (0, -6, 0)}
    return {"name": "point", "code": "point", "quantityframes": 90, "onActivityStopped": "EaseOut", "onAnimationEnd": "Stop",
            "keyframes": [_key(0, names, {}), _key(14, names, held), _key(70, names, dict(held, Neck=(0, -10, 0))), _key(89, names, {})]}


def faceling_shape():
    """The faceless body with every attachment box on it, and room in the texture for them. Also the child's shape:
    the same body, drawn smaller by the entity, with a head a fifth larger."""
    shape = json.load(open(vanilla("game/shapes/entity/humanoid/seraph-faceless.json"), encoding="utf-8-sig"))
    uvs, height = attachment_uvs()
    shape["textureHeight"] = height
    # The seraph declares its texture's size per texture code, and that wins over textureWidth/Height: without this
    # every face samples the texture at the wrong height (the bug of 2026-10-06: a body of misplaced squares)
    shape.setdefault("textureSizes", {})["seraph"] = [32, height]
    parts = {e["name"]: e for e in walk(shape["elements"])}
    for name, parent, frm, size in ATTACHMENTS:
        p = parts[parent]
        p["children"] = p.get("children") or []
        p["children"].append({
            "name": name, "from": list(frm), "to": [frm[i] + size[i] for i in range(3)], "rotationOrigin": list(frm),
            "faces": {face: {"texture": "#seraph", "uv": uv} for face, uv in uvs[name].items()},
        })
    # (FloatUpWhenStuck looks for a Center point)
    lower = parts["LowerTorso"]
    lower["attachmentpoints"] = [{"code": "Center", "posX": 2.5, "posY": 2.5, "posZ": 3.0, "rotationX": 0, "rotationY": 0, "rotationZ": 0}]
    shape["animations"].append(point_animation())
    write_json(shape, "shapes", "entity", "faceling.json")

    # The child: a head a fifth larger, scaled about the neck with everything on it (hair, hats, glasses)
    child = json.loads(json.dumps(shape))
    head = next(e for e in walk(child["elements"]) if e["name"] == "Head")
    k = 1.2
    o = head["rotationOrigin"]
    for key in ("from", "to"):
        head[key] = [o[i] + (head[key][i] - o[i]) * k for i in range(3)]

    def scale_children(e):
        for c in e.get("children") or []:
            for key in ("from", "to", "rotationOrigin"):
                if key in c:
                    c[key] = [v * k for v in c[key]]
            scale_children(c)

    scale_children(head)
    write_json(child, "shapes", "entity", "faceling-child.json")


class _Ctx:
    pass


# B17: light baked into each look from the shape's rest pose (rig.bake_shape): occlusion under hair, collars, sleeves
# and hems, round limbs, darker shoes; the clothes get a weave. None paints the looks as before.
FACELING_LIGHT = dict(round_px=3.0, grad=0.2, edge=0.08, foot=0.05, ground_h=4.0)


def _ctx(img, part, face, uv, rng):
    """A painting context like rig.py's, for one face of the seraph's texture."""
    u1, v1, u2, v2 = uv
    x0, x1 = sorted((int(round(u1 * SCALE)), int(round(u2 * SCALE))))
    y0, y1 = sorted((int(round(v1 * SCALE)), int(round(v2 * SCALE))))
    c = _Ctx()
    c.img, c.draw, c.x, c.y, c.w, c.h, c.face, c.part, c.rng = img, ImageDraw.Draw(img), x0, y0, max(1, x1 - x0), max(1, y1 - y0), face, part, rng
    c.baked = FACELING_LIGHT is not None
    return c


def clear_rect(ctx, u0, v0, u1, v1):
    """Cuts a rectangle (face fractions) out to transparency: an open jacket front, a lens, a ragged hem."""
    px = ctx.img.load()
    for yy in range(int(v0 * ctx.h), int(math.ceil(v1 * ctx.h))):
        for xx in range(int(u0 * ctx.w), int(math.ceil(u1 * ctx.w))):
            if 0 <= xx < ctx.w and 0 <= yy < ctx.h:
                px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)


def ragged(ctx, depth=3):
    px = ctx.img.load()
    for xx in range(ctx.w):
        cut = ctx.rng.choice([0] * 3 + list(range(1, depth + 1)))
        for yy in range(ctx.h - cut, ctx.h):
            px[ctx.x + xx, ctx.y + yy] = (0, 0, 0, 0)


# ---- Skin and the face

def paint_skin(ctx, base, weathered=False, freckles=False):
    fill(ctx, base, 0.025)
    blotch(ctx, shade(base, 0.9), 1, 2, 5, 0.25)
    if weathered:
        speckle(ctx, shade(base, 0.72), 0.02)                        # age spots
        blotch(ctx, mix(base, (170, 120, 110), 0.5), 1, 1.5, 3, 0.25)
    if freckles:
        speckle(ctx, shade(base, 0.8), 0.03)


def paint_face(ctx, base, weathered):
    """The blank face: the anatomy is in the light, not in features. A forehead that catches light, temples and
    cheeks falling into shadow, a touch of warmth over the cheekbones, the jaw darker; and nothing at all else."""
    paint_skin(ctx, base, weathered)
    w, h = ctx.w, ctx.h
    px = ctx.img.load()
    for yy in range(h):
        v = (yy + 0.5) / h
        for xx in range(w):
            u = (xx + 0.5) / w
            k = 1.0
            k += 0.07 * max(0.0, 1 - abs(v - 0.22) / 0.22)                      # the forehead's light
            k -= 0.05 * max(0.0, 1 - abs(v - 0.46) / 0.08)                      # the brow's shadow line, faint
            edge = min(u, 1 - u)
            k -= 0.09 * max(0.0, 1 - edge / 0.18) * (0.4 + 0.6 * max(0.0, 1 - abs(v - 0.5) / 0.5))  # temples and cheek hollows
            k -= 0.10 * max(0.0, (v - 0.84) / 0.16)                             # the jaw in shadow
            k += 0.03 * max(0.0, 1 - abs(v - 0.62) / 0.1) * max(0.0, 1 - abs(u - 0.5) / 0.12)  # the nose's plane, barely
            old = px[ctx.x + xx, ctx.y + yy]
            c = clamp(tuple(ch * k for ch in old[:3]))
            warm = 0.12 * max(0.0, 1 - abs(v - 0.6) / 0.12) * max(0.0, 1 - abs(abs(u - 0.5) - 0.28) / 0.14)  # cheek warmth
            if warm > 0:
                c = mix(c, (210, 120, 110), warm)
            px[ctx.x + xx, ctx.y + yy] = c + (255,)


def paint_evolved_face(ctx, base):
    """A face that has not finished forming: the blank face with a lumpy brow ridge, two shallow dimples where eyes
    would be and a slit, barely lipped, for a mouth. Only shading, as the blank face is."""
    paint_face(ctx, base, True)
    w, h = ctx.w, ctx.h
    px = ctx.img.load()
    rng = random.Random("evolved-face")
    bumps = [rng.uniform(-0.04, 0.04) for _ in range(w)]
    eyes = ((0.29, 0.52), (0.71, 0.5))
    for yy in range(h):
        v = (yy + 0.5) / h
        for xx in range(w):
            u = (xx + 0.5) / w
            k = 1.0
            # the brow: a ridge across, uneven, lit on top and shadowed under
            ridge = 0.33 + bumps[xx] + 0.03 * math.sin(u * 17)
            k += 0.13 * max(0.0, 1 - abs(v - (ridge - 0.04)) / 0.07)
            k -= 0.20 * max(0.0, 1 - abs(v - (ridge + 0.07)) / 0.07)
            # the dimples: soft shallow hollows with a pale rim
            for (eu, ev) in eyes:
                d = math.hypot((u - eu) * 1.0, (v - ev) * 1.0)
                k -= 0.55 * max(0.0, 1 - d / 0.11) ** 0.8
                k += 0.08 * max(0.0, 1 - abs(d - 0.13) / 0.035)
            # the slit: a dark line, with a puckered lip above and below
            mid = 0.74 + 0.012 * math.sin(u * 11)
            if 0.27 < u < 0.73:
                edge = min(u - 0.27, 0.73 - u) / 0.46
                k -= 0.55 * max(0.0, 1 - abs(v - mid) / (0.022 + 0.012 * edge))
                k += 0.07 * max(0.0, 1 - abs(abs(v - mid) - 0.05) / 0.03)
            old = px[ctx.x + xx, ctx.y + yy]
            px[ctx.x + xx, ctx.y + yy] = clamp(tuple(ch * k for ch in old[:3])) + (255,)


# ---- Clothes

def knit(ctx, colour):
    fill(ctx, colour, 0.04)
    if ctx.baked:   # B17: knit stitches in columns of vees, the old ribbing kept faint
        rig.weave(ctx, 6.0, "knit", slubs=0.0)
        hlines(ctx, shade(colour, 0.92), 4, start=1, alpha=0.35)
        return
    hlines(ctx, shade(colour, 0.9), 2, start=1, alpha=0.5)
    vlines(ctx, shade(colour, 1.06), 4, start=2, alpha=0.3)


def cloth(ctx, colour, var=0.035):
    fill(ctx, colour, var)
    blotch(ctx, shade(colour, 0.92), 1, 2, 5, 0.3)
    if ctx.baked:
        rig.weave(ctx, 3.5 if sum(colour) > 300 else 4.5, "plain")      # B17: a plain weave, a few slubs


def denim(ctx, colour, knees=False):
    fill(ctx, colour, 0.05)
    if ctx.baked:   # B17: denim's twill instead of the old stripes; faded threads
        rig.weave(ctx, 6.0, "twill", slubs=0.06)
        speckle(ctx, shade(colour, 1.15), 0.02)
        if knees and ctx.face == "west":
            blotch(ctx, mix(colour, (200, 200, 200), 0.35), 1, 2.5, 4, 0.5)
        return
    vlines(ctx, shade(colour, 1.08), 3, start=1, alpha=0.25, jitter=0)
    speckle(ctx, shade(colour, 1.15), 0.04)
    if knees and ctx.face == "west":
        blotch(ctx, mix(colour, (200, 200, 200), 0.35), 1, 2.5, 4, 0.5)      # worn at the knee


def seam(ctx, colour, side="both"):
    if ctx.face in ("north", "south"):
        line(ctx, 0.5, 0.0, 0.5, 1.0, colour, 0.6)                           # the side seam


def paint_top(ctx, look, name, side):
    """The torso and arm skin or clothing, by the look's top."""
    kind, colour, accent = look["top"]
    skin = SKINS[look["skin"]]
    weathered = look["skin"] == "weathered"
    long_sleeve = kind not in ("tshirt", "overalls")
    if name in ("UpperTorso", "LowerTorso"):
        if kind == "suit":                          # a shirt and tie under the jacket box
            cloth(ctx, (226, 224, 216), 0.03)
            if ctx.face == "west" and name == "UpperTorso":
                rect(ctx, 0.42, 0.0, 0.58, 1.0, accent)
                rect(ctx, 0.46, 0.0, 0.54, 0.12, shade(accent, 0.8))
            if ctx.face == "west" and name == "LowerTorso":
                rect(ctx, 0.42, 0.0, 0.58, 0.45, accent)
        elif kind == "jacket":                      # a tee under the jacket box
            cloth(ctx, accent, 0.03)
        elif kind == "coat":
            cloth(ctx, shade(colour, 0.85), 0.03)   # the coat's lining shows in the open front
        elif kind == "cardigan":                    # a shirt under the cardigan box
            cloth(ctx, accent, 0.03)
            if ctx.face == "west":
                for v in (0.2, 0.45, 0.7):
                    rect(ctx, 0.47, v, 0.53, v + 0.05, shade(accent, 0.7))
        elif kind == "overalls":                    # a tee, with the bib and straps over it
            cloth(ctx, accent, 0.03)
            if name == "LowerTorso":
                denim(ctx, colour)
            elif ctx.face == "west":
                rect(ctx, 0.22, 0.35, 0.78, 1.0, colour)
                rect(ctx, 0.3, 0.55, 0.7, 0.8, shade(colour, 0.9))        # the bib pocket
                for u in (0.22, 0.68):
                    rect(ctx, u, 0.0, u + 0.1, 0.4, colour)
            elif ctx.face == "east":
                for u in (0.25, 0.65):
                    rect(ctx, u, 0.0, u + 0.1, 1.0, colour)
            elif ctx.face in ("north", "south"):
                rect(ctx, 0.0, 0.6, 1.0, 1.0, colour)
        elif kind in ("sweater",):
            knit(ctx, colour)
        elif kind == "hoodie":
            cloth(ctx, colour)
            if ctx.face == "west" and name == "LowerTorso":
                rect(ctx, 0.15, 0.1, 0.85, 0.7, shade(colour, 0.9))        # the kangaroo pocket
                line(ctx, 0.15, 0.1, 0.85, 0.1, shade(colour, 0.75), 0.6)
            if ctx.face == "west" and name == "UpperTorso":
                for u in (0.42, 0.56):
                    line(ctx, u, 0.0, u, 0.55, (220, 218, 210), 0.8)       # drawstrings
            if ctx.face == "east" and name == "UpperTorso":
                rect(ctx, 0.0, 0.0, 1.0, 0.45, shade(colour, 0.85))        # the hood, down
        elif kind == "blouse":
            cloth(ctx, colour, 0.02)
            if ctx.face == "west":
                line(ctx, 0.5, 0.0, 0.5, 1.0, shade(colour, 0.85), 0.6)
                for v in (0.15, 0.4, 0.65, 0.9):
                    rect(ctx, 0.46, v, 0.54, v + 0.05, shade(colour, 0.6))
        else:                                       # tshirt
            cloth(ctx, colour)
            if ctx.face == "west" and name == "UpperTorso":
                line(ctx, 0.3, 0.0, 0.7, 0.0, shade(colour, 0.8), 0.7)     # the neckline
        if name == "LowerTorso" and side not in ("up", "down"):
            if kind in ("tshirt", "jacket", "sweater", "hoodie", "cardigan"):
                rect(ctx, 0.0, 0.84, 1.0, 1.0, shade(colour if kind != "jacket" else accent, 0.8))  # the hem
            if kind in ("suit", "blouse", "coat"):
                rect(ctx, 0.0, 0.84, 1.0, 1.0, (46, 36, 30))                 # a belt
                if ctx.face == "west":
                    rect(ctx, 0.42, 0.84, 0.58, 1.0, (160, 140, 90))
    elif name in ("UpperArmL", "UpperArmR"):
        if kind in ("tshirt", "overalls"):
            paint_skin(ctx, skin, weathered)
            c = colour if kind == "tshirt" else accent
            if side != "down":
                rect(ctx, 0.0, 0.0, 1.0, 0.5, c)
                rect(ctx, 0.0, 0.46, 1.0, 0.5, shade(c, 0.8))
            else:
                fill(ctx, skin, 0.03)
        elif kind in ("jacket", "suit", "coat", "cardigan"):
            fill(ctx, shade(colour, 0.9), 0.03)      # under the sleeve box
        elif kind == "sweater":
            knit(ctx, colour)
        else:
            cloth(ctx, colour)
    elif name in ("LowerArmL", "LowerArmR"):
        # A sleeve to the wrist (or to the elbow), then the hand
        if side == "down":
            paint_skin(ctx, skin, weathered)
            return
        paint_skin(ctx, skin, weathered)
        if long_sleeve:
            c = colour
            if kind == "blouse":
                rect(ctx, 0.0, 0.0, 1.0, 0.45, c)                              # rolled to the elbow
                rect(ctx, 0.0, 0.38, 1.0, 0.45, shade(c, 0.85))
            else:
                if kind == "sweater":
                    px = ctx.img.load()
                    rect(ctx, 0.0, 0.0, 1.0, 0.72, c)
                    hlines(ctx, shade(c, 0.9), 2, start=1, alpha=0.5)
                else:
                    rect(ctx, 0.0, 0.0, 1.0, 0.72, c)
                rect(ctx, 0.0, 0.64, 1.0, 0.72, shade(c, 0.8))                 # the cuff
                if kind == "suit":
                    rect(ctx, 0.0, 0.64, 1.0, 0.72, (226, 224, 216))           # a shirt cuff showing
        if ctx.face == "west":
            line(ctx, 0.2, 0.86, 0.8, 0.86, shade(skin, 0.85), 0.5)            # knuckles


def paint_bottom(ctx, look, name, side):
    kind, colour = look["bottom"]
    skin = SKINS[look["skin"]]
    weathered = look["skin"] == "weathered"
    shoe_kind, shoe = look["shoes"]
    if name in ("UpperFootL", "UpperFootR"):
        if kind == "skirt":
            paint_skin(ctx, skin, weathered)                                     # the skirt box covers the thigh
        elif kind == "shorts":
            paint_skin(ctx, skin, weathered)
            if side != "down":
                rect(ctx, 0.0, 0.0, 1.0, 0.62, colour)
                rect(ctx, 0.0, 0.56, 1.0, 0.62, shade(colour, 0.8))
        elif kind == "jeans":
            denim(ctx, colour, knees=False)
            seam(ctx, shade(colour, 1.15))
            if ctx.face == "east":
                rect(ctx, 0.15, 0.08, 0.55, 0.4, shade(colour, 0.92))          # a back pocket
            if ctx.face == "west":
                blotch(ctx, mix(colour, (200, 200, 200), 0.3), 1, 2.5, 3.5, 0.45)
        else:
            cloth(ctx, colour, 0.02)
            if ctx.face in ("west", "east"):
                line(ctx, 0.5, 0.0, 0.5, 1.0, shade(colour, 1.1), 0.4)         # the crease
    elif name in ("LowerFootL", "LowerFootR"):
        if side == "down":
            fill(ctx, shade(shoe, 0.7), 0.04)
            return
        if kind in ("skirt", "shorts"):
            paint_skin(ctx, skin, weathered)
            if kind == "shorts" and shoe_kind == "sneakers":
                rect(ctx, 0.0, 0.66, 1.0, 0.78, (230, 230, 226))                # socks
        elif kind == "jeans":
            denim(ctx, colour, knees=True)
            seam(ctx, shade(colour, 1.15))
            rect(ctx, 0.0, 0.0, 1.0, 0.1, shade(colour, 0.88))
        else:
            cloth(ctx, colour, 0.02)
            if ctx.face in ("west", "east"):
                line(ctx, 0.5, 0.0, 0.5, 1.0, shade(colour, 1.1), 0.4)
        top = {"boots": 0.6, "sneakers": 0.8, "dress": 0.84}[shoe_kind]
        rect(ctx, 0.0, top, 1.0, 1.0, shoe)
        if shoe_kind == "boots":
            rect(ctx, 0.0, top, 1.0, top + 0.05, shade(shoe, 0.7))             # the boot's top edge
            rect(ctx, 0.0, 0.92, 1.0, 1.0, shade(shoe, 0.6))                   # the sole
            if ctx.face == "west":
                for v in (0.68, 0.76, 0.84):
                    rect(ctx, 0.3, v, 0.7, v + 0.03, shade(shoe, 0.5))        # laces
        elif shoe_kind == "sneakers":
            rect(ctx, 0.0, 0.92, 1.0, 1.0, mix(shoe, (120, 120, 120), 0.5))
            if ctx.face == "west":
                rect(ctx, 0.35, top + 0.02, 0.65, 0.9, shade(shoe, 0.85))
        else:
            rect(ctx, 0.0, 0.94, 1.0, 1.0, shade(shoe, 0.6))


def paint_attachment(ctx, look, name, side):
    """An attachment box: painted if the look wears it, else left transparent. Returns whether it was painted."""
    style, hair_colour = look["hair"]
    hair = HAIR_COLOURS[hair_colour]
    kind, colour, accent = look["top"]
    extras = look["extras"]
    if name.startswith("Hair"):
        if name not in HAIR_STYLES[style] or ("beanie" in extras and name in ("HairTop", "HairPuff", "HairFringe")) \
                or ("cap" in extras and name in ("HairTop", "HairPuff")):
            return False
        k = 1.1 if side == "up" else 0.85 if side in ("down", "east") else 1.0
        if ctx.baked and side != "down" and style != "curly":
            # B17: strands of their own tone, a lit band near the crown, partings
            rig.strands(ctx, shade(hair, k), shade(hair, 1.35), sheen=0.3, spread=0.35, parting=0.1,
                        along="u" if side == "up" else "v", sheen_at=0.2)
        else:
            fill(ctx, shade(hair, k), 0.12, face_shade=False)
        if side != "down" and not (ctx.baked and style != "curly"):
            vlines(ctx, shade(hair, 1.25), 2, start=0, alpha=0.4, jitter=1)      # strands
            vlines(ctx, shade(hair, 0.75), 3, start=1, alpha=0.4, jitter=1)
        if style == "curly" and side != "down":
            speckle(ctx, shade(hair, 1.3), 0.12, 2)
            speckle(ctx, shade(hair, 0.7), 0.1, 2)
        if name in ("HairLong", "HairPony", "HairBobL", "HairBobR") and side in ("north", "south", "east", "west"):
            ragged(ctx, 3)
        return True
    if name == "Collar":
        if kind in ("jacket", "suit", "coat", "blouse", "cardigan", "hoodie"):
            c = {"jacket": colour, "suit": colour, "coat": colour, "blouse": colour, "cardigan": colour, "hoodie": colour}[kind]
            if kind == "blouse":
                cloth(ctx, colour, 0.02)
            elif kind == "hoodie":
                cloth(ctx, shade(colour, 0.85))
            else:
                cloth(ctx, shade(c, 0.9))
            if side == "west":
                clear_rect(ctx, 0.3, 0.0, 0.7, 1.0)                                  # open at the throat
            return True
        return False
    if name == "Jacket":
        if kind in ("jacket", "suit", "coat", "cardigan"):
            if kind == "cardigan":
                knit(ctx, colour)
            else:
                cloth(ctx, colour)
            if side == "west":
                # Open down the front, the lapels wider at the top
                clear_rect(ctx, 0.4, 0.0, 0.6, 1.0)
                clear_rect(ctx, 0.3, 0.0, 0.7, 0.3)
                line(ctx, 0.3, 0.3, 0.4, 0.4, shade(colour, 0.75), 0.6)
                line(ctx, 0.7, 0.3, 0.6, 0.4, shade(colour, 0.75), 0.6)
                if kind in ("jacket",):
                    rect(ctx, 0.08, 0.5, 0.3, 0.75, shade(colour, 0.9))           # pockets
                    rect(ctx, 0.7, 0.5, 0.92, 0.75, shade(colour, 0.9))
                if kind in ("suit", "coat"):
                    rect(ctx, 0.62, 0.6, 0.68, 0.66, (40, 36, 30))                # a button
            if side in ("north", "south") and kind == "jacket":
                line(ctx, 0.0, 0.1, 1.0, 0.1, shade(colour, 0.8), 0.5)
            if side == "east":
                line(ctx, 0.5, 0.0, 0.5, 1.0, shade(colour, 0.9), 0.4)              # the back seam
            if side == "down":
                clear_rect(ctx, 0.0, 0.0, 1.0, 1.0)
            return side != "down"
        return False
    if name in ("SleeveL", "SleeveR"):
        if kind in ("jacket", "suit", "coat", "cardigan"):
            (knit if kind == "cardigan" else cloth)(ctx, colour)
            if side not in ("up", "down"):
                line(ctx, 0.0, 0.08, 1.0, 0.08, shade(colour, 0.8), 0.5)         # the shoulder seam
            if side == "down":
                clear_rect(ctx, 0.0, 0.0, 1.0, 1.0)
            return side != "down"
        return False
    if name == "CoatSkirt":
        if kind == "coat":
            cloth(ctx, colour)
            if side == "west":
                clear_rect(ctx, 0.42, 0.0, 0.58, 1.0)
                rect(ctx, 0.62, 0.15, 0.68, 0.21, (40, 36, 30))
            if side in ("north", "south"):
                rect(ctx, 0.2, 0.2, 0.7, 0.5, shade(colour, 0.9))                  # a pocket flap
            if side in ("up", "down"):
                clear_rect(ctx, 0.0, 0.0, 1.0, 1.0)
                return False
            return True
        return False
    if name == "Skirt":
        if look["bottom"][0] == "skirt":
            cloth(ctx, look["bottom"][1], 0.02)
            if side in ("north", "south", "east", "west"):
                vlines(ctx, shade(look["bottom"][1], 0.9), 4, start=2, alpha=0.3)   # pleats
            if side in ("up", "down"):
                clear_rect(ctx, 0.0, 0.0, 1.0, 1.0)
                return False
            return True
        return False
    if name == "Backpack":
        if "backpack" in extras:
            cloth(ctx, (74, 84, 72))
            if side == "east":
                rect(ctx, 0.15, 0.1, 0.85, 0.45, shade((74, 84, 72), 0.85))      # the front pocket
                rect(ctx, 0.3, 0.0, 0.7, 0.08, (40, 40, 38))
            return True
        return False
    if name == "Bag":
        if "bag" in extras:
            cloth(ctx, (110, 78, 50), 0.03)
            if side == "south":
                rect(ctx, 0.0, 0.0, 1.0, 0.4, shade((110, 78, 50), 0.85))         # the flap
                rect(ctx, 0.42, 0.3, 0.58, 0.46, (160, 140, 90))
            return True
        return False
    if name == "Glasses":
        if "glasses" in extras:
            fill(ctx, (34, 30, 30), 0.0, face_shade=False)
            if side == "west":
                clear_rect(ctx, 0.08, 0.15, 0.44, 0.85)                            # lenses, with nothing behind them
                clear_rect(ctx, 0.56, 0.15, 0.92, 0.85)
            return True
        return False
    if name in ("GlassesArmL", "GlassesArmR"):
        if "glasses" in extras:
            fill(ctx, (34, 30, 30), 0.0, face_shade=False)
            return True
        return False
    if name == "Beanie":
        if "beanie" in extras:
            knit(ctx, (84, 70, 94))
            if side not in ("up", "down"):
                rect(ctx, 0.0, 0.7, 1.0, 1.0, shade((84, 70, 94), 0.85))         # the folded brim
            return True
        return False
    if name in ("Cap", "CapBrim"):
        if "cap" in extras:
            cloth(ctx, (62, 60, 66), 0.03)
            if name == "Cap" and side == "west":
                rect(ctx, 0.35, 0.3, 0.65, 0.75, (200, 196, 186))                   # a blank patch
            return True
        return False
    return False


def paint_look(code, look):
    shape = json.load(open(vanilla("game/shapes/entity/humanoid/seraph-faceless.json"), encoding="utf-8-sig"))
    uvs, height = attachment_uvs()
    img = Image.new("RGBA", (32 * SCALE, height * SCALE), (0, 0, 0, 0))
    rng = random.Random(code)
    skin = SKINS[look["skin"]]
    weathered = look["skin"] == "weathered"
    for e in walk(shape["elements"]):
        name = e["name"]
        if name in TOOLS:
            continue
        for side, face in e.get("faces", {}).items():
            if face.get("texture") != "#seraph" or "uv" not in face:
                continue
            ctx = _ctx(img, name, side, face["uv"], rng)
            if name == "Head":
                if side == "west":
                    if look.get("evolved"):
                        paint_evolved_face(ctx, skin)
                    else:
                        paint_face(ctx, skin, weathered)
                else:
                    paint_skin(ctx, skin, weathered)
                    if look["hair"][0] == "buzz" and side in ("up", "east", "north", "south"):
                        fill(ctx, mix(skin, HAIR_COLOURS[look["hair"][1]], 0.7), 0.1)   # hair cropped to the skin
                    if look["hair"][0] == "bald" and side == "up":
                        fill(ctx, shade(skin, 1.06), 0.02)
            elif name == "Neck":
                paint_skin(ctx, skin, weathered)
                if side == "west":
                    line(ctx, 0.5, 0.3, 0.5, 1.0, shade(skin, 0.9), 0.3)
            elif name in ("UpperTorso", "LowerTorso", "UpperArmL", "UpperArmR", "LowerArmL", "LowerArmR"):
                paint_top(ctx, look, name, side)
            elif name in ("UpperFootL", "UpperFootR", "LowerFootL", "LowerFootR"):
                paint_bottom(ctx, look, name, side)
    for name, faces in uvs.items():
        for side, uv in faces.items():
            ctx = _ctx(img, name, side, uv, rng)
            paint_attachment(ctx, look, name, side)
    if FACELING_LIGHT is not None:
        shape_name = "faceling-child.json" if code.startswith("child-") else "faceling.json"
        with open(os.path.join(ASSETS, "shapes", "entity", shape_name), encoding="utf-8-sig") as f:
            shape = json.load(f)
        rig.bake_shape(shape, img, SCALE, skip=TOOLS | {"Glasses", "GlassesArmL", "GlassesArmR"}, **FACELING_LIGHT)
    save_texture(img, f"faceling-{code}")


def faceling_textures():
    for code, look in list(LOOKS.items()) + list(CHILD_LOOKS.items()):
        paint_look(code, look)


# ---------------------------------------------------------------- Entity types

# How long a knife takes over a body, on both sides. The knife stops when the client's copy of "harvestable" says it
# is done, and the server only generates the drops if that was long enough for its own copy, so a client copy shorter
# than the server's (2 s against the default 5 s, as it was up to 0.513.0) left every body empty.
HARVEST_SECONDS = 2


def sync_harvestable(entity):
    """Drops the client's "harvestable" from a creature whose server side has none: the knife would offer to harvest
    the body and then open it empty. The other two mismatches (the server has it and the client does not, or the two
    durations differ) are errors rather than something to patch: they would leave the same empty body."""
    server = entity.get("server", {}).get("behaviors", [])
    client = entity.get("client", {})
    s = next((b for b in server if b["code"] == "harvestable"), None)
    if s is None:
        client["behaviors"] = [b for b in client.get("behaviors", []) if b["code"] != "harvestable"]
        return entity
    c = next((b for b in client.get("behaviors", []) if b["code"] == "harvestable"), None)
    if c is None or c.get("duration") != s.get("duration"):
        raise ValueError(f"{entity.get('code')}: client and server 'harvestable' disagree ({c} against {s})")
    return entity


def anim(code, animation=None, speed=1.0, **extra):
    a = {"code": code, "animation": animation or code, "animationSpeed": speed, "blendMode": "Average"}
    a.update(extra)
    return a


def common_client(shape, texture, animations, size=1.0, step=1.1251, movable=True):
    client = {
        "renderer": "Shape",
        "shape": {"base": shape},
        "texture": texture,
        "size": size,
        "behaviors": [
            {"code": "repulseagents", "movable": movable},
            {"code": "controlledphysics", "stepHeight": step},
            {"code": "floatupwhenstuck", "onlyWhenDead": True},
            {"code": "interpolateposition"},
            # (The knife asks the client's copy whether a body can be harvested and how long it takes; the server's
            # copy, with the drops, must say the same: see sync_harvestable)
            {"code": "harvestable", "duration": HARVEST_SECONDS},
        ],
        "animations": animations,
    }
    return client


def server(health, tasks, drops=None, menace=None, step=1.1251, decay="game:carcass-medium", extra=(), movable=True):
    return server_(health, tasks, drops, menace, step, decay, extra, movable)


def server_(health, tasks, drops=None, menace=None, step=1.1251, decay="game:carcass-medium", extra=(), movable=True):
    behaviors = [
        {"code": "repulseagents", "movable": movable},
        {"code": "controlledphysics", "stepHeight": step},
    ]
    if health:
        behaviors.append({"code": "health", "currenthealth": health, "maxhealth": health})
        # (decay=None: the body leaves nothing behind when it goes, as the game's own mechanical things)
        behaviors.append(dict({"code": "deaddecay", "hoursToDecay": 24}, **({"decayedBlock": decay} if decay else {})))
    behaviors.append({"code": "floatupwhenstuck", "onlyWhenDead": True})
    if drops:
        behaviors.append({"code": "harvestable", "duration": HARVEST_SECONDS, "drops": drops})
    behaviors.extend(extra)
    behaviors.append(dict({"code": "backrooms-menace"}, **(menace or {})))
    behaviors.append({"code": "taskai", "aiCreatureType": "LandCreature", "aitasks": tasks})
    behaviors.append({"code": "entitystatetags"})
    return {"behaviors": behaviors}


def drop(code, avg, var=0):
    return {"type": "item", "code": code, "quantity": {"avg": avg, "var": var}}


def menace_task(**config):
    task = {"code": "backrooms-menace", "priority": 1.6, "priorityForCancel": 1.6, "mincooldown": 0, "maxcooldown": 0}
    task.update(config)
    return task


def model_anims(*extra, walk=1.0, run=1.0, attack=1.0):
    """The animations every one of our modelled entities has (codes as in gen_models.py), and any others."""
    return [
        anim("hurt", "hurt", 1.0, weight=10, blendMode="AddAverage"),
        anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
        anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage", easeOutSpeed=4),
        anim("walk", "walk", walk),
        anim("run", "run", run),
        anim("attack", "attack", attack, weight=10),
    ] + list(extra)


WANDER = {"code": "wander", "priority": 1.0, "priorityForCancel": 1.35, "movespeed": 0.008, "animation": "walk", "animationSpeed": 1.0,
          "maxDistanceToSpawn": 24}
LOOKAROUND = {"code": "lookaround", "priority": 0.5}
# AiTaskAmble: somewhere it can walk to (a search over the floor), never at a wall, turns to look down the hall and stands a while
AMBLE = {"code": "backrooms-amble", "priority": 1.0, "priorityForCancel": 1.35, "movespeed": 0.01, "walkAnimation": "walk",
         "maxDistanceToSpawn": 24, "minWalk": 5, "maxWalk": 16, "mincooldown": 3000, "maxcooldown": 12000}


def idle(animation, priority=1.2, min_ms=4000, max_ms=12000, cool_min=8000, cool_max=30000):
    return {"code": "idle", "priority": priority, "priorityForCancel": 1.35, "animation": animation, "minduration": min_ms, "maxduration": max_ms,
            "mincooldown": cool_min, "maxcooldown": cool_max}


def hound():
    animations = model_anims(anim("sniff", "sniff"), anim("howl", "howl"), anim("growl", "growl"), anim("scratch", "scratch"))
    tasks = [
        # (Speeds compare with a player's 0.025 walking and 0.05 sprinting; the level's danger adds up to 30 %. Like a vanilla
        # wolf in Level 1 (8 damage at tier 2, 15 health) and a bear (10 to 12) from Level 3; see docs/design/entity-difficulty.md.
        # Round 2 (isolation.md 4.5): it outruns a sprint everywhere (0.062 is 1.24 x, 1.5 x at the deepest danger) and light no
        # longer slows it, so a straight run does not work; what works is staying out of sight, the stare, a calm walk away
        # facing it, and a shut door)
        menace_task(walkSpeed=0.022, runSpeed=0.062, stalkMin=9, stalkMax=15, glimpseFleeDistance=16,
                    damage=7.2, damageTier=2, damageType="SlashingAttack", knockback=0.35, attackRange=1.0,
                    attackDurationMs=1000, damageAtMs=600, attackCooldownMs=1100, walkAnimation="walk", runAnimation="run",
                    attackAnimation="attack", fearsFire=True, retreatBelow=0.35, staredDown=True,
                    stalkSound="game:creature/wolf/growl*", huntSound="game:creature/wolf/howl*", attackSound="game:creature/wolf/attack*", soundRange=40,
                    # What it perceives (docs/design/entity-ai-overhaul/README.md section 6.1): hostile on sight, hears running
                    senses=dict(sightLit=40, sightDim=18, sightDark=8, sightCone=70, carriedLight=1.5, hearing=32, fearSense=12, memorySeconds=10, trackSeconds=12, trackError=10),
                    # Encounter v2 (README sections 5 and 6.1): a glimpse that sees turns to a stalk, a growl before the charge, barks
                    # while hunting in Level 3, investigates noise, searches a lost target, retaliation bounded
                    # It does not hunt on sight (AiTaskMenace.ShouldTurnToHunt, chargesWhenBacked): it closes at a walk, growling, and
                    # charges when the target runs, turns their back for 2 s within 16 blocks, comes within 5, or its nerve breaks under a
                    # stare (4 to 8 s: "won't work for long"); losing them it searches and then leaves (leavesAfterSearch)
                    chargesWhenBacked=True, backTurnedRange=16, backTurnedSeconds=2, backTurnedCone=70, chargeCloseRange=5, leavesAfterSearch=True,
                    # A Hound sent by a Flickering hunts until the lights return (AiTaskMenace.Relentless)
                    huntsUntilSet=True,
                    glimpseTurnsToStalk=True, growlBeforeCharge=True, growlMs=900, barks=True, huntBarkSeconds=2, huntBarkLevels=[3],
                    investigateSeconds=8, searchSeconds=14, retaliateSeconds=60, lookAnimation="sniff"),
        idle("sniff", 1.2, 5000, 5000, 8000, 25000),
        idle("scratch", 1.15, 2500, 2500, 30000, 90000),
        WANDER,
        LOOKAROUND,
    ]
    return {
        "code": "hound",
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "predator", "habitat-land"],
        "weight": 70,
        # The model is 23 px (1.45 blocks) at the shoulder and 33 long; the head hangs at about 1.1
        "hitboxSize": {"x": 1.1, "y": 1.3},
        "deadHitboxSize": {"x": 1.0, "y": 0.6},
        "eyeHeight": 1.1,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-hound"},
        # (Which look, the director decides: mostly the common one, a quarter starved, now and then an old one)
        "client": common_client("backrooms:entity/hound", {"base": "backrooms:entity/hound",
                                                           "alternates": [{"base": "backrooms:entity/hound-starved"}, {"base": "backrooms:entity/hound-elder"}]}, animations),
        "server": server(26, tasks, [drop("game:bushmeat-raw", 3, 1), drop("game:hide-raw-medium", 1), drop("game:bone", 1)], menace={"maxEncounterSeconds": 300}),
        "sounds": {"hurt": "game:creature/wolf/hurt", "death": "game:creature/wolf/hurt"},
    }


def smiler():
    tasks = [
        menace_task(walkSpeed=0.016, runSpeed=0.05, stalkMin=10, stalkMax=18, glimpseFleeDistance=14,
                    damage=6, damageTier=3, damageType="PiercingAttack", knockback=0.3, attackRange=0.9,
                    attackDurationMs=700, damageAtMs=300, attackCooldownMs=1800, walkAnimation="walk", runAnimation="run", attackAnimation="attack",
                    lightBound=True, stalkSound="backrooms:entity/smiler", huntSound="backrooms:entity/smiler", soundRange=20,
                    # What it perceives (README section 6.2): sees far in the light, comes for the unsteady and for light
                    senses=dict(sightLit=48, sightDim=16, sightDark=6, sightCone=80, hearing=24, fearSense=16, memorySeconds=10, trackSeconds=20, trackError=12),
                    drawnToLight=True, investigateSeconds=6, searchSeconds=8, retaliateSeconds=60),
    ]
    return {
        "code": "smiler",
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "habitat-land"],
        "weight": 60,
        "hitboxSize": {"x": 0.6, "y": 1.9},
        "eyeHeight": 1.7,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-smiler"},
        # (It glides more than it walks: running is the same gait, faster)
        "client": common_client("backrooms:entity/smiler", {"base": "backrooms:entity/smiler"},
                                [anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage"), anim("walk", "walk", 1.0),
                                 anim("run", "walk", 2.0), anim("attack", "attack", 1.0, weight=10),
                                 # (Struck, it flinches back into the dark: the hit comes before it withdraws)
                                 anim("hurt", "hurt", 1.5, weight=10, blendMode="AddAverage")]),
        # No health: it cannot be killed (struck, it withdraws)
        "server": server(0, tasks, menace={"immortal": True, "glimpseSeconds": 25, "stalkSeconds": 120, "maxEncounterSeconds": 300}),
        "sounds": {},
    }


FACELING_ANIMS = [
    anim("hurt", "hurt", 1.5, weight=10, blendMode="AddAverage"),
    anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
    anim("idle", "idle1", triggeredBy={"defaultAnim": True}, blendMode="AddAverage"),
    anim("walk", "walk", 1.0),
    anim("run", "sprint", 1.0),
    anim("attack", "hit", 1.2, weight=10),
    anim("sit", "sitflooridle", 1.0),
    anim("lookaround", "lookaround", 1.0),
    anim("headscratch", "headscratch", 1.0),
    # Human gestures, done a little too long or too often: the lore's Facelings imitate what people do
    anim("wave", "wave", 0.8),
    anim("nod", "nod", 0.9),
    anim("shrug", "shrug", 1.0),
    anim("stretch", "stretch", 0.9),
    anim("yawn", "yawn", 1.0),
    anim("facewipe", "facepalm", 0.7),      # a hand rubbed over where a face should be
    anim("point", "point", 0.8),           # showing the way, when a player greets one (held a beat)
    anim("tantrum", "rage", 1.3),          # a child's, when frightened or hurt
]


def faceling(child=False):
    code = "faceling-child" if child else "faceling"
    looks = CHILD_LOOKS if child else LOOKS
    first = next(iter(looks))
    tasks = [
        menace_task(walkSpeed=0.012 if not child else 0.016, runSpeed=0.03 if not child else 0.04, stalkMin=6, stalkMax=10,
                    damage=2 if not child else 0.8, damageTier=0, damageType="BluntAttack",
                    knockback=0.4 if not child else 0.2, attackRange=0.8, attackDurationMs=800, damageAtMs=400, attackCooldownMs=1500,
                    walkAnimation="walk", runAnimation="run", attackAnimation="attack" if not child else "tantrum", retaliates=True),
        # They leave when the Hounds come, before you see the Hounds
        {"code": "fleeentity", "entityCodes": ["hound"], "priority": 1.55, "movespeed": 0.03, "seekingRange": 16, "animation": "run",
         "fleeingDistance": 24, "fleeDurationMs": 9000},
        # Greeted (right-clicked): waves, turns and points toward the nearest gate, nods; above everything but fleeing
        # and being hurt, so nothing turns it away or walks it off meanwhile
        {"code": "backrooms-greet", "priority": 1.5, "priorityForCancel": 1.5, "mincooldown": 0, "maxcooldown": 0},
    ]
    if child:
        # Calmed with food (right-click mid-tantrum): follows that player at a few blocks for a minute
        tasks.append({"code": "backrooms-companion", "priority": 1.45, "priorityForCancel": 1.45, "mincooldown": 0, "maxcooldown": 0,
                      "walkSpeed": 0.016, "runSpeed": 0.04, "minDistance": 2, "maxDistance": 4})
        # Curious: comes to look at a player, keeps a few steps off, and runs if they come at it
        tasks.append({"code": "backrooms-curious", "priority": 1.3, "priorityForCancel": 1.35, "walkSpeed": 0.016, "runSpeed": 0.04,
                      "seekingRange": 14, "keepAway": 3.5, "fleeDistance": 2.2, "mincooldown": 8000, "maxcooldown": 30000})
        tasks += [idle("sit", 1.25, 8000, 20000, 20000, 60000), idle("lookaround", 1.2, 3000, 5000, 6000, 20000), idle("wave", 1.16, 3500, 3500, 30000, 90000)]
    else:
        # Disturbed (a block broken, a fall, a blow nearby): turns, throws its arms about, shoves once, calms
        tasks.append({"code": "backrooms-outburst", "priority": 1.52, "priorityForCancel": 1.52, "mincooldown": 0, "maxcooldown": 0,
                      "range": 6, "cooldownSeconds": 30, "damage": 1, "knockback": 0.35, "gesture": "stretch", "walkSpeed": 0.02})
        tasks += [
            idle("sit", 1.25, 20000, 60000, 30000, 120000),
            idle("lookaround", 1.2, 3000, 5000, 6000, 20000),
            idle("headscratch", 1.15, 2000, 3000, 30000, 90000),
            idle("wave", 1.16, 3500, 3500, 40000, 120000),
            idle("nod", 1.16, 4000, 4000, 30000, 90000),
            idle("stretch", 1.14, 2500, 2500, 60000, 180000),
            idle("facewipe", 1.17, 2800, 2800, 90000, 240000),
        ]
    # Walks somewhere it can reach along the halls (never at a wall), mostly on the way it was going, turns to look
    # down the most open way at the end and stands a while (in place of vanilla's wander and lookaround)
    tasks.append({"code": "backrooms-amble", "priority": 1.0, "priorityForCancel": 1.35, "movespeed": 0.01 if not child else 0.014,
                  "walkAnimation": "walk", "maxDistanceToSpawn": 24, "minWalk": 5 if not child else 4, "maxWalk": 16 if not child else 14,
                  "mincooldown": 3000 if not child else 2000, "maxcooldown": 12000 if not child else 8000})
    client = common_client(f"backrooms:entity/{code}",
                           {"base": f"backrooms:entity/faceling-{first}" if not child else f"backrooms:entity/faceling-{first}",
                            "alternates": [{"base": f"backrooms:entity/faceling-{c}"} for c in looks if c != first]},
                           FACELING_ANIMS, size=0.68 if child else 1.0, step=1.01)
    # The blank face follows a passing player (on the client, head only); greeted, it waves back and points the way;
    # hurt one, and the others nearby turn on you
    client["behaviors"].append({"code": "backrooms-faceling"})
    server = server_(10 if not child else 5, tasks, step=1.01, menace={"huntSeconds": 30 if not child else 15},
                     extra=[{"code": "backrooms-faceling"}])
    return {
        "code": code,
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": 70 if not child else 30,
        "hitboxSize": {"x": 0.6, "y": 1.85} if not child else {"x": 0.45, "y": 1.25},
        "deadHitboxSize": {"x": 0.75, "y": 0.5} if not child else {"x": 0.5, "y": 0.35},
        "eyeHeight": 1.7 if not child else 1.15,
        "attributes": {"killedByInfoText": f"backrooms:deadcreature-faceling"},
        "client": client,
        "server": server,
        "sounds": {"hurt": "game:player/hurt*", "death": "game:player/death*"},
    }

def tall_body(code, hitbox, eye, health, task, menace, drops, sounds, size=1.0, idle_anim="despair", idles=None, looks=(), extra_anims=(),
              walk=1.0, run=1.0, weight=90, amble=None):
    """A tall one of ours on its own model (Skin-Stealer, Duller, the Mangled, the Bacteria, the Wretches). The hitbox
    is kept to two blocks for the ones that must pass through doorways, though the model stands taller."""
    idles = idles or [idle(idle_anim, 1.15, 4000, 8000, 30000, 90000)]
    # (An amble, where given, goes to places it can reach along the halls in place of vanilla's straight-line wander and lookaround)
    wander = [dict(AMBLE, **amble)] if amble is not None else [dict(WANDER, movespeed=0.006), LOOKAROUND]
    tasks = [task] + idles + wander
    texture = {"base": f"backrooms:entity/{code}"}
    if looks:
        texture["alternates"] = [{"base": f"backrooms:entity/{code}-{look}"} for look in looks]
    animations = model_anims(*[anim(i["animation"], i["animation"]) for i in idles], *extra_anims,
                             walk=walk, run=run)
    return {
        "code": code,
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": weight,
        "canClimb": True,
        "hitboxSize": {"x": hitbox[0], "y": hitbox[1]},
        "deadHitboxSize": {"x": hitbox[0], "y": 0.6},
        "eyeHeight": eye,
        "attributes": {"killedByInfoText": f"backrooms:deadcreature-{code}"},
        "client": common_client(f"backrooms:entity/{code}", texture, animations, size),
        "server": server(health, tasks, drops, menace=menace),
        "sounds": sounds,
    }


def skinstealer():
    # It wears a person and has their hands: hunting someone shut in, out towards the edge of a level, it knocks on the
    # door and opens it (AiTaskMenace, opensDoors). A barred door it only knocks on; it fears fire.
    task = menace_task(walkSpeed=0.016, runSpeed=0.036, stalkMin=10, stalkMax=16, glimpseFleeDistance=12,
                       damage=10.6, damageTier=2, damageType="BluntAttack", knockback=0.5, attackRange=1.2,
                       attackDurationMs=1100, damageAtMs=650, attackCooldownMs=2000, attackAnimation="attack",
                       fearsFire=True, prefersHidden=True, retreatBelow=0.25, opensDoors=True,
                       voices=["backrooms:entity/cough", "game:player/hurt*", "backrooms:effect/whisper", "backrooms:entity/hello"],
                       voicesWhenSeen=0.35, stalkSound="backrooms:entity/stealer-breath*", huntSound="backrooms:entity/stealer-cry*",
                       attackSound="backrooms:entity/stealer-attack*", soundRange=32,
                       # What it perceives (README 6.1): patient, sees well in the light, hears a good way
                       senses=dict(sightLit=30, sightDim=14, sightDark=8, sightCone=80, hearing=24, memorySeconds=12, trackSeconds=15, trackError=10),
                       investigateSeconds=8, searchSeconds=10, retaliateSeconds=60,
                       # Harder (README 6.1): a kill feeds it for a day (fed, it is docile: the director's, and the behaviour's, to
                       # say), and a hit of 5 or more stuns it for a moment, once in a while: the opening
                       feedsOnKill=True, fedHours=24, stunDamage=5, stunSeconds=1.2, stunCooldownSeconds=8, stunAnimation="hurt",
                       # P7 round 2 (play-test). Fed, it keeps to itself but turns on anyone who comes within 5 blocks, a short hunt that
                       # ends (muttering again) once they are 12 off or have kept clear for 6 s. Hungry, it does not simply watch and go: a
                       # glimpse that has watched them follows (Approach band and out), and a stalk comes for them after about 8 s at the
                       # Threshold, 20 s in the Approach band (AiTaskMenace.EscalationDue)
                       fedGuardRange=5, fedGuardRelease=12, fedGuardSeconds=6, glimpseTurnsToStalk=True, escalateThreshold=8, escalateApproach=20)
    # The model stands 38.7 px; drawn at 0.92 it is 35.6 px (2.2 blocks), a head taller than a player, eyes at 2.05
    # (Health 34 to 51: 40 to 60 at Level 1, where the danger adds 17 %. Its second look, the fed one in its disguise, is
    # chosen by the director; the behaviour bleeds clear when struck, and a fed one says "hello?" now and then)
    return tall_body("skinstealer", (0.8, 1.95), 2.05, 55, task,
                     {"stalkSeconds": 180, "maxEncounterSeconds": 300, "bleedsClear": True,
                      "fedVoices": ["backrooms:entity/hello", "backrooms:entity/hello", "backrooms:entity/cough"]},
                     [drop("game:hide-raw-large", 1)], {"hurt": "game:creature/drifter-hurt", "death": "game:creature/drifter-death"},
                     size=0.92, idle_anim="skinadjust", looks=("fed",),
                     # (Fed, it walks slowly to somewhere real, stands and mutters; it used to take vanilla's straight-line wander)
                     amble=dict(movespeed=0.007, minWalk=4, maxWalk=12, mincooldown=6000, maxcooldown=22000))


def duller():
    task = menace_task(walkSpeed=0.018, runSpeed=0.054, stalkMin=3, stalkMax=8, glimpseFleeDistance=16,
                       damage=3, damageTier=1, damageType="BluntAttack", knockback=0.2, attackRange=0.8,
                       attackDurationMs=900, damageAtMs=400, attackCooldownMs=3000, attackAnimation="attack",
                       grabsThroughWalls=True, respectsAlmond=True, coward=True, prefersHidden=True, stealChance=0.25,
                       # What gives one away, from the other side of the wall: scraping, dragging, a knock
                       voices=["backrooms:entity/scratch", "backrooms:entity/drag", "backrooms:entity/knock"],
                       grabSound="backrooms:entity/grab", soundRange=20,
                       # What it perceives (README 6.1): the wall is its sense; its eyes are for seeing who faces it
                       senses=dict(special="wall", sightLit=20, sightDim=12, sightDark=6, hearing=16, memorySeconds=8, trackSeconds=0),
                       investigateSeconds=8, searchSeconds=10, retaliateSeconds=60,
                       # Faced, it flees at 1.3 times a sprint (a player sprints at 0.05); it can be hurt only from its grab until
                       # 1.5 s after it (the behaviour's hardToCatch)
                       fleeSpeed=0.065, catchWindowSeconds=1.5)
    # The model stands 39.5 px; drawn at 0.92 it is 36 px (2.3 blocks); the head is at about 2.1
    # (Health 15 to 20: 23 to 30 at Level 3)
    return tall_body("duller", (0.6, 1.95), 2.1, 20, task, {"stalkSeconds": 150, "maxEncounterSeconds": 300, "hardToCatch": True}, None,
                     {"hurt": "game:creature/drifter-hurt", "death": "game:creature/drifter-death"}, size=0.92)


def deathrat():
    animations = model_anims(anim("sniff", "sniff"), anim("scamper", "scamper"), anim("groom", "groom"), anim("rearup", "rearup"), anim("eat", "eat"))
    tasks = [
        menace_task(walkSpeed=0.022, runSpeed=0.048, stalkMin=6, stalkMax=11, glimpseFleeDistance=10,
                    damage=1.2, damageTier=0, damageType="PiercingAttack", knockback=0.1, attackRange=0.7,
                    attackDurationMs=600, damageAtMs=300, attackCooldownMs=900, attackAnimation="attack",
                    avoidsLight=True, fearsFire=True, retreatBelow=0.5,
                    stalkSound="backrooms:entity/squeak", attackSound="backrooms:entity/squeak", soundRange=20,
                    # What it perceives (README 6.1): small eyes that see wide, good ears, a short memory
                    senses=dict(sightLit=14, sightDim=10, sightDark=6, sightCone=120, hearing=24, memorySeconds=4, trackSeconds=0),
                    investigateSeconds=8, searchSeconds=10, retaliateSeconds=60),
        # Scavenger first (README 6.1): rats put down in the heart of a level are Ambient; they go to food on the floor and
        # eat it, scatter from a walking person (6 blocks; 3 if they creep or stand) and from a carried light (8), and
        # bite only when cornered or when a pack of 4 is round someone below half health
        {"code": "backrooms-scavenge", "priority": 1.4, "priorityForCancel": 1.4, "mincooldown": 0, "maxcooldown": 0,
         "walkSpeed": 0.022, "runSpeed": 0.048, "foodRange": 16, "scatterRange": 6, "sneakScatterRange": 3, "lightScatterRange": 8,
         "torchLight": 10, "scatterDistance": 8, "scatterSeconds": 5, "eatSeconds": 4, "carcassSeconds": 10,
         "corneredRange": 2, "corneredOpen": 3, "packBites": 4, "packBiteHealth": 0.5, "packRange": 12,
         "eatAnimation": "eat", "eatSound": "game:creature/animal-eat-small"},
        idle("sniff", 1.2, 2000, 4000, 4000, 12000),
        idle("groom", 1.18, 3000, 3000, 20000, 60000),
        idle("rearup", 1.17, 2000, 2000, 20000, 70000),
        idle("eat", 1.16, 4000, 8000, 30000, 90000),
        dict(WANDER, movespeed=0.012, animation="scamper"),
        LOOKAROUND,
        # Moth jelly set down within 24 blocks draws it (src/Entities/MothJelly.cs); outranks the menace task
        {"code": "backrooms-bait", "priority": 2.0, "priorityForCancel": 2.0, "mincooldown": 0, "maxcooldown": 0, "speed": 0.04},
    ]
    return {
        "code": "deathrat",
        "class": "EntityDeathRat",
        "tags": ["backrooms-entity", "animal", "huntable", "habitat-land"],
        "weight": 12,
        # 8 px at the shoulder, horn tips at 10, 32 px nose to tail
        "hitboxSize": {"x": 0.8, "y": 0.6},
        "deadHitboxSize": {"x": 0.8, "y": 0.35},
        "eyeHeight": 0.38,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-deathrat"},
        # (Which look, the director decides: hairless in Level 2's heat)
        "client": common_client("backrooms:entity/deathrat", {"base": "backrooms:entity/deathrat", "alternates": [{"base": "backrooms:entity/deathrat-hairless"}]}, animations),
        "server": server(5, tasks, [drop("game:bushmeat-raw", 1.5, 0.5), drop("game:hide-raw-small", 0.5, 0.5), drop("game:bone", 0.5, 0.5)],
                         # (Level 2's hairless look, texture 1, never bites)
                         menace={"maxEncounterSeconds": 300, "harmlessLooks": [1]}, decay="game:carcass-small"),
        "sounds": {"hurt": "game:creature/hare-hurt", "death": "game:creature/hare-hurt"},
    }


# Both moths: light-led sight (a flame is seen from far, the dark not at all) and a hearing of 10 for the alarm
MOTH_SENSES = dict(sightLit=24, sightDim=8, sightDark=0, hearing=10)


def deathmoth():
    animations = [anim("fly", "fly", 1.0), anim("glide", "glide", 1.0), anim("rest", "rest", 1.0), anim("feed", "feed", 1.0),
                  anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]})]
    female_animations = animations + [anim("bite", "bite", 1.0, weight=10, blendMode="AddAverage"), anim("threat", "threat", 1.0, weight=5)]
    tasks_by = {
        "*-female": [{"code": "backrooms-moth", "priority": 1.5, "speed": 0.04, "damage": 1.5, "bites": True, "orbitRadius": 1.3,
                      "biteSound": "game:creature/beesting", "senses": MOTH_SENSES}],
        # (A male scavenges within scavengeRange of food, keeps scavengeAvoid from a player, and in aggressiveLevel
        # bites like a female: the lore has Level 3's males aggressive too)
        "*": [{"code": "backrooms-moth", "priority": 1.5, "speed": 0.03, "damage": 1.5, "bites": False, "orbitRadius": 1.8,
               "biteSound": "game:creature/beesting", "aggressiveLevel": 3, "scavengeRange": 12, "scavengeAvoid": 5, "senses": MOTH_SENSES}],
    }
    entity = {
        "code": "deathmoth",
        "class": "EntityDeathmoth",
        "variantgroups": [{"code": "gender", "states": ["male", "female"]}],
        "tags": ["backrooms-entity", "animal", "habitat-air"],
        "habitat": "Air",
        "weight": 0.2,
        "hitboxSize": {"x": 0.6, "y": 0.4},
        "eyeHeight": 0.2,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-deathmoth"},
        "client": {
            "renderer": "Shape",
            "shapeByType": {"*-male": {"base": "backrooms:entity/deathmoth-male"}, "*-female": {"base": "backrooms:entity/deathmoth-female"}},
            "textureByType": {"*-male": {"base": "backrooms:entity/deathmoth-male"}, "*-female": {"base": "backrooms:entity/deathmoth-female"}},
            "size": 1.0,
            "behaviors": [{"code": "controlledphysics", "stepHeight": 1.0001}, {"code": "interpolateposition"}],
            "animationsByType": {"*-female": female_animations, "*": animations},
        },
        "server": {
            "attributes": {"pathfinder": {"minTurnAnglePerSec": 900, "maxTurnAnglePerSec": 1800}},
            "behaviors": [
                {"code": "controlledphysics", "stepHeight": 1.0001},
                {"code": "health", "currenthealthByType": {"*-female": 3, "*": 2}, "maxhealthByType": {"*-female": 3, "*": 2}},
                {"code": "backrooms-menace", "glimpseSeconds": 60, "stalkSeconds": 150},
                {"code": "taskai", "aitasksByType": tasks_by},
                {"code": "entitystatetags"},
            ],
        },
        "sounds": {},
    }
    # A female can be harvested for a quill (0 to 1); a male leaves nothing, so only the female has the behaviour, on
    # both sides with the same duration (see sync_harvestable). Her body goes in a day, as the game's creatures' do
    import copy
    female_server = copy.deepcopy(entity["server"])
    behaviors = female_server["behaviors"]
    behaviors.insert(3, {"code": "deaddecay", "hoursToDecay": 24})
    behaviors.insert(4, {"code": "harvestable", "duration": HARVEST_SECONDS, "drops": [drop("backrooms:mothquill", 0.5, 0.5)]})
    female_client = copy.deepcopy(entity["client"])
    female_client["behaviors"].append({"code": "harvestable", "duration": HARVEST_SECONDS})
    entity["serverByType"] = {"*-female": female_server, "*": entity.pop("server")}
    entity["clientByType"] = {"*-female": female_client, "*": entity.pop("client")}
    return entity


# ---------------------------------------------------------------- The optional three

def clump():
    # Brittle bones (README 6.1: effective health 27 to 18 and grab 6.3 to 7 at Level 2, whose danger scale is 1.35
    # on health and 1.26 on damage, so the bases are 13 and 5.5). No eyes: it only hears (running is a noise of 0.4,
    # and several runners are heard from further off) and touches. Fed, it buries again within buryAfterFeedMs and
    # stays dormant for fedDormantSeconds.
    tasks = [{"code": "backrooms-clump", "priority": 1.6, "mincooldown": 0, "maxcooldown": 0, "reach": 1.3, "damage": 6.5,
              "cooldownMs": 3000, "grabsBeforeLeaving": 2, "crawlSpeed": 0.028, "wakeRange": 4,
              "buryAfterFeedMs": 10000, "fedDormantSeconds": 60,
              "senses": dict(special="noiseOnly", hearing=14, touch=2.5),
              "grabSound": "backrooms:entity/grab", "stirSound": "backrooms:effect/squelch"}]
    return {
        "code": "clump",
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "habitat-land"],
        "weight": 80,
        # The mass is 12 px tall; the limbs spread over two blocks. Two looks: with eyes and an ear, and without.
        "hitboxSize": {"x": 1.0, "y": 0.8},
        "deadHitboxSize": {"x": 1.0, "y": 0.5},
        "eyeHeight": 0.5,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-clump"},
        "client": common_client("backrooms:entity/clump", {"base": "backrooms:entity/clump", "alternates": [{"base": "backrooms:entity/clump-blind"}]},
                                [anim("idle", "idle", triggeredBy={"defaultAnim": True}), anim("stir", "stir", 1.0), anim("grab", "grab", 1.0, weight=10),
                                 anim("feed", "feed", 1.0, weight=5), anim("crawl", "crawl", 1.0),
                                 # (Weighted well over the idle, which would otherwise pull the buried mass half up out of the floor)
                                 anim("dormant", "dormant", 1.0, weight=20), anim("emerge", "emerge", 1.0, weight=20),
                                 anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]})], movable=False),
        "server": server(15, tasks, menace={"stalkSeconds": 180}, movable=False),
        "sounds": {"hurt": "game:effect/squish*", "death": "backrooms:effect/squelch"},
    }


def mangled():
    # Only ever put down by its own event (src/Entities/MangledEvent.cs), which brings the fog and the voices
    # (Its legs carry it about 0.007 a step at the walk's own pace: walking and running at more than that, the
    # animations are played faster to match, so the feet don't skate. Slower than you: it is the reach that kills.)
    task = menace_task(walkSpeed=0.01, runSpeed=0.024, stalkMin=8, stalkMax=14, glimpseFleeDistance=10,
                       damage=5, damageTier=3, damageType="BluntAttack", knockback=0, attackRange=4.5,
                       attackDurationMs=900, damageAtMs=450, attackCooldownMs=4000, attackAnimation="attack",
                       liftBlocks=7, soundRange=64)
    # Too big for any door: it walks the streets, and a house is safer from it. A harvestman as tall as a house: the
    # model stands 7.8 blocks to its crown of knees, drawn half as big again, 11.7; the knot of faces hangs at 5 to 7.
    # Nothing kills it.
    return tall_body("mangled", (2.0, 3.8), 6.5, 40, task, {"immortal": True, "unmoved": True, "huntSeconds": 600}, None,
                     {"hurt": "backrooms:entity/chorus", "death": "backrooms:entity/chorus"}, size=1.5, idle_anim="despair",
                     walk=1.4, run=1.7, weight=400)


def bacteria():
    # Level 0's dark figures: seen far off down the halls, now and then following. It never hunts in the Lobby but
    # for someone who runs near the way out, and then it howls first. It rises out of the black mould where it appears.
    # Its patience has an end: corner it (4 blocks for 1.5 s) and it lunges, chase it for 10 s and it howls and turns,
    # both a provoked hunt as a blow makes (turnsWhenCornered, turnsWhenChased; AiTaskMenace.TryTurnOnTarget).
    # Its run in the Lobby's fright is a little short of a sprint (AiTaskMenace: x0.92 unless struck; it once outran one,
    # and with nothing to make it give up, one hunt was death); struck, it comes at a sprint and hits hard: a runner who keeps going pulls away, and the hunt itself is short (AiTaskMenace.Hunt, huntsInLobby).
    task = menace_task(walkSpeed=0.022, runSpeed=0.05, stalkMin=12, stalkMax=20, glimpseFleeDistance=18,
                       damage=8, damageTier=2, damageType="SlashingAttack", knockback=0.6, attackRange=1.8,
                       attackDurationMs=1000, damageAtMs=440, attackCooldownMs=1800, attackAnimation="attack",
                       prefersHidden=True, huntsInLobby=True, turnsWhenCornered=True, turnsWhenChased=True, emergeAnimation="emerge", emergeMs=2500,
                       huntAnimation="howl", huntAnimationMs=1500, huntSound="backrooms:entity/howl", soundRange=48,
                       # What it perceives (README section 6.2)
                       senses=dict(sightLit=32, sightDim=16, sightDark=10, sightCone=70, hearing=28, memorySeconds=6, trackSeconds=15, trackError=10),
                       investigateSeconds=6, searchSeconds=8, retaliateSeconds=60,
                       # Hide from it and the fright ends: a search that finds nothing sends it away, not back to following
                       leavesAfterSearch=True)
    # The model stoops to 44 px (2.76 blocks), just under Level 0's ceiling; the hitbox is kept to a doorway's two
    # blocks, the head above it. Its long arms reach 1.6 blocks ahead.
    return tall_body("bacteria", (0.7, 1.95), 2.5, 30, task, {"stalkSeconds": 120, "maxEncounterSeconds": 300}, None,
                     {"hurt": "game:creature/drifter-hurt", "death": "backrooms:entity/howl"},
                     idles=[idle("lurk", 1.15, 6000, 12000, 15000, 45000)],
                     extra_anims=[anim("emerge", "emerge", weight=10), anim("howl", "howl", weight=10)], weight=80)


def wretch():
    # Wanderers worn down by hunger, thirst and sleeplessness: a slow shamble, a sprint past yours, a bite. In
    # ones and twos wherever wanderers gather, and Level 8's feral dark; drawn to anyone starving.
    task = menace_task(walkSpeed=0.02, runSpeed=0.048, stalkMin=8, stalkMax=14, glimpseFleeDistance=12,
                       damage=5.5, damageTier=1, damageType="PiercingAttack", knockback=0.3, attackRange=0.9,
                       attackDurationMs=1000, damageAtMs=430, attackCooldownMs=1400, attackAnimation="attack",
                       prefersHidden=True, retreatBelow=0.2, huntAnimation="snarl", huntAnimationMs=1200,
                       stalkSound="backrooms:entity/gurgle", huntSound="backrooms:entity/snarl",
                       # What is left of the person: a cough, a whispered plea, a cry
                       # (and a plea, a word with nothing left behind it: sounds/entity/plea)
                       voices=["backrooms:entity/gurgle", "backrooms:entity/plea", "backrooms:entity/cough", "backrooms:effect/whisper", "game:player/hurt*"],
                       soundRange=24,
                       # What it perceives (README 6.1): it comes for the starving (fearSense 10: the director weighs them 3 times)
                       senses=dict(sightLit=24, sightDim=12, sightDark=6, sightCone=90, hearing=20, fearSense=10, memorySeconds=8, trackSeconds=12, trackError=10),
                       investigateSeconds=8, searchSeconds=10, retaliateSeconds=60,
                       # Its speed by look (texture 0 common, 1 early, 2 far-gone): the early ones are slower, the far-gone quicker
                       lookSpeeds=[1.0, 0.9, 1.2])
    # The model is 28.9 px hunched (1.8 blocks), the eyes at 1.6
    return tall_body("wretch", (0.65, 1.8), 1.6, 18, task, {"stalkSeconds": 90, "maxEncounterSeconds": 300}, None,
                     {"hurt": "game:creature/drifter-hurt", "death": "game:creature/drifter-death"},
                     idles=[idle("huddle", 1.15, 6000, 12000, 20000, 60000), idle("gnaw", 1.2, 2000, 6000, 15000, 45000)],
                     looks=("early", "fargone"), extra_anims=[anim("snarl", "snarl", weight=10)], weight=60)


def giantspider():
    # Level 8's nests and dark (tools/gen_spider.py has its model, its task config and the lore)
    import gen_spider
    LANG.update(gen_spider.LANG)
    # (Its meat: the cookbook's "Deep fried Arachnid", "singe off the hairs"; raw bushmeat, cooked like any. And silk: 2 plus or minus 1)
    return gen_spider.entity(anim, common_client, server, [drop("game:bushmeat-raw", 1), drop("backrooms:spidersilk", 2, 1)])


def thething():
    tasks = [{"code": "backrooms-thething", "priority": 1.6, "mincooldown": 0, "maxcooldown": 0, "speed": 0.035, "rushSpeed": 0.14,
              "orbitRadius": 18, "damage": 8, "patienceSeconds": 40, "groanSound": "backrooms:entity/groan",
              # It perceives only what is in the water, and hears swimming within 40 (README section 6.2; the profile is
              # what /backrooms perceive shows: the task itself goes by depth)
              "senses": dict(special="water", hearing=40),
              # A lit lantern or oil lamp held under water within 12 blocks of its rush breaks the rush off: it turns
              # away and circles again, not rushing for 20 seconds (a torch goes out in water)
              "lampRange": 12, "lampBreakSeconds": 20}]
    return {
        "code": "thething",
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "habitat-water"],
        "habitat": "Underwater",
        "weight": 4000,
        "hitboxSize": {"x": 3.6, "y": 1.2},
        # The model is eleven blocks long: the game culls an entity by its selection box, so give it the body's length
        "selectionBoxSize": {"x": 7.5, "y": 2.0},
        "eyeHeight": 0.6,
        "attributes": {"killedByInfoText": "backrooms:deadcreature-thething"},
        "client": {
            "renderer": "Shape",
            "shape": {"base": "backrooms:entity/thething"},
            "texture": {"base": "backrooms:entity/thething"},
            "size": 1,
            "behaviors": [{"code": "controlledphysics", "stepHeight": 0}, {"code": "interpolateposition"}],
            "animations": [anim("swim", "swim", 1.0, triggeredBy={"defaultAnim": True}), anim("rush", "rush", 1.0, weight=5),
                           anim("attack", "attack", 1.0, weight=10)],
        },
        "server": {
            "behaviors": [
                {"code": "controlledphysics", "stepHeight": 0},
                # Not fightable: no health; struck, it goes back down
                {"code": "backrooms-menace", "immortal": True, "stalkSeconds": 240, "huntSeconds": 240},
                {"code": "taskai", "aiCreatureType": "Default", "aitasks": tasks},
                {"code": "entitystatetags"},
            ],
        },
        "sounds": {},
    }


# ---------------------------------------------------------------- The Animations (Level 94, Motion)
# Entity 32: stop-motion figures that hunt anything that does not look animated. Their models (gen_models.py) are all
# animated in held poses; the attack each one makes has its own animation code. What they leave when killed is what
# they were made of (dropped on death, no knife needed).


def optional_sounds(*codes):
    """Sounds of ours that another part of the mod provides, kept only if their files are there (so a missing one is
    never asked for): "backrooms:entity/allglory" -> assets/backrooms/sounds/entity/allglory.ogg."""
    return [c for c in codes if os.path.exists(os.path.join(ASSETS, "sounds", *c.split(":", 1)[1].split("/")) + ".ogg")]


ANIMATION_MENACE = {"stalkSeconds": 150, "maxEncounterSeconds": 300}


def motion_body(code, hitbox, eye, health, task, attack, drops, sounds, weight=60, size=1.0, mechanical=False, menace=None):
    """One of the Animations: walk, run, idle, its attack, hurt and die, all in its own stop-motion."""
    animations = [
        anim("hurt", "hurt", 1.0, weight=10, blendMode="AddAverage"),
        anim("die", "die", 1.0, weight=10, triggeredBy={"onControls": ["dead"]}),
        anim("idle", "idle", triggeredBy={"defaultAnim": True}, blendMode="AddAverage"),
        anim("walk", "walk", 1.0),
        anim("run", "run", 1.0),
        anim(attack, attack, 1.0, weight=10),
    ]
    tasks = [task, dict(WANDER, movespeed=0.006), LOOKAROUND]
    return {
        "code": code,
        "class": "EntityAgent",
        "tags": ["backrooms-entity", "humanoid", "habitat-land"],
        "weight": weight,
        "hitboxSize": {"x": hitbox[0], "y": hitbox[1]},
        "deadHitboxSize": {"x": hitbox[0], "y": 0.4},
        "eyeHeight": eye,
        "attributes": dict({"killedByInfoText": f"backrooms:deadcreature-{code}"}, **({"isMechanical": True} if mechanical else {})),
        "drops": drops,
        "client": common_client(f"backrooms:entity/{code}", {"base": f"backrooms:entity/{code}"}, animations, size),
        "server": server(health, tasks, menace=menace or {"stalkSeconds": 150}, decay=None),
        "sounds": sounds,
    }


def animation_clay():
    # 1.65 blocks, hunched; a little slower than a walking player (who walks at about 0.025 in these units: the
    # game's base move speed 1.5 blocks/s times the 1/60 s physics step)
    task = menace_task(walkSpeed=0.012, runSpeed=0.021, stalkMin=6, stalkMax=11, glimpseFleeDistance=12,
                       damage=4, damageTier=1, damageType="BluntAttack", knockback=0.15, attackRange=1.0,
                       attackDurationMs=800, damageAtMs=450, attackCooldownMs=1800, walkAnimation="walk", runAnimation="run",
                       attackAnimation="smother", stalkSound="game:effect/clayform", attackSound="game:effect/squish*",
                       voices=optional_sounds("backrooms:entity/allglory"), soundRange=24)
    return motion_body("animation-clay", (0.75, 1.65), 1.45, 24, task, "smother",
                       [drop("game:clay-blue", 6, 2)], {"hurt": "game:effect/squish*", "death": "game:effect/clayform"}, weight=80, menace=ANIMATION_MENACE)


def animation_wooden():
    # 1.84 blocks; about a quarter faster than a walking player, and it hits hard. Wood: it keeps clear of fire
    task = menace_task(walkSpeed=0.016, runSpeed=0.031, stalkMin=8, stalkMax=13, glimpseFleeDistance=14,
                       damage=5, damageTier=2, damageType="BluntAttack", knockback=0.9, attackRange=1.1,
                       attackDurationMs=800, damageAtMs=420, attackCooldownMs=1500, walkAnimation="walk", runAnimation="run",
                       attackAnimation="club", fearsFire=True, stalkSound="game:block/woodcreak*", attackSound="game:block/chop*",
                       voices=optional_sounds("backrooms:entity/allglory", "backrooms:entity/laughter"), soundRange=28)
    return motion_body("animation-wooden", (0.6, 1.8), 1.65, 18, task, "club",
                       [drop("game:stick", 4, 2), drop("game:plank-oak", 2, 1)],
                       {"hurt": "game:block/stickhit", "death": "game:block/stickbreak"}, weight=40, menace=ANIMATION_MENACE)


def animation_paper():
    # 1.47 blocks and flat; weak, and it comes in groups. Paper cuts; paper burns
    task = menace_task(walkSpeed=0.014, runSpeed=0.026, stalkMin=6, stalkMax=10, glimpseFleeDistance=10,
                       damage=1.5, damageTier=0, damageType="SlashingAttack", knockback=0.1, attackRange=0.9,
                       attackDurationMs=600, damageAtMs=330, attackCooldownMs=1100, walkAnimation="walk", runAnimation="run",
                       attackAnimation="slap", fearsFire=True, retreatBelow=0.3, stalkSound="game:effect/writing",
                       attackSound="game:effect/swoosh", voices=optional_sounds("backrooms:entity/laughter"), soundRange=20)
    return motion_body("animation-paper", (0.5, 1.45), 1.3, 5, task, "slap",
                       [drop("game:paper-parchment", 2, 1)], {"hurt": "game:effect/clothrip", "death": "game:effect/clothrip"}, weight=5, menace=ANIMATION_MENACE)


def roboman():
    # The castle's guards: 1.53 blocks to the top of the head (1.77 to the bulb on its antenna). Slow, and it hits
    # hard. It only ever hunts (see Roster.Castle), and gives up long after anything else would.
    task = menace_task(walkSpeed=0.012, runSpeed=0.024, stalkMin=6, stalkMax=10, glimpseFleeDistance=10,
                       damage=6, damageTier=3, damageType="BluntAttack", knockback=1.2, attackRange=1.1,
                       attackDurationMs=700, damageAtMs=330, attackCooldownMs=2000, walkAnimation="walk", runAnimation="run",
                       attackAnimation="punch", stalkSound="game:effect/timeswitch", huntSound="game:effect/receptionbell",
                       attackSound="game:block/heavymetal-hit*", voices=optional_sounds("backrooms:entity/allglory"), soundRange=32)
    return motion_body("roboman", (0.8, 1.6), 1.45, 35, task, "punch",
                       [drop("game:metalnailsandstrips-iron", 3, 1), drop("backrooms:metalbracket", 1, 1)],
                       {"hurt": "game:creature/locust/hurt", "death": "game:creature/locust/death"}, weight=120, mechanical=True,
                       menace={"stalkSeconds": 150, "huntSeconds": 300})


# ---------------------------------------------------------------- Wanderers

def trade(code, price, stock=2, stack=1, kind="item"):
    return {"code": code, "type": kind, "stacksize": stack, "stock": {"avg": stock, "var": stock * 0.25}, "price": {"avg": price, "var": price * 0.25}}


# Each site's wanderer deals in what its place has and buys what it lacks (docs/design/traders/README.md, from the lore
# in docs/design/traders/lore.md). Prices in rusty gears, 1 to 8; stocks kept small (Almond Water above all: water is
# meant to stay scarce). Every list is written to config/trade/wanderer-<site>.json, which WandererSystem gives the
# wanderer of that site; "camp" doubles as the entity type's own list, for a wanderer with no site yet.
#   (code, price, stock, stacksize[, "block"])
WANDERER_SITES = {
    # Level 1: a crate-pickers' camp round a burning barrel, unaligned. Crate goods, the basics, seeds; salvage and hides.
    # (The Level 1 notes say: salvage and hides for Almond Water, Firesalt, candles, bandages and seeds.)
    "camp": {
        "sells": [("backrooms:almondwater", 1, 3, 1), ("backrooms:crackers", 1, 3, 2), ("backrooms:cannedbeans", 2, 2, 1),
                  ("game:candle", 1, 3, 2), ("backrooms:firesalt", 3, 2, 1, "block"), ("game:bandage-clean", 2, 2, 1),
                  ("game:flaxtwine", 1, 3, 4), ("game:seeds-flax", 2, 2, 4), ("game:seeds-cabbage", 2, 2, 4), ("game:linensack", 2, 1, 1)],
        "buys": [("backrooms:metalbracket", 1, 6, 4), ("backrooms:scrapwire", 1, 6, 5), ("backrooms:glassshard", 1, 4, 8),
                 ("game:hide-raw-medium", 2, 3, 1), ("game:hide-raw-large", 3, 2, 1), ("game:cloth-plain", 1, 4, 4),
                 ("game:metalbit-copper", 1, 6, 6)],
        "sellMax": 9, "buyMax": 7,
    },
    # Level 4: an M.E.G. supply outpost, where Almond Water is most plentiful: water (cheapest here), bottles to carry it
    # down to Level 5, medicine, light, seeds. Buys specimens for the M.E.G.'s files, salvage, paper, the hotel's silver.
    "outpost": {
        "sells": [("backrooms:almondwater", 1, 4, 1), ("backrooms:almondwaterblue", 2, 2, 1), ("backrooms:almondwatergreen", 2, 2, 1),
                  ("backrooms:emptybottle", 1, 3, 1), ("game:bandage-clean", 2, 3, 1), ("game:poultice-linen-horsetail", 3, 2, 1),
                  ("game:candle", 1, 3, 2), ("backrooms:firesalt", 3, 2, 1, "block"), ("game:seeds-flax", 2, 2, 4), ("game:seeds-cabbage", 2, 2, 4)],
        "buys": [("backrooms:mothquill", 2, 2, 1), ("backrooms:mothjelly", 3, 1, 1), ("backrooms:clumpsinew", 2, 2, 1),
                 ("backrooms:metalbracket", 1, 6, 4), ("backrooms:scrapwire", 1, 6, 5), ("backrooms:glassshard", 1, 4, 8),
                 ("game:paper-parchment", 1, 4, 8), ("game:metalbit-silver", 2, 4, 3)],
        "sellMax": 9, "buyMax": 7,
    },
    # Level 8, the 9th Road: an M.E.G. camp on the road, stocked by the B.N.T.G.'s caravans. Caving gear, light, food,
    # weapons for the dark; water dearer. Buys what keeps people warm and what maps are drawn on, and spider silk.
    "road": {
        "sells": [("backrooms:cannedbeans", 2, 3, 1), ("backrooms:crackers", 1, 3, 2), ("backrooms:almondwater", 2, 2, 1),
                  ("game:rope", 2, 2, 1), ("game:torch-basic-extinct-up", 1, 4, 2, "block"), ("game:lantern-small-up", 6, 1, 1, "block"),
                  ("game:pickaxe-tinbronze", 8, 1, 1), ("game:knife-generic-tinbronze", 6, 1, 1), ("game:spear-generic-tinbronze", 8, 1, 1),
                  ("game:armor-body-sewn-linen", 6, 1, 1), ("game:bandage-clean", 2, 2, 1)],
        "buys": [("game:hide-raw-medium", 2, 3, 1), ("game:hide-raw-large", 3, 2, 1), ("game:cloth-plain", 1, 4, 4),
                 ("backrooms:spidersilk", 2, 3, 1), ("game:paper-parchment", 1, 4, 8), ("backrooms:metalbracket", 1, 4, 4)],
        "sellMax": 8, "buyMax": 6,
    },
    # Level 11: a B.N.T.G. street vendor. The city has food and Almond Water for the taking, so it sells what the city
    # lacks: B.N.T.G. candy, the coloured waters, Firesalt, bronze, lanterns, chalk. Buys rare things from far levels.
    "city": {
        "sells": [("backrooms:candybar", 1, 3, 1), ("backrooms:chips", 1, 3, 1), ("backrooms:soda", 1, 3, 1),
                  ("backrooms:almondwaterblue", 2, 2, 1), ("backrooms:almondwatergreen", 2, 2, 1), ("backrooms:firesalt", 4, 2, 1, "block"),
                  ("game:knife-generic-tinbronze", 6, 1, 1), ("game:lantern-small-up", 6, 1, 1, "block"),
                  ("game:armor-body-sewn-linen", 5, 1, 1), ("backrooms:chalk", 2, 2, 1)],
        "buys": [("game:metalbit-silver", 2, 4, 3), ("game:metalbit-brass", 1, 4, 4), ("backrooms:l3999-ticket", 1, 4, 5),
                 ("backrooms:almondmilk", 2, 2, 1), ("backrooms:epsomsalt", 2, 2, 2), ("backrooms:mothquill", 2, 2, 1),
                 ("game:hide-raw-large", 3, 2, 1)],
        "sellMax": 8, "buyMax": 6,
    },
    # The End: a Junkie, at home in the library (trades only with someone carrying Memory Juice: the dialogue). Sells
    # what the library holds and what was brought from home; buys juice above all, and food, which The End has none of.
    "end": {
        "sells": [("backrooms:end-cataloguecard", 3, 2, 1), ("game:paper-parchment", 1, 4, 4), ("game:candle", 1, 3, 2),
                  ("backrooms:l974-plush-bear", 4, 1, 1), ("backrooms:almondwatergreen", 2, 1, 1), ("backrooms:chalk", 2, 1, 1)],
        "buys": [("backrooms:end-memoryjuice", 6, 4, 1), ("backrooms:crackers", 1, 3, 2), ("backrooms:cannedbeans", 2, 2, 1),
                 ("backrooms:almondwater", 1, 3, 1), ("backrooms:candybar", 1, 2, 1)],
        "sellMax": 5, "buyMax": 5,
    },
    # The Hub, the M.E.G.'s doorstep carpet by the city door (whose two Level Keys a week HubTower puts among the wares,
    # in free slots). Field supplies for a cold, foodless place; buys salvage, paper and The End's catalogue cards.
    "hub": {
        "sells": [("backrooms:almondwater", 2, 2, 1), ("game:bandage-clean", 2, 2, 1), ("backrooms:chalk", 2, 2, 1),
                  ("game:candle", 1, 3, 2), ("backrooms:crackers", 1, 3, 2), ("game:torch-basic-extinct-up", 1, 3, 2, "block"),
                  ("game:armor-body-sewn-linen", 6, 1, 1), ("backrooms:firesalt", 3, 2, 1, "block")],
        "buys": [("backrooms:metalbracket", 1, 6, 4), ("backrooms:scrapwire", 1, 6, 5), ("backrooms:glassshard", 1, 4, 8),
                 ("game:paper-parchment", 1, 4, 8), ("game:hide-raw-medium", 2, 2, 1), ("backrooms:end-cataloguecard", 2, 2, 1)],
        "sellMax": 7, "buyMax": 6,
    },
    # The Hub, Camp Amber by the Level 1 door: teachers with limited supplies, cheap, for the newly arrived. Buys the
    # Lobby's scraps, which is all a new wanderer has.
    "amber": {
        "sells": [("backrooms:almondwater", 1, 2, 1), ("backrooms:crackers", 1, 3, 2), ("game:candle", 1, 3, 2),
                  ("game:bandage-clean", 2, 2, 1), ("game:flaxtwine", 1, 3, 4), ("backrooms:emptybottle", 1, 2, 1),
                  ("game:seeds-flax", 2, 2, 4)],
        "buys": [("backrooms:metalbracket", 1, 6, 4), ("backrooms:scrapwire", 1, 6, 5), ("backrooms:glassshard", 1, 4, 8),
                 ("backrooms:carpetfibre", 1, 4, 8), ("backrooms:wallpaperstrip", 1, 4, 8), ("game:cloth-plain", 1, 3, 4)],
        "sellMax": 6, "buyMax": 5,
    },
    # Level 3999: campers of the Megacolony, warm and fed. Sell the mall's food, water and prizes; buy tickets (for the
    # counters), Firesalt and hides for the dark fringe, cloth and brackets the mall doesn't give.
    "3999": {
        "sells": [("backrooms:almondwater", 1, 3, 1), ("backrooms:l3999-traymeal-burger", 2, 2, 1), ("backrooms:l3999-traymeal-noodles", 2, 2, 1),
                  ("backrooms:l3999-popcorn", 1, 3, 1), ("backrooms:l3999-cottoncandy", 1, 3, 1), ("backrooms:l3999-soda-cherry", 1, 2, 1),
                  ("backrooms:l3999-glowband-cyan", 2, 1, 1), ("game:seeds-cabbage", 2, 2, 4), ("game:lantern-small-up", 7, 1, 1, "block")],
        "buys": [("backrooms:l3999-ticket", 1, 6, 5), ("backrooms:firesalt", 3, 2, 1, "block"), ("game:hide-raw-medium", 2, 2, 1),
                 ("game:cloth-plain", 1, 3, 4), ("backrooms:metalbracket", 1, 4, 4)],
        "sellMax": 7, "buyMax": 4,
    },
}


def trade_props(site):
    """A site's trade list, as vanilla's tradeProps."""
    spec = WANDERER_SITES[site]

    def items(rows):
        return [trade(r[0], r[1], r[2], r[3], r[4] if len(r) > 4 else "item") for r in rows]
    return {
        "money": {"avg": 25, "var": 6},
        "selling": {"maxItems": spec["sellMax"], "list": items(spec["sells"])},
        "buying": {"maxItems": spec["buyMax"], "list": items(spec["buys"])},
    }


WANDERER_NAMES = ["Wanderer", "Courier", "Old Lamp", "Doorman", "Static", "Exit", "Mender", "Ledger", "Gauge", "Stray", "Waypoint",
                  "Bulb", "Chalk", "Almond", "Fuse", "Lintel", "Cartographer", "Long Walk", "Seven", "Quiet"]

# What a new wanderer is called at each site (one is picked when it is put down; the names of wanderers already met
# are kept): camp survivors by what they carry, M.E.G. operatives by callsign, B.N.T.G. traders by trade name.
WANDERER_SITE_NAMES = {
    "camp": ["Pell", "Barrel", "Old Lamp", "Stray", "Fuse", "Crate", "Mender", "Quiet"],
    "outpost": ["Compass", "Quartermaster", "Survey", "Gauge", "Ledger"],
    "road": ["Lumen", "Gravel", "Marker", "Caravan", "Long Walk"],
    "city": ["Prospero", "Margin", "Bargain", "Courier", "Ledger"],
    "end": ["Wick", "Sunday", "Porch Light", "Daydream"],
    "hub": ["Doorman", "Keyholder", "Register", "Lintel"],
    "amber": ["Amber", "Primer", "Signpost", "Chalk"],
    "3999": ["Token", "Seven", "Lobby", "Neon"],
}


def wanderer_trade_files():
    for site in WANDERER_SITES:
        write_json(trade_props(site), "config", "trade", "wanderer-" + site + ".json")


def wanderer():
    """A wanderer who trades: the vanilla trader, dressed from the survival-goods trader's wardrobe, with a trade list
    and a name for each site (WandererSites, WandererSystem) and a dialogue of its own (tools/gen_dialogue.py). Rusty
    gears are the money, as everywhere in Vintage Story."""
    import json5
    base = json5.load(open(vanilla("survival/entities/humanoid/trader-male.json"), encoding="utf-8"))
    entity = dict(base)
    entity["code"] = "wanderer"
    entity["variantgroups"] = [{"code": "gender", "states": ["male"]}]
    attrs = dict(base["attributes"])
    attrs.pop("tradePropsFile", None)
    attrs["tradeProps"] = trade_props("camp")
    attrs["backroomsSiteNames"] = WANDERER_SITE_NAMES
    outfits = base["attributes"]["partialRandomOutfitsByType"]
    attrs["partialRandomOutfitsByType"] = {"*": outfits["trader-male-*-temperate"]}
    entity["attributes"] = attrs
    client = dict(base["client"])
    client["behaviors"] = [dict(b, dialogue="config/dialogue/trader") if b["code"] == "conversable" and "dialogueByType" in b else b for b in client["behaviors"]]
    for b in client["behaviors"]:
        b.pop("dialogueByType", None)
    entity["client"] = client
    server = dict(base["server"])
    behaviors = []
    for b in server["behaviors"]:
        b = dict(b)
        if b["code"] == "conversable":
            b.pop("dialogueByType", None)
            b["dialogue"] = "config/dialogue/trader"
        if b["code"] == "nametag":
            b["selectFromRandomName"] = WANDERER_NAMES
        # Wanderers never fight back: struck, they only back away (the vanilla trader may turn on whoever hits it)
        if b["code"] == "emotionstates":
            b["states"] = [dict(st, chance=1) for st in b["states"] if st["code"] == "fleeondamage"]
        if b["code"] == "taskai":
            b["aitasks"] = [t for t in b["aitasks"] if t["code"] not in ("meleeattack", "seekentity")]
        behaviors.append(b)
    server["behaviors"] = behaviors
    entity["server"] = server
    entity["tags"] = ["humanoid", "trader", "human", "habitat-land", "backrooms-wanderer"]

    # The vanilla file's paths have no domain, so in ours they would point at our own assets
    def game(path):
        return path if ":" in path else "game:" + path
    client["shape"] = {"base": game(client["shape"]["base"])}
    client["texture"] = {"base": game(client["texture"]["base"])}
    attrs["outfitConfigFileName"] = game(attrs["outfitConfigFileName"])
    for b in client["behaviors"] + behaviors:
        if b["code"] == "conversable":
            b["dialogue"] = "backrooms:config/dialogue/wanderer"
    entity["sounds"] = {k: game(v) if isinstance(v, str) else v for k, v in (base.get("sounds") or {}).items()}
    return entity


# ---------------------------------------------------------------- Firesalt

def firesalt():
    """Firesalt: a block (it is put down to burn) carried as a stack of handfuls."""
    img = Image.new("RGBA", (32, 32))
    rng = random.Random(77)
    px = img.load()
    for y in range(32):
        for x in range(32):
            v = rng.random()
            base = (238, 222, 214) if v > 0.25 else (200, 120, 96)
            if v > 0.93:
                base = (255, 150, 90)
            m = 0.85 + 0.25 * rng.random()
            px[x, y] = tuple(min(255, int(c * m)) for c in base) + (255,)
    path = os.path.join(ASSETS, "textures", "block", "firesalt.png")
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT))

    # A low heap of crystals
    elements = []
    rng = random.Random(78)
    for i, (x0, z0, w, d, h) in enumerate([(5, 5, 6, 6, 2), (4, 7, 3, 3, 1.5), (9, 4, 3, 3, 1.5), (7, 9, 3, 3, 1.5), (6.5, 6.5, 3, 3, 3.2), (8, 7, 1.5, 1.5, 4)]):
        faces = {s: {"texture": "#salt", "uv": [x0, z0, x0 + w, z0 + h if s not in ("up", "down") else z0 + d], "glow": 120} for s in ("north", "east", "south", "west", "up")}
        elements.append({"name": f"Crystal{i}", "from": [x0, 0, z0], "to": [x0 + w, h, z0 + d], "faces": faces})
    shape = {"textureWidth": 16, "textureHeight": 16, "textures": {"salt": "backrooms:block/firesalt"}, "elements": elements}
    write_json(shape, "shapes", "block", "firesalt.json")

    block = {
        "code": "firesalt",
        "class": "BackroomsFiresalt",
        "entityClass": "BackroomsFiresalt",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "shape": {"base": "backrooms:block/firesalt"},
        "textures": {"salt": {"base": "backrooms:block/firesalt"}},
        "drawtype": "json",
        "renderpass": "OpaqueNoCull",
        "lightAbsorption": 0,
        "lightHsv": [2, 6, 17],
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "replaceable": 5000,
        "resistance": 0.1,
        "maxStackSize": 32,
        "collisionbox": None,
        "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.2, "x2": 0.8, "y2": 0.3, "z2": 0.8},
        # Spent once lifted: it burns away
        "drops": [],
        "materialDensity": 600,
        "sounds": {"place": "game:block/sand", "break": "game:block/sand", "hit": "game:block/sand", "ambient": "game:effect/embers", "ambientBlockCount": 1},
        "particleProperties": [
            {"hsvaColor": [{"avg": 10, "var": 10}, {"avg": 255, "var": 30}, {"avg": 255, "var": 30}, {"avg": 255, "var": 0}],
             "gravityEffect": {"dist": "invexp", "avg": -0.05, "var": 0.2},
             "posOffset": [{"avg": 0, "var": 0.15}, {"avg": 0.1, "var": 0}, {"avg": 0, "var": 0.15}],
             "velocity": [{"avg": 0, "var": 0.03}, {"avg": 0.12, "var": 0.04}, {"avg": 0, "var": 0.03}],
             "quantity": {"avg": 0.06}, "size": {"avg": 0.3, "var": 0.1}, "sizeEvolve": {"transform": "linear", "factor": -0.6},
             "lifeLength": {"avg": 0.6, "var": 0.3}, "vertexFlags": 255, "particleModel": "Quad"},
        ],
        "guiTransform": {"rotation": {"x": -30, "y": 45, "z": 0}, "origin": {"x": 0.5, "y": 0.1, "z": 0.5}, "scale": 2.6},
        "groundTransform": {"scale": 2.5},
        "tpHandTransform": {"translation": {"x": -0.9, "y": -0.3, "z": -0.6}, "scale": 0.8},
    }
    write_json(block, "blocktypes", "firesalt.json")

    write_json({
        "ingredientPattern": "SP",
        "ingredients": {"S": {"type": "item", "code": "game:salt"}, "P": {"type": "item", "code": "game:powder-sulfur"}},
        "width": 2, "height": 1, "shapeless": True,
        "output": {"type": "block", "code": "backrooms:firesalt", "stacksize": 2},
    }, "recipes", "grid", "firesalt.json")


# ---------------------------------------------------------------- Hive heart and Clump remnant

def _plain_texture(name, base, flecks, seed, streaks=None):
    img = Image.new("RGBA", (16, 16))
    rng = random.Random(seed)
    px = img.load()
    for y in range(16):
        for x in range(16):
            v = rng.random()
            c = base if v > 0.2 else flecks[0]
            if v > 0.92:
                c = flecks[1]
            m = 0.88 + 0.22 * rng.random()
            px[x, y] = tuple(min(255, int(k * m)) for k in c) + (255,)
    for (x0, y0, x1, y1, col) in streaks or ():
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[x, y] = col + (255,)
    path = os.path.join(ASSETS, "textures", "block", name + ".png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT))


def _box(name, frm, to, tex, faces=("north", "east", "south", "west", "up", "down")):
    return {"name": name, "from": list(frm), "to": list(to), "faces": {s: {"texture": "#" + tex, "uv": [0, 0, 16, 16]} for s in faces}}


def mothhiveheart():
    """The hive's heart: a resin column ringed by larval columns. Placed at runtime (MenaceSystem.Hives.cs)."""
    _plain_texture("mothhiveheart-resin", (122, 96, 58), [(78, 58, 34), (170, 138, 84)], 301)
    # Larvae: pale, ringed with darker segments
    segs = [(0, y, 16, y + 1, (168, 156, 124)) for y in range(1, 16, 4)]
    _plain_texture("mothhiveheart-larva", (222, 210, 176), [(190, 176, 140), (240, 232, 204)], 302, segs)
    elements = [_box("Core", (4, 0, 4), (12, 13, 12), "resin"), _box("Cap", (3, 13, 3), (13, 15, 13), "resin")]
    for i, (x, z) in enumerate([(2, 2), (10, 2), (2, 10), (10, 10)]):
        elements.append(_box(f"Larva{i}", (x, 1, z), (x + 4, 12 - (i % 2) * 2, z + 4), "larva"))
    shape = {"textureWidth": 16, "textureHeight": 16,
             "textures": {"resin": "backrooms:block/mothhiveheart-resin", "larva": "backrooms:block/mothhiveheart-larva"}, "elements": elements}
    write_json(shape, "shapes", "block", "mothhiveheart.json")
    block = {
        "code": "mothhiveheart",
        "class": "BackroomsMothHiveHeart",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "shape": {"base": "backrooms:block/mothhiveheart"},
        "textures": {"resin": {"base": "backrooms:block/mothhiveheart-resin"}, "larva": {"base": "backrooms:block/mothhiveheart-larva"}},
        "drawtype": "json",
        "blockmaterial": "Plant",
        "lightAbsorption": 0,
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        # Slow to break by hand: it is meant to be a decision
        "resistance": 6,
        "collisionbox": {"x1": 0.125, "y1": 0, "z1": 0.125, "x2": 0.875, "y2": 0.95, "z2": 0.875},
        "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.95, "z2": 0.9},
        # Nothing yet: BlockMothHiveHeart.HiveHeartDrops is where the quills and moth jelly are added
        "drops": [],
        "materialDensity": 400,
        "sounds": {"place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
        "guiTransform": {"rotation": {"x": -30, "y": 45, "z": 0}, "origin": {"x": 0.5, "y": 0.4, "z": 0.5}, "scale": 1.6},
    }
    write_json(block, "blocktypes", "mothhiveheart.json")


def clumpremnant():
    """A killed Clump's remains: a flat patch of flesh. After a day it grows a new Clump unless burnt (BlockEntityClumpRemnant)."""
    veins = [(3, 2, 4, 9, (96, 40, 52)), (9, 5, 10, 14, (96, 40, 52)), (5, 9, 12, 10, (84, 34, 46))]
    _plain_texture("clumpremnant", (176, 112, 112), [(132, 72, 78), (214, 168, 150)], 303, veins)
    elements = [
        _box("Patch", (2, 0, 2), (14, 1, 14), "flesh"),
        _box("Lump", (5, 1, 5), (11, 2, 11), "flesh", ("north", "east", "south", "west", "up")),
        _box("Knuckle", (8, 1, 9), (10, 3, 11), "flesh", ("north", "east", "south", "west", "up")),
    ]
    write_json({"textureWidth": 16, "textureHeight": 16, "textures": {"flesh": "backrooms:block/clumpremnant"}, "elements": elements}, "shapes", "block", "clumpremnant.json")
    block = {
        "code": "clumpremnant",
        "class": "BackroomsClumpRemnant",
        "entityClass": "BackroomsClumpRemnant",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "shape": {"base": "backrooms:block/clumpremnant"},
        "textures": {"flesh": {"base": "backrooms:block/clumpremnant"}},
        "drawtype": "json",
        "blockmaterial": "Plant",
        "lightAbsorption": 0,
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "replaceable": 5000,
        "resistance": 0.5,
        "collisionbox": None,
        "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.2, "z2": 0.9},
        # Nothing yet: BlockClumpRemnant.RemnantDrops is where the sinew is added
        "drops": [],
        "materialDensity": 600,
        "sounds": {"place": "game:block/plant", "break": "game:block/plant", "hit": "game:block/plant"},
        "guiTransform": {"rotation": {"x": -30, "y": 45, "z": 0}, "origin": {"x": 0.5, "y": 0.1, "z": 0.5}, "scale": 2.2},
    }
    write_json(block, "blocktypes", "clumpremnant.json")


# ---------------------------------------------------------------- Names

LANG = {
    "item-creature-hound": "Hound",
    "item-creature-smiler": "Smiler",
    "item-creature-faceling": "Faceling",
    "item-creature-faceling-child": "Faceling child",
    "item-creature-deathmoth-male": "Deathmoth",
    "item-creature-deathmoth-female": "Deathmoth (female)",
    "item-creature-skinstealer": "Skin-Stealer",
    "item-creature-duller": "Duller",
    "item-creature-deathrat": "Death Rat",
    # prefixandcreature-<code> is what the server's death message names the killer by ("got killed by a Hound");
    # without it the game says "a wild animal"
    "prefixandcreature-hound": "a Hound",
    "prefixandcreature-smiler": "a Smiler",
    "prefixandcreature-faceling": "a Faceling",
    "prefixandcreature-faceling-child": "a Faceling child",
    "prefixandcreature-deathmoth-male": "Deathmoths",
    "prefixandcreature-deathmoth-female": "Deathmoths",
    "prefixandcreature-skinstealer": "a Skin-Stealer",
    "prefixandcreature-duller": "a Duller",
    "prefixandcreature-deathrat": "Death Rats",
    "deadcreature-hound": "Killed by a Hound",
    "deadcreature-smiler": "Killed by a Smiler",
    "deadcreature-faceling": "Killed by a Faceling",
    "deadcreature-deathmoth": "Killed by Deathmoths",
    "deadcreature-skinstealer": "Killed by a Skin-Stealer",
    "deadcreature-duller": "Killed by a Duller",
    "deadcreature-deathrat": "Killed by Death Rats",
    "item-creature-wanderer-male": "Wanderer",
    "prefixandcreature-wanderer-male": "a Wanderer",
    "item-creature-clump": "Clump",
    "prefixandcreature-clump": "a Clump",
    "item-creature-mangled": "The Mangled",
    "prefixandcreature-mangled": "the Mangled",
    "item-creature-thething": "The Thing",
    "prefixandcreature-thething": "something in the deep",
    "deadcreature-clump": "Killed by a Clump",
    "deadcreature-mangled": "Killed by the Mangled",
    "deadcreature-thething": "Killed by something in the deep",
    "item-creature-bacteria": "Bacteria",
    "prefixandcreature-bacteria": "the Bacteria",
    "deadcreature-bacteria": "Taken by the Bacteria",
    "item-creature-wretch": "Wretch",
    "prefixandcreature-wretch": "a Wretch",
    "deadcreature-wretch": "Killed by a Wretch",
    "item-creature-animation-clay": "Clay Animation",
    "item-creature-animation-wooden": "Wooden Animation",
    "item-creature-animation-paper": "Paper Animation",
    "item-creature-roboman": "Robo-Man",
    "prefixandcreature-animation-clay": "a Clay Animation",
    "prefixandcreature-animation-wooden": "a Wooden Animation",
    "prefixandcreature-animation-paper": "Paper Animations",
    "prefixandcreature-roboman": "a Robo-Man",
    "deadcreature-animation-clay": "Smothered by a Clay Animation",
    "deadcreature-animation-wooden": "Killed by a Wooden Animation",
    "deadcreature-animation-paper": "Killed by Paper Animations",
    "deadcreature-roboman": "Killed by a Robo-Man",
    "block-firesalt": "Firesalt",
    "blockdesc-firesalt": "A strange salt that burns with a hot red light once set down. While it burns, nothing hostile comes near. Burns for half a day.",
    "firesalt-hoursleft": "Burns for about {0} more hours",
    "block-mothhiveheart": "Deathmoth Hive Heart",
    "blockdesc-mothhiveheart": "Resin walled round columns of pale larvae, at the heart of a Deathmoth hive. Breaking it brings every female near, and more after them.",
    "block-clumpremnant": "Clump Remnant",
    "blockdesc-clumpremnant": "What is left of a Clump: a patch of flesh on the floor. Left alone, it grows a new one in about a day. Fire ends it.",
    "clumpremnant-hoursleft": "Grows a new Clump in about {0} hours",
}


def merge_lang():
    """Adds the names to lang/en.json without disturbing its layout: existing keys updated in place, new ones appended."""
    path = os.path.join(ASSETS, "lang", "en.json")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new_lines = []
    for key, value in LANG.items():
        line = TAB + json.dumps(key) + ": " + json.dumps(value, ensure_ascii=False)
        pattern = re.compile("^" + TAB + re.escape(json.dumps(key)) + ":.*?(,?)$", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda m: line + m.group(1), text, count=1)
        else:
            new_lines.append(line)
    if new_lines:
        body = text.rstrip().rpartition("}")[0].rstrip()
        if not body.endswith(",") and not body.endswith("{"):
            body += ","
        text = body + NL + NL + ("," + NL).join(new_lines) + NL + "}" + NL
    with open(path, "w", encoding="utf-8", newline=NL) as f:
        f.write(text)
    json.loads(text)


def main():
    import gen_models
    gen_models.build()
    faceling_shape()
    faceling_textures()
    for entity in (hound(), smiler(), faceling(), faceling(child=True), skinstealer(), duller(), deathrat(), deathmoth(), wanderer(), clump(), mangled(), thething(), bacteria(), wretch(),
                   animation_clay(), animation_wooden(), animation_paper(), roboman(), giantspider()):
        write_json(sync_harvestable(entity), "entities", entity["code"] + ".json")
    wanderer_trade_files()
    firesalt()
    mothhiveheart()
    clumpremnant()
    merge_lang()


if __name__ == "__main__":
    main()
