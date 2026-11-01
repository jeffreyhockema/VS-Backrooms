"""The Basement, round 3 (2026-11-01): the house's rooms by what they are for, as objects of several blocks, and the
writing a real basement has on it. Called by tools/gen_basement.py (`textures()` and `blocks()`), which empties the
level's folders first; run it through that:

    bash tools/locked.sh run python tools/gen_basement.py

New blocks (all `basement-`):
    furnace    an old "octopus" gravity furnace: its round body (lower, upper) and, in the block over it, its ducts
               rising into the joists, lagged in white (top); a cast maker's plate on its fire door
    heater     a water heater: the tank (lower, upper) and its flue and pipes going up, tagged HOT and COLD (top)
    bench      a workbench two tiles long (l, r) with a vice and its tools; the pegboard over it is a `basement-wallthing`
    pooltable  the rec room's pool table, two tiles long (l, r); `basement-poollamp` hangs over each half
    shelving   steel shelving two blocks high (lower, upper), loaded with boxes, jars or paint cans
    boxes      cardboard boxes stacked two high (lower, upper), labelled in marker
    winerack   a wine rack two blocks high (lower, upper), dusty bottles in most cubbies
    sump       the sump pit: an iron grate in the floor over black water
    wallthing  things on a wall at head height, in the block in front of it: a pegboard of tools (a, b), the fuse box
               (its door hanging open on hand-labelled breakers) and the conduit up from it, caution signs (CAUTION,
               WATCH YOUR HEAD, DANGER DEEP WATER), a calendar, a coal chute's hatch with its trough
    overhead   in the top block of air: a clothesline (bare, a shirt, a sheet, a towel; along x or z), a cobweb in a
               corner
    poollamp   the long green shade hung over the pool table (lit)
    studs      an unfinished wall: bare studs, fibreglass batts stapled between them
    earth      a root cellar's floor of trodden earth
    rug        a braided rag rug
The swollen-shut doors get a board nailed across them with DO NOT ENTER on it (gen_basement.door_blocks).
"""
import os
import zlib

from PIL import Image, ImageDraw, ImageFont

import matlib as M
import modelkit as K

ROOT = os.path.join(os.path.dirname(__file__), "..")
ASSETS = os.path.join(ROOT, "assets", "backrooms")
TEX = os.path.join(ASSETS, "textures", "block", "basement")
SHAPES = os.path.join(ASSETS, "shapes", "block", "basement")
BLOCKS = os.path.join(ASSETS, "blocktypes", "basement")
FONTS = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")

ROT = {"north": 0, "east": 270, "south": 180, "west": 90}
RUST = (122, 72, 40)
RUSTDARK = (78, 48, 30)
WOOD = {"walk": "game:walk/wood", "place": "game:block/planks", "break": "game:block/planks", "hit": "game:block/planks"}
METAL = {"walk": "game:walk/stone", "place": "game:block/anvil1", "break": "game:block/heavymetal-hit", "hit": "game:block/heavymetal-hit"}
STONE = {"walk": "game:walk/stone", "place": "game:block/loosestone", "break": "game:block/rock-break-pickaxe", "hit": "game:block/rock-hit-pickaxe"}
CLOTH = {"walk": "game:walk/cloth", "place": "game:block/cloth", "break": "game:block/cloth", "hit": "game:block/cloth"}
SCRAP = [{"type": "item", "code": "metalbracket", "quantity": {"avg": 0.6, "var": 0.4}},
         {"type": "item", "code": "scrapwire", "quantity": {"avg": 0.4, "var": 0.4}}]
STICKS = [{"type": "item", "code": "game:stick", "quantity": {"avg": 1.5, "var": 1}}]

LANG = {}

# Texture keys to paths: the level's own, and a few of the mod's
T = {k: "backrooms:block/basement/" + k for k in (
    "furnace", "furnacedoor", "furnaceplate", "lagging", "heater", "heaterplate", "copper", "pipetags", "benchtop",
    "pegboard", "fusebox", "fuseinside", "sign-caution", "sign-head", "sign-water", "calendar", "box-xmas", "box-taxes",
    "box-moms", "box-keep", "paintcan", "studs", "insulation", "rug", "floor-earth", "cobweb", "cloth-shirt",
    "cloth-sheet", "cloth-towel", "doorboard", "poolshade", "balls", "chute", "sumpwater", "grate", "rope", "bottle",
    "jar", "panel", "floor-dry", "duct", "wall-plain", "cage", "bulb-lit")}
T.update({"metal": "backrooms:block/props/metal", "metaldark": "backrooms:block/props/metal-dark",
          "cardboard": "backrooms:block/supplybox-side", "cardboardtop": "backrooms:block/supplybox-top",
          "felt": "backrooms:block/level5/felt", "mahogany": "backrooms:block/level5/mahogany",
          "brass": "backrooms:block/level5/brass", "redpaint": "backrooms:block/basement/crowbar",
          "lobbycarpet": "backrooms:block/carpet-soaked"})


def save(img, name):
    img.save(os.path.join(TEX, name + ".png"))


def font(name, px):
    try:
        return ImageFont.truetype(os.path.join(FONTS, name), px)
    except OSError:
        return ImageFont.load_default(size=px)


def write_text(img, lines, box, fontname, color, max_px=40, rotate=0.0, seed=0):
    """Draws `lines` as large as fits `box` (x0, y0, x1, y1) on `img`, centred, one font size for all."""
    x0, y0, x1, y1 = box
    px = max_px
    while px > 5:
        f = font(fontname, px)
        sizes = [f.getbbox(s) for s in lines]
        w = max(b[2] - b[0] for b in sizes)
        lh = max(b[3] - b[1] for b in sizes) * 1.15
        if w <= x1 - x0 and lh * len(lines) <= y1 - y0:
            break
        px -= 1
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    top = y0 + ((y1 - y0) - lh * len(lines)) / 2
    for i, s in enumerate(lines):
        b = f.getbbox(s)
        d.text((x0 + ((x1 - x0) - (b[2] - b[0])) / 2 - b[0], top + i * lh - b[1]), s, font=f, fill=color)
    if rotate:
        layer = layer.rotate(rotate, resample=Image.BICUBIC, center=((x0 + x1) / 2, (y0 + y1) / 2))
    img.alpha_composite(layer)
    return img


def rgba(img):
    return img.convert("RGBA")


# ======================================================================== Textures

def textures():
    S2 = 64
    # The furnace: cream enamel gone yellow, rust bleeding at its seams; its fire door dark cast iron, vents cut in it
    f = M.painted_metal(seed=301, base=(150, 142, 116), panel=False, chips=6, under=(90, 70, 52))
    M.rust(f, 0.25, seed=302, color=RUST, dark=RUSTDARK, cells=(8, 4, 2))
    M.grime(f, 0.3, seed=303, color=(70, 64, 52), cells=(8, 4), cover=0.6)
    save(f, "furnace")
    d = M.painted_metal(seed=304, base=(46, 44, 42), panel=False, chips=2, under=(80, 50, 34))
    M.rust(d, 0.3, seed=305, color=RUST, dark=RUSTDARK, cells=(4, 2))
    dd = ImageDraw.Draw(d)
    for y in (6, 10, 14):
        dd.rectangle([9, y, 22, y + 1], fill=(14, 12, 10))
    save(d, "furnacedoor")
    # Its cast plate: raised letters on dull brass (the maker is invented; Cincinnati is the clipping's city)
    p = rgba(M.painted_metal(seed=306, size=S2, base=(150, 124, 70), panel=False, chips=0, under=(80, 60, 40)))
    ImageDraw.Draw(p).rectangle([0, 0, 63, 31], outline=(40, 30, 16), width=2)
    write_text(p, ["HEARTHMASTER"], (3, 3, 61, 17), "arialbd.ttf", (28, 20, 10, 255), 16)
    write_text(p, ["No.6  CINCINNATI, O."], (3, 18, 61, 29), "arialbd.ttf", (28, 20, 10, 255), 10)
    save(p, "furnaceplate")
    # Asbestos lagging on the ducts: dirty white cloth, banded
    lag = M.fabric(seed=307, base=(188, 184, 170), weave="plain", contrast=8, grain=3, mottle=6)
    M.grime(lag, 0.35, seed=308, color=(120, 112, 94), cells=(8, 4, 2), cover=0.6)
    M.emboss_lines(lag, ys=(0, 15, 16, 31), strength=0.25)
    save(lag, "lagging")
    # The water heater: white enamel gone grey, a brown drip line from its drain
    h = M.painted_metal(seed=311, base=(170, 170, 162), panel=False, chips=3, under=(96, 76, 56))
    M.drips(h, n=2, seed=312, color=(110, 72, 40), length=(10, 24), strength=0.4, width=2)
    M.grime(h, 0.28, seed=313, color=(90, 86, 74), cells=(8, 4), cover=0.55)
    save(h, "heater")
    hp = rgba(M.paper(seed=314, size=S2, base=(206, 200, 178)))
    dh = ImageDraw.Draw(hp)
    dh.rectangle([0, 0, 63, 11], fill=(30, 52, 104))
    write_text(hp, ["RHEEMCO"], (2, 1, 62, 11), "arialbd.ttf", (230, 230, 220, 255), 10)
    write_text(hp, ["MODEL 40-G", "40 GAL  GAS", "TEMP: 130 F", "INSTALLED 1987"], (3, 14, 61, 48), "arialbd.ttf", (40, 38, 34, 255), 8)
    dh.rectangle([2, 50, 61, 62], fill=(220, 180, 30))
    write_text(hp, ["DANGER  HOT"], (4, 51, 60, 62), "arialbd.ttf", (20, 18, 14, 255), 10)
    save(hp, "heaterplate")
    cu = M.brushed_metal(seed=315, base=(150, 96, 62), direction="v", streak=6, sheen=8)
    M.grime(cu, 0.35, seed=316, color=(60, 84, 70), cells=(4, 2), cover=0.35)  # verdigris
    save(cu, "copper")
    # Pipe tags: the top half HOT (red), the bottom COLD (blue), stencilled
    tg = Image.new("RGBA", (S2, S2), (0, 0, 0, 255))
    dt = ImageDraw.Draw(tg)
    dt.rectangle([0, 0, 63, 31], fill=(176, 44, 34))
    dt.rectangle([0, 32, 63, 63], fill=(40, 78, 150))
    write_text(tg, ["HOT"], (4, 4, 60, 28), "STENCIL.TTF", (240, 232, 214, 255), 24)
    write_text(tg, ["COLD"], (4, 36, 60, 60), "STENCIL.TTF", (240, 232, 214, 255), 24)
    save(tg, "pipetags")
    # The workbench top: thick boards, oil and paint on them
    bt = M.wood_planks(seed=321, base=(118, 92, 62), planks=4, direction="h", grain=4, per_plank=8, gap=(44, 32, 22))
    M.stain(bt, seed=322, radius=6, color=(40, 34, 28), strength=0.5)
    M.stain(bt, seed=323, radius=3, color=(150, 40, 30), strength=0.4)
    M.scratches(bt, n=10, seed=324, length=(3, 8), light=0.2)
    save(bt, "benchtop")
    # The pegboard: brown hardboard, its holes, outlines of the tools drawn where they hang, some gone
    pb = rgba(M.noise_hv((112, 82, 52), 4, seed=325, size=S2, mottle=5))
    dp = ImageDraw.Draw(pb)
    for y in range(3, 64, 6):
        for x in range(3, 64, 6):
            dp.rectangle([x, y, x + 1, y + 1], fill=(40, 28, 18))
    for (x0, y0, x1, y1) in ((8, 10, 14, 44), (40, 8, 46, 36), (22, 40, 34, 46)):
        dp.rectangle([x0, y0, x1, y1], outline=(26, 22, 18))
    M.grime(pb, 0.3, seed=326, color=(70, 60, 48), cells=(8, 4), cover=0.5)
    save(pb, "pegboard")
    # The fuse box: grey enamel; inside, two rows of breakers, each with a strip of tape and a word in pencil
    fb = M.painted_metal(seed=331, base=(112, 116, 112), panel=True, chips=3, under=(80, 64, 50), screws=True)
    M.grime(fb, 0.2, seed=332, color=(70, 68, 60), cells=(8, 4), cover=0.5)
    save(fb, "fusebox")
    fi = rgba(M.painted_metal(seed=333, size=S2, base=(96, 100, 98), panel=False, chips=1))
    di = ImageDraw.Draw(fi)
    labels = ["FURNACE", "WASHER", "KITCHEN", "BSMT LTS", "PUMP", "?", "UPSTAIRS", "DON'T"]
    for k, lab in enumerate(labels):
        col, row = k % 2, k // 2
        x, y = 3 + col * 31, 3 + row * 15
        di.rectangle([x, y, x + 6, y + 11], fill=(28, 28, 28))      # the breaker
        di.rectangle([x + 2, y + (2 if k % 3 else 6), x + 4, y + (5 if k % 3 else 9)], fill=(200, 196, 186))  # its toggle
        di.rectangle([x + 8, y + 2, x + 28, y + 10], fill=(214, 204, 168))  # masking tape
        write_text(fi, [lab], (x + 9, y + 2, x + 28, y + 10), "Inkfree.ttf", (40, 38, 60, 255), 10)
    save(fi, "fuseinside")
    # Caution signs (Fandom: "caution signs" among the things in the Basement that serve no purpose)
    for name, top, body, band in (("sign-caution", "CAUTION", ["KEEP OUT"], (232, 186, 30)),
                                  ("sign-head", "CAUTION", ["WATCH", "YOUR HEAD"], (232, 186, 30)),
                                  ("sign-water", "DANGER", ["DEEP WATER", "NO WADING"], (190, 36, 30))):
        s = Image.new("RGBA", (S2, S2), (236, 232, 218, 255))
        ds = ImageDraw.Draw(s)
        ds.rectangle([0, 0, 63, 15], fill=band + (255,))
        write_text(s, [top], (2, 1, 62, 15), "arialbd.ttf", (244, 240, 230, 255) if top == "DANGER" else (20, 20, 20, 255), 13)
        write_text(s, body, (3, 18, 61, 41), "arialbd.ttf", (20, 20, 20, 255), 12)
        s = s
        M.grime(s, 0.25, seed=zlib.crc32(name.encode()) % 1000, color=(110, 96, 70), cells=(8, 4), cover=0.5)
        M.rust(s, 0.12, seed=zlib.crc32(name.encode()) % 997, color=RUST, dark=RUSTDARK, cells=(4, 2))
        save(s, name)
    # A calendar on a nail, stopped at January 1951 (the clipping's muddled date), days crossed off to the 6th
    c = rgba(M.paper(seed=341, size=S2, base=(214, 206, 176)))
    dc = ImageDraw.Draw(c)
    write_text(c, ["JANUARY 1951"], (3, 2, 61, 11), "arialbd.ttf", (120, 30, 26, 255), 10)
    for k in range(31):
        col, row = (k + 1) % 7, (k + 1) // 7
        x, y = 4 + col * 8, 14 + row * 9
        dc.rectangle([x, y, x + 6, y + 7], outline=(150, 140, 120))
        if k < 6:
            dc.line([x, y, x + 6, y + 7], fill=(40, 40, 50), width=1)
            dc.line([x + 6, y, x, y + 7], fill=(40, 40, 50), width=1)
    cc = c
    M.grime(cc, 0.3, seed=342, color=(130, 110, 70), cells=(8, 4), cover=0.6)
    M.tideline(cc, 52, seed=343, color=(120, 100, 64), amount=0.4, wave=1.5, below=0.8)
    save(cc, "calendar")
    # Boxes, labelled in marker
    for k, (name, words) in enumerate((("box-xmas", ["XMAS"]), ("box-taxes", ["TAXES", "'84-'91"]), ("box-moms", ["MOM'S", "DON'T"]),
                                        ("box-keep", ["KEEP"]))):
        b = rgba(M.noise_hv((156, 124, 82), 4, seed=351 + k, size=S2, mottle=6))
        db = ImageDraw.Draw(b)
        db.rectangle([0, 28, 63, 34], fill=(176, 160, 120))  # tape
        write_text(b, words, (8, 38, 56, 62), "segoeprb.ttf", (24, 22, 26, 255), 18, rotate=(k * 7) % 9 - 4)
        bb = b
        M.grime(bb, 0.3, seed=360 + k, color=(90, 78, 60), cells=(8, 4), cover=0.55)
        M.tideline(bb, 56, seed=365 + k, color=(96, 76, 50), amount=0.35, wave=1.2, below=0.9)
        save(bb, name)
    # Paint cans: labels in faded colours round a tin body, a drip down one side
    pc = M.brushed_metal(seed=371, base=(150, 150, 146), direction="v")
    dpc = ImageDraw.Draw(pc)
    for x0, col in ((0, (150, 60, 50)), (8, (70, 96, 130)), (16, (196, 186, 150)), (24, (80, 110, 70))):
        dpc.rectangle([x0, 9, x0 + 7, 24], fill=col)
    M.drips(pc, n=3, seed=372, color=(210, 206, 196), length=(4, 10), strength=0.6)
    M.grime(pc, 0.3, seed=373, color=(70, 64, 56), cells=(8, 4), cover=0.5)
    save(pc, "paintcan")
    # The studs and the batts between them
    st = M.wood_planks(seed=381, base=(150, 120, 82), planks=1, direction="v", grain=4, per_plank=6, gap=(60, 46, 30))
    M.grime(st, 0.3, seed=382, color=(90, 84, 70), cells=(8, 4), cover=0.5)
    save(st, "studs")
    ins = M.fabric(seed=383, base=(200, 150, 140), weave="plain", contrast=18, grain=6, mottle=10)
    M.grime(ins, 0.35, seed=384, color=(120, 100, 80), cells=(8, 4, 2), cover=0.6)
    di2 = ImageDraw.Draw(ins)
    for y in (0, 31):
        di2.line([0, y, 31, y], fill=(150, 124, 80))  # the kraft facing's flange
    save(ins, "insulation")
    # A braided rag rug: rings of faded colours
    rg = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    pr = rg.load()
    cols = [(104, 74, 60), (92, 90, 72), (118, 104, 82), (82, 76, 80), (110, 86, 64)]  # (faded: round 3's first shots read garish)
    for y in range(32):
        for x in range(32):
            ring = (y // 3 + (1 if (x // 2 + y) % 6 == 0 else 0))  # braided bands, a plait's stagger
            pr[x, y] = cols[ring % len(cols)] + (255,)
    M.grime(rg, 0.3, seed=391, color=(110, 104, 88), cells=(8, 4, 2), cover=0.6)
    M.hue_jitter(rg, 3, seed=392, cell=2)
    save(rg, "rug")
    e = M.noise_hv((84, 70, 52), 6, seed=393, mottle=10)
    M.grime(e, 0.3, seed=394, color=(60, 50, 38), cells=(8, 4, 2), cover=0.6)
    M.grime(e, 0.15, seed=395, color=(110, 100, 80), cells=(4, 2), cover=0.3)
    save(e, "floor-earth")
    # A cobweb: grey strands on nothing
    cw = Image.new("RGBA", (S2, S2), (0, 0, 0, 0))
    dw = ImageDraw.Draw(cw)
    import math
    for k in range(9):
        a = k / 8 * 1.5708
        dw.line([0, 0, 64 * math.cos(a) * 1.4, 64 * math.sin(a) * 1.4], fill=(200, 200, 196, 170), width=1)
    for r in range(8, 70, 8):
        pts = [(r * math.cos(k / 12 * 1.5708) * (1 + 0.08 * ((k * 7) % 3)), r * math.sin(k / 12 * 1.5708)) for k in range(13)]
        dw.line(pts, fill=(196, 196, 190, 140), width=1)
    save(cw, "cobweb")
    for name, base in (("cloth-shirt", (120, 132, 150)), ("cloth-sheet", (196, 192, 178)), ("cloth-towel", (150, 88, 70))):
        cl = M.fabric(seed=zlib.crc32(name.encode()) % 500, base=base, weave="plain", contrast=8, grain=3, mottle=8)
        M.grime(cl, 0.3, seed=zlib.crc32(name.encode()) % 400, color=(110, 104, 88), cells=(8, 4), cover=0.5)
        M.tideline(cl, 26, seed=zlib.crc32(name.encode()) % 300, color=(100, 94, 80), amount=0.3, wave=1.3, below=0.7)
        save(cl, name)
    # DO NOT ENTER, in marker on a scrap of board (the swollen doors)
    db = rgba(M.wood_planks(seed=401, size=S2, base=(140, 116, 80), planks=1, direction="h", grain=4, per_plank=6))
    write_text(db, ["DO NOT", "ENTER"], (4, 3, 60, 20), "segoeprb.ttf", (150, 22, 18, 255), 16, rotate=-2)
    dbb = db
    M.grime(dbb, 0.25, seed=402, color=(80, 70, 56), cells=(8, 4), cover=0.5)
    save(dbb, "doorboard")
    shade = M.noise_hv((60, 110, 70), 4, seed=411, mottle=5)
    M.grime(shade, 0.2, seed=412, color=(40, 50, 40), cells=(4, 2), cover=0.4)
    save(shade, "poolshade")
    bl = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    pl = bl.load()
    bcols = [(230, 220, 190), (200, 40, 30), (240, 190, 30), (30, 60, 150), (20, 20, 20), (110, 40, 120), (230, 120, 30), (30, 110, 60)]
    for y in range(32):
        for x in range(32):
            pl[x, y] = bcols[(x // 4 + y // 4 * 3) % len(bcols)] + (255,)
    save(bl, "balls")
    ch = M.painted_metal(seed=421, base=(52, 50, 46), panel=False, chips=2, under=(90, 56, 34))
    M.rust(ch, 0.45, seed=422, color=RUST, dark=RUSTDARK, cells=(8, 4, 2))
    M.grime(ch, 0.3, seed=423, color=(20, 18, 16), cells=(4, 2), cover=0.5)  # coal dust
    save(ch, "chute")
    sw = M.noise_hv((14, 20, 16), 3, seed=431, mottle=6)
    M.grime(sw, 0.25, seed=432, color=(40, 50, 30), cells=(8, 4), cover=0.4)
    save(sw, "sumpwater")
    g = M.painted_metal(seed=433, base=(48, 46, 44), panel=False, chips=1)
    M.rust(g, 0.5, seed=434, color=RUST, dark=RUSTDARK, cells=(4, 2))
    save(g, "grate")


# ======================================================================== Shapes

def b(name, frm, to, tex, faces=K.DIRS, rot=None, origin=None, uv=None, glow=0):
    return K.box(name, frm, to, tex, faces=faces, rot=rot, origin=origin, uv=uv, glow=glow)


def write_json(path, data, comment=None):
    import json
    text = json.dumps(data, indent="\t", ensure_ascii=False)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        if comment:
            f.write("// " + comment + "\n")
        f.write(text + "\n")


def shape(name, els):
    keys = K.textures(els)
    write_json(os.path.join(SHAPES, name + ".json"), {"textureWidth": 16, "textureHeight": 16,
                                                     "textures": {k: T[k] for k in keys}, "elements": els})
    return "block/basement/" + name


def round_body(name, cx, cz, r, y1, y2, tex, front=None):
    """A round body as an octagon (a square and the same turned an eighth)."""
    els = [b(name + "A", (cx - r, y1, cz - r), (cx + r, y2, cz + r), tex),
           b(name + "B", (cx - r, y1, cz - r), (cx + r, y2, cz + r), tex, rot=(0, 45, 0), origin=(cx, (y1 + y2) / 2, cz))]
    return els


def furnace(part):
    """(Round 3, after the first shots: wider, its arms climbing outward to the joists, as an octopus furnace's do.)"""
    cx, cz = 8, 8.75
    if part == "lower":
        els = [b("Plinth", (0.5, 0, 1.25), (15.5, 1.5, 16), "metaldark")]
        els += round_body("Body", cx, cz, 7.25, 1.5, 16, "furnace")
        els += [b("FireDoor", (4.75, 3.5, 1.2), (11.25, 10, 1.9), "furnacedoor"),
                b("Latch", (9.75, 6.25, 0.7), (10.75, 7.25, 1.2), "brass"),
                b("AshDoor", (5.5, 1.6, 1.4), (10.5, 3, 1.9), "metaldark"),
                b("Plate", (5, 11, 1.3), (11, 14, 1.9), "furnaceplate", uv=(0, 0, 16, 8))]
        for k, y in enumerate((1.5, 15)):
            els.append(b(f"Band{k}", (cx - 7.5, y, cz - 7.5), (cx + 7.5, y + 1, cz + 7.5), "metaldark", rot=(0, 45, 0), origin=(cx, y + 0.5, cz)))
        return els
    if part == "upper":
        els = round_body("Body", cx, cz, 7.25, 0, 6, "furnace")
        els += round_body("Shoulder", cx, cz, 6, 6, 9, "furnace")
        els += round_body("Dome", cx, cz, 4.5, 9, 12, "furnace")
        els += [b("Plenum", (5, 12, 6.25), (11, 16, 11.25), "lagging"),
                b("Gauge", (7, 3, 1.4), (9, 5, 1.9), "brass"),
                b("FlueBoot", (11, 7, 13), (14, 10, 16), "metaldark"), b("Flue", (11.5, 10, 13.5), (13.5, 16, 15.5), "metaldark")]
        return els
    # top: the arms climb outward from the plenum to the joists in steps, lagged white; one goes straight up at the back
    els = [b("Plenum", (5, 0, 6.25), (11, 4, 11.25), "lagging"), b("Flue", (11.5, 0, 13.5), (13.5, 16, 15.5), "metaldark"),
           b("ArmBack", (6.25, 3, 10.5), (9.75, 16, 14), "lagging")]
    for k in range(4):
        y = 2 + k * 3.5
        els += [b(f"ArmW{k}", (2 - k * 3, y, 7), (6 - k * 3, y + 4, 10.5), "lagging"),
                b(f"ArmE{k}", (10 + k * 3, y, 7), (14 + k * 3, y + 4, 10.5), "lagging"),
                b(f"ArmN{k}", (6.25, y, 3 - k * 3), (9.75, y + 4, 7 - k * 3), "lagging")]
    for k, (x1, z1, x2, z2) in enumerate(((-4.2, 6.8, -3.8, 10.7), (19.8, 6.8, 20.2, 10.7), (6.05, -4.2, 9.95, -3.8))):
        els.append(b(f"Collar{k}", (x1, 12.5, z1), (x2, 16, z2), "metaldark"))
    return els


def heater(part):
    cx, cz = 8, 9.5
    if part == "lower":
        els = round_body("Tank", cx, cz, 5.5, 0.5, 16, "heater")
        els += [b("Base", (3, 0, 4.5), (13, 0.5, 14.5), "metaldark"),
                b("Burner", (6, 1, 3.6), (10, 4, 4.2), "metaldark"),
                b("Valve", (6.5, 5, 3.0), (9.5, 8, 4.1), "metaldark"), b("Knob", (7.5, 6, 2.4), (8.5, 7, 3.0), "redpaint"),
                b("Gasline", (9.5, 6, 3.3), (16, 6.8, 4.1), "metaldark"),
                b("Drain", (7.5, 1.5, 2.8), (8.5, 2.5, 3.6), "brass"),
                b("Plate", (5.5, 9, 3.55), (10.5, 15, 4.1), "heaterplate", uv=(0, 0, 16, 16))]
        return els
    if part == "upper":
        els = round_body("Tank", cx, cz, 5.5, 0, 12, "heater")
        els += [b("Cap", (3, 12, 4.5), (13, 13, 14.5), "heater"), b("Hood", (6, 13, 8), (10, 16, 11), "metaldark"),
                b("Relief", (12, 9, 8.75), (14, 10.5, 10.25), "brass"), b("ReliefPipe", (13, 0, 9), (14, 9, 10), "copper"),
                b("Cold", (3.5, 13, 9), (4.75, 16, 10.25), "copper"), b("Hot", (11.25, 13, 9), (12.5, 16, 10.25), "copper")]
        return els
    return [b("Flue", (6.5, 0, 8), (9.5, 16, 11), "metaldark"), b("FlueJoint", (6.2, 6, 7.7), (9.8, 7, 11.3), "metaldark"),
            b("Cold", (3.5, 0, 9), (4.75, 16, 10.25), "copper"), b("Hot", (11.25, 0, 9), (12.5, 16, 10.25), "copper"),
            b("TagCold", (3.3, 7, 8.2), (4.95, 9, 8.95), "pipetags", uv=(0, 8, 16, 16)),
            b("TagHot", (11.05, 7, 8.2), (12.7, 9, 8.95), "pipetags", uv=(0, 0, 16, 8))]


def cut2(els):
    """A model two blocks long west to east (x 0-32) as its two blocks: (west, east)."""
    from gen_suburbs import cut
    turned = [e for e in els if any(k in e for k in ("rotationX", "rotationY", "rotationZ"))]
    parts = cut([e for e in els if e not in turned], 2, 1)
    west, east = parts[(0, 0)], parts[(1, 0)]
    # (a turned element goes whole to the block that holds its middle)
    for e in turned:
        if (e["from"][0] + e["to"][0]) / 2 < 16:
            west.append(e)
        else:
            east.extend(K.move([e], dx=-16))
    return west, east


def bench():
    els = [b("Top", (0, 13, 3), (32, 15, 16), "benchtop"), b("Apron", (0.5, 10.5, 3), (31.5, 13, 3.75), "benchtop"),
           b("Shelf", (1, 3, 4), (31, 4, 15.5), "benchtop")]
    for k, (x, z) in enumerate(((1, 4), (29, 4), (1, 13.5), (29, 13.5))):
        els.append(b(f"Leg{k}", (x, 0, z), (x + 2, 13, z + 2), "panel"))
    # The vice on the left, its screw and bar out front
    els += [b("ViceBase", (3, 15, 2.5), (8, 16.75, 7), "metaldark"), b("ViceJawB", (3.5, 16.75, 4), (7.5, 19, 5.5), "metaldark"),
            b("ViceJawF", (3.5, 15.5, 1), (7.5, 19, 2.5), "metaldark"), b("ViceScrew", (5, 16.5, -1), (6, 17.5, 1), "metal"),
            b("ViceBar", (2.5, 16.75, -1.4), (8.5, 17.25, -0.9), "metal")]
    # On the bench: a can of nails, a coffee can of brushes, a block of wood, a hammer; under it a toolbox, paint
    els += [b("NailCan", (12, 15, 8), (14.5, 18.5, 10.5), "paintcan", uv=(4, 4, 8, 8.5)), b("BrushCan", (24, 15, 11), (26.5, 18, 13.5), "paintcan", uv=(8, 4, 12, 8.5)),
            b("Brush", (24.75, 18, 11.75), (25.75, 21, 12.75), "panel"),
            b("Block", (17, 15, 5), (22, 16.5, 9), "panel", rot=(0, 22.5, 0)),
            b("HammerHandle", (18.5, 15, 10.5), (19.5, 15.75, 15), "panel", rot=(0, -22.5, 0), origin=(19, 15.4, 12.75)),
            b("HammerHead", (17, 15, 14), (21, 16.5, 15.25), "metaldark", rot=(0, -22.5, 0), origin=(19, 15.4, 12.75)),
            b("Toolbox", (4, 4, 6), (11, 8, 10), "redpaint"), b("ToolboxHandle", (6.5, 8, 7.75), (8.5, 9, 8.25), "metal"),
            b("Paint1", (20, 4, 6), (23, 8, 9), "paintcan", uv=(12, 4, 16, 8.5)), b("Paint2", (24, 4, 7), (27, 8, 10), "paintcan", uv=(0, 4, 4, 8.5)),
            b("Board", (0, 15, 15), (32, 16, 16), "benchtop")]
    return cut2(els)


def pooltable():
    els = [b("Bed", (1.5, 10, 2.5), (30.5, 12, 13.5), "felt"),
           b("RailN", (1, 10, 1), (31, 13, 2.5), "mahogany"), b("RailS", (1, 10, 13.5), (31, 13, 15), "mahogany"),
           b("RailW", (0, 10, 1), (1.5, 13, 15), "mahogany"), b("RailE", (30.5, 10, 1), (32, 13, 15), "mahogany"),
           b("Apron", (2, 7, 3), (30, 10, 13), "mahogany")]
    for k, (x, z) in enumerate(((2.5, 3.5), (27, 3.5), (2.5, 9.5), (27, 9.5))):
        els.append(b(f"Leg{k}", (x, 0, z), (x + 2.5, 7, z + 3), "mahogany"))
    for k, (x, z) in enumerate(((1.5, 2.5), (15, 2.5), (29.5, 2.5), (1.5, 12.5), (15, 12.5), (29.5, 12.5))):
        els.append(b(f"Pocket{k}", (x, 11.9, z), (x + 1.5 if k % 3 != 1 else x + 2, 12.1, z + 1), "metaldark", faces=("up",)))
    for k, (x, z) in enumerate(((8, 6), (9.2, 6.8), (8, 7.6), (20, 9), (23.5, 4.5), (13, 11))):
        u = (k % 4) * 4
        els.append(b(f"Ball{k}", (x, 12, z), (x + 1, 13, z + 1), "balls", uv=(u, 0, u + 2, 2)))
    els += [b("Cue", (4, 12, 5), (26, 12.6, 5.6), "panel", rot=(0, 10, 0), origin=(15, 12.3, 5.3)),
            b("Rack", (24, 12, 6.5), (27, 12.4, 9.5), "panel")]
    return cut2(els)


def shelving(part, kind):
    els = []
    for k, (x, z) in enumerate(((0.5, 3), (14.5, 3), (0.5, 14.5), (14.5, 14.5))):
        els.append(b(f"Post{k}", (x, 0, z), (x + 1, 16, z + 1), "metal"))
    levels = (1, 8) if part == "lower" else (0, 7, 14)
    for k, y in enumerate(levels):
        els.append(b(f"Shelf{k}", (0.5, y, 3), (15.5, y + 0.75, 15.5), "metal"))
    for k, y in enumerate(levels[:2] if part == "upper" else levels):
        y0 = y + 0.75
        if kind == "boxes":
            els += [b(f"BoxA{k}", (1.5, y0, 5), (8, y0 + 5.5, 14.5), "cardboard"), b(f"BoxB{k}", (8.5, y0, 6), (14, y0 + 4 + k, 14.5), "cardboard")]
        elif kind == "jars":
            for j in range(4):
                els.append(b(f"Jar{k}{j}", (1.5 + j * 3.4, y0, 5 + (j % 2) * 4), (4.3 + j * 3.4, y0 + 4, 8 + (j % 2) * 4), "jar"))
        elif kind == "paint":
            for j in range(3):
                if (j + k) % 3 == 2:
                    continue
                els.append(b(f"Can{k}{j}", (1.5 + j * 4.6, y0, 5), (5.5 + j * 4.6, y0 + 4.5, 9), "paintcan", uv=((j * 4 + k * 8) % 16, 4, (j * 4 + k * 8) % 16 + 4, 8.5)))
            els.append(b(f"Tray{k}", (2, y0, 10), (13, y0 + 1, 14), "metaldark"))
        else:  # odds and ends: a box, a lamp base, jars
            els += [b(f"Box{k}", (1.5, y0, 6), (7, y0 + 4, 14), "cardboard"),
                    b(f"Jar{k}", (9, y0, 6), (11.5, y0 + 4, 8.5), "jar"), b(f"Can{k}", (12, y0, 9), (15, y0 + 4.5, 12), "paintcan", uv=(k * 4, 4, k * 4 + 4, 8.5))]
    return els


def boxes(part, kind):
    tex = "box-" + kind
    face = {"north": tex, "south": "cardboard", "east": "cardboard", "west": "cardboard", "up": "cardboardtop", "down": "cardboard"}
    if part == "lower":
        return [b("Big", (1, 0, 3), (15, 9, 15), face), b("Mid", (2, 9, 4), (14, 16, 14.5), face)]
    return [b("Small", (3, 0, 5), (12, 6, 14), face, rot=(0, 10, 0), origin=(7.5, 3, 9.5)),
            b("Flat", (2, 6, 4), (11, 8, 13), "cardboard", rot=(0, -15, 0), origin=(6.5, 7, 8.5))]


def winerack(part):
    els = [b("SideW", (0.5, 0, 6), (1.5, 16, 15.5), "panel"), b("SideE", (14.5, 0, 6), (15.5, 16, 15.5), "panel"),
           b("Back", (1.5, 0, 15), (14.5, 16, 15.5), "panel")]
    for k, x in enumerate((5, 10)):
        els.append(b(f"Div{k}", (x, 0, 6), (x + 0.75, 16, 15), "panel"))
    rows = (0.5, 5.75, 11) if part == "lower" else (0, 5.25, 10.5)
    for r, y in enumerate(rows):
        els.append(b(f"Shelf{r}", (1.5, y, 6), (14.5, y + 0.5, 15), "panel"))
        for c, x in enumerate((1.5, 5.75, 10.75)):
            if (r * 3 + c + (part == "upper")) % 4 == 3:
                continue
            els += [b(f"Bottle{r}{c}", (x + 0.75, y + 0.75, 7.5), (x + 3.25, y + 3.25, 14.5), "bottle"),
                    b(f"Neck{r}{c}", (x + 1.5, y + 1.5, 5.5), (x + 2.5, y + 2.5, 7.5), "bottle")]
    if part == "upper":
        els.append(b("Top", (0.5, 15.5, 6), (15.5, 16, 15.5), "panel"))
    return els


def sump():
    # A concrete rim round a square hole, black water a block down, an iron grate over it, flush with the floor
    els = [b("RimN", (0, 0, 0), (16, 16, 3), "floor-dry"), b("RimS", (0, 0, 13), (16, 16, 16), "floor-dry"),
           b("RimW", (0, 0, 3), (3, 16, 13), "floor-dry"), b("RimE", (13, 0, 3), (16, 16, 13), "floor-dry"),
           b("Bottom", (3, 0, 3), (13, 2, 13), "floor-dry"), b("Water", (3, 8, 3), (13, 8.5, 13), "sumpwater", faces=("up",))]
    for k in range(5):
        els.append(b(f"Bar{k}", (3 + k * 2.25, 15, 2.5), (4 + k * 2.25, 16, 13.5), "grate"))
    els += [b("FrameN", (2.5, 15, 2.5), (13.5, 16, 3.5), "grate"), b("FrameS", (2.5, 15, 12.5), (13.5, 16, 13.5), "grate"),
            b("Pipe", (10, 2, 10), (12, 13, 12), "metaldark")]
    return els


def wallthing(kind):
    """Modelled on the south face of the block (the wall is to the south in the north variant), facing north."""
    if kind in ("pegboard-a", "pegboard-b"):
        els = [b("Board", (0, 1, 15.2), (16, 15, 15.75), "pegboard", uv=(0, 0, 16, 14)),
               b("Cleat", (0, 0.5, 15.75), (16, 1.5, 16), "panel")]
        if kind == "pegboard-a":
            els += [b("SawBlade", (2, 6, 14.9), (9, 10, 15.2), "metal"), b("SawHandle", (9, 6.5, 14.6), (11.5, 10, 15.2), "panel"),
                    b("Wrench1", (12, 3, 14.9), (12.75, 12, 15.2), "metal"), b("Wrench2", (13.5, 4, 14.9), (14.25, 12, 15.2), "metal"),
                    b("Coil", (3, 1.5, 14.4), (7, 5, 15.2), "rope"), b("Hook", (4.75, 5, 14.6), (5.25, 6, 15.2), "metal")]
        else:
            els += [b("Hammer", (2, 10, 14.7), (6, 11.5, 15.2), "metaldark"), b("HammerHandle", (3.5, 3, 14.8), (4.5, 10, 15.2), "panel"),
                    b("Driver1", (8, 6, 14.8), (8.75, 12, 15.2), "redpaint"), b("Driver2", (9.75, 6, 14.8), (10.5, 12, 15.2), "redpaint"),
                    b("Square", (11.5, 2, 14.9), (15, 2.75, 15.2), "metal"), b("SquareArm", (11.5, 2.75, 14.9), (12.25, 9, 15.2), "metal"),
                    b("Pliers", (6, 2, 14.8), (7, 6, 15.2), "metaldark")]
        return els
    if kind == "fusebox":
        return [b("Box", (3, 1, 13), (13, 13, 16), {"north": "fuseinside", "south": "fusebox", "east": "fusebox", "west": "fusebox",
                                                   "up": "fusebox", "down": "fusebox"}, uv=(0, 0, 16, 16)),
                b("Door", (2, 1, 3.5), (2.5, 13, 13), "fusebox"), b("DoorHinge", (2.25, 2, 12.75), (3.25, 12, 13.25), "metal"),
                b("Conduit", (7, 13, 14), (9, 16, 16), "metal"), b("ConduitLow", (10, 0, 14.5), (11.5, 1, 16), "metal")]
    if kind == "conduit":
        return [b("Conduit", (7, 0, 14), (9, 16, 16), "metal"), b("Strap", (6.5, 7, 13.75), (9.5, 8, 16), "metaldark"),
                b("Box", (6, 13, 13), (10, 16, 16), "metal")]
    if kind.startswith("sign-"):
        return [b("Plate", (2, 4, 15.3), (14, 12, 16), {"north": kind, "south": "metal", "east": "metal", "west": "metal", "up": "metal", "down": "metal"},
                  uv=(0, 0, 16, 10.67))]
    if kind == "calendar":
        return [b("Paper", (4.5, 1, 15.6), (11.5, 11, 16), "calendar", rot=(0, 0, 3), uv=(0, 0, 16, 16)),
                b("Nail", (7.75, 11, 15.2), (8.25, 11.5, 16), "metal")]
    # the coal chute: its iron hatch high on the wall, a trough down from it
    return [b("Frame", (2, 4, 15), (14, 16, 16), "chute"), b("Hatch", (3, 5, 14.4), (13, 15, 15), "chute"),
            b("Handle", (7, 6, 13.8), (9, 7, 14.4), "metaldark"),
            b("Trough", (4, 0, 6), (12, 1, 16), "chute", rot=(-30, 0, 0), origin=(8, 3, 16)),
            b("TroughW", (3.5, 0, 6), (4, 3, 16), "chute", rot=(-30, 0, 0), origin=(8, 3, 16)),
            b("TroughE", (12, 0, 6), (12.5, 3, 16), "chute", rot=(-30, 0, 0), origin=(8, 3, 16))]


def overhead(kind):
    """In the top block of air. A line runs west to east across the block's middle; a web fills the north-west corner."""
    if kind == "cobweb":
        return [b("Web", (-3, 2, 4.5), (13, 16, 4.6), "cobweb", rot=(0, 45, 0), origin=(5, 9, 5), faces=("north", "south"), uv=(0, 0, 16, 16)),
                b("WebTop", (0, 15.8, 0), (9, 15.9, 9), "cobweb", faces=("down",), uv=(0, 0, 16, 16))]
    els = [b("Line", (0, 11.75, 7.85), (16, 12.15, 8.15), "rope")]
    if kind == "shirt":
        els += [b("Shirt", (4, 3, 7.7), (12, 11.75, 8.3), "cloth-shirt"), b("SleeveW", (2, 7.5, 7.7), (4, 11.75, 8.3), "cloth-shirt"),
                b("SleeveE", (12, 7.5, 7.7), (14, 11.75, 8.3), "cloth-shirt")]
    elif kind == "sheet":
        els += [b("Sheet", (0.5, 1, 7.75), (15.5, 11.75, 8.25), "cloth-sheet")]
    elif kind == "towel":
        els += [b("Towel", (5, 5, 7.6), (11, 12, 8.4), "cloth-towel")]
    for k, x in enumerate((4.5, 11.5) if kind != "line" else ()):
        els.append(b(f"Peg{k}", (x, 11, 7.6), (x + 0.6, 13, 8.4), "panel"))
    return els


def poollamp():
    """(Round 3, after the first shots: hung lower on its chain, the shade sloped.)"""
    return [b("Chain", (7.75, 6, 7.75), (8.25, 16, 8.25), "metaldark"),
            b("ShadeTop", (4, 5, 5.5), (12, 6, 10.5), "poolshade"),
            b("Shade", (2, 2, 4), (14, 5, 12), "poolshade", faces=("north", "south", "east", "west", "up")),
            b("ShadeIn", (2.5, 2.01, 4.5), (13.5, 4.5, 11.5), "bulb-lit", faces=("down",), glow=120),
            b("Rim", (1.75, 1.75, 3.75), (14.25, 2.25, 12.25), "brass")]


def fallen():
    """Under the crack: a broken joist come down with the floor, leaning, and a board across it (each turned about its own
    middle, so they stand clear of the floor whichever way the turn goes)."""
    return [b("Joist", (6.5, 10.5, -8), (10, 14.5, 24), "panel", rot=(35, 0, 0), origin=(8, 12.5, 8)),
            b("Board", (1, 5, 2), (15, 6, 6), "panel", rot=(0, 0, 20), origin=(8, 5.5, 4)),
            b("Scrap", (2, 0.1, 8), (10, 0.6, 14), "lobbycarpet", rot=(0, 20, 0))]


def studs():
    # (Round 3, after the first shots: narrower studs, the batts nearer the faces so they show between them)
    els = [b("Batt", (0, 0, 2.5), (16, 16, 13.5), "insulation")]
    for k, x in enumerate((0, 8)):
        els.append(b(f"Stud{k}", (x, 0, 0), (x + 1.5, 16, 16), "studs"))
    return els


# ======================================================================== Blocks

def oriented(code, english, shapes_by, comment, material="Wood", sounds=WOOD, box=None, collide=True, light=None, drops=None,
             extra=None, groups=()):
    """A block with variant groups `groups` (code, states) and a side; `shapes_by` maps a tuple of states to a shape path."""
    vg = [{"code": c, "states": s} for c, s in groups] + [{"code": "side", "states": list(ROT)}]
    shape_by = {}
    for states, path in shapes_by.items():
        for side, r in ROT.items():
            shape_by["*-" + "-".join(states + (side,))] = {"base": path, "rotateY": r}
    first = "*-" + "-".join([s[0] for _, s in groups] + ["north"])
    data = {"code": code, "variantgroups": vg, "creativeinventory": {"general": [first], "decorative": [first]},
            "blockmaterial": material, "drawtype": "json", "shapeByType": shape_by,
            "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2,
            "drops": drops if drops is not None else [], "sounds": sounds}
    if box is not None:
        x1, y1, z1, x2, y2, z2 = box
        data["collisionSelectionBoxesByType"] = {f"*-{s}": [dict({"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2},
                                                                 **({"rotateY": r} if r else {}))] for s, r in ROT.items()}
    if not collide:
        data["collisionbox"] = None
        data.pop("collisionSelectionBoxesByType", None)
        sel = box or (0.1, 0.1, 0.8, 0.9, 0.9, 1)
        x1, y1, z1, x2, y2, z2 = sel
        data["selectionboxByType"] = {f"*-{s}": dict({"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2},
                                                    **({"rotateY": r} if r else {})) for s, r in ROT.items()}
    if light:
        data["lightHsvByType"] = light
    if extra:
        data.update(extra)
    write_json(os.path.join(BLOCKS, code + ".json"), data, comment)
    LANG[f"block-{code}-*"] = english


def blocks():
    oriented("basement-furnace", "Old furnace", {(p,): shape(f"furnace-{p}", furnace(p)) for p in ("lower", "upper", "top")},
             "The Basement: an old octopus gravity furnace, its round body two blocks high and its lagged ducts rising from it "
             "into the joists (part lower, upper, top)", material="Metal", sounds=METAL, box=(0.1, 0, 0.15, 0.9, 1, 1),
             drops=SCRAP, groups=[("part", ["lower", "upper", "top"])])
    oriented("basement-heater", "Water heater", {(p,): shape(f"heater-{p}", heater(p)) for p in ("lower", "upper", "top")},
             "The Basement: a water heater, its tank two blocks high, its flue and pipes going up into the joists, tagged",
             material="Metal", sounds=METAL, box=(0.15, 0, 0.2, 0.85, 1, 0.95), drops=SCRAP, groups=[("part", ["lower", "upper", "top"])])
    l, r = bench()
    oriented("basement-bench", "Workbench", {("l",): shape("bench-l", l), ("r",): shape("bench-r", r)},
             "The Basement: a workbench two blocks long (l, r as seen from in front), a vice on it", box=(0, 0, 0.15, 1, 0.95, 1),
             drops=STICKS, groups=[("half", ["l", "r"])])
    l, r = pooltable()
    oriented("basement-pooltable", "Pool table", {("l",): shape("pooltable-l", l), ("r",): shape("pooltable-r", r)},
             "The Basement: the rec room's pool table, two blocks long (l, r)", box=(0, 0, 0.05, 1, 0.82, 0.95),
             drops=STICKS, groups=[("half", ["l", "r"])])
    kinds = ["boxes", "jars", "paint", "odds"]
    oriented("basement-shelving", "Steel shelving", {(k, p): shape(f"shelving-{k}-{p}", shelving(p, k)) for k in kinds for p in ("lower", "upper")},
             "The Basement: steel shelving two blocks high (lower, upper), loaded (boxes, jars, paint cans, odds and ends)",
             material="Metal", sounds=METAL, box=(0, 0, 0.15, 1, 1, 1), drops=SCRAP, groups=[("load", kinds), ("part", ["lower", "upper"])])
    labels = ["xmas", "taxes", "moms", "keep"]
    oriented("basement-boxes", "Stacked boxes", {(k, p): shape(f"boxes-{k}-{p}", boxes(p, k)) for k in labels for p in ("lower", "upper")},
             "The Basement: cardboard boxes stacked two high (lower, upper), labelled in marker", box=(0.05, 0, 0.15, 0.95, 1, 0.95),
             sounds=CLOTH, drops=[{"type": "item", "code": "carpetfibre", "quantity": {"avg": 0.3, "var": 0.3}}],
             groups=[("label", labels), ("part", ["lower", "upper"])])
    oriented("basement-winerack", "Wine rack", {(p,): shape(f"winerack-{p}", winerack(p)) for p in ("lower", "upper")},
             "The Basement: a wine rack two blocks high (lower, upper), dusty bottles in most of its cubbies",
             box=(0, 0, 0.35, 1, 1, 1), drops=[{"type": "item", "code": "emptybottle", "quantity": {"avg": 0.5, "var": 0.5}}],
             groups=[("part", ["lower", "upper"])])
    write_json(os.path.join(BLOCKS, "basement-sump.json"), {
        "code": "basement-sump", "creativeinventory": {"general": ["*"], "decorative": ["*"]},
        "blockmaterial": "Stone", "drawtype": "json", "shape": {"base": shape("sump", sump())},
        "sidesolid": {"all": False, "up": True}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 6,
        "requiredMiningTier": 2, "drops": [], "sounds": METAL,
    }, "The Basement: the sump pit, an iron grate in the floor over black water")
    LANG["block-basement-sump"] = "Sump pit"
    things = ["pegboard-a", "pegboard-b", "fusebox", "conduit", "sign-caution", "sign-head", "sign-water", "calendar", "chute"]
    oriented("basement-wallthing", "Wall fixture", {(k,): shape(f"wallthing-{k}", wallthing(k)) for k in things},
             "The Basement: things on a wall at head height (pegboards of tools, the fuse box and its conduit, caution signs, "
             "a calendar, a coal chute's hatch), in the block in front of the wall", material="Metal", sounds=METAL,
             collide=False, box=(0.05, 0, 0.8, 0.95, 1, 1), drops=[{"type": "item", "code": "scrapwire", "quantity": {"avg": 0.3, "var": 0.3}}],
             groups=[("thing", things)])
    for k, e in {"pegboard-a": "Pegboard of tools", "pegboard-b": "Pegboard of tools", "fusebox": "Fuse box", "conduit": "Conduit",
                 "sign-caution": "Caution sign", "sign-head": "Caution sign", "sign-water": "Danger sign", "calendar": "Old calendar",
                 "chute": "Coal chute"}.items():
        LANG[f"block-basement-wallthing-{k}-*"] = e
    del LANG["block-basement-wallthing-*"]
    over = ["line", "shirt", "sheet", "towel", "cobweb"]
    oriented("basement-overhead", "Clothesline", {(k,): shape(f"overhead-{k}", overhead(k)) for k in over},
             "The Basement: in the top block of air, a clothesline (bare, a shirt, a sheet, a towel on it) or a cobweb in a corner",
             sounds=CLOTH, collide=False, box=(0, 0.2, 0.3, 1, 1, 0.7), drops=[], groups=[("hang", over)],
             extra={"renderpass": "OpaqueNoCull"})
    LANG["block-basement-overhead-cobweb-*"] = "Cobweb"
    oriented("basement-poollamp", "Pool table lamp", {(): shape("poollamp", poollamp())},
             "The Basement: the green-shaded lamp hung over the pool table, lit", material="Glass", sounds=METAL, collide=False,
             box=(0.1, 0.3, 0.2, 0.9, 1, 0.8), light={"*": [8, 3, 11]}, drops=[{"type": "item", "code": "glassshard", "quantity": {"avg": 1, "var": 0.5}}])
    write_json(os.path.join(BLOCKS, "basement-fallen.json"), {
        "code": "basement-fallen", "variantgroups": [{"code": "side", "states": list(ROT)}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{s}": {"base": shape("fallen", fallen()), "rotateY": r} for s, r in ROT.items()},
        "collisionbox": None, "selectionbox": {"x1": 0.1, "y1": 0, "z1": 0.1, "x2": 0.9, "y2": 0.9, "z2": 0.9},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 1, "replaceable": 400,
        "drops": STICKS, "sounds": WOOD,
    }, "The Basement: a broken joist and a board come down through the crack with whoever fell, leaning in the rubble")
    LANG["block-basement-fallen-*"] = "Fallen Joist"
    write_json(os.path.join(BLOCKS, "basement-studs.json"), {
        "code": "basement-studs", "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Wood", "drawtype": "json", "shape": {"base": shape("studs", studs())},
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 99, "resistance": 3,
        "drops": STICKS + [{"type": "item", "code": "carpetfibre", "quantity": {"avg": 0.5, "var": 0.5}}], "sounds": WOOD,
    }, "The Basement: an unfinished wall, bare studs with fibreglass batts stapled between them")
    LANG["block-basement-studs"] = "Unfinished stud wall"
    for code, tex, english, mat, snd, drops in (
            ("basement-earth", "floor-earth", "Trodden earth", "Soil", {"walk": "game:walk/gravel", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"},
             [{"type": "item", "code": "game:soil-medium-none", "quantity": {"avg": 1, "var": 0}}]),
            ("basement-rug", "rug", "Braided rug", "Cloth", CLOTH, [{"type": "item", "code": "carpetfibre", "quantity": {"avg": 2, "var": 1}}])):
        write_json(os.path.join(BLOCKS, code + ".json"), {
            "code": code, "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": mat, "drawtype": "cube",
            # (the rug's braids keep one way; the earth turns)
            "textures": {"all": {"base": "block/basement/" + tex, "alternates": [{"base": "block/basement/" + tex, "rotation": r} for r in ((180,) if tex == "rug" else (90, 180, 270))]}},
            "resistance": 2, "lightAbsorption": 99, "drops": drops, "sounds": snd,
        }, "The Basement: " + english.lower())
        LANG["block-" + code] = english


def door_board():
    """The board nailed across a swollen-shut door, DO NOT ENTER on it (in the door's upper block, on its outer face)."""
    return [b("Board", (0.25, 2.5, 1.0), (15.75, 7.5, 2.0), {"north": "doorboard", "south": "panel", "east": "panel", "west": "panel",
                                                            "up": "panel", "down": "panel"}, uv=(0, 0, 16, 5.33), rot=(0, 0, -4)),
            b("NailW", (1, 4.5, 0.6), (1.75, 5.25, 1.0), "metaldark"), b("NailE", (14.25, 4, 0.6), (15, 4.75, 1.0), "metaldark")]


SHAPE_TEX = T
