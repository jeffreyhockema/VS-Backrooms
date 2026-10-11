"""Details added to bring the levels closer to the lore: Level 2's doors and clutter, Level 1's cameras and traffic
signs, Level 3's plaques, Level 5's ceiling fans, Level 6's dead light switch and Level 8's seeps of Almond Water.
Called from gen_detail.py, which writes them out along with everything else (python tools/gen_detail.py).

(Level 0's red wallpaper and red lamp are wallpaper and light variants, so their textures are in gen_textures.py.)
"""
import random

from PIL import Image, ImageDraw

from detail_kit import GLASS, LANG, METAL, STONE, WOOD, Decor, block, bx, name, prop, shape, turn, wall_family
from detail_textures import S, noise, rgb, save, text
from gen_deep import door_block, drops, threshold
from gen_detail import carton, cube_block, plate
import fire_fx
from detail_kit import T, seed_of


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


# ======================= Textures =======================

# Level 2's steel doors by paint: body, edge, kick plate, stencil colour, and the number stencilled on (the
# grey-green "" keeps the first doors' texture names)
DOOR_PAINTS = {
    "": (0x4E5A52, 0x2A322C, 0x5E6A60, 0xC8C4B0, 7),
    "white": (0xC6C8C2, 0x8A8E88, 0xB4B6B0, 0x3A3C3A, 12),
    "grey": (0x7C8084, 0x4A4E52, 0x8C9094, 0xD8D6CE, 4),
    "cream": (0xC9BD98, 0x8E8468, 0xB8AC88, 0x4A3E2C, 21),
}


def tunnel_door(paint, body, edge, kick, ink, number):
    suffix = f"-{paint}" if paint else ""
    for part in ("lower", "upper"):
        img = noise(body, 5, "tunneldoor" + paint + part)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, S - 1, S - 1], outline=rgb(edge), width=2)
        if part == "lower":
            d.rectangle([4, 20, S - 5, 27], fill=rgb(kick))                     # kick plate
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
            d.rectangle([10, 5, 21, 18], outline=rgb(edge))
            text(img, "B-%02d" % number, (4, 21, S - 4, 29), ink, 6)
            rng = random.Random(seed_of("tdstreak" + paint))
            px = img.load()
            for _ in range(5):                                                  # rust weeping from the hinges
                x = rng.choice((2, 3, 28, 29))
                for y in range(rng.randint(0, 6), rng.randint(12, 26)):
                    px[x, y] = shade((110, 62, 34), rng.uniform(0.8, 1.1))
        save(img, f"tunneldoor{suffix}-{part}")


def tram_textures():
    """Level 2's tramway (layout version 5): rusted rail, the B.N.T.G.'s locomotive in faded green with a yellow band
    and its initials, its grimy cab glass and grilles; the candle stubs a den's visitors left."""
    img = noise(0x5A3A26, 6, "tramrail")
    T.blotch(img, (10, 10), 8, (120, 66, 34), 0.6, seed_of("tramrail1"))
    T.blotch(img, (24, 24), 7, (70, 46, 30), 0.5, seed_of("tramrail2"))
    save(img, "tramrail")
    body = noise(0x3E5A44, 5, "trambody")
    d = ImageDraw.Draw(body)
    d.rectangle([0, 19, S - 1, 22], fill=rgb(0xC8A030))                       # the yellow band
    d.line([0, 18, S - 1, 18], fill=rgb(0x283A2C))
    for x in (0, 15, 31):                                                     # panel seams
        d.line([x, 0, x, S - 1], fill=rgb(0x2C4032))
    for k, (cx, cy, r) in enumerate(((6, 27, 6), (24, 8, 5), (20, 29, 7))):
        T.blotch(body, (cx, cy), r, (110, 62, 32), 0.6, seed_of("tramrust%d" % k))
    save(body, "trambody")
    side = body.copy()
    text(side, "B.N.T.G.", (2, 24, S - 2, 31), 0xD8C890, 6)                # under the band, below the cab windows
    save(side, "trambodylogo")
    glass = noise(0x1A2224, 4, "tramglass")
    d = ImageDraw.Draw(glass)
    d.line([3, 3, 12, 12], fill=rgb(0x3E4A4E), width=2)
    T.blotch(glass, (24, 26), 7, (70, 66, 54), 0.5, seed_of("tramgrime"))
    save(glass, "tramglass")
    grille = noise(0x3E5A44, 4, "tramgrille")
    d = ImageDraw.Draw(grille)
    for y in range(3, S - 2, 4):
        d.rectangle([3, y, S - 4, y + 1], fill=rgb(0x14181A))
    save(grille, "tramgrille")
    wax = noise(0xE6DCC0, 3, "candlewax")
    T.blotch(wax, (16, 4), 8, (200, 186, 150), 0.4, seed_of("candlewax"))
    save(wax, "candlewax")


def textures():
    # Level 2's steel doors: grey-green paint, rust creeping up from the floor, a wired-glass slit, a stencilled number;
    # and the same doors "in various shades of white, grey and cream" (Wikidot), their numbers stencilled dark
    for paint, (body, edge, kick, ink, number) in DOOR_PAINTS.items():
        tunnel_door(paint, body, edge, kick, ink, number)

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

    # Almond Water seeping down a rock face (see level8): plain wet rock for a seep whose rock is unknown, the dark
    # wet stain it leaves (the upper block's, from the crack it comes out of, and the lower block's, widening to the
    # floor; dithered at its edges so the rock shows through), the milky water, the cream crust it lays down at
    # its source, and the pool it gathers in
    save(noise(0x55504A, 9, "seeprock"), "almondseep")
    rng = random.Random(seed_of("seep"))
    for name, top, bottom, start in (("seepstain", 2.0, 8.5, 6), ("seepstainlow", 8.5, 11.0, 0)):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        px = img.load()
        for y in range(start, S):
            hw = top + (bottom - top) * (y - start) / (S - 1 - start)
            if name == "seepstainlow" and y >= S - 6:
                hw += (y - (S - 7)) * 0.9  # spreading out where it meets the floor
            for x in range(S):
                d = abs(x - 15.5 - 1.2 * ((y // 7) % 2)) / hw
                if d < 0.6 or (d < 1.15 and rng.random() < 1.15 - d):
                    v = rng.randint(-5, 5)
                    px[x, y] = (38 + v, 35 + v, 31 + v, 255)
        if name == "seepstain":
            for y in range(3, 7):
                for x in range(14, 18):
                    px[x, y] = (18, 16, 14, 255)  # the crack it comes out of
        for x0 in (14, 17):
            x = x0
            for y in range(start + 1, S):
                x += rng.choice((-1, 0, 0, 0, 1)) if y % 5 == 0 else 0
                if rng.random() < 0.7:
                    px[x, y] = (150, 144, 122, 255)  # a milky film
        save(img, name)
    img = noise(0xD8D2B8, 6, "seepwater")
    ImageDraw.Draw(img).line([1, 0, 1, S - 1], fill=rgb(0xF4F0E0))
    save(img, "seepwater")
    img = noise(0xC8BC98, 8, "seepcrust")
    T.blotch(img, (16, 16), 12, (226, 218, 190), 0.5, seed_of("seepcrust"))
    save(img, "seepcrust")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for y in range(S):
        for x in range(S):
            d = (((x - 15.5) / 15.5) ** 2 + ((y - 15.5) / 15.5) ** 2) ** 0.5 + rng.uniform(-0.12, 0.12)
            if d < 1:
                v = rng.randint(-6, 6)
                px[x, y] = (200 + v, 194 + v, 168 + v, 255) if d < 0.75 else (120 + v, 114 + v, 96 + v, 255)
    for x, y in ((12, 13), (18, 17), (15, 20)):
        px[x, y] = (244, 240, 224, 255)  # glints where the drips land
    save(img, "seeppool")

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
    # The same door in white, grey or cream paint (the generator picks the paint by the door's place)
    paints = [p for p in DOOR_PAINTS if p]
    block("tunneldoorpaint", {
        "variantgroups": [{"code": "paint", "states": paints}, {"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Metal", "drawtype": "cube",
        "textures": {"all": {"base": "block/detail/tunneldoor-{paint}-{part}"}},
        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL,
        "behaviors": threshold("tunneldoor")},
        "A steel door off one of Level 2's tunnels, painted white, grey or cream. Most are locked. A few open, onto another level")
    name("tunneldoorpaint-*", "Steel Door")
    tramway()
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


def track(z1=0.0, z2=16.0, sleepers=(1.5, 5.5, 9.5, 13.5), gone=()):
    """Narrow-gauge track along Z: two rails on sleepers, laid straight on the tunnel floor."""
    els = [bx(f"Sleeper{i}", (1.5, 0, z), (14.5, 0.8, z + 2), "wooddark") for i, z in enumerate(sleepers) if i not in gone]
    for nm, x in (("RailL", 3.2), ("RailR", 11.8)):
        els += [bx(nm + "Foot", (x - 0.4, 0.8, z1), (x + 1.4, 1.1, z2), "tramrail"),
                bx(nm, (x, 1.1, z1), (x + 1, 2.2, z2), "tramrail")]
    return els


def tramway():
    """The B.N.T.G.'s narrow-gauge tramway down some of Level 2's mains (layout version 5): "a narrow-gauge tramway
    ... used as a means to transport vast quantities of acquired goods", its trains "powered via Level 2's
    electricity", and when the power failed "the railway system The B.N.T.G. created was left to the elements"
    (Wikidot). The rails, a two-block electric locomotive dead on them, and the goods wagon it was hauling."""
    rails = {"ns": track(gone=(2,)), "we": track(gone=(0,)),
             "cross": track(sleepers=()) + [turn(e, 1) for e in track(sleepers=())]}
    by_type = {}
    for k, els in rails.items():
        path = shape(f"tramrails-{k}", [turn(e, 1) for e in els] if k == "we" else els)
        by_type[f"*-{k}"] = {"base": path}
    block("tramrails", {
        "variantgroups": [{"code": "axis", "states": ["we", "ns", "cross"]}],
        "creativeinventory": {"general": ["*-ns"], "decorative": ["*-ns"]},
        "blockmaterial": "Metal", "drawtype": "json", "shapeByType": by_type,
        "sidesolid": {"all": False}, "sideopaque": {"all": False}, "collisionbox": None,
        "selectionbox": {"x1": 0, "y1": 0, "z1": 0, "x2": 1, "y2": 0.14, "z2": 1},
        "lightAbsorption": 0, "resistance": 2, "sounds": METAL,
        "drops": drops(("metalbracket", 0.6, 0.3), ("game:plank-aged", 0.4, 0.3))},
        "The B.N.T.G.'s narrow-gauge tramway down one of Level 2's mains, rusting since the power went")
    name("tramrails-*", "Tram Rails")

    def bogie(z):
        return [bx(f"Wheel{z}L", (2.6, 0.9, z), (3.6, 4.4, z + 3.5), "blackmetal"), bx(f"Wheel{z}R", (12.4, 0.9, z), (13.4, 4.4, z + 3.5), "blackmetal"),
                bx(f"Axlebox{z}L", (1.8, 2, z + 1), (2.6, 3.4, z + 2.5), "rust"), bx(f"Axlebox{z}R", (13.4, 2, z + 1), (14.2, 3.4, z + 2.5), "rust")]
    frame = [bx("Frame", (2, 3.4, 0.4), (14, 5, 16), "steeldark")] + bogie(2) + bogie(10.5)
    front = track() + frame + [
        bx("Buffer", (1, 3, -0.2), (15, 6, 0.6), "redmetal"), bx("Coupler", (7, 3.6, -1.2), (9, 5, -0.2), "steeldark"),
        bx("Cab", (2, 5, 0.6), (14, 22, 16), "trambody", faces=("north", "up", "down", "south")),
        bx("CabSideL", (2, 5, 0.6), (2.01, 22, 16), "trambodylogo", faces=("west",), full=True),
        bx("CabSideR", (13.99, 5, 0.6), (14, 22, 16), "trambodylogo", faces=("east",), full=True),
        bx("WindowL", (3.2, 13, 0.3), (7.6, 19.5, 0.6), "tramglass", full=True),
        bx("WindowR", (8.4, 13, 0.3), (12.8, 19.5, 0.6), "tramglass", full=True),
        bx("SideWinL", (1.7, 13, 3), (2, 19.5, 9), "tramglass", full=True),
        bx("SideWinR", (14, 13, 3), (14.3, 19.5, 9), "tramglass", full=True),
        bx("Roof", (1.5, 22, 0.2), (14.5, 23.2, 16), "steeldark"), bx("RoofTop", (3, 23.2, 0.8), (13, 24.2, 16), "steeldark"),
        bx("Lamp", (6.5, 8, 0.2), (9.5, 11, 0.6), "steel"), bx("LampGlass", (7, 8.5, 0), (9, 10.5, 0.2), "tubeoff"),
        bx("Step", (0.8, 3, 11), (2, 3.6, 14), "steeldark"), bx("Handrail", (1.4, 6, 10.6), (1.8, 14, 11), "steel")]
    rear = track() + frame + [
        bx("Hood", (3, 5, 0), (13, 16, 13.5), "tramgrille", faces=("east", "west"), full=True),
        bx("HoodTop", (3, 5, 0), (13, 16, 13.5), "trambody", faces=("up", "south")),
        bx("Battery", (2.2, 5, 2), (3, 10, 11), "blackmetal"), bx("Battery2", (13, 5, 2), (13.8, 10, 11), "blackmetal"),
        bx("Buffer", (1, 3, 15.4), (15, 6, 16.2), "redmetal"), bx("Coupler", (7, 3.6, 16.2), (9, 5, 17.2), "steeldark"),
        bx("PoleBase", (7, 16, 4), (9, 17.5, 6), "steeldark"),
        bx("Pole", (7.6, 16.5, 4.5), (8.4, 17.3, 22), "steel", rot=(28, 0, 0), origin=(8, 17, 5)),
        bx("PoleHead", (7, 16, 21), (9, 18, 23), "blackmetal", rot=(28, 0, 0), origin=(8, 17, 5))]
    prop("deadtram", "Dead Tram", {"front": front, "rear": rear}, box=(0.06, 0, 0, 0.94, 1.45, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 3, 1), ("scrapwire", 2, 1), ("game:metalbit-copper", 1, 0.5))},
         comment="The B.N.T.G.'s little electric locomotive, two blocks long, dead on its rails since the power went")
    wagon = track() + frame + [
        bx("Deck", (1.5, 5, 0.4), (14.5, 5.8, 15.6), "palletwood"),
        bx("Stake1", (1.5, 5.8, 0.4), (2.3, 12, 1.2), "steeldark"), bx("Stake2", (13.7, 5.8, 0.4), (14.5, 12, 1.2), "steeldark"),
        bx("Stake3", (1.5, 5.8, 14.8), (2.3, 12, 15.6), "steeldark"), bx("Stake4", (13.7, 5.8, 14.8), (14.5, 12, 15.6), "steeldark"),
        bx("Buffer", (1, 3, -0.2), (15, 6, 0.6), "redmetal"), bx("BufferB", (1, 3, 15.4), (15, 6, 16.2), "redmetal")] + \
        carton("Load1", (2.5, 5.8, 1.5), (8, 11, 7)) + carton("Load2", (8.5, 5.8, 2), (13.5, 10, 7.5)) + \
        carton("Load3", (3, 5.8, 8.5), (9.5, 10.5, 14.5)) + carton("Load4", (3.5, 11, 2), (7.5, 14, 6))
    prop("tramwagon", "Tram Wagon", wagon, box=(0.06, 0, 0, 0.94, 0.9, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("metalbracket", 2, 1), ("game:plank-aged", 2, 1))},
         comment="A goods wagon of the B.N.T.G.'s tramway, still loaded, where the power left it")

    # Candle stubs on a tin plate, by a Warren's cache and under its crosses (layout version 5), so its warnings show
    candles = [(6, 6, 3.5), (9.5, 7.5, 2.5), (7, 10, 2)]
    els = [bx("Plate", (4, 0, 4), (12, 0.5, 12), "steeldark"), bx("Puddle", (8.5, 0.5, 9), (11, 0.7, 11.5), "candlewax")]
    flames = []
    for i, (x, z, h) in enumerate(candles):
        els += [bx(f"Candle{i}", (x, 0.5, z), (x + 1.4, 0.5 + h, z + 1.4), "candlewax"),
                bx(f"Wick{i}", (x + 0.55, 0.5 + h, z + 0.55), (x + 0.85, 1.1 + h, z + 0.85), "blackmetal")]
        flames.append(fire_fx.flame((x + 0.7) / 16 - 0.5, (1.1 + h) / 16 - 0.25, (z + 0.7) / 16 - 0.5, quantity=0.06, size=0.04))
    prop("candlestubs", "Candle Stubs", els, box=(0.25, 0, 0.25, 0.75, 0.25, 0.75), oriented=False, material="Metal", sounds=METAL,
         light=[7, 5, 7], extra={"particleProperties": flames, "drops": drops(("game:candle", 1, 0.5))},
         comment="Candle stubs left burning by a den's cache and under its crosses by whoever came before")


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


# The rocks of Level 8's strata, in WorldGenerator.Deep's order: a seep wears the rock it seeps out of
SEEP_ROCKS = ("granite", "limestone", "andesite", "shale", "basalt", "sandstone", "chalk", "slate", "claystone", "peridotite", "chert",
              "halite")


def level8():
    # Almond Water seeping out of the rock: a rock cube (the host's own rock) with a crust of deposit where it comes out
    # of a crack, two milky trickles running down this face and the one below over a dark wet stain, and a pool on the
    # floor in front. The block does not know which way the road is, so every face has it (the others are in rock)
    side = [bx("Stain", (0, 0, -0.12), (16, 16, -0.1), "seepstain", faces=("north",), full=True),
            bx("StainLow", (0, -16, -0.12), (16, 0, -0.1), "seepstainlow", faces=("north",), full=True),
            bx("Crust", (6.2, 12.6, -0.7), (10.2, 14.2, 0), "seepcrust", faces=("north", "east", "west", "up", "down")),
            bx("Crust2", (7, 11.6, -0.4), (9.4, 12.6, 0), "seepcrust", faces=("north", "east", "west", "down")),
            bx("Pool", (3.5, -15.85, -5), (12.5, -15.7, -0.1), "seeppool", faces=("up",), full=True, glow=20)]
    for i, (x, y1, y2) in enumerate(((7.4, 6, 11.6), (7.9, -4, 6), (7.5, -15.9, -4), (8.9, 0.5, 11.6), (9.2, -15.9, 0.5))):
        side.append(bx(f"Trickle{i}", (x, y1, -0.4), (x + 0.5, y2, -0.12), "seepwater", faces=("north", "east", "west"), glow=30))
    els = [bx("Rock", (0, 0, 0), (16, 16, 16), "rock")]
    for k in range(4):
        els += [turn(e, k) for e in side]
    path = shape("almondseep", els)
    common = {
        "class": "BackroomsDispenser", "entityClass": "BackroomsDispenser",
        "attributes": {"dispenses": ["backrooms:almondwater"], "restock": True},
        "blockmaterial": "Stone", "drawtype": "json", "shape": {"base": path},
        "lightAbsorption": 99, "resistance": 6, "drops": [], "sounds": STONE,
        "particleProperties": [{
            "hsvaColor": [{"avg": 32, "var": 4}, {"avg": 40, "var": 15}, {"avg": 225, "var": 20}, {"avg": 200, "var": 30}],
            "gravityEffect": {"avg": 0.6, "var": 0}, "posOffset": [{"avg": 0, "var": 0.55}, {"avg": -0.1, "var": 0.4}, {"avg": 0, "var": 0.55}],
            "velocity": [{"avg": 0, "var": 0.01}, {"avg": -0.2, "var": 0.1}, {"avg": 0, "var": 0.01}], "quantity": {"avg": 0.08},
            "size": {"avg": 0.12, "var": 0.04}, "particleModel": "Cube", "lifeLength": {"avg": 0.9, "var": 0.3}}],
    }
    block("almondseep", dict(common, creativeinventory={"general": ["*"]}, textures={"rock": {"base": "block/detail/almondseep"}}),
          "Almond Water seeping out of the rock beside the 9th Road. It fills a bottle now and then, and comes back")
    name("almondseep", "Almond Water Seep")
    block("almondseeprock", dict(common, variantgroups=[{"code": "rock", "states": list(SEEP_ROCKS)}],
                                 creativeinventory={"general": ["*-granite"]},
                                 texturesByType={f"*-{r}": {"rock": {"base": f"game:block/stone/rock/{r}1"}} for r in SEEP_ROCKS}),
          "The same seep in each of Level 8's rocks, so that it is part of the rock face it seeps out of")
    name("almondseeprock-*", "Almond Water Seep")


def lang():
    LANG["level-redrooms"] = "The Red Rooms"
    LANG["levelhint-redrooms"] = "Nothing holds here. Take what you came for and get out."
    LANG["block-fluorescentlight-red"] = "Red Lamp"
    for part in ("upper", "plain", "baseboard", "rail", "outlet"):
        LANG[f"block-wallpaper-red-{part}"] = "Red Wallpaper"


def generate():
    textures()
    tram_textures()
    level1()
    level2()
    level3()
    level5()
    level8()
    lang()
