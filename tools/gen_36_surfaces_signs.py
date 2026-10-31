"""Level 36, "Airport" (experimental): the textures of its signs and screens: the hanging wayfinding boxes (gate letters
and numbers, pictogram signs), the flight information displays, the shop fascias and the station clocks. Called from
gen_36_surfaces.py. Text-bearing faces are drawn larger than the world's 32 px a block (signs 8 px a shape unit, the
screens 6, the fascias and clocks 64 px a block), large shapes drawn four times over and shrunk so edges stay clean.

Lettering: the wayfinding signs use Bahnschrift (a DIN, the airport face) bold; the fascias each their own face. If a
font is missing the next in its list is used, ending at PIL's built-in font, so the script runs anywhere. All brands
are invented.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import matlib as M
from gen_3999_kit import F5
from gen_36_surfaces_tex import S, from_array, panel_img, save, seed_of, shrink, to_array

FONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")

CHARCOAL = (40, 42, 47)
YELLOW = (255, 200, 20)
K = 4  # supersampling for drawn shapes


# ======================================================================== Fonts

def font(names, size, variation=None):
    for n in names:
        for path in (os.path.join(FONTS, n), n):
            try:
                f = ImageFont.truetype(path, size)
                if variation:
                    try:
                        f.set_variation_by_name(variation)
                    except Exception:
                        pass
                return f
            except OSError:
                continue
    return ImageFont.load_default(size=size)


DIN = (["bahnschrift.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"], b"Bold")
DIN_COND = (["bahnschrift.ttf", "ARIALNB.TTF", "arialbd.ttf"], b"Bold Condensed")
DIN_SEMI = (["bahnschrift.ttf", "ARIALNB.TTF", "arialbd.ttf"], b"SemiBold SemiCondensed")


def text_mask(size, s, spec, box, max_px, align="centre", min_px=8, tracking=0):
    """An L mask (`size`, already supersampled) with `s` drawn as large as fits `box` (x0, y0, x1, y1), the cap
    height at most max_px; lines split on '\n'. Returns (mask, font size)."""
    names, var = spec
    lines = s.split("\n")
    x0, y0, x1, y1 = box
    px = max_px
    while px >= min_px:
        f = font(names, px, var)
        widths = [f.getlength(line) + tracking * max(0, len(line) - 1) for line in lines]
        asc, desc = f.getmetrics()
        cap = f.getbbox("H")[3] - f.getbbox("H")[1]
        lh = cap * 1.45
        th = cap + lh * (len(lines) - 1)
        if max(widths) <= x1 - x0 and th <= y1 - y0:
            break
        px -= 1
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    top = y0 + ((y1 - y0) - th) / 2
    for i, line in enumerate(lines):
        w = widths[i]
        x = x0 + ((x1 - x0) - w) / 2 if align == "centre" else (x0 if align == "left" else x1 - w)
        ytop = top + i * lh - f.getbbox("H")[1]
        if tracking:
            for ch in line:
                d.text((x, ytop), ch, font=f, fill=255)
                x += f.getlength(ch) + tracking
        else:
            d.text((x, ytop), line, font=f, fill=255)
    return m, px


def paint(img, mask, colour):
    """Paints `colour` through an L mask onto img (same size)."""
    layer = Image.new("RGBA", img.size, tuple(colour[:3]) + (255,))
    img.paste(layer, (0, 0), mask)
    return img


# ======================================================================== Pictograms (drawn into an L mask, a box)

def _poly(d, pts, box, fill=255):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d.polygon([(x0 + u * w, y0 + v * h) for u, v in pts], fill=fill)


def _line(d, pts, box, width, fill=255):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d.line([(x0 + u * w, y0 + v * h) for u, v in pts], fill=fill, width=int(width * w), joint="curve")
    for u, v in (pts[0], pts[-1]):
        r = width * w / 2
        d.ellipse((x0 + u * w - r, y0 + v * h - r, x0 + u * w + r, y0 + v * h + r), fill=fill)


def _disc(d, u, v, r, box, fill=255):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d.ellipse((x0 + (u - r) * w, y0 + (v - r) * h, x0 + (u + r) * w, y0 + (v + r) * h), fill=fill)


def _rrect(d, u0, v0, u1, v1, r, box, fill=255, outline=None, width=0):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d.rounded_rectangle((x0 + u0 * w, y0 + v0 * h, x0 + u1 * w, y0 + v1 * h), radius=r * w, fill=fill,
                        outline=outline, width=int(width * w) if width else 0)


def pict_plane(d, box, fill=255):
    """An airliner from above, nose up and a little to the right (the departures sign)."""
    x0, y0, x1, y1 = box
    cx, cy, w = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0)
    pts = [(0, -0.46), (0.045, -0.40), (0.05, -0.12), (0.44, 0.08), (0.44, 0.15), (0.05, 0.04), (0.04, 0.30),
           (0.17, 0.40), (0.17, 0.46), (0, 0.42)]
    pts = pts + [(-u, v) for u, v in reversed(pts[1:-1])]
    a = math.radians(35)
    rot = [(cx + (u * math.cos(a) - v * math.sin(a)) * w, cy + (u * math.sin(a) + v * math.cos(a)) * w) for u, v in pts]
    d.polygon(rot, fill=fill)


def pict_arrow(d, box, left, fill=255):
    pts = [(0.0, 0.5), (0.48, 0.08), (0.48, 0.32), (1.0, 0.32), (1.0, 0.68), (0.48, 0.68), (0.48, 0.92)]
    if not left:
        pts = [(1 - u, v) for u, v in pts]
    _poly(d, pts, box, fill)


def pict_suitcase(d, box, fill=255):
    _rrect(d, 0.12, 0.28, 0.88, 0.88, 0.08, box, fill)
    _rrect(d, 0.34, 0.10, 0.66, 0.32, 0.06, box, fill=None, outline=fill, width=0.07)
    _rrect(d, 0.22, 0.88, 0.32, 0.95, 0.02, box, fill)
    _rrect(d, 0.68, 0.88, 0.78, 0.95, 0.02, box, fill)


def _person(d, box, u, v, s, fill, dress=False):
    """A standing figure (as the toilet signs), centred at u, top at v, height s (box fractions)."""
    _disc(d, u, v + 0.09 * s, 0.085 * s, box, fill)
    if dress:
        _poly(d, [(u - 0.06 * s, v + 0.21 * s), (u + 0.06 * s, v + 0.21 * s), (u + 0.20 * s, v + 0.66 * s),
                  (u - 0.20 * s, v + 0.66 * s)], box, fill)
        _rrect(d, u - 0.10 * s, v + 0.62 * s, u - 0.03 * s, v + 1.0 * s, 0.02 * s, box, fill)
        _rrect(d, u + 0.03 * s, v + 0.62 * s, u + 0.10 * s, v + 1.0 * s, 0.02 * s, box, fill)
    else:
        _rrect(d, u - 0.13 * s, v + 0.21 * s, u + 0.13 * s, v + 0.60 * s, 0.05 * s, box, fill)
        _rrect(d, u - 0.12 * s, v + 0.55 * s, u - 0.015 * s, v + 1.0 * s, 0.02 * s, box, fill)
        _rrect(d, u + 0.015 * s, v + 0.55 * s, u + 0.12 * s, v + 1.0 * s, 0.02 * s, box, fill)
    _rrect(d, u - 0.21 * s, v + 0.22 * s, u - 0.15 * s, v + 0.56 * s, 0.03 * s, box, fill)
    _rrect(d, u + 0.15 * s, v + 0.22 * s, u + 0.21 * s, v + 0.56 * s, 0.03 * s, box, fill)


def pict_runner(d, box, fill=255):
    """The exit sign's running figure, heading left through a doorway."""
    _rrect(d, 0.62, 0.06, 0.94, 0.94, 0.0, box, fill=None, outline=fill, width=0.07)
    _disc(d, 0.40, 0.17, 0.085, box, fill)
    w = 0.10
    _line(d, [(0.44, 0.32), (0.34, 0.58)], box, w + 0.02, fill)          # torso, leaning
    _line(d, [(0.42, 0.36), (0.22, 0.42), (0.12, 0.34)], box, w, fill)   # front arm
    _line(d, [(0.42, 0.36), (0.56, 0.48), (0.66, 0.40)], box, w, fill)   # back arm
    _line(d, [(0.34, 0.58), (0.20, 0.70), (0.10, 0.90)], box, w, fill)   # front leg
    _line(d, [(0.34, 0.58), (0.48, 0.72), (0.58, 0.88)], box, w, fill)   # back leg


def pict_meeting(d, box, fill=255):
    """The meeting point: four arrows from the corners pointing at a dot."""
    _disc(d, 0.5, 0.5, 0.10, box, fill)
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        tip = (0.5 + sx * 0.17, 0.5 + sy * 0.17)
        tail = (0.5 + sx * 0.46, 0.5 + sy * 0.46)
        _line(d, [tail, (0.5 + sx * 0.28, 0.5 + sy * 0.28)], box, 0.09, fill)
        # the head: a triangle at the tip, pointing in
        nx, ny = -sx / math.sqrt(2), -sy / math.sqrt(2)
        px, py = -ny, nx
        base = (tip[0] - nx * 0.16, tip[1] - ny * 0.16)
        _poly(d, [tip, (base[0] + px * 0.11, base[1] + py * 0.11), (base[0] - px * 0.11, base[1] - py * 0.11)], box, fill)


def pict_bag(d, box, fill=255):
    """A shopping bag (duty free)."""
    _poly(d, [(0.18, 0.34), (0.82, 0.34), (0.88, 0.92), (0.12, 0.92)], box, fill)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    d.arc((x0 + 0.32 * w, y0 + 0.10 * h, x0 + 0.68 * w, y0 + 0.50 * h), 180, 360, fill=fill, width=int(0.07 * w))


def pict_food(d, box, fill=255):
    """Knife and fork."""
    # fork: tines, neck, handle
    for u in (0.24, 0.32, 0.40):
        _rrect(d, u - 0.025, 0.08, u + 0.025, 0.36, 0.02, box, fill)
    _rrect(d, 0.20, 0.30, 0.44, 0.42, 0.05, box, fill)
    _rrect(d, 0.28, 0.38, 0.36, 0.92, 0.03, box, fill)
    # knife: blade with a rounded back, handle
    _poly(d, [(0.62, 0.08), (0.72, 0.10), (0.75, 0.24), (0.72, 0.52), (0.62, 0.52)], box, fill)
    _rrect(d, 0.615, 0.48, 0.705, 0.92, 0.03, box, fill)


def pict_lounge(d, box, fill=255):
    """An armchair."""
    _rrect(d, 0.22, 0.14, 0.78, 0.60, 0.08, box, fill)    # back
    _rrect(d, 0.10, 0.40, 0.26, 0.80, 0.06, box, fill)    # arms
    _rrect(d, 0.74, 0.40, 0.90, 0.80, 0.06, box, fill)
    _rrect(d, 0.22, 0.56, 0.78, 0.76, 0.04, box, fill)    # seat
    _rrect(d, 0.14, 0.78, 0.20, 0.90, 0.01, box, fill)    # feet
    _rrect(d, 0.80, 0.78, 0.86, 0.90, 0.01, box, fill)


def pict_security(d, box, fill=255):
    """A walk-through scanner arch with a figure in it."""
    _rrect(d, 0.08, 0.06, 0.92, 0.18, 0.02, box, fill)
    _rrect(d, 0.08, 0.06, 0.22, 0.94, 0.02, box, fill)
    _rrect(d, 0.78, 0.06, 0.92, 0.94, 0.02, box, fill)
    _person(d, box, 0.5, 0.26, 0.68, fill)


def pict_checkin(d, box, fill=255):
    """A check-in desk: an agent behind a counter, a case on the scale."""
    _person(d, box, 0.36, 0.08, 0.62, fill)
    _rrect(d, 0.06, 0.56, 0.94, 0.94, 0.03, box, fill)
    _rrect(d, 0.64, 0.30, 0.90, 0.54, 0.03, box, fill)
    _rrect(d, 0.72, 0.24, 0.82, 0.31, 0.02, box, fill=None, outline=fill, width=0.03)


def pict_toilets(d, box, fill=255):
    _person(d, box, 0.26, 0.06, 0.88, fill)
    _person(d, box, 0.74, 0.06, 0.88, fill, dress=True)
    _rrect(d, 0.485, 0.04, 0.515, 0.96, 0.0, box, fill)


PICTS = {"plane": pict_plane, "suitcase": pict_suitcase, "runner": pict_runner, "meeting": pict_meeting,
         "bag": pict_bag, "food": pict_food, "lounge": pict_lounge, "security": pict_security,
         "checkin": pict_checkin, "toilets": pict_toilets}


# ======================================================================== The hanging box signs

SIGN_W, SIGN_H = 128, 80   # a sign face: 16 x 10 shape units at 8 px a unit


def sign_ground(lit=True, colour=CHARCOAL, seed=0):
    """The face of a backlit box sign: an even panel, a touch brighter mid-face where the tubes are, a thin
    aluminium rim."""
    img = M.noise_hv(colour, 2, seed or seed_of("signface"), (SIGN_W, SIGN_H), 3, (32, 16), hue=1.0)
    a = to_array(img)
    if lit:
        yy, xx = np.mgrid[0:SIGN_H, 0:SIGN_W]
        a[..., :3] += (6 * np.exp(-((yy - SIGN_H / 2) / (SIGN_H / 2.2)) ** 2))[..., None]
    a[0:2, :, :3] = np.array((120, 124, 130))
    a[-2:, :, :3] = np.array((86, 88, 94))
    a[:, 0:2, :3] = np.array((106, 110, 116))
    a[:, -2:, :3] = np.array((92, 96, 102))
    a[0, :, :3] += 30
    return from_array(a)


def finish_face(img, layer_rgba, glow=True):
    """Lays a supersampled RGBA drawing over a sign face; lit lettering gets a faint halo on the panel."""
    small = shrink(layer_rgba, img.size)
    if glow:
        halo = small.filter(ImageFilter.GaussianBlur(1.6))
        ha = np.asarray(halo).astype(float)
        ha[..., 3] *= 0.22
        img.alpha_composite(Image.fromarray(np.clip(ha, 0, 255).astype(np.uint8), "RGBA"))
    img.alpha_composite(small)
    return img


def layer_from(mask, colour):
    lay = Image.new("RGBA", mask.size, tuple(colour) + (0,))
    lay.putalpha(mask)
    return lay


def gatesign_face(glyph):
    img = sign_ground(seed=seed_of("gatesign-" + glyph))
    size = (SIGN_W * K, SIGN_H * K)
    m, _ = text_mask(size, glyph.upper(), DIN, (10 * K, 8 * K, (SIGN_W - 10) * K, (SIGN_H - 8) * K), 58 * K * 1.35,
                     min_px=10 * K)
    return save(finish_face(img, layer_from(m, YELLOW)), "l36-gatesign-" + glyph)


SIGNS = {
    # glyph: (pictogram, word, arrow) ; arrow "l"/"r" or None
    "gatesl": ("plane", "Gates", "l"), "gatesr": ("plane", "Gates", "r"), "baggage": ("suitcase", "Baggage", None),
    "meeting": ("meeting", "Meeting\nPoint", None), "dutyfree": ("bag", "Duty\nFree", None),
    "food": ("food", "Food", None), "lounge": ("lounge", "Lounge", None), "security": ("security", "Security", None),
    "checkin": ("checkin", "Check-in", None),
}


def tile_layer(size, box, pict, tile_col=YELLOW, ink=CHARCOAL):
    """A yellow rounded tile with the pictogram knocked out of it in charcoal, as RGBA."""
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=(x1 - x0) * 0.12, fill=tuple(tile_col) + (255,))
    m = Image.new("L", size, 0)
    pad = (x1 - x0) * 0.14
    PICTS[pict](ImageDraw.Draw(m), (x0 + pad, y0 + pad, x1 - pad, y1 - pad))
    ink_l = layer_from(m, ink)
    lay.alpha_composite(ink_l)
    return lay


def sign_face(glyph):
    size = (SIGN_W * K, SIGN_H * K)
    if glyph == "exit":
        GREEN = (0, 150, 74)
        img = sign_ground(colour=GREEN, seed=seed_of("exit"))
        m = Image.new("L", size, 0)
        pict_runner(ImageDraw.Draw(m), (8 * K, 12 * K, 62 * K, 68 * K))
        t, _ = text_mask(size, "EXIT", DIN, (64 * K, 14 * K, 122 * K, 66 * K), 34 * K * 1.35)
        m = Image.fromarray(np.maximum(np.asarray(m), np.asarray(t)))
        return save(finish_face(img, layer_from(m, (246, 250, 246))), "l36-sign-exit")
    if glyph == "toilets":
        img = sign_ground(seed=seed_of("toilets"))
        lay = tile_layer(size, (10 * K, 12 * K, 66 * K, 68 * K), "toilets")
        t, _ = text_mask(size, "Toilets", DIN_COND, (72 * K, 14 * K, 122 * K, 66 * K), 22 * K * 1.35)
        lay.alpha_composite(layer_from(t, YELLOW))
        return save(finish_face(img, lay), "l36-sign-toilets")
    if glyph == "blank":
        # Lit, and nothing on it: a slightly warmer, brighter panel, evenly backlit ("Empty sign = no good!")
        img = sign_ground(colour=(52, 54, 58), seed=seed_of("blank"))
        a = to_array(img)
        yy, xx = np.mgrid[0:SIGN_H, 0:SIGN_W]
        a[2:-2, 2:-2, :3] += (10 * np.exp(-(((xx - 64) / 70) ** 2 + ((yy - 40) / 34) ** 2)))[2:-2, 2:-2, None]
        return save(from_array(a), "l36-sign-blank")
    if glyph == "broken":
        return broken_face()
    pict, word, arrow = SIGNS[glyph]
    img = sign_ground(seed=seed_of("sign-" + glyph))
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    x = 8
    if arrow == "l":
        m = Image.new("L", size, 0)
        pict_arrow(ImageDraw.Draw(m), (x * K, 24 * K, (x + 26) * K, 56 * K), True)
        lay.alpha_composite(layer_from(m, YELLOW))
        x += 30
    tile = 44 if arrow else 52
    ty = (SIGN_H - tile) // 2
    lay.alpha_composite(tile_layer(size, (x * K, ty * K, (x + tile) * K, (ty + tile) * K), pict))
    x += tile + 5
    right = SIGN_W - 8 - (30 if arrow == "r" else 0)
    t, _ = text_mask(size, word, DIN_COND, (x * K, 12 * K, right * K, 68 * K), 24 * K * 1.35)
    lay.alpha_composite(layer_from(t, YELLOW))
    if arrow == "r":
        m = Image.new("L", size, 0)
        pict_arrow(ImageDraw.Draw(m), ((SIGN_W - 34) * K, 24 * K, (SIGN_W - 8) * K, 56 * K), False)
        lay.alpha_composite(layer_from(m, YELLOW))
    return save(finish_face(img, lay), "l36-sign-" + glyph)


def broken_face():
    """Cracked and dead: the gates sign unlit, its yellow gone dull, letters half missing, a crack across it."""
    size = (SIGN_W * K, SIGN_H * K)
    img = sign_ground(lit=False, colour=(34, 35, 38), seed=seed_of("broken"))
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    DULL = (122, 104, 44)
    lay.alpha_composite(tile_layer(size, (8 * K, 14 * K, 60 * K, 66 * K), "plane", tile_col=(118, 102, 50),
                                   ink=(34, 35, 38)))
    t, _ = text_mask(size, "Gates", DIN_COND, (66 * K, 12 * K, 122 * K, 68 * K), 24 * K * 1.35)
    lay.alpha_composite(layer_from(t, DULL))
    # letters and the tile half missing: the vinyl peeled off in patches
    rng = random.Random(seed_of("broken-peel-3"))
    er = ImageDraw.Draw(lay)
    for k in range(12):   # irregular flakes, most of them over the word
        if k < 8:
            cx, cy = rng.uniform(68, 120) * K, rng.uniform(26, 54) * K
        else:
            cx, cy = rng.uniform(10, 60) * K, rng.uniform(16, 62) * K
        r = rng.uniform(3, 8) * K
        pts = [(cx + math.cos(k / 7 * 2 * math.pi) * r * rng.uniform(0.5, 1.3),
                cy + math.sin(k / 7 * 2 * math.pi) * r * rng.uniform(0.4, 1.0)) for k in range(7)]
        er.polygon(pts, fill=(0, 0, 0, 0))
    out = finish_face(img, lay, glow=False)
    # the crack: a wandering line from the top edge down, lit on one side, with a branch
    p = out.load()
    rng = random.Random(seed_of("broken-crack"))
    for start, length in (((40, 2), 70), ((70, 30), 26)):
        x, y = start
        for _ in range(length):
            if 2 <= x < SIGN_W - 2 and 2 <= y < SIGN_H - 2:
                p[x, y] = (14, 14, 16, 255)
                p[x + 1, y] = M.rgba(M.lift(p[x + 1, y], 40))
            y += 1
            x += rng.choice((-1, 0, 0, 1, 1))
    # grime: the dead panel has dust on it
    M.grime(out, 0.25, seed_of("broken-grime"), color=(70, 66, 58), cells=(16, 8, 4))
    return save(out, "l36-sign-broken")


def sign_case():
    case = M.painted_metal(seed_of("signcase"), base=(44, 46, 50), grain=2, mottle=3, panel=False, chips=0)
    save(case, "l36-sign-case")
    rod = M.brushed_metal(seed_of("signrod"), base=(184, 188, 192), direction="v", streak=8, sheen=10)
    save(rod, "l36-sign-rod")


# ======================================================================== Flight information displays

FW, FH = 96, 72   # a half: 16 x 12 shape units at 6 px a unit; the pair is 192 x 72
AMBER = (255, 178, 46)
WHITE = (232, 234, 228)
STATUS = {"BOARDING": (90, 232, 120), "DELAYED": (255, 84, 56), "CLOSED": (150, 150, 150), "NOW BOARDING": (90, 232, 120)}
HEADBAR = (18, 30, 72)


def _led_text(a, s, x, y, col, scale=1):
    """Draws s in the 5x7 dot font into the float array a (H, W, 3); returns the x after it."""
    rows = []
    for r in range(7):
        line = ""
        for i, ch in enumerate(s.upper()):
            g = F5.get(ch, F5[" "])
            line += g[r] + ("0" if i < len(s) - 1 else "")
        rows.append(line)
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v == "1":
                for dy in range(scale):
                    for dx in range(scale):
                        X, Y = x + c * scale + dx, y + r * scale + dy
                        if 0 <= X < a.shape[1] and 0 <= Y < a.shape[0]:
                            a[Y, X] = col
    return x + len(rows[0]) * scale


def _led_width(s, scale=1):
    return (sum(len(F5.get(ch, F5[" "])[0]) for ch in s.upper()) + max(0, len(s) - 1)) * scale


def _screen_base(seed):
    W, H = FW * 2, FH
    a = np.zeros((H, W, 3))
    a[:] = (7, 8, 11)
    yy, xx = np.mgrid[0:H, 0:W]
    a[(yy % 2 == 1) | (xx % 2 == 1)] = (4, 5, 7)   # the LED matrix's dark grid
    return a


def _screen_finish(a, name):
    """Bloom on the lit dots, the bezel round the pair, then split into the l and r halves."""
    W, H = FW * 2, FH
    lit = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").filter(ImageFilter.GaussianBlur(1.2))
    a = np.maximum(a, np.asarray(lit).astype(float) * 0.55)
    a[0:3, :] = (26, 26, 28)
    a[-3:, :] = (22, 22, 24)
    a[:, 0:3] = (26, 26, 28)
    a[:, -3:] = (22, 22, 24)
    a[0, :] = (54, 56, 60)
    a[3, 3:-3] *= 0.6
    a[:, 3][3:-3] *= 0.6
    for half, (x0, x1) in (("l", (0, FW)), ("r", (FW, W))):
        save(from_array(a[:, x0:x1].copy()), f"l36-fids-{name}-{half}")


BOARDS = {
    "a": [("4471QK", "LV6", "C14", "1204"), ("88JQ0", "LV37", "A03", "48881"), ("7720AB", "LV0", "B07", "BOARDING"),
          ("13Q9X", "LV94", "E22", "DELAYED"), ("5502RT", "LV11", "D41", "73310")],
    "b": [("0021LP", "LV3999", "F09", "CLOSED"), ("61ZZ8", "LV188", "K17", "906"), ("39KQ1", "LV2", "A11", "26044"),
          ("8810MN", "LV974", "H05", "DELAYED"), ("4407CV", "LV8", "C29", "5517")],
    "c": [("2290WE", "LV1", "M02", "BOARDING"), ("75HJ3", "LV5", "G33", "88120"), ("1103XA", "LV9", "B51", "12"),
          ("660QQ", "LV3", "L46", "CLOSED"), ("9184PU", "LV7", "J08", "301877")],
    "d": [("3301DD", "LV4", "T12", "DELAYED"), ("48GK7", "LV0", "Q58", "999999"), ("7077LM", "LV37", "A01", "4410"),
          ("1919YO", "LV94", "Z60", "BOARDING"), ("2468EV", "LV11", "R26", "18806")],
}


def fids_board(name):
    a = _screen_base(seed_of("fids-" + name))
    W = FW * 2
    cols = (6, 54, 96, 126)   # x of FLIGHT, TO, GATE, COUNT
    a[5:16, 4:W - 4] = HEADBAR
    for x, h in zip(cols, ("FLIGHT", "TO", "GATE", "COUNT")):
        _led_text(a, h, x, 7, (255, 214, 60))
    for i, (fl, to, gate, count) in enumerate(BOARDS[name]):
        y = 20 + i * 10
        _led_text(a, fl, cols[0], y, AMBER)
        _led_text(a, to, cols[1], y, AMBER)
        _led_text(a, gate, cols[2], y, WHITE)
        _led_text(a, count, cols[3], y, STATUS.get(count, WHITE))
    _screen_finish(a, name)


def fids_gate():
    """The gate desk's screen: NOW BOARDING over a big gate code, the flight and its count beside it."""
    a = _screen_base(seed_of("fids-gate"))
    W = FW * 2
    a[5:17, 4:W - 4] = (14, 64, 34)
    s = "NOW BOARDING"
    _led_text(a, s, (W - _led_width(s)) // 2, 7, STATUS["NOW BOARDING"])
    # (round 2: every gate shows this board, so it names the flight and where it goes, not a gate code that would
    # contradict the sign over the holdroom; the gate line is left blank, as the lore's screens show only the flight)
    _led_text(a, "TO", 12, 22, WHITE)
    _led_text(a, "LV6", 10, 32, (255, 214, 60), scale=4)
    x0 = 104
    for i, (label, value, col) in enumerate((("FLIGHT", "4471QK", AMBER), ("GATE", "--", AMBER),
                                             ("COUNT", "0987", WHITE))):
        y = 24 + i * 14
        _led_text(a, label, x0, y, (150, 156, 166))
        _led_text(a, value, x0 + 40, y, col)
    a[22:66, 94] = (40, 44, 52)
    _screen_finish(a, "gate")


def fids_c32():
    """Gate C32's board: the Support Group's flight, nine digits from boarding, delayed."""
    a = _screen_base(seed_of("fids-c32"))
    W = FW * 2
    a[5:16, 4:W - 4] = HEADBAR
    s = "GATE C32  DEPARTURES"
    _led_text(a, s, (W - _led_width(s)) // 2, 7, (255, 214, 60))
    rows = (("FLIGHT", "1784XBA8JLP", AMBER), ("TO", "LV186", AMBER), ("GATE", "C32", WHITE),
            ("COUNT", "94612753", WHITE), ("STATUS", "DELAYED", STATUS["DELAYED"]))
    for i, (label, value, col) in enumerate(rows):
        y = 20 + i * 10
        _led_text(a, label, 22, y, (150, 156, 166))
        _led_text(a, value, 78, y, col)
    _screen_finish(a, "c32")


def fids_misc():
    bez = M.painted_metal(seed_of("fidsbezel"), base=(26, 26, 28), grain=2, mottle=2, panel=False, chips=0)
    save(bez, "l36-fids-bezel")
    pole = M.brushed_metal(seed_of("fidspole"), base=(186, 190, 194), direction="v", streak=8, sheen=10)
    save(pole, "l36-fidspole")


# ======================================================================== Shop fascias

FASCIA = {
    # shop: (name, background, letter colour, fonts, variation, accent)
    "perfume": ("MAISON VEAU", (22, 20, 26), (216, 182, 112), ["BOD_R.TTF", "georgia.ttf", "times.ttf"], None, None),
    "fashion": ("LOSTWEAR", (240, 240, 238), (24, 24, 26), ["GILSANUB.TTF", "bahnschrift.ttf", "arialbd.ttf"], b"Bold", (214, 40, 46)),
    "books": ("PAGE & GATE", (24, 72, 54), (240, 230, 204), ["georgiab.ttf", "georgia.ttf", "times.ttf"], None, None),
    "snacks": ("SNAX TO GO", (238, 118, 22), (255, 252, 240), ["FRAHV.TTF", "impact.ttf", "arialbd.ttf"], None, (250, 214, 40)),
    "tech": ("VOLTA", (14, 18, 32), (80, 220, 250), ["ERASBD.TTF", "bahnschrift.ttf", "arialbd.ttf"], b"Bold", (80, 220, 250)),
    "bags": ("CARRY-ON CO.", (146, 96, 56), (250, 236, 210), ["ROCKB.TTF", "georgiab.ttf", "arialbd.ttf"], None, None),
    "cafe": ("TERMINAL BREW", (58, 36, 26), (238, 220, 190), ["GIL_____.TTF", "bahnschrift.ttf", "arial.ttf"], b"SemiBold", (196, 140, 80)),
    "pharma": ("PHARMACY +", (244, 246, 244), (20, 140, 70), ["bahnschrift.ttf", "arialbd.ttf"], b"Bold", (20, 160, 80)),
}
FASCIA_LIGHT = {"perfume": [8, 3, 5], "fashion": [0, 1, 5], "books": [22, 3, 5], "snacks": [5, 4, 5], "tech": [34, 3, 5],
                "bags": [6, 3, 5], "cafe": [5, 3, 5], "pharma": [21, 3, 5]}


def fascia(shop):
    name, bg, ink, names, var, accent = FASCIA[shop]
    W, H = 64 * 3, 64
    img = M.noise_hv(bg, 2, seed_of("fascia-" + shop), (W, H), 3, (32, 16), hue=1.0)
    a = to_array(img)
    yy, xx = np.mgrid[0:H, 0:W]
    a[..., :3] += (7 * np.exp(-((yy - 32) / 22.0) ** 2))[..., None]   # the backlight, strongest mid-height
    img = from_array(a)
    size = (W * K, H * K)
    lay = Image.new("RGBA", size, (0, 0, 0, 0))
    left = 14
    d = ImageDraw.Draw(lay)
    if shop == "pharma":   # the green cross
        m = Image.new("L", size, 0)
        dm = ImageDraw.Draw(m)
        dm.rectangle((19 * K, 18 * K, 27 * K, 46 * K), fill=255)
        dm.rectangle((9 * K, 28 * K, 37 * K, 36 * K), fill=255)
        lay = layer_from(m, accent)
        left = 42
    if shop == "cafe":     # a cup with steam
        m = Image.new("L", size, 0)
        dm = ImageDraw.Draw(m)
        dm.rounded_rectangle((12 * K, 28 * K, 30 * K, 46 * K), radius=4 * K, fill=255)
        dm.arc((26 * K, 31 * K, 36 * K, 41 * K), 270, 90, fill=255, width=3 * K)
        for sx in (17, 24):
            dm.arc((sx * K, 15 * K, (sx + 5) * K, 22 * K), 90, 270, fill=255, width=2 * K)
            dm.arc((sx * K, 20 * K, (sx + 5) * K, 27 * K), 270, 90, fill=255, width=2 * K)
        lay.alpha_composite(layer_from(m, accent))
        left = 42
    if shop == "tech":     # a lightning bolt
        m = Image.new("L", size, 0)
        ImageDraw.Draw(m).polygon([(c[0] * K, c[1] * K) for c in ((28, 12), (14, 35), (23, 35), (18, 52), (36, 27),
                                                                   (26, 27), (31, 12))], fill=255)
        lay.alpha_composite(layer_from(m, accent))
        left = 44
    right = W - 14
    tracking = {"perfume": 5 * K, "tech": 6 * K}.get(shop, 0)
    t, _ = text_mask(size, name, (names, var), (left * K, 14 * K, right * K, 50 * K), 30 * K * 1.4, tracking=tracking)
    lay.alpha_composite(layer_from(t, ink))
    if shop == "fashion":   # a red rule under the name
        tb = Image.fromarray(np.asarray(t)).getbbox()
        if tb:
            d2 = ImageDraw.Draw(lay)
            d2.rectangle((tb[0], tb[3] + 3 * K, tb[2], tb[3] + 5 * K), fill=accent + (255,))
    if shop == "snacks":    # a yellow swoosh under it
        d2 = ImageDraw.Draw(lay)
        d2.arc((30 * K, 30 * K, (W - 30) * K, 62 * K), 20, 160, fill=accent + (255,), width=3 * K)
    if shop == "perfume":   # hairline gold rules above and below
        d2 = ImageDraw.Draw(lay)
        for y in (15, 49):
            d2.rectangle((40 * K, y * K, (W - 40) * K, y * K + K // 2 + 1), fill=ink + (255,))
    small = shrink(lay, (W, H))
    halo = small.filter(ImageFilter.GaussianBlur(1.5))
    ha = np.asarray(halo).astype(float)
    ha[..., 3] *= 0.25
    img.alpha_composite(Image.fromarray(np.clip(ha, 0, 255).astype(np.uint8), "RGBA"))
    img.alpha_composite(small)
    # The aluminium frame: top and bottom bands, end caps on the outer ends
    a = to_array(img)
    frame = np.array((150, 154, 160))
    a[0:5, :, :3] = frame
    a[0, :, :3] = frame + 40
    a[4, :, :3] = frame - 50
    a[H - 5:H, :, :3] = frame - 14
    a[H - 5, :, :3] = frame - 60
    a[H - 1, :, :3] = frame - 40
    a[:, 0:4, :3] = frame
    a[:, 3, :3] -= 50
    a[:, 0, :3] += 30
    a[:, W - 4:W, :3] = frame - 10
    a[:, W - 4, :3] -= 50
    for part, x0 in (("l", 0), ("m", 64), ("r", 128)):
        save(from_array(a[:, x0:x0 + 64].copy()), f"l36-shopsign-{shop}-{part}")


# ======================================================================== Station clocks

def clock(kind):
    """A round station clock on the panel wall: white dial, black bars; nohands has none; stopped is frozen at 3:47
    with a hairline crack across the glass."""
    W = 64
    bg = panel_img(seed_of("clockpanel"), size=S).resize((W, W), Image.NEAREST)
    Kc = 6
    big = Image.new("RGBA", (W * Kc, W * Kc), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = W * Kc / 2
    cy = c - 1 * Kc
    R = 25 * Kc
    d.ellipse((c - R + 1.5 * Kc, cy - R + 3 * Kc, c + R + 1.5 * Kc, cy + R + 3 * Kc), fill=(0, 0, 0, 70))   # shadow
    d.ellipse((c - R, cy - R, c + R, cy + R), fill=(70, 74, 80, 255))   # the case
    d.ellipse((c - R + 1 * Kc, cy - R + 1 * Kc, c + R - 1 * Kc, cy + R - 1 * Kc), fill=(150, 154, 160, 255))
    r = R - 3 * Kc
    d.ellipse((c - r, cy - r, c + r, cy + r), fill=(246, 246, 242, 255))
    for k in range(60):
        ang = k / 60 * 2 * math.pi
        long = k % 5 == 0
        r0, r1 = (r - 6 * Kc, r - 1.2 * Kc) if long else (r - 2.4 * Kc, r - 1.2 * Kc)
        w = 2.2 * Kc if long else 0.6 * Kc
        sx, sy = math.sin(ang), -math.cos(ang)
        d.line((c + sx * r0, cy + sy * r0, c + sx * r1, cy + sy * r1), fill=(20, 20, 22, 255), width=int(w))
    if kind == "stopped":
        def hand(angle_deg, length, width, back, col):
            a_ = math.radians(angle_deg)
            sx, sy = math.sin(a_), -math.cos(a_)
            nx, ny = -sy, sx
            pts = [(c - sx * back + nx * width / 2, cy - sy * back + ny * width / 2),
                   (c + sx * length + nx * width * 0.4, cy + sy * length + ny * width * 0.4),
                   (c + sx * length - nx * width * 0.4, cy + sy * length - ny * width * 0.4),
                   (c - sx * back - nx * width / 2, cy - sy * back - ny * width / 2)]
            d.polygon(pts, fill=col)
        hand((3 + 47 / 60) * 30, r * 0.55, 3.2 * Kc, 3 * Kc, (18, 18, 20, 255))
        hand(47 * 6, r * 0.86, 2.4 * Kc, 4 * Kc, (18, 18, 20, 255))
        hand(12 * 6, r * 0.70, 0.7 * Kc, 6 * Kc, (200, 30, 30, 255))   # the red seconds hand, stopped too
        a_ = math.radians(72)
        d.ellipse((c + math.sin(a_) * r * 0.62 - 2.2 * Kc, cy - math.cos(a_) * r * 0.62 - 2.2 * Kc,
                   c + math.sin(a_) * r * 0.62 + 2.2 * Kc, cy - math.cos(a_) * r * 0.62 + 2.2 * Kc), fill=(200, 30, 30, 255))
        d.ellipse((c - 1.6 * Kc, cy - 1.6 * Kc, c + 1.6 * Kc, cy + 1.6 * Kc), fill=(18, 18, 20, 255))
    else:
        d.ellipse((c - 1 * Kc, cy - 1 * Kc, c + 1 * Kc, cy + 1 * Kc), fill=(60, 60, 64, 255))   # just the bare spindle
    # the glass: a soft highlight top-left
    hl = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((c - r * 0.8, cy - r * 0.85, c - r * 0.05, cy - r * 0.35), fill=(255, 255, 255, 34))
    big.alpha_composite(hl)
    small = shrink(big, (W, W))
    bg.alpha_composite(small)
    if kind == "stopped":   # the hairline crack, across the glass from the upper right
        p = bg.load()
        rng = random.Random(seed_of("clockcrack"))
        x, y = 46.0, 12.0
        for _ in range(30):
            xi, yi = int(x), int(y)
            if (xi - 32) ** 2 + (yi - 31) ** 2 < 21 ** 2:
                p[xi, yi] = M.rgba(M.lift(p[xi, yi], -70))
                p[xi + 1, yi] = M.rgba(M.lift(p[xi + 1, yi], 30))
            x -= 0.75 + rng.uniform(-0.4, 0.4)
            y += 0.8 + rng.uniform(-0.3, 0.5)
        x, y = 39.0, 19.0
        for _ in range(9):
            xi, yi = int(x), int(y)
            p[xi, yi] = M.rgba(M.lift(p[xi, yi], -55))
            x += 0.9
            y += 0.6 + rng.uniform(-0.3, 0.3)
    return save(bg, "l36-wallclock-" + kind)


GATE_GLYPHS = [chr(c) for c in range(ord("a"), ord("z") + 1)] + [str(n) for n in range(1, 61)]
SIGN_GLYPHS = ["gatesl", "gatesr", "baggage", "exit", "meeting", "dutyfree", "food", "lounge", "toilets", "security",
               "checkin", "blank", "broken"]
FIDS_TEXTS = ["a", "b", "c", "d", "gate", "c32"]
SHOPS = ["perfume", "fashion", "books", "snacks", "tech", "bags", "cafe", "pharma"]


def generate():
    sign_case()
    for g in GATE_GLYPHS:
        gatesign_face(g)
    for g in SIGN_GLYPHS:
        sign_face(g)
    fids_misc()
    for t in "abcd":
        fids_board(t)
    fids_gate()
    fids_c32()
    for s in SHOPS:
        fascia(s)
    for k in ("nohands", "stopped"):
        clock(k)
