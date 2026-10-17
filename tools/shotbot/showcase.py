"""Before and after showcase images for change notes and the mod page.

    python tools/shotbot/showcase.py [docs/design/graphics-pass/showcase.json]

The map lists the pairs: for each, a short file name, a subject (the contact sheet's label), a one-line caption (for the
docs, not drawn), the before and after shots (paths relative to the repo root) and an optional crop, [x0, y0, x1, y1]
in fractions of the frame, applied to both sides and widened to 16:9. For each pair it writes <out>/<file>.jpg: before
on the left and after on the right, two 960x540 halves split by a thin divider, a small "Before" and "After" label,
JPEG quality 90. Then <out>/00-overview.jpg, every pair stacked under its subject, and, when the map names a "moddb"
folder, a web copy of each pair there (progressive JPEG, "moddb_width" wide, as the mod page's other images).
"""
import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
HALF_W, HALF_H = 960, 540
DIVIDER = 4
DIV_COL = (14, 13, 11)
BG = (24, 22, 18)
TEXT = (246, 238, 205)
FONTS = (r"C:\Windows\Fonts\bahnschrift.ttf", "DejaVuSans.ttf", "arial.ttf")


def font(size, style="SemiBold"):
    for name in FONTS:
        try:
            f = ImageFont.truetype(name, size)
        except OSError:
            continue
        try:
            f.set_variation_by_name(style)
        except Exception:
            pass
        return f
    return ImageFont.load_default()


def crop_169(im, crop):
    """Crops to the fractions given, widened or heightened about their centre to 16:9 and kept inside the frame."""
    w, h = im.size
    if crop:
        x0, y0, x1, y1 = crop[0] * w, crop[1] * h, crop[2] * w, crop[3] * h
    else:
        x0, y0, x1, y1 = 0, 0, w, h
    cw, ch = x1 - x0, y1 - y0
    if cw / ch > 16 / 9:
        ch = cw * 9 / 16
    else:
        cw = ch * 16 / 9
    cw, ch = min(cw, w), min(ch, h)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    left = min(max(cx - cw / 2, 0), w - cw)
    top = min(max(cy - ch / 2, 0), h - ch)
    return im.crop((round(left), round(top), round(left + cw), round(top + ch)))


def half(path, crop):
    full = os.path.join(REPO, path)
    if not os.path.exists(full):
        sys.exit(f"missing shot: {path}")
    im = Image.open(full).convert("RGB")
    return crop_169(im, crop).resize((HALF_W, HALF_H), Image.LANCZOS)


def label(canvas, x, text):
    """A small label in a dark rounded box at the bottom left of a half."""
    f = font(26)
    d = ImageDraw.Draw(canvas, "RGBA")
    l, t, r, b = d.textbbox((0, 0), text, font=f)
    pad_x, pad_y, margin = 12, 7, 16
    bx, by = x + margin, HALF_H - margin - (b - t) - 2 * pad_y
    d.rounded_rectangle((bx, by, bx + (r - l) + 2 * pad_x, by + (b - t) + 2 * pad_y), radius=6, fill=(12, 11, 9, 170))
    d.text((bx + pad_x - l, by + pad_y - t), text, font=f, fill=TEXT)


def two_up(pair):
    canvas = Image.new("RGB", (2 * HALF_W, HALF_H), BG)
    canvas.paste(half(pair["before"], pair.get("crop")), (0, 0))
    canvas.paste(half(pair["after"], pair.get("crop")), (HALF_W, 0))
    ImageDraw.Draw(canvas).rectangle((HALF_W - DIVIDER // 2, 0, HALF_W + DIVIDER // 2 - 1, HALF_H), fill=DIV_COL)
    label(canvas, 0, "Before")
    label(canvas, HALF_W, "After")
    return canvas


def overview(images, subjects, width):
    ph = round(images[0].height * width / images[0].width)
    s = width / 1280  # label sizes are set for a 1280 px sheet
    head, gap, margin = round(52 * s), round(14 * s), round(20 * s)
    f = font(round(30 * s))
    sheet = Image.new("RGB", (width, len(images) * (head + ph) + (len(images) - 1) * gap + margin), BG)
    d = ImageDraw.Draw(sheet)
    for i, (im, subject) in enumerate(zip(images, subjects)):
        y = i * (head + ph + gap)
        l, t, r, b = d.textbbox((0, 0), subject, font=f)
        d.text((margin - l, y + (head - (b - t)) // 2 - t), subject, font=f, fill=TEXT)
        sheet.paste(im.resize((width, ph), Image.LANCZOS), (0, y + head))
    return sheet


def rel(path):
    return os.path.relpath(path, REPO).replace("\\", "/")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map", nargs="?", default="docs/design/graphics-pass/showcase.json")
    a = ap.parse_args()
    with open(os.path.join(REPO, a.map), encoding="utf-8") as fh:
        m = json.load(fh)
    out = os.path.join(REPO, m["out"])
    os.makedirs(out, exist_ok=True)
    web = os.path.join(REPO, m["moddb"]) if m.get("moddb") else None
    if web:
        os.makedirs(web, exist_ok=True)
    images, subjects = [], []
    for pair in m["pairs"]:
        im = two_up(pair)
        path = os.path.join(out, pair["file"] + ".jpg")
        im.save(path, quality=90)
        print("wrote", rel(path), im.size)
        if web:
            ww = m.get("moddb_width", 1280)
            small = im.resize((ww, round(im.height * ww / im.width)), Image.LANCZOS)
            wpath = os.path.join(web, pair["file"] + ".jpg")
            small.save(wpath, quality=88, progressive=True, optimize=True)
            print("wrote", rel(wpath), small.size)
        images.append(im)
        subjects.append(pair["subject"])
    sheet = overview(images, subjects, m.get("overview_width", 1280))
    path = os.path.join(out, "00-overview.jpg")
    sheet.save(path, quality=90)
    print("wrote", rel(path), sheet.size)


if __name__ == "__main__":
    main()
