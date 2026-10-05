"""Details added to bring the levels closer to the lore: Level 2's doors and clutter, Level 1's cameras and traffic
signs, Level 3's plaques, Level 5's ceiling fans, Level 6's dead light switch and Level 8's seeps of Almond Water.
Called from gen_detail.py, which writes them out along with everything else (python tools/gen_detail.py).

(Level 0's red wallpaper and red lamp are wallpaper and light variants, so their textures are in gen_textures.py.)
"""
import random

from PIL import Image, ImageDraw

from detail_kit import GLASS, LANG, METAL, STONE, WOOD, Decor, block, bx, name, prop, shape, wall_family
from detail_textures import S, noise, rgb, save, text
from gen_deep import door_block, drops, threshold
from gen_detail import cube_block, plate
from detail_kit import T, seed_of


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


# ======================= Textures =======================

def textures():
    # Level 2's steel doors: grey-green paint, rust creeping up from the floor, a wired-glass slit, a stencilled number
    for part in ("lower", "upper"):
        img = noise(0x4E5A52, 5, "tunneldoor" + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x2A322C), width=2)
        if part == "lower":
            d.rectangle([4, 20, S - 5, 27], fill=rgb(0x5E6A60))                 # kick plate
            d.rectangle([22, 2, 27, 5], fill=rgb(0x9A9A92))                     # lever handle
            d.rectangle([25, 5, 27, 8], fill=rgb(0x7A7A72))
            T.blotch(img, (8, 30), 9, (120, 66, 34), 0.75, seed_of("tdr1"))     # rust
            T.blotch(img, (24, 31), 6, (96, 52, 28), 0.7, seed_of("tdr2"))
        else:
            d.rectangle([11, 6, 20, 17], fill=rgb(0x14181A))                    # wired glass, dark behind
            for k in range(11, 21, 3):
                d.line([k, 6, k, 17], fill=rgb(0x39403C))
            for k in range(6, 18, 3):
                d.line([11, k, 20, k], fill=rgb(0x39403C))
            d.rectangle([10, 5, 21, 18], outline=rgb(0x2A322C))
            text(img, "B-%02d" % 7, (4, 21, S - 4, 29), 0xC8C4B0, 6)
            rng = random.Random(seed_of("tdstreak"))
            px = img.load()
            for _ in range(5):                                                  # rust weeping from the hinges
                x = rng.choice((2, 3, 28, 29))
                for y in range(rng.randint(0, 6), rng.randint(12, 26)):
                    px[x, y] = shade((110, 62, 34), rng.uniform(0.8, 1.1))
        save(img, f"tunneldoor-{part}")

    # A dead security camera's housing, and its lens
    img = noise(0xD8D6CC, 3, "camerabody")
    T.blotch(img, (20, 24), 8, (120, 116, 100), 0.35, seed_of("camgrime"))
    save(img, "camerabody")
    img = Image.new("RGBA", (S, S), rgb(0x16181A))
    d = ImageDraw.Draw(img)
    d.ellipse([5, 5, 26, 26], fill=rgb(0x08090A), outline=rgb(0x3A3E42), width=2)
    d.ellipse([10, 9, 15, 14], fill=rgb(0x4A5560))
    save(img, "cameralens")

    # Traffic signs
    img = Image.new("RGBA", (S, S), rgb(0x141414))
    d = ImageDraw.Draw(img)
    d.rectangle([1, 9, S - 2, 22], fill=rgb(0xF2F2EC))
    d.polygon([(3, 15.5), (9, 10), (9, 13), (22, 13), (22, 18), (9, 18), (9, 21)], fill=rgb(0x141414))
    text(img, "ONE WAY", (2, 23, S - 2, 31), 0xF2F2EC, 5)
    save(img, "sign-oneway")
    img = Image.new("RGBA", (S, S), rgb(0xF2F2EC))
    d = ImageDraw.Draw(img)
    d.ellipse([2, 2, S - 3, S - 3], fill=rgb(0xC81E1E))
    d.rectangle([7, 13, S - 8, 18], fill=rgb(0xF2F2EC))
    save(img, "sign-noentry")
    img = Image.new("RGBA", (S, S), rgb(0x1E6A3A))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0xF2F2EC))
    text(img, "EXIT", (2, 3, S - 2, 15), 0xF2F2EC, 9)
    d.polygon([(5, 23), (20, 23), (20, 19), (27, 24.5), (20, 30), (20, 26), (5, 26)], fill=rgb(0xF2F2EC))
    save(img, "sign-exit")

    # A plaque beside a barred way
    img = Image.new("RGBA", (S, S), rgb(0xE6E2D4))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], outline=rgb(0x8A1A14), width=2)
    text(img, "OUT OF", (2, 4, S - 2, 13), 0x8A1A14, 6)
    text(img, "BOUNDS", (2, 12, S - 2, 21), 0x8A1A14, 6)
    text(img, "DO NOT ENTER", (2, 22, S - 2, 29), 0x202020, 4)
    for x, y in ((2, 2), (S - 4, 2), (2, S - 4), (S - 4, S - 4)):
        d.point((x + 1, y + 1), fill=rgb(0x505050))
    save(img, "plaque")

    # Wet rock with Almond Water seeping down it: a pale, faintly milky trickle and a stain where it has run for years
    img = noise(0x55504A, 9, "seeprock")
    px = img.load()
    rng = random.Random(seed_of("seep"))
    for y in range(S):
        for x in range(S):
            d0 = abs(x - (15.5 + 2.5 * (rng.random() - 0.5) + 1.5 * ((y // 6) % 2)))
            if d0 < 6:
                px[x, y] = shade(px[x, y], 0.72 + 0.04 * d0)                      # wet and dark
    for strand in (13, 16, 18):
        x = strand
        for y in range(rng.randint(0, 5), S):
            x += rng.choice((-1, 0, 0, 0, 1)) if y % 4 == 0 else 0
            if 0 <= x < S:
                px[x, y] = (214, 208, 180, 255)
                if x + 1 < S and rng.random() < 0.4:
                    px[x + 1, y] = (170, 164, 140, 255)
    T.blotch(img, (16, 29), 7, (190, 184, 150), 0.4, seed_of("seeppool"))
    save(img, "almondseep")

    # Pieces of a machine: a gear seen from above
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for k in range(8):
        import math
        a = k * math.pi / 4
        cx, cy = 15.5 + 12 * math.cos(a), 15.5 + 12 * math.sin(a)
        d.rectangle([cx - 3, cy - 3, cx + 3, cy + 3], fill=rgb(0x6E5038))
    d.ellipse([4, 4, 27, 27], fill=rgb(0x7A5A3E))
    d.ellipse([11, 11, 20, 20], fill=(0, 0, 0, 0))
    T.blotch(img, (10, 20), 6, (90, 56, 30), 0.5, seed_of("gear"))
    save(img, "gearflat")


# ======================= Blocks and props =======================

def level1():
    camera = [bx("Mount", (6.5, 10, -1.5), (9.5, 13, 0), "blackmetal"),
              bx("Arm", (7.5, 8.5, -4), (8.5, 11, -1.5), "blackmetal"),
              bx("Body", (6, 5, -10), (10, 8.5, -3), "camerabody", faces=("east", "west", "up", "down", "south")),
              bx("Lens", (6, 5, -10), (10, 8.5, -3), "cameralens", faces=("north",), full=True),
              bx("Hood", (5.5, 8.5, -11), (10.5, 9.2, -3), "camerabody")]
    for family, english, walls in (("concretecam", "Concrete Wall", {1: "concretewall"}), ("whitecam", "Painted Block Wall", {1: "whiteblock"})):
        wall_family(family, english, walls, [Decor("camera", "Security Camera", {3: camera})],
                    comment="A security camera high on the wall. It has not worked in a long time, if it ever did")

    post = [bx("Post", (7.5, 0, 7.5), (8.5, 30, 8.5), "metal"), bx("Foot", (5.5, 0, 5.5), (10.5, 1, 10.5), "metaldark")]

    def sign(tex):
        return post + [bx("Sign", (2, 20, 6.9), (14, 32, 7.5), tex, faces=("north",), full=True),
                       bx("Back", (2, 20, 6.9), (14, 32, 7.5), "metal", faces=("south", "east", "west", "up", "down"))]
    prop("trafficsign", "Traffic Sign", {"oneway": sign("sign-oneway"), "noentry": sign("sign-noentry"), "exit": sign("sign-exit")},
         box=(0.42, 0, 0.42, 0.58, 2, 0.58), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 1.5, 0.5))},
         comment="A traffic sign in Level 1's car park. They point at walls and dead ends as often as not")


def level2():
    door_block("tunneldoor", "Steel Door", "tunneldoor", "tunneldoor",
               comment="A steel door off one of Level 2's tunnels. Most are locked. A few open, onto another level")
    prop("trolley", "Flatbed Trolley", [
        bx("Deck", (1, 4, 0.5), (15, 5.5, 15.5), "palletwood"), bx("Frame", (0.5, 3, 0), (15.5, 4, 16), "steeldark"),
        bx("W1", (1, 0, 1.5), (3, 3, 4.5), "rubber"), bx("W2", (13, 0, 1.5), (15, 3, 4.5), "rubber"),
        bx("W3", (1, 0, 11.5), (3, 3, 14.5), "rubber"), bx("W4", (13, 0, 11.5), (15, 3, 14.5), "rubber"),
        bx("HandleL", (1.5, 5.5, 14.5), (2.5, 21, 15.5), "steel"), bx("HandleR", (13.5, 5.5, 14.5), (14.5, 21, 15.5), "steel"),
        bx("Bar", (1.5, 20, 14.5), (14.5, 21, 15.5), "steel")],
         box=(0.03, 0, 0, 0.97, 0.38, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:plank-aged", 1.5, 0.5), ("metalbracket", 1.5, 0.5))},
         comment="A flatbed trolley left in a tunnel")
    prop("machineparts", "Machine Parts", [
        bx("Gear", (1, 0, 2), (9, 1.2, 10), "gearflat", faces=("up",), full=True),
        bx("GearEdge", (2.5, 0, 3.5), (7.5, 1.1, 8.5), "rust", faces=("north", "south", "east", "west")),
        bx("Pipe", (9, 0, 3), (11.5, 2.5, 13), "rust", rot=(0, 25, 0), origin=(10, 1, 8)),
        bx("Plate", (3, 0, 10.5), (10, 0.6, 14.5), "steeldark", rot=(0, -12, 0), origin=(6.5, 0, 12.5)),
        bx("Coil", (12, 0, 10), (15, 2, 13), "copper"), bx("Bolt1", (12.5, 0, 4), (13.5, 1, 5), "steel"),
        bx("Bolt2", (5, 0, 0.8), (6, 1, 1.8), "steel")],
         box=(0.06, 0, 0.06, 0.94, 0.16, 0.94), collide=False, material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 0.8, 0.5), ("scrapwire", 0.8, 0.5), ("game:metalbit-copper", 0.5, 0.5), ("game:gear-rusty", 0.08, 0))},
         comment="Pieces of a dismantled machine, left where they fell")


def level3():
    for material in ("glazed", "brick", "cinder"):
        wall_family(f"l3plaque{material}", "Level 3 Wall", {1: material},
                    [Decor("plaque", "Warning Plaque", {2: plate("Plaque", (2, 3, -0.4), (14, 13, 0), "plaque", "white")})],
                    comment="A plaque beside one of Level 3's barred ways")


def level5():
    blades = []
    for i, (frm, to) in enumerate((((10, 8.4, 6.6), (23, 8.9, 9.4)), ((-7, 8.4, 6.6), (6, 8.9, 9.4)),
                                   ((6.6, 8.4, 10), (9.4, 8.9, 23)), ((6.6, 8.4, -7), (9.4, 8.9, 6)))):
        blades.append(bx(f"Blade{i}", frm, to, "wooddark", rot=(0, 24, 0), origin=(8, 8.6, 8)))
    path = shape("ceilingfan", [
        bx("Rose", (6, 15, 6), (10, 16, 10), "brass"), bx("Rod", (7.4, 10, 7.4), (8.6, 15, 8.6), "brass"),
        bx("Hub", (5.8, 7.6, 5.8), (10.2, 10, 10.2), "brass")] + blades)
    block("ceilingfan", {
        "creativeinventory": {"general": ["*"], "decorative": ["*"]}, "blockmaterial": "Wood", "drawtype": "json",
        "shape": {"base": path}, "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionbox": {"x1": 0.3, "y1": 0.45, "z1": 0.3, "x2": 0.7, "y2": 1, "z2": 0.7},
        "lightAbsorption": 0, "resistance": 2, "drops": [], "sounds": WOOD,
    }, "A ceiling fan in one of the hotel's guest rooms. It turns, and cannot be switched off")
    name("ceilingfan", "Ceiling Fan")


def level8():
    block("almondseep", {
        "class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
        "attributes": {"dispenses": ["backrooms:almondwater"], "restock": True},
        "creativeinventory": {"general": ["*"]}, "blockmaterial": "Stone", "drawtype": "cube",
        "textures": {"all": {"base": "block/detail/almondseep"}}, "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": STONE,
        "particleProperties": [{
            "hsvaColor": [{"avg": 32, "var": 4}, {"avg": 40, "var": 15}, {"avg": 225, "var": 20}, {"avg": 200, "var": 30}],
            "gravityEffect": {"avg": 0.6, "var": 0}, "posOffset": [{"avg": 0, "var": 0.55}, {"avg": -0.1, "var": 0.4}, {"avg": 0, "var": 0.55}],
            "velocity": [{"avg": 0, "var": 0.01}, {"avg": -0.2, "var": 0.1}, {"avg": 0, "var": 0.01}], "quantity": {"avg": 0.08},
            "size": {"avg": 0.12, "var": 0.04}, "particleModel": "Cube", "lifeLength": {"avg": 0.9, "var": 0.3}}],
    }, "Almond Water seeping out of the rock beside the 9th Road. It fills a bottle now and then, and comes back")
    name("almondseep", "Almond Water Seep")


def lang():
    LANG["level-redrooms"] = "The Red Rooms"
    LANG["levelhint-redrooms"] = "Nothing holds here. Take what you came for and get out."
    LANG["block-fluorescentlight-red"] = "Red Lamp"
    for part in ("upper", "plain", "baseboard", "rail", "outlet"):
        LANG[f"block-wallpaper-red-{part}"] = "Red Wallpaper"


def generate():
    textures()
    level1()
    level2()
    level3()
    level5()
    level8()
    lang()
