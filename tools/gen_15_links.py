"""Level 15, "Futuristic Halls" (experimental): the blocks of its links (docs/design/experimental-levels/LINKS.md), and their
textures. The level's other blocks are tools/gen_15.py's; this uses its helpers and palette and writes only its own files.

    l15-walldoor    the small reinforced door in the immense white wall across Level 10's fields (lower, upper; four sides):
                    used, it takes you into Level 15, one way (threshold "l15-walldoor")
    l15-sealeddoor  the same door in the walls of Level 15's main halls, which does not open ("l15-sealed")
    l15-l3door      a steel door in a wall of Level 3, painted, a HIGH VOLTAGE label, cold white light under it ("l15-l3door")
    l15-escapelive  the ESCAPE panel that works: its button lit (four sides; Regions.L15System rolls up its room's gateway)
    l15-gatewayshut the locked gateway, its shutter down (lower with the hazard band, upper) ("l15-gatewayshut": locked)
    l15-gatewayopen the gateway rolled up: dark, a warm glow low down, no collision ("l15-gateway": Level 3)
    l15-cityglass   thick glass with a street's orange light behind it, as if a city lay past the machine room (broken: Level 11)

Run from the repo root:  python tools/gen_15_links.py   (under tools/locked.sh run)
"""
import math
import os
import random

import matlib as M
import gen_15 as G
from gen_15 import S, SIDES, METAL, GLASS, WHITE, INK, rect, blend, save, tex, write_json

BLOCKS = G.BLOCKS


# ======================================================================== Textures

def reinforced(part):
    """A small reinforced door: grey steel in a riveted frame, the lower half with a heavy lever handle and a kick plate,
    the upper a narrow wired window onto black."""
    img = M.brushed_metal(seed=15500, base=(148, 154, 160), direction="v", streak=5, sheen=7)
    # The frame: a raised steel band round three sides (top only on the upper half), rivets along it
    for x in range(S):
        for y in range(S):
            if x < 3 or x > 28 or (part == "upper" and y < 3):
                blend(img, x, y, (186, 192, 198), 0.8)
    M.emboss_lines(img, xs=(3, 28), raised=True, strength=0.25)
    if part == "upper":
        M.emboss_lines(img, ys=(3,), raised=True, strength=0.25)
    for y in range(5 if part == "upper" else 2, S, 6):
        for x in (1, 30):
            M.screw(img, x, y, slot=False)
    if part == "lower":
        # A kick plate, a heavy lever and its lock
        rect(img, 4, 24, 27, 30, (118, 122, 128))
        M.emboss_lines(img, ys=(24,), raised=True, strength=0.25)
        for x in range(6, 27, 4):
            M.screw(img, x, 27, slot=False)
        rect(img, 20, 6, 22, 9, (60, 64, 70))
        rect(img, 12, 7, 22, 8, (196, 200, 206))
        M.bevel(img, (12, 7, 23, 9), strength=0.25)
        rect(img, 20, 12, 22, 14, (40, 42, 46))
        M.grime(img, 0.12, seed=15501, bias="bottom", color=(70, 72, 74))
    else:
        # A narrow window of wired glass, black behind it
        rect(img, 11, 5, 20, 21, (90, 96, 104))
        M.bevel(img, (11, 5, 21, 22), strength=0.25)
        rect(img, 13, 7, 18, 19, (12, 14, 18))
        for y in range(7, 20, 3):
            for x in range(13, 19):
                blend(img, x, y, (70, 76, 84), 0.5)
        for x in range(13, 19, 3):
            for y in range(7, 20):
                blend(img, x, y, (70, 76, 84), 0.5)
        blend(img, 14, 8, (120, 130, 140), 0.6)
        # A stencilled number above it
        G.text(img, 10, 25, "15", INK)
    return img


def l3door(part):
    """Level 3's kind of door: steel painted a dull green-grey, chipped, a vertical pull handle, a yellow HIGH VOLTAGE label;
    under it a thin line of cold white light, cleaner than anything in Level 3."""
    img = M.painted_metal(seed=15510, base=(92, 104, 96), grain=3, mottle=6, panel=True, chips=6, under=(70, 62, 54))
    M.emboss_lines(img, xs=(2, 29), strength=0.2)
    if part == "lower":
        rect(img, 23, 0, 25, 12, (150, 152, 150))
        M.bevel(img, (23, 0, 26, 13), strength=0.25)
        M.rust(img, 0.18, seed=15511)
        M.grime(img, 0.2, seed=15512, bias="bottom", color=(58, 50, 40))
        # The light under it
        for x in range(S):
            for y in (29, 30, 31):
                blend(img, x, y, (238, 246, 255) if y == 31 else (190, 210, 228), 1.0 if y == 31 else 0.55 - 0.15 * (30 - y))
    else:
        # HIGH VOLTAGE: a yellow triangle with a bolt
        for y in range(8, 22):
            half = (y - 8) * 0.75
            for x in range(int(15.5 - half), int(15.5 + half) + 1):
                blend(img, x, y, (226, 186, 40), 1.0)
        for (x, y) in ((16, 11), (15, 12), (15, 13), (14, 14), (15, 14), (16, 14), (16, 15), (15, 16), (15, 17), (14, 18)):
            blend(img, x, y, (20, 18, 16), 1.0)
        rect(img, 7, 23, 24, 31, (226, 186, 40))
        G.text(img, 10, 24, "HV", (20, 18, 16))
        M.rust(img, 0.1, seed=15513)
    return img


def escape_live():
    """The ESCAPE panel that works: the panel of gen_15's escape deco, its button lit and a green lamp beside it."""
    img = G.deco_base()
    rect(img, 4, 4, 27, 27, (170, 176, 182))
    M.bevel(img, (4, 4, 28, 28), strength=0.22)
    G.text(img, 6, 6, "ESCAPE", INK, G.SMALL)
    for y in range(12, 23):
        for x in range(9, 23):
            d = math.hypot(x - 15.5, y - 17)
            if d < 5.6:
                blend(img, x, y, (255, 74, 58) if d < 4.2 else (150, 34, 28), 1.0)
                if d < 2.6:
                    blend(img, x, y, (255, 196, 180), 0.6)
    for y in (24, 25):
        for x in (24, 25):
            blend(img, x, y, (110, 255, 140), 1.0)
    return img


def gateway_slats():
    """The gateway's shutter above its hazard band: steel slats (gen_15's gate without its stripes)."""
    img = M.brushed_metal(seed=15301, base=(150, 156, 162), direction="h")
    M.emboss_lines(img, ys=(4, 8, 12, 16, 20, 24, 28), raised=True, strength=0.2)
    return img


def gateway_open(part):
    """The gateway rolled up: nothing behind it but dark, and low down a warm glow, as of hot wiring a long way off."""
    rng = random.Random(15520 if part == "lower" else 15521)
    img = M.new((S, S), (6, 6, 8))
    px = img.load()
    for y in range(S):
        for x in range(S):
            h = (S - 1 - y) / (S - 1) if part == "lower" else 0.0  # 1 at the foot of the lower block
            glow = max(0.0, 1.0 - h) ** 3 if part == "lower" else 0.0
            n = rng.uniform(-3, 3)
            px[x, y] = (M.clamp(8 + 150 * glow + n), M.clamp(7 + 72 * glow + n), M.clamp(9 + 18 * glow + n), 255)
    return img


def city_glass():
    """Thick glass with a street's light behind it: warm orange, the blur of lit windows far off, a sodium lamp's bloom."""
    img = M.glass(seed=15530, base=(214, 150, 86), alpha=120, streaks=2, dust=0.01)
    px = img.load()
    rng = random.Random(15531)
    for y in range(S):
        for x in range(S):
            r, g, b, a = px[x, y]
            d = math.hypot(x - 22, y - 9)
            bloom = max(0.0, 1 - d / 13)
            px[x, y] = (M.clamp(r + 40 * bloom), M.clamp(g + 30 * bloom), M.clamp(b + 6 * bloom), M.clamp(a + 60 * bloom))
    # Distant towers, darker, and their lit windows
    for (x0, x1, top) in ((2, 7, 14), (9, 13, 19), (15, 18, 11), (25, 30, 16)):
        for y in range(top, S):
            for x in range(x0, x1 + 1):
                r, g, b, a = px[x, y]
                px[x, y] = (M.clamp(r * 0.55), M.clamp(g * 0.5), M.clamp(b * 0.55), M.clamp(a + 50))
        for _ in range((x1 - x0) * (S - top) // 9):
            x, y = rng.randint(x0, x1), rng.randint(top + 1, S - 1)
            px[x, y] = (255, 214, 140, 230)
    return img


def textures():
    for part in ("lower", "upper"):
        save(reinforced(part), "door-reinforced" + part)
        save(l3door(part), "door-l3" + part)
        save(gateway_open(part), "gateway-open" + part)
    save(gateway_slats(), "gateway-slats")
    save(escape_live(), "deco-escapelive")
    save(city_glass(), "glass-city")


# ======================================================================== Block types

def door_block(code, texture, kind, comment, other="wall-panel"):
    tbt = {}
    for part in ("lower", "upper"):
        for s in SIDES:
            tbt[f"*-{part}-{s}"] = {"all": tex(other), s: tex(texture + part)}
    data = {"code": code, "variantgroups": [{"code": "part", "states": ["lower", "upper"]}, {"code": "side", "states": SIDES}],
            "texturesByType": tbt, "creativeinventory": {"general": ["*-lower-north"], "backrooms": ["*-lower-north"]},
            "blockmaterial": "Metal", "drawtype": "cube", "lightAbsorption": 99, "resistance": 10, "drops": [], "sounds": METAL,
            "behaviors": [{"name": "BackroomsThreshold", "properties": {"kind": kind}}]}
    return data, comment


def blocktypes():
    for code, texture, kind, comment, other in (
        ("l15-walldoor", "door-reinforced", "l15-walldoor",
         "Level 15's link: the small reinforced door in the immense white wall across Level 10's fields (lower, upper; the side its face "
         "is toward). Used: into Level 15, one way", "wall-panel"),
        ("l15-sealeddoor", "door-reinforced", "l15-sealed",
         "Level 15: the reinforced door in the wall of a main hall that does not open (lower, upper; the side its face is toward); "
         "whoever comes in from outside arrives beside one", "wall-panel"),
        ("l15-l3door", "door-l3", "l15-l3door",
         "Level 15's link: a steel door in a wall of Level 3, cold white light under it (lower, upper; the side its face is toward). "
         "Used: a shock from the handle, and Level 15, one way", "steel"),
    ):
        data, c = door_block(code, texture, kind, comment, other)
        if code == "l15-l3door":
            # The light under the door: a little, cold
            data["lightHsvByType"] = {"*-lower-*": [34, 1, 7]}
            data["vertexFlagsByType"] = {"*-lower-*": {"glowLevel": 110}}
        write_json(os.path.join(BLOCKS, code + ".json"), data, c)

    tbt = {f"*-{s}": {"all": tex("wall-panel"), s: tex("deco-escapelive")} for s in SIDES}
    write_json(os.path.join(BLOCKS, "l15-escapelive.json"),
               {"code": "l15-escapelive", "variantgroups": [{"code": "side", "states": SIDES}], "texturesByType": tbt,
                "creativeinventory": {"general": ["*-north"], "backrooms": ["*-north"]}, "blockmaterial": "Stone", "drawtype": "cube",
                "lightAbsorption": 99, "lightHsv": [0, 7, 3], "vertexFlags": {"glowLevel": 80}, "resistance": 6, "drops": [], "sounds": G.STONE,
                "behaviors": [{"name": "BackroomsL15Escape", "properties": {"kind": "l15-escape"}}]},
               "Level 15's link: the ESCAPE panel that works, its button lit (the side its face is toward). Pressed, the locked gateway "
               "in its room rolls up (Regions.L15System)")

    write_json(os.path.join(BLOCKS, "l15-gatewayshut.json"),
               {"code": "l15-gatewayshut", "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
                "texturesByType": {"*-lower": {"all": tex("gate")}, "*-upper": {"all": tex("gateway-slats")}},
                "creativeinventory": {"general": ["*-lower"], "backrooms": ["*-lower"]}, "blockmaterial": "Metal", "drawtype": "cube",
                "lightAbsorption": 99, "resistance": 10, "drops": [], "sounds": METAL,
                "behaviors": [{"name": "BackroomsThreshold", "properties": {"kind": "l15-gatewayshut"}}]},
               "Level 15's link: the locked gateway in a control room's wall, its shutter down (lower with the hazard band, upper). "
               "Its ESCAPE panel rolls it up (l15-gatewayopen)")

    write_json(os.path.join(BLOCKS, "l15-gatewayopen.json"),
               {"code": "l15-gatewayopen", "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
                "texturesByType": {"*-lower": {"all": tex("gateway-openlower")}, "*-upper": {"all": tex("gateway-openupper")}},
                "creativeinventory": {"general": ["*-lower"], "backrooms": ["*-lower"]}, "blockmaterial": "Metal", "drawtype": "cube",
                "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
                "lightAbsorption": 0, "lightHsvByType": {"*-lower": [6, 6, 6], "*": [6, 6, 2]},
                "vertexFlagsByType": {"*-lower": {"glowLevel": 60}}, "resistance": 10, "drops": [], "sounds": METAL,
                "behaviors": [{"name": "BackroomsThreshold", "properties": {"kind": "l15-gateway"}}]},
               "Level 15's link: the gateway rolled up, dark, a warm glow low down (lower, upper); no collision: walk into it, one way, "
               "to Level 3")

    write_json(os.path.join(BLOCKS, "l15-cityglass.json"),
               {"code": "l15-cityglass", "creativeinventory": {"general": ["*"], "backrooms": ["*"]}, "blockmaterial": "Glass",
                "drawtype": "cube", "textures": {"all": tex("glass-city")}, "renderpass": "Transparent", "sideopaque": {"all": False},
                "lightAbsorption": 1, "lightHsv": [5, 6, 5], "vertexFlags": {"glowLevel": 40}, "resistance": 4,
                "drops": [{"type": "item", "code": "glassshard", "quantity": {"avg": 2, "var": 1}}], "sounds": GLASS},
               "Level 15's link: thick glass with a street's orange light behind it. Broken, it takes whoever broke it through, one way, "
               "to Level 11 (Regions.L15System)")


def main():
    textures()
    blocktypes()
    print("Level 15 links: textures in", os.path.relpath(G.TEX, G.ROOT), "; blocktypes in", os.path.relpath(BLOCKS, G.ROOT))


if __name__ == "__main__":
    main()
