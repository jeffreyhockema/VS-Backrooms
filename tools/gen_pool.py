"""Level 37, the Poolrooms: its tile, slits, rails, ladders, door, and what is lost there. Called from gen_detail.py,
which writes them out along with everything else (python tools/gen_detail.py).

Everything in the Poolrooms is the same white ceramic tile, small square tiles with thin grout, glazed and
undamaged. The slits in the walls glow warm white (they are where the light comes from); the arches round a
rotunda glow whiter. In the Sanguine Reservoir a red film lies in the grout.
"""
import math
import os
import random

from PIL import Image, ImageDraw

from detail_kit import ASSETS, CLOTH, LANG, METAL, SIDES, STONE, ROTATE, block, bx, cube, ground_storable, name, prop, shape, write_json
from detail_textures import S, noise, rgb, save, text
from gen_deep import TRANSFORMS, door_block, drops, threshold
from gen_detail import cube_block
from detail_kit import T, seed_of


def tile_texture(tile, grout, key, film=None, glow=0.0, coping=False):
    """Eight by eight small square tiles to a block face (about 12 cm each, the mosaic of the renders), thin pale
    grout, each tile a hair different, glazed. Drawn at 64 px so the grout is one pixel in eight: at any distance
    the wall reads as white tile, not as a net. Coping has a broad rounded lip round its edge instead."""
    rng = random.Random(seed_of(key))
    size, count = 64, 8
    w = size // count
    img = Image.new("RGBA", (size, size), grout + (255,))
    px = img.load()
    for ty in range(count):
        for tx in range(count):
            f = rng.uniform(0.985, 1.012)
            base = tuple(min(255, int(c * f)) for c in tile)
            for y in range(ty * w + 1, ty * w + w):
                for x in range(tx * w + 1, tx * w + w):
                    c = list(base)
                    # A glaze highlight along the top and left of each tile
                    if y == ty * w + 1 or x == tx * w + 1:
                        c = [min(255, v + 5) for v in c]
                    n = rng.uniform(-2, 2)
                    px[x, y] = (int(min(255, c[0] + n)), int(min(255, c[1] + n)), int(min(255, c[2] + n)), 255)
    if coping:
        # A broad lip of solid tile round the edge, catching the light
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, size - 1, size - 1], outline=tuple(min(255, c + 6) for c in tile) + (255,), width=10)
        d.rectangle([10, 10, size - 11, size - 11], outline=tuple(max(0, c - 22) for c in tile) + (255,), width=2)
    if film:
        # A red film settled in the grout, heavier in places
        for y in range(size):
            for x in range(size):
                if x % w == 0 or y % w == 0:
                    if rng.random() < 0.8:
                        px[x, y] = film + (255,)
        T.blotch(img, (rng.randrange(size), rng.randrange(size)), 20, film, 0.25, seed_of(key + "b"))
    return img


def textures():
    save(tile_texture((244, 244, 238), (226, 224, 216), "pooltile"), "pooltile")
    save(tile_texture((255, 246, 216), (226, 210, 172), "poolsunlit"), "poolsunlit")
    save(tile_texture((236, 226, 224), (118, 22, 26), "poolred", film=(128, 18, 24)), "poolred")
    save(tile_texture((240, 240, 234), (226, 224, 216), "poolcoping", coping=True), "poolcoping")
    img = noise(0x07080A, 2, "poolvoid")
    save(img, "poolvoid")

    # The glare of a slit: warm white, brightest in the middle, nothing of what lies beyond to be seen
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = abs(x - 15.5) / 16
            v = 255 - int(40 * d * d)
            px[x, y] = (v, max(0, v - 8), max(0, v - 34), 255)
    save(img, "slitglow")
    img = Image.new("RGBA", (S, S), (250, 252, 255, 255))
    save(T.noise_fill((248, 250, 252), 2, seed_of("archglow")), "archglow")

    # Polished stainless for the handrails and ladders, stretched over each face: a bright body, a white glint
    # along the top where the light catches it, a soft reflection band, and a dark line underneath
    img = T.noise_fill(T.hexrgb(0xE4E8EC), 2, seed_of("poolchrome"))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            if y < 4:
                v = (255, 255, 255)
            elif y < 6:
                v = (242, 246, 250)
            elif 14 <= y < 18:
                v = (min(255, r + 8), min(255, g + 8), min(255, b + 8))
            elif y >= 28:
                v = (96, 102, 110)
            elif y >= 24:
                v = (176, 182, 190)
            else:
                v = (r, g, b)
            px[x, y] = v + (255,)
    save(img, "poolchrome")

    # The door marked POOL: cyan paint, a round porthole, the word in white
    for part in ("lower", "upper"):
        img = noise(0x3CC8C8, 4, "pooldoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x1E8A8C), width=2)
        if part == "upper":
            d.ellipse([9, 3, 22, 16], fill=rgb(0x9AD8DA), outline=rgb(0xE8F4F4), width=2)
            text(img, "POOL", (3, 19, S - 3, 29), 0xFFFFFF, 8)
        else:
            d.rectangle([22, 2, 27, 5], fill=rgb(0xD8DCDC))  # push plate
            d.rectangle([3, 22, S - 4, 28], fill=rgb(0x2AA4A6))  # kick plate
        save(img, f"pooldoor-{part}")

    # What is lost here
    img = Image.new("RGBA", (S, S), rgb(0xF4F0E8))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        d.rectangle([0, y, S - 1, y + 3], fill=rgb(0x3E8EC8))
    save(T.noise_fill_over(img, 4, seed_of("towel")) if hasattr(T, "noise_fill_over") else img, "towel")
    save(noise(0xE85A8A, 3, "noodle"), "noodle")
    save(noise(0x2A6AD8, 3, "flipflop"), "flipflop")
    img = noise(0xF2F2F2, 6, "epsom")
    rng = random.Random(seed_of("epsomc"))
    px = img.load()
    for _ in range(60):
        x, y = rng.randrange(S), rng.randrange(S)
        px[x, y] = (255, 255, 255, 255)
        if x + 1 < S:
            px[x + 1, y] = (230, 236, 240, 255)
    save(img, "epsomcrust")
    img = noise(0xC81428, 6, "redsprout")
    save(img, "redsprout")
    b13_textures()


def item_textures():
    # Epsom salt: a little heap of white crystals
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("epsomitem"))
    d.ellipse([5, 15, 27, 28], fill=(232, 236, 240, 255))
    for _ in range(40):
        x, y = rng.randrange(7, 25), rng.randrange(13, 26)
        c = rng.choice([(255, 255, 255, 255), (210, 220, 228, 255), (244, 248, 250, 255)])
        d.rectangle([x, y, x + 1, y + 1], fill=c)
    T.save(img, "item/epsomsalt.png")
    # Red water: a bottle of what the Reservoir's sprouts grow in
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([13, 3, 18, 8], fill=(200, 210, 210, 255))
    d.rectangle([12, 1, 19, 3], fill=(120, 90, 60, 255))
    d.rounded_rectangle([9, 8, 22, 29], 3, fill=(150, 18, 30, 235), outline=(210, 220, 225, 255))
    d.line([11, 11, 11, 25], fill=(220, 90, 100, 255))
    T.save(img, "item/redwater.png")


def blocks():
    # (B13) the mosaic in versions that share their grout and ground (three; the coping two), picked by height as well
    # (randomizeAxes xyz), so a wall's column does not stack one version
    import gen_detail as gd
    gd.ALTS.update({k: [f"{k}-{v}" for v in range(2, n + 1)] for k, n in POOL_VERSIONS.items()})
    cube_block("pooltile", {"plain": "Pool Tile", "sunlit": "Sunlit Pool Tile", "red": "Pool Tile (Red Film)", "void": "Darkness", "coping": "Pool Coping"},
               ["plain", "sunlit", "red", "void", "coping"],
               {"plain": "pooltile", "sunlit": "poolsunlit", "red": "poolred", "void": "poolvoid", "coping": "poolcoping"},
               comment="Level 37: white ceramic tile, every surface; lit warm where light falls through a slit; red-filmed in the Reservoir; the black of a tunnel mouth",
               lightHsvByType={"*-sunlit": [8, 2, 5]}, lightAbsorptionByType={"*-sunlit": 0, "*": 99}, randomizeAxes="xyz")

    # Tile walls carrying a slit of light, a tiled archway (an opening onto light), or a handrail on one face (modelled facing north). The
    # slit is an opening: tile reveals frame a glow set back into the wall, so it reads as light coming through
    wall = cube("pooltile")
    slit = [bx("Back", (0, 0, 1.5), (16, 16, 16), "pooltile", faces=("east", "south", "west", "up", "down")),
            bx("FrontL", (0, 0, 0), (6, 16, 1.5), "pooltile", faces=("north", "east", "west", "up", "down")),
            bx("FrontR", (10, 0, 0), (16, 16, 1.5), "pooltile", faces=("north", "east", "west", "up", "down")),
            bx("Slit", (6, 0, 1.45), (10, 16, 1.5), "slitglow", glow=255, faces=("north",), full=True)]
    # Keep the mosaic in register with the plain wall beside it
    slit[2]["faces"]["north"]["uv"] = [10, 0, 16, 16]
    slit[0]["faces"]["up"]["uv"] = slit[0]["faces"]["down"]["uv"] = [0, 1.5, 16, 16]

    def chrome(name, frm, to, upright=False):
        """A stainless part with the glint along its top (or, upright, along its left edge)."""
        el = bx(name, frm, to, "poolchrome", full=True)
        if upright:
            for f in ("north", "south", "east", "west"):
                el["faces"][f]["rotation"] = 90
        return el

    def arch_b11(round_top):
        """A tiled archway: an opening in the wall, tile reveals framing a glow set back 2 pixels, as if daylight came
        from beyond. Two of the plain kind stack under one rounded one (an opening 14 wide, 2 blocks and a half
        high, with a semicircular head)."""
        D, X1, X2 = 2, 1, 15
        keep = ("north", "east", "west", "up", "down")

        def tile(name, x1, y1, x2, y2):
            el = bx(name, (x1, y1, 0), (x2, y2, D), "pooltile", faces=keep)
            # Keep the mosaic in register with the plain wall beside it
            el["faces"]["north"]["uv"] = [x1, 16 - y2, x2, 16 - y1]
            return el

        def glow(name, x1, y1, x2, y2):
            return bx(name, (x1, y1, D - 0.05), (x2, y2, D), "archglow", glow=255, faces=("north",), full=True)

        els = [bx("Back", (0, 0, D), (16, 16, 16), "pooltile", faces=("east", "south", "west", "up", "down"))]
        els[0]["faces"]["up"]["uv"] = els[0]["faces"]["down"]["uv"] = [0, D, 16, 16]
        if not round_top:
            els += [tile("JambL", 0, 0, X1, 16), tile("JambR", X2, 0, 16, 16), glow("Glow", X1, 0, X2, 16)]
            return els
        spring, r = 7, 7
        els += [tile("JambL", 0, 0, X1, spring), tile("JambR", X2, 0, 16, spring), glow("Glow", X1, 0, X2, spring)]
        for i in range(r):
            y = spring + i
            w = min(7, round(math.sqrt(r * r - (i + 0.5) ** 2) * 2) / 2)
            lo, hi = 8 - w, 8 + w
            els += [tile(f"HeadL{i}", 0, y, lo, y + 1), tile(f"HeadR{i}", hi, y, 16, y + 1), glow(f"Head{i}", lo, y, hi, y + 1)]
        els.append(tile("Lintel", 0, spring + r, 16, 16))
        return els

    parts = {
        "slit": slit,
        "arch": arch_b11(False),
        "archtop": arch_b11(True),
        "rail": rail_b13(wall),
    }
    by_type = {}
    for kind, els in parts.items():
        path = shape(f"poolwall-{kind}", els)
        for s in SIDES:
            by_type[f"*-{kind}-{s}"] = {"base": path, "rotateY": ROTATE[s]}
    block("poolwall", {
        "variantgroups": [{"code": "kind", "states": list(parts)}, {"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "construction": ["*-north"]},
        "blockmaterial": "Ceramic", "drawtype": "json", "shapeByType": by_type,
        "lightAbsorption": 99, "resistance": 4, "sounds": STONE,
        "lightHsvByType": {"*-slit-*": [8, 1, 18], "*-arch-*": [8, 0, 17], "*-archtop-*": [8, 0, 17]},
        "lightAbsorptionByType": {"*-slit-*": 0, "*-arch-*": 0, "*-archtop-*": 0, "*": 99},
    }, "Level 37: tile walls with a slit of glare, a tiled archway (an opening onto light), or a handrail, on one face")
    name("poolwall-slit-*", "Slit of Light")
    name("poolwall-arch-*", "Tiled Archway")
    name("poolwall-archtop-*", "Tiled Archway (Arched Head)")
    name("poolwall-rail-*", "Pool Tile with Handrail")

    pool_door_block_b13()

    # A pool ladder: two stainless rails and steps, climbable, at the edge of the water (modelled against the north side)
    prop("poolladder", "Pool Ladder", ladder_b13(chrome),
         box=(0.18, 0, 0, 0.82, 1, 0.25), material="Metal", sounds=METAL, collide=True,
         extra={"climbable": True, "drops": []})
    prop("epsomcrust", "Epsom Salt Crust", epsom_b13(),
         box=(0.12, 0, 0.18, 0.88, 0.12, 0.82), oriented=False, collide=False, material="Stone", sounds=STONE,
         comment="A crust of Epsom salt dried on a rim in the dark",
         extra={"drops": drops(("epsomsalt", 1.5, 0.5))})
    prop("lostthing", "Lost Thing", lost_b13(),
         box=(0.06, 0, 0.18, 0.94, 0.2, 0.82), collide=False, material="Cloth", sounds=CLOTH,
         comment="Something someone lost at the pool: a towel, a flip-flop, a pool noodle",
         extra={"dropsByType": {"*-towel-*": drops(("game:cloth-plain", 1, 0)), "*-flipflop-*": [], "*-noodle-*": []}})
    for k, eng in (("towel", "Towel"), ("flipflop", "Flip-Flops"), ("noodle", "Pool Noodle")):
        name(f"lostthing-{k}-*", eng)
    prop("redsprout", "Red Sprout", [
        bx("Stem1", (5, 0, 6), (6, 7, 7), "redsprout", glow=180), bx("Stem2", (9, 0, 9), (10, 9, 10), "redsprout", glow=180),
        bx("Stem3", (7, 0, 4), (8, 5, 5), "redsprout", glow=180), bx("Bud1", (4.5, 7, 5.5), (6.5, 8.5, 7.5), "redsprout", glow=255),
        bx("Bud2", (8.5, 9, 8.5), (10.5, 10.5, 10.5), "redsprout", glow=255)],
         box=(0.25, 0, 0.25, 0.75, 0.6, 0.75), oriented=False, collide=False, material="Plant", sounds=CLOTH, light=[0, 7, 6],
         comment="A bright red sprout on the bottom of a pool in the Sanguine Reservoir: all the light there is",
         extra={"drops": drops(("redwater", 0.15, 0))})


def items():
    data = {"code": "epsomsalt", "maxstacksize": 64, "texture": {"base": "item/epsomsalt"},
            "creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 1700,
            "attributes": {"handbook": {"groupBy": ["epsomsalt"]}}}
    data.update(TRANSFORMS)
    ground_storable(data, "Messy12")
    write_json(os.path.join(ASSETS, "itemtypes", "pool", "epsomsalt.json"), data, "Epsom salt, dried out of the Poolrooms' water")
    LANG["item-epsomsalt"] = "Epsom Salt"
    LANG["itemdesc-epsomsalt"] = "Dried out of the Poolrooms' water on the rims of its dark corners. Eases aches and draws out what festers: mixed with linen it makes a salt poultice."
    data = {"code": "redwater", "class": "BackroomsRedWater", "maxstacksize": 4, "texture": {"base": "item/redwater"},
            "creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 1000,
            "nutritionProps": {"satiety": 40, "foodcategory": "NoNutrition"}}
    data.update(TRANSFORMS)
    ground_storable(data)
    write_json(os.path.join(ASSETS, "itemtypes", "pool", "redwater.json"), data, "Red water from the Sanguine Reservoir")
    LANG["item-redwater"] = "Red Water"
    LANG["itemdesc-redwater"] = "Water from where the red sprouts grow, at the bottom of the Sanguine Reservoir. Drink it and every wound closes. Everyone who has drunk it was changed for good."


def recipes():
    # A salt poultice: Epsom salt in place of honey and sulfur, on linen; as good as the best poultice there is
    write_json(os.path.join(ASSETS, "recipes", "grid", "saltpoultice.json"), [{
        "ingredientPattern": "E,L", "width": 1, "height": 2,
        "ingredients": {"E": {"type": "item", "code": "backrooms:epsomsalt", "quantity": 2}, "L": {"type": "block", "code": "game:linen-*"}},
        "output": {"type": "item", "code": "game:poultice-linen-honey-sulfur", "quantity": 3},
    }], "Epsom salt and linen make a salt poultice")


def lang():
    LANG.update({
        "level-12": "Level 37: Sublimity",
        "levelhint-12": "You feel a calming sensation.",
        "level-371": "Level 37.1: The Sanguine Reservoir",
        "levelhint-371": "The water will not let go. Find the light.",
        "levelname-37.1": "Level 37.1",
        "surface37": "You come up into warm, still water, under white tile.",
        "tunnelmouth": "The dark closes round you, and opens onto the sound of the sea.",
        "poolcarpet": "The tile gives way to carpet. The air is cooler, and somewhere a printer is jammed.",
        "pitbottom": "There was a bottom after all. You come up in a backyard pool, under a night sky.",
        "redwater-drunk": "Every wound closes. Something in you is different, and stays that way: your stability will never again be above {0}%.",
    })


def generate():
    textures()
    item_textures()
    blocks()
    items()
    recipes()
    lang()


# ======================= Graphics pass B13 =======================
# Each B13 painter runs after the old one under the same keys (plus new versions beside them), so dropping its call
# from textures() reverts that family's textures; the models are in the *_b13 functions blocks() calls.

import math  # noqa: E402

import matlib as M  # noqa: E402
import modelkit as MK  # noqa: E402
from gen_city import CITY_F5, ptext_c  # noqa: E402

# Each family's mean colour before B13, measured on main's PNGs: the new versions are shifted to it
POOL_MEAN = {"pooltile": (239.6, 239.1, 232.7), "poolsunlit": (246.9, 237.5, 205.6), "poolred": (207.8, 172.9, 172.9),
             "poolcoping": (240.0, 239.8, 233.6), "pooldoor-lower": (53.5, 179.6, 180.4), "pooldoor-upper": (79.1, 191.7, 192.3),
             "epsomcrust": (242.0, 242.3, 242.6)}
POOL_ROW = 17  # (D2) the top pixel row of POOL on the upper leaf
KICK_ROWS = 8  # (D2) the kick plate's height in texture pixels (4 units)
POOL_TILE = {"pooltile": ((244, 244, 238), (226, 224, 216)), "poolsunlit": ((255, 246, 216), (226, 210, 172)),
             "poolred": ((236, 226, 224), (118, 22, 26)), "poolcoping": ((240, 240, 234), (226, 224, 216))}


def mosaic_b13(key, version, film=None):
    """The Poolrooms' mosaic (B13): eight by eight glazed tiles to a 64 px face, as before, in pale grout, but each tile
    a hair different in shade and hue and very slightly tilted (so the light lies differently on each), lit along its
    top and left edge and shaded along its bottom and right, with a small glint up and to the left; the grout is
    recessed, darkest under each tile. A tile in about twelve has a faint crazing of the glaze. Nothing is chipped or
    stained: the lore's tile is pristine. Versions share the grout and the ground (one seed) and differ only in which
    tile takes which shade, so blocks of different versions meet without a step. The coping is the same tile at four
    by four, with a rounded (bullnose) glaze. The Reservoir's red film lies in the grout, heavier along some joints."""
    tile, grout = POOL_TILE[key]
    if not film:  # (round 2) the grout a step darker, so the joint reads; the mean is matched again below
        grout = M.lift(grout, -6)
    size = 64
    coping = key == "poolcoping"
    pitch = 16 if coping else 8
    tw = pitch - 1
    gseed = seed_of("b13" + key)
    rng = random.Random(seed_of(f"b13{key}v{version}"))
    img = M.noise_hv(grout, 1.5, gseed, size, 2.0, (16, 8), hue=0.6)
    ground = M.noise_hv(tile, 1.2, gseed + 1, size, 1.5, (32, 16), hue=0.6)
    p, g = img.load(), ground.load()
    n = size // pitch
    for r in range(n):
        for c in range(n):
            x0, y0 = c * pitch, r * pitch
            v = max(-3.0, min(3.0, rng.gauss(0, 1.3)))
            hu = rng.uniform(-1.2, 1.2)
            ax, ay = rng.uniform(-1.6, 1.6), rng.uniform(-1.6, 1.6)
            for yy in range(tw):
                for xx in range(tw):
                    d = v + (xx / (tw - 1) - 0.5) * ax + (yy / (tw - 1) - 0.5) * ay
                    e = 2 if coping else 1  # the glazed edge: lit top and left, shaded bottom and right
                    if yy < e:
                        d += 5.0 if yy == 0 else 2.5
                    elif xx < e:
                        d += 2.0 if xx == 0 else 1.0
                    if yy >= tw - e:
                        d -= 7.0 if yy == tw - 1 else 3.0
                    elif xx >= tw - e:
                        d -= 3.0 if xx == tw - 1 else 1.5
                    p[x0 + xx, y0 + yy] = M.rgba(M.hue_shift(M.lift(g[x0 + xx, y0 + yy][:3], d), hu))
            # the glint
            if rng.random() < 0.9:
                gx, gy = x0 + 1 + (1 if coping else 0), y0 + 1 + (1 if coping else 0)
                for (dx, dy, k) in ((0, 0, 10), (1, 0, 7), (0, 1, 5), (2, 0, 3)) + (((2, 0, 2), (1, 1, 2)) if coping else ()):
                    p[gx + dx, gy + dy] = M.rgba(M.lift(p[gx + dx, gy + dy][:3], k))
            # the recessed grout: in the tile's shadow under it, a little at its right
            for xx in range(-1, tw + 1):
                q = p[(x0 + xx) % size, y0 + tw]
                p[(x0 + xx) % size, y0 + tw] = M.rgba(M.lift(q[:3], -4.0))
            for yy in range(tw):
                q = p[x0 + tw, y0 + yy]
                p[x0 + tw, y0 + yy] = M.rgba(M.lift(q[:3], -1.2))
            # a faint crazing of the glaze, now and then
            if rng.random() < 0.08:
                cx, cy = x0 + rng.uniform(1.5, tw - 2.5), y0 + rng.uniform(1.5, tw - 2.5)
                a = rng.uniform(0, math.pi)
                for i in range(rng.randint(3, 5)):
                    X, Y = int(cx), int(cy)
                    if x0 < X < x0 + tw - 1 and y0 < Y < y0 + tw - 1:
                        p[X, Y] = M.rgba(M.lift(p[X, Y][:3], -2.2))
                    a += rng.uniform(-0.7, 0.7)
                    cx += math.cos(a)
                    cy += math.sin(a)
    if film:
        # the red film settled in the grout, heavier along some joints
        for r in range(n):
            for c in range(n):
                x0, y0 = c * pitch, r * pitch
                k = rng.uniform(0.55, 1.0)
                for xx in range(pitch):
                    for (X, Y) in (((x0 + xx) % size, y0 + tw), (x0 + tw, (y0 + xx) % size)):
                        if rng.random() < 0.85:
                            p[X, Y] = M.rgba(M.mix(p[X, Y][:3], M.lift(film, rng.uniform(-6, 6)), k))
    return T.match_rgb(img, POOL_MEAN[key], key="b13" + key)


POOL_VERSIONS = {"pooltile": 3, "poolsunlit": 3, "poolred": 3, "poolcoping": 2}


def b13_mosaic():
    for key, n in POOL_VERSIONS.items():
        for v in range(1, n + 1):
            img = mosaic_b13(key, v, film=(128, 18, 24) if key == "poolred" else None)
            save(img, key if v == 1 else f"{key}-{v}")


def b13_chrome():
    """Polished stainless for the rails and ladders (B13): the old bright body and glint along the top, but the glint
    is a soft gradient with a warm reflected band and a cool shadowed foot, and a faint polish streak along it."""
    img = Image.new("RGBA", (S, S))
    px = img.load()
    rng = random.Random(seed_of("b13chrome"))
    prof = []
    for y in range(S):
        t = y / (S - 1)
        v = 252 - 40 * t + 22 * math.exp(-((t - 0.5) / 0.08) ** 2) - 60 * max(0.0, t - 0.78) * 3.2
        prof.append(v)
    for y in range(S):
        for x in range(S):
            v = prof[y] + rng.uniform(-1.5, 1.5) + 2 * math.sin((x + 3 * y) * 0.35)
            px[x, y] = M.rgba((v - 6, v - 2, v + 3))
    save(img, "poolchrome")
    tread = M.brushed_metal(seed_of("b13tread"), base=(176, 180, 184), streak=6, sheen=6)
    M.emboss_lines(tread, ys=(4, 12, 20, 28), raised=True, strength=0.18)
    save(tread, "pooltread")


def b13_door():
    """The POOL door (B13): the leaf is cyan painted steel with an orange-peel coat and a little wear at the foot, and
    POOL in white pixel letters under the porthole (D2; B13 had them over it); the porthole ring, its glass, the push
    plate and kick plate are geometry now (pool_door_b13), so the old painted ones are gone."""
    for part in ("lower", "upper"):
        img = M.painted_metal(seed_of("b13pooldoor"), base=(60, 186, 186), grain=3, mottle=4, panel=False, chips=0,
                              under=(150, 160, 160))
        if part == "lower":
            M.grime(img, 0.08, seed_of("b13pooldoorg"), cells=(8, 4), bias="bottom", cover=0.4)
        else:
            # (D2) POOL at about eye level, under the porthole (rows 17-23: 1.36 m up the door), as the old door had it;
            # B13 put it at the top of the leaf (rows 2-8), which the user read as too high
            ptext_c(img, "POOL", POOL_ROW, (250, 252, 250), CITY_F5)
        save(T.match_rgb(img, POOL_MEAN[f"pooldoor-{part}"], key=f"b13pooldoor-{part}"), f"pooldoor-{part}")
    steel = M.brushed_metal(seed_of("b13poolsteel"), base=(200, 204, 206), streak=7, sheen=8)
    save(steel, "poolsteel")
    # (D2) the kick plate: darker brushed stainless with a lit top edge, a shaded foot and four screws, so it reads as a
    # plate on the leaf; B13's kick plate was poolsteel, in the wall tile's own tone, and read as a gap under the door
    kick = M.brushed_metal(seed_of("d2poolkick"), base=(124, 138, 140), streak=6, sheen=7)
    for x in range(S):
        M.touch(kick, x, 0, 0.22)
        M.touch(kick, x, 1, 0.08)
        M.touch(kick, x, KICK_ROWS - 1, -0.18)
    for x, y in ((2, 3), (29, 3), (2, KICK_ROWS - 3), (29, KICK_ROWS - 3)):
        M.touch(kick, x, y, -0.25)
        M.touch(kick, x + 1, y, 0.1)
    save(kick, "poolkick")
    # the porthole's glass: dark teal water-light behind it, a bright glint across the top left
    img = Image.new("RGBA", (S, S))
    px = img.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            c = M.mix((176, 224, 226), (104, 176, 182), t)
            d = abs((x - y) - (-8)) if x < 18 and y < 18 else 99
            if d < 3 and 4 < x + y < 26:
                c = M.mix(c, (230, 246, 246), 0.7 * (1 - d / 3))
            px[x, y] = M.rgba(c)
    save(img, "poolporthole")


def b13_lost():
    """What is lost at the pool (B13): the towel is terry cloth in its old blue stripes, the noodle foam with its
    hollow, the flip-flops a rubber sole and strap; the Epsom crust is a glittering salt crystal crust."""
    img = M.fabric(seed_of("b13towel"), base=(244, 240, 232), weave="basket", contrast=8, thread=3)
    px = img.load()
    for y in range(S):
        if y % 8 < 4:
            for x in range(S):
                c = px[x, y]
                px[x, y] = M.rgba(M.mix(c[:3], M.lift((62, 142, 200), M.lum(c[:3]) - 238), 0.9))
    save(img, "towel")
    img = M.noise_hv((232, 90, 138), 3, seed_of("b13noodle"), S, 4, (8, 4), hue=1.5)
    rng = random.Random(seed_of("b13noodlec"))
    for _ in range(40):  # the foam's cells
        M.touch(img, rng.randrange(S), rng.randrange(S), rng.choice((-0.08, 0.06)))
    save(img, "noodle")
    save(M.rubber(seed_of("b13flip"), base=(42, 106, 216), grain=3, mottle=5), "flipflop")
    img = M.noise_hv((236, 238, 240), 3, seed_of("b13epsom"), S, 5, (8, 4), hue=1.0)
    rng = random.Random(seed_of("b13epsomc"))
    for _ in range(70):  # crystal faces: a lit facet over a shaded one
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, 0.12)
        M.touch(img, x + 1, y, 0.06)
        M.touch(img, x, y + 1, -0.1)
    save(T.match_rgb(img, POOL_MEAN["epsomcrust"], key="b13epsom"), "epsomcrust")


def b13_textures():
    b13_mosaic()
    b13_chrome()
    b13_door()
    b13_lost()


# ---- Models ----

def octo_bar(name, frm, to, tex, axis):
    """A round-ish bar along `axis` ("x", "y" or "z"): a square bar and the same bar turned 45 degrees about its axis,
    a little thinner, so the section reads as an octagon."""
    a = bx(name, frm, to, tex, full=True)
    (x1, y1, z1), (x2, y2, z2) = frm, to
    c = ((x1 + x2) / 2, (y1 + y2) / 2, (z1 + z2) / 2)
    k = 0.86
    sh = {"x": (1, k, k), "y": (k, 1, k), "z": (k, k, 1)}[axis]
    f2 = tuple(c[i] - (to[i] - frm[i]) / 2 * sh[i] for i in range(3))
    t2 = tuple(c[i] + (to[i] - frm[i]) / 2 * sh[i] for i in range(3))
    rot = {"x": (45, 0, 0), "y": (0, 45, 0), "z": (0, 0, 45)}[axis]
    b = bx(name + "R", f2, t2, tex, full=True, rot=rot, origin=c)
    return [a, b]


def rail_b13(wall):
    """A tile wall with a stainless handrail (B13): a round-ish rail on two brackets, each a short arm from a round
    rose on the wall. The rail runs on from block to block as before."""
    els = [wall] + octo_bar("Rail", (0, 2.9, -1.75), (16, 4.1, -0.55), "poolchrome", "x")
    for i, x in enumerate((3.5, 12.5)):
        els += [bx(f"Rose{i}", (x - 1.0, 1.6, -0.35), (x + 1.0, 3.6, 0), "poolchrome", full=True),
                bx(f"RoseR{i}", (x - 0.85, 1.75, -0.3), (x + 0.85, 3.45, 0), "poolchrome", full=True, rot=(0, 0, 45), origin=(x, 2.6, -0.15)),
                bx(f"Arm{i}", (x - 0.4, 2.45, -1.55), (x + 0.4, 3.0, -0.35), "poolchrome", full=True)]
    return els


def ladder_b13(chrome):
    """A pool ladder (B13): two round stainless rails standing off the wall on brackets, and two treads of ribbed
    stainless with a lit nosing, held in brackets at the rails."""
    els = []
    for i, x in enumerate((3.5, 12.5)):
        els += octo_bar(f"Rail{i}", (x - 0.6, 0, 1.0), (x + 0.6, 16, 2.2), "poolchrome", "y")
        els.append(bx(f"Stay{i}", (x - 0.35, 13, 0), (x + 0.35, 13.7, 1.0), "poolchrome", full=True))
    for k, y in enumerate((3, 10)):
        els += [bx(f"Tread{k}", (4.1, y, 1.0), (11.9, y + 0.75, 4.4), "pooltread"),
                bx(f"Nose{k}", (4.1, y + 0.75, 4.0), (11.9, y + 0.95, 4.4), "poolsteel"),
                bx(f"Clip{k}L", (4.1, y - 0.6, 1.2), (4.6, y, 3.6), "poolsteel"),
                bx(f"Clip{k}R", (11.4, y - 0.6, 1.2), (11.9, y, 3.6), "poolsteel")]
    return els


def pool_door_b13():
    """The POOL door (B13), as a model on the old codes: the leaf is the whole block (so the wall stays closed), and on
    each of its four sides (it has no facing; against the wall the extra sides are buried) a raised frame of stiles,
    the upper half's porthole (a ring of eight stainless segments round its glass) and push plate, the lower half's
    kick plate (D2: darker, down to the floor). Hardware stops 0.05 short of the block's side planes (B8)."""
    paths = {}
    for part in ("lower", "upper"):
        leaf = f"pooldoor-{part}"
        front = [MK.box("StileL", (0.05, 0, -0.4), (1.75, 16 if part == "lower" else 15.5, 0), leaf, faces=MK.without(MK.DIRS, "south")),
                 MK.box("StileR", (14.25, 0, -0.4), (15.95, 16 if part == "lower" else 15.5, 0), leaf, faces=MK.without(MK.DIRS, "south"))]
        if part == "upper":
            # (D2) the porthole higher on the leaf (B13: centre 7.25, radius 3.6), so POOL can sit under it at eye level
            cx, cy, r = 8.0, 11.3, 3.2
            k = r * math.tan(math.radians(22.5))
            # the glass: one square pane under the ring, its corners hidden by the ring's diagonal segments
            g = 2.3
            front.append(MK.box("Glass", (cx - g, cy - g, -0.06), (cx + g, cy + g, 0), "poolporthole", faces=("north",), uv=[0, 0, 16, 16]))
            for i in range(8):
                front.append(MK.box(f"Ring{i}", (cx - k - 0.1, cy + r - 1.1, -0.55), (cx + k + 0.1, cy + r, 0), "poolsteel",
                                    faces=MK.without(MK.DIRS, "south"), rot=(0, 0, 45 * i), origin=(cx, cy, -0.3)))
            front.append(MK.box("Push", (11.0, 0.5, -0.3), (13.5, 3.0, 0), "poolsteel", faces=MK.without(MK.DIRS, "south")))
        else:
            # (D2) the kick plate down to the floor, darker steel, and no mid rail over it: B13's plate in the tile's tone
            # from 0.6 up under a rail read as the leaf standing raised off the floor
            front.append(MK.box("Kick", (1.75, 0, -0.25), (14.25, KICK_ROWS / 2, 0), "poolkick",
                                faces=MK.without(MK.DIRS, "south", "down"), uv=[0, 0, 16, KICK_ROWS / 2]))
        els = [bx("Leaf", (0, 0, 0), (16, 16, 16), leaf, full=True)]
        for t in range(4):
            for e in MK.turn(front, t):
                e = dict(e, name=f"{e['name']}{t}")
                els.append(e)
        paths[part] = shape(f"pooldoor-{part}", els)
    return paths


def pool_door_block_b13():
    paths = pool_door_b13()
    data = {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{p}": {"base": paths[p]} for p in ("lower", "upper")},
        "sideopaque": {"all": True}, "sidesolid": {"all": True},
        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL,
        "behaviors": threshold("pooldoor"),
    }
    block("pooldoor", data, "A cyan door marked POOL: between the Poolrooms and the Terror Hotel")
    name("pooldoor-*", "POOL Door")


def epsom_b13():
    """An Epsom salt crust (B13): a thin irregular crust in three overlapping sheets, with crystal lumps."""
    return [bx("Crust", (2, 0, 3.5), (13.5, 0.6, 12.5), "epsomcrust"), bx("Crust2", (3.5, 0, 2.5), (11, 0.8, 13.5), "epsomcrust"),
            bx("Crust3", (5, 0.6, 4.5), (12, 1.1, 10.5), "epsomcrust"),
            bx("Lump1", (4, 0.8, 5), (6.5, 2.2, 7.5), "epsomcrust", rot=(0, 20, 0)), bx("Lump2", (9, 0.8, 8), (11.5, 1.8, 10.5), "epsomcrust", rot=(0, -15, 0)),
            bx("Lump3", (7, 1.1, 5.5), (8.5, 2.0, 7), "epsomcrust", rot=(0, 40, 0))]


def lost_b13():
    """What is lost (B13): a towel folded in three with its hem showing, flip-flops of sole and V strap, a pool noodle
    as a round foam tube with its hollow at the ends."""
    noodle = octo_bar("Noodle", (1, 0, 6.3), (15, 3.4, 9.7), "noodle", "x")
    noodle += [bx("Hole1", (0.95, 1.2, 7.5), (1.0, 2.2, 8.5), "rubber", faces=("west",)), bx("Hole2", (15.0, 1.2, 7.5), (15.05, 2.2, 8.5), "rubber", faces=("east",))]
    flip = []
    for i, (x, z, rot) in enumerate(((3, 4, 8), (9, 3, -10))):
        flip += [bx(f"Sole{i}", (x, 0, z), (x + 4, 0.8, z + 9), "flipflop", rot=(0, rot, 0), origin=(x + 2, 0, z + 4.5)),
                 bx(f"StrapA{i}", (x + 0.5, 0.8, z + 2.5), (x + 2.2, 1.6, z + 3.2), "flipflop", rot=(0, rot - 30, 0), origin=(x + 2, 0, z + 2)),
                 bx(f"StrapB{i}", (x + 1.8, 0.8, z + 2.5), (x + 3.5, 1.6, z + 3.2), "flipflop", rot=(0, rot + 30, 0), origin=(x + 2, 0, z + 2)),
                 bx(f"Post{i}", (x + 1.7, 0.8, z + 1.4), (x + 2.3, 1.5, z + 2.0), "flipflop")]
    towel = [bx("Fold1", (2, 0, 4), (14, 0.6, 12), "towel"), bx("Fold2", (2.2, 0.6, 4.2), (13.8, 1.2, 11.8), "towel"),
             bx("Fold3", (2.4, 1.2, 4.4), (13.6, 1.8, 11.6), "towel")]
    return {"towel": towel, "flipflop": flip, "noodle": noodle}
