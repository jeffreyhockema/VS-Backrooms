"""Before/after sheet for the graphics pass: before above a magenta line, after below, one column per spot.

    python tools/shotbot/compare.py <before dir> <after dir> --out sheet.jpg [--width 480] [--cols 6] [--only a,b] [--stats]

Spots are matched by file name (name.jpg or name.png, as batch.py writes them); a spot missing on one side shows a
magenta MISSING box. --stats prints, per spot, the mean difference between the two (0-255, on 160x90 grey thumbnails,
so it measures framing and light rather than texture detail) and the share of the frame that moved, to check that a
retake lines up (a repeat of the same build should be near 0) or to find what a batch changed.
With more spots than --cols the sheet wraps into bands, each band a row of befores over a row of afters, so every
pair stays one above the other. The spot's name is drawn over each pair.
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

MAGENTA = (255, 0, 255)
EXTS = (".jpg", ".png")


def font(size):
    for name in ("consola.ttf", "DejaVuSansMono.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def shots(folder):
    out = {}
    for f in sorted(os.listdir(folder)):
        stem, ext = os.path.splitext(f)
        if ext.lower() in EXTS and stem != "sheet" and not stem.startswith("compare"):
            out.setdefault(stem, os.path.join(folder, f))
    return out


def main():
    ap = argparse.ArgumentParser(description="before/after sheet")
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=480, help="width of each shot on the sheet")
    ap.add_argument("--cols", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--stats", action="store_true", help="print how far each pair differs")
    a = ap.parse_args()
    before, after = shots(a.before), shots(a.after)
    names = sorted(set(before) | set(after), key=lambda n: (n.endswith("-inspection"), n))
    if a.only:
        keep = a.only.split(",")
        names = [n for n in names if n in keep]
    if not names:
        sys.exit("no shots")
    sample = Image.open(next(iter(before.values()) if before else next(iter(after.values()))))
    w = a.width
    h = round(w * sample.height / sample.width)
    label_h, line, gap = 22, 4, 14
    cols = min(a.cols, len(names))
    bands = (len(names) + cols - 1) // cols
    band_h = label_h + h + line + h
    W = cols * w + (cols - 1) * 4
    H = bands * band_h + (bands - 1) * gap
    sheet = Image.new("RGB", (W, H), (16, 16, 16))
    d = ImageDraw.Draw(sheet)
    f = font(15)
    for i, n in enumerate(names):
        x = (i % cols) * (w + 4)
        y = (i // cols) * (band_h + gap)
        d.text((x + 4, y + 3), n, fill=(255, 255, 255), font=f)
        for side, (src, yy) in enumerate(((before.get(n), y + label_h), (after.get(n), y + label_h + h + line))):
            if src:
                sheet.paste(Image.open(src).convert("RGB").resize((w, h), Image.LANCZOS), (x, yy))
            else:
                d.rectangle((x, yy, x + w - 1, yy + h - 1), outline=MAGENTA, width=3)
                d.text((x + 10, yy + 10), "MISSING", fill=MAGENTA, font=f)
        # the magenta line between before and after, across this band
        d.rectangle((x, y + label_h + h, x + w - 1, y + label_h + h + line - 1), fill=MAGENTA)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    sheet.save(a.out, quality=90)
    if a.stats:
        print(f"{'spot':32} {'mean':>6} {'moved':>6}")
        for n in names:
            if n not in before or n not in after:
                print(f"{n:32} {'missing':>13}")
                continue
            x = Image.open(before[n]).convert("L").resize((160, 90), Image.BOX)
            y = Image.open(after[n]).convert("L").resize((160, 90), Image.BOX)
            diff = [abs(p - q) for p, q in zip(x.tobytes(), y.tobytes())]
            mean = sum(diff) / len(diff)
            moved = sum(1 for v in diff if v > 24) / len(diff)
            print(f"{n:32} {mean:6.1f} {moved:6.1%}" + ("   <- differs" if mean > 6 or moved > 0.05 else ""))
    print(f"{a.out}: {len(names)} spots, {bands} band(s); before {len(before)}, after {len(after)}")


if __name__ == "__main__":
    main()
