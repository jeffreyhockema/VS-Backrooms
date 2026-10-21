"""Details added to bring the levels closer to the lore: Level 2's doors and clutter, Level 1's cameras and traffic
signs, Level 3's plaques, Level 5's ceiling fans, Level 6's dead light switch and Level 8's seeps of Almond Water.
Called from gen_detail.py, which writes them out along with everything else (python tools/gen_detail.py).

(Level 0's red wallpaper and red lamp are wallpaper and light variants, so their textures are in gen_textures.py.)
"""
import math
import random

from PIL import Image, ImageDraw

from detail_kit import EXT, GLASS, LANG, METAL, STONE, WOOD, Decor, block, bx, name, prop, shape, turn, wall_family
from detail_textures import S, enamel_plaque, noise, rgb, save, text
import matlib as M
import modelkit as K
import l1props as L1
from gen_deep import door_block, drops, threshold
from gen_detail import carton, cube_block, plate, rivets
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
    """(B5) A steel door's leaf, painted: `matlib.painted_metal` in the door's paint with chips to grey primer, the
    2 px edge shaded as a frame (lit top and left, dark where it meets the leaf), rust creeping up from the floor on the
    lower half and weeping from the hinges on the upper, the wired glass and the stencilled number. The lever handle,
    the kick plate, the hinges and the window's bead are geometry now (`tunnel_door_shape`); `kick` is no longer
    painted."""
    suffix = f"-{paint}" if paint else ""
    base = T.hexrgb(body)
    for part in ("lower", "upper"):
        img = M.painted_metal(seed_of("tunneldoor" + paint + part), base=base, grain=3, mottle=5, panel=False, chips=3,
                              under=(118, 116, 108))
        px = img.load()
        frame = T.hexrgb(edge)
        for y in range(S):
            for x in range(S):
                if x < 2 or x >= S - 2 or (part == "upper" and y < 2) or (part == "lower" and y >= S - 2):
                    px[x, y] = M.rgba(M.lift(frame, (x < 2) * 6 - (x >= S - 2) * 6 + (y < 2) * 6))
        for y in range(S):  # the leaf's edge in the frame's shadow
            M.touch(img, 2, y, -0.12)
            M.touch(img, S - 3, y, 0.05)
        if part == "upper":
            for x in range(2, S - 2):
                M.touch(img, x, 2, -0.12)
        if part == "lower":
            clean = img.copy()
            M.grime(img, 0.5, seed_of("tdr1" + paint), color=(120, 66, 34), bias="bottom", cover=0.45)  # rust from the floor
            cp = clean.load()
            for y in range(24):  # ... only up the lowest third of the leaf, fading out
                t = max(0.0, (y - 14) / 10)
                for x in range(S):
                    px[x, y] = M.rgba(M.mix(cp[x, y][:3], px[x, y][:3], t))
            M.grime(img, 0.14, seed_of("tdgrime" + paint), bias="bottom", cover=0.5)
        else:
            for y in range(6, 18):  # wired glass, dark behind, a faint sheen across it (its bead is geometry)
                for x in range(11, 21):
                    c = (22, 26, 28)
                    if (x - 11) % 3 == 0 or (y - 6) % 3 == 0:
                        c = (58, 64, 62)
                    if 5 <= (x - 11) + (17 - y) <= 7:
                        c = M.lift(c, 12)
                    px[x, y] = M.rgba(c)
            text(img, "B-%02d" % number, (3, 19, S - 3, 30), ink, 8)
            rng = random.Random(seed_of("tdstreak" + paint))
            for _ in range(5):                                                  # rust weeping from the hinges
                x = rng.choice((2, 3, 28, 29))
                for y in range(rng.randint(0, 6), rng.randint(12, 26)):
                    px[x, y] = shade((110, 62, 34), rng.uniform(0.8, 1.1))
        M.grime(img, 0.14, seed_of("tdage" + paint + part), cover=0.5)  # (round 2) older, dirtier paint
        save(img, f"tunneldoor{suffix}-{part}")


def tunnel_door_shape(part):
    """(B5) A steel door as a cube leaf with its hardware standing out of it. The block has no facing, so, as Level 2's
    pipe walls do, the hardware is on all four sides; on the two that face the doorway's jambs it is buried in the wall.
    Lower: a lever handle on its rose, a brushed kick plate with screws, a hinge. Upper: a steel bead round the wired
    glass, a hinge. The leaf keeps the cube's texture key, named after its texture so the painted doors can swap it."""
    key = f"tunneldoor-{part}"
    if part == "lower":
        hw = K.lever("Lever", 3.5, 13.5, 0, length=3.0, tex="doorsteel", side=1)
        hw += K.kick_plate("Kick", 2.0, 14.0, 2.5, 6.0, 0, tex="doorsteel")
        hw += K.hinge("Hinge", 15.25, 2.0, 5.0, 0, tex="doorsteel", side="right")
    else:
        hw = [K.box("BeadT", (5.0, 13.0, -0.5), (11.0, 13.5, 0), "doorsteel", faces=("north", "east", "west", "up", "down")),
              K.box("BeadB", (5.0, 7.0, -0.5), (11.0, 7.5, 0), "doorsteel", faces=("north", "east", "west", "up", "down")),
              K.box("BeadL", (5.0, 7.5, -0.5), (5.5, 13.0, 0), "doorsteel", faces=("north", "east", "west")),
              K.box("BeadR", (10.5, 7.5, -0.5), (11.0, 13.0, 0), "doorsteel", faces=("north", "east", "west"))]
        hw += K.hinge("Hinge", 15.25, 10.0, 13.0, 0, tex="doorsteel", side="right")
    els = [bx("Leaf", (0, 0, 0), (16, 16, 16), key, full=True)]
    for i in range(4):
        els += [dict(e, name=f"{e['name']}{i}") for e in K.turn(hw, i)]
    return shape(f"tunneldoor-{part}", els)


def trolley_textures():
    """(Level 2 art) The flatbed trolley's materials: faded ochre paint on the stake pockets and handle, bare rusty steel
    for the chassis, two weathered deck boards, and a worn tyre. Each shows rust, grime or runs; the model's faces show
    a texture from its corner, so nothing is tied to its edges."""
    def steel(key, base, rust, mean):
        im = M.painted_metal(seed_of(key), base=base, grain=3, mottle=6, panel=False, chips=5, under=(96, 78, 62))
        M.rust(im, rust, seed_of(key + "rust"), color=(142, 74, 38), dark=(86, 46, 30))
        M.grime(im, 0.22, seed_of(key + "grime"), cover=0.55)
        M.drips(im, 4, seed_of(key + "runs"), color=(110, 62, 36), length=(6, 16), strength=0.35)
        return T.match_mean(im, mean)
    save(steel("trolleypaint", (168, 138, 66), 0.16, 104), "trolleypaint")
    save(steel("trolleyrust", (84, 66, 52), 0.5, 66), "trolleyrust")
    for k, base, mean in (("", (150, 112, 70), 96), ("2", (128, 94, 60), 84)):
        im = M.wood_planks(seed_of("trolleyplank" + k), base=base, planks=[S], direction="v", grain=4, contrast=1.1,
                           flecks=1.2, per_plank=4)
        M.grime(im, 0.3, seed_of("trolleyplankgrime" + k), color=(48, 40, 30), cover=0.6)
        M.stain(im, seed_of("trolleyplankstain" + k), radius=7, color=(60, 48, 34), strength=0.3)
        save(T.match_mean(im, mean), "trolleyplank" + k)
    im = M.rubber(seed_of("trolleytyre"), base=(52, 50, 50), grain=3, mottle=5)
    M.grime(im, 0.25, seed_of("trolleytyregrime"), color=(86, 80, 70), cover=0.5)
    save(im, "trolleytyre")


def tram_textures():
    """Level 2's tramway (layout version 5): rusted rail, the B.N.T.G.'s locomotive in faded green with a yellow band
    and its initials, its grimy cab glass and grilles; the candle stubs a den's visitors left.
    (B5) The paint is `matlib.painted_metal` gone to rust in scattered patches (the model's faces show the texture from
    its corner, so nothing is tied to the texture's edges), the band and lettering kept; the cab front's lower panel has
    its own key (`tramfront`) so the band lines up with the sides; the glass is darker at the foot with a soft sheen; the
    headlamp lens is its own key. The grilles, windows and lamps are geometry (`tramway`)."""
    img = M.noise_hv((98, 60, 40), 4, seed_of("tramrail"), mottle=6)
    M.rust(img, 0.45, seed_of("tramrail1"), pits=True)
    save(T.match_mean(img, 66), "tramrail")
    green = (62, 90, 68)

    def paint(key, mean):
        im = M.painted_metal(seed_of(key), base=green, grain=3, mottle=6, panel=False, chips=4, under=(92, 84, 72))
        M.rust(im, 0.1, seed_of(key + "rust"), color=(122, 70, 40), dark=(78, 48, 32))
        M.grime(im, 0.22, seed_of(key + "grime"), cover=0.55)
        M.drips(im, 4, seed_of(key + "runs"), color=(104, 64, 40), length=(6, 16), strength=0.35)
        return T.match_mean(im, mean)

    def band(im, y0, y1):
        px = im.load()
        for y in range(y0, y1 + 1):
            for x in range(S):
                under = px[x, y]
                d = (M.lum(under) - 84) * 0.5
                px[x, y] = M.rgba(M.lift((196, 156, 52), d + (8 if y == y0 else -14 if y == y1 else 0)))
        for x in range(S):
            M.touch(im, x, y0 - 1, -0.25)
            M.touch(im, x, y1 + 1, -0.12)

    body = paint("trambody", 82)
    save(body, "trambody")
    front = paint("tramfront", 82)
    band(front, 18, 21)
    save(front, "tramfront")
    side = paint("trambodylogo", 82)
    band(side, 19, 22)
    M.emboss_lines(side, xs=(15,), strength=0.16)
    for y in range(3, 17, 4):  # rivets down the panel seam
        M.screw(side, 13, y, slot=False)
    text(side, "B.N.T.G.", (2, 24, S - 2, 31), 0xD8C890, 6)                # under the band, below the cab windows
    save(side, "trambodylogo")
    glass = M.noise_hv((24, 32, 34), 2, seed_of("tramglass"), mottle=3)
    gp = glass.load()
    for y in range(S):
        for x in range(S):
            k = (x + (S - y)) % 40
            if 10 <= k <= 15:  # a soft sheen across the pane
                M.touch(glass, x, y, 0.35 - abs(k - 12.5) * 0.08)
            if y > 22:  # grime settled at the foot of the pane
                gp[x, y] = M.rgba(M.mix(gp[x, y][:3], (64, 60, 50), (y - 22) / 18))
    save(glass, "tramglass")
    lens = M.noise_hv((170, 166, 140), 2, seed_of("tramlens"), (16, 16), 2)
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5 / 7.5
            M.touch(lens, x, y, 0.12 - 0.4 * d * d + (0.3 if (x - 5) ** 2 + (y - 5) ** 2 < 4 else 0))
    save(lens, "tramlens")
    grille = noise(0x3E5A44, 4, "tramgrille")
    d = ImageDraw.Draw(grille)
    for y in range(3, S - 2, 4):
        d.rectangle([3, y, S - 4, y + 1], fill=rgb(0x14181A))
    save(grille, "tramgrille")
    # (B5) tallow, yellowed: a soft mottle with faint runs down it and a darker skin where it has been handled
    wax = M.noise_hv((228, 216, 186), 2, seed_of("candlewax"), mottle=5)
    M.drips(wax, 5, seed_of("candleruns"), color=(206, 190, 150), length=(8, 20), strength=0.3)
    save(wax, "candlewax")


def textures():
    # Level 2's steel doors: grey-green paint, rust creeping up from the floor, a wired-glass slit, a stencilled number;
    # and the same doors "in various shades of white, grey and cream" (Wikidot), their numbers stencilled dark
    for paint, (body, edge, kick, ink, number) in DOOR_PAINTS.items():
        tunnel_door(paint, body, edge, kick, ink, number)
    steel = M.brushed_metal(seed_of("doorsteel"), base=(92, 94, 92), grain=3)  # (B5) its hardware: dark, scuffed
    M.scratches(steel, 6, seed_of("doorsteelscratch"))
    M.grime(steel, 0.2, seed_of("doorsteelgrime"), cover=0.5)
    save(steel, "doorsteel")

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

    # A plaque beside a barred way. (B6) An enamel face with a red rule (detail_textures.enamel_plaque); its screws are
    # geometry now (level3), where the old one painted them
    img = enamel_plaque(seed_of("plaque"), ground=(230, 226, 212), rule=(138, 30, 24), inset=1)
    text(img, "OUT OF", (2, 4, S - 2, 13), 0x8A1A14, 6)
    text(img, "BOUNDS", (2, 12, S - 2, 21), 0x8A1A14, 6)
    text(img, "DO NOT ENTER", (2, 22, S - 2, 29), 0x202020, 4)
    save(img, "plaque")

    # Almond Water seeping down a rock face (see level8): plain wet rock for a seep whose rock is unknown, the dark
    # wet stain it leaves (the upper block's, from the crack it comes out of, and the lower block's, widening to the
    # floor; dithered at its edges so the rock shows through), the milky water, the cream crust it lays down at
    # its source, and the pool it gathers in
    save(noise(0x55504A, 9, "seeprock"), "almondseep")
    seep_textures()

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
    camera = L1.camera()  # (Level 1 props) modelled in tools/l1props.py
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


def trolley_parts():
    """(Level 2 art) The flatbed trolley as geometry, front to the north: two steel channels with cross members and the
    axles under them, five deck boards with gaps (one split and sagging), stake pockets along both sides with one bent
    stake still in its pocket, a tow ring at the front, rubber tyres on hubs, and a push handle at the back (two
    uprights in sockets, a lower bar and a grip). Footprint and collision as before; the top of the deck is at 5.5."""
    els = []
    # chassis: channels (web and inward lip), cross members, tow ring
    for nm, x1, x2, lx1, lx2 in (("L", 1.2, 2.4, 2.4, 3.4), ("R", 13.6, 14.8, 12.6, 13.6)):
        els += [bx(f"Channel{nm}", (x1, 3.0, 0.4), (x2, 4.2, 15.6), "trolleyrust"),
                bx(f"Lip{nm}", (lx1, 3.0, 0.4), (lx2, 3.5, 15.6), "trolleyrust", faces=("north", "south", "up", "down", "east", "west"))]
    for i, z in enumerate((1.5, 7.0, 13.0)):
        els.append(bx(f"Cross{i}", (3.4, 3.4, z), (12.6, 4.2, z + 1.2), "trolleyrust", faces=("north", "south", "down")))
    els += [bx("TowPlate", (6.5, 3.2, 0.2), (9.5, 4.2, 1.6), "trolleyrust"),
            bx("TowRingL", (6.7, 3.4, 0.05), (7.5, 4.0, 1.0), "trolleypaint", faces=("north", "east", "up")),
            bx("TowRingR", (8.5, 3.4, 0.05), (9.3, 4.0, 1.0), "trolleypaint", faces=("north", "west", "up")),
            bx("TowRingBar", (7.5, 3.4, 0.05), (8.5, 4.0, 0.6), "trolleypaint", faces=("north", "up"))]
    # deck boards along Z with gaps, uneven wear
    for i in range(5):
        x1 = 1.4 + i * 2.7
        key = "trolleyplank" if i % 2 == 0 else "trolleyplank2"
        top = (4.2, 5.5)
        if i == 2:  # split across the middle: the rear half sags
            els += [bx("PlankSplitF", (x1, 4.2, 0.2), (x1 + 2.4, 5.5, 7.6), key, faces=("north", "east", "west", "up", "south")),
                    bx("PlankSplitR", (x1, 4.2, 8.5), (x1 + 2.4, 5.3, 15.8), key, faces=("south", "east", "west", "up", "north"),
                       rot=(-2.5, 0, 0), origin=(x1 + 1.2, 5.0, 15.8))]
            continue
        z1 = 0.9 if i == 4 else 0.2  # one board worn short at the front
        els.append(bx(f"Plank{i}", (x1, top[0], z1), (x1 + 2.4, top[1], 15.8), key, faces=("north", "east", "west", "up", "south")))
    # stake pockets (sockets with a dark mouth) on both sides, a bent stake in one
    for nm, x1, x2 in (("L", 0.3, 1.4), ("R", 14.6, 15.7)):
        for j, z in enumerate((5.6, 9.0)):
            els += [bx(f"Pocket{nm}{j}", (x1, 3.4, z), (x2, 6.1, z + 1.5), "trolleypaint", faces=("north", "south", "east", "west", "down")),
                    bx(f"PocketTop{nm}{j}", (x1, 6.1, z), (x2, 6.2, z + 1.5), "trolleypaint", faces=("up",)),
                    bx(f"PocketMouth{nm}{j}", (x1 + 0.3, 6.12, z + 0.3), (x2 - 0.3, 6.25, z + 1.2), "blackmetal", faces=("up",))]
    els += [bx("Stake", (0.55, 6.2, 5.9), (1.15, 15.2, 6.5), "trolleypaint", rot=(0, 0, 9), origin=(0.85, 6.2, 6.2)),
            bx("StakeCap", (0.5, 15.0, 5.85), (1.2, 15.6, 6.55), "trolleyrust", rot=(0, 0, 9), origin=(0.85, 6.2, 6.2))]
    # axles with their hangers, and four wheels (a square plus the square turned 45 degrees, so it reads round)
    for z in (3.2, 12.8):
        els += [bx(f"Axle{z}", (0.6, 1.8, z - 0.4), (15.4, 2.6, z + 0.4), "trolleyrust", faces=("north", "south", "up", "down")),
                bx(f"Hanger{z}L", (1.6, 2.6, z - 0.7), (2.6, 3.0, z + 0.7), "trolleyrust", faces=("north", "south", "east", "west")),
                bx(f"Hanger{z}R", (13.4, 2.6, z - 0.7), (14.4, 3.0, z + 0.7), "trolleyrust", faces=("north", "south", "east", "west"))]
        for nm, x1, x2, side in (("L", 0.4, 1.6, "west"), ("R", 14.4, 15.6, "east")):
            xm = (x1 + x2) / 2
            els += [bx(f"Tyre{z}{nm}", (x1, 0, z - 2.2), (x2, 4.4, z + 2.2), "trolleytyre"),
                    bx(f"Tyre{z}{nm}45", (x1 + 0.05, 0, z - 2.2), (x2 - 0.05, 4.4, z + 2.2), "trolleytyre",
                       faces=("north", "south", "up", "down", side), rot=(45, 0, 0), origin=(xm, 2.2, z)),
                    bx(f"Hub{z}{nm}", (x1 - 0.2 if nm == "L" else x2, 1.3, z - 0.9), (x1 if nm == "L" else x2 + 0.2, 3.1, z + 0.9),
                       "steel", faces=("north", "south", "up", "down", side))]
    # the push handle at the back: sockets, uprights, a lower bar, a grip
    for nm, x1 in (("L", 1.8), ("R", 12.8)):
        els += [bx(f"Socket{nm}", (x1 - 0.3, 5.5, 14.0), (x1 + 1.3, 7.2, 15.7), "trolleypaint", faces=("north", "south", "east", "west", "up")),
                bx(f"Upright{nm}", (x1, 7.2, 14.4), (x1 + 1.0, 20.2, 15.4), "trolleypaint")]
    els += [bx("LowerBar", (2.8, 10.5, 14.5), (12.8, 11.3, 15.3), "trolleyrust", faces=("north", "south", "up", "down")),
            bx("Grip", (3.6, 19.8, 14.0), (12.0, 21.2, 15.8), "trolleytyre"),
            bx("GripCapL", (1.8, 19.9, 14.3), (3.6, 21.1, 15.5), "trolleypaint"),
            bx("GripCapR", (12.0, 19.9, 14.3), (13.8, 21.1, 15.5), "trolleypaint")]
    return els


def level2():
    # (B5) Drawn from a shape (the leaf and its hardware), not as a cube; codes, groups and behaviour as before
    shapes = {part: tunnel_door_shape(part) for part in ("lower", "upper")}
    block("tunneldoor", {
        "variantgroups": [{"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {f"*-{part}": {"base": path} for part, path in shapes.items()},
        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL,
        "behaviors": threshold("tunneldoor")},
        "A steel door off one of Level 2's tunnels. Most are locked. A few open, onto another level")
    name("tunneldoor-*", "Steel Door")
    # The same door in white, grey or cream paint (the generator picks the paint by the door's place)
    paints = [p for p in DOOR_PAINTS if p]
    block("tunneldoorpaint", {
        "variantgroups": [{"code": "paint", "states": paints}, {"code": "part", "states": ["lower", "upper"]}],
        "creativeinventory": {"general": ["*"], "construction": ["*"]},
        "blockmaterial": "Metal", "drawtype": "json",
        "shapeByType": {f"*-{part}": {"base": path} for part, path in shapes.items()},
        "texturesByType": {f"*-{part}": {f"tunneldoor-{part}": {"base": f"block/detail/tunneldoor-{{paint}}-{part}"}}
                           for part in ("lower", "upper")},
        "lightAbsorption": 99, "resistance": 4, "drops": [], "sounds": METAL,
        "behaviors": threshold("tunneldoor")},
        "A steel door off one of Level 2's tunnels, painted white, grey or cream. Most are locked. A few open, onto another level")
    name("tunneldoorpaint-*", "Steel Door")
    tramway()
    prop("trolley", "Flatbed Trolley", trolley_parts(),
         box=(0.03, 0, 0, 0.97, 0.38, 1), material="Metal", sounds=METAL,
         extra={"drops": drops(("game:plank-aged", 1.5, 0.5), ("metalbracket", 1.5, 0.5))},
         comment="A flatbed trolley left in a tunnel")
    prop("machineparts", "Machine Parts", [
    ] + gear(5, 6) + [  # (B5) the gear as a toothed disc, not a picture of one

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
    for nm, x in (("RailL", 3.2), ("RailR", 11.8)):  # (B5) a rail profile: foot, web and head
        els += [bx(nm + "Foot", (x - 0.4, 0.8, z1), (x + 1.4, 1.1, z2), "tramrail"),
                bx(nm + "Web", (x + 0.25, 1.1, z1), (x + 0.75, 1.7, z2), "tramrail", faces=("east", "west")),
                bx(nm, (x, 1.7, z1), (x + 1, 2.2, z2), "tramrail")]
    return els


def cab_front():
    """(B5) The locomotive's cab front (north), as geometry: a lower panel carrying the livery band (`tramfront`, its
    band level with the sides'), a vertical-barred grille between two headlamps in bezels under visors, and above it
    two windows set back in the cab's frame (posts, sill and header lining the recess), each glass in a dark rubber
    seal with a wiper parked on it."""
    els = [bx("FrontPanel", (2, 5, 0.6), (14, 13, 2.0), "tramfront", faces=("north",), uv=[0, 8, 12, 16]),
           bx("FrontSill", (2, 5, 0.6), (14, 13, 2.0), "trambody", faces=("up", "down")),
           bx("Header", (2, 19.5, 0.6), (14, 22, 2.0), "trambody", faces=("north", "down"))]
    for nm, (a, b), faces in (("PostL", (2, 3), ("north", "east")), ("PostM", (7.5, 8.5), ("north", "east", "west")),
                              ("PostR", (13, 14), ("north", "west"))):  # (the outer posts' sides are the cab's sides)
        els.append(bx(nm, (a, 13, 0.6), (b, 19.5, 2.0), "trambody", faces=faces))
    for nm, (a, b) in (("L", (3, 7.5)), ("R", (8.5, 13))):
        els.append(bx("Glass" + nm, (a, 13, 1.5), (b, 19.5, 1.75), "tramglass", faces=("north",), full=True))
        els += [bx(f"Seal{nm}B", (a, 13, 1.0), (b, 13.5, 1.5), "blackmetal", faces=("north", "up")),
                bx(f"Seal{nm}T", (a, 19.0, 1.0), (b, 19.5, 1.5), "blackmetal", faces=("north", "down")),
                bx(f"Seal{nm}L", (a, 13.5, 1.0), (a + 0.5, 19.0, 1.5), "blackmetal", faces=("north", "east")),
                bx(f"Seal{nm}R", (b - 0.5, 13.5, 1.0), (b, 19.0, 1.5), "blackmetal", faces=("north", "west"))]
        wx = (a + b) / 2
        els.append(bx("Wiper" + nm, (wx - 0.25, 13.6, 0.75), (wx + 0.25, 17.6, 1.0), "steeldark",
                      faces=("north", "east", "west", "up"), rot=(0, 0, -28), origin=(wx, 13.85, 0.85)))
    for nm, cx in (("L", 12.6), ("R", 3.4)):
        cy = 8.0
        els += K.bevelled_box("Lamp" + nm, (cx - 1.25, cy - 1.25, -0.6), (cx + 1.25, cy + 1.25, 0.6), "steeldark")
        els.append(bx("Lens" + nm, (cx - 0.85, cy - 0.85, -0.85), (cx + 0.85, cy + 0.85, -0.6), "tramlens",
                      faces=("north", "east", "west", "up", "down"), uv=[0, 0, 16, 16]))
        els.append(bx("Visor" + nm, (cx - 1.5, cy + 1.25, -1.25), (cx + 1.5, cy + 1.75, 0.6), "steeldark",
                      faces=("north", "east", "west", "up", "down")))
    els += K.grille("Grille", (5.5, 6.25, -0.4), (10.5, 9.75, 0.6), "steeldark", bars=4, axis="v", frame=0.5,
                    back="blackmetal")
    return els


def side_windows():
    """(B5) A bead round each side window of the cab, standing out of the side, so the glass sits back in it."""
    els = []
    for nm, (x1, x2) in (("L", (1.45, 2.0)), ("R", (14.0, 14.55))):
        els += [bx(f"Bead{nm}T", (x1, 19.5, 2.5), (x2, 20.0, 9.5), "steeldark"),
                bx(f"Bead{nm}B", (x1, 12.5, 2.5), (x2, 13.0, 9.5), "steeldark"),
                bx(f"Bead{nm}F", (x1, 13.0, 2.5), (x2, 19.5, 3.0), "steeldark", faces=("north", "south", "east", "west")),
                bx(f"Bead{nm}A", (x1, 13.0, 9.0), (x2, 19.5, 9.5), "steeldark", faces=("north", "south", "east", "west"))]
    return els


def hood_grilles():
    """(B5) The louvred grilles down both sides of the locomotive's hood, as geometry: a grille built facing north and
    turned to the east side, and one turned to the west."""
    east = K.turn(K.grille("GrilleE", (2, 10.5, 2), (11.5, 15, 3), "steeldark", bars=6, axis="v", frame=0.5,
                           back="blackmetal"), 1)
    west = K.turn(K.grille("GrilleW", (4.5, 10.5, 2), (14, 15, 3), "steeldark", bars=6, axis="v", frame=0.5,
                           back="blackmetal"), 3)
    return east + west


def gear(cx, cz, r=3.0, y=1.0):
    """(B5) A rusty gear lying flat at (cx, cz): a disc (a square and the same square turned 45 degrees), eight teeth
    round it, each turned to face out, and a raised hub."""
    els = [bx("GearDisc", (cx - r, 0, cz - r), (cx + r, y, cz + r), "rust"),
           bx("GearDisc45", (cx - r + 0.05, 0, cz - r + 0.05), (cx + r - 0.05, y - 0.05, cz + r - 0.05), "rust",
              faces=("north", "south", "east", "west", "up"), rot=(0, 45, 0), origin=(cx, 0, cz))]
    for k in range(8):
        els.append(bx(f"Tooth{k}", (cx - 0.5, 0, cz - r - 0.9), (cx + 0.5, y - 0.1, cz - r + 0.3), "rust",
                      faces=("north", "east", "west", "up"), rot=(0, 22.5 + 45 * k, 0), origin=(cx, 0, cz)))
    els.append(bx("GearHub", (cx - 1, 0, cz - 1), (cx + 1, y + 0.4, cz + 1), "steeldark", faces=("north", "south", "east", "west", "up")))
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
        # (B5) each wheel a square and the same square turned 45 degrees (a hair thinner), so it reads round
        cy, cz = 2.65, z + 1.75
        return [bx(f"Wheel{z}L", (2.6, 0.9, z), (3.6, 4.4, z + 3.5), "blackmetal"), bx(f"Wheel{z}R", (12.4, 0.9, z), (13.4, 4.4, z + 3.5), "blackmetal"),
                bx(f"Wheel{z}L45", (2.65, 0.9, z), (3.55, 4.4, z + 3.5), "blackmetal", faces=("north", "south", "up", "down", "west"),
                   rot=(45, 0, 0), origin=(3.1, cy, cz)),
                bx(f"Wheel{z}R45", (12.45, 0.9, z), (13.35, 4.4, z + 3.5), "blackmetal", faces=("north", "south", "up", "down", "east"),
                   rot=(45, 0, 0), origin=(12.9, cy, cz)),
                bx(f"Axlebox{z}L", (1.8, 2, z + 1), (2.6, 3.4, z + 2.5), "rust"), bx(f"Axlebox{z}R", (13.4, 2, z + 1), (14.2, 3.4, z + 2.5), "rust")]
    frame = [bx("Frame", (2, 3.4, 0.4), (14, 5, 16), "steeldark")] + bogie(2) + bogie(10.5)
    front = track() + frame + [
        bx("Buffer", (1, 3, -0.2), (15, 6, 0.6), "redmetal"), bx("Coupler", (7, 3.6, -1.2), (9, 5, -0.2), "steeldark"),
        bx("Cab", (2, 5, 2.0), (14, 22, 16), "trambody", faces=("up", "down", "south")),
        bx("CabSideL", (2, 5, 0.6), (2.01, 22, 16), "trambodylogo", faces=("west",), full=True),
        bx("CabSideR", (13.99, 5, 0.6), (14, 22, 16), "trambodylogo", faces=("east",), full=True),
        bx("Roof", (1.5, 22, 0.2), (14.5, 23.2, 16), "steeldark"), bx("RoofTop", (3, 23.2, 0.8), (13, 24.2, 16), "steeldark"),
        bx("Step", (0.8, 3, 11), (2, 3.6, 14), "steeldark"), bx("Handrail", (1.4, 6, 10.6), (1.8, 14, 11), "steel")] + cab_front() + side_windows()
    rear = track() + frame + [
        bx("Hood", (3, 5, 0), (13, 16, 13.5), "trambody", faces=("east", "west", "up", "south")),
        bx("Battery", (2.2, 5, 2), (3, 10, 11), "blackmetal"), bx("Battery2", (13, 5, 2), (13.8, 10, 11), "blackmetal"),
        bx("Buffer", (1, 3, 15.4), (15, 6, 16.2), "redmetal"), bx("Coupler", (7, 3.6, 16.2), (9, 5, 17.2), "steeldark"),
        bx("PoleBase", (7, 16, 4), (9, 17.5, 6), "steeldark"),
        bx("Pole", (7.6, 16.5, 4.5), (8.4, 17.3, 22), "steel", rot=(28, 0, 0), origin=(8, 17, 5)),
        bx("PoleHead", (7, 16, 21), (9, 18, 23), "blackmetal", rot=(28, 0, 0), origin=(8, 17, 5))] + hood_grilles()
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
        # (B5) each stub stands in its own pool of wax, a run of wax down its front, its top hollowed round the wick
        els += [bx(f"Candle{i}", (x, 0.5, z), (x + 1.4, 0.3 + h, z + 1.4), "candlewax"),
                bx(f"Rim{i}", (x, 0.3 + h, z), (x + 1.4, 0.5 + h, z + 1.4), "candlewax", faces=("north", "south", "east", "west")),
                bx(f"Pool{i}", (x - 0.45, 0.5, z - 0.45), (x + 1.85, 0.75, z + 1.85), "candlewax", faces=("north", "south", "east", "west", "up")),
                bx(f"Run{i}", (x + 0.3, 0.75, z - 0.25), (x + 0.8, 0.2 + h, z), "candlewax", faces=("north", "east", "west", "up")),
                bx(f"Wick{i}", (x + 0.55, 0.3 + h, z + 0.55), (x + 0.85, 1.1 + h, z + 0.85), "blackmetal")]
        flames.append(fire_fx.flame((x + 0.7) / 16 - 0.5, (1.1 + h) / 16 - 0.25, (z + 0.7) / 16 - 0.5, quantity=0.06, size=0.04))
    prop("candlestubs", "Candle Stubs", els, box=(0.25, 0, 0.25, 0.75, 0.25, 0.75), oriented=False, material="Metal", sounds=METAL,
         light=[7, 5, 7], extra={"particleProperties": flames, "drops": drops(("game:candle", 1, 0.5))},
         comment="Candle stubs left burning by a den's cache and under its crosses by whoever came before")


def level3():
    for material in ("glazed", "brick", "cinder"):
        wall_family(f"l3plaque{material}", "Level 3 Wall", {1: material},
                    [Decor("plaque", "Warning Plaque", {2: plate("Plaque", (2, 3, -0.4), (14, 13, 0), "plaque", "white")
                                                         + rivets("Plaque", 2, 3, 14, 13, -0.4)})],
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


def seep_textures():
    """(deep props) Almond Water seeping down a rock face. The wet stain is darker, bluer stone with glossy highlights
    along the runs and a fringe of pale mineral (calcite) at its edges, dithered at the very edge so the rock shows
    through (the cutout pass has no half-alpha); the water is a milky film with a bright core and a lit edge; the crust
    is flowstone in layers; the pool is a milky basin of water with ripple rings and a wet rim."""
    rng = random.Random(seed_of("seep"))
    wet = (34, 36, 38)
    for name, top, bottom, start in (("seepstain", 2.4, 9.0, 6), ("seepstainlow", 9.0, 11.5, 0)):
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        px = img.load()
        for y in range(start, S):
            hw = top + (bottom - top) * (y - start) / (S - 1 - start)
            if name == "seepstainlow" and y >= S - 6:
                hw += (y - (S - 7)) * 0.9  # spreading out where it meets the floor
            for x in range(S):
                d = abs(x - 15.5 - 1.2 * ((y // 7) % 2) - 0.8 * math.sin(y * 0.55)) / hw
                if d < 0.62 or (d < 1.1 and rng.random() < (1.1 - d) * 1.6):
                    v = rng.randint(-4, 4) + (3 if (x * 5 + y * 3) % 11 == 0 else 0)
                    px[x, y] = (wet[0] + v, wet[1] + v, wet[2] + v + 2, 255)
                    if d > 0.4 and rng.random() < 0.18:
                        px[x, y] = (24, 26, 28, 255)  # a deeper, wetter pit
                elif d < 1.5 and rng.random() < 0.13 * (1.5 - d):
                    c = rng.choice(((178, 166, 132), (156, 144, 112), (198, 188, 156)))
                    px[x, y] = (c[0], c[1], c[2], 255)  # calcite speckle past the wet edge
        if name == "seepstain":
            for y in range(3, 7):
                for x in range(14, 18):
                    px[x, y] = (16, 14, 12, 255)  # the crack it comes out of
            for x in (13, 18):
                px[x, 4] = (170, 160, 128, 255)
        for x0 in (14, 17):  # the glossy runs: a bright 1 px line that wanders, broken
            x = x0
            for y in range(start + 1, S):
                x += rng.choice((-1, 0, 0, 0, 1)) if y % 5 == 0 else 0
                if rng.random() < 0.72:
                    px[x, y] = (176, 186, 190, 255) if rng.random() < 0.45 else (128, 138, 142, 255)
        save(img, name)
    img = noise(0xC4CCD0, 4, "seepwater")
    d = ImageDraw.Draw(img)
    d.line([1, 0, 1, S - 1], fill=rgb(0xF6F8FA))
    d.line([0, 0, 0, S - 1], fill=rgb(0x9AA6AC))
    d.line([2, 0, 2, S - 1], fill=rgb(0xA8B4BA))
    for y in range(2, S, 9):
        d.point((1, y), fill=(255, 255, 255, 255))
    save(img, "seepwater")
    img = noise(0xC8BC98, 8, "seepcrust")
    for y in range(3, S, 5):  # flowstone grows in layers
        ImageDraw.Draw(img).line([0, y, S - 1, y + 1 if y % 10 == 3 else y], fill=rgb(0xA89C78))
        ImageDraw.Draw(img).line([0, y + 1, S - 1, y + 1 if y % 10 == 3 else y + 1], fill=rgb(0xE6DEC0))
    T.blotch(img, (16, 16), 12, (226, 218, 190), 0.4, seed_of("seepcrust"))
    save(img, "seepcrust")
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    px = img.load()
    for y in range(S):
        for x in range(S):
            dd = (((x - 15.5) / 15.5) ** 2 + ((y - 15.5) / 15.5) ** 2) ** 0.5 + rng.uniform(-0.1, 0.1)
            if dd < 1:
                v = rng.randint(-5, 5)
                px[x, y] = (178 + v, 190 + v, 192 + v, 255) if dd < 0.8 else (108 + v, 112 + v, 108 + v, 255)
    for r in (0.28, 0.5, 0.7):  # ripple rings round where the drips land
        for k in range(48):
            a = k / 48 * 2 * math.pi
            x, y = int(15.5 + 15.5 * r * math.cos(a)), int(15.5 + 15.5 * r * math.sin(a))
            if px[x, y][3]:
                px[x, y] = (222, 232, 234, 255)
    for x, y in ((12, 13), (18, 17), (15, 20)):
        px[x, y] = (250, 252, 252, 255)
    save(img, "seeppool")


def level8():
    # Almond Water seeping out of the rock: a rock cube (the host's own rock) with a crust of deposit where it comes out
    # of a crack, two milky trickles running down this face and the one below over a dark wet stain, and a pool on the
    # floor in front. The block does not know which way the road is, so every face has it (the others are in rock)
    side = [bx("Stain", (0, 0, -0.12), (16, 16, -0.1), "seepstain", faces=("north",), full=True),
            bx("StainLow", (0, -16, -0.12), (16, 0, -0.1), "seepstainlow", faces=("north",), full=True),
            bx("Crust", (6.2, 12.6, -0.7), (10.2, 14.2, 0), "seepcrust", faces=("north", "east", "west", "up", "down")),
            bx("Crust2", (7, 11.6, -0.4), (9.4, 12.6, 0), "seepcrust", faces=("north", "east", "west", "down")),
            bx("Drape", (7.3, 9.4, -0.3), (9.1, 11.6, -0.12), "seepcrust", faces=("north", "east", "west", "down")),
            bx("Drip1", (7.7, 8.7, -0.28), (8.3, 9.4, -0.12), "seepcrust", faces=("north", "east", "west", "down")),
            bx("Drip2", (8.5, 9.0, -0.26), (8.9, 9.4, -0.12), "seepcrust", faces=("north", "east", "west", "down")),
            # the basin it gathers in, on the road in front: a low lip of the host rock round a milky pool
            bx("Pool", (3.5, -15.0, -5.8), (12.5, -14.9, -0.5), "seeppool", faces=("up",), full=True, glow=20),
            bx("LipF", (3.0, -16, -6.4), (13.0, -14.7, -5.7), "rock", faces=("north", "up", "east", "west")),
            bx("LipL", (3.0, -16, -5.7), (3.7, -14.7, -0.5), "rock", faces=("up", "west", "east")),
            bx("LipR", (12.3, -16, -5.7), (13.0, -14.7, -0.5), "rock", faces=("up", "west", "east"))]
    for i, (x, y1, y2) in enumerate(((7.4, 6, 11.6), (7.9, -4, 6), (7.5, -15.9, -4), (8.9, 0.5, 11.6), (9.2, -15.9, 0.5),
                                      (6.4, -8, 4), (10.4, -10, 1))):
        side.append(bx(f"Trickle{i}", (x, y1, -0.4), (x + 0.5, y2, -0.12), "seepwater", faces=("north", "east", "west"), glow=30))
    els = [bx("Rock", (0, 0, 0), (16, 16, 16), "rock")]
    for k in range(4):
        els += [turn(e, k) for e in side]
    # The shape's own default for "rock" is the seep's real texture (almondseeprock swaps it per variant), not a
    # nonexistent block/detail/rock that only the block's override hides.
    EXT["rock"] = "backrooms:block/detail/almondseep"
    try:
        path = shape("almondseep", els)
    finally:
        del EXT["rock"]
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
    trolley_textures()
    level1()
    level2()
    level3()
    level5()
    level8()
    lang()
