"""The Basement, round 4 (2026-11-02): the asset-quality pass. Called by tools/gen_basement.py after round 3's
`textures()` / `blocks()` (which empty the level's folders first); run it through that:

    bash tools/locked.sh run python tools/gen_basement.py

Rebuilt to the bar (same block codes as round 3, their shapes rewritten here): the octopus furnace (its arms round
ducts climbing at an angle, with collars and foil tape, its flue into a thimble in the wall), the water heater (T&P
valve and discharge, gas control and drip leg, draft hood, a handwheel on the cold), the pool table (cushions, pockets
with leather drops, sights, a racked set of balls), the steel shelving (jars and tins with printed labels, paint cans
with lids and bails), the workbench (a modelled vice) and its pegboards (the tools as models), the clothesline (pegs,
the washing with folds), the hall's duct (now with a water main and a gas line beside it, a gate valve or a gauge on
some blocks).

New blocks (all `basement-`):
    laundry    the basement's own washer and dryer (round porthole doors, a console, feet, hoses to a hose bib, the
               dryer's foil vent into the wall) and a laundry tub on legs (kind washer, dryer, tub; part lower, upper)
    sofa       an old plaid sofa two tiles long, its cushions, arms and a crocheted throw (half l, r)
    tv         a console television on legs, its tube's hump behind, rabbit ears on top (part lower, upper)
    cuerack    the rec room's cue rack on the wall, four cues in it, the chalk on its shelf
    shoplight  a two-tube fluorescent shop light hung on chains over the workbench (lit)
    joists     the ceiling of bare joists as a model: subfloor boards over the joists, NM cable stapled along one, a
               junction box, cross bridging (kind plain, cable, box, bridge; axis we, ns; light dark, faint)
    rail       the handrail of the stairs down into the Flood: a pipe rail on a leaning newel, a baluster in the water
               (hand l, r)
    slabedge   the broken edge of the slab round the crack: jagged concrete, rebar bent down (shape a, b)
    scum       on the Flood's water: a film of scum and leaves (a, b, c), a floating board, a sodden box, a bottle
"""
import json
import math
import os
import zlib

from PIL import Image, ImageDraw

import matlib as M
import modelkit as K
import gen_basement_r3 as R3
from gen_suburbs import mirror_x

TEX, SHAPES, BLOCKS = R3.TEX, R3.SHAPES, R3.BLOCKS
ROT = R3.ROT
RUST, RUSTDARK = R3.RUST, R3.RUSTDARK
WOOD, METAL, STONE, CLOTH = R3.WOOD, R3.METAL, R3.STONE, R3.CLOTH
SCRAP, STICKS = R3.SCRAP, R3.STICKS
save, write_text, rgba = R3.save, R3.write_text, R3.rgba

NEW = ("galv", "foiltape", "castiron", "blackpipe", "redwheel", "yellowgrip", "enamel", "console-washer", "console-dryer",
       "drumglass", "chrome", "hose-red", "hose-blue", "foilduct", "tub", "tubin", "plaid", "throw", "walnut", "tvscreen",
       "tvback", "speakercloth", "bakelite", "doily", "photo", "cushion", "leather", "ivory", "poolballs", "maple", "cuebutt",
       "chalk", "labels", "tin", "toolsteel", "grip", "handlewood", "pegwood", "vicepaint", "detergent", "jug", "lumber",
       "subfloor", "nmcable", "jbox", "newel", "railpipe", "slabbreak", "rebar", "scum-a", "scum-b", "scum-c", "soggy",
       "shoplight", "tube", "wallpaint", "ceiling-under", "dialface", "gauge-tag", "porcelain", "bulb-off", "filament",
       "slime-bed", "pvc", "sumpwater", "grate", "floor-dry")
T = dict(R3.T)
T.update({k: "backrooms:block/basement/" + k for k in NEW})
T["dialface"] = "backrooms:block/detail/gauge"
T["lobbytile"] = "backrooms:block/ceilingtile-stain"
T["lobbypaper"] = "backrooms:block/wallpaper/chevron-plain-damp"
T["ceiling-under"] = "backrooms:block/basement/ceiling-plain"
S2 = 64


def shape(name, els):
    keys = K.textures(els)
    missing = [k for k in keys if k not in T]
    assert not missing, (name, missing)
    R3.write_json(os.path.join(SHAPES, name + ".json"), {"textureWidth": 16, "textureHeight": 16,
                                                        "textures": {k: T[k] for k in keys}, "elements": els})
    return "block/basement/" + name


def b(name, frm, to, tex, faces=K.DIRS, rot=None, origin=None, uv=None, glow=0):
    return K.box(name, frm, to, tex, faces=faces, rot=rot, origin=origin, uv=uv, glow=glow)


def oct_xz(name, cx, cz, r, y1, y2, tex, rot_tex=None):
    """A round body standing up: a square and the same turned an eighth (set a hair smaller, so no face meets a face)."""
    return [b(name + "A", (cx - r, y1, cz - r), (cx + r, y2, cz + r), tex),
            b(name + "B", (cx - r + 0.05, y1 + 0.02, cz - r + 0.05), (cx + r - 0.05, y2 - 0.02, cz + r - 0.05), rot_tex or tex,
              rot=(0, 45, 0), origin=(cx, (y1 + y2) / 2, cz))]


def rod_x(name, x1, x2, cy, cz, d, tex):
    """A round rod along x: two boxes crossed (a plus in section), so it reads round from any side."""
    n = d * 0.62
    return [b(name + "A", (x1, cy - n / 2, cz - d / 2), (x2, cy + n / 2, cz + d / 2), tex),
            b(name + "B", (x1 + 0.01, cy - d / 2, cz - n / 2), (x2 - 0.01, cy + d / 2, cz + n / 2), tex)]


def rod_y(name, y1, y2, cx, cz, d, tex, rot=None, origin=None):
    n = d * 0.62
    return [b(name + "A", (cx - d / 2, y1, cz - n / 2), (cx + d / 2, y2, cz + n / 2), tex, rot=rot, origin=origin),
            b(name + "B", (cx - n / 2, y1 + 0.01, cz - d / 2), (cx + n / 2, y2 - 0.01, cz + d / 2), tex, rot=rot, origin=origin)]


def rod_z(name, z1, z2, cx, cy, d, tex, rot=None, origin=None):
    n = d * 0.62
    return [b(name + "A", (cx - d / 2, cy - n / 2, z1), (cx + d / 2, cy + n / 2, z2), tex, rot=rot, origin=origin),
            b(name + "B", (cx - n / 2, cy - d / 2, z1 + 0.01), (cx + n / 2, cy + d / 2, z2 - 0.01), tex, rot=rot, origin=origin)]


def ring_xy(name, cx, cy, z1, z2, r, bar, tex):
    """A ring facing north (a porthole's frame, a handwheel): four bars and four more turned an eighth about z."""
    els = []
    s = r * 0.83
    for k, (a, c) in enumerate((((cx - s / 2, cy + r - bar), (cx + s / 2, cy + r)), ((cx - s / 2, cy - r), (cx + s / 2, cy - r + bar)),
                                ((cx - r, cy - s / 2), (cx - r + bar, cy + s / 2)), ((cx + r - bar, cy - s / 2), (cx + r, cy + s / 2)))):
        els.append(b(f"{name}R{k}", (a[0], a[1], z1), (c[0], c[1], z2), tex))
    m = (r - bar / 2) / math.sqrt(2)
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        ox, oy = cx + sx * m, cy + sy * m
        els.append(b(f"{name}D{k}", (ox - s / 2, oy - bar / 2, z1 + 0.03), (ox + s / 2, oy + bar / 2, z2 - 0.03), tex,
                     rot=(0, 0, -45 * sx * sy), origin=(ox, oy, (z1 + z2) / 2)))
    return els


def ring_xz(name, cx, y, cz, r, bar, h, tex):
    """A ring lying flat (a handwheel under a valve): the same in the horizontal plane, turned about y."""
    els = []
    s = r * 0.83
    for k, (a, c) in enumerate((((cx - s / 2, cz + r - bar), (cx + s / 2, cz + r)), ((cx - s / 2, cz - r), (cx + s / 2, cz - r + bar)),
                                ((cx - r, cz - s / 2), (cx - r + bar, cz + s / 2)), ((cx + r - bar, cz - s / 2), (cx + r, cz + s / 2)))):
        els.append(b(f"{name}R{k}", (a[0], y, a[1]), (c[0], y + h, c[1]), tex))
    m = (r - bar / 2) / math.sqrt(2)
    for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (1, -1), (-1, -1))):
        ox, oz = cx + sx * m, cz + sz * m
        els.append(b(f"{name}D{k}", (ox - s / 2, y + 0.03, oz - bar / 2), (ox + s / 2, y + h - 0.03, oz + bar / 2), tex,
                     rot=(0, 45 * sx * sz, 0), origin=(ox, y + h / 2, oz)))
    els += [b(name + "Sp1", (cx - r + bar, y + 0.05, cz - 0.2), (cx + r - bar, y + h - 0.05, cz + 0.2), tex),
            b(name + "Sp2", (cx - 0.2, y + 0.05, cz - r + bar), (cx + 0.2, y + h - 0.05, cz + r - bar), tex)]
    return els


# ======================================================================== Textures

def labelled(base_img, lines, box, color, px=12, fontname="arialbd.ttf"):
    return write_text(base_img, lines, box, fontname, color, px)


def textures():
    # ---- metals ----
    g = M.galvanised(seed=501, base=(126, 130, 130), white_rust=0.15)
    M.grime(g, 0.3, seed=502, color=(70, 66, 58), cells=(8, 4, 2), cover=0.55)
    save(g, "galv")
    ft = M.brushed_metal(seed=503, base=(176, 176, 172), direction="h", streak=12, sheen=16)
    M.scratches(ft, n=12, seed=504, length=(3, 9), light=0.3)
    M.grime(ft, 0.3, seed=505, color=(110, 100, 80), cells=(8, 4), cover=0.5)
    save(ft, "foiltape")
    ci = M.painted_metal(seed=506, base=(42, 42, 41), panel=False, chips=3, under=(96, 60, 36))
    M.rust(ci, 0.35, seed=507, color=RUST, dark=RUSTDARK, cells=(8, 4, 2))
    save(ci, "castiron")
    bp = M.painted_metal(seed=508, base=(36, 36, 35), panel=False, chips=2, under=(90, 70, 52))
    M.rust(bp, 0.3, seed=509, color=RUST, dark=RUSTDARK, cells=(4, 2))
    M.grime(bp, 0.2, seed=510, color=(80, 76, 66), cells=(8, 4), cover=0.4)  # dust on top
    save(bp, "blackpipe")
    rw = M.painted_metal(seed=511, base=(150, 38, 30), panel=False, chips=5, under=(60, 44, 34))
    M.rust(rw, 0.2, seed=512, color=RUST, dark=RUSTDARK, cells=(4, 2))
    save(rw, "redwheel")
    yg = M.rubber(seed=513, base=(196, 150, 40))
    M.grime(yg, 0.3, seed=514, color=(80, 70, 50), cells=(4, 2), cover=0.5)
    save(yg, "yellowgrip")
    ch = M.brushed_metal(seed=515, base=(196, 198, 198), direction="h", streak=10, sheen=20)
    M.rust(ch, 0.08, seed=516, color=RUST, dark=RUSTDARK, cells=(4, 2))
    save(ch, "chrome")
    tn = M.brushed_metal(seed=517, base=(168, 166, 160), direction="v", streak=8, sheen=10)
    M.grime(tn, 0.3, seed=518, color=(96, 84, 64), cells=(8, 4), cover=0.5)
    save(tn, "tin")
    ts = M.brushed_metal(seed=519, base=(112, 114, 116), direction="h", streak=8, sheen=12)
    M.rust(ts, 0.15, seed=520, color=RUST, dark=RUSTDARK, cells=(4, 2))
    save(ts, "toolsteel")
    vp = M.painted_metal(seed=521, base=(62, 82, 104), panel=False, chips=6, under=(70, 70, 70))
    M.grime(vp, 0.3, seed=522, color=(40, 40, 36), cells=(4, 2), cover=0.5)
    save(vp, "vicepaint")
    gr = M.rubber(seed=523, base=(178, 72, 34), pattern="ribs", pitch=4)
    save(gr, "grip")
    rb = M.painted_metal(seed=524, base=(52, 64, 46), panel=False, chips=1)
    M.rust(rb, 0.75, seed=525, color=RUST, dark=RUSTDARK, cells=(4, 2))
    d = ImageDraw.Draw(rb)
    for y in range(0, 32, 4):
        d.line([0, y, 31, y + 1], fill=(70, 40, 24))  # the ribs
    save(rb, "rebar")
    rp = M.painted_metal(seed=526, base=(40, 40, 38), panel=False, chips=2)
    M.rust(rp, 0.4, seed=527, color=RUST, dark=RUSTDARK, cells=(8, 4))
    for x in range(32):  # worn bright along the top, where hands went
        for y in (13, 14, 15, 16, 17):
            M.touch(rp, x, y, 0.22 if y in (14, 15, 16) else 0.1)
    save(rp, "railpipe")
    jb = M.galvanised(seed=528, base=(140, 142, 140))
    M.screw(jb, 15, 15)
    save(jb, "jbox")
    # ---- appliances (1950s enamel, gone yellow, chipped, rust at the foot) ----
    en = M.painted_metal(seed=531, base=(196, 190, 170), panel=False, chips=5, under=(66, 58, 52))
    M.rust(en, 0.14, seed=532, color=RUST, dark=RUSTDARK, cells=(8, 4))
    M.grime(en, 0.3, seed=533, color=(120, 104, 76), cells=(8, 4, 2), bias="bottom", cover=0.6)
    M.drips(en, n=2, seed=534, color=(140, 96, 56), length=(6, 14), strength=0.3)
    save(en, "enamel")
    for name, words, dials in (("console-washer", ["SPINMASTER"], ("WASH", "RINSE", "SPIN")),
                               ("console-dryer", ["TUMBLEMASTER"], ("COOL", "WARM", "HOT"))):
        c = rgba(M.painted_metal(seed=zlib.crc32(name.encode()) % 900, size=S2, base=(190, 184, 164), panel=False, chips=3, under=(70, 60, 52)))
        dc = ImageDraw.Draw(c)
        dc.rectangle([0, 0, 63, 3], fill=(196, 198, 196))   # chrome trim
        dc.rectangle([0, 60, 63, 63], fill=(150, 146, 132))
        dc.rectangle([22, 10, 42, 22], fill=(70, 96, 110))  # the brand's enamel badge
        write_text(c, words, (23, 11, 42, 21), "arialbd.ttf", (230, 226, 210, 255), 9)
        write_text(c, ["HOMEMAID"], (20, 26, 44, 34), "segoeprb.ttf", (120, 30, 26, 255), 9)
        for k, (x, word) in enumerate(((8, dials[0]), (32, dials[1]), (56, dials[2]))):
            dc.ellipse([x - 6, 38, x + 6, 50], outline=(60, 56, 50), width=1)
            write_text(c, [word], (x - 8, 51, x + 8, 58), "arial.ttf", (50, 46, 40, 255), 6)
        M.grime(c, 0.25, seed=541, color=(110, 96, 70), cells=(8, 4), cover=0.5)
        save(c, name)
    dg = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    pd = dg.load()
    for y in range(32):
        for x in range(32):
            r = math.hypot(x - 15.5, y - 15.5) / 16
            v = 34 + int(22 * (1 - r))
            col = (v - 8, v + 2, v + 6)
            if 0.55 < r < 0.62:
                col = (70, 74, 74)  # the drum's rim seen through the glass
            if y > 20 and r < 0.95:
                col = (60, 66, 50) if y > 21 else (110, 112, 90)  # stale water and its scum line
            pd[x, y] = col + (255,)
    dd = ImageDraw.Draw(dg)
    dd.line([6, 10, 12, 4], fill=(150, 160, 160), width=2)  # a reflection
    M.grime(dg, 0.2, seed=542, color=(90, 86, 70), cells=(8, 4), cover=0.4)
    save(dg, "drumglass")
    for name, base in (("hose-red", (140, 40, 32)), ("hose-blue", (42, 64, 120))):
        h = M.rubber(seed=zlib.crc32(name.encode()) % 700, base=base, pattern="ribs", pitch=4)
        M.grime(h, 0.3, seed=543, color=(70, 64, 56), cells=(4, 2), cover=0.5)
        save(h, name)
    fd = M.brushed_metal(seed=544, base=(170, 168, 162), direction="h", streak=8, sheen=18)
    d = ImageDraw.Draw(fd)
    for y in range(0, 32, 3):
        d.line([0, y, 31, y], fill=(110, 108, 100))  # the flexible duct's ribs
        d.line([0, y + 1, 31, y + 1], fill=(200, 198, 190))
    M.grime(fd, 0.35, seed=545, color=(110, 100, 80), cells=(8, 4), cover=0.6)
    save(fd, "foilduct")
    tb = M.concrete(seed=546, base=(112, 116, 112), grain=3, mottle=6, aggregate=0.03, pores=0.01)
    M.grime(tb, 0.25, seed=547, color=(80, 82, 74), cells=(8, 4), cover=0.5)
    save(tb, "tub")
    ti = M.concrete(seed=548, base=(92, 96, 92), grain=3, mottle=6, aggregate=0.02, pores=0.01)
    M.grime(ti, 0.4, seed=549, color=(96, 76, 50), cells=(8, 4, 2), bias="bottom", cover=0.7)
    M.tideline(ti, 20, seed=550, color=(110, 92, 60), amount=0.45, wave=1.2, below=0.8)
    save(ti, "tubin")
    dt = rgba(M.paper(seed=551, size=S2, base=(220, 120, 40)))
    dtd = ImageDraw.Draw(dt)
    dtd.ellipse([6, 8, 58, 44], fill=(30, 70, 150))
    write_text(dt, ["SUDZO"], (10, 14, 54, 38), "arialbd.ttf", (246, 236, 200, 255), 18)
    write_text(dt, ["SOAP FLAKES"], (6, 47, 58, 58), "arialbd.ttf", (40, 30, 20, 255), 9)
    M.grime(dt, 0.25, seed=552, color=(110, 90, 60), cells=(8, 4), cover=0.5)
    M.tideline(dt, 58, seed=553, color=(120, 90, 60), amount=0.4, wave=1.2, below=0.9)
    save(dt, "detergent")
    jg = rgba(M.noise_hv((206, 204, 192), 3, seed=554, size=S2, mottle=4))
    jd = ImageDraw.Draw(jg)
    jd.rectangle([4, 22, 59, 46], fill=(40, 90, 160))
    write_text(jg, ["BLEACH"], (6, 24, 58, 44), "arialbd.ttf", (240, 240, 230, 255), 14)
    M.grime(jg, 0.25, seed=555, color=(120, 110, 90), cells=(8, 4), cover=0.5)
    save(jg, "jug")
    # ---- the rec room ----
    pl = M.fabric(seed=556, base=(112, 78, 52), weave="twill", contrast=10, grain=3, mottle=6)
    pp = pl.load()
    for y in range(32):
        for x in range(32):
            c = pp[x, y]
            band = ((x % 16) in (2, 3, 10), (y % 16) in (2, 3, 10))
            if (x % 16) in (6, 7) or (y % 16) in (6, 7):
                c = M.mix(c, (150, 104, 54), 0.5)  # an orange stripe
            if band[0] or band[1]:
                c = M.mix(c, (60, 66, 44), 0.55)  # a dark green one
            if band[0] and band[1]:
                c = M.mix(c, (40, 40, 30), 0.4)
            pp[x, y] = tuple(int(round(v)) for v in c[:3]) + (255,)
    M.grime(pl, 0.3, seed=557, color=(80, 66, 50), cells=(8, 4, 2), cover=0.55)
    save(pl, "plaid")
    th = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    tp = th.load()
    gran = [(150, 60, 50), (190, 150, 60), (70, 100, 70), (120, 80, 110), (60, 80, 120)]
    for y in range(32):
        for x in range(32):
            sx, sy = x // 8, y // 8
            ix, iy = x % 8, y % 8
            ring = min(ix, iy, 7 - ix, 7 - iy)
            c = (24, 20, 18) if ring == 0 else gran[(sx * 2 + sy * 3 + ring) % len(gran)]
            tp[x, y] = c + (255,)
    M.grime(th, 0.3, seed=558, color=(110, 100, 80), cells=(8, 4), cover=0.6)
    save(th, "throw")
    wn = M.wood_planks(seed=559, base=(86, 54, 34), planks=1, direction="h", grain=5, per_plank=4, flecks=0.7)
    M.scratches(wn, n=8, seed=560, length=(2, 7), light=0.2)
    M.grime(wn, 0.25, seed=561, color=(90, 84, 70), cells=(8, 4), cover=0.4)  # dust
    save(wn, "walnut")
    sc = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    ps = sc.load()
    for y in range(32):
        for x in range(32):
            r = max(abs(x - 15.5) / 16, abs(y - 15.5) / 16) ** 3
            v = int(64 - 40 * r)
            ps[x, y] = (v - 6, v + 4, v) + (255,)
    dsd = ImageDraw.Draw(sc)
    dsd.line([5, 9, 13, 3], fill=(120, 132, 126), width=2)
    dsd.line([6, 12, 10, 8], fill=(96, 104, 100), width=1)
    M.grime(sc, 0.15, seed=562, color=(90, 90, 80), cells=(8, 4), cover=0.4)
    save(sc, "tvscreen")
    tbk = M.noise_hv((60, 50, 42), 3, seed=563, mottle=4)
    d = ImageDraw.Draw(tbk)
    for y in range(4, 28, 3):
        d.line([6, y, 25, y], fill=(24, 20, 18))  # vents
    save(tbk, "tvback")
    sk = M.fabric(seed=564, base=(150, 130, 96), weave="basket", contrast=14, grain=3, mottle=4)
    d = ImageDraw.Draw(sk)
    for x in range(0, 32, 4):
        d.line([x, 0, x, 31], fill=(170, 140, 70))  # a gold thread
    M.grime(sk, 0.3, seed=565, color=(90, 80, 60), cells=(8, 4), cover=0.5)
    save(sk, "speakercloth")
    bk = M.noise_hv((56, 36, 26), 3, seed=566, mottle=4)
    save(bk, "bakelite")
    dl = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(dl)
    for r in range(15, 2, -3):
        d.ellipse([16 - r, 16 - r, 15 + r, 15 + r], outline=(214, 208, 190, 255), width=1)
    d.ellipse([12, 12, 19, 19], fill=(214, 208, 190, 255))
    for k in range(12):
        a = k / 12 * 2 * math.pi
        d.line([16, 16, 16 + 15 * math.cos(a), 16 + 15 * math.sin(a)], fill=(204, 198, 180, 255), width=1)
    save(dl, "doily")
    ph = rgba(M.paper(seed=567, size=(32, 32), base=(150, 140, 120)))
    d = ImageDraw.Draw(ph)
    d.rectangle([0, 0, 31, 31], outline=(170, 140, 60), width=2)
    d.rectangle([4, 4, 27, 27], fill=(120, 116, 104))
    d.ellipse([9, 7, 15, 14], fill=(70, 62, 54))
    d.ellipse([17, 8, 23, 15], fill=(70, 62, 54))
    d.rectangle([8, 14, 16, 27], fill=(60, 56, 70))
    d.rectangle([16, 15, 24, 27], fill=(110, 70, 60))
    save(ph, "photo")
    cu = M.noise_hv((44, 92, 56), 3, seed=568, mottle=5)
    M.grime(cu, 0.25, seed=569, color=(40, 50, 40), cells=(8, 4), cover=0.5)
    save(cu, "cushion")
    lt = M.noise_hv((70, 44, 30), 4, seed=570, mottle=6)
    M.scratches(lt, n=6, seed=571, length=(2, 5), light=0.2)
    save(lt, "leather")
    save(M.noise_hv((214, 204, 176), 2, seed=572, mottle=3), "ivory")
    pb = Image.new("RGBA", (32, 32), (0, 0, 0, 255))
    pbd = ImageDraw.Draw(pb)
    cols = [(228, 220, 196), (214, 170, 30), (34, 60, 150), (190, 40, 30), (100, 40, 120), (220, 110, 30), (30, 110, 60),
            (120, 30, 30), (24, 24, 24)]
    for k in range(16):
        x, y = (k % 4) * 8, (k // 4) * 8
        if k == 0:
            pbd.rectangle([x, y, x + 7, y + 7], fill=cols[0])  # the cue ball
            continue
        n = k if k <= 8 else k - 8
        base = cols[n] if n < len(cols) else cols[1]
        if k > 8:  # stripes: white with a band
            pbd.rectangle([x, y, x + 7, y + 7], fill=(226, 218, 194))
            pbd.rectangle([x, y + 2, x + 7, y + 5], fill=base)
        else:
            pbd.rectangle([x, y, x + 7, y + 7], fill=base)
        pbd.rectangle([x + 3, y + 3, x + 4, y + 4], fill=(236, 230, 210))  # the number's spot
        pbd.point((x + 1, y + 1), fill=(250, 246, 230))  # a highlight
    save(pb, "poolballs")
    mp = M.wood_planks(seed=573, base=(196, 160, 110), planks=1, direction="v", grain=3, per_plank=2, flecks=0.4)
    save(mp, "maple")
    cb = M.wood_planks(seed=574, base=(52, 30, 24), planks=1, direction="v", grain=3, per_plank=2)
    d = ImageDraw.Draw(cb)
    for y in (6, 7, 20, 21):
        d.line([0, y, 31, y], fill=(220, 210, 180))  # the inlay rings
    save(cb, "cuebutt")
    save(M.noise_hv((60, 110, 170), 3, seed=575, mottle=4), "chalk")
    # ---- labels: jars, tins and paint cans, 4 x 4 cells of 32 px (a cell maps to a 4 x 4 uv square) ----
    lb = Image.new("RGBA", (128, 128), (0, 0, 0, 255))
    jars = [("PEACHES", (196, 118, 40)), ("PICKLES", (88, 110, 44)), ("TOMATOES", (150, 40, 28)), ("BEANS", (150, 120, 70)),
            ("CHERRIES", (110, 20, 30)), ("CORN", (200, 170, 50)), ("APPLE", (176, 140, 80)), ("?", (34, 40, 26))]
    for k, (word, fill) in enumerate(jars):
        x0, y0 = (k % 4) * 32, (k // 4) * 32
        cell = Image.new("RGBA", (32, 32), fill + (255,))
        M.grime(cell, 0.35, seed=580 + k, color=tuple(max(0, c - 40) for c in fill), cells=(8, 4), cover=0.6)
        cd = ImageDraw.Draw(cell)
        cd.rectangle([0, 10, 31, 24], fill=(214, 204, 170))  # the label, hand-written
        write_text(cell, [word], (2, 11, 30, 18), "segoeprb.ttf", (40, 36, 60, 255), 9)
        write_text(cell, ["'58" if k % 3 else "1957"], (8, 18, 24, 24), "segoeprb.ttf", (60, 50, 60, 255), 6)
        cd.line([3, 0, 3, 31], fill=tuple(min(255, c + 70) for c in fill))  # the glass's highlight
        cd.line([4, 0, 4, 9], fill=tuple(min(255, c + 40) for c in fill))
        lb.alpha_composite(cell, (x0, y0))
    tins = [("COFFEE", (150, 30, 26), (230, 210, 150)), ("PORK & BEANS", (40, 80, 140), (240, 230, 200)),
            ("TOMATO SOUP", (200, 40, 30), (240, 236, 220)), ("PEAS", (60, 120, 60), (240, 230, 190))]
    for k, (word, fill, ink) in enumerate(tins):
        x0, y0 = (k % 4) * 32, 64
        cell = Image.new("RGBA", (32, 32), fill + (255,))
        cd = ImageDraw.Draw(cell)
        cd.rectangle([0, 0, 31, 2], fill=(170, 168, 160))
        cd.rectangle([0, 29, 31, 31], fill=(150, 148, 140))
        cd.rectangle([2, 9, 29, 22], fill=ink)
        write_text(cell, word.split(" ", 1) if " " in word else [word], (3, 10, 29, 22), "arialbd.ttf", fill + (255,), 9)
        M.rust(cell, 0.18, seed=590 + k, color=RUST, dark=RUSTDARK, cells=(4, 2))
        M.grime(cell, 0.3, seed=594 + k, color=(90, 80, 60), cells=(8, 4), cover=0.5)
        lb.alpha_composite(cell, (x0, y0))
    paints = [("WHITE", (230, 226, 214)), ("BARN RED", (140, 40, 30)), ("GREEN", (60, 100, 60)), ("VARNISH", (120, 76, 36))]
    for k, (word, fill) in enumerate(paints):
        x0, y0 = (k % 4) * 32, 96
        cell = M.brushed_metal(seed=600 + k, base=(160, 158, 152), direction="v")
        cd = ImageDraw.Draw(cell)
        cd.rectangle([0, 6, 31, 25], fill=fill)
        cd.rectangle([0, 6, 31, 8], fill=(40, 40, 40))
        write_text(cell, ["DUTCH BOY" if k % 2 else "SHERWOOD"], (2, 9, 30, 15), "arialbd.ttf", (30, 30, 30, 255) if k == 0 else (240, 236, 220, 255), 6)
        write_text(cell, [word], (2, 15, 30, 24), "arialbd.ttf", (30, 30, 30, 255) if k == 0 else (240, 236, 220, 255), 8)
        M.drips(cell, n=2, seed=604 + k, color=fill, length=(4, 12), strength=0.7)
        M.grime(cell, 0.3, seed=608 + k, color=(80, 70, 56), cells=(8, 4), cover=0.5)
        lb.alpha_composite(rgba(cell), (x0, y0))
    save(lb, "labels")
    # ---- wood and tools ----
    hw = M.wood_planks(seed=611, base=(160, 112, 66), planks=1, direction="v", grain=3, per_plank=3)
    M.grime(hw, 0.3, seed=612, color=(70, 56, 40), cells=(4, 2), cover=0.5)
    save(hw, "handlewood")
    pw = M.wood_planks(seed=613, base=(176, 150, 110), planks=1, direction="v", grain=2, per_plank=2)
    save(pw, "pegwood")
    lu = M.wood_planks(seed=614, base=(124, 98, 66), planks=1, direction="h", grain=4, per_plank=4, flecks=0.8)
    M.grime(lu, 0.3, seed=615, color=(110, 106, 96), cells=(8, 4), cover=0.45)  # dust and cobweb
    M.stain(lu, seed=616, radius=6, color=(70, 56, 40), strength=0.35)
    save(lu, "lumber")
    sf = M.wood_planks(seed=617, base=(104, 80, 54), planks=4, direction="h", grain=3, per_plank=8, gap=(30, 22, 16))
    d = ImageDraw.Draw(sf)
    for k in range(10):  # nail points through from the floor above
        x, y = (k * 13 + 5) % 32, (k * 7 + 3) % 32
        d.point((x, y), fill=(170, 166, 156))
        d.point((x, y + 1), fill=(80, 60, 40))
    M.stain(sf, seed=618, radius=8, color=(66, 52, 36), strength=0.4)
    M.grime(sf, 0.25, seed=619, color=(110, 106, 96), cells=(8, 4), cover=0.4)
    save(sf, "subfloor")
    nm = M.noise_hv((206, 194, 150), 3, seed=620, mottle=4)
    d = ImageDraw.Draw(nm)
    for x in range(0, 32, 8):
        d.line([x, 15, x + 4, 15], fill=(110, 100, 80))  # the printing along it
    save(nm, "nmcable")
    nw = M.painted_metal(seed=621, base=(170, 160, 132), panel=False, chips=8, under=(110, 80, 52))
    M.grime(nw, 0.35, seed=622, color=(90, 80, 60), cells=(8, 4), cover=0.55)
    save(nw, "newel")
    # ---- the crack's broken slab, the Flood's surface ----
    sb = M.concrete(seed=623, base=(104, 104, 98), grain=6, mottle=9, aggregate=0.22, pores=0.03, cracks=2)
    M.grime(sb, 0.3, seed=624, color=(60, 58, 52), cells=(4, 2), cover=0.6)
    save(sb, "slabbreak")
    for k, name in enumerate(("scum-a", "scum-b", "scum-c")):
        f = M.fbm((32, 32), 630 + k, (8, 4, 2))
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        p = img.load()
        rnd = M.fbm((32, 32), 640 + k, (4, 2))
        for y in range(32):
            for x in range(32):
                v = f[y][x]
                if v > 0.12 + 0.08 * k:
                    t = (rnd[y][x] + 1) / 2
                    c = M.mix((70, 76, 44), (104, 92, 56), t)
                    if v > 0.55:
                        c = M.mix(c, (130, 124, 90), 0.4)  # thicker, drier crust
                    p[x, y] = tuple(int(v2) for v2 in c[:3]) + (255,)
        d = ImageDraw.Draw(img)
        for j in range(4):  # a few leaves and specks
            x, y = (j * 11 + k * 5) % 30, (j * 7 + k * 13) % 30
            d.ellipse([x, y, x + 2, y + 1], fill=(96, 62, 30, 255))
        save(img, name)
    sg = M.noise_hv((112, 92, 62), 4, seed=650, mottle=8)
    M.grime(sg, 0.45, seed=651, color=(60, 56, 40), cells=(8, 4, 2), bias="bottom", cover=0.7)
    save(sg, "soggy")
    # ---- the shop light, a gauge's tag, the wall paint under a fixture ----
    sl = M.painted_metal(seed=652, base=(200, 198, 188), panel=False, chips=3, under=(90, 80, 70))
    M.grime(sl, 0.3, seed=653, color=(100, 96, 80), cells=(8, 4), cover=0.5)
    save(sl, "shoplight")
    save(M.noise_hv((246, 246, 236), 2, seed=654, mottle=2), "tube")
    tg = rgba(M.paper(seed=655, size=(32, 32), base=(220, 200, 140)))
    write_text(tg, ["MAIN", "SHUT", "OFF"], (2, 2, 30, 30), "segoeprb.ttf", (120, 24, 20, 255), 10)
    save(tg, "gauge-tag")
    save(M.noise_hv((90, 96, 90), 3, seed=656, mottle=4), "wallpaint")
    # The batts' kraft facing, stapled to the studs by its flanges, the maker's print on it, a tear showing the pink
    kr = rgba(M.paper(seed=657, size=(32, 32), base=(196, 164, 104)))
    d = ImageDraw.Draw(kr)
    for x0 in (3, 19):
        d.line([x0, 0, x0, 31], fill=(120, 90, 58))          # the flange's fold
        d.line([x0 + 12, 0, x0 + 12, 31], fill=(120, 90, 58))
        for y in range(2, 32, 7):
            d.point((x0, y), fill=(190, 190, 184))           # staples
            d.point((x0 + 12, y + 3), fill=(190, 190, 184))
    for k, y in enumerate((5, 21)):
        write_text(kr, ["R-11"], (6 + 2 * k, y, 14 + 2 * k, y + 5), "arialbd.ttf", (90, 60, 40, 255), 6)
        write_text(kr, ["R-11"], (22 - 2 * k, y + 6, 30 - 2 * k, y + 11), "arialbd.ttf", (90, 60, 40, 255), 6)
    d.polygon([(23, 12), (28, 14), (27, 19), (22, 18)], fill=(196, 140, 140))  # torn, the fibreglass behind
    M.grime(kr, 0.3, seed=658, color=(100, 84, 60), cells=(8, 4), cover=0.5)
    M.tideline(kr, 26, seed=659, color=(110, 84, 54), amount=0.35, wave=1.3, below=0.7)
    save(kr, "insulation")
    pc = M.noise_hv((206, 200, 184), 2, seed=660, mottle=3)
    M.grime(pc, 0.3, seed=661, color=(110, 96, 70), cells=(8, 4), cover=0.5)
    M.scratches(pc, n=4, seed=662, length=(2, 4), light=0.25)
    save(pc, "porcelain")
    fl = Image.new("RGBA", (32, 32), (255, 214, 120, 255))
    d = ImageDraw.Draw(fl)
    d.line([4, 16, 10, 10, 16, 16, 22, 10, 28, 16], fill=(255, 250, 220), width=2)
    save(fl, "filament")
    pv = M.noise_hv((206, 204, 194), 2, seed=663, mottle=3)
    M.grime(pv, 0.35, seed=664, color=(120, 110, 86), cells=(8, 4), cover=0.55)
    d = ImageDraw.Draw(pv)
    d.line([0, 12, 31, 12], fill=(150, 60, 120))  # the purple primer at a joint
    save(pv, "pvc")


# ======================================================================== Shapes

# ---- The furnace ----

def furnace_arm(name, cx, cz, by, L, w, theta, run=6.0):
    """One of the octopus's arms in the north frame: a round lagged duct from its base on the bonnet (cx, by, cz),
    climbing north at `theta` degrees from upright, banded at its joints, then turning level under the joists."""
    o = (cx, by, cz)
    r = (-theta, 0, 0)
    n = 0.62 * w
    els = [b(name + "A", (cx - w / 2, by, cz - n / 2), (cx + w / 2, by + L, cz + n / 2), "lagging", rot=r, origin=o),
           b(name + "B", (cx - n / 2, by + 0.01, cz - w / 2), (cx + n / 2, by + L - 0.01, cz + w / 2), "lagging", rot=r, origin=o)]
    c = w + 0.6
    for k, (y0, h, tex) in enumerate(((by + 0.2, 0.9, "galv"), (by + L * 0.5, 1.4, "foiltape"), (by + L - 1.0, 0.9, "galv"))):
        els += [b(f"{name}C{k}A", (cx - c / 2, y0, cz - c * 0.31), (cx + c / 2, y0 + h, cz + c * 0.31), tex, rot=r, origin=o),
                b(f"{name}C{k}B", (cx - c * 0.31, y0 + 0.01, cz - c / 2), (cx + c * 0.31, y0 + h - 0.01, cz + c / 2), tex, rot=r, origin=o)]
    t = math.radians(theta)
    yt, zt = by + L * math.cos(t), cz - L * math.sin(t)
    # (level under the joists: an elbow box, the run, its collar)
    top = 15.9
    els += [b(name + "Elbow", (cx - w / 2 - 0.2, yt - w / 2, zt - w / 2 - 0.4), (cx + w / 2 + 0.2, top, zt + w / 2), "galv"),
            b(name + "Run", (cx - w / 2, top - w * 0.9, zt - w / 2 - run), (cx + w / 2, top, zt - w / 2 - 0.4), "lagging"),
            b(name + "RunTape", (cx - w / 2 - 0.25, top - w * 0.9 - 0.25, zt - w / 2 - run * 0.55), (cx + w / 2 + 0.25, top, zt - w / 2 - run * 0.55 + 1.2), "foiltape")]
    return els


def furnace(part):
    cx, cz = 8, 8.75
    if part == "lower":
        els = [b("Plinth", (0.5, 0, 1.25), (15.5, 1.5, 16), "castiron")]
        for k, (x, z) in enumerate(((0.5, 1.25), (13.5, 1.25), (0.5, 14), (13.5, 14))):
            els.append(b(f"Foot{k}", (x, -0.01, z), (x + 2, 0.6, z + 2), "castiron"))
        els += R3.round_body("Body", cx, cz, 7.25, 1.5, 16, "furnace")
        els += [b("DoorFrame", (4.25, 3, 1.15), (11.75, 10.5, 1.6), "castiron"),
                b("FireDoor", (4.75, 3.5, 0.75), (11.25, 10, 1.25), "furnacedoor"),
                b("HingeT", (4.0, 8.25, 0.9), (5.0, 9.5, 1.4), "castiron"), b("HingeB", (4.0, 4.0, 0.9), (5.0, 5.25, 1.4), "castiron"),
                b("Latch", (9.75, 6.25, 0.25), (10.75, 7.25, 0.75), "brass"), b("LatchBar", (9.0, 6.5, 0.0), (11.5, 7.0, 0.3), "castiron"),
                b("DraftSlide", (6.0, 8.6, 0.55), (10.0, 9.4, 0.75), "castiron"),
                b("AshDoor", (5.5, 1.6, 1.0), (10.5, 3, 1.5), "castiron"), b("AshHandle", (7.5, 2.1, 0.6), (8.5, 2.6, 1.0), "brass"),
                b("Plate", (5, 11, 1.3), (11, 14, 1.9), "furnaceplate", uv=(0, 0, 16, 8))]
        for k, y in enumerate((1.5, 15)):
            els.append(b(f"Band{k}", (cx - 7.5, y, cz - 7.5), (cx + 7.5, y + 1, cz + 7.5), "castiron", rot=(0, 45, 0), origin=(cx, y + 0.5, cz)))
        return els
    if part == "upper":
        els = R3.round_body("Body", cx, cz, 7.25, 0, 7, "furnace")
        els += R3.round_body("Shoulder", cx, cz, 6.5, 7, 10, "furnace")
        els += [b("ShoulderBand", (cx - 6.9, 6.6, cz - 6.9), (cx + 6.9, 7.4, cz + 6.9), "castiron", rot=(0, 45, 0), origin=(cx, 7, cz)),
                b("Bonnet", (3.5, 10, 4.5), (12.5, 16, 13), "lagging"),
                b("BonnetBand", (3.3, 12.5, 4.3), (12.7, 13.5, 13.2), "galv"),
                b("Sight", (6.75, 2.5, 1.3), (9.25, 5, 1.6), "castiron"), b("SightGlass", (7.25, 3.0, 1.2), (8.75, 4.5, 1.3), "bulb-lit", glow=60),
                b("Limit", (10.5, 11, 3.8), (12.5, 14, 4.5), "castiron"), b("LimitDial", (11, 11.75, 3.6), (12, 12.75, 3.8), "brass"),
                b("FlueBoot", (12, 7, 13), (15, 10, 16), "castiron")]
        els += rod_y("Flue", 10, 16, 13.5, 14.5, 2.4, "blackpipe")
        return els
    # top: the bonnet, the return trunk up the back, the flue into the wall's thimble, five arms out to the joists
    els = [b("Bonnet", (3.5, 0, 4.5), (12.5, 3, 13), "lagging"), b("BonnetCap", (4.5, 3, 5.5), (11.5, 3.8, 12), "galv"),
           b("Return", (5, 0, 12.5), (11, 16, 16), "galv"), b("ReturnSeam", (7.75, 0, 12.3), (8.25, 16, 12.5), "galv"),
           b("ReturnFlange", (4.6, 7.5, 12.1), (11.4, 8.3, 16), "galv")]
    els += rod_y("Flue", 0, 8.5, 13.5, 14.5, 2.4, "blackpipe")
    els += rod_z("FlueElbow", 13.0, 16.4, 13.5, 9.7, 2.4, "blackpipe")
    els += [b("FlueCollar", (12.0, 8.2, 13.2), (15.0, 11.2, 13.8), "castiron"),
            b("Thimble", (11.8, 7.0, 15.7), (15.2, 12.4, 16.0), "castiron")]
    arms = []
    arms += furnace_arm("ArmN", 8, 5.5, 2.0, 13.5, 3.2, 38)
    for k, (o, t) in enumerate(((5.5, 40), (10.5, 34))):
        arms += K.turn(furnace_arm(f"ArmW{k}", o, 5.5, 2.0, 13.0 + k, 3.0, t, run=5), 3)
        arms += K.turn(furnace_arm(f"ArmE{k}", o, 5.5, 2.0, 13.5 - k, 3.0, t + 2, run=5), 1)
    return els + arms


# ---- The water heater ----

def heater(part):
    cx, cz = 8, 9.5
    if part == "lower":
        els = R3.round_body("Tank", cx, cz, 5.5, 1.5, 16, "heater")
        for k, (x, z) in enumerate(((4, 5.5), (11, 5.5), (7.5, 14))):
            els.append(b(f"Leg{k}", (x, 0, z), (x + 1, 1.6, z + 1), "castiron"))
        els += [b("Seam", (11.5, 1.5, 4.3), (11.9, 16, 4.6), "heater", rot=(0, 45, 0), origin=(cx, 8, cz)),
                b("Access", (5.5, 2, 3.7), (10.5, 4.5, 4.2), "castiron"),
                b("Control", (6.0, 5, 3.0), (10.0, 9, 4.1), "castiron"), b("Knob", (7.25, 7.5, 2.4), (8.75, 8.5, 3.0), "redwheel"),
                b("Pilot", (6.6, 5.6, 2.9), (7.6, 6.6, 3.0), "bulb-lit", glow=80),
                b("Drain", (7.5, 1.8, 2.8), (8.5, 2.8, 3.8), "brass"), b("DrainCap", (7.6, 1.9, 2.5), (8.4, 2.7, 2.8), "brass"),
                b("Plate", (5.5, 10, 3.55), (10.5, 15.5, 4.1), "heaterplate", uv=(0, 0, 16, 16))]
        # The gas line: from the control out to the side, a tee, the drip leg down, the riser up with its yellow valve
        els += rod_x("Gas", 10, 14.6, 6.5, 3.6, 1.0, "blackpipe")
        els += rod_y("GasRiser", 2.5, 16, 14.6, 3.6, 1.1, "blackpipe")
        els += [b("Tee", (14.0, 5.9, 3.0), (15.2, 7.1, 4.2), "blackpipe"), b("DripCap", (14.05, 2.0, 3.05), (15.15, 2.6, 4.15), "blackpipe"),
                b("Valve", (13.9, 11, 2.9), (15.3, 12.6, 4.3), "brass"), b("ValveHandle", (11.0, 11.4, 3.3), (14.0, 12.2, 3.9), "yellowgrip")]
        # The relief valve's discharge, down the east side to just over the floor
        els += rod_y("Discharge", 2.0, 16, 13.8, 9.5, 1.0, "copper")
        return els
    if part == "upper":
        els = R3.round_body("Tank", cx, cz, 5.5, 0, 11, "heater")
        els += R3.round_body("Dome", cx, cz, 4.8, 11, 12.5, "heater")
        els += [b("Relief", (12.8, 7.5, 8.75), (14.6, 9.5, 10.25), "brass"), b("ReliefLever", (13.6, 9.5, 9.25), (14.0, 11.5, 9.75), "brass")]
        els += rod_y("Discharge", 0, 8, 13.8, 9.5, 1.0, "copper")
        els += rod_y("GasRiser", 0, 16, 14.6, 3.6, 1.1, "blackpipe")
        # The draft hood on its three legs, the flue from it
        els += [b("HoodLegA", (6, 12.5, 8), (6.5, 13.5, 8.5), "galv"), b("HoodLegB", (9.5, 12.5, 8), (10, 13.5, 8.5), "galv"),
                b("HoodLegC", (7.75, 12.5, 11.5), (8.25, 13.5, 12), "galv"),
                b("Hood", (5, 13.5, 6.5), (11, 15, 12.5), "galv"), b("HoodNeck", (6.25, 15, 7.75), (9.75, 16, 11.25), "galv")]
        els += rod_y("Cold", 12.5, 16, 4.25, 9.5, 1.2, "copper") + rod_y("Hot", 12.5, 16, 11.75, 9.5, 1.2, "copper")
        els += [b("NippleC", (3.5, 12.4, 8.75), (5.0, 13.2, 10.25), "brass"), b("NippleH", (11.0, 12.4, 8.75), (12.5, 13.2, 10.25), "brass")]
        return els
    els = rod_y("Flue", 0, 16, 8, 9.5, 3.2, "galv")
    els += [b("FlueJoint", (6.1, 6, 7.6), (9.9, 7, 11.4), "galv")]
    els += rod_y("Cold", 0, 16, 4.25, 9.5, 1.2, "copper") + rod_y("Hot", 0, 16, 11.75, 9.5, 1.2, "copper")
    els += rod_y("GasRiser", 0, 16, 14.6, 3.6, 1.1, "blackpipe")
    # The cold's shut-off: a gate valve, its red handwheel facing out, a tag on it
    els += [b("GateBody", (3.25, 4, 8.5), (5.25, 7, 10.5), "brass"), b("GateStem", (3.9, 5.1, 7.0), (4.6, 5.9, 8.5), "brass")]
    els += ring_xy("Wheel", 4.25, 5.5, 6.4, 7.0, 1.9, 0.5, "redwheel")
    els += [b("WheelHub", (3.9, 5.15, 6.2), (4.6, 5.85, 7.0), "redwheel"),
            b("Tag", (4.6, 2.2, 6.6), (6.6, 4.8, 6.7), "gauge-tag", uv=(0, 0, 16, 16), rot=(0, 0, 8)),
            b("TagCold", (3.45, 9, 8.6), (5.05, 11, 8.75), "pipetags", uv=(0, 8, 16, 16)),
            b("TagHot", (10.95, 9, 8.6), (12.55, 11, 8.75), "pipetags", uv=(0, 0, 16, 8))]
    return els


# ---- The boiler (the utility rooms': a cast-iron sectional boiler, in place of Level 5's) ----

def boiler(part):
    """Against a wall (to the south), facing north. Lower: the cast-iron sections on a base, ribbed, the front section's
    fire door and the burner under it, the tridicator gauge, the relief valve and the return coming down to the bottom.
    Upper: the supply riser with its gate valve and tag, the flue: both bend back into the wall."""
    if part == "lower":
        els = [b("Base", (1, 0, 2), (15, 2, 15.5), "castiron")]
        for k in range(6):
            z = 3.0 + k * 2.0
            els += [b(f"Section{k}", (1.6, 2, z), (14.4, 13.5, z + 1.6), "castiron"),
                    b(f"SectionTop{k}", (3.0, 13.5, z + 0.2), (13.0, 14.5, z + 1.4), "castiron")]
        els += [b("Core", (2.2, 2, 3.0), (13.8, 13.2, 14.8), "castiron"),
                b("Front", (1.2, 2, 1.6), (14.8, 14.0, 3.0), "castiron"),
                b("FireDoor", (4.0, 6.5, 1.1), (12.0, 11.5, 1.6), "furnacedoor"),
                b("Hinge", (3.4, 7.0, 1.2), (4.2, 11.0, 1.6), "castiron"), b("Latch", (10.6, 8.5, 0.6), (11.6, 9.5, 1.1), "brass"),
                b("Burner", (5.0, 2.4, 1.2), (11.0, 5.0, 1.6), "metaldark"), b("Peep", (7.4, 3.2, 1.0), (8.6, 4.2, 1.2), "bulb-lit", glow=40),
                b("Plate", (5.0, 12.0, 1.1), (11.0, 13.6, 1.25), "furnaceplate", uv=(0, 0, 16, 8))]
        els += K.gauge("Tri", 12.6, 15.0, 2.4, r=1.6, angle=50, face="dialface", body="brass", needle="redwheel", depth=1.2, stem=False)
        els += [b("TriStem", (12.4, 13.0, 2.6), (12.8, 13.5, 3.4), "brass")]
        els += rod_y("Return", 2.5, 16, 14.8, 13.5, 1.6, "blackpipe")
        els += [b("ReturnTee", (13.9, 3.0, 12.6), (15.7, 5.0, 14.4), "blackpipe"), b("Drain", (14.4, 3.5, 11.6), (15.2, 4.5, 12.6), "brass")]
        els += rod_y("Supply", 14.5, 16, 8.0, 9.0, 2.0, "blackpipe")
        els += [b("Relief", (3.0, 14.5, 9.0), (4.6, 16.0, 10.6), "brass")]
        return els
    els = rod_y("Supply", 0, 9.5, 8.0, 9.0, 2.0, "blackpipe")
    els += [b("Elbow", (6.8, 8.5, 7.8), (9.2, 11.5, 10.2), "blackpipe")]
    els += rod_z("SupplyOut", 10.0, 16.4, 8.0, 10.0, 2.0, "blackpipe")
    els += [b("GateBody", (6.6, 3.0, 7.6), (9.4, 6.0, 10.4), "brass"), b("GateStem", (7.7, 4.1, 5.8), (8.3, 4.9, 7.6), "brass")]
    els += ring_xy("Wheel", 8.0, 4.5, 5.2, 5.8, 1.8, 0.5, "redwheel")
    els += [b("Tag", (8.6, 1.4, 5.3), (10.6, 4.0, 5.4), "gauge-tag", uv=(0, 0, 16, 16), rot=(0, 0, -8))]
    els += rod_y("Return", 0, 12.0, 14.8, 13.5, 1.6, "blackpipe")
    els += rod_z("ReturnOut", 13.0, 16.4, 14.8, 12.0, 1.6, "blackpipe")
    els += [b("Collar", (6.4, 8.4, 15.6), (9.6, 11.6, 16.0), "castiron"), b("Collar2", (13.6, 10.8, 15.6), (16.0, 13.2, 16.0), "castiron")]
    els += rod_y("Flue", 0, 6, 4.0, 12.5, 2.6, "blackpipe")
    els += rod_z("FlueOut", 11.5, 16.4, 4.0, 5.2, 2.6, "blackpipe")
    els += [b("Thimble", (2.2, 3.4, 15.6), (5.8, 7.0, 16.0), "castiron")]
    return els


# ---- The laundry ----

def appliance_shell(console):
    els = K.bevelled_box("Body", (0.75, 1.0, 1.5), (15.25, 13.5, 15.0), "enamel", b=0.5)
    els += [b("Top", (0.5, 13.5, 1.25), (15.5, 14.25, 15.25), "enamel"),
            b("Console", (0.75, 14.25, 11.5), (15.25, 18.5, 14.5), {"north": console, "all": "enamel"}, uv=None),
            b("ConsoleTrim", (0.6, 18.5, 11.3), (15.4, 19.0, 14.7), "chrome"),
            b("Kick", (1.5, 1.0, 1.25), (14.5, 2.4, 1.5), "castiron")]
    els[-3]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    for k, x in enumerate((3.5, 8, 12.5)):
        els.append(b(f"Dial{k}", (x - 0.8, 15.6, 10.8), (x + 0.8, 17.2, 11.5), "bakelite"))
        els.append(b(f"DialPip{k}", (x - 0.15, 16.7, 10.6), (x + 0.15, 17.1, 10.8), "chrome"))
    for k, (x, z) in enumerate(((1, 2), (13.5, 2), (1, 13), (13.5, 13))):
        els.append(b(f"Foot{k}", (x, 0, z), (x + 1.5, 1.0, z + 1.5), "castiron"))
    return els


def laundry(kind, part):
    if part == "lower":
        if kind == "tub":
            return laundry_tub()
        els = appliance_shell("console-" + kind)
        cx, cy = 7.5, 7.5
        if kind == "washer":
            els += ring_xy("Port", cx, cy, 0.7, 1.5, 4.8, 1.0, "chrome")
            els += [b("Glass", (cx - 3.9, cy - 3.9, 1.1), (cx + 3.9, cy + 3.9, 1.3), "drumglass", faces=("north",), uv=(0, 0, 16, 16)),
                    b("Handle", (12.6, 6.0, 0.6), (13.6, 9.5, 1.5), "chrome"),
                    b("Drawer", (11.5, 11.3, 1.2), (14.5, 12.8, 1.5), "enamel"), b("DrawerLip", (12.2, 11.6, 0.9), (13.8, 12.1, 1.2), "chrome")]
        else:
            # the dryer: a solid door with a small window, a lint screen in its top, the foil vent from its back
            els += ring_xy("Door", cx, cy, 0.8, 1.5, 5.0, 1.2, "enamel")
            els += [b("DoorFace", (cx - 3.9, cy - 3.9, 1.0), (cx + 3.9, cy + 3.9, 1.3), "enamel"),
                    b("Window", (cx - 2, cy - 1, 0.9), (cx + 2, cy + 2.5, 1.0), "drumglass", faces=("north",), uv=(2, 2, 14, 14)),
                    b("Handle", (12.6, 6.0, 0.6), (13.6, 9.5, 1.5), "chrome"),
                    b("Lint", (3, 14.25, 5), (12, 14.4, 8), "castiron", faces=("up",)),
                    b("Vent", (9.5, 4, 15.0), (13.5, 16, 16.4), "foilduct"),
                    b("VentClamp", (9.3, 5.5, 14.8), (13.7, 6.3, 16.4), "galv")]
        # hoses (washer) up behind the console
        if kind == "washer":
            els += [b("HoseHot", (3.0, 14.25, 14.6), (4.0, 16, 15.6), "hose-red"), b("HoseCold", (5.0, 14.25, 14.6), (6.0, 16, 15.6), "hose-blue")]
        return els
    # upper: the wall over them. The washer: a shelf of soap and bleach on brackets, the hose bib and its two hoses;
    # the dryer: its foil vent rising behind it and bending into the wall under a hood
    if kind == "washer":
        els = [b("HoseHot", (3.0, 0, 14.6), (4.0, 3.0, 15.6), "hose-red"), b("HoseCold", (5.0, 0, 14.6), (6.0, 3.0, 15.6), "hose-blue"),
               b("Bib", (2.5, 3.0, 15.0), (6.5, 5.0, 16.0), "brass"), b("BibPlate", (2.0, 2.5, 15.8), (7.0, 5.5, 16.0), "castiron"),
               b("KnobHot", (2.6, 5.0, 15.2), (3.8, 5.8, 15.9), "redwheel"), b("KnobCold", (5.2, 5.0, 15.2), (6.4, 5.8, 15.9), "hose-blue"),
               b("Shelf", (1, 9, 10.5), (15, 9.75, 16), "panel"),
               b("BracketA", (2, 6.5, 15.25), (2.75, 9, 16), "castiron"), b("BracketA2", (2, 8.25, 11.5), (2.75, 9, 15.25), "castiron"),
               b("BracketB", (13.25, 6.5, 15.25), (14, 9, 16), "castiron"), b("BracketB2", (13.25, 8.25, 11.5), (14, 9, 15.25), "castiron"),
               b("Soap", (2, 9.75, 11.5), (6.5, 15.5, 14.5), {"north": "detergent", "all": "cardboard"}),
               b("Jug", (8, 9.75, 11.5), (11, 14, 14.5), {"north": "jug", "all": "jug"}),
               b("JugNeck", (8.5, 14, 12.5), (9.75, 15, 13.75), "jug"), b("JugCap", (8.4, 15, 12.4), (9.85, 15.6, 13.85), "hose-blue"),
               b("JugHandle", (9.9, 13.6, 12.6), (10.7, 14.6, 13.6), "jug"),
               b("Starch", (12, 9.75, 12), (14, 13.5, 14), "tin")]
        els[-7]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        els[-6]["faces"]["north"]["uv"] = [0, 0, 16, 16]
        return els
    if kind == "dryer":
        return [b("Vent", (9.5, 0, 15.0), (13.5, 6, 16.4), "foilduct"),
                b("VentBend", (9.5, 5.5, 13.4), (13.5, 9.5, 16.2), "foilduct"),
                b("Hood", (8.5, 4.5, 15.6), (14.5, 10.5, 16.0), "galv"), b("HoodClamp", (9.3, 6.8, 13.2), (13.7, 7.6, 15.6), "galv")]
    # the tub's: a soap dish and a scrub brush on a nail
    return [b("Dish", (3, 1.5, 14), (6, 2.3, 16), "tub"), b("Soap", (3.5, 2.3, 14.4), (5.5, 3.1, 15.6), "ivory"),
            b("Nail", (10.8, 6.5, 15.0), (11.2, 6.9, 16), "metal"), b("Brush", (9.5, 2.5, 15.0), (12.5, 6.5, 15.6), "handlewood"),
            b("Bristles", (9.6, 2.5, 14.4), (12.4, 6.4, 15.0), "rope")]


def laundry_tub():
    els = []
    for k, (x, z) in enumerate(((1.5, 3.5), (13.5, 3.5), (1.5, 13.5), (13.5, 13.5))):
        els += K.leg(f"Leg{k}", x + 0.5, z + 0.5, 0, 9, t=1.0, tex="metal", foot=0.4)
    els += [b("Brace", (2, 3, 13.75), (14, 3.6, 14.25), "metal")]
    # the tub: walls, a bottom, a divider; stained inside, a rolled lip
    els += [b("Bottom", (1, 9, 3), (15, 10, 15), {"up": "tubin", "all": "tub"}),
            b("Front", (1, 10, 2.5), (15, 16, 3.5), {"south": "tubin", "all": "tub"}),
            b("Back", (1, 10, 14.5), (15, 18, 15.5), {"north": "tubin", "all": "tub"}),
            b("West", (1, 10, 3.5), (2, 16, 14.5), {"east": "tubin", "all": "tub"}),
            b("East", (14, 10, 3.5), (15, 16, 14.5), {"west": "tubin", "all": "tub"}),
            b("Divider", (7.75, 10, 3.5), (8.25, 15.5, 14.5), "tub"),
            b("Lip", (0.8, 15.9, 2.3), (15.2, 16.4, 3.6), "tub"),
            b("DrainW", (4, 10.01, 8), (5.5, 10.1, 9.5), "castiron", faces=("up",)),
            b("DrainE", (10.5, 10.01, 8), (12, 10.1, 9.5), "castiron", faces=("up",))]
    # its faucet on the back ledge, a hose on its threaded spout
    els += [b("Faucet", (6, 16.5, 13.2), (10, 17.8, 14.6), "chrome"),
            b("Spout", (7.4, 14.8, 11.0), (8.6, 17.2, 13.2), "chrome"),
            b("HandleH", (5.0, 17.3, 13.6), (6.4, 18.4, 14.2), "redwheel"), b("HandleC", (9.6, 17.3, 13.6), (11.0, 18.4, 14.2), "hose-blue")]
    # the trap under it, into the wall
    els += rod_y("Tail", 5, 9, 8, 9, 1.2, "blackpipe")
    els += rod_z("Trap", 9, 16, 8, 4.4, 1.2, "blackpipe")
    return els


# ---- The rec room ----

def cut2(els):
    return R3.cut2(els)


def sofa():
    els = []
    for k, x in enumerate((1.5, 29)):
        for z in (3, 13.5):
            els.append(b(f"Foot{k}{z}", (x, 0, z), (x + 1.5, 1.5, z + 1.5), "walnut"))
    els += [b("Base", (0.5, 1.5, 2.5), (31.5, 6, 15.5), "plaid"),
            b("Skirt", (0.4, 1.4, 2.3), (31.6, 2.4, 2.5), "plaid"),
            b("Back", (0.5, 6, 12.5), (31.5, 17, 15.5), "plaid"),
            b("BackTop", (0.7, 17, 12.9), (31.3, 17.8, 15.3), "plaid")]
    # three seat cushions (the middle one sagging), three back cushions leaning back
    for k, (x, sag) in enumerate(((3.6, 0.3), (12.0, 0.9), (20.4, 0.2))):
        els += K.bevelled_box(f"Seat{k}", (x, 6, 2.0), (x + 8.2, 9.6 - sag, 12.6), "plaid", b=0.6)
        els += [b(f"Pipe{k}", (x - 0.05, 9.0 - sag, 1.9), (x + 8.25, 9.3 - sag, 2.05), "plaid")]
        els += [dict(e, rotationOrigin=[x + 4.1, 9.5, 12.5], rotationX=10 + k * 2) for e in
                K.bevelled_box(f"Cush{k}", (x, 9.5, 9.6), (x + 8.2, 17.6, 12.5), "plaid", b=0.6)]
    for k, x in enumerate((0, 28.4)):
        els += K.bevelled_box(f"Arm{k}", (x, 1.5, 2.5), (x + 3.6, 11.5, 15.5), "plaid", b=0.5)
        els += [b(f"ArmRoll{k}", (x - 0.3, 10.5, 2.1), (x + 3.9, 13.0, 15.5), "plaid"),
                b(f"ArmFront{k}", (x - 0.2, 9.0, 2.0), (x + 3.8, 12.6, 2.4), "plaid")]
    # a crocheted throw over the back on the left, down onto the seat
    els += [b("ThrowTop", (3.4, 17.8, 12.3), (12.4, 18.4, 15.8), "throw"),
            b("ThrowBack", (3.4, 11.5, 15.5), (12.4, 18.4, 16.1), "throw"),
            b("ThrowFront", (3.6, 12.0, 9.2), (12.2, 17.8, 9.6), "throw", rot=(10, 0, 0), origin=(7.9, 9.5, 12.5)),
            b("ThrowFold", (3.6, 17.4, 9.2), (12.2, 18.4, 12.3), "throw")]
    return cut2(els)


def tv(part):
    if part == "lower":
        els = []
        for k, (x, z) in enumerate(((2.5, 4.5), (13.5, 4.5), (2.5, 12.5), (13.5, 12.5))):
            els += K.leg(f"Leg{k}", x, z, 0, 3.2, t=1.2, tex="walnut", taper=0.5, foot=0.3)
        els += K.bevelled_box("Cabinet", (1, 3, 3.5), (15, 15.2, 13), "walnut", b=0.5)
        els += [b("Lid", (0.6, 15.2, 3.2), (15.4, 15.8, 13.3), "walnut"),
                b("Hump", (3.5, 5, 13), (12.5, 13.5, 15.6), "tvback"), b("HumpCap", (5, 6.5, 15.6), (11, 12, 16.2), "tvback"),
                # the screen: a bezel round a domed face, proud of the cabinet
                b("Bezel", (2.2, 5.6, 3.0), (11.0, 14.2, 3.5), "bakelite"),
                b("Screen", (2.8, 6.2, 2.85), (10.4, 13.6, 3.0), "tvscreen", faces=("north",), uv=(0, 0, 16, 16)),
                b("Dome", (3.6, 7.0, 2.7), (9.6, 12.8, 2.85), "tvscreen", faces=("north", "east", "west", "up", "down"), uv=(2, 2, 14, 14)),
                b("Speaker", (11.6, 6.2, 3.2), (14.2, 14.0, 3.5), "speakercloth"),
                b("Badge", (11.8, 4.2, 3.2), (14.0, 5.0, 3.5), "chrome"),
                b("KnobA", (3.5, 3.9, 2.6), (5.1, 5.3, 3.5), "bakelite"), b("KnobB", (6.5, 3.9, 2.6), (8.1, 5.3, 3.5), "bakelite"),
                b("KnobPipA", (4.15, 4.9, 2.45), (4.45, 5.2, 2.6), "chrome"), b("KnobPipB", (7.15, 4.9, 2.45), (7.45, 5.2, 2.6), "chrome")]
        return els
    # upper: on its lid (0.2 down from this block), a doily, the rabbit ears, a photograph in a frame
    els = [b("Doily", (3, -0.19, 5), (13, -0.12, 12), "doily", faces=("up",), uv=(0, 0, 16, 16)),
           b("EarsBase", (6, -0.2, 7), (10, 1.0, 10), "bakelite"), b("EarsDome", (6.8, 1.0, 7.6), (9.2, 1.9, 9.4), "bakelite")]
    for k, (x, a) in enumerate(((7.3, 26), (8.7, -22))):
        o = (x, 1.5, 8.5)
        els += [b(f"Rod{k}", (x - 0.25, 1.5, 8.25), (x + 0.25, 15.5, 8.75), "chrome", rot=(0, 0, a), origin=o),
                b(f"Seg{k}", (x - 0.35, 1.5, 8.15), (x + 0.35, 6.5, 8.85), "chrome", rot=(0, 0, a), origin=o),
                b(f"Tip{k}", (x - 0.45, 15.5, 8.05), (x + 0.45, 16.3, 8.95), "chrome", rot=(0, 0, a), origin=o)]
    els += [b("Frame", (11, -0.2, 9.5), (14.4, 4.0, 10.1), {"north": "photo", "all": "brass"}, rot=(10, 0, 0), origin=(12.7, 0, 10))]
    els[-1]["faces"]["north"]["uv"] = [0, 0, 16, 16]
    return els


def pooltable():
    els = []
    # turned legs
    for k, (x, z) in enumerate(((3.25, 4.5), (28.75, 4.5), (3.25, 11.5), (28.75, 11.5))):
        els += [b(f"LegFoot{k}", (x - 1.4, 0, z - 1.4), (x + 1.4, 1.2, z + 1.4), "mahogany"),
                b(f"LegLow{k}", (x - 0.8, 1.2, z - 0.8), (x + 0.8, 3.5, z + 0.8), "mahogany"),
                b(f"LegBulb{k}", (x - 1.3, 3.5, z - 1.3), (x + 1.3, 6.0, z + 1.3), "mahogany"),
                b(f"LegTop{k}", (x - 1.0, 6.0, z - 1.0), (x + 1.0, 8.0, z + 1.0), "mahogany")]
    els += K.bevelled_box("Apron", (1.5, 8, 2.5), (30.5, 10.5, 13.5), "mahogany", b=0.5)
    els += [b("Bed", (1.5, 10.5, 2.0), (30.5, 11.5, 14.0), "felt")]
    # rails, split at the six pockets; the cushions inside them
    for k, (x1, x2) in enumerate(((2.6, 14.6), (17.4, 29.4))):
        els += [b(f"RailN{k}", (x1, 10.2, 0.5), (x2, 13.0, 2.0), "mahogany"), b(f"RailS{k}", (x1, 10.2, 14.0), (x2, 13.0, 15.5), "mahogany"),
                b(f"CushN{k}", (x1 + 0.3, 11.5, 2.0), (x2 - 0.3, 12.6, 2.9), "cushion"),
                b(f"CushS{k}", (x1 + 0.3, 11.5, 13.1), (x2 - 0.3, 12.6, 14.0), "cushion")]
    for k, x in enumerate((0.0, 30.5)):
        els += [b(f"RailE{k}", (x, 10.2, 2.6), (x + 1.5, 13.0, 13.4), "mahogany")]
    els += [b("CushW", (1.5, 11.5, 2.9), (2.4, 12.6, 13.1), "cushion"), b("CushE", (29.6, 11.5, 2.9), (30.5, 12.6, 13.1), "cushion")]
    pockets = [(1.3, 1.25), (16.0, 1.0), (30.7, 1.25), (1.3, 14.75), (16.0, 15.0), (30.7, 14.75)]
    for k, (x, z) in enumerate(pockets):
        els += [b(f"PocketBlock{k}", (x - 1.3, 10.2, z - 1.25), (x + 1.3, 12.6, z + 1.25), "mahogany"),
                b(f"Pocket{k}", (x - 0.9, 12.62, z - 0.9), (x + 0.9, 12.64, z + 0.9), "bakelite", faces=("up",)),
                b(f"Drop{k}", (x - 1.0, 8.2, z - 1.0), (x + 1.0, 10.2, z + 1.0), "leather")]
    for k, x in enumerate((6.0, 10.3, 21.7, 26.0)):
        for z in (1.25, 14.75):
            els.append(b(f"Sight{k}{int(z)}", (x - 0.25, 13.0, z - 0.25), (x + 0.25, 13.08, z + 0.25), "ivory", faces=("up",)))
    for k, z in enumerate((5.5, 8.0, 10.5)):
        for x in (0.75, 31.25):
            els.append(b(f"SightE{k}{int(x)}", (x - 0.25, 13.0, z - 0.25), (x + 0.25, 13.08, z + 0.25), "ivory", faces=("up",)))
    # the balls racked at the foot (apex toward the head), the cue ball at the head, the wooden triangle round them
    n = 0
    for row in range(5):
        for j in range(row + 1):
            x = 22.0 + row * 0.95
            z = 8.0 + (j - row / 2) * 1.08
            n += 1
            cell = n if n < 16 else 1
            u, v = (cell % 4) * 4, (cell // 4) * 4
            els += [b(f"Ball{n}A", (x - 0.5, 11.5, z - 0.35), (x + 0.5, 12.45, z + 0.35), "poolballs", uv=(u, v, u + 4, v + 4)),
                    b(f"Ball{n}B", (x - 0.35, 11.55, z - 0.5), (x + 0.35, 12.5, z + 0.5), "poolballs", uv=(u, v, u + 4, v + 4))]
    els += [b("CueBallA", (8.5, 11.5, 7.65), (9.5, 12.45, 8.35), "poolballs", uv=(0, 0, 4, 4)),
            b("CueBallB", (8.65, 11.55, 7.5), (9.35, 12.5, 8.5), "poolballs", uv=(0, 0, 4, 4))]
    els += [b("RackBack", (26.3, 11.5, 5.1), (26.8, 12.3, 10.9), "maple"),
            b("RackA", (21.0, 11.5, 7.9), (27.0, 12.3, 8.4), "maple", rot=(0, 28, 0), origin=(21.2, 11.9, 8.0)),
            b("RackB", (21.0, 11.5, 7.6), (27.0, 12.3, 8.1), "maple", rot=(0, -28, 0), origin=(21.2, 11.9, 8.0)),
            b("Chalk", (29.6, 13.0, 13.9), (30.6, 13.8, 14.9), "chalk")]
    return cut2(els)


def cuerack():
    """Floor-standing against a wall (wall to the south): a walnut back board, cups at the foot, a notched top rail,
    four cues of the five, the chalk and a bridge on its shelf."""
    els = [b("Board", (2, 4, 15), (14, 26, 16), "walnut"),
           b("Cups", (2, 5, 12.5), (14, 6.5, 15), "walnut"), b("CupsLip", (2, 6.5, 12.5), (14, 7.0, 13.0), "walnut"),
           b("Rail", (2, 21, 12.8), (14, 22.5, 15), "walnut"), b("Shelf", (2, 25.2, 12.2), (14, 26, 15), "walnut"),
           b("Chalk1", (3, 26, 13), (4, 26.8, 14), "chalk"), b("Chalk2", (5, 26, 13.2), (6, 26.8, 14.2), "chalk")]
    for k, x in enumerate((3.4, 5.8, 10.6, 13.0)):  # (the third slot empty)
        z = 13.8
        els += [b(f"Butt{k}", (x - 0.45, 6.5, z - 0.45), (x + 0.45, 13.5, z + 0.45), "cuebutt"),
                b(f"Wrap{k}", (x - 0.4, 13.5, z - 0.4), (x + 0.4, 16.0, z + 0.4), "bakelite"),
                b(f"Shaft{k}", (x - 0.3, 16.0, z - 0.3), (x + 0.3, 29.6, z + 0.3), "maple"),
                b(f"Ferrule{k}", (x - 0.28, 29.6, z - 0.28), (x + 0.28, 30.1, z + 0.28), "ivory"),
                b(f"Tip{k}", (x - 0.26, 30.1, z - 0.26), (x + 0.26, 30.4, z + 0.26), "chalk")]
    return els


def poollamp():
    """The green-shaded billiard lamp over each half of the table: a flared shade of four tilted panels, its lit
    underside, a brass cap and finial, the chain up to the joists."""
    els = [b("Top", (4, 6, 5.5), (12, 6.6, 10.5), "poolshade"),
           b("PanelN", (2.6, 2.4, 5.3), (13.4, 6.0, 5.8), "poolshade", rot=(30, 0, 0), origin=(8, 6, 5.5)),
           b("PanelS", (2.6, 2.4, 10.2), (13.4, 6.0, 10.7), "poolshade", rot=(-30, 0, 0), origin=(8, 6, 10.5)),
           b("PanelW", (3.8, 2.4, 5.4), (4.3, 6.0, 10.6), "poolshade", rot=(0, 0, -30), origin=(4, 6, 8)),
           b("PanelE", (11.7, 2.4, 5.4), (12.2, 6.0, 10.6), "poolshade", rot=(0, 0, 30), origin=(12, 6, 8)),
           b("Glow", (3.4, 3.2, 4.6), (12.6, 3.25, 11.4), "bulb-lit", faces=("down",), glow=150),
           b("Cap", (6.5, 6.6, 7), (9.5, 7.4, 9), "brass"), b("Finial", (7.5, 7.4, 7.5), (8.5, 8.4, 8.5), "brass"),
           b("Chain", (7.8, 8.4, 7.8), (8.2, 16, 8.2), "metaldark"),
           b("RimN", (2.0, 2.0, 3.3), (14.0, 2.5, 3.8), "brass"), b("RimS", (2.0, 2.0, 12.2), (14.0, 2.5, 12.7), "brass")]
    return els


# ---- The store: steel shelving loaded with labelled jars, tins and paint ----

def jar(name, x, y, z, w, h, cell):
    u, v = (cell % 4) * 4, (cell // 4) * 4
    return [b(name, (x, y, z), (x + w, y + h, z + w), "labels", uv=(u, v, u + 4, v + 4)),
            b(name + "Lid", (x - 0.1, y + h, z - 0.1), (x + w + 0.1, y + h + 0.6, z + w + 0.1), "brass")]


def tin(name, x, y, z, d, h, cell, lid="tin"):
    u, v = (cell % 4) * 4, (cell // 4) * 4
    r = d / 2
    cx, cz = x + r, z + r
    return [b(name + "A", (x, y, z), (x + d, y + h, z + d), {"north": "labels", "south": "labels", "east": "labels", "west": "labels",
                                                              "up": lid, "down": lid}, uv=(u, v, u + 4, v + 4)),
            b(name + "B", (x + 0.05, y + 0.02, z + 0.05), (x + d - 0.05, y + h - 0.02, z + d - 0.05), "tin",
              rot=(0, 45, 0), origin=(cx, y + h / 2, cz))]


def shelving(part, kind):
    els = []
    for k, (x, z) in enumerate(((0.5, 3), (14.5, 3), (0.5, 14.5), (14.5, 14.5))):
        # angle posts: two flanges
        els += [b(f"PostA{k}", (x, 0, z), (x + 1, 16, z + 0.35), "metal"), b(f"PostB{k}", (x + (0.65 if x > 8 else 0), 0, z), (x + (1 if x > 8 else 0.35), 16, z + 1), "metal")]
    levels = (1, 8) if part == "lower" else (0, 7, 14)
    for k, y in enumerate(levels):
        els += [b(f"Shelf{k}", (0.5, y, 3), (15.5, y + 0.5, 15.5), "metal"), b(f"Lip{k}", (0.5, y - 0.4, 2.9), (15.5, y + 0.5, 3.25), "metal")]
    for k, y in enumerate(levels[:2] if part == "upper" else levels):
        y0 = y + 0.5
        if kind == "boxes":
            els += [b(f"BoxA{k}", (1.5, y0, 5), (8, y0 + 5.5, 14.5), "cardboard"), b(f"BoxB{k}", (8.5, y0, 6), (14, y0 + 4 + k, 14.5), "cardboard"),
                    b(f"FlapA{k}", (1.5, y0 + 5.5, 5), (8, y0 + 5.9, 8.5), "cardboard", rot=(-35, 0, 0), origin=(4.75, y0 + 5.5, 5)),
                    b(f"TapeB{k}", (10.8, y0 + 4 + k, 6), (11.8, y0 + 4.05 + k, 14.5), "cardboardtop", faces=("up",))]
        elif kind == "jars":
            for j in range(4):
                cell = (j * 3 + k * 5 + (part == "upper") * 2) % 8
                h = 4.0 if j % 2 else 3.2
                els += jar(f"Jar{k}{j}", 1.4 + j * 3.5, y0, 4.5 + (j % 2) * 3.5, 2.8, h, cell)
            els += jar(f"Back{k}", 3.0, y0, 10.5, 2.6, 3.6, (k * 3 + 7) % 8)
            els += tin(f"Tin{k}", 9.5, y0, 11.0, 2.4, 3.2, 8 + (k + (part == "upper")) % 4)
        elif kind == "paint":
            for j in range(3):
                if (j + k) % 3 == 2:
                    continue
                x = 1.4 + j * 4.6
                els += tin(f"Can{k}{j}", x, y0, 4.8, 3.8, 4.4, 12 + (j + k * 2) % 4, lid="metal")
                els += [b(f"Bail{k}{j}", (x + 0.2, y0 + 4.4, 6.5), (x + 3.6, y0 + 5.2, 6.9), "metaldark"),
                        b(f"LidRim{k}{j}", (x + 0.3, y0 + 4.4, 5.1), (x + 3.5, y0 + 4.7, 8.3), "metaldark")]
            els += [b(f"Tray{k}", (2, y0, 10), (13, y0 + 1, 14), "metaldark"), b(f"Roller{k}", (3, y0 + 1, 11), (9, y0 + 2.2, 12.2), "rug")]
        else:  # odds and ends: a box, a jar, tins of nails
            els += [b(f"Box{k}", (1.5, y0, 6), (7, y0 + 4, 14), "cardboard")]
            els += jar(f"Jar{k}", 8.5, y0, 6, 2.6, 3.6, (k + 1) % 8)
            els += tin(f"Can{k}", 11.5, y0, 9, 3.0, 4.0, 8 + k % 4)
    return els


# ---- Boxes, the wine rack, the fuse box, the coal chute (round 3's, given their hardware) ----

def boxes(part, kind):
    """Cardboard boxes stacked two high: flaps folded in with packing tape over the seam and down the front, a crushed
    corner on the big one, the top one's flap sprung open."""
    tex = "box-" + kind
    face = {"north": tex, "south": "cardboard", "east": "cardboard", "west": "cardboard", "up": "cardboardtop", "down": "cardboard"}
    if part == "lower":
        els = [b("Big", (1, 0, 3), (15, 9, 15), face, uv=(0, 0, 16, 16)), b("Mid", (2, 9, 4), (14, 16, 14.5), face, uv=(0, 0, 16, 16)),
               b("TapeTop", (7.2, 16, 4), (8.8, 16.05, 14.5), "cardboardtop", faces=("up",)),
               b("TapeFront", (7.2, 12.5, 3.95), (8.8, 16, 4.0), "cardboardtop", faces=("north",)),
               b("Crush", (12.5, 6.5, 2.6), (15.4, 9.2, 5.0), "cardboard", rot=(0, 0, -18), origin=(15, 9, 3.8))]
        return els
    return [b("Small", (3, 0, 5), (12, 6, 14), face, rot=(0, 10, 0), origin=(7.5, 3, 9.5), uv=(0, 4, 16, 14)),
            b("FlapOpen", (3, 6, 5), (12, 6.4, 9.5), "cardboard", rot=(-55, 10, 0), origin=(7.5, 6, 5)),
            b("Flat", (2, 6, 4), (11, 8, 13), "cardboard", rot=(0, -15, 0), origin=(6.5, 7, 8.5))]


def winerack(part):
    """The wine rack: dusty bottles on their sides, foil capsules on their necks, labels where the light catches them."""
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
            cap = "redwheel" if (r + c) % 3 else "brass"
            els += [b(f"Bottle{r}{c}A", (x + 0.75, y + 0.9, 8.0), (x + 3.25, y + 3.4, 14.5), "bottle"),
                    b(f"Bottle{r}{c}B", (x + 1.0, y + 0.65, 8.3), (x + 3.0, y + 3.65, 14.4), "bottle"),
                    b(f"Shoulder{r}{c}", (x + 1.1, y + 1.1, 7.0), (x + 2.9, y + 3.2, 8.0), "bottle"),
                    b(f"Neck{r}{c}", (x + 1.5, y + 1.6, 5.4), (x + 2.5, y + 2.6, 7.0), cap),
                    b(f"Dust{r}{c}", (x + 0.85, y + 3.4, 8.6), (x + 3.15, y + 3.45, 14.0), "cobweb", faces=("up",), uv=(0, 0, 6, 6))]
    if part == "upper":
        els.append(b("Top", (0.5, 15.5, 6), (15.5, 16, 15.5), "panel"))
    return els


def fusebox():
    """The fuse box: its door swung open on two hinges, the breakers inside behind their panel, the main switch's
    handle, the conduit up from it with its straps and a locknut."""
    inside = {"north": "fuseinside", "south": "fusebox", "east": "fusebox", "west": "fusebox", "up": "fusebox", "down": "fusebox"}
    return [b("Box", (3, 1, 13), (13, 13, 16), inside, uv=(0, 0, 16, 16)),
            b("Trim", (2.6, 0.6, 12.6), (13.4, 1.0, 16), "fusebox"), b("TrimT", (2.6, 13.0, 12.6), (13.4, 13.4, 16), "fusebox"),
            b("Door", (2.0, 1.2, 4.0), (2.5, 12.8, 12.8), "fusebox"),
            b("DoorLip", (2.0, 1.2, 3.6), (3.0, 12.8, 4.0), "fusebox"),
            b("DoorLatch", (1.6, 6.5, 4.5), (2.0, 7.5, 5.5), "metal"),
            b("HingeT", (2.2, 10.5, 12.6), (3.2, 12.0, 13.4), "metal"), b("HingeB", (2.2, 2.0, 12.6), (3.2, 3.5, 13.4), "metal"),
            b("Main", (11.0, 9.0, 12.2), (12.6, 12.0, 13.0), "metaldark"), b("MainHandle", (11.5, 11.5, 11.4), (12.1, 12.2, 12.2), "redwheel"),
            b("Conduit", (7, 13.4, 14), (9, 16, 16), "metal"), b("Locknut", (6.6, 13.4, 13.6), (9.4, 14.0, 16), "metal"),
            b("ConduitLow", (10, 0, 14.5), (11.5, 1, 16), "metal")]


def chute():
    """The coal chute: its iron hatch high in the wall in a frame, hinged at the top, a handle, propped a little open;
    the trough down from it, the coal dust under it."""
    return [b("FrameT", (2, 14.5, 15), (14, 16, 16), "chute"), b("FrameB", (2, 4, 15), (14, 5.5, 16), "chute"),
            b("FrameW", (2, 5.5, 15), (3.5, 14.5, 16), "chute"), b("FrameE", (12.5, 5.5, 15), (14, 14.5, 16), "chute"),
            b("Dark", (3.5, 5.5, 15.8), (12.5, 14.5, 16), "bakelite", faces=("north",)),
            b("Hatch", (3.2, 5.6, 14.3), (12.8, 14.6, 14.9), "chute", rot=(-14, 0, 0), origin=(8, 14.6, 14.9)),
            b("HingeW", (4.0, 14.2, 14.2), (5.5, 15.2, 15.2), "castiron"), b("HingeE", (10.5, 14.2, 14.2), (12.0, 15.2, 15.2), "castiron"),
            b("Handle", (7, 6.4, 13.4), (9, 7.2, 14.2), "castiron", rot=(-14, 0, 0), origin=(8, 14.6, 14.9)),
            b("Rivets", (3.8, 13.4, 14.2), (12.2, 13.8, 14.4), "castiron", rot=(-14, 0, 0), origin=(8, 14.6, 14.9)),
            b("Trough", (4, 0, 6), (12, 1, 16), "chute", rot=(-30, 0, 0), origin=(8, 3, 16)),
            b("TroughW", (3.5, 0, 6), (4, 3, 16), "chute", rot=(-30, 0, 0), origin=(8, 3, 16)),
            b("TroughE", (12, 0, 6), (12.5, 3, 16), "chute", rot=(-30, 0, 0), origin=(8, 3, 16))]


# ---- The workshop ----

def bench():
    els = [b("Top", (0, 13, 3), (32, 15, 16), "benchtop"), b("Apron", (0.5, 10.5, 3), (31.5, 13, 3.75), "benchtop"),
           b("Shelf", (1, 3, 4), (31, 4, 15.5), "benchtop"), b("Back", (0, 15, 15), (32, 18, 16), "benchtop")]
    for k, (x, z) in enumerate(((1, 4), (29, 4), (1, 13.5), (29, 13.5))):
        els.append(b(f"Leg{k}", (x, 0, z), (x + 2, 13, z + 2), "panel"))
    els += [b("Stretcher", (3, 3.5, 4.5), (29, 4.25, 5.25), "panel")]
    # the vice, bolted to the top on the left: its swivel base, the fixed jaw, the sliding jaw out front on its bar,
    # serrated jaw plates, the screw and its T-handle with knobs on its ends
    els += [b("ViceBase", (2.5, 15, 3.5), (8.5, 15.8, 8.5), "vicepaint"),
            b("ViceSwivel", (3.2, 15.8, 4.2), (7.8, 16.4, 7.8), "vicepaint"),
            b("ViceFixed", (3.5, 16.4, 5.0), (7.5, 20.0, 7.6), "vicepaint"),
            b("ViceAnvil", (3.8, 20.0, 5.6), (7.2, 20.6, 7.6), "toolsteel"),
            b("ViceJawPlateB", (3.6, 18.2, 4.6), (7.4, 20.0, 5.0), "toolsteel"),
            b("ViceSlide", (4.6, 16.6, 1.8), (6.4, 17.8, 5.0), "vicepaint"),
            b("ViceFront", (3.5, 16.4, 0.6), (7.5, 20.0, 2.6), "vicepaint"),
            b("ViceJawPlateF", (3.6, 18.2, 2.6), (7.4, 20.0, 3.0), "toolsteel"),
            b("ViceNut", (4.7, 16.7, 0.0), (6.3, 18.3, 0.6), "toolsteel"),
            b("ViceScrew", (5.2, 17.2, -1.6), (5.8, 17.8, 0.0), "toolsteel"),
            b("ViceHandle", (2.0, 17.25, -1.5), (9.0, 17.75, -1.0), "toolsteel"),
            b("ViceKnobW", (1.6, 17.0, -1.75), (2.2, 18.0, -0.75), "toolsteel"),
            b("ViceKnobE", (8.8, 17.0, -1.75), (9.4, 18.0, -0.75), "toolsteel")]
    # on the bench: a coffee can of nails, a can of brushes, a block, a hammer; under it a toolbox and paint
    els += [b("NailCan", (12, 15, 8), (14.5, 18.5, 10.5), "paintcan", uv=(4, 4, 8, 8.5)), b("BrushCan", (24, 15, 11), (26.5, 18, 13.5), "paintcan", uv=(8, 4, 12, 8.5)),
            b("Brush", (24.75, 18, 11.75), (25.75, 21, 12.75), "panel"), b("Bristle", (24.6, 21, 11.6), (25.9, 22.5, 12.9), "rope"),
            b("Block", (17, 15, 5), (22, 16.5, 9), "panel", rot=(0, 22.5, 0)),
            b("HammerHandle", (18.5, 15, 10.5), (19.5, 15.75, 15), "handlewood", rot=(0, -22.5, 0), origin=(19, 15.4, 12.75)),
            b("HammerHead", (17, 15, 14), (21, 16.5, 15.25), "toolsteel", rot=(0, -22.5, 0), origin=(19, 15.4, 12.75)),
            b("Toolbox", (4, 4, 6), (11, 8, 10), "redpaint"), b("ToolboxLid", (3.8, 8, 5.8), (11.2, 8.6, 10.2), "redpaint"),
            b("ToolboxHandle", (6.5, 8.6, 7.75), (8.5, 9.4, 8.25), "metal"),
            b("Paint1", (20, 4, 6), (23, 8, 9), "labels", uv=(4, 12, 8, 16)), b("Paint2", (24, 4, 7), (27, 8, 10), "labels", uv=(12, 12, 16, 16)),
            b("Rag", (27, 15, 6), (30, 15.6, 9), "cloth-towel", rot=(0, 15, 0))]
    return cut2(els)


def pegboard(kind):
    """On the south face (the wall), facing north. The tools are models on their hooks, not paint."""
    els = [b("Board", (0, 1, 15.2), (16, 15, 15.75), "pegboard", uv=(0, 0, 16, 14)),
           b("FrameT", (0, 14.6, 15.0), (16, 15.4, 16), "panel"), b("FrameB", (0, 0.6, 15.0), (16, 1.4, 16), "panel")]

    def hook(n, x, y):
        return [b(f"Hook{n}", (x - 0.2, y - 0.2, 14.0), (x + 0.2, y + 0.2, 15.2), "metal"),
                b(f"HookUp{n}", (x - 0.2, y + 0.2, 14.0), (x + 0.2, y + 0.9, 14.4), "metal")]
    if kind == "pegboard-a":
        # a hand saw, two wrenches, a coil of extension cord
        els += [b("SawBlade", (1.5, 6.5, 14.8), (9.5, 9.8, 15.0), "toolsteel"), b("SawTip", (1.0, 7.8, 14.8), (1.6, 9.8, 15.0), "toolsteel"),
                b("SawTeeth", (1.5, 6.1, 14.82), (9.5, 6.5, 14.98), "metaldark"),
                b("SawHandleT", (9.4, 9.0, 14.5), (12.2, 10.4, 15.15), "handlewood"),
                b("SawHandleB", (9.4, 5.6, 14.5), (11.6, 6.8, 15.15), "handlewood"),
                b("SawGrip", (11.0, 5.6, 14.5), (12.2, 10.4, 15.15), "handlewood"),
                b("SawRivet", (9.8, 7.7, 14.4), (10.4, 8.3, 14.5), "brass")]
        els += hook("S", 10.6, 10.6)
        for k, (x, y1, y2, hw) in enumerate(((13.0, 3.0, 12.0, 1.6), (14.8, 4.5, 11.5, 1.3))):
            els += [b(f"Wr{k}", (x - 0.35, y1, 14.8), (x + 0.35, y2, 15.1), "toolsteel"),
                    b(f"WrOpenL{k}", (x - hw / 2, y2, 14.8), (x - 0.15, y2 + 1.4, 15.1), "toolsteel"),
                    b(f"WrOpenR{k}", (x + 0.15, y2, 14.8), (x + hw / 2, y2 + 1.4, 15.1), "toolsteel"),
                    b(f"WrRing{k}", (x - hw / 2 + 0.1, y1 - 1.2, 14.8), (x + hw / 2 - 0.1, y1, 15.1), "toolsteel")]
            els += hook(f"W{k}", x, y2 + 1.6)
        els += [b("CordT", (2.8, 4.6, 14.2), (7.2, 5.2, 15.1), "grip"), b("CordB", (3.0, 0.9, 14.2), (7.0, 1.5, 15.1), "grip"),
                b("CordW", (2.6, 1.3, 14.2), (3.2, 4.8, 15.1), "grip"), b("CordE", (6.8, 1.3, 14.2), (7.4, 4.8, 15.1), "grip"),
                b("CordIn", (3.6, 1.7, 14.4), (6.6, 4.3, 14.7), "grip"),
                b("Plug", (4.7, 0.0, 14.3), (5.6, 1.0, 14.9), "bakelite")]
        els += hook("C", 5.0, 5.4)
    else:
        # a claw hammer, three screwdrivers, pliers, a square, a tape measure
        els += [b("HammerHandle", (3.4, 2.5, 14.65), (4.4, 10.0, 15.15), "handlewood"),
                b("HammerHead", (1.6, 10.0, 14.5), (5.6, 11.6, 15.2), "toolsteel"),
                b("HammerFace", (1.2, 10.2, 14.55), (1.7, 11.4, 15.15), "toolsteel"),
                b("HammerClaw", (5.4, 10.2, 14.6), (7.0, 11.0, 15.1), "toolsteel", rot=(0, 0, -25), origin=(5.5, 10.6, 14.85))]
        els += hook("H", 3.9, 12.0)
        for k, (x, col) in enumerate(((8.0, "redpaint"), (9.4, "yellowgrip"), (10.8, "redpaint"))):
            els += [b(f"DrvHandle{k}", (x - 0.5, 8.0, 14.6), (x + 0.5, 11.5, 15.2), col),
                    b(f"DrvShaft{k}", (x - 0.15, 3.5 + k * 0.8, 14.8), (x + 0.15, 8.0, 15.0), "toolsteel")]
        els += [b("DrvRack", (7.0, 11.5, 13.8), (11.6, 12.0, 15.2), "panel")]
        els += [b("PliersL", (6.0, 2.0, 14.75), (6.6, 6.0, 15.1), "grip", rot=(0, 0, 6), origin=(6.6, 6.0, 14.9)),
                b("PliersR", (6.8, 2.0, 14.75), (7.4, 6.0, 15.1), "grip", rot=(0, 0, -6), origin=(6.8, 6.0, 14.9)),
                b("PliersJaw", (6.2, 6.0, 14.75), (7.2, 8.0, 15.1), "toolsteel")]
        els += [b("Square", (11.5, 2, 14.85), (15, 2.75, 15.15), "toolsteel"), b("SquareArm", (11.5, 2.75, 14.85), (12.25, 9, 15.15), "toolsteel"),
                b("Tape", (12.6, 10.8, 14.2), (14.8, 13.0, 15.2), "yellowgrip"), b("TapeBlade", (12.0, 10.8, 14.4), (12.7, 11.3, 15.0), "toolsteel")]
        els += hook("T", 13.7, 13.3)
    return els


def shoplight():
    """A two-tube fluorescent shop light hung on chains over the workbench, along it (west to east, two blocks long:
    this block holds it all, from x 2 to 26)."""
    els = [b("Housing", (2, 6, 6), (26, 7.6, 10.5), "shoplight"),
           b("LipN", (2, 4.6, 5.6), (26, 6.4, 6.1), "shoplight"), b("LipS", (2, 4.6, 10.4), (26, 6.4, 10.9), "shoplight"),
           b("EndW", (1.6, 4.6, 5.6), (2.1, 7.6, 10.9), "shoplight"), b("EndE", (25.9, 4.6, 5.6), (26.4, 7.6, 10.9), "shoplight"),
           b("TubeA", (2.2, 4.8, 6.6), (25.8, 5.6, 7.4), "tube", glow=200), b("TubeB", (2.2, 4.8, 9.1), (25.8, 5.6, 9.9), "tube", glow=200),
           b("ChainW", (5.8, 7.6, 8.05), (6.2, 16, 8.45), "metaldark"), b("ChainE", (21.8, 7.6, 8.05), (22.2, 16, 8.45), "metaldark"),
           b("Cord", (13.8, 7.6, 8.1), (14.2, 16, 8.4), "bakelite")]
    return els


# ---- The clothesline ----

def overhead(kind):
    """In the top block of air, along x (the ns variant is turned). The web keeps round 3's."""
    if kind == "cobweb":
        return R3.overhead("cobweb")
    els = [b("Line", (0, 12.1, 7.85), (16, 12.45, 8.2), "rope")]

    def peg(n, x):
        return [b(f"Peg{n}F", (x, 10.6, 7.45), (x + 0.5, 13.0, 7.85), "pegwood"),
                b(f"Peg{n}B", (x, 10.6, 8.2), (x + 0.5, 13.0, 8.6), "pegwood"),
                b(f"Peg{n}S", (x - 0.05, 11.7, 7.4), (x + 0.55, 12.1, 8.65), "metal")]
    if kind == "shirt":
        els += [b("Body", (4.5, 3.2, 7.6), (11.5, 11.9, 8.45), "cloth-shirt"),
                b("Yoke", (4.3, 10.4, 7.5), (11.7, 12.1, 8.55), "cloth-shirt"),
                b("Collar", (6.5, 11.6, 7.4), (9.5, 12.4, 8.65), "cloth-sheet"),
                b("Placket", (7.75, 3.4, 7.5), (8.25, 11.4, 7.6), "cloth-sheet"),
                b("Hem", (4.6, 2.6, 7.65), (11.4, 3.2, 8.4), "cloth-shirt", rot=(0, 0, 3), origin=(8, 3, 8)),
                b("Pocket", (5.4, 8.0, 7.5), (7.2, 9.8, 7.6), "cloth-shirt"),
                b("SleeveW", (2.4, 5.2, 7.7), (4.6, 11.8, 8.35), "cloth-shirt", rot=(0, 0, -14), origin=(4.6, 11.8, 8)),
                b("SleeveE", (11.4, 5.2, 7.7), (13.6, 11.8, 8.35), "cloth-shirt", rot=(0, 0, 14), origin=(11.4, 11.8, 8))]
        els += peg("A", 4.8) + peg("B", 10.8)
    elif kind == "sheet":
        els += [b("Front", (0.5, 1.2, 7.25), (15.5, 12.3, 7.75), "cloth-sheet"),
                b("Rear", (0.5, 3.6, 8.3), (15.5, 12.3, 8.8), "cloth-sheet"),
                b("Fold", (0.5, 12.3, 7.25), (15.5, 12.8, 8.8), "cloth-sheet"),
                b("Crease1", (4.0, 1.4, 7.15), (4.6, 11.8, 7.25), "cloth-sheet"),
                b("Crease2", (10.5, 2.0, 7.15), (11.3, 11.6, 7.25), "cloth-sheet"),
                b("Corner", (13.0, 0.4, 7.3), (15.4, 1.4, 7.7), "cloth-sheet", rot=(0, 0, -12), origin=(15.4, 1.4, 7.5))]
        els += peg("A", 1.5) + peg("B", 13.5)
    elif kind == "towel":
        els += [b("Front", (5, 4.5, 7.35), (11, 12.3, 7.8), "cloth-towel"), b("Rear", (5, 6.4, 8.25), (11, 12.3, 8.7), "cloth-towel"),
                b("Fold", (5, 12.3, 7.35), (11, 12.75, 8.7), "cloth-towel"),
                b("Fringe", (5, 4.0, 7.4), (11, 4.5, 7.75), "rope"),
                b("Sock1", (12.5, 7.0, 7.7), (13.6, 12.2, 8.35), "cloth-shirt"), b("Sock1Foot", (12.5, 7.0, 7.7), (14.8, 8.2, 8.35), "cloth-shirt")]
        els += peg("A", 5.5) + peg("B", 10.0) + peg("C", 12.8)
    else:  # a bare stretch, a peg or two left on it
        els += peg("A", 6.0) + peg("B", 11.5)
    return els


# ---- The caged bulb ----

def lamp(lit):
    """A bare bulb in a porcelain socket hanging on its cord, a wire cage round it on a hook, a pull chain."""
    bulb = "bulb-lit" if lit else "bulb-off"
    g = 170 if lit else 0
    els = [b("Rose", (6.5, 15.2, 6.5), (9.5, 16, 9.5), "porcelain"),
           b("Cord", (7.8, 10.5, 7.8), (8.2, 15.2, 8.2), "bakelite")]
    els += oct_xz("Socket", 8, 8, 1.3, 8.2, 10.5, "porcelain")
    els += [b("SocketRing", (6.5, 8.0, 6.5), (9.5, 8.4, 9.5), "brass"),
            b("Chain", (9.2, 4.5, 7.9), (9.4, 9.0, 8.1), "brass"), b("ChainBead", (9.0, 4.0, 7.7), (9.6, 4.6, 8.3), "brass")]
    # the bulb: a neck and a round body, the filament glowing inside when lit
    els += [b("Neck", (7.2, 6.8, 7.2), (8.8, 8.0, 8.8), bulb, glow=g)]
    els += oct_xz("Bulb", 8, 8, 1.6, 4.0, 6.8, bulb)
    for e in els[-2:]:
        for f in e["faces"].values():
            if g:
                f["glow"] = g
    if lit:
        els.append(b("Filament", (7.4, 5.0, 7.95), (8.6, 6.0, 8.05), "filament", glow=255, faces=("north", "south")))
    # the cage: a hook on the socket, two rings, six bars, a bottom cross
    els += [b("Hook", (7.6, 8.0, 7.6), (8.4, 8.6, 8.4), "cage")]
    for k, y in enumerate((7.6, 3.4)):
        els += [b(f"RingN{k}", (5.4, y, 5.4), (10.6, y + 0.4, 5.8), "cage"), b(f"RingS{k}", (5.4, y, 10.2), (10.6, y + 0.4, 10.6), "cage"),
                b(f"RingW{k}", (5.4, y, 5.8), (5.8, y + 0.4, 10.2), "cage"), b(f"RingE{k}", (10.2, y, 5.8), (10.6, y + 0.4, 10.2), "cage")]
    for k, (x, z) in enumerate(((5.4, 5.4), (10.2, 5.4), (5.4, 10.2), (10.2, 10.2), (7.8, 5.4), (7.8, 10.2))):
        els.append(b(f"Bar{k}", (x, 3.4, z), (x + 0.4, 7.6, z + 0.4), "cage"))
    els += [b("CrossA", (5.8, 3.0, 7.8), (10.2, 3.4, 8.2), "cage"), b("CrossB", (7.8, 3.0, 5.8), (8.2, 3.4, 10.2), "cage"),
            b("Top", (6.6, 7.6, 7.8), (9.4, 8.0, 8.2), "cage")]
    return els


# ---- The stud wall ----

def studs(part):
    """Runs west to east (the ns variant turned): two studs, the kraft-faced batts between them, the bottom plate (low)
    or the doubled top plate (top)."""
    els = [b("Batt", (0, 0, 2.5), (16, 16, 13.5), "insulation", uv=(0, 0, 16, 16))]
    for k, x in enumerate((0, 8)):
        els.append(b(f"Stud{k}", (x, 0, 0), (x + 1.5, 16, 16), "studs"))
    if part == "low":
        els.append(b("Plate", (0, 0, 0), (16, 1.5, 16), "studs"))
    elif part == "top":
        els += [b("Plate", (0, 14.5, 0), (16, 16, 16), "studs"), b("Plate2", (0, 13.0, 0.1), (16, 14.5, 15.9), "studs")]
    else:
        els.append(b("Block", (9.5, 7.0, 0.3), (16, 8.5, 15.7), "studs"))  # a fire block between two studs
    return els


# ---- The joists ----

def joists(kind):
    """The ceiling of a finished room, as a model, joists along x (the ns variant turned): the subfloor's underside, two
    joists, and by kind NM cable stapled along one, a junction box with its cable, or cross bridging."""
    els = [b("Subfloor", (0, 14.5, 0), (16, 16, 16), "subfloor")]
    for k, z in enumerate((3.0, 11.0)):
        els.append(b(f"Joist{k}", (0, 9.75, z), (16, 14.5, z + 1.75), "lumber"))
    if kind in ("cable", "box"):
        els += [b("Cable", (0, 12.0, 4.75), (16, 12.6, 5.25), "nmcable")]
        for k, x in enumerate((3.5, 11.5)):
            els.append(b(f"Staple{k}", (x, 11.8, 4.7), (x + 0.4, 12.8, 5.35), "metal"))
    if kind == "box":
        els += oct_xz("Box", 8, 7.5, 1.8, 12.4, 14.5, "jbox")
        els += [b("BoxCover", (6.4, 12.1, 5.9), (9.6, 12.4, 9.1), "jbox"),
                b("Drop", (7.5, 12.6, 5.25), (8.5, 13.4, 6.0), "nmcable")]
    if kind == "bridge":
        for k, (a, o) in enumerate(((40, 13.0), (-40, 13.0))):
            els.append(b(f"Bridge{k}", (o - 0.4, 10.0, 7.0), (o + 0.4, 14.3, 7.6), "lumber", rot=(a, 0, 0), origin=(o, 12.15, 7.85)))
            els.append(b(f"BridgeB{k}", (o - 0.4, 10.0, 8.1), (o + 0.4, 14.3, 8.7), "lumber", rot=(-a, 0, 0), origin=(o, 12.15, 7.85)))
        els.append(b("Cobweb", (9, 10.2, 4.8), (9.05, 14.5, 11.0), "cobweb", faces=("east", "west"), uv=(0, 0, 16, 16)))
    return els


# ---- The hall's duct and the mains beside it ----

def duct(fit):
    """Along x (the ns variant turned): the duct on the north side, a copper water main and a black gas line beside
    it on hangers; a gate valve with its handwheel and tag, or a pressure gauge, on some blocks."""
    els = [b("Duct", (0, 7.5, 1.5), (16, 14.5, 9.5), "duct", faces=("north", "south", "up", "down")),
           b("Flange", (0, 7.2, 1.2), (0.8, 14.8, 9.8), "duct"),
           b("Strap", (9, 7, 1.0), (10, 16, 1.4), "duct"), b("StrapS", (9, 7, 9.6), (10, 16, 10.0), "duct"),
           b("StrapB", (9, 7, 1.0), (10, 7.4, 10.0), "duct")]
    els += rod_x("Water", 0, 16, 12.6, 11.9, 1.3, "copper")
    els += rod_x("Gas", 0, 16, 12.4, 14.4, 1.5, "blackpipe")
    els += [b("WaterCoupling", (0, 11.8, 11.1), (0.9, 13.4, 12.7), "copper"), b("GasCoupling", (15.0, 11.4, 13.5), (16, 13.4, 15.3), "blackpipe"),
            b("HangerRodW", (4.3, 13.2, 11.75), (4.6, 16, 12.05), "metal"), b("HangerW", (3.9, 11.7, 11.0), (5.0, 12.0, 12.8), "metal"),
            b("HangerRodG", (12.3, 13.1, 14.25), (12.6, 16, 14.55), "metal"), b("HangerG", (11.9, 11.4, 13.4), (13.0, 11.7, 15.4), "metal")]
    if fit == "valve":
        els += [b("ValveBody", (6.5, 11.4, 10.8), (9.0, 13.8, 13.0), "brass"),
                b("ValveBonnet", (7.25, 9.8, 11.5), (8.25, 11.4, 12.3), "brass"),
                b("ValveStem", (7.55, 8.8, 11.75), (7.95, 9.8, 12.05), "brass")]
        els += ring_xz("Wheel", 7.75, 8.3, 11.9, 1.9, 0.45, 0.5, "redwheel")
        els += [b("Tag", (8.6, 5.4, 13.6), (10.6, 8.2, 13.7), "gauge-tag", faces=("north", "south"), uv=(0, 0, 16, 16), rot=(0, 0, -6))]
    elif fit == "gauge":
        g = K.gauge("Gauge", 8, 9.6, 2.6, r=1.7, angle=35, face="dialface", body="brass", needle="redwheel", depth=1.1, stem=False)
        els += K.turn(g, 2)
        els += [b("GaugeStem", (7.8, 11.3, 12.4), (8.2, 12.3, 12.9), "brass"), b("GaugeTee", (7.3, 11.6, 11.1), (8.7, 13.6, 12.7), "brass")]
    return els


# ---- The stairs down into the Flood ----

def rail():
    """For the upper step (it climbs north; its tread at y 0 for z 0-8, y -8 for z 8-16, the water's surface at y 0):
    a pipe rail along its west side at 45 degrees, from a newel at the top that leans out (it wobbles) down into the
    water, a baluster standing in the water, a bracket to the wall."""
    x = 1.6
    els = [b("Rail", (x - 0.45, 6.6, 5.0), (x + 0.45, 7.5, 25.0), "railpipe", rot=(45, 0, 0), origin=(x, 7.05, 15.0)),
           b("RailB", (x - 0.3, 6.45, 5.05), (x + 0.3, 7.65, 24.95), "railpipe", rot=(45, 0, 0), origin=(x, 7.05, 15.0))]
    lean = (5, 0, -3)
    o = (x, 0, 7.5)
    els += [b("Newel", (x - 1.0, 0, 6.5), (x + 1.0, 15.0, 8.5), "newel", rot=lean, origin=o),
            b("NewelCap", (x - 1.3, 15.0, 6.2), (x + 1.3, 16.0, 8.8), "newel", rot=lean, origin=o),
            b("NewelBall", (x - 0.7, 16.0, 6.8), (x + 0.7, 17.0, 8.2), "newel", rot=lean, origin=o),
            b("NewelBase", (x - 1.3, 0, 6.2), (x + 1.3, 1.0, 8.8), "newel", rot=lean, origin=o),
            b("Bolt", (x + 0.9, 3.0, 7.0), (x + 1.4, 3.6, 7.6), "castiron", rot=lean, origin=o),
            b("Baluster", (x - 0.35, -8.0, 13.65), (x + 0.35, 8.0, 14.35), "railpipe"),
            b("Bracket", (-0.2, 9.6, 11.2), (x, 10.2, 11.8), "castiron"), b("BracketPlate", (-0.1, 8.8, 10.7), (0.2, 11.0, 12.3), "castiron")]
    return els


def wallrail():
    """A handrail on the outer wall of an Escherian stairwell (the wall to the west of a step that climbs north): a
    pipe at 45 degrees on two brackets, in the block over the step."""
    x = 1.4
    els = [b("Rail", (x - 0.4, 13.6, -4.7), (x + 0.4, 14.4, 20.7), "railpipe", rot=(45, 0, 0), origin=(x, 14, 8)),
           b("RailB", (x - 0.25, 13.45, -4.65), (x + 0.25, 14.55, 20.65), "railpipe", rot=(45, 0, 0), origin=(x, 14, 8))]
    for k, z in enumerate((3.5, 12.5)):
        y = 22 - z - 0.9
        els += [b(f"Arm{k}", (0, y - 0.3, z - 0.3), (x, y + 0.3, z + 0.3), "castiron"),
                b(f"Plate{k}", (0, y - 1.0, z - 0.8), (0.3, y + 0.6, z + 0.8), "castiron")]
    return els


# ---- The sump and its pump ----

def sump():
    """The sump pit in a room's corner (the walls to the north and west): the concrete rim, black water a block down,
    the pump standing in it with its float, the grate over it, the discharge pipe up through the grate's corner."""
    els = [b("RimN", (0, 0, 0), (16, 16, 3), "floor-dry"), b("RimS", (0, 0, 13), (16, 16, 16), "floor-dry"),
           b("RimW", (0, 0, 3), (3, 16, 13), "floor-dry"), b("RimE", (13, 0, 3), (16, 16, 13), "floor-dry"),
           b("Bottom", (3, 0, 3), (13, 2, 13), "floor-dry"), b("Water", (3, 8, 3), (13, 8.5, 13), "sumpwater", faces=("up",))]
    els += oct_xz("Pump", 9, 9, 2.4, 2, 11, "castiron")
    els += [b("PumpCap", (7.4, 11, 7.4), (10.6, 12, 10.6), "castiron"),
            b("FloatRod", (12.0, 6, 9.4), (12.4, 13, 9.8), "metal"), b("Float", (11.4, 9, 8.8), (13.0, 10.4, 10.4), "redwheel"),
            b("Outlet", (6.4, 10, 4.6), (8.6, 11.2, 9.2), "pvc")]
    els += rod_y("Riser", 10, 16, 4.0, 4.0, 1.4, "pvc")
    els += [b("Cord", (9.6, 12, 4.2), (10.0, 16, 4.6), "bakelite")]
    for k in range(5):
        els.append(b(f"Bar{k}", (3 + k * 2.25, 15, 2.5), (4 + k * 2.25, 16, 13.5), "grate"))
    els += [b("FrameN", (2.5, 15, 2.5), (13.5, 16, 3.5), "grate"), b("FrameS", (2.5, 15, 12.5), (13.5, 16, 13.5), "grate")]
    return els


def sumppipe(part):
    """Over the sump (walls north and west): the white discharge pipe up the corner, a check valve and a union, a strap
    to the wall, the pump's cord to an outlet; up top it bends into the north wall."""
    if part == "low":
        els = rod_y("Pipe", 0, 16, 4.0, 4.0, 1.4, "pvc")
        els += [b("Check", (3.0, 5, 3.0), (5.0, 8.5, 5.0), "pvc"), b("CheckBolt", (2.7, 6.5, 3.6), (5.3, 7.0, 4.4), "castiron"),
                b("Union", (3.2, 11, 3.2), (4.8, 12, 4.8), "pvc"),
                b("Strap", (3.1, 13.5, 0), (4.9, 14.1, 4.9), "metal"),
                b("Cord", (9.6, 0, 1.6), (10.0, 9.5, 2.0), "bakelite"), b("CordRun", (9.6, 0, 2.0), (10.0, 0.4, 4.6), "bakelite"),
                b("OutletBox", (8.6, 9.5, 0), (11.4, 13.5, 0.8), "metal"), b("Plug", (9.4, 10.2, 0.8), (10.2, 11.2, 1.6), "bakelite")]
        return els
    els = rod_y("Pipe", 0, 9, 4.0, 4.0, 1.4, "pvc")
    els += [b("Elbow", (3.1, 8.5, 2.6), (4.9, 10.5, 4.9), "pvc")]
    els += rod_z("Out", -0.5, 3.2, 4.0, 9.5, 1.4, "pvc")
    els += [b("Collar", (2.8, 8.0, 0), (5.2, 11.0, 0.4), "castiron"), b("Strap", (3.1, 4, 0), (4.9, 4.6, 4.9), "metal")]
    return els


def debris(kind):
    """Under the crack: what came down with whoever fell, heaped: broken slab with its rebar, a stained ceiling tile and
    a strip of the yellow wallpaper from the room above, a scrap of its wet carpet, splintered floorboards, grit."""
    els = [b("Grit", (0.5, 0, 0.5), (15.5, 0.25, 15.5), "slabbreak", faces=("up", "north", "south", "east", "west"))]
    if kind == "boards":
        els += [b("Board1", (1, 0.25, 6), (15, 1.25, 9), "panel", rot=(0, 22.5, 0)),
                b("Board2", (3, 0.5, 3), (13, 1.5, 5.5), "panel", rot=(0, -22.5, 8), origin=(8, 1, 4.25)),
                b("Splinter", (12.5, 0.5, 3.6), (15.5, 1.1, 4.4), "panel", rot=(0, -40, 15), origin=(12.5, 0.8, 4)),
                b("Board3", (4, 0.25, 11), (14, 1.75, 13.5), "panel", rot=(0, 8, -10), origin=(9, 1, 12.25)),
                b("Carpet", (2, 0.3, 1), (11, 0.8, 9), "lobbycarpet", rot=(0, 22.5, 0)),
                b("CarpetFold", (2.5, 0.8, 1.5), (10.5, 1.2, 4.5), "lobbycarpet", rot=(-25, 22.5, 0), origin=(6.5, 0.8, 4.5)),
                b("Tile", (8, 1.25, 7), (14, 1.75, 12.5), "lobbytile", rot=(0, 30, 12), origin=(11, 1.5, 9.75), uv=(0, 0, 8, 8)),
                b("Chunk", (10, 0.25, 1.5), (13.5, 3.25, 5), "slabbreak", rot=(0, 45, 0)),
                b("Rebar", (9.5, 2.5, 3.0), (15.5, 3.0, 3.5), "rebar", rot=(0, 30, -20), origin=(11.5, 2.75, 3.25))]
        return els
    els += [b("Chunk1", (2, 0.25, 3), (8, 4.5, 8.5), "slabbreak", rot=(0, 22.5, 10), origin=(5, 2, 5.75)),
            b("Chunk2", (8, 0.25, 7), (14, 3.0, 12), "slabbreak", rot=(8, -22.5, 0), origin=(11, 1.5, 9.5)),
            b("Chunk3", (4, 0.25, 10), (7.5, 2.0, 13.5), "slabbreak", rot=(0, 45, 0)),
            b("Chunk4", (9.5, 0.25, 2), (12.5, 1.75, 5), "slabbreak", rot=(0, 15, 0)),
            b("UnderCeil", (2.2, 4.5, 3.2), (7.8, 4.55, 8.3), "ceiling-under", faces=("up",), rot=(0, 22.5, 10), origin=(5, 2, 5.75)),
            b("RebarA", (1.0, 3.6, 5.3), (11.0, 4.1, 5.8), "rebar", rot=(0, 22.5, 18), origin=(5, 3.85, 5.5)),
            b("RebarB", (5.5, 2.4, 2.5), (6.0, 2.9, 12.5), "rebar", rot=(-12, 10, 0), origin=(5.75, 2.65, 7.5)),
            b("Carpet", (7, 0.3, 12.5), (15, 0.8, 15.5), "lobbycarpet", rot=(0, -22.5, 0)),
            b("Paper", (1, 0.3, 12), (6, 0.5, 15), "lobbypaper", rot=(0, 30, 0), uv=(0, 0, 10, 6)),
            b("Tile", (10, 3.0, 7.5), (14.5, 3.4, 11.5), "lobbytile", rot=(15, -22.5, 0), origin=(12.25, 3.2, 9.5), uv=(0, 0, 8, 8)),
            b("Board", (1, 0.25, 0.5), (12, 1.25, 2.5), "panel", rot=(0, 5, 6), origin=(6.5, 0.75, 1.5))]
    return els


# ---- The crack's broken edge ----

def slabedge(kind):
    """The ceiling slab beside the crack (the hole to the north): the slab's underside like the ceiling, its edge broken
    back in chunks, rebar ends sticking out and bent down into the hole."""
    under = {"down": "ceiling-under", "all": "slabbreak"}
    if kind == "a":
        chunks = [((0, 0, 5), (16, 16, 16)), ((0, 5, 2), (6, 16, 5)), ((6, 9, 3.5), (11, 16, 5)), ((11, 3, 1), (16, 16, 5)),
                  ((2, 2, 4.2), (5, 5.01, 5))]
        bars = [(3.5, 11, 0.0, -35), (8.5, 12, 3.5, -60), (13.5, 8, 1.0, -20)]
    else:
        chunks = [((0, 0, 4), (16, 16, 16)), ((0, 8, 0.5), (5, 16, 4)), ((5, 4, 2.5), (12, 16, 4)), ((12, 10, 1.5), (16, 16, 4))]
        bars = [(2.5, 12.5, 0.5, -10), (7.0, 9.5, 2.5, -45), (10.5, 9.5, 2.5, -80), (14.0, 12.5, 1.5, -30)]
    els = [b(f"Slab{k}", f, t, under) for k, (f, t) in enumerate(chunks)]
    for k, (x, y, z0, a) in enumerate(bars):
        els.append(b(f"Rebar{k}", (x - 0.3, y - 0.3, z0 - 6.0), (x + 0.3, y + 0.3, z0 + 1.0), "rebar", rot=(a, 0, 0), origin=(x, y, z0)))
    els.append(b("Spall", (6, 0, 5.0), (11, 0.6, 8.0), "slabbreak", rot=(8, 0, 0), origin=(8.5, 0.3, 5.0)))
    return els


# ---- The Flood's surface ----

def scum(kind):
    """At the top of the Flood's upper water block (its surface a little under the block's top)."""
    y = 14.3
    if kind in ("a", "b", "c"):
        return [b("Film", (0, y, 0), (16, y + 0.05, 16), "scum-" + kind, faces=("up", "down"), uv=(0, 0, 16, 16))]
    els = [b("Film", (0, y, 0), (16, y + 0.05, 16), "scum-a", faces=("up", "down"), uv=(0, 0, 16, 16))]
    if kind == "board":
        els += [b("Board", (1.5, y - 1.0, 5.5), (14.5, y + 0.5, 9.0), "panel", rot=(0, 18, 0)),
                b("Nail", (12.2, y + 0.5, 6.8), (12.6, y + 0.9, 7.2), "metaldark", rot=(0, 18, 0), origin=(8, y, 7.25))]
    elif kind == "box":
        els += [b("Box", (4, y - 4.5, 4), (12, y + 1.6, 12), {"up": "soggy", "all": "soggy"}, rot=(0, 14, 0)),
                b("Flap", (4, y + 1.6, 4), (12, y + 2.0, 7.5), "soggy", rot=(-50, 0, 0), origin=(8, y + 1.6, 4))]
    elif kind == "chair":
        # a kitchen chair gone over in the water, its back legs and a rail of its back above the surface
        o = (8, y - 2, 8)
        r = (-62, 20, 0)
        els += [b("Seat", (3, y - 4, 3), (13, y - 2.5, 13), "panel", rot=r, origin=o),
                b("LegA", (3, y - 2.5, 3), (4.2, y + 6, 4.2), "panel", rot=r, origin=o),
                b("LegB", (11.8, y - 2.5, 3), (13, y + 6, 4.2), "panel", rot=r, origin=o),
                b("Stretcher", (4.2, y + 2.5, 3.3), (11.8, y + 3.2, 3.9), "panel", rot=r, origin=o)]
    elif kind == "laptop":
        # (on the bed under the water: the block under the surface's, its floor the bed's top)
        els = [b("Base", (3, 0, 4.5), (13, 0.8, 11.5), "castiron", rot=(0, 12, 0)),
               b("Keys", (3.8, 0.8, 5.2), (12.2, 0.85, 9.0), "bakelite", faces=("up",), rot=(0, 12, 0), origin=(8, 0.4, 8)),
               b("Lid", (3, 0.8, 10.7), (13, 7.6, 11.5), {"north": "tvscreen", "all": "castiron"}, rot=(-18, 12, 0), origin=(8, 0.8, 11.1)),
               b("Silt", (2, 0, 2), (14, 0.3, 14), "slime-bed", faces=("up",))]
        return els
    else:
        els += [b("Bottle", (6.5, y - 0.6, 6), (8.3, y + 0.9, 11), "bottle", rot=(0, 30, 0), origin=(7.4, y, 8.5)),
                b("Neck", (7.0, y - 0.3, 3.8), (7.8, y + 0.5, 6.0), "bottle", rot=(0, 30, 0), origin=(7.4, y, 8.5))]
    return els


# ======================================================================== Blocks

def lang(code, english):
    R3.LANG[code] = english


def blocks():
    oriented = R3.oriented
    # Rebuilt (their shapes rewritten over round 3's of the same names)
    for p in ("lower", "upper", "top"):
        shape(f"furnace-{p}", furnace(p))
        shape(f"heater-{p}", heater(p))
    l, r = bench()
    shape("bench-l", l)
    shape("bench-r", r)
    l, r = pooltable()
    shape("pooltable-l", l)
    shape("pooltable-r", r)
    shape("poollamp", poollamp())
    for k in ("boxes", "jars", "paint", "odds"):
        for p in ("lower", "upper"):
            shape(f"shelving-{k}-{p}", shelving(p, k))
    for k in ("pegboard-a", "pegboard-b"):
        shape(f"wallthing-{k}", pegboard(k))
    shape("wallthing-fusebox", fusebox())
    shape("debris-boards", debris("boards"))
    shape("debris-chunks", debris("chunks"))
    shape("wallthing-chute", chute())
    for k in ("xmas", "taxes", "moms", "keep"):
        for p in ("lower", "upper"):
            shape(f"boxes-{k}-{p}", boxes(p, k))
    for p in ("lower", "upper"):
        shape(f"winerack-{p}", winerack(p))
    for k in ("line", "shirt", "sheet", "towel"):
        shape(f"overhead-{k}", overhead(k))
    # New
    kinds = ["washer", "dryer", "tub"]
    oriented("basement-laundry", "Washing machine",
             {(k, p): shape(f"laundry-{k}-{p}", laundry(k, p)) for k in kinds for p in ("lower", "upper")},
             "The Basement: its own washer and dryer (porthole doors, consoles, hoses to a bib, the dryer's vent into the wall) "
             "and a laundry tub on legs; upper is the wall over them", material="Metal", sounds=METAL,
             box=(0.05, 0, 0.1, 0.95, 1, 0.95), drops=SCRAP, groups=[("kind", kinds), ("part", ["lower", "upper"])])
    data_path = os.path.join(BLOCKS, "basement-laundry.json")
    patch_upper_no_collide(data_path)
    l, r = sofa()
    oriented("basement-sofa", "Old sofa", {("l",): shape("sofa-l", l), ("r",): shape("sofa-r", r)},
             "The Basement: the rec room's old plaid sofa, two blocks long (l, r), a crocheted throw over it",
             sounds=CLOTH, box=(0, 0, 0.1, 1, 0.6, 1), drops=[{"type": "item", "code": "carpetfibre", "quantity": {"avg": 1, "var": 1}}],
             groups=[("half", ["l", "r"])])
    oriented("basement-tv", "Console television", {(p,): shape(f"tv-{p}", tv(p)) for p in ("lower", "upper")},
             "The Basement: a console television on legs, its tube's hump behind; upper, the rabbit ears on its lid",
             box=(0.05, 0, 0.18, 0.95, 1, 0.98), drops=SCRAP, groups=[("part", ["lower", "upper"])])
    patch_upper_no_collide(os.path.join(BLOCKS, "basement-tv.json"), sel=(0.3, 0, 0.35, 0.7, 0.9, 0.7))
    oriented("basement-cuerack", "Cue rack", {(): shape("cuerack", cuerack())},
             "The Basement: the rec room's cue rack on the wall, four cues in it", box=(0.1, 0, 0.75, 0.9, 1, 1), drops=STICKS)
    oriented("basement-shoplight", "Shop light", {(): shape("shoplight", shoplight())},
             "The Basement: a fluorescent shop light hung on chains over the workbench, lit", material="Glass", sounds=METAL,
             collide=False, box=(0.1, 0.25, 0.3, 1, 1, 0.7), light={"*": [32, 1, 11]},
             drops=[{"type": "item", "code": "glassshard", "quantity": {"avg": 1, "var": 0.5}}])
    oriented("basement-rail", "Stair handrail", {(h,): shape(f"rail-{h}", rail() if h == "l" else mirror_x(rail())) for h in ("l", "r")},
             "The Basement: the handrail down the steps into the Flood, its newel leaning (hand l: on the west of a stair that "
             "climbs north)", sounds=METAL, box=(0.03, 0, 0.4, 0.2, 1, 0.55), drops=SCRAP, groups=[("hand", ["l", "r"])])
    fix_mirrored_box(os.path.join(BLOCKS, "basement-rail.json"))
    oriented("basement-boiler", "Old boiler", {(p,): shape(f"boiler-{p}", boiler(p)) for p in ("lower", "upper")},
             "The Basement: a cast-iron sectional boiler, its gauge and relief valve; upper, its supply with a gate valve, its "
             "return and its flue going back into the wall", material="Metal", sounds=METAL, box=(0.06, 0, 0.1, 0.94, 1, 1),
             drops=SCRAP, groups=[("part", ["lower", "upper"])])
    patch_upper_no_collide(os.path.join(BLOCKS, "basement-boiler.json"), sel=(0.2, 0, 0.3, 0.8, 0.8, 1))
    # The sump, turned to its corner, and its pipe up the walls
    oriented("basement-sump", "Sump pit", {(): shape("sump", sump())},
             "The Basement: the sump pit in a room's corner, its pump in the black water under an iron grate (the walls to the "
             "north and west of the north variant)", material="Stone", sounds=METAL, box=(0, 0, 0, 1, 1, 1), drops=[])
    with open(os.path.join(BLOCKS, "basement-sump.json"), encoding="utf-8") as f:
        head = f.readline()
        data = json.loads(f.read())
    data["sidesolid"] = {"all": False, "up": True}
    data["resistance"] = 6
    data["requiredMiningTier"] = 2
    R3.write_json(os.path.join(BLOCKS, "basement-sump.json"), data, head[3:].strip())
    oriented("basement-sumppipe", "Sump pump pipe", {(p,): shape(f"sumppipe-{p}", sumppipe(p)) for p in ("low", "high")},
             "The Basement: the sump pump's discharge pipe up a room's corner and into the wall (part low, high; the walls to "
             "the north and west of the north variant)", sounds=METAL, collide=False, box=(0.1, 0, 0, 0.4, 1, 0.4), drops=[],
             groups=[("part", ["low", "high"])])
    oriented("basement-wallrail", "Stair handrail", {(): shape("wallrail", wallrail())},
             "The Basement: a handrail on the outer wall of an Escherian stairwell, over a step (the wall to the west of a step "
             "that climbs north)", sounds=METAL, collide=False, box=(0, 0.5, 0, 0.15, 1, 1), drops=SCRAP)
    oriented("basement-slabedge", "Broken slab", {(k,): shape(f"slabedge-{k}", slabedge(k)) for k in ("a", "b")},
             "The Basement: the ceiling's slab broken back round the crack someone fell through, its rebar bent down into the "
             "hole (the hole to the north)", material="Stone", sounds=STONE, box=(0, 0, 0, 1, 1, 1),
             drops=[], groups=[("shape", ["a", "b"])])
    scums = ["a", "b", "c", "board", "box", "bottle", "chair", "laptop"]
    oriented("basement-scum", "Scum on the water", {(k,): shape(f"scum-{k}", scum(k)) for k in scums},
             "The Basement: on the Flood's water, a film of scum and leaves, or a floating board, a sodden box, a bottle "
             "(swum through)", sounds=CLOTH, collide=False, box=(0.1, 0.8, 0.1, 0.9, 0.95, 0.9), drops=[], groups=[("what", scums)],
             extra={"renderpass": "OpaqueNoCull", "replaceable": 500})
    # The caged bulb (the same block, its shapes rebuilt)
    shape("lamp-lit", lamp(True))
    shape("lamp-off", lamp(False))
    # The stud wall, by part and the way it runs
    sp = ["low", "mid", "top"]
    shape_by = {}
    for k in sp:
        path = shape(f"studs-{k}", studs(k))
        for ax, r in (("we", 0), ("ns", 90)):
            shape_by[f"*-{k}-{ax}"] = {"base": path, "rotateY": r}
    old = os.path.join(SHAPES, "studs.json")
    if os.path.exists(old):
        os.remove(old)
    R3.write_json(os.path.join(BLOCKS, "basement-studs.json"), {
        "code": "basement-studs", "variantgroups": [{"code": "part", "states": sp}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-mid-we"], "construction": ["*-mid-we"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 99, "resistance": 3,
        "drops": STICKS + [{"type": "item", "code": "carpetfibre", "quantity": {"avg": 0.5, "var": 0.5}}], "sounds": WOOD,
    }, "The Basement: an unfinished wall, bare studs with kraft-faced batts stapled between them (part low with the bottom "
       "plate, mid, top with the top plate; axis the way the wall runs)")
    # The joists' ceiling, as a model
    jk = ["plain", "cable", "box", "bridge"]
    shape_by = {}
    for k in jk:
        path = shape(f"joists-{k}", joists(k))
        for ax, r in (("we", 0), ("ns", 90)):
            shape_by[f"*-{k}-{ax}-*"] = {"base": path, "rotateY": r}
    R3.write_json(os.path.join(BLOCKS, "basement-joists.json"), {
        "code": "basement-joists",
        "variantgroups": [{"code": "kind", "states": jk}, {"code": "axis", "states": ["we", "ns"]}, {"code": "light", "states": ["dark", "faint"]}],
        "creativeinventory": {"general": ["*-plain-we-dark"], "construction": ["*-plain-we-dark"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": shape_by,
        "sidesolid": {"all": False, "up": True}, "sideopaque": {"all": False, "up": True}, "lightAbsorption": 0, "resistance": 3,
        # (faint: Fandom's light that has no source, as the ceiling's faint variant)
        "lightHsvByType": {"*-faint": [8, 2, 5]},
        "drops": STICKS, "sounds": WOOD,
    }, "The Basement: bare joists under the floor above, as a model (kind plain, cable, box, bridge; axis the joists run; "
       "light faint gives off the light nobody can find the source of)")
    # The hall's duct, with the mains beside it (a code of its own: Level 31 reuses round 2's basement-duct)
    fits = ["plain", "valve", "gauge"]
    shape_by = {}
    for f in fits:
        path = shape(f"ductrun-{f}", duct(f))
        for ax, r in (("we", 0), ("ns", 90)):
            shape_by[f"*-{f}-{ax}"] = {"base": path, "rotateY": r}
    R3.write_json(os.path.join(BLOCKS, "basement-ductrun.json"), {
        "code": "basement-ductrun",
        "variantgroups": [{"code": "fit", "states": fits}, {"code": "axis", "states": ["we", "ns"]}],
        "creativeinventory": {"general": ["*-plain-we"], "decorative": ["*-plain-we"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": shape_by,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2,
        "collisionSelectionBoxesByType": {"*-we": [{"x1": 0, "y1": 0.42, "z1": 0.06, "x2": 1, "y2": 1, "z2": 0.97}],
                                          "*-ns": [{"x1": 0.03, "y1": 0.42, "z1": 0, "x2": 0.97, "y2": 1, "z2": 1}]},
        "drops": SCRAP, "sounds": METAL,
    }, "The Basement: a heating duct under the joists with a water main and a gas line beside it (fit: plain, a gate "
       "valve, a gauge; axis we or ns)")


def patch_upper_no_collide(path, sel=(0.1, 0, 0.7, 0.9, 0.6, 1)):
    """An `upper` part is what hangs on the wall over a thing: no collision, a thin selection at the wall."""
    with open(path, encoding="utf-8") as f:
        head = f.readline()
        data = json.loads(f.read())
    boxes = data.pop("collisionSelectionBoxesByType")
    data["collisionboxByType"] = {"*-upper-*": None}
    data["collisionSelectionBoxesByType"] = {}
    for k, v in boxes.items():
        side = k.split("-")[-1]
        data["collisionSelectionBoxesByType"]["*-lower-" + side] = v
    data["selectionBoxByType"] = {f"*-upper-{s}": dict(zip(("x1", "y1", "z1", "x2", "y2", "z2"), sel),
                                                       **({"rotateY": r} if r else {})) for s, r in ROT.items()}
    R3.write_json(path, data, head[3:].strip())


def fix_mirrored_box(path):
    """The r-hand rail's box is on the east side."""
    with open(path, encoding="utf-8") as f:
        head = f.readline()
        data = json.loads(f.read())
    boxes = data.pop("collisionSelectionBoxesByType")
    out = {}
    for k, v in boxes.items():
        side = k.split("-")[-1]
        for h in ("l", "r"):
            bx = [dict(e) for e in v]
            if h == "r":
                for e in bx:
                    e["x1"], e["x2"] = round(1 - e["x2"], 4), round(1 - e["x1"], 4)
            out[f"*-{h}-{side}"] = bx
    data["collisionSelectionBoxesByType"] = out
    R3.write_json(path, data, head[3:].strip())
