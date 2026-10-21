"""Level 94, Motion: its clay turf, roads, painted backdrop, glass mountain, castle and funhouse, water towers,
fountains, doors, and the props of a 1930s-50s stop-motion picture. Called from gen_detail.py, which writes them out
along with everything else (python tools/gen_detail.py).

Everything outside the castle is a little too saturated and a little grainy, as if it had been made by hand: the
turf is plasticine with thumbprints in it, mown in stripes; the clay under it is real clay. Inside the castle nothing
is animated, and the textures are plain.
"""
import math
import os
import random

from PIL import Image, ImageDraw

from detail_kit import ASSETS, CLOTH, GLASS, LANG, METAL, SIDES, STONE, WOOD, ROTATE, block, bx, cube, cyl, ground_storable, name, prop, shape, write_json
from detail_textures import S, noise, rgb, save, text
from gen_deep import TRANSFORMS, door_block, drops, threshold
from gen_detail import cube_block
from detail_kit import T, seed_of


def grain(img, amount, key, prints=True):
    """The grain of something made by hand: per-pixel noise, and a few thumbprint swirls (unless `prints` is off)."""
    rng = random.Random(seed_of(key))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount)
            px[x, y] = (max(0, min(255, int(r + n))), max(0, min(255, int(g + n))), max(0, min(255, int(b + n))), a)
    if not prints:
        return img
    d = ImageDraw.Draw(img)
    for _ in range(2):
        cx, cy, r0 = rng.randrange(S), rng.randrange(S), rng.randint(4, 7)
        for k in range(3):
            rr = r0 - k * 2
            if rr <= 0:
                break
            box = [cx - rr, cy - rr, cx + rr, cy + rr]
            col = px[min(S - 1, max(0, cx)), min(S - 1, max(0, cy))]
            d.arc(box, rng.randint(0, 90), rng.randint(200, 330), fill=tuple(max(0, c - 14) for c in col[:3]) + (255,))
    return img


def flat(c):
    return Image.new("RGBA", (S, S), tuple(c) + (255,))


def textures():
    # Clay turf, mown in stripes: two greens, too bright, and its side where it meets the clay
    for kind, c in (("light", (98, 186, 64)), ("dark", (70, 150, 48))):
        img = flat(c)
        d = ImageDraw.Draw(img)
        rng = random.Random(seed_of("turf" + kind))
        for _ in range(26):
            x, y = rng.randrange(S), rng.randrange(S)
            d.line([x, y, x + rng.randint(-1, 1), y - rng.randint(1, 3)], fill=tuple(min(255, v + 18) for v in c) + (255,))
        # (No thumbprints on top: seen from above they read as dirt. The sides keep them, and say "clay")
        save(grain(img, 6, "turf" + kind, prints=False), f"clayturf-{kind}")
        # The side is turf too, nearly to the bottom, a shade darker than the top so the terraces still read as steps;
        # only a broken, dull line of clay shows at its foot (a thick band would stripe every contour of a hill)
        shade = tuple(int(v * 0.87) for v in c)
        side = flat(shade)
        d = ImageDraw.Draw(side)
        for _ in range(18):
            x, y = rng.randrange(S), rng.randrange(S - 4)
            d.line([x, y, x, y + rng.randint(1, 3)], fill=tuple(min(255, v + 12) for v in shade) + (255,))
        fringe = tuple(int(0.5 * u + 0.5 * v) for u, v in zip(shade, (128, 104, 80)))
        for x in range(S):
            if rng.random() < 0.55:
                d.point([x, S - 1], fill=fringe + (255,))
        save(grain(side, 7, "turfside" + kind), f"clayturf-side-{kind}")
    save(grain(flat((168, 104, 64)), 8, "claysoil"), "claysoil")
    save(grain(flat((182, 150, 104)), 7, "motionpath"), "motionpath")
    save(grain(flat((208, 204, 194)), 5, "motionconcrete"), "motionconcrete")
    save(grain(flat((86, 86, 92)), 6, "motionasphalt"), "motionasphalt")
    img = flat((222, 220, 212))
    ImageDraw.Draw(img).line([0, 15, S, 15], fill=(180, 178, 170, 255))
    save(grain(img, 4, "motionkerb"), "motionkerb")

    # The painted backdrop: hills along the bottom, a sky with a cloud or two above, brush strokes showing
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        d.line([0, y, S, y], fill=(126, 182, 228, 255))
    for k, (cx, r, c) in enumerate(((6, 14, (110, 176, 82)), (24, 18, (88, 156, 66)))):
        d.ellipse([cx - r, S - r // 1.4, cx + r, S + r * 1.4], fill=c + (255,))
    save(grain(img, 5, "backdrophills"), "backdrop-hills")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        d.line([0, y, S, y], fill=(int(96 + 40 * t), int(156 + 30 * t), int(220 + 10 * t), 255))
    d.ellipse([4, 8, 18, 15], fill=(246, 248, 250, 255))
    d.ellipse([12, 6, 26, 14], fill=(250, 250, 252, 255))
    save(grain(img, 4, "backdropsky"), "backdrop-sky")

    # The glass of the mountain: almost clear, catching the sky
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        d.line([0, y, S, y], fill=(int(214 - 40 * t), int(234 - 30 * t), 248, 150))
    d.line([3, S - 6, S - 6, 3], fill=(255, 255, 255, 215), width=2)
    d.line([12, S - 3, S - 3, 12], fill=(255, 255, 255, 170), width=1)
    d.rectangle([0, 0, S - 1, S - 1], outline=(236, 246, 252, 200))
    save(img, "glassmountain")

    # The castle: white stone, red roofs; the funhouse: pink and yellow stripes with porthole rings
    img = flat((240, 238, 232))
    d = ImageDraw.Draw(img)
    for y in (0, 8, 16, 24):
        d.line([0, y, S, y], fill=(214, 210, 202, 255))
        off = 8 if y % 16 else 0
        for x in range(off, S, 16):
            d.line([x, y, x, y + 7], fill=(214, 210, 202, 255))
    save(grain(img, 3, "castlewall"), "castlewall")
    img = flat((196, 44, 40))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 4):
        d.line([0, y, S, y], fill=(160, 30, 30, 255))
    save(grain(img, 4, "castleroof"), "castleroof")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.rectangle([x, 0, x + 3, S], fill=(244, 150, 196, 255))
        d.rectangle([x + 4, 0, x + 7, S], fill=(250, 222, 96, 255))
    d.ellipse([9, 9, 22, 22], outline=(120, 90, 160, 255), width=2)
    d.ellipse([12, 12, 19, 19], fill=(150, 200, 230, 255))
    save(img, "funwall")
    save(flat((246, 244, 236)), "castleceiling")
    save(grain(flat((252, 252, 250)), 2, "castlewhite"), "castlewhite")
    img = flat((255, 236, 190))
    ImageDraw.Draw(img).rectangle([3, 3, S - 4, S - 4], outline=(230, 200, 140, 255))
    save(img, "funlight-warm")
    save(flat((255, 255, 255)), "funlight-blinding")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(0, S, 8):
        for x in range(0, S, 8):
            d.rectangle([x, y, x + 7, y + 7], fill=(60, 96, 200, 255) if (x + y) // 8 % 2 == 0 else (250, 210, 60, 255))
    save(img, "funfloor-checker")
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 8):
        d.rectangle([x, 0, x + 3, S], fill=(206, 40, 44, 255))
        d.rectangle([x + 4, 0, x + 7, S], fill=(246, 240, 236, 255))
    save(img, "funfloor-carpet")
    img = flat((40, 44, 110))
    d = ImageDraw.Draw(img)
    pts = [(16 + 13 * math.cos(math.pi / 2 + k * math.pi * 2 / 10) * (1 if k % 2 == 0 else 0.45),
            16 - 13 * math.sin(math.pi / 2 + k * math.pi * 2 / 10) * (1 if k % 2 == 0 else 0.45)) for k in range(10)]
    d.polygon(pts, fill=(250, 214, 70, 255))
    save(img, "funfloor-star")

    # The water tower, white and steel; the fountain's stone
    save(grain(flat((236, 236, 232)), 3, "towertank"), "towertank")
    save(grain(flat((150, 154, 160)), 4, "towersteel"), "towersteel")
    save(grain(flat((206, 196, 170)), 5, "fountainstone"), "fountainstone")

    # Doors: a doll's house's cream door, a flooded house's (the same, water at the keyhole), the throne room's
    for part in ("lower", "upper"):
        for kind, base, trim in (("dolldoor", 0xF0E2C0, 0xC8A878), ("flooddoor", 0xF0E2C0, 0x7AA8C0), ("thronedoor", 0x7A2A2A, 0xD8B040)):
            img = grain(noise(base, 3, kind + part), 3, kind + part)
            d = ImageDraw.Draw(img)
            d.rectangle([0, 0, S - 1, S - 1], outline=rgb(trim), width=2)
            d.rectangle([5, 4 if part == "upper" else 2, S - 6, S - 5], outline=rgb(trim), width=1)
            if part == "lower":
                d.ellipse([23, 1, 26, 4], fill=rgb(0xD8B040))
                if kind == "flooddoor":
                    d.rectangle([2, 2, S - 3, S - 3], outline=(110, 170, 200, 255))
            elif kind == "thronedoor":
                d.polygon([(10, 12), (13, 6), (16, 11), (19, 6), (22, 12)], fill=rgb(0xD8B040))
            save(img, f"{kind}-{part}")

    # Signs and the cars
    img = flat((248, 210, 30))
    text(img, "NO", (2, 4, S - 2, 14), 0x101010, 9)
    text(img, "OUTLET", (1, 16, S - 1, 27), 0x101010, 6)
    ImageDraw.Draw(img).rectangle([0, 0, S - 1, S - 1], outline=(16, 16, 16, 255))
    save(img, "nooutlet")
    for kind, c in (("milkvan", (244, 242, 236)), ("oldcar-black", (32, 32, 36)), ("oldcar-green", (54, 92, 64)), ("oldcar-maroon", (110, 34, 40))):
        save(grain(flat(c), 4, kind), kind)
    img = grain(flat((244, 242, 236)), 3, "milkside")
    text(img, "ALMOND", (2, 6, S - 2, 15), 0x2A6AB0, 6)
    text(img, "MILK", (4, 16, S - 4, 25), 0x2A6AB0, 7)
    save(img, "milkvan-side")

    # The castle's things: coloured balls, an arcade screen, the model town, sketches, the King's stone
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("balls"))
    for y in range(0, S, 4):
        for x in range(0, S, 4):
            c = rng.choice([(230, 50, 50), (50, 120, 230), (250, 210, 40), (60, 190, 90), (240, 130, 200)])
            d.ellipse([x, y, x + 3, y + 3], fill=c + (255,))
    save(img, "ballpit")
    img = flat((24, 24, 40))
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, S - 5, 20], fill=(10, 14, 20, 255))
    d.rectangle([6, 23, 10, 27], fill=(230, 50, 50, 255))
    d.rectangle([14, 23, 18, 27], fill=(250, 210, 40, 255))
    save(img, "arcade-front")
    img = flat((98, 186, 64))
    d = ImageDraw.Draw(img)
    rng = random.Random(seed_of("diorama"))
    d.line([0, 16, S, 14], fill=(90, 90, 96, 255), width=2)
    for _ in range(7):
        x, y = rng.randrange(2, S - 6), rng.randrange(2, S - 6)
        d.rectangle([x, y, x + 3, y + 3], fill=(240, 230, 200, 255))
        d.rectangle([x, y, x + 3, y], fill=(190, 60, 50, 255))
    save(img, "diorama-top")
    img = flat((244, 240, 228))
    d = ImageDraw.Draw(img)
    d.ellipse([8, 6, 22, 20], outline=(60, 60, 60, 255))
    d.line([15, 20, 15, 28], fill=(60, 60, 60, 255))
    d.line([10, 24, 20, 24], fill=(60, 60, 60, 255))
    d.line([11, 11, 13, 11], fill=(60, 60, 60, 255))
    d.line([17, 11, 19, 11], fill=(60, 60, 60, 255))
    d.arc([11, 12, 19, 18], 20, 160, fill=(60, 60, 60, 255))
    save(img, "sketch")
    save(grain(flat((132, 128, 122)), 10, "kingstone"), "kingstone")
    save(grain(flat((248, 246, 240)), 3, "picket"), "picket")

    # The picture on a city cinema's screen: round green hills, a cream house on one, a white water tower, blue sky
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        d.line([0, y, S, y], fill=(int(120 + y), int(170 + y), 230, 255))
    d.ellipse([-10, 14, 18, 44], fill=(84, 168, 60, 255))
    d.ellipse([12, 18, 44, 48], fill=(70, 150, 50, 255))
    d.rectangle([5, 11, 11, 17], fill=(240, 228, 196, 255))
    d.polygon([(4, 11), (8, 7), (12, 11)], fill=(170, 60, 50, 255))
    d.rectangle([25, 10, 26, 18], fill=(220, 220, 220, 255))
    d.ellipse([22, 6, 29, 11], fill=(240, 240, 240, 255))
    save(grain(img, 6, "cinemascreen"), "cinemascreen")
    b13_textures()


def blocks():
    # The ground. (B13) The turf's top in three versions turned at random, its sides in three and a faint thumbprint one
    # block in eight, the clay in three turned; picked by height as well as place (randomizeAxes xyz)
    turns = (0, 90, 180, 270)
    clay = tex_entry("claysoil", alts("claysoil", 3), turns)
    for kind in ("light", "dark"):
        block(f"clayturf-{kind}", {
            "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
            "textures": {"up": tex_entry(f"clayturf-{kind}", alts(f"clayturf-{kind}", 3), turns), "down": clay,
                         "horizontals": tex_entry(f"clayturf-side-{kind}", alts(f"clayturf-side-{kind}", 0, [""] + TURF_SIDE_MIX))},
            "randomizeAxes": "xyz",
            "lightAbsorption": 99, "resistance": 1.5,
            # Fertile enough for the grass and flowers on it, and (like soil) keeps the shrubs' leaves from decaying
            "fertility": 50, "attributes": {"preventsDecay": True},
            "sounds": {"walk": "game:walk/grass", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"},
            "drops": [{"type": "block", "code": "game:soil-low-none", "quantity": {"avg": 1}}],
        }, "Level 94: clay turf, mown in stripes. Dug up, it gives a poor sort of soil")
        name(f"clayturf-{kind}", "Clay Turf")
    block("claysoil", {
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
        "textures": {"all": clay}, "randomizeAxes": "xyz", "lightAbsorption": 99, "resistance": 1.5,
        "fertility": 10, "attributes": {"preventsDecay": True},
        "sounds": {"walk": "game:walk/sludge*", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"},
        "drops": [{"type": "item", "code": "game:clay-red", "quantity": {"avg": 3, "var": 1}}],
    }, "Level 94: the modelling clay everything is made of. Dug up, it is clay for the potter's wheel")
    name("claysoil", "Modelling Clay")
    import gen_detail as gd
    gd.TURNED.update({"motionpath", "motionconcrete", "motionasphalt", "motionkerb"})
    gd.ALTS.update({k: alts(k, 3)[1:] for k in ("motionpath", "motionconcrete", "motionkerb", "castlewall", "castleroof")})
    gd.ALTS["motionasphalt"] = ["motionasphalt-2"] * 3 + ["motionasphalt"] * 2 + ["motionasphalt-3"]
    cube_block("motionground", {"path": "Dirt Path", "concrete": "Concrete Path", "asphalt": "Asphalt", "kerb": "Kerb"},
               ["path", "concrete", "asphalt", "kerb"],
               {"path": "motionpath", "concrete": "motionconcrete", "asphalt": "motionasphalt", "kerb": "motionkerb"},
               comment="Level 94: paths, roads and kerbs")
    cube_block("backdrop", {"hills": "Painted Backdrop", "sky": "Painted Backdrop"}, ["hills", "sky"],
               {"hills": "backdrop-hills", "sky": "backdrop-sky"}, material="Wood", sounds=WOOD,
               comment="Level 94: the painted backdrop at the edge of the set")
    block("glassmountain", {
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Glass", "drawtype": "cube",
        "renderpass": "Transparent", "faceCullMode": "MergeMaterial", "sideopaque": {"all": False},
        "textures": {"all": tex_entry("glassmountain", alts("glassmountain", 4))}, "randomizeAxes": "xyz",
        "lightAbsorption": 0, "resistance": 4, "sounds": GLASS,
    }, "Level 94: the glass of the transparent mountain")
    name("glassmountain", "Mountain Glass")
    cube_block("castleblock", {"wall": "Castle Stone", "roof": "Castle Roof", "funwall": "Funhouse Wall", "ceiling": "Castle Ceiling", "white": "White Wall"},
               ["wall", "roof", "funwall", "ceiling", "white"],
               {"wall": "castlewall", "roof": "castleroof", "funwall": "funwall", "ceiling": "castleceiling", "white": "castlewhite"},
               comment="Level 94: the castle on the mountain",
               # Its white walls and red roofs glow a little, so at dusk the castle still stands out on its mountain, lit
               # like a set under the studio lights, when the hills round it have gone dark (a glow, not a light: no
               # light is spread, so the castle costs nothing to light)
               vertexFlagsByType={"*-wall": {"glowLevel": 72}, "*-roof": {"glowLevel": 56}}, randomizeAxes="xyz")
    cube_block("funfloor", {"checker": "Checkerboard Floor", "carpet": "Striped Carpet", "star": "Star Floor"}, ["checker", "carpet", "star"],
               {"checker": "funfloor-checker", "carpet": "funfloor-carpet", "star": "funfloor-star"}, comment="Level 94: the funhouse's floors")
    block("funlight", {
        "variantgroups": [{"code": "kind", "states": ["warm", "blinding"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Glass", "drawtype": "cube",
        "texturesByType": {"*-warm": {"all": {"base": "block/detail/funlight-warm"}}, "*-blinding": {"all": {"base": "block/detail/funlight-blinding"}}},
        "lightHsvByType": {"*-warm": [7, 3, 16], "*-blinding": [0, 0, 22]}, "lightAbsorption": 0, "resistance": 2, "sounds": GLASS,
    }, "Level 94: the funhouse's lights, warm, and in the blinding halls blinding")
    name("funlight-*", "Funhouse Light")

    # The water tower: legs, tank, roof, and the tap at the foot that runs with Almond Water
    block("watertower", {
        "variantgroups": [{"code": "part", "states": ["leg", "tank", "roof", "tap"]}],
        "creativeinventory": {"general": ["*"]}, "blockmaterial": "Metal",
        "drawtypeByType": {"*-leg": "json", "*-tap": "json", "*": "cube"},
        "shapeByType": {"*-leg": {"base": shape("watertower-leg", towerleg_b13())},
                        "*-tap": {"base": shape("watertower-tap", [bx("Pipe", (6.5, 0, 6.5), (9.5, 14, 9.5), "towersteel"),
                                                                   bx("Spout", (7, 9, 2), (9, 11, 6.5), "brass"),
                                                                   bx("Wheel", (6, 12, 6), (10, 12.6, 10), "redmetal")])}},
        "texturesByType": {"*-tank": {"all": tex_entry("towertank", alts("towertank", 3))}, "*-roof": {"all": {"base": "block/detail/towersteel"}}},
        "randomizeAxes": "xyz",
        "sideopaqueByType": {"*-leg": {"all": False}, "*-tap": {"all": False}, "*": {"all": True}},
        "lightAbsorptionByType": {"*-leg": 0, "*-tap": 0, "*": 99},
        "collisionboxByType": {"*-leg": {"x1": 0.37, "y1": 0, "z1": 0.37, "x2": 0.63, "y2": 1, "z2": 0.63},
                               "*-tap": {"x1": 0.4, "y1": 0, "z1": 0.4, "x2": 0.6, "y2": 0.9, "z2": 0.6}},
        "selectionboxByType": {"*-leg": {"x1": 0.37, "y1": 0, "z1": 0.37, "x2": 0.63, "y2": 1, "z2": 0.63},
                               "*-tap": {"x1": 0.35, "y1": 0, "z1": 0.1, "x2": 0.65, "y2": 0.9, "z2": 0.65}},
        "classByType": {"*-tap": "BackroomsDispenser"}, "entityClassByType": {"*-tap": "BackroomsDispenser"},
        "attributesByType": {"*-tap": {"dispenses": ["backrooms:almondwater"], "restock": True}},
        "resistance": 4, "drops": [], "sounds": METAL,
    }, "Level 94: a white water tower on a hilltop, full of Almond Water")
    for part, eng in (("leg", "Water Tower Leg"), ("tank", "Water Tower Tank"), ("roof", "Water Tower Roof"), ("tap", "Water Tower Tap")):
        name(f"watertower-{part}", eng)
    # (D3) The tower of the pictures, placed by the world generator where this one's legs, tank and roof went
    tower_d3_blocks()

    # The town fountain: a stone rim, and a spout of Almond Water in the middle
    block("almondfountain", {
        "variantgroups": [{"code": "part", "states": ["rim", "spout"]}],
        "creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {"*-rim": {"base": shape("almondfountain-rim", fountain_b13()[0])},
                        "*-spout": {"base": shape("almondfountain-spout", fountain_b13()[1])}},
        "sideopaque": {"all": False}, "lightAbsorption": 0,
        "collisionboxByType": {"*-rim": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.45, "z2": 1}},
        "classByType": {"*-spout": "BackroomsDispenser"}, "entityClassByType": {"*-spout": "BackroomsDispenser"},
        "attributesByType": {"*-spout": {"dispenses": ["backrooms:almondwater"], "restock": True}},
        "resistance": 4, "drops": [], "sounds": STONE,
        "particlePropertiesByType": {"*-spout": [{
            "hsvaColor": [{"avg": 32, "var": 4}, {"avg": 40, "var": 15}, {"avg": 225, "var": 20}, {"avg": 200, "var": 30}],
            "gravityEffect": {"avg": 0.8, "var": 0}, "posOffset": [{"avg": 0, "var": 0.15}, {"avg": 0.6, "var": 0.1}, {"avg": 0, "var": 0.15}],
            "velocity": [{"avg": 0, "var": 0.3}, {"avg": 0.4, "var": 0.1}, {"avg": 0, "var": 0.3}], "quantity": {"avg": 2},
            "size": {"avg": 0.15, "var": 0.05}, "particleModel": "Cube", "lifeLength": {"avg": 0.8, "var": 0.2}}]},
    }, "Level 94: the town fountain, running with Almond Water")
    name("almondfountain-rim", "Fountain Rim")
    name("almondfountain-spout", "Almond Water Fountain")

    # White picket fences: a post, and pickets out to each side it joins (connections N1 E2 S4 W8)
    for mask in range(16):
        els = [bx("Post", (6.5, 0, 6.5), (9.5, 15, 9.5), "picket"), bx("PostCap", (7, 15, 7), (9, 16, 9), "picket")]
        for bit, (x1, z1, x2, z2, along_x) in ((1, (7.25, 0, 8.75, 6.5, False)), (2, (9.5, 7.25, 16, 8.75, True)),
                                               (4, (7.25, 9.5, 8.75, 16, False)), (8, (0, 7.25, 6.5, 8.75, True))):
            if not mask & bit:
                continue
            els.append(bx(f"RailLow{bit}", (x1, 4, z1), (x2, 5, z2), "picket"))
            els.append(bx(f"RailHigh{bit}", (x1, 10, z1), (x2, 11, z2), "picket"))
            # Pickets every couple of pixels along the rails, pointed at the top
            length = (x2 - x1) if along_x else (z2 - z1)
            start = x1 if along_x else z1
            k = 0
            while k * 2.5 + 1.5 <= length:
                a = start + k * 2.5 + 0.5
                if along_x:
                    els.append(bx(f"P{bit}{k}", (a, 1, 7.5), (a + 1.5, 13, 8.5), "picket"))
                    els.append(bx(f"T{bit}{k}", (a + 0.25, 13, 7.6), (a + 1.25, 14, 8.4), "picket"))
                else:
                    els.append(bx(f"P{bit}{k}", (7.5, 1, a), (8.5, 13, a + 1.5), "picket"))
                    els.append(bx(f"T{bit}{k}", (7.6, 13, a + 0.25), (8.4, 14, a + 1.25), "picket"))
                k += 1
        shape(f"picketfence-{mask}", els)
    block("picketfence", {
        "variantgroups": [{"code": "joins", "states": [str(m) for m in range(16)]}],
        "creativeinventory": {"general": ["*-15"], "decorative": ["*-15"]},
        "blockmaterial": "Wood", "drawtype": "json",
        "shapeByType": {f"*-{m}": {"base": f"block/detail/picketfence-{m}"} for m in range(16)},
        "sideopaque": {"all": False}, "lightAbsorption": 0, "resistance": 2, "sounds": WOOD,
        "collisionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 1.5, "z2": 1},
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.95, "z2": 1},
        "drops": [{"type": "item", "code": "game:stick", "quantity": {"avg": 2}}],
    }, "Level 94: a white picket fence")
    name("picketfence-*", "Picket Fence")

    # A city cinema's screen: the back wall of the hall, the picture on its inner face (modelled facing north)
    path = shape("cinemascreen", [cube("plaster-interior"), bx("Picture", (0, 0, -0.02), (16, 16, 0), "cinemascreen", glow=200, faces=("north",), full=True)])
    block("cinemascreen", {
        "variantgroups": [{"code": "side", "states": SIDES}],
        "creativeinventory": {"general": ["*-north"], "decorative": ["*-north"]},
        "blockmaterial": "Stone", "drawtype": "json", "shapeByType": {f"*-{s_}": {"base": path, "rotateY": ROTATE[s_]} for s_ in SIDES},
        "lightHsv": [32, 2, 8], "lightAbsorption": 0, "resistance": 4, "sounds": STONE,
    }, "A city cinema's screen, showing a stop-motion picture of round green hills. Walk into it and you are in Level 94")
    name("cinemascreen-*", "Cinema Screen")

    door_block("dolldoor", "Front Door", "dolldoor", "dollhouse", material="Wood", sounds=WOOD,
               comment="A cream front door between Level 94 and the Suburbs")
    door_block("flooddoor", "Front Door", "flooddoor", "floodedhouse", material="Wood", sounds=WOOD,
               comment="The front door of a house full of water to its ceiling. Open it and the water takes you, into Level 7")
    door_block("thronedoor", "Door", "thronedoor", "thronedoor", material="Wood", sounds=WOOD,
               comment="One of the throne room's doors: only one opens, a different one each day")


def props():
    # The town: siren poles, milk vans, old cars, signs
    prop("sirenpole", "Siren Pole", sirenpole_d4() if D4_SIREN else sirenpole_b13(),
         box=(0.4, 0, 0.4, 0.6, 2, 0.6), oriented=False, material="Wood", sounds=WOOD,
         comment="A siren pole on a corner of the town, playing the same happy tune all day")
    van = [bx("Body", (1, 2.5, 8), (31, 24, 63), "milkvan", faces=("north", "up", "down", "south")),
           bx("Sides", (1, 2.5, 8), (31, 24, 63), "milkvan-side", faces=("east", "west"), full=True),
           bx("Cab", (2, 2.5, 0), (30, 18, 9), "milkvan"), bx("Windscreen", (3, 11, -0.2), (29, 17, 0), "lampglass", faces=("north",)),
           bx("Bumper", (1, 3, -0.6), (31, 6, 0), "chrome"),
           bx("WheelFL", (0, 0, 2), (3, 8, 10), "rubber"), bx("WheelFR", (29, 0, 2), (32, 8, 10), "rubber"),
           bx("WheelRL", (0, 0, 48), (3, 8, 56), "rubber"), bx("WheelRR", (29, 0, 48), (32, 8, 56), "rubber"),
           bx("LampL", (3, 8, -0.4), (7, 11, 0), "lampglass"), bx("LampR", (25, 8, -0.4), (29, 11, 0), "lampglass")]
    van = milkvan_b13()
    prop("milkvan", "Milk Van", van, box=(0, 0, 0, 1, 1.5, 1), material="Metal", sounds=METAL,
         comment="A 1930s milk van, its crates still full of Almond Milk",
         extra={"class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
                "attributes": {"dispenses": ["backrooms:almondmilk"], "restock": True}, "drops": []})

    def car(body):
        return [bx("Body", (1, 3, 4), (31, 12, 60), body), bx("Hood", (6, 12, 4), (26, 15, 22), body),
                bx("Cabin", (3, 12, 26), (29, 24, 50), body, faces=("up", "east", "west", "south")),
                bx("Windscreen", (4, 15, 25.8), (28, 23, 26), "lampglass", faces=("north",)),
                bx("FenderFL", (-1, 3, 6), (5, 9, 18), body), bx("FenderFR", (27, 3, 6), (33, 9, 18), body),
                bx("FenderRL", (-1, 3, 44), (5, 9, 56), body), bx("FenderRR", (27, 3, 44), (33, 9, 56), body),
                bx("Grille", (9, 4, 3.6), (23, 13, 4), "chrome"), bx("BumperF", (1, 3, 2.6), (31, 5, 3.6), "chrome"),
                bx("BumperR", (1, 3, 60), (31, 5, 61), "chrome"),
                bx("WheelFL", (0, 0, 8), (4, 8, 16), "rubber"), bx("WheelFR", (28, 0, 8), (32, 8, 16), "rubber"),
                bx("WheelRL", (0, 0, 46), (4, 8, 54), "rubber"), bx("WheelRR", (28, 0, 46), (32, 8, 54), "rubber"),
                bx("LampL", (2, 10, 3), (6, 14, 7), "lampglass"), bx("LampR", (26, 10, 3), (30, 14, 7), "lampglass")]
    prop("oldcar", "Old Car", {c: oldcar_wheels_b13(car(f"oldcar-{c}")) for c in ("black", "green", "maroon")}, box=(0, 0, 0, 1, 1.5, 1),
         material="Metal", sounds=METAL, comment="A 1930s car, parked in the middle of nowhere",
         extra={"drops": drops(("metalbracket", 2, 1), ("scrapwire", 1, 0.5), ("glassshard", 1, 0.5))})
    prop("nooutletsign", "NO OUTLET Sign", [
        bx("Pole", (7.5, 0, 7.5), (8.5, 26, 8.5), "metal"),
        bx("Sign", (2, 24, 7), (14, 34, 7.6), "nooutlet", faces=("north",), full=True),
        bx("Back", (2, 24, 7.6), (14, 34, 8), "metal", faces=("south", "east", "west", "up", "down"))],
         box=(0.42, 0, 0.42, 0.58, 2, 0.58), material="Metal", sounds=METAL, comment="A NO OUTLET sign at a road that goes on forever")

    # Inside the houses: the 1950s
    prop("icebox", "Icebox", icebox_b13(),
         box=(0.12, 0, 0.25, 0.88, 1.62, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:cheese-cheddar-1slice", 0.8, 0.6), ("game:butter-salted", 0.5, 0.4),
                               ("almondmilk", 0.6, 0.4), ("cannedbeans", 0.4, 0.3), ("metalbracket", 1, 0.5))})
    prop("radiocabinet", "Radio Cabinet", radio_b13(),
         box=(0.06, 0, 0.31, 0.94, 0.94, 0.88), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:plank-aged", 2, 1), ("scrapwire", 1.5, 0.5), ("glassshard", 0.5, 0.5))})
    prop("rotaryphone", "Telephone Table", phone_b13(),
         box=(0.18, 0, 0.18, 0.82, 0.97, 0.82), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:plank-aged", 1, 0), ("scrapwire", 1, 0.5))})

    # Heaps of furniture with no house
    pile = {
        "chairs": [bx("C1", (1, 0, 2), (7, 9, 8), "wood"), bx("C2", (8, 0, 6), (14, 8, 12), "wooddark", rot=(0, 30, 0)),
                   bx("C3", (3, 8, 4), (10, 15, 10), "wood", rot=(20, 0, 15)), bx("Seat", (4, 15, 3), (12, 16, 12), "fabric1", rot=(0, 0, -25))],
        "tables": [bx("Top", (0, 8, 1), (16, 9.5, 15), "tabletop", rot=(0, 0, 12)), bx("Leg", (2, 0, 3), (3.5, 9, 4.5), "wood"),
                   bx("Leg2", (13, 0, 12), (14.5, 7, 13.5), "wood"), bx("Drawer", (5, 0, 5), (12, 6, 12), "dresserwood")],
        "drawers": [bx("Chest", (2, 0, 3), (14, 12, 13), "dresserwood", rot=(0, 15, 0)), bx("Lamp", (6, 12, 6), (10, 18, 10), "lampshade", rot=(0, 0, 30)),
                    bx("Frame", (9, 0, 0), (16, 10, 2), "gilt", rot=(-15, 0, 0))],
        "mixed": [bx("Sofa", (0, 0, 2), (16, 7, 9), "fabric3"), bx("Back", (0, 7, 2), (16, 13, 4), "fabric3"),
                  bx("Tv", (4, 7, 6), (11, 13, 12), "tvwood", rot=(0, 0, 40)), bx("Box", (10, 0, 10), (16, 5, 16), "cardboard")],
    }
    prop("furniturepile", "Heap of Furniture", pile, box=(0, 0, 0, 1, 1, 1), material="Wood", sounds=WOOD,
         comment="Furniture heaped on a hill, with no house anywhere",
         extra={"drops": drops(("game:plank-aged", 3, 1), ("game:stick", 2, 1), ("game:metalnailsandstrips-iron", 0.5, 0.5),
                               ("game:cloth-plain", 0.4, 0.4))})
    prop("twilightgate", "Rusted Gate", [
        bx("PostL", (0, 0, 7), (2, 20, 9), "rust"), bx("PostR", (14, 0, 7), (16, 20, 9), "rust"),
        bx("Bar1", (2, 3, 7.5), (14, 4, 8.5), "rust"), bx("Bar2", (2, 9, 7.5), (14, 10, 8.5), "rust"), bx("Bar3", (2, 15, 7.5), (14, 16, 8.5), "rust"),
        bx("Brace", (2, 3, 7.6), (14, 4, 8.4), "rust", rot=(0, 0, 40), origin=(8, 9.5, 8))],
         box=(0, 0, 0.4, 1, 1.25, 0.6), collide=False, material="Metal", sounds=METAL,
         comment="A rusted field gate with no sign on it. At twilight it opens onto somewhere else")

    # The castle. The ball pit's balls fill a block sunk into the floor: you wade through them, slowly
    block("ballpitfill", {
        "creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Cloth", "drawtype": "cube",
        "textures": {"all": {"base": "block/detail/ballpit"}}, "sideopaque": {"all": False}, "lightAbsorption": 0,
        "collisionbox": None, "walkspeedmultiplier": 0.5, "resistance": 1, "drops": [], "sounds": CLOTH,
    }, "Level 94: the funhouse's ball pit, full to the brim")
    name("ballpitfill", "Ball Pit")
    prop("ballpit", "Ball Pit", [bx("Balls", (0, 0, 0), (16, 9, 16), "ballpit")], box=(0, 0, 0, 1, 0.56, 1), oriented=False,
         collide=False, material="Cloth", sounds=CLOTH, comment="A pit of coloured balls, waist deep",
         extra={"drops": []})
    prop("arcade", "Arcade Cabinet", [
        bx("Body", (2, 0, 4), (14, 28, 15), "blackmetal", faces=("east", "west", "up", "south")),
        bx("Front", (2, 0, 4), (14, 28, 15), "arcade-front", faces=("north",), full=True),
        bx("Panel", (2, 14, 1), (14, 15, 4), "blackmetal")], box=(0.12, 0, 0.06, 0.88, 1.75, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("scrapwire", 2, 1), ("glassshard", 1, 0.5), ("metalbracket", 1, 0.5))})
    prop("diorama", "Model Town", [
        bx("Table", (-8, 10, -8), (24, 12, 24), "wood", faces=("north", "south", "east", "west", "down")),
        bx("Town", (-8, 10, -8), (24, 12, 24), "diorama-top", faces=("up",), full=True),
        bx("Leg1", (-7, 0, -7), (-5, 10, -5), "wood"), bx("Leg2", (21, 0, -7), (23, 10, -5), "wood"),
        bx("Leg3", (-7, 0, 21), (-5, 10, 23), "wood"), bx("Leg4", (21, 0, 21), (23, 10, 23), "wood"),
        bx("Mountain", (5, 12, 5), (11, 17, 11), "glassmountain"), bx("Castle", (6.5, 17, 6.5), (9.5, 19, 9.5), "white")],
         box=(-0.5, 0, -0.5, 1.5, 0.75, 1.5), oriented=False, material="Wood", sounds=WOOD,
         comment="The animation studio's model of the town, its hills and its mountain, every house in place")
    prop("studiocamera", "Studio Camera", [
        bx("LegA", (7, 0, 2), (8, 18, 3), "wood", rot=(-15, 0, 0), origin=(7.5, 18, 8)), bx("LegB", (2, 0, 12), (3, 18, 13), "wood", rot=(10, 0, 12), origin=(8, 18, 8)),
        bx("LegC", (13, 0, 12), (14, 18, 13), "wood", rot=(10, 0, -12), origin=(8, 18, 8)),
        bx("Body", (4, 18, 4), (12, 26, 14), "blackmetal"), bx("Lens", (6, 20, 0), (10, 24, 4), "chrome"),
        bx("ReelA", (4, 26, 4), (12, 32, 5), "metaldark"), bx("ReelB", (4, 26, 12), (12, 32, 13), "metaldark")],
         box=(0.12, 0, 0.12, 0.88, 2, 0.88), material="Metal", sounds=METAL)
    prop("easel", "Easel of Sketches", [
        bx("LegL", (2, 0, 9), (3, 26, 10), "wood"), bx("LegR", (13, 0, 9), (14, 26, 10), "wood"), bx("Back", (7.5, 0, 14), (8.5, 24, 15), "wood"),
        bx("Board", (1, 10, 8), (15, 26, 9), "sketch", faces=("north",), full=True), bx("Shelf", (1, 9, 7), (15, 10, 10), "wood")],
         box=(0.06, 0, 0.4, 0.94, 1.62, 0.94), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:paper-parchment", 2, 1), ("game:stick", 2, 1))})
    prop("thronetable", "Long Table", [
        bx("Top", (0, 12, 0), (16, 13, 16), "tablecloth"), bx("Skirt", (0, 8, 0), (16, 12, 16), "tablecloth", faces=("east", "west")),
        bx("Plate", (4, 13, 4), (12, 13.4, 12), "china"), bx("Candle", (7.5, 13, 1), (8.5, 18, 2), "white")],
         box=(0, 0, 0, 1, 0.82, 1), oriented=False, material="Wood", sounds=WOOD)
    prop("trialchair", "The Second Chair", [
        bx("Seat", (2, 8, 2), (14, 10, 14), "velvet"), bx("Back", (2, 10, 12), (14, 30, 14), "velvet"),
        bx("Leg1", (2, 0, 2), (4, 8, 4), "gilt"), bx("Leg2", (12, 0, 2), (14, 8, 4), "gilt"),
        bx("Leg3", (2, 0, 12), (4, 8, 14), "gilt"), bx("Leg4", (12, 0, 12), (14, 8, 14), "gilt"),
        bx("Crest", (5, 30, 12), (11, 33, 14), "gilt")],
         box=(0.12, 0, 0.12, 0.88, 0.62, 0.88), material="Wood", sounds=WOOD,
         comment="The second chair at the King's table. Sit in it, and the trial begins",
         extra={"class": "BackroomsTrialChair", "drops": []})
    prop("kingstatue", "The King", [
        bx("Plinth", (-2, 0, -2), (18, 6, 18), "kingstone"), bx("Robe", (1, 6, 2), (15, 26, 14), "kingstone"),
        bx("Chest", (2, 26, 3), (14, 36, 13), "kingstone"), bx("Head", (4, 36, 4), (12, 45, 12), "kingstone", rot=(0, 0, 8)),
        bx("Crown", (3.5, 45, 3.5), (12.5, 49, 12.5), "gilt", rot=(0, 0, 8)),
        bx("Sword", (13, 6, -2), (15, 40, 0), "chrome", rot=(-10, 0, 0)), bx("Hilt", (11, 38, -2), (17, 40, 0), "gilt", rot=(-10, 0, 0)),
        bx("ArmL", (-1, 22, 5), (3, 36, 10), "kingstone", rot=(0, 0, -12)), bx("ArmR", (13, 22, 1), (17, 36, 6), "kingstone", rot=(-20, 0, 12))],
         box=(-0.12, 0, -0.12, 1.12, 3, 1.12), material="Stone", sounds=STONE,
         comment="A twisted stone statue of a king, sword in hand, crown on his head. The crown is called Machination",
         extra={"drops": []})
    # A car tipped on its side among the heaps: the old car's body, turned over onto its left flank
    def tipped(body):
        return [bx("Body", (0, 0, 4), (12, 30, 60), body, rot=(0, 0, 0)), bx("Roof", (12, 3, 26), (22, 27, 50), body),
                bx("Under", (-0.5, 1, 6), (0, 29, 58), "metaldark"),
                bx("WheelA", (2, 26, 8), (10, 32, 16), "rubber"), bx("WheelB", (2, 26, 46), (10, 32, 54), "rubber"),
                bx("Glass", (12.2, 6, 27), (22.2, 24, 49), "lampglass", faces=("east",))]
    prop("tippedcar", "Overturned Car", {c: tipped(f"oldcar-{c}") for c in ("black", "green")}, box=(0, 0, 0, 1, 1.9, 1),
         material="Metal", sounds=METAL, comment="A 1930s car tipped on its side among the heaps of furniture",
         extra={"drops": drops(("metalbracket", 2, 1), ("scrapwire", 1, 0.5), ("glassshard", 1, 0.5))})

    prop("slide", "Slide", [
        bx("Ramp", (3, 0, -12), (13, 1, 16), "redmetal", rot=(-30, 0, 0), origin=(8, 0, 16)),
        bx("SideL", (2, 1, -12), (3, 3, 16), "trafficyellow", rot=(-30, 0, 0), origin=(8, 0, 16)),
        bx("SideR", (13, 1, -12), (14, 3, 16), "trafficyellow", rot=(-30, 0, 0), origin=(8, 0, 16)),
        bx("Ladder1", (3, 0, 16), (4, 16, 17), "steel"), bx("Ladder2", (12, 0, 16), (13, 16, 17), "steel"),
        bx("Top", (3, 14, 13), (13, 15, 17), "steel")],
         box=(0.06, 0, 0, 0.94, 1, 1), material="Metal", sounds=METAL)


def items():
    data = {"code": "almondmilk", "class": "BackroomsAlmondWater", "maxstacksize": 8, "texture": {"base": "item/almondmilk"},
            "creativeinventory": {"general": ["*"], "items": ["*"]},
            "nutritionProps": {"satiety": 300, "foodcategory": "Dairy"}, "materialDensity": 1000,
            "attributes": {"stabilityRestored": 0.1}}
    data.update(TRANSFORMS)
    ground_storable(data)
    write_json(os.path.join(ASSETS, "itemtypes", "motion", "almondmilk.json"), data, "Almond Milk, from the milk vans of Level 94")
    LANG["item-almondmilk"] = "Almond Milk"
    LANG["itemdesc-almondmilk"] = "From the crates of a milk van in Level 94. Creamy, sweet, and it pours like it's being animated a frame at a time. Steadies you a little, like Almond Water."
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([12, 2, 19, 6], fill=(220, 60, 60, 255))
    d.rectangle([13, 6, 18, 9], fill=(232, 236, 236, 230))
    d.rounded_rectangle([9, 9, 22, 29], 3, fill=(250, 248, 240, 255), outline=(200, 204, 206, 255))
    d.rectangle([10, 15, 21, 22], fill=(70, 120, 190, 255))
    T.save(img, "item/almondmilk.png")
    data = {"code": "crownshard", "maxstacksize": 1, "texture": {"base": "item/crownshard"},
            "creativeinventory": {"general": ["*"], "items": ["*"]}, "materialDensity": 2000}
    data.update(TRANSFORMS)
    ground_storable(data)
    write_json(os.path.join(ASSETS, "itemtypes", "motion", "crownshard.json"), data, "A shard of the King's crown")
    LANG["item-crownshard"] = "Machination's Crown Shard"
    LANG["itemdesc-crownshard"] = "A gilt shard of the King's crown, left when he burst into light. While you carry it, the Animations of Level 94 take you for one of their own."
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.polygon([(6, 26), (10, 8), (14, 18), (18, 5), (22, 18), (26, 10), (25, 26)], fill=(222, 178, 60, 255), outline=(150, 110, 30, 255))
    d.ellipse([15, 19, 19, 23], fill=(190, 30, 40, 255))
    T.save(img, "item/crownshard.png")


def lang():
    LANG.update({
        "level-13": "Level 94: Motion",
        "levelhint-13": "Be indoors by nightfall.",
        "level-941": "The Castle of the Transparent Mountain",
        "levelhint-941": "Touch nothing.",
        "cinemascreen": "You walk into the picture, and fall out of a black square in the sky.",
        "dollhouse": "The door opens onto a hilltop, under a sky too blue to be real.",
        "floodedhouse": "The water takes you.",
        "twilightgate": "The rusted gate swings open in the half light.",
        "castle-alarm": "Somewhere in the castle, a key is turning.",
        "thronedoor-shut": "This door is only painted on. Today, at least.",
        "throneroom": "A long dim hall, a table set for two, and at its head a king of stone.",
        "trial-busy": "The King is receiving someone else.",
        "trial-start": "\"Sit, sit. Let us see what you are afraid of.\" The King's stone face does not move. Something stirs at the end of the table.",
        "trial-won": "\"He's only what you think he is.\" The King bursts into light.",
        "trial-carried": "The light carries you somewhere else.",
        "blockhelp-trialchair": "Sit down",
    })


def far_castle():
    """The castle on its glass mountain as it looks from a long way off, for the picture drawn on the horizon when the
    real one is past the view distance (src/Regions/MotionLandmark.cs). Two pixels to the block, its foot at the bottom
    middle: the mountain 180 blocks across at the foot and 40 high, the castle 56 across on top of it, its towers' red
    roofs stepping in to 61. Symmetric, so it reads the same whichever way it is turned to face you."""
    W, H = 360, 128
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def px(bx, by):
        return 180 + 2 * bx, H - 2 * by

    # The mountain: a shell of glass, dark and hollow inside, so it shows the dark through a pale skin, paler toward
    # the top where it catches the sky, and a seam of light down each flank
    for by in range(40):
        half = 90 - 50 * by / 40
        t = by / 40
        c = (int(116 + 70 * t), int(146 + 66 * t), int(180 + 52 * t), 255)
        x0, y0 = px(-half, by + 1)
        x1, y1 = px(half, by)
        d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=c)
    for side in (-1, 1):
        for by in range(2, 38):
            x, y = px(side * (86 - 50 * by / 40), by)
            d.rectangle([x - 1, y - 2, x, y - 1], fill=(244, 250, 255, 255))
        x0, y0 = px(side * 30, 6)
        x1, y1 = px(side * 18, 34)
        d.line([x0, y0, x1, y1], fill=(236, 246, 252, 255), width=2)

    white, line, red, redline = (240, 238, 232, 255), (214, 210, 202, 255), (196, 44, 40, 255), (160, 30, 30, 255)
    # The curtain wall, eight high, with battlements along its top
    x0, y0 = px(-28, 48)
    x1, y1 = px(28, 40)
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill=white)
    for by in (42, 44, 46):
        d.line([x0, px(0, by)[1], x1 - 1, px(0, by)[1]], fill=line)
    for bx in range(-27, 27, 2):
        a, b = px(bx, 49)
        d.rectangle([a, b, a + 1, b + 1], fill=white)
    # The gate: a dark arch in the middle
    a, b = px(-2, 44)
    c, e = px(2, 40)
    d.rectangle([a, b, c - 1, e - 1], fill=(40, 34, 40, 255))
    d.rectangle([a + 1, b - 1, c - 2, b], fill=(40, 34, 40, 255))
    # The towers at the corners, thirteen high, their red roofs stepping in to a point
    for side in (-1, 1):
        lo, hi = (-28, -21) if side < 0 else (21, 28)
        a, b = px(lo, 53)
        c, e = px(hi, 40)
        d.rectangle([a, b, c - 1, e - 1], fill=white)
        for by in (44, 48, 52):
            d.line([a, px(0, by)[1], c - 1, px(0, by)[1]], fill=line)
        # A slit window or two
        mid = (lo + hi) / 2
        for by in (45, 50):
            u, v = px(mid, by + 1)
            d.rectangle([u - 1, v, u, v + 2], fill=(52, 44, 52, 255))
        for ring, (top, inset) in enumerate(((55, 0), (57, 1), (59, 2), (61, 3))):
            a, b = px(lo + inset, top)
            c, e = px(hi - inset, top - 2 if ring else 53)
            d.rectangle([a, b, c - 1, e - 1], fill=red)
            d.line([a, e - 1, c - 1, e - 1], fill=redline)
    T.save(img, "environment/motioncastle-far.png")


def generate():
    textures()
    far_castle()
    blocks()
    props()
    items()
    lang()


# ======================= Graphics pass B13 =======================
# Each B13 painter runs after the old one under the same keys (plus new versions beside them), so dropping its call
# from b13_textures() reverts that family's textures; the models are in the *_b13 functions that blocks() and props()
# call.

import matlib as M  # noqa: E402
import modelkit as MK  # noqa: E402
from gen_city import CITY_F3, CITY_F5, ptext_c  # noqa: E402
from gen_textures import inside_block  # noqa: E402

# Each family's mean colour before B13, measured on main's PNGs: the new versions are shifted to it
MOTION_MEAN = {
    "clayturf-light": (98.8, 186.8, 64.8), "clayturf-dark": (70.8, 150.8, 48.8),
    "clayturf-side-light": (84.5, 159.7, 54.4), "clayturf-side-dark": (59.8, 129.1, 40.6),
    "claysoil": (166.9, 102.9, 62.9), "motionpath": (180.3, 148.3, 102.3), "motionconcrete": (206.4, 202.4, 192.4),
    "motionasphalt": (85.0, 85.0, 91.0), "motionkerb": (219.4, 217.4, 209.4),
    "castlewall": (234.3, 232.0, 225.6), "castleroof": (186.2, 39.6, 36.5),
    "towertank": (235.1, 235.1, 231.1), "towersteel": (149.2, 153.2, 159.2), "fountainstone": (204.7, 194.7, 168.7),
    "milkvan": (242.7, 240.7, 234.7), "milkvan-side": (230.1, 232.3, 231.0),
}
TURF = {"light": (98, 186, 64), "dark": (70, 150, 48)}
CLAY = (168, 104, 64)


def matched(img, key, vkey=None):
    return T.match_rgb(img, MOTION_MEAN[key], key="b13" + (vkey or key))


def stroke(img, x, y, a, length, depth, ridge=0.6):
    """A tool mark pressed into clay: a short groove (darker) along angle a, with the clay it pushed aside raised
    (lighter) along its upper side. Wraps."""
    w, h = img.size
    px = img.load()
    nx, ny = -math.sin(a), math.cos(a)
    if ny > 0:  # the ridge on the side nearer the light (up the texture)
        nx, ny = -nx, -ny
    for i in range(length):
        t = math.sin(math.pi * (i + 0.5) / length) ** 0.5
        X, Y = round(x + math.cos(a) * i), round(y + math.sin(a) * i)
        px[X % w, Y % h] = M.rgba(M.lift(px[X % w, Y % h][:3], -depth * t), px[X % w, Y % h][3])
        RX, RY = round(X + nx), round(Y + ny)
        px[RX % w, RY % h] = M.rgba(M.lift(px[RX % w, RY % h][:3], depth * ridge * t), px[RX % w, RY % h][3])


def arcs(img, cx, cy, radii, depth, seed, gap=(0.6, 1.4)):
    """Part of a thumbprint: concentric arcs (each broken by a gap) pressed in, a lit pixel inside each."""
    rng = random.Random(seed)
    w, h = img.size
    px = img.load()
    for r in radii:
        a0 = rng.uniform(0, 2 * math.pi)
        span = 2 * math.pi - rng.uniform(*gap)
        n = max(6, int(span * r * 1.6))
        for i in range(n):
            a = a0 + span * i / n
            X, Y = round(cx + r * math.cos(a)), round(cy + r * math.sin(a))
            px[X % w, Y % h] = M.rgba(M.lift(px[X % w, Y % h][:3], -depth))
            IX, IY = round(cx + (r - 1) * math.cos(a)), round(cy + (r - 1) * math.sin(a))
            if (IX, IY) != (X, Y):
                px[IX % w, IY % h] = M.rgba(M.lift(px[IX % w, IY % h][:3], depth * 0.35))


def smear(img, x, y, a, length, width, depth):
    """(round 2) A thumb dragged across soft clay: a broad shallow trough along angle a, `width` px across, the clay
    it pushed up lit along its far edge, fading at both ends. Wraps."""
    w, h = img.size
    px = img.load()
    nx, ny = -math.sin(a), math.cos(a)
    for i in range(length * 2):
        t = math.sin(math.pi * (i + 0.5) / (length * 2))
        cx, cy = x + math.cos(a) * i / 2, y + math.sin(a) * i / 2
        for j in range(-width, width + 1):
            X, Y = round(cx + nx * j / 1.2), round(cy + ny * j / 1.2)
            f = j / max(1, width)
            d = -depth * t * (1 - f * f) if j < width else depth * 0.8 * t
            q = px[X % w, Y % h]
            px[X % w, Y % h] = M.rgba(M.lift(q[:3], d / 2), q[3])


def clay_ground(base, seed, mottle=5, grain=2.5, hue=2.0):
    return M.noise_hv(base, grain, seed, S, mottle, (16, 8), hue=hue)


def turf_top_b13(kind, v):
    """Clay turf from above (B13): a smooth plasticine green, softly modelled, covered in the small pressed strokes a
    modelling tool leaves when it is used to make grass (each a groove with the clay pushed up beside it, at every
    angle, so a block reads the same at any turn). Three versions on one shared ground (matlib.turn_safe), turned at
    random; no thumbprints on top (they read as dirt from above). The mean is the old one."""
    base = TURF[kind]
    gs = seed_of("b13turf" + kind)
    ground = clay_ground(base, gs, grain=0)
    img = clay_ground(base, gs + 31 * v, grain=2.5)
    M.turn_safe(img, ground, band=8, keep=0.5)
    rng = random.Random(gs + 101 * v)
    for _ in range(130):
        stroke(img, rng.uniform(0, S), rng.uniform(0, S), rng.uniform(0, 2 * math.pi), rng.choice((2, 2, 3)), rng.uniform(10, 15), ridge=0.75)
    for _ in range(4):  # (round 2) thumb drags in the clay, small and many, at random angles
        smear(img, rng.uniform(0, S), rng.uniform(0, S), rng.uniform(0, 2 * math.pi), rng.randint(5, 8), 2, 7)
    return matched(img, f"clayturf-{kind}", f"turf{kind}")


def turf_side_b13(kind, v, thumb=False):
    """Clay turf from the side (B13): the same plasticine, a shade darker as before, with a rounded lip along the top
    where the turf turns the edge (lit), grass strokes running up, darker toward the foot of the step, and the clay
    once showing at the very foot (removed in round 2). Versions share the ground and the lip; a thumbprint is in one block
    in eight, faint and inside the block."""
    base = tuple(int(c * 0.87) for c in TURF[kind])
    gs = seed_of("b13turfside" + kind)
    img = clay_ground(base, gs, mottle=4, grain=2.5)
    px = img.load()
    for y in range(S):
        d = {0: 10, 1: 5, 2: 2}.get(y, 0) - max(0, y - 24) * 0.9
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], d))
    rng = random.Random(gs + 101 * v)
    for _ in range(90):
        stroke(img, rng.uniform(0, S), rng.uniform(2, S - 3), -math.pi / 2 + rng.uniform(-0.5, 0.5), rng.choice((2, 3, 3)), rng.uniform(8, 12), ridge=0.75)
    for x in range(S):  # the lip's ragged lower edge: blades overhanging it
        if rng.random() < 0.35:
            px[x, 3] = M.rgba(M.lift(px[x, 3][:3], 5))
    # (round 2) the clay line at the foot is gone (it read as a line along every step); the face bulges a little,
    # lit above its middle, and carries a few thumb drags, mostly downward, at different places in each version
    for y in range(S):
        d = 2.5 * math.cos(math.pi * (y - 12) / 40)
        for x in range(S):
            px[x, y] = M.rgba(M.lift(px[x, y][:3], d - 1.5))
    for _ in range(4):
        smear(img, rng.uniform(0, S), rng.uniform(5, S - 8), math.pi / 2 + rng.uniform(-0.6, 0.6), rng.randint(5, 8), 2, 7)
    if thumb:
        plain = img.copy()
        arcs(img, 15.5, 14.5, (3, 5, 7), 3, gs + 9)
        img = inside_block(plain, img, band=6)
    return matched(img, f"clayturf-side-{kind}", f"turfside{kind}")


def clay_b13(v):
    """The modelling clay under the turf (B13): smooth, softly modelled, with the odd partial thumbprint and smear and
    a few little lumps, small and many, so no one mark repeats; three versions on one ground, turned at random."""
    gs = seed_of("b13claysoil")
    ground = clay_ground(CLAY, gs, mottle=6, grain=0, hue=3)
    img = clay_ground(CLAY, gs + 31 * v, mottle=6, grain=3, hue=3)
    M.turn_safe(img, ground, band=8, keep=0.5)
    rng = random.Random(gs + 101 * v)
    for k in range(5):
        arcs(img, rng.uniform(0, S), rng.uniform(0, S), (2, 4) if k % 2 else (3,), 5, gs + v * 17 + k, gap=(1.5, 3.0))
    for _ in range(14):
        stroke(img, rng.uniform(0, S), rng.uniform(0, S), rng.uniform(0, 2 * math.pi), rng.choice((2, 3, 4)), 5)
    for _ in range(6):  # lumps: lit on top, shadow under
        x, y = rng.randrange(S), rng.randrange(S)
        M.touch(img, x, y, 0.08)
        M.touch(img, x, y + 1, -0.06)
    return matched(img, "claysoil")


def path_b13(v):
    """The dirt path (B13): pale clay trodden smooth, with little clay pebbles (each lit on top with a shadow under it)
    and a few smears; three versions on one ground, turned at random."""
    base = (182, 150, 104)
    gs = seed_of("b13path")
    ground = clay_ground(base, gs, mottle=6, grain=0, hue=3)
    img = clay_ground(base, gs + 31 * v, mottle=6, grain=3, hue=3)
    M.turn_safe(img, ground, band=8, keep=0.5)
    rng = random.Random(gs + 101 * v)
    px = img.load()
    for _ in range(rng.randint(6, 10)):
        x, y = rng.randrange(S), rng.randrange(S)
        c = M.lift(base, rng.uniform(-10, 8))
        for dx, dy, d in ((0, 0, 4), (1, 0, 0), (0, 1, -2), (1, 1, -6)):
            px[(x + dx) % S, (y + dy) % S] = M.rgba(M.lift(c, d))
        px[(x + 1) % S, (y + 2) % S] = M.rgba(M.lift(px[(x + 1) % S, (y + 2) % S][:3], -9))
        px[(x + 2) % S, (y + 1) % S] = M.rgba(M.lift(px[(x + 2) % S, (y + 1) % S][:3], -6))
    for _ in range(10):
        stroke(img, rng.uniform(0, S), rng.uniform(0, S), rng.uniform(0, 2 * math.pi), rng.choice((3, 4)), 5)
    return matched(img, "motionpath")


def asphalt_b13(v):
    """The road (B13): asphalt as a modeller would make it, smooth dark clay with a fine grit pressed in (matlib.asphalt
    at low contrast), three versions on one ground, turned at random. No swirl."""
    base = (86, 86, 92)
    gs = seed_of("b13asphalt")
    ground = M.asphalt(gs, base=base, grain=0, aggregate=0.0, binder=0.0, pits=0.0, mottle=5)
    img = M.asphalt(gs + 31 * v, base=base, grain=3, mottle=5, aggregate=0.14, binder=0.25, chip=(4, 10), pits=0.002,
                    shadow=0.06)
    M.turn_safe(img, ground, band=8, keep=0.5)
    # (round 2) a faint hairline crack in the third version only, inside the block, listed one block in seven
    plain = img.copy()
    if v == 3:
        M.crack(img, gs + 5, at=(9, 14), length=(12, 16), strength=0.16)
    img = inside_block(plain, img, band=4)
    return matched(img, "motionasphalt")


def slab_b13(key, base, v, kerb=False):
    """A concrete path slab or a kerb stone (B13), one to a block: a smooth cast face with a little pinholing and
    a sunk joint on all four edges (each block shares half), so a run of them reads as slabs
    whichever way it goes; the kerb's arris is rounded (a lit band inside the joint). The old line across the kerb
    is gone: kerbs run both ways. Three versions on one ground, turned at random (the joints are symmetric)."""
    gs = seed_of("b13" + key)
    ground = clay_ground(base, gs, mottle=4, grain=0, hue=1.2)
    img = M.concrete(gs + 31 * v, base=base, grain=2.5, mottle=4, aggregate=0.0, pores=0.004, hue=1.2)
    M.turn_safe(img, ground, band=8, keep=0.5)
    rng = random.Random(gs + 101 * v)
    px = img.load()
    for y in range(S):
        for x in range(S):
            e = min(x, y, S - 1 - x, S - 1 - y)
            d = {0: -13, 1: -3}.get(e, 0)
            if kerb and e in (2, 3):
                d += 4 if e == 2 else 2
            if d:
                px[x, y] = M.rgba(M.lift(px[x, y][:3], d))
    return matched(img, key)


def castle_b13(v):
    """The castle's white stone (B13): ashlar at the old courses (8 px, the joints 16 apart in a running bond), each
    stone its own shade, lit along its top, with sunk joints; three versions share the stones' faces and differ in
    shade only (matlib.brick tones). It keeps its glow."""
    img = M.brick(seed_of("b13castle"), base=(240, 238, 232), mortar=(212, 208, 198), course=8, length=16, jitter=5, hue=1.5,
                  recess=0.7, pits=0.0, grain=3, mottle=4, tones=seed_of("b13castlet") + v)
    return matched(img, "castlewall", "castle")


def roof_b13(v):
    """The castle's red roofs (B13): clay tiles, each its own red, lit at its lower lip and shadowed where the course
    above overlaps it; three versions by tone. The red keeps the old mean."""
    # (round 2) bigger tiles, 8 x 8 in courses that break joint, each tail rounded (its lower corners in the shadow
    # of the course below) and lit along its lower lip, with the course above casting a dark line over its head
    rng = random.Random(seed_of("b13rooft") + v)
    img = M.noise_hv((190, 44, 38), 2.5, seed_of("b13roof"), S, 4, (16, 8), hue=2.0)
    px = img.load()
    for r in range(4):
        off = 4 if r % 2 else 0
        for c in range(4):
            tv = rng.uniform(-7, 7)
            x0, y0 = c * 8 + off, r * 8
            for yy in range(8):
                for xx in range(8):
                    X, Y = (x0 + xx) % S, y0 + yy
                    d = tv + (yy - 3.5) * 0.9
                    if yy == 0:
                        d -= 22  # the overlap's shadow
                    elif yy == 1:
                        d -= 8
                    if yy == 6:
                        d += 6  # the lit lip
                    if xx in (0, 7):
                        d -= 9 if yy >= 5 else 5  # the joint, deeper at the rounded tail
                    if yy == 7 and xx in (0, 1, 6, 7):
                        d -= 14
                    px[X, Y] = M.rgba(M.lift(px[X, Y][:3], d))
    return matched(img, "castleroof", "roof")


def tower_b13(v):
    """The water tower (B13): its tank is white-painted riveted plate, a seam and a row of rivets at the block's edges,
    a faint rust weep from a rivet in one version; its legs and roof painted grey steel, worn at the edges."""
    img = M.riveted_plate(seed_of("b13tank"), base=(236, 236, 232), grain=2, mottle=4, pitch=4, layout="edges")
    if v == 3:
        M.drips(img, 2, seed_of("b13tankd"), color=(150, 110, 80), length=(5, 11), strength=0.18, start=3)
    return matched(img, "towertank", "tank")


def fountain_tex_b13():
    """The fountain's cast stone (B13): fine sandstone-coloured cast stone with small pores and a soft mottle, and a
    smoother, lighter cap; and the Almond Water standing in its bowl."""
    img = M.concrete(seed_of("b13fountain"), base=(206, 196, 170), grain=3, mottle=6, aggregate=0.015, pores=0.006, hue=1.5)
    save(matched(img, "fountainstone"), "fountainstone")
    cap = M.concrete(seed_of("b13fountaincap"), base=(214, 205, 180), grain=2, mottle=4, aggregate=0.0, pores=0.003, hue=1.2)
    save(cap, "fountaincap")
    w = M.noise_hv((236, 228, 206), 2, seed_of("b13almondwater"), S, 5, (16, 8), hue=1.5)
    rng = random.Random(seed_of("b13awr"))
    for _ in range(8):  # ripples
        stroke(w, rng.uniform(0, S), rng.uniform(0, S), rng.uniform(-0.3, 0.3), rng.choice((3, 4, 5)), -6, ridge=-0.4)
    save(w, "fountainwater")


def glass_b13(v):
    """The mountain's glass (B13): the old pale sky-tinted gradient without the outline that drew every block, and
    in two versions of four a short, soft glint at a different place."""
    img = Image.new("RGBA", (S, S))
    d = ImageDraw.Draw(img)
    for y in range(S):
        t = y / S
        d.line([0, y, S, y], fill=(int(214 - 40 * t), int(234 - 30 * t), 248, 150))
    if v in (2, 4):
        x0, y0 = (6, 24) if v == 2 else (14, 28)
        for k in range(9):
            a = 190 - abs(k - 4) * 12
            for w_ in (0, 1):
                X, Y = x0 + k + w_, y0 - k
                if 0 <= X < S and 0 <= Y < S:
                    img.putpixel((X, Y), (250, 252, 255, a - 30 * w_))
    return img


def furniture_tex_b13():
    """1950s things (B13): the icebox's white enamel and its doors, the radio's walnut, grille cloth and dial, the
    telephone's bakelite dial ring."""
    enamel = M.painted_metal(seed_of("b13enamel"), base=(238, 234, 220), grain=2, mottle=3, panel=False, chips=0, under=(90, 90, 90))
    save(enamel, "iceboxenamel")
    door = M.painted_metal(seed_of("b13iceboxdoor"), base=(240, 236, 222), grain=2, mottle=3, panel=True, chips=0, under=(90, 90, 90))
    save(door, "iceboxdoor")
    walnut = M.wood_planks(seed_of("b13walnut"), base=(112, 72, 42), planks=1, direction="h", grain=3, contrast=0.8, per_plank=4)
    save(walnut, "radiowalnut")
    cloth = M.fabric(seed_of("b13radiocloth"), base=(196, 170, 120), weave="basket", contrast=12, thread=3)
    save(cloth, "radiocloth")
    dial = Image.new("RGBA", (S, S), (226, 206, 150, 255))
    p = dial.load()
    for x in range(2, S - 2, 3):
        for y in range(10, 14 if x % 6 == 2 else 12):
            p[x, y] = (90, 64, 40, 255)
    ptext_c(dial, "RADIO", 17, (110, 40, 30), CITY_F5)
    for y in range(4, 22):
        p[19, y] = (176, 30, 24, 255)
    save(dial, "radiodial")


def van_tex_b13():
    """The milk van (B13): cream enamel over its body, and its sides in the dairy's livery at the body's own
    proportions (112 x 40, so the letters stay square): a blue pinstripe and ALMOND MILK in crisp pixel letters."""
    body = M.painted_metal(seed_of("b13van"), base=(244, 242, 236), grain=2, mottle=3, panel=False, chips=2, under=(120, 120, 118))
    save(matched(body, "milkvan"), "milkvan")
    side = M.painted_metal(seed_of("b13vanside"), base=(244, 242, 236), grain=2, mottle=3, size=(112, 40), panel=False, chips=3,
                           under=(120, 120, 118))
    px = side.load()
    blue = (42, 106, 176)
    for x in range(112):
        for y in (31, 32):
            px[x, y] = M.rgba(blue)
        px[x, 34] = M.rgba(M.lift(blue, 20))
    ptext_c(side, "ALMOND MILK", 11, blue, CITY_F5)
    ptext_c(side, "FRESH EVERY DAY", 22, M.lift(blue, -10), CITY_F3)
    M.grime(side, 0.06, seed_of("b13vansideg"), cells=(8, 4), bias="bottom", cover=0.4)
    save(side, "milkvan-side")
    grille = M.brushed_metal(seed_of("b13vangrille"), base=(196, 200, 204), streak=6, sheen=8)
    M.emboss_lines(grille, xs=tuple(range(0, S, 4)), strength=0.25)
    save(grille, "milkvangrille")


def nooutlet_b13():
    """The NO OUTLET sign (B13): crisp pixel letters on a lightly weathered yellow plate with a black border."""
    img = M.painted_metal(seed_of("b13nooutlet"), base=(248, 210, 30), grain=2, mottle=3, panel=False, chips=2, under=(150, 150, 150))
    ptext_c(img, "NO", 4, (16, 16, 16), CITY_F5, scale=2)
    ptext_c(img, "OUTLET", 22, (16, 16, 16), CITY_F3)
    p = img.load()
    for i in range(S):
        for (x, y) in ((i, 0), (i, S - 1), (0, i), (S - 1, i)):
            p[x, y] = (16, 16, 16, 255)
    save(img, "nooutlet")


TURF_SIDE_MIX = ["", "-2", "-3", "", "-2", "-3", "-4"]  # with the base: the thumbprint (-4) one block in eight


def b13_textures():
    for kind in ("light", "dark"):
        for v in (1, 2, 3):
            save(turf_top_b13(kind, v), f"clayturf-{kind}" + ("" if v == 1 else f"-{v}"))
            save(turf_side_b13(kind, v), f"clayturf-side-{kind}" + ("" if v == 1 else f"-{v}"))
        save(turf_side_b13(kind, 4, thumb=True), f"clayturf-side-{kind}-4")
    for v in (1, 2, 3):
        sfx = "" if v == 1 else f"-{v}"
        save(clay_b13(v), "claysoil" + sfx)
        save(path_b13(v), "motionpath" + sfx)
        save(asphalt_b13(v), "motionasphalt" + sfx)
        save(slab_b13("motionconcrete", (208, 204, 194), v), "motionconcrete" + sfx)
        save(slab_b13("motionkerb", (222, 220, 212), v, kerb=True), "motionkerb" + sfx)
        save(castle_b13(v), "castlewall" + sfx)
        save(roof_b13(v), "castleroof" + sfx)
        save(tower_b13(v), "towertank" + sfx)
    for v in (1, 2, 3, 4):
        save(glass_b13(v), "glassmountain" + ("" if v == 1 else f"-{v}"))
    steel = M.painted_metal(seed_of("b13towersteel"), base=(150, 154, 160), grain=3, mottle=4, panel=False, chips=0, screws=False)
    M.grime(steel, 0.06, seed_of("b13towersteelg"), cells=(8, 4), cover=0.4)
    save(matched(steel, "towersteel"), "towersteel")
    fountain_tex_b13()
    furniture_tex_b13()
    van_tex_b13()
    nooutlet_b13()
    tower_d3_textures()  # D3
    siren_tex_d4()  # D4


def alts(key, n, mix=None):
    """A texture entry with its B13 versions as alternates (and turned, with `turns`)."""
    names = [key + s for s in (mix or [""] + [f"-{k}" for k in range(2, n + 1)])]
    return names


def tex_entry(key, versions, turns=(0,)):
    """{base, alternates}: every version at every turn (the base at turn 0 is the base)."""
    out = {"base": f"block/detail/{key}", "alternates": []}
    for i, v in enumerate(versions):
        for r in turns:
            if i == 0 and r == 0:
                continue
            out["alternates"].append({"base": f"block/detail/{v}", "rotation": r} if r else {"base": f"block/detail/{v}"})
    return out


# ---- Models ----

def octo_wheel(name, x1, x2, yc, zc, r, hub="chrome"):
    """A tyre seen side on as an octagon (three crossed boxes) with a chrome hub cap (B13; the wheels were square)."""
    k = r * 0.41
    return [bx(f"{name}A", (x1, yc - r, zc - k), (x2, yc + r, zc + k), "rubber"),
            bx(f"{name}B", (x1 + 0.15, yc - k, zc - r), (x2 - 0.15, yc + k, zc + r), "rubber"),
            bx(f"{name}C", (x1 + 0.3, yc - r * 0.77, zc - r * 0.77), (x2 - 0.3, yc + r * 0.77, zc + r * 0.77), "rubber"),
            bx(f"{name}Hub", (x1 - 0.3, yc - r * 0.42, zc - r * 0.42), (x2 + 0.3, yc + r * 0.42, zc + r * 0.42), hub)]


def milkvan_b13():
    """The milk van (B13): the old body, with a rounded roof edge, the cab's side windows, a chrome grille and bumper,
    round headlamps on the mudguards, mudguards over octagonal wheels with chrome hubs, and the dairy's livery."""
    els = [bx("Body", (1, 2.5, 8), (31, 23, 63), "milkvan", faces=("north", "up", "down", "south")),
           bx("Sides", (1, 2.5, 8), (31, 23, 63), "milkvan-side", faces=("east", "west"), full=True),
           bx("RoofEdge", (1.5, 23, 8.5), (30.5, 24.5, 62.5), "milkvan"),
           bx("Cab", (2, 2.5, 0.5), (30, 13, 9), "milkvan"),
           bx("CabTop", (3, 13, 2), (29, 20, 9), "milkvan", faces=("up", "east", "west", "north")),
           bx("Windscreen", (4, 13.5, 1.95), (28, 19.5, 2), "lampglass", faces=("north",)),
           bx("SideWinL", (2.95, 14, 3), (3, 19, 8), "lampglass", faces=("west",)),
           bx("SideWinR", (29, 14, 3), (29.05, 19, 8), "lampglass", faces=("east",)),
           bx("Grille", (9, 4, 0.1), (23, 11.5, 0.5), "milkvangrille", faces=("north", "up", "east", "west")),
           bx("Bumper", (0.75, 2.75, -0.6), (31.25, 4.5, 0.6), "chrome"),
           bx("BumperR", (0.75, 2.75, 62.8), (31.25, 4.5, 63.8), "chrome")]
    for i, x in enumerate((5.5, 26.5)):
        els += [bx(f"Lamp{i}", (x - 1.6, 9, -0.4), (x + 1.6, 12.2, 1.5), "chrome"),
                bx(f"Lens{i}", (x - 1.2, 9.4, -0.45), (x + 1.2, 11.8, -0.4), "lampglass", faces=("north",))]
    for nm, (x1, x2), z in (("FL", (0, 3), 6), ("FR", (29, 32), 6), ("RL", (0, 3), 52), ("RR", (29, 32), 52)):
        els += octo_wheel(f"Wheel{nm}", x1, x2, 4, z, 4)
        els.append(bx(f"Guard{nm}", (x1 - 0.4, 7.5, z - 5), (x2 + 0.4, 9, z + 5), "milkvan"))
    return els


def oldcar_wheels_b13(els):
    """The old car's square wheels as octagons with chrome hubs (B13); the rest of the car is unchanged."""
    out = [e for e in els if not e["name"].startswith("Wheel")]
    for nm, (x1, x2), z in (("FL", (0, 4), 12), ("FR", (28, 32), 12), ("RL", (0, 4), 50), ("RR", (28, 32), 50)):
        out += octo_wheel(f"Wheel{nm}", x1, x2, 4, z, 4)
    return out


def sirenpole_b13():
    """A siren pole (B13): a wooden pole on an iron shoe, a hub with four horns that flare from a throat to a bell,
    and a cap."""
    els = [bx("Pole", (7, 0, 7), (9, 52, 9), "wood"), bx("Shoe", (6, 0, 6), (10, 2.5, 10), "metaldark"),
           bx("ShoeCap", (6.5, 2.5, 6.5), (9.5, 3, 9.5), "metaldark"),
           bx("Hub", (5.5, 46, 5.5), (10.5, 50, 10.5), "metaldark"), bx("Cap", (6.5, 52, 6.5), (9.5, 54, 9.5), "metaldark"),
           bx("Collar", (6.5, 50, 6.5), (9.5, 52, 9.5), "metaldark")]
    horn = [bx("Throat", (6.75, 46.75, 2.5), (9.25, 49.25, 5.5), "steel"), bx("Bell", (5.75, 45.5, -0.5), (10.25, 50.5, 2.5), "steel"),
            bx("Mouth", (6.25, 46, -0.55), (9.75, 50, -0.5), "metaldark", faces=("north",))]
    for t in range(4):
        for e in MK.turn(horn, t):
            els.append(dict(e, name=f"{e['name']}{t}"))
    return els


D4_SIREN = True  # (graphics pass D4) horn speakers on cross arms and a junction box; False: B13's hub of boxes


def _horn(name, axis, sign, c1, c2, yc, start, length=6.0, r0=1.0, r1=3.0, t=0.3):
    """(D4) A flared horn speaker: eight plates round its axis, each tilted out from the throat (radius r0, at `start`
    along the axis) to the mouth (r1, `length` further on, the `sign` way along x or z), a parent turned about the axis
    carrying a child tilted about the cross axis (B14, D3). The plates' outsides are the enamel, their insides the dark
    throat; the open mouth shows the inside. c1, c2: the axis's place across (z for an x horn, x for a z horn)."""
    alpha = math.degrees(math.atan2(r1 - r0, length))
    ls = math.hypot(length, r1 - r0)
    w = 2 * r1 * math.tan(math.radians(22.5)) + 0.25
    out = []
    for k in range(8):
        tex_out, tex_in = "sirenhorn", "sirenmouth"
        if axis == "x":
            x1, x2 = (start, start + ls) if sign > 0 else (start - ls, start)
            child = MK.box(f"{name}P{k}", (x1, yc + r0 - t, c1 - w / 2), (x2, yc + r0, c1 + w / 2),
                           {"top": tex_out, "bottom": tex_in, "side": tex_out}, faces=("up", "down", "east" if sign > 0 else "west"))
            child["rotationOrigin"] = [round(start, 4), round(yc + r0, 4), round(c1, 4)]
            child["rotationZ"] = round(alpha * sign, 4)
            parent = {"name": f"{name}A{k}", "from": [0, 0, 0], "to": [0, 0, 0], "faces": {},
                      "rotationOrigin": [round(start, 4), round(yc, 4), round(c1, 4)], "children": [child]}
            if k:
                parent["rotationX"] = k * 45
        else:
            z1, z2 = (start, start + ls) if sign > 0 else (start - ls, start)
            child = MK.box(f"{name}P{k}", (c1 - w / 2, yc + r0 - t, z1), (c1 + w / 2, yc + r0, z2),
                           {"top": tex_out, "bottom": tex_in, "side": tex_out},
                           faces=("up", "down", "south" if sign > 0 else "north"))
            child["rotationOrigin"] = [round(c1, 4), round(yc + r0, 4), round(start, 4)]
            child["rotationX"] = round(-alpha * sign, 4)
            parent = {"name": f"{name}A{k}", "from": [0, 0, 0], "to": [0, 0, 0], "faces": {},
                      "rotationOrigin": [round(c1, 4), round(yc, 4), round(start, 4)], "children": [child]}
            if k:
                parent["rotationZ"] = k * 45
        out.append(parent)
    return out


def _driver(name, axis, sign, c1, yc, start, length=2.5, r=1.6):
    """(D4) The horn's driver: an octagonal can behind the throat (two crossed boxes and the same turned 45 degrees
    about the axis), its back capped, and the throat's dark disk where the horn begins."""
    k = r * math.tan(math.radians(22.5))
    a, b = (start - length * sign, start) if sign > 0 else (start, start - length * sign)
    a, b = min(a, b), max(a, b)
    els = []
    for i, (hy, hc, rot) in enumerate(((r, k, 0), (k, r, 0), (r, k, 45), (k, r, 45))):
        if axis == "x":
            e = MK.box(f"{name}Can{i}", (a, yc - hy, c1 - hc), (b, yc + hy, c1 + hc), "sirenhorn",
                       faces=("north", "south", "up", "down", "west" if sign > 0 else "east"),
                       rot=(rot, 0, 0) if rot else None, origin=(a, yc, c1))
        else:
            e = MK.box(f"{name}Can{i}", (c1 - hc, yc - hy, a), (c1 + hc, yc + hy, b), "sirenhorn",
                       faces=("east", "west", "up", "down", "north" if sign > 0 else "south"),
                       rot=(0, 0, rot) if rot else None, origin=(c1, yc, a))
        els.append(e)
    d = 0.75
    if axis == "x":
        x = start + 0.05 * sign
        els.append(MK.box(f"{name}Throat", (min(x, x + 0.1 * sign), yc - d, c1 - d), (max(x, x + 0.1 * sign), yc + d, c1 + d),
                          "sirenmouth", faces=("east" if sign > 0 else "west",)))
    else:
        z = start + 0.05 * sign
        els.append(MK.box(f"{name}Throat", (c1 - d, yc - d, min(z, z + 0.1 * sign)), (c1 + d, yc + d, max(z, z + 0.1 * sign)),
                          "sirenmouth", faces=("south" if sign > 0 else "north",)))
    return els


def sirenpole_d4():
    """(D4) The siren pole after D3 graded its speakers C+ (B13's hub of four plain grey boxes): the same wooden pole
    on its iron shoe, now with two cross arms, one along x and one along z a little lower, each carrying at either end
    a flared horn speaker hung under it on a strap (a driver can behind a horn of eight tilted plates, dark inside), the
    four horns facing the four ways down the streets; a junction box on the pole with its lid and a conduit up to the
    arms. Same footprint and collision box."""
    els = [bx("Pole", (7, 0, 7), (9, 52, 9), "wood"), bx("Shoe", (6, 0, 6), (10, 2.5, 10), "metaldark"),
           bx("ShoeCap", (6.5, 2.5, 6.5), (9.5, 3, 9.5), "metaldark"),
           bx("Cap", (6.5, 52, 6.5), (9.5, 53.5, 9.5), "metaldark"), bx("CapTop", (7, 53.5, 7), (9, 54, 9), "metaldark"),
           # the arms, through the pole, with a clamp plate where each crosses it
           bx("ArmX", (0.5, 48.1, 7.5), (15.5, 49.1, 8.5), "metaldark", faces=("north", "south", "up", "down", "east", "west")),
           bx("ClampX", (6.75, 47.5, 6.75), (9.25, 49.5, 9.25), "metaldark"),
           bx("ArmZ", (7.5, 41, 0.5), (8.5, 42, 15.5), "metaldark", faces=("north", "south", "up", "down", "east", "west")),
           bx("ClampZ", (6.75, 40.5, 6.75), (9.25, 42.5, 9.25), "metaldark")]
    # the horns: east and west under the x arm, north and south under the z arm
    for nm, axis, sign, yc, arm_y, start in (("E", "x", 1, 45.5, 48.1, 12.5), ("W", "x", -1, 45.5, 48.1, 3.5),
                                             ("S", "z", 1, 38.5, 41, 12.5), ("N", "z", -1, 38.5, 41, 3.5)):
        els += _horn(f"Horn{nm}", axis, sign, 8.0, 0, yc, start)
        els += _driver(f"Drv{nm}", axis, sign, 8.0, yc, start)
        mid = start - 1.25 * sign
        if axis == "x":
            els.append(bx(f"Strap{nm}", (mid - 0.4, yc + 1.5, 7.6), (mid + 0.4, arm_y, 8.4), "metaldark"))
        else:
            els.append(bx(f"Strap{nm}", (7.6, yc + 1.5, mid - 0.4), (8.4, arm_y, mid + 0.4), "metaldark"))
    # the junction box on the pole's north face, its lid, two screws, and the conduit up to the arms
    els += [bx("Box", (5.5, 27, 5.0), (10.5, 33, 7), "sirenbox"),
            bx("Lid", (5.25, 33, 4.75), (10.75, 33.5, 7), "sirenbox"),
            bx("Screw1", (6.0, 31.75, 4.8), (6.5, 32.25, 5.0), "metaldark", faces=("north", "east", "west", "up", "down")),
            bx("Screw2", (9.5, 27.75, 4.8), (10.0, 28.25, 5.0), "metaldark", faces=("north", "east", "west", "up", "down")),
            bx("Conduit", (7.65, 33.5, 6.2), (8.35, 40.5, 6.9), "metaldark"),
            bx("Gland", (7.4, 33.5, 5.95), (8.6, 34.2, 7.0), "metaldark")]
    return els


def siren_tex_d4():
    """(D4) The siren's enamel (a warm sage cream, as Level 94's whites are warm, D3), its dark throat, and the junction
    box's grey-green paint; all painted metal, a little grimy."""
    horn = M.painted_metal(seed_of("d4sirenhorn"), base=(192, 190, 166), grain=3, mottle=4, panel=False, chips=2, under=(110, 104, 92))
    M.grime(horn, 0.08, seed_of("d4sirenhorng"), cells=(8, 4), cover=0.4)
    save(horn, "sirenhorn")
    mouth = M.noise_hv((50, 48, 46), 3, seed_of("d4sirenmouth"), mottle=4)
    save(mouth, "sirenmouth")
    box = M.painted_metal(seed_of("d4sirenbox"), base=(118, 128, 112), grain=3, mottle=4, panel=True, chips=2, under=(90, 88, 84))
    M.grime(box, 0.1, seed_of("d4sirenboxg"), cells=(8, 4), cover=0.4)
    save(box, "sirenbox")


def icebox_b13():
    """The icebox (B13): a white enamel cabinet on a dark plinth with a rounded top, two doors standing proud, each
    with a chrome lever latch and two hinges, and a little chrome badge."""
    els = [bx("Plinth", (2.5, 0, 4.5), (13.5, 1.5, 14.5), "metaldark"),
           bx("Body", (2, 1.5, 4), (14, 25.5, 15), "iceboxenamel"),
           bx("Top", (2.25, 25.5, 4.25), (13.75, 26.25, 14.75), "iceboxenamel"),
           bx("DoorU", (2.5, 15.5, 3.4), (13.5, 25, 4), "iceboxdoor", faces=("north", "east", "west", "up", "down"), full=True),
           bx("DoorL", (2.5, 2.25, 3.4), (13.5, 14.75, 4), "iceboxdoor", faces=("north", "east", "west", "up", "down"), full=True),
           bx("Badge", (6.5, 15.0, 3.6), (9.5, 15.5, 4), "chrome")]
    for nm, y in (("U", 20.25), ("L", 11.0)):
        els += [bx(f"Latch{nm}", (11.0, y - 0.5, 2.4), (12.75, y + 0.5, 3.4), "chrome"),
                bx(f"LatchGrip{nm}", (11.75, y - 2.25, 2.0), (12.75, y + 0.5, 2.6), "chrome")]
        lo, hi = (16.25, 24.0) if nm == "U" else (3.0, 14.0)
        els += [bx(f"Hinge{nm}1", (2.2, lo, 3.6), (3.0, lo + 1.25, 4), "chrome"), bx(f"Hinge{nm}2", (2.2, hi - 1.25, 3.6), (3.0, hi, 4), "chrome")]
    return els


def radio_b13():
    """The radio cabinet (B13): a walnut cabinet on four short tapered legs, its top overhanging, a speaker grille of
    walnut bars over grille cloth, a lit dial behind glass, and two knobs."""
    els = [bx("Body", (1.5, 2, 5.5), (14.5, 14.5, 14), "radiowalnut"),
           bx("Top", (1, 14.5, 5), (15, 15.25, 14.5), "radiowalnut"),
           bx("Cloth", (3, 3.5, 5.4), (13, 9.5, 5.5), "radiocloth", faces=("north",))]
    for i, x in enumerate((4.5, 6.5, 8.5, 10.5)):
        els.append(bx(f"Bar{i}", (x, 3.5, 4.9), (x + 1, 9.5, 5.5), "radiowalnut"))
    els += [bx("GrilleTop", (2.5, 9.5, 4.9), (13.5, 10.25, 5.5), "radiowalnut"),
            bx("GrilleBot", (2.5, 2.75, 4.9), (13.5, 3.5, 5.5), "radiowalnut"),
            bx("GrilleL", (2.5, 3.5, 4.9), (3, 9.5, 5.5), "radiowalnut"), bx("GrilleR", (13, 3.5, 4.9), (13.5, 9.5, 5.5), "radiowalnut"),
            bx("Dial", (4, 11, 5.45), (10, 13.5, 5.5), "radiodial", faces=("north",), full=True),
            bx("DialRim", (3.5, 10.5, 5.2), (10.5, 11, 5.5), "brass"), bx("DialRim2", (3.5, 13.5, 5.2), (10.5, 14, 5.5), "brass")]
    for i, x in enumerate((11.5, 13.0)):
        els += MK.knob(f"Knob{i}", x, 12.25, 5.5, r=0.6, depth=1.2, tex="bakelite")
    for i, (x, z) in enumerate(((2.5, 6.5), (13.5, 6.5), (2.5, 13), (13.5, 13))):
        els += MK.leg(f"Leg{i}", x, z, 0, 2, t=1.0, tex="radiowalnut", taper=0.3)
    return els


def phone_b13():
    """The telephone table (B13): a top with a lip on four tapered legs and a shelf, and on it a bakelite telephone
    with a sloped front, its dial a ring of geometry over the printed dial, and the handset in its cradle."""
    els = [bx("Table", (3, 10, 3), (13, 11, 13), "tvwood"), bx("Lip", (3.25, 9.5, 3.25), (12.75, 10, 12.75), "tvwood"),
           bx("Shelf", (4, 3, 4), (12, 3.5, 12), "tvwood")]
    for i, (x, z) in enumerate(((4, 4), (12, 4), (4, 12), (12, 12))):
        els += MK.leg(f"Leg{i}", x, z, 0, 9.5, t=1.0, tex="tvwood", taper=0.3)
    els += [bx("Base", (5, 11, 5.5), (11, 12.5, 11), "bakelite"), bx("Upper", (5.5, 12.5, 6.5), (10.5, 13.75, 10.75), "bakelite"),
            bx("Dial", (6.25, 13.75, 7), (9.75, 13.8, 10.25), "phonedial", faces=("up",), full=True),
            bx("Cradle1", (5.5, 13.75, 9.75), (6.5, 14.5, 10.75), "bakelite"), bx("Cradle2", (9.5, 13.75, 9.75), (10.5, 14.5, 10.75), "bakelite"),
            bx("Handset", (4.75, 14.5, 9.75), (11.25, 15.25, 10.75), "bakelite"),
            bx("Ear", (4.25, 14.25, 9.5), (5.75, 15.75, 11), "bakelite"), bx("Mouth", (10.25, 14.25, 9.5), (11.75, 15.75, 11), "bakelite")]
    for i in range(8):  # the finger wheel's ring
        a = 45 * i
        els.append(bx(f"Ring{i}", (7.6, 13.8, 7.0), (8.4, 14.05, 7.4), "chrome", rot=(0, a, 0), origin=(8, 13.9, 8.625)))
    return els


def fountain_b13():
    """The town fountain (B13): the rim a cast-stone wall under a lighter cap course; the spout a moulded plinth, an
    octagonal shaft, a bowl with a rim round Almond Water, and a finial for the jet."""
    rim = [bx("Rim", (0, 0, 0), (16, 5.5, 16), "fountainstone"), bx("Cap", (0, 5.5, 0), (16, 7, 16), "fountaincap")]
    sp = [bx("Plinth", (4, 0, 4), (12, 1.5, 12), "fountaincap"), bx("Plinth2", (4.75, 1.5, 4.75), (11.25, 2.5, 11.25), "fountainstone")]
    sp += cyl("Shaft", 8, 8, 2.4, 2.5, 12.5, "fountainstone")
    sp += [bx("Collar", (5, 12.5, 5), (11, 13.5, 11), "fountaincap"), bx("Under", (3.5, 13.5, 3.5), (12.5, 14.25, 12.5), "fountainstone"),
           bx("Floor", (2, 14.25, 2), (14, 15.25, 14), "fountainstone"),
           bx("WallN", (2, 15.25, 2), (14, 17, 3), "fountaincap"), bx("WallS", (2, 15.25, 13), (14, 17, 14), "fountaincap"),
           bx("WallW", (2, 15.25, 3), (3, 17, 13), "fountaincap"), bx("WallE", (13, 15.25, 3), (14, 17, 13), "fountaincap"),
           bx("Water", (3, 16.25, 3), (13, 16.3, 13), "fountainwater", faces=("up",)),
           bx("Finial", (7, 16.3, 7), (9, 18.5, 9), "fountaincap"), bx("Jet", (7.5, 18.5, 7.5), (8.5, 21, 8.5), "fountaincap")]
    return rim, sp


def towerleg_b13():
    """A water tower's leg (B13): a painted steel post with a flange at its foot and a band at the brace, and the
    brace as a channel with a lit flange."""
    return [bx("Foot", (5.5, 0, 5.5), (10.5, 1, 10.5), "towersteel"), bx("Leg", (6.25, 0, 6.25), (9.75, 16, 9.75), "towersteel"),
            bx("Band", (6, 6.5, 6), (10, 8.5, 10), "towersteel"),
            bx("Brace", (0, 7, 7.5), (16, 8, 8.5), "towersteel"), bx("BraceLip", (0, 8, 7.25), (16, 8.25, 8.75), "towersteel")]


# ======================= Graphics pass D3: the water tower =======================
# The water tower of the pictures (Wikidot's "94 CC 1", Miraheze's Level-94.jpg): a white municipal tank high on four
# straight legs on a hilltop, a squat round tank with a rounded bottom and a low cone of a roof, a catwalk round its
# waist, the tank plain white as in the Wikidot picture (no lettering: Miraheze's "Sikeston" water tower is the castle,
# and is kept for it). It is one model over the old tower's five by five tiles and fourteen levels, cut into one block per tile and
# level: `watertowerframe-x<i>z<j>y<level>`, a new code beside `watertower` (which stays, for the towers already
# standing in worlds). The world generator places it where the old tower's legs, tank and roof went
# (WorldGenerator.Motion.cs, WaterTowerFrameBlock); the tap at the foot of the riser is still `watertower-tap`.
# Reverting: drop tower_d3_blocks() from blocks() and the generator falls back to the old tower by itself.

import json as _json  # noqa: E402
import shutil  # noqa: E402

import preview_shapes as PS  # noqa: E402
from detail_kit import tpath  # noqa: E402

TW_C = 40.0          # the tower's axis, in its own units (16 to a block; its tiles run 0..80 in x and z)
TW_LEVELS = 14       # levels above the ground, as the old tower
TW_R = 35.0          # the tank's shell (outer face)
TW_DECK = (34.5, 42.0)
TW_RAIL = 41.25
TW_LEGS = ((12.0, 12.0), (68.0, 12.0), (12.0, 68.0), (68.0, 68.0))
TW_SIDE = 2 * math.tan(math.radians(11.25))  # a sixteen-sided ring's side, over its apothem
TW_SHELL_Y = (150.0, 182.0)  # the shell's foot (on the catwalk) and top (under the roof's eave)
# (review round 1: a neutral white tank read grey beside the ivory legs and the cream houses; everything is one warm
# white now, and the rust is runs only, no speckle at the rivets)
TW_WHITE = (236, 233, 222)


def tower_d3_textures():
    """The tower's paint: white riveted plate on the tank (three versions, one with rust runs from its rivets, one with
    a faint weep), white painted steel on the legs and the catwalk, rust and dirt
    at the legs' feet, a seamed roof, a bar grating on the catwalk, concrete footings and a red beacon."""
    def shell(v):
        img = M.riveted_plate(seed_of("d3shell"), base=(236, 236, 232), grain=2, mottle=4, pitch=4, layout="edges")
        if v == 2:
            M.drips(img, 2, seed_of("d3shelld"), color=(150, 92, 54), length=(10, 18), strength=0.55, start=29)
            M.drips(img, 2, seed_of("d3shelld2"), color=(142, 88, 52), length=(6, 12), strength=0.45, start=5)
        elif v == 3:
            M.drips(img, 1, seed_of("d3shellw"), color=(156, 112, 76), length=(7, 13), strength=0.3, start=29)
            M.grime(img, 0.05, seed_of("d3shellg"), cells=(8, 4), bias="bottom", cover=0.4)
        return T.match_rgb(img, TW_WHITE, key="d3shell")
    for v in (1, 2, 3):
        save(shell(v), "towershell" + ("" if v == 1 else f"-{v}"))

    paint = M.painted_metal(seed_of("d3paint"), base=TW_WHITE, grain=2, mottle=3, panel=False, chips=2, under=(150, 146, 140))
    M.grime(paint, 0.05, seed_of("d3paintg"), cells=(8, 4), cover=0.35)
    save(paint, "towerpaint")
    foot = paint.copy()
    M.grime(foot, 0.16, seed_of("d3footg"), cells=(8, 4, 2), cover=0.5)
    rust = M.rust(paint.copy(), 0.32, seed_of("d3footr"), color=(146, 84, 48), dark=(98, 60, 40), cells=(8, 4, 2))
    fp, rp = foot.load(), rust.load()
    # (the leg's foot shows the texture's rows 0-18: it stands from 7 to 16, laid on as the game lays a block's face)
    for y in range(S):
        t = min(1.0, max(0.0, (y - 6) / 12.0))
        for x in range(S):
            fp[x, y] = M.rgba(M.mix(fp[x, y][:3], rp[x, y][:3], t))
    M.drips(foot, 2, seed_of("d3footd"), color=(140, 86, 52), length=(5, 9), strength=0.4, start=1)
    save(foot, "towerfoot")

    # (round 1: a seam at each plate's edge broke into dashes where the cone's plates overlap; the roof is plain paint)
    roof = M.painted_metal(seed_of("d3roof"), base=(230, 227, 216), grain=2, mottle=4, panel=False, chips=1, under=(150, 150, 146))
    M.grime(roof, 0.05, seed_of("d3roofg"), cells=(8, 2), cover=0.35)
    save(roof, "towerroof")

    grate = M.painted_metal(seed_of("d3grate"), base=(228, 225, 214), grain=2, mottle=3, panel=False, chips=2, under=(140, 136, 130))
    gp = grate.load()
    for y in range(S):
        for x in range(S):
            if y % 4 == 3:
                gp[x, y] = M.rgba(M.lift(gp[x, y][:3], -46))
            elif y % 4 == 0:
                gp[x, y] = M.rgba(M.lift(gp[x, y][:3], 8))
            if x % 16 == 15 and y % 4 != 3:
                gp[x, y] = M.rgba(M.lift(gp[x, y][:3], -18))
    save(grate, "towergrate")

    footing = M.concrete(seed_of("d3footing"), base=(188, 184, 174), grain=3, mottle=5, aggregate=0.03, pores=0.01, hue=1.2)
    M.grime(footing, 0.1, seed_of("d3footingg"), cells=(8, 4), bias="bottom", cover=0.5)
    save(footing, "towerfooting")

    lamp = M.painted_metal(seed_of("d3lamp"), base=(182, 46, 40), grain=2, mottle=3, panel=False, chips=0)
    M.bevel(lamp, None, 2, 0.22)
    save(lamp, "towerlamp")


# ---- The model, in the tower's own units ----

def _tw_box(name, frm, to, tex, faces=None, solid=False):
    """An unrotated part, cut at the block edges later (each piece's texture laid on as the game would lay it on a
    block there, so it runs on unbroken from block to block)."""
    e = MK.box(name, frm, to, tex, faces=faces or MK.DIRS)
    e["_kind"], e["_solid"] = "box", solid
    return e


def _tw_octo(name, cx, cz, r, y1, y2, tex, solid=True, faces=None, cap=False):
    """A round post as a cross of two boxes; with `cap` the second is a hair shorter, so their ends never share a plane."""
    k, d = r * 0.72, (0.05 if cap else 0.0)
    return [_tw_box(name + "A", (cx - r, y1, cz - k), (cx + r, y2, cz + k), tex, faces, solid),
            _tw_box(name + "B", (cx - k, y1 + d, cz - r), (cx + k, y2 - d, cz + r), tex, faces, solid)]


def _tw_whole(e, solid=False):
    """A part that goes whole into the block its middle is in (anything turned)."""
    e["_kind"], e["_solid"] = "whole", solid
    return e


def _tw_yaw(name, frm, to, tex, theta, faces=None, solid=False, uv=None):
    """A part built north of the axis and turned `theta` degrees about it. Kept to one level, since it is not cut."""
    e = MK.box(name, frm, to, tex, faces=faces or MK.DIRS)
    if uv:
        for f, u in uv.items():
            if f in e["faces"]:
                e["faces"][f]["uv"] = [round(v, 4) for v in u]
    if theta % 360:
        e["rotationOrigin"] = [TW_C, round((frm[1] + to[1]) / 2, 4), TW_C]
        e["rotationY"] = round(theta, 4)
    return _tw_whole(e, solid)


def _tw_facet(name, theta, yo, alpha, s1, s2, thick, tex, below, solid=True):
    """A plate of a cone round the axis whose apex is at height `yo`: from `s1` to `s2` along its slope, tilted
    `alpha` degrees (positive raises its outer end) and turned `theta` about the axis. A roof's plates lie under the
    cone (their tops are the roof); a bowl's over it (their undersides are the bowl). A parent turned about the axis
    carries a child tilted about x, so each element turns about one axis only (B14)."""
    a = math.radians(alpha)
    w = TW_SIDE * s2 * math.cos(a) + 0.2
    y1, y2 = (yo - thick, yo) if below else (yo, yo + thick)
    child = MK.box(name, (TW_C - w / 2, y1, TW_C - s2), (TW_C + w / 2, y2, TW_C - s1), tex)
    child["rotationOrigin"] = [TW_C, round(yo, 4), TW_C]
    child["rotationX"] = round(alpha, 4)
    parent = {"name": name + "Yaw", "from": [0, 0, 0], "to": [0, 0, 0], "rotationOrigin": [TW_C, round(yo, 4), TW_C],
              "faces": {}, "children": [child]}
    if theta % 360:
        parent["rotationY"] = round(theta, 4)
    return _tw_whole(parent, solid)


def _tw_cone(name, yo, alpha, s_in, s_out, segs, thick, tex, below, solid=True):
    """Sixteen plates round the axis, each in `segs` lengths so no plate is longer than a block."""
    out = []
    for k in range(16):
        for s in range(segs):
            a = s_in + (s_out - s_in) * s / segs
            b = s_in + (s_out - s_in) * (s + 1) / segs
            out.append(_tw_facet(f"{name}{k}s{s}", k * 22.5, yo, alpha, a, b, thick, tex, below, solid))
    return out


def _tw_profile(name, pts, thick, tex, below, solid=True):
    """A round shape turned from a profile of (radius, height) points, each pair a ring of sixteen cone plates."""
    out = []
    for n, ((r0, y0), (r1, y1)) in enumerate(zip(pts, pts[1:])):
        a = math.atan2(y1 - y0, r1 - r0)
        yo = y0 - r0 * math.tan(a)
        segs = max(1, math.ceil((math.hypot(r1 - r0, y1 - y0) - 0.01) / 16))
        out += _tw_cone(f"{name}{n}r", yo, math.degrees(a), r0 / math.cos(a), r1 / math.cos(a), segs, thick, tex, below, solid)
    return out


def _tw_rod(name, plane, at, p0, p1, tex="towersteel", t=0.75):
    """A tension rod in a vertical plane (`plane` "z": the plane z = `at`, running along x; "x": along z), from p0 to
    p1, each an (along, y) pair; cut into straight lengths at the block edges, each lying in one block."""
    if p1[0] < p0[0]:
        p0, p1 = p1, p0
    (a0, y0), (a1, y1) = p0, p1
    ts = {0.0, 1.0}
    for k in range(1, 5):
        if (a0 - 16 * k) * (a1 - 16 * k) < 0:
            ts.add((16 * k - a0) / (a1 - a0))
    for k in range(1, TW_LEVELS):
        if (y0 - 16 * k) * (y1 - 16 * k) < 0:
            ts.add((16 * k - y0) / (y1 - y0))
    ts = sorted(ts)
    length = math.hypot(a1 - a0, y1 - y0)
    ang = math.degrees(math.atan2(y1 - y0, a1 - a0))
    out = []
    for n, (ta, tb) in enumerate(zip(ts, ts[1:])):
        if tb - ta < 1e-6:
            continue
        ln = length * (tb - ta)
        ma, my = a0 + (a1 - a0) * (ta + tb) / 2, y0 + (y1 - y0) * (ta + tb) / 2
        first, last = n == 0, tb >= 1.0
        if plane == "z":
            faces = [f for f in MK.DIRS if not (f == "west" and not first or f == "east" and not last)]
            e = MK.box(f"{name}{n}", (ma - ln / 2, my - t / 2, at - t / 2), (ma + ln / 2, my + t / 2, at + t / 2), tex, faces=faces)
            e["rotationOrigin"] = [round(ma, 4), round(my, 4), round(at, 4)]
            e["rotationZ"] = round(ang, 4)
        else:
            faces = [f for f in MK.DIRS if not (f == "north" and not first or f == "south" and not last)]
            e = MK.box(f"{name}{n}", (at - t / 2, my - t / 2, ma - ln / 2), (at + t / 2, my + t / 2, ma + ln / 2), tex, faces=faces)
            e["rotationOrigin"] = [round(at, 4), round(my, 4), round(ma, 4)]
            e["rotationX"] = round(-ang, 4)
        out.append(_tw_whole(e))
    return out


def _tw_level_spans(y1, y2):
    """(y1, y2) cut at the block levels."""
    out, y = [], y1
    while y < y2 - 1e-6:
        top = min(y2, (math.floor(y / 16 + 1e-9) + 1) * 16)
        out.append((y, top))
        y = top
    return out


def tower_d3_model():
    """The tower as one list of parts, in its own units: x and z 0..80 over its five by five tiles (north is -z, as in
    the world), y from the top of the ground (0) up through its fourteen levels."""
    els = []
    # Four legs on concrete footings, a base plate and anchor bolts, rust and dirt at the foot; a bracket under the deck
    for k, (lx, lz) in enumerate(TW_LEGS):
        els.append(_tw_box(f"Footing{k}", (lx - 4, 0, lz - 4), (lx + 4, 5.5, lz + 4), "towerfooting", solid=True))
        els.append(_tw_box(f"FootingCap{k}", (lx - 3.5, 5.5, lz - 3.5), (lx + 3.5, 6.25, lz + 3.5), "towerfooting", solid=True))
        els.append(_tw_box(f"BasePlate{k}", (lx - 3, 6.25, lz - 3), (lx + 3, 7, lz + 3), "towersteel", solid=True))
        for b, (bx_, bz_) in enumerate(((-2.25, -2.25), (2.25, -2.25), (-2.25, 2.25), (2.25, 2.25))):
            els.append(_tw_box(f"Bolt{k}{b}", (lx + bx_ - 0.4, 7, lz + bz_ - 0.4), (lx + bx_ + 0.4, 7.75, lz + bz_ + 0.4), "towersteel"))
        els += _tw_octo(f"LegFoot{k}", lx, lz, 2.5, 7, 16, "towerfoot", faces=[f for f in MK.DIRS if f != "up"])
        els += _tw_octo(f"Leg{k}", lx, lz, 2.5, 16, 146, "towerpaint", faces=[f for f in MK.DIRS if f != "down"])
        els.append(_tw_box(f"LegCap{k}", (lx - 3.25, 146, lz - 3.25), (lx + 3.25, 150, lz + 3.25), "towerpaint", solid=True))

    # Girders between the legs at two heights, and crossed tension rods in each bay with a ring where they cross
    lo, hi = TW_LEGS[0][0], TW_LEGS[1][0]  # 12, 68
    bays = ((8.0, 54.0), (56.0, 102.0), (104.0, 145.0))
    for y in (54.0, 102.0):
        els.append(_tw_box(f"GirderN{int(y)}", (lo + 2.25, y, lo - 0.75), (hi - 2.25, y + 2, lo + 0.75), "towerpaint", faces=["north", "south", "up", "down"]))
        els.append(_tw_box(f"GirderS{int(y)}", (lo + 2.25, y, hi - 0.75), (hi - 2.25, y + 2, hi + 0.75), "towerpaint", faces=["north", "south", "up", "down"]))
        els.append(_tw_box(f"GirderW{int(y)}", (lo - 0.75, y, lo + 2.25), (lo + 0.75, y + 2, hi - 2.25), "towerpaint", faces=["east", "west", "up", "down"]))
        els.append(_tw_box(f"GirderE{int(y)}", (hi - 0.75, y, lo + 2.25), (hi + 0.75, y + 2, hi - 2.25), "towerpaint", faces=["east", "west", "up", "down"]))
    a0, a1 = lo + 2.5, hi - 2.5
    for b, (y0, y1) in enumerate(bays):
        for side, plane, at in (("N", "z", lo), ("S", "z", hi), ("W", "x", lo), ("E", "x", hi)):
            # the two rods pass a little apart, front and back of the leg line, so they never share a face
            els += _tw_rod(f"Rod{side}{b}a", plane, at - 0.45, (a0, y0 + 1), (a1, y1 - 1))
            els += _tw_rod(f"Rod{side}{b}b", plane, at + 0.45, (a0, y1 - 1), (a1, y0 + 1))
            m, my = (a0 + a1) / 2, (y0 + y1) / 2
            ring = ((m - 1.2, my - 1.2, at - 1.1), (m + 1.2, my + 1.2, at + 1.1)) if plane == "z" else \
                ((at - 1.1, my - 1.2, m - 1.2), (at + 1.1, my + 1.2, m + 1.2))
            els.append(_tw_box(f"Ring{side}{b}", ring[0], ring[1], "towersteel"))

    # The riser: up from the tap (the old tap block, whose pipe stops at 14) to the bowl, flanged, a boot under the bowl
    reducer = _tw_box("RiserReducer", (TW_C - 2, 13.5, TW_C - 2), (TW_C + 2, 16, TW_C + 2), "towerpaint", faces=["north", "east", "south", "west", "down"])
    reducer["_kind"], reducer["_cell"] = "whole", (2, 2, 2)
    els.append(reducer)
    els += _tw_octo("Riser", TW_C, TW_C, 4, 16, 126, "towerpaint", cap=True)
    for n, y in enumerate((17.0, 64.0, 112.0)):
        els += _tw_octo(f"Flange{n}", TW_C, TW_C, 4.75, y, y + 1.5, "towerpaint", solid=False, cap=True)
    els += _tw_octo("Boot", TW_C, TW_C, 6, 124, 131, "towerpaint", cap=True)

    # The tank: a rounded bottom in rings of plates, a plain white shell of sixteen plates,
    # a low cone of a roof with an eave, and at its top a finial, a vent, the red beacon and a lightning rod
    # (the bottom is half an ellipse, 22 deep: flat in the middle, steep at the rim)
    els += _tw_profile("Bowl", [(0.0, 128.0), (14.0, 129.8), (24.0, 134.0), (31.0, 139.8), (TW_R, TW_SHELL_Y[0])], 1.5, "towershell", below=False)
    w = TW_SIDE * TW_R
    for k in range(16):
        th = k * 22.5
        for (y1, y2) in _tw_level_spans(*TW_SHELL_Y):
            lv = math.floor(y1 / 16 + 1e-9)
            v1, v2 = 16 - (y2 - 16 * lv), 16 - (y1 - 16 * lv)
            uv = {"north": (0, v1, 16, v2), "east": (0, v1, 1.5, v2), "west": (0, v1, 1.5, v2)}
            els.append(_tw_yaw(f"Shell{k}y{int(y1)}", (TW_C - w / 2, y1, TW_C - TW_R), (TW_C + w / 2, y2, TW_C - TW_R + 1.5),
                               "towershell", th, faces=["north", "east", "west"], solid=True, uv=uv))
    roof_a = 24.0
    eave = TW_R + 1.75
    apex = TW_SHELL_Y[1] + eave * math.tan(math.radians(roof_a))
    crown = 6.5  # a round crown plate over the middle, where sixteen plates would crowd into a star
    els += _tw_cone("Roof", apex, -roof_a, crown / math.cos(math.radians(roof_a)), eave / math.cos(math.radians(roof_a)), 3, 1.5, "towerroof", below=True)
    els += _tw_octo("Crown", TW_C, TW_C, crown + 0.5, apex - (crown + 0.5) * math.tan(math.radians(roof_a)) - 0.6, apex - 1.6, "towerroof", cap=True)
    els += _tw_octo("Finial", TW_C, TW_C, 3.25, apex - 3, apex + 1.5, "towerroof", cap=True)
    els.append(_tw_box("FinialCap", (TW_C - 2.75, apex + 1.5, TW_C - 2.75), (TW_C + 2.75, apex + 2.25, TW_C + 2.75), "towerroof", solid=True))
    els += _tw_octo("Vent", TW_C, TW_C, 1.6, apex + 2.25, apex + 5, "towerpaint", cap=True)
    els.append(_tw_box("VentCap", (TW_C - 2.6, apex + 5, TW_C - 2.6), (TW_C + 2.6, apex + 5.75, TW_C + 2.6), "towerpaint"))
    els.append(_tw_box("Beacon", (TW_C - 1.25, apex + 5.75, TW_C - 1.25), (TW_C + 1.25, apex + 8, TW_C + 1.25), "towerlamp"))
    els.append(_tw_box("BeaconCap", (TW_C - 0.75, apex + 8, TW_C - 0.75), (TW_C + 0.75, apex + 8.5, TW_C + 0.75), "towersteel"))
    els.append(_tw_box("LightningRod", (TW_C - 0.3, apex + 8.5, TW_C - 0.3), (TW_C + 0.3, apex + 14, TW_C + 0.3), "towersteel"))

    # The catwalk: a grating deck round the tank's waist, posts and two rails; joints a hair apart in height so the
    # plates' overlapping corners never share a plane
    dw = TW_SIDE * TW_DECK[1] + 0.1
    rw = TW_SIDE * (TW_RAIL + 0.4) + 0.1
    for k in range(16):
        th, h = k * 22.5, 0.08 * (k % 2)
        els.append(_tw_yaw(f"Deck{k}", (TW_C - dw / 2, 150 + h, TW_C - TW_DECK[1]), (TW_C + dw / 2, 151.5 + h, TW_C - TW_DECK[0]),
                           {"top": "towergrate", "all": "towerpaint"}, th, faces=["north", "east", "west", "up", "down"], solid=True))
        # (the posts a little thinner than the rails across the ring, so the rails stand proud of them)
        els.append(_tw_yaw(f"Post{k}", (TW_C - 0.4, 151.5, TW_C - TW_RAIL - 0.3), (TW_C + 0.4, 160.0, TW_C - TW_RAIL + 0.3), "towerpaint", th,
                           faces=["north", "east", "south", "west", "down"]))
        els.append(_tw_yaw(f"PostTop{k}", (TW_C - 0.4, 160.0, TW_C - TW_RAIL - 0.3), (TW_C + 0.4, 162.6, TW_C - TW_RAIL + 0.3), "towerpaint", th, faces=["north", "east", "south", "west"]))
        els.append(_tw_yaw(f"Rail{k}", (TW_C - rw / 2, 162.25 + h / 2, TW_C - TW_RAIL - 0.4), (TW_C + rw / 2, 163.0 + h / 2, TW_C - TW_RAIL + 0.4), "towerpaint", th))
        els.append(_tw_yaw(f"MidRail{k}", (TW_C - rw / 2, 156.5 + h / 2, TW_C - TW_RAIL - 0.35), (TW_C + rw / 2, 157.1 + h / 2, TW_C - TW_RAIL + 0.35), "towerpaint", th))

    # A ladder up the south-east leg's east side to the catwalk, its rails running on up as hand holds, held off the
    # leg by brackets; and a ladder from the catwalk up the tank's south-east side to the roof
    lx, lz = TW_LEGS[3]
    ladder_x = (lx + 9.5, lx + 10.25)
    for zr in (lz - 2.4, lz + 1.65):
        els.append(_tw_box(f"LadderRail{int(zr * 10)}", (ladder_x[0], 9, zr), (ladder_x[1], 166, zr + 0.75), "towerpaint"))
        for n, y in enumerate((24.0, 64.0, 104.0, 140.0)):
            els.append(_tw_box(f"LadderBracket{int(zr * 10)}_{n}", (lx + 1.75, y, zr + 0.1), (ladder_x[0], y + 0.75, zr + 0.65), "towerpaint",
                               faces=["north", "south", "up", "down"]))
    for n, y in enumerate(range(12, 165, 4)):
        els.append(_tw_box(f"Rung{n}", (ladder_x[0] + 0.1, y, lz - 1.65), (ladder_x[1] - 0.1, y + 0.6, lz + 1.65), "towersteel",
                           faces=["east", "west", "up", "down"]))
    th = 225.0
    sz = TW_C - TW_R - 1.6
    for (y1, y2) in _tw_level_spans(151.5, 184.5):
        for side, x0 in (("L", TW_C - 2.4), ("R", TW_C + 1.65)):
            els.append(_tw_yaw(f"TankLadder{side}{int(y1)}", (x0, y1, sz - 0.75), (x0 + 0.75, y2, sz), "towerpaint", th,
                               faces=["north", "east", "south", "west"] + (["up"] if y2 == 184.5 else [])))
    for n, y in enumerate(range(154, 183, 4)):
        els.append(_tw_yaw(f"TankRung{n}", (TW_C - 1.65, y, sz - 0.65), (TW_C + 1.65, y + 0.6, sz - 0.1), "towersteel", th,
                           faces=["north", "south", "up", "down"]))
    for n, y in enumerate((158.0, 172.0)):
        for side, x0 in (("L", TW_C - 2.4), ("R", TW_C + 1.65)):
            els.append(_tw_yaw(f"TankClip{side}{n}", (x0, y, sz), (x0 + 0.75, y + 0.75, TW_C - TW_R), "towersteel", th,
                               faces=["east", "west", "up", "down"]))
    return els


# ---- Cutting it into blocks ----

def _tw_world_box(e):
    """The axis-aligned bounds of a part (and its children) as the game places them, in the tower's units."""
    pts = []
    for el, chain in PS.walk([e]):
        if not el.get("faces") and el.get("children"):
            continue
        f0, t0 = el["from"], el["to"]
        for cx in (f0[0], t0[0]):
            for cy in (f0[1], t0[1]):
                for cz in (f0[2], t0[2]):
                    pts.append(PS.place((cx, cy, cz), el, chain))
    return [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]


def _tw_local(e, ox, oy, oz):
    """A part moved into a block's own units (a parent's `from` stays at the block's corner, so its children, placed
    from there, move with it)."""
    e = _json.loads(_json.dumps({k: v for k, v in e.items() if not k.startswith("_")}))

    def mv(p):
        return [round(p[0] - ox, 4), round(p[1] - oy, 4), round(p[2] - oz, 4)]
    if "rotationOrigin" in e:
        e["rotationOrigin"] = mv(e["rotationOrigin"])
    if e.get("children"):
        e["children"] = [_tw_local(c, ox, oy, oz) for c in e["children"]]
    else:
        e["from"], e["to"] = mv(e["from"]), mv(e["to"])
    return e


def _tw_auto_uv(face, f0, t0):
    """The UV the game lays on an unturned face (its extent in the block), so a part's pieces join across blocks."""
    (x0, y0, z0), (x1, y1, z1) = f0, t0
    return [round(v, 4) for v in {"north": (16 - x1, 16 - y1, 16 - x0, 16 - y0), "south": (x0, 16 - y1, x1, 16 - y0),
                                  "west": (z0, 16 - y1, z1, 16 - y0), "east": (16 - z1, 16 - y1, 16 - z0, 16 - y0),
                                  "up": (x0, z0, x1, z1), "down": (x0, 16 - z1, x1, 16 - z0)}[face]]


def tower_d3_cells(els):
    """{(i, j, level): [(element in the block's units, solid)]}: unrotated parts cut at the block edges, the rest whole
    in the block their middle is in."""
    cells = {}
    for e in els:
        if e["_kind"] == "box":
            (x1, y1, z1), (x2, y2, z2) = e["from"], e["to"]
            for i in range(max(0, math.floor(x1 / 16)), min(5, math.ceil(x2 / 16))):
                for lv in range(max(0, math.floor(y1 / 16)), min(TW_LEVELS, math.ceil(y2 / 16))):
                    for j in range(max(0, math.floor(z1 / 16)), min(5, math.ceil(z2 / 16))):
                        lo = [max(x1, 16 * i), max(y1, 16 * lv), max(z1, 16 * j)]
                        hi = [min(x2, 16 * (i + 1)), min(y2, 16 * (lv + 1)), min(z2, 16 * (j + 1))]
                        if any(hi[n] - lo[n] < 1e-6 for n in range(3)):
                            continue
                        cut = {"west": lo[0] > x1, "east": hi[0] < x2, "down": lo[1] > y1, "up": hi[1] < y2,
                               "north": lo[2] > z1, "south": hi[2] < z2}
                        p = _json.loads(_json.dumps({k: v for k, v in e.items() if not k.startswith("_")}))
                        p["from"], p["to"] = [round(v, 4) for v in lo], [round(v, 4) for v in hi]
                        p["faces"] = {f: v for f, v in p["faces"].items() if not cut[f]}
                        if not p["faces"]:
                            continue
                        p = _tw_local(p, 16 * i, 16 * lv, 16 * j)
                        for f, v in p["faces"].items():
                            v["uv"] = _tw_auto_uv(f, p["from"], p["to"])
                        cells.setdefault((i, j, lv + 1), []).append((p, e["_solid"]))
        else:
            if "_cell" in e:
                i, j, c = e["_cell"]
            else:
                lo, hi = _tw_world_box(e)
                mx, my, mz = ((lo[n] + hi[n]) / 2 for n in range(3))
                i, j, c = min(4, max(0, int(mx // 16))), min(4, max(0, int(mz // 16))), min(TW_LEVELS, max(1, int(my // 16) + 1))
            cells.setdefault((i, j, c), []).append((_tw_local(e, 16 * i, 16 * (c - 1), 16 * j), e["_solid"]))
    return cells


def _tw_bounds(items):
    """The block-unit bounds (0..1) of what is in a block, clipped to it."""
    pts = []
    for e, _ in items:
        lo, hi = _tw_world_box(e)
        pts.append((lo, hi))
    if not pts:
        return None
    lo = [max(0.0, min(p[0][n] for p in pts)) / 16 for n in range(3)]
    hi = [min(16.0, max(p[1][n] for p in pts)) / 16 for n in range(3)]
    if any(hi[n] - lo[n] < 0.02 for n in range(3)):
        return None
    return {"x1": round(lo[0], 3), "y1": round(lo[1], 3), "z1": round(lo[2], 3), "x2": round(hi[0], 3), "y2": round(hi[1], 3), "z2": round(hi[2], 3)}


TW_SHAPES = os.path.join(ASSETS, "shapes", "block", "detail", "watertowerframe")


def tower_d3_blocks():
    """The rebuilt tower's blocks: one variant per tile and level that has something in it, each its own shape."""
    cells = tower_d3_cells(tower_d3_model())
    assert (2, 2, 1) not in cells, "the tap's block is the old watertower-tap"
    shutil.rmtree(TW_SHAPES, ignore_errors=True)
    states, shapes, coll, sel = [], {}, {}, {}
    for (i, j, c) in sorted(cells, key=lambda k: (k[2], k[1], k[0])):
        st = f"x{i}z{j}y{c:02d}"
        items = cells[(i, j, c)]
        els = [e for e, _ in items]
        keys = sorted({f["texture"][1:] for el, _ in PS.walk(els) for f in el.get("faces", {}).values()})
        write_json(os.path.join(TW_SHAPES, st + ".json"),
                   {"textureWidth": 16, "textureHeight": 16, "textures": {k: tpath(k) for k in keys}, "elements": els})
        states.append(st)
        shapes[f"*-{st}"] = {"base": f"block/detail/watertowerframe/{st}"}
        sel[f"*-{st}"] = _tw_bounds(items) or {"x1": 0.4, "y1": 0.4, "z1": 0.4, "x2": 0.6, "y2": 0.6, "z2": 0.6}
        coll[f"*-{st}"] = _tw_bounds([it for it in items if it[1]])
    block("watertowerframe", {
        "variantgroups": [{"code": "part", "states": states}],
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": shapes,
        "textures": {"towershell": tex_entry("towershell", alts("towershell", 3))},
        "randomizeAxes": "xyz",
        "sideopaque": {"all": False}, "sidesolid": {"all": False}, "lightAbsorption": 0,
        "collisionboxByType": coll, "selectionboxByType": sel,
        "resistance": 4, "drops": [], "sounds": METAL,
    }, "Level 94 (D3): the water tower of the pictures, one block per tile and level of its five by five tiles; "
       "generated by tools/gen_motion.py (tower_d3_*)")
    name("watertowerframe-*", "Water Tower")
    return len(states)
