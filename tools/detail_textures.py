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
        if alt == 2:
            rng = random.Random(sd)
            for _ in range(3):
                x, y, L = rng.uniform(0, S), rng.uniform(0, S), rng.randint(3, 7)
                a = rng.uniform(-0.5, 0.5) + rng.choice((0, 1.57))
                for i in range(L):
                    t = math.sin(math.pi * (i + 0.5) / L)
                    M.touch(img, round(x + math.cos(a) * i), round(y + math.sin(a) * i), -0.09 * t)
        save(T.match_mean(img, 113), "l1hallfloor" + v)

    # (B4) The locked steel door, still a cube (the block has no facing to hang a modelled door on): dark painted
    # steel with an orange-peel finish, the frame lit on its top and left edges and shaded where it meets the leaf,
    # the push bar and the window's bead shaded as raised parts, the kick plate brushed, wear at the handle
    for part in ("lower", "upper"):
        img = M.painted_metal(seed_of("metaldoor" + part), base=(36, 38, 40), grain=2, mottle=4, panel=False, chips=3,
                              under=(84, 86, 88))
        px = img.load()
        frame = (84, 86, 90)
        for y in range(S):
            for x in range(S):
                if x < 2 or x >= S - 2 or (part == "upper" and y < 2) or (part == "lower" and y >= S - 2):
                    px[x, y] = M.rgba(M.lift(frame, (2 - min(x, 2)) * 6 - (x >= S - 2) * 8 + (y < 2) * 6))
        for y in range(S):  # the leaf's edge in the frame's shadow
            M.touch(img, 2, y, -0.18)
            M.touch(img, S - 3, y, 0.06)
        if part == "upper":
            for x in range(2, S - 2):
                M.touch(img, x, 2, -0.18)
        if part == "lower":
            kick = M.brushed_metal(seed_of("metaldoorkick"), base=(120, 122, 124), grain=3)
            kp = kick.load()
            for y in range(19, 29):
                for x in range(4, 28):
                    px[x, y] = kp[x, y]
            M.bevel(img, (4, 19, 28, 29), 1, 0.2)
            for (sx, sy) in ((5, 20), (26, 20), (5, 27), (26, 27)):
                px[sx, sy] = M.rgba((64, 66, 68))
            bar = (168, 172, 176)  # the push bar: a lit top, a dark underside and a shadow on the leaf below it
            for x in range(5, 27):
                px[x, 2] = M.rgba(M.lift(bar, 16))
                px[x, 3] = M.rgba(bar)
                px[x, 4] = M.rgba(M.lift(bar, -38))
                M.touch(img, x, 5, -0.2)
                M.touch(img, x, 6, -0.08)
            for y in range(1, 7):
                for x in range(24, 27):
                    px[x, y] = M.rgba(M.lift((124, 128, 132), 10 if y == 1 else -14 if y == 6 else 0))
        else:
            # wired glass in a raised bead: dark glass with a faint diagonal sheen and the wire mesh
            for y in range(5, 21):
                for x in range(9, 23):
                    c = (26, 34, 38)
                    if (x - 9 + y - 5) % 4 == 0 or (x - 9 - (y - 5)) % 4 == 0:
                        c = (70, 80, 86)
                    if 6 <= (x - 9) + (20 - y) <= 9:
                        c = M.lift(c, 14)
                    px[x, y] = M.rgba(c)
            for x in range(8, 24):
                M.touch(img, x, 4, 0.3)
                M.touch(img, x, 21, -0.3)
            for y in range(4, 22):
                M.touch(img, 8, y, 0.24)
                M.touch(img, 23, y, -0.26)
            d = ImageDraw.Draw(img)
            d.rectangle([7, 24, 24, 29], fill=rgb(0xD8B028))
            text(img, "NO ENTRY", (7, 24, 25, 30), 0x1A1A1A, 5)
            for x in range(7, 25):
                M.touch(img, x, 24, 0.08)
                M.touch(img, x, 29, -0.1)
        save(img, f"metaldoor-{part}")
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

def level3():
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
    flat("switchgear", 0x7A8288, 3)
    img = noise(0x7A8288, 3, "switchgearfront")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x4A5258), width=1)
    d.line([0, 15, S - 1, 15], fill=rgb(0x4A5258))
    for i, x in enumerate((5, 13, 21)):
        d.ellipse([x, 3, x + 6, 9], fill=rgb(0xF0EEE4), outline=rgb(0x222222))
        d.line([x + 3, 6, x + 5, 4], fill=rgb(0xC81818))
        d.ellipse([x + 1, 11, x + 3, 13], fill=rgb(0xE83020 if i != 1 else 0x30D050))
    d.rectangle([24, 20, 27, 27], fill=rgb(0x1A1A1A))  # handle
    d.rectangle([4, 19, 18, 23], fill=rgb(0xF4F4F0))
    text(img, "No. 7", (4, 19, 19, 24), 0x111111, 4)
    save(img, "switchgearfront")
    img = Image.new("RGBA", (S, S), rgb(0x1E2022))
    d = ImageDraw.Draw(img)
    for r in range(3, 16, 3):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0x6A6E72))
    d.line([16, 1, 16, 31], fill=rgb(0x6A6E72))
    d.line([1, 16, 31, 16], fill=rgb(0x6A6E72))
    save(img, "fancage")
    img = noise(0xC8A030, 5, "generator")
    d = ImageDraw.Draw(img)
    for y in range(4, S, 6):
        d.line([0, y, S - 1, y], fill=rgb(0x9A7820))
    save(img, "generator")
    img = noise(0x2E3236, 3, "generatorpanel")
    d = ImageDraw.Draw(img)
    for x in (5, 17):
        d.ellipse([x, 4, x + 9, 13], fill=rgb(0xF0EEE4))
        d.line([x + 4, 9, x + 7, 6], fill=rgb(0xC81818))
    for x in range(5, 27, 5):
        d.rectangle([x, 19, x + 2, 24], fill=rgb(0xD8D8D0))
    d.ellipse([24, 26, 28, 30], fill=rgb(0xD82020))
    save(img, "generatorpanel")
    img = noise(0x8E6A40, 5, "spoolwood")
    d = ImageDraw.Draw(img)
    for r in (5, 10, 14):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0x6A4A28))
    save(img, "spoolwood")
    img = noise(0x5A6268, 3, "controlpanel")
    d = ImageDraw.Draw(img)
    for i in range(4):
        x = 3 + i * 7
        d.ellipse([x, 3, x + 5, 8], fill=rgb(0xF0EEE4))
        d.line([x + 2, 6, x + 4, 4], fill=rgb(0x111111))
    for i in range(8):
        d.rectangle([3 + i * 3, 13, 4 + i * 3, 17], fill=rgb(0xD8D8D0 if i % 3 else 0x222222))
    for i, c in enumerate((0xE83020, 0x30D050, 0xF0C020, 0x30D050, 0xE83020)):
        d.ellipse([4 + i * 5, 22, 6 + i * 5, 24], fill=rgb(c))
    save(img, "controlpanel")
    img = noise(0x26282A, 3, "conveyorbelt")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A3C3E))
    save(img, "conveyorbelt")
    img = noise(0xC8C4BA, 5, "stone")
    T.blotch(img, (8, 24), 7, (150, 146, 136), 0.3, 91)
    save(img, "stone")
    img = noise(0xC8C4BA, 5, "stonewing")
    d = ImageDraw.Draw(img)
    for y in range(3, S, 5):
        d.arc([-8, y - 6, 40, y + 6], 20, 160, fill=rgb(0xA8A498))
    save(img, "stonewing")
    # The statue's pedestal, darker than the figure so the figure stands clear of it; its folds
    img = noise(0x6E685E, 4, "pedestal")
    d = ImageDraw.Draw(img)
    d.line([0, 2, S - 1, 2], fill=rgb(0x8A8478))
    d.line([0, S - 3, S - 1, S - 3], fill=rgb(0x4E4A42))
    save(img, "pedestal")
    img = noise(0xC8C4BA, 4, "stonefold")
    d = ImageDraw.Draw(img)
    for x in range(2, S, 6):
        d.line([x, 0, x + 1, S - 1], fill=rgb(0xA49E92))
        d.line([x + 2, 0, x + 3, S - 1], fill=rgb(0xDAD6CC))
    save(img, "stonefold")
    # A Sanctum's ceiling: pale ashlar ribs, and the plastered vault cells between them, paler toward their middles
    img = noise(0xC4BCAC, 3, "sanctumvault")
    T.blotch(img, (16, 16), 14, (214, 208, 194), 0.6, 93)
    save(img, "sanctumvault")
    # Purpification (layout version 5): what is left of the thing gone purple and glowing faintly, and the wall round it
    img = noise(0x8A3CC8, 8, "purpskin")
    T.blotch(img, (10, 12), 7, (190, 120, 240), 0.6, 94)
    T.blotch(img, (24, 24), 6, (60, 20, 96), 0.6, 95)
    d = ImageDraw.Draw(img)
    for (x1, y1, x2, y2) in ((3, 4, 12, 20), (18, 2, 22, 14), (14, 22, 28, 30)):
        d.line([x1, y1, x2, y2], fill=rgb(0x4A1470))  # veins
    save(img, "purpskin")
    # The wall gone purple round it, a ragged patch over two blocks: the lower block mostly, the upper only at its foot
    rng = random.Random(seed_of("purpwall"))
    for part in ("lower", "upper"):
        img = noise(0x6A2C9C, 6, "purpwall" + part)
        for k, (cx, cy, r) in enumerate(((8, 20, 9), (24, 26, 10), (14, 8, 7))):
            T.blotch(img, (cx, cy), r, (150, 90, 210), 0.45, 96 + k)
        px = img.load()
        for y in range(S):
            for x in range(S):
                # Inside an ellipse centred on the floor at the foot of the lower block (the upper one has its top)
                ey = (y - (S if part == "lower" else S * 2)) / (S * 1.35)
                ex = (x - S / 2 + 0.5) / (S * 0.5)
                if ex * ex + ey * ey + rng.uniform(-0.12, 0.12) > 1:
                    px[x, y] = (0, 0, 0, 0)
        save(img, f"purpwall-{part}")
    img = Image.new("RGBA", (S, S), rgb(0x1E2022))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 4):
        d.line([k, 0, k, S - 1], fill=rgb(0x5A5E62))
        d.line([0, k, S - 1, k], fill=rgb(0x4A4E52))
    save(img, "grate")
    img = T.noise_fill(T.hexrgb(0x857868), 6, 505)
    stripes(img, rgb(0xE0B020), rgb(0x1E1E1E), 4, (0, 0, S, 6))
    stripes(img, rgb(0xE0B020), rgb(0x1E1E1E), 4, (0, S - 6, S, S))
    save(img, "l3hazard")
    img = noise(0x8C877C, 6, "l3stone")
    d = ImageDraw.Draw(img)
    for y, xs in ((0, (0, 18)), (11, (8, 26)), (21, (4, 20))):
        d.line([0, y, S - 1, y], fill=rgb(0x5E5A52))
        for x in xs:
            d.line([x, y, x, y + 10], fill=rgb(0x5E5A52))
    save(img, "l3stone")
    img = noise(0x7A1414, 4, "sanctumcarpet")
    d = ImageDraw.Draw(img)
    for x in (2, 29):
        d.rectangle([x, 0, x + 1, S - 1], fill=rgb(0xC8A040))
    save(img, "sanctumcarpet")
    img = noise(0xB8B0A0, 4, "sanctumwall")
    d = ImageDraw.Draw(img)
    for r in range(2):
        y = r * 16
        d.line([0, y, S - 1, y], fill=rgb(0x8A8274))
        off = 12 if r % 2 else 0
        for x in range(off, S + 24, 24):
            d.line([x % S, y, x % S, y + 15], fill=rgb(0x8A8274))
    save(img, "sanctumwall")


# ---------------- Level 4 ----------------

def level4():
    wall = noise(0xD8D5D4, 4, "officewall-x")
    base = wall.copy()
    d = ImageDraw.Draw(base)
    d.rectangle([0, 27, S - 1, S - 1], fill=rgb(0x3E3E40))
    d.line([0, 26, S - 1, 26], fill=rgb(0x555558))
    save(base, "drywall-base")
    tile = T.noise_fill(T.hexrgb(0xD8D4CF), 3, 524)
    d = ImageDraw.Draw(tile)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x969490))
    d.line([0, 15, S - 1, 15], fill=rgb(0x969490))
    img = tile.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([7, 7, 24, 24], fill=rgb(0xE8E8E4), outline=rgb(0xA8A8A4))
    for k in (10, 13):
        d.rectangle([k, k, S - 1 - k, S - 1 - k], outline=rgb(0xB8B8B4))
    save(img, "officeceiling-vent")
    img = tile.copy()
    d = ImageDraw.Draw(img)
    d.ellipse([13, 20, 18, 25], fill=rgb(0xE0E0DC), outline=rgb(0x9A9A96))
    d.point((15, 22), fill=rgb(0xC8301C))
    save(img, "officeceiling-sprinkler")
    img = tile.copy()
    T.blotch(img, (18, 12), 11, (150, 120, 70), 0.55, 333)
    save(img, "officeceiling-stain")

    img = Image.new("RGBA", (S, S), rgb(0x141414))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x28292C), width=2)
    d.line([2, 2, S - 3, 2], fill=rgb(0x6A7078))  # light leaking round the paper
    d.line([2, S - 3, 12, S - 3], fill=rgb(0x5A6068))
    for x, y in ((3, 3), (25, 3), (3, 25), (25, 25)):
        d.rectangle([x, y, x + 4, y + 2], fill=rgb(0xC8C0A0))  # tape
    d.line([16, 0, 16, S - 1], fill=rgb(0x28292C))
    save(img, "officewindow-blackout")
    img = Image.new("RGBA", (S, S), rgb(0xC8C6C0))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 3):
        d.line([0, y, S - 1, y], fill=rgb(0x8A8884))
    d.line([8, 0, 8, S - 1], fill=rgb(0xE8E8E2))
    d.line([24, 0, 24, S - 1], fill=rgb(0xE8E8E2))
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x28292C), width=2)
    save(img, "officewindow-blinds")
    carpet = T.noise_fill(T.hexrgb(0x85837D), 7, 523)
    img = carpet.copy()
    d = ImageDraw.Draw(img)
    for x, y, a in ((4, 6, 0), (18, 14, 1), (9, 22, 0)):
        d.polygon([(x, y), (x + 8, y + a * 2), (x + 7, y + 10), (x - 1, y + 9 - a)], fill=rgb(0xF0EEE6))
        d.line([x + 1, y + 3, x + 6, y + 3], fill=rgb(0x9A9A9A))
    save(img, "officecarpet-papers")
    img = carpet.copy()
    T.blotch(img, (14, 16), 7, (70, 50, 30), 0.6, 334)
    save(img, "officecarpet-stain")
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
    for half in ("l", "r"):
        seam, frame = (S - 1, 0) if half == "l" else (0, S - 1)
        for part in ("lower", "upper"):
            img = noise(0xA8ACB0, 3, f"lift{part}{half}")
            d = ImageDraw.Draw(img)
            for x in range(1, S, 3):
                d.line([x, 0, x, S - 1], fill=rgb(0x9CA0A4))
            d.line([seam, 0, seam, S - 1], fill=rgb(0x3A3E42))
            d.rectangle([frame - 1 if half == "r" else 0, 0, frame if half == "r" else 1, S - 1], fill=rgb(0x6A6E72))
            if part == "upper":
                d.rectangle([0, 0, S - 1, 1], fill=rgb(0x6A6E72))
            save(img, f"liftdoor-{part}-{half}")
        img = noise(0x6A6E72, 3, f"liftheader{half}")
        d = ImageDraw.Draw(img)
        d.rectangle([2, 8, S - 3, 23], fill=rgb(0x141414))
        if half == "l":
            d.polygon([(10, 20), (22, 20), (16, 11)], fill=rgb(0xF0A020))
        else:
            text(img, "13", (2, 8, S - 2, 24), 0xF0A020, 11)
        save(img, f"liftheader-{half}")
    flat("liftframe", 0x6A6E72, 3)
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
    img = noise(0xF6F6F4, 2, "whiteboard")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xA8ACB0), width=1)
    T.blotch(img, (12, 12), 8, (200, 204, 210), 0.5, 335)
    d.line([4, 8, 18, 8], fill=rgb(0x2A4AA8))
    d.line([4, 12, 14, 12], fill=rgb(0x2A4AA8))
    d.ellipse([20, 18, 28, 26], outline=rgb(0xC82020))
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
    img = noise(0xE8E8E2, 2, "extcabinet")
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0xB8C8CC), outline=rgb(0x8A8E92))
    d.rectangle([12, 8, 19, 26], fill=rgb(0xC21C18))
    d.rectangle([13, 5, 17, 8], fill=rgb(0x1A1A1A))
    d.line([5, 5, 10, 10], fill=rgb(0xF0F8FA))
    save(img, "extcabinet")
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
    for i, (word, sky, ground) in enumerate((("TEAMWORK", 0x6A8AB0, 0x5A6A4A), ("SUCCESS", 0xC88A50, 0x3A3A44), ("PERSEVERE", 0x2A3A5A, 0x6A7A8A))):
        img = Image.new("RGBA", (S, S), rgb(0x1A1A1A))
        d = ImageDraw.Draw(img)
        d.rectangle([2, 2, 29, 22], fill=rgb(sky))
        d.polygon([(2, 22), (12, 8), (18, 16), (22, 11), (29, 22)], fill=rgb(ground))
        text(img, word, (1, 23, 31, 30), 0xE8E4D8, 5)
        save(img, f"poster{i}")
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
    img = noise(0x6A6A3A, 14, "ficusleaves")
    rng = random.Random(7)
    for _ in range(50):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(rng.choice([0x8A7040, 0x4A5A2A, 0xA08048])))
    save(img, "ficusleaves")
    flat("dryleaf", 0x8A6A3A, 8)
    flat("plasticchair", 0x5A6E86, 4)
    flat("copier", 0xD8D2C2, 3)
    img = noise(0x3A3E42, 3, "copierpanel")
    ImageDraw.Draw(img).rectangle([4, 6, 18, 14], fill=rgb(0x7AB07A))
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
    img = noise(0xEEEEE8, 2, "cabinetwhite")
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, S - 1], fill=rgb(0xB8B8B2))
    d.rectangle([12, 4, 14, 5], fill=rgb(0x8A8E92))
    d.rectangle([18, 4, 20, 5], fill=rgb(0x8A8E92))
    save(img, "cabinetwhite")
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
    for half in ("l", "r"):
        img = Image.new("RGBA", (S, S), rgb(0x1E120A))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], fill=rgb(0x2A1A10))
        for k in range(-S, 2 * S, 8):
            d.line([k, 0, k + S, S], fill=rgb(0xC89A40), width=1)
            d.line([k + S, 0, k, S], fill=rgb(0xC89A40), width=1)
        for x in range(0, S, 8):
            d.line([x, 0, x, S - 1], fill=rgb(0xA87A30))
        edge = 0 if half == "l" else S - 2
        d.rectangle([edge, 0, edge + 1, S - 1], fill=rgb(0x8A6020))
        save(img, f"cagegate-{half}")
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
    img = noise(0x5A2E1A, 4, "keyrack")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x3A1C0E))
    for x in range(0, S, 8):
        d.line([x, 0, x, S - 1], fill=rgb(0x3A1C0E))
    rng = random.Random(55)
    for y in range(0, S, 8):
        for x in range(0, S, 8):
            if rng.random() < 0.6:
                d.line([x + 4, y + 1, x + 4, y + 5], fill=rgb(0xD8B050))
                d.rectangle([x + 3, y + 5, x + 5, y + 7], fill=rgb(0xE8DCC0))
    save(img, "keyrack")
    img = noise(0xC9A040, 4, "callplate")
    d = ImageDraw.Draw(img)
    d.ellipse([11, 5, 20, 14], fill=rgb(0xF0E6C8), outline=rgb(0x6A4A10))
    d.ellipse([11, 18, 20, 27], fill=rgb(0xF0E6C8), outline=rgb(0x6A4A10))
    save(img, "callplate")
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
    wood = T.noise_fill(T.hexrgb(0x3A2014), 5, 546)
    for axis in ("ns", "we"):
        img = wood.copy()
        d = ImageDraw.Draw(img)
        if axis == "ns":
            d.rectangle([3, 0, 28, S - 1], fill=rgb(0x8A1C14))
            d.rectangle([5, 0, 6, S - 1], fill=rgb(0xC9A040))
            d.rectangle([25, 0, 26, S - 1], fill=rgb(0xC9A040))
        else:
            d.rectangle([0, 3, S - 1, 28], fill=rgb(0x8A1C14))
            d.rectangle([0, 5, S - 1, 6], fill=rgb(0xC9A040))
            d.rectangle([0, 25, S - 1, 26], fill=rgb(0xC9A040))
        save(img, f"runner-{axis}")
    img = noise(0x7A1A18, 5, "rug")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x1E2A4A), width=3)
    d.polygon([(16, 5), (27, 16), (16, 27), (5, 16)], fill=rgb(0x1E2A4A), outline=rgb(0xC9A040))
    d.polygon([(16, 10), (22, 16), (16, 22), (10, 16)], fill=rgb(0xC9A040))
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
    img = noise(0x5A2E1A, 4, "receptionmahogany")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, 2], fill=rgb(0xC9A040))
    d.rectangle([3, 6, 13, 28], outline=rgb(0xC9A040))
    d.rectangle([18, 6, 28, 28], outline=rgb(0xC9A040))
    save(img, "receptionmahogany")
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
    img = noise(0x1A1A1C, 12, "coal")
    rng = random.Random(77)
    for _ in range(30):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(0x4A4A50))
    save(img, "coal")


def generate():
    shared()
    level1()
    level3()
    level4()
    level5()
