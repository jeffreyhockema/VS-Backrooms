"""The Level Keys (for tools/gen_hub.py): one item, backrooms:hub-key-<tag>, for every level the Hub has a door to.

Each key looks like where it comes from (hub-plan.md 4.6) and bears its door's sigil on the bow (gen_hub_sigils.py).
Keys are modelled lying flat (in the XZ plane, the bow toward -X), so they lie right on the ground; the GUI view looks
down on them steeply.
"""
import math
import os
import random

from PIL import Image, ImageDraw

import gen_hub_sigils as SIG
import gen_textures as T
from gen_hub_kit import ASSETS, COUNTS, LANG, S, bx, noise, rgb, save_tex, seed_of, tint, write_json

# tag -> (English level name, internal level id, display number); the sigil comes from gen_hub_sigils.LEVEL_SIGIL
LEVELS = [("l0", "Level 0", 0), ("l1", "Level 1", 1), ("l2", "Level 2", 2), ("l3", "Level 3", 3), ("l4", "Level 4", 4),
          ("l5", "Level 5", 5), ("l6", "Level 6", 6), ("l61", "Level 6.1", 6), ("l7", "Level 7", 7), ("l8", "Level 8", 8),
          ("l9", "Level 9", 9), ("l10", "Level 10", 10), ("l11", "Level 11", 11), ("l37", "Level 37", 12),
          ("l94", "Level 94", 13), ("run", "Level !", 14), ("fun", "Level Fun", 15), ("end", "The End", 16),
          ("l3999", "Level 3999", 19)]

TEXTURES = {}


def tex(name, img):
    save_tex(img, name, folder="item")
    TEXTURES[name] = img


def sigil_on(base, n, ink, light=None, margin=3):
    """A bow texture: the material, with the sigil engraved (ink) over it, and a fine rim."""
    img = base.copy()
    size = S - 2 * margin
    mask = SIG.draw(n, size)
    px, m = img.load(), mask.load()
    for y in range(size):
        for x in range(size):
            a = m[x, y] / 255
            if a > 0.05:
                r, g, b, al = px[x + margin, y + margin]
                px[x + margin, y + margin] = (T.clamp(r * (1 - a) + ink[0] * a), T.clamp(g * (1 - a) + ink[1] * a),
                                              T.clamp(b * (1 - a) + ink[2] * a), al)
    if light:
        d = ImageDraw.Draw(img)
        d.ellipse([1, 1, S - 2, S - 2], outline=light)
    return img


def materials():
    brass = noise(0xC8A050, 7, "kbrass")
    tex("brass", brass)
    tex("nickel", noise(0xC4C8CC, 5, "knickel"))
    tex("steel", noise(0x9AA0A6, 5, "ksteel"))
    img = noise(0x7A4A2A, 12, "krust")
    T.blotch(img, (10, 10), 8, (150, 80, 40), 0.5, seed_of("krust2"))
    tex("rust", img)
    tex("blackiron", noise(0x26262A, 4, "kblack"))
    img = noise(0x8C6A3A, 8, "kbronze")
    T.blotch(img, (20, 12), 10, (70, 140, 120), 0.55, seed_of("kverd"))
    T.blotch(img, (6, 24), 7, (80, 150, 130), 0.5, seed_of("kverd2"))
    tex("bronze-green", img)
    tex("bronze", noise(0x9A7440, 7, "kbronze2"))
    tex("slate", noise(0x4A5058, 6, "kslate"))
    TEXTURES["ceramic"] = noise(0xF2F2EE, 2, "kceramic")  # only a bow's base, not saved
    tex("teal", noise(0x2AA4A6, 4, "kteal"))
    tex("redrubber", noise(0xB82820, 5, "kred"))
    tex("yellowplastic", noise(0xE8C020, 4, "kyellow"))
    TEXTURES["blackrubber"] = noise(0x202022, 3, "kblackrub")  # only a bow's base, not saved
    tex("tassel", noise(0xA81E2A, 10, "ktassel"))
    tex("cork", noise(0xB08A5A, 14, "kcork"))
    tex("barnacle", noise(0xD8D0C0, 16, "kbarn"))
    tex("twine", noise(0xB89A6A, 10, "ktwine"))
    tex("string", noise(0xD8CCB0, 6, "kstring"))
    tex("card", noise(0xF4F4F2, 2, "kcard"))
    tex("stripe", noise(0x1A1A1C, 2, "kstripe"))
    tex("clip", noise(0xB8BCC0, 4, "kclip"))
    tex("pinkplastic", noise(0xF07AB0, 4, "kpink"))
    TEXTURES["candyyellow"] = noise(0xFFD84A, 4, "kcandyy")  # only a bow's base, not saved
    tex("balloon", noise(0xE83040, 4, "kballoon"))
    tex("ribbon", noise(0xF4F0F8, 4, "kribbon"))
    tex("clay", noise(0xD86A3A, 10, "kclay"))
    tex("claypaint", noise(0x3A8AD8, 9, "kclayblue"))
    TEXTURES["neonmagenta"] = noise(0xFF3CD2, 3, "kneonmag")  # only a bow's base, not saved
    tex("chrome", noise(0xD8DCE2, 3, "kchrome"))
    tex("candyblue", noise(0x5AB4F0, 4, "kcandyb"))
    # A yellowed paper tag with a scribble on it
    img = noise(0xE8DCA8, 4, "ktag")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("ktagscribble"))
    for y in (10, 15, 20):
        pts = [(4 + x * 3, y + rng.randint(-1, 1)) for x in range(8)]
        d.line(pts, fill=(60, 50, 90, 255))
    tex("papertag", img)
    # The fire brigade tag: IN EMERGENCY
    img = noise(0xD02018, 4, "kfiretag")
    T.text_img(img, "IN", (2, 4, 30, 14), (255, 255, 255, 255), 8)
    T.text_img(img, "EMERGENCY", (0, 16, 32, 26), (255, 255, 255, 255), 6)
    tex("firetag", img)
    # A brass room-number fob and the apartment key's plastic fob
    img = noise(0xC8A050, 7, "kfob")
    T.text_img(img, "217", (4, 8, 28, 24), (70, 50, 20, 255), 12)
    tex("fob5", img)
    img = noise(0x2A5AA8, 4, "kfob11")
    T.text_img(img, "11", (4, 6, 28, 26), (240, 240, 240, 255), 14)
    tex("fob11", img)
    img = noise(0x2A6AD8, 4, "khouse")
    tex("housetag", img)
    img = noise(0x8A5A3A, 5, "kbook")
    d = ImageDraw.Draw(img)
    d.line([0, 4, S, 4], fill=rgb(0xD4AF37))
    d.line([0, 27, S, 27], fill=rgb(0xD4AF37))
    tex("bookcover", img)


def bows():
    """Each key's bow texture: its material with the sigil worked into it."""
    spec = {"l0": ("brass", (110, 80, 30)), "l1": ("yellowplastic", (60, 50, 20)), "l2": ("rust", (40, 22, 12)),
            "l3": ("redrubber", (60, 10, 8)), "l4": ("card", (40, 60, 120)), "l5": ("brass", (90, 60, 20)),
            "l6": ("blackiron", (70, 70, 76)), "l61": ("pinkplastic", (120, 30, 70)), "l7": ("bronze-green", (40, 30, 15)),
            "l8": ("slate", (140, 150, 160)), "l9": ("nickel", (70, 74, 80)), "l10": ("rust", (30, 18, 10)),
            "l11": ("blackrubber", (150, 150, 150)), "l37": ("ceramic", (40, 150, 150)), "l94": ("claypaint", (250, 230, 120)),
            "run": ("brass", (150, 20, 15)), "fun": ("candyyellow", (240, 60, 140)), "end": ("bookcover", (212, 175, 55)),
            "l3999": ("neonmagenta", (40, 10, 60))}
    for tag, (mat, ink) in spec.items():
        tex(f"bow-{tag}", sigil_on(TEXTURES[mat], SIG.LEVEL_SIGIL[tag], ink))


# ---------------- Shapes ----------------
# Keys lie flat: x along the key (bow at small x), z across it, y up (thickness). Centred near (8, 8, 8).

Y0 = 7.5  # the underside of the key


def flat(nm, x1, z1, x2, z2, t, h=1.0, y=Y0, faces=None, rot=None, origin=None, full=False):
    kw = {"aligned": False}
    if faces:
        kw["faces"] = faces
    if full:
        kw["full"] = True
    return bx(nm, (x1, y, z1), (x2, y + h, z2), t, rot=rot, origin=origin, **kw)


BOW_MATERIAL = {"bow-l0": "brass", "bow-l5": "brass", "bow-l7": "bronze-green", "bow-l8": "slate", "bow-l9": "nickel",
                "bow-l10": "rust", "bow-l94": "claypaint", "bow-run": "brass"}


def bow_disc(nm, cx, cz, r, t, h=1.0, y=Y0):
    """A round bow: an octagon of the key's metal (four slabs turned 0, 45, 90, 135 degrees, their tops a hair apart so
    they never fight), with the sigil on a medallion inset on both faces."""
    mat = BOW_MATERIAL[t]
    a = r * math.tan(math.pi / 8)
    els = []
    for i, ang in enumerate((0, 45, 90, 135)):
        dy = 0.004 * i
        e = bx(f"{nm}{i}", (cx - r, y + dy, cz - a), (cx + r, y + h - dy, cz + a), mat, aligned=False,
               rot=(0, ang, 0) if ang else None, origin=(cx, y, cz))
        els.append(e)
    m = r * 0.7
    els.append(bx(nm + "Face", (cx - m, y + h, cz - m), (cx + m, y + h + 0.1, cz + m), t, aligned=False, full=True,
                  faces=("up", "north", "south", "east", "west")))
    els.append(bx(nm + "Back", (cx - m, y - 0.1, cz - m), (cx + m, y, cz + m), t, aligned=False, full=True, faces=("down",)))
    return els


def teeth(x1, x2, z, t, depth=1.2, step=1.2, seed=1, y=Y0, h=1.0, sign=1):
    """A row of key teeth along one edge of the blade (sign +1 toward +z)."""
    rng = random.Random(seed)
    out = []
    x = x1
    k = 0
    while x < x2 - 0.1:
        d = depth * rng.choice([0.4, 0.7, 1.0])
        z1, z2 = (z, z + d) if sign > 0 else (z - d, z)
        out.append(flat(f"Tooth{k}", x, z1, min(x2, x + step * 0.8), z2, t, h=h, y=y))
        x += step
        k += 1
    return out


def ring(nm, cx, cz, r, t, w=0.5, h=0.6, y=Y0 + 0.2):
    return [flat(nm + "N", cx - r, cz - r, cx + r, cz - r + w, t, h, y), flat(nm + "S", cx - r, cz + r - w, cx + r, cz + r, t, h, y),
            flat(nm + "W", cx - r, cz - r + w, cx - r + w, cz + r - w, t, h, y), flat(nm + "E", cx + r - w, cz - r + w, cx + r, cz + r - w, t, h, y)]


def key_l0():
    # A brass Yale key, a yellowed paper tag on a string
    bow = bow_disc("Bow", 4.5, 8, 2.6, "bow-l0")
    return bow + [flat("Shoulder", 6.8, 7.2, 7.6, 9.2, "brass"), flat("Blade", 7.6, 7.4, 13.6, 8.8, "brass"),
                  flat("Tip", 13.6, 7.6, 14.2, 8.6, "brass")] + teeth(8, 13.4, 8.8, "brass", 0.9, 1.1, 3) + \
        [flat("String", 1.0, 7.8, 2.4, 8.2, "string", 0.3, Y0 + 0.35), flat("Tag", -2.2, 6.4, 1.0, 10.2, "papertag", 0.25, Y0 + 0.4, full=True)]


def key_l1():
    # A stamped steel maintenance key with a yellow plastic head
    return [flat("Head", 1.8, 6, 6.6, 10, "bow-l1", 1.6, Y0 - 0.3, full=True), flat("HeadNeck", 6.6, 6.8, 7.4, 9.2, "yellowplastic", 1.2, Y0 - 0.1),
            flat("Blade", 7.4, 7.3, 13.8, 8.7, "steel"), flat("Tip", 13.8, 7.5, 14.4, 8.5, "steel"),
            flat("Hole", 2.6, 7.6, 3.4, 8.4, "stripe", 0.1, Y0 + 1.3, faces=("up",))] + teeth(8, 13.4, 7.3, "steel", 0.8, 1.0, 11, sign=-1)


def key_l2():
    # A rusted iron T-handle valve key: a crossbar, a long shank, a square socket
    return [flat("Handle", 1.4, 4.2, 3.2, 11.8, "rust", 1.6, Y0 - 0.3), flat("Boss", 2.6, 6.6, 5.6, 9.4, "bow-l2", 1.4, Y0 - 0.2, full=True),
            flat("Shank", 5.6, 7.4, 12.6, 8.6, "rust", 1.2, Y0 - 0.1), flat("Socket", 12.6, 6.8, 14.8, 9.2, "rust", 1.8, Y0 - 0.4),
            flat("SocketHole", 13.6, 7.4, 14.81, 8.6, "blackiron", 1.0, Y0 - 0.0, faces=("east",))]


def key_l3():
    # An electrical cabinet key: a red rubber grip, a triangular socket on the end
    return [flat("Grip", 1.6, 5.6, 6.4, 10.4, "bow-l3", 1.8, Y0 - 0.4, full=True), flat("GripRidge", 1.2, 6.4, 1.6, 9.6, "redrubber", 1.4, Y0 - 0.2),
            flat("Shank", 6.4, 7.3, 12, 8.7, "steel", 1.4, Y0 - 0.2),
            flat("Tri1", 12, 6.8, 14.6, 9.2, "steel", 1.0, Y0 - 0.0),
            flat("Tri2", 12, 7.0, 14.6, 9.0, "steel", 1.6, Y0 - 0.3, rot=(0, 0, 0)),
            flat("TriPoint", 12.4, 7.6, 14.6, 8.4, "steel", 2.2, Y0 - 0.6)]


def key_l4():
    # An office key card on a clip: Object 2's key that isn't a key
    return [flat("Card", 3, 4.6, 13.6, 11.4, "bow-l4", 0.3, Y0 + 0.3, full=True),
            flat("Stripe", 3.2, 9.2, 13.4, 10.4, "stripe", 0.02, Y0 + 0.6, faces=("up",)),
            flat("Clip", 0.8, 7.2, 3.4, 8.8, "clip", 0.5, Y0 + 0.2), flat("ClipRing", -0.6, 6.8, 0.8, 9.2, "clip", 0.4, Y0 + 0.25)]


def key_l5():
    # An ornate hotel room key: a trefoil bow, a brass number fob on a ring, a red tassel
    bow = bow_disc("Bow", 5, 8, 2.4, "bow-l5")
    lobes = [flat("LobeN", 4.0, 4.9, 6.0, 6.0, "brass"), flat("LobeS", 4.0, 10.0, 6.0, 11.1, "brass"), flat("LobeW", 2.0, 7.0, 2.9, 9.0, "brass")]
    return bow + lobes + [flat("Collar", 7.2, 7.1, 8.0, 8.9, "brass"), flat("Shank", 8.0, 7.5, 14.0, 8.5, "brass"),
                          flat("Bit", 12.6, 8.5, 14.0, 10.6, "brass"), flat("BitNotch", 13.0, 10.6, 13.6, 11.0, "brass"),
                          flat("Ring", 0.6, 7.6, 2.0, 8.4, "brass", 0.4, Y0 + 0.3),
                          flat("Fob", -3.4, 5.6, 0.6, 10.4, "fob5", 0.6, Y0 + 0.2, full=True),
                          flat("TasselCord", -4.6, 7.7, -3.4, 8.3, "tassel", 0.4, Y0 + 0.3),
                          flat("Tassel", -7.0, 6.8, -4.6, 9.2, "tassel", 1.0, Y0)]


def key_l6():
    # A long matte black skeleton key, hard to see
    return ring("Bow", 3.4, 8, 2.4, "blackiron", 0.9, 0.9, Y0) + \
        [flat("BowPlate", 2.0, 6.6, 4.8, 9.4, "bow-l6", 0.5, Y0 + 0.2, full=True),
         flat("Collar", 5.8, 7.2, 6.6, 8.8, "blackiron"), flat("Shank", 6.6, 7.6, 14.2, 8.4, "blackiron"),
         flat("Bit", 12.4, 8.4, 14.2, 10.8, "blackiron"), flat("BitWard", 13.0, 9.4, 13.6, 10.8, "blackiron", 1.02, Y0 - 0.01)]


def key_l61():
    # A vending machine's tubular key: a round barrel, a candy-pink plastic head
    return [flat("Head", 1.6, 5.4, 6.8, 10.6, "bow-l61", 1.6, Y0 - 0.3, full=True),
            flat("Barrel", 6.8, 7.0, 12.8, 9.0, "nickel", 2.0, Y0 - 0.5), flat("BarrelB", 6.8, 7.3, 12.8, 8.7, "nickel", 2.4, Y0 - 0.7),
            flat("Pin", 12.8, 7.6, 13.4, 8.4, "nickel", 1.0, Y0)]


def key_l7():
    # A corroded bronze key, barnacles on it, tied to a cork float
    els = bow_disc("Bow", 6, 8, 2.4, "bow-l7") + [flat("Shank", 8.2, 7.4, 14.2, 8.6, "bronze-green"),
                                                   flat("Bit", 12.6, 8.6, 14.2, 10.4, "bronze-green")]
    rng = random.Random(77)
    for k in range(5):
        x, z = rng.uniform(8.5, 13.5), rng.choice([7.2, 8.4])
        els.append(flat(f"Barnacle{k}", x, z, x + 0.7, z + 0.6, "barnacle", 0.6, Y0 + 0.9))
    els += [flat("Cord", 1.6, 7.8, 3.8, 8.2, "twine", 0.3, Y0 + 0.4),
            flat("Cork", -2.6, 6.2, 1.6, 9.8, "cork", 3.0, Y0 - 1.0), flat("CorkB", -2.2, 5.8, 1.2, 10.2, "cork", 2.4, Y0 - 0.7)]
    return els


def key_l8():
    # A key carved of slate: thick, rough, its teeth knapped
    return bow_disc("Bow", 4.6, 8, 3.0, "bow-l8", h=1.6, y=Y0 - 0.3) + \
        [flat("Shank", 7.4, 7.0, 13.6, 9.0, "slate", 1.6, Y0 - 0.3)] + teeth(9, 13.6, 9.0, "slate", 1.4, 1.5, 8, y=Y0 - 0.3, h=1.6)


def key_l9():
    # A house key on a split ring, with a little plastic house tag
    return bow_disc("Bow", 6.2, 8, 2.2, "bow-l9") + [flat("Blade", 8.2, 7.4, 14.0, 8.7, "nickel")] + \
        teeth(8.6, 13.8, 8.7, "nickel", 0.9, 1.0, 9) + ring("Ring", 2.6, 8, 1.8, "steel") + \
        [flat("House", -3.0, 6.2, 0.8, 9.8, "housetag", 0.8, Y0 + 0.1),
         flat("Roof", -2.6, 6.2, -0.4, 9.8, "housetag", 0.8, Y0 + 0.1, rot=(0, 45, 0), origin=(-1.1, Y0, 8)),
         flat("Window", -1.6, 7.4, -0.6, 8.6, "yellowplastic", 0.05, Y0 + 0.9, faces=("up",))]


def key_l10():
    # An old barn padlock key on a loop of twine
    return bow_disc("Bow", 6.6, 8, 2.0, "bow-l10") + [flat("Shank", 8.4, 7.5, 13.0, 8.5, "rust"),
                                                       flat("Bit", 11.8, 8.5, 13.0, 9.8, "rust")] + \
        ring("Twine", 1.6, 8, 3.0, "twine", 0.6, 0.5, Y0 + 0.3)


def key_l11():
    # A city apartment key: a black rubber head, nickel blade, a numbered fob
    return [flat("Head", 3.0, 6.0, 7.4, 10.0, "bow-l11", 1.4, Y0 - 0.2, full=True), flat("Blade", 7.4, 7.3, 13.8, 8.7, "nickel"),
            flat("Tip", 13.8, 7.5, 14.4, 8.5, "nickel")] + teeth(7.8, 13.4, 8.7, "nickel", 0.9, 0.9, 12) + \
        ring("Ring", 1.6, 8, 1.4, "steel") + [flat("Fob", -3.8, 6.4, 0.2, 9.6, "fob11", 0.6, Y0 + 0.2, full=True)]


def key_l37():
    # A white ceramic locker key on a coiled teal wristband
    els = [flat("Head", 3.6, 6.0, 7.6, 10.0, "bow-l37", 1.4, Y0 - 0.2, full=True), flat("Blade", 7.6, 7.4, 12.6, 8.6, "steel"),
           flat("Bit", 11.2, 8.6, 12.6, 9.8, "steel")]
    for k in range(10):  # the coil: a ring of short segments, tipped alternately
        a = 2 * math.pi * k / 10
        cx, cz = 0.4 + 3.2 * math.cos(a), 8 + 3.2 * math.sin(a)
        els.append(bx(f"Coil{k}", (cx - 0.5, Y0 + (0.2 if k % 2 else 0), cz - 1.1), (cx + 0.5, Y0 + 0.8 + (0.2 if k % 2 else 0), cz + 1.1),
                      "teal", aligned=False, rot=(0, -math.degrees(a), 0), origin=(cx, Y0, cz)))
    return els


def key_l94():
    # A painted clay wind-up key: two round lobes, a stubby stem, thumbprints in the clay
    return bow_disc("LobeA", 4.6, 5.0, 2.6, "bow-l94", h=1.4, y=Y0 - 0.2) + bow_disc("LobeB", 4.6, 11.0, 2.6, "bow-l94", h=1.4, y=Y0 - 0.2) + \
        [flat("Hub", 3.6, 6.8, 7.0, 9.2, "clay", 1.6, Y0 - 0.3), flat("Stem", 7.0, 7.3, 12.4, 8.7, "clay", 1.4, Y0 - 0.2),
         flat("Square", 12.4, 7.0, 13.8, 9.0, "clay", 1.8, Y0 - 0.4)]


def key_run():
    # A fire-brigade key: brass, a red tag that says IN EMERGENCY
    return bow_disc("Bow", 5.4, 8, 2.4, "bow-run") + [flat("Shank", 7.6, 7.4, 13.8, 8.6, "brass"), flat("Bit", 12.2, 8.6, 13.8, 10.6, "brass"),
                                                       flat("BitStep", 12.8, 10.6, 13.8, 11.2, "brass")] + \
        ring("Ring", 1.8, 8, 1.4, "steel") + [flat("Tag", -4.6, 6.0, 0.4, 10.0, "firetag", 0.5, Y0 + 0.25, full=True)]


def key_fun():
    # A chunky candy-coloured plastic toy key, a balloon on a ribbon
    return [flat("Head", 3.0, 5.0, 8.0, 11.0, "bow-fun", 1.8, Y0 - 0.4, full=True),
            flat("Shank", 8.0, 7.0, 13.4, 9.0, "candyblue", 1.4, Y0 - 0.2), flat("ToothA", 10.0, 9.0, 11.2, 10.4, "candyblue", 1.4, Y0 - 0.2),
            flat("ToothB", 12.0, 9.0, 13.4, 10.8, "pinkplastic", 1.4, Y0 - 0.2),
            flat("Ribbon", -1.0, 7.8, 3.0, 8.2, "ribbon", 0.2, Y0 + 0.4),
            flat("Balloon", -5.4, 6.0, -1.4, 10.0, "balloon", 3.4, Y0 - 1.2), flat("BalloonB", -5.0, 5.6, -1.8, 10.4, "balloon", 2.6, Y0 - 0.8),
            flat("BalloonKnot", -1.4, 7.6, -0.8, 8.4, "balloon", 0.8, Y0)]


def key_end():
    # A bronze library key whose bow is a closed book
    return [flat("Cover", 1.6, 5.4, 7.0, 10.6, "bow-end", 0.4, Y0 + 0.9, full=True), flat("Pages", 1.9, 5.7, 6.7, 10.3, "card", 0.9, Y0),
            flat("CoverB", 1.6, 5.4, 7.0, 10.6, "bookcover", 0.4, Y0 - 0.4), flat("Spine", 1.2, 5.4, 1.6, 10.6, "bookcover", 1.7, Y0 - 0.4),
            flat("Collar", 7.0, 7.2, 7.8, 8.8, "bronze"), flat("Shank", 7.8, 7.5, 14.0, 8.5, "bronze"),
            flat("Bit", 12.4, 8.5, 14.0, 10.4, "bronze"), flat("BitWard", 12.9, 9.4, 13.5, 10.4, "bronze", 1.02, Y0 - 0.01)]


def key_l3999():
    # A chrome room key off the key board in a lobby of the Neon Paradise, on a glowing magenta acrylic keychain
    return [flat("Head", 3.6, 6.0, 7.2, 10.0, "chrome", 1.0), flat("Shank", 7.2, 7.5, 13.8, 8.5, "chrome"),
            flat("BitA", 10.4, 8.5, 11.4, 9.8, "chrome"), flat("BitB", 12.2, 8.5, 13.8, 10.2, "chrome")] +         ring("Ring", 2.6, 8, 1.2, "steel") + [flat("Fob", -4.8, 5.4, 1.2, 10.6, "bow-l3999", 0.6, Y0 + 0.2, full=True)]


BUILD = {"l0": key_l0, "l1": key_l1, "l2": key_l2, "l3": key_l3, "l4": key_l4, "l5": key_l5, "l6": key_l6, "l61": key_l61,
         "l7": key_l7, "l8": key_l8, "l9": key_l9, "l10": key_l10, "l11": key_l11, "l37": key_l37, "l94": key_l94,
         "run": key_run, "fun": key_fun, "end": key_end, "l3999": key_l3999}


def key_shape(tag, els):
    keys = set()
    for e in els:
        for f in e["faces"].values():
            keys.add(f["texture"][1:])
    data = {"textureWidth": 16, "textureHeight": 16, "textures": {k: f"backrooms:item/hub/{k}" for k in sorted(keys)}, "elements": els}
    write_json(os.path.join(ASSETS, "shapes", "item", "hub", f"key-{tag}.json"), data)
    COUNTS["shapes"] += 1
    return f"item/hub/key-{tag}"


def generate():
    materials()
    bows()
    shapes = {tag: key_shape(tag, BUILD[tag]()) for tag, _, _ in LEVELS}
    data = {
        "code": "hub-key",
        "variantgroups": [{"code": "level", "states": [t for t, _, _ in LEVELS]}],
        "maxstacksize": 1,
        "shapeByType": {f"*-{t}": {"base": p} for t, p in shapes.items()},
        "creativeinventory": {"general": ["*"], "items": ["*"]},
        "materialDensity": 4000,
        "attributesByType": {f"*-{t}": {"hubKey": {"level": lvl, "tag": t, "sigil": SIG.LEVEL_SIGIL[t], "sub": "6.1" if t == "l61" else None},
                                        "handbook": {"groupBy": ["hub-key-*"]}}
                             for t, _, lvl in LEVELS},
        "guiTransform": {"rotation": {"x": -62, "y": -35, "z": 0}, "origin": {"x": 0.5, "y": 0.5, "z": 0.5}, "scale": 1.7},
        "fpHandTransform": {"translation": {"x": 0, "y": 0.2, "z": 0.3}, "rotation": {"x": 60, "y": 20, "z": 0}, "scale": 1.6},
        "tpHandTransform": {"translation": {"x": -0.8, "y": -0.45, "z": -0.6}, "rotation": {"x": 0, "y": -45, "z": -10}, "scale": 0.55},
        "groundTransform": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation": {"x": 0, "y": 0, "z": 0},
                            "origin": {"x": 0.5, "y": 0.45, "z": 0.5}, "scale": 2.4},
    }
    write_json(os.path.join(ASSETS, "itemtypes", "hub", "key.json"), data,
               "The Level Keys: backrooms:hub-key-<tag>, one per level the Hub has a door to. attributes.hubKey: level (internal"
               " id), tag, sigil (the door's, gen_hub_sigils.py), sub (6.1 for the Snackrooms)")
    for tag, english, _ in LEVELS:
        LANG[f"item-hub-key-{tag}"] = f"Level Key ({english})"
    LANG["itemdesc-hub-key-*"] = "Found only in its own level. Struck, it hums faintly. In the Hub it opens that level's door, once."
