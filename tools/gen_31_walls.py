"""Level 31, "Roller Rink": the cladding on the neon halls' walls (round 2, beside gen_31.py and gen_31_props.py).

It writes only its own files:
    blocktypes/31/l31-cladding.json   a thin panel (one texture pixel thick) against the wall behind its block, the picture
                                      toward the side named (modelled facing north, the wall to the south):
        m<c><r>       one block of the hall mural, 6 wide and 4 high (c 0-5 from the viewer's left, r 0-3 from the top): a
                      1990s rink mural in UV-bright paint on gloss black (zigzags, squiggles, triangles, rings, confetti),
                      seamless left to right; its paint glows a little, as blacklight paint does
        f<tl..br>     a chrome-framed wall mirror, 2 wide and 3 high (t m b by l r, as seen from in front)
        lacq, lacqtop black lacquer panels between the mirrors (lacqtop with the chrome trim along its top)
        dj<c><r>      the DJ station's neon sign on the wall behind it, 3 wide and 2 high (lit, pink)
        exit          a cinema's red EXIT sign over its door (lit, dim red)
        crt           a small wall-hung TV in a cinema, showing the same sunset as the big one (lit, dim)
    shapes/block/31/l31-cladding.json and textures/block/31/clad-*.png

Run from the repo root:  bash tools/locked.sh run python tools/gen_31_walls.py
"""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

from modelkit import box
from texlib import S
from gen_31 import write_json, shape, SIDES, TEX, BLOCKS, GLASS

ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
COLS, ROWS = 6, 4
PAINT = [(255, 60, 178), (40, 226, 226), (255, 222, 48), (156, 92, 255), (150, 255, 84), (255, 140, 46)]
BASE = (16, 14, 30)


def clamp(v):
    return max(0, min(255, int(round(v))))


def save(img, name):
    os.makedirs(TEX, exist_ok=True)
    img.save(os.path.join(TEX, name + ".png"))


def wrap_draw(img, fn):
    """Draws fn(draw, dx) three times, shifted a mural's width either way, so what crosses the right edge comes back on the left."""
    d = ImageDraw.Draw(img)
    w = img.size[0]
    for dx in (-w, 0, w):
        fn(d, dx)


def mural():
    """The hall mural: 192 x 128 px (6 x 4 blocks), seamless left to right."""
    W, H = COLS * S, ROWS * S
    img = Image.new("RGBA", (W, H), BASE + (255,))
    px = img.load()
    # Gloss: a soft vertical sheen and a darker foot
    for y in range(H):
        for x in range(W):
            k = 1 + 0.22 * math.exp(-((y - 26) / 18.0) ** 2) + 0.06 * math.sin(2 * math.pi * x / W * 3)
            if y > H - 12:
                k *= 0.8
            px[x, y] = tuple(clamp(c * k) for c in BASE) + (255,)
    rng = random.Random(3161)
    paint = ImageDraw.Draw(img)

    # The big zigzag band across the middle (pink over a violet shadow) and a teal wave above it
    def zigzag(d, dx):
        pts = [(dx + i * 16, 74 + (12 if i % 2 else -12)) for i in range(-1, W // 16 + 2)]
        d.line([(x + 2, y + 3) for x, y in pts], fill=PAINT[3] + (255,), width=6)
        d.line(pts, fill=PAINT[0] + (255,), width=5)
    wrap_draw(img, zigzag)

    def wave(d, dx):
        pts = [(dx + x, 34 + 7 * math.sin(2 * math.pi * x / (W / 3))) for x in range(0, W + 1, 2)]
        d.line(pts, fill=PAINT[1] + (255,), width=4)
        pts2 = [(dx + x, 42 + 7 * math.sin(2 * math.pi * x / (W / 3))) for x in range(0, W + 1, 2)]
        d.line(pts2, fill=(20, 120, 140, 255), width=2)
    wrap_draw(img, wave)

    # Scattered shapes, kept off the bands a little: triangles, rings, squiggles, dots, sparkles
    shapes = []
    for _ in range(46):
        x, y = rng.randrange(W), rng.randrange(6, H - 14)
        if 60 <= y <= 88 and rng.random() < 0.7:
            continue
        shapes.append((rng.choice("ttrrsdddkk"), x, y, rng.choice(PAINT), rng.uniform(0, 2 * math.pi), rng.randint(4, 8)))

    def scatter(d, dx):
        for kind, x, y, c, a, r in shapes:
            x += dx
            if kind == "t":  # a solid triangle
                pts = [(x + r * math.cos(a + k * 2 * math.pi / 3), y + r * math.sin(a + k * 2 * math.pi / 3)) for k in range(3)]
                d.polygon(pts, fill=c + (255,))
            elif kind == "r":  # a ring
                d.ellipse([x - r, y - r, x + r, y + r], outline=c + (255,), width=2)
            elif kind == "s":  # a squiggle
                pts = [(x + k * 2 - 8, y + 3 * math.sin(k * 1.1 + a)) for k in range(9)]
                d.line(pts, fill=c + (255,), width=2)
            elif kind == "k":  # a four-point sparkle
                d.line([(x - r, y), (x + r, y)], fill=(250, 250, 255, 255), width=1)
                d.line([(x, y - r), (x, y + r)], fill=(250, 250, 255, 255), width=1)
                d.point((x, y), fill=c + (255,))
            else:  # confetti dots
                d.rectangle([x, y, x + 1, y + 1], fill=c + (255,))
    wrap_draw(img, scatter)

    # The chrome trim along the top and a dark rule at the foot
    for x in range(W):
        for y, c in ((0, (120, 126, 140)), (1, (226, 230, 240)), (2, (170, 176, 190)), (3, (40, 40, 52))):
            px[x, y] = c + (255,)
        px[x, H - 1] = (8, 8, 14, 255)
    # A fine grain so it is paint, not print
    g = random.Random(3162)
    for y in range(H):
        for x in range(W):
            r, gg, b, a = px[x, y]
            n = g.uniform(-3, 3)
            px[x, y] = (clamp(r + n), clamp(gg + n), clamp(b + n), a)
    for c in range(COLS):
        for r in range(ROWS):
            save(img.crop((c * S, r * S, c * S + S, r * S + S)), f"clad-m{c}{r}")


def mirror():
    """A wall mirror, 64 x 96 px (2 x 3 blocks): silvered glass with streaks and a blur of the hall's neon, a chrome frame."""
    W, H = 2 * S, 3 * S
    img = Image.new("RGBA", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            t = y / (H - 1)
            base = (int(150 - 60 * t), int(162 - 58 * t), int(190 - 50 * t))
            k = 1 + 0.35 * math.exp(-(((x - 0.6 * y) - 6) / 4.0) ** 2) + 0.2 * math.exp(-(((x - 0.6 * y) + 22) / 2.5) ** 2)
            px[x, y] = tuple(clamp(c * k) for c in base) + (255,)
    # The reflected hall: a dim floor band with the neon strip's dashes, the far tubes as soft dots
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    d.rectangle([0, H - 20, W, H], fill=(30, 26, 52, 150))
    for x in range(2, W, 7):
        d.rectangle([x, H - 13, x + 3, H - 11], fill=(120, 230, 255, 230))
    for x, c in ((16, (255, 90, 200)), (40, (90, 230, 255)), (54, (255, 90, 200))):
        d.ellipse([x - 3, 10, x + 3, 14], fill=c + (200,))
    glow = glow.filter(ImageFilter.GaussianBlur(1.2))
    img.alpha_composite(glow)
    # The frame: chrome, lit from the top left
    for i in range(3):
        c = (232 - 30 * i, 236 - 30 * i, 244 - 30 * i)
        for x in range(i, W - i):
            px[x, i] = c + (255,)
            px[x, H - 1 - i] = tuple(clamp(v * 0.75) for v in c) + (255,)
        for y in range(i, H - i):
            px[i, y] = c + (255,)
            px[W - 1 - i, y] = tuple(clamp(v * 0.8) for v in c) + (255,)
    for x in range(3, W - 3):
        px[x, 3] = (40, 42, 54, 255)
    for y in range(3, H - 3):
        px[3, y] = (40, 42, 54, 255)
    for r, rn in enumerate("tmb"):
        for c, cn in enumerate("lr"):
            save(img.crop((c * S, r * S, c * S + S, r * S + S)), f"clad-f{rn}{cn}")


def lacquer():
    """Black lacquer between the mirrors: a soft vertical highlight; the top one with the chrome trim."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(3163)
    for y in range(S):
        for x in range(S):
            k = 1 + 0.5 * math.exp(-((x - 11) / 5.0) ** 2) * (0.6 + 0.4 * y / S)
            n = rng.uniform(-2, 2)
            px[x, y] = (clamp(20 * k + n), clamp(20 * k + n), clamp(30 * k + n), 255)
    save(img, "clad-lacq")
    top = img.copy()
    p = top.load()
    for x in range(S):
        for y, c in ((0, (120, 126, 140)), (1, (226, 230, 240)), (2, (170, 176, 190)), (3, (40, 40, 52))):
            p[x, y] = c + (255,)
    save(top, "clad-lacqtop")
    edge = Image.new("RGBA", (S, S), (170, 176, 190, 255))
    save(edge, "clad-edge")


def signs():
    """The DJ station's neon sign (96 x 64: "DJ" in pink tube lettering, cyan notes either side) and the cinema's EXIT sign."""
    from gen_31_props import text, textw
    W, H = 3 * S, 2 * S
    img = Image.new("RGBA", (W, H), (14, 12, 22, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    w = textw("DJ", 6)
    text(glow, (W - w) // 2, 16, "DJ", (255, 70, 190), 6, 6)
    d = ImageDraw.Draw(glow)
    for x0 in (4, W - 18):  # two quavers
        d.ellipse([x0, 40, x0 + 7, 46], fill=(70, 230, 255, 255))
        d.line([(x0 + 7, 43), (x0 + 7, 22)], fill=(70, 230, 255, 255), width=2)
        d.line([(x0 + 7, 22), (x0 + 13, 27)], fill=(70, 230, 255, 255), width=2)
    halo = glow.filter(ImageFilter.GaussianBlur(2.5))
    img.alpha_composite(halo)
    img.alpha_composite(halo)
    img.alpha_composite(glow)
    # (a white-hot core down the middle of each tube)
    px, cp = img.load(), glow.load()
    for y in range(1, H - 1):
        for x in range(1, W - 1):
            if cp[x, y][3] and cp[x - 1, y][3] and cp[x + 1, y][3] and cp[x, y - 1][3] and cp[x, y + 1][3]:
                r, g, b, a = px[x, y]
                px[x, y] = (clamp(r * 0.5 + 128), clamp(g * 0.5 + 128), clamp(b * 0.5 + 128), 255)
    for c in range(3):
        for r in range(2):
            save(img.crop((c * S, r * S, c * S + S, r * S + S)), f"clad-dj{c}{r}")
    ex = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(ex)
    d.rectangle([2, 9, 29, 22], fill=(30, 28, 30, 255))
    d.rectangle([3, 10, 28, 21], fill=(60, 10, 12, 255))
    text(ex, 16 - textw("EXIT", 1) // 2, 13, "EXIT", (255, 60, 50), 1, 1)
    save(ex, "clad-exit")
    tv = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tv)
    d.rounded_rectangle([3, 6, 28, 25], 2, fill=(48, 46, 50, 255))
    d.rectangle([13, 25, 18, 27], fill=(40, 38, 42, 255))  # the bracket
    for y in range(8, 23):  # a sunset over hills, with scanlines
        t = (y - 8) / 14
        c = (int(70 + 170 * t), int(50 + 60 * t), int(140 - 60 * t))
        if y % 2:
            c = tuple(int(v * 0.8) for v in c)
        d.line([(5, y), (26, y)], fill=c + (255,))
    d.ellipse([12, 13, 19, 20], fill=(255, 220, 140, 255))
    d.polygon([(5, 22), (11, 16), (17, 21), (22, 17), (26, 22)], fill=(40, 24, 60, 255))
    save(tv, "clad-crt")


def blocktype():
    kinds = [f"m{c}{r}" for c in range(COLS) for r in range(ROWS)] + [f"f{r}{c}" for r in "tmb" for c in "lr"] + ["lacq", "lacqtop"]         + [f"dj{c}{r}" for c in range(3) for r in range(2)] + ["exit", "crt"]
    # One shape (the panel at the south edge of its block, its picture facing north), the picture by type
    # (the mural's paint glows a little, as UV paint under the halls' neon does)
    def panel(glow):
        el = box("Panel", (0, 0, 15.5), (16, 16, 16), {"front": "art", "all": "edge"}, faces=("north", "east", "west", "up", "down"), glow=glow)
        if glow == 255:  # (a lit sign's picture glows, not its rim)
            for f in ("east", "west", "up", "down"):
                el["faces"][f].pop("glow", None)
        return el
    refs = {glow: shape("l31-cladding" + ("-glow" if glow == 48 else "-lit" if glow else ""), [panel(glow)]) for glow in (0, 48, 255)}
    shapes, textures, sels = {}, {}, {}
    for k in kinds:
        for side in SIDES:
            key = f"l31-cladding-{k}-{side}"
            ref = refs[48 if k.startswith("m") else 255 if k.startswith(("dj", "exit", "crt")) else 0]
            shapes[key] = {"base": ref, "rotateY": ROT[side]} if ROT[side] else {"base": ref}
            sel = {"x1": 0, "y1": 0, "z1": 0.96875, "x2": 1, "y2": 1, "z2": 1}
            if ROT[side]:
                sel["rotateY"] = ROT[side]
            sels[key] = sel
        textures[f"*-{k}-*"] = {"art": {"base": "backrooms:block/31/clad-" + k}, "edge": {"base": "backrooms:block/31/clad-edge"}}
    light = {f"l31-cladding-{k}-*": ([51, 6, 9] if k.startswith("dj") else [0, 7, 5] if k == "exit" else [36, 3, 7])
             for k in kinds if k.startswith(("dj", "exit", "crt"))}
    data = {"code": "l31-cladding", "lightHsvByType": light, "variantgroups": [{"code": "kind", "states": kinds}, {"code": "side", "states": SIDES}],
            "shapeByType": shapes, "texturesByType": textures,
            "creativeinventory": {"general": ["*"], "backrooms": ["*"]},
            "blockmaterial": "Glass", "drawtype": "json", "sidesolid": {"all": False}, "sideopaque": {"all": False},
            "lightAbsorption": 0, "resistance": 3, "drops": [], "sounds": GLASS,
            "selectionboxByType": sels, "collisionboxByType": sels}
    write_json(os.path.join(BLOCKS, "l31-cladding.json"), data,
               "Level 31: the halls' wall cladding, a thin panel against the wall behind its block, picture toward the side: the mural "
               "(m<col><row>, 6 x 4 blocks), a chrome-framed mirror (f<row><col>, 2 x 3) and black lacquer (lacq, lacqtop)")


def main():
    mural()
    mirror()
    lacquer()
    signs()
    blocktype()
    print("Level 31 cladding: textures in", os.path.relpath(TEX), "; blocktype in", os.path.relpath(BLOCKS))


if __name__ == "__main__":
    main()
