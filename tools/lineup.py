"""Renders the creature lineup for the mod page ("What lives here"): every entity at its true size relative to the
others (the two giants at half scale), facing the viewer, standing on one ground line, named underneath.

    python tools/lineup.py out.png [yaw=65] [pitch=8] [rings=1|few=1]

`rings=1` draws only what lives in the rings (Levels 0 to 11), in two rows. `few=1` draws eight of them in two rows beside the Mangled
with "and many more to discover" under it: the mod page's lineup, which keeps most of what lives here out of sight. A 1920x1080 picture in three rows, with the Mangled standing at the right beside them, scaled to fill it. `yaw` turns the models from straight on (90) so their depth shows. The renderer is the one in
entrender.py (the game's element transforms), drawing onto a transparent canvas.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from entrender import pose_at, quads  # noqa: E402

ASSETS = os.path.join(HERE, "..", "assets", "backrooms")

# name, shape, texture, entity size, extra scale (1, or 0.5 for the giants), label
ROSTER = [
    ("Smiler", "smiler", "smiler", 1.0, 1),
    ("Hound", "hound", "hound", 1.0, 1),
    ("Faceling", "faceling", "faceling-casual", 1.0, 1),
    ("Deathmoth", "deathmoth-male", "deathmoth-male", 1.0, 1),
    ("Skin-Stealer", "skinstealer", "skinstealer", 0.92, 1),
    ("Duller", "duller", "duller", 0.92, 1),
    ("Death Rat", "deathrat", "deathrat", 1.0, 1),
    ("Clump", "clump", "clump", 1.0, 1),
    ("Bacteria", "bacteria", "bacteria", 1.0, 1),
    ("Wretch", "wretch", "wretch", 1.0, 1),
    ("The Beast\nof Level 5", "beast", "beast", 1.0, 1),
    ("Giant Spider", "giantspider", "giantspider", 1.0, 1),
    ("Neighborhood\nWatch", "neighborhoodwatch", "neighborhoodwatch", 1.0, 1),
    ("Watcher", "watcher", "watcher", 1.0, 1),
    ("Partygoer", "fun-partygoer", "fun-partygoer", 1.0, 1),
    ("Kitty", "974/l974-kitty", "974/l974-kitty", 1.0, 1),
    ("Window Arm", "188/l188-arm", "188/l188-arm", 1.0, 1),
    ("Clay\nAnimation", "animation-clay", "animation-clay", 1.0, 1),
    ("Wooden\nAnimation", "animation-wooden", "animation-wooden", 1.0, 1),
    ("Paper\nAnimation", "animation-paper", "animation-paper", 1.0, 1),
    ("Robo-Man", "roboman", "roboman", 1.0, 1),
    ("Lure Balloon", "fun-lureballoon", "fun-lureballoon", 1.0, 1),
    ("Keymaster", "hub-keymaster", "hub-keymaster", 1.0, 1),
    ("Attendant", "3999/attendant", "3999/attendant", 1.0, 1),
    ("The Thing\n(half scale)", "thething", "thething", 1.0, 0.5),
    ("The Mangled (half scale)", "mangled", "mangled", 1.5, 0.5),
]


def render_rgba(shape, tex, pose, yaw, pitch, scale):
    """entrender.render onto a transparent canvas fitted to the model; returns (image, ground y in the image)."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    light = np.array([0.35, 0.8, 0.5]); light /= np.linalg.norm(light)
    px = tex.load()
    polys = []
    for pts, (u1, v1, u2, v2), glow in quads(shape, tex, pose):
        p = [np.array(q) - np.array([0.5, 0, 0.5]) for q in pts]
        normal = np.cross(p[1] - p[0], p[3] - p[0])
        nl = np.linalg.norm(normal)
        normal = normal / nl if nl > 1e-9 else normal
        k = 0.5 + 0.5 * max(0.0, float(normal @ light))
        if glow:
            k = max(k, 0.5 + glow / 255 * 0.5)
        nu = max(2, min(24, int(round(abs(u2 - u1)))))
        nv = max(2, min(24, int(round(abs(v2 - v1)))))
        for i in range(nu):
            for j in range(nv):
                def at(a, b):
                    return p[0] + (p[1] - p[0]) * a + (p[3] - p[0]) * b
                corners = [at(i / nu, j / nv), at((i + 1) / nu, j / nv), at((i + 1) / nu, (j + 1) / nv), at(i / nu, (j + 1) / nv)]
                uu = u1 + (u2 - u1) * (i + 0.5) / nu
                vv = v2 + (v1 - v2) * (j + 0.5) / nv
                c = px[min(tex.width - 1, max(0, int(uu))), min(tex.height - 1, max(0, int(vv)))]
                if len(c) == 4 and c[3] < 10:
                    continue
                proj, depth = [], 0
                for q in corners:
                    x, y, z = q
                    x, z = x * cy - z * sy, x * sy + z * cy
                    y, z = y * cp - z * sp, y * sp + z * cp
                    proj.append((x * scale, -y * scale))
                    depth += z
                polys.append((depth / 4, proj, tuple(int(v * k) for v in c[:3]) + (255,)))
    xs = [x for _, pr, _ in polys for x, _ in pr]
    ys = [y for _, pr, _ in polys for _, y in pr]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 4
    W, H = int(x1 - x0) + 2 * pad, int(y1 - y0) + 2 * pad
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _, proj, col in sorted(polys, key=lambda t: -t[0]):
        d.polygon([(x - x0 + pad, y - y0 + pad) for x, y in proj], fill=col)
    # The model's own ground (y = 0) in the image: below it only feet that sink into the floor
    ground = -y0 + pad
    return img, ground


def idle_pose(shape):
    anims = {a["code"]: a for a in shape.get("animations", [])}
    for code in ("idle", "rest", "stand"):
        if code in anims:
            return pose_at(anims[code], 0)
    return {}


def font(names, size):
    for n in names:
        try:
            return ImageFont.truetype(os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", n), size)
        except OSError:
            continue
    return ImageFont.load_default()


# Three rows: the small and human-sized first, then the far levels' own; The Thing last, the Mangled beside them all
ROWS = [9, 8, 8]
# What lives in the rings (Levels 0 to 11): the mod page's lineup (rings=1), two rows
RINGS = ["Smiler", "Hound", "Faceling", "Deathmoth", "Skin-Stealer", "Duller", "Death Rat", "Clump", "Bacteria", "Wretch",
         "The Beast\nof Level 5", "Giant Spider", "Neighborhood\nWatch", "Watcher", "The Thing\n(half scale)",
         "The Mangled (half scale)"]
RINGS_ROWS = [7, 8]
# A taste (few=1): eight, the small ones over the tall ones beside the Mangled, and the rest left to be met
FEW = ["Death Rat", "Deathmoth", "Hound", "Faceling", "Bacteria", "Keymaster", "The Thing\n(half scale)",
       "The Mangled (half scale)"]
FEW_ROWS = [4, 3]
FEW_CAPTION = "...and many more to discover"
# Drawn standing at the right, beside every row, so the rows need not be as tall as it
SIDE = {"The Mangled (half scale)"}
SIZE = (1920, 1080)
RINGS_ONLY = False
FEW_ONLY = False


def render_all(ppb, yaw, pitch):
    figures = []
    for label, shape_name, tex_name, size, extra in ROSTER:
        if RINGS_ONLY and label not in RINGS:
            continue
        if FEW_ONLY and label not in FEW:
            continue
        shape = json.load(open(os.path.join(ASSETS, "shapes", "entity", shape_name + ".json"), encoding="utf-8-sig"))
        tex = Image.open(os.path.join(ASSETS, "textures", "entity", tex_name + ".png")).convert("RGBA")
        img, ground = render_rgba(shape, tex, idle_pose(shape), yaw, pitch, ppb * size * extra)
        figures.append((label, img, ground))
    return figures


LINE_H = 34  # each further line of a two-line label


def label_w(label_font, label):
    """A label's width: its longest line (a label may break over two lines with a newline)."""
    return max(label_font.getbbox(line)[2] for line in label.split("\n"))


def label_lines(row):
    return max(label.count("\n") + 1 for label, _, _ in row)


def layout(figures, label_font, gap):
    """Per row: (figures, width, height above the ground line, height below it)."""
    rows, i = [], 0
    for n in ROWS:
        row = figures[i:i + n]
        i += n
        width = sum(max(img.width, label_w(label_font, label)) for label, img, _ in row) + gap * (len(row) - 1)
        rows.append((row, width, max(g for _, _, g in row), max(img.height - g for _, img, g in row)))
    return rows


def split(figures):
    """The rows' figures, and the one drawn standing at the right beside every row (the tallest giant)."""
    side = [f for f in figures if f[0] in SIDE]
    return [f for f in figures if f[0] not in SIDE], side[0] if side else None


def main():
    out = sys.argv[1]
    opts = dict(a.split("=", 1) for a in sys.argv[2:])
    yaw, pitch = float(opts.get("yaw", 65)), float(opts.get("pitch", 8))
    global RINGS_ONLY, FEW_ONLY, ROWS
    RINGS_ONLY = opts.get("rings", "0") == "1"
    FEW_ONLY = opts.get("few", "0") == "1"
    if RINGS_ONLY:
        ROWS = RINGS_ROWS
    if FEW_ONLY:
        ROWS = FEW_ROWS
    W, H = SIZE
    label_font, title_font = font(["georgia.ttf", "times.ttf"], 28), font(["georgiab.ttf", "timesbd.ttf"], 52)
    gap, margin, top, label_h, row_gap = 26, 60, 130, 58, 18
    caption_font = font(["georgiai.ttf", "timesi.ttf", "georgia.ttf"], 40)
    caption_h = 56 if FEW_ONLY else 0  # room at the bottom for the caption, in the bottom right corner

    # Measure at a reference scale, then render again at the largest scale that fits the frame (labels keep their
    # size, so shrink a little more until every row fits beside the side figure's column)
    ref = 100.0
    figs, side = split(render_all(ref, yaw, pitch))
    rows = layout(figs, label_font, gap)
    fit_w = min((W - 2 * margin) / (w - gap * (len(r) - 1)) * 1.0 for r, w, _, _ in rows)
    fit_h = (H - top - 30 - caption_h - sum(label_h + LINE_H * (label_lines(r) - 1) for r, _, _, _ in rows) - row_gap * (len(rows) - 1)) / sum(a + b for _, _, a, b in rows)
    if side:
        fit_h = min(fit_h, (H - top - 30 - caption_h - label_h) / side[1].height)
    ppb = ref * min(fit_w, fit_h) * 0.97
    while True:
        figs, side = split(render_all(ppb, yaw, pitch))
        rows = layout(figs, label_font, gap)
        side_w = (max(side[1].width, label_w(label_font, side[0])) + gap) if side else 0
        region = W - 2 * margin - side_w
        if all(w <= region for _, w, _, _ in rows) or ppb < 20:
            break
        ppb *= 0.96

    sheet = Image.new("RGBA", (W, H))
    grad = ImageDraw.Draw(sheet)
    for y in range(H):
        t = y / H
        grad.line([(0, y), (W, y)], fill=(int(36 + 22 * t), int(36 + 20 * t), int(44 + 20 * t), 255))
    d = ImageDraw.Draw(sheet)
    d.text((margin, 40), "What lives here", font=title_font, fill=(240, 234, 218))

    # Share the spare height out between the rows; the rows sit left of the side figure's column
    labels_h = [label_h + LINE_H * (label_lines(r) - 1) for r, _, _, _ in rows]
    used = sum(a + b for _, _, a, b in rows) + sum(labels_h) + row_gap * (len(rows) - 1)
    if FEW_ONLY and side:
        # A tight stack, centred together with the side figure, whose feet stand on the last row's ground line
        last_from_top = used - (rows[-1][3] + labels_h[-1])
        above_line = max(last_from_top, side[2])
        below_line = max(rows[-1][3] + labels_h[-1], side[1].height - side[2] + label_h)
        spare = 0
        y = top + max(0, H - top - 30 - caption_h - above_line - below_line) / 2 + above_line - last_from_top
    else:
        spare = max(0, H - top - 30 - caption_h - used) / (len(rows) + 1)
        y = top + spare
    base = 0
    for row, width, above, below in rows:
        base = int(y + above)
        x = margin + (region - width) / 2
        d.line([(x - 20, base + 2), (x + width + 20, base + 2)], fill=(86, 84, 94), width=2)
        for label, img, ground in row:
            lw = label_w(label_font, label)
            slot = max(img.width, lw)
            sheet.alpha_composite(img, (int(x + (slot - img.width) / 2), int(base - ground)))
            d.multiline_text((x + slot / 2, base + int(below) + 16), label, font=label_font, fill=(222, 216, 204),
                             anchor="ma", align="center", spacing=LINE_H - 30)
            x += slot + gap
        last_below = below
        y = base + below + label_h + LINE_H * (label_lines(row) - 1) + row_gap + spare
    if side:
        label, img, ground = side
        lw = label_w(label_font, label)
        slot = max(img.width, lw)
        x = W - margin - slot
        d.line([(x - 20, base + 2), (x + slot + 20, base + 2)], fill=(86, 84, 94), width=2)
        sheet.alpha_composite(img, (int(x + (slot - img.width) / 2), int(base - ground)))
        d.text((x + (slot - lw) / 2, base + int(last_below) + 16), label, font=label_font, fill=(222, 216, 204))
    if FEW_ONLY:
        cw = caption_font.getbbox(FEW_CAPTION)[2]
        d.text((W - margin - cw, H - 30 - caption_h + 6), FEW_CAPTION, font=caption_font, fill=(222, 216, 204))
    sheet.convert("RGB").save(out)
    print(out, sheet.size, f"{ppb:.0f} px per block")


if __name__ == "__main__":
    main()
