"""Level 11, the Endless City: its textures, blocks, props, wall decorations and names. Called from gen_detail.py,
which writes them out along with everything else (python tools/gen_detail.py).

Façades come in six styles (curtain glass, mirror glass, red and dark brick, limestone, concrete), each with a plain
wall, a window (dark, lit, or with the blinds down) and the band at each floor. Façade blocks show their style on one
face, the outside, and plaster on the others, like the Suburbs' house walls.
"""
import json
import math
import os
import random
import sys

from PIL import Image, ImageDraw

import matlib as M
import texlib
from detail_kit import (ASSETS, CLOTH, GLASS, LANG, METAL, ROTATE, SIDES, STONE, WOOD, Decor, block, bx, cube, cyl, name,
                        prop, seam_halves, shape, wall_family, write_json)
from detail_textures import S, noise, rgb, save, text
from gen_detail import cube_block, plate
from detail_kit import T, seed_of
import l11art as L11
import l11art_tex


def drops(*items):
    out = []
    for code, avg, var in items:
        kind = "item"
        if code.startswith("block:"):
            kind, code = "block", code[6:]
        out.append({"type": kind, "code": code, "quantity": {"avg": avg, "var": var}})
    return out


def threshold(kind):
    return [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]


STYLES = ["glass", "mirror", "brick", "brickdark", "stone", "concrete"]
PARTS = ["wall", "window", "lit", "blinds", "band"]
# The other panes of the mirror-glass towers, mixed in among the first so a façade doesn't tile
MIRROR_ALTERNATES = ["facade-mirror-alt1", "facade-mirror-alt2", "facade-mirror-alt3"]


# ======================= Textures =======================

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def blend(a, b, t):
    return tuple(int(a[k] + (b[k] - a[k]) * t) for k in range(3)) + (255,)


def bricks(base, mortar, key, course=4, length=8):
    """Small bricks in running bond, each a little different in colour."""
    rng = random.Random(seed_of(key))
    img = Image.new("RGBA", (S, S), rgb(mortar))
    d = ImageDraw.Draw(img)
    b = T.hexrgb(base)
    for r in range(S // course):
        y = r * course
        off = (length // 2) if r % 2 else 0
        for x in range(-off, S, length):
            f = rng.uniform(0.82, 1.12)
            d.rectangle([x + 1, y + 1, x + length - 1, y + course - 1], fill=shade(b, f))
    return T.noise_fill_over(img, 5, seed_of(key) + 1) if hasattr(T, "noise_fill_over") else img


def speckle(img, amount, key):
    rng = random.Random(seed_of(key))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount)
            px[x, y] = (max(0, min(255, int(r + n))), max(0, min(255, int(g + n))), max(0, min(255, int(b + n))), a)
    return img


def glass_pane(sky_top, sky_bottom, frame, key, mullion=True):
    """Reflective glass: the sky, lighter at the top, with a diagonal sheen, framed by mullions."""
    img = texlib.vertical_gradient(sky_top, sky_bottom)
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of(key))
    for k in range(3):
        x = rng.randrange(-S, S)
        d.line([x, S, x + S, 0], fill=blend(sky_top, (255, 255, 255), 0.25), width=rng.randint(1, 3))
    if mullion:
        d.line([0, 0, 0, S - 1], fill=frame, width=2)
        d.line([0, S - 1, S - 1, S - 1], fill=frame, width=1)
    return img


def facade_textures():
    sky_top, sky_bottom = (150, 178, 205), (88, 112, 140)
    # Curtain glass: the sky in tinted glass, aluminium mullions; spandrels of dark glass at each floor
    frame = (60, 66, 74, 255)
    save(glass_pane(sky_top, sky_bottom, frame, "glasswin"), "facade-glass-window")
    lit = texlib.vertical_gradient((250, 236, 196), (214, 196, 150))
    d = ImageDraw.Draw(lit)
    d.rectangle([0, 0, S - 1, 3], fill=(255, 252, 236, 255))  # the ceiling lights of the office inside
    for x in (6, 20):
        d.rectangle([x, 22, x + 7, 31], fill=(120, 110, 96, 255))  # a desk partition
    d.line([0, 0, 0, S - 1], fill=frame, width=2)
    d.line([0, S - 1, S - 1, S - 1], fill=frame)
    save(lit, "facade-glass-lit")
    blinds = glass_pane((176, 182, 188), (150, 156, 162), frame, "glassblinds")
    d = ImageDraw.Draw(blinds)
    for y in range(1, S - 1, 3):
        d.line([2, y, S - 1, y], fill=(196, 198, 196, 255))
    save(blinds, "facade-glass-blinds")
    spandrel = texlib.vertical_gradient((52, 64, 80), (40, 48, 60))
    d = ImageDraw.Draw(spandrel)
    d.line([0, 0, 0, S - 1], fill=frame, width=2)
    d.line([0, 0, S - 1, 0], fill=frame, width=2)
    d.line([0, S - 1, S - 1, S - 1], fill=frame, width=2)
    save(spandrel, "facade-glass-band")
    save(spandrel, "facade-glass-wall")
    save(speckle(Image.new("RGBA", (S, S), (70, 76, 84, 255)), 4, "glasspier"), "pier-glass")

    # Mirror glass: black, dull, giving back a dim and wrong reflection of the street. They never open. Each block is a
    # pane in a thin mullion grid, and no two neighbours quite match (MIRROR_ALTERNATES, picked at random by the game):
    # a plain pane, a faint sheen across one at a different place each time, a lighter one holding a band of the street
    # opposite, a darker one. A single streak baked into every pane tiled a whole tower into a quilt
    def mirror_pane(top, bottom, key, sheen=None, band=None):
        img = texlib.vertical_gradient(top, bottom)
        if sheen is not None:
            px = img.load()
            for y in range(S):
                for x in range(S):
                    t = max(0.0, 1 - abs(x + y - sheen) / 5.0) * 7
                    r_, g_, b_, a_ = px[x, y]
                    px[x, y] = (int(r_ + t), int(g_ + t), int(b_ + t * 1.3), a_)
        d = ImageDraw.Draw(img)
        if band is not None:
            d.rectangle([1, band, S - 1, band + 3], fill=tuple(int(v * 0.5 + 0.5 * w) for v, w in zip(bottom, (44, 46, 54))) + (255,))
        d.line([0, 0, 0, S - 1], fill=(8, 8, 10, 255))
        d.line([1, 0, S - 1, 0], fill=(10, 10, 13, 255))
        save(img, key)
        return img

    mirror = mirror_pane((30, 31, 37), (17, 17, 22), "facade-mirror-wall")
    for part in ("window", "lit", "blinds"):
        save(mirror, f"facade-mirror-{part}")
    mirror_pane((30, 31, 37), (17, 17, 22), "facade-mirror-alt1", sheen=22)
    mirror_pane((34, 35, 42), (21, 21, 27), "facade-mirror-alt2", band=19)
    mirror_pane((25, 26, 31), (14, 14, 18), "facade-mirror-alt3", sheen=40)
    band = Image.new("RGBA", (S, S), (14, 14, 18, 255))
    d = ImageDraw.Draw(band)
    d.line([0, 0, S - 1, 0], fill=(36, 36, 42, 255))
    d.line([0, S - 1, S - 1, S - 1], fill=(36, 36, 42, 255))
    save(band, "facade-mirror-band")
    save(speckle(Image.new("RGBA", (S, S), (10, 10, 13, 255)), 2, "mirrorpier"), "pier-mirror")

    # Brick, red and dark: a band of stone at each floor
    for style, base, mortar in (("brick", 0xA2482E, 0xB8AC98), ("brickdark", 0x5E3A30, 0x8E8678)):
        wall = bricks(base, mortar, style)
        save(wall, f"facade-{style}-wall")
        save(wall, f"pier-{style}")
        b = wall.copy()
        d = ImageDraw.Draw(b)
        d.rectangle([0, 0, S - 1, 5], fill=(196, 188, 170, 255))
        d.line([0, 5, S - 1, 5], fill=(120, 112, 100, 255))
        save(b, f"facade-{style}-band")

    # Limestone: big ashlar blocks, a moulded cornice at each floor
    stone = noise(0xCFC2A2, 5, "limestone")
    d = ImageDraw.Draw(stone)
    for y in (0, 16):
        d.line([0, y, S - 1, y], fill=(170, 160, 136, 255))
    d.line([10, 0, 10, 15], fill=(170, 160, 136, 255))
    d.line([26, 16, 26, 31], fill=(170, 160, 136, 255))
    save(stone, "facade-stone-wall")
    pier = stone.copy()
    d = ImageDraw.Draw(pier)
    for y in (7, 23):
        d.line([0, y, S - 1, y], fill=(176, 166, 140, 255))  # rustication
    save(pier, "pier-stone")
    cornice = noise(0xD6CAAA, 4, "cornice")
    d = ImageDraw.Draw(cornice)
    d.rectangle([0, 0, S - 1, 4], fill=(232, 224, 204, 255))
    d.rectangle([0, 5, S - 1, 7], fill=(150, 140, 116, 255))
    for x in range(1, S, 4):
        d.rectangle([x, 8, x + 1, 11], fill=(186, 176, 150, 255))  # dentils
    d.line([0, 12, S - 1, 12], fill=(160, 150, 126, 255))
    save(cornice, "facade-stone-band")

    # Concrete: board-marked, with tie holes
    conc = noise(0x9A9892, 4, "cityconcrete")
    d = ImageDraw.Draw(conc)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=(138, 136, 130, 255))
    for x, y in ((6, 4), (22, 4), (6, 20), (22, 20)):
        d.point((x, y), fill=(80, 78, 74, 255))
    save(conc, "facade-concrete-wall")
    save(conc, "pier-concrete")
    band = noise(0xA6A49E, 3, "concband")
    ImageDraw.Draw(band).line([0, S - 3, S - 1, S - 3], fill=(96, 94, 90, 255), width=2)
    save(band, "facade-concrete-band")

    # The storefront fascia: a painted board over the glass, where the sign hangs
    fascia = noise(0x23392E, 3, "fascia")
    d = ImageDraw.Draw(fascia)
    d.rectangle([1, 1, S - 2, S - 2], outline=(176, 150, 90, 255))
    d.line([0, S - 1, S - 1, S - 1], fill=(14, 20, 16, 255), width=2)
    save(fascia, "cityfascia")
    roof = noise(0x3C3B3A, 8, "cityroof")
    T.save(speckle(roof, 14, "cityroof2"), "block/detail/cityroof.png")
    save(noise(0xE6DECC, 2, "cityplaster"), "cityplaster")

    # Stained glass: leaded panes of red, blue and gold, lit from inside
    rng = random.Random(1101)
    img = Image.new("RGBA", (S, S), (30, 26, 24, 255))
    d = ImageDraw.Draw(img)
    colours = [(170, 30, 40), (40, 70, 170), (210, 160, 40), (40, 120, 70), (120, 40, 130)]
    for y in range(1, S, 8):
        for x in range(1, S, 6):
            d.rectangle([x, y, x + 4, y + 6], fill=rng.choice(colours) + (255,))
    d.ellipse([9, 9, 22, 22], outline=(30, 26, 24, 255), width=2)
    save(img, "stainedglass")


def street_textures():
    asphalt = T.load("block/detail/asphalt.png") if hasattr(T, "load") else None
    if asphalt is None:
        asphalt = Image.open(os.path.join(ASSETS, "textures", "block", "detail", "asphalt.png")).convert("RGBA")
    yellow, white = (214, 176, 40, 255), (222, 222, 214, 255)
    img = asphalt.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([12, 0, 13, S - 1], fill=yellow)
    d.rectangle([18, 0, 19, S - 1], fill=yellow)
    save(img, "asphalt-doublens")
    save(img.rotate(90), "asphalt-doublewe")
    img = asphalt.copy()
    ImageDraw.Draw(img).rectangle([15, 0, 16, S - 1], fill=white)
    save(img, "asphalt-bayns")
    save(img.rotate(90), "asphalt-baywe")
    img = asphalt.copy()
    d = ImageDraw.Draw(img)
    d.rectangle([4, 6, 21, 19], fill=(58, 58, 60, 255))  # a patch
    for pts in ([(0, 24), (8, 21), (13, 26), (22, 23), (31, 28)], [(25, 0), (23, 7), (27, 13), (26, 18)]):
        d.line(pts, fill=(18, 18, 20, 255), width=1)
    save(img, "asphalt-cracked")

    # Granite pavers on the plazas; polished marble in the lobbies; painted concrete in the garages
    img = noise(0xB4B0A8, 6, "plaza")
    speckle(img, 10, "plaza2")
    d = ImageDraw.Draw(img)
    d.line([0, 0, S - 1, 0], fill=(130, 126, 120, 255))
    d.line([0, 0, 0, S - 1], fill=(130, 126, 120, 255))
    d.line([0, 16, S - 1, 16], fill=(140, 136, 130, 255))
    d.line([16, 0, 16, S - 1], fill=(140, 136, 130, 255))
    save(img, "cityfloor-plaza")
    marble = texlib.marble((226, 220, 206), (160, 150, 136), 1102, veins=1, sharpness=8, mottle=0.05)
    d = ImageDraw.Draw(marble)
    d.line([0, 0, S - 1, 0], fill=(190, 182, 168, 255))
    d.line([0, 0, 0, S - 1], fill=(190, 182, 168, 255))
    save(marble, "cityfloor-marble")
    garage = noise(0x8C8A86, 4, "garage")
    T.blotch(garage, (20, 12), 7, (40, 38, 36), 0.3, 1103)
    save(garage, "cityfloor-garage")

    # The subway: ballast, rails on their sleepers, the platform and its yellow edge, white tile, the dark ceiling
    ballast = noise(0x5A5652, 10, "ballast")
    speckle(ballast, 18, "ballast2")
    save(ballast, "subwayfloor-bed")
    platform = noise(0x8E8A84, 4, "platform")
    speckle(platform, 8, "platform2")
    save(platform, "subwayfloor-platform")
    edge = platform.copy()
    d = ImageDraw.Draw(edge)
    d.rectangle([0, 0, S - 1, S - 1], fill=(204, 168, 30, 255))
    for y in range(2, S, 5):
        for x in range(2, S, 5):
            d.ellipse([x, y, x + 2, y + 2], fill=(176, 142, 20, 255))
    save(edge, "subwayfloor-edge")
    tile = Image.new("RGBA", (S, S), (236, 236, 230, 255))
    d = ImageDraw.Draw(tile)
    for y in range(0, S, 8):
        d.line([0, y, S - 1, y], fill=(176, 176, 168, 255))
        off = 8 if (y // 8) % 2 else 0
        for x in range(off, S + 16, 16):
            d.line([x % S, y, x % S, y + 7], fill=(176, 176, 168, 255))
    T.blotch(tile, (8, 28), 6, (150, 140, 100), 0.18, 1104)
    save(tile, "subwaywall-tile")
    save(speckle(noise(0x4A4846, 3, "subwayceiling"), 6, "subwayceiling2"), "subwaywall-ceiling")
    rim = noise(0xBDB6A8, 4, "fountainrim")
    ImageDraw.Draw(rim).rectangle([0, 0, S - 1, 3], fill=(214, 208, 196, 255))
    save(rim, "fountainrim")

    # The barn wall in Level 10 that isn't quite there: the boards, but subtly out of true
    barn = Image.open(os.path.join(ASSETS, "textures", "block", "detail", "barnwall-red.png")).convert("RGBA")
    ghost = Image.new("RGBA", (S, S))
    ghost.paste(barn.crop((2, 0, S, S)), (0, 0))
    ghost.paste(barn.crop((0, 0, 2, S)), (S - 2, 0))
    img = Image.blend(barn, ghost, 0.45)
    d = ImageDraw.Draw(img)
    d.line([0, 13, S - 1, 13], fill=(170, 80, 70, 255))
    save(img, "barnwall-noclip")


def door_textures():
    # A rowhouse door: dark green panels, a glazed top, a brass knob and knocker, a transom over
    for part in ("lower", "upper"):
        img = noise(0x23402F, 3, "rowdoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 2, S - 1], fill=(200, 196, 186, 255))
        d.rectangle([S - 3, 0, S - 1, S - 1], fill=(200, 196, 186, 255))
        if part == "lower":
            d.rectangle([7, 4, 24, 26], outline=(16, 32, 22, 255), width=2)
            d.ellipse([22, 0, 26, 4], fill=(200, 160, 60, 255))
        else:
            d.rectangle([7, 12, 24, S - 1], fill=(40, 52, 60, 255))
            d.rectangle([7, 12, 24, S - 1], outline=(16, 32, 22, 255), width=2)
            d.rectangle([3, 0, S - 4, 6], fill=(60, 72, 84, 255))  # the transom
            d.ellipse([14, 14, 18, 18], fill=(200, 160, 60, 255))
        save(img, f"rowhousedoor-{part}")
    # Steel doors: grey, with a stencilled word (the basement door is a model now, l11art: it brings its own)
    for code, color, label, sign in (("substationdoor", 0x6A6E68, None, "danger"),
                                     ("maintenancedoor", 0x5E6A62, "AUTHORIZED\nPERSONNEL", None)):
        for part in ("lower", "upper"):
            img = noise(color, 3, code + part)
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, S - 1, S - 1], outline=shade(T.hexrgb(color), 0.7), width=2)
            if part == "lower":
                d.rectangle([22, 0, 27, 3], fill=(180, 180, 176, 255))  # the handle
                d.rectangle([4, 24, S - 5, 28], fill=shade(T.hexrgb(color), 0.85))  # kick plate
            elif sign == "danger":
                d.rectangle([4, 6, S - 5, 24], fill=(236, 200, 30, 255))
                text(img, "DANGER", (5, 7, S - 5, 14), 0x101010, 6)
                text(img, "HIGH VOLTAGE", (4, 15, S - 4, 23), 0x101010, 4)
            elif label:
                for k, line in enumerate(label.split("\n")):
                    text(img, line, (2, 6 + k * 8, S - 2, 14 + k * 8), 0xE8E4D8, 5 if len(line) > 8 else 6)
            save(img, f"{code}-{part}")


def sign(code, words, bg, fg, border=None, size=8, glyph=None):
    img = Image.new("RGBA", (S, S), rgb(bg))
    d = ImageDraw.Draw(img)
    if border:
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(border), width=1)
    lines = words.split("\n")
    h = (S - 6) // len(lines)
    for k, line in enumerate(lines):
        text(img, line, (1, 3 + k * h, S - 1, 3 + (k + 1) * h), fg, size if len(line) <= 6 else max(4, size - 2 - (len(line) - 6) // 2))
    if glyph == "cross":
        d.rectangle([13, 2, 18, 13], fill=rgb(0x2ACC4A))
        d.rectangle([10, 5, 21, 10], fill=rgb(0x2ACC4A))
    if glyph == "p":
        d.rectangle([2, 2, 12, 12], fill=rgb(0x1C4AB0))
        text(img, "P", (2, 2, 12, 12), 0xFFFFFF, 9)
    save(img, code)


def sign_wide(code, lines, bg, fg, border=None, glyph=None):
    """The sign over a two-wide door: twice the width of the one-block sign, so the name fits on one line at a size
    that reads from the street. `lines` are (words, size) pairs; `glyph` is drawn in a square at the left."""
    w, h = 2 * S, S
    img = Image.new("RGBA", (w, h), rgb(bg))
    d = ImageDraw.Draw(img)
    if border:
        d.rectangle([0, 0, w - 1, h - 1], outline=rgb(border), width=1)
    x0 = 2
    if glyph == "cross":
        d.rectangle([8, 8, 13, 23], fill=rgb(0x2ACC4A))
        d.rectangle([3, 13, 18, 18], fill=rgb(0x2ACC4A))
        x0 = 20
    if glyph == "p":
        d.rectangle([3, 7, 20, 24], fill=rgb(0x1C4AB0))
        text(img, "P", (3, 7, 21, 25), 0xFFFFFF, 15)
        x0 = 22
    row = (h - 4) // len(lines)
    for k, (words, size) in enumerate(lines):
        text(img, words, (x0, 2 + k * row, w - 2, 2 + (k + 1) * row), fg, size)
    save(img, code + "-wide")


def sign_textures():
    sign("signdiner", "DINER\nOPEN 24 HRS", 0x181418, 0xFF4A5A, border=0x606060)
    sign("signgrocery", "GROCERY", 0x1C3A24, 0xF2E8C8, border=0xC8B060)
    sign("signbodega", "BODEGA\nDELI", 0xC8381E, 0xFFF0C8)
    sign("signpharmacy", "\nPHARMACY", 0xF4F4F0, 0x1A7A3A, glyph="cross")
    sign("signfarmacia", "\nFARMACIA", 0xF4F4F0, 0x1A7A3A, glyph="cross")
    sign("signhardware", "HARDWARE\nTOOLS", 0xB01818, 0xFFFFFF)
    sign("signlaundry", "LAUNDRO\nMAT", 0x1A3A8A, 0xFFFFFF)
    sign("signlavanderia", "LAVAN\nDERIA", 0x1A3A8A, 0xFFE860)
    sign("signclothing", "CLOTHING", 0x101010, 0xE8D8B0, border=0xB0A070)
    sign("signhotel", "HOTEL", 0x4A0E14, 0xE8C060, border=0xE8C060)
    sign("signoffices", "1100", 0x2A2620, 0xC8A060, border=0x5A5040, size=9)
    sign("signapartments", "THE\nARMS", 0x1C2A24, 0xE8E0C8)
    sign("signparking", "   PARK\n   ING", 0xF0F0F0, 0x1C4AB0, glyph="p")
    sign("signmuseum", "MUSEUM", 0xD8CCAA, 0x3A3020, border=0x9A8E70)
    # The same signs made for a two-wide door, to hang centred over it in two halves (storefrontsign)
    sign_wide("signdiner", [("DINER", 13), ("OPEN 24 HRS", 7)], 0x181418, 0xFF4A5A, border=0x606060)
    sign_wide("signgrocery", [("GROCERY", 12)], 0x1C3A24, 0xF2E8C8, border=0xC8B060)
    sign_wide("signbodega", [("BODEGA", 12), ("DELI", 9)], 0xC8381E, 0xFFF0C8)
    sign_wide("signpharmacy", [("PHARMACY", 7)], 0xF4F4F0, 0x1A7A3A, glyph="cross")
    sign_wide("signfarmacia", [("FARMACIA", 7)], 0xF4F4F0, 0x1A7A3A, glyph="cross")
    sign_wide("signhardware", [("HARDWARE", 10), ("TOOLS", 9)], 0xB01818, 0xFFFFFF)
    sign_wide("signlaundry", [("LAUNDROMAT", 9)], 0x1A3A8A, 0xFFFFFF)
    sign_wide("signlavanderia", [("LAVANDERIA", 9)], 0x1A3A8A, 0xFFE860)
    sign_wide("signclothing", [("CLOTHING", 11)], 0x101010, 0xE8D8B0, border=0xB0A070)
    sign_wide("signhotel", [("HOTEL", 14)], 0x4A0E14, 0xE8C060, border=0xE8C060)
    sign_wide("signoffices", [("1100", 14)], 0x2A2620, 0xC8A060, border=0x5A5040)
    sign_wide("signapartments", [("THE ARMS", 11)], 0x1C2A24, 0xE8E0C8)
    sign_wide("signparking", [("PARKING", 8)], 0xF0F0F0, 0x1C4AB0, glyph="p")
    sign_wide("signmuseum", [("MUSEUM", 12)], 0xD8CCAA, 0x3A3020, border=0x9A8E70)

    # Inside: a bank of brass mailboxes, a felt letter board, a missing person poster
    img = Image.new("RGBA", (S, S), rgb(0x6A5430))
    d = ImageDraw.Draw(img)
    for y in range(1, S, 8):
        for x in range(1, S, 8):
            d.rectangle([x, y, x + 6, y + 6], fill=rgb(0xB8923A))
            d.rectangle([x + 1, y + 1, x + 5, y + 2], fill=rgb(0x3A2E1C))
            d.point((x + 5, y + 5), fill=rgb(0x2A2014))
    save(img, "mailboxes")
    img = Image.new("RGBA", (S, S), rgb(0xF0ECDC))
    d = ImageDraw.Draw(img)
    text(img, "MISSING", (2, 1, S - 2, 9), 0xC01818, 7)
    d.rectangle([10, 10, 21, 22], fill=rgb(0x8A8278))
    d.ellipse([13, 11, 18, 17], fill=rgb(0xC8B49A))
    text(img, "HAVE YOU SEEN ME", (1, 23, S - 1, 31), 0x202020, 4)
    save(img, "missingposter")

    # The museum's paintings, each of another level: the Lobby, the car park, the pipes, the office, the hotel,
    # the sea under its ceiling, a suburban street at night, a field under a grey sky
    def canvas(fill):
        return Image.new("RGBA", (S, S), fill + (255,))

    pics = []
    p = canvas((196, 178, 96))  # Level 0
    d = ImageDraw.Draw(p)
    d.rectangle([0, 22, S - 1, S - 1], fill=(150, 128, 70, 255))
    d.rectangle([12, 8, 19, 22], fill=(90, 76, 40, 255))
    for x in (4, 26):
        d.rectangle([x, 0, x + 3, 2], fill=(255, 250, 220, 255))
    pics.append(p)
    p = canvas((120, 120, 116))  # Level 1
    d = ImageDraw.Draw(p)
    for x in (4, 16, 28):
        d.rectangle([x - 2, 6, x + 1, 26], fill=(150, 150, 144, 255))
    d.rectangle([0, 26, S - 1, S - 1], fill=(80, 80, 78, 255))
    d.rectangle([6, 22, 13, 26], fill=(150, 40, 40, 255))
    pics.append(p)
    p = canvas((40, 36, 32))  # Level 2
    d = ImageDraw.Draw(p)
    for y, c in ((6, (120, 70, 40)), (11, (90, 90, 86)), (16, (140, 60, 30))):
        d.rectangle([0, y, S - 1, y + 3], fill=c + (255,))
    d.ellipse([20, 24, 24, 28], fill=(255, 180, 90, 255))
    pics.append(p)
    p = canvas((150, 150, 140))  # Level 4
    d = ImageDraw.Draw(p)
    for x in range(2, S, 9):
        d.rectangle([x, 16, x + 6, 26], fill=(110, 112, 116, 255))
    d.rectangle([0, 0, S - 1, 4], fill=(220, 220, 214, 255))
    d.rectangle([22, 6, 30, 13], fill=(90, 110, 130, 255))
    pics.append(p)
    p = canvas((110, 24, 28))  # Level 5
    d = ImageDraw.Draw(p)
    d.polygon([(0, S), (12, 14), (19, 14), (S, S)], fill=(150, 40, 36, 255))
    d.rectangle([13, 6, 18, 14], fill=(30, 10, 10, 255))
    d.ellipse([14, 1, 17, 4], fill=(255, 210, 120, 255))
    pics.append(p)
    p = canvas((60, 64, 70))  # Level 7
    d = ImageDraw.Draw(p)
    d.rectangle([0, 14, S - 1, S - 1], fill=(30, 70, 100, 255))
    for x in range(0, S, 8):
        d.line([x, 16, x + 5, 15], fill=(140, 170, 190, 255))
    d.rectangle([0, 0, S - 1, 3], fill=(90, 90, 92, 255))
    pics.append(p)
    p = canvas((14, 18, 36))  # Level 9
    d = ImageDraw.Draw(p)
    d.rectangle([0, 24, S - 1, S - 1], fill=(30, 30, 34, 255))
    d.polygon([(6, 16), (14, 9), (22, 16)], fill=(70, 40, 36, 255))
    d.rectangle([8, 16, 20, 24], fill=(150, 150, 140, 255))
    d.rectangle([12, 18, 14, 20], fill=(255, 210, 110, 255))
    d.line([27, 8, 27, 24], fill=(60, 60, 60, 255))
    d.ellipse([25, 6, 29, 9], fill=(255, 220, 140, 255))
    pics.append(p)
    p = canvas((176, 178, 178))  # Level 10
    d = ImageDraw.Draw(p)
    d.rectangle([0, 16, S - 1, S - 1], fill=(206, 176, 80, 255))
    for x in range(0, S, 3):
        d.line([x, 16, x + 1, 13], fill=(220, 190, 90, 255))
    d.rectangle([24, 10, 28, 16], fill=(150, 40, 30, 255))
    pics.append(p)
    for i, pic in enumerate(pics):
        framed = Image.new("RGBA", (S, S), (150, 118, 46, 255))
        framed.paste(pic.resize((S - 6, S - 6)), (3, 3))
        ImageDraw.Draw(framed).rectangle([0, 0, S - 1, S - 1], outline=(100, 74, 24, 255))
        save(framed, f"gallery{i}")

    # The subway: the station's name, a map of lines going nowhere, a faded advertisement, a caged lamp
    img = Image.new("RGBA", (S, S), rgb(0x141414))
    text(img, "11 ST", (1, 4, S - 1, 16), 0xFFFFFF, 9)
    d = ImageDraw.Draw(img)
    for x, c in ((6, 0xE03A2A), (14, 0x2A6AE0), (22, 0xF0B020)):
        d.ellipse([x, 20, x + 6, 26], fill=rgb(c))
    save(img, "stationsign")
    img = Image.new("RGBA", (S, S), rgb(0xF2F0E8))
    d = ImageDraw.Draw(img)
    for pts, c in (([(2, 6), (14, 6), (20, 14), (30, 14)], 0xE03A2A), ([(4, 30), (10, 18), (10, 4)], 0x2A6AE0),
                   ([(2, 22), (16, 22), (24, 28), (30, 28)], 0x3AA040), ([(18, 2), (18, 30)], 0xF0B020)):
        d.line(pts, fill=rgb(c), width=2)
    for x, y in ((10, 6), (10, 18), (18, 14), (18, 22)):
        d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=rgb(0x101010))
    save(img, "subwaymap")
    img = Image.new("RGBA", (S, S), rgb(0x8AB8C8))
    d = ImageDraw.Draw(img)
    d.rectangle([11, 9, 20, 26], fill=rgb(0xF4ECD8))
    d.rectangle([13, 6, 18, 9], fill=rgb(0xE8E0CC))
    text(img, "ALMOND", (1, 0, S - 1, 6), 0x203040, 5)
    text(img, "STAY HYDRATED", (0, 26, S, S), 0x203040, 3)
    T.blotch(img, (26, 6), 6, (200, 196, 186), 0.5, 1105)  # faded and peeling
    save(img, "subwayad")
    img = Image.new("RGBA", (S, S), (255, 238, 196, 255))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 6):
        d.line([x, 0, x, S - 1], fill=(60, 56, 50, 255))
    save(img, "subwaylampglass")


def prop_textures():
    def flat(code, c, n=4):
        save(noise(c, n, code), code)

    flat("binsgreen", 0x2C5A34, 5)
    flat("trafficyellow", 0xD0A21C, 4)
    flat("streetgreen", 0x1E6A3A, 2)
    flat("pewwood", 0x5A3A22, 5)
    flat("tankwood", 0x6E5236, 7)
    flat("acgrey", 0xA4A6A2, 3)
    flat("postblue", 0x1E3A7A, 3)
    flat("cartwire", 0xB8BCC0, 6)
    flat("trashbag", 0x141618, 4)
    flat("canopy", 0xE8E2D2, 3)
    flat("cartsteel", 0xC8CCCE, 4)
    for code, c in (("fabric0", 0x8A2A2A), ("fabric1", 0x2A4A8A), ("fabric2", 0xC8B490), ("fabric3", 0x3A3A3A)):
        flat(code, c, 6)

    def lens(code, on, c):
        img = Image.new("RGBA", (S, S), (12, 12, 12, 255))
        d = ImageDraw.Draw(img)
        d.ellipse([4, 4, 27, 27], fill=(c if on else tuple(v // 6 for v in c)) + (255,))
        if on:
            d.ellipse([8, 8, 15, 15], fill=tuple(min(255, v + 80) for v in c) + (255,))
        save(img, code)

    lens("lens-red", True, (230, 30, 20))
    lens("lens-amber", True, (240, 160, 20))
    lens("lens-off", False, (160, 160, 150))
    img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
    text(img, "W 11 ST", (1, 6, S - 1, 26), 0xFFFFFF, 7)
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFFFFF))
    save(img, "streetsign-st")
    img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
    text(img, "AVENIDA 11", (0, 6, S, 26), 0xFFFFFF, 6)
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=rgb(0xFFFFFF))
    save(img, "streetsign-ave")
    img = Image.new("RGBA", (S, S), rgb(0xC8C8C0))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, 27, 20], fill=rgb(0x2A3A2A))
    d.line([16, 14, 22, 8], fill=rgb(0xD02020), width=1)
    text(img, "EXPIRED", (2, 22, S - 2, 30), 0xD02020, 5)
    save(img, "meterface")
    img = Image.new("RGBA", (S, S), rgb(0x1A3A8A))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, S - 4, 18], fill=rgb(0xD8D0B8))
    text(img, "NEWS", (3, 4, S - 4, 12), 0x101010, 6)
    for y in range(13, 18, 2):
        d.line([5, y, S - 6, y], fill=rgb(0x606060))
    d.rectangle([10, 22, 21, 24], fill=rgb(0x606060))
    save(img, "newsfront")
    img = Image.new("RGBA", (S, S), rgb(0xC8CCCE))
    d = ImageDraw.Draw(img)
    d.rectangle([2, 4, S - 3, 26], fill=rgb(0xF4ECD8))
    text(img, "ALMOND", (3, 5, S - 3, 14), 0x8A3A1A, 6)
    text(img, "WATER $1", (2, 15, S - 2, 25), 0x203040, 5)
    save(img, "cartfront")
    img = Image.new("RGBA", (S, S), rgb(0xE8E2D2))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.rectangle([x, 0, x + 3, S - 1], fill=rgb(0x2A7A4A))
    save(img, "umbrella")
    img = Image.new("RGBA", (S, S), (190, 206, 214, 255))
    d = ImageDraw.Draw(img)
    d.line([0, 26, 26, 0], fill=(220, 232, 238, 255), width=2)
    d.rectangle([0, 0, S - 1, S - 1], outline=(90, 96, 100, 255))
    save(img, "shelterglass")
    img = Image.new("RGBA", (S, S), rgb(0x203040))
    d = ImageDraw.Draw(img)
    d.rectangle([3, 3, S - 4, S - 4], fill=rgb(0xE8DEC8))
    text(img, "ALMOND", (4, 6, S - 4, 14), 0x8A3A1A, 6)
    text(img, "WATER", (4, 14, S - 4, 22), 0x8A3A1A, 6)
    d.rectangle([12, 22, 19, 27], fill=rgb(0x8AB8C8))
    save(img, "shelterad")
    img = Image.new("RGBA", (S, S), rgb(0x4A4E52))
    d = ImageDraw.Draw(img)
    for k in range(0, S, 4):
        d.line([k, 0, k, S - 1], fill=rgb(0x2A2C2E))
        d.line([0, k, S - 1, k], fill=rgb(0x2A2C2E))
    d.ellipse([6, 6, 25, 25], outline=rgb(0x1A1A1A), width=2)
    save(img, "acgrille")
    flat("dumpsterlid", 0x1C1E20, 3)


# The billboards on the brick roofs and the advertising pillars on the corners (the lore's "advertising pillars and
# billboards"): the same few brands as the rest of the city, sun-faded, and one billboard stripped to its last shreds
BILLBOARDS = ["almond", "city", "diner", "stripped"]
PILLARS = ["a", "b", "c"]


def poster_textures():
    def faded(img, key, amount=0.18):
        """Sun and rain: the colours washed toward paper, a few streaks down from the top."""
        rng = random.Random(seed_of(key))
        px = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                f = amount + rng.uniform(0, 0.05)
                px[x, y] = (int(r + (226 - r) * f), int(g + (220 - g) * f), int(b + (204 - b) * f), a)
        for _ in range(w // 16):
            x = rng.randrange(w)
            for y in range(rng.randrange(h // 3, h)):
                r, g, b, a = px[x, y]
                px[x, y] = (int(r + (214 - r) * 0.3), int(g + (208 - g) * 0.3), int(b + (192 - b) * 0.3), a)
        return img

    W, H = 3 * S, S + S // 2  # a billboard's poster: three blocks by a block and a half
    img = texlib.vertical_gradient((150, 196, 214), (104, 160, 188)).resize((W, H))
    d = ImageDraw.Draw(img)
    d.rectangle([62, 8, 80, 44], fill=rgb(0xF4ECD8))
    d.rectangle([66, 3, 76, 8], fill=rgb(0xE8E0CC))
    d.rectangle([65, 0, 77, 3], fill=rgb(0x2A6A9A))
    d.rectangle([64, 20, 78, 32], fill=rgb(0x8AB8C8))
    text(img, "ALMOND", (3, 4, 60, 22), 0x203040, 13)
    text(img, "WATER", (3, 20, 60, 36), 0x203040, 13)
    text(img, "STAY HYDRATED", (2, 36, 60, 46), 0x8A3A1A, 6)
    save(faded(img, "bb-almond"), "billboard-almond")
    img = texlib.vertical_gradient((24, 30, 64), (60, 54, 96)).resize((W, H))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("bb-city"))
    x = 0
    while x < W:
        bw, bh = rng.randint(4, 9), rng.randint(10, 26)
        d.rectangle([x, H - bh, x + bw - 1, H - 1], fill=(16, 18, 34, 255))
        for wy in range(H - bh + 2, H - 2, 3):
            for wx in range(x + 1, x + bw - 1, 2):
                if rng.random() < 0.35:
                    d.point((wx, wy), fill=(250, 214, 120, 255))
        x += bw
    text(img, "THE CITY THAT", (4, 2, W - 4, 13), 0xF2D27A, 9)
    text(img, "NEVER SLEEPS", (4, 12, W - 4, 24), 0xF2D27A, 9)
    save(faded(img, "bb-city", 0.12), "billboard-city")
    img = Image.new("RGBA", (W, H), rgb(0xB82A24))
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 10, W - 1, H - 1], fill=rgb(0xF2E8C8))
    d.ellipse([70, 8, 90, 30], fill=rgb(0xF4F0E8))
    d.ellipse([74, 12, 86, 20], fill=rgb(0x5A3420))
    d.arc([86, 14, 94, 24], 270, 90, fill=rgb(0xF4F0E8), width=2)
    text(img, "EAT AT THE", (4, 3, 66, 14), 0xF2E8C8, 8)
    text(img, "DINER", (4, 13, 66, 36), 0xFFFFFF, 17)
    text(img, "OPEN 24 HRS  NEXT CORNER", (2, H - 10, W - 2, H), 0xB82A24, 6)
    save(faded(img, "bb-diner"), "billboard-diner")
    # Stripped: grey backing boards, the last strips of old posters pasted one over another
    img = Image.new("RGBA", (W, H), rgb(0x8A8A84))
    d = ImageDraw.Draw(img)
    for xx in range(0, W, 16):
        d.line([xx, 0, xx, H - 1], fill=rgb(0x74746E))
    rng = random.Random(seed_of("bb-stripped"))
    for c in (0xE8E0CC, 0x2A6A9A, 0xB82A24, 0xF2D27A):
        for _ in range(5):
            x0, y0 = rng.randrange(W - 10), rng.randrange(H - 6)
            d.polygon([(x0, y0), (x0 + rng.randint(6, 22), y0 + rng.randint(-2, 2)), (x0 + rng.randint(4, 18), y0 + rng.randint(4, 14)),
                       (x0 + rng.randint(-2, 3), y0 + rng.randint(3, 12))], fill=rgb(c))
    save(img, "billboard-stripped")
    save(noise(0x3A3C3E, 4, "billboardframe"), "billboardframe")

    # The advertising pillars: a column of posters pasted up one over another, one over the next, in the city's brands
    ph = 3 * S
    for k, posters in enumerate((
            [("ALMOND", "WATER", 0x8AB8C8, 0x203040), ("DINER", "24 HRS", 0xB82A24, 0xF2E8C8), ("THE ARMS", "ROOMS", 0x1C2A24, 0xE8E0C8)],
            [("MUSEUM", "OPEN", 0xD8CCAA, 0x3A3020), ("HOTEL", "VACANCY", 0x4A0E14, 0xE8C060), ("LAUNDRO", "MAT", 0x1A3A8A, 0xFFFFFF)],
            [("CINEMA", "TONIGHT", 0x181418, 0xF2D27A), ("MISSING", "?", 0xF0ECDC, 0xC01818), ("BODEGA", "DELI", 0xC8381E, 0xFFF0C8)])):
        img = Image.new("RGBA", (S, ph), rgb(0xD8D2C0))
        d = ImageDraw.Draw(img)
        for n, (top, bottom, bg, fg) in enumerate(posters):
            y0 = 2 + n * S
            d.rectangle([1, y0, S - 2, y0 + S - 4], fill=rgb(bg))
            text(img, top, (2, y0 + 3, S - 2, y0 + 13), fg, 6 if len(top) > 6 else 7)
            text(img, bottom, (2, y0 + 14, S - 2, y0 + 24), fg, 5 if len(bottom) > 6 else 6)
            # A torn corner, the poster under it showing through
            d.polygon([(S - 2, y0 + S - 10), (S - 2, y0 + S - 4), (S - 8, y0 + S - 4)], fill=rgb(0xD8D2C0))
        save(faded(img, f"pillar-{k}", 0.1), f"adpillar-{PILLARS[k]}")
    save(noise(0x24503A, 3, "pillargreen"), "pillargreen")


# ======================= Graphics pass B12 =======================
# (B12) Level 11 brought toward the vanilla standard. The painters below run after the old ones and redraw a family
# under the old keys (and a few new ones), so a family goes back to main's look by dropping its call from
# generate_textures (and, for the façades, bands, subway rails and the traffic light, the matching (B12) model in
# facades(), decorations() or props()). Old tones are kept: each surface is shifted to the old texture's mean colour.

OLD_MEAN = {  # each family's mean colour before B12, measured on main's PNGs
    "facade-brick-wall": (168.6, 105.7, 82.0), "facade-brick-band": (171.6, 117.7, 95.0),
    "facade-brickdark-wall": (106.5, 81.6, 70.5), "facade-brickdark-band": (120.4, 98.2, 86.1),
    "facade-concrete-wall": (151.7, 149.7, 143.7), "facade-concrete-band": (161.7, 159.7, 153.9),
    "facade-glass-window": (115.8, 139.4, 164.8), "facade-glass-band": (47.5, 56.9, 69.9),
    "facade-glass-lit": (203.2, 191.6, 160.6), "facade-glass-blinds": (166.9, 171.6, 175.2),
    "facade-stone-wall": (203.6, 190.8, 159.6), "facade-stone-band": (207.4, 196.4, 167.7),
    "pier-glass": (69.6, 75.6, 83.6), "pier-mirror": (9.5, 9.5, 12.5), "pier-stone": (201.7, 189.2, 158.3),
    "cityfascia": (50.3, 66.3, 50.0), "cityroof": (59.6, 58.6, 57.6), "cityplaster": (230.0, 222.0, 204.0),
    "cityfloor-marble": (217.9, 211.5, 197.5), "cityfloor-plaza": (174.2, 170.2, 162.4),
    "subwayfloor-bed": (90.1, 86.1, 82.1), "subwayfloor-edge": (199.1, 163.4, 28.2),
    "subwayfloor-platform": (141.2, 137.2, 131.2), "subwaywall-ceiling": (73.7, 71.7, 69.7),
    "subwaywall-tile": (224.7, 224.6, 218.0), "fountainrim": (192.2, 185.3, 171.5),
    "billboardframe": (58.0, 60.0, 62.0), "pillargreen": (36.0, 80.0, 58.0), "binsgreen": (43.9, 89.9, 51.9),
    "trafficyellow": (208.0, 162.0, 28.0), "streetgreen": (30.0, 106.0, 58.0), "postblue": (30.1, 58.1, 122.1),
    "acgrey": (164.0, 166.0, 162.0), "cartsteel": (200.0, 204.0, 206.0), "dumpsterlid": (28.0, 30.0, 32.0),
    "pewwood": (90.0, 58.0, 34.0), "tankwood": (110.0, 82.0, 54.0),
}


def matched(img, ref, key=None):
    """img shifted to the old mean colour of `ref`; versions drawn under one `key` share one shift (B6)."""
    return T.match_rgb(img, OLD_MEAN[ref], key="city:" + (key or ref))


# Crisp pixel lettering for small signs (B9's lesson: text scaled below 10 px smears): a 5 x 7 face and a 3 x 5 one
CITY_F5 = {
    "A": "01110 10001 10001 11111 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110", "D": "11110 10001 10001 10001 10001 10001 11110",
    "E": "11111 10000 10000 11110 10000 10000 11111", "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "111 010 010 010 010 010 111", "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001", "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101", "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110", "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110", "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010", "X": "10001 10001 01010 00100 01010 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "010 110 010 010 010 010 111",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11110 00001 00001 01110 00001 00001 11110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "$": "00100 01111 10100 01110 00101 11110 00100", "?": "01110 10001 00001 00010 00100 00000 00100",
    "-": "0000 0000 0000 1111 0000 0000 0000", ".": "0 0 0 0 0 0 1", " ": "000 000 000 000 000 000 000",
}
CITY_F3 = {
    "A": "010 101 111 101 101", "B": "110 101 110 101 110", "C": "011 100 100 100 011", "D": "110 101 101 101 110",
    "E": "111 100 110 100 111", "F": "111 100 110 100 100", "G": "011 100 101 101 011", "H": "101 101 111 101 101",
    "I": "111 010 010 010 111", "J": "001 001 001 101 010", "K": "101 101 110 101 101", "L": "100 100 100 100 111",
    "M": "101 111 111 101 101", "N": "110 101 101 101 101", "O": "010 101 101 101 010",
    "P": "110 101 110 100 100", "Q": "010 101 101 110 011", "R": "110 101 110 101 101", "S": "011 100 010 001 110",
    "T": "111 010 010 010 010", "U": "101 101 101 101 111", "V": "101 101 101 101 010", "W": "101 101 111 111 101",
    "X": "101 101 010 101 101", "Y": "101 101 010 010 010", "Z": "111 001 010 100 111",
    "0": "111 101 101 101 111", "1": "010 110 010 010 111", "2": "110 001 010 100 111", "3": "110 001 010 001 110",
    "4": "101 101 111 001 001", "5": "111 100 110 001 110", "6": "011 100 110 101 010", "7": "111 001 010 010 010",
    "8": "010 101 010 101 010", "9": "010 101 011 001 110", "$": "011 110 010 011 110", "?": "110 001 010 000 010",
    "-": "000 000 111 000 000", ".": "0 0 0 0 1", " ": "00 00 00 00 00",
}


def ptext_width(s, font=CITY_F5, scale=1, gap=1):
    return sum((len(font[ch].split()[0]) + gap) * scale for ch in s.upper()) - gap * scale


def ptext(img, s, x, y, col, font=CITY_F5, scale=1, gap=1):
    """Draws `s` in a pixel face at (x, y), each lit pixel `col` (an RGB tuple or a function of the old pixel)."""
    p = img.load()
    w, h = img.size
    for ch in s.upper():
        rows = font[ch].split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit != "1":
                    continue
                for dy in range(scale):
                    for dx in range(scale):
                        X, Y = x + c * scale + dx, y + r * scale + dy
                        if 0 <= X < w and 0 <= Y < h:
                            p[X, Y] = M.rgba(col(p[X, Y]) if callable(col) else col)
        x += (len(rows[0]) + gap) * scale
    return x


def ptext_c(img, s, y, col, font=CITY_F5, scale=1, gap=1, x0=0, x1=None):
    x1 = img.size[0] if x1 is None else x1
    return ptext(img, s, x0 + (x1 - x0 - ptext_width(s, font, scale, gap) + 1) // 2, y, col, font, scale, gap)


def painted_board(key, colour, chips=3, grain=3, mottle=4, grime_amt=0.08):
    """Paint on a prop's metal or board, in its old colour: an even, slightly orange-peel coat, a few worn spots and a
    little dirt (matlib.painted_metal without a panel edge, since props show the texture from its corner)."""
    img = M.painted_metal(seed_of("b12" + key), base=colour, grain=grain, mottle=mottle, panel=False, chips=chips)
    if grime_amt:
        M.grime(img, grime_amt, seed_of("b12g" + key), cells=(8, 4), cover=0.45)
    return img


# ---- Façades ----

BRICK = {"brick": ((152, 78, 60), (182, 172, 156), (232, 228, 218)), "brickdark": ((100, 62, 48), (150, 138, 120), (44, 58, 52))}
FRAME = {"brick": "cityframe-white", "brickdark": "cityframe-green", "stone": "cityframe-bronze", "concrete": "cityframe-alu"}
# The panes behind the modelled sash windows (B12): three reflections each, picked at random by the game
PANE_VERSIONS = 3


def b12_brick():
    """Brick in running bond at the old units (8 x 4 px with the joint): each brick its own shade and hue, a lit top
    and a shaded foot, the mortar raked back. Three versions differ only in which bricks are darker (matlib.brick
    tones), so they mix without a patchwork; the piers take the first. The band is the brick with a stone string
    course along its top, which the band block's model brings forward (facades())."""
    for style, (base, mortar, _) in BRICK.items():
        seed = seed_of("b12brick" + style)
        vers = []
        for k in range(3):
            img = M.brick(seed=seed, base=base, mortar=mortar, course=4, length=8, mortar_w=1, jitter=13, hue=5,
                          recess=1.0, pits=0.02, grain=4, mottle=5, tones=None if k == 0 else seed + 101 * k)
            vers.append(matched(img, f"facade-{style}-wall"))
        for k, img in enumerate(vers):
            save(img, f"facade-{style}-wall" + (f"-{k + 1}" if k else ""))
        save(vers[0], f"pier-{style}")
        band = vers[0].copy()
        stone = M.noise_hv((200, 192, 174) if style == "brick" else (164, 158, 146), 3, seed_of("b12course" + style), S, 4, (8, 4), hue=1.0)
        p, q = band.load(), stone.load()
        for y in range(6):
            for x in range(S):
                p[x, y] = q[x, y]
        for x0 in (0, 16):  # two stones to the block, each bevelled, a joint between
            M.bevel(band, (x0 + 1, 0, x0 + 16, 6), 1, 0.16)
            for y in range(6):
                M.touch(band, x0, y, -0.2)
        for x in range(S):
            M.touch(band, x, 6, -0.3)  # the course's shadow on the brick under it
            M.touch(band, x, 7, -0.12)
        save(matched(band, f"facade-{style}-band"), f"facade-{style}-band")


def pane_texture(key, kind, glass, seed):
    """The glass of a modelled window, seen in its reveal: `kind` window (the sky and the street across, dark below,
    a soft sheen that wanders from version to version), lit (a room with its lights on and curtains drawn back) or
    blinds (slats, each lit along its top). Drawn at 32 px; the model shows its middle (about x 2..14 of the block)."""
    rng = random.Random(seed)
    top, bottom = glass
    if kind == "window":
        img = M.new(S, top)
        p = img.load()
        f = M.fbm(S, seed, (16, 8), 0.5)
        s0 = rng.uniform(4, 28)
        for y in range(S):
            for x in range(S):
                t = y / (S - 1)
                c = M.mix(top, bottom, t ** 0.8)
                d = f[y][x] * 5 + 9 * max(0.0, 1 - abs((x + 0.6 * y) % S - s0) / 6.0)
                p[x, y] = M.rgba(M.lift(c, d, 0.05))
        # the building across the street, a dark band low in the reflection
        yb = rng.randint(17, 22)
        for y in range(yb, S):
            for x in range(S):
                M.touch(img, x, y, -0.12)
        return img
    if kind == "lit":
        img = M.new(S, (236, 206, 150))
        p = img.load()
        for y in range(S):
            for x in range(S):
                c = M.mix((250, 232, 186), (214, 168, 108), (y / (S - 1)) ** 0.9)
                p[x, y] = M.rgba(M.lift(c, rng.uniform(-2, 2)))
        for y in range(0, 3):
            for x in range(8, 24):
                p[x, y] = M.rgba((255, 248, 226))  # the ceiling light
        curtain = (176, 74, 56)
        for x0, x1 in ((5, 10), (22, 27)):  # curtains drawn back, in folds
            for y in range(2, S):
                for x in range(x0, x1):
                    p[x, y] = M.rgba(M.lift(curtain, (6 if (x - x0) % 2 == 0 else -8) - y * 0.3))
        return img
    img = M.new(S, (214, 206, 188))
    p = img.load()
    for y in range(S):
        for x in range(S):
            k = y % 3
            p[x, y] = M.rgba(M.lift((214, 206, 188), (8 if k == 0 else -2 if k == 1 else -16) + rng.uniform(-1.5, 1.5)))
    return img


def frame_textures():
    """Painted window frames: white and dark green over wood (the brick styles), dark bronze (limestone), anodised
    aluminium (concrete), each with a faint grain along the member and a little dirt."""
    for key, colour, grain in (("cityframe-white", (226, 222, 210), 3), ("cityframe-green", (46, 60, 54), 3),
                               ("cityframe-bronze", (64, 56, 48), 3), ("cityframe-alu", (150, 152, 156), 2)):
        img = M.noise_hv(colour, grain, seed_of("b12" + key), S, 3, (8, 4), hue=1.0)
        f = M.fbm(S, seed_of("b12s" + key), (32, 4), 0.5)
        for y in range(S):
            for x in range(S):
                M.touch(img, x, y, f[y][x] * 0.03)
        M.grime(img, 0.06, seed_of("b12g" + key), cells=(8, 4), cover=0.4)
        save(img, key)


def b12_windows():
    """The panes of the brick, limestone and concrete windows (their frames and reveals are geometry, facades())."""
    glasses = {"brick": ((92, 104, 118), (26, 30, 38)), "brickdark": ((84, 96, 110), (22, 26, 32)),
               "stone": ((86, 96, 106), (22, 26, 30)), "concrete": ((118, 136, 154), (44, 54, 66))}
    for style, glass in glasses.items():
        for kind in ("window", "lit", "blinds"):
            for v in range(PANE_VERSIONS if kind == "window" else 1):
                img = pane_texture(None, kind, glass, seed_of(f"b12pane{style}{kind}{v}"))
                if kind == "lit" and style == "concrete":  # an office behind a ribbon window: no curtains
                    img = Image.open(os.path.join(ASSETS, "textures", "block", "detail", "facade-glass-lit.png")).convert("RGBA")
                if kind == "blinds" and style == "concrete":
                    img = M.noise_hv((200, 196, 186), 2, seed_of("b12vb"), S, 2, (8,))
                    for y in range(S):
                        for x in range(S):
                            M.touch(img, x, y, 0.05 if y % 3 == 0 else -0.08 if y % 3 == 2 else 0)
                save(img, f"citypane-{style}-{kind}" + (f"-{v + 1}" if v else ""))
    frame_textures()


def ashlar(seed, tones, base=(206, 194, 164)):
    """Limestone ashlar at the old courses (joints at 0 and 16, the vertical joints at x 10 and 26): each stone its own
    shade, a soft lit arris on top and left and a shaded one below and right, sunk joints, fine pores. `tones` seeds
    the shades only, so versions share every stone face."""
    img = M.noise_hv(base, 3, seed, S, 5, (16, 8, 4), hue=1.5)
    rng = random.Random(seed + 7)
    for _ in range(26):
        M.touch(img, rng.randrange(S), rng.randrange(S), -0.08)
    tr = random.Random(tones)
    for (y0, jx) in ((0, 10), (16, 26)):
        v = tr.uniform(-5, 5)
        for y in range(y0, y0 + 16):
            for x in range(S):
                M.touch(img, x, y, v / 200)
        for x in range(S):
            M.touch(img, x, y0, -0.17)
            M.touch(img, x, y0 + 1, 0.07)
            M.touch(img, x, y0 + 15, -0.06)
        for y in range(y0 + 1, y0 + 16):
            M.touch(img, jx, y, -0.17)
            M.touch(img, (jx + 1) % S, y, 0.05)
            M.touch(img, (jx - 1) % S, y, -0.05)
    return img


def b12_stone():
    """Limestone: ashlar walls in three versions; rusticated piers (a V-groove at every 8 px course, the stones
    staggered); the cornice's moulding (the band block's model brings it forward, facades())."""
    seed = seed_of("b12ashlar")
    for k in range(3):
        img = matched(ashlar(seed, seed + 31 * k), "facade-stone-wall")
        save(img, "facade-stone-wall" + (f"-{k + 1}" if k else ""))
    pier = M.noise_hv((204, 192, 162), 3, seed_of("b12pier"), S, 4, (16, 8), hue=1.5)
    for c in range(4):
        y0 = c * 8
        for x in range(S):
            M.touch(pier, x, y0, -0.24)
            M.touch(pier, x, y0 + 1, -0.08)
            M.touch(pier, x, y0 + 2, 0.08)
            M.touch(pier, x, y0 + 7, -0.06)
        jx = 10 if c % 2 == 0 else 26
        for y in range(y0 + 1, y0 + 8):
            M.touch(pier, jx, y, -0.2)
            M.touch(pier, jx + 1, y, 0.06)
    save(matched(pier, "pier-stone"), "pier-stone")
    # The band: ashlar under the cornice; the cornice texture (rows 0-4 the crown, a cyma lit at its top; rows 5-9
    # the dentil course; the rest plain stone for the soffits)
    band = ashlar(seed, seed)
    for x in range(S):
        for y, f in ((0, 0.08), (1, 0.04), (2, -0.1), (3, -0.18)):
            M.touch(band, x, y, f)
    save(matched(band, "facade-stone-band"), "facade-stone-band")
    cor = M.noise_hv((212, 202, 174), 3, seed_of("b12cornice"), S, 3, (8, 4), hue=1.0)
    for x in range(S):
        for y, f in ((0, 0.16), (1, 0.08), (2, 0.0), (3, -0.08), (4, -0.2), (5, 0.06), (9, -0.16), (10, -0.06)):
            M.touch(cor, x, y, f)
        for y in range(6, 9):
            if x % 4 in (2, 3):  # between the dentils, in shadow
                M.touch(cor, x, y, -0.26)
            elif x % 4 == 0:
                M.touch(cor, x, y, 0.06)
    save(matched(cor, "facade-stone-band", "cornice"), "citycornice")


def b12_concrete():
    """Board-marked concrete: a calm cement ground, the form boards' joints every 8 px with a little bleed, a faint
    grain along each board. Three versions on one ground: plain, a rust run from a tie hole, a lime
    bloom along a joint (the last two each one block in seven). (Round 2: the tie holes in every block read as a grid
    of square marks; one is left, above the rust run.) The band is a smooth precast spandrel with a drip
    groove under it; the ribbon windows between are geometry (facades())."""
    seed = seed_of("b12conc")
    base = (150, 148, 142)
    vers = []
    for k in range(3):
        img = M.concrete(seed=seed, base=base, grain=3, mottle=5, aggregate=0.015, pores=0.002, joints=(0, 8, 16, 24),
                         hue=1.0)
        f = M.fbm(S, seed_of("b12board"), (32, 2), 0.5)
        for y in range(S):
            for x in range(S):
                M.touch(img, x, y, f[y][x] * 0.025)
        for (x, y) in (((22, 4),) if k == 1 else ()):  # (round 2) one tie hole, in the rusty version only
            for dx, dy, v in ((0, 0, -0.22), (1, 0, -0.14), (0, 1, -0.14), (1, 1, -0.08), (0, 2, 0.05)):
                M.touch(img, x + dx, y + dy, v)
        if k == 1:
            x = 22  # a rust run down from the tie hole
            for i in range(10):
                M.put(img.load(), S, S, x, 7 + i, M.mix(img.load()[x, 7 + i], (132, 90, 58), 0.3 * (1 - i / 10) ** 0.7))
                if i in (3, 7):
                    x += 1
        if k == 2:
            for x in range(4, 28):
                M.touch(img, x, 17, 0.06 + 0.04 * math.sin(x * 0.9))
                if x % 3 == 0:
                    M.touch(img, x, 18, 0.05)
        vers.append(matched(img, "facade-concrete-wall", "concwall"))
    for k, img in enumerate(vers):
        save(img, "facade-concrete-wall" + (f"-{k + 1}" if k else ""))
    save(vers[0], "pier-concrete")
    band = M.concrete(seed=seed_of("b12concband"), base=(160, 158, 152), grain=2, mottle=4, aggregate=0.02, pores=0.01, hue=1.0)
    for x in range(S):
        M.touch(band, x, 0, 0.08)
        M.touch(band, x, 1, 0.03)
        M.touch(band, x, 28, -0.24)
        M.touch(band, x, 29, 0.08)
        M.touch(band, x, 31, -0.1)
    save(matched(band, "facade-concrete-band"), "facade-concrete-band")


def b12_glass():
    """The curtain wall: tinted glass holding the sky, a soft reflection of cloud and of the street across, in three
    versions (the old one had the same three streaks in every pane, a grid on a tower); an anodised mullion down the
    left (lit edge, shaded side) and a transom along the foot, with the gasket's shadow on the glass. The spandrel,
    the lit office and the blinds share the frame. Still cubes: a tower is thousands of panes."""
    sky_top, sky_bottom = (156, 182, 206), (90, 114, 142)
    frame_lit, frame, frame_dark = (112, 118, 126), (74, 80, 88), (46, 50, 56)

    def framed(img):
        p = img.load()
        for y in range(S):
            p[0, y] = M.rgba(frame_lit)
            p[1, y] = M.rgba(frame)
            M.touch(img, 2, y, -0.22)
        for x in range(S):
            p[x, S - 1] = M.rgba(frame_dark)
            M.touch(img, x, S - 2, -0.16)
        return img

    for k in range(3):
        img = M.new(S, sky_top)
        p = img.load()
        f = M.fbm(S, seed_of(f"b12cloud{k}"), (16, 8), 0.5)
        s0 = 6 + 9 * k
        for y in range(S):
            for x in range(S):
                c = M.mix(sky_top, sky_bottom, y / (S - 1))
                d = f[y][x] * 7 + 7 * max(0.0, 1 - abs((x + 0.5 * y) % S - s0) / 7.0)
                p[x, y] = M.rgba(M.lift(c, d, 0.04))
        yb = 20 + 3 * k  # the tower across the street, darker, low in the pane
        for y in range(yb, S):
            for x in range(S):
                M.touch(img, x, y, -0.1)
        save(matched(framed(img), "facade-glass-window", "glasswin"), "facade-glass-window" + (f"-{k + 1}" if k else ""))
    spandrel = M.new(S, (50, 62, 78))
    p = spandrel.load()
    f = M.fbm(S, seed_of("b12spandrel"), (16, 8), 0.5)
    for y in range(S):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(M.mix((56, 68, 84), (40, 48, 60), y / (S - 1)), f[y][x] * 3, 0.04))
    framed(spandrel)
    for x in range(S):
        spandrel.load()[x, 0] = M.rgba(frame_lit)
        spandrel.load()[x, 1] = M.rgba(frame)
        M.touch(spandrel, x, 2, -0.18)
    spandrel = matched(spandrel, "facade-glass-band")
    save(spandrel, "facade-glass-band")
    save(spandrel, "facade-glass-wall")
    lit = M.new(S, (240, 228, 192))
    p = lit.load()
    rng = random.Random(seed_of("b12glasslit"))
    for y in range(S):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(M.mix((248, 238, 204), (210, 194, 152), y / (S - 1)), rng.uniform(-2, 2)))
    for x in range(S):
        for y in range(0, 3):
            p[x, y] = M.rgba((255, 252, 238) if x % 16 < 12 else (226, 220, 200))  # troffers in the ceiling
    for x0 in (5, 19):
        for y in range(21, 31):
            for x in range(x0, x0 + 8):
                p[x, y] = M.rgba(M.lift((124, 114, 100), 6 if y == 21 else -4 if x == x0 + 7 else 0))  # partitions
    save(matched(framed(lit), "facade-glass-lit"), "facade-glass-lit")
    blinds = M.new(S, (190, 194, 196))
    p = blinds.load()
    for y in range(S):
        for x in range(S):
            k = y % 3
            p[x, y] = M.rgba(M.lift((190, 194, 196), 9 if k == 0 else -1 if k == 1 else -14))
    save(matched(framed(blinds), "facade-glass-blinds"), "facade-glass-blinds")
    col = M.brushed_metal(seed_of("b12glasspier"), base=(72, 78, 86), grain=3, direction="v", streak=6, sheen=6)
    for y in range(S):
        M.touch(col, 15, y, -0.3)
        M.touch(col, 16, y, 0.12)
        M.touch(col, 0, y, 0.08)
        M.touch(col, S - 1, y, -0.12)
    save(matched(col, "pier-glass"), "pier-glass")
    # The black glass of the mirror towers' corners and of the city's rim: a pane in a faint mullion grid, the same
    # glass as the towers (it was a near-black speckle)
    rim = M.new(S, (12, 12, 15))
    p = rim.load()
    f = M.fbm(S, seed_of("b12rim"), (16, 8), 0.5)
    for y in range(S):
        for x in range(S):
            p[x, y] = M.rgba(M.lift(M.mix((14, 14, 18), (7, 7, 10), y / (S - 1)), f[y][x] * 1.5, 0.0))
    for y in range(S):
        p[0, y] = M.rgba((4, 4, 6))
    for x in range(S):
        p[x, 0] = M.rgba((5, 5, 7))
        p[x, 1] = M.rgba((18, 18, 23))
    save(matched(rim, "pier-mirror"), "pier-mirror")


def b12_fascia_roof_plaster():
    """The storefront fascia: a painted board with a gilt bead round it, raised (lit top and left, shaded below and
    right, its shadow inside), a little dirt; the old dark foot kept. The tar-and-gravel roofs: dark tar under a
    scatter of pebbles, each lit on top with its shadow, in three versions turned at random. The plaster inside."""
    img = M.painted_metal(seed_of("b12fascia"), base=(44, 62, 48), grain=2, mottle=4, panel=False, chips=0)
    M.grime(img, 0.08, seed_of("b12fasciag"), cells=(8, 4), cover=0.4)
    p = img.load()
    gold = (182, 154, 92)
    for i in range(1, S - 1):
        for (x, y) in ((i, 1), (i, S - 3), (1, i), (S - 2, i)):
            if y <= S - 3:
                p[x, y] = M.rgba(gold)
    M.bevel(img, (1, 1, S - 1, S - 2), 1, 0.22)
    M.inset(img, (2, 2, S - 2, S - 3), 1, 0.2)
    for x in range(S):
        p[x, S - 1] = M.rgba((16, 22, 18))
        p[x, S - 2] = M.rgba((24, 32, 26))
    save(matched(img, "cityfascia"), "cityfascia")
    for k in range(3):
        roof = M.noise_hv((56, 55, 54), 3, seed_of("b12roof"), S, 3, (8, 4), hue=1.0)
        rng = random.Random(seed_of("b12roofpebbles") + k)
        for _ in range(190):
            x, y = rng.randrange(S), rng.randrange(S)
            v = rng.uniform(5, 20)
            c = M.hue_shift(M.lift((60, 58, 56), v), rng.uniform(-6, 8))
            M.put(roof.load(), S, S, x, y, c)
            if rng.random() < 0.45:
                M.put(roof.load(), S, S, x + 1, y, M.lift(c, -6))
            M.touch(roof, x, y + 1, -0.14)
        for _ in range(14):  # a few tar blisters, glossy
            x, y = rng.randrange(S), rng.randrange(S)
            M.touch(roof, x, y, 0.1)
        save(matched(roof, "cityroof", "roof"), "cityroof" + (f"-{k + 1}" if k else ""))
    save(matched(M.plaster(seed_of("b12plaster"), base=(230, 222, 204), grain=2, mottle=4), "cityplaster"), "cityplaster")


# ---- Streets ----

def b12_streets():
    """The cracked asphalt, rebuilt on B7's road (deep_textures.asphalt_version): the plain road's versions, with a
    soft, irregular cold-mix patch and two fine tar-filled cracks in one (`asphalt-cracked`), which the blocktype lists
    one block in seven among the plain versions (asphalt.json, facades()); the layout puts this floor in a fifth of
    the road, so the featured version shows in about one road block in thirty. The markings painted on the road take
    its grain (deep_textures.painted_mark). Granite pavers on the plazas (three versions); the lobbies' marble in
    three cuts (one vein scribble repeated in every block was graded D). Neither is turned: their joints run along two
    sides only, so a turned block doubles or loses a joint."""
    import deep_textures as DT
    road = DT.asphalt_base()
    yellow, white = (204, 168, 44), (214, 214, 206)
    img = road.copy()
    DT.painted_mark(img, (12, 0, 13, S - 1), yellow)
    DT.painted_mark(img, (18, 0, 19, S - 1), yellow)
    save(img, "asphalt-doublens")
    save(img.rotate(90), "asphalt-doublewe")
    img = road.copy()
    DT.painted_mark(img, (15, 0, 16, S - 1), white)
    save(img, "asphalt-bayns")
    save(img.rotate(90), "asphalt-baywe")
    plain = DT.asphalt_version(2)
    img = plain.copy()
    patch = M.asphalt(seed=seed_of("b12patch"), base=(43, 44, 45), grain=2, mottle=2, aggregate=0.32, binder=0.4,
                      chip=(2, 8), pits=0.002, shadow=0.04)
    mask = DT._blob(13, 18, 7.5, seed_of("b12patchshape"), wobble=0.4)
    p, q = img.load(), patch.load()
    for y in range(S):
        for x in range(S):
            m = mask[y][x]
            if m > 0:
                c = M.mix(p[x, y], q[x, y], m)
                if 0.15 < m < 0.75:
                    c = M.lift(c, -4)
                p[x, y] = M.rgba(c)
    rng = random.Random(seed_of("b12cracks"))
    for (x, y, a, n) in ((21.0, 6.0, 1.9, 14), (19.5, 21.0, 0.3, 9)):
        for i in range(n):
            xi, yi = int(x) % S, int(y) % S
            M.put(img.load(), S, S, xi, yi, (37, 38, 39))
            M.touch(img, xi + 1, yi, -0.05)
            a += rng.uniform(-0.5, 0.5)
            x, y = x + math.cos(a) * 0.9, y + math.sin(a) * 0.9
    save(T.inside_block(plain, img, band=3), "asphalt-cracked")

    seed = seed_of("b12plaza")
    for k in range(3):
        img = M.noise_hv((174, 170, 162), 3, seed, S, 3, (8, 4), hue=1.5)
        rng = random.Random(seed + 1)
        for _ in range(int(S * S * 0.08)):  # the granite's grains: black mica, white quartz, a few pink feldspar
            x, y = rng.randrange(S), rng.randrange(S)
            r = rng.random()
            c = (96, 94, 92) if r < 0.4 else (212, 208, 200) if r < 0.85 else (190, 160, 150)
            M.put(img.load(), S, S, x, y, M.mix(img.load()[x, y], c, rng.uniform(0.15, 0.3)))
        tr = random.Random(seed + 11 * k)
        for (x0, y0) in ((0, 0), (16, 0), (0, 16), (16, 16)):
            v = tr.uniform(-4, 4) / 170
            M.hue_jitter(img, 3, seed + x0 + y0 + k, boxes=[(x0, y0, x0 + 16, y0 + 16)])
            for y in range(y0, y0 + 16):
                for x in range(x0, x0 + 16):
                    M.touch(img, x, y, v)
            M.bevel(img, (x0 + 1, y0 + 1, x0 + 16, y0 + 16), 1, 0.07)
            for i in range(16):
                M.touch(img, x0 + i, y0, -0.2)
                M.touch(img, x0, y0 + i, -0.2)
        save(matched(img, "cityfloor-plaza", "plaza"), "cityfloor-plaza" + (f"-{k + 1}" if k else ""))
    for k in range(3):
        marble = texlib.marble((226, 220, 206), (160, 150, 136), 1102 + 17 * k, veins=1, sharpness=8, mottle=0.05)
        for i in range(S):
            M.touch(marble, i, 0, -0.1)
            M.touch(marble, 0, i, -0.1)
            M.touch(marble, i, 1, 0.04)
        save(matched(marble, "cityfloor-marble", "marble"), "cityfloor-marble" + (f"-{k + 1}" if k else ""))
    rim = M.noise_hv((190, 183, 168), 3, seed_of("b12rim2"), S, 4, (16, 8), hue=1.5)
    for x in range(S):
        for y, f in ((0, 0.14), (1, 0.08), (2, 0.03), (6, -0.16), (7, 0.05)):
            M.touch(rim, x, y, f)
    for y in range(8, S):
        M.touch(rim, 0, y, -0.14)
        M.touch(rim, 16, y, -0.14)
    save(matched(rim, "fountainrim"), "fountainrim")


# ---- The subway ----

def b12_subway():
    """Glazed subway tiles at the old 16 x 8 bond: each tile's face a little uneven in tone, lit along its top and
    left with a soft glaze highlight, shaded at its foot; grey grout pressed in. Three versions (which tiles are
    darker), and a fourth with grime run down from the joints, one block in eight. The ceiling, platform and ballast
    as shaded concrete and stone; the yellow edge with its domes raised; the rails and sleepers are geometry now
    (facades()), so the track blocks show ballast."""
    seed = seed_of("b12subtile")
    for k in range(4):
        img = M.noise_hv((232, 232, 226), 2, seed, S, 2, (16, 8), hue=1.0)
        tr = random.Random(seed + 13 * (k % 3))
        for r in range(4):
            y0 = r * 8
            off = 8 if r % 2 else 0
            for i in range(3):
                x0 = off + i * 16 - 16
                v = tr.uniform(-3, 3) / 230
                for y in range(y0, y0 + 8):
                    for x in range(x0, x0 + 16):
                        M.touch(img, x % S, y, v)
                for x in range(x0 + 1, x0 + 15):
                    M.touch(img, x % S, y0 + 1, 0.04)
                    M.touch(img, x % S, y0 + 6, -0.05)
                    M.touch(img, x % S, y0 + 7, -0.1)
                for y in range(y0 + 1, y0 + 7):
                    M.touch(img, (x0 + 1) % S, y, 0.03)
                    M.touch(img, (x0 + 15) % S, y, -0.06)
                for (dx, dy) in ((3, 2), (4, 2), (3, 3)):  # the glaze's glint
                    M.touch(img, (x0 + dx) % S, y0 + dy, 0.03)
                for y in range(y0, y0 + 8):
                    M.put(img.load(), S, S, x0 % S, y, (176, 176, 168))
            for x in range(S):
                M.put(img.load(), S, S, x, y0, (170, 170, 162))
        if k == 3:
            M.drips(img, 3, seed_of("b12subgrime"), color=(150, 140, 112), length=(6, 14), strength=0.22)
        save(matched(img, "subwaywall-tile", "subtile"), "subwaywall-tile" + (f"-{k + 1}" if k else ""))
    ceil = M.concrete(seed=seed_of("b12subceil"), base=(74, 72, 70), grain=3, mottle=6, aggregate=0.04, pores=0.02, hue=1.0)
    M.grime(ceil, 0.12, seed_of("b12soot"), color=(40, 38, 36), cells=(16, 8), cover=0.5)
    save(matched(ceil, "subwaywall-ceiling"), "subwaywall-ceiling")
    plat = M.concrete(seed=seed_of("b12plat"), base=(140, 136, 130), grain=3, mottle=4, aggregate=0.04, pores=0.015, hue=1.0)
    save(matched(plat, "subwayfloor-platform"), "subwayfloor-platform")
    edge = M.noise_hv((200, 166, 36), 3, seed_of("b12edge"), S, 3, (8, 4), hue=1.0)
    for y in range(1, S, 4):
        for x in range(1, S, 4):
            for (dx, dy, f) in ((0, 0, 0.2), (1, 0, 0.1), (0, 1, 0.06), (1, 1, -0.14), (2, 1, -0.24), (1, 2, -0.26), (2, 2, -0.18)):
                M.touch(edge, x + dx, y + dy, f)
    M.grime(edge, 0.1, seed_of("b12edgeg"), cells=(8, 4), cover=0.45)
    save(matched(edge, "subwayfloor-edge"), "subwayfloor-edge")
    bed = M.noise_hv((70, 66, 62), 3, seed_of("b12bed"), S, 3, (8, 4), hue=1.0)
    rng = random.Random(seed_of("b12ballast"))
    for _ in range(120):  # crushed stone: angular pieces of 2-3 px, each lit on top and shaded at its foot
        x, y = rng.randrange(S), rng.randrange(S)
        c = M.hue_shift(M.lift((94, 90, 86), rng.uniform(-8, 16)), rng.uniform(-4, 4))
        cells = [(x, y), (x + 1, y), (x, y + 1)] + ([(x + 1, y + 1)] if rng.random() < 0.6 else [])
        for (cx, cy) in cells:
            M.put(bed.load(), S, S, cx, cy, c)
        M.touch(bed, x, y, 0.08)
        M.touch(bed, x + 1, y + 2, -0.12)
        M.touch(bed, x, y + 2, -0.1)
    bed = matched(bed, "subwayfloor-bed")
    save(bed, "subwayfloor-bed")
    sleeper = M.wood_planks(seed_of("b12sleeper"), base=(70, 52, 38), planks=1, direction="h", grain=3)
    M.grime(sleeper, 0.2, seed_of("b12sleeperg"), color=(34, 28, 24), cells=(8, 4), cover=0.6)
    save(sleeper, "subwaysleeper")
    rail = M.painted_metal(seed_of("b12rail"), base=(104, 82, 66), panel=False, chips=0, grain=4)
    M.rust(rail, 0.12, seed_of("b12railrust"), pits=False, cells=(4, 2))
    save(rail, "subwayrail")
    top = M.brushed_metal(seed_of("b12railtop"), base=(184, 182, 178), direction="v", streak=6, sheen=10)
    save(top, "subwayrailtop")
    # The station's signs, in a pixel face: the name and the lines it serves, drawn in the 20 rows the plate shows
    img = M.painted_metal(seed_of("b12stationsign"), base=(24, 24, 26), panel=False, chips=2, grain=2)
    ptext_c(img, "11 ST", 8, (240, 240, 234))
    for x, c in ((8, (210, 64, 50)), (14, (52, 104, 206)), (20, (226, 168, 40))):
        for (dx, dy) in ((1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (1, 3), (2, 3), (3, 3)):
            img.load()[x + dx, 18 + dy] = M.rgba(M.lift(c, 8 if dy == 0 else -6 if dy == 3 else 0))
    for x in range(S):
        M.touch(img, x, 6, 0.2)
        M.touch(img, x, 25, -0.2)
    save(img, "stationsign")
    img = M.new(S, (206, 222, 228))
    p = img.load()
    for y in range(S):
        for x in range(S):
            p[x, y] = M.rgba(M.lift((168, 196, 206), random.Random(x * 97 + y).uniform(-2, 2) - y * 0.2))
    for y in range(9, 26):
        for x in range(11, 21):
            p[x, y] = M.rgba(M.lift((240, 232, 214), -2 if x == 20 else 3 if x == 11 else 0))  # the bottle
    for y in range(6, 9):
        for x in range(13, 19):
            p[x, y] = M.rgba((228, 220, 204))
    for y in range(15, 21):
        for x in range(12, 20):
            p[x, y] = M.rgba((120, 168, 186))  # its label
    ptext_c(img, "ALMOND", 1, (32, 48, 64), CITY_F3)
    ptext_c(img, "HYDRATE", 27, (32, 48, 64), CITY_F3)
    M.stain(img, seed_of("b12adpeel"), radius=6, color=(196, 192, 182), strength=0.45, at=(27, 5))
    M.grime(img, 0.1, seed_of("b12adgrime"), cells=(8, 4), cover=0.5)
    save(img, "subwayad")
    glass = M.noise_hv((250, 232, 190), 2, seed_of("b12lampglass"), S, 3, (8, 4), hue=0.5)
    save(glass, "subwaylampglass")


# ---- Signs, doors and props ----

def b12_props():
    """The street props' paint (matlib's painted metal, worn and dirty, in the old colours), the woods, and the small
    signs redrawn in a pixel face (they were type scaled down past reading): the newspaper box, the mailbox, the
    parking meter, the phone booth's sign, the vendor's cart, the street signs. The traffic lights' lenses keep a lit
    centre without the black square round them; their hoods and back plate are geometry (props())."""
    for key, ref in (("binsgreen", "binsgreen"), ("trafficyellow", "trafficyellow"), ("streetgreen", "streetgreen"),
                     ("postblue", "postblue"), ("acgrey", "acgrey"), ("cartsteel", "cartsteel"), ("dumpsterlid", "dumpsterlid"),
                     ("pillargreen", "pillargreen")):
        save(matched(painted_board(key, OLD_MEAN[ref], chips=1), ref), key)
    frame = M.painted_metal(seed_of("b12bbframe"), base=(58, 60, 62), panel=False, chips=5, grain=3)
    M.rust(frame, 0.2, seed_of("b12bbrust"))
    save(matched(frame, "billboardframe"), "billboardframe")
    for key, ref, base in (("pewwood", "pewwood", (96, 62, 36)), ("tankwood", "tankwood", (112, 84, 56))):
        img = M.wood_planks(seed_of("b12" + key), base=base, planks=3, direction="v" if key == "tankwood" else "h", grain=4)
        save(matched(img, ref), key)

    def lens(code, c, on):
        img = M.new(S, (26, 26, 24))
        p = img.load()
        for y in range(S):
            for x in range(S):
                d = math.hypot(x - 15.5, y - 15.5)
                if d < 14:
                    k = d / 14
                    if on:
                        col = M.mix(tuple(min(255, v + 90) for v in c), c, min(1.0, k * 1.3))
                        col = M.lift(col, -18 * max(0.0, k - 0.8) / 0.2)
                    else:
                        col = M.lift(tuple(v // 5 + 18 for v in c), 10 * (1 - k) - 6 * max(0.0, k - 0.7))
                    p[x, y] = M.rgba(col)
                elif d < 15.5:
                    p[x, y] = M.rgba((40, 40, 38))
        save(img, code)
    lens("lens-red", (226, 40, 26), True)
    lens("lens-amber", (240, 160, 30), True)
    lens("lens-off", (160, 160, 150), False)

    def sign_face(key, base, ink, words, border=None, font=CITY_F5, ys=None):
        img = M.painted_metal(seed_of("b12" + key), base=base, panel=False, chips=2, grain=2)
        if border:
            for i in range(S):
                for (x, y) in ((i, 0), (i, S - 1), (0, i), (S - 1, i)):
                    img.load()[x, y] = M.rgba(border)
        for (w, y) in zip(words, ys):
            ptext_c(img, w, y, ink, font)
        return img
    img = M.painted_metal(seed_of("b12newsfront"), base=(30, 58, 122), panel=True, chips=3, grain=2)
    p = img.load()
    for y in range(3, 19):
        for x in range(3, S - 3):
            p[x, y] = M.rgba(M.lift((214, 206, 186), -3 if (y - 11) % 2 == 0 and y > 11 else 0))
    ptext_c(img, "NEWS", 4, (24, 24, 24))
    for y in range(13, 18, 2):
        for x in range(5, S - 5):
            if (x * 7 + y) % 5:
                p[x, y] = M.rgba((112, 110, 104))
    M.inset(img, (3, 3, S - 3, 19), 1, 0.25)
    for y in range(22, 25):
        for x in range(10, 22):
            p[x, y] = M.rgba(M.lift((150, 150, 146), 6 if y == 22 else -8 if y == 24 else 0))  # the coin slot plate
    save(img, "newsfront")
    img = M.painted_metal(seed_of("b12meter"), base=(196, 196, 188), panel=True, chips=2, grain=2)
    p = img.load()
    for y in range(4, 20):
        for x in range(4, 28):
            p[x, y] = M.rgba(M.lift((40, 54, 42), -2 * (y - 4) / 16))
    M.inset(img, (4, 4, 28, 20), 1, 0.3)
    for i in range(7):
        p[16 + i, 14 - i] = M.rgba((210, 40, 34))  # the needle at zero
    ptext_c(img, "EXPIRED", 23, (206, 36, 30), CITY_F3)
    save(img, "meterface")
    img = M.painted_metal(seed_of("b12cartfront"), base=(200, 204, 206), panel=True, chips=2, grain=2)
    p = img.load()
    for y in range(4, 27):
        for x in range(2, S - 2):
            p[x, y] = M.rgba(M.lift((240, 232, 214), -1 if y > 15 else 1))
    ptext_c(img, "ALMOND", 6, (138, 58, 26), CITY_F3)
    ptext_c(img, "WATER", 12, (138, 58, 26), CITY_F3)
    ptext_c(img, "$1", 18, (32, 48, 64))
    M.bevel(img, (2, 4, S - 2, 27), 1, 0.15)
    save(img, "cartfront")
    # Street signs: a blade two blocks long (its face is 32 x 4 units), so the face is 64 x 8 px at the world's density
    for key, word in (("streetsign-st", "W 11 ST"), ("streetsign-ave", "AVENIDA 11")):
        img = M.new((64, 8), (30, 106, 58))
        p = img.load()
        rng = random.Random(seed_of("b12" + key))
        for y in range(8):
            for x in range(64):
                p[x, y] = M.rgba(M.lift((30, 104, 58), rng.uniform(-2, 2)))
        for x in range(64):
            p[x, 0] = p[x, 7] = M.rgba((222, 226, 220))
        for y in range(8):
            p[0, y] = p[63, y] = M.rgba((222, 226, 220))
        ptext(img, word, (64 - ptext_width(word, CITY_F3)) // 2, 2, (240, 242, 236), CITY_F3)
        save(img, key)
    save(sign_face("shelterad", (32, 48, 64), (138, 58, 26), ["ALMOND", "WATER"], font=CITY_F3, ys=[8, 15]), "shelterad")


def b12_posters():
    """Billboard posters and the advertising pillars' columns: the old pictures, pasted up in sheets (faint seams
    every 16 px), sun-faded, the small type now in a pixel face. Each billboard has a second version a summer older,
    more washed out and rain-streaked at other places (the blocktype picks between them; round 1's peeling corner read
    as a missing chunk of the picture)."""
    def sheets(img):
        w, h = img.size
        for x in range(16, w, 16):
            for y in range(h):
                M.touch(img, x, y, -0.05)
                M.touch(img, x - 1, y, 0.03)
        return img

    def weathered(img, seed):
        """(round 2) The same poster a summer older: a little more washed out, rain run down from the top in a few
        soft streaks at other places (the second version the blocktype picks)."""
        w, h = img.size
        rng = random.Random(seed)
        p = img.load()
        for y in range(h):
            for x in range(w):
                p[x, y] = M.rgba(M.mix(p[x, y], (222, 216, 200), 0.08))
        for _ in range(7):
            x0 = rng.randrange(w)
            L = rng.randint(h // 3, h)
            for y in range(L):
                for dx in (0, 1):
                    xx = (x0 + dx) % w
                    p[xx, y] = M.rgba(M.mix(p[xx, y], (214, 208, 192), 0.2 * (1 - y / L)))
        return img

    import os as _os
    base = _os.path.join(ASSETS, "textures", "block", "detail")
    for k in BILLBOARDS:
        img = Image.open(_os.path.join(base, f"billboard-{k}.png")).convert("RGBA")
        d = ImageDraw.Draw(img)
        if k == "almond":
            d.rectangle([2, 36, 60, 46], fill=img.getpixel((30, 40)))
            ptext(img, "STAY HYDRATED", 5, 39, (138, 58, 26), CITY_F3)
        if k == "city":  # (round 2) the slogan in a pixel face, with a drop shadow (the scaled type smeared)
            band = Image.new("RGBA", (img.width, 22), (30, 34, 70, 255))
            pb = band.load()
            for y in range(22):
                for x in range(img.width):
                    pb[x, y] = M.rgba(M.mix((26, 32, 66), (38, 38, 78), y / 21))
            img.paste(band, (0, 0))
            for (word, y) in (("THE CITY THAT", 3), ("NEVER SLEEPS", 13)):
                ptext_c(img, word, y + 1, (12, 12, 26))
                ptext_c(img, word, y, (246, 214, 122))
        if k == "diner":
            d.rectangle([0, 38, img.width - 1, img.height - 1], fill=(240, 230, 204, 255))
            ptext_c(img, "OPEN 24 HRS NEXT CORNER", 41, (176, 42, 36), CITY_F3)
        sheets(img)
        save(img, f"billboard-{k}")
        save(weathered(img.copy(), seed_of("b12weather" + k)), f"billboard-{k}-2")
    for k, posters in enumerate((
            [("ALMOND", "WATER", (138, 184, 200), (32, 48, 64)), ("DINER", "24 HRS", (184, 42, 36), (242, 232, 200)), ("THE ARMS", "ROOMS", (28, 42, 36), (232, 224, 200))],
            [("MUSEUM", "OPEN", (216, 204, 170), (58, 48, 32)), ("HOTEL", "VACANCY", (74, 14, 20), (232, 192, 96)), ("LAUNDRO", "MAT", (26, 58, 138), (255, 255, 255))],
            [("CINEMA", "TONIGHT", (24, 20, 24), (242, 210, 122)), ("MISSING", "?", (240, 236, 220), (192, 24, 24)), ("BODEGA", "DELI", (200, 56, 30), (255, 240, 200))])):
        img = M.noise_hv((214, 208, 190), 2, seed_of(f"b12pillar{k}"), (S, 3 * S), 3, (8, 4))
        p = img.load()
        for n, (top, bottom, bg, fg) in enumerate(posters):
            y0 = 2 + n * S
            for y in range(y0, y0 + S - 3):
                for x in range(1, S - 1):
                    p[x, y] = M.rgba(M.lift(bg, random.Random(x * 13 + y * 7 + n).uniform(-2, 2)))
            for (word, yy) in ((top, y0 + 5), (bottom, y0 + 16)):
                font = CITY_F5 if ptext_width(word) <= S - 4 else CITY_F3
                ptext_c(img, word, yy + (1 if font is CITY_F3 else 0), fg, font)
            for y in range(y0 + S - 10, y0 + S - 3):  # a torn corner, the poster under it
                for x in range(S - 2 - (y - (y0 + S - 10)), S - 1):
                    p[x, y] = M.rgba((214, 208, 190))
            for x in range(1, S - 1):
                M.touch(img, x, y0 + S - 3, -0.12)
        M.grime(img, 0.08, seed_of(f"b12pillarg{k}"), cells=(8, 4), cover=0.45)
        save(img, f"adpillar-{PILLARS[k]}")


def b12_doors():
    """The row-house door and the steel doors (still cubes, as the old ones): panels shaded as raised fields in their
    frames, a brass knob and knocker with highlights; steel doors in worn paint with their stencils in a pixel face."""
    for part in ("lower", "upper"):
        img = M.painted_metal(seed_of("b12rowdoor" + part), base=(36, 64, 48), panel=False, chips=3, grain=2)
        p = img.load()
        for y in range(S):
            for x in list(range(0, 3)) + list(range(S - 3, S)):
                p[x, y] = M.rgba(M.lift((204, 200, 190), 4 if x in (0, S - 3) else -6 if x in (2, S - 1) else 0))
        if part == "lower":
            M.bevel(img, (7, 4, 25, 27), 2, 0.18)
            M.inset(img, (5, 2, 27, 29), 1, 0.2)
            for (dx, dy, c) in ((0, 0, (236, 206, 120)), (1, 0, (210, 170, 80)), (0, 1, (200, 160, 70)), (1, 1, (150, 112, 46))):
                p[23 + dx, 1 + dy] = M.rgba(c)  # the knob
        else:
            for y in range(12, S):
                for x in range(7, 25):
                    p[x, y] = M.rgba(M.lift((52, 64, 74), 10 if (x + y) % 11 == 0 else -(y - 12) * 0.4))
            M.inset(img, (7, 12, 25, S), 2, 0.25)
            for y in range(0, 7):
                for x in range(3, S - 3):
                    p[x, y] = M.rgba(M.lift((64, 78, 92), 6 if y == 1 else -4 if y == 6 else 0))  # the transom
            for (dx, dy, c) in ((0, 0, (236, 206, 120)), (1, 0, (214, 176, 84)), (2, 0, (190, 150, 64)),
                                (0, 1, (200, 160, 70)), (1, 1, (170, 130, 56)), (2, 1, (132, 98, 40))):
                p[15 + dx, 15 + dy] = M.rgba(c)  # the knocker
        save(img, f"rowhousedoor-{part}")
    for code, colour, label, danger in (("substationdoor", (106, 110, 104), None, True),
                                        ("maintenancedoor", (94, 106, 98), ["STAFF", "ONLY"], False)):
        for part in ("lower", "upper"):
            img = M.painted_metal(seed_of("b12" + code + part), base=colour, panel=True, chips=5, grain=3)
            M.rust(img, 0.12 if part == "lower" else 0.05, seed_of("b12r" + code + part))
            p = img.load()
            if part == "lower":
                for y in range(1, 4):
                    for x in range(21, 28):
                        p[x, y] = M.rgba(M.lift((184, 184, 180), 10 if y == 1 else -10 if y == 3 else 0))  # the lever
                M.bevel(img, (4, 23, S - 4, 29), 1, 0.2)
            elif danger:
                for y in range(6, 25):
                    for x in range(4, S - 4):
                        p[x, y] = M.rgba(M.lift((230, 196, 40), -2 if y > 15 else 0))
                ptext_c(img, "DANGER", 8, (20, 20, 20), CITY_F3)
                ptext_c(img, "HIGH", 15, (20, 20, 20), CITY_F3)
                ptext_c(img, "VOLTAGE", 20, (20, 20, 20), CITY_F3)
                M.bevel(img, (4, 6, S - 4, 25), 1, 0.12)
            elif label:
                for i, word in enumerate(label):
                    ptext_c(img, word, 8 + 7 * i, (232, 228, 216), CITY_F3)
            save(img, f"{code}-{part}")


def generate_textures():
    l11art_tex.generate()  # (l11art) the basement door, directory, hydrant, mailboxes, booth, cabinet, piano, pantry shelf
    facade_textures()
    street_textures()
    door_textures()
    sign_textures()
    prop_textures()
    poster_textures()
    # (B12) the graphics pass; drop a line to put that family back as it was
    b12_brick()
    b12_glass()
    b12_windows()
    b12_stone()
    b12_concrete()
    b12_fascia_roof_plaster()
    b12_streets()
    b12_subway()
    b12_props()
    b12_posters()
    b12_doors()


# ======================= Blocks =======================

def wbox(name, frm, to, tex, faces=None, glow=0, glow_faces=("north",)):
    """(B12) A box whose faces take their texture where a cube block would show it (world-aligned UVs: north u = 16 - x,
    south u = x, east u = 16 - z, west u = z, v = 16 - y), so a modelled wall continues the bricks of the cube beside
    it. `tex` is one key or {face: key}; faces left out of `tex` (or not in `faces`) are not drawn."""
    (x1, y1, z1), (x2, y2, z2) = frm, to
    uv = {"north": [16 - x2, 16 - y2, 16 - x1, 16 - y1], "south": [x1, 16 - y2, x2, 16 - y1],
          "east": [16 - z2, 16 - y2, 16 - z1, 16 - y1], "west": [z1, 16 - y2, z2, 16 - y1],
          "up": [x1, z1, x2, z2], "down": [x1, 16 - z2, x2, 16 - z1]}
    texmap = tex if isinstance(tex, dict) else {f: tex for f in uv}
    out = {}
    for f in (faces or texmap.keys()):
        if f in texmap:
            out[f] = {"texture": "#" + texmap[f], "uv": [round(v, 4) for v in uv[f]]}
            if glow and f in glow_faces:
                out[f]["glow"] = glow
    return {"name": name, "from": [x1, y1, z1], "to": [x2, y2, z2], "faces": out}


# (B12) The modelled façade parts: the brick and limestone sash windows set back in their reveals, the concrete
# ribbon windows, and the string course or cornice at each floor. Everything else stays a cube.
WINDOW_DEPTH = {"brick": 1.5, "brickdark": 1.5, "stone": 2.5, "concrete": 2.0}
# (round 2) the openings nearly as wide as the block and the frames as broad as the old painted ones (the blind review
# read the first, narrower slots as a change of the buildings' look)
WINDOW_OPENING = {"brick": (0.75, 15.25), "brickdark": (0.75, 15.25), "stone": (1.0, 15.0)}  # across the block, in units
FRAME_W = {"brick": 2.0, "brickdark": 2.0, "stone": 1.5}  # the stiles' width; the rails are 1.5 high
MODELLED_BANDS = ("brick", "brickdark", "stone")


def window_shape(style, part):
    """A window block, its outside face north: the wall either side of the opening (or none, for a ribbon), the pane
    set back WINDOW_DEPTH units, and a frame of painted members round it, with a glazing bar across the middle.
    Stacked, two of them make one tall window whose top and bottom rails meet as the meeting rail. The opening's
    head and sill are the faces of the blocks above and below, which this block leaves open for them."""
    wall, pier, plaster = f"facade-{style}-wall", f"pier-{style}", "cityplaster"
    pane, frame = f"citypane-{style}-{part}", FRAME[style]
    dz = WINDOW_DEPTH[style]
    glow = 150 if part == "lit" else 0
    els = []
    if style == "concrete":
        x0, x1 = 0.0, 16.0
        els.append(wbox("Room", (0, 0, dz), (16, 16, 16), {"north": pane, "south": plaster, "up": pier, "down": pier}, glow=glow))
        els.append(wbox("Mullion", (0, 0.75, dz - 0.5), (0.75, 15.25, dz), frame, faces=("north", "east")))
        els.append(wbox("Mullion2", (8, 0.75, dz - 0.5), (8.75, 15.25, dz), frame, faces=("north", "east", "west")))
        els.append(wbox("RailB", (0, 0, dz - 0.5), (16, 0.75, dz), frame, faces=("north", "up")))
        els.append(wbox("RailT", (0, 15.25, dz - 0.5), (16, 16, dz), frame, faces=("north", "down")))
        return els
    x0, x1 = WINDOW_OPENING[style]
    side = {"north": wall, "east": wall, "west": wall, "south": plaster, "up": pier, "down": pier}
    els.append(wbox("WallL", (0, 0, 0), (x0, 16, 16), side))
    els.append(wbox("WallR", (x1, 0, 0), (16, 16, 16), side))
    els.append(wbox("Room", (x0, 0, dz), (x1, 16, 16), {"north": pane, "south": plaster, "up": pier, "down": pier}, glow=glow))
    f0, fw = dz - 0.5, FRAME_W[style]
    els.append(wbox("StileL", (x0, 0, f0), (x0 + fw, 16, dz), frame, faces=("north", "east")))
    els.append(wbox("StileR", (x1 - fw, 0, f0), (x1, 16, dz), frame, faces=("north", "west")))
    els.append(wbox("RailB", (x0 + fw, 0, f0), (x1 - fw, 1.5, dz), frame, faces=("north", "up")))
    els.append(wbox("RailT", (x0 + fw, 14.5, f0), (x1 - fw, 16, dz), frame, faces=("north", "down")))
    els.append(wbox("Bar", (x0 + fw, 7.5, f0 + 0.25), (x1 - fw, 8.5, dz), frame, faces=("north", "up", "down")))
    return els


def band_shape(style):
    """A band block, its outside face north: the wall, and in front of it a stone string course (brick) or a cornice of
    a crown moulding over a dentil course (limestone), kept off the block's top plane so it takes its own light."""
    band, pier, plaster = f"facade-{style}-band", f"pier-{style}", "cityplaster"
    els = [wbox("Wall", (0, 0, 0), (16, 16, 16), {"north": band, "east": plaster, "west": plaster, "south": plaster, "up": pier, "down": pier})]
    if style == "stone":
        els.append({"name": "Bed", "from": [0, 11.25, -0.75], "to": [16, 13.5, 0], "faces": {
            "north": {"texture": "#citycornice", "uv": [0, 2.5, 16, 4.75]}, "down": {"texture": "#citycornice", "uv": [0, 11, 16, 11.75]},
            "east": {"texture": "#citycornice", "uv": [0, 2.5, 0.75, 4.75]}, "west": {"texture": "#citycornice", "uv": [0, 2.5, 0.75, 4.75]}}})
        els.append({"name": "Crown", "from": [0, 13.5, -1.5], "to": [16, 15.75, 0], "faces": {
            "north": {"texture": "#citycornice", "uv": [0, 0, 16, 2.25]}, "up": {"texture": "#citycornice", "uv": [0, 6, 16, 7.5]},
            "down": {"texture": "#citycornice", "uv": [0, 12, 16, 13.5]},
            "east": {"texture": "#citycornice", "uv": [0, 0, 1.5, 2.25]}, "west": {"texture": "#citycornice", "uv": [0, 0, 1.5, 2.25]}}})
    else:
        els.append({"name": "Course", "from": [0, 13, -0.5], "to": [16, 15.75, 0], "faces": {
            "north": {"texture": "#" + band, "uv": [0, 0.25, 16, 3]}, "up": {"texture": "#" + band, "uv": [0, 0, 16, 0.5]},
            "down": {"texture": "#" + band, "uv": [0, 2.5, 16, 3]},
            "east": {"texture": "#" + band, "uv": [0, 0.25, 0.5, 3]}, "west": {"texture": "#" + band, "uv": [0, 0.25, 0.5, 3]}}})
    return els


def surface_alternates(key, n=3, extra=()):
    return [{"base": f"block/detail/{key}-{k}"} for k in range(2, n + 1)] + [{"base": f"block/detail/{k}"} for k in extra]


# (B12) The surfaces drawn in versions: which keys pick among which others (the plain version listed more than once
# where a feature should be rare)
WALL_ALTS = {
    "facade-brick-wall": surface_alternates("facade-brick-wall"),
    "facade-brickdark-wall": surface_alternates("facade-brickdark-wall"),
    "facade-stone-wall": surface_alternates("facade-stone-wall"),
    "facade-concrete-wall": [{"base": "block/detail/facade-concrete-wall"}] * 5 + surface_alternates("facade-concrete-wall"),
    "facade-glass-window": surface_alternates("facade-glass-window"),
}


def facades():
    by_type, sounds_by, material_by, glow_by = {}, {}, {}, {}
    draw_by, shape_by, opaque_by = {}, {}, {}
    for style in STYLES:
        for part in PARTS:
            modelled = (part in ("window", "lit", "blinds") and style in WINDOW_DEPTH) or (part == "band" and style in MODELLED_BANDS)
            if modelled:
                els = window_shape(style, part) if part != "band" else band_shape(style)
                path = shape(f"cityfacade-{style}-{part}", els)
                tex = {}
                for k in sorted({f["texture"][1:] for e in els for f in e["faces"].values()}):
                    t = {"base": f"block/detail/{k}"}
                    if k in WALL_ALTS:
                        t["alternates"] = WALL_ALTS[k]
                    if k.startswith("citypane-") and k.endswith("-window"):
                        t["alternates"] = surface_alternates(k, PANE_VERSIONS)
                    tex[k] = t
                for s in SIDES:
                    draw_by[f"*-{style}-{part}-{s}"] = "json"
                    shape_by[f"*-{style}-{part}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
                    by_type[f"*-{style}-{part}-{s}"] = tex
                    if part != "band":
                        # the opening leaves the outside face, and the head and sill, to the blocks round it (a
                        # ribbon window runs on into its neighbours, so its ends too)
                        op = {f: f not in (s, "up", "down") for f in ("north", "east", "south", "west", "up", "down")}
                        if style == "concrete":
                            op.update({k: False for k in SIDES})
                        opaque_by[f"*-{style}-{part}-{s}"] = op
                continue
            for s in SIDES:
                faces = {f: {"base": "block/detail/cityplaster"} for f in ("north", "east", "south", "west")}
                faces["up"] = faces["down"] = {"base": f"block/detail/pier-{style}"}
                faces[s] = {"base": f"block/detail/facade-{style}-{part}"}
                if style == "mirror" and part != "band":
                    faces[s]["alternates"] = [{"base": f"block/detail/{k}"} for k in MIRROR_ALTERNATES]
                if f"facade-{style}-{part}" in WALL_ALTS:
                    faces[s]["alternates"] = WALL_ALTS[f"facade-{style}-{part}"]
                by_type[f"*-{style}-{part}-{s}"] = faces
            if part == "lit" and style != "mirror" and style not in WINDOW_DEPTH:
                glow_by[f"*-{style}-lit-*"] = {"glowLevel": 150}
        sounds_by[f"*-{style}-*"] = GLASS if style in ("glass", "mirror") else STONE
    block("cityfacade", {
        "variantgroups": [{"code": "style", "states": STYLES}, {"code": "part", "states": PARTS}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "cube", "drawtypeByType": dict(draw_by, **{"*": "cube"}),
        "shapeByType": shape_by, "sideopaqueByType": dict(opaque_by, **{"*": {"all": True}}), "texturesByType": by_type,
        "lightAbsorption": 99, "resistance": 6, "soundsByType": sounds_by, "vertexFlagsByType": glow_by,
        "randomizeAxes": "xyz",  # (D4) the walls' versions picked by height too (B13's lesson)
    }, "The Endless City's façades: the style on the outside face, plaster within; the brick, limestone and concrete "
       "windows and the brick and limestone bands are modelled (graphics pass B12)")
    for style, english in (("glass", "Curtain Wall"), ("mirror", "Black Mirror Glass"), ("brick", "Brick Wall"), ("brickdark", "Brick Wall"),
                           ("stone", "Limestone Wall"), ("concrete", "Concrete Wall")):
        name(f"cityfacade-{style}-*", english)
    cube_block("citypier", {"glass": "Aluminium Column", "mirror": "Black Mirror Glass", "brick": "Brick", "brickdark": "Brick",
                            "stone": "Limestone", "concrete": "Concrete"}, STYLES, {s: f"pier-{s}" for s in STYLES},
               comment="Corners, columns and parapets of the city's buildings")
    tex_by = {}
    for s in SIDES:
        faces = {f: {"base": "block/detail/cityplaster"} for f in ("north", "east", "south", "west", "up", "down")}
        faces[s] = {"base": "block/detail/cityfascia"}
        tex_by[f"*-{s}"] = faces
    block("cityfascia", {"variantgroups": [{"code": "side", "states": SIDES}], "creativeinventory": {"general": ["*-north"]},
                         "blockmaterial": "Wood", "drawtype": "cube", "texturesByType": tex_by, "lightAbsorption": 99,
                         "resistance": 4, "sounds": WOOD}, "The painted fascia over a storefront")
    name("cityfascia-*", "Storefront Fascia")
    # (B12) versions of the city's large surfaces: the roofs turned at random, the plazas', lobbies' and subway's in
    # three versions (the subway's grimy fourth one block in eight), through gen_detail's TURNED and ALTS
    gd = sys.modules[cube_block.__module__]
    gd.TURNED.update({"cityroof"})  # (the pavers and marble have their joints on two sides only: never turned)
    gd.ALTS.update({"cityroof": ["cityroof-2", "cityroof-3"], "cityfloor-plaza": ["cityfloor-plaza-2", "cityfloor-plaza-3"],
                    "cityfloor-marble": ["cityfloor-marble-2", "cityfloor-marble-3"],
                    "subwaywall-tile": ["subwaywall-tile"] * 2 + ["subwaywall-tile-2"] * 2 + ["subwaywall-tile-3"] * 3 + ["subwaywall-tile-4"]})
    cube_block("cityroof", "Tar and Gravel Roof", ["gravel"], {"gravel": "cityroof"})
    cube_block("cityplaster", "Plaster Wall", ["plain"], {"plain": "cityplaster"})
    cube_block("stainedglass", "Stained Glass", ["plain"], {"plain": "stainedglass"}, material="Glass", sounds=GLASS,
               vertexFlags={"glowLevel": 110}, lightAbsorption=0)
    cube_block("cityfloor", {"marble": "Marble Floor", "plaza": "Granite Pavers", "garage": "Concrete"}, ["marble", "plaza", "garage"],
               {"marble": "cityfloor-marble", "plaza": "cityfloor-plaza", "garage": "cityfloor-garage"})
    cube_block("subwayfloor", {"bed": "Ballast", "raill": "Track", "railr": "Track", "platform": "Platform", "edge": "Platform Edge"},
               ["bed", "raill", "railr", "platform", "edge"],
               {"bed": "subwayfloor-bed", "raill": "subwayfloor-bed", "railr": "subwayfloor-bed",
                "platform": "subwayfloor-platform", "edge": "subwayfloor-edge"})
    # (B12) The track blocks are models: the ballast cube with two sleepers across it and a rail (foot, web and head)
    # along it, standing on top as the old texture painted them (left rail 4.5-5.5, right 10-11, as before)
    path_ = os.path.join(ASSETS, "blocktypes", "detail", "subwayfloor.json")
    with open(path_, encoding="utf-8") as f:
        sub = json.load(f)
    draw, shapes_ = {}, {}
    for kind, cx in (("raill", 5.0), ("railr", 10.5)):
        els = [wbox("Ballast", (0, 0, 0), (16, 16, 16), "subwayfloor-bed")]
        for i, z0 in enumerate((2.0, 10.0)):
            ends = ("west",) if kind == "raill" else ("east",)
            els.append(bx(f"Sleeper{i}", (0, 16, z0), (16, 16.75, z0 + 3), "subwaysleeper", faces=("up", "north", "south") + ends))
        els += [bx("Foot", (cx - 1.25, 16.75, 0), (cx + 1.25, 17.0, 16), "subwayrail", faces=("up", "east", "west")),
                bx("Web", (cx - 0.25, 17.0, 0), (cx + 0.25, 17.75, 16), "subwayrail", faces=("east", "west")),
                bx("Head", (cx - 0.75, 17.75, 0), (cx + 0.75, 18.5, 16), "subwayrail", faces=("east", "west", "down")),
                bx("Top", (cx - 0.75, 18.5 - 0.01, 0), (cx + 0.75, 18.5, 16), "subwayrailtop", faces=("up",))]
        shapes_[f"*-{kind}"] = {"base": shape(f"subwaytrack-{kind}", els)}
        draw[f"*-{kind}"] = "json"
        sub["texturesByType"].pop(f"*-{kind}", None)  # (an "all" there would paint every part of the model with it)
    sub["drawtypeByType"] = dict(draw, **{"*": "cube"})
    sub["shapeByType"] = shapes_
    block("subwayfloor", {k: v for k, v in sub.items() if k != "code"}, "The subway's floors; the tracks modelled (graphics pass B12)")
    # (B12) The cracked asphalt (written by gen_deep.level9's asphalt blocktype, which runs first): the plain road's
    # three versions at four turns, with the patched-and-cracked version and B7's crack one block in seven between them
    path_ = os.path.join(ASSETS, "blocktypes", "detail", "asphalt.json")
    with open(path_, encoding="utf-8") as f:
        road = json.load(f)
    alts = [{"base": f"block/detail/{v}", "rotation": r} if r else {"base": f"block/detail/{v}"}
            for v in ("asphalt", "asphalt-4", "asphalt-5") for r in (0, 90, 180, 270)][1:]
    road["texturesByType"]["*-cracked"] = {"all": {"base": "block/detail/asphalt", "alternates": alts + [
        {"base": "block/detail/asphalt-cracked"}, {"base": "block/detail/asphalt-2", "rotation": 90}]}}
    block("asphalt", {k: v for k, v in road.items() if k != "code"})
    cube_block("subwaywall", {"tile": "Subway Tiles", "ceiling": "Tunnel Ceiling"}, ["tile", "ceiling"],
               {"tile": "subwaywall-tile", "ceiling": "subwaywall-ceiling"}, randomizeAxes="xyz")  # (D4) by height too
    cube_block("fountainrim", "Fountain Rim", ["stone"], {"stone": "fountainrim"})

    # The barn wall in Level 10 that isn't quite there
    block("noclipwall", {
        "variantgroups": [{"code": "kind", "states": ["barn"]}], "creativeinventory": {"general": ["*"]},
        "blockmaterial": "Wood", "drawtype": "cube", "textures": {"all": {"base": "block/detail/barnwall-noclip"}},
        "collisionbox": None, "lightAbsorption": 99, "resistance": 4, "sounds": WOOD,
        "particleProperties": [{
            "hsvaColor": [{"avg": 30, "var": 10}, {"avg": 40, "var": 20}, {"avg": 200, "var": 30}, {"avg": 90, "var": 30}],
            "gravityEffect": {"avg": 0, "var": 0.01}, "posOffset": [{"avg": 0, "var": 0.5}, {"avg": 0, "var": 0.5}, {"avg": 0, "var": 0.5}],
            "velocity": [{"avg": 0, "var": 0.02}, {"avg": 0.01, "var": 0.01}, {"avg": 0, "var": 0.02}], "quantity": {"avg": 0.04},
            "size": {"avg": 0.1, "var": 0.05}, "particleModel": "Quad", "lifeLength": {"avg": 2, "var": 1}, "selfPropelled": True}],
    }, "A stretch of barn wall that isn't quite there. Walk into it and you noclip into the Endless City")
    name("noclipwall-barn", "Barn Boards")

    # Sounds from below: the city's hum, the subway's rumble
    for code, english, sound, count in (("cityhum", "Sound of Traffic", "backrooms:ambient/cityhum", 3),
                                        ("subwayrumble", "Sound of the Subway", "backrooms:ambient/subway", 2)):
        block(code, {
            "blockmaterial": "Stone", "drawtype": "Empty",
            "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None, "selectionbox": None,
            "lightAbsorption": 0, "resistance": 999, "drops": [], "replaceable": 9000,
            "sounds": {"ambient": sound, "ambientBlockCount": count},
        }, f"Invisible: {english.lower()}")
        name(code, english)

    # Doors that lead out of the city
    for code, english, kind, material, sounds in (("rowhousedoor", "Front Door", "rowhouse", "Wood", WOOD),
                                                  ("basementdoor", "Basement Door", "basement", "Metal", METAL),
                                                  ("substationdoor", "Substation Door", "substation", "Metal", METAL),
                                                  ("maintenancedoor", "Maintenance Door", "maintenance", "Metal", METAL)):
        if code == "basementdoor":  # (l11art) the steel door as geometry, the same codes, parts and threshold
            import gen_deep
            gen_deep.door_json(code, english, {"lower": L11.basement_door(False), "upper": L11.basement_door(True)}, kind,
                               comment="A steel door marked BASEMENT; the stair behind it leads down")
            continue
        data = {
            "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
            "creativeinventory": {"general": ["*"], "construction": ["*"]},
            "blockmaterial": material, "drawtype": "cube",
            "textures": {"all": {"base": f"block/detail/{code}-{{part}}"}},
            "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": sounds, "behaviors": threshold(kind),
        }
        block(code, data, english)
        name(f"{code}-*", english)


def decorations():
    signs = ["signdiner", "signgrocery", "signbodega", "signpharmacy", "signfarmacia", "signhardware", "signlaundry",
             "signlavanderia", "signclothing", "signhotel", "signoffices", "signapartments", "signparking", "signmuseum"]
    english = {"signdiner": "Diner Sign", "signgrocery": "Grocery Sign", "signbodega": "Bodega Sign", "signpharmacy": "Pharmacy Sign",
               "signfarmacia": "Farmacia Sign", "signhardware": "Hardware Store Sign", "signlaundry": "Laundromat Sign",
               "signlavanderia": "Lavandería Sign", "signclothing": "Clothing Store Sign", "signhotel": "Hotel Sign",
               "signoffices": "Building Number", "signapartments": "Apartments Sign", "signparking": "Parking Sign",
               "signmuseum": "Museum Sign"}
    neon = {"signdiner", "signhotel", "signbodega", "signlaundry", "signlavanderia"}
    wall_family("storefrontdeco", "Storefront Fascia", {1: "cityfascia"}, [
        Decor(code, english[code], {3: plate("Sign", (0.5, 2.5, -1), (15.5, 13.5, 0), code, "blackmetal", glow=200 if code in neon else 60)},
              light=[0, 3, 7] if code in neon else None)
        for code in signs], material="Wood", sounds=WOOD)
    # Over a two-wide door, the wide sign centred on the seam between the two fascia blocks over it, in halves: "l"
    # carries the half seen on the left from the street, "r" the other (layout version 4 on; before, the one-block
    # sign hung over one of the doors). Both halves of a neon sign are lit, as the one-block sign is
    by_type, light_by = {}, {}
    for code in signs:
        wide = plate("Sign", (-5, 2, -1), (21, 15, 0), code + "-wide", "blackmetal", glow=200 if code in neon else 60)
        for half, els in zip(("l", "r"), seam_halves(wide)):
            path = shape(f"storefrontsign-{code}-{half}", [cube("cityfascia")] + els)
            for s in SIDES:
                by_type[f"*-{code}-{half}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
        if code in neon:
            light_by[f"*-{code}-*"] = [0, 3, 7]
        name(f"storefrontsign-{code}-*", english[code])
    block("storefrontsign", {
        "variantgroups": [{"code": "sign", "states": signs}, {"code": "half", "states": ["l", "r"]}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Wood", "drawtype": "json", "shapeByType": by_type,
        "lightHsvByType": light_by, "lightAbsorptionByType": dict({k: 0 for k in light_by}, **{"*": 99}),
        "resistance": 4, "sounds": WOOD,
    }, "Storefront fascia carrying half of a store's sign: two side by side make one sign centred over a two-wide door")
    wall_family("citydeco", "Plaster Wall", {1: "cityplaster"}, [
        Decor("mailboxes", "Mailboxes", {2: plate("Boxes", (1, 1, -1.5), (15, 15, 0), "mailboxes", "brass")}),
        Decor("directory", "Directory Board", {2: L11.directory()}),  # (l11art) frame, felt, title plate and letter rows
        Decor("missingposter", "Missing Poster", {2: [bx("Poster", (3, 2, -0.1), (13, 14, 0), "missingposter", faces=("north",), full=True)]}),
    ] + [Decor(f"gallery{i}", "Painting", {2: plate("Picture", (1, 1, -0.8), (15, 15, 0), f"gallery{i}", "gilt")}) for i in range(8)],
                material="Stone", sounds=STONE)
    # (B12) The station sign shows the middle 20 rows of its texture (the name in a pixel face, drawn there at the
    # world's density); the wall lamp is a glass globe in a cage of bars, on a back plate, the cage no longer painted
    sign_ = plate("Sign", (0, 3, -0.6), (16, 13, 0), "stationsign", "blackmetal")
    sign_[0]["faces"]["north"]["uv"] = [0, 3, 16, 13]
    lamp = [bx("Base", (4, 2, -1), (12, 12, 0), "metaldark", faces=("north", "east", "west", "up", "down")),
            bx("Glass", (5.5, 3.5, -3.5), (10.5, 10.5, -1), "subwaylampglass", glow=230, faces=("north", "east", "west", "up", "down")),
            bx("RingT", (5, 10.5, -4), (11, 11, -1), "metaldark", faces=("north", "east", "west", "up", "down")),
            bx("RingB", (5, 3, -4), (11, 3.5, -1), "metaldark", faces=("north", "east", "west", "up", "down"))]
    for i, x in enumerate((5.0, 7.75, 10.5)):
        lamp.append(bx(f"BarF{i}", (x, 3.5, -4), (x + 0.5, 10.5, -3.5), "metaldark", faces=("north", "east", "west")))
    for i, z in enumerate((-2.5,)):
        lamp.append(bx(f"BarL{i}", (5, 3.5, z), (5.5, 10.5, z + 0.5), "metaldark", faces=("west", "north", "south")))
        lamp.append(bx(f"BarR{i}", (10.5, 3.5, z), (11, 10.5, z + 0.5), "metaldark", faces=("east", "north", "south")))
    wall_family("subwaydeco", "Subway Tiles", {1: "subwaywall-tile"}, [
        Decor("stationsign", "Station Sign", {3: sign_}),
        Decor("subwaymap", "Subway Map", {2: plate("Map", (2, 1, -0.8), (14, 15, 0), "subwaymap", "steel")}),
        Decor("subwayad", "Advertisement", {2: plate("Ad", (1, 1, -0.6), (15, 15, 0), "subwayad", "steeldark")}),
        Decor("subwaylamp", "Wall Lamp", {3: lamp}, light=[8, 2, 11]),
    ], material="Stone", sounds=STONE,
                textures={"subwaywall-tile": {"base": "block/detail/subwaywall-tile", "alternates": [
                    {"base": f"block/detail/subwaywall-tile{v}"} for v in ("-2", "-3")]}})


D4_TRAFFIC = True  # (graphics pass D4) domed lenses and a second signal face; False: B12's heads


def props():
    pole = [bx("Pole", (7, 0, 7), (9, 50, 9), "trafficyellow"), bx("Base", (6, 0, 6), (10, 2, 10), "metaldark")]

    def head_d4(lens_top, lens_mid, lens_low, glow_top=0, glow_mid=0):
        """(D4) B12 carried the fronts unseen (C+); seen at last, the lenses were flat squares and the second head a
        blank yellow box. Now: each lens has a domed centre standing out of it (the lens picture's middle on a smaller
        face in front, so the glass reads as a dome with a rim) under B12's visor, and the second head is a whole
        signal face too: the first turned to face east."""
        face = [bx("Plate", (4, 33.5, 2.5), (12, 50.5, 3), "blackmetal", faces=("north", "east", "west", "up", "down"))]
        for nm, (lens, glow, y0) in (("Top", (lens_top, glow_top, 44.5)), ("Mid", (lens_mid, glow_mid, 40)), ("Low", (lens_low, 0, 35.5))):
            face += [bx(nm, (6, y0, 2.4), (10, y0 + 4, 2.5), lens, faces=("north",), full=True, glow=glow),
                     bx(nm + "Dome", (6.6, y0 + 0.6, 2.1), (9.4, y0 + 3.4, 2.4), lens, faces=("north", "east", "west", "up", "down"),
                        uv=[2.4, 2.4, 13.6, 13.6], glow=glow)]
            y = y0 + 4
            # (round 2) B12's visors kept as they were: round 1's deeper, cut-away ones hid the lenses from the street
            face += [bx(f"Hood{nm}", (5.5, y, 0.5), (10.5, y + 0.5, 2.5), "blackmetal", faces=("north", "east", "west", "up", "down")),
                     bx(f"Hood{nm}L", (5.5, y - 2.5, 1.25), (6, y, 2.5), "blackmetal", faces=("north", "east", "west", "down")),
                     bx(f"Hood{nm}R", (10, y - 2.5, 1.25), (10.5, y, 2.5), "blackmetal", faces=("north", "east", "west", "down"))]
        body = [bx("Head", (5, 34, 3), (11, 50, 7), "trafficyellow")]
        import modelkit as MK
        second = [dict(e, name=e["name"] + "E") for e in MK.turn(body + face, 1)]
        return body + face + second + [bx("Walk", (6.5, 22, 9), (9.5, 27, 11), "blackmetal")]

    def head(lens_top, lens_mid, lens_low, glow_top=0, glow_mid=0):
        if D4_TRAFFIC:
            return head_d4(lens_top, lens_mid, lens_low, glow_top, glow_mid)
        # (B12) a black back plate round the head, each lens set in it under a hood (geometry; the lenses were flat
        # squares on the yellow box)
        els = [bx("Head", (5, 34, 3), (11, 50, 7), "trafficyellow"),
               bx("Plate", (4, 33.5, 2.5), (12, 50.5, 3), "blackmetal", faces=("north", "east", "west", "up", "down")),
               bx("Top", (6, 44.5, 2.4), (10, 48.5, 2.5), lens_top, faces=("north",), full=True, glow=glow_top),
               bx("Mid", (6, 40, 2.4), (10, 44, 2.5), lens_mid, faces=("north",), full=True, glow=glow_mid),
               bx("Low", (6, 35.5, 2.4), (10, 39.5, 2.5), lens_low, faces=("north",), full=True),
               bx("Head2", (9, 34, 5), (13, 50, 11), "trafficyellow", rot=(0, -90, 0), origin=(8, 42, 8)),
               bx("Walk", (6.5, 22, 9), (9.5, 27, 11), "blackmetal")]
        for nm, y in (("Top", 48.5), ("Mid", 44.0), ("Low", 39.5)):
            els += [bx(f"Hood{nm}", (5.5, y, 0.5), (10.5, y + 0.5, 2.5), "blackmetal", faces=("north", "east", "west", "up", "down")),
                    bx(f"Hood{nm}L", (5.5, y - 2.5, 1.25), (6, y, 2.5), "blackmetal", faces=("north", "east", "west", "down")),
                    bx(f"Hood{nm}R", (10, y - 2.5, 1.25), (10.5, y, 2.5), "blackmetal", faces=("north", "east", "west", "down"))]
        return els
    prop("trafficlight", "Traffic Lights", {
        "dead": pole + head("lens-off", "lens-off", "lens-off"),
        "red": pole + head("lens-red", "lens-off", "lens-off", glow_top=255),
        "amber": pole + head("lens-off", "lens-amber", "lens-off", glow_mid=255)},
         box=(0.38, 0, 0.38, 0.62, 2, 0.62), material="Metal", sounds=METAL,
         extra={"lightHsvByType": {"*-red-*": [0, 7, 6]},
                "entityClassByType": {"*-amber-*": "BackroomsFlicker"},
                "attributesByType": {f"*-amber-{s}": {"offBlock": f"backrooms:trafficlight-dead-{s}"} for s in SIDES}},
         comment="Traffic lights on a corner: dead, stuck on red, or blinking amber over the empty junction")
    prop("busshelter", "Bus Shelter", [
        bx("Roof", (-16, 38, -2), (32, 40, 18), "steeldark"),
        bx("Back", (-16, 2, 16.5), (32, 36, 17.5), "shelterglass", faces=("north", "south"), full=True),
        bx("Frame", (-16, 0, 16), (32, 38, 18), "steeldark", faces=("up", "down", "east", "west")),
        bx("PostL", (-16, 0, 15.5), (-14.5, 38, 18), "steeldark"), bx("PostR", (30.5, 0, 15.5), (32, 38, 18), "steeldark"),
        bx("Side", (-15.95, 2, 2), (-15, 36, 16), "shelterad", faces=("east", "west"), full=True),
        bx("Seat", (-10, 7, 11), (26, 8.5, 16), "steel"), bx("SeatLegs", (-8, 0, 13), (24, 7, 14), "steeldark")],
         box=(0, 0, 0.7, 1, 2.4, 1.1), material="Metal", sounds=METAL, comment="A bus shelter. No bus has come for a long time")
    prop("newsbox", "Newspaper Box", [
        bx("Body", (3, 6, 4), (13, 20, 12), "postblue", faces=("east", "west", "south", "up", "down")),
        bx("Front", (3, 6, 4), (13, 20, 12), "newsfront", faces=("north",), full=True),
        bx("Legs", (4, 0, 5), (12, 6, 11), "metaldark")],
         box=(0.18, 0, 0.25, 0.82, 1.25, 0.75), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:paper-parchment", 2, 1), ("metalbracket", 0.4, 0.3))})
    prop("streetsign", "Street Sign", [
        bx("Pole", (7.5, 0, 7.5), (8.5, 50, 8.5), "streetgreen"),
        bx("St", (-8, 44, 7.6), (24, 48, 8.4), "streetsign-st", faces=("north", "south"), full=True),
        bx("StEdge", (-8, 44, 7.6), (24, 48, 8.4), "streetgreen", faces=("east", "west", "up", "down")),
        bx("Ave", (7.6, 39, -8), (8.4, 43, 24), "streetsign-ave", faces=("east", "west"), full=True),
        bx("AveEdge", (7.6, 39, -8), (8.4, 43, 24), "streetgreen", faces=("north", "south", "up", "down"))],
         box=(0.44, 0, 0.44, 0.56, 2, 0.56), material="Metal", sounds=METAL, comment="Street signs, in English and in Spanish")
    prop("parkingmeter", "Parking Meter", [
        bx("Post", (7.5, 0, 7.5), (8.5, 16, 8.5), "metaldark"),
        bx("Head", (5.5, 16, 6), (10.5, 25, 10), "steeldark", faces=("east", "west", "south", "up", "down")),
        bx("Face", (5.5, 16, 6), (10.5, 25, 10), "meterface", faces=("north",), full=True)],
         box=(0.34, 0, 0.37, 0.66, 1.56, 0.63), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:metalbit-copper", 1, 1), ("game:metalbit-silver", 0.15, 0), ("metalbracket", 0.5, 0.3))})
    prop("phonebooth", "Phone Booth", L11.phonebooth(),
         box=(0.06, 0, 0.06, 0.94, 2.25, 0.94), material="Metal", sounds=METAL,
         extra={"renderpass": "Transparent",  # (l11art) the panes are glass; the frame and the sign are opaque in the same pass
                "drops": drops(("scrapwire", 1, 0.5), ("glassshard", 1, 0.5), ("metalbracket", 1, 0.5), ("game:metalbit-copper", 0.5, 0.4))})
    prop("vendorcart", "Vendor's Cart", [
        bx("Body", (0, 6, 3), (16, 18, 13), "cartsteel", faces=("east", "west", "south", "up", "down")),
        bx("Front", (0, 6, 3), (16, 18, 13), "cartfront", faces=("north",), full=True),
        bx("WheelL", (1, 0, 6), (3, 6, 10), "rubber"), bx("WheelR", (13, 0, 6), (15, 6, 10), "rubber"),
        bx("Pole", (7.5, 18, 7.5), (8.5, 34, 8.5), "steel"),
        bx("Umbrella", (-6, 34, -6), (22, 36, 22), "umbrella", faces=("up", "down"), full=True),
        bx("UmbrellaEdge", (-6, 34, -6), (22, 36, 22), "canopy", faces=("north", "south", "east", "west"))],
         box=(0, 0, 0.18, 1, 1.12, 0.82), material="Metal", sounds=METAL,
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:almondwater", "backrooms:almondwater", "backrooms:waterbottle",
                                               "backrooms:almondwaterblue", "backrooms:almondwatergreen"], "restock": True}},
         comment="A street vendor's cart, still selling Almond Water. Nobody is minding it")
    rack = [bx("Rail", (0, 24, 7.5), (16, 25, 8.5), "chrome"), bx("PostL", (0.5, 0, 7.5), (1.5, 25, 8.5), "chrome"),
            bx("PostR", (14.5, 0, 7.5), (15.5, 25, 8.5), "chrome"), bx("Feet", (0, 0, 4), (16, 1, 12), "chrome")]
    for i, x in enumerate((2, 5, 8, 11)):
        rack.append(bx(f"Coat{i}", (x, 8, 5), (x + 2.6, 23, 11), f"fabric{i % 5}"))
    prop("clothesrack", "Clothes Rack", rack, box=(0, 0, 0.3, 1, 1.56, 0.7), material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("game:clothes-upperbody-linen-tunic", 0.2, 0), ("game:clothes-upperbody-woolen-shirt", 0.15, 0),
                                ("game:clothes-lowerbody-commoner-trousers", 0.2, 0), ("game:clothes-foot-commoner-boots", 0.12, 0),
                                ("game:clothes-upperbody-commoner-shirt", 0.15, 0), ("game:cloth-plain", 1, 0.5), ("metalbracket", 0.5, 0.3),
                                # (Level 974: now and then a plush toy left on a rack, cute)
                                ("l974-plush-bunny", 0.01, 0), ("l974-plush-bear", 0.01, 0))})
    prop("shoppingcart", "Shopping Cart", [
        bx("Basket", (2, 8, 1), (14, 18, 14), "cartwire"), bx("Handle", (2, 18, 14), (14, 19, 15), "redmetal"),
        bx("Frame", (3, 2, 2), (13, 8, 13), "chrome", faces=("east", "west")),
        bx("W1", (3, 0, 2), (4, 2, 3), "rubber"), bx("W2", (12, 0, 2), (13, 2, 3), "rubber"),
        bx("W3", (3, 0, 12), (4, 2, 13), "rubber"), bx("W4", (12, 0, 12), (13, 2, 13), "rubber")],
         box=(0.12, 0, 0.06, 0.88, 1.2, 0.94), material="Metal", sounds=METAL, extra={"drops": drops(("metalbracket", 2, 1))})
    prop("pew", "Pew", [
        bx("Seat", (0, 7, 3), (16, 8.5, 11), "pewwood"), bx("Back", (0, 8.5, 10.5), (16, 21, 12), "pewwood"),
        bx("EndL", (0, 0, 2.5), (1, 19, 12), "pewwood"), bx("EndR", (15, 0, 2.5), (16, 19, 12), "pewwood"),
        bx("Kneeler", (0, 2, -1), (16, 3.5, 2), "pewwood")],
         box=(0, 0, 0.12, 1, 1.3, 0.75), extra={"drops": drops(("game:plank-aged", 3, 1), ("game:metalnailsandstrips-iron", 0.4, 0.3))})
    prop("dumpster", "Dumpster", [
        bx("Body", (-6, 1, 1), (22, 18, 15), "binsgreen"), bx("Lid", (-6.5, 18, 0.5), (22.5, 19.5, 15.5), "dumpsterlid", rot=(-4, 0, 0), origin=(8, 18, 15.5)),
        bx("WheelL", (-5, 0, 3), (-3, 2, 5), "rubber"), bx("WheelR", (19, 0, 3), (21, 2, 5), "rubber"),
        bx("Lip", (-6.5, 15, 0.5), (22.5, 16, 15.5), "metaldark")],
         box=(0, 0, 0.06, 1, 1.2, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:paper-parchment", 1.5, 1), ("rottenwood", 1, 0.8), ("glassshard", 0.6, 0.5), ("game:cloth-plain", 0.4, 0.4),
                                ("game:bone", 0.4, 0.3), ("crackers", 0.3, 0.3), ("cannedbeans", 0.2, 0.2), ("metalbracket", 0.4, 0.3))},
         comment="A dumpster in an alley. Worth going through")
    prop("trashbags", "Bags of Rubbish", [
        bx("Bag1", (1, 0, 2), (8, 7, 9), "trashbag"), bx("Tie1", (4, 7, 5), (5, 8.5, 6), "trashbag"),
        bx("Bag2", (8, 0, 4), (15, 8, 12), "trashbag"), bx("Tie2", (11, 8, 7.5), (12, 9.5, 8.5), "trashbag"),
        bx("Bag3", (3, 0, 9), (9, 5, 15), "trashbag")],
         box=(0.06, 0, 0.12, 0.94, 0.5, 0.94), oriented=False, material="Cloth", sounds=CLOTH,
         extra={"drops": drops(("game:paper-parchment", 1, 0.8), ("rottenwood", 0.6, 0.5), ("game:bone", 0.3, 0.3), ("glassshard", 0.3, 0.3),
                                ("game:drygrass", 0.4, 0.4))})
    prop("acunit", "Air Conditioning Unit", [
        bx("Body", (0, 0, 2), (16, 13, 14), "acgrey", faces=("north", "east", "west", "south", "down")),
        bx("Grille", (0, 0, 2), (16, 13, 14), "acgrille", faces=("up",), full=True),
        bx("Duct", (6, 3, 14), (10, 7, 18), "steel")], box=(0, 0, 0.12, 1, 0.81, 0.88), material="Metal", sounds=METAL)
    legs = [bx(f"Leg{i}", (x, 0, z), (x + 1.5, 26, z + 1.5), "metaldark") for i, (x, z) in enumerate(((-10, -10), (24.5, -10), (-10, 24.5), (24.5, 24.5)))]
    prop("watertank", "Water Tank", legs + [bx("Deck", (-12, 26, -12), (28, 28, 28), "tankwood")]
         + cyl("Tank", 8, 8, 18, 28, 66, "tankwood")
         + [bx("Band1", (-10.5, 36, -10.5), (26.5, 37, 26.5), "metaldark", faces=("north", "south", "east", "west")),
            bx("Band2", (-10.5, 52, -10.5), (26.5, 53, 26.5), "metaldark", faces=("north", "south", "east", "west")),
            bx("Roof1", (-8, 66, -8), (24, 70, 24), "tankwood"), bx("Roof2", (-2, 70, -2), (18, 74, 18), "tankwood"),
            bx("Cap", (5, 74, 5), (11, 78, 11), "tankwood")],
         box=(0, 0, 0, 1, 1, 1), oriented=False, sounds=WOOD, comment="An old wooden water tank on a brick building's roof")
    mast = [bx("Mast", (7, 0, 7), (9, 120, 9), "steel"), bx("Light", (6.5, 120, 6.5), (9.5, 123, 9.5), "lens-red", glow=255)]
    for k, y in enumerate(range(16, 120, 24)):
        mast += [bx(f"BarX{k}", (2, y, 7.5), (14, y + 1, 8.5), "steel"), bx(f"BarZ{k}", (7.5, y + 12, 2), (8.5, y + 13, 14), "steel")]
    prop("antenna", "Radio Mast", mast, box=(0.4, 0, 0.4, 0.6, 1, 0.6), oriented=False, material="Metal", sounds=METAL)
    # A billboard on a brick roof: a steel frame on legs, the poster three blocks wide facing the street (north), a
    # catwalk along its foot and three lamps over it, long dead. Drawn from the middle block of the three
    frame = [bx("LegL", (-14, 0, 9), (-12, 14, 11), "billboardframe"), bx("LegR", (28, 0, 9), (30, 14, 11), "billboardframe"),
             bx("LegM", (7, 0, 9), (9, 14, 11), "billboardframe"),
             # Raking struts from the roof behind up to the back of the frame
             bx("StrutL", (-14, 0, 19), (-12, 31, 21), "billboardframe", rot=(-20, 0, 0), origin=(-13, 0, 20)),
             bx("StrutR", (28, 0, 19), (30, 31, 21), "billboardframe", rot=(-20, 0, 0), origin=(29, 0, 20)),
             bx("Back", (-16, 14, 8), (32, 38, 9), "billboardframe", faces=("south", "east", "west", "up", "down")),
             bx("Trim", (-16.5, 13.5, 7.5), (32.5, 14.5, 8.5), "billboardframe"),
             bx("TrimTop", (-16.5, 37.5, 7.5), (32.5, 38.5, 8.5), "billboardframe"),
             bx("Catwalk", (-16, 12.5, 2), (32, 13.5, 8), "billboardframe"),
             bx("Rail", (-16, 16, 1.5), (32, 16.5, 2), "billboardframe")]
    for k, x in enumerate((-8, 8, 24)):
        frame += [bx(f"Arm{k}", (x - 0.5, 38, 2), (x + 0.5, 39, 8), "billboardframe"),
                  bx(f"Lamp{k}", (x - 2, 36.5, 1), (x + 2, 38.5, 3.5), "metaldark")]
    prop("billboard", "Billboard", {k: frame + [bx("Poster", (-16, 14, 7.9), (32, 38, 8), f"billboard-{k}", faces=("north",), full=True)]
                                    for k in BILLBOARDS},
         box=(0, 0, 0.5, 1, 0.9, 0.75), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 2, 1), ("game:metalnailsandstrips-iron", 0.6, 0.4), ("game:paper-parchment", 1, 1)),
                # (B12) each poster has a second version with a sheet peeling at a corner
                "textures": {f"billboard-{k}": {"base": f"block/detail/billboard-{k}", "alternates": [{"base": f"block/detail/billboard-{k}-2"}]}
                             for k in BILLBOARDS}},
         comment="A billboard on a brick roof, its poster to the street, its lamps long dead")

    # An advertising pillar on a street corner: a round column pasted all round with posters, a moulded cap and a finial
    def column(k):
        return ([bx("Plinth", (2, 0, 2), (14, 3, 14), "pillargreen"), bx("PlinthB", (1, 0, 4), (15, 3, 12), "pillargreen"),
                 bx("PlinthC", (4, 0, 1), (12, 3, 15), "pillargreen")]
                + [bx("Column", (2, 3, 3.8), (14, 39, 12.2), f"adpillar-{k}", faces=("north", "south", "east", "west"), full=True),
                   bx("ColumnB", (3.8, 3, 2), (12.2, 39, 14), f"adpillar-{k}", faces=("north", "south", "east", "west"), full=True)]
                + [bx("Band", (1.5, 39, 3.5), (14.5, 41, 12.5), "pillargreen"), bx("BandB", (3.5, 39, 1.5), (12.5, 41, 14.5), "pillargreen"),
                   bx("Cap", (2.5, 41, 2.5), (13.5, 44, 13.5), "pillargreen"), bx("Dome", (5, 44, 5), (11, 46, 11), "pillargreen"),
                   bx("Finial", (7.5, 46, 7.5), (8.5, 49, 8.5), "metaldark")])
    prop("adpillar", "Advertising Pillar", {k: column(k) for k in PILLARS}, box=(0.1, 0, 0.1, 0.9, 1.5, 0.9), oriented=False,
         material="Stone", sounds=STONE, extra={"drops": drops(("game:paper-parchment", 2, 1))},
         comment="An advertising pillar on a street corner, pasted all round with posters")
    prop("postbox", "Mailbox", L11.postbox(),
         box=(0.18, 0, 0.25, 0.82, 1.31, 0.75), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:paper-parchment", 1.5, 1), ("metalbracket", 0.5, 0.3))})


def lang():
    for k, v in {
        "level-11": "Level 11: The Endless City",
        "levelhint-11": "Safe, quiet, and endless. Almond Water is everywhere; the ways out are as many as they are hard to spot.",
        "noclip": "You lean on the boards, and they aren't there. You fall through, and stand up on a sidewalk.",
        "darkpassage": "The dark beyond the doorway takes the alley, the city and the light.",
        "elevator-outoforder": "OUT OF ORDER",
        "item-almondwater": "Almond Water",
    }.items():
        if k == "item-almondwater":
            continue
        LANG[k] = v


def thresholds():
    """The thin spot: what is left where a two-way threshold put someone down in a place with no threshold of its
    own. A pale, wavering seam in the air; step through it to go back."""
    rng = random.Random(1111)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for y in range(S):
        # The seam wanders a little from side to side as it rises
        centre = 15.5 + 2.2 * math.sin(y / 5.0) + 1.1 * math.sin(y / 2.3 + 1.0)
        for x in range(S):
            d = abs(x - centre)
            seam = max(0.0, 1 - d / 1.6)            # the bright tear itself
            haze = max(0.0, 1 - d / 11.0) ** 2      # the shimmer round it
            streak = 0.6 + 0.4 * math.sin(x * 1.9 + y * 0.35)
            a = min(1.0, 0.85 * seam + 0.32 * haze * streak + rng.uniform(-0.03, 0.03) * haze)
            edge = min(1.0, y / 5.0, (S - 1 - y) / 4.0)  # fades out at the floor and overhead
            if a * edge <= 0.02:
                continue
            c = blend((214, 204, 150), (255, 252, 232), seam)
            px[x, y] = c[:3] + (int(255 * a * edge),)
    save(img, "thinspot")
    from detail_kit import shape
    path = shape("thinspot", [
        bx("SeamA", (1, 0, 7.95), (15, 30, 8.05), "thinspot", faces=("north", "south"), full=True, glow=150),
        bx("SeamB", (7.95, 0, 1), (8.05, 30, 15), "thinspot", faces=("east", "west"), full=True, glow=150)])
    block("thinspot", {
        "creativeinventory": {"general": ["*"]}, "blockmaterial": "Glass", "drawtype": "json", "shape": {"base": path},
        "renderPass": "Transparent", "faceCullMode": "NeverCull",
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionbox": {"x1": 0.2, "y1": 0, "z1": 0.2, "x2": 0.8, "y2": 1.85, "z2": 0.8},
        "lightAbsorption": 0, "lightHsv": [8, 2, 4], "resistance": 999, "drops": [], "behaviors": threshold("thinspot"),
        "sounds": {"ambient": "game:effect/translocate-idle", "ambientBlockCount": 3},
        "particleProperties": [{
            "hsvaColor": [{"avg": 35, "var": 8}, {"avg": 50, "var": 20}, {"avg": 235, "var": 20}, {"avg": 130, "var": 40}],
            "gravityEffect": {"avg": -0.01, "var": 0.01}, "posOffset": [{"avg": 0, "var": 0.3}, {"avg": 0.4, "var": 0.8}, {"avg": 0, "var": 0.3}],
            "velocity": [{"avg": 0, "var": 0.03}, {"avg": 0.03, "var": 0.02}, {"avg": 0, "var": 0.03}], "quantity": {"avg": 0.12},
            "size": {"avg": 0.08, "var": 0.04}, "particleModel": "Quad", "lifeLength": {"avg": 1.6, "var": 0.8},
            "vertexFlags": 96, "selfPropelled": True}],
    }, "A thin spot: the way back from a place a two-way threshold put someone down. Step through it to return")
    name("thinspot", "Thin Spot")
    LANG["blockdesc-thinspot"] = "The world is thin here: something came through. Step through, and you go back the way it came."
    LANG["blockhelp-thinspot"] = "Step through"
    LANG["thinspot-nowhere"] = "It leads nowhere."


def generate():
    generate_textures()
    facades()
    decorations()
    props()
    thresholds()
    lang()
