"""Contact sheet of textures at 4x nearest-neighbour, for judging them without the client.

    python tools/texsheet.py <folder or glob>... --out sheet.png [--ref <png>...] [--tile] [--scale 4]
                             [--max 256] [--cols N] [--per-page N] [-r]

  folder or glob   a folder (its PNGs; with -r also its subfolders') or a glob such as assets/backrooms/textures/block/level1/wall*.png
  --ref            vanilla references for the first row, as paths or relative to the game's survival textures,
                   e.g. --ref block/stone/cobblestone/granite1 block/wood/planks/oak1
                   (VINTAGE_STORY, else G:/Games/Vintagestory; the .png may be left off)
  --tile           each texture as a 3x3 repeat, so seams and repetition show
  --scale          magnification (default 4); a texture bigger than --max px on the sheet (3x --max with --tile) is
                   shown at a smaller whole-number scale (at least 1x), and the label says so
  --per-page N     at most N textures per sheet: sheet-1.png, sheet-2.png ... (the references head every page)
  --all            every folder under assets/backrooms/textures into --out/<folder>.png (block/level1 ->
                   block-level1.png), each with its vanilla counterparts as references (FOLDER_REFS), e.g.
                   python tools/texsheet.py --all --per-page 48 --out review/baseline/texsheets
                   python tools/texsheet.py --all --tile --per-page 24 --out review/baseline/texsheets
Each tile is labelled with its file name (relative to the folder) and its size; references are framed in gold.
"""
import argparse
import glob
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

GAME = os.environ.get("VINTAGE_STORY", r"G:\Games\Vintagestory")
VANILLA = os.path.join(GAME, "assets", "survival", "textures")
LABEL_H = 44
PAD = 8
BG = (36, 38, 42)
REF_FRAME = (212, 175, 55)


def font(size):
    for name in ("consola.ttf", "DejaVuSansMono.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def find_ref(p):
    cands = [p, p + ".png", os.path.join(VANILLA, p), os.path.join(VANILLA, p + ".png"),
             os.path.join(GAME, "assets", p), os.path.join(GAME, "assets", p + ".png")]
    for c in cands:
        if os.path.isfile(c):
            return c
    sys.exit(f"reference not found: {p}")


def collect(inputs, recursive):
    files = []
    for spec in inputs:
        if os.path.isdir(spec):
            pattern = os.path.join(spec, "**", "*.png") if recursive else os.path.join(spec, "*.png")
            for f in sorted(glob.glob(pattern, recursive=recursive)):
                files.append((f, os.path.relpath(f, spec).replace("\\", "/")))
        else:
            matches = sorted(glob.glob(spec, recursive=True))
            if not matches:
                print(f"nothing matches {spec}", file=sys.stderr)
            for f in matches:
                files.append((f, os.path.basename(f)))
    return files


def checker(w, h, s=8):
    im = Image.new("RGB", (w, h), (90, 90, 90))
    d = ImageDraw.Draw(im)
    for y in range(0, h, s):
        for x in range((y // s) % 2 * s, w, 2 * s):
            d.rectangle((x, y, x + s - 1, y + s - 1), fill=(120, 120, 120))
    return im


def render(path, scale, cap, tile):
    im = Image.open(path).convert("RGBA")
    if tile:
        t = Image.new("RGBA", (im.width * 3, im.height * 3))
        for j in range(3):
            for i in range(3):
                t.paste(im, (i * im.width, j * im.height))
        im = t
    s = scale
    while s > 1 and max(im.width, im.height) * s > cap:
        s -= 1
    big = im.resize((im.width * s, im.height * s), Image.NEAREST)
    if max(big.width, big.height) > cap:  # still too big at 1x: shrink smoothly, and say so
        k = cap / max(big.width, big.height)
        big = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))), Image.LANCZOS)
        s = k
    base = checker(big.width, big.height)
    base.paste(big, (0, 0), big)
    return base, s


def sheet(entries, refs, out, scale, cap, tile, cols):
    """entries: [(path, label)], refs: [(path, label)] -> writes out."""
    rendered = []
    for path, label in refs:
        im, s = render(path, scale, cap, tile)
        rendered.append((im, label, s, path, True))
    nrefs = len(rendered)
    for path, label in entries:
        try:
            im, s = render(path, scale, cap, tile)
        except OSError as e:
            print(f"cannot read {path}: {e}", file=sys.stderr)
            continue
        rendered.append((im, label, s, path, False))
    if not rendered:
        return None
    # Flow layout: each tile as wide as it is (at least 128 px, for the label), rows as tall as their tallest tile;
    # the references on their own first row(s), then the textures. --cols fixes the number per row instead.
    width = 2000
    places, x, y, row_h, k_in_row = [], PAD, PAD, 0, 0
    for i, (im, label, s, path, is_ref) in enumerate(rendered):
        w = max(im.width, 128)
        new_row = (x + w > width and k_in_row > 0) or (cols and k_in_row >= cols) or (i == nrefs and nrefs > 0)
        if new_row:
            x, y, k_in_row = PAD, y + row_h + LABEL_H + PAD, 0
            row_h = 0
        places.append((x, y, w))
        x += w + PAD
        k_in_row += 1
        row_h = max(row_h, im.height)
    W = max(p[0] + p[2] for p in places) + PAD
    H = y + row_h + LABEL_H + PAD
    sh = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sh)
    f = font(12)
    for (im, label, s, path, is_ref), (x, y, cell) in zip(rendered, places):
        sh.paste(im, (x, y))
        if is_ref:
            d.rectangle((x - 3, y - 3, x + im.width + 2, y + im.height + 2), outline=REF_FRAME, width=2)
        w0, h0 = Image.open(path).size
        size = f"{w0}x{h0}" + ("" if s == scale else (f" @{s}x" if isinstance(s, int) else " shrunk"))
        name = ("vanilla " if is_ref else "") + label
        maxch = max(8, cell // 7)
        d.text((x, y + im.height + 2), name[:maxch], fill=REF_FRAME if is_ref else (235, 235, 235), font=f)
        line = 15
        if len(name) > maxch:
            d.text((x, y + im.height + line), name[maxch:maxch * 2], fill=REF_FRAME if is_ref else (235, 235, 235), font=f)
            line += 13
        d.text((x, y + im.height + line), size, fill=(160, 160, 160), font=f)
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    sh.save(out)
    return out


# --all: one set of sheets per folder under assets/backrooms/textures, each with the vanilla references that are its
# obvious counterparts (stone, planks, brick, cloth, metal, plaster, wallpaper); folders with none get none
STONE, BRICK, PLANKS = "block/stone/cobblestone/granite1", "block/stone/brick/andesite1", "block/wood/planks/oak1"
WOOL, CARPET, PLASTER = "block/cloth/wool/gray1", "block/cloth/mediumcarpet/blue", "block/stone/plaster/plain"
IRON, RIVETED, WALLPAPER = "block/metal/plate/iron", "block/metal/riveted/copper3", "block/wallpaper/aged/walnut"
FOLDER_REFS = {
    "block": [CARPET, PLASTER, STONE], "block/level1": [STONE, IRON, PLASTER], "block/level2": [STONE, BRICK, IRON],
    "block/level3": [BRICK, RIVETED, PLASTER], "block/level4": [WOOL, PLANKS, PLASTER],
    "block/level5": ["block/cloth/wool/red1", PLANKS, "block/metal/plate/brass"], "block/props": [IRON, RIVETED],
    "block/wallpaper": [WALLPAPER, PLASTER], "block/detail": [STONE, PLANKS, IRON],
    "block/run": [PLASTER, IRON, WOOL], "block/fun": [CARPET, PLANKS, PLASTER], "block/end": [PLASTER, IRON, STONE],
    "block/hub": [STONE, BRICK, PLANKS], "block/974": [WALLPAPER, PLANKS, WOOL], "block/3999": [STONE, IRON, CARPET],
    "block/188": [BRICK, PLASTER, IRON],
}
TEXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "backrooms", "textures")


def make(entries, refs, out, a):
    cap = a.max * 3 if a.tile else a.max  # a 3x3 repeat gets three times the room
    pages = [entries]
    if a.per_page and len(entries) > a.per_page:
        pages = [entries[i:i + a.per_page] for i in range(0, len(entries), a.per_page)]
    stem, ext = os.path.splitext(out)
    for n, page in enumerate(pages, 1):
        o = out if len(pages) == 1 else f"{stem}-{n}{ext or '.png'}"
        sheet(page, refs, o, a.scale, cap, a.tile, a.cols)
        print(f"{o}: {len(page)} textures" + (f", {len(refs)} references" if refs else ""))


def ref_entries(names):
    out = []
    for r in names:
        p = find_ref(r)
        out.append((p, os.path.relpath(p, VANILLA).replace("\\", "/")[:-4] if p.startswith(VANILLA) else os.path.basename(p)))
    return out


def main():
    ap = argparse.ArgumentParser(description="Contact sheet of textures at 4x nearest-neighbour")
    ap.add_argument("inputs", nargs="*")
    ap.add_argument("--out", help="the sheet (with --all: the folder for every folder's sheets)")
    ap.add_argument("--ref", nargs="*", default=[])
    ap.add_argument("--tile", action="store_true")
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--max", type=int, default=256, help="largest side of a tile on the sheet, in px")
    ap.add_argument("--cols", type=int)
    ap.add_argument("--per-page", type=int, default=0)
    ap.add_argument("-r", "--recursive", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="every folder under assets/backrooms/textures into --out/<folder>.png (paged), with its references")
    a = ap.parse_args()
    if not a.out:
        sys.exit("--out is required")
    if a.all:
        root = os.path.abspath(TEXTURES)
        for folder, _, files in sorted(os.walk(root)):
            if not any(f.endswith(".png") for f in files):
                continue
            rel = os.path.relpath(folder, root).replace("\\", "/")
            name = rel.replace("/", "-") + ("-tile" if a.tile else "")
            make(collect([folder], False), ref_entries(FOLDER_REFS.get(rel, [])), os.path.join(a.out, name + ".png"), a)
        return
    entries = collect(a.inputs, a.recursive)
    if not entries:
        sys.exit("no textures")
    make(entries, ref_entries(a.ref), a.out, a)


if __name__ == "__main__":
    main()
