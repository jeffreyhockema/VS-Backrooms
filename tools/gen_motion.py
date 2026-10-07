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

from detail_kit import ASSETS, CLOTH, GLASS, LANG, METAL, SIDES, STONE, WOOD, ROTATE, block, bx, cube, cyl, name, prop, shape, write_json
from detail_textures import S, noise, rgb, save, text
from gen_deep import TRANSFORMS, door_block, drops, threshold
from gen_detail import cube_block
from detail_kit import T, seed_of


def grain(img, amount, key):
    """The grain of something made by hand: per-pixel noise, and a few thumbprint swirls."""
    rng = random.Random(seed_of(key))
    px = img.load()
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            n = rng.uniform(-amount, amount)
            px[x, y] = (max(0, min(255, int(r + n))), max(0, min(255, int(g + n))), max(0, min(255, int(b + n))), a)
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
        save(grain(img, 6, "turf" + kind), f"clayturf-{kind}")
        side = flat(c)
        d = ImageDraw.Draw(side)
        for x in range(S):
            d.line([x, S - 3 - (x * 7 % 3), x, S], fill=(168, 104, 64, 255))
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

    # The 1950s: an icebox, a radio cabinet, a telephone
    img = grain(flat((238, 232, 214)), 3, "icebox")
    d = ImageDraw.Draw(img)
    d.line([0, 15, S, 15], fill=(196, 188, 170, 255))
    d.rectangle([24, 5, 26, 11], fill=(200, 206, 210, 255))
    d.rectangle([24, 19, 26, 25], fill=(200, 206, 210, 255))
    save(img, "icebox-front")
    img = grain(flat((110, 70, 40)), 4, "radiocab")
    d = ImageDraw.Draw(img)
    d.rectangle([4, 4, S - 5, 14], fill=(200, 176, 120, 255))
    for x in range(6, S - 6, 3):
        d.line([x, 5, x, 13], fill=(150, 120, 80, 255))
    d.ellipse([7, 18, 12, 23], fill=(220, 200, 150, 255))
    d.ellipse([19, 18, 24, 23], fill=(220, 200, 150, 255))
    save(img, "radio-front")

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


def blocks():
    # The ground
    for kind in ("light", "dark"):
        block(f"clayturf-{kind}", {
            "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
            "textures": {"up": {"base": f"block/detail/clayturf-{kind}"}, "down": {"base": "block/detail/claysoil"},
                         "horizontals": {"base": f"block/detail/clayturf-side-{kind}"}},
            "lightAbsorption": 99, "resistance": 1.5,
            "sounds": {"walk": "game:walk/grass", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"},
            "drops": [{"type": "block", "code": "game:soil-low-none", "quantity": {"avg": 1}}],
        }, "Level 94: clay turf, mown in stripes. Dug up, it gives a poor sort of soil")
        name(f"clayturf-{kind}", "Clay Turf")
    block("claysoil", {
        "creativeinventory": {"general": ["*"], "construction": ["*"]}, "blockmaterial": "Soil", "drawtype": "cube",
        "textures": {"all": {"base": "block/detail/claysoil"}}, "lightAbsorption": 99, "resistance": 1.5,
        "sounds": {"walk": "game:walk/sludge*", "place": "game:block/dirt", "break": "game:block/dirt", "hit": "game:block/dirt"},
        "drops": [{"type": "item", "code": "game:clay-red", "quantity": {"avg": 3, "var": 1}}],
    }, "Level 94: the modelling clay everything is made of. Dug up, it is clay for the potter's wheel")
    name("claysoil", "Modelling Clay")
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
        "textures": {"all": {"base": "block/detail/glassmountain"}}, "lightAbsorption": 0, "resistance": 4, "sounds": GLASS,
    }, "Level 94: the glass of the transparent mountain")
    name("glassmountain", "Mountain Glass")
    cube_block("castleblock", {"wall": "Castle Stone", "roof": "Castle Roof", "funwall": "Funhouse Wall", "ceiling": "Castle Ceiling", "white": "White Wall"},
               ["wall", "roof", "funwall", "ceiling", "white"],
               {"wall": "castlewall", "roof": "castleroof", "funwall": "funwall", "ceiling": "castleceiling", "white": "castlewhite"},
               comment="Level 94: the castle on the mountain")
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
        "shapeByType": {"*-leg": {"base": shape("watertower-leg", [bx("Leg", (6, 0, 6), (10, 16, 10), "towersteel"),
                                                                   bx("Brace", (0, 7, 7.5), (16, 8, 8.5), "towersteel")])},
                        "*-tap": {"base": shape("watertower-tap", [bx("Pipe", (6.5, 0, 6.5), (9.5, 14, 9.5), "towersteel"),
                                                                   bx("Spout", (7, 9, 2), (9, 11, 6.5), "brass"),
                                                                   bx("Wheel", (6, 12, 6), (10, 12.6, 10), "redmetal")])}},
        "texturesByType": {"*-tank": {"all": {"base": "block/detail/towertank"}}, "*-roof": {"all": {"base": "block/detail/towersteel"}}},
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

    # The town fountain: a stone rim, and a spout of Almond Water in the middle
    block("almondfountain", {
        "variantgroups": [{"code": "part", "states": ["rim", "spout"]}],
        "creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "json",
        "shapeByType": {"*-rim": {"base": shape("almondfountain-rim", [bx("Rim", (0, 0, 0), (16, 7, 16), "fountainstone")])},
                        "*-spout": {"base": shape("almondfountain-spout", [
                            bx("Column", (5, 0, 5), (11, 14, 11), "fountainstone"), bx("Bowl", (2, 14, 2), (14, 17, 14), "fountainstone"),
                            bx("Jet", (7, 17, 7), (9, 21, 9), "fountainstone")])}},
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
    prop("sirenpole", "Siren Pole", [
        bx("Pole", (7, 0, 7), (9, 52, 9), "wood"), bx("Base", (6, 0, 6), (10, 2, 10), "metaldark"),
        bx("Hub", (5.5, 46, 5.5), (10.5, 50, 10.5), "metaldark"),
        bx("HornN", (6, 45, -1), (10, 51, 5.5), "steel"), bx("HornS", (6, 45, 10.5), (10, 51, 17), "steel"),
        bx("HornE", (10.5, 45, 6), (17, 51, 10), "steel"), bx("HornW", (-1, 45, 6), (5.5, 51, 10), "steel"),
        bx("Cap", (6.5, 52, 6.5), (9.5, 54, 9.5), "metaldark")],
         box=(0.4, 0, 0.4, 0.6, 2, 0.6), oriented=False, material="Wood", sounds=WOOD,
         comment="A siren pole on a corner of the town, playing the same happy tune all day")
    van = [bx("Body", (1, 2.5, 8), (31, 24, 63), "milkvan", faces=("north", "up", "down", "south")),
           bx("Sides", (1, 2.5, 8), (31, 24, 63), "milkvan-side", faces=("east", "west"), full=True),
           bx("Cab", (2, 2.5, 0), (30, 18, 9), "milkvan"), bx("Windscreen", (3, 11, -0.2), (29, 17, 0), "lampglass", faces=("north",)),
           bx("Bumper", (1, 3, -0.6), (31, 6, 0), "chrome"),
           bx("WheelFL", (0, 0, 2), (3, 8, 10), "rubber"), bx("WheelFR", (29, 0, 2), (32, 8, 10), "rubber"),
           bx("WheelRL", (0, 0, 48), (3, 8, 56), "rubber"), bx("WheelRR", (29, 0, 48), (32, 8, 56), "rubber"),
           bx("LampL", (3, 8, -0.4), (7, 11, 0), "lampglass"), bx("LampR", (25, 8, -0.4), (29, 11, 0), "lampglass")]
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
    prop("oldcar", "Old Car", {c: car(f"oldcar-{c}") for c in ("black", "green", "maroon")}, box=(0, 0, 0, 1, 1.5, 1),
         material="Metal", sounds=METAL, comment="A 1930s car, parked in the middle of nowhere",
         extra={"drops": drops(("metalbracket", 2, 1), ("scrapwire", 1, 0.5), ("glassshard", 1, 0.5))})
    prop("nooutletsign", "NO OUTLET Sign", [
        bx("Pole", (7.5, 0, 7.5), (8.5, 26, 8.5), "metal"),
        bx("Sign", (2, 24, 7), (14, 34, 7.6), "nooutlet", faces=("north",), full=True),
        bx("Back", (2, 24, 7.6), (14, 34, 8), "metal", faces=("south", "east", "west", "up", "down"))],
         box=(0.42, 0, 0.42, 0.58, 2, 0.58), material="Metal", sounds=METAL, comment="A NO OUTLET sign at a road that goes on forever")

    # Inside the houses: the 1950s
    prop("icebox", "Icebox", [
        bx("Body", (2, 0, 4), (14, 26, 15), "fridgewhite", faces=("east", "west", "up", "south")),
        bx("Front", (2, 0, 4), (14, 26, 15), "icebox-front", faces=("north",), full=True)],
         box=(0.12, 0, 0.25, 0.88, 1.62, 0.94), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:cheese-cheddar-1slice", 0.8, 0.6), ("game:butter", 0.5, 0.4),
                               ("almondmilk", 0.6, 0.4), ("cannedbeans", 0.4, 0.3), ("metalbracket", 1, 0.5))})
    prop("radiocabinet", "Radio Cabinet", [
        bx("Body", (1, 0, 5), (15, 15, 14), "tvwood", faces=("east", "west", "up", "south")),
        bx("Front", (1, 0, 5), (15, 15, 14), "radio-front", faces=("north",), full=True)],
         box=(0.06, 0, 0.31, 0.94, 0.94, 0.88), material="Wood", sounds=WOOD,
         extra={"drops": drops(("game:plank-aged", 2, 1), ("scrapwire", 1.5, 0.5), ("glassshard", 0.5, 0.5))})
    prop("rotaryphone", "Telephone Table", [
        bx("Table", (3, 10, 3), (13, 11, 13), "tvwood"), bx("Leg1", (4, 0, 4), (5, 10, 5), "tvwood"), bx("Leg2", (11, 0, 4), (12, 10, 5), "tvwood"),
        bx("Leg3", (4, 0, 11), (5, 10, 12), "tvwood"), bx("Leg4", (11, 0, 11), (12, 10, 12), "tvwood"),
        bx("Phone", (5, 11, 5), (11, 14, 11), "bakelite"), bx("Dial", (6, 14, 6), (10, 14.2, 10), "phonedial", faces=("up",), full=True),
        bx("Handset", (4.5, 14, 6.5), (11.5, 15.5, 8), "bakelite")],
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


def generate():
    textures()
    blocks()
    props()
    items()
    lang()
