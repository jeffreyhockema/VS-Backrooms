"""Level 11, the Endless City: its textures, blocks, props, wall decorations and names. Called from gen_detail.py,
which writes them out along with everything else (python tools/gen_detail.py).

Façades come in six styles (curtain glass, mirror glass, red and dark brick, limestone, concrete), each with a plain
wall, a window (dark, lit, or with the blinds down) and the band at each floor. Façade blocks show their style on one
face, the outside, and plaster on the others, like the Suburbs' house walls.
"""
import math
import os
import random

from PIL import Image, ImageDraw

import texlib
from detail_kit import (ASSETS, CLOTH, GLASS, LANG, METAL, ROTATE, SIDES, STONE, WOOD, Decor, block, bx, cube, cyl, name,
                        prop, seam_halves, shape, wall_family, write_json)
from detail_textures import S, noise, rgb, save, text
from gen_detail import cube_block, plate
from detail_kit import T, seed_of


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


def sash(frame, glass, key, lit=False, blinds=False):
    """A sash window filling the face: a painted frame, two panes, the meeting rail across the middle."""
    img = Image.new("RGBA", (S, S), rgb(frame))
    d = ImageDraw.Draw(img)
    if lit:
        inner = texlib.vertical_gradient((255, 226, 150), (230, 170, 90))
    elif blinds:
        inner = Image.new("RGBA", (S, S), (222, 214, 196, 255))
        dd = ImageDraw.Draw(inner)
        for y in range(0, S, 3):
            dd.line([0, y, S - 1, y], fill=(176, 168, 150, 255))
    else:
        inner = texlib.vertical_gradient(glass[0], glass[1])
        ImageDraw.Draw(inner).line([4, 26, 26, 4], fill=blend(glass[0], (255, 255, 255), 0.15), width=2)
    img.paste(inner.crop((4, 4, S - 4, S - 4)), (4, 4))
    d.rectangle([3, 3, S - 4, S - 4], outline=shade(T.hexrgb(frame), 0.75))
    d.rectangle([3, 15, S - 4, 17], fill=rgb(frame))
    if lit:
        # Curtains drawn back at the sides
        d.rectangle([4, 4, 7, S - 5], fill=(190, 80, 60, 255))
        d.rectangle([S - 8, 4, S - 5, S - 5], fill=(190, 80, 60, 255))
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

    # Brick, red and dark: sash windows with white or dark frames, a band of stone at each floor
    for style, base, mortar, frame in (("brick", 0xA2482E, 0xB8AC98, 0xEDEAE2), ("brickdark", 0x5E3A30, 0x8E8678, 0x2E3A34)):
        wall = bricks(base, mortar, style)
        save(wall, f"facade-{style}-wall")
        save(wall, f"pier-{style}")
        b = wall.copy()
        d = ImageDraw.Draw(b)
        d.rectangle([0, 0, S - 1, 5], fill=(196, 188, 170, 255))
        d.line([0, 5, S - 1, 5], fill=(120, 112, 100, 255))
        save(b, f"facade-{style}-band")
        glass = ((60, 70, 84), (24, 28, 36))
        save(sash(frame, glass, style + "w"), f"facade-{style}-window")
        save(sash(frame, glass, style + "l", lit=True), f"facade-{style}-lit")
        save(sash(frame, glass, style + "b", blinds=True), f"facade-{style}-blinds")

    # Limestone: big ashlar blocks, deep windows between, a moulded cornice at each floor
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
    glass = ((54, 62, 72), (22, 26, 32))
    for part, kw in (("window", {}), ("lit", {"lit": True}), ("blinds", {"blinds": True})):
        win = sash(0x3A3630, glass, "stone" + part, **kw)
        d = ImageDraw.Draw(win)
        d.rectangle([0, 0, S - 1, S - 1], outline=(200, 190, 166, 255), width=2)  # the stone reveal
        save(win, f"facade-stone-{part}")

    # Concrete: board-marked, with tie holes; ribbon windows in thin aluminium frames
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
    for part, top, bottom in (("window", (90, 108, 126), (40, 50, 62)), ("lit", (246, 230, 186), (216, 190, 140)), ("blinds", (200, 196, 186), (180, 176, 166))):
        win = texlib.vertical_gradient(top, bottom)
        d = ImageDraw.Draw(win)
        if part == "blinds":
            for y in range(0, S, 3):
                d.line([0, y, S - 1, y], fill=(160, 156, 148, 255))
        d.line([0, 0, 0, S - 1], fill=(150, 152, 156, 255), width=2)
        d.line([16, 0, 16, S - 1], fill=(150, 152, 156, 255))
        d.rectangle([0, 0, S - 1, 1], fill=(150, 152, 156, 255))
        d.rectangle([0, S - 2, S - 1, S - 1], fill=(150, 152, 156, 255))
        save(win, f"facade-concrete-{part}")

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
    for side, x in (("raill", 9), ("railr", 20)):
        img = ballast.copy()
        d = ImageDraw.Draw(img)
        for y in range(2, S, 8):
            d.rectangle([0, y, S - 1, y + 3], fill=(70, 50, 36, 255))  # sleepers
        d.rectangle([x, 0, x + 2, S - 1], fill=(120, 116, 112, 255))
        d.line([x + 1, 0, x + 1, S - 1], fill=(176, 172, 166, 255))  # the worn top of the rail
        save(img, f"subwayfloor-{side}")
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
    # Steel doors: grey, with a stencilled word
    for code, color, label, sign in (("basementdoor", 0x707470, "BASEMENT", None), ("substationdoor", 0x6A6E68, None, "danger"),
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
    img = Image.new("RGBA", (S, S), rgb(0x141414))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A8070))
    for k, line in enumerate(("DIRECTORY", "1  LOBBY", "2-11 ----", "12 ?????")):
        text(img, line, (2, 2 + k * 7, S - 2, 9 + k * 7), 0xE8E8E0, 4)
    save(img, "directory")
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
    img = Image.new("RGBA", (S, S), rgb(0x1E3A7A))
    d = ImageDraw.Draw(img)
    d.rectangle([6, 6, 25, 9], fill=rgb(0x101010))
    text(img, "MAIL", (2, 14, S - 2, 24), 0xFFFFFF, 7)
    save(img, "postfront")
    img = Image.new("RGBA", (S, S), rgb(0x2A2C30))
    text(img, "TELEPHONE", (0, 8, S, 22), 0xF2F2EA, 5)
    save(img, "phonesign")
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


def generate_textures():
    facade_textures()
    street_textures()
    door_textures()
    sign_textures()
    prop_textures()
    poster_textures()


# ======================= Blocks =======================

def facades():
    by_type, sounds_by, material_by, glow_by = {}, {}, {}, {}
    for style in STYLES:
        for part in PARTS:
            for s in SIDES:
                faces = {f: {"base": "block/detail/cityplaster"} for f in ("north", "east", "south", "west")}
                faces["up"] = faces["down"] = {"base": f"block/detail/pier-{style}"}
                faces[s] = {"base": f"block/detail/facade-{style}-{part}"}
                if style == "mirror" and part != "band":
                    faces[s]["alternates"] = [{"base": f"block/detail/{k}"} for k in MIRROR_ALTERNATES]
                by_type[f"*-{style}-{part}-{s}"] = faces
            if part == "lit" and style != "mirror":
                glow_by[f"*-{style}-lit-*"] = {"glowLevel": 150}
        sounds_by[f"*-{style}-*"] = GLASS if style in ("glass", "mirror") else STONE
    block("cityfacade", {
        "variantgroups": [{"code": "style", "states": STYLES}, {"code": "part", "states": PARTS}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "cube", "texturesByType": by_type,
        "lightAbsorption": 99, "resistance": 6, "soundsByType": sounds_by, "vertexFlagsByType": glow_by,
    }, "The Endless City's façades: the style on the outside face, plaster within")
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
    cube_block("cityroof", "Tar and Gravel Roof", ["gravel"], {"gravel": "cityroof"})
    cube_block("cityplaster", "Plaster Wall", ["plain"], {"plain": "cityplaster"})
    cube_block("stainedglass", "Stained Glass", ["plain"], {"plain": "stainedglass"}, material="Glass", sounds=GLASS,
               vertexFlags={"glowLevel": 110}, lightAbsorption=0)
    cube_block("cityfloor", {"marble": "Marble Floor", "plaza": "Granite Pavers", "garage": "Concrete"}, ["marble", "plaza", "garage"],
               {"marble": "cityfloor-marble", "plaza": "cityfloor-plaza", "garage": "cityfloor-garage"})
    cube_block("subwayfloor", {"bed": "Ballast", "raill": "Track", "railr": "Track", "platform": "Platform", "edge": "Platform Edge"},
               ["bed", "raill", "railr", "platform", "edge"],
               {"bed": "subwayfloor-bed", "raill": ("subwayfloor-raill", 0), "railr": ("subwayfloor-railr", 0),
                "platform": "subwayfloor-platform", "edge": "subwayfloor-edge"})
    cube_block("subwaywall", {"tile": "Subway Tiles", "ceiling": "Tunnel Ceiling"}, ["tile", "ceiling"],
               {"tile": "subwaywall-tile", "ceiling": "subwaywall-ceiling"})
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
        Decor("directory", "Directory Board", {2: plate("Board", (2, 2, -0.8), (14, 14, 0), "directory", "wooddark")}),
        Decor("missingposter", "Missing Poster", {2: [bx("Poster", (3, 2, -0.1), (13, 14, 0), "missingposter", faces=("north",), full=True)]}),
    ] + [Decor(f"gallery{i}", "Painting", {2: plate("Picture", (1, 1, -0.8), (15, 15, 0), f"gallery{i}", "gilt")}) for i in range(8)],
                material="Stone", sounds=STONE)
    wall_family("subwaydeco", "Subway Tiles", {1: "subwaywall-tile"}, [
        Decor("stationsign", "Station Sign", {3: plate("Sign", (0, 3, -0.6), (16, 13, 0), "stationsign", "blackmetal")}),
        Decor("subwaymap", "Subway Map", {2: plate("Map", (2, 1, -0.8), (14, 15, 0), "subwaymap", "steel")}),
        Decor("subwayad", "Advertisement", {2: plate("Ad", (1, 1, -0.6), (15, 15, 0), "subwayad", "steeldark")}),
        Decor("subwaylamp", "Wall Lamp", {3: [bx("Cage", (5, 3, -4), (11, 11, 0), "subwaylampglass", glow=230),
                                              bx("Base", (4, 2, -1), (12, 12, 0), "metaldark", faces=("north", "east", "west", "up", "down"))]},
              light=[8, 2, 11]),
    ], material="Stone", sounds=STONE)


def props():
    pole = [bx("Pole", (7, 0, 7), (9, 50, 9), "trafficyellow"), bx("Base", (6, 0, 6), (10, 2, 10), "metaldark")]

    def head(lens_top, lens_mid, lens_low, glow_top=0, glow_mid=0):
        return [bx("Head", (5, 34, 3), (11, 50, 7), "trafficyellow"),
                bx("Top", (6, 44.5, 2.9), (10, 48.5, 3), lens_top, faces=("north",), full=True, glow=glow_top),
                bx("Mid", (6, 40, 2.9), (10, 44, 3), lens_mid, faces=("north",), full=True, glow=glow_mid),
                bx("Low", (6, 35.5, 2.9), (10, 39.5, 3), lens_low, faces=("north",), full=True),
                bx("Head2", (9, 34, 5), (13, 50, 11), "trafficyellow", rot=(0, -90, 0), origin=(8, 42, 8)),
                bx("Walk", (6.5, 22, 9), (9.5, 27, 11), "blackmetal")]
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
    prop("phonebooth", "Phone Booth", [
        bx("Base", (1, 0, 1), (15, 2, 15), "steeldark"), bx("Top", (1, 34, 1), (15, 36, 15), "steeldark"),
        bx("Sign", (1, 30, 0.9), (15, 34, 1), "phonesign", faces=("north",), full=True),
        bx("GlassL", (1, 2, 1), (1.5, 30, 15), "shelterglass", faces=("east", "west"), full=True),
        bx("GlassR", (14.5, 2, 1), (15, 30, 15), "shelterglass", faces=("east", "west"), full=True),
        bx("Back", (1.05, 2, 14.5), (14.95, 30, 15), "steel"),  # (its ends inside the side glass, not in its faces)
        bx("Phone", (6, 14, 12), (10, 22, 14.5), "blackmetal"), bx("Handset", (5, 16, 11.5), (6, 21, 12.5), "blackmetal")],
         box=(0.06, 0, 0.06, 0.94, 2.25, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("scrapwire", 1, 0.5), ("glassshard", 1, 0.5), ("metalbracket", 1, 0.5), ("game:metalbit-copper", 0.5, 0.4))})
    prop("vendorcart", "Vendor's Cart", [
        bx("Body", (0, 6, 3), (16, 18, 13), "cartsteel", faces=("east", "west", "south", "up", "down")),
        bx("Front", (0, 6, 3), (16, 18, 13), "cartfront", faces=("north",), full=True),
        bx("WheelL", (1, 0, 6), (3, 6, 10), "rubber"), bx("WheelR", (13, 0, 6), (15, 6, 10), "rubber"),
        bx("Pole", (7.5, 18, 7.5), (8.5, 34, 8.5), "steel"),
        bx("Umbrella", (-6, 34, -6), (22, 36, 22), "umbrella", faces=("up", "down"), full=True),
        bx("UmbrellaEdge", (-6, 34, -6), (22, 36, 22), "canopy", faces=("north", "south", "east", "west"))],
         box=(0, 0, 0.18, 1, 1.12, 0.82), material="Metal", sounds=METAL,
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:almondwater", "backrooms:almondwater", "backrooms:waterbottle"], "restock": True}},
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
         extra={"drops": drops(("metalbracket", 2, 1), ("game:metalnailsandstrips-iron", 0.6, 0.4), ("game:paper-parchment", 1, 1))},
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
    prop("postbox", "Mailbox", [
        bx("Body", (3, 2, 4), (13, 18, 12), "postblue", faces=("east", "west", "south", "down")),
        bx("Front", (3, 2, 4), (13, 18, 12), "postfront", faces=("north",), full=True),
        bx("Dome", (3.5, 18, 4.5), (12.5, 21, 11.5), "postblue"), bx("Legs", (4, 0, 5), (12, 2, 11), "metaldark")],
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
