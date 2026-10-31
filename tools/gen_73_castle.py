"""Level 73, "The Redlands": the Silver Castle's furnishings, called from gen_73.py (run that, under the asset lock).

The lore (Wikidot's Level 73): "Red velvet curtains in front of every window ... the windows behind them are completely
boarded with wooden planks"; banners of "a silver heart with ram's horns on a black field" on the walls; "numerous paintings
of locations in The Frontrooms, but none of them lead outside"; "glasses of potable water and portions of food for each
human ... appear on the silverware at the grand mahogany table at regular intervals"; two bathrooms with "large,
infinitely-refilling barrels ... warm water"; a door that keeps everything out until you "bang on the door as loud as
possible"; and an attic CORAN "has declared off-limits".

Writes, under blocktypes/73, shapes/block/73 and textures/block/73:
  l73-slate                    the attic's slate roof (cube)
  l73-curtain-{top,mid,low}-*  red velvet curtains in front of a boarded window, a pelmet with a gold fringe over them
  l73-banner-*                 the heart-and-horns banner, two blocks long, hung from the top one on an iron rod
  l73-painting-{1..6}-*        a gilt frame round a painting of the Frontrooms (a house at dusk, a street at night, a barn
                               in a wheat field, a pier at sunset, a lake under mountains, a diner's neon)
  l73-door-{shut,open}-{lb,rb,lm,rm,lt,rt}  the keep's door, two studded oak leaves three high (class BackroomsL73Door)
  l73-atticdoor-{lb,rb,lt,rt}  the attic's doors, chained and padlocked (the same class, locked)
  l73-table-{set,bare}-*       the mahogany table, a place set (stew, bread, a glass of water) or cleared (BackroomsL73Table)
  l73-bath                     a barrel of warm water, steaming (BackroomsL73Bath)
Every one of them is attribute l73Fixed (they never break: the castle is "impenetrable and invincible").
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

import matlib as M

SIDES = ["north", "east", "south", "west"]
ROT = {"north": 0, "east": 270, "south": 180, "west": 90}


# ---------------- Textures ----------------

def slate(seed):
    img = M.brick(seed=seed, base=(58, 60, 70), mortar=(22, 22, 28), course=8, length=8, offset=0.5, mortar_w=1, jitter=8, hue=3,
                  recess=1.0, pits=0.02, chamfer=False, grain=3, mottle=6)
    # Each row of slates overlaps the one below: darker at its lower edge, a lit lip at the top
    px = img.load()
    for y in range(32):
        k = (y % 8) / 7.0
        for x in range(32):
            M.touch(img, x, y, 0.1 - 0.22 * k)
    M.grime(img, 0.12, seed=seed + 3, color=(30, 34, 30), cover=0.35)
    return img


def velvet(seed, base=(118, 12, 22)):
    """Crimson velvet hanging in vertical folds: lit ridges, deep troughs, a soft nap."""
    img = Image.new("RGBA", (32, 32))
    px = img.load()
    rng = random.Random(seed)
    noise = M.fbm(32, seed, (8, 4))
    for x in range(32):
        ph = math.sin(2 * math.pi * x / 8.0 + 0.4 * math.sin(x * 0.7))
        for y in range(32):
            k = 0.72 + 0.3 * ph + 0.06 * noise[y][x] + rng.uniform(-0.03, 0.03)
            px[x, y] = M.rgba((base[0] * k * 1.08, base[1] * k, base[2] * k))
    return img


def gold(seed):
    img = M.noise_hv((176, 136, 52), amp=8, seed=seed, mottle=8, hue=2)
    px = img.load()
    for y in range(32):
        for x in range(32):
            if (x + y) % 4 == 0:
                M.touch(img, x, y, 0.18)
            elif (x + 2 * y) % 7 == 0:
                M.touch(img, x, y, -0.2)
    return img


def iron(seed):
    img = M.noise_hv((34, 32, 34), amp=3, seed=seed, mottle=5, hue=1)
    M.rust(img, 0.1, seed=seed + 1)
    return img


def heart_horns(draw, cx, top, scale, fill, outline=None):
    """The emblem: a heart, and a ram's horn curling out and down from each of its lobes. Drawn four times as large on a
    layer of its own and scaled down onto the image, so its curves come out smooth."""
    img = draw._image
    k = 4
    r = scale * 0.5 * k
    w, h = img.size
    layer = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0, y0 = cx * k, top * k
    # The horns: thick arcs round a centre beside each lobe, from the lobe up and out, down, and curling back in
    for side in (-1, 1):
        sx, sy = x0 + side * 2.35 * r, y0 + 1.3 * r
        pts = []
        for i in range(60):
            t = i / 59.0
            a = math.radians(150 - 430 * t)
            rad = r * (1.25 - 0.95 * t)
            pts.append((sx + side * rad * math.cos(a), sy - rad * math.sin(a)))
        for i in range(len(pts) - 1):
            wid = max(2, int(r * (0.36 - 0.2 * i / len(pts))))
            d.line([pts[i], pts[i + 1]], fill=fill, width=wid)
            d.ellipse([pts[i][0] - wid / 2, pts[i][1] - wid / 2, pts[i][0] + wid / 2, pts[i][1] + wid / 2], fill=fill)
    # The heart
    for side in (-1, 1):
        lx = x0 + side * 0.9 * r
        d.ellipse([lx - r, y0, lx + r, y0 + 2 * r], fill=fill)
    d.polygon([(x0 - 1.85 * r, y0 + 1.25 * r), (x0 + 1.85 * r, y0 + 1.25 * r), (x0, y0 + 3.6 * r)], fill=fill)
    if outline:
        d.line([(x0, y0 + 0.6 * r), (x0, y0 + 2.6 * r)], fill=outline, width=k)
    small = layer.resize((w, h), Image.LANCZOS)
    px, sp = img.load(), small.load()
    for y in range(h):
        for x in range(w):
            a = sp[x, y][3] / 255.0
            if a > 0.15 and px[x, y][3] > 0:
                c = sp[x, y]
                base = px[x, y]
                t = min(1.0, a * 1.15)
                px[x, y] = (int(base[0] + (c[0] / max(a, 1e-3) - base[0]) * t), int(base[1] + (c[1] / max(a, 1e-3) - base[1]) * t),
                            int(base[2] + (c[2] / max(a, 1e-3) - base[2]) * t), base[3])


def banner_tex(seed):
    """32x64: the cloth at x 4-28, y 2-60, black with a silver border, the emblem in silver, a swallowtail hem."""
    img = Image.new("RGBA", (32, 64), (0, 0, 0, 0))
    rng = random.Random(seed)
    px = img.load()
    for y in range(2, 61):
        for x in range(4, 28):
            d = rng.uniform(-3, 3) + 4 * math.sin(x * 0.9) * 0.5
            px[x, y] = M.rgba((16 + d, 14 + d, 18 + d))
    # The swallowtail: a notch up the middle of the hem
    for y in range(52, 61):
        half = (y - 52) * 1.4
        for x in range(4, 28):
            if abs(x + 0.5 - 16) < half:
                px[x, y] = (0, 0, 0, 0)
    d = ImageDraw.Draw(img)
    silver, shade = (206, 208, 216, 255), (120, 122, 132, 255)
    # A silver border just inside the edge
    d.line([(5, 4), (26, 4)], fill=silver)
    d.line([(5, 4), (5, 50)], fill=silver)
    d.line([(26, 4), (26, 50)], fill=silver)
    heart_horns(d, 16, 10, 5.0, silver, outline=shade)
    # Under the emblem, three small silver studs, and the rod's loops at the top (dark)
    for x in (12, 16, 20):
        d.point((x, 42), fill=silver)
    for x in (6, 11, 16, 21, 25):
        d.line([(x, 2), (x + 1, 2)], fill=(40, 40, 44, 255))
    return img


def plate_tex(seed):
    img = M.noise_hv((232, 230, 224), amp=3, seed=seed, mottle=3, hue=1)
    d = ImageDraw.Draw(img)
    d.ellipse([3, 3, 28, 28], outline=(196, 160, 72, 255), width=1)  # the gold rim line
    return img


def stew_tex(seed):
    img = M.noise_hv((110, 46, 30), amp=6, seed=seed, mottle=9, hue=4)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(40):
        x, y = rng.randrange(32), rng.randrange(32)
        c = rng.choice([(150, 60, 36), (176, 120, 60), (70, 110, 46), (196, 150, 90)])
        for dx in range(2):
            for dy in range(2):
                px[(x + dx) % 32, (y + dy) % 32] = M.rgba(c)
    return img


def bread_tex(seed):
    img = M.noise_hv((176, 122, 62), amp=6, seed=seed, mottle=7, hue=3)
    M.grime(img, 0.1, seed=seed + 1, color=(120, 70, 30), cover=0.5)
    return img


def water_glass_tex(seed, full=True):
    img = Image.new("RGBA", (32, 32))
    px = img.load()
    for y in range(32):
        for x in range(32):
            if full and y >= 8:
                c = (150, 196, 214)
            else:
                c = (210, 226, 232)
            edge = x < 3 or x > 28
            k = 0.85 if edge else 1.0
            px[x, y] = M.rgba((c[0] * k, c[1] * k, c[2] * k))
    for y in range(32):
        px[6, y] = M.rgba((246, 250, 252))
    return img


def silver_tex(seed):
    return M.brushed_metal(seed=seed, base=(196, 198, 204), direction="h", streak=6, sheen=14)


def mahogany(seed):
    return M.wood_planks(seed=seed, base=(96, 38, 26), planks=2, direction="h", grain=4, contrast=1.1, per_plank=6, gap=(40, 16, 12))


def mahogany_end(seed):
    return M.noise_hv((80, 32, 22), amp=4, seed=seed, mottle=6, hue=2)


def oak(seed):
    return M.wood_planks(seed=seed, base=(70, 48, 30), planks=4, direction="v", grain=4, contrast=1.0, per_plank=8, gap=(26, 18, 12))


def staves(seed):
    img = M.wood_planks(seed=seed, base=(92, 64, 40), planks=5, direction="v", grain=4, contrast=1.0, per_plank=10, gap=(34, 24, 16))
    M.grime(img, 0.12, seed=seed + 1, color=(50, 40, 30), cover=0.4)
    return img


def warm_water(seed):
    img = M.noise_hv((92, 128, 138), amp=5, seed=seed, mottle=8, hue=2)
    rng = random.Random(seed)
    px = img.load()
    for _ in range(30):  # glints and wisps of steam on the surface
        x, y = rng.randrange(32), rng.randrange(32)
        px[x, y] = M.rgba(M.mix(px[x, y], (226, 232, 230), 0.6))
    return img


def door_outer(seed):
    """64x96: the keep's door seen from outside, both leaves (32 wide each) three blocks high."""
    w, h = 64, 96
    img = Image.new("RGBA", (w, h))
    base = M.wood_planks(seed=seed, size=64, base=(64, 40, 26), planks=8, direction="v", grain=4, contrast=1.1, per_plank=8,
                         gap=(22, 14, 10))
    base2 = M.wood_planks(seed=seed + 1, size=64, base=(64, 40, 26), planks=8, direction="v", grain=4, contrast=1.1, per_plank=8,
                          gap=(22, 14, 10))
    img.paste(base, (0, 0))
    img.paste(base2.crop((0, 0, 64, 32)), (0, 64))
    d = ImageDraw.Draw(img)
    strap, stud, dark = (30, 28, 30, 255), (150, 146, 140, 255), (12, 10, 10, 255)
    for y in (10, 46, 84):
        d.rectangle([2, y, 61, y + 3], fill=strap)
        for x in range(4, 62, 6):
            d.point((x, y + 1), fill=stud)
    # The meeting of the leaves, a dark seam down the middle; the frame's edge
    d.line([(31, 0), (31, 95)], fill=dark)
    d.line([(32, 0), (32, 95)], fill=(40, 26, 18, 255))
    d.rectangle([0, 0, 63, 95], outline=(26, 18, 12, 255))
    # Ring handles either side of the seam, at hand height (the middle block)
    for cx in (26, 37):
        d.ellipse([cx - 3, 54, cx + 3, 62], outline=(170, 168, 160, 255), width=1)
        d.rectangle([cx - 1, 52, cx + 1, 54], fill=strap)
    # The emblem in silver across the top of both leaves
    heart_horns(d, 32, 12, 8.0, (196, 198, 206, 255), outline=(110, 112, 120, 255))
    # Battered: dents and scratches where things have clawed at it
    rng = random.Random(seed + 7)
    px = img.load()
    for _ in range(26):
        x0, y0 = rng.randrange(4, 60), rng.randrange(40, 94)
        for i in range(rng.randrange(3, 8)):
            x, y = x0 + i, y0 + i // 2
            if 0 <= x < w and 0 <= y < h:
                r, g, b, a = px[x, y]
                px[x, y] = (min(255, r + 40), min(255, g + 30), min(255, b + 20), a)
    return img


def door_inner(seed):
    img = Image.new("RGBA", (64, 96))
    base = M.wood_planks(seed=seed, size=64, base=(78, 52, 34), planks=8, direction="v", grain=4, per_plank=8, gap=(26, 18, 12))
    img.paste(base, (0, 0))
    img.paste(base.crop((0, 0, 64, 32)), (0, 64))
    d = ImageDraw.Draw(img)
    brace = (58, 38, 24, 255)
    for y in (8, 46, 84):
        d.rectangle([2, y, 61, y + 4], fill=brace)
    d.line([(31, 0), (31, 95)], fill=(20, 14, 10, 255))
    # The great bar's brackets either side of the seam
    for x in (22, 38):
        d.rectangle([x, 50, x + 3, 58], fill=(36, 34, 36, 255))
    return img


def attic_door(seed):
    """64x64: two plain leaves, a heavy chain across them, a padlock at the seam."""
    img = M.wood_planks(seed=seed, size=64, base=(58, 42, 30), planks=8, direction="v", grain=4, per_plank=8, gap=(20, 14, 10))
    M.grime(img, 0.18, seed=seed + 1, color=(40, 34, 28), cover=0.5)
    d = ImageDraw.Draw(img)
    d.line([(31, 0), (31, 63)], fill=(14, 10, 8, 255))
    d.rectangle([0, 0, 63, 63], outline=(26, 18, 12, 255))
    # The chain: links of gold-brass and iron, sagging across at hand height
    for i in range(16):
        x = 2 + i * 4
        y = 30 + int(4 * math.sin(math.pi * i / 15))
        col = (118, 112, 104, 255) if i % 2 else (88, 84, 80, 255)
        if i % 2:
            d.ellipse([x, y - 2, x + 5, y + 2], outline=col, width=1)
        else:
            d.line([(x, y), (x + 5, y)], fill=col, width=2)
    d.rectangle([28, 34, 35, 42], fill=(60, 56, 50, 255))
    d.arc([29, 29, 34, 37], 180, 360, fill=(110, 106, 100, 255), width=1)
    d.point((31, 38), fill=(10, 8, 8, 255))
    return img


# ---- The paintings of the Frontrooms (48x28, painterly) ----

def _sky(img, top, bottom, h=None):
    w, hh = img.size
    h = h or hh
    px = img.load()
    for y in range(h):
        c = M.mix(top, bottom, y / max(1, h - 1))
        for x in range(w):
            px[x, y] = M.rgba(c)


def _painterly(img, seed):
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    out = img.copy()
    po = out.load()
    for y in range(h):
        for x in range(w):
            dx, dy = rng.choice([(0, 0), (1, 0), (-1, 0), (0, 1)])
            sx, sy = min(w - 1, max(0, x + dx)), min(h - 1, max(0, y + dy))
            r, g, b, a = px[sx, sy]
            j = rng.uniform(-6, 6)
            po[x, y] = M.rgba((r + j, g + j, b + j))
    return out


def painting(kind, seed):
    img = Image.new("RGBA", (48, 28))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    if kind == 0:  # A suburban house at dusk, one window lit
        _sky(img, (40, 46, 92), (214, 120, 84), 20)
        d.rectangle([0, 20, 47, 27], fill=(46, 70, 40, 255))
        d.rectangle([14, 11, 32, 21], fill=(170, 160, 140, 255))
        d.polygon([(11, 12), (23, 4), (35, 12)], fill=(90, 50, 44, 255))
        d.rectangle([17, 14, 20, 17], fill=(250, 210, 120, 255))
        d.rectangle([26, 14, 29, 17], fill=(60, 70, 90, 255))
        d.rectangle([22, 16, 24, 21], fill=(90, 60, 40, 255))
        d.ellipse([36, 9, 46, 21], fill=(30, 54, 34, 255))
        d.rectangle([40, 19, 41, 22], fill=(60, 44, 30, 255))
    elif kind == 1:  # A city street at night, lamps and lit windows
        _sky(img, (14, 16, 34), (54, 46, 70), 28)
        for bx, bw, bh in ((0, 10, 20), (11, 8, 14), (20, 12, 22), (33, 6, 12), (40, 8, 18)):
            d.rectangle([bx, 28 - bh, bx + bw, 27], fill=(30, 30, 38, 255))
            for wy in range(28 - bh + 2, 24, 3):
                for wx in range(bx + 1, bx + bw - 1, 3):
                    if rng.random() < 0.45:
                        d.point((wx, wy), fill=(240, 200, 110, 255))
        d.rectangle([0, 24, 47, 27], fill=(40, 40, 44, 255))
        for lx in (8, 26, 42):
            d.line([(lx, 15), (lx, 24)], fill=(20, 20, 20, 255))
            d.ellipse([lx - 2, 13, lx + 2, 16], fill=(255, 226, 150, 255))
    elif kind == 2:  # A red barn in a field of wheat under a summer sky
        _sky(img, (90, 150, 214), (200, 220, 236), 16)
        d.rectangle([0, 16, 47, 27], fill=(214, 182, 90, 255))
        for x in range(0, 48, 2):
            d.line([(x, 16 + (x * 7) % 3), (x, 27)], fill=(196, 160, 70, 255))
        d.rectangle([28, 8, 42, 18], fill=(150, 40, 32, 255))
        d.polygon([(26, 9), (35, 3), (44, 9)], fill=(110, 30, 26, 255))
        d.rectangle([33, 12, 37, 18], fill=(230, 226, 214, 255))
        d.ellipse([6, 4, 18, 8], fill=(246, 246, 250, 255))
    elif kind == 3:  # A pier on a beach at sunset
        _sky(img, (250, 150, 90), (250, 214, 140), 14)
        d.ellipse([18, 8, 28, 18], fill=(255, 236, 170, 255))
        d.rectangle([0, 14, 47, 21], fill=(60, 96, 140, 255))
        for y in range(15, 21, 2):
            d.line([(14, y), (32, y)], fill=(240, 180, 120, 255))
        d.rectangle([0, 21, 47, 27], fill=(214, 190, 150, 255))
        d.rectangle([30, 13, 47, 14], fill=(60, 40, 30, 255))
        for x in range(31, 48, 4):
            d.line([(x, 14), (x, 20)], fill=(50, 34, 26, 255))
    elif kind == 4:  # A lake under mountains, pines on the shore
        _sky(img, (120, 160, 210), (210, 226, 236), 16)
        d.polygon([(0, 16), (12, 4), (22, 14), (32, 2), (47, 16)], fill=(110, 120, 140, 255))
        d.polygon([(10, 6), (12, 4), (14, 6)], fill=(240, 244, 250, 255))
        d.polygon([(30, 4), (32, 2), (34, 4)], fill=(240, 244, 250, 255))
        d.rectangle([0, 16, 47, 27], fill=(70, 110, 140, 255))
        for x in (2, 6, 40, 44):
            d.polygon([(x, 22), (x + 2, 12), (x + 4, 22)], fill=(30, 60, 40, 255))
        d.rectangle([0, 24, 47, 27], fill=(70, 90, 50, 255))
    else:  # A roadside diner at night, its neon sign
        _sky(img, (16, 20, 40), (40, 40, 70), 28)
        d.rectangle([0, 22, 47, 27], fill=(36, 36, 40, 255))
        d.rectangle([8, 12, 40, 22], fill=(190, 196, 200, 255))
        d.rectangle([10, 15, 38, 19], fill=(250, 220, 150, 255))
        for x in range(12, 38, 4):
            d.line([(x, 15), (x, 19)], fill=(160, 150, 130, 255))
        d.rectangle([14, 6, 34, 10], fill=(40, 14, 30, 255))
        d.line([(16, 8), (32, 8)], fill=(255, 80, 150, 255), width=2)
        d.ellipse([41, 2, 45, 6], fill=(240, 240, 220, 255))
    img = _painterly(img, seed + 1)
    # Old varnish: a warm, slightly darkened cast
    px = img.load()
    for y in range(28):
        for x in range(48):
            r, g, b, a = px[x, y]
            px[x, y] = M.rgba((r * 0.88 + 12, g * 0.84 + 8, b * 0.74 + 4))
    return img


# ---------------- Shapes ----------------

def face(tex, uv, **kw):
    f = {"texture": tex, "uv": [round(v, 3) for v in uv]}
    f.update(kw)
    return f


def box(name, frm, to, tex, faces=None, uv=None, glow=0, **kw):
    """A box with every face mapped by position (as a 16-unit block), unless faces gives its own."""
    x1, y1, z1 = frm
    x2, y2, z2 = to
    auto = {
        "north": [16 - x2, 16 - y2, 16 - x1, 16 - y1], "south": [x1, 16 - y2, x2, 16 - y1],
        "east": [16 - z2, 16 - y2, 16 - z1, 16 - y1], "west": [z1, 16 - y2, z2, 16 - y1],
        "up": [x1, z1, x2, z2], "down": [x1, 16 - z2, x2, 16 - z1],
    }
    fs = {}
    for k, a in auto.items():
        if faces is not None and k not in faces:
            continue
        t = tex if not isinstance(tex, dict) else tex.get(k, tex.get("*"))
        u = (faces or {}).get(k) if isinstance(faces, dict) else None
        fs[k] = face(t, [max(0, min(16, v)) for v in (u or a)], **({"glow": glow} if glow else {}))
    e = {"name": name, "from": list(frm), "to": list(to), "faces": fs}
    e.update(kw)
    return e


def shape(textures, elements, tw=16, th=16):
    return {"textureWidth": tw, "textureHeight": th, "textures": textures, "elements": elements}


def curtain_shape(part):
    """A curtain against the wall to its back (south): four folds, the pelmet over the top piece, a gold hem on the low one."""
    tex = {"velvet": "backrooms:block/73/velvet", "gold": "backrooms:block/73/gold"}
    y0 = 1 if part == "low" else 0
    y1 = 8 if part == "top" else 16
    els = []
    for i in range(4):
        z0 = 12.4 if i % 2 == 0 else 13.4
        if part == "low" and i % 2 == 0:
            z0 = 11.8
        els.append(box(f"Fold{i}", [4 * i, y0, z0], [4 * i + 4, y1, 15.2], "#velvet"))
    if part == "top":
        els.append(box("Pelmet", [0, 8, 11.0], [16, 16, 16], "#velvet"))
        els.append(box("Fringe", [0, 7.2, 10.8], [16, 8.4, 16], "#gold"))
    if part == "low":
        els.append(box("Hem", [0, 1, 11.6], [16, 1.8, 15.3], "#gold"))
    return shape(tex, els)


def banner_shape():
    tex = {"cloth": "backrooms:block/73/banner", "iron": "backrooms:block/73/sconce-iron"}
    # The cloth, 12 wide and 28.5 long, hangs from the top of this block down through the one below it
    cloth_uv = [4 / 2, 2 / 2, 28 / 2, 60 / 2]  # in the 16x32 texture space
    els = [
        box("Rod", [0.5, 14.6, 13.3], [15.5, 15.6, 14.2], "#iron"),
        box("FinialL", [0, 14.2, 13.2], [1, 16, 15], "#iron"),
        box("FinialR", [15, 14.2, 13.2], [16, 16, 15], "#iron"),
        box("Bracket", [7.5, 15, 14.6], [8.5, 16, 16], "#iron"),
        {"name": "Cloth", "from": [2, -14.5, 14.3], "to": [14, 14.5, 14.8], "faces": {
            "north": face("#cloth", cloth_uv), "south": face("#cloth", [cloth_uv[2], cloth_uv[1], cloth_uv[0], cloth_uv[3]]),
        }},
    ]
    s = shape(tex, els, 16, 32)
    return s


def painting_shape(n):
    tex = {"canvas": f"backrooms:block/73/painting-{n}", "frame": "backrooms:block/73/gold"}
    canvas = {"name": "Canvas", "from": [2, 5, 15.2], "to": [14, 12, 15.9], "faces": {"north": face("#canvas", [0, 0, 16, 16])}}
    els = [
        canvas,
        box("FrameTop", [1, 12, 14.6], [15, 13, 16], "#frame"),
        box("FrameBottom", [1, 4, 14.6], [15, 5, 16], "#frame"),
        box("FrameLeft", [1, 5, 14.6], [2, 12, 16], "#frame"),
        box("FrameRight", [14, 5, 14.6], [15, 12, 16], "#frame"),
    ]
    return shape(tex, els)


DOOR_PARTS = ["lb", "rb", "lm", "rm", "lt", "rt"]


def door_shape(part, state, attic=False):
    """One cell of a door leaf. Shut: a leaf four thick in the middle of the wall. Open: swung in (north) against its
    jamb. The texture is the whole door (2 x 3 blocks, or 2 x 2 for the attic's), each cell taking its own part."""
    rows = 2 if attic else 3
    col = 0 if part[0] == "l" else 1
    row = {"b": 0, "m": 1, "t": rows - 1}[part[1]]
    tw, th = 32, 16 * rows
    u0, v0 = col * 16, (rows - 1 - row) * 16
    outer = [u0, v0, u0 + 16, v0 + 16]
    inner = [32 - u0 - 16, v0, 32 - u0, v0 + 16]
    texname = "atticdoor" if attic else "door"
    tex = {"out": f"backrooms:block/73/{texname}-out", "in": f"backrooms:block/73/{texname}-in", "edge": "backrooms:block/73/oak"}
    edge = [0, 0, 4, 16]
    if state == "shut":
        el = {"name": "Leaf", "from": [0, 0, 6], "to": [16, 16, 10], "faces": {
            "south": face("#out", outer), "north": face("#in", inner),
            "east": face("#edge", edge), "west": face("#edge", edge), "up": face("#edge", [0, 0, 16, 4]), "down": face("#edge", [0, 0, 16, 4])}}
    else:
        x0 = 0 if col == 0 else 12
        el = {"name": "Leaf", "from": [x0, 0, -10], "to": [x0 + 4, 16, 6], "faces": {
            ("west" if col == 0 else "east"): face("#out", outer), ("east" if col == 0 else "west"): face("#in", inner),
            "north": face("#edge", edge), "south": face("#edge", edge), "up": face("#edge", [0, 0, 4, 16]), "down": face("#edge", [0, 0, 4, 16])}}
    return {"textureWidth": tw, "textureHeight": th, "textures": tex, "elements": [el]}


def table_shape(state):
    """The mahogany table; the diner sits to the north (the model's front). Set: a plate of stew and bread, a fork and knife,
    a glass of water. Cleared: the plate and the glass, empty."""
    tex = {"wood": "backrooms:block/73/mahogany", "end": "backrooms:block/73/mahogany-end", "plate": "backrooms:block/73/plate",
           "stew": "backrooms:block/73/stew", "bread": "backrooms:block/73/bread", "glass": "backrooms:block/73/glass-full",
           "empty": "backrooms:block/73/glass-empty", "silver": "backrooms:block/73/silverware"}
    els = [
        box("Top", [0, 12.5, 0], [16, 14, 16], {"*": "#wood", "up": "#wood"}),
        box("Apron", [0.5, 10.5, 0.5], [15.5, 12.5, 15.5], "#end"),
        box("LegNW", [1, 0, 1], [2.5, 10.5, 2.5], "#end"),
        box("LegNE", [13.5, 0, 1], [15, 10.5, 2.5], "#end"),
        box("LegSW", [1, 0, 13.5], [2.5, 10.5, 15], "#end"),
        box("LegSE", [13.5, 0, 13.5], [15, 10.5, 15], "#end"),
        box("Plate", [4, 14, 2], [10.5, 14.4, 8.5], "#plate"),
        box("Glass", [12, 14, 2.5], [13.6, 17.6, 4.1], "#glass" if state == "set" else "#empty"),
    ]
    if state == "set":
        els += [
            box("Stew", [5, 14.4, 3], [9.5, 15.4, 7.5], "#stew"),
            box("Bread", [7.5, 14.4, 6.2], [10, 15.6, 8.2], "#bread"),
            box("Fork", [2.6, 14, 3], [3.2, 14.25, 8], "#silver"),
            box("Knife", [11, 14, 4.5], [11.6, 14.25, 9.5], "#silver"),
        ]
    return shape(tex, els)


def bath_shape():
    """A big barrel: four walls of staves (open at the top, so the water shows), two iron bands, the steaming water."""
    tex = {"staves": "backrooms:block/73/staves", "iron": "backrooms:block/73/sconce-iron", "water": "backrooms:block/73/warmwater",
           "end": "backrooms:block/73/mahogany-end"}
    sides = {"north": None, "south": None, "east": None, "west": None}
    els = [
        box("WallN", [1, 0, 1], [15, 14, 2], {"*": "#staves", "up": "#end", "down": "#end"}),
        box("WallS", [1, 0, 14], [15, 14, 15], {"*": "#staves", "up": "#end", "down": "#end"}),
        box("WallW", [1, 0, 2], [2, 14, 14], {"*": "#staves", "up": "#end", "down": "#end"}),
        box("WallE", [14, 0, 2], [15, 14, 14], {"*": "#staves", "up": "#end", "down": "#end"}),
        box("BandLow", [0.7, 2, 0.7], [15.3, 3, 15.3], "#iron", faces=sides),
        box("BandHigh", [0.7, 11, 0.7], [15.3, 12, 15.3], "#iron", faces=sides),
        box("Water", [2, 12.4, 2], [14, 12.8, 14], "#water", faces={"up": None}),
    ]
    return shape(tex, els)


# ---------------- Blocktypes ----------------

def fixed(b):
    b.setdefault("attributes", {})["l73Fixed"] = True
    b["resistance"] = 1000
    return b


def oriented(code, comment, shape_base, material, sel, coll=None, light=None, sounds=None, extra_variants=None, extra=None,
             shape_by=None, inv=None):
    groups = (extra_variants or []) + [{"code": "side", "states": SIDES}]
    b = {
        "code": code,
        "variantgroups": groups,
        "creativeinventory": {"general": [inv or "*-north"], "backrooms": [inv or "*-north"]},
        "blockmaterial": material,
        "drawtype": "json",
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "selectionboxByType": {f"*-{s}": dict(sel, rotateY=ROT[s]) for s in SIDES},
        "drops": [],
        "sounds": sounds or {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"},
    }
    if shape_by:
        b["shapeByType"] = shape_by
    else:
        b["shapeByType"] = {f"*-{s}": {"base": shape_base, "rotateY": ROT[s]} for s in SIDES}
    if coll is None:
        b["collisionbox"] = None
    else:
        b["collisionboxByType"] = {f"*-{s}": dict(coll, rotateY=ROT[s]) for s in SIDES}
    if light:
        b["lightHsv"] = light
    if extra:
        b.update(extra)
    return comment, fixed(b)


CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
WOOD = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}


def blocktypes():
    out = []
    out.append(("// Level 73: the attic's slate roof", fixed({
        "code": "l73-slate", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "textures": {"all": {"base": "block/73/slate", "alternates": [{"base": "block/73/slate-2"}]}}, "drops": [],
        "sounds": {"walk": "game:walk/stone*", "place": "game:block/rock-hit-pickaxe", "break": "game:block/rock-hit-pickaxe", "hit": "game:block/rock-hit-pickaxe"},
    })))
    out.append(("// Level 73: the planks the castle's windows are boarded up with (never broken: \"do not look outside\")", fixed({
        "code": "l73-boards", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Wood", "drawtype": "cube",
        "textures": {"all": {"base": "block/73/oak"}}, "drops": [], "sounds": WOOD,
    })))
    out.append(oriented(
        "l73-curtain", "// Level 73: red velvet curtains in front of a boarded window (the window behind it, south for -north); top has the pelmet",
        None, "Cloth", {"x1": 0, "y1": 0, "z1": 0.6875, "x2": 1, "y2": 1, "z2": 1}, sounds=CLOTH,
        extra_variants=[{"code": "part", "states": ["top", "mid", "low"]}],
        shape_by={f"*-{p}-{s}": {"base": f"block/73/curtain-{p}", "rotateY": ROT[s]} for p in ("top", "mid", "low") for s in SIDES},
        inv="*-mid-north"))
    out.append(oriented(
        "l73-banner", "// Level 73: the Silver Castle's banner, a silver heart with ram's horns on black, hung from this block down over the one below",
        "block/73/banner", "Cloth", {"x1": 0.0625, "y1": 0, "z1": 0.8125, "x2": 0.9375, "y2": 1, "z2": 1}, sounds=CLOTH,
        extra={"renderpass": "OpaqueNoCull"}))
    out.append(oriented(
        "l73-painting", "// Level 73: a gilt-framed painting of a place in the Frontrooms (\"none of them lead outside\")",
        None, "Wood", {"x1": 0.0625, "y1": 0.25, "z1": 0.9, "x2": 0.9375, "y2": 0.8125, "z2": 1}, sounds=WOOD,
        extra_variants=[{"code": "scene", "states": [str(i) for i in range(1, 7)]}],
        shape_by={f"*-{n}-{s}": {"base": f"block/73/painting-{n}", "rotateY": ROT[s]} for n in range(1, 7) for s in SIDES},
        inv="*-1-north"))
    door = fixed({
        "code": "l73-door",
        "class": "BackroomsL73Door",
        "variantgroups": [{"code": "state", "states": ["shut", "open"]}, {"code": "part", "states": DOOR_PARTS}],
        "creativeinventory": {"general": ["*-shut-lb"], "backrooms": ["*-shut-lb"]},
        "blockmaterial": "Wood",
        "drawtype": "json",
        "shapeByType": {f"*-{st}-{p}": {"base": f"block/73/door-{st}-{p}"} for st in ("shut", "open") for p in DOOR_PARTS},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 1,
        "collisionboxByType": {"*-open-*": None},
        "selectionboxByType": {"*-open-l*": {"x1": 0, "y1": 0, "z1": -0.625, "x2": 0.25, "y2": 1, "z2": 0.375},
                               "*-open-r*": {"x1": 0.75, "y1": 0, "z1": -0.625, "x2": 1, "y2": 1, "z2": 0.375},
                               "*-shut-*": {"x1": 0, "y1": 0, "z1": 0.375, "x2": 1, "y2": 1, "z2": 0.625}},
        "attributes": {"l73Door": "keep"},
        "drops": [],
        "sounds": {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    })
    out.append(("// Level 73: the keep's door, two studded oak leaves three high; it opens to banging from outside (Regions.L73System)", door))
    attic = fixed({
        "code": "l73-atticdoor",
        "class": "BackroomsL73Door",
        "variantgroups": [{"code": "part", "states": ["lb", "rb", "lt", "rt"]}],
        "creativeinventory": {"general": ["*-lb"], "backrooms": ["*-lb"]},
        "blockmaterial": "Wood",
        "drawtype": "json",
        "shapeByType": {f"*-{p}": {"base": f"block/73/atticdoor-{p}"} for p in ("lb", "rb", "lt", "rt")},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 1,
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0.375, "x2": 1, "y2": 1, "z2": 0.625},
        "attributes": {"l73Door": "attic"},
        "drops": [],
        "sounds": {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"},
    })
    out.append(("// Level 73: the attic's doors, chained and padlocked: CORAN has declared the attic off-limits", attic))
    out.append(oriented(
        "l73-table", "// Level 73: the grand mahogany table; a place set at it (the diner to the north for -north) refills by itself (Regions.L73System)",
        None, "Wood", {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.875, "z2": 1}, coll={"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.875, "z2": 1},
        sounds=WOOD, extra_variants=[{"code": "state", "states": ["set", "bare"]}],
        shape_by={f"*-{st}-{s}": {"base": f"block/73/table-{st}", "rotateY": ROT[s]} for st in ("set", "bare") for s in SIDES},
        extra={"class": "BackroomsL73Table", "entityClass": "BackroomsL73Table"}, inv="*-set-north"))
    out.append(("// Level 73: a large barrel of warm water in a bathroom, never empty (Regions.L73System)", fixed({
        "code": "l73-bath",
        "class": "BackroomsL73Bath",
        "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
        "blockmaterial": "Wood",
        "drawtype": "json",
        "shape": {"base": "block/73/bath"},
        "sidesolid": {"all": False},
        "sideopaque": {"all": False},
        "lightAbsorption": 0,
        "collisionbox": {"x1": 0.0625, "y1": 0, "z1": 0.0625, "x2": 0.9375, "y2": 0.875, "z2": 0.9375},
        "selectionbox": {"x1": 0.0625, "y1": 0, "z1": 0.0625, "x2": 0.9375, "y2": 0.875, "z2": 0.9375},
        "attributes": {"liquidSource": False},
        "drops": [],
        "sounds": WOOD,
    })))
    return out


def textures(save):
    save(slate(7370), "block/73/slate")
    save(slate(7371), "block/73/slate-2")
    save(velvet(7372), "block/73/velvet")
    save(gold(7373), "block/73/gold")
    save(banner_tex(7374), "block/73/banner")
    for i in range(6):
        save(painting(i, 7380 + i), f"block/73/painting-{i + 1}")
    save(door_outer(7390), "block/73/door-out")
    save(door_inner(7391), "block/73/door-in")
    save(attic_door(7392), "block/73/atticdoor-out")
    save(door_inner(7393).crop((0, 0, 64, 64)), "block/73/atticdoor-in")
    save(oak(7394), "block/73/oak")
    save(mahogany(7395), "block/73/mahogany")
    save(mahogany_end(7396), "block/73/mahogany-end")
    save(plate_tex(7397), "block/73/plate")
    save(stew_tex(7398), "block/73/stew")
    save(bread_tex(7399), "block/73/bread")
    save(water_glass_tex(7400, True), "block/73/glass-full")
    save(water_glass_tex(7401, False), "block/73/glass-empty")
    save(silver_tex(7402), "block/73/silverware")
    save(staves(7403), "block/73/staves")
    save(warm_water(7404), "block/73/warmwater")
    return 30


def shapes(write_json, shape_dir):
    n = 0
    for p in ("top", "mid", "low"):
        write_json(os.path.join(shape_dir, f"curtain-{p}.json"), None, curtain_shape(p)); n += 1
    write_json(os.path.join(shape_dir, "banner.json"), None, banner_shape()); n += 1
    for i in range(1, 7):
        write_json(os.path.join(shape_dir, f"painting-{i}.json"), None, painting_shape(i)); n += 1
    for st in ("shut", "open"):
        for p in DOOR_PARTS:
            write_json(os.path.join(shape_dir, f"door-{st}-{p}.json"), None, door_shape(p, st)); n += 1
    for p in ("lb", "rb", "lt", "rt"):
        write_json(os.path.join(shape_dir, f"atticdoor-{p}.json"), None, door_shape(p, "shut", attic=True)); n += 1
    for st in ("set", "bare"):
        write_json(os.path.join(shape_dir, f"table-{st}.json"), None, table_shape(st)); n += 1
    write_json(os.path.join(shape_dir, "bath.json"), None, bath_shape()); n += 1
    return n


LANG = [
    ("block-l73-slate", "Slate"),
    ("block-l73-boards", "Window Boards"),
    ("block-l73-curtain-*", "Red Velvet Curtain"),
    ("block-l73-banner-*", "Banner of the Silver Heart"),
    ("block-l73-painting-*", "Painting of the Frontrooms"),
    ("block-l73-door-*", "Silver Castle Door"),
    ("block-l73-atticdoor-*", "Attic Door"),
    ("block-l73-table-set-*", "Mahogany Table (a place set)"),
    ("block-l73-table-bare-*", "Mahogany Table"),
    ("block-l73-bath", "Barrel of Warm Water"),
]
