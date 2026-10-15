"""Textures for Levels 6 to 10 and Level 6.1 (32x32, in block/detail/ and item/)."""
import math
import random

from PIL import Image, ImageDraw

import matlib as M
from detail_kit import T, seed_of
from detail_textures import S, block_wall, flat, grime, noise, rgb, save, stripes, text


def save_item(img, name):
    T.save(img, f"item/{name}.png")


def sprite():
    return Image.new("RGBA", (S, S), (0, 0, 0, 0))


def specks(img, colors, count, key):
    rng = random.Random(seed_of(key))
    for _ in range(count):
        img.putpixel((rng.randrange(S), rng.randrange(S)), rgb(rng.choice(colors)))
    return img


def chalk_stroke(d, pts, width=2):
    d.line(pts, fill=(236, 236, 228, 235), width=width)


# ---------------- Level 6 ----------------

def level6():
    level6_b9()  # (B9) the cold walls, floor, ceiling and standing water, and the dead switch's materials

    def chalk_decal(name, draw):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw(ImageDraw.Draw(img), img)
        if name.startswith("chalk"):
            chalky(img, seed_of(name))  # (B9) broken, dusty strokes
        save(img, name)

    chalk_decal("chalk-megexit", lambda d, img: (chalk_stroke(d, [4, 20, 26, 20]), chalk_stroke(d, [20, 14, 27, 20, 20, 26]),
                                                 chalk_text(img, "EXIT", 1, 4, 2)))
    chalk_decal("chalk-megcross", lambda d, img: (chalk_stroke(d, [6, 4, 26, 22], 3), chalk_stroke(d, [26, 4, 6, 22], 3),
                                                  chalk_text(img, "DEAD END", 2, 25, 1)))
    chalk_decal("chalk-meglogo", lambda d, img: (d.ellipse([3, 3, 28, 28], outline=(236, 236, 228, 235), width=2),
                                                 chalk_text(img, "MEG", 10, 13, 1)))  # (smaller: at 2 px a dot it ran into the ring)

    def hands(d, img):
        rng = random.Random(61)
        for (x, y) in ((6, 6), (18, 12), (9, 19)):
            d.ellipse([x, y + 4, x + 6, y + 11], fill=(26, 20, 18, 200))
            for k in range(4):
                d.line([x + 1 + k * 1.6, y + 4, x + rng.uniform(-1, 1) + k * 1.8, y], fill=(26, 20, 18, 200), width=1)
    chalk_decal("handprints", hands)

    def scratches(d, img):
        for k in range(6):
            d.line([6 + k * 3, 6, 5 + k * 3, 24], fill=(200, 200, 196, 210))
        d.line([4, 20, 25, 9], fill=(200, 200, 196, 210))
    chalk_decal("scratches", scratches)

    for name, draw in (("left", lambda d: (chalk_stroke(d, [27, 16, 5, 16], 3), chalk_stroke(d, [12, 8, 4, 16, 12, 24], 3))),
                       ("right", lambda d: (chalk_stroke(d, [5, 16, 27, 16], 3), chalk_stroke(d, [20, 8, 28, 16, 20, 24], 3))),
                       ("cross", lambda d: (chalk_stroke(d, [6, 6, 26, 26], 3), chalk_stroke(d, [26, 6, 6, 26], 3))),
                       ("circle", lambda d: d.ellipse([6, 6, 26, 26], outline=(236, 236, 228, 235), width=3))):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw(ImageDraw.Draw(img))
        save(chalky(img, seed_of("chalkmark-" + name)), f"chalkmark-{name}")
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(8, 26), (22, 6), (27, 10), (13, 29)], fill=(240, 238, 230, 255), outline=(170, 168, 160, 255))
    d.polygon([(8, 26), (13, 29), (10, 30), (6, 28)], fill=(200, 198, 190, 255))
    save_item(img, "chalk")


# ---------------- Level 6.1 ----------------

def level61():
    level61_b9()  # (B9) floors, walls, ceiling, skylight, and the fixtures' and machines' materials
    for part in ("lower", "upper"):
        img = noise(0x6A4A3A, 12, "rusty" + part)
        T.blotch(img, (10, 20), 9, (150, 80, 40), 0.6, 72)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x3A2A20), width=2)
        if part == "lower":
            d.rectangle([22, 0, 27, 3], fill=rgb(0x9A9488))
        else:
            d.rectangle([8, 10, 23, 14], fill=rgb(0xC8B060))
            text(img, "EXIT", (8, 9, 24, 15), 0x3A2A10, 5)
        save(img, f"rustydoor-{part}")
        img = Image.new("RGBA", (S, S), rgb(0x9AB8C0))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=2)
        d.line([4, 4, 12, 12] if part == "upper" else [18, 4, 26, 12], fill=rgb(0xE0F0F4), width=2)
        if part == "lower":
            d.rectangle([2, 0, 29, 2], fill=rgb(0x8A8E92))
        save(img, f"glassdoors-{part}")
        img = noise(0xC8C8C4, 3, "kitchendoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=2)
        if part == "upper":
            d.ellipse([9, 6, 22, 19], fill=rgb(0x2A3A42), outline=rgb(0x8A8E92), width=2)
        else:
            d.rectangle([4, 4, 27, 10], fill=rgb(0xA8ACB0))
        save(img, f"kitchendoor-{part}")
    img = Image.new("RGBA", (S, S), rgb(0x1A1C1E))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8E92), width=3)
    for y in range(6, S - 4, 4):
        d.line([4, y, S - 5, y], fill=rgb(0x6A6E72), width=2)
    save(img, "ventgrate")

    flat("navy", 0x1E2E5A, 4)
    flat("chrome", 0xC8CCD0, 3)
    flat("formica", 0xE8DCC8, 3)
    # The snack machine's dark inside behind the glass; its paint, header, glass, packets, spirals and panel are B9's
    # (machine_textures)
    save(noise(0x16191E, 3, "snackvendinside"), "snackvendinside")
    # The drinks fridge in 3D: cold white inside, and the cans and bottles: four 4-unit bands, one a column (its
    # enamel, header, grille and glass are B9's, machine_textures)
    save(noise(0xDCE8F0, 2, "fridgeinside"), "fridgeinside")
    img = Image.new("RGBA", (S, S), rgb(0x1A1E24))
    d = ImageDraw.Draw(img)
    for band, (c, label) in enumerate(((0xC81E1E, 0xF4F0E8), (0x2E9A3A, 0xF0E040), (0x7AB8E8, 0x2A5AA8), (0xF08A1E, 0xFFFFFF))):
        x0 = band * 8
        d.rectangle([x0, 0, x0 + 5, S - 1], fill=rgb(c))
        d.line([x0 + 1, 0, x0 + 1, S - 1], fill=T.shade(T.hexrgb(c), 1.3))  # the shine down a can
        for y in range(3, S, 8):
            d.rectangle([x0, y, x0 + 5, y + 2], fill=rgb(label))
        d.line([x0, 0, x0 + 5, 0], fill=rgb(0xB8BCC0))  # the lids
    save(img, "drinkcans")
    # A dead machine of a vending room's heap: its glass cracked (its paint and unlit sign are B9's)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for pts in (((20, 9), (13, 3), (9, 0)), ((20, 9), (27, 4)), ((20, 9), (24, 20), (22, 31)), ((20, 9), (8, 14), (0, 15))):
        d.line(pts, fill=(226, 232, 236, 210))  # cracks spreading from a blow
    d.line([4, S - 1, 12, 18], fill=(214, 230, 240, 150))
    save(img, "vendpileglass")
    for name, word, color in (("signburger", "BURGERS", 0xFF4060), ("signpizza", "PIZZA", 0x40FF90), ("signtaco", "TACOS", 0xFFC040), ("signdonut", "DONUTS", 0x60C0FF)):
        img = Image.new("RGBA", (S, S), rgb(0x141018))
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(color), width=1)
        text(img, word, (1, 8, 31, 24), color, 8)
        save(img, name)
    img = Image.new("RGBA", (S, S), rgb(0x1A1A1A))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A6A3A), width=2)
    for y, w in ((5, 16), (10, 20), (15, 14), (20, 18), (25, 12)):
        d.line([4, y, 4 + w, y], fill=rgb(0xF0F0E8))
        d.line([26, y, 28, y], fill=rgb(0xF0C040))
    save(img, "menuboard")
    img = noise(0xF4F0E8, 2, "mallmap")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    d.rectangle([12, 4, 19, 27], fill=rgb(0xC8E8E4))
    d.rectangle([4, 12, 27, 19], fill=rgb(0xC8E8E4))
    for x, y, c in ((5, 5, 0xE88AA0), (21, 5, 0xF0C040), (5, 21, 0x7AC8C0), (21, 21, 0xA080D0)):
        d.rectangle([x, y, x + 5, y + 5], fill=rgb(c))
    d.ellipse([14, 14, 17, 17], fill=rgb(0xD82020))
    save(img, "mallmap")

    # Food: snacks and drinks
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(7, 5), (25, 5), (27, 27), (5, 27)], fill=rgb(0xE8C020), outline=rgb(0xA08010))
    d.rectangle([7, 12, 25, 20], fill=rgb(0xD82020))
    text(img, "CHIPS", (7, 12, 26, 21), 0xF4F0E0, 5)
    save_item(img, "chips")
    img = sprite()
    d = ImageDraw.Draw(img)
    d.polygon([(4, 18), (24, 6), (28, 12), (8, 24)], fill=rgb(0x5A2A14), outline=rgb(0x2A1408))
    d.polygon([(10, 16), (20, 10), (23, 14), (13, 20)], fill=rgb(0xE8C040))
    save_item(img, "candybar")
    img = sprite()
    d = ImageDraw.Draw(img)
    d.rectangle([10, 6, 21, 27], fill=rgb(0xC82020), outline=rgb(0x801010))
    d.rectangle([10, 6, 21, 8], fill=rgb(0xC8CCD0))
    d.line([12, 14, 19, 18], fill=rgb(0xF4F0E8), width=2)
    save_item(img, "soda")
    for name, liquid in (("cashewwater", 0xE8D8B0), ("waterbottle", 0xB8D8F0)):
        img = sprite()
        d = ImageDraw.Draw(img)
        d.rectangle([13, 3, 18, 7], fill=rgb(0x3A6AB0 if name == "waterbottle" else 0x8A5A2A))
        d.polygon([(11, 8), (20, 8), (22, 12), (22, 28), (9, 28), (9, 12)], fill=rgb(liquid, 220), outline=rgb(0x8A9AA8))
        d.rectangle([9, 15, 22, 21], fill=rgb(0xF4F0E8))
        save_item(img, name)


# ---------------- Graphics pass B9: Levels 6 and 6.1 ----------------
#
# Level 6's cold walls, floor and ceiling and its dead switch, chalk that reads as chalk; the Snackrooms' floors, walls,
# ceiling and skylight, and the materials of its fixtures (whose shapes are in gen_deep.level61). Each surface keeps the
# mean colour of the texture it replaces (B9_MEAN, measured on main before B9), so the levels keep their tones: Level 6
# black, the food court its mint, pink, cream and navy (the diner palette is a lore decision, docs/design/visual-review.md).

B9_MEAN = {"l6wall": (57.6, 60.6, 65.6), "l6floor": (44.0, 46.0, 50.0), "l6ceiling": (48.0, 50.0, 54.0),
           "l6floor-wet": (30.7, 32.9, 37.0), "terrazzo": (227.6, 213.4, 198.4), "checker": (134.0, 134.0, 134.0),
           "quarry": (160.5, 64.8, 43.8), "mall": (143.0, 193.3, 186.8), "panel": (134.0, 87.0, 50.0),
           "tile": (232.1, 232.1, 228.1), "window": (235.6, 218.5, 191.7), "grid": (229.9, 229.9, 225.9),
           "navy": (30.1, 46.1, 90.1), "chrome": (200.1, 204.1, 208.1), "formica": (232.0, 220.0, 200.0),
           "stove": (154.0, 158.0, 162.0), "vending": (42.1, 106.1, 176.1), "fridge": (229.9, 231.9, 233.9),
           "vendpile": (137.2, 44.3, 38.2)}
L6_WALL = (58, 61, 66)
CHALK = (236, 236, 228)
CHALK_DUST = (198, 198, 194)  # thin chalk: the same white, greyer


def b9_match(img, key, versions=None):
    """img shifted to the old texture's mean colour; with `versions` (a name shared by the versions of one surface)
    the shift is worked out once and reused, so the versions keep one ground (T.match_rgb)."""
    return T.match_rgb(img, B9_MEAN[key], versions)


def b9_save(img, name):
    """Saves a B9 texture: block textures in block/detail/, as every Level 6 and 6.1 texture is."""
    save(img, name)


def keep_inside(plain, featured, band=5):
    return T.inside_block(plain, featured, band)


# ---- Level 6 ----

def l6_panel_shade(img, joints=(0, 16)):
    """The cold material's cast panels: a groove at each joint (dark, a lit lip under it) and a faint polish that is
    lightest just under each joint and fades down the panel, so the panels read under a lantern."""
    w, h = img.size
    span = h // len(joints)
    for y in range(h):
        k = (y - joints[0]) % span / span
        for x in range(w):
            M.touch(img, x, y, 0.035 * (1 - k) - 0.012, 0.1)
    M.emboss_lines(img, ys=joints, strength=0.16)
    return img


def l6_floor_joints(img, strength=0.04):
    """The floor's cast slabs, one to the block: a soft 2 px groove at the block's edges (31-0), symmetric about the
    block centre so a block turned any way keeps it in place (B8's lesson on turned floors). (Joints at 15-16 too read
    as a heavy grid under a lantern.)"""
    for k in (31, 0):
        for t in range(S):
            M.touch(img, k, t, -strength, 0.08)
            M.touch(img, t, k, -strength, 0.08)
    return img


def l6_ground(seed, base):
    """The smooth, cold material itself: almost no grain, a slow mottle, the odd pin-hole; held to a cold grey hue."""
    img = M.concrete(seed, base=base, grain=2, mottle=2, aggregate=0.0, pores=0.0, hue=0.5, drift=0.08)
    return T.calm_hue(img, base, 0.6)


def l6_wall(version):
    """Level 6's wall: two smooth panels to the block, one above the other (the old joints at 0 and 16). Every
    version is the same panel; the second has a faint damp run down from a joint, the third a hairline crack; each is
    listed one block in eight (gen_detail ALTS)."""
    img = l6_ground(6100, L6_WALL)
    rng = random.Random(6101)
    for _ in range(5):  # the odd pin-hole in the cast face
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, -0.1)
        M.touch(img, x, y + 1, 0.05)
    l6_panel_shade(img)
    if version == 2:
        run = img.copy()
        M.drips(run, 2, 6102, color=(36, 40, 44), length=(8, 13), strength=0.32, start=17)
        img = keep_inside(img, run, 3)
    elif version == 3:
        cr = img.copy()
        M.crack(cr, 6103, at=(20, 7), length=(9, 13), strength=0.22)
        img = keep_inside(img, cr, 3)
    return b9_match(img, "l6wall", "b9l6wall")


def l6_floor(version):
    """Level 6's floor: the same cold material in cast slabs, one to the block (l6_floor_joints), turned at random and
    seamless (matlib.turn_safe): three versions on one ground, each with a few pin-holes, the third with a faint
    scuff, kept inside the block."""
    base = (44, 46, 50)
    ground = l6_ground(6110, base)
    img = ground.copy()
    rng = random.Random(6111 + version)
    for _ in range(2 + 2 * version):
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, -0.1)
        M.touch(img, x, y + 1, 0.04)
    if version == 3:
        sc = img.copy()
        M.scratches(sc, 3, 6114, length=(3, 6), light=0.14)
        img = keep_inside(img, sc, 5)
    img = l6_floor_joints(M.turn_safe(img, ground, keep=0.5))
    return b9_match(img, "l6floor", "b9l6floor")


def l6_ceiling(version):
    """Level 6's ceiling: the cold material in cast slabs, one to the block (a faint joint at its edges); the second
    version has a faint damp mark, listed one block in six."""
    img = l6_ground(6120, (48, 50, 54))
    M.emboss_lines(img, xs=(0,), ys=(0,), strength=0.08)
    if version == 2:
        st = img.copy()
        M.stain(st, 6121, radius=6, color=(34, 36, 38), strength=0.4, at=(22, 10), ring=0.6)
        img = keep_inside(img, st, 3)
    return b9_match(img, "l6ceiling", "b9l6ceil")


def l6_wet(version=1):
    """Standing water on the cold floor: the floor's material, darker and bluer under a film of water (all over the
    block, or a turned block shows its square), with a few long glints where the film catches a light (as the old one
    had), kept off the block's edge so turned blocks meet."""
    base = (30, 33, 37)
    ground = l6_ground(6130, base)
    gp = ground.load()
    for y in range(S):
        for x in range(S):
            gp[x, y] = M.rgba(M.hue_shift(gp[x, y], -1.5))
    img = ground.copy()
    film = img.copy()
    # (round 2) a few soft, irregular patches where the film catches a light, each with a short bright glint, placed
    # by the version (the old dashes sat in the same place in every block and read as road markings)
    rng = random.Random(6132 + version)
    fp = film.load()
    for _ in range(3):
        cx, cy, r = rng.uniform(8, 24), rng.uniform(8, 24), rng.uniform(3, 6)
        wob = M.fbm((S, S), rng.randrange(1 << 16), (8, 4))
        for y in range(S):
            for x in range(S):
                dd = math.hypot((x - cx) / 1.6, y - cy) / r + wob[y][x] * 0.35
                if dd < 1:
                    fp[x, y] = M.rgba(M.lift(M.hue_shift(fp[x, y], -1), 7 * (1 - dd) ** 0.7, 0.05))
        gx, gy = int(cx - r * 0.5), int(cy - r * 0.3)
        for k in range(rng.randint(2, 4)):
            fp[gx + k, gy] = M.rgba((62, 68, 76))
    img = keep_inside(img, film, 4)
    img = l6_floor_joints(M.turn_safe(img, ground, keep=0.5), 0.06)
    return b9_match(img, "l6floor-wet", "b9l6wet")


def l6_switch():
    """The dead light switch's materials (its plate, screws and toggle are geometry, gen_deep.level6): yellowed old
    bakelite with a faint grime of hands, the toggle a little paler, the slot dark."""
    plate = M.noise_hv((214, 204, 178), 2, 6140, mottle=4, cells=(8, 4), hue=1.0)
    M.grime(plate, 0.18, 6141, color=(120, 104, 80), cells=(4, 2), cover=0.45)
    b9_save(plate, "l6switchplate")
    toggle = M.noise_hv((226, 218, 194), 2, 6142, mottle=3, cells=(8, 4), hue=1.0)
    M.grime(toggle, 0.12, 6143, color=(120, 104, 80), cells=(4, 2), cover=0.4)
    b9_save(toggle, "l6switchtoggle")
    b9_save(M.noise_hv((34, 30, 28), 2, 6144, mottle=2), "l6switchslot")


CHALK_FONT = {"D": ("110", "101", "101", "101", "110"), "E": ("111", "100", "110", "100", "111"),
              "A": ("010", "101", "111", "101", "101"), "N": ("101", "111", "111", "111", "101"),
              "X": ("101", "101", "010", "101", "101"), "I": ("111", "010", "010", "010", "111"),
              "T": ("111", "010", "010", "010", "010"), "M": ("101", "111", "111", "101", "101"),
              "G": ("011", "100", "101", "101", "011")}


def chalk_text(img, word, x, y, scale):
    """(B9 round 2) Chalked capitals, 3 x 5 at `scale` px a dot, crisp: the old lettering was text scaled down, which
    the chalk's break-up (chalky) left unreadable. A space is two dots wide; a full stop is one dot at the foot, in the
    gap after a letter."""
    p = img.load()
    for ch in word:
        if ch == " ":
            x += 2 * scale
            continue
        if ch == ".":
            if x - scale >= 0 and x <= img.width:  # (a full stop past the edge is left off)
                for dy in range(scale):
                    for dx in range(scale):
                        p[x - scale + dx, y + 4 * scale + dy] = (236, 236, 228, 235)
            continue
        for r, row in enumerate(CHALK_FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            p[x + c * scale + dx, y + r * scale + dy] = (236, 236, 228, 235)
        x += 4 * scale if word.count(".") == 0 else 5 * scale
    return img


def chalky(img, seed, dust=CHALK_DUST):
    """Chalk on a smooth wall: the strokes break up (a few pixels skipped, more at the edges, where the stick drags),
    and each pixel is its own mix of chalk and a thinner, white-grey dust. The block is drawn in the opaque pass, which
    cuts out alpha under a half, so the dust is a colour rather than an alpha. It is neutral (no wall colour in it), so
    chalk a player draws on any level's walls stays clean."""
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    solid = [[px[x, y][3] >= 90 for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            if not solid[y][x]:
                px[x, y] = (0, 0, 0, 0)
                continue
            near = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                       if 0 <= x + dx < w and 0 <= y + dy < h and solid[y + dy][x + dx])
            edge = near < 4
            # (round 2) only thick strokes break up: lettering and 1-2 px lines lost their shape (EXIT, DEAD END)
            if near >= 3 and rng.random() < (0.14 if edge else 0.04):
                px[x, y] = (0, 0, 0, 0)
                continue
            c = px[x, y][:3]
            if c[0] > 150:  # chalk (the dark handprints keep their colour)
                c = M.mix(CHALK, dust, rng.uniform(0.0, 0.45) + (0.25 if edge else 0.0))
                c = M.lift(c, rng.uniform(-4, 4), 0.05)
            px[x, y] = M.rgba(c, max(px[x, y][3], 160))
    return img


# ---- Level 6.1: surfaces ----

TERRAZZO = (230, 216, 200)
TERRAZZO_CHIPS = ((232, 138, 160), (122, 200, 192), (154, 140, 124), (244, 240, 232))


def terrazzo(version):
    """The food court's terrazzo: a polished cream matrix (marble dust in it) set with chips of 1 to 3 px in the old
    four colours (pink, teal, taupe and white; the old floor had single specks), each chip its own shade with a
    glint on the larger ones. Three versions, each its own scatter of chips on one ground, turned at random and
    seamless (matlib.turn_safe); about as many chip pixels as the old floor had specks."""
    ground = M.noise_hv(TERRAZZO, 2, 6200, mottle=3, cells=(16, 8), hue=0.8)
    img = ground.copy()
    p = img.load()
    rng = random.Random(6201 + version)
    for _ in range(70):  # marble dust in the matrix
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((-0.04, 0.03)))
    placed = 0
    shapes = {1: [[(0, 0)]], 2: [[(0, 0), (1, 0)], [(0, 0), (0, 1)], [(0, 0), (1, 1)]],
              3: [[(0, 0), (1, 0), (0, 1)], [(0, 0), (1, 0), (1, 1), (0, 1)], [(1, 0), (0, 1), (1, 1), (2, 1)],
                  [(0, 0), (1, 0), (1, 1), (2, 1)], [(0, 0), (0, 1), (1, 1)]]}
    while placed < 80:
        size = rng.choices((1, 2, 3), (0.72, 0.26, 0.02))[0]  # (round 2: mostly fine; larger ones read as squares)
        cells = rng.choice(shapes[size])
        fx, fy, tr = rng.choice((1, -1)), rng.choice((1, -1)), rng.random() < 0.5  # each chip turned its own way
        cells = [((dy if tr else dx) * fx, (dx if tr else dy) * fy) for (dx, dy) in cells]
        col = rng.choices(TERRAZZO_CHIPS, (1.0, 1.0, 0.6, 1.0))[0]
        v, hu = rng.uniform(-8, 6), rng.uniform(-3, 3)
        x0, y0 = rng.randrange(S), rng.randrange(S)
        for (dx, dy) in cells:
            M.put(p, S, S, x0 + dx, y0 + dy, M.hue_shift(M.lift(col, v + rng.uniform(-3, 3)), hu))
        if size > 1:
            M.touch(img, x0 + cells[0][0], y0 + cells[0][1], 0.08)  # the polish catching the light
        placed += len(cells)
    img = M.turn_safe(img, ground, keep=0.3)
    return b9_match(img, "terrazzo", "b9terrazzo")


CHECK_WHITE, CHECK_BLACK = (234, 232, 224), (36, 36, 40)


def checker(version):
    """The chequered floor: 8 px vinyl tiles as before, off-white and charcoal now (no pure black and white), each tile
    its own shade, a lit top and left edge, a fine dark joint at its bottom and right, wax gathered toward the edges.
    The second version has a faint heel mark, the third a chipped corner; each is listed one block in eight. Not
    turned: a quarter turn would swap the colours."""
    img = Image.new("RGBA", (S, S))
    rng = random.Random(6210)  # one tile layout for every version, so versions differ only in their features
    p = img.load()
    for j in range(4):
        for i in range(4):
            white = (i + j) % 2 == 0
            col = CHECK_WHITE if white else CHECK_BLACK
            v = rng.uniform(-2.5, 2.5) if white else rng.uniform(-1, 1)  # (a tile's own shade repeats block to block:
            hu = rng.uniform(-1, 1) if white else rng.uniform(-0.4, 0.4)  # kept small, most of all on the charcoal)
            for yy in range(8):
                for xx in range(8):
                    c = M.hue_shift(M.lift(col, v + rng.uniform(-2, 2), 0.1), hu)
                    p[i * 8 + xx, j * 8 + yy] = M.rgba(c)
            box = (i * 8, j * 8, i * 8 + 8, j * 8 + 8)
            M.ao_border(img, 2, 0.04 if white else 0.0, box)
            for k in range(8):
                M.touch(img, i * 8 + k, j * 8, 0.05 if white else 0.12, 0.1)
                M.touch(img, i * 8, j * 8 + k, 0.03 if white else 0.08, 0.1)
                M.touch(img, i * 8 + k, j * 8 + 7, -0.1 if white else -0.05, 0.1)
                M.touch(img, i * 8 + 7, j * 8 + k, -0.07 if white else -0.04, 0.1)
    if version == 2:
        f = img.copy()
        d = ImageDraw.Draw(f)
        for (x, y, x2, y2) in ((9, 18, 12, 17),):
            d.line([x, y, x2, y2], fill=(212, 208, 198, 255))
        img = keep_inside(img, f, 3)
    elif version == 3:
        f = img.copy()
        for (x, y) in ((23, 8), (24, 8), (23, 9)):  # a chipped corner on a charcoal tile, the pale backing showing
            f.load()[x, y] = M.rgba((96, 94, 90))
        img = keep_inside(img, f, 3)
    return b9_match(img, "checker", "b9checker")


def quarry(version):
    """The restaurants' quarry tiles: four unglazed 16 px tiles to the block in the old dark grout, each its own shade
    and hue with a speckled body, a slight tilt and a lit edge; three versions (other shades)."""
    img = M.tile(6220 + version, base=(166, 68, 46), grout=(104, 42, 28), pitch=16, grout_w=1, jitter=9, uneven=5,
                 glaze=False, speckle=0.6)
    return b9_match(img, "quarry", "b9quarry")


MINT, PINK, CREAM = (126, 200, 190), (232, 138, 160), (244, 232, 208)


def mall_wall():
    """The mall wall: mint paint on plaster (a roller stipple, soft clouds) with the old pink band and cream pinstripe
    painted across it, clean edged so the bands run on from block to block. One version: a smudge in a second one read
    as a column of marks on a sheet, since the wall's rows repeat the block one above the other."""
    img = M.plaster(6230, base=MINT, grain=2, mottle=5, roller=0.6, bumps=0.004)
    p = img.load()
    lm = M.lum(MINT)
    for y in range(S):
        for x in range(S):
            rel = M.lum(p[x, y]) - lm
            if 18 <= y <= 21:
                c = M.lift(PINK, rel * 0.8 + (1.5 if y == 18 else -1.5 if y == 21 else 0))
            elif y == 23:
                c = M.lift(CREAM, rel * 0.6)
            else:
                continue
            p[x, y] = M.rgba(c)
    return b9_match(img, "mall")


def wood_panel():
    """The restaurants' wood panelling: four upright boards of 8 px to the block (the old grooves), grained, each its own
    shade, a dark groove between them."""
    img = M.wood_planks(6240, base=(140, 92, 54), planks=4, direction="v", grain=2, contrast=0.45, knots=0, joints=0,
                        flecks=0.3, per_plank=6, gap=(92, 56, 30))
    return b9_match(img, "panel")


def tiled_wall():
    """White glazed wall tiles, 8 px, in pale grout (the pattern is defined but no layout places it)."""
    img = M.tile(6250, base=(240, 240, 236), grout=(196, 196, 190), pitch=8, jitter=3, uneven=3, glaze=True)
    return b9_match(img, "tile")


def shop_window():
    """A shop window that glows like daylight: two frosted panes, brightest in the middle, in a brushed aluminium frame
    with a lit top edge and a centre mullion. The block stays a cube with its old light; no dark gap round the panes."""
    frame = M.brushed_metal(6260, base=(190, 186, 178), grain=2, streak=5, sheen=5)
    img = frame.copy()
    p = img.load()
    glow, warm = (255, 248, 232), (255, 228, 190)
    rng = random.Random(6261)
    for (x0, x1) in ((2, 15), (17, 30)):
        for y in range(2, 30):
            for x in range(x0, x1):
                u = (x - x0 + 0.5) / (x1 - x0) * 2 - 1
                v = (y - 1.5) / 28 * 2 - 1
                t = max(0.0, 1 - (u * u * 0.7 + v * v * 0.9))
                c = M.mix(warm, glow, t)
                p[x, y] = M.rgba(M.lift(c, rng.uniform(-1.5, 1.5) - 2 * (1 - t), 0.05))
    M.bevel(img, (0, 0, S, S), 1, 0.12)
    for (x0, x1) in ((2, 15), (17, 30)):
        for x in range(x0, x1):
            M.touch(img, x, 2, -0.03, 0.05)
    return b9_match(img, "window")


SNACK_TILE, SNACK_RAIL = (238, 238, 234), (184, 184, 180)


def snack_ceiling(version):
    """The food court's drop ceiling, two 32 x 16 tiles to the block as before: Level 0's lay-in tile (matlib.ceiling_tile)
    in the old light grey and grid. Three versions (other fissures)."""
    img = Image.new("RGBA", (S, S))
    for half in (0, 1):
        tile = M.ceiling_tile(6270 + version * 2 + half, size=(S, S // 2), base=SNACK_TILE, rail=SNACK_RAIL,
                              fissures=0.5, recess=2)
        img.paste(tile, (0, half * S // 2))
    T.calm_hue(img, SNACK_TILE, 0.6)
    return b9_match(img, "grid", "b9grid")


def skylight():
    """A skylight in the grid that shows only darkness, though light comes from it: the grid rail at its edge (shared
    with the tiles round it), a glowing diffuser rim, the light catching the aluminium curb inside it, then four panes
    of night-black glass between mullions. The panes are deepest at their middle, with a faint sheen across the glass
    and the rim's warm light reflected along their outer edges; the mullions are lit on the side toward the rim. The
    block stays a cube with its old light (graphics pass lesson: a shaped light loses its glow)."""
    img = Image.new("RGBA", (S, S))
    p = img.load()
    rng = random.Random(6280)
    rim, rim2, curb = (255, 236, 204), (244, 214, 170), (206, 170, 124)
    for y in range(S):
        for x in range(S):
            e = min(x, y, S - 1 - x, S - 1 - y)
            if e == 0:
                c = M.lift(SNACK_RAIL, 10 if (x == 0 or y == 0) else 0)
            elif e <= 2:
                c = M.mix(rim, rim2, (e - 1) * 0.6)
            elif e == 3:
                c = curb
            else:
                qx, qy = (x - 4) % 12 if x < 16 else (x - 17) % 12, (y - 4) % 12 if y < 16 else (y - 17) % 12
                if x in (15, 16) or y in (15, 16):
                    lit = (x == 15 and y not in (15, 16)) or (y == 15 and x not in (15, 16))
                    c = (96, 88, 78) if lit else (66, 62, 58)
                else:
                    d = min(qx, qy, 11 - qx, 11 - qy) / 5.5
                    t = ((x % 16) + (y % 16)) / 30.0
                    c = (12 + 5 * t + 4 * (1 - d), 14 + 6 * t + 4 * (1 - d), 21 + 9 * t + 3 * (1 - d))  # (night glass)
                    if abs((x % 16) - (y % 16) - 3) <= 1:
                        c = M.lift(c, 8, 0.05)  # the sheen on the glass
                    if e == 4:
                        c = M.mix(c, (60, 48, 36), 0.5)  # the rim's light reflected in the pane's edge
            p[x, y] = M.rgba(M.lift(c, rng.uniform(-1, 1), 0.05))
    return img


# ---- Level 6.1: the fixtures' materials ----

def snack_materials():
    """The Snackrooms furniture's materials (the old ones were flat colours): polished chrome with its reflections,
    navy vinyl upholstery with a pebble grain and a soft shine, a navy laminate table top with a fleck, the counters'
    cream laminate and brushed stainless, a black rubber kick, and the stainless of the griddle and fryer. Each keeps
    the old mean colour of what it replaces."""
    img = M.brushed_metal(6300, base=(198, 202, 208), grain=3, direction="v", streak=6, sheen=18)
    b9_save(b9_match(img, "chrome"), "snackchrome")

    img = M.noise_hv((30, 46, 90), 2, 6302, mottle=4, cells=(16, 8), hue=1.0)
    peb = M.fbm((S, S), 6303, (2, 1), 0.6)
    shine = M.value_noise((S, S), 16, 6304)
    p = img.load()
    for y in range(S):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(p[x, y], peb[y][x] * 3 + max(0.0, shine[y][x]) * 7, 0.1))
    b9_save(b9_match(img, "navy"), "snackvinyl")

    img = M.noise_hv((32, 48, 92), 2, 6305, mottle=3, cells=(16, 8), hue=1.0)
    rng = random.Random(6306)
    for _ in range(90):  # the laminate's fleck: small, many, close to the ground
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((0.18, 0.12, -0.12)), 0.05)
    b9_save(b9_match(img, "navy"), "snacktabletop")

    img = M.noise_hv((232, 220, 200), 2, 6307, mottle=3, cells=(16, 8), hue=1.0)
    rng = random.Random(6308)
    for _ in range(30):
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((-0.08, -0.05, 0.04)))
    b9_save(b9_match(img, "formica"), "counterfront")

    b9_save(b9_match(M.brushed_metal(6309, base=(198, 202, 206), grain=3, streak=6, sheen=8), "chrome"), "snackcountertop")
    b9_save(b9_match(M.brushed_metal(6310, base=(154, 158, 162), grain=3, streak=7, sheen=8), "stove"), "stovesteel")
    b9_save(M.rubber(6311, base=(40, 38, 40)), "snackkick")


def b9_font(img, s, x, y, colour):
    """A 3 x 5 pixel font for the tiny print of price tags and displays, drawn crisp (no antialiasing)."""
    glyphs = {"0": ("111", "101", "101", "101", "111"), "1": ("010", "110", "010", "010", "111"),
              "2": ("111", "001", "111", "100", "111"), "3": ("111", "001", "011", "001", "111"),
              "4": ("101", "101", "111", "001", "001"), "5": ("111", "100", "111", "001", "111"),
              "6": ("111", "100", "111", "101", "111"), "7": ("111", "001", "010", "010", "010"),
              "8": ("111", "101", "111", "101", "111"), "9": ("111", "101", "111", "001", "111"),
              "$": ("111", "110", "111", "011", "111"), ".": ("000", "000", "000", "000", "010")}
    p = img.load()
    for ch in s:
        g = glyphs[ch]
        wdt = 1 if ch == "." else 3
        for r, row in enumerate(g):
            for c, bit in enumerate(row[:3] if wdt == 3 else row[1:2]):
                if bit == "1" and 0 <= x + c < img.width and 0 <= y + r < img.height:
                    p[x + c, y + r] = M.rgba(colour)
        x += wdt + 1


def fixture_textures():
    """The fixtures' other parts: the cash register's charcoal body, green display and pale keys; the food case's
    glass, deck and pastries; the griddle plate, burner grates and caps, knobs and oven window; the fryer's oil and
    basket mesh; the shelving's paint, pegboard, price strip and the packets on it."""
    b9_save(M.noise_hv((44, 48, 54), 2, 6320, mottle=3, cells=(16, 8), hue=1.0), "registerbody")
    img = M.noise_hv((12, 30, 16), 1, 6321, mottle=2)
    b9_font(img, "$0.00", 2, 2, (110, 244, 130))
    b9_font(img, "$1.25", 2, 18, (110, 244, 130))
    b9_save(img, "registerdisp")
    key = M.noise_hv((210, 206, 194), 2, 6322, mottle=2)
    b9_save(key, "snackkey")

    b9_save(glints(((3, 8, 7, 2), (5, 9, 6, 7), (14, 9, 18, 3), (24, 8, 26, 5), (8, 30, 12, 24), (22, 28, 25, 23)), frost_top=True),
            "caseglass")  # (its top row is the pane's edge catching the light)
    b9_save(M.noise_hv((226, 224, 216), 2, 6323, mottle=3), "caseinside")

    # Pastries, one 8 px band each, the top seen from above in the band's first 8 rows, the side in the next 8:
    # pink-iced and chocolate doughnuts, a croissant, a blueberry muffin in its paper case
    img = Image.new("RGBA", (S, S), M.rgba((200, 150, 90)))
    p = img.load()
    rng = random.Random(6324)
    dough = (204, 150, 86)
    for b, icing in enumerate(((232, 140, 170), (96, 58, 38))):
        x0 = b * 8
        for y in range(8):
            for x in range(8):
                r = math.hypot(x - 3.5, y - 3.5)
                c = icing if r < 3.6 else dough
                if r < 1.1:
                    c = (120, 86, 52)  # the hole
                p[x0 + x, y] = M.rgba(M.lift(c, rng.uniform(-4, 4) + (5 if x + y < 6 else 0)))
            for x in range(8):
                p[x0 + x, 8 + y] = M.rgba(M.lift(icing if y < 3 else dough, rng.uniform(-4, 4) + (-8 if y == 7 else 0)))
        for _ in range(7 if b == 0 else 3):  # sprinkles
            x, y = rng.randrange(1, 7), rng.randrange(1, 7)
            if math.hypot(x - 3.5, y - 3.5) > 1.4:
                p[x0 + x, y] = M.rgba(rng.choice(((250, 240, 120), (110, 200, 230), (250, 250, 240), (120, 210, 120))))
    x0 = 16
    for y in range(16):
        for x in range(8):
            ridge = (x + (y // 2)) % 3 == 0
            p[x0 + x, y] = M.rgba(M.lift((214, 152, 70), (-16 if ridge else 4) + rng.uniform(-4, 4) + (8 if y < 2 else 0)))
    x0 = 24
    for y in range(8):
        for x in range(8):
            p[x0 + x, y] = M.rgba(M.lift((168, 112, 64), rng.uniform(-8, 8)))
    for _ in range(6):
        p[x0 + rng.randrange(8), rng.randrange(8)] = M.rgba((62, 52, 96))
    for y in range(8, 16):
        for x in range(8):
            c = (168, 112, 64) if y < 11 else M.lift((232, 222, 204), -8 if x % 2 else 4)
            p[x0 + x, y] = M.rgba(M.lift(c, rng.uniform(-3, 3)))
    b9_save(img, "pastries")

    plate = M.brushed_metal(6325, base=(60, 56, 52), grain=3, streak=6, sheen=6)
    M.grime(plate, 0.2, 6326, color=(30, 24, 18), cells=(8, 4), cover=0.5)
    b9_save(plate, "griddleplate")
    b9_save(M.noise_hv((46, 44, 42), 4, 6327, mottle=3), "burnergrate")
    b9_save(M.noise_hv((30, 30, 32), 2, 6328, mottle=2), "stoveknob")
    img = M.noise_hv((22, 24, 28), 1, 6329, mottle=2)
    ImageDraw.Draw(img).line([4, 14, 12, 4], fill=(70, 74, 80, 255))
    b9_save(img, "ovenwindow")

    img = M.noise_hv((188, 146, 64), 3, 6330, mottle=6, cells=(8, 4), hue=2.0)
    rng = random.Random(6331)
    for _ in range(14):  # bubbles and glints on the oil
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, 0.22, 0.05)
        M.touch(img, x, y + 1, -0.08)
    b9_save(img, "fryeroil")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))  # wire mesh, a 2 px pitch, cut out between the wires
    p = img.load()
    for y in range(S):
        for x in range(S):
            if x % 2 == 0 or y % 2 == 0:
                p[x, y] = M.rgba(M.lift((150, 152, 154), 10 if y % 2 == 0 and x % 2 else -6 if x % 2 == 0 and y % 2 else 0))
    b9_save(img, "fryerbasket")

    b9_save(M.painted_metal(6332, base=(200, 200, 196), grain=2, mottle=3, panel=False, chips=0), "shelfmetal")
    img = M.painted_metal(6333, base=(184, 180, 170), grain=2, mottle=3, panel=False, chips=0)
    for y in range(1, S, 4):
        for x in range(1, S, 4):
            img.load()[x, y] = M.rgba((70, 68, 64))
            M.touch(img, x, y + 1, 0.06)
    b9_save(img, "shelfpegboard")
    img = M.noise_hv((232, 232, 226), 1, 6334, mottle=2)
    p = img.load()
    for x in range(S):
        p[x, 0] = M.rgba((250, 250, 246))
        p[x, 3] = M.rgba((176, 176, 170))
    for k, x in enumerate(range(1, S, 8)):
        for yy in (1, 2):
            for xx in range(x, x + 6):
                p[xx, yy] = M.rgba((240, 226, 140) if k % 2 else (250, 250, 246))
        for xx in (x + 1, x + 2, x + 4):
            p[xx, 2] = M.rgba((120, 118, 112))
    b9_save(img, "pricestrip")
    # (round 2) three arrangements of the packs, given to the shelf as texture alternates, so the shelves of a store
    # do not repeat one sequence block after block
    for v, order in enumerate(((0, 1, 2, 3, 4, 5, 6, 7), (2, 3, 0, 1, 6, 7, 4, 5), (1, 0, 3, 2, 5, 4, 7, 6))):
        b9_save(snack_packs(order), "snackpacks" + ("" if v == 0 else f"-{v + 1}"))


PACKS = (((210, 40, 36), (240, 196, 40)), ((40, 90, 200), (236, 236, 228)), ((236, 176, 40), (210, 60, 30)),
         ((48, 150, 66), (240, 236, 210)), ((226, 110, 32), (250, 246, 236)), ((36, 52, 110), (170, 116, 66)),
         ((150, 60, 176), (246, 210, 70)), ((232, 228, 214), (200, 40, 40)))


def snack_packs(order=tuple(range(8))):
    """The goods on the shelves, eight packs to an atlas, each a 4 x 8 unit (8 x 16 px) cell: four bags of chips with
    crimped ends and an oval logo, a box of crackers, a box of cookies, a box of candy and a box of rice cakes. The
    shelf's products are boxes whose faces take a cell (gen_deep.snack_shelf), so the packs stand as geometry."""
    img = Image.new("RGBA", (S, S))
    p = img.load()
    rng = random.Random(6340)
    for cell, i in enumerate(order):
        body, logo = PACKS[i]
        x0, y0 = (cell % 4) * 8, (cell // 4) * 16
        bag = i < 4
        for y in range(16):
            for x in range(8):
                c = body
                if bag and (y in (0, 15) or y in (1, 14) and x % 2 == 0):
                    c = M.lift(body, 26)  # the crimped seal
                elif bag:
                    c = M.lift(body, 10 if x in (1, 2) else -10 if x == 7 else 0)  # the crinkle catching the light
                else:
                    c = M.lift(body, 8 if y == 0 else -10 if x == 7 else 0)
                p[x0 + x, y0 + y] = M.rgba(M.lift(c, rng.uniform(-2, 2)))
        if bag:
            for y in range(5, 10):
                for x in range(1, 7):
                    if ((x - 3.5) / 3.0) ** 2 + ((y - 7) / 2.4) ** 2 <= 1:
                        p[x0 + x, y0 + y] = M.rgba(logo)
            for x in (2, 3, 4, 5):
                p[x0 + x, y0 + 7] = M.rgba(M.lift(body, -30))  # the brand name
        elif i == 5:
            for (cx, cy) in ((2, 9), (5, 11), (3, 13)):
                for (dx, dy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                    p[x0 + cx + dx, y0 + cy + dy] = M.rgba(logo)
            for x in range(1, 7):
                p[x0 + x, y0 + 3] = M.rgba((236, 232, 220))
        else:
            for y in range(4, 8):
                for x in range(1, 7):
                    p[x0 + x, y0 + y] = M.rgba(logo)
            for x in (2, 3, 4, 5):
                p[x0 + x, y0 + 6] = M.rgba(M.lift(body, -20))
            for y in range(10, 14):
                p[x0 + 2, y0 + y] = M.rgba(M.lift(logo, -20))
    for y in range(S):  # (round 2) each pack lit from above: lighter at its top, darker at its foot
        for x in range(S):
            k = (y % 16) / 15.0
            M.touch(img, x, y, 0.06 * (1 - k) - 0.08 * k, 0.1)
    return img


HEAD_FONT = {"S": ("1111", "1000", "1111", "0001", "1111"), "N": ("1001", "1101", "1011", "1001", "1001"),
             "A": ("0110", "1001", "1111", "1001", "1001"), "C": ("0111", "1000", "1000", "1000", "0111"),
             "K": ("1001", "1010", "1100", "1010", "1001"), "D": ("1110", "1001", "1001", "1001", "1110"),
             "R": ("1110", "1001", "1110", "1010", "1001"), "I": ("111", "010", "010", "010", "111"),
             "O": ("0110", "1001", "1001", "1001", "0110"), "L": ("1000", "1000", "1000", "1000", "1111")}


def machine_header(seed, body, panel, ink, word, faded=False):
    """(round 2) A machine's lit sign, in the 9 px band its header face shows (uv 16 x 4.5): the cabinet colour round a
    pale panel and the word in crisp 4 x 5 capitals, centred (the old ones were text scaled down, which smeared)."""
    img = M.noise_hv(body, 2, seed, mottle=3)
    p = img.load()
    rng = random.Random(seed)
    for y in range(1, 8):
        for x in range(1, S - 1):
            p[x, y] = M.rgba(M.lift(panel, rng.uniform(-2, 2) - (8 * rng.random() if faded else 0)))
    widths = [len(HEAD_FONT[ch][0]) for ch in word]
    x = (S - (sum(widths) + len(word) - 1)) // 2
    for ch, wd in zip(word, widths):
        for r, row in enumerate(HEAD_FONT[ch]):
            for c, bit in enumerate(row):
                if bit == "1" and not (faded and rng.random() < 0.15):
                    p[x + c, 2 + r] = M.rgba(ink)
        x += wd + 1
    return img


def glints(spots, frost_top=False):
    """(round 2) Clear glass: see-through (the opaque pass cuts it out) but for a few short glints, so the glass reads
    without long streaks that look like rods in front of what is behind it."""
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1) in spots:
        d.line([x0, y0, x1, y1], fill=(226, 236, 242, 255))
    if frost_top:
        d.line([0, 0, S - 1, 0], fill=(214, 226, 232, 255))
    return img


def machine_textures():
    """The snack machine, the drinks fridge and the dead machines of the vending rooms. The paint is matlib's painted
    metal with a fine grain (the old fills were flat noise); the keypads, coin plates and kick grilles are geometry
    now, so the panels are plain plates; the packets behind the glass hang on modelled spirals (`vendspiral`, a cut-out
    coil), so the packets no longer paint their spiral."""
    img = M.painted_metal(6350, base=(42, 106, 176), grain=2, mottle=4, panel=False, chips=0)
    b9_save(b9_match(img, "vending"), "snackvending")
    b9_save(M.noise_hv((58, 62, 68), 2, 6351, mottle=2), "snackvendpanel")
    b9_save(machine_header(6354, (42, 106, 176), (244, 240, 228), (204, 34, 30), "SNACKS"), "snackvendhead")
    b9_save(machine_header(6355, (30, 74, 138), (244, 248, 252), (30, 74, 154), "DRINKS"), "drinkhead")
    b9_save(machine_header(6356, (106, 36, 32), (184, 176, 160), (122, 26, 20), "COLA", faded=True), "vendpilehead")
    b9_save(glints(((5, 12, 9, 6), (6, 15, 8, 12), (24, 28, 27, 23))), "snackvendglass")
    b9_save(glints(((4, 10, 9, 4), (5, 13, 7, 10), (24, 29, 28, 24))), "fridgeglass")
    img = M.noise_hv((12, 30, 16), 1, 6352, mottle=2)
    b9_font(img, "1.25", 1, 1, (110, 244, 130))
    b9_save(img, "vendlcd")
    img = M.brushed_metal(6353, base=(196, 200, 206), grain=2, streak=4, sheen=10)
    d = ImageDraw.Draw(img)
    d.rectangle([14, 6, 17, 25], fill=(20, 20, 22, 255))
    d.line([18, 6, 18, 25], fill=(232, 236, 240, 255))
    M.bevel(img, (0, 0, S, S), 2, 0.18)
    b9_save(img, "coinplate")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))  # a coil seen from the front: slanted turns of bright wire
    p = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y // 2) % 8
            if t == 0:
                p[x, y] = M.rgba((214, 218, 222))
            elif t == 1:
                p[x, y] = M.rgba((140, 144, 148))
    b9_save(img, "vendspiral")
    # The packets behind the glass: four 4-unit bands (packets 6 px wide), each one packet's face from the top
    img = Image.new("RGBA", (S, S), M.rgba((26, 30, 36)))
    p = img.load()
    for band, (c, logo) in enumerate(((0xE82020, 0xF0C020), (0xF0C020, 0xC02020), (0x30A040, 0xF4F4F0), (0xE87020, 0x6A2A10))):
        body, lg = T.hexrgb(c), T.hexrgb(logo)
        for y in range(S):
            for x in range(6):
                k = y % 6
                col = M.lift(body, 24) if k == 0 else M.lift(body, -14) if k == 5 else M.lift(body, 8 if x < 2 else -6 if x == 5 else 0)
                if k in (2, 3) and 1 <= x <= 4:
                    col = lg
                p[band * 8 + x, y] = M.rgba(col)
    b9_save(img, "snackvendrows")

    img = M.painted_metal(6360, base=(230, 232, 234), grain=2, mottle=3, panel=False, chips=0)
    M.grime(img, 0.06, 6361, color=(150, 146, 136), cells=(8, 4), cover=0.4)
    b9_save(b9_match(img, "fridge"), "fridgebody")
    b9_save(M.noise_hv((22, 24, 26), 2, 6362, mottle=2), "fridgegrille")

    img = M.painted_metal(6370, base=(150, 50, 42), grain=3, mottle=6, panel=False, chips=0)
    M.rust(img, 0.22, 6371, pits=True)
    M.grime(img, 0.3, 6372, color=(60, 42, 30), cells=(8, 4, 2), cover=0.5)
    M.scratches(img, 6, 6373, length=(2, 6), light=0.3)
    b9_save(b9_match(img, "vendpile"), "vendpilebody")
    img = M.noise_hv((58, 60, 64), 2, 6374, mottle=3)
    M.grime(img, 0.25, 6375, color=(50, 40, 32), cells=(4, 2), cover=0.5)
    b9_save(img, "vendpilepanel")
    b9_save(M.noise_hv((14, 16, 16), 1, 6376, mottle=2), "vendpilelcd")


def level61_b9():
    """B9's Level 6.1 textures (see the section's header)."""
    for v in (1, 2, 3):
        sfx = "" if v == 1 else f"-{v}"
        b9_save(terrazzo(v), "snackfloor-terrazzo" + sfx)
        b9_save(checker(v), "snackfloor-checker" + sfx)
        b9_save(quarry(v), "snackfloor-quarry" + sfx)
        b9_save(snack_ceiling(v), "snackceiling-grid" + sfx)
    b9_save(mall_wall(), "snackwall-mall")
    b9_save(wood_panel(), "snackwall-panel")
    b9_save(tiled_wall(), "snackwall-tile")
    b9_save(shop_window(), "snackwall-window")
    b9_save(skylight(), "snackceiling-skylight")
    snack_materials()
    fixture_textures()
    machine_textures()


def level6_b9():
    """B9's Level 6 textures (see the section's header)."""
    for v in (1, 2, 3):
        sfx = "" if v == 1 else f"-{v}"
        b9_save(l6_wall(v), "l6wall" + sfx)
        b9_save(l6_floor(v), "l6floor" + sfx)
    for v in (1, 2):
        b9_save(l6_ceiling(v), "l6ceiling" + ("" if v == 1 else "-2"))
    for v in (1, 2, 3):
        b9_save(l6_wet(v), "l6floor-wet" + ("" if v == 1 else f"-{v}"))
    l6_switch()


# ---------------- Level 7 ----------------

def level7():
    img = noise(0x5E6466, 6, "oceanceiling")
    T.blotch(img, (10, 22), 8, (40, 56, 60), 0.35, 91)
    d = ImageDraw.Draw(img)
    for x in (5, 19, 27):
        d.line([x, 24, x, 31], fill=rgb(0x485052))  # water stains running down
    save(img, "oceanceiling")
    # The islands' unknown rock: dark grey-green basalt broken into angular facets, each its own shade, with dark
    # cracks between them, a pale edge where a facet catches the light, and a few specks of lichen
    rng = random.Random(seed_of("islandrock"))
    pts = [(rng.uniform(0, S), rng.uniform(0, S)) for _ in range(6)]
    shades = [rng.uniform(0.8, 1.1) for _ in pts]
    cracked = {(a, b): rng.random() < 0.55 for a in range(len(pts)) for b in range(len(pts))}
    img = noise(0x4A4F4C, 10, "islandrock")
    px = img.load()
    def nearest(x, y):
        best = []
        for i, (cx, cy) in enumerate(pts):
            for ox in (-S, 0, S):
                for oy in (-S, 0, S):
                    best.append(((x - cx - ox) ** 2 + (y - cy - oy) ** 2, i))
        best.sort()
        return best[0][1], math.sqrt(best[1][0]) - math.sqrt(best[0][0]), best[1][1]
    for y in range(S):
        for x in range(S):
            i, edge, other = nearest(x + 0.5, y + 0.5)
            c = px[x, y]
            k = shades[i] * (1 + 0.1 * ((x - pts[i][0]) + (y - pts[i][1])) / S)  # each facet lit from one side
            c = tuple(max(0, min(255, int(v * k))) for v in c[:3])
            if edge < 0.7 and cracked[min(i, other), max(i, other)]:
                c = (24, 27, 26)  # a crack (not every facet is split from its neighbour)
            elif edge < 1.8 and nearest(x - 0.5, y - 0.5)[0] != i:
                c = tuple(min(255, int(v * 1.25)) for v in c)  # the lit lip of a facet
            px[x, y] = c + (255,)
    specks(img, [0x6E7A5A, 0x8A946A, 0x2A302C], 14, "islandrock-lichen")
    save(img, "islandrock")
    # Tar: glossy near-black, a faint broad sheen across it; on top, a few soft domes where bubbles are rising, each
    # with a pinpoint highlight; down the sides, slow drips with a glint along them and a bead at the end
    def tar_base(key):
        img = noise(0x0A0A0C, 2, key)
        px = img.load()
        for y in range(S):
            for x in range(S):
                t = max(0.0, 1 - abs((x + y) - 26) / 9)
                c = px[x, y]
                px[x, y] = tuple(min(255, int(v + 12 * t)) for v in c[:3]) + (255,)
        return img
    img = tar_base("tar")
    px = img.load()
    for cx, cy, r in ((9, 22, 4.5), (23, 9, 3.5), (25, 25, 2.5)):
        for y in range(S):
            for x in range(S):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 / r
                if d < 1:
                    c = px[x, y]
                    px[x, y] = tuple(min(255, int(v + 26 * (1 - d * d))) for v in c[:3]) + (255,)
        hx, hy = int(cx - r * 0.4), int(cy - r * 0.4)
        px[hx, hy] = (92, 92, 102, 255)
        px[hx + 1, hy] = (56, 56, 64, 255)
    save(img, "tar")
    img = tar_base("tar-side")
    px = img.load()
    rng = random.Random(93)
    for x0 in (3, 10, 19, 27):
        length = rng.randint(10, 26)
        for y in range(length):
            for x in (x0, x0 + 1):
                px[x, y] = (6, 6, 8, 255)
            px[x0 + 1, y] = (34, 34, 40, 255) if y % 7 != 3 else (52, 52, 60, 255)  # the glint along it
        for x in range(x0 - 1, x0 + 3):
            px[x, length] = (8, 8, 10, 255)
        px[x0, length + 1] = (8, 8, 10, 255)
        px[x0 + 1, length + 1] = (8, 8, 10, 255)
        px[x0 + 1, length] = (70, 70, 80, 255)  # the bead's highlight
    save(img, "tar-side")
    flat("bone", 0xE4D8BC, 6)
    flat("scrap", 0x7A4A2A, 14)
    img = noise(0x8A7A50, 5, "canvas")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 12, 27, 24], fill=rgb(0x6A5A38))
    d.line([4, 18, 27, 18], fill=rgb(0x4A3A20))
    save(img, "canvas")
    img = noise(0x3A2A1C, 8, "wetwood")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x221810), width=3)
    d.line([3, 3, S - 4, S - 4], fill=rgb(0x2A1E14), width=2)
    save(img, "wetwood")


# ---------------- Level 8 ----------------

def level8():
    img = noise(0xD8D0B8, 3, "megplate")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A2A2A), width=2)
    d.ellipse([4, 3, 27, 18], outline=rgb(0x2A4A8A), width=2)
    text(img, "M.E.G.", (5, 5, 27, 16), 0x2A4A8A, 6)
    text(img, "9TH ROAD", (1, 20, 31, 29), 0x2A2A2A, 5)
    save(img, "megplate")
    img = noise(0xFFD890, 4, "lampglass")
    ImageDraw.Draw(img).rectangle([12, 0, 19, S - 1], fill=rgb(0xFFF4D0))
    save(img, "lampglass")
    flat("cavestone", 0x8A8478, 8)
    # Bioluminescent fungi: caps that glow from within (a brighter rim and gills, paler speckles), stems, and the
    # mycelium they grow from; blood-red, and the other colours of the mixed clusters
    for name, cap, rim in (("glowcapred", 0xB01818, 0xFF5A40), ("glowcapblue", 0x2A6AD8, 0x8AD8FF),
                           ("glowcapviolet", 0x8A2AC8, 0xE09AFF), ("glowcapgreen", 0x38B850, 0xB8FF8A)):
        img = noise(cap, 6, name)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(rim), width=2)
        rng = random.Random(seed_of(name))
        for _ in range(10):
            x, y = rng.randrange(3, S - 3), rng.randrange(3, S - 3)
            d.rectangle([x, y, x + 1, y + 1], fill=T.shade(T.hexrgb(rim), 1.15))
        save(img, name)
    img = noise(0xD8CCB8, 4, "glowstem")
    save(img, "glowstem")
    img = noise(0x3A1414, 5, "mycelium")
    specks(img, [0x7A2A20, 0xA03A2A, 0x1A0A0A], 40, "mycelium")
    save(img, "mycelium")


# ---------------- Level 9 ----------------

ASPHALT = (48, 49, 50)
ASPHALT_MEAN = (48.5, 49.0, 49.1)  # the road's tone before B7 (and before B11): kept


def asphalt_version(k=0):
    """(B7, at the user's request after B11) The Suburbs' road: a fine, even wearing course: dense 1 px aggregate that
    lifts the binder only a little (matlib.asphalt with a low `chip` range, few pits, faint shadows), almost no broad
    mottle and few binder-rich patches, so it reads as one smooth dark road rather than a speckle. Three versions
    (`k`) differ only in their chips; their broad field is one shared ground at the block edges (`matlib.turn_safe`), so
    the blocktype turns and mixes them without a patchwork. The tone is the old road's."""
    img = M.asphalt(seed=seed_of("asphalt") + 7 * k, base=ASPHALT, grain=2, mottle=2, aggregate=0.45, binder=0.2,
                    chip=(3, 11), pits=0.004, shadow=0.06)
    ground = M.noise_hv(ASPHALT, 0, seed_of("asphalt"), S, 2, (16,), hue=0)
    M.turn_safe(img, ground, band=8, keep=0.5)
    return T.match_rgb(img, ASPHALT_MEAN, "asphalt")


def asphalt_base():
    """The road every marking, the leaves and Level 11's streets (gen_city reads asphalt.png) are painted on."""
    return asphalt_version(0)


def _blob(cx, cy, r, seed, wobble=0.3):
    """A soft, irregular round mask (0..1) about (cx, cy): its radius wanders with the angle (a few lobes from a seeded
    sum of sines), its edge fades over 1.5 px. For patches that must not have straight sides."""
    rng = random.Random(seed)
    lobes = [(rng.randint(2, 5), rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 1.0)) for _ in range(3)]
    norm = sum(a for _, _, a in lobes)
    out = [[0.0] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            dx, dy = x + 0.5 - cx, (y + 0.5 - cy) * 1.15
            ang = math.atan2(dy, dx)
            rr = r * (1 + wobble * sum(a * math.sin(n * ang + ph) for n, ph, a in lobes) / norm)
            out[y][x] = max(0.0, min(1.0, (rr - math.hypot(dx, dy)) / 1.5 + 0.5))
    return out


def asphalt_features():
    """asphalt-2, a crack wandering across the middle of the block, filled with tar (a dark line in a faint glossy
    band); asphalt-3, an old cold-mix patch: an irregular, soft-edged blob, smoother and a shade darker than the road,
    its rim sealed. Both kept inside the block (the versions are turned and mixed) and faint; each is listed one block
    in sixteen (gen_deep.level9). B11's were a straight full-height crack and a square patch."""
    plain = asphalt_version(1)
    img = plain.copy()
    rng = random.Random(seed_of("asphalt-crack"))
    x, y, a = 7.0, 10.0, rng.uniform(-0.3, 0.3)
    for i in range(24):
        xi, yi = int(x) % S, int(y) % S
        M.put(img.load(), S, S, xi, yi, (36, 37, 38))  # (round 2) fainter
        M.touch(img, xi, yi - 1, -0.06)
        M.touch(img, xi, yi + 1, -0.05)
        if i % 3 == 0:
            M.touch(img, xi, yi - 1, 0.08)  # the tar's gloss
        a = a * 0.7 + rng.uniform(-0.45, 0.45)  # wanders, but keeps on across the block
        x, y = x + math.cos(a) * 0.8, y + 0.45 + math.sin(a) * 0.5
    save(T.inside_block(plain, img, band=3), "asphalt-2")
    plain = asphalt_version(2)
    img = plain.copy()
    patch = M.asphalt(seed=seed_of("asphalt-patch"), base=(42, 43, 44), grain=2, mottle=2, aggregate=0.3, binder=0.4,
                      chip=(2, 8), pits=0.002, shadow=0.04)
    mask = _blob(16, 15, 8.5, seed_of("asphalt-patchshape"))
    p, q = img.load(), patch.load()
    for yy in range(S):
        for xx in range(S):
            m = mask[yy][xx]
            if m > 0:
                c = M.mix(p[xx, yy], q[xx, yy], m)
                if 0.15 < m < 0.75:  # the sealed rim: a dark seam of tar round the edge
                    c = M.lift(c, -4)
                p[xx, yy] = M.rgba(c)
    save(T.inside_block(plain, img), "asphalt-3")


def painted_mark(img, box, colour, k=0.55):
    """(B7) Road paint over the asphalt: the paint's colour taking the road's own light and dark (so the line has the
    grain under it), clean to the box's edges, which run to the block's edges, so a line meets the next one."""
    x0, y0, x1, y1 = box
    px = img.load()
    base = M.lum(ASPHALT)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px[x, y] = M.rgba(M.lift(colour, (M.lum(px[x, y]) - base) * k))
    return img


def level9():
    img = asphalt_base()
    save(img, "asphalt")
    save(asphalt_version(1), "asphalt-4")  # (B7) the plain road's other two versions
    save(asphalt_version(2), "asphalt-5")
    asphalt_features()
    leaves = img.copy()
    rng = random.Random(101)
    d = ImageDraw.Draw(leaves)
    for _ in range(14):
        x, y = rng.randrange(S - 3), rng.randrange(S - 3)
        d.ellipse([x, y, x + 3, y + 2], fill=rgb(rng.choice([0x8A5A1E, 0xB07A20, 0x6A3A14, 0x9A2A14])))
    save(leaves, "asphalt-leaves")
    # Wet asphalt: standing water, smoother and darker than the dry road, with the sky in it as a blue-grey sheen in
    # long ripples and a glint or two, so a puddle reads as water and not as a shadow. The ripples wrap round the tile
    # (it is turned at random from block to block, so they never line up)
    wet = noise(0x181C24, 2, "asphaltwet")
    px = wet.load()
    for y in range(S):
        for x in range(S):
            ripple = 0.5 + 0.5 * math.sin(2 * math.pi * (x + 3 * y) / S + 0.8 * math.sin(2 * math.pi * 2 * x / S))
            t = 0.06 + 0.22 * ripple ** 3
            r_, g_, b_, a_ = px[x, y]
            px[x, y] = (int(r_ + (78 - r_) * t), int(g_ + (90 - g_) * t), int(b_ + (112 - b_) * t), a_)
    rng = random.Random(102)
    for _ in range(5):
        wet.putpixel((rng.randrange(S), rng.randrange(S)), (128, 138, 156, 255))
    save(wet, "asphalt-wet")
    img = M.concrete(seed=seed_of("sidewalk"), base=(156, 153, 144), grain=3, mottle=5, aggregate=0.05, pores=0.01)
    M.emboss_lines(img, xs=(0,), ys=(0, 16), strength=0.3)
    save(img, "sidewalk")
    img = noise(0x8A5E38, 5, "housewood")
    for y in range(0, S, 5):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x6A4424))
    save(img, "housefloor-wood")
    save(noise(0x7A6A60, 5, "housecarpet"), "housefloor-carpet")
    img = noise(0xE8ECF0, 2, "housetile")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0xA8B0B8))
        d.line([k, 0, k, S - 1], fill=rgb(0xA8B0B8))
    save(img, "housefloor-tile")
    img = Image.new("RGBA", (S, S))
    for y in range(S):
        for x in range(S):
            img.putpixel((x, y), rgb(0xE8DCC0 if (x // 8 + y // 8) % 2 == 0 else 0xC89A6A))
    save(img, "housefloor-lino")
    save(T.concrete_floor("plain"), "housefloor-garage")
    # (the painted siding: exteriors_b11)
    save(grime(block_wall(0x9A4A34, 0xC8B8A8, "brick", rows=8), "brick", 0.15), "siding-brick")
    save(noise(0xE6DCC8, 2, "plaster-interior"), "plaster-interior")
    img = noise(0xE8DCC8, 2, "paper-floral")
    rng = random.Random(111)
    d = ImageDraw.Draw(img)
    for y in range(4, S, 10):
        for x in range(4 + (y // 10 % 2) * 5, S, 10):
            d.ellipse([x - 2, y - 2, x + 2, y + 2], fill=rgb(0xC87888))
            d.point((x + 3, y + 1), fill=rgb(0x6A9A5A))
    save(img, "houseinterior-floral")
    img = noise(0xD8D8E8, 2, "paper-stripe")
    for x in range(0, S, 6):
        ImageDraw.Draw(img).rectangle([x, 0, x + 1, S - 1], fill=rgb(0xA8A8C8))
    save(img, "houseinterior-stripe")
    save(noise(0xD8C8A8, 3, "paper-beige"), "houseinterior-beige")
    img = noise(0xA8C0A0, 3, "paper-green")
    for y in range(0, S, 8):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x98B090))
    save(img, "houseinterior-green")
    img = noise(0xF0F2F4, 2, "paper-tile")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0xB8C0C8))
        d.line([k, 0, k, S - 1], fill=rgb(0xB8C0C8))
    save(img, "houseinterior-tile")
    # The glass of a house window (the frame, the glazing bars and the sill are the block's own boxes): dark, with the
    # night sky's faint sheen across it and the curtains just showing at the sides; or lit, warm, the curtains drawn
    # back in folds either side
    def lerp(a, b, f):
        return tuple(p + (q - p) * f for p, q in zip(a[:3], b[:3]))

    for state in ("dark", "lit"):
        img = Image.new("RGBA", (S, S))
        px = img.load()
        rng = random.Random(seed_of("housewindow" + state))
        for y in range(S):
            for x in range(S):
                edge = min(x, S - 1 - x)
                fold = 0.85 + 0.15 * math.sin(x * 1.9)
                if state == "dark":
                    sheen = max(0.0, 1 - abs((x + y * 0.6) - 18) / 6) * 0.35
                    c = lerp(T.hexrgb(0x0C1018), T.hexrgb(0x2A3442), 0.25 * (1 - y / S) + sheen)
                    if edge < 5:
                        c = lerp(c, T.shade(T.hexrgb(0x3A3028), fold), 0.55)
                else:
                    glow = 1 - abs(x - S / 2) / (S / 2) * 0.35 - y / S * 0.1
                    c = T.shade(T.hexrgb(0xFFD890), glow)
                    if edge < 6:
                        c = T.shade(T.hexrgb(0xD8904A), fold * (0.8 + 0.04 * edge))
                k = rng.uniform(0.96, 1.04)
                px[x, y] = tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)
        save(img, f"housewindow-{state}")
    # Painted wood: the window frames, a porch's posts and the skirt round its deck
    img = noise(0xEEEDE6, 2, "windowtrim")
    d = ImageDraw.Draw(img)
    for y in (7, 19, 28):
        d.line([0, y, S - 1, y], fill=rgb(0xDCDAD0))
    save(img, "windowtrim")
    # A porch lamp with no power: dusty amber glass
    img = noise(0x5A4A30, 4, "porchglass-off")
    ImageDraw.Draw(img).line([4, 4, 12, 20], fill=rgb(0x7A6A50))
    save(img, "porchglass-off")
    # The concrete step up to a porch
    img = noise(0xB8B4AA, 4, "porchstep")
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xA09C92))
    save(img, "porchstep")
    # Street names on the Suburbs' corners, white on green; the same few over and over
    for street in ("elm", "oak", "maple", "pine", "cedar", "birch", "walnut", "ash"):
        img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
        text(img, f"{street.upper()} ST", (0, 6, S, 26), 0xFFFFFF, 5)
        ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFFFFF))
        save(img, f"suburbsign-{street}")
    for street in ("willow", "linden", "aspen", "poplar", "holly", "laurel", "spruce", "cherry"):
        img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
        text(img, f"{street.upper()} AV", (0, 6, S, 26), 0xFFFFFF, 5)
        ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFFFFF))
        save(img, f"suburbsignblade-{street}")
    # The guide sign toward the city: DOWNTOWN in plain block capitals (three pixels wide, doubled in height, to fill
    # the plate) and an arrow, as read from either side
    glyphs = {"D": ["110", "101", "101", "101", "110"], "O": ["111", "101", "101", "101", "111"],
              "W": ["101", "101", "111", "111", "101"], "N": ["110", "101", "101", "101", "101"], "T": ["111", "010", "010", "010", "010"]}
    for side in ("right", "left"):
        img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
        d = ImageDraw.Draw(img)
        d.line([0, 1, S - 1, 1], fill=rgb(0xFFFFFF))
        d.line([0, S - 2, S - 1, S - 2], fill=rgb(0xFFFFFF))
        for k, ch in enumerate("DOWNTOWN"):
            for gy, row in enumerate(glyphs[ch]):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        d.rectangle([k * 4 + gx, 5 + gy * 2, k * 4 + gx, 6 + gy * 2], fill=rgb(0xFFFFFF))
        # The arrow, drawn rather than lettered so it is the same in any font
        tip = S - 6 if side == "right" else 5
        tail = 6 if side == "right" else S - 7
        d.line([tail, 22, tip, 22], fill=rgb(0xFFFFFF), width=2)
        k = -1 if side == "right" else 1
        d.polygon([(tip - k, 22), (tip + k * 5, 17), (tip + k * 5, 27)], fill=rgb(0xFFFFFF))
        save(img, f"citysign-{side}")
    # (the roofing: exteriors_b11)
    img = noise(0xF0EEE8, 6, "popcorn")
    save(img, "houseceiling")
    for part in ("lower", "upper"):
        img = M.noise_hv((136, 48, 36), amp=3, seed=seed_of("housedoor" + part), mottle=4, hue=2)
        # the casing round the door, painted like the windows
        trim = M.noise_hv(TRIM, amp=2, seed=seed_of("doortrim" + part), mottle=2, hue=1)
        for y in range(S):
            for x in list(range(0, 2)) + list(range(S - 2, S)):
                img.putpixel((x, y), trim.getpixel((x, y)))
        if part == "upper":
            for x in range(S):
                for y in (0, 1):
                    img.putpixel((x, y), trim.getpixel((x, y)))
        M.inset(img, (2, 0 if part == "lower" else 2, S - 2, S), strength=0.3)
        panels = ((5, 3, 15, 28), (17, 3, 27, 28)) if part == "lower" else ((5, 18, 15, 30), (17, 18, 27, 30))
        for box in panels:
            M.inset(img, box, strength=0.24)
            M.bevel(img, (box[0] + 1, box[1] + 1, box[2] - 1, box[3] - 1), strength=0.14)
        if part == "lower":
            for x, y, f in ((22, 1, 0.5), (23, 1, 0.7), (22, 2, 0.3), (23, 2, 0.2), (24, 2, 0.0), (23, 3, -0.2)):
                img.putpixel((x, y), M.rgba(M.shade_px((200, 160, 70), f)))
        else:
            glass = Image.new("RGBA", (12, 10), (26, 32, 40, 255))
            for y in range(10):
                for x in range(12):
                    sheen = max(0.0, 1 - abs((x + y * 0.6) - 7) / 3) * 0.25
                    glass.putpixel((x, y), M.rgba(M.mix((26, 32, 40), (70, 84, 100), sheen + 0.1 * (1 - y / 10))))
            img.paste(glass, (10, 5))
            M.inset(img, (9, 4, 23, 16), strength=0.3)
        save(img, f"housedoor-{part}")
        img = M.noise_hv((226, 224, 214), amp=2, seed=seed_of("garage" + part), mottle=3, hue=1)
        for y0 in range(0, S, 8):
            M.emboss_lines(img, ys=(y0,), strength=0.28)
            for x0 in (2, 17):
                M.inset(img, (x0, y0 + 2, x0 + 13, y0 + 7), strength=0.2)
                M.bevel(img, (x0 + 1, y0 + 3, x0 + 12, y0 + 6), strength=0.16)
        save(img, f"garagedoor-{part}")
    flat("tvwood", 0x5A3A22, 4)
    img = Image.new("RGBA", (S, S), rgb(0x1A1A1C))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([3, 4, 24, 26], 4, fill=rgb(0x2A3036))
    d.line([6, 8, 12, 12], fill=rgb(0x4A5258))
    for y in (8, 14, 20):
        d.ellipse([26, y, 29, y + 3], fill=rgb(0x8A8E92))
    save(img, "tvscreen")
    flat("enamel", 0xF0F0EC, 2)
    flat("dresserwood", 0x7A5232, 5)
    img = noise(0x7A5232, 5, "dresserfront")
    d = ImageDraw.Draw(img)
    for y in (2, 12, 22):
        d.rectangle([2, y, S - 3, y + 8], outline=rgb(0x4A3018))
        d.rectangle([13, y + 3, 18, y + 4], fill=rgb(0xC8A050))
    save(img, "dresserfront")
    img = noise(0xFFF0C0, 3, "streetlamp")
    save(img, "streetlamp")
    save(noise(0x8A9094, 3, "streetlampoff"), "streetlampoff")
    save(M.painted_metal(seed=seed_of("mailbox"), base=(44, 60, 92), panel=False, chips=0), "mailbox")
    img = noise(0xA88A5A, 10, "burlap")
    for k in range(0, S, 3):
        ImageDraw.Draw(img).line([0, k, S - 1, k], fill=rgb(0x8A6E44))
    save(img, "burlap")
    img = Image.new("RGBA", (S, S), rgb(0x6A4A2A))
    d = ImageDraw.Draw(img)
    rng = random.Random(121)
    for row in range(3):
        for x in range(2, S - 4, 6):
            c = rng.choice([0xC8B070, 0xA03020, 0x3A6AB0, 0xE8E0C8, 0x6A8A3A])
            d.rectangle([x, row * 11 + 3, x + 4, row * 11 + 9], fill=rgb(c))
        d.line([0, row * 11 + 10, S - 1, row * 11 + 10], fill=rgb(0x4A3018))
    save(img, "pantry")
    img = Image.new("RGBA", (S, S), rgb(0x5A5E62))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 9, 14], fill=rgb(0xB02018))
    d.rectangle([13, 4, 15, 15], fill=rgb(0x8A6A3A))
    d.rectangle([12, 3, 18, 6], fill=rgb(0x8A8E92))
    d.rectangle([20, 3, 29, 9], fill=rgb(0xE0B020))
    d.ellipse([3, 18, 14, 29], outline=rgb(0x2A6A2A), width=2)
    d.rectangle([18, 20, 29, 28], fill=rgb(0x8A8E92))
    save(img, "toolwall")
    img = noise(0xC89A6A, 4, "cabinetfront")
    d = ImageDraw.Draw(img)
    d.line([16, 0, 16, S - 1], fill=rgb(0x8A6A44))
    d.rectangle([2, 2, 14, S - 3], outline=rgb(0x8A6A44))
    d.rectangle([18, 2, 29, S - 3], outline=rgb(0x8A6A44))
    d.rectangle([12, 14, 13, 18], fill=rgb(0xC8CCD0))
    d.rectangle([19, 14, 20, 18], fill=rgb(0xC8CCD0))
    save(img, "cabinetfront")


# ---------------- Level 10 ----------------

def level10():
    img = noise(0x8A6E4A, 6, "dirtroad")
    specks(img, [0x6A5236, 0xA0845A, 0x5A4630], 60, "dirtroad")
    save(img, "dirtroad")
    tracks = img.copy()
    d = ImageDraw.Draw(tracks)
    for x in (5, 24):
        d.rectangle([x, 0, x + 3, S - 1], fill=rgb(0x5E4A32))
        for y in range(0, S, 4):
            d.line([x, y, x + 3, y + 1], fill=rgb(0x4E3C28))
    save(tracks, "dirtroad-tracks")
    # (the barns' boards and tin: exteriors_b11)
    img = noise(0x8A4A4A, 10, "wormmass")
    d = ImageDraw.Draw(img)
    rng = random.Random(131)
    for _ in range(26):
        x, y = rng.randrange(S), rng.randrange(S)
        pts = [(x, y)]
        for k in range(4):
            x, y = x + rng.randint(-3, 3), y + rng.randint(-3, 3)
            pts.append((x, y))
        d.line(pts, fill=rgb(rng.choice([0xC87878, 0xB06060, 0xD89090, 0x7A3A3A])), width=2)
    save(img, "wormmass")
    flat("feed", 0xC8A858, 10)
    img = noise(0x6A4A2A, 6, "barrelwood")
    d = ImageDraw.Draw(img)
    for y in (4, 27):
        d.rectangle([0, y, S - 1, y + 1], fill=rgb(0x3A3A3E))
    save(img, "barrelwood")
    img = noise(0x5A5E62, 10, "nails")
    specks(img, [0x9A9EA2, 0xB8BCC0, 0x3A3E42], 120, "nails")
    save(img, "nails")


# ---------------- Refinements: Levels 5 to 10 in more detail ----------------

def refinements():
    # (Level 6's standing water on the cold floor is B9's l6_wet, written by level6)

    # Level 7: a weathered jetty
    img = noise(0x6A5A44, 5, "jetty")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=rgb(0x3E3226))
        d.point([(4, y + 3), (27, y + 4)], fill=rgb(0x2A2420))
    save(img, "jetty")

    # Level 9: road markings, a manhole, a porch, a drive, a rug, a drained pool, ceiling lights
    asphalt = asphalt_base()
    line = painted_mark(asphalt.copy(), (0, 13, S - 1, 18), T.hexrgb(0xD8B830))
    save(line, "asphalt-line")
    save(line.rotate(90), "asphalt-linens")
    zebra = painted_mark(asphalt.copy(), (0, 2, S - 1, 15), T.hexrgb(0xD8D8D2))
    save(zebra, "asphalt-crossing")
    save(zebra.rotate(90), "asphalt-crossingns")
    hole = asphalt.copy()
    d = ImageDraw.Draw(hole)
    d.ellipse([3, 3, 28, 28], fill=rgb(0x2E2A26), outline=rgb(0x141210))
    for k in range(7, 26, 4):
        d.line([7, k, 24, k], fill=rgb(0x403A34))
    save(hole, "asphalt-manhole")
    img = noise(0x8A8E92, 3, "porch")
    for y in range(0, S, 6):
        ImageDraw.Draw(img).line([0, y, S - 1, y], fill=rgb(0x5E6266))
    save(img, "housefloor-porch")
    img = noise(0xB4B0A8, 3, "driveway")
    ImageDraw.Draw(img).line([0, 0, S - 1, 0], fill=rgb(0x8A8680))
    save(img, "housefloor-driveway")
    img = noise(0x8A2A2E, 3, "rug")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, S - 3, S - 3], outline=rgb(0xC8A060))
    d.rectangle([6, 6, S - 7, S - 7], outline=rgb(0x2A3A6A))
    d.polygon([(16, 9), (23, 16), (16, 23), (9, 16)], outline=rgb(0xC8A060))
    save(img, "housefloor-rug")
    img = noise(0x8AB8CC, 2, "poolfloor")
    d = ImageDraw.Draw(img)
    for k in range(0, S, 8):
        d.line([0, k, S - 1, k], fill=rgb(0x6A98AC))
        d.line([k, 0, k, S - 1], fill=rgb(0x6A98AC))
    rng = random.Random(201)
    for _ in range(5):  # dead leaves and grime in the bottom
        x, y = rng.randrange(S - 3), rng.randrange(S - 3)
        d.ellipse([x, y, x + 3, y + 2], fill=rgb(rng.choice([0x6A4A24, 0x4A3A20, 0x5A6A50])))
    save(img, "pool-floor")
    save(noise(0xD8D0BC, 3, "coping"), "pool-coping")
    for name, on in (("lightoff", False), ("lighton", True)):
        img = T.noise_fill(T.hexrgb(0xE8E4DA), 2, seed_of("houseceiling"))
        d = ImageDraw.Draw(img)
        d.ellipse([8, 8, 23, 23], fill=rgb(0xFFF4D0 if on else 0xD8D4CA), outline=rgb(0xB0A890))
        save(img, f"houseceiling-{name}")
    # Exterior things
    img = Image.new("RGBA", (S, S), rgb(0xE8E6E0))
    d = ImageDraw.Draw(img)
    d.polygon([(10, 2), (22, 2), (30, 10), (30, 22), (22, 30), (10, 30), (2, 22), (2, 10)], fill=rgb(0xB01818), outline=rgb(0xF0F0F0))
    text(img, "STOP", (4, 10, 28, 22), 0xF4F4F4, 9)
    save(img, "stopsign")
    flat("binplastic", 0x2A4A2E, 4)
    img = noise(0xF0F0EC, 2, "backboard")
    ImageDraw.Draw(img).rectangle([10, 14, 21, 25], outline=rgb(0xD04A18), width=2)
    save(img, "backboard")
    save(M.painted_metal(seed=seed_of("tractorgreen"), base=(62, 98, 54), panel=False, chips=4, under=(70, 66, 60)), "tractorgreen")
    img = noise(0xC8A850, 8, "hayside")
    d = ImageDraw.Draw(img)
    for y in range(0, S, 3):
        d.line([0, y, S - 1, y + 1], fill=rgb(0xA88A3A))
    save(img, "hayroll-side")
    img = noise(0xC8A850, 8, "hayend")
    d = ImageDraw.Draw(img)
    for r in range(3, 16, 3):
        d.ellipse([16 - r, 16 - r, 16 + r, 16 + r], outline=rgb(0xA0823A))
    save(img, "hayroll-end")
    # A galvanised trough out in a field, ribbed, and the rainwater in it with a leaf floating
    img = noise(0x9AA2A4, 6, "galvanised")
    d = ImageDraw.Draw(img)
    for x in range(0, S, 4):
        d.line([x, 0, x, S - 1], fill=rgb(0x848C8E))
    save(img, "galvanised")
    img = noise(0x3E5A5A, 4, "troughwater")
    d = ImageDraw.Draw(img)
    d.line([3, 20, 14, 18], fill=rgb(0x96AAAC))
    d.line([18, 9, 27, 8], fill=rgb(0x789296))
    d.ellipse([22, 22, 26, 25], fill=rgb(0x606E46))
    save(img, "troughwater")
    img = noise(0xB8BCC0, 3, "icemachine")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 14, 27, 28], fill=rgb(0x6A7076))
    text(img, "ICE", (6, 2, 26, 12), 0x2A5A9A, 9)
    save(img, "icemachine")
    img = Image.new("RGBA", (S, S), rgb(0x5A3A20))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, 28, 28], fill=rgb(0xC8C0A8))
    for cx, h in ((10, 13), (16, 10), (22, 14)):  # a family, smiling, faded
        d.ellipse([cx - 3, h, cx + 3, h + 6], fill=rgb(0xC09070))
        d.rectangle([cx - 4, h + 6, cx + 4, 27], fill=rgb(0x5A6A8A))
    save(img, "familyphoto")
    img = noise(0xDCDAD2, 2, "washer")
    d = ImageDraw.Draw(img)
    d.ellipse([7, 9, 24, 26], fill=rgb(0x3A4048), outline=rgb(0x9AA0A8), width=2)
    d.rectangle([3, 2, 28, 6], fill=rgb(0xB8B8B0))
    save(img, "washerfront")
    img = noise(0x8A2A2A, 4, "toybox")
    d = ImageDraw.Draw(img)
    for x, c in ((5, 0xD8C030), (14, 0x3A6AC8), (23, 0x3A9A4A)):
        d.rectangle([x, 12, x + 5, 20], fill=rgb(c))
    save(img, "toybox")
    img = corrugated((172, 168, 160), seed_of("silo"))
    save(img, "silo")
    flat("silotop", 0x6A6E72, 4)
    img = noise(0xA88A52, 8, "stubble")
    d = ImageDraw.Draw(img)
    rng = random.Random(207)
    for _ in range(70):
        x, y = rng.randrange(S), rng.randrange(S - 2)
        d.line([x, y, x, y + 2], fill=rgb(rng.choice([0xD8C070, 0xC8B060, 0xE8D890])))
    save(img, "stubble")



# ---------------- Graphics pass B11: the Suburbs' and the farms' outsides ----------------
#
# One material family per surface, shared by every block that shows it: the lap siding on a house's walls, corners and
# gable ends (the roof blocks over a gable wall carry the same siding: gen_deep.roofs), the roofing courses, the eave's
# soffit, fascia and gutter, and the barns' boards and tin. Built from tools/matlib.py: structure, then the light from
# above, then a low grain; seamless, with the odd feature (a paint chip, a rust streak) in one alternate of three.

SIDING = {"white": (226, 224, 214), "blue": (120, 150, 182), "yellow": (222, 202, 136), "green": (136, 166, 136)}
ROOFING = {"grey": (92, 90, 88), "brown": (96, 70, 50), "red": (124, 54, 42)}
TRIM = (236, 234, 226)


def lap_siding(base, seed, wear=0):
    """Painted lap siding: eight boards of 4 px to the block, each a touch its own shade and hue; under the butt of the
    board above, a dark shadow line, then the face catching more light toward its lower edge, which stands proud.
    `wear` scatters that many paint chips (for one alternate in three)."""
    img = M.noise_hv(base, amp=3, seed=seed, mottle=2, cells=(16, 8), hue=1.0)
    px = img.load()
    rng = random.Random(M.sub(seed, "boards"))
    streak = M.value_noise((S, S), (8, 1), M.sub(seed, "streak"))
    rows = (-0.26, -0.07, 0.0, 0.05)
    for b in range(S // 4):
        dv, dh = rng.uniform(-3, 3), rng.uniform(-2, 2)
        for r in range(4):
            y = b * 4 + r
            for x in range(S):
                c = M.hue_shift(M.lift(px[x, y], dv + streak[y][x] * 3), dh)
                px[x, y] = M.rgba(M.shade_px(c, rows[r]))
    for _ in range(wear):
        x, b = rng.randrange(S), rng.randrange(S // 4)
        y = b * 4 + 3  # paint lifts at the proud lower edge first
        for k in range(rng.randint(1, 3)):
            M.put(px, S, S, x + k, y, M.lift(M.mix(px[(x + k) % S, y], (150, 132, 104), 0.4), -4))
        M.touch(img, x, y - 1, -0.06)
    return img


def shingle_courses(base, seed, courses=4, dark_tabs=0.2):
    """Laminated roofing shingles for the course-by-course roof (gen_deep.roofs). Each band of 32/courses px is one
    course; its top row is the butt (the lower, down-slope edge: an up face's v runs north to south and the roof is
    built sloping down to the north), its last rows sit in the shadow of the next course's butt, which the shape raises
    as geometry. Tabs of uneven width (as dimensional shingles have) each take their own shade and hue, a slot of the
    dark underlayer between them, granules over all."""
    img = M.noise_hv(base, amp=5, seed=seed, mottle=4, cells=(16, 8), hue=2.5)
    px = img.load()
    rng = random.Random(M.sub(seed, "tabs"))
    ch = S // courses
    for c in range(courses):
        widths = []
        while sum(widths) < S:
            widths.append(rng.choice((6, 7, 8, 9, 10, 12)))
        widths[-1] -= sum(widths) - S
        if widths[-1] < 3:
            widths[-2] += widths.pop()
        x0 = rng.randrange(S)
        for w in widths:
            tone, hue = rng.uniform(-6, 6), rng.uniform(-3, 3)
            band = rng.random() < dark_tabs  # a darker laminate tab
            for r in range(ch):
                y = c * ch + r
                f = 0.06 if r == 0 else -0.10 if r == ch - 2 else -0.24 if r == ch - 1 else 0.0
                for k in range(w):
                    x = (x0 + k) % S
                    col = M.hue_shift(M.lift(px[x, y], tone - (10 if band and r >= ch // 2 else 0)), hue)
                    if k == 0 and r < ch - 1:
                        col = M.lift(col, -32)  # the slot
                    elif k == w - 1:
                        col = M.lift(col, -5)
                    px[x, y] = M.rgba(M.shade_px(col, f))
            x0 += w
    # granules: the odd light and dark grain
    g = random.Random(M.sub(seed, "granules"))
    for _ in range(90):
        M.touch(img, g.randrange(S), g.randrange(S), g.choice((-0.12, -0.08, 0.1)))
    return img


def roof_edge(base, seed):
    """The butt and cut ends of the courses, and the edge of a ridge cap: the shingle's thickness, in shade."""
    img = M.noise_hv(M.lift(base, -10), amp=4, seed=seed, mottle=3, hue=2)
    for y in range(0, S, 4):
        for x in range(S):
            M.touch(img, x, y, 0.08)
    return img


def ridge_cap(base, seed):
    """Cap shingles along a ridge, each lapping the next: a dark butt line every 8 px across the ridge (the cap's up
    face runs u along the ridge), lit on its upper side."""
    img = M.noise_hv(M.lift(base, -6), amp=5, seed=seed, mottle=3, hue=2)
    for x0 in range(0, S, 8):
        for y in range(S):
            M.touch(img, x0, y, -0.28)
            M.touch(img, x0 + 1, y, 0.08)
            M.touch(img, x0 + 7, y, -0.08)
    return img


def soffit(base, seed, board=16):
    """The painted soffit under the eaves and the porch roofs: light panels with a fine vent perforation in a band
    along each, a shallow joint every `board` px. It is seen from below and in shade, so it is painted light and
    keeps its lines faint, or it reads as more siding."""
    img = M.noise_hv(M.lift(base, 10), amp=2, seed=seed, mottle=2, hue=1)
    for y0 in range(0, S, board):
        for x in range(S):
            M.touch(img, x, y0, -0.1)
        for x in range(1, S, 2):
            for y in (y0 + 6, y0 + 9):
                M.touch(img, x, y, -0.12)
    return img


def gutter(seed):
    """A painted aluminium gutter: the rolled lip lit along the top, the face, its shadowed underside; seen from above
    (its up face), the dark trough between two lips."""
    img = M.noise_hv((214, 214, 206), amp=2, seed=seed, mottle=2, hue=1)
    shade = {0: 0.12, 1: 0.04, 2: -0.1, 13: -0.06, 14: -0.14, 15: -0.2}
    for y in range(S):
        f = shade.get(y % 16, 0.0)
        for x in range(S):
            M.touch(img, x, y, f)
    for x in range(0, S, 16):  # a joint strap now and then
        for y in range(S):
            M.touch(img, x, y, -0.08)
    return img


def corrugated(base, seed, rust=0):
    """Corrugated tin for the barns' roofs: ribs every 4 px running down the slope (along v), each lit on its left
    flank and dark on its right; galvanising worn to grey, a rust streak down from a nail line in `rust` places."""
    img = M.noise_hv(base, amp=3, seed=seed, mottle=6, cells=(16, 8), hue=1.5)
    prof = (0.12, 0.04, -0.06, -0.16)
    for x in range(S):
        for y in range(S):
            M.touch(img, x, y, prof[x % 4])
    for y in (0, 16):  # the nail lines across the sheets
        for x in range(1, S, 4):
            M.touch(img, x, y + 3, -0.3)
    if rust:
        M.drips(img, n=rust, seed=M.sub(seed, "rust"), color=(122, 70, 40), length=(8, 20), strength=0.35, width=1)
    return img


def barn_boards(base, seed, wear=False):
    """Board and batten for the barns and sheds: three boards to the block, grain upright, and a batten every
    10-11 px as a raised strip lit on its left edge and shadowed to its right; paint gone thin at the foot in one
    alternate."""
    img = M.wood_planks(seed=seed, base=base, planks=(12, 9, 11), direction="v", grain=3, contrast=0.4, flecks=0.4,
                        per_plank=5, gap=M.lift(base, -40))
    for x0 in (0, 12, 21):  # battens over the gaps
        for y in range(S):
            M.touch(img, (x0 - 1) % S, y, 0.16)
            M.touch(img, x0, y, 0.1)
            M.touch(img, (x0 + 2) % S, y, -0.18)
    if wear:
        M.grime(img, 0.18, seed=M.sub(seed, "wear"), color=(118, 104, 86), cover=0.35)
    return img


def exteriors_b11():
    """The Suburbs' siding (every colour, three alternates each), roofing, eaves, and the barns' boards and tin."""
    for name, c in SIDING.items():
        for k, wear in enumerate((0, 0, 0)):
            save(lap_siding(c, seed_of(f"siding-{name}-{k}"), wear), f"siding-{name}" + ("" if k == 0 else f"-{k + 1}"))
    for name, c in ROOFING.items():
        for k in range(3):
            save(shingle_courses(c, seed_of(f"roof-{name}-{k}")), f"houseroof-{name}" + ("" if k == 0 else f"-{k + 1}"))
        save(roof_edge(c, seed_of(f"roofedge-{name}")), f"roofedge-{name}")
        save(ridge_cap(c, seed_of(f"roofcap-{name}")), f"roofcap-{name}")
    save(soffit(TRIM, seed_of("soffit")), "soffit")
    save(gutter(seed_of("gutter")), "gutter")
    tin = (128, 130, 128)
    for k, rust in enumerate((0, 0, 3)):
        save(corrugated(tin, seed_of(f"barnroof-{k}"), rust), "barnroof" + ("" if k == 0 else f"-{k + 1}"))
    save(roof_edge(tin, seed_of("barnroofedge")), "roofedge-barn")
    img = M.brushed_metal(seed=seed_of("barnroofcap"), base=(140, 142, 140), direction="h")
    save(img, "roofcap-barn")
    save(M.wood_planks(seed=seed_of("barndeck"), base=(96, 82, 66), planks=4, grain=4, contrast=0.8, per_plank=8), "barndeck")
    for name, c in (("red", (124, 44, 34)), ("grey", (134, 128, 118))):
        for k in range(3):
            save(barn_boards(c, seed_of(f"barnwall-{name}-{k}"), wear=k == 2), f"barnwall-{name}" + ("" if k == 0 else f"-{k + 1}"))


def generate():
    refinements()
    level6()
    level61()
    level7()
    level8()
    level9()
    level10()
    exteriors_b11()
