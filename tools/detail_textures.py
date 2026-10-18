"""Textures for the detail props, signs, doors and floors added to Levels 1, 3, 4 and 5 (32x32, in block/detail/).

Pictures meant to fill a face (signs, screens, paintings) are drawn edge to edge; materials are noise with a few
features so they keep their scale on boxes of any size.
"""
import math
import random

import matlib as M
import texlib

from PIL import Image, ImageDraw

from detail_kit import T, seed_of

S = 32


def rgb(h, a=255):
    return T.hexrgb(h) + (a,)


def noise(color, n=5, key="x"):
    return T.noise_fill(T.hexrgb(color), n, seed_of(key))


def save(img, name):
    T.save(img, f"block/detail/{name}.png")


def flat(name, color, n=5):
    save(noise(color, n, name), name)


def text(img, s, box, color, size):
    T.text_img(img, s, box, rgb(color) if isinstance(color, int) else color, size)


def stripes(img, c1, c2, width=4, box=None, diagonal=True):
    x0, y0, x1, y1 = box or (0, 0, S, S)
    px = img.load()
    for y in range(y0, y1):
        for x in range(x0, x1):
            k = ((x + y) if diagonal else x) // width
            px[x, y] = c1 if k % 2 == 0 else c2


def block_wall(base, mortar, key, rows=4):
    """Painted concrete block: courses of 16x8 px blocks, staggered."""
    img = noise(base, 3, key)
    d = ImageDraw.Draw(img)
    h = S // rows
    for r in range(rows):
        y = r * h
        d.line([0, y, S - 1, y], fill=rgb(mortar))
        off = 8 if r % 2 else 0
        for x in range(off, S + 16, 16):
            d.line([x % S, y, x % S, y + h - 1], fill=rgb(mortar))
    return img


# Bold capitals for the EXIT signs, 10 px high with 2 px strokes ("1" is ink)
EXIT_GLYPHS = {
    "E": ["111111", "111111", "110000", "110000", "111110", "111110", "110000", "110000", "111111", "111111"],
    "X": ["11000011", "11000011", "01100110", "00111100", "00011000", "00011000", "00111100", "01100110", "11000011", "11000011"],
    "I": ["11"] * 10,
    "T": ["11111111", "11111111"] + ["00011000"] * 8,
}
# 7 px capitals for small plates
PLATE_GLYPHS = {
    "S": ["0111", "1000", "1000", "0110", "0001", "0001", "1110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "A": ["0110", "1001", "1001", "1111", "1001", "1001", "1001"],
    "F": ["1111", "1000", "1000", "1110", "1000", "1000", "1000"],
    "O": ["0110", "1001", "1001", "1001", "1001", "1001", "0110"],
    "N": ["1001", "1101", "1101", "1011", "1011", "1001", "1001"],
    "L": ["1000", "1000", "1000", "1000", "1000", "1000", "1111"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
}


def glyphs(img, rows_list, x, y, color, gap=1):
    """Draws bitmap glyphs (lists of rows of "0"/"1") left to right from (x, y); returns the x after the last."""
    px = img.load()
    for rows in rows_list:
        for j, row in enumerate(rows):
            for i, c in enumerate(row):
                if c == "1":
                    px[x + i, y + j] = color
        x += len(rows[0]) + gap
    return x


def glyph_width(word, font, gap=1):
    return sum(len(font[c][0]) for c in word) + gap * (len(word) - 1)


def grime(img, key, strength=0.25, color=(90, 86, 70)):
    rng = random.Random(seed_of(key))
    T.blotch(img, (rng.randrange(S), S - 4), rng.randint(6, 10), color, strength, seed_of(key) + 1)
    return img


# ---------------- Shared ----------------

def shared():
    flat("steel", 0xB4B8BC, 4)
    flat("steeldark", 0x5C6064, 4)
    flat("blackmetal", 0x1C1E21, 3)
    flat("copper", 0xB8733A, 8)
    flat("wood", 0x8A6440, 6)
    flat("wooddark", 0x4A3220, 5)
    flat("paper", 0xF2EEE2, 2)
    flat("string", 0xC8B48C, 4)
    # The EXIT sign's housing: white enamelled steel (graphics pass B4: a slight orange peel and a few worn spots)
    save(M.painted_metal(seed_of("exithousing"), base=(226, 224, 216), grain=2, mottle=3, panel=False, chips=2,
                         under=(176, 174, 168)), "exithousing")
    flat("redmetal", 0xB42820, 6)
    flat("orange", 0xE8661C, 5)
    flat("white", 0xEEEEEA, 2)
    flat("rubber", 0x222224, 3)

    # The lit face of an EXIT sign: bold red capitals on white, drawn pixel by pixel so they stay crisp (the font,
    # scaled down, left the letters pink at the edges). Only rows 8-23 show (the faces' UV band); the letters fill
    # rows 11-20 and are centred on the middle of the texture, where the two halves of a sign over a two-wide
    # doorway meet
    # (B4) The face is a diffuser lit from behind: brightest in the middle, a little dimmer toward its frame, and the
    # red light bleeding a pink halo a pixel or two round each letter; a thin bezel round the band that shows
    img = Image.new("RGBA", (S, S), rgb(0xF4F2EC))
    glyphs(img, [EXIT_GLYPHS[c] for c in "EXIT"], 1, 11, rgb(0xD8141E), gap=2)
    px = img.load()
    red = [(x, y) for y in range(S) for x in range(S) if px[x, y][:3] == (0xD8, 0x14, 0x1E)]
    near = {}
    for (rx, ry) in red:
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                q = (rx + dx, ry + dy)
                if 0 <= q[0] < S and 0 <= q[1] < S:
                    near[q] = min(near.get(q, 9), max(abs(dx), abs(dy)))
    for y in range(S):
        for x in range(S):
            if px[x, y][:3] == (0xD8, 0x14, 0x1E):
                continue
            c = (244, 242, 236)
            edge = min(x, S - 1 - x, abs(y - 8), abs(y - 23)) if 8 <= y <= 23 else 0
            c = M.lift(c, -min(10, max(0, 5 - edge) * 2.2))
            k = near.get((x, y))
            if k == 1:
                c = M.mix(c, (232, 120, 118), 0.32)
            elif k == 2:
                c = M.mix(c, (236, 168, 164), 0.16)
            px[x, y] = M.rgba(c)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xB8B6AE), width=1)
    d.line([0, 8, S - 1, 8], fill=rgb(0xC4C2BA))
    d.line([0, 23, S - 1, 23], fill=rgb(0xCECCC4))
    save(img, "exitface")

    img = Image.new("RGBA", (S, S))
    stripes(img, rgb(0xE8B81C), rgb(0x1C1C1C), 4)
    save(img, "hazard")


# ---------------- Level 1 ----------------

def level1():
    wall = grime(block_wall(0xE4E2DA, 0xC2C0B8, "whiteblock"), "whiteblock", 0.18)
    save(wall, "whiteblock")
    base = wall.copy()
    d = ImageDraw.Draw(base)
    base.paste(grime(block_wall(0x55595C, 0x45494C, "whiteblockbase"), "wbb", 0.2).crop((0, 16, S, S)), (0, 16))
    d.rectangle([0, 14, S - 1, 15], fill=rgb(0xE0B624))
    save(base, "whiteblock-base")
    lintel = wall.copy()
    ImageDraw.Draw(lintel).rectangle([0, 28, S - 1, S - 1], fill=rgb(0x2A2C2E))
    save(lintel, "whiteblock-lintel")
    # The halls' floor: grey floor paint over concrete, the concrete's pores and patches showing faintly through.
    # (B4) Three versions, all turned at random (gen_detail ALTS); the heel scuffs are in the third only, at random
    # places, so they no longer stand at the same spot in every block
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        sd = seed_of("l1hallfloor") * 10 + alt
        img = M.concrete(sd, base=(114, 117, 114), grain=2, mottle=4, aggregate=0.0, pores=0.004, patches=3.5,
                         patch_hue=1.0, hue=1.0)
        # (D1) the versions are turned and mixed at random: their broad mottle blends into one shared field toward the
        # edges (matlib.turn_safe), and the scuffs fade out before the edge, so the blocks meet without a seam. The paint
        # has almost no grain to hide a calm border round a mottled middle, so only a quarter of each version's own
        # mottle is kept
        M.turn_safe(img, M.concrete(sd - alt, base=(114, 117, 114), grain=2, mottle=4, aggregate=0.0, pores=0.0,
                                    patches=3.5, patch_hue=1.0, hue=1.0), band=12, keep=0.25)
        plain = img.copy()
        if alt == 2:
            rng = random.Random(sd)
            for _ in range(3):
                x, y, L = rng.uniform(0, S), rng.uniform(0, S), rng.randint(3, 7)
                a = rng.uniform(-0.5, 0.5) + rng.choice((0, 1.57))
                for i in range(L):
                    t = math.sin(math.pi * (i + 0.5) / L)
                    M.touch(img, round(x + math.cos(a) * i), round(y + math.sin(a) * i), -0.09 * t)
        img = T.inside_block(plain, img)
        save(T.match_mean(img, 113), "l1hallfloor" + v)

    # (Level 1 props) The locked steel door's leaf, and every texture of the rebuilt props: tools/l1props_tex.py
    import l1props_tex
    l1props_tex.generate()
    img = noise(0x1E2022, 3, "firedoor")
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, S - 2, S - 2], outline=rgb(0x34373A))
    d.rectangle([4, 20, 27, 29], outline=rgb(0x2A2D30))
    save(img, "firedoor")

    # (B4) The hazard band painted on the column's own concrete: the paint takes the concrete's light and dark, and
    # is scuffed off here and there along its foot
    img = T.match_mean(T.pillar_concrete(), 154)
    band = Image.new("RGBA", (S, S))
    stripes(band, rgb(0xD8AC24), rgb(0x24221E), 4, (0, 20, S, S))
    px, bp = img.load(), band.load()
    rng = random.Random(seed_of("pillarbase"))
    for y in range(20, S):
        for x in range(S):
            if y >= S - 2 and rng.random() < 0.25:
                continue
            px[x, y] = M.rgba(M.lift(bp[x, y][:3], (M.lum(px[x, y]) - 154) * 0.5 + rng.uniform(-3, 3)))
    for x in range(S):
        M.touch(img, x, 20, 0.05)
    save(img, "pillarbase")

    floor = T.concrete_floor("plain")
    img = floor.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([14, 12, 17, 28], fill=rgb(0xE8E8E0))  # arrow pointing north
    d.polygon([(9, 13), (22, 13), (15.5, 3)], fill=rgb(0xE8E8E0))
    save(img, "parkarrow")
    img = floor.copy()
    T.blotch(img, (16, 18), 9, (24, 24, 22), 0.75, 61)
    T.blotch(img, (10, 10), 4, (30, 28, 26), 0.6, 62)
    save(img, "parkoil")
    img = floor.copy()
    # (B4) A cast grate set into a recessed frame: the frame's inner edge in shadow at the top, the bars lit on their
    # left and dark on their right, black water below them
    d = ImageDraw.Draw(img)
    d.rectangle([8, 8, 23, 23], fill=rgb(0x1E2020))
    px = img.load()
    for x in range(9, 23, 3):
        for y in range(9, 23):
            px[x, y] = M.rgba(M.lift((88, 90, 86), 6 - (y - 9) * 0.5))
            px[x + 1, y] = M.rgba(M.lift((70, 72, 70), -(y - 9) * 0.5))
    for k in range(8, 24):
        px[k, 8] = M.rgba((52, 54, 52))
        px[8, k] = M.rgba((58, 60, 58))
        px[k, 23] = M.rgba((112, 114, 110))
        px[23, k] = M.rgba((104, 106, 102))
    M.inset(img, (7, 7, 25, 25), 1, 0.18)
    save(img, "parkdrain")
    img = Image.new("RGBA", (S, S))
    stripes(img, rgb(0xE8C020), rgb(0x202020), 8, diagonal=False)
    save(img, "speedbump")

    flat("conewhite", 0xF0F0EA, 2)
    img = Image.new("RGBA", (S, S), rgb(0xF2C81C))
    d = ImageDraw.Draw(img)
    text(img, "CAUTION", (1, 2, 31, 10), 0x111111, 6)
    d.polygon([(16, 12), (26, 28), (6, 28)], outline=rgb(0x111111))
    d.ellipse([14, 16, 17, 19], fill=rgb(0x111111))  # slipping figure
    d.line([15, 19, 13, 24, 18, 26], fill=rgb(0x111111))
    save(img, "wetfloor")
    flat("paybody", 0x8E9296, 4)
    img = noise(0xC8A020, 4, "payface")
    d = ImageDraw.Draw(img)
    d.rectangle([5, 3, 26, 12], fill=rgb(0x1C3020))
    text(img, "PAY HERE", (5, 4, 27, 11), 0x7CE090, 4)
    d.rectangle([7, 16, 15, 18], fill=rgb(0x111111))  # ticket slot
    for r in range(3):
        for c in range(3):
            d.rectangle([18 + c * 3, 15 + r * 3, 19 + c * 3, 16 + r * 3], fill=rgb(0xDDDDDD))
    d.rectangle([8, 24, 23, 27], fill=rgb(0x222222))  # coin return
    save(img, "payface")
    img = noise(0x4A4E52, 4, "trashgrey")
    d = ImageDraw.Draw(img)
    for x in range(2, S, 6):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A3E42))
    save(img, "trashgrey")
    img = noise(0xB89C6C, 6, "palletwood")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x8A7048))
    save(img, "palletwood")
    img = noise(0xA87A48, 5, "benchtop")
    for y in range(0, S, 4):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x8E643A))
    save(img, "benchtop")
    img = noise(0x9A7A54, 4, "pegboard")
    d = ImageDraw.Draw(img)
    for y in range(2, S, 4):
        for x in range(2, S, 4):
            d.point((x, y), fill=rgb(0x4A3A28))
    d.rectangle([4, 6, 6, 18], fill=rgb(0x6A3A20))  # hammer handle
    d.rectangle([2, 4, 9, 7], fill=rgb(0x55585C))
    d.rectangle([14, 5, 15, 20], fill=rgb(0xC03020))  # screwdriver
    d.rectangle([20, 4, 27, 6], fill=rgb(0x8A8E92))  # wrench
    d.rectangle([22, 6, 24, 22], fill=rgb(0x8A8E92))
    d.ellipse([17, 22, 29, 30], outline=rgb(0x2A5A2A), width=2)  # coiled cord
    save(img, "pegboard")
    img = noise(0xB0261C, 5, "toolboxred")
    d = ImageDraw.Draw(img)
    d.line([0, 11, S - 1, 11], fill=rgb(0x701812))
    d.rectangle([5, 9, 8, 13], fill=rgb(0xC0C4C8))
    d.rectangle([23, 9, 26, 13], fill=rgb(0xC0C4C8))
    save(img, "toolboxred")
    img = noise(0xC8A472, 6, "plywood")
    rng = random.Random(seed_of("plywood"))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        y = rng.randrange(S)
        d.arc([rng.randint(-20, 10), y - 6, rng.randint(20, 50), y + 6], 0, 180, fill=rgb(0xA8844E))
    save(img, "plywood")
    # (B4) Woven poly tarp: a fine plain weave, a reinforcing line every 8 px, soft folds across it, a grommet;
    # the colours a little duller (sun-faded), the old ones' brightness kept
    for name, c, mean in (("tarp", (52, 94, 160), 88), ("tarporange", (198, 104, 44), 118)):
        img = M.fabric(seed_of(name), base=c, weave="plain", contrast=7, grain=2, mottle=5, thread=2)
        fold = M.fbm((S, S), seed_of(name + "fold"), (16, 8), 0.4)
        px = img.load()
        for y in range(S):
            for x in range(S):
                px[x, y] = M.rgba(M.lift(px[x, y], fold[y][x] * 9))
        for x in range(0, S, 8):
            for y in range(S):
                M.touch(img, x, y, -0.08)
                M.touch(img, x + 1, y, 0.04)
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, 4, 4], outline=rgb(0xB8B8B0))  # grommet
        save(T.match_mean(img, mean), name)
    # (B4) The bedroll: olive cotton canvas (a 2x2 basket weave) rolled up, so a soft shadow every 8 px where one turn
    # meets the next; the pillow a plain-woven ticking
    img = M.fabric(seed_of("bedroll"), base=(64, 92, 48), weave="basket", contrast=6, grain=2, mottle=5, thread=2)
    for y0 in range(0, S, 8):
        for x in range(S):
            for k, f in ((0, -0.16), (1, 0.06), (2, 0.04), (6, -0.03), (7, -0.08)):
                M.touch(img, x, y0 + k, f)
    save(T.match_mean(img, 74), "bedroll")
    img = M.fabric(seed_of("bedrollpillow"), base=(142, 130, 112), weave="plain", contrast=6, grain=2, mottle=6)
    save(T.match_mean(img, 128), "bedrollpillow")
    # The two-block camp tent's fly: green ripstop nylon (a faint grid), a darker seam every half block, a grommet
    # (B4) A ripstop weave from matlib.fabric, the cloth a touch uneven where it hangs (soft broad light and dark),
    # a flat-felled seam every half block (a dark fold with its two rows of stitching lit), and a grommet
    img = M.fabric(seed_of("tentfly"), base=(72, 100, 60), weave="ripstop", contrast=6, grain=2, mottle=6, thread=2)
    sag = M.fbm((S, S), seed_of("tentflysag"), (16, 8), 0.45)
    px = img.load()
    for y in range(S):
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y], sag[y][x] * 12))
    for x0 in (0, 16):
        for y in range(S):
            M.touch(img, x0, y, -0.32)
            M.touch(img, x0 + 1, y, 0.14)
            M.touch(img, x0 - 1, y, -0.06)
            if y % 2 == 0:
                M.touch(img, x0 + 2, y, 0.07)
                M.touch(img, x0 - 2, y, 0.05)
    d = ImageDraw.Draw(img)
    d.ellipse([27, 27, 30, 30], outline=rgb(0xB0B0A6))
    save(T.match_mean(img, 86), "tentfly")
    img = M.fabric(seed_of("tentinside"), base=(34, 46, 30), weave="ripstop", contrast=4, grain=2, mottle=4, thread=1)
    save(T.match_mean(img, 38), "tentinside")
    # The two-block sleeping bag: faded red quilted nylon, its channels sewn across every three pixels' worth, and the
    # brushed flannel lining of the turned-back top (a blue tartan)
    # (B4) Quilted nylon: channels 8 px apart (the old 6 px did not tile), each puffed, lit along its upper half and
    # shaded into the stitched seam below; a fine ripstop under it, a faint sheen in broad patches
    img = M.fabric(seed_of("sleepingbag"), base=(150, 60, 50), weave="ripstop", contrast=3, grain=2, mottle=5, thread=1)
    sheen = M.fbm((S, S), seed_of("sleepingbagsheen"), (16, 8), 0.4)
    px = img.load()
    for y in range(S):
        t = (y % 8 + 0.5) / 8
        puff = math.sin(math.pi * t)
        for x in range(S):
            d = 14 * puff - 7 + 4 * (0.5 - t) + max(0, sheen[y][x]) * 10
            px[x, y] = M.rgba(M.lift(px[x, y], d))
    for y0 in range(0, S, 8):
        for x in range(S):
            M.touch(img, x, y0, -0.16 if x % 3 else -0.1)
    save(T.match_mean(img, 82), "sleepingbag")
    # The lining: a brushed flannel tartan (twill, blue ground, dark bands every 8 px, a thin ochre line)
    img = M.fabric(seed_of("sleepingbaglining"), base=(74, 102, 124), weave="twill", contrast=6, grain=2, mottle=4)
    px = img.load()
    for y in range(S):
        for x in range(S):
            k = 0.0
            if x % 8 < 3:
                k += 0.5
            if y % 8 < 3:
                k += 0.5
            c = M.mix(px[x, y], M.lift(px[x, y], -34), k)
            if x % 8 == 5 or y % 8 == 5:
                c = M.mix(c, (148, 132, 88), 0.55)
            px[x, y] = M.rgba(c)
    save(img, "sleepingbaglining")
    flat("sleepingbagzip", 0x2A2624, 3)
    img = noise(0xFFC060, 4, "lanternglass")
    ImageDraw.Draw(img).rectangle([12, 0, 19, S - 1], fill=rgb(0xFFF0C0))
    save(img, "lanternglass")
    # Burn barrel: a near-black steel drum, sooted at the top, thin rust runs down from the rim and rust eating
    # in from the foot; a darker band for the rim and hoops, and the burnt-out inside
    # (B4) The drum's old black paint (matlib.painted_metal) gone to rust in patches, heaviest at the foot where it
    # stood in the wet, rust runs down from the rim, and soot over the top where the fire licks out
    rng = random.Random(seed_of("burnbarrel"))
    img = M.painted_metal(seed_of("burnbarrel"), base=(44, 40, 38), grain=3, mottle=6, panel=False, chips=6,
                          under=(92, 70, 52))
    M.rust(img, 0.32, seed_of("burnbarrelrust"), color=(112, 60, 32), dark=(58, 34, 22))
    foot = M.fbm((S, S), seed_of("burnbarrelfoot"), (8, 4), 0.5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = max(0.0, (y - 20) / 11) * (0.6 + 0.4 * foot[y][x])
            if t > 0:
                px[x, y] = M.rgba(M.mix(px[x, y], (98, 54, 30), min(0.8, t)))
            if y < 7:  # soot
                px[x, y] = M.rgba(M.lift(px[x, y], -(7 - y) * 2.6))
    M.drips(img, 6, seed_of("burnbarrelruns"), color=(104, 58, 32), length=(6, 18), strength=0.5, start=2)
    save(img, "burnbarrel")
    # The rolled rim and hoops: the same steel worn to bare metal along the roll (a lit line) with more rust
    img = M.painted_metal(seed_of("burnbarrelrim"), base=(52, 46, 42), grain=3, mottle=5, panel=False, chips=8,
                          under=(104, 96, 88))
    M.rust(img, 0.4, seed_of("burnbarrelrimrust"), color=(118, 64, 34), dark=(62, 36, 22))
    for x in range(S):
        for y in range(0, S, 8):
            M.touch(img, x, y, 0.16)
            M.touch(img, x, y + 1, 0.06)
    save(img, "burnbarrelrim")
    flat("burnbarrelinside", 0x100D0B, 3)
    img = noise(0xC8401C, 30, "embers")
    rng = random.Random(9)
    for _ in range(30):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(0xFFD060))
    save(img, "embers")
    flat("hospitalsheet", 0xDCE6EC, 3)
    flat("hospitalframe", 0xE8E8E2, 3)
    # A quilt folded in four at the foot of a hospital bed: its edges show the layers
    flat("hospitalquilt", 0xB8C8D8, 3)
    img = noise(0xB8C8D8, 3, "hospitalquiltfold")
    d = ImageDraw.Draw(img)
    for y in range(7, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x8496A8))
        d.line([0, y - 1, S - 1, y - 1], fill=rgb(0xA4B4C4))
    save(img, "hospitalquiltfold")
    flat("tabletop", 0xD2C6A8, 3)
    flat("foldsteel", 0x6E7276, 4)
    flat("medcab", 0xECECE6, 2)
    img = noise(0xECECE6, 2, "medcabfront")
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, S - 1], fill=rgb(0xB0B0AA))
    d.rectangle([9, 8, 13, 20], fill=rgb(0xC8201C))
    d.rectangle([5, 12, 17, 16], fill=rgb(0xC8201C))
    d.rectangle([19, 12, 20, 18], fill=rgb(0x8A8A86))
    save(img, "medcabfront")

    img = noise(0x8C9094, 3, "powerbox")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x5A5E62), width=2)
    d.polygon([(16, 6), (24, 20), (8, 20)], fill=rgb(0xE8C020), outline=rgb(0x111111))
    d.line([16, 10, 14, 15, 18, 14, 16, 19], fill=rgb(0x111111))
    d.rectangle([22, 24, 26, 27], fill=rgb(0x3A3E42))
    save(img, "powerbox")
    img = noise(0x7E8286, 3, "breaker")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x4E5256), width=2)
    for r in range(6):
        for c in (6, 18):
            d.rectangle([c, 4 + r * 4, c + 7, 6 + r * 4], fill=rgb(0x222426))
            d.rectangle([c + (2 if (r + c) % 3 else 4), 4 + r * 4, c + (3 if (r + c) % 3 else 5), 6 + r * 4], fill=rgb(0xD8D8D0))
    save(img, "breaker")
    img = noise(0xE4DCC4, 2, "outlet")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xB8B09A))
    for y in (6, 19):
        d.rectangle([10, y, 11, y + 4], fill=rgb(0x2A2A2A))
        d.rectangle([20, y, 21, y + 4], fill=rgb(0x2A2A2A))
        d.ellipse([14, y + 5, 17, y + 7], fill=rgb(0x2A2A2A))
    save(img, "outlet")

    # Crude drawings: paper hung on a string, and one old canvas whose eyes seem to follow you
    img = noise(0xEDE6D2, 3, "painting0")
    d = ImageDraw.Draw(img)
    for i, x in enumerate((7, 16, 25)):
        d.ellipse([x - 3, 6, x + 3, 12], outline=rgb(0xA01818))
        d.line([x, 12, x, 21, x - 3, 28], fill=rgb(0xA01818))
        d.line([x, 21, x + 3, 28], fill=rgb(0xA01818))
        d.line([x - 4, 15, x + 4, 15], fill=rgb(0xA01818))
    d.line([2, 29, 30, 29], fill=rgb(0x303030))
    save(img, "painting0")
    img = noise(0xE8E2CE, 3, "painting1")
    d = ImageDraw.Draw(img)
    for x in (9, 23):
        d.ellipse([x - 6, 10, x + 6, 20], fill=rgb(0xF8F8F0), outline=rgb(0x202020))
        d.ellipse([x - 2, 13, x + 2, 17], fill=rgb(0x101010))
    text(img, "SEE", (4, 23, 28, 31), 0x202020, 6)
    save(img, "painting1")
    img = noise(0x2E241C, 5, "painting2")
    d = ImageDraw.Draw(img)
    d.ellipse([10, 6, 22, 20], fill=rgb(0x9C8468))
    d.ellipse([12, 11, 14, 13], fill=rgb(0xF0F0F0))
    d.ellipse([18, 11, 20, 13], fill=rgb(0xF0F0F0))
    d.point((13, 12), fill=rgb(0x000000))
    d.point((19, 12), fill=rgb(0x000000))
    d.rectangle([8, 20, 24, 31], fill=rgb(0x1E2A22))
    save(img, "painting2")
    img = noise(0xEAE4D0, 3, "painting3")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 18, S - 1, S - 1], fill=rgb(0x6A8E3A))
    d.rectangle([13, 8, 19, 20], fill=rgb(0x5A3A1E), outline=rgb(0x2A1A0E))  # a door standing in a field
    d.ellipse([3, 3, 9, 9], fill=rgb(0xE8C030))
    save(img, "painting3")
    img = noise(0xC22A20, 5, "extsign")
    d = ImageDraw.Draw(img)
    d.rectangle([12, 8, 19, 28], fill=rgb(0xF0F0F0))
    d.rectangle([13, 4, 18, 8], fill=rgb(0xF0F0F0))
    save(img, "extsign")
    flat("extinguisher", 0xC21C18, 6)
    img = noise(0xC21C18, 4, "firealarm")
    d = ImageDraw.Draw(img)
    text(img, "FIRE", (2, 2, 30, 11), 0xF4F4F0, 7)
    d.rectangle([9, 14, 22, 20], fill=rgb(0xF4F4F0))
    d.rectangle([12, 20, 19, 26], fill=rgb(0xE0E0DA))
    save(img, "firealarm")
    for i, (c, logo) in enumerate(((0xE86A10, "eagle"), (0x9ACD32, "circle"), (0x7A3AB0, "tri"), (0x2A8AD8, "star"))):
        img = noise(c, 6, f"banner{i}")
        d = ImageDraw.Draw(img)
        ink = rgb(0xF4F0E0)
        if logo == "eagle":
            d.polygon([(4, 14), (16, 10), (28, 14), (16, 18)], fill=ink)
            d.polygon([(13, 8), (19, 8), (16, 22)], fill=ink)
        elif logo == "circle":
            d.ellipse([7, 6, 25, 24], outline=ink, width=3)
            d.line([16, 4, 16, 26], fill=ink, width=2)
        elif logo == "tri":
            d.polygon([(16, 4), (28, 24), (4, 24)], outline=ink, width=2)
        else:
            pts = [(16 + 11 * math.sin(a * math.pi / 5) * (1 if a % 2 == 0 else 0.45),
                    15 - 11 * math.cos(a * math.pi / 5) * (1 if a % 2 == 0 else 0.45)) for a in range(10)]
            d.polygon(pts, fill=ink)
        d.line([0, 29, S - 1, 29], fill=T.shade(T.hexrgb(c), 0.7), width=2)
        save(img, f"banner{i}")
    img = noise(0xB82018, 4, "hosecab")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0x401410), outline=rgb(0x8A1810))
    d.ellipse([7, 7, 24, 24], outline=rgb(0xD84030), width=3)
    d.ellipse([13, 13, 18, 18], fill=rgb(0x9A9A9A))
    d.line([4, 4, 12, 12], fill=rgb(0xC8D8E0))  # glass glint
    save(img, "hosecab")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xE8C020))
    text(img, "P2", (4, 7, 28, 25), 0x1C1C1C, 15)
    save(img, "levelsign")
    # Level 1's stairwells from layout version 4 are each on a floor, painted the same way: yellow for the parking
    # floors, orange for the basements below them
    for label in ("P5", "P4", "P3", "P2", "P1", "B1", "B2", "B3"):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse([2, 2, 29, 29], fill=rgb(0xE8C020 if label[0] == "P" else 0xE07020))
        text(img, label, (4, 7, 28, 25), 0x1C1C1C, 15)
        save(img, f"levelsign-{label.lower()}")
    img = noise(0x1E7A3A, 3, "stairsign")
    d = ImageDraw.Draw(img)
    text(img, "STAIRS", (1, 2, 31, 11), 0xF4F4F0, 7)
    d.line([5, 27, 11, 27, 11, 22, 17, 22, 17, 17, 23, 17, 23, 13], fill=rgb(0xF4F4F0), width=2)
    save(img, "stairsign")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 27, 29], fill=rgb(0xF4F0DC))
    for y in range(9, 27, 3):
        d.line([7, y, 7 + random.Random(y).randint(10, 18), y], fill=rgb(0x303060))
    d.rectangle([12, 2, 19, 5], fill=rgb(0xD8D0A0, 230))
    save(img, "note")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([26, 12, 6, 12], fill=rgb(0xC81818), width=3)
    d.polygon([(4, 12), (11, 6), (11, 18)], fill=rgb(0xC81818))
    for k in range(5):
        d.line([7 + k * 3, 21, 7 + k * 3, 29], fill=rgb(0x202020), width=1)
    d.line([5, 27, 21, 22], fill=rgb(0x202020))
    save(img, "graffiti")


# ---------------- Level 3 ----------------

def grate():
    """(B6) Level 3's steel bar grating, on the old 4 px pitch: bearing bars running north-south, each lit along its
    top with a dark flank, and lower cross rods between them, darker and broken by the bars; the dark well beneath
    with a faint gleam; the bar tops worn bright in patches and a few specks of rust. Mean kept (55)."""
    seed = seed_of("grate")
    well = M.noise_hv((24, 23, 22), 2, seed, S, 3)
    px = well.load()
    worn = M.fbm((S, S), M.sub(seed, "worn"), (8, 4), 0.6)
    steel = (88, 92, 96)
    rng = random.Random(seed)
    for y in range(S):
        for x in range(S):
            if y % 4 == 0 and x % 4 not in (0, 1):  # a cross rod, below the bars' tops
                c = M.lift(steel, 2 + rng.uniform(-3, 3))
                if x % 4 == 2:
                    c = M.lift(c, 6)
                px[x, y] = M.rgba(c)
            elif y % 4 == 1 and x % 4 not in (0, 1):  # its shadow on the well
                px[x, y] = M.rgba(M.lift(px[x, y], -6))
            if x % 4 == 0:  # bearing bar top
                c = M.lift(steel, 8 + worn[y][x] * 10 + rng.uniform(-3, 3))
                if rng.random() < 0.04:
                    c = M.mix(c, (110, 66, 40), 0.5)
                px[x, y] = M.rgba(c)
            elif x % 4 == 1:  # its flank, in shade
                c = M.lift(steel, -10 + rng.uniform(-3, 3))
                if rng.random() < 0.06:
                    c = M.mix(c, (84, 50, 32), 0.5)
                px[x, y] = M.rgba(c)
    return T.match_mean(well, 55)


def hazard_floor():
    """(B6) Concrete with yellow and black hazard stripes at the edges, round machinery: the stripes are paint that
    takes the concrete's light and dark, clean at the block edges so they run on from block to block, over the dusty
    floor's concrete. Mean kept (114)."""
    img = T.dusty_floor(0)
    px = img.load()
    m = sum(M.lum(px[x, y]) for y in range(S) for x in range(S)) / (S * S)
    rng = random.Random(seed_of("hazard"))
    for y in list(range(0, 6)) + list(range(S - 6, S)):
        for x in range(S):
            colour = (212, 166, 34) if ((x + y) // 4) % 2 == 0 else (34, 32, 30)
            d = (M.lum(px[x, y]) - m) * 0.4 + rng.uniform(-2, 2)
            if y in (5, S - 6):
                d -= 4  # the paint's edge, a hair darker
            px[x, y] = M.rgba(M.lift(colour, d))
    return T.match_mean(img, 114)


def enamel_plaque(seed, ground=(226, 222, 208), rule=(70, 66, 60), inset=2):
    """(B6) A small enamelled steel plaque's face: a slightly uneven cream enamel, a printed rule 1 px in from the
    edge, the edge itself bevelled (lit along the top and left, shaded along the bottom and right), a few chips to
    dark steel at the edge and a little grime. The screws are geometry (gen_detail.rivets), not paint."""
    img = M.noise_hv(ground, 2, seed, S, 3, hue=1.0)
    px = img.load()
    for i in range(inset, S - inset):
        for (x, y) in ((i, inset), (i, S - 1 - inset), (inset, i), (S - 1 - inset, i)):
            px[x, y] = M.rgba(M.lift(rule, M.lum(px[x, y]) - M.lum(ground)))
    M.bevel(img, (0, 0, S, S), 1, 0.16)
    M.chip_edges(img, (0, 0, S - 1, S - 1), M.sub(seed, "chips"), 5, under=(64, 62, 58))
    M.grime(img, 0.1, M.sub(seed, "grime"), cover=0.45)
    return img


def l3_plaques():
    """(B6) Level 3's room-number plaques beside the doors: the old numbers on an enamel face (enamel_plaque)."""
    out = {}
    for i, number in enumerate(("447", "112", "318", "905", "563", "274", "781", "036")):
        img = enamel_plaque(seed_of(f"l3plaque{i}"))
        text(img, number, (4, 5, 28, 19), 0x26221E, 11)
        px = img.load()
        rng = random.Random(seed_of(f"l3plaquetext{i}"))
        for y in (22, 25):  # a line of small print beneath, too small to read
            x = 7
            while x < 25:
                n = rng.randint(1, 3)
                for k in range(n):
                    if x + k < 25:
                        px[x + k, y] = M.rgba(M.lift((96, 92, 86), rng.uniform(-6, 6)))
                x += n + 1
        out[f"l3plaque{i}"] = img
    return out


def limestone(seed, base, mottle=6, pits=0.03, streaks=2):
    """Pale carved limestone for the Sanctum's statue: an even fine-grained stone with soft clouding, a few pits, and
    faint darker weathering run down from above."""
    img = M.plaster(seed, base=base, grain=3, mottle=mottle, roller=0.0, bumps=0.0)
    rng = random.Random(M.sub(seed, "pits"))
    for _ in range(int(pits * S * S)):
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, -0.12)
        M.touch(img, x, y + 1, 0.04)
    if streaks:
        M.drips(img, streaks, M.sub(seed, "weather"), color=M.lift(base, -40), length=(8, 20), strength=0.12)
    return img


# The Sanctum's ashlar (round 2): courses of 16 px with stones of mixed lengths, as the old wall had, on a bond that
# comes round over the block (the old 24 px stones did not): each row's joints, as x positions
ASHLAR_ROWS = ((0, 20), (10, 26))


def ashlar(alt):
    """Pale sandstone ashlar: two courses of mixed-length stones, each its own shade, its arris lit softly along the top
    and left and shaded along the foot, the bed joints recessed, a little claw tooling. Three versions differ only in
    the shades of the stones that lie wholly inside the block (a stone across the block edge keeps one shade)."""
    seed = seed_of("sanctumwall")
    base, mortar = (186, 177, 158), (146, 138, 120)
    img = M.noise_hv(mortar, 3, M.sub(seed, "mortar"), S, 4, (8, 4))
    face = M.noise_hv(base, 3, seed, S, 5, (8, 4, 2), hue=1.5)
    p, fp = img.load(), face.load()
    rng_alt = random.Random(seed + 7 * alt)
    rng0 = random.Random(seed)
    for r, joints in enumerate(ASHLAR_ROWS):
        y0 = r * 16
        js = list(joints) + [joints[0] + S]
        for a, b in zip(js, js[1:]):
            v0 = rng0.uniform(-6, 6)
            v = rng_alt.uniform(-6, 6)
            if b > S:  # across the block edge
                v = v0
            for y in range(y0, y0 + 15):
                for x in range(a, b - 1):
                    X = x % S
                    f = 0.0
                    if y == y0:
                        f = 0.07
                    elif y == y0 + 14:
                        f = -0.08
                    elif x == a:
                        f = 0.03
                    elif x == b - 2:
                        f = -0.04
                    p[X, y] = M.rgba(M.lift(fp[X, y], v + f * 120))
            for x in range(a, b):  # the bed joint under the stone, in its shadow
                M.touch(img, x % S, y0 + 15, -0.12)
    rng = random.Random(seed_of("tooling") + alt)
    for _ in range(60):  # the mason's claw tooling: short diagonal strokes
        x, y = rng.randrange(S), rng.randrange(S)
        if y % 16 in (0, 14, 15):
            continue
        for k in range(rng.randint(2, 3)):
            M.touch(img, x + k, y - k, -0.03)
    return T.match_rgb(img, (178, 170, 154), "sanctumwall")


def sanctum_textures():
    """(B6) The Sanctum and its statue. Ashlar: pale sandstone blocks two to a course (16 x 32 px, the old ones were
    24 px and did not tile), each its own shade with a chamfered, lit edge and a tooled face, in three versions that
    differ only in shades. Flagstones: four to a block on a square grid, so a turned block meets its neighbours,
    each its own shade with worn, recessed joints; two versions. The runner: a red cut pile with a woven gold band
    near each edge (`matlib.carpet`). The vault cells: plaster, paler toward the crown. The statue: limestone for
    the figure, the robe's folds shaded as ridges and hollows, feathers as rows of overlapping scallops each lit on
    its rounded edge, and a darker pedestal with a lit cornice line. The Purpified: wet violet skin with branching
    veins and a sheen, and the wall round it stained in a ragged, veined patch."""
    out = {}
    for alt, v in ((0, ""), (1, "-2"), (2, "-3")):
        out["sanctumwall" + v] = ashlar(alt)
    # (round 2) The flagstones are the original texture again: the blind reviewer read B6's square grid as worse
    img = noise(0x8C877C, 6, "l3stone")
    d = ImageDraw.Draw(img)
    for y, xs in ((0, (0, 18)), (11, (8, 26)), (21, (4, 20))):
        d.line([0, y, S - 1, y], fill=rgb(0x5E5A52))
        for x in xs:
            d.line([x, y, x, y + 10], fill=rgb(0x5E5A52))
    out["l3stone"] = img
    # (round 2) a short, even pile: the first cut's nap made the runner read as red static at range
    carpet = M.carpet(seed_of("sanctumcarpet"), base=(122, 34, 26), pile=3, grain=2, mottle=3)
    px = carpet.load()
    gold, shadow = (196, 156, 70), (70, 24, 18)
    for y in range(S):
        for x0 in (2, 28):
            for dx in (0, 1):
                c = M.lift(gold, (8 if (y + dx) % 2 == 0 else -10) + (M.lum(px[x0 + dx, y]) - 64) * 0.3)
                px[x0 + dx, y] = M.rgba(c)
            px[x0 - 1, y] = M.rgba(M.mix(px[x0 - 1, y], shadow, 0.25))
            px[x0 + 2, y] = M.rgba(M.mix(px[x0 + 2, y], shadow, 0.2))
    out["sanctumcarpet"] = T.match_mean(carpet, 64)
    vault = M.plaster(seed_of("sanctumvault"), base=(196, 188, 172), grain=3, mottle=5, roller=0.3)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 15.5, y - 15.5) / 22
            M.touch(vault, x, y, 0.06 * (1 - r) - 0.04)
    out["sanctumvault"] = T.match_mean(vault, 190)

    out["stone"] = T.match_mean(limestone(seed_of("stone"), (200, 196, 186)), 195)
    fold = limestone(seed_of("stonefold"), (198, 194, 184), streaks=1)
    for y in range(S):
        for x in range(S):
            t = math.cos((x + 0.5 * math.sin(y / 5.0)) / 6.0 * 2 * math.pi)  # folds a little uneven down their length
            M.touch(fold, x, y, 0.1 * t)
    out["stonefold"] = T.match_mean(fold, 193)
    # Feathers: rows of rounded tips pointing down, each row overlapping the one below (drawn from the bottom up, so
    # an upper row's tips lie over the lower row), each feather lighter along its shaft, its rounded edge lit and the
    # shadow it casts dark under it
    ground = limestone(seed_of("stonewing"), (198, 194, 184), streaks=0, pits=0.01)
    wing = ground.copy()
    gp, wp = ground.load(), wing.load()
    # (the last row once more at the end, for the tips it wraps over the first row's top)
    for row, wrapped in [(r, False) for r in reversed(range(S // 4))] + [(S // 4 - 1, True)]:
        y0 = row * 4
        off = 3 if row % 2 else 0
        for x0 in range(-6 + off, S, 6):
            for x in range(x0, x0 + 6):
                u = (x - x0 - 2.5) / 3.0
                tip = y0 + 6 - round(2.5 * u * u)  # the rounded lower edge, 2 px below the next row's top
                for y in range(y0, tip + 2):
                    if wrapped and y < S:
                        continue
                    if y <= tip:
                        c = M.lift(gp[x % S, y % S], 7 * (1 - abs(u)) - 3 + (5 if y == tip else 0))
                    else:
                        c = M.lift(gp[x % S, y % S], -26)
                    wp[x % S, y % S] = M.rgba(c)
    out["stonewing"] = T.match_mean(wing, 191)
    ped = limestone(seed_of("pedestal"), (112, 106, 96), mottle=7, pits=0.05, streaks=3)
    for x in range(S):
        M.touch(ped, x, 1, 0.16)
        M.touch(ped, x, 2, 0.08)
        M.touch(ped, x, S - 3, -0.16)
    out["pedestal"] = T.match_mean(ped, 104)

    # Purpification (layout version 5): what is left of the thing gone purple and glowing faintly, and the wall round it
    skin = M.noise_hv((136, 60, 196), 4, seed_of("purpskin"), S, 10, hue=3.0)
    rng = random.Random(seed_of("purpveins"))
    for _ in range(4):  # veins: dark branching runs
        x, y = rng.uniform(0, S), rng.uniform(0, S)
        a = rng.uniform(0, 6.3)
        for k in range(rng.randint(8, 16)):
            M.put(skin.load(), S, S, round(x), round(y), M.mix(skin.getpixel((round(x) % S, round(y) % S)), (58, 16, 88), 0.45))
            M.touch(skin, round(x), round(y) + 1, 0.06)
            a += rng.uniform(-0.6, 0.6)
            x, y = x + math.cos(a), y + math.sin(a)
    for _ in range(22):  # a wet sheen in specks
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(skin, x, y, 0.3)
    out["purpskin"] = T.match_mean(skin, 97)
    for part in ("lower", "upper"):
        img = M.noise_hv((106, 44, 156), 5, seed_of("purpwall" + part), S, 9, hue=3.0)
        rng = random.Random(seed_of("purpwallveins" + part))
        for _ in range(9):
            x, y = rng.uniform(4, 28), rng.uniform(S * 0.55 if part == "lower" else S - 3, S)
            a = rng.uniform(-2.6, -0.5)  # spreading up and out from the body
            for k in range(rng.randint(6, 14)):
                M.touch(img, round(x), round(y), -0.25)
                a += rng.uniform(-0.5, 0.5)
                x, y = x + math.cos(a), y + math.sin(a)
        px = img.load()
        edge = M.fbm((S, S), seed_of("purpedge" + part), (8, 4), 0.6)
        for y in range(S):
            for x in range(S):
                # inside an ellipse centred on the floor at the foot of the lower block (the upper one has its top)
                ey = (y - (S if part == "lower" else S * 2)) / (S * 1.35)
                ex = (x - S / 2 + 0.5) / (S * 0.5)
                d = ex * ex + ey * ey + edge[y][x] * 0.5
                if d > 1:
                    px[x, y] = (0, 0, 0, 0)
                elif d > 0.85:  # the stain thins toward its edge
                    px[x, y] = M.rgba(M.lift(px[x, y], 10), px[x, y][3])
        out[f"purpwall-{part}"] = img
    return out


def level3():
    for k, img in l3_plaques().items():
        save(img, k)
    img = noise(0xF0C818, 3, "dangersign")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x111111), width=2)
    d.rectangle([2, 2, S - 3, 11], fill=rgb(0xC81818))
    text(img, "DANGER", (2, 2, 30, 12), 0xF4F4F0, 7)
    text(img, "HIGH", (2, 13, 30, 20), 0x111111, 6)
    text(img, "VOLTAGE", (2, 20, 30, 28), 0x111111, 6)
    save(img, "dangersign")
    img = Image.new("RGBA", (S, S), rgb(0x1A1A1A))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xF0EEE4))
    for a in range(-120, 121, 30):
        r = math.radians(a)
        d.line([16 + 10 * math.sin(r), 16 - 10 * math.cos(r), 16 + 13 * math.sin(r), 16 - 13 * math.cos(r)], fill=rgb(0x222222))
    d.arc([5, 5, 26, 26], 40, 120, fill=rgb(0xC81818), width=2)
    d.line([16, 16, 24, 9], fill=rgb(0xC81818), width=2)
    save(img, "gauge")
    flat("slate", 0x2E3236, 3)
    img = noise(0x4A3020, 4, "outletburnt")
    d = ImageDraw.Draw(img)
    d.rectangle([6, 4, 25, 27], fill=rgb(0xC8BEA0))
    T.blotch(img, (16, 10), 10, (20, 18, 16), 0.85, 77)
    for y in (8, 18):
        d.rectangle([11, y, 12, y + 4], fill=rgb(0x1A1A1A))
        d.rectangle([19, y, 20, y + 4], fill=rgb(0x1A1A1A))
    save(img, "outletburnt")
    # The bulkhead's glass: a warm bulb glowing through frosted glass, bright in the middle, amber at the rim
    img = noise(0xFFB050, 3, "bulkheadglass")
    px = img.load()
    hot, rim = T.hexrgb(0xFFE6B0), T.hexrgb(0xC06A22)
    for y in range(S):
        for x in range(S):
            t = min(1.0, math.hypot(x - 15.5, y - 14.5) / 17) ** 1.4
            n = px[x, y][0] - 0xFF  # keep the frosting's grain
            px[x, y] = tuple(T.clamp(hot[k] + (rim[k] - hot[k]) * t + n) for k in range(3)) + (255,)
    save(img, "bulkheadglass")
    img = noise(0xB8733A, 6, "coil")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 2):
        d.line([0, y, S - 1, y], fill=rgb(0x8A5022))
    save(img, "coil")
    # (B6) The machine-room props' paint: their meters, lamps, switches, vents and fan guards are geometry now
    # (gen_detail.switchgear, floor_fan, generator_panel, control_desk), so these are plain painted metal
    for key, base, grime in (("switchgear", (122, 130, 136), 0.2), ("switchgearpanel", (100, 106, 110), 0.15),
                             ("switchgeartop", (112, 118, 122), 0.4), ("generatorpanel", (46, 50, 54), 0.15)):
        img = M.painted_metal(seed_of(key), base=base, grain=4, mottle=6, panel=False, chips=4, under=(150, 146, 136))
        M.grime(img, grime, seed_of(key + "g"), cover=0.6 if key == "switchgeartop" else 0.5)
        M.scratches(img, 2, seed_of(key + "s"))
        save(img, key)
    # The generator's yellow paint, with cooling ribs pressed into its casing every 6 px
    img = M.painted_metal(seed_of("generator"), base=(196, 156, 50), grain=4, mottle=6, panel=False, chips=6, under=(90, 84, 76))
    M.grime(img, 0.25, seed_of("generatorg"), cover=0.55)
    M.drips(img, 2, seed_of("generatord"), color=(70, 60, 40), length=(6, 14), strength=0.3)
    for y in range(4, S, 6):
        for x in range(S):
            M.touch(img, x, y, -0.2)
            M.touch(img, x, y + 1, 0.08)
    save(img, "generator")
    img = M.noise_hv((60, 170, 80), 3, seed_of("lampgreen"), 16, 2)
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5) / 7.5
            M.touch(img, x, y, 0.18 - 0.42 * d * d + (0.3 if math.hypot(x - 4.5, y - 4.5) < 2 else 0))
    save(img, "lampgreen")
    save(M.noise_hv((214, 200, 168), 2, seed_of("wax"), 16, 2), "wax")
    save(M.noise_hv((214, 150, 255), 3, seed_of("purpglow"), 16, 3), "purpglow")
    img = noise(0x26282A, 3, "conveyorbelt")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A3C3E))
    save(img, "conveyorbelt")
    for k, img in sanctum_textures().items():
        save(img, k)
    save(grate(), "grate")
    save(hazard_floor(), "l3hazard")


# ---------------- Level 4 ----------------

def paper_sheet(img, x, y, w, h, tilt, seed, fold=False):
    """(B7) A sheet of office paper lying on the floor: a slightly yellowed page as a tilted quad, its shadow on what
    it lies on along the lower and right edges, a few rows of grey type, and with `fold` a crease across it (a lit
    and a shaded line). All of it inside the box it is given, so a turned block never cuts a sheet."""
    rng = random.Random(seed)
    px = img.load()
    c, s_ = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    cx, cy = x + w / 2, y + h / 2

    def local(px_, py_):  # pixel centre to the sheet's own (u, v), 0..w, 0..h
        dx, dy = px_ + 0.5 - cx, py_ + 0.5 - cy
        return dx * c + dy * s_ + w / 2, -dx * s_ + dy * c + h / 2
    paper_c = (230, 228, 218)
    lines = {r: rng.uniform(w * 0.4, w - 3.5) for r in range(2, int(h) - 2, 2)}  # each row of type its own length
    for yy in range(S):
        for xx in range(S):
            u, v = local(xx, yy)
            if 0 <= u < w and 0 <= v < h:
                k = 0
                if rng.random() < 0.3:
                    k = rng.uniform(-3, 3)
                col = M.lift(paper_c, k - 6 * (v / h))  # a little shade toward its lower edge, lying on the pile
                row = int(v)
                if 2 <= u < 2 + lines.get(row, 0) and row % 2 == 0:
                    col = M.mix(col, (128, 128, 126), 0.4)  # a line of type
                if fold and abs(v - h * 0.45) < 0.5:
                    col = M.lift(col, -16)
                elif fold and abs(v - h * 0.45 - 1) < 0.5:
                    col = M.lift(col, 8)
                px[xx, yy] = M.rgba(col)
            elif -1.2 <= u < w + 1 and -0.5 <= v < h + 1.4 and (u >= w or v >= h):
                px[xx, yy] = M.rgba(M.shade_px(px[xx, yy], -0.22))  # its shadow on the carpet


def _sky(img, box, top, bottom):
    x0, y0, x1, y1 = box
    px = img.load()
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        for x in range(x0, x1):
            px[x, y] = M.rgba(M.mix(top, bottom, t))


POSTERS = {  # word, sky top, sky bottom, what stands in it
    "poster0": ("TEAMWORK", (106, 138, 176), (226, 186, 150), "rowers"),
    "poster0-2": ("COURAGE", (92, 128, 170), (196, 210, 222), "peak"),
    "poster0-3": ("VISION", (52, 60, 92), (200, 130, 96), "lighthouse"),
    "poster1": ("SUCCESS", (200, 138, 80), (236, 196, 120), "ridge"),
    "poster1-2": ("QUALITY", (90, 130, 180), (190, 210, 226), "eagle"),
    "poster1-3": ("ACHIEVE", (226, 170, 110), (244, 214, 150), "road"),
    "poster2": ("PERSEVERE", (42, 58, 90), (106, 122, 138), "wave"),
    "poster2-2": ("BALANCE", (120, 160, 196), (206, 220, 214), "tree"),
    "poster2-3": ("PURPOSE", (196, 204, 210), (230, 226, 214), "geese"),
}


def poster_prints():
    """(B7) Motivational posters: a black mat, a picture in a thin white rule (a sky graded top to bottom and a scene
    in silhouette), the word in pale capitals under it, and a line of small print; sun-faded a little and dusty, as
    everything on these walls is."""
    out = {}
    for key, (word, top, bottom, scene) in POSTERS.items():
        img = M.noise_hv((22, 22, 24), 2, seed_of(key), S, 2, (16,), hue=0.5)
        d = ImageDraw.Draw(img)
        box = (3, 3, 29, 22)
        _sky(img, box, top, bottom)
        dark = M.lift(M.mix(top, (20, 22, 28), 0.75), -10)
        if scene == "rowers":  # a shell on still water at dawn
            d.rectangle([3, 16, 28, 21], fill=M.rgba(M.mix(bottom, (40, 56, 80), 0.6)))
            d.line([7, 16, 24, 16], fill=M.rgba(dark))
            for x in range(9, 23, 3):
                d.line([x, 13, x, 15], fill=M.rgba(dark))
                d.line([x - 1, 17, x + 2, 19], fill=M.rgba(dark))
        elif scene == "peak":
            d.polygon([(3, 21), (14, 7), (19, 13), (22, 10), (28, 21)], fill=M.rgba((96, 104, 118)))
            d.polygon([(11, 11), (14, 7), (17, 11), (15, 10), (13, 12)], fill=M.rgba((236, 238, 240)))
            d.point((14, 6), fill=M.rgba(dark))
        elif scene == "lighthouse":
            d.rectangle([3, 18, 28, 21], fill=M.rgba((30, 34, 50)))
            d.polygon([(14, 18), (15, 9), (17, 9), (18, 18)], fill=M.rgba((220, 214, 200)))
            d.rectangle([14, 7, 17, 8], fill=M.rgba((250, 230, 150)))
            d.line([17, 8, 28, 5], fill=M.rgba((240, 210, 150)))
        elif scene == "ridge":
            d.polygon([(3, 21), (3, 15), (9, 11), (14, 14), (20, 9), (28, 15), (28, 21)], fill=M.rgba((70, 56, 64)))
            d.ellipse([18, 12, 23, 17], fill=M.rgba((250, 222, 150)))
            d.polygon([(3, 21), (3, 17), (12, 15), (21, 18), (28, 16), (28, 21)], fill=M.rgba((44, 38, 48)))
        elif scene == "eagle":
            d.polygon([(8, 12), (15, 14), (16, 16), (17, 14), (24, 11), (17, 15), (16, 18), (15, 15)], fill=M.rgba(dark))
            d.rectangle([3, 19, 28, 21], fill=M.rgba((110, 120, 110)))
        elif scene == "road":
            d.rectangle([3, 15, 28, 21], fill=M.rgba((150, 120, 80)))
            d.polygon([(10, 21), (15, 15), (16, 15), (21, 21)], fill=M.rgba((70, 66, 64)))
            d.line([15, 20, 15, 16], fill=M.rgba((230, 210, 140)))
        elif scene == "wave":
            d.polygon([(3, 21), (3, 16), (10, 13), (16, 11), (20, 12), (17, 14), (22, 15), (28, 14), (28, 21)],
                      fill=M.rgba((30, 50, 70)))
            d.line([16, 11, 20, 12], fill=M.rgba((220, 228, 232)))
            d.line([10, 13, 14, 12], fill=M.rgba((200, 210, 216)))
        elif scene == "tree":
            d.polygon([(3, 21), (3, 19), (10, 17), (16, 16), (22, 17), (28, 19), (28, 21)], fill=M.rgba((86, 110, 70)))
            d.line([16, 17, 16, 12], fill=M.rgba((60, 48, 36)))
            d.ellipse([11, 7, 21, 14], fill=M.rgba((64, 92, 56)))
        elif scene == "geese":
            for i in range(5):
                for sx in (-1, 1):
                    x, y = 16 + sx * i * 2, 9 + i
                    d.point((x, y), fill=M.rgba(dark))
                    d.point((x + sx, y), fill=M.rgba(dark))
        d.rectangle([2, 2, 29, 22], outline=M.rgba((200, 198, 190)))  # the print's white rule (round 2: drawn before the word)
        # (round 2) the print is drawn at 64 px (the picture doubled, the word and small print at the finer scale) so
        # the word reads from two blocks; a poster is a picture on a small face, as vanilla's paintings are
        img = img.resize((2 * S, 2 * S), Image.NEAREST)
        text(img, word, (2, 45, 62, 58), 0xE8E4D8, 9)
        for x in range(18, 46):  # small print
            if x % 3:
                img.putpixel((x, 59), M.rgba((120, 118, 112)))
        px = img.load()
        for y in range(2 * S):  # faded by years of strip light, and dusty
            for x in range(2 * S):
                c = px[x, y]
                g = M.lum(c)
                px[x, y] = M.rgba(M.mix(c, (g, g, g), 0.18))
        M.grime(img, 0.06, seed_of(key + "dust"), color=(150, 146, 136), cells=(16, 8), cover=0.5)
        out[key] = img
    return out


def level4():
    # (B7) The wall's foot: the office drywall (gen_textures.office_wall) with the vinyl cove base
    save(T.office_baseboard(T.office_wall(0)), "drywall-base")
    # (B7) The ceiling's odd blocks share the office ceiling (gen_textures.office_ceiling): the diffuser and the
    # sprinkler are geometry under a plain tile (gen_detail.level4), the stain is in one of a block's two tiles, at
    # two places
    save(T.office_ceiling(0), "officeceiling-vent")
    save(T.office_ceiling(1), "officeceiling-sprinkler")
    save(T.office_ceiling(2, stain=0), "officeceiling-stain")
    save(T.office_ceiling(0, stain=1), "officeceiling-stain-2")
    # (B7 round 2) the diffuser's white enamel with a fine orange-peel grain, and its face: concentric square air
    # slots in crisp pixels, each a dark gap with the lit lip of the ring inside it, dust fanned out round them
    save(M.painted_metal(seed_of("diffuser"), base=(222, 222, 216), grain=4, mottle=2, panel=False, chips=0), "diffuser")
    img = M.painted_metal(seed_of("diffuserface"), base=(222, 222, 216), grain=4, mottle=2, panel=False, chips=0)
    px = img.load()
    for k in (3, 7, 11):
        for i in range(k, S - k):
            for (x, y) in ((i, k), (k, i), (i, S - 1 - k), (S - 1 - k, i)):
                px[x, y] = M.rgba(M.lift(px[x, y], -70))
            for (x, y) in ((i, k + 1), (k + 1, i)):
                if k + 1 <= x < S - 1 - k and k + 1 <= y < S - 1 - k:
                    px[x, y] = M.rgba(M.lift(px[x, y], 10))
    M.grime(img, 0.12, seed_of("diffusergrime"), color=(120, 116, 104), cells=(4, 2), cover=0.45)
    save(img, "diffuser-face")
    save(M.brushed_metal(seed_of("sprinkler"), base=(196, 196, 192), grain=3, streak=6, sheen=8), "sprinklerchrome")
    save(M.noise_hv((150, 70, 58), 3, seed_of("sprinklerbulb"), S, 3, (8,)), "sprinklerbulb")  # (round 2) muted

    img = Image.new("RGBA", (S, S), rgb(0x141414))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x28292C), width=2)
    d.line([2, 2, S - 3, 2], fill=rgb(0x6A7078))  # light leaking round the paper
    d.line([2, S - 3, 12, S - 3], fill=rgb(0x5A6068))
    for x, y in ((3, 3), (25, 3), (3, 25), (25, 25)):
        d.rectangle([x, y, x + 4, y + 2], fill=rgb(0xC8C0A0))  # tape
    d.line([16, 0, 16, S - 1], fill=rgb(0x28292C))
    save(img, "officewindow-blackout")
    # (B7) Venetian blinds: each slat lit along its rounded top, shaded under it, the gap between dark, the two
    # ladder cords as pale lines, the frame as the plain window's
    img = Image.new("RGBA", (S, S), rgb(0xC8C6C0))
    px = img.load()
    rng = random.Random(seed_of("blinds"))
    for y in range(S):
        for x in range(S):
            k = y % 3
            v = (14, 0, -26)[k] + rng.uniform(-2, 2)
            px[x, y] = M.rgba(M.lift((198, 196, 190), v))
    for x in (8, 24):
        for y in range(S):
            px[x, y] = M.rgba(M.lift((226, 224, 216), 4 if y % 3 == 0 else -6))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x28292C), width=2)
    for i in range(2, S - 2):
        M.touch(img, i, 1, 0.3)
        M.touch(img, 1, i, 0.2)
    save(img, "officewindow-blinds")
    # (B7) A filing drawer's label: a white card in a steel holder (the holder's lip lit along its top), a typed line
    img = M.noise_hv((160, 162, 164), 2, seed_of("filinglabel"), S, 2, (16,))
    px = img.load()
    for y in range(S):
        for x in range(S):
            if 2 <= x % 16 <= 13 and 2 <= y % 16 <= 12:
                px[x, y] = M.rgba(M.lift((232, 230, 220), -4 * ((y % 16) > 10)))
            if (y % 16) == 0:
                px[x, y] = M.rgba(M.lift(px[x, y], 18))
    for y0 in (0, 16):
        for x0 in (0, 16):
            for x in range(x0 + 4, x0 + 11):
                px[x, y0 + 6] = M.rgba((90, 90, 96))
    save(img, "filinglabel")
    # (B7) The carpet's odd blocks: the office carpet's own versions (gen_textures.office_carpet) with papers
    # scattered on them (three arrangements) or a spill soaked in (two places); everything inside the block, as the
    # blocktype turns them at random among the plain carpet
    for alt, v, sheets in ((0, "", ((4, 5, 8, 10, 12, 1, 0), (17, 13, 8, 10, -8, 2, 1), (7, 19, 8, 10, 30, 3, 0))),
                           (1, "-2", ((14, 4, 8, 10, -20, 4, 1), (5, 15, 8, 10, 6, 5, 0))),
                           (2, "-3", ((9, 8, 8, 10, 74, 6, 0), (18, 17, 8, 10, -4, 7, 0), (16, 19, 8, 10, 22, 8, 1)))):
        img = T.office_carpet(alt)
        for (x, y, w, h, tilt, sd, fold) in sheets:
            paper_sheet(img, x, y, w, h, tilt, seed_of("papers") + sd, fold)
        save(img, "officecarpet-papers" + v)
    for alt, v, at in ((1, "", (14, 16)), (2, "-2", (18, 13))):
        plain = T.office_carpet(alt)
        img = plain.copy()
        M.stain(img, seed_of("carpetstain" + v), radius=7, color=(76, 56, 34), strength=0.45, at=at, ring=0.6)
        save(T.inside_block(plain, img), "officecarpet-stain" + v)
    for part in ("lower", "upper"):
        img = noise(0xA88458, 4, "officedoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=2)
        if part == "lower":
            d.rectangle([22, 0, 27, 2], fill=rgb(0xC0C4C8))  # lever
            d.rectangle([22, 0, 23, 4], fill=rgb(0xC0C4C8))
            d.rectangle([3, 26, 28, 29], fill=rgb(0x8A8E92))  # kick plate
        else:
            d.rectangle([5, 4, 9, 28], fill=rgb(0x3A4A52))  # narrow glass strip
            d.rectangle([14, 12, 26, 17], fill=rgb(0xC8B070))
            text(img, "ROOM", (14, 12, 27, 18), 0x2A2010, 4)
        save(img, f"officedoor-{part}")

    # Modern elevator: brushed steel leaves meeting in the middle of a 2-wide opening, an indicator above
    # (B8) The leaves are plain brushed steel: their panels' stiles and rails are geometry (gen_detail.lift_leaf_panels),
    # and only the meeting edge is painted, a dark gap with the lit arris of each leaf beside it
    for half in ("l", "r"):
        seam = S - 1 if half == "l" else 0
        for part in ("lower", "upper"):
            img = M.brushed_metal(seed_of(f"lift{part}{half}"), base=(172, 170, 166), grain=3, direction="v", streak=7, sheen=8)
            for y in range(S):
                img.putpixel((seam, y), M.rgba(M.lift((58, 62, 66), 0)))
                M.touch(img, seam - 1 if half == "l" else 1, y, 0.12, 0.1)
            save(img, f"liftdoor-{part}-{half}")
    save(M.brushed_metal(seed_of("liftsteel"), base=(180, 178, 174), grain=3, direction="v", streak=7, sheen=8), "liftsteel")
    for half in ("l", "r"):
        img = noise(0x6A6E72, 3, f"liftheader{half}")
        d = ImageDraw.Draw(img)
        d.rectangle([2, 8, S - 3, 23], fill=rgb(0x141414))
        if half == "l":
            d.polygon([(10, 20), (22, 20), (16, 11)], fill=rgb(0xF0A020))
        else:
            text(img, "13", (2, 8, S - 2, 24), 0xF0A020, 11)
        save(img, f"liftheader-{half}")
    save(M.brushed_metal(seed_of("liftframe"), base=(106, 110, 114), grain=3, direction="v", streak=6, sheen=6), "liftframe")
    img = noise(0xA8ACB0, 3, "callpanel")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x6A6E72), width=2)
    d.ellipse([11, 6, 20, 15], fill=rgb(0xF4F0E0), outline=rgb(0x4A4E52))
    d.ellipse([11, 18, 20, 27], fill=rgb(0xF0A020), outline=rgb(0x4A4E52))
    save(img, "callpanel")

    flat("fountainsteel", 0xBCC0C4, 4)
    img = Image.new("RGBA", (S, S), rgb(0xF4F2EC))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    for h in range(12):
        a = math.radians(h * 30)
        d.line([16 + 11 * math.sin(a), 16 - 11 * math.cos(a), 16 + 13 * math.sin(a), 16 - 13 * math.cos(a)], fill=rgb(0x222222))
    d.line([16, 16, 16, 7], fill=rgb(0x111111), width=2)  # stopped at 3:14
    d.line([16, 16, 23, 18], fill=rgb(0x111111), width=1)
    save(img, "clockface")
    # (B7) The whiteboard's face: its aluminium frame is geometry now, so no painted border. Old writing wiped and
    # ghosting grey, a few marker lines still on it, the board's sheen a pale band
    img = noise(0xF6F6F4, 2, "whiteboard")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("wbghost"))
    for _ in range(9):  # wiped writing: faint grey rows
        x, y = rng.randrange(2, 20), rng.randrange(3, 28)
        d.line([x, y, x + rng.randint(5, 11), y], fill=rgb(0xDCDEE2))
    T.blotch(img, (12, 12), 8, (200, 204, 210), 0.5, 335)
    d.line([4, 8, 18, 8], fill=rgb(0x2A4AA8))
    d.line([4, 12, 14, 12], fill=rgb(0x2A4AA8))
    d.ellipse([20, 18, 28, 26], outline=rgb(0xC82020))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = x - y * 0.8
            if 6 < t < 14:
                px[x, y] = M.rgba(M.lift(px[x, y], 4))
    save(img, "whiteboard")
    img = noise(0xB08A5A, 8, "corkboard")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x7A5A34), width=2)
    for x, y, c in ((5, 5, 0xF4F0E0), (18, 8, 0xF0E070), (8, 18, 0xF4F0E0)):
        d.rectangle([x, y, x + 8, y + 9], fill=rgb(c))
        d.point((x + 4, y + 1), fill=rgb(0xC82020))
    save(img, "corkboard")
    img = noise(0xF4F2EC, 2, "evacmap")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    for r in ((4, 6, 14, 14), (16, 6, 27, 14), (4, 17, 27, 26)):
        d.rectangle(r, outline=rgb(0x555555))
    d.line([8, 21, 26, 21], fill=rgb(0x2A9A3A))
    d.ellipse([7, 9, 10, 12], fill=rgb(0xD82020))
    text(img, "YOU ARE HERE", (2, 26, 30, 31), 0xD82020, 3)
    save(img, "evacmap")
    # (B7) The fire extinguisher cabinet is geometry now (gen_detail.level4): a white enamel tub, its pale blue-grey
    # back, and the extinguisher in it (red body shaded round, its label, a black valve and hose)
    save(M.painted_metal(seed_of("extsteel"), base=(226, 226, 222), grain=2, mottle=3, panel=False, chips=2,
                         under=(150, 150, 146)), "extsteel")
    save(M.noise_hv((184, 200, 204), 2, seed_of("extcabinet"), S, 3, (16, 8)), "extcabinet")
    img = M.painted_metal(seed_of("extred"), base=(186, 30, 26), grain=2, mottle=3, panel=False, chips=0)
    px = img.load()
    for y in range(S):
        for x in range(S):
            u = (x % 8) / 7.0  # round: the body's faces are 2-3 units across, so the shading repeats every 8 px
            px[x, y] = M.rgba(M.lift(px[x, y], 18 * math.cos((u - 0.3) * math.pi) - 6))
            if 10 <= y % 16 <= 14:  # the label band
                px[x, y] = M.rgba(M.lift((230, 226, 214), 14 * math.cos((u - 0.3) * math.pi) - 6))
    save(img, "extred")
    img = noise(0xF0F0EA, 2, "strobe")
    ImageDraw.Draw(img).rectangle([6, 8, 25, 23], fill=rgb(0xF8E8E0))
    text(img, "FIRE", (4, 10, 28, 22), 0xD82020, 6)
    save(img, "strobe")
    flat("switchplate", 0xE8E2D0, 2)
    img = noise(0xE4DFD2, 2, "thermostat")
    d = ImageDraw.Draw(img)
    d.rectangle([6, 8, 25, 18], fill=rgb(0x9AB89A))
    text(img, "72", (6, 8, 26, 19), 0x1E2E1E, 7)
    save(img, "thermostat")
    # (B7) The framed motivational posters: three in the layout (poster0-2), each now with two more prints listed as
    # texture alternates (gen_detail: officedeco), so a corridor of them is not the same three pictures
    for k, img in poster_prints().items():
        save(img, k)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], fill=rgb(0xE8E6E4))
    save(img, "frameghost")
    flat("wallphone", 0xD8D2C0, 3)
    img = noise(0xC8301C, 4, "stairsign-office")
    d = ImageDraw.Draw(img)
    text(img, "STAIR", (2, 4, 30, 14), 0xF4F4F0, 7)
    text(img, "3", (2, 15, 30, 29), 0xF4F4F0, 11)
    save(img, "stairsign-office")
    flat("planter", 0xE4E0D6, 3)
    # (B7) The dead ficus's foliage as cut-out leaves (the prop is drawn OpaqueNoCull, as vanilla's leaves are): small
    # pointed leaves, olive going brown and some dead, each lit on its upper side, the gaps between them open, so the
    # clumps read as sparse foliage instead of three noisy boxes
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    rng = random.Random(seed_of("ficusleaves"))
    shapes = (((0, 0), (1, 0), (2, 0), (1, 1)), ((0, 0), (0, 1), (0, 2), (1, 1)), ((0, 0), (1, 0), (1, 1), (2, 1)),
              ((1, 0), (0, 1), (1, 1), (1, 2)), ((0, 0), (1, 0), (0, 1), (1, 1)))
    for _ in range(95):  # (round 2) denser: about half the face is leaf, so a clump reads as foliage, not debris
        x, y = rng.randrange(S), rng.randrange(S)
        col = rng.choice([(92, 96, 50), (100, 98, 52), (112, 100, 54), (128, 104, 58), (84, 88, 46), (140, 110, 62)])
        for i, (dx, dy) in enumerate(rng.choice(shapes)):
            px[(x + dx) % S, (y + dy) % S] = M.rgba(M.lift(col, (8 if dy == 0 else -6 if dy == 2 else 0) + rng.uniform(-4, 4)))
    save(img, "ficusleaves")
    flat("dryleaf", 0x8A6A3A, 8)
    flat("plasticchair", 0x5A6E86, 4)
    # (B7) The copier: beige plastic (as the terminals), its control panel dark with a small green display; the
    # buttons, drawers and handles are geometry
    save(T.beige_plastic(seed_of("copier"), base=(216, 210, 194), yellow=0.1), "copier")
    img = M.noise_hv((58, 62, 66), 2, seed_of("copierpanel"), S, 2, (16,))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 4, 17, 11], fill=rgb(0x2A3A2A))
    d.rectangle([4, 5, 16, 10], fill=rgb(0x6A9A6A))
    d.line([5, 7, 13, 7], fill=rgb(0x3A5A3A))
    save(img, "copierpanel")
    img = Image.new("RGBA", (S, S), rgb(0x2A2622))
    d = ImageDraw.Draw(img)
    x = 0
    rng = random.Random(seed_of("binders"))
    while x < S:
        w = rng.randint(3, 5)
        c = rng.choice([0x2A4A8A, 0x1A1A1A, 0x8A2020, 0xE8E8E0, 0x2A6A3A])
        d.rectangle([x, 2, x + w - 1, S - 1], fill=rgb(c))
        d.rectangle([x + 1, 8, x + w - 2, 12], fill=rgb(0xF0F0EA))
        x += w + rng.choice([0, 0, 1, 6])
    save(img, "binders")
    img = Image.new("RGBA", (S, S), rgb(0x16181A))
    d = ImageDraw.Draw(img)
    rng = random.Random(4)
    for y in range(1, S, 4):
        d.line([1, y + 2, S - 2, y + 2], fill=rgb(0x2A2C2E))
        for x in range(3, S - 3, 3):
            if rng.random() < 0.3:
                d.point((x, y), fill=rgb(rng.choice([0x30E050, 0x30E050, 0xF0A020, 0x40A0F0])))
    save(img, "serverfront")
    # (B7) The kitchen counters' white laminate doors: the seam and handles are geometry now
    save(M.noise_hv((236, 236, 230), 2, seed_of("cabinetwhite"), S, 2, (16, 8), hue=0.8), "cabinetwhite")
    flat("countertop", 0x6E6A64, 3)
    img = noise(0xE8E8E4, 2, "microwave")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, 21, 27], fill=rgb(0x1E2224))
    for r in range(4):
        for c in range(2):
            d.rectangle([24 + c * 3, 6 + r * 4, 25 + c * 3, 7 + r * 4], fill=rgb(0x555555))
    d.rectangle([24, 23, 29, 26], fill=rgb(0x1A2A1A))
    save(img, "microwave")
    flat("fridgewhite", 0xF0F0EC, 2)
    img = noise(0x9A7A52, 4, "receptionfront")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 3], fill=rgb(0x6E6A64))
    d.rectangle([8, 10, 23, 20], fill=rgb(0xC8C4BA))
    text(img, "WELCOME", (8, 10, 24, 21), 0x2A2A2A, 4)
    save(img, "receptionfront")
    img = Image.new("RGBA", (S, S), rgb(0x2A2A2C))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 3):
        d.line([k, 0, k, S - 1], fill=rgb(0x3E3E40))
        d.line([0, k, S - 1, k], fill=rgb(0x3E3E40))
    save(img, "wastebin")
    flat("coat", 0x4A4E54, 5)
    img = noise(0xC8A878, 4, "benchwood")
    for x in range(0, S, 8):
        ImageDraw.Draw(img).line([0, x, S - 1, x], fill=rgb(0x9A7E54))
    save(img, "benchwood")
    # (Level 4 art) the dead ficus, reception desk, coat stand, stacked chairs, clock, office door, fountain and windows;
    # written last, so the office door and the blinds replace the earlier versions above
    import l4props_tex
    l4props_tex.generate()


# ---------------- Level 5 ----------------

def level5():
    # STAFF ONLY over the doors into the boiler halls: a black enamel plate in a brass frame, gilt capitals. Drawn in
    # rows 5-26 (the plate's UV band), the words centred on the middle of the texture
    img = noise(0x15120E, 2, "staffplaque")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 5, S - 1, 26], outline=rgb(0xB08A3A), width=2)
    d.line([1, 6, S - 2, 6], fill=rgb(0xE0C070))  # the frame's lit upper edge
    for k, word in enumerate(("STAFF", "ONLY")):
        w = glyph_width(word, PLATE_GLYPHS)
        glyphs(img, [PLATE_GLYPHS[c] for c in word], (S - w + 1) // 2, 8 + k * 9, rgb(0xE2C26A))
    save(img, "staffplaque")

    # Antique elevator: a brass scissor gate across a 2-wide opening, a dial above showing the floor
    # (B8) The gate is geometry (gen_detail.cage_gate); behind it the shaft: near black, a little lighter toward the
    # top, two cables hanging in it
    img = M.noise_hv((22, 16, 12), 2, seed_of("cageshaft"), S, 3, (16, 8), hue=0.5)
    for y in range(S):
        for x in range(S):
            M.touch(img, x, y, 0.25 * (1 - y / S) - 0.1, 0.05)
        for x in (9, 22):
            img.putpixel((x, y), M.rgba(M.lift(img.getpixel((x, y)), 16)))
            M.touch(img, x + 1, y, -0.15)
    save(img, "cageshaft")
    # The call plate's ivory pushes, a highlight on their upper left
    img = M.noise_hv((232, 222, 196), 2, seed_of("callbutton"), S, 2, (16, 8), hue=1.0)
    M.bevel(img, None, 3, 0.12)
    save(img, "callbutton")
    # The room keys' oval brass fobs, numbers stamped on (four fobs to the texture, one per quarter)
    img = T.brass_metal(seed_of("keytag"))
    for qx in (0, 16):
        for qy in (0, 16):
            M.bevel(img, (qx, qy, qx + 16, qy + 16), 1, 0.2)
            for k, x in enumerate(range(qx + 4, qx + 12, 3)):
                for y in range(qy + 6, qy + 10):
                    if (y + k) % 4:
                        M.touch(img, x, y, -0.3)
    save(img, "keytag")
    # (B8) The front desk's plinth: the mahogany, darker
    save(T.match_rgb(T.wood_grain(seed_of("mahoganydark"), (60, 32, 20), "h"), (56, 30, 18)), "mahoganydark")
    big = Image.new("RGBA", (2 * S, S), rgb(0x452518))
    d = ImageDraw.Draw(big)
    d.pieslice([6, 4, 58, 56], 180, 360, fill=rgb(0xC9A040), outline=rgb(0x8A6A20))
    d.pieslice([10, 8, 54, 52], 180, 360, fill=rgb(0xF0E6C8))
    for i in range(13):
        a = math.radians(180 + i * 15)
        d.line([32 + 18 * math.cos(a), 30 + 18 * math.sin(a), 32 + 21 * math.cos(a), 30 + 21 * math.sin(a)], fill=rgb(0x3A2A10))
    d.line([32, 30, 32 + 17 * math.cos(math.radians(318)), 30 + 17 * math.sin(math.radians(318))], fill=rgb(0x1A1A1A), width=2)
    d.rectangle([0, 0, 2 * S - 1, 1], fill=rgb(0x8A6A20))
    save(big.crop((0, 0, S, S)), "cagedial-l")
    save(big.crop((S, 0, 2 * S, S)), "cagedial-r")

    # Mirror glass edge to edge: pale blue-grey, a little darker toward the foot, a 1 px bevel lit from above, and
    # a diagonal sheen
    img = texlib.vertical_gradient(T.hexrgb(0xB2C2CA), T.hexrgb(0x96A6B0))
    d = ImageDraw.Draw(img)
    for k, w, c in ((-6, 3, 0xC8D6DC), (2, 1, 0xC2D0D6), (14, 2, 0xBCCAD2)):  # the sheen, rising to the right
        d.line([k, S - 1, k + S - 1, 0], fill=rgb(c), width=w)
    d.line([0, 0, S - 1, 0], fill=rgb(0xDCE6EA))  # bevel
    d.line([0, 0, 0, S - 1], fill=rgb(0xD0DCE2))
    d.line([0, S - 1, S - 1, S - 1], fill=rgb(0x6E7E88))
    d.line([S - 1, 0, S - 1, S - 1], fill=rgb(0x7A8A94))
    save(img, "mirrorglass")
    img = noise(0xB08A3C, 5, "speakergrille")
    d = ImageDraw.Draw(img)
    for r in range(3, 15, 3):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0x5A4418))
    save(img, "speakergrille")
    flat("bakelite", 0x18120E, 2)
    img = Image.new("RGBA", (S, S), rgb(0x18120E))
    d = ImageDraw.Draw(img)
    d.ellipse([3, 3, 28, 28], fill=rgb(0xE8E0C8))
    for i in range(10):
        a = math.radians(i * 30 + 30)
        d.ellipse([14 + 9 * math.cos(a), 14 + 9 * math.sin(a), 18 + 9 * math.cos(a), 18 + 9 * math.sin(a)], fill=rgb(0x18120E))
    save(img, "phonedial")
    img = noise(0x8A1C14, 4, "hotelhosecab")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 29, 29], outline=rgb(0xC9A040), width=2)
    d.rectangle([5, 5, 26, 26], fill=rgb(0x2A1410))
    d.ellipse([8, 8, 23, 23], outline=rgb(0xB8733A), width=3)
    d.line([6, 6, 12, 12], fill=rgb(0xE0E8EC))
    save(img, "hotelhosecab")
    img = Image.new("RGBA", (S, S), rgb(0xC9A040))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xF0E6C8), outline=rgb(0x8A6A20))
    for h in range(12):
        a = math.radians(h * 30)
        d.line([16 + 10 * math.sin(a), 16 - 10 * math.cos(a), 16 + 12 * math.sin(a), 16 - 12 * math.cos(a)], fill=rgb(0x2A1A0A), width=1)
    d.line([16, 16, 16, 6], fill=rgb(0x111111))
    d.line([16, 16, 10, 20], fill=rgb(0x111111), width=2)
    save(img, "ornateclock")
    # (B8) The key rack's old painted picture (unused since the rack was modelled) and the painted call plate are gone
    # A pastoral landscape: an evening sky, a line of blue hills, green fields, a tree, a road toward a house
    img = texlib.vertical_gradient((232, 196, 140), (150, 170, 190), height=S)
    d = ImageDraw.Draw(img)
    d.polygon([(0, 15), (6, 11), (12, 14), (19, 9), (26, 13), (31, 11), (31, 18), (0, 18)], fill=rgb(0x6A7A98))
    d.rectangle([0, 17, S - 1, S - 1], fill=rgb(0x6E8A3E))
    d.polygon([(0, 24), (31, 20), (31, 31), (0, 31)], fill=rgb(0x5A7832))
    d.polygon([(14, 31), (17, 18), (18, 18), (21, 31)], fill=rgb(0xB8A274))
    d.rectangle([22, 15, 25, 18], fill=rgb(0xE8E0D0))
    d.polygon([(21, 15), (23.5, 12), (26, 15)], fill=rgb(0x8A3A2A))
    d.ellipse([3, 9, 11, 17], fill=rgb(0x3A5A2A))
    d.rectangle([6, 16, 7, 22], fill=rgb(0x4A3220))
    d.ellipse([24, 3, 28, 7], fill=rgb(0xF8E8B0))
    save(img, "landscape")

    # White marble floor: grey veining, with small black diamonds set at the corners where four slabs meet
    img = texlib.marble((232, 228, 220), (150, 146, 140), 66, sharpness=6, mottle=0.05)
    d = ImageDraw.Draw(img)
    for x, y in ((0, 0), (S, 0), (0, S), (S, S)):
        d.polygon([(x - 4, y), (x, y - 4), (x + 4, y), (x, y + 4)], fill=rgb(0x1E1C1A))
    save(img, "marble")
    save(texlib.marble((236, 232, 224), (160, 154, 146), 67, sharpness=7, mottle=0.04), "marbletop")
    # (B8) The runner: a short red pile with its gold bands woven in, a dark binding along each edge and a small gold
    # lozenge every half block, laid over the dining rooms' walnut boards (gen_textures.hotel_floorboards, so it
    # meets the bare floor beside it), the boards in shadow along the runner's edges
    red = (138, 28, 20)
    pile = T.hotel_pile(seed_of("runner"), red)

    def bands(d, k):
        for x in (5, 25):
            d.rectangle([x * k, 0, (x + 2) * k - 1, S * k - 1], fill=255)
        for cy in (8, 24):
            d.polygon([(16 * k, (cy - 3) * k), (19 * k, cy * k), (16 * k, (cy + 3) * k), (13 * k, cy * k)], fill=255)

    def binding(d, k):
        for x in (3, 28):
            d.rectangle([x * k, 0, (x + 1) * k - 1, S * k - 1], fill=255)
    M.dye(pile, T.layered_pattern([((201, 160, 64), bands), ((84, 14, 10), binding)], crisp=True), red)
    T.dingy(pile, seed_of("runner"), dull=0.05, dim=1.0, grime=0.05, flecks=5)
    for axis in ("ns", "we"):
        img = T.hotel_floorboards(0)
        lay = pile if axis == "ns" else pile.transpose(Image.Transpose.ROTATE_90)
        for y in range(S):
            for x in range(S):
                u = x if axis == "ns" else y
                if 3 <= u <= 28:
                    img.putpixel((x, y), lay.getpixel((x, y)))
                elif u in (2, 29):
                    M.touch(img, x, y, -0.18)
        save(img, f"runner-{axis}")
    # (B8) The Persian rug on the same short pile: its red field, navy border with a row of gold knots, the navy
    # medallion edged in gold with a gold heart, gold corner squares
    field = (122, 26, 24)
    img = T.hotel_pile(seed_of("rug"), field)

    def border(d, k):
        d.rectangle([0, 0, S * k - 1, S * k - 1], fill=255)
        d.rectangle([3 * k, 3 * k, (S - 3) * k - 1, (S - 3) * k - 1], fill=0)
        d.polygon([(16 * k, 5 * k), (27 * k, 16 * k), (16 * k, 27 * k), (5 * k, 16 * k)], fill=255)

    def gold(d, k):
        d.polygon([(16 * k, 4 * k), (28 * k, 16 * k), (16 * k, 28 * k), (4 * k, 16 * k)], outline=255, width=k)
        d.polygon([(16 * k, 10 * k), (22 * k, 16 * k), (16 * k, 22 * k), (10 * k, 16 * k)], fill=255)
        for i in range(2, S, 4):
            for (x, y) in ((i, 1), (i, S - 2), (1, i), (S - 2, i)):
                d.rectangle([x * k, y * k, (x + 1) * k - 1, (y + 1) * k - 1], fill=255)
        for (x, y) in ((4, 4), (26, 4), (4, 26), (26, 26)):
            d.rectangle([x * k, y * k, (x + 2) * k - 1, (y + 2) * k - 1], fill=255)
    M.dye(img, T.layered_pattern([((30, 42, 74), border), ((201, 160, 64), gold)], crisp=True), field)
    T.dingy(img, seed_of("rug"), dull=0.05, dim=1.0, grime=0.05, flecks=5)
    save(img, "rug")

    img = noise(0xE8ECF4, 3, "vase")
    d = ImageDraw.Draw(img)
    for y in (6, 16, 26):
        d.line([0, y, S - 1, y], fill=rgb(0x2A4A9A), width=2)
    save(img, "vase")
    flat("driedflowers", 0x7A4A3A, 12)
    img = Image.new("RGBA", (S, S), rgb(0x2A1810))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("books"))
    for row in range(2):
        x = 0
        while x < S:
            w = rng.randint(2, 4)
            c = rng.choice([0x5A1A14, 0x1E3A2A, 0x2A2A4A, 0x6A4A2A, 0x3A1A2A])
            top = row * 16 + rng.randint(1, 4)
            d.rectangle([x, top, x + w - 1, row * 16 + 15], fill=rgb(c))
            d.line([x, top + 3, x + w - 1, top + 3], fill=rgb(0xC9A040))
            x += w
    save(img, "books")
    img = Image.new("RGBA", (S, S), rgb(0x1A2224))
    d = ImageDraw.Draw(img)
    d.line([4, 2, 12, 30], fill=rgb(0x5A6E74))
    d.line([18, 2, 26, 30], fill=rgb(0x3A4A50))
    save(img, "curioglass")
    flat("china", 0xF4F2EC, 2)
    flat("cartcarpet", 0x8A1C14, 4)
    img = noise(0x6A3A1E, 5, "suitcaseleather")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x3A1E0E), width=2)
    for x in (8, 23):
        d.rectangle([x, 0, x + 1, S - 1], fill=rgb(0x3A1E0E))
    save(img, "suitcaseleather")
    flat("suitcasetan", 0xB89060, 5)
    flat("tablecloth", 0xF2F0EA, 2)
    flat("silver", 0xD0D4D8, 4)
    img = noise(0xD8CCA8, 3, "radiator")
    for x in range(0, S, 4):
        ImageDraw.Draw(img).line([x, 0, x, S - 1], fill=rgb(0xA89A78))
    save(img, "radiator")
    flat("bankergreen", 0x1E7A44, 4)
    img = Image.new("RGBA", (S, S), rgb(0x1A120C))
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, 22], fill=rgb(0xC9A040), width=1)
    d.ellipse([12, 21, 20, 29], fill=rgb(0xC9A040))
    save(img, "clockpendulum")
    img = Image.new("RGBA", (S, S), rgb(0x5A2E1A))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, 29, 29], fill=rgb(0xE8DCBC), outline=rgb(0xC9A040), width=2)
    for h in range(12):
        a = math.radians(h * 30)
        d.text((14 + 10 * math.sin(a), 13 - 10 * math.cos(a)), ".", fill=rgb(0x1A1A1A))
    d.line([16, 16, 16, 7], fill=rgb(0x111111))
    d.line([16, 16, 22, 19], fill=rgb(0x111111), width=2)
    save(img, "clockface-old")
    # (B8) The front desk's panels are geometry now (gen_detail level5); its painted front is gone
    img = noise(0x5A1A14, 3, "guestbook")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, 29, 29], fill=rgb(0xF0E8D0))
    d.line([16, 2, 16, 29], fill=rgb(0x8A7A5A))
    for y in range(6, 28, 3):
        d.line([4, y, 13, y], fill=rgb(0x5A5A7A))
        d.line([19, y, 27, y], fill=rgb(0x5A5A7A))
    save(img, "guestbook")
    flat("pianoblack", 0x101012, 2)
    img = Image.new("RGBA", (S, S), rgb(0xF4F2EA))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 2):
        d.line([x, 0, x, S - 1], fill=rgb(0xB8B6AE))
    for x in range(1, S, 4):
        d.rectangle([x, 0, x + 1, 18], fill=rgb(0x111111))
    save(img, "pianokeys")
    # (B6) Coal: broken faces, each a flat facet at its own shade, some catching the light with a glint
    pts = M.points((S, S), 40, seed_of("coalfacets"), 1.0)
    f1, f2, idx = M.worley((S, S), pts)
    rng = random.Random(77)
    shades = [rng.uniform(-10, 14) for _ in pts]
    img = M.noise_hv((28, 28, 30), 3, seed_of("coal"), S, 3, hue=0.5)
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = shades[idx[y][x]] - (8 if f2[y][x] - f1[y][x] < 0.8 else 0)
            px[x, y] = M.rgba(M.lift(px[x, y], d, 0.05))
    for _ in range(14):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = M.rgba((96, 98, 104))
    save(img, "coal")


def generate():
    shared()
    level1()
    level3()
    level4()
    level5()
