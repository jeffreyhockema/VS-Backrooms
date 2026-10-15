"""Per-family before/after pairs for the graphics pass, so the user can choose family by family what to keep.

    python tools/shotbot/sidebyside.py <map.json> [--index review/compare.html]

The map names the batch, the before and after shot folders, the output folder, and for each asset family the spots
that show it best (a close-up first, then a wide where it matters):

    {"batch": "B3", "title": "Level 0",
     "before": "review/baseline/0", "after": "review/b3/final", "out": "review/b3/sidebyside",
     "families": [{"id": "wallpaper", "name": "Chevron wallpaper", "spots": ["close-wall", "wide-02"]}, ...]}

Paths are relative to the repo root. For each family it writes <out>/<id>.jpg: one row per spot, BEFORE on the left and
AFTER on the right, each at 1920 px wide (shots taken at another size are scaled to it), labelled. It then records the
batch in review/compare.json (one entry per batch, replaced when the batch is run again) and rebuilds the index,
review/compare.html: a plain local page (relative image paths, no external resources) with a section per batch and a
row per family. Later batches run this with their own map and their section is added beside the others.
"""
import argparse
import html
import json
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from compare import font, shots  # noqa: E402

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
W, H = 1920, 1080
BAR = 56
GAP = 16
BG = (24, 24, 28)


def fit(path):
    im = Image.open(path).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, int(im.height * W / im.width)), Image.LANCZOS)
        if im.height != H:
            pad = Image.new("RGB", (W, H), BG)
            pad.paste(im, (0, (H - im.height) // 2))
            im = pad
    return im


def missing(name):
    im = Image.new("RGB", (W, H), BG)
    ImageDraw.Draw(im).text((40, 40), f"MISSING: {name}", fill=(255, 0, 255), font=font(40))
    return im


def pair(family, before, after, batch):
    rows = len(family["spots"])
    sheet = Image.new("RGB", (2 * W + GAP, rows * (H + BAR) + (rows - 1) * GAP), BG)
    d = ImageDraw.Draw(sheet)
    f = font(34)
    for i, spot in enumerate(family["spots"]):
        y = i * (H + BAR + GAP)
        for k, (side, src) in enumerate((("BEFORE (baseline)", before), (f"AFTER ({batch})", after))):
            x = k * (W + GAP)
            d.text((x + 16, y + 10), f"{side}  -  {family['name']}  -  {spot}", fill=(235, 235, 235), font=f)
            sheet.paste(fit(src[spot]) if spot in src else missing(spot), (x, y + BAR))
    return sheet


def rel(path, start):
    return os.path.relpath(path, start).replace("\\", "/")


def write_index(manifest, index):
    base = os.path.dirname(index)
    parts = ["<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             "<title>Graphics pass side by side</title>",
             "<style>body{background:#1c1c20;color:#e6e6e6;font:15px/1.4 system-ui,sans-serif;margin:16px}"
             "h1{font-size:22px}h2{margin-top:32px;border-bottom:1px solid #444;padding-bottom:4px}"
             ".fam{margin:18px 0}.fam h3{margin:0 0 6px;font-size:16px}.fam img{width:100%;height:auto;display:block}"
             "nav a{color:#9cf;margin-right:12px}a{color:#9cf}</style></head><body>",
             "<h1>Graphics pass: before and after, family by family</h1>",
             "<p>Left: before (the baseline). Right: after. Click an image for full size. Decisions go in "
             "docs/design/graphics-pass/decisions.md.</p><nav>"]
    for b in manifest["batches"]:
        parts.append(f'<a href="#{html.escape(b["batch"])}">{html.escape(b["batch"])} {html.escape(b.get("title", ""))}</a>')
    parts.append("</nav>")
    for b in manifest["batches"]:
        parts.append(f'<h2 id="{html.escape(b["batch"])}">{html.escape(b["batch"])}: {html.escape(b.get("title", ""))}</h2>')
        if b.get("note"):
            parts.append(f'<p class="note" style="color:#e0b060;max-width:900px"><b>Note:</b> {html.escape(b["note"])}</p>')
        for fam in b["families"]:
            src = rel(os.path.join(REPO, fam["image"]), base)
            parts.append(f'<div class="fam"><h3>{html.escape(fam["name"])} <small>({html.escape(fam["id"])}; '
                         f'{html.escape(", ".join(fam["spots"]))})</small></h3>'
                         f'<a href="{html.escape(src)}"><img src="{html.escape(src)}" alt="{html.escape(fam["name"])}" loading="lazy"></a></div>')
    parts.append("</body></html>")
    with open(index, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(parts) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map")
    ap.add_argument("--index", default="review/compare.html")
    a = ap.parse_args()
    with open(a.map, encoding="utf-8") as fh:
        m = json.load(fh)
    before, after = shots(os.path.join(REPO, m["before"])), shots(os.path.join(REPO, m["after"]))
    out = os.path.join(REPO, m["out"])
    os.makedirs(out, exist_ok=True)
    fams = []
    for fam in m["families"]:
        img = os.path.join(out, fam["id"] + ".jpg")
        pair(fam, before, after, m["batch"]).save(img, quality=90)
        print("wrote", rel(img, REPO))
        fams.append(dict(fam, image=rel(img, REPO)))
    index = os.path.join(REPO, a.index)
    mpath = os.path.join(os.path.dirname(index), "compare.json")
    manifest = {"batches": []}
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as fh:
            manifest = json.load(fh)
    manifest["batches"] = [b for b in manifest["batches"] if b["batch"] != m["batch"]]
    manifest["batches"].append({"batch": m["batch"], "title": m.get("title", ""), "families": fams})
    manifest["batches"].sort(key=lambda b: (len(b["batch"]), b["batch"]))
    with open(mpath, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1)
    write_index(manifest, index)
    print("wrote", rel(index, REPO))


if __name__ == "__main__":
    main()
