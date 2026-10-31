"""Finishing for the mod's flat item icons (graphics pass B17): the generators paint an icon as flat PIL shapes; `finish`
lights it the way vanilla's item icons are lit, without changing its silhouette or its colours' means.

    img = iconkit.finish(img, seed="soda")       # an RGBA icon (32 x 32 or 16 x 16)

What it does, on the icon's own pixels only (nothing outside the silhouette is drawn, nothing inside is cut):
- splits the icon into areas of one colour (a label, a cap, a blade), and gives each a soft bevel: a height that rises
  from its edges over a few pixels, lit from the top left, so each area reads as a moulded part, the label as printed
  on the body;
- the whole silhouette rounds off the same way, more broadly, so the object has a lit top-left and a shaded
  bottom-right;
- the outline (the silhouette's edge pixels) is redrawn in a darker shade of the colour inside it, rather than one
  flat dark line, darker on the bottom-right than on the top-left;
- lit pixels drift a little warm and shaded ones cool, and a fine grain of 2 to 3 levels is added;
- each area keeps its mean colour, so the icon reads as the same object in the same colours.

ICONS lists the 2D icons (items drawn from their texture, with no shape) the generators finish when they save them;
textures laid on item shapes (almondwater, beans, crackers, the keys, the plush toys) are not icons and are left alone.
"""
import math
import random
from collections import deque

from PIL import Image

# Icons by their path under textures/ (without .png): items whose type has a texture and no shape
ICONS = {
    "item/candybar", "item/cashewwater", "item/chalk", "item/chips", "item/soda", "item/waterbottle",
    "item/almondmilk", "item/crownshard", "item/epsomsalt", "item/redwater", "item/prybar",
    "item/mothquill", "item/spidersilk", "item/clumpsinew", "item/mothjelly",
    "item/seedpacket-carrot", "item/seedpacket-flax", "item/seedpacket-onion", "item/seedpacket-spelt",
    "item/seedpacket-turnip", "item/wanderernote", "item/wanderernote-folded",
    "item/salvage/carpetfibre", "item/salvage/ceramicgrit", "item/salvage/glassshard", "item/salvage/glassshiv",
    "item/salvage/metalbracket", "item/salvage/pleather", "item/salvage/potshard", "item/salvage/rottenwood", "item/salvage/rubble",
    "item/salvage/scraper", "item/salvage/scrapwire", "item/salvage/wallpaperstrip",
    "item/188/cereal", "item/188/juicebox", "item/188/keycard",
    "item/3999/circuitboard", "item/3999/coinmech", "item/3999/cottoncandy", "item/3999/glowband-cyan",
    "item/3999/glowband-lilac", "item/3999/glowband-magenta", "item/3999/neontubing", "item/3999/plastic",
    "item/3999/popcorn", "item/3999/soda-cherry", "item/3999/soda-grape", "item/3999/soda-lime", "item/3999/ticket",
    "item/3999/traymeal-burger", "item/3999/traymeal-icecream", "item/3999/traymeal-noodles",
    "item/3999/traymeal-pizza", "item/3999/traymeal-pretzel", "item/3999/traymeal-taco",
    "item/974/candy", "item/974/marshmallow", "item/974/meal-macaroni", "item/974/meal-pancakes", "item/974/meal-soup",
    "item/974/strawberrymilk",
    "item/end/cataloguecard",
    "item/fun/cakeslice-birthday", "item/fun/cakeslice-velvet", "item/fun/cookie", "item/fun/lucatears",
}


def is_icon(rel):
    """`rel`: a texture path under textures/ (forward or back slashes, with or without .png)."""
    rel = rel.replace("\\", "/")
    if rel.endswith(".png"):
        rel = rel[:-4]
    return rel in ICONS


def _lum(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def _regions(px, w, h, tol):
    """Areas of one colour: 4-connected opaque pixels within `tol` (RGB distance) of their neighbour and of the
    area's first pixel."""
    rid = [[-1] * w for _ in range(h)]
    out = []
    for y in range(h):
        for x in range(w):
            if rid[y][x] >= 0 or px[x, y][3] == 0:
                continue
            seed = px[x, y]
            q = deque([(x, y)])
            rid[y][x] = len(out)
            cells = []
            while q:
                cx, cy = q.popleft()
                cells.append((cx, cy))
                c = px[cx, cy]
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and rid[ny][nx] < 0:
                        d = px[nx, ny]
                        if d[3] and sum(abs(d[i] - c[i]) for i in range(3)) <= tol \
                                and sum(abs(d[i] - seed[i]) for i in range(3)) <= tol * 2:
                            rid[ny][nx] = len(out)
                            q.append((nx, ny))
            out.append(cells)
    return rid, out


def _distance(inside, w, h, cap):
    """Chessboard-ish distance (in px) from each inside pixel to the nearest outside one, capped."""
    d = [[0 if not inside[y][x] else cap for x in range(w)] for y in range(h)]
    q = deque()
    for y in range(h):
        for x in range(w):
            if inside[y][x]:
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not (0 <= nx < w and 0 <= ny < h) or not inside[ny][nx]:
                        d[y][x] = 1
                        q.append((x, y))
                        break
    while q:
        x, y = q.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and inside[ny][nx] and d[ny][nx] > d[y][x] + 1:
                d[ny][nx] = d[y][x] + 1
                q.append((nx, ny))
    return d


def finish(img, seed="", bevel=0.26, round_=0.2, outline=0.55, grain=2.5, drift=0.15, tol=24, min_area=6):
    """The finished icon (a new RGBA image of the same size); see the module docstring."""
    img = img.convert("RGBA")
    w, h = img.size
    src = img.load()
    out = img.copy()
    px = out.load()
    rng = random.Random("icon:" + str(seed))
    solid = [[src[x, y][3] > 0 for x in range(w)] for y in range(h)]
    if not any(any(r) for r in solid):
        return out
    cap_s = max(2, min(w, h) // 8)
    sil = _distance(solid, w, h, cap_s)
    rid, regions = _regions(src, w, h, tol)
    # each area's own height (areas too small to bevel follow the silhouette alone)
    area_h = [[0.0] * w for _ in range(h)]
    for i, cells in enumerate(regions):
        if len(cells) < min_area:
            continue
        inside = [[False] * w for _ in range(h)]
        for x, y in cells:
            inside[y][x] = True
        d = _distance(inside, w, h, 2)
        for x, y in cells:
            area_h[y][x] = d[y][x] / 2.0
    H = [[0.6 * sil[y][x] / cap_s + 0.4 * area_h[y][x] for x in range(w)] for y in range(h)]

    def hget(x, y):
        return H[y][x] if 0 <= x < w and 0 <= y < h and solid[y][x] else 0.0

    edge = [[solid[y][x] and any(not (0 <= nx < w and 0 <= ny < h) or not solid[ny][nx]
                                 for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
             for x in range(w)] for y in range(h)]
    k = [[1.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not solid[y][x]:
                continue
            # slope toward the light (top left): lit where the surface falls away toward it
            s = (hget(x, y) - hget(x - 1, y - 1)) + 0.5 * ((hget(x, y) - hget(x - 1, y)) + (hget(x, y) - hget(x, y - 1)))
            kk = 1 + bevel * max(-1.5, min(1.5, s))
            # the silhouette's broad rounding: lighter toward the top left of the object, darker bottom right
            kk *= 1 + round_ * (0.5 - (x + y) / (w + h - 2)) * (1 - min(1.0, sil[y][x] / cap_s) * 0.3)
            k[y][x] = kk
    # keep each area's mean: the light moves within an area, its colour stays
    for cells in regions:
        m = sum(k[y][x] for x, y in cells) / len(cells)
        for x, y in cells:
            k[y][x] /= m if m > 0 else 1
    for y in range(h):
        for x in range(w):
            if not solid[y][x]:
                continue
            c = src[x, y]
            kk = k[y][x]
            lum = _lum(c)
            dl = max(-5.0, min(5.0, (kk - 1) * lum * drift))
            g = rng.uniform(-grain, grain)
            r, gg, b = c[0] * kk + dl + g, c[1] * kk + dl * 0.3 + g, c[2] * kk - dl + g
            if edge[y][x] and outline:
                # the outline: a darker shade of what is inside, darker on the bottom right
                ins = [src[nx, ny] for nx in range(x - 2, x + 3) for ny in range(y - 2, y + 3)
                       if 0 <= nx < w and 0 <= ny < h and solid[ny][nx] and not edge[ny][nx]]
                if ins:
                    base = tuple(sum(c2[i] for c2 in ins) / len(ins) for i in range(3))
                    br = (x + y) / (w + h - 2)
                    dark = 0.62 - 0.22 * br
                    tgt = (base[0] * dark, base[1] * dark, base[2] * dark * 1.04 + 4)
                    if _lum(c) < _lum(base) * 0.7:          # an outline already drawn: retint it
                        mixk = outline
                    else:                                     # an unoutlined edge: only shade it
                        mixk = outline * 0.45
                    r, gg, b = (r * (1 - mixk) + tgt[0] * mixk, gg * (1 - mixk) + tgt[1] * mixk, b * (1 - mixk) + tgt[2] * mixk)
            px[x, y] = (max(0, min(255, int(round(r)))), max(0, min(255, int(round(gg)))), max(0, min(255, int(round(b)))), c[3])
    return out
