"""Level 37, the Poolrooms: its tile, slits, rails, ladders, door, and what is lost there. Called from gen_detail.py,
which writes them out along with everything else (python tools/gen_detail.py).

Everything in the Poolrooms is the same white ceramic tile, small square tiles with thin grout, glazed and
undamaged. The slits in the walls glow warm white (they are where the light comes from); the arches round a
rotunda glow whiter. In the Sanguine Reservoir a red film lies in the grout.
"""
import os
import random

from PIL import Image, ImageDraw

from detail_kit import ASSETS, CLOTH, LANG, METAL, SIDES, STONE, ROTATE, block, bx, cube, name, prop, shape, write_json
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
    cube_block("pooltile", {"plain": "Pool Tile", "sunlit": "Sunlit Pool Tile", "red": "Pool Tile (Red Film)", "void": "Darkness", "coping": "Pool Coping"},
               ["plain", "sunlit", "red", "void", "coping"],
               {"plain": "pooltile", "sunlit": "poolsunlit", "red": "poolred", "void": "poolvoid", "coping": "poolcoping"},
               comment="Level 37: white ceramic tile, every surface; lit warm where light falls through a slit; red-filmed in the Reservoir; the black of a tunnel mouth",
               lightHsvByType={"*-sunlit": [8, 2, 5]}, lightAbsorptionByType={"*-sunlit": 0, "*": 99})

    # Tile walls carrying a slit of light, a glowing arch, or a handrail on one face (modelled facing north). The
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

    parts = {
        "slit": slit,
        "arch": [wall,
                 bx("Arch", (3, 0, -0.02), (13, 12, 0.2), "archglow", glow=255, faces=("north",)),
                 bx("ArchTop", (4.5, 12, -0.02), (11.5, 14, 0.2), "archglow", glow=255, faces=("north",)),
                 bx("ArchCrown", (6.5, 14, -0.02), (9.5, 15, 0.2), "archglow", glow=255, faces=("north",))],
        "rail": [wall,
                 chrome("Rail", (0, 3, -1.6), (16, 4, -0.6)),
                 chrome("Bracket1", (2.5, 2, -1.2), (4.5, 3.5, 0)), chrome("Bracket2", (11.5, 2, -1.2), (13.5, 3.5, 0)),
                 chrome("Rose1", (2, 1.5, -0.4), (5, 4, 0)), chrome("Rose2", (11, 1.5, -0.4), (14, 4, 0))],
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
        "lightHsvByType": {"*-slit-*": [8, 1, 18], "*-arch-*": [8, 0, 17]},
        "lightAbsorptionByType": {"*-slit-*": 0, "*-arch-*": 0, "*": 99},
    }, "Level 37: tile walls with a slit of glare, a glowing arch, or a handrail, on one face")
    name("poolwall-slit-*", "Slit of Light")
    name("poolwall-arch-*", "Glowing Arch")
    name("poolwall-rail-*", "Pool Tile with Handrail")

    door_block("pooldoor", "POOL Door", "pooldoor", "pooldoor", material="Wood",
               comment="A cyan door marked POOL: between the Poolrooms and the Terror Hotel")

    # A pool ladder: two stainless rails and steps, climbable, at the edge of the water (modelled against the north side)
    prop("poolladder", "Pool Ladder", [
        chrome("RailL", (3, 0, 1), (4, 16, 2), upright=True), chrome("RailR", (12, 0, 1), (13, 16, 2), upright=True),
        bx("Step1", (4, 3, 1.2), (12, 3.6, 4), "steel"), bx("Step2", (4, 10, 1.2), (12, 10.6, 4), "steel")],
         box=(0.18, 0, 0, 0.82, 1, 0.25), material="Metal", sounds=METAL, collide=True,
         extra={"climbable": True, "drops": []})
    prop("epsomcrust", "Epsom Salt Crust", [
        bx("Crust", (2, 0, 3), (14, 0.8, 13), "epsomcrust"), bx("Lump1", (4, 0.8, 5), (7, 2, 8), "epsomcrust"),
        bx("Lump2", (9, 0.8, 8), (12, 1.6, 11), "epsomcrust")],
         box=(0.12, 0, 0.18, 0.88, 0.12, 0.82), oriented=False, collide=False, material="Stone", sounds=STONE,
         comment="A crust of Epsom salt dried on a rim in the dark",
         extra={"drops": drops(("epsomsalt", 1.5, 0.5))})
    prop("lostthing", "Lost Thing", {
        "towel": [bx("Towel", (2, 0, 4), (14, 1.4, 12), "towel")],
        "flipflop": [bx("Left", (3, 0, 4), (7, 0.8, 13), "flipflop"), bx("Right", (9, 0, 3), (13, 0.8, 12), "flipflop"),
                     bx("StrapL", (4.5, 0.8, 6), (5.5, 1.6, 8), "flipflop"), bx("StrapR", (10.5, 0.8, 5), (11.5, 1.6, 7), "flipflop")],
        "noodle": [bx("Noodle", (1, 0, 6.5), (15, 3, 9.5), "noodle")]},
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
    write_json(os.path.join(ASSETS, "itemtypes", "pool", "epsomsalt.json"), data, "Epsom salt, dried out of the Poolrooms' water")
    LANG["item-epsomsalt"] = "Epsom Salt"
    LANG["itemdesc-epsomsalt"] = "Dried out of the Poolrooms' water on the rims of its dark corners. Eases aches and draws out what festers: mixed with linen it makes a salt poultice."
    data = {"code": "redwater", "class": "BackroomsRedWater", "maxstacksize": 4, "texture": {"base": "item/redwater"},
            "creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 1000,
            "nutritionProps": {"satiety": 40, "foodcategory": "NoNutrition"}}
    data.update(TRANSFORMS)
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
